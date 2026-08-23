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
from harness.runner import benchmark as bench_module
from harness.runner.benchmark import (
    CONVERGENCE_TURN_BUDGET,
    BenchmarkReport,
    RoleMetrics,
    UnitEvaluation,
    _parse_turn_stats,
    _retry_delta,
    _retry_snapshot,
    candidate_keys,
    evaluate_unit,
    evaluation_from_record,
    gold_row_keys,
    load_log,
    prepare_resume,
    resolve_unit_bounds,
    run_benchmark,
)
from harness.runner.statusline import HarnessStatusLine
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
    assert m["session_turns"] == 0 and m["slow_turns"] == 0
    assert m["wall_clock_seconds"] == 0.0
    assert m["mean_turn_seconds"] is None and m["max_turn_seconds"] is None


def test_report_metrics_aggregate_per_turn_timing_and_count_slow_turns():
    """§4 item 5: wall clock rolls up per turn; brooding turns surface as slow_turns."""
    report = BenchmarkReport()
    for seconds in ([10.0, 305.5], [2.25]):
        ev = UnitEvaluation(case_id="x", category="historical", unit={})
        ev.turn_seconds = seconds
        ev.turns = len(seconds)
        report.add(ev)
    m = report.metrics()
    assert m["session_turns"] == 3
    assert m["wall_clock_seconds"] == 317.8
    assert m["mean_turn_seconds"] == 105.9
    assert m["max_turn_seconds"] == 305.5
    assert m["slow_turns"] == 1  # SLOW_TURN_SECONDS = 300
    text = report.summary()
    assert "turns: 3 in 318s" in text and "slow(>= 300s): 1" in text


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
    assert isinstance(rec["turn_seconds"], list) and len(rec["turn_seconds"]) >= 1
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


def test_run_benchmark_progress_announces_each_case_position(toolkit, capsys):
    """§4 item 5: watched runs announce every case with its [index/total]."""
    first = case_by_id("ctl-inf01-010")
    second = case_by_id("quo-pur01-046")
    scripts = []
    for case in (first, second):
        rows = _gold_rows_as_dicts(case.canticle, case.canto, case.line_start, case.line_end)
        scripts.append(
            [
                _validate_block(rows, case.canticle, case.canto, case.line_start),
                "solved",
            ]
        )
    transport = StubTransport(scripts[0] + scripts[1])
    run_benchmark([first, second], transport, toolkit=toolkit, progress=True)
    err = capsys.readouterr().err
    assert "\n===== [1/2] ctl-inf01-010 =====\n" in err
    assert "\n===== [2/2] quo-pur01-046 =====\n" in err
    # Turn lines follow each announcement (progress_printer is wired too).
    assert f"[ctl-inf01-010] turn" in err and f"[quo-pur01-046] turn" in err


def test_run_benchmark_status_bar_tracks_the_separator_positions(toolkit, capsys):
    """§4 item 5: a status line's bar counts sessions on the separators' basis.

    Separators and turn lines route through the status line's console stream
    instead of stderr; the bar advances to `pos/total` as each session starts.
    """
    first = case_by_id("ctl-inf01-010")
    second = case_by_id("quo-pur01-046")
    scripts = []
    for case in (first, second):
        rows = _gold_rows_as_dicts(case.canticle, case.canto, case.line_start, case.line_end)
        scripts.append(
            [
                _validate_block(rows, case.canticle, case.canto, case.line_start),
                "solved",
            ]
        )
    transport = StubTransport(scripts[0] + scripts[1])

    updates = []

    class _Bar:
        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

        def update(self, completed):
            updates.append(completed)

    class _FakeStatusLine:
        def __init__(self):
            self.stream = io.StringIO()

        def progress(self, total, start=0, label=None):
            assert (total, start) == (2, 0)
            assert label == "bench:unit"
            return _Bar()

    fake = _FakeStatusLine()
    run_benchmark(
        [first, second],
        transport,
        toolkit=toolkit,
        progress=True,
        status_line=fake,
    )
    assert updates == [1, 2]
    # Everything human-facing went through the status line's console...
    display = fake.stream.getvalue()
    assert "===== [1/2] ctl-inf01-010 =====" in display
    assert "[ctl-inf01-010] turn" in display
    # ...and stderr stayed clean.
    assert capsys.readouterr().err == ""


def test_run_benchmark_resume_offset_spans_the_whole_run(toolkit, capsys):
    """Resumed runs keep whole-run positions: `[offset+i/offset+N]`, bar from offset."""
    done = case_by_id("ctl-inf01-010")
    case = case_by_id("quo-pur01-046")
    rows = _gold_rows_as_dicts(case.canticle, case.canto, case.line_start, case.line_end)
    script = [_validate_block(rows, case.canticle, case.canto, case.line_start), "solved"]

    seeded = BenchmarkReport()
    seeded.add(
        UnitEvaluation(
            case_id=done.case_id, category=done.category,
            unit={"canticle": done.canticle, "canto": done.canto,
                  "line_start": done.line_start, "line_end": done.line_end},
            turn_seconds=[100.0],
        )
    )

    updates = []

    class _Bar:
        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

        def update(self, completed):
            updates.append(completed)

    class _FakeStatusLine:
        def __init__(self):
            self.stream = io.StringIO()

        def progress(self, total, start=0, label=None):
            assert (total, start) == (2, 1)  # 1 resumed + 1 to run
            return _Bar()

    fake = _FakeStatusLine()
    report = run_benchmark(
        [case],
        StubTransport(script),
        toolkit=toolkit,
        progress=True,
        status_line=fake,
        report=seeded,
        resume_offset=1,
    )
    # The separator counts the resumed case; the bar starts past it.
    assert "===== [2/2] quo-pur01-046 =====" in fake.stream.getvalue()
    assert updates == [2]
    assert len(report) == 2
    assert capsys.readouterr().err == ""


def test_harness_status_line_stream_is_markup_safe(capsys):
    """Forwarded corpus/model text must never be parsed as Rich markup.

    `[role=...]` citations used to vanish and closing-tag fragments raised
    MarkupError; the harness stream renders both verbatim.
    """
    if HarnessStatusLine is None:  # pragma: no cover - rich ships via llm7shi extra
        pytest.skip("llm7shi statusline extra not installed")
    line = HarnessStatusLine()
    dangerous = 'rows [obj] plus [/b] plus [obl:a=(126,3)] end'
    line.stream.write(dangerous + "\n")
    captured = capsys.readouterr()
    assert dangerous in captured.err
    assert captured.out == ""


def test_harness_status_line_counts_api_retries(monkeypatch):
    """Auto-retried 429 backoffs become countable through the stream's wait_retry."""
    if HarnessStatusLine is None:  # pragma: no cover - rich ships via llm7shi extra
        pytest.skip("llm7shi statusline extra not installed")
    from llm7shi.statusline import StatusLineConsoleStream

    monkeypatch.setattr(
        StatusLineConsoleStream, "wait_retry", lambda self, delay, message="...": None
    )
    line = HarnessStatusLine()
    line.stream.wait_retry(50)
    line.stream.wait_retry(12)
    assert line.stream.api_retries == 2
    assert line.stream.api_retry_seconds == 62.0


def test_api_retry_accounting_round_trip():
    """Untracked runs stay None; snapshots measure per-case retry deltas."""
    ev = UnitEvaluation(case_id="x", category="historical", unit={})
    record = ev.to_dict()
    assert record["api_retries"] is None and record["api_retry_seconds"] is None

    # Without a status line nothing is tracked.
    snap = _retry_snapshot(None)
    assert snap is None and _retry_delta(snap, None) is None

    class _Stream:
        api_retries = 3
        api_retry_seconds = 95.0

    holder = type("Holder", (), {"stream": _Stream()})()
    snap = _retry_snapshot(holder)
    assert snap == (3, 95.0)
    _Stream.api_retries, _Stream.api_retry_seconds = 5, 151.5
    assert _retry_delta(snap, holder) == (2, 56.5)

    report = BenchmarkReport()
    report.add(
        UnitEvaluation(case_id="a", category="historical", unit={},
                       api_retries=2, api_retry_seconds=60.0)
    )
    report.add(UnitEvaluation(case_id="b", category="control", unit={}))
    metrics = report.metrics()
    assert metrics["api_retries"] == 2
    assert metrics["api_retry_seconds"] == 60.0


# --- workflow granularity (predicate accumulation) ---------------------------------------


def _gold_by_predicate(case):
    by_pred = {}
    for key in sorted(
        gold_row_keys(case.canticle, case.canto, case.line_start, case.line_end)
    ):
        by_pred.setdefault(key[:2], []).append(key)
    return by_pred


def _rows_for(keys):
    # Coordinates alone identify tokens: word anchors are optional now.
    return [
        {"line": k[0], "token": k[1], "role": k[2], "arg_line": k[3], "arg_token": k[4]}
        for k in keys
    ]


def _session_script(case, submissions):
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
        )
    ]
    script.extend(
        _validate_block(rows, case.canticle, case.canto, case.line_start)
        for rows in submissions
    )
    script.append("Done.")
    return script


def test_evaluate_accumulates_union_across_submissions(toolkit):
    case = case_by_id("rel-inf01-007")
    by_pred = _gold_by_predicate(case)
    assert len(by_pred) >= 3  # a real multi-predicate unit
    # One validate_candidate call per predicate, in text order.
    submissions = [_rows_for(keys) for _, keys in sorted(by_pred.items())]
    result = run_unit(
        transport=StubTransport(_session_script(case, submissions)),
        toolkit=toolkit,
        canticle=case.canticle,
        canto=case.canto,
        line_start=case.line_start,
        line_end=case.line_end,
        workflow="predicate",
    )

    accumulated = evaluate_unit(result, case=case, accumulate=True)
    assert accumulated.accumulate is True
    assert accumulated.workflow == "predicate"
    # No single submission covered gold; the per-predicate latest states do.
    assert accumulated.exact_first is False
    assert accumulated.exact_final is True
    assert accumulated.missing == [] and accumulated.extra == []
    # Unit-level convergence keeps its turn-budget semantics; a 6-predicate
    # interleaved session legitimately exceeds it (the per-predicate first-pass
    # rate is the fine-grained convergence signal for this workflow).
    assert accumulated.converged == (result.turns <= CONVERGENCE_TURN_BUDGET)
    assert result.turns > CONVERGENCE_TURN_BUDGET
    # Every predicate's first (and only) coverage was exact.
    assert accumulated.preds_total == len(by_pred)
    assert accumulated.preds_first_pass == len(by_pred)

    # Without accumulation the last submission alone is compared, as before.
    plain = evaluate_unit(result, case=case)
    assert plain.accumulate is False
    assert plain.exact_final is False


def test_predicate_first_pass_uses_first_coverage_not_the_final_union(toolkit):
    case = case_by_id("rel-inf01-007")
    by_pred = _gold_by_predicate(case)
    p1 = min(by_pred)
    submissions = [_rows_for(keys) for pred, keys in sorted(by_pred.items())]
    broken_first = [dict(submissions[0][0], role="obj")]  # wrong first frame
    submissions[0:1] = [broken_first, _rows_for(by_pred[p1])]  # then corrected
    result = run_unit(
        transport=StubTransport(_session_script(case, submissions)),
        toolkit=toolkit,
        canticle=case.canticle,
        canto=case.canto,
        line_start=case.line_start,
        line_end=case.line_end,
        workflow="predicate",
    )

    evaluation = evaluate_unit(result, case=case, accumulate=True)
    assert evaluation.exact_final is True  # the union covers gold completely
    assert evaluation.preds_total == len(by_pred)
    assert evaluation.preds_first_pass == len(by_pred) - 1  # only p1's first try broke
    assert 0.0 < evaluation.predicate_first_pass_rate < 1.0


def test_case_record_serializes_workflow_and_predicate_metrics():
    data = UnitEvaluation(case_id="x", category="control", unit={}).to_dict()
    assert data["workflow"] == "unit" and data["accumulate"] is False
    assert data["preds_first_pass"] == 0 and data["preds_total"] == 0
    assert data["predicate_first_pass_rate"] is None

    rated = UnitEvaluation(
        case_id="y", category="control", unit={}, preds_first_pass=3, preds_total=4
    ).to_dict()
    assert rated["predicate_first_pass_rate"] == 0.75


def test_report_aggregates_pooled_predicate_first_pass_rate():
    report = BenchmarkReport()
    report.add(
        UnitEvaluation(case_id="a", category="control", unit={},
                       preds_first_pass=1, preds_total=2)
    )
    report.add(
        UnitEvaluation(case_id="b", category="control", unit={},
                       preds_first_pass=3, preds_total=4)
    )
    assert report.metrics()["predicate_first_pass_rate"] == round(4 / 6, 4)


# --- resume support (interrupted --log files) ---------------------------------------------------------


def _perfect_script_for(case):
    rows = _gold_rows_as_dicts(case.canticle, case.canto, case.line_start, case.line_end)
    return [
        _block("read_unit",
               json.dumps({"canticle": case.canticle, "canto": case.canto,
                           "line_start": case.line_start})),
        _validate_block(rows, case.canticle, case.canto, case.line_start),
        "The unit is solved.",
    ]


def test_evaluation_from_record_rebuilds_identical_aggregates(toolkit):
    """A logged case record rejoins a resumed report with identical metrics."""
    case = case_by_id("rel-inf01-007")
    result = _run(_perfect_script_for(case), toolkit,
                  canticle=case.canticle, canto=case.canto,
                  line_start=case.line_start, line_end=case.line_end)
    evaluation = evaluate_unit(result, case=case)
    evaluation.turn_seconds = [12.5, 130.0]
    evaluation.api_retries, evaluation.api_retry_seconds = 2, 40.0

    record = json.loads(json.dumps(evaluation.to_dict()))
    rebuilt = evaluation_from_record(record)

    assert rebuilt.case_id == evaluation.case_id
    assert rebuilt.exact_first and rebuilt.exact_final and rebuilt.converged
    assert rebuilt.turn_seconds == [12.5, 130.0]
    assert rebuilt.api_retries == 2 and rebuilt.api_retry_seconds == 40.0
    assert rebuilt.gold_key_set == evaluation.gold_key_set
    assert rebuilt.final_key_set == evaluation.final_key_set

    solo, resumed = BenchmarkReport(), BenchmarkReport()
    solo.add(evaluation)
    resumed.add(rebuilt)
    assert solo.metrics() == resumed.metrics()
    assert solo.role_table() == resumed.role_table()


def test_load_log_skips_blank_and_torn_lines(tmp_path):
    log = tmp_path / "bench.log"
    good = {"record": "case", "case_id": "x"}
    log.write_text(json.dumps(good) + "\n\n" + '{"record": "case", "case_i')
    assert load_log(str(log)) == [good]


def test_prepare_resume_filters_selection_and_workflow():
    first = case_by_id("ctl-inf01-010")
    second = case_by_id("quo-pur01-046")
    done = {
        "record": "case",
        "case_id": first.case_id,
        "workflow": "unit",
        "unit": {"canticle": first.canticle, "canto": first.canto,
                 "line_start": first.line_start, "line_end": first.line_end},
        "exact_final": True,
    }
    records = [
        done,
        {**done, "case_id": second.case_id, "workflow": "predicate"},  # other scoring
        {**done, "case_id": "no-such-case"},  # outside this selection
        {"record": "summary"},
    ]
    loaded, remaining = prepare_resume(records, [first, second], "unit")
    assert [ev.case_id for ev in loaded] == [first.case_id]
    assert [case.case_id for case in remaining] == [second.case_id]


def test_prepare_resume_reruns_unrebuildable_records(toolkit, capsys):
    """A record whose gold artifact cannot be reloaded is re-run, not dropped."""
    case = case_by_id("ctl-inf01-010")
    broken = {
        "record": "case",
        "case_id": case.case_id,
        "workflow": "unit",
        "unit": {"canticle": "inferno", "canto": 99999,
                 "line_start": 1, "line_end": 3},
    }
    loaded, remaining = prepare_resume([broken], [case], "unit")
    assert loaded == []
    assert [c.case_id for c in remaining] == [case.case_id]
    assert "could not reload" in capsys.readouterr().err


def test_run_benchmark_seeds_resumed_report_into_the_aggregate(toolkit):
    prior_case = case_by_id("ctl-inf01-010")
    gold = frozenset(gold_row_keys(prior_case.canticle, prior_case.canto,
                                   prior_case.line_start, prior_case.line_end))
    prior = UnitEvaluation(
        case_id=prior_case.case_id,
        category=prior_case.category,
        unit={"canticle": prior_case.canticle, "canto": prior_case.canto,
              "line_start": prior_case.line_start, "line_end": prior_case.line_end},
        turns=2, submissions=2, exact_first=False, exact_final=True, converged=True,
        turn_seconds=[100.0],
        gold_key_set=gold,
        final_key_set=gold,
    )
    report = BenchmarkReport()
    report.add(prior)

    case = case_by_id("quo-pur01-046")
    rows = _gold_rows_as_dicts(case.canticle, case.canto, case.line_start, case.line_end)
    script = [_validate_block(rows, case.canticle, case.canto, case.line_start), "solved"]
    result = run_benchmark([case], StubTransport(script), toolkit=toolkit, report=report)

    assert len(result) == 2
    metrics = result.metrics()
    assert metrics["units"] == 2
    assert metrics["one_shot_exact_match_rate"] == 0.5
    # The resumed session's wall clock counts toward the summed total.
    assert metrics["wall_clock_seconds"] >= 100.0


def test_main_resumes_existing_log_appends_and_sums_session_time(
    toolkit, tmp_path, monkeypatch, capsys
):
    """Re-running an interrupted log skips finished cases and appends the rest.

    The summary must carry no start/end span (idle time between attempts would
    poison it) — only summed per-session durations via the aggregate metrics.
    """
    first = case_by_id("ctl-inf01-010")
    second = case_by_id("quo-pur01-046")

    log = tmp_path / "bench.log"
    with log.open("w", encoding="utf-8") as sink:
        run_benchmark([first], StubTransport(_perfect_script_for(first)),
                      toolkit=toolkit, sink=sink)
    with log.open("a", encoding="utf-8") as sink:  # stale completion marker
        sink.write(json.dumps({"record": "summary"}) + "\n")

    captured = {}

    def fake_run(cases_, transport, *, sink=None, report=None, **kwargs):
        captured["cases"] = cases_
        captured["seeded"] = [ev.case_id for ev in report.evaluations]
        for case in cases_:
            gold = frozenset(gold_row_keys(case.canticle, case.canto,
                                           case.line_start, case.line_end))
            ev = UnitEvaluation(
                case_id=case.case_id, category=case.category,
                unit={"canticle": case.canticle, "canto": case.canto,
                      "line_start": case.line_start, "line_end": case.line_end},
                turns=1, submissions=1, exact_first=True, exact_final=True,
                converged=True, turn_seconds=[7.0],
                gold_key_set=gold, final_key_set=gold,
            )
            if sink is not None:
                record = ev.to_dict()
                record["final_text"] = "solved"
                record["trace"] = {"record": "session"}
                sink.write(json.dumps(record, ensure_ascii=False) + "\n")
            report.add(ev)
        return report

    monkeypatch.setattr(bench_module, "run_benchmark", fake_run)
    monkeypatch.setattr(bench_module, "HarnessStatusLine", None)
    monkeypatch.setattr(bench_module, "PromptXmlTransport", lambda **kw: None)
    monkeypatch.setattr(bench_module, "llm7shi_generate", lambda *a, **k: None)

    rc = bench_module.main([
        "--model", "stub", "--log", str(log),
        "--case-id", first.case_id, "--case-id", second.case_id,
    ])

    assert rc == 0
    out = capsys.readouterr().out
    assert f"resume: 1 completed case(s) loaded from {log}" in out
    assert [c.case_id for c in captured["cases"]] == [second.case_id]
    assert captured["seeded"] == [first.case_id]

    records = [json.loads(line) for line in log.read_text().splitlines()]
    assert [r["record"] for r in records] == ["case", "case", "summary"]
    summary = records[-1]
    prior_turns = sum(records[0]["turn_seconds"])
    assert summary["units"] == 2
    assert summary["one_shot_exact_match_rate"] == 1.0  # both sessions hit gold first
    assert summary["wall_clock_seconds"] == round(prior_turns + 7.0, 1)
    assert "started_at" not in summary  # no start/end span: meaningless across attempts
