# Grammar Agent Harness: Overall Architecture & Master Plan

## 1. Overview & Paradigm Shift: Generalizable Layer 5 Reconstruction

`harness/` is a dedicated **Grammar Agent Harness for Local LLMs** (e.g., **Gemma 4 31B**), designed to systematically reconstruct Layer 5 predicate-argument skeletons (`skel/`) from multi-layer grammatical contexts (Layer 1 text/tokens, quotes hierarchy, Layer 2 morphology, pronoun case annex, Layer 3 noun phrase spans, and Layer 4 Universal Dependencies syntax trees).

### Motivation & Rationale
1. **Historical Context & Limitations of `skel/`**:
   - Layer 5 (`skel/`) was historically constructed through Phases 5–7 using an interactive, semi-manual process: a frontier LLM (Claude Opus 5, later switched to Gemini 3.7 Flash at the end of Phase 8) and human operators iteratively triaged outlier positions to formulate 130 deterministic rules (Rules A–EI).
   - Although this successfully produced a 100% clean corpus (**0 hard / 0 soft violations across all 100 cantos**, 547 pytest passing), the **construction methodology itself was ad hoc, bespoke to Dante's Italian, and insufficiently automated**.
   - As a result, the Phase 5–8 methodology cannot be directly generalized to other texts, genres, or languages (such as Latin).
2. **Mission of `harness/`**:
   - `harness/` solves this limitation by creating a **reproducible, fully automated, and generalizable reconstruction pipeline**.
   - Preserving `skel/` as an **immutable Gold Standard (Ground Truth)** for benchmark evaluation, `harness/` demonstrates how local LLMs can autonomously project Layer 4 UD syntax onto predicate-argument frames (Stage 1) and empirically induce syntax rules and valency lexicons (Stage 2).

```mermaid
graph TD
    subgraph "Dante Corpus (Ground Truth Layers)"
        L1["Layer 1: Tokens / Texts"]
        L2["Layer 2: Morphology + Case"]
        L3["Layer 3: Noun Phrases"]
        L4["Layer 4: UD Syntax Trees"]
        L5_Gold["Layer 5: skel/ (0-Soft Gold Reference, 547 tests)"]
    end

    subgraph "harness/ (Two-Stage Bottom-Up Architecture)"
        L1 & L2 & L3 & L4 --> Stage1["Stage 1: Autonomous Inference (runner/)<br/>・Dedicated Grammar Toolset<br/>・Multi-Layer CoT Reasoning<br/>・Syntactic Challenge Benchmark"]
        
        Stage1 --> Logs["Execution Logs & Reasoning Traces<br/>(Exact matches, ambiguities, lexical decisions)"]
        
        Logs --> Stage2["Stage 2: Bottom-Up Extraction (extractor/)<br/>・Syntax Pattern Mining (Deterministic Fast Path)<br/>・Verb Valency / Lexicon Profile Extraction<br/>・Hybrid Execution Engine (Fast-path + Fallback)"]
        
        Stage2 --> GatedBuild["Production Pipeline & Gated Reconstruction<br/>(Token assertions, content hashes, 0-soft verification)"]
    end

    Stage1 -.->|Benchmark & Diff Evaluation| L5_Gold
    GatedBuild -.->|Verification & Audit| L5_Gold
```

---

## 1.5 Current Status & Handoff (2026-08-22)

### Handoff — read this first

**Where we are.** The Tool Call Protocol sub-project ([`TOOLCALL.md`](TOOLCALL.md)) is
complete through its live-probe gate (**T1–T4 done, GATE PASSED**) and is cleared for
wiring into the Stage 1 runner. Milestone 1.1 (Grammar Tool API) was already complete.

**Next action — milestone 1.2 `runner/agent.py`:**
- System prompt per unit = 5-step CoT reasoning protocol (`runner/prompts.py`, to be
  written) + `toolcall.xml_contract_section()` + `toolcall.tool_specs_section(TOOL_SPECS)`.
- Drive each session through `toolcall.run_tool_loop(...)` with a
  `PromptXmlTransport`; `probe.py`'s `_system_prompt` / `llm7shi_generate` are proven
  adapters to copy from (both Ollama and Gemini paths exercised).
- `LoopResult` (final text, outcome envelopes, full transcript) is what milestone 1.3's
  benchmark will consume; design trace logging around it.

**Carry-over issues from live probing** (details in [`TOOLCALL.md`](TOOLCALL.md) T4):
1. **Few-shot echo contamination**: every probed final answer repeated the demonstration
   exchange's 'cammin' search content despite contract rule 7. When writing the runner
   prompts, replace the few-shot demo (`toolcall.prompts.few_shot_messages`) with
   non-colliding content.
2. **Gate margin is thin**: pooled run = 47 turns at 0.957 vs 0.95 gate (wide binomial
   CI). Keep measuring parse success inside 1.3/1.4 benchmark runs rather than treating
   the gate as permanently closed.
3. **No-call turns happen** (1 of 47): the model sometimes answers in prose without
   calling tools. The loop currently treats zero calls as the final answer; decide
   whether 1.2 needs a nudge policy instead — this interacts with open question §7.1
   (a `submit_candidate` termination tool).

**Environment & artifacts.**
- Default model: `ollama:gemma4:31b-it-qat` (Gemini path `google:gemma-4-31b-it` also
  validated end-to-end).
- Live probe: `uv run python -m harness.toolcall.probe --model <model> --repeat N --log
  harness/probe.log` — streaming JSONL: one scenario record per completed scenario,
  summary record last (a log without the summary line = interrupted run);
  `*.log` is gitignored.
- Test suite: **621 passed** (547 pre-existing + 36 `test_harness_tools.py` +
  38 `tests/test_harness_toolcall.py`).

### Milestone ledger

**Milestone 1.1 — Dedicated Grammar Tool API (`runner/tools.py`): COMPLETE.**

- `GrammarToolkit` serves multi-layer context (L1 tokens/texts, quotes hierarchy, L2
  morphology, pronoun case annex, L3 noun phrases, L4 UD trees) through three closed tools,
  with Layer 5 masked **structurally**: `tools.py` never imports `skel.io` / `skel.registry`
  and no code path opens a file under `skel/`.
  - `read_unit`: parse-unit snapping via `dep.sentence_groups` (`MAX_UNIT_LINES = 12`);
    boundary-crossing ranges are rejected with the actual unit bounds.
  - `search_corpus`: conjunctive `word` / `lemma` / `pos` / `deprel` / `case` search with an
    **Anti-Leakage Guard** excluding the active canto (tracked toolkit state, not model-supplied).
  - `validate_candidate`: intrinsic well-formedness — predicate existence + word anchors,
    L3 NP-head / pronoun citations, slot uniqueness with clitic licensing (multi-slot case
    annex rows), frozen role vocabulary — plus an `upstream_feedback` discrepancy log.
  - Tool-call layer: `TOOL_SPECS` / `tool_specs()` (OpenAI-function JSON Schema, prompt-ready)
    and `GrammarToolkit.dispatch()` (accepts dict or JSON-string arguments, coerces numeric
    strings, never raises into the loop — errors return as structured payloads).
- Tests: `tests/test_harness_tools.py` — 36 deterministic tests incl. poisoning
  `skel.io.load_skel` / `skel.registry.rule_active` to prove masking.

**Tool Call Protocol sub-project (`harness/toolcall/`) — T1–T4 COMPLETE, GATE PASSED.**

Gemma cannot use native tool calling on the Gemini API path and its structured output is
unreliable there, so the interim protocol is prompt-instructed `<tool_call>` blocks (one
JSON object per block) converted into OpenAI-compatible tool-call dicts; native Ollama
tool calling later is a pure transport swap (`OllamaNativeTransport`, T5, deferred).
Deliverables: parser/formatter (`parser.py`), prompt contract + few-shot (`prompts.py`),
transports (`transports.py`), transport-agnostic loop (`loop.py`), live-probe CLI
(`probe.py`); 38 deterministic tests in `tests/test_harness_toolcall.py`. Live probing
motivated a wire-format simplification from nested tags to one JSON object per block
([`TOOLCALL.md`](TOOLCALL.md) §3.1); **final-format pooled run on `google:gemma-4-31b-it`
(--repeat 5): 20 scenarios, 47 turns, parse success rate 0.957 ≥ 0.95 gate**, 0
hallucinated tools, 0 dispatch errors, both observed failure classes benign and
prompt-side.

**Remaining milestones**: 1.2 agent loop (see Handoff above), 1.3 benchmark suite, 1.4
evaluation runs; deferred T5 native transport parity check ([`TOOLCALL.md`](TOOLCALL.md)
§5.3). Open design question: §7.1 termination tool.

---

## 2. Two-Stage Bottom-Up Strategy

In contrast to the top-down methodology used in Phases 5–8 (where frontier LLMs deduced abstract rules applied top-down in local environments), `harness/` adopts an empirical **bottom-up strategy (instance-level inference ➔ pattern induction)**.

### Stage 1: Autonomous Local Inference & Capability Benchmark (`harness/runner/`)
- **Approach**: For each parse unit, the agent receives the multi-layer context (L1–L4, quotes, case) and autonomously solves predicate-argument frames on the fly using Chain-of-Thought (CoT) and a dedicated Tool Calling API (`validate_candidate`, etc.).
- **Objectives**:
  - Quantitatively benchmark local LLM capabilities (1-shot exact match rate, multi-turn self-correction convergence rate, role-level F1) against the 0-soft Gold Standard (`skel/`).
  - Capture comprehensive execution logs, successful syntax projections, and lexical decision traces (e.g., argument vs. adjunct discrimination, reflexive pronouns, control verbs).
- **Specification**: [`harness/runner/PLAN.md`](runner/PLAN.md).

### Stage 2: Bottom-Up Rule & Lexicon Extraction (`harness/extractor/`)
- **Approach**: Mine and aggregate the reasoning logs and decision trajectories from Stage 1 to:
  1. Extract stable, deterministic Universal Dependencies patterns as **Syntax Fast-Path Rules**.
  2. Aggregate verb-preposition-case co-occurrences into an empirical **Verb Valency Lexicon**.
  3. Construct a **Hybrid Execution Engine** combining deterministic fast paths (rules + lexicon) with fallback to Stage 1 agent inference for ambiguous or rare contexts.
- **Objectives**:
  - Maximize cross-corpus consistency and reduce inference latency and token overhead (targeting >80% fast-path coverage).
  - Provide a gated production pipeline that reconstructs cantos under strict 0-soft regression verification and content hash updating.
- **Specification**: [`harness/extractor/PLAN.md`](extractor/PLAN.md).

---

## 3. Directory Structure & Separation of Concerns

```
dante-corpus/
├── skel/                          # [Protected] Layer 5 Gold TSV & Phase 8 Deterministic Engine
│   ├── RULES.md                   # 130 Deterministic Rule Handbook (Reference)
│   └── ...                        # Active 0-Soft Regression Gate Target
│
├── harness/                       # [Isolated] Grammar Agent Harness & Extraction Lab
│   ├── PLAN.md                    # Master Plan (Architecture, Two-Stage Strategy, Handoff)
│   ├── TOOLCALL.md                # Tool Call Protocol Sub-Project (XML interim → native)
│   │
│   ├── toolcall/                  # [Protocol Library] XML interim ↔ canonical tool calls
│   │   ├── parser.py              # parse_tool_calls / format_tool_result (T1)
│   │   ├── prompts.py             # XML output contract + few-shot exchange (T2)
│   │   ├── transports.py          # Transport interface, PromptXml / Stub transports
│   │   ├── loop.py                # Transport-agnostic loop + turn budget (T3)
│   │   └── probe.py               # Live-probe CLI for the §5.2 gate (T4, operator-run)
│   │
│   ├── runner/                    # [Stage 1] Autonomous Inference Agent & Benchmark
│   │   ├── PLAN.md                # Stage 1 Specification (Toolset, Agent, Benchmark)
│   │   ├── tools.py               # Dedicated Grammar Tool API — IMPLEMENTED (Milestone 1.1)
│   │   ├── agent.py               # Gemma 4 31B Multi-Turn CoT Loop (next: Milestone 1.2)
│   │   ├── prompts.py             # 5-Step Grammatical Reasoning Protocol Prompts
│   │   └── benchmark.py           # Syntactic Challenge & Historical Case Evaluation Suite
│   │
│   ├── extractor/                 # [Stage 2] Rule & Lexicon Extraction & Hybridization
│   │   ├── PLAN.md                # Stage 2 Specification (Mining, Lexicon, Hybrid Engine)
│   │   ├── syntax_miner.py        # Syntax Pattern Mining Engine
│   │   ├── lexicon_builder.py     # Verb Valency & Lexicon Profile Aggregator
│   │   ├── hybrid_engine.py       # Fast Path (Rules/Lexicon) + Fallback (Agent) Router
│   │   └── reconstruct.py         # Canto-Wide Gated Reconstruction Pipeline
│   │
│   └── fixtures/                  # Benchmark Challenge Fixtures & Historical Case Units
│       └── challenge_cases.py     # Syntactic Challenge Fixtures (Hyperbaton, Control, Quotes)
│
└── tests/
    ├── test_harness_tools.py      # Toolset unit tests (masking, anti-leakage, validation)
    └── test_harness_toolcall.py   # Tool-call protocol tests (parser, transports, loop)
```

---

## 4. Standing Invariants & Disciplines

1. **Strict Masking of Gold Layer 5**:
   - `runner/` agents are strictly forbidden access to gold `skel/*.tsv`, the 130-rule registry, and historical correction records ([`CORRECTIONS.md`](../skel/CORRECTIONS.md)).
2. **No Free-Form Bash Execution**:
   - Agents operate strictly via closed, structured Tool Calling (`tools.py`) without shell execution privileges.
3. **Preservation of the 0-Soft Regression Gate**:
   - Benchmark and evaluation modes operate strictly in-memory or write to scratch buffers; gold TSVs in `skel/` are never overwritten during benchmark runs.
4. **Upstream Discrepancy Channel**:
   - Discrepancies identified in upstream layers (Layer 2 morphology or Layer 4 UD syntax) are emitted as structured `upstream_feedback` records for human audit and triage.
