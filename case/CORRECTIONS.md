# case — measurement history

Every measurement this annex makes is recorded here, including the ones that kill it. See
the plan for what the annex is and why the pilot is a kill gate rather than a
formality.

## Pilot (step 1) — setup, 2026-07-29

### State check

Re-confirmed before rebuilding anything, per the plan's *Confirm the state first*.
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
the plan predicted:

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
([`README.md`](README.md), *Independence*).

The answer vocabulary is **not** constrained by the prompt: the model is asked for one English
word, and whatever it produces is the census that step 2 would freeze — measure-then-freeze, the
same order every other layer used.

### Harness

`population.py` (bucket extraction; run from `skel/`, writes `population.json`), `pilot.py`
(one run per variant, resumable, appends `results.<RUN>.jsonl`), `report.py` (aggregation).

the plan called for these to be uncommitted throwaways in the session scratchpad.
They live here instead, on the branch `case-pilot`: the run is a multi-hour job the user
drives, so a session-scoped scratchpad is the wrong place for it, and a harness in the repo
makes the measurement reproducible rather than merely reported. The branch is the revert path
if the pilot kills the annex — `case/` then disappears with it, exactly as *Revertibility* in
the plan requires.

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

**How the stop rule was read.** As literally worded in the plan — disputed
agreement must be *clearly higher* than control agreement — the gate is unpassable by
construction: the control is the ceiling, being the positions two independent reads already
agree on. The intent, and what the control was built to supply, is a **yardstick for noise**:
the question is whether the disputed positions are answered stably at all, or whether the model
waffles on exactly the cases the column would be built for. The wording has been corrected in
the plan; the substantive bar was not moved after seeing the numbers, and the
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
and consistent with the plan's stated expected value of ≈90–100 soft violations.

**These 61 are not usable as corrections.** They were produced by asking about the disputed
positions, which is exactly the manufacturing failure mode [`README.md`](README.md)'s *Independence*
section forbids. They are evidence that the instrument discriminates, nothing more; the
corrections must come from the blind corpus pass of step 3, frozen before it is joined to `dep`.

**Answer vocabulary census** (570 answers, no unmapped values): accusative 276, dative 252,
ablative 28, nominative 7, genitive 5, locative 2. The model's own word for the partitive /
locative class is **`ablative`**, not the `oblique` the plan anticipated, and it
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
consequences worth stating, because both overrule the plan's guess:

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
the plan's step-3 sizing (300–500 calls) assumed. It was **not** chosen, for three
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
condition the plan states up front. The example now reads `reflexive`.

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
([`README.md`](README.md), *Independence*). It had to be settled before the corpus pass, not after.

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

## Step 3 corpus pass — first run, 2026-07-31

The user's corpus pass ran to completion. `make -C case check` reported **1236 hard
violations**, all of one kind — `missing lines`, an in-scope position with no row — across
**23 of the 100 cantos**.

### The violations are one driver bug, not a model failure

None of them are structural. Every in-scope position was confirmed satisfiable with no model
call: over all 100 cantos, Layer 2's row count matches Layer 1's alpha-token count on every
line, and every target's `word` is the verbatim token at its index (0 mismatches). So no chunk
was failing because it could not be aligned.

The pattern gives the cause away. In each affected canto the missing lines are a **contiguous
tail from one point onward** — *Inferno* 8 misses 82-130, *Inferno* 10 misses 1-136 (the whole
canto), *Paradiso* 28 misses only line 138 — and each of those points is exactly a chunk
boundary. `_build_canto` treated a chunk the model could not get past as fatal: after the
retries and the unit-by-unit fallback it flushed and `return False`, **abandoning every
remaining chunk of that canto**. One bad chunk therefore cost every chunk after it.

Measured amplification: **192 of the 1340 chunks (14%) are still pending, from roughly 23
genuine failures** — about eight chunks of collateral for every one the model actually missed.
Resuming would have converged eventually, but at one genuine failure per canto per run.

### Fix — skip the chunk, not the canto

A chunk that exhausts its retries is now **skipped**: its lines are left empty, `--check`
reports them, and the next run re-requests exactly those. Lines already committed by
successful units of the same chunk are kept (the pop-then-update window narrowed from the
whole chunk to the positions actually covered). `_build_canto` still returns False so `build`
can print a closing `Incomplete (n): ...` list. With skipping in place `--log` is the only record
of *why* a chunk failed, so a re-run should pass it — the first pass kept none.

This is the driver's own bug and the same abort-on-failure shape exists in `skel/skel.py`; it
was never as costly there because that layer's chunks fail far more rarely. Left alone.

### State

The re-run is the user's (LLM-scale generation, the convention Phase 5 settled): 192 chunks,
about 14% of the original pass. The artifact stays **untracked** until `--check` is 0 hard —
step 3's commit order is unchanged.

## Step 3 corpus pass — second run, 2026-07-31

With the skip fix in place the re-run took `--check` from **1236 hard to 70**, over 19 cantos.
The `--log` the first pass lacked was collected for *Inferno*, and it made the residue legible:
the failures are **not** the model's, and both have a determinate cause.

### The dominant failure — Layer 2's `pos` undercounting its own `lemma`

`sen` accounts for most of it. On `Ora sen va per un secreto calle` the model answered
`reflexive+ablative` on all three attempts, and on the unit-by-unit retry, and in every canto it
appears in — the correct reading of `se ne`, two clitics. `scope_slots` reads the component count
off `pos` alone, Layer 2 tagged that token `pronoun` (one slot), and so a right answer was
rejected forever: three attempts, then the unit retry, then the chunk skipped.

24 tokens were affected (`sen`, `men`, `cen`, `gliel`, `gliene`), and Layer 2 already contradicted
itself on them — the identical `sen` / `si+ne` is `pronoun+pronoun` 15 times elsewhere. **Fixed in
`morph/`, not worked around here**: see [`../morph/CORRECTIONS.md`](../morph/CORRECTIONS.md)'s
*Fused clitic clusters*. Working around it in `case/` was rejected because no rule over `pos` and
`lemma` separates `sen` (`si+ne`, two clitics) from `voialtri` (`voi+altro`, one compound
pronoun) — only a frozen list of word forms does, and *Scope* exists precisely so this layer
holds none. The round also corrected one token in the same family that is not a cluster at all
(*Purgatorio* 20:85 `men` = `meno`, the adverb), which drops the scope to **13112 tokens over
8541 lines**, 13171 case values.

`morph --check` stays 0/0, `dep --check` 0/0, `skel --check` 0 hard / 3551 soft — re-measured, no
other layer's verdict moved.

### The second failure — the model answers with the clitic, not the fused token

Asked for the case of the pronoun in `parlami`, `sodisfammi`, `tacerci`, `vedervi`, the model
sometimes writes the `Word` cell as `mi` / `ci` / `vi` — the part the question is actually about.
`_match` required the whole token, so the row was dropped, the position aligned empty, and the
chunk failed. `_match` now also accepts a `Word` that is the **clitic the fused token ends in**
(two characters or more). This is safe rather than lax because alignment is a forward walk: a row
consumed by the wrong position leaves a later one empty, which `validate_line` reports as a hard
violation instead of absorbing. Unlike the first failure this one is self-recovering — `inferno`
10's lines 4-6 passed on a later attempt — so it inflated the retry count more than the residue.

### State

`make -C case clean` dropped the chunks holding the now-invalid one-case rows (132 lines).
**30 chunks are pending** — 2% of the original 1340, down from 192 after the first pass. The
artifact stays untracked until `--check` is 0 hard.

## Step 3 corpus pass — third run, 2026-07-31

`--check` went **70 → 13 hard**, over three cantos. No log was captured this run (the Makefile
recipe carries no `--log`), but none was needed: the residue was determinate from Layer 2 alone,
and it was the **same defect as the second run in a shape the first correction round did not
cover**.

That round keyed on `pos` naming fewer pronouns than a two-part `lemma`. It therefore missed
every token where the lemma undercounts as well — *Paradiso* 11:5 `sen giva` and 11:85 `Indi sen
va` carry the lemma `si`, not `si+ne`, so they were never candidates and kept rejecting the
model's correct two-value answer. Two further shapes came with them: *Purgatorio* 19:139
`Vattene` (`andare+ti+ne` under a two-part `pos`) and *Purgatorio* 31:99 `nol`, which is
`non lo` — one pronoun — but was tagged `ne+lo` / `pronoun+pronoun` and so demanded two.

**Fixed by auditing the whole family rather than the symptom**: 14 tokens, each verified against
the terzina, in [`../morph/CORRECTIONS.md`](../morph/CORRECTIONS.md)'s *Fused-token component
counts, round 2*. The remaining `pos`/`lemma` disagreements in the pronoun population are all
single-pronoun tokens whose count is right (`meco`/`teco`/`seco`, `ne`, `voialtri`), so they
block nothing and are parked.

**The audit also closed a Layer-5 violation.** *Paradiso* 17:92 `nol` was tagged
`adverb+article`, putting it outside the pronoun scope entirely — and that same mistag was why
`skel --check` reported `argument (92, 4) for role obj heads no NP/pronoun/predicate`. Correcting
it took Layer 5 from **3551 to 3550 soft** with no change to `skel/`. This is the annex auditing
Layer 2 the way Layer 5 audits Layer 4, and it happened before the `dep` join has been looked at
at all: reading `pos` as a **count** exercises Layer 2 in a way no earlier consumer did.

### State

Scope: **13112 tokens over 8540 lines**, 13176 case values. `make -C case clean` dropped the
chunks holding rows the corrections invalidated (77 lines). **12 chunks are pending**, under 1%
of the original 1340. `morph --check` 0/0, `dep --check` 0/0, `skel --check` 0 hard / 3550 soft.

### Lesson

Three runs, three residues, and **not one of them was the model getting the Italian wrong** — the
first was a driver abort, the second and third were Layer 2 disagreeing with itself about how
many pronouns a fused token holds. The smoke test's lesson (`--check` passing is not evidence the
artifact is right) has a converse worth recording: **`--check` failing is not evidence the model
is wrong.** A formal check compares the answer against the frozen layers, so it fails whenever
*either* side is at fault, and on this layer the frozen side was at fault three times running.
Read the log before re-running.

## Step 3 corpus pass — fourth run and the freeze, 2026-07-31

The last 12 chunks were re-requested and all validated. `--check` is **0 hard**, the dry run
reports nothing pending, and the artifact is **100 files / 13112 rows** — exactly the frozen
scope. `morph --check` 0/0, `dep --check` 0/0, `skel --check` 0 hard / 3550 soft, `pytest` 138
passed.

**The artifact was committed before `--stats` was run** (`0027494`). This is the order
[`README.md`](README.md)'s *Independence* section exists to enforce, and it is the only part of the
annex's design that cannot be recovered after the fact: once the join to `dep` has been read, any
subsequent edit to the column is indistinguishable from manufacturing it to close violations. The
commit is the evidence that it was not.

### The census, over the whole population

| value | count | share |
|---|---|---|
| `nominative` | 5620 | 42.7% |
| `accusative` | 2003 | 15.2% |
| `reflexive` | 1961 | 14.9% |
| `ablative` | 1805 | 13.7% |
| `dative` | 1409 | 10.7% |
| `genitive` | 267 | 2.0% |
| `locative` | 81 | 0.6% |
| `vocative` | 30 | 0.2% |

13176 values over 13112 tokens (the excess is the fused clitic clusters, which carry two).

Two values added rather than measured have now been measured. **`reflexive` was worth adding**:
at 1961 it is the third-largest class, and the smoke test's finding — that the seven-value
vocabulary had no home for the reflexive/impersonal clitic — would have mistagged 15% of the
column had it not been caught in one canto. **`vocative` was not**: 30 tokens, 0.2%. It is
harmless and it is *correct* — direct address is pervasive in the poem but overwhelmingly nominal
(`maestro`, `figliuol`), not pronominal — but it is on the wrong side of the criterion the
oblique tail is judged by, and the honest record is that it was frozen on an argument from the
poem's rhetoric rather than from a count.

The distribution is the scope decision made visible: `nominative` is 43% because step 2 widened
from the clitic subset to every pronoun-POS token, and tonic subject pronouns dominate that
extension. The clitic population the adjudication actually needs is the `accusative`/`dative`/
`reflexive` block, 5373 tokens.

### The oblique tail — and how the first verdict on it was wrong

16.3% of the column. **The first reading of these numbers was wrong in both directions and is
recorded here in full**, because the mistake is more instructive than the answer.

#### The subset argument was wrong

`--stats` originally reported the tail *by word form*, and concluded: every form carrying
`genitive` (`lor`, `cui`, `loro`, `sé`, `colui`, `lui`, `lei`) also carries `ablative`, so
`genitive` is a **meaning** split of `ablative` rather than a distinct slot, and folds into it by
a mechanical rewrite. That was recommended as the verdict.

**It does not follow.** The same word form appearing under two values is exactly what a case
column exists to record — `lor` is one form in `lor danno` ("their harm") and in `di lor suona`
("resounds of them"), and if those two are the same value then the column has no purpose. Form
overlap was used as a refutation when it is the phenomenon being measured. The inference also
failed on its own terms: 11 forms / 12 tokens carry `genitive` and **never** `ablative`, and they
are `tuo`, `mia`, `mio`, `tuoi`, `tue`, `suoi` — possessives, the same class as `loro`, differing
only in person and number — plus `ambedue`/`amendue`, `alcuno`, and the Latin `horum`/`quorum`.
So it was not even a subset.

#### What the deprels say

The criterion is *a value earns its place if it changes the slot the pronoun fills, not what the
oblique means* — so the deciding evidence is the `dep` deprel distribution, and `--stats` now
prints it:

| deprel | `ablative` 1805 | `genitive` 267 | `locative` 81 |
|---|---|---|---|
| `obl` | **1481** (82%) | 59 | **45** (56%) |
| `nmod` | 94 | **139** | — |
| `det:poss` | **0** | **50** | — |
| other | 230 | 19 | 36 |

- **`ablative` stands**, uncontroversially: a prepositional oblique governed by a predicate.
- **`genitive` stands.** 189 of its 267 (71%) are **adnominal** — they modify a noun rather than
  filling an argument slot — and `det:poss` is a slot `ablative` occupies **zero** times. The
  terzine confirm it at sight: `da le fatiche loro`, `far lor pro`, `il senso lor`, `a' lor
  piedi`, `le gambe loro`, `i legni lor`. These are possessive determiners, not obliques. Under
  the stated criterion this is the clearest earn in the whole tail, and it was the value the
  first reading proposed deleting.
- **`locative` is genuinely open**, and the first reading acquitted it too cheaply. It was passed
  on the grounds that its forms (`vi`, `v'`, `ci`, `c'`) are absent from `ablative`'s form set —
  which is true (they carry `locative`/`accusative`/`dative`/`reflexive`/`nominative` and never
  `ablative`) but is **the same kind of form argument**, used as an acquittal where the identical
  argument was used against `genitive` as a conviction. By deprel it does *not* separate: it is
  `obl`-dominant exactly as `ablative` is. Whether "place" is a distinct slot or a distinct
  *meaning* of the same slot is unresolved, and it stays open, to be decided at the `morph/`
  merge. 81 rows; nothing depends on it.

#### The tail's actual state

**Fold nothing.** `ablative` and `genitive` are earned; `locative` is open; `vocative` (30) is
frozen-but-unearned — correct and harmless, but argued from the poem's rhetoric rather than from
a count. `reflexive` (1961), the other value added rather than measured, is vindicated at 15% of
the column. `case/*/*.tsv` is untouched: the rewrite was recommended but never executed.

#### The lesson

This annex has now been wrong in the same shape three times, each time on the *frozen* side
rather than the model's: three corpus runs blamed the model when Layer 2 was at fault, and this
round blamed the vocabulary when the analysis was at fault. The common failure is **reaching a
verdict from a summary statistic without looking at what the rows are doing.** The subset line
was printed by `case.py` itself, which made it read like a measurement rather than an inference —
so the fix is not only to the documents but to the report: `--stats` now prints deprels and says
in as many words that word forms do not decide this.

### The join to `dep` — step 4's input

Agreement, on the three deprels the column can be compared against at all:

| `dep` | reads as | agree | contradict | rate |
|---|---|---|---|---|
| `obj` | `accusative` | 1631 | 317 | 84% |
| `iobj` | `dative` | 669 | 46 | 94% |
| `nsubj` | `nominative` | 5076 | 98 | 98% |

**461 contradictions** and **49 impossible pairings** (`obl` × `nominative`). Three things in
those numbers matter for step 4:

1. **The disputed class is exactly where the disagreement is.** `obj` is the weak column at 84%
   while `nsubj` runs at 98% — the annex was built to adjudicate accusative-vs-dative on clitics,
   and that is the one place the two reads come apart. This is the pilot's finding reproduced at
   corpus scale, and it is the annex working as designed rather than a defect.
2. **The third class the pilot could not sample is real.** The 49 impossible pairings are the
   relative-pronoun-as-clause-subject class the Inferno 1 rebuild surfaced (3 in that canto
   alone). At 49 corpus-wide it is small but coherent — `che` / `chi` / `quei` / `colui` read
   `nominative` by `case` and `obl` by Layer 4 — and it is the highest-yield slice of step 4,
   because `obl` × `nominative` is a combination neither layer can be right about together.
3. **461 is a candidate list, not an edit list.** Nothing here is applied mechanically. Step 4
   verifies against the terzina one position at a time, in the style of Phases 5i/5n, and
   `make -C dep check` stays 0/0 throughout. The expected yield remains what
   the plan stated before any of this was measured: **≈90–100 of Layer 5's 3550**,
   not zero.

## Step 4, slice 1 — the 49 impossible pairings, 2026-07-31

All 49 opened against their terzine, one position at a time. The edits are in
[`../dep/CORRECTIONS.md`](../dep/CORRECTIONS.md); what belongs here is the triage, the two
things it measured, and the fact that the slice did not do what this plan predicted.

### State check

| check | before | after |
|---|---|---|
| `uv run pytest -q` | 138 passed | 138 passed |
| `make -C morph check` | 0 hard, 0 soft | 0 hard, 0 soft |
| `make -C dep check` | 0 hard, 0 soft | **0 hard, 0 soft** |
| `make -C skel check` | 0 hard, 3550 soft | **0 hard, 3555 soft** |
| `make -C case check` | 0 hard | 0 hard (artifact untouched) |
| impossible pairings | 49 | **39** |

### The triage — 49 positions, six families

| family | n | verdict |
|---|---|---|
| **A.** simile / comparative standard — *come quei che…*, *più ch'altro*, *che quel di pria* | 21 | no edit; see below |
| **B.** genuine prepositional oblique — *a chi la 'ntende*, *con l'altro*, *'n chi la vede*, *ne l'altro*, *in che… acquista*, *innanzi altro* | 9 | no edit — **`case` is wrong**, a preposition governs the pronoun |
| **C.** relative adverbial of time or cause — *nel tempo che*, *ne l'ora che*, *la cagion che* | 3 | no edit — **`case` is wrong** |
| **D.** single-row Layer-4 errors | 9 | **edited** |
| **E.** two-row Layer-4 errors | 1 (2 rows) | **edited** (purgatorio 5:14–15) |
| **F.** entangled or Layer-2-blocked | 6 | recorded, not acted on |

Family **F**, for whoever picks these up: purgatorio 31:25 (`quai fossi attraversati` — Layer 2
tags `fossi` `verb`), purgatorio 23:126 (`torti` tagged `noun`; an edit was made here and
**reverted** — see [`../dep/CORRECTIONS.md`](../dep/CORRECTIONS.md)), inferno 10:136 (the
causative reading of *facea spiacer suo lezzo*), purgatorio 7:107 (the proleptic `ccomp` of
*L'altro vedete c'ha fatto*), purgatorio 24:13 (a loose connective relative), paradiso 23:68 (the
head choice in *non è pareggio … quel che*). The first two are `morph/` questions; the rest are
three-or-more-row re-parses that no single position justifies.

One position outside the 49 was verified in passing and is a real Layer-4 error: **purgatorio
28:51**, *nel tempo che perdette / la madre lei* — `madre`:`obj` and `lei`:`nsubj` are swapped
(Ceres lost Proserpina, not the reverse). It belongs to the contradictions list, so it is left
for slice 2 rather than folded in here.

### `case` on the comparative standard — instability, not bias

Family A is a third of the slice, so it was measured rather than characterized. Population:
pronoun-POS tokens that Layer 4 attaches `obl` and that carry a `come`/`com'`/`che`/`ch'`/`quanto`
child tagged `case` or `mark` — the standard-of-comparison frame, **26 corpus-wide**.

`case` answers **`nominative` 17, `ablative` 5, `accusative` 3, `dative` 1**, and the split has no
principle behind it:

```
inferno    5:126  dirò come colui che piange e dice.       -> ablative
paradiso  22:25   Io stava come quei che 'n sé repreme     -> nominative
purgatorio 22:67  Facesti come quei che va di notte,       -> ablative
paradiso  23:49   Io era come quei che si risente          -> nominative
```

**This is not a systematic error, and calling it one was the first reading of this slice.** It is
the model answering unstably on one construction — the pilot's measured **81%** self-agreement
showing up at corpus scale, on a frame the clitic-only pilot could not sample. Family A therefore
indicts neither layer: Layer 4's `obl` is the UD convention for a comparative standard, and the
model itself gives a non-nominative answer 35% of the time in the same frame.

The unambiguous `case`-side errors are families B and C: **12 positions of 13176 values, 0.09%.**

### The column was not unfrozen, and should not be

Asked directly whether a measured weakness justifies lifting the freeze, the answer is no, on
three grounds:

1. **It would destroy the only thing the annex has.** Rewriting `nominative` after seeing `dep`
   is an edit toward `dep`, and README.md's *Independence* section forbids exactly that — an edit
   made now is indistinguishable from one made to close a violation. Both this file and root
   [`../PLAN.md`](../PLAN.md) record that the order *generate blind → freeze → join* "is the only
   part of it that cannot be recovered after the fact".
2. **Step 4 already decided it**: *if a position looks like a `case` error, the answer is to
   record it, not to rewrite the column.*
3. **49 positions is not a basis for rewriting a 13176-value column** — the frame in question is
   26 rows and `nominative` is 5620. Deciding a column-wide rewrite from this sample would be the
   fifth instance of this annex's one recurring failure.

The legitimate route is the `morph/` merge: **regenerate the whole column blind under a revised
prompt**, which is a fresh independent read rather than a patch. What this round contributes to
that revision is concrete — the prompt has no rule for the standard of comparison, and it should
be told to give the case of the pronoun in its own clause.

`case.py`'s `_IMPOSSIBLE` rule was **left alone** for the same reason. Excluding family A would
shrink the reported number without changing a single edit — the 21 rows produced none, and so did
the 12 in B and C. Narrowing a checker after the fact to reduce a count it just produced is the
move this file exists to catch.

### The slice did not do what this plan predicted

*The join to `dep` — step 4's input* above called the 49 "the highest-yield slice of step 4,
because `obl` × `nominative` is a combination neither layer can be right about together."
**Measured: 49 candidates, 10 edited positions (20%), and Layer 5 rose 3550 → 3555.**

The pairing being contradictory says nothing about yield. What predicts yield is *which two of
the three reads already agree*, and the impossible pairings are precisely the population where
`dep` and `skel` agree and only `case` dissents — so correcting `dep` there breaks an agreement
and raises the count. The **≈90–100** estimate was always drawn from the opposite configuration,
the Phase 5h/5i population where `skel` **already dissents from** `dep` and a third read breaks a
2-1 tie. Full reasoning in [`../skel/CORRECTIONS.md`](../skel/CORRECTIONS.md)'s entry of this
date; the consequence for slices 2 and 3 is in the plan's *Step 4*.

## Step 4, slice 2 — the `skel`-flagged contradictions, 2026-07-31

The first round run under the selector slice 1 corrected. **102 candidates, 81 positions edited
(79%), 92 rows in `dep/`, and Layer 5 fell 3555 → 3469 (−86).** Rows and readings are in
[`../dep/CORRECTIONS.md`](../dep/CORRECTIONS.md); the delta analysis is in
[`../skel/CORRECTIONS.md`](../skel/CORRECTIONS.md). `dep --check` stayed 0/0 throughout and the
`case/` artifact was not touched.

### Building the intersection

The measurement slice 2 needed did not exist, and it is two joins:

1. `case.py --stats --full` gives the 462 contradictions as `<canticle> <canto>:<line>.<token>`.
2. `skel.py --check`'s stderr gives every soft violation with the argument positions it cites, in
   `(line, token)` form — so the violation list can be keyed by position without a monkeypatch.
   The detail formats carry the direction: `role_mismatch: L.T arg (l, t) 'GIVEN' vs 'DERIVED'`
   with **given = the LLM** and **derived = `dep`**, `extra_arg: L.T GIVEN (l, t)`,
   `missing_arg: L.T DERIVED (l, t)`.

| tier | positions | what it is |
|---|---|---|
| A — `skel`'s *given* role sides with `case` | **102** | the 2-1 tie; the ≈90–100 estimate's actual population |
| B — `skel` flags, asserting something else | 15 | a third reading, no tie to break |
| C — `skel` flags `missing_arg`/membership only | 21 | the LLM asserted no role here |
| — no `skel` flag at all | 324 | the slice-1 configuration; correct these too, expect no fall |

**Tier A is 22% of the contradiction list and produced 100% of the fall.** That ratio is the
practical form of slice 1's finding: the annex's value in Layer 5's count lives entirely in the
intersection, and its value *outside* the intersection is a more correct `dep`, which is real but
does not show up in this number.

### The census the round produced

`--stats` after the round, against the pre-round figures:

| `dep` | reads as | agree | contradict | rate | was |
|---|---|---|---|---|---|
| `obj` | `accusative` | 1660 | 267 | **86%** | 84% |
| `iobj` | `dative` | 708 | 38 | **95%** | 93% |
| `nsubj` | `nominative` | 5095 | 77 | **99%** | 98% |

462 contradictions → **382**. The impossible pairings stay at 39, as they must: slice 1 closed
that list and nothing this round touched an `obl` × `nominative` position.

### The column was wrong eleven times, and that is the useful number

Slice 1 measured 12 `case`-side errors in 49; slice 2 measured **11 in 102**. Both are worth
recording because the annex's whole claim is to be a *third* read, not a better one — a column
that never dissents wrongly would be suspect, and a column whose dissents are always right would
not need hand verification. The eleven split into two shapes:

- **A genuine accusative read as dative** — inferno 17:77.6 *m'avea 'mmonito*, which is the
  worked example [`README.md`](README.md) uses to *teach* the accusative; inferno 19:44.5, 26:110.5,
  30:126.8; purgatorio 13:108.5; paradiso 15:96.2 (a real dative, read accusative — the mirror
  slip).
- **The relative and the postposed subject inverted** — paradiso 19:59.3, 21:12.3, 23:92.2;
  purgatorio 7:99.1; inferno 31:116.1. In each the model made the relative pronoun nominative
  where the line puts its subject after the verb. This is the same weakness the standard of
  comparison showed in slice 1: **`case` reads a pronoun's case well and word order poorly**, and
  that is a coherent, prompt-fixable finding for the `morph/` merge rather than a scatter of
  one-offs.

A third shape is not an error at all: **the accusative-and-infinitive** (inferno 22:32.1 *uno
aspettar*, paradiso 30:57.1 *me sormontar*), where `case` reads `accusative` and is
morphologically correct, while `dep` writes `nsubj` because the corpus writes the notional subject
of a perception verb's infinitive `nsubj` 141 times against `obj` 100. Two vocabularies, both
right. It is the clearest illustration in either slice of why the contradiction list is an
adjudication input and never an edit list.

### Layer-2 items this slice surfaced

Neither blocked an edit, unlike slice 1's two:

- **inferno 8:4.5** `i` (for *ivi*, "there") is tagged `pronoun`, which is what put it in the case
  scope at all. `dep`'s `nsubj` on it is impossible (*vedemmo* is 1pl with a pro-drop subject),
  but `che` already holds the `obj` slot, so there is no clean Layer-4 target while Layer 2 calls
  it a pronoun. A `morph/` item.
- **purgatorio 31:90.1** *salsi* carries the lemma `salutare`; the line needs *sapere* (*sallosi*).

### Slice 1's deferred position is still deferred

**Purgatorio 28:51**, *nel tempo che perdette / la madre lei* — the `madre`/`lei` swap slice 1
verified and left. It is **not** in tier A (`skel` does not flag it), so it was not taken here
either; it belongs with the 324 and is called out again so slice 3 does not re-derive it.

## Step 4, slice 3 — the contradictions `skel` does not flag, 2026-08-01

The round's honest completion, and the one whose result was known in advance: **325 candidates,
124 positions edited (38%), 167 rows in `dep/`, and Layer 5 rose 3469 → 3634 (+165).** The
`case/` artifact was not touched. `dep --check` stayed 0/0, `morph --check` 0/0, `pytest` 138.

the plan offered two defensible outcomes here — run it, or stop after slice 2 and
record the 325 as deliberately unspent. **Slice 3 was run**, because the deliverable is a more
correct Layer 4 and because leaving a measured population with no verdict is the one shape
[`../skel/PLAN.md`](../skel/PLAN.md)'s Phase 5 avoided for every route it opened. The count
movement is reported as expected, not as regression; the analysis is in
[`../skel/CORRECTIONS.md`](../skel/CORRECTIONS.md).

### Rebuilding the partition

The two-join recipe from *Step 4, slice 2* reproduces it exactly. After slice 2 the list stood at
**382 contradictions**, of which **57** fall on a position `skel --check` cites and **325** do
not. (The plan's figure was 324; the extra one is *paradiso* 9:110.1 `ten`, a fused token whose
`case` value is `accusative+ablative` and which the slice-2 parser's regex dropped.)

### The four shapes, and how each paid

| family | `dep` vs `case` | n | edited | yield |
|---|---|---|---|---|
| A | `obj` vs `nominative` | 142 | 50 | 35% |
| B | `obj` vs `dative` | 88 | 41 | 47% |
| C | `iobj` vs `accusative` | 35 | 10 | 29% |
| D/E | `nsubj` vs `accusative`/`dative` | 60 | 23 | 38% |

Family B — the accusative-vs-dative clitic class the annex was built to adjudicate — is the
highest-yielding even out here, which is the annex's own case restated: it is the question the
existing layers structurally cannot answer, so it is where `dep` is least reliable. Family A is
the largest and the one where `case`'s measured weakness bites hardest.

### The column was wrong 171 times, and that is the slice's most useful number

Slice 1 measured 12 `case`-side errors in 49 (24%); slice 2, **11 in 102 (11%)**; slice 3,
**171 in 325 (53%)**. Read together these are one measurement of the selector: *inside* the
population where Layer 5 already dissents from `dep`, the `case` column is right roughly nine
times in ten; *outside* it, where `dep` and `skel` agree, it is a coin flip. That is exactly what
a genuine third read should look like — it is not a better read, it is an independent one, and
its dissent is informative only in proportion to how much of the rest of the corpus already
doubts the position.

The 171 fall into the two shapes the earlier slices named, now with a corpus-scale count behind
them:

- **Word order — the postposed subject, 78 instances (all of family A).** `case` makes a relative
  pronoun `nominative` whenever its clause puts a noun after the verb, without deciding whether
  that noun is the subject or the patient. It is right 50 times and wrong 78. Slice 2 saw five of
  these; slice 3 shows it is the column's dominant failure mode. Examples where `dep` is right and
  `case` is not: *l'angoscia che tu hai*, *le fredde membra che la notte aggrava*, *la turba che
  Tagliamento e Adice richiude*, *l'alta letizia che 'l tuo parlar m'infonde*.
- **The dative of possession alongside an explicit object, 24 instances (all of family C).** A
  new shape, and a clean one: where the verb already carries a direct object, `case` reads the
  clitic as `accusative` when Italian requires the dative — *li percosse **l'epa** croia*, *mi
  batté **l'ali** per la fronte*, *li metti **li unghioni** a dosso*, *mi sentiva **la possa** de
  le gambe*, *t'ascondeva **la giustizia** viva*. Every one of the 24 has the object sitting in
  the same line.

A third of the remainder is the pronoun in a plainly nominative slot read as accusative — *ed el
gridò*, *tal parve quelli*, *crescerann' ei* — which is the same word-order weakness seen from
the other side.

**Both are prompt-fixable and neither was patched.** The fix belongs to a blind regeneration at
the `morph/` merge, never to an edit of the frozen artifact. Across all three slices the annex has
now recorded **194 `case`-side errors and rewritten none.**

### Five positions no vocabulary can adjudicate

`case` annotates a *pronoun*; `dep` annotates a *token*. Where a fused token's pronoun component
has a different role from the token as a whole, the two columns are answering different
questions and the contradiction is an artifact: inferno 2:81.7 *aprirmi*, 23:128.7 *dirci*;
purgatorio 8:45.4 *vedervi*, 14:20.1 *dirvi*; paradiso 29:92.1 *seminarla*. In each the whole
token is the subject of an impersonal predicate while its clitic is a dative or accusative. Worth
recording for the `morph/` merge, where the two would finally have to share a row.

Two more are Latin: purgatorio 8:13.1 *'Te lucis ante'* (a hymn incipit quoted as a title, so the
citation is the subject) and paradiso 32:12.5 *'Miserere **mei**'* — a Latin genitive governed by
*misereri*, which the eight-value vocabulary has no home for and which `case` read `dative`.

### Conventions that decided a position against both layers

Measured before any target deprel was chosen, per the plan's standing trap:

| convention | measurement | effect |
|---|---|---|
| predicative pronoun under a copula | `attr` 48 / `obj` 20 | 11 rows to `attr`, siding with neither case claim |
| causative `fare`, bare infinitive | `obj` 38 / `iobj` 3 | **stopped** 3 edits (inferno 9:26.3, purgatorio 21:116.3, paradiso 20:101.1) |
| causative `fare`, infinitive with its own object | `iobj` 7 / `obj` residue | made 6 edits, and set paradiso 33:96.3 to `iobj` rather than `obj` |
| notional subject of a perception verb's infinitive | `nsubj` 141 / `obj` 100 | stopped 4 edits |
| `credere` + person | `obj` 4 / `iobj` 0 | stopped 1 edit (purgatorio 16:113.3), and names a 4-position family for its own round |
| `gravare` | pushed-down patient `obj`, burdened experiencer `iobj` | made 1 edit and stopped 1 — the same lemma, two constructions |
| fused `sen`/`ten` under a *-sene* verb | `expl` 20 / `obl` 14 / `obj` 6 / `iobj` 0 | 1 row to `expl` |

The `gravare` pair is the sharpest illustration: *ché più **mi** graverà* (inferno 26:12) took
`iobj` and *Non **ti** dovea gravar le penne in giuso* (purgatorio 31:58) was left at `obj`,
because the corpus writes the patient pushed downward `obj` at inferno 6:86 *diverse colpe giù
**li** grava al fondo*. The reading alone would have taken both.

### Layer-2 items this slice surfaced

- **purgatorio 20:83.2** `c'` — the conjunction of *poscia che*, tagged `pronoun`, which is what
  put it in the case scope. Its `dep` row wants `mark`; the retag is blocked until Layer 2 moves.
  This is the slice's one blocked edit.
- **purgatorio 11:137.2** `e'` (= *ei*, "he") carries a `dep` deprel of `aux`, which suggests
  Layer 2 read it as a form of *essere*.

Both join the `morph/` round already holding slice 1's `fossi`/`torti` and slice 2's inferno
8:4.5 `i` and purgatorio 31:90.1 *salsi*.

### The census after the round

| `dep` | reads as | agree | contradict | rate | before slice 3 |
|---|---|---|---|---|---|
| `obj` | `accusative` | 1685 | 178 | **90%** | 1660 / 267, 86% |
| `iobj` | `dative` | 755 | 28 | **96%** | 708 / 38, 95% |
| `nsubj` | `nominative` | 5130 | 54 | **99%** | 5095 / 77, 99% |

**382 contradictions → 260; impossible pairings 39 → 40.** The extra impossible pairing is
purgatorio 17:45.4, where the standard of comparison went `obj` → `obl` and thereby joined the
`obl` × `nominative` list slice 1 measured and settled. It is the round's one deliberate increase
and it is recorded so a later reader does not take the list as having grown on its own.

### Step 4 is complete

All 510 candidates from the original join — 49 impossible pairings, 102 tier-A contradictions, 36
tier-B/C, 325 unflagged — have a verdict. **215 positions edited across three slices, 270 rows in
`dep/`** (slice 1: 10/11, slice 2: 81/92, slice 3: 124/167). What remains in the contradiction
list is 260 positions, and the annex's own reading of them is that they are dominated by the
`case` column's word-order weakness rather than by Layer-4 defects: in the two slices that
sampled this configuration `case` was the wrong read 24% and 53% of the time against 11% inside
the `skel`-flagged intersection. Re-opening them is not the next instrument; a blind regeneration
of `case` under a corrected prompt, at the `morph/` merge, is.

## Step 5 — the `locative` question, 2026-08-02

The last of the three parked questions, and the one the tail analysis left open on purpose:
**is `locative` (81) a distinct slot, or a distinct meaning of `ablative` (1805)?** The verdict
is **`locative` is earned and stays** — but the round reached the opposite verdict first, on a
containment test and a minimal pair that turned out to be an artifact, and the reversal is the
useful part. Both are recorded below in the order they happened.

### How it was measured, and against which tree

Measured on 2026-08-02 **while a user-run `make -C case clean && make -C case` regeneration was in
flight** — the 25 hard the step-5 `morph/` round left. A working-tree census would have
undercounted, so every figure below is read from `git show HEAD:case/<canticle>/NN.tsv`, i.e. the
frozen artifact at `0027494`, joined to the working tree's `dep/` and `morph/`. The census
reproduces exactly: **13176 values over 13112 tokens, `ablative` 1805, `genitive` 267,
`locative` 81**. Nothing here needs re-measuring after the regeneration; what the regeneration
moves is the *scope* (13112 → 13125 tokens), which can shift these counts by a few rows and
cannot change a containment result of this shape. Scripts were throwaway, as every round's are.

**No artifact was touched.** As with the rest of the tail: no rows were rewritten.

### The criterion, and the trap it has to avoid

The criterion is the one the `instrumental` rejection established: *a value earns its place when
it changes the **slot** the pronoun fills, not what the oblique **means***. The trap is recorded
above in *The subset argument was wrong* — that round argued from **word forms** (every form
carrying `genitive` also carries `ablative`, so fold it) and was wrong, because form overlap is
the phenomenon a case column exists to record. `locative` was **acquitted by the mirror image of
that same bad argument**: its forms (`vi`, `v'`, `ci`, `c'`) never carry `ablative`. Both the
conviction and the acquittal were form arguments. This round uses deprels and rows only.

### First measurement, and why it does not decide

The tail table already showed `locative` is `obl`-dominant exactly as `ablative` is. One column
does separate them sharply — whether the pronoun governs an adposition (a `case` child in `dep`):

| | `ablative` 1805 | `genitive` 267 | `locative` 81 |
|---|---|---|---|
| has a `case` child | **74%** | 58% | **2%** |

That looks decisive and is not. It is a **clitic-vs-tonic confound**: `ablative`'s mass is tonic
(`me` 183, `sé` 120, `lui` 115, `noi` 110, `te` 88) and a tonic oblique needs a preposition to
appear at all, while `locative` is 79/81 the bare clitic `ci`/`vi`. The comparison has to be made
against `ablative`'s **own bare clitic**, which is `ne` — Italian's other adverbial clitic, and
the corpus tags it `ablative` 283 times.

### The controlled comparison — the profiles converge

| deprel | `ablative` +adp (1328) | `ablative` bare `ne` (283) | `locative` (81) |
|---|---|---|---|
| `obl` | 90.1% | 51.9% | **55.6%** |
| `obj` | 1.8% | 18.4% | 6.2% |
| `expl` | 0% | 8.1% | **9.9%** |
| `iobj` | 0.4% | 2.1% | 8.6% |
| `advmod` | 0.1% | 1.8% | 8.6% |
| `root` | 0% | 2.8% | 6.2% |
| `nmod` | 6.6% | 0.7% | **0%** |

Split `ablative` on the confound and the adposition gap disappears (bare `ne` is 0%, as
`locative` is 2%), and `locative`'s profile lands on the bare-`ne` column, not the `+adp` one —
`obl`-led with a real `expl` tail, which is what a clitic filling an oblique slot looks like.

### The containment test — the same test `genitive` passed

The question `genitive` was acquitted by was: **is there a slot this value fills that `ablative`
fills zero times?** For `genitive` the answer was `det:poss` — 50 rows, 18.7% of it, and
`ablative` fills it 0 times out of 1805. That is why `genitive` stands.

Run the identical test on `locative`:

```
locative deprels:              advmod, conj, expl, iobj, mark, obj, obl, root, xcomp
in locative but NOT ablative:  (none)
in genitive  but NOT ablative:  attr
```

**Every one of `locative`'s nine slots is a slot `ablative` also fills** — `expl` 26, `advmod` 7,
`iobj` 12, `obj` 91, `root` 8, `conj` 21, `xcomp` 10, `mark` 8, `obl` 1481. The containment is
total, and it is not a small-sample artifact: `locative`'s three most *distinctive* deprels by
share (`expl` 9.9%, `advmod` 8.6%, `iobj` 8.6%) are all ones bare `ne` occupies too. There is no
`det:poss` here. `locative` opens no slot.


### The first verdict was *fold*, and it was wrong

**That is where this round's first analysis stopped, and it recommended folding `locative` into
`ablative`.** The user's objection is what broke it: *for a form like `vi`, whether it is locative
changes the reading of the token itself.* It does, and the containment test above cannot see it.

Two things were wrong.

**1. The "minimal pair" was an artifact of collapsing a fused cell.** The claim was that *Ora
**cen** porta l'un de' duri margini* (inf 15:1) is `ablative` while ***cen** porta la virtù di
quella corda* (par 1:125) is `locative` — same form, same verb, same deprel — so the boundary
could not be structural. The raw cells say otherwise:

```
inf 15:1     cen    accusative+ablative
par  1:125   cen    locative+ablative
```

`cen` is `ci`+`ne`, and the measuring script kept a token if *any* component was locative. **The
`ne` component is `ablative` in both.** The component that differs is `ci`, and it differs because
the reading of `ci` differs — "carries **us**" against "carries [us] **there**". The row was
evidence *for* the value, printed as evidence against it. Re-run over single-value cells only, 26
triples survive covering 36 of the 81 rows, and **not one of them is the same word form**: they
are `locative` on `ci`/`vi` beside `ablative` on `ne`/`me`/`lui`. They show the two values share
syntactic slots, which the containment test had already said.

**2. Containment was the wrong test for this value.** The criterion — *a value earns its place
when it changes the slot the pronoun fills, not what the oblique means* — was written to reject
`instrumental`, where the two labels name **one reading of one token**. `locative` is not that
shape. Cross-tabulate the bare `ci`/`vi` tokens in scope against Layer 2's `lemma`:

| | `vi`/`v'`/`ve` (101) | `ci`/`c'`/`ce` (129) |
|---|---|---|
| `locative` | 46 — lemma `vi` 44, **`voi` 2** | 22 — lemma `ci` 21, `che` 1 |
| `accusative` | 26 — lemma `vi` 21, `voi` 5 | 33 — lemma `ci` 29, `che` 4 |
| `dative` | 25 — lemma `vi` 15, `voi` 10 | 24 — lemma `ci` 24 |
| `reflexive` | 4 — lemma `vi` 4 | 15 — lemma `ci` 15 |
| `nominative` | — | 35 — lemma `che` 30, `ci` 5 |
| `ablative` | **0** | **0** |

**Layer 2's lemma does not carry the distinction.** The lemma `vi` spans `locative` 44,
`accusative` 21, `dative` 15 and `reflexive` 4; the lemma `ci` spans `locative` 21, `accusative`
29, `dative` 24, `reflexive` 15, `nominative` 5. Lemmatization returns the form, not the reading.
So the `case` column's `locative` is **the only place in the whole stack** that records whether a
given `vi` means *there* or *to you* — a place or the addressee. That is not "what the oblique
means"; it is which referent class the pronoun belongs to, and it is the same shape of question as
the accusative-vs-dative clitic this entire annex was built to answer.

The sharpest rows are the two where `case` says `locative` and Layer 2's lemma says `voi`:

```
par 22:40   vi   obl   e quel son io che sù vi portai prima
par 32:67   vi   obl   E ciò espresso e chiaro vi si nota
```

Those are the annex working as designed — a third read dissenting from Layer 2 about what the
token *is*. Folding `locative` deletes the dissent along with the value.

**The recoverability argument does not save the fold either.** One could answer that nothing is
lost, because `ci`/`vi` carry `ablative` **zero** times, so an `ablative` on a `ci`/`vi` would
still uniquely mark the place reading. That is a **word-form argument** — precisely the class of
argument *The subset argument was wrong* rules inadmissible for this question. Folding a value and
then invoking form distribution to claim the information survives is the same error twice in one
paragraph.

### Verdict — `locative` is earned, and stays

**Fold nothing.** All three of the tail's values stand, for three different reasons:

| | why it stands |
|---|---|
| `ablative` 1805 | the prepositional oblique; `obl` at 82%, 74% governing an adposition |
| `genitive` 267 | opens a **slot** `ablative` never fills — `det:poss`, 50 rows |
| `locative` 81 | opens no slot, but is the **only** record of which reading a `ci`/`vi` token has; Layer 2's lemma collapses `locative`/`accusative`/`dative`/`reflexive` onto one form |

`vocative` (30) remains frozen-but-unearned, argued from the poem's rhetoric rather than a count —
it is now the only value in that position. `reflexive` (1961) is vindicated. **No rows were
rewritten**, and none should be: the `morph/` merge's blind regeneration keeps all eight values,
and `locative` is not to be dropped from `CASES` or aliased onto `ablative`.

### The lesson — the fourth time, and the same shape

*The subset argument was wrong* recorded this annex reaching a verdict from a summary statistic
without looking at what the rows do. This round did look at rows — and still repeated the error,
because **it looked at the wrong rows**. The comparison was `locative` against `ablative`,
which is the question as posed; the question that decides it is `locative` against **the other
values on its own word forms**, which is where the ambiguity `vi` actually carries lives. A
containment test over deprels can only ever answer "does this value open a slot", and for a value
whose work is disambiguating *one form into several readings*, that is not the question.

The concrete guard, for the next value that comes up for review: before folding value *V*, print
the cross-tab of **V's word forms against every value they carry**, not only V against its
proposed parent. If the forms are shared across several values and no other layer separates them,
V is doing disambiguation work and folding it destroys information, whatever its deprels look
like.

## Step 5 — the chunk regeneration the `morph/` round owed, 2026-08-02

The 25 hard the 2026-08-02 `morph/` round left were closed by a user-run
`make -C case clean && make -C case`. **`--check` is back to 0 hard**, `--stats` runs again, and
this section records the deltas the blocking item owed.

### The five layers, and the tests

| check | before the regeneration | after |
|---|---|---|
| `uv run pytest -q` | 138 passed | **138 passed** |
| `make -C morph check` | 0 hard, 0 soft | **0 hard, 0 soft** |
| `make -C np check` | 5 hard, 96 soft | **5 hard, 96 soft** (the open defect, unmoved) |
| `make -C dep check` | 0 hard, 0 soft | **0 hard, 0 soft** |
| `make -C skel check` | 0 hard, 3633 soft | **0 hard, 3633 soft** |
| `make -C case check` | **25 hard** | **0 hard** |

Nothing moved outside `case/`, which is what a `[count]`-mismatch regeneration should look like:
the 20 lines needed a different *number* of case values, not different readings, so no other
layer's input changed.

### The census, before and after

| value | frozen (`0027494`) | after | Δ |
|---|---|---|---|
| `nominative` | 5620 | 5621 | +1 |
| `accusative` | 2003 | 1999 | −4 |
| `reflexive` | 1961 | 1962 | +1 |
| `ablative` | 1805 | **1819** | **+14** |
| `dative` | 1409 | 1410 | +1 |
| `genitive` | 267 | 267 | — |
| `locative` | 81 | 81 | — |
| `vocative` | 30 | 30 | — |
| **tokens / values** | 13112 / 13176 | **13125 / 13189** | +13 |

The scope moved exactly as predicted. **`ablative` takes almost all of the gain**, and it is the
comitative family: the `morph/` round normalized `meco`/`teco`/`seco`/`nosco`/`vosco` to
`<pronoun>+con` / `pronoun+preposition`, which `--stats` now reports as 58 tokens under that `pos`,
and a comitative is an ablative — the reading `_CASE_ALIASES` already anticipated by mapping
`comitative` onto `ablative`. The new column agrees with the alias table it never saw.

**`genitive` and `locative` did not move at all**, so the tail analysis in the section above —
measured from `git show HEAD:` while this regeneration was in flight — needs no revision. Both
were re-run against the regenerated artifact and reproduce: `locative`'s deprels are still
`obl` 45 / `expl` 8 / `advmod` 7 / `iobj` 7 / `root` 5, and the `ci`/`vi` cross-tab against Layer
2's `lemma` is unchanged but for one `ci` `nominative` row (35 → 34). The verdict stands.

### The join to `dep`

| `dep` | reads as | agree | contradict | rate | at step 4's close |
|---|---|---|---|---|---|
| `obj` | `accusative` | 1683 | 178 | 90% | 1685 / 178, 90% |
| `iobj` | `dative` | 756 | 27 | **97%** | 755 / 28, 96% |
| `nsubj` | `nominative` | 5131 | 53 | 99% | 5130 / 54, 99% |

**258 contradictions, 40 impossible pairings** (from 260 / 40). The two that left the list are
regeneration effects, not new adjudication: the corrected chunks happened to re-answer two
positions in agreement with `dep`. This is the residue step 4 measured, unchanged in substance —
and step 4's verdict on it stands: it is dominated by the `case` column's word-order weakness, and
the next instrument is the merge's blind regeneration under a corrected prompt, not another
Layer-4 slice.

**Every figure in this annex is now measured against a valid artifact again.** Step 5's two
analysis sub-items — the oblique tail and the `locative` question — are closed, and what remains
is the `morph/` merge.

## Step 5 — the corrected build prompt, for the merge's blind regeneration *(2026-08-02)*

**Assistant-side work only: the prompt is rewritten, no artifact was touched, and nothing has
been regenerated yet.** `make -C case check` is still 0 hard over the frozen 13125 tokens /
13189 values, and the 258 contradictions are the same 258. The regeneration itself is LLM-scale
and therefore the user's, by the convention Phase 5 settled.

### What it fixes, and nothing else

The two shapes slice 3 counted, and only those. Both are word order, not case — the column reads
a pronoun's *case* well and the *order of the clause* poorly:

| shape | count | what the column did | the rule now added |
|---|---|---|---|
| the postposed subject | **78** | made a relative pronoun `nominative` whenever its clause put a noun after the verb | a relative pronoun is nominative **only** where its clause has no other subject; a noun postposed after the verb is that subject, and the relative pronoun is then the object. Plus the agreement check: a singular verb cannot take a plural relative as its subject |
| the dative of possession | **24** | read the clitic `accusative` where the verb already carried an explicit object | a verb takes at most one direct object, so a clitic beside an object noun is dative — the ordinary dative of possession or of the person affected |

A third rule was added for the same weakness seen from the other side (*ed el gridò*, *tal parve
quelli* — a pronoun in a plainly nominative slot read `accusative`): a personal pronoun **after**
its verb is still nominative when nothing else is the subject.

A **second worked example** was added to the prompt, because the existing one teaches exactly the
ambiguous shape and teaches only its nominative half — *che nel pensier rinova la paura*, where
`che` is the subject and the postposed noun is the object. The new example is the other half.

### Every illustration is a position the frozen column and `dep` already agree on

This is the part that needed care. The obvious illustrations are the errors themselves — *le
fredde membra che la notte aggrava*, *mi batté l'ali per la fronte* — and quoting those with the
`dep`-side answer would pre-answer a **disputed** position inside the prompt. That is the
manufacturing the blindness rule forbids ([README.md](README.md), *Independence*), one level up: the
regeneration is supposed to be a measurement of whether a general rule moves the shape, and a
prompt that names four of the contradictions makes those four agree trivially.

So the illustrations were selected the other way round — from positions where the frozen `case`
value and `dep`'s deprel **already agree**, found by sweeping the corpus for each shape:

- postposed subject, `case` `accusative` × `dep` `obj`: **51 positions**; used *nel nome che sonò
  la voce sola* (inferno 4:92), *che mena il vento, e che batte la pioggia* (inferno 11:71),
  *l'anime di color cui vinse l'ira* (inferno 7:116).
- postposed subject pronoun, `case` `nominative` × `dep` `nsubj`: **755 positions**; used *Non odi
  tu la pieta del suo pianto* (inferno 2:106), *e poi comincia' io* (inferno 2:75).
- dative of possession, `case` `dative` × `dep` `iobj` with a noun in the same line: **226
  positions**; used *Li occhi mi sciolse* (inferno 9:73), *ch'ella mi fa tremar le vene e i polsi*
  (inferno 1:90), *questa mi porse tanto di gravezza* (inferno 1:52).

The second worked example is inferno 4:91–93, quoted with the frozen column's own six answers
(`ciascun` nominative, `meco` ablative, `si` reflexive, `che` **accusative**, `fannomi` dative,
`ciò` ablative) — one passage that carries the postposed subject, the fused verb+pronoun and the
comitative at once, and every value in it is what the blind pass itself already produced.

**The prompt therefore encodes no answer the column did not already give.** What it adds is the
generalization the column failed to make on its own.

### `make -C case regen`, and why `clean` is the wrong instrument here

`--clean` drops only chunks holding a **violation**, and after a prompt change nothing in the
artifact is invalid — so `make -C case clean && make -C case` would remove nothing and skip
everything, which is not what step 3's rounds needed it for. The new `regen` target drops the
artifacts and then builds normally; `--force` is deliberately not used, because it restarts from
scratch on every resumed run and this job is 1340 chunks. The frozen column is committed, so
`git checkout case/` is the undo.

### What to measure afterwards, and what not to conclude

The question the round answers is **whether the two shapes move**, not whether the contradiction
total falls. Re-run `make -C case stats` against the current baseline — 258 contradictions / 40
impossible pairings, `obj` 90% / `iobj` 97% / `nsubj` 99% — and count the two shapes directly, not
the headline. A regenerated column that fixes 78 postposed subjects and introduces 30 new
disagreements elsewhere is a better column and a worse number, exactly as slice 3 was.

**Nothing licenses editing `dep/` from the new column without the same hand verification.** Step
4's rate stands: outside the population where `skel` already dissents from `dep`, the `case`
column was the wrong read 53% of the time.

## Step 5 — the blind regeneration, measured *(2026-08-02)*

The user ran `make -C case regen` over all 1340 chunks with the corrected `SYSTEM_PROMPT`. The new
column is `0 hard` over the same 13125 tokens / 13189 values, and **791 values changed**. This
section is step 3 of the open item — the re-measurement — and it is a measurement only: no row was
edited by hand, and the merge decision it feeds is still open.

### The headline, which is not the answer

| | frozen | regenerated |
|---|---|---|
| contradictions | 258 | **295** (+37) |
| impossible pairings | 40 | **32** (−8) |
| `dep=obj` (accusative) | 90% | 93% |
| `dep=iobj` (dative) | 97% | 93% |
| `dep=nsubj` (nominative) | 99% | 98% |

### The two shapes, counted directly

The rule was supposed to teach a *discrimination*, so the test is both populations at once — the
one the rule was meant to move and the one it was meant to leave alone.

| population | n | frozen | regenerated |
|---|---|---|---|
| relative pronoun, `dep=obj` (want `accusative`) | 433 | 325 (75%) | **377 (87%)** +52 |
| relative pronoun, `dep=nsubj` (want `nominative`) | 2075 | 2062 (99%) | **1986 (96%)** −76 |
| clitic, `dep=iobj` (want `dative`) | 588 | 549 (93%) | 534 (91%) −15 |
| clitic, `dep=obj` (want `accusative`) | 726 | 447 (62%) | 454 (63%) +7 |

1. **The postposed subject moved, and overshot.** The hard population gained 52 of 433 — the rule
   fires and it fires on the right shape. But the easy population lost 76 of 2075, and 70 of the 85
   newly introduced `accusative × nsubj` contradictions are `che`. The rule did not stay a
   discrimination; on a relative pronoun it shifted the default. Four of the losses were read
   against the text and all four are `case`-side errors, not `dep`-side ones: inferno 3:108
   *ch'attende ciascun uom* (the bank awaits the man), 3:134 *che balenò una luce vermiglia*,
   2:46 *la qual molte fïate l'omo ingombra*, 5:24 *ciò che si vuole*. Every one is the shape the
   rule names — a noun after the verb — with the relative still the subject.
2. **The dative of possession fired, and the net still fell.** On the population the rule names —
   the frozen column's `accusative × dep=iobj`, 27 positions — **19 flipped to `dative`**, including
   every one slice 3 quoted by name (*li percosse l'epa croia*, *mi batté l'ali per la fronte*,
   *t'ascondeva la giustizia viva*). The rule works. But 40 *other* `iobj` clitics went `dative` →
   `accusative`, and those are not ambiguous: *li rispuosi*, *mi 'nsegni*, *se ben vi ricorda*, *li
   fallia la lena*, *mi comandò* — verbs that govern `a`. Nothing in the new rules asks for that
   move.

### The mechanism is one global shift, not two mis-scoped rules

The census says it plainly:

| | frozen | regenerated |
|---|---|---|
| `nominative` | 5621 | 5492 (−129) |
| `accusative` | 1999 | **2155 (+156)** |
| `dative` | 1410 | 1367 (−43) |
| `genitive` | 267 | 242 (−25) |

Both new rules hit their named shapes (relative `obj` +52, dative of possession 19 of 27). What
sank the round is a **prior shifted toward `accusative`** across the whole column, drawn out of
`nominative` and `dative` — and every loss above is that shift, not a rule firing where it should
not. The likely cause is the shape of the addition rather than its content: three rules and a
second worked example that all argue *against* a nominative reading, with the example's most
salient answer being `che` = `accusative`. The prompt now spends most of its word-order text
making the case for one value.

The `−8` on impossible pairings is real and is the round's other gain: `nominative` on a `dep=obl`
pronoun is the one pairing no reading reconciles.

### What this licenses

**The frozen column was restored** (`git checkout -- case/inferno case/purgatorio case/paradiso`);
`case --stats` reads 258 / 40 again, and the regenerated column survives only as this measurement.
Adopting it was not on the table once the mechanism was clear: it buys 52 + 19 correct moves on two
named shapes and pays 76 + 40 for them on populations the rules never mention.

What the round settles is that **both rules are right and the prompt around them is unbalanced**.
That is a repairable fault and it is repaired in the prompt, not in the artifact — see *The
rebalanced build prompt* below.

### The rebalanced build prompt *(2026-08-02)*

The diagnosis above says the two rules are sound and the prompt around them leans. So the revision
changes the *framing* and adds one guard; it does not withdraw either rule.

1. **The relative pronoun now starts in the subject slot and has to be argued out of it.** The
   previous wording — "nominative only when its clause has no other subject" — makes nominative
   the exception and hands the model a trigger (a noun after the verb) that is far commoner than
   the reading it licenses. The corpus settles the direction: a relative pronoun whose clause puts
   an object noun after it is **nominative in 738 positions and accusative in 51** where `case` and
   `dep` agree. The postposed noun is therefore evidence *for* the subject reading, and the rule
   now says so. Moving the relative to the object requires naming the postposed noun as the thing
   the verb agrees with **and** as something that can perform the action.
2. **Agreement is promoted from an afterthought to a decider, in both directions.** It was there
   only as "a singular verb cannot have a plural relative as its subject". Added: a
   second-person verb (*che spandi di parlar sì largo fiume*) fixes the subject as the addressee
   whatever noun follows.
3. **A dative clitic no longer needs a second object to license it.** This is the guard for the 40
   spilled positions. The one-direct-object rule is stated as a sufficient condition for `dative`
   and the column read it as a necessary one, so clitics of verbs governing `a` — with no other
   object anywhere — fell to `accusative`. The rule now names the class: *rispondere, insegnare,
   piacere, parere, nuocere, ricordare, fallire*.
4. **A third worked example**, inferno 3:106–108, carrying two relative pronouns that both keep
   the subject slot with a noun after their verb (*ch'attende ciascun uom che Dio non teme*). The
   two existing examples split 1–1 between the readings but the rule text argued in one direction
   only; this is the counterweight, and it is one line rather than a passage.

**The selection discipline holds, with one dependency named.** Every illustration is a position
where the frozen column and `dep` already agree — the subject-side ones were swept out of the 738,
the dative ones out of `dative × iobj` with no object in the line. What *is* new is that the
lexical class in (3) was noticed because the regenerated column got those positions wrong, which
is a `dep`-derived observation one level up. The class itself is a fact of Italian and not of any
layer, and no disputed position is quoted or pre-answered; the dependency is recorded here rather
than argued away.

**Nothing else moved**: the vocabulary is unchanged, all eight values stay, and no artifact row was
touched. `case --check` is 0 hard over the frozen column and `pytest` is 142 passed. The next
action is again the user's — `make -C case regen`, one shell per canticle, with the same
smoke-test-one-canto-first advice as before; the regenerated column measured here is not in the
tree and does not need to be restored.

## Step 5 — the second regeneration, measured and rejected *(2026-08-02)*

The user ran `make -C case regen` a second time, over all 1340 chunks under the rebalanced
`SYSTEM_PROMPT`. The new column was `0 hard` over the same 13125 tokens / 13189 values. This is
the re-measurement the rebalance owed — round 2 of the two the merge's *Handing off* section
budgeted — and, per the verdict rule fixed in advance, it is also the last one.

### The four populations, against the same frozen baseline

Scratch analysis (not kept, per round 1's own precedent — the recipe is *How round 2 was
measured* above), joining `case` (frozen = `git show HEAD:case/…`, before this round; regenerated
= the round-2 output), `dep`, restricted to positions where the case value carries a
`nominative`/`accusative`/`dative` reading (the same `_CORE` filter `case.py --stats` itself
applies, so a purely `reflexive`/oblique-tagged position is dropped from the count rather than
scored as a miss):

| population | frozen | round 2 |
|---|---|---|
| relative pronoun, `dep=nsubj` (want `nominative`) | 2062/2073 (99%) | **2006/2070 (97%) −56** |
| relative pronoun, `dep=obj` (want `accusative`) | 320/414 (77%) | **366/417 (88%) +46** |
| clitic, `dep=iobj` (want `dative`) | 581/598 (97%) | 585/605 (97%) +4 |
| clitic, `dep=obj` (want `accusative`) | 517/555 (93%) | 523/560 (93%) +6 |

The two easy populations (rows 3–4, the ones round 1 broke) **held** this time — the guard added
in the rebalance (a dative clitic no longer needs a second object to license it) worked, and
round 1's 40-position `dative → accusative` leak on verbs governing `a` did not reappear. The named
target, relative-pronoun `obj`, **rose again**, by almost exactly round 1's margin (+46 against
+52). But the population the rule is framed to protect — relative-pronoun `nsubj`, the "starts in
the subject slot" reading the rebalance was written to restore — **fell again**, by −56 against
round 1's −76. Less than round 1, but the same direction, on the same population, after the
rebalance was specifically aimed at reversing it.

### The census — the drift shrank, it did not stop

| | frozen | round 2 |
|---|---|---|
| `nominative` | 5621 | 5511 (−110) |
| `accusative` | 1999 | 2116 (+117) |
| `dative` | 1410 | 1436 (+26) |
| `genitive` | 267 | 248 (−19) |
| `ablative` | 1819 | 1826 (+7) |
| `locative` | 81 | 76 (−5) |
| `vocative` | 30 | 28 (−2) |
| `reflexive` | 1962 | 1948 (−14) |

Round 1's global shift was `nominative` −129 / `accusative` +156. Round 2's is −110 / +117 — the
rebalance cut the drift by roughly a sixth, but did not close it, and the *shape* of the failure
is identical: value pulled out of `nominative` and into `accusative` across the whole column, not
confined to the two rules' named positions. The verdict rule this session inherited was written
for exactly this outcome: **"adopt only if the two target populations rise and the two others
hold within a few positions of the frozen figures."** Row 3–4 hold. Row 2 (the named target) rose.
Row 1 — the *other* target the rebalance's first change was aimed at (the relative pronoun
"starts in the subject slot") — fell, and a −110/+117 census line is not "nearly still" by the
comparison the rule itself set up against round 1's −129/+156.

### Verdict — reject, and this is the last round

**The rebalanced column was measured and not adopted.** It was held in `git stash` for a day while
the measurement above was written up, then dropped once the verdict was final (2026-08-03) — the
frozen column (`case --stats`: 258 contradictions / 40 impossible pairings) is what `main` and any
future session sees, and this file's numbers are what a third attempt would have to reproduce from
scratch rather than diff against. Per the guardrail against a third round (root
[`../PLAN.md`](../PLAN.md)'s *What must not be done*): **do not tune the prompt a third time.** Two rounds were the stated budget,
for the reason given there — choosing prompt wording by re-scoring against `dep` is exactly the
fitting-to-Layer-4 that would make `case`'s independence worthless, and a third round would be
that regardless of outcome.

**What this settles for the merge**: the frozen column carries two measured weaknesses, unchanged
by two regeneration attempts — the postposed relative-pronoun subject (the rule that fires
correctly on `dep=obj` overshoots onto `dep=nsubj` every time it's tried) and, more diffusely, a
persistent pull of the whole column toward `accusative`. Both are now **recorded, not chased
further**; the merge proceeds from the frozen artifact with the weakness noted.

## Step 5 — the merge decision, 2026-08-02

**Verdict: no physical merge into `morph/*.tsv`. `case/` is promoted from experimental annex to a
permanent Layer-2 sibling extension, on the same footing as `np/`, `dep/` and `skel/` already are
relative to `morph/`.** This is the "merge" the plan's open item names — not a schema change, a
status change.

### What was weighed

[`README.md`](README.md)'s *Why its own directory* gave three reasons for the sibling-directory design, written
before step 3's corpus pass existed:

1. **Hash blast radius.** A column non-empty on ~13% of tokens (13125 of 101601) would move all
   100 `morph/*.tsv` content hashes for a column empty on the other 87%, invalidating every
   downstream consumer's cached parse (`dante-analyze`, `dante-dravidian`) for a gain concentrated
   in a sixth of the rows.
2. **Provenance stays visible.** `morph/*.tsv` is one pass, one model, one moment; `case/` is a
   later pass, over a narrower scope, and — as of this annex's own two rejected regeneration
   rounds — a pass with two *named and measured* weaknesses (the postposed relative-pronoun
   subject; a diffuse `nominative`→`accusative` pull). Folding it into Layer 2's single artifact
   would blend a column with known residue into one that has none, and erase the visibility that
   lets a future reader tell them apart.
3. **Revertibility.** Cheaper to have kept than to need, and nothing accrued against it.

None of the three depends on the column's measured quality, and nothing the annex did — the 90%
/ 96% / 99% agreement with `dep`, the two rejected regeneration rounds, the settled vocabulary —
touches any of them. Reason 2 is, if anything, stronger at the close than at the start: a column
that ends with recorded weaknesses is a *better* argument for keeping its provenance separately
legible, not a worse one.

**The architectural precedent points the same way.** Every layer in this corpus already lives in
its own directory — `np/`, `dep/` and `skel/` are not merged into `morph/` either, despite each
being "conceptually" downstream of it. `case/` living apart from `morph/` is not a compromise
state left over from an experiment; it is the corpus's normal shape. A literal TSV-column merge
would have been the outlier.

### The fused-token mismatch, resolved without a schema change

The plan's open item worried that "a merge into `morph/*.tsv` forces one row per token, and
`case` annotates a pronoun." Under this decision that concern does not arise: `case/*.tsv` is
already one row per **in-scope token**, exactly `morph`'s own convention (`--check`'s `count`
rule), with one case value per pronoun *component* joined by `+` for a fused token — the identical
convention `morph` already uses for a fused token's lemma parts. No schema exists that a merge
would have had to reconcile.

The five contradictions this mismatch produces against `dep` (inferno 2:81.7 `aprirmi`, 23:128.7
`dirci`; purgatorio 8:45.4 `vedervi`, 14:20.1 `dirvi`; paradiso 29:92.1 `seminarla`) are not a
`case`-side error and not a design defect: `dep` assigns one `deprel` to the whole fused token,
while `case` assigns a value per pronoun component within it, so the join compares a token-level
judgment against a component-level one at exactly the positions where a verb and its enclitic
share a token. They are recorded here as **structural residue of the `dep` join**, not scheduled
for any correction round — the same status the two prompt-side weaknesses have.

### The prompt was reverted too, so the code matches the artifact it stands for

The verdict rejects both regeneration rounds, but `case/case.py`'s `SYSTEM_PROMPT` still carried
round 2's rebalanced rules — the corrected-then-rebalanced prompt was never reverted when its
output was rejected, unlike the artifact itself (round 1 was restored with `git checkout`, round 2
held in `git stash` and, once measured, dropped). Left as it stood, this was a live inconsistency: the prompt in the
tree could no longer regenerate the artifact in the tree, and if any future partial regeneration
ever ran again (as happened once already, when the `morph/` scope shift forced a 20-line chunk
regen), it would silently apply round 2's rejected rules to a handful of chunks while the other
1339 stayed on the original prompt — a non-uniform artifact with no record of why. **The prompt
was reverted to the pre-round-1 version** (`git show 2e3cdba:case/case.py`, the state the frozen
column was actually built under), leaving only the Makefile's `regen` target (a generic
drop-and-rebuild utility, not tied to the rejected rules) and this written record as what remains
of the two rounds. `case --check` stays 0 hard and the 138 tests stay unaffected — the prompt has
no effect on either. The round-1 and round-2 rule text is preserved in git history
(`038d1ec`, `ffc8180`) and described above, not in the live file.

### What this closes

The annex's remaining open item — *the case annex's `morph/` merge* — is **closed**. `case/`
stays exactly where it is: a permanent, separately-hashed, separately-provenanced Layer-2
extension, frozen at 100 cantos / 0 hard / 13125 tokens / 13189 values, with 258 contradictions
and 40 impossible pairings against `dep` recorded as measured residue and two named weaknesses
(the postposed relative-pronoun subject; the `nominative`→`accusative` census pull) recorded
rather than chased past their two-round budget. **The build prompt matches the frozen artifact
again**, so the code in the tree and the data in the tree tell the same story. Nothing in
`morph/*.tsv` changes, no hash moves, and no further regeneration is scheduled. See
[`README.md`](README.md)'s *Why its own directory* for the reasoning this decision confirms
rather than revisits, and for the serve-time API this leaves unchanged.

## Step 6 — the clitic accusative/dative residue, hand-corrected (2026-08-03)

**"Frozen" never meant "unfixable."** Step 5 closed the annex's *regeneration* and *merge*
questions, and its 258 contradictions / 40 impossible pairings were recorded as measured residue
rather than chased. That was right for the classes with no single verdict (the postposed
relative-pronoun subject, the free-relative and accusative-and-infinitive populations `dep`'s
[Step 4 slices](#step-4-slice-2--the-skel-flagged-contradictions-2026-07-31) already settled
structurally) — but a position where the Italian's own valency gives one clear answer is a plain
error, and this project's standing rule is to correct those, not to let a "closed" label stand in
for one. [[project_skel_soft_violations_goal]]

**Scope: the 50 bare-clitic contradictions** (`mi ti ci vi si li` + elisions) out of the 258 — the
population [`../skel/PLAN.md`](../skel/PLAN.md) section 1 calls "the clitic-case question" and
Step 4 slice 2's "21 tier-A candidates were left alone" section already named eleven of by hand
(*m'avea 'mmonito*, *mi giunse al rotto*, *mi lasciai Sibilia*, *omor mi rinfarcia*, *che sé ne
presti*, *tu li raccorci* among them) without ever writing the fix into `case/*.tsv` — that round
only ever edited `dep/`, so a position where `dep` was right and `case` was wrong was left
dissenting rather than corrected. This step is that missing half, extended to the full 50.

**Method.** Each terzina was read against the governing verb's actual valency: plain transitives
take an accusative object (*percuotere*, *toccare*, *pregare*, *torcere*, *prendere*, *vincere*,
*affinare*, *rimordere*, *dilettare*, *annoiare*...); the *fare* + accusative-clitic +
predicate-adjective/infinitive causative (*fa sicuro*, *fa manifesto*, *fé mettere*, *fece
ardere*) takes an accusative causee when the embedded predicate is intransitive; the
dative-of-the-affected-person construction (*mi batté l'ali*, *tu li raccorci* [*con l'opere
tue*], *mi fa certo*) takes a dative once a separate accusative argument (a body part, "la lunga
fatica," the predicative complement) is already present; and the causative with a *transitive*
infinitive (*mi fai rimembrar*, where *rimembrare* keeps its own object) takes a dative causee —
the textbook complement to the intransitive-infinitive rule above. Three positions were checked
against the corpus's own convention for that verb rather than judged in isolation (`credere`,
`gravare`, reflexive `vi`), and one (**purgatorio 16:56** *mi fa certo*) was checked by trial:
flipping `dep` to match `case`'s dative reading and re-running `skel --check` **regressed** the
soft count (3634 → 3635), showing the position's *given* `skel` reading sides with `dep`'s
original tag, so `case` was the outlier and was corrected instead of `dep`. The same
trial-and-revert method also tried, and rejected, a `dep` fix for the `gravare`
population (**purgatorio 31:58**, **inferno 6:86**, **purgatorio 18:6**) and for the *mi
lasciai Sibilia* / *m'avea lasciata Setta* pair (**inferno 26:110-111**): each looked like a
plausible reflexive or dative-of-possession reading in isolation, but re-running `skel --check`
after the `dep` edit moved the soft count against it (or, for 26:110, left it unchanged at a
predicate the LLM's own independent reading does not resolve under any tagging), so none of those
`dep` rows were touched — only the one `dep` fix below survived the same test.

**One `dep/` row, confirmed by measurement.** `purgatorio 11:39.6` *che secondo il disio vostro
**vi** lievi* had `vi` tagged `nsubj` — a **hapax**: `vi` carries `nsubj` nowhere else in the
corpus, against 906 instances of `si` tagged `expl` for the identical reflexive *levarsi*
construction with a pro-dropped subject. Retagged `nsubj` → `expl`. `dep --check` stays **0 hard,
0 soft**; `pytest` stays 142; **`skel`: 3635 → 3634, −1** — the one row in this round that both
closes a Layer-5 divergence and is independently justified by the corpus's own convention for the
word.

**49 rows in `case/*.tsv`**, one canto-file each, plus the `vi` position's own value corrected
alongside its `dep` fix (`accusative` → `reflexive`, matching the retag):

| position | word | was | now | why |
|---|---|---|---|---|
| inferno 8:21.3 | ci | dative | accusative | *avere* — plain transitive |
| inferno 8:65.5 | mi | dative | accusative | *percuotere* — plain transitive |
| inferno 8:105.2 | ci | accusative | dative | *tòrre ... a* — deny/deprive someone of something |
| inferno 9:26.3 | mi | dative | accusative | *fare* + intransitive infinitive (*intrar*) |
| inferno 9:30.6 | ti | dative | accusative | *fare* + predicate adjective (*sicuro*) |
| inferno 10:25.4 | ti | dative | accusative | *fare* + predicate adjective (*manifesto*) |
| inferno 14:78.5 | mi | dative | accusative | *raccapricciare* — transitive |
| inferno 19:44.5 | mi | dative | accusative | *giungere qualcuno a un luogo* — transitive |
| inferno 20:14.5 | li | nominative | dative | *convenire* — dative-experiencer verb; `li` cannot be nominative at all |
| inferno 22:40.6 | li | accusative | dative | *mettere ... a dosso a qualcuno* |
| inferno 25:52.5 | li | accusative | dative | *avvincere ... a qualcuno* |
| inferno 26:110.5 | mi | dative | accusative | *lasciare* — the corpus tags every instance `obj` (see Step 4 tier-A) |
| inferno 27:111.1 | ti | dative | accusative | *fare* + intransitive infinitive (*trïunfar*) |
| inferno 29:110.4 | mi | dative | accusative | *fare* + *mettere* (causee = the embedded verb's own object) |
| inferno 29:116.6 | mi | dative | accusative | *fare* + intransitive infinitive (*ardere*) |
| inferno 30:102.3 | li | accusative | dative | dative-of-possession — *l'epa* is the accusative object |
| inferno 30:126.8 | mi | dative | accusative | *rinfarciare* — transitive |
| inferno 31:72.6 | ti | dative | accusative | *toccare* — plain transitive |
| inferno 31:127.2 | ti | accusative | dative | *rendere ... a qualcuno* |
| purgatorio 1:79.8 | ti | dative | accusative | *pregare* — plain transitive |
| purgatorio 1:128.2 | mi | accusative | dative | *fare ... discoverto* + separate accusative *color* |
| purgatorio 6:116.7 | ti | dative | accusative | *muovere* — plain transitive |
| purgatorio 10:53.8 | mi | dative | accusative | *fare* + predicate adverb (*presso*) |
| purgatorio 11:39.6 | vi | accusative | reflexive | *levarsi* — matches the `dep` retag above |
| purgatorio 12:98.2 | mi | accusative | dative | dative-of-possession — *l'ali* is the accusative object |
| purgatorio 13:142.6 | mi | accusative | dative | *richiedere a qualcuno* |
| purgatorio 14:124.8 | mi | dative | accusative | *dilettare* — accusative-experiencer class, not `piacere`-class |
| purgatorio 16:56.6 | mi | accusative | dative | confirmed by trial: flipping `dep` to `obj` regressed `skel` |
| purgatorio 16:113.3 | mi | dative | accusative | *credere* — corpus convention is `obj` (2/2 instances) |
| purgatorio 17:74.6 | mi | accusative | dative | dative-of-possession — *la possa de le gambe* is the object |
| purgatorio 18:13.2 | ti | dative | accusative | *pregare* — plain transitive |
| purgatorio 19:130.7 | ti | dative | accusative | *torcere* — plain transitive |
| purgatorio 19:132.4 | mi | dative | accusative | *rimordere* — plain transitive |
| purgatorio 20:128.5 | mi | dative | accusative | *prendere* — plain transitive |
| purgatorio 21:116.3 | mi | dative | accusative | *fare* + intransitive infinitive (*tacer*) |
| purgatorio 24:25.3 | mi | accusative | dative | *nominare qualcosa a qualcuno* |
| purgatorio 26:148.7 | li | dative | accusative | *affinare* — plain transitive |
| purgatorio 27:92.1 | mi | dative | accusative | *prendere* — plain transitive |
| purgatorio 28:49.2 | mi | accusative | dative | *fare* + transitive infinitive (*rimembrar*) |
| purgatorio 31:58.2 | ti | dative | accusative | *gravare* with no separate accusative object; confirmed by trial |
| purgatorio 32:12.6 | mi | dative | accusative | *fare* + *essere* (copular causee) |
| paradiso 3:48.3 | ti | dative | accusative | *celare qualcuno a qualcuno* — `dep` already tags `mi`/`ti` consistently (dative/accusative) here |
| paradiso 9:35.8 | mi | dative | accusative | *noiare* — accusative-experiencer class |
| paradiso 15:96.2 | li | accusative | dative | *raccorciare qualcosa a qualcuno* |
| paradiso 17:26.5 | mi | accusative | dative | *appressarsi a qualcuno* |
| paradiso 17:114.7 | mi | dative | accusative | *levare* — plain transitive |
| paradiso 20:101.1 | ti | dative | accusative | *fare* + intransitive infinitive (*maravigliar*) |
| paradiso 21:142.6 | mi | dative | accusative | *vincere* — plain transitive |
| paradiso 22:100.7 | mi | dative | accusative | *pingere/spingere* — plain transitive |
| paradiso 26:89.4 | mi | dative | accusative | *fare* + predicate adjective (*sicuro*) |

`case --check` stays **0 hard**. The adjudication join against `dep` (`--stats`) drops from **258
to 208 contradictions** — exactly the 50 rows corrected, none of them reopening as a different
mismatch. `dep --check` stays **0 hard, 0 soft**; `pytest`: **142 passed**; `skel --check`: **0
hard, 3634 soft** (the one point of overlap with a Layer-5 divergence, `purgatorio 11:39`, closed
via the `dep` fix above — the other 49 are `case`-only corrections with no Layer-5 effect, since
`skel`'s checker does not consume `case`).

**What this does not do.** It does not reopen Step 5's "frozen" verdict on regeneration or the
`morph/` merge — both stand. It is not a blanket sweep of the 258 (or the 462 `dep`/`case`/`skel`
three-way population Step 4 measured): only the bare-clitic accusative/dative subset, where a
single textbook valency rule decides the answer. The wider residue Step 4 already classified as
structural (free relatives, the accusative-and-infinitive, the standard of comparison) is
untouched, and the two named weaknesses from Step 5's rejected regenerations are still recorded,
not re-litigated. A further pass over the remaining ~150+ documented-but-uncorrected `case`-is-wrong
positions from Step 4 slices 2 and 3 (see [`../dep/CORRECTIONS.md`](../dep/CORRECTIONS.md)'s
*tier-A candidates were left alone* and *slice 3*) is open but not started.

## Step 7 — the first hand-verified pass over slice 2/3's named-but-uncorrected residue (2026-08-03)

Step 6 closed the bare-clitic population and left the larger, previously-named residue open: the
"21 tier-A candidates" and the slice-3 "201 positions left alone" sections of
[`../dep/CORRECTIONS.md`](../dep/CORRECTIONS.md) had already identified `case` as the dissenting,
wrong read at ~180 named positions, but — under the freeze policy in force when those sections were
written — only ever edited `dep`, never `case/*.tsv` itself. Per the standing rule this file's
opening states (a decided error gets fixed where it's found, not filed), this round went back to
those positions, opened each against its terzina, and corrected the column.

**Method.** `case --stats --full` was rerun to get the current position list (post Step 6), which
matches the doc's named residue closely but not exactly (some of Step 6's 50 overlapped). For the
`nominative`-vs-`obj` shape (the largest class, matching slice 3's "word order — postposed subject"
family), each position was checked mechanically first: does another explicit token attach to the
same head verb as its subject (`nsubj`/`expl`)? Where yes, the flagged pronoun cannot also be that
verb's subject, so it is genuinely the postposed object and `nominative` is wrong. Where no such
sibling existed, each position was read individually against its terzina rather than assumed either
way. Two known-and-named exceptions were preserved without touching `case`: **free relatives**
(`chi`/`che` simultaneously the matrix argument and the subject of their own clause — inferno
5:107.3, 11:51.2, 32:55.4's sibling patterns, purgatorio 2:99.1, 3:62.4, 11:126.3, 14:123.1,
17:50.3), the **standard of comparison** (paradiso 13:131.5, 16:18.10), and the three positions
already on record as genuine restructuring deferrals (inferno 1:117.1, paradiso 11:118.3, 22:55.2 —
untouched, still needing a re-parse the reading alone doesn't settle) and the **entangled/
Layer-2-blocked** set from Step 4 slice 1's family F (paradiso 2:119.3 among them).

**12 impossible pairings — the prepositional oblique and relative-adverbial families (family B/C
from Step 4 slice 1's original triage).** These were characterized back in slice 1 as "`case` is
wrong, a preposition governs the pronoun" / "`case` is wrong" but left un-edited only because the
column was frozen at the time — the reading itself was never in doubt. Retagged `nominative` →
`ablative` (the corpus's own residual class for the prepositional-oblique/partitive read, per
[`README.md`](README.md)'s *oblique tail*): inferno 2:82.5 (*la cagion che*), 11:97.5 (*a chi la
'ntende*), 23:8.6 (*l'un con l'altro*); purgatorio 10:134.3 (*'n chi la vede*), 26:1.9 (*innanzi
altro*), 26:32.5 (*con una*), 28:50.4 (*nel tempo che*); paradiso 10:140.4 (*ne l'ora che*), 13:16.6
(*ne l'altro*), 16:116.3 and 17:50.6 (*a chi*), 20:144.2 (*in che... acquista*). `case --check`
stays 0 hard throughout.

**99 contradictions — the word-order family, corpus-wide.** `nominative` → `accusative` on a bound
relative or demonstrative pronoun (`che`/`ch'`/`chi`/`quel`/`quello`/`quelle`/`ciò`/`tutto`/`un`/
`lui`/`lei`/`questo`/`qualunque`/`essi`) genuinely functioning as the postposed object of its clause,
its antecedent or a separate noun/pronoun holding the subject slot (explicit or pro-drop):

inferno 2:135.5, 3:96.2 (see below — the one `nominative` fix in this batch), 6:43.7, 8:112.5,
9:97.1, 10:98.3, 10:131.7, 12:81.7, 13:86.3, 13:110.3, 14:80.1, 17:77.1, 18:98.2, 19:19.2, 19:117.1,
20:9.1, 21:38.2, 24:136.6, 25:24.4, 25:63.9, 25:124.1, 26:9.3, 26:74.2, 26:105.4, 29:101.6, 30:51.5,
32:112.6, 33:41.3, 34:113.6, 34:138.1; purgatorio 1:129.3, 5:135.2, 6:7.6, 6:39.2, 7:99.1, 7:122.5,
8:29.4, 8:51.4, 10:2.1, 11:46.4, 11:137.1, 13:97.1, 15:44.1, 15:133.7, 16:64.3, 19:11.4, 20:121.4,
22:4.2, 24:82.6, 24:90.2, 28:69.1, 28:75.2, 32:51.2; paradiso 1:78.4, 1:102.1, 1:120.2, 1:126.3,
2:59.3, 3:87.2, 3:102.1, 3:112.2, 4:102.5, 5:21.5, 6:19.5, 6:43.3, 6:58.2, 6:104.7, 8:86.1, 8:95.6,
9:44.1, 9:108.7, 10:95.1, 11:87.1, 11:108.1, 11:135.2, 12:71.6, 12:75.5, 13:54.1, 14:46.6, 18:36.1,
18:84.2, 19:59.3, 19:118.6, 20:80.7, 21:12.3, 21:45.6, 21:102.1, 23:68.2, 23:134.1, 25:87.2, 26:59.3,
27:28.4, 27:97.4, 28:117.1, 31:3.1, 31:69.3, 32:19.5, 33:35.2.

Four of these — **paradiso 19:59.3, 21:12.3; purgatorio 7:99.1**, and one more from this list —
are the same positions dep/CORRECTIONS.md's *21 tier-A candidates* section already named ("the
postposed noun really is the subject and `che` really is the object; `case` inverted them"); the
rest are slice 3's unflagged population getting the same reading applied for the first time.

**1 `accusative` → `nominative` — a si-passive, not a word-order case.** **Inferno 3:96.2** *ciò che
si vuole* (the porter's "what is willed there is willed, and ask no further" — canto III's most
quoted line): `che` refers to `ciò` and is the grammatical subject of the passive `si vuole` ("that
which is willed"), not its object; the parallel construction with `si puote` in the line before
confirms the passive reading. `dep` already had this right (`nsubj`); `case` read the semantic
patient role instead of the promoted-subject syntax.

**9 `dep` retags surfaced while verifying the above — two small, well-precedented families.**
Reading each terzina individually rather than trusting the corpus's stored parse turned up two
already-established `dep` conventions applied inconsistently:

- **Predicative pronoun under a copula, `obj` → `attr`** (the same convention that took 11 rows in
  an earlier round): inferno 13:52.3 *chi tu fosti*, 16:32.3 *chi tu se'*, 32:55.4 *chi son cotesti
  due*; paradiso 21:105.4 *chi fue* — all "tell me who you were/are" indirect questions with `chi`
  predicated of *essere*, missed by the earlier sweep. `case`'s `nominative` read was already
  correct for these and was left untouched, exactly as the original 11 sided with neither layer's
  case claim.
- **A subject plainly mistagged object, `obj` → `nsubj`**: inferno 9:10.1 *I' vidi ben sì...* and
  22:31.1 *I' vidi, e anco il cor...* (`I'` = apocopated *io*, unambiguously the subject of *vidi*),
  inferno 12:23.1 *c'ha ricevuto già 'l colpo mortale* (the relative pronoun already has an explicit
  object, *'l colpo mortale* — it cannot also be one), purgatorio 26:105.4 *l'affermar che fa
  credere altrui* and paradiso 9:106.7 *l'arte ch'addorna* (same test: the head verb's object slot
  was already filled by a separate token, so the flagged pronoun had to be the subject). `case` was
  already correct (`nominative`) at all five and was left untouched.

**State check.** `case --check`: 0 hard. `dep --check`: 0 hard, 0 soft. `pytest`: 142 passed.
`skel --check`: 3634 → **3631** soft (the 9 `dep` retags' effect; none of the 111 pure-`case` edits
touch Layer 5, which does not consume `case`). The adjudication join (`--stats`) drops from **208
contradictions / 40 impossible pairings** to **100 contradictions / 28 impossible pairings** — 111
`case` corrections total (12 impossible-pairing + 99 contradiction), all recorded above.

**What's still open.** The remaining 100 contradictions are the `accusative`-vs-`nsubj` (the
accusative-and-infinitive convention and its genuine exceptions), `dative`-vs-`obj` (the
transitivity test that decided the earlier 40-row "clitic dative" family), `accusative`-vs-`iobj`,
and `dative`-vs-`nsubj` shapes — none of the word-order family this round mechanized. The 28
remaining impossible pairings are family A (the comparative standard, measured unstable — 65/35 —
and correctly left alone) and family F (entangled/Layer-2-blocked, also correctly left alone). A
follow-up batch should apply the same per-position terzina check to those shapes; the transitivity
test used for slice 2's original 40-row dative family (does the head verb already carry an
explicit object?) is the natural starting heuristic for the `dative`-vs-`obj` shape.

## Step 8 — `dative`-vs-`nsubj`, `accusative`-vs-`iobj`, `dative`-vs-`obj` (2026-08-03)

Continuing Step 7's per-shape sweep of the named residue: the three smaller contradiction shapes
(`dative`-vs-`nsubj`, `accusative`-vs-`iobj`, `dative`-vs-`obj` — 8 + 12 + 24 = 44 candidates) were
each opened against their terzina, read individually, and a plain transitivity test applied where
the verb's argument structure decided it: **does the head verb already have an explicit object
filled?** If yes, the flagged pronoun is genuinely the second (dative/indirect) argument and
`case`'s reading is right — a `dep` retag is due instead. If no, the flagged pronoun is the verb's
sole complement and takes the verb's basic (accusative/direct-object) valency, so `case`'s dative
read was simply wrong. `accusative`-vs-`iobj` mirrors the same test in the other direction: a
flagged pronoun tagged `iobj` by `dep` next to an already-filled object is genuinely dative, not
accusative.

**33 `case` corrections — dative read simply wrong, fixed to the verb's basic valency:**

- **19 → `accusative`** (verb's sole complement, ordinary transitive object): inferno 9:102.3
  *cui... stringa e morda*, 13:84.7 *m'accora*, 17:77.6 *m'avea 'mmonito*, 20:97.2 *t'assenno*,
  29:36.4 *m'ha... fatto*; purgatorio 7:102.2 *cui... pasce*, 10:47.6 *che m'avea*, 13:93.8
  *s'i' l'apparo*, 18:4.3 *cui... frugava*, 18:96.1 *cui... cavalca*, 27:108.5 *me... appaga*;
  paradiso 2:130.4 *cui... fanno bello*, 14:48.4 *a lui veder* (the fronted infinitive-marker `a`
  governs `veder`, not `lui` — `lui` is `veder`'s direct object), 19:90.4 *lui cagiona*, 20:62.3
  *cui... plora*, 21:57.7 *t'ha posta*, 22:55.2 *m'ha dilatata*, 28:48.2 *m'avrebbe... sazio*
  (factitive *avere*+adjective, same shape as *fare*+adjective), 30:140.3 *v'ha... fatti simili*.
- **2 → `reflexive`** (an inherently pronominal verb, not a true dative/accusative argument):
  inferno 26:12.7 *m'attempo* (*attemparsi*, "to age" — obligatory reflexive, no independent
  referent), purgatorio 13:108.5 *che sé... presti* (*prestarsi a*, "to lend oneself" — same
  subject as the antecedent *colui*).

**11 more `case` corrections from `accusative`-vs-`iobj`, same test, opposite direction — the
verb's own object was already filled, so the flagged clitic is the second (dative) argument, fixed
`accusative` → `dative`:** inferno 29:15.2 *m'avresti... lo star dimesso* (object `lo star`
filled); purgatorio 1:64.3 *Mostrata ho lui... la gente* (object `gente` filled), 4:117.2 *non
m'impedì l'andare* (object `l'andare` filled), 11:118.8 *dir m'incora bona umiltà* (object `umiltà`
filled), 11:119.6 *tumor m'appiani* (object `tumor` filled), 19:95.10 *ch'io t'impetri / cosa*
(object `cosa` filled), 22:95.2 *m'ascondeva quanto bene* (object clause filled), 23:57.3
*rispuos' io lui* (*rispondere* inherently governs dative, "answer *to* someone", no direct
object exists to compete for); paradiso 19:68.2 *t'ascondeva la giustizia* (object `giustizia`
filled), 21:45.8 *tu m'accenne* (object `che`/*l'amor* filled), 27:97.7 *lo sguardo m'indulse*
(object `che`/*virtù* filled).

**2 `dative`-vs-`nsubj` corrections — plain subject pronouns misread as an oblique case, fixed to
`nominative`:** inferno 6:104.2 *crescerann' ei* ("will they grow" — `ei` = *essi*, subject of
*crescerann'*), purgatorio 7:13.3 *tal parve quelli* ("he seemed such" — `quelli` = *egli*,
subject of *parve*).

**3 `dep` retags — `case` was already right, `dep` had mistagged the deprel:**

- **`iobj` → `obj`**: inferno 26:9.8 *Prato... t'agogna* (*agognare* is a plain transitive verb,
  "to long for someone" — accusative direct object, no dative sense; `case`'s `accusative` was
  already correct).
- **`obj` → `iobj`** (×2): inferno 10:114.6 *l'error che m'avete soluto* (*sciogliere un dubbio a
  qualcuno*, "to resolve a doubt for someone" — the doubt itself, `che`, is the direct object even
  though tagged `obl` for its relative-clause fronting; `m'` is the dative beneficiary), paradiso
  4:32.6 *questi spirti che... t'appariro* (*apparire* is inherently intransitive/unaccusative —
  "to appear *to* someone" — it cannot take a direct object at all, so `t'` must be dative).

**11 positions left alone, each for a stated structural reason — not decided by the reading
alone:**

- **Fused infinitive+clitic, `dep` tags the whole unit's clause-level role, `case` tags the
  embedded clitic's own case — not a disagreement, a scope mismatch** (matches the existing *fused
  tokens `dep` can't align component-wise* convention): inferno 2:81.7 *ch'aprirmi il tuo talento*
  (`aprirmi` = *aprire*+*mi*, `mi` genuinely dative — "to open to me" — while `dep`'s `nsubj` tags
  the whole infinitive clause, correctly, as the impersonal `è`'s subject), inferno 23:128.7
  *dirci* (same shape, `ci` dative within a fused infinitive tagged `nsubj` of *dispiaccia*),
  purgatorio 14:20.1 *dirvi ch'i' sia* (same shape again, `vi` dative within a fused infinitive
  tagged `nsubj` of *parlare*).
- **Free relative — `chi` is simultaneously its own clause's subject (`dep`'s read) and the whole
  clause's semantic role in the matrix clause (`case`'s read)**, the same structural ambiguity
  already on record for the `nominative`-vs-`obj` shape: paradiso 33:17.2 *a chi domanda* (`chi` is
  `nsubj` of *domanda* within its own clause, but the free relative *a chi domanda* as a whole
  fills a dative argument slot of *soccorre*).
- **Causative-construction ambiguity, genuinely undecided by the text alone**: purgatorio 26:105.7
  *che fa credere altrui* (*altrui*, the invariant oblique form, as the causee of *fare* + the
  otherwise-intransitive *credere* — Italian causative rules mark an intransitive infinitive's
  causee as accusative, but *credere* itself inherently governs dative ["credere a qualcuno"],
  and the two rules conflict here).
- **Impersonal dative-experiencer/passive ambiguity**: paradiso 11:11.3 *con Bëatrice m'era...
  accolto* (mirrors this very README's own opening example, "mi pesa" = "it weighs on me" —
  `dep`'s `nsubj` treats the impersonal passive as if `m'` were its subject, but the construction
  is at least as naturally read as a dative experiencer of a null-subject impersonal, matching
  `case`'s `dative`).
- **Latin quotation**: paradiso 32:12.5 *'Miserere mei'* (a direct Psalm 51 quotation; Latin
  *miserere* governs the genitive, which does not map onto this vocabulary's Italian-grammar
  case values — the existing *Latin quotations* exception from the slice-3 residue).
- The 4 remaining `accusative`-vs-`nsubj`-adjacent items visible in this batch's fetch but not
  part of these three shapes were left untouched — they belong to the still-open
  `accusative`-vs-`nsubj` shape below.

**State check.** `case --check`: 0 hard. `dep --check`: 0 hard, 0 soft. `pytest`: 142 passed.
`skel --check`: 3631 → **3633** soft (the 3 `dep` retags' net effect — two moved a divergence in,
one moved one out; none of the pure-`case` edits touch Layer 5). `--stats` contradictions: 100 →
**63** (37 resolved: 33 `case` corrections + 3 `dep` retags = 36 positions decided out of 44
candidates, plus one already-decided position from Step 7's tally overlapped the count by one).

**What's still open.** The `accusative`-vs-`nsubj` shape (~44 candidates, unchanged by this batch)
is the only shape left from the plan's original four. Per the handoff that opened this batch, it is
mostly the accusative-and-infinitive convention (leave alone) and si-passive reads (check each),
plus a residue of plain subject pronouns (`el`/`ei`/`elli`/`tu`/`io`/`noi`/`che`/`ciò`/`quel`-family
demonstratives) misread as accusative that should become `nominative` — the same word-order logic
Step 7 already mechanized for the `nominative`-vs-`obj` shape, just with the disagreeing values
swapped. The 28 impossible pairings (family A comparative-standard + family F entangled) remain
correctly left alone, as in Step 7.

## Step 9 — `accusative`-vs-`nsubj`, the last named shape (2026-08-03)

The final shape from the plan's original four: all **43** `accusative`-vs-`nsubj` contradictions,
each opened against its terzina and read individually. The shape split exactly as Step 8's closing
note predicted — a large residue of plain subject pronouns misread as accusative, plus a smaller
set of positions where the two layers are not disagreeing at all but describing different scopes.

**31 `case` corrections, `accusative` → `nominative`.** The flagged pronoun holds the subject slot
of its own clause; `dep`'s `nsubj` was right and `case` read the pronoun's semantic patient role,
or its antecedent's role, instead of its syntax. Three families:

- **Relative/demonstrative subject with the object slot already filled by a separate token** — the
  mirror image of the word-order test Step 7 mechanized for `nominative`-vs-`obj`: inferno 13:83.3
  *quel che... a me satisfaccia*, 31:116.1 *la valle che fece Scipïon... reda* (object *Scipïon*),
  33:5.3 *dolor che 'l cor mi preme* (object *'l cor*); purgatorio 20:97.1 *Ciò ch'io dicea...
  tanto è risposto*, 28:89.4 *ciò ch'ammirar ti face* (subject of *procede*); paradiso 3:87.1 *ciò
  che... si squaderna* (subject of *s'interna*), 12:26.5 *li occhi ch'... conviene chiudere e
  levarsi* (the eyes do the closing; `accusative` is untenable on any reading of the impersonal
  *conviene*), 21:95.5 *quel che chiedi* (subject of *s'innoltra*), 23:92.2 *il quale e il quanto
  de la viva stella* (the star's quality is what paints the eyes — object *ambo le luci* is
  filled), 28:5.2 *vede colui che se n'alluma* (object *fiamma* filled), 28:110.7 *l'atto che
  vede*, 28:111.4 *quel ch'ama*, 28:111.6 *che poscia seconda*, 33:90.2 *ciò ch'i' dico è un
  semplice lume*.
- **Plain subject pronouns** (`el`/`elli`/`noi`/`i'`/`nessun`/`quale`): inferno 5:90.1 *noi che
  tignemmo... pregheremmo*, 12:81.8 *ciò ch'el tocca*, 19:52.2 *Ed el gridò*, 23:64.7 *sì ch'elli
  abbaglia*, 25:34.6 *ed el trascorse*, 29:36.6 *m'ha el fatto... più pio*; purgatorio 2:72.4 *di
  calcar nessun si mostra schivo*, 13:54.6 *quel ch'i' vidi poi*, 20:17.8 *ch'i' sentia*; paradiso
  6:43.4 *quel ch'el fé portato*, 19:12.6 *quand' era nel concetto e 'noi' e 'nostro'* (the quoted
  word is the copula's predicate nominal), 20:80.8 *lo color ch'el veste*, 26:59.4 *la morte ch'el
  sostenne*.
- **Si-passives — the promoted subject, not the semantic patient**, applying Step 7's inferno
  3:96.2 verdict (*ciò che si vuole*) to the remaining three: purgatorio 11:27.4 *quel che talvolta
  si sogna*; paradiso 2:65.3 *li quali... notar si posson* (the plural *posson* agreeing with
  *lumi* settles it), 3:93.2 *che quel si chere*.

**12 positions left alone, each for a stated structural reason** — all four exceptions already on
record, none a new one:

- **Accusative-and-infinitive** (a perception/causative verb's object doubling as the infinitive's
  subject — the framework choice `case` and `dep` describe from opposite ends, deliberately not
  reconciled): inferno 22:32.1 *I' vidi... uno aspettar*; purgatorio 19:74.3 *sentia dir lor*,
  30:95.1 *'ntesi... lor compatire a me*; paradiso 8:46.7 *vid' io lei far piùe*, 27:21.4 *vedrai
  trascolorar tutti costoro*, 30:57.1 *compresi me sormontar*.
- **Fused infinitive+clitic — a scope mismatch, not a disagreement** (`dep` tags the whole unit's
  clause-level role, `case` the embedded clitic's own case; same convention as Step 8's *aprirmi*
  family): purgatorio 8:45.4 *grazïoso fia lor vedervi* (`vi` accusative inside an infinitive
  clause tagged `nsubj` of *grazïoso*), paradiso 29:92.1 *quanto sangue costa seminarla* (`la`
  accusative inside an infinitive tagged `nsubj` of *costa*).
- **Free relative** — the pronoun is simultaneously its own clause's argument and the whole
  clause's role in the matrix clause: paradiso 32:56.1 *è stabilito quantunque vedi* (object of
  *vedi*, subject of *è stabilito*), plus paradiso 3:59.5 *non so che divino* — the fossilized
  *non so che* idiom, where `che` is at once the object of *so* and the head of the phrase that
  serves as subject of *risplende*.
- **Causative causee**: paradiso 2:51.5 *fan di Cain favoleggiare altrui* (`altrui` is the
  invariant oblique form and cannot be nominative; Italian causative rules mark the causee of an
  intransitive infinitive accusative, while `dep` gives the standard UD `nsubj` of the infinitive
  — the same construction Step 8 left alone at purgatorio 26:105.7).
- **Latin quotation**: purgatorio 8:13.1 *'Te lucis ante'* (the hymn's own Latin accusative, quoted
  whole; `dep` tags the citation's role in the Italian sentence, which the Latin form does not
  answer to — the existing *Latin quotations* exception).

**State check.** `case --check`: 0 hard. `dep --check`: 0 hard, 0 soft (untouched — this batch made
no `dep` retags; every position resolved was a `case` error or a stated exception). `pytest`: 142
passed. `skel --check`: **3633** soft, unchanged (pure-`case` edits do not touch Layer 5).
`--stats` contradictions: 63 → **32**; `dep=nsubj` agreement 5139/49 → 5170/18.

**What's left.** All four named shapes from the plan are now worked through. The 32 remaining
contradictions are the accumulated *verified-and-left-alone* residue of Steps 7-9 (accusative-and-
infinitive, fused infinitive+clitic, free relatives, causative causees, impersonal
dative-experiencers, Latin quotations) plus the 14 `dep=obj`-side positions — mostly free-relative
`chi` — that the `nominative`-vs-`obj` sweep also left standing for the same reasons. The 28
impossible pairings (family A comparative-standard + family F entangled) remain correctly left
alone. No shape-driven pass is open; a future round would have to re-litigate structural
conventions the corpus has deliberately fixed, which is out of scope.

## Step 10 — four corrections from Layer 5's rule-U round, 2026-08-03

[`../skel/CORRECTIONS.md`](../skel/CORRECTIONS.md)'s *Phase 5r* made this annex a third read in
Layer 5's divergence checker (rule U: accept a `role_mismatch` when the frozen case value
corroborates the `dep`-derived role and not the LLM's). Reading its 17 mirror-direction candidates
by hand turned up four positions where **this column** was the wrong one — the same standing rule
Steps 6-9 followed: a clear, decidable error gets fixed in the session that finds it.

- **purgatorio 14:12.3 `ne` `ablative` → `accusative`**, **14:12.6 `ne` `ablative` → `dative`**,
  **14:13.8 `ne` `ablative` → `accusative`**. *per carità ne consola e ne ditta / onde vieni e chi
  se'; ché tu ne fai tanto maravigliar*: all three `ne` are the Tuscan *ne* = *ci* ("us"), not the
  partitive the model read. *consolarci* takes it accusative; *dittarci onde vieni* has its
  content clause as the object, leaving `ne` the dative addressee (Step 8's transitivity test);
  *far maravigliare* takes it as an accusative causee. `dep` was retagged to match at both
  12.6 (`obj` → `iobj`) and 13.8 (`obl` → `obj`), see
  [`../dep/CORRECTIONS.md`](../dep/CORRECTIONS.md)).
- **paradiso 1:48.4 `li` `accusative` → `dative`**. *aguglia sì non li s'affisse unquanco*:
  *affissarsi* is reflexive and takes its target obliquely (*a/in esso*), so an accusative direct
  object is impossible here; `li` is the archaic dative. `dep`'s `obl` was already right and was
  left untouched.

**State check.** `case --check`: 0 hard. `dep --check`: 0 hard, 0 soft. `pytest`: 149 passed.
`skel --check`: **3465** soft. `--stats` contradictions: **32**, unchanged (12:12.6's new
`dative` would have contradicted `dep=obj`, so that deprel was retagged `iobj` in the same round);
impossible pairings: 28 → **26** (both closed by the `dep` retags at
inferno 10:136.1 and paradiso 23:68.1); `dep=nsubj` agreement 5170/18 → 5172/18.

## Eleven corrections from Layer 4's multiple-`obj` round (2026-08-03)

[`../dep/CORRECTIONS.md`](../dep/CORRECTIONS.md)'s *"at most one `obj` per predicate" rule* read
203 predicates against their terzine and retagged 316 rows. Ten of those retags moved a pronoun
position into fresh contradiction with this annex, and **in all ten the annex was the wrong side** —
the same two shapes Steps 6-8 worked, found by a different instrument. Fixed here, in the session
that found them, per this file's standing rule.

**Seven clitic datives read as accusative** (`accusative` → `dative`): inferno 8:93.2 *che **li**
ha' iscorta sì buia contrada*, 12:86.2 *mostrar **li** mi convien la valle buia*, 25:54.2 *poi
**li** addentò e l'una e l'altra guancia* (dative of possession), 26:9.8 *che Prato ... **t'**agogna*,
26:67.3 *che non **mi** facci de l'attender niego*, purgatorio 19:86.3 *ond' elli **m'**assentì ...
ciò che chiedea*, paradiso 2:63.5 *l'argomentar ch'io **li** farò avverso*. In each the head verb's
object is filled by something else in the same clause — Step 8's transitivity test, reached this
time from Layer 4's side.

**Two subjects read as accusative** (`accusative` → `nominative`): inferno 8:93.1 *ché tu qui
rimarrai, **che** li ha' iscorta sì buia contrada* (the relative resumes *tu*), paradiso 14:5.1 *ne
la mia mente fé sùbito caso **questo** ch'io dico* (*far caso* is the idiom; *questo* is what makes
it).

**One subject read where the object stands** (`nominative` → `accusative`): purgatorio 19:144.3
*pur che la nostra casa non faccia **lei** per essempro malvagia* — *casa* is the subject and *lei*
what it would make wicked; `dep` had the two inverted and was corrected in the same round.

**Plus one fused-token value** (`accusative+ablative` → `dative+ablative`): inferno 29:125.6
*«Tra'**mene** Stricca* — *me* is a dativus ethicus, not an object; *ne* keeps its ablative. This is
the fused-token scope Phase 5r's rule U had to gate on, so the row is also the annex's own answer
to what that gate excludes.

**State check.** `case --check`: 0 hard. `dep --check`: 0 hard, 0 soft. `pytest`: 154 passed.
`--stats` contradictions: 32 → **31**; impossible pairings: **26**, unchanged;
`skel --check`: 3465 → **3509** soft, for the reason
[`../dep/CORRECTIONS.md`](../dep/CORRECTIONS.md) states.

## One row from Layer 4's subject-agreement round (2026-08-07)

Layer 4's new subject-agreement check (see [`../dep/CORRECTIONS.md`](../dep/CORRECTIONS.md))
established that paradiso 6:136 *il* in "E poi il mosser le parole biece" is the clitic object
**lo**, not an article — Layer 2 was retagged `pronoun`. That brought the position into the annex's
scope, and `case --check` reported it as a missing row. Added: `136 3 il accusative`. The annex is
back to **0 hard**, and `--stats` is unchanged (31 contradictions, 26 impossible pairings).

## Thirty-two rows from Layer 5's membership audit (2026-08-09)

Layer 2's membership round (see [`../morph/CORRECTIONS.md`](../morph/CORRECTIONS.md)) retagged 32
tokens as pronouns — 16 `onde`, 2 `quantunque`, 8 proclitics that had been articles, 2 `e'`, and
4 clitics that had been prepositions — which brings each of them into the annex's scope
(`case.scope_slots` reads Layer 2's `pos` column), and `case --check` reported them as missing
rows: 32 hard, 12 of them whole lines the annex had never had a row for. Same shape as the single
paradiso 6:136 row the subject-agreement round added, at larger scale.

Each value was read off the position's own clause, not inferred from `dep`:

- **`ablative` (17)** — every `onde`/`ond'` ("da cui"), plus paradiso 30:69 *n'* ("un'altra
  **n'**uscia fori").
- **`accusative` (9)** — the 2 `quantunque` (objects of *guarda*/*vorrai*) and 7 of the 8
  proclitics.
- **`dative` (2)** — inferno 13:97 *l'* ("non **l'**è parte scelta") and paradiso 10:111 *ne*
  ("là giù **ne** gola", the Tuscan *ne* = *ci*).
- **`nominative` (3)** — purgatorio 32:116 *el*, and the two `e'` subjects.
- **Fused (2)** — inferno 29:34 *sen* = `reflexive+ablative`, the annex's existing value for that
  cluster; purgatorio 12:48 *nel* = *ne lo* = `ablative+accusative`, one case per component in
  reading order.

`case --check` is back to **0 hard**. `--stats` is unchanged by the round: **34** contradictions
and **26** impossible pairings before and after (34 is also what HEAD measures — the 31 this file
last recorded predates Layer 4's subject-agreement round, which evidently added three and did not
re-measure). None of the 32 new rows is among them.
