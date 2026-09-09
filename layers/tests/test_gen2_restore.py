"""Tests for generation 2's Layer 2, step 0 — the restore (`layers/gen2/restore.py`).

Run on demand — `uv run pytest layers/tests` — the same way `harness/tests` does; `layers/`
is not yet part of the maintained root suite (`pyproject.toml` `testpaths`).

No test touches a model or a network (`ARCHITECTURE.md` §8): the model is a scripted stub
whose raw answer strings go through the real parser, so the wire format under test is the
one the live run uses.
"""

import pytest

from layers.gen2 import l1, l2, restore


# --- The stub model -------------------------------------------------------------------------

# The one restoration *Inf* 1:1-3 contains; every other token is written whole.
RESTORATIONS = {"cammin": "cammino"}


def answer_for(user_message, table=RESTORATIONS):
    """A correct `<restore>` block for whatever tokens the message listed."""
    block = user_message.split("<tokens>\n", 1)[1].split("\n</tokens>", 1)[0]
    tokens = block.split()
    rows = [
        f"{token}:{table[token.casefold()]}"
        for token in tokens
        if token.casefold() in table
    ]
    return "reasoning\n<restore>\n" + "\n".join(rows) + "\n</restore>"


def stub(answers):
    """A `generate` that returns the queued answers in order, recording what it was sent."""
    sent = []

    def generate(messages):
        sent.append(messages)
        return answers[len(sent) - 1] if len(sent) <= len(answers) else answers[-1]

    generate.sent = sent
    return generate


def lines_1_3():
    return list(l1.l1_canto("inferno", 1))[:3]


# --- The gate's criterion: what counts as a restoration --------------------------------------


@pytest.mark.parametrize(
    "token, restored",
    [
        ("cammin", "cammino"),   # dropped final syllable
        ("ben", "bene"),
        ("pel", "pelo"),         # the trap this pass exists for
        ("ch'", "che"),          # apostrophe at the end
        ("l'", "lo"),
        ("Tant'", "Tanto"),      # case is not a difference
        ("i'", "io"),
        ("'l", "il"),            # apostrophe at the beginning
        ("'ncontro", "incontro"),
        ("'nvidia", "invidia"),
    ],
)
def test_letters_put_back_at_the_ends_are_restorations(token, restored):
    assert restore.is_restoration(token, restored)


@pytest.mark.parametrize(
    "token, restored",
    [
        ("sanza", "senza"),      # respelling: `a` would have to become `e`
        ("core", "cuore"),
        ("giuso", "giu"),        # shorter, not longer
        ("ritrovai", "ritrovare"),  # a dictionary form is not a restoration
        ("mezzo", "mezzo"),      # unchanged says nothing
    ],
)
def test_a_respelling_or_a_lemma_is_not_a_restoration(token, restored):
    assert not restore.is_restoration(token, restored)


@pytest.mark.parametrize(
    "token, restored",
    [
        ("ch'", "ache"),         # the apostrophe is at the end; this grew at the start
        ("cammin", "acammino"),  # no apostrophe at all, so the start may not grow
        ("pel", "apelo"),
        ("'l", "lo"),            # the apostrophe is at the start; this grew at the end
        ("'ncontro", "ncontrol"),
        ("de'", "ade"),
    ],
)
def test_letters_may_only_be_put_back_where_the_apostrophe_says(token, restored):
    """Reading straight through is not enough: it does not say which end was dropped.

    A leading apostrophe is the only thing that opens the start of a token, and a trailing
    one requires the end to grow — otherwise `ch'` -> `ache` would pass as readily as
    `ch'` -> `che`.
    """
    assert not restore.is_restoration(token, restored)


def test_a_token_elided_at_both_ends_may_grow_at_both():
    assert restore.is_restoration("'nfin", "infine")
    assert not restore.is_restoration("nfin", "infine")  # no apostrophe, no growth at start


def test_the_gate_is_what_keeps_the_pass_off_lexical_substitution():
    """`sanza` -> `senza` is the whole scope question, and it is refused mechanically."""
    assert not restore.is_restoration("sanza", "senza")
    assert restore.is_restoration("pel", "pelo")


# --- The answer contract ---------------------------------------------------------------------


def tokens_of(chunk):
    return restore.asked_tokens(chunk)


def test_only_the_tokens_that_changed_are_listed():
    chunk = lines_1_3()
    tokens = tokens_of(chunk)
    answer = "<restore>\ncammin:cammino\n</restore>"
    rows, error = restore.parse_restore_answer(answer, tokens=tokens)
    assert error == ""
    assert [tokens[index].text for index in rows] == ["cammin"]
    assert list(rows.values()) == ["cammino"]


def test_an_empty_block_means_nothing_was_dropped():
    tokens = tokens_of(lines_1_3())
    rows, error = restore.parse_restore_answer("<restore>\n</restore>", tokens=tokens)
    assert error == ""
    assert rows == {}


def test_a_missing_block_is_refused():
    tokens = tokens_of(lines_1_3())
    _, error = restore.parse_restore_answer("cammin is cammino", tokens=tokens)
    assert "no <restore> block" in error


def test_two_blocks_are_refused():
    tokens = tokens_of(lines_1_3())
    _, error = restore.parse_restore_answer(
        "<restore>\n</restore>\n<restore>\n</restore>", tokens=tokens
    )
    assert "send exactly one" in error


def test_a_two_word_value_is_refused_because_this_pass_never_splits():
    tokens = tokens_of(lines_1_3())
    _, error = restore.parse_restore_answer("<restore>\nNel:in il\n</restore>",
                                            tokens=tokens)
    assert "two words" in error


def test_a_split_value_is_refused():
    tokens = tokens_of(lines_1_3())
    _, error = restore.parse_restore_answer("<restore>\nNel:in+il\n</restore>",
                                            tokens=tokens)
    assert "never splits" in error


def test_a_respelling_is_refused_with_the_rule_it_broke():
    lines = [l1.l1_line(1, "che di pel macolato era coverta")]
    tokens = tokens_of(lines)
    _, error = restore.parse_restore_answer("<restore>\ndi:de\n</restore>", tokens=tokens)
    assert "read straight through" in error


def test_a_value_equal_to_the_token_says_nothing_and_is_refused():
    tokens = tokens_of(lines_1_3())
    _, error = restore.parse_restore_answer("<restore>\nmezzo:mezzo\n</restore>",
                                            tokens=tokens)
    assert "unchanged" in error


def test_a_key_naming_two_places_is_refused_until_it_is_prefixed():
    """A bare key matching two occurrences is refused rather than applied to both."""
    tokens = tokens_of([l1.l1_line(1, "di qua di la")])
    _, error = restore.parse_restore_answer("<restore>\ndi:dio\n</restore>", tokens=tokens)
    assert "names 2 places" in error


def test_the_same_wordform_can_be_restored_two_ways_in_one_passage():
    """`l'` is `lo` before one noun and `la` before another — per occurrence, never pooled."""
    lines = [l1.l1_line(1, "così l' animo e poi l' aura")]
    tokens = tokens_of(lines)
    rows, error = restore.parse_restore_answer(
        "<restore>\ncosì l':lo\npoi l':la\n</restore>", tokens=tokens
    )
    assert error == ""
    assert sorted(rows.values()) == ["la", "lo"]


# --- The bounded step ------------------------------------------------------------------------


def test_a_refused_answer_records_nothing_and_is_asked_again():
    chunk = lines_1_3()
    generate = stub(["no block here", answer_for(restore.ask_message(chunk))])
    result = restore.restore_chunk(
        chunk, generate=generate, system_prompt="s", max_iterations=3
    )
    assert result.accepted
    assert [attempt.accepted for attempt in result.attempts] == [False, True]
    assert result.restored == 1


def test_a_chunk_that_never_passes_leaves_the_table_untouched():
    chunk = lines_1_3()
    generate = stub(["nothing"])
    result = restore.restore_chunk(
        chunk, generate=generate, system_prompt="s", max_iterations=2
    )
    assert not result.accepted
    assert result.answers == {}
    assert result.stop_reason == "budget"


def test_every_attempt_sends_exactly_system_and_user():
    chunk = lines_1_3()
    generate = stub(["bad", answer_for(restore.ask_message(chunk))])
    restore.restore_chunk(chunk, generate=generate, system_prompt="s", max_iterations=3)
    for messages in generate.sent:
        assert [message["role"] for message in messages] == ["system", "user"]


def test_a_group_that_fails_degrades_to_line_by_line():
    lines = lines_1_3()
    answers = ["nope", "nope", "nope"] + [
        answer_for(restore.ask_message((line,))) for line in lines for _ in (0,)
    ]
    generate = stub(answers)
    restorations = restore.build_restorations(
        lines, generate=generate, system_prompt="s", chunk_size=3, max_iterations=3
    )
    assert restorations  # `cammin` was recovered by the per-line retries


# --- The artifact -----------------------------------------------------------------------------


def test_the_artifact_writes_every_token_and_reads_back_the_changed_ones(tmp_path):
    lines = lines_1_3()
    restorations = {(1, 3): "cammino"}
    text = restore.render_artifact(lines, restorations)
    assert text.splitlines()[0] == "line\tl1_index\ttext\trestored"
    assert "1\t3\tcammin\tcammino" in text
    assert "1\t1\tmezzo\tmezzo" in text  # unchanged tokens are written too

    path = tmp_path / "01-restore.tsv"
    path.write_text(text, encoding="utf-8")
    # `parse_artifact` keeps every position (that is what resumption reads); the split
    # pass's own loader keeps only what actually changed.
    assert restore.parse_artifact(text)[(1, 1)] == "mezzo"
    assert restore.load_restorations(path) == {(1, 3): "cammino"}


# --- What the split pass does with it ----------------------------------------------------------


def test_a_restored_token_is_asked_about_in_its_restored_spelling():
    lines = [l1.l1_line(33, "che di pel macolato era coverta")]
    plain = [token.text for token in l2.asked_tokens(lines)]
    restored = [token.text for token in l2.asked_tokens(lines, {(33, 2): "pelo"})]
    assert "pel" in plain and "pelo" not in plain
    assert "pelo" in restored and "pel" not in restored
    assert "pelo" in l2.ask_message(lines, restored={(33, 2): "pelo"})


def test_the_question_says_that_the_token_list_differs_from_the_verse():
    lines = [l1.l1_line(33, "che di pel macolato era coverta")]
    message = l2.ask_message(lines, restored={(33, 2): "pelo"})
    assert "<note>" in message
    assert "<note>" not in l2.ask_message(lines)


def test_a_token_left_whole_keeps_its_L1_surface_however_it_was_asked_about():
    """The restoration moves the *question*, never what an unsplit entry records —
    restoring an entry's spelling stays step 3's job."""
    lines = [l1.l1_line(33, "che di pel macolato era coverta")]
    generate = stub(["<split>\n</split>"])
    splits = l2.build_splits(
        lines, generate=generate, system_prompt="s", chunk_size=3,
        restored={(33, 2): "pelo"},
    )
    assert splits == {}
    l2_line = l2.apply_splits(lines[0], splits)
    assert [entry.text for entry in l2_line.entries][2] == "pel"


def test_the_split_answer_is_keyed_by_the_restored_token():
    """A key is copied from the token list, which is the restored spelling — so `locate_key`
    resolves against what the model was actually shown."""
    lines = [l1.l1_line(1, "e ben ch' i' fossi")]
    tokens = l2.asked_tokens(lines, {(1, 1): "bene"})
    splits, error = l2.parse_split_answer("<split>\nbene:be+ne\n</split>", tokens=tokens)
    assert error == ""
    assert splits == {1: ["be", "ne"]}
