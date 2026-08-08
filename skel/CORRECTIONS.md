# skel — Layer 5 correction history

## Rule V, the control/participial subject chain — 3136 → 2623, −513 (2026-08-09)

This started as a per-position read of **Inferno 1's twelve** soft violations, asked for as a check
on what the residue actually consists of. Four of the twelve were one thing: `derive_unit` has no
rule for the subject of a **non-finite** predicate. Classifying all 805 `extra_arg subj` violations
corpus-wide — the largest single class, 26% of the residue — showed the same four shapes account
for most of it, and that they are the checker's silence rather than a reading disagreement.

### What derive_unit was doing

`derive_unit` reads a predicate's own dep children. A predicate with no `nsubj` child and no finite
morphology therefore gets **no `subj` row at all** — not "∅", which rule 4 reserves for finite
pro-drop, but nothing. `_apply_subj_authority` already accepted an LLM subject at such a position,
but only from a candidate set built from the **immediate** head, and only when the predicate's own
deprel was `xcomp`/`ccomp`, and only from that head's `subj`/`obj`. Everything else the LLM
resolved was reported as `extra_arg subj`. The classification (all 805, by whether the derivation
also proposed a competing subject):

| shape | n | why the candidate set missed it |
|---|---|---|
| control subject reachable up the chain | 289 | the walk stopped at the immediate head |
| `acl` participle, subject = modified noun | 155 | `acl` was not a control deprel at all |
| LLM says ∅ where derivation has a subject | 127 | genuine disagreement, left flagged |
| head-to-head (derivation has a *different* subject) | 189 | genuine disagreement, left flagged |
| causative: the matrix `iobj` is the causee | 13 | `iobj` was not a candidate role |
| other | 32 | left flagged |

### Rule V

`_control_subject_candidates` walks the predicate's dep head chain (limit 8) and collects, at each
link, the `subj`/`obj`/`iobj` of that ancestor's **derived** rows, plus the modified nominal itself
when the link is `acl`/`acl:relcl`. It stops at the first ancestor that has a subject of its own —
that clause supplies the controller, and a subject taken from beyond it stays flagged. Two readings
of Italian are what the walk encodes:

- **Control / raising through a chain of subjectless non-finite links.** "e molte genti **fé** già
  *viver* *grame*": `grame` is an xcomp of `viver`, itself an xcomp of `fé`, and the controller
  `genti` is `fé`'s object, two links up. Which argument controls is lexical — subject control
  (*vuole partire*), object control (*fé … viver*), the causative's **dative** causee ("ella **mi**
  fa *tremar* le vene") — so all three roles are candidates.
- **The adnominal participle.** "le sue spalle *vestite* de' raggi", "io, *vinto* dal sonno",
  "prieghi *fatti* a Dio": an `acl` participle's subject is the nominal it modifies. 155 positions,
  and the shape is unambiguous — 154 of them `acl`, 1 `acl:relcl`.

A second pass added the case Inferno 1:63 exposed: when the walk reaches a matrix whose own subject
`derive_unit` could only give as pro-drop **∅** ("chi per lungo silenzio *parea* fioco"), the
controller is a referent the derivation never resolved, so it cannot adjudicate the LLM's
resolution of it either. That is exactly what `_apply_subj_authority`'s pro-drop branch already
concludes one level down, and the walk now returns it as an `unresolved` flag (−50 further).

Membership in the candidate set is an **acceptance, never an assertion**: the derivation still says
nothing at these positions, and a subject from outside the set is still reported. Five new tests in
`tests/test_skel.py` pin the participle, the two-link chain, the causative dative, the pro-drop
matrix, and the walk's stop condition (a subject taken past a subject-bearing ancestor still
flags).

### The cross-layer corrections the same audit produced

Classifying the 82 `membership` violations by the Layer-2 POS of the cited token found five shapes
where Layer 2 was wrong about the word, not Layer 5 about the argument: `onde` as a conjunction
where it is a relative pro-form (16), `quantunque` (2), proclitic pronouns tagged as articles (8),
`e'` read as a form of `essere` (2), fused clitic clusters and adverbs tagged as prepositions (7),
plus 2 tags corrected in the other direction. All 37 are in
[`../morph/CORRECTIONS.md`](../morph/CORRECTIONS.md), with the 32 case rows and 4 Layer-3 clitic
mentions they pulled in ([`../case/CORRECTIONS.md`](../case/CORRECTIONS.md),
[`../np/CORRECTIONS.md`](../np/CORRECTIONS.md)) and eight Layer-4 retags
([`../dep/CORRECTIONS.md`](../dep/CORRECTIONS.md)).

### Measured

| kind | before | after | Δ |
|---|---|---|---|
| `extra_arg` | 1544 | 1065 | **−479** (−31%) |
| `membership` | 82 | 47 | **−35** (−43%) |
| `role_mismatch` | 292 | 288 | −4 |
| `missing_arg` | 953 | 957 | +4 |
| `extra_tuple` | 156 | 157 | +1 |
| `missing_tuple` | 109 | 109 | 0 |
| **total** | **3136** | **2623** | **−513 (−16.4%)** |

By step: rule V in its first form −427, the cross-layer corrections −34, the pro-drop extension
−50, inferno 1:112's Layer-4 rows −2. `extra_arg subj` itself went **805 → 327**, of which 127 are
the LLM asserting ∅ against a derived subject. Inferno 1 went **12 → 5**.

`skel --check` 0 hard / **2623** soft; `dep --check` 0 hard / 18 soft; `case --check` 0 hard;
`np --check` 0/0; `morph --check` 0/0; `pytest` 173 passed.

### What Inferno 1's five survivors say about the rest

Two are LLM slips that only regeneration settles (27.3 reads *persona viva* as the subject of "lo
passo che non lasciò già mai persona viva"; 122.5 promotes the comparative adverb *più* to a
predicate). One is an attachment-level disagreement (`nel foco` cited on the predicate adjective
*contenti* rather than on its copula). **Two are one open question**: "fui **per** *ritornar* più
volte vòlto" has Layer 4 treating `per` + infinitive as `obl` + `case`, where UD would have
`advcl` + `mark`, so the LLM's predicate reading of the infinitive is reported as both an
`extra_tuple` and a `missing_arg obl:per`. `missing_arg obl:per` stands at 44 corpus-wide; whether
that convention should change is a Layer-4 question, not a checker one, and it is the next named
route — see [`../PLAN.md`](../PLAN.md).

The `membership` remainder (47) is deliberately untouched: substantivized adjectives (23 before the
round), quoted mention words as the object of a verb of saying ("faceva dir l'un ‘No’"), and
adverbs cited as objects ("non sa **como**"). None of those is a data error — they are all
questions about what the check should admit as an argument, and they need a decision on the check
rather than an edit to an artifact.

## Phase 5t: the `--fix` round after the subject-agreement corrections — 3270 → 3136, −134 (2026-08-09)

Baseline: **0 hard, 3270 soft**, **1575 flagged parse units** — the state left by Layer 4's
subject-agreement round (2026-08-07, below). One full `--fix` pass over all three canticles, run by
the user as `make -C skel fix` 3-way parallel. It was run on Phase 5s's recommendation: a
cross-layer correction round had just moved 424 Layer-4 and 77 Layer-2 rows under the flagged set,
which is the condition 5s measured as the one that makes regeneration pay.

Measured from a `git worktree` at the pre-`--fix` commit (with the generated `src/` canticle
directories symlinked in), diffed against the working tree at the **parse-unit** level
(`dep.sentence_groups`, which is what `--fix` regenerates):

| metric | measured |
|---|---|
| units flagged before | 1575 |
| units flagged after | 1527 (**−48 cleared outright**) |
| units improved | 96 |
| soft violations removed | **134** (3270 → **3136**, −4.1%) |
| violations removed per LLM call | **≈0.085** |
| units that got *worse* | **0** (Phase 5c's criterion held) |
| units newly flagged | **0** |
| cantos touched | 61 — inferno 22, purgatorio 19, paradiso 20 |

Per class:

| kind | before | after | Δ |
|---|---|---|---|
| `extra_arg` | 1580 | 1544 | −36 (−2.3%) |
| `missing_arg` | 985 | 953 | −32 (−3.2%) |
| `role_mismatch` | 305 | 292 | −13 (−4.3%) |
| `extra_tuple` | 175 | 156 | −19 (−10.9%) |
| `missing_tuple` | 140 | 109 | **−31 (−22.1%)** |
| `membership` | 85 | 82 | −3 (−3.5%) |

**Phase 5s's prediction held only for the population that round created, not for the pass as a
whole.** The overall yield came in at **0.085 per call** — indistinguishable from 5q's 0.086 and
5e's 0.11, the flat rate on a *static* residue, and less than half of 5s's 0.199. But the class
breakdown is not flat: `missing_tuple` fell **22.1%**, five times the pass average and the largest
single-class move of any `--fix` round on record, while the two big classes moved 2-3%, i.e. at
their usual regeneration-resistant rate. `missing_tuple` is exactly where the subject-agreement
round's +105 had landed (the 99 promoted speech frames), so the same pattern as 5s — where
`extra_tuple`, the `adverb` bug's population, moved furthest — repeated in miniature.

**The corrected reading of 5s's rule**, which supersedes the version `PLAN.md`'s *Where Phase 5
ended* carried: a cross-layer correction round does **not** raise the yield of the next `--fix`
pass as such. It creates a *sub-population* that regeneration settles at a high rate, and the
pass-level yield is that rate diluted by however much of the flagged set the new population
occupies. In 5s the two 2026-08-03 populations were large against 1659 units, so the pass looked
like a break from the stop rule; here +105 against 1575 units was too small, and the pass reverted
to the flat rate. **Phase 5q's stop rule stands** — with the qualification that it is about the
*old* residue, and says nothing about freshly created LLM-authored error, which is worth
regenerating whatever its size.

What changed, concretely: **33 of the 99 promoted speech frames were taken up by the LLM** and 2
newly appeared (inferno 30:37-38), a net −31. E.g. inferno 3:34 *«Ed elli a me: "Questo misero
modo…"»* went from an empty row to `34.2 elli` carrying `subj (0,0)`, `ccomp 35.1` and
`obl:a 34.4` — the UD ellipsis promotion the subject-agreement round normalized corpus-wide, now
proposed independently by the LLM. The same canto shows the other kind of move: `obl:senza` →
`obl:sanza` at 36:2, the preposition lemma taken from the form the line actually uses.

**Zero units got worse and zero were newly flagged** — the third consecutive round to hold both
(5q, 5s, 5t). As in 5q and 5s, the per-unit acceptance count is not recoverable: `skel/skel.log`
was again left empty by the parallel invocation, so the table reports the flagged-unit delta (−48),
a lower bound on accepted units.

Checks after the round: `skel --check` 0 hard / **3136** soft, `dep --check` 0 hard / 18 soft,
`case --check` 0 hard, `np` and `morph --check` 0/0, `pytest` 168 passed. No code changed; the
round is 61 `skel/*.tsv` files, 303 insertions / 242 deletions.

## Layer 4's subject-agreement round — 3215 → 3270, +55 (2026-08-07)

No Layer-5 change: a new `dep` soft check (an `nsubj` whose person or number contradicts its finite
head's) flagged 173 positions, 155 of which were corrected in Layers 2/4 — see
[`../dep/CORRECTIONS.md`](../dep/CORRECTIONS.md) and
[`../morph/CORRECTIONS.md`](../morph/CORRECTIONS.md). `derive_unit` reads those layers, so the
count moved underneath Layer 5, and, as in the multiple-`obj` round, **it moved up**:

| kind | before | after | Δ |
|---|---|---|---|
| `extra_arg` | 1558 | 1580 | +22 |
| `missing_arg` | 1053 | 985 | −68 |
| `role_mismatch` | 309 | 305 | −4 |
| `extra_tuple` | 174 | 175 | +1 |
| `missing_tuple` | 35 | 140 | +105 |
| `membership` | 86 | 85 | −1 |
| **total** | **3215** | **3270** | **+55** |

`missing_arg` fell by 68 — the derivation now supplies arguments it had been attaching elsewhere —
and the whole of the rise is `missing_tuple`: the 99 **promoted speech frames** ("Ed elli a me:
«…»", where the elided verb of speech makes the subject the clause head) each give `derive_unit` a
predicate the LLM never proposed, exactly as the gapping promotions of the multiple-`obj` round
did. The audit reading of PLAN.md's *A note on Layer 5's count* applies unchanged: this is
`--fix` material — LLM-authored rows against a now-corrected Layer 4 — and `--fix` is user-run
work. Do not "fix" it by reverting the Layer-4 corrections.

The round also started here: it was `skel`'s own 133 `extra_arg subj (0,0)` violations that
exposed the agreement problem. 43 of those had a derived subject that could not agree with its
predicate, which is what made the generalized test worth running over all ~6 000 `nsubj` edges.

## Phase 5s: the `--fix` round the 2026-08-03 work opened up — 3545 → 3215, −330 (2026-08-07)

Baseline: **0 hard, 3545 soft**, **1659 flagged parse units** — the state left by the multiple-`obj`
round and the `adverb` bug fix (both 2026-08-03, below). One full `--fix` pass over all three
canticles, run by the user as `make -C skel fix` 3-way parallel. This is the route PLAN.md's *If a
next task is wanted* had reserved for the user, and the reason to run a third pass after Phase 5q's
stop rule was specific: the 2026-08-03 round had **added two populations that are `--fix` material
by construction** (LLM-authored artifact rows against a now-corrected Layer 4, and the 72
adverb-as-predicate `extra_tuple`s the bug had been absorbing), not the regeneration-resistant
residue 5q measured.

| metric | measured |
|---|---|
| units flagged before | 1659 |
| units flagged after | 1549 (**−110 cleared outright**) |
| soft violations removed | **330** (3545 → **3215**, −9.3%) |
| violations removed per LLM call | **≈0.199** |
| units that got *worse* | **0** (Phase 5c's criterion held) |
| units newly flagged | **0** |
| cantos touched | 91 — inferno 30, purgatorio 30, paradiso 31 |

Per class:

| kind | before | after | Δ |
|---|---|---|---|
| extra_arg | 1687 | 1558 | −129 (−7.6%) |
| missing_arg | 1151 | 1053 | −98 (−8.5%) |
| role_mismatch | 360 | 309 | −51 (−14.2%) |
| extra_tuple | 217 | 174 | −43 (−19.8%) |
| argument | 92 | 86 | −6 (−6.5%) |
| missing_tuple | 38 | 35 | −3 (−7.9%) |

**The prediction held, and this does not reopen Phase 5q's stop rule.** The yield came in at
**0.199 violations per call against 5q's 0.086 and 5e's 0.11** — the first pass to beat that flat
rate, by better than double. The stop rule 5q wrote said *what is left does not respond to
regeneration*; it was measured on a residue that had not yet had a wrong Layer 4 corrected under it.
Every class moved further than in 5q (7.6%/8.5%/14.2% against 4.4%/3.6%/3.4%), and `extra_tuple`
moved most of all (−19.8%) — which is where the adverb bug's +72 had landed. Three of the five
adverb-predicate positions the bug write-up names by hand are now cleared (inferno 11:93 *non men
che saver*, 13:112 *similemente a colui*, 14:44 *fuor che ' demon duri*); 1:122 *più di me degna*
and 21:49 *altrimenti che nel Serchio* still stand. The correct reading is that a regeneration pass
is worth running **after a cross-layer correction round moves the ground under the flagged set**,
not on a static residue.

**Zero units got worse and zero were newly flagged** — the cleanest round on record on both counts
(5q also held the no-worse criterion, but is not recorded against newly-flagged). Line-level counts
do show 49 lines rising, entirely from violations relocating to a neighbouring line inside the same
parse unit; measured at the parse-unit level, which is the unit `--fix` actually regenerates, the
delta is one-directional: **238 units improved, 0 degraded.**

Sample of what changed (inferno 1–2): 1:56 `perder` `subj` → `obj` with `face`'s duplicate `obj`
dropped — the LLM converging on the Layer-4 tree the multiple-`obj` round had just corrected;
1:59–60 the `obl` under fused `venendomi` re-attached as `ripigneva`'s `obl:a`; 2:110/113 the
missing implicit-subject rows (`subj 0 0`) supplied on infinitives and a gerund.

As in 5q, the per-unit acceptance count is not recoverable — `skel/skel.log` was again left empty by
the parallel invocation — so the table reports the flagged-unit delta (−110), a lower bound on
accepted units.

**Current state**: `skel --check` **0 hard, 3215 soft** (down from 17438 at the first full-corpus
measurement, overall Δ14223, 81.6%). `dep --check` 0 hard / 0 soft, `case --check` 0 hard,
`np --check` 0 hard / 0 soft, `pytest` 154 passed.

## The `"verb" in pos` bug: `adverb` matched too — 3509 → 3545, +36 (2026-08-03)

Found while wiring Layer 4's new *at most one `obj` per predicate* rule
([`../dep/CORRECTIONS.md`](../dep/CORRECTIONS.md), same date). Layer 2's `pos` is a `+`-joined
list of components (`verb`, `verb+pronoun`, `adverb`, `conjunction+pronoun+verb`), and three
places in `skel.py` tested it with a plain substring — **`"verb" in "adverb"` is `True`**, so every
adverb in the corpus was being read as a verb:

- `derive_unit`'s **rule 2** ("a non-auxiliary *verb* that itself takes an argument-bearing
  dependent") was promoting adverbs to predicates. The comment above `CLAUSE_HEAD_DEPRELS` says
  *verb*; the code did not.
- `_ccomp_over_a_verbal_argument` (rule for a given `ccomp` against a derived `obj`/`subj`) was
  accepting an adverbial argument as verbal.
- The elided-copula whitelist's "predicate is not a verb" gate was excluding adverbs from a
  whitelist meant to cover exactly the non-verbal predicates.

Fixed by a shared `is_verb_pos(pos)` that splits on non-letters and tests for a `verb`
**component**; two tests pin it (`adverb` and `preposition+adverb` are not verbs, `adverb+verb` and
`conjunction+pronoun+verb` are).

**The count goes up, and every component of the move is an improvement.** By kind: `extra_arg`
1709 → **1687** (−22), `missing_arg` 1156 → **1151** (−5), `role_mismatch` 362 → **360** (−2),
`missing_tuple` 45 → **38** (−7), `argument` **92** unchanged — and `extra_tuple` 145 → **217**
(+72). The +72 are positions where the LLM proposes a comparative or exceptive **adverb** as a
predicate and the derivation, no longer buggy, does not: *non men che saver* (inferno 11:93),
*similemente a colui* (13:112), *fuor che ' demon duri* (14:44), *più di me degna* (1:122), *qui si
nuota altrimenti che nel Serchio* (21:49). Each is an adverb carrying its own comparative standard
as an `obl` child. An adverb is not a predicate in a UD-derived role vocabulary, so all 72 are real
LLM divergences the bug had been silently absorbing by inventing a matching derived tuple. They are
`--fix` material (LLM-authored artifact), not rule material.

Left alone deliberately: the corpus is **not** re-checked for whether those `obl` standards should
attach to the adverb or to the clause head. Both are attested; the rule does not care; and moving
them would be a separate round.

`skel --check`: 0 hard, **3545** soft. `dep --check` 0/0, `case --check` 0 hard, `np --check` 0/0,
`pytest` 154 passed.

## Phase 5r: rule U — the `case` annex as a third read — 3633 → 3465, −168 (2026-08-03)

Phase 5's closing position parked its largest remaining reading-disagreement population with an
explicit reason: deciding it "needs a Layer-2 case feature or a clitic lexicon", and the project
had twice declined to open one. **That feature exists now** — `case/` was built after that verdict
was written and hand-audited against `dep` through the annex's Steps 6-9 — but until this phase
`dante_corpus/skel.py` never imported it. This phase wires it into the checker.

### The measurement (on the post-Step-9 tree, 3633 soft)

Of the **516** `role_mismatch` violations, **210** sit on an argument position the annex holds a
value for. Classifying each by whether that value corroborates the derived (`dep`-side) or the
given (LLM-side) role, under the obvious mapping between the two frozen vocabularies —
`nominative`↔`subj`, `accusative`↔`obj`, `dative`↔`iobj`/`obl:a`, `ablative`/`locative`↔`obl*`,
with `obl:a` deliberately compatible with *both* `dative` and the locative values because Italian
`a` marks both:

| | count |
|---|---|
| `case` corroborates the **derived** side → rule-U candidate | **161** |
| `case` corroborates the **given** side → `dep`-correction candidate | **17** |
| value has no role mapping (`reflexive`/`vocative`/`genitive`/fused `a+b`) | 23 |
| decides neither (both or neither side match) | 9 |

The four biggest buckets are all in the first row: given `obj` / derived `obl:a` with `dative`
(55), given `obj` / derived `subj` with `nominative` (43), given `subj` / derived `obj` with
`accusative` (21), given `obl:a` / derived `obj` with `accusative` (20).

### Rule U (`_case_corroborated_role`), −160

A one-directional acceptance in `_classify_divergence`'s `elif grole != drole:` branch, in the
same shape as rules L/M/N/O: accept the divergence when the annex's value for that argument
position corroborates the **derived** role and *not* the given one. Corroborating both or neither
accepts nothing, and the mirror direction is never an automatic accept — it is the hand round
below. This is the same asymmetry Phase 5j enforced when it rejected rule O's two-directional
variant. `case` data is threaded into the checker the way `dep_index_by_pos`/
`morph_pos_by_position` already are (`validate_unit(..., case_rows=...)`, fed by `skel.py`'s new
`_case_rows`).

**One scope gate, `_bare_pronoun_position`, costs the rule exactly 1 of its 161:** the annex is in
scope for every token whose Layer-2 `pos` *names* a pronoun, fused ones included (601 of the 13113
in-scope positions are `verb+pronoun` and friends), and there `venendomi`'s value is the
enclitic's case while a Layer-5 argument citing that position cites the **verb**. The one instance
this removed is a given `xcomp` / derived `obl` with `ablative` — an infinitive+`ne`, exactly the
scope mismatch the annex's own Steps 8 and 9 left alone by hand. Yield: **3633 → 3473, −160**.

Tests: `tests/test_skel.py`'s `test_case_supports_role_mapping` plus six
`test_classify_divergence_case_*` cases covering the accept, the mirror direction, both-sides,
neither-side, the fused-token gate, and an absent position.

### The 17 `dep`-correction candidates, hand-verified — a further −8

Every position where the annex sides with the LLM against `dep`, read against its terzina. **Ten
`dep` retags** (recorded in [`../dep/CORRECTIONS.md`](../dep/CORRECTIONS.md)) and **four `case`
corrections** (in [`../case/CORRECTIONS.md`](../case/CORRECTIONS.md)) came out of it; the other
**8** are left alone for stated structural reasons, in four families:

- **A copular predicate nominal is nominative too** (5): inferno 7:69.1 *che è*, 24:112.2 *qual è
  quel che cade*, purgatorio 2:120.4 *Che è ciò*, 10:90.3 *L'altrui bene a te che fia*, 23:13.6
  *che è quel ch'i' odo*. `dep` tags the pronoun `attr` (canonicalized to `xcomp`), the LLM calls
  it `subj`, and the annex says `nominative` — but Italian predicate nominals **are** nominative,
  so the value corroborates both readings and adjudicates neither. The mapping cannot separate a
  subject from a copular predicative, and the measurement's "corroborates given" column overstates
  itself by exactly this family. Rule U is unaffected: it is one-directional and never fires here.
- **The tree's preposition is explicit** (1): inferno 12:16.5 *Lo savio mio inver' lui gridò*.
  `lui` carries an `inver'` `case` child, so derived `obl:in` (`_PREP_LEMMA_NORM` folds `inver'`
  into `in`) is what the tree says; the annex reading `lui` as the `dative` addressee of *gridò*
  is a semantic-role read, not a contradiction of the parse. No `dep` error.
- **Fused infinitive+clitic scope mismatch** (1): inferno 21:79.5 *Credi tu... vedermi esser
  venuto*. The annex's `accusative` is `mi`'s; the disputed role is the whole infinitive's. The
  same exception rule U's own gate encodes, and the one Steps 8/9 already established.
- **Comparative standard** (1): paradiso 13:131.5 *sì come quei che stima*. `dep`'s convention
  makes *come* the `advcl` head and *quei* its `obj`; the annex's `nominative` reflects the form,
  not the attachment. Already on record as a left-alone shape in `../case/CORRECTIONS.md`.

**State check.** `skel --check`: **0 hard, 3465 soft** (3633 → 3473 by rule U → 3465 by the
corrections). By kind: `role_mismatch` 516 → **347**, `missing_tuple` 25 → **26** (one retag made
the derivation propose a predicate the artifact does not), `extra_arg` 1649, `missing_arg` 1206,
`extra_tuple` 145 and `membership` 92 all unchanged. `dep --check`: 0 hard, 0 soft. `case --check`: 0 hard. `np --check`: 0/0. `pytest`:
149 passed.

## Layer 3's clitic reconciliation — 3633 → 3635, both at one position (2026-08-02)

Closing Layer 3's stale clitic mentions (see [`../np/CORRECTIONS.md`](../np/CORRECTIONS.md)) moved
this count by **+2**, and both of them are the same position: **purgatorio 20:83**, *poscia c'ha'
il mio sangue a te sì tratto*.

The 94 backfilled `+lemma` mentions and the 6 dropped ones moved nothing — a clitic mention is not
an argument citation, so Layer 5's derivation never reads one. What moved the count was the
**non-clitic** half of the same round: the 2026-08-02 Layer-2 correction had retagged `c'` from
the pronoun `ci` to the conjunction *che* of *poscia che*, and once Layer 3 dropped its `c'` span
and Layer 4 took `c'` `obj` → `mark` (`poscia` `mark` → `advmod`, matching the **27** other
*poscia che* pairs in `dep/`, against the one that reads `mark` + `mark`), the frozen `skel/` row asserting `83.10 tratto obj (83, 2)`
had nothing left to cite:

- `argument (83, 2) for role obj heads no NP/pronoun/predicate` — the membership check.
- `extra_arg: 83.10 obj (83, 2)` — the derivation now yields one `obj` (`sangue`), the artifact two.

**Both flags are correct and neither was closed.** Layer 5's read of this line — `subj` = *sangue*,
`obj` = `c'` — *is* the pre-correction pronoun reading: the subject is the pro-drop *tu* of `ha'`
and `il mio sangue` is the object. Editing the `skel/` row to agree would manufacture the
agreement this layer exists to measure; it is `--fix` work, which is the user's to run. This is the
count moving up because the corpus got better, the same shape as the case annex's first and third
Layer-4 rounds below.

## The `case` annex's Layer-2 round — 3634 → 3633, and Layer 5 confirming two readings (2026-08-02)

The case annex's step 5 finally spent the `morph/` corrections its three earlier steps had
surfaced and parked — 10 hand-verified singletons plus the 58-token comitative family, recorded
in full in [`../morph/CORRECTIONS.md`](../morph/CORRECTIONS.md). **No `skel/` artifact and no
`dep/` row was touched**; the whole delta is Layer 5's deterministic derivation reading a changed
Layer 2.

The net is −1, but the interesting part is that it is **−2 +1**, and both of the closures are
Layer 5's LLM having been right about a position where Layer 2 was wrong:

| | position | violation | why it moved |
|---|---|---|---|
| **closed** | *Purg* 11:137 | `argument (137, 2) for role subj heads no NP/pronoun/predicate` | the LLM read `e'` as the subject of `sostenea`. Layer 2 had it as a form of `essere`, so the argument headed no pronoun. Retagged `egli`/`pronoun`, the violation dissolves |
| **closed** | *Purg* 16:141 | `argument (141, 9) for role obl heads no NP/pronoun/predicate` | the same shape for `vosco`, which Layer 2 had as an `adjective`. Retagged `voi+con`/`pronoun+preposition` |
| **opened** | *Inf* 23:87 | `extra_arg: 87.7 obl (87, 8)` | `seco` is now a pronoun, so `derive_unit` produces an `obl` argument the LLM's skeleton does not carry |

**This is the audit running in the direction it was designed to run.** Layer 5's whole rationale
is that the LLM's skeleton is an independent read, so a divergence can indict a lower layer rather
than the model — Phases 5i, 5n and 5p spent that against Layer 4, and here it lands on Layer 2
instead. Neither `e'` nor `vosco` was found *by* Layer 5; both came off the `case` annex's parked
list. But Layer 5 had already flagged both, which is exactly the corroboration a third read is
for, and it is worth more than the −1.

The single opened violation is the behaviour recorded at length in the three step-4 entries below:
**the soft count measures divergence between two independent reads, not correctness**, so a
correct round can move it either way. 3633 is not a better number than 3634 by one; it is a
different corpus, marginally more correct, whose two reads happen to line up once more often.

**Other layers**: `morph --check` and `dep --check` stay 0/0, `pytest` stays at 138 passed.
`case --check` goes 0 → **25 hard** and `np --check` 3/64 → **5/96**, both of them the mechanical
consequence of a moved Layer 2 and both described in
[`../morph/CORRECTIONS.md`](../morph/CORRECTIONS.md).

## The `case` annex's third Layer-4 round — 3469 → 3634, upward by 165 (2026-08-01)

**The count rose, the round was correct, and the rise was predicted before it was run.** Slice 3
is the population `case.py --stats` lists and `skel --check` does *not* flag: 325 positions where
`dep` and Layer 5 already **agree** and only the `case` column dissents. Correcting `dep` there
necessarily breaks an agreement, so every correct fix creates a divergence rather than closing
one. The previous two entries said so; this one is the measurement.

**124 positions, 167 rows, +165 soft.** `dep --check` stayed 0/0 throughout. Rows and readings in
[`../dep/CORRECTIONS.md`](../dep/CORRECTIONS.md); the partition and the per-position verdicts in
[`../case/CORRECTIONS.md`](../case/CORRECTIONS.md).

### The three slices, side by side

| slice | population | candidates | edited | yield | Layer 5 |
|---|---|---|---|---|---|
| 1 | `obl` × `nominative` impossible pairings | 49 | 10 | 20% | 3550 → **3555**, +5 |
| 2 | contradictions where `skel` sides with `case` | 102 | 81 | 79% | 3555 → **3469**, −86 |
| 3 | contradictions `skel` does not flag | 325 | 124 | 38% | 3469 → **3634**, +165 |

The selector holds on both axes it was built to predict. **Direction**: it is the only thing that
decided the sign, and it decided it three times out of three. **Yield**: 79% inside the
intersection, 38% and 20% outside — a contradiction that breaks a 2-1 tie really is a better
predictor of a Layer-4 defect than one that is merely a disagreement, and this is now measured
over 476 candidates rather than argued.

### Where the 165 went

| kind | added | note |
|---|---|---|
| `role_mismatch` | 133 | the direct consequence: `dep`'s role moved away from the one the LLM asserted |
| `missing_arg` | 16 | mostly the `obj` → `attr` and `obj` → `mark` rows, which remove an argument the derivation used to produce |
| `extra_arg` | 15 | the swaps, where the newly-`nsubj` relative is an argument the LLM did not list |
| `missing_tuple` | 2 | two predicates the derivation no longer reaches |
| `extra_arg` | −1 | one closed |

Almost exactly one new divergence per edited row (165 / 167). That ratio is the mirror image of
slice 2's (86 closed / 92 rows) and it is what the configuration guarantees: in slice 2 the
correction and the LLM's dissent were the same judgment, so the report stopped existing; here the
correction and the LLM's *agreement* were opposed, so a report starts.

### Why this is not a regression, and how to tell the difference

Layer 5's soft count measures divergence between two independent reads. It falls when `dep` moves
toward the LLM and rises when it moves away, and **neither movement is evidence about
correctness** — that comes from the terzina. The guard this round offers is its own control: of
the 325 candidates, **171 were `case`-side errors and were left alone**. Had the round been
optimizing the number in either direction, that is the population it would have touched.

The practical reading for anyone interpreting this number later: **3634 is a worse number and a
better corpus than 3469**, and after slice 3 the divergence that remains at these 124 positions is
a documented disagreement between a corrected Layer 4 and an uncorrected Layer-5 reading — the
same category as the 2832 `extra_arg`/`missing_arg` residue Phase 5 closed its books on, not a
new defect. A future `--fix` pass over the affected units is the only instrument that would move
it, and Phase 5q's measured verdict on `--fix` yield (~0.09-0.11 violations per call) applies
unchanged.

## The `case` annex's second Layer-4 round — 3555 → 3469, −86 (2026-07-31)

**The corrected selector paid out.** Slice 1 spent 49 candidates and the count rose by 5; slice 2
spent 102 and it fell by **86**. The difference is not effort or care — both rounds were
hand-verified against the terzine to the same standard — it is entirely *which two of the three
reads already agreed*, which is what the previous entry predicted and this one measures.

### How the population was selected

Of `case.py --stats`'s 462 contradictions, **138** fall on a position Layer 5 already flags, and
**102** of those are positions where the role the Layer-5 LLM *asserted* sides with `case`
against `dep`. That last set is tier A — the 2-1 configuration, and the only population the
annex's **≈90–100** estimate ever described. It is worth stating how close the estimate landed:
predicted ≈90–100, spent 102 candidates, measured **−86**.

The remaining 36 of the 138 are positions where `skel` flags something else at that token
(`missing_arg` only, or a role pointing away from `case`), and the other 324 contradictions are
positions `skel` does not flag at all. **Those 324 are the slice-1 configuration**: correcting
`dep` there is still correct, and it will not lower this count.

### The delta, by group

| group | candidates | edited | Layer 5 |
|---|---|---|---|
| `dep`=`obj`, `case`=`dative`, `skel`=`obl:a` | 46 | 39 (40 rows) | 3555 → 3518, **−37** |
| `dep`=`obj`, `case`=`nominative`, `skel`=`subj` | 18 | 12 (19 rows) | 3518 → 3499, **−19** |
| `dep`=`nsubj`, `case`=`accusative`, `skel`=`obj` | 25 | 19 (22 rows) | 3499 → 3479, **−20** |
| `dep`=`iobj`/`nsubj` mirror direction | 13 | 11 (11 rows) | 3479 → 3469, **−10** |
| **total** | **102** | **81 positions / 92 rows** | **−86** |

The yield rate is the other measured difference from slice 1: **79%** of tier-A candidates were
Layer-4 errors, against slice 1's 20%. A contradiction where the third read breaks a tie is a
much better predictor of a defect than a contradiction that is merely structurally impossible.

Roughly one violation closes per edited position (86 / 81). That is the expected ratio when the
LLM's dissent and the correction are the same judgment: the divergence that was being reported
simply stops existing. It is not one-to-one because a few edits close two violations (a swap
fixes both halves) and a few convert one violation into another instead of closing it — most
visibly the two edits that side with neither `case` nor `skel` (purgatorio 10:90.3 `obj` → `attr`,
paradiso 10:22.2 `nsubj` → `expl`), which are correct Layer-4 fixes that leave a divergence
standing.

### What this does not license

The count fell because `dep` got more correct at positions where an independent read already said
so — the Phase 5i mechanism, not a new one. **It remains a diagnostic, not the objective.** The
21 tier-A candidates left alone are the guard: in eleven of them `case` is the read that is wrong
(*m'avea 'mmonito* is the annex's own worked example of an accusative, read `dative` by the
column), and editing `dep` toward `case` there would have lowered this number by making Layer 4
worse. The rows are in [`../dep/CORRECTIONS.md`](../dep/CORRECTIONS.md); the point is that a
selector good enough to be worth 86 is still not good enough to apply without opening the terzina.

## The `case` annex's first Layer-4 round — 3550 → 3555, upward (2026-07-31)

**The soft count went up by 5, and the round was still correct.** Recorded here because Layer 5's
count is the thing that moved, and because the reason invalidates the ordering
[`../case/CORRECTIONS.md`](../case/CORRECTIONS.md) gave step 4.

The round is in [`../dep/CORRECTIONS.md`](../dep/CORRECTIONS.md): 11 rows over 10 positions,
drawn from the 49 `obl` × `nominative` impossible pairings, each verified against its terzina and
each justified by a parallel the corpus itself already contains. `dep --check` stayed 0/0.

Per position, from a before/after diff of the violation list:

| position | delta | what happened |
|---|---|---|
| inferno 1:80, purgatorio 25:8 | **−2** | the Layer-5 LLM had already read these the way the edit does |
| inferno 14:80, 16:94, 27:54, purgatorio 5:14 | **+5** | the LLM shares Layer 4's **original** reading |
| purgatorio 4:38 | **+2** | derivation artifact: `elli`:`nsubj` propagates a subject to the `conj` predicate on the next line |
| the three `Ed elli a me:` positions | **0** | the violation changed shape (`missing_arg obl` → `missing_arg subj`); the LLM proposes the pronoun as an argument under neither reading |

### Why a correct round can raise the count

The soft count measures **divergence between two independent reads**, not correctness. It falls
when a Layer-4 fix moves `dep` toward what the Layer-5 LLM already said, and rises when it moves
`dep` away from a reading the LLM happened to share. Both are possible, and which one happens is
a property of **the population the candidates were drawn from**, not of whether the edits were
right.

The impossible pairings are, by construction, positions where `dep` and `skel` **agree** and only
`case` dissents — `case` is the third read precisely because it was authored blind. Correcting
`dep` there breaks an existing agreement, so the count goes up whenever `case` is right and the
other two shared an error. That is the annex doing exactly what
[`../case/README.md`](../case/README.md)'s *Independence* section built it to do.

### What this changes about the remaining slices

[`../case/CORRECTIONS.md`](../case/CORRECTIONS.md) ordered step 4 by "the combination neither layer can be right
about together", predicting the 49 would be the **highest-yield** slice. **That criterion was
wrong**, and this is its measurement: 49 candidates produced 10 edits and *cost* 5 soft
violations.

The **≈90–100** figure in that plan was never derived from impossible pairings. It came from the
Phase 5h/5i population — positions where the Layer-5 LLM **already dissents from** Layer 4, so a
third read that sides with the LLM breaks a 2-1 tie and closes the violation. The correct
selector for slices 2 and 3 is therefore not "do `case` and `dep` contradict" but **"does `skel`
already diverge from `dep` here"**, with `case` used to adjudicate. Measure that intersection
before working the `obj` column's 317.

None of this is an argument for reverting the 11 rows. Layer 4 is more correct than it was, which
is the thing the round is for; the count is a diagnostic, and treating it as the objective is how
a round starts editing artifacts to move a number.

## Layer-2 `nol` mistag closes one soft violation (2026-07-31)

**3551 → 3550.** Not a Layer-5 change: a Layer-2 correction round driven by the
[`case/`](../case/README.md) annex happened to close one of Layer 5's soft residue, and the
delta is recorded here because Layer 5's count is the thing that moved.

*Paradiso* 17:92, "e nol dirai" ("and you will not say it"). Layer 2 read `nol` as
`non+il` / `adverb+article`, treating the clitic `lo` as an article. Layer 5's membership check
consequently reported `argument (92, 4) for role obj heads no NP/pronoun/predicate` — the `obj`
was correct, but the token it cited was tagged as neither a noun phrase nor a pronoun. Correcting
`nol` to `non+lo` / `adverb+pronoun`, which is how the corpus reads the other 37 occurrences of
the form, resolves it with no change to `skel/`.

The mistag was found by [`case/`](../case/README.md)'s scope audit rather than by Layer 5's own
triage, which is the annex behaving as PLAN.md's *Layer 5 doubles as an audit of Layer 4* claim
predicted, one layer further down: a column that reads `pos` as a **count** exercises Layer 2 in
a way no previous consumer did. See [`../morph/CORRECTIONS.md`](../morph/CORRECTIONS.md)'s
*Fused-token component counts, round 2*.

`skel --check` is now **0 hard, 3550 soft**; `morph --check` and `dep --check` stay 0/0. Figures
quoted as 3551 elsewhere in this repo describe the Phase-5 end state and are left as they were.

## Phase 5q: the final `--fix` regeneration pass, and the `ioj` typo (2026-07-29)

Baseline: **0 hard, 3702 soft** (the Phase 5p state), **1702 flagged parse units**. One full
`--fix` pass over all three canticles, run by the user as `make -C skel fix` 3-way parallel,
**≈28 hours wall time**. This is the work item PLAN.md had reserved for the user once the
deterministic route was exhausted, and it is the second (and last) full regeneration round.

| metric | measured |
|---|---|
| units flagged before | 1702 |
| units flagged after | 1644 (**−58 cleared outright**) |
| soft violations removed | **147** (3702 → **3555**, −4.0%) |
| violations removed per LLM call | **≈0.086** |
| units that got *worse* | **0** (Phase 5c's criterion held) |
| cantos touched | 66 — inferno 25, purgatorio 21, paradiso 20 |

Per class:

| kind | before | after | Δ |
|---|---|---|---|
| extra_arg | 1714 | 1639 | −75 (−4.4%) |
| missing_arg | 1238 | 1193 | −45 (−3.6%) |
| role_mismatch | 475 | 459 | −16 (−3.4%) |
| extra_tuple | 155 | 145 | −10 (−6.5%) |
| missing_tuple | 24 | 23 | −1 |
| membership | 94 | 94 | 0 |
| unknown_role | 2 | 2 | 0 |

**The Phase 5e result reproduced, on a residue two Layer-4 correction rounds and nine checker
rules further along.** The yield came in at 0.086 violations per call against 5e's 0.11 — the
same flat rate, on a flagged set composed very differently. Every class moved less than it did in
5e (the three large ones 4.4%/3.6%/3.4% against 5.2%/5.1%/2.9%), so **PLAN.md's stop rule applies
again and no third pass is warranted**: what is left does not respond to regeneration.

The per-unit acceptance count is not recoverable for this round — `skel/skel.log` was left empty
by the parallel invocation — so the table reports the flagged-unit delta (−58) instead, which is
a lower bound on accepted units (a unit can be improved without being cleared).

**The `ioj` typo (−4).** `--stats` had reported `unknown_role 2` since the Phase 4b round; the
two rows were `purgatorio 13:103 dome` and `13:104 rispondesti`, both carrying the role `ioj` —
a plain misspelling of `iobj`, not a reading. Layer 4 tags both arguments (`ti dome`, `mi
rispondesti`) `iobj`, so the correction is mechanical and agrees with the tree. Fixing it removed
the 2 `unknown_role` violations and the 2 `role_mismatch` rows they carried (`'ioj' vs 'obl:a'`):
3555 → **3551**, and **`unknown_role` is now 0 for the first time**.

**Current state**: `make -C skel check` — **0 hard, 3551 soft** (down from 17438 at the first
full-corpus measurement, overall Δ13887, 79.7%; Δ2368 across Phase 5). `make -C dep check` stays
0 hard / 0 soft; `uv run pytest -q` 125 passed.

## Phase 5p: two Layer-4 correction rounds — clausal complements and the `mark` deferrals (2026-07-28)

Baseline: **0 hard, 3702 soft** (from 3712, the Phase 5o state) — −10, no checker code and no
skel artifact touched, zero model calls. Both rounds are Layer-4 edits, the third and fourth the
audit role has produced; the full reading is in [`../dep/CORRECTIONS.md`](../dep/CORRECTIONS.md),
and this section records only what it means for Layer 5.

- **Round A (−7)** — the `ccomp`/`xcomp`-over-`advcl` population Phase 5o left with a verdict but
  no rule. All 35 were re-read with their sub-trees; **6 were retagged** (5 `advcl` → `ccomp`, 1
  → `csubj`, plus one supporting `obj` → `mark` and one `nsubj` → `attr`), and **29 were left**
  because Layer 4 is right. Phase 5o predicted 5-8 plausible cases and named four of them; three
  of those four were retagged and the fourth (`supplica … tanto che possa levarsi`) was left with
  the consecutives, `tanto … che` being the shape Phase 5o had already assigned to Layer 4.
  The 29 residuals are now classified by shape in `dep/CORRECTIONS.md`, so the class does not
  need re-triaging: purposive `per`/`a` + infinitive (10), consecutive `sì`/`tanto … che` (8),
  conditional/temporal adverbials, gerunds after perception or inceptive verbs, and depictive
  adjectives — the last confirmed conventional by a corpus sweep (350 `advcl` heads carry an
  adjective POS).
- **Round B (−3)** — the two multi-edge deferrals of the Phase 5n `mark` round (purgatorio 8:114,
  purgatorio 22:15), closed with the full restructuring (2 and 4 rows) rather than the single-row
  retag 5n was scoped to.

Both rounds kept `dep --check` at **0 hard, 0 soft**. One flagged violation survived by design:
purgatorio 8:114 `quant'` still reports `argument (114, 1) for role subj heads no
NP/pronoun/predicate`, which reads Layer 2's POS (it calls the word a conjunction), not Layer 4's
tree.

By kind, `extra_arg` 1722 → **1714**, `missing_arg` 1239 → **1238** and `role_mismatch` 476 →
**475**. With this the audit route
Phases 5i/5n/5p worked has no measured population left either: every structural bucket the plan
enumerated is closed, and the residual is the reading disagreement the user-run `--fix` pass is
for.

## Checker Phase 5o: rule T — marked adverbial clauses, and the `advcl` verdict (2026-07-28)

Baseline: **0 hard, 3725 soft** (the Phase 5n state). 3725 → **3712** (−13), all `extra_arg`
(1735 → **1722**); every other kind unchanged. Checker-side, zero model calls, zero artifacts
touched. This closes the **last open row** of the `extra_arg` direct-child bucket.

The 51 `advcl` instances were measured before proposing, as the plan required, and they split
into two populations that need opposite treatment:

- **16 give an oblique role** (`obl:per` 8, `obl:a` 4, bare `obl` 3, `obl:senza` 1). These are
  **prepositional infinitive clauses** — "un angel che s'appresta **per venir** verso noi", "**A
  descriver** lor forme più non spargo rime", "Ciascun si fida del beneficio tuo **sanza
  giurarlo**", "discesi tanto sol **per farti** festa". Layer 4 attaches them as `advcl`, outside
  `ARG_DEPRELS`, so `derive_unit` cannot produce them at all; the LLM reads the same edge as an
  oblique and names the preposition literally sitting on it as a `mark`.
- **35 give a complement role** (`ccomp` 18, `xcomp` 14, `subj` 2, `obj` 1) — the
  complement-vs-adjunct distinction, treated separately below.

**Rule T (−13)** (`_marked_adverbial_clause`): a given `obl:<lemma>` whose argument is an `advcl`
child **of the predicate itself** and carries a `mark`/`case` child naming that same preposition.
This is rule S's shape with `advcl` in place of `nmod`, and it inherits rule N's gate — the lemma
must be one the tree itself carries. `_classify_divergence`'s `case_lemmas` map gained a sibling
`marker_lemmas` that also indexes `mark` children, because the preposition of an infinitive
clause is a `mark`, not a `case`; `case_lemmas` is unchanged, so rules L/N/O/S keep their exact
populations (measured: their counts do not move).

**The loose variant was measured at a further −2 and rejected.** Accepting a bare given `obl`
whenever the clause carries any marker admits markers that are not prepositions at all — "infin
ch'el si raggiunge **ove** la tirannia convien che gema" (marker `ove`) and "**quando** a' vapori"
— where nothing in the tree confirms an oblique reading. This is the same narrowing rules N, O
and S apply, and the third time in Phase 5 that measuring the loose variant changed the shipped
rule.

**The `ccomp`/`xcomp` half stays flagged — verdict, not rule.** Read against their terzine, the
35 are mixed in exactly the way the `mark` and clitic populations were, and the split is a
*lexical argument-structure* judgment:

- **Layer 4 is right in the purposive and consecutive cases**, where the LLM over-promotes an
  adjunct to a complement: "i' vegno **per menarvi** a l'altra riva", "non sì **ch'io non
  discernessi** in parte", "e fé sì lor, **che ciascun se ne loda**", "la percossa pianta tanto
  puote, **che de la sua virtute l'aura impregna**".
- **Layer 4 looks wrong in the indirect questions and true complements**: "nota … **come natura
  lo suo corso prende**", "Ch'avete tu e 'l tuo padre sofferto … **che 'l giardin de lo 'mperio
  sia diserto**", "supplica a te … **che possa … levarsi**", "mostrommi l'alma … **qual era tra i
  cantor del cielo artista**".

  The boundary between the two is genuinely fine, which is the argument against ruling on it: in
  "dimmi, **se tu sai**, perché tai crolli diè" the `se` clause is a parenthetical conditional and
  Layer 4's `advcl` is right, while in the superficially identical "Ricorditi, lettor, **se** mai
  … ti colse nebbia" it heads the recalled content. Only a per-case reading separates them.

Separating the two requires knowing which matrix verbs take clausal complements, i.e. the verb
lexicon Phase 5k refused for the predicative-PP half of the clausal cluster. The matrix-lemma
distribution confirms no cheaper gate exists: after splitting off the copular/aspectual verbs
(8 instances), the remaining 43 are spread over **37 distinct lemmas**, 33 of them appearing
exactly once — not a coherent population. The honest residual route is Phase 5i/5n's, a
hand-verified `dep/` correction round over the handful of plausible complement cases (**5-8** of
the 35 on this reading, each needing the sub-tree check 5n established); it is recorded as an
option, not opened here, and is worth at most −8. **It ran as Phase 5p** — 6 retagged, −7 with
its supporting rows.

Four tests in `tests/test_skel.py` (accepted; non-preposition marker still flagged; a given
`xcomp` over an `advcl` still flagged; an `advcl` of another verb still flagged), 125 passing.

**State at this phase**: `make -C skel check` — **0 hard, 3712 soft** (down from 17438 at the
first full-corpus measurement, overall Δ13726, 78.7%; Δ2207 across Phase 5). By kind: `extra_arg`
1722, `missing_arg` 1239, `role_mismatch` 476, `extra_tuple` 155, `membership` 94,
`missing_tuple` 24, `unknown_role` 2.

## Phase 5n: the `mark` bucket, resolved as a Layer-4 correction (2026-07-28)

Baseline: **0 hard, 3746 soft** (the Phase 5m state). 3746 → **3725** (−21). Zero model calls,
zero checker code changed, zero skel artifacts touched — the whole round is 22 retagged rows in
`dep/`, and the full reading of all 35 instances lives in
[`../dep/CORRECTIONS.md`](../dep/CORRECTIONS.md).

This is the second correction Layer 5's audit role produced (Phase 5i was the first), and it
closes the last **open** row of the `extra_arg` direct-child triage table apart from `advcl`.
The population: Layer 4 tags a relative or interrogative word `mark` on a predicate, and the
LLM — which never sees that parse — cites the same token as an argument of it.

**Why a correction and not a rule.** All 35 were read against their terzine, and the population
is mixed the way the clitic-case one was: 22 are Layer-4 mistags (the word fills a real argument
slot — `poi mi farai, **quantunque** vorrai, fretta`; `per la ragion **che** di'`; `**qual**
diverrebbe Iove`), 11 are cases where Layer 4 is right and the LLM misreads (complex
subordinators `secondo che`, comparative and consecutive `che`, the idiomatic concessives `qual
che si sia` / `che che li appaia`), and 2 need a multi-edge restructuring this round is not
scoped to. **No gate separates them.** Layer 2's POS is not usable either — it calls most of
these words "conjunction", including the ones that are plainly relative pronouns. A blanket
`mark` exemption would have swallowed the 11 correct Layer-4 tags along with the mistags, which
is exactly what PLAN.md's *What is deliberately not proposed* warned against.

**Measured.** `dep --check` stays **0 hard, 0 soft**; `pytest` 121 passed. All 22 retags closed
their `extra_arg` violation; the net is −21 rather than −22 because paradiso 27:79 (`Da l'ora
**ch'**ïo avea guardato prima`) **converts** instead of closing — `ch'` is a temporal oblique,
which is what the retag says, but the LLM had cited it as an `obj`, so the divergence is now
reported as a `role_mismatch` against a reading that is still wrong. That is the checker
classifying more precisely rather than the correction failing, the same sign rule C gave in
Phase 5a.

**Current state**: `make -C skel check` — **0 hard, 3725 soft** (down from 17438 at the first
full-corpus measurement, overall Δ13713, 78.6%; Δ2194 across Phase 5). By kind: `extra_arg`
1735, `missing_arg` 1239, `role_mismatch` 476, `extra_tuple` 155, `membership` 94,
`missing_tuple` 24, `unknown_role` 2.

## Checker Phase 5m: rule S — `nmod` complements of the predicate (2026-07-28)

Baseline: **0 hard, 3808 soft** (the Phase 5l state). 3808 → **3746** (−62), all `extra_arg`
(1819 → **1757**); every other kind unchanged. Checker-side, zero model calls, zero artifacts
touched. This is the second cut into the `extra_arg` **direct-child** bucket Phase 5l identified
as the most promising remaining structural population.

Re-triage of that bucket (324 after rule R), by the deprel `derive_unit`'s map omits:

| deprel | count | | deprel | count |
|---|---|---|---|---|
| `expl` | 87 | | `mark` | 35 |
| `nmod` | 62 | | `cop` | 9 |
| `advcl` | 51 | | `conj` | 8 |
| `advmod` | 50 | | `vocative` | 7 |
| | | | tail (`case`, `aux`, …) | 15 |

**Rule S (−62)** (`_nmod_complement_of_predicate`): a given `obl:<lemma>` whose argument is an
`nmod` child **of the predicate itself** and carries a `case` child naming that same preposition.
Rule D already accepts this shape one edge further out (an `nmod` of one of the predicate's
*derived arguments*, "ha bisogno **di te**"); this is the direct-child case, which `derive_unit`
cannot produce because `nmod` is outside `ARG_DEPRELS`.

The population is completely uniform on the gate — **all 62** `nmod` direct-child `extra_arg`
instances are `obl:<lemma>` with a same-lemma `case` child, so the strict and loose variants
return the identical set, the same evidence rule L's two variants gave. By the predicate's POS it
splits into two constructions, both of which leave the tree uncontradicted:

- **58 nominal or adjectival predicates** (noun 32, adjective 26): "intese cose che furon
  *cagione* **di sua vittoria**", "di quanto *mal* fu matre", "*Oppresso* **di stupore**", "di
  sospetto *pieno* e d'ira crudo". UD correctly attaches the PP complement of a predicate nominal
  as `nmod`, and it is an argument of the predication all the same.
- **4 verbal predicates** where Layer 4 wrote `nmod` for a plain oblique: "nel *fermar* **tra Dio
  e l'omo** il patto", "*mischiato* **di lagrime**".

**Shipped ungated on the predicate's POS**, for the reason measured for rule M's proposed gate:
the two shapes are both correct readings, so a gate there would separate the wrong thing rather
than sound from unsound. The lemma match is the structural gate — the LLM names the preposition
literally present on that edge, and naming a different one stays flagged.

Three tests in `tests/test_skel.py` (accepted; different `case` lemma still flagged; `nmod` of a
non-predicate head still flagged), 121 passing.

**State at this phase**: `make -C skel check` — **0 hard, 3746 soft** (down from 17438 at the first
full-corpus measurement, overall Δ13692, 78.5%; Δ2173 across Phase 5). By kind: `extra_arg`
1757, `missing_arg` 1239, `role_mismatch` 475, `extra_tuple` 155, `membership` 94,
`missing_tuple` 24, `unknown_role` 2.

## Checker Phase 5l: rule R — predicative adjectives attached as `advmod` (2026-07-28)

Baseline: **0 hard, 3876 soft** (the Phase 5k state). 3876 → **3808** (−68), all `extra_arg`
(1887 → **1819**); every other kind unchanged. Checker-side, zero model calls, zero artifacts
touched. **This is the first cut into `extra_arg`/`missing_arg` since Phase 5b.**

The re-triage of the two big classes started as this plan prescribed — classifying every
instance by how the cited argument reaches the predicate in the dep tree:

| `extra_arg` (1887) | count | | `missing_arg` (1239) | count |
|---|---|---|---|---|
| unrelated | 659 | | direct child | 1116 |
| descendant, depth 2 | 398 | | unrelated | 123 |
| direct child | 392 | | | |
| predicate is a descendant of the argument | 268 | | | |
| pro-drop ∅ | 131 | | | |
| descendant, depth ≥ 3 | 39 | | | |

`missing_arg` is now **90% direct-child** — the LLM omitting an argument the tree carries on the
very edge `derive_unit` reads. That is LLM incompleteness, not a checker artifact, and no
structural rule can absorb it. (The pairing hypothesis was tested and is small: only **70**
`extra_arg`/`missing_arg` pairs on the same predicate cite two tokens of the same NP span or two
adjacent tokens — "Pape/Satàn", "Anastasio/papa", "Caron/dimonio" — so citation-token drift is
not what these classes are made of.)

**Rule R (−68)** (`_predicative_advmod`): a given `xcomp` whose argument is an **adjective**
attached to that same predicate as `advmod` — "e io etterno **duro**", "dinanzi polveroso va
**superbo**", "il primo cerchio è **tutto**", "tal mi **fec'** io". These are the predicative
complements rule M already covers, which Layer 4 attached adverbially instead; `derive_unit`
only reads `ARG_DEPRELS`, so it can produce no argument for them at all. The whole direct-child
`advmod` population is 118, and the rule takes the 68 that are adjectives.

**The adjective gate was measured against its alternatives and is what keeps this from being a
blanket `advmod` exemption**: the same shape with an **adverb** argument (17 — "che fu nel
cominciar cotanto **tosta**", "m'è **tardi**", "lungi **fia** dal becco l'erba") is Layer 2
calling the word an adverb, which leaves the predicative reading genuinely undecided, so it
stays flagged; so does everything with a non-`xcomp` role (33, mostly `obl`/`obj` over a
quantifier adverb — "guardommi **un poco**", "ebbi **assai**"). This is the split Phase 5b
predicted but did not have the POS breakdown to make: it left the "`xcomp`-over-`advmod` half"
whole, and it divides cleanly.

Three tests in `tests/test_skel.py` (accepted; adverb POS still flagged; non-`xcomp` role still
flagged), 118 passing.

**Current state**: `make -C skel check` — **0 hard, 3808 soft** (down from 17438 at the first
full-corpus measurement, overall Δ13630, 78.2%; Δ2111 across Phase 5). By kind: `extra_arg`
1819, `missing_arg` 1239, `role_mismatch` 475, `extra_tuple` 155, `membership` 94,
`missing_tuple` 24, `unknown_role` 2.

## Checker Phase 5k: rules P and Q — the clausal-complement cluster (2026-07-28)

Baseline: **0 hard, 3924 soft** (the Phase 5j state). 3924 → **3876** (−48), all
`role_mismatch` (523 → **475**); every other kind unchanged. Checker-side, zero model calls,
zero artifacts touched.

The `xcomp`/`ccomp`/`obj` cluster this plan queued was enumerated by (given role, derived role,
the argument's dep deprel, its Layer-2 POS), 173 instances. Two sub-classes are mechanical; the
rest are not, and are left alone.

**Rule P — `ccomp` against `xcomp`, either direction (−22)** (`_clausal_complement_flavor`).
Both labels say *clausal complement of this predicate*; they differ only on whether the
complement has its own subject or takes one by control. Layer 4 makes that judgment
inconsistently on the same construction — "Fa che tu **m'abbracce**" is tagged `xcomp` with an
overt "tu" — so neither side is more informative. This is therefore a **label equivalence**, the
move `_ROLE_CANON` already makes for `attr`/`xcomp`, and it is the one rule in Phase 5 that is
deliberately two-directional: the asymmetry argument L/M/N/O/Q rest on ("one side names
something the tree makes explicit") does not apply when both labels name the same tree edge.
Kept local to the divergence check, so `ccomp` and `xcomp` remain distinct in the artifact and
in the role vocabulary. Distribution: 21 given `ccomp` / derived `xcomp`, 1 the other way.

**Rule Q — given `ccomp` against derived `obj`/`subj` with a verb argument (−25)**
(`_clausal_object`). Layer 4 attaches the complement clause's head verb straight to the matrix
predicate as `obj`/`nsubj` — "or mi concedi ch'io **sappia**", "dimmi se tu **sai**", "avvien
che poi nel maginare **abborri**" — and `derive_unit` reads the deprel alone, so a whole clause
is reported as a direct argument. Same shape as rule N: the LLM's label is strictly more
informative, and one-directional (a given `obj`/`subj` against a derived `ccomp` means the tree
*did* carry the explicit deprel and the LLM flattened it — 4 instances, still flagged).

**The ungated variant was measured: dropping the verb-POS gate would admit exactly one more
instance, and it is an error** — inferno 18:117 "che non parëa s'era **laico** o cherco", where
the cited argument is a noun. Small, but it is the difference between a structural claim and a
blanket exemption, so the gate stays.

**Deliberately not proposed: the predicative-PP half of the cluster (≈55).** Given `xcomp`
against a derived `obl`/`obl:<lemma>` whose argument is an `obl` dependent — "sta **come torre**
ferma", "fu **di grado** maggior", "son io medesmo **di questi cotai**". The LLM reads the PP as
the copula's predicative complement, which is a real reading, but so is the tree's: both sides
make a claim about the same edge, and separating the copular cases would need a verb lexicon
(`essere`/`stare`/`parere`/`sembrare`), which this project has consistently refused in favour of
structural checks. Left flagged.

Four tests in `tests/test_skel.py` (rule P both directions, rule Q accepted, the verb-POS gate,
the flattened-`ccomp` mirror), 115 passing.

**Current state**: `make -C skel check` — **0 hard, 3876 soft** (down from 17438 at the first
full-corpus measurement, overall Δ13562, 77.8%; Δ2043 across Phase 5). By kind: `extra_arg`
1887, `missing_arg` 1239, `role_mismatch` 475, `extra_tuple` 155, `membership` 94,
`missing_tuple` 24, `unknown_role` 2.

## Checker Phase 5j: preposition-lemma normalization + rule O (2026-07-28)

Baseline: **0 hard, 4042 soft** (the Phase 5i state). 4042 → **3924** (−118), all
`role_mismatch` (641 → **523**); every other kind unchanged. Checker-side, zero model calls,
zero artifacts touched.

The 140 remaining `obl:<lemma>` vs `obl:<other>` mismatches were enumerated with each argument's
`case`-child words beside them, which split them into two mechanical classes and a small
residue.

**1. Same preposition, different spelling (−57).** `_PREP_LEMMA_NORM` — Phase 1's normalization
table, until now eight entries hand-picked from the pair list — was rebuilt from what the corpus
actually contains: every `case`-child word form in `dep/`, cross-checked against the pair table.
Three kinds of key, all spellings of their value, never a different preposition:

- **preposition+article contractions** (`nel`/`ne`/`ne'` → `in`, `al`/`ai`/`a'` → `a`, `dal` →
  `da`, `del`/`de'` → `di`, `sul` → `su`, `pel` → `per`) — the LLM names the contraction it sees
  ("scendemmo **ne la** quarta lacca" → `obl:ne`), while Layer 2 lemmatizes it as `in+il` and
  `_prep_lemma` keeps the first part, so `derive_unit` says `obl:in`. `col`/`coi` were already
  in the table for exactly this reason; this generalizes them.
- **archaic/apocopated spellings** (`sovr'`/`sovresso` → `sopra`, `ver'` → `verso`, `'nnanzi` →
  `innanzi`, `fin`/`infin`/`insin` → `fino`, `contr'` → `contro`, `tr'`/`fra`/`intra` → `tra`,
  `incontr'` → `incontra`, `lunghesso` → `lungo`, `apo` → `appresso`).
- **the `in+verso` univerbation family** (`inver`, `inver'`, `'nver'`, `inverso`, `invero` →
  `in`) — Layer 2 analyses `inver'` as the compound `in+verso` (21 of the 30 occurrences), so
  `_prep_lemma`'s split reports `in`. Normalizing onto `in` rather than onto `verso` follows
  this table's stated convention (canonicalize to the derived side), and it collapses the pair
  in both directions at once: `obl:inver` vs `obl:in` (5), `obl:inver'` vs `obl:in` (4),
  `obl:in` vs `obl:invero` (2), `obl:inverso` vs `obl:in` (2).

**2. Rule O — co-present prepositions (−61)** (`_co_present_preposition`): two different
`obl:<lemma>` labels for the same argument where the **given** lemma is one of that argument's
own `case` children. Italian stacks prepositions and the dep tree attaches both markers to the
nominal — "**in su** le porte", "dietro **a** noi", "dentro **a** lo specchio", "infino **al**
giro quinto" — while `derive_unit` reports whichever it reaches first. The LLM naming the other
one is a choice between two markers that are both in the tree, not a contradiction of it. Same
shape and the same one-directional gate as rules L/M/N.

**The negative (two-directional) variant was measured and rejected: it would remove 30 more, on
much weaker evidence.** In the mirror direction — the *derived* lemma is the argument's `case`
child, the given one is not — the given preposition is a `case` marker attached **elsewhere** in
the unit in 17 instances ("in su la ripa", where Layer 4 attached only `su` to `ripa`), an
`advmod`/`obl` token in 7, and **absent from the unit entirely** in 5. The first group is a
Layer-4 inconsistency (multiword prepositions sometimes get both `case` children, sometimes
one), the last is plainly the LLM inventing a preposition, and a single gate cannot tell them
apart — so the mirror stays flagged, as it does for L, M and N. What is left after rule O is 3
instances where neither side's preposition is anywhere near the argument.

Five tests in `tests/test_skel.py` (`test_normalize_prep_lemma_contractions_and_variants`,
`test_classify_divergence_contraction_lemma_is_not_a_divergence`, rule O accepted / mirror
flagged / both-sides-oblique gate), 111 passing.

**Current state**: `make -C skel check` — **0 hard, 3924 soft** (down from 17438 at the first
full-corpus measurement, overall Δ13514, 77.5%; Δ1995 across Phase 5). By kind: `extra_arg`
1887, `missing_arg` 1239, `role_mismatch` 523, `extra_tuple` 155, `membership` 94,
`missing_tuple` 24, `unknown_role` 2.

## Phase 5i: the clitic-case question, resolved as a Layer-4 correction (2026-07-28)

Baseline: **0 hard, 4042 soft** (from the Phase 5h state of 4068, −26, all `role_mismatch`:
667 → **641**). **No checker code changed and no skel artifact was touched** — the 26 came from
correcting Layer 4, which is what Phase 5h filed this class as.

Phase 5h left 97 instances where the LLM labels a clitic `obl:a`/`obl:di` against Layer 4's
`obj`, and argued they could not be a checker rule because both sides make a case claim about
the same token. Reading them confirmed that, and sharpened it: the population is genuinely
**mixed**. Most are datives Layer 4 mistagged (`mi pesa`, `ti noccia`, `li convien fuggire`,
`ha tolto loro`), but some are plain accusatives the LLM got wrong (`m'avea 'mmonito`,
`ti priego`) — so no blanket routing was possible either.

**What decides a subset is structural, and needs no case feature.** In 30 of the 97 the
predicate carries a *second* `obj` child in the dep tree. UD allows at most one `obj` per
predicate, so the tree contradicts itself independently of the LLM, and the non-clitic object is
the direct one. Those 30 were hand-read against their terzine, 4 rejected, and the remaining 26
retagged in `dep/` (22 → `iobj`, 4 → `obl` for partitive `ne`); see
[`../dep/CORRECTIONS.md`](../dep/CORRECTIONS.md) for the full list and the rejections. `dep
--check` stays **0 hard, 0 soft**; every retagged row closed its Layer-5 divergence, because
Phase 1 canonicalizes `iobj` → `obl:a` and rule L reconciles bare derived `obl` with a given
`obl:<lemma>`.

**This is the first Layer-4 correction Layer 5 produced**, which is the audit role the layer was
built for (see the README's *What it does*): a divergence between two independent readings
located a real mis-parse in the frozen dependency artifact, not just an LLM slip.

**Still open** (unchanged in count, now with a measured reason): the other **67** — no second
`obj`, so nothing structural decides them — and the **30** mirror-direction instances (`iobj`
given by Layer 4, `obj` by the LLM: `mi bagna`, `mi tormenta`, `ti conforta`, `lui non aita`).
Several of the mirror cases look like Layer-4 datives over real accusatives, i.e. errors running
the other way. Deciding either group needs a Layer-2 case feature or a clitic lexicon.

**A wider Layer-4 finding**, recorded in `dep/CORRECTIONS.md` and not acted on: **231**
predicates corpus-wide carry two or more `obj` children (84 with a clitic, 147 without —
flattened coordinations and object complements).

**Current state**: `make -C skel check` — **0 hard, 4042 soft** (down from 17438 at the first
full-corpus measurement, overall Δ13396, 76.8%; Δ1877 across Phase 5).

## Checker Phase 5h: rule N — case-marked objects, and the clitic-case finding (2026-07-28)

Baseline: **0 hard, 4097 soft** (the Phase 5g state). 4097 → **4068** (−29), all `role_mismatch`
(696 → **667**). The small number is the point: the class it came from is 148 instances, and the
measurement split it into two populations that are *not* the same phenomenon.

The `obl:<lemma>` vs `obj`/`subj` pairs (148 given-side, 45 in the mirror direction), classified
by what the dep tree says about the argument:

| bucket | count | reading |
|---|---|---|
| argument has a `case` child naming **the same** preposition | **29** | notation split — **accepted (rule N)** |
| argument has **no** `case` child, and is a **pronoun** | **97** | clitic case — see below |
| argument has a `case` child naming a **different** preposition | 12 | real disagreement — stays flagged |
| argument has no `case` child and is a noun/adjective/article | 10 | stays flagged |

**Rule N (−29)**: the argument carries an explicit `case` child, but Layer 4 attached it as
`obj`/`nsubj`, and `derive_unit` takes the role from the deprel alone — so the preposition
sitting in the tree is dropped ("curan **di te**", "contastare **a Ruberto**", "gridavano «**A
Filippo** Argenti!»", "pigliando più **de la** dolente ripa"). The LLM reads the preposition that
is there; nothing is contradicted. Same one-directional shape as rules L and M (given
`obj`/`subj` vs derived `obl:<lemma>` means the LLM *dropped* an explicit preposition — flagged),
and requiring the *same* lemma is what keeps it narrow: the 12 different-lemma instances stay
flagged. Implemented as `_case_marked_object`; `case_children` from rule L became `case_lemmas`
(position → normalized `case`-child lemmas) to serve both.

**The 97 pronominal cases are deliberately not accepted, and they are a Layer-4 finding.** They
are clitics — 84 of them `obl:a` — where the LLM names a case the token carries morphologically
and the tree cannot express: "**mi** pesa", "non **ti** noccia", "**li** convien fuggire", "fa
che **gliel'** accocchi", "**n'**accorgo", "**ne** portò un lacerto". Layer 4 tags them `obj`.
Unlike rules L/M/N, **both sides here make a case claim about the same token**, so the
"strictly more informative" argument does not apply — and the mirror direction confirms it is a
real disagreement rather than a convention split: in 30 further instances Layer 4 tags the clitic
`iobj` (which Phase 1 canonicalizes to `obl:a`) and the *LLM* says `obj`. The two sides disagree
about clitic case in **both** directions, on the same syncretic pronoun set (`mi`/`ti`/`ci`/`vi`/
`li`/`ne`, accusative and dative alike in Italian).

That makes it a Layer-2/Layer-4 question, not a checker rule: if "mi pesa" is a dative, Layer 4's
`obj` is a mistag, and the correction belongs in [`dep/CORRECTIONS.md`](../dep/CORRECTIONS.md)
under the same measure-then-freeze discipline Phase 5d used to *reject* the `expl` hypothesis. No
correction is opened here — Layer 2 records no case feature (`MorphRow` has gender/number/person,
not case), so deciding it needs either that feature or a clitic lexicon, and both are larger
moves than this round. **Filed as the open question for the next round.**

**Current state**: `make -C skel check` — **0 hard, 4068 soft** (down from 17438 at the first
full-corpus measurement, overall Δ13370, 76.7%; Δ1851 across Phase 5).

## Checker Phase 5g: rule M — given `xcomp` vs derived `obj`/`subj` (2026-07-28)

Baseline: **0 hard, 4327 soft** (the Phase 5f state). One rule, no LLM call, no artifact touched:
4327 → **4097** (−230, −5.3%), all of it `role_mismatch` (926 → **696**, −24.8%).

**The gate this plan proposed was measured and abandoned, in both variants.** PLAN.md's candidate
was to accept the pair only in the object-complement configuration — the predicate carrying
*another* `obj`/`subj` argument. Measured full-corpus: the **given-side** gate admits **227 of
230** (98.7%), so it is the ungated rule under another name and discriminates nothing; the
**derived-side** gate admits **163** (71%). The derived-side variant looked principled — of the
73 adjective arguments 63 pass it, against 60 of 100 nouns — until the excluded 67 were read:

```
  gated:    "tal mi fece la bestia"   "li chiama orbi"      "hanno Italia morta"
            "mi chiamaste Ciacco"     "si fa vino"          "chi tu se'"
  excluded: "non son torri"           "mi parve una lontra"  "fummo Frati godenti"
            "è tempo da scostarsi"    "sarà maraviglia"      "ben son Beatrice"
```

The excluded set is not a different phenomenon; it is the **copular** half of the same one. The
gate separates object complements from predicate nominals, which is not the distinction the rule
turns on, and leaving the second group flagged would keep 67 known-correct readings in the
violation count. So the rule ships ungated.

**Why the pair is a notation split**: UD has no relation for secondary predication. An object
complement is attached as a plain `obj`, and a copular predicate nominal as `nsubj`, so
`derive_unit` can only ever report the *attachment* — the LLM names the same token's *predicative
function*. This is exactly the split Phase 1 already canonicalizes `attr` → `xcomp` for, one step
further. Both descriptions are true of the same token and nothing in the dep tree contradicts the
LLM, the same "strictly more informative" argument as Rule L.

**One-directional, deliberately.** The mirror pairs (given `obj`/`subj` vs derived `xcomp` — 15
and 22) stay flagged: there the dep tree *did* carry an explicit `xcomp`/`ccomp` deprel and the
LLM contradicted it. Same asymmetry as `_safe_role_repair` and Rule L.

Evidence and its limits: roughly 110 of the 230 were read by hand across every POS bucket
(adjective 73, noun 100, pronoun 31, verb 11). No case was found where the LLM's `xcomp` labels a
plain direct object — the residual doubt is a handful (~3%) of arguable readings such as
"n'andavam l'un dinanzi" and "Femmina è nata", where the token is defensibly the subject. The
`verb`-argument cases are causative/modal infinitives ("perder lo face", "pianger non lascia"),
where `xcomp` is if anything the better UD label.

Implemented as `_predicative_complement` (`dante_corpus/skel.py`), consulted from the same
`elif grole != drole:` branch as Rule L. Three tests: object complement accepted, copular
predicate nominal accepted, mirror direction still flagged.

**Current state**: `make -C skel check` — **0 hard, 4097 soft** (down from 17438 at the first
full-corpus measurement, overall Δ13341, 76.5%; Δ1822 across Phase 5).

## Checker Phase 5f: rule L — `obl:<lemma>` given vs bare `obl` derived (2026-07-28)

Baseline: **0 hard, 4615 soft** (the Phase 5e state). One rule, measured corpus-wide before
implementing, **no LLM call and no artifact touched**: 4615 → **4327** (−288, −6.2%), all of it
`role_mismatch` (1214 → **926**, −23.7%).

`derive_unit` emits a bare `obl` in exactly one situation: the argument has no `case` child
naming the preposition (the `obl`/`obl:agent` branch of its argument loop builds the
lemma-qualified form from that lookup). In **all 288** instances of this pair that condition
holds — the strict variant of the rule (gated on the absence of a `case` child) and the loose one
(ungated) return the identical set, which is itself the evidence that the two sides are not
disagreeing. The preposition is fused into the token: a clitic dative (`che nel lago del cor
**m'**era durata` — derived `obl`, given `obl:a`) or a preposition+article contraction. The LLM's
label is therefore **strictly more informative, not a divergence** — the same argument the Phase 2
authority model makes for pro-drop subjects, and the mirror of `--repair`'s `role_label` rule
(`_safe_role_repair`), which rewrites the *opposite* direction, given bare `obl` → derived
`obl:<lemma>`, precisely because *there* the dep tree is explicit.

Implemented checker-side as `_oblique_lemma_refinement` (`dante_corpus/skel.py`), consulted in
the `elif grole != drole:` branch of `_classify_divergence`. Deliberately **not** a `--repair`
rule: the derivation is the less informative side here, so there is nothing to rewrite the
artifact towards. Three tests, per the file's per-rule convention: the accepted case, a
cross-lemma pair (`obl:a` vs `obl:di`, still flagged — that disagreement is real), and the
defensive negative where the argument *does* carry a `case` child (still flagged: that
combination means the derivation had the preposition and dropped it).

This single deterministic rule removed **more than the entire Phase 5e `--fix` pass** (288 vs
231) at zero model calls — the third time in Phase 5 that measuring a class beat regenerating it.

**Current state**: `make -C skel check` — **0 hard, 4327 soft** (down from 17438 at the first
full-corpus measurement, overall Δ13111, 75.2%; Δ1592 across Phase 5).

## Phase 5e: full-corpus `--fix` regeneration round (2026-07-28)

Baseline: **0 hard, 4846 soft** (the Phase 5b state), 2037 flagged parse units. One full pass,
all three canticles, under the Phase 5c acceptance criterion. This is the first `--fix` round
run on a residue the deterministic phases had already cleared of structurally unfixable units.

| metric | measured |
|---|---|
| units attempted | 2037 |
| units accepted (rewritten) | **178 (8.7%)** |
| units that got *worse* | **0** |
| soft violations removed | **231** (4846 → **4615**, −4.8%) |
| violations removed per accepted unit | 1.3 |
| cantos touched | 85 |
| accepted per canticle | inferno 56, purgatorio 58, paradiso 64 |

Per class:

| kind | before | after | Δ |
|---|---|---|---|
| extra_arg | 1991 | 1887 | −104 (−5.2%) |
| missing_arg | 1305 | 1239 | −66 (−5.1%) |
| role_mismatch | 1250 | 1214 | −36 (−2.9%) |
| extra_tuple | 176 | 155 | −21 (−11.9%) |
| missing_tuple | 26 | 24 | −2 |
| membership | 96 | 94 | −2 |
| unknown_role | 2 | 2 | 0 |

**The expected rise in success rate did not materialize.** PLAN.md predicted the rate would come
in above the pre-Phase-5 10.5%, since 5a/5b had removed from the denominator precisely the units
regeneration could never fix. It came in at **8.7%** instead — statistically indistinguishable
from the earlier figure (which was itself 2 of 19 units on a local model), so the honest reading
is that the method's yield is **flat at roughly 0.11 violations per LLM call**, independent of
how the flagged set is composed. Regeneration is not the lever that closes the remaining gap.

Phase 5c's tightened acceptance held: **no unit regressed**, and `unknown_role` stayed at 2 —
the failure mode that motivated the rule did not recur.

**PLAN.md's stop rule therefore applies: no second pass.** No class moved more than 11.9%, and
the three large ones moved 5.2%/5.1%/2.9% — a class that barely moves after a full pass is
evidence of a checker-side rule mismatch, not of an LLM error awaiting another attempt.
`role_mismatch` moved least while sitting 99.9% on edges *both* sides see, and its top pairs are
strikingly systematic:

```
'xcomp' vs 'obj'   170    'obl:a' vs 'obl'  94    'obl:a' vs 'obj'  92
'obl:di' vs 'obl'   84    'obj'  vs 'subj'  81    'subj'  vs 'obj'  67
'xcomp' vs 'subj'   60
```

The `xcomp`/`obj` and `obl:<lemma>`/bare-`obl` pairs in particular look like the same kind of
labeling-convention split Phase 1 and Phase 5a/5b already normalized elsewhere (a nominalized
infinitive read as a clausal complement; a preposition the dep tree attaches without a `case`
child) — they should be measured before any further model calls. That is the next round.

**Current state**: `make -C skel check` — **0 hard, 4615 soft** (down from 17438 at the first
full-corpus measurement, overall Δ12823, 73.5%; Δ1304 across Phase 5). The artifacts changed
this round are the 85 cantos listed above — the first `skel/*/` change since the Phase 4b round.

## Checker Phase 5b/5d: re-triage of the reduced set (2026-07-26)

Baseline: **0 hard, 5105 soft** (the Phase 5a state). Every surviving violation was re-classified
by its dep-tree context — for `extra_arg`/`missing_arg`/`role_mismatch`, how the cited argument
attaches under the predicate (direct child + deprel, descendant depth, unrelated, ∅); for
`extra_tuple`/`missing_tuple`, the predicate's own deprel and Layer-2 POS. Three mechanical
classes fell out, all measured corpus-wide before implementing, and all landing additively
(5105 → 5012 → 5006 → 4945 → **4846**, exactly the sum of the three measured sizes):

1. **Coordinating conjunctions promoted to predicates** (`derive_unit` rule 1, −93):
   `missing_tuple` was **74% a single pattern** — a line-initial `E`/`Ed`/`Ma` that Layer 4
   attaches to the previous clause head with deprel `conj` ("E 'l mio buon duca, che già li er'
   al petto"), which `derive_unit`'s conj-promotion then made a predicate. A coordinating
   conjunction is a function word and can never be a predicate: this is a **derivation
   over-generation**, not an LLM omission — the LLM was right to not propose it. Gated on the
   Layer-2 POS being `conjunction`, so gapped predicates of other POS (the `conj`/`noun` and
   `conj`/`pronoun` cases, real ellipsis) stay derived. `missing_tuple` **100 → 26**.
2. **Copula/auxiliary listed as the predicate** (`_classify_divergence`, `_aux_head`, −99):
   "Molti *son* li animali", "se tu *vorrai* salire" — the LLM names the copula or modal as the
   predicate where `derive_unit`, following UD, names the lexical head it attaches to. In
   essentially every instance the LLM lists the head **as well**, so this is the same
   double-listing the Phase 4a `attr`/`xcomp` whitelist already suppresses, and it is gated the
   same way: only when the `aux`/`aux:pass`/`cop` token's head is itself a derived predicate.
   `extra_tuple` **275 → 176**, with `extra_arg`/`missing_arg` untouched (an `extra_tuple`
   predicate's argument rows were never compared, so nothing stops being checked).
3. **Adverbial obliques** (`_adverbial_oblique`, −67): `obl`/`obl:<prep>` citing an adverb that
   hangs off the same predicate as `advmod` (`quivi`, `là`, `dinanzi`) — 67% of all remaining
   bare-`obl` `extra_arg`. `derive_unit` builds obliques only from `obl` deprel children, so it
   structurally can't emit one; the membership soft check **already** accepts exactly these
   tokens as `obl` arguments for exactly this reason (Pilot-build item 3), so this closes an
   inconsistency between the two checks rather than adding an exemption.

Rejected by the same measurement — recorded because each disproves a plausible rule:

| candidate | measured |
|---|---|
| remap every given `aux`/`cop` predicate onto its head (instead of suppressing) | **−6** ❌ — merging the two argument sets adds `extra_arg` +19 as fast as it removes tuples |
| remap only when the head is derived but *not* also listed by the LLM | −2 ❌ — the pattern is double-listing, so this variant almost never fires |

**Phase 5d (route Layer-4 errors back to Layer 4): the hypothesis is disproved.** PLAN.md
expected the `extra_arg` cases citing an `expl` child (107, counting `expl:pass`) to be `dep`
mistags. Enumerating them: **99 of 107** cite a clitic — `si` 30, `mi` 27, `s'` 20, `ti` 7, `m'`
7, `ci` 3, `se`/`sen`/`v'` 5 — i.e. Layer 4 correctly marks the clitic of an inherently
pronominal verb (`andarsene`, `muoversi`, `rimanersi`, `raccostarsi`) as `expl`, and the LLM
promotes it to `obj` (78) or an oblique (18). The 8 non-clitic stragglers (`noi`, `io`, `te`...)
are too few to constitute a class.
That is an **LLM reading against the frozen UD convention**, not a Layer-4 error — `--fix`
material for Phase 5e, and nothing to file in `dep/CORRECTIONS.md`. No Layer-4 correction was
opened this round.

- Tests (`tests/test_skel.py`): `test_derive_unit_does_not_promote_coordinating_conjunction` +
  `..._still_promotes_gapped_non_conjunction_conj`,
  `test_classify_divergence_copula_predicate_double_listing_suppressed` +
  `..._copula_of_underived_head_still_flagged`, `..._adverbial_oblique_accepted` +
  `..._adverbial_argument_of_nominal_role_still_flagged` — again one negative case per rule.
- No artifact under `skel/*/` was touched; checker-only, no model call.

**Current state**: `make -C skel check` — **0 hard, 4846 soft** (5105 → 4846, Δ259; Δ1073 across
Phase 5 so far, 18.1%). Remaining: `extra_arg` 1991, `missing_arg` 1305, `role_mismatch` 1250,
`extra_tuple` 176, `membership` 96, `missing_tuple` 26, `unknown_role` 2. What is left in the
three big classes is now dominated by patterns triage says are genuine reading disagreements:
`extra_arg subj` 936 (73% citing a token *unrelated* to the predicate in the dep tree —
enjambment and pro-drop resolution), `missing_arg` 716 obliques and 265 objects `derive_unit`
reads off explicit dep edges the LLM simply didn't list, and `role_mismatch` 99.9% on edges both
sides see. Those are Phase 5e (`--fix`) material.

## Checker Phase 5a/5c: coordination + `nmod`-oblique normalization; `--fix` acceptance (2026-07-26)

Baseline before this round (`make -C skel check`): **0 hard, 5919 soft** — the state after one
Phase 4b `--fix` regeneration pass. That pass is what motivated the round: measured on inferno 1
it improved **2 of 19** flagged units (10.5%) in 3 hours, because a large share of flagged units
cannot be fixed by regeneration at all — the LLM's reading is already correct and the divergence
is on the checker's side. `PLAN.md` records the full measurement, including the four candidate
rules that were implemented, measured corpus-wide, and **rejected**.

Two rules landed in `dante_corpus/skel.py`'s `_classify_divergence`, both applied to the
`by_arg` maps after `_apply_subj_authority` and before the diff — normalizations of the same
shape as Phase 1's preposition-lemma and `attr`≡`xcomp` equivalences, not new derived rows:

1. **Rule C — coordination normalization** (`_coordination_head` / `_collapse_coordination`):
   every argument citation is mapped onto its coordination head by walking `conj` edges up
   (bounded to 8, never collapsing onto the predicate's own position), on **both** sides, with
   de-duplication. "si ciberà di terra e di sapïenza" — both conjuncts are objects and the LLM
   lists both, while `derive_unit` reads only a predicate's *direct* dep children and so sees
   the first alone. Coordination was the dominant `extra_arg` bucket (38.5% of them attached at
   dep depth 2, overwhelmingly `conj`). Roles are preserved, so a genuine role disagreement on a
   conjunct still surfaces. Emitting a derived row per conjunct instead (PLAN.md's Rule A) was
   measured at net **−2** — `extra_arg` −554 against `missing_arg` +529 — proving the divergence
   is a notation-convention mismatch, not a parse disagreement, and that normalization is the
   right instrument.
2. **Rule D — `nmod` oblique of a derived argument** (`_drop_nmod_obliques`): a given
   `obl`/`obl:<prep>` row is accepted when its argument is an `nmod` dependent of a token
   `derive_unit` already derived as an argument of the same predicate ("ha *bisogno* **di te**"
   — the dep tree hangs "te" off the noun, the LLM reads it as the predicate's oblique).

- Measured (all 100 cantos): **5919 → 5105 soft, Δ814 (13.8%), 0 hard throughout, 0 LLM calls.**
  By kind: `extra_arg` 2848 → 2065, `missing_arg` 1353 → 1317, `role_mismatch` 1245 → 1250;
  `extra_tuple` (275), `missing_tuple` (100), `membership` (96), `unknown_role` (2) unchanged.
  The slight `role_mismatch` **rise** is the expected sign of a normalization that is not merely
  suppressing: collapsing a coordination exposes role disagreements previously split across an
  `extra_arg`/`missing_arg` pair. (PLAN.md's monkeypatched pre-measurement predicted 5099; the
  landed version differs by 6 because it applies the authority model before collapsing, keeping
  Phase 2 behaviour exactly intact.)
- No artifact under `skel/*/` was touched — checker-only, like Phases 0-2 and 4a.
- Tests (`tests/test_skel.py`): `test_classify_divergence_coordinated_argument_collapsed`,
  `..._coordination_collapse_preserves_role_disagreement`,
  `..._uncoordinated_extra_argument_still_flagged`,
  `..._nmod_oblique_of_derived_argument_accepted`,
  `..._nmod_oblique_of_unrelated_token_still_flagged` — each rule paired with a negative case
  proving it doesn't swallow genuine errors.

**Phase 5c** (`skel/skel.py`, new `_is_improvement`): `--fix` accepted a regeneration on
`len(soft_after) < len(soft_before)` alone, a total-count test that admits regressions in *kind*
— the Phase 4b round traded a net count drop for `unknown_role` 0 → 2, a role outside the frozen
vocabulary. Acceptance now additionally requires that every surviving violation's class was
already present before the regeneration.

**Current state**: `make -C skel check` — **0 hard, 5105 soft** (down from 5919, Δ814; down from
17438 at the first full-corpus measurement, overall Δ12333, 70.7%). Remaining, in order:
`extra_arg` 2065 (of which `subj` 936), `missing_arg` 1317, `role_mismatch` 1250. Next is
PLAN.md's Phase 5b re-triage on this reduced set — no further `--fix` calls until it says which
classes are genuine LLM misreadings, since 5d expects part of the residue (the `expl` cases) to
be Layer-4 errors belonging in `dep/CORRECTIONS.md`.

## Checker Phase 4a: attr/xcomp double-listing + elided-copula whitelist (2026-07-20)

Corpus-wide baseline before this round (`make -C skel check`): **0 hard, 8090 soft** — Phase 3's
ending state. Phase 4 opens with a measure-first pass over the two candidate checker
refinements this file's *Next steps* named, rather than assuming their rough estimates: a
read-only analysis (calling `derive_unit`/`validate_unit` directly over the frozen corpus, no
artifact touched) sized each pattern before writing any rule.

1. **Attr/xcomp double-listing** (`dante_corpus/skel.py`'s `_classify_divergence`, new
   `double_listed` set gating the `extra_tuple` loop): a predicate nominal/adjective the LLM
   lists both as another predicate's `attr`/`xcomp` row *and* as its own redundant predicate
   tuple with the same subj — pure restatement, not new information (e.g. `inferno 1:100`, "Molti
   son li animali...": `son`'s `attr Molti` already captures the reading; the LLM's extra `Molti
   subj=animali` tuple adds nothing). Structurally identical to Phase 1's already-landed
   `ccomp`/`xcomp` double-listing suppression for `missing_arg`, just never extended to the
   `extra_tuple` side or to `attr`. Measured: **264** of 914 `extra_tuple` violations.
2. **Elided-copula predicate nominal whitelist** (same function, new `_elided_copula_nominal`
   helper, gated on both the predicate's dep deprel — `conj`/`appos`/`attr` — and a non-verb
   Layer-2 POS, via a new `morph_pos_by_position` parameter threaded from `validate_unit`'s
   `morph_rows`): a predicate nominal coordinate or apposed to a real clause with no copula token
   anywhere (`mantoani per patrïa ambedui`, `Non omo, omo già fui`) — `derive_unit` structurally
   cannot produce this (no verb, no clause-head deprel), but it's a genuine reading, not an error.
   **Narrower than this file's own earlier description** ("no verb token in the unit at all"):
   measuring the full 289 non-verb-POS `extra_tuple` predicates by dep deprel showed only
   `conj`/`appos`/`attr` (**~50**) look like genuine elided copulas. The dominant sub-pattern,
   **150** with deprel `amod` (plus `advmod` 22, `obj` 13, `nsubj` 13, `nmod` 4), are NP-internal
   participial/adjectival modifiers (`unta`, `atra`, `spiacenti`, `cinta`...) the LLM wrongly
   promoted to independent predicate status — genuine LLM errors, deliberately left flagged for
   `--fix`, not swallowed by a blanket "non-verb POS" rule.
   - Effect: `extra_tuple` dropped **914 → 600** (Δ314, exactly 264 + 50 — the two rules'
     measured sizes, confirming no unintended overlap or side effect on other kinds).
   - Tests (`tests/test_skel.py`): `test_classify_divergence_attr_double_listing_suppressed`,
     `test_classify_divergence_elided_copula_conj_whitelisted`,
     `test_classify_divergence_amod_extra_tuple_not_whitelisted` (negative case proving the
     whitelist doesn't swallow genuine errors).

**Current state**: `make -C skel check` — **0 hard, 7776 soft** (down from 8090, Δ314, 3.9%; down
from 14329 at the start of Phases 0-2, overall Δ6553, 45.7%). No artifact under `skel/*/` was
touched — checker-only, like Phases 0-2. `extra_tuple` (600), `missing_tuple` (117), `role_mismatch`
(1466), and the remaining `extra_arg`/`missing_arg`/`membership` are left for `--fix` (LLM
regeneration) or hand triage — see `skel/README.md`'s *Next steps*.

## Checker Phase 3: `--repair` mechanical TSV rewriting (2026-07-20)

Corpus-wide baseline before this round (`make -C skel check`, all 100 cantos): **0 hard, 9672
soft** — Phase 2's ending state, reproduced exactly. Phase 3 is the first pass that touches the
artifact itself (every `skel/<canticle>/<NN>.tsv` with an eligible
divergence), using a new `--repair` mode (`skel/skel.py`) that rewrites committed rows
deterministically — no model call — via two conservative rules in `dante_corpus/skel.py`'s new
`Repair`/`_find_repairs`/`_safe_role_repair`, sourced entirely from `_classify_divergence`'s own
violation list (already passed through Phase 2's `_apply_subj_authority`), never recomputing the
diff independently:

1. **null_subject** — a `missing_arg subj` (`derive_unit` resolved a real subject from an
   explicit `nsubj` edge, e.g. an enjambment subject on a preceding line) paired with an
   `extra_arg subj (0,0)` (the LLM wrote pro-drop ∅) for the *same* predicate: the ∅ row's
   citation is replaced with the derived one. Requires *both* violations present for the same
   predicate — a lone one of either means Phase 2's authority model already accepted it, or the
   two sides cite different real subjects (genuine disagreement), and no repair fires. Effect:
   `extra_arg subj` dropped **2133 → 1350** (of which ∅ `(0,0)`: **878 → 95**); `missing_arg subj`
   dropped **1127 → 344**. **783** rewrites across 100 cantos.
2. **role_label** — a `role_mismatch` where the given role is bare `obl` and the derived role is
   `obl:<lemma>` (`derive_unit`'s `case`-child detection — the only role_mismatch shape that is
   dep-tree-explicit post-Phase-1-normalization): the role cell is rewritten to the derived label.
   Explicitly does **not** fire for `subj`/`obj` or `iobj`/`obj` reversals (either direction) or
   for `obl:<lemma1>` vs `obl:<lemma2>` (cross-lemma) pairs — all genuine disagreements per this
   file's Phase 0 "Top role_mismatch pairs" table, left for Phase 4. Effect: `role_mismatch`
   dropped **1487 → 1466** (Δ21, exactly the **21** rewrites this rule made).
3. **Side effect, not fixed by this phase**: `membership` rose **89 → 94** (Δ+5). In these five
   cases (e.g. paradiso 6:142's `subj` citation to `(136,3)`, the archaic accusative clitic `il`
   in "E poi il mosser le parole biece") `derive_unit`'s `nsubj`-edge resolution points at a token
   Layer 3's NP-span/pronoun data doesn't recognize as heading an argument — a genuine Layer
   3/4 boundary case that repair's null_subject rule surfaces rather than causes. Left as-is and
   folded into Phase 4's existing `membership` backlog (deliberately not special-cased in
   `_find_repairs`, to keep the rule's precondition — "both a missing_arg and a paired ∅ extra_arg
   for the same predicate" — the sole gate, rather than adding a second, NP-membership-shaped
   gate that duplicates the checker's own membership logic).

Tests (`tests/test_skel.py`): `test_find_repairs_null_subject_pairs_missing_and_extra`,
`test_find_repairs_null_subject_then_reclassify_is_clean`,
`test_find_repairs_null_subject_not_produced_when_pro_drop_authoritative`,
`test_find_repairs_null_subject_not_produced_for_xcomp_control_accept`,
`test_find_repairs_null_subject_not_produced_for_genuine_disagreement`,
`test_find_repairs_role_label_bare_obl_to_lemma`,
`test_find_repairs_role_label_then_reclassify_is_clean`,
`test_find_repairs_role_label_rejects_subj_obj_reversal`,
`test_find_repairs_role_label_rejects_different_obl_lemma`,
`test_find_repairs_role_label_rejects_iobj_obj_reversal`.

Corpus-wide run: `make -C skel repair` — **804** total rewrites (783 null-subject + 21
role-label) across 100 cantos, touching 100 `skel/<canticle>/<NN>.tsv` files (804 rows changed,
804 removed — a clean 1:1 replace per row, verified by diff; re-running `--repair` afterward is a
no-op, confirming convergence). By kind, before → after: `extra_arg` 4502 → 3719, `missing_arg`
2563 → 1780, `role_mismatch` 1487 → 1466, `extra_tuple` 914 → 914 (untouched, Phase 4), `missing_
tuple` 117 → 117 (untouched, Phase 4), `membership` 89 → 94 (see item 3 above).

**Current state**: `make -C skel check` — **0 hard, 8090 soft** (down from 9672 at Phase 2's end,
Δ1582, 16.4%; down from 14329 at the start of Phases 0-2, overall Δ6239, 43.5%). Every touched
`skel/<canticle>/<NN>.tsv` was committed alongside this entry. Phase 4 (targeted `--fix`/hand
corrections for the remainder — genuine subj/obj/iobj reversals, elided-copula extra_tuples,
membership) is still open; see `skel/README.md`'s *Next steps*.

## Checker Phases 0-2: normalization + authority model (2026-07-20)

Corpus-wide baseline before this round (`make -C skel check`, all 100 cantos): **0 hard, 14329
soft**. Phases 0-2 are pure checker changes — no artifact
edited — that shrink the soft-violation count deterministically before any TSV is touched
(Phase 3) or the LLM is re-invoked (Phase 4). All three phases (`dante_corpus/skel.py`,
`skel/skel.py`) landed together in this pass; measured **corpus-wide `--stats` after each
phase**, not just the final number, so each phase's own contribution is on record.

1. **Phase 0 — `--stats`** (`skel/skel.py`): added a `--stats` flag/`stats()` function that
   aggregates `validate_unit`'s soft `Violation`s by kind, by `(kind, role, ∅-or-real)`, and by
   `role_mismatch` pair, instead of the one-line-per-violation dump `--check` prints. Required
   extending the shared `Violation` dataclass (`dante_corpus/morph.py`) with optional
   `role`/`given_role`/`arg`/`predicate` fields, populated only by `skel._classify_divergence` —
   additive, no other layer's `Violation` construction changed. Baseline reproduced exactly:
   7035 extra_arg / 3782 missing_arg / 2392 role_mismatch / 914 extra_tuple / 117 missing_tuple /
   89 membership = 14329, matching the original plan's published table verbatim (measurement only, no
   count changed).
2. **Phase 1 — normalization layer** (`dante_corpus/skel.py`, `_canonicalize_role`/
   `_normalize_prep_lemma`, applied inside `_classify_divergence`'s `by_arg` comparison and
   inside `derive_unit`'s own `obl:<lemma>` construction): canonicalized both sides of the diff
   toward the derived side's convention before comparing.
   - Preposition-lemma orthographic variants: `sanza`/`sanz`/`sans` → `senza`,
     `sovra`/`sovr'`/`sor` → `sopra`, `de` → `di`, `contra`/`contr` → `contro`, `ver` → `verso`,
     `ad` → `a`, `col`/`coi` → `con` (the last four extend the original plan's three named pairs, found
     via `--stats`'s role_mismatch-pairs table as it recommends).
   - Role-label splits for one reading: `attr` ≡ `xcomp` (copular-complement labeling),
     `iobj` ≡ `obl:a` (dative alternation) — both canonicalize to the derived side's label.
   - Clausal-complement double-listing: a `missing_arg` for a `ccomp`/`xcomp` derived role is
     suppressed when the argument token is itself proposed as its own predicate tuple by the LLM.
   - Effect: **14329 → 12825** (Δ1504, close to the original ~1500 estimate). `role_mismatch`
     dropped 2392 → 1584; the `attr`/`xcomp`, `iobj`/`obl:a`, and all seven orthographic prep
     pairs no longer appear in the pairs table. Tests: `test_validate_unit_divergence_
     normalizes_attr_xcomp_and_prep_variants`, `test_validate_unit_divergence_ccomp_double_
     listing_suppressed` (`tests/test_skel.py`).
3. **Phase 2 — authority model for `subj`** (`dante_corpus/skel.py`, `_apply_subj_authority`,
   threaded into `_classify_divergence` via a new `dep_index_by_pos` parameter built from
   `dep_rows` at `validate_unit`'s call site): made the `subj` slot LLM-authoritative (validated
   against a candidate set, not exact-matched) in exactly the three cases the original plan named, no
   further:
   - **Pro-drop antecedent** — `derive_unit` produced `subj (0,0)`: any concrete subject the LLM
     resolves is accepted (strictly more informative than ∅, not wrong).
   - **Non-finite ∅** — `derive_unit` produced no `subj` row at all for the predicate: an
     LLM-proposed `(0,0)` is accepted.
   - **xcomp/ccomp control subject** — `derive_unit` produced no `subj` row and the predicate's
     own deprel (via `dep_index_by_pos`) is `xcomp`/`ccomp`: an LLM-proposed subject is accepted
     iff it equals the matrix predicate's derived `subj` or `obj` — replaces the verb-specific
     control lexicon the pilot-build note above (Item 1, 2026-07-13) explicitly deferred, with a
     structural candidate-set check instead (no lexicon, still UD-deprel-only).
   - Every other role, and `subj` where `derive_unit` derives a real (non-∅) subject, stay
     exact-match — this is deliberately narrower than "any subject disagreement is fine": a
     control-subject candidate outside the matrix subj/obj pair, or a `subj` disagreement on a
     predicate `derive_unit` already resolves, still flags (`test_classify_divergence_xcomp_
     control_subject_rejects_unrelated_arg` asserts this negative case explicitly).
   - Effect: **12825 → 9672** (Δ3153; the original ~6000-7000 estimate for this phase was
     explicitly rough/non-additive — the actual figure is lower because a meaningful share of
     `extra_arg subj`/`missing_arg subj` are genuine LLM/derivation disagreements on predicates
     `derive_unit` *does* resolve a real subject for, which correctly remain exact-match and
     unaffected). `extra_arg subj` dropped 4666 → 2133 (of which ∅ 2227 → 878); `missing_arg
     subj` dropped 1718 → 1127. Tests: `test_classify_divergence_non_finite_predicate_accepts_
     null_subject`, `test_classify_divergence_xcomp_control_subject_accepts_matrix_arg`,
     `test_classify_divergence_xcomp_control_subject_rejects_unrelated_arg`.

**Current state**: `make -C skel check` — **0 hard, 9672 soft** (down from 14329; Δ4657, 32.5%).
No artifact under `skel/*/` was touched — this is checker-only, per the plan's gate before
Phase 3 (`--repair`, mechanical TSV rewriting) and Phase 4 (targeted `--fix`/hand corrections),
both still open. `dante_corpus/README.md`'s Layer-5 section (still to be written — see root
`PLAN.md`'s Handoff) and root `PLAN.md`'s Layer-5 "Check" paragraph should describe the
derive-authoritative/LLM-authoritative distinction once Phase 3/4 land alongside it.

## Pilot build, Inferno 1 (2026-07-13)

First build (`uv run skel/skel.py inferno -c 1 -m ollama:gemma4:31b-it-qat`) hit 3/3 retry
failures on lines 55-60, all identical: the model cited `59.2 venendomi` (gerund `venire` fused
with the enclitic dative pronoun `mi` — Layer 2 lemma `venire+mi`, no separate token exists for
`mi`) as its own argument, tripping the hard self-citation check. Fixed in `SYSTEM_PROMPT`
(`skel/skel.py`) with an explicit rule: a verb token with a fused enclitic pronoun encodes that
pronoun internally; do not cite it, or the predicate's own position, as a separate argument. No
`derive_unit` change — this is a token-citation constraint the prompt needs to state, not a
divergence the deterministic derivation gets wrong.

After that fix, the canto built clean: **0 hard** violations, all 136 lines committed.

### Soft-divergence triage (`--check`: 0 hard, 136 soft before the fixes below)

Every soft violation was inspected by comparing the LLM's rows against `derive_unit`'s output
for the same parse unit (not just the violation's one-line detail). Four distinct root causes
emerged, none of them the mixed-copular-style pattern the *Handoff* section predicted as the
likely largest class — that pattern (`è root`/`cosa attr` vs `amara`/`è cop`) barely appears in
canto 1; the actual largest class is different and still open (see below).

1. **`xcomp`-complement subject/object control (largest class, ~50+ of 136 soft violations)** —
   copular-raising verbs (`sembiava carca`, `parea fioco`) and causative `fare` (`fé... viver
   grame`, `fai... mesti`) both take an `xcomp` complement whose own implicit subject
   `derive_unit` currently leaves unfilled (only `conj`-chain subject sharing is implemented, not
   `xcomp`/`ccomp` control). The LLM consistently filled it in, but with an important wrinkle:
   `sembiare`/`parere` are **subject-control** (the xcomp's implicit subject = the matrix
   predicate's own subject) while `fare` is **object-control** (the xcomp's implicit subject =
   the matrix predicate's direct object) — a lexically-governed distinction, not one derivable
   from UD deprels alone. **Deferred, not fixed**: extending `derive_unit` would mean encoding a
   verb-specific control lexicon, which sits uneasily with this layer's "no semantic frame, UD
   deprels only" design (see `dante_corpus/skel.py`'s module docstring and PLAN.md's *Out of
   scope*). Revisit once more cantos are built and the pattern's shape (how many verbs, how
   reliably subject- vs object-control splits along closed verb classes) is actually measured,
   per the *measure-then-freeze* discipline — a single canto is too small a sample to freeze a
   control lexicon against.
2. **Elliptical predicate nominals with no verb token at all** (`mantoani per patrïa ambedui` —
   "[we were] Mantuans by homeland", copula elided; `Non omo, omo già fui` — "[I was] not a man,
   [but] a man I once was", first `omo` has no copula at all) — `derive_unit`'s two predicate
   rules both require either a clause-head deprel or a verb token; an elided-copula predicate
   nominal satisfies neither structurally. Genuinely unexpressable by the current derivation, not
   a bug. **Exemption, not fixed** — same shape as `dep/CORRECTIONS.md`'s substantivization
   cases: a real reading the mechanism can't cite, checked by hand against its terzina, not a
   parse error.
3. **NP-membership soft-check false positives, fixed deterministically** (`dante_corpus/skel.py`
   `validate_unit`) — two sub-patterns, both mechanical widenings of the membership check, not
   changes to `derive_unit` or any artifact:
   - Relative pronoun `che`/`ch'` cited as a `subj`/`obj`/`obl` argument is correctly Layer-5
     usage, but Layer 2 tags `che`/`ch'` inconsistently between `pronoun` and `conjunction` even
     in its relative use (`morph/CORRECTIONS.md`'s `che`/`ch'` mistag section), so the
     POS-based pronoun check missed it. Fixed by also accepting the word form itself
     (`che`/`ch'`/`cui`/`qual`/`quale`/`chi`) regardless of the frozen POS tag.
   - An adverbial oblique (`quivi`, `là`, `sù`, `dietro`) is a legitimate `obl`/`obl:*` argument
     with no NP to cite — adverbs were simply never in the membership check's acceptance set.
     Fixed by accepting an adverb-POS token specifically for `obl`/`obl:*` roles (not for
     `subj`/`obj`/`iobj`, where an adverb would still be a genuine miscitation).
   - Tests: `tests/test_skel.py`'s four new `test_validate_unit_membership_*` cases.
   - Effect on canto 1: 13 -> 2 membership violations (11 resolved: 6 relative-pronoun instances,
     5 adverb instances). `--check`: **136 -> 125 soft** (0 hard throughout).
4. **Two single-instance boundary cases, left as-is** — inferno 1:59 `'ncontro` (the model, having
   been told not to cite the fused-enclitic argument of `venendomi` directly per item 1's build
   fix, cited the adjacent preposition instead — a defensible fallback, not wrong, but not a
   nominal citation either); inferno 1:110 `l'` (elided direct-object clitic `lo`, graphically
   identical to an elided article, so Layer 2 tags it `article` — genuinely ambiguous without
   deeper morph-layer work, out of scope for this pass). Both remain flagged by the membership
   check; revisit only if the pattern recurs at scale.

**Current state**: `skel/inferno/01.tsv` — **0 hard, 125 soft** (`uv run skel/skel.py inferno -c
1 --check`). Item 1 (xcomp control) is the dominant remaining class and is an open design
question, not a bug to silently fix; items 2 and 4 are structural/POS-ambiguity limits expected
to recur at low, tolerable rates across the corpus. No canto-2+ build has been run yet.
