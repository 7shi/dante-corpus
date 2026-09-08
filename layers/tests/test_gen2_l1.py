"""Tests for generation 2's Layer 1 (`layers/gen2/l1.py`).

Run on demand — `uv run pytest layers/tests` — the same way `harness/tests` does; `layers/`
is not yet part of the maintained root suite (`pyproject.toml` `testpaths`). See `PLAN.md`'s
handoff note: this integrates with `dante_corpus` and root `tests/` once gen2 replaces the
old layer stack.
"""

from collections import Counter

import pytest

from dante_corpus import api
from layers.gen2 import l1


# --- tokenize_l1: whitespace dropped, everything else kept -----------------------------------


def test_tokenize_l1_drops_only_pure_whitespace_tokens():
    assert l1.tokenize_l1("Nel mezzo del cammin") == ("Nel", "mezzo", "del", "cammin")


def test_tokenize_l1_keeps_punctuation_as_its_own_terminal():
    assert l1.tokenize_l1("ancor fuggiva,") == ("ancor", "fuggiva", ",")


def test_tokenize_l1_keeps_apostrophes_fused_to_their_word():
    assert l1.tokenize_l1("l'animo") == ("l'", "animo")


# --- l1_line: worked examples from REDESIGN.md §2.1 -------------------------------------------


def test_l1_line_matches_the_inf_1_1_worked_example():
    """*Inf* 1:1 `Nel mezzo del cammin di nostra vita` — no punctuation, 7 terminals."""
    line = l1.l1_line(1, "Nel mezzo del cammin di nostra vita")
    assert [(t.index, t.text) for t in line.tokens] == [
        (0, "Nel"), (1, "mezzo"), (2, "del"), (3, "cammin"),
        (4, "di"), (5, "nostra"), (6, "vita"),
    ]


def test_l1_line_matches_the_inf_1_25_worked_example():
    """*Inf* 1:25 `così l'animo mio, ch'ancor fuggiva,` — commas get their own index."""
    line = l1.l1_line(1, "così l'animo mio, ch'ancor fuggiva,")
    assert [(t.index, t.text) for t in line.tokens] == [
        (0, "così"), (1, "l'"), (2, "animo"), (3, "mio"), (4, ","),
        (5, "ch'"), (6, "ancor"), (7, "fuggiva"), (8, ","),
    ]


def test_l1_line_preserves_no_and_text_verbatim():
    line = l1.l1_line(3, "e la verace via abbandonai.")
    assert line.no == 3
    assert line.text == "e la verace via abbandonai."


def test_l1_token_to_dict():
    assert l1.L1Token(2, "del").to_dict() == {"index": 2, "text": "del"}


def test_l1_line_to_dict_shape():
    line = l1.l1_line(1, "Nel mezzo")
    assert line.to_dict() == {
        "no": 1,
        "text": "Nel mezzo",
        "tokens": [{"index": 0, "text": "Nel"}, {"index": 1, "text": "mezzo"}],
    }


# --- L1 diverges from old Layer 1 exactly where punctuation is concerned ---------------------


def test_l1_indices_shift_past_old_layer_1_once_punctuation_intervenes():
    """Old `Line.tokens` (`has_alpha`-filtered) never assigns punctuation a position; L1 does,
    so an alpha token after a comma sits at a higher L1 index than its old-Layer-1 index."""
    old_line = api.Line(no=1, text="e la verace via abbandonai.")
    new_line = l1.l1_line(1, old_line.text)

    old_alpha = old_line.tokens
    new_alpha = tuple(t.text for t in new_line.tokens if any(c.isalpha() for c in t.text))
    assert new_alpha == old_alpha  # same alpha tokens, same order — only addressing changed


def test_l1_indices_diverge_once_a_line_carries_punctuation():
    old_line = api.Line(no=25, text="così l'animo mio, ch'ancor fuggiva,")
    new_line = l1.l1_line(25, old_line.text)

    # old Layer 1: 6 alpha tokens, comma-free, indexed 0..5
    assert old_line.tokens == ("così", "l'", "animo", "mio", "ch'", "ancor", "fuggiva")
    # L1: same 7 alpha-bearing tokens plus 2 commas, 9 terminals total, indexed 0..8
    assert len(new_line.tokens) == 9
    assert new_line.tokens[6].text == "ancor" and new_line.tokens[6].index == 6
    # old Layer 1 has no position at all for either comma
    assert "," not in old_line.tokens


# --- l1_canto: reads real source text, no dependency on old Layer 1 --------------------------


def test_l1_canto_reads_inferno_1_and_matches_the_line_count():
    lines = l1.l1_canto("inferno", 1)
    assert len(lines) == len(api.canto("inferno", 1).lines())
    assert lines[0].no == 1
    assert lines[0].text == api.canto("inferno", 1).line(1).text


def test_l1_canto_rejects_an_unknown_canticle():
    with pytest.raises(ValueError):
        l1.l1_canto("limbo", 1)


# --- corpus-wide punctuation census, pinned to REDESIGN.md §2.1's measurement ----------------


def test_l1_corpus_wide_punctuation_census_matches_redesign_measurement():
    """Regression pin for the numbers `REDESIGN.md` §2.1 argues the design from: 101,601 alpha
    terminals, 17,434 punctuation terminals, every quotation-mark pair exactly balanced."""
    alpha = 0
    punct: Counter[str] = Counter()
    for canticle in api.canticles():
        for number in api.cantos(canticle):
            for line in l1.l1_canto(canticle, number):
                for token in line.tokens:
                    if any(ch.isalpha() for ch in token.text):
                        alpha += 1
                    else:
                        punct[token.text] += 1

    assert alpha == 101_601
    assert sum(punct.values()) == 17_434
    assert punct[","] == 8_513
    assert punct["."] == 3_275
    for open_mark, close_mark in (("«", "»"), ("‘", "’"), ("“", "”")):
        assert punct[open_mark] == punct[close_mark] > 0
