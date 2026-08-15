# skel — Layer 5: predicate-argument skeleton

Predicate ↔ argument tuples binding Layers 2-4 into bare propositions, citing **token
positions**, not raw text or lemmas — the next layer of the grammatical stack
([`../PLAN.md`](../PLAN.md)) after dependency parsing. This is the *raw* skeleton only: **no
semantic frame, no coreference, no vocabulary normalization.** Role labels are **UD-derived**
(`subj`/`obj`/`iobj`/`attr`/`xcomp`/`ccomp`/`obl:<preposition lemma>`), not semantic, so the
canon-neutral.

**Status: built for all 100 cantos, checker refined through Phase 5 (5,919 → 2,084 soft) and Phase 6 (Rules AG–BN plus three `--fix` rounds: 650 soft). `--fix` operates as a three-stage driver (deterministic auto-repair, POS-keyed micro-prompts, and fallback regeneration).**

`make -C skel check`: **0 hard, 650 soft** violations across all 100 cantos (down from 17,438 at the first full-corpus measurement). Full historical measurement tables, per-phase progressions, and empirical findings on regeneration yields are documented in [`PHASE5.md`](PHASE5.md). For current Phase 6 operating principles, active routes, and driver architecture, see [`PLAN.md`](PLAN.md) and [`CORRECTIONS.md`](CORRECTIONS.md).

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

Thirteen refinements make that divergence check meaningful rather than noisy — landed as
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
3. **`--repair`** (`Repair`/`_find_repairs`/`_safe_role_repair`), which is also `--fix`'s
   stage 1: for the subset of divergences that need no *reading*, mechanically rewrites the
   committed TSV — no model call — from the checker's own violation list (so the authority model
   above automatically gates what's eligible). Each rewrite is applied singly and re-validated,
   and rolled back if it does not clear violations cleanly. The rules split into two tiers, and
   the split is the design:
   - **Tier A asserts no reading** — the two sides spell one thing two ways.
     **role_label**: given bare `obl` against a derived `obl:<lemma>` (the dep tree's
     `case`-child detection) — the role cell is rewritten.
     **prep_stack**: given `obl:X` against derived `obl:Y` where **both** lemmas sit in the same
     `case`-child chain off the argument ("in su la cima" is chained `in` → `su` → nominal, so
     the derivation names the inner preposition and the LLM the outer one). The corpus already
     normalizes this family onto the derived side (`_PREP_LEMMA_NORM`). When the LLM names a
     preposition the tree does not carry *at all*, the two sides differ about what is attached
     and nothing is rewritten.
   - **Tier B does assert a reading**, so it fires only where a signal **independent of Layer 4**
     corroborates it — a Layer-5 divergence is evidence that Layer 4 may be the wrong side, so
     "the derivation says so" is not by itself a reason to rewrite.
     **null_subject**: a `missing_arg subj` paired with an `extra_arg subj (0,0)` (the LLM wrote
     pro-drop ∅) for the same predicate, rewritten to the derived subject **only when Layer 2's
     person/number agrees with the predicate** (`dep.subject_agreement`, the same test
     `dep --check`'s subject-agreement rule runs, extracted so the two cannot drift). Its third
     answer, "undecidable", is not a weak yes: the rule repairs only on "agree". Of the corpus's
     67 candidate pairs Layer 2 corroborates 37 and *contradicts* 20.
   - Genuine disagreements (`subj`/`obj` reversals, `iobj`/`obj` reversals, cross-lemma `obl`
     pairs the tree does not stack) are excluded and left for `--fix`'s stage 2.
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
   After Layer 4's 2026-08-14 multiword-preposition normalization the lemma collection also
   aggregates a `fixed` member under its `case` row (`su` `fixed`→ `in` `case`→ nominal), so the
   rule accepts either member of the stack unchanged.
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

13. **Phase 6 — rules AH-AL, from the Inferno 7-10 read** (2026-08-14). Five acceptances, each
    measured over all 100 cantos before being written; together **1247 → 1091 soft**, no model
    calls. Full evidence in [`CORRECTIONS.md`](CORRECTIONS.md).
    - **AH** (`_apply_subj_authority`, rule AG's branch): when rule AG drops a conj-inherited
      subject whose Layer-2 person/number contradicts the predicate, the LLM's `∅` is dropped with
      it. AG was disclaiming the derived subject and then reporting the LLM's ∅ as an `extra_arg`
      about a slot the derivation no longer filled. Only `∅` — a concrete subject stays flagged.
    - **AI** (`_np_head_equivalent` / `_merge_np_head_citations`): Layer 3's NP `head` and Layer
      4's attachment point are computed independently and do not always land on the same token
      (`[più di mille]` has `head=più`; Layer 4 attaches `mille`). Since `SYSTEM_PROMPT` tells the
      model to prefer the NP head, one argument became a `missing_arg` **and** an `extra_arg`.
      Paired and dropped when both positions lie in one NP span, one of them is its head, and the
      role is the same. Two tokens sharing only a line, or a role disagreement, stay flagged.
    - **AJ** (`_conj_shared_argument`): `derive_unit`'s step 3 propagates a shared **subject**
      across a coordination and nothing else, but Italian gaps objects and datives just as freely
      ("li rami *schianta*, *abbatte* e *porta* fori"). An `extra_arg` on a `conj` predicate is
      accepted when the cited argument is an argument of some conjunct **up its chain** and the
      conjunct has no derived filler of that role. The role may differ — gapping changes it — but
      the slot must be empty, and `subj` is excluded (rules AC/AG/AH own it).
    - **AK** (`_comparative_come_complement`): a given `xcomp` against a derived `obl:come`, when
      Layer 2 tags `come` a **conjunction** and only Layer 4's `case` edge makes it a preposition
      ("staranno *come porci* in brago").
    - **AL** (`_fused_clitic_dual_role`): a `role_mismatch` between `obj` and `obl:a`/`iobj` on an
      argument Layer 2 tags as two fused pronouns (`gliel` = `gli` + `lo`), which genuinely fills
      both slots. The Phase-4 `double_listed` whitelist already accepted the `extra_arg` leg.

14. **Phase 6 — rules AM-AT, from the Inferno 11-15 read** (2026-08-15). Eight rules, each
    measured over all 100 cantos before being kept; together **963 → 888 soft**, no model calls.
    Four of them correct `derive_unit` itself rather than accepting a divergence — the first batch
    to find the derivation *wrong* rather than silent. Full evidence, including the variants
    measured and dropped, in [`CORRECTIONS.md`](CORRECTIONS.md).
    - **AM** (`argument_children`, in `derive_unit`): UD attaches a clause's arguments to its
      lexical predicate, but Layer 4 sometimes leaves them on the `cop`/`aux` ("'n la mente m'è
      fitta"), where the derivation never saw them. Non-subject slots only — the subject leg was
      measured separately and dropped, since the authority model owns that slot.
    - **AN** (`gapped_conjuncts`, in `derive_unit`): a conjunct carrying an `orphan` child heads a
      *gapped* clause, not a predicate ("e 'l villan la sua marra"). Its remnants fill the
      coordination head's own slots again: a case-marked remnant takes the matching oblique, the
      rest take the remaining slots in canonical role order.
    - **AJ′** (`_conj_shared_argument`, widened): gapping runs in every direction inside a
      coordination cluster, not only up the `conj` chain — from a sibling conjunct ("biscazza e
      *fonde* la sua facultade") and from a conjunct up onto its head ("col cor *negando* e
      bestemmiando quella").
    - **AP** (`_coordination_head`, widened to `appos`): an apposition is the same argument named
      a second time ("guastatori e predon, *tutti* tormenta"), and collapses exactly as a
      conjunct does. Roles are preserved, so a genuine role disagreement still surfaces.
    - **AQ** (`_merge_auxiliary_citations`): an argument citation landing on an `aux`/`cop` names
      its lexical head ("ch'altro ne *volesse* dire") — rule I's identity applied to the argument
      slot rather than the predicate slot.
    - **AR** (`_comparative_come_adjunct`): rule AK's `missing_arg` leg. A comparison with no verb
      of its own leaves Layer 4 nothing but the main predicate to hang the compared nominal on
      ("come que' che lassi", "Come d'un stizzo verde … sì"). Gated on a Layer-2 conjunction
      `come` marking the phrase, and — where the marker is on the predicate — on a correlative
      `sì`/`così` separating the two halves.
    - **AS** (`_reflexive_clitic_argument`, widened): a fused clitic's *second* `case`-annex slot
      licenses the oblique role Layer 4's single `expl` deprel cannot record ("poi *sen* van giù"
      = `si` + `ne`, `reflexive+ablative`). Fused values only; a plain reflexive decides nothing.
    - **AT** (`derive_unit` step 3): only a **verb** inherits a subject across `conj`. A nominal
      promoted to predicate is an elided clause of its own — the speaker of an elided verb of
      speech ("Ed *elli*: «Vedi …»"), not a second subject of the coordination head's verb.

15. **Phase 6 — rules AU-AY, from the Inferno 16-20 read** (2026-08-15). Five rules, each
    censused corpus-wide, measured alone by violation diff and mutation-checked; together
    **888 → 834 soft**, no model calls, and none of them newly flagged a position. Three are
    *mirror legs* of rules the checker already had. Full evidence in
    [`CORRECTIONS.md`](CORRECTIONS.md).
    - **AU** (`_secondary_predicate_over_argument`, `amod` leg): an **adjective** Layer 4 hangs
      `amod` on one of *this* predicate's own derived arguments is the predication's secondary
      predicate ("fa **servo forte**", "ho **le cose conte**", "fia **la tua imagine leggera**").
      Rule R takes the same complement when Layer 4 hangs it on the predicate as `advmod`; rule
      AA takes the participial version off an argument as `acl`. Largest mover of the batch (−17).
    - **AV** (`_named_by_its_auxiliary`): `_aux_of_derived_predicate`'s missing leg. When the LLM
      names *only* the `aux`/`cop` as the predicate ("che spezzate **averien** ritorte"), Layer
      4's lexical head was reported "not proposed" although the same predication was proposed
      under the other convention. Rule AQ's predicate-position twin.
    - **AW** (`_pronominal_verb_clitic`): rule AB's mirror. Layer 4 still calls 371 reflexive
      clitics `obj`/`iobj` rather than `expl`, on no visible principle, and there the derivation
      asserts an object the LLM does not read in a pronominal verb ("si partiro", "s'atterga",
      "si puose"). Same gates as AB: annex-reflexive, Layer-2 pronoun, own child, clitic-carriable
      role.
    - **AX** (`_control_partners`): rule X's mechanism pointed at the `xcomp` edge. A control or
      modal periphrasis is one predication over two tokens, so which end carries a shared argument
      is a placement convention ("hanno a passar" — `per l'essercito` on the finite verb in Layer
      4, on the infinitive in the reading). Role must match; `ccomp` is excluded.
    - **AY** (`_complemented_adjective_phrase`): `_elided_copula_nominal`'s adjective-phrase
      sibling. An `amod` adjective that governs an argument of its own is a reduced relative and
      predicates ("maravigliosa ad ogne cor sicuro", "piena di duolo"); the complement child is
      the evidence, and a bare attributive stays flagged.

16. **Phase 6 — rules AZ-BI, from the Inferno 21-25 read** (2026-08-15). Nine rules, each
    censused corpus-wide, measured alone by violation diff and mutation-checked; together with 20
    Layer-4 and 5 Layer-2 rows **834 → 691 soft**, no model calls — the largest batch of the read
    series so far. Full evidence in [`CORRECTIONS.md`](CORRECTIONS.md).
    - **AZ** (`_depictive_bare_oblique`): rule R's mirror leg. The depictive adjective Layer 4
      hangs on the predicate as a **bare `obl`** rather than `advmod` ("tornò sù **convolto**",
      "ne verranno dietro **più crudeli**", "si mira tutto **smarrito**"). Gated on no `case`
      child (a preposition makes it a genuine adjunct), adjective POS, and the predicate's own
      child. Closes the standing `supin ricadde` route.
    - **BA** (`_undecided_subject_slot`): a clause has one subject slot, so a predicate with
      **two** derived `subj` rows has not been decided by the tree — an elided verb of speech's
      speaker ("E quelli: «**I'** mi partii»"), a relative pronoun beside its own antecedent, a
      coordination Layer 4 wrote as two flat `nsubj` edges. Naming either is a reading of the
      same slot. Largest mover of the batch (−41).
    - **BB** (rule V's coordination leg): the LLM lists *every* conjunct of a controlled
      infinitive's subject, and `_subj_arg` took only the first out; rule C then collapsed the
      rest back onto the citation just accepted. Rule V's candidate set is now also tested
      through `_coordination_head`.
    - **BC** (`_adverbial_oblique`, widened): an `advmod` whose filler Layer 2 calls a **noun or
      pronoun** is an oblique ("stieno … **un poco** in cesso", "dicean **seco**", "**li** giacea
      un draco"). Rule R's caution still holds for the adjective and verb cases.
    - **BD** (`_pronominal_verb_clitic`, third deprel): 35 reflexive clitics stand as `obl`, and
      the same labeling split rule AW settles for `obj`/`iobj` applies ("s'aggueffa", "si fuggì").
      Also settles the mismatch leg, where both readings park the clitic in a clitic-carriable
      slot and differ only over which.
    - **BE** (`_coordination_head`, `flat` leg): `flat` is UD's *headless* multiword relation, so
      its members are the same nominal, not modifiers of the opening word ("son **Vanni Fucci**").
    - **BF** (`_inverted_copula_complement`): a `cop` edge Layer 4 pointed the wrong way. A `cop`
      child Layer 2 calls an adjective or a noun cannot be a copula, so the edge is inverted on
      the tree's own evidence and the token in it is the complement ("fu a terra sì **distrutto**").
    - **BH** (`_displaced_subject_pro_drop`): rule M's mirror leg. Once rule M concedes the
      derived `subj` to the LLM's predicative complement ("mi parve una **lontra**", "**Frati
      godenti** fummo"), the clause has no overt subject left and the LLM's ∅ was reported as an
      extra argument — the same labeling split counted twice. Gated on rule M having fired.
    - **BI** (`_accusative_and_infinitive`): after a verb of perception or causation the nominal
      is the matrix object *and* the infinitive's subject ("vidi … **uno** aspettar", "trovammo
      risonar **quell' acqua tinta**"). Layer 4 records the second, the LLM names the first, and
      the tree asserts both edges. Censused at 10; took all 10.
17. **Phase 6 — rules BJ-BN, from the Inferno 26-30 read** (2026-08-15). Five rules plus three
    legs added to rules already in the checker, each censused corpus-wide, measured alone by
    violation diff and mutation-checked; together with 10 Layer-4 and 1 Layer-2 rows **691 → 650
    soft**, no model calls. Full evidence in [`CORRECTIONS.md`](CORRECTIONS.md).
    - **BJ** (`_merge_adverb_cluster_citations`): the adverb-preposition cluster ("**fuor** del
      dritto amore", "**innanzi** a li altri", "da **qui innanzi**") is one complex preposition
      and one adjunct, named by either of its two words. Layer 4's 2026-08-14 prep-stack
      normalization deliberately left these 40 clusters alone because Layer 2 calls the opening
      word an adverb; the citation is merged onto the cluster head as rule AQ merges an auxiliary
      citation, and the cluster's inner preposition joins rule O's lemma set. Censused at 147;
      largest mover of the batch (−21).
    - **BK** (`_comparative_come_adjunct`, `che` leg): the second term of a comparison is marked
      by `che` as often as by `come` ("vedesse altro **che la fiamma sola**", "fuor **che
      Bonturo**"). Argument leg only — a `che`-marked *clause* on the predicate is a complement.
      Censused at 51.
    - **BL** (same rule, `sì come` order): when the correlative stands immediately *before* the
      marker the two are one word, so the comparison is what the marker opens rather than what
      lies between the two ("**sì come nuvoletta**, in sù salire"). Censused at 107; worth −1.
    - **BM** (`_conjunction_oblique`): an oblique whose filler Layer 2 calls a **conjunction** is
      the clause's connective ("Nel tempo **che** Iunone era crucciata", "**onde**", "**per
      che**"). Oblique slot only: the same census finds 147 `nsubj` and 61 `obj` conjunction-
      tagged tokens, which are relative pronouns doing real argument work. Censused at 37 (−11).
    - **BN** (`derive_unit` step 1): a conjunction in a clause-head deprel with no arguments of
      its own is a connective, not an elided predicate ("**Onde** l'altro lebbroso … rispuose").
      Rule AN's clause-head leg says the same of a gapped comparison promoted to `advcl` with an
      `orphan` remnant. Both are net zero and both make the derivation right.
    - **BI**′ (`_accusative_and_infinitive`, `obj` host): Layer 4 also writes the perception
      verb's infinitive as a plain `obj` ("Io vidi **due** sedere"). Gated on Layer 2 calling the
      host an infinitive — 28 of the 35 candidates are finite clauses whose `nsubj` is their own.
    - **AQ**′ (membership check): rule AQ's `cop`/`aux` merge applied where the citation is still
      raw. The membership check runs before `_merge_auxiliary_citations` and was reporting the
      un-normalized position ("vorrebbe di vedere **esser** digiuno"). 2 positions.

**Measured Progression Across Phases**:
- **Phase 4a Checkpoint (2026-07-20)**: `0 hard, 7776 soft` (down from 17,438 initial).
- **Phase 4b `--fix` Pass (2026-07-25)**: `0 hard, 5919 soft` across all 100 cantos.
- **Phase 5 Deterministic Series & Upstream Audits (Phases 5a–5w, Rules C–AF)**: Reduced soft violations from **5,919 → 2,084**. For the complete chronological record, per-phase measurement tables, Layer-4 corrections, and empirical findings on regeneration yield, see [`PHASE5.md`](PHASE5.md).
- **Phase 6 Restructured `--fix`, Rules AG–BN**: Reduced soft violations from **2,084 → 1,091** (first user-run pass: 2011 → 1452; Rule AG: 1452 → 1409; second user-run pass: 1409 → 1247; Rules AH–AL and the Inferno 7–10 read: 1247 → 1091), then **1094** after the Layer-4 agreement close and prep-stack normalization (net zero by design), then **963** with the third user-run pass (1094 → 963, 2026-08-15), then **888** with rules AM–AT and the Inferno 11–15 read (963 → 888, 2026-08-15 — eight rules, four of them in `derive_unit` itself, plus 16 Layer-4 and 2 Layer-2 rows), then **834** with rules AU–AY and the Inferno 16–20 read (888 → 834, 2026-08-15 — five rules, three of them mirror legs of existing ones, plus 25 Layer-4 and 1 Layer-2 rows), then **691** with rules AZ–BI and the Inferno 21–25 read (834 → 691, 2026-08-15 — nine rules, plus 20 Layer-4 and 5 Layer-2 rows), then **650** with rules BJ–BN and the Inferno 26–30 read (691 → 650, 2026-08-15 — five rules plus three legs added to existing ones, and 10 Layer-4 and 1 Layer-2 rows). See [`PLAN.md`](PLAN.md) and [`CORRECTIONS.md`](CORRECTIONS.md).

## Next steps

For active Phase 6 open routes (a queued `--fix` round, plus assistant-side manual audits of the `extra_arg subj` null-position residue, quoted speech under `parataxis`, Inferno 11–13, attributive adjectives, and promoted adverbs — the stacked-preposition route closed 2026-08-14 with Layer 4's multiword-preposition normalization), see the active plan in [`PLAN.md`](PLAN.md).

`--fix` (`skel/skel.py`) keeps a change only if the unit's soft violation count strictly drops
**and** no violation class appears that wasn't already there (`_is_improvement`, Phase 5c — the
plain count test let the Phase 4b round trade a net drop for `unknown_role` 0 → 2, a role outside
the frozen vocabulary). That gate now applies **per stage**, so the no-worse-off guarantee holds
at each step rather than only across the pass.

## `--fix`'s three stages (Phase 6)

Phase 5w measured the old design's cost: 1290 LLM calls removed 123 violations, because a flagged
unit was regenerated *whole* from one monolithic prompt and accepted only if the *whole* unit
improved. `--fix` now works cheapest-first, and a unit drops out as soon as it is clean.

1. **Deterministic** — `_apply_unit_repairs`, the `--repair` rules above, no model call. Measured
   at **2084 → 2011, −73** over the corpus. A unit this clears never reaches the model.
2. **Class-targeted** — the remaining violations are grouped by `_violation_subclass` and each
   group gets **its own system prompt, its own narrow question, and its own small answer**,
   spliced in at row level and accepted independently (`_CLASS_PROMPTS`, `_ask_class`). Tuple-level
   classes are asked before argument-level ones (`_CLASS_ORDER`), because adding or withdrawing a
   predicate changes which arguments there are to dispute.
3. **Whole-unit regeneration** — the original instrument, now a fallback for units the first two
   stages left untouched; `--no-whole` disables it so a round can be measured with and without it.

The summary is printed **per class, with calls beside violations removed**. That is what Phase
5w's finding demands: a pass average conceals which instrument worked.

### Why per-class prompts

Phase 5w's result was that a prose rule buried in a long prompt does not change the reading,
while an instruction that reaches the model *at the flagged position* does. Splitting the prompt
by class makes that structural rather than a matter of prompt-writing discipline: each class
prompt carries only the conventions bearing on it — the adverb rule for an adverb `extra_tuple`,
the attributive-adjective rule for an adjective one, the elided-speech-frame rule for a nominal
`missing_tuple` — all lifted verbatim from `SYSTEM_PROMPT`, which is unchanged and still used by
`build`. Each is under half its length. The other gain is partial credit: settling one class is
committed even when the others fail.

`membership` and `unknown_role` have no prompt on purpose — `_fix_hint` never produced one for
them (they carry no predicate), rule AF closed the membership question at 8, and `unknown_role`
stands at 0.

### The independence rule, in stage 2

A question may name the predicate, the argument **the LLM itself cited**, and the role slot in
dispute — exactly what `_fix_hint` already disclosed. It may **never** cite `derive_unit`'s own
argument position, which would reduce the model to confirming Layer 4 instead of reading the
line; `tests/test_skel_fix.py` pins this for both the position and, for `role_mismatch`, the
derived role.

## `--fix` hint (Phase 4b; now stage 3 only)

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
make -C skel repair                   # --fix's deterministic stage on its own, no model call
make -C skel fix                      # reduce soft violations (three stages)

uv run skel/skel.py inferno [-c 1] [-m MODEL] [--chunk 12] [--force] [--check] [--stats]
uv run skel/skel.py inferno purgatorio paradiso --repair    # no model call
uv run skel/skel.py inferno -m ollama:gpt-oss --fix         # all three stages
uv run skel/skel.py inferno -m ... --fix --no-whole         # without the regeneration fallback

uv run skel/read.py inferno 16 43                           # read one position, all five layers
uv run skel/read.py inferno 16 43 48                        # ... over a line range
```

`read.py` is the audit series' tool (see [`PLAN.md`](PLAN.md)'s *How to Read a Batch*): `--check`
names a position, `read.py` prints its whole parse unit with Layer-2 morphology and the `case`
annex, Layer-4 deprels, Layer-3 NP spans, and **both** Layer-5 readings — the frozen artifact rows
and `derive_unit`'s derived rows, which is exactly the pair the soft checks diff.

Consumers read it deterministically via `Canto.skel()` (frozen, grouped, identified
`SkelTuple`s) or the CLI `dante-corpus text skel inferno 1:1-3` (`--format json` for tuple
dicts). `skel.antecedent` resolves a relative-pronoun subject's antecedent NP at serve time
(never stored); `skel.pro_drop_features` similarly derives person/number for a `∅` subject from
the predicate's own morphology.
