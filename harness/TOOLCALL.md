# Tool Call Protocol: XML Interim with Native Migration Path (`harness/TOOLCALL.md`)

## 1. Status & Scope

**Status: T1–T5 COMPLETE (2026-08-22); T4 live gate PASSED; T5 live parity run PASSED
(twice). Adoption decision: the prompt-instructed XML protocol is the OFFICIAL
production wire format — the Gemini API executes it roughly 3x faster than local
Ollama; native Ollama tool calling stays implemented and gated but is reserved for
comparison experiments.**
The sub-project is a
standalone library between the model and `GrammarToolkit`; nothing in `tools.py` depends
on it, and `GrammarToolkit.dispatch()` is unchanged. The live probe (§5.2) and migration
parity check (§5.3) are executed by the human operator; both measurement scripts ship
with the library (`python -m harness.toolcall.probe` / `python -m harness.toolcall.parity`).

The sub-project delivers one thing: a **reliable conversion from what Gemma can actually
produce (prompt-instructed XML) into the OpenAI-compatible tool-call representation**, so that
the agent loop never knows which transport was used and a later migration to native tool
calling becomes a transport swap with zero loop changes.

### 1.1 Implemented layout (supersedes §4 placement)

| Component | File |
| :--- | :--- |
| `parse_tool_calls` / `format_tool_call` / `format_tool_result` / `is_parse_error` | `harness/toolcall/parser.py` |
| XML output contract + few-shot exchange + `tool_specs_section` | `harness/toolcall/prompts.py` |
| Transport interface, `PromptXmlTransport`, `OllamaNativeTransport`, `StubTransport` | `harness/toolcall/transports.py` |
| Loop, turn budget, `execute_tool_calls`, `LoopResult` | `harness/toolcall/loop.py` |
| Live-probe CLI (T4 measurement script) | `harness/toolcall/probe.py` |
| Migration parity CLI (§5.3, T5) | `harness/toolcall/parity.py` |
| Deterministic tests (§5.1 + T5) | `tests/test_harness_toolcall.py` |

Design decisions taken during implementation (resolving parts of §7):

- **Parse errors are envelopes, not exceptions**: malformed blocks surface as
  `{"ok": False, "tool": ..., "error": ...}` — the same shape as `dispatch` errors — and
  ride through `execute_tool_calls` into `<tool_result ok="false">` feedback verbatim.
- **Parser validates arguments JSON eagerly**; canonical calls out of `parse_tool_calls`
  always carry valid JSON strings.
- **Termination**: a response with zero tool calls ends the loop (final answer);
  `max_turns` exhaustion returns `LoopResult(exhausted=True)`. No dedicated
  `submit_candidate` termination tool — decided against, see §7.1.
- **Multiple calls per turn are allowed** (§7.3): parser preserves order, the loop
  executes sequentially and embeds all `<tool_result>` blocks in one user message.
- **Streaming**: not needed for benchmark runs (§7.2 resolved: non-streaming).
- **Turn-level observability**: `run_tool_loop` records per-turn wall-clock durations
  (`LoopResult.turn_seconds`, propagated into probe/parity/benchmark JSONL records and
  agent traces) and takes an optional `on_turn(turn, response, outcomes)` callback;
  `progress_printer` builds one that prints a stderr line per turn showing each call's
  compact return value (`outcome_brief`) — identical for XML and native calls, since
  outcomes come from the shared loop. `progress_separator` announces each session with
  its `[index/total]` position so multi-hour runs stay navigable, and
  `progress_subseparator` divides a session's named passes with minor `-----` lines
  (parity's xml → native). All live CLIs enable
  both by default. Native-side streaming display comes from
  `parity.ollama_chat(echo=True)`: ollama is driven in stream mode and rendered through
  llm7shi's own `StreamProcessor` — the same 🤔 Thinking / 💡 Answer separation the XML
  side shows, fed from ollama's split fields (`message.thinking` vs `message.content`);
  only the answer text is assembled back into the transport (thoughts are display-only).

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

### 3.1 Wire format — one JSON object per block

```xml
<tool_call>
{"name": "read_unit", "arguments": {"canticle": "inferno", "canto": 1, "line_start": 1}}
</tool_call>
```

Rationale (revised after live probing — see T4 in §6):

- The block body is a **single JSON object in native tool-call shape**: the model writes
  exactly what it would have written for a native call; the tags are only extraction
  anchors that keep extraction robust against surrounding prose and markdown fences.
- Only **one tag pair to close**, and JSON validity already has to hold anyway — the two
  failure modes of the original nested layout (`</name>` / `</arguments>` omissions) are
  structurally eliminated. Live probe run 2 caught Gemma forgetting `</arguments>` on the
  argument-heaviest tool, which motivated this simplification. (The original layout was
  never released, so it was removed outright rather than kept as a tolerated alias.)

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
- Malformed cases (non-object body, missing `"name"`, unparsable JSON, unknown tool
  name) surface as structured per-call errors that the loop feeds back verbatim,
  mirroring `dispatch`'s error envelope — never exceptions across the loop boundary.

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
        ├─ OllamaNativeTransport (native): ollama package directly, native tool_calls
        └─ StubTransport         (tests): scripted responses, fully deterministic
   │
   ▼ OpenAI-format tool_calls (canonical)
GrammarToolkit.dispatch(name, arguments)     ← unchanged from milestone 1.1
```

Placement: implemented as the `harness/toolcall/` library — see §1.1 for the module map
(the per-file split below `runner/` was superseded during implementation).

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

### 5.3 Migration verification (XML → native)

For a fixed sample of units, run both transports and compare the resulting tool-call
sequences (name + parsed arguments) and final candidate rows. Sequences need not be identical
turn-for-turn (the model may behave differently), but the *protocol* is verified by: every
call sequence produced under native mode is accepted unchanged by the same loop under XML
mode's parser, and vice versa via the canonical representation.

Implemented as `harness/toolcall/parity.py` (T5): the hard gate checks that every canonical
call recorded under either transport survives the `format_tool_call` → `parse_tool_calls`
round trip unchanged; call-name sequence and candidate-row equality between transports are
reported observationally, not gated. Each variant gets its idiomatic opening — XML contract
+ few-shot demo vs bare native specs (`ollama.chat(tools=...)`) — so neither side is taught
the other's wire format.

### 5.4 Plan B (fallback if XML compliance is insufficient)

Line-oriented protocol: a `TOOL <name>` line followed by a JSON arguments line; `FINAL` marks
termination. Extracted by regex, maximally tolerant of prose contamination. The same
conversion-layer shape applies (Plan B parser also emits OpenAI-format calls), so switching
protocols later never touches the loop again.

---

## 6. Milestones

- [x] **T1 Parser & formatter**: `parse_tool_calls` / `format_tool_result` + deterministic unit tests. *(Complete 2026-08-22: `harness/toolcall/parser.py`; error envelopes mirror `dispatch`.)*
- [x] **T2 Prompt contract**: system-prompt section instructing the XML format + few-shot exchange. *(Complete 2026-08-22: `harness/toolcall/prompts.py` — `XML_CONTRACT`, `few_shot_messages`, `tool_specs_section`; few-shot kept parse-consistent by test.)*
- [x] **T3 Stub loop**: agent loop over `StubTransport` proving dispatch/feedback convergence deterministically. *(Complete 2026-08-22: `harness/toolcall/loop.py` + `transports.py`; scripted multi-turn convergence against the real `GrammarToolkit`, incl. parse-error recovery, hallucinated-tool feedback, multi-call turns, budget exhaustion — 29 tests, suite 612 passed.)*
- [x] **T4 Live probe**: parse-success-rate measurement over scenarios; go/no-go vs §5.2 gate; document results here. *(Complete 2026-08-22. History: nested-tag format, `ollama:n4:31b-it-qat` — run 1: 10 turns, 1.000; run 2: 10 turns, 0.900 (unclosed `<arguments>`, recovered next turn) → motivated the one-JSON-object format (§3.1). **Final-format pooled run** (`google:gemma-4-31b-it`, `--repeat 5`, log `harness/probe.log`): 20 scenarios, **47 turns, parse success rate 0.9574 — GATE PASS**; 26 calls, 0 hallucinated tools, 0 dispatch errors; failures = 1 malformed-but-recoverable (truncated JSON body, self-corrected in `read_then_validate#1`) + 1 no-call turn (`read_unit#4`, answered in prose). Both classes are prompt-side, not parser-side. Caveats for milestone 1.2: (a) n=47 leaves a wide binomial CI around the 0.95 threshold — keep measuring during benchmark runs; (b) final answers still echo the few-shot demo's 'cammin' content despite contract rule 7 — replace the demonstration with non-colliding content when building the runner prompts.)*
- [x] **T5 `OllamaNativeTransport` + migration parity check (§5.3)**. *(Implemented
  2026-08-22: `transports.OllamaNativeTransport` over an injected chat backend — the
  library core still never imports ollama; `normalize_tool_calls` converts ollama-style
  objects/dicts into canonical dicts with compact JSON-string arguments, error envelopes
  instead of raising. Because the loop keeps only assistant text in transcripts, the
  transport re-attaches each session turn's calls when rebuilding requests — per-
  conversation ledger keyed by transcript identity, opening-prompt demo turns untouched;
  known limitation: nudged resumes start a fresh transcript whose pre-nudge turns keep
  text-only history. `parser.format_tool_call` is the canonical→wire inverse used by the
  parity criterion. `parity.py` runs every probe scenario through both transports with a
  fresh toolkit per session: hard gate = canonical round-trip interop on both sides;
  observational = call-name sequences + final candidate rows; streaming JSONL log like
  the probe. **Live run PASSED** (`ollama:gemma4:31b-it-qat`, `--repeat 3`, log
  `harness/parity.log`): 12 scenarios (4 × 3), **interop 24/24 checks — GATE PASS**;
  observational names-equal 7/12, rows-equal 6/12 (expected to differ across wire
  formats); xml turns=29/calls=18 vs native turns=31/calls=19, 0 parse errors,
  0 exhausted — wall-clock parity too (~148 min total). Fix during bring-up:
  `parity.resolve_ollama_model` strips the CLI's provider prefix before handing the
  name to the native transport (the XML side's llm7shi parses prefixes itself).
  **Second run (same model/--repeat 3, first with per-turn `turn_seconds`)**: interop
  24/24 PASS again; observational names-equal 5/12, rows-equal 4/12 (run-to-run
  variance, not gated). Wall clock xml 3769s vs native 4993s (+32%) — fully explained
  by turn structure, not transport cost: matched first turns are equal (~103–125 s on
  both sides) and same-shape scenarios tie (`search_corpus#1-3` within ±5%); the gap is
  native overshooting the scripted intent (extra `validate_candidate` passes in
  `read_unit#1-3`, +1098 s; a duplicated validation in `read_then_validate#1`, +466 s),
  partly offset by an xml-side duplicate (`read_then_validate#2`, −194 s) and two
  **native empty-response sessions** (`validate_candidate#1/#3`: one turn, zero calls,
  empty final text after ~150 s of generation — protocol-legitimate but would score
  zero downstream; the runner's nudge policy recovers these, so track their occurrence
  rate in milestone 1.4 logs). **Adoption decision (2026-08-22): the Gemini API path
  executes the XML protocol roughly 3x faster than local Ollama, so the XML protocol is
  adopted as the official Stage 1/2 wire format; `OllamaNativeTransport` and this parity
  check remain implemented and gated but are reserved for comparison experiments.**)*

## 7. Open Questions

1. **Streaming**: does the Stage 1 runner need llm7shi-style streaming/statusline output, or is
   non-streaming sufficient for benchmark runs? (Affects how much of llm7shi is worth wrapping.)
2. **Multiple calls per turn**: allow parallel tool calls in one response, or force exactly one
   to keep transcripts simpler? (Native path permits multiple; the prompt contract should match
   whichever is chosen.)

### 7.1 Resolved: no dedicated termination tool (decided 2026-08-29)

Closes the former item 1 (introduce a 4th tool `submit_candidate(...)` that validates
internally and ends the loop on success, vs. reusing `validate_candidate` and treating
validity as implicit acceptance). **Decision: keep the current design — no
`submit_candidate`.** `validate_candidate` already doubles as the de-facto acceptance
gate (`runner/agent.py`'s no-call nudge policy: a final answer with zero successful
`validate_candidate` dispatches earns a protocol reminder; one or more successes let the
loop's natural termination — a response with no tool calls — stand as acceptance). Two
lines of evidence closed the question rather than just deferring it:

- **Error-driven retry already converges without a dedicated tool.** In
  `harness/bench-unit-retry.log` (87 benchmark cases), 14 cases had at least one invalid
  `validate_candidate` call; all of them reached `valid: true` on a later call in the
  same session, with `nudges == 0` throughout — the model reads row-level errors
  (`row[N]: ...`) and self-corrects on the existing stateless contract. A dedicated
  termination tool would not change this path.
- **The natural follow-up — accept already-valid rows and have the model resubmit only
  a diff — was considered and rejected**, for reasons that also bear on why
  `submit_candidate` itself buys nothing:
  1. Some `validate_candidate` checks are not row-local (e.g. slot uniqueness is
     checked per predicate across the whole candidate), so a partial/diff submission
     would need session-side state plus row-identity tracking across edits — real
     complexity for an untested payoff.
  2. Where a candidate is globally misaligned (e.g. `hist-pur09-064`: 6/6 rows wrong,
     30 errors), the whole thing is rejected anyway, so there is no accepted remainder
     to preserve — diffing buys nothing in exactly the case that generates the most
     retries.
  3. Where only one row was wrong (`hist-pur13-133`: 4 rows, 1 error), the *fix* turn
     took longer than the *original* generation turn (182 s vs 145 s), even though only
     one row changed. Turn duration is dominated by the model's reasoning over the
     whole candidate, not by how many characters it emits — so neither a diff-only
     submission nor a dedicated `submit_candidate` tool is expected to shorten the
     turns that actually cost time.

No code change follows from this; it documents why the existing
`validate_candidate`-as-acceptance design is being kept rather than replaced.

---

## 8. Milestone Ledger (archived from `harness/PLAN.md`, 2026-08-24)

Split out when `PLAN.md` was trimmed; content verbatim. Stage-1 milestone
records live in [`STAGE1.md`](STAGE1.md).

**Tool Call Protocol sub-project (`harness/toolcall/`) — T1–T5 COMPLETE, BOTH LIVE GATES
PASSED (T4 probe, T5 parity).**

Gemma cannot use native tool calling on the Gemini API path and its structured output is
unreliable there, so the interim protocol is prompt-instructed `<tool_call>` blocks (one
JSON object per block) converted into OpenAI-compatible tool-call dicts; native Ollama
tool calling is a pure transport swap (`OllamaNativeTransport`, T5). Deliverables:
parser/formatter (`parser.py`), prompt contract + few-shot (`prompts.py`), transports
(`transports.py`), transport-agnostic loop (`loop.py`), live-probe CLI (`probe.py`),
migration-parity CLI (`parity.py`); 74 deterministic tests in
`tests/test_harness_toolcall.py`. Live probing motivated a wire-format simplification
from nested tags to one JSON object per block ([§3.1](#31-wire-format--one-json-object-per-block));
**final-format pooled run on `google:gemma-4-31b-it` (--repeat 5): 20 scenarios, 47
turns, parse success rate 0.957 ≥ 0.95 gate**, 0 hallucinated tools, 0 dispatch errors,
both observed failure classes benign and prompt-side.

**T5 — Native Transport & Migration Parity (`toolcall/transports.py`,
`toolcall/parity.py`): COMPLETE — live parity run PASSED (2026-08-22).**

- `OllamaNativeTransport` drives an injected chat backend (`(messages, tools) -> message`;
  the library core still never imports ollama — the live adapter lives in
  `parity.ollama_chat` over `ollama.chat(tools=...)`). `normalize_tool_calls` converts
  ollama-style tool-call objects/dicts into canonical dicts with compact JSON-string
  arguments; anything malformed surfaces as a structured error envelope, never a raise.
  Because the loop keeps only assistant *text* in transcripts, the transport re-attaches
  each session turn's calls when rebuilding requests (per-conversation ledger keyed by
  transcript identity; opening-prompt demo turns untouched; nudged resumes start fresh
  transcripts and keep text-only pre-nudge history — documented limitation).
- `parser.format_tool_call(call)` is the canonical→wire inverse; together with
  `parse_tool_calls` it backs the §5.3 interop criterion.
- `parity.py`: runs every probe scenario through both transports (fresh toolkit per
  session; XML side gets contract + demo, native side bare specs). Hard gate = canonical
  round-trip interop on both sides (`ParityReport.parity_pass`); observational =
  call-name sequences + final candidate rows. Streaming JSONL log mirrors the probe.
- **Live verdict (2026-08-22, `ollama:gemma4:31b-it-qat`, `--repeat 3`)**: 12 scenarios,
  interop 24/24 checks — PASS; names-equal 7/12, rows-equal 6/12 (observational);
  xml turns=29/calls=18 vs native turns=31/calls=19, 0 parse errors, 0 exhausted,
  ~148 min wall clock. Bring-up fix: `resolve_ollama_model` strips the CLI provider
  prefix before it reaches the native transport. **Second run** (first with per-turn
  `turn_seconds`): interop 24/24 again; native +32% wall clock fully explained by extra
  validation turns (matched turns are equally fast) plus a native-only empty-response
  pattern; observational equality fluctuates between runs (names 5/12, rows 4/12).
  **Adoption decision: XML is the official wire format (Gemini API ≈3x faster than
  local); native stays for comparison experiments.**
- Tests: 25 new deterministic tests (normalization, history re-attachment, ledger
  isolation, round-trip property, end-to-end stubbed parity); suite total 688 passed.
