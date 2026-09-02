"""Gated reconstruction pipeline: whole-canto Layer-5 rebuild behind three gates (Milestone 2.4).

Fourth Stage-2 deliverable (`harness/extractor/PLAN.md` §4): drive
`HybridEngine.run_unit` over every parse unit of whole cantos — the mined fast
path deciding what it can, the Stage-1 agent fallback (operator-run, live)
deciding the rest — and gate every disk write on the three §4.1 criteria:

1. **Token-stream assertion** against Layer 1: every candidate row's predicate
   and argument positions must index the canto's alpha-token stream, and each
   row's word anchor is taken verbatim from that stream.
2. **0-soft regression verification** through the proven checker machinery:
   `skel.validate.validate_unit` (which runs `skel.derive.derive_unit` inside
   it) over the assembled candidate rows with all four frozen layers attached,
   split hard/soft exactly like the Phase 5-8 drivers do (`tag` -> soft) — a
   unit passes only at **0 hard / 0 soft**, the same standard the committed
   gold artifacts meet corpus-wide.
3. **Content-hash verification** via `dante_corpus.hashes.canto_hashes`: the
   bytes about to be committed are digested first; after `write_skel` lands
   them, the recomputed `skel` hash must equal that digest — proving the file
   on disk is byte-for-byte the payload the gates validated. A mismatch rolls
   the artifact back to its previous bytes.

Two gold disciplines, as everywhere in the extractor:

- **Execution** (`reconstruct_canto`, `commit`) never opens a gold artifact:
  `CantoLayers` loads L1-L4 + the case annex only. Gates are intrinsic.
- **Evaluation** (`--verify-gold`) reads gold operator-side exactly like
  `runner/benchmark.py` to compare accepted rows against gold keys. It never
  influences gating or writes.

**Module layout (S7.2).** This file is the pipeline: the canto loop
(`reconstruct_canto`), gate 3 (`commit`) and the CLI (`main`). Everything it
drives sits in sibling modules, each importable on its own and each named for
the one responsibility it holds:

| Module | Holds |
|---|---|
| `layers.py` | `CantoLayers` + gates 1-2 (`build_rows`, `validate_rows`) |
| `outcome.py` | `UnitOutcome`, `CantoReconstruction`, unit-level resume |
| `artifact.py` | `render_tsv` + `TsvArtifact` — the durable artifact |
| `fixrun.py` | the Stage-6 `--fix` machinery (plan, verdict, salvage, revert) |
| `goldeval.py` | the evaluation face — **the only module that opens gold** |
| `report.py` | `ReconstructReport` + `load_log` |

That last row is why the split is more than tidying: the execution and commit
faces now import nothing from the module that reads gold, so Standing Invariant
§4 item 1's boundary is a file boundary rather than a comment. The public names
this module exported before the split are re-exported here unchanged.

Commits are **canto-atomic**: a canto is written only when *every* parse unit
passes all gates, so an artifact is always wholly checker-clean — never a mix
of derived and previously-frozen units. Writes additionally require the
explicit `--write` flag: `skel/` is protected gold (harness/PLAN.md §3), so
the default run reconstructs, verifies, and reports without touching disk
(`--dry-run` is accepted as the explicit spelling of that default).

CLI (LLM-in-the-loop when agent fallback runs — operator-run only):

    uv run python -m harness.extractor.reconstruct --canticle inferno --canto 1 --dry-run
    uv run python -m harness.extractor.reconstruct --all --verify-gold [--write]

Observability follows ARCHITECTURE.md §4-§6 scaled to a batch job: stderr
progress per phase and per canto, a streaming JSONL `--log` (`unit` record per
parse unit, optional `gold` records under `--verify-gold`, one `canto_complete`
record per finished canto, `summary` record last — the completion marker).
When Rich is available a `runner.statusline.HarnessStatusLine` bar names the
running position the way the `skel/` drivers do — Canticle Canto Line: one bar
per canto, labeled `{canticle} {canto}`, its numerator walking that canto's
Dante lines as each parse unit starts — while the separators keep whole-run
`[index/total]` canto positions. Every human-facing line routes through the
bar's console stream, and the live fallback's llm7shi sink shares that console
so streamed model output coexists with the bar; auto-retried API backoffs are
counted per canto through the stream's `wait_retry` hook (`api_retries` /
`api_retry_seconds`) and rolled into the summary, and each `canto_complete`
record carries the canto's `elapsed_seconds` (everything it cost:
reconstruction, gates, gold comparison, commit) whose sum is the run's
`wall_clock_seconds` — the benchmark's no-timestamp-span discipline, so idle
gaps between resumed attempts never count. The same `--log` also
carries the request-level cost records: the live fallback appends one JSONL
pair per backend LLM call (`llm_request` before, `llm_response` after:
timestamp, model, unit coordinates, transcript position, attempt,
context/new/output sizes in UTF-8 bytes, duration). The log is **append-only
and never read back** — it is a debug record, so a resumed run's aggregates
cover that attempt alone.

Resume runs off the artifact instead (`--tsv`, `TsvArtifact`, `../stages/05.md`
record S5.5). The canto's gold-format TSV is written **unit by unit as units
settle** (`emit_unit`), so a kill mid-canto leaves every finished unit on
disk; the next run reads the file back, treats every unit whose lines are all
present as settled, and re-runs only the rest — a canto killed partway through
a live-fallback run never pays for its already-settled units twice. Settled
units still go through the gates (deterministic and free), so their verdicts
are measured on the bytes on disk rather than trusted from a log.

That also makes the artifact the repair surface: **delete the lines of a
stretch you want reconsidered and re-run**, and just that unit regenerates. A
gap in the middle cannot be appended around, so the file is rewritten whole
in line order whenever one exists — the streamed output stays byte-identical
to a single-pass `render_tsv` either way.

Deterministic tests inject stub fallbacks; nothing in the test suite touches a
model.
"""

from __future__ import annotations

import argparse
import contextlib
import dataclasses
import hashlib
import json
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, TextIO

from dante_corpus import api
from dante_corpus.skel.models import SkelRow

from harness.extractor import fixlevel
from harness.extractor.artifact import TsvArtifact, render_tsv
from harness.extractor.fixrun import (
    FixPlan,
    Span,
    fix_diagnosis,
    fix_summary_line,
    fix_verdict,
    plan_fix,
    refusal_note,
    revert_outcome,
    row_delta,
    salvage_outcome,
    salvage_rows,
)
from harness.extractor.goldeval import GoldFace, GoldReport, verify_against_gold
from harness.extractor.hybrid_engine import (
    DEFAULT_EVAL_CANTICLES,
    AgentFallback,
    HybridEngine,
    RoutePolicy,
    agent_fallback,
    load_lexicon_json,
    load_rules_json,
    mine_artifacts,
)
from harness.extractor.layers import (
    SAMPLE_VIOLATIONS,
    CantoLayers,
    RowKey,
    build_rows,
    split_violations,
    validate_rows,
)
from harness.extractor.outcome import (
    CantoReconstruction,
    UnitOutcome,
    final_validation_errors,
    replay_unit_outcome,
)
from harness.extractor.report import ReconstructReport, load_log
from harness.runner.prompts import skill_digest
from harness.runner.statusline import HarnessStatusLine
from harness.toolcall import DEFAULT_RESULT_CHARS
from harness.toolcall.loop import progress_separator

__all__ = [
    "SAMPLE_VIOLATIONS",
    "CantoLayers",
    "CantoReconstruction",
    "GoldReport",
    "ReconstructReport",
    "TsvArtifact",
    "UnitOutcome",
    "build_rows",
    "commit",
    "load_log",
    "main",
    "reconstruct_canto",
    "render_tsv",
    "split_violations",
]

# Gate 2 under the name it carried while it lived in this module — call sites
# and tests that reach for it through the pipeline keep working after the split.
_validate_rows = validate_rows


def reconstruct_canto(
    engine: HybridEngine,
    canticle: str,
    canto: int,
    *,
    fallback: AgentFallback | None = None,
    policy: RoutePolicy | None = None,
    progress_stream: TextIO | None = sys.stderr,
    status_line=None,
    settled_units: dict[tuple[int, int], dict[int, list[SkelRow]]] | None = None,
    fix_spans: set[Span] | None = None,
    emit_unit: Callable[[UnitOutcome], None] | None = None,
) -> CantoReconstruction:
    """Drive the hybrid engine over every parse unit of one canto, gated.

    Execution face: loads frozen L1-L4 only; gold is never touched. Each unit
    runs `engine.run_unit` (the live `fallback` callable when given), its
    accepted rows are anchored on Layer 1 (gate 1), and the unit is verified
    through `validate_unit` with all layers attached (gate 2). `status_line`,
    when given (a `runner.statusline.HarnessStatusLine`), owns the display the
    way the `skel/` drivers do: a bar labeled `{canticle} {canto}` counting the
    canto's lines, advanced to each unit's first line, with the per-unit
    progress lines routed through its console stream so they coexist with it.

    `emit_unit`, when given, is called with each freshly computed outcome the
    moment it settles — before the next unit starts. This is §5's durability
    seam: the caller streams the unit's records to disk here, so a kill
    mid-canto leaves every already-settled unit on disk for unit-level resume
    instead of losing them all to a post-canto flush. Replayed units are never
    passed (their records already sit in the caller's log from the prior
    attempt).

    `settled_units`, when given, maps `(line_start, line_end)` to the rows a
    previous attempt already wrote to the canto's TSV: unit-level resume off
    the artifact itself (`TsvArtifact.settled`). Matching units are rebuilt
    from those rows (`replay_unit_outcome`, gates re-run) instead of
    re-running `engine.run_unit` — the caller must not re-emit them, since the
    artifact already holds them.
    """
    stream = status_line.stream if status_line is not None else progress_stream
    layers = CantoLayers.load(canticle, canto)
    recon = CantoReconstruction(
        canticle=canticle, canto=canto, nos=list(layers.nos)
    )
    units = layers.units()
    # Skel-driver display (`driver_build._build_canto`): the bar's label names
    # Canticle Canto and its numerator walks the canto's Dante lines as each
    # parse unit starts; whole-run `[i/N]` positions stay with the separators.
    bar = (
        status_line.progress(len(layers.nos), label=f"{canticle} {canto}")
        if status_line is not None
        else contextlib.nullcontext()
    )
    with bar as prog:
        for pos, group in enumerate(units, start=1):
            if prog is not None:
                prog.update(group[0])
            if stream is not None and pos % 5 == 0:
                print(
                    f"[reconstruct] {canticle} {canto} units {pos}/{len(units)}",
                    file=stream,
                    flush=True,
                )
            line_start, line_end = group[0], group[-1]
            settled = (
                settled_units.get((line_start, line_end)) if settled_units else None
            )
            if settled is not None:
                recon.outcomes.append(
                    replay_unit_outcome(settled, layers, group)
                )
                continue
            started = time.monotonic()
            # A unit reopened for repair must reach the model: the fast path
            # would answer it with `derive_unit`'s own rows, clearing the class
            # by definition and measuring nothing (`../stages/06.md`).
            unit_policy = policy
            if fix_spans and (line_start, line_end) in fix_spans:
                base = policy if policy is not None else RoutePolicy()
                unit_policy = dataclasses.replace(base, force_fallback=True)
            result = engine.run_unit(
                canticle=canticle,
                canto=canto,
                line_start=line_start,
                line_end=line_end,
                policy=unit_policy,
                fallback=fallback,
            )
            elapsed = time.monotonic() - started
            rows, assertions = build_rows(
                result.row_keys, layers, line_start, line_end
            )
            unit_rows = {no: rows.get(no, []) for no in group}
            hard, soft = validate_rows(layers, group, unit_rows)
            fallback_seconds: float | None = None
            agent_result = getattr(result, "agent_result", None)
            turn_seconds = getattr(agent_result, "turn_seconds", None)
            if result.fallback_ran and turn_seconds is not None:
                fallback_seconds = sum(turn_seconds)
            elif result.fallback_ran:
                fallback_seconds = elapsed
            outcome = UnitOutcome(
                unit={
                    "canticle": canticle,
                    "canto": canto,
                    "line_start": line_start,
                    "line_end": line_end,
                },
                route=result.decision.route,
                reason=result.decision.reason,
                origin=result.origin,
                fallback_ran=result.fallback_ran,
                row_keys=frozenset(result.row_keys),
                rows=unit_rows,
                token_assertions=assertions,
                hard=hard,
                soft=soft,
                fallback_seconds=fallback_seconds,
                final_submission_valid=getattr(
                    result, "final_submission_valid", None
                ),
                invalid_nudges=getattr(agent_result, "invalid_nudges", None),
                final_validation_errors=final_validation_errors(agent_result),
            )
            recon.outcomes.append(outcome)
            # §5 durability seam: hand the settled outcome to the caller while
            # the canto is still running, so the record is on disk before the
            # next unit's (possibly hours-long) fallback begins.
            if emit_unit is not None:
                emit_unit(outcome)
    return recon


# --- commit (gate 3): canto-atomic write + hash verification -----------------------------


def commit(
    recon: CantoReconstruction,
    *,
    progress_stream: TextIO | None = sys.stderr,
) -> dict:
    """§4.1 gate 3 — write the canto atomically, then verify the hashes.

    Refuses blocked cantos outright (never partial writes). The payload is
    rendered and digested first; `write_skel` lands it; `canto_hashes()` must
    then recompute exactly that digest. Any mismatch rolls the artifact back
    to its previous bytes (or removes a freshly created file). The returned
    record is the commit audit trail: pre/post hashes and the verdict.
    """
    record: dict = {
        "record": "commit",
        "canticle": recon.canticle,
        "canto": recon.canto,
    }
    if not recon.passed:
        record.update(wrote=False, reason="gates_failed")
        return record

    from dante_corpus.hashes import canto_hashes
    from dante_corpus.skel.io import write_skel

    # Resolve the target through the writer's own path resolver, so test
    # redirections and production agree on one file.
    from dante_corpus.skel import io as skel_io

    path = skel_io._artifact_path(recon.canticle, recon.canto)
    merged = recon.rows_by_line()
    lines = [(no, merged.get(no, [])) for no in sorted(recon.nos)]
    payload = render_tsv(lines)
    expected = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    before = canto_hashes(recon.canticle, recon.canto).get("skel")
    old_bytes = path.read_bytes() if path.exists() else None

    write_skel(recon.canticle, recon.canto, lines)
    after = canto_hashes(recon.canticle, recon.canto).get("skel")
    verified = after == expected
    rolled_back = False
    if not verified:
        if progress_stream is not None:
            print(
                f"[reconstruct] hash verification failed for "
                f"{recon.canticle} {recon.canto}; rolling back",
                file=progress_stream,
                flush=True,
            )
        if old_bytes is not None:
            path.write_bytes(old_bytes)
        else:
            with contextlib.suppress(OSError):
                path.unlink()
        rolled_back = True
    record.update(
        wrote=verified,
        reason=None if verified else "hash_mismatch",
        units_passed=sum(o.passed for o in recon.outcomes),
        units_total=len(recon.outcomes),
        before_skel_hash=before,
        expected_digest=expected,
        after_skel_hash=after,
        digest_verified=verified,
        rolled_back=rolled_back,
    )
    return record


# --- CLI ------------------------------------------------------------------------------------


def _retry_snapshot(status_line) -> tuple[int, float] | None:
    """`(count, seconds)` of api-retry backoffs seen so far, or None if untracked.

    Same contract as `runner.benchmark`'s helpers: llm7shi auto-retries 429
    backoffs silently; the status line's stream counts them via `wait_retry`.
    """
    stream = getattr(status_line, "stream", None)
    count = getattr(stream, "api_retries", None)
    if count is None:
        return None
    return count, getattr(stream, "api_retry_seconds", 0.0)


def _retry_delta(
    snapshot: tuple[int, float] | None, status_line
) -> tuple[int, float] | None:
    """Backoff `(count, seconds)` accumulated since `snapshot`; None if untracked."""
    if snapshot is None:
        return None
    now = _retry_snapshot(status_line)
    if now is None:
        return 0, 0.0
    return max(now[0] - snapshot[0], 0), max(now[1] - snapshot[1], 0.0)


def _select_cantos(args) -> list[tuple[str, int]]:
    canticles = args.canticles or list(DEFAULT_EVAL_CANTICLES)
    if args.canto is not None:
        return [(c, args.canto) for c in canticles]
    wanted: list[tuple[str, int]] = []
    for canticle in canticles:
        for number in api.cantos(canticle):
            wanted.append((canticle, number))
    return wanted


def main(argv=None, *, fallback: AgentFallback | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Gated whole-canto reconstruction through the hybrid engine "
            "(harness/extractor PLAN.md milestone 2.4)."
        )
    )
    parser.add_argument(
        "--canticle",
        action="append",
        choices=("inferno", "purgatorio", "paradiso"),
        dest="canticles",
        help="restrict scope to these canticles (default: all)",
    )
    parser.add_argument("--canto", type=int, help="single canto number (with --canticle)")
    parser.add_argument(
        "--all", action="store_true", help="iterate every canto of the selected canticles"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="explicit no-write run (the default; skel/ is protected gold)",
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="commit passing cantos to skel/ (canto-atomic, hash-verified)",
    )
    parser.add_argument(
        "--verify-gold",
        action="store_true",
        help="also compare accepted rows against gold (observational only)",
    )
    parser.add_argument("--rules-in", type=Path)
    parser.add_argument("--lexicon-in", type=Path)
    parser.add_argument(
        "--run-log",
        action="append",
        type=Path,
        dest="run_logs",
        help="input benchmark JSONL log for fresh mining (repeatable; defaults "
        "to the four M1.4/re-run logs under harness/)",
    )
    parser.add_argument("--min-support", type=int, default=None)
    parser.add_argument(
        "--model",
        default=None,
        help="model for the Stage-1 agent fallback (default: runner default)",
    )
    parser.add_argument("--max-turns", type=int, default=None)
    parser.add_argument(
        "--max-invalid-nudges", type=int, default=1,
        help="resumes offered when a session ends on rows its own gate "
             "rejected while turns remain (default 1; 0 restores the "
             "measure-as-is behaviour the Stage-1 benchmark keeps)",
    )
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument(
        "--payload-tier",
        choices=("R1", "S1"),
        default="R1",
        help="read_unit payload rendering: positional rows + legend (R1, "
        "default) or sparse named dicts (S1 fallback tier)",
    )
    parser.add_argument(
        "--min-send-interval",
        type=float,
        default=0.0,
        help="minimum seconds between this stream's backend sends (0 = off, "
        "the default; pass e.g. 35 to break the fast-response/big-send "
        "pairing, ../stages/03.md §2.C)",
    )
    parser.add_argument(
        "--max-length",
        type=int,
        default=6000,
        help="generation-side runaway cap in answer-text characters per call "
        "(llm7shi max_length: crossing it fails the turn and the Client "
        "regenerates; thinking is not counted; 0 disables; default 6000, "
        "../stages/03.md record S3.10)",
    )
    parser.add_argument(
        "--tool-result-chars",
        type=int,
        default=DEFAULT_RESULT_CHARS,
        help="echo each tool call's returned block to the console, truncated to "
        "this many payload characters (0 = off). The model's own turn streams "
        "already; this is the other half of the exchange — the validator's "
        "verdict and its errors — made watchable (PLAN.md §4 item 5)",
    )
    parser.add_argument(
        "--log",
        type=Path,
        help="streaming JSONL debug log: unit/gold/canto_complete records, "
        "summary last, plus llm_request/llm_response records from the live "
        "fallback. Append-only — never read back; resume state is the TSV",
    )
    parser.add_argument(
        "--tsv",
        type=Path,
        help="gold-format TSV for the selected canto, written unit by unit as "
        "units settle and read back on the next run to resume: units already "
        "present are not re-run. Single-canto only (needs --canticle/--canto)",
    )
    parser.add_argument(
        "--fix",
        metavar="LEVEL",
        help="Stage-6 soft repair: reopen the units of the --tsv artifact that "
        "carry a level-LEVEL soft finding, show the session their recorded rows "
        "and the invariants those break, and replace the rows with what it "
        f"re-solves (levels 1..{fixlevel.MAX_LEVEL}, cumulative, or 'max' for "
        "every level defined). A unit whose answer is not hard-clean, does not "
        "reduce the level's findings, or introduces a new violation class is "
        "retried at position scope — the answer taken only at the rows the "
        "findings name — and keeps its recorded rows if that fails the same "
        "test",
    )
    parser.add_argument(
        "--started-at",
        type=float,
        default=None,
        help="unix timestamp (seconds) the enclosing run started, e.g. "
        "harness/recon/Makefile's $STARTED_AT: shown as the status bar's "
        "label-side elapsed time. Needed because that Makefile launches one "
        "reconstruct.py process per canto, so this process's own clock alone "
        "can only show that canto's elapsed time, never the run's cumulative "
        "one — omit for a bare single-canto invocation",
    )
    args = parser.parse_args(argv)

    if args.fix is not None:
        if args.tsv is None:
            parser.error("--fix repairs an existing artifact: pass --tsv")
        try:
            args.fix = fixlevel.resolve_level(args.fix)
        except ValueError as exc:
            parser.error(f"--fix: {exc}")
    if args.canto is not None and not args.canticles:
        parser.error("--canto needs an explicit --canticle")
    if (args.canto is None) == (not args.all):
        parser.error("select exactly one of --canto N or --all")
    # One TSV is one canto's artifact; a multi-canto run would interleave
    # unrelated line numbers into it.
    if args.tsv is not None and args.canto is None:
        parser.error("--tsv needs a single canto (--canticle C --canto N)")

    # §4 optional Rich bar: created up front so every human-facing line and
    # the live fallback's model stream can share its console; without the
    # extra this stays None and plain stderr lines keep the run watchable.
    status_line = HarnessStatusLine() if HarnessStatusLine is not None else None
    if status_line is not None and args.started_at is not None:
        status_line.run_started_at = args.started_at
    ui_stream = status_line.stream if status_line is not None else None

    if args.rules_in and args.lexicon_in:
        rules = load_rules_json(args.rules_in)
        entries = load_lexicon_json(args.lexicon_in)
        print(
            f"reconstruct: loaded {len(rules)} rules + {len(entries)} frames "
            f"from artifacts"
        )
    else:
        print(
            "[reconstruct] regenerating artifacts from run logs...",
            file=ui_stream if ui_stream is not None else sys.stderr,
            flush=True,
        )
        kwargs = {}
        if args.min_support is not None:
            kwargs["min_support"] = args.min_support
        bundle = mine_artifacts(args.run_logs, **kwargs)
        rules, entries = bundle.rules, bundle.entries
    engine = HybridEngine(rules, entries)

    wanted = _select_cantos(args)
    total = len(wanted)
    report = ReconstructReport()

    # Resume state is the artifact: units already written to the TSV are not
    # re-run (`TsvArtifact`). The log plays no part — it is an append-only
    # debug record now, never read back, so a resumed run's report aggregate
    # covers this attempt only. Units resumed from the TSV are re-validated
    # and counted with `route="tsv"`, so the artifact's own verdict is always
    # measured rather than carried over from a prior attempt's log.
    artifact = TsvArtifact(args.tsv) if args.tsv else None
    settled_units: dict[tuple[int, int], dict[int, list[SkelRow]]] = {}
    fix_plan: FixPlan | None = None
    if artifact is not None:
        artifact.load()
        fix_layers = CantoLayers.load(*wanted[0])
        settled_units = artifact.settled(fix_layers.units())
        if settled_units:
            print(
                f"resume: {len(settled_units)} unit(s) already settled in "
                f"{args.tsv}"
            )
        if args.fix is not None:
            # Selection: settled units carrying a finding of this level are
            # unsettled again, so the ordinary unit loop re-runs them — with
            # their recorded rows kept for the acceptance test below. The
            # replacement happens through `write_unit`, which needs the rewrite
            # path once a unit in the middle of the file is overwritten.
            fix_plan = plan_fix(fix_layers, settled_units, args.fix)
            for span in fix_plan.prior:
                settled_units.pop(span, None)
            artifact.reopen()
            print(
                f"fix level {args.fix}: {len(fix_plan.prior)} unit(s) reopened, "
                f"{fix_plan.findings} finding(s) of "
                f"{', '.join(c.name for c in fixlevel.classes_for(args.fix))}"
            )

    header = (
        f"reconstruct: {'WRITE' if args.write else 'dry-run'} "
        f"(gates: token stream, 0 hard / 0 soft, content hash)"
        f"{', verify-gold' if args.verify_gold else ''}; "
        f"{len(wanted)} canto(s) selected"
    )
    print(header)

    # Stage-3 configuration line (../stages/03.md §4 item 6): payload tier + pacing
    # are live-run facts the operator must see announced before the hours run.
    if args.max_length < 0:
        parser.error("--max-length must be >= 0 (0 disables the cap)")
    if args.tool_result_chars < 0:
        parser.error("--tool-result-chars must be >= 0 (0 disables the echo)")
    max_length = args.max_length or None
    print(
        f"reconstruct: transcripts verbatim, "
        f"payload tier {args.payload_tier}; pacing: min-send-interval "
        f"{args.min_send_interval:g}s; "
        f"max-length "
        f"{'off' if max_length is None else f'{max_length} chars'}"
    )

    # One streaming log carries everything: unit/gold/canto_complete/summary
    # records plus the live fallback's llm_request/llm_response records (the
    # canto-scoped cost trail; resume compaction keeps them for completed
    # cantos exactly like the unit records). Opened after compaction — the
    # rewrite swaps the file, so an earlier handle would append into limbo.
    sink = open(args.log, "a", encoding="utf-8") if args.log else None
    if fallback is None:
        fallback_kwargs = {
            "model": args.model,
            "payload_tier": args.payload_tier,
            "min_send_interval": args.min_send_interval,
            "max_length": max_length,
            "result_chars": args.tool_result_chars,
            # A production run keeps the session's last submission whatever its
            # verdict, so ending early on rows the session itself rejected puts
            # them in the artifact. Nudge instead (S6.6). The benchmark keeps
            # the opposite default: there, the give-up is the measurement.
            "max_invalid_nudges": args.max_invalid_nudges,
        }
        if args.max_turns is not None:
            fallback_kwargs["max_turns"] = args.max_turns
        if fix_plan is not None and fix_plan:
            # The session sees two extra things under --fix, and only these two:
            # the level's own bar added to its gate, and the unit's recorded rows
            # with the invariants they break. No derived label crosses over
            # (`../stages/06.md`; `../stages/05.md` S5.5 for the line being crossed).
            fallback_kwargs["fix_level"] = args.fix
            fallback_kwargs["revision_for"] = (
                lambda canticle, canto, line_start, line_end, _plan=fix_plan: (
                    _plan.revisions.get((line_start, line_end))
                )
            )
        fallback = agent_fallback(
            verbose=args.verbose,
            file=status_line.stream if status_line is not None else None,
            request_log=sink,
            **fallback_kwargs,
        )
    try:
        for index, (canticle, canto) in enumerate(wanted, start=1):
            progress_separator(
                f"{canticle} {canto}", index, total, stream=ui_stream
            )
            retry_before = _retry_snapshot(status_line)
            canto_started = time.monotonic()
            # §5 durability seam: settled units stream out as they settle, so
            # a mid-canto kill keeps every finished unit on disk and the next
            # attempt resumes unit-by-unit instead of re-running (and
            # re-costing, for the live fallback) the whole canto.
            gold_face = GoldFace() if args.verify_gold else None
            fix_stats: Counter[str] = Counter()

            def settle(outcome: UnitOutcome) -> None:
                span = (
                    outcome.unit["line_start"], outcome.unit["line_end"]
                )
                fix_verdict_reason: str | None = None
                unit_verdict: str | None = None
                diagnosis: dict | None = None
                if fix_plan is not None and span in fix_plan.prior:
                    # Acceptance, in two scopes. The whole unit first: that is
                    # the answer the session stands behind, and where it passes
                    # it is taken entire. Where it does not, the same test runs
                    # again over a position-scoped splice — the answer at the
                    # rows the findings name, the record everywhere else — so a
                    # repair the level itself calls correct is not thrown away
                    # with the rest of the unit. Only if that fails too do the
                    # recorded rows go back verbatim.
                    level = fix_plan.level
                    before = fix_plan.before[span]
                    submitted = outcome.rows
                    accepted, fix_verdict_reason = fix_verdict(
                        before, outcome.hard, outcome.soft, level
                    )
                    if not accepted:
                        # S6.7: the whole-unit answer was refused, so record
                        # what it actually proposed before it is spliced or
                        # thrown away. Decided already; this only reports.
                        diagnosis = fix_diagnosis(
                            fix_plan.prior[span], submitted, before,
                            outcome.hard, outcome.soft, level,
                        )
                        candidate = salvage_outcome(outcome, fix_plan, span)
                        if candidate is None:
                            diagnosis["salvage"] = (
                                "token_assertions"
                                if outcome.token_assertions
                                else "no_governed_rows"
                            )
                        else:
                            salvaged, salvage_reason = fix_verdict(
                                before, candidate.hard, candidate.soft, level
                            )
                            diagnosis["salvage"] = salvage_reason
                            if salvaged:
                                accepted = True
                                unit_verdict = fix_verdict_reason
                                fix_verdict_reason = "salvaged"
                                outcome = candidate
                    if accepted:
                        for key, value in row_delta(
                            fix_plan.prior[span], outcome.rows
                        ).items():
                            fix_stats[key] += value
                    else:
                        outcome = revert_outcome(outcome, fix_plan, span)
                    fix_stats["units"] += 1
                    fix_stats[f"verdict:{fix_verdict_reason.split(':')[0]}"] += 1
                    fix_stats["findings_before"] += len(
                        fixlevel.select(before, level)
                    )
                    fix_stats["findings_after"] += len(
                        fixlevel.select(outcome.soft, level)
                    )
                    fix_stats["soft_before"] += len(before)
                    fix_stats["soft_after"] += len(outcome.soft)
                    print(
                        f"[fix] {canticle} {canto} lines {span[0]}-{span[1]}: "
                        f"{fix_verdict_reason}"
                        + (f" (unit: {unit_verdict})" if unit_verdict else "")
                        + refusal_note(diagnosis),
                        file=ui_stream if ui_stream is not None else sys.stderr,
                        flush=True,
                    )
                record = outcome.to_dict()
                if fix_verdict_reason is not None:
                    record["fix"] = {
                        "level": fix_plan.level, "verdict": fix_verdict_reason,
                    }
                    if unit_verdict is not None:
                        # What the whole-unit answer was refused for, kept on
                        # record: the salvage rate is only readable against it.
                        record["fix"]["unit_verdict"] = unit_verdict
                    # What the rows on disk became, under every verdict (a
                    # reverted unit reports zeros), so an accepted unit's
                    # off-brief reach is readable without a git diff.
                    record["fix"]["delta"] = row_delta(
                        fix_plan.prior[span], outcome.rows
                    )
                    if diagnosis is not None:
                        # Only where the whole-unit answer was refused, and
                        # about that answer rather than about what was kept.
                        record["fix"]["refused"] = diagnosis
                report.add_unit(record)
                if artifact is not None:
                    # The artifact lands first: it, not the log, is what the
                    # next run resumes from, so it must never be the thing
                    # missing after a kill between the two writes.
                    artifact.write_unit(
                        sorted(outcome.rows), outcome.rows
                    )
                if sink is not None:
                    sink.write(json.dumps(record, ensure_ascii=False) + "\n")
                    sink.flush()  # §5: every completed unit is durable at once
                if gold_face is not None:
                    gold_record = gold_face.observe(outcome)
                    report.add_gold(gold_record)
                    if sink is not None:
                        sink.write(
                            json.dumps(gold_record, ensure_ascii=False) + "\n"
                        )
                        sink.flush()

            recon = reconstruct_canto(
                engine, canticle, canto,
                fallback=fallback, status_line=status_line,
                settled_units=settled_units,
                fix_spans=set(fix_plan.prior) if fix_plan else None,
                emit_unit=settle,
            )
            retries = _retry_delta(retry_before, status_line)
            # Units resumed from the TSV never reach `emit_unit` — the artifact
            # already holds their rows, and re-writing them would duplicate
            # lines. They still belong in this run's aggregates, so they are
            # folded in here, from the re-validated outcome rather than from
            # any prior attempt's record. They are deliberately not appended to
            # the log: the log records what this run actually did.
            for outcome in recon.outcomes:
                if not outcome.replayed:
                    continue
                report.add_unit(outcome.to_dict())
                if gold_face is not None:
                    report.add_gold(gold_face.observe(outcome))
            complete: dict = {
                "record": "canto_complete",
                "canticle": canticle,
                "canto": canto,
                "units": len(recon.outcomes),
                "passed": recon.passed,
                # Which wording the canto ran under (Standing Invariant §6). The
                # skill's files are the session semantics; recording their digest
                # canto by canto is how a later reader tells two runs apart, and
                # how a mid-run change would show up at all.
                "skill_digest": skill_digest(),
            }
            if retries is not None:
                complete["api_retries"] = retries[0]
                complete["api_retry_seconds"] = round(retries[1], 1)
            if fix_plan is not None and fix_stats:
                # Discipline 6 (`../PLAN.md`): a reduction is reported by its
                # mechanism, not by its delta — how many units were reopened,
                # how many answers were kept, and what happened to the rows.
                complete["fix"] = {"level": fix_plan.level, **dict(fix_stats)}
                print(fix_summary_line(fix_plan.level, fix_stats), file=ui_stream
                      if ui_stream is not None else sys.stderr, flush=True)
            if args.write:
                commit_record = commit(recon)
                complete["commit"] = commit_record
                if sink is not None:
                    sink.write(json.dumps(commit_record, ensure_ascii=False) + "\n")
                    sink.flush()
            # Wall clock of everything this canto cost (reconstruction,
            # verification, gold comparison, commit) — sums into the summary
            # and folds across resumed attempts via the record.
            complete["elapsed_seconds"] = round(time.monotonic() - canto_started, 1)
            report.add_canto_complete(complete)
            if sink is not None:
                sink.write(json.dumps(complete, ensure_ascii=False) + "\n")
                sink.flush()
        if sink is not None:
            summary = {
                "record": "summary",
                "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                **report.metrics(),
            }
            sink.write(json.dumps(summary, ensure_ascii=False) + "\n")
            sink.flush()
    finally:
        if sink is not None:
            sink.close()

    if args.log:
        print(f"records written to {args.log}")
    print(report.summary())
    return 0


if __name__ == "__main__":
    sys.exit(main())
