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


def test_revision_block_states_the_acceptance_rule_without_stating_an_answer():
    """S6.6: the session is told how its answer will be judged (`fix_verdict`),
    which is its own situation — not the derivation's label, which never crosses.
    S6.5 measured why it matters: 15 of 74 units satisfied their own gate and were
    refused for a class they introduced elsewhere, unaware that was the rule."""
    group, key, rows = _level1_target()
    layers = rc.CantoLayers.load("inferno", 1)
    _hard, soft = rc._validate_rows(layers, group, rows)
    block = fixlevel.revision_block(
        rows, fixlevel.select(soft, 1), layers.dep_rows, 1
    )
    # the three refusals of `fix_verdict`, in the session's own words
    assert "breaks no schema rule" in block
    assert "settles the points listed" in block
    assert "no *kind* of problem this unit did not already have" in block
    # and the salvage fallback, so a partial answer is not a wasted one
    assert "only the rows the points name are taken from it" in block
    # still no derived label anywhere
    derived = fixlevel.select(soft, 1)[0].role
    assert derived.startswith("obl:") and derived not in block


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


def test_level_1_governs_exactly_the_row_its_finding_names():
    v = _soft("role_mismatch: 3.5 arg (3, 7) 'obl' vs 'obl:di'",
              role="obl:di", given_role="obl", predicate=(3, 5), arg=(3, 7))
    assert fixlevel.governed_keys([v], 1) == frozenset({(3, 5, 3, 7)})
    # a finding of no class at this level governs nothing
    assert fixlevel.governed_keys([_soft("missing_arg: 3.5 obj (3, 9)")], 1) == (
        frozenset()
    )


def test_salvage_takes_the_answer_only_at_the_governed_rows():
    prior = {
        1: [SkelRow(1, 2, "w", "obl", 1, 4), SkelRow(1, 2, "w", "subj", 0, 0)]
    }
    submitted = {
        1: [
            SkelRow(1, 2, "w", "obl:di", 1, 4),   # the repair: governed
            SkelRow(1, 2, "w", "obj", 1, 6),      # an addition: not governed
        ]
    }
    salvaged = rc.salvage_rows(prior, submitted, frozenset({(1, 2, 1, 4)}))
    assert sorted(
        (r.role, r.arg_line, r.arg_token) for r in salvaged[1]
    ) == [("obl:di", 1, 4), ("subj", 0, 0)]
    # neither added nor removed outside the governed keys
    delta = rc.row_delta(prior, salvaged)
    assert delta["rows_added"] == delta["rows_removed"] == 0
    assert delta["rows_relabelled"] == 1


def test_fix_diagnosis_names_the_dropped_argument_and_where_it_sat():
    """S6.7's unanswerable question, made answerable.

    All 15 of that run's `new_class` refusals were `missing_arg` — the answer
    dropped an argument — and the log could not say *which* one, nor whether the
    drop was on the row the level named (the level's own job done badly) or
    somewhere else in the unit (the ask being too wide). Both are recorded now,
    and this is the second shape: the repair landed on the governed row, and a
    different row of the unit went missing with it.
    """
    prior = {
        1: [
            SkelRow(1, 2, "w", "obl", 1, 4),    # the level's finding sits here
            SkelRow(1, 2, "w", "subj", 1, 1),   # collateral
        ]
    }
    submitted = {1: [SkelRow(1, 2, "w", "obl:di", 1, 4)]}
    before = [_soft("role_mismatch: 1.2 arg (1, 4) 'obl' vs 'obl:di'",
                    role="obl:di", given_role="obl",
                    predicate=(1, 2), arg=(1, 4))]
    after = [_soft("missing_arg: 1.2 subj (1, 1)",
                   role="subj", predicate=(1, 2), arg=(1, 1))]

    d = rc.fix_diagnosis(prior, submitted, before, [], after, 1)

    assert d["rows_removed"] == 1 and d["rows_relabelled"] == 1
    assert d["rows"]["removed"] == [
        {"predicate": [1, 2], "argument": [1, 1], "role": "subj",
         "governed": False},
    ]
    assert d["rows"]["relabelled"] == [
        {"predicate": [1, 2], "argument": [1, 4], "role": ["obl", "obl:di"],
         "governed": True},
    ]
    # the level's own row was answered; the class came from off-brief
    assert d["governed_rows"] == {
        "named": 1, "relabelled": 1, "removed": 0, "untouched": 0, "missing": 0,
    }
    assert d["findings_before"] == 1 and d["findings_after"] == 0
    assert [(v["class"], v["governed"]) for v in d["introduced"]] == [
        ("missing_arg", False)
    ]


def test_fix_diagnosis_marks_a_class_introduced_on_the_governed_row_itself():
    """The other shape: the answer moved the very row the level named."""
    prior = {1: [SkelRow(1, 2, "w", "obl", 1, 4)]}
    submitted = {1: [SkelRow(1, 2, "w", "obl:di", 1, 6)]}  # relabelled *and* moved
    before = [_soft("role_mismatch: 1.2 arg (1, 4) 'obl' vs 'obl:di'",
                    role="obl:di", given_role="obl",
                    predicate=(1, 2), arg=(1, 4))]
    after = [_soft("missing_arg: 1.2 obl:di (1, 4)",
                   role="obl:di", predicate=(1, 2), arg=(1, 4))]

    d = rc.fix_diagnosis(prior, submitted, before, [], after, 1)

    assert d["rows"]["removed"][0]["governed"] is True
    assert d["rows"]["added"][0]["governed"] is False
    assert d["governed_rows"]["removed"] == 1
    assert d["governed_rows"]["missing"] == 1  # the named row did not come back
    assert [(v["class"], v["governed"]) for v in d["introduced"]] == [
        ("missing_arg", True)
    ]


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
    assert unit["fix"]["level"] == 1
    assert unit["fix"]["verdict"] == "no_improvement"
    assert "unit_verdict" not in unit["fix"]
    # the rows on disk are the recorded ones, so the delta is all zeros …
    assert unit["fix"]["delta"]["rows_added"] == 0
    assert unit["fix"]["delta"]["rows_removed"] == 0
    assert unit["fix"]["delta"]["rows_relabelled"] == 0
    # … while the diagnosis is about the answer that was thrown away (S6.7):
    # it returned the record unchanged, so it left the governed row untouched
    # and introduced nothing.
    refused = unit["fix"]["refused"]
    assert refused["governed_rows"] == {
        "named": 1, "relabelled": 0, "removed": 0, "untouched": 1, "missing": 0,
    }
    assert refused["introduced"] == [] and refused["introduced_total"] == 0
    assert refused["findings_before"] == refused["findings_after"] == 1
    assert refused["salvage"] == "no_improvement"
    complete = next(r for r in records if r.get("record") == "canto_complete")
    assert complete["fix"]["units"] == 1
    assert complete["fix"]["verdict:no_improvement"] == 1
    assert complete["fix"]["findings_before"] == complete["fix"]["findings_after"] == 1


def _extra_row_that_trades_a_class(layers, group, rows, key):
    """A row the unit did not carry that costs the whole answer its acceptance.

    Located, not hard-coded, in the spirit of `_level1_target`: any row whose
    presence makes `validate_unit` report a class the unit did not have, while
    the answer stays hard-clean — the shape S6.3 measured 46 times.
    """
    pred_line, pred_token = key[0], key[1]
    taken = {(r.arg_line, r.arg_token) for r in rows.get(pred_line, [])}
    word = layers.tokens[pred_line][pred_token - 1]
    for token in range(1, len(layers.tokens[pred_line]) + 1):
        if (pred_line, token) in taken or token == pred_token:
            continue
        extra = SkelRow(pred_line, pred_token, word, "obl",
                        pred_line, token)
        candidate = {no: list(rs) for no, rs in rows.items()}
        candidate[pred_line] = candidate.get(pred_line, []) + [extra]
        hard, soft = rc._validate_rows(layers, group, candidate)
        if hard:
            continue
        seen = {fixlevel.violation_class(v) for v in rc._validate_rows(
            layers, group, rows)[1]}
        if {fixlevel.violation_class(v) for v in soft} - seen:
            return extra
    pytest.skip("no class-trading row available in this unit")


def test_fix_salvages_the_repair_when_the_whole_answer_trades_a_class(
    tmp_path, monkeypatch
):
    """The granularity seam: a level names a row, a session answers a unit.

    The answer qualifies the oblique correctly *and* brings a row the unit never
    carried, so as a whole it is refused (S6.3's dominant refusal, 46 units). The
    position-scoped splice keeps the repair and drops the rest, and the artifact
    ends up exactly as the accepted-repair test leaves it.
    """
    tsv, layers, group, key, merged = _seed(tmp_path, monkeypatch)
    gold = load_skel("inferno", 1)
    repaired = {no: list(gold.get(no, [])) for no in layers.nos}
    unit_rows = {no: list(repaired.get(no, [])) for no in group}
    extra = _extra_row_that_trades_a_class(layers, group, unit_rows, key)
    overreaching = {no: list(rs) for no, rs in repaired.items()}
    overreaching[extra.line] = overreaching.get(extra.line, []) + [extra]

    def fallback(**kw):
        return _StubResult(
            _rows_payload(overreaching, kw["line_start"], kw["line_end"])
        )

    assert rc.main(_fix_argv(tmp_path, tsv), fallback=fallback) == 0

    # the repair landed; the row that came with it did not
    assert tsv.read_text(encoding="utf-8") == rc.render_tsv(
        [(no, repaired.get(no, [])) for no in sorted(layers.nos)]
    )
    records = [
        json.loads(line)
        for line in (tmp_path / "recon.log").read_text(encoding="utf-8").splitlines()
    ]
    unit = next(
        r for r in records
        if r.get("record") == "unit" and r.get("line_start") == group[0]
    )
    assert unit["fix"]["verdict"] == "salvaged"
    assert unit["fix"]["unit_verdict"].startswith("new_class:")
    # S6.7's missing evidence, now on record: *which* row the refused answer
    # brought, whether it sat on a row the level named, and what the splice
    # then made of it.
    refused = unit["fix"]["refused"]
    assert refused["rows_added"] == 1
    added = refused["rows"]["added"]
    assert [e["argument"] for e in added] == [[extra.arg_line, extra.arg_token]]
    assert added[0]["governed"] is False  # off-brief: not a row the level named
    assert refused["governed_rows"]["relabelled"] == 1  # the level's own job, done
    assert refused["introduced_total"] >= 1
    assert all(not v["governed"] for v in refused["introduced"])
    assert refused["salvage"] == "accepted"
    complete = next(r for r in records if r.get("record") == "canto_complete")
    assert complete["fix"]["verdict:salvaged"] == 1
    assert complete["fix"]["findings_before"] == 1
    assert complete["fix"]["findings_after"] == 0
    assert complete["fix"]["rows_relabelled"] == 1
    assert complete["fix"]["rows_added"] == complete["fix"]["rows_removed"] == 0


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


def test_select_declines_a_finding_whose_row_the_artifact_lacks():
    """A repair level acts on a *row*, so it may not act where the row is absent.

    `rules.py`'s divergence classifier compares two maps keyed by argument position,
    and registry rules C / BJ rewrite those keys first — two of the artifact's own
    citations can collapse onto one key with one role silently replacing the other.
    The finding then names a position whose artifact row already carries the
    qualified role, and the notice built from it describes a row that does not
    exist (`../harness/stages/06.md` S6.9). `select` declines it when the rows are in
    hand, and is unchanged without them: `fix_verdict` compares a before-count with
    an after-count and must apply one definition to two different sets of rows.
    """
    v = _violation(
        "role_mismatch: 37.5 arg (38, 3) 'obl' vs 'obl:per'",
        line=37, role="obl:per", given_role="obl",
        predicate=(37, 5), arg=(38, 3),
    )
    assert fixlevel.select([v], 1) == [v]

    qualified = {38: [SkelRow(37, 5, "fece", "obl:per", 38, 3)]}
    assert fixlevel.select([v], 1, qualified) == []

    bare = {38: [SkelRow(37, 5, "fece", "obl", 38, 3)]}
    assert fixlevel.select([v], 1, bare) == [v]

    assert fixlevel.select([v], 1, {}) == []


def test_fix_level_readout_and_plan_agree_on_the_pool():
    """`make fix-level` must count exactly the units a run would reopen.

    Both go through `fixlevel.select` with the artifact's rows, so the precondition
    above cannot make the readout and the plan disagree — the failure mode would be
    a launch list naming cantos the run then declines to touch.
    """
    root = recon_check.Path(recon_check.__file__).parent
    results = recon_check.run(root, canticle="paradiso", canto=6, stream=None)
    counted = sum(
        len(fixlevel.select(
            [v for v in r["violations"] if v.kind == "tag"], 1, r.get("rows")
        ))
        for r in results
    )
    rows = load_skel("paradiso", 6, base_dir=root)
    planned = sum(
        len(fixlevel.select(
            [v for v in r["violations"] if v.kind == "tag"], 1, rows
        ))
        for r in results
    )
    assert counted == planned
