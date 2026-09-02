"""The run's durable artifact: a canto's gold-format TSV, and how it is rendered.

Split out of `reconstruct.py` (S7.2). Two things live here, and they are one
thing: the renderer that must stay byte-exact with `skel.io.write_skel`, and
the file that is written through it unit by unit and read back to resume
(`../STAGE5.md` record S5.5). Keeping them together is what keeps the streamed
file byte-identical to a single-pass `render_tsv` — the property `TsvArtifact`
depends on and `test_render_tsv_matches_write_skel_bytes` pins.

Nothing here knows about gates, sessions, or gold.
"""

from __future__ import annotations

from pathlib import Path

from dante_corpus.skel.models import SkelRow, _row_sort_key

__all__ = ["TsvArtifact", "render_tsv"]

_TSV_HEADER = ("line", "token", "word", "role", "arg_line", "arg_token")


def render_tsv(lines: list[tuple[int, list[SkelRow]]]) -> str:
    """Byte-exact mirror of `skel.io.write_skel`'s payload for the same input.

    Gate 3 digests the payload *before* writing and compares against the
    recomputed content hash *after* writing, which requires rendering the
    bytes independently of the writer. If `write_skel`'s format ever drifts
    from this mirror the commit fails loudly instead of landing unverified
    bytes — `test_render_tsv_matches_write_skel_bytes` pins the parity.
    """
    return "\t".join(_TSV_HEADER) + "\n" + _render_body(lines)


def _render_body(lines: list[tuple[int, list[SkelRow]]]) -> str:
    """`render_tsv`'s payload without the header — one line block per canto line.

    Shared with `TsvArtifact.write_unit`, which appends these blocks a unit at
    a time; keeping one renderer is what makes the streamed file byte-identical
    to a whole-canto render.
    """
    out = []
    for no, rows in lines:
        if not rows:
            out.append("\t".join((str(no), "0", "", "", "0", "0")))
            continue
        for row in sorted(rows, key=_row_sort_key):
            out.append(
                "\t".join((str(no), str(row.token), row.word, row.role,
                           str(row.arg_line), str(row.arg_token)))
            )
    return "\n".join(out) + "\n"


class TsvArtifact:
    """A canto's gold-format TSV, written unit by unit and read back to resume.

    The TSV — not the log — is the run's durable artifact and its resume state
    (`../STAGE5.md` record S5.5). Two properties make that work:

    - **Append-per-unit is byte-identical to the whole-canto render.** Parse
      units come from `dep.sentence_groups` (the same call, with the same
      default `MAX_UNIT_LINES`, that `recon/check.py` validates against), so
      they are line-ordered, contiguous, and cover every line exactly once;
      `render_tsv` emits a sentinel row for a line with no predicates. Writing
      units in order therefore reproduces `render_tsv(whole canto)` exactly.
    - **Line-number presence is the settled-unit test.** Every line of a
      settled unit is in the file, sentinel or not, so a unit whose lines are
      all present needs no rerun and a unit missing any of them is unsettled.

    That second property is also the operator's fix gesture: delete the lines
    of a stretch you want reconsidered and re-run — the unit regenerates. A
    *partially* deleted unit counts as unsettled too, and its surviving rows
    are dropped, so a half-edited unit never lands half old and half new.

    Writes go through one of two paths. While the settled units form a prefix
    of the canto, each newly settled unit is appended (durable per unit, like
    the log sink). Once there is a gap in the middle — the fix case — the file
    is rewritten whole, in line order, on every settle: append cannot express
    an insertion, and the artifact must never be left in line-shuffled order.
    """

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.rows: dict[int, list[SkelRow]] = {}
        self._append_only = True

    # --- read ---------------------------------------------------------------------

    def load(self) -> dict[int, list[SkelRow]]:
        """Parse the artifact on disk (missing file = nothing settled yet).

        Mirror of `skel.io.load_skel` over an arbitrary path: a sentinel row
        (`token == 0`) registers its line as present without contributing a
        row, which is exactly what the settled-unit test needs.
        """
        self.rows = {}
        if not self.path.exists():
            return self.rows
        for index, text in enumerate(
            self.path.read_text(encoding="utf-8").splitlines()
        ):
            if index == 0 or not text:  # header / blank
                continue
            cells = text.split("\t")
            cells += [""] * (len(_TSV_HEADER) - len(cells))
            no = int(cells[0])
            token = int(cells[1])
            bucket = self.rows.setdefault(no, [])
            if token == 0:  # sentinel: line processed, no predicates
                continue
            bucket.append(
                SkelRow(line=no, token=token, word=cells[2], role=cells[3],
                        arg_line=int(cells[4]), arg_token=int(cells[5]))
            )
        return self.rows

    def settled(
        self, units: list[list[int]]
    ) -> dict[tuple[int, int], dict[int, list[SkelRow]]]:
        """`(line_start, line_end) -> rows` for every unit fully present on disk.

        Units only partially present are *not* returned and their rows are
        discarded from the in-memory artifact, so a rewrite never carries a
        half-deleted unit's leftovers.
        """
        result: dict[tuple[int, int], dict[int, list[SkelRow]]] = {}
        for group in units:
            span = (group[0], group[-1])
            if all(no in self.rows for no in group):
                result[span] = {no: list(self.rows[no]) for no in group}
            else:
                for no in group:
                    self.rows.pop(no, None)
        # A gap anywhere but the tail means later settles cannot be appended.
        settled_lines = {no for group in units for no in group if no in self.rows}
        ordered = [no for group in units for no in group]
        seen_missing = False
        for no in ordered:
            if no not in settled_lines:
                seen_missing = True
            elif seen_missing:
                self._append_only = False
                break
        return result

    # --- write --------------------------------------------------------------------

    def write_unit(self, group: list[int], rows: dict[int, list[SkelRow]]) -> None:
        """Land one settled unit, appending when possible and rewriting when not."""
        for no in group:
            self.rows[no] = list(rows.get(no, []))
        if self._append_only:
            new = not self.path.exists()
            with open(self.path, "a", encoding="utf-8") as fh:
                if new:
                    fh.write("\t".join(_TSV_HEADER) + "\n")
                fh.write(_render_body([(no, self.rows[no]) for no in group]))
                fh.flush()  # durable per unit, like the log sink
        else:
            self.rewrite()

    def reopen(self) -> None:
        """Leave the append path for good — later writes rewrite the whole file.

        A Stage-6 `--fix` run overwrites units that are already on disk, and an
        overwrite in the middle of the file cannot be expressed by appending: the
        rows would be added a second time rather than replaced. `settled` only
        clears the append flag for *missing* lines, so a caller that intends to
        replace present ones says so here.
        """
        self._append_only = False

    def rewrite(self) -> None:
        """Write every settled line in line order (the post-gap path)."""
        payload = render_tsv(
            [(no, self.rows[no]) for no in sorted(self.rows)]
        )
        self.path.write_text(payload, encoding="utf-8")
