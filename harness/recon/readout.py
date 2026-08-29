"""Stage-4 corpus-wide log readout: aggregates the 100 per-canto `harness/recon/<canticle>/NN.log`
JSONL streams (`../STAGE4.md` §5's closing act) into the hygiene, F1, gate-pass, TPM-pressure,
wall-clock, and cap-accounting numbers needed to write the closing ledger entry.

Deterministic and LLM-free: reads logs only, never launches `reconstruct.py`.

    uv run python -m harness.recon.readout [--root harness/recon]
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from statistics import median

CANTICLE_COUNTS = {"inferno": 34, "purgatorio": 33, "paradiso": 33}
# Established in STAGE3.md/STAGE4.md across four inferno-1 confirmation runs;
# purgatorio/paradiso have no prior band — this run establishes their baseline.
INFERNO_F1_BAND = (0.744, 0.796)
ROLLING_WINDOW_SECONDS = 60.0


def iter_log_paths(root: Path):
    for canticle, count in CANTICLE_COUNTS.items():
        for n in range(1, count + 1):
            yield canticle, n, root / canticle / f"{n:02d}.log"


def load_log(path: Path) -> list[dict]:
    records = []
    with path.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return records


def is_complete(records: list[dict]) -> bool:
    return bool(records) and records[-1].get("record") == "summary"


@dataclass
class Corpus:
    """Records grouped by canticle, keyed by kind. Populated from disk or, in tests, by hand."""

    summaries: dict[str, list[dict]] = field(default_factory=lambda: {c: [] for c in CANTICLE_COUNTS})
    requests: dict[str, list[dict]] = field(default_factory=lambda: {c: [] for c in CANTICLE_COUNTS})
    responses: dict[str, list[dict]] = field(default_factory=lambda: {c: [] for c in CANTICLE_COUNTS})
    missing_logs: list[Path] = field(default_factory=list)
    incomplete_logs: list[Path] = field(default_factory=list)

    def add(self, canticle: str, records: list[dict], canto: int | None = None) -> None:
        for r in records:
            kind = r.get("record")
            if kind == "summary":
                # The Stage 4 layout is one canto per log, but the summary record itself is a
                # Report.metrics() aggregate with no canto number — tag it from the file identity
                # so per-canto breakdowns (F1/slow-unit outliers) can name which canto they mean.
                r = dict(r)
                r["_canto"] = canto
                self.summaries[canticle].append(r)
            elif kind == "llm_request":
                self.requests[canticle].append(r)
            elif kind == "llm_response":
                self.responses[canticle].append(r)

    def all_summaries(self) -> list[dict]:
        return [s for lst in self.summaries.values() for s in lst]

    def all_requests(self) -> list[dict]:
        return [r for lst in self.requests.values() for r in lst]

    def all_responses(self) -> list[dict]:
        return [r for lst in self.responses.values() for r in lst]


def load_corpus(root: Path) -> Corpus:
    corpus = Corpus()
    for canticle, canto, path in iter_log_paths(root):
        if not path.exists():
            corpus.missing_logs.append(path)
            continue
        records = load_log(path)
        if not is_complete(records):
            corpus.incomplete_logs.append(path)
        corpus.add(canticle, records, canto=canto)
    return corpus


def hygiene_report(corpus: Corpus) -> dict:
    summaries = corpus.all_summaries()
    responses = corpus.all_responses()
    written = [s for s in summaries if s.get("written_cantos", 0) != 0]
    empty_responses = [r for r in responses if r.get("empty")]
    missing_tokens = [
        r
        for r in responses
        if r.get("input_tokens") is None or r.get("output_tokens") is None or r.get("total_tokens") is None
    ]
    return {
        "missing_logs": corpus.missing_logs,
        "incomplete_logs": corpus.incomplete_logs,
        "written_cantos_nonzero": written,
        "token_assertion_errors_total": sum(s.get("token_assertion_errors", 0) for s in summaries),
        "empty_responses": empty_responses,
        "responses_missing_tokens": missing_tokens,
    }


def canticle_f1(summaries: list[dict]) -> dict:
    tp = fp = fn = 0
    per_canto = []
    for s in summaries:
        gold = s.get("gold")
        if not gold:
            continue
        tp += gold["tp"]
        fp += gold["fp"]
        fn += gold["fn"]
        per_canto.append(gold["f1"])
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    per_canto.sort()
    return {
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "per_canto_min": per_canto[0] if per_canto else None,
        "per_canto_median": median(per_canto) if per_canto else None,
        "per_canto_max": per_canto[-1] if per_canto else None,
    }


def f1_outliers(summaries: list[dict], n: int = 3) -> list[tuple[int | None, float]]:
    """The n lowest-F1 cantos, named by canto number, for isolating a canto-level collapse."""
    rows = [(s.get("_canto"), s["gold"]["f1"]) for s in summaries if s.get("gold")]
    rows.sort(key=lambda row: row[1])
    return rows[:n]


def slow_units(summaries: list[dict], n: int = 3) -> list[tuple[int | None, float]]:
    """The n cantos with the largest single-unit fallback latency (`fallback_seconds_max`)."""
    rows = [(s.get("_canto"), s["fallback_seconds_max"]) for s in summaries if s.get("fallback_seconds_max")]
    rows.sort(key=lambda row: row[1], reverse=True)
    return rows[:n]


def sum_counter_field(summaries: list[dict], field_name: str) -> Counter:
    counter = Counter()
    for s in summaries:
        counter.update(s.get(field_name) or {})
    return counter


# S3.10/S3.11's own catch regenerated to a 114 B opener; STAGE4.md §4 expects the same rare,
# small-opener shape corpus-wide. A trigger regenerating to something much larger suggests the
# cap caught a different failure mode than the expected turn-1 over-pack.
CAP_ANOMALY_BYTES = 200


def cap_anomalies(responses: list[dict]) -> list[dict]:
    return [
        r
        for r in responses
        if r.get("max_length_retries", 0) > 0 and r.get("output_bytes", 0) > CAP_ANOMALY_BYTES
    ]


def gate_pass_report(summaries: list[dict]) -> dict:
    cantos = sum(s.get("cantos", 0) for s in summaries)
    cantos_passed = sum(s.get("cantos_passed", 0) for s in summaries)
    units = sum(s.get("units", 0) for s in summaries)
    passed_units = sum(s.get("passed_units", 0) for s in summaries)
    return {
        "cantos": cantos,
        "cantos_passed": cantos_passed,
        "canto_pass_rate": cantos_passed / cantos if cantos else 0.0,
        "units": units,
        "passed_units": passed_units,
        "unit_pass_rate": passed_units / units if units else 0.0,
    }


def parse_ts(s: str) -> datetime:
    return datetime.fromisoformat(s)


# Provider per-process rate limit, confirmed operator-side: each concurrently running
# `make` stream (one process per canticle) is metered independently by the provider — it is
# NOT a single quota shared across streams — so this threshold applies per canticle/stream,
# never to a cross-canticle merged timeline. The operator dropped the launch from 3-way to
# 2-way parallelism mid-run after repeatedly exceeding it on a single stream.
STREAM_TPM_LIMIT = 16_000


def rolling_window_sums(
    events: list[tuple[datetime, float]], window_seconds: float = ROLLING_WINDOW_SECONDS
) -> list[float]:
    """Trailing window sum ending at each event, in timestamp order."""
    events = sorted(events, key=lambda e: e[0])
    window = timedelta(seconds=window_seconds)
    running = 0.0
    j = 0
    sums = []
    for i in range(len(events)):
        running += events[i][1]
        while events[i][0] - events[j][0] > window:
            running -= events[j][1]
            j += 1
        sums.append(running)
    return sums


def rolling_max_sum(events: list[tuple[datetime, float]], window_seconds: float = ROLLING_WINDOW_SECONDS) -> float:
    sums = rolling_window_sums(events, window_seconds)
    return max(sums) if sums else 0.0


def threshold_exceedances(
    events: list[tuple[datetime, float]], threshold: float, window_seconds: float = ROLLING_WINDOW_SECONDS
) -> dict:
    sums = rolling_window_sums(events, window_seconds)
    over = [s for s in sums if s > threshold]
    return {
        "windows": len(sums),
        "over_count": len(over),
        "over_fraction": len(over) / len(sums) if sums else 0.0,
        "peak": max(sums) if sums else 0.0,
    }


def tpm_report(requests: list[dict], responses: list[dict]) -> dict:
    total_events = [
        (parse_ts(r["timestamp"]), r["total_tokens"]) for r in responses if r.get("total_tokens") is not None
    ]
    generated_events = [
        (parse_ts(r["timestamp"]), (r.get("output_tokens") or 0) + (r.get("thought_tokens") or 0))
        for r in responses
    ]
    if total_events:
        span_seconds = (max(t for t, _ in total_events) - min(t for t, _ in total_events)).total_seconds()
    else:
        span_seconds = 0.0
    span_avg_total_tpm = sum(v for _, v in total_events) / span_seconds * 60 if span_seconds else 0.0
    span_avg_generated_tpm = sum(v for _, v in generated_events) / span_seconds * 60 if span_seconds else 0.0
    paced_anomalies = [r for r in requests if (r.get("paced_seconds") or 0.0) != 0.0]
    return {
        "span_seconds": span_seconds,
        "span_avg_total_tpm": span_avg_total_tpm,
        "span_avg_generated_tpm": span_avg_generated_tpm,
        "peak_total_tpm": rolling_max_sum(total_events),
        "peak_generated_tpm": rolling_max_sum(generated_events),
        "paced_anomalies": paced_anomalies,
        "total_over_limit": threshold_exceedances(total_events, STREAM_TPM_LIMIT),
    }


def retry_tax_percent(summaries: list[dict]) -> float:
    retry_seconds = sum(s.get("api_retry_seconds") or 0.0 for s in summaries)
    wall_seconds = sum(s.get("wall_clock_seconds") or 0.0 for s in summaries)
    return retry_seconds / wall_seconds * 100 if wall_seconds else 0.0


def api_retry_count(summaries: list[dict]) -> int:
    return sum(s.get("api_retries") or 0 for s in summaries)


def _wire_key(r: dict) -> tuple:
    # (session, messages, attempt) alone repeats across canto processes — see ARCHITECTURE.md §5 —
    # so canticle/canto namespace it before any request/response join.
    return (r.get("canticle"), r.get("canto"), r.get("session"), r.get("messages"), r.get("attempt"))


def peak_context_bytes(requests: list[dict], responses: list[dict] | None = None) -> dict | None:
    """The single largest transcript ever sent, plus its paired response's token counts if available."""
    with_context = [r for r in requests if r.get("context_bytes") is not None]
    if not with_context:
        return None
    peak = dict(max(with_context, key=lambda r: r["context_bytes"]))
    if responses is not None:
        response_by_key = {_wire_key(r): r for r in responses}
        matched = response_by_key.get(_wire_key(peak))
        if matched is not None:
            peak["input_tokens"] = matched.get("input_tokens")
            peak["output_tokens"] = matched.get("output_tokens")
            peak["thought_tokens"] = matched.get("thought_tokens")
            peak["total_tokens"] = matched.get("total_tokens")
    return peak


def format_duration(seconds: float) -> str:
    total = int(round(seconds))
    days, rem = divmod(total, 86400)
    hours, rem = divmod(rem, 3600)
    minutes, secs = divmod(rem, 60)
    return f"{days}:{hours:02d}:{minutes:02d}:{secs:02d}"


def wall_clock_seconds(summaries: list[dict]) -> float:
    return sum(s.get("wall_clock_seconds") or 0.0 for s in summaries)


def canto_duration_stats(summaries: list[dict]) -> dict:
    """Per-canto wall-clock durations — each summary here is one canto's log (Stage 4 layout)."""
    durations = [s["wall_clock_seconds"] for s in summaries if s.get("wall_clock_seconds") is not None]
    if not durations:
        return {"total": 0.0, "mean": 0.0, "min": 0.0, "max": 0.0, "n": 0}
    return {
        "total": sum(durations),
        "mean": sum(durations) / len(durations),
        "min": min(durations),
        "max": max(durations),
        "n": len(durations),
    }


def corpus_observed_span(corpus: Corpus) -> timedelta:
    timestamps = [
        parse_ts(r["timestamp"])
        for lst in (corpus.all_requests(), corpus.all_responses(), corpus.all_summaries())
        for r in lst
        if r.get("timestamp")
    ]
    return max(timestamps) - min(timestamps) if timestamps else timedelta(0)


def cap_report(responses: list[dict]) -> dict:
    triggered = [r for r in responses if r.get("max_length_retries", 0) > 0]
    sessions = {(r["canticle"], r["canto"], r["session"]) for r in triggered}
    return {
        "total_retries": sum(r.get("max_length_retries", 0) for r in responses),
        "triggered_responses": triggered,
        "triggered_sessions": sessions,
    }


def print_report(corpus: Corpus) -> None:
    print("=== Hygiene ===")
    hygiene = hygiene_report(corpus)
    for label, key in [
        ("missing logs", "missing_logs"),
        ("incomplete logs (no parseable summary)", "incomplete_logs"),
        ("summaries with written_cantos != 0", "written_cantos_nonzero"),
        ("responses marked empty", "empty_responses"),
        ("responses missing provider token counts", "responses_missing_tokens"),
    ]:
        n = len(hygiene[key])
        print(f"  {label}: {n}" + (f"  e.g. {hygiene[key][0]}" if n else ""))
    print(f"  token_assertion_errors (sum): {hygiene['token_assertion_errors_total']}")

    print("\n=== Per-canticle F1 (micro, aggregated tp/fp/fn) ===")
    all_summaries = corpus.all_summaries()
    for canticle in CANTICLE_COUNTS:
        f1r = canticle_f1(corpus.summaries[canticle])
        band_note = ""
        if canticle == "inferno":
            lo, hi = INFERNO_F1_BAND
            band_note = f"  [{'IN BAND' if lo <= f1r['f1'] <= hi else 'OUT OF BAND'} {lo}-{hi}]"
        print(
            f"  {canticle}: f1={f1r['f1']:.4f} p={f1r['precision']:.4f} r={f1r['recall']:.4f} "
            f"tp={f1r['tp']} fp={f1r['fp']} fn={f1r['fn']} "
            f"per-canto[min/median/max]={f1r['per_canto_min']:.4f}/{f1r['per_canto_median']:.4f}/{f1r['per_canto_max']:.4f}"
            f"{band_note}"
        )
    corpus_f1 = canticle_f1(all_summaries)
    print(f"  corpus-wide: f1={corpus_f1['f1']:.4f} p={corpus_f1['precision']:.4f} r={corpus_f1['recall']:.4f}")

    print("\n=== Lowest-F1 cantos (for isolating a canto-level collapse, §6) ===")
    for canticle in CANTICLE_COUNTS:
        outliers = f1_outliers(corpus.summaries[canticle])
        rendered = ", ".join(f"canto {canto} f1={f1:.4f}" for canto, f1 in outliers)
        print(f"  {canticle}: {rendered}")

    print("\n=== Gate-pass rates (informational — F1 above is the reliable judge) ===")
    for canticle in CANTICLE_COUNTS:
        g = gate_pass_report(corpus.summaries[canticle])
        print(
            f"  {canticle}: canto {g['cantos_passed']}/{g['cantos']} ({g['canto_pass_rate']:.1%}), "
            f"unit {g['passed_units']}/{g['units']} ({g['unit_pass_rate']:.1%})"
        )
    g = gate_pass_report(all_summaries)
    print(f"  corpus-wide: canto {g['cantos_passed']}/{g['cantos']}, unit {g['passed_units']}/{g['units']}")

    print("\n=== Violation kinds (pooled hard+soft, per §4 watch item: dup/position surface only here) ===")
    for canticle in CANTICLE_COUNTS:
        kinds = sum_counter_field(corpus.summaries[canticle], "violation_kinds")
        rendered = ", ".join(f"{k}={v}" for k, v in kinds.most_common())
        print(f"  {canticle}: {rendered}")
    print(f"  corpus-wide: {dict(sum_counter_field(all_summaries, 'violation_kinds'))}")

    print("\n=== Routing & reasons (fast-path vs agent-fallback coverage) ===")
    for canticle in CANTICLE_COUNTS:
        routes = sum_counter_field(corpus.summaries[canticle], "routes")
        reasons = sum_counter_field(corpus.summaries[canticle], "reasons")
        total = sum(routes.values())
        fast = routes.get("fast", 0)
        print(
            f"  {canticle}: routes={dict(routes)} (fast-path {fast}/{total} = {fast / total:.1%}), "
            f"reasons={dict(reasons)}"
        )
    all_routes = sum_counter_field(all_summaries, "routes")
    all_total = sum(all_routes.values())
    all_fast = all_routes.get("fast", 0)
    print(f"  corpus-wide: routes={dict(all_routes)} (fast-path {all_fast}/{all_total} = {all_fast / all_total:.1%})")

    print(f"\n=== TPM pressure (each stream/canticle is metered independently at {STREAM_TPM_LIMIT:,}/min) ===")
    for canticle in CANTICLE_COUNTS:
        t = tpm_report(corpus.requests[canticle], corpus.responses[canticle])
        over = t["total_over_limit"]
        print(
            f"  {canticle}: span_avg total={t['span_avg_total_tpm']:.0f}/min generated={t['span_avg_generated_tpm']:.0f}/min "
            f"peak(60s) total={t['peak_total_tpm']:.0f} generated={t['peak_generated_tpm']:.0f} "
            f"paced_seconds anomalies={len(t['paced_anomalies'])}"
        )
        print(
            f"    over {STREAM_TPM_LIMIT:,}/min: {over['over_count']}/{over['windows']} response-windows "
            f"({over['over_fraction']:.1%}), peak {over['peak']:.0f}/min "
            f"({over['peak'] / STREAM_TPM_LIMIT - 1:+.1%} over limit)"
        )
    print(
        "  corpus-wide (three-stream merge, informational throughput only — NOT quota-relevant, "
        "since each stream's limit is counted independently, not shared):"
    )
    t = tpm_report(corpus.all_requests(), corpus.all_responses())
    print(
        f"    span_avg total={t['span_avg_total_tpm']:.0f}/min "
        f"generated={t['span_avg_generated_tpm']:.0f}/min "
        f"peak(60s) total={t['peak_total_tpm']:.0f} generated={t['peak_generated_tpm']:.0f} "
        f"paced_seconds anomalies={len(t['paced_anomalies'])}"
    )
    for canticle in CANTICLE_COUNTS:
        tax = retry_tax_percent(corpus.summaries[canticle])
        retries = api_retry_count(corpus.summaries[canticle])
        print(f"  {canticle} api-retries (429 backoffs): {retries}  (tax {tax:.2f}%)")
    print(
        f"  corpus-wide api-retries (429 backoffs): {api_retry_count(all_summaries)}  "
        f"(tax {retry_tax_percent(all_summaries):.2f}%)"
    )

    print("\n=== Peak context (largest single request sent) ===")

    def _format_peak(peak: dict) -> str:
        tokens = (
            f"in={peak['input_tokens']} out={peak['output_tokens']} "
            f"thought={peak['thought_tokens']} total={peak['total_tokens']}"
            if "total_tokens" in peak
            else "no paired response found"
        )
        return f"{peak['context_bytes']:,} B  (canto {peak['canto']} session {peak['session']} attempt {peak['attempt']}, tokens: {tokens})"

    for canticle in CANTICLE_COUNTS:
        peak = peak_context_bytes(corpus.requests[canticle], corpus.responses[canticle])
        if peak is None:
            print(f"  {canticle}: no context_bytes recorded")
            continue
        print(f"  {canticle}: {_format_peak(peak)}")
    corpus_peak = peak_context_bytes(corpus.all_requests(), corpus.all_responses())
    if corpus_peak is not None:
        print(f"  corpus-wide ({corpus_peak['canticle']}): {_format_peak(corpus_peak)}")

    print("\n=== Wall clock (d:hh:mm:ss) ===")
    for canticle in CANTICLE_COUNTS:
        d = canto_duration_stats(corpus.summaries[canticle])
        print(
            f"  {canticle}: total={format_duration(d['total'])} over {d['n']} cantos, "
            f"mean={format_duration(d['mean'])} min={format_duration(d['min'])} max={format_duration(d['max'])}"
        )
    d = canto_duration_stats(all_summaries)
    print(
        f"  corpus-wide: total={format_duration(d['total'])} over {d['n']} cantos, "
        f"mean={format_duration(d['mean'])} min={format_duration(d['min'])} max={format_duration(d['max'])}"
    )
    compute_total = wall_clock_seconds(all_summaries)
    observed = corpus_observed_span(corpus)
    print(f"  corpus-wide compute-only sum: {format_duration(compute_total)}")
    print(f"  corpus-wide observed span (first to last timestamp): {format_duration(observed.total_seconds())}")
    # compute_total sums three concurrent streams' work, so it naturally exceeds the observed
    # wall span when parallelism is winning; this ratio isolates that effect, not "contention" —
    # a *rising* ratio across future runs (parallelism buying less) is what would flag contention.
    speedup = compute_total / observed.total_seconds() if observed.total_seconds() else 0.0
    print(f"  effective 3-stream parallelism: {speedup:.2f}x (compute-only sum / observed span)")

    print("\n=== Slowest single fallback call per canticle (fallback_seconds_max outliers) ===")
    for canticle in CANTICLE_COUNTS:
        outliers = slow_units(corpus.summaries[canticle])
        rendered = ", ".join(f"canto {canto} {format_duration(secs)}" for canto, secs in outliers)
        print(f"  {canticle}: {rendered}")

    print("\n=== Cap accounting (max_length_retries) ===")
    for canticle in CANTICLE_COUNTS:
        c = cap_report(corpus.responses[canticle])
        print(f"  {canticle}: retries={c['total_retries']} triggered_sessions={len(c['triggered_sessions'])}")
        for r in c["triggered_responses"]:
            anomaly = "  [ANOMALY: expected ~114 B opener]" if r.get("output_bytes", 0) > CAP_ANOMALY_BYTES else ""
            print(
                f"    canto {r['canto']} session {r['session']}: "
                f"{r['max_length_retries']} retries, final output_bytes={r['output_bytes']}{anomaly}"
            )
    c = cap_report(corpus.all_responses())
    anomalies = cap_anomalies(corpus.all_responses())
    print(
        f"  corpus-wide: retries={c['total_retries']} triggered_sessions={len(c['triggered_sessions'])}, "
        f"anomalous triggers (>{CAP_ANOMALY_BYTES} B): {len(anomalies)}"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).parent,
        help="directory holding <canticle>/NN.log (default: this script's own directory)",
    )
    args = parser.parse_args()
    corpus = load_corpus(args.root)
    print_report(corpus)


if __name__ == "__main__":
    main()
