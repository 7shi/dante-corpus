"""Wire-format conversion between model text and the canonical tool-call representation.

Implements `harness/TOOLCALL.md` §3: Gemma cannot use native tool calling on the Gemini
API path, so the interim protocol is prompt-instructed `<tool_call>` blocks embedded in
free text. The block body is a single JSON object in native tool-call shape:

    <tool_call>
    {"name": "read_unit", "arguments": {"canticle": "inferno", "canto": 1}}
    </tool_call>

One tag pair to close and a native-shaped payload — the two things the model already
has to get right anyway. This module is the only place that knows that format:

- `parse_tool_calls(text)` converts model output into OpenAI-compatible tool-call dicts
  (the same shape ollama/OpenAI put on `message.tool_calls`), so the agent loop and
  `GrammarToolkit.dispatch()` never learn which transport was used.
- `format_tool_result(outcome)` renders a dispatch outcome envelope as a `<tool_result>`
  block for the next user message.

Error discipline mirrors `dispatch`: malformed input (unparsable JSON, missing name,
unterminated block) never raises; it surfaces as a structured per-call error envelope
(`{"ok": False, "tool": ..., "error": ...}`) that the loop feeds back verbatim.

Content inside `<tool_result>` blocks is emitted verbatim (no XML escaping): these blocks
are read by the model as plain text, never re-parsed by this library.
"""

from __future__ import annotations

import json

__all__ = [
    "TOOL_CALL_CLOSE",
    "TOOL_CALL_OPEN",
    "format_tool_call",
    "format_tool_result",
    "is_parse_error",
    "parse_tool_calls",
]

TOOL_CALL_OPEN = "<tool_call>"
TOOL_CALL_CLOSE = "</tool_call>"

# Error envelopes quote raw model output; keep them readable in the transcript.
_RAW_SNIPPET_LIMIT = 200


def _snippet(raw: str) -> str:
    raw = " ".join(raw.split())
    if len(raw) > _RAW_SNIPPET_LIMIT:
        raw = raw[:_RAW_SNIPPET_LIMIT] + "..."
    return raw


def _error(name: str, message: str) -> dict:
    """A parse-error envelope shaped exactly like `GrammarToolkit.dispatch`'s."""
    return {"ok": False, "tool": name, "error": message}


def is_parse_error(item: dict) -> bool:
    """True for a parse-error envelope (as opposed to a canonical tool-call dict)."""
    return item.get("ok") is False


def _canonical(name: str, arguments: str) -> dict:
    return {"type": "function", "function": {"name": name, "arguments": arguments}}


def _json_object_body(body: str) -> dict | None:
    """Parse the block body as a JSON object; tolerate prose wrapped around it."""
    candidates = [body]
    start, end = body.find("{"), body.rfind("}")
    if 0 <= start < end:
        candidates.insert(0, body[start : end + 1])
    for candidate in candidates:
        try:
            obj = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(obj, dict):
            return obj
    return None


def _parse_json_body(raw: str, items: list[dict]) -> None:
    """Parse the block body as one JSON object with "name"/"arguments"."""
    obj = _json_object_body(raw.strip())
    if obj is None:
        items.append(
            _error(
                "",
                '<tool_call> content must be a single JSON object '
                '{"name": ..., "arguments": {...}}: ' + _snippet(raw),
            )
        )
        return

    name = obj.get("name")
    if not isinstance(name, str) or not name.strip():
        items.append(
            _error(
                "",
                '<tool_call> JSON object needs a string "name" field: ' + _snippet(raw),
            )
        )
        return
    name = name.strip()

    arguments = obj.get("arguments", {})
    if isinstance(arguments, dict):
        arguments_text = json.dumps(arguments, ensure_ascii=False)
    elif isinstance(arguments, str):
        arguments_text = arguments.strip()
    else:
        items.append(
            _error(
                name,
                f'tool call {name!r}: "arguments" must be a JSON object '
                f"(or a JSON string), got {type(arguments).__name__}",
            )
        )
        return

    try:
        json.loads(arguments_text)
    except json.JSONDecodeError as exc:
        items.append(
            _error(
                name,
                f"tool call {name!r} has unparsable arguments JSON ({exc}): "
                f"{_snippet(arguments_text)}",
            )
        )
        return

    items.append(_canonical(name, arguments_text))


def parse_tool_calls(text: str) -> list[dict]:
    """Extract every `<tool_call>` block from model output.

    Returns a list whose items are either

    - a canonical OpenAI-format tool-call dict
      ``{"type": "function", "function": {"name": ..., "arguments": <JSON str>}}``
      with `arguments` guaranteed to be valid JSON (a JSON-object ``arguments`` field is
      re-serialized compactly; whitespace inside the block is normalized away; a missing
      ``arguments`` field defaults to ``{}``), or
    - a parse-error envelope ``{"ok": False, "tool": ..., "error": ...}`` for a block
      that could not be converted (missing name, non-object body, unparsable JSON,
      unterminated block).

    Zero blocks (pure thinking/final-answer text) yields an empty list. Prose and
    markdown code fences around blocks — and prose wrapped around the JSON body inside
    a block — are tolerated and ignored. Duplicate tool names across blocks are kept:
    they are distinct calls under the native convention.
    """
    items: list[dict] = []
    segments = text.split(TOOL_CALL_OPEN)
    for segment in segments[1:]:
        raw, close, _tail = segment.partition(TOOL_CALL_CLOSE)
        if not close:
            items.append(
                _error(
                    "",
                    "unterminated <tool_call> block (missing </tool_call>): "
                    f"{_snippet(raw)}",
                )
            )
            continue
        _parse_json_body(raw, items)
    return items


def format_tool_call(call: dict) -> str:
    """Render one canonical tool-call dict as a `<tool_call>` block.

    The inverse of `parse_tool_calls` for a single well-formed call: canonical
    OpenAI-format dicts — as produced by this parser, by native transports, or by
    real ollama/OpenAI responses — come back as a wire block whose re-parse yields
    the identical canonical dict (`TOOLCALL.md` §5.3 interop criterion). The block
    body is compact JSON with non-ASCII characters kept literal (the corpus is
    Italian). Raises ValueError for a call that is not canonically shaped with
    JSON-object arguments — a programmer error on this side of the wire, never a
    model-output condition.
    """
    function = call.get("function", {})
    name = function.get("name")
    arguments = function.get("arguments", {})
    if not isinstance(name, str) or not name.strip():
        raise ValueError(f"canonical tool call needs a string name: {call!r}")
    if isinstance(arguments, str):
        try:
            arguments_obj = json.loads(arguments)
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"canonical tool call {name!r} has unparsable arguments JSON: {exc}"
            ) from exc
    else:
        arguments_obj = arguments
    if not isinstance(arguments_obj, dict):
        raise ValueError(
            f"canonical tool call {name!r} arguments must be a JSON object, "
            f"got {type(arguments_obj).__name__}"
        )
    body = json.dumps({"name": name, "arguments": arguments_obj}, ensure_ascii=False)
    return f"{TOOL_CALL_OPEN}\n{body}\n{TOOL_CALL_CLOSE}"


def format_tool_result(outcome: dict) -> str:
    """Render one dispatch outcome envelope as a `<tool_result>` block.

    `outcome` is `{"ok": True, "tool": ..., "result": ...}` from a successful
    `GrammarToolkit.dispatch`, `{"ok": False, "tool": ..., "error": ...}` from a
    rejected one, or a parse-error envelope of the same shape. The payload is compact
    JSON with non-ASCII characters kept literal (the corpus is Italian).
    """
    ok = bool(outcome.get("ok"))
    tool = str(outcome.get("tool", ""))
    if ok:
        payload = json.dumps(outcome.get("result"), ensure_ascii=False, sort_keys=True)
    else:
        payload = json.dumps({"error": str(outcome.get("error", ""))}, ensure_ascii=False)
    return (
        f'<tool_result tool="{tool}" ok="{"true" if ok else "false"}">\n'
        f"{payload}\n"
        f"</tool_result>"
    )
