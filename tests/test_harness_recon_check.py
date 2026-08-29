"""Tests for the Stage-5 addendum check (`harness/recon/check.py`).

Exercises the check against the real frozen inferno-1 gold TSV, byte-copied into `tmp_path`
(the recon TSVs are gold-format, so a genuine gold file stands in for one) — no
`harness/recon/*.tsv` on disk is touched and nothing writes under `skel/`.
"""

import io

from dante_corpus import skel
from harness.recon import check as ck


def _copy_gold(tmp_path, canticle="inferno", canto=1):
    gold = skel.artifact_path(canticle, canto).read_text(encoding="utf-8")
    path = tmp_path / canticle / f"{canto:02d}.tsv"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(gold, encoding="utf-8")
    return path


def test_gold_shaped_tsv_reports_zero_violations(tmp_path):
    _copy_gold(tmp_path)
    result = ck.check_canto("inferno", 1, tmp_path)
    assert result["status"] == "ok"
    assert result["hard"] == 0
    assert result["soft"] == 0
    assert result["missing"] == []


def test_missing_tsv_is_a_hard_violation_not_a_crash(tmp_path):
    result = ck.check_canto("inferno", 1, tmp_path)
    assert result["status"] == "missing"
    assert result["hard"] == 1


def test_word_mismatch_is_flagged_as_a_hard_violation(tmp_path):
    path = _copy_gold(tmp_path)
    path.write_text(
        path.read_text(encoding="utf-8").replace("ritrovai", "xxxxxxxx"),
        encoding="utf-8",
    )
    result = ck.check_canto("inferno", 1, tmp_path)
    assert result["status"] == "hard_violations"
    assert result["hard"] > 0
    assert any(v.kind == "word" for v in result["violations"])


def test_unknown_role_is_flagged_as_a_soft_violation_only(tmp_path):
    path = _copy_gold(tmp_path)
    path.write_text(
        path.read_text(encoding="utf-8").replace("\tobl:in\t", "\tbogus\t", 1),
        encoding="utf-8",
    )
    result = ck.check_canto("inferno", 1, tmp_path)
    assert result["status"] == "ok"  # soft-only violations don't fail the check
    assert result["hard"] == 0
    assert result["soft"] > 0
    assert any(v.kind == "tag" for v in result["violations"])


def test_stats_breaks_soft_violations_down_by_class(tmp_path):
    path = _copy_gold(tmp_path)
    path.write_text(
        path.read_text(encoding="utf-8").replace("\tobl:in\t", "\tbogus\t", 1),
        encoding="utf-8",
    )
    results = ck.run(tmp_path, canticle="inferno", canto=1, stream=None)
    buf = io.StringIO()
    ck.print_stats(results, stream=buf)
    out = buf.getvalue()
    assert "unknown_role" in out
    assert "stats complete: " in out
    assert "(0 hard)" in out


def test_main_stats_exits_zero_even_with_soft_violations(tmp_path, monkeypatch):
    monkeypatch.setattr(ck, "CANTICLE_COUNTS", {"inferno": 1})
    path = _copy_gold(tmp_path)
    path.write_text(
        path.read_text(encoding="utf-8").replace("\tobl:in\t", "\tbogus\t", 1),
        encoding="utf-8",
    )
    assert ck.main(["--root", str(tmp_path), "--stats"]) == 0


def test_run_and_main_over_a_single_canticle(tmp_path, monkeypatch):
    monkeypatch.setattr(ck, "CANTICLE_COUNTS", {"inferno": 1})
    _copy_gold(tmp_path)
    results = ck.run(tmp_path, stream=None)
    assert len(results) == 1
    assert results[0]["status"] == "ok"
    assert ck.main(["--root", str(tmp_path)]) == 0

    path = tmp_path / "inferno" / "01.tsv"
    path.write_text(
        path.read_text(encoding="utf-8").replace("ritrovai", "xxxxxxxx"),
        encoding="utf-8",
    )
    assert ck.main(["--root", str(tmp_path)]) == 1
