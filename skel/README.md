# skel — Layer 5: predicate-argument skeleton

Predicate ↔ argument tuples binding Layers 2-4 into bare propositions, citing **token
positions**, not raw text or lemmas — the next layer of the grammatical stack
([`../PLAN.md`](../PLAN.md)) after dependency parsing. This is the *raw* skeleton only: **no
semantic frame, no coreference, no vocabulary normalization.** Role labels are **UD-derived**
(`subj`/`obj`/`iobj`/`attr`/`xcomp`/`ccomp`/`obl:<preposition lemma>`), not semantic, so the
canon-neutral.

**Status: built for all 100 cantos, checker refined through Phase 5 (5,919 → 2,084 soft) and Phase 6 (Rules AG–DR plus five `--fix` rounds: 261 soft). `--fix` operates as a three-stage driver (deterministic auto-repair, POS-keyed micro-prompts, and fallback regeneration).**

`make -C skel check`: **0 hard, 261 soft** violations across all 100 cantos (down from 17,438 at the first full-corpus measurement). Full historical measurement tables, per-phase progressions, and empirical findings on regeneration yields are documented in [`PHASE5.md`](PHASE5.md). For current Phase 6 operating principles, active routes, and driver architecture, see [`PLAN.md`](PLAN.md) and [`CORRECTIONS.md`](CORRECTIONS.md).

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

18. **Phase 6 — rules BO-BV, from the Inferno 31-34 read** (2026-08-16). Eight rules, each
    censused corpus-wide, measured alone by violation diff and mutation-checked; together with 15
    Layer-4 rows, 2 Layer-2 rows, 1 Layer-3 span and 1 case-annex row **541 → 506 soft**, no model
    calls. Full evidence in [`CORRECTIONS.md`](CORRECTIONS.md).
    - **BO** (call order in `_classify_divergence`): rule AI (`_merge_np_head_citations`) runs
      **before** rule D (`_drop_nmod_obliques`). Both fire on a given citation the derivation does
      not carry; rule D drops it as an accepted adjunct and leaves the derived position reported,
      while rule AI re-keys it and silences both halves ("torreggiavan **di mezza la persona**").
    - **BP** (`_hosts_child`): every "is this the predicate's own child" gate — nine of them —
      reads an `aux`/`cop` head through to its lexical word. 53 arguments corpus-wide hang on an
      auxiliary rather than on the verb carrying the tuple ("tre Frison **s'**averien dato mal
      vanto"). `derive_unit` has reached through that edge since rule AM; the gates had not.
    - **BQ** (`_adverb_cluster_head`, bare leg): rule BJ's other two orders — the cluster's
      nominal hangs **bare** under the adverb ("dinanzi **l'altro**") or the preposition sits on
      the adverb ("'n su **lo scoperto**"). Censused at 11 against rule BJ's 150; a `mark` on the
      nominal excludes the second term of a comparison, which rules BK/BL own.
    - **BR** (`_nested_in_named_phrase`): a derived argument buried inside a Layer-3 noun phrase
      whose head is another derived argument the LLM *did* cite ("**Gualandi con Sismondi e con
      Lanfranchi** s'avea messi"). Rule AI's case for when the roles differ. Structural pattern
      censused at 404, of which 8 fire. Its mirror leg was measured (−6/+0) and **dropped**: on
      the given side the only evidence is a Layer-3 span, and Layer 3 is over-inclusive by design.
    - **BS** (`_copular_predication`, copula leg): rule Y read from the other end — the LLM names
      a nominal predication by its copula ("e cortesia fu lui **esser villano**"). The citation is
      tested through `_aux_head` first, rule BP's normalization on a tuple-side gate.
    - **BT** (`_free_relative_matrix_head`): rule AE's embedded side. In an embedded question
      Layer 4 hangs the clause **under** the interrogative pronoun ("saper **chi son cotesti
      due**"), so the word filling the clause's own slot is its governor in the tree. 765
      predicates are `acl:relcl` under a pronoun; requiring the clause to hold no relative pronoun
      of its own — the discriminator against ordinary correlatives — leaves 92.
    - **BU** (`_apply_subj_authority`, rule AC's branch): the subject a coordination supplies from
      its **last** conjunct ("**lasciò** … **quella ch'appar di qua**, e sù ricorse"). Rule AT's
      direction reversed, for the case where the head has no subject of its own to defend.
      Censused at 74.
    - **BV** (`_prep_stack_nominal`): a `fixed` word of a multiword preposition is not an
      argument — the citation names the nominal the cluster opens, as rules AQ and BJ merge onto
      their phrase's head. Entered only from a `fixed` member; the same walk started from a plain
      `case` re-keyed citations onto the predicate itself and was narrowed.


19. **Phase 6 — rules BW-BZ, from the Purgatorio 1-5 read** (2026-08-16). Four rules, each
    censused corpus-wide, measured alone by violation diff and mutation-checked; together with 2
    Layer-4 rows and 1 case-annex row **506 → 481 soft**, no model calls. Full evidence in
    [`CORRECTIONS.md`](CORRECTIONS.md).
    - **BW** (`_marker_slot_argument`): rule BM's mirror leg. An interrogative or relative word
      opens its clause *and* fills one of its argument slots; Layer 4 records the first function
      with `mark`, which is outside `ARG_DEPRELS`, so the derivation cannot assert the second at
      all ("un non sapeva **che** bianco"). Gated on Layer 2 *not* calling the marker a
      conjunction — that is a subordinator, and rule BM's reading — and on the marker hanging on
      this predicate. Censused at 63; 19 standing `extra_arg` positions cite a `mark`, 14 of them
      non-conjunction.
    - **BX** (`_depictive_bare_oblique_omitted`): rule AZ's `missing_arg` leg. A depictive
      adjective in a bare `obl` slot is an adjunct of the predication ("mi cominciò **tutto
      rivolto**"), so the LLM omitting it is as faithful as rule AZ's case of naming it. Rule AZ's
      three gates unchanged. Censused at 44, 11 of them standing positions, all 11 taken.
    - **BY** (`_auxiliary_hosts`): the LLM writes two tuples for one periphrasis and splits the
      arguments between the lexical verb and its `aux` ("quel da Esti **il fé far**"). Rule X's
      mechanism pointed at the `aux`/`cop` edge, so it inherits the role-must-match gate.
      Population 5, 3 fired.
    - **BZ** (`derive_unit`, predicate census): the `conj` chain is walked a second time after the
      argument-bearing-verb pass, because the first walk resolves against a set that pass has not
      yet written ("com' io **rimango** sol, se non **restai**"). Restricted to *finite* verbs by
      rule BN's test — a nominal or bare-infinitive conjunct would carry an empty tuple. Net zero
      (−2/+2) and kept for correctness, as rules BN and AN′ were.


20. **Phase 6 — rules CA-CJ, from the Purgatorio 6-10 read** (2026-08-16). Ten rules, each
    censused corpus-wide, measured alone by violation diff and mutation-checked; together with 1
    Layer-4 row **481 → 448 soft**, no model calls. Eight of the ten are about coordination or
    about a predicate the derivation declines to mint. Full evidence in
    [`CORRECTIONS.md`](CORRECTIONS.md).
    - **CA** (`derive_unit`, `promote_conjuncts`): rule BN's argument test on the `conj` branch. A
      non-verb conjunct with no argument child and no `cop`/`aux` is a coordinate nominal, not an
      elided clause, and the tuple minted for it is empty ("Sordel rimase e **l'altre genti**
      forme"). Censused at 209. Generalizing the same test to *all* non-verb clause heads was
      measured at **+168** and rejected — those are copular predicates with pro-drop subjects.
    - **CC** (`_promoted_conjunct_argument`): rule CA's acceptance leg. Having denied the conjunct
      is a clause, the checker owes it a slot, and the derivation gives it none; accepted in the
      LLM's role, on rule CA's own gate.
    - **CD** (`_coordination_head`): the collapse stops at a `conj` step from a nominal onto a verb
      **in a clause slot**, where argument coordination ends. A verb that is itself an argument
      stays walked through (paradiso 12:95, which the first variant re-flagged).
    - **CB** (`_stranded_on_underived_complement`): an oblique the tree hangs on an `attr`/`xcomp`
      complement the derivation never promotes, so the argument has one home in each reading and
      they are the same ("e **al sì e al no** discordi **fensi**"). Rules S/T's lemma gate.
      Censused at 566.
    - **CE**, **CF**, **CJ** (`_control_subject_candidates`): three legs on rule V's candidate set
      — the antecedent's own relative pronoun (2061), the controller fused into a clitic host
      ("tenerla **serrata**", 66), and controllers Layer 4 labelled `obl` ("s'avacci **lor**
      divenir **sante**").
    - **CG** (`_gapped_coordinate_oblique`): the coordinate oblique whose noun is elided, citable
      only by its adjective, with the second `case` child as the evidence and the gate ("or dal
      sinistro e or dal destro fianco"). Censused at 56.
    - **CH** (`_verb_in_adnominal_slot`): rule Z's adnominal leg. A verb in `amod`/`acl` is a
      reduced relative clause, which the derivation already reads as a predicate whenever it has an
      argument to be found by; one with nothing but its subject is the same reading the derivation
      is silent about ("fogliette pur mo **nate**").
    - **CI** (rule AA's host gate): the small clause's host is read through rule C's collapse, so a
      participle on a coordinate object is recognised ("e l'uno e **l'altro mosso**").
21. **Phase 6 — rules CK-CO, from the Purgatorio 11-15 read** (2026-08-16). Five rules, each
    censused corpus-wide, measured alone by violation diff and mutation-checked; together with the
    `dep.subject_agreement` coordinated-subject refinement, 11 Layer-4 rows, 8 Layer-2 rows, 1
    Layer-3 span and 1 case-annex row, **448 → 427 soft**, no model calls. Full evidence in
    [`CORRECTIONS.md`](CORRECTIONS.md).
    - **CK** (`_clause_named_by_marker` / `_marker_of_derived_clause`): the LLM names a subordinate
      clause by the complementizer that opens it, the derivation by its verb ("degno / ben è
      **che** 'l nome di tal valle **pèra**"). One gate written from both sides, so the marker is
      not an `extra_arg` and the clause not a `missing_arg`. Censused at 18, of which the 3 with
      matching roles are taken; the 15 that pair the LLM's `subj` against a derived `ccomp` are the
      impersonal subject-clause question and stay out.
    - **CL** (`_accept_control_subjects`): rule AG's third leg. Once AG has dropped an inherited
      subject that contradicts the predicate's own person, the derivation asserts *no* subject, so
      the slot is LLM-authoritative on branch 2's terms — validated against rule V's candidate set,
      not accepted outright ("e tutti li sgomenta", purgatorio 14:60).
    - **CM** (`_fused_clitic_dual_role`): rule AL read through the `case` annex instead of a fixed
      role pair. A fused clitic whose two annex slots back the two disputed roles *separately* is
      filling both ("in Siena **sen** pispiglia", `reflexive+ablative`). Censused at 13 fused
      role_mismatch positions, 7 of which split this way.
    - **CN** (`derive_unit`, rule AN's slot assignment): a slot the head clause fills with ∅ goes
      to the **back** of the queue. ∅ = (0, 0) sorts before every real position, so the empty
      subject slot was taking the *first* remnant of every gapped clause under a pro-drop
      predicate ("molti di vita e **sé** di pregio priva").
    - **CO** (rule AU's `advmod` leg): a second predicative adjective Layer 4 hangs `advmod` on the
      predicate's own complement rather than `amod` on its argument ("esser contento **più
      digiuno**"). Censused at 101 / 77.
22. **Phase 6 — rules CP-CT, from the Purgatorio 16-20 read** (2026-08-16). Four Layer-5 rules and
    one `dep.subject_agreement` refinement, each censused corpus-wide, measured alone by violation
    diff and mutation-checked; together with 17 Layer-4 rows, 2 Layer-2 rows, 1 Layer-3 span and
    2 case-annex rows, **427 → 409 soft**, no model calls. Full evidence in
    [`CORRECTIONS.md`](CORRECTIONS.md).
    - **CP** (`_depictive_bare_oblique`, rule AZ's noun leg): a bare caseless `obl` **nominal** is
      the predicate's secondary predicate, exactly as an adjective in the same slot already was
      ("come fatto fui **roman pastore**"). Censused at 245 nominal against 44 adjectival; the
      adverb leg stays declined and the pronoun leg is refused outright (509 clitics).
    - **CQ** (`_marked_complement_clause`, rule T's `xcomp` leg): the prepositional infinitive
      Layer 4 attaches as a complement while writing its preposition as a `case` child, so the
      derivation says `xcomp` and the LLM `obl:di` ("desideroso **di sapere**"). Gated on the
      lemma being one the tree carries on that very token.
    - **CS** (`_classify_divergence`, the `missing_tuple` loop): a derived predicate whose tuple is
      **empty** asserts nothing, so the LLM's not proposing it is not a divergence ("**Nullo**,
      però che …"). The variant that refuses to mint the predicate at all, by POS, was measured at
      **+180** and rejected.
    - **CT** (`_copula_under_its_complement`): a copula Layer 4 hung *under* its own predicate
      complement, which the LLM reads as the predication it is ("quant' **esser può** … di nuvol
      **tenebrata**"). Censused at 25 `essere` clauses under a nominal head against 294 `advcl`
      verbs there in all — the copular lemma is the gate.
    - **CR** (`dep.subject_agreement`): the "1/2 plural head admits a singular member" exclusion
      covers the *number* test, not the person one — a lone third-person subject cannot be a member
      of a "we" ("contrario suon **prendemo**"). The 3 positions it surfaced are quantifiers
      resuming a plural and join `_DISTRIBUTIVE_LEMMAS`; `dep --check` stays 0/0.
23. **Phase 6 — rules CU-CY, from the Purgatorio 21-25 read** (2026-08-16). Four Layer-5 rules and
    one `dep.subject_agreement` refinement, each censused corpus-wide, measured alone by violation
    diff and mutation-checked; together with 27 Layer-4 rows and 1 Layer-2 row, **409 → 388 soft**,
    no model calls. Full evidence in [`CORRECTIONS.md`](CORRECTIONS.md).
    - **CW** (`_gapped_second_term_argument`, rule BA's oblique leg): two derived subjects on one
      predicate is Layer 4 collapsing **two clauses** onto one head, so the arguments standing
      after the second subject belong to the elided one ("così **quello in giuso**", "e **io di
      rietro inver' l'altura**"). Censused at 85 such arguments, 13 of them uncited, all gapped.
    - **CX** (`_wh_word_of_derived_clause`, rule CK widened): the LLM names an indirect question by
      the **interrogative word** that opens it, in the complement slot the derivation gives the
      clause ("riduci a mente **qual** fosti meco"). Gated on rule BW's POS test, on both roles
      being complement roles, and on the word being the leftmost token of the clause subtree; the
      clause's own `nsubj` is refused, that being rule BI's construction.
    - **CU** (`_apply_subj_authority`): a pro-drop ∅ the LLM lists **beside** the derived subject
      is the slot not decided, not a second claim — rule BA's principle read from the LLM's end
      ("tanti secoli **giaciuto** / qui se'"). Only the ∅ half is dropped.
    - **CY** (the clausal-complement double-listing skip): the test reads the `aux` edge, so a
      clause the LLM lists under its auxiliary counts as listed ("chi v'**ha** … tanto
      **scorte**?"). Censused at 1 and kept for consistency with `_aux_of_derived_predicate`.
    - **CV** (`dep.subject_agreement`): the *number*-only exclusions ran **before** the person test
      and took it down with them — rule CR's finding, in six more places and as an ordering defect
      ("né 'l dir l'andar … **andavam** forte"). Plus a transitive `conj` walk (a coordination is a
      chain) and `tutto` joining `_DISTRIBUTIVE_LEMMAS`; `dep --check` stays 0/0.
24. **Phase 6 — rules CZ-DD, from the Purgatorio 26-30 read** (2026-08-17). Five Layer-5 rules,
    one of them in `derive_unit` itself, each censused corpus-wide, measured alone by violation
    diff and mutation-checked; together with 12 Layer-4 rows, **388 → 358 soft**, no model calls.
    Full evidence in [`CORRECTIONS.md`](CORRECTIONS.md).
    - **DA** (the `empty_derived` gate, rule CS's argument leg): a derived tuple that is **empty**
      asserts nothing, so it contradicts no argument the LLM puts on the predicate either ("Poco
      **parer** potea lì del di fori"). **Except in the subject slot**, where an empty tuple is
      rule V having walked the control chain and *declined* — opening the gate there breaks the
      five near-miss tests of the rule-V family (BB, CF, CI, CJ), which is how the boundary was
      found. 17 positions, against 23 for the unrestricted form.
    - **DD** (`_relative_adverb_oblique`): the relative locative adverb Layer 4 writes as a `case`
      on its own clause's finite verb is that clause's locative adjunct ("questo mondo / **dove**
      poter peccar non è più nostro"). Censused at 21 such rows, every one of them on a verb — a
      Layer-4 convention applied consistently, so the fix belongs here and not upstream.
    - **CZ** (`derive_unit`, rule AN's slot claim): a gapped-clause remnant the `case` annex
      assigns a case to claims the slot that case names, before the role-rank queue hands out the
      rest ("**lei** lo vedere, e me l'ovrare appaga", where `lei` is accusative). Rule AN's
      comment had promised slot order "in the order the predicate's own arguments stand in the
      line" while its sort key used role rank; ordering by position instead measures −2/+3,
      because Dante inverts a gapped clause's halves chiastically ("onde fa l'arco il Sole e
      **Delia il cinto**") as readily as he parallels them. `derive_unit` gained an optional
      `case_rows_by_line` parameter, read at this one site.
    - **DB** (`_prepositional_copular_complement`, rule AD's mismatch leg): a copula's only
      complement, an adverb Layer 4 wrote as `obl` rather than `advmod` because it carries a
      preposition ("a tutti altri sapori esto è **di sopra**"). Gated on the copula having no
      other complement — `essere` with one already in hand takes prepositional phrases as
      ordinary adjuncts.
    - **DC** (`_secondary_predicate_over_argument`, host gate): rule AA/AU's host test read
      through rule CE's relative-pronoun identity — inside a relative clause the derived argument
      is `che` and the adjective hangs on the antecedent it stands for ("come ninfe che si givan
      **sole**"). Structural census 489; moves 1, the same trade rule CI recorded.
25. **Phase 6 — rules DE-DF, from the Purgatorio 31-33 read** (2026-08-17). Two Layer-5 rules,
    each censused, measured alone by violation diff and mutation-checked; together with 4 Layer-4
    rows, 1 Layer-2 row, 2 Layer-3 spans and 2 case-annex rows, **358 → 351 soft**, no model
    calls. Both are an existing normalization applied at a gate that had not read it — the
    ordering question a fifth consecutive batch has asked. Full evidence in
    [`CORRECTIONS.md`](CORRECTIONS.md).
    - **DF** (`_accept_control_subjects`): rule V's control/raising candidate set read through
      rule AI's Layer-3 NP-head equivalence. Rule V's candidates are Layer 4's attachment points
      and the LLM cites a phrase by Layer 3's head ("l'altre tre si fero avanti, **danzando**",
      where Layer 4 subjects `fero` on `altre` and Layer 3 heads `[l'altre tre]` on `tre`); rule
      AI cannot reach it, because it pairs citations of a role the derivation *has* and an
      inherited subject is exactly the role it does not. −4/+0.
    - **DE** (`_collapse_coordination` / `_distinctly_marked_conjunct`): a conjunct's role never
      displaces the coordination head's **own** citation when the conjunct carries a distinct
      `case` marker of its own ("la flagellò **dal capo** infin **le piante**" — two prepositional
      phrases, not one named twice). Censused at 98 such `conj` nominals; rank still decides
      between two collapsed conjuncts. Ungated the rule measures −2/+1, because apposition is the
      shape where the conjunct's role is the right one (purgatorio 3:30). −2/+0.
26. **Phase 6 — rules DG-DJ, from the Paradiso 1-5 read** (2026-08-17). Four Layer-5 rules, each
    censused, measured alone by violation diff and mutation-checked; together with 6 Layer-4 rows,
    1 Layer-2 row, 1 Layer-3 span and 2 case-annex rows, **298 → 288 soft**, no model calls. The
    batch's finding is that a gate written to admit a specific *disagreement* can exclude the case
    where the two sides agree outright — strictly the weaker claim. Full evidence in
    [`CORRECTIONS.md`](CORRECTIONS.md).
    - **DJ** (`_wh_word_of_derived_clause`): rule CX's complement-role gate dropped where the two
      sides name the **same** role. That gate licenses `obj` ↔ `ccomp`, a difference of notation;
      identical roles is the case where there is no difference to license at all ("Veramente
      **quant'** io … potei **far** tesoro, / sarà ora materia del mio canto", where both readings
      put the free relative in the subject slot). Also reaches a comparative (paradiso 23:14) and
      a quantified nominal whose Layer-3 span is headed on the same token (purgatorio 11:41).
      Censused at 28; −3/+0.
    - **DI** (`_gapped_clause_read_as_predicate`): rule AN's acceptance leg. Rule AN reads Layer
      4's `orphan` as a gapped clause and hands its remnants to the coordination head's slots; the
      LLM heads the same gap on the remnant itself ("de la voglia assoluta **intende**, e **io**
      de l'**altra**"). Which token carries the second clause's tuple is the citation convention
      rules CA/CC established. Censused at 13 such derived arguments (18 `orphan` deprels in all),
      2 of which the LLM heads as a predicate; −2/+0.
    - **DG** (membership check, in `validate_unit`): rule C's coordination collapse applied where
      the citation is still raw. Rule AQ′ exactly: `_collapse_coordination` merges a `conj`
      citation onto its head before the divergence check, and the membership check runs earlier
      ("cui più si convenia dicer 'Mal feci' / **che, servando, far peggio**"). −1/+0.
    - **DH** (`_gapped_first_term_argument`): rule CW's mirror leg — the elided clause is the
      **first** one. Rule CW drops the remnants standing after the second of two derived subjects
      because the LLM read the first clause; at "**Beatrice in suso**, e io in lei guardava" the
      verb's own 1sg morphology says it read the second, so the remnant is the oblique before its
      subject. Gated on which subject the LLM named, so the two legs stay disjoint. Censused at
      64 / 2; −1/+0.

27. **Phase 6 — rules DK-DR, from the Paradiso 6-10 read** (2026-08-17). **Eight** Layer-5 rules,
    each censused, measured alone by violation diff and mutation-checked; together with 10
    Layer-4 rows, 2 Layer-2 rows and 2 case-annex rows, **288 → 261 soft**, no model calls. The
    batch's finding is that a rule's docstring can be more correct than its code — two rules
    (DL, DM) are one extra condition dropped, in each case a part-of-speech gate inherited from
    the single line that motivated the rule and absent from the rule's own stated reason. Full
    evidence in [`CORRECTIONS.md`](CORRECTIONS.md).
    - **DO** (`_donor_predicate_disagrees`): rule AG's agreement test asked of the two
      **predicates**. Rule AG compares the `conj`-inherited nominal with the predicate it lands
      on, which decides nothing when the nominal is a third-person noun; two finite verbs sharing
      one subject must agree with each other, and that is decidable whenever both carry person and
      number ("Cunizza fui chiamata … a me medesma **indulgo** … e non mi **noia**"). Censused at
      30 of 1151 inheritance candidates — 25 rule AG calls undecidable and 5 it calls *agree*;
      −5/+0.
    - **DQ** (`_impersonal_clausal_subject`): the impersonal verb whose subject is its own
      `che`-clause ("di sua nobilità **convien che caggia**", "**par** ch'abbia", "**avvegna** che
      si rauni"). Reaches the family the Paradiso 1-5 batch dropped as needing a verb-valency
      lexicon, with two purely structural gates instead: the derived subject must be inherited
      across `conj`, and a `ccomp` must be the only other thing derived for the predicate.
      Censused at 217; −5/+0.
    - **DL** (`_prepositional_copular_complement`): rule DB's part-of-speech gate dropped. Rule
      DB's deciding test is that the copula has **no other complement**; the requirement that the
      complement be an adverb came from rule AD, where it is load-bearing, and does nothing here
      ("tal ch'**è da sermone**", "elli **era d'alte lode**", "**sarebbe a maraviglia**"). Censused
      at 492 sole-complement `obl` children of `essere`, 78 of them the adverbs rule DB had;
      −5/+0.
    - **DP** (`_antecedent_for_relative_pronoun`, second leg): the relative clause with **no
      relativizer at all**. An `acl:relcl` edge is the claim that its head is a participant of the
      clause, and with no pronoun inside it the edge is Layer 4's only record of that ("credo che
      l'alta **letizia** … per te si **veggia**"). Gated to a role the derivation left empty, to
      the non-complement roles (the free-relative shape is rules AE/BT's), and to the clause
      having no relativizer of any kind. Censused at 474 of 3261; −3/+0.
    - **DK** (`_antecedent_for_relative_pronoun`): the antecedent, where the derivation names that
      clause's own relative pronoun — one referent under two names, which is `skel.antecedent`'s
      own stated policy and rule CE's identity moved to the argument comparison. Reads the
      antecedent through rule C's coordination collapse, because the LLM's citation already has
      been ("e in **dolcezza** **ch'** esser non pò nota"). Censused at 2574 of 3261; −2/+0.
    - **DR** (`_comparative_come_adjunct`): `quasi` is the third marker of rule AR's verbless
      comparison, and Layer 4 writes it `advmod` because Layer 2 calls it an adverb ("**quasi
      animal** di sua seta fasciato", "**Quasi ammiraglio** che in poppa e in prora"). Censused at
      52 `quasi` rows, every one `advmod`, 9 of them on an `obl`; −2/+0.
    - **DM** (`_comparative_come_complement`): rule AK's gate read as the negative its own
      docstring states — no layer calls the particle a preposition — rather than as the one tag
      the evidence line carried. The census of comparative particles in a `case` slot is 150 and
      only 117 are conjunctions: `come`/`com'` is an adverb 24 times and `qual` an adjective or
      pronoun 5 ("mi si fece in vista **qual fin balasso**"). −1/+0.
    - **DN** (`_raised_infinitive_subject`): the subject Layer 4 writes inside a periphrasis, on
      the `xcomp` infinitive rather than the modal ("e **ciò** **esser** non **può**"), against a
      `conj` inheritance that never saw it. Kept as an *acceptance*: the same rule in
      `derive_unit` measured −4/**+40**, because an overt subject under an `xcomp` is more often
      the accusative-and-infinitive's own. Censused at 106 of 1130; −1/+0.

**Measured Progression Across Phases**:
- **Phase 4a Checkpoint (2026-07-20)**: `0 hard, 7776 soft` (down from 17,438 initial).
- **Phase 4b `--fix` Pass (2026-07-25)**: `0 hard, 5919 soft` across all 100 cantos.
- **Phase 5 Deterministic Series & Upstream Audits (Phases 5a–5w, Rules C–AF)**: Reduced soft violations from **5,919 → 2,084**. For the complete chronological record, per-phase measurement tables, Layer-4 corrections, and empirical findings on regeneration yield, see [`PHASE5.md`](PHASE5.md).
- **Phase 6 Restructured `--fix`, Rules AG–DR**: Reduced soft violations from **2,084 → 1,091** (first user-run pass: 2011 → 1452; Rule AG: 1452 → 1409; second user-run pass: 1409 → 1247; Rules AH–AL and the Inferno 7–10 read: 1247 → 1091), then **1094** after the Layer-4 agreement close and prep-stack normalization (net zero by design), then **963** with the third user-run pass (1094 → 963, 2026-08-15), then **888** with rules AM–AT and the Inferno 11–15 read (963 → 888, 2026-08-15 — eight rules, four of them in `derive_unit` itself, plus 16 Layer-4 and 2 Layer-2 rows), then **834** with rules AU–AY and the Inferno 16–20 read (888 → 834, 2026-08-15 — five rules, three of them mirror legs of existing ones, plus 25 Layer-4 and 1 Layer-2 rows), then **691** with rules AZ–BI and the Inferno 21–25 read (834 → 691, 2026-08-15 — nine rules, plus 20 Layer-4 and 5 Layer-2 rows), then **650** with rules BJ–BN and the Inferno 26–30 read (691 → 650, 2026-08-15 — five rules plus three legs added to existing ones, and 10 Layer-4 and 1 Layer-2 rows), then **541** with the fourth user-run pass (650 → 541, 2026-08-16), then **506** with rules BO–BV and the Inferno 31–34 read (541 → 506, 2026-08-16 — eight rules, plus 15 Layer-4 rows, 2 Layer-2 rows, 1 Layer-3 span and 1 case-annex row), then **481** with rules BW–BZ and the Purgatorio 1–5 read (506 → 481, 2026-08-16 — four rules, plus 2 Layer-4 rows and 1 case-annex row), then **448** with rules CA–CJ and the Purgatorio 6–10 read (481 → 448, 2026-08-16 — ten rules, eight of them about coordination or about a predicate the derivation declines to mint, plus 1 Layer-4 row), then **427** with rules CK–CO and the Purgatorio 11–15 read (448 → 427, 2026-08-16 — five rules, the `dep.subject_agreement` coordinated-subject refinement the Inferno 21–25 batch had deferred, plus 11 Layer-4 rows, 8 Layer-2 rows, 1 Layer-3 span and 1 case-annex row), then **409** with rules CP–CT and the Purgatorio 16–20 read (427 → 409, 2026-08-16 — four Layer-5 rules and the `dep.subject_agreement` person refinement, plus 17 Layer-4 rows, 2 Layer-2 rows, 1 Layer-3 span and 2 case-annex rows), then **388** with rules CU–CY and the Purgatorio 21–25 read (409 → 388, 2026-08-16 — four Layer-5 rules and the `dep.subject_agreement` ordering refinement, plus 27 Layer-4 rows and 1 Layer-2 row), then **358** with rules CZ–DD and the Purgatorio 26–30 read (388 → 358, 2026-08-17 — five Layer-5 rules, one of them in `derive_unit`, plus 12 Layer-4 rows), then **351** with rules DE–DF and the Purgatorio 31–33 read (358 → 351, 2026-08-17 — two Layer-5 rules, plus 4 Layer-4 rows, 1 Layer-2 row, 2 Layer-3 spans and 2 case-annex rows), then **298** with the fifth user-run pass (351 → 298, 2026-08-17 — run with no prompt change and no model change, so it tested no hypothesis; what it measured is that the read series' rules and the LLM's repairs take largely disjoint residue), then **288** with rules DG–DJ and the Paradiso 1–5 read (298 → 288, 2026-08-17 — four Layer-5 rules, plus 6 Layer-4 rows, 1 Layer-2 row, 1 Layer-3 span and 2 case-annex rows), then **261** with rules DK–DR and the Paradiso 6–10 read (288 → 261, 2026-08-17 — eight Layer-5 rules, plus 10 Layer-4 rows, 2 Layer-2 rows and 2 case-annex rows). See [`PLAN.md`](PLAN.md) and [`CORRECTIONS.md`](CORRECTIONS.md).

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

uv run skel/skel.py inferno [-c SPEC] [-m MODEL] [--chunk 12] [--force] [--check] [--stats]
uv run skel/skel.py inferno purgatorio paradiso --repair    # no model call
uv run skel/skel.py inferno -m ollama:gpt-oss --fix         # all three stages
uv run skel/skel.py inferno -m ... --fix --no-whole         # without the regeneration fallback

uv run skel/read.py inferno 16 43                           # read one position, all five layers
uv run skel/read.py inferno 16 43 48                        # ... over a line range
```

`-c`/`--canto` selects which cantos to process: `1`, `11-20`, `12-` (from 12 on), `-20` (up to
20), or a comma-separated mix such as `1,3-5,11-`. It is the same selection syntax in every build
driver, and a spec matching no canto is a command-line error rather than a silent no-op.

`read.py` is the audit series' tool (see [`PLAN.md`](PLAN.md)'s *How to Read a Batch*): `--check`
names a position, `read.py` prints its whole parse unit with Layer-2 morphology and the `case`
annex, Layer-4 deprels, Layer-3 NP spans, and **both** Layer-5 readings — the frozen artifact rows
and `derive_unit`'s derived rows, which is exactly the pair the soft checks diff.

Consumers read it deterministically via `Canto.skel()` (frozen, grouped, identified
`SkelTuple`s) or the CLI `dante-corpus text skel inferno 1:1-3` (`--format json` for tuple
dicts). `skel.antecedent` resolves a relative-pronoun subject's antecedent NP at serve time
(never stored); `skel.pro_drop_features` similarly derives person/number for a `∅` subject from
the predicate's own morphology.
