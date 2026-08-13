# Plan: a shared grammatical-analysis stack in the corpus

## Handoff (2026-08-13) — resume here

**Everything is committed. Newest work: rule AG (from re-reading Inferno 4-6's residue) plus a
third POS-keyed `--fix` class, `extra_arg_adjective`, generalizing one of that read's shapes.**
Checks at commit time: `dep --check` 0 hard/**18** soft (the subject-agreement rule's
verified-and-left-alone residue), `case --check` 0 hard, `skel --check` 0 hard/**1409** soft,
`np --check` 0/0, `morph --check` 0/0, `pytest` **243** passed.

**Rule AG scored 1452 → 1409, −43, no model call.** `derive_unit`'s conj-subject-propagation
(step 3) inherited a coordination head's subject unconditionally, with no check that the
inherited subject's Layer-2 person/number actually fits the predicate receiving it. Gated on
`dep.subject_agreement` (extended with a new `_finite_head_of` helper so a periphrastic predicate
checks its `aux`, not its own non-finite morph row): of 1370 conj-inherited-subject candidates,
682 agree, 461 are undecidable (left untouched, same discipline as the `null_subject` gate), and
**227 actively disagree** — those are no longer required. One cross-layer fix rode along
(`fiacco`, inferno 6:54, was tagged an adjective; it's 1sg of *fiaccarsi*). Full write-up in
[`skel/CORRECTIONS.md`](skel/CORRECTIONS.md)'s *Rule AG*; the other 17 of Inferno 4-6's 19
remaining positions were read individually and are genuine LLM disagreement/omission, not
checker silence — recorded there with the reason for each.

**`extra_arg_adjective`**: one of those 17 (6:70, "Alte terrà... le fronti") is the same
attributive-vs-depictive-adjective misreading `extra_tuple_adjective` (rules Y-AF) already has a
dedicated `--fix` question and prompt for, one level down — the adjective is wrongly attached as
an argument of a predicate rather than promoted to a predicate of its own. Checked against the
corpus before generalizing from one instance: **65 of 107** `extra_arg xcomp`/`attr` violations
cite an adjective as the argument, a population the size of `extra_tuple_adjective`'s original
37. `skel/skel.py` gained the matching `--fix` machinery — `_violation_subclass`/`_CLASS_PROMPTS`
entry keyed on the *argument's* POS this time, `_fix_hint` phrasing, `_CLASS_ORDER` placement —
reusing `extra_arg`'s own ask/apply functions with `_CONV_ADJECTIVE` fronted in its system prompt.
Full write-up in [`skel/CORRECTIONS.md`](skel/CORRECTIONS.md)'s *A third POS-keyed `--fix`
class*. **Unmeasured until a `--fix` round runs** — `skel --check` is unaffected by this change
(it only changes which question a violation is asked).

**A `--fix` round against this state is queued, user-run next.** It carries `extra_arg_adjective`
into a live pass for the first time; per *How to measure a future `--fix` round* below, read the
subclass table for that class specifically against its 65-position population, not just the pass
average.

### What Phase 6 did (2026-08-12)

`--fix` was the project's most expensive instrument and its least efficient: Phase 5w's pass
spent **1290 LLM calls to remove 123 violations**. Two properties explain that, and both are
gone. It regenerated a *whole* parse unit and accepted the result only if the *whole* unit
improved, so settling one of five violations counted for nothing; and it used **one monolithic
prompt for every violation class**, which Phase 5w had already shown does not move a class. Full
write-up in [`skel/CORRECTIONS.md`](skel/CORRECTIONS.md)'s *Phase 6*.

`--fix` now runs three stages per flagged unit, cheapest first, each under the same acceptance
gate (0 hard, `_is_improvement`) so the no-worse-off guarantee holds stage by stage:

- **Stage 1, deterministic — measured at 2084 → 2011, −73, with zero model calls.** The
  `_find_repairs` catalogue grew from two rules to four and is now split into two explicit tiers.
  **Tier A asserts no reading** (`role_label` 7, and the new `prep_stack` 4 — one preposition of
  a chained stack named instead of another). **Tier B does assert a reading and may only do so
  where a signal independent of Layer 4 corroborates it**: `null_subject` (31) now fires only
  when Layer 2's person/number agrees with the predicate. That gate is the substance, not
  paperwork — of the corpus's **67** ∅-subject pairs Layer 2 corroborates 37 and **actively
  contradicts 20**, so the ungated rule this plan warned against would have rewritten 30 rows on
  the derivation's say-so exactly where the two frozen layers disagree. `dep.subject_agreement`
  is the same test `dep --check` runs, extracted so the two cannot drift; its third answer,
  "undecidable", is treated as a refusal, not a weak yes. Stage 1 also verifies itself (6 of the
  37 corroborated candidates were rolled back) and is idempotent. `--repair` is now this stage
  run alone.
- **Stage 2, one narrow question per violation class.** Each class gets its own short system
  prompt — only the conventions bearing on it, lifted verbatim from `SYSTEM_PROMPT`, each under
  half its length — its own question, and its own small answer, spliced in at row level and
  accepted per class. So an instruction reaches the model at the flagged position *by
  construction* rather than by prompt-writing discipline, and a unit keeps the classes that were
  settled. `membership` (8) and `unknown_role` (0) have no prompt on purpose.
- **Stage 3, the old whole-unit regeneration**, unchanged, for units the first two left
  untouched; `--no-whole` turns it off so a round can be measured with and without it.

**The independence rule is preserved and now tested.** A question may name the predicate, the
argument the LLM itself cited, and the role slot in dispute — what `_fix_hint` already disclosed
— but never `derive_unit`'s own argument position.

**Two rules were measured and deliberately not shipped**, so the counts are not re-derived: a
`case`-annex-corroborated relabel would rewrite **106** rows for **zero** violations (rule U
already suppresses every one — artifact hygiene, not fix efficiency), and a `role_alias` rule has
a population of **0**.

**What the next round should report**: calls *and* violations removed **per class**, against
Phase 5w's 1290 / 123 / 0.095. Do not expect fewer calls — grouping by (unit × class) yields a
similar count. Expect a higher per-call yield, and read the per-class table, not the average.

### What rule AG did (2026-08-13)

A per-position read of **all 19 remaining soft violations in Inferno 4-6** — the fourth read of
this kind (after rule V's twelve, rules W/X's five, rules Y-AF's twenty-six). Full write-up in
[`skel/CORRECTIONS.md`](skel/CORRECTIONS.md).

- **1452 → 1409 soft, −43**, no model call. `missing_arg` 566 → **522**; `extra_arg` 661 → 662
  (+1, a corner case where clearing one position's derived subject converted a matched row
  elsewhere into a fresh mismatch — net still a large improvement).
- **Rule AG** (`_apply_subj_authority`'s new branch): `derive_unit`'s conj-subject-propagation
  inherited a coordination head's subject with no check that its Layer-2 person/number actually
  fits the predicate receiving it. Gated on `dep.subject_agreement`, the same test the
  `null_subject` gate uses, extended with a new `_finite_head_of` helper so a periphrastic
  predicate ("**potrai** vedere") is checked against the token that carries person, not the
  non-finite verb itself. Of 1370 conj-inherited-subject candidates, 682 agree, 461 are
  undecidable (untouched), **227 actively disagree** and are no longer required.
- **One cross-layer fix**: `fiacco` (inferno 6:54) was tagged an adjective, impossible next to the
  reflexive clitic `mi`; it's 1sg present of *fiaccarsi*. This is what let rule AG's agreement
  check see it as a finite verb at all.
- **A gate that was wrong, kept on record**: an initial version dropped the inherited subject
  unconditionally on disagreement, without checking whether the LLM's own reading already matched
  it — that *raised* the count to 1586 (turning agreeing cases into fresh `extra_arg` reports) and
  was rejected before landing, the same shape of near-miss Stage 1's `null_subject` gate warned
  about.
- **The other 17 read individually stay flagged for stated reasons** — real LLM omissions
  (compound subjects/obliques with only one conjunct cited), real reading disagreements (a
  causative construction read backwards, an attributive adjective read as a depictive predicate),
  and two further silence shapes (an adverb-headed oblique with a nested `nmod`; a locative clitic
  tagged `advmod`) seen only once each in this sample — not generalized without a larger read. See
  [`skel/CORRECTIONS.md`](skel/CORRECTIONS.md) for the position-by-position record.

### What the Phase 6 `--fix` round did (2026-08-13, user-run)

The round Phase 6 called for: `make -C skel fix` 3-way parallel over the 1106 units flagged at
2011, the first pass against the restructured stage 2/3 driver. Full write-up in
[`skel/CORRECTIONS.md`](skel/CORRECTIONS.md)'s *The round, measured*.

- **2011 → 1452 soft, −559 (−27.8%)**, 98 cantos touched, 259 units cleared outright, 197
  improved. **0 units got worse and 0 were newly flagged** — the guarantee held stage by stage,
  as designed. `skel/skel.log` was again left empty by the parallel invocation, so the exact call
  count is unrecoverable; against the 1106-unit lower bound the yield is **0.505 per unit**, five
  times Phase 5w's 0.095 and two and a half times 5s's 0.199 prior ceiling. The true per-call
  figure is lower (stage 2 asks one question per class per unit, so calls exceed units), but the
  margin is too large to be call-count inflation alone.
- **Both Phase 6 predictions held, sharply, at the POS-keyed subclass level `--fix` actually
  works in.** `extra_tuple_adverb` — its own narrow prompt, carrying only the adverb rule —
  **37 → 7, −78.8%, the largest single-class move of any `--fix` round on record**.
  `extra_tuple_adjective` moved 37 → 17, −54.1%, a real disagreement (no `cop` edge either way)
  so it moves less than its sibling but still far above the pass average. The three classes with
  no stage-2 prompt (`extra_tuple`, `missing_tuple`, `membership`) moved at or near zero — the
  control confirming the gain is the targeted prompts, not stage 3 alone. `role_mismatch`
  (−40.8%) and `missing_tuple_nominal` (−40.3%) also moved well above average; `missing_arg`
  (−28.9%) and `extra_arg` (−19.1%) moved at their usual regeneration-resistant rate, though even
  that beats any prior round's pass average.
- **The two open routes from the previous handoff are answered by this number**: attributive
  adjectives (17 left) and promoted adverbs (7 left) were exactly the populations these two new
  prompts moved, and the adverb route is now nearly closed. Do not write a checker rule for
  either without re-reading what's left first — see *If a next task is wanted* below.
- **Three `tests/test_skel_fix.py` fixtures needed updating, not the driver.** They pinned
  Inferno 1 as "the smallest real case" (one `extra_tuple` violation); this round cleared it
  outright, so no canto now has a single-unit `extra_tuple_adverb` case. Repointed to Purgatorio
  1 (one `missing_arg`), mechanics unchanged. `pytest` 243 passed after the update.

### What rules Y-AF did (2026-08-12)

A per-position read of **all 26** Layer-5 soft violations standing in **Inferno 1-3** — the third
time this exercise has been run (rule V from Inferno 1's twelve, W and X from its five) and the
first over more than one canto. Full write-up in [`skel/CORRECTIONS.md`](skel/CORRECTIONS.md);
the cross-layer halves are in [`dep/`](dep/CORRECTIONS.md), [`morph/`](morph/CORRECTIONS.md) and
[`case/`](case/CORRECTIONS.md).

- **2330 → 2084 soft, −246 (−10.6%)**, 89 cantos touched. `membership` 47 → **8**, `extra_tuple`
  137 → **91**, `extra_arg` 954 → **848**, `missing_arg` 883 → **827**; Inferno 1-3 itself 26 →
  **11**. No model call; no artifact row was changed by a rule.
- **The finding: `role_mismatch` did not move at all — 234 before and after.** Every one of the
  eight rules landed on a class where **one side is silent**, and that is structural, not a gating
  accident: a `role_mismatch` is the one class where both layers speak, so it is a real
  disagreement and only a third read (rule U's `case` annex) has ever settled one. What the
  checker still had to give was silence being reported as denial.
- **The two biggest rules were not on the route list either.** Rule AB (−63) accepts the reflexive
  clitic Layer 4 writes as `expl`, which puts it outside `ARG_DEPRELS` entirely; rule Z (−77 over
  two legs) accepts a **verb form** Layer 4 put in an argument slot, which generalizes the
  `per`+infinitive route the plan had ranked *last* at 27 violations. Rule Y closed the route
  ranked **first** and was worth only −8 — rules X and `double_listed` had already absorbed most
  of that class. **The classification by count mispredicted both ends of the list.**
- **The `membership` class is closed as a question** (rule AF, 47 → 8): a token Layer 4 fills an
  argument slot with is admissible as a Layer-5 argument whatever its POS. Five consecutive
  `--fix` rounds had left it at exactly 47, which is what a checker question looks like from
  outside.
- **Seven cross-layer corrections**, fixed in the same session per the standing rule: 4 Layer-2
  rows (`tosta` read as an adverb, `disio` as a noun, `che` as a conjunction, `fier`/`conte` as
  `fare` + a noun), 11 Layer-4 rows (including **an elided speech frame at inferno 3:13 the
  2026-08-07 round missed** while normalizing 99 others), and 1 `case` row the Layer-2 retag
  brought into scope. Two of them **raise** Layer 5's count by four, because a corrected parse no
  longer matches a wrong LLM reading — the honest-checker case again.
- **Two `--fix` hints, not prose alone.** 33 of the 91 surviving `extra_tuple` cite an adverb
  although the prompt has forbidden adverb predicates throughout, and 37 cite an adjective; both
  now have POS-keyed `_fix_hint` phrasings plus matching prompt prose, per Phase 5w's rule that an
  instruction must reach the model at the flagged position. `missing_tuple_nominal` was widened
  past the elided verb of speech to any verbless clause (32 of 76 cite a pronoun at a verbless
  root). **Unmeasured** until a `--fix` round runs.

### What rules W and X did (2026-08-12)

A per-position read of **Inferno 1's five** remaining soft violations — the same exercise that
produced rule V from its twelve. Full write-up in
[`skel/CORRECTIONS.md`](skel/CORRECTIONS.md). No artifact regenerated, no model call.

- **2408 → 2330 soft, −78 (−3.2%)**, 44 cantos touched. `extra_arg` 995 → **954**,
  `role_mismatch` 258 → **234**, `missing_arg` 896 → **883**; Inferno 1 itself 5 → **3**. Nothing
  in the after-run was absent from the before-run.
- **Rule W** (`_case_corroborated_swap`, −24): rule U is scoped to the pronoun position the `case`
  annex holds a value for, but a `subj`/`obj` disagreement inverts **both** legs of a transitive
  clause and typically only one leg is a pronoun. "lo passo **che** non lasciò già mai **persona
  viva**" (inferno 1:27) — the annex reads `che` as `nominative`, rule U accepted that leg, and
  `persona`, a noun, stayed flagged although it is the same decision reported twice. Gated on the
  exact exchange of the two roles, not on co-presence under the predicate; one-directional.
- **Rule X** (`_complement_hosted_argument`, −54): the argument side of the copula convention. The
  frozen style makes the copula the clause head and the predicate nominal its `attr`/`xcomp`, so
  Layer 4 hangs obliques on the copula while the LLM follows UD and hangs them on the complement.
  `double_listed` and `_aux_of_derived_predicate` already accepted this on the *tuple* side;
  nothing did on the argument side, where it cost a `missing_arg` on the copula **plus** an
  `extra_arg` on the complement when both are derived. Gated on both readings agreeing the pair
  forms one predication, and on the role matching.
- **The finding is procedural.** Rule V's write-up had read these same five positions and called
  two of them *"an LLM slip"* and *"an attachment-level disagreement"*. Both were checker silence.
  A per-position read has to ask **which rule declined to fire**, not only what the line means:
  reading the line settles what is true, but it does not reveal that the checker already knew.
- **A first gate that was wrong, kept on record**: rule X initially required the complement *not*
  be a derived predicate, and rejected 12 of 17 candidates (−28 only). Backwards — when both are
  derived the convention costs *two* violations, so those are the cases most worth accepting.
- **Prediction for the next `--fix` round**: both rules create no LLM-authored rows, so by Phase
  5u's rule they remove exactly the positions regeneration had a chance at. Expect a yield at or
  below 5u's 0.068 floor. That is confirmation, not failure.

### What Phase 5w did (2026-08-12, user-run)

The pass Phase 5v set up: `make -C skel fix` 3-way parallel over the 1290 units flagged at 2531,
run against a `SYSTEM_PROMPT` that had just gained four convention rules, a second worked example
and a corrected `--fix` hint. Full write-up in
[`skel/CORRECTIONS.md`](skel/CORRECTIONS.md)'s *Phase 5w*.

- **2531 → 2408 soft, −123 (−4.9%)**, 57 cantos touched. **0 units got worse and 0 were newly
  flagged** — the fifth consecutive round to hold both. 90 units improved, 51 cleared outright.
- **Yield 0.095 violations per LLM call**: back inside the flat 0.085-0.11 band, above 5u's 0.068
  floor, nowhere near 5s's 0.199. At the pass level the prompt rewrite bought an ordinary round.
- **The four rules did not score alike, and that is the finding.** The elided speech frame
  (`missing_tuple` on a pronoun) fell **63 → 45, −28.6%** — six times the pass average, and 15% of
  the whole pass's −123 out of a class that is 2.5% of the residue. The other three moved at or
  below the pass average: `extra_arg subj (0,0)` 126 → 123 (−2.4%), adverb `extra_tuple` 35 → 33
  (−5.7%), and `attr` turned out **unmeasurable** — the label never appears in `--check` output at
  all, so no round can score it without a check that reports it.
- **What separates them is the form of the instruction, not the subject.** The speech-frame rule
  was the only one 5v gave three instruments: prose, a **worked example as a table**, and a
  **rewritten `--fix` hint** (`_fix_hint` stopped asking whether a pronoun "heads its own clause").
  The others were prose in an already long prompt. **A prose rule buried in a long prompt does not
  change the reading; an instruction that reaches the model at the flagged position does** — and
  the per-violation hint is both the likelier half to be doing the work and much the cheaper to
  write.
- **The corollary 5v asked for**: the residue is *not* reading disagreement all the way down — one
  correctly closed silence was worth 18 violations — but it is not prompt-side in bulk either.
  Write further prompt rules only with a `--fix` hint attached; the volume is in the
  assistant-side routes below.

### What Phase 5v did (2026-08-10)

A prompt-vs-residue audit, prompted by the user's point that yield cannot change unless the prompt
is adjusted to the corrections. Full write-up in
[`skel/CORRECTIONS.md`](skel/CORRECTIONS.md)'s *Phase 5v*. No artifact changed; count still 2531.

- **The gap, measured by the POS of the token each violation cites**: 79 of 94 `missing_tuple` are
  the elided verb of speech promoted to its subject token (`io` 30, `elli` 22, 16 nouns) — a
  convention Layer 4 normalized corpus-wide in 2026-08-07 and the prompt never mentioned; 126 of
  321 `extra_arg subj` are the model writing ∅ where rule V would accept a controller's subject,
  because the prompt describes the ∅ row only for *finite* verbs; 35 of 146 `extra_tuple` are
  adverbs, which the derivation stopped promoting when the `adverb` bug was fixed; `attr` sits in
  the role list with no gloss although the multiple-`obj` round chose it over `xcomp` deliberately.
- **Four rules added** plus a second worked example (inferno 3:34-35, the promoted frame as a
  table), and the `--fix` hint for a non-verb `missing_tuple` rewritten — it had been asking
  *"check whether it heads its own clause"* about a pronoun, which is the wrong question.
- **Two classes turned out not to be prompt-side** and are recorded as routes instead: 47
  `extra_tuple` adjectives where Layer 4 attaches a copular clause head with a nominal deprel so
  `derive_unit` stays silent (rule V's shape again — the strongest assistant-side route), and 14
  stacked-preposition mismatches where Layer 4 itself is inconsistent (`in su` chained vs
  `dentro al` flat).

### What Phase 5u did (2026-08-10, user-run)

The `--fix` pass the previous handoff called for, `make -C skel fix` 3-way parallel over the 1347
units flagged at 2623. Full write-up in [`skel/CORRECTIONS.md`](skel/CORRECTIONS.md)'s *Phase 5u*.

- **2623 → 2531 soft, −92 (−3.5%)**, 54 cantos touched. **0 units got worse and 0 were newly
  flagged** — the fourth consecutive round to hold both. 79 units improved, 57 cleared outright.
- **Yield 0.068 violations per LLM call — the lowest of any `--fix` round**, below 5t's 0.085,
  5q's 0.086, 5e's 0.11 and a third of 5s's 0.199. **The prediction the previous handoff made was
  wrong**, and the correction is the finding of the round.
- **Provenance, not magnitude, is the predictor.** 5s and 5t were preceded by rounds that *created*
  LLM-authored rows (the `adverb` bug's surfaced tuples; the 99 promoted speech frames), and the
  class carrying them moved several times the pass average each time. Rule V created nothing: it is
  a checker *acceptance* that deleted 479 `extra_arg` reports without touching an artifact row — so
  it removed precisely the positions regeneration had a chance at, and left a flagged set **more**
  resistant than 5t's. A cross-layer round's violation count says nothing on its own.
- `missing_tuple` was again the fastest class (−13.8%), the tail of the speech frames. `membership`
  moved **0**, confirming its 47 are a question about the check rather than artifact error.

### What rule V and the membership audit did (2026-08-09)

A per-position read of **Inferno 1's twelve** soft violations, asked for as a check on what the
residue is actually made of, turned into the largest single reduction the checker has produced.
Full write-up in [`skel/CORRECTIONS.md`](skel/CORRECTIONS.md); the cross-layer halves are in
[`morph/`](morph/CORRECTIONS.md), [`dep/`](dep/CORRECTIONS.md), [`case/`](case/CORRECTIONS.md) and
[`np/CORRECTIONS.md`](np/CORRECTIONS.md).

- **3136 → 2623 soft, −513 (−16.4%)**, no artifact regenerated and no model call. `extra_arg`
  1544 → **1065**, `membership` 82 → **47**; Inferno 1 itself 12 → **5**.
- **Rule V** (`_control_subject_candidates`): `derive_unit` reads only a predicate's own dep
  children, so a **non-finite** predicate with no `nsubj` child got no `subj` row at all — silence,
  not an assertion — and every subject the LLM resolved there was reported as `extra_arg subj`,
  the largest class in the corpus (805, 26% of the residue). The rule walks the dep head chain and
  accepts a subject that is any ancestor's `subj`/`obj`/`iobj` up to the first ancestor with a
  subject of its own (control/raising, including the causative's dative causee), or the nominal an
  `acl` participle modifies. `extra_arg subj` 805 → **327**.
- **The four shapes were not evenly split**: 289 control-chain, 155 `acl` participle, 13 causative
  dative — against 316 that are genuine head-to-head disagreement and stay flagged. The rule is an
  *acceptance*, never an assertion: a subject outside the reachable set is still reported.
- **The membership class was a Layer-2 audit in disguise.** Classifying all 82 by the POS of the
  cited token found 37 tokens Layer 2 was simply wrong about — `onde` as a conjunction where it is
  a relative pro-form (16), proclitic pronouns tagged as articles (8), `e'` read as `essere` (2),
  `quantunque` (2), fused clitic clusters and adverbs tagged as prepositions (7), 2 the other way.
  The retags pulled 32 rows into the `case` annex's scope and 4 clitic mentions into Layer 3.
- **The remaining 47 are a checker question, not a data error**: substantivized adjectives, quoted
  mention words as the object of a verb of saying ("faceva dir l'un ‘No’"), adverbs cited as
  objects ("non sa **como**"). They need a decision about what the check admits as an argument.

### What Phase 5t did (2026-08-09, user-run)

The `--fix` pass the previous handoff reserved for the user, run as `make -C skel fix` 3-way
parallel over the 1575 units flagged at 3270. Full write-up in
[`skel/CORRECTIONS.md`](skel/CORRECTIONS.md)'s *Phase 5t*.

- **3270 → 3136 soft, −134 (−4.1%)**, 61 cantos touched. **0 units got worse and 0 were newly
  flagged** — the third consecutive round to hold both. 96 units improved, 48 cleared outright.
- **Yield 0.085 violations per LLM call** — the flat rate of 5q (0.086) and 5e (0.11), *not* the
  0.199 Phase 5s measured and this plan predicted.
- **The prediction was wrong at the pass level and right at the class level.** `missing_tuple` —
  where the subject-agreement round's +105 promoted speech frames had landed — fell **22.1%**, five
  times the pass average and the largest single-class move of any `--fix` round; 33 of the 99
  promoted frames were taken up by the LLM independently. The two big classes moved 2-3%, their
  usual regeneration-resistant rate.
- **The corrected rule, which supersedes what 5s wrote**: a cross-layer round does not raise the
  yield of the next pass as such. It creates a sub-population regeneration settles fast, and the
  pass-level yield is that rate **diluted by the rest of the flagged set**. 5s only looked like a
  break from Phase 5q's stop rule because its two new populations were large against 1659 units;
  +105 against 1575 was not. Phase 5q's stop rule stands.

### What the subject-agreement round did (2026-08-07)

A new `dep` soft check — an `nsubj`/`nsubj:pass` whose Layer-2 person or number contradicts its
**finite** head's — opened at **173** positions and closed at **18** in one round. Full write-ups
in [`dep/CORRECTIONS.md`](dep/CORRECTIONS.md) and [`morph/CORRECTIONS.md`](morph/CORRECTIONS.md).

- It came out of a Layer-5 audit: of `skel`'s 133 `extra_arg subj (0,0)` violations, 43 had a
  derived subject that could not agree with its own predicate, which made the generalized test
  worth running over all ~6 000 `nsubj` edges. **Don't re-measure that population**: it stands at
  125 now, and what is left of it is a head-to-head reading disagreement (the LLM says the subject
  is dropped, a now-corrected Layer 4 says it is overt), i.e. `--fix` material, not a checker
  question. `--repair`'s `null_subject` rule would rewrite those rows to the derived position; do
  **not** run it blind, since it asserts Layer 4 is right at exactly the positions this round found
  Layer 4 could be wrong.
- **155 corrections**: 77 Layer-2 rows (archaic 1sg forms tagged 3rd person, `altri`/`quei` tagged
  plural, apocopated 3pl forms tagged singular, six words read as the wrong POS), 424 Layer-4 rows
  across 66 cantos, 2 Layer-3 spans and 1 `case` row.
- The largest family was the **elided verb of speech**: "Ed elli a me: «…»" attaches its subject
  *inside* the quotation. Normalized corpus-wide to UD's ellipsis promotion — **99 frames**, not
  only the ones agreement exposed — matching the 42 the corpus already had in that shape.
- **18 verified and left alone**, each enumerated with its reason: *constructio ad sensum*,
  plural/measure subjects with a singular verb, distributive `ciascuna`, a copula agreeing with its
  plural predicate nominal, one anacoluthon, and four lines of non-Italian text. This is the first
  standing soft residue `dep` has carried; it is a property of the text, not of the parse.
- **Layer 5's soft count rose, 3215 → 3270 (+55)** — `missing_arg` −68 against `missing_tuple`
  +105 (the promoted speech frames are predicates the LLM never proposed). Same honest reading as
  the multiple-`obj` round; see *A note on Layer 5's count* below. **Phase 5t then settled a third
  of that `missing_tuple` population by regeneration** (−31), which is what that reading predicted.

### What Phase 5s did (2026-08-07, user-run)

The route *If a next task is wanted* reserved for the user: a full-corpus `--fix` regeneration
pass, `make -C skel fix` 3-way parallel, over the 1659 units flagged at 3545. Full write-up in
[`skel/CORRECTIONS.md`](skel/CORRECTIONS.md)'s *Phase 5s*.

- **3545 → 3215 soft, −330 (−9.3%)**, 91 cantos touched. **0 units got worse and 0 were newly
  flagged**; 238 units improved, 110 cleared outright.
- **Yield 0.199 violations per LLM call — more than double Phase 5q's 0.086 and 5e's 0.11.** This
  is the first pass to beat that flat rate, and it confirms the prediction in *A note on Layer 5's
  count* below: the two populations the 2026-08-03 round added were LLM-authored artifact rows, and
  `--fix` is the instrument that settles them. `extra_tuple` moved most (−19.8%), which is exactly
  where the `adverb` bug's +72 had landed.
- **The refinement to Phase 5q's stop rule**: regeneration is exhausted against a *static* residue,
  which is what 5q measured. It is **not** exhausted after a cross-layer correction round moves the
  ground under the flagged set. `skel/PLAN.md`'s *Where Phase 5 ended* carries this qualification.

### A silent `--check` pass, closed (2026-08-07)

Found while re-measuring Phase 5s from a `git worktree` (where `src/` is unbuilt, because the
per-canticle source directories are generated, not tracked). `api.cantos()` globbed
`src/<canticle>/[0-9][0-9].txt` and returned `()` when the directory was absent, so every build and
`--check` driver — `skel`, `dep`, `np`, `case`, `morph` all share the call — iterated nothing and
printed **`0 hard, 0 soft`**, exit 0. A check that examines no cantos must not report success.
`cantos()` now raises `FileNotFoundError` naming the directory; `canticles()` is unchanged and
remains the probe for *which* canticles exist. `tests/test_api.py` pins both behaviours (5 tests).

### What the multiple-`obj` round did (2026-08-03)

The one remaining named task in *If a next task is wanted* below. Full write-ups in
[`dep/CORRECTIONS.md`](dep/CORRECTIONS.md), [`case/CORRECTIONS.md`](case/CORRECTIONS.md) and
[`skel/CORRECTIONS.md`](skel/CORRECTIONS.md).

- **A new `dep` soft check**: a predicate carrying more than one `obj` child. It flagged **203**
  predicates (not the 231 the earlier note estimated — the `case` annex's Steps 6-9 had already
  closed 28 of them). All 203 were read against their terzine and corrected: **316 row edits**,
  nothing left alone. `dep --check` 203 → **0 soft**.
  - The recurring families: later conjuncts re-attached with `conj` (88), secondary predicates over
    an object relabelled **`attr`** (63 — *not* `xcomp`, which is a `CLAUSE_HEAD_DEPRELS` member and
    would make Layer 5 derive a predicate for an adjective), reflexive clitics → `expl` (22),
    partitive/locative `ne`/`vi` → `obl` (27), clitic datives → `iobj` (9), and UD's
    promoted-conjunct + `orphan` treatment for gapping (14).
- **Eleven `case` rows corrected** — ten of them positions the retags moved into fresh contradiction
  with the annex, where the annex was the wrong side every time. `--stats` contradictions 32 →
  **31**, impossible pairings **26** unchanged.
- **A latent Layer-5 bug**: `"verb" in pos.lower()` also matches **`adverb`**, so `derive_unit`'s
  rule 2 had been promoting adverbs to predicates (plus two smaller sites). Fixed with a shared
  `is_verb_pos`.

**Layer 5's soft count went up, 3465 → 3509 → 3545**, and both moves are the checker becoming more
honest rather than a regression — see the *A note on Layer 5's count* paragraph below before
treating it as something to undo.

### A note on Layer 5's count

The standing goal is Layer 5's soft residue at **0**
([[project_skel_soft_violations_goal]]). This session's work moved it the other way, on purpose,
and the reasoning should not be re-litigated from the number alone:

- `derive_unit` reads Layer 4. Where the LLM had agreed with a **wrong** `obj`, correcting Layer 4
  turns a spurious agreement into a real disagreement (+44). `missing_arg` actually **fell** 50.
- The `adverb` bug had been inventing derived predicates that happened to match 72 LLM tuples.
  Removing it surfaces them as `extra_tuple` (+36 net).

Both populations are **`--fix` material** — LLM-authored artifact rows that no deterministic
rule can settle — and `--fix` is **user-run** work. Do not "fix" either by reverting the checker.

**This was borne out (2026-08-07).** Phase 5s ran exactly that pass and took 3545 → **3215**, at
double the per-call yield of the two prior `--fix` rounds, with `extra_tuple` — the `adverb` bug's
population — moving furthest. **Borne out again, in miniature, by Phase 5t (2026-08-09)**: the
subject-agreement round's `missing_tuple` population fell 22.1% under regeneration while the pass
as a whole returned the flat rate. The claim to carry forward is about the *population*, not the
pass: freshly created LLM-authored error is `--fix` material and settles fast; the old residue does
not move. **Phase 5u (2026-08-10) is the negative control**: rule V removed 513 violations while
creating *no* LLM-authored rows, and the following `--fix` pass returned the lowest yield ever
measured. Read the provenance of a count move, never the count.

### What Phase 5r did (2026-08-03)

The task the previous handoff wrote up — wiring the `case` annex into Layer 5's checker — landed
in full, both halves in one batch. See [`skel/CORRECTIONS.md`](skel/CORRECTIONS.md)'s *Phase 5r*
for the measurement table and the per-position record.

- **Rule U** (`_case_corroborated_role` in `dante_corpus/skel.py`, −160): a one-directional
  acceptance of a `role_mismatch` when the annex's frozen case value for the argument corroborates
  the **derived** (`dep`-side) role and *not* the given (LLM-side) one. Corroborating both or
  neither accepts nothing. `case_rows` is threaded through `validate_unit` the way
  `dep_rows`/`morph_rows` already were (`skel/skel.py`'s new `_case_rows`). Seven new tests.
  - **One gate the plan's measurement had not anticipated**: the annex is in scope for *fused*
    tokens too (`venendomi` = `verb+pronoun`, 601 of 13113 in-scope positions), where its value is
    the **enclitic's** case while a Layer-5 argument citing that position cites the **verb**.
    `_bare_pronoun_position` excludes them; it cost the rule exactly 1 of the predicted 161.
- **The 17 mirror-direction candidates**, each read against its terzina (−8 more): **ten `dep`
  retags** (four locative/partitive clitics tagged `obj`, four rows of two misassembled causative
  *fare* constructions, one clitic dative tagged `obj`, one subject tagged `obl`) and **four
  `case` corrections** (three Tuscan *ne* = *ci* read as partitive, one impossible accusative
  under a reflexive verb). **Eight left
  alone** — five of them because *a copular predicate nominal is nominative just as a subject is*,
  so the annex adjudicates nothing between `subj` and `attr`; plus one explicit-preposition case,
  one fused infinitive+clitic, one comparative standard.

By kind: `role_mismatch` 516 → **347**, `missing_tuple` 25 → **26**, everything else unchanged.
`case --stats`: contradictions 32 (unchanged), impossible pairings 28 → **26**.

### What the four batches before it did (Steps 6-9, 2026-07-31 … 2026-08-02)

The user's standing goal is Layer 5's soft residue at **0**
([[project_skel_soft_violations_goal]] — soft checks are rule mismatches to fix, not a baseline to
tolerate). Investigating the "clitic-case question" turned up that the case annex's own Step 4
(2026-07-31) had already found, and never acted on, many positions where **`case/*.tsv` itself is
wrong**. Four sessions worked through that residue, and all four named contradiction shapes are
closed:

- **Step 6**: the 50 bare-clitic (`mi ti ci vi si li` + elisions) contradictions — 1 genuine
  `dep/` mistag, 49 `case/*.tsv` errors. See `case/CORRECTIONS.md` Step 6.
- **Step 7**: the 40 "impossible pairings" (`obl`×`nominative`) and the remaining 208 named
  contradictions — mechanized the `nominative`-vs-`obj` word-order shape. **12** impossible
  pairings and **99** contradictions were `case/*.tsv` errors; **9** more were `dep/` mistags.
  Contradictions: 208→100; impossible pairings: 40→28.
- **Step 8**: the `dative`-vs-`nsubj` (8), `accusative`-vs-`iobj` (12), and `dative`-vs-`obj` (24)
  shapes — a transitivity test at each position (does the head verb already have an explicit
  object filled?). **33** `case/*.tsv` corrections and **3** `dep/` retags; **11** left alone for
  stated structural reasons. Contradictions: 100→63.
- **Step 9**: **`accusative`-vs-`nsubj`**, the last shape — all 43 candidates read individually.
  **31** `case/*.tsv` corrections to `nominative`, **0** `dep` retags, **12** left alone under
  exceptions already on record. Contradictions: 63→**32**.

**Nothing shape-driven is open.** The 32 remaining contradictions and 26 impossible pairings are
the accumulated *verified-and-left-alone* residue: every one has been read against its terzina and
left standing for a stated structural reason (accusative-and-infinitive, fused infinitive+clitic,
free relatives, causative causees, impersonal dative-experiencers, Latin quotations, comparative
standards, family F entangled). A further pass would have to re-litigate framework conventions the
corpus deliberately fixed — don't. If a *new* `case`/`dep`/`skel` error surfaces while working
something else, the standing rule below applies: fix it there, record it there.

Should another batch of per-position work come up, each batch still ends in: `case --check` still
0 hard, `dep --check` still 0/0, `pytest` still passing, and a new dated section in
`case/CORRECTIONS.md` (+ `dep/CORRECTIONS.md` for any `dep` retag) recording what was fixed, what
was verified-and-left-alone and why, and the before/after count from `case --stats`.
**Also watch for CRLF line endings**: writing TSVs with Python's `csv` module and `newline=''`
still defaults to `\r\n` — the originals are `\n`-only, so `sed -i 's/\r$//'` (or an explicit
`lineterminator='\n'`) is needed on any touched file before diffing/committing, or `git diff` will
show the whole file changed. (In-place `sed -i` edits, and a Python script that splits/joins on
`\n` and writes back with `Path.write_text` — Steps 9 and Phase 5r's method — don't have this
problem; they preserve the original line endings.)

**How `CORRECTIONS.md` is used — this is the point the user asked to be explicit about.**
`*/CORRECTIONS.md` records **corrections that were actually applied**, not a place to log "found a
problem, leaving it." If a review turns up a clear, decidable error, **fix it in the same session**
and record what was fixed and why — do not write a "known issue" entry and move on. The only
legitimate "left alone" write-ups are ones with a genuine structural reason the text itself doesn't
decide (the existing *tier-A candidates left alone* and *201 positions left alone* sections explain
this correctly: free relatives, the accusative-and-infinitive convention, Latin quotations, fused
tokens `dep` can't align component-wise) — never "this is wrong but out of scope for today." Step 5
"froze" the case annex's **regeneration and merge** questions, not its **correctness**: "frozen"
means no wholesale drop-and-rebuild (that would erase every hand correction on record), not that a
per-position error is untouchable. If a future session finds another clear `case/`, `dep/`, or
`skel` error while working something else, the same rule applies: fix it there, record it there,
don't defer it to a separate pass unless it's genuinely undecidable from the text alone.

## If a next task is wanted

**The `--fix` round against Phase 6's restructured pass is done and both stage-2 predictions
held** (see *What the Phase 6 `--fix` round did* above): `extra_tuple_adverb` −78.8%,
`extra_tuple_adjective` −54.1%, both far above the pass average, against a control of ~0% for the
three classes with no dedicated prompt. The remaining routes are assistant-side, plus a second
`--fix` round is itself now a candidate (below).

**How to measure a future `--fix` round** (the method Phases 5t/5u/5w/this round used; the whole
round arrives as modified `skel/*.tsv` in the working tree):

1. `git worktree add <scratch>/base HEAD`, then symlink each `src/<canticle>` into the worktree —
   the per-canticle source dirs are **generated, not tracked**, and `api.cantos()` now raises
   `FileNotFoundError` rather than silently checking nothing.
2. Run `uv run skel.py inferno purgatorio paradiso --check` in both trees, saving the output.
3. Diff at the **parse-unit** level (`dep.sentence_groups`, which is what `--fix` regenerates), by
   mapping each `<canticle> <canto>:<line>` violation to its unit's first line: units flagged
   before/after, improved, cleared, **got worse**, **newly flagged**. Zero on the last two has held
   for six consecutive rounds and is Phase 5c's acceptance criterion.
4. Per-call yield = violations removed ÷ units flagged before (`skel.log` is left empty by the
   parallel invocation, so the flagged-unit delta is the only available lower bound on accepted
   units — don't look for a per-unit count).
5. **Classify at `_violation_subclass` granularity, not `--check`'s coarse kind** — the
   POS-keyed split (`extra_tuple_adverb`/`extra_tuple_adjective`/`missing_tuple_nominal`) is what
   `_CLASS_PROMPTS` is actually keyed by, and this round's finding only showed up at that level;
   the coarse `extra_tuple` number would have hidden the 78.8%-vs-54.1% split entirely.

**Read the per-class (subclass) table before the pass-level number** — this round is the sharpest
case yet: a −27.8% pass average concealed a −78.8% move in the class with a dedicated prompt and
~0% in the three with none. Score each intervention against *its* population, never against the
pass.

**A fresh `--fix` round is now itself a live option**, since 259 units cleared and 197 more
improved — a materially different flagged set than any prior round measured against. Prior
practice (Phase 5s/5t) found that a changed flagged set can raise the *next* pass's yield when it
contains freshly-created LLM-authored rows; whether that applies here (this round's residue is
mostly *un*-touched, not newly authored) is unmeasured. Run one and read the subclass table if so.

The open routes, all assistant-side. **Three of the four routes the previous handoff listed are
closed** — rule Y took the copular-clause-head route (−8, not the 43 its class count promised),
rule Z absorbed the `per`+infinitive route by generalizing past the preposition (−77), and rule AF
answered the `membership` question (47 → 8). What is left:

- **Attributive vs predicative adjectives (17 `extra_tuple_adjective`, down from 37).** *"non fur
  mai persone **ratte** / a far lor pro"* (inferno 2:109): Layer 4 attaches the adjective `amod`
  inside the subject NP, the LLM promotes it to a predicate of its own. Unlike rule Y's
  population there is **no `cop` edge** — nothing in the tree asserts a predication — so this is
  a genuine reading disagreement, not checker silence. The dedicated prompt moved it −54.1% in
  one round; whether the residue is a checker question (like `membership`) or keeps yielding to
  regeneration is worth a per-position read of the 17 before writing a checker rule.
- **Adverbs promoted to predicates (7 `extra_tuple_adverb`, down from 33).** Nearly closed by the
  dedicated prompt (−78.8%); a per-position read of the last 7 is now cheap and would settle
  whether any residue is genuine or a further prompt tweak would clear it.
- **Stacked prepositions in Layer 4 (14 `role_mismatch`).** Phase 6 measured this class and
  **took the decidable 4 of it**: where Layer 4 chains *"in su"* (`in` → `su` → argument), both
  lemmas sit in the argument's `case` chain and the `prep_stack` rule normalizes onto the derived
  side. What remains is **18 positions where the LLM names a preposition the tree does not carry
  at all** — Layer 4 writes *"in su"* flat in some places and chained in others, so the two sides
  differ about what is *attached*, not about what to call it. That is still a `dep/`
  normalization round, and it is still the only *checker/Layer-4* route on the list.
- **The `missing_arg obl` bucket.** Still the single largest sub-class after the two subject
  buckets, and never classified. A per-position read of a sample is the cheap first move.

**A per-position read has now produced a rule four times running, and the residue classification
has mispredicted it every time.** Rules W and X were absent from the route list; rules Y-AF
inverted it — the route ranked first was worth 8 and the route ranked last, generalized, was worth
77, while the two biggest rules (AB, Z) described shapes no classification had named; rule AG
(Inferno 4-6, −43) was also off the list — the `missing_arg obl` bucket above had been ranked as
the cheap next move, and the rule that actually fired was a `subj`-side agreement gate. The
classification tells you where the volume is; a per-position read tells you *which rule declined to
fire*. **Two shapes rule AG's write-up flagged but did not generalize** (only one instance each in
the Inferno 4-6 sample) are candidates for the next read: an adverb-headed oblique with a nested
`nmod` (*"dinanzi al cristianesmo"*) where Layer 4 attaches the adverb itself and the LLM cites
only the nested noun, and a locative clitic (`v'`/`ci`) tagged `advmod` rather than `obl`. Run the
read on **Inferno 7-9** next, not another statistics pass.

Past those, the standing goal of 0 soft violations needs a *new instrument* against the two big
reading-disagreement classes — and the candidate this project has identified there (an imported
verb-valency lexicon) is declined on neutrality grounds; see *Out of scope*.

## Status

**All five layers are implemented, built for all 100 cantos, and merged to `main`.** Layer 5's
checker was refined through Phases 0-5r and rules V through AG, and its soft residue is **1409**
(down from
17438 at the
first full-corpus measurement; Phase 5r's rule U and its hand round took it to 3465, Layer 4's
multiple-`obj` round plus the `adverb` bug fix moved it back up to 3545 — see the handoff's *A note
on Layer 5's count* — Phase 5s's user-run `--fix` pass took it to 3215, the subject-agreement
round moved it to 3270, Phase 5t's user-run `--fix` pass took it to 3136, rule V plus the
membership audit took it to 2623, Phase 5u's user-run `--fix` pass took it to 2531, and Phase 5w's
user-run `--fix` pass on the prompt Phase 5v rewrote took it to 2408, rules W and X took it to
2330, and rules Y-AF plus the Inferno 1-3 cross-layer corrections took it to 2084, Phase 6's
deterministic `--fix` stage took it to 2011, the first user-run `--fix` round against Phase
6's restructured stage 2/3 driver took it to 1452, and rule AG plus the Inferno 4-6 cross-layer
correction took it to 1409) — every
route the
Phase
5 plan opened has a measured verdict
(see
[`skel/PLAN.md`](skel/PLAN.md)'s *Where Phase 5 ended*). See *The layers* below and
[`skel/README.md`](skel/README.md) for the design and current status.

**The pronoun case annex is complete and closed (2026-08-02).** It is a permanent Layer-2 sibling
extension, `case/`, on the same footing as `np/`, `dep/` and `skel/` relative to `morph/` — not a
new `morph/*.tsv` column, decided at the annex's close after two budgeted blind-regeneration
rounds were measured and rejected against a verdict rule fixed in advance. See
[`case/README.md`](case/README.md) for the design and current status and
[`case/CORRECTIONS.md`](case/CORRECTIONS.md) for the full measurement history, including *Step 5 —
the merge decision*.

**No route is blocked on the user; the routes that remain are assistant-side** (see *If a next
task is wanted*). All five layers plus the case extension are implemented, built for all 100
cantos and merged to `main`. The first `--fix` round against Phase 6's restructured driver
generalized Phase 5w's finding again, more sharply: a prompt rule moves its class only when it
reaches the model at the flagged position — the two POS-keyed prompts built for this round moved
their classes −78.8% and −54.1%, the three classes with no dedicated prompt moved near zero.
Further prompt work is worth doing only with a hint attached; the volume is in the routes listed
there.

- **Layer 1 — Tokens**: implemented (`dante_corpus/tokenizer.py`, served via `Line.tokens`).
- **Layer 2 — Morphology + lemma**: implemented; see [`morph/README.md`](morph/README.md).
  Artifacts are built for all 100 cantos. Its pronoun-case feature is served separately, as the
  permanent Layer-2 sibling extension `case/` — see [`case/README.md`](case/README.md).
- **Layer 3 — Noun phrases**: implemented; see [`np/README.md`](np/README.md). Build
  driver `np/np.py`, served via `Canto.np()` and `dante-corpus text np`. Artifacts generated for
  all 100 cantos. `--check` reports **0 hard / 0 soft** — see
  [`np/README.md`](np/README.md)'s *Check* section and [`np/CORRECTIONS.md`](np/CORRECTIONS.md).
- **Layer 4 — Dependency / grammatical role**: implemented and complete; see
  [`dep/README.md`](dep/README.md). Build driver `dep/dep.py`, served via `Canto.dep()` and
  `dante-corpus text dep` (with `text np` gaining a derived `role=` per noun phrase). Artifacts
  built for all 100 cantos; `--check` reports **0 hard / 18 soft** violations, the
  subject-agreement rule's verified-and-left-alone residue — see
  [`dep/README.md`](dep/README.md)'s *Check* section and
  [`dep/CORRECTIONS.md`](dep/CORRECTIONS.md) for the full correction history.
- **Layer 5 — skeleton**: implemented, all 100 cantos built, checker refined through Phases 0-5r
  — the four mechanical phases (normalization, authority model, `--repair`,
  double-listing/elided-copula whitelist) plus Phase 5's rule series, 5r's rule U, which reads the
  `case` annex as a third opinion on a disputed argument role, rule V, which supplies the
  control/participial subject of a non-finite predicate, and the Y-AF series, which closes eight
  further shapes where the derivation was silent rather than disagreeing; see
  [`skel/README.md`](skel/README.md). `dante_corpus/skel.py` (dataclasses, role
  vocabulary, deterministic derivation, table parsing, validation, TSV I/O, serve-time joins),
  `dante_corpus/hashes.py` (content-hash versioning, all layers), `Canto.skel()`/`Canto.hashes()`
  in `api.py`, `dante-corpus text skel`/`dante-corpus hash` in `cli.py`, `skel/skel.py` (LLM
  build driver, mirrors `dep/dep.py`, plus `--stats`/`--repair` modes). `--check` across all
  three canticles reports **0 hard, 1409 soft** (down from 17438 at the first full-corpus
  measurement) — see [`skel/README.md`](skel/README.md)'s *Check* section and
  [`skel/CORRECTIONS.md`](skel/CORRECTIONS.md) for the full correction history, including the
  case annex's contribution to that count. Phase 5 (see [`skel/PLAN.md`](skel/PLAN.md)) is
  **complete**: its measured finding is that `--fix` yields a flat ~0.09-0.11 violations per LLM
  call on a *static* residue however that residue is composed, so the bulk of the reduction came
  from deterministic checker rules and cross-layer corrections instead. **Phase 5s (2026-08-07)
  qualified that**: the same instrument returned 0.199 per call when run right after a cross-layer
  round had changed what the flagged set contains. **Phase 5t (2026-08-09) narrowed the
  qualification**: after a *smaller* such round it returned 0.085 — the flat rate — because the
  high yield belongs to the newly created population, not to the pass, and dilutes with that
  population's share of the flagged set. **Phase 5u (2026-08-10) settled the shape of the rule**:
  after rule V — a cross-layer round of 513, but one that *created* nothing, being a checker
  acceptance — it returned 0.068, the lowest on record. What raises the yield is a preceding round
  that added LLM-authored rows to the flagged set, not the size of the violation move.
  **Phase 5w (2026-08-12) generalized it past provenance**: run on a *rewritten prompt* rather than
  a changed flagged set, it returned 0.095 — the flat rate again — while the single class whose
  instruction had been rewritten with a worked example and a per-violation `--fix` hint fell 28.6%.
  A pass moves a class when something about *that class* changed since the last pass; the pass
  average is that move diluted by everything that did not.
  **Phase 6 (2026-08-12) restructured `--fix` itself** — deterministic repairs first, then one
  narrow question per violation *class* instead of one monolithic prompt per whole unit, with
  partial credit kept class by class — and its first user-run round (2026-08-13) confirmed the
  rule at the sharpest resolution yet: the two POS-keyed classes built for it moved −78.8% and
  −54.1%, the classes with no dedicated prompt moved near zero, in the same pass.
  `--fix` rounds are **LLM-regeneration work
  the user runs themselves** (`make -C skel fix`, run 3-way parallel); checker-side and audit
  work is the assistant's.

`grammar-stack-plan` was merged into `main` (fast-forward) and pushed; Layers 1–4 and their
artifacts now live on `main`.

## Why this lives in the corpus

`dante-corpus` is the queryable, **canon-neutral source of truth** for the *Commedia*: it serves
the normalized Italian text, the token stream, and the nested quote-span tree, all derived from
the poem itself with no external ontology. Today it stops at tokens and quotes.

Downstream projects each need to *read the source grammatically* before they can do their own
work — the formalization layer (`dante-analyze`) to extract entities and relations, the
translation layer (`dante-dravidian`) to align tokens to a reference. Both currently re-derive
the same morphosyntax from scratch, in their own prompts, every time. That re-derivation is not
project-specific: **the grammar of an Italian line is the same regardless of what you do with
it.** So it belongs here, computed once, and served like any other corpus asset.

The line that keeps this in the corpus — rather than letting it drift into an interpretation
engine — is a strict **asymmetry**:

> The corpus **enumerates and annotates** what the text's own grammar determines.
> Consumers **decide, normalize, and bind to external references** on top of that.

Everything in this plan is recoverable from the Italian source alone. Nothing here looks at a
reference translation, a knowledge-graph goal, or any external canon. The contested judgments —
*is this noun phrase an entity? which closed relation is this verb? is this a simile? what is the
English equivalent?* — are deliberately **not** computed here; they are the consumers' jobs (see
*Out of scope* below). This keeps the corpus reproducible and neutral while still removing the
duplicated reading.

## The layers

Five layers, each a function of the source text. All five are implemented and built for all 100
cantos. Examples use *Inferno* I.1–6.

```
1  Nel mezzo del cammin di nostra vita
2  mi ritrovai per una selva oscura,
3  ché la diritta via era smarrita.
4  Ahi quanto a dir qual era è cosa dura
5  esta selva selvaggia e aspra e forte
6  che nel pensier rinova la paura!
```

### Layer 1 — Tokens *(implemented — no new work)*

The token stream already produced by `dante_corpus/tokenizer.py` and served via `Line.tokens`.
This is the deterministic foundation every higher layer cites and checks against; it needs no
further design. Its unit already matches what the morphology layer expects: it splits
apostrophe-linked elisions (`ch'` `i'`), keeps prepositional contractions whole (`Nel`, `del`),
and excludes punctuation (`has_alpha`).

- `mi` `ritrovai` `per` `una` `selva` `oscura` …
- **Generation**: deterministic (`tokenizer.py` over the normalized `src/`).
- **Check**: each token is a verbatim, in-order substring of its source line.

### Layer 2 — Morphology + lemma *(implemented — see [`morph/README.md`](morph/README.md))*

Per-token lemma, part of speech, and morphological features (gender, number, person, tense, mood),
plus a note for contraction / apocope / elision — generated from the Italian alone at build time,
aligned 1:1 to the Layer-1 tokens, and frozen as TSV. This is the first layer that removes
duplicated reading: the translation layer (`dante-dravidian` Step 1) currently regenerates the same
morphology inline; this is what it would consume instead. A prior local-LLM experiment produced
exactly this table from the source with no reference, evidence the layer is intrinsically
recoverable.

The mechanics — columns, generation rules, the token-alignment algorithm, validation tiers, and
usage — live in [`morph/README.md`](morph/README.md). It is served via `Canto.morph()` and
`dante-corpus text morph`.

**Pronoun case** is served as a Layer-2 morphological feature — the one this layer's own columns
omit — but held in its own permanent sibling directory rather than a `morph/*.tsv` column, so no
existing artifact hash moves. See [`case/README.md`](case/README.md) for the design, scope, and
vocabulary, and [`case/CORRECTIONS.md`](case/CORRECTIONS.md) for why a sibling directory over a
merged column.

### Layer 3 — Noun-phrase enumeration *(implemented — see [`np/README.md`](np/README.md))*

Every noun phrase in the line, with its head, source span, and modifiers — enumerated
**exhaustively and over-inclusively**. The corpus does **not** decide whether an NP is an entity;
it lists every candidate so consumers can decide. Each NP is frozen as a contiguous Layer-1 token
range (`start`/`end`) with a `head` token index and verbatim `text`; nesting is derived by span
containment at serve time. Served via `Canto.np()` and `dante-corpus text np`.

- `[nostra vita]` · `[una selva oscura]` · `[la diritta via]` · `[esta selva selvaggia e aspra e
  forte]` · `[la paura]`
- **Generation**: LLM shallow parse at build time, frozen. Nesting (e.g. `mezzo del cammin di
  nostra vita`) is represented explicitly; over-inclusion is correct behaviour, not noise.
- **Check**: each NP span reproduces a verbatim source substring; the head token lies within the
  span.
- **Scope**: NP spans are **single-line** by design (each is a verbatim substring of one source
  line), so an enjambed phrase appears as its per-line pieces and is rejoined by layer-4
  attachment. Bare clitic and relative pronouns are **not** NPs — they are layer-1/2 tokens that
  receive their clause function in layer 4.

### Layer 4 — Dependency / grammatical role *(implemented — see [`dep/README.md`](dep/README.md))*

Each token tagged with its function in the clause (a Universal Dependencies relation) and the head
it attaches to — `[la diritta via]` = subject of `era smarrita`; `che` (l.6) = relative pronoun,
subject of `rinova`, antecedent `[esta selva …]`. Attachment may cross line boundaries, which is
what rejoins layer-3's single-line enjambed NP pieces; bare pronoun tokens (deliberately not
layer-3 NPs) each carry a role and a head here, making every pronoun mention enumerable. The
mechanics — parse units, index-citing generation, validation tiers, and usage — live in
[`dep/README.md`](dep/README.md). It is served via `Canto.dep()` and `dante-corpus text dep`.

### Layer 5 — Predicate-argument skeleton *(implemented — see [`skel/README.md`](skel/README.md))*

Predicate ↔ argument tuples binding layers 2–4 into bare propositions, citing **token
positions**, not raw text or lemmas — `[la diritta via]` = subject of `smarrita`; `che` (l.6) =
relative pronoun, subject of `rinova`, antecedent `[esta selva …]` (derived at serve time via
`skel.antecedent`, not stored). This is the *raw* skeleton only: **no semantic frame, no
coreference, no vocabulary normalization.** Role labels are **UD-derived**
(`subj`/`obj`/`iobj`/`attr`/`xcomp`/`ccomp`/`obl:<preposition lemma>`), not semantic, so they
stay directly comparable with the deterministic derivation below and the vocabulary stays
canon-neutral.

Unlike Layers 2–4, **the LLM authors the artifact but a deterministic derivation is the
checker**: `derive_unit` in `dante_corpus/skel.py` computes the same predicate-argument
structure mechanically from the frozen Layers 2–4, and the LLM proposes its own, independent
reading of the same parse unit (it is **not shown** the Layer-4 parse). Soft checks report every
divergence between the two. A purely deterministic Layer 5 would just be `f(dep)` and could
never disagree with Layer 4; giving the LLM an independent read means a divergence can surface
a genuine Layer-4 mis-parse, not just an LLM slip — Layer 5 doubles as an audit of Layer 4,
triaged with the same measure-then-freeze discipline as `dep/CORRECTIONS.md`. The mechanics —
parse units, table format, the derivation, the divergence-normalization/authority-model/
`--repair` checker phases, and usage — live in [`skel/README.md`](skel/README.md). It is served
via `Canto.skel()` and `dante-corpus text skel`.

## Out of scope — consumer responsibilities

These are intentionally absent from the corpus because they are not determined by the text's own
grammar; they are contested judgments, normalizations, or bindings to something external. Listing
them fixes the boundary:

- **Entity-hood and entity typing** — which layer-3 noun phrases are entities, and of what kind.
  (A formalization-layer judgment, frozen against that project's own evidence-derived vocabulary.)
- **Coreference / referent identity** — linking pronouns, pro-drop subjects, and epithets to a
  single referent. (Reading-bound interpretation; belongs to the consumer.)
- **Closed relation vocabulary** — mapping a layer-5 predicate onto a frozen relation set.
- **Frame** — literal / simile / prophecy / reported. (Interpretive.)
- **Reference equivalents and truth-conditions** — any alignment to an English (or other) reference
  translation. (Translation-layer concern; brings external canon and must not enter the corpus.)
- **An imported verb-valency lexicon** — the instrument that would settle Layer 5's remaining
  complement-vs-adjunct disagreements (`essere`/`stare`/`parere` as copulas, and the ~37 lemmas
  behind the residual `advcl` cases). Rejected on the same grounds: it is an external authority,
  not something the Italian line determines. Note the contrast with the case extension
  ([`case/README.md`](case/README.md)), which asks a model to *read* the source rather than
  importing a dictionary, and so satisfies the *Neutrality audit* invariant below.

## Build & serve model

Mirror the existing `quotes/` pipeline exactly: a build step generates each layer, the result is
**committed**, and the package then **serves it deterministically** through the `dante_corpus`
API. The LLM is a build-time tool whose output is frozen and round-trip-checked — consumers see a
stable, reproducible asset, never a live model call. This follows the *measure-then-freeze*
discipline already used for normalization and quotes.

- **Artifact**: one structured file per canto per layer, under its own directory. Rectangular
  layers freeze as TSV (Layer 2 → `morph/<canticle>/NN.tsv`, one line-numbered row per token);
  layers with nesting may use another structured form. Layers join by token order; whether later
  layers share a file or stay in sibling directories is decided per layer.
- **Versioning**: every canto×layer artifact is **content-addressed** — the serve API exposes a
  content hash alongside the data, so a consumer can record exactly which parse a derived artifact
  annotated and recompute only what a regeneration actually changed (granular invalidation, per
  `dante-analyze`'s REARCHITECTURE.md). Regenerating one canto changes only that canto's hash;
  nothing else downstream is invalidated.
- **Build driver**: each LLM-built layer's generator lives in its own step directory (Layer 2 →
  `morph/morph.py`, the reference implementation) and is **resumable from its own output** — every
  chunk's rows are written back to the artifact as soon as they validate, so an interrupted run
  skips already-committed lines and re-requests only the remainder. Progress is shown live through
  `llm7shi.statusline` (Rich) — a per-canto bar (`canticle canto/total |
  line/total …`) with the model's streamed output routed through the same console.
- **Output routing convention** (shared across all LLM build drivers): the `StatusLine` object
  (`ui`) is the single output channel throughout the build flow. `ui.log()` is used for status
  messages (skip, resume, wrote); `ui.stream` is passed as `file` to the `llm7shi.Client` so
  streamed LLM tokens flow through the same console; `ui.stream.error()` is used for error
  messages (attempt failures, giving up) so they appear in red and are visually distinct from
  normal progress output. All future layer drivers follow this same convention.
- **Multi-turn recovery** (shared pattern): the `llm7shi.Client` maintains a conversation session,
  enabling two-stage recovery when a local model fails to produce a complete response in one turn.
  First, split output is repaired before alignment (e.g. `_merge_tables()` in Layer 2 merges
  consecutive pipe-tables into one). Second, if the aligned result still has lines with fewer
  elements than expected, a follow-up turn on the same session asks the model to supply the missing
  content, and the result is concatenated before retrying. These two stages — structural repair
  then continuation — are the standard recovery pattern for all LLM-built layers.
- **API**: extend the corpus query surface (alongside `text tokens`, `quote show`) with each
  grammatical layer, addressable by canticle / canto / line range (Layer 2: `Canto.morph()` /
  `dante-corpus text morph`).
- **Strongest reader for the hard layers**: morphology (L2) is robust; NP/dependency/skeleton
  (L3–L5) are reading-bound and should use the strongest available model at build time, measured
  before freezing.

## Validation

- **Per-layer checks** (above) run over all 100 cantos; zero round-trip failures is the structural
  bar, exactly as for `quotes/`.
- **Closed tag/role sets**: features (L2) and roles (L4) validate against frozen vocabularies, so a
  drift in the build model is caught rather than silently absorbed.
- **Neutrality audit**: the build prompt for every layer takes only the Italian source as input —
  no reference translation, no entity list, no canon. This is the invariant that lets two very
  different consumers share one parse.

## Sequencing

1. **Layer 2 (morphology + lemma)** — *implemented* (`dante_corpus/morph.py` + `morph/morph.py`). Lowest risk,
   already shown feasible intrinsically, and immediately useful as a lemma-queryable index.
2. **Layer 3 (noun phrases)** — *implemented* (`dante_corpus/np.py` + `np/np.py`). The census/entity
   substrate consumers most want.
3. **Layer 4 (dependency)** — *implemented* (`dante_corpus/dep.py` + `dep/dep.py`). The syntactic
   spine that rejoins enjambed NPs and makes pronoun mentions enumerable.
4. **Layer 5 (skeleton)** — *implemented* (`dante_corpus/skel.py` + `dante_corpus/hashes.py` +
   `skel/skel.py`), all 100 cantos built, checker refined through Phases 0-5r plus rules V, W,
   X and the Y-AF series and AG, with `--fix` restructured in Phase 6 and its first round run
   (`--check`: 0 hard / 1409 soft). Phase 5 closed with every route measured; see
   [`skel/PLAN.md`](skel/PLAN.md) and [`skel/README.md`](skel/README.md).
5. **Pronoun case extension** — *complete and closed, 2026-08-02*
   (`dante_corpus/case.py` + `case/case.py`; [`case/README.md`](case/README.md),
   [`case/CORRECTIONS.md`](case/CORRECTIONS.md)). Not a sixth layer: a
   Layer-2 morphological feature held in its own **permanent** directory, useful to consumers on
   its own terms independently of Layer 5's violation count. See [`case/README.md`](case/README.md)
   for the full status.

Build alongside the existing assets, gate each layer on its checks, then expose through the API.
Layers 1–5 are implemented, built for all 100 cantos, and merged to `main`; the grammatical
stack this plan describes is complete. **The pronoun case extension is also complete and closed**,
merged to `main`.
