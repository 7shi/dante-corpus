# Stage 1: Autonomous Inference & Benchmark (`harness/runner/`)

Stage 1 provides an autonomous execution environment for Local LLMs (**Gemma 4 31B** via `llm7shi.Client`) to infer Layer 5 predicate-argument skeletons on the fly from multi-layer grammatical contexts.

Rather than giving the model an unconstrained bash environment, Stage 1 equips the model with a **closed, dedicated grammatical toolset (Tool Calling)** and a structured 5-step Chain-of-Thought (CoT) reasoning protocol.

---

## Key Components

- **Dedicated Grammar Tool API (`tools.py`)**:
  - `read_unit`: Retrieves multi-layer grammatical context (L1–L4, quotes, case) for a sentence group while strictly masking Layer 5 gold rows and rule definitions.
  - `search_corpus`: Enables scoped searches for analogous syntactic constructions across other cantos (with anti-leakage guards).
  - `validate_candidate`: Evaluates intrinsic syntactic well-formedness (slot uniqueness, valid NP head citations, role vocabulary) and captures `upstream_feedback` records.
- **Autonomous Multi-Turn Agent Runner (`agent.py`)**:
  - Executes the 5-step CoT reasoning protocol (Quotes ➔ Morphology ➔ Case/UD ➔ NP/Control ➔ Self-Correction) using `ollama:gemma4:31b-it-qat`.
- **Syntactic Challenge Benchmark Suite (`benchmark.py`)**:
  - Evaluates 1-shot exact match rate, multi-turn convergence rate, and role-level F1 across challenge fixtures and historical outlier units, logging structured traces for Stage 2.

---

## Detailed Plan & Master Documentation

- **Stage 1 Specification**: [`PLAN.md`](PLAN.md)
- **Harness Master Plan**: [`../PLAN.md`](../PLAN.md)
- **Harness Overview**: [`../README.md`](../README.md)
