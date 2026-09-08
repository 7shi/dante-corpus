"""Deterministic tests for Stage 9's fixed-context execution loop.

No model calls anywhere: `generate` is a stub list of canned answers, and every
run reads the real frozen layers of inferno 1 through the masked toolkit. The
tests are organized around the four properties `../stages/09.md` §2 and
§2.1 argue the design *has*, rather than around the functions:

1. the context is fixed — every request is `[system, user]`, with no transcript
   and no growth in the iteration count;
2. refusal is the identity — a step whose answer fails the runtime gate leaves
   the rows exactly as they were, and the failure comes back in the verdict;
3. the gate is the runtime's — validation happens on every answer, without the
   model electing it;
4. the stopping rule is a fixed point, not a count.

The observation half of $O$ is tested against the tree directly (`observe.py`),
including the adversarial case: it must not read gold to say what it says.
"""

import json

import pytest

from dante_corpus import dep as dep_layer
from dante_corpus.skel import io as skel_io
from dante_corpus.skel.models import SkelRow

from harness.extractor import fixedcontext as fx
from harness.extractor import observe as ob
from harness.runner import prompts
from harness.runner.tools import GrammarToolkit


# --- helpers -----------------------------------------------------------------------------


class _Stub:
    """A `generate` stub: canned answers, one per call, recording every request."""

    def __init__(self, answers):
        self.answers = list(answers)
        self.calls: list[list[dict]] = []
        self.resets = 0

    def __call__(self, messages):
        self.calls.append([dict(m) for m in messages])
        if not self.answers:
            return "no more answers"
        return self.answers.pop(0)

    def reset(self):
        self.resets += 1


def _rows_block(rows):
    body = "\n".join(
        f"{r[0]}\t{r[1]}\t\t{r[2]}\t{r[3]}\t{r[4]}" for r in rows
    )
    return f"Prose first.\n<rows>\n{body}\n</rows>"


def _toolkit():
    return GrammarToolkit()


def _run(answers, **kwargs):
    stub = _Stub(answers)
    result = fx.run_unit_fixed(
        toolkit=_toolkit(),
        generate=stub,
        canticle="inferno",
        canto=1,
        line_start=1,
        **kwargs,
    )
    return result, stub


# --- $\Sigma$ in and out -----------------------------------------------------------------


def test_rows_from_skel_round_trips_the_artifact_rows():
    rows = {2: [SkelRow(2, 2, "ritrovai", "subj", 0, 0)]}
    assert fx.rows_from_skel(rows) == [
        {
            "line": 2,
            "token": 2,
            "word": "ritrovai",
            "role": "subj",
            "arg_line": 0,
            "arg_token": 0,
        }
    ]
    assert fx.rows_from_skel(None) == []


# --- $O$: the frozen-layer observation ---------------------------------------------------


def _dep():
    return dep_layer.load_dep("inferno", 1)


def test_observation_flags_a_bare_obl_with_a_case_child():
    # inferno 1:2 — `per` (2.3) is the `case` child of `selva` (2.5), which hangs
    # on the predicate `ritrovai` (2.2) as an `obl`.
    rows = [
        {"line": 2, "token": 2, "role": "obl", "arg_line": 2, "arg_token": 5},
    ]
    found = ob.observe_rows(rows, _dep(), line_start=1, line_end=3)
    kinds = [o.kind for o in found]
    assert "unqualified_oblique" in kinds
    notice = next(o for o in found if o.kind == "unqualified_oblique").text
    assert "case" in notice and "'per'" in notice
    # …and never the derived label itself.
    assert "obl:per" not in notice


def test_observation_is_silent_once_the_oblique_is_qualified():
    rows = [
        {"line": 2, "token": 2, "role": "obl:per", "arg_line": 2, "arg_token": 5},
    ]
    found = ob.observe_rows(rows, _dep(), line_start=1, line_end=3)
    assert "unqualified_oblique" not in [o.kind for o in found]


def test_observation_flags_an_uncited_layer4_argument_child():
    # `ritrovai` (2.2) is registered with no arguments at all; Layer 4 hangs
    # `mezzo` (1.2) and `selva` (2.5) on it, both under `obl`. The `expl` clitic
    # and the `advcl` clause are not argument relations, so neither is named.
    rows = [{"line": 2, "token": 2, "role": "", "arg_line": 0, "arg_token": 0}]
    found = ob.observe_rows(rows, _dep(), line_start=1, line_end=3)
    assert [o.kind for o in found] == ["uncited_l4_argument"] * 2
    assert {o.argument for o in found} == {(1, 2), (2, 5)}
    assert {o.predicate for o in found} == {(2, 2)}


def test_observation_says_nothing_about_an_unregistered_predicate():
    # No rows at all: an empty record raises nothing about itself, because the
    # frame it would be missing arguments from was never written.
    assert ob.observe_rows([], _dep(), line_start=1, line_end=3) == []


def test_observation_never_opens_gold(monkeypatch):
    def boom(*a, **kw):
        raise AssertionError("the observation must not read gold skel/")

    monkeypatch.setattr(skel_io, "load_skel", boom)
    rows = [{"line": 2, "token": 2, "role": "obl", "arg_line": 2, "arg_token": 5}]
    assert ob.observe_rows(rows, _dep(), line_start=1, line_end=3)


# --- the loop ----------------------------------------------------------------------------


SETTLED_ROWS = [
    (2, 2, "subj", 0, 0),
    (2, 2, "obl:in", 1, 2),
    (2, 2, "obl:per", 2, 5),
]


def test_a_clean_answer_settles_in_one_call():
    result, stub = _run([_rows_block(SETTLED_ROWS)])
    assert result.stop_reason == "settled"
    assert len(result.iterations) == 1
    assert result.iterations[0].accepted
    assert result.final_submission_valid is True
    assert len(result.rows) == 3
    assert len(stub.calls) == 1
    assert result.observations == []


def test_the_context_is_fixed_across_iterations():
    # First answer: schema-valid but leaves an observation open, so the loop
    # asks again; second: the same rows, which stops it.
    open_rows = _rows_block([(2, 2, "obl", 2, 5)])
    result, stub = _run([open_rows, open_rows])
    assert len(stub.calls) == 2
    for messages in stub.calls:
        assert [m["role"] for m in messages] == ["system", "user"]
    # $P$ never varies within a run (Standing Invariant §6 in the reader position).
    assert stub.calls[0][0]["content"] == stub.calls[1][0]["content"]
    # No transcript crosses the boundary: the second request carries neither the
    # first answer nor the first verdict's prose beyond what the rows imply.
    assert "Prose first." not in stub.calls[1][1]["content"]
    # And the adapter is reset before every send, so no history accumulates.
    assert stub.resets == 2


def test_the_verdict_carries_the_observation_and_not_the_answer():
    result, stub = _run([_rows_block([(2, 2, "obl", 2, 5)])] * 2)
    second = stub.calls[1][1]["content"]
    assert "<verdict>" in second
    assert "Layer-4 `case` child" in second
    assert "obl:per" not in second  # the derived label never crosses over
    # $\Sigma$ is in the request as the artifact's own table.
    assert "<rows_on_record>" in second
    assert "2\t2\t\tobl\t2\t5" in second


def test_refusal_is_the_identity_and_the_errors_come_back():
    # A row citing its own predicate is hard-invalid (`validate_candidate` check
    # 5a), so the answer is refused and nothing is recorded.
    bad = _rows_block([(2, 2, "obj", 2, 2)])
    good = _rows_block(SETTLED_ROWS)
    result, stub = _run([bad, good])
    first, second = result.iterations[0], result.iterations[1]
    assert first.reason == "schema_invalid" and not first.accepted
    assert first.rows_in == 0  # $\Sigma$ was empty and stayed empty
    assert second.accepted
    assert "cites its own predicate" in stub.calls[1][1]["content"]
    assert "still stand" in stub.calls[1][1]["content"]
    assert len(result.rows) == 3


def test_a_refused_answer_leaves_recorded_rows_untouched():
    sigma0 = fx.rows_from_skel(
        {2: [SkelRow(2, 2, "ritrovai", "subj", 0, 0)]}
    )
    result, _ = _run([_rows_block([(2, 2, "obj", 2, 2)])] * 4, rows=sigma0)
    assert result.rows == sigma0  # every step refused: the loop is `id`
    assert result.final_submission_valid is False
    assert all(not r.accepted for r in result.iterations)


def test_an_unreadable_answer_is_a_refusal_too():
    result, stub = _run(["I would rather not.", _rows_block([(2, 2, "subj", 0, 0)])])
    assert result.iterations[0].reason == "unparsed"
    assert result.rows  # the second answer landed
    assert "no readable <rows> block" in stub.calls[1][1]["content"]


def test_the_loop_stops_at_a_fixed_point_not_at_a_count():
    # The model is shown an open observation and returns the same rows: iterating
    # again would ask the same question, so the loop stops.
    same = _rows_block([(2, 2, "obl", 2, 5)])
    result, stub = _run([same] * 4)
    assert result.stop_reason == "fixed_point"
    assert len(stub.calls) == 2
    assert result.observations  # it stopped *with* the point open, and says so


def test_the_iteration_budget_is_a_cap():
    answers = [
        _rows_block([(2, 2, "obl", 2, 5)]),
        _rows_block([(2, 2, "obl", 2, 5), (2, 2, "subj", 0, 0)]),
        _rows_block([(2, 2, "obl", 2, 5)]),
    ]
    result, stub = _run(answers, max_iterations=2)
    assert len(stub.calls) == 2
    assert result.stop_reason == "budget"


def test_every_answer_is_gated_by_the_runtime():
    result, _ = _run([_rows_block([(2, 2, "obj", 2, 2)])] * 3)
    # One gate verdict per answer, none of them elected by the model.
    assert len(result.validations) == 3
    assert all(v["result"]["valid"] is False for v in result.validations)
    # Three refused answers and an empty record: the budget ran out with nothing
    # ever accepted, which the record names as such rather than as a stop.
    assert result.to_dict()["stop_reason"] == "unanswered"


def test_the_record_is_json_serializable():
    result, _ = _run([_rows_block([(2, 2, "subj", 0, 0)])])
    json.dumps(result.to_dict())


# --- the seam into the pipeline ------------------------------------------------------------


def test_the_pipeline_consumes_the_loop_like_any_fallback():
    """`reconstruct_canto` drives it unchanged, and the record carries the loop."""
    from harness.extractor import reconstruct as rc

    def fallback(*, canticle, canto, line_start, line_end):
        return fx.run_unit_fixed(
            toolkit=_toolkit(),
            generate=_Stub([_rows_block(SETTLED_ROWS)]),
            canticle=canticle,
            canto=canto,
            line_start=line_start,
            line_end=line_end,
        )

    recon = rc.reconstruct_canto(
        "inferno", 1, fallback=fallback, progress_stream=None
    )
    first = recon.outcomes[0]
    assert first.fallback_ran
    record = first.to_dict()
    assert record["fixed"]["stop_reason"] in {"settled", "fixed_point", "budget"}
    assert record["fixed"]["iterations"]
    assert record["final_submission_valid"] is True
    json.dumps(record)


# --- $P$ ---------------------------------------------------------------------------------


def test_the_fixed_prompt_is_the_skill_and_carries_no_tools():
    text = prompts.fixed_system_prompt()
    for absent in ("<tool_call>", "read_unit", "validate_candidate", "search_corpus"):
        assert absent not in text
    assert "<rows>" in text  # the answer contract
    # Every byte comes from the skill directory, so the digest covers all of $P$.
    for piece in (
        prompts.FIXED_SKILL.body,
        prompts.FIXED_SKILL.resource("protocol.md"),
        prompts.FIXED_SKILL.resource("answer.md"),
    ):
        assert piece in text
    assert prompts.fixed_skill_digest() == prompts.FIXED_SKILL.digest()
