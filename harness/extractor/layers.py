"""Frozen-layer bundle and the two intrinsic gates that read it (execution face).

Split out of `reconstruct.py` (S7.2). This is the bottom of the reconstruction
stack: everything here reads Layer 1-4 plus the case annex and nothing else —
no gold artifact is opened anywhere in this module, which is what makes it safe
for the execution face to depend on (`../PLAN.md` §4 item 1).

Two of the three §4.1 gates live here because both are functions of the frozen
layers alone: `build_rows` (gate 1, the Layer-1 token-stream assertion) and
`validate_rows` (gate 2, `validate_unit` over one unit's assembled rows, split
hard/soft the way the Phase 5-8 drivers do). Gate 3 is a disk operation and
stays with `commit` in `reconstruct.py`.
"""

from __future__ import annotations

from dataclasses import dataclass

from dante_corpus import api, case as case_layer, dep as dep_layer, morph as morph_layer, np as np_layer
from dante_corpus.morph import Violation
from dante_corpus.skel.models import SkelRow, _row_sort_key
from dante_corpus.skel.validate import validate_unit

__all__ = [
    "SAMPLE_VIOLATIONS",
    "CantoLayers",
    "RowKey",
    "build_rows",
    "split_violations",
    "validate_rows",
    "violation_record",
]

# Per-unit violation details kept in log records; the summary carries the full
# kind histogram, so samples only need to seed triage.
SAMPLE_VIOLATIONS = 10

RowKey = tuple[int, int, str, int, int]


# --- frozen-layer bundle (execution face: no gold anywhere) ------------------------------


@dataclass
class CantoLayers:
    """Everything the execution face may read for one canto: L1-L4 + case annex."""

    canticle: str
    canto: int
    nos: list[int]
    texts: list[str]
    tokens: dict[int, list[str]]
    morph_rows: dict[int, tuple]
    np_rows: dict[int, tuple]
    dep_rows: dict[int, tuple]
    case_rows: dict[int, tuple]

    @property
    def text_by_no(self) -> dict[int, str]:
        return dict(zip(self.nos, self.texts))

    @classmethod
    def load(cls, canticle: str, canto: int) -> "CantoLayers":
        data = api.canto(canticle, canto)
        lines = data.lines()
        return cls(
            canticle=canticle,
            canto=canto,
            nos=[line.no for line in lines],
            texts=[line.text for line in lines],
            tokens={line.no: list(line.tokens) for line in lines},
            morph_rows=morph_layer.load_morph(canticle, canto),
            np_rows=np_layer.load_np(canticle, canto),
            dep_rows=dep_layer.load_dep(canticle, canto),
            case_rows=case_layer.load_case(canticle, canto),
        )

    def units(self) -> list[list[int]]:
        """Parse-unit line groups (`dep.sentence_groups`) covering every line once."""
        return [
            list(group)
            for group in dep_layer.sentence_groups(self.nos, self.texts)
        ]


def split_violations(
    violations: list[Violation],
) -> tuple[list[Violation], list[Violation]]:
    """`(hard, soft)` — the drivers' split (`driver_ui._classify_violations`)."""
    hard: list[Violation] = []
    soft: list[Violation] = []
    for v in violations:
        (soft if v.kind == "tag" else hard).append(v)
    return hard, soft


def build_rows(
    keys: set[RowKey],
    layers: CantoLayers,
    line_start: int,
    line_end: int,
) -> tuple[dict[int, list[SkelRow]], list[str]]:
    """§4.1 gate 1 — normalize accepted row keys onto the Layer-1 token stream.

    Every predicate/argument position must index the canto's alpha-token
    stream inside the unit's bounds; each row's word anchor is taken verbatim
    from that stream, so token-for-token alignment holds by construction and
    is asserted after construction. Bad positions are reported (and dropped),
    never raised.
    """
    errors: list[str] = []
    by_line: dict[int, list[SkelRow]] = {}
    for key in sorted(keys):
        pline, ptok, role, aline, atok = key
        if not line_start <= pline <= line_end:
            errors.append(f"predicate {pline}.{ptok} outside unit bounds")
            continue
        ptoks = layers.tokens.get(pline, [])
        if not 1 <= ptok <= len(ptoks):
            errors.append(
                f"predicate {pline}.{ptok} outside the Layer-1 token stream"
            )
            continue
        if (aline, atok) != (0, 0):
            if not line_start <= aline <= line_end:
                errors.append(f"argument {aline}.{atok} outside unit bounds")
                continue
            atoks = layers.tokens.get(aline, [])
            if not 1 <= atok <= len(atoks):
                errors.append(
                    f"argument {aline}.{atok} outside the Layer-1 token stream"
                )
                continue
        word = ptoks[ptok - 1]
        by_line.setdefault(pline, []).append(
            SkelRow(line=pline, token=ptok, word=word, role=role,
                    arg_line=aline, arg_token=atok)
        )
    for rows in by_line.values():
        rows.sort(key=_row_sort_key)
    return by_line, errors


def violation_record(v: Violation) -> dict:
    return {"line": v.line, "kind": v.kind, "detail": v.detail}


def validate_rows(
    layers: CantoLayers, group: list[int], unit_rows: dict[int, list[SkelRow]]
) -> tuple[list[Violation], list[Violation]]:
    """§4.1 gate 2 over one unit's assembled rows -> `(hard, soft)`."""
    text_by_no = layers.text_by_no
    violations = validate_unit(
        group,
        [text_by_no[no] for no in group],
        unit_rows,
        morph_rows=layers.morph_rows,
        np_rows=layers.np_rows,
        dep_rows=layers.dep_rows,
        case_rows=layers.case_rows,
    )
    return split_violations(violations)
