# Tool Call Protocol Library (`harness/toolcall/`)

Standalone library implementing [`../TOOLCALL.md`](../TOOLCALL.md): a reliable conversion
from what Gemma can actually produce (prompt-instructed XML) into the OpenAI-compatible
tool-call representation, so the agent loop never knows which transport was used and a
later migration to native Ollama tool calling becomes a pure transport swap.

**Why XML anchors?** Gemma cannot use native tool calling on the Gemini API path and its
structured output is unreliable there. The interim protocol is prompt-driven: the model
emits `<tool_call>` blocks — each containing a single JSON object in native tool-call
shape (`{"name": ..., "arguments": {...}}`) — inside free text; this library extracts
them, executes them through `GrammarToolkit.dispatch()` (unchanged from milestone 1.1),
and renders outcomes back as `<tool_result>` blocks.

## Modules

| Module | Responsibility |
| :--- | :--- |
| `parser.py` | `parse_tool_calls(text)` → canonical OpenAI-format calls + parse-error envelopes; `format_tool_result(outcome)` → `<tool_result>` block |
| `prompts.py` | `XML_CONTRACT` output rules, `few_shot_messages()`, `tool_specs_section(specs)` |
| `transports.py` | `Transport` interface; `PromptXmlTransport` (interim), `StubTransport` (deterministic tests) |
| `loop.py` | `run_tool_loop(...)`: history, turn budget, termination, dispatch/feedback |
| `probe.py` | Live-probe CLI measuring parse success rate against a real model (§5.2 gate) |

Error discipline: nothing here ever raises into the loop — malformed wire input becomes
`{"ok": False, "tool": ..., "error": ...}` envelopes, mirroring `dispatch`, and is fed
back to the model verbatim for self-correction.

Masking discipline: the library core (`parser` / `prompts` / `transports` / `loop`) never
imports runner code or touches Layer 5 gold data — it is protocol plumbing only. Only the
probe CLI imports `GrammarToolkit` so live experiments exercise the real closed toolset.

## Usage

```python
from harness.runner.tools import GrammarToolkit, TOOL_SPECS
from harness.toolcall import (
    PromptXmlTransport, run_tool_loop, xml_contract_section, few_shot_messages,
)

system = grammar_system_prompt + "\n\n" + xml_contract_section()
messages = [{"role": "system", "content": system}, *few_shot_messages(),
            {"role": "user", "content": task}]
result = run_tool_loop(
    transport=PromptXmlTransport(generate=my_llm_adapter),
    toolkit=GrammarToolkit(),
    messages=messages,
    tools=TOOL_SPECS,
    max_turns=8,
)
result.text        # final answer ("" if budget exhausted)
result.outcomes    # every dispatch envelope, in call order
result.messages    # full transcript
```

## Live probe (operator-run)

Measures the §5.2 go/no-go gate (parse success rate ≥ 0.95) over four scripted scenarios:

```bash
uv run python -m harness.toolcall.probe --model ollama:gemma4:31b-it-qat --log probe.jsonl
```

Tests: `tests/test_harness_toolcall.py` — 38 deterministic tests, no network, no model.
