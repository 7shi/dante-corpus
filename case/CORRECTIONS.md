# case — measurement history

Every measurement this annex makes is recorded here, including the ones that kill it. See
[`PLAN.md`](PLAN.md) for what the annex is and why the pilot is a kill gate rather than a
formality.

## Pilot (step 1) — setup, 2026-07-29

### State check

Re-confirmed before rebuilding anything, per [`PLAN.md`](PLAN.md)'s *Confirm the state first*.
All four match the state the plan was written at, so its counts still describe this corpus:

| check | result |
|---|---|
| `make -C skel check` | 0 hard, **3551** soft |
| `make -C dep check` | 0 hard, 0 soft |
| `uv run pytest -q` | 125 passed |
| `make -C skel stats` | `'obl:a' vs 'obj'` **61**, `'obj' vs 'obl:a'` **28** |

### Population

Rebuilt with `case/population.py` (see *Harness* below) following
[`../skel/PLAN.md`](../skel/PLAN.md)'s *How to measure a candidate rule* — the `stats()` loop
with `dante_corpus.skel._classify_divergence` monkeypatched, run from `skel/`, positions read
1-based over alpha-only tokens. The two disputed buckets come out at exactly the sizes
[`PLAN.md`](PLAN.md) predicted:

| bucket | selector | count |
|---|---|---|
| parked | `role_mismatch`, given `obl:*` / derived `obj`\|`subj`, argument has no `case` child, argument POS is pronoun, predicate has no second `obj` child | **67** |
| mirror | given `obj`\|`subj` / derived `obl:*`, argument's dep deprel is `iobj` | **28** |
| control | clitic arguments where the given and derived reads already **agree** on the role, drawn corpus-wide from the same parse-unit shape, sampled (seed 20260729) to the disputed size | **95** |

Word forms: parked is `mi` 26, `ti` 8, `li` 6, `m'` 6, then a tail; mirror is `mi` 13, `ti` 5
plus tonic forms (`cui`, `me`, `lui`, `altrui`, `lor`) that its selector admits; control is
`mi` 30, `m'` 12, `ti` 11, `si` 7, `li` 7. The control exists because a raw self-agreement
number means nothing without it — a model that answers "accusative" to everything scores
perfectly on consistency.

### Method

Three runs (A / B / C), one per **presentation variant**, each asking every position once in a
fresh `llm7shi.Client` session, in a per-run shuffled order that interleaves disputed and
control positions:

- **A** — the whole parse unit, line-numbered, target pronoun wrapped in `**…**`.
- **B** — the target line and the one before it, unnumbered.
- **C** — the unit joined as prose, the question naming the pronoun.

Three variants rather than three identical repeats: identical prompts measure sampling
temperature, not whether the reading is stable. The prompt carries the terzina and the marked
pronoun and **nothing else** — no `dep/` row, no `skel/` row, no hint that a position is
disputed. That blindness is the design constraint the annex's whole value rests on
([`PLAN.md`](PLAN.md), *Independence*).

The answer vocabulary is **not** constrained by the prompt: the model is asked for one English
word, and whatever it produces is the census that step 2 would freeze — measure-then-freeze, the
same order every other layer used.

### Harness

`population.py` (bucket extraction; run from `skel/`, writes `population.json`), `pilot.py`
(one run per variant, resumable, appends `results.<RUN>.jsonl`), `report.py` (aggregation).

[`PLAN.md`](PLAN.md) called for these to be uncommitted throwaways in the session scratchpad.
They live here instead, on the branch `case-pilot`: the run is a multi-hour job the user
drives, so a session-scoped scratchpad is the wrong place for it, and a harness in the repo
makes the measurement reproducible rather than merely reported. The branch is the revert path
if the pilot kills the annex — `case/` then disappears with it, exactly as *Revertibility* in
[`PLAN.md`](PLAN.md) requires.

Model: **`google:gemma-4-31b-it`** (Gemini API), the artifact's author, i.e. the second line of
[`../model.mk`](../model.mk) — *not* the `ollama:` default, which is the quantized local debug
backend. 190 positions × 3 runs = **570 calls**. Plumbing was smoke-tested on the local backend
(7 calls, discarded).

### Result

**Pending — the three runs have not been made yet.** The verdict, the agreement rates, the
direction breakdown, and the answer-vocabulary census go here when they have.

Stop rule, fixed in advance ([`PLAN.md`](PLAN.md), step 1): if the model does not agree with
itself on the disputed positions at a clearly higher rate than on the control, the column is
measuring noise and the annex ends here.
