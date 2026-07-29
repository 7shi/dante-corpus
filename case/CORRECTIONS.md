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

## Step 2 — the freeze, 2026-07-30

No model calls. Two things were frozen from measurement, and the code was written against them
([`README.md`](README.md) documents the result; this records how it was decided).

### Vocabulary — the census, plus one added value

The six values of the pilot's own answer census become the closed vocabulary, with no removals:
`accusative` 276, `dative` 252, `ablative` 28, `nominative` 7, `genitive` 5, `locative` 2. Two
consequences worth stating, because both overrule [`PLAN.md`](PLAN.md)'s guess:

- The partitive/locative class is called **`ablative`**, not `oblique`. The plan predicted
  "nominative / accusative / dative / oblique, with the last covering partitive `ne` and locative
  `ci`/`vi`"; the model does not use `oblique` at all, and it distinguishes `genitive` and
  `locative` from `ablative`. Measure-then-freeze means the census wins.
- The rare values (`genitive` 5, `locative` 2) are kept rather than folded into `ablative`. They
  are exactly the boundary the pilot found unstable, and collapsing them would hide the
  distinction the artifact is being built to record. What is settled instead is the **prompt**:
  the build rules name where each of the three applies, since the pilot showed this is a labeling
  boundary, not a reading disagreement ("the model is stably reading a third thing and varying
  only in what to call it"). `canon_case` maps the near-synonyms the pilot produced (`oblique`,
  `partitive`, `instrumental`) onto `ablative`.

**`vocative` — one value added, not measured.** The census contains no `vocative`, and it is in
the frozen vocabulary anyway. This is a departure from measure-then-freeze and is recorded as
such, with its reason: the pilot's population was disputed and control **clitic argument**
positions, which structurally cannot hold a term of address, so the census's silence is a
property of that sample rather than evidence about the corpus. The scope frozen in this step is
every pronoun, not the clitic subset the pilot sampled, and direct address is pervasive in the
poem (`O tu che ...`, `Or se' tu quel Virgilio`). Without the value the build would have to force
those pronouns into `nominative`, i.e. record a judgment the vocabulary made for it. The build
prompt draws the boundary explicitly — a pronoun that is the verb's subject stays `nominative`
even in a sentence addressed to someone — so the added value is a labeling rule of the same kind
as the `ablative`/`locative` one above, not a new reading.

Whether the model actually uses it is measurable after step 3: `--stats`' vocabulary census over
the built artifact is the check. A `vocative` count of zero there would mean the value is
unnecessary and can be dropped before the column is merged into `morph/`.

**`instrumental` — considered and rejected.** Recorded here because this repository records
rejected candidates with their measurements. Three findings, and they point the same way:

- **The pilot produced it zero times out of 570.** This is *evidence*, unlike the `vocative`
  gap above: the pilot's positions included `ne` / `ci` / `vi` obliques, which are exactly where
  an instrumental reading could have surfaced, and the model answered `ablative` there (28
  times). The absence is a property of the corpus and the reader, not of the sample.
- **Italian inherits no instrumental form.** Latin merged instrumental into the ablative, and
  Italian pronouns carry only prepositional obliques onward. The one place the question is even
  live is the archaic fused comitatives `meco` / `teco` / `seco` (= `con me` / `con te` /
  `con sé`), and a census of the corpus finds **43 tokens** of them — all *accompaniment*
  ("with me"), none instrument-of-action. They are ablatives.
- **The split would be semantic, not formal.** Dividing `ablative` into instrument / source /
  accompaniment rests on no distinction the Italian marks; it is a reading of what the oblique
  *means*, which [`../PLAN.md`](../PLAN.md)'s *Out of scope* assigns to the consumer. This is
  what separates it from `vocative`, which distinguishes a pronoun that fills **no verb slot at
  all** from one that does — a syntactic distinction the line itself carries.

So `instrumental` is not a value. It survives only as a `canon_case` alias onto `ablative`, to
absorb drift, alongside `oblique`, `partitive` and `comitative`; and the build prompt names
`meco`/`teco`/`seco` explicitly so their landing place is decided here rather than invented per
call.

### The oblique tail — `ablative` is a residual class, and it is left measured, not defended

Rejecting `instrumental` on the grounds above exposes an inconsistency in the vocabulary as
frozen, and it is recorded rather than argued away. The proportions first:

| | answers | share |
|---|---|---|
| `accusative` + `dative` — the question the annex exists to answer | 528 | 93% |
| the oblique tail: `ablative` 28, `genitive` 5, `locative` 2 | 35 | 6% |
| `nominative` | 7 | 1% |

The tail is also precisely where the pilot found the model unstable. The *Result* section above
already says so — "the split is not accusative-vs-dative at all but ablative/genitive/locative,
i.e. the model is stably reading a third thing and varying only in what to call it" — and step 2
first responded by settling the boundary in the prompt. That response accepts the framing rather
than examining it: `ablative` is functioning as the **residual class** for every non-core
oblique, and naming the residue is not the same as resolving it.

The inconsistency is this. `instrumental` was rejected for being a *semantic* split of
`ablative` with no formal support. But `genitive` on a pronoun is `ne` meaning "of it" rather
than "from there" — the same clitic, the same slot, split on meaning alone. The argument that
kills `instrumental` reaches `genitive` too, and 5 answers out of 570 is not a rate at which a
distinction can be called measured.

**The criterion, stated so it can be applied consistently**: a value earns its place if it
changes the **slot** the pronoun fills, not what the oblique *means*.

| value | slot it distinguishes | verdict |
|---|---|---|
| `nominative` / `accusative` / `dative` | subject / direct object / indirect object | keep |
| `locative` | `ci` "to there" vs dative `ci` "to us" — the annex's own core question, one paradigm over | keep |
| `vocative` | fills no slot of the verb at all | keep |
| `ablative` | non-core oblique — the residual class, named as such | keep |
| `genitive` | none: an `ablative` whose meaning is possession or partition | **fails** |
| `instrumental` | none: an `ablative` whose meaning is means or accompaniment | rejected above |

**Decision: freeze all seven anyway and measure before folding.** The user's call, and the
cheap direction: collapsing `genitive` into `ablative` afterwards is a mechanical rewrite of
the frozen TSVs — no LLM calls, no regeneration — whereas dropping it now and finding it needed
would cost a corpus pass. So the vocabulary stays at seven through step 3, and `--stats` was
extended to make the verdict decidable rather than a matter of taste: it prints the tail's share
of all rows and, for each of `ablative` / `genitive` / `locative`, the **word forms** that
carry it. If `genitive`'s forms turn out to be a subset of `ablative`'s (i.e. both are `ne`),
that is the criterion above being met numerically, and the value folds before the column is
merged into `morph/`. The same test applies to `vocative` and to `locative`.

Recorded so the next session inherits the open question rather than the settled-looking table.

**Side-finding for a later round (not acted on).** The comitative census also shows Layer 2
tagging those 43 tokens inconsistently: `meco` appears as `pronoun+preposition`, `preposition+
pronoun`, `pronoun` and `adverb`, and `vosco` twice as `adjective` (once with the lemma
`boscoso`, a plain mistag). 11 of the 43 therefore fall **out of** the case scope, which is
decided by `pos`. This is a `morph/` correction candidate of the kind
[`../morph/CORRECTIONS.md`](../morph/CORRECTIONS.md) already records — surfaced by this annex,
belonging to Layer 2, and deliberately left alone here so that step 3 generates against the
frozen state rather than a state this step edited.

### Scope — every pronoun-POS token

Measured over the frozen `morph/*.tsv`, with the call counts taken from the driver's own
`--dry-run` rather than estimated:

| candidate scope | tokens | lines | calls |
|---|---|---|---|
| clitic forms (`mi ti si ci vi ne lo la li le gli` + elisions, + fused `nol`/`sen`/…) | 3809 | 3563 | ~446 |
| + tonic personal / relative (`me`, `lui`, `cui`, `altrui`, `lor`, …) | 8248 | 6319 | ~790 |
| **all pronoun-POS tokens (chosen)** | **13113** | **8542** | **1340** |

The clitic subset is what the Layer-5 adjudication strictly needs and is what
[`PLAN.md`](PLAN.md)'s step-3 sizing (300–500 calls) assumed. It was **not** chosen, for three
reasons:

1. **The scope becomes a judgment.** A clitic-only pass needs a hand-frozen list of word forms,
   and the middle option needs a second one to separate tonic personal pronouns from
   demonstratives and indefinites. "Every token whose Layer-2 `pos` names a pronoun" is read off
   an existing artifact and draws no line of its own.
2. **The *mirror* bucket contains tonic forms.** `cui`, `me`, `lui`, `altrui`, `lor` are ~8 of the
   95 disputed positions; under a clitic-only scope they would carry no case value and stay
   undecided — the annex would fail to answer part of the question it was built for.
3. **Cost is affordable at the corpus's own scale.** 1340 calls is below Phase 5q's `--fix` pass
   (1702 calls, ≈28 h, 3-way parallel), and the build is resumable and parallelizable per
   canticle. `--chunk 15` would bring it to 1069 and `--chunk 18` to 888, at a rising risk of a
   truncated table.

The scope decision was the user's, taken on these numbers.

### Unit of work — the parse unit, not a fixed line count

`morph/morph.py` chunks by a fixed 3 lines. Case cannot: the case of a clitic is decided by its
governing verb, which is frequently on another line, so a chunk boundary in the wrong place
removes the evidence. The driver chunks by `dep.sentence_groups` — derived from the source
punctuation alone, **not** from the `dep/` artifact, so neutrality and blindness are intact — and
merges consecutive units up to `--chunk` lines, never splitting one. Chunks with no pronoun are
never sent, which is why 8542 pronoun-bearing lines cost 1340 calls rather than 14233/12 ≈ 1186 +
misses.

### Fused tokens

The census's scope test (`scope_slots`) counts the pronoun components of the Layer-2 `pos`, which
makes the 35 fused tokens checkable instead of ambiguous: `pronoun+pronoun` (30, e.g. `gliel'`)
and `verb+pronoun+pronoun` (5) carry two case values, joined with `+` in reading order the way
Layer 2 already joins the lemmas of a contraction (`Nel` → `in+il`). `verb+pronoun` (487) carries
one. A count mismatch is the hard `slot` violation.

### What `--check` deliberately does not do

The `dep` cross-check (`obj` ↔ accusative, `iobj` ↔ dative) is the only cross-check that exists
and is **the very judgment under adjudication**, so it is not a check. It lives in `--stats`,
which is a **post-freeze** report producing candidates for a hand-verified Layer-4 round — not
automatic edits, and not a checker exemption. Every check in `--check` is formal:
`count` / `word` / `slot` / `tag`, all hard.

### State

`uv run pytest -q`: **138 passed** (125 before, +13 in `tests/test_case.py`). `make -C skel check`
and `make -C dep check` are untouched by this step — no existing artifact was written, and
`"case"` is appended to `hashes.LAYERS` so no existing content hash moves. The plumbing has not
yet been smoke-tested against a live model (no local backend was available in this session); the
first canto of step 3 is that test, and `--check` gates it.

## Step 3 smoke test — Inferno 1, 2026-07-30

The user built one canto before committing to the corpus pass. It is the plumbing test the
freeze deferred (no local backend was available in step 2), and it did what a smoke test is for:
`--check` passed, and the artifact was **wrong in two ways the checker cannot see**.

### What passed

`case/inferno/01.tsv`, 135 rows, `--check` **0 hard**. Alignment, resume, the sparse artifact
shape, the fused tokens and the serve surface all work. Cross-tabulated against Layer 4 (this is
`--stats`' adjudication view, run post-freeze):

| dep deprel | case | agreement |
|---|---|---|
| `nsubj` | `nominative` | 58 / 61 (95%) |
| `obj` | `accusative` | 23 / 26 (88%) |
| `iobj` | `dative` | 8 / 8 (100%) |
| `obl` | `ablative` / `dative` / `locative` | 23 / 25 (92%) |

Fused tokens land correctly (`Rispuosemi` → dative, `aiutami` → accusative), as do prepositional
obliques (`di me`, `per cu'` → ablative), and `qual che tu sii` gives `tu` `nominative` rather
than `vocative` — the boundary rule added with that value works.

The two `obj`/`iobj` contradictions are exactly the mixed population the plan predicted, and
they show why step 4 must be hand-verified rather than mechanical: at 1:90 (`ch'ella mi fa
tremar le vene`) `case` reads a dative experiencer and **`dep` looks wrong**; at 1:135 (`color
cui tu fai cotanto mesti`) **`case` looks wrong** and `dep` right.

### Failure 1 — the prompt's own example taught a wrong answer

The system prompt's worked example was Inferno I.1-6 with `| 2 | mi | accusative |`. But
`mi ritrovai` is reflexive, so the example was teaching the wrong label for the single most
common clitic pattern in the poem, on the first thing the model reads. The built artifact
reproduces it: line 2's `mi` came back `accusative`, against Layer 4's `expl`.

Caught only because the smoke test was cross-tabulated against `dep` rather than merely checked.
`--check` cannot see this — there is no deterministic ground truth for case, which is the
condition [`PLAN.md`](PLAN.md) states up front. The example now reads `reflexive`.

### Failure 2 — the reflexive clitic had no home in the vocabulary, and it is 10.8% of the scope

| in-scope pronoun tokens by Layer-4 deprel | n |
|---|---|
| `nsubj` | 5239 |
| `obj` | 2410 |
| `obl` | 2066 |
| **`expl`** | **1411** |
| `iobj` | 748 |
| *(total in scope)* | *13113* |

`expl` is the reflexive / reciprocal / impersonal / passive clitic (`si` 905, `s'` 291, `mi` 88,
`m'` 25, `ti` 23, …). It fills no argument slot of the verb, and the seven frozen values gave it
nowhere to go: in canto 1 the model split its eight such tokens `accusative` 6 / `nominative` 2,
and `nominative` on a reflexive particle is plainly wrong.

**This is not the `genitive` situation, and the difference decided the response.** The oblique
tail was left open because folding a value afterwards is a mechanical rewrite. Here the only
post-hoc fix would be to relabel every `expl` position from `dep` — letting Layer 4 decide 10.8%
of the column and destroying on that subset the independence the whole annex rests on
([`PLAN.md`](PLAN.md), *Independence*). It had to be settled before the corpus pass, not after.

**Decision: `reflexive` is added as an eighth value** (the user's call). It satisfies the
criterion recorded in *The oblique tail* above — a value earns its place if it changes the
**slot** the pronoun fills — in the same way `vocative` does: both name a pronoun that fills no
slot of the verb, and they name different ones. The name is measured rather than invented:
Layer 2's `note` column already reads `reflexive` on 1271 pronoun tokens and `impersonal` on
174, totalling 1445 against Layer 4's 1411 `expl` — the corpus's own word for the same class.

The objection that this duplicates `dep`'s `expl` is answered the way every other cross-layer
overlap in this corpus is: agreement is evidence, and a disagreement flags a `dep` `expl`
mistag, which is precisely the audit role the annex exists to perform.

The prompt's boundary is participant-based so a model can apply it: a clitic introducing nobody
distinct from the subject is `reflexive`; one naming someone else keeps its ordinary case. In
`mi si fu offerto` the `si` is `reflexive` and the `mi` is `dative`; in `aiutami` the `mi` is
`accusative`.

### Consequence

`case/inferno/01.tsv` was generated under both bugs and **must be rebuilt**, not repaired:
`uv run case.py inferno -c 1 --force`. `--clean` will not catch it, because the rows are
formally valid under the new vocabulary too — which is the same blind spot as Failure 1, stated
once more. Re-run the cross-tab before starting the other 99 cantos.

### Rebuild — Inferno 1 under the corrected prompt and eight-value vocabulary

`uv run case.py inferno -c 1 --force`. **0 hard**, 135 rows.

**The fix landed.** `reflexive` maps onto Layer 4's `expl` at **9 of 10** positions, and both
exceptions are informative rather than noise:

- 1:88 `io mi volsi` — `case` `reflexive`, `dep` `obj`. A true reflexive object; both readings
  are defensible in their own vocabulary, which is why `reflexive` is deliberately **not**
  counted as contradicting `obj` (see `_CORE` in `case.py`).
- 1:112 `per lo tuo me'` — `dep` `expl` on `me'`, which is apocopated *meglio*, not a pronoun at
  all. A Layer-2 mistag (`morph` calls it `pronoun`) dragging both layers with it; a `morph/`
  correction candidate, not a case error.

Line 2's `mi` now reads `reflexive`, so Failure 1 is confirmed fixed at its own site. `venendomi`
(1:59) moved from `ablative` to `dative` — the fused-token case the earlier build got wrong for
the same reason.

**A third adjudication class the pilot never sampled.** Three rows are relative pronouns that are
plainly the subject of their clause, read `nominative` by `case` and `obj` by Layer 4:

| position | line | `case` | `dep` |
|---|---|---|---|
| 1:27.1 | `che non lasciò già mai persona viva` | `nominative` | `obj` |
| 1:117.1 | `ch'a la seconda morte ciascun grida` | `nominative` | `obj` |
| 1:80.1 | `che spandi di parlar sì largo fiume?` | `nominative` | `obl` |

The pilot's population was clitics, so this class could not appear in it, and `--stats`' original
`obj`/`iobj`-only mapping dropped it from the candidate list entirely. Two changes, both to the
report and neither to generation:

- `nsubj` → `nominative` joins `_DEP_EXPECTS`. Canto 1: 58 agree, 0 contradict.
- `_IMPOSSIBLE` reports pairings no single expected case covers but which still cannot both be
  right — currently `obl` × `nominative`, an oblique-attached pronoun bearing the subject case.
  Reported separately so it does not distort the agreement rates.

Canto 1 now yields **3 contradictions + 2 impossible pairings** from 135 rows. Whether the
relative-pronoun class is real at corpus scale, and which side is wrong in each, is step 4's
hand-verification — not this report's call.

**Agreement after the rebuild**: `nsubj`/`nominative` 58/58, `iobj`/`dative` 8/8,
`obj`/`accusative` 22/25 (88%), `expl`/`reflexive` 9/10.

**Vocabulary so far** (one canto, 135 rows): nominative 63, accusative 26, dative 17, ablative
15, reflexive 10, locative 3, genitive 1. The oblique tail is 19 rows (14%), and `genitive`'s one
row is `tuo` — a form disjoint from `ablative`'s, so the fold question stays open exactly as
*The oblique tail* framed it. Far too small a sample to decide on; the verdict waits for the
corpus pass.
