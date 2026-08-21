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

from dataclasses import dataclass, field
from typing import Sequence

from .parser import format_tool_result, is_parse_error
from .transports import Transport

__all__ = [
    "LoopResult",
    "execute_tool_calls",
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


def run_tool_loop(
    *,
    transport: Transport,
    toolkit,
    messages: list[dict],
    tools: Sequence[dict] = (),
    max_turns: int = DEFAULT_MAX_TURNS,
) -> LoopResult:
    """Drive the multi-turn tool-call conversation to a final answer.

    `messages` is the opening transcript (system prompt + task); it is copied, never
    mutated. `tools` (the closed tool surface, e.g. `runner.tools.TOOL_SPECS`) is handed
    to the transport untouched. The loop ends on the first response without tool calls
    (final answer) or after `max_turns` model turns (`exhausted=True`).
    """
    transcript = [dict(message) for message in messages]
    result = LoopResult(text="", turns=0, exhausted=False)

    for _turn in range(max_turns):
        response = transport.complete(transcript, tools)
        result.turns += 1
        transcript.append({"role": "assistant", "content": response.text})

        if not response.tool_calls:
            result.text = response.text
            result.messages = transcript
            return result

        turn_outcomes = execute_tool_calls(toolkit, response.tool_calls)
        result.outcomes.extend(turn_outcomes)

        # Interim path: results ride in the next user message, one block per call,
        # in call order (native paths would emit one `tool` message per call instead).
        feedback = "\n".join(format_tool_result(outcome) for outcome in turn_outcomes)
        transcript.append({"role": "user", "content": feedback})

    result.exhausted = True
    result.messages = transcript
    return result
