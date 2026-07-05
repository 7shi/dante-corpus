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
