"""Deterministic tests for Layer 4 dependency parsing/resolution (no model calls)."""

from dante_corpus import api, dep

# Dependencies for Inferno I.1-3, matching PLAN.md's worked example (and dep/dep.py's system
# prompt). Head Line/Head Token are the authoritative citation; Head Word is a verification
# anchor only.
SAMPLE_TABLE = """\
| Line | Token | Word | Deprel | Head Line | Head Token | Head Word |
|---|---|---|---|---|---|---|
| 1 | 1 | Nel | case | 1 | 2 | mezzo |
| 1 | 2 | mezzo | obl | 2 | 2 | ritrovai |
| 1 | 3 | del | case | 1 | 4 | cammin |
| 1 | 4 | cammin | nmod | 1 | 2 | mezzo |
| 1 | 5 | di | case | 1 | 7 | vita |
| 1 | 6 | nostra | det:poss | 1 | 7 | vita |
| 1 | 7 | vita | nmod | 1 | 4 | cammin |
| 2 | 1 | mi | expl | 2 | 2 | ritrovai |
| 2 | 2 | ritrovai | root | 0 | 0 | - |
| 2 | 3 | per | case | 2 | 5 | selva |
| 2 | 4 | una | det | 2 | 5 | selva |
| 2 | 5 | selva | obl | 2 | 2 | ritrovai |
| 2 | 6 | oscura | amod | 2 | 5 | selva |
| 3 | 1 | ché | mark | 3 | 6 | smarrita |
| 3 | 2 | la | det | 3 | 4 | via |
| 3 | 3 | diritta | amod | 3 | 4 | via |
| 3 | 4 | via | nsubj | 3 | 6 | smarrita |
| 3 | 5 | era | aux | 3 | 6 | smarrita |
| 3 | 6 | smarrita | advcl | 2 | 2 | ritrovai |
"""


def _lines(start, end):
    lines = api.canto("inferno", 1).lines(start, end)
    return [line.no for line in lines], [line.text for line in lines]


# --- sentence_groups -----------------------------------------------------------------


def test_sentence_groups_basic():
    nos, texts = _lines(1, 9)
    assert dep.sentence_groups(nos, texts) == [[1, 2, 3], [4, 5, 6], [7, 8, 9]]


def test_sentence_groups_embedded_quote_no_break():
    texts = [
        'udì «Dolce Maria!»',
        "e poi continuò a parlare",
        "fino alla fine.",
    ]
    nos = [1, 2, 3]
    assert dep.sentence_groups(nos, texts) == [[1, 2, 3]]


def test_sentence_groups_flushes_final_group_without_terminal():
    nos, texts = [1, 2], ["riga senza punto", "altra riga"]
    assert dep.sentence_groups(nos, texts) == [[1, 2]]


def test_sentence_groups_cap_splits_at_soft_break():
    # 15 synthetic lines, no terminal punctuation until the very end, with a ';' at line 6.
    texts = ["riga" for _ in range(14)] + ["fine."]
    texts[5] = "riga;"
    nos = list(range(1, 16))
    groups = dep.sentence_groups(nos, texts, max_lines=12)
    assert groups == [[1, 2, 3, 4, 5, 6], [7, 8, 9, 10, 11, 12, 13, 14, 15]]


def test_sentence_groups_cap_hard_splits_without_soft_break():
    texts = ["riga" for _ in range(13)] + ["fine."]
    nos = list(range(1, 15))
    groups = dep.sentence_groups(nos, texts, max_lines=12)
    assert groups == [list(range(1, 13)), list(range(13, 15))]


# --- canon_header ----------------------------------------------------------------------


def test_canon_header():
    assert dep.canon_header("Head Line") == "head_line"
    assert dep.canon_header(" Deprel ") == "deprel"
    assert dep.canon_header("Relation") == "deprel"
    assert dep.canon_header("Reference Equivalent") is None


# --- resolve_chunk / validate_unit round trip -------------------------------------------


def test_resolve_chunk_round_trip():
    nos, texts = _lines(1, 3)
    rows_by_line, mismatches = dep.resolve_chunk(nos, texts, SAMPLE_TABLE)
    assert mismatches == []
    for no in nos:
        assert len(rows_by_line[no]) == len(api.canto("inferno", 1).line(no).tokens)
    root = rows_by_line[2][1]
    assert root.deprel == "root" and root.head_line == 0 and root.head_token == 0
    via = rows_by_line[3][3]  # token 4 = "via"
    assert via.word == "via" and via.deprel == "nsubj" and (via.head_line, via.head_token) == (3, 6)
    smarrita = rows_by_line[3][5]  # token 6 = "smarrita", cross-line head
    assert (smarrita.head_line, smarrita.head_token) == (2, 2)
    assert dep.validate_unit(nos, texts, rows_by_line) == []


def test_resolve_chunk_raises_without_table():
    try:
        dep.resolve_chunk([1], ["x"], "not a table")
    except ValueError:
        return
    raise AssertionError("expected ValueError for unparseable table")


def test_resolve_chunk_flags_head_word_mismatch():
    table = SAMPLE_TABLE.replace(
        "| 3 | 4 | via | nsubj | 3 | 6 | smarrita |",
        "| 3 | 4 | via | nsubj | 3 | 6 | WRONG |",
    )
    nos, texts = _lines(1, 3)
    _, mismatches = dep.resolve_chunk(nos, texts, table)
    assert len(mismatches) == 1
    assert "3.4" in mismatches[0] and "WRONG" in mismatches[0]


# --- validate_unit: hard checks ---------------------------------------------------------


def _unit(rows):
    """Group DepRows by line for validate_unit's rows_by_line argument."""
    by_line: dict[int, list[dep.DepRow]] = {}
    for row in rows:
        by_line.setdefault(row.line, []).append(row)
    return by_line


def test_validate_unit_flags_count():
    nos, texts = [1], ["Nel mezzo del"]
    rows = [dep.DepRow(1, 1, "Nel", "case", 1, 2)]  # only 1 row for 3 tokens
    violations = dep.validate_unit(nos, texts, _unit(rows))
    assert any(v.kind == "count" for v in violations)


def test_validate_unit_flags_word():
    nos, texts = [1], ["Nel mezzo"]
    rows = [
        dep.DepRow(1, 1, "Nel", "case", 1, 2),
        dep.DepRow(1, 2, "WRONG", "root", 0, 0),
    ]
    violations = dep.validate_unit(nos, texts, _unit(rows))
    assert any(v.kind == "word" for v in violations)


def test_validate_unit_flags_out_of_unit_head():
    nos, texts = [1], ["Nel mezzo"]
    rows = [
        dep.DepRow(1, 1, "Nel", "case", 5, 9),  # no line 5 in this unit
        dep.DepRow(1, 2, "mezzo", "root", 0, 0),
    ]
    violations = dep.validate_unit(nos, texts, _unit(rows))
    assert any(v.kind == "head" for v in violations)


def test_validate_unit_flags_self_head():
    nos, texts = [1], ["Nel mezzo"]
    rows = [
        dep.DepRow(1, 1, "Nel", "case", 1, 1),  # points at itself
        dep.DepRow(1, 2, "mezzo", "root", 0, 0),
    ]
    violations = dep.validate_unit(nos, texts, _unit(rows))
    assert any(v.kind == "head" for v in violations)


def test_validate_unit_flags_root_deprel_head_inconsistency():
    nos, texts = [1], ["Nel mezzo"]
    rows = [
        dep.DepRow(1, 1, "Nel", "case", 1, 2),
        dep.DepRow(1, 2, "mezzo", "nsubj", 0, 0),  # head 0 but not deprel root
    ]
    violations = dep.validate_unit(nos, texts, _unit(rows))
    assert any(v.kind == "head" for v in violations)


def test_validate_unit_flags_cycle():
    nos, texts = [1], ["uno due"]
    rows = [
        dep.DepRow(1, 1, "uno", "conj", 1, 2),
        dep.DepRow(1, 2, "due", "conj", 1, 1),  # 1<->2 cycle, no root at all
    ]
    violations = dep.validate_unit(nos, texts, _unit(rows))
    kinds = {v.kind for v in violations}
    assert "cycle" in kinds
    assert "root" in kinds  # no root reached either


def test_validate_unit_flags_missing_root():
    nos, texts = [1], ["Nel"]
    rows = [dep.DepRow(1, 1, "Nel", "case", 1, 1)]  # self-head, no root anywhere
    violations = dep.validate_unit(nos, texts, _unit(rows))
    assert any(v.kind == "root" for v in violations)


# --- validate_unit: soft checks ---------------------------------------------------------


def test_validate_unit_flags_unknown_deprel():
    nos, texts = [1], ["Nel mezzo"]
    rows = [
        dep.DepRow(1, 1, "Nel", "bogus", 1, 2),
        dep.DepRow(1, 2, "mezzo", "root", 0, 0),
    ]
    violations = dep.validate_unit(nos, texts, _unit(rows))
    assert any(v.kind == "tag" and "bogus" in v.detail for v in violations)


def test_validate_unit_flags_multiple_roots_as_soft():
    nos, texts = [1], ["uno due"]
    rows = [
        dep.DepRow(1, 1, "uno", "root", 0, 0),
        dep.DepRow(1, 2, "due", "root", 0, 0),
    ]
    violations = dep.validate_unit(nos, texts, _unit(rows))
    assert any(v.kind == "tag" and "root" in v.detail for v in violations)
    assert not any(v.kind in ("count", "word", "head", "cycle") for v in violations)


def test_validate_unit_flags_non_nominal_relcl_head():
    from dante_corpus.morph import MorphRow

    nos, texts = [1], ["che corre"]
    rows = [
        dep.DepRow(1, 1, "che", "nsubj", 1, 2),
        dep.DepRow(1, 2, "corre", "acl:relcl", 1, 1),  # head "che" is a pronoun: fine
    ]
    morph_rows = {1: [MorphRow(word="che", pos="conjunction"), MorphRow(word="corre", pos="verb")]}
    violations = dep.validate_unit(nos, texts, _unit(rows), morph_rows=morph_rows)
    assert any(v.kind == "tag" and "acl:relcl" in v.detail for v in violations)


def test_validate_unit_accepts_nominal_relcl_head():
    from dante_corpus.morph import MorphRow

    nos, texts = [1], ["via che corre"]
    rows = [
        dep.DepRow(1, 1, "via", "root", 0, 0),
        dep.DepRow(1, 2, "che", "nsubj", 1, 3),
        dep.DepRow(1, 3, "corre", "acl:relcl", 1, 1),  # head "via" is a noun: fine
    ]
    morph_rows = {
        1: [
            MorphRow(word="via", pos="noun"),
            MorphRow(word="che", pos="pronoun"),
            MorphRow(word="corre", pos="verb"),
        ]
    }
    violations = dep.validate_unit(nos, texts, _unit(rows), morph_rows=morph_rows)
    assert not any(v.kind == "tag" and "acl:relcl" in v.detail for v in violations)


# --- index / np_role ---------------------------------------------------------------------


def test_index_and_np_role():
    from dante_corpus.np import NPSpan

    data = {3: (
        dep.DepRow(3, 2, "la", "det", 3, 4),
        dep.DepRow(3, 3, "diritta", "amod", 3, 4),
        dep.DepRow(3, 4, "via", "nsubj", 3, 6),
    )}
    idx = dep.index(data)
    span = NPSpan(line=3, start=2, end=4, head=4, text="la diritta via")
    assert dep.np_role(span, idx) == "nsubj"

    missing = NPSpan(line=9, start=1, end=1, head=1, text="x")
    assert dep.np_role(missing, idx) == ""


# --- artifact I/O --------------------------------------------------------------------------


def test_write_load_round_trip(tmp_path, monkeypatch):
    monkeypatch.setattr(dep, "DEP_DIR", tmp_path)
    rows = [
        dep.DepRow(1, 1, "Nel", "case", 1, 2),
        dep.DepRow(1, 2, "mezzo", "root", 0, 0),
    ]
    dep.write_dep("inferno", 1, [(1, rows)])
    assert dep.has_dep("inferno", 1)
    loaded = dep.load_dep("inferno", 1)
    assert loaded[1] == tuple(rows)


def test_validate_unit_flags_two_obj_children_as_soft():
    nos, texts = [1], ["vide Isara ed Era"]
    rows = [
        dep.DepRow(1, 1, "vide", "root", 0, 0),
        dep.DepRow(1, 2, "Isara", "obj", 1, 1),
        dep.DepRow(1, 3, "ed", "cc", 1, 4),
        dep.DepRow(1, 4, "Era", "obj", 1, 1),  # flattened coordination: two obj on one predicate
    ]
    violations = dep.validate_unit(nos, texts, _unit(rows))
    tags = [v for v in violations if v.kind == "tag" and "obj children" in v.detail]
    assert len(tags) == 1
    assert "1.2 'Isara'" in tags[0].detail and "1.4 'Era'" in tags[0].detail
    assert not any(v.kind in ("count", "word", "head", "cycle", "root") for v in violations)


def test_validate_unit_accepts_coordinated_obj_as_conj():
    nos, texts = [1], ["vide Isara ed Era"]
    rows = [
        dep.DepRow(1, 1, "vide", "root", 0, 0),
        dep.DepRow(1, 2, "Isara", "obj", 1, 1),
        dep.DepRow(1, 3, "ed", "cc", 1, 4),
        dep.DepRow(1, 4, "Era", "conj", 1, 2),  # UD shape: later conjunct hangs off the first
    ]
    violations = dep.validate_unit(nos, texts, _unit(rows))
    assert not any("obj children" in v.detail for v in violations)


def test_validate_unit_counts_obj_children_per_predicate():
    nos, texts = [1], ["vide Isara ed Era vide Senna"]
    rows = [
        dep.DepRow(1, 1, "vide", "root", 0, 0),
        dep.DepRow(1, 2, "Isara", "obj", 1, 1),
        dep.DepRow(1, 3, "ed", "cc", 1, 4),
        dep.DepRow(1, 4, "Era", "conj", 1, 2),
        dep.DepRow(1, 5, "vide", "conj", 1, 1),
        dep.DepRow(1, 6, "Senna", "obj", 1, 5),  # a second predicate's own single obj is fine
    ]
    violations = dep.validate_unit(nos, texts, _unit(rows))
    assert not any("obj children" in v.detail for v in violations)


# --- subject agreement (Layer 2-aware soft check) ------------------------------------


def _agreement(nos, texts, rows, morph_rows):
    violations = dep.validate_unit(nos, texts, _unit(rows), morph_rows=morph_rows)
    return [v for v in violations if "disagrees with head" in v.detail]


def test_validate_unit_flags_subject_person_disagreement():
    from dante_corpus.morph import MorphRow

    nos, texts = [1], ["rui Anfïarao"]
    rows = [
        dep.DepRow(1, 1, "rui", "root", 0, 0),
        dep.DepRow(1, 2, "Anfïarao", "nsubj", 1, 1),  # a vocative, not the 2sg verb's subject
    ]
    morph_rows = {
        1: [
            MorphRow(word="rui", lemma="ruere", pos="verb", number="sg.", person="2",
                     tense="present", mood="indicative"),
            MorphRow(word="Anfïarao", lemma="Anfiarao", pos="proper noun", number="sg."),
        ]
    }
    flagged = _agreement(nos, texts, rows, morph_rows)
    assert len(flagged) == 1
    assert "person 3 vs 2" in flagged[0].detail


def test_validate_unit_flags_subject_number_disagreement():
    from dante_corpus.morph import MorphRow

    nos, texts = [1], ["altri guidi"]
    rows = [
        dep.DepRow(1, 1, "altri", "nsubj", 1, 2),
        dep.DepRow(1, 2, "guidi", "root", 0, 0),
    ]
    morph_rows = {
        1: [
            MorphRow(word="altri", lemma="altri", pos="pronoun", number="pl."),
            MorphRow(word="guidi", lemma="guidare", pos="verb", number="sg.", person="3"),
        ]
    }
    flagged = _agreement(nos, texts, rows, morph_rows)
    assert len(flagged) == 1
    assert "number pl. vs sg." in flagged[0].detail


def test_validate_unit_accepts_agreeing_subject():
    from dante_corpus.morph import MorphRow

    nos, texts = [1], ["via corre"]
    rows = [
        dep.DepRow(1, 1, "via", "nsubj", 1, 2),
        dep.DepRow(1, 2, "corre", "root", 0, 0),
    ]
    morph_rows = {
        1: [
            MorphRow(word="via", lemma="via", pos="noun", number="sg."),
            MorphRow(word="corre", lemma="correre", pos="verb", number="sg.", person="3"),
        ]
    }
    assert _agreement(nos, texts, rows, morph_rows) == []


def test_validate_unit_skips_relative_pronoun_subject():
    from dante_corpus.morph import MorphRow

    nos, texts = [1], ["tu che onori"]
    rows = [
        dep.DepRow(1, 1, "tu", "root", 0, 0),
        dep.DepRow(1, 2, "che", "nsubj", 1, 3),  # person comes from the antecedent "tu"
        dep.DepRow(1, 3, "onori", "acl:relcl", 1, 1),
    ]
    morph_rows = {
        1: [
            MorphRow(word="tu", lemma="tu", pos="pronoun", number="sg.", person="2"),
            MorphRow(word="che", lemma="che", pos="relative pronoun", number="sg."),
            MorphRow(word="onori", lemma="onorare", pos="verb", number="sg.", person="2"),
        ]
    }
    assert _agreement(nos, texts, rows, morph_rows) == []


def test_validate_unit_skips_coordinated_subject():
    from dante_corpus.morph import MorphRow

    nos, texts = [1], ["superbia e invidia sono"]
    rows = [
        dep.DepRow(1, 1, "superbia", "nsubj", 1, 4),
        dep.DepRow(1, 2, "e", "cc", 1, 3),
        dep.DepRow(1, 3, "invidia", "conj", 1, 1),  # coordination agrees as a whole
        dep.DepRow(1, 4, "sono", "root", 0, 0),
    ]
    morph_rows = {
        1: [
            MorphRow(word="superbia", lemma="superbia", pos="noun", number="sg."),
            MorphRow(word="e", lemma="e", pos="conjunction"),
            MorphRow(word="invidia", lemma="invidia", pos="noun", number="sg."),
            MorphRow(word="sono", lemma="essere", pos="verb", number="pl.", person="3"),
        ]
    }
    assert _agreement(nos, texts, rows, morph_rows) == []


def test_validate_unit_skips_fused_non_finite_token():
    from dante_corpus.morph import MorphRow

    nos, texts = [1], ["è aprirmi"]
    rows = [
        dep.DepRow(1, 1, "è", "root", 0, 0),
        dep.DepRow(1, 2, "aprirmi", "nsubj", 1, 1),  # 1sg is the enclitic *mi*, not the verb
    ]
    morph_rows = {
        1: [
            MorphRow(word="è", lemma="essere", pos="verb", number="sg.", person="3",
                     tense="present", mood="indicative"),
            MorphRow(word="aprirmi", lemma="aprire+mi", pos="verb+pronoun", number="sg.",
                     person="1"),
        ]
    }
    assert _agreement(nos, texts, rows, morph_rows) == []


def test_validate_unit_skips_inclusive_plural_head():
    from dante_corpus.morph import MorphRow

    nos, texts = [1], ["amendue mostravam"]
    rows = [
        dep.DepRow(1, 1, "amendue", "nsubj", 1, 2),  # "both of us": one member names the group
        dep.DepRow(1, 2, "mostravam", "root", 0, 0),
    ]
    morph_rows = {
        1: [
            MorphRow(word="amendue", lemma="amendue", pos="pronoun", number="pl."),
            MorphRow(word="mostravam", lemma="mostrare", pos="verb", number="pl.", person="1",
                     tense="imperfect", mood="indicative"),
        ]
    }
    assert _agreement(nos, texts, rows, morph_rows) == []


def test_validate_unit_skips_non_verb_head():
    from dante_corpus.morph import MorphRow

    nos, texts = [1], ["nome fu vosco"]
    rows = [
        dep.DepRow(1, 1, "nome", "nsubj", 1, 3),  # copular clause: the predicate heads it
        dep.DepRow(1, 2, "fu", "cop", 1, 3),
        dep.DepRow(1, 3, "vosco", "root", 0, 0),
    ]
    morph_rows = {
        1: [
            MorphRow(word="nome", lemma="nome", pos="noun", number="sg."),
            MorphRow(word="fu", lemma="essere", pos="verb", number="sg.", person="3",
                     tense="remote past", mood="indicative"),
            MorphRow(word="vosco", lemma="voi+con", pos="pronoun+preposition", number="pl.",
                     person="2"),
        ]
    }
    assert _agreement(nos, texts, rows, morph_rows) == []


def test_validate_unit_skips_non_finite_head():
    from dante_corpus.morph import MorphRow

    nos, texts = [1], ["altri andare"]
    rows = [
        dep.DepRow(1, 1, "altri", "nsubj", 1, 2),
        dep.DepRow(1, 2, "andare", "root", 0, 0),  # infinitive asserts no person/number
    ]
    morph_rows = {
        1: [
            MorphRow(word="altri", lemma="altri", pos="pronoun", number="pl."),
            MorphRow(word="andare", lemma="andare", pos="verb", mood="infinitive"),
        ]
    }
    assert _agreement(nos, texts, rows, morph_rows) == []


# --- the exclusions that closed the rule's 18-position residue (2026-08-14) ------------


def test_validate_unit_skips_flagged_ad_sensum_subject():
    from dante_corpus.morph import MorphRow

    nos, texts = [1], ["la gente si parton"]
    rows = [
        dep.DepRow(1, 1, "la", "det", 1, 2),
        dep.DepRow(1, 2, "gente", "nsubj", 1, 4),
        dep.DepRow(1, 3, "si", "expl", 1, 4),
        dep.DepRow(1, 4, "parton", "root", 0, 0),
    ]

    def morph(note: str) -> dict:
        return {
            1: [
                MorphRow(word="la", lemma="lo", pos="article", number="sg."),
                MorphRow(word="gente", lemma="gente", pos="noun", number="sg.", note=note),
                MorphRow(word="si", lemma="si", pos="pronoun", number="pl."),
                MorphRow(word="parton", lemma="partire", pos="verb", number="pl.", person="3",
                         tense="present", mood="indicative"),
            ]
        }

    # The flag is a hand-verified per-row exemption, not a blanket rule for the word.
    assert _agreement(nos, texts, rows, morph("AD_SENSUM")) == []
    assert len(_agreement(nos, texts, rows, morph(""))) == 1


def test_validate_unit_skips_foreign_flagged_token():
    from dante_corpus.morph import MorphRow

    nos, texts = [1], ["Raphel zabi"]
    rows = [
        dep.DepRow(1, 1, "Raphel", "nsubj", 1, 2),
        dep.DepRow(1, 2, "zabi", "root", 0, 0),
    ]
    morph_rows = {
        1: [
            MorphRow(word="Raphel", lemma="Raphel", pos="noun", number="sg.",
                     note="proper noun, FOREIGN"),
            MorphRow(word="zabi", lemma="sapere", pos="verb", number="sg.", person="2",
                     tense="present", mood="indicative", note="distortion, FOREIGN"),
        ]
    }
    assert _agreement(nos, texts, rows, morph_rows) == []


def test_validate_unit_skips_distributive_subject():
    from dante_corpus.morph import MorphRow

    nos, texts = [1], ["vanno ciascuna"]
    rows = [
        dep.DepRow(1, 1, "vanno", "root", 0, 0),
        dep.DepRow(1, 2, "ciascuna", "nsubj", 1, 1),  # resumes the plural one member at a time
    ]
    morph_rows = {
        1: [
            MorphRow(word="vanno", lemma="andare", pos="verb", number="pl.", person="3",
                     tense="present", mood="indicative"),
            MorphRow(word="ciascuna", lemma="ciascuno", pos="pronoun", number="sg."),
        ]
    }
    assert _agreement(nos, texts, rows, morph_rows) == []


def test_validate_unit_skips_phrase_internal_coordination():
    from dante_corpus.morph import MorphRow

    nos, texts = [1], ["uno e altro coro parver"]
    rows = [
        dep.DepRow(1, 1, "uno", "nmod", 1, 4),
        dep.DepRow(1, 2, "e", "cc", 1, 4),
        dep.DepRow(1, 3, "altro", "nmod", 1, 4),
        dep.DepRow(1, 4, "coro", "nsubj", 1, 5),  # one noun, two coordinated choirs
        dep.DepRow(1, 5, "parver", "root", 0, 0),
    ]
    morph_rows = {
        1: [
            MorphRow(word="uno", lemma="uno", pos="numeral", number="sg."),
            MorphRow(word="e", lemma="e", pos="conjunction"),
            MorphRow(word="altro", lemma="altro", pos="adjective", number="sg."),
            MorphRow(word="coro", lemma="coro", pos="noun", number="sg."),
            MorphRow(word="parver", lemma="parere", pos="verb", number="pl.", person="3",
                     tense="remote past", mood="indicative"),
        ]
    }
    assert _agreement(nos, texts, rows, morph_rows) == []


def test_validate_unit_skips_comitative_plural_head():
    from dante_corpus.morph import MorphRow

    nos, texts = [1], ["necesse con contingente fenno"]
    rows = [
        dep.DepRow(1, 1, "necesse", "nsubj", 1, 4),
        dep.DepRow(1, 2, "con", "case", 1, 3),
        dep.DepRow(1, 3, "contingente", "obl", 1, 4),
        dep.DepRow(1, 4, "fenno", "root", 0, 0),
    ]
    morph_rows = {
        1: [
            MorphRow(word="necesse", lemma="necessario", pos="noun", number="sg."),
            MorphRow(word="con", lemma="con", pos="preposition"),
            MorphRow(word="contingente", lemma="contingente", pos="noun", number="sg."),
            MorphRow(word="fenno", lemma="fare", pos="verb", number="pl.", person="3",
                     tense="remote past", mood="indicative"),
        ]
    }
    assert _agreement(nos, texts, rows, morph_rows) == []
    # Without the comitative phrase the same pair stays in scope.
    bare = [dep.DepRow(1, 1, "necesse", "nsubj", 1, 2),
            dep.DepRow(1, 2, "fenno", "root", 0, 0)]
    bare_morph = {1: [morph_rows[1][0], morph_rows[1][3]]}
    assert len(_agreement([1], ["necesse fenno"], bare, bare_morph)) == 1


def test_validate_unit_skips_quantified_measure_subject():
    from dante_corpus.morph import MorphRow

    nos, texts = [1], ["cento miglia sazia"]
    rows = [
        dep.DepRow(1, 1, "cento", "nummod", 1, 2),
        dep.DepRow(1, 2, "miglia", "nsubj", 1, 3),  # a hundred miles, read as one measure
        dep.DepRow(1, 3, "sazia", "root", 0, 0),
    ]
    morph_rows = {
        1: [
            MorphRow(word="cento", lemma="cento", pos="numeral"),
            MorphRow(word="miglia", lemma="miglio", pos="noun", number="pl."),
            MorphRow(word="sazia", lemma="saziare", pos="verb", number="sg.", person="3",
                     tense="present", mood="indicative"),
        ]
    }
    assert _agreement(nos, texts, rows, morph_rows) == []


def test_validate_unit_skips_copula_agreeing_with_predicate_nominal():
    from dante_corpus.morph import MorphRow

    nos, texts = [1], ["la prova son le opere"]
    rows = [
        dep.DepRow(1, 1, "la", "det", 1, 2),
        dep.DepRow(1, 2, "prova", "nsubj", 1, 3),
        dep.DepRow(1, 3, "son", "root", 0, 0),
        dep.DepRow(1, 4, "le", "det", 1, 5),
        dep.DepRow(1, 5, "opere", "attr", 1, 3),  # the verb agrees with its complement
    ]
    morph_rows = {
        1: [
            MorphRow(word="la", lemma="lo", pos="article", number="sg."),
            MorphRow(word="prova", lemma="prova", pos="noun", number="sg."),
            MorphRow(word="son", lemma="essere", pos="verb", number="pl.", person="3",
                     tense="present", mood="indicative"),
            MorphRow(word="le", lemma="lo", pos="article", number="pl."),
            MorphRow(word="opere", lemma="opera", pos="noun", number="pl."),
        ]
    }
    assert _agreement(nos, texts, rows, morph_rows) == []


def test_validate_unit_skips_impersonal_si_with_postposed_subject():
    from dante_corpus.morph import MorphRow

    nos, texts = [1], ["non si convenia salmi"]
    rows = [
        dep.DepRow(1, 1, "non", "advmod", 1, 3),
        dep.DepRow(1, 2, "si", "expl", 1, 3),
        dep.DepRow(1, 3, "convenia", "root", 0, 0),
        dep.DepRow(1, 4, "salmi", "nsubj", 1, 3),
    ]
    morph_rows = {
        1: [
            MorphRow(word="non", lemma="non", pos="adverb"),
            MorphRow(word="si", lemma="si", pos="pronoun", number="sg.", note="impersonal"),
            MorphRow(word="convenia", lemma="convenire", pos="verb", number="sg.", person="3",
                     tense="imperfect", mood="indicative"),
            MorphRow(word="salmi", lemma="salmo", pos="noun", number="pl."),
        ]
    }
    assert _agreement(nos, texts, rows, morph_rows) == []


def test_validate_unit_accepts_coordinated_subject_agreeing_with_one_conjunct():
    """"Tosto che 'l duca e io nel legno fui" (inferno 8:28): Italian lets a finite verb agree
    with one member of a coordinated subject, in either direction, so the person test is
    satisfied by any conjunct."""
    from dante_corpus.morph import MorphRow

    nos, texts = [1], ["'l duca e io fui"]
    rows = [
        dep.DepRow(1, 1, "duca", "nsubj", 1, 4),
        dep.DepRow(1, 2, "e", "cc", 1, 3),
        dep.DepRow(1, 3, "io", "conj", 1, 1),
        dep.DepRow(1, 4, "fui", "root", 0, 0),
    ]
    morph_rows = {
        1: [
            MorphRow(word="duca", lemma="duca", pos="noun", number="sg."),
            MorphRow(word="e", lemma="e", pos="conjunction"),
            MorphRow(word="io", lemma="io", pos="pronoun", number="sg.", person="1"),
            MorphRow(word="fui", lemma="essere", pos="verb", number="sg.", person="1"),
        ]
    }
    assert _agreement(nos, texts, rows, morph_rows) == []


def test_validate_unit_reports_a_coordination_no_conjunct_of_which_agrees():
    """A coordination has a person even though it has no fixed number: when *no* member carries
    the head's person, the attachment is a real question."""
    from dante_corpus.morph import MorphRow

    nos, texts = [1], ["'l duca e Virgilio fui"]
    rows = [
        dep.DepRow(1, 1, "duca", "nsubj", 1, 4),
        dep.DepRow(1, 2, "e", "cc", 1, 3),
        dep.DepRow(1, 3, "Virgilio", "conj", 1, 1),
        dep.DepRow(1, 4, "fui", "root", 0, 0),
    ]
    morph_rows = {
        1: [
            MorphRow(word="duca", lemma="duca", pos="noun", number="sg."),
            MorphRow(word="e", lemma="e", pos="conjunction"),
            MorphRow(word="Virgilio", lemma="Virgilio", pos="noun", number="sg."),
            MorphRow(word="fui", lemma="essere", pos="verb", number="sg.", person="1"),
        ]
    }
    assert [v.detail for v in _agreement(nos, texts, rows, morph_rows)] == [
        "nsubj 1.1 'duca' disagrees with head 1.4 'fui': person 3 vs 1"
    ]


def test_validate_unit_reports_a_third_person_subject_under_a_first_plural_head():
    """Rule CR: the "1/2 plural head admits a singular member" exclusion covers the *number*
    test, not the person one. "Ciò ch'io dicea … contrario suon **prendemo**" (purgatorio
    20:102): `Ciò` is the subject of the first conjunct, and no "we" has a lone third person in
    it."""
    from dante_corpus.morph import MorphRow

    nos, texts = [1], ["Ciò prendemo"]
    rows = [
        dep.DepRow(1, 1, "Ciò", "nsubj", 1, 2),
        dep.DepRow(1, 2, "prendemo", "root", 0, 0),
    ]
    morph_rows = {
        1: [
            MorphRow(word="Ciò", lemma="ciò", pos="pronoun", number="sg."),
            MorphRow(word="prendemo", lemma="prendere", pos="verb", number="pl.", person="1"),
        ]
    }
    assert [v.detail for v in _agreement(nos, texts, rows, morph_rows)] == [
        "nsubj 1.1 'Ciò' disagrees with head 1.2 'prendemo': person 3 vs 1"
    ]


def test_validate_unit_accepts_a_first_person_singular_under_a_first_plural_head():
    """The exclusion still stands for a subject that *could* be one member of the plural — the
    reduced "io [e tu] andiamo" the rule was written for."""
    from dante_corpus.morph import MorphRow

    nos, texts = [1], ["io andiamo"]
    rows = [
        dep.DepRow(1, 1, "io", "nsubj", 1, 2),
        dep.DepRow(1, 2, "andiamo", "root", 0, 0),
    ]
    morph_rows = {
        1: [
            MorphRow(word="io", lemma="io", pos="pronoun", number="sg.", person="1"),
            MorphRow(word="andiamo", lemma="andare", pos="verb", number="pl.", person="1"),
        ]
    }
    assert _agreement(nos, texts, rows, morph_rows) == []


def test_validate_unit_accepts_a_quantifier_resuming_a_first_plural_subject():
    """"A seder ci **ponemmo** ivi **ambedui**" (purgatorio 4:52): `ambedue`/`amendue` and the
    distributive `uno` stand in for the whole of a "we" the verb already carries."""
    from dante_corpus.morph import MorphRow

    nos, texts = [1], ["ponemmo ambedui"]
    rows = [
        dep.DepRow(1, 1, "ponemmo", "root", 0, 0),
        dep.DepRow(1, 2, "ambedui", "nsubj", 1, 1),
    ]
    morph_rows = {
        1: [
            MorphRow(word="ponemmo", lemma="porre", pos="verb", number="pl.", person="1"),
            MorphRow(word="ambedui", lemma="ambedue", pos="adjective", number="pl."),
        ]
    }
    assert _agreement(nos, texts, rows, morph_rows) == []


# --- Purgatorio 21-25 read: rule CV -----------------------------------------------------


def test_validate_unit_reports_a_third_person_coordination_under_a_first_plural_head():
    """Rule CV: the 1/2-plural exclusion delegated the coordinate case to the conjunct branch's
    person test, but *returned* before that branch could run. "Né 'l dir l'andar, né l'andar lui
    più lento / facea, ma ragionando **andavam** forte" (purgatorio 24:2): no member of the
    coordination is a "we"."""
    from dante_corpus.morph import MorphRow

    nos, texts = [1], ["'l dir l'andar andavam"]
    rows = [
        dep.DepRow(1, 1, "dir", "conj", 1, 2),
        dep.DepRow(1, 2, "andar", "nsubj", 1, 3),
        dep.DepRow(1, 3, "andavam", "root", 0, 0),
    ]
    morph_rows = {
        1: [
            MorphRow(word="dir", lemma="dire", pos="noun", number="sg."),
            MorphRow(word="andar", lemma="andare", pos="noun", number="sg."),
            MorphRow(word="andavam", lemma="andare", pos="verb", number="pl.", person="1"),
        ]
    }
    assert [v.detail for v in _agreement(nos, texts, rows, morph_rows)] == [
        "nsubj 1.2 'andar' disagrees with head 1.3 'andavam': person 3 vs 1"
    ]


def test_validate_unit_accepts_a_coordination_whose_nested_conjunct_carries_the_person():
    """Rule CV's other half: a coordination is a **chain**. "La bella donna … e Stazio e io
    seguitavam" (purgatorio 32:28) hangs `io` under `Stazio` under `donna`, so the member that
    carries the person is only reachable by walking `conj` transitively."""
    from dante_corpus.morph import MorphRow

    nos, texts = [1], ["donna Stazio io seguitavam"]
    rows = [
        dep.DepRow(1, 1, "donna", "nsubj", 1, 4),
        dep.DepRow(1, 2, "Stazio", "conj", 1, 1),
        dep.DepRow(1, 3, "io", "conj", 1, 2),
        dep.DepRow(1, 4, "seguitavam", "root", 0, 0),
    ]
    morph_rows = {
        1: [
            MorphRow(word="donna", lemma="donna", pos="noun", number="sg."),
            MorphRow(word="Stazio", lemma="Stazio", pos="noun", number="sg."),
            MorphRow(word="io", lemma="io", pos="pronoun", number="sg.", person="1"),
            MorphRow(word="seguitavam", lemma="seguire", pos="verb", number="pl.", person="1"),
        ]
    }
    assert _agreement(nos, texts, rows, morph_rows) == []


def test_validate_unit_reports_a_person_clash_a_number_exclusion_used_to_swallow():
    """Rule CV: the number-only exclusions ran *before* the person test and took it down with
    them. Here "coordination inside the subject phrase" licenses the singular-under-plural, and
    the 3-vs-1 person clash is asked anyway."""
    from dante_corpus.morph import MorphRow

    nos, texts = [1], ["coro e altro andavam"]
    rows = [
        dep.DepRow(1, 1, "coro", "nsubj", 1, 4),
        dep.DepRow(1, 2, "e", "cc", 1, 1),
        dep.DepRow(1, 3, "altro", "nmod", 1, 1),
        dep.DepRow(1, 4, "andavam", "root", 0, 0),
    ]
    morph_rows = {
        1: [
            MorphRow(word="coro", lemma="coro", pos="noun", number="sg."),
            MorphRow(word="e", lemma="e", pos="conjunction"),
            MorphRow(word="altro", lemma="altro", pos="pronoun", number="sg."),
            MorphRow(word="andavam", lemma="andare", pos="verb", number="pl.", person="1"),
        ]
    }
    assert [v.detail for v in _agreement(nos, texts, rows, morph_rows)] == [
        "nsubj 1.1 'coro' disagrees with head 1.4 'andavam': person 3 vs 1"
    ]


def test_validate_unit_still_accepts_the_number_licence_when_the_person_agrees():
    """The same shape with a third-person head: the number exclusion still applies, and the pair
    comes out undecidable exactly as before rule CV."""
    from dante_corpus.morph import MorphRow

    nos, texts = [1], ["coro e altro andavano"]
    rows = [
        dep.DepRow(1, 1, "coro", "nsubj", 1, 4),
        dep.DepRow(1, 2, "e", "cc", 1, 1),
        dep.DepRow(1, 3, "altro", "nmod", 1, 1),
        dep.DepRow(1, 4, "andavano", "root", 0, 0),
    ]
    morph_rows = {
        1: [
            MorphRow(word="coro", lemma="coro", pos="noun", number="sg."),
            MorphRow(word="e", lemma="e", pos="conjunction"),
            MorphRow(word="altro", lemma="altro", pos="pronoun", number="sg."),
            MorphRow(word="andavano", lemma="andare", pos="verb", number="pl.", person="3"),
        ]
    }
    assert _agreement(nos, texts, rows, morph_rows) == []


def test_validate_unit_accepts_tutti_e_cinque_under_a_first_plural_head():
    """Rule CV: `tutto` joins `_DISTRIBUTIVE_LEMMAS`. "là 've già **tutti e cinque sedavamo**"
    (purgatorio 9:12) names the whole of the "we" the verb carries."""
    from dante_corpus.morph import MorphRow

    nos, texts = [1], ["tutti e cinque sedavamo"]
    rows = [
        dep.DepRow(1, 1, "tutti", "nsubj", 1, 4),
        dep.DepRow(1, 2, "e", "cc", 1, 3),
        dep.DepRow(1, 3, "cinque", "conj", 1, 1),
        dep.DepRow(1, 4, "sedavamo", "root", 0, 0),
    ]
    morph_rows = {
        1: [
            MorphRow(word="tutti", lemma="tutto", pos="adjective", number="pl."),
            MorphRow(word="e", lemma="e", pos="conjunction"),
            MorphRow(word="cinque", lemma="cinque", pos="numeral"),
            MorphRow(word="sedavamo", lemma="sedere", pos="verb", number="pl.", person="1"),
        ]
    }
    assert _agreement(nos, texts, rows, morph_rows) == []
