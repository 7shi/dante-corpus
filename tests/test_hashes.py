"""Tests for content-addressed artifact hashing (PLAN.md "Versioning")."""

import hashlib

from dante_corpus import hashes


def test_artifact_path_dispatch(tmp_path, monkeypatch):
    monkeypatch.setattr(hashes, "SRC_DIR", tmp_path / "src")
    assert hashes.artifact_path("text", "inferno", 1) == tmp_path / "src" / "inferno" / "01.txt"

    try:
        hashes.artifact_path("bogus", "inferno", 1)
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError for unknown layer")


def test_artifact_hash_and_canto_hashes(tmp_path, monkeypatch):
    src_dir = tmp_path / "src"
    monkeypatch.setattr(hashes, "SRC_DIR", src_dir)
    # Isolate every layer's directory so this test sees none of the repo's real artifacts.
    monkeypatch.setattr(hashes._morph, "MORPH_DIR", tmp_path / "morph")
    monkeypatch.setattr(hashes._np, "NP_DIR", tmp_path / "np")
    monkeypatch.setattr(hashes._dep, "DEP_DIR", tmp_path / "dep")
    monkeypatch.setattr(hashes._skel, "SKEL_DIR", tmp_path / "skel")

    text_path = src_dir / "inferno" / "01.txt"
    text_path.parent.mkdir(parents=True)
    text_path.write_text("Nel mezzo del cammin di nostra vita\n", encoding="utf-8")

    expected = hashlib.sha256(text_path.read_bytes()).hexdigest()
    assert hashes.artifact_hash("text", "inferno", 1) == expected

    data = hashes.canto_hashes("inferno", 1)
    assert data == {"text": expected}  # morph/np/dep/skel artifacts don't exist yet

    # Regenerating the file (content change) changes the hash.
    text_path.write_text("Nel mezzo del cammin di nostra vita, altered\n", encoding="utf-8")
    assert hashes.artifact_hash("text", "inferno", 1) != expected


def test_artifact_hash_missing_raises(tmp_path, monkeypatch):
    monkeypatch.setattr(hashes, "SRC_DIR", tmp_path / "src")
    try:
        hashes.artifact_hash("text", "inferno", 99)
    except FileNotFoundError:
        return
    raise AssertionError("expected FileNotFoundError for missing artifact")
