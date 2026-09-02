"""What one parse unit and one canto came out as, and how each reads back.

Split out of `reconstruct.py` (S7.2). `UnitOutcome` is the reconstruction
stack's central value: the canto loop produces it, the fix machinery rewrites
it, the gold face observes it, and the log record is `to_dict()`. It sits below
all of those so each can depend on it without depending on each other.

`_replay_unit_outcome` is the same value rebuilt from rows already on disk —
unit-level resume — with the gates re-run rather than trusted, so a replayed
unit's verdict is measured on the bytes in the artifact.
"""

from __future__ import annotations

import dataclasses
from collections import Counter
from dataclasses import dataclass, field

from dante_corpus.morph import Violation
from dante_corpus.skel.models import SkelRow, _row_sort_key

from harness.extractor.layers import (
    SAMPLE_VIOLATIONS,
    CantoLayers,
    RowKey,
    validate_rows,
    violation_record,
)

__all__ = [
    "CantoReconstruction",
    "UnitOutcome",
    "final_validation_errors",
    "replay_unit_outcome",
]


def final_validation_errors(agent_result) -> list[str]:
    """The gate errors on the submission the session actually handed downstream.

    Read off the last `validate_candidate` dispatch, the same call
    `final_submission_valid` reads its verdict from, so the two can never
    describe different submissions. Empty when it passed, when no session ran,
    or when the fallback is a stub without the attribute.
    """
    validations = getattr(agent_result, "validations", None) or []
    if not validations:
        return []
    result = validations[-1].get("result", {})
    if result.get("valid"):
        return []
    return [str(e) for e in result.get("errors", [])]


@dataclass
class UnitOutcome:
    """One parse unit's reconstruction result plus its two intrinsic gates."""

    unit: dict
    route: str  # "fast" | "agent"
    reason: str
    origin: str  # "fast" | "agent" (dry mode keeps "agent" with no rows)
    fallback_ran: bool
    row_keys: frozenset[RowKey]
    rows: dict[int, list[SkelRow]]
    token_assertions: list[str]
    hard: list[Violation]
    soft: list[Violation]
    fallback_seconds: float | None = None
    # Verdict the agent's own gate gave the submission that was adopted: None
    # when nothing was validated (fast path, dry mode, or a session that never
    # called the tool), False when the session ended on rows its gate rejected
    # — a *provisional* adoption at the turn cap, and the primary readout of
    # whether in-session correction converges (`../STAGE5.md` record S5.5).
    final_submission_valid: bool | None = None
    # Resumes the session was given after ending on rows its own gate rejected
    # (S6.6). None when no session ran. Logged because it is the only part of
    # that policy's effect the per-canto log would not otherwise carry — the
    # transcript is not written, so a run could not be read out without it.
    invalid_nudges: int | None = None
    # What the session's own gate said about the submission that was adopted,
    # when it said no (S6.7). `final_submission_valid` records *that* it
    # refused; without the errors themselves a run cannot say what it refused
    # over — and S6.7 found every accepted fix sitting on such a submission, so
    # the two verdicts disagreeing is now the thing to explain. Empty list when
    # the gate passed or no session ran.
    final_validation_errors: list[str] = dataclasses.field(default_factory=list)
    # Unit-level resume: a unit rebuilt from the TSV already on disk instead of
    # re-running `engine.run_unit`. Its gates are still re-run (deterministic,
    # no model cost), so `passed` is measured rather than trusted; the caller
    # must not re-emit it to the sink, which already holds the artifact.
    replayed: bool = False

    @property
    def passed(self) -> bool:
        """§4.1 gates 1+2: clean assertions AND 0 hard / 0 soft violations."""
        return not self.token_assertions and not self.hard and not self.soft

    def to_dict(self) -> dict:
        kinds = Counter(v.kind for v in self.hard + self.soft)
        sample = [
            violation_record(v)
            for v in (self.hard + self.soft)[:SAMPLE_VIOLATIONS]
        ]
        return {
            "record": "unit",
            **self.unit,
            "route": self.route,
            "reason": self.reason,
            "origin": self.origin,
            "fallback_ran": self.fallback_ran,
            "accepted_rows": len(self.row_keys),
            # Persisted so an interrupted run can resume unit-by-unit: a
            # future attempt rebuilds this unit's rows from these keys
            # instead of re-running the (expensive, live) fallback.
            "row_keys": [list(key) for key in sorted(self.row_keys)],
            "token_assertion_errors": len(self.token_assertions),
            "assertions": list(self.token_assertions[:SAMPLE_VIOLATIONS]),
            "hard_violations": len(self.hard),
            "soft_violations": len(self.soft),
            "violation_kinds": dict(kinds),
            "sample_violations": sample,
            "passed": self.passed,
            # True only when the session ended on rows its own gate rejected.
            "adopted_invalid": self.final_submission_valid is False,
            "final_submission_valid": self.final_submission_valid,
            "invalid_nudges": self.invalid_nudges,
            "final_validation_errors": self.final_validation_errors[
                :SAMPLE_VIOLATIONS
            ],
            "fallback_seconds": (
                None if self.fallback_seconds is None
                else round(self.fallback_seconds, 1)
            ),
        }


def replay_unit_outcome(
    rows: dict[int, list[SkelRow]], layers: CantoLayers, group: list[int]
) -> UnitOutcome:
    """Rebuild a `UnitOutcome` from the unit's rows already on disk in the TSV.

    Unit-level resume: the artifact carries the rows, so nothing has to be
    re-run through the (expensive, live) fallback. What the artifact does *not*
    carry is telemetry — route, reason, timings all belong to the attempt that
    produced it — so those read `tsv` rather than being invented. The gates,
    by contrast, are re-run: they are deterministic and free, so the verdict
    here is measured on the bytes on disk instead of trusted from a log.
    """
    line_start, line_end = group[0], group[-1]
    unit_rows = {no: list(rows.get(no, [])) for no in group}
    row_keys = frozenset(
        (row.line, row.token, row.role, row.arg_line, row.arg_token)
        for line_rows in unit_rows.values()
        for row in line_rows
    )
    hard, soft = validate_rows(layers, group, unit_rows)
    return UnitOutcome(
        unit={
            "canticle": layers.canticle,
            "canto": layers.canto,
            "line_start": line_start,
            "line_end": line_end,
        },
        route="tsv",
        reason="already settled in the artifact",
        origin="tsv",
        fallback_ran=False,
        row_keys=row_keys,
        rows=unit_rows,
        token_assertions=[],
        hard=hard,
        soft=soft,
        replayed=True,
    )


@dataclass
class CantoReconstruction:
    """Every unit outcome of one canto, plus the merged candidate artifact."""

    canticle: str
    canto: int
    nos: list[int]
    outcomes: list[UnitOutcome] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        """A canto commits only when every one of its units passes."""
        return bool(self.outcomes) and all(o.passed for o in self.outcomes)

    def rows_by_line(self) -> dict[int, list[SkelRow]]:
        merged: dict[int, list[SkelRow]] = {}
        for outcome in self.outcomes:
            for no, rows in outcome.rows.items():
                merged.setdefault(no, []).extend(rows)
        for rows in merged.values():
            rows.sort(key=_row_sort_key)
        return merged
