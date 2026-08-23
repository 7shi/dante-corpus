# Grammar Agent Harness: Overall Architecture & Master Plan

## Handoff — resume here

Temporary notes for the next session; durable state lives in **Current Status**
and the **Milestone Ledger** below.

**Next action — finish the in-flight instrumented unit re-run, then Stage 2:**

- **In flight (operator-run, started 2026-08-23): the unit-mode full benchmark
  re-run on `google:gemma-4-31b-it` — first run with api-retry instrumentation
  AND the Client-backed transport adapter** (`--workflow unit`; disk-only JSONL,
  gitignored like all run logs). On resume:
  1. Check completion per the streaming contract: the log must end with a
     `summary` record over 87 cases (no summary line = interrupted; finished
     case records are kept either way).
  2. Read out `api_retries` / `api_retry_seconds` and compare against the
     predicate run's measured quota tax (103 backoffs / 3,526 s across 40 of
     87 cases), then decompose BOTH workflows into compute vs quota wait —
     this closes the Current Status operational issue's unit-side numbers.
  3. Quality numbers of this re-run are NOT directly comparable to the first
     unit run (run variance plus two behavior changes shipped since: the
     status-bar instrumentation, and the `llm7shi.Client` adapter whose
     quality-retry loop regenerates empty/repetitive replies). Watch whether
     protocol_complete stays at 1.0 and whether any empty final still slips
     through despite the quality retry.
  4. Record durable numbers in this file (never log filenames), then proceed.
- **Stage 2 kickoff afterwards** (`harness/extractor/`, milestones 2.1–2.5 in
  [`extractor/PLAN.md`](extractor/PLAN.md)): mine the traces collected by the
  milestone-1.4 runs into syntax fast-path rules + verb valency lexicon.
- Standing observability requirements (§4 item 5) bind every new extractor
  CLI from day one: streaming JSONL `--log`, stderr progress display, session
  separators, per-turn timings rolled into summary records.
- Error structure to mine around (details in the M1.4 Ledger entry):
  systematic gold-convention divergence on verbless frames dominates
  `historical` misses; bare-`obl` over-assignment and `xcomp` over-generation
  are the top noise sources; the unit run's 19 well-formed `upstream_feedback`
  records await human triage before any upstream-retag decisions (the
  predicate pass filed only 4 — unit remains the primary discovery channel).
- Session housekeeping: this session left UNCOMMITTED working-tree changes —
  new `runner/statusline.py`, Client-backed `agent.llm7shi_generate` with
  explicit `transport.reset()` per session (native ledger flush included),
  benchmark status bar + retry counters + reset plumbing, tests at 725 passed,
  and the PLAN.md updates below. Commit hygiene is the operator's call.
- `*.log` files are gitignored; `harness/bench-strict-validator-baseline.log`
  and `harness/parity.log` exist on disk only, as do the milestone-1.4 run
  logs and the in-flight re-run's log. Durable numbers live in this file.

---

## Current Status

- [x] **Tool Call Protocol sub-project (T1–T5)** — prompt-instructed XML
      protocol; both live gates PASSED (probe 0.957 ≥ 0.95 over 47 turns;
      parity interop 24/24 twice). Details in [`TOOLCALL.md`](TOOLCALL.md) + Ledger.
- [x] **Milestone 1.1 — Dedicated Grammar Tool API** (`runner/tools.py`; Layer 5
      masked structurally; anti-leakage search; intrinsic validation).
- [x] **Milestone 1.2 — Agent Runner** (`runner/agent.py` + `runner/prompts.py`;
      autonomous grammar sessions incl. the no-call nudge policy).
- [x] **Milestone 1.3 — Benchmark Suite** (`runner/benchmark.py` +
      `fixtures/challenge_cases.py`: 87 curated cases; gold comparison + §5.2
      metric suite; streaming JSONL CLI).
- [x] **Milestone 1.4 pre-flight** — §4-item-5 live-run observability complete
      on every CLI (session separators incl. nudge-resume boundaries, per-turn
      stderr lines with timings, streaming pinned to stderr, JSONL summaries
      carrying total elapsed time + `slow_turns`).
- [x] **Milestone 1.4 — Evaluation execution & trace collection** — full
      87-case benchmarks completed for BOTH workflows (`unit` default + the
      `predicate` contrast pass; quality parity at scale, micro F1 0.711 vs
      0.708; details in the M1.4 Ledger entry) → produces the traces Stage 2
      mines.
- [ ] **Stage 2 — Rule & Lexicon Extraction** (`harness/extractor/`, milestones
      2.1–2.5 in [`extractor/PLAN.md`](extractor/PLAN.md)).
- Open design question: §7.1 termination tool — the practical half is resolved
  by the nudge policy (Ledger, M1.2); a dedicated `submit_candidate` termination
  tool stays open at the protocol layer.
- Open operational issue (2026-08-23, predicate full run): long agent contexts
  trip the Gemini API's per-model input-token quota (`gemma-4-31b` paid tier:
  16k input tokens/min) — 429 RESOURCE_EXHAUSTED with ~50 s backoffs becomes
  frequent past ~10 turns, because every loop turn resends the whole transcript
  and the predicate workflow accumulates turns fast. Candidate mitigations
  (undecided): local Ollama backend for long sessions (same XML wire format, no
  TPM ceiling — but the ~3× figure was calibrated on short probe/unit-mode
  sessions; with long transcripts every request pays full local prefill, so the
  penalty compounds roughly quadratically with turn count and may far exceed
  3×), client-side pacing, or a transcript-compaction policy (changes session
  semantics — design first, never mid-benchmark). Measurement: llm7shi's
  auto-retry hides these failures from artifacts; since 2026-08-23 the
  `HarnessStatusLine` stream counts them (`api_retries` / `api_retry_seconds`
  in case records and summaries).   `turn_seconds` still absorbs the wait time,
  so quota-affected turns inflate slow-turn counts unless read together with
  the retry counters. Measured on the predicate full run (first instrumented
  run): 103 backoffs / 3,526 s across 40 of 87 cases, worst session 14
  backoffs / 670 s over 19 turns; excluding backoff, its compute matched the
  unit run (~18.8 ks vs 18.7 ks) — the entire +19% wall clock was quota wait.
- Test suite: **725 passed** (547 corpus + 41 `test_harness_tools.py` +
  76 `test_harness_toolcall.py` + 29 `test_harness_agent.py` +
  32 `test_harness_benchmark.py`).

---

## Milestone Ledger

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
from nested tags to one JSON object per block ([`TOOLCALL.md`](TOOLCALL.md) §3.1);
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

**Milestone 1.2 — Agent Runner (`harness/runner/agent.py`, `runner/prompts.py`): COMPLETE.**

- `runner/prompts.py`: per-unit system prompt = role intro + skeleton-row conventions +
  the 5-step reasoning protocol (quotes → predicates/agreement → case/UD → NP/control →
  validate & self-correct) + `toolcall.xml_contract_section()` +
  `toolcall.tool_specs_section(TOOL_SPECS)`; `unit_task(...)` opens each session; a
  non-colliding few-shot demo replaces the probe's 'cammin' exchange (T4 carry-over 1).
- `runner/agent.py`: `run_unit(...)` drives one parse-unit session through
  `toolcall.run_tool_loop` over a `PromptXmlTransport` (proven `llm7shi_generate`
  adapter copied from `probe.py`); no-call nudge policy (carry-over 3 in the record below);
  `UnitResult` wraps the loop's final text / outcome envelopes / full transcript and
  derives candidate rows (re-parsed from the last `validate_candidate` submission),
  validation outcomes, upstream-feedback records, compliance flags, and a
  Stage-2-ready `trace_record()`; operator CLI (`python -m harness.runner.agent`) for
  live single-unit smoke runs with optional JSONL trace.
- Tests: `tests/test_harness_agent.py` — 18 deterministic tests over `StubTransport` +
  the real toolkit and prompts: prompt assembly, nudge policy (nudge-once-then-converge,
  no nudge on capability give-up or exhaustion, shared turn budget), transcript-derived
  candidate rows, trace round-trip, adapter forwarding.

**Milestone 1.3 — Benchmark Suite (`harness/runner/benchmark.py`,
`harness/fixtures/challenge_cases.py`): COMPLETE.**

- `fixtures/challenge_cases.py`: 87 curated challenge cases, frozen as verbatim data
  (mined deterministically from the corpus at authoring time): 48 **historical** units
  hosting positions from `skel/CORRECTIONS.md` censuses (§P15 residue closure,
  §P13 spurious clausal complements, §P5 verbless speech frames) plus balanced core
  categories across all three canticles — control (`xcomp`), coordination, relative
  chains (≥2 `acl:relcl`), quotes, and hyperbaton (argument cited ≥45 linear tokens
  from its predicate). Coordinates only; no gold rows are stored, and nothing under
  `runner/` reads the fixtures.
- `runner/benchmark.py`: `evaluate_unit` scores a finished session against gold read
  operator-side (`skel.io.load_skel`; agent-side masking untouched) on row keys
  `(line, token, role, arg_line, arg_token)` restricted to unit bounds; per-unit record
  carries exact-first / exact-final / converged (`CONVERGENCE_TURN_BUDGET = 5`),
  missing/extra diffs, malformed and out-of-unit counts, upstream-feedback
  form-validity precision, and probe-style parse-success turn stats.
  `BenchmarkReport` aggregates the §5.2 suite: one-shot exact-match rate, convergence
  rate, role-level P/R/F1 (per-label + micro/macro), upstream feedback precision,
  pooled parse success vs the 0.95 gate, and per-category breakdowns; streaming JSONL
  CLI mirrors `probe.py` log semantics (case records flushed as they complete,
  summary last).
- Agent-side support: `UnitResult` gained `submissions` / `first_candidate_rows`
  (1-shot metric reads the first submission), plus `opening_len` / `session_messages`
  so turn-level consumers skip the few-shot demo exchange in the opening prompt.
- Tests: `tests/test_harness_benchmark.py` — 22 deterministic tests over
  `StubTransport` + real gold data (fixture integrity incl. sentence-group snapping,
  gold comparison, probe-semantics parse stats, metric aggregation, streaming sink);
  suite total 663 passed.

**Milestone 1.4 — Evaluation Execution & Trace Collection (operator-run):
COMPLETE — both workflows at scale (runs of 2026-08-22/23, `google:gemma-4-31b-it`,
XML path over the Gemini API backend).**

- **Workflow A/B decided: default = `unit`.** Two-case pilots
  (hist-inf14-124 + hist-inf22-097; hist-inf14-124 doubled as the carry-over-4
  regression check — gold-style clausal-complement rows validated cleanly):
  unit beat predicate on `predicate_first_pass_rate` (0.44 vs 0.32), role
  micro F1 (0.705 vs 0.588) and wall clock (586 s vs 689 s); predicate's only
  win was parse robustness (1.0 vs 0.75). Predicate failure shapes:
  premature termination after submitting 2/9 predicates (predicted 5 rows vs
  gold 18), a 37-dispatch ~246 s mega-turn that defeats interleaving, and
  final answers echoing raw `<tool_result>` blocks instead of a summary.
  Shared predicates produced identical extra-row patterns across workflows,
  exposing the systematic error classes below.
- **Full unit-mode run: 87/87 cases clean.** protocol_complete_rate 1.0,
  0 exhausted / 0 nudges / 0 malformed / 0 out-of-unit rows; pooled parse
  success 287/287 turns = 1.0 ≥ the 0.95 gate (watch items a/b/c closed — no
  empty-response turns, max turn 291.8 s just under `SLOW_TURN_SECONDS`);
  ~18.7 ks wall clock (~215 s/unit), mean turn 65.2 s, 114 validate
  dispatches across 287 turns.
- **Headline metrics**: role micro P/R/F1 = 0.693/0.729/**0.711**, macro F1
  0.493; one-shot exact match = convergence = 3/87 (all Inferno 1 units);
  `predicate_first_pass_rate` 0.395; gold 1458 rows vs predicted 1533
  (missing 395 / extra 470 → mild over-prediction).
- **Role structure**: obj F1 0.855 (recall 0.944) and subj F1 0.743 are solid;
  weak spots are bare `obl` F1 0.342 (gold's adverbial-marker convention
  over-assigned, 74 fps), `xcomp` precision 0.55 (over-generation), ccomp F1
  0.538, and prep obliques obl:di / obl:in at recall 0.54–0.60.
- **Category structure**: historical exact 0/48 — dominated by systematic
  gold-convention divergence (§P5 verbless frames anchor the predicate token;
  the model normalizes through the copula), not random noise; hyperbaton
  carries the worst per-unit diff density.
- **Upstream feedback channel live**: 19 records from 11 units, form-validity
  precision 1.0 (e.g., L2 POS on `tòrre`, L3 NP head `via Fiorenza`, L4 nsubj
  misassignments) — awaiting human triage before upstream-retag decisions.
- **Full predicate-mode contrast run: quality parity at scale.** 87/87 cases,
  350 turns / 647 validate dispatches, 0 exhausted / 0 nudges; pfpr 0.413 vs
  unit's 0.395, micro F1 0.708 vs 0.711, macro F1 0.502 vs 0.493, converged
  3/87 on the same cases. The pilots' failure shapes did not reproduce: parse
  success 349/350, only one turn over `SLOW_TURN_SECONDS` (313 s,
  retry-inflated), no coverage collapse (647 submissions vs unit's 114). Two
  sessions ended with an *empty* final text after successful validations
  (protocol_complete 0.977) — the XML path's first empty-response cases
  (watch item a); their accumulated submissions still scored normally.
  Mitigated 2026-08-23: `runner.agent.llm7shi_generate` now mirrors the loop's
  transcript into a per-session `llm7shi.Client` (history + system prompt +
  quality-retry loop), so empty or repetitive replies are regenerated instead
  of ending a session. Session boundaries are explicit — `run_unit` opens each
  session with `transport.reset()` (the Client adapter regenerates its
  instance; the native transport flushes its re-attachment ledgers), with the
  length sync invariant kept as a leak guard for callers that never reset.
  One-shot exact 0.0 is structural under accumulation (the first submission
  covers one predicate), not a regression. Default stays `unit` on two
  grounds: the predicate wall clock (+19%, ~22.3 ks) is almost entirely 429
  backoff (Current Status operational issue), and fine-grained validation
  suppresses the upstream-discovery channel (4 records vs 19).
- Run logs are gitignored disk-only artifacts; the durable numbers above are
  the record. Stage 2 mines traces from both runs.


### Carry-over issues from live probing (record; details in [`TOOLCALL.md`](TOOLCALL.md) T4):
1. ~~**Few-shot echo contamination**~~ — RESOLVED in 1.2: `runner/prompts.py` ships its
   own demonstration exchange with deliberately non-colliding content (a foreign-lemma
   search returning an empty hit list); nothing fixture-shaped remains to echo.
2. ~~**Gate margin is thin**~~ — RESOLVED by the milestone-1.4 full run:
   pooled parse success 287/287 turns = 1.0 ≥ the 0.95 gate at benchmark
   scale (T4's 47-turn margin concern closed; per-session parse stats remain
   in every case record for future re-checks).
3. ~~**No-call turns happen**~~ — RESOLVED in 1.2 via the nudge policy in
   `agent.run_unit`: a final answer with zero successful `validate_candidate` dispatches
   earns up to one protocol reminder (resuming the same transcript through a fresh loop
   run under the shared turn budget); give-ups *after* failed validations are never
   nudged so convergence metrics stay honest. This resolves the practical half of
   TOOLCALL.md §7.1 for Stage 1 — `validate_candidate` doubles as the acceptance gate;
   a dedicated `submit_candidate` termination tool stays open at the protocol layer.
4. ~~**Validator rejects gold-correct complement rows**~~ — RESOLVED (2026-08-22,
   after the first live run): the interrupted benchmark surfaced a model
   `upstream_feedback` report proving `validate_candidate`'s citation rule rejected
   gold-style rows (`elli ccomp←sai`, `sai ccomp←tondo`, `de' xcomp←addur`). Root
   cause: the implementation applied the NP-head/pronoun requirement to *every*
   argument, while the spec (`runner/PLAN.md` §3.3 item 2, and the agent prompt) scopes
   it to **nominal** arguments. A corpus-wide scan put 71% of all rejections on
   non-nominal roles (ccomp/xcomp/attr anchor on predicate tokens by nature; bare
   `obl` is gold's adverbial marker). Fix: `tools.requires_nominal_anchor()` — the
   requirement now covers only subj/obj/iobj/obl:<prep>; clausal roles and bare obl
   pass with existence checks; `word` anchors became optional (~40% smaller calls).
   Residual: nominal-role rows whose anchors are genuinely non-nominal (clausal
   subjects etc.) still reject — measured at 527 rows / 1.7% of anchored nominal rows,
   touching ~100 of 3477 parse units; these stay documented ceilings funneled through
   upstream_feedback rather than spec-violating over-reach.
5. ~~**Submission granularity**~~ — RESOLVED by the milestone-1.4 A/B pilots:
   whole-unit submission (workflow `unit`) is the default. Predicate mode lost
   on every deciding metric except parse robustness (pfpr 0.32 vs 0.44, micro
   F1 0.588 vs 0.705, wall clock +18%) and showed three failure shapes:
   premature termination after submitting 2/9 predicates, a 37-dispatch
   ~246 s mega-turn that defeats interleaving (against the §4-item-5
   turn-granularity spirit), and final answers echoing raw `<tool_result>`
   blocks instead of a summary. It stays implemented for comparison
   experiments. *Scale verdict (2026-08-23 full run): the pilot gap did not
   hold — quality reached parity (see M1.4); `unit` stays default on cost
   and upstream-feedback grounds, not on quality.*

---

## 1. Overview & Paradigm Shift: Generalizable Layer 5 Reconstruction

`harness/` is a dedicated **Grammar Agent Harness for Local LLMs** (e.g., **Gemma 4 31B**), designed to systematically reconstruct Layer 5 predicate-argument skeletons (`skel/`) from multi-layer grammatical contexts (Layer 1 text/tokens, quotes hierarchy, Layer 2 morphology, pronoun case annex, Layer 3 noun phrase spans, and Layer 4 Universal Dependencies syntax trees).

### Motivation & Rationale
1. **Historical Context & Limitations of `skel/`**:
   - Layer 5 (`skel/`) was historically produced by a **small local LLM**
     (`ollama:gemma4:31b-it-qat`, pinned in `model.mk`) driving the driver's
     `--fix` regeneration loop; its residual errors were then triaged through an
     interactive, semi-manual process in which a frontier LLM (Claude Opus 5,
     later switched to Gemini 3.7 Flash at the end of Phase 8) and human
     operators read the outlier positions to formulate 130 deterministic rules
     (Rules A–EI) and hand-apply the corrections recorded in
     [`CORRECTIONS.md`](../skel/CORRECTIONS.md).
   - Throughout, the small model was granted **no autonomy**: it ran on rails
     laid down by the larger model — executing repairs inside a checker/rule
     system it did not shape, with everything beyond those rails escalated to
     the frontier-LLM/human triage loop.
   - Although this successfully produced a 100% clean corpus (**0 hard / 0 soft violations across all 100 cantos**, 547 pytest passing), the **construction methodology itself was ad hoc, bespoke to Dante's Italian, and insufficiently automated**.
   - As a result, the Phase 5–8 methodology cannot be directly generalized to other texts, genres, or languages (such as Latin).
2. **Mission of `harness/`**:
   - The gist of `harness/` is to grant the local model that missing **autonomy**: remove the hand-laid rails and let it reason from linguistic first principles, deciding its own path through multi-layer context and closed tools instead of executing rules handed down by a larger model.
   - `harness/` embeds this autonomous agent in a **reproducible, fully automated, and generalizable reconstruction pipeline**.
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

## 2. Two-Stage Bottom-Up Strategy

In contrast to the top-down methodology used in Phases 5–8 — where frontier LLMs deduced abstract rules that the local executor then followed mechanically, without autonomy of its own — `harness/` hands agency to the local model and adopts an empirical **bottom-up strategy (instance-level inference ➔ pattern induction)**.

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

### Beyond Layer 5 (design notes)

Directions that open up **after** the `skel/` reconstruction — a layer swap
(same machinery, different target layer), a vertical whole-stack slice, and the
horizon of reconstructing grammar for a language with no available description
— are kept out of this plan in [`FUTURE.md`](FUTURE.md). None of it is
scheduled work; `PLAN.md` remains the source of truth for status and
milestones.

### Transport & backend policy (2026-08-22)

The Gemini API executes the XML protocol roughly 3× faster than local Ollama,
so **XML (`PromptXmlTransport`) is the officially adopted wire format for Stage
1/2 production runs; native Ollama tool calling (`OllamaNativeTransport`) stays
implemented and gated but is reserved for comparison experiments** (re-run
`harness.toolcall.parity` when revisiting local-only deployments). Backend choice
remains free: `google:gemma-4-31b-it` when wall clock matters,
`ollama:gemma4:31b-it-qat` for offline/cost-constrained work — both ride the
same XML protocol unchanged; both were validated end-to-end over the XML protocol
during the T4/T5 gates.

---

## 3. Separation of Concerns

The directory map lives in [`README.md`](README.md#directory-structure) —
single source, not duplicated here. The boundaries it encodes:

- **`skel/` is protected, not a dependency.** Gold TSVs, the 130-rule registry,
  and [`CORRECTIONS.md`](../skel/CORRECTIONS.md) are the evaluation reference
  and are masked from agents structurally (§4 item 1); only operator-side
  benchmark code reads them.
- **`toolcall/` is a layer- and task-agnostic protocol library.** It knows
  nothing about grammar: wire format, transports, and the multi-turn loop only.
  Everything grammatical lives in `runner/`.
- **`runner/` (Stage 1) produces traces; `extractor/` (Stage 2) consumes
  them.** The contract between the stages is `UnitResult.trace_record()`, not
  shared internals.
- **`fixtures/` is data, read operator-side only.** Nothing under `runner/`
  imports it, so the agent path cannot see the benchmark's case selection.
- **Tests live at the repo root** (`tests/test_harness_*.py`) alongside the
  corpus suite, so the harness stays inside one pytest run.

---

## Environment & Artifacts (reference)

- Live probe: `uv run python -m harness.toolcall.probe --model <model> --repeat N --log
  harness/probe.log` — streaming JSONL: one scenario record per completed scenario,
  summary record last (a log without the summary line = interrupted run);
  `*.log` is gitignored.
- Migration parity check (T5, live run PASSED 2026-08-22): `uv run python -m
  harness.toolcall.parity
  --model <model> [--repeat N] [--log harness/parity.log]` — same log semantics;
  hard gate = canonical interop on both transports.
- Single-unit session CLI (live smoke tests): `uv run python -m harness.runner.agent
  --canticle inferno --canto 1 --line-start 1 [--line-end N] [--trace trace.jsonl]`.
- Benchmark CLI (milestone 1.3): `uv run python -m harness.runner.benchmark [--category
  C]... [--case-id ID]... [--limit N] [--list] [--log bench.log] [--full-transcript]`.

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
5. **Live-Run Observability — separators & streaming**:
   - LLM-in-the-loop runs are inherently slow (minutes per turn on local models, hours per benchmark), and an unwatchable run is an unusable run: every operator-facing CLI must keep progress **visible by default**, not silent-until-finished.
    - Concretely (implemented in `toolcall.loop`): stream model output to stderr as it arrives (llm7shi does this natively on the XML path; `parity.ollama_chat(echo=True)` replays it via llm7shi's `StreamProcessor` on the native path); print one stderr progress line per turn with each call's compact return value (`outcome_brief`) and elapsed seconds (`progress_printer`); announce every session with its `[index/total]` position via major `=====` separators and divide named passes inside a session with minor `-----` ones (`progress_separator` / `progress_subseparator`). Per-turn wall-clock durations ride in the JSONL logs (`turn_seconds`) for post-run profiling.
    - **Optional Rich status bar**: live CLIs may attach a `HarnessStatusLine` (`runner/statusline.py`, the same wiring as the `skel/` build driver) whose bar counts the same units as the separators — the numerator advances to `[pos/total]` as each session starts. Separators, turn lines, and nudge markers then route through its console, and the same console stream is handed to llm7shi as the streaming sink so model output shares the display instead of clobbering the bar. Its console stays pinned to stderr by convention, and forwarded text renders with Rich markup disabled: corpus text routinely contains bracket fragments (`[obl:a=(126,3)]`, closing-tag lookalikes) that markup parsing would silently swallow or crash on mid-stream. The stream also counts llm7shi's automatic api-retry backoffs via its `wait_retry` hook (`api_retries` / `api_retry_seconds`, per case and rolled into summaries), so silent 429 handling stays measurable instead of only inflating `turn_seconds`.
    - **Per-turn logging & timing are a measurement instrument, not decoration**: the per-turn stderr lines and `turn_seconds` arrays exist so per-turn cost is visible live *and* auditable after the run, and run summaries must aggregate them (probe / parity / benchmark roll per-turn seconds up into their `summary` records).
    - **Turn-granularity discipline — keep turns small**: one healthy model turn is one reasoning step plus its dispatches. Prefer many short turns over few long ones; a single turn that sits thinking for many minutes signals that too much work was bundled into one response (e.g., whole-unit CoT ending in one giant validate call) and the prompt or workflow must be **reconsidered, not the latency accepted**. To make brooding measurable, benchmark reports count turns ≥ `SLOW_TURN_SECONDS = 300` as `slow_turns`, and the milestone 1.4 pilot comparison reads these timings when choosing between the unit and predicate workflows.
    - **Log durability never relies on shell redirection**: every live CLI opens and writes its own artifact files (`--log`, `--trace`), so where the human-facing stream display lands is immaterial — stdout or stderr both stay out of any machine-facing record. Current code pins streaming sinks to stderr as a harmless convention (llm7shi defaults to stdout; `parity.ollama_chat(echo=True)` feeds llm7shi's `StreamProcessor`); keep it, but nothing downstream may *depend* on it.
    - **Streaming JSONL log contract** (as implemented by `probe` / `parity` / `benchmark`, binding for all future live CLIs): append one JSON object per completed unit of work (`scenario` / comparison / `case` / `session` record) and flush it immediately, so an interrupted run keeps everything already finished on disk; write a final `summary` record carrying the aggregate metrics **including total elapsed time** (run-level wall clock plus rolled-up per-turn seconds / mean / max). The log truncates on startup (`"w"` mode: one file per attempt, runs never append across attempts), and a file without its summary line marks an interrupted run.
    - This is a standing requirement, not a one-off patch: new live entry points (Stage 2's `extractor/` CLIs included) must ship the same observability from day one, keep the human-facing progress display on stderr by convention (JSONL logs go to their own `--log` files, never to redirected console output), and any future transport must preserve it.
