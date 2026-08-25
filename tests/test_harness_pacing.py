"""Deterministic tests for the Stage-3 adapter: pacing and Client sync.

Covers what survived record S3.7 (transcript compaction and the continuation
prompt removed): the adapter sends the transcript verbatim and keeps one
`llm7shi.Client` in sync with it by content fingerprint, the min-send interval
(injected clock), and the shared token bucket (tmp file, sequential
"processes"). No test touches a model: `llm7shi.Client` is faked.
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
from harness.runner.prompts import system_prompt


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


def test_opening_message_count_matches_the_runner_opening():
    from harness.runner.prompts import few_shot_messages

    assert OPENING_MESSAGE_COUNT == 1 + len(few_shot_messages()) + 1 == OPENING_LEN


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


def test_adapter_keeps_one_client_per_session(fake_llm):
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
    clock_times = iter([0.0, 10.0, 100.0, 110.0, 135.0])
    sleeps = []

    generate = llm7shi_generate(
        "ollama:m",
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
    times = iter([0.0, 5.0, 100.0])
    sleeps = []
    generate = llm7shi_generate(
        "ollama:m",
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


def test_adapter_logs_context_and_paced_fields(fake_llm, tmp_path, capsys):
    times = iter([0.0, 0.5, 35.0])
    log = tmp_path / "requests.jsonl"
    with log.open("w", encoding="utf-8") as sink:
        generate = llm7shi_generate(
            "ollama:m",
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
    # context_bytes measures what is physically sent = the whole transcript
    # (record S3.7: no compaction layer any more).
    assert requests[1]["context_bytes"] == sum(
        len(m["content"].encode()) for m in t2
    )
    assert "uncompacted_bytes" not in requests[0]
    # messages keeps transcript-position meaning (join key unchanged).
    assert [r["messages"] for r in requests] == [5, 7]


# --- end-to-end: the real loop, real corpus, compacted adapter ---------------------------------


def test_verbatim_session_over_the_real_loop(monkeypatch):
    """`run_unit` with the real toolkit (inferno 1 served in R1), the real
    prompts, and the real adapter: every call sends the transcript verbatim
    (record S3.7), one Client serves the whole session because the prefix
    only ever extends, and the loop's transcript is what rides the wire."""
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
    transport = PromptXmlTransport(
        generate=llm7shi_generate("ollama:m")
    )
    result = run_unit(
        transport=transport,
        toolkit=GrammarToolkit(),
        canticle="inferno",
        canto=1,
        line_start=1,
    )
    assert result.protocol_complete and result.turns == 3
    # The transcript only ever extends, so one Client serves the session.
    assert len(created) == 1
    client = created[0]
    assert client.history[0]["content"] == system_prompt(specs)
    sent = "".join(m["content"] for m in client.history)
    # The read_unit payload and validator feedback ride verbatim (R1 legend)
    # and so does every assistant turn: the session sees its own history.
    assert '"legend"' in sent and '"morphology"' in sent
    assert '"obl:per"' in sent  # inside a2, the newest submission
    a1 = _block("read_unit", {"canticle": "inferno", "canto": 1, "line_start": 1})
    a2 = _block(
        "validate_candidate",
        {
            "canticle": "inferno",
            "canto": 1,
            "line_start": 1,
            "candidate_rows": rows,
        },
    )
    assert a1 in sent and a2 in sent
    # The loop's transcript is what the wire carries.
    assert result.messages[0]["content"] == system_prompt(specs)
    assert '"candidate_rows"' in result.messages[OPENING_MESSAGE_COUNT + 2]["content"]


# --- agent_fallback wiring (construction only; the callable is operator-run) -------------------


def test_agent_fallback_builds_with_stage3_parameters(tmp_path):
    from harness.extractor.hybrid_engine import agent_fallback

    fallback = agent_fallback(
        payload_tier="S1",
        min_send_interval=35.0,
        token_bucket=TokenBucket(tmp_path / "bucket.state"),
    )
    assert callable(fallback)
    # Default build: R1, no pacing (the benchmark shape).
    assert callable(agent_fallback())
    with pytest.raises(TypeError):
        agent_fallback(token_bucket="not-a-bucket")


def test_agent_fallback_shares_one_transport_across_units(monkeypatch):
    """One transport/generate pair serves all units: pacing state lives in
    the generate closure and session boundaries are sends too, so a fresh
    closure per `_run` call would let every session-opening send skip the
    min-send interval (the wiring bug behind confirmation-run #1's 76%
    rolling-60 window — fixed by hoisting construction into the factory)."""
    import harness.runner.agent as agent_mod

    from harness.extractor.hybrid_engine import agent_fallback

    seen = []

    def spy_run_unit(**kwargs):
        seen.append(kwargs["transport"])
        return "unit-result"

    monkeypatch.setattr(agent_mod, "run_unit", spy_run_unit)
    fallback = agent_fallback()
    assert fallback(canticle="inferno", canto=1, line_start=1, line_end=3) == "unit-result"
    assert fallback(canticle="inferno", canto=1, line_start=4, line_end=6) == "unit-result"
    assert len(seen) == 2
    assert seen[0] is seen[1]
    # The shared generate exposes reset() so run_unit's per-session reset
    # clears session state while pacing state survives it.
    assert callable(getattr(seen[0].generate, "reset", None))


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
    log = tmp_path / "requests.jsonl"
    with log.open("w", encoding="utf-8") as sink:
        generate = llm7shi_generate(
            "ollama:m", token_bucket=bucket, request_log=sink
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
