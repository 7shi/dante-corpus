"""Divergence classification rules (Rules A–EI) and subject authority handlers."""

from __future__ import annotations

import re

from ..case import SLOT_SEP
from ..dep import DepRow, subject_agreement
from ..morph import MorphRow, Violation
from ..np import NPSpan
from .derive import (
    ARG_DEPRELS,
    CLAUSE_HEAD_DEPRELS,
    _ADJECTIVE_COMPLEMENT_DEPRELS,
    _ADNOMINAL_DEPRELS,
    _AUX_DEPRELS,
    _CONJ_WALK_LIMIT,
    _DIRECT_ROLE_MAP,
    _ELIDED_COPULA_DEPRELS,
    _FLOATING_QUANTIFIERS,
    _NOMINAL_SLOT_DEPRELS,
    _QUANTIFIER_POS,
    _SUBJ_DEPRELS,
    _accept_control_subjects,
    _adverb_cluster_head,
    _aux_head,
    _case_supports_role,
    _collapse_coordination,
    _conj_shared_argument,
    _conjunct_named_by_phrase_head,
    _coordination_head,
    _distinctly_marked_conjunct,
    _donor_predicate_disagrees,
    _finite_head_of,
    _floating_quantifier_of,
    _inherited_subject,
    _merge_adverb_cluster_citations,
    _merge_auxiliary_citations,
    _merge_floating_quantifier_citations,
    _merge_np_head_citations,
    _nested_in_named_phrase,
    _np_head_equivalent,
    _prep_stack_nominal,
    is_verb_pos,
)
from .models import (
    _COMPARATIVE_LEMMAS,
    _COMPARATIVE_PARTICLES,
    _LOCATIVE_RELATIVE_LEMMAS,
    _RELATIVE_PRONOUNS,
    _RELATIVIZERS,
    OBL_RE,
    SkelRow,
    _canonicalize_role,
    _normalize_prep_lemma,
    _role_rank,
)
from .registry import rule_active


def _predicate_positions_in(rows_by_line: dict[int, list[SkelRow]]) -> set[tuple[int, int]]:
    return {
        (row.line, row.token)
        for rows in rows_by_line.values()
        for row in rows
        if row.token > 0
    }


def _subj_arg(by_arg_map: dict[tuple[int, int], str]) -> tuple[int, int] | None:
    return next((arg for arg, role in by_arg_map.items() if role == "subj"), None)


def _apply_subj_authority(
    g: dict[tuple[int, int], str], d: dict[tuple[int, int], str],
    pos: tuple[int, int], derived_by_pred: dict[tuple[int, int], list[SkelRow]],
    dep_index_by_pos: dict[tuple[int, int], DepRow],
    given_by_pred: "dict[tuple[int, int], list[SkelRow]] | None" = None,
    morph_rows: dict[int, list[MorphRow]] | None = None,
    children_by_pos: "dict[tuple[int, int], list[DepRow]] | None" = None,
    np_spans_by_line: "dict[int, list[NPSpan]] | None" = None,
) -> None:
    """Mutate `g`/`d` in place: drop the subj arg where PLAN.md's authority model makes the slot
    LLM-authoritative (validated against a candidate set) rather than derive-authoritative (exact
    match, the default `by_arg` diff already handles).
    """
    d_subj = _subj_arg(d)
    # Rule CU: the LLM filled the subject slot **twice**, once with pro-drop ∅ and once with the
    # very token the derivation supplies.
    if d_subj not in (None, (0, 0)) and g.get((0, 0)) == "subj" and g.get(d_subj) == "subj" and rule_active("CU"):
        g.pop((0, 0), None)
    if d_subj == (0, 0):
        # Pro-drop antecedent: derive_unit only knows ∅; any concrete subject the LLM resolves is
        # strictly more informative, not wrong.
        g_subj = _subj_arg(g)
        if g_subj is not None:
            g.pop(g_subj, None)
        d.pop((0, 0), None)
    elif d_subj is None:
        # derive_unit asserted no subject at all: the predicate is non-finite, so ∅ is accepted
        # and so is any subject rule V's head-chain walk can reach.
        _accept_control_subjects(g, pos, derived_by_pred, dep_index_by_pos, morph_rows,
                                 np_spans_by_line)
    elif (morph_rows is not None and children_by_pos is not None
          and _inherited_subject(pos, dep_index_by_pos)
          and _subj_arg(g) != d_subj
          and ((subject_agreement(d_subj, _finite_head_of(pos, children_by_pos, morph_rows),
                                 morph_rows, children_by_pos)[0] == "disagree" and rule_active("AG"))
               or (_donor_predicate_disagrees(pos, d_subj, dep_index_by_pos, children_by_pos,
                                             morph_rows) and rule_active("DO")))):
        # Rule AG: derive_unit's conj-subject-propagation (step 3) walks the conj chain
        # unconditionally, with no agreement gate.
        d.pop(d_subj, None)
        if _subj_arg(g) == (0, 0):
            if rule_active("AH"):
                g.pop((0, 0), None)
        else:
            if rule_active("CL"):
                _accept_control_subjects(g, pos, derived_by_pred, dep_index_by_pos, morph_rows,
                                         np_spans_by_line)
    elif given_by_pred is not None and _inherited_subject(pos, dep_index_by_pos):
        # Rule AC: an inherited subject is not an independent assertion about *this* predicate.
        g_subj = _subj_arg(g)
        if g_subj is None or g_subj == d_subj:
            return
        head = _coordination_head(pos, dep_index_by_pos)
        head_given = next(
            ((r.arg_line, r.arg_token) for r in given_by_pred.get(head, ()) if r.role == "subj"),
            None,
        )
        if head_given == g_subj and rule_active("AC"):
            g.pop(g_subj, None)
            d.pop(d_subj, None)
            return
        # Rule BU: the subject a coordination supplies from its **last** conjunct.
        if children_by_pos is not None and g_subj is not None and rule_active("BU"):
            for child in children_by_pos.get(pos, ()):
                if child.deprel != "conj":
                    continue
                conjunct = (child.line, child.token)
                if any(k.deprel in _SUBJ_DEPRELS and (k.line, k.token) == g_subj
                       for k in children_by_pos.get(conjunct, ())):
                    g.pop(g_subj, None)
                    d.pop(d_subj, None)
                    return


def _is_nominal_pos(pos_text: str) -> bool:
    """Rule CP: an adjective or a noun — the two POS a secondary predicate is written with."""
    text = pos_text.lower()
    if "pronoun" in text:
        return False
    return "adjective" in text or "noun" in text


def _hosts_child(
    pos: tuple[int, int], row: DepRow, dep_index_by_pos: dict[tuple[int, int], DepRow]
) -> bool:
    """Rule BP: whether `row` is a child of the predicate at `pos`, reading an `aux`/`cop` head
    through to its lexical word."""
    head = (row.head_line, row.head_token)
    return head == pos or _aux_head(head, dep_index_by_pos) == pos


def _adverbial_oblique(
    pos: tuple[int, int], arg: tuple[int, int], role: str,
    dep_index_by_pos: dict[tuple[int, int], DepRow],
    morph_pos_by_position: dict[tuple[int, int], str] | None,
) -> bool:
    """Rule J: a given `obl`/`obl:<prep>` whose argument is an adverb attached to that same
    predicate as `advmod` ("quivi", "là", "dinanzi") — an adverbial oblique."""
    if not (role == "obl" or OBL_RE.fullmatch(role)):
        return False
    row = dep_index_by_pos.get(arg)
    if row is None or row.deprel != "advmod" or not _hosts_child(pos, row, dep_index_by_pos):
        return False
    arg_pos = (morph_pos_by_position or {}).get(arg, "").lower()
    return any(tag in arg_pos for tag in ("adverb", "noun", "pronoun"))


def _predicative_advmod(
    pos: tuple[int, int], arg: tuple[int, int], role: str,
    dep_index_by_pos: dict[tuple[int, int], DepRow],
    morph_pos_by_position: dict[tuple[int, int], str] | None,
) -> bool:
    """Rule R: a given `xcomp` whose argument is an **adjective** attached to that same predicate
    as `advmod`."""
    if role != "xcomp":
        return False
    row = dep_index_by_pos.get(arg)
    if row is None or row.deprel != "advmod" or not _hosts_child(pos, row, dep_index_by_pos):
        return False
    arg_pos = (morph_pos_by_position or {}).get(arg, "").lower()
    if "pronoun" in arg_pos:
        return False
    return "adjective" in arg_pos or "noun" in arg_pos


def _accusative_and_infinitive(
    pos: tuple[int, int], arg: tuple[int, int], role: str,
    dep_index_by_pos: dict[tuple[int, int], DepRow] | None,
    morph_features_by_position: dict[tuple[int, int], str] | None = None,
) -> bool:
    """Rule BI: the accusative-and-infinitive's shared nominal, named from the matrix side."""
    if role != "obj" or dep_index_by_pos is None:
        return False
    row = dep_index_by_pos.get(arg)
    if row is None or row.deprel not in ("nsubj", "nsubj:pass"):
        return False
    host_pos = (row.head_line, row.head_token)
    host = dep_index_by_pos.get(host_pos)
    if host is None:
        return False
    if host.deprel not in ("xcomp", "ccomp"):
        if host.deprel != "obj" or "infinitive" not in (
                morph_features_by_position or {}).get(host_pos, "").lower():
            return False
    return (host.head_line, host.head_token) == pos


def _displaced_subject_pro_drop(
    grole: str, arg: tuple[int, int],
    g: dict[tuple[int, int], str], d: dict[tuple[int, int], str],
) -> bool:
    """Rule BH: rule M's mirror leg — the ∅ subject rule M's relabelling leaves behind."""
    if grole != "subj" or arg != (0, 0):
        return False
    return any(role == "subj" and g.get(a) == "xcomp" for a, role in d.items())


def _inverted_copula_complement(
    pos: tuple[int, int], arg: tuple[int, int], role: str,
    dep_index_by_pos: dict[tuple[int, int], DepRow] | None,
    morph_pos_by_position: dict[tuple[int, int], str] | None,
) -> bool:
    """Rule BF: a `cop` edge Layer 4 wrote the wrong way round."""
    if role != "xcomp":
        return False
    row = (dep_index_by_pos or {}).get(arg)
    if row is None or row.deprel != "cop" or not _hosts_child(pos, row, dep_index_by_pos):
        return False
    arg_pos = (morph_pos_by_position or {}).get(arg, "").lower()
    return "verb" not in arg_pos and any(t in arg_pos for t in ("adjective", "noun"))


def _undecided_subject_slot(
    drole: str, arg: tuple[int, int],
    g: dict[tuple[int, int], str], d: dict[tuple[int, int], str],
) -> bool:
    """Rule BA: `derive_unit` gave one predicate **two** subjects, and the LLM named one of them."""
    if drole != "subj" or arg == (0, 0):
        return False
    derived_subjects = [a for a, role in d.items() if role == "subj"]
    if len(derived_subjects) < 2:
        return False
    return any(g.get(a) == "subj" for a in derived_subjects)


def _gapped_clause_read_as_predicate(
    pos: tuple[int, int], arg: tuple[int, int],
    dep_index_by_pos: dict[tuple[int, int], DepRow] | None,
    children_by_pos: dict[tuple[int, int], list[DepRow]] | None,
    given_preds: frozenset[tuple[int, int]] | set[tuple[int, int]],
) -> bool:
    """Rule DI: rule AN's acceptance leg — the gapped clause the LLM heads on its own remnant."""
    if arg == (0, 0) or dep_index_by_pos is None or children_by_pos is None:
        return False
    for head in (arg, *(_owner for _owner in _gap_owner(arg, dep_index_by_pos))):
        if head not in given_preds:
            continue
        if not any(c.deprel == "orphan" for c in children_by_pos.get(head, ())):
            continue
        row = dep_index_by_pos.get(head)
        if row is not None and (row.head_line, row.head_token) == pos:
            return True
    return False


def _gap_owner(
    arg: tuple[int, int], dep_index_by_pos: dict[tuple[int, int], DepRow]
) -> tuple[tuple[int, int], ...]:
    """The position `arg` is an `orphan` of, if any (rule DI's second citation)."""
    row = dep_index_by_pos.get(arg)
    if row is None or row.deprel != "orphan":
        return ()
    return ((row.head_line, row.head_token),)


def _gapped_first_term_argument(
    arg: tuple[int, int], g: dict[tuple[int, int], str], d: dict[tuple[int, int], str],
) -> bool:
    """Rule DH: rule CW's mirror leg — the elided clause is the **first** one."""
    if arg == (0, 0):
        return False
    subjects = sorted(a for a, role in d.items() if role == "subj" and a != (0, 0))
    return len(subjects) >= 2 and arg < subjects[-1] and g.get(subjects[-1]) == "subj"


def _gapped_second_term_argument(
    arg: tuple[int, int], d: dict[tuple[int, int], str],
) -> bool:
    """Rule CW: rule BA's oblique leg — the rest of the elided clause the second subject opens."""
    if arg == (0, 0):
        return False
    subjects = sorted(a for a, role in d.items() if role == "subj" and a != (0, 0))
    return len(subjects) >= 2 and arg > subjects[-1]


def _depictive_bare_oblique(
    grole: str, drole: str, pos: tuple[int, int], arg: tuple[int, int],
    dep_index_by_pos: dict[tuple[int, int], DepRow] | None,
    morph_pos_by_position: dict[tuple[int, int], str] | None,
    case_children: set[tuple[int, int]],
) -> bool:
    """Rule AZ: rule R's mirror leg — the depictive adjective Layer 4 hung on the predicate as a
    bare `obl` instead of as `advmod`."""
    if grole != "xcomp" or drole != "obl":
        return False
    if arg in case_children:
        return False
    row = (dep_index_by_pos or {}).get(arg)
    if row is None or row.deprel != "obl" or not _hosts_child(pos, row, dep_index_by_pos):
        return False
    return _is_nominal_pos((morph_pos_by_position or {}).get(arg, ""))


def _nmod_complement_of_predicate(
    pos: tuple[int, int], arg: tuple[int, int], role: str,
    dep_index_by_pos: dict[tuple[int, int], DepRow],
    case_lemmas: dict[tuple[int, int], set[str]],
) -> bool:
    """Rule S: a given `obl:<lemma>` whose argument is an `nmod` child **of the predicate itself**
    and carries a `case` child naming that same preposition."""
    if not OBL_RE.fullmatch(role):
        return False
    row = dep_index_by_pos.get(arg)
    if row is None or row.deprel != "nmod" or not _hosts_child(pos, row, dep_index_by_pos):
        return False
    return role.split(":", 1)[1] in case_lemmas.get(arg, set())


def _marked_adverbial_clause(
    pos: tuple[int, int], arg: tuple[int, int], role: str,
    dep_index_by_pos: dict[tuple[int, int], DepRow],
    marker_lemmas: dict[tuple[int, int], set[str]],
) -> bool:
    """Rule T: a given `obl:<lemma>` whose argument is an `advcl` child **of the predicate itself**
    and carries a `mark`/`case` child naming that same preposition."""
    if not OBL_RE.fullmatch(role):
        return False
    row = dep_index_by_pos.get(arg)
    if row is None or row.deprel != "advcl" or not _hosts_child(pos, row, dep_index_by_pos):
        return False
    return role.split(":", 1)[1] in marker_lemmas.get(arg, set())


def _marked_complement_clause(
    pos: tuple[int, int], grole: str, drole: str, arg: tuple[int, int],
    dep_index_by_pos: dict[tuple[int, int], DepRow] | None,
    marker_lemmas: dict[tuple[int, int], set[str]],
) -> bool:
    """Rule CQ: rule T's `xcomp` leg — the prepositional infinitive Layer 4 attached as a
    complement rather than as an adverbial clause."""
    if drole != "xcomp" or not OBL_RE.fullmatch(grole):
        return False
    row = (dep_index_by_pos or {}).get(arg)
    if row is None or not _hosts_child(pos, row, dep_index_by_pos or {}):
        return False
    return grole.split(":", 1)[1] in marker_lemmas.get(arg, set())


def _gapped_coordinate_oblique(
    pos: tuple[int, int], arg: tuple[int, int], role: str,
    dep_index_by_pos: dict[tuple[int, int], DepRow],
    children_by_pos: dict[tuple[int, int], list[DepRow]],
    d: dict[tuple[int, int], str],
) -> bool:
    """Rule CG: the coordinate oblique whose noun is elided."""
    head_row = dep_index_by_pos.get(arg)
    if head_row is None or head_row.deprel not in ("amod", "det", "det:poss", "nummod"):
        return False
    host = (head_row.head_line, head_row.head_token)
    if d.get(host) != role:
        return False
    return sum(1 for c in children_by_pos.get(host, ()) if c.deprel == "case") >= 2


def _promoted_conjunct_argument(
    pos: tuple[int, int], arg: tuple[int, int],
    dep_index_by_pos: dict[tuple[int, int], DepRow],
    children_by_pos: dict[tuple[int, int], list[DepRow]],
    morph_pos_by_position: dict[tuple[int, int], str] | None,
) -> bool:
    """Rule CC: rule CA's argument leg — the coordinate nominal Layer 4 promoted to `conj` on the
    predicate itself."""
    row = dep_index_by_pos.get(arg)
    if row is None or row.deprel != "conj":
        return False
    if (row.head_line, row.head_token) != pos:
        return False
    pos_label = (morph_pos_by_position or {}).get(arg, "")
    if not pos_label or is_verb_pos(pos_label) or "conjunction" in pos_label.lower():
        return False
    return not any(c.deprel in ARG_DEPRELS for c in children_by_pos.get(arg, ()))


def _stranded_on_underived_complement(
    pos: tuple[int, int], arg: tuple[int, int], role: str,
    dep_index_by_pos: dict[tuple[int, int], DepRow],
    derived_preds: set[tuple[int, int]],
    case_lemmas: dict[tuple[int, int], set[str]],
) -> bool:
    """Rule CB: an oblique the tree hangs on a predicative complement the derivation never promotes."""
    if not OBL_RE.fullmatch(role):
        return False
    row = dep_index_by_pos.get(arg)
    if row is None or row.deprel not in ("obl", "obl:agent"):
        return False
    host = (row.head_line, row.head_token)
    if host == pos or host in derived_preds:
        return False
    host_row = dep_index_by_pos.get(host)
    if host_row is None:
        return False
    if host_row.deprel in ("attr", "xcomp"):
        if (host_row.head_line, host_row.head_token) != pos:
            return False
    elif host_row.deprel == "amod":
        owner_row = dep_index_by_pos.get((host_row.head_line, host_row.head_token))
        if owner_row is None or owner_row.deprel not in ARG_DEPRELS:
            return False
        if (owner_row.head_line, owner_row.head_token) != pos:
            return False
    else:
        return False
    return role.split(":", 1)[1] in case_lemmas.get(arg, set())


def _drop_nmod_obliques(
    g: dict[tuple[int, int], str], d: dict[tuple[int, int], str],
    derived_args: set[tuple[int, int]], dep_index_by_pos: dict[tuple[int, int], DepRow],
) -> None:
    """Rule D: accept an oblique whose argument hangs as `nmod` off one of the predicate's own
    derived arguments. Mutates `g` in place."""
    for arg, role in list(g.items()):
        if arg in d or not (role == "obl" or OBL_RE.fullmatch(role)):
            continue
        row = dep_index_by_pos.get(arg)
        if row is not None and row.deprel == "nmod" and (row.head_line, row.head_token) in derived_args:
            g.pop(arg)


def _oblique_lemma_refinement(
    grole: str, drole: str, arg: tuple[int, int], case_children: set[tuple[int, int]]
) -> bool:
    """Rule L: derived bare `obl` vs a given `obl:<lemma>`."""
    return drole == "obl" and bool(OBL_RE.fullmatch(grole)) and arg not in case_children


def _case_marked_object(
    grole: str, drole: str, arg: tuple[int, int],
    case_lemmas: dict[tuple[int, int], set[str]],
) -> bool:
    """Rule N: a given `obl:<lemma>` against a derived `obj`/`subj`."""
    if not (OBL_RE.fullmatch(grole) and drole in ("obj", "subj")):
        return False
    return grole.split(":", 1)[1] in case_lemmas.get(arg, set())


def _co_present_preposition(
    grole: str, drole: str, arg: tuple[int, int],
    case_lemmas: dict[tuple[int, int], set[str]],
) -> bool:
    """Rule O: two different `obl:<lemma>` labels for the same argument."""
    if not (OBL_RE.fullmatch(grole) and OBL_RE.fullmatch(drole)):
        return False
    return grole.split(":", 1)[1] in case_lemmas.get(arg, set())


def _clausal_complement_flavor(grole: str, drole: str) -> bool:
    """Rule P: `ccomp` against `xcomp` (either way round)."""
    return {grole, drole} == {"ccomp", "xcomp"}


def _clausal_object(
    grole: str, drole: str, arg: tuple[int, int],
    morph_pos_by_position: dict[tuple[int, int], str] | None,
) -> bool:
    """Rule Q: a given `ccomp` against a derived `obj`/`subj` whose argument is a **verb**."""
    if not (grole == "ccomp" and drole in ("obj", "subj")):
        return False
    return is_verb_pos((morph_pos_by_position or {}).get(arg, ""))


def _predicative_complement(grole: str, drole: str) -> bool:
    """Rule M: a given `xcomp` against a derived `obj`/`subj`."""
    return grole == "xcomp" and drole in ("obj", "subj")


def _bare_pronoun_position(
    pos: tuple[int, int], morph_pos_by_position: dict[tuple[int, int], str] | None
) -> bool:
    """Whether a token is a pronoun and *nothing else* — rule U's scope gate."""
    value = (morph_pos_by_position or {}).get(pos)
    if value is None:
        return False
    return SLOT_SEP not in value and value.strip().lower().endswith("pronoun")


def _comparative_come_complement(
    grole: str, drole: str, arg: tuple[int, int],
    dep_index_by_pos: dict[tuple[int, int], DepRow] | None,
    morph_pos_by_position: dict[tuple[int, int], str] | None,
) -> bool:
    """Rule AK: a comparative `come` phrase read as a predicative complement."""
    if drole.split(":", 1)[-1] not in _COMPARATIVE_LEMMAS or grole != "xcomp":
        return False
    if dep_index_by_pos is None or morph_pos_by_position is None:
        return False
    return any(
        row.deprel == "case" and (row.head_line, row.head_token) == arg
        and row.word.lower().rstrip("'") in _COMPARATIVE_PARTICLES
        and "preposition" not in morph_pos_by_position.get((row.line, row.token), "").lower()
        for row in dep_index_by_pos.values()
    )


def _comparative_come_adjunct(
    pos: tuple[int, int], arg: tuple[int, int], drole: str,
    dep_index_by_pos: dict[tuple[int, int], DepRow] | None,
    children_by_pos: dict[tuple[int, int], list[DepRow]] | None,
    morph_pos_by_position: dict[tuple[int, int], str] | None,
    d: dict[tuple[int, int], str] | None = None,
) -> bool:
    """Rule AR: an oblique the derivation reads off a verbless comparative clause."""
    if drole != "obl" and not drole.startswith("obl:"):
        return False
    if dep_index_by_pos is None or children_by_pos is None or morph_pos_by_position is None:
        return False

    def come_mark(host: tuple[int, int], words: tuple[str, ...] = ("come", "com"),
                  deprels: tuple[str, ...] = ("mark",)) -> DepRow | None:
        for c in children_by_pos.get(host, ()):
            if c.deprel in deprels and c.word.lower().rstrip("'") in words:
                return c
        return None

    if come_mark(arg, ("come", "com", "che", "ch"), ("mark", "advmod")) is not None:
        return True
    if any(c.deprel == "advmod" and c.word.lower().rstrip("'") == "quasi"
           and "adverb" in morph_pos_by_position.get((c.line, c.token), "").lower()
           for c in children_by_pos.get(arg, ())):
        return True
    marker = come_mark(pos, deprels=("mark", "advmod"))
    if marker is None:
        return False
    correlative = next(
        (c for c in children_by_pos.get(pos, ())
         if c.deprel == "advmod" and c.word.lower().rstrip("'") in ("sì", "si", "così", "cosi")),
        None,
    )
    if correlative is None:
        subjects = sorted(a for a, role in (d or {}).items() if role == "subj" and a != (0, 0))
        return len(subjects) >= 2 and arg > (marker.line, marker.token)
    if (correlative.line, correlative.token + 1) == (marker.line, marker.token):
        own = {(c.line, c.token) for c in children_by_pos.get(arg, ())
               if c.deprel in ("det", "det:poss", "amod", "nummod", "case", "cc")}
        between = {(marker.line, t) for t in range(marker.token + 1, arg[1])} if marker.line == arg[0] else None
        return between is not None and arg > (marker.line, marker.token) and between <= own
    return (marker.line, marker.token) <= arg < (correlative.line, correlative.token)


def _conjunction_oblique(
    arg: tuple[int, int], drole: str,
    morph_pos_by_position: dict[tuple[int, int], str] | None,
) -> bool:
    """Rule BM: an oblique whose filler is a token Layer 2 calls a **conjunction**."""
    if not (drole == "obl" or OBL_RE.fullmatch(drole)):
        return False
    return "conjunction" in (morph_pos_by_position or {}).get(arg, "").lower()


def _clause_named_by_marker(
    pos: tuple[int, int], clause: tuple[int, int], role: str,
    dep_index_by_pos: dict[tuple[int, int], DepRow] | None,
    cited: dict[tuple[int, int], str],
) -> bool:
    """Rule CK: the LLM names a subordinate clause by the complementizer that opens it."""
    if dep_index_by_pos is None or clause == (0, 0):
        return False
    clause_row = dep_index_by_pos.get(clause)
    if clause_row is None or (clause_row.head_line, clause_row.head_token) != pos:
        return False
    for other, other_role in cited.items():
        if other_role != role or other == clause:
            continue
        marker = dep_index_by_pos.get(other)
        if marker is None or marker.deprel != "mark":
            continue
        if (marker.head_line, marker.head_token) == clause:
            return True
    return False


def _marker_of_derived_clause(
    pos: tuple[int, int], arg: tuple[int, int], grole: str,
    dep_index_by_pos: dict[tuple[int, int], DepRow] | None,
    derived: dict[tuple[int, int], str],
) -> bool:
    """Rule CK, read from the marker's end."""
    if dep_index_by_pos is None or arg == (0, 0):
        return False
    marker = dep_index_by_pos.get(arg)
    if marker is None or marker.deprel != "mark":
        return False
    clause = (marker.head_line, marker.head_token)
    return (clause != arg and derived.get(clause) == grole
            and _clause_named_by_marker(pos, clause, grole, dep_index_by_pos, {arg: grole}))


_COMPLEMENT_ROLES = frozenset({"obj", "ccomp", "xcomp"})


def _wh_word_of_derived_clause(
    pos: tuple[int, int], arg: tuple[int, int], grole: str,
    dep_index_by_pos: dict[tuple[int, int], DepRow] | None,
    morph_pos_by_position: dict[tuple[int, int], str] | None,
    children_by_pos: dict[tuple[int, int], list[DepRow]] | None,
    derived: dict[tuple[int, int], str],
) -> bool:
    """Rule CX: rule CK widened from the complementizer to the **interrogative word**."""
    if dep_index_by_pos is None or arg == (0, 0):
        return False
    row = dep_index_by_pos.get(arg)
    if row is None or row.deprel in _SUBJ_DEPRELS:
        return False
    clause = (row.head_line, row.head_token)
    drole = derived.get(clause)
    if clause == arg or drole is None:
        return False
    if not (drole == grole or (drole in _COMPLEMENT_ROLES and grole in _COMPLEMENT_ROLES)):
        return False
    clause_row = dep_index_by_pos.get(clause)
    if clause_row is None or (clause_row.head_line, clause_row.head_token) != pos:
        return False
    tag = (morph_pos_by_position or {}).get(arg, "").lower()
    if not tag or "conjunction" in tag:
        return False
    if not ("pronoun" in tag or "adjective" in tag or "adverb" in tag):
        return False
    return arg == min(_subtree(clause, children_by_pos) | {clause})


def _subtree(
    pos: tuple[int, int], children_by_pos: dict[tuple[int, int], list[DepRow]] | None
) -> set[tuple[int, int]]:
    """Every position below `pos` in the Layer-4 tree (rule CX's "opens the clause" test)."""
    seen: set[tuple[int, int]] = set()
    frontier = [pos]
    while frontier and len(seen) < 64:
        for child in (children_by_pos or {}).get(frontier.pop(), ()):
            node = (child.line, child.token)
            if node not in seen:
                seen.add(node)
                frontier.append(node)
    return seen


def _marker_slot_argument(
    pos: tuple[int, int], arg: tuple[int, int], grole: str,
    dep_index_by_pos: dict[tuple[int, int], DepRow] | None,
    morph_pos_by_position: dict[tuple[int, int], str] | None,
) -> bool:
    """Rule BW: rule BM's mirror leg — an argument Layer 4 parked in this predicate's `mark` slot."""
    if dep_index_by_pos is None or morph_pos_by_position is None or arg == (0, 0):
        return False
    row = dep_index_by_pos.get(arg)
    if row is None or row.deprel != "mark" or not _hosts_child(pos, row, dep_index_by_pos):
        return False
    tag = morph_pos_by_position.get(arg, "").lower()
    if not tag or "conjunction" in tag:
        return False
    return "pronoun" in tag or "adjective" in tag or "adverb" in tag


def _depictive_bare_oblique_omitted(
    pos: tuple[int, int], arg: tuple[int, int], drole: str,
    dep_index_by_pos: dict[tuple[int, int], DepRow] | None,
    morph_pos_by_position: dict[tuple[int, int], str] | None,
    case_children: set[tuple[int, int]],
) -> bool:
    """Rule BX: rule AZ's `missing_arg` leg — the depictive the LLM leaves out entirely."""
    if drole != "obl" or arg in case_children:
        return False
    row = (dep_index_by_pos or {}).get(arg)
    if row is None or row.deprel != "obl" or not _hosts_child(pos, row, dep_index_by_pos):
        return False
    return "adjective" in (morph_pos_by_position or {}).get(arg, "").lower()


def _depictive_attr_omitted(
    pos: tuple[int, int], arg: tuple[int, int], drole: str,
    dep_index_by_pos: dict[tuple[int, int], DepRow] | None,
    derived_roles: dict[tuple[int, int], str],
    morph_pos_by_position: dict[tuple[int, int], str] | None,
    case_children: set[tuple[int, int]],
) -> bool:
    """Rule DW: rule BX's `attr` leg — the depictive Layer 4 wrote in the complement slot."""
    if drole != "xcomp" or arg in case_children:
        return False
    row = (dep_index_by_pos or {}).get(arg)
    if row is None or row.deprel != "attr" or not _hosts_child(pos, row, dep_index_by_pos):
        return False
    if "adjective" not in (morph_pos_by_position or {}).get(arg, "").lower():
        return False
    return bool(set(derived_roles.values()) - {"subj", "xcomp"})


def _fused_clitic_dual_role(
    grole: str, drole: str, arg: tuple[int, int],
    morph_pos_by_position: dict[tuple[int, int], str] | None,
    case_by_position: "dict[tuple[int, int], str] | None" = None,
    morph_lemma_by_position: "dict[tuple[int, int], str] | None" = None,
) -> bool:
    """Rule AL: a fused clitic cluster that genuinely fills two roles at once."""
    if morph_pos_by_position is None:
        return False
    tag = morph_pos_by_position.get(arg, "").lower()
    if tag.count("pronoun") < 2:
        return False
    if {grole, drole} == {"obj", "obl:a"}:
        return True
    slots = [s for s in (case_by_position or {}).get(arg, "").split(SLOT_SEP) if s]
    if len(slots) < 2:
        return False

    parts = [p for p in (morph_lemma_by_position or {}).get(arg, "").lower().split(SLOT_SEP) if p]
    by_slot = dict(zip(slots, parts)) if len(parts) == len(slots) else {}

    def supported(role: str) -> set[str]:
        marker = role.split(":", 1)[1] if role.startswith("obl:") else None
        return {s for s in slots
                if _case_supports_role(s, role)
                or (s == "reflexive" and role in ("obj", "iobj", "obl:a"))
                or (marker is not None and by_slot.get(s) == marker)}

    given_slots, derived_slots = supported(grole), supported(drole)
    return bool(given_slots) and bool(derived_slots) and given_slots != derived_slots


def _case_corroborated_role(
    grole: str, drole: str, arg: tuple[int, int],
    case_by_position: dict[tuple[int, int], str] | None,
    morph_pos_by_position: dict[tuple[int, int], str] | None,
) -> bool:
    """Rule U: a role_mismatch whose argument is a pronoun the Layer-2 `case` annex holds a value for."""
    value = (case_by_position or {}).get(arg)
    if value is None or not _bare_pronoun_position(arg, morph_pos_by_position):
        return False
    return _case_supports_role(value, drole) and not _case_supports_role(value, grole)


def _case_corroborated_swap(
    grole: str, drole: str, arg: tuple[int, int],
    given_roles: dict[tuple[int, int], str], derived_roles: dict[tuple[int, int], str],
    case_by_position: dict[tuple[int, int], str] | None,
    morph_pos_by_position: dict[tuple[int, int], str] | None,
) -> bool:
    """Rule W: the swap partner of a rule-U accept."""
    if {grole, drole} != {"subj", "obj"}:
        return False
    for other, other_given in given_roles.items():
        if other == arg:
            continue
        other_derived = derived_roles.get(other)
        if other_given != drole or other_derived != grole:
            continue
        if _case_corroborated_role(other_given, other_derived, other, case_by_position,
                                   morph_pos_by_position):
            return True
    return False


def _classify_divergence(
    given: dict[int, list[SkelRow]], derived: dict[int, list[SkelRow]],
    dep_index_by_pos: dict[tuple[int, int], DepRow] | None = None,
    morph_pos_by_position: dict[tuple[int, int], str] | None = None,
    case_by_position: dict[tuple[int, int], str] | None = None,
    morph_lemma_by_position: dict[tuple[int, int], str] | None = None,
    morph_rows: dict[int, list[MorphRow]] | None = None,
    np_rows: dict[int, list[NPSpan]] | None = None,
) -> list[Violation]:
    violations: list[Violation] = []
    morph_tense_by_position: dict[tuple[int, int], str] = {
        (no, i + 1): row.tense
        for no, rows in (morph_rows or {}).items() for i, row in enumerate(rows)
    }
    morph_note_by_position: dict[tuple[int, int], str] = {
        (no, i + 1): row.note
        for no, rows in (morph_rows or {}).items() for i, row in enumerate(rows)
    }
    children_by_pos: dict[tuple[int, int], list[DepRow]] = {}
    for row in (dep_index_by_pos or {}).values():
        if not (row.head_line == 0 and row.head_token == 0):
            children_by_pos.setdefault((row.head_line, row.head_token), []).append(row)
    case_lemmas: dict[tuple[int, int], set[str]] = {}
    marker_lemmas: dict[tuple[int, int], set[str]] = {}
    for row in (dep_index_by_pos or {}).values():
        if row.deprel in ("case", "mark"):
            lemma = _normalize_prep_lemma(row.word.lower())
            marker_lemmas.setdefault((row.head_line, row.head_token), set()).add(lemma)
            if row.deprel == "case":
                case_lemmas.setdefault((row.head_line, row.head_token), set()).add(lemma)
    for row in (dep_index_by_pos or {}).values():
        if row.deprel != "fixed":
            continue
        head = dep_index_by_pos.get((row.head_line, row.head_token))
        while head is not None and head.deprel == "fixed":
            head = dep_index_by_pos.get((head.head_line, head.head_token))
        if head is not None and head.deprel == "case":
            lemma = _normalize_prep_lemma(row.word.lower())
            marker_lemmas.setdefault((head.head_line, head.head_token), set()).add(lemma)
            case_lemmas.setdefault((head.head_line, head.head_token), set()).add(lemma)
    case_children = set(case_lemmas)
    for arg in list(case_lemmas):
        head = _adverb_cluster_head(arg, dep_index_by_pos, children_by_pos, morph_pos_by_position)
        if head is not None:
            case_lemmas.setdefault(head, set()).update(case_lemmas[arg])
    copula_hosts: set[tuple[int, int]] = {
        (row.head_line, row.head_token)
        for row in (dep_index_by_pos or {}).values()
        if row.deprel in _AUX_DEPRELS
    }
    given_preds = _predicate_positions_in(given)
    derived_preds = _predicate_positions_in(derived)

    double_listed = {
        (r.arg_line, r.arg_token)
        for rows in given.values()
        for r in rows
        if r.role in ("attr", "xcomp") and (r.arg_line, r.arg_token) != (r.line, r.token)
    }
    complement_hosts: dict[tuple[int, int], set[tuple[int, int]]] = {}
    for rows in given.values():
        for r in rows:
            arg_pos = (r.arg_line, r.arg_token)
            if r.role in ("attr", "xcomp") and arg_pos != (r.line, r.token):
                complement_hosts.setdefault(arg_pos, set()).add((r.line, r.token))

    def _elided_copula_nominal(pos: tuple[int, int]) -> bool:
        if dep_index_by_pos is None or morph_pos_by_position is None:
            return False
        dep_row = dep_index_by_pos.get(pos)
        if dep_row is None or dep_row.deprel not in _ELIDED_COPULA_DEPRELS:
            return False
        pos_tag = morph_pos_by_position.get(pos, "")
        return not is_verb_pos(pos_tag)

    def _complemented_adjective_phrase(pos: tuple[int, int]) -> bool:
        if dep_index_by_pos is None or morph_pos_by_position is None:
            return False
        dep_row = dep_index_by_pos.get(pos)
        if dep_row is None or dep_row.deprel != "amod":
            return False
        if "adjective" not in morph_pos_by_position.get(pos, "").lower():
            return False
        return any(c.deprel in _ADJECTIVE_COMPLEMENT_DEPRELS
                   for c in children_by_pos.get(pos, ()))

    def _aux_of_derived_predicate(pos: tuple[int, int]) -> bool:
        if dep_index_by_pos is None:
            return False
        head = _aux_head(pos, dep_index_by_pos)
        return head != pos and head in derived_preds

    def _aux_named_predicate(arg: tuple[int, int]) -> bool:
        if dep_index_by_pos is None:
            return False
        return any(p != arg and _aux_head(p, dep_index_by_pos) == arg for p in given_preds)

    def _predicate_complements(pos: tuple[int, int]) -> set[tuple[int, int]]:
        if dep_index_by_pos is None:
            return set()
        out = set()
        for complement, hosts in complement_hosts.items():
            if pos not in hosts:
                continue
            dep_row = dep_index_by_pos.get(complement)
            if dep_row is None or dep_row.deprel not in ("attr", "xcomp"):
                continue
            if (dep_row.head_line, dep_row.head_token) == pos:
                out.add(complement)
        return out

    def _complement_hosted_argument(
        pos: tuple[int, int], arg: tuple[int, int], role: str,
        rows_by_pred: dict[tuple[int, int], list[SkelRow]],
        hosts: "set[tuple[int, int]] | None" = None,
    ) -> bool:
        for complement in (hosts if hosts is not None else _predicate_complements(pos)):
            for row in rows_by_pred.get(complement, ()):
                if (row.arg_line, row.arg_token) == arg and _canonicalize_role(row.role) == role:
                    return True
        return False

    def _control_partners(pos: tuple[int, int]) -> set[tuple[int, int]]:
        if dep_index_by_pos is None:
            return set()
        partners: set[tuple[int, int]] = set()
        row = dep_index_by_pos.get(pos)
        if row is not None and row.deprel == "xcomp":
            partners.add((row.head_line, row.head_token))
        for child in children_by_pos.get(pos, ()):
            if child.deprel == "xcomp":
                partners.add((child.line, child.token))
        return partners - {pos}

    def _free_relative_head(
        pos: tuple[int, int], arg: tuple[int, int], role: str,
        derived_roles: dict[tuple[int, int], str],
    ) -> bool:
        if dep_index_by_pos is None:
            return False
        if "pronoun" not in (morph_pos_by_position or {}).get(arg, "").lower():
            return False
        row = dep_index_by_pos.get(arg)
        if row is None or row.deprel not in _SUBJ_DEPRELS:
            return False
        clause = (row.head_line, row.head_token)
        return clause != pos and derived_roles.get(clause) == role

    def _free_relative_matrix_head(pos: tuple[int, int], arg: tuple[int, int]) -> bool:
        if dep_index_by_pos is None:
            return False
        row = dep_index_by_pos.get(pos)
        if row is None or row.deprel != "acl:relcl":
            return False
        if (row.head_line, row.head_token) != arg:
            return False
        if "pronoun" not in (morph_pos_by_position or {}).get(arg, "").lower():
            return False
        if (morph_lemma_by_position or {}).get(arg, "").lower() not in ("chi", "che", "quale"):
            return False
        if "relative" in morph_note_by_position.get(arg, "").lower():
            return False
        kids = children_by_pos.get(arg, ())
        if any(k.deprel in ("det", "amod") for k in kids):
            return False
        return not any(
            "relative" in morph_note_by_position.get((k.line, k.token), "").lower()
            for k in children_by_pos.get(pos, ())
        )

    def _copula_under_its_complement(
        pos: tuple[int, int], arg: tuple[int, int], role: str
    ) -> bool:
        if dep_index_by_pos is None:
            return False
        if role != "xcomp":
            return False
        if (morph_lemma_by_position or {}).get(pos, "").lower() != "essere":
            return False
        row = dep_index_by_pos.get(pos)
        if row is None or row.deprel not in CLAUSE_HEAD_DEPRELS:
            return False
        if (row.head_line, row.head_token) != arg:
            return False
        return _is_nominal_pos((morph_pos_by_position or {}).get(arg, ""))

    def _copular_adverb_complement(
        pos: tuple[int, int], arg: tuple[int, int], role: str
    ) -> bool:
        if dep_index_by_pos is None or role != "xcomp":
            return False
        if (morph_lemma_by_position or {}).get(pos, "").lower() != "essere":
            return False
        row = dep_index_by_pos.get(arg)
        if row is None or row.deprel != "advmod" or not _hosts_child(pos, row, dep_index_by_pos):
            return False
        return "adverb" in (morph_pos_by_position or {}).get(arg, "").lower()

    def _relative_adverb_oblique(
        pos: tuple[int, int], arg: tuple[int, int], grole: str
    ) -> bool:
        if dep_index_by_pos is None:
            return False
        if grole != "obl" and not OBL_RE.fullmatch(grole):
            return False
        row = dep_index_by_pos.get(arg)
        if row is None or row.deprel != "case":
            return False
        if (row.head_line, row.head_token) != pos:
            return False
        if (morph_lemma_by_position or {}).get(arg, "").lower() in _LOCATIVE_RELATIVE_LEMMAS:
            return True
        return "adverb" in (morph_pos_by_position or {}).get(arg, "").lower()

    def _antecedent_for_relative_pronoun(
        pos: tuple[int, int], arg: tuple[int, int], grole: str
    ) -> bool:
        if dep_index_by_pos is None:
            return False
        row = dep_index_by_pos.get(pos)
        if row is None or row.deprel != "acl:relcl":
            return False
        antecedent = (row.head_line, row.head_token)
        if arg != antecedent and arg != _coordination_head(
                antecedent, dep_index_by_pos, morph_pos_by_position):
            return False
        if any(
            drole == grole and (p := dep_index_by_pos.get(darg)) is not None
            and (p.head_line, p.head_token) == pos
            and p.word.lower().rstrip("'") in _RELATIVE_PRONOUNS
            for darg, drole in d.items()
        ):
            return True
        return (grole not in ("xcomp", "ccomp") and grole not in d.values()
                and not any(
                    r.deprel in ARG_DEPRELS and (r.head_line, r.head_token) == pos
                    and r.word.lower().rstrip("'") in _RELATIVIZERS
                    for r in dep_index_by_pos.values()))

    def _raised_infinitive_subject(
        pos: tuple[int, int], drole: str, g: dict[tuple[int, int], str]
    ) -> bool:
        if dep_index_by_pos is None or drole != "subj":
            return False
        for child in children_by_pos.get(pos, ()):
            if child.deprel != "xcomp":
                continue
            for c in children_by_pos.get((child.line, child.token), ()):
                if c.deprel in _SUBJ_DEPRELS and g.get((c.line, c.token)) == "subj":
                    return True
        return False

    def _impersonal_clausal_subject(
        pos: tuple[int, int], drole: str, d: dict[tuple[int, int], str]
    ) -> bool:
        return (drole == "subj" and dep_index_by_pos is not None
                and _inherited_subject(pos, dep_index_by_pos)
                and set(d.values()) - {"subj"} == {"ccomp"})

    def _prepositional_copular_complement(
        pos: tuple[int, int], grole: str, drole: str, arg: tuple[int, int]
    ) -> bool:
        if dep_index_by_pos is None or grole != "xcomp" or not drole.startswith("obl"):
            return False
        if (morph_lemma_by_position or {}).get(pos, "").lower() != "essere":
            return False
        row = dep_index_by_pos.get(arg)
        if row is None or row.deprel != "obl" or not _hosts_child(pos, row, dep_index_by_pos):
            return False
        return not any(_canonicalize_role(r.role) == "xcomp"
                       and (r.arg_line, r.arg_token) != arg
                       for r in derived_by_pred.get(pos, []))

    def _reflexive_clitic_argument(
        pos: tuple[int, int], arg: tuple[int, int], role: str
    ) -> bool:
        if dep_index_by_pos is None:
            return False
        row = dep_index_by_pos.get(arg)
        if row is None or row.deprel != "expl":
            return False
        if not _hosts_child(pos, row, dep_index_by_pos):
            return False
        if "pronoun" not in (morph_pos_by_position or {}).get(arg, "").lower():
            return False
        if role in ("obj", "iobj", "obl:a"):
            return True
        slots = [s for s in (case_by_position or {}).get(arg, "").split(SLOT_SEP) if s]
        return len(slots) > 1 and any(_case_supports_role(s, role) for s in slots)

    def _pronominal_verb_clitic(
        pos: tuple[int, int], arg: tuple[int, int], role: str
    ) -> bool:
        if dep_index_by_pos is None or role not in ("obj", "iobj", "obl", "obl:a"):
            return False
        row = dep_index_by_pos.get(arg)
        if row is None or row.deprel not in ("obj", "iobj", "obl"):
            return False
        if not _hosts_child(pos, row, dep_index_by_pos):
            return False
        if "pronoun" not in (morph_pos_by_position or {}).get(arg, "").lower():
            return False
        slots = [s for s in (case_by_position or {}).get(arg, "").split(SLOT_SEP) if s]
        return "reflexive" in slots

    def _secondary_predicate_over_argument(
        pos: tuple[int, int], arg: tuple[int, int], role: str,
        derived_args: set[tuple[int, int]],
    ) -> bool:
        if dep_index_by_pos is None:
            return False

        antecedent: tuple[int, int] | None = None
        prow = dep_index_by_pos.get(pos)
        if (prow is not None and prow.deprel in ("acl", "acl:relcl")
                and any((row_ := dep_index_by_pos.get(a)) is not None
                        and row_.deprel in _SUBJ_DEPRELS or row_.deprel == "obj"
                        and (row_.head_line, row_.head_token) == pos
                        and row_.word.lower().rstrip("'") in _RELATIVE_PRONOUNS
                        for a in derived_args)):
            antecedent = (prow.head_line, prow.head_token)

        def _hosted_by_derived_argument(r: DepRow) -> bool:
            host = (r.head_line, r.head_token)
            return (host in derived_args
                    or _coordination_head(host, dep_index_by_pos) in derived_args
                    or host == antecedent)

        row = dep_index_by_pos.get(arg)
        if row is None:
            return False
        if row.deprel in ("amod", "advmod"):
            if role != "xcomp":
                return False
            if "adjective" not in (morph_pos_by_position or {}).get(arg, "").lower():
                return False
            return _hosted_by_derived_argument(row)
        if role not in ("xcomp", "ccomp"):
            return False
        if row.deprel not in ("acl", "acl:relcl"):
            return False
        return _hosted_by_derived_argument(row)

    def _copular_hosts(pos: tuple[int, int]) -> set[tuple[int, int]]:
        if dep_index_by_pos is None:
            return set()
        dep_row = dep_index_by_pos.get(pos)
        if dep_row is None or dep_row.deprel not in ("attr", "xcomp"):
            return set()
        head = (dep_row.head_line, dep_row.head_token)
        return {head} if head in complement_hosts.get(pos, ()) else set()

    def _comparison_clause_hosts(pos: tuple[int, int]) -> set[tuple[int, int]]:
        if dep_index_by_pos is None or children_by_pos is None:
            return set()
        return {(c.line, c.token) for c in children_by_pos.get(pos, ())
                if c.deprel in CLAUSE_HEAD_DEPRELS
                and c.word.lower().rstrip("'") in ("come", "com")}

    def _auxiliary_hosts(pos: tuple[int, int]) -> set[tuple[int, int]]:
        if dep_index_by_pos is None:
            return set()
        return {(c.line, c.token) for c in children_by_pos.get(pos, ())
                if c.deprel in _AUX_DEPRELS} - {pos}

    def _named_by_its_auxiliary(pos: tuple[int, int]) -> bool:
        if dep_index_by_pos is None:
            return False
        return any(
            _aux_head(g, dep_index_by_pos) == pos
            for g in given_preds
            if (dep_index_by_pos.get(g) or DepRow(0, 0, "", "", 0, 0)).deprel in _AUX_DEPRELS
        )

    empty_derived = {
        (row.line, row.token)
        for rows in derived.values()
        for row in rows
        if row.token > 0 and not row.role
    }
    speech_act_nominal = set()
    if dep_index_by_pos is not None:
        derived_rows_by_pos: dict[tuple[int, int], list[SkelRow]] = {}
        for rows in derived.values():
            for row in rows:
                if row.token > 0:
                    derived_rows_by_pos.setdefault((row.line, row.token), []).append(row)
        for p, rows in derived_rows_by_pos.items():
            if len(rows) != 1 or rows[0].role != "subj":
                continue
            if (rows[0].arg_line, rows[0].arg_token) != (0, 0):
                continue
            row = dep_index_by_pos.get(p)
            if row is None or row.deprel != "parataxis":
                continue
            if not is_verb_pos((morph_pos_by_position or {}).get(p, "")):
                speech_act_nominal.add(p)
    for line, token in sorted(derived_preds - given_preds):
        if (line, token) in empty_derived and rule_active("CS"):
            continue
        if _named_by_its_auxiliary((line, token)) and rule_active("AV"):
            continue
        violations.append(Violation(line, "tag", f"missing_tuple: predicate {line}.{token} not proposed",
                                     predicate=(line, token)))

    def _copular_predication(pos: tuple[int, int]) -> bool:
        if pos in copula_hosts:
            return True
        return (dep_index_by_pos is not None
                and _aux_head(pos, dep_index_by_pos) in copula_hosts)

    def _verb_in_argument_slot(pos: tuple[int, int]) -> bool:
        if dep_index_by_pos is None or morph_pos_by_position is None:
            return False
        row = dep_index_by_pos.get(pos)
        if row is None or row.deprel not in _NOMINAL_SLOT_DEPRELS:
            return False
        return is_verb_pos(morph_pos_by_position.get(pos, ""))

    def _verb_in_adnominal_slot(pos: tuple[int, int]) -> bool:
        if dep_index_by_pos is None or morph_pos_by_position is None:
            return False
        row = dep_index_by_pos.get(pos)
        seen = {pos}
        while row is not None and row.deprel == "conj":
            head = (row.head_line, row.head_token)
            if head in seen:
                return False
            seen.add(head)
            row = dep_index_by_pos.get(head)
        if row is None or row.deprel not in ("amod", "acl", "acl:relcl"):
            return False
        return (is_verb_pos(morph_pos_by_position.get(pos, ""))
                and is_verb_pos(morph_pos_by_position.get((row.line, row.token), "")))

    for line, token in sorted(given_preds - derived_preds):
        pos = (line, token)
        if (pos in double_listed
                or (_elided_copula_nominal(pos) and rule_active("Y"))
                or (_aux_of_derived_predicate(pos) and rule_active("I"))
                or (_copular_predication(pos) and rule_active("Y"))
                or (_verb_in_argument_slot(pos) and rule_active("Z"))
                or (_complemented_adjective_phrase(pos) and rule_active("AY"))
                or (_verb_in_adnominal_slot(pos) and rule_active("CH"))):
            continue
        violations.append(Violation(line, "tag", f"extra_tuple: predicate {line}.{token} not derived",
                                     predicate=(line, token)))

    given_by_pred: dict[tuple[int, int], list[SkelRow]] = {}
    for rows in given.values():
        for row in rows:
            if row.token > 0:
                given_by_pred.setdefault((row.line, row.token), []).append(row)
    derived_by_pred: dict[tuple[int, int], list[SkelRow]] = {}
    for rows in derived.values():
        for row in rows:
            derived_by_pred.setdefault((row.line, row.token), []).append(row)

    for pos in sorted(given_preds & derived_preds):
        line, token = pos

        def by_arg(rows: list[SkelRow]) -> dict[tuple[int, int], str]:
            return {
                (r.arg_line, r.arg_token): _canonicalize_role(r.role)
                for r in rows
                if r.role and (r.arg_line, r.arg_token) != pos
            }

        g = by_arg(given_by_pred.get(pos, []))
        d = by_arg(derived_by_pred.get(pos, []))
        if dep_index_by_pos is not None:
            _apply_subj_authority(g, d, pos, derived_by_pred, dep_index_by_pos, given_by_pred,
                                  morph_rows, children_by_pos, np_rows)
            derived_args = set(d)
            if rule_active("AQ"):
                g = _merge_auxiliary_citations(g, pos, dep_index_by_pos)
            if rule_active("BV"):
                g = {
                    (_prep_stack_nominal(a, dep_index_by_pos) if a != (0, 0) else a): r
                    for a, r in g.items()
                }
            if rule_active("BJ"):
                g = _merge_adverb_cluster_citations(g, pos, dep_index_by_pos, children_by_pos,
                                                    morph_pos_by_position)
            if rule_active("C"):
                g = _collapse_coordination(g, pos, dep_index_by_pos, morph_pos_by_position)
                d = _collapse_coordination(d, pos, dep_index_by_pos, morph_pos_by_position)
            if np_rows is not None and rule_active("AI"):
                _merge_np_head_citations(g, d, np_rows)
            if rule_active("EI"):
                _merge_floating_quantifier_citations(g, d, dep_index_by_pos,
                                                     morph_lemma_by_position, morph_pos_by_position)
            if rule_active("D"):
                _drop_nmod_obliques(g, d, derived_args, dep_index_by_pos)
        for arg, drole in sorted(d.items()):
            grole = g.get(arg)
            if grole is None:
                if drole in ("ccomp", "xcomp") and (arg in given_preds
                                                    or _aux_named_predicate(arg)) and rule_active("CY"):
                    continue
                if arg in given_preds and _verb_in_argument_slot(arg) and rule_active("Z"):
                    continue
                if _complement_hosted_argument(pos, arg, drole, given_by_pred) and rule_active("X"):
                    continue
                if _comparative_come_adjunct(pos, arg, drole, dep_index_by_pos, children_by_pos,
                                             morph_pos_by_position, d) and rule_active("AR"):
                    continue
                if _conjunction_oblique(arg, drole, morph_pos_by_position) and rule_active("BM"):
                    continue
                if _pronominal_verb_clitic(pos, arg, drole) and rule_active("AW"):
                    continue
                if _nested_in_named_phrase(arg, g, d, np_rows) and rule_active("BR"):
                    continue
                if _depictive_bare_oblique_omitted(pos, arg, drole, dep_index_by_pos,
                                                   morph_pos_by_position, case_children) and rule_active("BX"):
                    continue
                if _depictive_attr_omitted(pos, arg, drole, dep_index_by_pos, d,
                                           morph_pos_by_position, case_children) and rule_active("DW"):
                    continue
                if _undecided_subject_slot(drole, arg, g, d) and rule_active("BA"):
                    continue
                if _gapped_second_term_argument(arg, d) and rule_active("CW"):
                    continue
                if _gapped_first_term_argument(arg, g, d) and rule_active("DH"):
                    continue
                if _gapped_clause_read_as_predicate(pos, arg, dep_index_by_pos, children_by_pos,
                                                    given_preds) and rule_active("DI"):
                    continue
                if _complement_hosted_argument(pos, arg, drole, given_by_pred,
                                               hosts=_control_partners(pos)) and rule_active("AX"):
                    continue
                if _complement_hosted_argument(pos, arg, drole, given_by_pred,
                                               hosts=_auxiliary_hosts(pos)) and rule_active("BY"):
                    continue
                if _clause_named_by_marker(pos, arg, drole, dep_index_by_pos, g) and rule_active("CK"):
                    continue
                if _raised_infinitive_subject(pos, drole, g) and rule_active("DN"):
                    continue
                if _impersonal_clausal_subject(pos, drole, d) and rule_active("DQ"):
                    continue
                violations.append(Violation(line, "tag", f"missing_arg: {line}.{token} {drole} {arg}",
                                             role=drole, arg=arg, predicate=pos))
            elif grole != drole:
                if ((_oblique_lemma_refinement(grole, drole, arg, case_children) and rule_active("L"))
                        or (_predicative_complement(grole, drole) and rule_active("M"))
                        or (_case_marked_object(grole, drole, arg, case_lemmas) and rule_active("N"))
                        or (_co_present_preposition(grole, drole, arg, case_lemmas) and rule_active("O"))
                        or (_clausal_complement_flavor(grole, drole) and rule_active("P"))
                        or (_clausal_object(grole, drole, arg, morph_pos_by_position) and rule_active("Q"))
                        or (_case_corroborated_role(grole, drole, arg, case_by_position,
                                                    morph_pos_by_position) and rule_active("U"))
                        or (_case_corroborated_swap(grole, drole, arg, g, d, case_by_position,
                                                    morph_pos_by_position) and rule_active("W"))
                        or (_comparative_come_complement(grole, drole, arg, dep_index_by_pos,
                                                         morph_pos_by_position) and rule_active("AK"))
                        or (_fused_clitic_dual_role(grole, drole, arg, morph_pos_by_position,
                                                    case_by_position, morph_lemma_by_position) and rule_active("AL"))
                        or (_depictive_bare_oblique(grole, drole, pos, arg, dep_index_by_pos,
                                                    morph_pos_by_position, case_children) and rule_active("AZ"))
                        or (_marked_complement_clause(pos, grole, drole, arg, dep_index_by_pos,
                                                      marker_lemmas) and rule_active("CQ"))
                        or ((_pronominal_verb_clitic(pos, arg, grole)
                             and _pronominal_verb_clitic(pos, arg, drole)) and rule_active("BD"))
                        or (_prepositional_copular_complement(pos, grole, drole, arg) and rule_active("DB"))):
                    continue
                violations.append(
                    Violation(line, "tag", f"role_mismatch: {line}.{token} arg {arg} {grole!r} vs {drole!r}",
                              role=drole, given_role=grole, arg=arg, predicate=pos)
                )
        for arg, grole in sorted(g.items()):
            if arg not in d:
                if dep_index_by_pos is not None and (
                    (_adverbial_oblique(pos, arg, grole, dep_index_by_pos, morph_pos_by_position) and rule_active("J"))
                    or (_predicative_advmod(pos, arg, grole, dep_index_by_pos,
                                           morph_pos_by_position) and rule_active("R"))
                    or (_nmod_complement_of_predicate(pos, arg, grole, dep_index_by_pos,
                                                     case_lemmas) and rule_active("S"))
                    or (_marked_adverbial_clause(pos, arg, grole, dep_index_by_pos,
                                                marker_lemmas) and rule_active("T"))
                    or (_secondary_predicate_over_argument(pos, arg, grole, derived_args) and rule_active("AA"))
                    or (_displaced_subject_pro_drop(grole, arg, g, d) and rule_active("BH"))
                    or (_accusative_and_infinitive(pos, arg, grole, dep_index_by_pos,
                                                  morph_tense_by_position) and rule_active("BI"))
                    or (_inverted_copula_complement(pos, arg, grole, dep_index_by_pos,
                                                   morph_pos_by_position) and rule_active("BF"))
                    or (_reflexive_clitic_argument(pos, arg, grole) and rule_active("AB"))
                    or (_copular_adverb_complement(pos, arg, grole) and rule_active("AD"))
                    or (_free_relative_head(pos, arg, grole, d) and rule_active("AE"))
                    or (_free_relative_matrix_head(pos, arg) and rule_active("BT"))
                    or (_copula_under_its_complement(pos, arg, grole) and rule_active("CT"))
                    or (_marker_slot_argument(pos, arg, grole, dep_index_by_pos,
                                             morph_pos_by_position) and rule_active("BW"))
                    or (_conj_shared_argument(pos, arg, grole, dep_index_by_pos,
                                             derived_by_pred, d) and rule_active("AJ"))
                    or (_complement_hosted_argument(pos, arg, grole, derived_by_pred,
                                                   hosts=_copular_hosts(pos)) and rule_active("X"))
                    or (_complement_hosted_argument(pos, arg, grole, derived_by_pred,
                                                   hosts=_comparison_clause_hosts(pos)) and rule_active("ED"))
                    or (_complement_hosted_argument(pos, arg, grole, derived_by_pred,
                                                   hosts=_control_partners(pos)) and rule_active("AX"))
                    or _gapped_coordinate_oblique(pos, arg, grole, dep_index_by_pos,
                                                  children_by_pos, d)
                    or _promoted_conjunct_argument(pos, arg, dep_index_by_pos, children_by_pos,
                                                   morph_pos_by_position)
                    or _stranded_on_underived_complement(pos, arg, grole, dep_index_by_pos,
                                                         derived_preds, case_lemmas)
                    or (_marker_of_derived_clause(pos, arg, grole, dep_index_by_pos, d) and rule_active("CK"))
                    or _wh_word_of_derived_clause(pos, arg, grole, dep_index_by_pos,
                                                  morph_pos_by_position, children_by_pos, d)
                    or ((grole != "subj" and pos in empty_derived) and rule_active("DA"))
                    or (_relative_adverb_oblique(pos, arg, grole) and rule_active("DD"))
                    or (_antecedent_for_relative_pronoun(pos, arg, grole) and rule_active("DK"))
                    or _conjunct_named_by_phrase_head(arg, grole, d, dep_index_by_pos,
                                                      morph_pos_by_position, np_rows)
                    or ((grole != "subj" and pos in speech_act_nominal) and rule_active("EA"))
                ):
                    continue
                violations.append(Violation(line, "tag", f"extra_arg: {line}.{token} {grole} {arg}",
                                             role=grole, arg=arg, predicate=pos))
    return violations
