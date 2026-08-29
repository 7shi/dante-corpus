"""Stage-5 readout: row-level agreement of the recon corpus with gold.

    P / R / F1 over exact rows `(line, token, role, arg_line, arg_token)`

against the same canto's gold TSV. Role-less rows (a predicate with no arguments) carry no
role assignment and are excluded from both sides.

**This is a measurement, not an objective.** It reports how far the autonomous
reconstruction landed from the evaluation reference, in the same spirit as `benchmark.py`'s
micro F1 and `reconstruct.py --verify-gold` — nothing more. Gold is the *benchmark* for
`harness/`, never its target (PLAN.md §1, §4 item 1): fitting repair rules to it would be
teaching to the test, would make this very number meaningless, and would reinstate the
top-down "rails" methodology `harness/` exists to replace. Repair rules are therefore
derived from the layer's own schema and derivation contract (`dante_corpus/skel/validate.py`,
`derive.py`) with gold unopened, and this score is read *afterwards* to see where the
gold-free work landed — it may not decide what ships (`../STAGE5.md` §5).

Operator-side only, like `benchmark.py`: it reads gold, so nothing under `runner/` may
import it (PLAN.md §4 item 1). Read-only and LLM-free — it writes nothing anywhere.

    uv run python -m harness.recon.agree [--root harness/recon] [--canticle C]
                                         [--canto N] [--per-canticle]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import TextIO

from dante_corpus import skel
from harness.recon.readout import CANTICLE_COUNTS

Row = tuple[str, int, int, int, str, int, int]


def canto_rows(canticle: str, canto: int, base_dir: Path | None) -> set[Row]:
    """The canto's role-bearing rows as comparable keys, or an empty set if absent."""
    if not skel.has_skel(canticle, canto, base_dir=base_dir):
        return set()
    data = skel.load_skel(canticle, canto, base_dir=base_dir)
    return {
        (canticle, canto, no, row.token, row.role, row.arg_line, row.arg_token)
        for no, rows in data.items()
        for row in rows
        if row.role
    }


def score(predicted: set[Row], gold: set[Row]) -> dict:
    tp = len(predicted & gold)
    precision = tp / len(predicted) if predicted else 0.0
    recall = tp / len(gold) if gold else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {"predicted": len(predicted), "gold": len(gold), "tp": tp,
            "precision": precision, "recall": recall, "f1": f1}


def iter_targets(canticle: str | None, canto: int | None):
    for name, count in CANTICLE_COUNTS.items():
        if canticle is not None and name != canticle:
            continue
        for n in range(1, count + 1):
            if canto is not None and n != canto:
                continue
            yield name, n


def run(
    root: Path,
    *,
    canticle: str | None = None,
    canto: int | None = None,
) -> tuple[dict, dict[str, dict]]:
    """Score the selected cantos, returning `(corpus_wide, per_canticle)` records."""
    predicted: dict[str, set[Row]] = {}
    gold: dict[str, set[Row]] = {}
    for name, n in iter_targets(canticle, canto):
        predicted.setdefault(name, set()).update(canto_rows(name, n, root))
        gold.setdefault(name, set()).update(canto_rows(name, n, None))

    per_canticle = {name: score(predicted[name], gold[name]) for name in predicted}
    overall = score(
        set().union(*predicted.values()) if predicted else set(),
        set().union(*gold.values()) if gold else set(),
    )
    return overall, per_canticle


def _line(label: str, s: dict) -> str:
    return (f"{label:<12} rows={s['predicted']:>6} gold={s['gold']:>6} tp={s['tp']:>6}  "
            f"P={s['precision']:.4f} R={s['recall']:.4f} F1={s['f1']:.4f}")


def print_report(
    overall: dict,
    per_canticle: dict[str, dict],
    *,
    detail: bool,
    stream: TextIO | None = None,
) -> None:
    stream = stream or sys.stdout
    if detail:
        for name, s in per_canticle.items():
            print(_line(name, s), file=stream)
    print(_line("corpus-wide", overall), file=stream)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).parent,
        help="directory holding <canticle>/NN.tsv (default: this script's own directory)",
    )
    parser.add_argument(
        "--canticle", choices=sorted(CANTICLE_COUNTS), help="score one canticle only"
    )
    parser.add_argument("--canto", type=int, help="score one canto only")
    parser.add_argument(
        "--per-canticle", action="store_true", help="also break the score down per canticle"
    )
    args = parser.parse_args(argv)

    overall, per_canticle = run(args.root, canticle=args.canticle, canto=args.canto)
    print_report(overall, per_canticle, detail=args.per_canticle)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
