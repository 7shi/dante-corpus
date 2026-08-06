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
