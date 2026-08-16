"""Tests for the corpus source-enumeration API."""

import pytest

from dante_corpus import api


def test_cantos_enumerates_the_built_source_tree():
    assert api.cantos("inferno") == tuple(range(1, 35))


def test_cantos_rejects_an_unknown_canticle():
    with pytest.raises(ValueError):
        api.cantos("limbo")


def test_cantos_raises_when_the_source_tree_is_missing(tmp_path, monkeypatch):
    """An unbuilt `src/` must not read as "zero cantos".

    Every caller of `cantos()` is a build or `--check` driver that iterates the result, so a silent
    `()` made `--check` print `0 hard, 0 soft` without having examined a single canto.
    """
    monkeypatch.setattr(api, "SRC_DIR", tmp_path)
    with pytest.raises(FileNotFoundError):
        api.cantos("inferno")


def test_cantos_raises_when_the_canticle_directory_is_empty(tmp_path, monkeypatch):
    (tmp_path / "inferno").mkdir()
    monkeypatch.setattr(api, "SRC_DIR", tmp_path)
    with pytest.raises(FileNotFoundError):
        api.cantos("inferno")


def test_canticles_still_probes_without_raising(tmp_path, monkeypatch):
    """`canticles()` is the probe; only `cantos()` treats absence as an error."""
    monkeypatch.setattr(api, "SRC_DIR", tmp_path)
    assert api.canticles() == ()


# --- the build drivers' shared `-c` selection ------------------------------------------------


@pytest.mark.parametrize("spec, expected", [
    ("7", ((7, 7),)),
    ("12-", ((12, None),)),
    ("-20", ((None, 20),)),
    ("11-20", ((11, 20),)),
    ("1,5,7", ((1, 1), (5, 5), (7, 7))),
    ("1,3-5,11-", ((1, 1), (3, 5), (11, None))),
    (" 1 , 3 - 5 ", ((1, 1), (3, 5))),
])
def test_parse_canto_spec_reads_every_form(spec, expected):
    assert api.parse_canto_spec(spec) == expected


@pytest.mark.parametrize("spec", ["", "1,,3", "-", "abc", "1-x", "5-3", "1..3"])
def test_parse_canto_spec_rejects_malformed_input(spec):
    with pytest.raises(ValueError):
        api.parse_canto_spec(spec)


def test_select_cantos_filters_and_orders_by_canto_number():
    assert api.select_cantos("inferno", "33-") == (33, 34)
    assert api.select_cantos("inferno", "-3") == (1, 2, 3)
    assert api.select_cantos("inferno", "5,1,3-4") == (1, 3, 4, 5)
    assert api.select_cantos("inferno", None) == api.cantos("inferno")


def test_select_cantos_clamps_an_open_range_to_what_exists():
    """A spec is a filter, not an assertion that canto 40 exists — `33-` is the resume idiom."""
    assert api.select_cantos("inferno", "30-99") == (30, 31, 32, 33, 34)


def test_select_cantos_rejects_a_selection_that_matches_nothing():
    """A typo must fail loudly: a driver that selected nothing would report success unexamined."""
    with pytest.raises(ValueError):
        api.select_cantos("inferno", "40")


def test_check_canto_spec_reports_the_first_bad_canticle():
    assert api.check_canto_spec(["inferno"], None) is None
    assert api.check_canto_spec(["inferno"], "1,33-") is None
    assert "purgatorio" in api.check_canto_spec(["inferno", "purgatorio"], "34")
    assert api.check_canto_spec(["inferno"], "1-x")
