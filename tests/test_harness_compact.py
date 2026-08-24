"""Deterministic tests for the Stage-3 compaction/pacing package.

Covers STAGE3.md §4 items 3-4: the pure history policy (`runner.compact.
compact_view`), the continuation system prompt, and the adapter's wiring of
both plus pacing — fingerprint sync (rebuild on view-prefix change), the
min-send interval (injected clock), and the shared token bucket (tmp file,
sequential "processes"). No test touches a model: `llm7shi.Client` is faked.
"""

import json

import pytest

from harness.runner.agent import (
    BYTES_PER_TOKEN,
    DEFAULT_BUCKET_DEPTH_TOKENS,
    DEFAULT_BUCKET_RATE_TOKENS_PER_MIN,
    OPENING_MESSAGE_COUNT,
    TokenBucket,
    llm7shi_generate,
)
from harness.runner.compact import (
    DIGEST_HEAD_CHARS,
    compact_view,
    digest_message,
    history_policy,
)
from harness.runner.prompts import (
    continuation_system_prompt,
    system_prompt,
)
from harness.runner.tools import TOOL_SPECS


def _block(name, arguments):
    args = json.dumps(arguments) if isinstance(arguments, dict) else arguments
    return f'<tool_call>\n{{"name": "{name}", "arguments": {args}}}\n</tool_call>'


OPENING_LEN = 5  # system + demo(user/assistant/user) + task, as the runner builds it


def _opening(task="solve inferno 1 line 1"):
    return [
        {"role": "system", "content": "system-prompt-with-steps"},
        {"role": "user", "content": "demo?"},
        {"role": "assistant", "content": _block("search_corpus", {"query": {"lemma": "Waldeinsamkeit"}})},
        {"role": "user", "content": "<tool_result>[]</tool_result>"},
        {"role": "user", "content": f"<task>{task}</task>"},
    ]


CONT_SYSTEM = "continuation-system-prompt"


# --- digest rendering ----------------------------------------------------------------------


def test_digest_names_dispatched_tools_and_head():
    content = (
        "I will read the unit first and think about the morphology.\n"
        + _block("read_unit", {"canticle": "inferno", "canto": 1, "line_start": 1})
        + "\n"
        + _block("search_corpus", {"query": {"lemma": "vita"}})
    )
    digest = digest_message(content, turn=3)
    assert digest.startswith("[turn 3; called read_unit, search_corpus]")
    assert "Waldeinsamkeit" not in digest
    assert "read the unit first" in digest
    # Tool-call JSON bodies are stripped from the prose head.
    assert '"canticle"' not in digest


def test_digest_truncates_the_prose_head_with_an_ellipsis():
    prose = " ".join(f"word{i}" for i in range(100))
    digest = digest_message(prose, turn=1)
    head = digest.split("] ", 1)[1]
    assert len(head) == DIGEST_HEAD_CHARS + 1  # +1 for the ellipsis character
    assert head.endswith("…")


def test_digest_reports_parse_errors_and_pure_prose():
    broken = 'thinking…\n<tool_call>\n{"name": "read_unit", "arguments": {'  # unterminated
    assert "called" in digest_message(broken, turn=2)  # parse-error envelope named
    prose = digest_message("just a final answer in prose", turn=4)
    assert prose == "[turn 4] just a final answer in prose"


# --- compact_view shapes -------------------------------------------------------------------


def test_call_one_serves_the_verbatim_opening():
    opening = _opening()
    view = compact_view(opening, opening_len=OPENING_LEN, continuation_system=CONT_SYSTEM)
    assert view == opening
    assert view[0] is not opening[0] or view == opening  # fresh list, equal content


def test_calls_two_plus_use_the_continuation_layout():
    payload = '{"unit": {"line_start": 1}}'  # a read_unit result body
    transcript = _opening() + [
        {"role": "assistant", "content": "reading.\n" + _block("read_unit", {"canticle": "inferno", "canto": 1, "line_start": 1})},
        {"role": "user", "content": f'<tool_result tool="read_unit" ok="true">\n{payload}\n</tool_result>'},
        {"role": "assistant", "content": "submitting.\n" + _block("validate_candidate", {"canticle": "inferno", "canto": 1, "line_start": 1, "candidate_rows": []})},
        {"role": "user", "content": '<tool_result tool="validate_candidate" ok="false">\n{"error": "row[0]: missing field"}\n</tool_result>'},
    ]
    view = compact_view(
        transcript, opening_len=OPENING_LEN, continuation_system=CONT_SYSTEM
    )
    roles = [m["role"] for m in view]
    assert roles == ["system", "user", "assistant", "user", "assistant", "user"]
    assert view[0]["content"] == CONT_SYSTEM
    # The task message follows the continuation system verbatim.
    assert view[1]["content"] == transcript[OPENING_LEN - 1]["content"]
    # The read_unit payload (user) and the validator feedback (newest user)
    # ride verbatim.
    assert view[3]["content"] == transcript[OPENING_LEN + 1]["content"]
    assert view[-1]["content"] == transcript[-1]["content"]
    # The older assistant turn (read_unit dispatch) is digested; the last
    # assistant turn (the candidate submission) stays verbatim.
    assert view[2]["content"] == digest_message(
        transcript[OPENING_LEN]["content"], 1
    )
    assert view[4]["content"] == transcript[OPENING_LEN + 2]["content"]
    # No opening demo survives into the continuation view.
    assert all("Waldeinsamkeit" not in m["content"] for m in view)


def test_older_assistant_turns_digest_but_the_last_stays_verbatim():
    a1 = "first turn.\n" + _block("read_unit", {"canticle": "inferno", "canto": 1, "line_start": 1})
    u1 = '<tool_result tool="read_unit" ok="true">\n{}\n</tool_result>'
    a2 = "second turn.\n" + _block("search_corpus", {"query": {"lemma": "vita"}})
    u2 = "<tool_result>[]</tool_result>"
    a3 = "third turn, the newest submission.\n" + _block("validate_candidate", {"canticle": "inferno", "canto": 1, "line_start": 1, "candidate_rows": []})
    u3 = '<tool_result tool="validate_candidate" ok="false">\n{"error": "x"}\n</tool_result>'
    transcript = _opening() + [
        {"role": "assistant", "content": a1},
        {"role": "user", "content": u1},
        {"role": "assistant", "content": a2},
        {"role": "user", "content": u2},
        {"role": "assistant", "content": a3},
        {"role": "user", "content": u3},
    ]
    view = compact_view(
        transcript, opening_len=OPENING_LEN, continuation_system=CONT_SYSTEM
    )
    session_view = view[2:]
    assert [m["content"] for m in session_view] == [
        digest_message(a1, 1),
        u1,
        digest_message(a2, 2),
        u2,
        a3,  # the last assistant turn verbatim
        u3,  # the newest message verbatim, last position
    ]
    digests = [session_view[0]["content"], session_view[2]["content"]]
    assert all(len(d.encode()) < 300 for d in digests)
    assert "[turn 1; called read_unit]" in digests[0]
    assert "[turn 2; called search_corpus]" in digests[1]


def test_nudge_transcripts_compact_with_the_reminder_verbatim():
    prose_answer = "I believe the answer is three predicates."
    nudge = "Do not answer in prose alone: validate a candidate."
    transcript = _opening() + [
        {"role": "assistant", "content": prose_answer},
        {"role": "user", "content": nudge},
        {"role": "assistant", "content": "fixed now.\n" + _block("validate_candidate", {"canticle": "inferno", "canto": 1, "line_start": 1, "candidate_rows": []})},
        {"role": "user", "content": '<tool_result tool="validate_candidate" ok="true">\n{"valid": true}\n</tool_result>'},
    ]
    view = compact_view(
        transcript, opening_len=OPENING_LEN, continuation_system=CONT_SYSTEM
    )
    # The pre-nudge prose answer is an *older* assistant turn: digested.
    assert view[2]["content"] == digest_message(prose_answer, 1)
    assert nudge in [m["content"] for m in view]  # the reminder is a user message: verbatim
    assert view[-2]["content"].startswith("fixed now.")  # last assistant verbatim
    assert view[-1]["content"].startswith('<tool_result tool="validate_candidate"')


def test_compact_view_never_mutates_or_aliases_the_transcript():
    transcript = _opening() + [
        {"role": "assistant", "content": "a turn"},
        {"role": "user", "content": "feedback"},
    ]
    before = json.dumps(transcript)
    view = compact_view(
        transcript, opening_len=OPENING_LEN, continuation_system=CONT_SYSTEM
    )
    view[0]["content"] = "mutated"
    view[-1]["content"] = "mutated"
    assert json.dumps(transcript) == before


def test_compact_view_validates_opening_len():
    with pytest.raises(ValueError):
        compact_view([], opening_len=0, continuation_system=CONT_SYSTEM)


def test_history_policy_binds_the_parameters():
    policy = history_policy(OPENING_LEN, CONT_SYSTEM)
    opening = _opening()
    assert policy(opening) == opening
    view = policy(opening + [{"role": "assistant", "content": "turn"}])
    assert view[0]["content"] == CONT_SYSTEM


def test_opening_message_count_matches_the_runner_opening():
    from harness.runner.agent import _opening_messages
    from harness.runner.tools import tool_specs

    assert OPENING_MESSAGE_COUNT == len(
        _opening_messages(tool_specs(), "inferno", 1, 1, None)
    )


# --- continuation system prompt ---------------------------------------------------------------


def test_continuation_system_prompt_drops_planning_keeps_load_bearing_sections():
    cont = continuation_system_prompt(TOOL_SPECS, "unit")
    full = system_prompt(TOOL_SPECS, "unit")
    # Kept: role framing, Step 5, wire contract, full specs.
    for fragment in (
        "grammar analysis agent",
        "Step 5",
        "validate_candidate",
        "<tool_call>",
        "Available tools",
    ):
        assert fragment in cont
    # Dropped: the planning protocol and the few-shot demo.
    assert "Step 1" not in cont and "Step 4" not in cont
    assert "Waldeinsamkeit" not in cont
    assert len(cont.encode()) < len(full.encode())
    # The measured design size (STAGE3.md §2.A: 8,831 B) stays the reference.
    assert 8_000 < len(cont.encode()) < 9_500


def test_continuation_system_prompt_selects_step5_by_workflow():
    predicate = continuation_system_prompt(TOOL_SPECS, "predicate")
    assert "one at a time" in predicate
    assert "Never batch several predicates into one call" in predicate
    with pytest.raises(KeyError):
        continuation_system_prompt(TOOL_SPECS, "verse")


# --- adapter: fake Client ----------------------------------------------------------------------


class FakeClient:
    def __init__(self, model="", temperature=None, file=None, show_params=True, **kw):
        self.model = model
        self.temperature = temperature
        self.file = file
        self.show_params = show_params
        self.history = []
        self.calls = []

    def set_system_prompt(self, prompt):
        if self.history and self.history[0].get("role") == "system":
            self.history[0]["content"] = prompt
        else:
            self.history.insert(0, {"role": "system", "content": prompt})

    def __call__(self, prompt):
        reply = f"reply:{len(self.calls)}:{len(self.history)}"
        self.calls.append(prompt)
        self.history.append({"role": "user", "content": prompt})
        self.history.append({"role": "assistant", "content": reply})

        class _Response:
            text = reply

        return _Response()


@pytest.fixture()
def fake_llm(monkeypatch):
    created = []

    def factory(**kwargs):
        client = FakeClient(**kwargs)
        created.append(client)
        return client

    monkeypatch.setattr("llm7shi.Client", factory)
    return created


def _session_transcript():
    """A three-call session: read_unit -> validate(invalid) -> validate(valid)."""
    a1 = "reading.\n" + _block("read_unit", {"canticle": "inferno", "canto": 1, "line_start": 1})
    u1 = '<tool_result tool="read_unit" ok="true">\n{"lines": []}\n</tool_result>'
    a2 = "submitting.\n" + _block("validate_candidate", {"canticle": "inferno", "canto": 1, "line_start": 1, "candidate_rows": []})
    u2 = '<tool_result tool="validate_candidate" ok="false">\n{"error": "e"}\n</tool_result>'
    opening = _opening()
    t1 = list(opening)
    t2 = opening + [{"role": "assistant", "content": a1}, {"role": "user", "content": u1}]
    t3 = t2 + [{"role": "assistant", "content": a2}, {"role": "user", "content": u2}]
    return opening, t2, t3


def test_adapter_sends_the_wire_view_and_rebuilds_on_prefix_change(fake_llm):
    """Compaction end-to-end through the adapter: call 1 verbatim opening,
    calls 2+ continuation views, one rebuild per changed prefix, and the
    Client's history always equals the view it was built from."""
    policy = history_policy(OPENING_LEN, CONT_SYSTEM)
    generate = llm7shi_generate("ollama:m", history_policy=policy)
    opening, t2, t3 = _session_transcript()

    generate([dict(m) for m in opening])
    assert len(fake_llm) == 1
    first = fake_llm[0]
    # Call 1 mirrors the verbatim opening; the newest (task) was the prompt.
    assert first.history[0]["content"] == "system-prompt-with-steps"
    assert first.calls == ["<task>solve inferno 1 line 1</task>"]

    generate(t2)
    assert len(fake_llm) == 2  # opening -> continuation: prefix changed
    second = fake_llm[1]
    assert second.history[0]["content"] == CONT_SYSTEM
    assert [m["role"] for m in second.history] == [
        "system", "user", "assistant", "user", "assistant",
    ]
    assert second.history[1]["content"] == opening[-1]["content"]  # task
    assert second.history[2]["content"] == t2[OPENING_LEN]["content"]  # last assistant verbatim
    assert second.history[3]["content"] == t2[OPENING_LEN + 1]["content"]  # payload verbatim
    assert second.calls == [t2[-1]["content"]]

    generate(t3)
    # The previously-verbatim assistant turn became a digest: prefix changed
    # again -> rebuild (never a stale-history patch-up).
    assert len(fake_llm) == 3
    third = fake_llm[2]
    assert third.history[0]["content"] == CONT_SYSTEM
    assert third.history[2]["content"] != t2[OPENING_LEN]["content"]  # digested
    assert third.history[4]["content"] == t3[-2]["content"]  # last assistant verbatim
    assert third.calls == [t3[-1]["content"]]


def test_adapter_without_policy_keeps_one_client_per_session(fake_llm):
    generate = llm7shi_generate("ollama:m")
    opening, _t2, _t3 = _session_transcript()
    # The real loop records the generate return as the next assistant turn.
    r1 = generate(opening)
    t2 = opening + [
        {"role": "assistant", "content": r1},
        {"role": "user", "content": "<tool_result>…</tool_result>"},
    ]
    r2 = generate(t2)
    t3 = t2 + [
        {"role": "assistant", "content": r2},
        {"role": "user", "content": "<tool_result>…</tool_result>"},
    ]
    generate(t3)
    assert len(fake_llm) == 1  # prefix merely extended: no rebuild
    client = fake_llm[0]
    # system + demo(user/assistant/user) + task, then reply/feedback pairs.
    assert [m["role"] for m in client.history] == [
        "system", "user", "assistant", "user", "user",
        "assistant", "user", "assistant", "user", "assistant",
    ]
    # A repeated call at the same position finds the mirror ahead: rebuild.
    generate(t3)
    assert len(fake_llm) == 2


def test_adapter_reset_regenerates_client_but_not_pacing_state(fake_llm):
    policy = history_policy(OPENING_LEN, CONT_SYSTEM)
    clock_times = iter([0.0, 10.0, 100.0, 110.0, 135.0])
    sleeps = []

    generate = llm7shi_generate(
        "ollama:m",
        history_policy=policy,
        min_send_interval=35.0,
        clock=lambda: next(clock_times),
        sleeper=sleeps.append,
    )
    opening, t2, _t3 = _session_transcript()
    generate(opening)  # t=0: first send, no wait; last send start = 0
    assert sleeps == []
    generate(t2)  # t=10: due at 35 -> waits 25; send starts at post-sleep t=100
    assert sleeps == [25.0]
    generate.reset()
    generate(opening)  # new session, fresh Client — pacing remembered t=100
    assert sleeps == [25.0, 25.0]  # t=110, due 135 -> waits 25 again
    assert len(fake_llm) == 3  # reset regenerated the Client


def test_adapter_interval_pacing_prints_and_records(fake_llm, capsys):
    policy = history_policy(OPENING_LEN, CONT_SYSTEM)
    times = iter([0.0, 5.0, 100.0])
    sleeps = []
    generate = llm7shi_generate(
        "ollama:m",
        history_policy=policy,
        min_send_interval=35.0,
        clock=lambda: next(times),
        sleeper=sleeps.append,
    )
    opening, t2, _ = _session_transcript()
    generate(opening)
    generate(t2)
    assert sleeps == [30.0]
    err = capsys.readouterr().err
    assert "[pace] send interval: waiting 30.0s" in err


def test_adapter_interval_zero_disables_pacing(fake_llm, capsys):
    generate = llm7shi_generate("ollama:m", min_send_interval=0.0)
    opening, t2, _ = _session_transcript()
    generate(opening)
    generate(t2)
    err = capsys.readouterr().err
    assert "[pace]" not in err


def test_adapter_logs_uncompacted_and_paced_fields(fake_llm, tmp_path, capsys):
    policy = history_policy(OPENING_LEN, CONT_SYSTEM)
    times = iter([0.0, 0.5, 35.0])
    log = tmp_path / "requests.jsonl"
    with log.open("w", encoding="utf-8") as sink:
        generate = llm7shi_generate(
            "ollama:m",
            history_policy=policy,
            min_send_interval=35.0,
            clock=lambda: next(times),
            sleeper=lambda _s: None,
            request_log=sink,
        )
        opening, t2, _ = _session_transcript()
        generate(opening)
        generate(t2)  # paced 34.5s
    records = [
        json.loads(line)
        for line in log.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    requests = [r for r in records if r["record"] == "llm_request"]
    assert requests[0]["paced_seconds"] == 0.0
    assert requests[1]["paced_seconds"] == 34.5
    # context_bytes measures the physically sent view; uncompacted_bytes the
    # full transcript — call 2's view is the compacted one.
    assert requests[0]["context_bytes"] == requests[0]["uncompacted_bytes"]
    assert requests[1]["uncompacted_bytes"] == sum(
        len(m["content"].encode()) for m in t2
    )
    assert requests[1]["context_bytes"] < requests[1]["uncompacted_bytes"]
    # messages keeps transcript-position meaning (join key unchanged).
    assert [r["messages"] for r in requests] == [5, 7]


# --- end-to-end: the real loop, real corpus, compacted adapter ---------------------------------


def test_compacted_session_over_the_real_loop(monkeypatch):
    """The whole §2.A package over `run_unit` with the real toolkit (inferno 1
    served in R1), the real prompts, and the real adapter: call 1 sends the
    verbatim opening, calls 2+ send continuation views whose read_unit payload
    rides verbatim while older assistant turns digest — and the transcript
    (UnitResult.messages) is untouched by any of it."""
    from harness.runner.agent import run_unit
    from harness.runner.tools import GrammarToolkit, tool_specs
    from harness.toolcall import PromptXmlTransport

    rows = [
        {"line": 2, "token": 2, "role": "subj", "arg_line": 0, "arg_token": 0},
        {"line": 2, "token": 2, "role": "obl:per", "arg_line": 2, "arg_token": 5},
    ]
    script = iter(
        [
            _block("read_unit", {"canticle": "inferno", "canto": 1, "line_start": 1}),
            _block(
                "validate_candidate",
                {
                    "canticle": "inferno",
                    "canto": 1,
                    "line_start": 1,
                    "candidate_rows": rows,
                },
            ),
            "The unit is solved: two rows validated.",
        ]
    )
    created = []

    class ScriptedClient:
        def __init__(self, model="", **kw):
            self.history = []
            self.calls = []
            created.append(self)

        def set_system_prompt(self, prompt):
            self.history.insert(0, {"role": "system", "content": prompt})

        def __call__(self, prompt):
            reply = next(script)

            class _Response:
                text = reply

            self.calls.append(prompt)
            self.history.append({"role": "user", "content": prompt})
            self.history.append({"role": "assistant", "content": reply})
            return _Response()

    monkeypatch.setattr("llm7shi.Client", ScriptedClient)

    specs = tool_specs()
    from harness.runner.prompts import continuation_system_prompt as csp

    transport = PromptXmlTransport(
        generate=llm7shi_generate(
            "ollama:m",
            history_policy=history_policy(OPENING_MESSAGE_COUNT, csp(specs)),
        )
    )
    result = run_unit(
        transport=transport,
        toolkit=GrammarToolkit(),
        canticle="inferno",
        canto=1,
        line_start=1,
    )
    assert result.protocol_complete and result.turns == 3
    assert len(created) == 3  # opening, continuation, digested continuation

    # Call 1: verbatim opening; system == the full system prompt.
    first = created[0]
    assert first.history[0]["content"] == system_prompt(specs)

    # Call 2: continuation system (the measured 8,831 B prompt) + task, then
    # the read_unit payload verbatim in a user message.
    second = created[1]
    assert second.history[0]["content"] == csp(specs)
    assert len(second.history[0]["content"].encode()) == 8831
    payload = second.history[3]["content"]
    assert payload.startswith('<tool_result tool="read_unit" ok="true">')
    assert '"legend"' in payload and '"morphology"' in payload

    # Call 3: the read_unit dispatch turn digested — its JSON body is gone,
    # the payload user message and the validator feedback stay verbatim.
    third = created[2]
    digest = third.history[2]["content"]
    assert "[turn 1; called read_unit]" in digest
    assert '"canticle"' not in digest
    assert third.history[3]["content"] == second.history[3]["content"]
    assert third.history[5]["content"].startswith(
        '<tool_result tool="validate_candidate"'
    )
    # The loop's transcript keeps full fidelity regardless of the wire view.
    assert result.messages[0]["content"] == system_prompt(specs)
    assert '"candidate_rows"' in result.messages[OPENING_MESSAGE_COUNT + 2]["content"]


# --- agent_fallback wiring (construction only; the callable is operator-run) -------------------


def test_agent_fallback_builds_with_stage3_parameters(tmp_path):
    from harness.extractor.hybrid_engine import agent_fallback

    fallback = agent_fallback(
        compact=True,
        payload_tier="S1",
        min_send_interval=35.0,
        token_bucket=TokenBucket(tmp_path / "bucket.state"),
    )
    assert callable(fallback)
    # Default build: compaction on, R1, no pacing (the benchmark shape).
    assert callable(agent_fallback())
    with pytest.raises(TypeError):
        agent_fallback(token_bucket="not-a-bucket")


# --- token bucket ---------------------------------------------------------------------------


def test_bucket_debits_and_refills_over_injected_clock(tmp_path):
    path = tmp_path / "bucket.state"
    now = {"t": 1000.0}

    def clock():
        return now["t"]

    bucket = TokenBucket(path, rate_per_min=600.0, depth=100.0, clock=clock)
    assert bucket.acquire(100.0) == 0.0  # full depth funds immediately
    state = json.loads(path.read_text())
    assert state["tokens"] == 0.0
    # Starved: 25 tokens need 2.5 min at 600/min (plus the retry epsilon).
    sleeps = []

    def sleeper(seconds):
        sleeps.append(seconds)
        now["t"] += seconds  # time passes while sleeping

    bucket.sleeper = sleeper
    waited = bucket.acquire(25.0)
    assert waited > 0 and sleeps  # slept until funded
    state = json.loads(path.read_text())
    # Refill overshoots by the sleep epsilon; the debit left the remainder
    # of exactly that overshoot.
    assert 0.0 <= state["tokens"] < 1.0


def test_bucket_shares_state_across_processes(tmp_path):
    """Sequential 'processes' (two instances, one file) see each other's
    debits and the shared refill clock — the three-parallel-launch contract."""
    path = tmp_path / "bucket.state"
    now = {"t": 0.0}

    def clock():
        return now["t"]

    a = TokenBucket(path, rate_per_min=600.0, depth=100.0, clock=clock)
    b = TokenBucket(path, rate_per_min=600.0, depth=100.0, clock=clock)
    assert a.acquire(100.0) == 0.0  # A drains the bucket
    now["t"] += 30.0  # 30 s -> +300 tokens, capped at depth
    assert b.acquire(100.0) == 0.0  # B refills and drains again
    state = json.loads(path.read_text())
    assert state["tokens"] == 0.0
    assert state["t"] == 30.0


def test_bucket_recreates_corrupt_state_at_full_depth(tmp_path):
    path = tmp_path / "bucket.state"
    path.write_text("not json at all{", encoding="utf-8")
    bucket = TokenBucket(path, rate_per_min=600.0, depth=50.0, clock=lambda: 0.0)
    assert bucket.acquire(50.0) == 0.0
    path.write_text('{"t": "bogus", "tokens": []}', encoding="utf-8")
    assert TokenBucket(path, rate_per_min=600.0, depth=50.0, clock=lambda: 0.0).acquire(50.0) == 0.0


def test_bucket_rejects_nonpositive_parameters(tmp_path):
    with pytest.raises(ValueError):
        TokenBucket(tmp_path / "b", rate_per_min=0, depth=10)
    with pytest.raises(ValueError):
        TokenBucket(tmp_path / "b", rate_per_min=10, depth=0)


def test_bucket_launch_defaults_match_the_design(tmp_path):
    bucket = TokenBucket(tmp_path / "b")
    assert bucket.rate_per_min == DEFAULT_BUCKET_RATE_TOKENS_PER_MIN == 12000.0
    assert bucket.depth == DEFAULT_BUCKET_DEPTH_TOKENS == 6500.0
    assert BYTES_PER_TOKEN == 3.5


def test_adapter_bucket_wait_logs_paced_seconds(fake_llm, tmp_path, capsys):
    path = tmp_path / "bucket.state"
    now = {"t": 1000.0}

    def clock():
        return now["t"]

    def sleeper(seconds):
        now["t"] += seconds

    # Depth covers the opening (the launch invariant: depth >= max single
    # call); the rate starves the second send.
    bucket = TokenBucket(path, rate_per_min=60.0, depth=100.0, clock=clock, sleeper=sleeper)
    policy = history_policy(OPENING_LEN, CONT_SYSTEM)
    log = tmp_path / "requests.jsonl"
    with log.open("w", encoding="utf-8") as sink:
        generate = llm7shi_generate(
            "ollama:m", history_policy=policy, token_bucket=bucket, request_log=sink
        )
        opening, t2, _ = _session_transcript()
        generate(opening)
        generate(t2)  # drains what refill gave: must wait for the rest
    records = [
        json.loads(line)
        for line in log.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    requests = [r for r in records if r["record"] == "llm_request"]
    opening_tokens = requests[0]["context_bytes"] / BYTES_PER_TOKEN
    assert opening_tokens < 100.0  # funded from full depth: no wait
    assert requests[0]["paced_seconds"] == 0.0
    view_tokens = requests[1]["context_bytes"] / BYTES_PER_TOKEN
    assert view_tokens > 100.0 - opening_tokens  # second send exceeds the remainder
    assert requests[1]["paced_seconds"] > 0.0
    err = capsys.readouterr().err
    assert "[pace] token bucket: waited" in err


def test_bucket_over_depth_debit_drains_and_proceeds(tmp_path):
    """A debit larger than depth can never be funded: it drains and proceeds
    (no deadlock) — misconfigured depth degrades to an unpaced burst."""
    path = tmp_path / "bucket.state"
    bucket = TokenBucket(
        path, rate_per_min=60.0, depth=10.0, clock=lambda: 0.0, sleeper=lambda s: None
    )
    assert bucket.acquire(10_000.0) == 0.0
    state = json.loads(path.read_text())
    assert state["tokens"] == 0.0
