"""Stage 1 agent runner: one autonomous grammar session per parse unit (Milestone 1.2).

Wires the proven pieces together (`harness/PLAN.md` Handoff):

- system prompt per unit = 5-step CoT reasoning protocol (`runner.prompts`) +
  the tool-call wire contract + the closed tool specs;
- the session itself runs through `toolcall.run_tool_loop` over a
  `PromptXmlTransport`, so migrating to native tool calling later stays a
  transport swap;
- everything the Milestone 1.3 benchmark consumes hangs off `UnitResult`, which
  wraps the loop's `LoopResult` fields (final text, outcome envelopes, full
  transcript) plus the derived facts: candidate rows, validation outcomes,
  protocol-compliance flags, and a structured trace record for Stage 2 mining.

**No-call nudge policy** (TOOLCALL.md T4 carry-over): the loop treats a response
without `<tool_call>` blocks as the final answer, but live probing caught the
model answering in prose before doing any tool work. This runner resumes such a
session once with a protocol reminder — appended as an ordinary user message, the
loop untouched — but only when *zero* successful `validate_candidate` dispatches
have happened. Giving up after failed validations is a capability failure the
benchmark must measure, so it is never nudged. This resolves the practical half
of TOOLCALL.md §7.1 for Stage 1: `validate_candidate` doubles as the de-facto
acceptance gate; a dedicated `submit_candidate` termination tool stays open.
"""

from __future__ import annotations

import argparse
import itertools
import json
import sys
import time
from contextvars import ContextVar
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Sequence

from harness.toolcall import (
    PromptXmlTransport,
    Transport,
    is_parse_error,
    parse_tool_calls,
    progress_printer,
    progress_separator,
    progress_subseparator,
    run_tool_loop,
)

from .prompts import (
    WORKFLOWS,
    few_shot_messages,
    system_prompt,
    unit_task,
)
from .tools import GrammarToolkit, tool_specs

__all__ = [
    "BYTES_PER_TOKEN",
    "DEFAULT_BUCKET_DEPTH_TOKENS",
    "DEFAULT_BUCKET_RATE_TOKENS_PER_MIN",
    "DEFAULT_MODEL",
    "OPENING_MESSAGE_COUNT",
    "SESSION_MAX_TURNS",
    "MAX_NUDGES",
    "NUDGE_MESSAGE",
    "WORKFLOWS",
    "TokenBucket",
    "UnitResult",
    "llm7shi_generate",
    "run_unit",
    "token_usage",
    "_validate_calls",
]

DEFAULT_MODEL = "ollama:gemma4:31b-it-qat"  # model.mk default: Gemma 4 31B QAT via Ollama

# Roomier than the loop default (8): five protocol steps plus correction turns on
# sentence-group units that carry several predicates.
SESSION_MAX_TURNS = 12

# Live probing saw ~2% no-call turns; one reminder is enough, more risks loops.
MAX_NUDGES = 1

# The prompt-side prefix of every session transcript: system + few-shot demo
# exchange + task.
OPENING_MESSAGE_COUNT = 1 + len(few_shot_messages()) + 1

VALIDATE_TOOL = "validate_candidate"

NUDGE_MESSAGE = (
    "Your reply ended the session without any successful `validate_candidate` "
    "call, so no candidate skeleton exists yet. Do not answer in prose alone: "
    "return to the task, decide your skeleton rows for the unit, and submit "
    "them with `validate_candidate`. Only after you have validated a candidate "
    "may you give your final answer."
)

# Request-level observability (§4 make-the-invisible-measurable): every live
# LLM request flows through `llm7shi_generate`, which reads this context to
# stamp its JSONL records with the session/unit that issued the call. `run_unit`
# sets it around the session loop; outside a session it reads as None.
_LLM_REQUEST_CONTEXT: ContextVar[dict | None] = ContextVar(
    "llm_request_context", default=None
)
_SESSION_SEQ = itertools.count(1)

# Pacing conventions (STAGE3.md §2.C): the TPM ceiling is a property of the
# model API key shared by every parallel stream, so the launch paces through
# one bucket file. Token amounts use the 3.5 bytes/token wire convention the
# Stage-3 measurements were made in.
BYTES_PER_TOKEN = 3.5
DEFAULT_BUCKET_RATE_TOKENS_PER_MIN = 12000.0  # 42 kB/min: sustained <= 75% of the 16k ceiling
DEFAULT_BUCKET_DEPTH_TOKENS = 6500.0  # >= max single call (STAGE3.md §3)


def token_usage(response) -> dict:
    """Provider-reported token counts for one backend call, best effort.

    Byte sizes are the harness's portable currency, but the API ceiling the
    Stage-3 pacing fights is denominated in *tokens*, and the bytes/token
    ratio is neither constant nor ours to choose (JSON indentation, XML
    markup and Italian text tokenize at very different rates). Providers do
    report the real numbers, but only in provider-specific shapes on the raw
    stream chunks, which llm7shi keeps verbatim on `Response.chunks`:

    - Gemini (`google-genai`): a `usage_metadata` on the chunks — the final
      one carries the call's totals (`prompt_token_count`,
      `candidates_token_count`, `thoughts_token_count`, `total_token_count`);
    - Ollama: `prompt_eval_count` / `eval_count` on the terminating chunk.

    Returns the normalized keys `input_tokens` / `output_tokens` /
    `thought_tokens` / `total_tokens` (values `None` where the backend does
    not report them) so the log schema stays uniform across providers. An
    unknown backend, a missing stream, or a chunk shape that has changed
    yields all-`None` rather than raising: cost accounting must never break a
    live run.
    """
    for chunk in reversed(list(getattr(response, "chunks", None) or [])):
        usage = _chunk_usage(chunk)
        if usage:
            return usage
    return dict(_EMPTY_USAGE)


_EMPTY_USAGE = {
    "input_tokens": None,
    "output_tokens": None,
    "thought_tokens": None,
    "total_tokens": None,
}


def _field(source, name):
    """Read `name` off a chunk that may be an object or a mapping."""
    if isinstance(source, dict):
        value = source.get(name)
    else:
        value = getattr(source, name, None)
    return value if isinstance(value, int) else None


def _chunk_usage(chunk) -> dict | None:
    """Normalize one raw stream chunk, or None when it reports no usage."""
    metadata = chunk.get("usage_metadata") if isinstance(chunk, dict) else getattr(
        chunk, "usage_metadata", None
    )
    if metadata is not None:
        prompt = _field(metadata, "prompt_token_count")
        candidates = _field(metadata, "candidates_token_count")
        thoughts = _field(metadata, "thoughts_token_count")
        total = _field(metadata, "total_token_count")
        if prompt is not None or total is not None:
            return {
                "input_tokens": prompt,
                "output_tokens": candidates,
                "thought_tokens": thoughts,
                "total_tokens": total,
            }
        return None
    prompt = _field(chunk, "prompt_eval_count")
    output = _field(chunk, "eval_count")
    if prompt is None and output is None:
        return None
    return {
        "input_tokens": prompt,
        "output_tokens": output,
        "thought_tokens": None,
        "total_tokens": None if prompt is None or output is None else prompt + output,
    }


class TokenBucket:
    """Cross-process pacing bucket over an fcntl-locked JSON file.

    State is `{"t": <unix seconds>, "tokens": <float>}`: refill continuous at
    `rate_per_min` tokens/min up to `depth`, debit before send, sleep until
    funded. The lock releases on process death (single machine, wall clock);
    a missing or corrupt file recreates at full depth (STAGE3.md §6). All
    waits are injectable (`clock`/`sleeper`) so tests pace deterministically.
    """

    def __init__(
        self,
        path,
        *,
        rate_per_min: float = DEFAULT_BUCKET_RATE_TOKENS_PER_MIN,
        depth: float = DEFAULT_BUCKET_DEPTH_TOKENS,
        clock=time.time,
        sleeper=time.sleep,
    ) -> None:
        import fcntl
        import pathlib

        if rate_per_min <= 0 or depth <= 0:
            raise ValueError(
                "bucket rate and depth must be positive: "
                f"rate_per_min={rate_per_min!r}, depth={depth!r}"
            )
        self.path = pathlib.Path(path)
        self.rate_per_min = float(rate_per_min)
        self.depth = float(depth)
        self.clock = clock
        self.sleeper = sleeper
        self._fcntl = fcntl

    def _parse(self, raw: str) -> dict:
        """Decode persisted state; missing/corrupt recreates at full depth."""
        try:
            state = json.loads(raw)
            if (
                not isinstance(state, dict)
                or not isinstance(state.get("t"), (int, float))
                or not isinstance(state.get("tokens"), (int, float))
            ):
                raise ValueError("malformed bucket state")
            return {"t": float(state["t"]), "tokens": float(state["tokens"])}
        except (ValueError, TypeError):
            return {"t": self.clock(), "tokens": self.depth}

    def acquire(self, amount: float) -> float:
        """Debit `amount` tokens, sleeping until funded; returns seconds waited.

        A debit larger than `depth` can never be funded (refill caps at
        depth): it drains the bucket and proceeds without waiting instead of
        deadlocking — a misconfigured depth then shows up as an unpaced
        burst, the same residual class the 429 backstop already absorbs.
        The launch parameters keep depth >= any single call by design.
        """
        waited = 0.0
        amount = min(float(amount), self.depth)
        while True:
            deficit = 0.0
            with open(self.path, "a+", encoding="utf-8") as handle:
                self._fcntl.flock(handle.fileno(), self._fcntl.LOCK_EX)
                try:
                    handle.seek(0)
                    state = self._parse(handle.read())
                    now = self.clock()
                    # Continuous refill since the last touch (any process).
                    elapsed = max(0.0, now - state["t"])
                    state["tokens"] = min(
                        self.depth,
                        state["tokens"] + elapsed * self.rate_per_min / 60.0,
                    )
                    state["t"] = now
                    if state["tokens"] >= amount:
                        state["tokens"] -= amount
                        handle.seek(0)
                        handle.truncate()
                        handle.write(json.dumps(state, ensure_ascii=False) + "\n")
                        handle.flush()
                        return waited
                    deficit = amount - state["tokens"]
                finally:
                    self._fcntl.flock(handle.fileno(), self._fcntl.LOCK_UN)
            # Starving: sleep the deficit off (small epsilon avoids tight
            # re-lock loops), then retry — another process may have consumed.
            pause = deficit / (self.rate_per_min / 60.0) + 0.05
            self.sleeper(pause)
            waited += pause


def llm7shi_generate(
    model: str = DEFAULT_MODEL,
    temperature: float | None = None,
    quiet: bool = True,
    file=None,
    request_log=None,
    min_send_interval: float = 0.0,
    token_bucket: TokenBucket | None = None,
    clock=time.monotonic,
    sleeper=time.sleep,
):
    """Build a generate function over `llm7shi.Client` and its history management.

    The loop's transcript stays the single source of truth; this adapter mirrors
    it into a per-session `Client` (system prompt + history) so every model call
    also rides `Client`'s quality-retry loop — empty replies and repetitive
    output are regenerated instead of silently ending a session (the predicate
    run's two empty-final sessions, 2026-08-23). Session boundaries are explicit:
    the session runner calls ``transport.reset()`` (forwarded to ``generate.
    reset``), which regenerates the Client instance for the next session.

    **What is sent** (STAGE3.md record S3.7): the transcript verbatim, every
    call. Transcript compaction was designed, implemented, measured and
    **removed** — every shape of it (results-only, newest-turn-only, digests)
    bought ≤ 0.5% of the wire while degrading the model's view of its own
    session. The Client sync invariant is a **content fingerprint** over the
    transcript prefix: the adapter remembers exactly which `(role, content)`
    pairs the Client mirrors, appends when the new transcript merely extends
    them, and rebuilds the Client (system prompt + history re-append) whenever
    the prefix changes. A repeated call at the same transcript position finds
    the mirror *ahead* and rebuilds, exactly like the old length sync.

    **Pacing (STAGE3.md §2.C)**, both at the single send point and deliberately
    surviving ``reset()`` (session boundaries are sends too):

    - ``min_send_interval`` (seconds, 0 = off): sleep until the last send
      *start* is at least this far past — breaks the fast-response/big-send
      pairing that stacks two sends into one rolling minute;
    - ``token_bucket`` (a `TokenBucket`, shared file across processes):
      debit the send's input tokens (view bytes / `BYTES_PER_TOKEN`) before
      sending, sleeping until funded.

    Every deliberate wait prints one line to the adapter's stream and lands as
    ``paced_seconds`` on the ``llm_request`` record, keeping it separable from
    429 backoffs (``api_retry_seconds``). ``clock``/``sleeper`` are injectable
    for deterministic tests.

    ``request_log`` (an open text sink, UTF-8 JSONL) makes every backend
    request measurable: one `llm_request` record is appended just before the
    call (timestamp, model, session/unit coordinates from the request
    context, transcript position, same-turn attempt, `context_bytes`,
    newest-message size, paced seconds) and one `llm_response` record
    after it (duration, output bytes, empty flag, and the backend's own
    token counts via `token_usage` — `None` where the provider reports
    none, and covering only the attempt whose text the Client returned,
    exactly like the byte figures). Join key across the pair:
    ``(session, messages, attempt)``. Retries inside `Client` (429 backoffs, quality
    regeneration) stay invisible here by construction; they are measured by
    the stream's `wait_retry` counters and correlated by timestamp. The
    reconstruct CLI points this at its own streaming `--log` sink, so the
    cost records ride the same file as the unit records (canto-scoped,
    resume-compacted with them).
    """
    from llm7shi import Client

    state: dict = {
        "client": None,
        "mirrored": [],  # (role, content) pairs the Client's history holds
        "attempts": {},
        "last_send_start": None,
    }

    def _attempt(session, position: int) -> int:
        key = (session, position)
        state["attempts"][key] = state["attempts"].get(key, 0) + 1
        return state["attempts"][key]

    def _log(record: dict) -> None:
        if request_log is not None:
            request_log.write(json.dumps(record, ensure_ascii=False) + "\n")
            request_log.flush()

    def _sync_client(view: list[dict]):
        """Mirror the view prefix into the Client: append the delta when the
        view merely extends what is mirrored, rebuild on any change."""
        prefix = [
            (str(m.get("role", "")), str(m.get("content", ""))) for m in view[:-1]
        ]
        mirrored = state["mirrored"]
        extends = len(mirrored) <= len(prefix) and mirrored == prefix[: len(mirrored)]
        if state["client"] is not None and extends:
            for role, content in prefix[len(mirrored):]:
                state["client"].history.append({"role": role, "content": content})
            state["mirrored"] = prefix
            return state["client"]
        # A fresh `Client` starts its own stream mid-console: without a
        # separating blank line its first "🤔 Thinking..." line runs
        # straight onto whatever the previous Client (or progress line)
        # last printed, e.g. `</tool_call>🤔 Thinking...`.
        print(file=sys.stderr if file is None else file)
        client = Client(
            model=model,
            temperature=temperature,
            show_params=not quiet,
            file=sys.stderr if file is None else file,
        )
        start = 0
        if view and view[0].get("role") == "system":
            client.set_system_prompt(view[0]["content"])
            start = 1
        for message in view[start : len(view) - 1]:
            client.history.append(
                {"role": message["role"], "content": message["content"]}
            )
        state["client"] = client
        state["mirrored"] = prefix
        return client

    def generate(messages: list[dict]) -> str:
        view = messages
        client = _sync_client(view)

        context_bytes = sum(
            len(str(m.get("content", "")).encode("utf-8")) for m in view
        )

        # Pacing first, so the logged timestamp marks the physical send.
        paced_seconds = 0.0
        if min_send_interval > 0 and state["last_send_start"] is not None:
            due = state["last_send_start"] + min_send_interval
            now = clock()
            if now < due:
                pause = due - now
                print(
                    f"[pace] send interval: waiting {pause:.1f}s",
                    file=sys.stderr if file is None else file,
                    flush=True,
                )
                sleeper(pause)
                paced_seconds += pause
        if token_bucket is not None:
            waited = token_bucket.acquire(context_bytes / BYTES_PER_TOKEN)
            if waited > 0:
                print(
                    f"[pace] token bucket: waited {waited:.1f}s",
                    file=sys.stderr if file is None else file,
                    flush=True,
                )
                paced_seconds += waited
        if min_send_interval > 0:
            state["last_send_start"] = clock()

        context = _LLM_REQUEST_CONTEXT.get() or {}
        session = context.get("session")
        position = len(messages)
        attempt = _attempt(session, position)
        _log(
            {
                "record": "llm_request",
                "timestamp": datetime.now(timezone.utc).isoformat(
                    timespec="milliseconds"
                ),
                "model": model,
                "session": session,
                **{
                    k: context.get(k)
                    for k in ("canticle", "canto", "line_start", "line_end")
                },
                "messages": position,
                "attempt": attempt,
                "context_bytes": context_bytes,
                "new_bytes": len(
                    str(view[-1].get("content", "")).encode("utf-8")
                ),
                "paced_seconds": round(paced_seconds, 3),
            }
        )
        began = time.monotonic()
        response = client(view[-1]["content"])
        text = response.text
        _log(
            {
                "record": "llm_response",
                "timestamp": datetime.now(timezone.utc).isoformat(
                    timespec="milliseconds"
                ),
                "model": model,
                "session": session,
                **{
                    k: context.get(k)
                    for k in ("canticle", "canto", "line_start", "line_end")
                },
                "messages": position,
                "attempt": attempt,
                "duration_seconds": round(time.monotonic() - began, 3),
                "output_bytes": len(str(text).encode("utf-8")),
                # Provider-reported, so the TPM ceiling can be read in its own
                # currency instead of through the 3.5 B/token convention.
                **token_usage(response),
                "empty": not str(text).strip(),
            }
        )
        # Client appended the newest message and its reply, so the mirror is
        # the full view plus the reply — exactly the transcript's next prefix.
        # Any divergence (a retry at the same position) is caught by the next
        # call's fingerprint check, which rebuilds.
        state["mirrored"] = [
            (str(m.get("role", "")), str(m.get("content", ""))) for m in view
        ] + [("assistant", str(text))]
        return text

    def reset() -> None:
        """Session boundary: the next call regenerates the Client instance.

        Pacing state (last send start, the shared bucket) deliberately
        survives — session boundaries are sends too (STAGE3.md §2.C)."""
        state["client"] = None
        state["mirrored"] = []
        state["attempts"] = {}

    generate.reset = reset
    return generate


@dataclass
class UnitResult:
    """Everything one unit session produced; the contract consumed by 1.3/1.4."""

    unit: dict  # requested coordinates: canticle, canto, line_start, line_end?
    text: str = ""  # final assistant text; "" when the budget was exhausted
    turns: int = 0  # total model turns across the original run plus nudged resumes
    exhausted: bool = False
    nudges: int = 0  # protocol reminders issued
    workflow: str = "unit"  # validation granularity taught by the system prompt
    outcomes: list[dict] = field(default_factory=list)  # every envelope, in call order
    messages: list[dict] = field(default_factory=list)  # full transcript incl. nudges
    opening_len: int = 0  # prompt-side messages (system + demo + task) before turn 1
    turn_seconds: list[float] = field(default_factory=list)  # wall clock per model turn

    @property
    def session_messages(self) -> list[dict]:
        """The transcript from the model's first turn on (prompt-side stripped).

        Turn-level consumers (benchmark parse-success measurement, Stage 2 mining)
        must use this, not `messages`: the few-shot demo exchange inside the
        opening prompt contains a well-formed tool call that is not a model turn.
        """
        return self.messages[self.opening_len:]

    @property
    def validations(self) -> list[dict]:
        """Successful `validate_candidate` envelopes, in dispatch order."""
        return [
            o
            for o in self.outcomes
            if o.get("ok") and o.get("tool") == VALIDATE_TOOL
        ]

    @property
    def valid_seen(self) -> bool:
        """True if any dispatched validation reported `"valid": true`."""
        return any(o.get("result", {}).get("valid") for o in self.validations)

    @property
    def protocol_complete(self) -> bool:
        """Final answer given (not exhausted) after at least one successful validation."""
        return bool(self.text) and not self.exhausted and bool(self.validations)

    @property
    def submissions(self) -> list[list[dict]]:
        """Candidate rows from every `validate_candidate` call, in submission order.

        Parsed back out of the assistant turns (the dispatch envelope does not echo
        arguments), so this reflects exactly what the model submitted, first to last.
        The 1-shot exact-match metric reads `submissions[0]`; `candidate_rows`
        (the final submission) is `submissions[-1]`.
        """
        return [call.get("candidate_rows", []) for call in _validate_calls(self.messages)]

    @property
    def first_candidate_rows(self) -> list[dict]:
        """Candidate rows from the *first* `validate_candidate` submission."""
        subs = self.submissions
        return subs[0] if subs else []

    @property
    def candidate_rows(self) -> list[dict]:
        """Candidate rows from the last `validate_candidate` call in the transcript."""
        call = _last_validate_call(self.messages)
        return call.get("candidate_rows", []) if call else []

    @property
    def upstream_feedback(self) -> list[dict]:
        """All upstream-feedback records the model filed, in submission order."""
        records: list[dict] = []
        for outcome in self.validations:
            records.extend(outcome.get("result", {}).get("upstream_feedback") or [])
        return records

    def trace_record(self, *, include_transcript: bool = True) -> dict:
        """Structured session record for Stage 2 mining / 1.4 trace collection."""
        record = {
            "record": "session",
            "unit": self.unit,
            "workflow": self.workflow,
            "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "turns": self.turns,
            "turn_seconds": self.turn_seconds,
            "nudges": self.nudges,
            "exhausted": self.exhausted,
            "protocol_complete": self.protocol_complete,
            "validations": len(self.validations),
            "valid": self.valid_seen,
            "candidate_rows": self.candidate_rows,
            "upstream_feedback": self.upstream_feedback,
            "outcomes": self.outcomes,
            "final_text": self.text,
        }
        if include_transcript:
            record["messages"] = self.messages
        return record

    def summary(self) -> str:
        """Human-readable one-screen report used by the CLI."""
        lines = [
            f"unit: {self.unit['canticle']} {self.unit['canto']} "
            f"line {self.unit['line_start']}"
            + (f"-{self.unit['line_end']}" if self.unit.get("line_end") else ""),
            f"turns: {self.turns} (nudges: {self.nudges}, exhausted: {self.exhausted})",
            f"validations: {len(self.validations)} (any valid: {self.valid_seen})",
            f"candidate rows: {len(self.candidate_rows)}",
            f"upstream feedback records: {len(self.upstream_feedback)}",
        ]
        if self.turn_seconds:
            lines.append(
                f"turn seconds: total={sum(self.turn_seconds):.0f} "
                f"max={max(self.turn_seconds):.0f}"
            )
        if self.validations:
            diagnostics = self.validations[-1].get("result", {}).get("diagnostics")
            lines.append(f"last diagnostics: {diagnostics}")
        return "\n".join(lines)


def _validate_calls(messages: list[dict]) -> list[dict]:
    """Arguments dicts of every well-formed `validate_candidate` call, in order.

    Assistant turns are scanned in emission order; within a turn the parser
    preserves block order. Malformed JSON is skipped (dispatch would have errored).
    """
    calls: list[dict] = []
    for message in messages:
        if message.get("role") != "assistant":
            continue
        for item in parse_tool_calls(message.get("content", "")):
            if is_parse_error(item):
                continue
            function = item.get("function", {})
            if function.get("name") != VALIDATE_TOOL:
                continue
            try:
                arguments = json.loads(function.get("arguments", "{}"))
            except json.JSONDecodeError:
                continue  # dispatch would have errored; keep scanning
            if isinstance(arguments, dict):
                calls.append(arguments)
    return calls


def _last_validate_call(messages: list[dict]) -> dict | None:
    """Arguments dict of the last well-formed `validate_candidate` call, or None."""
    calls = _validate_calls(messages)
    return calls[-1] if calls else None


def _opening_messages(
    specs: Sequence[dict],
    canticle: str,
    canto: int,
    line_start: int,
    line_end: int | None,
    workflow: str = "unit",
) -> list[dict]:
    """System prompt (protocol + contract + specs), non-colliding demo, task."""
    messages: list[dict] = [
        {"role": "system", "content": system_prompt(specs, workflow)},
        *few_shot_messages(),
        {
            "role": "user",
            "content": unit_task(canticle, canto, line_start, line_end),
        },
    ]
    return messages


def run_unit(
    *,
    transport: Transport,
    toolkit: GrammarToolkit,
    canticle: str,
    canto: int,
    line_start: int,
    line_end: int | None = None,
    specs: Sequence[dict] | None = None,
    max_turns: int = SESSION_MAX_TURNS,
    max_nudges: int = MAX_NUDGES,
    workflow: str = "unit",
    on_turn=None,
    progress: bool = False,
    progress_stream=None,
) -> UnitResult:
    """Run one autonomous grammar session for a single parse unit.

    Opens the conversation with the reasoning-protocol prompt (`workflow` selects
    "unit" whole-unit validation vs "predicate" per-predicate interleaved
    validation), drives it through `run_tool_loop`, and enforces the no-call nudge
    policy: a final answer given with zero successful `validate_candidate`
    dispatches earns up to `max_nudges` reminders, each resuming the very same
    transcript through a fresh loop run under the shared turn budget. The loop
    library itself is left untouched. `on_turn` (see `toolcall.progress_printer`)
    is forwarded to every loop run with the turn number offset so nudged resumes
    keep counting session-wide. The session opens by calling ``transport.reset()``
    when the transport provides it, so per-session backend state (the Client
    adapter's history mirror, the native ledger) never carries across units.
    `progress` keeps multi-pass sessions watchable
    (harness/PLAN.md §4 item 5): each nudged resume is announced with a minor
    `toolcall.progress_subseparator` before the pass starts, written to
    `progress_stream` when given (a status line's console stream) or stderr.
    """
    specs = tool_specs() if specs is None else list(specs)
    opening = _opening_messages(
        specs, canticle, canto, line_start, line_end, workflow
    )
    result = UnitResult(
        unit={
            "canticle": canticle,
            "canto": canto,
            "line_start": line_start,
            "line_end": line_end,
        },
        workflow=workflow,
        opening_len=len(opening),
    )

    # Session boundary: transports/backends keeping per-session state (the
    # llm7shi Client adapter, the native transport's re-attachment ledger)
    # start fresh; stateless ones (StubTransport) simply have no reset.
    reset = getattr(transport, "reset", None)
    if callable(reset):
        reset()

    # Stamp this session's LLM requests (llm7shi_generate's request_log) with
    # the unit coordinates so request records join back to units.
    context_token = _LLM_REQUEST_CONTEXT.set(
        {
            "session": next(_SESSION_SEQ),
            "canticle": canticle,
            "canto": canto,
            "line_start": line_start,
            "line_end": line_end,
        }
    )

    transcript = [dict(m) for m in opening]
    remaining_budget = max_turns
    nudges_left = max_nudges

    try:
        while remaining_budget > 0:
            turns_before = result.turns

            def loop_on_turn(turn, response, outcomes, offset=turns_before):
                on_turn(turn + offset, response, outcomes)

            loop_result = run_tool_loop(
                transport=transport,
                toolkit=toolkit,
                messages=transcript,
                tools=specs,
                max_turns=remaining_budget,
                on_turn=loop_on_turn if on_turn is not None else None,
            )
            result.turns += loop_result.turns
            result.turn_seconds.extend(loop_result.turn_seconds)
            result.outcomes.extend(loop_result.outcomes)
            result.text = loop_result.text
            result.exhausted = loop_result.exhausted
            result.messages = loop_result.messages
            remaining_budget -= loop_result.turns

            if loop_result.exhausted:
                break  # budget spent; a reminder cannot help
            if any(
                o.get("ok") and o.get("tool") == VALIDATE_TOOL
                for o in loop_result.outcomes
            ):
                break  # worked through validation; prose ending is legitimate
            if nudges_left == 0 or remaining_budget <= 0:
                break  # still no validation: capability failure, measured as-is

            nudges_left -= 1
            result.nudges += 1
            if progress:
                progress_subseparator("nudged resume", stream=progress_stream)
            transcript = loop_result.messages + [
                {"role": "user", "content": NUDGE_MESSAGE}
            ]
    finally:
        _LLM_REQUEST_CONTEXT.reset(context_token)

    return result


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Run one autonomous grammar session for a single parse unit "
            "(harness/runner PLAN.md milestone 1.2)."
        )
    )
    parser.add_argument("--canticle", choices=("inferno", "purgatorio", "paradiso"))
    parser.add_argument("--canto", type=int)
    parser.add_argument("--line-start", type=int)
    parser.add_argument("--line-end", type=int)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--temperature", type=float, default=None)
    parser.add_argument("--max-turns", type=int, default=SESSION_MAX_TURNS)
    parser.add_argument("--max-nudges", type=int, default=MAX_NUDGES)
    parser.add_argument(
        "--workflow",
        choices=WORKFLOWS,
        default="unit",
        help="validation granularity: whole unit in one call (unit) or one "
        "predicate per call (predicate)",
    )
    parser.add_argument(
        "--trace",
        help="write this session's trace record (JSONL, one line) to this file",
    )
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args(argv)

    if not (args.canticle and args.canto and args.line_start):
        parser.error("--canticle, --canto and --line-start are required")

    transport = PromptXmlTransport(
        generate=llm7shi_generate(args.model, args.temperature, quiet=not args.verbose)
    )
    # §4 item 5: a live CLI announces its (single) session before turn lines start.
    progress_separator(f"{args.canticle} {args.canto} {args.line_start}", 1, 1)
    result = run_unit(
        transport=transport,
        toolkit=GrammarToolkit(),
        canticle=args.canticle,
        canto=args.canto,
        line_start=args.line_start,
        line_end=args.line_end,
        max_turns=args.max_turns,
        max_nudges=args.max_nudges,
        workflow=args.workflow,
        on_turn=progress_printer(
            f"{args.canticle} {args.canto} {args.line_start}", args.max_turns
        ),
        progress=True,
    )

    if args.trace:
        with open(args.trace, "w", encoding="utf-8") as sink:
            sink.write(json.dumps(result.trace_record(), ensure_ascii=False) + "\n")
        print(f"trace written to {args.trace}")
    print(result.summary())
    return 0


if __name__ == "__main__":
    sys.exit(main())
