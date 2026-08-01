# case — a pronoun case annex to Layer 2

## Status

**Steps 1–3 are done. Step 4 is under way: slice 1 (the 49 impossible pairings) and slice 2 (the
102 contradictions `skel` already flags) both closed on 2026-07-31.** All 100 cantos, 13112
pronoun tokens, 13176 case values. Slice 2 edited **81 positions / 92 rows** in `dep/` and took
Layer 5 from **3555 to 3469 (−86)** — against slice 1's +5 from 49 candidates, which is the
corrected selector paying out. Agreement with `dep` is now 86% on `obj`, 95% on `iobj`, 99% on
`nsubj`, and the contradiction list is **382** (was 462). What remains of step 4 is
[*slice 3*](#step-4--the-next-action): the 324 contradictions `skel` does **not** flag, where a
correct fix will not lower Layer 5's count. See [`CORRECTIONS.md`](CORRECTIONS.md)'s
*Step 4, slice 2*.

The vocabulary and scope are frozen and the code exists — [`case.py`](case.py) (build driver,
`--check`/`--stats`/`--clean`), [`README.md`](README.md), [`Makefile`](Makefile),
`dante_corpus/case.py`, `Canto.case()`, `dante-corpus text case`, `"case"` appended to
`hashes.LAYERS`, and `tests/test_case.py`. Everything lives on the branch `case-pilot` so the
whole annex can be dropped in one move. Written 2026-07-29, immediately after Layer 5's
Phase 5 closed at **0 hard, 3551 soft** (see [`../skel/PLAN.md`](../skel/PLAN.md)'s *Where
Phase 5 ended*); Layer 5 stood at **3550** after step 3's `morph/` rounds (see *Step 3 result*)
at **3555** after slice 1 and at **3469** after slice 2 (see *Step 4*).

**Pilot result (2026-07-30, 570 calls, `google:gemma-4-31b-it`).** The state check below was
re-run and matched; the disputed population rebuilt at exactly **67 + 28**, with a **95**-position
control group. Self-agreement across the three presentation variants: **81% unanimous on the
disputed positions with zero three-way splits**, against **95%** on the control — stable
answering, not noise, so the kill gate is **passed**. The model sides with neither existing read
systematically (Layer 4 on 29 positions, the Layer-5 LLM on 61), which is what a genuine third
independent read should look like, and its own vocabulary census (`accusative` 276, `dative` 252,
`ablative` 28, `nominative` 7, `genitive` 5, `locative` 2) is what step 2 freezes. Full
measurement, including how the stop rule's wording was corrected, in
[`CORRECTIONS.md`](CORRECTIONS.md).

**Step 2 result (2026-07-30).** Vocabulary frozen at the census's own six values —
`accusative` / `dative` / `ablative` / `nominative` / `genitive` / `locative`, with `ablative`
(not the `oblique` this plan guessed) as the model's word for the partitive/locative class —
plus `vocative`, the one value added rather than measured (the pilot sampled clitic argument
positions, which cannot hold a term of address; the frozen scope is every pronoun, and direct
address is pervasive in the poem). `--stats` over the built artifact measures whether it is
used at all. The oblique tail is left **open on purpose**: `ablative` is a residual class, the
tail was 6% of the pilot's answers and is where the model was least stable, and `genitive` is
weak under the criterion the `instrumental` rejection implies (a value earns its place if it
changes the *slot* the pronoun fills, not what the oblique means). Seven values are frozen
anyway because folding one into `ablative` afterwards is a mechanical rewrite while dropping it
now and being wrong costs a corpus pass — see [`CORRECTIONS.md`](CORRECTIONS.md)'s
*The oblique tail*.

Scope frozen at **every pronoun-POS token** (13112 tokens over 8540 lines), read off Layer 2's
own `pos` column rather than a hand-frozen list of word forms, at a measured **1340 calls**; the
clitic-only alternative was 3710 tokens for ~446 calls but needed a curated form list and left
the *mirror* bucket's tonic forms (`cui`, `me`, `lui`, `altrui`, `lor`) unanswered. Driver,
module, serve surface and tests written; see [`README.md`](README.md) and
[`CORRECTIONS.md`](CORRECTIONS.md)'s *Step 2*.

**Step 3 smoke test (2026-07-30).** Inferno 1 was built before committing to the corpus pass.
`--check` passed at **0 hard**, and cross-tabulating against Layer 4 found two things the
checker structurally cannot see: the prompt's worked example taught `accusative` for the
reflexive `mi ritrovai`, and the reflexive/impersonal clitic (**1411 tokens, 10.8% of the
scope**, Layer 4's `expl`) had no home in the vocabulary. Both are fixed — the example now reads
`reflexive`, and **`reflexive` is an eighth value** — and `case/inferno/01.tsv` must be rebuilt
with `--force`. See [`CORRECTIONS.md`](CORRECTIONS.md)'s *Step 3 smoke test*.

Inferno 1 was then **rebuilt** under the corrected prompt: 0 hard, and `reflexive` maps onto
Layer 4's `expl` at 9/10. The rebuild also surfaced a third adjudication class the clitic-only
pilot could not have sampled — relative pronouns that are the subject of their clause, read
`nominative` by `case` and `obj`/`obl` by Layer 4 — so `--stats` gained `nsubj` → `nominative`
and an *impossible pairings* report (`obl` × `nominative`). Report-side only; generation is
unchanged.

**Step 3 result (2026-07-31, four runs).** All 100 cantos are built and `--check` is **0 hard**.
Across the first three runs it went **1236 → 70 → 13 hard**, and **no residue was ever the model
getting the Italian wrong** — every one was a defect on the frozen side:

| run | `--check` | what it actually was |
|---|---|---|
| 1 | 1236 over 23 cantos | driver bug: a chunk the model could not get past aborted the *whole remaining canto*, so ~23 genuine failures cost 192 of the 1340 chunks. Fixed — a failed chunk is now skipped, not fatal (`3157f86`). |
| 2 | 70 over 19 cantos | Layer 2's `pos` undercounting its own `lemma` on 24 fused clitic clusters (`sen` = `si+ne`, tagged `pronoun` here and `pronoun+pronoun` 15 times elsewhere), rejecting a correct two-value answer forever. Corrected in `morph/` (`880fc2e`). Also: the model writes the `Word` cell as the clitic (`mi`) rather than the fused token (`parlami`), so `_match` now accepts the clitic a fused token ends in. |
| 3 | 13 over 3 cantos | the same defect in shapes round 2 did not cover — the *lemma* undercounting too (`sen` with the lemma `si`), a three-part lemma under a two-part `pos` (`Vattene`), `nol` = `non lo` demanding two cases for one pronoun. 14 more tokens, audited as a family rather than as symptoms (`a97b80e`). |

Round 3's corrections changed how many cases 15 frozen positions need, so rows that had validated
became wrong and `make -C case clean` dropped the chunks holding them — `--check` briefly read
**89**, higher than the 13 that caused it, because the fix widened what had to be regenerated
rather than because anything regressed. **Run 4 re-requested those 12 chunks and all of them
validated**, taking `--check` to 0 hard. The artifact is committed at `0027494`.

Round 3 also took **Layer 5 from 3551 to 3550 soft**: *Paradiso* 17:92's `nol`, tagged
`adverb+article`, was why `skel --check` reported `argument (92, 4) for role obj heads no
NP/pronoun/predicate`. The annex has therefore already audited Layer 2 — before its `dep` join
has been looked at at all — because a column that reads `pos` as a **count** exercises Layer 2 in
a way no earlier consumer did.

**The lesson the pass leaves behind.** The smoke test established that `--check` passing is not
evidence the artifact is right. The three failing runs established the converse: **`--check`
failing is not evidence the model is wrong.** A formal check compares the answer against the
frozen layers, so it fails whenever *either* side is at fault, and here the frozen side was at
fault three times running. If a future chunk fails identically on all three attempts *and* on the
unit-by-unit retry, suspect Layer 2 first, and pass `--log`.

**Resuming? Read [*Resuming cold — step 4, slice 3*](#resuming-cold--step-4-slice-3) first**, then
[*Step 4*](#step-4--the-next-action) for the detail.
[*Starting from a cold session*](#starting-from-a-cold-session--everything-the-pilot-needs)
carries the step-1 context (how the disputed population was rebuilt, which model, who runs what)
and is now historical. Everything between them is rationale.

## Resuming cold — step 4, slice 3

**Written 2026-07-31 at the end of slice 2, so a session with no memory of it can carry on from
this section alone.** Branch `case-pilot`.

### Where things stand

| commit | what |
|---|---|
| `0027494` | the frozen `case/` artifact — 100 cantos, 0 hard. **Do not touch it** |
| `419120b` | slice 1's Layer-4 edits: 10 positions / 11 rows in `dep/` |
| `40c8a11` | slice 1's measurements and the step-4 selector change |
| `596bdae` | the cold-start handoff slice 2 was executed from |
| *slice 2* | 81 positions / 92 rows in `dep/`, plus the `case`/`dep`/`skel` CORRECTIONS entries |

```bash
git status --short          # expect clean
uv run pytest -q            # expect 138 passed
make -C morph check         # expect 0 hard, 0 soft
make -C dep check           # expect 0 hard, 0 soft
make -C skel check          # expect 0 hard, 3469 soft
make -C case check          # expect 0 hard
cd case && uv run case.py inferno purgatorio paradiso --stats --full
                            # expect 382 contradictions, 39 impossible pairings
```

If `skel` reads 3555 and `case --stats` reads 462/39, slice 2 is not in the tree.

### What slices 1 and 2 settled, so none of it is re-litigated

1. **The 49 impossible pairings are done** (slice 1) and **the 102 tier-A contradictions are
   done** (slice 2). Neither list is work in progress.
2. **The artifact stays frozen.** Asked and answered in slice 1: a measured weakness in `case` is
   recorded, never patched. Slice 2 measured eleven more `case`-side errors and patched none.
3. **`case.py`'s `_IMPOSSIBLE` rule stays as it is.**
4. **Layer 5's soft count is a diagnostic, not the objective.** Slice 1 raised it correctly;
   slice 2 lowered it by 86. Neither number decided whether an edit was right.
5. **The selector works and its limits are measured.** Tier A yielded 79%; the impossible
   pairings yielded 20%. But tier A still contained eleven positions where `case` was the wrong
   read, so **the terzina is still opened one at a time**.

### The next action

**Slice 3: the 324 contradictions `skel` does not flag** — everything in
`case.py --stats --full`'s list that is not in slice 2's tier A, B or C. Rebuild the partition
with the two-join recipe in [`CORRECTIONS.md`](CORRECTIONS.md)'s *Step 4, slice 2* (it is five
lines of parsing, not a monkeypatch: `--stats --full` for the contradictions, `skel.py --check`'s
stderr for the flagged positions, keyed on the `(line, token)` pairs in each violation's detail).

**Expect Layer 5's count not to move, and do not treat that as failure.** This is the slice-1
configuration — `dep` and `skel` agree, only `case` dissents — so a correct fix breaks an
agreement and may raise the count. The deliverable here is a more correct Layer 4, not a smaller
number. If that trade is not worth the hours, **stopping after slice 2 is a defensible end to
step 4**; say so explicitly rather than leaving the list looking unfinished.

Two things to carry in:

- **Purgatorio 28:51**, *nel tempo che perdette / la madre lei* — `madre`:`obj` and `lei`:`nsubj`
  are swapped (Ceres lost Proserpina, not the reverse). Verified in slice 1, not in tier A, so
  still untaken. Take it with slice 3 rather than re-deriving it.
- **The two `morph/` items slice 2 surfaced** — inferno 8:4.5 `i` (for *ivi*) tagged `pronoun`,
  and purgatorio 31:90.1 *salsi* lemmatized `salutare`. Both belong to a `morph/` round, with
  slice 1's `fossi` and `torti`.

### The traps, in the order the two slices hit them

- **Layer 2 can block a Layer-4 edit, and that outranks the reading.** Slice 1 lost two edits to
  it. Before proposing a retag, check `morph`'s `pos` for the tokens involved; if the edit needs
  Layer 2 to be wrong, it is a `morph/` item.
- **The corpus-internal convention sweep is what makes an edit defensible**, and it decided more
  of slice 2 than the reading did: bare clitic under these verbs is `iobj` 181 / `obj` 42;
  predicative `che` under a copula is `attr` 26 / `obj` 17; the notional subject of a perception
  verb's infinitive is `nsubj` 141 / `obj` 100 — that last one *stopped* two edits. Measure the
  convention before choosing a target deprel, every time.
- **Layer 5's LLM is a third read too, and it can be right when you are not.** It sided against
  both of slice 1's two-row edits and was right on one.
- **Judge from the rows, never from the summary.** This annex has now been wrong five times in
  that exact shape.

### The `case` column's measured weakness, for the `morph/` merge

Across both slices the column's errors are not scattered. It reads a pronoun's **case** well and
its **word order** poorly: it makes a relative pronoun nominative when the clause's subject is
postposed (five instances in slice 2), and it has no rule for the standard of comparison (slice
1's 21). Both are prompt-fixable, and the fix belongs to a **blind regeneration at the `morph/`
merge**, never to an edit of the frozen artifact.

## Step 4 — the next action

**A hand-verified Layer-4 correction round over the contradiction list, in the style of Phases
5i/5n.** `make -C case stats` regenerates the input; nothing in it is applied mechanically.

```bash
make -C case stats     # census, oblique tail, dep agreement, contradictions, impossible pairings
cd case && uv run case.py inferno purgatorio paradiso --stats --full   # all 421 candidates
```

`make -C case stats` truncates the candidate lists to the first 40 / 20 so the report stays
readable; `--full` is what the round actually works from.

### State to confirm before assuming anything

```bash
git status --short          # expect clean (or only doc edits in flight)
uv run pytest -q            # expect 138 passed
make -C morph check         # expect 0 hard, 0 soft
make -C dep check           # expect 0 hard, 0 soft
make -C skel check          # expect 0 hard, 3469 soft   (3555 before slice 2, 3550 before slice 1)
make -C case check          # expect 0 hard
```

The artifact is **frozen and committed**, and step 4 must not touch it. Every edit this round
produces belongs in `dep/`; if a position looks like a `case` error, the answer is to record it,
not to rewrite the column — the column's value is that it was authored before any of this was
looked at, and an edit made now is indistinguishable from one made to close a violation. Slices 1
and 2 together recorded **23 `case`-side errors** and rewrote none.

### What the join found, and what the two slices spent

| `dep` | reads as | agree | contradict | rate | before step 4 |
|---|---|---|---|---|---|
| `obj` | `accusative` | 1660 | 267 | 86% | 1631 / 317, 84% |
| `iobj` | `dative` | 708 | 38 | 95% | 669 / 46, 94% |
| `nsubj` | `nominative` | 5095 | 77 | 99% | 5076 / 98, 98% |

**382 contradictions, 39 impossible pairings** (from 461 and 49).

| slice | population | candidates | edited | Layer 5 |
|---|---|---|---|---|
| 1 ✅ | the `obl` × `nominative` impossible pairings | 49 | 10 (20%) | 3550 → **3555** |
| 2 ✅ | contradictions where `skel`'s given role sides with `case` (tier A) | 102 | 81 (79%) | 3555 → **3469** |
| 3 | the 324 contradictions `skel` does **not** flag | 324 | — | expect ~0 |

**The selector, established by slice 1 and confirmed by slice 2.** Rank candidates not by whether
`case` and `dep` contradict, but by **whether `skel` already diverges from `dep` at that
position**:

- Where `dep` and `skel` **agree** and only `case` dissents, a correct Layer-4 fix *breaks* an
  agreement and **raises** Layer 5's count. Slice 1 is that configuration by construction.
- Where `skel` **already dissents from** `dep`, a third read that sides with `skel` breaks a 2-1
  tie and **closes** the violation. This is the Phase 5h/5i configuration and the only population
  the **≈90–100** estimate was ever derived from. Slice 2 is that configuration, and it measured
  −86 from 102 candidates — the estimate was accurate.

Slice 2's other measured result is that the selector predicts **yield**, not just direction: 79%
of tier A were Layer-4 errors against 20% of the impossible pairings. It does not replace
verification — eleven tier-A positions were `case` errors and were left alone.

### Slice 3, and whether to run it

The remaining 324 are the slice-1 configuration. Correcting Layer 4 there is still correct work,
and it is the honest completion of the round, but **Layer 5's count will not fall and may rise**.
Two defensible outcomes:

- **Run it**, for a more correct `dep`, reporting the count movement as expected rather than as
  regression.
- **Stop after slice 2** and record step 4 as complete at 91 positions, with the 324 documented as
  a known, measured, deliberately-unspent population.

Either way, say which was chosen. What is *not* defensible is leaving the list looking like
unfinished work with no verdict — that is the shape [`../skel/PLAN.md`](../skel/PLAN.md)'s Phase 5
was careful to avoid for every route it opened.

Verify against the terzina one position at a time; `make -C dep check` must stay 0/0 throughout.
**Layer 5's soft count is a diagnostic, not the objective** — it measures divergence between two
independent reads, not correctness, and a round that optimizes it is a round editing artifacts to
move a number.

**Judge from the rows, never from the summary.** This annex has been wrong five times and every
one was the same shape — a verdict reached from an aggregate without looking at what the rows
were doing. Three corpus runs blamed the model when Layer 2 was at fault; the oblique-tail reading
blamed the vocabulary when the analysis was at fault; slice 1's first reading called the
comparative frame a systematic error before measuring it. 382 contradictions is an aggregate.
Open the terzina.

### How to inspect a position

There is no checked-in harness; each round uses a throwaway script. The serve API's shapes, which
cost four failed attempts to rediscover last time:

```python
from dante_corpus import canto
c = canto("inferno", 1)
c.lines()          # tuple[Line];  Line.no (not .number), Line.text, Line.tokens
c.dep()            # dict[int, tuple[DepRow]] keyed by line — NOT a flat sequence
                   #   DepRow(line, token, word, deprel, head_line, head_token)
c.case()           # dict[int, tuple[CaseRow]] keyed by line
                   #   CaseRow(line, token, word, case); .cases() splits a fused token
```

`token` is **1-based over the alpha-only tokens** of a line, the same convention Layers 2–5 use
(`[t for t in tokenize(text) if has_alpha(t)]`). Indexing raw `tokenize` output misaligns every
word you print — it has bitten previous rounds in `skel/` too.

### Then step 5

Re-measure Layer 5 and record the delta in
[`../skel/CORRECTIONS.md`](../skel/CORRECTIONS.md).

### The three parked questions — now answered

Measurements in [`CORRECTIONS.md`](CORRECTIONS.md)'s *fourth run and the freeze*.

- **The oblique tail: fold nothing.** The deciding evidence is the `dep` deprel distribution,
  not the word forms. **`ablative` (1805)** is `obl` at 82% — the prepositional oblique.
  **`genitive` (267) is earned**: 189 of it (71%) is adnominal (`nmod` 139, `det:poss` 50), and
  `det:poss` is a slot `ablative` fills **zero** times — `lor danno`, `il senso lor`, `le gambe
  loro` are possessive determiners, not obliques. **`locative` (81) stays open**: by deprel it
  is `obl`-dominant exactly as `ablative` is, so whether "place" is a distinct slot or a distinct
  meaning of the same slot is undecided; settle it at the `morph/` merge. `vocative` (30) is
  frozen-but-unearned — correct and harmless, but argued from the poem's rhetoric rather than a
  count. `reflexive`, the other value added rather than measured, is vindicated at 1961 — 15% of
  the column, and mistagging it was what the Inferno 1 smoke test caught.
  **An earlier reading of this tail recommended folding `genitive` and was wrong**; the argument,
  the refutation and the lesson are in [`CORRECTIONS.md`](CORRECTIONS.md)'s *The subset argument
  was wrong*. No rows were rewritten.
- **The third adjudication class is real**, at 49 corpus-wide — and step 4's slice 1 has now
  worked all 49. It is smaller than it looks: only 10 were Layer-4 errors. 21 are the standard of
  comparison (*come quei che…*), where `obl` is the UD convention and `case` is unstable rather
  than wrong; 12 are genuine `case` errors on a real prepositional oblique; 6 are blocked or
  entangled. See [`CORRECTIONS.md`](CORRECTIONS.md)'s *Step 4, slice 1*.
- **A fourth adjudication class, and the largest**: the contradictions where `skel` already
  dissents from `dep`, **102 corpus-wide** — worked exhaustively by slice 2, 81 of them Layer-4
  errors. This is the population the annex's expected value was always about; the impossible
  pairings were a smaller, differently-shaped list that happened to be found first.
- **Layer-2 mistags this annex surfaced and did not act on**, all single-pronoun tokens whose
  `pos` gives the right count, so nothing is blocked: the comitatives `meco`/`teco`/`seco` are
  tagged four different ways (and `vosco` twice as `adjective`, once with the lemma `boscoso`),
  `ne` at *Paradiso* 14:55 carries the lemma `in+esso`, and `me'` (apocopated *meglio*) is tagged
  `pronoun` at Inferno 1:112. Step 4's slice 1 added two more, both of which **blocked a Layer-4
  edit**: *Purgatorio* 31:25 `fossi` (the noun "ditches", tagged `verb`, so Layer 4's `aux`
  follows Layer 2) and *Purgatorio* 23:126 `torti` (tagged `noun`, where the *drizza*/*torti*
  antithesis argues for the predicative adjective Layer 2 uses at *Paradiso* 13:129). These
  belong to a `morph/` round of their own.

## Why this exists

Layer 5's residual is documented reading disagreement, and its largest *decidable-looking*
remnant is one question the existing layers structurally cannot answer: **is a pronominal clitic
accusative or dative?**

```
mi pesa            "it weighs on me"      -> mi is dative     (iobj)
m'avea 'mmonito    "he had warned me"     -> mi is accusative (obj)
```

`mi` / `ti` / `si` / `ci` / `vi` / `ne` are identical in form in both cases. Neither the token
stream (Layer 1), the morphology as it stands (Layer 2 has gender/number/person/tense/mood but
**no case**), nor the dependency tree (Layer 4 — the tree shape is the same; the deprel *is* the
disputed judgment) distinguishes them. What decides it is the governing verb's argument
structure.

Layer 5's audit surfaced this as a concrete population and then had to park it:

- **Phase 5h** measured 97 divergences where Layer 4 and the LLM disagree exactly here.
- **Phase 5i** closed the 26 that a *structural* argument could settle (the predicate already
  carried a second `obj`, and UD allows at most one) — hand-verified, retagged in `dep/`.
- **The other 67, plus the mirror-direction cases** (Layer 4 `iobj`, LLM `obj` — `mi bagna`,
  `mi tormenta`, `ti conforta`) were parked with an explicit reason: *"both need a Layer-2 case
  feature or a clitic lexicon"* ([`../skel/PLAN.md`](../skel/PLAN.md), section 1).

In the `role_mismatch` pair table that population is `'obl:a' vs 'obj'` (61) and
`'obj' vs 'obl:a'` (28) as of the post-Phase-5q state; the mirror figure was 30 before that
round. **Re-measure before using any count here** — see *Starting from a cold session* below.
This plan is the instrument those verdicts named.

## What it is — and what it is not

**It is:** one more Layer-2-style morphological column, authored the same way every other Layer-2
column was — an LLM reading the Italian source and nothing else, frozen as TSV, round-trip
checked, content-hashed.

**It is not a lexicon.** The rejected alternative — importing a valency dictionary that says
`pesare` takes a dative and `ammonire` an accusative — brings an external authority into a
corpus whose whole premise is that every layer is a function of the Italian source alone. This
plan does not do that, and the sibling proposal it was paired with (**a verb lexicon** for the
complement-vs-adjunct distinction) stays rejected for exactly that reason.

**The neutrality question, answered.** The *Neutrality audit* invariant in
[`../PLAN.md`](../PLAN.md) is a constraint on **inputs to the build prompt**: no reference
translation, no entity list, no external canon. A case pass over the Italian source satisfies it
on the same terms `pos` and `deprel` already do — those are model judgments too, informed by the
model's internalized knowledge of Italian. Case is not a special case of external canon; treating
it as one would condemn every existing layer.

## The real risks

Two, and neither is neutrality.

### 1. Independence — the design constraint that matters most

Layer 5 is valuable **because the LLM's skeleton is an independent read of the same text**: a
divergence can therefore indict Layer 4, not just the model. A case column can either strengthen
that or destroy it, depending entirely on how it is generated.

- **Wrong**: measure the 91 disputed positions, then ask the model about *those positions*. That
  manufactures an artifact to close violations. It is the failure mode
  [`../dep/CORRECTIONS.md`](../dep/CORRECTIONS.md) already names — *pick the deprel the corpus
  uses for that word, not the one that closes the violation* — applied one level up.
- **Right**: generate case for **every clitic in the corpus, blind** to which positions are
  disputed, in a pass that is shown neither `dep/` nor `skel/`. The result is then a genuine
  **third independent read**, and `dep` / `skel` / `case` can be adjudicated 2-of-3 mechanically.

The blind pass is the only version worth building. If cost pressure ever suggests narrowing it to
the flagged set, the correct response is to abandon the plan, not to narrow it.

### 2. There is no deterministic checker for case

Every other layer has a mechanical ground truth to check against — Layer 3 spans must reproduce
verbatim source substrings, Layer 4 is a well-formedness-checkable tree, Layer 5 has
`derive_unit`. **Case has none.** The available hard checks are formal only:

- closed vocabulary,
- 1:1 alignment to the Layer-1 token stream,
- the column is non-empty **only** on pronoun-POS tokens (Layer 2 decides which those are).

Beyond that, the only cross-check is `dep`'s `obj`/`iobj` — which is the very thing under
adjudication. So this layer's correctness rests on the model's **self-consistency**, and that is
a measurable property, not an article of faith. Measuring it is step 1 below.

## Why its own directory

Decided before writing: `case/` is a sibling directory, **not** a new column in `morph/*.tsv`,
even though case is conceptually a Layer-2 morphological feature.

1. **Hash blast radius.** Adding a column to `morph/*.tsv` changes the content hash of all 100
   morph artifacts — for a column that is empty on 97% of tokens. `morph` is read by `np`, `dep`
   and `skel`, plus the external consumers (`dante-analyze`, `dante-dravidian`) that
   [`../PLAN.md`](../PLAN.md)'s *Versioning* section promises granular invalidation to. A sibling
   directory adds one key to `hashes.LAYERS` and **moves no existing hash**.
2. **Provenance stays visible.** The existing morph columns are one pass, one model, one moment.
   This one is a later pass, a different model, covering clitics only. Since the entire value of
   the artifact is *being an independent third read*, that independence should be legible in the
   file layout rather than merged away.
3. **Revertibility.** This is an experiment that the pilot may kill. `rm -rf case/` must return
   the repo to an untouched state.

**Merging into `morph/` later stays open** and is the natural end state if the column proves out.
The reverse — extracting a column from `morph/` after consumers have recorded its hash — is much
worse, so the order is: build separately, prove, then consider merging.

## Design sketch

Mirrors the existing per-layer pattern exactly (own driver, own README, own CORRECTIONS, own
Makefile; `morph/morph.py` is the reference implementation for the driver).

```
case/            <canticle>/NN.tsv   line, token, word, case
  case.py        LLM build driver + --check / --stats   (mirrors morph/morph.py)
  README.md      closed vocabulary, generation rules, validation tiers, usage
  CORRECTIONS.md measurement and adjudication history
  Makefile       all / check / stats
dante_corpus/case.py   dataclass, TSV I/O, serve-time index
```

- **Scope**: pronoun-POS tokens. The clitic subset (`mi ti si ci vi ne lo la li le gli` and their
  elided forms) is what the adjudication needs; whether to cover *all* pronouns or only clitics is
  a decision for step 2, taken on measured cost.
- **Closed vocabulary**: to be frozen before the corpus pass, from the pilot's own output rather
  than from a grammar book — the same measure-then-freeze order every other layer used. The
  expected shape is nominative / accusative / dative / oblique, with the last covering partitive
  `ne` and locative `ci`/`vi`.
- **Serve surface**: `Canto.case()`, `dante-corpus text case`, `"case"` appended to
  `hashes.LAYERS` (additive — no existing hash changes).
- **Consumption by Layer 5**: `skel._classify_divergence` already accepts an optional
  `morph_pos_by_position`; a `case_by_position` argument fits that existing shape. **Layer 5's
  checker is a consumer, never the owner** — the adjudication report itself belongs to
  `case/ --check`.
- **Adjudication output, not exemption**: where `case` contradicts `dep`, the result is a
  candidate list for a **hand-verified Layer-4 correction round** in the style of Phases 5i/5n —
  not a checker rule that silences the violation. Layer 5's soft count falls because `dep` got
  more correct, which is the same mechanism every audit round in Phase 5 used.

## Starting from a cold session — everything the pilot needs

**Historical as of 2026-07-31 — step 1 is done and its numbers came in.** This section is kept
because it is the record of what the pilot was executed against, and because *Which model* and
*Who runs it* still govern step 3. For the current state and the next action, read
[*Step 4*](#step-4--the-next-action) instead; the figures below describe the
corpus as it was on 2026-07-29, before the annex's two `morph/` correction rounds.

It exists so a session that has only read [`../PLAN.md`](../PLAN.md) and this file can execute
step 1 without reconstructing context from the Phase 5 history.

### Confirm the state first

```bash
make -C skel check     # was: 0 hard, 3551 soft   (the state this plan was written at; now 3469)
make -C dep check      # expect: 0 hard, 0 soft
uv run pytest -q       # was: 125 passed          (now 138, with the annex's tests)
make -C skel stats     # by-kind + the role_mismatch pair table
```

If those differ, every count in this file is describing a different corpus — **re-measure the
population and update this file before proceeding**. The counts here are already one round old in
one place (the mirror pair was 30 pre-5q, 28 after), which is exactly the failure this check
catches.

### How to rebuild the disputed population

There is no checked-in harness; every Phase 5 measurement used a throwaway script. **Copy the
skeleton from [`../skel/PLAN.md`](../skel/PLAN.md)'s *How to measure a candidate rule*** — it
loops the corpus, monkeypatches `dante_corpus.skel._classify_divergence`, and gives access to the
whole dep sub-tree and Layer-2 POS of each unit. Two things from that section are load-bearing:

- Run the script **from `skel/`** (`cd skel && uv run <script>.py`) so `import skel as driver`
  resolves to the build driver.
- Token positions are **1-based over the alpha-only tokens** of a line
  (`[t for t in tokenize(text) if has_alpha(t)]`). Indexing raw `tokenize` output silently
  misaligns every word you print — this has bitten previous rounds.

The two buckets, per [`../skel/PLAN.md`](../skel/PLAN.md) section 1's *How to regenerate any of
these populations*:

| bucket | selector | ~count |
|---|---|---|
| the parked 67 | `role_mismatch` with given `obl:*` / derived `obj`\|`subj`, argument has **no** `case` child, argument POS is pronoun, predicate has **no** second `obj` child | 67 |
| the mirror cases | given `obj`\|`subj` / derived `obl:*`, where the argument's dep deprel is `iobj` | 28 |

**Control group** (needed for the kill gate, and not optional): clitic tokens where `dep` and
`skel` already **agree** — same clitic word forms, same terzina-shaped context, drawn corpus-wide,
sampled to roughly the size of the disputed set. Without it, a raw self-agreement number means
nothing: a model that answers "accusative" to everything scores perfectly on consistency.

### Which model — the pilot must use the artifact's author

**`google:gemma-4-31b-it` (Gemini API)**, i.e. the second line of [`../model.mk`](../model.mk),
which is what the production layers were built with. Note that `model.mk`'s **default `MODEL` is
`ollama:gemma4:31b-it-qat`, the local debug backend** — the same model, but the quantized local
serving path, used for cheap smoke tests.

This is not a detail. The kill gate measures a property *of the model that would author the
column*, so measuring the debug backend and killing the plan on that number would be a wrong
verdict for the wrong reason. Set the model explicitly in the pilot script rather than relying on
the Makefile default.

Call it through `llm7shi.Client`, as every build driver does; `morph/morph.py` is the reference
implementation for prompt shape, chunking and multi-turn recovery. The pilot is a throwaway, so
it needs neither `StatusLine` wiring nor resumability — but it **must** show the model the
terzina and nothing else: no `dep/` row, no `skel/` row, no hint that the position is disputed.
That blindness is the whole point (see *Independence* above).

### Who runs it

**The harness is the assistant's work; the calls are the user's** — a few hundred calls,
~1 hour, no artifact written. (This plan originally assigned the whole pilot to the assistant;
in the event the user ran the calls, as they do for every other LLM-scale job here.) Step 3 is `--fix`-scale LLM regeneration and follows the
convention Phase 5 settled on: **the user runs the corpus-scale generation**
(cf. [`../skel/PLAN.md`](../skel/PLAN.md), where `make -C skel fix` is explicitly the user's).

### Where the numbers go

Create **`case/CORRECTIONS.md`** and record the pilot there — agreement rates, the control
comparison, the model and date, and the verdict. **Do this even if the verdict is to kill the
plan.** This repository's discipline is that rejected candidates are recorded with their
measurements (see the *rejected variants* throughout [`../skel/CORRECTIONS.md`](../skel/CORRECTIONS.md)
and its *What is deliberately not proposed* counterpart in the plan); a killed case annex with a
measured reason is a finished piece of work, not a failure to clean up. The scripts themselves
live alongside it (`population.py`, `pilot.py`, `report.py`) on the branch `case-pilot`, so the
measurement is reproducible rather than merely reported; the branch is the revert path if the
verdict is to kill the annex.

## Sequencing

1. **Pilot: measure self-consistency. This is a kill gate, not a formality.**
   Over the disputed clitic positions rebuilt as described above, ask for case **three times
   independently** (fresh sessions; vary the surrounding-context presentation so the runs are not
   trivially correlated), and over the control group the same way.
   Report per-position agreement for both. Harness in `case/` on the branch `case-pilot`; **no
   artifact is written** — the deliverable is `case/CORRECTIONS.md`. Cost, as sized against the
   rebuilt population: 190 positions × 3 runs = **570 calls**, ~1 hour.
   - **Stop rule, fixed in advance**: if the model does not agree with itself on the disputed
     positions at a rate clearly above noise — with the control sample of *undisputed* clitics as
     the yardstick for what stable answering looks like on this corpus — the column is measuring
     noise and **this plan ends here**. A case column that waffles on exactly the cases it was
     built for is worthless regardless of its aggregate accuracy.
     *(Corrected wording. As first written this asked for disputed agreement **higher than** the
     control's, which is unpassable by construction — the control is the ceiling, being the
     positions two reads already agree on. The bar itself was not moved after the numbers came
     in; see [`CORRECTIONS.md`](CORRECTIONS.md)'s *How the stop rule was read*.)*
   - Also report the *direction* of the answers: if the model systematically sides with `dep`, or
     systematically against it, that is itself the finding, and it changes what step 3 does.
2. **If the pilot passes: freeze the vocabulary and scope, then write the driver.** ✅ **done
   2026-07-30** — see *Step 2 result* above and [`README.md`](README.md). The sizing below is what
   the decision was taken against; the pass went to the full pronoun population rather than the
   clitic subset, and the unit of work is the parse unit rather than a fixed line count, so the
   measured cost is 1340 calls at the default `--chunk 12` (1069 at 15, 888 at 18). Sizing, from
   the current corpus:

   | population | count |
   |---|---|
   | source lines | 14233 (100 cantos) |
   | Layer-2 tokens | 101601 |
   | pronoun-POS tokens | 12332, over 8542 lines |
   | clitic-form subset | 3241, over 2998 lines |

   `morph/morph.py` runs 3 lines per LLM call, so a full Layer-2 regeneration would be ~4700
   calls. A case-only pass over the 2998 clitic-bearing lines, with one output row per clitic,
   can carry more lines per call (6–10) and lands at roughly **300–500 calls** — well under a
   quarter of Phase 5q's `--fix` pass (1702 calls, ≈28 h, 3-way parallel).
3. **Blind corpus pass, freeze, then adjudicate.** Generate, validate, commit, *then* join
   against `dep`. Never the other way round. ✅ **done 2026-07-31** — four runs, 1340 chunks, all
   100 cantos at **0 hard**, 13112 tokens / 13176 values, frozen at `0027494` **before** `--stats`
   was run. The order was kept literally, which is the only part of it that cannot be recovered
   after the fact.
4. **Layer-4 correction round** over the contradictions, hand-verified against the terzine, in the
   style of Phases 5i/5n. `make -C dep check` must stay 0/0 throughout. *Under way* — the input
   was: **461 contradictions, 49 impossible pairings**. Slices 1 and 2 are done — 91
   positions, 103 rows — and slice 3 is the open question; see *Step 4* above.
5. **Re-measure Layer 5** and record the delta in [`../skel/CORRECTIONS.md`](../skel/CORRECTIONS.md).
   *Done for each slice as it landed*, which is the only way the per-slice deltas are
   attributable — but note Layer 5 has already moved twice for reasons that are not step 5's:
   3551 → 3550 from step 3's `morph/` corrections, 3550 → 3555 from step 4's slice 1 (which
   raised it deliberately) and 3555 → **3469** from slice 2. Read
   [`../skel/CORRECTIONS.md`](../skel/CORRECTIONS.md)'s entry on why a correct Layer-4 round can
   raise the count before interpreting any delta this step measures.

## Expected value — stated honestly before starting

**≈90–100 soft violations of the 3551**, i.e. the disputed clitic population and little else.
This does not reach 0 and does not come close: the bulk of the residual is subject resolution
across enjambment and pro-drop (`extra_arg subj` 865), which no case feature touches. Anyone
reading this plan as a route to zero has misread it — it converts **one specifically identified
undecidable class into a decidable one**, and its second, less quantifiable return is a corpus
where the clitic case of every pronominal mention is queryable at all, which is useful to
downstream consumers independently of Layer 5's violation count.

If that trade looks poor at the pilot stage, the correct outcome is to stop and leave the
residual documented as reading disagreement, which is where
[`../skel/PLAN.md`](../skel/PLAN.md) left it.
