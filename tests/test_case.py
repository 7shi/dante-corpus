"""Deterministic tests for the pronoun case annex (no model calls)."""

import pytest

from dante_corpus import api, case, hashes
from dante_corpus.morph import MorphRow

# Inferno I.2 — "mi ritrovai per una selva oscura,"
LINE2_MORPH = (
    MorphRow(word="mi", lemma="mi", pos="pronoun"),
    MorphRow(word="ritrovai", lemma="ritrovare", pos="verb"),
    MorphRow(word="per", lemma="per", pos="preposition"),
    MorphRow(word="una", lemma="uno", pos="article"),
    MorphRow(word="selva", lemma="selva", pos="noun"),
    MorphRow(word="oscura", lemma="oscuro", pos="adjective"),
)

SAMPLE_TABLE = """\
| Line | Word | Case |
|---|---|---|
| 2 | mi | accusative |
| 6 | che | nominative |
"""


def test_scope_slots_counts_pronoun_components():
    assert case.scope_slots("pronoun") == 1
    assert case.scope_slots("relative pronoun") == 1
    assert case.scope_slots("verb+pronoun") == 1
    assert case.scope_slots("verb + pronoun") == 1
    assert case.scope_slots("pronoun+pronoun") == 2
    assert case.scope_slots("verb+pronoun+pronoun") == 2
    assert case.scope_slots("noun") == 0
    assert case.scope_slots("") == 0


def test_targets_indexes_by_token_position():
    targets = case.targets(2, list(LINE2_MORPH))
    assert [(t.token, t.word, t.slots) for t in targets] == [(1, "mi", 1)]


def test_canon_case_normalizes_to_the_frozen_vocabulary():
    assert case.canon_case("Accusative") == "accusative"
    assert case.canon_case("dat.") == "dative"
    assert case.canon_case("**ablative**") == "ablative"
    # the pilot's near-synonyms for the partitive/locative class
    assert case.canon_case("oblique") == "ablative"
    assert case.canon_cell("dative + accusative") == "dative+accusative"
    # The two values added rather than measured — both name a pronoun that fills no slot
    # of the verb (case/CORRECTIONS.md: *vocative*, *Step 3 smoke test*).
    assert case.canon_case("voc.") == "vocative"
    assert case.canon_case("expletive") == "reflexive"
    assert case.canon_case("impersonal") == "reflexive"
    assert {"vocative", "reflexive"} <= set(case.CASES)
    # unknown values pass through so validate_line can report them
    assert case.canon_case("prepositional") == "prepositional"


def test_align_unit_matches_expected_positions():
    expected = [case.Target(2, 1, "mi", 1), case.Target(6, 1, "che", 1)]
    rows = case.align_unit(expected, SAMPLE_TABLE)
    assert [(r.line, r.token, r.word, r.case) for r in rows] == [
        (2, 1, "mi", "accusative"),
        (6, 1, "che", "nominative"),
    ]


def test_align_unit_leaves_unreached_positions_empty():
    expected = [case.Target(2, 1, "mi", 1), case.Target(6, 1, "che", 1),
                case.Target(9, 3, "lo", 1)]
    rows = case.align_unit(expected, SAMPLE_TABLE)
    assert rows[-1].case == ""


def test_align_unit_drops_rows_for_unmarked_words():
    noisy = SAMPLE_TABLE + "| 3 | via | nominative |\n"
    expected = [case.Target(2, 1, "mi", 1), case.Target(6, 1, "che", 1)]
    rows = case.align_unit(expected, noisy)
    assert [r.word for r in rows] == ["mi", "che"]


def test_align_unit_raises_without_table():
    with pytest.raises(ValueError):
        case.align_unit([case.Target(2, 1, "mi", 1)], "no table here")


def test_validate_line_accepts_a_correct_row():
    text = api.canto("inferno", 1).line(2).text
    rows = [case.CaseRow(2, 1, "mi", "accusative")]
    assert case.validate_line(2, text, LINE2_MORPH, rows) == []


def test_validate_line_flags_count_word_slot_and_tag():
    text = api.canto("inferno", 1).line(2).text
    kinds = lambda rows: {v.kind for v in case.validate_line(2, text, LINE2_MORPH, rows)}
    assert "count" in kinds([])  # the pronoun has no row
    assert "count" in kinds([case.CaseRow(2, 1, "mi", "accusative"),
                             case.CaseRow(2, 5, "selva", "nominative")])
    assert "word" in kinds([case.CaseRow(2, 1, "ti", "accusative")])
    assert "tag" in kinds([case.CaseRow(2, 1, "mi", "prepositional")])
    assert "tag" in kinds([case.CaseRow(2, 1, "mi", "")])
    fused = (MorphRow(word="gliel", lemma="gli+lo", pos="pronoun+pronoun"),)
    assert "slot" in {v.kind for v in
                      case.validate_line(1, "gliel", fused,
                                         [case.CaseRow(1, 1, "gliel", "dative")])}
    assert case.validate_line(1, "gliel", fused,
                              [case.CaseRow(1, 1, "gliel", "dative+accusative")]) == []


def test_validate_line_flags_out_of_order_rows():
    fake_morph = (MorphRow(word="e", pos="conjunction"),
                  MorphRow(word="io", pos="pronoun"),
                  MorphRow(word="a", pos="preposition"),
                  MorphRow(word="lui", pos="pronoun"))
    rows = [case.CaseRow(1, 4, "lui", "dative"), case.CaseRow(1, 2, "io", "nominative")]
    kinds = {v.kind for v in case.validate_line(1, "e io a lui", fake_morph, rows)}
    assert "count" in kinds


def test_write_load_round_trip(tmp_path, monkeypatch):
    monkeypatch.setattr(case, "CASE_DIR", tmp_path)
    monkeypatch.setattr(case, "_artifact_path",
                        lambda canticle, number: tmp_path / canticle / f"{number:02d}.tsv")
    rows = [case.CaseRow(2, 1, "mi", "accusative"),
            case.CaseRow(6, 1, "che", "nominative"),
            case.CaseRow(6, 4, "gliel", "dative+accusative")]
    case.write_case("inferno", 1, [(2, rows[:1]), (6, rows[1:])])
    assert case.has_case("inferno", 1)
    loaded = case.load_case("inferno", 1)
    assert loaded[2] == (rows[0],)
    assert loaded[6] == (rows[1], rows[2])
    assert loaded[6][1].cases() == ("dative", "accusative")
    # sparse: a line without a pronoun has no key at all
    assert 1 not in loaded


def test_case_index_is_position_keyed():
    data = {2: (case.CaseRow(2, 1, "mi", "accusative"),)}
    assert case.case_index(data) == {(2, 1): "accusative"}


def test_case_is_an_appended_hash_layer():
    # Appending must not reorder the existing layers — no existing artifact hash moves.
    assert hashes.LAYERS[:5] == ("text", "morph", "np", "dep", "skel")
    assert hashes.LAYERS[5] == "case"
    assert hashes.artifact_path("case", "inferno", 1).name == "01.tsv"
