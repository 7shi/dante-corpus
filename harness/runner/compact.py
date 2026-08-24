"""The continuation wire view: a pure history policy for calls 2+ (STAGE3.md §2.A).

Compaction changes only what the backend physically receives, never the
transcript: `LoopResult.messages`, traces, mining, and nudge resumes keep
their Stage-1/2 semantics because the loop's transcript stays the single
source of truth. This module is the policy the adapter (`runner.agent.
llm7shi_generate`) applies at its single send point:

- **Call 1** (transcript length == the opening length): the verbatim opening —
  planning semantics are exactly Stage-1/2's.
- **Calls 2+**: `[continuation-system] [task] [compacted history] [newest]`:

  - the continuation system prompt (see `runner.prompts.
    continuation_system_prompt`) as message 0;
  - the opening's task message verbatim (the unit assignment);
  - the compacted history: the `read_unit` payload and every other
    `<tool_result>` feedback **verbatim** (they ride in user messages, which
    never shrink), the **last** assistant turn verbatim (the newest candidate
    submission the model repairs from), and every older assistant turn as a
    one-line digest (turn number, dispatched tool names, 80-char prose head);
  - the newest transcript message verbatim, in last position — the loop's
    contract.

Pure by construction: no I/O, no model, no clocks; deterministic over the
message list. Digests re-derive tool names through the real wire parser
(`toolcall.parse_tool_calls`) so they describe exactly what was dispatched.
"""

from __future__ import annotations

import re
from typing import Callable

from harness.toolcall import is_parse_error, parse_tool_calls

__all__ = [
    "DIGEST_HEAD_CHARS",
    "compact_view",
    "digest_message",
    "history_policy",
]

DIGEST_HEAD_CHARS = 80

_TOOL_BLOCK_RE = re.compile(r"<tool_call>.*?</tool_call>", re.DOTALL)


def _prose_head(content: str, limit: int) -> str:
    """The leading prose of a turn: tool-call blocks stripped, whitespace
    collapsed, truncated to `limit` characters (ellipsis marks a cut)."""
    prose = " ".join(_TOOL_BLOCK_RE.sub(" ", content).split())
    if len(prose) <= limit:
        return prose
    return prose[:limit] + "…"


def digest_message(content: str, turn: int, *, head_chars: int = DIGEST_HEAD_CHARS) -> str:
    """One-line digest of an older assistant turn (~150 B, STAGE3.md §2.A).

    Names the 1-based session turn number, the tools dispatched in that turn
    (parse-error envelopes collapse to `<parse-error>`), and the turn's
    80-character prose head.
    """
    names: list[str] = []
    for item in parse_tool_calls(content):
        if is_parse_error(item):
            names.append(str(item.get("tool") or "") or "<parse-error>")
        else:
            name = str(item.get("function", {}).get("name") or "")
            names.append(name or "<unnamed>")
    head = _prose_head(content, head_chars)
    parts = [f"turn {turn}"]
    if names:
        # Deduplicate, keep dispatch order.
        parts.append("called " + ", ".join(dict.fromkeys(names)))
    label = "[" + "; ".join(parts) + "]"
    return f"{label} {head}" if head else label


def compact_view(
    messages: list[dict],
    *,
    opening_len: int,
    continuation_system: str,
) -> list[dict]:
    """Render the wire view of one send (STAGE3.md §2.A); pure function.

    `messages` is the loop's full transcript (opening first); `opening_len`
    its prompt-side prefix length (system + demo + task); `continuation_system`
    the calls-2+ system prompt. Returns a fresh message list — the input is
    never mutated or aliased.
    """
    if opening_len < 1:
        raise ValueError(f"opening_len must be positive, got {opening_len!r}")
    if len(messages) <= opening_len:
        # Call 1: the verbatim opening.
        return [dict(message) for message in messages]

    task = messages[opening_len - 1]
    session = messages[opening_len:]
    newest = session[-1]
    history = session[:-1]
    last_assistant = max(
        (i for i, m in enumerate(history) if m.get("role") == "assistant"),
        default=None,
    )

    view: list[dict] = [
        {"role": "system", "content": continuation_system},
        {"role": "user", "content": str(task.get("content", ""))},
    ]
    turn = 0
    for i, message in enumerate(history):
        content = str(message.get("content", ""))
        if message.get("role") == "assistant":
            turn += 1
            if i == last_assistant:
                view.append({"role": "assistant", "content": content})
            else:
                view.append(
                    {"role": "assistant", "content": digest_message(content, turn)}
                )
        else:
            # Tool-result feedback (read_unit payloads included) and nudge
            # reminders ride in user messages and stay verbatim.
            view.append({"role": str(message.get("role", "user")), "content": content})
    view.append(
        {"role": str(newest.get("role", "user")), "content": str(newest.get("content", ""))}
    )
    return view


def history_policy(
    opening_len: int, continuation_system: str
) -> Callable[[list[dict]], list[dict]]:
    """Bind `compact_view` into the `messages -> wire view` callable the
    adapter takes as `history_policy`."""

    def policy(messages: list[dict]) -> list[dict]:
        return compact_view(
            messages,
            opening_len=opening_len,
            continuation_system=continuation_system,
        )

    return policy
