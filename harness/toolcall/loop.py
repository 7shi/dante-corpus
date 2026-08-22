"""Transport-agnostic agent loop over the closed grammar toolset (`TOOLCALL.md` §4).

The loop owns history, turn budget, and termination; it never learns which transport
produced a turn. Each turn:

1. `transport.complete(messages, tools)` -> `{text, tool_calls}` (canonical form).
2. The assistant message is appended to the transcript verbatim.
3. Zero tool calls = final answer: the loop ends.
4. Otherwise every call — canonical or parse-error envelope — is executed through
   `GrammarToolkit.dispatch` (or passed through as an error), every outcome is rendered
   by `format_tool_result`, and all blocks are embedded in one user message (interim
   path convention), mirroring how native paths deliver `tool` role messages.

Errors never cross the loop boundary: dispatch and parser failures come back as
structured envelopes and are fed to the model verbatim for self-correction.
"""

from __future__ import annotations

import sys
import time
from dataclasses import dataclass, field
from typing import Callable, Sequence

from .parser import format_tool_result, is_parse_error
from .transports import Transport, TransportResponse

__all__ = [
    "LoopResult",
    "execute_tool_calls",
    "outcome_brief",
    "progress_printer",
    "progress_separator",
    "progress_subseparator",
    "run_tool_loop",
]

DEFAULT_MAX_TURNS = 8


@dataclass
class LoopResult:
    """Outcome of one `run_tool_loop` session."""

    text: str  # final assistant text; "" when the turn budget was exhausted
    turns: int  # completed model turns
    exhausted: bool  # True if stopped by the turn budget instead of a final answer
    outcomes: list[dict] = field(default_factory=list)  # every envelope, in call order
    messages: list[dict] = field(default_factory=list)  # full transcript
    # Wall-clock seconds per completed model turn (model call + tool dispatches),
    # aligned with the turn counter; logged so long runs can be profiled afterwards.
    turn_seconds: list[float] = field(default_factory=list)


def execute_tool_calls(toolkit, calls: Sequence[dict]) -> list[dict]:
    """Run canonical tool calls through `toolkit.dispatch`; pass error envelopes through.

    Returns one outcome envelope per input item, in order:
    `{"ok": True/False, "tool": ..., "result"/"error": ...}`.
    """
    outcomes: list[dict] = []
    for item in calls:
        if not is_parse_error(item) and item.get("type") == "function":
            function = item.get("function", {})
            outcomes.append(
                toolkit.dispatch(function.get("name", ""), function.get("arguments", ""))
            )
        else:
            outcomes.append(item)
    return outcomes


def _brief_error(message: str, limit: int = 90) -> str:
    """One-line short error rendering that keeps both the cause and the evidence.

    Parse-error texts lead with a long fixed explanation and end with a snippet of
    the offending model output — where syntax mistakes (e.g. an unbalanced brace)
    usually live — so long messages keep their head *and* tail.
    """
    message = " ".join(str(message).split())
    if len(message) <= limit:
        return message
    return f"{message[:30]}…{message[-(limit - 31):]}"


def outcome_brief(outcome: dict) -> str:
    """Compact human-readable summary of one dispatch outcome envelope.

    Progress lines show the tool's *return value*, not just its name: validation
    verdicts (with error/warning/feedback counts), served unit bounds, hit counts,
    or the error text for failed dispatches — kept to one short field per call.
    """
    name = outcome.get("tool") or "?"
    if not outcome.get("ok"):
        return f"{name}=ERROR:{_brief_error(outcome.get('error', ''))}"
    result = outcome.get("result")
    if isinstance(result, dict):
        if "valid" in result:
            verdict = "valid" if result["valid"] else "INVALID"
            extra = ""
            if result.get("errors"):
                extra += f" {len(result['errors'])}err"
            if result.get("warnings"):
                extra += f" {len(result['warnings'])}warn"
            feedback = result.get("upstream_feedback")
            if feedback:
                extra += f" +{len(feedback)}uf"
            return f"{name}={verdict}{extra}"
        unit = result.get("unit")
        if isinstance(unit, dict):
            canticle = str(unit.get("canticle", "?"))[:3]
            bounds = f"L{unit.get('line_start')}-{unit.get('line_end')}"
            return f"{name}={canticle} {unit.get('canto')} {bounds}"
        return f"{name}=ok({len(result)} keys)"
    if isinstance(result, list):
        return f"{name}={len(result)} hits"
    return f"{name}=ok"


def progress_printer(
    label: str, max_turns: int, stream=None
) -> Callable[[int, TransportResponse, list[dict]], None]:
    """Build an `on_turn` callback printing one stderr line per completed model turn.

    Live runs are otherwise silent for minutes per turn on local models; this makes
    them watchable without polluting the JSONL logs (stderr only). The line carries
    the label, cumulative turn counter against the session budget, each dispatched
    call with its compact return value (see `outcome_brief`), and seconds since the
    printer was created. Works unchanged over both wire formats: outcomes come from
    the shared loop, so native tool calls report exactly like XML ones.
    """
    stream = sys.stderr if stream is None else stream
    started = time.monotonic()

    def on_turn(turn: int, response: TransportResponse, outcomes: list[dict]) -> None:
        if outcomes:
            what = "; ".join(outcome_brief(outcome) for outcome in outcomes)
        elif response.tool_calls:
            names = [
                call.get("function", {}).get("name") or "<parse-error>"
                for call in response.tool_calls
            ]
            what = ", ".join(names)
        else:
            what = "final answer"
        elapsed = time.monotonic() - started
        print(
            f"[{label}] turn {turn}/{max_turns} {what} (+{elapsed:.0f}s)",
            file=stream,
            flush=True,
        )

    return on_turn


def progress_separator(label: str, index: int, total: int, stream=None) -> None:
    """Announce one session's start with its position in the run.

    Long benchmark/probe/parity runs process dozens of sessions; without a marker
    between them there is no way to tell where a multi-hour run currently is. The
    line goes to stderr (JSONL logs stay clean) and names the session plus its
    `[index/total]` position.
    """
    stream = sys.stderr if stream is None else stream
    print(f"\n===== [{index}/{total}] {label} =====", file=stream, flush=True)


def progress_subseparator(label: str, stream=None) -> None:
    """Mark a sub-boundary inside one announced group (`-` line, no position).

    Used where one session splits into named passes — parity's xml vs native side —
    so the transcript reads as major `=====` separators between sessions and minor
    `-----` ones between the passes within a session.
    """
    stream = sys.stderr if stream is None else stream
    print(f"\n----- {label} -----", file=stream, flush=True)


def run_tool_loop(
    *,
    transport: Transport,
    toolkit,
    messages: list[dict],
    tools: Sequence[dict] = (),
    max_turns: int = DEFAULT_MAX_TURNS,
    on_turn: Callable[[int, TransportResponse, list[dict]], None] | None = None,
) -> LoopResult:
    """Drive the multi-turn tool-call conversation to a final answer.

    `messages` is the opening transcript (system prompt + task); it is copied, never
    mutated. `tools` (the closed tool surface, e.g. `runner.tools.TOOL_SPECS`) is handed
    to the transport untouched. The loop ends on the first response without tool calls
    (final answer) or after `max_turns` model turns (`exhausted=True`). `on_turn`, when
    given, is called after every completed model turn — including the final-answer
    turn — with `(1-based turn number, response, outcomes)`, where `outcomes` holds the
    turn's dispatch envelopes (empty for a final answer); it is pure observability and
    never influences the loop. Per-turn wall-clock durations are recorded on the result.
    """
    transcript = [dict(message) for message in messages]
    result = LoopResult(text="", turns=0, exhausted=False)

    for _turn in range(max_turns):
        turn_started = time.monotonic()
        response = transport.complete(transcript, tools)
        result.turns += 1
        transcript.append({"role": "assistant", "content": response.text})

        if not response.tool_calls:
            result.turn_seconds.append(time.monotonic() - turn_started)
            result.text = response.text
            result.messages = transcript
            if on_turn is not None:
                on_turn(result.turns, response, [])
            return result

        turn_outcomes = execute_tool_calls(toolkit, response.tool_calls)
        result.outcomes.extend(turn_outcomes)
        result.turn_seconds.append(time.monotonic() - turn_started)
        if on_turn is not None:
            on_turn(result.turns, response, turn_outcomes)

        # Interim path: results ride in the next user message, one block per call,
        # in call order (native paths would emit one `tool` message per call instead).
        feedback = "\n".join(format_tool_result(outcome) for outcome in turn_outcomes)
        transcript.append({"role": "user", "content": feedback})

    result.exhausted = True
    result.messages = transcript
    return result
