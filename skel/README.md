# skel — Layer 5: predicate-argument skeleton

Predicate ↔ argument tuples binding Layers 2-4 into bare propositions, citing **token
positions**, not raw text or lemmas — the next layer of the grammatical stack
([`../PLAN.md`](../PLAN.md)) after dependency parsing. This is the *raw* skeleton only: **no
semantic frame, no coreference, no vocabulary normalization.** Role labels are **UD-derived**
(`subj`/`obj`/`iobj`/`attr`/`xcomp`/`ccomp`/`obl:<preposition lemma>`), not semantic, so the
LLM's roles and the derivation's roles are directly comparable and the corpus stays
canon-neutral.

**Status: built for all 100 cantos, checker refined through Phase 5r, six full `--fix` rounds
run (Phases 5e, 5q, 5s, 5t, 5u and 5w), and five Layer-4 correction rounds (Phases 5i, 5n, 5p's two and 5r)
fed back into `dep/`.**
`make -C skel check`: **0 hard, 2408 soft** violations (down from 17438 at the first
full-corpus measurement, 7776 at the Phase 4a checkpoint, 5919 after the Phase 4b `--fix` round,
5105 after Phase 5a, 4846 after Phase 5b, 4615 after the Phase 5e `--fix` round, 4327 after
Phase 5f, 4097 after Phase 5g, 4068 after Phase 5h, 4042 after Phase 5i, 3924 after Phase 5j,
3876 after Phase 5k, 3808 after Phase 5l, 3746 after Phase 5m, 3725 after Phase 5n, 3712 after
Phase 5o, 3702 after Phase 5p, 3551 after Phase 5q and its `ioj` typo fix, 3635 after the `case`
annex's own Layer-4 corrections (see [`CORRECTIONS.md`](CORRECTIONS.md) and
[`../case/CORRECTIONS.md`](../case/CORRECTIONS.md)), and 3634 after the one `dep` fix in the
`case` annex's Step 6 clitic round, 3633 at the close of that annex's Steps 7-9, 3473 after Phase
5r's rule U, 3465 after that phase's hand-verified `dep`/`case` round, 3509 after Layer 4's
multiple-`obj` round moved it *up* again, 3545 after the `"verb" in pos` bug fix, 3215 after
Phase 5s's user-run `--fix` pass, 3270 after Layer 4's subject-agreement round moved it *up*
once more, 3136 after Phase 5t's user-run `--fix` pass, 2623 after rule V's
control/participial subject chain and the membership audit's cross-layer corrections, 2531
after Phase 5u's user-run `--fix` pass, and 2408 after Phase 5w's user-run `--fix` pass on the
prompt Phase 5v rewrote). See
[`../PLAN.md`](../PLAN.md) for the current authoritative count.
See
[skel/CORRECTIONS.md](CORRECTIONS.md) for the full
correction history. `--fix` regeneration improves **8.7%** of the units it attempts (178 of
2037 in the Phase 5e round, ~0.11 violations per LLM call) and that rate did not improve once
the deterministic phases had cleared the unfixable units out of the flagged set — Phase 5q
measured 0.086 per call on a residue nine rules further along, the same flat figure. So more
model calls do not close a *static* residue. **Phase 5s qualified that**: run after Layer 4's
multiple-`obj` round and the `"verb" in pos` bug fix had changed what the flagged set contains,
the same instrument yielded **0.199 per call** (−330, 0 units worse, 0 newly flagged).
**Phase 5t narrowed the qualification**: the same experiment after Layer 4's subject-agreement
round returned **0.085 per call** (−134), back at the flat rate — because what a cross-layer round
buys is a *sub-population* regeneration settles fast (5t's `missing_tuple` fell 22.1% against a
4.1% pass average), and the pass-level yield is that rate diluted by the rest of the flagged set.
Judge a pass by how large the newly created population is relative to the flagged set (see
[PLAN.md](PLAN.md) and *Next steps*).

## What it does

Unlike Layers 2-4, this layer's artifact is LLM-authored but **checked by a deterministic
derivation**: one LLM pass per parse unit (the same sentence-grouped units as Layer 4, see
`dep.sentence_groups`) proposes, independently, a Markdown table listing every predicate token
and its arguments — the model is deliberately **not shown the Layer-4 parse**, so its reading is
its own. `derive_unit` (`dante_corpus/skel.py`) computes the same predicate-argument structure
*mechanically* from the frozen Layer 2-4 artifacts, and `validate_unit`'s soft checks report
every place the LLM's tuple set diverges from that derivation. A purely deterministic Layer 5
would just be `f(dep)` and could never disagree with Layer 4; giving the LLM an independent read
means a divergence can surface a genuine Layer-4 mis-parse, not just an LLM slip — Layer 5
doubles as an audit of Layer 4, triaged with the same measure-then-freeze discipline as
[`dep/CORRECTIONS.md`](../dep/CORRECTIONS.md).

Worked example, Inferno I.1-9 (verified by hand against the frozen `dep`/`np`/`morph` artifacts;
reproduced exactly by `derive_unit`, see `tests/test_skel.py::test_derive_unit_inferno_1_1_9`):

- `ritrovai` (2.2): `subj = ∅` (pro-drop), `obl:in = [mezzo del cammin di nostra vita]` (1.1),
  `obl:per = [una selva oscura]` (2.1)
- `smarrita` (3.6): `subj = [la diritta via]` (3.1)
- `rinova` (6.4): `subj = che` (the relative pronoun token itself — its antecedent, `[esta selva
  selvaggia e aspra e forte]`, is *derived*, not stored, via `skel.antecedent`), `obj = [la
  paura]` (6.2), `obl:in = pensier` (6.1)

Each tuple is addressable by a stable id (`<line>.<ordinal>` in line order, mirroring Layer 3's
NP ids, derived at serve time via `skel.tuples_canto`), so a consumer artifact can **cite** a
skeleton tuple rather than paraphrase it.

## Output

`skel/<canticle>/NN.tsv` — one tab-separated row per (predicate, argument) pair: `line  token
word  role  arg_line  arg_token`. `arg_line=0, arg_token=0` marks pro-drop ∅ or a zero-argument
predicate. A `token=0` sentinel row (empty `word`/`role`, `0 0`) marks a whole line with no
predicates. Example (`skel/inferno/04.tsv`):

```
line	token	word	role	arg_line	arg_token
1	1	Ruppemi	subj	2	3
1	1	Ruppemi	obj	1	4
1	1	Ruppemi	obl:in	1	7
4	6	mossi	subj	0	0
```

## Check

`--check` validates every committed artifact with **no model call** (`validate_unit`):

- **Hard** (the structural bar): the predicate token exists in Layer 1 and every argument
  position is a valid in-unit token position or the `(0,0)` sentinel. `0 hard` is required
  before an artifact is trusted.
- **Soft** (reported, not enforced; measure-then-freeze): an argument citing a nominal role must
  be a Layer-3 NP head, a Layer-1 pronoun token, or an in-unit predicate (clausal argument); and,
  the central check, every divergence from `derive_unit`:
  `missing_tuple`/`extra_tuple`/`missing_arg`/`extra_arg`/`role_mismatch`.

Eleven refinements make that divergence check meaningful rather than noisy — landed as
successive phases, each measured before/after (`--stats` aggregates violations by kind, by
`(kind, role, ∅-or-real)`, and by `role_mismatch` pair):

1. **Normalization layer** (`_canonicalize_role`/`_normalize_prep_lemma`, applied to both sides
   before comparison): preposition-lemma orthographic variants (`sanza`/`sovra`/`de`/... →
   `senza`/`sopra`/`di`/...), the `attr`≡`xcomp` and `iobj`≡`obl:a` labeling splits, and
   clausal-complement double-listing (a `ccomp`/`xcomp` the LLM lists as its own tuple instead of
   also citing as its matrix predicate's argument) — all label-level equivalences, not
   disagreements about the parse.
2. **Authority model** (`_apply_subj_authority`): makes the `subj` slot LLM-authoritative
   (validated against a candidate set, not exact-matched) in exactly three mechanically
   underdetermined cases — pro-drop antecedents (`derive_unit` says ∅, any concrete subject the
   LLM cites is accepted), non-finite ∅ (LLM marks ∅ on an infinitive/gerund `derive_unit`'s
   pro-drop rule doesn't cover), and the control/participial subject of a non-finite predicate
   (**rule V**, `_control_subject_candidates`, 2026-08-09). `derive_unit` reads a predicate's own
   dep children, so a non-finite predicate with no `nsubj` child gets no `subj` row at all — it is
   silent, not asserting the predicate has no subject. Rule V walks the dep head chain and accepts
   an LLM-proposed subject that is the `subj`/`obj`/`iobj` of any ancestor up to the first one that
   has a subject of its own (control and raising through a chain of subjectless links, including
   the causative's dative causee), or the nominal an `acl` participle modifies. If the walk reaches
   a matrix whose own subject is pro-drop ∅, the controller is unresolved and any resolution is
   accepted, as in the first case. Every other role, and `subj` where `derive_unit` resolves a real
   subject, stay exact-match.
3. **`--repair`** (`Repair`/`_find_repairs`/`_safe_role_repair`): for the subset of divergences
   the dep tree fully determines, mechanically rewrites the committed TSV — no model call — two
   conservative rules, both sourced from the checker's own violation list (so the authority model
   above automatically gates what's eligible):
   - **null_subject**: a `missing_arg subj` (derived a real subject from an explicit `nsubj`
     edge) paired with an `extra_arg subj (0,0)` (the LLM wrote pro-drop ∅) for the same
     predicate — the ∅ citation is replaced with the derived one.
   - **role_label**: a `role_mismatch` where the given role is bare `obl` and the derived role is
     `obl:<lemma>` (the dep tree's `case`-child detection) — the role cell is rewritten.
   - Genuine disagreements (`subj`/`obj` reversals, `iobj`/`obj` reversals, cross-lemma `obl`
     pairs) are deliberately excluded from both rules and left for hand/LLM triage.
4. **Phase 4a — double-listing + elided-copula whitelist** (`_classify_divergence`, gating the
   `extra_tuple` set): a predicate nominal/adjective double-listed as both another predicate's
   `attr`/`xcomp` argument *and* its own redundant predicate tuple is suppressed (extends Phase
   1's `ccomp`/`xcomp` double-listing suppression to `attr` and to `extra_tuple`); separately, a
   predicate nominal with **no verb token at all**, coordinate or apposed to a real clause (dep
   deprel `conj`/`appos`/`attr` — e.g. "mantoani per patrïa ambedui") is exempted as a genuine
   elided-copula reading `derive_unit` structurally can't produce. Deliberately narrower than a
   blanket "non-verb POS" rule: the majority of non-verb `extra_tuple` predicates (dep deprel
   `amod`/`advmod`/`obj`/`nsubj`/`nmod`) are NP-internal modifiers the LLM wrongly promoted to
   predicate status — genuine errors, left flagged for `--fix`, not swallowed by the whitelist.
5. **Phase 5a — coordination + `nmod`-oblique normalization** (`_collapse_coordination` /
   `_drop_nmod_obliques`, applied to the argument maps after the authority model, before the
   diff): every argument citation is collapsed onto its coordination head by walking `conj`
   edges up, on **both** sides ("si ciberà di terra e di sapïenza" — the LLM lists both
   conjuncts, `derive_unit` reads only a predicate's direct dep children and sees the first
   alone); and an `obl`/`obl:<prep>` whose argument is an `nmod` dependent of one of the same
   predicate's own derived arguments is accepted ("ha *bisogno* **di te**"). Both are
   notation-convention equivalences like Phase 1's, not new derived rows — emitting a derived
   row per conjunct instead was measured at net −2 (`extra_arg` −554 against `missing_arg` +529),
   because the LLM's own enumeration of coordinations is inconsistent. Roles are preserved, so a
   genuine role disagreement on a conjunct still surfaces.
6. **Phase 5b — three classes the re-triage isolated**: (a) `derive_unit` no longer promotes a
   **coordinating conjunction** to predicate status via its `conj` rule — Layer 4 routinely
   attaches a line-initial `E`/`Ma` to the previous clause head, and a function word is never a
   predicate (gated on Layer-2 POS, so gapped predicates of other POS stay derived); (b) a given
   predicate that is an `aux`/`cop` whose head `derive_unit` derived as the predicate is
   suppressed (`_aux_head`) — "Molti *son* li animali", the copula/modal double-listing, same
   shape as the Phase 4a `attr`/`xcomp` rule; (c) an `obl`/`obl:*` citing an adverb attached
   `advmod` to the same predicate (`quivi`, `là`, `dinanzi`) is accepted (`_adverbial_oblique`)
   — the membership check already accepts exactly these tokens as `obl` arguments.
7. **Phases 5f/5g — two `role_mismatch` acceptances, both one-directional**
   (`_oblique_lemma_refinement` / `_predicative_complement`): a given `obl:<lemma>` against a
   derived bare `obl` is accepted, because `derive_unit` emits the bare form only when no `case`
   child names the preposition — it is fused into the token (`che nel lago del cor **m'**era
   durata`), so the LLM's label adds information rather than contradicting the tree; and a given
   `xcomp` against a derived `obj`/`subj` is accepted, because UD has no relation for secondary
   predication — an object complement is attached as plain `obj` ("mi chiamaste **Ciacco**") and
   a copular predicate nominal as `nsubj` ("non son **torri**"), so the derivation can only
   report the attachment while the LLM names the predicative function. Both **mirror** directions
   stay flagged (given bare `obl` vs derived `obl:<lemma>`; given `obj`/`subj` vs derived
   `xcomp`): there the dep tree is explicit and the LLM contradicts it — the same asymmetry
   `--repair`'s `role_label` rule already rewrites on.
8. **Phase 5h — case-marked objects** (`_case_marked_object`): a given `obl:<lemma>` against a
   derived `obj`/`subj` is accepted when the argument carries a `case` child naming that same
   preposition — `derive_unit` takes the role from the deprel alone, so a case-marked nominal
   Layer 4 attached as `obj` loses the preposition that is sitting in the tree. Naming a
   *different* preposition than the `case` child stays flagged, as does the mirror direction.
9. **Phase 5j — co-present prepositions** (`_co_present_preposition`) and a rebuilt
   preposition-lemma table: Italian stacks prepositions and the dep tree attaches both markers
   to the nominal ("**in su** le porte", "dietro **a** noi"), while `derive_unit` reports only
   one, so a given `obl:<lemma>` naming another `case` child of the same argument is accepted.
   Phase 1's `_PREP_LEMMA_NORM` was at the same time rebuilt from every `case`-child word form
   in `dep/`, so preposition+article contractions (`nel` → `in`, `dal` → `da`, `al` → `a`) and
   archaic spellings (`sovr'` → `sopra`, `'nnanzi` → `innanzi`) stop reading as disagreements.
10. **Phase 5k — the clausal-complement cluster** (`_clausal_complement_flavor`,
    `_clausal_object`): `ccomp` against `xcomp` is treated as one label in either direction —
    both say *clausal complement of this predicate*, and Layer 4 splits them inconsistently on
    the same construction; and a given `ccomp` against a derived `obj`/`subj` is accepted when
    the argument is a **verb**, since Layer 4 attaches a complement clause's head verb straight
    to the matrix predicate ("or mi concedi ch'io **sappia**"). The mirror of the second (a
    given `obj`/`subj` against an explicit derived `ccomp`) stays flagged.
11. **Phase 5l — predicative adjectives attached adverbially** (`_predicative_advmod`): a given
    `xcomp` whose argument is an **adjective** attached to that predicate as `advmod` ("e io
    etterno **duro**", "va **superbo**") is accepted — rule M's construction, which Layer 4
    attached adverbially, and which `derive_unit` cannot produce at all since `advmod` is not in
    `ARG_DEPRELS`. The adjective gate is load-bearing: the same shape with an adverb argument,
    and any non-`xcomp` role, stay flagged.

12. **Phase 5r — the `case` annex as a third read** (`_case_corroborated_role`): a
    `role_mismatch` is accepted when the Layer-2 [`case/`](../case/README.md) annex's frozen value
    for the argument corroborates the **derived** role and *not* the given one — `nominative`↔
    `subj`, `accusative`↔`obj`, `dative`↔`iobj`/`obl:a`, `ablative`/`locative`↔`obl*`. This is the
    2-of-3 adjudication the annex was built for: `case` and `dep` agreeing against the LLM's
    reading, on exactly the clitic positions where the tree shape cannot decide (*mi pesa* dative
    vs *m'avea 'mmonito* accusative). Corroborating **both** sides (`obl:a` under `dative`, since
    Italian *a* marks place as well as recipient) or neither accepts nothing, the mirror direction
    is a hand-verified `dep` round rather than an automatic accept, and *fused* argument positions
    (`venendomi` = `verb+pronoun`, where the annex's value is the enclitic's while the citation is
    the verb's) are excluded by `_bare_pronoun_position`.

**Measured over the full 100-canto corpus** (`--check`, 2026-07-20 Phase 4a checkpoint): **0
hard, 7776 soft** — by kind, `extra_arg` 3719, `missing_arg` 1780, `role_mismatch` 1466,
`extra_tuple` 600, `missing_tuple` 117, `membership` 94. See [CORRECTIONS.md](CORRECTIONS.md)
for the measured before/after at every phase (14329 → 12825 → 9672 → 8090 → 7776) and the tests
backing each rule.

After a round of Phase 4b `--fix` regeneration (2026-07-25, run 3-way parallel): **0 hard, 5919
soft** — by kind, `extra_arg` 2848, `missing_arg` 1353, `role_mismatch` 1245, `extra_tuple` 275,
`missing_tuple` 100, `membership` 96, `unknown_role` 2. Every kind dropped, but the pace slowed
noticeably compared to the mechanical phases above — and the measurement in [PLAN.md](PLAN.md)
showed why: most flagged units are checker-side notation mismatches, not LLM errors.

After Phase 5a (2026-07-26, checker-only, no model call): **0 hard, 5105 soft** — by kind,
`extra_arg` 2065, `missing_arg` 1317, `role_mismatch` 1250, the rest unchanged. Δ814 in minutes,
roughly 1.8× what a full 2235-call `--fix` pass was extrapolated to remove. `subj` remains the
largest role bucket (`extra_arg subj` 936, `missing_arg subj` 323), and that residue is genuine
subject disagreement (enjambment, pro-drop resolution) — widening the control-subject authority
model was measured at −22 and rejected.

After Phase 5b (2026-07-26, checker-only): **0 hard, 4846 soft** — `extra_arg` 1991,
`missing_arg` 1305, `role_mismatch` 1250, `extra_tuple` 176, `membership` 96, `missing_tuple`
26, `unknown_role` 2. Phase 5d's hypothesis that the `expl` cases are Layer-4 mistags was
**disproved** by enumeration (99 of 107 cite the clitic of an inherently pronominal verb, which
Layer 4 tags correctly) — no `dep/CORRECTIONS.md` entry was opened.

After the Phase 5e `--fix` round (2026-07-28, all three canticles, 2037 units attempted): **0
hard, 4615 soft** — `extra_arg` 1887, `missing_arg` 1239, `role_mismatch` 1214, `extra_tuple`
155, `membership` 94, `missing_tuple` 24, `unknown_role` 2. 178 units accepted (8.7%), none
regressed, 231 violations removed. No class moved more than 11.9% and the three large ones moved
2.9-5.2%, which is the signal that what remains is checker-side rather than LLM error.

After Phase 5f (2026-07-28, checker-only, rule L): **0 hard, 4327 soft** — `role_mismatch` falls
1214 → **926** (−288, −23.7%), every other class unchanged. A given `obl:<lemma>` against a
derived bare `obl` is not a disagreement: `derive_unit` emits the bare form only when no `case`
child names the preposition, which holds in all 288 instances (the preposition is fused into the
token — a clitic dative or a preposition+article contraction), so the LLM's label is strictly
more informative. One deterministic rule removed more than the whole Phase 5e `--fix` pass.

After Phase 5g (2026-07-28, checker-only, rule M): **0 hard, 4097 soft** — `role_mismatch` falls
926 → **696** (−230, −24.8%), every other class unchanged. UD has no relation for secondary
predication: an object complement is attached as plain `obj` ("mi chiamaste **Ciacco**") and a
copular predicate nominal as `nsubj` ("non son **torri**"), so a given `xcomp` against a derived
`obj`/`subj` is the same labeling split Phase 1 canonicalizes `attr` → `xcomp` for. The mirror
direction stays flagged, since there the dep tree carries an explicit `xcomp` deprel.

After Phase 5h (2026-07-28, checker-only, rule N): **0 hard, 4068 soft** — `role_mismatch` 696 →
**667**. A given `obl:<lemma>` against a derived `obj`/`subj` is accepted when the argument
carries a `case` child naming *that same* preposition ("curan **di te**"): Layer 4 attached a
case-marked nominal as `obj`, and `derive_unit` reads the deprel alone. The other 97 instances of
that pair are **clitics** ("**mi** pesa", "**li** convien") where both sides make a case claim
the tree cannot settle — left flagged, and filed as a Layer-4 question in
[CORRECTIONS.md](CORRECTIONS.md).

After Phase 5i (2026-07-28, **Layer-4 correction**, no checker change and no skel artifact
touched): **0 hard, 4042 soft** — `role_mismatch` 667 → **641**. Phase 5h's 97 clitic cases were
read: the population is mixed (real Layer-4 dative mistags *and* real LLM errors), but a
structural subset decides itself — in 30 of them the predicate carries a **second** `obj` child,
which UD forbids, so the clitic cannot be the direct object. 26 survived hand-verification and
were retagged in `dep/` (22 → `iobj`, 4 → `obl` for partitive `ne`), each closing its Layer-5
divergence; `dep --check` stays 0 hard / 0 soft. This is the **first Layer-4 mis-parse Layer 5's
audit role actually produced** — see [`../dep/CORRECTIONS.md`](../dep/CORRECTIONS.md).

After Phase 5j (2026-07-28, checker-only, rule O + normalization): **0 hard, 3924 soft** —
`role_mismatch` 641 → **523** (−118), every other kind unchanged. The 140 `obl:<lemma>` vs
`obl:<other>` mismatches were two mechanical classes: one preposition spelled two ways (−57,
absorbed into `_PREP_LEMMA_NORM`) and two co-present prepositions of which the derivation
reports one (−61, rule O). The two-directional variant of rule O was measured at a further −30
and **rejected** — in the mirror direction the given preposition is attached elsewhere in the
unit (17), is an `advmod`/`obl` token (7), or is absent from the unit altogether (5), and no
single gate separates the Layer-4 inconsistency from the LLM invention.

After Phase 5k (2026-07-28, checker-only, rules P and Q): **0 hard, 3876 soft** —
`role_mismatch` 523 → **475** (−48), every other kind unchanged. Of the 173-instance
`xcomp`/`ccomp`/`obj` cluster, the `ccomp`≡`xcomp` flavor split (−22) and the clause-attached-as-
object cases (−25) are mechanical; the predicative-PP half (≈55, "sta **come torre** ferma",
"fu **di grado** maggior") is **not** — separating the copular readings would need a verb
lexicon, so it stays flagged.

After Phase 5l (2026-07-28, checker-only, rule R): **0 hard, 3808 soft** — `extra_arg` 1887 →
**1819** (−68), the first cut into the two big classes since Phase 5b. The re-triage that
produced it also settled what those classes are made of: `missing_arg` is **90% direct-child**
(the LLM omitting an argument sitting on the very edge `derive_unit` reads — LLM incompleteness,
not a checker artifact), and only 70 `extra_arg`/`missing_arg` pairs across the corpus are the
same NP cited at two different tokens.

After Phase 5m (2026-07-28, checker-only, rule S): **0 hard, 3746 soft** — `extra_arg` 1819 →
**1757** (−62), every other kind unchanged. A given `obl:<lemma>` whose argument is an `nmod`
child of the predicate itself and carries a `case` child naming that same preposition — rule D's
shape one edge in. The whole `nmod` direct-child population (62) satisfies the gate, splitting
into PP complements of nominal predicates ("furon **cagione di sua vittoria**", 58) and plain
Layer-4 `nmod`-for-`obl` mistags on verbs (4); both are correct readings, so the rule ships
ungated on the predicate's POS.

After Phase 5n (2026-07-28, a Layer-4 correction, not a checker change): **0 hard, 3725 soft** —
`extra_arg` 1757 → **1735**, `role_mismatch` 475 → **476**. The `mark` direct-child population
(35 instances where Layer 4 tags a relative or interrogative word `mark` on a predicate and the
LLM cites it as that predicate's argument) was read in full against its terzine: **22 are
Layer-4 mistags** and were retagged in `dep/` (8 → `obl`, 7 → `obj`, 7 → `attr`), 11 are cases
where Layer 4 is right and the LLM misreads (complex subordinators, comparative and consecutive
`che`, the idiomatic concessives), and 2 need a multi-edge restructuring. No gate separates
them, so this is the second audit finding routed back to Layer 4 rather than absorbed by a
checker rule — see [`../dep/CORRECTIONS.md`](../dep/CORRECTIONS.md). `dep --check` stayed 0/0.

After Phase 5o (2026-07-28, checker-only, rule T): **0 hard, 3712 soft** — `extra_arg` 1735 →
**1722** (−13), every other kind unchanged. A given `obl:<lemma>` whose argument is an `advcl`
child of the predicate itself and carries a `mark`/`case` child naming that same preposition —
rule S's shape with `advcl` in place of `nmod`, covering the prepositional infinitive clause
("s'appresta **per venir** verso noi", "**A descriver** lor forme più non spargo rime"). This
closes the last open row of the `extra_arg` direct-child bucket: the other 35 `advcl` instances
give a complement role (`ccomp`/`xcomp`) over an adverbial clause, which is the
complement-vs-adjunct distinction and would need the verb lexicon Phase 5k refused — after
excluding the copular/aspectual matrix verbs the remainder is 43 instances over 37 lemmas, so no
cheaper gate exists. 6 of them turned out to be Layer-4 mistags and were retagged by Phase 5p; the other 29 stay
flagged.

After Phase 5p (2026-07-28, two Layer-4 correction rounds, not a checker change): **0 hard, 3702
soft** — `extra_arg` 1722 → **1714**, `missing_arg` 1239 → **1238**, `role_mismatch` 476 →
**475**. Round A retagged 6 of Phase 5o's 35 `ccomp`/`xcomp`-over-`advcl` instances (5 →
`ccomp`, 1 → `csubj`, plus 2 supporting rows) and left the 29 where Layer 4 is right — purposive
`per`/`a` + infinitive, consecutive `sì`/`tanto … che`, conditional and temporal adverbials,
gerunds after perception verbs, depictive adjectives. Round B closed the two multi-edge
deferrals Phase 5n had left (purgatorio 8:114, purgatorio 22:15). `dep --check` stayed 0/0; see
[`../dep/CORRECTIONS.md`](../dep/CORRECTIONS.md).

After Phase 5q (2026-07-29, the user-run `--fix` pass plus the `ioj` typo fix): **0 hard, 3551
soft** — `extra_arg` 1714 → **1639**, `missing_arg` 1238 → **1193**, `role_mismatch` 475 →
**457**, `extra_tuple` 155 → **145**, `unknown_role` 2 → **0**. One full pass over all three
canticles, 1702 flagged parse units, ≈28 hours wall time run 3-way parallel, 66 cantos touched,
no unit regressed: **−147**, i.e. 0.086 violations per LLM call. The two `unknown_role` rows
(`purgatorio 13:103`, `13:104`) held the role `ioj`, a misspelling of `iobj` that Layer 4's tree
confirms; fixing it took 3555 → **3551**.

After Phase 5r (2026-08-03, rule U — the `case` annex as a third read — plus its hand-verified
mirror round): **0 hard, 3465 soft** — `role_mismatch` 516 → **347**, `missing_tuple` 25 →
**26** (one `dep` retag made the derivation propose a predicate the artifact does not), every
other class unchanged. Rule U accepts a
`role_mismatch` when the Layer-2 `case` annex's frozen value for the argument corroborates the
`dep`-derived role and *not* the LLM's (−160, one-directional, and gated off fused
`verb+pronoun` positions where the annex's value is the enclitic's, not the cited token's). The
17 positions where the annex sides the other way were read by hand: ten `dep` retags, four
`case` corrections, eight left alone — chiefly because a copular predicate nominal is nominative
just as a subject is, so the annex cannot separate `subj` from `attr`. See
[CORRECTIONS.md](CORRECTIONS.md), [`../dep/CORRECTIONS.md`](../dep/CORRECTIONS.md) and
[`../case/CORRECTIONS.md`](../case/CORRECTIONS.md).

## Next steps

What remains past the mechanical phases above is **reading disagreement between two independent
parses**, not a class with a known instrument: subject resolution across enjambment and pro-drop
(`extra_arg subj` 327 after rule V took it from 805, of which 127 are the LLM asserting ∅ against a
derived subject), the direct-child `missing_arg` mass, the clitic dative/accusative
question (needs a Layer-2 case feature), and the complement-vs-adjunct distinction (needs a verb
lexicon). Both routes are now measured out — regeneration at a flat ~0.09-0.11 violations per
call over two full passes on a static residue (Phase 5s's third pass returned 0.199, but only
because a cross-layer round had just put a *large* population of fresh LLM-authored error into the
flagged set; Phase 5t's fourth pass, after a smaller such round, was back at 0.085), and
deterministic rules against every population [PLAN.md](PLAN.md) triaged. The goal remains **0 soft
violations**, but reaching it needs an instrument this project has declined on principle, so it is
a new plan rather than more of this one.

`--fix` (`skel/skel.py`) regenerates a flagged parse unit and keeps the result only if its soft
violation count strictly drops **and** no violation class appears that wasn't already there
(`_is_improvement`, Phase 5c — the plain count test let the Phase 4b round trade a net drop for
`unknown_role` 0 → 2, a role outside the frozen vocabulary). As of Phase 4b's `_fix_hint`, a regeneration attempt gets a
per-predicate pointer built from the unit's prior soft violations — which predicate looks
unwarranted or missing, which role slot looks missing/extra/mislabeled — appended to the prompt
`build`'s initial parse never receives. The hint deliberately withholds `derive_unit`'s actual
argument citations and its correct role label (a `role_mismatch` hint names the LLM's *own*
prior label, not the derived one), so the retry still reads the sentence independently rather
than parroting back a guess; without it, a systematic misreading (e.g. resolving an `xcomp`
control subject from the wrong constituent) tends to reproduce itself verbatim across attempts.

## `--fix` hint (Phase 4b)

`skel/skel.py`:

- **`_fix_hint(nos, texts, violations)`**: summarizes a unit's `soft_before` violations into a
  short list, one line per `(predicate, role)` pair, phrased per violation kind
  (`missing_tuple`/`extra_tuple`/`missing_arg`/`extra_arg`/`role_mismatch`) — see
  `_HINT_PHRASING`. Only violations carrying a `.predicate` (i.e. `_classify_divergence`'s
  output) are included; `membership`/`unknown_role` violations (no predicate attached) are
  skipped.
- **`_prompt`/`_try_parse`** gained an optional `hint` parameter, appended as a final prompt
  section when present. `_fix_canto` is the only caller that supplies one, computed from each
  unit's `soft_before` right before regenerating; `build`'s call sites pass none.

## Model

Build-time only, set in [`../model.mk`](../model.mk), overridable with `make skel MODEL=...`.
The model is a build tool whose output is frozen and checked; consumers see a stable asset.

## Usage

```bash
make -C skel                          # build all three canticles (model from model.mk)
make -C skel MODEL=ollama:gpt-oss     # override the model
make -C skel check                    # validate artifacts, no model call
make -C skel stats                    # validate artifacts, no model call; soft counts by class
make -C skel repair                   # rewrite derive-authoritative errors, no model call
make -C skel fix                      # regenerate parse units carrying soft violations

uv run skel/skel.py inferno [-c 1] [-m MODEL] [--chunk 12] [--force] [--check] [--stats]
uv run skel/skel.py inferno purgatorio paradiso --repair   # no model call
uv run skel/skel.py inferno -m ollama:gpt-oss --fix        # regenerate flagged units
```

Consumers read it deterministically via `Canto.skel()` (frozen, grouped, identified
`SkelTuple`s) or the CLI `dante-corpus text skel inferno 1:1-3` (`--format json` for tuple
dicts). `skel.antecedent` resolves a relative-pronoun subject's antecedent NP at serve time
(never stored); `skel.pro_drop_features` similarly derives person/number for a `∅` subject from
the predicate's own morphology.
