# Grammar Agent Harness

Autonomous Grammar Agent Harness for Local LLMs (e.g., **Gemma 4 31B**), designed to systematically infer and reconstruct Layer 5 predicate-argument skeletons from multi-layer grammatical contexts (Layer 1 tokens, quotes hierarchy, Layer 2 morphology, pronoun case annex, Layer 3 noun phrases, and Layer 4 UD syntax trees).

### Motivation: Generalizable Layer 5 Reconstruction
While Layer 5 (`skel/`) reached **0 hard / 0 soft violations across all 100 cantos** in Phase 8, its historical construction relied on an ad hoc, semi-manual process (interactive audits with Claude Opus 5, switching to Gemini 3.7 Flash at the end of Phase 8, and hand-crafted rules) that was insufficiently automated and difficult to generalize to new texts or languages.

`harness/` is the **systematic and fully automated reconstruction of Layer 5**. It treats `skel/` as an immutable **0-soft Gold Standard** and implements a **two-stage bottom-up architecture** to prove that a local LLM can autonomously reconstruct Layer 5 and generalize across grammatical domains:

1. **Stage 1: Autonomous Inference & Benchmark** ([`runner/`](runner/README.md)) — Evaluates local models using dedicated tool calling and 5-step CoT reasoning without free-form bash execution, logging rich inference traces.
2. **Stage 2: Bottom-Up Extraction & Hybrid Engine** ([`extractor/`](extractor/README.md)) — Mines Stage 1 logs to formulate deterministic fast-path rules and verb valency lexicons, integrating them into a high-speed hybrid execution engine and gated production pipeline.

---

## Documentation & Roadmap

- **Master Plan**: [`PLAN.md`](PLAN.md) — Comprehensive architectural specification and two-stage bottom-up strategy.
- **Stage 1 (Inference & Benchmark)**: [`runner/README.md`](runner/README.md) | [`runner/PLAN.md`](runner/PLAN.md)
- **Stage 2 (Extraction & Hybrid Engine)**: [`extractor/README.md`](extractor/README.md) | [`extractor/PLAN.md`](extractor/PLAN.md)

---

## Directory Structure

```
harness/
├── README.md                      # Overview and navigation (this document)
├── PLAN.md                        # Master architectural plan
│
├── toolcall/                      # [Protocol Library] Tool Call Protocol (XML interim → native)
│   ├── README.md                  # Protocol library overview
│   ├── parser.py                  # <tool_call> wire format ↔ canonical tool-call dicts
│   ├── prompts.py                 # XML output contract + few-shot exchange
│   ├── transports.py              # Transport interface (PromptXml / Stub)
│   ├── loop.py                    # Transport-agnostic multi-turn loop
│   └── probe.py                   # Live-probe CLI (parse-success-rate gate)
│
├── runner/                        # [Stage 1] Autonomous Inference & Benchmark
│   ├── README.md                  # Stage 1 overview
│   ├── PLAN.md                    # Stage 1 specification (tools, agent, benchmark)
│   ├── tools.py                   # Dedicated Grammar Tool API
│   ├── agent.py                   # Gemma 4 31B Multi-Turn CoT Loop
│   ├── prompts.py                 # 5-step CoT reasoning protocol
│   └── benchmark.py               # Syntactic Challenge & Case Evaluation Suite
│
├── extractor/                     # [Stage 2] Bottom-Up Extraction & Hybrid Engine
│   ├── README.md                  # Stage 2 overview
│   ├── PLAN.md                    # Stage 2 specification (miner, lexicon, hybrid engine)
│   ├── syntax_miner.py            # Syntax pattern mining engine
│   ├── lexicon_builder.py         # Verb valency & lexicon profile aggregator
│   ├── hybrid_engine.py           # Fast-path + agent fallback execution router
│   └── reconstruct.py             # Canto-wide gated reconstruction pipeline
│
└── fixtures/                      # Curated Challenge Fixtures & Test Cases
    └── challenge_cases.py         # Syntactic challenge fixtures (hyperbaton, control, etc.)
```
