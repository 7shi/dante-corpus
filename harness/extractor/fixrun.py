"""The Stage-6 `--fix` machinery: what a repair run reopens, and what it keeps.

Split out of `reconstruct.py` (S7.2). Everything a `--fix <level>` run decides
lives here, in the order the run uses it: `plan_fix` selects the settled units
carrying a finding of the level, `fix_verdict` decides whether the session's
answer may replace the recorded rows, `salvage_outcome` re-measures the answer
at position scope when the whole unit is refused, `salvage_by_row` re-measures it
one finding's row at a time when that is refused too, and `revert_outcome` puts
the record back verbatim when none of them passes. `fix_diagnosis` and `row_delta` report
the mechanism (`../PLAN.md` discipline 6) after the verdict is already decided.

The two disciplines this module exists to hold: selection never decides
(discipline 1 — the counter picks the work, the session answers it), and a fix
run can never leave the artifact worse than it found it, because every path out
of a refusal ends on rows that were already on disk.
"""

from __future__ import annotations

import dataclasses
from collections import Counter
from dataclasses import dataclass, field

from dante_corpus.morph import Violation
from dante_corpus.skel.models import SkelRow

from harness.extractor import fixlevel
from harness.extractor.layers import (
    SAMPLE_VIOLATIONS,
    CantoLayers,
    validate_rows,
    violation_record,
)
from harness.extractor.outcome import UnitOutcome

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

Span = tuple[int, int]


@dataclass
class FixPlan:
    """Which settled units a `--fix <level>` run reopens, and what it shows them.

    Selection only — the counter selects the work and never decides it
    (`../PLAN.md` discipline 1). Each selected span keeps its rows on record so
    the acceptance test in `settle()` can put them back unchanged when the
    session's answer is not an improvement: a fix run must never leave the
    artifact worse than it found it.

    The canto's layers and each span's line group are kept too, so a refused
    answer can be re-measured at position scope (`salvage_outcome`) without the
    caller having to carry the layers into its settle callback.
    """

    level: int
    prior: dict[Span, dict[int, list[SkelRow]]] = field(default_factory=dict)
    revisions: dict[Span, str] = field(default_factory=dict)
    before: dict[Span, list[Violation]] = field(default_factory=dict)
    before_hard: dict[Span, list[Violation]] = field(default_factory=dict)
    groups: dict[Span, list[int]] = field(default_factory=dict)
    layers: CantoLayers | None = None

    def __bool__(self) -> bool:
        return bool(self.prior)

    @property
    def dep_rows(self) -> dict:
        """The canto's Layer-4 rows, for the classes whose definition reads them."""
        return self.layers.dep_rows if self.layers is not None else {}

    @property
    def findings(self) -> int:
        return sum(
            len(fixlevel.select(vs, self.level, dep_rows=self.dep_rows))
            for vs in self.before.values()
        )


def plan_fix(
    layers: CantoLayers,
    settled_units: dict[Span, dict[int, list[SkelRow]]],
    level: int,
) -> FixPlan:
    """Find the settled units carrying a level-`level` finding, gold-closed."""
    plan = FixPlan(level=level, layers=layers)
    groups = {(g[0], g[-1]): g for g in layers.units()}
    for span, rows in settled_units.items():
        group = groups.get(span)
        if group is None:
            continue
        hard, soft = validate_rows(layers, group, rows)
        findings = fixlevel.select(soft, level, rows, layers.dep_rows)
        if not findings:
            continue
        plan.prior[span] = {no: list(rows.get(no, [])) for no in group}
        plan.groups[span] = list(group)
        plan.before[span] = list(soft)
        plan.before_hard[span] = list(hard)
        plan.revisions[span] = fixlevel.revision_block(
            plan.prior[span], findings, layers.dep_rows, level
        )
    return plan


def fix_verdict(
    before: list[Violation],
    hard_after: list[Violation],
    soft_after: list[Violation],
    level: int,
    dep_rows: dict | None = None,
) -> tuple[bool, str]:
    """Accept the re-solved unit, or say why the prior rows stand.

    Three refusals, in the order they are checked: the submission is not
    hard-clean; the level's own findings did not fall; or a violation class the
    unit did not carry before is now present. The last is the acceptance gate
    SOFT.md §6's dry run used — a repair may not trade its class for another.

    `dep_rows` carries the canto's Layer 4 for the classes defined by the tree
    (level 2). It is the class definition, not the `holds` precondition — the two
    counts are taken over different sets of rows and must share one definition —
    so it is passed to both sides here and the rows are passed to neither.
    """
    if hard_after:
        return False, "hard"
    if len(fixlevel.select(soft_after, level, dep_rows=dep_rows)) >= len(
        fixlevel.select(before, level, dep_rows=dep_rows)
    ):
        return False, "no_improvement"
    seen = {fixlevel.violation_class(v) for v in before}
    new = {fixlevel.violation_class(v) for v in soft_after} - seen
    if new:
        return False, f"new_class:{','.join(sorted(new))}"
    return True, "accepted"


def revert_outcome(
    outcome: UnitOutcome, plan: FixPlan, span: Span
) -> UnitOutcome:
    """Restore the unit's recorded rows on a refused fix, verdicts included.

    The rows go back byte-for-byte, and so do the gate results they were
    measured with — a reverted unit must be reported as what is on disk, not as
    the submission that was thrown away. Only the session telemetry (route,
    timings, `final_submission_valid`) is left as this run produced it.
    """
    rows = {no: list(r) for no, r in plan.prior[span].items()}
    keys = frozenset(
        (r.line, r.token, r.role, r.arg_line, r.arg_token)
        for rs in rows.values()
        for r in rs
    )
    return dataclasses.replace(
        outcome,
        rows=rows,
        row_keys=keys,
        hard=list(plan.before_hard[span]),
        soft=list(plan.before[span]),
        token_assertions=[],
    )


def salvage_rows(
    prior: dict[int, list[SkelRow]],
    submitted: dict[int, list[SkelRow]],
    keys: frozenset[fixlevel.RowKey],
) -> dict[int, list[SkelRow]]:
    """Position-scoped replacement: the answer stands at `keys`, the record elsewhere.

    A level names a *row* while a session answers a whole *unit*, so the two
    replacements a fix run can make are not the same size. `settle()` tries the
    whole unit first — that is the answer the model actually stands behind, and
    where it survives the acceptance test it is taken entire. This is what to do
    when it does not: keep the recorded rows, and take from the answer only the
    rows the findings themselves name. Rows outside `keys` are neither added nor
    removed, so a repair cannot import a class the unit never carried, and the
    result is still measured by `fix_verdict` rather than assumed.
    """
    out = {
        no: [r for r in rows if _key_of(r) not in keys]
        for no, rows in prior.items()
    }
    for no, rows in submitted.items():
        if no not in out:
            continue  # not a line of this unit; the artifact holds none of it
        out[no].extend(r for r in rows if _key_of(r) in keys)
    return out


def _key_of(row: SkelRow) -> fixlevel.RowKey:
    return (row.line, row.token, row.arg_line, row.arg_token)


def salvage_outcome(
    outcome: UnitOutcome, plan: FixPlan, span: Span
) -> UnitOutcome | None:
    """Re-measure the unit with the answer taken only at its findings' rows.

    `None` when the salvage cannot be measured honestly: the plan carries no
    layers to validate against, the level names no row for this unit, or the
    submission's own token assertions failed — its words disagree with Layer 1,
    so none of its rows may be spliced into the record.
    """
    if plan.layers is None or outcome.token_assertions:
        return None
    keys = fixlevel.governed_keys(
        fixlevel.select(
            plan.before[span], plan.level, plan.prior[span], plan.dep_rows
        ),
        plan.level,
        plan.dep_rows,
    )
    if not keys:
        return None
    rows = salvage_rows(plan.prior[span], outcome.rows, keys)
    hard, soft = validate_rows(plan.layers, plan.groups[span], rows)
    return dataclasses.replace(
        outcome,
        rows=rows,
        row_keys=frozenset(
            (r.line, r.token, r.role, r.arg_line, r.arg_token)
            for rs in rows.values()
            for r in rs
        ),
        hard=hard,
        soft=soft,
        token_assertions=[],
    )


def salvage_by_row(
    outcome: UnitOutcome, plan: FixPlan, span: Span
) -> tuple[UnitOutcome | None, int, int]:
    """The third scope: take the answer one *finding's* row at a time.

    Why there is a scope below `salvage_outcome`'s. That one splices every row the
    level named in this unit and measures the result as one, so a single row the
    model labelled wrongly refuses the whole splice along with its correct
    siblings. S8.2's residue is where that cost showed: at `purgatorio 10`
    (13-21) the answer carried four named rows, three of them agreeing with the
    derivation exactly, and all four were dropped because the fourth read
    `xcomp` where the derivation reads `obl:per`. The unit was re-answered four
    times over the run's relaunches and refused identically each time, so the
    rows were not going to arrive by re-asking.

    Each finding's rows are therefore spliced and measured on their own, in a
    deterministic order, against the state accumulated so far: a step is kept
    only when it stays hard-clean, introduces no class the unit did not carry,
    and strictly lowers the level's own finding count. Every kept step is an
    improvement that was measured, so the standing guarantee is unchanged — the
    artifact cannot end worse than it started, and the whole result is still put
    to `fix_verdict` by the caller rather than assumed.

    Returns `(outcome | None, taken, offered)`: `None` when nothing finer than
    the unit-scope splice is available (no layers, failed token assertions, fewer
    than two findings carrying rows) or when no single row survived on its own.
    """
    if plan.layers is None or outcome.token_assertions:
        return None, 0, 0
    findings = fixlevel.select(
        plan.before[span], plan.level, plan.prior[span], plan.dep_rows
    )
    offers = []
    for v in findings:
        keys = fixlevel.governed_keys([v], plan.level, plan.dep_rows)
        if keys:
            offers.append((sorted(keys), keys))
    if len(offers) < 2:
        # One finding's rows *are* the unit-scope splice; re-measuring them
        # under another name would only repeat that verdict.
        return None, 0, 0
    offers.sort(key=lambda offer: offer[0])

    seen = {fixlevel.violation_class(v) for v in plan.before[span]}
    rows = {no: list(rs) for no, rs in plan.prior[span].items()}
    hard, soft = list(plan.before_hard[span]), list(plan.before[span])
    taken = 0
    for _, keys in offers:
        trial = salvage_rows(rows, outcome.rows, keys)
        trial_hard, trial_soft = validate_rows(
            plan.layers, plan.groups[span], trial
        )
        if trial_hard:
            continue
        if {fixlevel.violation_class(v) for v in trial_soft} - seen:
            continue
        if len(fixlevel.select(trial_soft, plan.level, dep_rows=plan.dep_rows)) \
                >= len(fixlevel.select(soft, plan.level, dep_rows=plan.dep_rows)):
            continue
        rows, hard, soft = trial, trial_hard, trial_soft
        taken += 1
    if not taken:
        return None, 0, len(offers)
    return dataclasses.replace(
        outcome,
        rows=rows,
        row_keys=frozenset(
            (r.line, r.token, r.role, r.arg_line, r.arg_token)
            for rs in rows.values()
            for r in rs
        ),
        hard=hard,
        soft=soft,
        token_assertions=[],
    ), taken, len(offers)


def refusal_note(diagnosis: dict | None) -> str:
    """One clause naming what the refused answer did, for a watched run.

    The log carries the whole diagnosis; this is the part a human reading the
    stream needs to see the pattern forming — how far the answer reached, and
    whether what it introduced sat on a row the level named or beside it.
    """
    if diagnosis is None:
        return ""
    introduced = diagnosis["introduced_total"]
    governed = sum(1 for v in diagnosis["introduced"] if v["governed"])
    note = (
        f" [answer: ~{diagnosis['rows_relabelled']} "
        f"+{diagnosis['rows_added']} -{diagnosis['rows_removed']}"
    )
    if introduced:
        note += f"; {introduced} introduced, {governed} on named rows"
    return note + "]"


def fix_summary_line(level: int, stats: Counter[str]) -> str:
    """One line naming the mechanism of a fix run (`../PLAN.md` discipline 6)."""
    return (
        f"[fix] level {level}: {stats['units']} unit(s) reopened, "
        f"{stats['verdict:accepted']} accepted / "
        f"{stats['verdict:salvaged']} salvaged / "
        f"{stats['units'] - stats['verdict:accepted'] - stats['verdict:salvaged']}"
        f" reverted; "
        f"level findings {stats['findings_before']} -> {stats['findings_after']}, "
        f"soft {stats['soft_before']} -> {stats['soft_after']}; rows "
        f"{stats['rows_relabelled']} relabelled, {stats['rows_added']} added, "
        f"{stats['rows_removed']} removed"
    )


def row_delta(
    before: dict[int, list[SkelRow]], after: dict[int, list[SkelRow]]
) -> dict[str, int]:
    """Row-level mechanism of one accepted fix (`../PLAN.md` discipline 6).

    A delta on the violation count says nothing about how it was reached, so
    every accepted unit reports what actually happened to its rows: how many were
    added, removed, and relabelled in place (same predicate and argument, new
    role).
    """
    def keyed(rows: dict[int, list[SkelRow]]) -> dict[tuple, str]:
        return {
            (r.line, r.token, r.arg_line, r.arg_token): r.role
            for rows_ in rows.values()
            for r in rows_
        }

    b, a = keyed(before), keyed(after)
    return {
        "rows_before": len(b),
        "rows_after": len(a),
        "rows_added": len(a.keys() - b.keys()),
        "rows_removed": len(b.keys() - a.keys()),
        "rows_relabelled": sum(
            1 for key in b.keys() & a.keys() if b[key] != a[key]
        ),
    }


def _violation_position(v: Violation) -> fixlevel.RowKey | None:
    """The artifact row a divergence finding names, in `governed_keys` shape."""
    if v.predicate is None or v.arg is None:
        return None
    return (v.predicate[0], v.predicate[1], v.arg[0], v.arg[1])


def fix_diagnosis(
    prior: dict[int, list[SkelRow]],
    submitted: dict[int, list[SkelRow]],
    before: list[Violation],
    hard_after: list[Violation],
    soft_after: list[Violation],
    level: int,
    dep_rows: dict | None = None,
) -> dict:
    """Why a refused answer was refused, in the terms the verdict is decided in.

    Record S6.7's own limit: `fix` carried `level` and `verdict` and nothing
    else, so the run could report *that* 15 answers introduced a `missing_arg`
    and never *which* argument they dropped, nor whether the drop sat on the row
    the finding names — the one question that separates "the ask is too wide"
    from "the model is wrong here". That is S6.4's mistake in a second place and
    this closes it: the refused submission's own rows are diffed against the
    record and each side is marked `governed` (inside `fixlevel.governed_keys`,
    i.e. a row the level itself names) or not, and every violation class the
    answer introduced is listed with the position that carries it.

    Nothing here reaches a session — it is written to the log after the verdict
    is already decided, and `fix_verdict` is not consulted about it. The
    derivation's answer stays out of the notice exactly as before.
    """
    keys = fixlevel.governed_keys(
        fixlevel.select(before, level, prior, dep_rows), level, dep_rows
    )

    def keyed(rows: dict[int, list[SkelRow]]) -> dict[fixlevel.RowKey, str]:
        return {_key_of(r): r.role for rs in rows.values() for r in rs}

    b, a = keyed(prior), keyed(submitted)

    def entry(key: fixlevel.RowKey, *roles: str) -> dict:
        line, token, arg_line, arg_token = key
        return {
            "predicate": [line, token],
            "argument": [arg_line, arg_token],
            "role": list(roles) if len(roles) > 1 else roles[0],
            "governed": key in keys,
        }

    added = sorted(a.keys() - b.keys())
    removed = sorted(b.keys() - a.keys())
    relabelled = sorted(k for k in b.keys() & a.keys() if b[k] != a[k])
    seen = {fixlevel.violation_class(v) for v in before}
    introduced = [v for v in soft_after if fixlevel.violation_class(v) not in seen]
    return {
        **row_delta(prior, submitted),
        "rows": {
            "added": [entry(k, a[k]) for k in added[:SAMPLE_VIOLATIONS]],
            "removed": [entry(k, b[k]) for k in removed[:SAMPLE_VIOLATIONS]],
            "relabelled": [
                entry(k, b[k], a[k]) for k in relabelled[:SAMPLE_VIOLATIONS]
            ],
        },
        # The rows the level itself named, and what the answer did with each —
        # the level's own job, separated from everything the answer did beside
        # it. `missing` is a governed row the answer did not return at all.
        "governed_rows": {
            "named": len(keys),
            "relabelled": sum(1 for k in relabelled if k in keys),
            "removed": sum(1 for k in removed if k in keys),
            "untouched": sum(1 for k in keys if k in b and k in a and b[k] == a[k]),
            "missing": sum(1 for k in keys if k not in a),
        },
        "findings_before": len(fixlevel.select(before, level, dep_rows=dep_rows)),
        "findings_after": len(
            fixlevel.select(soft_after, level, dep_rows=dep_rows)
        ),
        "soft_before": len(before),
        "soft_after": len(soft_after),
        "hard_after": [violation_record(v) for v in hard_after[:SAMPLE_VIOLATIONS]],
        # The classes the answer brought that the unit did not carry — the
        # `new_class` refusal, itemised, each with the position it sits on and
        # whether that position is one the level asked about.
        "introduced": [
            {
                **violation_record(v),
                "class": fixlevel.violation_class(v),
                "governed": (
                    (pos := _violation_position(v)) is not None and pos in keys
                ),
            }
            for v in introduced[:SAMPLE_VIOLATIONS]
        ],
        "introduced_total": len(introduced),
    }
