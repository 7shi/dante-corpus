# case — a pronoun case annex to Layer 2

## Status

**Step 4 is complete. All three slices are done and every one of the 510 adjudication candidates
has a verdict.** All 100 cantos, frozen since `0027494` — 13112 pronoun tokens / 13176 case values
then, **13125 / 13189** after the 2026-08-02 `morph/` round and its chunk regeneration.
Across the three slices the round edited **215 positions / 270 rows** in `dep/`, with
`dep --check` at 0/0 throughout and the `case/` artifact never touched.

| slice | population | candidates | edited | yield | Layer 5 |
|---|---|---|---|---|---|
| 1 ✅ | `obl` × `nominative` impossible pairings | 49 | 10 | 20% | 3550 → **3555**, +5 |
| 2 ✅ | contradictions where `skel`'s given role sides with `case` | 102 | 81 | 79% | 3555 → **3469**, −86 |
| 3 ✅ | the contradictions `skel` does **not** flag | 325 | 124 | 38% | 3469 → **3634**, +165 |

**Slice 3 was run rather than skipped**, and its rise was predicted before it started: it is the
slice-1 configuration, where `dep` and `skel` agree and only `case` dissents, so a correct fix
breaks an agreement. **3634 is a worse number and a better corpus than 3469.** The selector this
plan established decided the sign three times out of three and now predicts yield over 476
candidates as well. See [`CORRECTIONS.md`](CORRECTIONS.md)'s *Step 4, slice 3* and
[`../skel/CORRECTIONS.md`](../skel/CORRECTIONS.md).

Agreement with `dep` is now **90%** on `obj`, **96%** on `iobj`, **99%** on `nsubj`, and the
contradiction list is **258** (was 462 before step 4; 260 at step 4's close, and the
regeneration below re-answered two positions in agreement with `dep`).

**Step 5's owed `morph/` correction round landed on 2026-08-02** — 10 hand-verified singletons and
the 58-token comitative family, in
[`../morph/CORRECTIONS.md`](../morph/CORRECTIONS.md). It moved the pronoun scope to **13125 tokens
/ 13189 values**, which left `case --check` at 25 hard over 20 lines, all of them `[count]`
mismatches. **That regeneration has been run and `--check` is back to 0 hard** — the deltas are in
[`CORRECTIONS.md`](CORRECTIONS.md)'s *the chunk regeneration the `morph/` round owed*; the gain is
almost all `ablative` (1805 → 1819), the newly in-scope comitatives, and `genitive`/`locative` did
not move at all. **Step 5's other open sub-item, the
`locative` question, was settled the same day: it is earned and stays** — analysis only, no
artifact moved and no vocabulary change for the merge to carry.
What remains after that is the
`morph/` merge itself — and the annex's own verdict is that a **blind regeneration of `case` under
a corrected prompt** is the next instrument, not another Layer-4 slice. The column's two measured
weaknesses are both prompt-fixable and both were recorded rather than patched: **194 `case`-side
errors across the three slices, none rewritten.**

The vocabulary and scope are frozen and the code exists — [`case.py`](case.py) (build driver,
`--check`/`--stats`/`--clean`), [`README.md`](README.md), [`Makefile`](Makefile),
`dante_corpus/case.py`, `Canto.case()`, `dante-corpus text case`, `"case"` appended to
`hashes.LAYERS`, and `tests/test_case.py`. Everything lives on the branch `case-pilot` so the
whole annex can be dropped in one move. Written 2026-07-29, immediately after Layer 5's
Phase 5 closed at **0 hard, 3551 soft** (see [`../skel/PLAN.md`](../skel/PLAN.md)'s *Where
Phase 5 ended*).

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

**Resuming? Read [*Resuming cold — after step 4*](#resuming-cold--after-step-4) first**, then
[*Step 4*](#step-4--complete) for the detail.
[*Starting from a cold session*](#starting-from-a-cold-session--everything-the-pilot-needs)
carries the step-1 context (how the disputed population was rebuilt, which model, who runs what)
and is now historical. Everything between them is rationale.

## Resuming cold — after step 4

**Written 2026-08-01 at the close of step 4, so a session with no memory of it can carry on from
this section alone.** Branch `case-pilot`.

### Where things stand

| commit | what |
|---|---|
| `0027494` | the frozen `case/` artifact — 100 cantos, 0 hard. **Do not touch it** |
| `419120b` | slice 1's Layer-4 edits: 10 positions / 11 rows |
| `40c8a11` | slice 1's measurements and the step-4 selector change |
| `439f6af` | slice 2's Layer-4 edits: 81 positions / 92 rows |
| `bedfd97` | slice 3's Layer-4 edits: 124 positions / 167 rows |
| *the `morph/` round* | 2026-08-02, 41 canto artifacts — 10 singletons + 58 comitatives |

```bash
git status --short          # expect clean
uv run pytest -q            # expect 142 passed
make -C morph check         # expect 0 hard, 0 soft
make -C np check            # expect 0 hard, 0 soft -- see below
make -C dep check           # expect 0 hard, 0 soft
make -C skel check          # expect 0 hard, 3635 soft
make -C case check          # expect 0 hard  -- regenerated 2026-08-02
```

`case --stats` reads **258 contradictions / 40 impossible pairings** over 13125 tokens / 13189
values (260 / 40 over 13112 / 13176 at step 4's close).

If `skel` reads 3469, slice 3 is not in the tree; if it reads 3633, Layer 3's clitic
reconciliation is not; if it reads 3634 and `case` reads 0 hard, the `morph/` round is not either.

**`np` read 5 hard / 96 soft and that belonged to this annex; it was closed on 2026-08-02.**
Step 3's Layer-2 correction rounds (`880fc2e`, `a97b80e`) moved the lemma parts of fused clitic
tokens to unblock the case pass, and the 2026-08-02 `morph/` round moved more of them; `np`'s
checker derives its expected `+X` clitic mentions from exactly those lemma parts, so the frozen
Layer-3 artifacts went stale. `morph`, `dep` and `skel` were re-measured at the time and `np` was
not. It is now back to **0/0** — `--fix-clitics` was made symmetric (94 mentions added, 6 dropped)
and two non-clitic soft were fixed by hand, one of which unblocked the Layer-4 deferral at
purgatorio 20:83 and took `skel` to **3635**. Full description in
[`../PLAN.md`](../PLAN.md)'s *The clitic reconciliation* and
[`../np/CORRECTIONS.md`](../np/CORRECTIONS.md).

### What step 4 settled, so none of it is re-litigated

1. **All 510 candidates have a verdict.** The 258 contradictions that remain are not unfinished
   work; they are the measured residue, and 53% of the sample taken from them was the `case`
   column being wrong, not Layer 4.
2. **The artifact stays frozen.** Asked and answered in slice 1, and held through 194 recorded
   `case`-side errors.
3. **`case.py`'s `_IMPOSSIBLE` rule stays as it is.**
4. **Layer 5's soft count is a diagnostic, not the objective.** It rose 5, fell 86 and rose 165
   across three correct rounds. None of those numbers decided whether an edit was right.
5. **The selector is measured, not argued** — direction three times out of three, yield 79%
   inside the intersection against 38% and 20% outside.

### The next action

**Step 5's remaining item: the `morph/` merge**, and the two things it must carry.

- **A blind regeneration of the `case` column under a corrected prompt.** The column reads a
  pronoun's case well and word order poorly, in two shapes now counted at corpus scale: it makes
  a relative pronoun nominative whenever the clause postposes a noun (78 instances), and it reads
  the dative of possession as accusative whenever the verb already carries an object (24). Both
  are prompt problems. Regeneration is **LLM-scale work and therefore the user's**, by the
  convention Phase 5 settled.
- **The `locative` question is now settled (2026-08-02): it is earned and stays**, so the
  regeneration keeps all eight values and the vocabulary does not move. By deprel it opens no slot
  — the containment test that acquitted `genitive` fails it outright — but that is the wrong test
  here: **Layer 2's `lemma` collapses `locative`/`accusative`/`dative`/`reflexive` onto the same
  `ci`/`vi` form**, so this column is the only record of whether a given `vi` means *there* or *to
  you*. The round reached the opposite verdict first; the refutation and the guard against
  repeating it are in [`CORRECTIONS.md`](CORRECTIONS.md)'s *Step 5 — the `locative` question*.
- **The fused-token problem**, which a merge into `morph/*.tsv` would finally force: `case`
  annotates a pronoun and `dep` a token, and five contradictions are nothing but that mismatch
  (inferno 2:81.7 *aprirmi*, 23:128.7 *dirci*; purgatorio 8:45.4 *vedervi*, 14:20.1 *dirvi*;
  paradiso 29:92.1 *seminarla*).

**The `morph/` correction round is done (2026-08-02)** — see
[`../morph/CORRECTIONS.md`](../morph/CORRECTIONS.md)'s *The mistags the case annex surfaced and
parked*. It spent all six positions step 4 left (purgatorio 31:25 `fossi`, 23:126 `torti`,
inferno 8:4.5 `i`, purgatorio 31:90.1 `salsi`, 20:83.2 `c'`, 11:137.2 `e'`), plus the four step 3
had parked (`me'`, `ne` at paradiso 14:55, and the comitatives), and **sweeping each reported word
form corpus-wide doubled two of them**: both corpus `me'` tokens are *meglio* and both `salsi`
tokens are the *salsi colui/colei che…* idiom, so each is a family of two rather than the singleton
it was reported as. The comitatives turned out to be **58 tokens under 34 distinct taggings**, not
the "four different ways" the report said, and are normalized to `<pronoun>+con` /
`pronoun+preposition`.

**It left `case/` at 25 hard — the expected handoff, not a break, and now closed.** The scope this
column derives from `morph` moved — **13112 → 13125 tokens, 13176 → 13189 values** — so 20 lines
now need a different number of case values. Every one of the 25 is a `[count]` mismatch; none is
the model getting the Italian wrong. Closing them is `make -C case clean` then `make -C case`,
LLM-scale work and so the user's, exactly as step 3's two rounds went. `skel` went 3634 → **3633**,
and two of the three moves are Layer 5 independently confirming this round's readings (purgatorio
11:137 `e'` and 16:141 `vosco` each closed a membership violation). `np` went 3 hard / 64 soft →
**5 / 96**, widening what was then the open defect rather than adding a new one; it has since
been reconciled back to 0/0 (see the state check above).

### The traps, in the order the three slices hit them

- **Layer 2 can block a Layer-4 edit, and that outranks the reading.** Slice 1 lost two edits to
  it, slice 3 one. Check `morph`'s `pos` before proposing a retag.
- **The corpus-internal convention sweep is what makes an edit defensible**, and it decided more
  of every slice than the reading did. Slice 3's own table of measured conventions is in
  [`CORRECTIONS.md`](CORRECTIONS.md); the sharpest is `gravare`, where the same lemma took an
  edit in one construction and stopped one in the other.
- **Layer 5's LLM is a third read too, and it can be right when you are not.**
- **Judge from the rows, never from the summary.** This annex has been wrong five times in that
  exact shape.

### The `case` column's measured weakness, for the `morph/` merge

Across the three slices the column's errors are not scattered, and slice 3 put counts on them:
**the postposed subject (78)** and **the dative of possession alongside an explicit object (24)**.
It reads a pronoun's *case* well and its *word order* poorly. Both fixes belong to a blind
regeneration at the `morph/` merge, never to an edit of the frozen artifact.

## Step 4 — complete

**A hand-verified Layer-4 correction round over the contradiction list, in the style of Phases
5i/5n, run in three slices and closed on 2026-08-01.** `make -C case stats` regenerates the
input; nothing in it was ever applied mechanically.

```bash
make -C case stats     # census, oblique tail, dep agreement, contradictions, impossible pairings
cd case && uv run case.py inferno purgatorio paradiso --stats --full
```

`make -C case stats` truncates the candidate lists so the report stays readable; `--full` is what
each round worked from.

### What the join found, and what the three slices spent

| `dep` | reads as | agree | contradict | rate | before step 4 |
|---|---|---|---|---|---|
| `obj` | `accusative` | 1685 | 178 | 90% | 1631 / 317, 84% |
| `iobj` | `dative` | 755 | 28 | 96% | 669 / 46, 94% |
| `nsubj` | `nominative` | 5130 | 54 | 99% | 5076 / 98, 98% |

**260 contradictions, 40 impossible pairings** (from 461 and 49). The impossible pairings went
*up* by one, deliberately: purgatorio 17:45.4's standard of comparison moved `obj` → `obl` and
thereby joined the list slice 1 had already settled.

**The selector, established by slice 1 and confirmed twice.** Rank candidates not by whether
`case` and `dep` contradict, but by **whether `skel` already diverges from `dep` at that
position**:

- Where `dep` and `skel` **agree** and only `case` dissents, a correct Layer-4 fix *breaks* an
  agreement and **raises** Layer 5's count. Slices 1 and 3 are that configuration; they moved it
  +5 and +165.
- Where `skel` **already dissents from** `dep`, a third read that sides with `skel` breaks a 2-1
  tie and **closes** the violation. Slice 2 is that configuration: 102 candidates, −86, against a
  prediction of ≈90–100.

It predicts **yield** as well as direction: 79% of tier A were Layer-4 errors, against 38% of the
unflagged 325 and 20% of the impossible pairings. It never replaced verification — 194 positions
across the three slices were `case`-side errors and were left alone.

### How to inspect a position

There is no checked-in harness; each round uses a throwaway script. The serve API's shapes, which
cost four failed attempts to rediscover the first time:

```python
from dante_corpus import canto
c = canto("inferno", 1)
c.lines()          # tuple[Line];  Line.no (not .number), Line.text, Line.tokens
c.dep()            # dict[int, tuple[DepRow]] keyed by line — NOT a flat sequence
                   #   DepRow(line, token, word, deprel, head_line, head_token)
c.case()           # dict[int, tuple[CaseRow]] keyed by line
                   #   CaseRow(line, token, word, case); .cases() splits a fused token
c.morph()          # dict[int, tuple[MorphRow]] — the pos/lemma a retag must not contradict
c.skel()           # tuple[SkelTuple]; SkelTuple.args carry role/line/token
```

`token` is **1-based over the alpha-only tokens** of a line, the same convention Layers 2–5 use
(`[t for t in tokenize(text) if has_alpha(t)]`). Indexing raw `tokenize` output misaligns every
word you print — it has bitten previous rounds in `skel/` too.

### Then step 5

Layer 5 was re-measured after each slice and the deltas recorded in
[`../skel/CORRECTIONS.md`](../skel/CORRECTIONS.md) as they landed. What is left of step 5 is the
`morph/` merge — see *Resuming cold* above.

### The three parked questions — now answered

Measurements in [`CORRECTIONS.md`](CORRECTIONS.md)'s *fourth run and the freeze*.

- **The oblique tail: fold nothing.** The deciding evidence is the `dep` deprel distribution,
  not the word forms. **`ablative` (1805)** is `obl` at 82% — the prepositional oblique.
  **`genitive` (267) is earned**: 189 of it (71%) is adnominal (`nmod` 139, `det:poss` 50), and
  `det:poss` is a slot `ablative` fills **zero** times — `lor danno`, `il senso lor`, `le gambe
  loro` are possessive determiners, not obliques. **`locative` (81) is earned** (settled
  2026-08-02) — **but on different grounds, and the deprel test gets it wrong.** By deprel it
  opens no slot: there is no relation `locative` fills that `ablative` does not, and its 2%
  adposition rate against `ablative`'s 74% is a clitic-vs-tonic confound that vanishes against
  `ablative`'s own bare clitic `ne`. What earns it is that **Layer 2's `lemma` collapses the
  readings of its forms**: lemma `vi` spans `locative` 44 / `accusative` 21 / `dative` 15 /
  `reflexive` 4, lemma `ci` spans five values, and `ci`/`vi` carry `ablative` zero times — so
  whether a given `vi` is *there* or *to you* is recorded nowhere else in the stack. The round
  recommended folding it first and was wrong. `vocative` (30) is
  frozen-but-unearned — correct and harmless, but argued from the poem's rhetoric rather than a
  count. `reflexive`, the other value added rather than measured, is vindicated at 1961 — 15% of
  the column, and mistagging it was what the Inferno 1 smoke test caught.
  **An earlier reading of this tail recommended folding `genitive` and was wrong**; the argument,
  the refutation and the lesson are in [`CORRECTIONS.md`](CORRECTIONS.md)'s *The subset argument
  was wrong*. No rows were rewritten.
- **The third adjudication class is real**, at 49 corpus-wide — and step 4's slice 1 worked all
  49. It is smaller than it looks: only 10 were Layer-4 errors. 21 are the standard of
  comparison (*come quei che…*), where `obl` is the UD convention and `case` is unstable rather
  than wrong; 12 are genuine `case` errors on a real prepositional oblique; 6 are blocked or
  entangled. See [`CORRECTIONS.md`](CORRECTIONS.md)'s *Step 4, slice 1*.
- **A fourth adjudication class, and the largest**: the contradictions where `skel` already
  dissents from `dep`, **102 corpus-wide** — worked exhaustively by slice 2, 81 of them Layer-4
  errors. This is the population the annex's expected value was always about; the impossible
  pairings were a smaller, differently-shaped list that happened to be found first. The **325**
  contradictions `skel` does not flag were worked by slice 3, 124 of them Layer-4 errors and 171
  of them `case`-side errors.
- **The Layer-2 mistags this annex surfaced are now corrected** (2026-08-02), in the `morph/`
  round of their own that this bullet asked for. They were: the comitatives
  `meco`/`teco`/`seco`/`nosco`/`vosco`; `ne` at *Paradiso* 14:55 with the lemma `in+esso`; `me'`
  (apocopated *meglio*) tagged `pronoun`; slice 1's *Purgatorio* 31:25 `fossi` (the noun
  "ditches", tagged `verb`, so Layer 4's `aux` followed Layer 2) and 23:126 `torti` (tagged
  `noun`, where the *drizza*/*torti* antithesis argues for the predicative adjective Layer 2 uses
  at *Paradiso* 13:129), **both of which had blocked a Layer-4 edit**; and slices 2–3's `i`,
  `salsi`, `c'` and `e'`. Full record and the corpus-internal precedent behind each tag in
  [`../morph/CORRECTIONS.md`](../morph/CORRECTIONS.md).

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
make -C skel check     # was: 0 hard, 3551 soft   (the state this plan was written at; now 3635)
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
   style of Phases 5i/5n. `make -C dep check` stayed 0/0 throughout. ✅ **done 2026-08-01** — the
   input was **461 contradictions, 49 impossible pairings**, and all three slices are closed at
   **215 positions / 270 rows**; see *Step 4* above.
5. **Re-measure Layer 5** and record the delta in [`../skel/CORRECTIONS.md`](../skel/CORRECTIONS.md).
   *Done for each slice as it landed*, which is the only way the per-slice deltas are
   attributable — but note Layer 5 has already moved twice for reasons that are not step 5's:
   3551 → 3550 from step 3's `morph/` corrections, 3550 → 3555 from step 4's slice 1, 3555 →
   3469 from slice 2, and 3469 → **3634** from slice 3 (slices 1 and 3 raised it, correctly and
   by design). Read
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
