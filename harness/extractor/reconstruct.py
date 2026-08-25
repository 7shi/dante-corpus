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
   split hard/soft exactly like the Phase 5–8 drivers do (`tag` -> soft) — a
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
context/new/output sizes in UTF-8 bytes, duration). They are canto-scoped
like every other record — never replayed into aggregates, and resume
compaction keeps them for both completed and in-progress cantos.
Unlike the deterministic miners this CLI **resumes** rather than truncates
(live fallback makes attempts hours long and worth keeping), down to the
**parse unit**, not just the canto: completed cantos reload from an existing
log and are skipped outright, and a canto interrupted mid-run reloads its
already-logged `unit` records (each one carries its accepted `row_keys`) and
replays them without re-invoking the fallback, resuming only the units that
never finished — a canto killed partway through a live-fallback run never
pays for its already-settled units twice. The log is compacted atomically
before appending: only the (now superseded) `summary` record is ever
dropped; every `unit`/`gold`/`commit`/`canto_complete`/`llm_request`/
`llm_response` record survives so a subsequent resume can rebuild on top of
it, and a unit is never re-emitted once replayed so nothing double-counts.

Deterministic tests inject stub fallbacks; nothing in the test suite touches a
model.
"""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import json
import os
import sys
import tempfile
import time
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator, TextIO

from dante_corpus import api, case as case_layer, dep as dep_layer, morph as morph_layer, np as np_layer
from dante_corpus.morph import Violation
from dante_corpus.skel.models import SkelRow, _row_sort_key
from dante_corpus.skel.validate import validate_unit

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
from harness.runner.statusline import HarnessStatusLine
from harness.toolcall.loop import progress_separator

__all__ = [
    "SAMPLE_VIOLATIONS",
    "CantoLayers",
    "CantoReconstruction",
    "GoldReport",
    "ReconstructReport",
    "UnitOutcome",
    "build_rows",
    "commit",
    "compact_log",
    "completed_cantos",
    "load_log",
    "main",
    "prepare_resume",
    "reconstruct_canto",
    "render_tsv",
    "split_violations",
]

# Per-unit violation details kept in log records; the summary carries the full
# kind histogram, so samples only need to seed triage.
SAMPLE_VIOLATIONS = 10

RowKey = tuple[int, int, str, int, int]

_TSV_HEADER = ("line", "token", "word", "role", "arg_line", "arg_token")


# --- frozen-layer bundle (execution face: no gold anywhere) ------------------------------


@dataclass
class CantoLayers:
    """Everything the execution face may read for one canto: L1-L4 + case annex."""

    canticle: str
    canto: int
    nos: list[int]
    texts: list[str]
    tokens: dict[int, list[str]]
    morph_rows: dict[int, tuple]
    np_rows: dict[int, tuple]
    dep_rows: dict[int, tuple]
    case_rows: dict[int, tuple]

    @property
    def text_by_no(self) -> dict[int, str]:
        return dict(zip(self.nos, self.texts))

    @classmethod
    def load(cls, canticle: str, canto: int) -> "CantoLayers":
        data = api.canto(canticle, canto)
        lines = data.lines()
        return cls(
            canticle=canticle,
            canto=canto,
            nos=[line.no for line in lines],
            texts=[line.text for line in lines],
            tokens={line.no: list(line.tokens) for line in lines},
            morph_rows=morph_layer.load_morph(canticle, canto),
            np_rows=np_layer.load_np(canticle, canto),
            dep_rows=dep_layer.load_dep(canticle, canto),
            case_rows=case_layer.load_case(canticle, canto),
        )

    def units(self) -> list[list[int]]:
        """Parse-unit line groups (`dep.sentence_groups`) covering every line once."""
        return [
            list(group)
            for group in dep_layer.sentence_groups(self.nos, self.texts)
        ]


def split_violations(
    violations: list[Violation],
) -> tuple[list[Violation], list[Violation]]:
    """`(hard, soft)` — the drivers' split (`driver_ui._classify_violations`)."""
    hard: list[Violation] = []
    soft: list[Violation] = []
    for v in violations:
        (soft if v.kind == "tag" else hard).append(v)
    return hard, soft


def build_rows(
    keys: set[RowKey],
    layers: CantoLayers,
    line_start: int,
    line_end: int,
) -> tuple[dict[int, list[SkelRow]], list[str]]:
    """§4.1 gate 1 — normalize accepted row keys onto the Layer-1 token stream.

    Every predicate/argument position must index the canto's alpha-token
    stream inside the unit's bounds; each row's word anchor is taken verbatim
    from that stream, so token-for-token alignment holds by construction and
    is asserted after construction. Bad positions are reported (and dropped),
    never raised.
    """
    errors: list[str] = []
    by_line: dict[int, list[SkelRow]] = {}
    for key in sorted(keys):
        pline, ptok, role, aline, atok = key
        if not line_start <= pline <= line_end:
            errors.append(f"predicate {pline}.{ptok} outside unit bounds")
            continue
        ptoks = layers.tokens.get(pline, [])
        if not 1 <= ptok <= len(ptoks):
            errors.append(
                f"predicate {pline}.{ptok} outside the Layer-1 token stream"
            )
            continue
        if (aline, atok) != (0, 0):
            if not line_start <= aline <= line_end:
                errors.append(f"argument {aline}.{atok} outside unit bounds")
                continue
            atoks = layers.tokens.get(aline, [])
            if not 1 <= atok <= len(atoks):
                errors.append(
                    f"argument {aline}.{atok} outside the Layer-1 token stream"
                )
                continue
        word = ptoks[ptok - 1]
        by_line.setdefault(pline, []).append(
            SkelRow(line=pline, token=ptok, word=word, role=role,
                    arg_line=aline, arg_token=atok)
        )
    for rows in by_line.values():
        rows.sort(key=_row_sort_key)
    return by_line, errors


def _violation_record(v: Violation) -> dict:
    return {"line": v.line, "kind": v.kind, "detail": v.detail}


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
    # Unit-level resume (§ replay): a unit rebuilt from a previously logged
    # `unit` record instead of re-running `engine.run_unit`/`validate_unit`.
    # `passed` then trusts the logged verdict (no violation objects survive
    # the log), and the caller must not re-emit it to the sink or aggregates
    # — it is already there from the prior attempt.
    replayed: bool = False
    passed_override: bool | None = None

    @property
    def passed(self) -> bool:
        """§4.1 gates 1+2: clean assertions AND 0 hard / 0 soft violations."""
        if self.passed_override is not None:
            return self.passed_override
        return not self.token_assertions and not self.hard and not self.soft

    def to_dict(self) -> dict:
        kinds = Counter(v.kind for v in self.hard + self.soft)
        sample = [
            _violation_record(v)
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
            "fallback_seconds": (
                None if self.fallback_seconds is None
                else round(self.fallback_seconds, 1)
            ),
        }


def _replay_unit_outcome(
    record: dict, layers: "CantoLayers", group: list[int]
) -> UnitOutcome:
    """Rebuild a `UnitOutcome` from a previously logged `unit` record.

    Unit-level resume: the row keys are the only thing the log needs to carry
    for a full replay (rows re-anchor deterministically via `build_rows`;
    the pass/fail verdict is trusted from the record rather than
    re-validated, since no `Violation` objects survive the log).
    """
    line_start, line_end = group[0], group[-1]
    row_keys = frozenset(tuple(key) for key in record.get("row_keys", []))
    rows, assertions = build_rows(row_keys, layers, line_start, line_end)
    unit_rows = {no: rows.get(no, []) for no in group}
    return UnitOutcome(
        unit={
            "canticle": record["canticle"],
            "canto": record["canto"],
            "line_start": line_start,
            "line_end": line_end,
        },
        route=record.get("route", "?"),
        reason=record.get("reason", "?"),
        origin=record.get("origin", "?"),
        fallback_ran=bool(record.get("fallback_ran")),
        row_keys=row_keys,
        rows=unit_rows,
        token_assertions=assertions,
        hard=[],
        soft=[],
        fallback_seconds=record.get("fallback_seconds"),
        replayed=True,
        passed_override=bool(record.get("passed")),
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


def reconstruct_canto(
    engine: HybridEngine,
    canticle: str,
    canto: int,
    *,
    fallback: AgentFallback | None = None,
    policy: RoutePolicy | None = None,
    progress_stream: TextIO | None = sys.stderr,
    status_line=None,
    skip_units: dict[tuple[int, int], dict] | None = None,
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

    `skip_units`, when given, maps `(line_start, line_end)` to a previously
    logged `unit` record: unit-level resume for a canto that was interrupted
    mid-run. Matching units are rebuilt from the log (`_replay_unit_outcome`)
    instead of re-running `engine.run_unit` — the caller (`main`) must not
    re-emit them to the sink or aggregates, since the prior attempt already
    did.
    """
    stream = status_line.stream if status_line is not None else progress_stream
    layers = CantoLayers.load(canticle, canto)
    recon = CantoReconstruction(
        canticle=canticle, canto=canto, nos=list(layers.nos)
    )
    text_by_no = layers.text_by_no
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
            skip_record = (
                skip_units.get((line_start, line_end)) if skip_units else None
            )
            if skip_record is not None:
                recon.outcomes.append(
                    _replay_unit_outcome(skip_record, layers, group)
                )
                continue
            started = time.monotonic()
            result = engine.run_unit(
                canticle=canticle,
                canto=canto,
                line_start=line_start,
                line_end=line_end,
                policy=policy,
                fallback=fallback,
            )
            elapsed = time.monotonic() - started
            rows, assertions = build_rows(
                result.row_keys, layers, line_start, line_end
            )
            unit_rows = {no: rows.get(no, []) for no in group}
            violations = validate_unit(
                group,
                [text_by_no[no] for no in group],
                unit_rows,
                morph_rows=layers.morph_rows,
                np_rows=layers.np_rows,
                dep_rows=layers.dep_rows,
                case_rows=layers.case_rows,
            )
            hard, soft = split_violations(violations)
            fallback_seconds: float | None = None
            agent_result = getattr(result, "agent_result", None)
            turn_seconds = getattr(agent_result, "turn_seconds", None)
            if result.fallback_ran and turn_seconds is not None:
                fallback_seconds = sum(turn_seconds)
            elif result.fallback_ran:
                fallback_seconds = elapsed
            recon.outcomes.append(
                UnitOutcome(
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
                )
            )
    return recon


# --- commit (gate 3): canto-atomic write + hash verification -----------------------------


def render_tsv(lines: list[tuple[int, list[SkelRow]]]) -> str:
    """Byte-exact mirror of `skel.io.write_skel`'s payload for the same input.

    Gate 3 digests the payload *before* writing and compares against the
    recomputed content hash *after* writing, which requires rendering the
    bytes independently of the writer. If `write_skel`'s format ever drifts
    from this mirror the commit fails loudly instead of landing unverified
    bytes — `test_render_tsv_matches_write_skel_bytes` pins the parity.
    """
    out = ["\t".join(_TSV_HEADER)]
    for no, rows in lines:
        if not rows:
            out.append("\t".join((str(no), "0", "", "", "0", "0")))
            continue
        for row in sorted(rows, key=_row_sort_key):
            out.append(
                "\t".join((str(no), str(row.token), row.word, row.role,
                           str(row.arg_line), str(row.arg_token)))
            )
    return "\n".join(out) + "\n"


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


# --- evaluation face: gold comparison (operator-side; reads gold) ------------------------


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


def verify_against_gold(
    recon: CantoReconstruction,
) -> tuple[GoldReport, Iterator[dict]]:
    """Compare every unit's accepted rows against gold (evaluation face).

    Reads the frozen artifacts exactly like `runner/benchmark.py`; purely
    observational — the result never feeds gating or writes.
    """
    from dante_corpus.skel.io import load_skel

    report = GoldReport()
    cache: dict[tuple[str, int], dict] = {}

    def records():
        for outcome in recon.outcomes:
            unit = outcome.unit
            key = (unit["canticle"], unit["canto"])
            if key not in cache:
                cache[key] = load_skel(unit["canticle"], unit["canto"])
            gold_rows = cache[key]
            gold = {
                (row.line, row.token, row.role, row.arg_line, row.arg_token)
                for no in range(unit["line_start"], unit["line_end"] + 1)
                for row in gold_rows.get(no, ())
            }
            counts = report.observe(outcome.row_keys, gold)
            yield {"record": "gold", **unit, **counts}

    return report, records()


# --- aggregate report ---------------------------------------------------------------------


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


# --- streaming JSONL log: resume support ---------------------------------------------------


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


def completed_cantos(records: list[dict]) -> set[tuple[str, int]]:
    """Cantos whose terminal `canto_complete` marker is already on disk."""
    return {
        (record["canticle"], record["canto"])
        for record in records
        if record.get("record") == "canto_complete" and "canticle" in record
    }


def prepare_resume(
    records: list[dict],
    wanted: list[tuple[str, int]],
) -> tuple[list[dict], list[tuple[str, int]], dict[tuple[str, int], dict[tuple[int, int], dict]]]:
    """Split a previous attempt into
    `(records_to_replay, remaining_cantos, pending_units)`.

    Everything belonging to a completed canto replays into the aggregate;
    those cantos are skipped entirely. A canto still in `remaining` may
    nonetheless carry logged `unit` records from an interrupted attempt —
    unit-level resume: `pending_units` maps such a canto to its
    `(line_start, line_end) -> unit record` table so `reconstruct_canto` can
    skip re-running (and re-costing, for the live fallback) units already
    settled, picking up only where the prior attempt broke off.
    """
    done = completed_cantos(records)
    replay: list[dict] = [
        record
        for record in records
        if (record.get("canticle"), record.get("canto")) in done
        and record.get("record") in ("unit", "gold", "commit", "canto_complete")
    ]
    remaining = [canto for canto in wanted if canto not in done]
    remaining_set = set(remaining)
    pending_units: dict[tuple[str, int], dict[tuple[int, int], dict]] = {}
    for record in records:
        if record.get("record") != "unit":
            continue
        key = (record.get("canticle"), record.get("canto"))
        if key not in remaining_set:
            continue
        pending_units.setdefault(key, {})[
            (record.get("line_start"), record.get("line_end"))
        ] = record
    return replay, remaining, pending_units


def compact_log(path: str | Path) -> None:
    """Strip superseded `summary` records from an existing log (atomic replace).

    Every other record survives compaction, including `unit`/`gold` records
    of a canto still in progress: unit-level resume (`prepare_resume`'s
    `pending_units`) needs them on disk to skip already-settled units on the
    next attempt. Only the completion marker is ever stale across attempts —
    a `summary` reflects a prior (possibly now-superseded) run's aggregate —
    so it alone is dropped.
    """
    with open(path, encoding="utf-8") as fh:
        kept = [line for line in fh if _jsonl_record_should_keep(line)]
    directory = os.path.dirname(os.path.abspath(path))
    fd, tmp = tempfile.mkstemp(dir=directory, prefix=".reconstruct-log-", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as dst:
            dst.writelines(kept)
        os.replace(tmp, path)
    except BaseException:
        with contextlib.suppress(OSError):
            os.unlink(tmp)
        raise


def _jsonl_record_should_keep(line: str) -> bool:
    """Compaction predicate: valid JSON, not a (superseded) `summary` record."""
    stripped = line.strip()
    if not stripped:
        return False
    try:
        record = json.loads(stripped)
    except json.JSONDecodeError:
        return False  # torn tail: drop it
    return record.get("record") != "summary"


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
        "pairing, STAGE3.md §2.C)",
    )
    parser.add_argument(
        "--token-bucket",
        type=Path,
        help="shared pacing bucket file (fcntl-locked JSON shared by all "
        "parallel streams; off by default)",
    )
    parser.add_argument(
        "--bucket-rate",
        type=float,
        default=None,
        help="bucket refill rate in tokens/min (default: 12000)",
    )
    parser.add_argument(
        "--bucket-depth",
        type=float,
        default=None,
        help="bucket capacity in tokens (default: 6500)",
    )
    parser.add_argument(
        "--max-length",
        type=int,
        default=6000,
        help="generation-side runaway cap in answer-text characters per call "
        "(llm7shi max_length: crossing it fails the turn and the Client "
        "regenerates; thinking is not counted; 0 disables; default 6000, "
        "STAGE3.md record S3.10)",
    )
    parser.add_argument(
        "--log",
        type=Path,
        help="streaming JSONL log: unit/gold/canto_complete records, summary "
        "last, plus llm_request/llm_response records from the live fallback. "
        "An existing file is resumed: completed cantos reload and are skipped",
    )
    args = parser.parse_args(argv)

    if args.canto is not None and not args.canticles:
        parser.error("--canto needs an explicit --canticle")
    if (args.canto is None) == (not args.all):
        parser.error("select exactly one of --canto N or --all")

    # §4 optional Rich bar: created up front so every human-facing line and
    # the live fallback's model stream can share its console; without the
    # extra this stays None and plain stderr lines keep the run watchable.
    status_line = HarnessStatusLine() if HarnessStatusLine is not None else None
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

    prior_records: list[dict] = []
    resume_offset = 0
    pending_units: dict[tuple[str, int], dict[tuple[int, int], dict]] = {}
    if args.log and os.path.exists(args.log):
        prior_records = load_log(args.log)
        replay, wanted, pending_units = prepare_resume(prior_records, wanted)
        for record in replay:
            kind = record.get("record")
            if kind == "unit":
                report.add_unit(record)
            elif kind == "gold":
                report.add_gold(record)
            elif kind == "canto_complete":
                report.add_canto_complete(record)
        resumed_units = 0
        for units_by_span in pending_units.values():
            for record in units_by_span.values():
                report.add_unit(record)
                resumed_units += 1
        # A canto still in progress may also carry logged `gold` records for
        # the units above; fold them in too so --verify-gold's aggregate
        # stays exact across the resume.
        pending_cantos = set(pending_units)
        for record in prior_records:
            if record.get("record") == "gold" and (
                record.get("canticle"), record.get("canto")
            ) in pending_cantos:
                report.add_gold(record)
        # Compact before appending: only the (now superseded) summary is
        # stripped. Everything else — including incomplete cantos' unit
        # records — stays, so unit-level resume can skip them below.
        compact_log(args.log)
        if replay or resumed_units:
            resume_offset = total - len(wanted)
            print(
                f"resume: {resume_offset} completed canto(s) loaded from "
                f"{args.log}"
                + (
                    f" ({resumed_units} unit(s) already settled across "
                    f"{len(pending_units)} in-progress canto(s))"
                    if resumed_units
                    else ""
                )
                + f"; continuing with {len(wanted)} left"
            )

    header = (
        f"reconstruct: {'WRITE' if args.write else 'dry-run'} "
        f"(gates: token stream, 0 hard / 0 soft, content hash)"
        f"{', verify-gold' if args.verify_gold else ''}; "
        f"{len(wanted)} canto(s) selected"
    )
    print(header)

    # Stage-3 configuration line (STAGE3.md §4 item 6): payload tier + pacing
    # are live-run facts the operator must see announced before the hours run.
    bucket_note = "off"
    if args.token_bucket is not None:
        rate = (
            DEFAULT_BUCKET_RATE_TOKENS_PER_MIN
            if args.bucket_rate is None
            else args.bucket_rate
        )
        depth = (
            DEFAULT_BUCKET_DEPTH_TOKENS
            if args.bucket_depth is None
            else args.bucket_depth
        )
        bucket_note = (
            f"{args.token_bucket} (rate {rate:g} tok/min, depth {depth:g} tok)"
        )
    if args.max_length < 0:
        parser.error("--max-length must be >= 0 (0 disables the cap)")
    max_length = args.max_length or None
    print(
        f"reconstruct: transcripts verbatim, "
        f"payload tier {args.payload_tier}; pacing: min-send-interval "
        f"{args.min_send_interval:g}s, token bucket {bucket_note}; "
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
        bucket = None
        if args.token_bucket is not None:
            from harness.runner.agent import (
                DEFAULT_BUCKET_DEPTH_TOKENS,
                DEFAULT_BUCKET_RATE_TOKENS_PER_MIN,
                TokenBucket,
            )

            bucket = TokenBucket(
                args.token_bucket,
                rate_per_min=(
                    DEFAULT_BUCKET_RATE_TOKENS_PER_MIN
                    if args.bucket_rate is None
                    else args.bucket_rate
                ),
                depth=(
                    DEFAULT_BUCKET_DEPTH_TOKENS
                    if args.bucket_depth is None
                    else args.bucket_depth
                ),
            )
        fallback_kwargs = {
            "model": args.model,
            "payload_tier": args.payload_tier,
            "min_send_interval": args.min_send_interval,
            "token_bucket": bucket,
            "max_length": max_length,
        }
        if args.max_turns is not None:
            fallback_kwargs["max_turns"] = args.max_turns
        fallback = agent_fallback(
            verbose=args.verbose,
            file=status_line.stream if status_line is not None else None,
            request_log=sink,
            **fallback_kwargs,
        )
    try:
        for index, (canticle, canto) in enumerate(wanted, start=resume_offset + 1):
            progress_separator(
                f"{canticle} {canto}", index, total, stream=ui_stream
            )
            retry_before = _retry_snapshot(status_line)
            canto_started = time.monotonic()
            recon = reconstruct_canto(
                engine, canticle, canto,
                fallback=fallback, status_line=status_line,
                skip_units=pending_units.get((canticle, canto)),
            )
            retries = _retry_delta(retry_before, status_line)
            # Replayed units were already folded into `report` and the log at
            # startup (unit-level resume) — re-emitting them here would
            # double-count and duplicate the sink.
            for outcome in recon.outcomes:
                if outcome.replayed:
                    continue
                record = outcome.to_dict()
                report.add_unit(record)
                if sink is not None:
                    sink.write(json.dumps(record, ensure_ascii=False) + "\n")
            if args.verify_gold:
                gold_report, gold_records = verify_against_gold(recon)
                for outcome, record in zip(recon.outcomes, gold_records):
                    if outcome.replayed:
                        continue
                    report.add_gold(record)
                    if sink is not None:
                        sink.write(json.dumps(record, ensure_ascii=False) + "\n")
            complete: dict = {
                "record": "canto_complete",
                "canticle": canticle,
                "canto": canto,
                "units": len(recon.outcomes),
                "passed": recon.passed,
            }
            if retries is not None:
                complete["api_retries"] = retries[0]
                complete["api_retry_seconds"] = round(retries[1], 1)
            if args.write:
                commit_record = commit(recon)
                complete["commit"] = commit_record
                if sink is not None:
                    sink.write(json.dumps(commit_record, ensure_ascii=False) + "\n")
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
