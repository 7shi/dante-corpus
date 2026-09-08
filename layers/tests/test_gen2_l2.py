"""Tests for generation 2's Layer 2, step 1 — the split (`layers/gen2/l2.py`).

Run on demand — `uv run pytest layers/tests` — the same way `harness/tests` does; `layers/`
is not yet part of the maintained root suite (`pyproject.toml` `testpaths`).

No test touches a model or a network (`ARCHITECTURE.md` §8): the model is a scripted stub
whose raw answer strings go through the real parser, so the wire format under test is the
one the live run uses.
"""

import pytest

from dante_corpus.morph import load_morph
from layers.gen2 import l1, l2


# --- The stub model --------------------------------------------------------------------------

# The two splits *Inf* 1:1-9 actually contains; every other token is one word.
SPLITS = {"nel": "in+il", "del": "di+il"}


def answer_for(user_message, table=SPLITS):
    """A correct `<split>` block for whatever tokens the message listed: splits only.

    Keys are prefixed with preceding tokens where the bare word would name two places,
    which is the contract the real prompt asks for.
    """
    block = user_message.split("<tokens>\n", 1)[1].split("\n</tokens>", 1)[0]
    tokens = block.split()
    rows = []
    for index, token in enumerate(tokens):
        value = table.get(token.casefold())
        if not value:
            continue
        key = token
        span = 1
        while sum(
            1
            for start in range(len(tokens) - span + 1)
            if [t.casefold() for t in tokens[start : start + span]]
            == [k.casefold() for k in key.split()]
        ) > 1:
            span += 1
            key = " ".join(tokens[index - span + 1 : index + 1])
        rows.append(f"{key}:{value}")
    return "<split>\n" + "\n".join(rows) + "\n</split>"


class StubGenerate:
    """A scripted `generate(messages) -> str`, counting calls and resets.

    `script` maps a chunk's line-number tuple to a list of raw answers consumed in order;
    anything unscripted gets the correct answer for the tokens it was asked about.
    """

    def __init__(self, script=None, table=SPLITS):
        self.script = {k: list(v) for k, v in (script or {}).items()}
        self.table = table
        self.calls = []
        self.resets = 0

    def __call__(self, messages):
        assert [m["role"] for m in messages] == ["system", "user"]
        user = messages[1]["content"]
        self.calls.append(user)
        lines = user.split("<lines>\n", 1)[1].split("\n</lines>", 1)[0]
        key = tuple(int(row.split(" ", 1)[0]) for row in lines.splitlines() if row)
        queue = self.script.get(key)
        if queue:
            return queue.pop(0) if len(queue) > 1 else queue[0]
        return answer_for(user, self.table)

    def reset(self):
        self.resets += 1


SYSTEM = "you are the split step"


def inf1(start=1, end=9):
    return [line for line in l1.l1_canto("inferno", 1) if start <= line.no <= end]


# --- Chunking: old Layer 2's unit of work ----------------------------------------------------


def test_chunks_group_consecutive_lines_like_morph_py():
    got = l2.chunks(inf1(), 3)
    assert [[line.no for line in chunk] for chunk in got] == [[1, 2, 3], [4, 5, 6], [7, 8, 9]]


def test_the_last_chunk_is_short_rather_than_padded():
    got = l2.chunks(inf1(1, 4), 3)
    assert [[line.no for line in chunk] for chunk in got] == [[1, 2, 3], [4]]


def test_the_default_chunk_is_old_layer_2s_three_lines():
    assert l2.CHUNK_SIZE == 3


def test_asked_tokens_are_the_chunks_splittable_tokens_in_l1_order():
    asked = l2.asked_tokens(inf1(1, 2))
    assert [t.text for t in asked] == [
        "Nel", "mezzo", "del", "cammin", "di", "nostra", "vita",
        "mi", "ritrovai", "per", "una", "selva", "oscura",
    ]
    assert [(t.line, t.l1_index) for t in asked][:3] == [(1, 0), (1, 1), (1, 2)]
    assert "," not in [t.text for t in asked]  # punctuation is never asked about


# --- Which tokens are asked about ------------------------------------------------------------


def test_punctuation_is_not_splittable():
    assert not l2.is_splittable(",")
    assert not l2.is_splittable("!")
    assert not l2.is_splittable("«")


def test_elided_and_apocopated_forms_are_splittable_questions():
    # They pass through unchanged, but that is the model's answer, not a code-side rule.
    assert l2.is_splittable("ch'")
    assert l2.is_splittable("i'")
    assert l2.is_splittable("cammin")


def test_distinct_wordforms_dedupes_case_folded_in_first_appearance_order():
    forms = l2.distinct_wordforms(inf1(1, 6))
    assert forms[:7] == ["Nel", "mezzo", "del", "cammin", "di", "nostra", "vita"]
    assert [f for f in forms if f.casefold() == "nel"] == ["Nel"]
    assert "," not in forms and "!" not in forms


# --- apply_splits: the pure half -------------------------------------------------------------


def test_apply_splits_reproduces_the_l2_md_worked_example_for_inf_1_1():
    line = l1.l1_line(1, "Nel mezzo del cammin di nostra vita")
    out = l2.apply_splits(line, {(1, 0): ["in", "il"], (1, 2): ["di", "il"]})
    assert [(e.l1_index, e.text) for e in out.entries] == [
        (0, "in"), (0, "il"), (1, "mezzo"), (2, "di"), (2, "il"),
        (3, "cammin"), (4, "di"), (5, "nostra"), (6, "vita"),
    ]


def test_apply_splits_is_the_identity_for_a_line_with_no_composite_token():
    line = l1.l1_line(5, "esta selva selvaggia e aspra e forte")
    out = l2.apply_splits(line, {})
    assert [(e.l1_index, e.text) for e in out.entries] == [
        (0, "esta"), (1, "selva"), (2, "selvaggia"), (3, "e"),
        (4, "aspra"), (5, "e"), (6, "forte"),
    ]


def test_apply_splits_keeps_casing_apostrophes_and_punctuation_of_a_pass_through():
    line = l1.l1_line(8, "ma per trattar del ben ch'i' vi trovai,")
    out = l2.apply_splits(line, {(8, 3): ["di", "il"]})
    assert [e.text for e in out.entries] == [
        "ma", "per", "trattar", "di", "il", "ben", "ch'", "i'", "vi", "trovai", ",",
    ]
    # `ch'` and `i'` are elisions — step 3's business, untouched here.
    assert ("ch'", "i'") == tuple(e.text for e in out.entries if e.text.endswith("'"))


def test_splits_are_per_occurrence_so_one_wordform_can_go_two_ways():
    # The whole reason splits are keyed by position rather than by wordform.
    line = l1.l1_line(1, "nel mezzo nel")
    out = l2.apply_splits(line, {(1, 0): ["in", "il"], (1, 2): ["ne", "lo"]})
    assert [e.text for e in out.entries] == ["in", "il", "mezzo", "ne", "lo"]


def test_a_single_part_entry_is_a_pass_through_not_a_rewrite():
    line = l1.l1_line(1, "cammin")
    out = l2.apply_splits(line, {(1, 0): ["cammino"]})
    assert [e.text for e in out.entries] == ["cammin"]


# --- The question ----------------------------------------------------------------------------


def test_the_ask_shows_the_lines_for_context_and_the_tokens_for_the_answer():
    message = l2.ask_message(inf1(1, 2))
    assert "1 Nel mezzo del cammin di nostra vita" in message
    assert "<tokens>\nNel mezzo del cammin" in message
    assert "an empty block means you found none" in message


def test_a_refused_ask_carries_the_reason_and_asks_for_the_whole_block_again():
    message = l2.ask_message(inf1(1, 1), refusal="'del' names 2 places")
    assert "'del' names 2 places" in message
    assert "whole block again" in message


# --- Locating a key --------------------------------------------------------------------------


def tokens_of(*texts, line=1):
    return [l2.Asked(line=line, l1_index=i, text=t) for i, t in enumerate(texts)]


def test_a_unique_bare_word_locates_itself():
    assert l2.locate_key("del", tokens_of("Nel", "mezzo", "del")) == (2, "")


def test_a_key_is_matched_case_insensitively():
    assert l2.locate_key("nel", tokens_of("Nel", "mezzo")) == (0, "")


def test_a_word_naming_two_places_is_refused_with_both_lines_named():
    tokens = [
        l2.Asked(line=1, l1_index=0, text="nel"),
        l2.Asked(line=3, l1_index=1, text="nel"),
    ]
    index, error = l2.locate_key("nel", tokens)
    assert index == -1
    assert "names 2 places" in error and "line 1" in error and "line 3" in error


def test_preceding_words_disambiguate_and_the_last_word_is_the_target():
    tokens = [
        l2.Asked(line=1, l1_index=0, text="in"),
        l2.Asked(line=1, l1_index=1, text="nel"),
        l2.Asked(line=3, l1_index=0, text="che"),
        l2.Asked(line=3, l1_index=1, text="nel"),
    ]
    assert l2.locate_key("in nel", tokens) == (1, "")
    assert l2.locate_key("che nel", tokens) == (3, "")


def test_a_key_that_is_not_a_run_of_tokens_is_refused():
    index, error = l2.locate_key("nowhere", tokens_of("Nel", "mezzo"))
    assert index == -1 and "not a run of consecutive tokens" in error


# --- The gate --------------------------------------------------------------------------------


def test_the_answer_names_only_the_tokens_that_split():
    tokens = tokens_of("Nel", "mezzo", "del", "cammin")
    text = "prose first\n\n<split>\nNel:in+il\ndel:di+il\n</split>"
    assert l2.parse_split_answer(text, tokens=tokens) == (
        {0: ["in", "il"], 2: ["di", "il"]}, ""
    )


def test_an_empty_block_means_nothing_in_the_passage_splits():
    tokens = tokens_of("esta", "selva", "selvaggia")
    assert l2.parse_split_answer("<split>\n</split>", tokens=tokens) == ({}, "")


def test_a_none_placeholder_reads_as_an_empty_block():
    tokens = tokens_of("esta", "selva")
    assert l2.parse_split_answer("<split>\nnone\n</split>", tokens=tokens) == ({}, "")


def test_the_gate_accepts_a_three_way_split():
    tokens = tokens_of("dirtelo")
    assert l2.parse_split_answer("<split>\ndirtelo:dir+te+lo\n</split>", tokens=tokens) == (
        {0: ["dir", "te", "lo"]}, ""
    )


def test_a_prefixed_key_resolves_to_its_last_token():
    tokens = [
        l2.Asked(line=8, l1_index=2, text="trattar"),
        l2.Asked(line=8, l1_index=3, text="del"),
        l2.Asked(line=1, l1_index=2, text="del"),
    ]
    assert l2.parse_split_answer("<split>\ntrattar del:di+il\n</split>", tokens=tokens) == (
        {1: ["di", "il"]}, ""
    )


def test_a_row_restating_a_token_unchanged_is_refused():
    tokens = tokens_of("mezzo")
    splits, error = l2.parse_split_answer("<split>\nmezzo:mezzo\n</split>", tokens=tokens)
    assert splits == {} and "says nothing" in error


def test_the_same_token_named_twice_is_refused():
    tokens = tokens_of("Nel")
    splits, error = l2.parse_split_answer("<split>\nNel:in+il\nNel:ne+lo\n</split>",
                                          tokens=tokens)
    assert splits == {} and "a second time" in error


@pytest.mark.parametrize(
    "text",
    [
        "no block at all",
        "<split>\nNel:in+il\n</split><split>\nNel:ne+lo\n</split>",
        "<split>\nin+il\n</split>",
        "<split>\nNel:\n</split>",
        "<split>\nNel:in+\n</split>",
        "<split>\nNel:in il\n</split>",
        "<split>\nNel:a+b+c+d\n</split>",
        "<split>\nnowhere:a+b\n</split>",
    ],
)
def test_parse_split_answer_refuses_every_malformed_shape(text):
    splits, error = l2.parse_split_answer(text, tokens=tokens_of("Nel"))
    assert splits == {} and error


# --- The bounded step ------------------------------------------------------------------------


def test_split_chunk_settles_on_the_first_good_answer():
    stub = StubGenerate()
    result = l2.split_chunk(inf1(1, 3), generate=stub, system_prompt=SYSTEM)
    assert result.stop_reason == "settled" and result.accepted
    assert result.lines == [1, 2, 3]
    assert result.splits == 2  # Nel and del
    assert result.positions() == {(1, 0): ["in", "il"], (1, 2): ["di", "il"]}
    assert len(stub.calls) == 1 and stub.resets == 1


def test_a_chunk_where_nothing_splits_is_settled_not_failed():
    stub = StubGenerate()
    result = l2.split_chunk(inf1(5, 5), generate=stub, system_prompt=SYSTEM)
    assert result.accepted and result.splits == 0
    assert result.stop_reason == "settled"


def test_a_refused_answer_records_nothing_and_the_budget_is_a_cap():
    stub = StubGenerate({(1, 2, 3): ["nothing parsable"]})
    result = l2.split_chunk(inf1(1, 3), generate=stub, system_prompt=SYSTEM,
                            max_iterations=1)
    assert not result.accepted and result.stop_reason == "budget"
    assert result.attempts[0].error.startswith("no <split> block")
    assert len(stub.calls) == 1


def test_the_refusal_reason_is_fed_back_verbatim_on_the_retry():
    class OneBadThenGood(StubGenerate):
        def __call__(self, messages):
            self.calls.append(messages[1]["content"])
            if len(self.calls) == 1:
                return "nothing parsable"
            return answer_for(messages[1]["content"])

    stub = OneBadThenGood()
    result = l2.split_chunk(inf1(1, 1), generate=stub, system_prompt=SYSTEM)
    assert result.accepted
    assert "no <split> block" in stub.calls[1]
    assert stub.resets == 2  # no history crosses a retry either


def test_a_chunk_of_pure_punctuation_costs_no_request():
    stub = StubGenerate()
    result = l2.split_chunk((l1.l1_line(1, ", ."),), generate=stub, system_prompt=SYSTEM)
    assert result.accepted and result.stop_reason == "settled"
    assert result.tokens == [] and stub.calls == []


# --- build_splits ----------------------------------------------------------------------------


def test_build_splits_asks_once_per_chunk_not_once_per_wordform():
    stub = StubGenerate()
    splits = l2.build_splits(inf1(), generate=stub, system_prompt=SYSTEM, chunk_size=3)
    assert len(stub.calls) == 3  # nine lines, three at a time
    assert len(l2.distinct_wordforms(inf1())) == 56  # what per-wordform would have cost
    assert splits == {
        (1, 0): ["in", "il"], (1, 2): ["di", "il"],
        (6, 1): ["in", "il"], (8, 3): ["di", "il"],
    }


def test_chunk_size_one_is_line_by_line():
    stub = StubGenerate()
    l2.build_splits(inf1(1, 3), generate=stub, system_prompt=SYSTEM, chunk_size=1)
    assert len(stub.calls) == 3


def test_a_failing_chunk_degrades_to_line_by_line_like_morph_py():
    class GroupFails(StubGenerate):
        def __call__(self, messages):
            user = messages[1]["content"]
            self.calls.append(user)
            lines = user.split("<lines>\n", 1)[1].split("\n</lines>", 1)[0].splitlines()
            if len(lines) > 1:
                return "the group answer is broken"
            return answer_for(user)

    stub = GroupFails()
    settled = []
    splits = l2.build_splits(inf1(1, 3), generate=stub, system_prompt=SYSTEM, chunk_size=3,
                             max_iterations=2, on_settled=settled.append)
    # 2 refused group attempts, then one request per line.
    assert len(stub.calls) == 5
    assert [r.lines for r in settled] == [[1, 2, 3], [1], [2], [3]]
    assert [r.fallback for r in settled] == [False, True, True, True]
    assert splits[(1, 0)] == ["in", "il"]  # the fallback still found the splits


def test_a_failing_single_line_is_not_retried_further():
    class AlwaysFails(StubGenerate):
        def __call__(self, messages):
            self.calls.append(messages[1]["content"])
            return "broken"

    stub = AlwaysFails()
    settled = []
    splits = l2.build_splits(inf1(1, 1), generate=stub, system_prompt=SYSTEM, chunk_size=1,
                             max_iterations=2, on_settled=settled.append)
    assert len(stub.calls) == 2 and len(settled) == 1
    assert splits == {}


def test_build_splits_streams_each_chunk_as_it_settles():
    seen = []
    l2.build_splits(inf1(), generate=StubGenerate(), system_prompt=SYSTEM, chunk_size=3,
                    on_settled=seen.append)
    assert [r.lines for r in seen] == [[1, 2, 3], [4, 5, 6], [7, 8, 9]]


def test_a_wordform_answered_two_ways_keeps_both_and_is_recorded_as_a_conflict():
    # `nel` appears at 1:1 and 6:2; make the second chunk answer it the other way.
    class Drifts(StubGenerate):
        def __call__(self, messages):
            user = messages[1]["content"]
            self.calls.append(user)
            first = user.split("<lines>\n", 1)[1].split(" ", 1)[0]
            table = SPLITS if first == "1" else {**SPLITS, "nel": "ne+lo"}
            return answer_for(user, table)

    settled = []
    splits = l2.build_splits(inf1(), generate=Drifts(), system_prompt=SYSTEM, chunk_size=3,
                             on_settled=settled.append)
    assert splits[(1, 0)] == ["in", "il"]  # each occurrence keeps its own reading
    assert splits[(6, 1)] == ["ne", "lo"]
    conflicts = [c for r in settled for c in r.conflicts]
    assert [(c["word"], c["first"], c["here"]) for c in conflicts] == [
        ("nel", ["in", "il"], ["ne", "lo"])
    ]


# --- The artifact ----------------------------------------------------------------------------


def test_the_artifact_goes_beside_gen2_never_inside_it():
    path = l2.artifact_path("inferno", 1)
    assert path.parts[-3:] == ("l2", "inferno", "01.tsv")
    assert "gen2" not in path.parts  # gen2/ holds code, not output
    assert path.parent.parent.parent.name == "layers"


def test_render_artifact_writes_one_row_per_entry_with_the_header():
    line = l1.l1_line(1, "Nel mezzo")
    text = l2.render_artifact([l2.apply_splits(line, {(1, 0): ["in", "il"]})])
    assert text.splitlines() == [
        "line\tl1_index\tl2_index\ttext",
        "1\t0\t0\tin",
        "1\t0\t1\til",
        "1\t1\t2\tmezzo",
    ]


def test_artifact_round_trips():
    lines = inf1()
    splits = l2.build_splits(lines, generate=StubGenerate(), system_prompt=SYSTEM)
    l2_lines = [l2.apply_splits(line, splits) for line in lines]
    back = l2.parse_artifact(l2.render_artifact(l2_lines))
    assert [(line.no, [(e.l1_index, e.text) for e in line.entries]) for line in back] == [
        (line.no, [(e.l1_index, e.text) for e in line.entries]) for line in l2_lines
    ]


def test_the_split_costs_exactly_the_measured_entries_over_inf_1_1_9():
    lines = inf1()
    splits = l2.build_splits(lines, generate=StubGenerate(), system_prompt=SYSTEM)
    l2_lines = [l2.apply_splits(line, splits) for line in lines]
    l1_tokens = sum(len(line.tokens) for line in lines)
    l2_entries = sum(len(line.entries) for line in l2_lines)
    # Four composite tokens in these nine lines — Nel 1:1, del 1:1, nel 6:2, del 8:4 —
    # each yielding one extra entry.
    assert l1_tokens == 74 and l2_entries == 78


# --- The precedent check ---------------------------------------------------------------------


def test_precedent_splits_reads_composites_off_the_lemma_column():
    theirs = l2.precedent_splits(load_morph("inferno", 1), (1, 9))
    assert theirs["nel"] == (("in", "il"),)
    assert theirs["del"] == (("di", "il"),)


def test_precedent_splits_treats_a_non_composite_row_as_the_wordform_itself():
    theirs = l2.precedent_splits(load_morph("inferno", 1), (1, 9))
    # Old Layer 2's lemma for `cammin` is `cammino`, but a lemma is not a split.
    assert theirs["cammin"] == (("cammin",),)
    assert theirs["ch'"] == (("ch'",),)


def test_our_splits_keys_by_the_l1_surface_form_and_keeps_every_reading():
    lines = inf1(1, 6)
    l2_lines = [l2.apply_splits(line, {(1, 0): ["in", "il"], (6, 1): ["ne", "lo"]})
                for line in lines]
    ours = l2.our_splits(lines, l2_lines)
    assert ours["nel"] == (("in", "il"), ("ne", "lo"))
    assert ours["mezzo"] == (("mezzo",),)


def test_check_against_precedent_agrees_where_the_split_is_the_recorded_one():
    lines = inf1()
    splits = l2.build_splits(lines, generate=StubGenerate(), system_prompt=SYSTEM)
    l2_lines = [l2.apply_splits(line, splits) for line in lines]
    rows = l2.check_against_precedent(lines, l2_lines, load_morph("inferno", 1),
                                      line_range=(1, 9))
    verdicts = {row.wordform: row.verdict for row in rows}
    assert verdicts["nel"] == "agrees" and verdicts["del"] == "agrees"
    assert set(verdicts.values()) == {"agrees"}
    assert len(rows) == 56


def test_check_against_precedent_reports_a_wrong_split_as_differs():
    lines = inf1(1, 1)
    l2_lines = [l2.apply_splits(line, {(1, 0): ["ne", "lo"]}) for line in lines]
    rows = l2.check_against_precedent(lines, l2_lines, load_morph("inferno", 1),
                                      line_range=(1, 1))
    row = next(r for r in rows if r.wordform == "nel")
    assert row.verdict == "differs"
    assert row.ours == (("ne", "lo"),) and row.theirs == (("in", "il"),)


def test_a_wordform_this_artifact_splits_two_ways_is_reported_not_hidden():
    lines = inf1(1, 6)
    l2_lines = [l2.apply_splits(line, {(1, 0): ["in", "il"], (6, 1): ["ne", "lo"]})
                for line in lines]
    rows = l2.check_against_precedent(lines, l2_lines, load_morph("inferno", 1),
                                      line_range=(1, 6))
    row = next(r for r in rows if r.wordform == "nel")
    assert row.verdict == "ours-ambiguous"
    assert row.ours == (("in", "il"), ("ne", "lo"))


def test_check_against_precedent_never_collapses_two_recorded_readings():
    class Row:
        def __init__(self, word, lemma):
            self.word, self.lemma = word, lemma

    rows = l2.check_against_precedent(
        [l1.l1_line(1, "nel")],
        [l2.apply_splits(l1.l1_line(1, "nel"), {(1, 0): ["in", "il"]})],
        {1: (Row("nel", "in+il"),), 2: (Row("nel", "ne+lo"),)},
    )
    row = next(r for r in rows if r.wordform == "nel")
    assert row.verdict == "precedent-ambiguous"
    assert row.theirs == (("in", "il"), ("ne", "lo"))


# --- The report: two faces of one aggregate (ARCHITECTURE.md §6) -----------------------------


def _report_over(results):
    report = l2.SplitReport()
    for result in results:
        report.add_chunk(result.to_dict())
    return report


def test_the_report_is_fed_by_exactly_the_records_the_log_carries():
    settled = []
    l2.build_splits(inf1(), generate=StubGenerate(), system_prompt=SYSTEM, chunk_size=3,
                    on_settled=settled.append)
    m = _report_over(settled).metrics()
    assert m["chunks"] == 3 and m["settled_chunks"] == 3 and m["unresolved_chunks"] == 0
    assert m["tokens_answered"] == 68  # 74 L1 tokens less 6 punctuation marks
    assert m["split"] == 4 and m["passed_through"] == 64
    assert m["attempts"] == 3 and m["refusals"] == 0
    assert m["unresolved_lines"] == []


def test_the_report_counts_refusals_and_the_line_by_line_fallback():
    class GroupFails(StubGenerate):
        def __call__(self, messages):
            user = messages[1]["content"]
            self.calls.append(user)
            lines = user.split("<lines>\n", 1)[1].split("\n</lines>", 1)[0].splitlines()
            return "broken" if len(lines) > 1 else answer_for(user)

    settled = []
    l2.build_splits(inf1(1, 3), generate=GroupFails(), system_prompt=SYSTEM, chunk_size=3,
                    max_iterations=2, on_settled=settled.append)
    m = _report_over(settled).metrics()
    assert m["chunks"] == 4 and m["unresolved_chunks"] == 1 and m["fallback_chunks"] == 3
    assert m["refusals"] == 2
    # The group failed, but every one of its lines was answered on retry — so no line
    # is left without an answer and the gate still passes.
    assert m["unresolved_lines"] == []
    # The refused group's tokens are not counted; only the three retries' are.
    assert m["tokens_answered"] == len(l2.asked_tokens(inf1(1, 3)))


def test_a_line_no_attempt_ever_answered_stays_on_the_unresolved_list():
    class AlwaysFails(StubGenerate):
        def __call__(self, messages):
            self.calls.append(messages[1]["content"])
            return "broken"

    settled = []
    l2.build_splits(inf1(1, 2), generate=AlwaysFails(), system_prompt=SYSTEM, chunk_size=2,
                    max_iterations=1, on_settled=settled.append)
    m = _report_over(settled).metrics()
    assert m["unresolved_lines"] == [1, 2]
    assert "gate == 0 lines: FAIL" in _report_over(settled).summary()


def test_summary_timings_are_summed_steps_never_a_wall_span():
    # ARCHITECTURE.md §5: no start-to-end span, no `started_at` field.
    report = l2.SplitReport()
    report.add_chunk({"lines": [1], "tokens": 1, "resolved": True, "attempts": [{}],
                      "answers": [], "seconds": 2.0})
    report.add_chunk({"lines": [2], "tokens": 1, "resolved": True, "attempts": [{}],
                      "answers": [], "seconds": 4.0})
    m = report.metrics()
    assert m["step_seconds_total"] == 6.0
    assert m["step_seconds_mean"] == 3.0 and m["step_seconds_max"] == 4.0
    assert "elapsed_seconds" not in m and "started_at" not in m


def test_slow_steps_are_counted_against_the_benchmark_threshold():
    report = l2.SplitReport()
    report.add_chunk({"lines": [1], "tokens": 0, "resolved": True, "seconds": 1.0})
    report.add_chunk({"lines": [2], "tokens": 0, "resolved": True,
                      "seconds": l2.SLOW_STEP_SECONDS})
    assert report.metrics()["slow_steps"] == 1


def test_api_retry_counters_fold_in_and_default_to_zero_when_untracked():
    report = l2.SplitReport()
    report.add_retries(None)  # no status line owned the display
    assert report.metrics()["api_retries"] == 0
    report.add_retries((3, 12.5))
    assert report.metrics()["api_retries"] == 3
    assert report.metrics()["api_retry_seconds"] == 12.5


def test_the_summary_record_is_the_metrics_dict_and_carries_the_run_context():
    report = l2.SplitReport(context={"record": "summary", "canticle": "inferno",
                                     "canto": 1, "model": "m", "skill_digest": "d"})
    m = report.metrics()
    assert m["record"] == "summary" and m["canticle"] == "inferno"
    assert m["skill_digest"] == "d"


def test_both_reporting_faces_render_and_show_the_gate_with_its_threshold():
    report = l2.SplitReport()
    report.add_chunk({"lines": [1], "tokens": 1, "resolved": True, "attempts": [{}],
                      "answers": [{"line": 1, "parts": ["in", "il"]}], "seconds": 1.0})
    assert "gate == 0 lines: PASS" in report.summary()


def test_conflicts_reach_the_metrics_and_the_summary_line():
    report = l2.SplitReport()
    report.add_chunk({"lines": [6], "tokens": 1, "resolved": True, "attempts": [{}],
                      "answers": [{"line": 6, "parts": ["ne", "lo"]}], "seconds": 1.0,
                      "conflicts": [{"word": "nel", "line": 6, "first": ["in", "il"],
                                     "here": ["ne", "lo"]}]})
    assert len(report.metrics()["conflicts"]) == 1
    assert "1 answered two ways" in report.summary()


# --- The prompt is a file, and it loads ------------------------------------------------------


def test_the_split_skill_loads_with_its_declared_resource():
    from dante_corpus.harness.skills import Skill

    skill = Skill.load(l2.SKILL_DIR)
    assert skill.name == "l2-split"
    assert "answer.md" in skill.resources
    assert "<split>" in skill.resource("answer.md")
    assert len(skill.digest()) == 64
