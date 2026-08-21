"""Deterministic tests for the Tool Call Protocol library (`harness/toolcall/`).

Covers the validation plan of `harness/TOOLCALL.md` §5.1: parser/formatter edge cases,
prompt-contract self-consistency, transport stubs, and scripted multi-turn convergence
through the real loop code with the real `GrammarToolkit` — no network, no model.
"""

import json

import pytest

from harness.runner.tools import GrammarToolkit, TOOL_SPECS
from harness.toolcall import (
    LoopResult,
    PromptXmlTransport,
    StubTransport,
    execute_tool_calls,
    few_shot_messages,
    format_tool_result,
    is_parse_error,
    parse_tool_calls,
    run_tool_loop,
    tool_specs_section,
    xml_contract_section,
)


def _call(name: str, arguments: dict | str) -> dict:
    args = arguments if isinstance(arguments, str) else json.dumps(arguments)
    return {"type": "function", "function": {"name": name, "arguments": args}}


def _block(name: str, arguments: str) -> str:
    """Current wire format: the block body is one JSON object."""
    return (
        "<tool_call>\n"
        f'{{"name": "{name}", "arguments": {arguments}}}\n'
        "</tool_call>"
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


# The opening unit (Inferno I.1-3), as in test_harness_tools.py.
GOOD_ROWS = [
    _row(2, 2, "ritrovai", "subj"),
    _row(2, 2, "ritrovai", "obl:in", 1, 2, "mezzo"),
    _row(2, 2, "ritrovai", "obl:per", 2, 5, "selva"),
    _row(3, 6, "smarrita", "subj", 3, 4, "via"),
]


# --- parse_tool_calls -------------------------------------------------------------------


def test_parse_bare_call():
    items = parse_tool_calls(_block("read_unit", '{"canticle": "inferno", "canto": 1}'))
    assert items == [_call("read_unit", '{"canticle": "inferno", "canto": 1}')]


def test_parse_call_wrapped_in_prose_and_fences():
    text = (
        "Let me read the unit first.\n"
        "```xml\n"
        + _block("read_unit", '{"canticle": "inferno", "canto": 1}')
        + "\n```\n"
        "Now I will analyze it."
    )
    items = parse_tool_calls(text)
    assert len(items) == 1 and not is_parse_error(items[0])
    assert items[0]["function"]["name"] == "read_unit"


def test_parse_multiple_calls_in_order():
    text = (
        _block("read_unit", '{"canticle": "inferno", "canto": 1, "line_start": 1}')
        + "\nSome prose between calls.\n"
        + _block("search_corpus", '{"query": {"lemma": "cammin"}}')
    )
    items = parse_tool_calls(text)
    assert [it["function"]["name"] for it in items] == ["read_unit", "search_corpus"]
    assert all(not is_parse_error(it) for it in items)


def test_parse_zero_calls_yields_empty_list():
    assert parse_tool_calls("I have finished: la via è ritrovata.") == []


def test_parse_duplicate_names_kept_as_distinct_calls():
    text = _block("search_corpus", '{"query": {"lemma": "a"}}') + _block(
        "search_corpus", '{"query": {"lemma": "b"}}'
    )
    items = parse_tool_calls(text)
    assert len(items) == 2 and all(not is_parse_error(it) for it in items)


def test_parse_multiline_json_arguments_normalize_whitespace():
    arguments = '{\n  "canticle": "inferno",\n  "canto": 1,\n  "line_start": 1\n}'
    items = parse_tool_calls(_block("read_unit", arguments))
    canonical = items[0]["function"]["arguments"]
    assert json.loads(canonical) == json.loads(arguments)
    assert "\n" not in canonical  # canonical form is compact


def test_parse_preserves_unicode_arguments():
    arguments = '{"query": {"word": "per una selva oscura"}}'
    items = parse_tool_calls(_block("search_corpus", arguments))
    assert json.loads(items[0]["function"]["arguments"])["query"]["word"] == (
        "per una selva oscura"
    )


def test_parse_tolerates_prose_around_json_body():
    text = (
        "<tool_call>\n"
        'Sure — reading the unit now: {"name": "read_unit", '
        '"arguments": {"canticle": "inferno", "canto": 1}}\n'
        "</tool_call>"
    )
    items = parse_tool_calls(text)
    assert items == [_call("read_unit", '{"canticle": "inferno", "canto": 1}')]


def test_parse_arguments_as_json_string_is_accepted_verbatim():
    arguments = '{"canticle": "inferno", "canto": 1}'
    text = (
        "<tool_call>\n"
        f'{{"name": "read_unit", "arguments": {json.dumps(arguments)}}}\n'
        "</tool_call>"
    )
    items = parse_tool_calls(text)
    assert items == [_call("read_unit", arguments)]


def test_parse_non_object_body_is_error_envelope():
    items = parse_tool_calls("<tool_call>\n[1, 2]\n</tool_call>")
    assert is_parse_error(items[0]) and "single JSON object" in items[0]["error"]


def test_parse_body_without_name_is_error_envelope():
    items = parse_tool_calls('<tool_call>\n{"arguments": {}}\n</tool_call>')
    assert is_parse_error(items[0])
    assert "name" in items[0]["error"]


def test_parse_wrong_arguments_type_is_error_envelope():
    items = parse_tool_calls('<tool_call>\n{"name": "read_unit", "arguments": 5}\n</tool_call>')
    assert is_parse_error(items[0])
    assert items[0]["tool"] == "read_unit" and "arguments" in items[0]["error"]


def test_parse_unparsable_arguments_string_is_error_envelope():
    # A string-typed "arguments" must itself be JSON; garbage surfaces as an error
    # envelope attributed to the named tool.
    text = '<tool_call>\n{"name": "read_unit", "arguments": "oops"}\n</tool_call>'
    items = parse_tool_calls(text)
    assert is_parse_error(items[0]) and items[0]["tool"] == "read_unit"
    assert "unparsable" in items[0]["error"]


def test_parse_unparsable_body_is_error_envelope():
    # A truncated block poisons the whole JSON document; the error teaches the shape.
    text = '<tool_call>\n{"name": "read_unit", "arguments": {"canticle"\n</tool_call>'
    items = parse_tool_calls(text)
    assert len(items) == 1 and is_parse_error(items[0])
    assert "single JSON object" in items[0]["error"]


def test_parse_missing_arguments_field_defaults_to_empty_object():
    # Native convention: tool calls without an arguments field mean {}.
    items = parse_tool_calls('<tool_call>\n{"name": "read_unit"}\n</tool_call>')
    assert items == [_call("read_unit", "{}")]


def test_parse_unterminated_block_is_error_envelope():
    text = '<tool_call>\n{"name": "read_unit", "arguments": {"canticle"'
    items = parse_tool_calls(text)
    assert is_parse_error(items[0]) and "unterminated" in items[0]["error"]


# --- format_tool_result -----------------------------------------------------------------


def test_format_success_envelope():
    outcome = {"ok": True, "tool": "read_unit", "result": {"unit": {"canto": 1}}}
    block = format_tool_result(outcome)
    assert block.startswith('<tool_result tool="read_unit" ok="true">')
    assert block.endswith("</tool_result>")
    payload = block.split("\n")[1]
    assert json.loads(payload) == {"unit": {"canto": 1}}


def test_format_error_envelope():
    outcome = {"ok": False, "tool": "read_unit", "error": "unknown canticle: limbo"}
    block = format_tool_result(outcome)
    assert 'ok="false"' in block
    assert json.loads(block.split("\n")[1]) == {"error": "unknown canticle: limbo"}


def test_format_keeps_non_ascii_literal():
    outcome = {"ok": True, "tool": "search_corpus", "result": [{"word": "selva"}]}
    block = format_tool_result(outcome)
    assert "selva" in block
    assert "\\u" not in block


def test_format_round_trip_stability():
    outcome = {
        "ok": True,
        "tool": "validate_candidate",
        "result": {"valid": True, "errors": [], "warnings": []},
    }
    assert format_tool_result(outcome) == format_tool_result(outcome)
    payload = format_tool_result(outcome).split("\n")[1]
    assert json.loads(payload)["valid"] is True


# --- prompt contract ----------------------------------------------------------------------


def test_contract_mentions_wire_format():
    section = xml_contract_section()
    for fragment in ("<tool_call>", "</tool_call>", '"name"', '"arguments"'):
        assert fragment in section


def test_few_shot_assistant_turn_parses_to_a_well_formed_call():
    assistant_turns = [
        m["content"] for m in few_shot_messages() if m["role"] == "assistant"
    ]
    items = parse_tool_calls("\n".join(assistant_turns))
    assert len(items) == 1 and not is_parse_error(items[0])
    assert items[0]["function"]["name"] == "search_corpus"


def test_tool_specs_section_renders_valid_json_with_all_names():
    section = tool_specs_section(TOOL_SPECS)
    functions = json.loads(section.split("```json")[1].split("```")[0])
    assert [f["name"] for f in functions] == [
        "read_unit",
        "search_corpus",
        "validate_candidate",
    ]


# --- transports ---------------------------------------------------------------------------


def test_stub_transport_routes_raw_strings_through_real_parser():
    stub = StubTransport([_block("read_unit", '{"canticle": "inferno", "canto": 1}')])
    response = stub.complete([], ())
    assert response.text.startswith("<tool_call>")
    assert response.tool_calls[0]["function"]["name"] == "read_unit"


def test_stub_transport_accepts_explicit_canonical_dicts():
    stub = StubTransport([{"text": "done", "tool_calls": [_call("read_unit", "{}")]}])
    response = stub.complete([], ())
    assert response.text == "done"
    assert response.tool_calls[0]["type"] == "function"


def test_stub_transport_raises_when_script_exhausted():
    stub = StubTransport(["first"])
    stub.complete([], ())
    with pytest.raises(StopIteration):
        stub.complete([], ())


def test_prompt_xml_transport_passes_messages_and_parses_reply():
    seen = {}

    def fake_generate(messages):
        seen["messages"] = messages
        return _block("search_corpus", '{"query": {"lemma": "cammin"}}')

    messages = [{"role": "user", "content": "find cammin"}]
    response = PromptXmlTransport(generate=fake_generate).complete(messages, TOOL_SPECS)
    assert seen["messages"] is messages
    assert response.tool_calls[0]["function"]["name"] == "search_corpus"


# --- loop over the real toolkit -------------------------------------------------------------


@pytest.fixture()
def toolkit():
    return GrammarToolkit()


def _opening_messages(task="Solve Inferno I lines 1-3."):
    return [{"role": "user", "content": task}]


def test_loop_converges_through_scripted_multi_turn_session(toolkit):
    script = [
        _block("read_unit", '{"canticle": "inferno", "canto": 1, "line_start": 1}'),
        _block("validate_candidate", json.dumps({
            "canticle": "inferno",
            "canto": 1,
            "line_start": 1,
            "candidate_rows": GOOD_ROWS,
        })),
        "The candidate is validated; la diritta via è smarrita.",
    ]
    result = run_tool_loop(
        transport=StubTransport(script),
        toolkit=toolkit,
        messages=_opening_messages(),
        tools=TOOL_SPECS,
    )

    assert isinstance(result, LoopResult)
    assert result.exhausted is False
    assert result.turns == 3
    assert "diritta via" in result.text
    assert len(result.outcomes) == 2 and all(o["ok"] for o in result.outcomes)
    validate_outcome = result.outcomes[1]
    assert validate_outcome["result"]["valid"] is True

    roles = [m["role"] for m in result.messages]
    assert roles == ["user", "assistant", "user", "assistant", "user", "assistant"]
    feedback = result.messages[2]["content"]
    assert '<tool_result tool="read_unit" ok="true">' in feedback
    validate_feedback = result.messages[4]["content"]
    assert '<tool_result tool="validate_candidate" ok="true">' in validate_feedback
    assert '"valid": true' in validate_feedback


def test_loop_feeds_parse_errors_back_for_self_correction(toolkit):
    script = [
        # Turn 1: truncated block body -> parse-error envelope -> fed back verbatim.
        '<tool_call>\n{"name": "read_unit", "arguments": {"canticle"\n</tool_call>',
        # Turn 2: corrected call.
        _block("read_unit", '{"canticle": "inferno", "canto": 1, "line_start": 1}'),
        "Done.",
    ]
    result = run_tool_loop(
        transport=StubTransport(script),
        toolkit=toolkit,
        messages=_opening_messages(),
        tools=TOOL_SPECS,
    )
    assert result.turns == 3 and result.text == "Done."
    assert len(result.outcomes) == 2
    assert result.outcomes[0]["ok"] is False
    assert "single JSON object" in result.outcomes[0]["error"]
    assert result.outcomes[1]["ok"] is True
    assert "single JSON object" in result.messages[2]["content"]


def test_loop_reports_hallucinated_tool_via_dispatch(toolkit):
    script = [
        _block("read_gold_skel", '{"canticle": "inferno"}'),
        _block("read_unit", '{"canticle": "inferno", "canto": 1, "line_start": 1}'),
        "Done.",
    ]
    result = run_tool_loop(
        transport=StubTransport(script),
        toolkit=toolkit,
        messages=_opening_messages(),
        tools=TOOL_SPECS,
    )
    assert result.outcomes[0]["ok"] is False
    assert "unknown tool" in result.outcomes[0]["error"]
    assert result.outcomes[1]["ok"] is True


def test_loop_executes_multiple_calls_per_turn_in_order(toolkit):
    script = [
        _block("read_unit", '{"canticle": "inferno", "canto": 1, "line_start": 1}')
        + "\n"
        + _block("search_corpus", '{"query": {"lemma": "ritrovare"}, "limit": 1}'),
        "Done.",
    ]
    result = run_tool_loop(
        transport=StubTransport(script),
        toolkit=toolkit,
        messages=_opening_messages(),
        tools=TOOL_SPECS,
    )
    assert [o["tool"] for o in result.outcomes] == ["read_unit", "search_corpus"]
    feedback = result.messages[2]["content"]
    assert feedback.count("<tool_result ") == 2
    assert feedback.index('tool="read_unit"') < feedback.index('tool="search_corpus"')


def test_loop_stops_at_turn_budget_and_reports_exhaustion(toolkit):
    endless = [_block("read_unit", '{"canticle": "inferno", "canto": 1}')] * 5
    result = run_tool_loop(
        transport=StubTransport(endless),
        toolkit=toolkit,
        messages=_opening_messages(),
        tools=TOOL_SPECS,
        max_turns=2,
    )
    assert result.exhausted is True and result.text == ""
    assert result.turns == 2 and len(result.outcomes) == 2
    # Every assistant call still receives its result block, keeping the transcript valid.
    assert result.messages[-1]["content"].count("<tool_result ") == 1


def test_execute_tool_calls_passes_error_envelopes_through(toolkit):
    mixed = [
        _call("read_unit", '{"canticle": "inferno", "canto": 1, "line_start": 1}'),
        {"ok": False, "tool": "", "error": 'missing "name" field'},
    ]
    outcomes = execute_tool_calls(toolkit, mixed)
    assert outcomes[0]["ok"] is True
    assert outcomes[1] == mixed[1]


def test_loop_does_not_mutate_opening_messages(toolkit):
    script = ["Done."]
    messages = _opening_messages()
    snapshot = [dict(m) for m in messages]
    run_tool_loop(
        transport=StubTransport(script), toolkit=toolkit, messages=messages
    )
    assert messages == snapshot


# --- probe scenario selection ---------------------------------------------------------


def test_expand_scenarios_defaults_to_all_once():
    from harness.toolcall.probe import SCENARIOS, expand_scenarios

    assert expand_scenarios() == SCENARIOS


def test_expand_scenarios_filters_by_name():
    from harness.toolcall.probe import expand_scenarios

    scenarios = expand_scenarios(selected=["read_unit", "search_corpus"])
    assert [s["name"] for s in scenarios] == ["read_unit", "search_corpus"]


def test_expand_scenarios_repeats_without_selection_regression():
    # Regression: --repeat 5 without --scenario used to be silently ignored.
    from harness.toolcall.probe import expand_scenarios

    scenarios = expand_scenarios(repeat=5)
    assert len(scenarios) == 20
    names = [s["name"] for s in scenarios]
    assert names[:4] == [
        "read_unit#1",
        "search_corpus#1",
        "validate_candidate#1",
        "read_then_validate#1",
    ]
    assert names[-1] == "read_then_validate#5"


def test_expand_scenarios_repeat_with_selection():
    from harness.toolcall.probe import expand_scenarios

    scenarios = expand_scenarios(selected=["read_unit"], repeat=3)
    assert [s["name"] for s in scenarios] == [
        "read_unit#1",
        "read_unit#2",
        "read_unit#3",
    ]
