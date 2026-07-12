"""Deterministic tests for Layer 5 predicate-argument skeleton (no model calls)."""

from dante_corpus import api, dep, morph, skel

# The skeleton table format: model cites predicate/argument token positions the same way
# Layer 4 does; Pred Word/Arg Word are build-time verification anchors only.
SAMPLE_TABLE = """\
| Pred Line | Pred Token | Pred Word | Role | Arg Line | Arg Token | Arg Word |
|---|---|---|---|---|---|---|
| 2 | 2 | ritrovai | subj | 0 | 0 | - |
| 2 | 2 | ritrovai | obl:in | 1 | 2 | mezzo |
| 2 | 2 | ritrovai | obl:per | 2 | 5 | selva |
| 3 | 6 | smarrita | subj | 3 | 4 | via |
"""


def _lines(start, end):
    lines = api.canto("inferno", 1).lines(start, end)
    return [line.no for line in lines], [line.text for line in lines]


def _unit(rows):
    by_line: dict[int, list[skel.SkelRow]] = {}
    for row in rows:
        by_line.setdefault(row.line, []).append(row)
    return by_line


# --- canon_header --------------------------------------------------------------------


def test_canon_header():
    assert skel.canon_header("Pred Line") == "line"
    assert skel.canon_header(" Arg Token ") == "arg_token"
    assert skel.canon_header("Role") == "role"
    assert skel.canon_header("Reference Equivalent") is None


# --- resolve_chunk ---------------------------------------------------------------------


def test_resolve_chunk_round_trip():
    nos, texts = _lines(1, 3)
    rows_by_line, mismatches = skel.resolve_chunk(nos, texts, SAMPLE_TABLE)
    assert mismatches == []
    ritrovai_rows = rows_by_line[2]
    assert len(ritrovai_rows) == 3
    subj = next(r for r in ritrovai_rows if r.role == "subj")
    assert (subj.arg_line, subj.arg_token) == (0, 0)
    obl_in = next(r for r in ritrovai_rows if r.role == "obl:in")
    assert (obl_in.arg_line, obl_in.arg_token) == (1, 2)
    smarrita = rows_by_line[3][0]
    assert smarrita.role == "subj" and (smarrita.arg_line, smarrita.arg_token) == (3, 4)


def test_resolve_chunk_raises_without_table():
    try:
        skel.resolve_chunk([1], ["x"], "not a table")
    except ValueError:
        return
    raise AssertionError("expected ValueError for unparseable table")


def test_resolve_chunk_flags_arg_word_mismatch():
    table = SAMPLE_TABLE.replace(
        "| 3 | 6 | smarrita | subj | 3 | 4 | via |",
        "| 3 | 6 | smarrita | subj | 3 | 4 | WRONG |",
    )
    nos, texts = _lines(1, 3)
    _, mismatches = skel.resolve_chunk(nos, texts, table)
    assert len(mismatches) == 1
    assert "3.6" in mismatches[0] and "WRONG" in mismatches[0]


def test_resolve_chunk_zero_arg_predicate():
    nos, texts = [1], ["Nel mezzo"]
    table = """\
| Pred Line | Pred Token | Pred Word | Role | Arg Line | Arg Token | Arg Word |
|---|---|---|---|---|---|---|
| 1 | 2 | mezzo | - | 0 | 0 | - |
"""
    rows_by_line, mismatches = skel.resolve_chunk(nos, texts, table)
    assert mismatches == []
    row = rows_by_line[1][0]
    assert row.role == "" and (row.arg_line, row.arg_token) == (0, 0)


# --- derive_unit: worked example (Inferno I.1-9) ----------------------------------------


def _canto1_morph():
    return morph.load_morph("inferno", 1)


def _canto1_dep():
    return dep.load_dep("inferno", 1)


def test_derive_unit_inferno_1_1_9():
    nos, texts = _lines(1, 9)
    dep_data = _canto1_dep()
    morph_data = _canto1_morph()
    derived = skel.derive_unit(nos, dep_data, morph_data)

    def role_args(line, token):
        return sorted(
            (r.role, r.arg_line, r.arg_token)
            for rows in derived.values()
            for r in rows
            if r.line == line and r.token == token
        )

    # ritrovai (2.2): pro-drop subj + two obliques.
    assert role_args(2, 2) == [
        ("obl:in", 1, 2),
        ("obl:per", 2, 5),
        ("subj", 0, 0),
    ]
    # smarrita (3.6): subj = via (3.4), cross-line predicate via advcl already resolved.
    assert role_args(3, 6) == [("subj", 3, 4)]
    # Line 4 hosts three predicates: dir (ccomp), era (subj/attr), è (subj/attr).
    assert role_args(4, 4) == [("ccomp", 4, 6)]
    assert role_args(4, 6) == [("attr", 4, 5), ("subj", 5, 2)]
    assert role_args(4, 7) == [("attr", 4, 8), ("subj", 4, 4)]
    # Line 5 has no predicate.
    assert derived.get(5, []) == []
    # rinova (6.4): relative pronoun subj, obj, oblique.
    assert role_args(6, 4) == [("obj", 6, 6), ("obl:in", 6, 3), ("subj", 6, 1)]
    # amara (7.3): finite via cop child, pro-drop subj.
    assert role_args(7, 3) == [("subj", 0, 0)]
    # morte (7.8): subj = poco (7.5).
    assert role_args(7, 8) == [("subj", 7, 5)]
    # trattar (8.3): non-finite, oblique only, no pro-drop subj.
    assert role_args(8, 3) == [("obl:di", 8, 5)]
    # trovai (8.9): acl:relcl predicate with subj/obj/bare obl.
    assert role_args(8, 9) == [("obj", 8, 6), ("obl", 8, 8), ("subj", 8, 7)]
    # dirò (9.1): pro-drop subj + oblique.
    assert role_args(9, 1) == [("obl:di", 9, 5), ("subj", 0, 0)]
    # scorte (9.10): acl:relcl predicate with subj/obj/bare obl.
    assert role_args(9, 10) == [("obj", 9, 6), ("obl", 9, 8), ("subj", 9, 7)]


def test_derive_unit_sorts_canonically():
    # Uses the full sentence unit (lines 1-3): the "mezzo" oblique's head lives on line 1.
    nos, texts = _lines(1, 3)
    derived = skel.derive_unit(nos, _canto1_dep(), _canto1_morph())
    roles = [r.role for r in derived[2]]
    assert roles == ["subj", "obl:in", "obl:per"]


# --- validate_unit: hard checks ---------------------------------------------------------


def test_validate_unit_flags_position_out_of_range():
    nos, texts = [1], ["Nel mezzo"]
    rows = [skel.SkelRow(1, 5, "x", "subj", 1, 1)]  # token 5 doesn't exist
    violations = skel.validate_unit(nos, texts, _unit(rows))
    assert any(v.kind == "position" for v in violations)


def test_validate_unit_flags_word_mismatch():
    nos, texts = [1], ["Nel mezzo"]
    rows = [skel.SkelRow(1, 2, "WRONG", "", 0, 0)]
    violations = skel.validate_unit(nos, texts, _unit(rows))
    assert any(v.kind == "word" for v in violations)


def test_validate_unit_flags_bad_zero_arg():
    nos, texts = [1], ["Nel mezzo"]
    rows = [skel.SkelRow(1, 2, "mezzo", "obj", 0, 0)]  # obj may not use (0,0)
    violations = skel.validate_unit(nos, texts, _unit(rows))
    assert any(v.kind == "position" for v in violations)


def test_validate_unit_flags_dup_and_self_citation():
    nos, texts = [1], ["Nel mezzo"]
    rows = [
        skel.SkelRow(1, 2, "mezzo", "obj", 1, 1),
        skel.SkelRow(1, 2, "mezzo", "obj", 1, 1),  # exact duplicate
        skel.SkelRow(1, 1, "Nel", "obl", 1, 1),  # self-citation
    ]
    violations = skel.validate_unit(nos, texts, _unit(rows))
    kinds = [v.kind for v in violations]
    assert kinds.count("dup") >= 2


def test_validate_unit_flags_clausal_arg_not_a_predicate():
    nos, texts = [1], ["Nel mezzo"]
    rows = [skel.SkelRow(1, 1, "Nel", "ccomp", 1, 2)]  # 1.2 is never a predicate here
    violations = skel.validate_unit(nos, texts, _unit(rows))
    assert any(v.kind == "clausal" for v in violations)


def test_validate_unit_sentinel_conflict():
    nos, texts = [1], ["Nel mezzo"]
    rows = [
        skel.SkelRow(1, 0, "", "", 0, 0),
        skel.SkelRow(1, 2, "mezzo", "", 0, 0),
    ]
    violations = skel.validate_unit(nos, texts, _unit(rows))
    assert any(v.kind == "sentinel" for v in violations)


# --- validate_unit: soft checks -----------------------------------------------------------


def test_validate_unit_flags_unknown_role():
    nos, texts = [1], ["Nel mezzo"]
    rows = [skel.SkelRow(1, 2, "mezzo", "bogus", 1, 1)]
    violations = skel.validate_unit(nos, texts, _unit(rows))
    assert any(v.kind == "tag" and "bogus" in v.detail for v in violations)


def test_validate_unit_accepts_obl_prep_role():
    nos, texts = [1], ["Nel mezzo"]
    rows = [skel.SkelRow(1, 2, "mezzo", "obl:in", 1, 1)]
    violations = skel.validate_unit(nos, texts, _unit(rows))
    assert not any(v.kind == "tag" and "obl:in" in v.detail for v in violations)


def test_validate_unit_flags_membership_violation():
    from dante_corpus.morph import MorphRow

    nos, texts = [1], ["Nel mezzo del"]
    rows = [skel.SkelRow(1, 2, "mezzo", "obj", 1, 1)]  # 1.1 "Nel" heads no NP, not a pronoun
    morph_rows = {
        1: [
            MorphRow(word="Nel", pos="preposition"),
            MorphRow(word="mezzo", pos="noun"),
            MorphRow(word="del", pos="preposition"),
        ]
    }
    violations = skel.validate_unit(nos, texts, _unit(rows), morph_rows=morph_rows, np_rows={1: []})
    assert any(v.kind == "tag" and "heads no NP" in v.detail for v in violations)


def test_validate_unit_membership_accepts_np_head():
    from dante_corpus.morph import MorphRow
    from dante_corpus.np import NPSpan

    nos, texts = [1], ["Nel mezzo del"]
    rows = [skel.SkelRow(1, 2, "mezzo", "obj", 1, 2)]
    morph_rows = {
        1: [
            MorphRow(word="Nel", pos="preposition"),
            MorphRow(word="mezzo", pos="noun"),
            MorphRow(word="del", pos="preposition"),
        ]
    }
    np_rows = {1: [NPSpan(line=1, start=2, end=2, head=2, text="mezzo")]}
    violations = skel.validate_unit(nos, texts, _unit(rows), morph_rows=morph_rows, np_rows=np_rows)
    assert not any(v.kind == "tag" and "heads no NP" in v.detail for v in violations)


def _unit_1_3():
    nos, texts = _lines(1, 3)
    dep_all, morph_all = _canto1_dep(), _canto1_morph()
    dep_data = {no: dep_all[no] for no in nos}
    morph_data = {no: morph_all[no] for no in nos}
    return nos, texts, dep_data, morph_data


def test_validate_unit_divergence_missing_and_extra_tuple():
    nos, texts, dep_data, morph_data = _unit_1_3()
    # Given: only the subj row, missing the two obliques; plus one bogus extra predicate.
    rows = _unit([
        skel.SkelRow(2, 2, "ritrovai", "subj", 0, 0),
        skel.SkelRow(2, 6, "oscura", "", 0, 0),  # not a real predicate per derive_unit
    ])
    violations = skel.validate_unit(nos, texts, rows, morph_rows=morph_data, dep_rows=dep_data)
    details = [v.detail for v in violations]
    assert any("missing_arg" in d and "obl:in" in d for d in details)
    assert any("missing_arg" in d and "obl:per" in d for d in details)
    assert any("extra_tuple" in d and "2.6" in d for d in details)


def test_validate_unit_divergence_role_mismatch():
    nos, texts, dep_data, morph_data = _unit_1_3()
    rows = _unit([
        skel.SkelRow(2, 2, "ritrovai", "subj", 0, 0),
        skel.SkelRow(2, 2, "ritrovai", "obj", 1, 2),  # should be obl:in, not obj
        skel.SkelRow(2, 2, "ritrovai", "obl:per", 2, 5),
    ])
    violations = skel.validate_unit(nos, texts, rows, morph_rows=morph_data, dep_rows=dep_data)
    assert any("role_mismatch" in v.detail for v in violations)


def test_validate_unit_clean_matches_derivation():
    nos, texts, dep_data, morph_data = _unit_1_3()
    derived = skel.derive_unit(nos, dep_data, morph_data)
    violations = skel.validate_unit(nos, texts, derived, morph_rows=morph_data, dep_rows=dep_data)
    assert violations == []


# --- artifact I/O ----------------------------------------------------------------------


def test_write_load_round_trip(tmp_path, monkeypatch):
    monkeypatch.setattr(skel, "SKEL_DIR", tmp_path)
    rows = [
        skel.SkelRow(2, 2, "ritrovai", "subj", 0, 0),
        skel.SkelRow(2, 2, "ritrovai", "obl:per", 2, 5),
    ]
    skel.write_skel("inferno", 1, [(1, []), (2, rows)])
    assert skel.has_skel("inferno", 1)
    loaded = skel.load_skel("inferno", 1)
    assert loaded.get(1, ()) == ()  # sentinel line: no predicates
    assert loaded[2] == tuple(sorted(rows, key=skel._row_sort_key))


def test_tuples_canto_ids(tmp_path, monkeypatch):
    monkeypatch.setattr(skel, "SKEL_DIR", tmp_path)
    rows = [
        skel.SkelRow(2, 2, "ritrovai", "subj", 0, 0),
        skel.SkelRow(2, 2, "ritrovai", "obl:per", 2, 5),
        skel.SkelRow(2, 6, "oscura", "", 0, 0),
    ]
    skel.write_skel("inferno", 1, [(2, rows)])
    tuples = skel.tuples_canto("inferno", 1)
    assert [t.skel_id for t in tuples] == ["2.1", "2.2"]
    first = tuples[0]
    assert first.word == "ritrovai" and len(first.args) == 2
    second = tuples[1]
    assert second.word == "oscura" and second.args == ()


# --- serve-time joins --------------------------------------------------------------------


def test_np_head_index_and_arg_np():
    from dante_corpus.np import NPSpan

    child = NPSpan(line=1, start=4, end=7, head=4, text="cammin di nostra vita")
    parent = NPSpan(line=1, start=2, end=7, head=2, text="mezzo del cammin di nostra vita", children=(child,))
    idx = skel.np_head_index((parent,))
    assert idx[(1, 2)] is parent
    assert idx[(1, 4)] is child
    arg = skel.SkelArg(role="obl:in", line=1, token=2)
    assert skel.arg_np(arg, idx) is parent


def test_antecedent_via_acl_relcl():
    idx = dep.index(_canto1_dep())
    t = skel.SkelTuple(line=6, token=4, word="rinova", skel_id="6.1")
    assert skel.antecedent(t, idx) == (5, 2)
    non_relcl = skel.SkelTuple(line=2, token=2, word="ritrovai", skel_id="2.1")
    assert skel.antecedent(non_relcl, idx) is None


def test_pro_drop_features():
    morph_idx = skel.morph_index(_canto1_morph())
    children_idx = skel.children_index(_canto1_dep())
    ritrovai = skel.SkelTuple(line=2, token=2, word="ritrovai", skel_id="2.1")
    feats = skel.pro_drop_features(ritrovai, morph_idx, children_idx)
    assert feats  # has person info directly on the finite verb
