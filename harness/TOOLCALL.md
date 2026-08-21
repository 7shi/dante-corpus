# Tool Call Protocol: XML Interim with Native Migration Path (`harness/TOOLCALL.md`)

## 1. Status & Scope

**Status: PLAN ONLY — implementation deferred.** This is a standalone sub-project to be
designed, built, and validated independently of the Stage 1 agent loop (`harness/runner/PLAN.md`
§4 / milestone 1.2). Nothing in `tools.py` depends on it yet; `GrammarToolkit` and
`GrammarToolkit.dispatch()` are already final and protocol-agnostic.

The sub-project delivers one thing: a **reliable conversion from what Gemma can actually
produce (prompt-instructed XML) into the OpenAI-compatible tool-call representation**, so that
the agent loop never knows which transport was used and a later migration to native tool
calling becomes a transport swap with zero loop changes.

---

## 2. Background & Constraints

| Path | Tool calling | Structured output | Notes |
| :--- | :--- | :--- | :--- |
| Gemini API (gemma) | **Unavailable for gemma models** despite the API supporting tools natively | **Unreliable in practice** | Cannot be used as the mechanism |
| Ollama (`ollama:gemma4:31b-it-qat`) | Works via the `ollama` Python package directly (`chat(tools=...)`) | Works fine | llm7shi's `Client.__call__` has fixed parameters and does not forward `tools`; bypassing llm7shi is required |
| `llm7shi.Client` | Not exposed | `schema=` → `response_format: json_schema` only | Wraps Ollama/OpenAI/Gemini; no `tool_calls` handling anywhere |

Consequences:

1. The interim protocol must be **prompt-driven**: the model is instructed to emit tool calls
   as XML inside free text.
2. The design must keep the door open for **native tool calling on the Ollama path**
   (direct use of the wrapped `ollama` package) without touching agent-loop code.
3. Free-form bash execution remains forbidden; the model may only speak through the closed
   tool surface (`TOOL_SPECS` in `tools.py`: `read_unit`, `search_corpus`, `validate_candidate`,
   plus the proposed `submit_candidate`, see §7).

---

## 3. Protocol Design (Interim: XML)

### 3.1 Wire format — JSON-in-XML

```xml
<tool_call>
  <name>read_unit</name>
  <arguments>{"canticle": "inferno", "canto": 1, "line_start": 1}</arguments>
</tool_call>
```

Rationale:

- **Arguments stay JSON inside `<arguments>` tags** rather than being expanded into pure XML.
  Skeleton rows (`candidate_rows`) are arrays of objects; expressing them in pure XML would be
  verbose and error-prone. With JSON-in-XML, the model writes exactly the JSON it would have
  written for a native tool call — the tags are only extraction anchors.
- Tags make extraction robust against surrounding prose and markdown code fences, which must be
  assumed present even when the prompt forbids them.

### 3.2 Canonical internal representation

`parse_tool_calls(text)` converts model output into **OpenAI-compatible tool-call dicts** — the
same shape ollama/OpenAI put on `message.tool_calls`:

```python
[{
    "type": "function",
    "function": {
        "name": "read_unit",
        "arguments": "{\"canticle\": \"inferno\", \"canto\": 1, \"line_start\": 1}",
    },
}]
```

- `arguments` remains a JSON **string** (native convention); parsing it is already
  `GrammarToolkit.dispatch()`'s job — no double parsing logic.
- Zero or more `<tool_call>` blocks are accepted. Zero calls = pure thinking text → nudge or
  turn-budget handling by the loop.
- Malformed cases (unparsable arguments JSON, missing `<name>`, unknown tool name) surface as
  structured per-call errors that the loop feeds back verbatim, mirroring `dispatch`'s error
  envelope — never exceptions across the loop boundary.

### 3.3 Results back to the model

`format_tool_result(call, result)` renders each dispatch outcome as a `<tool_result>` block
appended to the conversation (interim path embeds these in the next user message):

```xml
<tool_result tool="read_unit" ok="true">
{"unit": {"canticle": "inferno", ...}}
</tool_result>
```

Errors use `ok="false"` and carry the human-readable correction text from the dispatch
envelope, driving the Step-5 self-correction loop of the reasoning protocol.

---

## 4. Architecture

```
agent.py loop (transport-agnostic: history, turn budget, termination)
   │
   ▼ complete(messages, tools) -> {text, tool_calls}      ← Transport interface
        ├─ PromptXmlTransport    (interim): prompt contract + parse_tool_calls()
        ├─ OllamaNativeTransport (future): ollama package directly, native tool_calls
        └─ StubTransport         (tests): scripted responses, fully deterministic
   │
   ▼ OpenAI-format tool_calls (canonical)
GrammarToolkit.dispatch(name, arguments)     ← unchanged from milestone 1.1
```

Placement:

| Component | File |
| :--- | :--- |
| `parse_tool_calls` / `format_tool_result` (pure functions) | `harness/runner/tools.py` (or a sibling `toolcalls.py` if tools.py grows too large) |
| XML output-contract prompt + few-shot example | `harness/runner/prompts.py` |
| Transports + loop + turn budget | `harness/runner/agent.py` |

---

## 5. Validation Plan (Independent Sub-Project)

The protocol is validated on its own before being wired into the Stage 1 runner.

### 5.1 Deterministic layer (no LLM, joins the 547-test suite)

- `parse_tool_calls`: bare call, prose-wrapped call, fenced code block, multiple calls,
  zero calls, unparsable arguments JSON, missing name, duplicate names.
- `format_tool_result`: success envelope, error envelope, non-ASCII content, round-trip
  stability.
- Transport stub: scripted multi-turn sequences converge through the real loop code with
  `StubTransport` — no network, no model.

### 5.2 Live probe (real Gemma, small scale)

Run over the challenge fixtures (§5 of the Stage 1 plan, once curated) or an initial sample of
units:

- **Primary metric — parse success rate**: fraction of turns where at least one well-formed
  tool call is extractable. Target ≥ 95% before wiring into Stage 1.
- **Secondary metrics**: malformed-but-recoverable rate (fixed by one feedback turn),
  hallucinated-tool rate, arguments-type-error rate tolerated by `dispatch` coercion.
- **Decision gate**: below target, fall back to **Plan B** (§6).

### 5.3 Migration verification (XML → native, later)

For a fixed sample of units, run both transports and compare the resulting tool-call
sequences (name + parsed arguments) and final candidate rows. Sequences need not be identical
turn-for-turn (the model may behave differently), but the *protocol* is verified by: every
call sequence produced under native mode is accepted unchanged by the same loop under XML
mode's parser, and vice versa via the canonical representation.

### 5.4 Plan B (fallback if XML compliance is insufficient)

Line-oriented protocol: a `TOOL <name>` line followed by a JSON arguments line; `FINAL` marks
termination. Extracted by regex, maximally tolerant of prose contamination. The same
conversion-layer shape applies (Plan B parser also emits OpenAI-format calls), so switching
protocols later never touches the loop again.

---

## 6. Milestones

- [ ] **T1 Parser & formatter**: `parse_tool_calls` / `format_tool_result` + deterministic unit tests.
- [ ] **T2 Prompt contract**: system-prompt section instructing the XML format + few-shot exchange (in `prompts.py`, importable independently).
- [ ] **T3 Stub loop**: minimal agent loop over `StubTransport` proving dispatch/feedback convergence deterministically.
- [ ] **T4 Live probe**: parse-success-rate measurement script over fixtures; go/no-go vs §5.2 gate; document results here.
- [ ] **T5 (deferred)** `OllamaNativeTransport` + migration parity check (§5.3).

## 7. Open Questions

1. **Termination tool**: introduce a 4th tool `submit_candidate(...)` (validates internally,
   accepts on valid → loop ends; returns errors otherwise), keeping termination uniform across
   XML and native paths? Alternative: reuse `validate_candidate` and treat validity as implicit
   acceptance.
2. **Streaming**: does the Stage 1 runner need llm7shi-style streaming/statusline output, or is
   non-streaming sufficient for benchmark runs? (Affects how much of llm7shi is worth wrapping.)
3. **Multiple calls per turn**: allow parallel tool calls in one response, or force exactly one
   to keep transcripts simpler? (Native path permits multiple; the prompt contract should match
   whichever is chosen.)
