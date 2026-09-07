# `harness/extractor/`: the reconstruction pipeline

The bounded loop that solves one parse unit, the gates that stand between its
answer and the disk, and the durable artifact it writes. What it shows the model
is [`../runner/`](../runner/).

---

## Key Components

- **Bounded per-unit step (`dante_corpus.harness.fixedcontext`, `observe.py`)**:
  - One request per iteration — specification, frozen-layer evidence, the unit's rows so far, and the verdict on them — whose size is a function of the unit, not of the iteration count. The runtime recomputes the verdict between steps; the model holds no transcript.
- **Soft repair levels (`fixlevel.py`, `dante_corpus.harness.fixrun`)**:
  - `--fix` reopens the units carrying a finding at a level, shows the model its own recorded rows and the invariants they break, and takes the answer only if it is hard-clean, reduces the level's findings, and adds no violation class.
- **Frozen layers and gates 1–2 (`layers.py`)**:
  - `CantoLayers` loads L1–L4 plus the case annex and nothing else; rows are anchored on the Layer-1 token stream and verified through `validate_unit` at 0 hard / 0 soft.
- **Durable artifact (`dante_corpus.harness.artifact`, `.outcome`)**:
  - The canto's TSV is written unit by unit as units settle, and is also the run's resume state — deleting a stretch's lines is how you ask for that unit back.
- **Gated production pipeline (`reconstruct.py`)**:
  - The canto loop, the canto-atomic commit behind a content-hash check and an explicit `--write`, and the CLI.

The Stage-2 pieces this directory was built around — the syntax pattern miner,
the valency lexicon builder, and the hybrid fast-path router — were removed on
2026-09-07 after the fast path measured 7% of the corpus against its own >80%
target. Every unit now reaches the model. What Stage 2 built and measured is
recorded in [`../stages/02.md`](../stages/02.md).

---

## Detailed Plan & Master Documentation

- **Specification**: [`PLAN.md`](PLAN.md)
- **Harness Master Plan**: [`../PLAN.md`](../PLAN.md)
- **Harness Overview**: [`../README.md`](../README.md)
