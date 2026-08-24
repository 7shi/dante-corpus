# Stage 1 Record: Autonomous Inference & Capability Benchmark (`harness/STAGE1.md`)

Archive of the **completed** Stage-1 record, split from [`PLAN.md`](PLAN.md)
on 2026-08-24 to keep the master plan lean. `PLAN.md` stays the single source
of truth for status and milestones; this file is the durable readout for
milestones 1.1–1.4 (incl. the instrumented re-runs) and the carry-over
resolutions. The Tool Call Protocol sub-project ledger (T1–T5) lives in
[`TOOLCALL.md`](TOOLCALL.md) §8.

## Status at archive time (2026-08-24)

- [x] **Tool Call Protocol sub-project (T1–T5)** — prompt-instructed XML
      protocol; both live gates PASSED (probe 0.957 ≥ 0.95 over 47 turns;
      parity interop 24/24 twice). Details in [`TOOLCALL.md`](TOOLCALL.md)
      (§6 milestones + §8 Ledger).
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
      0.708; details in the M1.4 Ledger entry below) → produces the traces
      Stage 2 mines.
- Open design question: §7.1 termination tool — the practical half is resolved
  by the nudge policy (Ledger, M1.2 / carry-over 3); a dedicated
  `submit_candidate` termination tool stays open at the protocol layer
  ([`TOOLCALL.md`](TOOLCALL.md) §7.1).

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
  backoff (PLAN.md Current Status operational issue), and fine-grained validation
  suppresses the upstream-discovery channel (4 records vs 19).
- Run logs are gitignored disk-only artifacts; the durable numbers above are
  the record. Stage 2 mines traces from both runs.

**Milestone 1.4 addendum — instrumented re-runs (finished 2026-08-24,
`google:gemma-4-31b-it`): COMPLETE.** Both workflows re-run end-to-end with
api-retry instrumentation and the `llm7shi.Client` transport adapter (same
turn budgets as the originals); the unit attempt survived a mid-run server
stall via log-resume, so summaries carry summed per-session durations across
attempts. Readout:

- **Quota tax closed on both sides** (see the PLAN.md Current Status
  operational issue): predicate 103 backoffs / 3,196 s across 47/87 cases vs
  the original 103 / 3,526 s across 40/87 — reproduces at scale; unit measured
  for the first time at 55 backoffs / 1,659 s across 36/87. Compute-only
  totals: unit ≈18.1 ks, predicate ≈19.0 ks.
- **Empty-final failure mode eliminated**: zero empty final texts in either
  run; `protocol_complete_rate` 1.0 on BOTH workflows (predicate was 0.977
  before the Client adapter) — watch item a from the original predicate pass
  closed in practice.
- **Quality parity holds under variance** (re-runs not head-to-head with the
  originals): unit micro F1 0.704 (P 0.690 / R 0.719), macro 0.489;
  predicate micro F1 0.706 (P 0.687 / R 0.727), macro 0.521; pfpr 0.383 vs
  0.408; one-shot exact = converged = 2/87 on unit, 0/87 and 2/87 on
  predicate; gold 1458 vs predicted 1518 (missing 410 / extra 470, unit) and
  1544 (398 / 484, predicate). No regression signal against M1.4.
- **Protocol health**: unit parse success 286/287 (first sub-1.0 pooled rate,
  still far above the 0.95 gate), predicate 337/337 = 1.0; slow turns 1
  (max turn 338 s) vs 4 (max 532 s, retry-inflated); 0 exhausted / 0 nudges /
  0 malformed / 0 out-of-unit rows on both; wall ≈19.8 ks (unit) vs ≈22.2 ks
  (predicate), mean turn 68.9 s vs 65.8 s.
- **Upstream channel**: unit 12 well-formed records from 8 units vs
  predicate 6 from 5, form-validity precision 1.0 everywhere — unit stays
  the primary discovery channel; all unit-side records now total 31 and await
  human triage.

---

## Carry-over issues from live probing (record; details in [`TOOLCALL.md`](TOOLCALL.md) T4):

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
