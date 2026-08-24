"""Deterministic tests for the gated reconstruction pipeline
(`harness/extractor/reconstruct.py`, milestone 2.4).

No model calls anywhere. The pipeline runs over real frozen layers (inferno 1)
with stub agent fallbacks: one serving the gold rows verbatim proves a canto
can pass all three gates end to end, degraded/garbage stubs prove every gate
blocks. The execution face is tested adversarially against poisoned
`load_skel`; commit tests redirect the writer and hash machinery into
`tmp_path` so `skel/` is never touched. The one integration test re-mines a
capped slice of the real M1.4 logs when present on disk and skips otherwise.
"""

import hashlib
import json
from pathlib import Path

import pytest

from dante_corpus import hashes as hashes_module
from dante_corpus.skel import io as skel_io
from dante_corpus.skel.io import load_skel
from dante_corpus.skel.models import SkelRow

from harness.extractor import hybrid_engine as he
from harness.extractor import reconstruct as rc
from harness.extractor import syntax_miner as sm


# --- fixtures & helpers ------------------------------------------------------------------


class _StubResult:
    def __init__(self, rows):
        self.candidate_rows = rows


def _gold_keys(canticle="inferno", canto=1):
    return {
        (row.line, row.token, row.role, row.arg_line, row.arg_token)
        for rows in load_skel(canticle, canto).values() for row in rows
    }


def _gold_fallback(canticle="inferno", canto=1, drop=None):
    """Stub Tier-2 callable serving this canto's gold rows for any unit."""
    by_line = {}
    for line, rows in load_skel(canticle, canto).items():
        by_line[line] = [
            {"line": r.line, "token": r.token, "role": r.role,
             "arg_line": r.arg_line, "arg_token": r.arg_token}
            for r in rows
            if drop is None
            or (r.line, r.token, r.role, r.arg_line, r.arg_token) != drop
        ]

    def _run(*, canticle, canto, line_start, line_end):
        rows = [
            row
            for no in range(line_start, line_end + 1)
            for row in by_line.get(no, [])
        ]
        return _StubResult(rows)

    return _run


def _engine():
    return he.HybridEngine([], [])


def _patch_skel_target(monkeypatch, tmp_path, seed=None):
    """Redirect the writer and the skel content hash into tmp_path."""
    target = tmp_path / "skel" / "inferno" / "01.tsv"
    target.parent.mkdir(parents=True, exist_ok=True)

    def fake_path(canticle, number):
        return target

    monkeypatch.setattr(skel_io, "_artifact_path", fake_path)
    monkeypatch.setitem(hashes_module._ARTIFACT_PATH, "skel", fake_path)
    if seed is not None:
        target.write_bytes(seed)
    return target


# --- gate 1: token-stream assertion --------------------------------------------------------


def _build_rows(layers, keys):
    return rc.build_rows(keys, layers, 1, len(layers.nos))


def test_build_rows_anchor_words_on_layer1():
    layers = rc.CantoLayers.load("inferno", 1)
    rows, errors = _build_rows(layers, {(2, 2, "obl:in", 1, 2), (2, 2, "subj", 0, 0)})
    assert errors == []
    assert all(r.word == "ritrovai" for r in rows[2])  # L1 token at inferno 1.2.2
    assert [(r.role, r.arg_line, r.arg_token) for r in rows[2]] == [
        ("subj", 0, 0),  # canonical sort: the ∅ subject precedes real args
        ("obl:in", 1, 2),
    ]


def test_build_rows_flags_positions_outside_the_token_stream():
    layers = rc.CantoLayers.load("inferno", 1)
    rows, errors = _build_rows(
        layers,
        {(2, 99, "obj", 0, 0), (3, 6, "obj", 3, 99)},
    )
    assert rows == {}
    assert len(errors) == 2
    assert "Layer-1 token stream" in errors[0]
    assert "3.99" in errors[1]


def test_build_rows_flags_out_of_unit_predicate():
    layers = rc.CantoLayers.load("inferno", 1)
    _, errors = rc.build_rows({(999, 1, "subj", 0, 0)}, layers, 1, 5)
    assert errors == ["predicate 999.1 outside unit bounds"]


def test_build_rows_pro_drop_key_becomes_null_subject_row():
    layers = rc.CantoLayers.load("inferno", 1)
    rows, errors = _build_rows(layers, {(7, 3, "subj", 0, 0)})
    assert errors == []
    assert rows[7] == [SkelRow(7, 3, layers.tokens[7][2], "subj", 0, 0)]


def test_canto_layers_units_partition_every_line_once():
    layers = rc.CantoLayers.load("inferno", 1)
    seen = [no for group in layers.units() for no in group]
    assert seen == sorted(layers.nos)
    assert len(seen) == len(set(seen))


# --- gate 2: 0-soft verification -------------------------------------------------------------


def test_gold_rows_validate_clean_through_pipeline_wiring():
    from dante_corpus.skel.validate import validate_unit

    layers = rc.CantoLayers.load("inferno", 1)
    gold = load_skel("inferno", 1)
    for group in layers.units():
        unit_rows = {no: list(gold.get(no, ())) for no in group}
        violations = validate_unit(
            group,
            [layers.text_by_no[no] for no in group],
            unit_rows,
            morph_rows=layers.morph_rows,
            np_rows=layers.np_rows,
            dep_rows=layers.dep_rows,
            case_rows=layers.case_rows,
        )
        hard, soft = rc.split_violations(violations)
        assert hard == [], (group, [v.detail for v in hard])
        assert soft == [], (group, [v.detail for v in soft])


def test_split_violations_separates_hard_from_soft():
    """A duplicated row is a hard violation; a dropped argument row surfaces
    as a divergence (`tag`) — the drivers' soft class."""
    from dante_corpus.skel.validate import validate_unit

    layers = rc.CantoLayers.load("inferno", 1)
    group = next(g for g in layers.units() if 4 in g)
    gold = load_skel("inferno", 1)
    broken = {no: list(gold.get(no, ())) for no in group}
    broken[4].append(broken[4][1])  # duplicate a row -> hard "dup"
    broken[4].remove(
        next(r for r in broken[4]
             if r.token == 6 and r.role == "attr" and r.arg_token == 5)
    )  # drop an argument row -> soft missing_arg divergence
    violations = validate_unit(
        group,
        [layers.text_by_no[no] for no in group],
        broken,
        morph_rows=layers.morph_rows,
        np_rows=layers.np_rows,
        dep_rows=layers.dep_rows,
        case_rows=layers.case_rows,
    )
    hard, soft = rc.split_violations(violations)
    assert any(v.kind == "dup" for v in hard)
    assert any(v.detail.startswith(("missing_tuple", "missing_arg"))
               for v in soft)


# --- pipeline ---------------------------------------------------------------------------------


def test_reconstruct_with_gold_stub_passes_all_gates():
    recon = rc.reconstruct_canto(
        _engine(), "inferno", 1,
        fallback=_gold_fallback(), progress_stream=None,
    )
    assert recon.outcomes
    assert recon.passed
    assert all(o.passed for o in recon.outcomes)
    merged = {
        (r.line, r.token, r.role, r.arg_line, r.arg_token)
        for rows in recon.rows_by_line().values() for r in rows
    }
    assert merged == _gold_keys()


def test_execution_face_never_touches_gold(monkeypatch):
    fallback = _gold_fallback()  # reads gold BEFORE poisoning; data-only after

    def boom(*a, **kw):
        raise AssertionError("execution must not read gold skel/ artifacts")

    monkeypatch.setattr(skel_io, "load_skel", boom)
    monkeypatch.setattr(sm, "load_skel", boom)
    recon = rc.reconstruct_canto(
        _engine(), "inferno", 1, fallback=fallback, progress_stream=None
    )
    assert recon.passed


def test_dry_mode_blocks_every_agent_unit():
    recon = rc.reconstruct_canto(
        _engine(), "inferno", 1, fallback=None, progress_stream=None
    )
    assert recon.outcomes
    assert not recon.passed
    assert all(o.route == "agent" for o in recon.outcomes)
    assert all(not o.fallback_ran for o in recon.outcomes)
    assert all(o.row_keys == frozenset() for o in recon.outcomes)


def test_blocked_outcome_records_violation_samples():
    from collections import Counter

    recon = rc.reconstruct_canto(
        _engine(), "inferno", 1, fallback=None, progress_stream=None
    )
    outcome = next(o for o in recon.outcomes if o.hard or o.soft)
    record = outcome.to_dict()
    assert record["record"] == "unit"
    assert record["passed"] is False
    assert record["soft_violations"] + record["hard_violations"] > 0
    assert record["sample_violations"]
    assert record["violation_kinds"] == dict(
        Counter(v.kind for v in outcome.hard + outcome.soft)
    )


# --- commit: gate 3 ------------------------------------------------------------------------------


def test_commit_refuses_a_blocked_canto(monkeypatch, tmp_path):
    target = _patch_skel_target(monkeypatch, tmp_path)
    recon = rc.reconstruct_canto(
        _engine(), "inferno", 1, fallback=None, progress_stream=None
    )
    record = rc.commit(recon, progress_stream=None)
    assert record["wrote"] is False
    assert record["reason"] == "gates_failed"
    assert not target.exists()


def test_commit_writes_and_verifies_content_hash(monkeypatch, tmp_path):
    # Capture the stub's gold data BEFORE the writer/hash redirection, so it
    # serves real rows rather than reading the redirected target.
    fallback = _gold_fallback()
    seed = b"stale artifact bytes\n"
    target = _patch_skel_target(monkeypatch, tmp_path, seed=seed)
    recon = rc.reconstruct_canto(
        _engine(), "inferno", 1, fallback=fallback, progress_stream=None,
    )
    record = rc.commit(recon, progress_stream=None)
    assert record["wrote"] is True
    assert record["digest_verified"] is True
    assert record["rolled_back"] is False
    assert record["before_skel_hash"] == hashlib.sha256(seed).hexdigest()
    payload = target.read_text(encoding="utf-8")
    assert payload == rc.render_tsv(
        [(no, recon.rows_by_line().get(no, [])) for no in sorted(recon.nos)]
    )
    assert hashlib.sha256(target.read_bytes()).hexdigest() == \
        record["after_skel_hash"]
    # predicate-less lines land as sentinels, exactly like the frozen format
    assert payload.splitlines()[1] == "1\t0\t\t\t0\t0"


def test_commit_rolls_back_on_hash_mismatch(monkeypatch, tmp_path):
    fallback = _gold_fallback()  # capture data before redirection
    seed = b"previous committed bytes\n"
    target = _patch_skel_target(monkeypatch, tmp_path, seed=seed)
    recon = rc.reconstruct_canto(
        _engine(), "inferno", 1, fallback=fallback, progress_stream=None,
    )
    real_render = rc.render_tsv
    monkeypatch.setattr(
        rc, "render_tsv",
        lambda lines: real_render(lines) + "drifted extra byte\n",
    )
    record = rc.commit(recon, progress_stream=None)
    assert record["wrote"] is False
    assert record["reason"] == "hash_mismatch"
    assert record["rolled_back"] is True
    assert target.read_bytes() == seed  # previous artifact restored verbatim


def test_render_tsv_matches_write_skel_bytes(monkeypatch, tmp_path):
    """Parity pin: the gate's digest mirror and the canonical writer agree."""
    gold = load_skel("inferno", 1)  # read before redirection
    target = _patch_skel_target(monkeypatch, tmp_path)
    lines = [(no, list(gold.get(no, ()))) for no in sorted(gold)]
    rendered = rc.render_tsv(lines)
    skel_io.write_skel("inferno", 1, lines)
    assert target.read_text(encoding="utf-8") == rendered


# --- evaluation face: gold comparison --------------------------------------------------------------


def test_verify_against_gold_exact_for_gold_stub():
    recon = rc.reconstruct_canto(
        _engine(), "inferno", 1,
        fallback=_gold_fallback(), progress_stream=None,
    )
    report, records = rc.verify_against_gold(recon)
    drained = list(records)
    assert len(drained) == len(recon.outcomes)
    assert report.units == len(recon.outcomes)
    assert report.exact_units == report.units
    assert report.fp == 0 and report.fn == 0
    metrics = report.metrics()
    assert metrics["exact_rate"] == 1.0
    assert "exact units" in report.summary()


def test_verify_against_gold_counts_missing_rows():
    gold = load_skel("inferno", 1)
    victim = next(
        (row.line, row.token, row.role, row.arg_line, row.arg_token)
        for rows in gold.values() for row in rows
        if (row.line, row.arg_line, row.arg_token) != (row.line, 0, 0)
    )
    recon = rc.reconstruct_canto(
        _engine(), "inferno", 1,
        fallback=_gold_fallback(drop=victim), progress_stream=None,
    )
    report, records = rc.verify_against_gold(recon)
    list(records)
    assert report.fn >= 1
    assert report.exact_units < report.units
    assert report.tp > 0


# --- aggregate report faces -------------------------------------------------------------------------


def test_report_faces_aggregate_streamed_records():
    report = rc.ReconstructReport()
    unit_record = {
        "record": "unit", "canticle": "inferno", "canto": 1,
        "line_start": 1, "line_end": 5, "route": "agent", "reason": "no_rows",
        "passed": False, "token_assertion_errors": 1, "hard_violations": 1,
        "soft_violations": 2, "violation_kinds": {"tag": 2}, "fallback_seconds": 3.5,
    }
    report.add_unit(unit_record)
    report.add_unit({
        **unit_record,
        "passed": True,
        "token_assertion_errors": 0,
        "hard_violations": 0,
        "soft_violations": 0,
        "violation_kinds": {},
        "fallback_seconds": None,
    })
    report.add_gold({"record": "gold", "tp": 5, "fp": 1, "fn": 2, "exact": False})
    report.add_canto_complete(
        {"record": "canto_complete", "canticle": "inferno", "canto": 1,
         "units": 2, "passed": False}
    )
    report.add_canto_complete(
        {"record": "canto_complete", "canticle": "inferno", "canto": 2,
         "units": 1, "passed": True,
         "commit": {"wrote": True}}
    )
    metrics = report.metrics()
    assert metrics["units"] == 2 and metrics["passed_units"] == 1
    assert metrics["blocked_units"] == 1
    assert metrics["cantos_passed"] == 1
    assert metrics["written_cantos"] == 1
    assert metrics["token_assertion_errors"] == 1
    assert metrics["fallback_seconds_total"] == 3.5
    assert metrics["gold"]["tp"] == 5
    text = report.summary()
    assert "0 hard / 0 soft" in text
    assert "written 1" in text
    assert "gold comparison:" in text


# --- streaming log resume ------------------------------------------------------------------------------


def _write_log(path: Path, records) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        for record in records:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")


def test_completed_cantos_and_prepare_resume_split(tmp_path):
    done_unit = {"record": "unit", "canticle": "inferno", "canto": 1,
                 "line_start": 1, "line_end": 5, "passed": True}
    open_unit = {"record": "unit", "canticle": "inferno", "canto": 2,
                 "line_start": 1, "line_end": 4, "passed": False}
    records = [
        done_unit,
        {"record": "gold", "canticle": "inferno", "canto": 1, "tp": 1},
        {"record": "canto_complete", "canticle": "inferno", "canto": 1,
         "units": 1, "passed": True},
        open_unit,
        {"record": "summary", "units": 2},
    ]
    log = tmp_path / "recon.log"
    _write_log(log, records)
    loaded = rc.load_log(log)
    assert rc.completed_cantos(loaded) == {("inferno", 1)}
    replay, remaining = rc.prepare_resume(
        loaded, [("inferno", 1), ("inferno", 2)]
    )
    assert remaining == [("inferno", 2)]
    assert {r["record"] for r in replay} == {"unit", "gold", "canto_complete"}
    assert all(r.get("canto") == 1 for r in replay)

    # Compaction drops the summary AND the orphaned partial-canto records;
    # re-running canto 2 later must not double-count them.
    rc.compact_log(log, rc.completed_cantos(loaded))
    kept = rc.load_log(log)
    assert all(r.get("record") != "summary" for r in kept)
    assert all(r.get("canto") == 1 for r in kept)
    assert len(kept) == 3


# --- CLI end-to-end (injected fallback; never a live model) ------------------------------------------


def _case_record():
    return {
        "record": "case",
        "unit": {"canticle": "inferno", "canto": 2, "line_start": 82,
                 "line_end": 84},
        "workflow": "unit",
        "missing": [],
        "extra": [],
        "trace": {"timestamp": "2026-08-24T00:00:00+00:00"},
    }


def test_cli_main_streams_log_with_summary_last(tmp_path):
    run_log = tmp_path / "bench-x.log"
    out_log = tmp_path / "recon.log"
    _write_log(run_log, [_case_record()])
    exit_code = rc.main(
        [
            "--canticle", "inferno", "--canto", "1",
            "--run-log", str(run_log),
            "--min-support", "99",
            "--verify-gold",
            "--log", str(out_log),
        ],
        fallback=_gold_fallback(),
    )
    assert exit_code == 0
    lines = [
        json.loads(l)
        for l in out_log.read_text(encoding="utf-8").splitlines() if l.strip()
    ]
    assert lines[-1]["record"] == "summary"  # completion marker
    kinds = [record["record"] for record in lines[:-1]]
    assert kinds.count("unit") == 34
    assert kinds.count("gold") == 34
    assert kinds.count("canto_complete") == 1
    assert "commit" not in kinds  # dry-run default writes nothing
    summary = lines[-1]
    assert summary["units"] == 34
    assert summary["cantos_passed"] == 1
    assert summary["written_cantos"] == 0
    assert summary["gold"]["exact_rate"] == 1.0


def test_cli_write_refused_when_gates_block(tmp_path, monkeypatch):
    seed = b"protected gold stays\n"
    target = _patch_skel_target(monkeypatch, tmp_path, seed=seed)
    run_log = tmp_path / "bench-x.log"
    out_log = tmp_path / "recon.log"
    _write_log(run_log, [_case_record()])

    def garbage_fallback(*, canticle, canto, line_start, line_end):
        return _StubResult([
            {"line": line_start, "token": 1, "role": "hades",
             "arg_line": line_start, "arg_token": 2}
        ])

    exit_code = rc.main(
        [
            "--canticle", "inferno", "--canto", "1",
            "--run-log", str(run_log),
            "--min-support", "99",
            "--write",
            "--log", str(out_log),
        ],
        fallback=garbage_fallback,
    )
    assert exit_code == 0
    lines = [
        json.loads(l)
        for l in out_log.read_text(encoding="utf-8").splitlines() if l.strip()
    ]
    commits = [r for r in lines if r["record"] == "commit"]
    completes = [r for r in lines if r["record"] == "canto_complete"]
    assert commits and commits[-1]["wrote"] is False
    assert commits[-1]["reason"] == "gates_failed"
    assert completes and completes[-1]["passed"] is False
    assert lines[-1]["written_cantos"] == 0
    assert target.read_bytes() == seed  # protected artifact untouched


def test_cli_resume_skips_completed_cantos(tmp_path):
    run_log = tmp_path / "bench-x.log"
    out_log = tmp_path / "recon.log"
    _write_log(run_log, [_case_record()])
    calls = []

    def counting_fallback(**kw):
        calls.append(kw)
        return _StubResult([])

    argv = [
        "--canticle", "inferno", "--canto", "1",
        "--run-log", str(run_log),
        "--min-support", "99",
        "--log", str(out_log),
    ]
    assert rc.main(argv, fallback=counting_fallback) == 0
    first_calls = len(calls)
    assert first_calls == 34
    assert rc.main(argv, fallback=counting_fallback) == 0
    assert len(calls) == first_calls  # completed canto replayed, not re-run
    lines = [
        json.loads(l)
        for l in out_log.read_text(encoding="utf-8").splitlines() if l.strip()
    ]
    summaries = [r for r in lines if r["record"] == "summary"]
    assert len(summaries) == 1  # stale summary stripped atomically on resume
    assert lines[-1]["units"] == 34  # replayed records still aggregate


# --- integration over real mined artifacts ------------------------------------------------------------


@pytest.mark.skipif(
    not (Path(__file__).resolve().parent.parent / "harness"
         / "bench-unit-retry.log").exists(),
    reason="M1.4 run logs are gitignored disk-only artifacts",
)
def test_real_artifacts_reconstruction_is_gate_honest():
    bundle = he.mine_artifacts(progress_stream=None)
    engine = he.HybridEngine(bundle.rules, bundle.entries)
    recon = rc.reconstruct_canto(
        engine, "inferno", 1, fallback=None, progress_stream=None
    )
    assert len(recon.outcomes) == 34
    # Deterministic fast path alone cannot clear the 0-soft gate corpus-wide:
    # mined rules cover a fraction of each unit's derivation, so blocked
    # units are the honest majority and nothing may claim a pass it lacks.
    passed = sum(o.passed for o in recon.outcomes)
    assert passed < len(recon.outcomes)
    assert all(o.route in ("fast", "agent") for o in recon.outcomes)
    assert all(o.token_assertions == [] for o in recon.outcomes)
