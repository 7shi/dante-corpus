"""Deterministic tests for the Stage 1 benchmark (`harness/runner/benchmark.py`).

No model calls: scripted `StubTransport` sessions run through the real loop,
toolkit, prompts, and fixtures, and are scored against the real 0-soft Gold
Standard (`skel/`) — the evaluation reference the agent itself never sees.
Covers milestone 1.3's contract: gold comparison, §5.2 metric aggregation,
probe-style parse-success measurement, and fixture-table integrity.
"""

import io
import json

import pytest

from dante_corpus import api

from harness.fixtures import CATEGORIES, CHALLENGE_CASES, case_by_id, cases_for
from harness.fixtures.challenge_cases import ChallengeCase
from harness.runner.agent import run_unit
from harness.runner.benchmark import (
    CONVERGENCE_TURN_BUDGET,
    BenchmarkReport,
    RoleMetrics,
    UnitEvaluation,
    _parse_turn_stats,
    candidate_keys,
    evaluate_unit,
    gold_row_keys,
    resolve_unit_bounds,
    run_benchmark,
)
from harness.runner.tools import GrammarToolkit
from harness.toolcall import StubTransport


def _block(name: str, arguments: str | dict) -> str:
    args = arguments if isinstance(arguments, str) else json.dumps(arguments)
    return (
        "<tool_call>\n"
        f'{{"name": "{name}", "arguments": {args}}}\n'
        "</tool_call>"
    )


def _validate_block(rows, canticle="inferno", canto=1, line_start=1):
    return _block(
        "validate_candidate",
        {
            "canticle": canticle,
            "canto": canto,
            "line_start": line_start,
            "candidate_rows": rows,
        },
    )


def _row(line, token, word, role, arg_line=0, arg_token=0, arg_word=""):
    return {
        "line": line,
        "token": token,
        "word": word,
        "role": role,
        "arg_line": arg_line,
        "arg_token": arg_token,
        "arg_word": arg_word,
    }


def _gold_rows_as_dicts(canticle, canto, line_start, line_end):
    """Gold rows as submission dicts with real word anchors (for scripted sessions)."""
    tokens = {line.no: line.tokens for line in api.canto(canticle, canto).lines()}
    rows = []
    for key in sorted(gold_row_keys(canticle, canto, line_start, line_end)):
        rows.append(
            {
                "line": key[0],
                "token": key[1],
                "role": key[2],
                "arg_line": key[3],
                "arg_token": key[4],
                "word": tokens[key[0]][key[1] - 1],
            }
        )
    return rows


# The famous opening unit's gold (Inferno I.1-3), cross-checked against the artifact.
GOOD_ROWS_1_3 = [
    _row(2, 2, "ritrovai", "subj"),
    _row(2, 2, "ritrovai", "obl:in", 1, 2, "mezzo"),
    _row(2, 2, "ritrovai", "obl:per", 2, 5, "selva"),
    _row(3, 6, "smarrita", "subj", 3, 4, "via"),
]


@pytest.fixture()
def toolkit():
    return GrammarToolkit()


def _run(script, toolkit_, **kwargs):
    kwargs.setdefault("canticle", "inferno")
    kwargs.setdefault("canto", 1)
    kwargs.setdefault("line_start", 1)
    return run_unit(transport=StubTransport(script), toolkit=toolkit_, **kwargs)


# --- fixture table integrity ----------------------------------------------------------------


def test_fixture_table_shape_and_categories():
    assert len(CHALLENGE_CASES) >= 50  # runner/PLAN.md §5.1: 50–100 units
    ids = [case.case_id for case in CHALLENGE_CASES]
    assert len(ids) == len(set(ids))
    for case in CHALLENGE_CASES:
        assert case.category in CATEGORIES
        assert case.line_start <= case.line_end


def test_every_fixture_snaps_to_one_sentence_group_with_gold():
    seen_units = set()
    for case in CHALLENGE_CASES:
        start, end = resolve_unit_bounds(case.canticle, case.canto, case.line_start)
        assert (start, end) == (case.line_start, case.line_end), case.case_id
        unit = (case.canticle, case.canto, start, end)
        assert unit not in seen_units, f"{case.case_id} duplicates {sorted(seen_units)}"
        seen_units.add(unit)
        gold = gold_row_keys(case.canticle, case.canto, start, end)
        assert gold, f"{case.case_id}: fixture unit has no gold rows"


def test_core_categories_are_balanced_across_canticles():
    for category in ("control", "coordination", "relative_chain", "quotes"):
        cases = cases_for([category])
        canticles = {case.canticle for case in cases}
        assert canticles == {"inferno", "purgatorio", "paradiso"}, category


def test_historical_fixtures_cover_the_documented_censuses():
    historical = cases_for(["historical"])
    assert len(historical) >= 40
    notes = {case.note for case in historical}
    assert any(note.startswith("P15") for note in notes)
    assert any(note.startswith("P5") for note in notes)
    assert any(note.startswith("P13") for note in notes)


# --- row normalization & gold comparison ------------------------------------------------------


def test_gold_row_keys_match_hand_written_opening_rows():
    assert gold_row_keys("inferno", 1, 1, 3) == {
        (row["line"], row["token"], row["role"], row["arg_line"], row["arg_token"])
        for row in GOOD_ROWS_1_3
    }


def test_resolve_unit_bounds_snaps_to_sentence_group():
    assert resolve_unit_bounds("inferno", 1, 1) == (1, 3)
    with pytest.raises(ValueError):
        resolve_unit_bounds("inferno", 1, 1000)


def test_candidate_keys_filter_and_count():
    rows = GOOD_ROWS_1_3 + [
        _row(99, 1, "fuori", "subj"),  # predicate outside the unit
        "garbage",  # not a dict
        {"line": 2},  # missing fields
    ]
    keys, malformed, out_of_unit = candidate_keys(rows, 1, 3)
    assert keys == {(r["line"], r["token"], r["role"], r["arg_line"], r["arg_token"]) for r in GOOD_ROWS_1_3}
    assert malformed == 2
    assert out_of_unit == 1


# --- evaluate_unit ------------------------------------------------------------------------------


def test_evaluate_perfect_session_on_real_fixture(toolkit):
    case = case_by_id("rel-inf01-007")
    rows = _gold_rows_as_dicts(case.canticle, case.canto, case.line_start, case.line_end)
    script = [
        _block(
            "read_unit",
            json.dumps(
                {
                    "canticle": case.canticle,
                    "canto": case.canto,
                    "line_start": case.line_start,
                }
            ),
        ),
        _validate_block(rows, case.canticle, case.canto, case.line_start),
        "The unit is solved.",
    ]
    result = _run(script, toolkit, canticle=case.canticle, canto=case.canto,
                  line_start=case.line_start, line_end=case.line_end)
    evaluation = evaluate_unit(result, case=case)

    assert isinstance(evaluation, UnitEvaluation)
    assert evaluation.exact_first is True
    assert evaluation.exact_final is True
    assert evaluation.converged is True  # 3 turns <= 5-turn budget
    assert evaluation.missing == [] and evaluation.extra == []
    assert evaluation.gold_rows == evaluation.predicted_rows > 0
    assert evaluation.parse_success_turns == result.turns
    assert evaluation.parse_failure_turns == 0
    assert evaluation.upstream_feedback_precision is None

    data = evaluation.to_dict()
    blob = json.dumps(data, ensure_ascii=False)
    loaded = json.loads(blob)
    assert loaded["record"] == "case" and loaded["exact_first"] is True


def test_evaluate_distinguishes_one_shot_from_convergence(toolkit):
    wrong_first = [_row(2, 2, "ritrovai", "obj")]
    script = [
        _block("read_unit", '{"canticle": "inferno", "canto": 1, "line_start": 1}'),
        _validate_block(wrong_first),
        _validate_block(GOOD_ROWS_1_3),
        "Converged on the second submission.",
    ]
    result = _run(script, toolkit)
    ev = evaluate_unit(result)
    assert ev.exact_first is False  # 1-shot failed...
    assert ev.exact_final is True  # ...but self-correction reached gold
    assert ev.converged is True  # within the 5-turn budget (4 turns)
    assert ev.submissions == 2


def test_convergence_requires_the_turn_budget(toolkit):
    slow = [_block("read_unit", '{"canticle": "inferno", "canto": 1, "line_start": 1}')] * (
        CONVERGENCE_TURN_BUDGET + 1
    )
    script = [*slow, _validate_block(GOOD_ROWS_1_3), "finally solved"]
    result = _run(script, toolkit)
    assert result.turns == CONVERGENCE_TURN_BUDGET + 3
    ev = evaluate_unit(result)
    assert ev.exact_final is True
    assert ev.converged is False  # matched gold but needed too many turns


def test_evaluate_without_case_snaps_bounds_to_the_parse_unit(toolkit):
    """A bare UnitResult opened at line 1 must be scored against gold for lines 1-3."""
    script = [
        _block("read_unit", '{"canticle": "inferno", "canto": 1, "line_start": 1}'),
        _validate_block(GOOD_ROWS_1_3),
        "done",
    ]
    result = _run(script, toolkit, line_end=None)
    ev = evaluate_unit(result)
    assert ev.unit == {"canticle": "inferno", "canto": 1, "line_start": 1, "line_end": 3}
    assert ev.exact_final is True


def test_out_of_unit_predicates_do_not_break_exactness(toolkit):
    rows = [*GOOD_ROWS_1_3, _row(99, 1, "inesistente", "subj")]
    script = [
        _validate_block(rows),
        "done",
    ]
    result = _run(script, toolkit)
    ev = evaluate_unit(result)
    assert ev.out_of_unit_rows == 1
    assert ev.exact_final is True  # excluded from comparison, counted separately


# --- probe-style parse-success measurement --------------------------------------------------------


def test_prose_only_session_is_a_parse_failure():
    result = _run(["prose without calls"], GrammarToolkit(), max_nudges=0)
    assert _parse_turn_stats(result) == (0, 1)


def test_malformed_block_then_recovery_counts_like_the_probe(toolkit):
    script = [
        "<tool_call>\n{not json}\n</tool_call>",  # all blocks malformed -> failure
        _block("read_unit", '{"canticle": "inferno", "canto": 1, "line_start": 1}'),
        _validate_block(GOOD_ROWS_1_3),
        "final answer after successful work",  # block-free -> legitimate success
    ]
    result = _run(script, toolkit)
    assert _parse_turn_stats(result) == (3, 1)


def test_demo_exchange_is_not_counted_as_a_model_turn(toolkit):
    """The few-shot demo carries a well-formed call; it lives in the opening prompt."""
    script = [
        _block("read_unit", '{"canticle": "inferno", "canto": 1, "line_start": 1}'),
        _validate_block(GOOD_ROWS_1_3),
        "done",
    ]
    result = _run(script, toolkit)
    assert result.opening_len > 0
    import harness.runner.benchmark as bench

    ok, bad = bench._parse_turn_stats(result)
    assert (ok, bad) == (3, 0)


# --- upstream feedback channel --------------------------------------------------------------------


def test_upstream_feedback_precision_mixes_wellformed_and_broken_records(toolkit):
    feedback = [
        {"layer": "L4", "description": "impossible attachment"},
        {"layer": "L2"},  # no description -> filed but malformed
    ]
    call = {
        "canticle": "inferno",
        "canto": 1,
        "line_start": 1,
        "candidate_rows": GOOD_ROWS_1_3,
        "upstream_feedback": feedback,
    }
    script = [
        _block("validate_candidate", call),
        "filed",
    ]
    result = _run(script, toolkit)
    ev = evaluate_unit(result)
    assert ev.upstream_feedback == feedback
    assert ev.upstream_wellformed == 1
    assert ev.upstream_feedback_precision == pytest.approx(0.5)


# --- aggregate report -------------------------------------------------------------------------------


def _synthetic_evaluation(final_keys, gold_keys, **kwargs):
    return UnitEvaluation(
        case_id=kwargs.pop("case_id", "synthetic"),
        category=kwargs.pop("category", "control"),
        unit={"canticle": "inferno", "canto": 1, "line_start": 1, "line_end": 3},
        gold_key_set=frozenset(gold_keys),
        final_key_set=frozenset(final_keys),
        **kwargs,
    )


def test_role_metrics_math_handles_zero_division():
    empty = RoleMetrics(0, 0, 0)
    assert empty.precision == 0.0 and empty.recall == 0.0 and empty.f1 == 0.0
    half = RoleMetrics(1, 1, 1)
    assert half.precision == 0.5 and half.recall == 0.5 and half.f1 == 0.5


def test_role_table_and_micro_aggregation():
    gold = [(2, 2, "subj", 0, 0), (2, 2, "obl:in", 1, 2), (3, 6, "obj", 3, 6)]
    final = [(2, 2, "subj", 0, 0), (2, 2, "obj", 1, 2)]  # obl mislabeled obj, obj missed
    ev = _synthetic_evaluation(final, gold)
    report = BenchmarkReport()
    report.add(ev)
    table = report.role_table()
    assert table["subj"].tp == 1 and table["subj"].fp == 0 and table["subj"].fn == 0
    assert table["obl:in"].fn == 1 and table["obl:in"].tp == 0
    assert table["obj"].fp == 1 and table["obj"].fn == 1
    micro = report._micro(report.evaluations)
    assert (micro.tp, micro.fp, micro.fn) == (1, 1, 2)


def test_report_metrics_and_summary_round_trip():
    gold = {(2, 2, "subj", 0, 0)}
    report = BenchmarkReport()
    report.add(
        _synthetic_evaluation(
            gold, gold, exact_first=True, exact_final=True, converged=True, submissions=1
        )
    )
    report.add(_synthetic_evaluation(set(), gold, category="quotes", submissions=1))
    m = report.metrics()
    assert m["units"] == 2
    assert m["one_shot_exact_match_rate"] == 0.5
    assert m["convergence_rate"] == 0.5
    assert m["no_submission_units"] == 0  # an empty submission still counts as submitted
    assert m["categories"]["control"]["units"] == 1
    assert m["roles"]["subj"]["fn"] == 1
    assert json.dumps(m)  # serializable
    text = report.summary()
    assert "1-shot exact match: 0.500" in text


def test_report_metrics_on_empty_report_is_defined():
    m = BenchmarkReport().metrics()
    assert m["units"] == 0 and m["one_shot_exact_match_rate"] == 0.0
    assert m["parse_success_rate"] is None
    assert m["upstream_feedback_precision"] is None


# --- run_benchmark (streaming sink) -----------------------------------------------------------------


def test_run_benchmark_streams_case_records_and_scores_real_fixture(toolkit):
    case = case_by_id("quo-pur01-046")
    rows = _gold_rows_as_dicts(case.canticle, case.canto, case.line_start, case.line_end)
    good_script = [
        _block(
            "validate_candidate",
            {
                "canticle": case.canticle,
                "canto": case.canto,
                "line_start": case.line_start,
                "candidate_rows": rows,
            },
        ),
        "solved",
    ]
    sink = io.StringIO()
    report = run_benchmark([case], StubTransport(good_script), toolkit=toolkit, sink=sink)

    assert len(report) == 1
    records = [json.loads(line) for line in sink.getvalue().splitlines()]
    assert len(records) == 1 and records[0]["record"] == "case"
    rec = records[0]
    assert rec["case_id"] == case.case_id and rec["category"] == "quotes"
    assert rec["exact_first"] is True and rec["converged"] is True
    assert rec["trace"]["record"] == "session"
    assert "messages" not in rec["trace"]  # slim by default
    assert rec["trace"]["outcomes"][0]["ok"] is True

    metrics = report.metrics()
    assert metrics["units"] == 1
    assert metrics["one_shot_exact_match_rate"] == 1.0
    assert metrics["parse_success_rate"] == 1.0


def test_run_benchmark_sequential_cases_share_the_toolkit_cache(toolkit):
    """Two cases run back-to-back through one toolkit; anti-leakage state resets per session."""
    first = case_by_id("ctl-inf01-010")
    second = case_by_id("quo-pur01-046")
    scripts = []
    for case in (first, second):
        rows = _gold_rows_as_dicts(case.canticle, case.canto, case.line_start, case.line_end)
        scripts.append(
            [
                _block(
                    "search_corpus",
                    json.dumps({"query": {"lemma": "essere"}}),
                ),
                _validate_block(rows, case.canticle, case.canto, case.line_start),
                "solved",
            ]
        )
    transport = StubTransport(scripts[0] + scripts[1])
    report = run_benchmark([first, second], transport, toolkit=toolkit)
    assert len(report) == 2
    assert report.metrics()["one_shot_exact_match_rate"] == 1.0
