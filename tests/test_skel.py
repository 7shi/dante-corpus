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


def test_validate_unit_membership_accepts_relative_pronoun_mistagged_conjunction():
    from dante_corpus.morph import MorphRow

    # "che" mistagged conjunction (see morph/CORRECTIONS.md) still counts as a pronoun by word form.
    nos, texts = [1], ["mezzo che"]
    rows = [skel.SkelRow(1, 1, "mezzo", "obj", 1, 2)]
    morph_rows = {1: [MorphRow(word="mezzo", pos="noun"), MorphRow(word="che", pos="conjunction")]}
    violations = skel.validate_unit(nos, texts, _unit(rows), morph_rows=morph_rows, np_rows={1: []})
    assert not any(v.kind == "tag" and "heads no NP" in v.detail for v in violations)


def test_validate_unit_membership_accepts_elided_che():
    from dante_corpus.morph import MorphRow

    nos, texts = [1], ["mezzo ch'"]
    rows = [skel.SkelRow(1, 1, "mezzo", "obj", 1, 2)]
    morph_rows = {1: [MorphRow(word="mezzo", pos="noun"), MorphRow(word="ch'", pos="conjunction")]}
    violations = skel.validate_unit(nos, texts, _unit(rows), morph_rows=morph_rows, np_rows={1: []})
    assert not any(v.kind == "tag" and "heads no NP" in v.detail for v in violations)


def test_validate_unit_membership_accepts_adverb_obl():
    from dante_corpus.morph import MorphRow

    nos, texts = [1], ["mezzo quivi"]
    rows = [skel.SkelRow(1, 1, "mezzo", "obl", 1, 2)]
    morph_rows = {1: [MorphRow(word="mezzo", pos="noun"), MorphRow(word="quivi", pos="adverb")]}
    violations = skel.validate_unit(nos, texts, _unit(rows), morph_rows=morph_rows, np_rows={1: []})
    assert not any(v.kind == "tag" and "heads no NP" in v.detail for v in violations)


def test_validate_unit_membership_rejects_adverb_for_non_obl_role():
    from dante_corpus.morph import MorphRow

    nos, texts = [1], ["mezzo quivi"]
    rows = [skel.SkelRow(1, 1, "mezzo", "obj", 1, 2)]  # obj, not obl -> adverb still doesn't count
    morph_rows = {1: [MorphRow(word="mezzo", pos="noun"), MorphRow(word="quivi", pos="adverb")]}
    violations = skel.validate_unit(nos, texts, _unit(rows), morph_rows=morph_rows, np_rows={1: []})
    assert any(v.kind == "tag" and "heads no NP" in v.detail for v in violations)


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


def test_validate_unit_divergence_normalizes_attr_xcomp_and_prep_variants():
    nos, texts, dep_data, morph_data = _unit_1_3()
    rows = _unit([
        skel.SkelRow(2, 2, "ritrovai", "subj", 0, 0),
        skel.SkelRow(2, 2, "ritrovai", "attr", 1, 2),  # derived: xcomp — should canonicalize equal
        skel.SkelRow(2, 2, "ritrovai", "obl:sanza", 2, 5),  # derived: obl:per — genuine mismatch survives
    ])
    violations = skel.validate_unit(nos, texts, rows, morph_rows=morph_data, dep_rows=dep_data)
    details = [v.detail for v in violations]
    assert not any("attr" in d and "xcomp" in d and "role_mismatch" in d for d in details)
    assert any("role_mismatch" in d for d in details)  # obl:sanza vs obl:per still a real mismatch


def test_validate_unit_divergence_ccomp_double_listing_suppressed():
    nos, texts = _lines(4, 5)
    dep_all, morph_all = _canto1_dep(), _canto1_morph()
    dep_data = {no: dep_all[no] for no in nos}
    morph_data = {no: morph_all[no] for no in nos}
    # Derived: dir (4.4) has a ccomp arg citing 4.6 ("era"). Given side omits that arg but lists
    # 4.6 as its own predicate tuple instead — the double-listing derive_unit doesn't dedupe.
    rows = _unit([
        skel.SkelRow(4, 6, "era", "subj", 5, 2),
        skel.SkelRow(4, 6, "era", "attr", 4, 5),
        skel.SkelRow(4, 7, "è", "subj", 4, 4),
        skel.SkelRow(4, 7, "è", "attr", 4, 8),
    ])
    violations = skel.validate_unit(nos, texts, rows, morph_rows=morph_data, dep_rows=dep_data)
    details = [v.detail for v in violations]
    assert not any("missing_arg" in d and "ccomp" in d for d in details)
    assert any("missing_tuple" in d and "4.4" in d for d in details)  # dir itself still unproposed


# --- _classify_divergence: attr/xcomp double-listing + elided copula (Phase 4) --------


def test_classify_divergence_attr_double_listing_suppressed():
    # "son" (2.2) has an attr row citing "Molti" (2.1); the LLM also lists "Molti" as its own
    # redundant predicate tuple with the same subj — pure restatement, not a divergence.
    derived = {2: [
        skel.SkelRow(2, 2, "son", "subj", 2, 4),
        skel.SkelRow(2, 2, "son", "attr", 2, 1),
    ]}
    given = {2: [
        skel.SkelRow(2, 2, "son", "subj", 2, 4),
        skel.SkelRow(2, 2, "son", "attr", 2, 1),
        skel.SkelRow(2, 1, "Molti", "subj", 2, 4),  # double-listed, not derived as its own predicate
    ]}
    assert skel._classify_divergence(given, derived) == []


def test_classify_divergence_elided_copula_conj_whitelisted():
    # "mantoani" (1.1) is coordinate (conj) with a real clause and carries no copula token at
    # all — derive_unit structurally can't produce it, but it's a genuine reading, not an error.
    derived = {1: []}
    given = {1: [skel.SkelRow(1, 1, "mantoani", "subj", 1, 4)]}
    dep_index_by_pos = {
        (1, 1): dep.DepRow(line=1, token=1, word="mantoani", deprel="conj", head_line=0, head_token=6),
    }
    morph_pos_by_position = {(1, 1): "adjective"}
    violations = skel._classify_divergence(given, derived, dep_index_by_pos, morph_pos_by_position)
    assert violations == []


def test_classify_divergence_amod_extra_tuple_not_whitelisted():
    # A plain NP-internal participial modifier (amod) the LLM wrongly promoted to predicate
    # status — a genuine error, must still flag (not swallowed by the elided-copula whitelist).
    derived = {1: []}
    given = {1: [skel.SkelRow(1, 3, "unta", "subj", 1, 5)]}
    dep_index_by_pos = {
        (1, 3): dep.DepRow(line=1, token=3, word="unta", deprel="amod", head_line=1, head_token=5),
    }
    morph_pos_by_position = {(1, 3): "adjective"}
    violations = skel._classify_divergence(given, derived, dep_index_by_pos, morph_pos_by_position)
    assert any(v.detail.startswith("extra_tuple") and "1.3" in v.detail for v in violations)


# --- _classify_divergence: authority model (Phase 2, PLAN.md) -------------------------


def test_classify_divergence_non_finite_predicate_accepts_null_subject():
    # trattar-style: no derived subj row at all (non-finite), LLM marks pro-drop ∅ anyway.
    derived = {1: [skel.SkelRow(1, 3, "trattar", "obl:di", 1, 5)]}
    given = {1: [
        skel.SkelRow(1, 3, "trattar", "obl:di", 1, 5),
        skel.SkelRow(1, 3, "trattar", "subj", 0, 0),
    ]}
    dep_index_by_pos = {
        (1, 3): dep.DepRow(line=1, token=3, word="trattar", deprel="advcl", head_line=1, head_token=1),
    }
    assert skel._classify_divergence(given, derived, dep_index_by_pos) == []


def test_classify_divergence_xcomp_control_subject_accepts_matrix_arg():
    matrix = skel.SkelRow(2, 2, "vuole", "subj", 2, 1)
    matrix_xcomp = skel.SkelRow(2, 2, "vuole", "xcomp", 2, 3)
    derived = {2: [matrix, matrix_xcomp, skel.SkelRow(2, 3, "partire", "", 0, 0)]}
    given = {2: [
        skel.SkelRow(2, 2, "vuole", "subj", 2, 1),
        skel.SkelRow(2, 2, "vuole", "xcomp", 2, 3),
        skel.SkelRow(2, 3, "partire", "subj", 2, 1),  # LLM resolves the control subject explicitly
    ]}
    dep_index_by_pos = {
        (2, 3): dep.DepRow(line=2, token=3, word="partire", deprel="xcomp", head_line=2, head_token=2),
    }
    assert skel._classify_divergence(given, derived, dep_index_by_pos) == []


def test_classify_divergence_xcomp_control_subject_rejects_unrelated_arg():
    matrix = skel.SkelRow(2, 2, "vuole", "subj", 2, 1)
    matrix_xcomp = skel.SkelRow(2, 2, "vuole", "xcomp", 2, 3)
    derived = {2: [matrix, matrix_xcomp, skel.SkelRow(2, 3, "partire", "", 0, 0)]}
    given = {2: [
        skel.SkelRow(2, 2, "vuole", "subj", 2, 1),
        skel.SkelRow(2, 2, "vuole", "xcomp", 2, 3),
        skel.SkelRow(2, 3, "partire", "subj", 2, 5),  # neither matrix subj nor obj -> genuine disagreement
    ]}
    dep_index_by_pos = {
        (2, 3): dep.DepRow(line=2, token=3, word="partire", deprel="xcomp", head_line=2, head_token=2),
    }
    violations = skel._classify_divergence(given, derived, dep_index_by_pos)
    assert any(v.detail.startswith("extra_arg") and v.arg == (2, 5) for v in violations)


# --- _classify_divergence: coordination / nmod normalization (Phase 5, PLAN.md) -------


def test_classify_divergence_coordinated_argument_collapsed():
    # "si ciberà di terra e di sapïenza": both conjuncts are objects and the LLM lists both;
    # derive_unit reads only the predicate's direct children, so it sees "terra" (1.3) alone.
    derived = {1: [skel.SkelRow(1, 2, "ciberà", "obj", 1, 3)]}
    given = {1: [
        skel.SkelRow(1, 2, "ciberà", "obj", 1, 3),
        skel.SkelRow(1, 2, "ciberà", "obj", 1, 5),  # second conjunct
    ]}
    dep_index_by_pos = {
        (1, 3): dep.DepRow(line=1, token=3, word="terra", deprel="obj", head_line=1, head_token=2),
        (1, 5): dep.DepRow(line=1, token=5, word="sapïenza", deprel="conj", head_line=1, head_token=3),
    }
    assert skel._classify_divergence(given, derived, dep_index_by_pos) == []


def test_classify_divergence_coordination_collapse_preserves_role_disagreement():
    # Collapsing the coordination must not swallow a genuine role disagreement on the conjunct.
    derived = {1: [skel.SkelRow(1, 2, "ciberà", "obj", 1, 3)]}
    given = {1: [skel.SkelRow(1, 2, "ciberà", "subj", 1, 5)]}
    dep_index_by_pos = {
        (1, 3): dep.DepRow(line=1, token=3, word="terra", deprel="obj", head_line=1, head_token=2),
        (1, 5): dep.DepRow(line=1, token=5, word="sapïenza", deprel="conj", head_line=1, head_token=3),
    }
    violations = skel._classify_divergence(given, derived, dep_index_by_pos)
    assert [v.detail.split(":", 1)[0] for v in violations] == ["role_mismatch"]


def test_classify_divergence_uncoordinated_extra_argument_still_flagged():
    derived = {1: [skel.SkelRow(1, 2, "ciberà", "obj", 1, 3)]}
    given = {1: [
        skel.SkelRow(1, 2, "ciberà", "obj", 1, 3),
        skel.SkelRow(1, 2, "ciberà", "obj", 1, 5),
    ]}
    dep_index_by_pos = {
        (1, 3): dep.DepRow(line=1, token=3, word="terra", deprel="obj", head_line=1, head_token=2),
        (1, 5): dep.DepRow(line=1, token=5, word="sapïenza", deprel="nmod", head_line=1, head_token=4),
    }
    violations = skel._classify_divergence(given, derived, dep_index_by_pos)
    assert any(v.detail.startswith("extra_arg") and v.arg == (1, 5) for v in violations)


def test_classify_divergence_nmod_oblique_of_derived_argument_accepted():
    # "ha bisogno di te": the dep tree hangs "te" off the noun "bisogno" (nmod), which is itself
    # a derived argument of "ha"; the LLM reads it as the predicate's oblique.
    derived = {1: [skel.SkelRow(1, 1, "ha", "obj", 1, 2)]}
    given = {1: [
        skel.SkelRow(1, 1, "ha", "obj", 1, 2),
        skel.SkelRow(1, 1, "ha", "obl:di", 1, 4),
    ]}
    dep_index_by_pos = {
        (1, 2): dep.DepRow(line=1, token=2, word="bisogno", deprel="obj", head_line=1, head_token=1),
        (1, 4): dep.DepRow(line=1, token=4, word="te", deprel="nmod", head_line=1, head_token=2),
    }
    assert skel._classify_divergence(given, derived, dep_index_by_pos) == []


def test_classify_divergence_nmod_oblique_of_unrelated_token_still_flagged():
    derived = {1: [skel.SkelRow(1, 1, "ha", "obj", 1, 2)]}
    given = {1: [
        skel.SkelRow(1, 1, "ha", "obj", 1, 2),
        skel.SkelRow(1, 1, "ha", "obl:di", 1, 4),
    ]}
    dep_index_by_pos = {
        (1, 2): dep.DepRow(line=1, token=2, word="bisogno", deprel="obj", head_line=1, head_token=1),
        (1, 4): dep.DepRow(line=1, token=4, word="te", deprel="nmod", head_line=1, head_token=6),
    }
    violations = skel._classify_divergence(given, derived, dep_index_by_pos)
    assert any(v.detail.startswith("extra_arg") and v.arg == (1, 4) for v in violations)


# --- derive_unit / _classify_divergence: Phase 5b rules --------------------------------


def _conj_unit(conj_pos: str):
    """A line-initial coordinating word attached to the previous clause head with deprel `conj`
    ("E 'l mio buon duca ...", inferno 12:83) — Layer 4's routine treatment of such a token."""
    dep_rows = {1: [
        dep.DepRow(line=1, token=1, word="disse", deprel="root", head_line=0, head_token=0),
        dep.DepRow(line=1, token=2, word="E", deprel="conj", head_line=1, head_token=1),
        dep.DepRow(line=1, token=3, word="duca", deprel="nsubj", head_line=1, head_token=2),
    ]}
    morph_rows = {1: [
        morph.MorphRow(word="disse", pos="verb", person="3"),
        morph.MorphRow(word="E", pos=conj_pos),
        morph.MorphRow(word="duca", pos="noun"),
    ]}
    return skel.derive_unit([1], dep_rows, morph_rows)


def test_derive_unit_does_not_promote_coordinating_conjunction():
    derived = _conj_unit("conjunction")
    assert {(r.line, r.token) for rows in derived.values() for r in rows} == {(1, 1)}


def test_derive_unit_still_promotes_gapped_non_conjunction_conj():
    # Same shape, but the coordinated token is a real (gapped) predicate — still derived.
    derived = _conj_unit("verb")
    assert (1, 2) in {(r.line, r.token) for rows in derived.values() for r in rows}


def test_classify_divergence_copula_predicate_double_listing_suppressed():
    # "Molti son li animali": derive_unit's predicate is the nominal "Molti" (UD suppresses the
    # copula); the LLM lists "son" as the predicate too — a labeling-convention split.
    derived = {1: [skel.SkelRow(1, 1, "Molti", "subj", 1, 4)]}
    given = {1: [
        skel.SkelRow(1, 1, "Molti", "subj", 1, 4),
        skel.SkelRow(1, 2, "son", "subj", 1, 4),
    ]}
    dep_index_by_pos = {
        (1, 1): dep.DepRow(line=1, token=1, word="Molti", deprel="root", head_line=0, head_token=0),
        (1, 2): dep.DepRow(line=1, token=2, word="son", deprel="cop", head_line=1, head_token=1),
    }
    assert skel._classify_divergence(given, derived, dep_index_by_pos, {}) == []


def test_classify_divergence_copula_of_underived_head_still_flagged():
    # The copula's head is not a derived predicate: a genuine extra tuple, not a notation split.
    derived = {1: []}
    given = {1: [skel.SkelRow(1, 2, "son", "subj", 1, 4)]}
    dep_index_by_pos = {
        (1, 1): dep.DepRow(line=1, token=1, word="Molti", deprel="amod", head_line=1, head_token=4),
        (1, 2): dep.DepRow(line=1, token=2, word="son", deprel="cop", head_line=1, head_token=1),
    }
    violations = skel._classify_divergence(given, derived, dep_index_by_pos, {})
    assert any(v.detail.startswith("extra_tuple") and "1.2" in v.detail for v in violations)


def test_classify_divergence_adverbial_oblique_accepted():
    # "quivi" as an obl argument: an adverb attached advmod, which derive_unit can't emit as obl.
    derived = {1: [skel.SkelRow(1, 1, "vidi", "obj", 1, 3)]}
    given = {1: [
        skel.SkelRow(1, 1, "vidi", "obj", 1, 3),
        skel.SkelRow(1, 1, "vidi", "obl", 1, 2),
    ]}
    dep_index_by_pos = {
        (1, 2): dep.DepRow(line=1, token=2, word="quivi", deprel="advmod", head_line=1, head_token=1),
    }
    morph_pos = {(1, 2): "adverb"}
    assert skel._classify_divergence(given, derived, dep_index_by_pos, morph_pos) == []


def test_classify_divergence_adverbial_argument_of_nominal_role_still_flagged():
    # Same adverb cited as an obj — a genuine miscitation, not an adverbial oblique.
    derived = {1: [skel.SkelRow(1, 1, "vidi", "obj", 1, 3)]}
    given = {1: [
        skel.SkelRow(1, 1, "vidi", "obj", 1, 3),
        skel.SkelRow(1, 1, "vidi", "obj", 1, 2),
    ]}
    dep_index_by_pos = {
        (1, 2): dep.DepRow(line=1, token=2, word="quivi", deprel="advmod", head_line=1, head_token=1),
    }
    morph_pos = {(1, 2): "adverb"}
    violations = skel._classify_divergence(given, derived, dep_index_by_pos, morph_pos)
    assert any(v.detail.startswith("extra_arg") and v.arg == (1, 2) for v in violations)


# --- _classify_divergence: Phase 5f rule L ---------------------------------------------


def test_classify_divergence_oblique_lemma_refinement_accepted():
    # "che nel lago del cor m'era durata": the dative is a clitic fused into the token, so the
    # dep tree gives it no `case` child and derive_unit can only emit a bare `obl`; the LLM
    # naming the preposition is strictly more informative.
    derived = {1: [skel.SkelRow(1, 1, "era", "obl", 1, 2)]}
    given = {1: [skel.SkelRow(1, 1, "era", "obl:a", 1, 2)]}
    dep_index_by_pos = {
        (1, 2): dep.DepRow(line=1, token=2, word="m'", deprel="obl", head_line=1, head_token=1),
    }
    assert skel._classify_divergence(given, derived, dep_index_by_pos) == []


def test_classify_divergence_cross_lemma_oblique_still_flagged():
    # Both sides name a preposition and they disagree — a real divergence.
    derived = {1: [skel.SkelRow(1, 1, "era", "obl:di", 1, 2)]}
    given = {1: [skel.SkelRow(1, 1, "era", "obl:a", 1, 2)]}
    dep_index_by_pos = {
        (1, 2): dep.DepRow(line=1, token=2, word="cor", deprel="obl", head_line=1, head_token=1),
    }
    violations = skel._classify_divergence(given, derived, dep_index_by_pos)
    assert any(v.detail.startswith("role_mismatch") and v.arg == (1, 2) for v in violations)


def test_classify_divergence_bare_oblique_with_case_child_still_flagged():
    # The argument does have an explicit preposition, so a bare derived `obl` means derive_unit
    # had the lemma and dropped it — not the situation rule L describes.
    derived = {1: [skel.SkelRow(1, 1, "era", "obl", 1, 3)]}
    given = {1: [skel.SkelRow(1, 1, "era", "obl:a", 1, 3)]}
    dep_index_by_pos = {
        (1, 2): dep.DepRow(line=1, token=2, word="nel", deprel="case", head_line=1, head_token=3),
        (1, 3): dep.DepRow(line=1, token=3, word="lago", deprel="obl", head_line=1, head_token=1),
    }
    violations = skel._classify_divergence(given, derived, dep_index_by_pos)
    assert any(v.detail.startswith("role_mismatch") and v.arg == (1, 3) for v in violations)


# --- _classify_divergence: Phase 5g rule M ---------------------------------------------


def test_classify_divergence_object_complement_accepted():
    # "Voi cittadini mi chiamaste Ciacco": UD attaches the object complement as a plain `obj`,
    # the LLM names its predicative function.
    derived = {1: [skel.SkelRow(1, 4, "chiamaste", "obj", 1, 5)]}
    given = {1: [skel.SkelRow(1, 4, "chiamaste", "xcomp", 1, 5)]}
    assert skel._classify_divergence(given, derived) == []


def test_classify_divergence_copular_predicate_nominal_accepted():
    # "non son torri, ma giganti": the predicate nominal is attached as a subject.
    derived = {1: [skel.SkelRow(1, 2, "son", "subj", 1, 3)]}
    given = {1: [skel.SkelRow(1, 2, "son", "xcomp", 1, 3)]}
    assert skel._classify_divergence(given, derived) == []


def test_classify_divergence_explicit_xcomp_contradicted_still_flagged():
    # The mirror direction: the dep tree carried an explicit xcomp deprel and the LLM called it
    # an object — a real disagreement, not a notation split.
    derived = {1: [skel.SkelRow(1, 1, "vuolsi", "xcomp", 1, 3)]}
    given = {1: [skel.SkelRow(1, 1, "vuolsi", "obj", 1, 3)]}
    violations = skel._classify_divergence(given, derived)
    assert any(v.detail.startswith("role_mismatch") and v.arg == (1, 3) for v in violations)


# --- _classify_divergence: Phase 5h rule N ---------------------------------------------


def test_classify_divergence_case_marked_object_accepted():
    # "curan di te ne la corte del cielo": the argument carries the `case` child "di", but Layer
    # 4 attached it as `obj`, so derive_unit reports the deprel and drops the preposition.
    derived = {1: [skel.SkelRow(1, 1, "curan", "obj", 1, 3)]}
    given = {1: [skel.SkelRow(1, 1, "curan", "obl:di", 1, 3)]}
    dep_index_by_pos = {
        (1, 2): dep.DepRow(line=1, token=2, word="di", deprel="case", head_line=1, head_token=3),
        (1, 3): dep.DepRow(line=1, token=3, word="te", deprel="obj", head_line=1, head_token=1),
    }
    assert skel._classify_divergence(given, derived, dep_index_by_pos) == []


def test_classify_divergence_case_marked_object_other_lemma_still_flagged():
    # The LLM names a different preposition than the one in the tree — a real disagreement.
    derived = {1: [skel.SkelRow(1, 1, "curan", "obj", 1, 3)]}
    given = {1: [skel.SkelRow(1, 1, "curan", "obl:a", 1, 3)]}
    dep_index_by_pos = {
        (1, 2): dep.DepRow(line=1, token=2, word="di", deprel="case", head_line=1, head_token=3),
        (1, 3): dep.DepRow(line=1, token=3, word="te", deprel="obj", head_line=1, head_token=1),
    }
    violations = skel._classify_divergence(given, derived, dep_index_by_pos)
    assert any(v.detail.startswith("role_mismatch") and v.arg == (1, 3) for v in violations)


def test_classify_divergence_clitic_object_without_case_child_still_flagged():
    # No `case` child at all (a clitic whose case the tree cannot express): both sides make a
    # case claim, so this stays a divergence — see CORRECTIONS.md's Phase 5h.
    derived = {1: [skel.SkelRow(1, 2, "pesa", "obj", 1, 1)]}
    given = {1: [skel.SkelRow(1, 2, "pesa", "obl:a", 1, 1)]}
    dep_index_by_pos = {
        (1, 1): dep.DepRow(line=1, token=1, word="mi", deprel="obj", head_line=1, head_token=2),
    }
    violations = skel._classify_divergence(given, derived, dep_index_by_pos)
    assert any(v.detail.startswith("role_mismatch") and v.arg == (1, 1) for v in violations)


# --- Phase 5j: preposition-lemma normalization + rule O --------------------------------


def test_normalize_prep_lemma_contractions_and_variants():
    # Preposition+article contractions collapse onto the base preposition (the LLM names the
    # contraction, derive_unit the base, since Layer 2 lemmatizes "nel" as "in+il").
    assert skel._normalize_prep_lemma("nel") == "in"
    assert skel._normalize_prep_lemma("dal") == "da"
    assert skel._normalize_prep_lemma("al") == "a"
    assert skel._normalize_prep_lemma("del") == "di"
    assert skel._normalize_prep_lemma("sul") == "su"
    # Archaic/apocopated spellings of the same preposition.
    assert skel._normalize_prep_lemma("sovr'") == "sopra"
    assert skel._normalize_prep_lemma("ver'") == "verso"
    assert skel._normalize_prep_lemma("'nnanzi") == "innanzi"
    assert skel._normalize_prep_lemma("fin") == "fino"
    # The `in+verso` univerbation family, normalized onto the derived side's convention.
    assert skel._normalize_prep_lemma("inver'") == "in"
    assert skel._normalize_prep_lemma("inverso") == "in"
    # A preposition that is nobody's variant is left alone.
    assert skel._normalize_prep_lemma("dentro") == "dentro"


def test_classify_divergence_contraction_lemma_is_not_a_divergence():
    # "ne la quarta lacca": the LLM writes `obl:ne`, derive_unit `obl:in` — one preposition.
    derived = {1: [skel.SkelRow(1, 1, "scendemmo", "obl:in", 1, 3)]}
    given = {1: [skel.SkelRow(1, 1, "scendemmo", "obl:ne", 1, 3)]}
    assert skel._classify_divergence(given, derived) == []


def test_classify_divergence_co_present_preposition_accepted():
    # "in su le porte": both prepositions are `case` children of the argument and derive_unit
    # reports only one of them, so naming the other is a choice, not a contradiction.
    derived = {1: [skel.SkelRow(1, 1, "vidi", "obl:su", 1, 4)]}
    given = {1: [skel.SkelRow(1, 1, "vidi", "obl:in", 1, 4)]}
    dep_index_by_pos = {
        (1, 2): dep.DepRow(line=1, token=2, word="in", deprel="case", head_line=1, head_token=4),
        (1, 3): dep.DepRow(line=1, token=3, word="su", deprel="case", head_line=1, head_token=4),
        (1, 4): dep.DepRow(line=1, token=4, word="porte", deprel="obl", head_line=1, head_token=1),
    }
    assert skel._classify_divergence(given, derived, dep_index_by_pos) == []


def test_classify_divergence_co_present_preposition_mirror_still_flagged():
    # The mirror direction: the *derived* lemma is the argument's only `case` child and the LLM
    # named a preposition the tree does not attach there — measured as a heterogeneous class
    # (see CORRECTIONS.md's Phase 5j), so it stays flagged.
    derived = {1: [skel.SkelRow(1, 1, "giunse", "obl:su", 1, 3)]}
    given = {1: [skel.SkelRow(1, 1, "giunse", "obl:in", 1, 3)]}
    dep_index_by_pos = {
        (1, 2): dep.DepRow(line=1, token=2, word="su", deprel="case", head_line=1, head_token=3),
        (1, 3): dep.DepRow(line=1, token=3, word="ripa", deprel="obl", head_line=1, head_token=1),
    }
    violations = skel._classify_divergence(given, derived, dep_index_by_pos)
    assert any(v.detail.startswith("role_mismatch") and v.arg == (1, 3) for v in violations)


def test_classify_divergence_co_present_preposition_requires_both_sides_oblique():
    # Rule O only ever compares two `obl:<lemma>` labels; a given `obl:<lemma>` against a
    # derived `obj`/`subj` is rule N's business and keeps its own, narrower gate.
    derived = {1: [skel.SkelRow(1, 1, "vidi", "obj", 1, 3)]}
    given = {1: [skel.SkelRow(1, 1, "vidi", "obl:con", 1, 3)]}
    dep_index_by_pos = {
        (1, 2): dep.DepRow(line=1, token=2, word="in", deprel="case", head_line=1, head_token=3),
        (1, 3): dep.DepRow(line=1, token=3, word="porte", deprel="obj", head_line=1, head_token=1),
    }
    violations = skel._classify_divergence(given, derived, dep_index_by_pos)
    assert any(v.detail.startswith("role_mismatch") and v.arg == (1, 3) for v in violations)


# --- Phase 5l: rule R ------------------------------------------------------------------


def test_classify_divergence_predicative_advmod_accepted():
    # "e io etterno duro": the predicative adjective is attached as `advmod`, a deprel
    # derive_unit never reads, so it can produce no argument at all for it.
    derived = {1: [skel.SkelRow(1, 3, "duro", "subj", 1, 1)]}
    given = {1: [skel.SkelRow(1, 3, "duro", "subj", 1, 1),
                 skel.SkelRow(1, 3, "duro", "xcomp", 1, 2)]}
    dep_index_by_pos = {
        (1, 1): dep.DepRow(line=1, token=1, word="io", deprel="nsubj", head_line=1, head_token=3),
        (1, 2): dep.DepRow(line=1, token=2, word="etterno", deprel="advmod", head_line=1,
                           head_token=3),
    }
    morph_pos = {(1, 1): "pronoun", (1, 2): "adjective"}
    assert skel._classify_divergence(given, derived, dep_index_by_pos, morph_pos) == []


def test_classify_divergence_predicative_advmod_requires_adjective():
    # "che fu nel cominciar cotanto tosta": Layer 2 calls "tosta" an adverb, which leaves the
    # predicative reading undecided — still flagged.
    derived = {1: [skel.SkelRow(1, 1, "fu", "subj", 1, 3)]}
    given = {1: [skel.SkelRow(1, 1, "fu", "subj", 1, 3),
                 skel.SkelRow(1, 1, "fu", "xcomp", 1, 2)]}
    dep_index_by_pos = {
        (1, 2): dep.DepRow(line=1, token=2, word="tosta", deprel="advmod", head_line=1,
                           head_token=1),
        (1, 3): dep.DepRow(line=1, token=3, word="ella", deprel="nsubj", head_line=1,
                           head_token=1),
    }
    morph_pos = {(1, 2): "adverb", (1, 3): "pronoun"}
    violations = skel._classify_divergence(given, derived, dep_index_by_pos, morph_pos)
    assert any(v.detail.startswith("extra_arg") and v.arg == (1, 2) for v in violations)


def test_classify_divergence_predicative_advmod_requires_xcomp_role():
    # An adjective attached as `advmod` and cited as an *object* is a different claim, and one
    # the tree does not support — still flagged.
    derived = {1: [skel.SkelRow(1, 1, "va", "subj", 1, 3)]}
    given = {1: [skel.SkelRow(1, 1, "va", "subj", 1, 3),
                 skel.SkelRow(1, 1, "va", "obj", 1, 2)]}
    dep_index_by_pos = {
        (1, 2): dep.DepRow(line=1, token=2, word="superbo", deprel="advmod", head_line=1,
                           head_token=1),
        (1, 3): dep.DepRow(line=1, token=3, word="elli", deprel="nsubj", head_line=1,
                           head_token=1),
    }
    morph_pos = {(1, 2): "adjective", (1, 3): "pronoun"}
    violations = skel._classify_divergence(given, derived, dep_index_by_pos, morph_pos)
    assert any(v.detail.startswith("extra_arg") and v.arg == (1, 2) for v in violations)


# --- Phase 5m: rule S ------------------------------------------------------------------


def test_classify_divergence_nmod_complement_of_predicate_accepted():
    # "furon cagione di sua vittoria": the PP complement of a nominal predicate is attached
    # `nmod`, outside ARG_DEPRELS, so derive_unit can produce no argument for it — while the
    # `case` child names the very preposition the LLM cites.
    derived = {1: [skel.SkelRow(1, 1, "cagione", "subj", 1, 4)]}
    given = {1: [skel.SkelRow(1, 1, "cagione", "subj", 1, 4),
                 skel.SkelRow(1, 1, "cagione", "obl:di", 1, 3)]}
    dep_index_by_pos = {
        (1, 2): dep.DepRow(line=1, token=2, word="di", deprel="case", head_line=1, head_token=3),
        (1, 3): dep.DepRow(line=1, token=3, word="vittoria", deprel="nmod", head_line=1,
                           head_token=1),
        (1, 4): dep.DepRow(line=1, token=4, word="cose", deprel="nsubj", head_line=1,
                           head_token=1),
    }
    assert skel._classify_divergence(given, derived, dep_index_by_pos) == []


def test_classify_divergence_nmod_complement_requires_matching_case_child():
    # Naming a preposition the `nmod` edge does not carry is a real disagreement, the same
    # narrowing rules N and O apply.
    derived = {1: [skel.SkelRow(1, 1, "cagione", "subj", 1, 4)]}
    given = {1: [skel.SkelRow(1, 1, "cagione", "subj", 1, 4),
                 skel.SkelRow(1, 1, "cagione", "obl:a", 1, 3)]}
    dep_index_by_pos = {
        (1, 2): dep.DepRow(line=1, token=2, word="di", deprel="case", head_line=1, head_token=3),
        (1, 3): dep.DepRow(line=1, token=3, word="vittoria", deprel="nmod", head_line=1,
                           head_token=1),
        (1, 4): dep.DepRow(line=1, token=4, word="cose", deprel="nsubj", head_line=1,
                           head_token=1),
    }
    violations = skel._classify_divergence(given, derived, dep_index_by_pos)
    assert any(v.detail.startswith("extra_arg") and v.arg == (1, 3) for v in violations)


def test_classify_divergence_nmod_complement_requires_predicate_as_head():
    # An `nmod` hanging off some other token of the unit is not the predicate's own edge; rule D
    # covers the one case that is (an `nmod` of a *derived argument*), and nothing else.
    derived = {1: [skel.SkelRow(1, 1, "vidi", "obj", 1, 5)]}
    given = {1: [skel.SkelRow(1, 1, "vidi", "obj", 1, 5),
                 skel.SkelRow(1, 1, "vidi", "obl:di", 1, 3)]}
    dep_index_by_pos = {
        (1, 2): dep.DepRow(line=1, token=2, word="di", deprel="case", head_line=1, head_token=3),
        (1, 3): dep.DepRow(line=1, token=3, word="pietra", deprel="nmod", head_line=1,
                           head_token=4),
        (1, 4): dep.DepRow(line=1, token=4, word="torre", deprel="obl", head_line=1, head_token=1),
        (1, 5): dep.DepRow(line=1, token=5, word="gente", deprel="obj", head_line=1, head_token=1),
    }
    violations = skel._classify_divergence(given, derived, dep_index_by_pos)
    assert any(v.detail.startswith("extra_arg") and v.arg == (1, 3) for v in violations)


# --- Phase 5o: rule T ------------------------------------------------------------------


def test_classify_divergence_marked_adverbial_clause_accepted():
    # "un angel che s'appresta per venir verso noi": the infinitive clause hangs off the
    # predicate as `advcl` (outside ARG_DEPRELS, so derive_unit emits nothing), and its `mark`
    # child is the very preposition the LLM names.
    derived = {1: [skel.SkelRow(1, 2, "appresta", "subj", 1, 1)]}
    given = {1: [skel.SkelRow(1, 2, "appresta", "subj", 1, 1),
                 skel.SkelRow(1, 2, "appresta", "obl:per", 1, 4)]}
    dep_index_by_pos = {
        (1, 1): dep.DepRow(line=1, token=1, word="angel", deprel="nsubj", head_line=1,
                           head_token=2),
        (1, 3): dep.DepRow(line=1, token=3, word="per", deprel="mark", head_line=1, head_token=4),
        (1, 4): dep.DepRow(line=1, token=4, word="venir", deprel="advcl", head_line=1,
                           head_token=2),
    }
    assert skel._classify_divergence(given, derived, dep_index_by_pos) == []


def test_classify_divergence_marked_adverbial_clause_requires_matching_marker():
    # The rejected loose variant: a clause marked by something that is not the cited preposition
    # — "infin ch'el si raggiunge ove la tirannia convien che gema" — leaves the oblique reading
    # unconfirmed by the tree and stays flagged.
    derived = {1: [skel.SkelRow(1, 2, "raggiunge", "subj", 1, 1)]}
    given = {1: [skel.SkelRow(1, 2, "raggiunge", "subj", 1, 1),
                 skel.SkelRow(1, 2, "raggiunge", "obl:a", 1, 4)]}
    dep_index_by_pos = {
        (1, 1): dep.DepRow(line=1, token=1, word="el", deprel="nsubj", head_line=1, head_token=2),
        (1, 3): dep.DepRow(line=1, token=3, word="ove", deprel="mark", head_line=1, head_token=4),
        (1, 4): dep.DepRow(line=1, token=4, word="convien", deprel="advcl", head_line=1,
                           head_token=2),
    }
    violations = skel._classify_divergence(given, derived, dep_index_by_pos)
    assert any(v.detail.startswith("extra_arg") and v.arg == (1, 4) for v in violations)


def test_classify_divergence_marked_adverbial_clause_leaves_complement_readings_flagged():
    # The complement-vs-adjunct half of the `advcl` bucket: a given `xcomp`/`ccomp` over an
    # adverbial clause is a lexical argument-structure judgment, not a preposition the tree
    # carries, so rule T does not touch it ("i' vegno per menarvi a l'altra riva").
    derived = {1: [skel.SkelRow(1, 2, "vegno", "subj", 1, 1)]}
    given = {1: [skel.SkelRow(1, 2, "vegno", "subj", 1, 1),
                 skel.SkelRow(1, 2, "vegno", "xcomp", 1, 4)]}
    dep_index_by_pos = {
        (1, 1): dep.DepRow(line=1, token=1, word="i", deprel="nsubj", head_line=1, head_token=2),
        (1, 3): dep.DepRow(line=1, token=3, word="per", deprel="mark", head_line=1, head_token=4),
        (1, 4): dep.DepRow(line=1, token=4, word="menarvi", deprel="advcl", head_line=1,
                           head_token=2),
    }
    violations = skel._classify_divergence(given, derived, dep_index_by_pos)
    assert any(v.detail.startswith("extra_arg") and v.arg == (1, 4) for v in violations)


def test_classify_divergence_marked_adverbial_clause_requires_predicate_as_head():
    # An `advcl` of some other verb in the unit is not this predicate's own edge.
    derived = {1: [skel.SkelRow(1, 1, "disse", "subj", 1, 2)]}
    given = {1: [skel.SkelRow(1, 1, "disse", "subj", 1, 2),
                 skel.SkelRow(1, 1, "disse", "obl:per", 1, 5)]}
    dep_index_by_pos = {
        (1, 2): dep.DepRow(line=1, token=2, word="duca", deprel="nsubj", head_line=1,
                           head_token=1),
        (1, 3): dep.DepRow(line=1, token=3, word="venne", deprel="conj", head_line=1,
                           head_token=1),
        (1, 4): dep.DepRow(line=1, token=4, word="per", deprel="mark", head_line=1, head_token=5),
        (1, 5): dep.DepRow(line=1, token=5, word="veder", deprel="advcl", head_line=1,
                           head_token=3),
    }
    violations = skel._classify_divergence(given, derived, dep_index_by_pos)
    assert any(v.detail.startswith("extra_arg") and v.arg == (1, 5) for v in violations)


# --- Phase 5k: rules P and Q -----------------------------------------------------------


def test_classify_divergence_clausal_complement_flavor_accepted_both_ways():
    # "Fa che tu m'abbracce": Layer 4 tags the complement `xcomp` although its subject is overt,
    # the LLM calls it `ccomp`. Both say "clausal complement"; only the control judgment differs.
    derived = {1: [skel.SkelRow(1, 1, "Fa", "xcomp", 1, 4)]}
    given = {1: [skel.SkelRow(1, 1, "Fa", "ccomp", 1, 4)]}
    assert skel._classify_divergence(given, derived) == []
    derived = {1: [skel.SkelRow(1, 1, "par", "ccomp", 1, 4)]}
    given = {1: [skel.SkelRow(1, 1, "par", "xcomp", 1, 4)]}
    assert skel._classify_divergence(given, derived) == []


def test_classify_divergence_clausal_object_accepted():
    # "or mi concedi ch'io sappia": the complement clause's verb is attached straight to the
    # matrix predicate as `obj`, so derive_unit reports a direct argument for a whole clause.
    derived = {1: [skel.SkelRow(1, 1, "concedi", "obj", 1, 3)]}
    given = {1: [skel.SkelRow(1, 1, "concedi", "ccomp", 1, 3)]}
    morph_pos = {(1, 3): "verb"}
    assert skel._classify_divergence(given, derived, {}, morph_pos) == []


def test_classify_divergence_clausal_object_requires_verb_argument():
    # "che non parëa s'era laico o cherco": the cited argument is a noun, so calling it a clausal
    # complement is a misreading, not a more informative label.
    derived = {1: [skel.SkelRow(1, 1, "parëa", "subj", 1, 5)]}
    given = {1: [skel.SkelRow(1, 1, "parëa", "ccomp", 1, 5)]}
    morph_pos = {(1, 5): "noun"}
    violations = skel._classify_divergence(given, derived, {}, morph_pos)
    assert any(v.detail.startswith("role_mismatch") and v.arg == (1, 5) for v in violations)


def test_classify_divergence_explicit_ccomp_flattened_still_flagged():
    # The mirror of rule Q: the tree carried an explicit `ccomp` deprel and the LLM flattened it
    # to an object.
    derived = {1: [skel.SkelRow(1, 1, "sappi", "ccomp", 1, 3)]}
    given = {1: [skel.SkelRow(1, 1, "sappi", "obj", 1, 3)]}
    morph_pos = {(1, 3): "verb"}
    violations = skel._classify_divergence(given, derived, {}, morph_pos)
    assert any(v.detail.startswith("role_mismatch") and v.arg == (1, 3) for v in violations)


# --- _classify_divergence: Phase 5r rule U (the `case` annex as a third read) -----------


def test_case_supports_role_mapping():
    assert skel._case_supports_role("nominative", "subj")
    assert skel._case_supports_role("accusative", "obj")
    assert skel._case_supports_role("dative", "iobj")
    assert skel._case_supports_role("dative", "obl:a")
    assert skel._case_supports_role("ablative", "obl")
    assert skel._case_supports_role("locative", "obl:in")
    # `a` marks both the indirect object and a place, so `obl:a` stays compatible with both.
    assert skel._case_supports_role("locative", "obl:a")
    # No role mapping: these decide nothing either way.
    assert not skel._case_supports_role("reflexive", "obj")
    assert not skel._case_supports_role("genitive", "obl:di")
    assert not skel._case_supports_role("vocative", "subj")
    # A fused token's `SLOT_SEP`-joined value matches no single role.
    assert not skel._case_supports_role("dative+accusative", "iobj")


def test_classify_divergence_case_corroborates_derived_accepted():
    # "mi pesa": the same fixture as the rule-N test above, which stays flagged without the
    # annex — `case` says dative, which corroborates the derived `obl:a` and not the given `obj`.
    derived = {1: [skel.SkelRow(1, 2, "pesa", "obl:a", 1, 1)]}
    given = {1: [skel.SkelRow(1, 2, "pesa", "obj", 1, 1)]}
    dep_index_by_pos = {
        (1, 1): dep.DepRow(line=1, token=1, word="mi", deprel="obl", head_line=1, head_token=2),
    }
    case_by_position = {(1, 1): "dative"}
    assert skel._classify_divergence(
        given, derived, dep_index_by_pos, {(1, 1): "pronoun"}, case_by_position) == []


def test_classify_divergence_case_corroborates_given_still_flagged():
    # The mirror direction — the annex siding with the LLM against `dep` — is never an automatic
    # accept; it is a `dep`-correction candidate for hand review.
    derived = {1: [skel.SkelRow(1, 2, "pesa", "obl:a", 1, 1)]}
    given = {1: [skel.SkelRow(1, 2, "pesa", "obj", 1, 1)]}
    case_by_position = {(1, 1): "accusative"}
    violations = skel._classify_divergence(
        given, derived, {}, {(1, 1): "pronoun"}, case_by_position)
    assert any(v.detail.startswith("role_mismatch") and v.arg == (1, 1) for v in violations)


def test_classify_divergence_case_corroborating_both_sides_still_flagged():
    # `ablative` supports every oblique label, so it cannot choose between two of them. (The
    # `iobj`/`obl:a` pair can't reach here at all — Phase 1 canonicalizes `iobj` to `obl:a`.)
    derived = {1: [skel.SkelRow(1, 2, "disse", "obl:a", 1, 1)]}
    given = {1: [skel.SkelRow(1, 2, "disse", "obl:con", 1, 1)]}
    case_by_position = {(1, 1): "ablative"}
    violations = skel._classify_divergence(
        given, derived, {}, {(1, 1): "pronoun"}, case_by_position)
    assert any(v.detail.startswith("role_mismatch") and v.arg == (1, 1) for v in violations)


def test_classify_divergence_case_deciding_neither_side_still_flagged():
    # `reflexive` maps onto no role at all.
    derived = {1: [skel.SkelRow(1, 2, "volsi", "obj", 1, 1)]}
    given = {1: [skel.SkelRow(1, 2, "volsi", "subj", 1, 1)]}
    case_by_position = {(1, 1): "reflexive"}
    violations = skel._classify_divergence(
        given, derived, {}, {(1, 1): "pronoun"}, case_by_position)
    assert any(v.detail.startswith("role_mismatch") and v.arg == (1, 1) for v in violations)


def test_classify_divergence_case_on_fused_token_still_flagged():
    # `recarne` (`verb+pronoun`): the annex's `ablative` is the enclitic `ne`'s case, but the
    # argument cited here is the infinitive itself, so it decides nothing about that role.
    derived = {1: [skel.SkelRow(1, 1, "vo", "obl", 1, 2)]}
    given = {1: [skel.SkelRow(1, 1, "vo", "xcomp", 1, 2)]}
    morph_pos = {(1, 2): "verb+pronoun"}
    violations = skel._classify_divergence(given, derived, {}, morph_pos, {(1, 2): "ablative"})
    assert any(v.detail.startswith("role_mismatch") and v.arg == (1, 2) for v in violations)


def test_classify_divergence_case_absent_position_unchanged():
    # A non-pronoun argument has no row in the sparse annex, so the rule never fires.
    derived = {1: [skel.SkelRow(1, 2, "vide", "obj", 1, 3)]}
    given = {1: [skel.SkelRow(1, 2, "vide", "subj", 1, 3)]}
    violations = skel._classify_divergence(
        given, derived, {}, {(1, 1): "pronoun"}, {(1, 1): "accusative"})
    assert any(v.detail.startswith("role_mismatch") and v.arg == (1, 3) for v in violations)


# --- _find_repairs (Phase 3, PLAN.md) --------------------------------------------------


def test_find_repairs_null_subject_pairs_missing_and_extra():
    derived = {2: [skel.SkelRow(2, 2, "vede", "subj", 3, 4)]}
    given = {2: [skel.SkelRow(2, 2, "vede", "subj", 0, 0)]}
    violations = skel._classify_divergence(given, derived)
    repairs = skel._find_repairs(given, derived, violations)
    assert len(repairs) == 1
    r = repairs[0]
    assert r.kind == "null_subject"
    assert (r.before.arg_line, r.before.arg_token) == (0, 0)
    assert (r.after.arg_line, r.after.arg_token) == (3, 4)
    assert r.after.role == "subj" and r.after.line == 2 and r.after.token == 2


def test_find_repairs_null_subject_then_reclassify_is_clean():
    derived = {2: [skel.SkelRow(2, 2, "vede", "subj", 3, 4)]}
    given = {2: [skel.SkelRow(2, 2, "vede", "subj", 0, 0)]}
    violations = skel._classify_divergence(given, derived)
    repairs = skel._find_repairs(given, derived, violations)
    repaired = {2: [repairs[0].after]}
    assert skel._classify_divergence(repaired, derived) == []


def test_find_repairs_null_subject_not_produced_when_pro_drop_authoritative():
    # Same fixture as test_classify_divergence_non_finite_predicate_accepts_null_subject: the
    # authority model already accepts this, so no divergence violation reaches _find_repairs.
    derived = {1: [skel.SkelRow(1, 3, "trattar", "obl:di", 1, 5)]}
    given = {1: [
        skel.SkelRow(1, 3, "trattar", "obl:di", 1, 5),
        skel.SkelRow(1, 3, "trattar", "subj", 0, 0),
    ]}
    dep_index_by_pos = {
        (1, 3): dep.DepRow(line=1, token=3, word="trattar", deprel="advcl", head_line=1, head_token=1),
    }
    violations = skel._classify_divergence(given, derived, dep_index_by_pos)
    assert violations == []
    assert skel._find_repairs(given, derived, violations) == []


def test_find_repairs_null_subject_not_produced_for_xcomp_control_accept():
    # Same fixture as test_classify_divergence_xcomp_control_subject_accepts_matrix_arg.
    matrix = skel.SkelRow(2, 2, "vuole", "subj", 2, 1)
    matrix_xcomp = skel.SkelRow(2, 2, "vuole", "xcomp", 2, 3)
    derived = {2: [matrix, matrix_xcomp, skel.SkelRow(2, 3, "partire", "", 0, 0)]}
    given = {2: [
        skel.SkelRow(2, 2, "vuole", "subj", 2, 1),
        skel.SkelRow(2, 2, "vuole", "xcomp", 2, 3),
        skel.SkelRow(2, 3, "partire", "subj", 2, 1),
    ]}
    dep_index_by_pos = {
        (2, 3): dep.DepRow(line=2, token=3, word="partire", deprel="xcomp", head_line=2, head_token=2),
    }
    violations = skel._classify_divergence(given, derived, dep_index_by_pos)
    assert violations == []
    assert skel._find_repairs(given, derived, violations) == []


def test_find_repairs_null_subject_not_produced_for_genuine_disagreement():
    # Both sides cite a real (non-∅) subject, just a different one — not the ∅-vs-real shape
    # rule 1 requires.
    derived = {2: [skel.SkelRow(2, 2, "vede", "subj", 3, 4)]}
    given = {2: [skel.SkelRow(2, 2, "vede", "subj", 5, 1)]}
    violations = skel._classify_divergence(given, derived)
    assert skel._find_repairs(given, derived, violations) == []


def test_find_repairs_role_label_bare_obl_to_lemma():
    derived = {2: [skel.SkelRow(2, 2, "pred", "obl:di", 1, 3)]}
    given = {2: [skel.SkelRow(2, 2, "pred", "obl", 1, 3)]}
    violations = skel._classify_divergence(given, derived)
    repairs = skel._find_repairs(given, derived, violations)
    assert len(repairs) == 1
    r = repairs[0]
    assert r.kind == "role_label"
    assert r.before.role == "obl" and r.after.role == "obl:di"
    assert (r.after.arg_line, r.after.arg_token) == (1, 3)


def test_find_repairs_role_label_then_reclassify_is_clean():
    derived = {2: [skel.SkelRow(2, 2, "pred", "obl:di", 1, 3)]}
    given = {2: [skel.SkelRow(2, 2, "pred", "obl", 1, 3)]}
    violations = skel._classify_divergence(given, derived)
    repairs = skel._find_repairs(given, derived, violations)
    repaired = {2: [repairs[0].after]}
    assert skel._classify_divergence(repaired, derived) == []


def test_find_repairs_role_label_rejects_subj_obj_reversal():
    derived = {2: [skel.SkelRow(2, 2, "pred", "obj", 1, 3)]}
    given = {2: [skel.SkelRow(2, 2, "pred", "subj", 1, 3)]}
    violations = skel._classify_divergence(given, derived)
    assert any(v.detail.startswith("role_mismatch") for v in violations)
    assert skel._find_repairs(given, derived, violations) == []


def test_find_repairs_role_label_rejects_different_obl_lemma():
    derived = {2: [skel.SkelRow(2, 2, "pred", "obl:di", 1, 3)]}
    given = {2: [skel.SkelRow(2, 2, "pred", "obl:con", 1, 3)]}
    violations = skel._classify_divergence(given, derived)
    assert any(v.detail.startswith("role_mismatch") for v in violations)
    assert skel._find_repairs(given, derived, violations) == []


def test_find_repairs_role_label_rejects_iobj_obj_reversal():
    derived = {2: [skel.SkelRow(2, 2, "pred", "obj", 1, 3)]}
    given = {2: [skel.SkelRow(2, 2, "pred", "iobj", 1, 3)]}
    violations = skel._classify_divergence(given, derived)
    assert skel._find_repairs(given, derived, violations) == []


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


def test_is_verb_pos_does_not_match_adverb():
    assert skel.is_verb_pos("verb")
    assert skel.is_verb_pos("verb+pronoun")
    assert skel.is_verb_pos("conjunction+pronoun+verb")
    assert skel.is_verb_pos("adverb+verb")
    assert not skel.is_verb_pos("adverb")
    assert not skel.is_verb_pos("preposition+adverb")
    assert not skel.is_verb_pos("noun")


def test_derive_unit_does_not_promote_an_adverb_with_an_oblique():
    """Rule 2 promotes an argument-bearing *verb*; `altrimenti` is an adverb, not a predicate."""
    from dante_corpus.dep import DepRow
    from dante_corpus.morph import MorphRow

    nos = [1]
    dep_rows = {1: [
        DepRow(1, 1, "nuota", "root", 0, 0),
        DepRow(1, 2, "altrimenti", "advmod", 1, 1),
        DepRow(1, 3, "Serchio", "obl", 1, 2),
    ]}
    morph_rows = {1: [
        MorphRow(word="nuota", pos="verb"),
        MorphRow(word="altrimenti", pos="adverb"),
        MorphRow(word="Serchio", pos="proper noun"),
    ]}
    derived = skel.derive_unit(nos, dep_rows, morph_rows)
    assert {(r.line, r.token) for r in derived[1]} == {(1, 1)}
