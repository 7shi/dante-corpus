"""Aggregate reporting: the run's two §6 faces, fed from streamed records.

Split out of `reconstruct.py` (S7.2). `ReconstructReport` consumes the same
JSONL records the log carries (`add_unit` / `add_gold` / `add_canto_complete`),
so the machine-readable `metrics()` and the human-readable `summary()` are two
renderings of one aggregate and cannot drift from each other or from the log.
`load_log` reads a previous attempt's records back for offline analysis — the
log itself is append-only and never read back by a run (`../stages/05.md` S5.5).
"""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

from harness.extractor.goldeval import GoldReport

__all__ = ["ReconstructReport", "load_log"]


@dataclass
class ReconstructReport:
    """Aggregates streamed records; ships both §6 reporting faces.

    Fed identically from live results and replayed resume records via
    `add_unit` / `add_gold` / `add_canto_complete`.
    """

    units: int = 0
    passed_units: int = 0
    routes: Counter = field(default_factory=Counter)
    reasons: Counter = field(default_factory=Counter)
    token_assertion_errors: int = 0
    hard_violations: int = 0
    soft_violations: int = 0
    violation_kinds: Counter = field(default_factory=Counter)
    fallback_seconds: list[float] = field(default_factory=list)
    canto_seconds: list[float] = field(default_factory=list)
    api_retries: list[int] = field(default_factory=list)
    api_retry_seconds: list[float] = field(default_factory=list)
    cantos: int = 0
    cantos_passed: int = 0
    writes: list[dict] = field(default_factory=list)
    gold: GoldReport | None = None

    def add_unit(self, record: dict) -> None:
        self.units += 1
        self.passed_units += int(bool(record.get("passed")))
        self.routes[record.get("route", "?")] += 1
        self.reasons[record.get("reason", "?")] += 1
        self.token_assertion_errors += int(record.get("token_assertion_errors") or 0)
        self.hard_violations += int(record.get("hard_violations") or 0)
        self.soft_violations += int(record.get("soft_violations") or 0)
        for kind, count in (record.get("violation_kinds") or {}).items():
            self.violation_kinds[kind] += count
        seconds = record.get("fallback_seconds")
        if seconds is not None:
            self.fallback_seconds.append(float(seconds))

    def add_gold(self, record: dict) -> None:
        if self.gold is None:
            self.gold = GoldReport()
        self.gold.add_record(record)

    def add_canto_complete(self, record: dict) -> None:
        self.cantos += 1
        self.cantos_passed += int(bool(record.get("passed")))
        commit_rec = record.get("commit")
        if commit_rec is not None:
            self.writes.append(commit_rec)
        # Wall clock rides the canto records (sum-the-records architecture):
        # like the benchmark's per-case turn sums, resumed attempts fold in
        # per canto and idle gaps between attempts never count.
        seconds = record.get("elapsed_seconds")
        if seconds is not None:
            self.canto_seconds.append(float(seconds))
        # §4 make-the-invisible-measurable: per-canto api-retry deltas fold in
        # only when the run tracked them (a status line owned the display).
        retries = record.get("api_retries")
        if retries is not None:
            self.api_retries.append(int(retries))
            self.api_retry_seconds.append(
                float(record.get("api_retry_seconds") or 0.0)
            )

    def metrics(self) -> dict:
        metrics = {
            "cantos": self.cantos,
            "cantos_passed": self.cantos_passed,
            "written_cantos": sum(1 for w in self.writes if w.get("wrote")),
            "units": self.units,
            "passed_units": self.passed_units,
            "blocked_units": self.units - self.passed_units,
            "routes": dict(self.routes),
            "reasons": dict(self.reasons),
            "token_assertion_errors": self.token_assertion_errors,
            "hard_violations": self.hard_violations,
            "soft_violations": self.soft_violations,
            "violation_kinds": dict(self.violation_kinds),
            "fallback_seconds_total": round(sum(self.fallback_seconds), 1),
            "fallback_seconds_max": round(max(self.fallback_seconds), 1)
            if self.fallback_seconds
            else None,
            "wall_clock_seconds": round(sum(self.canto_seconds), 1)
            if self.canto_seconds
            else None,
            "api_retries": sum(self.api_retries) if self.api_retries else None,
            "api_retry_seconds": (
                round(sum(self.api_retry_seconds), 1)
                if self.api_retry_seconds
                else None
            ),
        }
        if self.gold is not None:
            metrics["gold"] = self.gold.metrics()
        return metrics

    def summary(self) -> str:
        lines = [
            f"cantos: {self.cantos} passing all gates "
            f"{self.cantos_passed}/{self.cantos}"
            + (
                f", written {sum(1 for w in self.writes if w.get('wrote'))}"
                if self.writes
                else ""
            ),
            f"units: {self.units} passing {self.passed_units} "
            f"(gate: every unit 0 hard / 0 soft)",
            f"routing: "
            + ", ".join(
                f"{route}={count}" for route, count in sorted(self.routes.items())
            ),
            f"  reasons: "
            + ", ".join(
                f"{reason}={count}" for reason, count in sorted(self.reasons.items())
            ),
            f"violations: hard {self.hard_violations}, soft {self.soft_violations} "
            f"(token assertions {self.token_assertion_errors})",
        ]
        if self.violation_kinds:
            top = ", ".join(
                f"{kind}={count}"
                for kind, count in sorted(
                    self.violation_kinds.items(), key=lambda kv: -kv[1]
                )[:6]
            )
            lines.append(f"  top kinds: {top}")
        if self.fallback_seconds:
            total = sum(self.fallback_seconds)
            lines.append(
                f"fallback sessions: {len(self.fallback_seconds)} in {total:.0f}s "
                f"(max {max(self.fallback_seconds):.1f}s)"
            )
        if self.canto_seconds:
            lines.append(
                f"wall clock: {sum(self.canto_seconds):.0f}s across "
                f"{len(self.canto_seconds)} canto(s)"
            )
        if self.api_retries:
            lines.append(
                f"api retries: {sum(self.api_retries)} "
                f"(~{sum(self.api_retry_seconds):.0f}s backoff)"
            )
        if self.gold is not None:
            lines.append(self.gold.summary())
        return "\n".join(lines)


def load_log(path: str | Path) -> list[dict]:
    """Parse a previous attempt's log into records (torn tails skipped)."""
    records: list[dict] = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            stripped = line.strip()
            if not stripped:
                continue
            try:
                record = json.loads(stripped)
            except json.JSONDecodeError:
                continue
            if isinstance(record, dict):
                records.append(record)
    return records
