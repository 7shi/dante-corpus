"""Prompt-side contract for the interim XML tool-call protocol (`TOOLCALL.md` §3, T2).

The model is *instructed* to speak the `<tool_call>` wire format; `parser.py` is the
tolerant counterpart that extracts whatever comes back. The contract is importable
independently of any transport or loop so the Stage 1 runner can embed it into its own
5-step reasoning system prompt.

`few_shot_messages()` returns a minimal user/assistant/user exchange demonstrating one
tool call and its result handling; it is kept parse-consistent with `parser.py` by test.
"""

from __future__ import annotations

import json
from typing import Sequence

__all__ = [
    "XML_CONTRACT",
    "few_shot_messages",
    "tool_specs_section",
    "xml_contract_section",
]

XML_CONTRACT = """\
## Tool call protocol

You interact with the corpus exclusively through the tools described below. To call a \
tool, emit a `<tool_call>` block whose entire content is a single JSON object with \
"name" and "arguments":

<tool_call>
{"name": "tool_name", "arguments": {"json": "object matching the tool's parameters"}}
</tool_call>

Rules:

1. The block contains only that JSON object — nothing else, no other tags inside. Write \
"arguments" exactly as you would for a native function call.
2. You may emit several `<tool_call>` blocks in one response; they execute in order and \
you receive one `<tool_result>` per block, in order.
3. After tool-call turns you receive results as `<tool_result>` blocks (ok="true" or \
ok="false"). Read ok="false" payloads as corrections: fix the specific problem they name \
and call again.
4. Do not wrap blocks in markdown code fences.
5. Use only the tools listed below — never invent tool names or parameters.
6. A response containing no `<tool_call>` block at all is understood as your final \
answer: emit calls until your work is done, then answer in plain prose.
7. Any demonstration exchanges are format illustrations only — never reuse their \
content or results in your own work."""


def xml_contract_section() -> str:
    """The protocol section to append to a system prompt."""
    return XML_CONTRACT


def tool_specs_section(specs: Sequence[dict]) -> str:
    """Render OpenAI-format tool specs as the "Available tools" prompt section.

    Accepts the full `{"type": "function", "function": {...}}` specs (e.g.
    `runner.tools.TOOL_SPECS`) and lists the function objects, which carry name,
    description, and JSON-Schema parameters.
    """
    functions = [spec.get("function", spec) for spec in specs]
    body = json.dumps(functions, ensure_ascii=False, indent=2)
    return f"## Available tools\n\n```json\n{body}\n```"


def few_shot_messages() -> list[dict]:
    """A minimal demonstration exchange (user task -> assistant tool call -> result).

    Insert after the system prompt and before the real conversation. The assistant turn
    intentionally shows prose reasoning around the block, mirroring what CoT output
    looks like, and stays parse-consistent with `parser.parse_tool_calls`.
    """
    return [
        {
            "role": "user",
            "content": (
                "<task>\n"
                "Find where the lemma 'cammin' occurs outside this canto.\n"
                "</task>"
            ),
        },
        {
            "role": "assistant",
            "content": (
                "I will search other cantos for this lemma.\n"
                "<tool_call>\n"
                '{"name": "search_corpus", '
                '"arguments": {"query": {"lemma": "cammin"}, "limit": 5}}\n'
                "</tool_call>"
            ),
        },
        {
            "role": "user",
            "content": (
                '<tool_result tool="search_corpus" ok="true">\n'
                '[{"canticle": "inferno", "canto": 2, "line": 1, "token": 11, '
                '"word": "cammin", "lemma": "cammino", "pos": "noun"}]\n'
                "</tool_result>"
            ),
        },
    ]
