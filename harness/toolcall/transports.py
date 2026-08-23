"""Transports: the only layer that knows how a model session is driven (`TOOLCALL.md` §4).

A transport turns a message history into one model turn and normalizes it to
`TransportResponse(text, tool_calls)`, where `tool_calls` are canonical OpenAI-format
tool-call dicts (possibly interleaved with parse-error envelopes from `parser.py`). The
agent loop above this module is transport-agnostic: swapping the interim XML path for
native Ollama tool calling touches only this layer.

- `PromptXmlTransport`: interim path. Sends the conversation as plain messages through an
  injected generate function (e.g. an adapter over `llm7shi`) and parses the XML wire
  format out of the reply.
- `OllamaNativeTransport`: native path. Sends the conversation through an injected chat
  backend (e.g. an adapter over the `ollama` package's `chat(tools=...)`) and normalizes
  the response's native tool calls into the same canonical dicts. Because the loop keeps
  only assistant *text* in the transcript, this transport re-attaches each session turn's
  calls when rebuilding the request, so the model sees its own call structure in history.
- `StubTransport`: deterministic scripted responses for tests — no network, no model.
  Scripted raw strings go through the real parser, so tests exercise the actual protocol.

This module never imports llm7shi/ollama itself: backends are injected as callables, so
the library core stays dependency-free and importable in any environment.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Callable, Protocol, Sequence

from .parser import parse_tool_calls

__all__ = [
    "ChatFn",
    "OllamaNativeTransport",
    "PromptXmlTransport",
    "StubTransport",
    "Transport",
    "TransportResponse",
    "normalize_tool_calls",
]

Generate = Callable[[list[dict]], str]
"""A text backend: full OpenAI-format message list -> completion text.

Usually stateless (each call resends the whole conversation); a stateful
adapter that mirrors the transcript into its own client (e.g. `runner.agent.
llm7shi_generate` over `llm7shi.Client`'s history + quality-retry loop) is
fine too — the transport only ever calls it with the loop's transcript.
"""

ChatFn = Callable[[Sequence[dict], Sequence[dict]], Any]
"""A native chat backend: `(messages, tools) -> response message`.

The message carries the model turn in native shape: text under `.content`
(attribute or mapping access) and native tool calls under `.tool_calls`. See
`harness.toolcall.parity.ollama_chat` for the live adapter over the `ollama`
package; tests inject deterministic fakes.
"""


@dataclass(frozen=True)
class TransportResponse:
    """One normalized model turn."""

    text: str
    # Canonical OpenAI-format tool-call dicts; may include parse-error envelopes
    # ({"ok": False, ...}) which the loop feeds back like dispatch errors.
    tool_calls: tuple[dict, ...] = ()


class Transport(Protocol):
    def complete(self, messages: list[dict], tools: Sequence[dict]) -> TransportResponse:
        """Produce one assistant turn for `messages`, aware of the closed `tools` surface."""
        ...


@dataclass
class PromptXmlTransport:
    """Interim transport: prompt-instructed XML parsed into canonical tool calls.

    `generate` is any backend taking the full message list and returning the
    completion text (see `harness.toolcall.probe.llm7shi_generate` for the
    stateless llm7shi adapter, `runner.agent.llm7shi_generate` for the stateful
    Client-based one; `reset()` forwards to backends exposing it). The tool
    specs are not serialized here — embedding them in the system prompt is the
    caller's job (system prompt + `prompts.xml_contract_section()`); they are
    accepted to keep the transport interface identical for the native path.
    """

    generate: Generate

    def complete(self, messages: list[dict], tools: Sequence[dict]) -> TransportResponse:
        text = self.generate(messages)
        return TransportResponse(text=text, tool_calls=tuple(parse_tool_calls(text)))

    def reset(self) -> None:
        """Signal a session boundary: a generate backend keeping per-session
        state (`runner.agent.llm7shi_generate`'s Client mirror) starts fresh on
        the next call. Stateless backends need no `reset` attribute at all."""
        reset = getattr(self.generate, "reset", None)
        if callable(reset):
            reset()


def _error(name: str, message: str) -> dict:
    """A parse-error envelope shaped exactly like `GrammarToolkit.dispatch`'s."""
    return {"ok": False, "tool": name, "error": message}


def _get_field(message: Any, name: str) -> Any:
    """Read `name` off a response message via attribute or mapping access."""
    if isinstance(message, dict):
        return message.get(name)
    return getattr(message, name, None)


def normalize_tool_calls(items: Sequence[Any]) -> list[dict]:
    """Normalize native tool-call items into canonical OpenAI-format dicts.

    Accepts what real backends put on a response message: ollama-style objects with
    `.function.name` / `.function.arguments`, plain dicts of the same shape, and
    already-canonical dicts with JSON-string arguments. `arguments` mappings are
    serialized to compact JSON (non-ASCII kept literal); anything that cannot be
    converted — missing/blank name, non-object arguments — surfaces as a structured
    error envelope instead of raising, mirroring the parser's discipline.
    """
    canonical: list[dict] = []
    for item in items:
        function = _get_field(item, "function")
        if function is None and isinstance(item, dict) and "function" not in item:
            function = item  # tolerate flat dicts: {"name": ..., "arguments": ...}
        if isinstance(function, dict):
            name = function.get("name")
            arguments = function.get("arguments", {})
        else:
            name = _get_field(function, "name")
            arguments = _get_field(function, "arguments")
        if not isinstance(name, str) or not name.strip():
            canonical.append(
                _error("", f"native tool call without a usable name: {item!r}")
            )
            continue
        name = name.strip()
        if isinstance(arguments, str):
            try:
                arguments_obj = json.loads(arguments)
            except json.JSONDecodeError as exc:
                canonical.append(
                    _error(
                        name,
                        f"tool call {name!r} has unparsable arguments JSON ({exc})",
                    )
                )
                continue
        elif isinstance(arguments, dict):
            arguments_obj = arguments
        else:
            canonical.append(
                _error(
                    name,
                    f"tool call {name!r}: arguments must be an object, "
                    f"got {type(arguments).__name__}",
                )
            )
            continue
        canonical.append(
            {
                "type": "function",
                "function": {
                    "name": name,
                    "arguments": json.dumps(arguments_obj, ensure_ascii=False),
                },
            }
        )
    return canonical


def _native_history_call(call: dict) -> dict | None:
    """Reshape one canonical call for re-attachment on an assistant history message.

    Ollama's request schema wants assistant `tool_calls` entries as
    `{"function": {"name": ..., "arguments": <object>}}`; the canonical JSON-string
    form is decoded back to an object here. Returns None for error envelopes.
    """
    if call.get("ok") is False or call.get("type") != "function":
        return None
    try:
        arguments_obj = json.loads(call["function"].get("arguments", "{}"))
    except (KeyError, TypeError, json.JSONDecodeError):
        return None
    return {
        "function": {"name": call["function"]["name"], "arguments": arguments_obj}
    }


@dataclass
class OllamaNativeTransport:
    """Native transport over an injected chat backend (`TOOLCALL.md` T5).

    `chat(messages, tools)` returns one response message in native shape (see
    `ChatFn`). The loop keeps only assistant *text* in the transcript, so this
    transport remembers each session turn's calls per conversation — keyed by the
    transcript list identity, which is stable for a conversation's lifetime — and
    re-attaches them when rebuilding subsequent requests; opening-prompt assistant
    messages (the few-shot demo) stay untouched. Conversations are sequential
    (one shared transport drives sessions one at a time), so a dead conversation's
    id is never seen again.

    Known limitation: when the runner nudges a no-call session it resumes through a
    fresh transcript copy, whose pre-nudge turns therefore keep text-only history.
    """

    chat: ChatFn
    _openings: dict[int, int] = field(default_factory=dict, init=False)
    _turns: dict[int, list[list[dict]]] = field(default_factory=dict, init=False)

    def complete(self, messages: list[dict], tools: Sequence[dict]) -> TransportResponse:
        key = id(messages)
        if key not in self._openings:
            self._openings[key] = sum(
                1 for m in messages if m.get("role") == "assistant"
            )
        turn_calls = self._turns.setdefault(key, [])

        rebuilt: list[dict] = []
        session_index = 0
        for message in messages:
            if message.get("role") != "assistant":
                rebuilt.append(dict(message))
                continue
            offset = session_index - self._openings[key]
            session_index += 1
            attached: list[dict] = []
            if 0 <= offset < len(turn_calls):
                attached = [
                    shaped
                    for call in turn_calls[offset]
                    if (shaped := _native_history_call(call))
                ]
            if attached:
                rebuilt.append({**message, "tool_calls": attached})
            else:
                rebuilt.append(dict(message))

        raw_message = self.chat(rebuilt, tools)
        calls = normalize_tool_calls(_get_field(raw_message, "tool_calls") or ())
        turn_calls.append(calls)
        text = _get_field(raw_message, "content") or ""
        return TransportResponse(text=text, tool_calls=tuple(calls))

    def reset(self) -> None:
        """Drop the re-attachment ledgers of finished conversations.

        Keys are transcript `id()`s that a sequential run never revisits, so
        the entries would only accumulate memory; a session boundary is the
        natural flush point.
        """
        self._openings.clear()
        self._turns.clear()


@dataclass
class StubTransport:
    """Scripted responses consumed in order; fully deterministic.

    Each script item is either

    - a raw model string — routed through the real `parse_tool_calls`, so stub tests
      exercise the actual wire format, or
    - a dict with explicit `"text"` and/or `"tool_calls"` (canonical dicts), bypassing
      the parser for cases where the test wants to script the canonical representation
      directly (as a native transport would deliver it).

    Raises `StopIteration` when the script runs dry — a looping test is a broken script.
    """

    script: Sequence[str | dict]
    _cursor: int = field(default=0, init=False)

    def complete(self, messages: list[dict], tools: Sequence[dict]) -> TransportResponse:
        if self._cursor >= len(self.script):
            raise StopIteration(
                f"StubTransport script exhausted after {self._cursor} turn(s)"
            )
        item = self.script[self._cursor]
        self._cursor += 1
        if isinstance(item, str):
            return TransportResponse(
                text=item, tool_calls=tuple(parse_tool_calls(item))
            )
        return TransportResponse(
            text=item.get("text", ""),
            tool_calls=tuple(item.get("tool_calls", ())),
        )
