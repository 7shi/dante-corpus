"""Deterministic tests for the Stage-6 soft repair levels
(`harness/extractor/fixlevel.py` and the `--fix` wiring around it).

No model calls anywhere: the CLI tests inject a stub fallback the way
`test_harness_reconstruct.py` does, and the session gate is exercised on the
toolkit directly. The level-1 target position is *located* rather than
hard-coded — gold scores 0 soft, so downgrading one `obl:<lemma>` row to bare
`obl` manufactures exactly one level-1 finding wherever the derivation
qualifies that oblique, and the test searches for the first such row.
"""

import dataclasses
import io
import json

import pytest

from dante_corpus.morph import Violation
from dante_corpus.skel.io import load_skel
from dante_corpus.skel.models import OBL_RE, SkelRow

from harness.extractor import fixlevel
from harness.extractor import reconstruct as rc
from harness.recon import check as recon_check
from harness.runner import prompts
from harness.runner.tools import GrammarToolkit


# --- helpers ------------------------------------------------------------------------------


def _violation(detail, **kw):
    return Violation(line=kw.pop("line", 1), kind=kw.pop("kind", "tag"),
                     detail=detail, **kw)


def _downgraded_rows(rows_by_line, target):
    """`rows_by_line` with `target`'s role replaced by bare `obl`."""
    out = {}
    for no, rows in rows_by_line.items():
        out[no] = [
            SkelRow(r.line, r.token, r.word, "obl", r.arg_line, r.arg_token)
            if (r.line, r.token, r.role, r.arg_line, r.arg_token) == target
            else r
            for r in rows
        ]
    return out


def _level1_target(canticle="inferno", canto=1):
    """Find a gold `obl:<lemma>` row whose downgrade yields one level-1 finding.

    Returns `(unit_group, row_key, downgraded_rows)`. Skips when the canto has
    none — the test is about the mechanism, not about this canto's inventory.
    """
    layers = rc.CantoLayers.load(canticle, canto)
    gold = load_skel(canticle, canto)
    for group in layers.units():
        rows = {no: list(gold.get(no, [])) for no in group}
        for row in [r for rs in rows.values() for r in rs]:
            if not OBL_RE.fullmatch(row.role):
                continue
            key = (row.line, row.token, row.role, row.arg_line, row.arg_token)
            candidate = _downgraded_rows(rows, key)
            hard, soft = rc._validate_rows(layers, group, candidate)
            if not hard and len(fixlevel.select(soft, 1)) == 1:
                return group, key, candidate
    pytest.skip(f"no level-1 target in {canticle} {canto}")


def _write_tsv(path, rows_by_line, nos):
    path.write_text(
        rc.render_tsv([(no, rows_by_line.get(no, [])) for no in sorted(nos)]),
        encoding="utf-8",
    )


class _StubResult:
    def __init__(self, rows):
        self.candidate_rows = rows


def _rows_payload(rows_by_line, line_start, line_end):
    return [
        {"line": r.line, "token": r.token, "role": r.role,
         "arg_line": r.arg_line, "arg_token": r.arg_token}
        for no in range(line_start, line_end + 1)
        for r in rows_by_line.get(no, [])
    ]


# --- the level table ----------------------------------------------------------------------


def test_level_1_selects_only_the_unqualified_oblique_direction():
    """The direction registry rule L does NOT excuse, and nothing else."""
    target = _violation("role_mismatch: 3.5 arg (3, 7) 'obl' vs 'obl:di'",
                        role="obl:di", given_role="obl", arg=(3, 7),
                        predicate=(3, 5))
    assert fixlevel.select([target], 1) == [target]

    # Rule L's own direction: a qualified label against a derived bare `obl`.
    excused = _violation("role_mismatch: 3.5 arg (3, 7) 'obl:di' vs 'obl'",
                         role="obl", given_role="obl:di", arg=(3, 7))
    # Other classes, and other role disagreements.
    others = [
        excused,
        _violation("role_mismatch: 3.5 arg (3, 7) 'obj' vs 'subj'",
                   role="subj", given_role="obj", arg=(3, 7)),
        _violation("missing_arg: 3.5 obl:di (3, 7)", role="obl:di", arg=(3, 7)),
        _violation("extra_arg: 3.5 obl (3, 7)", role="obl", arg=(3, 7)),
        _violation("missing_tuple: predicate 3.5 not proposed", predicate=(3, 5)),
        _violation("argument (3, 7) for role obl heads no NP/pronoun/predicate"),
        _violation("xcomp argument (3, 7) is not a predicate in this unit",
                   kind="clausal"),
    ]
    assert fixlevel.select(others, 1) == []


def test_levels_are_cumulative_and_bounded():
    assert fixlevel.classes_for(1) == (fixlevel.OBLIQUE_QUALIFICATION,)
    for level in range(1, fixlevel.MAX_LEVEL + 1):
        assert set(fixlevel.classes_for(level)) >= set(
            fixlevel.classes_for(level - 1) if level > 1 else ()
        )
    with pytest.raises(ValueError):
        fixlevel.classes_for(0)
    with pytest.raises(ValueError):
        fixlevel.classes_for(fixlevel.MAX_LEVEL + 1)


def test_violation_class_is_one_implementation_shared_with_the_stats_readout():
    cases = {
        "missing_arg: 3.5 obl:di (3, 7)": "missing_arg",
        "role_mismatch: 3.5 arg (3, 7) 'obl' vs 'obl:di'": "role_mismatch",
        "dual_role: 3.5 arg (3, 7) listed as 'obj', 'obl'": "dual_role",
        "argument (3, 7) for role obl heads no NP/pronoun/predicate": "membership",
        "role 'zzz' not in frozen vocabulary": "unknown_role",
    }
    for detail, expected in cases.items():
        v = _violation(detail)
        assert fixlevel.violation_class(v) == expected
        assert recon_check._violation_class(v) == expected


def test_resolve_level_accepts_numbers_and_the_max_aliases():
    """The drivers ask the level table how far repair reaches, rather than
    restating a number that would drift the moment a level is added."""
    assert fixlevel.resolve_level(1) == 1
    assert fixlevel.resolve_level("1") == 1
    for alias in fixlevel.MAX_ALIASES + ("MAX", " all "):
        assert fixlevel.resolve_level(alias) == fixlevel.MAX_LEVEL
    for bad in ("nope", "", 0, fixlevel.MAX_LEVEL + 1, None):
        with pytest.raises(ValueError):
            fixlevel.resolve_level(bad)


def test_cli_flags_take_max(tmp_path, monkeypatch):
    """Both drivers resolve `max` the same way, and report the level they ran."""
    assert recon_check.main(
        ["--canticle", "inferno", "--canto", "1", "--fix-level", "max"]
    ) == 0
    out = io.StringIO()
    results = recon_check.run(
        recon_check.Path(recon_check.__file__).parent,
        canticle="inferno", canto=1, stream=None,
    )
    recon_check.print_fix_level(results, fixlevel.MAX_LEVEL, stream=out)
    assert f"fix-level {fixlevel.MAX_LEVEL}:" in out.getvalue()

    tsv, layers, group, key, merged = _seed(tmp_path, monkeypatch)

    def fallback(**kw):
        return _StubResult(
            _rows_payload(merged, kw["line_start"], kw["line_end"])
        )

    argv = _fix_argv(tmp_path, tsv, level="max")
    assert rc.main(argv, fallback=fallback) == 0
    complete = next(
        json.loads(line)
        for line in (tmp_path / "recon.log").read_text(encoding="utf-8").splitlines()
        if json.loads(line).get("record") == "canto_complete"
    )
    assert complete["fix"]["level"] == fixlevel.MAX_LEVEL


def test_toolkit_flags_turn_the_levels_own_bar_on():
    assert fixlevel.toolkit_flags(1)["oblique_case_qualification"] is True


# --- what crosses into the session --------------------------------------------------------


def test_revision_block_shows_the_rows_and_the_invariant_not_the_answer():
    """The S5.5 line: the invariant and the frozen-layer evidence cross into the
    session; `derive_unit`'s own label never does."""
    group, key, rows = _level1_target()
    layers = rc.CantoLayers.load("inferno", 1)
    _hard, soft = rc._validate_rows(layers, group, rows)
    findings = fixlevel.select(soft, 1)
    block = fixlevel.revision_block(rows, findings, layers.dep_rows, 1)

    derived = findings[0].role  # e.g. "obl:di" — must NOT appear anywhere
    assert derived.startswith("obl:")
    assert derived not in block
    assert "vs" not in block.split("Reviewing")[1].split("Re-solve")[0]
    assert "case" in block and "Layer-2 lemma" in block
    # the recorded rows are there, as the artifact holds them
    assert "line\ttoken\tword\trole\targ_line\targ_token" in block
    assert f"{key[0]}\t{key[1]}\t" in block


def test_notice_does_not_claim_a_case_child_when_there_is_none():
    """4 of the corpus's 377 level-1 findings are oblique clitics with no `case`
    edge (`ci`/`ne` read as `obl:a`). The notice must describe *that* evidence,
    not report an empty case-child list — and still name no derived label."""
    v = _violation("role_mismatch: 87.4 arg (87, 3) 'obl' vs 'obl:a'",
                   line=87, role="obl:a", given_role="obl", arg=(87, 3),
                   predicate=(87, 4))
    notice = fixlevel.OBLIQUE_QUALIFICATION.notice(v, {})
    assert "obl:a" not in notice
    assert "case child" not in notice
    assert "case annex" in notice


def test_unit_task_appends_the_revision_block_and_is_unchanged_without_one():
    plain = prompts.unit_task("inferno", 1, 1, 4)
    assert prompts.unit_task("inferno", 1, 1, 4, revision=None) == plain
    with_block = prompts.unit_task("inferno", 1, 1, 4, revision="<revision>x</revision>")
    assert with_block.startswith(plain)
    assert with_block.endswith("<revision>x</revision>")


# --- the session gate ---------------------------------------------------------------------


def _validate(toolkit, rows, canticle="inferno", canto=1, line_start=1):
    return toolkit.validate_candidate(canticle, canto, line_start, rows)


def test_gate_rejects_a_bare_obl_whose_argument_carries_a_case_child():
    group, key, rows = _level1_target()
    line_start, line_end = group[0], group[-1]
    payload = _rows_payload(rows, line_start, line_end)

    off = _validate(GrammarToolkit(), payload, line_start=line_start)
    on = _validate(
        GrammarToolkit(oblique_case_qualification=True), payload,
        line_start=line_start,
    )
    assert off["valid"] is True
    assert on["valid"] is False
    assert any("case" in e and "obl" in e for e in on["errors"])
    # the gate names the invariant and the evidence, never the qualified label
    target_role = next(
        r.role for rs in load_skel("inferno", 1).values() for r in rs
        if (r.line, r.token, r.role, r.arg_line, r.arg_token) == key
    )
    assert all(target_role not in e for e in on["errors"])


def test_gate_is_silent_when_the_oblique_has_no_case_child():
    """Bare `obl` is correct for an oblique with no case marker — the invariant
    is one-directional, so the gate must not chase every bare `obl`."""
    toolkit = GrammarToolkit(oblique_case_qualification=True)
    gold = load_skel("inferno", 1)
    layers = rc.CantoLayers.load("inferno", 1)
    for group in layers.units():
        rows = {no: list(gold.get(no, [])) for no in group}
        bare = [
            r for rs in rows.values() for r in rs
            if r.role == "obl" and (r.arg_line, r.arg_token) != (0, 0)
            and not fixlevel.case_children(layers.dep_rows, (r.arg_line, r.arg_token))
        ]
        if not bare:
            continue
        result = _validate(
            toolkit, _rows_payload(rows, group[0], group[-1]), line_start=group[0]
        )
        assert all("case" not in e for e in result["errors"])
        return
    pytest.skip("inferno 1 has no case-less bare obl row")


# --- acceptance ---------------------------------------------------------------------------


def _soft(detail, **kw):
    return _violation(detail, **kw)


def test_fix_verdict_refuses_hard_no_improvement_and_a_new_class():
    before = [_soft("role_mismatch: 3.5 arg (3, 7) 'obl' vs 'obl:di'",
                    role="obl:di", given_role="obl", arg=(3, 7))]
    hard = [_violation("argument (3, 7) not in unit", kind="position")]

    assert rc.fix_verdict(before, hard, [], 1) == (False, "hard")
    assert rc.fix_verdict(before, [], before, 1) == (False, "no_improvement")

    traded = [_soft("missing_arg: 3.5 obl:di (3, 7)", role="obl:di", arg=(3, 7))]
    accepted, reason = rc.fix_verdict(before, [], traded, 1)
    assert accepted is False and reason.startswith("new_class:missing_arg")

    assert rc.fix_verdict(before, [], [], 1) == (True, "accepted")


def test_row_delta_names_the_mechanism():
    before = {1: [SkelRow(1, 2, "w", "obl", 1, 4), SkelRow(1, 2, "w", "subj", 0, 0)]}
    after = {1: [SkelRow(1, 2, "w", "obl:di", 1, 4), SkelRow(1, 2, "w", "obj", 1, 5)]}
    assert rc.row_delta(before, after) == {
        "rows_before": 2, "rows_after": 2,
        "rows_added": 1, "rows_removed": 1, "rows_relabelled": 1,
    }


# --- the CLI, end to end (stub fallback, no model) -----------------------------------------


def _case_record():
    """One mining input, in the shape `syntax_miner` expects (see
    `test_harness_reconstruct.py`); `--min-support 99` keeps it mining nothing."""
    return {
        "record": "case",
        "unit": {"canticle": "inferno", "canto": 2, "line_start": 82,
                 "line_end": 84},
        "workflow": "unit",
        "missing": [],
        "extra": [],
        "trace": {"timestamp": "2026-08-24T00:00:00+00:00"},
    }


def _write_log(path, records):
    path.write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in records) + "\n",
        encoding="utf-8",
    )


def _fix_argv(tmp_path, tsv, level=1):
    return [
        "--canticle", "inferno", "--canto", "1",
        "--run-log", str(tmp_path / "bench-x.log"),
        "--min-support", "99",
        "--log", str(tmp_path / "recon.log"),
        "--tsv", str(tsv),
        "--fix", str(level),
    ]


def _seed(tmp_path, monkeypatch):
    """A committed-style artifact carrying exactly one level-1 finding."""
    monkeypatch.setattr(rc, "HarnessStatusLine", None)
    _write_log(tmp_path / "bench-x.log", [_case_record()])
    layers = rc.CantoLayers.load("inferno", 1)
    gold = load_skel("inferno", 1)
    group, key, rows = _level1_target()
    merged = {no: list(gold.get(no, [])) for no in layers.nos}
    merged.update(rows)
    tsv = tmp_path / "01.tsv"
    _write_tsv(tsv, merged, layers.nos)
    return tsv, layers, group, key, merged


def test_fix_reopens_only_the_units_carrying_a_level_finding(tmp_path, monkeypatch):
    tsv, layers, group, key, merged = _seed(tmp_path, monkeypatch)
    calls = []

    def fallback(**kw):
        calls.append(kw)
        return _StubResult(
            _rows_payload(merged, kw["line_start"], kw["line_end"])
        )

    assert rc.main(_fix_argv(tmp_path, tsv), fallback=fallback) == 0
    assert [(c["line_start"], c["line_end"]) for c in calls] == [
        (group[0], group[-1])
    ]


def test_fix_replaces_the_units_rows_in_place_without_duplicating_lines(
    tmp_path, monkeypatch
):
    """Replacement, not delete-and-append: the repaired unit's lines are
    overwritten where they stand and the file stays in line order."""
    tsv, layers, group, key, merged = _seed(tmp_path, monkeypatch)
    gold = load_skel("inferno", 1)
    repaired = {no: list(gold.get(no, [])) for no in layers.nos}

    def fallback(**kw):
        return _StubResult(
            _rows_payload(repaired, kw["line_start"], kw["line_end"])
        )

    assert rc.main(_fix_argv(tmp_path, tsv), fallback=fallback) == 0

    text = tsv.read_text(encoding="utf-8")
    expected = rc.render_tsv(
        [(no, repaired.get(no, [])) for no in sorted(layers.nos)]
    )
    assert text == expected  # in line order, every line exactly once
    lines = [ln.split("\t")[0] for ln in text.splitlines()[1:]]
    assert lines == sorted(lines, key=int)


def test_fix_keeps_the_recorded_rows_when_the_answer_is_not_an_improvement(
    tmp_path, monkeypatch
):
    tsv, layers, group, key, merged = _seed(tmp_path, monkeypatch)
    before = tsv.read_text(encoding="utf-8")

    def useless_fallback(**kw):
        # the same (still-unqualified) rows back: no improvement
        return _StubResult(
            _rows_payload(merged, kw["line_start"], kw["line_end"])
        )

    assert rc.main(_fix_argv(tmp_path, tsv), fallback=useless_fallback) == 0
    assert tsv.read_text(encoding="utf-8") == before

    records = [
        json.loads(line)
        for line in (tmp_path / "recon.log").read_text(encoding="utf-8").splitlines()
    ]
    unit = next(
        r for r in records
        if r.get("record") == "unit" and r.get("line_start") == group[0]
    )
    assert unit["fix"] == {"level": 1, "verdict": "no_improvement"}
    complete = next(r for r in records if r.get("record") == "canto_complete")
    assert complete["fix"]["units"] == 1
    assert complete["fix"]["verdict:no_improvement"] == 1
    assert complete["fix"]["findings_before"] == complete["fix"]["findings_after"] == 1


def test_fix_summary_reports_the_mechanism_of_an_accepted_repair(
    tmp_path, monkeypatch
):
    tsv, layers, group, key, merged = _seed(tmp_path, monkeypatch)
    gold = load_skel("inferno", 1)
    repaired = {no: list(gold.get(no, [])) for no in layers.nos}

    def fallback(**kw):
        return _StubResult(
            _rows_payload(repaired, kw["line_start"], kw["line_end"])
        )

    assert rc.main(_fix_argv(tmp_path, tsv), fallback=fallback) == 0
    complete = next(
        json.loads(line)
        for line in (tmp_path / "recon.log").read_text(encoding="utf-8").splitlines()
        if json.loads(line).get("record") == "canto_complete"
    )
    stats = complete["fix"]
    assert stats["level"] == 1
    assert stats["verdict:accepted"] == 1
    assert stats["findings_before"] == 1 and stats["findings_after"] == 0
    # one label rewritten in place — no row added, none deleted
    assert stats["rows_relabelled"] == 1
    assert stats["rows_added"] == 0 and stats["rows_removed"] == 0


def test_fix_needs_an_artifact_and_a_known_level(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(rc, "HarnessStatusLine", None)
    _write_log(tmp_path / "bench-x.log", [_case_record()])
    base = [
        "--canticle", "inferno", "--canto", "1",
        "--run-log", str(tmp_path / "bench-x.log"), "--min-support", "99",
    ]
    with pytest.raises(SystemExit):
        rc.main(base + ["--fix", "1"])
    assert "--tsv" in capsys.readouterr().err
    with pytest.raises(SystemExit):
        rc.main(base + ["--tsv", str(tmp_path / "01.tsv"), "--fix", "99"])
    assert "level" in capsys.readouterr().err


def test_a_reopened_unit_never_takes_the_fast_path():
    """The derivation's own rows would clear the class by definition, so a fix
    unit must reach the model (`route_derivation`'s first check)."""
    from harness.extractor.hybrid_engine import (
        Derivation, RoutePolicy, route_derivation,
    )

    clean = Derivation(unit={})  # no conflicts, no schema violations
    lenient = RoutePolicy(require_rows=False, require_explicit_subjects=False)
    assert route_derivation(clean, lenient).route == "fast"
    decision = route_derivation(
        clean, dataclasses.replace(lenient, force_fallback=True)
    )
    assert (decision.route, decision.reason) == ("agent", "fix")
