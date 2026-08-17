"""Deterministic tests for `skel/skel.py`'s `--fix` stages (no model calls).

The build driver is a script rather than a package module, so it is loaded by path — the same
thing `--fix` itself runs. Only the pure parts are exercised here: the per-class question
builders, the answer parsers, and the row splices. `_ask_class` (the one function that calls a
model) is deliberately untested, because everything it does apart from the call is covered by
the apply tests below.
"""

import importlib.util
import sys
from pathlib import Path

import pytest

from dante_corpus import dep, morph, skel

_ROOT = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("skel_driver", _ROOT / "skel" / "skel.py")
drv = importlib.util.module_from_spec(_spec)
sys.modules["skel_driver"] = drv
_spec.loader.exec_module(drv)


# Two lines whose tokenization is obvious, so a test can cite positions by eye:
#   1.1 la  1.2 donna  1.3 vede    2.1 il  2.2 lume  2.3 chiaro
_NOS = [1, 2]
_TEXTS = ["la donna vede", "il lume chiaro"]
_MORPH = {
    1: [morph.MorphRow(word="la", pos="article"),
        morph.MorphRow(word="donna", lemma="donna", pos="noun", number="sg."),
        morph.MorphRow(word="vede", lemma="vedere", pos="verb", person="3", number="sg.")],
    2: [morph.MorphRow(word="il", pos="article"),
        morph.MorphRow(word="lume", lemma="lume", pos="noun", number="sg."),
        morph.MorphRow(word="chiaro", lemma="chiaro", pos="adjective")],
}


def _ctx(morph_rows=None):
    return drv._UnitContext(_NOS, _TEXTS, _MORPH if morph_rows is None else morph_rows, {})


def _rows(*rows):
    out: dict[int, list[skel.SkelRow]] = {}
    for r in rows:
        out.setdefault(r.line, []).append(r)
    return out


# --- answer parsing ---------------------------------------------------------------------------


def test_parse_answers_reads_numbered_lines():
    assert drv._parse_answers("Q1: obj\nQ2: subj") == {1: "obj", 2: "subj"}


def test_parse_answers_ignores_surrounding_prose():
    text = "Here is my analysis.\n\nQ1: obl:in\nQ2. drop\n\nHope that helps!"
    assert drv._parse_answers(text) == {1: "obl:in", 2: "drop"}


def test_parse_answers_strips_markdown_emphasis():
    assert drv._parse_answers("Q1: `iobj`\nQ2: **keep**") == {1: "iobj", 2: "keep"}


def test_parse_answers_returns_empty_for_unparseable_output():
    assert drv._parse_answers("I am not sure about this sentence.") == {}


@pytest.mark.parametrize("text,expected", [
    ("3.4", (3, 4)), (" 12.1 ", (12, 1)), ("0.0", (0, 0)), ("3,4", (3, 4)),
    ("none", None), ("3.4 donna", None), ("", None),
])
def test_token_ref(text, expected):
    assert drv._token_ref(text) == expected


# --- the independence rule: a question may never carry the derivation's answer ------------------


def test_class_question_never_leaks_derived_argument():
    """The model is not shown the Layer-4 parse (module docstring), and `_fix_hint` has always
    withheld the derivation's argument positions specifically. A pinpoint question must not
    quietly reintroduce them, or the model is only confirming Layer 4 rather than reading."""
    # The derivation says `vede`'s object is `lume` (2.2); the committed rows say otherwise.
    derived = {1: [skel.SkelRow(1, 3, "vede", "subj", 1, 2), skel.SkelRow(1, 3, "vede", "obj", 2, 2)]}
    given = {1: [skel.SkelRow(1, 3, "vede", "subj", 1, 2)]}
    violations = skel._classify_divergence(given, derived)
    missing = [v for v in violations if v.detail.startswith("missing_arg")]
    assert missing, "fixture must produce a missing_arg"
    question = drv._ask_missing_arg(_ctx(), missing)
    # The role slot may be named (as `_fix_hint` already does); the position may not.
    assert "'obj'" in question
    assert "2.2" not in question.split("Q1:", 1)[1]


def test_role_mismatch_question_never_leaks_the_derived_role():
    derived = {1: [skel.SkelRow(1, 3, "vede", "obj", 1, 2)]}
    given = {1: [skel.SkelRow(1, 3, "vede", "iobj", 1, 2)]}
    violations = skel._classify_divergence(given, derived)
    mismatch = [v for v in violations if v.detail.startswith("role_mismatch")]
    assert mismatch
    asked = drv._ask_role_mismatch(_ctx(), mismatch).split("Q1:", 1)[1]
    # The question names the predicate and the disputed argument, and stops there: naming the
    # derived role would turn "which role is this?" into "is it obj?".
    assert "obj" not in asked
    assert "iobj" not in asked


# --- role_mismatch ------------------------------------------------------------------------------


def _role_mismatch_fixture(given_role="iobj", derived_role="obj"):
    derived = {1: [skel.SkelRow(1, 3, "vede", derived_role, 1, 2)]}
    given = _rows(skel.SkelRow(1, 3, "vede", given_role, 1, 2))
    violations = [v for v in skel._classify_divergence(given, derived)
                  if v.detail.startswith("role_mismatch")]
    return given, violations


def test_apply_role_mismatch_relabels_the_row():
    given, vs = _role_mismatch_fixture()
    assert drv._apply_role_mismatch(_ctx(), vs, given, "Q1: obj")
    assert given[1][0].role == "obj"


def test_apply_role_mismatch_none_removes_the_row():
    given, vs = _role_mismatch_fixture()
    assert drv._apply_role_mismatch(_ctx(), vs, given, "Q1: none")
    assert given[1] == []


def test_apply_role_mismatch_rejects_a_role_outside_the_vocabulary():
    given, vs = _role_mismatch_fixture()
    assert not drv._apply_role_mismatch(_ctx(), vs, given, "Q1: locative")
    assert given[1][0].role == "iobj"


def test_apply_role_mismatch_ignores_an_unanswered_question():
    given, vs = _role_mismatch_fixture()
    assert not drv._apply_role_mismatch(_ctx(), vs, given, "I could not decide.")
    assert given[1][0].role == "iobj"


def test_apply_role_mismatch_matches_a_row_spelled_differently():
    """A violation reports the canonical role (`iobj` canonicalizes to `obl:a`), while the
    committed row holds whatever spelling the model wrote. The splice must still find it."""
    derived = {1: [skel.SkelRow(1, 3, "vede", "obj", 1, 2)]}
    given = _rows(skel.SkelRow(1, 3, "vede", "iobj", 1, 2))
    vs = [v for v in skel._classify_divergence(given, derived)
          if v.detail.startswith("role_mismatch")]
    assert vs[0].given_role == "obl:a"  # canonicalized, not the row's own spelling
    assert drv._apply_role_mismatch(_ctx(), vs, given, "Q1: obj")
    assert given[1][0].role == "obj"


# --- extra_arg ------------------------------------------------------------------------------------


def _extra_arg_fixture():
    derived = {1: [skel.SkelRow(1, 3, "vede", "subj", 1, 2)]}
    given = _rows(skel.SkelRow(1, 3, "vede", "subj", 1, 2),
                  skel.SkelRow(1, 3, "vede", "obj", 2, 2))
    violations = [v for v in skel._classify_divergence(given, derived)
                  if v.detail.startswith("extra_arg")]
    return given, violations


def test_apply_extra_arg_keep_changes_nothing():
    given, vs = _extra_arg_fixture()
    assert not drv._apply_extra_arg(_ctx(), vs, given, "Q1: keep")
    assert len(given[1]) == 2


def test_apply_extra_arg_drop_removes_the_row():
    given, vs = _extra_arg_fixture()
    assert drv._apply_extra_arg(_ctx(), vs, given, "Q1: drop")
    assert [r.role for r in given[1]] == ["subj"]


def test_apply_extra_arg_relabels_when_a_role_is_answered():
    given, vs = _extra_arg_fixture()
    assert drv._apply_extra_arg(_ctx(), vs, given, "Q1: obl:in")
    assert [r.role for r in given[1]] == ["subj", "obl:in"]


# --- missing_arg ----------------------------------------------------------------------------------


def _missing_arg_fixture():
    derived = {1: [skel.SkelRow(1, 3, "vede", "subj", 1, 2), skel.SkelRow(1, 3, "vede", "obj", 2, 2)]}
    given = _rows(skel.SkelRow(1, 3, "vede", "subj", 1, 2))
    violations = [v for v in skel._classify_divergence(given, derived)
                  if v.detail.startswith("missing_arg")]
    return given, violations


def test_apply_missing_arg_inserts_the_cited_token():
    given, vs = _missing_arg_fixture()
    assert drv._apply_missing_arg(_ctx(), vs, given, "Q1: 2.2")
    assert skel.SkelRow(1, 3, "vede", "obj", 2, 2) in given[1]


def test_apply_missing_arg_none_inserts_nothing():
    given, vs = _missing_arg_fixture()
    assert not drv._apply_missing_arg(_ctx(), vs, given, "Q1: none")
    assert len(given[1]) == 1


def test_apply_missing_arg_ignores_an_unparseable_position():
    given, vs = _missing_arg_fixture()
    assert not drv._apply_missing_arg(_ctx(), vs, given, "Q1: the noun lume")
    assert len(given[1]) == 1


def test_apply_missing_arg_does_not_duplicate_an_existing_row():
    given, vs = _missing_arg_fixture()
    given[1].append(skel.SkelRow(1, 3, "vede", "obj", 2, 2))
    assert not drv._apply_missing_arg(_ctx(), vs, given, "Q1: 2.2")
    assert len(given[1]) == 2


def test_apply_missing_arg_refuses_to_put_one_token_in_two_roles():
    """Rule EG's splice guard. `vede` already holds 1.2 as its `subj`; answering the `obj` question
    with the same token would write one token into two roles of one predicate — the artifact
    contradicting itself, which the sixth `--fix` round did at paradiso 1:81 and no divergence check
    can see. The splice must refuse it rather than let the per-unit gate absorb it."""
    given, vs = _missing_arg_fixture()
    assert not drv._apply_missing_arg(_ctx(), vs, given, "Q1: 1.2")
    assert given[1] == [skel.SkelRow(1, 3, "vede", "subj", 1, 2)]


def test_apply_missing_arg_allows_a_fused_clitic_to_fill_two_slots():
    """The exception is rule AL's, and it is the rule's own gate that grants it: Layer 2 tags
    "gliel" as two fused pronouns, so the dative and the accusative of one verb are one token."""
    morph_rows = {
        1: [morph.MorphRow(word="non", pos="adverb"),
            morph.MorphRow(word="gliel", lemma="gliel", pos="pronoun+pronoun"),
            morph.MorphRow(word="celai", lemma="celare", pos="verb", person="1", number="sg.")],
    }
    ctx = drv._UnitContext([1], ["non gliel celai"], morph_rows, {})
    given = _rows(skel.SkelRow(1, 3, "celai", "obj", 1, 2))
    # Built directly: the pair (obj, obl:a) on one fused clitic is what rule AL licenses, so
    # `_classify_divergence` reports nothing for it at all — there is no violation to derive here.
    vs = [morph.Violation(1, "tag", "missing_arg: 1.3 obl:a (1, 2)",
                          role="obl:a", arg=(1, 2), predicate=(1, 3))]
    assert drv._apply_missing_arg(ctx, vs, given, "Q1: 1.2")
    assert skel.SkelRow(1, 3, "celai", "obl:a", 1, 2) in given[1]


# --- arg_slot: the two sides of one slot, merged into one question -------------------------------


def _slot_conflict_violations():
    """One disagreement about `vede`'s object: the derivation says 2.2, the reading says 1.2. The
    checker reports it as a `missing_arg` and an `extra_arg` on the same role."""
    derived = {1: [skel.SkelRow(1, 3, "vede", "obj", 2, 2)]}
    given = _rows(skel.SkelRow(1, 3, "vede", "obj", 1, 2))
    return given, skel._classify_divergence(given, derived)


def test_split_slot_conflicts_merges_the_pair_into_one_question():
    given, violations = _slot_conflict_violations()
    ctx = _ctx()
    by_class: dict[str, list] = {}
    for v in violations:
        by_class.setdefault(drv._violation_subclass(v, ctx), []).append(v)
    assert set(by_class) == {"missing_arg", "extra_arg"}, "fixture must open both sides"
    merged = drv._split_slot_conflicts(by_class)
    assert set(merged) == {"arg_slot"}
    # The half kept is the one carrying the reading's own filler, which is what may be quoted.
    assert merged["arg_slot"][0].arg == (1, 2)


def test_split_slot_conflicts_leaves_unrelated_violations_alone():
    """Two different slots of one predicate are two questions, not one — the merge is keyed on the
    role, not on the predicate."""
    derived = {1: [skel.SkelRow(1, 3, "vede", "subj", 2, 2)]}
    given = _rows(skel.SkelRow(1, 3, "vede", "obj", 1, 2))
    by_class: dict[str, list] = {}
    for v in skel._classify_divergence(given, derived):
        by_class.setdefault(drv._violation_subclass(v, _ctx()), []).append(v)
    assert drv._split_slot_conflicts(by_class) == by_class


def test_arg_slot_question_names_the_reading_own_filler_and_not_the_derived_one():
    given, violations = _slot_conflict_violations()
    vs = [v for v in violations if v.detail.startswith("extra_arg")]
    asked = drv._ask_arg_slot(_ctx(), vs).split("Q1:", 1)[1]
    assert "1.2" in asked          # the filler the reading itself wrote
    assert "'obj'" in asked        # the slot in dispute
    assert "2.2" not in asked      # never the derivation's answer


def test_apply_arg_slot_moves_the_slot_to_the_answered_token():
    given, violations = _slot_conflict_violations()
    vs = [v for v in violations if v.detail.startswith("extra_arg")]
    assert drv._apply_arg_slot(_ctx(), vs, given, "Q1: 2.2")
    assert given[1] == [skel.SkelRow(1, 3, "vede", "obj", 2, 2)]


def test_apply_arg_slot_keep_and_none():
    given, violations = _slot_conflict_violations()
    vs = [v for v in violations if v.detail.startswith("extra_arg")]
    assert not drv._apply_arg_slot(_ctx(), vs, given, "Q1: keep")
    assert len(given[1]) == 1
    assert drv._apply_arg_slot(_ctx(), vs, given, "Q1: none")
    assert given[1] == []


# --- dual_role (rule EG) ------------------------------------------------------------------------


def _dual_role_fixture():
    given = _rows(skel.SkelRow(1, 3, "vede", "subj", 1, 2),
                  skel.SkelRow(1, 3, "vede", "obj", 1, 2))
    vs = skel._dual_role_violations([r for rows in given.values() for r in rows], _MORPH, None)
    return given, vs


def test_dual_role_question_quotes_both_roles():
    given, vs = _dual_role_fixture()
    assert len(vs) == 1
    assert drv._violation_class(vs[0]) == "dual_role"
    asked = drv._ask_dual_role(_ctx(), vs).split("Q1:", 1)[1]
    # Internal to the reading, so both of its own rows may be named; nothing derived is disclosed.
    assert "'subj'" in asked and "'obj'" in asked and "1.2" in asked


def test_apply_dual_role_keeps_the_answered_role_and_drops_the_other():
    given, vs = _dual_role_fixture()
    assert drv._apply_dual_role(_ctx(), vs, given, "Q1: obj")
    assert given[1] == [skel.SkelRow(1, 3, "vede", "obj", 1, 2)]


def test_apply_dual_role_both_changes_nothing():
    given, vs = _dual_role_fixture()
    assert not drv._apply_dual_role(_ctx(), vs, given, "Q1: both")
    assert len(given[1]) == 2


def test_apply_dual_role_can_replace_both_rows_with_a_third_role():
    given, vs = _dual_role_fixture()
    assert drv._apply_dual_role(_ctx(), vs, given, "Q1: iobj")
    assert given[1] == [skel.SkelRow(1, 3, "vede", "iobj", 1, 2)]


# --- extra_tuple ------------------------------------------------------------------------------------


def _extra_tuple_fixture():
    """`chiaro` (2.3) is listed as a predicate of its own; the derivation proposes no such
    clause. This is the attributive-adjective shape."""
    derived = {1: [skel.SkelRow(1, 3, "vede", "subj", 1, 2)]}
    given = _rows(skel.SkelRow(1, 3, "vede", "subj", 1, 2),
                  skel.SkelRow(2, 3, "chiaro", "subj", 2, 2))
    violations = [v for v in skel._classify_divergence(given, derived)
                  if v.detail.startswith("extra_tuple")]
    return given, violations


def test_apply_extra_tuple_yes_changes_nothing():
    given, vs = _extra_tuple_fixture()
    assert not drv._apply_extra_tuple(_ctx(), vs, given, "Q1: yes")
    assert len(given[2]) == 1


def test_apply_extra_tuple_no_withdraws_the_predicate():
    given, vs = _extra_tuple_fixture()
    assert drv._apply_extra_tuple(_ctx(), vs, given, "Q1: no -")
    assert given[2] == []


def test_apply_extra_tuple_no_with_a_host_recites_it_as_an_argument():
    given, vs = _extra_tuple_fixture()
    assert drv._apply_extra_tuple(_ctx(), vs, given, "Q1: no 1.3 attr")
    assert given[2] == []
    assert skel.SkelRow(1, 3, "vede", "attr", 2, 3) in given[1]


def test_apply_extra_tuple_rejects_a_host_role_outside_the_vocabulary():
    given, vs = _extra_tuple_fixture()
    drv._apply_extra_tuple(_ctx(), vs, given, "Q1: no 1.3 modifier")
    assert given[2] == []                                  # the withdrawal still stands
    assert all(r.role != "modifier" for r in given[1])     # the bad role does not


# --- missing_tuple ------------------------------------------------------------------------------------


def test_apply_missing_tuple_adds_only_the_predicates_that_were_asked_about():
    derived = {2: [skel.SkelRow(2, 3, "chiaro", "subj", 2, 2)]}
    given = _rows(skel.SkelRow(1, 3, "vede", "subj", 1, 2))
    vs = [v for v in skel._classify_divergence(given, derived)
          if v.detail.startswith("missing_tuple")]
    assert vs
    answer = (
        "| Pred Line | Pred Token | Pred Word | Role | Arg Line | Arg Token | Arg Word |\n"
        "|---|---|---|---|---|---|---|\n"
        "| 2 | 3 | chiaro | subj | 2 | 2 | lume |\n"
        "| 1 | 3 | vede | obj | 2 | 2 | lume |\n"  # not asked about — must be ignored
    )
    assert drv._apply_missing_tuple(_ctx(), vs, given, answer)
    assert skel.SkelRow(2, 3, "chiaro", "subj", 2, 2) in given[2]
    assert all(r.role != "obj" for r in given[1])


def test_apply_missing_tuple_survives_an_unparseable_answer():
    derived = {2: [skel.SkelRow(2, 3, "chiaro", "subj", 2, 2)]}
    given = _rows(skel.SkelRow(1, 3, "vede", "subj", 1, 2))
    vs = [v for v in skel._classify_divergence(given, derived)
          if v.detail.startswith("missing_tuple")]
    assert not drv._apply_missing_tuple(_ctx(), vs, given, "There is no such clause.")
    assert 2 not in given


# --- class routing --------------------------------------------------------------------------------


def test_violation_subclass_splits_extra_tuple_by_pos():
    ctx = _ctx()
    v = morph.Violation(2, "tag", "extra_tuple: predicate 2.3 not derived", predicate=(2, 3))
    assert drv._violation_subclass(v, ctx) == "extra_tuple_adjective"


def test_violation_subclass_splits_missing_tuple_on_a_non_verb():
    ctx = _ctx()
    v = morph.Violation(2, "tag", "missing_tuple: predicate 2.2 not proposed", predicate=(2, 2))
    assert drv._violation_subclass(v, ctx) == "missing_tuple_nominal"
    verb = morph.Violation(1, "tag", "missing_tuple: predicate 1.3 not proposed", predicate=(1, 3))
    assert drv._violation_subclass(verb, ctx) == "missing_tuple"


def test_every_ordered_class_has_a_prompt_and_vice_versa():
    """`_CLASS_ORDER` drives the loop and `_CLASS_PROMPTS` supplies the instrument; a class in
    one and not the other is silently never asked, or asked in an undefined order."""
    assert set(drv._CLASS_ORDER) == set(drv._CLASS_PROMPTS)


def test_membership_has_no_prompt_on_purpose():
    assert "membership" not in drv._CLASS_PROMPTS
    assert "unknown_role" not in drv._CLASS_PROMPTS


# --- stage 1 inside --fix ---------------------------------------------------------------------------


def test_apply_unit_repairs_rolls_back_a_rewrite_that_does_not_help(monkeypatch):
    """The stage-1 applier verifies every rewrite. A rule that proposes something the checker
    does not actually like must leave the rows exactly as it found them."""
    rows_by_line = _rows(skel.SkelRow(1, 3, "vede", "subj", 0, 0))
    before = {no: list(rs) for no, rs in rows_by_line.items()}
    bad = skel.Repair("bogus", (1, 3), rows_by_line[1][0],
                      skel.SkelRow(1, 3, "vede", "subj", 9, 9))
    monkeypatch.setattr(skel, "_find_repairs", lambda *a, **k: [bad])
    applied = drv._apply_unit_repairs(_NOS, _TEXTS, rows_by_line, _MORPH, {}, {}, None)
    assert applied == []
    assert rows_by_line == before


class _FakeStream:
    def end(self): pass
    def error(self, *a, **k): pass


class _FakeProgress:
    def update(self, *a, **k): pass
    def __enter__(self): return self
    def __exit__(self, *a): return False


class _FakeUI:
    """Enough of `llm7shi.statusline.StatusLine` for `_fix_canto` to run headless."""
    stream = _FakeStream()

    def progress(self, *a, **k): return _FakeProgress()

    def log(self, *a, **k): pass


class _FakeClient:
    """A model that always answers `reply`, recording the system prompt it was given."""
    seen: list[tuple[str, str]] = []

    def __init__(self, reply):
        self._reply = reply

    def __call__(self, prompt):
        _FakeClient.seen.append((self._system, prompt))
        return type("R", (), {"text": self._reply})()

    def set_system_prompt(self, text):
        self._system = text


def _stub_model(monkeypatch, reply):
    """Point `_ask_class`'s `from llm7shi import Client` at a canned answer, and keep the run
    from touching the committed artifact."""
    import llm7shi
    _FakeClient.seen = []
    monkeypatch.setattr(llm7shi, "Client",
                        lambda *a, **k: _FakeClient(reply), raising=False)
    written: list = []
    monkeypatch.setattr(drv.skel, "write_skel", lambda *a, **k: written.append(a))
    return written


# Purgatorio 1's `missing_arg` at 102.1 is the smallest real case for driving the whole stage-2
# loop: one violation in its own parse unit, whose argument is `intorno` (100.3), an adverb, so it
# routes to the `missing_arg_adverb` subclass — the position is itself one of the 82 locative-adverb
# omissions that class was written for. The canto's other two soft violations are rule EG's
# `dual_role` at 96.6 and 133.7, in two other units, and each gets its own class question.
def test_fix_canto_asks_only_the_flagged_class_and_keeps_a_refusal_harmless(monkeypatch):
    written = _stub_model(monkeypatch, "Q1: none")
    stats = drv._fix_canto("purgatorio", 1, 34, "fake", _FakeUI(), None, whole=False)
    assert stats["units:flagged"] == 3
    # One question per flagged unit, each keyed to that unit's own class and nothing else.
    assert stats["calls:missing_arg_adverb"] == 1
    assert stats["calls:dual_role"] == 2
    assert sum(n for k, n in stats.items() if k.startswith("calls:")) == 3
    assert sum(n for k, n in stats.items() if k.startswith("removed:")) == 0
    assert written == []                          # "none" changes nothing, so nothing is written


# Inferno 5's only flagged unit is a same-slot pair: `missing_arg subj (90,1)` and
# `extra_arg subj (92,1)` on the predicate at 92.2 — one disagreement about which token is the
# subject, which the driver must put to the model **once**.
def test_fix_canto_asks_a_same_slot_pair_as_one_question(monkeypatch):
    _stub_model(monkeypatch, "Q1: keep")
    stats = drv._fix_canto("inferno", 5, 34, "fake", _FakeUI(), None, whole=False)
    assert stats["units:flagged"] == 1
    assert stats["calls:arg_slot"] == 1
    assert sum(n for k, n in stats.items() if k.startswith("calls:")) == 1
    system, question = _FakeClient.seen[0]
    assert system == drv._CLASS_PROMPTS["arg_slot"].system
    assert "90.1" not in question.split("Q1:", 1)[1]   # the derivation's filler stays hidden


def test_fix_canto_accepts_a_class_answer_and_commits_it(monkeypatch):
    written = _stub_model(monkeypatch, "Q1: 100.3")
    stats = drv._fix_canto("purgatorio", 1, 34, "fake", _FakeUI(), None, whole=False)
    assert stats["removed:missing_arg_adverb"] == 1
    assert stats["units:cleared"] == 1
    assert written, "an accepted splice must be written back"


def test_fix_canto_sends_the_class_specific_system_prompt(monkeypatch):
    _stub_model(monkeypatch, "Q1: none")
    drv._fix_canto("purgatorio", 1, 34, "fake", _FakeUI(), None, whole=False)
    system, question = next(
        (s, q) for s, q in _FakeClient.seen
        if s == drv._CLASS_PROMPTS["missing_arg_adverb"].system
    )
    # The narrow prompt is a fraction of the monolithic build prompt it replaces — which is the
    # point of splitting it: the conventions that do not bear on this class are not competing
    # for the model's attention.
    assert len(system) < len(drv.SYSTEM_PROMPT) / 2
    assert "Q1:" in question


def test_apply_unit_repairs_accepts_a_rewrite_that_clears_a_violation():
    """The `prep_stack` rule end to end, through the verifying applier rather than
    `_find_repairs` alone."""
    # "in su vede / il lume chiaro": Layer 4 chains in -> su -> lume and hangs lume on vede as an
    # oblique, so the derivation names `obl:su` where the committed row names `obl:in`. This test
    # needs prepositions in the text itself, so it does not use the shared fixture.
    texts = ["in su vede", "il lume chiaro"]
    morph_rows = {
        1: [morph.MorphRow(word="in", lemma="in", pos="preposition"),
            morph.MorphRow(word="su", lemma="su", pos="preposition"),
            morph.MorphRow(word="vede", lemma="vedere", pos="verb", person="3", number="sg.")],
        2: _MORPH[2],
    }
    dep_rows = {
        1: [dep.DepRow(line=1, token=1, word="in", deprel="case", head_line=1, head_token=2),
            dep.DepRow(line=1, token=2, word="su", deprel="case", head_line=2, head_token=2),
            dep.DepRow(line=1, token=3, word="vede", deprel="root", head_line=0, head_token=0)],
        2: [dep.DepRow(line=2, token=2, word="lume", deprel="obl", head_line=1, head_token=3)],
    }
    rows_by_line = _rows(skel.SkelRow(1, 3, "vede", "obl:in", 2, 2))
    applied = drv._apply_unit_repairs(_NOS, texts, rows_by_line, morph_rows, {}, dep_rows, None)
    assert [r.kind for r in applied] == ["prep_stack"]
    assert rows_by_line[1][0].role == "obl:su"


# --- field notes: the model's report on a question it could not answer cleanly ------------------


def test_split_field_notes_reads_question_numbered_notes():
    text = "Q1: obj\nQ2: subj\nN2: the sentence writes no subject for this verb."
    clean, notes = drv._split_field_notes(text)
    assert drv._parse_answers(clean) == {1: "obj", 2: "subj"}
    assert [(n.index, n.pos) for n in notes] == [(2, None)]
    assert notes[0].text == "the sentence writes no subject for this verb."


def test_split_field_notes_reads_position_cited_notes():
    """The table classes number no questions, so their notes cite a token instead — and the
    `<line>.<token>` form must not be read as a question number with a period after it."""
    _, notes = drv._split_field_notes("| 1 | 3 | vede | subj | 1 | 2 | donna |\nN2.3: ambiguous.")
    assert [(n.index, n.pos, n.text) for n in notes] == [(None, (2, 3), "ambiguous.")]


def test_split_field_notes_removes_them_from_the_response():
    """The whole no-op guarantee rests on this: what reaches `apply`/`resolve_chunk` is the text
    that would have arrived without the instrument."""
    table = "| Pred Line | Pred Token |\n|---|---|\n| 1 | 3 |"
    clean, notes = drv._split_field_notes(f"{table}\nN1.3: two readings fit equally well.")
    assert [ln for ln in clean.splitlines() if ln.strip()] == table.splitlines()
    assert len(notes) == 1


def test_split_field_notes_ignores_a_response_without_any():
    text = "Q1: obj\nQ2: keep"
    assert drv._split_field_notes(text) == (text, [])


def test_log_field_notes_writes_one_tab_separated_line_per_note(tmp_path):
    log = tmp_path / "skel.log"
    notes = [drv._FieldNote(1, None, "no token fills this slot"),
             drv._FieldNote(None, (1, 3), "two readings fit")]
    drv._log_field_notes(log, "inferno 5", [1, 2], "missing_arg", notes,
                         {1: "1.3 'vede' subj"}, _ctx().word)
    rows = [ln.split("\t") for ln in log.read_text(encoding="utf-8").splitlines()]
    assert [r[0] for r in rows] == ["NOTE", "NOTE"]
    assert rows[0] == ["NOTE", "inferno 5", "1-2", "missing_arg", "1.3 'vede' subj",
                       "no token fills this slot"]
    # The position-cited note resolves its own word, so a census never needs the source open.
    assert rows[1][4] == "1.3 'vede'"


def test_fix_canto_logs_a_field_note_against_its_own_position(monkeypatch, tmp_path):
    """End to end: an answer carrying a note files it under the class and predicate it came
    from, which is what makes the log a list of positions to read."""
    log = tmp_path / "skel.log"
    _stub_model(monkeypatch, "Q1: none\nN1: no locative in this sentence answers 'where'.")
    drv._fix_canto("purgatorio", 1, 34, "fake", _FakeUI(), log, whole=False)
    notes = [ln.split("\t") for ln in log.read_text(encoding="utf-8").splitlines()
             if ln.startswith("NOTE")]
    assert notes, "the note must reach the log"
    assert any(n[3] == "missing_arg_adverb" for n in notes)
    assert all(n[5] == "no locative in this sentence answers 'where'." for n in notes)


def test_a_field_note_changes_nothing_about_the_splice(monkeypatch):
    """The instrument is inert by construction: the same answer with and without a note must
    produce the same stats, or a round stops being comparable with the six before it."""
    _stub_model(monkeypatch, "Q1: 100.3")
    plain = drv._fix_canto("purgatorio", 1, 34, "fake", _FakeUI(), None, whole=False)
    _stub_model(monkeypatch, "Q1: 100.3\nN1: the antecedent is not obvious here.")
    noted = drv._fix_canto("purgatorio", 1, 34, "fake", _FakeUI(), None, whole=False)
    assert plain == noted
