"""Syntax pattern miner: UD-topology clustering over Stage-1 traces (Milestone 2.1).

Mines the four pooled 87-case benchmark logs (`harness/bench-{unit,predicate}
[-retry].log`) for recurring Universal Dependencies topologies that deterministically
yield a skeleton role, and emits them as executable fast-path rules
(`harness/extractor/PLAN.md` §2.1).

**Supervision is row-level, pooled across runs.** Unit-level 1-shot exact match
happened only 3/87 times (M1.4), far too starved to cluster on; but every case
record carries its final diff against gold (`missing` / `extra` row keys), so
each gold row absent from `missing` is a *correct* predicted row and every
`extra` key is a wrong one. Pooling the four runs yields thousands of labeled
decisions. Sessions are deduped by (unit, workflow, timestamp) so a case
re-run under an identical attempt cannot double-count.

**The mined pattern** is the UD topology around one skeleton row
(predicate position -> argument position):

    (pred_pos_class, pred_deprel, arg_attachment, arg_deprel, arg_pos_class,
     case_lemma)

- `pred_deprel` / `arg_deprel`: the L4 edge labels at both positions (the head
  relations of the subtree);
- `arg_attachment`: how the argument reaches the predicate — `direct` when the
  arg token's own head is the predicate, `conj` when a chain of `conj` edges
  leads there (coordinated dependents share the first conjunct's shape),
  `other` otherwise;
- `case_lemma`: lemma of the argument's `case` child (the preposition), which
  separates `obl:a` / `obl:di` / ... from bare adverbial `obl`;
- `*_pos_class`: coarse Layer-2 classes (fused forms collapse into their verbal /
  nominal head class).

Pro-drop subjects (`arg == (0, 0)`) have no subtree to describe; they are
counted but never clustered — they belong to morphology, not syntax rules.

A cluster (one signature -> one predicted role) becomes a `SyntaxRule` when its
precision `ok / total(cluster-signature)` reaches `--min-precision` (default
1.0, the PLAN's "consistently yield 100% precision") with at least
`--min-support` correct observations. The denominator spans *every* instance
sharing the signature regardless of its predicted role, so systematic noise
(the bare-`obl` over-assignment, `xcomp` over-generation) suppresses the rules
it touches instead of slipping through.

This module is operator-side extraction tooling: it reads gold `skel/` artifacts
and the frozen L2/L4 layers exactly like `runner/benchmark.py`, and writes only
its own reports (`--log`, `--rules-out`). Nothing runs *as* an agent here, so
§4-item-1 masking does not apply (harness/PLAN.md Handoff item 4).

CLI (deterministic batch — no model calls, no live turns):

    uv run python -m harness.extractor.syntax_miner [--run-log LOG]... \
        [--min-support N] [--min-precision P] [--rules-out FILE] \
        [--log FILE] [--max-sessions N] [--coverage-canticle C]... [--max-cantos N]

Observability follows ARCHITECTURE.md §4–§6 scaled to a batch job: stderr
progress per phase, a streaming JSONL `--log` (one `rule` record per emitted
rule, `summary` record last — the completion marker; truncated on startup, a
deliberate one-shot-experiment choice under §5 since mining is deterministic
and cheap to re-run), and a report with both `metrics()` and `summary()` faces.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator, TextIO

from dante_corpus.dep import DepRow, load_dep
from dante_corpus.morph import load_morph
from dante_corpus.skel.io import children_index, load_skel, morph_index

__all__ = [
    "DEFAULT_MIN_PRECISION",
    "DEFAULT_MIN_SUPPORT",
    "DEFAULT_RUN_LOGS",
    "MAX_CONJ_HOPS",
    "CoverageReport",
    "InstanceStats",
    "MineReport",
    "RowContext",
    "RowInstance",
    "SyntaxRule",
    "collect_instances",
    "compute_coverage",
    "iter_case_records",
    "load_rule_table",
    "main",
    "mine_rules",
    "pos_class",
    "rules_to_records",
    "write_rules_json",
]

HARNESS_DIR = Path(__file__).resolve().parents[1]

# The M1.4 + instrumented-re-run logs (gitignored disk artifacts; regenerate
# rather than re-mine if lost — harness/PLAN.md Handoff item 2).
DEFAULT_RUN_LOGS = (
    HARNESS_DIR / "bench-unit.log",
    HARNESS_DIR / "bench-predicate.log",
    HARNESS_DIR / "bench-unit-retry.log",
    HARNESS_DIR / "bench-predicate-retry.log",
)

DEFAULT_MIN_SUPPORT = 3
DEFAULT_MIN_PRECISION = 1.0

# Coordination chains longer than this stop being one construction ("other").
MAX_CONJ_HOPS = 8

RowKey = tuple[int, int, str, int, int]
Position = tuple[int, int]


# --- topology features ---------------------------------------------------------------


def pos_class(pos: str) -> str:
    """Coarse Layer-2 class; fused tokens collapse into their head class."""
    p = (pos or "").lower()
    if "verb" in p:
        return "verb"
    if "pronoun" in p:  # before noun: "relative pronoun" contains both
        return "pronoun"
    if "noun" in p:
        return "noun"
    if "adjective" in p or "participle" in p:
        return "adjective"
    if "numeral" in p:
        return "numeral"
    if "adverb" in p:
        return "adverb"
    return p or "other"


def _attachment(
    arg_row: DepRow, pred: Position, dep_index: dict[Position, DepRow]
) -> str:
    """`direct` / `conj` / `other`: how the arg token reaches the predicate."""
    cur = arg_row
    hops = 0
    while True:
        head = (cur.head_line, cur.head_token)
        if head == (0, 0):
            return "other"
        if head == pred:
            return "direct" if hops == 0 else "conj"
        if cur.deprel != "conj":
            return "other"
        nxt = dep_index.get(head)
        if nxt is None:
            return "other"
        cur = nxt
        hops += 1
        if hops > MAX_CONJ_HOPS:
            return "other"


def _case_lemma(
    arg: Position,
    children_idx: dict[Position, list[DepRow]],
    morph_idx: dict[Position, object],
) -> str:
    """Lemma of the arg's preposition (`case` child), '' when none."""
    children = sorted(
        children_idx.get(arg, ()), key=lambda r: (r.line, r.token)
    )
    for child in children:
        if child.deprel == "case":
            morph = morph_idx.get((child.line, child.token))
            lemma = getattr(morph, "lemma", "")
            return lemma or ""
    return ""


@dataclass(frozen=True)
class RowContext:
    """UD-subtree features of one skeleton row (predicate -> argument)."""

    pred_pos_class: str
    pred_deprel: str
    arg_attachment: str
    arg_deprel: str
    arg_pos_class: str
    case_lemma: str

    def signature(self) -> tuple[str, ...]:
        return (
            self.pred_pos_class,
            self.pred_deprel,
            self.arg_attachment,
            self.arg_deprel,
            self.arg_pos_class,
            self.case_lemma,
        )

    def to_dict(self) -> dict:
        return {
            "pred_pos_class": self.pred_pos_class,
            "pred_deprel": self.pred_deprel,
            "arg_attachment": self.arg_attachment,
            "arg_deprel": self.arg_deprel,
            "arg_pos_class": self.arg_pos_class,
            "case_lemma": self.case_lemma,
        }

    @classmethod
    def build(
        cls,
        dep_index: dict[Position, DepRow],
        morph_idx: dict[Position, object],
        children_idx: dict[Position, list[DepRow]],
        pred: Position,
        arg: Position,
    ) -> "RowContext | None":
        """Features for one pair, or None when either side lacks L2/L4 rows."""
        prow = dep_index.get(pred)
        arow = dep_index.get(arg)
        pm = morph_idx.get(pred)
        am = morph_idx.get(arg)
        if prow is None or arow is None or pm is None or am is None:
            return None
        return cls(
            pred_pos_class=pos_class(getattr(pm, "pos", "")),
            pred_deprel=prow.deprel,
            arg_attachment=_attachment(arow, pred, dep_index),
            arg_deprel=arow.deprel,
            arg_pos_class=pos_class(getattr(am, "pos", "")),
            case_lemma=_case_lemma(arg, children_idx, morph_idx),
        )


@dataclass(frozen=True)
class SyntaxRule:
    """A high-confidence signature->role derivation (the executable predicate).

    `matches` is the fast-path entry point the hybrid engine will call: given a
    freshly built `RowContext`, return the derived role or None.
    """

    pred_pos_class: str
    pred_deprel: str
    arg_attachment: str
    arg_deprel: str
    arg_pos_class: str
    case_lemma: str
    role: str
    support: int
    total: int
    precision: float

    def matches(self, ctx: RowContext) -> str | None:
        return self.role if ctx.signature() == self.signature() else None

    def signature(self) -> tuple[str, ...]:
        return (
            self.pred_pos_class,
            self.pred_deprel,
            self.arg_attachment,
            self.arg_deprel,
            self.arg_pos_class,
            self.case_lemma,
        )

    def to_dict(self) -> dict:
        return asdict(self)


# --- log parsing & instance collection -----------------------------------------------


def iter_case_records(paths: list[Path]) -> Iterator[tuple[str, dict]]:
    """`(run_id, case_record)` pairs from streaming benchmark JSONL logs.

    Torn tail lines from killed runs are skipped (ARCHITECTURE.md §5), as are
    non-case records (summaries, future kinds).
    """
    for path in paths:
        run_id = Path(path).stem
        try:
            fh = open(path, encoding="utf-8")
        except OSError:
            continue
        with fh:
            for line in fh:
                stripped = line.strip()
                if not stripped:
                    continue
                try:
                    record = json.loads(stripped)
                except json.JSONDecodeError:
                    continue
                if isinstance(record, dict) and record.get("record") == "case":
                    yield run_id, record


def _gold_keys(unit: dict) -> set[RowKey]:
    """Gold row keys of one parse unit, read from the frozen artifact."""
    gold = load_skel(unit["canticle"], unit["canto"])
    return {
        (row.line, row.token, row.role, row.arg_line, row.arg_token)
        for no in range(unit["line_start"], unit["line_end"] + 1)
        for row in gold.get(no, ())
    }


@dataclass
class InstanceStats:
    """Counters surfaced alongside the mined instances."""

    sessions: int = 0
    duplicate_sessions: int = 0
    rows_correct: int = 0
    rows_wrong: int = 0
    pro_drop_correct: int = 0
    pro_drop_wrong: int = 0
    unresolved: int = 0

    def to_dict(self) -> dict:
        return {
            "sessions": self.sessions,
            "duplicate_sessions": self.duplicate_sessions,
            "rows_correct": self.rows_correct,
            "rows_wrong": self.rows_wrong,
            "pro_drop_correct": self.pro_drop_correct,
            "pro_drop_wrong": self.pro_drop_wrong,
            "unresolved": self.unresolved,
        }


@dataclass(frozen=True)
class RowInstance:
    """One labeled row-level decision from a pooled run log."""

    run_id: str
    unit: tuple[str, int, int, int]  # canticle, canto, line_start, line_end
    role: str  # the role as predicted (wrong ones keep their wrong label)
    ok: bool  # True when it matched gold
    ctx: RowContext


class _CantoViews:
    """Per-canto artifact caches, built lazily during instance collection."""

    def __init__(self) -> None:
        self._dep: dict[tuple[str, int], dict[Position, DepRow]] = {}
        self._children: dict[tuple[str, int], dict[Position, list[DepRow]]] = {}
        self._morph: dict[tuple[str, int], dict[Position, object]] = {}
        self._gold: dict[tuple[str, int], dict[int, tuple]] = {}

    def view(self, canticle: str, canto: int) -> tuple[dict, dict, dict]:
        key = (canticle, canto)
        if key not in self._dep:
            dep = load_dep(canticle, canto)
            self._dep[key] = {
                (row.line, row.token): row for rows in dep.values() for row in rows
            }
            self._children[key] = children_index(dep)
            self._morph[key] = morph_index(load_morph(canticle, canto))
        return self._dep[key], self._morph[key], self._children[key]

    def gold(self, canticle: str, canto: int) -> dict[int, tuple]:
        key = (canticle, canto)
        if key not in self._gold:
            self._gold[key] = load_skel(canticle, canto)
        return self._gold[key]


def collect_instances(
    paths: list[Path],
    *,
    max_sessions: int | None = None,
    stats: InstanceStats | None = None,
    progress_stream: TextIO | None = sys.stderr,
) -> tuple[list[RowInstance], InstanceStats]:
    """Pool labeled row decisions out of the given run logs.

    Correct instances are the session's gold rows minus `missing`; wrong ones
    are the `extra` keys with their (wrong) predicted roles. Pro-drop rows and
    positions without resolvable L2/L4 context are counted, not clustered.
    """
    stats = stats if stats is not None else InstanceStats()
    instances: list[RowInstance] = []
    views = _CantoViews()
    seen: set[tuple] = set()

    for run_id, record in iter_case_records(paths):
        if max_sessions is not None and stats.sessions >= max_sessions:
            break
        unit = record["unit"]
        trace = record.get("trace") or {}
        dedupe_key = (
            unit.get("canticle"),
            unit.get("canto"),
            unit.get("line_start"),
            unit.get("line_end"),
            record.get("workflow"),
            trace.get("timestamp"),
        )
        if dedupe_key in seen:
            stats.duplicate_sessions += 1
            continue
        seen.add(dedupe_key)
        stats.sessions += 1
        if progress_stream is not None and stats.sessions % 20 == 0:
            print(
                f"[syntax_miner] scanned {stats.sessions} sessions "
                f"(+{stats.duplicate_sessions} duplicates)",
                file=progress_stream,
                flush=True,
            )

        gold_rows = views.gold(unit["canticle"], unit["canto"])
        gold = {
            (row.line, row.token, row.role, row.arg_line, row.arg_token)
            for no in range(unit["line_start"], unit["line_end"] + 1)
            for row in gold_rows.get(no, ())
        }
        missing = {tuple(k) for k in record.get("missing") or []}
        extra = {tuple(k) for k in record.get("extra") or []}
        dep_idx, morph_idx, children_idx = views.view(unit["canticle"], unit["canto"])

        labeled = sorted(gold - missing)
        wrong = sorted(extra)
        for key, ok in [(k, True) for k in labeled] + [(k, False) for k in wrong]:
            pline, ptok, role, aline, atok = key
            if (aline, atok) == (0, 0):
                if ok:
                    stats.pro_drop_correct += 1
                else:
                    stats.pro_drop_wrong += 1
                continue
            ctx = RowContext.build(
                dep_idx, morph_idx, children_idx, (pline, ptok), (aline, atok)
            )
            if ctx is None:
                stats.unresolved += 1
                continue
            if ok:
                stats.rows_correct += 1
            else:
                stats.rows_wrong += 1
            instances.append(
                RowInstance(
                    run_id=run_id,
                    unit=(unit["canticle"], unit["canto"], unit["line_start"], unit["line_end"]),
                    role=role,
                    ok=ok,
                    ctx=ctx,
                )
            )
    return instances, stats


# --- clustering ----------------------------------------------------------------------


def mine_rules(
    instances: list[RowInstance],
    *,
    min_support: int = DEFAULT_MIN_SUPPORT,
    min_precision: float = DEFAULT_MIN_PRECISION,
) -> tuple[list[SyntaxRule], dict]:
    """Cluster instances by signature and keep the high-confidence derivations.

    Returns `(rules, cluster_stats)`; `cluster_stats` carries the full cluster
    table (including rejected clusters) for reporting. A cluster passes when
    `support >= min_support` and `ok / total(signature) >= min_precision`,
    where the denominator spans every role ever predicted under the signature —
    competing readings poison the pattern instead of hiding from the gate.
    """
    table: dict[tuple, dict[str, list[int]]] = {}
    for inst in instances:
        roles = table.setdefault(inst.ctx.signature(), {})
        bucket = roles.setdefault(inst.role, [0, 0])
        bucket[0 if inst.ok else 1] += 1

    rules: list[SyntaxRule] = []
    rejected = 0
    for sig in sorted(table):
        roles = table[sig]
        total = sum(ok + nok for ok, nok in roles.values())
        for role in sorted(roles):
            ok, nok = roles[role]
            precision = ok / total if total else 0.0
            if ok >= min_support and precision >= min_precision:
                fields = dict(zip(RowContext.__dataclass_fields__, sig))
                rules.append(
                    SyntaxRule(
                        role=role,
                        support=ok,
                        total=total,
                        precision=round(precision, 4),
                        **fields,
                    )
                )
            else:
                rejected += 1
    rules.sort(key=lambda r: (-r.support, r.signature(), r.role))
    cluster_stats = {
        "clusters": len(table),
        "rejected_candidates": rejected,
        "instances_clustered": len(instances),
    }
    return rules, cluster_stats


def rules_to_records(rules: list[SyntaxRule]) -> Iterator[dict]:
    for rule in rules:
        record = {"record": "rule"}
        record.update(rule.to_dict())
        yield record


def load_rule_table(rules: list[SyntaxRule]) -> dict[tuple, SyntaxRule]:
    """Signature -> rule lookup; later duplicates must not exist at 1.0 precision."""
    table: dict[tuple, SyntaxRule] = {}
    for rule in rules:
        existing = table.get(rule.signature())
        if existing is None or (rule.precision, rule.support) > (
            existing.precision,
            existing.support,
        ):
            table[rule.signature()] = rule
    return table


def write_rules_json(path: Path, rules: list[SyntaxRule]) -> None:
    payload = {
        "record": "syntax_rules",
        "mined_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "rules": [rule.to_dict() for rule in rules],
    }
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )


# --- deterministic coverage ----------------------------------------------------------


@dataclass
class CoverageReport:
    """Gold-vs-rule-table agreement over whole cantos (deterministic recall probe)."""

    agree: int = 0
    conflict: int = 0
    unmatched: int = 0
    pro_drop: int = 0
    per_role: dict = field(default_factory=dict)

    def observe(self, role: str, outcome: str) -> None:
        setattr(self, outcome, getattr(self, outcome) + 1)
        bucket = self.per_role.setdefault(role, Counter())
        bucket[outcome] += 1

    @property
    def gold_rows(self) -> int:
        return self.agree + self.conflict + self.unmatched

    @property
    def coverage_rate(self) -> float:
        return self.agree / self.gold_rows if self.gold_rows else 0.0

    def to_dict(self) -> dict:
        return {
            "gold_rows": self.gold_rows,
            "agree": self.agree,
            "conflict": self.conflict,
            "unmatched": self.unmatched,
            "pro_drop_rows": self.pro_drop,
            "coverage_rate": round(self.coverage_rate, 4),
            "per_role": {
                role: {
                    "gold": sum(counts.values()),
                    "agree": counts.get("agree", 0),
                    "conflict": counts.get("conflict", 0),
                    "unmatched": counts.get("unmatched", 0),
                }
                for role, counts in sorted(self.per_role.items())
            },
        }


def compute_coverage(
    rules: list[SyntaxRule],
    *,
    canticles: list[str] | None = None,
    max_cantos: int | None = None,
    progress_stream: TextIO | None = sys.stderr,
) -> CoverageReport:
    """How much of the frozen gold the rule table reproduces, corpus-wide.

    Every gold row gets its topology built from L2/L4 and looked up in the
    table: `agree` (rule exists and predicts the stored role), `conflict`
    (rule exists, different role — a real ambiguity signal), `unmatched` (no
    rule), plus the morphology-driven pro-drop rows the syntax tier cannot own.
    """
    from dante_corpus import api

    table = load_rule_table(rules)
    report = CoverageReport()
    canticles = list(canticles or api.canticles())
    done = 0
    total_cantos = sum(len(api.cantos(c)) for c in canticles)
    if max_cantos is not None:
        total_cantos = min(total_cantos, max_cantos)
    views = _CantoViews()
    for canticle in canticles:
        for canto in api.cantos(canticle):
            if max_cantos is not None and done >= max_cantos:
                break
            done += 1
            if progress_stream is not None and done % 10 == 0:
                print(
                    f"[syntax_miner] coverage {done}/{total_cantos} cantos",
                    file=progress_stream,
                    flush=True,
                )
            dep_idx, morph_idx, children_idx = views.view(canticle, canto)
            for rows in load_skel(canticle, canto).values():
                for row in rows:
                    if (row.arg_line, row.arg_token) == (0, 0):
                        report.observe(row.role, "pro_drop")
                        continue
                    ctx = RowContext.build(
                        dep_idx,
                        morph_idx,
                        children_idx,
                        (row.line, row.token),
                        (row.arg_line, row.arg_token),
                    )
                    if ctx is None:
                        report.observe(row.role, "unmatched")
                        continue
                    rule = table.get(ctx.signature())
                    if rule is None:
                        report.observe(row.role, "unmatched")
                    elif rule.role == row.role:
                        report.observe(row.role, "agree")
                    else:
                        report.observe(row.role, "conflict")
        if max_cantos is not None and done >= max_cantos:
            break
    return report


# --- aggregate report -----------------------------------------------------------------


@dataclass
class MineReport:
    """Everything one mining run produced; ships both §6 reporting faces."""

    stats: InstanceStats = field(default_factory=InstanceStats)
    rules: list[SyntaxRule] = field(default_factory=list)
    cluster_stats: dict = field(default_factory=dict)
    coverage: CoverageReport | None = None
    min_support: int = DEFAULT_MIN_SUPPORT
    min_precision: float = DEFAULT_MIN_PRECISION

    def metrics(self) -> dict:
        metrics = {
            "min_support": self.min_support,
            "min_precision": self.min_precision,
            **self.stats.to_dict(),
            **self.cluster_stats,
            "rules": len(self.rules),
            "top_support": max((r.support for r in self.rules), default=0),
        }
        if self.coverage is not None:
            metrics["coverage"] = self.coverage.to_dict()
        return metrics

    def summary(self) -> str:
        s = self.stats
        lines = [
            f"sessions: {s.sessions} (+{s.duplicate_sessions} duplicates skipped)",
            f"labeled rows: {s.rows_correct} correct / {s.rows_wrong} wrong "
            f"(pro-drop {s.pro_drop_correct}/{s.pro_drop_wrong}, unresolved {s.unresolved})",
            f"clusters: {self.cluster_stats.get('clusters', 0)} "
            f"(rejected candidates: {self.cluster_stats.get('rejected_candidates', 0)})",
            f"rules: {len(self.rules)} at precision >= {self.min_precision:.2f} "
            f"(support >= {self.min_support})",
        ]
        if self.rules:
            top = self.rules[:5]
            lines.append("top rules by support:")
            for rule in top:
                lines.append(
                    f"    {rule.pred_pos_class}.{rule.pred_deprel} <- "
                    f"{rule.arg_attachment}:{rule.arg_deprel}"
                    f"[{rule.arg_pos_class}]"
                    f"{'' if not rule.case_lemma else f' +case={rule.case_lemma}'} "
                    f"-> {rule.role} [{rule.support}/{rule.total}]"
                )
        cov = self.coverage
        if cov is not None:
            lines.append(
                f"corpus coverage: {cov.agree}/{cov.gold_rows} gold rows = "
                f"{cov.coverage_rate:.3f} "
                f"(conflict {cov.conflict}, unmatched {cov.unmatched}, "
                f"pro-drop {cov.pro_drop})"
            )
        return "\n".join(lines)


# --- CLI -------------------------------------------------------------------------------


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Mine deterministic UD-topology fast-path rules from Stage-1 "
            "benchmark traces (harness/extractor PLAN.md milestone 2.1)."
        )
    )
    parser.add_argument(
        "--run-log",
        action="append",
        type=Path,
        dest="run_logs",
        help="input benchmark JSONL log (repeatable; defaults to the four "
        "M1.4/re-run logs under harness/)",
    )
    parser.add_argument("--min-support", type=int, default=DEFAULT_MIN_SUPPORT)
    parser.add_argument("--min-precision", type=float, default=DEFAULT_MIN_PRECISION)
    parser.add_argument("--rules-out", type=Path, help="write the rule table JSON here")
    parser.add_argument(
        "--log",
        type=Path,
        help="streaming JSONL output: one rule record per mined rule, summary "
        "record last (truncated on startup — deterministic one-shot run)",
    )
    parser.add_argument(
        "--max-sessions", type=int, help="cap scanned sessions (debug/testing)"
    )
    parser.add_argument(
        "--coverage-canticle",
        action="append",
        choices=("inferno", "purgatorio", "paradiso"),
        dest="coverage_canticles",
        help="restrict corpus coverage to these canticles (default: all)",
    )
    parser.add_argument("--max-cantos", type=int, help="cap coverage scope")
    args = parser.parse_args(argv)

    run_logs = args.run_logs or list(DEFAULT_RUN_LOGS)
    print(
        f"syntax_miner: {len(run_logs)} run log(s), min_support={args.min_support}, "
        f"min_precision={args.min_precision}"
    )

    print("[syntax_miner] scanning run logs...", file=sys.stderr, flush=True)
    instances, stats = collect_instances(run_logs, max_sessions=args.max_sessions)
    rules, cluster_stats = mine_rules(
        instances, min_support=args.min_support, min_precision=args.min_precision
    )
    print("[syntax_miner] computing corpus coverage...", file=sys.stderr, flush=True)
    coverage = compute_coverage(
        rules,
        canticles=args.coverage_canticles,
        max_cantos=args.max_cantos,
    )
    report = MineReport(
        stats=stats,
        rules=rules,
        cluster_stats=cluster_stats,
        coverage=coverage,
        min_support=args.min_support,
        min_precision=args.min_precision,
    )

    if args.rules_out:
        write_rules_json(args.rules_out, rules)
        print(f"rule table written to {args.rules_out}")
    if args.log:
        # One-shot experiment mode (ARCHITECTURE.md §5): truncate on startup;
        # the trailing summary record is the completion marker.
        with open(args.log, "w", encoding="utf-8") as sink:
            for record in rules_to_records(rules):
                sink.write(json.dumps(record, ensure_ascii=False) + "\n")
            sink.write(
                json.dumps(
                    {
                        "record": "summary",
                        "timestamp": datetime.now(timezone.utc).isoformat(
                            timespec="seconds"
                        ),
                        **report.metrics(),
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )
        print(f"records written to {args.log}")
    print(report.summary())
    return 0


if __name__ == "__main__":
    sys.exit(main())
