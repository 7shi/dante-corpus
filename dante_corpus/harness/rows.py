"""The seam: what the apparatus knows about a row, and nothing more.

Measured after Stage 10 closed, the apparatus turned out to be coupled to Layer 5
by a *type* rather than by behaviour — `skel.models.SkelRow` was carried by eight
modules that are otherwise indifferent to what a row means. This module is what
replaces that type at the boundary.

The choice is a **codec the subject supplies**, not a row type the apparatus
owns. Two things rule the alternatives out. A bare `Protocol` cannot carry a
constructor or an ordering, and the apparatus needs both: `TsvArtifact.load`
builds rows back out of the file, and every render sorts them. An
apparatus-owned row type is worse still — loaded rows flow straight on into the
subject's own code (gate 2's validator, gate 3's writer), so an intermediate
type would mean converting at each crossing, on the path whose bytes gate 3
pins. The codec keeps the subject's own row type flowing end to end and puts the
facts the apparatus needs *about* it in one object.

A frozen dataclass of callables is this project's idiom for a small injected
contract; `harness/extractor/fixlevel.py`'s `FixClass` carries its five
predicates the same way.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable, Protocol, Sequence, runtime_checkable

__all__ = [
    "ROW_FIELDS",
    "PositionKey",
    "Row",
    "RowCodec",
    "RowKey",
    "Violation",
    "position_key",
    "row_key",
]

# The row schema the apparatus reconstructs: a predicate token pointing at an
# argument token under a label. Four copies of this tuple existed before the
# split (`artifact.py`, `fixedcontext.py`, `fixlevel.py`, `runner/tools.py`,
# each mirroring `skel.io._TSV_HEADER`); collapsing them here is what makes the
# byte-exactness gate 3 rests on checkable in one place.
ROW_FIELDS = ("line", "token", "word", "role", "arg_line", "arg_token")


@runtime_checkable
class Row(Protocol):
    """A subject's row, structurally. `dante_corpus.skel.models.SkelRow` is one."""

    line: int
    token: int
    word: str
    role: str
    arg_line: int
    arg_token: int


@runtime_checkable
class Violation(Protocol):
    """What the apparatus reads off a finding: enough to count it and log it.

    Structural, so the subject's own violation type satisfies it without
    inheriting anything — `dante_corpus.morph.Violation` does.
    """

    line: int
    kind: str
    detail: str


# The two key shapes that both used to be called `RowKey`, named apart.
RowKey = tuple[int, int, str, int, int]  # with the label: was `layers.RowKey`
PositionKey = tuple[int, int, int, int]  # without it, so a relabel keeps its key


def row_key(row: Row) -> RowKey:
    return (row.line, row.token, row.role, row.arg_line, row.arg_token)


def position_key(row: Row) -> PositionKey:
    return (row.line, row.token, row.arg_line, row.arg_token)


@dataclass(frozen=True)
class RowCodec:
    """How one subject's row type crosses the apparatus boundary.

    `make` is the row constructor, called with `header`'s names as keywords.
    `sort_key` is the subject's own row order — Layer 5 ranks by its role
    vocabulary (`skel.models._row_sort_key`), which is exactly the kind of fact
    the apparatus must not guess: the artifact's bytes are that order.
    """

    make: Callable[..., Row]
    sort_key: Callable[[Row], tuple]
    header: tuple[str, ...] = ROW_FIELDS
    sentinel_token: int = 0

    def cells(self, no: int, row: Row) -> tuple[str, ...]:
        """One row's TSV cells, under the block's line number."""
        return (
            str(no),
            str(row.token),
            row.word,
            row.role,
            str(row.arg_line),
            str(row.arg_token),
        )

    def sentinel_cells(self, no: int) -> tuple[str, ...]:
        """A line that was processed and has no predicates."""
        return (str(no), str(self.sentinel_token), "", "", "0", "0")

    def parse_cells(self, cells: Sequence[str]) -> tuple[int, Row | None]:
        """`(line number, row)` for one TSV line; the row is None for a sentinel.

        The sentinel still reports its line, because line-number presence is the
        settled-unit test (`../../harness/stages/05.md` record S5.5).
        """
        padded = list(cells) + [""] * (len(self.header) - len(cells))
        no = int(padded[0])
        token = int(padded[1])
        if token == self.sentinel_token:
            return no, None
        return no, self.make(
            line=no,
            token=token,
            word=padded[2],
            role=padded[3],
            arg_line=int(padded[4]),
            arg_token=int(padded[5]),
        )

    def to_dict(self, row: Row) -> dict:
        """The candidate-row dict form the model's answer is read and written in."""
        return {
            "line": row.line,
            "token": row.token,
            "word": row.word,
            "role": row.role,
            "arg_line": row.arg_line,
            "arg_token": row.arg_token,
        }

    def sorted(self, rows: Iterable[Row]) -> list[Row]:
        return sorted(rows, key=self.sort_key)
