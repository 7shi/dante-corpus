# Grammar Agent Harness

Autonomous Grammar Agent Harness for Local LLMs (e.g., **Gemma 4 31B**), designed to systematically infer and reconstruct Layer 5 predicate-argument skeletons from multi-layer grammatical contexts (Layer 1 tokens, quotes hierarchy, Layer 2 morphology, pronoun case annex, Layer 3 noun phrases, and Layer 4 UD syntax trees).

### Design Philosophy: Autonomy Over Rigid Templates
The harness favors letting the model decide for itself — when a candidate is ready to submit, when its work on a unit is actually done — over forcing it through a fixed, scripted procedure. Structured output isn't available for the models in use, so submission goes through a `validate_candidate` tool call instead; the model may call it any number of times as it revises, and the session ends the moment it answers in plain text with no further tool call, which the loop treats as the model's own completion signal rather than as a scripted turn count or an externally imposed cutoff (the turn budget exists only as a safety net). A model boxed into a rigid template is expected to underperform one given room to judge for itself when its work is done.

### Motivation: Generalizable Layer 5 Reconstruction
While Layer 5 (`skel/`) reached **0 hard / 0 soft violations across all 100 cantos** in Phase 8, its historical construction had a small local LLM (`gemma4:31b-it-qat`) generate and repair the TSVs, while its residual errors required an ad hoc, semi-manual triage process (interactive audits with frontier LLMs — Claude Opus 5, switching to Gemini 3.7 Flash at the end of Phase 8 — plus hand-crafted rules and manual corrections) that was bespoke to Dante's Italian and difficult to generalize to new texts or languages.

`harness/` is the **systematic and fully automated reconstruction of Layer 5**. It treats `skel/` as an immutable **0-soft Gold Standard** and implements a **two-stage bottom-up architecture** to prove that a local LLM can autonomously reconstruct Layer 5 and generalize across grammatical domains:

1. **Stage 1: Autonomous Inference & Benchmark** ([`runner/`](runner/README.md)) — Evaluates local models using dedicated tool calling and 5-step CoT reasoning without free-form bash execution, logging rich inference traces.
2. **Stage 2: Bottom-Up Extraction & Hybrid Engine** ([`extractor/`](extractor/README.md)) — Mines Stage 1 logs to formulate deterministic fast-path rules and verb valency lexicons, integrating them into a high-speed hybrid execution engine and gated production pipeline.

---

## Documentation & Roadmap

- **Master Plan**: [`PLAN.md`](PLAN.md) — Comprehensive architectural specification and staged bottom-up strategy (Stages 1–2 induction core, Stage 3 context optimization, Stage 4 corpus scale-out, Stages 5–6 corpus durability and divergence reduction). Keeps Current Status and the session handoff.
- **Stage 1 Record**: [`STAGE1.md`](STAGE1.md) — Archived milestones, ledger, and carry-over resolutions for the completed Stage 1 (split from PLAN.md).
- **Stage 2 Record**: [`STAGE2.md`](STAGE2.md) — Archived milestones, ledger, and carry-overs for the completed Stage 2, incl. the inferno-1 pilot/recheck readouts (split from PLAN.md).
- **Stage 3 Design & Ledger**: [`STAGE3.md`](STAGE3.md) — Stage-3 home: the payload/pacing design (S3.2), gate re-check, implementation map, confirmation protocol, and the record of why transcript compaction was removed (S3.7). CLOSED on S3.11.
- **Stage 4 Record**: [`STAGE4.md`](STAGE4.md) — The 99-canto full-corpus scale-out: commands, watch items, readout criteria, and the ledger S4.1–S4.3. CLOSED on S4.3.
- **Stage 5 Record**: [`STAGE5.md`](STAGE5.md) — Corpus durability (the run's logs turned into 100 committed gold-format TSVs) and the hard-divergence reduction that followed, incl. what the violation count is and what gold is not (§5). CLOSED on S5.8 at **0 hard**.
- **Stage 6 Design & Ledger**: [`STAGE6.md`](STAGE6.md) — Living Stage-6 home: reducing the 5,014 soft findings, the standing method that record S6.1 forced on it, and class eligibility.
- **Classification audits**: [`HARD.md`](HARD.md) (S5.4) and [`SOFT.md`](SOFT.md) (S6.1) — evidence records asking whether the checker's own hard/soft classification is sound, each filed before the design pass it would otherwise drive. Cross-linked to each other.
- **Beyond Layer 5**: [`FUTURE.md`](FUTURE.md) — Unscheduled design notes on layer swaps, whole-stack vertical slices, and grammar reconstruction without a grammar book.
- **Stage 1 (Inference & Benchmark)**: [`runner/README.md`](runner/README.md) | [`runner/PLAN.md`](runner/PLAN.md)
- **Stage 2 (Extraction & Hybrid Engine)**: [`extractor/README.md`](extractor/README.md) | [`extractor/PLAN.md`](extractor/PLAN.md)

---

## Directory Structure

The single directory map for the harness — [`PLAN.md`](PLAN.md) and the stage
plans reference this section instead of repeating it. Implementation status is
tracked in [`PLAN.md`](PLAN.md) (Current Status / Milestone Ledger), not here.

```
dante-corpus/
├── skel/                          # [Protected] Layer 5 gold TSV & Phase 8 deterministic engine
│   ├── RULES.md                   # 130 deterministic rule handbook (masked from agents)
│   └── ...                        # Active 0-soft regression gate target
│
├── harness/                       # [Isolated] Grammar Agent Harness & Extraction Lab
│   ├── README.md                  # Overview, navigation, and this directory map
│   ├── PLAN.md                    # Master architectural plan (status, milestones, disciplines)
│   ├── STAGE1.md                  # Archived Stage-1 record (milestones 1.1–1.4, carry-overs)
│   ├── STAGE2.md                  # Archived Stage-2 record (milestones 2.1–2.5, pilot/recheck readouts)
│   ├── STAGE3.md                  # Stage-3 design + ledger (payload/pacing, launch hardening)
│   ├── STAGE4.md                  # Stage-4 record (99-canto corpus run, readout, ledger)
│   ├── STAGE5.md                  # Stage-5 record (corpus durability + hard reduction to 0)
│   ├── STAGE6.md                  # Stage-6 design + ledger (soft divergence reduction)
│   ├── HARD.md                    # Audit: is the hard classification sound? (S5.4)
│   ├── SOFT.md                    # Audit: is the soft classification sound? (S6.1)
│   ├── TOOLCALL.md                # Tool call protocol sub-project (XML interim → native)
│   ├── FUTURE.md                  # Beyond Layer 5 (unscheduled design notes)
│   │
│   ├── toolcall/                  # [Protocol Library] XML interim ↔ canonical tool calls
│   │   ├── README.md              # Protocol library overview
│   │   ├── parser.py              # parse_tool_calls / format_tool_call / format_tool_result
│   │   ├── prompts.py             # XML output contract + few-shot exchange
│   │   ├── transports.py          # Transport interface (PromptXml / OllamaNative / Stub)
│   │   ├── loop.py                # Transport-agnostic multi-turn loop + turn budget
│   │   ├── probe.py               # Live-probe CLI, parse-success-rate gate (operator-run)
│   │   └── parity.py              # Migration-parity CLI, XML vs native (operator-run)
│   │
│   ├── runner/                    # [Stage 1] Autonomous inference agent & benchmark
│   │   ├── README.md              # Stage 1 overview
│   │   ├── PLAN.md                # Stage 1 specification (toolset, agent, benchmark)
│   │   ├── tools.py               # Dedicated Grammar Tool API (Layer 5 masked structurally)
│   │   ├── agent.py               # Per-unit session runner over run_tool_loop
│   │   ├── prompts.py             # 5-step CoT grammatical reasoning protocol
│   │   ├── benchmark.py           # Gold comparison & metric suite
│   │   └── statusline.py          # Rich live status bar for long operator-run sessions
│   │
│   ├── extractor/                 # [Stage 2] Rule & lexicon extraction, hybrid engine
│   │   ├── README.md              # Stage 2 overview
│   │   ├── PLAN.md                # Stage 2 specification (miner, lexicon, hybrid engine)
│   │   ├── syntax_miner.py        # Syntax pattern miner: UD-topology rules from traces
│   │   ├── lexicon_builder.py     # Verb valency & lexicon profile aggregator
│   │   ├── hybrid_engine.py       # Fast-path (rules/lexicon) + agent fallback router
│   │   └── reconstruct.py         # Canto-wide gated reconstruction pipeline
│   │
│   ├── recon/                     # [Stage 4–6] Full-corpus run drivers & durable artifacts
│   │   ├── Makefile               # 100-canto launch, resumable; goal & resume state = NN.tsv
│   │   ├── readout.py             # [Stage 4] Corpus-wide log aggregation & closing readout
│   │   ├── convert.py             # [Stage 5] Legacy logs -> gold-format NN.tsv (no make target)
│   │   ├── check.py               # [Stage 5] Hard/soft violation check & stats over the TSVs
│   │   ├── repair.py              # [Stage 5] Deterministic divergence-reduction rules
│   │   ├── agree.py               # [Stage 5] Row-level P/R/F1 vs gold (readout, not a target)
│   │   └── <canticle>/            # NN.tsv (skel-compatible, committed); NN.log = gitignored by-product
│   │
│   └── fixtures/                  # Benchmark challenge fixtures & historical case units
│       ├── __init__.py            # Public fixture accessors
│       └── challenge_cases.py     # Frozen 87-case table (historical/control/coordination/
│                                  #   relative_chain/quotes/hyperbaton)
│
└── tests/
    ├── test_harness_tools.py      # Toolset unit tests (masking, anti-leakage, validation)
    ├── test_harness_toolcall.py   # Tool-call protocol tests (parser, transports, loop)
    ├── test_harness_agent.py      # Runner tests (nudge policy, submissions, traces)
    ├── test_harness_benchmark.py  # Benchmark tests (gold comparison, metrics, fixtures)
    ├── test_harness_pacing.py     # Stage 3 tests (Client sync, interval, token bucket)
    ├── test_harness_syntax_miner.py  # Stage 2 miner tests (clustering, rules, coverage)
    ├── test_harness_lexicon_builder.py  # Stage 2 lexicon tests (frames, gating, coverage)
    ├── test_harness_hybrid_engine.py   # Stage 2 engine tests (derivation, routing, fallback)
    ├── test_harness_reconstruct.py     # Stage 2 gate tests (assertions, 0-soft, hash commit)
    ├── test_harness_recon_readout.py   # Stage 4 readout tests (aggregation math)
    ├── test_harness_recon_convert.py   # Stage 5 conversion tests (TSV shape, idempotence)
    ├── test_harness_recon_check.py     # Stage 5 check tests (hard/soft split, base_dir)
    └── test_harness_recon_repair.py    # Stage 5 repair + agreement-gate tests
```
