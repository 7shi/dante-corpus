"""File serialization/deserialization and serve-time helpers for Layer 5."""

from __future__ import annotations

from pathlib import Path

from ..dep import DepRow
from ..morph import MorphRow, read_table, strip_word_punct
from ..np import NPSpan
from ..tokenizer import has_alpha, tokenize
from .derive import _AUX_DEPRELS
from .models import (
    SKEL_DIR,
    SkelArg,
    SkelRow,
    SkelTuple,
    _row_sort_key,
    canon_header,
)


def _alpha_tokens(text: str) -> list[str]:
    return [t for t in tokenize(text) if has_alpha(t)]


def _words_match(word: str, token: str) -> bool:
    return word == token or strip_word_punct(word, token) is not None


def _parse_int(value: str | None) -> int | None:
    if not value:
        return None
    digits = "".join(ch for ch in value if ch.isdigit())
    return int(digits) if digits else None


def resolve_chunk(
    nos: list[int], texts: list[str], table_text: str
) -> tuple[dict[int, list[SkelRow]], list[str]]:
    """Parse a skeleton table and resolve it into `SkelRow`s keyed by predicate line.

    Returns (rows-by-line, arg-word mismatch descriptions). Raises `ValueError` if no table
    can be parsed.
    """
    table = read_table(table_text)
    if table is None:
        raise ValueError("no parseable skeleton table found")
    keys = [canon_header(h) for h in table[0]]
    token_lists = {no: _alpha_tokens(t) for no, t in zip(nos, texts)}

    result: dict[int, list[SkelRow]] = {no: [] for no in nos}
    mismatches: list[str] = []
    for raw in table[2:]:  # skip header + separator
        cells = dict(zip(keys, raw))
        line = _parse_int(cells.get("line"))
        token = _parse_int(cells.get("token"))
        word = (cells.get("word") or "").strip()
        if line is None or token is None or not word or line not in result:
            continue
        role_cell = (cells.get("role") or "").strip()
        role = "" if role_cell in ("-", "", "n/a", "N/A") else role_cell
        arg_line = _parse_int(cells.get("arg_line")) or 0
        arg_token = _parse_int(cells.get("arg_token")) or 0
        if role == "":
            arg_line = arg_token = 0
        arg_word = (cells.get("arg_word") or "").strip()

        result[line].append(SkelRow(line=line, token=token, word=word, role=role,
                                     arg_line=arg_line, arg_token=arg_token))

        if arg_line and arg_token:
            arg_tokens = token_lists.get(arg_line)
            if arg_tokens is not None and 1 <= arg_token <= len(arg_tokens):
                expected = arg_tokens[arg_token - 1]
                if arg_word and not _words_match(arg_word, expected):
                    mismatches.append(
                        f"{line}.{token} cites arg {arg_line}.{arg_token} as {arg_word!r}, "
                        f"actual {expected!r}"
                    )

    for rows in result.values():
        rows.sort(key=_row_sort_key)
    return result, mismatches


# --- Serve-time joins (Layer 3 <-> Layer 5, Layer 4 <-> Layer 5) --------------------


def _iter_np(spans: tuple[NPSpan, ...]):
    for span in spans:
        yield span
        yield from _iter_np(span.children)


def np_head_index(spans: tuple[NPSpan, ...]) -> dict[tuple[int, int], NPSpan]:
    """(line, head) -> the widest Layer-3 NP headed there, over the whole nested forest."""
    idx: dict[tuple[int, int], NPSpan] = {}
    for span in _iter_np(spans):
        key = (span.line, span.head)
        current = idx.get(key)
        if current is None or (span.end - span.start) > (current.end - current.start):
            idx[key] = span
    return idx


def morph_index(data: dict[int, tuple[MorphRow, ...]]) -> dict[tuple[int, int], MorphRow]:
    return {(no, i + 1): row for no, rows in data.items() for i, row in enumerate(rows)}


def arg_np(arg: SkelArg, idx: dict[tuple[int, int], NPSpan]) -> NPSpan | None:
    """The maximal Layer-3 NP headed at `arg`'s position, or None. Derived, never stored."""
    return idx.get((arg.line, arg.token))


def antecedent(pred: SkelTuple, idx: dict[tuple[int, int], DepRow]) -> tuple[int, int] | None:
    """A relative-clause predicate's antecedent: the `acl:relcl` head position, or None."""
    row = idx.get((pred.line, pred.token))
    if row is not None and row.deprel == "acl:relcl":
        return (row.head_line, row.head_token)
    return None


def children_index(data: dict[int, tuple[DepRow, ...]]) -> dict[tuple[int, int], list[DepRow]]:
    idx: dict[tuple[int, int], list[DepRow]] = {}
    for rows in data.values():
        for row in rows:
            if not (row.head_line == 0 and row.head_token == 0):
                idx.setdefault((row.head_line, row.head_token), []).append(row)
    return idx


def pro_drop_features(
    pred: SkelTuple,
    morph_idx: dict[tuple[int, int], MorphRow],
    children_idx: dict[tuple[int, int], list[DepRow]],
) -> str:
    """Person/number of a pro-drop ∅ subject, from the predicate's own morphology or its
    finite aux/cop child. Not stored — recoverable from Layer 2 + Layer 4 at serve time.
    """
    own = morph_idx.get((pred.line, pred.token))
    if own and own.person:
        return " ".join(f for f in (own.person, own.number) if f)
    for child in children_idx.get((pred.line, pred.token), ()):
        if child.deprel in _AUX_DEPRELS:
            cm = morph_idx.get((child.line, child.token))
            if cm and cm.person:
                return " ".join(f for f in (cm.person, cm.number) if f)
    return ""


# --- Artifact I/O --------------------------------------------------------------------

_TSV_HEADER = ("line", "token", "word", "role", "arg_line", "arg_token")


def _artifact_path(canticle: str, number: int, base_dir: Path | None = None) -> Path:
    if base_dir is not None:
        return base_dir / canticle / f"{number:02d}.tsv"
    from .. import skel as _skel
    return _skel.SKEL_DIR / canticle / f"{number:02d}.tsv"


artifact_path = _artifact_path


def write_skel(canticle: str, number: int, lines: list[tuple[int, list[SkelRow]]]) -> Path:
    path = _artifact_path(canticle, number)
    path.parent.mkdir(parents=True, exist_ok=True)
    out = ["\t".join(_TSV_HEADER)]
    for no, rows in lines:
        if not rows:
            out.append("\t".join((str(no), "0", "", "", "0", "0")))
            continue
        for row in sorted(rows, key=_row_sort_key):
            out.append(
                "\t".join((str(no), str(row.token), row.word, row.role,
                           str(row.arg_line), str(row.arg_token)))
            )
    path.write_text("\n".join(out) + "\n", encoding="utf-8")
    return path


def has_skel(canticle: str, number: int, base_dir: Path | None = None) -> bool:
    return _artifact_path(canticle, number, base_dir).exists()


def load_skel(
    canticle: str, number: int, base_dir: Path | None = None
) -> dict[int, tuple[SkelRow, ...]]:
    """Load a frozen skeleton artifact: line-number -> SkelRows (no model call). A `token == 0`
    row is the sentinel (processed, no predicates) and is not returned as data.

    `base_dir` reads from an alternate root laid out like `SKEL_DIR` (e.g. a reconstruction
    run's output) instead of gold; the default reads gold as always.
    """
    path = _artifact_path(canticle, number, base_dir)
    if not path.exists():
        raise FileNotFoundError(path)
    grouped: dict[int, list[SkelRow]] = {}
    for lineno, text in enumerate(path.read_text(encoding="utf-8").splitlines()):
        if lineno == 0 or not text:  # header / blank
            continue
        cells = text.split("\t")
        cells += [""] * (len(_TSV_HEADER) - len(cells))  # tolerate dropped trailing blanks
        no = int(cells[0])
        token = int(cells[1])
        bucket = grouped.setdefault(no, [])
        if token == 0:  # sentinel: processed, no predicates
            continue
        bucket.append(
            SkelRow(line=no, token=token, word=cells[2], role=cells[3],
                    arg_line=int(cells[4]), arg_token=int(cells[5]))
        )
    return {no: tuple(rows) for no, rows in grouped.items()}


def tuples_canto(canticle: str, number: int) -> tuple[SkelTuple, ...]:
    """Serve a canto's skeleton as grouped, identified tuples, ordered by (line, token)."""
    data = load_skel(canticle, number)
    result: list[SkelTuple] = []
    for no in sorted(data):
        by_token: dict[int, list[SkelRow]] = {}
        for row in data[no]:
            by_token.setdefault(row.token, []).append(row)
        for i, token in enumerate(sorted(by_token), start=1):
            group = by_token[token]
            args = tuple(
                SkelArg(role=r.role, line=r.arg_line, token=r.arg_token)
                for r in sorted(group, key=_row_sort_key)
                if r.role
            )
            result.append(SkelTuple(line=no, token=token, word=group[0].word,
                                     skel_id=f"{no}.{i}", args=args))
    return tuple(result)
