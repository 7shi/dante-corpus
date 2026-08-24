"""Hybrid execution engine: deterministic fast path + Stage-1 agent fallback (Milestone 2.3).

Third Stage-2 deliverable (`harness/extractor/PLAN.md` §3): a two-tier router
that derives skeleton rows without any model call wherever the mined rule
table (`syntax_miner.py`) and valency lexicon (`lexicon_builder.py`) decide
confidently, and hands the whole parse unit to the Stage-1 agent runner
(`runner.agent.run_unit`) otherwise.

**Tier 1 — the fast path** re-derives rows from the frozen L2/L4 layers only.
For every ordered token pair (predicate, argument) inside the parse unit whose
argument reaches the predicate through a UD edge or a `conj` chain
(`RowContext.arg_attachment` in {direct, conj}), it looks up:

- the rule table by topology signature — a hit derives the signature's role;
- failing that, when the predicate is verbal and the argument carries a `case`
  child, the valency lexicon by `(verb_lemma, norm_prep(case lemma))` — a hit
  derives `obl:<prep>` as an argument frame.

Pairs where both sources fire with *different* roles are recorded as conflicts
and derive nothing: ambiguity routes upward, it never gets resolved silently.

The mined `other`-attachment rules are deliberately **not executable here**:
they were learned from gold-row-shaped pairs, and on fresh pairs they fire on
grammatically unrelated tokens (measured P 0.42 all-pairs vs 0.95 attached on
inferno 1-5). Their signatures stay ambiguity signals for mining; derivation
enumerates only structurally attached pairs.

Pro-drop rows have no argument position to derive from, so the fast path can
never complete such a unit alone. The router therefore counts **pro-drop
suspects** — finite personal verbs (`mood` indicative/subjunctive/imperative,
`person` set) that carry no derived `subj` row and are not `cop`/`aux` heads —
and defaults to routing those units to the agent. The bias is deliberately
conservative: over-routing costs agent turns, under-routing silently loses
rows. Until the morphology tier exists this keeps fast-path output trustworthy;
the probe reports what share of units that is today.

**Tier 2 — the fallback seam**: `HybridEngine.run_unit(..., fallback=...)`
takes any callable `(canticle=..., canto=..., line_start=..., line_end=...) ->
UnitResult`; its final `validate_candidate` submission is normalized with the
benchmark's own `candidate_keys`, so agent-routed units are judged exactly like
Stage-1 benchmark cases. `agent_fallback(model=...)` builds the live callable
over `runner.agent.run_unit` (lazy imports; operator-run only). With
`fallback=None` an agent-routed unit stays unrouted — dry mode for probes.

This module has two faces with different gold discipline:

- **Execution** (`HybridEngine.derive_unit` / `.run_unit`) never opens a gold
  artifact — `_CantoViews.view()` loads L2/L4 only — so it is production-safe
  and tested adversarially against a poisoned `skel.io.load_skel`.
- **Evaluation** (`evaluate_fast_path`, the CLI) is operator-side tooling that
  reads gold `skel/` exactly like `runner/benchmark.py` to score derived rows.

CLI (deterministic batch — no model calls, no live turns):

    uv run python -m harness.extractor.hybrid_engine [--rules-in FILE] \
        [--lexicon-in FILE] [--run-log LOG]... [--min-support N]
        [--min-precision P] [--min-consistency P] [--eval-canticle C]...
        [--max-cantos N] [--log FILE]

Without `--rules-in` / `--lexicon-in` the artifacts are regenerated
deterministically from the pooled run logs (mining runs in seconds), so no
mined artifact needs to be frozen on disk (harness/PLAN.md Handoff item 1).
Observability follows ARCHITECTURE.md §4–§6 scaled to a batch job, mirroring
`syntax_miner.py`: stderr progress per phase, a streaming JSONL `--log` (one
`unit` record per probed parse unit, `summary` record last — the completion
marker; truncated on startup as a deliberate one-shot-experiment choice under
§5), and a report with both `metrics()` and `summary()` faces.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Iterator, TextIO

from harness.extractor.lexicon_builder import (
    DEFAULT_MIN_CONSISTENCY,
    ValencyEntry,
    build_lexicon,
    collect_valency_instances,
    norm_prep,
    write_lexicon_json,
)
from harness.extractor.syntax_miner import (
    DEFAULT_MIN_PRECISION,
    DEFAULT_MIN_SUPPORT,
    DEFAULT_RUN_LOGS,
    Position,
    RowContext,
    SyntaxRule,
    _CantoViews,
    collect_instances,
    load_rule_table,
    mine_rules,
    pos_class,
    write_rules_json,
)
from harness.runner.benchmark import candidate_keys

# Fallback contract: `(canticle=..., canto=..., line_start=..., line_end=...)`
# -> Stage-1 `UnitResult` (only `.candidate_rows` is consumed).
AgentFallback = Callable[..., object]

__all__ = [
    "COVERAGE_TARGET",
    "DEFAULT_EVAL_CANTICLES",
    "FINITE_MOODS",
    "AgentFallback",
    "DerivedRow",
    "Derivation",
    "EngineReport",
    "HybridEngine",
    "HybridResult",
    "MinedArtifacts",
    "PairConflict",
    "RouteDecision",
    "RoutePolicy",
    "agent_fallback",
    "load_lexicon_json",
    "load_rules_json",
    "main",
    "mine_artifacts",
    "route_derivation",
]

# extractor/PLAN.md §1 objective: ">80% fast-path coverage".
COVERAGE_TARGET = 0.80

# L2 morphology moods whose verbs take a (possibly unexpressed) subject.
FINITE_MOODS = frozenset({"indicative", "subjunctive", "imperative"})

# Copula/auxiliary heads: the subject attaches to the content predicate, not
# to them, so their lacking a derived subj says nothing about pro-drop.
NON_SUBJECT_HEAD_DEPRELS = frozenset({"cop", "aux"})

DEFAULT_EVAL_CANTICLES = ("inferno", "purgatorio", "paradiso")

RowKey = tuple[int, int, str, int, int]


# --- fast-path derivation ---------------------------------------------------------------


@dataclass(frozen=True)
class DerivedRow:
    """One deterministically derived skeleton row, with its evidence."""

    line: int
    token: int
    role: str
    arg_line: int
    arg_token: int
    source: str  # "rule" | "lexicon"
    support: int  # rule support / entry support behind the decision
    confidence: float  # rule precision / entry consistency

    def key(self) -> RowKey:
        return (self.line, self.token, self.role, self.arg_line, self.arg_token)

    def to_dict(self) -> dict:
        return {
            "line": self.line,
            "token": self.token,
            "role": self.role,
            "arg_line": self.arg_line,
            "arg_token": self.arg_token,
            "source": self.source,
            "support": self.support,
            "confidence": self.confidence,
        }


@dataclass(frozen=True)
class PairConflict:
    """A pair where the rule table and the lexicon disagree on the role."""

    pred: Position
    arg: Position
    rule_role: str
    lexicon_role: str

    def to_dict(self) -> dict:
        return {
            "pred": list(self.pred),
            "arg": list(self.arg),
            "rule_role": self.rule_role,
            "lexicon_role": self.lexicon_role,
        }


@dataclass
class Derivation:
    """Everything one unit's fast path produced (no gold anywhere)."""

    unit: dict  # canticle, canto, line_start, line_end
    rows: list[DerivedRow] = field(default_factory=list)
    conflicts: list[PairConflict] = field(default_factory=list)
    pro_drop_suspects: list[Position] = field(default_factory=list)
    pairs_examined: int = 0
    attached_pairs: int = 0  # direct/conj candidates actually looked up
    other_attachment_pairs: int = 0  # structurally unrelated: never decided
    unresolved_pairs: int = 0  # L2/L4 rows missing at one side
    reinforced_pairs: int = 0  # rule and lexicon agreed on the same role

    @property
    def keys(self) -> set[RowKey]:
        return {row.key() for row in self.rows}

    def to_dict(self) -> dict:
        return {
            "unit": dict(self.unit),
            "rows": [row.to_dict() for row in self.rows],
            "conflicts": [c.to_dict() for c in self.conflicts],
            "pro_drop_suspects": [list(p) for p in self.pro_drop_suspects],
            "pairs_examined": self.pairs_examined,
            "attached_pairs": self.attached_pairs,
            "other_attachment_pairs": self.other_attachment_pairs,
            "unresolved_pairs": self.unresolved_pairs,
            "reinforced_pairs": self.reinforced_pairs,
        }


def _is_finite_personal(morph) -> bool:
    """True for verbs inflected for person in a finite mood (pro-drop hosts)."""
    if pos_class(getattr(morph, "pos", "")) != "verb":
        return False
    return (
        getattr(morph, "person", "") in {"1", "2", "3"}
        and getattr(morph, "mood", "") in FINITE_MOODS
    )


class HybridEngine:
    """Tier-1 derivation plus the Tier-2 routing seam.

    Built from mined artifacts (`SyntaxRule`s + `ValencyEntry`s); holds a lazy
    per-canto L2/L4 cache shared across units. Execution face: `derive_unit`
    and `run_unit` never read gold `skel/` artifacts.
    """

    def __init__(
        self,
        rules: list[SyntaxRule],
        entries: list[ValencyEntry],
        *,
        views: _CantoViews | None = None,
    ) -> None:
        self.rule_table = load_rule_table(rules)
        self.lexicon = {(e.verb_lemma, e.prep): e for e in entries}
        self.views = views if views is not None else _CantoViews()

    def derive_unit(
        self, canticle: str, canto: int, line_start: int, line_end: int
    ) -> Derivation:
        """Run tier 1 over one parse unit from the frozen layers alone."""
        dep_idx, morph_idx, children_idx = self.views.view(canticle, canto)
        tokens = sorted(
            pos for (line, tok) in dep_idx if line_start <= line <= line_end
            for pos in [(line, tok)]
        )
        d = Derivation(
            unit={
                "canticle": canticle,
                "canto": canto,
                "line_start": line_start,
                "line_end": line_end,
            }
        )
        has_subj: set[Position] = set()
        for pred in tokens:
            pm = morph_idx.get(pred)
            pclass = pos_class(getattr(pm, "pos", "")) if pm else ""
            verb_lemma = getattr(pm, "lemma", "") if pm else ""
            for arg in tokens:
                if arg == pred:
                    continue
                d.pairs_examined += 1
                ctx = RowContext.build(
                    dep_idx, morph_idx, children_idx, pred, arg
                )
                if ctx is None:
                    d.unresolved_pairs += 1
                    continue
                if ctx.arg_attachment == "other":
                    d.other_attachment_pairs += 1
                    continue
                d.attached_pairs += 1
                rule = self.rule_table.get(ctx.signature())
                entry = None
                if pclass == "verb" and ctx.case_lemma:
                    prep = norm_prep(ctx.case_lemma)
                    if prep:
                        entry = self.lexicon.get((verb_lemma, prep))
                lexicon_role = entry.role if entry is not None else None
                if rule is not None and lexicon_role is not None:
                    if rule.role != lexicon_role:
                        d.conflicts.append(
                            PairConflict(
                                pred=pred,
                                arg=arg,
                                rule_role=rule.role,
                                lexicon_role=lexicon_role,
                            )
                        )
                        continue
                    d.reinforced_pairs += 1
                if rule is not None:
                    d.rows.append(
                        DerivedRow(
                            pred[0], pred[1], rule.role, arg[0], arg[1],
                            source="rule",
                            support=rule.support,
                            confidence=rule.precision,
                        )
                    )
                elif entry is not None:
                    d.rows.append(
                        DerivedRow(
                            pred[0], pred[1], entry.role, arg[0], arg[1],
                            source="lexicon",
                            support=entry.support,
                            confidence=entry.consistency,
                        )
                    )
                else:
                    continue
                if d.rows[-1].role == "subj":
                    has_subj.add(pred)

            if (
                pclass == "verb"
                and pred not in has_subj
                and _is_finite_personal(pm)
                and (dep := dep_idx.get(pred)) is not None
                and dep.deprel not in NON_SUBJECT_HEAD_DEPRELS
            ):
                d.pro_drop_suspects.append(pred)
        return d

    def run_unit(
        self,
        *,
        canticle: str,
        canto: int,
        line_start: int,
        line_end: int | None = None,
        policy: RoutePolicy | None = None,
        fallback: AgentFallback | None = None,
    ) -> "HybridResult":
        """Derive, route, and (when routed) execute the fallback seam.

        `fallback`, when given, is called once with the unit coordinates and
        must return a Stage-1 `UnitResult`-like object; its final submission is
        normalized with the benchmark's own `candidate_keys`. When it is None
        an agent-routed unit stays unrouted (dry mode: decision + derivation
        only, empty accepted rows). Fast-path rows are returned as-is — they
        are already `RowKey`-shaped decisions.
        """
        active_policy = policy if policy is not None else RoutePolicy()
        if line_end is None:
            from harness.runner.benchmark import resolve_unit_bounds

            _, line_end = resolve_unit_bounds(canticle, canto, line_start)
        derivation = self.derive_unit(canticle, canto, line_start, line_end)
        decision = route_derivation(derivation, active_policy)
        result = HybridResult(
            unit=derivation.unit,
            derivation=derivation,
            decision=decision,
        )
        if decision.route == "fast":
            result.origin = "fast"
            result.row_keys = frozenset(derivation.keys)
            return result
        result.origin = "agent"
        if fallback is None:
            return result
        result.fallback_ran = True
        agent_result = fallback(
            canticle=canticle,
            canto=canto,
            line_start=line_start,
            line_end=line_end,
        )
        keys, malformed, out_of_unit = candidate_keys(
            agent_result.candidate_rows, line_start, line_end
        )
        result.agent_result = agent_result
        result.row_keys = frozenset(keys)
        result.malformed_rows = malformed
        result.out_of_unit_rows = out_of_unit
        return result


# --- routing ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RoutePolicy:
    """What the fast path must guarantee before a unit skips the agent.

    Checks run in order; the first failed one names the reason. Toggling a
    check off changes only the routing decision — conflicting pairs always
    derive nothing at derivation time.
    """

    forbid_conflicts: bool = True
    require_rows: bool = True
    require_explicit_subjects: bool = True


@dataclass(frozen=True)
class RouteDecision:
    """`route` in {"fast", "agent"}; `reason` names the deciding check."""

    route: str
    reason: str  # "complete" | "conflicts" | "no_rows" | "pro_drop_suspects"

    def to_dict(self) -> dict:
        return {"route": self.route, "reason": self.reason}


def route_derivation(
    d: Derivation, policy: RoutePolicy | None = None
) -> RouteDecision:
    """Apply the policy checks, most severe first."""
    p = policy if policy is not None else RoutePolicy()
    if p.forbid_conflicts and d.conflicts:
        return RouteDecision("agent", "conflicts")
    if p.require_rows and not d.rows:
        return RouteDecision("agent", "no_rows")
    if p.require_explicit_subjects and d.pro_drop_suspects:
        return RouteDecision("agent", "pro_drop_suspects")
    return RouteDecision("fast", "complete")


@dataclass
class HybridResult:
    """Outcome of one hybrid unit execution."""

    unit: dict
    derivation: Derivation
    decision: RouteDecision
    origin: str = "fast"  # "fast" | "agent"
    fallback_ran: bool = False
    row_keys: frozenset[RowKey] = frozenset()
    malformed_rows: int = 0
    out_of_unit_rows: int = 0
    agent_result: object | None = None


# --- live fallback factory (operator-run; lazy imports per ARCHITECTURE.md §2) -----------


def agent_fallback(
    *,
    model: str | None = None,
    workflow: str = "unit",
    max_turns: int | None = None,
    verbose: bool = False,
    file=None,
    request_log=None,
) -> AgentFallback:
    """Build the live Tier-2 callable over `runner.agent.run_unit`.

    Everything model-facing imports lazily so importing this module never
    touches a network. One transport/toolkit pair serves all units (the
    benchmark pattern); `run_unit` resets the transport per session.
    `file`, when given (e.g. a status line's console stream per
    ARCHITECTURE.md §4), becomes llm7shi's streaming sink so streamed model
    output and retry countdowns share the caller's display instead of
    clobbering it; the default stays plain stderr. `request_log`, when given
    (an open UTF-8 JSONL sink), receives one `llm_request` / `llm_response`
    record pair per backend call (see `runner.agent.llm7shi_generate`).
    """
    from harness.runner.agent import DEFAULT_MODEL, SESSION_MAX_TURNS
    from harness.runner.agent import llm7shi_generate, run_unit as agent_run_unit
    from harness.runner.tools import GrammarToolkit, tool_specs
    from harness.toolcall import PromptXmlTransport

    model = DEFAULT_MODEL if model is None else model
    max_turns = SESSION_MAX_TURNS if max_turns is None else max_turns
    specs = tool_specs()

    def _run(*, canticle: str, canto: int, line_start: int, line_end: int):
        return agent_run_unit(
            transport=PromptXmlTransport(
                generate=llm7shi_generate(
                    model, quiet=not verbose, file=file, request_log=request_log
                )
            ),
            toolkit=GrammarToolkit(),
            canticle=canticle,
            canto=canto,
            line_start=line_start,
            line_end=line_end,
            specs=specs,
            max_turns=max_turns,
            workflow=workflow,
        )

    return _run


# --- artifact sources --------------------------------------------------------------------


@dataclass
class MinedArtifacts:
    """Rule table + lexicon regenerated fresh from the pooled run logs."""

    rules: list[SyntaxRule] = field(default_factory=list)
    entries: list[ValencyEntry] = field(default_factory=list)
    mine_stats: dict = field(default_factory=dict)
    lexicon_stats: dict = field(default_factory=dict)


def mine_artifacts(
    run_logs: list[Path] | None = None,
    *,
    min_support: int = DEFAULT_MIN_SUPPORT,
    min_precision: float = DEFAULT_MIN_PRECISION,
    min_consistency: float = DEFAULT_MIN_CONSISTENCY,
    progress_stream: TextIO | None = sys.stderr,
) -> MinedArtifacts:
    """Regenerate both fast-path artifacts deterministically (seconds)."""
    logs = list(run_logs) if run_logs is not None else list(DEFAULT_RUN_LOGS)
    bundle = MinedArtifacts()
    instances, stats = collect_instances(
        logs, progress_stream=progress_stream
    )
    bundle.rules, bundle.mine_stats = mine_rules(
        instances, min_support=min_support, min_precision=min_precision
    )
    valency_instances, vstats = collect_valency_instances(
        logs, progress_stream=None
    )
    bundle.entries, bundle.lexicon_stats = build_lexicon(
        valency_instances,
        min_support=min_support,
        min_consistency=min_consistency,
    )
    if progress_stream is not None:
        print(
            f"[hybrid_engine] artifacts regenerated: {len(bundle.rules)} rules, "
            f"{len(bundle.entries)} frames "
            f"(sessions {stats.sessions}, duplicates {stats.duplicate_sessions})",
            file=progress_stream,
            flush=True,
        )
    return bundle


def load_rules_json(path: Path) -> list[SyntaxRule]:
    """Reload a `syntax_miner --rules-out` artifact."""
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return [SyntaxRule(**raw) for raw in payload["rules"]]


def load_lexicon_json(path: Path) -> list[ValencyEntry]:
    """Reload a `lexicon_builder --lexicon-out` artifact."""
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return [ValencyEntry(**raw) for raw in payload["entries"]]


# --- deterministic evaluation probe (operator-side; reads gold) --------------------------


def iter_parse_units(
    canticles: list[str] | None = None,
    *,
    max_cantos: int | None = None,
    progress_stream: TextIO | None = sys.stderr,
    label: str = "hybrid_engine",
) -> Iterator[dict]:
    """Every parse unit (`dep.sentence_groups`) of the selected cantos.

    Production shape: the same iteration `reconstruct.py` will drive. Yields
    `{canticle, canto, line_start, line_end}` dicts.
    """
    from dante_corpus import api
    from dante_corpus.dep import sentence_groups

    canticles = list(canticles or DEFAULT_EVAL_CANTICLES)
    done = 0
    total = sum(len(api.cantos(c)) for c in canticles)
    if max_cantos is not None:
        total = min(total, max_cantos)
    for canticle in canticles:
        for canto in api.cantos(canticle):
            if max_cantos is not None and done >= max_cantos:
                return
            done += 1
            if progress_stream is not None and done % 5 == 0:
                print(
                    f"[{label}] units {done}/{total} cantos",
                    file=progress_stream,
                    flush=True,
                )
            data = api.canto(canticle, canto)
            for group in sentence_groups(
                [line.no for line in data.lines()],
                [line.text for line in data.lines()],
            ):
                yield {
                    "canticle": canticle,
                    "canto": canto,
                    "line_start": group[0],
                    "line_end": group[-1],
                }


@dataclass
class EngineReport:
    """Aggregated probe: routing shares plus gold-scored derivation quality."""

    units: int = 0
    routes: Counter = field(default_factory=Counter)
    reasons: Counter = field(default_factory=Counter)
    derived_rows: int = 0
    conflicts: int = 0
    pro_drop_suspects: int = 0
    tp: int = 0
    fp: int = 0
    fn: int = 0
    fast_tp: int = 0
    fast_fp: int = 0
    fast_fn: int = 0
    roles: dict = field(default_factory=dict)  # role -> [tp, fp, fn]
    coverage_target: float = COVERAGE_TARGET

    def observe(
        self,
        d: Derivation,
        decision: RouteDecision,
        gold: set[RowKey],
    ) -> tuple[int, int, int]:
        """Score one unit's derivation against its gold rows (operator-side)."""
        keys = d.keys
        u_tp, u_fp, u_fn = len(keys & gold), len(keys - gold), len(gold - keys)
        self.units += 1
        self.routes[decision.route] += 1
        self.reasons[decision.reason] += 1
        self.derived_rows += len(d.rows)
        self.conflicts += len(d.conflicts)
        self.pro_drop_suspects += len(d.pro_drop_suspects)
        self.tp += u_tp
        self.fp += u_fp
        self.fn += u_fn
        table = self.roles
        for key in keys:
            bucket = table.setdefault(key[2], [0, 0, 0])
            bucket[0 if key in gold else 1] += 1
        for key in gold - keys:
            table.setdefault(key[2], [0, 0, 0])[2] += 1
        if decision.route == "fast":
            self.fast_tp += u_tp
            self.fast_fp += u_fp
            self.fast_fn += u_fn
        return u_tp, u_fp, u_fn

    @property
    def fast_share(self) -> float:
        return self.routes["fast"] / self.units if self.units else 0.0

    @staticmethod
    def _micro(tp: int, fp: int, fn: int) -> dict:
        p = tp / (tp + fp) if tp + fp else 0.0
        r = tp / (tp + fn) if tp + fn else 0.0
        f = 2 * p * r / (p + r) if p + r else 0.0
        return {
            "precision": round(p, 4),
            "recall": round(r, 4),
            "f1": round(f, 4),
        }

    def metrics(self) -> dict:
        macro = (
            sum(
                self._micro(*counts)["f1"] for counts in self.roles.values()
            )
            / len(self.roles)
            if self.roles
            else 0.0
        )
        return {
            "units": self.units,
            "routes": dict(self.routes),
            "reasons": dict(self.reasons),
            "fast_share": round(self.fast_share, 4),
            "coverage_target": self.coverage_target,
            "derived_rows": self.derived_rows,
            "conflicts": self.conflicts,
            "pro_drop_suspects": self.pro_drop_suspects,
            "tp": self.tp,
            "fp": self.fp,
            "fn": self.fn,
            "role_micro": self._micro(self.tp, self.fp, self.fn),
            "role_macro_f1": round(macro, 4),
            "fast_path_micro": self._micro(self.fast_tp, self.fast_fp, self.fast_fn),
            "roles": {
                role: {
                    "tp": counts[0],
                    "fp": counts[1],
                    "fn": counts[2],
                    **self._micro(*counts),
                }
                for role, counts in sorted(self.roles.items())
            },
        }

    def summary(self) -> str:
        micro = self._micro(self.tp, self.fp, self.fn)
        fast = self._micro(self.fast_tp, self.fast_fp, self.fast_fn)
        gate = "PASS" if self.fast_share >= self.coverage_target else "MISS"
        lines = [
            f"units: {self.units}",
            f"routing: fast {self.routes['fast']} / agent {self.routes['agent']} "
            f"= fast-path share {self.fast_share:.3f} "
            f"(target >= {self.coverage_target:.2f}: {gate})",
            f"  reasons: "
            + ", ".join(
                f"{reason}={count}"
                for reason, count in sorted(self.reasons.items())
            ),
            f"derived rows: {self.derived_rows} "
            f"(conflicts {self.conflicts}, pro-drop suspects {self.pro_drop_suspects})",
            f"derivation quality: P={micro['precision']:.3f} R={micro['recall']:.3f} "
            f"F1={micro['f1']:.3f} (tp={self.tp} fp={self.fp} fn={self.fn})",
            f"fast-routed units only: P={fast['precision']:.3f} "
            f"R={fast['recall']:.3f} F1={fast['f1']:.3f}",
        ]
        top = sorted(
            self.roles.items(), key=lambda kv: -(kv[1][0] + kv[1][1] + kv[1][2])
        )[:8]
        if top:
            lines.append("top roles by gold support:")
            for role, counts in top:
                rm = self._micro(*counts)
                lines.append(
                    f"    {role}: P={rm['precision']:.3f} R={rm['recall']:.3f} "
                    f"F1={rm['f1']:.3f}"
                )
        return "\n".join(lines)


def evaluate_fast_path(
    engine: HybridEngine,
    *,
    canticles: list[str] | None = None,
    max_cantos: int | None = None,
    policy: RoutePolicy | None = None,
    progress_stream: TextIO | None = sys.stderr,
) -> tuple[EngineReport, Iterator[dict]]:
    """Probe the fast path corpus-wide against gold (operator-side).

    Returns the aggregate plus an iterator of per-unit records so the CLI can
    stream them into `--log` while the probe runs. Gold is read only here, in
    the evaluation face — never in `derive_unit`.
    """
    from dante_corpus.skel.io import load_skel

    active_policy = policy if policy is not None else RoutePolicy()
    report = EngineReport()

    def records():
        for unit in iter_parse_units(
            canticles,
            max_cantos=max_cantos,
            progress_stream=progress_stream,
        ):
            derivation = engine.derive_unit(
                unit["canticle"],
                unit["canto"],
                unit["line_start"],
                unit["line_end"],
            )
            decision = route_derivation(derivation, active_policy)
            gold = load_skel(unit["canticle"], unit["canto"])
            gold_keys = {
                (row.line, row.token, row.role, row.arg_line, row.arg_token)
                for no in range(unit["line_start"], unit["line_end"] + 1)
                for row in gold.get(no, ())
            }
            u_tp, u_fp, u_fn = report.observe(derivation, decision, gold_keys)
            yield {
                "record": "unit",
                **unit,
                **decision.to_dict(),
                "derived_rows": len(derivation.rows),
                "conflicts": len(derivation.conflicts),
                "pro_drop_suspects": len(derivation.pro_drop_suspects),
                "pairs_examined": derivation.pairs_examined,
                "attached_pairs": derivation.attached_pairs,
                "other_attachment_pairs": derivation.other_attachment_pairs,
                "unresolved_pairs": derivation.unresolved_pairs,
                "reinforced_pairs": derivation.reinforced_pairs,
                "tp": u_tp,
                "fp": u_fp,
                "fn": u_fn,
            }

    return report, records()


# --- CLI -----------------------------------------------------------------------------------


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Probe the hybrid fast path (mined rules + valency lexicon) over "
            "whole cantos (harness/extractor PLAN.md milestone 2.3)."
        )
    )
    parser.add_argument(
        "--rules-in",
        type=Path,
        help="load the rule table JSON instead of re-mining it",
    )
    parser.add_argument(
        "--lexicon-in",
        type=Path,
        help="load the lexicon JSON instead of re-building it",
    )
    parser.add_argument(
        "--run-log",
        action="append",
        type=Path,
        dest="run_logs",
        help="input benchmark JSONL log for fresh mining (repeatable; "
        "defaults to the four M1.4/re-run logs under harness/)",
    )
    parser.add_argument("--min-support", type=int, default=DEFAULT_MIN_SUPPORT)
    parser.add_argument("--min-precision", type=float, default=DEFAULT_MIN_PRECISION)
    parser.add_argument(
        "--min-consistency", type=float, default=DEFAULT_MIN_CONSISTENCY
    )
    parser.add_argument(
        "--eval-canticle",
        action="append",
        choices=("inferno", "purgatorio", "paradiso"),
        dest="eval_canticles",
        help="restrict the probe to these canticles (default: all)",
    )
    parser.add_argument("--max-cantos", type=int, help="cap probe scope")
    parser.add_argument(
        "--log",
        type=Path,
        help="streaming JSONL output: one unit record per probed parse unit, "
        "summary record last (truncated on startup — deterministic probe)",
    )
    args = parser.parse_args(argv)

    if args.rules_in and args.lexicon_in:
        rules = load_rules_json(args.rules_in)
        entries = load_lexicon_json(args.lexicon_in)
        print(
            f"hybrid_engine: loaded {len(rules)} rules + {len(entries)} frames "
            f"from artifacts"
        )
    else:
        print("[hybrid_engine] regenerating artifacts from run logs...", file=sys.stderr, flush=True)
        bundle = mine_artifacts(
            args.run_logs,
            min_support=args.min_support,
            min_precision=args.min_precision,
            min_consistency=args.min_consistency,
        )
        rules, entries = bundle.rules, bundle.entries

    engine = HybridEngine(rules, entries)
    print(
        f"hybrid_engine: probing fast path "
        f"(canticles={args.eval_canticles or ['all']}, "
        f"max_cantos={args.max_cantos})"
    )
    print("[hybrid_engine] evaluating parse units...", file=sys.stderr, flush=True)
    report, records = evaluate_fast_path(
        engine,
        canticles=args.eval_canticles,
        max_cantos=args.max_cantos,
    )
    if args.log:
        # One-shot experiment mode (ARCHITECTURE.md §5): truncate on startup;
        # the trailing summary record is the completion marker.
        with open(args.log, "w", encoding="utf-8") as sink:
            for record in records:
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
    else:
        for _ in records:  # drain so the aggregate completes
            pass
    print(report.summary())
    return 0


if __name__ == "__main__":
    sys.exit(main())
