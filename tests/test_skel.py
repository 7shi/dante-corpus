"""Deterministic tests for Layer 5 predicate-argument skeleton (no model calls)."""

from dante_corpus import api, case, dep, morph, skel

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


# --- _classify_divergence: rule V, the control/participial subject chain --------------


def test_classify_divergence_adnominal_participle_subject_is_modified_noun():
    # "vidi le sue spalle / vestite già de' raggi": `vestite` is an `acl` on `spalle` (16.8),
    # which is its subject. derive_unit reads only the participle's own children, so it is
    # silent about the subject.
    derived = {17: [skel.SkelRow(17, 1, "vestite", "obl:di", 17, 4)]}
    given = {17: [
        skel.SkelRow(17, 1, "vestite", "subj", 16, 8),
        skel.SkelRow(17, 1, "vestite", "obl:di", 17, 4),
    ]}
    dep_index_by_pos = {
        (17, 1): dep.DepRow(line=17, token=1, word="vestite", deprel="acl", head_line=16, head_token=8),
    }
    assert skel._classify_divergence(given, derived, dep_index_by_pos) == []


def test_classify_divergence_control_subject_two_links_up():
    # "e molte genti fé già viver grame": `grame` is an xcomp of `viver`, itself an xcomp of
    # `fé`, whose object `genti` (51.3) is the subject of both. Neither non-finite link has a
    # subject of its own, so the walk has to cross `viver` to reach it.
    derived = {51: [
        skel.SkelRow(51, 4, "fé", "obj", 51, 3),
        skel.SkelRow(51, 4, "fé", "xcomp", 51, 6),
        skel.SkelRow(51, 6, "viver", "xcomp", 51, 7),
        skel.SkelRow(51, 7, "grame", "", 0, 0),
    ]}
    given = {51: [
        skel.SkelRow(51, 4, "fé", "obj", 51, 3),
        skel.SkelRow(51, 4, "fé", "xcomp", 51, 6),
        skel.SkelRow(51, 6, "viver", "subj", 51, 3),
        skel.SkelRow(51, 7, "grame", "subj", 51, 3),
    ]}
    dep_index_by_pos = {
        (51, 6): dep.DepRow(line=51, token=6, word="viver", deprel="xcomp", head_line=51, head_token=4),
        (51, 7): dep.DepRow(line=51, token=7, word="grame", deprel="xcomp", head_line=51, head_token=6),
    }
    violations = skel._classify_divergence(given, derived, dep_index_by_pos)
    assert [v.detail for v in violations if v.detail.startswith("extra_arg")] == []


def test_classify_divergence_causative_dative_causee_is_control_subject():
    # "ch'ella mi fa tremar le vene": the causee `mi` (90.3) is an `iobj` of `fa` and the
    # subject of `tremar` — object control through the dative, not the accusative.
    derived = {90: [
        skel.SkelRow(90, 4, "fa", "subj", 90, 2),
        skel.SkelRow(90, 4, "fa", "iobj", 90, 3),
        skel.SkelRow(90, 4, "fa", "xcomp", 90, 5),
        skel.SkelRow(90, 5, "tremar", "obj", 90, 7),
    ]}
    given = {90: [
        skel.SkelRow(90, 4, "fa", "subj", 90, 2),
        skel.SkelRow(90, 4, "fa", "iobj", 90, 3),
        skel.SkelRow(90, 4, "fa", "xcomp", 90, 5),
        skel.SkelRow(90, 5, "tremar", "subj", 90, 3),
        skel.SkelRow(90, 5, "tremar", "obj", 90, 7),
    ]}
    dep_index_by_pos = {
        (90, 5): dep.DepRow(line=90, token=5, word="tremar", deprel="xcomp", head_line=90, head_token=4),
    }
    assert skel._classify_divergence(given, derived, dep_index_by_pos) == []


def test_classify_divergence_control_subject_of_pro_drop_matrix_is_llm_authoritative():
    # "chi per lungo silenzio parea fioco": `fioco` is an xcomp of `parea`, whose own subject
    # derive_unit can only give as pro-drop ∅. The controller is a referent the derivation never
    # resolved, so it cannot adjudicate the LLM's resolution of it either.
    derived = {63: [
        skel.SkelRow(63, 5, "parea", "subj", 0, 0),
        skel.SkelRow(63, 5, "parea", "xcomp", 63, 6),
        skel.SkelRow(63, 6, "fioco", "", 0, 0),
    ]}
    given = {63: [
        skel.SkelRow(63, 5, "parea", "subj", 63, 1),
        skel.SkelRow(63, 5, "parea", "xcomp", 63, 6),
        skel.SkelRow(63, 6, "fioco", "subj", 63, 1),
    ]}
    dep_index_by_pos = {
        (63, 6): dep.DepRow(line=63, token=6, word="fioco", deprel="xcomp", head_line=63, head_token=5),
    }
    assert skel._classify_divergence(given, derived, dep_index_by_pos) == []


def test_classify_divergence_control_walk_stops_at_subject_bearing_ancestor():
    # The walk climbs only through subjectless links. Once an ancestor has a subject of its
    # own, that clause supplies the controller; a subject taken from beyond it is a genuine
    # reading disagreement, not derive_unit's silence.
    derived = {3: [
        skel.SkelRow(3, 1, "disse", "subj", 3, 2),
        skel.SkelRow(3, 1, "disse", "ccomp", 3, 3),
        skel.SkelRow(3, 3, "vuole", "subj", 3, 4),
        skel.SkelRow(3, 3, "vuole", "xcomp", 3, 5),
        skel.SkelRow(3, 5, "partire", "", 0, 0),
    ]}
    given = {3: [
        skel.SkelRow(3, 1, "disse", "subj", 3, 2),
        skel.SkelRow(3, 1, "disse", "ccomp", 3, 3),
        skel.SkelRow(3, 3, "vuole", "subj", 3, 4),
        skel.SkelRow(3, 3, "vuole", "xcomp", 3, 5),
        skel.SkelRow(3, 5, "partire", "subj", 3, 2),  # the *matrix* subject, past `vuole`
    ]}
    dep_index_by_pos = {
        (3, 3): dep.DepRow(line=3, token=3, word="vuole", deprel="ccomp", head_line=3, head_token=1),
        (3, 5): dep.DepRow(line=3, token=5, word="partire", deprel="xcomp", head_line=3, head_token=3),
    }
    violations = skel._classify_divergence(given, derived, dep_index_by_pos)
    assert any(v.detail.startswith("extra_arg") and v.arg == (3, 2) for v in violations)


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


def test_classify_divergence_copula_of_underived_nominal_accepted():
    # Rule BS: the copula's head is not a derived predicate, but it *is* the nominal rule Y calls
    # a predication — Layer 4's own `cop` edge asserts one, whatever deprel the nominal carries
    # ("e cortesia fu lui **esser villano**", inferno 33:150). Naming that predication by its
    # copula is the same labeling split `_aux_of_derived_predicate` accepts when the head happens
    # to be derived, so the citation is read through `_aux_head` first.
    derived = {1: []}
    given = {1: [skel.SkelRow(1, 2, "son", "subj", 1, 4)]}
    dep_index_by_pos = {
        (1, 1): dep.DepRow(line=1, token=1, word="Molti", deprel="amod", head_line=1, head_token=4),
        (1, 2): dep.DepRow(line=1, token=2, word="son", deprel="cop", head_line=1, head_token=1),
    }
    assert skel._classify_divergence(given, derived, dep_index_by_pos, {}) == []


def test_classify_divergence_non_copula_extra_tuple_still_flagged():
    # Rule BS's near miss: the same underived predicate with no `cop`/`aux` edge anywhere is a
    # genuine extra tuple, and stays reported.
    derived = {1: []}
    given = {1: [skel.SkelRow(1, 2, "vede", "subj", 1, 4)]}
    dep_index_by_pos = {
        (1, 1): dep.DepRow(line=1, token=1, word="Molti", deprel="amod", head_line=1, head_token=4),
        (1, 2): dep.DepRow(line=1, token=2, word="vede", deprel="amod", head_line=1, head_token=1),
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


def test_classify_divergence_co_present_preposition_fixed_member_accepted():
    # "in su le porte" after the dep/ multiword-preposition normalization: `in` is the nominal's
    # `case` child and `su` hangs off `in` as `fixed`. The fixed member still names a
    # preposition of the same PP, so rule O accepts it exactly as it did when Layer 4 attached
    # both members flat.
    derived = {1: [skel.SkelRow(1, 1, "vidi", "obl:in", 1, 4)]}
    given = {1: [skel.SkelRow(1, 1, "vidi", "obl:su", 1, 4)]}
    dep_index_by_pos = {
        (1, 2): dep.DepRow(line=1, token=2, word="in", deprel="case", head_line=1, head_token=4),
        (1, 3): dep.DepRow(line=1, token=3, word="su", deprel="fixed", head_line=1, head_token=2),
        (1, 4): dep.DepRow(line=1, token=4, word="porte", deprel="obl", head_line=1, head_token=1),
    }
    assert skel._classify_divergence(given, derived, dep_index_by_pos) == []


def test_classify_divergence_co_present_preposition_fixed_absent_still_flagged():
    # Mirror: the normalized tree carries `in` (case) and `su` (fixed) but the LLM names `di`,
    # which no member of the stack spells — a genuine disagreement about what is attached.
    derived = {1: [skel.SkelRow(1, 1, "vidi", "obl:in", 1, 4)]}
    given = {1: [skel.SkelRow(1, 1, "vidi", "obl:di", 1, 4)]}
    dep_index_by_pos = {
        (1, 2): dep.DepRow(line=1, token=2, word="in", deprel="case", head_line=1, head_token=4),
        (1, 3): dep.DepRow(line=1, token=3, word="su", deprel="fixed", head_line=1, head_token=2),
        (1, 4): dep.DepRow(line=1, token=4, word="porte", deprel="obl", head_line=1, head_token=1),
    }
    violations = skel._classify_divergence(given, derived, dep_index_by_pos)
    assert any(v.detail.startswith("role_mismatch") and v.arg == (1, 4) for v in violations)


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


# --- _find_repairs (Phase 3, PLAN.md; tier-A/tier-B division) --------------------------

# The `null_subject` rule is tier B — it asserts a reading, so it fires only where Layer 2's
# person/number corroborates the derived subject independently of Layer 4 (`dep.
# subject_agreement`). These fixtures supply that corroboration; the ones below withhold it.
_NULL_SUBJ_DERIVED = {2: [skel.SkelRow(2, 2, "vede", "subj", 3, 4)]}
_NULL_SUBJ_GIVEN = {2: [skel.SkelRow(2, 2, "vede", "subj", 0, 0)]}


def _agreeing_morph(head_person="3", head_number="sg.", subj_number="sg."):
    """Layer-2 rows for the `null_subject` fixture: a finite 3sg verb at 2.2 and a noun at 3.4."""
    return {
        2: [morph.MorphRow(word="ei", pos="pronoun"),
            morph.MorphRow(word="vede", lemma="vedere", pos="verb", person=head_person,
                           number=head_number, tense="present", mood="indicative")],
        3: [morph.MorphRow(word="a", pos="preposition"),
            morph.MorphRow(word="la", pos="article"),
            morph.MorphRow(word="bella", pos="adjective"),
            morph.MorphRow(word="donna", lemma="donna", pos="noun", number=subj_number)],
    }


def test_find_repairs_null_subject_pairs_missing_and_extra():
    violations = skel._classify_divergence(_NULL_SUBJ_GIVEN, _NULL_SUBJ_DERIVED)
    repairs = skel._find_repairs(_NULL_SUBJ_GIVEN, _NULL_SUBJ_DERIVED, violations,
                                 _agreeing_morph())
    assert len(repairs) == 1
    r = repairs[0]
    assert r.kind == "null_subject"
    assert (r.before.arg_line, r.before.arg_token) == (0, 0)
    assert (r.after.arg_line, r.after.arg_token) == (3, 4)
    assert r.after.role == "subj" and r.after.line == 2 and r.after.token == 2


def test_find_repairs_null_subject_then_reclassify_is_clean():
    violations = skel._classify_divergence(_NULL_SUBJ_GIVEN, _NULL_SUBJ_DERIVED)
    repairs = skel._find_repairs(_NULL_SUBJ_GIVEN, _NULL_SUBJ_DERIVED, violations,
                                 _agreeing_morph())
    repaired = {2: [repairs[0].after]}
    assert skel._classify_divergence(repaired, _NULL_SUBJ_DERIVED) == []


def test_find_repairs_null_subject_refused_without_morph_corroboration():
    # Tier B's gate. The shape is exactly the one the rule targets, but with no Layer-2 rows
    # `dep.subject_agreement` returns "undecidable" — and undecidable is not a weak yes.
    violations = skel._classify_divergence(_NULL_SUBJ_GIVEN, _NULL_SUBJ_DERIVED)
    assert skel._find_repairs(_NULL_SUBJ_GIVEN, _NULL_SUBJ_DERIVED, violations) == []


def test_find_repairs_null_subject_refused_when_layers_disagree():
    # A plural subject under a singular verb: the two frozen layers contradict each other, so
    # the derived subject is as likely to be the wrong side. PLAN.md's warning about running
    # this rule blind is exactly this position.
    violations = skel._classify_divergence(_NULL_SUBJ_GIVEN, _NULL_SUBJ_DERIVED)
    morph_rows = _agreeing_morph(subj_number="pl.")
    assert skel._find_repairs(_NULL_SUBJ_GIVEN, _NULL_SUBJ_DERIVED, violations, morph_rows) == []


def test_find_repairs_null_subject_refused_for_relative_pronoun_subject():
    # `che` takes its person from its antecedent, so Layer 2's own row corroborates nothing.
    morph_rows = _agreeing_morph()
    morph_rows[3][3] = morph.MorphRow(word="che", lemma="che", pos="pronoun", person="3")
    violations = skel._classify_divergence(_NULL_SUBJ_GIVEN, _NULL_SUBJ_DERIVED)
    assert skel._find_repairs(_NULL_SUBJ_GIVEN, _NULL_SUBJ_DERIVED, violations, morph_rows) == []


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


def test_find_repairs_prep_stack_accepts_chained_preposition():
    # "in su la cima": Layer 4 chains `in` -> `su` -> `cima`, so the derivation names the
    # preposition adjacent to the nominal and the LLM the one that opens the phrase. Tier A —
    # one PP spelled two ways, no reading asserted.
    derived = {2: [skel.SkelRow(2, 2, "fui", "obl:su", 1, 3)]}
    given = {2: [skel.SkelRow(2, 2, "fui", "obl:in", 1, 3)]}
    dep_rows = {1: [
        dep.DepRow(line=1, token=1, word="in", deprel="case", head_line=1, head_token=2),
        dep.DepRow(line=1, token=2, word="su", deprel="case", head_line=1, head_token=3),
    ]}
    violations = skel._classify_divergence(given, derived)
    repairs = skel._find_repairs(given, derived, violations, None, dep_rows)
    assert len(repairs) == 1
    assert repairs[0].kind == "prep_stack"
    assert repairs[0].before.role == "obl:in" and repairs[0].after.role == "obl:su"
    assert skel._classify_divergence({2: [repairs[0].after]}, derived) == []


def test_find_repairs_prep_stack_rejects_preposition_absent_from_the_tree():
    # Same role pair, but Layer 4 attached only `su` and never `in` — the tree and the reading
    # differ about what is attached, which is a dep-normalization question, not a relabeling.
    derived = {2: [skel.SkelRow(2, 2, "fui", "obl:su", 1, 3)]}
    given = {2: [skel.SkelRow(2, 2, "fui", "obl:in", 1, 3)]}
    dep_rows = {1: [
        dep.DepRow(line=1, token=2, word="su", deprel="case", head_line=1, head_token=3),
    ]}
    violations = skel._classify_divergence(given, derived)
    assert skel._find_repairs(given, derived, violations, None, dep_rows) == []


def test_find_repairs_prep_stack_rejects_flat_sibling_prepositions():
    # Both prepositions are `case` children of the nominal itself, not stacked one on the other.
    # `_stacked_prep_lemmas` walks *from* the argument, so both are reachable and the rule fires;
    # this pins that the walk starts at the argument rather than requiring a chain of depth 2.
    derived = {2: [skel.SkelRow(2, 2, "sta", "obl:a", 1, 3)]}
    given = {2: [skel.SkelRow(2, 2, "sta", "obl:dentro", 1, 3)]}
    dep_rows = {1: [
        dep.DepRow(line=1, token=1, word="dentro", deprel="case", head_line=1, head_token=3),
        dep.DepRow(line=1, token=2, word="al", deprel="case", head_line=1, head_token=3),
    ]}
    violations = skel._classify_divergence(given, derived)
    repairs = skel._find_repairs(given, derived, violations, None, dep_rows)
    assert [r.kind for r in repairs] == ["prep_stack"]


def test_find_repairs_prep_stack_reaches_fixed_member():
    # "in su la cima" after the dep/ multiword-preposition normalization: `in` is the nominal's
    # `case` child, `su` its `fixed` child. The stack walk must reach the fixed member, so the
    # two readings naming different members of one stack still repair to one label.
    derived = {2: [skel.SkelRow(2, 2, "fui", "obl:in", 1, 3)]}
    given = {2: [skel.SkelRow(2, 2, "fui", "obl:su", 1, 3)]}
    dep_rows = {1: [
        dep.DepRow(line=1, token=1, word="in", deprel="case", head_line=1, head_token=3),
        dep.DepRow(line=1, token=2, word="su", deprel="fixed", head_line=1, head_token=1),
    ]}
    violations = skel._classify_divergence(given, derived)
    repairs = skel._find_repairs(given, derived, violations, None, dep_rows)
    assert len(repairs) == 1
    assert repairs[0].kind == "prep_stack"
    assert repairs[0].before.role == "obl:su" and repairs[0].after.role == "obl:in"
    assert skel._classify_divergence({2: [repairs[0].after]}, derived) == []


def test_find_repairs_prep_stack_needs_dep_rows():
    derived = {2: [skel.SkelRow(2, 2, "fui", "obl:su", 1, 3)]}
    given = {2: [skel.SkelRow(2, 2, "fui", "obl:in", 1, 3)]}
    violations = skel._classify_divergence(given, derived)
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


# --- _classify_divergence: rule W (the swap partner of a rule-U accept) -----------------


def test_classify_divergence_case_corroborated_swap_partner_accepted():
    # "lo passo che non lasciò già mai persona viva" (inferno 1:27). Layer 4 reads `che` as the
    # subject and `persona` as the object; the LLM inverted both. The annex reads `che` as
    # `nominative`, so rule U accepts that leg — and `persona`, a noun and so out of the annex's
    # scope, is the same decision reported a second time.
    derived = {1: [skel.SkelRow(1, 3, "lasciò", "subj", 1, 1),
                   skel.SkelRow(1, 3, "lasciò", "obj", 1, 6)]}
    given = {1: [skel.SkelRow(1, 3, "lasciò", "obj", 1, 1),
                 skel.SkelRow(1, 3, "lasciò", "subj", 1, 6)]}
    morph_pos = {(1, 1): "pronoun", (1, 6): "noun"}
    assert skel._classify_divergence(
        given, derived, {}, morph_pos, {(1, 1): "nominative"}) == []


def test_classify_divergence_swap_partner_without_the_annex_still_flagged():
    # The same inversion with no annex value for either leg decides nothing: both stay flagged.
    derived = {1: [skel.SkelRow(1, 3, "lasciò", "subj", 1, 1),
                   skel.SkelRow(1, 3, "lasciò", "obj", 1, 6)]}
    given = {1: [skel.SkelRow(1, 3, "lasciò", "obj", 1, 1),
                 skel.SkelRow(1, 3, "lasciò", "subj", 1, 6)]}
    morph_pos = {(1, 1): "pronoun", (1, 6): "noun"}
    violations = skel._classify_divergence(given, derived, {}, morph_pos, {})
    assert {v.arg for v in violations if v.detail.startswith("role_mismatch")} == {(1, 1), (1, 6)}


def test_classify_divergence_swap_partner_not_an_inversion_still_flagged():
    # The partner disagreement is `obl:a` vs `obj`, not this argument's two roles exchanged, so
    # the annex never adjudicated the subject question: the gate is the exchange, not
    # co-presence under one predicate.
    derived = {1: [skel.SkelRow(1, 3, "disse", "obl:a", 1, 1),
                   skel.SkelRow(1, 3, "disse", "obj", 1, 6)]}
    given = {1: [skel.SkelRow(1, 3, "disse", "obj", 1, 1),
                 skel.SkelRow(1, 3, "disse", "subj", 1, 6)]}
    morph_pos = {(1, 1): "pronoun", (1, 6): "noun"}
    violations = skel._classify_divergence(
        given, derived, {}, morph_pos, {(1, 1): "dative"})
    assert any(v.detail.startswith("role_mismatch") and v.arg == (1, 6) for v in violations)


def test_classify_divergence_swap_partner_mirror_direction_still_flagged():
    # One-directional like rule U: the annex siding with the LLM accepts nothing, on either leg.
    derived = {1: [skel.SkelRow(1, 3, "lasciò", "subj", 1, 1),
                   skel.SkelRow(1, 3, "lasciò", "obj", 1, 6)]}
    given = {1: [skel.SkelRow(1, 3, "lasciò", "obj", 1, 1),
                 skel.SkelRow(1, 3, "lasciò", "subj", 1, 6)]}
    morph_pos = {(1, 1): "pronoun", (1, 6): "noun"}
    violations = skel._classify_divergence(
        given, derived, {}, morph_pos, {(1, 1): "accusative"})
    assert {v.arg for v in violations if v.detail.startswith("role_mismatch")} == {(1, 1), (1, 6)}


# --- _classify_divergence: rule X (the argument side of the copula convention) ----------


def _copular_dep(head_token: int, complement_token: int, arg_token: int):
    from dante_corpus.dep import DepRow
    return {
        (1, complement_token): DepRow(line=1, token=complement_token, word="contenti",
                                      deprel="attr", head_line=1, head_token=head_token),
        (1, arg_token): DepRow(line=1, token=arg_token, word="foco", deprel="obl",
                               head_line=1, head_token=head_token),
    }


def test_classify_divergence_argument_on_the_complement_accepted():
    # "color che son contenti / nel foco" (inferno 1:118). Layer 4 hangs the oblique on the
    # copula `son`; the LLM hangs it on `contenti`, which it also lists as `son`'s `attr`.
    derived = {1: [skel.SkelRow(1, 5, "son", "attr", 1, 6),
                   skel.SkelRow(1, 5, "son", "obl:in", 1, 9)]}
    given = {1: [skel.SkelRow(1, 5, "son", "attr", 1, 6),
                 skel.SkelRow(1, 6, "contenti", "obl:in", 1, 9)]}
    assert skel._classify_divergence(given, derived, _copular_dep(5, 6, 9), {}) == []


def test_classify_divergence_argument_on_the_complement_mirror_leg_accepted():
    # "a costor si vuole esser cortese" (inferno 16:15): derive_unit promotes the complement
    # too, so the same convention was costing a `missing_arg` on the copula *and* an
    # `extra_arg` on the complement. Both legs are closed.
    derived = {1: [skel.SkelRow(1, 5, "son", "attr", 1, 6),
                   skel.SkelRow(1, 5, "son", "obl:in", 1, 9),
                   skel.SkelRow(1, 6, "contenti", "subj", 1, 1)]}
    given = {1: [skel.SkelRow(1, 5, "son", "attr", 1, 6),
                 skel.SkelRow(1, 6, "contenti", "subj", 1, 1),
                 skel.SkelRow(1, 6, "contenti", "obl:in", 1, 9)]}
    violations = skel._classify_divergence(given, derived, _copular_dep(5, 6, 9), {})
    assert [v.detail for v in violations] == []


def test_classify_divergence_argument_on_the_complement_relabelled_still_flagged():
    # Relocating the argument is the convention; relabelling it is a second claim, and only the
    # relocation is accepted.
    derived = {1: [skel.SkelRow(1, 5, "son", "attr", 1, 6),
                   skel.SkelRow(1, 5, "son", "obl:in", 1, 9)]}
    given = {1: [skel.SkelRow(1, 5, "son", "attr", 1, 6),
                 skel.SkelRow(1, 6, "contenti", "obl:su", 1, 9)]}
    violations = skel._classify_divergence(given, derived, _copular_dep(5, 6, 9), {})
    assert any(v.detail.startswith("missing_arg") and v.arg == (1, 9) for v in violations)


def test_classify_divergence_argument_on_a_non_complement_still_flagged():
    # Layer 4 does not attach the second predicate to the first as `attr`/`xcomp`, so the two
    # layers never agreed the pair forms one predication: this is a real relocation.
    from dante_corpus.dep import DepRow
    derived = {1: [skel.SkelRow(1, 5, "son", "attr", 1, 6),
                   skel.SkelRow(1, 5, "son", "obl:in", 1, 9)]}
    given = {1: [skel.SkelRow(1, 5, "son", "attr", 1, 6),
                 skel.SkelRow(1, 6, "contenti", "obl:in", 1, 9)]}
    dep_index = dict(_copular_dep(5, 6, 9))
    dep_index[(1, 6)] = DepRow(line=1, token=6, word="contenti", deprel="conj",
                               head_line=1, head_token=5)
    violations = skel._classify_divergence(given, derived, dep_index, {})
    assert any(v.detail.startswith("missing_arg") and v.arg == (1, 9) for v in violations)


# --- _classify_divergence: rules Y-AF (the 2026-08-12 Inferno 1-3 re-read) ---------------


def _row(line: int, token: int, word: str, deprel: str, head_token: int, head_line: int = 1):
    from dante_corpus.dep import DepRow
    return DepRow(line=line, token=token, word=word, deprel=deprel,
                  head_line=head_line, head_token=head_token)


def test_classify_divergence_copular_predication_under_a_nominal_deprel_accepted():
    # Rule Y. "per non esser men belli" (inferno 3:40): the tree gives `belli` a `cop` child and
    # then attaches it as `obl`, so derive_unit never proposes the predication its own copula
    # edge asserts.
    derived = {1: [skel.SkelRow(1, 1, "Caccianli", "subj", 1, 3)]}
    given = {1: [skel.SkelRow(1, 1, "Caccianli", "subj", 1, 3),
                 skel.SkelRow(1, 8, "belli", "subj", 0, 0)]}
    dep_index = {(1, 8): _row(1, 8, "belli", "obl", 1),
                 (1, 6): _row(1, 6, "esser", "cop", 8)}
    assert skel._classify_divergence(given, derived, dep_index, {}) == []


def test_classify_divergence_nominal_predicate_without_a_copula_edge_still_flagged():
    # Without the `cop` edge nothing in the tree asserts a predication there, and the deprel is
    # outside `_ELIDED_COPULA_DEPRELS`, so the promotion stays a genuine divergence.
    derived = {1: [skel.SkelRow(1, 1, "Caccianli", "subj", 1, 3)]}
    given = {1: [skel.SkelRow(1, 1, "Caccianli", "subj", 1, 3),
                 skel.SkelRow(1, 8, "belli", "subj", 0, 0)]}
    dep_index = {(1, 8): _row(1, 8, "belli", "obl", 1)}
    violations = skel._classify_divergence(given, derived, dep_index, {(1, 8): "adjective"})
    assert any(v.detail.startswith("extra_tuple") for v in violations)


def test_classify_divergence_verb_in_an_argument_slot_accepted_on_both_legs():
    # Rule Z. "fui per ritornar più volte vòlto" (inferno 1:36): `ritornar` is an `obl` with
    # `per` as its `case` child. The LLM gives it a tuple; the derivation reports it as the
    # host's oblique. One decision, and it was being reported twice.
    derived = {1: [skel.SkelRow(1, 8, "vòlto", "obl:per", 1, 5)]}
    given = {1: [skel.SkelRow(1, 8, "vòlto", "subj", 0, 0),
                 skel.SkelRow(1, 5, "ritornar", "subj", 0, 0)]}
    dep_index = {(1, 5): _row(1, 5, "ritornar", "obl", 8),
                 (1, 8): _row(1, 8, "vòlto", "advcl", 2)}
    derived[1].append(skel.SkelRow(1, 8, "vòlto", "subj", 0, 0))
    assert skel._classify_divergence(
        given, derived, dep_index, {(1, 5): "verb", (1, 8): "adjective"}) == []


def test_classify_divergence_non_verb_in_an_argument_slot_still_flagged():
    # The rule turns on Layer 2 calling the token a verb: a noun in the same slot is not a
    # predicate under either reading.
    derived = {1: [skel.SkelRow(1, 8, "vòlto", "subj", 0, 0)]}
    given = {1: [skel.SkelRow(1, 8, "vòlto", "subj", 0, 0),
                 skel.SkelRow(1, 5, "ritorno", "subj", 0, 0)]}
    dep_index = {(1, 5): _row(1, 5, "ritorno", "obl", 8),
                 (1, 8): _row(1, 8, "vòlto", "advcl", 2)}
    violations = skel._classify_divergence(
        given, derived, dep_index, {(1, 5): "noun", (1, 8): "adjective"})
    assert any(v.detail.startswith("extra_tuple") for v in violations)


def test_classify_divergence_inherited_subject_echo_accepted():
    # Rule AC. "Questa chiese Lucia ... e disse" (inferno 2:97-98): `disse` has no subject of its
    # own, so both sides copy the coordination head's, and the disagreement is the head's.
    derived = {1: [skel.SkelRow(1, 2, "chiese", "subj", 1, 1),
                   skel.SkelRow(1, 5, "disse", "subj", 1, 1)]}
    given = {1: [skel.SkelRow(1, 2, "chiese", "subj", 1, 3),
                 skel.SkelRow(1, 5, "disse", "subj", 1, 3)]}
    dep_index = {(1, 5): _row(1, 5, "disse", "conj", 2),
                 (1, 1): _row(1, 1, "Questa", "nsubj", 2),
                 (1, 3): _row(1, 3, "Lucia", "obj", 2)}
    violations = skel._classify_divergence(given, derived, dep_index, {})
    assert {v.predicate for v in violations} == {(1, 2)}  # reported once, at the head


def test_classify_divergence_conjunct_with_its_own_subject_still_flagged():
    # A conjunct the tree gives a subject of its own is making an independent claim, so the
    # echo rule does not apply to it.
    derived = {1: [skel.SkelRow(1, 5, "disse", "subj", 1, 1)]}
    given = {1: [skel.SkelRow(1, 5, "disse", "subj", 1, 3)]}
    dep_index = {(1, 5): _row(1, 5, "disse", "conj", 2),
                 (1, 1): _row(1, 1, "Questa", "nsubj", 5)}
    violations = skel._classify_divergence(given, derived, dep_index, {})
    assert {v.predicate for v in violations} == {(1, 5)}


def test_classify_divergence_secondary_predicate_over_an_argument_accepted():
    # Rule AA. "Queste parole ... vid' ïo scritte" (inferno 3:11): the participle is an `acl` of
    # the object noun, outside ARG_DEPRELS, so the derivation cannot report it at all.
    derived = {1: [skel.SkelRow(1, 1, "vid'", "obj", 1, 4)]}
    given = {1: [skel.SkelRow(1, 1, "vid'", "obj", 1, 4),
                 skel.SkelRow(1, 1, "vid'", "xcomp", 1, 6)]}
    dep_index = {(1, 6): _row(1, 6, "scritte", "acl", 4)}
    derived[1].append(skel.SkelRow(1, 6, "scritte", "", 0, 0))
    given[1].append(skel.SkelRow(1, 6, "scritte", "", 0, 0))
    assert skel._classify_divergence(given, derived, dep_index, {}) == []


def test_classify_divergence_acl_on_an_unrelated_nominal_still_flagged():
    derived = {1: [skel.SkelRow(1, 1, "vid'", "obj", 1, 4)]}
    given = {1: [skel.SkelRow(1, 1, "vid'", "obj", 1, 4),
                 skel.SkelRow(1, 1, "vid'", "xcomp", 1, 6)]}
    dep_index = {(1, 6): _row(1, 6, "scritte", "acl", 9)}
    derived[1].append(skel.SkelRow(1, 6, "scritte", "", 0, 0))
    given[1].append(skel.SkelRow(1, 6, "scritte", "", 0, 0))
    violations = skel._classify_divergence(given, derived, dep_index, {})
    assert any(v.detail.startswith("extra_arg") and v.arg == (1, 6) for v in violations)


def test_classify_divergence_reflexive_clitic_read_as_an_argument_accepted():
    # Rule AB. "tal mi fec' ïo" (inferno 2:40): Layer 4 writes the reflexive as `expl`, which is
    # outside ARG_DEPRELS, so the derivation says nothing about it.
    derived = {1: [skel.SkelRow(1, 3, "fec'", "subj", 1, 4)]}
    given = {1: [skel.SkelRow(1, 3, "fec'", "subj", 1, 4),
                 skel.SkelRow(1, 3, "fec'", "obj", 1, 2)]}
    dep_index = {(1, 2): _row(1, 2, "mi", "expl", 3)}
    assert skel._classify_divergence(given, derived, dep_index, {(1, 2): "pronoun"}) == []


def test_classify_divergence_reflexive_clitic_with_an_absent_preposition_still_flagged():
    # Only the roles a bare clitic can carry are accepted; naming a preposition the tree does
    # not carry is a second claim.
    derived = {1: [skel.SkelRow(1, 3, "fec'", "subj", 1, 4)]}
    given = {1: [skel.SkelRow(1, 3, "fec'", "subj", 1, 4),
                 skel.SkelRow(1, 3, "fec'", "obl:di", 1, 2)]}
    dep_index = {(1, 2): _row(1, 2, "mi", "expl", 3)}
    violations = skel._classify_divergence(given, derived, dep_index, {(1, 2): "pronoun"})
    assert any(v.detail.startswith("extra_arg") and v.arg == (1, 2) for v in violations)


def test_classify_divergence_copular_adverb_complement_accepted():
    # Rule AD. "l'ubidir ... m'è tardi" (inferno 2:80): `essere` needs a complement to predicate
    # anything, so an adverb the tree attached `advmod` to it is that complement.
    derived = {1: [skel.SkelRow(1, 8, "è", "subj", 1, 3)]}
    given = {1: [skel.SkelRow(1, 8, "è", "subj", 1, 3),
                 skel.SkelRow(1, 8, "è", "attr", 1, 9)]}
    dep_index = {(1, 9): _row(1, 9, "tardi", "advmod", 8)}
    assert skel._classify_divergence(
        given, derived, dep_index, {(1, 9): "adverb"}, None, {(1, 8): "essere"}) == []


def test_classify_divergence_adverb_complement_of_a_lexical_verb_still_flagged():
    # The copula lemma is the whole gate: under a lexical verb the adverb reading is undecided,
    # exactly as rule R already had it.
    derived = {1: [skel.SkelRow(1, 8, "corre", "subj", 1, 3)]}
    given = {1: [skel.SkelRow(1, 8, "corre", "subj", 1, 3),
                 skel.SkelRow(1, 8, "corre", "attr", 1, 9)]}
    dep_index = {(1, 9): _row(1, 9, "tosto", "advmod", 8)}
    violations = skel._classify_divergence(
        given, derived, dep_index, {(1, 9): "adverb"}, None, {(1, 8): "correre"})
    assert any(v.detail.startswith("extra_arg") and v.arg == (1, 9) for v in violations)


def test_classify_divergence_free_relative_head_accepted():
    # Rule AE. "Galeotto fu 'l libro e chi lo scrisse" (inferno 5:137): the derivation cites the
    # clause's verb in the matrix role, the LLM the pronoun heading it.
    derived = {1: [skel.SkelRow(1, 2, "fu", "subj", 1, 8),
                   skel.SkelRow(1, 8, "scrisse", "subj", 1, 6)]}
    given = {1: [skel.SkelRow(1, 2, "fu", "subj", 1, 6),
                 skel.SkelRow(1, 8, "scrisse", "subj", 1, 6)]}
    dep_index = {(1, 6): _row(1, 6, "chi", "nsubj", 8),
                 (1, 8): _row(1, 8, "scrisse", "nsubj", 2)}
    # `scrisse` is a verb in a subject slot the LLM also gave a tuple of its own, so rule Z's
    # host leg closes the derivation's citation of the clause and rule AE the pronoun's.
    assert skel._classify_divergence(
        given, derived, dep_index, {(1, 6): "pronoun", (1, 8): "verb"}) == []


def test_classify_divergence_free_relative_head_in_another_role_still_flagged():
    derived = {1: [skel.SkelRow(1, 2, "fu", "obj", 1, 8)]}
    given = {1: [skel.SkelRow(1, 2, "fu", "subj", 1, 6)]}
    dep_index = {(1, 6): _row(1, 6, "chi", "nsubj", 8),
                 (1, 8): _row(1, 8, "scrisse", "obj", 2)}
    violations = skel._classify_divergence(given, derived, dep_index, {(1, 6): "pronoun"})
    assert any(v.detail.startswith("extra_arg") and v.arg == (1, 6) for v in violations)


def test_validate_unit_membership_accepts_a_dep_corroborated_argument():
    # Rule AF. "ch'io v'ebbi alcun riconosciuto" (inferno 3:58): `alcun` heads no Layer-3 NP, but
    # Layer 4 attaches it as the participle's `obj`, which is the corpus's own answer.
    from dante_corpus.dep import DepRow
    from dante_corpus.np import NPSpan
    nos, texts = [1], ["ch'io v'ebbi alcun riconosciuto"]
    rows = {1: [skel.SkelRow(1, 5, "riconosciuto", "obj", 1, 4)]}
    morph_rows = {1: [morph.MorphRow(word=w, lemma=w, pos=p)
                      for w, p in [("ch'", "conjunction"), ("io", "pronoun"),
                                   ("v'", "pronoun"), ("alcun", "adjective"),
                                   ("riconosciuto", "verb")]]}
    np_rows = {1: (NPSpan(line=1, start=2, end=2, head=2, text="io"),)}
    dep_rows = {1: [DepRow(line=1, token=4, word="alcun", deprel="obj",
                           head_line=1, head_token=5)]}
    violations = skel.validate_unit(nos, texts, rows, morph_rows, np_rows)
    assert any("heads no NP" in v.detail for v in violations)
    violations = skel.validate_unit(nos, texts, rows, morph_rows, np_rows, dep_rows)
    assert not any("heads no NP" in v.detail for v in violations)


# --- Phase 6: rule AH (Rule AG's second leg) -------------------------------------------


def _ag_fixture(subj_person, subj_number):
    """"La mente tua conservi ... e ora attendi qui" (inferno 10:127-129): `attendi` is a 2sg
    imperative attached `conj` to `conservi`, whose subject `mente` step 3 propagates onto it."""
    derived = {2: [skel.SkelRow(2, 1, "attendi", "subj", 1, 2)]}
    given = {2: [skel.SkelRow(2, 1, "attendi", "subj", 0, 0)]}
    dep_index_by_pos = {
        (1, 2): dep.DepRow(line=1, token=2, word="mente", deprel="nsubj",
                           head_line=1, head_token=3),
        (1, 3): dep.DepRow(line=1, token=3, word="conservi", deprel="root",
                           head_line=0, head_token=0),
        (2, 1): dep.DepRow(line=2, token=1, word="attendi", deprel="conj",
                           head_line=1, head_token=3),
    }
    morph_rows = {
        1: [morph.MorphRow(word="La", pos="article"),
            morph.MorphRow(word="mente", pos="noun", number=subj_number, person=subj_person),
            morph.MorphRow(word="conservi", pos="verb", number="sg.", person="3")],
        2: [morph.MorphRow(word="attendi", pos="verb", number="sg.", person="2")],
    }
    return given, derived, dep_index_by_pos, morph_rows


def test_classify_divergence_rule_ah_drops_null_subj_when_ag_drops_the_inherited_one():
    # `mente` is 3rd person, `attendi` 2nd: rule AG drops the derived subject, and rule AH drops
    # the ∅ with it — the derivation now says nothing about this predicate's subject.
    given, derived, dep_index_by_pos, morph_rows = _ag_fixture("", "sg.")
    assert skel._classify_divergence(
        given, derived, dep_index_by_pos, None, None, None, morph_rows) == []


def test_classify_divergence_rule_ah_leaves_an_agreeing_inherited_subject_flagged():
    # Same shape with an agreeing subject: rule AG does not fire, so nothing is disclaimed and
    # the LLM's ∅ is a real disagreement about a subject the derivation does assert.
    given, derived, dep_index_by_pos, morph_rows = _ag_fixture("2", "sg.")
    violations = skel._classify_divergence(
        given, derived, dep_index_by_pos, None, None, None, morph_rows)
    assert any(v.detail.startswith("extra_arg") and v.arg == (0, 0) for v in violations)


def test_classify_divergence_rule_ah_keeps_a_concrete_subject_flagged():
    # Rule AH drops only ∅. A conjunct where the LLM resolved a *different* concrete subject is
    # making its own claim about a slot the derivation no longer fills, and stays flagged.
    given, derived, dep_index_by_pos, morph_rows = _ag_fixture("", "sg.")
    given = {2: [skel.SkelRow(2, 1, "attendi", "subj", 1, 1)]}
    violations = skel._classify_divergence(
        given, derived, dep_index_by_pos, None, None, None, morph_rows)
    assert any(v.detail.startswith("extra_arg") and v.arg == (1, 1) for v in violations)


# --- Phase 6: rule AI (NP-head / dep-attachment equivalence) ---------------------------


def _np_head_fixture(np_head):
    """"Qui con più di mille giaccio" (inferno 10:118): Layer 3's NP head and Layer 4's oblique
    attachment land on different tokens of `[più di mille]`, so one argument costs two
    violations — a `missing_arg` for the derived token and an `extra_arg` for the cited one."""
    from dante_corpus.np import NPSpan
    derived = {1: [skel.SkelRow(1, 1, "giaccio", "obl:con", 1, 5)]}
    given = {1: [skel.SkelRow(1, 1, "giaccio", "obl:con", 1, 3)]}
    dep_index_by_pos = {
        (1, 2): dep.DepRow(line=1, token=2, word="con", deprel="case", head_line=1, head_token=5),
        (1, 5): dep.DepRow(line=1, token=5, word="mille", deprel="obl", head_line=1, head_token=1),
    }
    np_rows = {1: [NPSpan(line=1, start=3, end=5, head=np_head, text="più di mille")]}
    return given, derived, dep_index_by_pos, np_rows


def test_classify_divergence_rule_ai_merges_two_names_for_one_np():
    given, derived, dep_index_by_pos, np_rows = _np_head_fixture(np_head=3)
    assert skel._classify_divergence(
        given, derived, dep_index_by_pos, None, None, None, None, np_rows) == []


def test_classify_divergence_rule_ai_requires_one_side_to_be_the_np_head():
    # Both tokens inside one span but neither of them its head: they are not each other's
    # alternative name, and the pair stays flagged.
    given, derived, dep_index_by_pos, np_rows = _np_head_fixture(np_head=4)
    violations = skel._classify_divergence(
        given, derived, dep_index_by_pos, None, None, None, None, np_rows)
    assert any(v.detail.startswith("missing_arg") for v in violations)
    assert any(v.detail.startswith("extra_arg") for v in violations)


def test_classify_divergence_rule_ai_requires_the_same_role():
    # A role disagreement is a reading disagreement, whatever NP the two tokens share.
    given, derived, dep_index_by_pos, np_rows = _np_head_fixture(np_head=3)
    given = {1: [skel.SkelRow(1, 1, "giaccio", "obj", 1, 3)]}
    violations = skel._classify_divergence(
        given, derived, dep_index_by_pos, None, None, None, None, np_rows)
    assert any(v.detail.startswith("missing_arg") for v in violations)


# --- Phase 6: rule AJ (conj-shared non-subject argument) -------------------------------


def _gapping_fixture(conj_has_own_obj=False):
    """"li rami schianta, abbatte e porta fori" (inferno 9:70): `li rami` is the coordination
    head's object, gapped onto each conjunct, which the LLM restates and derive_unit sees once."""
    derived = {1: [skel.SkelRow(1, 3, "schianta", "obj", 1, 2)],
               2: [skel.SkelRow(2, 1, "abbatte", "subj", 1, 1)]}
    if conj_has_own_obj:
        derived[2].append(skel.SkelRow(2, 1, "abbatte", "obj", 2, 2))
    given = {1: [skel.SkelRow(1, 3, "schianta", "obj", 1, 2)],
             2: [skel.SkelRow(2, 1, "abbatte", "subj", 1, 1),
                 skel.SkelRow(2, 1, "abbatte", "obj", 1, 2)]}
    dep_index_by_pos = {
        (1, 2): dep.DepRow(line=1, token=2, word="rami", deprel="obj", head_line=1, head_token=3),
        (1, 3): dep.DepRow(line=1, token=3, word="schianta", deprel="root",
                           head_line=0, head_token=0),
        (2, 1): dep.DepRow(line=2, token=1, word="abbatte", deprel="conj",
                           head_line=1, head_token=3),
    }
    return given, derived, dep_index_by_pos


def test_classify_divergence_rule_aj_accepts_a_gapped_object():
    given, derived, dep_index_by_pos = _gapping_fixture()
    assert skel._classify_divergence(given, derived, dep_index_by_pos) == []


def test_classify_divergence_rule_aj_requires_the_slot_to_be_empty():
    # The conjunct has an object of its own, so a second one is a real extra argument.
    given, derived, dep_index_by_pos = _gapping_fixture(conj_has_own_obj=True)
    violations = skel._classify_divergence(given, derived, dep_index_by_pos)
    assert any(v.detail.startswith("extra_arg") and v.arg == (1, 2) for v in violations)


def test_classify_divergence_rule_aj_never_touches_the_subject():
    # `subj` belongs to step 3 and the authority model (rules AC/AG/AH); rule AJ leaves it alone.
    derived = {1: [skel.SkelRow(1, 3, "schianta", "subj", 1, 2)],
               2: [skel.SkelRow(2, 1, "abbatte", "subj", 1, 4)]}
    given = {1: [skel.SkelRow(1, 3, "schianta", "subj", 1, 2)],
             2: [skel.SkelRow(2, 1, "abbatte", "subj", 1, 4),
                 skel.SkelRow(2, 1, "abbatte", "obj", 1, 2)]}
    dep_index_by_pos = {
        (1, 2): dep.DepRow(line=1, token=2, word="rami", deprel="nsubj", head_line=1, head_token=3),
        (1, 3): dep.DepRow(line=1, token=3, word="schianta", deprel="root",
                           head_line=0, head_token=0),
        (2, 1): dep.DepRow(line=2, token=1, word="abbatte", deprel="conj",
                           head_line=1, head_token=3),
    }
    violations = skel._classify_divergence(given, derived, dep_index_by_pos)
    assert any(v.detail.startswith("extra_arg") and v.arg == (1, 2) for v in violations)


def test_classify_divergence_rule_aj_walks_past_intermediate_conjuncts():
    # "schianta, abbatte e porta": `porta` chains to `abbatte` and only then to `schianta`, whose
    # object it gaps — walking straight to the coordination *head* would miss it entirely when
    # the head is further up (`fier` in the real line).
    derived = {1: [skel.SkelRow(1, 3, "schianta", "obj", 1, 2)],
               2: [skel.SkelRow(2, 1, "abbatte", "subj", 1, 1)],
               3: [skel.SkelRow(3, 1, "porta", "subj", 1, 1)]}
    given = {1: [skel.SkelRow(1, 3, "schianta", "obj", 1, 2)],
             2: [skel.SkelRow(2, 1, "abbatte", "subj", 1, 1)],
             3: [skel.SkelRow(3, 1, "porta", "subj", 1, 1),
                 skel.SkelRow(3, 1, "porta", "obj", 1, 2)]}
    dep_index_by_pos = {
        (1, 2): dep.DepRow(line=1, token=2, word="rami", deprel="obj", head_line=1, head_token=3),
        (1, 3): dep.DepRow(line=1, token=3, word="schianta", deprel="root",
                           head_line=0, head_token=0),
        (2, 1): dep.DepRow(line=2, token=1, word="abbatte", deprel="conj",
                           head_line=1, head_token=3),
        (3, 1): dep.DepRow(line=3, token=1, word="porta", deprel="conj",
                           head_line=2, head_token=1),
    }
    assert skel._classify_divergence(given, derived, dep_index_by_pos) == []


# --- Phase 6: rules AK and AL ----------------------------------------------------------


def _come_fixture(come_pos):
    """"che qui staranno come porci in brago" (inferno 8:50): Layer 4 attaches the comparative
    `come` as a `case` child, minting `obl:come` out of a token Layer 2 calls a conjunction."""
    derived = {1: [skel.SkelRow(1, 1, "staranno", "obl:come", 1, 3)]}
    given = {1: [skel.SkelRow(1, 1, "staranno", "xcomp", 1, 3)]}
    dep_index_by_pos = {
        (1, 2): dep.DepRow(line=1, token=2, word="come", deprel="case", head_line=1, head_token=3),
        (1, 3): dep.DepRow(line=1, token=3, word="porci", deprel="obl", head_line=1, head_token=1),
    }
    return given, derived, dep_index_by_pos, {(1, 2): come_pos, (1, 3): "noun"}


def test_classify_divergence_rule_ak_accepts_a_comparative_come_complement():
    given, derived, dep_index_by_pos, morph_pos = _come_fixture("conjunction")
    assert skel._classify_divergence(given, derived, dep_index_by_pos, morph_pos) == []


def test_classify_divergence_rule_ak_requires_layer_2_to_call_come_a_conjunction():
    # Where Layer 2 does call it a preposition, the oblique reading is corroborated and stands.
    given, derived, dep_index_by_pos, morph_pos = _come_fixture("preposition")
    violations = skel._classify_divergence(given, derived, dep_index_by_pos, morph_pos)
    assert any(v.detail.startswith("role_mismatch") for v in violations)


def _fused_clitic_fixture(arg_pos):
    """"non gliel celai" (inferno 10:44): `gliel` is `gli` + `lo` in one token, so it genuinely
    fills both the dative and the accusative slot; Layer 4 has only one deprel to give it."""
    derived = {1: [skel.SkelRow(1, 3, "celai", "obj", 1, 2)]}
    given = {1: [skel.SkelRow(1, 3, "celai", "iobj", 1, 2)]}
    return given, derived, {}, {(1, 2): arg_pos}


def test_classify_divergence_rule_al_accepts_a_dual_role_fused_clitic():
    given, derived, dep_index_by_pos, morph_pos = _fused_clitic_fixture("pronoun+pronoun")
    assert skel._classify_divergence(given, derived, dep_index_by_pos, morph_pos) == []


def test_classify_divergence_rule_al_requires_two_fused_pronouns():
    # A plain pronoun encodes one role, so obj-vs-iobj on it is a real disagreement.
    given, derived, dep_index_by_pos, morph_pos = _fused_clitic_fixture("pronoun")
    violations = skel._classify_divergence(given, derived, dep_index_by_pos, morph_pos)
    assert any(v.detail.startswith("role_mismatch") for v in violations)


# --- Phase 6: rules AM-AT (the Inferno 11-15 read) --------------------------------------


def _cop_stranded_fixture(on_cop=True):
    """"'n la mente m'è fitta" (inferno 15:82): Layer 4 hangs the oblique and the dative on the
    copula `è`, leaving the adjective predicate `fitta` with nothing but its subject."""
    host = (1, 4) if on_cop else (1, 5)
    dep_rows = [
        dep.DepRow(line=1, token=2, word="mente", deprel="obl",
                   head_line=host[0], head_token=host[1]),
        dep.DepRow(line=1, token=3, word="m'", deprel="iobj",
                   head_line=host[0], head_token=host[1]),
        dep.DepRow(line=1, token=4, word="è", deprel="cop", head_line=1, head_token=5),
        dep.DepRow(line=1, token=5, word="fitta", deprel="root", head_line=0, head_token=0),
        dep.DepRow(line=1, token=6, word="imagine", deprel="nsubj", head_line=1, head_token=5),
    ]
    morph_rows = {1: [
        morph.MorphRow(word="'n", pos="preposition"),
        morph.MorphRow(word="mente", pos="noun"),
        morph.MorphRow(word="m'", pos="pronoun"),
        morph.MorphRow(word="è", pos="verb", person="3"),
        morph.MorphRow(word="fitta", pos="adjective"),
        morph.MorphRow(word="imagine", pos="noun"),
    ]}
    return {1: dep_rows}, morph_rows


def test_derive_unit_rule_am_lifts_arguments_off_a_copula():
    dep_rows, morph_rows = _cop_stranded_fixture()
    derived = skel.derive_unit([1], dep_rows, morph_rows)
    roles = {(r.role, r.arg_line, r.arg_token) for r in derived[1] if r.token == 5}
    assert ("obl", 1, 2) in roles and ("iobj", 1, 3) in roles


def test_derive_unit_rule_am_leaves_a_predicates_own_children_alone():
    # Same tree with the arguments already on the lexical predicate: one row each, not two.
    dep_rows, morph_rows = _cop_stranded_fixture(on_cop=False)
    derived = skel.derive_unit([1], dep_rows, morph_rows)
    obliques = [r for r in derived[1] if r.token == 5 and r.role == "obl"]
    assert len(obliques) == 1


def _orphan_fixture():
    """"però giri Fortuna la sua rota …, e 'l villan la sua marra" (inferno 15:95-96): UD promotes
    `villan` to `conj` and hangs `marra` on it as `orphan`, because the verb is elided."""
    dep_rows = [
        dep.DepRow(line=1, token=1, word="giri", deprel="root", head_line=0, head_token=0),
        dep.DepRow(line=1, token=2, word="Fortuna", deprel="nsubj", head_line=1, head_token=1),
        dep.DepRow(line=1, token=3, word="rota", deprel="obj", head_line=1, head_token=1),
        dep.DepRow(line=2, token=1, word="villan", deprel="conj", head_line=1, head_token=1),
        dep.DepRow(line=2, token=2, word="marra", deprel="orphan", head_line=2, head_token=1),
    ]
    morph_rows = {
        1: [morph.MorphRow(word="giri", pos="verb", person="3"),
            morph.MorphRow(word="Fortuna", pos="noun"), morph.MorphRow(word="rota", pos="noun")],
        2: [morph.MorphRow(word="villan", pos="noun"), morph.MorphRow(word="marra", pos="noun")],
    }
    return {1: [r for r in dep_rows if r.line == 1], 2: [r for r in dep_rows if r.line == 2]}, morph_rows


def test_derive_unit_rule_an_reads_a_gapped_conjunct_as_the_heads_slots():
    dep_rows, morph_rows = _orphan_fixture()
    derived = skel.derive_unit([1, 2], dep_rows, morph_rows)
    rows = {(r.role, r.arg_line, r.arg_token) for r in derived[1]}
    assert ("subj", 2, 1) in rows and ("obj", 2, 2) in rows


def test_derive_unit_rule_an_does_not_mint_the_gapped_conjunct_as_a_predicate():
    dep_rows, morph_rows = _orphan_fixture()
    derived = skel.derive_unit([1, 2], dep_rows, morph_rows)
    assert not derived[2]


def test_classify_divergence_rule_aj_accepts_an_object_gapped_from_a_sibling():
    # "biscazza e fonde la sua facultade" (inferno 11:44): the object hangs on the *second*
    # conjunct and is shared back to the first — neither is the other's ancestor.
    derived = {1: [skel.SkelRow(1, 1, "biscazza", "subj", 1, 9),
                   skel.SkelRow(1, 3, "fonde", "obj", 1, 6)]}
    given = {1: [skel.SkelRow(1, 1, "biscazza", "subj", 1, 9),
                 skel.SkelRow(1, 1, "biscazza", "obj", 1, 6),
                 skel.SkelRow(1, 3, "fonde", "obj", 1, 6)]}
    dep_index_by_pos = {
        (1, 1): dep.DepRow(line=1, token=1, word="biscazza", deprel="conj",
                           head_line=1, head_token=9),
        (1, 3): dep.DepRow(line=1, token=3, word="fonde", deprel="conj",
                           head_line=1, head_token=9),
        (1, 6): dep.DepRow(line=1, token=6, word="facultade", deprel="obj",
                           head_line=1, head_token=3),
        (1, 9): dep.DepRow(line=1, token=9, word="priva", deprel="root",
                           head_line=0, head_token=0),
    }
    assert skel._classify_divergence(given, derived, dep_index_by_pos) == []


def test_coordination_head_rule_ap_collapses_an_apposition_onto_its_host():
    # "guastatori e predon, tutti tormenta" (inferno 11:38): `tutti` sums up the objects it is
    # appositive to, and is not a second object of the verb.
    dep_index_by_pos = {
        (1, 1): dep.DepRow(line=1, token=1, word="omicide", deprel="obj",
                           head_line=1, head_token=3),
        (1, 2): dep.DepRow(line=1, token=2, word="tutti", deprel="appos",
                           head_line=1, head_token=1),
    }
    assert skel._coordination_head((1, 2), dep_index_by_pos) == (1, 1)


def test_classify_divergence_rule_aq_merges_a_citation_on_an_auxiliary():
    # "ch'altro ne volesse dire" (inferno 13:110): the LLM cites the finite auxiliary, the
    # derivation the lexical verb Layer 4 made the clause head.
    derived = {1: [skel.SkelRow(1, 1, "credendo", "ccomp", 1, 3)]}
    given = {1: [skel.SkelRow(1, 1, "credendo", "ccomp", 1, 2)]}
    dep_index_by_pos = {
        (1, 2): dep.DepRow(line=1, token=2, word="volesse", deprel="aux",
                           head_line=1, head_token=3),
        (1, 3): dep.DepRow(line=1, token=3, word="dire", deprel="ccomp",
                           head_line=1, head_token=1),
    }
    assert skel._classify_divergence(given, derived, dep_index_by_pos) == []


def _comparative_adjunct_fixture(come_pos="conjunction"):
    """"son tre cerchietti … come que' che lassi" (inferno 11:17): the comparison has no verb, so
    Layer 4 can only hang the compared nominal on the main predicate."""
    derived = {1: [skel.SkelRow(1, 1, "son", "obl", 1, 4)]}
    given: dict[int, list[skel.SkelRow]] = {1: [skel.SkelRow(1, 1, "son", "subj", 1, 2)]}
    derived[1].append(skel.SkelRow(1, 1, "son", "subj", 1, 2))
    dep_index_by_pos = {
        (1, 1): dep.DepRow(line=1, token=1, word="son", deprel="root", head_line=0, head_token=0),
        (1, 2): dep.DepRow(line=1, token=2, word="cerchietti", deprel="nsubj",
                           head_line=1, head_token=1),
        (1, 3): dep.DepRow(line=1, token=3, word="come", deprel="mark", head_line=1, head_token=4),
        (1, 4): dep.DepRow(line=1, token=4, word="que'", deprel="obl", head_line=1, head_token=1),
    }
    # The compared nominal is given a *noun* POS so this fixture isolates rule AR's own gate:
    # an adjective in a bare `obl` slot is rule AZ/BX's depictive shape and would be accepted
    # whatever Layer 2 calls the marker.
    return given, derived, dep_index_by_pos, {(1, 3): come_pos, (1, 4): "noun"}


def test_classify_divergence_rule_ar_accepts_a_verbless_comparative_oblique():
    given, derived, dep_index_by_pos, morph_pos = _comparative_adjunct_fixture()
    assert skel._classify_divergence(given, derived, dep_index_by_pos, morph_pos) == []


def test_classify_divergence_rule_ar_requires_layer_2_to_call_come_a_conjunction():
    given, derived, dep_index_by_pos, morph_pos = _comparative_adjunct_fixture("preposition")
    violations = skel._classify_divergence(given, derived, dep_index_by_pos, morph_pos)
    assert any(v.detail.startswith("missing_arg") for v in violations)


def _fused_expl_fixture(case_value):
    """"poi sen van giù" (inferno 14:117): `sen` is `si` + `ne`, and Layer 4's one deprel per
    token can only record the reflexive half."""
    derived = {1: [skel.SkelRow(1, 1, "van", "subj", 1, 4)]}
    given = {1: [skel.SkelRow(1, 1, "van", "subj", 1, 4),
                 skel.SkelRow(1, 1, "van", "obl:di", 1, 2)]}
    dep_index_by_pos = {
        (1, 1): dep.DepRow(line=1, token=1, word="van", deprel="root", head_line=0, head_token=0),
        (1, 2): dep.DepRow(line=1, token=2, word="sen", deprel="expl", head_line=1, head_token=1),
    }
    return given, derived, dep_index_by_pos, {(1, 2): "pronoun+pronoun"}, {(1, 2): case_value}


def test_classify_divergence_rule_as_accepts_a_fused_clitics_second_case():
    given, derived, idx, morph_pos, case_by = _fused_expl_fixture("reflexive+ablative")
    assert skel._classify_divergence(given, derived, idx, morph_pos, case_by) == []


def test_classify_divergence_rule_as_requires_a_second_case_slot():
    # A plain reflexive carries no ablative, so an oblique role on it is a real extra argument.
    given, derived, idx, morph_pos, case_by = _fused_expl_fixture("reflexive")
    violations = skel._classify_divergence(given, derived, idx, morph_pos, case_by)
    assert any(v.detail.startswith("extra_arg") for v in violations)


def _elided_speech_fixture(pred_pos="pronoun"):
    """"e io «…», dissi lui … Ed elli: «Vedi …»" (inferno 11:13-15): `elli` is a `conj` of the
    verb of speech and is the speaker of the elided second one, not a subject of the first."""
    dep_rows = {
        1: [dep.DepRow(line=1, token=1, word="dissi", deprel="root", head_line=0, head_token=0),
            dep.DepRow(line=1, token=2, word="io", deprel="nsubj", head_line=1, head_token=1)],
        2: [dep.DepRow(line=2, token=1, word="elli", deprel="conj", head_line=1, head_token=1),
            dep.DepRow(line=2, token=2, word="Vedi", deprel="ccomp", head_line=2, head_token=1)],
    }
    morph_rows = {
        1: [morph.MorphRow(word="dissi", pos="verb", person="1"),
            morph.MorphRow(word="io", pos="pronoun")],
        2: [morph.MorphRow(word="elli", pos=pred_pos),
            morph.MorphRow(word="Vedi", pos="verb", person="2")],
    }
    return dep_rows, morph_rows


def test_derive_unit_rule_at_a_nominal_conjunct_does_not_inherit_a_subject():
    dep_rows, morph_rows = _elided_speech_fixture()
    derived = skel.derive_unit([1, 2], dep_rows, morph_rows)
    subjects = {(r.arg_line, r.arg_token) for r in derived[2] if r.role == "subj"}
    assert (1, 2) not in subjects


def test_derive_unit_rule_at_a_verb_conjunct_still_inherits():
    dep_rows, morph_rows = _elided_speech_fixture(pred_pos="verb")
    derived = skel.derive_unit([1, 2], dep_rows, morph_rows)
    subjects = {(r.arg_line, r.arg_token) for r in derived[2] if r.role == "subj"}
    assert (1, 2) in subjects


# --- Phase 6: rules AU-AX (the Inferno 16-20 read) --------------------------------------


def _amod_secondary_predicate_fixture(arg_pos="adjective"):
    """"che innanzi a buon segnor fa servo forte" (inferno 17:90): `forte` is the object
    complement, and Layer 4 hangs it on the object noun as `amod`."""
    derived = {1: [skel.SkelRow(1, 1, "fa", "obj", 1, 2)]}
    given = {1: [skel.SkelRow(1, 1, "fa", "obj", 1, 2),
                 skel.SkelRow(1, 1, "fa", "attr", 1, 3)]}
    dep_index_by_pos = {
        (1, 1): dep.DepRow(line=1, token=1, word="fa", deprel="root", head_line=0, head_token=0),
        (1, 2): dep.DepRow(line=1, token=2, word="servo", deprel="obj", head_line=1, head_token=1),
        (1, 3): dep.DepRow(line=1, token=3, word="forte", deprel="amod", head_line=1, head_token=2),
    }
    return given, derived, dep_index_by_pos, {(1, 3): arg_pos}


def test_classify_divergence_rule_au_accepts_an_amod_secondary_predicate():
    given, derived, idx, morph_pos = _amod_secondary_predicate_fixture()
    assert skel._classify_divergence(given, derived, idx, morph_pos) == []


def test_classify_divergence_rule_au_requires_an_adjective():
    # Layer 2 calling the token something else leaves the reading undecided, as for rule R.
    given, derived, idx, morph_pos = _amod_secondary_predicate_fixture(arg_pos="noun")
    violations = skel._classify_divergence(given, derived, idx, morph_pos)
    assert any(v.detail.startswith("extra_arg") for v in violations)


def test_classify_divergence_rule_au_requires_the_host_to_be_this_predicates_argument():
    # `forte` modifies a noun that is not this predicate's argument, so the reading is a real
    # disagreement rather than a placement convention.
    given, derived, idx, morph_pos = _amod_secondary_predicate_fixture()
    idx[(1, 3)] = dep.DepRow(line=1, token=3, word="forte", deprel="amod",
                             head_line=1, head_token=4)
    violations = skel._classify_divergence(given, derived, idx, morph_pos)
    assert any(v.detail.startswith("extra_arg") for v in violations)


def _aux_only_predicate_fixture(aux_deprel="aux"):
    """"che spezzate averien ritorte e strambe" (inferno 19:27): the LLM's tuple sits on the
    auxiliary, Layer 4's lexical head is the participle."""
    derived = {1: [skel.SkelRow(1, 1, "spezzate", "obj", 1, 3)]}
    given = {1: [skel.SkelRow(1, 2, "averien", "obj", 1, 3)]}
    dep_index_by_pos = {
        (1, 1): dep.DepRow(line=1, token=1, word="spezzate", deprel="advcl",
                           head_line=0, head_token=0),
        (1, 2): dep.DepRow(line=1, token=2, word="averien", deprel=aux_deprel,
                           head_line=1, head_token=1),
        (1, 3): dep.DepRow(line=1, token=3, word="ritorte", deprel="obj",
                           head_line=1, head_token=1),
    }
    return given, derived, dep_index_by_pos


def test_classify_divergence_rule_av_accepts_a_predicate_named_by_its_auxiliary():
    given, derived, idx = _aux_only_predicate_fixture()
    details = [v.detail for v in skel._classify_divergence(given, derived, idx)]
    assert not any(d.startswith("missing_tuple") for d in details)


def test_classify_divergence_rule_av_requires_an_auxiliary_edge():
    given, derived, idx = _aux_only_predicate_fixture(aux_deprel="conj")
    details = [v.detail for v in skel._classify_divergence(given, derived, idx)]
    assert any(d.startswith("missing_tuple") for d in details)


def _pronominal_clitic_fixture(case_value="reflexive", deprel="obj"):
    """"poscia si puose là dove nacqu' io" (inferno 20:56): Layer 4 left this reflexive clitic
    as `obj` rather than `expl`, so the derivation asserts an object the LLM does not read."""
    derived = {1: [skel.SkelRow(1, 1, "puose", "obj", 1, 2)]}
    given: dict[int, list[skel.SkelRow]] = {1: [skel.SkelRow(1, 1, "puose", "subj", 0, 0)]}
    derived[1].append(skel.SkelRow(1, 1, "puose", "subj", 0, 0))
    dep_index_by_pos = {
        (1, 1): dep.DepRow(line=1, token=1, word="puose", deprel="root",
                           head_line=0, head_token=0),
        (1, 2): dep.DepRow(line=1, token=2, word="si", deprel=deprel,
                           head_line=1, head_token=1),
    }
    return given, derived, dep_index_by_pos, {(1, 2): "pronoun"}, {(1, 2): case_value}


def test_classify_divergence_rule_aw_accepts_an_unlisted_reflexive_clitic():
    given, derived, idx, morph_pos, case_by = _pronominal_clitic_fixture()
    assert skel._classify_divergence(given, derived, idx, morph_pos, case_by) == []


def test_classify_divergence_rule_aw_requires_the_annex_to_call_it_reflexive():
    # A plain accusative clitic is a real object, and its omission is a real divergence.
    given, derived, idx, morph_pos, case_by = _pronominal_clitic_fixture("accusative")
    violations = skel._classify_divergence(given, derived, idx, morph_pos, case_by)
    assert any(v.detail.startswith("missing_arg") for v in violations)


def _control_shared_argument_fixture(link="xcomp", given_role="obl:per"):
    """"come i Roman per l'essercito molto … hanno a passar la gente" (inferno 18:30): Layer 4
    hangs the oblique on the finite verb, the LLM on the infinitive it controls."""
    derived = {1: [skel.SkelRow(1, 1, "hanno", "obl:per", 1, 3),
                   skel.SkelRow(1, 2, "passar", "obj", 1, 4)]}
    given = {1: [skel.SkelRow(1, 1, "hanno", "subj", 0, 0),
                 skel.SkelRow(1, 2, "passar", given_role, 1, 3),
                 skel.SkelRow(1, 2, "passar", "obj", 1, 4)]}
    dep_index_by_pos = {
        (1, 1): dep.DepRow(line=1, token=1, word="hanno", deprel="root",
                           head_line=0, head_token=0),
        (1, 2): dep.DepRow(line=1, token=2, word="passar", deprel=link,
                           head_line=1, head_token=1),
        (1, 3): dep.DepRow(line=1, token=3, word="essercito", deprel="obl",
                           head_line=1, head_token=1),
        (1, 4): dep.DepRow(line=1, token=4, word="gente", deprel="obj",
                           head_line=1, head_token=2),
    }
    return given, derived, dep_index_by_pos


def test_classify_divergence_rule_ax_accepts_an_argument_shared_across_an_xcomp():
    given, derived, idx = _control_shared_argument_fixture()
    details = [v.detail for v in skel._classify_divergence(given, derived, idx)]
    assert not any(d.startswith(("extra_arg", "missing_arg")) for d in details)


def test_classify_divergence_rule_ax_excludes_a_ccomp_edge():
    given, derived, idx = _control_shared_argument_fixture(link="ccomp")
    details = [v.detail for v in skel._classify_divergence(given, derived, idx)]
    assert any(d.startswith(("extra_arg", "missing_arg")) for d in details)


def test_classify_divergence_rule_ax_requires_the_role_to_match():
    given, derived, idx = _control_shared_argument_fixture(given_role="obl:in")
    details = [v.detail for v in skel._classify_divergence(given, derived, idx)]
    assert any(d.startswith(("extra_arg", "missing_arg")) for d in details)


def _adjective_phrase_fixture(child_deprel="obl"):
    """"venir notando una figura in suso, / maravigliosa ad ogne cor sicuro" (inferno 16:132):
    the adjective governs its own complement, so it is a reduced relative, not an attributive."""
    derived: dict[int, list[skel.SkelRow]] = {1: []}
    given = {1: [skel.SkelRow(1, 2, "maravigliosa", "obl:a", 1, 3)]}
    dep_index_by_pos = {
        (1, 1): dep.DepRow(line=1, token=1, word="figura", deprel="root",
                           head_line=0, head_token=0),
        (1, 2): dep.DepRow(line=1, token=2, word="maravigliosa", deprel="amod",
                           head_line=1, head_token=1),
        (1, 3): dep.DepRow(line=1, token=3, word="cor", deprel=child_deprel,
                           head_line=1, head_token=2),
    }
    return given, derived, dep_index_by_pos, {(1, 2): "adjective", (1, 3): "noun"}


def test_classify_divergence_rule_ay_accepts_a_complemented_adjective_phrase():
    given, derived, idx, morph_pos = _adjective_phrase_fixture()
    details = [v.detail for v in skel._classify_divergence(given, derived, idx, morph_pos)]
    assert not any(d.startswith("extra_tuple") for d in details)


def test_classify_divergence_rule_ay_requires_a_complement_child():
    # A bare attributive adjective promoted to predicate is the genuine error rule
    # `_elided_copula_nominal` deliberately leaves flagged.
    given, derived, idx, morph_pos = _adjective_phrase_fixture(child_deprel="advmod")
    details = [v.detail for v in skel._classify_divergence(given, derived, idx, morph_pos)]
    assert any(d.startswith("extra_tuple") for d in details)


# --- The Inferno 21-25 read: rules AZ, BA, BB, BC, BD, BE, BF, BH, BI ------------------


def _depictive_oblique_fixture(arg_pos="adjective", extra=()):
    """"tornò sù convolto" (inferno 21:46): the depictive adjective hangs on the predicate as a
    bare `obl`, so the derivation reports an adjunct where the LLM reads the complement."""
    derived = {1: [skel.SkelRow(1, 1, "tornò", "obl", 1, 2)]}
    given = {1: [skel.SkelRow(1, 1, "tornò", "attr", 1, 2)]}
    dep_index_by_pos = {
        (1, 1): dep.DepRow(line=1, token=1, word="tornò", deprel="root",
                           head_line=0, head_token=0),
        (1, 2): dep.DepRow(line=1, token=2, word="convolto", deprel="obl",
                           head_line=1, head_token=1),
    }
    for row in extra:
        dep_index_by_pos[(row.line, row.token)] = row
    return given, derived, dep_index_by_pos, {(1, 2): arg_pos}


def test_classify_divergence_rule_az_accepts_a_depictive_bare_oblique():
    given, derived, idx, morph_pos = _depictive_oblique_fixture()
    assert skel._classify_divergence(given, derived, idx, morph_pos) == []


def test_classify_divergence_rule_az_requires_an_adjective():
    # An adverb in the same slot leaves the reading undecided, exactly as for rule R.
    given, derived, idx, morph_pos = _depictive_oblique_fixture(arg_pos="adverb")
    violations = skel._classify_divergence(given, derived, idx, morph_pos)
    assert any(v.detail.startswith("role_mismatch") for v in violations)


def test_classify_divergence_rule_az_requires_no_case_child():
    # A preposition in the tree makes the phrase a genuine adjunct.
    case_child = dep.DepRow(line=1, token=3, word="per", deprel="case",
                            head_line=1, head_token=2)
    given, derived, idx, morph_pos = _depictive_oblique_fixture(extra=(case_child,))
    violations = skel._classify_divergence(given, derived, idx, morph_pos)
    assert any(v.detail.startswith("role_mismatch") for v in violations)


def _two_subject_fixture(named=(1, 3)):
    """"E quelli: «I' mi partii»" (inferno 22:66): the elided verb of speech leaves `quelli`
    attached to the quoted verb next to its real subject, so the derivation has two."""
    derived = {1: [skel.SkelRow(1, 1, "partii", "subj", 1, 2),
                   skel.SkelRow(1, 1, "partii", "subj", 1, 3)]}
    given = {1: [skel.SkelRow(1, 1, "partii", "subj", *named)]}
    dep_index_by_pos = {
        (1, 1): dep.DepRow(line=1, token=1, word="partii", deprel="root",
                           head_line=0, head_token=0),
        (1, 2): dep.DepRow(line=1, token=2, word="quelli", deprel="nsubj",
                           head_line=1, head_token=1),
        (1, 3): dep.DepRow(line=1, token=3, word="I'", deprel="nsubj",
                           head_line=1, head_token=1),
    }
    return given, derived, dep_index_by_pos, {}


def test_classify_divergence_rule_ba_accepts_one_of_two_derived_subjects():
    given, derived, idx, morph_pos = _two_subject_fixture()
    assert skel._classify_divergence(given, derived, idx, morph_pos) == []


def test_classify_divergence_rule_ba_requires_the_llm_to_name_one_of_them():
    # A subject from outside the pair is the LLM's own claim and stays flagged.
    given, derived, idx, morph_pos = _two_subject_fixture(named=(1, 9))
    idx[(1, 9)] = dep.DepRow(line=1, token=9, word="altri", deprel="nsubj",
                             head_line=1, head_token=8)
    violations = skel._classify_divergence(given, derived, idx, morph_pos)
    assert any(v.detail.startswith("missing_arg") for v in violations)


def _coordinate_control_subject_fixture():
    """"vidi cavalier muover ... né pedoni ... né nave" (inferno 22:11): the LLM gives the
    controlled infinitive every conjunct of its subject; rule V accepted only the first."""
    derived = {1: [skel.SkelRow(1, 1, "vidi", "obj", 1, 2),
                   skel.SkelRow(1, 1, "vidi", "xcomp", 1, 4),
                   skel.SkelRow(1, 4, "muover", "", 0, 0)]}
    given = {1: [skel.SkelRow(1, 1, "vidi", "obj", 1, 2),
                 skel.SkelRow(1, 4, "muover", "subj", 1, 2),
                 skel.SkelRow(1, 4, "muover", "subj", 1, 3)]}
    dep_index_by_pos = {
        (1, 1): dep.DepRow(line=1, token=1, word="vidi", deprel="root",
                           head_line=0, head_token=0),
        (1, 2): dep.DepRow(line=1, token=2, word="cavalier", deprel="obj",
                           head_line=1, head_token=1),
        (1, 3): dep.DepRow(line=1, token=3, word="pedoni", deprel="conj",
                           head_line=1, head_token=2),
        (1, 4): dep.DepRow(line=1, token=4, word="muover", deprel="xcomp",
                           head_line=1, head_token=1),
    }
    return given, derived, dep_index_by_pos, {}


def test_classify_divergence_rule_bb_accepts_every_conjunct_of_a_control_subject():
    given, derived, idx, morph_pos = _coordinate_control_subject_fixture()
    assert skel._classify_divergence(given, derived, idx, morph_pos) == []


def test_classify_divergence_rule_bb_still_flags_a_subject_outside_the_chain():
    given, derived, idx, morph_pos = _coordinate_control_subject_fixture()
    given[1][2] = skel.SkelRow(1, 4, "muover", "subj", 1, 9)
    idx[(1, 9)] = dep.DepRow(line=1, token=9, word="altri", deprel="nsubj",
                             head_line=1, head_token=8)
    violations = skel._classify_divergence(given, derived, idx, morph_pos)
    assert any(v.detail.startswith("extra_arg") for v in violations)


def _nominal_advmod_fixture(arg_pos="noun"):
    """"stieno i Malebranche un poco in cesso" (inferno 22:100): Layer 4 parks the adverbial
    nominal on `advmod`, which `derive_unit` cannot read as an argument at all."""
    derived: dict[int, list[skel.SkelRow]] = {1: [skel.SkelRow(1, 1, "stieno", "subj", 0, 0)]}
    given = {1: [skel.SkelRow(1, 1, "stieno", "subj", 0, 0),
                 skel.SkelRow(1, 1, "stieno", "obl", 1, 2)]}
    dep_index_by_pos = {
        (1, 1): dep.DepRow(line=1, token=1, word="stieno", deprel="root",
                           head_line=0, head_token=0),
        (1, 2): dep.DepRow(line=1, token=2, word="poco", deprel="advmod",
                           head_line=1, head_token=1),
    }
    return given, derived, dep_index_by_pos, {(1, 2): arg_pos}


def test_classify_divergence_rule_bc_accepts_a_nominal_advmod_as_an_oblique():
    given, derived, idx, morph_pos = _nominal_advmod_fixture()
    assert skel._classify_divergence(given, derived, idx, morph_pos) == []


def test_classify_divergence_rule_bc_leaves_an_adjective_advmod_flagged():
    # Rule R's caution: an adjective there is a predicative complement, not an oblique.
    given, derived, idx, morph_pos = _nominal_advmod_fixture(arg_pos="adjective")
    violations = skel._classify_divergence(given, derived, idx, morph_pos)
    assert any(v.detail.startswith("extra_arg") for v in violations)


def test_classify_divergence_rule_bd_accepts_a_reflexive_clitic_left_as_obl():
    # "Se l'ira sovra 'l mal voler s'aggueffa" (inferno 23:16).
    given, derived, idx, morph_pos, case_by = _pronominal_clitic_fixture(deprel="obl")
    derived[1][0] = skel.SkelRow(1, 1, "puose", "obl", 1, 2)
    assert skel._classify_divergence(given, derived, idx, morph_pos, case_by) == []


def test_classify_divergence_rule_bd_requires_the_annex_to_call_it_reflexive():
    given, derived, idx, morph_pos, case_by = _pronominal_clitic_fixture(
        case_value="ablative", deprel="obl")
    derived[1][0] = skel.SkelRow(1, 1, "puose", "obl", 1, 2)
    violations = skel._classify_divergence(given, derived, idx, morph_pos, case_by)
    assert any(v.detail.startswith("missing_arg") for v in violations)


def test_coordination_head_rule_be_collapses_a_flat_name_onto_its_head():
    # "son Vanni Fucci" (inferno 24:125): `Fucci` is not a modifier of `Vanni`, it is the name.
    index = {
        (1, 1): dep.DepRow(line=1, token=1, word="Vanni", deprel="attr",
                           head_line=1, head_token=3),
        (1, 2): dep.DepRow(line=1, token=2, word="Fucci", deprel="flat",
                           head_line=1, head_token=1),
    }
    assert skel._coordination_head((1, 2), index) == (1, 1)


def _inverted_copula_fixture(arg_pos="adjective"):
    """"poi che fu a terra sì distrutto" (inferno 24:103): Layer 4 points the `cop` edge from the
    adjective down to the copula, so the derivation never sees the complement."""
    derived: dict[int, list[skel.SkelRow]] = {1: [skel.SkelRow(1, 1, "fu", "subj", 0, 0)]}
    given = {1: [skel.SkelRow(1, 1, "fu", "subj", 0, 0),
                 skel.SkelRow(1, 1, "fu", "attr", 1, 2)]}
    dep_index_by_pos = {
        (1, 1): dep.DepRow(line=1, token=1, word="fu", deprel="advcl",
                           head_line=2, head_token=1),
        (1, 2): dep.DepRow(line=1, token=2, word="distrutto", deprel="cop",
                           head_line=1, head_token=1),
    }
    return given, derived, dep_index_by_pos, {(1, 2): arg_pos}


def test_classify_divergence_rule_bf_accepts_an_inverted_copula_complement():
    given, derived, idx, morph_pos = _inverted_copula_fixture()
    assert skel._classify_divergence(given, derived, idx, morph_pos) == []


def test_classify_divergence_rule_bf_requires_a_non_verb_in_the_cop_slot():
    # An ordinary `cop` edge (a verb) is the normal shape and asserts nothing about a complement.
    given, derived, idx, morph_pos = _inverted_copula_fixture(arg_pos="verb")
    violations = skel._classify_divergence(given, derived, idx, morph_pos)
    assert any(v.detail.startswith("extra_arg") for v in violations)


def _displaced_subject_fixture(complement_role="attr"):
    """"che mi parve una lontra" (inferno 22:36): rule M concedes the derived `subj` to the LLM's
    predicative complement, which leaves the LLM's pro-drop subject with no counterpart."""
    derived = {1: [skel.SkelRow(1, 1, "parve", "subj", 1, 2)]}
    given = {1: [skel.SkelRow(1, 1, "parve", "subj", 0, 0),
                 skel.SkelRow(1, 1, "parve", complement_role, 1, 2)]}
    dep_index_by_pos = {
        (1, 1): dep.DepRow(line=1, token=1, word="parve", deprel="root",
                           head_line=0, head_token=0),
        (1, 2): dep.DepRow(line=1, token=2, word="lontra", deprel="nsubj",
                           head_line=1, head_token=1),
    }
    return given, derived, dep_index_by_pos, {(1, 2): "noun"}


def test_classify_divergence_rule_bh_accepts_the_pro_drop_rule_m_leaves_behind():
    given, derived, idx, morph_pos = _displaced_subject_fixture()
    assert skel._classify_divergence(given, derived, idx, morph_pos) == []


def test_classify_divergence_rule_bh_requires_rule_m_to_have_fired():
    # Without the complement relabelling, a ∅ subject against a concrete one is a real
    # disagreement — the `extra_arg subj ∅` bucket.
    given, derived, idx, morph_pos = _displaced_subject_fixture(complement_role="obj")
    violations = skel._classify_divergence(given, derived, idx, morph_pos)
    assert any(v.detail.startswith("extra_arg") for v in violations)


def _accusative_infinitive_fixture(link="xcomp"):
    """"I' vidi ... uno aspettar così" (inferno 22:31): the nominal is the matrix object and the
    infinitive's subject at once, and Layer 4 records only the second."""
    derived = {1: [skel.SkelRow(1, 1, "vidi", "xcomp", 1, 3),
                   skel.SkelRow(1, 3, "aspettar", "subj", 1, 2)]}
    given = {1: [skel.SkelRow(1, 1, "vidi", "obj", 1, 2),
                 skel.SkelRow(1, 1, "vidi", "xcomp", 1, 3),
                 skel.SkelRow(1, 3, "aspettar", "subj", 1, 2)]}
    dep_index_by_pos = {
        (1, 1): dep.DepRow(line=1, token=1, word="vidi", deprel="root",
                           head_line=0, head_token=0),
        (1, 2): dep.DepRow(line=1, token=2, word="uno", deprel="nsubj",
                           head_line=1, head_token=3),
        (1, 3): dep.DepRow(line=1, token=3, word="aspettar", deprel=link,
                           head_line=1, head_token=1),
    }
    return given, derived, dep_index_by_pos, {(1, 2): "pronoun"}


def test_classify_divergence_rule_bi_accepts_the_accusative_and_infinitive():
    given, derived, idx, morph_pos = _accusative_infinitive_fixture()
    assert skel._classify_divergence(given, derived, idx, morph_pos) == []


def test_classify_divergence_rule_bi_requires_the_infinitive_to_be_this_predicates_complement():
    given, derived, idx, morph_pos = _accusative_infinitive_fixture(link="advcl")
    violations = skel._classify_divergence(given, derived, idx, morph_pos)
    assert any(v.detail.startswith("extra_arg") for v in violations)


# --- Inferno 26-30 read: rules BJ-BN ---------------------------------------------------


def _adverb_cluster_fixture(head_pos="adverb", child_deprel="nmod"):
    """"che divenne / al padre, fuor del dritto amore, amica" (inferno 30:39): Layer 4 hangs the
    adverb `fuor` on the predicate and `amore` under it, so the derivation names the adverb and
    the LLM names the nominal that carries the meaning."""
    derived = {1: [skel.SkelRow(1, 1, "divenne", "obl", 1, 2)]}
    given = {1: [skel.SkelRow(1, 1, "divenne", "obl:di", 1, 4)]}
    dep_index_by_pos = {
        (1, 1): dep.DepRow(line=1, token=1, word="divenne", deprel="root",
                           head_line=0, head_token=0),
        (1, 2): dep.DepRow(line=1, token=2, word="fuor", deprel="obl",
                           head_line=1, head_token=1),
        (1, 3): dep.DepRow(line=1, token=3, word="del", deprel="case",
                           head_line=1, head_token=4),
        (1, 4): dep.DepRow(line=1, token=4, word="amore", deprel=child_deprel,
                           head_line=1, head_token=2),
    }
    return given, derived, dep_index_by_pos, {(1, 2): head_pos, (1, 4): "noun"}


def test_classify_divergence_rule_bj_merges_the_adverb_preposition_cluster():
    given, derived, idx, morph_pos = _adverb_cluster_fixture()
    assert skel._classify_divergence(given, derived, idx, morph_pos) == []


def test_classify_divergence_rule_bj_requires_layer2_to_call_the_head_an_adverb():
    # A nominal head is an ordinary `nmod` chain, which rule D governs on its own terms.
    given, derived, idx, morph_pos = _adverb_cluster_fixture(head_pos="noun")
    violations = skel._classify_divergence(given, derived, idx, morph_pos)
    assert any(v.detail.startswith("missing_arg") for v in violations)


def _comparative_che_fixture(marker="che", marker_pos="conjunction"):
    """"ch'el vedesse altro che la fiamma sola" (inferno 26:38): the second term of a comparison,
    which Layer 4 can only hang on the predicate and the LLM (rightly) does not list."""
    derived = {1: [skel.SkelRow(1, 1, "vedesse", "obj", 1, 2),
                   skel.SkelRow(1, 1, "vedesse", "obl", 1, 4)]}
    given = {1: [skel.SkelRow(1, 1, "vedesse", "obj", 1, 2)]}
    dep_index_by_pos = {
        (1, 1): dep.DepRow(line=1, token=1, word="vedesse", deprel="root",
                           head_line=0, head_token=0),
        (1, 2): dep.DepRow(line=1, token=2, word="altro", deprel="obj",
                           head_line=1, head_token=1),
        (1, 3): dep.DepRow(line=1, token=3, word=marker, deprel="mark",
                           head_line=1, head_token=4),
        (1, 4): dep.DepRow(line=1, token=4, word="fiamma", deprel="obl",
                           head_line=1, head_token=1),
    }
    return given, derived, dep_index_by_pos, {(1, 3): marker_pos, (1, 4): "noun"}


def test_classify_divergence_rule_bk_accepts_the_che_comparison():
    given, derived, idx, morph_pos = _comparative_che_fixture()
    assert skel._classify_divergence(given, derived, idx, morph_pos) == []


def test_classify_divergence_rule_bk_requires_layer2_to_call_the_marker_a_conjunction():
    given, derived, idx, morph_pos = _comparative_che_fixture(marker_pos="pronoun")
    violations = skel._classify_divergence(given, derived, idx, morph_pos)
    assert any(v.detail.startswith("missing_arg") for v in violations)


def _si_come_fixture(arg_token=3):
    """"sì come nuvoletta, in sù salire" (inferno 26:39): the correlative stands immediately
    before the marker, so the comparison is simply what `come` opens."""
    derived = {1: [skel.SkelRow(1, 6, "salire", "obl", 1, arg_token),
                   skel.SkelRow(1, 6, "salire", "obl:in", 1, 5)]}
    given = {1: [skel.SkelRow(1, 6, "salire", "obl:in", 1, 5)]}
    dep_index_by_pos = {
        (1, 1): dep.DepRow(line=1, token=1, word="sì", deprel="advmod",
                           head_line=1, head_token=6),
        (1, 2): dep.DepRow(line=1, token=2, word="come", deprel="mark",
                           head_line=1, head_token=6),
        (1, 3): dep.DepRow(line=1, token=3, word="nuvoletta", deprel="obl",
                           head_line=1, head_token=6),
        (1, 4): dep.DepRow(line=1, token=4, word="in", deprel="case",
                           head_line=1, head_token=5),
        (1, 5): dep.DepRow(line=1, token=5, word="sù", deprel="obl",
                           head_line=1, head_token=6),
        (1, 6): dep.DepRow(line=1, token=6, word="salire", deprel="root",
                           head_line=0, head_token=0),
    }
    return given, derived, dep_index_by_pos, {(1, 2): "conjunction", (1, 3): "noun",
                                              (1, 5): "adverb"}


def test_classify_divergence_rule_bl_accepts_the_si_come_comparison():
    given, derived, idx, morph_pos = _si_come_fixture()
    assert skel._classify_divergence(given, derived, idx, morph_pos) == []


def test_classify_divergence_rule_bl_leaves_the_predicates_own_oblique_flagged():
    # `in sù` is not what `come` opens: it stands past the compared nominal and is the
    # predicate's own adjunct, so dropping it from the LLM's rows stays reported.
    given, derived, idx, morph_pos = _si_come_fixture(arg_token=5)
    given[1] = [skel.SkelRow(1, 6, "salire", "obl", 1, 3)]
    derived[1] = [skel.SkelRow(1, 6, "salire", "obl:in", 1, 5)]
    violations = skel._classify_divergence(given, derived, idx, morph_pos)
    assert any(v.detail.startswith("missing_arg") for v in violations)


def _conjunction_oblique_fixture(filler_pos="conjunction"):
    """"Nel tempo che Iunone era crucciata" (inferno 30:1): the relative adverb Layer 4 parks in
    the `obl` slot is the clause's connective, not one of its arguments."""
    derived = {1: [skel.SkelRow(1, 4, "crucciata", "obl", 1, 1)]}
    given = {1: [skel.SkelRow(1, 4, "crucciata", "subj", 1, 2)]}
    dep_index_by_pos = {
        (1, 1): dep.DepRow(line=1, token=1, word="che", deprel="obl",
                           head_line=1, head_token=4),
        (1, 2): dep.DepRow(line=1, token=2, word="Iunone", deprel="nsubj",
                           head_line=1, head_token=4),
        (1, 4): dep.DepRow(line=1, token=4, word="crucciata", deprel="root",
                           head_line=0, head_token=0),
    }
    return given, derived, dep_index_by_pos, {(1, 1): filler_pos, (1, 2): "proper noun"}


def test_classify_divergence_rule_bm_accepts_a_conjunction_in_the_oblique_slot():
    given, derived, idx, morph_pos = _conjunction_oblique_fixture()
    # the derived `subj` is Iunone, which the LLM names too
    derived[1].append(skel.SkelRow(1, 4, "crucciata", "subj", 1, 2))
    assert skel._classify_divergence(given, derived, idx, morph_pos) == []


def test_classify_divergence_rule_bm_leaves_a_pronoun_oblique_flagged():
    given, derived, idx, morph_pos = _conjunction_oblique_fixture(filler_pos="pronoun")
    derived[1].append(skel.SkelRow(1, 4, "crucciata", "subj", 1, 2))
    violations = skel._classify_divergence(given, derived, idx, morph_pos)
    assert any(v.detail.startswith("missing_arg") for v in violations)


def _connective_clause_head(pos_tag="conjunction"):
    """"Onde l'altro lebbroso ... rispuose" (inferno 29:124): `Onde` is `advcl` on the main verb
    with nothing hanging on it — a connective, not an elided predicate."""
    dep_rows = {1: [
        dep.DepRow(line=1, token=1, word="Onde", deprel="advcl", head_line=1, head_token=3),
        dep.DepRow(line=1, token=2, word="lebbroso", deprel="nsubj", head_line=1, head_token=3),
        dep.DepRow(line=1, token=3, word="rispuose", deprel="root", head_line=0, head_token=0),
    ]}
    morph_rows = {1: [
        morph.MorphRow(word="Onde", pos=pos_tag),
        morph.MorphRow(word="lebbroso", pos="noun"),
        morph.MorphRow(word="rispuose", pos="verb", person="3"),
    ]}
    return skel.derive_unit([1], dep_rows, morph_rows)


def test_derive_unit_rule_bn_does_not_mint_a_predicate_at_a_connective():
    derived = _connective_clause_head()
    assert {(r.line, r.token) for rows in derived.values() for r in rows} == {(1, 3)}


def test_derive_unit_rule_bn_still_derives_a_verb_in_the_same_slot():
    derived = _connective_clause_head(pos_tag="verb")
    assert (1, 1) in {(r.line, r.token) for rows in derived.values() for r in rows}


def _gapped_comparison(remnant_deprel="orphan"):
    """"come coltel [fa] le scaglie di scardova" (inferno 29:83): a gapped comparison promoted to
    `advcl`, whose remnant UD marks `orphan`. No verb is elided that a tuple could be built on."""
    dep_rows = {1: [
        dep.DepRow(line=1, token=1, word="traevan", deprel="root", head_line=0, head_token=0),
        dep.DepRow(line=1, token=2, word="coltel", deprel="advcl", head_line=1, head_token=1),
        dep.DepRow(line=1, token=3, word="scaglie", deprel=remnant_deprel,
                   head_line=1, head_token=2),
    ]}
    morph_rows = {1: [
        morph.MorphRow(word="traevan", pos="verb", person="3"),
        morph.MorphRow(word="coltel", pos="noun"),
        morph.MorphRow(word="scaglie", pos="noun"),
    ]}
    return skel.derive_unit([1], dep_rows, morph_rows)


def test_derive_unit_rule_an_clause_head_leg_skips_a_gapped_comparison():
    derived = _gapped_comparison()
    assert {(r.line, r.token) for rows in derived.values() for r in rows} == {(1, 1)}


def test_derive_unit_rule_an_clause_head_leg_needs_the_orphan():
    # Without the `orphan` the promoted nominal is an ordinary elided-copula predicate.
    derived = _gapped_comparison(remnant_deprel="obj")
    assert (1, 2) in {(r.line, r.token) for rows in derived.values() for r in rows}


def _acc_inf_obj_fixture(host_tense="infinitive"):
    """"Io vidi due sedere a sé poggiati" (inferno 29:73): the same construction rule BI already
    takes, with Layer 4 writing the infinitive as a plain `obj`."""
    derived = {1: [skel.SkelRow(1, 2, "vidi", "obj", 1, 4),
                   skel.SkelRow(1, 4, "sedere", "subj", 1, 3)]}
    given = {1: [skel.SkelRow(1, 2, "vidi", "obj", 1, 3),
                 skel.SkelRow(1, 4, "sedere", "subj", 1, 3)]}
    dep_index_by_pos = {
        (1, 2): dep.DepRow(line=1, token=2, word="vidi", deprel="root",
                           head_line=0, head_token=0),
        (1, 3): dep.DepRow(line=1, token=3, word="due", deprel="nsubj",
                           head_line=1, head_token=4),
        (1, 4): dep.DepRow(line=1, token=4, word="sedere", deprel="obj",
                           head_line=1, head_token=2),
    }
    morph_rows = {1: [
        morph.MorphRow(word="Io", pos="pronoun"),
        morph.MorphRow(word="vidi", pos="verb", person="1"),
        morph.MorphRow(word="due", pos="numeral"),
        morph.MorphRow(word="sedere", pos="verb", tense=host_tense),
    ]}
    return given, derived, dep_index_by_pos, {(1, 3): "numeral", (1, 4): "verb"}, morph_rows


def test_classify_divergence_rule_bi_takes_the_obj_attached_infinitive():
    given, derived, idx, morph_pos, morph_rows = _acc_inf_obj_fixture()
    assert skel._classify_divergence(given, derived, idx, morph_pos,
                                     morph_rows=morph_rows) == []


def test_classify_divergence_rule_bi_obj_branch_requires_an_infinitive_host():
    # A finite clause in the `obj` slot has its own subject, which is nobody's matrix object.
    given, derived, idx, morph_pos, morph_rows = _acc_inf_obj_fixture(host_tense="present")
    violations = skel._classify_divergence(given, derived, idx, morph_pos,
                                           morph_rows=morph_rows)
    assert any(v.detail.startswith("extra_arg") for v in violations)


def test_validate_unit_membership_follows_a_cop_citation_to_its_lexical_head():
    # Rule AQ, applied to the membership check: "vorrebbe di vedere esser digiuno" (inferno
    # 28:87). The LLM cites `esser`, which Layer 4 marks `cop` on `digiuno` — the position the
    # divergence check already merges it onto.
    from dante_corpus.dep import DepRow
    from dante_corpus.np import NPSpan
    nos, texts = [1], ["vorrebbe di vedere esser digiuno"]
    rows = {1: [skel.SkelRow(1, 3, "vedere", "obj", 1, 4)]}
    morph_rows = {1: [morph.MorphRow(word=w, lemma=w, pos=p)
                      for w, p in [("vorrebbe", "verb"), ("di", "preposition"),
                                   ("vedere", "verb"), ("esser", "verb"),
                                   ("digiuno", "adjective")]]}
    np_rows = {1: (NPSpan(line=1, start=5, end=5, head=5, text="digiuno"),)}
    dep_rows = {1: [DepRow(line=1, token=4, word="esser", deprel="cop",
                           head_line=1, head_token=5),
                    DepRow(line=1, token=5, word="digiuno", deprel="xcomp",
                           head_line=1, head_token=3)]}
    violations = skel.validate_unit(nos, texts, rows, morph_rows, np_rows, dep_rows)
    assert not any("heads no NP" in v.detail for v in violations)
    # A citation nothing corroborates still fails: point the same row at the preposition.
    rows = {1: [skel.SkelRow(1, 3, "vedere", "obj", 1, 2)]}
    violations = skel.validate_unit(nos, texts, rows, morph_rows, np_rows, dep_rows)
    assert any("heads no NP" in v.detail for v in violations)


# --- Inferno 31-34 read: rules BO-BV -------------------------------------------------


def _np_head_nmod_fixture(head=5):
    """"torreggiavan **di mezza la persona**" (inferno 31:43): Layer 4 heads the oblique on
    `mezza` and hangs `persona` under it as `nmod`; Layer 3 heads the whole span on `persona`."""
    from dante_corpus.np import NPSpan
    derived = {1: [skel.SkelRow(1, 1, "torreggiavan", "obl:di", 1, 3)]}
    given = {1: [skel.SkelRow(1, 1, "torreggiavan", "obl:di", 1, 5)]}
    dep_index_by_pos = {
        (1, 1): dep.DepRow(line=1, token=1, word="torreggiavan", deprel="root",
                           head_line=0, head_token=0),
        (1, 2): dep.DepRow(line=1, token=2, word="di", deprel="case", head_line=1, head_token=3),
        (1, 3): dep.DepRow(line=1, token=3, word="mezza", deprel="obl", head_line=1, head_token=1),
        (1, 5): dep.DepRow(line=1, token=5, word="persona", deprel="nmod",
                           head_line=1, head_token=3),
    }
    np_rows = {1: [NPSpan(line=1, start=3, end=5, head=head, text="mezza la persona")]}
    return given, derived, dep_index_by_pos, np_rows


def test_classify_divergence_rule_bo_runs_rule_ai_before_rule_d():
    # Rule D would drop the given citation as an accepted `nmod` adjunct and leave the derived
    # position reported as a `missing_arg`; rule AI re-keys it and both halves go quiet.
    given, derived, idx, np_rows = _np_head_nmod_fixture()
    assert skel._classify_divergence(given, derived, idx, {}, np_rows=np_rows) == []


def test_classify_divergence_rule_bo_leaves_a_non_head_nmod_to_rule_d():
    # The same tree where Layer 3 heads the span elsewhere: the two positions are not one noun
    # phrase named twice, so rule AI must not fire and the derived oblique stays reported.
    given, derived, idx, np_rows = _np_head_nmod_fixture(head=4)
    violations = skel._classify_divergence(given, derived, idx, {}, np_rows=np_rows)
    assert any(v.detail.startswith("missing_arg") for v in violations)


def _clitic_on_auxiliary_fixture(aux_deprel="aux"):
    """"tre Frison **s'**averien dato mal vanto" (inferno 31:64): the reflexive clitic is `expl`
    on the auxiliary, while the predicate carrying the tuple is the past participle."""
    derived = {1: [skel.SkelRow(1, 5, "dato", "obj", 1, 7)]}
    given = {1: [skel.SkelRow(1, 5, "dato", "obj", 1, 7),
                 skel.SkelRow(1, 5, "dato", "iobj", 1, 3)]}
    dep_index_by_pos = {
        (1, 3): dep.DepRow(line=1, token=3, word="s'", deprel="expl", head_line=1, head_token=4),
        (1, 4): dep.DepRow(line=1, token=4, word="averien", deprel=aux_deprel,
                           head_line=1, head_token=5),
        (1, 5): dep.DepRow(line=1, token=5, word="dato", deprel="root",
                           head_line=0, head_token=0),
        (1, 7): dep.DepRow(line=1, token=7, word="vanto", deprel="obj", head_line=1, head_token=5),
    }
    morph_pos = {(1, 3): "pronoun", (1, 4): "verb", (1, 5): "verb", (1, 7): "noun"}
    return given, derived, dep_index_by_pos, morph_pos


def test_classify_divergence_rule_bp_reads_a_child_through_its_auxiliary():
    given, derived, idx, morph_pos = _clitic_on_auxiliary_fixture()
    assert skel._classify_divergence(given, derived, idx, morph_pos) == []


def test_classify_divergence_rule_bp_leaves_a_clitic_on_an_unrelated_word_flagged():
    # The intervening word is not an auxiliary, so the clitic is not this predicate's child.
    given, derived, idx, morph_pos = _clitic_on_auxiliary_fixture(aux_deprel="conj")
    violations = skel._classify_divergence(given, derived, idx, morph_pos)
    assert any(v.detail.startswith("extra_arg") for v in violations)


def _bare_adverb_cluster_fixture(extra_child=None):
    """"tenea soccinto **dinanzi l'altro**" (inferno 31:87): the nominal hangs bare under the
    adjunct adverb, with no preposition of its own."""
    derived = {1: [skel.SkelRow(1, 1, "tenea", "obl", 1, 2)]}
    given = {1: [skel.SkelRow(1, 1, "tenea", "obl:dinanzi", 1, 4)]}
    dep_index_by_pos = {
        (1, 1): dep.DepRow(line=1, token=1, word="tenea", deprel="root",
                           head_line=0, head_token=0),
        (1, 2): dep.DepRow(line=1, token=2, word="dinanzi", deprel="obl",
                           head_line=1, head_token=1),
        (1, 4): dep.DepRow(line=1, token=4, word="altro", deprel="obl", head_line=1, head_token=2),
    }
    if extra_child is not None:
        dep_index_by_pos[(1, 5)] = dep.DepRow(line=1, token=5, word="che", deprel=extra_child,
                                              head_line=1, head_token=4)
    morph_pos = {(1, 1): "verb", (1, 2): "adverb", (1, 4): "adjective", (1, 5): "conjunction"}
    return given, derived, dep_index_by_pos, morph_pos


def test_classify_divergence_rule_bq_merges_a_bare_nominal_onto_its_adverb():
    given, derived, idx, morph_pos = _bare_adverb_cluster_fixture()
    assert skel._classify_divergence(given, derived, idx, morph_pos) == []


def test_classify_divergence_rule_bq_leaves_a_marked_second_term_flagged():
    # A `mark` on the nominal makes it the second term of a comparison, which rules BK/BL own.
    given, derived, idx, morph_pos = _bare_adverb_cluster_fixture(extra_child="mark")
    violations = skel._classify_divergence(given, derived, idx, morph_pos)
    assert any(v.detail.startswith("missing_arg") for v in violations)


def _nested_phrase_fixture(head=1):
    """"**Gualandi con Sismondi e con Lanfranchi** s'avea messi" (inferno 33:33): Layer 3 reads
    the comitative chain as one subject phrase, Layer 4 hangs `Sismondi` off the verb as well."""
    from dante_corpus.np import NPSpan
    derived = {1: [skel.SkelRow(1, 7, "messi", "subj", 1, 1),
                   skel.SkelRow(1, 7, "messi", "obl:con", 1, 3)]}
    given = {1: [skel.SkelRow(1, 7, "messi", "subj", 1, 1)]}
    dep_index_by_pos = {
        (1, 1): dep.DepRow(line=1, token=1, word="Gualandi", deprel="nsubj",
                           head_line=1, head_token=7),
        (1, 2): dep.DepRow(line=1, token=2, word="con", deprel="case", head_line=1, head_token=3),
        (1, 3): dep.DepRow(line=1, token=3, word="Sismondi", deprel="obl",
                           head_line=1, head_token=7),
        (1, 7): dep.DepRow(line=1, token=7, word="messi", deprel="root",
                           head_line=0, head_token=0),
    }
    np_rows = {1: [NPSpan(line=1, start=1, end=3, head=head, text="Gualandi con Sismondi")]}
    return given, derived, dep_index_by_pos, np_rows


def test_classify_divergence_rule_br_accepts_a_phrase_named_by_its_head():
    given, derived, idx, np_rows = _nested_phrase_fixture()
    assert skel._classify_divergence(given, derived, idx, {}, np_rows=np_rows) == []


def test_classify_divergence_rule_br_leaves_an_uncited_phrase_flagged():
    # Layer 3 heads the span on the buried word itself, so nothing the LLM cited covers it.
    given, derived, idx, np_rows = _nested_phrase_fixture(head=3)
    violations = skel._classify_divergence(given, derived, idx, {}, np_rows=np_rows)
    assert any(v.detail.startswith("missing_arg") for v in violations)


def _free_relative_matrix_fixture(head_lemma="chi", clause_child=None):
    """"se vuoi saper **chi son cotesti due**" (inferno 32:55): Layer 4 hangs the embedded
    question under the interrogative pronoun, which fills that clause's own complement slot."""
    derived = {1: [skel.SkelRow(1, 5, "son", "subj", 1, 7)]}
    given = {1: [skel.SkelRow(1, 5, "son", "subj", 1, 7),
                 skel.SkelRow(1, 5, "son", "attr", 1, 4)]}
    dep_index_by_pos = {
        (1, 4): dep.DepRow(line=1, token=4, word="chi", deprel="attr", head_line=1, head_token=3),
        (1, 5): dep.DepRow(line=1, token=5, word="son", deprel="acl:relcl",
                           head_line=1, head_token=4),
        (1, 7): dep.DepRow(line=1, token=7, word="due", deprel="nsubj",
                           head_line=1, head_token=5),
    }
    morph_rows = {1: [morph.MorphRow(word=w, lemma=l, pos=p, note=n) for w, l, p, n in [
        ("se", "se", "conjunction", ""), ("vuoi", "volere", "verb", ""),
        ("saper", "sapere", "verb", ""), ("chi", head_lemma, "pronoun", ""),
        ("son", "essere", "verb", ""), ("cotesti", "cotesto", "adjective", ""),
        ("due", "due", "numeral", clause_child or ""),
    ]]}
    morph_pos = {(1, 4): "pronoun", (1, 5): "verb", (1, 7): "numeral"}
    morph_lemma = {(1, 4): head_lemma}
    return given, derived, dep_index_by_pos, morph_pos, morph_lemma, morph_rows


def test_classify_divergence_rule_bt_accepts_the_clauses_own_governor():
    given, derived, idx, morph_pos, lemma, morph_rows = _free_relative_matrix_fixture()
    assert skel._classify_divergence(given, derived, idx, morph_pos,
                                     morph_lemma_by_position=lemma,
                                     morph_rows=morph_rows) == []


def test_classify_divergence_rule_bt_leaves_a_correlative_antecedent_flagged():
    # `colui` is an ordinary antecedent, not a free relative: it is emphatically not an argument
    # of the clause hanging under it.
    given, derived, idx, morph_pos, lemma, morph_rows = _free_relative_matrix_fixture(
        head_lemma="colui")
    violations = skel._classify_divergence(given, derived, idx, morph_pos,
                                           morph_lemma_by_position=lemma,
                                           morph_rows=morph_rows)
    assert any(v.detail.startswith("extra_arg") for v in violations)


def test_classify_divergence_rule_bt_leaves_a_clause_with_its_own_relative_flagged():
    given, derived, idx, morph_pos, lemma, morph_rows = _free_relative_matrix_fixture(
        clause_child="relative")
    violations = skel._classify_divergence(given, derived, idx, morph_pos,
                                           morph_lemma_by_position=lemma,
                                           morph_rows=morph_rows)
    assert any(v.detail.startswith("extra_arg") for v in violations)


def _conjunct_subject_fixture(conj_deprel="conj"):
    """"**lasciò** qui loco vòto / **quella** ch'appar di qua, e sù **ricorse**" (inferno 34:125):
    the coordination head has no subject of its own and the overt `nsubj` is on its conjunct."""
    derived = {2: [skel.SkelRow(2, 1, "lasciò", "subj", 1, 1)]}
    given = {2: [skel.SkelRow(2, 1, "lasciò", "subj", 3, 1)]}
    dep_index_by_pos = {
        (1, 1): dep.DepRow(line=1, token=1, word="venne", deprel="root",
                           head_line=0, head_token=0),
        (2, 1): dep.DepRow(line=2, token=1, word="lasciò", deprel="conj",
                           head_line=1, head_token=1),
        (3, 1): dep.DepRow(line=3, token=1, word="quella", deprel="nsubj",
                           head_line=3, head_token=2),
        (3, 2): dep.DepRow(line=3, token=2, word="ricorse", deprel=conj_deprel,
                           head_line=2, head_token=1),
    }
    given_by_pred = {(1, 1): [skel.SkelRow(1, 1, "venne", "subj", 1, 3)]}
    return given, derived, dep_index_by_pos, given_by_pred


def test_classify_divergence_rule_bu_takes_the_subject_from_the_conjunct():
    given, derived, idx, _ = _conjunct_subject_fixture()
    assert skel._classify_divergence(given, derived, idx, {}) == []


def test_classify_divergence_rule_bu_leaves_an_unrelated_clauses_subject_flagged():
    # The clause carrying the overt subject is not this predicate's conjunct.
    given, derived, idx, _ = _conjunct_subject_fixture(conj_deprel="advcl")
    violations = skel._classify_divergence(given, derived, idx, {})
    assert any(v.detail.startswith("extra_arg") for v in violations)


def _prep_stack_citation_fixture(member_deprel="fixed"):
    """"Usa **con esso** donno Michel Zanche" (inferno 22:88): the reinforced preposition is
    normalized as `con` -> `case` on the nominal, `esso` -> `fixed` on `con`."""
    derived = {1: [skel.SkelRow(1, 1, "Usa", "obl:con", 1, 4)]}
    given = {1: [skel.SkelRow(1, 1, "Usa", "obl:con", 1, 3)]}
    dep_index_by_pos = {
        (1, 1): dep.DepRow(line=1, token=1, word="Usa", deprel="root",
                           head_line=0, head_token=0),
        (1, 2): dep.DepRow(line=1, token=2, word="con", deprel="case", head_line=1, head_token=4),
        (1, 3): dep.DepRow(line=1, token=3, word="esso", deprel=member_deprel,
                           head_line=1, head_token=2),
        (1, 4): dep.DepRow(line=1, token=4, word="donno", deprel="obl", head_line=1, head_token=1),
    }
    return given, derived, dep_index_by_pos


def test_classify_divergence_rule_bv_merges_a_fixed_member_onto_its_nominal():
    given, derived, idx = _prep_stack_citation_fixture()
    assert skel._classify_divergence(given, derived, idx, {}) == []


def test_classify_divergence_rule_bv_leaves_a_real_dependent_flagged():
    # An `appos` under the preposition is a word of its own, not part of the preposition.
    given, derived, idx = _prep_stack_citation_fixture(member_deprel="appos")
    violations = skel._classify_divergence(given, derived, idx, {})
    assert any(v.detail.startswith("extra_arg") for v in violations)


def _marker_slot_fixture(marker_pos="pronoun"):
    """"un non **sapeva che** bianco" (purgatorio 2:23): the interrogative `che` opens the clause
    and fills its object slot, and Layer 4 can only record the first of the two."""
    derived = {1: [skel.SkelRow(1, 2, "sapeva", "obj", 1, 4)]}
    given = {1: [skel.SkelRow(1, 2, "sapeva", "obj", 1, 3),
                 skel.SkelRow(1, 2, "sapeva", "attr", 1, 4)]}
    dep_index_by_pos = {
        (1, 1): dep.DepRow(line=1, token=1, word="un", deprel="nsubj", head_line=1, head_token=2),
        (1, 2): dep.DepRow(line=1, token=2, word="sapeva", deprel="acl",
                           head_line=1, head_token=1),
        (1, 3): dep.DepRow(line=1, token=3, word="che", deprel="mark", head_line=1, head_token=2),
        (1, 4): dep.DepRow(line=1, token=4, word="bianco", deprel="obj",
                           head_line=1, head_token=2),
    }
    return given, derived, dep_index_by_pos, {(1, 3): marker_pos, (1, 4): "adjective"}


def test_classify_divergence_rule_bw_accepts_an_argument_in_a_mark_slot():
    given, derived, idx, morph_pos = _marker_slot_fixture()
    assert skel._classify_divergence(given, derived, idx, morph_pos) == []


def test_classify_divergence_rule_bw_leaves_a_conjunction_marker_flagged():
    # A `mark` Layer 2 calls a conjunction is a subordinator, which is rule BM's reading.
    given, derived, idx, morph_pos = _marker_slot_fixture(marker_pos="conjunction")
    violations = skel._classify_divergence(given, derived, idx, morph_pos)
    assert any(v.detail.startswith("extra_arg") for v in violations)


def _omitted_depictive_fixture(arg_pos="adjective", case_child=False):
    """"mi cominciò **tutto rivolto**" (purgatorio 3:23): the depictive is an adjunct of the
    predication, and the LLM leaves it out entirely."""
    derived = {1: [skel.SkelRow(1, 1, "cominciò", "subj", 1, 2),
                   skel.SkelRow(1, 1, "cominciò", "obl", 1, 3)]}
    given = {1: [skel.SkelRow(1, 1, "cominciò", "subj", 1, 2)]}
    dep_index_by_pos = {
        (1, 1): dep.DepRow(line=1, token=1, word="cominciò", deprel="root",
                           head_line=0, head_token=0),
        (1, 2): dep.DepRow(line=1, token=2, word="conforto", deprel="nsubj",
                           head_line=1, head_token=1),
        (1, 3): dep.DepRow(line=1, token=3, word="rivolto", deprel="obl",
                           head_line=1, head_token=1),
    }
    if case_child:
        dep_index_by_pos[(1, 4)] = dep.DepRow(line=1, token=4, word="per", deprel="case",
                                              head_line=1, head_token=3)
    return given, derived, dep_index_by_pos, {(1, 3): arg_pos}


def test_classify_divergence_rule_bx_accepts_an_omitted_bare_adjectival_oblique():
    given, derived, idx, morph_pos = _omitted_depictive_fixture()
    assert skel._classify_divergence(given, derived, idx, morph_pos) == []


def test_classify_divergence_rule_bx_leaves_a_nominal_oblique_flagged():
    given, derived, idx, morph_pos = _omitted_depictive_fixture(arg_pos="noun")
    violations = skel._classify_divergence(given, derived, idx, morph_pos)
    assert any(v.detail.startswith("missing_arg") for v in violations)


def test_classify_divergence_rule_bx_leaves_a_prepositional_adjunct_flagged():
    given, derived, idx, morph_pos = _omitted_depictive_fixture(case_child=True)
    violations = skel._classify_divergence(given, derived, idx, morph_pos)
    assert any(v.detail.startswith("missing_arg") for v in violations)


def _auxiliary_split_fixture(finite_deprel="aux"):
    """"quel da Esti **il fé far**" (purgatorio 5:77): the LLM puts the subject on the finite
    `fé` and the object on the infinitive Layer 4 made the head."""
    derived = {1: [skel.SkelRow(1, 3, "far", "subj", 1, 1),
                   skel.SkelRow(1, 3, "far", "obj", 1, 2)]}
    given = {1: [skel.SkelRow(1, 4, "fé", "subj", 1, 1),
                 skel.SkelRow(1, 3, "far", "obj", 1, 2)]}
    dep_index_by_pos = {
        (1, 1): dep.DepRow(line=1, token=1, word="quel", deprel="nsubj",
                           head_line=1, head_token=3),
        (1, 2): dep.DepRow(line=1, token=2, word="il", deprel="obj", head_line=1, head_token=3),
        (1, 3): dep.DepRow(line=1, token=3, word="far", deprel="root",
                           head_line=0, head_token=0),
        (1, 4): dep.DepRow(line=1, token=4, word="fé", deprel=finite_deprel,
                           head_line=1, head_token=3),
    }
    return given, derived, dep_index_by_pos


def test_classify_divergence_rule_by_accepts_an_argument_on_the_auxiliary():
    given, derived, idx = _auxiliary_split_fixture()
    assert skel._classify_divergence(given, derived, idx, {}) == []


def test_classify_divergence_rule_by_leaves_a_separate_clause_flagged():
    # A `conj` verb is a predicate of its own, not this predicate's periphrasis.
    given, derived, idx = _auxiliary_split_fixture(finite_deprel="conj")
    violations = skel._classify_divergence(given, derived, idx, {})
    assert any(v.detail.startswith("missing_arg") for v in violations)


def _conjunct_of_an_argument_verb(person="1", pos_tag="verb"):
    """"com' io rimango sol, **se non restai**" (purgatorio 4:45): `rimango` is the `obj` of
    `rimira`, so it becomes a predicate only in the derivation's second pass, and its `conj`
    has to be walked again afterwards."""
    dep_rows = {1: [
        dep.DepRow(line=1, token=1, word="rimira", deprel="root", head_line=0, head_token=0),
        dep.DepRow(line=1, token=2, word="rimango", deprel="obj", head_line=1, head_token=1),
        dep.DepRow(line=1, token=3, word="io", deprel="nsubj", head_line=1, head_token=2),
        dep.DepRow(line=1, token=4, word="restai", deprel="conj", head_line=1, head_token=2),
    ]}
    morph_rows = {1: [
        morph.MorphRow(word="rimira", pos="verb", person="2"),
        morph.MorphRow(word="rimango", pos="verb", person="1"),
        morph.MorphRow(word="io", pos="pronoun", person="1"),
        morph.MorphRow(word="restai", pos=pos_tag, person=person),
    ]}
    derived = skel.derive_unit([1], dep_rows, morph_rows)
    return {(r.line, r.token) for rows in derived.values() for r in rows}


def test_derive_unit_rule_bz_promotes_a_conjunct_of_a_second_pass_predicate():
    assert (1, 4) in _conjunct_of_an_argument_verb()


def test_derive_unit_rule_bz_leaves_a_non_finite_conjunct_alone():
    # An infinitive with no argument child of its own would carry an empty tuple.
    assert (1, 4) not in _conjunct_of_an_argument_verb(person="")


# --- Purgatorio 6-10 read: rules CA-CJ -------------------------------------------------


def _nominal_conjunct_of_a_clause(kids=(), pos_tag="noun"):
    """"Sordel rimase e **l'altre genti** forme" (purgatorio 9:58): UD promotes the coordinate
    nominal to the clause head, and it carries nothing a tuple could be built from."""
    rows = [
        dep.DepRow(line=1, token=1, word="Sordel", deprel="nsubj", head_line=1, head_token=2),
        dep.DepRow(line=1, token=2, word="rimase", deprel="root", head_line=0, head_token=0),
        dep.DepRow(line=1, token=3, word="genti", deprel="conj", head_line=1, head_token=2),
        dep.DepRow(line=1, token=4, word="forme", deprel="amod", head_line=1, head_token=3),
    ]
    morph_rows = {1: [
        morph.MorphRow(word="Sordel", pos="proper noun"),
        morph.MorphRow(word="rimase", pos="verb", person="3"),
        morph.MorphRow(word="genti", pos=pos_tag, person="3" if pos_tag == "verb" else ""),
        morph.MorphRow(word="forme", pos="noun"),
    ]}
    for token, word, deprel in kids:
        rows.append(dep.DepRow(line=1, token=token, word=word, deprel=deprel,
                               head_line=1, head_token=3))
        morph_rows[1].append(morph.MorphRow(word=word, pos="noun"))
    derived = skel.derive_unit([1], {1: rows}, morph_rows)
    return {(r.line, r.token) for rows_ in derived.values() for r in rows_}


def test_derive_unit_rule_ca_drops_an_argumentless_nominal_conjunct():
    assert (1, 3) not in _nominal_conjunct_of_a_clause()


def test_derive_unit_rule_ca_keeps_a_conjunct_with_an_argument_of_its_own():
    # "Ed **elli**: «Vedi …»" — the elided speech verb's `ccomp` is a real tuple.
    assert (1, 3) in _nominal_conjunct_of_a_clause(kids=[(5, "vedi", "ccomp")])


def test_derive_unit_rule_ca_keeps_a_copular_conjunct():
    # "Tant' **è amara**" (inferno 1:7): the `cop` child is the tree's own predication.
    assert (1, 3) in _nominal_conjunct_of_a_clause(kids=[(5, "è", "cop")])


def _promoted_conjunct_citation_fixture(conjunct_pos="noun", kids=()):
    """"qual merito o **qual grazia** mi ti mostra?" (purgatorio 7:19): the LLM reads the
    promoted conjunct as the predicate's second subject, and the derivation has no slot for it."""
    derived = {1: [skel.SkelRow(1, 3, "mostra", "subj", 1, 1)]}
    given = {1: [skel.SkelRow(1, 3, "mostra", "subj", 1, 1),
                 skel.SkelRow(1, 3, "mostra", "subj", 1, 2)]}
    dep_index_by_pos = {
        (1, 1): dep.DepRow(line=1, token=1, word="merito", deprel="nsubj",
                           head_line=1, head_token=3),
        (1, 2): dep.DepRow(line=1, token=2, word="grazia", deprel="conj",
                           head_line=1, head_token=3),
        (1, 3): dep.DepRow(line=1, token=3, word="mostra", deprel="root",
                           head_line=0, head_token=0),
    }
    for token, word, deprel in kids:
        dep_index_by_pos[(1, token)] = dep.DepRow(line=1, token=token, word=word, deprel=deprel,
                                                  head_line=1, head_token=2)
    return given, derived, dep_index_by_pos, {(1, 2): conjunct_pos}


def test_classify_divergence_rule_cc_accepts_a_promoted_coordinate_nominal():
    given, derived, idx, morph_pos = _promoted_conjunct_citation_fixture()
    assert skel._classify_divergence(given, derived, idx, morph_pos) == []


def test_classify_divergence_rule_cc_leaves_a_gapped_clause_flagged():
    # A conjunct with an argument of its own is an elided clause, not a coordinate argument.
    given, derived, idx, morph_pos = _promoted_conjunct_citation_fixture(
        kids=[(4, "briga", "obj")])
    violations = skel._classify_divergence(given, derived, idx, morph_pos)
    assert any(v.detail.startswith("extra_arg") for v in violations)


def _clause_coordination_walk(head_deprel="conj"):
    """"sen venne suso; e **io** per le sue orme" (purgatorio 9:60): the walk from a nominal
    conjunct onto a verb leaves the arguments' coordination and enters the predicates'."""
    dep_index_by_pos = {
        (1, 1): dep.DepRow(line=1, token=1, word="venne", deprel=head_deprel,
                           head_line=1, head_token=3),
        (1, 2): dep.DepRow(line=1, token=2, word="io", deprel="conj", head_line=1, head_token=1),
        (1, 3): dep.DepRow(line=1, token=3, word="rimase", deprel="root",
                           head_line=0, head_token=0),
    }
    morph_pos = {(1, 1): "verb", (1, 2): "pronoun", (1, 3): "verb"}
    return skel._coordination_head((1, 2), dep_index_by_pos, morph_pos)


def test_coordination_head_rule_cd_stops_at_a_clause_conjunct():
    assert _clause_coordination_walk() == (1, 2)


def test_coordination_head_rule_cd_walks_through_an_argument_verb():
    # "addimandò … di dispensare … ma **licenza**" (paradiso 12:95): the head verb is itself an
    # argument, so the nominal really is its coordinate member.
    assert _clause_coordination_walk(head_deprel="obj") == (1, 1)


def _underived_complement_fixture(complement_deprel="attr"):
    """"li occhi … e **al sì** e al no **discordi fensi**" (purgatorio 10:63): the oblique hangs
    on the predicative adjective, which the derivation never promotes to a predicate."""
    derived = {1: [skel.SkelRow(1, 1, "fensi", "xcomp", 1, 2)]}
    given = {1: [skel.SkelRow(1, 1, "fensi", "xcomp", 1, 2),
                 skel.SkelRow(1, 1, "fensi", "obl:a", 1, 4)]}
    dep_index_by_pos = {
        (1, 1): dep.DepRow(line=1, token=1, word="fensi", deprel="root",
                           head_line=0, head_token=0),
        (1, 2): dep.DepRow(line=1, token=2, word="discordi", deprel=complement_deprel,
                           head_line=1, head_token=1),
        (1, 3): dep.DepRow(line=1, token=3, word="al", deprel="case", head_line=1, head_token=4),
        (1, 4): dep.DepRow(line=1, token=4, word="sì", deprel="obl", head_line=1, head_token=2),
    }
    return skel._classify_divergence(given, derived, dep_index_by_pos, {})


def test_classify_divergence_rule_cb_accepts_an_argument_on_an_underived_complement():
    assert _underived_complement_fixture() == []


def test_classify_divergence_rule_cb_leaves_an_adjunct_host_flagged():
    # An `advcl` host is a clause of its own, whose obliques are its own.
    violations = _underived_complement_fixture(complement_deprel="advcl")
    assert any(v.detail.startswith("extra_arg") for v in violations)


def _relative_antecedent_fixture(pronoun="che"):
    """"O superbi cristian … **che** … de la mente **infermi**, fidanza avete" (purgatorio
    10:122): the depictive's subject is the relative pronoun standing for the antecedent, and
    the antecedent itself hangs on the matrix verb, whose own subject is somebody else."""
    derived = {1: [skel.SkelRow(1, 4, "avete", "subj", 1, 2),
                   skel.SkelRow(1, 6, "accorgete", "subj", 1, 7),
                   skel.SkelRow(1, 3, "infermi", "obl:di", 1, 5)]}
    given = {1: [skel.SkelRow(1, 4, "avete", "subj", 1, 2),
                 skel.SkelRow(1, 6, "accorgete", "subj", 1, 7),
                 skel.SkelRow(1, 3, "infermi", "subj", 1, 2),
                 skel.SkelRow(1, 3, "infermi", "obl:di", 1, 5)]}
    dep_index_by_pos = {
        (1, 1): dep.DepRow(line=1, token=1, word="cristian", deprel="vocative",
                           head_line=1, head_token=6),
        (1, 2): dep.DepRow(line=1, token=2, word=pronoun, deprel="nsubj",
                           head_line=1, head_token=4),
        (1, 3): dep.DepRow(line=1, token=3, word="infermi", deprel="acl:relcl",
                           head_line=1, head_token=1),
        (1, 4): dep.DepRow(line=1, token=4, word="avete", deprel="acl:relcl",
                           head_line=1, head_token=1),
        (1, 5): dep.DepRow(line=1, token=5, word="vista", deprel="obl",
                           head_line=1, head_token=3),
        (1, 6): dep.DepRow(line=1, token=6, word="accorgete", deprel="root",
                           head_line=0, head_token=0),
        (1, 7): dep.DepRow(line=1, token=7, word="voi", deprel="nsubj",
                           head_line=1, head_token=6),
    }
    morph_rows = {1: [
        morph.MorphRow(word="cristian", pos="noun"),
        morph.MorphRow(word=pronoun, pos="pronoun"),
        morph.MorphRow(word="infermi", pos="adjective"),
        morph.MorphRow(word="avete", pos="verb", person="2"),
        morph.MorphRow(word="vista", pos="noun"),
        morph.MorphRow(word="accorgete", pos="verb", person="2"),
        morph.MorphRow(word="voi", pos="pronoun"),
    ]}
    return skel._classify_divergence(given, derived, dep_index_by_pos, {}, None, None, morph_rows)


def test_classify_divergence_rule_ce_accepts_the_antecedents_relative_pronoun():
    assert _relative_antecedent_fixture() == []


def test_classify_divergence_rule_ce_leaves_an_unrelated_clauses_subject_flagged():
    # A nominal subject of the relative clause is a different referent from the antecedent.
    violations = _relative_antecedent_fixture(pronoun="ella")
    assert any(v.detail.startswith("extra_arg") for v in violations)


def _fused_clitic_control_fixture(host_pos="verb+pronoun"):
    """"a **tenerla serrata**" (purgatorio 9:128): the controller is the clitic fused into the
    host verb, which has no position of its own to be cited by."""
    derived = {1: [skel.SkelRow(1, 1, "tenerla", "xcomp", 1, 2),
                   skel.SkelRow(1, 2, "serrata", "", 0, 0)]}
    given = {1: [skel.SkelRow(1, 1, "tenerla", "xcomp", 1, 2),
                 skel.SkelRow(1, 2, "serrata", "subj", 1, 1)]}
    dep_index_by_pos = {
        (1, 1): dep.DepRow(line=1, token=1, word="tenerla", deprel="root",
                           head_line=0, head_token=0),
        (1, 2): dep.DepRow(line=1, token=2, word="serrata", deprel="xcomp",
                           head_line=1, head_token=1),
    }
    morph_rows = {1: [
        morph.MorphRow(word="tenerla", pos=host_pos),
        morph.MorphRow(word="serrata", pos="adjective"),
    ]}
    return skel._classify_divergence(given, derived, dep_index_by_pos, {}, None, None, morph_rows)


def test_classify_divergence_rule_cf_accepts_a_fused_clitic_controller():
    assert _fused_clitic_control_fixture() == []


def test_classify_divergence_rule_cf_leaves_a_plain_host_flagged():
    # With no clitic fused into it the host verb is not an argument of its own clause.
    violations = _fused_clitic_control_fixture(host_pos="verb")
    assert any(v.detail.startswith("extra_arg") for v in violations)


def _gapped_oblique_fixture(second_case=True):
    """"or dal sinistro e or dal destro fianco" (purgatorio 10:27): two prepositions on one
    surviving noun, and the elided first phrase citable only by its adjective."""
    derived = {1: [skel.SkelRow(1, 1, "parea", "obl:da", 1, 5)]}
    given = {1: [skel.SkelRow(1, 1, "parea", "obl:da", 1, 5),
                 skel.SkelRow(1, 1, "parea", "obl:da", 1, 3)]}
    dep_index_by_pos = {
        (1, 1): dep.DepRow(line=1, token=1, word="parea", deprel="root",
                           head_line=0, head_token=0),
        (1, 2): dep.DepRow(line=1, token=2, word="dal", deprel="case", head_line=1, head_token=5),
        (1, 3): dep.DepRow(line=1, token=3, word="sinistro", deprel="amod",
                           head_line=1, head_token=5),
        (1, 5): dep.DepRow(line=1, token=5, word="fianco", deprel="obl",
                           head_line=1, head_token=1),
    }
    if second_case:
        dep_index_by_pos[(1, 4)] = dep.DepRow(line=1, token=4, word="dal", deprel="case",
                                              head_line=1, head_token=5)
    return skel._classify_divergence(given, derived, dep_index_by_pos, {})


def test_classify_divergence_rule_cg_accepts_an_elided_coordinate_oblique():
    assert _gapped_oblique_fixture() == []


def test_classify_divergence_rule_cg_leaves_a_plain_modifier_flagged():
    # One preposition is one oblique: an ordinary attributive adjective is not a second phrase.
    violations = _gapped_oblique_fixture(second_case=False)
    assert any(v.detail.startswith("extra_arg") for v in violations)


def _adnominal_participle_fixture(host_deprel="amod", pos_tag="verb"):
    """"come fogliette pur mo **nate**" (purgatorio 8:28): a reduced relative with nothing but
    its subject, which is exactly what the derivation's second pass cannot find it by."""
    derived = {1: [skel.SkelRow(1, 1, "erano", "obl:come", 1, 2)]}
    given = {1: [skel.SkelRow(1, 1, "erano", "obl:come", 1, 2),
                 skel.SkelRow(1, 3, "nate", "subj", 1, 2)]}
    dep_index_by_pos = {
        (1, 1): dep.DepRow(line=1, token=1, word="erano", deprel="root",
                           head_line=0, head_token=0),
        (1, 2): dep.DepRow(line=1, token=2, word="fogliette", deprel="obl",
                           head_line=1, head_token=1),
        (1, 3): dep.DepRow(line=1, token=3, word="nate", deprel=host_deprel,
                           head_line=1, head_token=2),
    }
    return skel._classify_divergence(given, derived, dep_index_by_pos,
                                     {(1, 2): "noun", (1, 3): pos_tag})


def test_classify_divergence_rule_ch_accepts_an_adnominal_participle_tuple():
    assert not any(v.detail.startswith("extra_tuple")
                   for v in _adnominal_participle_fixture())


def test_classify_divergence_rule_ch_leaves_a_nominal_modifier_flagged():
    # "l'altre genti **forme**" (purgatorio 9:58): a noun in `amod` heads no clause.
    violations = _adnominal_participle_fixture(pos_tag="noun")
    assert any(v.detail.startswith("extra_tuple") for v in violations)


def _coordinate_small_clause_fixture(host_deprel="conj"):
    """"ma vidi bene e l'uno e **l'altro mosso**" (purgatorio 8:105): the participle hangs on
    the second conjunct of the object."""
    derived = {1: [skel.SkelRow(1, 1, "vidi", "obj", 1, 2)]}
    given = {1: [skel.SkelRow(1, 1, "vidi", "obj", 1, 2),
                 skel.SkelRow(1, 1, "vidi", "xcomp", 1, 4)]}
    dep_index_by_pos = {
        (1, 1): dep.DepRow(line=1, token=1, word="vidi", deprel="root",
                           head_line=0, head_token=0),
        (1, 2): dep.DepRow(line=1, token=2, word="uno", deprel="obj", head_line=1, head_token=1),
        (1, 3): dep.DepRow(line=1, token=3, word="altro", deprel=host_deprel,
                           head_line=1, head_token=2),
        (1, 4): dep.DepRow(line=1, token=4, word="mosso", deprel="acl",
                           head_line=1, head_token=3),
    }
    return skel._classify_divergence(given, derived, dep_index_by_pos,
                                     {(1, 3): "adjective", (1, 4): "adjective"})


def test_classify_divergence_rule_ci_reads_the_host_through_its_coordination():
    assert _coordinate_small_clause_fixture() == []


def test_classify_divergence_rule_ci_leaves_an_unrelated_host_flagged():
    # A participle on a nominal outside this predicate's arguments is not its small clause.
    violations = _coordinate_small_clause_fixture(host_deprel="nmod")
    assert any(v.detail.startswith("extra_arg") for v in violations)


def _oblique_controller_fixture(controller_role="obl"):
    """"s'avacci **lor** divenir **sante**" (purgatorio 6:27): the controller is the possessor
    Layer 4 wrote as an oblique."""
    derived = {1: [skel.SkelRow(1, 1, "avacci", "subj", 1, 3),
                   skel.SkelRow(1, 1, "avacci", controller_role, 1, 2),
                   skel.SkelRow(1, 4, "sante", "", 0, 0)]}
    given = {1: [skel.SkelRow(1, 1, "avacci", "subj", 1, 3),
                 skel.SkelRow(1, 1, "avacci", controller_role, 1, 2),
                 skel.SkelRow(1, 4, "sante", "subj", 1, 2)]}
    dep_index_by_pos = {
        (1, 1): dep.DepRow(line=1, token=1, word="avacci", deprel="root",
                           head_line=0, head_token=0),
        (1, 2): dep.DepRow(line=1, token=2, word="lor", deprel="obl", head_line=1, head_token=1),
        (1, 3): dep.DepRow(line=1, token=3, word="divenir", deprel="nsubj",
                           head_line=1, head_token=1),
        (1, 4): dep.DepRow(line=1, token=4, word="sante", deprel="xcomp",
                           head_line=1, head_token=3),
    }
    morph_rows = {1: [
        morph.MorphRow(word="avacci", pos="verb", person="3"),
        morph.MorphRow(word="lor", pos="pronoun"),
        morph.MorphRow(word="divenir", pos="verb"),
        morph.MorphRow(word="sante", pos="adjective"),
    ]}
    return skel._classify_divergence(given, derived, dep_index_by_pos, {}, None, None, morph_rows)


def test_classify_divergence_rule_cj_accepts_an_oblique_controller():
    assert _oblique_controller_fixture() == []


def test_classify_divergence_rule_cj_leaves_an_uncollected_role_flagged():
    # `ccomp` is not an argument a control chain can take its subject from.
    violations = _oblique_controller_fixture(controller_role="ccomp")
    assert any(v.detail.startswith("extra_arg") for v in violations)


def _clause_marker_fixture(marker_deprel="mark"):
    """"degno / ben è **che** 'l nome di tal valle **pèra**" (purgatorio 14:30): the LLM names
    the subject clause by the `che` that opens it, the derivation by its verb."""
    derived = {1: [skel.SkelRow(1, 2, "è", "subj", 1, 5)]}
    given = {1: [skel.SkelRow(1, 2, "è", "subj", 1, 3)]}
    dep_index_by_pos = {
        (1, 2): dep.DepRow(line=1, token=2, word="è", deprel="root",
                           head_line=0, head_token=0),
        (1, 3): dep.DepRow(line=1, token=3, word="che", deprel=marker_deprel,
                           head_line=1, head_token=5),
        (1, 5): dep.DepRow(line=1, token=5, word="pèra", deprel="csubj",
                           head_line=1, head_token=2),
    }
    return skel._classify_divergence(given, derived, dep_index_by_pos, {})


def test_classify_divergence_rule_ck_accepts_a_clause_named_by_its_marker():
    assert _clause_marker_fixture() == []


def test_classify_divergence_rule_ck_leaves_a_non_marker_citation_flagged():
    # A token that is not the clause's `mark` names something else, whatever it sits next to.
    violations = _clause_marker_fixture(marker_deprel="advmod")
    assert {v.detail.split(":")[0] for v in violations} == {"extra_arg", "missing_arg"}


def _fused_clitic_slot_fixture(case_value="reflexive+ablative"):
    """"in Siena **sen** pispiglia" (purgatorio 11:111): `si` + `ne` in one token, whose two
    annex slots back the two readings separately."""
    derived = {1: [skel.SkelRow(1, 2, "pispiglia", "obj", 1, 1)]}
    given = {1: [skel.SkelRow(1, 2, "pispiglia", "obl:di", 1, 1)]}
    dep_index_by_pos = {
        (1, 1): dep.DepRow(line=1, token=1, word="sen", deprel="obj",
                           head_line=1, head_token=2),
        (1, 2): dep.DepRow(line=1, token=2, word="pispiglia", deprel="root",
                           head_line=0, head_token=0),
    }
    return skel._classify_divergence(given, derived, dep_index_by_pos,
                                     {(1, 1): "pronoun+pronoun"},
                                     {(1, 1): case_value})


def test_classify_divergence_rule_cm_accepts_a_fused_clitic_filling_two_slots():
    assert _fused_clitic_slot_fixture() == []


def test_classify_divergence_rule_cm_leaves_a_single_slot_mismatch_flagged():
    # One slot backing both sides decides nothing, so the roles stay in dispute.
    violations = _fused_clitic_slot_fixture(case_value="ablative")
    assert any(v.detail.startswith("role_mismatch") for v in violations)


def _gapped_remnant_slot_fixture(subject_arg=(0, 0)):
    """"molti di vita e **sé** di pregio priva" (purgatorio 14:63): the ∅ subject slot must not
    take the first remnant ahead of the overt object."""
    dep_rows = {1: [
        dep.DepRow(line=1, token=1, word="molti", deprel="obj", head_line=1, head_token=8),
        dep.DepRow(line=1, token=2, word="di", deprel="case", head_line=1, head_token=3),
        dep.DepRow(line=1, token=3, word="vita", deprel="obl", head_line=1, head_token=8),
        dep.DepRow(line=1, token=4, word="e", deprel="cc", head_line=1, head_token=5),
        dep.DepRow(line=1, token=5, word="sé", deprel="conj", head_line=1, head_token=8),
        dep.DepRow(line=1, token=6, word="di", deprel="case", head_line=1, head_token=7),
        dep.DepRow(line=1, token=7, word="pregio", deprel="orphan", head_line=1, head_token=5),
        dep.DepRow(line=1, token=8, word="priva", deprel="root", head_line=0, head_token=0),
    ]}
    if subject_arg != (0, 0):
        dep_rows[1].append(dep.DepRow(line=1, token=9, word="ella", deprel="nsubj",
                                      head_line=1, head_token=8))
    morph_rows = {1: [
        morph.MorphRow(word="molti", pos="pronoun"),
        morph.MorphRow(word="di", pos="preposition"),
        morph.MorphRow(word="vita", pos="noun"),
        morph.MorphRow(word="e", pos="conjunction"),
        morph.MorphRow(word="sé", pos="pronoun"),
        morph.MorphRow(word="di", pos="preposition"),
        morph.MorphRow(word="pregio", pos="noun"),
        morph.MorphRow(word="priva", pos="verb", person="3"),
        morph.MorphRow(word="ella", pos="pronoun", person="3"),
    ]}
    derived = skel.derive_unit([1], dep_rows, morph_rows)
    return {(r.role, r.arg_line, r.arg_token) for r in derived[1] if r.line == 1 and r.token == 8}


def test_derive_unit_rule_cn_gives_a_gapped_remnant_the_overt_slot_first():
    assert ("obj", 1, 5) in _gapped_remnant_slot_fixture()
    assert ("subj", 1, 5) not in _gapped_remnant_slot_fixture()


def test_derive_unit_rule_cn_still_offers_an_overt_subject_slot():
    # With a real subject in the line the slot is an ordinary one and keeps its place in the
    # order the arguments stand in.
    slots = _gapped_remnant_slot_fixture(subject_arg=(1, 9))
    assert ("subj", 1, 5) in slots


def _advmod_secondary_predicate_fixture(deprel="advmod"):
    """"Io non son … esser contento **più digiuno**" (purgatorio 15:58): a second predicative
    adjective Layer 4 hangs on the complement rather than on the copula."""
    derived = {1: [skel.SkelRow(1, 1, "esser", "xcomp", 1, 2)]}
    given = {1: [skel.SkelRow(1, 1, "esser", "xcomp", 1, 2),
                 skel.SkelRow(1, 1, "esser", "attr", 1, 3)]}
    dep_index_by_pos = {
        (1, 1): dep.DepRow(line=1, token=1, word="esser", deprel="root",
                           head_line=0, head_token=0),
        (1, 2): dep.DepRow(line=1, token=2, word="contento", deprel="xcomp",
                           head_line=1, head_token=1),
        (1, 3): dep.DepRow(line=1, token=3, word="digiuno", deprel=deprel,
                           head_line=1, head_token=2),
    }
    return skel._classify_divergence(given, derived, dep_index_by_pos,
                                     {(1, 2): "adjective", (1, 3): "adjective"})


def test_classify_divergence_rule_co_accepts_an_advmod_secondary_predicate():
    assert _advmod_secondary_predicate_fixture() == []


def test_classify_divergence_rule_co_leaves_an_unrelated_deprel_flagged():
    # `nmod` is a phrase-internal relation, not a predication over the argument.
    violations = _advmod_secondary_predicate_fixture(deprel="nmod")
    assert any(v.detail.startswith("extra_arg") for v in violations)


def _ag_reachable_fixture(cited_subj=(2, 7)):
    """"li occhi … de la mia donna, e l'animo con essi, / e da ogne altro intento s'era tolto"
    (paradiso 21:1-3): `tolto` is a `conj` whose inherited subject rule AG drops on person, and
    the subject the LLM resolves is the coordination head's *other* derived subject."""
    derived = {
        1: [skel.SkelRow(1, 6, "rifissi", "subj", 1, 4),
            skel.SkelRow(1, 6, "rifissi", "subj", 2, 7)],
        3: [skel.SkelRow(3, 8, "tolto", "subj", 1, 4)],
    }
    given = {
        1: [skel.SkelRow(1, 6, "rifissi", "subj", 1, 4),
            skel.SkelRow(1, 6, "rifissi", "subj", 2, 7)],
        3: [skel.SkelRow(3, 8, "tolto", "subj", *cited_subj)],
    }
    dep_index_by_pos = {
        (1, 4): dep.DepRow(line=1, token=4, word="occhi", deprel="nsubj",
                           head_line=1, head_token=6),
        (1, 6): dep.DepRow(line=1, token=6, word="rifissi", deprel="root",
                           head_line=0, head_token=0),
        (2, 7): dep.DepRow(line=2, token=7, word="animo", deprel="nsubj",
                           head_line=1, head_token=6),
        (3, 8): dep.DepRow(line=3, token=8, word="tolto", deprel="conj",
                           head_line=1, head_token=6),
    }
    morph_rows = {
        1: [morph.MorphRow(word="li"), morph.MorphRow(word="occhi", pos="noun", number="pl."),
            morph.MorphRow(word="de"), morph.MorphRow(word="occhi", pos="noun", number="pl."),
            morph.MorphRow(word="mia"),
            morph.MorphRow(word="rifissi", pos="verb", number="pl.", person="1")],
        2: [morph.MorphRow(word=w) for w in "de la mia donna e l".split()]
            + [morph.MorphRow(word="animo", pos="noun", number="sg.")],
        3: [morph.MorphRow(word=w) for w in "e da ogne altro intento s era".split()]
            + [morph.MorphRow(word="tolto", pos="verb", number="sg.", person="3")],
    }
    return skel._classify_divergence(given, derived, dep_index_by_pos, None, None, None,
                                     morph_rows)


def test_classify_divergence_rule_cl_accepts_a_reachable_subject_after_ag_drops_one():
    # Rule AG drops the 1pl `occhi` off the 3sg `tolto`; the derivation is then silent about the
    # slot, so rule V's candidate test decides it, exactly as it does for a non-finite predicate.
    assert _ag_reachable_fixture() == []


def test_classify_divergence_rule_cl_keeps_an_unreachable_subject_flagged():
    # A citation the control walk cannot reach at all — a token that is no argument of the
    # coordination head — is the LLM's own claim about the slot, and stays reported.
    violations = _ag_reachable_fixture(cited_subj=(2, 4))
    assert any(v.detail.startswith("extra_arg") and v.arg == (2, 4) for v in violations)


# --- Purgatorio 16-20 read: rules CP-CT ------------------------------------------------


def _bare_nominal_oblique_fixture(arg_pos="noun"):
    """"come fatto fui **roman pastore**" (purgatorio 19:107): the predicative nominal Layer 4
    hung on the predicate as a bare `obl`, rule AZ's noun leg."""
    derived = {1: [skel.SkelRow(1, 3, "fatto", "obl", 1, 6)]}
    given = {1: [skel.SkelRow(1, 3, "fatto", "attr", 1, 6)]}
    dep_index_by_pos = {
        (1, 3): dep.DepRow(line=1, token=3, word="fatto", deprel="advcl",
                           head_line=1, head_token=8),
        (1, 6): dep.DepRow(line=1, token=6, word="pastore", deprel="obl",
                           head_line=1, head_token=3),
    }
    return skel._classify_divergence(given, derived, dep_index_by_pos, {(1, 6): arg_pos})


def test_classify_divergence_rule_cp_accepts_a_bare_nominal_secondary_predicate():
    assert _bare_nominal_oblique_fixture() == []


def test_classify_divergence_rule_cp_leaves_a_pronoun_flagged():
    # "pronoun" contains "noun": the clitic leg is rules AB/AW's question, not this one.
    violations = _bare_nominal_oblique_fixture(arg_pos="pronoun")
    assert any(v.detail.startswith("role_mismatch") for v in violations)


def test_classify_divergence_rule_cp_leaves_an_adverb_flagged():
    violations = _bare_nominal_oblique_fixture(arg_pos="adverb")
    assert any(v.detail.startswith("role_mismatch") for v in violations)


def _marked_xcomp_fixture(marker_head=(1, 5)):
    """"mi fé desideroso **di sapere**" (purgatorio 20:146): the infinitive Layer 4 attached as
    `xcomp` while writing its preposition as a `case` child."""
    derived = {1: [skel.SkelRow(1, 3, "desideroso", "xcomp", 1, 5)]}
    given = {1: [skel.SkelRow(1, 3, "desideroso", "obl:di", 1, 5)]}
    dep_index_by_pos = {
        (1, 3): dep.DepRow(line=1, token=3, word="desideroso", deprel="xcomp",
                           head_line=1, head_token=2),
        (1, 4): dep.DepRow(line=1, token=4, word="di", deprel="case",
                           head_line=marker_head[0], head_token=marker_head[1]),
        (1, 5): dep.DepRow(line=1, token=5, word="sapere", deprel="xcomp",
                           head_line=1, head_token=3),
    }
    return skel._classify_divergence(given, derived, dep_index_by_pos, {})


def test_classify_divergence_rule_cq_accepts_a_marked_complement_clause():
    assert _marked_xcomp_fixture() == []


def test_classify_divergence_rule_cq_leaves_a_preposition_of_another_token_flagged():
    # "pare a' lor vivagni" (paradiso 9:135): the preposition marks the dative beside it, not
    # the complement, so nothing in the tree corroborates the oblique reading.
    violations = _marked_xcomp_fixture(marker_head=(1, 6))
    assert any(v.detail.startswith("role_mismatch") for v in violations)


def _empty_tuple_fixture(deprel="root"):
    """"**Nullo**, però che 'l pastor … rugumar può" (purgatorio 16:98): the elliptical answer
    Layer 4 heads its clause with, whose verb is gapped from the previous parse unit."""
    derived = {
        1: [skel.SkelRow(1, 1, "Nullo", "", 0, 0)],
        2: [skel.SkelRow(2, 2, "può", "subj", 1, 5)],
    }
    given = {2: [skel.SkelRow(2, 2, "può", "subj", 1, 5)]}
    dep_index_by_pos = {
        (1, 1): dep.DepRow(line=1, token=1, word="Nullo", deprel=deprel,
                           head_line=0, head_token=0),
        (1, 5): dep.DepRow(line=1, token=5, word="pastor", deprel="nsubj",
                           head_line=2, head_token=2),
        (2, 2): dep.DepRow(line=2, token=2, word="può", deprel="advcl",
                           head_line=1, head_token=1),
    }
    return skel._classify_divergence(given, derived, dep_index_by_pos, {})


def test_classify_divergence_rule_cs_accepts_an_empty_derived_tuple():
    assert _empty_tuple_fixture() == []


def test_classify_divergence_rule_cs_still_reports_a_tuple_with_an_argument():
    # The same predicate with an argument in it is a real assertion the LLM did not propose.
    derived = {1: [skel.SkelRow(1, 1, "Nullo", "subj", 1, 5)]}
    given: dict[int, list[skel.SkelRow]] = {}
    violations = skel._classify_divergence(given, derived, None, {})
    assert any(v.detail.startswith("missing_tuple") for v in violations)


def _copula_under_complement_fixture(lemma="essere"):
    """"quant' **esser** può di nuvol **tenebrata**" (purgatorio 16:3): the copula Layer 4 hung
    under the very adjective it predicates."""
    derived = {1: [skel.SkelRow(1, 2, "esser", "subj", 0, 0)]}
    given = {1: [skel.SkelRow(1, 2, "esser", "subj", 0, 0),
                 skel.SkelRow(1, 2, "esser", "attr", 1, 6)]}
    dep_index_by_pos = {
        (1, 2): dep.DepRow(line=1, token=2, word="esser", deprel="advcl",
                           head_line=1, head_token=6),
        (1, 6): dep.DepRow(line=1, token=6, word="tenebrata", deprel="amod",
                           head_line=1, head_token=1),
    }
    return skel._classify_divergence(given, derived, dep_index_by_pos, {(1, 6): "adjective"},
                                     None, {(1, 2): lemma})


def test_classify_divergence_rule_ct_accepts_a_copula_under_its_complement():
    assert _copula_under_complement_fixture() == []


def test_classify_divergence_rule_ct_leaves_a_lexical_verb_flagged():
    # The copular lemma is the gate: an ordinary adverbial clause under a nominal is not a
    # predication of it.
    violations = _copula_under_complement_fixture(lemma="parlare")
    assert any(v.detail.startswith("extra_arg") for v in violations)


# --- Purgatorio 21-25 read: rules CU, CW, CX, CY ----------------------------------------


def _double_filled_subject_fixture(second=(1, 5)):
    """"e perché tanti secoli **giaciuto** / qui se'" (purgatorio 21:80): the LLM fills the
    subject slot twice, once with pro-drop ∅ and once with the derived subject."""
    derived = {1: [skel.SkelRow(1, 3, "giaciuto", "subj", 1, 5)]}
    given = {1: [skel.SkelRow(1, 3, "giaciuto", "subj", 0, 0),
                 skel.SkelRow(1, 3, "giaciuto", "subj", *second)]}
    dep_index_by_pos = {
        (1, 3): dep.DepRow(line=1, token=3, word="giaciuto", deprel="root",
                           head_line=0, head_token=0),
        (1, 5): dep.DepRow(line=1, token=5, word="chi", deprel="nsubj",
                           head_line=1, head_token=3),
        (1, 7): dep.DepRow(line=1, token=7, word="spirto", deprel="nsubj",
                           head_line=1, head_token=3),
    }
    return skel._classify_divergence(given, derived, dep_index_by_pos, {})


def test_classify_divergence_rule_cu_accepts_a_null_beside_the_derived_subject():
    assert _double_filled_subject_fixture() == []


def test_classify_divergence_rule_cu_still_reports_a_second_concrete_subject():
    # Only the ∅ half is dropped: a concrete subject the derivation contradicts is a claim.
    violations = _double_filled_subject_fixture(second=(1, 7))
    assert any(v.detail.startswith("extra_arg") for v in violations)


def _gapped_second_term_fixture(oblique=(2, 4)):
    """"e come abete in alto si **digrada** / di ramo in ramo, così **quello in giuso**"
    (purgatorio 22:134): two subjects on one predicate is two clauses collapsed onto one head,
    and the arguments after the second belong to the elided one."""
    derived = {1: [skel.SkelRow(1, 1, "digrada", "subj", 1, 2),
                   skel.SkelRow(1, 1, "digrada", "subj", 2, 2),
                   skel.SkelRow(1, 1, "digrada", "obl:in", *oblique)]}
    given = {1: [skel.SkelRow(1, 1, "digrada", "subj", 1, 2)]}
    return skel._classify_divergence(given, derived, None, {})


def test_classify_divergence_rule_cw_accepts_the_elided_clauses_own_argument():
    assert _gapped_second_term_fixture() == []


def test_classify_divergence_rule_cw_still_reports_an_argument_before_the_second_subject():
    # An argument on the *first* term's side of the gap is the predicate's own.
    violations = _gapped_second_term_fixture(oblique=(1, 4))
    assert any(v.detail.startswith("missing_arg") for v in violations)


def _wh_opened_clause_fixture(cited=(2, 1)):
    """"Se tu riduci a mente **qual** fosti meco" (purgatorio 23:115): the LLM names the indirect
    question by the interrogative word that opens it, in the object slot the derivation gives the
    clause as a `ccomp`."""
    derived = {1: [skel.SkelRow(1, 1, "riduci", "ccomp", 2, 2)],
               2: [skel.SkelRow(2, 2, "fosti", "subj", 0, 0)]}
    given = {1: [skel.SkelRow(1, 1, "riduci", "obj", *cited)],
             2: [skel.SkelRow(2, 2, "fosti", "subj", 0, 0)]}
    dep_index_by_pos = {
        (1, 1): dep.DepRow(line=1, token=1, word="riduci", deprel="root",
                           head_line=0, head_token=0),
        (2, 1): dep.DepRow(line=2, token=1, word="qual", deprel="advmod",
                           head_line=2, head_token=2),
        (2, 2): dep.DepRow(line=2, token=2, word="fosti", deprel="ccomp",
                           head_line=1, head_token=1),
        (2, 3): dep.DepRow(line=2, token=3, word="meco", deprel="obl",
                           head_line=2, head_token=2),
    }
    return skel._classify_divergence(given, derived, dep_index_by_pos,
                                     {(2, 1): "adjective", (2, 3): "pronoun"})


def test_classify_divergence_rule_cx_accepts_the_wh_word_that_opens_the_clause():
    assert _wh_opened_clause_fixture() == []


def test_classify_divergence_rule_cx_requires_the_word_to_open_the_clause():
    # A word from the middle of the clause does not name it; only the token the whole subtree
    # begins with does.
    violations = _wh_opened_clause_fixture(cited=(2, 3))
    assert any(v.detail.startswith("extra_arg") for v in violations)


def _aux_named_clause_fixture(deprel="aux"):
    """"«Come!», diss' elli … chi v'**ha** per la sua scala tanto **scorte**?" (purgatorio
    21:21): the quoted clause is listed as its own tuple, headed by its auxiliary."""
    derived = {1: [skel.SkelRow(1, 1, "diss'", "subj", 1, 2),
                   skel.SkelRow(1, 1, "diss'", "ccomp", 2, 3)]}
    given = {1: [skel.SkelRow(1, 1, "diss'", "subj", 1, 2)],
             2: [skel.SkelRow(2, 1, "ha", "subj", 2, 2)]}
    dep_index_by_pos = {
        (1, 1): dep.DepRow(line=1, token=1, word="diss'", deprel="root",
                           head_line=0, head_token=0),
        (1, 2): dep.DepRow(line=1, token=2, word="elli", deprel="nsubj",
                           head_line=1, head_token=1),
        (2, 1): dep.DepRow(line=2, token=1, word="ha", deprel=deprel,
                           head_line=2, head_token=3),
        (2, 2): dep.DepRow(line=2, token=2, word="chi", deprel="nsubj",
                           head_line=2, head_token=3),
        (2, 3): dep.DepRow(line=2, token=3, word="scorte", deprel="ccomp",
                           head_line=1, head_token=1),
    }
    return skel._classify_divergence(given, derived, dep_index_by_pos, {})


def test_classify_divergence_rule_cy_reads_the_double_listing_through_the_auxiliary():
    assert [v for v in _aux_named_clause_fixture() if v.detail.startswith("missing_arg")] == []


def test_classify_divergence_rule_cy_requires_an_aux_edge():
    # A tuple that merely sits inside the clause does not list it: the edge is the gate.
    violations = _aux_named_clause_fixture(deprel="advmod")
    assert any(v.detail.startswith("missing_arg") for v in violations)


# --- Phase 6: rules CZ-DD (the Purgatorio 26-30 read) ------------------------------------


def _gapped_remnant_case_fixture(remnant_case="accusative"):
    """"lei lo vedere, e me l'ovrare appaga" (purgatorio 27:108): the gapped conjunct's two
    remnants, and the `case` annex reading `lei` as the object it is."""
    dep_rows = {1: [
        dep.DepRow(line=1, token=1, word="lei", deprel="conj", head_line=1, head_token=5),
        dep.DepRow(line=1, token=2, word="vedere", deprel="orphan", head_line=1, head_token=1),
        dep.DepRow(line=1, token=3, word="me", deprel="obj", head_line=1, head_token=5),
        dep.DepRow(line=1, token=4, word="ovrare", deprel="nsubj", head_line=1, head_token=5),
        dep.DepRow(line=1, token=5, word="appaga", deprel="root", head_line=0, head_token=0),
    ]}
    morph_rows = {1: [
        morph.MorphRow(word="lei", pos="pronoun"),
        morph.MorphRow(word="vedere", pos="verb"),
        morph.MorphRow(word="me", pos="pronoun"),
        morph.MorphRow(word="ovrare", pos="verb"),
        morph.MorphRow(word="appaga", pos="verb", person="3"),
    ]}
    case_rows = {1: [case.CaseRow(line=1, token=1, word="lei", case=remnant_case)]}
    derived = skel.derive_unit([1], dep_rows, morph_rows, case_rows)
    return {(r.arg_line, r.arg_token): r.role for r in derived[1] if r.token == 5 and r.role}


def test_derive_unit_rule_cz_lets_the_case_annex_claim_a_remnant_slot():
    slots = _gapped_remnant_case_fixture()
    assert slots[(1, 1)] == "obj"      # `lei`, accusative in the annex
    assert slots[(1, 2)] == "subj"     # `lo vedere`, what is left


def test_derive_unit_rule_cz_falls_back_to_role_rank_without_an_annex_value():
    # "onde fa l'arco il Sole e Delia il cinto" (paradiso 29:78) inverts the two halves, so a
    # remnant the annex holds no value for must still take the rank queue's first slot.
    slots = _gapped_remnant_case_fixture(remnant_case="")
    assert slots[(1, 1)] == "subj"
    assert slots[(1, 2)] == "obj"


def _empty_derived_tuple_fixture(role="obl:di"):
    """"Poco parer potea lì del di fori" (purgatorio 27:88): `parer`'s derived tuple is empty,
    so it contradicts no argument the LLM puts on it."""
    derived = {1: [skel.SkelRow(1, 3, "potea", "subj", 1, 1),
                   skel.SkelRow(1, 2, "parer", "", 0, 0)]}
    given = {1: [skel.SkelRow(1, 3, "potea", "subj", 1, 1),
                 skel.SkelRow(1, 2, "parer", role, 1, 4)]}
    dep_index_by_pos = {
        (1, 1): dep.DepRow(line=1, token=1, word="Poco", deprel="nsubj",
                           head_line=1, head_token=3),
        (1, 2): dep.DepRow(line=1, token=2, word="parer", deprel="xcomp",
                           head_line=1, head_token=3),
        (1, 3): dep.DepRow(line=1, token=3, word="potea", deprel="root",
                           head_line=0, head_token=0),
        (1, 4): dep.DepRow(line=1, token=4, word="di", deprel="nmod",
                           head_line=1, head_token=1),
    }
    return skel._classify_divergence(given, derived, dep_index_by_pos, {})


def test_classify_divergence_rule_da_accepts_an_argument_on_an_empty_tuple():
    assert [v for v in _empty_derived_tuple_fixture() if v.detail.startswith("extra_arg")] == []


def test_classify_divergence_rule_da_still_flags_the_subject_slot():
    # The subject slot is rule V's decision, not the derivation's silence.
    violations = _empty_derived_tuple_fixture(role="subj")
    assert any(v.detail.startswith("extra_arg") for v in violations)


def _prepositional_copular_complement_fixture(lemma="essere"):
    """"a tutti altri sapori esto è di sopra" (purgatorio 28:133): the copula's only complement
    is the prepositional adverb Layer 4 wrote as an `obl`."""
    derived = {1: [skel.SkelRow(1, 2, "è", "subj", 1, 1),
                   skel.SkelRow(1, 2, "è", "obl:di", 1, 4)]}
    given = {1: [skel.SkelRow(1, 2, "è", "subj", 1, 1),
                 skel.SkelRow(1, 2, "è", "attr", 1, 4)]}
    dep_index_by_pos = {
        (1, 1): dep.DepRow(line=1, token=1, word="esto", deprel="nsubj",
                           head_line=1, head_token=2),
        (1, 2): dep.DepRow(line=1, token=2, word="è", deprel="root",
                           head_line=0, head_token=0),
        (1, 3): dep.DepRow(line=1, token=3, word="di", deprel="case",
                           head_line=1, head_token=4),
        (1, 4): dep.DepRow(line=1, token=4, word="sopra", deprel="obl",
                           head_line=1, head_token=2),
    }
    return skel._classify_divergence(
        given, derived, dep_index_by_pos,
        {(1, 1): "pronoun", (1, 4): "adverb"}, None,
        {(1, 2): lemma, (1, 4): "sopra"},
    )


def test_classify_divergence_rule_db_accepts_a_copulas_prepositional_adverb():
    assert _prepositional_copular_complement_fixture() == []


def test_classify_divergence_rule_db_is_gated_on_the_copula():
    # Under a lexical verb the same phrase is an ordinary adjunct, and stays flagged.
    violations = _prepositional_copular_complement_fixture(lemma="stare")
    assert any(v.detail.startswith("role_mismatch") for v in violations)


def _relative_clause_depictive_fixture(clause_deprel="acl:relcl"):
    """"come ninfe che si givan sole" (purgatorio 29:4): `sole` is `amod` on the antecedent,
    and the clause's derived subject is the relative pronoun that stands for it."""
    derived = {1: [skel.SkelRow(1, 3, "givan", "subj", 1, 2)]}
    given = {1: [skel.SkelRow(1, 3, "givan", "subj", 1, 2),
                 skel.SkelRow(1, 3, "givan", "attr", 1, 4)]}
    dep_index_by_pos = {
        (1, 1): dep.DepRow(line=1, token=1, word="ninfe", deprel="obl",
                           head_line=0, head_token=0),
        (1, 2): dep.DepRow(line=1, token=2, word="che", deprel="nsubj",
                           head_line=1, head_token=3),
        (1, 3): dep.DepRow(line=1, token=3, word="givan", deprel=clause_deprel,
                           head_line=1, head_token=1),
        (1, 4): dep.DepRow(line=1, token=4, word="sole", deprel="amod",
                           head_line=1, head_token=1),
    }
    return skel._classify_divergence(given, derived, dep_index_by_pos,
                                     {(1, 2): "pronoun", (1, 4): "adjective"})


def test_classify_divergence_rule_dc_reads_the_host_through_the_antecedent():
    assert [v for v in _relative_clause_depictive_fixture()
            if v.detail.startswith("extra_arg")] == []


def test_classify_divergence_rule_dc_requires_a_relative_clause_edge():
    # Without the `acl:relcl` edge the nominal is not this predicate's antecedent.
    violations = _relative_clause_depictive_fixture(clause_deprel="advcl")
    assert any(v.detail.startswith("extra_arg") for v in violations)


def _relative_adverb_case_fixture(arg_pos="adverb"):
    """"questo mondo / dove poter peccar non è più nostro" (purgatorio 26:132): `dove` is a
    `case` on its own clause's verb, which `derive_unit` never reports."""
    derived = {1: [skel.SkelRow(1, 3, "è", "subj", 1, 2)]}
    given = {1: [skel.SkelRow(1, 3, "è", "subj", 1, 2),
                 skel.SkelRow(1, 3, "è", "obl", 1, 1)]}
    dep_index_by_pos = {
        (1, 1): dep.DepRow(line=1, token=1, word="dove", deprel="case",
                           head_line=1, head_token=3),
        (1, 2): dep.DepRow(line=1, token=2, word="peccar", deprel="nsubj",
                           head_line=1, head_token=3),
        (1, 3): dep.DepRow(line=1, token=3, word="è", deprel="acl:relcl",
                           head_line=0, head_token=0),
    }
    return skel._classify_divergence(given, derived, dep_index_by_pos, {(1, 1): arg_pos})


def test_classify_divergence_rule_dd_accepts_the_relative_locative_adverb():
    assert [v for v in _relative_adverb_case_fixture()
            if v.detail.startswith("extra_arg")] == []


def test_classify_divergence_rule_dd_is_gated_on_the_adverb_pos():
    # An ordinary preposition in a `case` slot names no adjunct of its own.
    violations = _relative_adverb_case_fixture(arg_pos="preposition")
    assert any(v.detail.startswith("extra_arg") for v in violations)


def _distinct_conjunct_preposition_fixture(conj_case="infin"):
    """"la flagellò dal capo infin le piante" (purgatorio 32:156): `piante` is a `conj` on
    `capo` carrying its own `case` marker, so the two are separately-marked obliques and the
    collapse must not let the conjunct's preposition displace the head's."""
    derived = {1: [skel.SkelRow(1, 2, "flagellò", "obl:da", 1, 4)]}
    given = {1: [skel.SkelRow(1, 2, "flagellò", "obl:da", 1, 4),
                 skel.SkelRow(1, 2, "flagellò", "obl:a", 1, 7)]}
    dep_index_by_pos = {
        (1, 2): dep.DepRow(line=1, token=2, word="flagellò", deprel="root",
                           head_line=0, head_token=0),
        (1, 3): dep.DepRow(line=1, token=3, word="dal", deprel="case",
                           head_line=1, head_token=4),
        (1, 4): dep.DepRow(line=1, token=4, word="capo", deprel="obl",
                           head_line=1, head_token=2),
        (1, 5): dep.DepRow(line=1, token=5, word=conj_case, deprel="case",
                           head_line=1, head_token=7),
        (1, 7): dep.DepRow(line=1, token=7, word="piante", deprel="conj",
                           head_line=1, head_token=4),
    }
    return skel._classify_divergence(given, derived, dep_index_by_pos)


def test_classify_divergence_rule_de_keeps_the_coordination_heads_own_role():
    assert _distinct_conjunct_preposition_fixture() == []


def test_classify_divergence_rule_de_is_gated_on_a_distinct_marker():
    # Sharing the head's preposition makes the two one phrase again, and rank decides as before.
    violations = _distinct_conjunct_preposition_fixture(conj_case="dal")
    assert any(v.detail.startswith("role_mismatch") for v in violations)


def _control_subject_np_head_fixture(span_end=3):
    """"l'altre tre si fero avanti, danzando" (purgatorio 31:132): Layer 4 makes `altre` the
    subject of `fero`, Layer 3 heads `[l'altre tre]` on `tre`, and the LLM cites Layer 3's head
    for the gerund's inherited subject."""
    from dante_corpus.np import NPSpan
    derived = {1: [skel.SkelRow(1, 4, "fero", "subj", 1, 2),
                   skel.SkelRow(1, 5, "danzando", "obl:a", 1, 7)]}
    given = {1: [skel.SkelRow(1, 4, "fero", "subj", 1, 2),
                 skel.SkelRow(1, 5, "danzando", "subj", 1, 3),
                 skel.SkelRow(1, 5, "danzando", "obl:a", 1, 7)]}
    dep_index_by_pos = {
        (1, 2): dep.DepRow(line=1, token=2, word="altre", deprel="nsubj",
                           head_line=1, head_token=4),
        (1, 3): dep.DepRow(line=1, token=3, word="tre", deprel="nummod",
                           head_line=1, head_token=2),
        (1, 4): dep.DepRow(line=1, token=4, word="fero", deprel="root",
                           head_line=0, head_token=0),
        (1, 5): dep.DepRow(line=1, token=5, word="danzando", deprel="advcl",
                           head_line=1, head_token=4),
        (1, 6): dep.DepRow(line=1, token=6, word="al", deprel="case",
                           head_line=1, head_token=7),
        (1, 7): dep.DepRow(line=1, token=7, word="caribo", deprel="obl",
                           head_line=1, head_token=5),
    }
    np_rows = {1: [NPSpan(line=1, start=2, end=span_end, head=span_end,
                          text="altre tre")]}
    return skel._classify_divergence(given, derived, dep_index_by_pos, np_rows=np_rows)


def test_classify_divergence_rule_df_accepts_the_np_head_as_the_inherited_subject():
    assert _control_subject_np_head_fixture() == []


def test_classify_divergence_rule_df_requires_one_noun_phrase():
    # Rule AI's own gate: outside the candidate's span the citation is a different nominal.
    violations = _control_subject_np_head_fixture(span_end=2)
    assert any(v.detail.startswith("extra_arg") for v in violations)
