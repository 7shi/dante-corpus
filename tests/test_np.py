"""Deterministic tests for Layer 3's clitic mentions (no model calls).

The `+lemma` mentions are derived from Layer 2 rather than authored, so both directions of that
derivation are checked here: what `clitic_mentions` produces, and what `validate_line` accepts as
a mention of a fused host. `np/np.py --fix-clitics` reconciles a frozen artifact against exactly
these two, in both directions.
"""

from dante_corpus.morph import MorphRow
from dante_corpus.np import NPSpan, clitic_mentions, validate_line

# purgatorio 13:141 — `meco` is one bound pronoun (`me`) plus a preposition (`con`).
MECO = MorphRow(word="meco", lemma="me+con", pos="pronoun+preposition")
# purgatorio 16:139 — `nol` = `non lo`, an adverb plus one bound pronoun.
NOL = MorphRow(word="nol", lemma="non+lo", pos="adverb+pronoun")
# A bare pronoun: Layer 1 tokenized it on its own, so it is an ordinary NP, not a mention.
CHE = MorphRow(word="che", lemma="che", pos="pronoun")


def test_clitic_mentions_names_only_the_pronoun_components():
    assert [m.text for m in clitic_mentions(1, ["meco"], [MECO])] == ["+me"]
    assert [m.text for m in clitic_mentions(1, ["nol"], [NOL])] == ["+lo"]


def test_clitic_mentions_skips_bare_pronouns():
    assert clitic_mentions(1, ["che"], [CHE]) == []


def test_validate_line_rejects_a_non_pronoun_component_of_a_fusion():
    """`meco` carrying `+con` names the preposition — a lemma part, but not a pronoun."""
    bad = [NPSpan(line=1, start=1, end=1, head=1, text="+con")]
    kinds = [v.kind for v in validate_line(1, "meco", bad, [MECO])]
    assert "word" in kinds

    good = [NPSpan(line=1, start=1, end=1, head=1, text="+me")]
    assert [v.kind for v in validate_line(1, "meco", good, [MECO])] == []


def test_validate_line_reports_a_missing_mention_as_soft():
    violations = validate_line(1, "nol", [], [NOL])
    assert [v.kind for v in violations] == ["tag"]
    assert "+lo" in violations[0].detail
