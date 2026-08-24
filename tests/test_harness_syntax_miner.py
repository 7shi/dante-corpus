"""Deterministic tests for the Stage 2 syntax pattern miner
(`harness/extractor/syntax_miner.py`, milestone 2.1).

No model calls anywhere: run logs are synthetic JSONL built around real frozen
artifacts (inferno 2), and coverage scopes itself to a couple of cantos. The
one integration test reads a capped slice of the real M1.4 log when present on
disk and skips otherwise (the logs are gitignored disk-only artifacts).
"""

import json
from pathlib import Path

import pytest

from dante_corpus.dep import DepRow, load_dep
from dante_corpus.morph import load_morph
from dante_corpus.skel.io import children_index, load_skel, morph_index

from harness.extractor import syntax_miner as sm

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


def _views(canticle="inferno", canto=2):
    dep = load_dep(canticle, canto)
    idx = {(r.line, r.token): r for rows in dep.values() for r in rows}
    return idx, morph_index(load_morph(canticle, canto)), children_index(dep)


# --- log parsing ------------------------------------------------------------------------


def test_iter_case_records_skips_torn_and_non_case(tmp_path):
    good = _case_record()
    log = tmp_path / "run.log"
    with open(log, "w", encoding="utf-8") as fh:
        fh.write(json.dumps({"record": "summary", "units": 1}) + "\n")
        fh.write(json.dumps(good, ensure_ascii=False) + "\n")
        fh.write('{"record": "case", "torn"\n')  # killed mid-write
        fh.write("\n")
    parsed = list(sm.iter_case_records([log]))
    assert len(parsed) == 1
    run_id, record = parsed[0]
    assert run_id == "run"
    assert record["unit"] == UNIT


def test_iter_case_records_missing_file_is_silent(tmp_path):
    assert list(sm.iter_case_records([tmp_path / "nope.log"])) == []


def test_collect_instances_dedupes_by_unit_workflow_timestamp(tmp_path):
    log = tmp_path / "run.log"
    _write_log(
        log,
        [
            _case_record(),
            _case_record(),  # identical session: duplicate
            _case_record(timestamp="2026-08-24T09:00:00+00:00"),  # re-run: kept
            _case_record(workflow="predicate"),  # other workflow: kept
        ],
    )
    _, stats = sm.collect_instances([log], progress_stream=None)
    assert stats.sessions == 3
    assert stats.duplicate_sessions == 1


# --- supervision labels against the real gold artifact -----------------------------------


# Real gold rows of inferno 2:82-84 (cross-checked via load_skel).
GOLD_TP = [(82, 8, "obj", 82, 7)]  # guardi obj ti
PRO_DROP_TP = (82, 8, "subj", 0, 0)  # guardi pro-drop subj


def test_collect_instances_labels_tp_and_fp(tmp_path):
    log = tmp_path / "run.log"
    _write_log(
        log,
        [
            _case_record(
                missing=[],  # nothing correct withheld...
                extra=[(83, 3, "obl", 83, 6)],  # ...and one invented wrong row
            ),
        ],
    )
    # With an empty diff every gold row is a TP; add one FP from `extra`.
    instances, stats = sm.collect_instances([log], progress_stream=None)
    by_ok = {inst.ok: [] for inst in instances}
    for inst in instances:
        by_ok.setdefault(inst.ok, []).append(inst)
    gold = load_skel("inferno", 2)
    expected_tp = {
        (r.line, r.token, r.role, r.arg_line, r.arg_token)
        for no in range(82, 85)
        for r in gold.get(no, ())
    }
    pro_drops = [k for k in expected_tp if k[3:] == (0, 0)]
    assert len(by_ok[True]) == len(expected_tp) - len(pro_drops)
    assert stats.rows_correct == len(expected_tp) - len(pro_drops)
    wrong = by_ok[False]
    assert len(wrong) == 1
    assert wrong[0].role == "obl"
    assert not wrong[0].ok
    assert by_ok[True]  # non-empty sanity


def test_pro_drop_rows_counted_never_clustered(tmp_path):
    log = tmp_path / "run.log"
    _write_log(
        log,
        [
            _case_record(
                missing=[(82, 8, "subj", 0, 0)],  # gold pro-drop missed -> still counted
                extra=[(82, 4, "subj", 0, 0)],  # invented pro-drop prediction
            ),
        ],
    )
    instances, stats = sm.collect_instances([log], progress_stream=None)
    assert all((inst.ctx is not None) for inst in instances)
    # (82,2) pro-drop stays a correct instance-side count; the missed (82,8)
    # never becomes one; the invented (82,4) prediction counts as wrong.
    assert stats.pro_drop_correct == 1
    assert stats.pro_drop_wrong == 1
    assert not any(i.role == "subj" and i.ctx is None for i in instances)


def test_unresolved_positions_counted_not_raised(tmp_path):
    log = tmp_path / "run.log"
    # A wrong row whose argument position has no L2/L4 rows anywhere.
    _write_log(log, [_case_record(extra=[(83, 3, "obl", 999, 1)])])
    instances, stats = sm.collect_instances([log], progress_stream=None)
    assert stats.unresolved == 1
    assert all(inst.ctx is not None for inst in instances)


# --- topology features --------------------------------------------------------------------


def test_pos_class_mapping():
    assert sm.pos_class("verb") == "verb"
    assert sm.pos_class("verb+pronoun") == "verb"
    assert sm.pos_class("proper noun") == "noun"
    assert sm.pos_class("relative pronoun") == "pronoun"
    assert sm.pos_class("participle") == "adjective"
    assert sm.pos_class("preposition+article") == "preposition+article"
    assert sm.pos_class("") == "other"


def test_attachment_walk():
    def row(line, token, deprel, head):
        return DepRow(line=line, token=token, word="", deprel=deprel,
                      head_line=head[0], head_token=head[1])

    pred = (1, 5)
    index = {
        (1, t): row(1, t, d, h)
        for t, d, h in [
            (7, "obj", pred),          # direct child of the predicate
            (8, "conj", (1, 7)),       # conjunct of the object
            (9, "conj", (1, 8)),       # second-hop conjunct
            (2, "amod", (1, 3)),       # unrelated branch
        ]
    }
    assert sm._attachment(index[(1, 7)], pred, index) == "direct"
    assert sm._attachment(index[(1, 8)], pred, index) == "conj"
    assert sm._attachment(index[(1, 9)], pred, index) == "conj"
    assert sm._attachment(index[(1, 2)], pred, index) == "other"


def test_row_context_features_on_real_unit():
    idx, mi, ci = _views()
    ctx = sm.RowContext.build(idx, mi, ci, (82, 8), (82, 7))
    assert ctx == sm.RowContext(
        pred_pos_class="verb",
        pred_deprel="acl:relcl",
        arg_attachment="direct",
        arg_deprel="obj",
        arg_pos_class="pronoun",  # ti: L2 tags the clitic as a pronoun
        case_lemma="",
    )
    assert ctx.signature() == (
        "verb", "acl:relcl", "direct", "obj", "pronoun", ""
    )


def test_case_lemma_reads_the_preposition_child():
    idx, mi, ci = _views()
    ctx = sm.RowContext.build(idx, mi, ci, (82, 8), (83, 3))
    assert ctx.case_lemma == "di"  # de lo scender -> obl:di
    assert ctx.arg_deprel == "obl"


def test_row_context_build_returns_none_without_rows():
    idx, mi, ci = _views()
    assert sm.RowContext.build(idx, mi, ci, (82, 8), (999, 1)) is None
    assert sm.RowContext.build({}, {}, {}, (82, 8), (82, 7)) is None


# --- clustering & rules ---------------------------------------------------------------------


def _ctx(**overrides):
    fields = {
        "pred_pos_class": "verb",
        "pred_deprel": "root",
        "arg_attachment": "direct",
        "arg_deprel": "obj",
        "arg_pos_class": "noun",
        "case_lemma": "",
    }
    fields.update(overrides)
    return sm.RowContext(**fields)


def _inst(ctx, role, ok=True, run_id="r"):
    return sm.RowInstance(run_id=run_id, unit=("inferno", 2, 82, 84),
                          role=role, ok=ok, ctx=ctx)


def test_pure_cluster_becomes_rule():
    ctx = _ctx()
    rules, cluster_stats = sm.mine_rules(
        [_inst(ctx, "obj")] * 4 + [_inst(_ctx(arg_deprel="obl"), "obl:a")],
        min_support=3,
    )
    assert cluster_stats["clusters"] == 2
    assert len(rules) == 1
    rule = rules[0]
    assert rule.role == "obj"
    assert rule.support == 4
    assert rule.total == 4
    assert rule.precision == 1.0
    assert rule.matches(ctx) == "obj"
    assert rule.matches(_ctx(arg_deprel="obl")) is None


def test_competing_reading_poisons_the_signature():
    ctx = _ctx()
    rules, _ = sm.mine_rules(
        [_inst(ctx, "obj")] * 10 + [_inst(ctx, "obl:a", ok=False)],
        min_support=3,
    )
    assert rules == []  # 10/11 < 1.0 precision: no rule may claim this shape


def test_min_precision_relaxes_the_gate():
    ctx = _ctx()
    rules, _ = sm.mine_rules(
        [_inst(ctx, "obj")] * 9 + [_inst(ctx, "attr", ok=False)],
        min_support=3,
        min_precision=0.9,
    )
    assert len(rules) == 1
    assert rules[0].precision == round(9 / 10, 4)


def test_min_support_gate_keeps_rare_patterns_out():
    ctx = _ctx(case_lemma="a")
    rules, _ = sm.mine_rules([_inst(ctx, "obl:a")] * 2, min_support=3)
    assert rules == []


def test_load_rule_table_prefers_higher_precision():
    weak = sm.SyntaxRule(
        pred_pos_class="verb", pred_deprel="root", arg_attachment="direct",
        arg_deprel="obj", arg_pos_class="noun", case_lemma="",
        role="obj", support=5, total=6, precision=round(5 / 6, 4),
    )
    strong = sm.SyntaxRule(
        **{f: getattr(weak, f) for f in (
            "pred_pos_class", "pred_deprel", "arg_attachment", "arg_deprel",
            "arg_pos_class", "case_lemma")},
        role="obj", support=9, total=9, precision=1.0,
    )
    table = sm.load_rule_table([weak, strong])
    assert table[strong.signature()] is strong


def test_rules_to_records_and_write_json_roundtrip(tmp_path):
    rules, _ = sm.mine_rules([_inst(_ctx(), "obj")] * 4, min_support=3)
    path = tmp_path / "rules.json"
    sm.write_rules_json(path, rules)
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["record"] == "syntax_rules"
    assert payload["rules"] == [rule.to_dict() for rule in rules]
    records = list(sm.rules_to_records(rules))
    assert records[0]["record"] == "rule"
    assert records[0]["role"] == "obj"


# --- deterministic coverage --------------------------------------------------------------


def test_compute_coverage_partitions_the_gold_rows(tmp_path):
    log = tmp_path / "run.log"
    _write_log(log, [_case_record()])
    instances, _ = sm.collect_instances([log], progress_stream=None)
    rules, _ = sm.mine_rules(instances, min_support=1)
    report = sm.compute_coverage(
        rules, canticles=["inferno"], max_cantos=2, progress_stream=None
    )
    assert report.gold_rows == report.agree + report.conflict + report.unmatched
    assert report.agree >= 1  # inferno 2 shapes mined above reproduce on gold
    assert report.pro_drop >= 1
    assert 0.0 <= report.coverage_rate <= 1.0
    metrics = report.to_dict()
    assert metrics["gold_rows"] == report.gold_rows
    assert set(metrics["per_role"]) >= {"subj", "obj"}  # inferno 1-2 roles


def test_empty_rule_table_covers_nothing():
    report = sm.compute_coverage([], canticles=["inferno"], max_cantos=1,
                                 progress_stream=None)
    assert report.agree == 0
    assert report.conflict == 0
    assert report.gold_rows + report.pro_drop > 0


# --- report faces (ARCHITECTURE.md §6) ------------------------------------------------------


def test_mine_report_metrics_and_summary_shapes():
    report = sm.MineReport(min_support=3, min_precision=1.0)
    metrics = report.metrics()
    assert metrics["rules"] == 0
    assert metrics["coverage_rate"] if "coverage_rate" in metrics else True
    text = report.summary()
    assert "sessions: 0" in text
    assert "precision >= 1.00" in text


def test_mine_report_summary_includes_top_rules_and_coverage():
    rules, cluster_stats = sm.mine_rules([_inst(_ctx(), "obj")] * 4, min_support=3)
    coverage = sm.CoverageReport(agree=3, conflict=1, unmatched=5, pro_drop=2)
    report = sm.MineReport(
        stats=sm.InstanceStats(sessions=1, rows_correct=4),
        rules=rules,
        cluster_stats=cluster_stats,
        coverage=coverage,
    )
    text = report.summary()
    assert "rules: 1" in text
    assert "-> obj [4/4]" in text
    assert "corpus coverage: 3/9 gold rows = 0.333" in text
    assert report.metrics()["coverage"]["conflict"] == 1


# --- CLI end-to-end -------------------------------------------------------------------------


def test_cli_main_writes_streaming_log_with_summary_last(tmp_path):
    run_log = tmp_path / "bench-x.log"
    _write_log(run_log, [_case_record()])
    out_log = tmp_path / "mine.log"
    rules_out = tmp_path / "rules.json"
    exit_code = sm.main(
        [
            "--run-log", str(run_log),
            "--min-support", "1",
            "--rules-out", str(rules_out),
            "--log", str(out_log),
            "--coverage-canticle", "inferno",
            "--max-cantos", "2",
        ]
    )
    assert exit_code == 0
    lines = [json.loads(l) for l in out_log.read_text(encoding="utf-8").splitlines() if l]
    assert lines[-1]["record"] == "summary"  # completion marker
    assert all(r["record"] == "rule" for r in lines[:-1])
    assert lines[-1]["sessions"] == 1
    assert rules_out.exists()


@pytest.mark.skipif(
    not (REPO_LOGS / "bench-unit.log").exists(),
    reason="M1.4 run logs are gitignored disk-only artifacts",
)
def test_real_log_integration_capped():
    instances, stats = sm.collect_instances(
        [REPO_LOGS / "bench-unit.log"],
        max_sessions=10,
        progress_stream=None,
    )
    assert stats.sessions == 10
    assert stats.duplicate_sessions == 0
    assert stats.rows_correct > 50
    rules, cluster_stats = sm.mine_rules(instances)
    assert rules
    assert cluster_stats["instances_clustered"] == len(instances)
