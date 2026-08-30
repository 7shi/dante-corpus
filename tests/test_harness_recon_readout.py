"""Smoke tests for the Stage-4 corpus-wide log readout (`harness/recon/readout.py`).

Pure aggregation math against small synthetic in-memory record sets — no real
`harness/recon/*.log` files are read here (that path is exercised manually by
running the script, per its own docstring).
"""

import json

import pytest

from harness.recon import readout as ro


def _summary(canto, tp, fp, fn, wall=10.0, api_retry_seconds=0.0, cantos_passed=1, units=2, passed_units=1):
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    return {
        "record": "summary",
        "cantos": 1,
        "cantos_passed": cantos_passed,
        "written_cantos": 0,
        "units": units,
        "passed_units": passed_units,
        "token_assertion_errors": 0,
        "wall_clock_seconds": wall,
        "api_retry_seconds": api_retry_seconds,
        "gold": {"tp": tp, "fp": fp, "fn": fn, "precision": precision, "recall": recall, "f1": f1},
    }


def test_canticle_f1_aggregates_tp_fp_fn_not_mean_of_per_canto_f1():
    summaries = [_summary(1, tp=8, fp=2, fn=0), _summary(2, tp=0, fp=0, fn=10)]
    result = ro.canticle_f1(summaries)
    assert result["tp"] == 8
    assert result["fp"] == 2
    assert result["fn"] == 10
    # micro F1 over pooled counts, not the mean of the two per-canto F1s (1.0 and 0.0)
    assert 0.0 < result["f1"] < 1.0
    assert result["per_canto_min"] == 0.0
    assert result["per_canto_max"] == pytest.approx(8 / 9)  # 2*0.8*1.0/(0.8+1.0), canto 1's own f1


def test_gate_pass_report_counts_cantos_and_units_separately():
    summaries = [
        _summary(1, tp=1, fp=0, fn=0, cantos_passed=1, units=3, passed_units=3),
        _summary(2, tp=1, fp=0, fn=0, cantos_passed=0, units=3, passed_units=1),
    ]
    result = ro.gate_pass_report(summaries)
    assert result == {
        "cantos": 2,
        "cantos_passed": 1,
        "canto_pass_rate": 0.5,
        "units": 6,
        "passed_units": 4,
        "unit_pass_rate": 4 / 6,
    }


def test_rolling_max_sum_finds_the_60_second_peak_not_the_span_average():
    base = ro.parse_ts("2026-08-25T00:00:00+00:00")
    events = [
        (base, 100.0),
        (base + ro.timedelta(seconds=10), 100.0),
        (base + ro.timedelta(seconds=20), 100.0),
        (base + ro.timedelta(seconds=300), 5.0),  # isolated, far outside any 60s window with the burst
    ]
    assert ro.rolling_max_sum(events) == 300.0


def test_threshold_exceedances_counts_windows_over_the_stream_limit():
    base = ro.parse_ts("2026-08-25T00:00:00+00:00")
    events = [
        (base, 10_000.0),
        (base + ro.timedelta(seconds=10), 10_000.0),  # window sum 20,000 > 16,000 here
        (base + ro.timedelta(seconds=120), 1_000.0),  # isolated, well under limit
    ]
    result = ro.threshold_exceedances(events, ro.STREAM_TPM_LIMIT)
    assert result["windows"] == 3
    assert result["over_count"] == 1
    assert result["peak"] == 20_000.0


def test_tpm_report_flags_nonzero_paced_seconds_as_anomalies():
    requests = [
        {"timestamp": "2026-08-25T00:00:00+00:00", "paced_seconds": 0.0},
        {"timestamp": "2026-08-25T00:00:05+00:00", "paced_seconds": 1.5},
    ]
    responses = [
        {"timestamp": "2026-08-25T00:00:01+00:00", "total_tokens": 1000, "output_tokens": 200, "thought_tokens": 0},
    ]
    result = ro.tpm_report(requests, responses)
    assert len(result["paced_anomalies"]) == 1


def test_cap_report_only_counts_responses_with_positive_retries():
    responses = [
        {"canticle": "inferno", "canto": 1, "session": 1, "max_length_retries": 0, "output_bytes": 500},
        {"canticle": "inferno", "canto": 1, "session": 2, "max_length_retries": 2, "output_bytes": 114},
    ]
    result = ro.cap_report(responses)
    assert result["total_retries"] == 2
    assert result["triggered_sessions"] == {("inferno", 1, 2)}


def test_hygiene_report_flags_written_cantos_and_missing_tokens():
    corpus = ro.Corpus()
    corpus.add("inferno", [_summary(1, tp=1, fp=0, fn=0)])
    corpus.summaries["inferno"][0]["written_cantos"] = 1
    corpus.add(
        "inferno",
        [{"record": "llm_response", "empty": False, "input_tokens": None, "output_tokens": 1, "total_tokens": 1}],
    )
    result = ro.hygiene_report(corpus)
    assert len(result["written_cantos_nonzero"]) == 1
    assert len(result["responses_missing_tokens"]) == 1


def test_corpus_add_tags_summaries_with_their_canto_number():
    corpus = ro.Corpus()
    corpus.add("inferno", [_summary(1, tp=1, fp=0, fn=0)], canto=7)
    assert corpus.summaries["inferno"][0]["_canto"] == 7


def test_f1_outliers_returns_the_lowest_n_sorted_ascending():
    summaries = [_summary(1, tp=1, fp=0, fn=0)]  # f1 = 1.0
    summaries[0]["_canto"] = 1
    low = _summary(2, tp=1, fp=9, fn=9)
    low["_canto"] = 2
    summaries.append(low)
    outliers = ro.f1_outliers(summaries, n=2)
    assert [canto for canto, _ in outliers] == [2, 1]


def test_slow_units_returns_the_largest_fallback_seconds_max_first():
    a = _summary(1, tp=1, fp=0, fn=0)
    a["_canto"], a["fallback_seconds_max"] = 1, 50.0
    b = _summary(2, tp=1, fp=0, fn=0)
    b["_canto"], b["fallback_seconds_max"] = 2, 800.0
    outliers = ro.slow_units([a, b], n=2)
    assert [canto for canto, _ in outliers] == [2, 1]


def test_sum_counter_field_pools_dict_valued_summary_fields():
    summaries = [
        {"violation_kinds": {"tag": 3, "dup": 1}},
        {"violation_kinds": {"tag": 2, "position": 1}},
    ]
    result = ro.sum_counter_field(summaries, "violation_kinds")
    assert dict(result) == {"tag": 5, "dup": 1, "position": 1}


def test_cap_anomalies_only_flags_triggers_over_the_byte_threshold():
    responses = [
        {"max_length_retries": 1, "output_bytes": 115},  # expected small opener, not an anomaly
        {"max_length_retries": 1, "output_bytes": 550},  # far bigger than expected — anomalous
        {"max_length_retries": 0, "output_bytes": 9000},  # no trigger at all
    ]
    anomalies = ro.cap_anomalies(responses)
    assert len(anomalies) == 1
    assert anomalies[0]["output_bytes"] == 550


def test_api_retry_count_sums_summary_field():
    summaries = [_summary(1, tp=1, fp=0, fn=0), _summary(2, tp=1, fp=0, fn=0)]
    summaries[0]["api_retries"] = 3
    summaries[1]["api_retries"] = 5
    assert ro.api_retry_count(summaries) == 8


def test_peak_context_bytes_picks_the_largest_request():
    requests = [
        {"canticle": "inferno", "canto": 1, "session": 1, "messages": 4, "attempt": 1, "context_bytes": 5000},
        {"canticle": "inferno", "canto": 2, "session": 3, "messages": 4, "attempt": 1, "context_bytes": 21700},
        {"canticle": "inferno", "canto": 1, "session": 2, "messages": 4, "attempt": 1, "context_bytes": 9000},
    ]
    peak = ro.peak_context_bytes(requests)
    assert peak["context_bytes"] == 21700
    assert peak["canto"] == 2
    assert ro.peak_context_bytes([]) is None


def test_peak_context_bytes_joins_the_paired_response_by_namespaced_key():
    requests = [
        {"canticle": "inferno", "canto": 2, "session": 3, "messages": 4, "attempt": 1, "context_bytes": 21700},
    ]
    responses = [
        # same (session, messages, attempt) but a different canto — must NOT match (namespacing check)
        {"canticle": "inferno", "canto": 9, "session": 3, "messages": 4, "attempt": 1, "total_tokens": 999},
        {
            "canticle": "inferno",
            "canto": 2,
            "session": 3,
            "messages": 4,
            "attempt": 1,
            "input_tokens": 5000,
            "output_tokens": 800,
            "thought_tokens": 100,
            "total_tokens": 5900,
        },
    ]
    peak = ro.peak_context_bytes(requests, responses)
    assert peak["total_tokens"] == 5900


def test_format_duration_renders_d_hh_mm_ss():
    assert ro.format_duration(0) == "0:00:00:00"
    assert ro.format_duration(65) == "0:00:01:05"
    assert ro.format_duration(302_786) == "3:12:06:26"
    assert ro.format_duration(554_331) == "6:09:58:51"


def test_canto_duration_stats_computes_total_mean_min_max():
    summaries = [
        _summary(1, tp=1, fp=0, fn=0, wall=100.0),
        _summary(2, tp=1, fp=0, fn=0, wall=300.0),
        _summary(3, tp=1, fp=0, fn=0, wall=200.0),
    ]
    stats = ro.canto_duration_stats(summaries)
    assert stats == {"total": 600.0, "mean": 200.0, "min": 100.0, "max": 300.0, "n": 3}
    assert ro.canto_duration_stats([]) == {"total": 0.0, "mean": 0.0, "min": 0.0, "max": 0.0, "n": 0}


def test_is_complete_requires_summary_as_last_record():
    assert ro.is_complete([{"record": "unit"}, {"record": "summary"}]) is True
    assert ro.is_complete([{"record": "unit"}]) is False
    assert ro.is_complete([]) is False


def test_last_run_returns_the_whole_file_for_a_canto_run_once():
    records = [{"record": "unit"}, {"record": "unit"}, {"record": "summary"}]
    assert ro.last_run(records) == records
    # A torn tail (no summary at all) is still one attempt.
    assert ro.last_run(records[:2]) == records[:2]


def test_last_run_keeps_only_the_final_attempts_block():
    records = [
        {"record": "unit", "id": "stage4-a"},
        {"record": "unit", "id": "stage4-b"},
        {"record": "summary", "id": "stage4"},
        {"record": "unit", "id": "rerun-a"},
        {"record": "summary", "id": "rerun"},
    ]
    assert ro.last_run(records) == [
        {"record": "unit", "id": "rerun-a"},
        {"record": "summary", "id": "rerun"},
    ]


def test_last_run_keeps_the_last_of_three_attempts():
    records = [
        {"record": "summary", "id": "one"},
        {"record": "summary", "id": "two"},
        {"record": "unit", "id": "three-a"},
        {"record": "summary", "id": "three"},
    ]
    assert [r["id"] for r in ro.last_run(records)] == ["three-a", "three"]


def test_load_corpus_folds_one_attempt_per_log_and_flags_the_re_runs(tmp_path):
    """The append-only log's regression guard: a re-run canto must not count twice."""
    root = tmp_path
    for canticle, count in ro.CANTICLE_COUNTS.items():
        (root / canticle).mkdir()
        for n in range(1, count + 1):
            lines = [_summary(n, tp=1, fp=0, fn=0)]
            if (canticle, n) == ("inferno", 1):
                # Re-run since S5.5: the log holds Stage 4's block and the re-run's.
                lines = [_summary(n, tp=99, fp=99, fn=99), _summary(n, tp=1, fp=0, fn=0)]
            (root / canticle / f"{n:02d}.log").write_text(
                "".join(json.dumps(r) + "\n" for r in lines), encoding="utf-8"
            )

    corpus = ro.load_corpus(root)
    total = sum(ro.CANTICLE_COUNTS.values())
    assert len(corpus.all_summaries()) == total  # not total + 1
    assert corpus.resumed_logs == [root / "inferno" / "01.log"]
    assert ro.hygiene_report(corpus)["resumed_logs"] == corpus.resumed_logs
    # The discarded Stage-4 block's counts are nowhere in the aggregate.
    assert ro.canticle_f1(corpus.summaries["inferno"])["fp"] == 0
