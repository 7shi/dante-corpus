"""Deterministic tests for the Stage 1 agent runner (`harness/runner/agent.py`).

No model calls: scripted `StubTransport` sessions run through the real loop, the
real `GrammarToolkit`, and the real prompts. Covers milestone 1.2's contract —
prompt assembly, nudge policy, transcript-derived candidate rows, trace records —
plus the carry-over disciplines from the live probe (TOOLCALL.md T4): a
non-colliding few-shot demo and no nudging of capability failures.
"""

import json

import pytest

from harness.runner.agent import (
    MAX_NUDGES,
    NUDGE_MESSAGE,
    SESSION_MAX_TURNS,
    UnitResult,
    _last_validate_call,
    run_unit,
)
from harness.runner.prompts import few_shot_messages, system_prompt, unit_task
from harness.runner.tools import TOOL_SPECS, GrammarToolkit, tool_specs
from harness.toolcall import StubTransport, is_parse_error, parse_tool_calls


def _block(name: str, arguments: str | dict) -> str:
    args = arguments if isinstance(arguments, str) else json.dumps(arguments)
    return (
        "<tool_call>\n"
        f'{{"name": "{name}", "arguments": {args}}}\n'
        "</tool_call>"
    )


def _validate_block(rows, line_start=1):
    return _block(
        "validate_candidate",
        {
            "canticle": "inferno",
            "canto": 1,
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


# The famous opening unit (Inferno I.1-3), as in test_harness_tools.py.
GOOD_ROWS = [
    _row(2, 2, "ritrovai", "subj"),
    _row(2, 2, "ritrovai", "obl:in", 1, 2, "mezzo"),
    _row(2, 2, "ritrovai", "obl:per", 2, 5, "selva"),
    _row(3, 6, "smarrita", "subj", 3, 4, "via"),
]

BAD_ROWS = [_row(99, 1, "inesistente", "subj")]


@pytest.fixture()
def toolkit():
    return GrammarToolkit()


def _run(script, toolkit_, **kwargs):
    kwargs.setdefault("canticle", "inferno")
    kwargs.setdefault("canto", 1)
    kwargs.setdefault("line_start", 1)
    return run_unit(transport=StubTransport(script), toolkit=toolkit_, **kwargs)


# --- prompt assembly ---------------------------------------------------------------------


def test_system_prompt_joins_protocol_contract_and_specs():
    prompt = system_prompt(TOOL_SPECS)
    # 5-step protocol present...
    for fragment in ("Step 1", "Step 5", "pro-drop", "validate_candidate"):
        assert fragment in prompt
    # ...wire contract present...
    for fragment in ("<tool_call>", 'ok="false"'):
        assert fragment in prompt
    # ...and every closed tool listed by name.
    for name in ("read_unit", "search_corpus", "validate_candidate"):
        assert f'"name": "{name}"' in prompt


def test_unit_task_names_the_target_unit():
    task = unit_task("purgatorio", 30, 90, 93)
    assert "purgatorio 30" in task and "lines 90-93" in task
    single = unit_task("inferno", 1, 1)
    assert "inferno 1" in single and "line 1" in single


def test_few_shot_demo_parses_and_does_not_collide():
    """The probe's 'cammin' demo was echoed into every final answer; the runner
    demo must parse cleanly and contain nothing a fixture could echo."""
    assistant_turns = "\n".join(
        m["content"] for m in few_shot_messages() if m["role"] == "assistant"
    )
    items = parse_tool_calls(assistant_turns)
    assert len(items) == 1 and not is_parse_error(items[0])
    assert items[0]["function"]["name"] == "search_corpus"
    blob = json.dumps(few_shot_messages(), ensure_ascii=False)
    assert "cammin" not in blob and "ritrovai" not in blob and "diritta" not in blob


def test_opening_messages_shape():
    from harness.runner.agent import _opening_messages

    specs = tool_specs()
    messages = _opening_messages(specs, "inferno", 1, 1, None)
    roles = [m["role"] for m in messages]
    # system -> demo exchange (user/assistant/user) -> task
    assert roles == ["system", "user", "assistant", "user", "user"]
    assert messages[0]["content"] == system_prompt(specs)
    assert "<task>" in messages[-1]["content"]
    # The demo exchange sits between the system prompt and the task.
    assert "(Demonstration only.)" in messages[1]["content"]


# --- happy path ---------------------------------------------------------------------------


def test_run_unit_converges_without_nudges(toolkit):
    script = [
        _block("read_unit", '{"canticle": "inferno", "canto": 1, "line_start": 1}'),
        _validate_block(GOOD_ROWS),
        "The unit is solved: ritrovai governs a pro-drop subject and two obliques.",
    ]
    result = _run(script, toolkit)
    assert isinstance(result, UnitResult)
    assert result.text.startswith("The unit is solved")
    assert result.turns == 3
    assert result.exhausted is False
    assert result.nudges == 0
    assert result.protocol_complete is True
    assert result.valid_seen is True
    assert len(result.validations) == 1
    assert result.candidate_rows == GOOD_ROWS


def test_run_unit_self_corrects_on_validation_errors(toolkit):
    script = [
        _block("read_unit", '{"canticle": "inferno", "canto": 1, "line_start": 1}'),
        _validate_block(BAD_ROWS),
        _validate_block(GOOD_ROWS),
        "Converged after fixing the predicate anchor.",
    ]
    result = _run(script, toolkit)
    assert result.nudges == 0
    assert result.protocol_complete is True
    assert [v["result"]["valid"] for v in result.validations] == [False, True]
    assert result.valid_seen is True
    assert result.candidate_rows == GOOD_ROWS


def test_run_unit_reports_upstream_feedback(toolkit):
    feedback = [{"layer": "L4", "description": "impossible head attachment"}]
    call = {
        "canticle": "inferno",
        "canto": 1,
        "line_start": 1,
        "candidate_rows": GOOD_ROWS,
        "upstream_feedback": feedback,
    }
    script = [
        _block("read_unit", '{"canticle": "inferno", "canto": 1, "line_start": 1}'),
        _block("validate_candidate", call),
        "Filed upstream feedback.",
    ]
    result = _run(script, toolkit)
    assert result.upstream_feedback == feedback
    assert toolkit.upstream_log[0]["layer"] == "L4"


# --- nudge policy --------------------------------------------------------------------------


def test_no_call_final_answer_gets_one_nudge_then_converges(toolkit):
    script = [
        "Nel mezzo del cammin di nostra vita mi ritrovai per una selva oscura. "
        "(answers in prose without ever calling a tool)",
        _block("read_unit", '{"canticle": "inferno", "canto": 1, "line_start": 1}'),
        _validate_block(GOOD_ROWS),
        "Validated now.",
    ]
    result = _run(script, toolkit)
    assert result.nudges == 1
    assert result.protocol_complete is True
    assert result.turns == 4
    assert result.candidate_rows == GOOD_ROWS
    # The reminder rides as an ordinary user turn between the two attempts.
    contents = [m["content"] for m in result.messages if m["role"] == "user"]
    assert any(NUDGE_MESSAGE == c for c in contents)


def test_prose_before_any_call_is_not_mistaken_for_a_validated_session(toolkit):
    script = [
        "I would start by reading the unit... (no calls)",
        "Let me think about it some more. (still no calls)",
    ]
    result = _run(script, toolkit, max_nudges=MAX_NUDGES)
    assert result.nudges == 1
    assert result.protocol_complete is False
    assert result.validations == []
    assert result.valid_seen is False
    # Second prose answer stands as the final one; no third attempt is funded.
    assert result.text.endswith("(still no calls)")
    assert result.turns == 2


def test_giving_up_after_failed_validation_is_never_nudged(toolkit):
    """A give-up after real validation work is a capability failure: measure it.
    The protocol was followed (validate-then-answer), so no reminder is due —
    the invalidity shows up in `valid_seen`, not in compliance."""
    script = [
        _block("read_unit", '{"canticle": "inferno", "canto": 1, "line_start": 1}'),
        _validate_block(BAD_ROWS),
        "I cannot fix this error; giving up.",
    ]
    result = _run(script, toolkit)
    assert result.nudges == 0
    assert result.protocol_complete is True
    assert result.validations and result.valid_seen is False
    assert result.text == "I cannot fix this error; giving up."


def test_exhausted_session_is_never_nudged(toolkit):
    endless = [_block("read_unit", '{"canticle": "inferno", "canto": 1}')]
    result = _run(endless * 10, toolkit, max_turns=2)
    assert result.exhausted is True and result.nudges == 0
    assert result.turns == 2 and result.text == ""


def test_max_nudges_zero_disables_reminders(toolkit):
    script = ["prose answer without any tool work"]
    result = _run(script, toolkit, max_nudges=0)
    assert result.nudges == 0
    assert result.text == "prose answer without any tool work"
    assert result.protocol_complete is False
    assert result.turns == 1


def test_nudged_resume_shares_the_turn_budget(toolkit):
    script = ["prose without calls", "second prose answer"]
    result = _run(script, toolkit, max_turns=2, max_nudges=5)
    # Attempt 1 spends turn 1 on prose and earns a reminder; only one budgeted
    # turn remains, so the resumed session spends it on the second prose answer.
    assert result.turns == 2
    assert result.nudges == 1
    assert result.text.endswith("second prose answer")
    assert result.protocol_complete is False


# --- transcript-derived facts ---------------------------------------------------------------


def test_last_validate_call_scans_newest_first_and_skips_noise(toolkit):
    messages = [
        {"role": "user", "content": "task"},
        {
            "role": "assistant",
            "content": _block("search_corpus", '{"query": {"lemma": "x"}}'),
        },
        {"role": "user", "content": '<tool_result tool="search_corpus" ok="true">\n[]\n</tool_result>'},
        {"role": "assistant", "content": _validate_block([_row(2, 2, "a", "subj")])},
    ]
    arguments = _last_validate_call(messages)
    assert arguments["candidate_rows"] == [_row(2, 2, "a", "subj")]
    assert _last_validate_call(messages[:2]) is None


def test_candidate_rows_reflect_the_last_submission(toolkit):
    script = [
        _validate_block(BAD_ROWS),
        _validate_block(GOOD_ROWS),
        "done",
    ]
    result = _run(script, toolkit)
    assert result.candidate_rows == GOOD_ROWS


# --- trace record ---------------------------------------------------------------------------


def test_trace_record_round_trips_with_transcript(toolkit):
    script = [
        _validate_block(GOOD_ROWS),
        "final answer",
    ]
    result = _run(script, toolkit)
    record = result.trace_record()
    blob = json.dumps(record, ensure_ascii=False)
    loaded = json.loads(blob)
    assert loaded["record"] == "session"
    assert loaded["unit"]["canticle"] == "inferno"
    assert loaded["valid"] is True and loaded["validations"] == 1
    assert loaded["candidate_rows"] == GOOD_ROWS
    assert loaded["messages"][0]["role"] == "system"
    assert loaded["outcomes"][0]["tool"] == "validate_candidate"

    slim = result.trace_record(include_transcript=False)
    assert "messages" not in slim


def test_default_session_constants_leave_room_for_correction():
    assert SESSION_MAX_TURNS >= 10
    assert MAX_NUDGES >= 1


def test_llm7shi_generate_builds_stateless_adapter(monkeypatch):
    """The proven probe adapter must keep forwarding model/temperature verbatim."""
    import harness.runner.agent as agent_module

    captured = {}

    def fake_generate_with_schema(messages, schema=None, **kwargs):
        captured.update(kwargs, schema=schema)

        class Response:
            text = "reply"

        return Response()

    monkeypatch.setattr(
        "llm7shi.compat.generate_with_schema", fake_generate_with_schema
    )
    generate = agent_module.llm7shi_generate("ollama:m", temperature=0.3)
    assert generate([{"role": "user", "content": "hi"}]) == "reply"
    assert captured["model"] == "ollama:m"
    assert captured["temperature"] == 0.3
