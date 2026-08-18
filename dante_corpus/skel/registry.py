"""Layer-5 Rule Registry and rule metadata."""

from __future__ import annotations

from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass


@dataclass(frozen=True)
class Rule:
    """A registered Layer-5 skeleton derivation or verification rule."""

    id: str
    name: str
    kind: str
    description: str


class RuleRegistry:
    """Registry managing Layer-5 rules and their active status / execution metrics."""

    def __init__(self) -> None:
        self._rules: dict[str, Rule] = {}
        self._disabled: set[str] = set()
        self._hits: Counter[str] = Counter()

    def register(self, id: str, name: str, kind: str, description: str) -> Rule:
        rule = Rule(id=id, name=name, kind=kind, description=description)
        self._rules[id] = rule
        return rule

    def is_enabled(self, id: str) -> bool:
        return id not in self._disabled

    def disable(self, id: str) -> None:
        self._disabled.add(id)

    def enable(self, id: str) -> None:
        self._disabled.discard(id)

    def reset_disabled(self) -> None:
        self._disabled.clear()

    def record_hit(self, id: str) -> None:
        self._hits[id] += 1

    def hit_count(self, id: str) -> int:
        return self._hits[id]

    def reset_hits(self) -> None:
        self._hits.clear()

    def get(self, id: str) -> Rule | None:
        return self._rules.get(id)

    def all_rules(self) -> list[Rule]:
        return list(self._rules.values())

    def rule(self, id: str, name: str, kind: str, description: str) -> Callable:
        """Decorator for registering a rule function."""
        rule = self.register(id, name, kind, description)

        def decorator(fn: Callable) -> Callable:
            fn._rule = rule  # type: ignore[attr-defined]
            return fn

        return decorator


RULES = RuleRegistry()


def rule_active(id: str) -> bool:
    """Check if rule is enabled and record a hit for census metrics."""
    if not RULES.is_enabled(id):
        return False
    RULES.record_hit(id)
    return True


# Populate rule registry with all Layer-5 rules (A through EI, plus 1 and 2)
_RULES_CATALOG: list[tuple[str, str, str, str]] = [
    ("1", "clause_head_predicate", "derivation", "Clause head token is a predicate"),
    ("2", "verb_with_dependent_predicate", "derivation", "Non-auxiliary verb carrying argument dependent is a predicate"),
    ("A", "coordination_collapse_base", "normalization", "Basic coordination argument mapping onto coordination head"),
    ("C", "coordination_collapse", "normalization", "Map argument citations across conj edges onto coordination head"),
    ("D", "drop_nmod_obliques", "normalization", "Drop nmod obliques whose parent nominal is cited as argument"),
    ("I", "auxiliary_host_head", "extra_tuple", "Lexical head attached by aux/cop is the predicate head"),
    ("J", "adverbial_oblique", "extra_arg", "Adverbial oblique in locative/directional slot"),
    ("L", "oblique_lemma_refinement", "role_mismatch", "Refinement between bare obl and lemma-qualified obl:<prep>"),
    ("M", "predicative_complement", "role_mismatch", "Predicative complement xcomp against derived obj/subj"),
    ("N", "case_marked_object", "role_mismatch", "Case-marked oblique against direct object/subject"),
    ("O", "co_present_preposition", "role_mismatch", "Co-present prepositional variants for one argument"),
    ("P", "clausal_complement_flavor", "role_mismatch", "Flavor mismatch between ccomp and xcomp"),
    ("Q", "clausal_object", "role_mismatch", "Clausal ccomp against derived direct object/subject"),
    ("R", "predicative_advmod", "extra_arg", "Predicative adjective or adverb attached as advmod or secondary predicate"),
    ("S", "nmod_complement_of_predicate", "extra_arg", "Prepositional nmod attached directly to predicate"),
    ("T", "marked_adverbial_clause", "extra_arg", "Prepositional infinitive adverbial clause attached as advcl"),
    ("U", "case_corroborated_role", "role_mismatch", "Role mismatch corroborated by Layer-2 case annex"),
    ("V", "control_subject_inheritance", "subject_authority", "Non-finite verb control subject inheritance along head chain"),
    ("W", "case_corroborated_swap", "role_mismatch", "Swap partner of a case-corroborated role assignment"),
    ("X", "copular_hosted_argument", "extra_arg", "Argument cited on copula complement vs matrix predicate"),
    ("Y", "copular_nominal_predication", "extra_tuple", "Copular nominal clause head attached under nominal deprel"),
    ("Z", "verb_in_argument_slot", "extra_tuple", "Verb in argument/adjunct slot proposed as predicate"),
    ("AA", "perception_depictive_small_clause", "extra_arg", "Perception or depictive small clause secondary predicate"),
    ("AB", "reflexive_clitic_argument", "extra_arg", "Reflexive clitic argument of pronominal verb"),
    ("AC", "inherited_subject_not_independent", "subject_authority", "Inherited subject across conj is not an independent assertion"),
    ("AD", "copular_adverb_complement", "extra_arg", "Copular adverb complement accepted as predicative modifier"),
    ("AE", "free_relative_head", "extra_arg", "Free relative clause cited by verb rather than relative pronoun"),
    ("AF", "dep_argument_membership", "membership", "Layer-4 argument deprel position admissible as Layer-5 argument"),
    ("AG", "conj_subject_person_mismatch", "subject_authority", "Drop conj-inherited subject when person/number disagrees"),
    ("AH", "silent_derivation_after_subject_drop", "subject_authority", "Derivation remains silent when inherited subject is dropped"),
    ("AI", "np_head_equivalence", "normalization", "Re-key given citation onto derived citation for same Layer-3 NP"),
    ("AJ", "conj_shared_argument", "extra_arg", "Argument shared across coordinate conjuncts"),
    ("AK", "comparative_come_complement", "role_mismatch", "Comparative come phrase as predicative complement"),
    ("AL", "fused_clitic_dual_role", "role_mismatch", "Fused clitic pronoun legitimately filling two argument slots"),
    ("AM", "cop_aux_stranded_arguments", "derivation", "Collect arguments stranded on cop/aux dependents"),
    ("AN", "gapped_conjunct_remnant", "derivation", "Gapped conjunct carrying orphan fills predicate slots as remnants"),
    ("AP", "coordination_head_walk", "normalization", "Walk conj chain to find coordination head"),
    ("AQ", "auxiliary_citation_merge", "normalization", "Map argument citations landing on aux/cop onto lexical head"),
    ("AR", "comparative_come_adjunct", "missing_arg", "Verbless comparative clause nominal in adjunct slot"),
    ("AS", "fused_clitic_role_widening", "role_mismatch", "Widen role gate for fused clitic combinations"),
    ("AT", "verb_only_conj_subject_inheritance", "derivation", "Only verbs inherit subjects across conj chains"),
    ("AU", "adjective_secondary_predicate", "extra_arg", "Adjective attached amod to argument acting as secondary predicate"),
    ("AV", "named_by_its_auxiliary", "missing_tuple", "Derived predicate named by auxiliary in LLM output"),
    ("AW", "pronominal_verb_clitic_omitted", "missing_arg", "Pronominal verb clitic omitted in LLM reading"),
    ("AX", "xcomp_control_partner_hosted", "extra_arg", "Argument hung on opposite end of xcomp edge"),
    ("AY", "complemented_adjective_phrase", "extra_tuple", "Adjective phrase governing an argument proposed as predicate"),
    ("AZ", "depictive_bare_oblique", "role_mismatch", "Depictive adjective attached as bare obl vs attr/xcomp"),
    ("BA", "undecided_subject_slot", "missing_arg", "Derivation produced two subjects without disambiguating"),
    ("BB", "coordinate_control_subjects", "subject_authority", "Accept all conjuncts of a coordinate controller"),
    ("BC", "adverbial_oblique_pos_filter", "extra_arg", "Filter adverbial obliques by Layer-2 POS"),
    ("BD", "pronominal_verb_clitic_mismatch", "role_mismatch", "Reflexive clitics in pronominal verbs with minor role discrepancy"),
    ("BE", "coordination_head_cycle_guard", "normalization", "Cycle protection in coordination head walk"),
    ("BF", "inverted_copula_complement", "extra_arg", "Inverted copula dependency structure"),
    ("BH", "displaced_subject_pro_drop", "extra_arg", "Displaced pro-drop subject when subject is expressed elsewhere"),
    ("BI", "accusative_and_infinitive", "extra_arg", "Accusative-and-infinitive subject/object sharing"),
    ("BJ", "adverb_preposition_cluster", "normalization", "Merge multi-word adverb-preposition cluster citations"),
    ("BK", "comparative_che_marker", "missing_arg", "Verbless comparative clause marked by che"),
    ("BL", "comparative_si_come_marker", "missing_arg", "Verbless comparative clause marked by sì come"),
    ("BM", "conjunction_oblique", "missing_arg", "Connective conjunction parked by Layer 4 in adjunct slot"),
    ("BN", "conjunction_clause_head_predicate", "derivation", "Filter out conjunctions attached as clause heads without arguments"),
    ("BO", "ordering_ai_before_d", "normalization", "Ordering gate: rule AI runs before rule D"),
    ("BP", "hosts_child_aux_normalization", "normalization", "Normalize aux/cop dependencies in child host checks"),
    ("BQ", "adverb_cluster_orders", "normalization", "Support alternative word orders in adverb-preposition clusters"),
    ("BR", "nested_in_named_phrase", "missing_arg", "Argument nested inside a larger Layer-3 noun phrase named by LLM"),
    ("BS", "copular_predication_via_aux", "extra_tuple", "Copular predication named by copula token"),
    ("BT", "free_relative_matrix_head", "extra_arg", "Free relative clause attached under matrix predicate"),
    ("BU", "coordination_last_conjunct_subject", "subject_authority", "Subject supplied by the last conjunct of a coordination"),
    ("BV", "prep_stack_nominal", "normalization", "Normalize multi-word preposition fixed/case tokens onto nominal head"),
    ("BW", "marker_slot_argument", "extra_arg", "Interrogative or relative marker token filling an argument slot"),
    ("BX", "depictive_bare_oblique_omitted", "missing_arg", "Depictive bare oblique omitted in LLM reading"),
    ("BY", "auxiliary_host_argument", "missing_arg", "Argument hung on this predicate's own aux/cop periphrasis"),
    ("BZ", "finite_verb_conj_chain_walk", "derivation", "Conj chain subject propagation restricted to finite verbs"),
    ("CA", "non_verb_conj_argument_test", "derivation", "Non-verb conjunct promoted only if it carries argument child"),
    ("CB", "stranded_on_underived_complement", "extra_arg", "Argument attached to predicative complement underived in Layer 5"),
    ("CC", "promoted_conjunct_argument", "extra_arg", "Coordinate nominal promoted to conj on predicate without slot"),
    ("CD", "coordination_head_termination", "normalization", "Coordination head search termination condition"),
    ("CE", "relative_pronoun_antecedent", "subject_authority", "Relative pronoun and antecedent co-indexing in control chain"),
    ("CF", "fused_clitic_controller", "subject_authority", "Extract controller hidden inside fused clitic pronoun"),
    ("CG", "gapped_coordinate_oblique", "extra_arg", "Elided coordinate oblique citable only by modifier"),
    ("CH", "verb_in_adnominal_slot", "extra_tuple", "Participle or verb in amod/acl slot acting as reduced relative"),
    ("CI", "host_position_coordination_resolution", "extra_arg", "Resolve host positions through coordination collapse"),
    ("CJ", "oblique_controller", "subject_authority", "Controller in Layer 4 obl slot in control candidate walk"),
    ("CK", "clause_named_by_marker", "missing_arg", "Subordinate clause cited by its marker/complementizer"),
    ("CL", "fallback_control_subject_after_ag", "subject_authority", "Fall back to control subject when rule AG drops inherited subject"),
    ("CM", "clitic_case_slot_mapping", "role_mismatch", "Map clitic pronoun to case annex slot"),
    ("CN", "pro_drop_queue_back", "derivation", "Pro-drop null subject slot placed at back of queue"),
    ("CP", "nominal_pos_classification", "extra_arg", "Identify adjective and noun POS for secondary predication"),
    ("CQ", "marked_complement_clause", "role_mismatch", "Prepositional infinitive complement clause as xcomp"),
    ("CS", "empty_derived_tuple", "missing_tuple", "Role-less empty derived tuple treated as non-asserting"),
    ("CT", "copula_under_its_complement", "extra_arg", "Copula attached under its own predicate complement"),
    ("CU", "pro_drop_and_concrete_double_listing", "subject_authority", "Accept double listing of pro-drop ∅ and concrete subject"),
    ("CW", "gapped_second_term_argument", "missing_arg", "Second term of gapped comparison clause"),
    ("CX", "wh_word_of_derived_clause", "extra_arg", "Interrogative wh-word opening a subordinate clause"),
    ("CY", "clausal_complement_aux_double_listing", "missing_arg", "Clausal complement double-listed under auxiliary"),
    ("CZ", "gapped_remnant_case_annex_slot", "derivation", "Gapped remnant case assignment via Layer-2 case annex"),
    ("DA", "empty_derived_predicate_non_subj", "extra_arg", "Empty derived predicate cannot contradict non-subject arguments"),
    ("DB", "prepositional_copular_complement", "role_mismatch", "Copular complement carrying prepositional marker"),
    ("DC", "host_position_relative_resolution", "extra_arg", "Resolve host position through relative pronoun identity"),
    ("DD", "relative_locative_adverb", "extra_arg", "Relative locative adverb attached as case on clause"),
    ("DE", "head_names_own_role", "normalization", "Coordination head names its own role independently"),
    ("DF", "control_candidate_np_normalization", "subject_authority", "Apply rule AI NP-head normalization to control candidates"),
    ("DG", "membership_coordination_normalization", "membership", "Apply coordination collapse in raw membership check"),
    ("DH", "gapped_first_term_argument", "missing_arg", "First term of gapped comparison clause"),
    ("DI", "gapped_clause_read_as_predicate", "missing_arg", "Gapped clause headed on remnant read as predicate"),
    ("DJ", "wh_word_identical_role", "extra_arg", "Wh-word opening clause with identical role"),
    ("DK", "antecedent_for_relative_pronoun", "extra_arg", "Antecedent cited where derivation names relative pronoun"),
    ("DL", "prepositional_copular_gate_pruning", "role_mismatch", "Pruned redundant gate in prepositional copular complement"),
    ("DM", "comparative_particles_in_case_slot", "role_mismatch", "Comparison markers in Layer-4 case slot"),
    ("DN", "raised_infinitive_subject", "missing_arg", "Subject written inside periphrasis by Layer 4"),
    ("DO", "donor_predicate_disagrees", "subject_authority", "Donor predicate disagrees in person/number with target"),
    ("DP", "relative_clause_relativizer_gate", "extra_arg", "Negative gate: clause relativized by non-pronoun particle"),
    ("DQ", "impersonal_clausal_subject", "missing_arg", "Impersonal verb whose subject is its own che-clause"),
    ("DR", "comparative_quasi_marker", "missing_arg", "Verbless comparison marked by quasi"),
    ("DS", "membership_marker_slot_normalization", "membership", "Marker slot argument normalization in raw membership check"),
    ("DT", "ordering_constraint_audit", "normalization", "Ordering constraint between classification rules"),
    ("DU", "conj_subject_chain_cut_by_pro_drop", "derivation", "Conj subject chain cut by explicit pro-drop ∅"),
    ("DV", "stranded_underived_via_au_host", "extra_arg", "Stranded complement read through rule AU adjective host"),
    ("DW", "depictive_attr_omitted", "missing_arg", "Depictive attr omitted in LLM reading"),
    ("DX", "predicative_advmod_adjective", "extra_arg", "Predicative adjective attached as advmod"),
    ("DY", "relative_locative_lemmas", "extra_arg", "Relative locative markers identified by Layer-2 lemma"),
    ("DZ", "conjunct_named_by_phrase_head", "extra_arg", "Rule AI NP-head equivalence read through rule C coordination collapse"),
    ("EA", "speech_act_nominal", "extra_arg", "Elided speech verb parataxis on pronoun asserts lone ∅ subject"),
    ("EB", "comparative_come_phrase_boundary", "missing_arg", "Boundary check for comparative come phrases"),
    ("EC", "comparative_come_correlative", "missing_arg", "Correlative comparison marker in comparative come phrases"),
    ("ED", "comparison_clause_host", "extra_arg", "Comparison clause headed on come with adjunct on matrix verb"),
    ("EE", "prep_stack_fixed_child", "normalization", "Fixed child in multiword preposition stack"),
    ("EF", "conj_subject_sibling_cut", "derivation", "Conj subject inheritance walk stops at sibling with subject"),
    ("EG", "dual_role_artifact_contradiction", "dual_role", "One token filling two incompatible roles of one predicate"),
    ("EH", "fused_clitic_lemma_alignment", "role_mismatch", "Positionally aligned lemma components for fused clitics"),
    ("EI", "floating_quantifier_citation_merge", "normalization", "Re-key given floating quantifier citation onto derived nominal head"),
]
for _rid, _rname, _rkind, _rdesc in _RULES_CATALOG:
    RULES.register(_rid, _rname, _rkind, _rdesc)
