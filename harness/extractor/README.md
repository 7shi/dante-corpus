# Stage 2: Bottom-Up Extraction & Hybrid Engine (`harness/extractor/`)

Stage 2 implements the empirical pattern extraction and hybridization pipeline. It ingests the reasoning trajectories, exact matches, and lexical decision traces collected during Stage 1 (`runner/`) to synthesize deterministic rules and empirical valency frames.

---

## Key Components

- **Syntax Pattern Miner (`syntax_miner.py`)**:
  - Clusters successful 1-shot Universal Dependencies subtrees to extract deterministic fast-path derivation rules.
- **Verb Valency Lexicon Builder (`lexicon_builder.py`)**:
  - Aggregates empirical decisions on prepositional argument complementation (`obl:<prep>`) and reflexive classifications to build a corpus-wide valency lexicon.
- **Hybrid Execution Engine (`hybrid_engine.py`)**:
  - Routes parse units through a fast-path tier (>80% unit coverage without LLM calls) with seamless fallback to the Stage 1 autonomous agent for ambiguous or rare contexts.
- **Gated Production Pipeline (`reconstruct.py`)**:
  - Executes full-canto reconstruction gated on token assertions, content hash recalculation, and 0-soft verification against the Gold Standard.

---

## Detailed Plan & Master Documentation

- **Stage 2 Specification**: [`PLAN.md`](PLAN.md)
- **Harness Master Plan**: [`../PLAN.md`](../PLAN.md)
- **Harness Overview**: [`../README.md`](../README.md)
