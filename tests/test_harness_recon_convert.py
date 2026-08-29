"""Tests for the Stage-5 durability conversion (`harness/recon/convert.py`).

Synthetic per-canto logs written into `tmp_path`, converted against the real
frozen inferno-1 layers (the conversion re-anchors every row on the Layer-1
token stream, so it needs the genuine layers, not a stub). No real
`harness/recon/*.log` is read and nothing writes under `skel/`.
"""

import json

from harness.extractor.reconstruct import CantoLayers
from harness.recon import convert as cv


def _unit(line_start, line_end, row_keys, **extra):
    record = {
        "record": "unit",
        "canticle": "inferno",
        "canto": 1,
        "line_start": line_start,
        "line_end": line_end,
        "route": "agent",
        "reason": "pro_drop_suspects",
        "origin": "agent",
        "fallback_ran": True,
        "accepted_rows": len(row_keys),
        "row_keys": [list(key) for key in row_keys],
        "token_assertion_errors": 0,
        "assertions": [],
        "hard_violations": 0,
        "soft_violations": 0,
        "violation_kinds": {},
        "sample_violations": [],
        "passed": True,
        "fallback_seconds": 12.5,
    }
    record.update(extra)
    return record


def _log(tmp_path, records, canticle="inferno", canto=1):
    path = tmp_path / canticle / f"{canto:02d}.log"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(r) + "\n" for r in records), encoding="utf-8"
    )
    return path


def test_tsv_matches_gold_shape_and_covers_every_canto_line():
    records = [_unit(1, 3, [(2, 2, "subj", 0, 0), (2, 2, "obl:in", 1, 2)])]
    payload, stats = cv.convert_canto(records, "inferno", 1)
    lines = payload.splitlines()
    gold_header = (
        "\t".join(("line", "token", "word", "role", "arg_line", "arg_token"))
    )
    assert lines[0] == gold_header
    layers = CantoLayers.load("inferno", 1)
    # every canto line is represented: the two predicate rows on line 2 plus
    # one placeholder row for each of the other 135 lines.
    assert len(lines) - 1 == len(layers.nos) + 1
    assert lines[1] == "1\t0\t\t\t0\t0"
    assert "2\t2\tritrovai\tsubj\t0\t0" in lines
    assert stats["rows"] == 2
    assert stats["lines"] == len(layers.nos)


def test_word_column_is_re_anchored_on_layer1_not_trusted_from_the_log():
    # The log carries no word at all — only positions — so a wrong word cannot
    # survive into the artifact even in principle.
    records = [_unit(1, 3, [(2, 2, "subj", 0, 0)])]
    payload, _ = cv.convert_canto(records, "inferno", 1)
    layers = CantoLayers.load("inferno", 1)
    assert f"2\t2\t{layers.tokens[2][1]}\tsubj\t0\t0" in payload.splitlines()


def test_only_unit_records_feed_the_tsv():
    # Telemetry records share the log with the unit records but contribute no
    # rows: the TSV is the reconstruction, not the run's instrumentation.
    telemetry = [
        {"record": "gold", "canticle": "inferno", "canto": 1,
         "line_start": 1, "line_end": 3, "tp": 4, "fp": 2, "fn": 0},
        {"record": "llm_response", "canticle": "inferno", "canto": 1,
         "line_start": 1, "line_end": 3, "total_tokens": 115},
        {"record": "canto_complete", "canticle": "inferno", "canto": 1,
         "units": 1, "elapsed_seconds": 4.0},
        {"record": "summary", "cantos": 1, "units": 1},
    ]
    bare, _ = cv.convert_canto(
        [_unit(1, 3, [(2, 2, "subj", 0, 0)])], "inferno", 1
    )
    noisy, stats = cv.convert_canto(
        [_unit(1, 3, [(2, 2, "subj", 0, 0)])] + telemetry, "inferno", 1
    )
    assert noisy == bare
    assert stats["units"] == 1


def test_out_of_range_row_keys_are_dropped_and_reported():
    records = [_unit(1, 3, [(2, 2, "subj", 0, 0), (2, 999, "obj", 0, 0)])]
    payload, stats = cv.convert_canto(records, "inferno", 1)
    assert stats["rows"] == 1
    assert stats["accepted_row_keys"] == 2
    assert len(stats["token_assertion_errors"]) == 1
    assert "1-3:" in stats["token_assertion_errors"][0]
    assert "\tobj\t" not in payload


def test_later_unit_record_supersedes_an_earlier_one_for_the_same_span():
    records = [
        _unit(1, 3, [(2, 2, "subj", 0, 0)], passed=False),
        _unit(1, 3, [(2, 2, "obl:in", 1, 2)], passed=True),
    ]
    payload, stats = cv.convert_canto(records, "inferno", 1)
    assert stats["units"] == 1
    assert "\tsubj\t" not in payload
    assert "\tobl:in\t" in payload


def test_log_without_a_summary_record_is_flagged_but_still_converted():
    records = [_unit(1, 3, [(2, 2, "subj", 0, 0)])]
    _, stats = cv.convert_canto(records, "inferno", 1)
    assert stats["log_complete"] is False
    assert stats["rows"] == 1


def test_conversion_writes_only_the_tsv_beside_the_log(tmp_path):
    path = _log(tmp_path, [_unit(1, 3, [(2, 2, "subj", 0, 0)])])
    cv.convert_log(path, "inferno", 1, check=False)
    written = sorted(p.name for p in path.parent.iterdir())
    assert written == ["01.log", "01.tsv"]


def test_conversion_is_idempotent_and_check_mode_writes_nothing(tmp_path):
    path = _log(tmp_path, [_unit(1, 3, [(2, 2, "subj", 0, 0)])])
    first = cv.convert_log(path, "inferno", 1, check=False)
    assert first["changed"] is True

    tsv = path.with_suffix(".tsv").read_bytes()
    second = cv.convert_log(path, "inferno", 1, check=False)
    assert second["changed"] is False
    assert path.with_suffix(".tsv").read_bytes() == tsv

    checked = cv.convert_log(path, "inferno", 1, check=True)
    assert checked["status"] == "ok"
    assert checked["drift"] is False


def test_check_mode_reports_drift_without_repairing_it(tmp_path):
    path = _log(tmp_path, [_unit(1, 3, [(2, 2, "subj", 0, 0)])])
    cv.convert_log(path, "inferno", 1, check=False)
    tsv_path = path.with_suffix(".tsv")
    tsv_path.write_text("stale\n", encoding="utf-8")

    result = cv.convert_log(path, "inferno", 1, check=True)
    assert result["status"] == "drift"
    assert tsv_path.read_text(encoding="utf-8") == "stale\n"


def test_missing_log_is_skipped_not_fatal(tmp_path):
    result = cv.convert_log(tmp_path / "inferno" / "07.log", "inferno", 7, check=False)
    assert result["status"] == "missing_log"


def test_main_check_exits_nonzero_on_drift(tmp_path, monkeypatch):
    monkeypatch.setattr(cv, "CANTICLE_COUNTS", {"inferno": 1})
    path = _log(tmp_path, [_unit(1, 3, [(2, 2, "subj", 0, 0)])])
    assert cv.main(["--root", str(tmp_path)]) == 0
    assert cv.main(["--root", str(tmp_path), "--check"]) == 0
    path.with_suffix(".tsv").write_text("stale\n", encoding="utf-8")
    assert cv.main(["--root", str(tmp_path), "--check"]) == 1
