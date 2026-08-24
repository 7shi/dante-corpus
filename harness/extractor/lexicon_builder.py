"""Verb valency lexicon builder: verb x preposition aggregation over Stage-1 traces (Milestone 2.2).

Mines the same pooled 87-case benchmark logs as the syntax pattern miner
(`harness/bench-{unit,predicate}[-retry].log`) for lexical facts the topology
rules cannot express: does verb V take a P-complement (`obl:a`, `obl:di`,
`obl:in`, ...) as an *argument*, or is that phrase an adjunct? This is the
direct lever on the M1.4 weak spots `obl:di` / `obl:in` (recall 0.54-0.60)
(`harness/extractor/PLAN.md` §2.2).

**Supervision is the same row-level diff labeling** (milestone 2.1): pooling
the four runs, every gold row absent from `missing` is a correct decision and
every `extra` key a wrong one. Sessions dedupe by (unit, workflow, timestamp);
pro-drop rows never yield (no argument position, no preposition). The shared
loader lives in `syntax_miner.iter_labeled_rows` — one scan, two consumers.

**What one observation looks like.** For a labeled row with an explicit
argument position, resolve from the frozen layers:

- `verb_lemma` — Layer-2 lemma at the predicate position;
- `prep` — normalized lemma of the argument's `case` child (Layer 4), i.e.
  what a reconstruction pass can observe without any Layer-5 hint;
- `role` — the asserted role string, kept even when wrong.

Normalization splits fused preposition+article lemmas (`a+il` -> `a`, the
single largest role-vs-case divergence family, ~1.5k gold rows) and strips
spacing/apostrophe variants.

**How observations label a (verb, prep) pair:**

- correct `obl:<prep>` row whose role suffix matches the observed case lemma
  -> positive evidence (the pair is an argument frame);
- correct `obl:` row whose role suffix disagrees with the case lemma
  (`mismatch`) -> poisons the case-lemma pair: the UD shape alone underdetermines
  the reading, exactly the competing-readings-poison discipline of milestone 2.1
  (rare after normalization, ~2% of gold `obl:` rows);
- wrong `obl:` row -> negative evidence against the pair it *claimed* (its own
  role suffix), never against the unrelated case lemma the UD happened to show;
- correct bare-`obl` rows carry no case child in practice (1 of 872 in gold),
  so adjunct-side negatives barely exist; they stay counted, not clustered.

A pair becomes a `ValencyEntry` when its positives reach `--min-support`
(default 3) at consistency `positives / (positives + negatives + mismatches)`
>= `--min-consistency` (default 1.0). Reflexive `si` profiling (PLAN §2.2's
second objective) stays open: in the data `si` surfaces as an ordinary
argument across many roles, so its classification needs clitic-licensing
context rather than co-occurrence counts — deferred, not forgotten.

Like the miner, a deterministic corpus-wide probe closes the loop: every gold
prepositional oblique is re-resolved from L2/L4 and looked up in the lexicon
(`agree` / `conflict` / `unmatched`, plus the bare-`obl` side where an entry
existing at all contradicts gold's adjunct verdict).

This module is operator-side extraction tooling: it reads gold `skel/`
artifacts and the frozen L2/L4 layers exactly like `runner/benchmark.py`, and
writes only its own reports (`--log`, `--lexicon-out`). Nothing runs *as* an
agent here, so §4-item-1 masking does not apply (harness/PLAN.md Handoff
item 4).

CLI (deterministic batch — no model calls, no live turns):

    uv run python -m harness.extractor.lexicon_builder [--run-log LOG]... \
        [--min-support N] [--min-consistency P] [--lexicon-out FILE] \
        [--log FILE] [--max-sessions N] [--coverage-canticle C]... [--max-cantos N]

Observability follows ARCHITECTURE.md §4–§6 scaled to a batch job, mirroring
`syntax_miner.py`: stderr progress per phase, a streaming JSONL `--log` (one
`frame` record per emitted entry, `summary` record last — the completion
marker; truncated on startup as a deliberate one-shot-experiment choice under
§5 since building is deterministic and cheap to re-run), and a report with
both `metrics()` and `summary()` faces.
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

from harness.extractor.syntax_miner import (
    DEFAULT_MIN_SUPPORT,
    DEFAULT_RUN_LOGS,
    InstanceStats,
    _CantoViews,
    _case_lemma,
    iter_labeled_rows,
)

__all__ = [
    "DEFAULT_MIN_CONSISTENCY",
    "LexiconReport",
    "ValencyCoverageReport",
    "ValencyEntry",
    "ValencyInstance",
    "ValencyStats",
    "build_lexicon",
    "collect_valency_instances",
    "compute_coverage",
    "frames_to_records",
    "main",
    "norm_prep",
    "write_lexicon_json",
]

DEFAULT_MIN_CONSISTENCY = 1.0

Position = tuple[int, int]


def norm_prep(lemma: str) -> str:
    """Normalize a case-child lemma into the frame key form.

    Fused preposition+article lemmas collapse to the preposition (`a+il` ->
    `a`); spacing and apostrophe variants fold together (`ver'` -> `ver`,
    `da + i` -> `da`). Empty input stays empty.
    """
    p = (lemma or "").strip().lower()
    p = p.replace("'", "").replace("\u2019", "").replace(" ", "")
    return p.split("+", 1)[0] if p else ""


@dataclass
class ValencyStats(InstanceStats):
    """Instance counters plus the out-of-scope rows this builder ignores."""

    out_of_scope: int = 0  # labeled rows with no preposition decision involved

    def to_dict(self) -> dict:
        return {**super().to_dict(), "out_of_scope": self.out_of_scope}


@dataclass(frozen=True)
class ValencyInstance:
    """One labeled verb-complementation decision from a pooled run log."""

    run_id: str
    unit: tuple[str, int, int, int]  # canticle, canto, line_start, line_end
    verb_lemma: str
    prep: str  # normalized case-child lemma ('' impossible in resolved rows)
    role: str  # the role as asserted (wrong ones keep their wrong label)
    ok: bool  # True when the assertion matched gold


def _in_scope(role: str, prep: str) -> bool:
    """Preposition decisions only: `obl:<prep>` claims, or a bare `obl` whose
    argument unexpectedly carries a case child."""
    return role.startswith("obl:") or (role == "obl" and bool(prep))


def collect_valency_instances(
    paths: list[Path],
    *,
    max_sessions: int | None = None,
    stats: ValencyStats | None = None,
    progress_stream: TextIO | None = sys.stderr,
) -> tuple[list[ValencyInstance], ValencyStats]:
    """Pool labeled verb-preposition decisions out of the given run logs.

    Rows outside the valency scope (subj/obj/ccomp/... and bare-`obl` rows
    without a case child) count as `out_of_scope`; in-scope rows whose verb
    lemma or L4 context cannot resolve count as `unresolved`. Everything else
    becomes a `ValencyInstance`.
    """
    stats = stats if stats is not None else ValencyStats()
    instances: list[ValencyInstance] = []
    views = _CantoViews()

    for run_id, unit, key, ok in iter_labeled_rows(
        paths,
        max_sessions=max_sessions,
        stats=stats,
        views=views,
        progress_stream=progress_stream,
        label="lexicon_builder",
    ):
        pline, ptok, role, aline, atok = key
        dep_idx, morph_idx, children_idx = views.view(unit["canticle"], unit["canto"])
        prep = _case_lemma((aline, atok), children_idx, morph_idx)
        if not _in_scope(role, prep):
            stats.out_of_scope += 1
            continue
        prow = dep_idx.get((pline, ptok))
        vmorph = morph_idx.get((pline, ptok))
        verb_lemma = getattr(vmorph, "lemma", "") if vmorph else ""
        if prow is None or not verb_lemma:
            stats.unresolved += 1
            continue
        if ok:
            stats.rows_correct += 1
        else:
            stats.rows_wrong += 1
        instances.append(
            ValencyInstance(
                run_id=run_id,
                unit=(unit["canticle"], unit["canto"], unit["line_start"], unit["line_end"]),
                verb_lemma=verb_lemma,
                prep=norm_prep(prep),
                role=role,
                ok=ok,
            )
        )
    return instances, stats


# --- frame aggregation -----------------------------------------------------------------


@dataclass(frozen=True)
class ValencyEntry:
    """One high-confidence verb x preposition argument frame (the executable fact).

    At reconstruction time the engine observes the UD case child, normalizes
    it, and looks up `(verb_lemma, prep)`: a hit derives `obl:<prep>` as an
    argument role; a miss leaves the decision to the next tier.
    """

    verb_lemma: str
    prep: str
    role: str  # f"obl:{prep}"
    support: int  # positive observations
    total: int  # support + rejected claims + poisoned mismatches
    consistency: float

    def predicts(self, role: str) -> bool:
        return self.role == role

    def to_dict(self) -> dict:
        return asdict(self)


def build_lexicon(
    instances: list[ValencyInstance],
    *,
    min_support: int = DEFAULT_MIN_SUPPORT,
    min_consistency: float = DEFAULT_MIN_CONSISTENCY,
) -> tuple[list[ValencyEntry], dict]:
    """Aggregate instances into gated `(verb_lemma, prep)` frames.

    Positives are correct `obl:` rows agreeing with the observed case lemma;
    negatives are wrong `obl:` claims charged to their own asserted suffix;
    mismatches (correct `obl:` rows whose role suffix disagrees with the case
    lemma) poison the case-lemma pair. Returns `(entries, cluster_stats)` with
    the full pair table size kept for reporting, rejected pairs included.
    """
    table: dict[tuple[str, str], Counter] = {}
    for inst in instances:
        if inst.ok and inst.role.startswith("obl:"):
            if norm_prep(inst.role[4:]) == inst.prep:
                table.setdefault((inst.verb_lemma, inst.prep), Counter())["arg"] += 1
            else:
                table.setdefault((inst.verb_lemma, inst.prep), Counter())["mismatch"] += 1
        elif not inst.ok and inst.role.startswith("obl:"):
            claimed = norm_prep(inst.role[4:])
            table.setdefault((inst.verb_lemma, claimed), Counter())["rejected"] += 1
        elif inst.ok:
            # Correct bare-`obl` with a stray case child: adjunct verdict over
            # this pair. Rare (1/872 in gold) but a real negative when present.
            table.setdefault((inst.verb_lemma, inst.prep), Counter())["adjunct"] += 1

    entries: list[ValencyEntry] = []
    rejected_pairs = 0
    for (verb_lemma, prep) in sorted(table):
        counts = table[(verb_lemma, prep)]
        support = counts["arg"]
        total = support + counts["rejected"] + counts["mismatch"] + counts["adjunct"]
        consistency = support / total if total else 0.0
        if support >= min_support and consistency >= min_consistency:
            entries.append(
                ValencyEntry(
                    verb_lemma=verb_lemma,
                    prep=prep,
                    role=f"obl:{prep}",
                    support=support,
                    total=total,
                    consistency=round(consistency, 4),
                )
            )
        else:
            rejected_pairs += 1
    entries.sort(key=lambda e: (-e.support, e.verb_lemma, e.prep))
    cluster_stats = {
        "pairs": len(table),
        "rejected_pairs": rejected_pairs,
        "instances_aggregated": len(instances),
    }
    return entries, cluster_stats


def frames_to_records(entries: list[ValencyEntry]) -> Iterator[dict]:
    for entry in entries:
        record = {"record": "frame"}
        record.update(entry.to_dict())
        yield record


def write_lexicon_json(path: Path, entries: list[ValencyEntry]) -> None:
    payload = {
        "record": "verb_valency_lexicon",
        "mined_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "entries": [entry.to_dict() for entry in entries],
    }
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )


# --- deterministic coverage ------------------------------------------------------------


@dataclass
class ValencyCoverageReport:
    """Gold-vs-lexicon agreement over whole cantos (deterministic recall probe).

    Scoped to the rows the lexicon owns: gold `obl:<prep>` rows plus gold
    bare-`obl` rows that carry a case child (where an existing entry directly
    contradicts the adjunct verdict). All other gold rows are out of scope and
    uncounted.
    """

    agree: int = 0
    conflict: int = 0
    unmatched: int = 0
    no_preposition: int = 0
    unresolved: int = 0
    adjunct_conflict: int = 0
    adjunct_unmatched: int = 0
    per_prep: dict = field(default_factory=dict)

    def observe(self, prep: str, outcome: str) -> None:
        setattr(self, outcome, getattr(self, outcome) + 1)
        self.per_prep.setdefault(prep, Counter())[outcome] += 1

    @property
    def gold_rows(self) -> int:
        return self.agree + self.conflict + self.unmatched

    @property
    def coverage_rate(self) -> float:
        return self.agree / self.gold_rows if self.gold_rows else 0.0

    def to_dict(self) -> dict:
        return {
            "gold_obl_rows": self.gold_rows,
            "agree": self.agree,
            "conflict": self.conflict,
            "unmatched": self.unmatched,
            "no_preposition": self.no_preposition,
            "unresolved": self.unresolved,
            "adjunct_conflict": self.adjunct_conflict,
            "adjunct_unmatched": self.adjunct_unmatched,
            "coverage_rate": round(self.coverage_rate, 4),
            "per_prep": {
                prep: {
                    outcome: counts.get(outcome, 0)
                    for outcome in (
                        "agree",
                        "conflict",
                        "unmatched",
                        "adjunct_conflict",
                        "adjunct_unmatched",
                    )
                    if counts.get(outcome)
                }
                for prep, counts in sorted(self.per_prep.items())
            },
        }


def compute_coverage(
    entries: list[ValencyEntry],
    *,
    canticles: list[str] | None = None,
    max_cantos: int | None = None,
    progress_stream: TextIO | None = sys.stderr,
) -> ValencyCoverageReport:
    """How much of the frozen gold's prepositional obliques the lexicon reproduces.

    Every gold `obl:` row gets its `(verb_lemma, case lemma)` re-resolved from
    L2/L4 and looked up: `agree` (entry exists and spells the stored role),
    `conflict` (entry exists, different suffix spelling — genuine ambiguity
    signal), `unmatched` (no entry). Bare-`obl` rows with a case child split
    into `adjunct_conflict` (entry exists — the lexicon would over-call) and
    `adjunct_unmatched`; rows without any case child land in `no_preposition`.
    """
    from dante_corpus import api

    table = {(e.verb_lemma, e.prep): e for e in entries}
    report = ValencyCoverageReport()
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
                    f"[lexicon_builder] coverage {done}/{total_cantos} cantos",
                    file=progress_stream,
                    flush=True,
                )
            dep_idx, morph_idx, children_idx = views.view(canticle, canto)
            for rows in views.gold(canticle, canto).values():
                for row in rows:
                    if (row.arg_line, row.arg_token) == (0, 0):
                        continue
                    role = row.role
                    if role != "obl" and not role.startswith("obl:"):
                        continue
                    raw_prep = _case_lemma(
                        (row.arg_line, row.arg_token), children_idx, morph_idx
                    )
                    prep = norm_prep(raw_prep)
                    vmorph = morph_idx.get((row.line, row.token))
                    verb_lemma = getattr(vmorph, "lemma", "") if vmorph else ""
                    if role == "obl":
                        # Bare-`obl` adjunct verdict; only interesting when the
                        # argument unexpectedly carries a preposition.
                        if prep:
                            report.observe(
                                prep,
                                "adjunct_conflict"
                                if (verb_lemma, prep) in table
                                else "adjunct_unmatched",
                            )
                        continue
                    if not verb_lemma:
                        report.observe(prep or "?", "unresolved")
                        continue
                    if not prep:
                        report.observe("?", "no_preposition")
                        continue
                    entry = table.get((verb_lemma, prep))
                    if entry is None:
                        report.observe(prep, "unmatched")
                    elif norm_prep(role[4:]) == prep:
                        report.observe(prep, "agree")
                    else:
                        report.observe(prep, "conflict")
        if max_cantos is not None and done >= max_cantos:
            break
    return report


# --- aggregate report -------------------------------------------------------------------


@dataclass
class LexiconReport:
    """Everything one lexicon build produced; ships both §6 reporting faces."""

    stats: ValencyStats = field(default_factory=ValencyStats)
    entries: list[ValencyEntry] = field(default_factory=list)
    cluster_stats: dict = field(default_factory=dict)
    coverage: ValencyCoverageReport | None = None
    min_support: int = DEFAULT_MIN_SUPPORT
    min_consistency: float = DEFAULT_MIN_CONSISTENCY

    def metrics(self) -> dict:
        metrics = {
            "min_support": self.min_support,
            "min_consistency": self.min_consistency,
            **self.stats.to_dict(),
            **self.cluster_stats,
            "entries": len(self.entries),
            "verbs": len({e.verb_lemma for e in self.entries}),
            "top_support": max((e.support for e in self.entries), default=0),
        }
        if self.coverage is not None:
            metrics["coverage"] = self.coverage.to_dict()
        return metrics

    def summary(self) -> str:
        s = self.stats
        lines = [
            f"sessions: {s.sessions} (+{s.duplicate_sessions} duplicates skipped)",
            f"labeled rows: {s.rows_correct} correct / {s.rows_wrong} wrong "
            f"(out of scope {s.out_of_scope}, unresolved {s.unresolved}, "
            f"pro-drop {s.pro_drop_correct}/{s.pro_drop_wrong})",
            f"pairs: {self.cluster_stats.get('pairs', 0)} "
            f"(rejected candidates: {self.cluster_stats.get('rejected_pairs', 0)})",
            f"frames: {len(self.entries)} entries over "
            f"{len({e.verb_lemma for e in self.entries})} verbs at consistency >= "
            f"{self.min_consistency:.2f} (support >= {self.min_support})",
        ]
        if self.entries:
            lines.append("top frames by support:")
            for entry in self.entries[:5]:
                lines.append(
                    f"    {entry.verb_lemma} +{entry.prep} -> {entry.role} "
                    f"[{entry.support}/{entry.total}]"
                )
        cov = self.coverage
        if cov is not None:
            lines.append(
                f"corpus coverage: {cov.agree}/{cov.gold_rows} gold obl rows = "
                f"{cov.coverage_rate:.3f} "
                f"(conflict {cov.conflict}, unmatched {cov.unmatched}, "
                f"adjunct conflict/unmatched {cov.adjunct_conflict}/"
                f"{cov.adjunct_unmatched})"
            )
        return "\n".join(lines)


# --- CLI ---------------------------------------------------------------------------------


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Build the empirical verb valency lexicon from Stage-1 benchmark "
            "traces (harness/extractor PLAN.md milestone 2.2)."
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
    parser.add_argument(
        "--min-consistency", type=float, default=DEFAULT_MIN_CONSISTENCY
    )
    parser.add_argument(
        "--lexicon-out", type=Path, help="write the lexicon JSON artifact here"
    )
    parser.add_argument(
        "--log",
        type=Path,
        help="streaming JSONL output: one frame record per emitted entry, "
        "summary record last (truncated on startup — deterministic one-shot run)",
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
        f"lexicon_builder: {len(run_logs)} run log(s), min_support={args.min_support}, "
        f"min_consistency={args.min_consistency}"
    )

    print("[lexicon_builder] scanning run logs...", file=sys.stderr, flush=True)
    instances, stats = collect_valency_instances(
        run_logs, max_sessions=args.max_sessions
    )
    entries, cluster_stats = build_lexicon(
        instances,
        min_support=args.min_support,
        min_consistency=args.min_consistency,
    )
    print("[lexicon_builder] computing corpus coverage...", file=sys.stderr, flush=True)
    coverage = compute_coverage(
        entries,
        canticles=args.coverage_canticles,
        max_cantos=args.max_cantos,
    )
    report = LexiconReport(
        stats=stats,
        entries=entries,
        cluster_stats=cluster_stats,
        coverage=coverage,
        min_support=args.min_support,
        min_consistency=args.min_consistency,
    )

    if args.lexicon_out:
        write_lexicon_json(args.lexicon_out, entries)
        print(f"lexicon written to {args.lexicon_out}")
    if args.log:
        # One-shot experiment mode (ARCHITECTURE.md §5): truncate on startup;
        # the trailing summary record is the completion marker.
        with open(args.log, "w", encoding="utf-8") as sink:
            for record in frames_to_records(entries):
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
