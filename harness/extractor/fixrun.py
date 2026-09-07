"""Layer 5's binding of the apparatus's `--fix` machinery.

The machinery is `dante_corpus.harness.fixrun`, which decides a repair run
without knowing what a row means: it asks a `Criteria` which findings a level
names and a `Validator` what the gate says. Layer 5's answers to both are
`harness.extractor.fixlevel` — passed as the module object, since it already has
`Criteria`'s shape — and `layers.validate_rows`.

Binding them here rather than at each call site keeps every signature the
pipeline and the tests use exactly as it was: `plan_fix(layers, settled, level)`,
`fix_verdict(before, hard, soft, level, dep_rows)`, `fix_diagnosis(...)`.
"""

from __future__ import annotations

from typing import Any

from dante_corpus.harness import fixrun as _fixrun
from dante_corpus.harness.fixrun import (
    FixPlan,
    Span,
    fix_summary_line,
    refusal_note,
    revert_outcome,
    row_delta,
    salvage_by_row,
    salvage_outcome,
    salvage_rows,
)
from dante_corpus.harness.rows import Row, Violation

from harness.extractor import fixlevel
from harness.extractor.layers import validate_rows

__all__ = [
    "FixPlan",
    "Span",
    "fix_diagnosis",
    "fix_summary_line",
    "fix_verdict",
    "plan_fix",
    "refusal_note",
    "revert_outcome",
    "row_delta",
    "salvage_by_row",
    "salvage_outcome",
    "salvage_rows",
]


def plan_fix(
    layers: Any,
    settled_units: dict[Span, dict[int, list[Row]]],
    level: int,
) -> FixPlan:
    """`fixrun.plan_fix` over Layer 5's levels and gate 2."""
    return _fixrun.plan_fix(
        layers, settled_units, level, criteria=fixlevel, validate=validate_rows
    )


def fix_verdict(
    before: list[Violation],
    hard_after: list[Violation],
    soft_after: list[Violation],
    level: int,
    dep_rows: dict | None = None,
) -> tuple[bool, str]:
    """`fixrun.fix_verdict` over Layer 5's levels."""
    return _fixrun.fix_verdict(
        before, hard_after, soft_after, level, dep_rows, criteria=fixlevel
    )


def fix_diagnosis(
    prior: dict[int, list[Row]],
    submitted: dict[int, list[Row]],
    before: list[Violation],
    hard_after: list[Violation],
    soft_after: list[Violation],
    level: int,
    dep_rows: dict | None = None,
) -> dict:
    """`fixrun.fix_diagnosis` over Layer 5's levels."""
    return _fixrun.fix_diagnosis(
        prior,
        submitted,
        before,
        hard_after,
        soft_after,
        level,
        dep_rows,
        criteria=fixlevel,
    )
