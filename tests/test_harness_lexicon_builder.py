"""Deterministic tests for the Stage 2 verb valency lexicon builder
(`harness/extractor/lexicon_builder.py`, milestone 2.2).

No model calls anywhere: run logs are synthetic JSONL built around real frozen
artifacts (inferno 2), and coverage scopes itself to a couple of cantos. The
one integration test reads a capped slice of the real M1.4 logs when present
on disk and skips otherwise (the logs are gitignored disk-only artifacts).
"""

import json
from pathlib import Path

import pytest

from harness.extractor import lexicon_builder as lb

REPO_LOGS = Path(__file__).resolve().parent.parent / "harness"

UNIT = {"canticle": "inferno", "canto": 2, "line_start": 82, "line_end": 84}


def _case_record(missing=(), extra=(), *, timestamp="2026-08-22T13:44:20+00:00",
                 workflow="unit", unit=None):
    return {
        "record": "case",
        "case_id": "hist-inf02-082",
        "category": "historical",
        "unit": dict(unit or UNIT),
        "workflow": workflow,
        "missing": [list(k) for k in missing],
        "extra": [list(k) for k in extra],
        "trace": {
            "record": "session",
            "unit": dict(unit or UNIT),
            "workflow": workflow,
            "timestamp": timestamp,
            "outcomes": [],
        },
    }


def _write_log(path: Path, records) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        for record in records:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")


def _inst(verb="guardare", prep="di", role="obl:di", ok=True, run_id="r"):
    return lb.ValencyInstance(
        run_id=run_id, unit=("inferno", 2, 82, 84), verb_lemma=verb,
        prep=prep, role=role, ok=ok,
    )


# --- prep normalization ---------------------------------------------------------------------


def test_norm_prep_handles_fusion_and_variants():
    assert lb.norm_prep("a+il") == "a"
    assert lb.norm_prep("di + i") == "di"
    assert lb.norm_prep("ver'") == "ver"
    assert lb.norm_prep("\u2019Ncontra") == "ncontra"
    assert lb.norm_prep("Di") == "di"
    assert lb.norm_prep("") == ""


# --- collection against the real gold artifact -----------------------------------------------


def test_collect_valency_instances_labels_scope_and_claims(tmp_path):
    log = tmp_path / "run.log"
    # Empty diff: every gold row is correct. The unit's gold has
    # guardare obl:di scender (in scope) and a bare-obl row without a case
    # child plus non-oblique rows (out of scope); add one invented wrong claim.
    _write_log(log, [_case_record(extra=[(82, 8, "obl:a", 83, 3)])])
    instances, stats = lb.collect_valency_instances([log], progress_stream=None)
    di = [i for i in instances if i.ok]
    wrong = [i for i in instances if not i.ok]
    # guardare +di observed correctly; the wrong obl:a claim keeps its label...
    assert [(i.verb_lemma, i.prep, i.role) for i in di] == [("guardare", "di", "obl:di")]
    assert len(wrong) == 1
    assert (wrong[0].verb_lemma, wrong[0].role) == ("guardare", "obl:a")
    # ...while its prep stays the UD-observable case lemma (di), so the poison
    # lands on the *claimed* pair 'a' during aggregation, never on (guardare, di).
    assert wrong[0].prep == "di"
    assert stats.rows_correct == 1
    assert stats.rows_wrong == 1
    assert stats.out_of_scope >= 1  # bare obl without case child + other roles


def test_collect_counts_unresolved_without_raising(tmp_path):
    log = tmp_path / "run.log"
    _write_log(log, [_case_record(extra=[(999, 9, "obl:a", 83, 6)])])
    instances, stats = lb.collect_valency_instances([log], progress_stream=None)
    assert not any(not i.ok for i in instances)  # the wrong row never resolved
    assert stats.unresolved == 1
    assert stats.rows_wrong == 0


def test_valency_stats_shape():
    stats = lb.ValencyStats(sessions=2, out_of_scope=7)
    assert stats.to_dict()["out_of_scope"] == 7
    assert stats.to_dict()["sessions"] == 2


# --- frame aggregation ------------------------------------------------------------------------


def test_pure_pair_becomes_frame():
    entries, cluster_stats = lb.build_lexicon(
        [_inst()] * 4 + [_inst(verb="andare", prep="a", role="obl:a")],
        min_support=3,
    )
    assert cluster_stats["pairs"] == 2
    assert len(entries) == 1
    entry = entries[0]
    assert (entry.verb_lemma, entry.prep, entry.role) == ("guardare", "di", "obl:di")
    assert entry.support == 4
    assert entry.total == 4
    assert entry.consistency == 1.0


def test_wrong_claim_poisons_its_own_suffix():
    entries, cluster_stats = lb.build_lexicon(
        [_inst()] * 10
        + [_inst(prep="di", role="obl:a", ok=False)],  # UD showed di, claimed a
        min_support=3,
    )
    by_pair = {(e.verb_lemma, e.prep): e for e in entries}
    # the claim refutes (guardare, a)...
    assert ("guardare", "a") not in by_pair or by_pair[("guardare", "a")].consistency < 1.0
    # ...and leaves the observed pair untouched at full consistency.
    assert by_pair[("guardare", "di")].total == 10
    assert cluster_stats["rejected_pairs"] >= 1


def test_mismatch_poisons_the_case_lemma_pair():
    # Correct obl:a rows whose UD case lemma says 'dinanzi': the observable
    # underdetermines the reading, so (guardare, dinanzi) may not become a frame.
    entries, _ = lb.build_lexicon(
        [_inst(prep="di")] * 5 + [_inst(prep="dinanzi", role="obl:a")],
        min_support=3,
    )
    assert all(e.prep != "dinanzi" for e in entries)


def test_adjunct_observation_poisons_the_pair():
    # Gold bare-obl verdict over a case-bearing phrase: negative evidence.
    entries, _ = lb.build_lexicon(
        [_inst()] * 5
        + [_inst(prep="di", role="obl", ok=True)],
        min_support=3,
    )
    assert entries == []  # 5/6 < 1.0


def test_min_support_gate_keeps_rare_pairs_out():
    entries, _ = lb.build_lexicon([_inst()] * 2, min_support=3)
    assert entries == []


def test_min_consistency_relaxes_the_gate():
    entries, _ = lb.build_lexicon(
        [_inst()] * 9 + [_inst(role="obl:di", ok=False)],
        min_support=3,
        min_consistency=0.9,
    )
    assert len(entries) == 1
    assert entries[0].consistency == round(9 / 10, 4)


def test_frames_to_records_and_write_json_roundtrip(tmp_path):
    entries, _ = lb.build_lexicon([_inst()] * 4, min_support=3)
    path = tmp_path / "lexicon.json"
    lb.write_lexicon_json(path, entries)
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["record"] == "verb_valency_lexicon"
    assert payload["entries"] == [entry.to_dict() for entry in entries]
    records = list(lb.frames_to_records(entries))
    assert records[0]["record"] == "frame"
    assert records[0]["role"] == "obl:di"


# --- deterministic coverage --------------------------------------------------------------------


def _entries_from_log(tmp_path):
    log = tmp_path / "run.log"
    _write_log(log, [_case_record()])
    instances, _ = lb.collect_valency_instances([log], progress_stream=None)
    return lb.build_lexicon(instances, min_support=1)[0]


def test_compute_coverage_partitions_gold_obl_rows(tmp_path):
    entries = _entries_from_log(tmp_path)
    report = lb.compute_coverage(
        entries, canticles=["inferno"], max_cantos=2, progress_stream=None
    )
    assert report.gold_rows == report.agree + report.conflict + report.unmatched
    # the mined guardare+di frame reproduces its own gold row on inferno 2
    assert report.agree >= 1
    assert report.per_prep["di"]["agree"] >= 1
    assert 0.0 <= report.coverage_rate <= 1.0
    metrics = report.to_dict()
    assert metrics["gold_obl_rows"] == report.gold_rows


def test_empty_lexicon_covers_nothing_but_counts_adjunct_side():
    report = lb.compute_coverage([], canticles=["inferno"], max_cantos=1,
                                 progress_stream=None)
    assert report.agree == 0
    assert report.conflict == 0
    assert report.adjunct_conflict == 0
    assert report.gold_rows + report.adjunct_unmatched > 0


# --- report faces (ARCHITECTURE.md §6) ----------------------------------------------------------


def test_lexicon_report_metrics_and_summary_shapes():
    report = lb.LexiconReport(min_support=3, min_consistency=1.0)
    metrics = report.metrics()
    assert metrics["entries"] == 0
    assert metrics["verbs"] == 0
    text = report.summary()
    assert "sessions: 0" in text
    assert "consistency >= 1.00" in text


def test_lexicon_report_summary_includes_top_frames_and_coverage():
    entries, cluster_stats = lb.build_lexicon([_inst()] * 4, min_support=3)
    coverage = lb.ValencyCoverageReport(agree=3, conflict=1, unmatched=5)
    report = lb.LexiconReport(
        stats=lb.ValencyStats(sessions=1, rows_correct=4),
        entries=entries,
        cluster_stats=cluster_stats,
        coverage=coverage,
    )
    text = report.summary()
    assert "frames: 1 entries over 1 verbs" in text
    assert "guardare +di -> obl:di [4/4]" in text
    assert "corpus coverage: 3/9 gold obl rows = 0.333" in text
    assert report.metrics()["coverage"]["conflict"] == 1


# --- CLI end-to-end ------------------------------------------------------------------------------


def test_cli_main_writes_streaming_log_with_summary_last(tmp_path):
    run_log = tmp_path / "bench-x.log"
    _write_log(run_log, [_case_record()])
    out_log = tmp_path / "lexicon.log"
    lexicon_out = tmp_path / "lexicon.json"
    exit_code = lb.main(
        [
            "--run-log", str(run_log),
            "--min-support", "1",
            "--lexicon-out", str(lexicon_out),
            "--log", str(out_log),
            "--coverage-canticle", "inferno",
            "--max-cantos", "2",
        ]
    )
    assert exit_code == 0
    lines = [json.loads(l) for l in out_log.read_text(encoding="utf-8").splitlines() if l]
    assert lines[-1]["record"] == "summary"  # completion marker
    assert all(r["record"] == "frame" for r in lines[:-1])
    assert lines[-1]["sessions"] == 1
    assert lexicon_out.exists()


@pytest.mark.skipif(
    not (REPO_LOGS / "bench-unit-retry.log").exists(),
    reason="M1.4 run logs are gitignored disk-only artifacts",
)
def test_real_log_integration_capped():
    instances, stats = lb.collect_valency_instances(
        [REPO_LOGS / "bench-unit-retry.log"],
        max_sessions=10,
        progress_stream=None,
    )
    assert stats.sessions == 10
    assert stats.duplicate_sessions == 0
    assert stats.out_of_scope > 0
    entries, _ = lb.build_lexicon(instances)
    assert isinstance(entries, list)
