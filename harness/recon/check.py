"""Stage-5 addendum: validate `harness/recon/<canticle>/NN.tsv` against the deterministic
derivation — the same hard/soft violation check (and soft-violation-by-class stats) gold gets
from `skel/skel.py --check`/`--stats` — with no model call.

The recon TSVs are byte-compatible with gold `skel/<canticle>/NN.tsv` (`../stages/05.md` §1), so
the same validation applies; only the artifact root differs. This wraps the common
`dante_corpus.skel` validation directly (`validate_unit`, `load_skel(..., base_dir=...)`) rather
than reusing gold's driver scripts under `skel/`, which stay untouched — `skel.py --check`/
`--stats` still own gold's own root.

    uv run python -m harness.recon.check [--root harness/recon]
                                          [--canticle C] [--canto N] [--stats]

Exit code is 1 if any hard violation is found (a missing line, or a genuine derivation mismatch);
soft violations (tag-kind — role-vocabulary/membership/derivation divergences) are reported but
do not fail the run, mirroring `skel.py --check`'s own semantics. `--stats` swaps the per-position
detail for a soft-violation breakdown by class (and by role, for extra_arg/missing_arg), mirroring
`skel.py --stats`.
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path
from typing import TextIO

from dante_corpus import api, case, dep, morph, np, skel
from harness.extractor import fixlevel
from harness.recon.readout import CANTICLE_COUNTS

_DIVERGENCE_KINDS = fixlevel._DIVERGENCE_KINDS


def _morph_rows(canticle: str, number: int) -> dict[int, list]:
    if not morph.has_morph(canticle, number):
        return {}
    return {no: list(rows) for no, rows in morph.load_morph(canticle, number).items()}


def _np_rows(canticle: str, number: int) -> dict[int, list]:
    if not np.has_np(canticle, number):
        return {}
    return {no: list(rows) for no, rows in np.load_np(canticle, number).items()}


def _dep_rows(canticle: str, number: int) -> dict[int, list]:
    if not dep.has_dep(canticle, number):
        return {}
    return {no: list(rows) for no, rows in dep.load_dep(canticle, number).items()}


def _case_rows(canticle: str, number: int) -> dict[int, list]:
    if not case.has_case(canticle, number):
        return {}
    return {no: list(rows) for no, rows in case.load_case(canticle, number).items()}


def _classify_violations(
    nos: list[int], texts: list[str], rows_by_line: dict[int, list[skel.SkelRow]],
    morph_rows: dict[int, list], np_rows: dict[int, list],
    dep_rows: dict[int, list], case_rows: dict[int, list],
) -> tuple[list[morph.Violation], list[morph.Violation]]:
    """Split validate_unit results into (hard, soft). tag -> soft; rest -> hard."""
    hard, soft = [], []
    for v in skel.validate_unit(nos, texts, rows_by_line, morph_rows, np_rows, dep_rows, case_rows):
        (soft if v.kind == "tag" else hard).append(v)
    return hard, soft


def check_canto(canticle: str, number: int, root: Path) -> dict:
    """Validate one `<root>/<canticle>/NN.tsv` against the frozen L1-L4 layers.

    Returns a result record: `status` ("missing" / "ok" / "hard_violations"), `hard`/`soft`
    counts, `missing` (line numbers absent from the artifact), and `violations` (the individual
    `Violation`s, hard first).
    """
    if not skel.has_skel(canticle, number, base_dir=root):
        return {"canticle": canticle, "canto": number, "status": "missing",
                "hard": 1, "soft": 0, "missing": [], "violations": []}

    data = skel.load_skel(canticle, number, base_dir=root)
    morph_rows = _morph_rows(canticle, number)
    np_rows = _np_rows(canticle, number)
    dep_rows = _dep_rows(canticle, number)
    case_rows = _case_rows(canticle, number)
    lines = api.canto(canticle, number).lines()
    text_by_no = {line.no: line.text for line in lines}
    nos_all = [line.no for line in lines]
    texts_all = [line.text for line in lines]

    missing = [no for no in nos_all if no not in data]
    violations: list[morph.Violation] = []
    hard = len(missing)
    soft = 0
    for unit in dep.sentence_groups(nos_all, texts_all, dep.MAX_UNIT_LINES):
        if any(no in missing for no in unit):
            continue
        unit_texts = [text_by_no[no] for no in unit]
        rows_by_line = {no: list(data[no]) for no in unit}
        hard_vs, soft_vs = _classify_violations(
            unit, unit_texts, rows_by_line, morph_rows, np_rows, dep_rows, case_rows,
        )
        hard += len(hard_vs)
        soft += len(soft_vs)
        violations.extend(hard_vs)
        violations.extend(soft_vs)

    status = "ok" if hard == 0 else "hard_violations"
    # `rows` rides along for `print_fix_level`: a fix level acts on a row, so its
    # selection needs the artifact and not only the findings (`fixlevel.select`).
    # `dep_rows` rides along for the same reason on the other side: a level-2 class
    # is *defined* by the Layer-4 edge under the argument, so the readout cannot
    # apply the definition without the tree the run applies it with.
    return {"canticle": canticle, "canto": number, "status": status,
            "hard": hard, "soft": soft, "missing": missing, "violations": violations,
            "rows": {no: list(rows) for no, rows in data.items()},
            "dep_rows": dep_rows}


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
    stream: TextIO | None = sys.stderr,
    verbose: bool = True,
) -> list[dict]:
    """Check every selected canto, reporting progress as it goes.

    `verbose` (the `--check` default) also prints each position's violation detail; `--stats`
    wants only the per-canto progress line, since its own class breakdown covers the rest.
    """
    results = []
    for name, n in iter_targets(root, canticle, canto):
        result = check_canto(name, n, root)
        results.append(result)
        if stream is not None:
            if verbose:
                _print_detail(result, stream)
            print(_progress_line(result), file=stream, flush=True)
    return results


def _print_detail(result: dict, stream: TextIO) -> None:
    canticle, number = result["canticle"], result["canto"]
    if result["status"] == "missing":
        print(f"Missing: {canticle}/{number:02d}.tsv", file=stream)
        return
    for v in result["violations"]:
        print(f"{canticle} {number}:{v.line} [{v.kind}] {v.detail}", file=stream)
    if result["missing"]:
        print(f"{canticle} {number}: missing lines {result['missing']}", file=stream)


def _progress_line(result: dict) -> str:
    head = f"[check] {result['canticle']} {result['canto']:>2}"
    if result["status"] == "missing":
        return f"{head} — no TSV on disk"
    return f"{head} — {result['hard']} hard, {result['soft']} soft"


def print_report(results: list[dict], *, stream: TextIO = sys.stdout) -> None:
    hard = sum(r["hard"] for r in results)
    soft = sum(r["soft"] for r in results)
    print(f"check complete: {hard} hard, {soft} soft violation(s)", file=stream)


def _violation_class(v: morph.Violation) -> str:
    """The class a soft finding is counted under — one implementation, shared with
    the Stage-6 fix levels (`harness/extractor/fixlevel.py`)."""
    return fixlevel.violation_class(v)


def print_stats(results: list[dict], *, stream: TextIO = sys.stdout) -> None:
    hard = sum(r["hard"] for r in results)
    all_soft = [v for r in results for v in r["violations"] if v.kind == "tag"]

    by_kind: Counter[str] = Counter()
    by_role: Counter[tuple[str, str]] = Counter()
    by_role_null: Counter[tuple[str, str]] = Counter()
    role_mismatch_pairs: Counter[tuple[str | None, str | None]] = Counter()

    for v in all_soft:
        kind = _violation_class(v)
        by_kind[kind] += 1
        if kind in ("extra_arg", "missing_arg") and v.role is not None:
            by_role[(kind, v.role)] += 1
            if v.arg == (0, 0):
                by_role_null[(kind, v.role)] += 1
        if kind == "role_mismatch":
            role_mismatch_pairs[(v.given_role, v.role)] += 1

    print("By kind:", file=stream)
    for kind, count in by_kind.most_common():
        print(f"  {kind:15s} {count:6d}", file=stream)

    print("\nBy role (extra_arg / missing_arg):", file=stream)
    for (kind, role), count in by_role.most_common():
        null_count = by_role_null[(kind, role)]
        null_tag = f" (of which ∅ (0,0): {null_count})" if null_count else ""
        print(f"  {kind:12s} {role:12s} {count:6d}{null_tag}", file=stream)

    if role_mismatch_pairs:
        print("\nTop role_mismatch pairs (given vs derived):", file=stream)
        for (grole, drole), count in role_mismatch_pairs.most_common():
            print(f"  {grole!r:14s} vs {drole!r:14s} {count:6d}", file=stream)

    print(f"\nstats complete: {len(all_soft)} soft violation(s) ({hard} hard)", file=stream)


def print_fix_level(results: list[dict], level: int, *, stream: TextIO = sys.stdout) -> None:
    """Per-canto counts of the findings a `reconstruct --fix <level>` run acts on.

    The selection readout for Stage 6: which cantos carry work at this level, and
    how much. Deterministic and free — it says what to launch, and (discipline 1)
    nothing about what to do with it.
    """
    total = 0
    print(f"Fix level {level} — "
          f"{', '.join(c.name for c in fixlevel.classes_for(level))}:", file=stream)
    for result in results:
        found = fixlevel.select(
            [v for v in result["violations"] if v.kind == "tag"],
            level,
            result.get("rows"),
            result.get("dep_rows"),
        )
        total += len(found)
        if found:
            print(f"  {result['canticle']:11s} {result['canto']:>2}  {len(found):5d}",
                  file=stream)
    print(f"\nfix-level {level}: {total} finding(s)", file=stream)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).parent,
        help="directory holding <canticle>/NN.tsv (default: this script's own directory)",
    )
    parser.add_argument(
        "--canticle", choices=sorted(CANTICLE_COUNTS), help="check one canticle only"
    )
    parser.add_argument("--canto", type=int, help="check one canto only")
    parser.add_argument(
        "--stats", action="store_true",
        help="soft-violation counts by class (and by role) instead of per-position detail",
    )
    parser.add_argument(
        "--fix-level", metavar="LEVEL",
        help=f"per-canto counts of the soft findings a `reconstruct --fix LEVEL` run "
             f"would act on (1..{fixlevel.MAX_LEVEL}, or 'max' for every level "
             f"defined), instead of per-position detail",
    )
    args = parser.parse_args(argv)

    if args.fix_level is not None:
        try:
            args.fix_level = fixlevel.resolve_level(args.fix_level)
        except ValueError as exc:
            parser.error(f"--fix-level: {exc}")

    quiet = args.stats or args.fix_level is not None
    results = run(args.root, canticle=args.canticle, canto=args.canto, verbose=not quiet)
    if args.stats:
        print_stats(results)
    elif args.fix_level is not None:
        print_fix_level(results, args.fix_level)
    else:
        print_report(results)
    return 1 if any(r["hard"] for r in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
