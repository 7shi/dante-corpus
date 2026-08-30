"""Deterministic tests for the Stage 2 hybrid execution engine
(`harness/extractor/hybrid_engine.py`, milestone 2.3).

No model calls anywhere. The fast path runs against real frozen L2/L4
artifacts (inferno 1-2); hand-built rule tables and valency entries pin down
derivation precedence, conflicts, and routing without needing mined
artifacts. The evaluation face reads gold exactly like the benchmark does;
the execution face is tested adversarially against poisoned `load_skel`.
The one integration test re-mines a capped slice of the real M1.4 logs when
present on disk and skips otherwise (gitignored disk-only artifacts).
"""

import json
from pathlib import Path

import pytest

from dante_corpus.dep import load_dep
from dante_corpus.morph import MorphRow, load_morph
from dante_corpus.skel import io as skel_io
from dante_corpus.skel.io import children_index, morph_index

from harness.extractor import hybrid_engine as he
from harness.extractor import syntax_miner as sm
from harness.extractor.lexicon_builder import ValencyEntry
from harness.extractor.syntax_miner import RowContext, SyntaxRule

REPO_LOGS = Path(__file__).resolve().parent.parent / "harness"


# --- fixtures & helpers ------------------------------------------------------------------


def _views(canticle="inferno", canto=2):
    dep = load_dep(canticle, canto)
    idx = {(r.line, r.token): r for rows in dep.values() for r in rows}
    return idx, morph_index(load_morph(canticle, canto)), children_index(dep)


def _rule(ctx: RowContext, role: str, support: int = 10) -> SyntaxRule:
    fields = {
        name: getattr(ctx, name)
        for name in (
            "pred_pos_class",
            "pred_deprel",
            "arg_attachment",
            "arg_deprel",
            "arg_pos_class",
            "case_lemma",
        )
    }
    return SyntaxRule(**fields, role=role, support=support, total=support,
                      precision=1.0)


def _entry(verb="guardare", prep="di", role=None, support=12):
    return ValencyEntry(
        verb_lemma=verb,
        prep=prep,
        role=role or f"obl:{prep}",
        support=support,
        total=support,
        consistency=1.0,
    )


def _engine(rules=(), entries=()):
    return he.HybridEngine(list(rules), list(entries))


OBJ_CTX = ("verb", "acl:relcl", "direct", "obj", "pronoun", "")


def _ctx_of(pred, arg):
    idx, mi, ci = _views()
    ctx = RowContext.build(idx, mi, ci, pred, arg)
    assert ctx is not None
    return ctx


# --- derivation on real layers -------------------------------------------------------------


def test_derived_row_key_and_dict_roundtrip():
    row = he.DerivedRow(82, 8, "obj", 82, 7, source="rule", support=4,
                        confidence=1.0)
    assert row.key() == (82, 8, "obj", 82, 7)
    assert he.DerivedRow(**row.to_dict()) == row


def test_rule_hit_derives_row_with_provenance():
    idx, mi, ci = _views()
    ctx = RowContext.build(idx, mi, ci, (82, 8), (82, 7))
    engine = _engine([_rule(ctx, "obj", support=154)])
    d = engine.derive_unit("inferno", 2, 82, 84)
    hits = [r for r in d.rows if (r.line, r.arg_line) == (82, 82)]
    # guardi <- ti: the mined obj topology reproduces its gold row.
    assert [(r.token, r.role, r.arg_token) for r in hits] == [(8, "obj", 7)]
    assert all(r.source == "rule" for r in hits)
    assert hits[0].support == 154
    assert hits[0].confidence == 1.0


def test_lexicon_entry_fires_where_no_rule():
    engine = _engine(entries=[_entry("guardare", "di")])
    d = engine.derive_unit("inferno", 2, 82, 84)
    hits = [r for r in d.rows if (r.line, r.token, r.arg_line, r.arg_token)
            == (82, 8, 83, 3)]
    assert len(hits) == 1  # guardare +di ("de lo scender") -> argument frame
    assert hits[0].role == "obl:di"
    assert hits[0].source == "lexicon"
    assert hits[0].support == 12
    assert hits[0].confidence == 1.0


def test_rule_takes_precedence_and_reinforces():
    ctx = _ctx_of((82, 8), (83, 3))
    engine = _engine([_rule(ctx, "obl:di")], [_entry("guardare", "di")])
    d = engine.derive_unit("inferno", 2, 82, 84)
    hits = [r for r in d.rows if (r.line, r.token, r.arg_line, r.arg_token)
            == (82, 8, 83, 3)]
    assert len(hits) == 1
    assert hits[0].source == "rule"  # rule wins; lexicon only fills gaps
    assert d.reinforced_pairs == 1
    assert d.conflicts == []


def test_conflicting_sources_derive_nothing():
    ctx = _ctx_of((82, 8), (83, 3))
    engine = _engine([_rule(ctx, "obl:a")], [_entry("guardare", "di")])
    d = engine.derive_unit("inferno", 2, 82, 84)
    keys = {(r.line, r.token, r.role, r.arg_line, r.arg_token) for r in d.rows}
    assert (82, 8, "obl:a", 83, 3) not in keys
    assert (82, 8, "obl:di", 83, 3) not in keys
    assert len(d.conflicts) == 1
    conflict = d.conflicts[0]
    assert conflict.pred == (82, 8)
    assert conflict.arg == (83, 3)
    assert (conflict.rule_role, conflict.lexicon_role) == ("obl:a", "obl:di")


def test_attachment_accounting_on_real_unit():
    engine = _engine()
    d = engine.derive_unit("inferno", 2, 82, 84)
    assert d.pairs_examined == d.attached_pairs + d.other_attachment_pairs \
        + d.unresolved_pairs
    assert d.attached_pairs > 0
    assert d.other_attachment_pairs > 0  # unrelated pairs stay undecided


def test_unresolved_pairs_counted_not_raised():
    from dante_corpus.dep import DepRow

    class NoMorphViews:
        def view(self, canticle, canto):
            idx = {
                pos: DepRow(line=pos[0], token=pos[1], word="x",
                            deprel="root", head_line=0, head_token=0)
                for pos in ((82, 8), (83, 3))
            }
            return dict(idx), {}, {}

    engine = he.HybridEngine([], [], views=NoMorphViews())
    d = engine.derive_unit("inferno", 2, 82, 84)
    assert d.rows == []
    assert d.pairs_examined == 2  # both orderings of the two positions
    assert d.unresolved_pairs == 2


def test_derivation_to_dict_roundtrips_rows():
    ctx = _ctx_of((82, 8), (82, 7))
    engine = _engine([_rule(ctx, "obj")])
    d = engine.derive_unit("inferno", 2, 82, 84)
    payload = d.to_dict()
    assert payload["unit"]["canto"] == 2
    assert any(row["role"] == "obj" for row in payload["rows"])


# --- pro-drop suspects ----------------------------------------------------------------------


def test_finite_personal_detector():
    def morph(**kw):
        return MorphRow(word="x", **kw)

    assert he._is_finite_personal(morph(pos="verb", person="3",
                                        mood="indicative"))
    assert he._is_finite_personal(morph(pos="verb+pronoun", person="1",
                                        mood="imperative"))
    assert not he._is_finite_personal(morph(pos="verb", mood="gerund"))
    assert not he._is_finite_personal(
        morph(pos="verb", tense="past participle")
    )  # no person
    assert not he._is_finite_personal(morph(pos="noun", person="3",
                                            mood="indicative"))


def test_suspect_is_a_finite_verb_without_derived_subject():
    # With an empty table nothing derives, so every finite personal verb that
    # is not a cop/aux head is a suspect; each must classify as one.
    engine = _engine()
    d = engine.derive_unit("inferno", 1, 1, 36)
    assert d.pro_drop_suspects
    idx, mi, _ci = _views("inferno", 1)
    for pos in d.pro_drop_suspects:
        assert he._is_finite_personal(mi.get(pos))
        assert idx[pos].deprel not in he.NON_SUBJECT_HEAD_DEPRELS


def test_cop_aux_heads_never_suspect():
    # "era" (essere, cop/aux head): its subject belongs to the content
    # predicate, so lacking a derived subj says nothing about pro-drop.
    engine = _engine()
    d = engine.derive_unit("inferno", 1, 1, 3)
    idx, mi, ci = _views("inferno", 1)
    era_tokens = {pos for pos in idx if getattr(mi.get(pos), "lemma", "")
                  == "essere"}
    assert era_tokens
    assert not era_tokens & set(d.pro_drop_suspects)


# --- routing ---------------------------------------------------------------------------------


def _derivation(rows=0, conflicts=0, suspects=0):
    d = he.Derivation(unit={"canticle": "inferno", "canto": 2,
                            "line_start": 82, "line_end": 84})
    d.rows = [
        he.DerivedRow(82, 8, "obj", 82, 7 + i, source="rule", support=3,
                      confidence=1.0)
        for i in range(rows)
    ]
    d.conflicts = [
        he.PairConflict((82, 8), (83, 3 + i), "obj", "obl:di")
        for i in range(conflicts)
    ]
    d.pro_drop_suspects = [(82, 1 + i) for i in range(suspects)]
    return d


def test_route_fast_only_when_all_checks_pass():
    assert he.route_derivation(_derivation()).route == "agent"
    assert he.route_derivation(_derivation()).reason == "no_rows"
    decision = he.route_derivation(_derivation(rows=2))
    assert (decision.route, decision.reason) == ("fast", "complete")


def test_route_reasons_in_severity_order():
    d = _derivation(rows=1, conflicts=1, suspects=1)
    assert he.route_derivation(d).reason == "conflicts"
    assert he.route_derivation(_derivation(rows=1, suspects=1)).reason == \
        "pro_drop_suspects"


def test_route_policy_toggles():
    d = _derivation(rows=1, suspects=2)
    relaxed = he.RoutePolicy(require_explicit_subjects=False)
    assert he.route_derivation(d, relaxed).route == "fast"
    permissive = he.RoutePolicy(forbid_conflicts=False, require_rows=False,
                                require_explicit_subjects=False)
    assert he.route_derivation(_derivation(), permissive).route == "fast"


def test_decision_to_dict():
    payload = he.RouteDecision("fast", "complete").to_dict()
    assert payload == {"route": "fast", "reason": "complete"}


# --- the fallback seam ------------------------------------------------------------------------


class _StubAgentResult:
    def __init__(self, rows):
        self.candidate_rows = rows


def test_run_unit_fast_path_skips_the_agent():
    ctx = _ctx_of((82, 8), (82, 7))
    engine = _engine([_rule(ctx, "obj")])
    calls = []

    def fallback(**kw):
        calls.append(kw)
        raise AssertionError("fallback must not run on a fast decision")

    result = engine.run_unit(
        canticle="inferno", canto=2, line_start=82, line_end=84,
        policy=he.RoutePolicy(require_explicit_subjects=False),
        fallback=fallback,
    )
    assert calls == []
    assert result.decision.reason == "complete"
    assert result.origin == "fast"
    assert not result.fallback_ran
    assert (82, 8, "obj", 82, 7) in result.row_keys


def test_run_unit_routes_to_agent_and_normalizes_submission():
    engine = _engine()  # empty tables: nothing derivable -> agent
    seen = {}

    def fallback(**kw):
        seen.update(kw)
        return _StubAgentResult([
            {"line": 83, "token": 3, "role": "obj", "arg_line": 83,
             "arg_token": 6},
            {"line": 999, "token": 1, "role": "obj", "arg_line": 999,
             "arg_token": 2},  # out of unit
            {"nonsense": True},  # malformed
        ])

    result = engine.run_unit(
        canticle="inferno", canto=2, line_start=82, line_end=84,
        fallback=fallback,
    )
    assert result.decision.route == "agent"
    assert result.decision.reason == "no_rows"
    assert result.fallback_ran
    assert seen == {"canticle": "inferno", "canto": 2, "line_start": 82,
                    "line_end": 84}
    assert result.row_keys == frozenset({(83, 3, "obj", 83, 6)})
    assert result.malformed_rows == 1
    assert result.out_of_unit_rows == 1


def test_run_unit_dry_mode_without_fallback():
    result = _engine().run_unit(
        canticle="inferno", canto=2, line_start=82, line_end=84
    )
    assert result.decision.route == "agent"
    assert not result.fallback_ran
    assert result.row_keys == frozenset()


def test_run_unit_snaps_open_line_ends():
    from harness.runner.benchmark import resolve_unit_bounds

    expected_end = resolve_unit_bounds("inferno", 2, 83)[1]
    result = _engine().run_unit(canticle="inferno", canto=2, line_start=83)
    assert result.unit["line_end"] == expected_end


def test_execution_face_never_touches_gold(monkeypatch):
    def boom(*a, **kw):
        raise AssertionError("execution must not read gold skel/ artifacts")

    monkeypatch.setattr(skel_io, "load_skel", boom)
    monkeypatch.setattr(sm, "load_skel", boom)
    ctx = _ctx_of((82, 8), (82, 7))
    engine = _engine([_rule(ctx, "obj")])
    d = engine.derive_unit("inferno", 2, 82, 84)
    assert d.keys
    result = engine.run_unit(
        canticle="inferno", canto=2, line_start=82, line_end=84,
        policy=he.RoutePolicy(require_explicit_subjects=False),
    )
    assert result.row_keys


# --- artifact sources --------------------------------------------------------------------------


def _write_log(path: Path, records) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        for record in records:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")


def _case_record(missing=(), extra=()):
    unit = {"canticle": "inferno", "canto": 2, "line_start": 82,
            "line_end": 84}
    return {
        "record": "case",
        "unit": unit,
        "workflow": "unit",
        "missing": [list(k) for k in missing],
        "extra": [list(k) for k in extra],
        "trace": {"timestamp": "2026-08-22T13:44:20+00:00"},
    }


def test_mine_artifacts_from_synthetic_log(tmp_path):
    log = tmp_path / "run.log"
    _write_log(log, [_case_record()])
    bundle = he.mine_artifacts(
        [log],
        min_support=1,
        min_precision=1.0,
        min_consistency=1.0,
        progress_stream=None,
    )
    # The empty diff labels every gold row correct: obj shapes mine into
    # rules and the guardare+di frame into the lexicon.
    assert bundle.rules
    assert any(r.role == "obj" for r in bundle.rules)
    assert ("guardare", "di") in {(e.verb_lemma, e.prep) for e in bundle.entries}
    assert bundle.mine_stats["instances_clustered"] > 0
    assert bundle.lexicon_stats["instances_aggregated"] > 0
    engine = _engine(bundle.rules, bundle.entries)
    assert engine.derive_unit("inferno", 2, 82, 84).keys


def test_artifact_json_roundtrip(tmp_path):
    from harness.extractor.lexicon_builder import write_lexicon_json

    rules_path = tmp_path / "rules.json"
    lexicon_path = tmp_path / "lexicon.json"
    ctx = _ctx_of((82, 8), (82, 7))
    rules = [_rule(ctx, "obj")]
    entries = [_entry()]
    sm.write_rules_json(rules_path, rules)
    write_lexicon_json(lexicon_path, entries)
    loaded_rules = he.load_rules_json(rules_path)
    loaded_entries = he.load_lexicon_json(lexicon_path)
    assert loaded_rules == rules
    assert loaded_entries == entries


# --- deterministic evaluation probe --------------------------------------------------------------


def test_iter_parse_units_matches_sentence_groups():
    computed = list(
        he.iter_parse_units(["inferno"], max_cantos=1, progress_stream=None)
    )
    from dante_corpus import api
    from dante_corpus.dep import sentence_groups

    data = api.canto("inferno", 1)
    groups = sentence_groups(
        [l.no for l in data.lines()], [l.text for l in data.lines()]
    )
    expected = [
        {"canticle": "inferno", "canto": 1, "line_start": g[0],
         "line_end": g[-1]}
        for g in groups
    ]
    assert computed == expected


def test_probe_partitions_gold_and_reports_faces():
    ctx = _ctx_of((82, 8), (82, 7))
    engine = _engine([_rule(ctx, "obj"), _rule(_ctx_of((82, 8), (83, 3)),
                                               "obl:di")], [_entry()])
    report, records = he.evaluate_fast_path(
        engine,
        canticles=["inferno"],
        max_cantos=2,
        progress_stream=None,
    )
    drained = list(records)
    assert report.units == len(drained) > 0
    assert sum(report.routes.values()) == report.units
    assert report.tp + report.fp + report.fn > 0
    assert report.fast_tp <= report.tp
    metrics = report.metrics()
    assert metrics["units"] == report.units
    assert set(metrics["routes"]) <= {"fast", "agent"}
    assert 0.0 <= metrics["fast_share"] <= 1.0
    text = report.summary()
    assert "target >= 0.80:" in text
    assert ": PASS)" in text or ": MISS)" in text


def test_empty_engine_routes_everything_to_agent():
    report, records = he.evaluate_fast_path(
        _engine(), canticles=["inferno"], max_cantos=1, progress_stream=None
    )
    list(records)
    assert report.routes["agent"] == report.units
    assert report.routes["fast"] == 0
    assert report.tp == 0


# --- CLI end-to-end -------------------------------------------------------------------------------


def test_cli_main_writes_streaming_log_with_summary_last(tmp_path):
    run_log = tmp_path / "bench-x.log"
    _write_log(run_log, [_case_record()])
    out_log = tmp_path / "engine.log"
    exit_code = he.main(
        [
            "--run-log", str(run_log),
            "--min-support", "1",
            "--eval-canticle", "inferno",
            "--max-cantos", "1",
            "--log", str(out_log),
        ]
    )
    assert exit_code == 0
    lines = [
        json.loads(l)
        for l in out_log.read_text(encoding="utf-8").splitlines()
        if l.strip()
    ]
    assert lines[-1]["record"] == "summary"  # completion marker
    units = [r for r in lines[:-1]]
    assert units and all(r["record"] == "unit" for r in units)
    assert lines[-1]["units"] == len(units)
    assert lines[-1]["fast_share"] <= 1.0
    assert {"tp", "fp", "fn", "route", "reason"} <= set(units[0])


# --- integration over real mined artifacts ---------------------------------------------------------


@pytest.mark.skipif(
    not (REPO_LOGS / "bench-unit-retry.log").exists(),
    reason="M1.4 run logs are gitignored disk-only artifacts",
)
def test_real_log_integration_capped():
    bundle = he.mine_artifacts(
        [REPO_LOGS / "bench-unit-retry.log"], progress_stream=None
    )
    # One 87-session log yields a fraction of the pooled table (183 rules /
    # 140 frames over all four runs) — enough to reproduce real gold rows.
    assert len(bundle.rules) > 20
    assert len(bundle.entries) > 3
    engine = he.HybridEngine(bundle.rules, bundle.entries)
    report, records = he.evaluate_fast_path(
        engine,
        canticles=["inferno"],
        max_cantos=2,
        progress_stream=None,
    )
    list(records)
    assert report.units > 30
    assert report.tp > 50  # the mined shapes reproduce real gold rows
    assert report.fp < report.tp  # derivation stays precision-dominated


# --- schema gate on the fast path (S5.7) -----------------------------------------------------


def _row(line, token, role, arg_line, arg_token):
    return he.DerivedRow(line, token, role, arg_line, arg_token, source="rule",
                         support=5, confidence=1.0)


def test_schema_violations_flags_unregistered_clausal_argument():
    # inferno 1.13-15: 'xcomp' pointing at a token no derived row makes a predicate.
    nos = [13, 14, 15]
    texts = ["che nel pensier rinova la paura!",
             "Tant' è amara che poco è più morte;",
             "ma per trattar del ben ch'i' vi trovai,"]
    rows = [_row(13, 4, "xcomp", 13, 6)]
    found = he.schema_violations(nos, texts, rows)
    assert len(found) == 1 and "[clausal]" in found[0]
    # registering the clause's own predicate satisfies the same check.
    rows.append(_row(13, 6, "subj", 13, 5))
    assert he.schema_violations(nos, texts, rows) == []


def test_schema_violations_covers_the_two_row_local_classes():
    nos, texts = [13], ["che nel pensier rinova la paura!"]
    self_arg = he.schema_violations(nos, texts, [_row(13, 4, "obj", 13, 4)])
    assert len(self_arg) == 1 and "[dup]" in self_arg[0]
    null_pos = he.schema_violations(nos, texts, [_row(13, 4, "obj", 0, 0)])
    assert len(null_pos) == 1 and "[position]" in null_pos[0]
    assert he.schema_violations(nos, texts, [_row(13, 4, "subj", 0, 0)]) == []


def test_schema_violations_drops_the_soft_tier():
    # An unknown role is a `tag` finding: soft, and never a routing reason.
    nos, texts = [13], ["che nel pensier rinova la paura!"]
    assert he.schema_violations(nos, texts, [_row(13, 4, "nonsense", 13, 6)]) == []


def test_route_schema_invalid_sends_a_confident_derivation_to_the_agent():
    d = _derivation(rows=2)
    assert he.route_derivation(d).route == "fast"
    d.schema_violations = ["82 [clausal] xcomp argument (82, 7) is not a predicate"]
    decision = he.route_derivation(d)
    assert (decision.route, decision.reason) == ("agent", "schema_invalid")
    relaxed = he.RoutePolicy(require_schema_valid=False)
    assert he.route_derivation(d, relaxed).route == "fast"


def test_route_conflicts_outrank_schema_invalid():
    d = _derivation(rows=1, conflicts=1)
    d.schema_violations = ["82 [dup] argument cites its own predicate (82, 8)"]
    assert he.route_derivation(d).reason == "conflicts"


def test_derive_unit_records_schema_violations():
    engine = _engine()
    d = engine.derive_unit("inferno", 1, 1, 3)
    assert d.schema_violations == []
    assert "schema_violations" in d.to_dict()
