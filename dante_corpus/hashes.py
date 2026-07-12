"""Content hashes for corpus artifacts (PLAN.md "Versioning").

Every canto x layer artifact is content-addressed by the sha256 of its file bytes, so a
consumer can record exactly which parse a derived artifact annotated and recompute only what a
regeneration actually changed. Regenerating one canto changes only that canto's hash for the
layers touched — nothing else downstream is invalidated. Quotes are out of scope: the artifact
is one XML file per canticle, not canto-granular.

This module is intentionally thin and stays free of `api`: it dispatches to each layer
module's own `artifact_path` alias (added alongside `morph.py`/`np.py`/`dep.py`/`skel.py`'s
existing `_artifact_path`), so path ownership stays with the layer that defines the artifact.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

from . import dep as _dep
from . import morph as _morph
from . import np as _np
from . import skel as _skel
from ._paths import SRC_DIR

LAYERS = ("text", "morph", "np", "dep", "skel")

_ARTIFACT_PATH = {
    "morph": _morph.artifact_path,
    "np": _np.artifact_path,
    "dep": _dep.artifact_path,
    "skel": _skel.artifact_path,
}


def artifact_path(layer: str, canticle: str, number: int) -> Path:
    if layer == "text":
        return SRC_DIR / canticle / f"{number:02d}.txt"
    if layer in _ARTIFACT_PATH:
        return _ARTIFACT_PATH[layer](canticle, number)
    raise ValueError(f"unknown layer: {layer}")


def artifact_hash(layer: str, canticle: str, number: int) -> str:
    """sha256 hex digest of one canto x layer artifact's file bytes."""
    path = artifact_path(layer, canticle, number)
    if not path.exists():
        raise FileNotFoundError(path)
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canto_hashes(canticle: str, number: int) -> dict[str, str]:
    """{layer: sha256} for every layer whose artifact currently exists for this canto."""
    result: dict[str, str] = {}
    for layer in LAYERS:
        path = artifact_path(layer, canticle, number)
        if path.exists():
            result[layer] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result
