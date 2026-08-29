"""Deterministic tests for the Stage 1 Grammar Tool API (`harness/runner/tools.py`).

No model calls. The masking and anti-leakage guarantees are enforced structurally by
`tools.py`; here they are verified behaviorally, including by poisoning the Layer-5
readers (`skel.io.load_skel`, `skel.registry.rule_active`) so that any accidental access
fails the test instead of leaking silently.
"""

import json

import pytest

from dante_corpus import skel
from harness.runner.tools import (
    MAX_UNIT_LINES,
    TOOL_SPECS,
    GrammarToolkit,
    requires_nominal_anchor,
    tool_specs,
)


def _row(line, token, word, role, arg_line=0, arg_token=0, arg_word=""):
    return {
        "line": line,
        "token": token,
        "word": word,
        "role": role,
        "arg_line": arg_line,
        "arg_token": arg_token,
        "arg_word": arg_word,
    }


# The famous opening unit (Inferno I.1-3), hand-written from public L1-L3 knowledge:
# `ritrovai` takes a pro-drop subject plus two obliques; `via` is the head of
# "la diritta via" (line 3, tokens 2-4, head 4).
GOOD_ROWS = [
    _row(2, 2, "ritrovai", "subj"),
    _row(2, 2, "ritrovai", "obl:in", 1, 2, "mezzo"),
    _row(2, 2, "ritrovai", "obl:per", 2, 5, "selva"),
    _row(3, 6, "smarrita", "subj", 3, 4, "via"),
]


@pytest.fixture()
def toolkit():
    return GrammarToolkit()


# --- read_unit -----------------------------------------------------------------------


def test_read_unit_serves_multilayer_context(toolkit):
    unit = toolkit.read_unit("inferno", 1, 1)
    assert unit["unit"] == {
        "canticle": "inferno",
        "canto": 1,
        "line_start": 1,
        "line_end": 3,
    }
    assert [line["no"] for line in unit["lines"]] == [1, 2, 3]
    assert unit["lines"][0]["tokens"][:3] == ["Nel", "mezzo", "del"]
    # Layer 2 morphology aligned with Layer 1 tokens, compact positional rows:
    # [word, lemma, pos, gender, number, person, tense, mood] (+ note when set).
    assert len(unit["morphology"][1]) == len(unit["lines"][0]["tokens"])
    # "ritrovai" (2.2): verb, sg., 1st person, remote past, indicative.
    assert unit["morphology"][2][1] == [
        "ritrovai", "ritrovare", "verb", "", "sg.", "1", "remote past", "indicative",
    ]
    # "mi" (2.1) carries a note: the 9th element, interior empties intact.
    assert unit["morphology"][2][0] == [
        "mi", "mi", "pronoun", "", "sg.", "1", "", "", "reflexive",
    ]
    # Layer 4 dependencies present for every token: [token, head_token, deprel].
    assert len(unit["dependencies"][2]) == len(unit["lines"][1]["tokens"])
    # Layer 3 noun phrases as [line, start, end, head] rows (nested spans flat).
    assert [1, 2, 7, 2] in unit["noun_phrases"]  # "mezzo del cammin di nostra vita"
    assert [3, 2, 4, 4] in unit["noun_phrases"]  # "la diritta via" -> via


def test_read_unit_snaps_to_sentence_group_bounds(toolkit):
    unit = toolkit.read_unit("inferno", 1, 1)
    start, end = unit["unit"]["line_start"], unit["unit"]["line_end"]
    assert start == 1 and end - start + 1 <= MAX_UNIT_LINES


def test_read_unit_rejects_range_crossing_unit_boundary(toolkit):
    # Lines 1-3 form one sentence group; asking through line 4 crosses into the next.
    with pytest.raises(ValueError, match="parse-unit boundary"):
        toolkit.read_unit("inferno", 1, 1, line_end=4)


def test_read_unit_accepts_range_within_one_unit(toolkit):
    unit = toolkit.read_unit("inferno", 1, 1, line_end=2)
    assert (unit["unit"]["line_start"], unit["unit"]["line_end"]) == (1, 2)


def test_read_unit_rejects_invalid_arguments(toolkit):
    with pytest.raises(ValueError):
        toolkit.read_unit("limbo", 1, 1)
    with pytest.raises(ValueError):
        toolkit.read_unit("inferno", 1, 0)
    with pytest.raises(ValueError):
        toolkit.read_unit("inferno", 1, 200)
    with pytest.raises(ValueError):
        toolkit.read_unit("inferno", 1, 2, line_end=1)


def test_read_unit_includes_quotes_only_where_they_exist(toolkit):
    # Empty sections are omitted entirely (the compact contract).
    assert "quotes" not in toolkit.read_unit("inferno", 1, 1)
    quoted = toolkit.read_unit("inferno", 1, 65)
    assert quoted["quotes"], "line 65 carries the first direct-speech quote"
    start = quoted["unit"]["line_start"]
    end = quoted["unit"]["line_end"]
    for quote in quoted["quotes"]:
        assert quote["end_line"] >= start and quote["start_line"] <= end


def test_read_unit_strictly_masks_layer_5(toolkit, monkeypatch):
    """Any read of gold skel TSVs or the rule registry must fail the test loudly."""

    def _poison(*args, **kwargs):
        raise AssertionError("Layer 5 gold data was accessed")

    monkeypatch.setattr(skel.io, "load_skel", _poison)
    monkeypatch.setattr(skel.registry, "rule_active", _poison)

    unit = toolkit.read_unit("inferno", 1, 1)
    serialized = json.dumps(unit)
    assert "role" not in serialized  # skeleton roles are Layer 5 vocabulary-in-use
    assert "skel" not in serialized
    # The payload speaks only Layers 1-4 + quotes + case, in compact form.
    assert set(unit) == {
        "unit",
        "legend",
        "lines",
        "morphology",
        "case",
        "noun_phrases",
        "dependencies",
    }


# --- read_unit payload tiers (STAGE3.md §2.B) ---------------------------------------------


def test_read_unit_r1_legend_makes_the_shapes_self_describing(toolkit):
    unit = toolkit.read_unit("inferno", 1, 1)  # default tier: R1
    assert toolkit.payload_tier == "R1"
    legend = unit["legend"]
    for fragment in (
        "morphology",
        "word,lemma,pos,gender,number,person,tense,mood",
        "dependencies [token,head_token,deprel]",
        "noun_phrases [line,start,end,head]",
    ):
        assert fragment in legend


def test_read_unit_r1_rows_are_positional_and_sparse(toolkit):
    unit = toolkit.read_unit("inferno", 1, 1)
    for rows in unit["morphology"].values():
        for row in rows:
            assert isinstance(row, list)
            assert 1 <= len(row) <= 9  # 8 fields + optional note
            assert row[0]  # the word anchors the row
    for rows in unit["dependencies"].values():
        for row in rows:
            assert isinstance(row, list) and 3 <= len(row) <= 4
    for row in unit["noun_phrases"]:
        assert isinstance(row, list) and len(row) == 4
    # head_line rides only when it differs from line.
    for line, rows in unit["dependencies"].items():
        for row in rows:
            if len(row) == 4:
                assert row[3] != line


def test_read_unit_s1_keeps_named_dicts_dropping_empties(toolkit):
    s1 = GrammarToolkit(payload_tier="S1")
    assert "legend" not in s1.read_unit("inferno", 1, 1)
    unit = s1.read_unit("inferno", 1, 1)
    for rows in unit["morphology"].values():
        for row in rows:
            assert isinstance(row, dict)
            assert set(row) <= {
                "word", "lemma", "pos", "gender", "number",
                "person", "tense", "mood", "note",
            }
            assert all(row.values())  # no empty-valued keys survive
    for rows in unit["dependencies"].values():
        for row in rows:
            assert isinstance(row, dict)
    assert "quotes" not in unit  # empty section dropped


def test_read_unit_tiers_cover_identical_content(toolkit):
    """R1 and S1 serve the same facts in different shapes (the §5 tier
    decision must not change what the model can know)."""
    s1 = GrammarToolkit(payload_tier="S1")
    for line_start in (1, 65, 112):  # plain, quoted, multi-line-heavy units
        r1 = toolkit.read_unit("inferno", 1, line_start)
        sparse = s1.read_unit("inferno", 1, line_start)
        assert r1["unit"] == sparse["unit"]
        assert r1["lines"] == sparse["lines"]
        # Quotes: same spans (S1 drops empty-valued keys like children: []).
        def _norm_quotes(quotes):
            return [
                {k: v for k, v in q.items() if v not in ([], None)}
                for q in quotes or []
            ]

        assert _norm_quotes(r1.get("quotes")) == _norm_quotes(sparse.get("quotes"))
        assert set(r1["morphology"]) == set(sparse["morphology"])
        assert set(r1["dependencies"]) == set(sparse["dependencies"])
        assert set(r1.get("case", {})) == set(sparse.get("case", {}))
        for no in r1["morphology"]:
            compact = r1["morphology"][no]
            named = sparse["morphology"][no]
            assert len(compact) == len(named)
            words = [row[0] for row in compact]
            assert words == [row["word"] for row in named]
            for pos_row, named_row in zip(compact, named):
                assert pos_row[1] == named_row.get("lemma", "")
                assert pos_row[2] == named_row.get("pos", "")
        for no in r1["dependencies"]:
            compact = r1["dependencies"][no]
            named = sparse["dependencies"][no]
            assert [(row[0], row[2]) for row in compact] == [
                (row["token"], row["deprel"]) for row in named
            ]
        assert [tuple(row) for row in r1["noun_phrases"]] == [
            (row["line"], row["start"], row["end"], row["head"])
            for row in sparse["noun_phrases"]
        ]


def test_toolkit_rejects_unknown_payload_tier():
    with pytest.raises(ValueError, match="payload tier"):
        GrammarToolkit(payload_tier="R2")


# --- search_corpus ---------------------------------------------------------------------


def test_search_corpus_finds_lemma_and_word_hits(toolkit):
    hits = toolkit.search_corpus({"word": "ritrovai"})
    assert hits and hits[0]["canticle"] == "inferno" and hits[0]["canto"] == 1
    assert hits[0]["line"] == 2 and hits[0]["token"] == 2
    assert hits[0]["lemma"] == "ritrovare" and hits[0]["pos"] == "verb"

    lemma_hits = toolkit.search_corpus({"lemma": "ritrovare"}, limit=5)
    assert lemma_hits
    assert all(hit["lemma"] == "ritrovare" for hit in lemma_hits)


def test_search_corpus_matches_deprel_and_pos(toolkit):
    hits = toolkit.search_corpus({"deprel": "root", "pos": "verb"}, limit=8)
    assert hits
    assert all(hit["deprel"] == "root" and "verb" in hit["pos"].lower() for hit in hits)


def test_search_corpus_excludes_active_canto(toolkit):
    toolkit.read_unit("inferno", 1, 1)  # sets the active unit -> active canto
    hits = toolkit.search_corpus({"word": "ritrovai"})
    assert all(
        not (hit["canticle"] == "inferno" and hit["canto"] == 1) for hit in hits
    ), "the Anti-Leakage Guard must exclude the active canto entirely"


def test_search_corpus_respects_limit(toolkit):
    hits = toolkit.search_corpus({"pos": "noun"}, limit=3)
    assert len(hits) == 3
    assert all("noun" in hit["pos"].lower() for hit in hits)


def test_search_corpus_validates_query_and_limit(toolkit):
    with pytest.raises(ValueError):
        toolkit.search_corpus({})
    with pytest.raises(ValueError):
        toolkit.search_corpus({"role": "subj"})  # Layer 5 vocabulary is unsearchable
    with pytest.raises(ValueError):
        toolkit.search_corpus({"lemma": "amor"}, limit=0)


def test_search_corpus_never_touches_layer_5(toolkit, monkeypatch):
    def _poison(*args, **kwargs):
        raise AssertionError("Layer 5 gold data was accessed")

    monkeypatch.setattr(skel.io, "load_skel", _poison)
    monkeypatch.setattr(skel.registry, "rule_active", _poison)
    for hit in toolkit.search_corpus({"pos": "verb"}, limit=5):
        assert set(hit) <= {
            "canticle",
            "canto",
            "line",
            "token",
            "word",
            "lemma",
            "pos",
            "deprel",
            "head_line",
            "head_token",
            "case",
        }


# --- validate_candidate ------------------------------------------------------------------


def test_validate_candidate_accepts_wellformed_rows(toolkit):
    result = toolkit.validate_candidate("inferno", 1, 1, GOOD_ROWS)
    assert result["valid"] is True
    assert result["errors"] == []
    assert result["warnings"] == []
    assert "well-formed" in result["diagnostics"]


def test_validate_candidate_rejects_unknown_predicate_token(toolkit):
    rows = [_row(2, 99, "ritrovai", "subj")]
    result = toolkit.validate_candidate("inferno", 1, 1, rows)
    assert result["valid"] is False
    assert any("out of range" in error for error in result["errors"])


def test_validate_candidate_rejects_nonexistent_predicate_line(toolkit):
    result = toolkit.validate_candidate("inferno", 1, 1, [_row(999, 1, "x", "subj")])
    assert any("does not exist" in error for error in result["errors"])


def test_validate_candidate_rejects_word_anchor_mismatch(toolkit):
    rows = [_row(2, 2, "trovai", "subj"), *_GOOD_WITHOUT_PRED]
    result = toolkit.validate_candidate("inferno", 1, 1, rows)
    assert result["valid"] is False
    assert any("does not match Layer 1" in error for error in result["errors"])


def test_validate_candidate_rejects_argument_not_np_head_nor_pronoun(toolkit):
    # "oscura" (2.6) belongs to the NP "una selva oscura" but is not its head (5).
    rows = [_row(2, 2, "ritrovai", "obj", 2, 6, "oscura")]
    result = toolkit.validate_candidate("inferno", 1, 1, rows)
    assert result["valid"] is False
    assert any(
        "neither a Layer 3 NP head nor a pronoun" in error for error in result["errors"]
    )


def test_requires_nominal_anchor_scope():
    assert requires_nominal_anchor("subj")
    assert requires_nominal_anchor("iobj")
    assert requires_nominal_anchor("obl:di")
    # Clausal / predicative roles and gold's adverbial marker are exempt.
    assert not requires_nominal_anchor("attr")
    assert not requires_nominal_anchor("ccomp")
    assert not requires_nominal_anchor("xcomp")
    assert not requires_nominal_anchor("obl")
    assert not requires_nominal_anchor("")


def test_validate_candidate_accepts_predicate_anchored_clausal_roles(toolkit):
    # Inferno XIV 124-129: complements cite their clause's own predicate-head
    # token (sai -> tondo; de' -> addur), which the *nominal* rule used to
    # reject — the exact upstream_feedback complaint from the first live
    # benchmark run (harness/bench-strict-validator-baseline.log). Exemption
    # from that rule stands; what the citation does incur is the registration
    # duty, satisfied here by giving each cited clause head its own row.
    rows = [
        _row(124, 2, "elli", "ccomp", 124, 6, "sai"),
        _row(124, 6, "sai", "ccomp", 124, 11, "tondo"),
        _row(124, 11, "tondo", "", 0, 0),
        _row(129, 2, "de'", "xcomp", 129, 3, "addur"),
        _row(129, 3, "addur", "", 0, 0),
    ]
    result = toolkit.validate_candidate("inferno", 14, 124, rows)
    assert result["valid"] is True
    assert result["errors"] == []


def test_validate_candidate_rejects_a_clausal_citation_it_does_not_register(toolkit):
    """`skel/validate.py` 115-121 as an admission condition: asserting that an
    argument heads a clause obliges the submission to carry that clause. The
    error names both ways out, so the model can act on it."""
    rows = [
        _row(124, 6, "sai", "ccomp", 124, 11, "tondo"),  # tondo unregistered
    ]
    result = toolkit.validate_candidate("inferno", 14, 124, rows)
    assert result["valid"] is False
    error = next(e for e in result["errors"] if "not a predicate" in e)
    assert "124.11" in error
    assert "add a row" in error and "attr" in error

    # Registering the clause resolves it; so does the weaker notation.
    assert toolkit.validate_candidate(
        "inferno", 14, 124, rows + [_row(124, 11, "tondo", "", 0, 0)]
    )["valid"] is True
    assert toolkit.validate_candidate(
        "inferno", 14, 124, [_row(124, 6, "sai", "attr", 124, 11, "tondo")]
    )["valid"] is True


def test_validate_candidate_clausal_registration_is_off_per_predicate():
    """The check reads one submission as a set, so the per-predicate workflow —
    whose calls carry one predicate's rows at a time — gets the row-local
    checks only; a sibling clause it has not submitted yet is not an error."""
    toolkit = GrammarToolkit(clausal_registration=False)
    rows = [_row(124, 6, "sai", "ccomp", 124, 11, "tondo")]
    assert toolkit.validate_candidate("inferno", 14, 124, rows)["valid"] is True


def test_validate_candidate_rejects_self_argument(toolkit):
    """`skel/validate.py` 107: an enclitic host citing its own token makes the
    predicate its own object — the format has no reading for that."""
    rows = [_row(1, 1, "", "obj", 1, 1, "")]
    result = toolkit.validate_candidate("inferno", 1, 1, rows)
    assert result["valid"] is False
    assert any("cites its own predicate" in e for e in result["errors"])


def test_validate_candidate_restricts_the_null_position_to_subjects(toolkit):
    """`skel/validate.py` 109-111: (0, 0) marks a dropped subject (and the
    zero-argument marker's own row), not an elided object."""
    assert toolkit.validate_candidate(
        "inferno", 1, 1, [_row(1, 1, "", "subj", 0, 0, "")]
    )["valid"] is True
    assert toolkit.validate_candidate(
        "inferno", 1, 1, [_row(1, 1, "", "", 0, 0, "")]
    )["valid"] is True
    result = toolkit.validate_candidate(
        "inferno", 1, 1, [_row(1, 1, "", "obj", 0, 0, "")]
    )
    assert result["valid"] is False
    assert any("may not cite (0, 0)" in e for e in result["errors"])


def test_validate_candidate_still_rejects_non_nominal_anchor_on_nominal_role(toolkit):
    # "tondo" (adjective) anchors sai's clausal complement fine, but as a *subject*
    # citation on a nominal role it still fails the NP-head/pronoun requirement.
    rows = [_row(124, 6, "sai", "subj", 124, 11, "tondo")]
    result = toolkit.validate_candidate("inferno", 14, 124, rows)
    assert result["valid"] is False
    assert any(
        "neither a Layer 3 NP head nor a pronoun" in error for error in result["errors"]
    )


def test_validate_candidate_accepts_attr_and_adverbial_obl_anchors(toolkit):
    # Gold usage: attr anchors on a predicative adjective (era <- dura), bare obl
    # on an adverb (ripigneva <- quivi-style locative).
    result = toolkit.validate_candidate(
        "inferno", 1, 4, [_row(4, 6, "", "attr", 4, 5, "")]
    )
    assert result["valid"] is True
    result = toolkit.validate_candidate(
        "inferno", 1, 60, [_row(60, 2, "", "obl", 60, 3, "")]
    )
    assert result["valid"] is True


def test_validate_candidate_word_fields_are_optional(toolkit):
    # Coordinates alone identify tokens; word/arg_word are optional anchors now.
    rows = [
        {"line": 2, "token": 2, "role": "obj", "arg_line": 2, "arg_token": 5},
        {"line": 2, "token": 2, "role": "subj", "arg_line": 0, "arg_token": 0},
    ]
    result = toolkit.validate_candidate("inferno", 1, 1, rows)
    assert result["valid"] is True


def test_validate_candidate_accepts_pronoun_argument(toolkit):
    # "mi" (2.1) is a pronoun, so it is a valid argument citation without an NP span.
    rows = [_row(2, 2, "ritrovai", "obj", 2, 1, "mi")]
    result = toolkit.validate_candidate("inferno", 1, 1, rows)
    assert result["valid"] is True


def test_validate_candidate_rejects_invalid_role(toolkit):
    rows = [_row(2, 2, "ritrovai", "subject", 2, 1, "mi")]
    result = toolkit.validate_candidate("inferno", 1, 1, rows)
    assert result["valid"] is False
    assert any("invalid role" in error for error in result["errors"])


def test_validate_candidate_rejects_duplicate_slot(toolkit):
    rows = GOOD_ROWS + [_row(2, 2, "ritrovai", "obl:per", 2, 5, "selva")]
    result = toolkit.validate_candidate("inferno", 1, 1, rows)
    assert result["valid"] is False
    assert any("duplicate slot" in error for error in result["errors"])


def test_validate_candidate_rejects_unlicensed_dual_role(toolkit):
    # Same argument cited for two roles of one predicate without a fused-clitic case row.
    rows = [
        _row(2, 2, "ritrovai", "obl:per", 2, 5, "selva"),
        _row(2, 2, "ritrovai", "obj", 2, 5, "selva"),
    ]
    result = toolkit.validate_candidate("inferno", 1, 1, rows)
    assert result["valid"] is False
    assert any("without clitic licensing" in error for error in result["errors"])


def test_validate_candidate_zero_argument_marker_consistency(toolkit):
    ok = toolkit.validate_candidate(
        "inferno", 1, 1, [_row(2, 2, "ritrovai", "", 0, 0)]
    )
    assert ok["valid"] is True

    bad_arg = toolkit.validate_candidate(
        "inferno", 1, 1, [_row(2, 2, "ritrovai", "", 1, 2, "mezzo")]
    )
    assert bad_arg["valid"] is False
    assert any("zero-argument marker" in error for error in bad_arg["errors"])

    mixed = toolkit.validate_candidate(
        "inferno", 1, 1,
        [
            _row(2, 2, "ritrovai", "", 0, 0),
            _row(2, 2, "ritrovai", "obl:per", 2, 5, "selva"),
        ],
    )
    assert mixed["valid"] is False


def test_validate_candidate_flags_out_of_unit_predicate_as_error(toolkit):
    # Line 10 belongs to a later parse unit than the one starting at line 1.
    rows = [_row(10, 3, "lo", "subj")]
    result = toolkit.validate_candidate("inferno", 1, 1, rows)
    assert result["valid"] is False
    assert any("outside the parse unit" in error for error in result["errors"])


def test_validate_candidate_warns_on_out_of_unit_argument(toolkit):
    # "cosa" (4.8) heads the NP "cosa dura" in the *next* parse unit: a resolvable
    # citation, so intrinsically valid but flagged as out-of-unit.
    rows = [_row(3, 6, "smarrita", "obl:in", 4, 8, "cosa")]
    result = toolkit.validate_candidate("inferno", 1, 1, rows)
    assert result["valid"] is True  # intrinsic citation is fine...
    assert any("outside the parse unit" in w for w in result["warnings"])  # ...but flagged


def test_validate_candidate_rejects_malformed_rows(toolkit):
    result = toolkit.validate_candidate("inferno", 1, 1, [{"line": 2}])
    assert result["valid"] is False
    assert any("missing field" in error for error in result["errors"])
    result = toolkit.validate_candidate("inferno", 1, 1, ["not-a-dict"])
    assert any("not a dict" in error for error in result["errors"])


def test_validate_candidate_logs_upstream_feedback(toolkit):
    feedback = [
        {"layer": "L4", "position": "3.6", "description": "advcl attachment looks wrong"},
    ]
    result = toolkit.validate_candidate("inferno", 1, 1, GOOD_ROWS, feedback)
    assert result["valid"] is True, "feedback records never affect syntactic validity"
    assert result["upstream_feedback"] == feedback
    assert toolkit.upstream_log[-1]["layer"] == "L4"
    assert toolkit.upstream_log[-1]["canticle"] == "inferno"

    malformed = toolkit.validate_candidate(
        "inferno", 1, 1, GOOD_ROWS, ["garbage", {"layer": "L2"}]
    )
    assert malformed["valid"] is True
    assert len(malformed["warnings"]) == 2


def test_validate_candidate_never_touches_layer_5(toolkit, monkeypatch):
    def _poison(*args, **kwargs):
        raise AssertionError("Layer 5 gold data was accessed")

    monkeypatch.setattr(skel.io, "load_skel", _poison)
    monkeypatch.setattr(skel.registry, "rule_active", _poison)
    result = toolkit.validate_candidate("inferno", 1, 1, GOOD_ROWS)
    assert result["valid"] is True


# --- tool-call specs & dispatch ---------------------------------------------------------


def test_tool_specs_describe_the_closed_surface():
    names = [spec["function"]["name"] for spec in TOOL_SPECS]
    assert names == ["read_unit", "search_corpus", "validate_candidate"]
    for spec in TOOL_SPECS:
        fn = spec["function"]
        assert fn["description"]
        params = fn["parameters"]
        assert params["type"] == "object"
        assert params["required"], "every tool needs at least one required argument"
        assert params["additionalProperties"] is False
    # JSON-serializable verbatim (they are embedded into prompts).
    json.dumps(TOOL_SPECS)


def test_tool_specs_returns_mutable_copies():
    specs = tool_specs()
    specs[0]["function"]["name"] = "tampered"
    assert TOOL_SPECS[0]["function"]["name"] == "read_unit"


def test_dispatch_read_unit_round_trip(toolkit):
    direct = toolkit.read_unit("inferno", 1, 1)
    call = toolkit.dispatch("read_unit", {"canticle": "inferno", "canto": 1, "line_start": 1})
    assert call["ok"] is True and call["tool"] == "read_unit"
    assert call["result"] == direct
    json.dumps(call)  # results must be JSON-ready for the next model turn


def test_dispatch_accepts_json_string_arguments(toolkit):
    call = toolkit.dispatch(
        "read_unit", json.dumps({"canticle": "inferno", "canto": 1, "line_start": 1})
    )
    assert call["ok"] is True


def test_dispatch_coerces_numeric_strings(toolkit):
    call = toolkit.dispatch(
        "read_unit", {"canticle": "inferno", "canto": "1", "line_start": "1"}
    )
    assert call["ok"] is True
    assert call["result"]["unit"]["canto"] == 1


def test_dispatch_search_and_validate(toolkit):
    toolkit.read_unit("inferno", 1, 1)
    search = toolkit.dispatch("search_corpus", {"query": {"word": "ritrovai"}})
    assert search["ok"] is True
    assert all(not (h["canticle"] == "inferno" and h["canto"] == 1) for h in search["result"])

    validate = toolkit.dispatch(
        "validate_candidate",
        {
            "canticle": "inferno",
            "canto": 1,
            "line_start": 1,
            "candidate_rows": GOOD_ROWS,
        },
    )
    assert validate["ok"] is True
    assert validate["result"]["valid"] is True


def test_dispatch_reports_errors_without_raising(toolkit):
    unknown = toolkit.dispatch("bash", {"command": "rm -rf /"})
    assert unknown["ok"] is False
    assert "unknown tool" in unknown["error"]

    bad_json = toolkit.dispatch("read_unit", "{not json")
    assert bad_json["ok"] is False and "not valid JSON" in bad_json["error"]

    not_object = toolkit.dispatch("read_unit", ["inferno", 1])
    assert not_object["ok"] is False

    missing = toolkit.dispatch("read_unit", {"canticle": "inferno"})
    assert missing["ok"] is False and "line_start" in missing["error"]

    rejected = toolkit.dispatch("search_corpus", {"query": {"lemma": "amor"}, "limit": 0})
    assert rejected["ok"] is False and "limit" in rejected["error"]

    crossing = toolkit.dispatch(
        "read_unit",
        {"canticle": "inferno", "canto": 1, "line_start": 1, "line_end": 4},
    )
    assert crossing["ok"] is False and "parse-unit boundary" in crossing["error"]


def test_dispatch_never_touches_layer_5(toolkit, monkeypatch):
    def _poison(*args, **kwargs):
        raise AssertionError("Layer 5 gold data was accessed")

    monkeypatch.setattr(skel.io, "load_skel", _poison)
    monkeypatch.setattr(skel.registry, "rule_active", _poison)
    for name, arguments in [
        ("read_unit", {"canticle": "inferno", "canto": 1, "line_start": 1}),
        ("search_corpus", {"query": {"pos": "verb"}, "limit": 3}),
        (
            "validate_candidate",
            {
                "canticle": "inferno",
                "canto": 1,
                "line_start": 1,
                "candidate_rows": GOOD_ROWS,
            },
        ),
    ]:
        call = toolkit.dispatch(name, arguments)
        assert call["ok"] is True, call


# --- shared fixture bits -------------------------------------------------------------


_GOOD_WITHOUT_PRED = [
    _row(2, 2, "ritrovai", "obl:in", 1, 2, "mezzo"),
    _row(2, 2, "ritrovai", "obl:per", 2, 5, "selva"),
]
