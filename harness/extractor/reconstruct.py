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
context/new/output sizes in UTF-8 bytes, duration). The log is **append-only
and never read back** — it is a debug record, so a resumed run's aggregates
cover that attempt alone.

Resume runs off the artifact instead (`--tsv`, `TsvArtifact`, `../STAGE5.md`
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
from typing import Callable, Iterator, TextIO

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
    # Verdict the agent's own gate gave the submission that was adopted: None
    # when nothing was validated (fast path, dry mode, or a session that never
    # called the tool), False when the session ended on rows its gate rejected
    # — a *provisional* adoption at the turn cap, and the primary readout of
    # whether in-session correction converges (`../STAGE5.md` record S5.5).
    final_submission_valid: bool | None = None
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
            # True only when the session ended on rows its own gate rejected.
            "adopted_invalid": self.final_submission_valid is False,
            "final_submission_valid": self.final_submission_valid,
            "fallback_seconds": (
                None if self.fallback_seconds is None
                else round(self.fallback_seconds, 1)
            ),
        }


def _validate_rows(
    layers: "CantoLayers", group: list[int], unit_rows: dict[int, list[SkelRow]]
) -> tuple[list[Violation], list[Violation]]:
    """§4.1 gate 2 over one unit's assembled rows -> `(hard, soft)`."""
    text_by_no = layers.text_by_no
    violations = validate_unit(
        group,
        [text_by_no[no] for no in group],
        unit_rows,
        morph_rows=layers.morph_rows,
        np_rows=layers.np_rows,
        dep_rows=layers.dep_rows,
        case_rows=layers.case_rows,
    )
    return split_violations(violations)


def _replay_unit_outcome(
    rows: dict[int, list[SkelRow]], layers: "CantoLayers", group: list[int]
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
    hard, soft = _validate_rows(layers, group, unit_rows)
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
    from those rows (`_replay_unit_outcome`, gates re-run) instead of
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
                    _replay_unit_outcome(settled, layers, group)
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
            hard, soft = _validate_rows(layers, group, unit_rows)
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
            )
            recon.outcomes.append(outcome)
            # §5 durability seam: hand the settled outcome to the caller while
            # the canto is still running, so the record is on disk before the
            # next unit's (possibly hours-long) fallback begins.
            if emit_unit is not None:
                emit_unit(outcome)
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
    return "\t".join(_TSV_HEADER) + "\n" + _render_body(lines)


def _render_body(lines: list[tuple[int, list[SkelRow]]]) -> str:
    """`render_tsv`'s payload without the header — one line block per canto line.

    Shared with `TsvArtifact.write_unit`, which appends these blocks a unit at
    a time; keeping one renderer is what makes the streamed file byte-identical
    to a whole-canto render.
    """
    out = []
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


class TsvArtifact:
    """A canto's gold-format TSV, written unit by unit and read back to resume.

    The TSV — not the log — is the run's durable artifact and its resume state
    (`../STAGE5.md` record S5.5). Two properties make that work:

    - **Append-per-unit is byte-identical to the whole-canto render.** Parse
      units come from `dep.sentence_groups` (the same call, with the same
      default `MAX_UNIT_LINES`, that `recon/check.py` validates against), so
      they are line-ordered, contiguous, and cover every line exactly once;
      `render_tsv` emits a sentinel row for a line with no predicates. Writing
      units in order therefore reproduces `render_tsv(whole canto)` exactly.
    - **Line-number presence is the settled-unit test.** Every line of a
      settled unit is in the file, sentinel or not, so a unit whose lines are
      all present needs no rerun and a unit missing any of them is unsettled.

    That second property is also the operator's fix gesture: delete the lines
    of a stretch you want reconsidered and re-run — the unit regenerates. A
    *partially* deleted unit counts as unsettled too, and its surviving rows
    are dropped, so a half-edited unit never lands half old and half new.

    Writes go through one of two paths. While the settled units form a prefix
    of the canto, each newly settled unit is appended (durable per unit, like
    the log sink). Once there is a gap in the middle — the fix case — the file
    is rewritten whole, in line order, on every settle: append cannot express
    an insertion, and the artifact must never be left in line-shuffled order.
    """

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.rows: dict[int, list[SkelRow]] = {}
        self._append_only = True

    # --- read ---------------------------------------------------------------------

    def load(self) -> dict[int, list[SkelRow]]:
        """Parse the artifact on disk (missing file = nothing settled yet).

        Mirror of `skel.io.load_skel` over an arbitrary path: a sentinel row
        (`token == 0`) registers its line as present without contributing a
        row, which is exactly what the settled-unit test needs.
        """
        self.rows = {}
        if not self.path.exists():
            return self.rows
        for index, text in enumerate(
            self.path.read_text(encoding="utf-8").splitlines()
        ):
            if index == 0 or not text:  # header / blank
                continue
            cells = text.split("\t")
            cells += [""] * (len(_TSV_HEADER) - len(cells))
            no = int(cells[0])
            token = int(cells[1])
            bucket = self.rows.setdefault(no, [])
            if token == 0:  # sentinel: line processed, no predicates
                continue
            bucket.append(
                SkelRow(line=no, token=token, word=cells[2], role=cells[3],
                        arg_line=int(cells[4]), arg_token=int(cells[5]))
            )
        return self.rows

    def settled(
        self, units: list[list[int]]
    ) -> dict[tuple[int, int], dict[int, list[SkelRow]]]:
        """`(line_start, line_end) -> rows` for every unit fully present on disk.

        Units only partially present are *not* returned and their rows are
        discarded from the in-memory artifact, so a rewrite never carries a
        half-deleted unit's leftovers.
        """
        result: dict[tuple[int, int], dict[int, list[SkelRow]]] = {}
        for group in units:
            span = (group[0], group[-1])
            if all(no in self.rows for no in group):
                result[span] = {no: list(self.rows[no]) for no in group}
            else:
                for no in group:
                    self.rows.pop(no, None)
        # A gap anywhere but the tail means later settles cannot be appended.
        settled_lines = {no for group in units for no in group if no in self.rows}
        ordered = [no for group in units for no in group]
        seen_missing = False
        for no in ordered:
            if no not in settled_lines:
                seen_missing = True
            elif seen_missing:
                self._append_only = False
                break
        return result

    # --- write --------------------------------------------------------------------

    def write_unit(self, group: list[int], rows: dict[int, list[SkelRow]]) -> None:
        """Land one settled unit, appending when possible and rewriting when not."""
        for no in group:
            self.rows[no] = list(rows.get(no, []))
        if self._append_only:
            new = not self.path.exists()
            with open(self.path, "a", encoding="utf-8") as fh:
                if new:
                    fh.write("\t".join(_TSV_HEADER) + "\n")
                fh.write(_render_body([(no, self.rows[no]) for no in group]))
                fh.flush()  # durable per unit, like the log sink
        else:
            self.rewrite()

    def rewrite(self) -> None:
        """Write every settled line in line order (the post-gap path)."""
        payload = render_tsv(
            [(no, self.rows[no]) for no in sorted(self.rows)]
        )
        self.path.write_text(payload, encoding="utf-8")


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
        "--max-length",
        type=int,
        default=6000,
        help="generation-side runaway cap in answer-text characters per call "
        "(llm7shi max_length: crossing it fails the turn and the Client "
        "regenerates; thinking is not counted; 0 disables; default 6000, "
        "STAGE3.md record S3.10)",
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
    args = parser.parse_args(argv)

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
    if artifact is not None:
        artifact.load()
        settled_units = artifact.settled(
            CantoLayers.load(*wanted[0]).units()
        )
        if settled_units:
            print(
                f"resume: {len(settled_units)} unit(s) already settled in "
                f"{args.tsv}"
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

            def settle(outcome: UnitOutcome) -> None:
                record = outcome.to_dict()
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
            }
            if retries is not None:
                complete["api_retries"] = retries[0]
                complete["api_retry_seconds"] = round(retries[1], 1)
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
