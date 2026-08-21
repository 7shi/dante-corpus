"""Tool Call Protocol library: XML interim with a native migration path.

Implements `harness/TOOLCALL.md` as a standalone, dependency-free layer between the
model and `GrammarToolkit`:

- `parser`: `<tool_call>` wire format <-> canonical OpenAI-format tool-call dicts,
  plus `<tool_result>` rendering of dispatch outcome envelopes.
- `prompts`: the prompt-side output contract and few-shot exchange.
- `transports`: the transport interface (`PromptXmlTransport`, `StubTransport`; native
  Ollama tool calling later is a pure transport swap).
- `loop`: the transport-agnostic multi-turn loop (history, turn budget, termination).

The Stage 1 runner (`harness/runner`) consumes this library; nothing here imports
runner code or touches Layer 5 gold data.
"""

from .loop import LoopResult, execute_tool_calls, run_tool_loop
from .parser import (
    format_tool_result,
    is_parse_error,
    parse_tool_calls,
)
from .prompts import (
    XML_CONTRACT,
    few_shot_messages,
    tool_specs_section,
    xml_contract_section,
)
from .transports import (
    PromptXmlTransport,
    StubTransport,
    Transport,
    TransportResponse,
)

__all__ = [
    "LoopResult",
    "PromptXmlTransport",
    "StubTransport",
    "Transport",
    "TransportResponse",
    "XML_CONTRACT",
    "execute_tool_calls",
    "few_shot_messages",
    "format_tool_result",
    "is_parse_error",
    "parse_tool_calls",
    "run_tool_loop",
    "tool_specs_section",
    "xml_contract_section",
]
