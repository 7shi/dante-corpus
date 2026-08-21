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
    # Layer 2 morphology aligned with Layer 1 tokens.
    assert len(unit["morphology"][1]) == len(unit["lines"][0]["tokens"])
    assert unit["morphology"][2][1]["lemma"] == "ritrovare"
    # Layer 4 dependencies present for every token.
    assert len(unit["dependencies"][2]) == len(unit["lines"][1]["tokens"])
    # Layer 3 noun phrases with heads.
    np_texts = {span["text"]: span["head"] for span in unit["noun_phrases"]}
    assert np_texts["mezzo del cammin di nostra vita"] == 2
    assert np_texts["la diritta via"] == 4


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
    assert toolkit.read_unit("inferno", 1, 1)["quotes"] == []
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
    # The payload speaks only Layers 1-4 + quotes + case.
    assert set(unit) == {
        "unit",
        "lines",
        "quotes",
        "morphology",
        "case",
        "noun_phrases",
        "dependencies",
    }


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
