"""Stage 1 benchmark: gold comparison & metric suite (`runner/PLAN.md` §5, Milestone 1.3).

Runs one autonomous grammar session per challenge case (`agent.run_unit`), then
compares the session's candidate submissions against the 0-soft Gold Standard
(`skel/*.tsv`) and aggregates the §5.2 metrics:

- **1-shot exact match rate**: first `validate_candidate` submission equals gold.
- **Autonomous convergence rate**: final submission equals gold within
  `CONVERGENCE_TURN_BUDGET` (5) turns, without exhausting the budget.
- **Role-level F1**: per-role precision / recall / F1 over (predicate, role,
  argument) row keys, plus micro- and macro-averages.
- **Upstream feedback precision**: form-validity of the records the model filed.
  (True semantic correctness needs human triage; this measures whether the
  channel was used with well-formed L2/L4 defect reports.)

Parse success is measured inside every benchmark run (T4 gate discipline): each
assistant turn is classified exactly like the live probe — a turn with at least
one well-formed `<tool_call>` block succeeds; a no-block turn succeeds only as a
legitimate final answer after prior successful work.

**Masking note**: this module is operator-side evaluation tooling. It reads gold
`skel/` artifacts for comparison only and never serves them to the agent
(`tools.py` stays structurally blind); it never writes under `skel/`.

Live usage (Milestone 1.4, operator-run):

    uv run python -m harness.runner.benchmark --category historical --log bench.log

An existing `--log` file is resumed, not restarted: its completed case records
are loaded into the aggregate (so the final summary covers every session across
attempts), those cases are skipped, and fresh records append after them. The
summary's timing is therefore the **sum of per-session durations** (`turn_seconds`
rolled up over all cases), never a start-to-end wall span — with interruptions
in between, such a span would measure idle time, not work.

Deterministic tests script sessions via `StubTransport` + real gold data.
"""

from __future__ import annotations

import argparse
import contextlib
import json
import os
import sys
import tempfile
from dataclasses import dataclass, field
from datetime import datetime, timezone

from dante_corpus.skel.io import load_skel

from harness.fixtures.challenge_cases import (
    CATEGORIES,
    ChallengeCase,
    case_by_id,
    cases_for,
)
from harness.toolcall import (
    PromptXmlTransport,
    Transport,
    is_parse_error,
    parse_tool_calls,
    progress_printer,
    progress_separator,
)

from .agent import (
    DEFAULT_MODEL,
    MAX_NUDGES,
    SESSION_MAX_TURNS,
    WORKFLOWS,
    UnitResult,
    llm7shi_generate,
    run_unit,
)
from .statusline import HarnessStatusLine
from .tools import GrammarToolkit, tool_specs

__all__ = [
    "CONVERGENCE_TURN_BUDGET",
    "BenchmarkReport",
    "RoleMetrics",
    "UnitEvaluation",
    "evaluate_unit",
    "evaluation_from_record",
    "gold_row_keys",
    "load_log",
    "prepare_resume",
    "run_benchmark",
]

# PLAN §5.2: "0 divergence after multi-turn self-correction (<= 5 turns)".
CONVERGENCE_TURN_BUDGET = 5

# Turn-granularity discipline (harness/PLAN.md §4 item 5): one healthy model turn
# is one reasoning step plus its dispatches. A turn that sits thinking for many
# minutes means too much work was bundled into one response and the prompt or
# workflow must be reconsidered, not the latency accepted. Reports count turns at
# or over this threshold as `slow_turns` so brooding shows up in the aggregates.
SLOW_TURN_SECONDS = 300

# Row identity for comparison: indices + role. Word anchors are verification-only
# (never stored in the artifact), so they are excluded from exact matching.
RowKey = tuple[int, int, str, int, int]


def _row_key(row: dict) -> RowKey:
    return (
        int(row["line"]),
        int(row["token"]),
        str(row["role"]),
        int(row["arg_line"]),
        int(row["arg_token"]),
    )


def _in_unit(line: int, line_start: int, line_end: int) -> bool:
    return line_start <= line <= line_end


def candidate_keys(
    rows: list[dict], line_start: int, line_end: int
) -> tuple[set[RowKey], int, int]:
    """Normalize submitted rows to comparable keys.

    Returns `(keys, malformed, out_of_unit)`: rows missing fields or carrying
    non-integer coordinates cannot be compared and count as malformed; well-formed
    rows whose predicate lies outside the parse unit are excluded from comparison
    (the intrinsic validator already flags them) and counted separately.
    """
    keys: set[RowKey] = set()
    malformed = 0
    out_of_unit = 0
    for raw in rows or []:
        if not isinstance(raw, dict):
            malformed += 1
            continue
        try:
            key = _row_key(raw)
        except (KeyError, TypeError, ValueError):
            malformed += 1
            continue
        if not _in_unit(key[0], line_start, line_end):
            out_of_unit += 1
            continue
        keys.add(key)
    return keys, malformed, out_of_unit


def gold_row_keys(canticle: str, canto: int, line_start: int, line_end: int) -> set[RowKey]:
    """Gold row keys of one parse unit, read from the frozen artifact."""
    gold = load_skel(canticle, canto)
    return {
        (row.line, row.token, row.role, row.arg_line, row.arg_token)
        for no in range(line_start, line_end + 1)
        for row in gold.get(no, ())
    }


def resolve_unit_bounds(canticle: str, canto: int, line_start: int) -> tuple[int, int]:
    """Snap a line to its parse unit (`dep.sentence_groups`), as `read_unit` does."""
    from dante_corpus import api
    from dante_corpus.dep import sentence_groups

    data = api.canto(canticle, canto)
    groups = sentence_groups(
        [line.no for line in data.lines()], [line.text for line in data.lines()]
    )
    for group in groups:
        if group[0] <= line_start <= group[-1]:
            return group[0], group[-1]
    raise ValueError(f"line {line_start} is outside {canticle} {canto}")


def _diff(mine: set[RowKey], gold: set[RowKey]) -> tuple[list[RowKey], list[RowKey]]:
    """Sorted `(missing_in_submission, extra_in_submission)` row-key lists."""
    return sorted(gold - mine), sorted(mine - gold)


# --- per-session measurements ---------------------------------------------------------


def _parse_turn_stats(result: UnitResult) -> tuple[int, int]:
    """`(success_turns, failure_turns)` with the probe's per-turn classification.

    Mirrors `harness.toolcall.probe`: a turn with >= 1 well-formed block parses;
    a block-free turn parses only if earlier turns already made successful calls
    (a legitimate final answer); all-malformed blocks fail. Scans
    `session_messages` only — the few-shot demo exchange in the opening prompt
    carries a well-formed call that is not a model turn.
    """
    success = failure = 0
    wellformed_so_far = 0
    for message in result.session_messages:
        if message.get("role") != "assistant":
            continue
        items = parse_tool_calls(message.get("content", ""))
        wellformed = [item for item in items if not is_parse_error(item)]
        if items:
            if wellformed:
                success += 1
                wellformed_so_far += len(wellformed)
            else:
                failure += 1
        elif wellformed_so_far > 0:
            success += 1
        else:
            failure += 1
    return success, failure


def _feedback_validity(records: list[dict]) -> tuple[int, int]:
    """`(wellformed, total)` upstream-feedback records filed by the model."""
    total = len(records)
    good = sum(
        1
        for record in records
        if isinstance(record, dict)
        and record.get("layer")
        and (record.get("description") or record.get("issue"))
    )
    return good, total


@dataclass(frozen=True)
class RoleMetrics:
    """Confusion counts and derived rates for one role label."""

    tp: int = 0
    fp: int = 0
    fn: int = 0

    @property
    def precision(self) -> float:
        return self.tp / (self.tp + self.fp) if self.tp + self.fp else 0.0

    @property
    def recall(self) -> float:
        return self.tp / (self.tp + self.fn) if self.tp + self.fn else 0.0

    @property
    def f1(self) -> float:
        p, r = self.precision, self.recall
        return 2 * p * r / (p + r) if p + r else 0.0

    def to_dict(self) -> dict:
        return {
            "tp": self.tp,
            "fp": self.fp,
            "fn": self.fn,
            "precision": round(self.precision, 4),
            "recall": round(self.recall, 4),
            "f1": round(self.f1, 4),
        }


@dataclass
class UnitEvaluation:
    """Everything one benchmarked unit produced, including its gold comparison."""

    case_id: str
    category: str
    unit: dict
    # Session facts (mirrors of UnitResult).
    turns: int = 0
    nudges: int = 0
    exhausted: bool = False
    protocol_complete: bool = False
    valid_seen: bool = False
    validations: int = 0
    submissions: int = 0
    workflow: str = "unit"
    # Gold comparison (final submission unless noted; the union of all submissions
    # when `accumulate` — predicate-workflow sessions build the skeleton piecemeal).
    accumulate: bool = False
    gold_rows: int = 0
    predicted_rows: int = 0
    exact_first: bool = False
    exact_final: bool = False
    converged: bool = False
    missing: list[RowKey] = field(default_factory=list)
    extra: list[RowKey] = field(default_factory=list)
    malformed_rows: int = 0
    out_of_unit_rows: int = 0
    # Predicate-level first-attempt exactness: gold predicates whose FIRST coverage
    # (first submission touching them) matched gold exactly for that predicate.
    preds_first_pass: int = 0
    preds_total: int = 0
    # Upstream discrepancy channel.
    upstream_feedback: list[dict] = field(default_factory=list)
    upstream_wellformed: int = 0
    # Protocol health (probe semantics, kept under observation per T4).
    parse_success_turns: int = 0
    parse_failure_turns: int = 0
    # Wall-clock seconds per completed model turn (mirrors UnitResult).
    turn_seconds: list[float] = field(default_factory=list)
    # API-retry backoffs observed during this session. llm7shi auto-retries 429s
    # silently, so without the status line's wait_retry counter these would be
    # invisible post-run; None when no status line tracked them.
    api_retries: int | None = None
    api_retry_seconds: float | None = None
    # Key sets backing the role-level aggregation (not serialized).
    gold_key_set: frozenset[RowKey] = frozenset()
    final_key_set: frozenset[RowKey] = frozenset()

    @property
    def upstream_feedback_precision(self) -> float | None:
        """Form-validity ratio of filed records; None when nothing was filed."""
        if not self.upstream_feedback:
            return None
        return self.upstream_wellformed / len(self.upstream_feedback)

    @property
    def predicate_first_pass_rate(self) -> float | None:
        """First-coverage exactness over the unit's gold predicates; None if no gold."""
        if not self.preds_total:
            return None
        return self.preds_first_pass / self.preds_total

    def to_dict(self) -> dict:
        data = {
            "record": "case",
            "case_id": self.case_id,
            "category": self.category,
            "unit": self.unit,
            "turns": self.turns,
            "nudges": self.nudges,
            "exhausted": self.exhausted,
            "protocol_complete": self.protocol_complete,
            "valid_seen": self.valid_seen,
            "validations": self.validations,
            "submissions": self.submissions,
            "workflow": self.workflow,
            "accumulate": self.accumulate,
            "gold_rows": self.gold_rows,
            "predicted_rows": self.predicted_rows,
            "exact_first": self.exact_first,
            "exact_final": self.exact_final,
            "converged": self.converged,
            "missing": [list(k) for k in self.missing],
            "extra": [list(k) for k in self.extra],
            "malformed_rows": self.malformed_rows,
            "out_of_unit_rows": self.out_of_unit_rows,
            "preds_first_pass": self.preds_first_pass,
            "preds_total": self.preds_total,
            "upstream_feedback": self.upstream_feedback,
            "upstream_wellformed": self.upstream_wellformed,
            "parse_success_turns": self.parse_success_turns,
            "parse_failure_turns": self.parse_failure_turns,
            "turn_seconds": self.turn_seconds,
        }
        precision = self.upstream_feedback_precision
        data["upstream_feedback_precision"] = None if precision is None else round(precision, 4)
        rate = self.predicate_first_pass_rate
        data["predicate_first_pass_rate"] = None if rate is None else round(rate, 4)
        data["api_retries"] = self.api_retries
        data["api_retry_seconds"] = (
            None if self.api_retry_seconds is None else round(self.api_retry_seconds, 1)
        )
        return data


def evaluate_unit(
    result: UnitResult,
    *,
    case: ChallengeCase | None = None,
    convergence_turn_budget: int = CONVERGENCE_TURN_BUDGET,
    accumulate: bool = False,
) -> UnitEvaluation:
    """Score one finished agent session against the 0-soft Gold Standard.

    `case` supplies the fixture identity (case id, category, canonical bounds);
    without it the evaluation still runs on the session's own unit coordinates.

    `accumulate` changes what counts as the final submission: False compares the
    last submission only (unit workflow); True compares, per predicate, its
    LATEST submission's rows (predicate workflow builds the skeleton one
    predicate at a time and may re-validate after corrections — taking the
    latest per predicate lets a repaired frame replace its earlier attempt,
    while a plain union would keep every superseded mistake as an extra row).
    The predicate-level first-pass metric is computed regardless of mode.
    """
    if case is not None:
        canticle, canto = case.canticle, case.canto
        line_start, line_end = case.line_start, case.line_end
        case_id, category = case.case_id, case.category
    else:
        canticle = result.unit["canticle"]
        canto = result.unit["canto"]
        line_start = result.unit["line_start"]
        # The session may have been opened without an explicit end: snap to the
        # actual parse unit so the gold subset is the one the agent was solving.
        _group_start, group_end = resolve_unit_bounds(canticle, canto, line_start)
        line_end = result.unit.get("line_end") or group_end
        case_id, category = "", ""

    gold = gold_row_keys(canticle, canto, line_start, line_end)

    per_submission = [
        candidate_keys(rows, line_start, line_end)
        for rows in result.submissions
    ]
    if not per_submission:
        final, malformed, out_of_unit = set(), 0, 0
    elif accumulate:
        latest_by_pred: dict[tuple[int, int], set[RowKey]] = {}
        malformed = out_of_unit = 0
        for keys, sub_malformed, sub_out_of_unit in per_submission:
            malformed += sub_malformed
            out_of_unit += sub_out_of_unit
            this_pass: dict[tuple[int, int], set[RowKey]] = {}
            for key in keys:
                this_pass.setdefault(key[:2], set()).add(key)
            latest_by_pred.update(this_pass)
        final = (
            set().union(*latest_by_pred.values()) if latest_by_pred else set()
        )
    else:
        final, malformed, out_of_unit = per_submission[-1]

    missing, extra = _diff(final, gold)
    parse_ok, parse_bad = _parse_turn_stats(result)
    preds_first_pass, preds_total = _predicate_first_pass(per_submission, gold)

    return UnitEvaluation(
        case_id=case_id,
        category=category,
        unit={
            "canticle": canticle,
            "canto": canto,
            "line_start": line_start,
            "line_end": line_end,
        },
        turns=result.turns,
        nudges=result.nudges,
        exhausted=result.exhausted,
        protocol_complete=result.protocol_complete,
        valid_seen=result.valid_seen,
        validations=len(result.validations),
        submissions=len(result.submissions),
        workflow=result.workflow,
        accumulate=accumulate,
        gold_rows=len(gold),
        predicted_rows=len(final),
        exact_first=bool(per_submission) and per_submission[0][0] == gold,
        exact_final=bool(result.submissions) and final == gold,
        converged=(
            bool(result.submissions)
            and final == gold
            and not result.exhausted
            and result.turns <= convergence_turn_budget
        ),
        missing=missing,
        extra=extra,
        malformed_rows=malformed,
        out_of_unit_rows=out_of_unit,
        preds_first_pass=preds_first_pass,
        preds_total=preds_total,
        upstream_feedback=list(result.upstream_feedback),
        upstream_wellformed=_feedback_validity(result.upstream_feedback)[0],
        parse_success_turns=parse_ok,
        parse_failure_turns=parse_bad,
        turn_seconds=list(result.turn_seconds),
        gold_key_set=frozenset(gold),
        final_key_set=frozenset(final),
    )


def _predicate_first_pass(
    per_submission: list[tuple[set[RowKey], int, int]],
    gold: set[RowKey],
) -> tuple[int, int]:
    """`(first_pass_preds, total_gold_preds)` at predicate granularity.

    A predicate's *first coverage* is its rows in the earliest submission that
    touches it; it passes when those rows equal gold's rows for that predicate.
    Predicates never covered count as failures via `total`.
    """
    gold_by_pred: dict[tuple[int, int], set[RowKey]] = {}
    for key in gold:
        gold_by_pred.setdefault(key[:2], set()).add(key)

    seen: set[tuple[int, int]] = set()
    first_pass = 0
    for keys, _, _ in per_submission:
        by_pred: dict[tuple[int, int], set[RowKey]] = {}
        for key in keys:
            by_pred.setdefault(key[:2], set()).add(key)
        for pred, pred_keys in by_pred.items():
            if pred in seen:
                continue
            seen.add(pred)
            if pred_keys == gold_by_pred.get(pred):
                first_pass += 1
    return first_pass, len(gold_by_pred)


# --- resume support ---------------------------------------------------------------------


def load_log(path: str) -> list[dict]:
    """Parse a previous attempt's streaming JSONL log into records.

    The stall/interrupt that motivates resuming may cut the final line
    mid-write, so unparsable lines are skipped rather than fatal; blank lines
    are ignored. Both `case` and `summary` records come back in file order.
    """
    records: list[dict] = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            stripped = line.strip()
            if not stripped:
                continue
            try:
                record = json.loads(stripped)
            except json.JSONDecodeError:
                continue  # torn tail from a killed run: keep what completed
            if isinstance(record, dict):
                records.append(record)
    return records


def evaluation_from_record(record: dict) -> UnitEvaluation:
    """Rebuild a reportable `UnitEvaluation` from a logged `case` record.

    Resume support (`prepare_resume`): the record carries every scalar metric,
    but the role-table backing key sets were never serialized — they are
    reconstructed exactly as `evaluate_unit` computed them, reloading the
    frozen gold artifact for the unit and inverting the stored diffs
    (`final = (gold - missing) ∪ extra`).
    """
    unit = record["unit"]
    missing = [tuple(key) for key in record.get("missing") or []]
    extra = [tuple(key) for key in record.get("extra") or []]
    gold = frozenset(
        gold_row_keys(
            unit["canticle"], unit["canto"], unit["line_start"], unit["line_end"]
        )
    )
    final = frozenset((gold - frozenset(missing)) | frozenset(extra))
    return UnitEvaluation(
        case_id=record.get("case_id", ""),
        category=record.get("category", ""),
        unit=dict(unit),
        turns=int(record.get("turns") or 0),
        nudges=int(record.get("nudges") or 0),
        exhausted=bool(record.get("exhausted")),
        protocol_complete=bool(record.get("protocol_complete")),
        valid_seen=bool(record.get("valid_seen")),
        validations=int(record.get("validations") or 0),
        submissions=int(record.get("submissions") or 0),
        workflow=record.get("workflow", "unit"),
        accumulate=bool(record.get("accumulate")),
        gold_rows=int(record.get("gold_rows") or len(gold)),
        predicted_rows=int(record.get("predicted_rows") or len(final)),
        exact_first=bool(record.get("exact_first")),
        exact_final=bool(record.get("exact_final")),
        converged=bool(record.get("converged")),
        missing=missing,
        extra=extra,
        malformed_rows=int(record.get("malformed_rows") or 0),
        out_of_unit_rows=int(record.get("out_of_unit_rows") or 0),
        preds_first_pass=int(record.get("preds_first_pass") or 0),
        preds_total=int(record.get("preds_total") or 0),
        upstream_feedback=list(record.get("upstream_feedback") or []),
        upstream_wellformed=int(record.get("upstream_wellformed") or 0),
        parse_success_turns=int(record.get("parse_success_turns") or 0),
        parse_failure_turns=int(record.get("parse_failure_turns") or 0),
        turn_seconds=[float(s) for s in record.get("turn_seconds") or []],
        api_retries=record.get("api_retries"),
        api_retry_seconds=record.get("api_retry_seconds"),
        gold_key_set=gold,
        final_key_set=final,
    )


def prepare_resume(
    records: list[dict],
    cases: list[ChallengeCase],
    workflow: str,
) -> tuple[list[UnitEvaluation], list[ChallengeCase]]:
    """Split a previous attempt's records into `(loaded_evaluations, remaining_cases)`.

    A `case` record resumes the run when its id is in the current selection and
    its workflow matches (`unit` vs `predicate` scoring aggregates are not
    comparable); anything else stays untouched in the file but cannot pollute
    this run's summary. Records that fail to rebuild (e.g. a unit whose gold
    artifact is gone) are re-run instead of silently dropped.
    """
    selected = {case.case_id: case for case in cases}
    loaded: list[UnitEvaluation] = []
    seen: set[str] = set()
    for record in records:
        if record.get("record") != "case":
            continue
        case_id = record.get("case_id")
        if (
            case_id not in selected
            or record.get("workflow") != workflow
            or case_id in seen
        ):
            continue
        try:
            loaded.append(evaluation_from_record(record))
        except (KeyError, TypeError, ValueError, OSError) as exc:
            print(
                f"resume: could not reload {case_id} ({exc}); rerunning it",
                file=sys.stderr,
            )
            continue
        seen.add(case_id)
    remaining = [case for case in cases if case.case_id not in seen]
    return loaded, remaining


def _jsonl_record_is(line: str, kind: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return False
    try:
        return json.loads(stripped).get("record") == kind
    except json.JSONDecodeError:
        return False


def _strip_stale_summary(path: str) -> None:
    """Drop summary records from an existing log (atomic replace).

    Resuming a *completed* log would otherwise append a fresh summary after the
    old one; stripping superseded summaries keeps the streaming contract's
    completion marker exact — the log ends with a summary iff the latest
    attempt finished.
    """
    with open(path, encoding="utf-8") as fh:
        kept = [line for line in fh if not _jsonl_record_is(line, "summary")]
    directory = os.path.dirname(os.path.abspath(path))
    fd, tmp = tempfile.mkstemp(dir=directory, prefix=".bench-log-", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as dst:
            dst.writelines(kept)
        os.replace(tmp, path)
    except BaseException:
        with contextlib.suppress(OSError):
            os.unlink(tmp)
        raise


# --- aggregate report -------------------------------------------------------------------


class BenchmarkReport:
    """Aggregate §5.2 metrics over evaluated cases."""

    def __init__(self) -> None:
        self.evaluations: list[UnitEvaluation] = []

    def add(self, evaluation: UnitEvaluation) -> None:
        self.evaluations.append(evaluation)

    def __len__(self) -> int:
        return len(self.evaluations)

    def _subset(self, evaluations=None):
        return self.evaluations if evaluations is None else evaluations

    def role_table(self, evaluations=None) -> dict[str, RoleMetrics]:
        """Per-role confusion counts pooled over the given evaluations."""
        table: dict[str, list[int]] = {}

        def bump(role: str, index: int) -> None:
            table.setdefault(role, [0, 0, 0])[index] += 1

        for ev in self._subset(evaluations):
            for key in ev.final_key_set:
                if key in ev.gold_key_set:
                    bump(key[2], 0)  # tp
                else:
                    bump(key[2], 1)  # fp
            for key in ev.gold_key_set - ev.final_key_set:
                bump(key[2], 2)  # fn
        return {role: RoleMetrics(*counts) for role, counts in sorted(table.items())}

    @staticmethod
    def _micro(evaluations) -> RoleMetrics:
        tp = sum(1 for ev in evaluations for key in ev.final_key_set if key in ev.gold_key_set)
        fp = sum(len(ev.final_key_set - ev.gold_key_set) for ev in evaluations)
        fn = sum(len(ev.gold_key_set - ev.final_key_set) for ev in evaluations)
        return RoleMetrics(tp, fp, fn)

    def metrics(self) -> dict:
        """Machine-readable aggregate, as embedded in the `--log` summary record."""
        evals = self.evaluations
        units = len(evals)
        roles = self.role_table()
        micro = self._micro(evals)
        macro_f1 = (
            sum(role.f1 for role in roles.values()) / len(roles) if roles else 0.0
        )
        feedback_records = sum(len(ev.upstream_feedback) for ev in evals)
        feedback_good = sum(ev.upstream_wellformed for ev in evals)
        categories: dict[str, dict] = {}
        for category in CATEGORIES:
            subset = [ev for ev in evals if ev.category == category]
            if subset:
                categories[category] = {
                    "units": len(subset),
                    "one_shot_exact_match_rate": round(
                        sum(ev.exact_first for ev in subset) / len(subset), 4
                    ),
                    "convergence_rate": round(
                        sum(ev.converged for ev in subset) / len(subset), 4
                    ),
                }
        parse_success = sum(ev.parse_success_turns for ev in evals)
        parse_failure = sum(ev.parse_failure_turns for ev in evals)
        preds_total = sum(ev.preds_total for ev in evals)
        preds_first_pass = sum(ev.preds_first_pass for ev in evals)
        # Per-turn wall clock (§4 item 5): aggregated so brooding turns surface
        # in the run totals instead of hiding inside per-case records.
        turn_seconds = [s for ev in evals for s in ev.turn_seconds]
        total_seconds = sum(turn_seconds)
        retry_counts = [ev.api_retries for ev in evals if ev.api_retries is not None]
        retry_secs = [
            ev.api_retry_seconds for ev in evals if ev.api_retry_seconds is not None
        ]
        return {
            "units": units,
            "protocol_complete_rate": round(
                sum(ev.protocol_complete for ev in evals) / units, 4
            ) if units else 0.0,
            "one_shot_exact_match_rate": round(
                sum(ev.exact_first for ev in evals) / units, 4
            ) if units else 0.0,
            "convergence_rate": round(sum(ev.converged for ev in evals) / units, 4)
            if units
            else 0.0,
            "predicate_first_pass_rate": round(preds_first_pass / preds_total, 4)
            if preds_total
            else None,
            "exhausted_sessions": sum(ev.exhausted for ev in evals),
            "no_submission_units": sum(ev.submissions == 0 for ev in evals),
            "role_micro": micro.to_dict(),
            "role_macro_f1": round(macro_f1, 4),
            "roles": {role: m.to_dict() for role, m in roles.items()},
            "upstream_feedback_records": feedback_records,
            "upstream_feedback_wellformed": feedback_good,
            "upstream_feedback_precision": round(feedback_good / feedback_records, 4)
            if feedback_records
            else None,
            "parse_success_turns": parse_success,
            "parse_failure_turns": parse_failure,
            "parse_success_rate": round(parse_success / (parse_success + parse_failure), 4)
            if parse_success + parse_failure
            else None,
            "session_turns": sum(ev.turns for ev in evals),
            "wall_clock_seconds": round(total_seconds, 1),
            "mean_turn_seconds": round(total_seconds / len(turn_seconds), 1)
            if turn_seconds
            else None,
            "max_turn_seconds": round(max(turn_seconds), 1) if turn_seconds else None,
            "slow_turns": sum(1 for s in turn_seconds if s >= SLOW_TURN_SECONDS),
            "api_retries": sum(retry_counts) if retry_counts else None,
            "api_retry_seconds": (
                round(sum(retry_secs), 1) if retry_secs else None
            ),
            "categories": categories,
        }

    def summary(self) -> str:
        """Human-readable one-screen report used by the CLI."""
        m = self.metrics()
        lines = [
            f"units: {m['units']}",
            f"protocol complete: {m['protocol_complete_rate']:.3f}",
            f"1-shot exact match: {m['one_shot_exact_match_rate']:.3f}",
            f"convergence (<= {CONVERGENCE_TURN_BUDGET} turns): {m['convergence_rate']:.3f}"
            f" (exhausted: {m['exhausted_sessions']}, no submission: {m['no_submission_units']})",
            f"role F1: micro={m['role_micro']['f1']:.3f} macro={m['role_macro_f1']:.3f}",
        ]
        if m["predicate_first_pass_rate"] is not None:
            lines.append(f"predicate first-pass exact: {m['predicate_first_pass_rate']:.3f}")
        for role, rm in m["roles"].items():
            lines.append(f"    {role}: P={rm['precision']:.3f} R={rm['recall']:.3f} F1={rm['f1']:.3f}")
        precision = m["upstream_feedback_precision"]
        lines.append(
            f"upstream feedback: {m['upstream_feedback_wellformed']}/{m['upstream_feedback_records']} well-formed"
            + ("" if precision is None else f" ({precision:.3f})")
        )
        if m["parse_success_rate"] is not None:
            lines.append(f"parse success rate: {m['parse_success_rate']:.3f} (gate >= 0.95)")
        if m["session_turns"]:
            lines.append(
                f"turns: {m['session_turns']} in {m['wall_clock_seconds']:.0f}s "
                f"(mean {m['mean_turn_seconds']:.1f}s, max {m['max_turn_seconds']:.1f}s, "
                f"slow(>= {SLOW_TURN_SECONDS}s): {m['slow_turns']})"
            )
        if m["api_retries"] is not None:
            lines.append(
                f"api retries: {m['api_retries']} "
                f"(~{m['api_retry_seconds']:.0f}s backoff)"
            )
        for category, stats in sorted(m["categories"].items()):
            lines.append(
                f"    [{category}] n={stats['units']} "
                f"1-shot={stats['one_shot_exact_match_rate']:.3f} conv={stats['convergence_rate']:.3f}"
            )
        return "\n".join(lines)


# --- runner ---------------------------------------------------------------------------


def _retry_snapshot(status_line) -> tuple[int, float] | None:
    """`(count, seconds)` of api-retry backoffs seen so far, or None if untracked."""
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


def run_benchmark(
    cases: list[ChallengeCase],
    transport: Transport,
    *,
    toolkit: GrammarToolkit | None = None,
    specs: list[dict] | None = None,
    max_turns: int = SESSION_MAX_TURNS,
    max_nudges: int = MAX_NUDGES,
    workflow: str = "unit",
    sink=None,
    include_transcript: bool = False,
    progress: bool = False,
    status_line=None,
    report: BenchmarkReport | None = None,
    resume_offset: int = 0,
) -> BenchmarkReport:
    """Run every case through a fresh session and score it against gold.

    One shared `GrammarToolkit` caches canto loads across sessions (sequential
    runs only: the active-unit guard tracks one unit at a time). `workflow`
    selects the validation granularity taught to the agent ("unit": whole-unit
    submission, compared last-submission-vs-gold; "predicate": per-predicate
    interleaved submissions, compared as their union). `sink`, when given,
    receives one JSONL record per completed case — flushed immediately so an
    interrupted run keeps everything already finished — followed by nothing;
    the caller writes the summary record (see CLI main, mirroring `probe.py`).
    `report`, when given, seeds the returned aggregate with previously
    evaluated cases (resume support: the CLI reloads an interrupted log's case
    records so the final summary aggregates every session across attempts).
    `resume_offset` counts those already-completed cases so the progress
    display spans the whole run, not just this attempt: separators read
    `[offset+i/offset+N]` and the status bar starts at `offset/offset+N`.
    `progress` keeps long live runs watchable (harness/PLAN.md §4 item 5): it
    announces each case with its `[index/total]` position (`toolcall.progress_separator`),
    prints one stderr line per model turn labeled with the running case id
    (`toolcall.progress_printer`), and marks nudged resumes inside a session with a
    minor separator (`toolcall.progress_subseparator`, via `agent.run_unit`).
    `status_line`, when given (a `runner.statusline.HarnessStatusLine`), adds a
    live progress bar whose numerator tracks exactly the separators' basis
    (`pos/total`, updated as each session starts); separators, turn lines, and
    nudge markers then route through its console, and the caller wires the same
    console stream into the transport so streamed model output coexists with the
    bar instead of clobbering it.
    """
    toolkit = GrammarToolkit() if toolkit is None else toolkit
    specs = tool_specs() if specs is None else specs
    if report is None:
        report = BenchmarkReport()
    ui_stream = status_line.stream if status_line is not None else None
    total = resume_offset + len(cases)
    bar = (
        status_line.progress(total, start=resume_offset, label=f"bench:{workflow}")
        if status_line is not None
        else contextlib.nullcontext()
    )
    with bar as prog:
        for pos, case in enumerate(cases, resume_offset + 1):
            retry_before = _retry_snapshot(status_line)
            if progress:
                progress_separator(case.case_id, pos, total, stream=ui_stream)
                if prog is not None:
                    prog.update(pos)
            result = run_unit(
                transport=transport,
                toolkit=toolkit,
                canticle=case.canticle,
                canto=case.canto,
                line_start=case.line_start,
                line_end=case.line_end,
                specs=specs,
                max_turns=max_turns,
                max_nudges=max_nudges,
                workflow=workflow,
                progress=progress,
                progress_stream=ui_stream,
                on_turn=(
                    progress_printer(f"{case.case_id}", max_turns, stream=ui_stream)
                    if progress
                    else None
                ),
            )
            evaluation = evaluate_unit(
                result, case=case, accumulate=(workflow == "predicate")
            )
            delta = _retry_delta(retry_before, status_line)
            if delta is not None:
                evaluation.api_retries, evaluation.api_retry_seconds = delta
            report.add(evaluation)
            if sink is not None:
                record = evaluation.to_dict()
                record["final_text"] = result.text
                record["trace"] = result.trace_record(include_transcript=include_transcript)
                record["trace"].pop("candidate_rows", None)  # already in the case record
                sink.write(json.dumps(record, ensure_ascii=False) + "\n")
                sink.flush()
    return report


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Syntactic challenge benchmark over curated fixtures "
            "(harness/runner PLAN.md milestone 1.3)."
        )
    )
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--temperature", type=float, default=None)
    parser.add_argument("--max-turns", type=int, default=SESSION_MAX_TURNS)
    parser.add_argument("--max-nudges", type=int, default=MAX_NUDGES)
    parser.add_argument(
        "--workflow",
        choices=WORKFLOWS,
        default="unit",
        help="validation granularity: whole unit in one call (unit) or one "
        "predicate per call (predicate; scored as the union of submissions)",
    )
    parser.add_argument("--category", action="append", choices=CATEGORIES)
    parser.add_argument("--case-id", action="append")
    parser.add_argument("--limit", type=int, help="evaluate only the first N selected cases")
    parser.add_argument(
        "--list", action="store_true", help="list the selected fixtures and exit"
    )
    parser.add_argument(
        "--log",
        help=(
            "streaming JSONL log: one case record per line as it completes; "
            "summary record last. An existing file is resumed rather than "
            "truncated: its completed cases are reloaded into the aggregate "
            "and skipped, fresh records append"
        ),
    )
    parser.add_argument("--full-transcript", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args(argv)

    cases = cases_for(args.category)
    if args.case_id:
        unknown = [cid for cid in args.case_id if case_by_id(cid) is None]
        if unknown:
            parser.error(f"unknown case id(s): {unknown}")
        wanted = set(args.case_id)
        cases = [c for c in cases if c.case_id in wanted]
    if args.limit is not None:
        cases = cases[: args.limit]

    if args.list:
        for case in cases:
            print(f"{case.case_id}\t{case.category}\t{case.canticle} {case.canto} "
                  f"{case.line_start}-{case.line_end}")
        return 0
    if not cases:
        parser.error("no cases selected")

    status_line = HarnessStatusLine() if HarnessStatusLine is not None else None
    transport = PromptXmlTransport(
        generate=llm7shi_generate(
            args.model,
            args.temperature,
            quiet=not args.verbose,
            file=status_line.stream if status_line is not None else None,
        )
    )

    # Resume, don't restart: an existing log's completed case records seed the
    # aggregate and their cases are skipped, so a stalled run continues where
    # it stopped instead of discarding hours of finished sessions.
    prior_report = BenchmarkReport()
    if args.log and os.path.exists(args.log):
        records = load_log(args.log)
        loaded, cases = prepare_resume(records, cases, args.workflow)
        for evaluation in loaded:
            prior_report.add(evaluation)
        # A superseded summary record would break "ends with summary = complete".
        if any(record.get("record") == "summary" for record in records):
            _strip_stale_summary(args.log)
        if loaded:
            print(
                f"resume: {len(loaded)} completed case(s) loaded from {args.log}; "
                f"continuing at {len(loaded) + 1}/{len(loaded) + len(cases)} "
                f"({len(cases)} left to run)"
            )

    print(
        f"benchmark: model={args.model} workflow={args.workflow} "
        f"cases={[c.case_id for c in cases][:5]}"
        + (" ..." if len(cases) > 5 else "")
    )
    # Append mode: fresh case records continue after the loaded ones; the
    # summary lands last, covering every session of every attempt.
    sink = open(args.log, "a", encoding="utf-8") if args.log else None
    try:
        report = run_benchmark(
            cases,
            transport,
            max_turns=args.max_turns,
            max_nudges=args.max_nudges,
            workflow=args.workflow,
            sink=sink,
            include_transcript=args.full_transcript,
            progress=True,
            status_line=status_line,
            report=prior_report,
            resume_offset=len(prior_report),
        )
        if sink is not None:
            # No started_at/timestamp span on purpose: with resumed runs the
            # gap between attempts is idle time, so total duration is summed
            # per session instead (wall_clock_seconds et al. below).
            summary = {
                "record": "summary",
                "model": args.model,
                "workflow": args.workflow,
                "temperature": args.temperature,
                "max_turns": args.max_turns,
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
