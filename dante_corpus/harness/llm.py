"""Model access for the fixed-context loop: the llm7shi adapter and its wire log.

Extracted from the Stage-1 agent runner when the per-unit tool-calling session
was removed (2026-09-07): this is the half of that module the fixed-context
loop actually uses — a `generate(messages) -> text` closure over
`llm7shi.Client`, plus the request-level observability every live run records.

The adapter policy is `../ARCHITECTURE.md` §2: one stateful `Client` per
session, reused across turns, reset at session boundaries with pacing state
deliberately surviving (`../stages/03.md` §2.C).

Every live request flows through `llm7shi_generate`, which reads
`_LLM_REQUEST_CONTEXT` to stamp its `llm_request` / `llm_response` JSONL pair
with the session/unit that issued the call. `extractor.fixedcontext` sets that
context around each iteration, so the log's `(session, messages, attempt)` join
key stays unique.
"""

from __future__ import annotations

import itertools
import json
import sys
import time
from contextvars import ContextVar
from datetime import datetime, timezone

__all__ = [
    "DEFAULT_MODEL",
    "llm7shi_generate",
    "token_usage",
]

DEFAULT_MODEL = "ollama:gemma4:31b-it-qat"  # model.mk default: Gemma 4 31B QAT via Ollama


# sets it around the session loop; outside a session it reads as None.
_LLM_REQUEST_CONTEXT: ContextVar[dict | None] = ContextVar(
    "llm_request_context", default=None
)
_SESSION_SEQ = itertools.count(1)

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


def llm7shi_generate(
    model: str = DEFAULT_MODEL,
    temperature: float | None = None,
    quiet: bool = True,
    file=None,
    request_log=None,
    min_send_interval: float = 0.0,
    max_length: int | None = None,
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

    **What is sent** (../stages/03.md record S3.7): the transcript verbatim, every
    call. Transcript compaction was designed, implemented, measured and
    **removed** — every shape of it (results-only, newest-turn-only, digests)
    bought ≤ 0.5% of the wire while degrading the model's view of its own
    session. The Client sync invariant is a **content fingerprint** over the
    transcript prefix: the adapter remembers exactly which `(role, content)`
    pairs the Client mirrors, appends when the new transcript merely extends
    them, and rebuilds the Client (system prompt + history re-append) whenever
    the prefix changes. A repeated call at the same transcript position finds
    the mirror *ahead* and rebuilds, exactly like the old length sync.

    **Pacing (../stages/03.md §2.C)**, at the single send point and deliberately
    surviving ``reset()`` (session boundaries are sends too):

    - ``min_send_interval`` (seconds, 0 = off): sleep until the last send
      *start* is at least this far past — breaks the fast-response/big-send
      pairing that stacks two sends into one rolling minute.

    Rate-limit responses (HTTP 429) are handled by `llm7shi.Client`'s own
    backoff (``api_retry_seconds``), not by pre-emptive pacing here.

    **Generation-side runaway cap (``max_length``, ../stages/03.md record S3.10)**:
    answer-text characters per call, handed straight to ``Client(max_length=)``
    — the same currency llm7shi counts in, because a stream's chunk is not
    necessarily one token and provider counts land only after the response
    completes. Crossing the cap fails the turn inside ``should_retry`` and
    the Client's quality-retry loop regenerates; only the final text enters
    history. Thinking-only runaways are not caught by design (they never
    reach history). ``None`` (the adapter default) disables the cap; callers
    own the policy value. Every cap-caused regeneration is counted and lands
    as ``max_length_retries`` on that call's ``llm_response`` record — the
    one Client-internal retry made visible, because its experiment needs a
    durable trigger count (the stderr warning alone is not durable).

    Every deliberate wait prints one line to the adapter's stream and lands as
    ``paced_seconds`` on the ``llm_request`` record, keeping it separable from
    429 backoffs (``api_retry_seconds``). ``clock``/``sleeper`` are injectable
    for deterministic tests.

    ``request_log`` (an open text sink, UTF-8 JSONL) makes every backend
    request measurable: one `llm_request` record is appended just before the
    call (timestamp, model, session/unit coordinates from the request
    context, transcript position, same-turn attempt, `context_bytes`,
    newest-message size, paced seconds) and one `llm_response` record
    after it (duration, output bytes, thinking bytes, empty flag, and the
    backend's own token counts via `token_usage` — `None` where the provider reports
    none, and covering only the attempt whose text the Client returned,
    exactly like the byte figures). Join key across the pair:
    ``(session, messages, attempt)``. Retries inside `Client` (429 backoffs,
    empty/repetition regenerations) stay invisible here by construction; they
    are measured by the stream's `wait_retry` counters and correlated by
    timestamp — except the answer-length cap's regenerations, counted as
    ``max_length_retries`` on the response record (S3.10). The
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
        "cap_hits": 0,  # cumulative should_retry hits on max_length (S3.10)
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
            max_length=max_length,
        )
        if max_length is not None and hasattr(client, "should_retry"):
            # Count cap-caused regenerations without touching the retry loop:
            # the instance-level wrapper sees exactly the attempts whose
            # Response carries `max_length` (the truncated ones). Fakes in
            # deterministic tests may not implement should_retry at all.
            base_should_retry = client.should_retry

            def _counting_should_retry(
                resp, schema=None, _base=base_should_retry
            ):
                reason = _base(resp, schema)
                if getattr(resp, "max_length", None) is not None:
                    state["cap_hits"] += 1
                return reason

            client.should_retry = _counting_should_retry
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
        cap_hits_before = state["cap_hits"]
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
                # Thinking is most of what a call actually generates (live
                # preflight: 139/203 thought tokens against 14/7 answer
                # tokens) and none of it reaches `text`, so per-call duration
                # is a function of this, not of `output_bytes`.
                "thought_bytes": len(
                    str(getattr(response, "thoughts", "") or "").encode("utf-8")
                ),
                # Provider-reported, so the TPM ceiling can be read in its own
                # currency instead of through the 3.5 B/token convention.
                **token_usage(response),
                "max_length_retries": state["cap_hits"] - cap_hits_before,
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
        survives — session boundaries are sends too (../stages/03.md §2.C)."""
        state["client"] = None
        state["mirrored"] = []
        state["attempts"] = {}
        state["cap_hits"] = 0

    generate.reset = reset
    return generate
