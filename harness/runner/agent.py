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
import json
import sys
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

from .prompts import WORKFLOWS, few_shot_messages, system_prompt, unit_task
from .tools import GrammarToolkit, tool_specs

__all__ = [
    "DEFAULT_MODEL",
    "SESSION_MAX_TURNS",
    "MAX_NUDGES",
    "NUDGE_MESSAGE",
    "WORKFLOWS",
    "UnitResult",
    "llm7shi_generate",
    "run_unit",
    "_validate_calls",
]

DEFAULT_MODEL = "ollama:gemma4:31b-it-qat"  # model.mk default: Gemma 4 31B QAT via Ollama

# Roomier than the loop default (8): five protocol steps plus correction turns on
# sentence-group units that carry several predicates.
SESSION_MAX_TURNS = 12

# Live probing saw ~2% no-call turns; one reminder is enough, more risks loops.
MAX_NUDGES = 1

VALIDATE_TOOL = "validate_candidate"

NUDGE_MESSAGE = (
    "Your reply ended the session without any successful `validate_candidate` "
    "call, so no candidate skeleton exists yet. Do not answer in prose alone: "
    "return to the task, decide your skeleton rows for the unit, and submit "
    "them with `validate_candidate`. Only after you have validated a candidate "
    "may you give your final answer."
)


def llm7shi_generate(
    model: str = DEFAULT_MODEL, temperature: float | None = None, quiet: bool = True
):
    """Build a stateless generate function over `llm7shi.compat.generate_with_schema`.

    Proven adapter copied from `harness.toolcall.probe` (both the Ollama and the
    Gemini path were exercised end-to-end during the T4 gate). The stream sink is
    pinned to stderr (§4 item 5): llm7shi defaults to stdout, which would mix the
    🤔 Thinking / 💡 Answer display into machine-facing output.
    """
    from llm7shi.compat import generate_with_schema

    def generate(messages: list[dict]) -> str:
        response = generate_with_schema(
            messages,
            schema=None,
            model=model,
            temperature=temperature,
            show_params=not quiet,
            file=sys.stderr,
        )
        return response.text

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
    keep counting session-wide. `progress` keeps multi-pass sessions watchable
    (harness/PLAN.md §4 item 5): each nudged resume is announced with a minor
    `toolcall.progress_subseparator` before the pass starts.
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

    transcript = [dict(m) for m in opening]
    remaining_budget = max_turns
    nudges_left = max_nudges

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
            progress_subseparator("nudged resume")
        transcript = loop_result.messages + [{"role": "user", "content": NUDGE_MESSAGE}]

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
