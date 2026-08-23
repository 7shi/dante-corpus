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


# --- live-run observability (harness/PLAN.md §4 item 5) -----------------------------------


def test_nudged_resume_marks_a_minor_pass_boundary_when_watched(toolkit, capsys):
    script = [
        "prose answer without any tool work",
        _validate_block(GOOD_ROWS),
        "Validated now.",
    ]
    result = _run(script, toolkit, progress=True)
    assert result.nudges == 1
    err = capsys.readouterr().err
    assert "\n----- nudged resume -----\n" in err


def test_run_unit_prints_nothing_without_the_progress_flag(toolkit, capsys):
    script = [
        "prose answer without any tool work",
        _validate_block(GOOD_ROWS),
        "Validated now.",
    ]
    result = _run(script, toolkit)
    assert result.nudges == 1
    assert capsys.readouterr().err == ""


def test_agent_cli_announces_its_single_session(monkeypatch, capsys):
    """Every live CLI announces each session with its [index/total] position."""
    import harness.runner.agent as agent_module

    def fake_transport(generate=None):
        return StubTransport([_validate_block(GOOD_ROWS), "Validated now."])

    monkeypatch.setattr(agent_module, "PromptXmlTransport", fake_transport)
    rc = agent_module.main(
        ["--canticle", "inferno", "--canto", "1", "--line-start", "1"]
    )
    assert rc == 0
    err = capsys.readouterr().err
    assert "\n===== [1/1] inferno 1 1 =====\n" in err


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


def test_submissions_preserve_first_to_last_order(toolkit):
    """The 1-shot metric reads submissions[0]; candidate_rows stays the last."""
    other = [_row(2, 2, "ritrovai", "obj")]
    script = [
        _validate_block(other),
        _validate_block(BAD_ROWS),
        _validate_block(GOOD_ROWS),
        "done",
    ]
    result = _run(script, toolkit)
    assert result.submissions == [other, BAD_ROWS, GOOD_ROWS]
    assert result.first_candidate_rows == other
    assert result.candidate_rows == GOOD_ROWS


def test_submissions_empty_without_validate_calls(toolkit):
    result = _run(["prose only"], toolkit, max_nudges=0)
    assert result.submissions == []
    assert result.first_candidate_rows == []


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


def test_llm7shi_generate_rides_client_history(monkeypatch):
    """The adapter mirrors the loop's transcript into a per-session Client:
    system prompt, demo exchange, tool feedback, and a fresh Client whenever a
    new session's shorter transcript breaks the sync invariant."""
    import sys

    import harness.runner.agent as agent_module

    created = []

    class FakeClient:
        def __init__(self, model="", temperature=None, file=None, show_params=True,
                     **kwargs):
            self.model = model
            self.temperature = temperature
            self.file = file
            self.show_params = show_params
            self.history = []
            created.append(self)

        def set_system_prompt(self, prompt):
            if self.history and self.history[0].get("role") == "system":
                self.history[0]["content"] = prompt
            else:
                self.history.insert(0, {"role": "system", "content": prompt})

        def __call__(self, prompt):
            class _Response:
                text = f"reply:{len(self.history)}"

            self.history.append({"role": "user", "content": prompt})
            self.history.append({"role": "assistant", "content": _Response.text})
            return _Response()

    monkeypatch.setattr("llm7shi.Client", FakeClient)
    generate = agent_module.llm7shi_generate("ollama:m", temperature=0.3, quiet=True)

    opening = [
        {"role": "system", "content": "sys"},
        {"role": "user", "content": "demo?"},
        {"role": "assistant", "content": "demo!"},
        {"role": "user", "content": "task-A"},
    ]
    first = generate([dict(m) for m in opening])
    assert first == "reply:3"  # system + demo pair were mirrored before the call
    client = created[-1]
    assert client.model == "ollama:m" and client.temperature == 0.3
    assert client.file is sys.stderr  # §4 item 5: streaming pinned to stderr
    assert client.show_params is False
    assert [m["role"] for m in client.history] == [
        "system", "user", "assistant", "user", "assistant",
    ]
    assert client.history[3]["content"] == "task-A"

    # Next loop turn: transcript grew by the reply plus a tool-result user message.
    transcript = opening + [
        {"role": "assistant", "content": first},
        {"role": "user", "content": "<tool_result>feedback</tool_result>"},
    ]
    generate(transcript)
    assert len(created) == 1  # same session, same Client
    assert client.history[5]["content"] == "<tool_result>feedback</tool_result>"
    assert client.history[6]["role"] == "assistant"

    # A new session's shorter opening breaks the sync invariant -> fresh Client.
    fresh = [dict(m) for m in opening]
    fresh[3] = {"role": "user", "content": "task-B"}
    generate(fresh)
    assert len(created) == 2
    assert created[-1].history[3]["content"] == "task-B"
    # The previous session's history never leaked into the new one.
    assert len(created[-1].history) == 5


def test_llm7shi_generate_reset_regenerates_the_client(monkeypatch):
    """Explicit reset() is the primary session signal: the next call builds a
    fresh Client regardless of any length continuation."""
    import harness.runner.agent as agent_module

    created = []

    class FakeClient:
        def __init__(self, model="", file=None, **kwargs):
            self.history = []
            created.append(self)

        def set_system_prompt(self, prompt):
            self.history.insert(0, {"role": "system", "content": prompt})

        def __call__(self, prompt):
            class _Response:
                text = "ok"

            self.history.append({"role": "user", "content": prompt})
            self.history.append({"role": "assistant", "content": "ok"})
            return _Response()

    monkeypatch.setattr("llm7shi.Client", FakeClient)
    generate = agent_module.llm7shi_generate("ollama:m")
    generate([{"role": "user", "content": "one"}])
    assert len(created) == 1

    generate.reset()
    # Same length as a legitimate continuation would have — reset wins anyway.
    generate([
        {"role": "user", "content": "one"},
        {"role": "assistant", "content": "ok"},
        {"role": "user", "content": "two"},
    ])
    assert len(created) == 2
    assert [m["content"] for m in created[-1].history][-2:] == ["two", "ok"]


def test_run_unit_resets_stateful_transports_at_session_start(toolkit):
    """Each session opens with transport.reset() when the transport has one."""
    from harness.toolcall import StubTransport

    class ResettableStub(StubTransport):
        resets: int = 0

        def reset(self):
            self.resets += 1

    script = [
        _validate_block(GOOD_ROWS),
        "final answer",
    ]
    transport = ResettableStub(script + script)
    run_unit(
        transport=transport,
        toolkit=toolkit,
        canticle="inferno",
        canto=1,
        line_start=1,
    )
    run_unit(
        transport=transport,
        toolkit=toolkit,
        canticle="inferno",
        canto=1,
        line_start=1,
    )
    assert transport.resets == 2


def test_summary_reports_per_turn_timing(toolkit):
    script = [
        _validate_block(GOOD_ROWS),
        "final answer",
    ]
    result = _run(script, toolkit)
    summary = result.summary()
    assert "turn seconds:" in summary and "max=" in summary


# --- workflow selection ------------------------------------------------------------------


def test_default_workflow_teaches_whole_unit_validation(toolkit):
    result = _run(["Done.", "Still done."], toolkit)
    assert result.workflow == "unit"
    system = result.messages[0]["content"]
    assert "Submit all rows of the unit in one `validate_candidate` call" in system


def test_predicate_workflow_selects_per_predicate_protocol(toolkit):
    result = _run(["Done.", "Still done."], toolkit, workflow="predicate")
    assert result.workflow == "predicate"
    system = result.messages[0]["content"]
    assert "one at a time" in system
    assert "Never batch several predicates into one call" in system
    assert result.trace_record(include_transcript=False)["workflow"] == "predicate"


def test_unknown_workflow_fails_loudly(toolkit):
    with pytest.raises(KeyError):
        _run(["Done.", "Still done."], toolkit, workflow="verse")
