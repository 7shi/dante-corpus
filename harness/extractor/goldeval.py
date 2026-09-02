"""Evaluation face: accepted rows compared against gold (operator-side).

Split out of `reconstruct.py` (S7.2) — and the split is the point. This is the
only module of the reconstruction stack that opens a gold artifact, so the
boundary Standing Invariant §4 item 1 draws is now a file boundary rather than
a comment: `layers.py`, `outcome.py`, `artifact.py`, `fixrun.py` and the
execution/commit faces of `reconstruct.py` import nothing from here, and this
module is reached only under `--verify-gold`.

Reads the frozen artifacts exactly like `runner/benchmark.py` does; purely
observational — nothing here ever feeds gating or writes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterator

from harness.extractor.layers import RowKey
from harness.extractor.outcome import CantoReconstruction, UnitOutcome

__all__ = ["GoldFace", "GoldReport", "verify_against_gold"]


@dataclass
class GoldReport:
    """Accepted-vs-gold agreement over reconstructed units."""

    units: int = 0
    exact_units: int = 0
    tp: int = 0
    fp: int = 0
    fn: int = 0
    roles: dict = field(default_factory=dict)  # role -> [tp, fp, fn]

    def observe(self, keys: frozenset[RowKey], gold: set[RowKey]) -> dict:
        u_tp = len(keys & gold)
        u_fp = len(keys - gold)
        u_fn = len(gold - keys)
        self.units += 1
        self.exact_units += int(keys == gold)
        self.tp += u_tp
        self.fp += u_fp
        self.fn += u_fn
        for key in keys:
            bucket = self.roles.setdefault(key[2], [0, 0, 0])
            bucket[0 if key in gold else 1] += 1
        for key in gold - keys:
            self.roles.setdefault(key[2], [0, 0, 0])[2] += 1
        return {"tp": u_tp, "fp": u_fp, "fn": u_fn, "exact": keys == gold}

    def add_record(self, record: dict) -> None:
        """Resume support: fold a logged `gold` record back into the aggregate."""
        self.units += 1
        self.exact_units += int(bool(record.get("exact")))
        self.tp += int(record.get("tp") or 0)
        self.fp += int(record.get("fp") or 0)
        self.fn += int(record.get("fn") or 0)

    def metrics(self) -> dict:
        precision = self.tp / (self.tp + self.fp) if self.tp + self.fp else 0.0
        recall = self.tp / (self.tp + self.fn) if self.tp + self.fn else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        return {
            "units": self.units,
            "exact_units": self.exact_units,
            "exact_rate": round(self.exact_units / self.units, 4) if self.units else 0.0,
            "tp": self.tp,
            "fp": self.fp,
            "fn": self.fn,
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1": round(f1, 4),
        }

    def summary(self) -> str:
        m = self.metrics()
        return (
            f"gold comparison: exact units {m['exact_units']}/{m['units']} "
            f"= {m['exact_rate']:.3f}, P={m['precision']:.3f} "
            f"R={m['recall']:.3f} F1={m['f1']:.3f} "
            f"(tp={m['tp']} fp={m['fp']} fn={m['fn']})"
        )


@dataclass
class GoldFace:
    """Per-unit gold observation, streamable as units settle.

    Each unit's tp/fp/fn depends only on that unit's accepted rows and its
    canto's frozen skel rows, so the evaluation face can ride `reconstruct`'s
    per-unit durability seam (`emit_unit`) instead of waiting for the canto
    to finish — an interrupted run keeps every settled unit's gold record on
    disk too. `verify_against_gold` wraps this face for callers holding a
    finished `CantoReconstruction`. Purely observational — the result never
    feeds gating or writes.
    """

    report: GoldReport = field(default_factory=GoldReport)
    cache: dict[tuple[str, int], dict] = field(default_factory=dict)

    def observe(self, outcome: UnitOutcome) -> dict:
        from dante_corpus.skel.io import load_skel

        unit = outcome.unit
        key = (unit["canticle"], unit["canto"])
        if key not in self.cache:
            self.cache[key] = load_skel(unit["canticle"], unit["canto"])
        gold_rows = self.cache[key]
        gold = {
            (row.line, row.token, row.role, row.arg_line, row.arg_token)
            for no in range(unit["line_start"], unit["line_end"] + 1)
            for row in gold_rows.get(no, ())
        }
        counts = self.report.observe(outcome.row_keys, gold)
        return {"record": "gold", **unit, **counts}


def verify_against_gold(
    recon: CantoReconstruction,
) -> tuple[GoldReport, Iterator[dict]]:
    """Compare every unit's accepted rows against gold (evaluation face).

    Reads the frozen artifacts exactly like `runner/benchmark.py`; purely
    observational — the result never feeds gating or writes.
    """
    face = GoldFace()

    def records():
        for outcome in recon.outcomes:
            yield face.observe(outcome)

    return face.report, records()
