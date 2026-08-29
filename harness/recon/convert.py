"""Stage-5 durability conversion: per-canto run logs -> committable skel TSVs.

The Stage-4 corpus run left 100 streaming JSONL logs at
`harness/recon/<canticle>/NN.log`. They are gitignored, disk-only, and
nothing regenerates them (live LLM output, see `../STAGE5.md` §1). This
script converts each one's settled reconstruction into a committable file
beside it:

    <canticle>/NN.tsv

in the **same format as gold `skel/<canticle>/NN.tsv`**, byte-rendered
through `reconstruct.render_tsv` (the writer-parity mirror of
`skel.io.write_skel`). Gold stays immutable: nothing here writes under
`skel/` (PLAN.md §4 item 1), so `diff harness/recon/inferno/01.tsv
skel/inferno/01.tsv` is the run's divergence readout.

What the TSV cannot carry — routing, gate verdicts, violation detail, gold
scores, and the `llm_request`/`llm_response` cost instrumentation — is run
telemetry, not corpus content, and is deliberately **not** committed
(operator decision 2026-08-29, `../STAGE5.md` §2). It is read from the logs
on demand by `harness/recon/readout.py` for as long as they exist.

Deterministic, idempotent and LLM-free: it reads logs plus the frozen L1-L4
layers, and re-running it over unchanged logs reproduces byte-identical
output, so it is a repeatable generation step rather than a one-time
migration — re-run it after any future corpus run to refresh the artifacts.

    uv run python -m harness.recon.convert [--root harness/recon]
                                           [--canticle C] [--canto N]
                                           [--check]

`--check` writes nothing and exits non-zero if any TSV on disk differs from
what this script would generate (drift detection for CI / review).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import TextIO

from harness.extractor.reconstruct import CantoLayers, build_rows, render_tsv
from harness.recon.readout import CANTICLE_COUNTS, is_complete, load_log


def _unit_key(record: dict) -> tuple[int, int]:
    return (record["line_start"], record["line_end"])


def convert_canto(
    records: list[dict], canticle: str, canto: int
) -> tuple[str, dict]:
    """Render one canto's log into `(tsv_payload, stats)`.

    Row keys are re-anchored on the frozen Layer-1 token stream through the
    very same `build_rows` the run itself used, so the words in the TSV are
    not trusted from the log — they are recomputed, and any key that no
    longer indexes the token stream is reported in `stats` instead of
    silently landing. Units are keyed by `(line_start, line_end)`; a later
    record for the same span (a resumed attempt) supersedes the earlier one.
    """
    layers = CantoLayers.load(canticle, canto)

    units: dict[tuple[int, int], dict] = {}
    for record in records:
        if record.get("record") == "unit":
            units[_unit_key(record)] = record

    merged: dict[int, list] = {}
    assertion_errors: list[str] = []
    accepted_keys = 0
    for (line_start, line_end), record in sorted(units.items()):
        row_keys = {tuple(key) for key in record.get("row_keys", [])}
        accepted_keys += len(row_keys)
        rows, errors = build_rows(row_keys, layers, line_start, line_end)
        for no, line_rows in rows.items():
            merged.setdefault(no, []).extend(line_rows)
        assertion_errors.extend(f"{line_start}-{line_end}: {e}" for e in errors)

    lines = [(no, merged.get(no, [])) for no in sorted(layers.nos)]
    payload = render_tsv(lines)
    stats = {
        "units": len(units),
        "lines": len(layers.nos),
        "rows": sum(len(rows) for _, rows in lines),
        "accepted_row_keys": accepted_keys,
        "log_complete": is_complete(records),
        "token_assertion_errors": assertion_errors,
    }
    return payload, stats


def convert_log(path: Path, canticle: str, canto: int, *, check: bool) -> dict:
    """Convert one log in place; returns the per-canto result record.

    `check` mode renders exactly the same payload but writes nothing,
    reporting instead whether the on-disk TSV already matches.
    """
    result: dict = {"canticle": canticle, "canto": canto, "status": "ok"}
    if not path.exists():
        result["status"] = "missing_log"
        return result

    payload, stats = convert_canto(load_log(path), canticle, canto)
    result.update(stats)
    result["token_assertion_errors"] = len(stats["token_assertion_errors"])
    result["assertions"] = stats["token_assertion_errors"]

    target = path.with_suffix(".tsv")
    on_disk = (
        target.read_text(encoding="utf-8") if target.exists() else None
    )
    if check:
        result["drift"] = on_disk != payload
        if result["drift"]:
            result["status"] = "drift"
        return result

    result["changed"] = on_disk != payload
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
            yield name, n, root / name / f"{n:02d}.log"


def run(
    root: Path,
    *,
    canticle: str | None = None,
    canto: int | None = None,
    check: bool = False,
    stream: TextIO | None = sys.stderr,
) -> list[dict]:
    """Convert every selected canto, reporting progress as it goes.

    Each canto is a second or two of deterministic work, but the corpus is
    100 of them and every layer load hits disk — so the run stays visible by
    default (§5 Live-run observability), one line per canto on stderr.
    """
    results = []
    for name, n, path in iter_targets(root, canticle, canto):
        result = convert_log(path, name, n, check=check)
        results.append(result)
        if stream is not None:
            print(_progress_line(result), file=stream, flush=True)
    return results


def _progress_line(result: dict) -> str:
    head = f"[convert] {result['canticle']} {result['canto']:>2}"
    if result["status"] == "missing_log":
        return f"{head} — no log on disk, skipped"
    detail = (
        f"{result['units']} units, {result['rows']} rows"
        + ("" if result["log_complete"] else ", INCOMPLETE log")
        + (
            ""
            if not result["token_assertion_errors"]
            else f", {result['token_assertion_errors']} dropped row keys"
        )
    )
    if result["status"] == "drift":
        return f"{head} — DRIFT ({detail})"
    if "drift" in result:
        return f"{head} — up to date ({detail})"
    tail = "written" if result["changed"] else "unchanged"
    return f"{head} — {detail} -> {tail}"


def print_report(
    results: list[dict], *, check: bool, stream: TextIO = sys.stdout
) -> None:
    converted = [r for r in results if r["status"] != "missing_log"]
    missing = [r for r in results if r["status"] == "missing_log"]
    incomplete = [r for r in converted if not r["log_complete"]]
    dropped = [r for r in converted if r["token_assertion_errors"]]
    drifted = [r for r in converted if r["status"] == "drift"]
    verb = "checked" if check else "converted"
    print(
        f"\n{verb} {len(converted)} cantos: "
        f"{sum(r['units'] for r in converted)} units, "
        f"{sum(r['rows'] for r in converted)} rows",
        file=stream,
    )
    if missing:
        print(f"  missing logs: {len(missing)}", file=stream)
    if incomplete:
        names = ", ".join(f"{r['canticle']} {r['canto']}" for r in incomplete)
        print(f"  logs without a summary record: {names}", file=stream)
    if dropped:
        names = ", ".join(f"{r['canticle']} {r['canto']}" for r in dropped)
        print(f"  cantos with dropped row keys: {names}", file=stream)
    if check:
        print(
            "  artifacts up to date"
            if not drifted
            else f"  DRIFT in {len(drifted)} cantos",
            file=stream,
        )
    else:
        changed = [r for r in converted if r["changed"]]
        print(f"  TSVs written: {len(changed)}", file=stream)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).parent,
        help="directory holding <canticle>/NN.log (default: this script's own directory)",
    )
    parser.add_argument(
        "--canticle", choices=sorted(CANTICLE_COUNTS), help="convert one canticle only"
    )
    parser.add_argument("--canto", type=int, help="convert one canto only")
    parser.add_argument(
        "--check",
        action="store_true",
        help="write nothing; exit 1 if any TSV differs from the regenerated one",
    )
    args = parser.parse_args(argv)

    results = run(
        args.root, canticle=args.canticle, canto=args.canto, check=args.check
    )
    print_report(results, check=args.check)
    if args.check and any(r["status"] == "drift" for r in results):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
