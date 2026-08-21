"""Transports: the only layer that knows how a model session is driven (`TOOLCALL.md` §4).

A transport turns a message history into one model turn and normalizes it to
`TransportResponse(text, tool_calls)`, where `tool_calls` are canonical OpenAI-format
tool-call dicts (possibly interleaved with parse-error envelopes from `parser.py`). The
agent loop above this module is transport-agnostic; migrating from the interim XML path
to native Ollama tool calling later is a pure transport swap.

- `PromptXmlTransport`: interim path. Sends the conversation as plain messages through an
  injected generate function (e.g. an adapter over `llm7shi`) and parses the XML wire
  format out of the reply.
- `StubTransport`: deterministic scripted responses for tests — no network, no model.
  Scripted raw strings go through the real parser, so tests exercise the actual protocol.

This module never imports llm7shi/ollama itself: backends are injected as callables, so
the library core stays dependency-free and importable in any environment.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Protocol, Sequence

from .parser import parse_tool_calls

__all__ = [
    "PromptXmlTransport",
    "StubTransport",
    "Transport",
    "TransportResponse",
]

Generate = Callable[[list[dict]], str]
"""A stateless text backend: full OpenAI-format message list -> completion text."""


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

    `generate` is any stateless backend taking the full message list and returning the
    completion text (see `harness.toolcall.probe.llm7shi_generate` for the llm7shi
    adapter). The tool specs are not serialized here — embedding them in the system
    prompt is the caller's job (system prompt + `prompts.xml_contract_section()`); they
    are accepted to keep the transport interface identical for the future native path.
    """

    generate: Generate

    def complete(self, messages: list[dict], tools: Sequence[dict]) -> TransportResponse:
        text = self.generate(messages)
        return TransportResponse(text=text, tool_calls=tuple(parse_tool_calls(text)))


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
