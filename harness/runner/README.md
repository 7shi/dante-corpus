# `harness/runner/`: the model-facing half

Everything that touches the model: the evidence it is shown, the wording it is
shown it in, the gate its answer must pass, and the adapter that carries the
request. It is driven by [`../extractor/`](../extractor/), which owns the loop
and the gates around it.

Rather than giving the model an unconstrained bash environment, it is given a
**closed, dedicated grammatical toolset** and a structured Chain-of-Thought
reasoning protocol. Nothing here executes shell commands, and nothing here opens
Layer 5 gold.

---

## Key Components

- **Dedicated Grammar Tool API (`tools.py`)**:
  - `read_unit`: Retrieves multi-layer grammatical context (L1–L4, quotes, case) for a sentence group while strictly masking Layer 5 gold rows and rule definitions.
  - `validate_candidate`: Evaluates intrinsic syntactic well-formedness (slot uniqueness, valid NP head citations, role vocabulary) and captures `upstream_feedback` records.
- **Prompt assembly (`prompts.py`, `skills/grammar-fixed/`)**:
  - `fixed_system_prompt()` concatenates three skill files and nothing else, so `fixed_skill_digest()` fingerprints every byte of the specification a run was launched under (Standing Invariant §6).
  - The grammatical wording lives in the files, not in Python: a change to what the model is taught is a reviewable diff.
- **Model access (`dante_corpus.harness.llm`)**:
  - The `llm7shi.Client` adapter — transcript sync, pacing, the generation-length cap — and the `llm_request` / `llm_response` JSONL wire log every live run is costed from.
- **Live status bar (`dante_corpus.harness.statusline`)**:
  - The Rich bar and shared console every operator-run CLI streams into, with the `wait_retry` hook that counts API backoff.

The Stage-1 pieces this directory was built around — the autonomous multi-turn
session (`agent.py`), the `search_corpus` tool, and the syntactic challenge
benchmark (`benchmark.py`) — were removed on 2026-09-07. What they built and
measured is recorded in [`../stages/01.md`](../stages/01.md).

---

## Usage

Nothing here has a CLI of its own: the operator-facing entry point is
`harness.extractor.reconstruct`, run through
[`../recon/Makefile`](../recon/Makefile).

```bash
cd harness/recon
make inferno/01.tsv            # one canto, through the fixed-context loop
make fix                       # the same loop over the committed artifacts
```

Programmatically, `fixedcontext.fixed_fallback(model=...)` builds the live
per-unit callable over these pieces, and `reconstruct_canto(..., fallback=...)`
takes any callable of the same shape — which is how the deterministic tests
drive the pipeline without a model.

---

## Detailed Plan & Master Documentation

- **Specification**: [`PLAN.md`](PLAN.md)
- **Harness Master Plan**: [`../PLAN.md`](../PLAN.md)
- **Harness Overview**: [`../README.md`](../README.md)
