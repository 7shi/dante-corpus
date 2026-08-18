# skel — Notes toward a portable Layer-5 checker

**Status: notes, not a plan in flight.** Nothing here is scheduled, and none of it should be
started before the condition in *Sequencing* below is met. `PLAN.md` remains the record of the
work and the place routes are opened; this file exists so that the portability question stops
being re-derived from scratch, and so a future cleanup does not tidy the wrong thing.

Written 2026-08-18, against `dante_corpus/skel.py` at 4484 lines.

---

## Why the file grew

`dante_corpus/skel.py` carries rules A through EG — 84 rule letters — added one read batch at a
time over 21 batches covering all 100 cantos. That growth was the method working, not the method
failing: each rule was censused corpus-wide before it was written, measured by violation diff on
its own, pinned by a mutation-checked test, and written up with its evidence line. Several
candidates were measured and rejected, and those are recorded too. The residue went from 17438 at
the first full-corpus measurement to 224.

What the method did *not* produce is any way to ask a question about the rule set **as a set**:
which rules are still load-bearing, which have been subsumed by later ones, what the ordering
between them actually is, and which of them are about Italian rather than about Universal
Dependencies. Those are the questions a port has to answer, and none of them can be answered from
the source as it stands.

## Sequencing — soft 0 is a precondition, not a milestone

**Do not restructure while the soft count is above 0.** The checker's own output is the
measurement instrument for every change made to it; the standing discipline is *measure a checker
rule by violation diff, never by the total* (`PLAN.md`, Standing Disciplines). A refactor landed
while the count is still moving cannot be shown to have moved nothing.

The inverse is the useful part: **once `--check` reports 0 hard / 0 soft over all 100 cantos, that
0 becomes a regression gate.** Any restructuring — merging rules, reordering them, extracting a
language pack, changing a signature — is then verifiable by re-running the same check and the same
`pytest` suite. That is a far stronger safety net than the project has had at any point so far,
and it is why the right move is to finish the residue first rather than to stop and tidy.

## What was measured (2026-08-18)

| | |
|---|---:|
| `dante_corpus/skel.py` total lines | 4484 |
| — code | 3171 |
| — comment | 865 |
| — blank | 448 |
| module-level functions | 135 |
| distinct rule letters referenced in comments | 84 |
| module-level constants | ~20 |
| **of those, language-specific** | **7** |

The seven:

```
_PREP_LEMMA_NORM            Italian preposition lemmas, article contractions, apocopes
_REL_PRONOUN_WORDS          relative-pronoun word forms, for the Layer-3 NP-head check
_RELATIVE_PRONOUNS          relative-pronoun word forms, for rules CE / DC / DK
_RELATIVIZERS               every word that relativizes a clause (rule DP's negative gate)
_COMPARATIVE_PARTICLES      comparison markers in a Layer-4 `case` slot (rules AK / DM)
_COMPARATIVE_LEMMAS         comparison markers by Layer-2 lemma (rule AR family)
_LOCATIVE_RELATIVE_LEMMAS   relative locatives by lemma (rule DY)
```

Everything else is UD deprel vocabulary (`_SUBJ_DEPRELS`, `_AUX_DEPRELS`, `_ELIDED_COPULA_DEPRELS`,
`_NOMINAL_SLOT_DEPRELS`, …) or this project's own frozen role vocabulary (`_ROLE_RANK`,
`_ROLE_CANON`, `_COMPLEMENT_ROLES`, `_DIRECT_ROLE_MAP`) — neither of which is about Italian.

**The three relative-pronoun sets are not duplicates, and merging them would be a bug.** They are
three different notions that happen to overlap in surface form: the word forms the NP-head check
accepts in an argument slot, the word forms rules CE/DC/DK match, and the deliberately *wider* set
rule DP uses as a **negative** gate (a clause carrying any of them has a relativizer of its own).
`_RELATIVIZERS` is documented in the source as intentionally wider than `_RELATIVE_PRONOUNS`. The
same holds for `_COMPARATIVE_PARTICLES` (by word form, in a `case` slot) versus
`_COMPARATIVE_LEMMAS` (by Layer-2 lemma). What is wrong with them is **naming, and the fact that
they are scattered** — not that there are too many.

So the headline for a port: **the Italian surface of a 4484-line checker is seven constants.** The
bulk of the file is about UD's conventions and about this corpus's five-layer stack, and both of
those travel.

## The four real couplings

### 1. Rule identity lives in comments

A rule is a named predicate function plus a `# rule XX:` comment at its call site in an
`if … continue` chain. Nothing in the program knows a rule's letter, its census, or its current
population. Consequences:

- **No rule can be re-measured without editing the source.** The censuses in `CORRECTIONS.md` are
  prose, taken at the base current when each rule was written — bases from 1452 down to 224.
- **Dead rules are invisible.** Over 84 letters and a base that fell by two orders of magnitude,
  some rules are certainly now subsumed by later ones. There is no way to find them.
- **A port cannot be prioritized.** "Which 20 rules carry 90% of the acceptances" is unanswerable.

### 2. Rule order is implicit and untested

Ordering has been the finding of several consecutive read batches (rules AQ′, DG, DS, DT, BO, BZ,
CZ) — "which check runs first" is a recurring source of real defects. Yet the order is nothing but
the line order of the `if … continue` chains in `_classify_divergence`, with no name, no test that
pins it, and no way to detect that a newly inserted rule shadowed an older one. This is the single
most fragile thing to carry to another corpus.

### 3. Tests are pinned to live corpus data

Several driver tests in `tests/test_skel_fix.py` drive `_fix_canto` against the *real* artifact of
a named canto and assert counts taken from it — `units:flagged == 1` for purgatorio 1, the
same-slot pair in inferno 5, and so on. The comments name the positions, which is what makes them
readable, but the assertions move whenever a `--fix` round touches those cantos: the seventh round
cleared purgatorio 1's two `dual_role` units and the test's `3` became `1` (2026-08-18).

That is backwards. The behaviour under test is the driver's — one question per flagged unit, keyed
to that unit's class, a refusal changing nothing — and none of it is about which cantos happen to
be flagged today. **After the residue reaches 0, move these to fixtures**: a handful of small
hand-written parse units checked into the test suite, so the driver's behaviour is pinned by data
the tests own. Keep one or two live-corpus tests deliberately, as an integration check that the
driver still runs against real artifacts, and mark them as such.

This matters twice over for a port: a new corpus has no purgatorio 1, so every data-pinned test
is dead weight on arrival, and the fixtures are exactly the thing that *does* travel.

### 4. Rules read the layer stack directly

`validate_unit` already has a clean seam — it takes `morph_rows`, `np_rows`, `dep_rows`,
`case_rows` as optional layers, and degrades when one is absent. Below it, though, individual rule
functions take derived indices positionally (`dep_index_by_pos`, `morph_pos_by_position`,
`case_children`, `case_by_position`, `children_by_pos`, `marker_lemmas`, …) and read tag text and
annex slot vocabulary inline — e.g. `_fused_clitic_dual_role` tests `tag.count("pronoun") >= 2` on
Layer-2 tag text and splits the `case` annex's slot string. Those are cross-linguistic *categories*
wearing this project's *encoding*. A port needs the categories, not the encoding.

## Proposed sequence, after 0

1. **Rule registry + one-shot census of every rule.** Move rule letters from comments into data,
   and measure each rule by the standing method — disable it, re-run `--check` over 100 cantos,
   record what comes back. Deliverable: one reproducible table of `rule → population → what it
   newly flags when removed`, replacing prose censuses taken at nine different bases.
   **This pays for itself before any port**: it names the dead rules, it makes the implicit
   ordering measurable (does removing A change B's contribution?), and it gives a port its
   priority order.
2. **Separate the driver tests from live corpus data** (coupling 3). Hand-written fixture parse
   units for the behavioural assertions; one or two live-corpus tests kept deliberately and
   labelled as integration checks. Cheap, and it is what stops a round from turning the suite red.
3. **Collect the seven language constants into one language pack,** named by what they mean rather
   than by which rule reads them, with the three relative-pronoun sets kept distinct and their
   differences documented at the point of definition rather than at the point of use.
4. **Give the layer stack an interface.** Promote the derived indices into a single object the
   rules receive, so "what a rule needs from the corpus" is declared rather than inferred from an
   argument list. Category vocabularies (pronoun-ness, annex slots) become part of that interface.

Steps 3 and 4 are cheap and low-risk once step 1 exists; without step 1 they are unverifiable
beyond "the tests still pass." Step 2 is independent of all of them and could be taken at any
time — it is placed here only because it is not urgent until a round stops being the thing that
breaks it.

## What is explicitly *not* the problem

- **The comment density.** 865 comment lines carry the evidence line, census and rejected variants
  for 84 rules. That is the project's memory, and it is what made the rules auditable. Do not
  compress it in the name of tidiness.
- **The rule count itself.** Dante is an archaic text across three styles; 84 rules is small against
  the 14,233 lines it parses. The goal is *portable rules*, not *fewer rules at the cost of
  correctness*.

---

## One-Shot Rule Census Results (Phase 8.1)

Executed across all 100 cantos (3,477 parse units) in-memory via `skel/census_rules.py`:

- **Total Registered Rules**: 130
- **Directly Active Rules (count on removal > 0)**: 82
- **Auxiliary / Structural Rules (population > 0, count on removal = 0)**: 5 (`I`, `AN`, `BN`, `CN`, `EG`)
- **Dormant / Subsumed Rules**: 43 (sub-predicates or conceptual variants subsumed by broader gates)

### Rule Census Table

| Rule ID | Name | Kind | Population | Count on Removal | Status | Description |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `1` | `clause_head_predicate` | `derivation` | 0 | 0 | **dormant** | Clause head token is a predicate |
| `2` | `verb_with_dependent_predicate` | `derivation` | 0 | 0 | **dormant** | Non-auxiliary verb carrying argument dependent is a predicate |
| `A` | `coordination_collapse_base` | `normalization` | 0 | 0 | **dormant** | Basic coordination argument mapping onto coordination head |
| `C` | `coordination_collapse` | `normalization` | 18323 | 705 | **active** | Map argument citations across conj edges onto coordination head |
| `D` | `drop_nmod_obliques` | `normalization` | 18323 | 142 | **active** | Drop nmod obliques whose parent nominal is cited as argument |
| `I` | `auxiliary_host_head` | `extra_tuple` | 193 | 0 | **auxiliary** | Lexical head attached by aux/cop is the predicate head |
| `J` | `adverbial_oblique` | `extra_arg` | 189 | 179 | **active** | Adverbial oblique in locative/directional slot |
| `L` | `oblique_lemma_refinement` | `role_mismatch` | 341 | 340 | **active** | Refinement between bare obl and lemma-qualified obl:<prep> |
| `M` | `predicative_complement` | `role_mismatch` | 142 | 133 | **active** | Predicative complement xcomp against derived obj/subj |
| `N` | `case_marked_object` | `role_mismatch` | 39 | 39 | **active** | Case-marked oblique against direct object/subject |
| `O` | `co_present_preposition` | `role_mismatch` | 127 | 127 | **active** | Co-present prepositional variants for one argument |
| `P` | `clausal_complement_flavor` | `role_mismatch` | 42 | 42 | **active** | Flavor mismatch between ccomp and xcomp |
| `Q` | `clausal_object` | `role_mismatch` | 38 | 38 | **active** | Clausal ccomp against derived direct object/subject |
| `R` | `predicative_advmod` | `extra_arg` | 96 | 90 | **active** | Predicative adjective or adverb attached as advmod or secondary predicate |
| `S` | `nmod_complement_of_predicate` | `extra_arg` | 66 | 43 | **active** | Prepositional nmod attached directly to predicate |
| `T` | `marked_adverbial_clause` | `extra_arg` | 27 | 27 | **active** | Prepositional infinitive adverbial clause attached as advcl |
| `U` | `case_corroborated_role` | `role_mismatch` | 153 | 144 | **active** | Role mismatch corroborated by Layer-2 case annex |
| `V` | `control_subject_inheritance` | `subject_authority` | 3237 | 2137 | **active** | Non-finite verb control subject inheritance along head chain |
| `W` | `case_corroborated_swap` | `role_mismatch` | 26 | 26 | **active** | Swap partner of a case-corroborated role assignment |
| `X` | `copular_hosted_argument` | `extra_arg` | 63 | 6 | **active** | Argument cited on copula complement vs matrix predicate |
| `Y` | `copular_nominal_predication` | `extra_tuple` | 203 | 202 | **active** | Copular nominal clause head attached under nominal deprel |
| `Z` | `verb_in_argument_slot` | `extra_tuple` | 70 | 69 | **active** | Verb in argument/adjunct slot proposed as predicate |
| `AA` | `perception_depictive_small_clause` | `extra_arg` | 34 | 29 | **active** | Perception or depictive small clause secondary predicate |
| `AB` | `reflexive_clitic_argument` | `extra_arg` | 74 | 74 | **active** | Reflexive clitic argument of pronominal verb |
| `AC` | `inherited_subject_not_independent` | `subject_authority` | 16 | 23 | **active** | Inherited subject across conj is not an independent assertion |
| `AD` | `copular_adverb_complement` | `extra_arg` | 14 | 14 | **active** | Copular adverb complement accepted as predicative modifier |
| `AE` | `free_relative_head` | `extra_arg` | 3 | 3 | **active** | Free relative clause cited by verb rather than relative pronoun |
| `AF` | `dep_argument_membership` | `membership` | 80 | 80 | **active** | Layer-4 argument deprel position admissible as Layer-5 argument |
| `AG` | `conj_subject_person_mismatch` | `subject_authority` | 58 | 2 | **active** | Drop conj-inherited subject when person/number disagrees |
| `AH` | `silent_derivation_after_subject_drop` | `subject_authority` | 43 | 43 | **active** | Derivation remains silent when inherited subject is dropped |
| `AI` | `np_head_equivalence` | `normalization` | 18323 | 33 | **active** | Re-key given citation onto derived citation for same Layer-3 NP |
| `AJ` | `conj_shared_argument` | `extra_arg` | 58 | 53 | **active** | Argument shared across coordinate conjuncts |
| `AK` | `comparative_come_complement` | `role_mismatch` | 12 | 8 | **active** | Comparative come phrase as predicative complement |
| `AL` | `fused_clitic_dual_role` | `role_mismatch` | 3 | 3 | **active** | Fused clitic pronoun legitimately filling two argument slots |
| `AM` | `cop_aux_stranded_arguments` | `derivation` | 18340 | 33 | **active** | Collect arguments stranded on cop/aux dependents |
| `AN` | `gapped_conjunct_remnant` | `derivation` | 2 | 0 | **auxiliary** | Gapped conjunct carrying orphan fills predicate slots as remnants |
| `AP` | `coordination_head_walk` | `normalization` | 0 | 0 | **dormant** | Walk conj chain to find coordination head |
| `AQ` | `auxiliary_citation_merge` | `normalization` | 18323 | 14 | **active** | Map argument citations landing on aux/cop onto lexical head |
| `AR` | `comparative_come_adjunct` | `missing_arg` | 24 | 19 | **active** | Verbless comparative clause nominal in adjunct slot |
| `AS` | `fused_clitic_role_widening` | `role_mismatch` | 0 | 0 | **dormant** | Widen role gate for fused clitic combinations |
| `AT` | `verb_only_conj_subject_inheritance` | `derivation` | 125 | 20 | **active** | Only verbs inherit subjects across conj chains |
| `AU` | `adjective_secondary_predicate` | `extra_arg` | 0 | 0 | **dormant** | Adjective attached amod to argument acting as secondary predicate |
| `AV` | `named_by_its_auxiliary` | `missing_tuple` | 5 | 5 | **active** | Derived predicate named by auxiliary in LLM output |
| `AW` | `pronominal_verb_clitic_omitted` | `missing_arg` | 21 | 21 | **active** | Pronominal verb clitic omitted in LLM reading |
| `AX` | `xcomp_control_partner_hosted` | `extra_arg` | 12 | 12 | **active** | Argument hung on opposite end of xcomp edge |
| `AY` | `complemented_adjective_phrase` | `extra_tuple` | 6 | 6 | **active** | Adjective phrase governing an argument proposed as predicate |
| `AZ` | `depictive_bare_oblique` | `role_mismatch` | 25 | 22 | **active** | Depictive adjective attached as bare obl vs attr/xcomp |
| `BA` | `undecided_subject_slot` | `missing_arg` | 29 | 18 | **active** | Derivation produced two subjects without disambiguating |
| `BB` | `coordinate_control_subjects` | `subject_authority` | 0 | 0 | **dormant** | Accept all conjuncts of a coordinate controller |
| `BC` | `adverbial_oblique_pos_filter` | `extra_arg` | 0 | 0 | **dormant** | Filter adverbial obliques by Layer-2 POS |
| `BD` | `pronominal_verb_clitic_mismatch` | `role_mismatch` | 3 | 3 | **active** | Reflexive clitics in pronominal verbs with minor role discrepancy |
| `BE` | `coordination_head_cycle_guard` | `normalization` | 0 | 0 | **dormant** | Cycle protection in coordination head walk |
| `BF` | `inverted_copula_complement` | `extra_arg` | 8 | 7 | **active** | Inverted copula dependency structure |
| `BH` | `displaced_subject_pro_drop` | `extra_arg` | 14 | 14 | **active** | Displaced pro-drop subject when subject is expressed elsewhere |
| `BI` | `accusative_and_infinitive` | `extra_arg` | 11 | 11 | **active** | Accusative-and-infinitive subject/object sharing |
| `BJ` | `adverb_preposition_cluster` | `normalization` | 18323 | 30 | **active** | Merge multi-word adverb-preposition cluster citations |
| `BK` | `comparative_che_marker` | `missing_arg` | 0 | 0 | **dormant** | Verbless comparative clause marked by che |
| `BL` | `comparative_si_come_marker` | `missing_arg` | 0 | 0 | **dormant** | Verbless comparative clause marked by sì come |
| `BM` | `conjunction_oblique` | `missing_arg` | 12 | 11 | **active** | Connective conjunction parked by Layer 4 in adjunct slot |
| `BN` | `conjunction_clause_head_predicate` | `derivation` | 4 | 0 | **auxiliary** | Filter out conjunctions attached as clause heads without arguments |
| `BO` | `ordering_ai_before_d` | `normalization` | 0 | 0 | **dormant** | Ordering gate: rule AI runs before rule D |
| `BP` | `hosts_child_aux_normalization` | `normalization` | 0 | 0 | **dormant** | Normalize aux/cop dependencies in child host checks |
| `BQ` | `adverb_cluster_orders` | `normalization` | 0 | 0 | **dormant** | Support alternative word orders in adverb-preposition clusters |
| `BR` | `nested_in_named_phrase` | `missing_arg` | 19 | 6 | **active** | Argument nested inside a larger Layer-3 noun phrase named by LLM |
| `BS` | `copular_predication_via_aux` | `extra_tuple` | 0 | 0 | **dormant** | Copular predication named by copula token |
| `BT` | `free_relative_matrix_head` | `extra_arg` | 2 | 1 | **active** | Free relative clause attached under matrix predicate |
| `BU` | `coordination_last_conjunct_subject` | `subject_authority` | 6 | 2 | **active** | Subject supplied by the last conjunct of a coordination |
| `BV` | `prep_stack_nominal` | `normalization` | 18323 | 6 | **active** | Normalize multi-word preposition fixed/case tokens onto nominal head |
| `BW` | `marker_slot_argument` | `extra_arg` | 12 | 12 | **active** | Interrogative or relative marker token filling an argument slot |
| `BX` | `depictive_bare_oblique_omitted` | `missing_arg` | 10 | 10 | **active** | Depictive bare oblique omitted in LLM reading |
| `BY` | `auxiliary_host_argument` | `missing_arg` | 7 | 7 | **active** | Argument hung on this predicate's own aux/cop periphrasis |
| `BZ` | `finite_verb_conj_chain_walk` | `derivation` | 3477 | 2 | **active** | Conj chain subject propagation restricted to finite verbs |
| `CA` | `non_verb_conj_argument_test` | `derivation` | 177 | 1 | **active** | Non-verb conjunct promoted only if it carries argument child |
| `CB` | `stranded_on_underived_complement` | `extra_arg` | 0 | 0 | **dormant** | Argument attached to predicative complement underived in Layer 5 |
| `CC` | `promoted_conjunct_argument` | `extra_arg` | 0 | 0 | **dormant** | Coordinate nominal promoted to conj on predicate without slot |
| `CD` | `coordination_head_termination` | `normalization` | 0 | 0 | **dormant** | Coordination head search termination condition |
| `CE` | `relative_pronoun_antecedent` | `subject_authority` | 0 | 0 | **dormant** | Relative pronoun and antecedent co-indexing in control chain |
| `CF` | `fused_clitic_controller` | `subject_authority` | 0 | 0 | **dormant** | Extract controller hidden inside fused clitic pronoun |
| `CG` | `gapped_coordinate_oblique` | `extra_arg` | 0 | 0 | **dormant** | Elided coordinate oblique citable only by modifier |
| `CH` | `verb_in_adnominal_slot` | `extra_tuple` | 3 | 3 | **active** | Participle or verb in amod/acl slot acting as reduced relative |
| `CI` | `host_position_coordination_resolution` | `extra_arg` | 0 | 0 | **dormant** | Resolve host positions through coordination collapse |
| `CJ` | `oblique_controller` | `subject_authority` | 0 | 0 | **dormant** | Controller in Layer 4 obl slot in control candidate walk |
| `CK` | `clause_named_by_marker` | `missing_arg` | 5 | 4 | **active** | Subordinate clause cited by its marker/complementizer |
| `CL` | `fallback_control_subject_after_ag` | `subject_authority` | 19 | 3 | **active** | Fall back to control subject when rule AG drops inherited subject |
| `CM` | `clitic_case_slot_mapping` | `role_mismatch` | 0 | 0 | **dormant** | Map clitic pronoun to case annex slot |
| `CN` | `pro_drop_queue_back` | `derivation` | 13 | 0 | **auxiliary** | Pro-drop null subject slot placed at back of queue |
| `CP` | `nominal_pos_classification` | `extra_arg` | 0 | 0 | **dormant** | Identify adjective and noun POS for secondary predication |
| `CQ` | `marked_complement_clause` | `role_mismatch` | 3 | 3 | **active** | Prepositional infinitive complement clause as xcomp |
| `CS` | `empty_derived_tuple` | `missing_tuple` | 12 | 12 | **active** | Role-less empty derived tuple treated as non-asserting |
| `CT` | `copula_under_its_complement` | `extra_arg` | 2 | 2 | **active** | Copula attached under its own predicate complement |
| `CU` | `pro_drop_and_concrete_double_listing` | `subject_authority` | 2 | 2 | **active** | Accept double listing of pro-drop ∅ and concrete subject |
| `CW` | `gapped_second_term_argument` | `missing_arg` | 5 | 5 | **active** | Second term of gapped comparison clause |
| `CX` | `wh_word_of_derived_clause` | `extra_arg` | 0 | 0 | **dormant** | Interrogative wh-word opening a subordinate clause |
| `CY` | `clausal_complement_aux_double_listing` | `missing_arg` | 858 | 834 | **active** | Clausal complement double-listed under auxiliary |
| `CZ` | `gapped_remnant_case_annex_slot` | `derivation` | 13 | 2 | **active** | Gapped remnant case assignment via Layer-2 case annex |
| `DA` | `empty_derived_predicate_non_subj` | `extra_arg` | 20 | 20 | **active** | Empty derived predicate cannot contradict non-subject arguments |
| `DB` | `prepositional_copular_complement` | `role_mismatch` | 9 | 9 | **active** | Copular complement carrying prepositional marker |
| `DC` | `host_position_relative_resolution` | `extra_arg` | 0 | 0 | **dormant** | Resolve host position through relative pronoun identity |
| `DD` | `relative_locative_adverb` | `extra_arg` | 5 | 5 | **active** | Relative locative adverb attached as case on clause |
| `DE` | `head_names_own_role` | `normalization` | 0 | 0 | **dormant** | Coordination head names its own role independently |
| `DF` | `control_candidate_np_normalization` | `subject_authority` | 0 | 0 | **dormant** | Apply rule AI NP-head normalization to control candidates |
| `DG` | `membership_coordination_normalization` | `membership` | 1 | 1 | **active** | Apply coordination collapse in raw membership check |
| `DH` | `gapped_first_term_argument` | `missing_arg` | 1 | 1 | **active** | First term of gapped comparison clause |
| `DI` | `gapped_clause_read_as_predicate` | `missing_arg` | 2 | 2 | **active** | Gapped clause headed on remnant read as predicate |
| `DJ` | `wh_word_identical_role` | `extra_arg` | 0 | 0 | **dormant** | Wh-word opening clause with identical role |
| `DK` | `antecedent_for_relative_pronoun` | `extra_arg` | 6 | 6 | **active** | Antecedent cited where derivation names relative pronoun |
| `DL` | `prepositional_copular_gate_pruning` | `role_mismatch` | 0 | 0 | **dormant** | Pruned redundant gate in prepositional copular complement |
| `DM` | `comparative_particles_in_case_slot` | `role_mismatch` | 0 | 0 | **dormant** | Comparison markers in Layer-4 case slot |
| `DN` | `raised_infinitive_subject` | `missing_arg` | 1 | 1 | **active** | Subject written inside periphrasis by Layer 4 |
| `DO` | `donor_predicate_disagrees` | `subject_authority` | 4 | 5 | **active** | Donor predicate disagrees in person/number with target |
| `DP` | `relative_clause_relativizer_gate` | `extra_arg` | 0 | 0 | **dormant** | Negative gate: clause relativized by non-pronoun particle |
| `DQ` | `impersonal_clausal_subject` | `missing_arg` | 5 | 5 | **active** | Impersonal verb whose subject is its own che-clause |
| `DR` | `comparative_quasi_marker` | `missing_arg` | 0 | 0 | **dormant** | Verbless comparison marked by quasi |
| `DS` | `membership_marker_slot_normalization` | `membership` | 1 | 1 | **active** | Marker slot argument normalization in raw membership check |
| `DT` | `ordering_constraint_audit` | `normalization` | 0 | 0 | **dormant** | Ordering constraint between classification rules |
| `DU` | `conj_subject_chain_cut_by_pro_drop` | `derivation` | 2 | 2 | **active** | Conj subject chain cut by explicit pro-drop ∅ |
| `DV` | `stranded_underived_via_au_host` | `extra_arg` | 0 | 0 | **dormant** | Stranded complement read through rule AU adjective host |
| `DW` | `depictive_attr_omitted` | `missing_arg` | 2 | 2 | **active** | Depictive attr omitted in LLM reading |
| `DX` | `predicative_advmod_adjective` | `extra_arg` | 0 | 0 | **dormant** | Predicative adjective attached as advmod |
| `DY` | `relative_locative_lemmas` | `extra_arg` | 0 | 0 | **dormant** | Relative locative markers identified by Layer-2 lemma |
| `DZ` | `conjunct_named_by_phrase_head` | `extra_arg` | 0 | 0 | **dormant** | Rule AI NP-head equivalence read through rule C coordination collapse |
| `EA` | `speech_act_nominal` | `extra_arg` | 1 | 1 | **active** | Elided speech verb parataxis on pronoun asserts lone ∅ subject |
| `EB` | `comparative_come_phrase_boundary` | `missing_arg` | 0 | 0 | **dormant** | Boundary check for comparative come phrases |
| `EC` | `comparative_come_correlative` | `missing_arg` | 0 | 0 | **dormant** | Correlative comparison marker in comparative come phrases |
| `ED` | `comparison_clause_host` | `extra_arg` | 1 | 1 | **active** | Comparison clause headed on come with adjunct on matrix verb |
| `EE` | `prep_stack_fixed_child` | `normalization` | 0 | 0 | **dormant** | Fixed child in multiword preposition stack |
| `EF` | `conj_subject_sibling_cut` | `derivation` | 36 | 5 | **active** | Conj subject inheritance walk stops at sibling with subject |
| `EG` | `dual_role_artifact_contradiction` | `dual_role` | 3477 | 0 | **auxiliary** | One token filling two incompatible roles of one predicate |
| `EH` | `fused_clitic_lemma_alignment` | `role_mismatch` | 0 | 0 | **dormant** | Positionally aligned lemma components for fused clitics |
| `EI` | `floating_quantifier_citation_merge` | `normalization` | 18323 | 4 | **active** | Re-key given floating quantifier citation onto derived nominal head |

## Open questions

- **What is the porting target?** "Another language" and "another corpus in the same language" are
  different problems: the first needs the language pack, the second needs the layer stack (a UD
  parse, a morphology layer, NP spans, a pronoun-case annex) to exist at all. The five-layer stack
  is the deeper assumption, and nothing here loosens it.
- **Does the authority model port?** `derive_unit` encodes decisions (pro-drop subjects, control
  subject propagation across `conj`, gapped-clause remnants) that are correct for a pro-drop,
  heavily-inverting poetic language. Which of those are UD-general and which are Italian is not
  known and is not answerable from the constants alone — it is a question for the census in step 1.
- **Should the checker and the derivation separate?** They are one module today. The acceptance
  rules compare an artifact with `derive_unit`'s reading; rule EG is the first check that reads the
  artifact against itself and needs no derivation at all. If that class grows, the two may want to
  be separable.
