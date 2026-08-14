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


# Purgatorio 1 carries exactly one soft violation — a `missing_arg` at 102.1 — which makes it the
# smallest real case for driving the whole stage-2 loop. Its argument is `intorno` (100.3), an
# adverb, so it routes to the `missing_arg_adverb` subclass: the position is itself one of the 82
# locative-adverb omissions that class was written for.
def test_fix_canto_asks_only_the_flagged_class_and_keeps_a_refusal_harmless(monkeypatch):
    written = _stub_model(monkeypatch, "Q1: none")
    stats = drv._fix_canto("purgatorio", 1, 34, "fake", _FakeUI(), None, whole=False)
    assert stats["units:flagged"] == 1
    assert sum(n for k, n in stats.items() if k.startswith("calls:")) == 1
    assert stats["calls:missing_arg_adverb"] == 1  # and no question about any other class
    assert sum(n for k, n in stats.items() if k.startswith("removed:")) == 0
    assert written == []                          # "none" changes nothing, so nothing is written


def test_fix_canto_accepts_a_class_answer_and_commits_it(monkeypatch):
    written = _stub_model(monkeypatch, "Q1: 100.3")
    stats = drv._fix_canto("purgatorio", 1, 34, "fake", _FakeUI(), None, whole=False)
    assert stats["removed:missing_arg_adverb"] == 1
    assert stats["units:cleared"] == 1
    assert written, "an accepted splice must be written back"


def test_fix_canto_sends_the_class_specific_system_prompt(monkeypatch):
    _stub_model(monkeypatch, "Q1: none")
    drv._fix_canto("purgatorio", 1, 34, "fake", _FakeUI(), None, whole=False)
    system, question = _FakeClient.seen[0]
    assert system == drv._CLASS_PROMPTS["missing_arg_adverb"].system
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
