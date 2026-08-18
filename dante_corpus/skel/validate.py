"""Validation engine for Layer 5 (hard and soft checks, divergence classification)."""

from __future__ import annotations

from ..case import CaseRow
from ..dep import DepRow, index as dep_index
from ..morph import MorphRow, Violation, strip_word_punct
from ..np import NPSpan
from .derive import ARG_DEPRELS, _aux_head, _coordination_head, derive_unit
from .io import _alpha_tokens
from .models import _REL_PRONOUN_WORDS, SkelRow, _role_valid
from .registry import rule_active
from .rules import (
    _classify_divergence,
    _fused_clitic_dual_role,
    _marker_slot_argument,
    _predicate_positions_in,
)


def _dual_role_violations(
    all_rows: list[SkelRow],
    morph_rows: dict[int, list[MorphRow]],
    case_rows: dict[int, list[CaseRow]] | None,
) -> list[Violation]:
    """**Rule EG**: one token filling two roles of one predicate — the first check in this layer
    that reads the artifact *against itself*.
    """
    morph_pos_by_position = {
        (no, i + 1): row.pos for no, rows in morph_rows.items() for i, row in enumerate(rows)
    }
    case_by_position = (
        {(row.line, row.token): row.case for rows in case_rows.values() for row in rows}
        if case_rows is not None else None
    )
    morph_lemma_by_position = {
        (no, i + 1): row.lemma for no, rows in morph_rows.items() for i, row in enumerate(rows)
    }
    roles_by_pair: dict[tuple[tuple[int, int], tuple[int, int]], list[str]] = {}
    for row in all_rows:
        if row.token == 0 or not row.role:
            continue
        pos, arg = (row.line, row.token), (row.arg_line, row.arg_token)
        if arg == (0, 0) or arg == pos:
            continue
        roles = roles_by_pair.setdefault((pos, arg), [])
        if row.role not in roles:
            roles.append(row.role)

    violations: list[Violation] = []
    for (pos, arg), roles in sorted(roles_by_pair.items()):
        if len(roles) < 2:
            continue
        if any(_fused_clitic_dual_role(a, b, arg, morph_pos_by_position, case_by_position,
                                       morph_lemma_by_position)
               for i, a in enumerate(roles) for b in roles[i + 1:]):
            continue
        listed = " and ".join(repr(r) for r in roles)
        violations.append(Violation(
            pos[0], "tag", f"dual_role: {pos[0]}.{pos[1]} arg {arg} listed as {listed}",
            role=roles[0], given_role=roles[1], arg=arg, predicate=pos,
        ))
    return violations


def validate_unit(
    nos: list[int],
    texts: list[str],
    rows_by_line: dict[int, list[SkelRow]],
    morph_rows: dict[int, list[MorphRow]] | None = None,
    np_rows: dict[int, list[NPSpan]] | None = None,
    dep_rows: dict[int, list[DepRow]] | None = None,
    case_rows: dict[int, list[CaseRow]] | None = None,
) -> list[Violation]:
    """Check `rows_by_line` for one parse unit."""
    violations: list[Violation] = []
    token_lists = {no: _alpha_tokens(t) for no, t in zip(nos, texts)}
    valid_positions = {(no, i + 1) for no in nos for i in range(len(token_lists[no]))}

    all_rows = [row for no in nos for row in rows_by_line.get(no, [])]

    for no in nos:
        line_tokens = token_lists[no]
        rows = rows_by_line.get(no, [])
        for row in rows:
            if row.token == 0:
                if any(r.token > 0 for r in rows):
                    violations.append(Violation(no, "sentinel", "sentinel row coexists with predicate rows"))
                continue
            if 1 <= row.token <= len(line_tokens):
                token = line_tokens[row.token - 1]
                if row.word != token and strip_word_punct(row.word, token) is None:
                    violations.append(Violation(no, "word", f"{row.word!r} != token {token!r}"))
            else:
                violations.append(Violation(no, "position", f"predicate token {row.token} out of range"))

    seen_rows: set[tuple[int, int, str, int, int]] = set()
    for row in all_rows:
        if row.token == 0:
            continue
        pos = (row.line, row.token)
        arg = (row.arg_line, row.arg_token)
        key = (row.line, row.token, row.role, row.arg_line, row.arg_token)
        if key in seen_rows:
            violations.append(Violation(row.line, "dup", f"duplicate row {key}"))
        seen_rows.add(key)
        if arg == pos:
            violations.append(Violation(row.line, "dup", f"argument cites its own predicate {pos}"))
        if arg == (0, 0):
            if row.role not in ("subj", ""):
                violations.append(Violation(row.line, "position", f"role {row.role!r} may not use (0,0)"))
        elif arg not in valid_positions:
            violations.append(Violation(row.line, "position", f"argument {arg} not in unit"))

    predicate_positions = _predicate_positions_in(rows_by_line)
    for row in all_rows:
        if row.token > 0 and row.role in ("ccomp", "xcomp"):
            arg = (row.arg_line, row.arg_token)
            if arg not in predicate_positions:
                violations.append(
                    Violation(row.line, "clausal", f"{row.role} argument {arg} is not a predicate in this unit")
                )

    for row in all_rows:
        if row.token > 0 and not _role_valid(row.role):
            violations.append(Violation(row.line, "tag", f"role {row.role!r} not in frozen vocabulary"))

    if morph_rows is not None and np_rows is not None:
        pronoun_positions = {
            (no, i + 1)
            for no, rows in morph_rows.items()
            for i, r in enumerate(rows)
            if "pronoun" in r.pos.lower() or r.word.lower() in _REL_PRONOUN_WORDS
        }
        adverb_obl_positions = {
            (no, i + 1)
            for no, rows in morph_rows.items()
            for i, r in enumerate(rows)
            if "adverb" in r.pos.lower()
        }
        np_head_positions = {(no, s.head) for no, spans in np_rows.items() for s in spans}
        membership_morph_pos = {
            (no, i + 1): r.pos for no, rows in morph_rows.items() for i, r in enumerate(rows)
        }
        dep_argument_positions = {
            (r.line, r.token)
            for rows in (dep_rows or {}).values() for r in rows
            if r.deprel in ARG_DEPRELS
        }
        for row in all_rows:
            if row.token == 0 or row.role in ("", "attr", "xcomp", "ccomp"):
                continue
            arg = (row.arg_line, row.arg_token)
            if arg == (0, 0) or arg == (row.line, row.token):
                continue
            if arg in np_head_positions or arg in pronoun_positions or arg in predicate_positions:
                continue
            if (row.role == "obl" or row.role.startswith("obl:")) and arg in adverb_obl_positions:
                continue
            if arg in dep_argument_positions and rule_active("AF"):
                continue
            index = dep_index(dep_rows) if dep_rows else {}
            aux_head = _aux_head(arg, index)
            if aux_head != arg and (aux_head in np_head_positions or aux_head in pronoun_positions
                                    or aux_head in predicate_positions
                                    or aux_head in dep_argument_positions) and rule_active("AQ"):
                continue
            coord_head = _coordination_head(arg, index) if index else arg
            if coord_head != arg and (coord_head in np_head_positions
                                      or coord_head in pronoun_positions
                                      or coord_head in predicate_positions
                                      or coord_head in dep_argument_positions) and rule_active("DG"):
                continue
            if _marker_slot_argument((row.line, row.token), arg, row.role, index,
                                     membership_morph_pos) and rule_active("DS"):
                continue
            violations.append(
                Violation(row.line, "tag", f"argument {arg} for role {row.role} heads no NP/pronoun/predicate")
            )

    if morph_rows is not None and rule_active("EG"):
        violations.extend(_dual_role_violations(all_rows, morph_rows, case_rows))

    if dep_rows is not None and morph_rows is not None:
        derived = derive_unit(nos, dep_rows, morph_rows, case_rows)
        morph_pos_by_position = {
            (no, i + 1): row.pos for no, rows in morph_rows.items() for i, row in enumerate(rows)
        }
        case_by_position = (
            {(row.line, row.token): row.case for rows in case_rows.values() for row in rows}
            if case_rows is not None else None
        )
        morph_lemma_by_position = {
            (no, i + 1): row.lemma for no, rows in morph_rows.items() for i, row in enumerate(rows)
        }
        violations.extend(_classify_divergence(
            rows_by_line, derived, dep_index(dep_rows), morph_pos_by_position, case_by_position,
            morph_lemma_by_position, morph_rows, np_rows,
        ))

    return violations
