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

Deterministic tests script sessions via `StubTransport` + real gold data.
"""

from __future__ import annotations

import argparse
import json
import sys
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
)

from .agent import (
    DEFAULT_MODEL,
    MAX_NUDGES,
    SESSION_MAX_TURNS,
    UnitResult,
    llm7shi_generate,
    run_unit,
)
from .tools import GrammarToolkit, tool_specs

__all__ = [
    "CONVERGENCE_TURN_BUDGET",
    "BenchmarkReport",
    "RoleMetrics",
    "UnitEvaluation",
    "evaluate_unit",
    "gold_row_keys",
    "run_benchmark",
]

# PLAN §5.2: "0 divergence after multi-turn self-correction (<= 5 turns)".
CONVERGENCE_TURN_BUDGET = 5

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
    # Gold comparison (final submission unless noted).
    gold_rows: int = 0
    predicted_rows: int = 0
    exact_first: bool = False
    exact_final: bool = False
    converged: bool = False
    missing: list[RowKey] = field(default_factory=list)
    extra: list[RowKey] = field(default_factory=list)
    malformed_rows: int = 0
    out_of_unit_rows: int = 0
    # Upstream discrepancy channel.
    upstream_feedback: list[dict] = field(default_factory=list)
    upstream_wellformed: int = 0
    # Protocol health (probe semantics, kept under observation per T4).
    parse_success_turns: int = 0
    parse_failure_turns: int = 0
    # Key sets backing the role-level aggregation (not serialized).
    gold_key_set: frozenset[RowKey] = frozenset()
    final_key_set: frozenset[RowKey] = frozenset()

    @property
    def upstream_feedback_precision(self) -> float | None:
        """Form-validity ratio of filed records; None when nothing was filed."""
        if not self.upstream_feedback:
            return None
        return self.upstream_wellformed / len(self.upstream_feedback)

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
            "gold_rows": self.gold_rows,
            "predicted_rows": self.predicted_rows,
            "exact_first": self.exact_first,
            "exact_final": self.exact_final,
            "converged": self.converged,
            "missing": [list(k) for k in self.missing],
            "extra": [list(k) for k in self.extra],
            "malformed_rows": self.malformed_rows,
            "out_of_unit_rows": self.out_of_unit_rows,
            "upstream_feedback": self.upstream_feedback,
            "upstream_wellformed": self.upstream_wellformed,
            "parse_success_turns": self.parse_success_turns,
            "parse_failure_turns": self.parse_failure_turns,
        }
        precision = self.upstream_feedback_precision
        data["upstream_feedback_precision"] = None if precision is None else round(precision, 4)
        return data


def evaluate_unit(
    result: UnitResult,
    *,
    case: ChallengeCase | None = None,
    convergence_turn_budget: int = CONVERGENCE_TURN_BUDGET,
) -> UnitEvaluation:
    """Score one finished agent session against the 0-soft Gold Standard.

    `case` supplies the fixture identity (case id, category, canonical bounds);
    without it the evaluation still runs on the session's own unit coordinates.
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

    subs = result.submissions
    first_keys, _, _ = candidate_keys(subs[0] if subs else [], line_start, line_end)
    final_rows = subs[-1] if subs else []
    final, malformed, out_of_unit = candidate_keys(final_rows, line_start, line_end)

    missing, extra = _diff(final, gold)
    parse_ok, parse_bad = _parse_turn_stats(result)

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
        submissions=len(subs),
        gold_rows=len(gold),
        predicted_rows=len(final),
        exact_first=bool(subs) and first_keys == gold,
        exact_final=bool(subs) and final == gold,
        converged=(
            bool(subs)
            and final == gold
            and not result.exhausted
            and result.turns <= convergence_turn_budget
        ),
        missing=missing,
        extra=extra,
        malformed_rows=malformed,
        out_of_unit_rows=out_of_unit,
        upstream_feedback=list(result.upstream_feedback),
        upstream_wellformed=_feedback_validity(result.upstream_feedback)[0],
        parse_success_turns=parse_ok,
        parse_failure_turns=parse_bad,
        gold_key_set=frozenset(gold),
        final_key_set=frozenset(final),
    )


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
        for role, rm in m["roles"].items():
            lines.append(f"    {role}: P={rm['precision']:.3f} R={rm['recall']:.3f} F1={rm['f1']:.3f}")
        precision = m["upstream_feedback_precision"]
        lines.append(
            f"upstream feedback: {m['upstream_feedback_wellformed']}/{m['upstream_feedback_records']} well-formed"
            + ("" if precision is None else f" ({precision:.3f})")
        )
        if m["parse_success_rate"] is not None:
            lines.append(f"parse success rate: {m['parse_success_rate']:.3f} (gate >= 0.95)")
        for category, stats in sorted(m["categories"].items()):
            lines.append(
                f"    [{category}] n={stats['units']} "
                f"1-shot={stats['one_shot_exact_match_rate']:.3f} conv={stats['convergence_rate']:.3f}"
            )
        return "\n".join(lines)


# --- runner ---------------------------------------------------------------------------


def run_benchmark(
    cases: list[ChallengeCase],
    transport: Transport,
    *,
    toolkit: GrammarToolkit | None = None,
    specs: list[dict] | None = None,
    max_turns: int = SESSION_MAX_TURNS,
    max_nudges: int = MAX_NUDGES,
    sink=None,
    include_transcript: bool = False,
) -> BenchmarkReport:
    """Run every case through a fresh session and score it against gold.

    One shared `GrammarToolkit` caches canto loads across sessions (sequential
    runs only: the active-unit guard tracks one unit at a time). `sink`, when
    given, receives one JSONL record per completed case — flushed immediately so
    an interrupted run keeps everything already finished — followed by nothing;
    the caller writes the summary record (see CLI main, mirroring `probe.py`).
    """
    toolkit = GrammarToolkit() if toolkit is None else toolkit
    specs = tool_specs() if specs is None else specs
    report = BenchmarkReport()
    for case in cases:
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
        )
        evaluation = evaluate_unit(result, case=case)
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
            "summary record last (a file without it = interrupted run)"
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

    transport = PromptXmlTransport(
        generate=llm7shi_generate(args.model, args.temperature, quiet=not args.verbose)
    )

    print(
        f"benchmark: model={args.model} cases={[c.case_id for c in cases][:5]}"
        + (" ..." if len(cases) > 5 else "")
    )
    started_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    # "w" mode: the log is truncated at startup so runs never append across attempts.
    sink = open(args.log, "w", encoding="utf-8") if args.log else None
    try:
        report = run_benchmark(
            cases,
            transport,
            max_turns=args.max_turns,
            max_nudges=args.max_nudges,
            sink=sink,
            include_transcript=args.full_transcript,
        )
        if sink is not None:
            summary = {
                "record": "summary",
                "model": args.model,
                "temperature": args.temperature,
                "max_turns": args.max_turns,
                "started_at": started_at,
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
