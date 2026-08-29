"""Stage-5 divergence reduction: deterministic repair of the committed recon TSVs.

S5.2 measured the Stage-4 reconstruction at 897 hard / 5,267 soft violations
(`../STAGE5.md` §4). Hard violations are **not** a diff against gold — they are the
artifact failing the layer's own schema, checked against the frozen L1-L4 layers by
`dante_corpus/skel/validate.py`. This script repairs the two classes the schema declares
outright impossible, in place, over `harness/recon/<canticle>/NN.tsv`:

    R1 `self_arg`     — a role-bearing row whose argument position equals its own
                        predicate's position (`validate.py`: `if arg == pos`). An argument
                        cannot be its own predicate; the assertion is void by definition.
                        Reported as `[dup] argument cites its own predicate`.
    R2 `null_nonsubj` — a role-bearing row that is not `subj` at the null position (0,0)
                        (`validate.py`: `if row.role not in ("subj", "")`). The schema
                        reserves the null position for an unexpressed subject. Reported as
                        `[position] role 'X' may not use (0,0)`.

**Why deletion is the repair.** Each such row asserts a relation the schema forbids, and
nothing in L1-L4 reconstructs what was meant: R1 is an enclitic pronoun (`aiutami`,
`trarrotti`, `venendomi`) whose referent needs a resolution decision, R2 an elided argument
with no position to cite. Repairing them by *inventing* a position would fabricate a claim
the layers do not support, so the conservative repair is to withdraw the void assertion and
leave the rest of the predicate's frame untouched. Both rules are derived from the schema
alone; gold is not consulted anywhere in this file, and the agreement readout
(`agree.py`) is run afterwards to see where the repair landed, never to choose it
(`../STAGE5.md` §5).

The two remaining hard classes (`[clausal] xcomp/ccomp argument is not a predicate`) are
NOT touched here: unlike these, they have a derivable alternative, so a conservative
deletion is the wrong repair and they need their own design pass.

Deterministic, LLM-free and idempotent — it reads the committed TSVs plus the frozen
Layer-1 token stream, never `skel/`, and re-running it over already-repaired artifacts
rewrites nothing.

    uv run python -m harness.recon.repair [--root harness/recon]
                                          [--canticle C] [--canto N] [--check]

`--check` writes nothing and exits non-zero if any TSV on disk still carries a repairable
row (drift detection for CI / review).
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path
from typing import TextIO

from dante_corpus import api, skel
from dante_corpus.skel.models import SkelRow
from harness.extractor.reconstruct import render_tsv
from harness.recon.readout import CANTICLE_COUNTS

RULES = ("self_arg", "null_nonsubj")


def classify(row: SkelRow) -> str | None:
    """Name the repair rule that deletes `row`, or `None` to keep it.

    Role-less rows are the line's own predicate-free placeholder and are never touched.
    """
    if not row.role:
        return None
    if (row.arg_line, row.arg_token) == (row.line, row.token):
        return "self_arg"
    if row.role != "subj" and (row.arg_line, row.arg_token) == (0, 0):
        return "null_nonsubj"
    return None


def repair_rows(
    rows_by_line: dict[int, list[SkelRow]]
) -> tuple[dict[int, list[SkelRow]], Counter, list[str]]:
    """Apply both rules, returning (kept rows, per-rule counts, emptied-predicate notes).

    A predicate whose every row is deleted would vanish from the artifact entirely,
    turning a hard violation into a `missing_tuple`; that never happens in the Stage-4
    corpus, but it is reported rather than assumed away.
    """
    kept: dict[int, list[SkelRow]] = {}
    counts: Counter = Counter()
    emptied: list[str] = []
    for no, rows in rows_by_line.items():
        survivors = []
        dropped_predicates = set()
        for row in rows:
            rule = classify(row)
            if rule is None:
                survivors.append(row)
            else:
                counts[rule] += 1
                dropped_predicates.add(row.token)
        kept[no] = survivors
        remaining = {row.token for row in survivors}
        for token in sorted(dropped_predicates - remaining):
            emptied.append(f"{no}.{token}")
    return kept, counts, emptied


def repair_canto(canticle: str, canto: int, root: Path, *, check: bool) -> dict:
    """Repair one `<root>/<canticle>/NN.tsv` in place; returns the per-canto record."""
    result: dict = {"canticle": canticle, "canto": canto, "status": "ok",
                    "counts": Counter(), "emptied": [], "changed": False}
    if not skel.has_skel(canticle, canto, base_dir=root):
        result["status"] = "missing_tsv"
        return result

    data = skel.load_skel(canticle, canto, base_dir=root)
    rows_by_line = {no: list(rows) for no, rows in data.items()}
    kept, counts, emptied = repair_rows(rows_by_line)
    result["counts"] = counts
    result["emptied"] = emptied

    nos = [line.no for line in api.canto(canticle, canto).lines()]
    payload = render_tsv([(no, kept.get(no, [])) for no in nos])
    target = root / canticle / f"{canto:02d}.tsv"
    result["changed"] = target.read_text(encoding="utf-8") != payload
    if check:
        if result["changed"]:
            result["status"] = "drift"
        return result
    if result["changed"]:
        target.write_text(payload, encoding="utf-8")
    return result


def iter_targets(root: Path, canticle: str | None, canto: int | None):
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
    check: bool = False,
    stream: TextIO | None = sys.stderr,
) -> list[dict]:
    """Repair every selected canto, one visible progress line each (PLAN.md §4 item 5)."""
    results = []
    for name, n in iter_targets(root, canticle, canto):
        result = repair_canto(name, n, root, check=check)
        results.append(result)
        if stream is not None:
            print(_progress_line(result), file=stream, flush=True)
    return results


def _progress_line(result: dict) -> str:
    head = f"[repair] {result['canticle']} {result['canto']:>2}"
    if result["status"] == "missing_tsv":
        return f"{head} — no TSV on disk, skipped"
    counts = result["counts"]
    detail = ", ".join(f"{rule} {counts[rule]}" for rule in RULES if counts[rule])
    detail = detail or "nothing to repair"
    if result["emptied"]:
        detail += f", EMPTIED {' '.join(result['emptied'])}"
    if result["status"] == "drift":
        return f"{head} — DRIFT ({detail})"
    tail = "written" if result["changed"] else "unchanged"
    return f"{head} — {detail} -> {tail}"


def print_report(
    results: list[dict], *, check: bool, stream: TextIO | None = None
) -> None:
    stream = stream or sys.stdout
    present = [r for r in results if r["status"] != "missing_tsv"]
    missing = [r for r in results if r["status"] == "missing_tsv"]
    totals: Counter = Counter()
    for r in present:
        totals.update(r["counts"])
    emptied = [f"{r['canticle']} {r['canto']}: {p}" for r in present for p in r["emptied"]]
    verb = "checked" if check else "repaired"
    print(f"\n{verb} {len(present)} cantos: {sum(totals.values())} rows removed", file=stream)
    for rule in RULES:
        print(f"  {rule}: {totals[rule]}", file=stream)
    if missing:
        print(f"  missing TSVs: {len(missing)}", file=stream)
    if emptied:
        print(f"  predicates left with no rows: {', '.join(emptied)}", file=stream)
    if check:
        drifted = [r for r in present if r["status"] == "drift"]
        print(
            "  artifacts up to date"
            if not drifted
            else f"  DRIFT in {len(drifted)} cantos",
            file=stream,
        )
    else:
        print(f"  TSVs written: {len([r for r in present if r['changed']])}", file=stream)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).parent,
        help="directory holding <canticle>/NN.tsv (default: this script's own directory)",
    )
    parser.add_argument(
        "--canticle", choices=sorted(CANTICLE_COUNTS), help="repair one canticle only"
    )
    parser.add_argument("--canto", type=int, help="repair one canto only")
    parser.add_argument(
        "--check",
        action="store_true",
        help="write nothing; exit 1 if any TSV still carries a repairable row",
    )
    args = parser.parse_args(argv)

    results = run(args.root, canticle=args.canticle, canto=args.canto, check=args.check)
    print_report(results, check=args.check)
    if args.check and any(r["status"] == "drift" for r in results):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
