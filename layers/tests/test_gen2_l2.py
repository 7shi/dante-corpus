"""Tests for generation 2's Layer 2 — grammatical words and coarse POS (`layers/gen2/l2.py`).

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

# The two composite tokens *Inf* 1:1-9 actually contains, as the answer writes them:
# `words` joined by `+`, one tag per word. Every other token is one word.
COMPOSITE = {
    "nel": ("in+il", "preposition+article"),
    "del": ("di+il", "preposition+article"),
}


def asked_rows(user_message):
    """The `(line, index, token)` triples of the blank table the request supplied."""
    block = user_message.split("<table>\n", 1)[1].split("\n</table>", 1)[0]
    out = []
    for raw in block.splitlines():
        cells = [cell.strip() for cell in raw.strip().strip("|").split("|")]
        if len(cells) != 5 or not cells[0].isdigit():
            continue
        out.append((cells[0], cells[1], cells[2]))
    return out


def answer_for(user_message, table=COMPOSITE, tag="noun"):
    """The request's own table, filled in — which is the whole contract.

    A token the table knows is written as its parts and their tags; every other token
    repeats itself and takes a single default tag, which is all the gate asks of it.
    """
    rows = ["| Line | Index | Token | Words | Part of Speech |", "|---|---|---|---|---|"]
    for line_no, index, token in asked_rows(user_message):
        words, tags = table.get(token.casefold(), (token, tag))
        rows.append(f"| {line_no} | {index} | {token} | {words} | {tags} |")
    return "<table>\n" + "\n".join(rows) + "\n</table>"


class StubGenerate:
    """A scripted `generate(messages) -> str`, counting calls and resets.

    `script` maps a chunk's line-number tuple to a list of raw answers consumed in order;
    anything unscripted gets the correct answer for the tokens it was asked about.
    """

    def __init__(self, script=None, table=COMPOSITE):
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


SYSTEM = "you are the l2 words step"


def inf1(start=1, end=9):
    return [line for line in l1.l1_canto("inferno", 1) if start <= line.no <= end]


def one(*parts_and_tags):
    """`Analysis` from `("in", "preposition"), ("il", "article")` pairs."""
    return l2.Analysis(
        parts=tuple(p for p, _ in parts_and_tags), tags=tuple(t for _, t in parts_and_tags)
    )


def table(rows, line=1):
    """A `<table>` block from `(token, words, tags)` triples — all on `line` unless a row
    names its own — header and ruler included."""
    body = ["| Line | Index | Token | Words | Part of Speech |", "|---|---|---|---|---|"]
    for index, row in enumerate(rows, start=1):
        no, token, words, tags = row if len(row) == 4 else (line, *row)
        body.append(f"| {no} | {index} | {token} | {words} | {tags} |")
    return "<table>\n" + "\n".join(body) + "\n</table>"


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


def test_elided_and_apocopated_forms_are_asked_about():
    for token in ("ch'", "i'", "'l", "cammin", "ben"):
        assert l2.is_splittable(token)


def test_distinct_wordforms_dedupes_case_folded_in_first_appearance_order():
    lines = [l1.l1_line(1, "Nel mezzo, nel"), l1.l1_line(2, "mezzo del")]
    assert l2.distinct_wordforms(lines) == ["Nel", "mezzo", "del"]


# --- apply_analyses: the pure half -----------------------------------------------------------


def test_apply_analyses_reproduces_the_l2_md_worked_example_for_inf_1_1():
    line = inf1(1, 1)[0]
    got = l2.apply_analyses(
        line,
        {
            (1, 0): one(("in", "preposition"), ("il", "article")),
            (1, 2): one(("di", "preposition"), ("il", "article")),
        },
    )
    assert [(e.l1_index, e.text) for e in got.entries] == [
        (0, "in"), (0, "il"), (1, "mezzo"), (2, "di"), (2, "il"),
        (3, "cammin"), (4, "di"), (5, "nostra"), (6, "vita"),
    ]
    assert [e.pos for e in got.entries][:2] == ["preposition", "article"]


def test_a_token_with_no_analysis_passes_through_untagged():
    line = l1.l1_line(1, "mezzo, oscura")
    got = l2.apply_analyses(line, {})
    assert [(e.text, e.pos) for e in got.entries] == [
        ("mezzo", ""), (",", ""), ("oscura", ""),
    ]


def test_punctuation_keeps_its_position_and_never_takes_a_tag():
    line = l1.l1_line(1, "mi ritrovai per una selva oscura,")
    got = l2.apply_analyses(line, {(1, 0): one(("mi", "pronoun"))})
    assert [(e.l1_index, e.text, e.pos) for e in got.entries][-2:] == [
        (5, "oscura", ""), (6, ",", ""),
    ]


def test_analyses_are_per_occurrence_so_one_wordform_can_go_two_ways():
    first = l1.l1_line(1, "Nel mezzo")
    second = l1.l1_line(6, "nel pensier")
    analyses = {
        (1, 0): one(("in", "preposition"), ("il", "article")),
        (6, 0): one(("ne", "pronoun"), ("lo", "pronoun")),
    }
    assert [e.text for e in l2.apply_analyses(first, analyses).entries][:2] == ["in", "il"]
    assert [e.text for e in l2.apply_analyses(second, analyses).entries][:2] == ["ne", "lo"]


def test_a_single_word_analysis_is_one_entry_carrying_its_tag():
    line = l1.l1_line(1, "cammin")
    got = l2.apply_analyses(line, {(1, 0): one(("cammin", "noun"))})
    assert [(e.text, e.pos) for e in got.entries] == [("cammin", "noun")]


# --- The question ----------------------------------------------------------------------------


def test_the_ask_shows_the_lines_for_context_and_the_table_to_fill_in():
    message = l2.ask_message(inf1(1, 1))
    assert "1 Nel mezzo del cammin di nostra vita" in message
    assert "| Line | Index | Token | Words | Part of Speech |" in message
    assert "| 1 | Nel |  |  |" in message
    assert "Nothing is on record" in message


def test_the_blank_table_carries_the_line_number_on_every_row():
    """A flat token list loses the line boundaries exactly where the analysis needs them
    (operator, 2026-09-09); the skeleton keeps each row attached to its verse."""
    blank = l2.render_blank_table(l2.asked_tokens(inf1(32, 33)))
    assert "| 32 | 2 | lonza |  |  |" in blank
    assert "| 33 | 9 | pel |  |  |" in blank
    assert "," not in blank  # punctuation is not in the table at all


def test_the_blank_table_numbers_its_rows_from_one_across_the_whole_chunk():
    """The Index is the row's own number, not the artifact's `l1_index` (operator,
    2026-09-10): it runs 1..n over the rows listed, unbroken across a line boundary and
    skipping nothing, because a gap or a repeat is exactly what it exists to make visible.
    """
    tokens = l2.asked_tokens(inf1(32, 33))
    blank = l2.render_blank_table(tokens)
    numbers = [
        row.strip().strip("|").split("|")[1].strip()
        for row in blank.splitlines()[2:]
    ]
    assert numbers == [str(n) for n in range(1, len(tokens) + 1)]


def test_a_row_whose_index_moved_is_refused():
    """The Index column is copied, so a number out of step means a row is missing,
    repeated, or out of place — caught before any of its content is read."""
    tokens = l2.asked_tokens(inf1(1, 1))
    rows = [(token.line, token.text, token.text, "noun") for token in tokens]
    answer = table(rows).replace("| 1 | 3 |", "| 1 | 4 |", 1)
    analyses, error = l2.parse_words_answer(answer, tokens=tokens)
    assert analyses == {} and "Index" in error


def test_a_row_whose_line_number_moved_is_refused():
    tokens = l2.asked_tokens(inf1(32, 33))
    rows = [(token.line, token.text, token.text, "noun") for token in tokens]
    rows[-1] = (32, rows[-1][1], rows[-1][2], "noun")  # coverta is on line 33
    _, error = l2.parse_words_answer(table(rows), tokens=tokens)
    assert "says line '32'" in error and "line 33" in error


def test_a_refused_ask_carries_the_reason_and_asks_for_the_whole_table_again():
    message = l2.ask_message(inf1(1, 1), refusal="row 3 says 'x'")
    assert "row 3 says 'x'" in message
    assert "Send the whole table again" in message


# --- The gate --------------------------------------------------------------------------------


def test_the_answer_carries_one_row_per_token_split_or_not():
    tokens = l2.asked_tokens(inf1(1, 1))
    answer = table([
        ("Nel", "in+il", "preposition+article"),
        ("mezzo", "mezzo", "noun"),
        ("del", "di+il", "preposition+article"),
        ("cammin", "cammin", "noun"),
        ("di", "di", "preposition"),
        ("nostra", "nostra", "adjective"),
        ("vita", "vita", "noun"),
    ])
    analyses, error = l2.parse_words_answer(answer, tokens=tokens)
    assert not error
    assert analyses[0] == one(("in", "preposition"), ("il", "article"))
    assert analyses[1] == one(("mezzo", "noun"))
    assert len(analyses) == len(tokens)


def test_a_missing_row_is_refused_rather_than_read_as_a_single_word():
    tokens = l2.asked_tokens(inf1(1, 1))
    answer = table([("Nel", "in+il", "preposition+article")])
    analyses, error = l2.parse_words_answer(answer, tokens=tokens)
    assert analyses == {} and "1 row(s) for 7 token(s)" in error


def test_rows_are_matched_by_position_so_a_repeated_token_is_no_problem():
    line = l1.l1_line(1, "e vidi e cose")
    tokens = l2.asked_tokens([line])
    answer = table([
        ("e", "e", "conjunction"),
        ("vidi", "vidi", "verb"),
        ("e", "e", "conjunction"),
        ("cose", "cose", "noun"),
    ])
    analyses, error = l2.parse_words_answer(answer, tokens=tokens)
    assert not error and analyses[0] == analyses[2] == one(("e", "conjunction"))


def test_a_row_naming_the_wrong_token_is_refused_with_both_names():
    tokens = l2.asked_tokens([l1.l1_line(1, "mezzo cammin")])
    answer = table([("cammin", "cammin", "noun"), ("mezzo", "mezzo", "noun")])
    _, error = l2.parse_words_answer(answer, tokens=tokens)
    assert "'cammin'" in error and "'mezzo'" in error


def test_the_token_column_is_matched_case_insensitively():
    tokens = l2.asked_tokens([l1.l1_line(1, "Nel mezzo")])
    answer = table([("nel", "in+il", "preposition+article"), ("mezzo", "mezzo", "noun")])
    analyses, error = l2.parse_words_answer(answer, tokens=tokens)
    assert not error and analyses[0].parts == ("in", "il")


def test_a_single_word_may_have_its_dropped_letters_put_back():
    """`ben` -> `bene` is a restoration, not a lemma: the pass subsumes it (operator)."""
    tokens = l2.asked_tokens([l1.l1_line(1, "ben")])
    analyses, error = l2.parse_words_answer(table([("ben", "bene", "adverb")]), tokens=tokens)
    assert not error and analyses[0] == one(("bene", "adverb"))


def test_an_elision_may_be_restored_at_the_end_the_apostrophe_opens():
    tokens = l2.asked_tokens([l1.l1_line(1, "ch'")])
    analyses, error = l2.parse_words_answer(table([("ch'", "che", "pronoun")]), tokens=tokens)
    assert not error and analyses[0].parts == ("che",)


def test_a_token_left_exactly_as_written_is_still_accepted():
    tokens = l2.asked_tokens([l1.l1_line(1, "ben")])
    analyses, error = l2.parse_words_answer(table([("ben", "ben", "adverb")]), tokens=tokens)
    assert not error and analyses[0].parts == ("ben",)


@pytest.mark.parametrize(
    "token, answered",
    [
        ("sanza", "senza"),      # a respelling: this language's own word, not a short one
        ("smarrita", "smarrito"),  # a lemma: the ending changes, the letters do not read through
        ("era", "essere"),         # a lemma, further still
        ("ch'", "ache"),           # letters put back at an end the spelling does not open
    ],
)
def test_a_substitution_that_is_not_a_restoration_is_refused(token, answered):
    """The boundary is mechanical (`is_restoration`), not a request in the prompt: the
    token's own letters must read straight through the answer, growing only where its own
    spelling says letters were dropped."""
    tokens = l2.asked_tokens([l1.l1_line(1, token)])
    _, error = l2.parse_words_answer(table([(token, answered, "noun")]), tokens=tokens)
    assert "neither the token as it stands nor the token with its dropped letters" in error


def test_the_gate_accepts_a_three_way_split():
    tokens = l2.asked_tokens([l1.l1_line(1, "dirtelo")])
    answer = table([("dirtelo", "dir+te+lo", "verb+pronoun+pronoun")])
    analyses, error = l2.parse_words_answer(answer, tokens=tokens)
    assert not error and analyses[0].parts == ("dir", "te", "lo")


def test_more_parts_than_the_cap_are_refused():
    tokens = l2.asked_tokens([l1.l1_line(1, "dirtelo")])
    answer = table([("dirtelo", "d+i+r+telo", "verb+verb+verb+pronoun")])
    _, error = l2.parse_words_answer(answer, tokens=tokens)
    assert "4 parts" in error


def test_one_tag_per_word_or_the_row_is_refused():
    tokens = l2.asked_tokens([l1.l1_line(1, "Nel")])
    answer = table([("Nel", "in+il", "preposition")])
    _, error = l2.parse_words_answer(answer, tokens=tokens)
    assert "one tag per word" in error


def test_a_tag_outside_the_closed_set_is_refused_and_the_set_is_named():
    tokens = l2.asked_tokens([l1.l1_line(1, "Beatrice")])
    answer = table([("Beatrice", "Beatrice", "proper noun")])
    _, error = l2.parse_words_answer(answer, tokens=tokens)
    assert "'proper noun'" in error and "interjection" in error


def test_the_closed_set_is_ten_coarse_tags():
    assert len(l2.POS_TAGS) == 10
    assert "noun" in l2.POS_TAGS and "participle" not in l2.POS_TAGS


@pytest.mark.parametrize(
    "answer",
    [
        "no block at all",
        "<table>\n| 1 | 1 | Nel | in+il | preposition+article |\n</table>\n<table>\n</table>",
        "<table>\n| 1 | 1 | Nel | in+il |\n</table>",
        "<table>\n| 1 | 1 | Nel | in+ | preposition+article |\n</table>",
        "<table>\n| 1 | 1 | Nel | in il | preposition+article |\n</table>",
    ],
)
def test_parse_words_answer_refuses_every_malformed_shape(answer):
    tokens = l2.asked_tokens([l1.l1_line(1, "Nel")])
    analyses, error = l2.parse_words_answer(answer, tokens=tokens)
    assert analyses == {} and error


# --- The bounded step ------------------------------------------------------------------------


def test_analyze_chunk_settles_on_the_first_good_answer():
    stub = StubGenerate()
    result = l2.analyze_chunk(inf1(1, 3), generate=stub, system_prompt=SYSTEM)
    assert result.accepted and result.stop_reason == "settled"
    assert len(stub.calls) == 1 and stub.resets == 1
    assert result.splits == 2  # Nel and del, both in line 1
    assert len(result.answers) == len(result.tokens)


def test_a_chunk_where_nothing_splits_is_settled_not_failed():
    stub = StubGenerate()
    result = l2.analyze_chunk(inf1(2, 2), generate=stub, system_prompt=SYSTEM)
    assert result.accepted and result.splits == 0
    assert all(not analysis.split for analysis in result.answers.values())


def test_a_refused_answer_records_nothing_and_the_budget_is_a_cap():
    stub = StubGenerate(script={(1, 2, 3): ["nothing like a table"]})
    result = l2.analyze_chunk(inf1(1, 3), generate=stub, system_prompt=SYSTEM,
                              max_iterations=2)
    assert not result.accepted and result.stop_reason == "budget"
    assert result.answers == {} and len(stub.calls) == 2


def test_the_refusal_reason_is_fed_back_verbatim_on_the_retry():
    stub = StubGenerate(script={(1,): ["<table>\n| 1 | 1 | Nel | bene | noun |\n</table>", None]})

    def generate(messages):
        user = messages[1]["content"]
        stub.calls.append(user)
        if len(stub.calls) == 1:
            return table([("Nel", "nel", "preposition")])
        return answer_for(user)

    result = l2.analyze_chunk(inf1(1, 1), generate=generate, system_prompt=SYSTEM)
    assert result.accepted
    assert "The check refused your last answer" in stub.calls[1]
    assert "1 row(s) for 7 token(s)" in stub.calls[1]  # the gate's own words, verbatim


def test_a_chunk_of_pure_punctuation_costs_no_request():
    stub = StubGenerate()
    result = l2.analyze_chunk([l1.l1_line(1, "«»")], generate=stub, system_prompt=SYSTEM)
    assert result.accepted and not stub.calls and result.answers == {}


# --- build_l2 --------------------------------------------------------------------------------


def test_build_l2_asks_once_per_chunk_not_once_per_wordform():
    stub = StubGenerate()
    found = l2.build_l2(inf1(), generate=stub, system_prompt=SYSTEM)
    assert len(stub.calls) == 3  # nine lines, three lines a chunk
    assert found[(1, 0)].parts == ("in", "il")
    assert found[(1, 1)] == one(("mezzo", "noun"))


def test_chunk_size_one_is_line_by_line():
    stub = StubGenerate()
    l2.build_l2(inf1(1, 3), generate=stub, system_prompt=SYSTEM, chunk_size=1)
    assert len(stub.calls) == 3


def test_a_failing_chunk_degrades_to_line_by_line_like_morph_py():
    settled = []
    stub = StubGenerate(script={(1, 2, 3): ["garbage"]})
    found = l2.build_l2(
        inf1(1, 3), generate=stub, system_prompt=SYSTEM,
        max_iterations=1, on_settled=settled.append,
    )
    assert [r.lines for r in settled] == [[1, 2, 3], [1], [2], [3]]
    assert [r.fallback for r in settled] == [False, True, True, True]
    assert found[(1, 0)].parts == ("in", "il")  # the retries recovered the answers


def test_a_failing_single_line_is_not_retried_further():
    settled = []
    stub = StubGenerate(script={(1,): ["garbage"]})
    l2.build_l2(
        inf1(1, 1), generate=stub, system_prompt=SYSTEM,
        max_iterations=1, chunk_size=1, on_settled=settled.append,
    )
    assert [r.lines for r in settled] == [[1]]
    assert not settled[0].accepted


def test_build_l2_streams_each_chunk_as_it_settles():
    seen = []
    l2.build_l2(inf1(), generate=StubGenerate(), system_prompt=SYSTEM,
                on_settled=lambda r: seen.append(list(r.lines)))
    assert seen == [[1, 2, 3], [4, 5, 6], [7, 8, 9]]


def test_a_skipped_chunk_costs_no_request_and_is_reported():
    stub = StubGenerate()
    skipped = []
    l2.build_l2(
        inf1(), generate=stub, system_prompt=SYSTEM,
        already_answered=lambda chunk: chunk[0].no == 1,
        on_skipped=lambda chunk: skipped.append([line.no for line in chunk]),
    )
    assert skipped == [[1, 2, 3]] and len(stub.calls) == 2


def test_a_wordform_answered_two_ways_keeps_both_and_is_recorded_as_a_conflict():
    """`nel` at 1:1 and at 6:2 — one answer each, the second one different. Both stand;
    the disagreement is recorded rather than resolved."""
    conflicts = []

    def generate(messages):
        user = messages[1]["content"]
        first = "1 Nel" in user
        return answer_for(
            user,
            COMPOSITE if first else {"nel": ("ne+lo", "pronoun+pronoun")},
        )

    found = l2.build_l2(
        inf1(1, 6), generate=generate, system_prompt=SYSTEM,
        on_settled=lambda r: conflicts.extend(r.conflicts),
    )
    assert found[(1, 0)].parts == ("in", "il")
    assert found[(6, 1)].parts == ("ne", "lo")
    assert [c["word"] for c in conflicts] == ["nel"]
    assert conflicts[0]["first"]["parts"] == ["in", "il"]


def test_the_same_reading_in_two_capitalisations_is_not_a_conflict():
    """A line-initial capital is not a judgment about anything (operator, 2026-09-10):
    `Nel` at 1:1 and `nel` at 6:2, read the same way, are one reading. Folding this out is
    what keeps every sentence-opening word from reporting itself as a disagreement — 22 of
    `Inf` 1's 76 conflicts were capitalisation and nothing else."""
    conflicts = []

    def generate(messages):
        user = messages[1]["content"]
        return answer_for(user, {"nel": ("In+il", "preposition+article")}
                          if "1 Nel" in user else {"nel": ("in+il", "preposition+article")})

    found = l2.build_l2(
        inf1(1, 6), generate=generate, system_prompt=SYSTEM,
        on_settled=lambda r: conflicts.extend(r.conflicts),
    )
    assert found[(1, 0)].parts == ("In", "il") and found[(6, 1)].parts == ("in", "il")
    assert conflicts == []


# --- The artifact ----------------------------------------------------------------------------


def test_the_artifact_goes_beside_gen2_never_inside_it():
    path = l2.artifact_path("inferno", 1)
    assert path.parts[-3:] == ("l2", "inferno", "01.tsv")
    assert "gen2" not in path.parts  # gen2/ holds code, not output
    assert path.parent.parent.parent.name == "layers"


def test_render_artifact_writes_one_row_per_entry_with_the_header():
    line = l1.l1_line(1, "Nel mezzo")
    l2_line = l2.apply_analyses(
        line,
        {
            (1, 0): one(("in", "preposition"), ("il", "article")),
            (1, 1): one(("mezzo", "noun")),
        },
    )
    assert l2.render_artifact([l2_line]).splitlines() == [
        "line\tl1_index\tl2_index\ttext\tpos",
        "1\t0\t0\tin\tpreposition",
        "1\t0\t1\til\tarticle",
        "1\t1\t2\tmezzo\tnoun",
    ]


def test_artifact_round_trips():
    lines = inf1()
    found = l2.build_l2(lines, generate=StubGenerate(), system_prompt=SYSTEM)
    l2_lines = [l2.apply_analyses(line, found) for line in lines]
    back = l2.parse_artifact(l2.render_artifact(l2_lines))
    assert [(line.no, [(e.l1_index, e.text, e.pos) for e in line.entries]) for line in back] == [
        (line.no, [(e.l1_index, e.text, e.pos) for e in line.entries]) for line in l2_lines
    ]


def test_a_split_only_artifact_reads_back_as_nothing_rather_than_as_untagged_answers():
    """The four-column shape this pass replaced. Reading it as answers with no tag would
    let a resume skip chunks that were never asked the POS question at all."""
    text = "line\tl1_index\tl2_index\ttext\n1\t0\t0\tin\n1\t0\t1\til\n"
    assert l2.parse_artifact(text) == []


def test_the_pass_costs_exactly_the_measured_entries_over_inf_1_1_9():
    lines = inf1()
    found = l2.build_l2(lines, generate=StubGenerate(), system_prompt=SYSTEM)
    l2_lines = [l2.apply_analyses(line, found) for line in lines]
    l1_tokens = sum(len(line.tokens) for line in lines)
    l2_entries = sum(len(line.entries) for line in l2_lines)
    # Four composite tokens in these nine lines — Nel 1:1, del 1:1, nel 6:2, del 8:4 —
    # each yielding one extra entry.
    assert l1_tokens == 74 and l2_entries == 78


# --- The precedent check ---------------------------------------------------------------------


class Row:
    """A stand-in for one old Layer 2 row: the three columns this check reads."""

    def __init__(self, word, lemma="", pos=""):
        self.word, self.lemma, self.pos = word, lemma or word, pos


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
    analyses = {
        (1, 0): one(("in", "preposition"), ("il", "article")),
        (6, 1): one(("ne", "pronoun"), ("lo", "pronoun")),
    }
    l2_lines = [l2.apply_analyses(line, analyses) for line in lines]
    ours = l2.our_splits(lines, l2_lines)
    assert ours["nel"] == (("in", "il"), ("ne", "lo"))
    assert ours["mezzo"] == (("mezzo",),)


def test_check_against_precedent_agrees_where_the_split_is_the_recorded_one():
    lines = inf1()
    found = l2.build_l2(lines, generate=StubGenerate(), system_prompt=SYSTEM)
    l2_lines = [l2.apply_analyses(line, found) for line in lines]
    rows = l2.check_against_precedent(lines, l2_lines, load_morph("inferno", 1),
                                      line_range=(1, 9))
    verdicts = {row.wordform: row.verdict for row in rows}
    assert verdicts["nel"] == "agrees" and verdicts["del"] == "agrees"
    assert set(verdicts.values()) == {"agrees"}
    assert len(rows) == 56


def test_check_against_precedent_reports_a_wrong_split_as_differs():
    lines = inf1(1, 1)
    l2_lines = [
        l2.apply_analyses(line, {(1, 0): one(("ne", "pronoun"), ("lo", "pronoun"))})
        for line in lines
    ]
    rows = l2.check_against_precedent(lines, l2_lines, load_morph("inferno", 1),
                                      line_range=(1, 1))
    row = next(r for r in rows if r.wordform == "nel")
    assert row.verdict == "differs"
    assert row.ours == (("ne", "lo"),) and row.theirs == (("in", "il"),)


def test_a_wordform_this_artifact_splits_two_ways_is_reported_not_hidden():
    lines = inf1(1, 6)
    analyses = {
        (1, 0): one(("in", "preposition"), ("il", "article")),
        (6, 1): one(("ne", "pronoun"), ("lo", "pronoun")),
    }
    l2_lines = [l2.apply_analyses(line, analyses) for line in lines]
    rows = l2.check_against_precedent(lines, l2_lines, load_morph("inferno", 1),
                                      line_range=(1, 6))
    row = next(r for r in rows if r.wordform == "nel")
    assert row.verdict == "l2-ambiguous"
    assert row.ours == (("in", "il"), ("ne", "lo"))


def test_a_wordform_this_artifact_reads_one_way_is_layer2_ambiguous_if_old_layer_2_is_not():
    """Symmetric to the `l2-ambiguous` case: old Layer 2 itself records two different
    readings for a wordform (within `line_range`, or all of `morph_rows` when unset, as
    `precedent_splits` already does) — a real disagreement, not folded into `differs`."""
    line = l1.l1_line(1, "nel")
    rows = l2.check_against_precedent(
        [line],
        [l2.apply_analyses(line, {(1, 0): one(("in", "preposition"), ("il", "article"))})],
        {1: (Row("nel", "in+il"),), 2: (Row("nel", "ne+lo"),)},
    )
    row = next(r for r in rows if r.wordform == "nel")
    assert row.verdict == "layer2-ambiguous"
    assert row.theirs == (("in", "il"), ("ne", "lo"))


# --- The POS half of the check ----------------------------------------------------------------


def test_coarse_pos_folds_old_layer_2s_subtypes_onto_this_vocabulary():
    assert l2.coarse_pos("proper noun") == ("noun",)
    assert l2.coarse_pos("relative pronoun") == ("pronoun",)
    assert l2.coarse_pos("past participle") == ("verb",)
    assert l2.coarse_pos("preposition+article") == ("preposition", "article")
    assert l2.coarse_pos("verb + pronoun") == ("verb", "pronoun")


def test_a_tag_with_no_coarse_equivalent_is_left_as_written_rather_than_hidden():
    assert l2.coarse_pos("pos") == ("pos",)


def test_pos_check_counts_a_folded_subtype_as_agreement():
    line = l1.l1_line(1, "Virgilio")
    l2_lines = [l2.apply_analyses(line, {(1, 0): one(("Virgilio", "noun"))})]
    compared, mismatches = l2.check_pos_against_precedent(
        [line], l2_lines, {1: (Row("Virgilio", "Virgilio", "proper noun"),)}
    )
    assert compared == 1 and mismatches == []


def test_pos_check_reports_a_real_category_disagreement_with_its_position():
    line = l1.l1_line(1, "smarrita")
    l2_lines = [l2.apply_analyses(line, {(1, 0): one(("smarrita", "verb"))})]
    compared, mismatches = l2.check_pos_against_precedent(
        [line], l2_lines, {1: (Row("smarrita", "smarrito", "adjective"),)}
    )
    assert compared == 1
    assert [(m.line, m.word, m.ours, m.theirs) for m in mismatches] == [
        (1, "smarrita", ("verb",), ("adjective",))
    ]


def test_a_position_where_the_splits_differ_is_not_also_counted_as_a_pos_difference():
    """One disagreement, one finding: where the two sides split the token differently the
    tags describe different words, so the split check owns it alone."""
    line = l1.l1_line(1, "pel")
    l2_lines = [
        l2.apply_analyses(line, {(1, 0): one(("per", "preposition"), ("il", "article"))})
    ]
    compared, mismatches = l2.check_pos_against_precedent(
        [line], l2_lines, {1: (Row("pel", "pelo", "noun"),)}
    )
    assert compared == 0 and mismatches == []


def test_an_untagged_entry_is_not_compared():
    line = l1.l1_line(1, "mezzo")
    l2_lines = [l2.apply_analyses(line, {})]
    compared, mismatches = l2.check_pos_against_precedent(
        [line], l2_lines, {1: (Row("mezzo", "mezzo", "noun"),)}
    )
    assert compared == 0 and mismatches == []


# --- The report: two faces of one aggregate (ARCHITECTURE.md §6) -----------------------------


def records(lines=None, **kwargs):
    """Run the pass over `lines` and feed the report exactly the log's chunk records."""
    report = l2.L2Report()
    l2.build_l2(
        lines if lines is not None else inf1(),
        system_prompt=SYSTEM,
        on_settled=lambda r: report.add_chunk(r.to_dict()),
        **kwargs,
    )
    return report


def test_the_report_is_fed_by_exactly_the_records_the_log_carries():
    report = records(generate=StubGenerate())
    m = report.metrics()
    assert m["chunks"] == 3 and m["settled_chunks"] == 3 and m["unresolved_chunks"] == 0
    assert m["tokens_answered"] == 68  # 74 L1 tokens less 6 punctuation marks
    assert m["split"] == 4 and m["passed_through"] == 64
    assert m["attempts"] == 3 and m["refusals"] == 0
    assert m["unresolved_lines"] == []


def test_the_tag_counter_is_fed_from_the_same_records():
    report = records(lines=inf1(1, 1), generate=StubGenerate())
    m = report.metrics()
    # The stub tags every non-composite token `noun`: five of them, plus in+il / di+il.
    assert m["tags"]["noun"] == 5
    assert m["tags"]["preposition"] == 2 and m["tags"]["article"] == 2


def test_the_report_counts_refusals_and_the_line_by_line_fallback():
    report = records(
        lines=inf1(1, 3),
        generate=StubGenerate(script={(1, 2, 3): ["garbage"]}),
        max_iterations=1,
    )
    m = report.metrics()
    assert m["chunks"] == 4 and m["unresolved_chunks"] == 1 and m["fallback_chunks"] == 3
    assert m["refusals"] == 1 and m["unresolved_lines"] == []


def test_a_line_no_attempt_ever_answered_stays_on_the_unresolved_list():
    report = records(
        lines=inf1(1, 1),
        generate=StubGenerate(script={(1,): ["garbage"]}),
        max_iterations=1,
        chunk_size=1,
    )
    assert report.metrics()["unresolved_lines"] == [1]
    assert "FAIL" in report.summary()


def test_summary_timings_are_summed_steps_never_a_wall_span():
    report = l2.L2Report()
    report.add_chunk({"resolved": True, "lines": [1], "tokens": 3, "seconds": 2.0,
                      "attempts": [{"accepted": True}]})
    report.add_chunk({"resolved": True, "lines": [2], "tokens": 3, "seconds": 4.0,
                      "attempts": [{"accepted": True}]})
    m = report.metrics()
    assert m["step_seconds_total"] == 6.0 and m["step_seconds_mean"] == 3.0
    assert m["step_seconds_max"] == 4.0


def test_slow_steps_are_counted_against_the_benchmark_threshold():
    report = l2.L2Report()
    report.add_chunk({"resolved": True, "lines": [1], "seconds": l2.SLOW_STEP_SECONDS + 1,
                      "attempts": []})
    assert report.metrics()["slow_steps"] == 1


def test_api_retry_counters_fold_in_and_default_to_zero_when_untracked():
    report = l2.L2Report()
    report.add_retries(None)
    assert report.metrics()["api_retries"] == 0
    report.add_retries((2, 3.5))
    assert report.metrics() == {**report.metrics(), "api_retries": 2,
                                "api_retry_seconds": 3.5}


def test_the_summary_record_is_the_metrics_dict_and_carries_the_run_context():
    report = l2.L2Report(context={"record": "summary", "canticle": "inferno", "canto": 1})
    m = report.metrics()
    assert m["record"] == "summary" and m["canticle"] == "inferno" and m["canto"] == 1


def test_both_reporting_faces_render_and_show_the_gate_with_its_threshold():
    report = records(generate=StubGenerate())
    text = report.summary()
    assert "PASS" in text and "chunks: 3" in text and "tags:" in text
    assert isinstance(report.metrics(), dict)


def test_conflicts_reach_the_metrics_and_the_summary_line():
    report = l2.L2Report()
    report.add_chunk({
        "resolved": True, "lines": [6], "tokens": 1, "attempts": [],
        "conflicts": [{"word": "nel", "line": 6,
                       "first": {"parts": ["in", "il"], "pos": ["preposition", "article"]},
                       "here": {"parts": ["ne", "lo"], "pos": ["pronoun", "pronoun"]}}],
    })
    assert len(report.metrics()["conflicts"]) == 1
    assert "1 answered two ways" in report.summary()


def test_two_readings_reports_one_line_per_wordform_not_one_per_occurrence():
    """Printed per occurrence the readout was unreadable (`Inf` 1: 76 lines, four of them
    real) because a wordform read two ways reports itself again at every later occurrence.
    Grouped, each wordform says its whole story once, with counts."""
    report = l2.L2Report()
    pronoun = {"parts": ["che"], "pos": ["pronoun"]}
    conjunction = {"parts": ["che"], "pos": ["conjunction"]}
    for line in (7, 12, 13):
        report.add_chunk({
            "resolved": True, "lines": [line], "tokens": 1, "attempts": [],
            "conflicts": [{"word": "che", "line": line,
                           "first": pronoun, "here": conjunction}],
        })
    rows = report.two_readings()
    assert len(rows) == 1
    assert "che" in rows[0]
    assert "che (pronoun) x3" in rows[0] and "che (conjunction) x3" in rows[0]


# --- The prompt is a file, and it loads ------------------------------------------------------


def test_the_skill_loads_with_its_declared_resource():
    from dante_corpus.harness.skills import Skill

    skill = Skill.load(l2.SKILL_DIR)
    assert skill.name == "l2-words"
    assert "<table>" in skill.resource("answer.md")
    assert skill.digest()


def test_the_system_prompt_states_the_closed_tag_set_and_the_restoration_boundary():
    prompt = l2._system_prompt()
    for tag in l2.POS_TAGS:
        assert tag in prompt
    assert "dictionary form" in prompt
