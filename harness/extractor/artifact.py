"""Layer 5's binding of the apparatus's artifact machinery.

The machinery itself is `dante_corpus.harness.artifact`, which knows nothing
about rows beyond what a `RowCodec` tells it. This module supplies Layer 5's
codec (`layers.SKEL_CODEC`) once, so every caller in the pipeline keeps the
one-argument forms it has always used and the committed TSVs keep their bytes.

`TsvArtifact` is a subclass rather than a partially applied constructor so that
`isinstance` and subclass hooks keep working for callers that use them.
"""

from __future__ import annotations

from pathlib import Path

from dante_corpus.harness import artifact as _artifact
from dante_corpus.harness.rows import Row

from harness.extractor.layers import SKEL_CODEC

__all__ = ["TsvArtifact", "render_tsv"]


def render_tsv(lines: list[tuple[int, list[Row]]]) -> str:
    """`skel.io.write_skel`'s payload for the same input, byte for byte."""
    return _artifact.render_tsv(lines, codec=SKEL_CODEC)


class TsvArtifact(_artifact.TsvArtifact):
    """The apparatus's artifact, bound to Layer 5's rows."""

    def __init__(self, path: str | Path):
        super().__init__(path, codec=SKEL_CODEC)
