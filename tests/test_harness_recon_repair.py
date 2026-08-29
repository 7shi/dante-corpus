"""Tests for the Stage-5 deterministic repair (`harness/recon/repair.py`) and the
gold-agreement readout (`harness/recon/agree.py`).

Every case runs against a byte copy of the real frozen inferno-1 gold TSV in `tmp_path`
(the recon TSVs are gold-format, so a gold file stands in for one), mutated to inject the
divergence under test. Nothing under `harness/recon/` or `skel/` is touched.
"""

import io

from dante_corpus import skel
from dante_corpus.skel.models import SkelRow
from harness.recon import agree, repair


def _copy_gold(tmp_path, canticle="inferno", canto=1):
    gold = skel.artifact_path(canticle, canto).read_text(encoding="utf-8")
    path = tmp_path / canticle / f"{canto:02d}.tsv"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(gold, encoding="utf-8")
    return path


def _row(**kw):
    base = dict(line=1, token=2, word="ritrovai", role="obj", arg_line=1, arg_token=3)
    base.update(kw)
    return SkelRow(**base)


# --- rule classification -------------------------------------------------------------


def test_self_citing_argument_is_classified_as_self_arg():
    assert repair.classify(_row(arg_line=1, arg_token=2)) == "self_arg"


def test_non_subj_null_position_is_classified_as_null_nonsubj():
    assert repair.classify(_row(role="obj", arg_line=0, arg_token=0)) == "null_nonsubj"


def test_subj_may_use_the_null_position():
    assert repair.classify(_row(role="subj", arg_line=0, arg_token=0)) is None


def test_roleless_predicate_row_is_never_touched():
    """The schema registers an argument-less predicate as a role-less row at (0,0)."""
    assert repair.classify(_row(role="", arg_line=0, arg_token=0)) is None


def test_an_ordinary_argument_row_is_kept():
    assert repair.classify(_row()) is None


def test_emptied_predicates_are_reported_not_silently_dropped():
    rows = {1: [_row(role="obj", arg_line=1, arg_token=2)]}
    kept, counts, emptied = repair.repair_rows(rows)
    assert kept == {1: []}
    assert counts["self_arg"] == 1
    assert emptied == ["1.2"]


def test_a_predicate_keeping_one_row_is_not_reported_as_emptied():
    rows = {1: [_row(role="obj", arg_line=1, arg_token=2), _row(role="subj")]}
    _, _, emptied = repair.repair_rows(rows)
    assert emptied == []


# --- end-to-end over a canto ---------------------------------------------------------


def test_clean_gold_needs_no_repair(tmp_path):
    _copy_gold(tmp_path)
    result = repair.repair_canto("inferno", 1, tmp_path, check=False)
    assert result["status"] == "ok"
    assert result["changed"] is False
    assert sum(result["counts"].values()) == 0


def test_injected_self_citation_is_removed(tmp_path):
    path = _copy_gold(tmp_path)
    before = path.read_text(encoding="utf-8")
    path.write_text(before + "2\t2\tritrovai\tiobj\t2\t2\n", encoding="utf-8")
    result = repair.repair_canto("inferno", 1, tmp_path, check=False)
    assert result["counts"]["self_arg"] == 1
    assert path.read_text(encoding="utf-8") == before


def test_injected_non_subj_null_row_is_removed(tmp_path):
    path = _copy_gold(tmp_path)
    before = path.read_text(encoding="utf-8")
    path.write_text(before + "2\t2\tritrovai\tobj\t0\t0\n", encoding="utf-8")
    result = repair.repair_canto("inferno", 1, tmp_path, check=False)
    assert result["counts"]["null_nonsubj"] == 1
    assert path.read_text(encoding="utf-8") == before


def test_repair_clears_the_hard_violations_it_targets(tmp_path):
    from harness.recon import check as ck

    path = _copy_gold(tmp_path)
    path.write_text(
        path.read_text(encoding="utf-8")
        + "2\t2\tritrovai\tiobj\t2\t2\n2\t2\tritrovai\tobj\t0\t0\n",
        encoding="utf-8",
    )
    dirty = ck.check_canto("inferno", 1, tmp_path)
    assert {v.kind for v in dirty["violations"]} >= {"dup", "position"}

    repair.repair_canto("inferno", 1, tmp_path, check=False)
    assert ck.check_canto("inferno", 1, tmp_path)["hard"] == 0


def test_missing_tsv_is_skipped_not_a_crash(tmp_path):
    result = repair.repair_canto("inferno", 1, tmp_path, check=False)
    assert result["status"] == "missing_tsv"
    assert result["changed"] is False


def test_repair_is_idempotent(tmp_path):
    path = _copy_gold(tmp_path)
    path.write_text(
        path.read_text(encoding="utf-8") + "2\t2\tritrovai\tobj\t0\t0\n", encoding="utf-8"
    )
    repair.repair_canto("inferno", 1, tmp_path, check=False)
    settled = path.read_text(encoding="utf-8")
    second = repair.repair_canto("inferno", 1, tmp_path, check=False)
    assert second["changed"] is False
    assert path.read_text(encoding="utf-8") == settled


def test_check_mode_writes_nothing_and_reports_drift(tmp_path):
    path = _copy_gold(tmp_path)
    dirty = path.read_text(encoding="utf-8") + "2\t2\tritrovai\tobj\t0\t0\n"
    path.write_text(dirty, encoding="utf-8")
    result = repair.repair_canto("inferno", 1, tmp_path, check=True)
    assert result["status"] == "drift"
    assert path.read_text(encoding="utf-8") == dirty


def test_main_check_exits_non_zero_on_a_repairable_row(tmp_path, capsys):
    path = _copy_gold(tmp_path)
    path.write_text(
        path.read_text(encoding="utf-8") + "2\t2\tritrovai\tobj\t0\t0\n", encoding="utf-8"
    )
    code = repair.main(["--root", str(tmp_path), "--canticle", "inferno", "--canto", "1",
                        "--check"])
    assert code == 1
    assert "DRIFT" in capsys.readouterr().out


# --- the gold-agreement readout ------------------------------------------------------


def test_agreement_of_gold_with_itself_is_perfect(tmp_path):
    _copy_gold(tmp_path)
    overall, _ = agree.run(tmp_path, canticle="inferno", canto=1)
    assert overall["precision"] == 1.0
    assert overall["recall"] == 1.0
    assert overall["f1"] == 1.0


def test_a_spurious_row_costs_precision_but_not_recall(tmp_path):
    """The failure mode the violation counter alone cannot see, in miniature."""
    path = _copy_gold(tmp_path)
    clean, _ = agree.run(tmp_path, canticle="inferno", canto=1)
    path.write_text(
        path.read_text(encoding="utf-8") + "2\t2\tritrovai\tobj\t0\t0\n", encoding="utf-8"
    )
    dirty, _ = agree.run(tmp_path, canticle="inferno", canto=1)
    assert dirty["recall"] == clean["recall"]
    assert dirty["precision"] < clean["precision"]

    repair.repair_canto("inferno", 1, tmp_path, check=False)
    healed, _ = agree.run(tmp_path, canticle="inferno", canto=1)
    assert healed == clean


def test_a_dropped_gold_row_costs_recall(tmp_path):
    path = _copy_gold(tmp_path)
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    path.write_text("".join(lines[:2] + lines[3:]), encoding="utf-8")
    overall, _ = agree.run(tmp_path, canticle="inferno", canto=1)
    assert overall["recall"] < 1.0


def test_agreement_reports_zero_for_a_root_with_no_artifacts(tmp_path):
    overall, _ = agree.run(tmp_path, canticle="inferno", canto=1)
    assert overall["predicted"] == 0
    assert overall["gold"] > 0
    assert overall["f1"] == 0.0


def test_agreement_main_prints_the_corpus_line(tmp_path, capsys):
    _copy_gold(tmp_path)
    code = agree.main(["--root", str(tmp_path), "--canticle", "inferno", "--canto", "1"])
    assert code == 0
    assert "corpus-wide" in capsys.readouterr().out


def test_print_report_detail_lists_each_canticle(tmp_path):
    _copy_gold(tmp_path)
    overall, per_canticle = agree.run(tmp_path, canticle="inferno", canto=1)
    buf = io.StringIO()
    agree.print_report(overall, per_canticle, detail=True, stream=buf)
    assert "inferno" in buf.getvalue()
