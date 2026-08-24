# Grammar Agent Harness

Autonomous Grammar Agent Harness for Local LLMs (e.g., **Gemma 4 31B**), designed to systematically infer and reconstruct Layer 5 predicate-argument skeletons from multi-layer grammatical contexts (Layer 1 tokens, quotes hierarchy, Layer 2 morphology, pronoun case annex, Layer 3 noun phrases, and Layer 4 UD syntax trees).

### Motivation: Generalizable Layer 5 Reconstruction
While Layer 5 (`skel/`) reached **0 hard / 0 soft violations across all 100 cantos** in Phase 8, its historical construction had a small local LLM (`gemma4:31b-it-qat`) generate and repair the TSVs, while its residual errors required an ad hoc, semi-manual triage process (interactive audits with frontier LLMs — Claude Opus 5, switching to Gemini 3.7 Flash at the end of Phase 8 — plus hand-crafted rules and manual corrections) that was bespoke to Dante's Italian and difficult to generalize to new texts or languages.

`harness/` is the **systematic and fully automated reconstruction of Layer 5**. It treats `skel/` as an immutable **0-soft Gold Standard** and implements a **two-stage bottom-up architecture** to prove that a local LLM can autonomously reconstruct Layer 5 and generalize across grammatical domains:

1. **Stage 1: Autonomous Inference & Benchmark** ([`runner/`](runner/README.md)) — Evaluates local models using dedicated tool calling and 5-step CoT reasoning without free-form bash execution, logging rich inference traces.
2. **Stage 2: Bottom-Up Extraction & Hybrid Engine** ([`extractor/`](extractor/README.md)) — Mines Stage 1 logs to formulate deterministic fast-path rules and verb valency lexicons, integrating them into a high-speed hybrid execution engine and gated production pipeline.

---

## Documentation & Roadmap

- **Master Plan**: [`PLAN.md`](PLAN.md) — Comprehensive architectural specification and two-stage bottom-up strategy.
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
    ├── test_harness_syntax_miner.py  # Stage 2 miner tests (clustering, rules, coverage)
    └── test_harness_lexicon_builder.py  # Stage 2 lexicon tests (frames, gating, coverage)
```
