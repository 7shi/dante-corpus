"""Deterministic tests for Layer 2 morphology parsing/alignment (no model calls)."""

from dante_corpus import api, morph

# A real word table for Inferno I.1-3 (from the dante-llm gptoss output).
SAMPLE_TABLE = """\
| Word | Lemma | Part of Speech | Gender | Number | Person | Tense | Mood | Note |
|---|---|---|---|---|---|---|---|---|
| Nel | in+il | preposition+article | m. | sg. | | | | contraction |
| mezzo | mezzo | noun | m. | sg. | | | | |
| del | di+il | preposition+article | m. | sg. | | | | contraction |
| cammin | cammino | noun | m. | sg. | | | | apocope |
| di | di | preposition | | | | | | |
| nostra | nostro | adjective | f. | sg. | | | | |
| vita | vita | noun | f. | sg. | | | | |
| mi | mi | pronoun | | sg. | 1 | | | reflexive |
| ritrovai | ritrovare | verb | | sg. | 1 | remote past | indicative | |
| per | per | preposition | | | | | | |
| una | uno | article | f. | sg. | | | | indefinite |
| selva | selva | noun | f. | sg. | | | | |
| oscura | oscuro | adjective | f. | sg. | | | | |
| ché | che | conjunction | | | | | | |
| la | la | article | f. | sg. | | | | |
| diritta | diritto | adjective | f. | sg. | | | | |
| via | via | noun | f. | sg. | | | | |
| era | essere | verb | | sg. | 3 | imperfect | indicative | |
| smarrita | smarrire | verb (past participle) | f. | sg. | | | | |
"""


def test_read_table_basic():
    table = morph.read_table(SAMPLE_TABLE)
    assert table is not None
    assert table[0][0] == "Word"
    assert "---" in table[1][0]
    assert table[2][0] == "Nel"


def test_read_table_rejects_non_table():
    assert morph.read_table("no table here\njust prose") is None


def test_fix_cell_normalizes():
    assert morph.fix_cell("number", "singular") == "sg."
    assert morph.fix_cell("gender", "Feminine") == "f."
    assert morph.fix_cell("person", "3rd") == "3"
    assert morph.fix_cell("note", "-") == ""
    assert morph.fix_cell("pos", "**noun**") == "noun"


def test_canon_header():
    assert morph.canon_header("Part of Speech") == "pos"
    assert morph.canon_header(" Lemma ") == "lemma"
    assert morph.canon_header("Reference Equivalent") is None


def test_align_chunk_round_trips_against_tokens():
    lines = api.canto("inferno", 1).lines(1, 3)
    nos = [line.no for line in lines]
    texts = [line.text for line in lines]
    aligned = morph.align_chunk(nos, texts, SAMPLE_TABLE)
    for line in lines:
        rows = aligned[line.no]
        assert tuple(r.word for r in rows) == line.tokens
        assert morph.validate_line(line.no, line.text, rows) == []
    # morphology actually landed on the right token
    assert aligned[2][1].lemma == "ritrovare"
    assert aligned[2][1].person == "1"


def test_align_chunk_raises_without_table():
    try:
        morph.align_chunk([1], ["x"], "not a table")
    except ValueError:
        return
    raise AssertionError("expected ValueError for unparseable table")


def test_validate_line_flags_count_and_word():
    rows = [morph.MorphRow(word="Nel"), morph.MorphRow(word="WRONG")]
    violations = morph.validate_line(1, "Nel mezzo del", rows)
    kinds = {v.kind for v in violations}
    assert "count" in kinds  # 2 rows vs 3 tokens
    assert "word" in kinds   # WRONG != mezzo


def test_validate_line_flags_closed_tag():
    rows = [morph.MorphRow(word="Nel", gender="masc")]
    violations = morph.validate_line(1, "Nel", rows)
    assert any(v.kind == "tag" for v in violations)


def test_split_table_salvages_transformed_word():
    # Second word hallucinated/transformed so it is not found in the source; the aligner
    # must salvage it to the previous line rather than dropping it.
    line_texts = ["uno due", "tre quattro"]
    table = [
        ["Word"],
        ["---"],
        ["uno"],
        ["XX"],
        ["tre"],
        ["quattro"],
    ]
    buckets = morph.split_table(line_texts, table)
    assert [row[0] for row in buckets[0]] == ["uno", "XX"]
    assert [row[0] for row in buckets[1]] == ["tre", "quattro"]


def test_fix_aligned_words_trailing_punct():
    rows = [morph.MorphRow(word="sono,"), morph.MorphRow(word="oscura,")]
    result, errors = morph.fix_aligned_words([1], ["sono oscura"], {1: rows})
    assert errors == []
    assert [r.word for r in result[1]] == ["sono", "oscura"]


def test_fix_aligned_words_apostrophe_cases():
    cases = {
        1: ([morph.MorphRow(word="I")],      "I'"),      # missing trailing '
        2: ([morph.MorphRow(word="nvidia")],  "'nvidia"), # missing leading '
        3: ([morph.MorphRow(word="'el")],    "el"),      # excess leading '
        4: ([morph.MorphRow(word="el'")],    "el"),      # excess trailing '
    }
    nos = list(cases)
    texts = [cases[n][1] for n in nos]
    aligned = {n: cases[n][0] for n in nos}
    result, errors = morph.fix_aligned_words(nos, texts, aligned)
    assert errors == []
    assert result[1][0].word == "I'"
    assert result[2][0].word == "'nvidia"
    assert result[3][0].word == "el"
    assert result[4][0].word == "el"


def test_fix_aligned_words_unfixable_mismatch():
    rows = [morph.MorphRow(word="wrong")]
    result, errors = morph.fix_aligned_words([1], ["right"], {1: rows})
    assert errors != []
    assert result[1][0].word == "wrong"  # unchanged


def test_fix_aligned_words_count_mismatch_passthrough():
    rows = [morph.MorphRow(word="a"), morph.MorphRow(word="b")]
    result, errors = morph.fix_aligned_words([1], ["solo"], {1: rows})
    assert errors == []  # count mismatch lines are skipped, not errored
    assert result[1] == rows  # unchanged


def test_write_load_round_trip(tmp_path, monkeypatch):
    monkeypatch.setattr(morph, "MORPH_DIR", tmp_path)
    rows = [morph.MorphRow(word="Nel", lemma="in+il", pos="preposition+article",
                           gender="m.", number="sg.", note="contraction"),
            morph.MorphRow(word="mezzo", lemma="mezzo", pos="noun", gender="m.", number="sg.")]
    morph.write_morph("inferno", 1, [(1, rows)])
    assert morph.has_morph("inferno", 1)
    loaded = morph.load_morph("inferno", 1)
    assert loaded[1] == tuple(rows)
