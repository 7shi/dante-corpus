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

### Result — **PASS** (2026-07-30, 570 calls)

| bucket | n | unanimous (3/3) | majority (2/3) | split (1/1/1) | → dep | → skel | → neither |
|---|---|---|---|---|---|---|---|
| parked | 67 | **56 (84%)** | 11 | 0 | 17 | 45 | 5 |
| mirror | 28 | **21 (75%)** | 7 | 0 | 12 | 16 | 0 |
| control | 95 | **90 (95%)** | 3 | 2 | — | — | — |

**Disputed unanimity 77/95 (81%) vs control 90/95 (95%).**

**How the stop rule was read.** As literally worded in [`PLAN.md`](PLAN.md) — disputed
agreement must be *clearly higher* than control agreement — the gate is unpassable by
construction: the control is the ceiling, being the positions two independent reads already
agree on. The intent, and what the control was built to supply, is a **yardstick for noise**:
the question is whether the disputed positions are answered stably at all, or whether the model
waffles on exactly the cases the column would be built for. The wording has been corrected in
[`PLAN.md`](PLAN.md); the substantive bar was not moved after seeing the numbers, and the
measurement is recorded here in full so the reading can be re-judged.

Against that bar the answer is unambiguous. Three-way splits on the disputed set: **zero** —
every one of the 95 disputed positions has at least a 2-of-3 majority, against 2 splits in the
control. With a near-binary answer space, chance unanimity is ~25%; 81% is not noise, and it
sits 14 points below a control that is itself not 100%.

**Where the instability actually is.** Unanimity by word form: `m'` 20/20, `si` 7/7, `la` 5/5,
`mi` 64/69 (93%), `li` 13/14, `ti` 22/24, `vi` 4/5. The disagreements concentrate on two
identifiable classes rather than being spread over the clitics generally:

- **partitive/locative `ne` / `n'` / `sen` / `cen` / `vi`** — where the split is not
  accusative-vs-dative at all but ablative/genitive/locative, i.e. the model is stably reading a
  third thing and varying only in what to call it. All 5 disputed positions whose majority
  answer is neither accusative nor dative are of this kind (all `obl:di`/`obl:a` vs `obj`).
- **clitic clusters and tonic forms** — `gliel`, `gliel'`, `lui`, `me`, `altrui`.

**Direction — the finding step 3 turns on.** The model does **not** side systematically with
either existing read: on the parked bucket it goes with the Layer-5 LLM 45 / Layer 4 17, on the
mirror bucket with the Layer-5 LLM 16 / Layer 4 12. So `case` behaves as a genuine third
independent read rather than a restatement of either, and it contradicts `dep` at **61**
positions (45 + 16) — the candidate volume a Phase-5i-style hand-verified Layer-4 round needs,
and consistent with [`PLAN.md`](PLAN.md)'s stated expected value of ≈90–100 soft violations.

**These 61 are not usable as corrections.** They were produced by asking about the disputed
positions, which is exactly the manufacturing failure mode [`PLAN.md`](PLAN.md)'s *Independence*
section forbids. They are evidence that the instrument discriminates, nothing more; the
corrections must come from the blind corpus pass of step 3, frozen before it is joined to `dep`.

**Answer vocabulary census** (570 answers, no unmapped values): accusative 276, dative 252,
ablative 28, nominative 7, genitive 5, locative 2. The model's own word for the partitive /
locative class is **`ablative`**, not the `oblique` [`PLAN.md`](PLAN.md) anticipated, and it
distinguishes `genitive` and `locative` from it. Step 2 freezes the vocabulary from this census,
not from the plan's guess — and the `ne`/`vi` instability above is a labeling boundary to settle
in the prompt, not a reading disagreement.

### Verdict

**The annex proceeds to step 2** (freeze vocabulary and scope, write the driver). The pilot
answered the question it was built to answer: the model reads these positions stably, its
answers split both ways against `dep`, and its vocabulary is coherent enough to freeze.
