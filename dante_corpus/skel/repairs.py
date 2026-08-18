"""Deterministic repair discovery and application."""

from __future__ import annotations

import dataclasses

from ..dep import DepRow, index as dep_index, subject_agreement
from ..morph import MorphRow, Violation
from .models import OBL_RE, Repair, SkelRow, _canonicalize_role, _normalize_prep_lemma


def _safe_role_repair(given_role: str, derived_role: str) -> bool:
    """Only a bare `obl` -> `obl:<lemma>` refinement is dep-tree-explicit (derive_unit only
    emits the lemma-qualified form when a `case` child makes the preposition explicit); every
    other role_mismatch pair surviving Phase 1/2 normalization (subj/obj, iobj/obj, cross-lemma
    obl pairs) is a genuine disagreement, left for Phase 4."""
    return given_role == "obl" and bool(OBL_RE.fullmatch(derived_role))


def _case_child_lemmas(
    dep_index_by_pos: dict[tuple[int, int], DepRow] | None,
) -> dict[tuple[int, int], set[tuple[tuple[int, int], str]]]:
    """`case` children per head, as (position, normalized lemma) — the input both preposition
    rules read."""
    out: dict[tuple[int, int], set[tuple[tuple[int, int], str]]] = {}
    for row in (dep_index_by_pos or {}).values():
        if row.deprel == "case":
            out.setdefault((row.head_line, row.head_token), set()).add(
                ((row.line, row.token), _normalize_prep_lemma(row.word.lower())))
        elif row.deprel == "fixed":
            head = dep_index_by_pos.get((row.head_line, row.head_token))
            if head is not None and head.deprel == "case":
                out.setdefault((head.line, head.token), set()).add(
                    ((row.line, row.token), _normalize_prep_lemma(row.word.lower())))
    return out


def _stacked_prep_lemmas(
    arg: tuple[int, int],
    case_kids: dict[tuple[int, int], set[tuple[tuple[int, int], str]]],
) -> set[str]:
    """Every preposition lemma reachable from `arg` by walking `case` children transitively."""
    out: set[str] = set()
    seen: set[tuple[int, int]] = set()
    frontier = list(case_kids.get(arg, ()))
    while frontier:
        token, lemma = frontier.pop()
        if token in seen:
            continue
        seen.add(token)
        out.add(lemma)
        frontier.extend(case_kids.get(token, ()))
    return out


def _prep_stack_label(
    given_role: str, derived_role: str, arg: tuple[int, int],
    case_kids: dict[tuple[int, int], set[tuple[tuple[int, int], str]]],
) -> bool:
    """Whether an `obl:X` vs `obl:Y` mismatch is the two readings naming *different prepositions
    of one stack* rather than disagreeing about the relation."""
    if not (given_role.startswith("obl:") and derived_role.startswith("obl:")):
        return False
    stack = _stacked_prep_lemmas(arg, case_kids)
    return (given_role.split(":", 1)[1] in stack
            and derived_role.split(":", 1)[1] in stack)


def _find_repairs(
    given: dict[int, list[SkelRow]], derived: dict[int, list[SkelRow]],
    violations: list[Violation],
    morph_rows: dict[int, list[MorphRow]] | None = None,
    dep_rows: dict[int, "list[DepRow] | tuple[DepRow, ...]"] | None = None,
) -> list[Repair]:
    """Mechanical rewrite candidates, sourced purely from `_classify_divergence`'s own violation
    list (already passed through Phase 2's `_apply_subj_authority` when `dep_index_by_pos` was
    given) — does not recompute the given/derived diff independently."""
    by_pred: dict[tuple[int, int], list[Violation]] = {}
    for v in violations:
        if v.predicate is not None:
            by_pred.setdefault(v.predicate, []).append(v)

    dep_index_by_pos = dep_index(dep_rows) if dep_rows is not None else None
    case_kids = _case_child_lemmas(dep_index_by_pos)
    dep_children: dict[tuple[int, int], list[DepRow]] = {}
    for row in (dep_index_by_pos or {}).values():
        dep_children.setdefault((row.head_line, row.head_token), []).append(row)

    def find_row(pos: tuple[int, int], role: str, arg: tuple[int, int]) -> SkelRow | None:
        for row in given.get(pos[0], ()):
            if ((row.line, row.token) == pos and _canonicalize_role(row.role) == role
                    and (row.arg_line, row.arg_token) == arg):
                return row
        return None

    repairs: list[Repair] = []
    for pos, vs in by_pred.items():
        missing_subj = [v for v in vs if v.detail.startswith("missing_arg") and v.role == "subj"]
        extra_null_subj = [
            v for v in vs
            if v.detail.startswith("extra_arg") and v.role == "subj" and v.arg == (0, 0)
        ]
        if len(missing_subj) == 1 and len(extra_null_subj) == 1:
            subj = missing_subj[0].arg
            verdict, _ = subject_agreement(subj, pos, morph_rows, dep_children)
            if verdict == "agree":
                before = find_row(pos, "subj", (0, 0))
                if before is not None:
                    after = dataclasses.replace(before, arg_line=subj[0], arg_token=subj[1])
                    repairs.append(Repair("null_subject", pos, before, after))

        for v in vs:
            if not (v.detail.startswith("role_mismatch") and v.given_role is not None
                    and v.role is not None and v.arg is not None):
                continue
            if _safe_role_repair(v.given_role, v.role):
                kind = "role_label"
            elif _prep_stack_label(v.given_role, v.role, v.arg, case_kids):
                kind = "prep_stack"
            else:
                continue
            before = find_row(pos, v.given_role, v.arg)
            if before is not None:
                repairs.append(Repair(kind, pos, before, dataclasses.replace(before, role=v.role)))
    return repairs
