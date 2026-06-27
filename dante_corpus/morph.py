"""Layer 2 of the grammatical stack: per-token morphology + lemma.

A local LLM proposes a Markdown *word table* per chunk of source lines (structured
JSON-schema output is unreliable at local-LLM scale; see PLAN.md). This module parses,
normalizes, and **aligns** that table to the deterministic Layer-1 tokens
(`tokenizer.tokenize`) so that every token receives exactly one morphology row.

The table parsing (`read_table`/`fix_cell`) and the line-bucketing aligner (`split_table`)
are ports of the proven logic in the `dante-llm` project (`dantetool/common.py`), adapted to
operate on the corpus's own source lines. Nothing here is imported across repositories.

This module stays free of `api` (which imports it) and depends only on `tokenizer`/`_paths`.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, replace as dc_replace
from pathlib import Path

from ._paths import MORPH_DIR
from .tokenizer import has_alpha, tokenize

# --- Table columns -----------------------------------------------------------------

# Canonical column keys, in artifact order. `word` is the alignment anchor; the rest is
# the morphology proper.
COLUMNS = ("word", "lemma", "pos", "gender", "number", "person", "tense", "mood", "note")

_HEADER_ALIASES = {
    "word": "word",
    "lemma": "lemma",
    "part of speech": "pos",
    "pos": "pos",
    "gender": "gender",
    "number": "number",
    "person": "person",
    "tense": "tense",
    "mood": "mood",
    "note": "note",
}


def canon_header(header: str) -> str | None:
    """Map a raw table header cell to a canonical column key, or None to ignore it."""
    return _HEADER_ALIASES.get(header.strip().lower())


# --- Closed tag sets ---------------------------------------------------------------

# Structural features have small, stable vocabularies and are enforced. POS / tense / mood
# vary more across archaic forms; they are collected (measure-then-freeze) and reported by
# `validate_rows` rather than hard-failed. See PLAN.md "measure-then-freeze".
CLOSED_TAGS: dict[str, set[str]] = {
    "gender": {"m.", "f.", "n."},
    "number": {"sg.", "pl."},
    "person": {"1", "2", "3"},
}


# --- MorphRow ----------------------------------------------------------------------


@dataclass(frozen=True)
class MorphRow:
    word: str
    lemma: str = ""
    pos: str = ""
    gender: str = ""
    number: str = ""
    person: str = ""
    tense: str = ""
    mood: str = ""
    note: str = ""

    def to_dict(self) -> dict[str, str]:
        return {key: getattr(self, key) for key in COLUMNS}

    @classmethod
    def from_dict(cls, data: dict[str, str]) -> "MorphRow":
        return cls(**{key: data.get(key, "") for key in COLUMNS})


# --- Markdown table parsing (ported from dante-llm dantetool/common.py) -------------

_ABBREVS = {
    "number": {"singular": "sg.", "plural": "pl."},
    "gender": {"masculine": "m.", "feminine": "f.", "neuter": "n."},
    "person": {"first": "1", "1st": "1", "second": "2", "2nd": "2", "third": "3", "3rd": "3"},
}


def read_table(text: str) -> list[list[str]] | None:
    """Parse the first Markdown pipe-table in `text` into rows (header + separator + body).

    Tolerates column-count drift by padding/truncating blank trailing cells. Returns None
    if no well-formed table (>= 3 rows, valid separator) is found.
    """
    rows: list[list[str]] = []
    rowlen = 0
    for line in text.splitlines():
        if line.startswith("|"):
            row = [cell.strip() for cell in line.split("|")[1:-1]]
            if not rows:
                rowlen = len(row)
            elif rowlen != len(row):
                if rowlen > len(row):
                    row += [""] * (rowlen - len(row))
                elif all(cell == "" for cell in row[rowlen:]):
                    row = row[:rowlen]
                else:
                    return None
            rows.append(row)
        elif rows:
            break
    if len(rows) < 3:
        return None

    separator: list[str] = []
    for cell in rows[1]:
        if "---" in cell:
            separator.append(re.sub(r"-+", "---", cell))
        else:
            return None
    rows[1] = separator
    return rows


def fix_cell(column: str, cell: str) -> str:
    """Normalize a single body cell: blanks, abbreviations, stray markdown emphasis."""
    cell = cell.strip()
    if cell in ("-", "n/a", "N/A"):
        return ""
    abbrev = _ABBREVS.get(column, {}).get(cell.lower())
    if abbrev:
        return abbrev
    if m := re.fullmatch(r"([^*]+)\*", cell):
        return m.group(1).strip()
    if m := re.fullmatch(r"\*\*([^*]+)\*\*", cell):
        return m.group(1).strip()
    return cell


# --- Aligner (ported from dante-llm split_table) -----------------------------------


def split_table(
    line_texts: list[str],
    table: list[list[str]],
    *,
    info: str = "",
    events: list[str] | None = None,
) -> list[list[list[str]]]:
    """Bucket body rows of `table` to the source line each belongs to.

    `table` is the raw `read_table` output (header, separator, body). Returns a list parallel
    to `line_texts`, each holding the raw body rows assigned to that line. Uses anchor-substring
    matching of the Word column within the source line, with FIFO salvage on line transitions —
    a faithful port of dante-llm's aligner, tolerating LLM word transforms/hallucinations.
    """

    def log(event: str, **kw: object) -> None:
        if events is not None:
            parts = [info, event] + [f"{k}={v!r}" for k, v in kw.items() if v not in (None, "")]
            events.append(" | ".join(str(p) for p in parts))

    buckets: list[list[list[str]]] = [[] for _ in line_texts]

    rows: list[list[str]] = []
    for idx, row in enumerate(table[1:]):
        if idx == 0 and row and "---" in row[0]:
            continue
        if row and has_alpha(row[0]):
            rows.append(list(row))

    if len(line_texts) <= 1:
        if line_texts:
            buckets[0].extend(rows)
        return buckets

    last_ln = len(line_texts) - 1
    ln = 0
    start = 0
    pending: list[list[str]] = []
    a_holds = False

    for row_idx, row in enumerate(rows):
        word = row[0]
        i = line_texts[ln].find(word, start)
        found_in_next = False
        if i < 0 and ln + 1 < len(line_texts):
            i = line_texts[ln + 1].find(word, 0)
            if i >= 0:
                found_in_next = True

        if found_in_next:
            prev_ln = ln
            next_ln = ln + 1
            next_prefix = line_texts[next_ln][0:i]
            has_next_prefix_alpha = has_alpha(next_prefix)

            if a_holds:
                if pending and has_next_prefix_alpha:
                    salvaged = pending.pop()
                    buckets[next_ln].append(salvaged)
                    log("salvage_next", ln=next_ln, word=salvaged[0] if salvaged else None)
                if pending:
                    log("drop", ln=prev_ln, count=len(pending))
                    pending.clear()
            else:
                for p in pending:
                    buckets[prev_ln].append(p)
                if pending:
                    log("salvage_prev", ln=prev_ln, count=len(pending))
                    pending.clear()

            ln = next_ln
            start = 0
            a_holds = False

            if ln == last_ln:
                buckets[ln].extend(rows[row_idx:])
                break

        if i >= 0:
            if pending:
                for p in pending:
                    buckets[ln].append(p)
                log("salvage_inline", ln=ln, count=len(pending))
                pending.clear()
            buckets[ln].append(row)
            start = i + len(word)
            a_holds = not has_alpha(line_texts[ln][start:])
        else:
            pending.append(row)
            log("not_found", ln=ln, word=word)

    if pending:
        log("drop", ln=ln, count=len(pending))
    return buckets


# --- High-level: table text -> aligned MorphRows -----------------------------------


def _rows_to_morph(header: list[str], raw_rows: list[list[str]]) -> list[MorphRow]:
    keys = [canon_header(h) for h in header]
    morphs: list[MorphRow] = []
    for raw in raw_rows:
        data: dict[str, str] = {}
        for key, cell in zip(keys, raw):
            if key:
                data[key] = fix_cell(key, cell)
        if data.get("word"):
            morphs.append(MorphRow.from_dict(data))
    return morphs


def align_chunk(
    line_numbers: list[int],
    line_texts: list[str],
    table_text: str,
    *,
    events: list[str] | None = None,
) -> dict[int, list[MorphRow]]:
    """Parse a word table and align it to the given source lines.

    Returns a mapping line-number -> aligned MorphRows. Raises ValueError if the table cannot
    be parsed at all.
    """
    table = read_table(table_text)
    if table is None:
        raise ValueError("no parseable word table found")
    header = table[0]
    buckets = split_table(line_texts, table, info="", events=events)
    return {
        no: _rows_to_morph(header, raw_rows)
        for no, raw_rows in zip(line_numbers, buckets)
    }


# --- Validation --------------------------------------------------------------------


@dataclass(frozen=True)
class Violation:
    line: int
    kind: str
    detail: str


def validate_line(line_no: int, source_text: str, rows: list[MorphRow]) -> list[Violation]:
    """Check that `rows` align 1:1 to the deterministic tokens of `source_text`.

    Hard checks (structural bar): one row per token, in order, each row's word a verbatim
    token. Soft checks: closed-tag membership for gender/number/person (reported, not fatal —
    callers decide). Returns all violations found.
    """
    tokens = [t for t in tokenize(source_text) if has_alpha(t)]
    violations: list[Violation] = []
    if len(rows) != len(tokens):
        violations.append(
            Violation(line_no, "count", f"{len(rows)} rows vs {len(tokens)} tokens")
        )
    for row, token in zip(rows, tokens):
        if row.word != token:
            violations.append(Violation(line_no, "word", f"{row.word!r} != token {token!r}"))
    for row in rows:
        for column, allowed in CLOSED_TAGS.items():
            value = getattr(row, column)
            if value and value not in allowed:
                violations.append(
                    Violation(line_no, "tag", f"{column}={value!r} for {row.word!r}")
                )
    return violations


# --- Word auto-fix -----------------------------------------------------------------


def _strip_word_punct(word: str, token: str) -> str | None:
    """Attempt to reconcile `word` (LLM output) with `token` (deterministic).

    Handles three auto-fixable cases:
    - trailing non-alpha, non-apostrophe punct on word  (e.g. "sono," -> "sono")
    - trailing apostrophe missing from word             (e.g. "I"    -> "I'")
    - leading apostrophe missing from word              (e.g. "nvidia" -> "'nvidia")

    Returns the corrected word, or None if the mismatch is not auto-fixable.
    """
    if word == token:
        return word
    if word.startswith(token):
        suffix = word[len(token):]
        if suffix and not has_alpha(suffix) and "'" not in suffix:
            return token
    if token == word + "'":
        return token
    if token == "'" + word:
        return token
    if word == token + "'":
        return token
    if word == "'" + token:
        return token
    return None


def fix_aligned_words(
    nos: list[int],
    texts: list[str],
    aligned: dict[int, list[MorphRow]],
) -> tuple[dict[int, list[MorphRow]], list[str]]:
    """Auto-strip trailing punctuation from word fields after alignment.

    For each line where the row count matches the token count, attempts to fix any word
    mismatch by stripping safe trailing punctuation (non-alpha, non-apostrophe). Lines with
    count mismatches are left untouched (handled by validate_line). Returns the (possibly
    modified) aligned dict and a list of error strings for unfixable word mismatches.
    """
    result: dict[int, list[MorphRow]] = {}
    errors: list[str] = []
    for no, text in zip(nos, texts):
        tokens = [t for t in tokenize(text) if has_alpha(t)]
        rows = list(aligned.get(no, []))
        if len(rows) != len(tokens):
            result[no] = rows
            continue
        fixed: list[MorphRow] = []
        for row, token in zip(rows, tokens):
            stripped = _strip_word_punct(row.word, token)
            if stripped is None:
                errors.append(f"line {no}: {row.word!r} != {token!r}")
                fixed.append(row)
            elif stripped != row.word:
                fixed.append(dc_replace(row, word=stripped))
            else:
                fixed.append(row)
        result[no] = fixed
    return result, errors


# --- Artifact I/O ------------------------------------------------------------------


# The artifact is a tab-separated table: a `line` column plus the nine `COLUMNS`, one row
# per token. The data is fully rectangular and contains no tabs or newlines, so plain TSV
# round-trips without quoting and keeps git diffs token-granular (see PLAN.md).
_TSV_HEADER = ("line", *COLUMNS)


def _artifact_path(canticle: str, number: int) -> Path:
    return MORPH_DIR / canticle / f"{number:02d}.tsv"


def write_morph(canticle: str, number: int, lines: list[tuple[int, list[MorphRow]]]) -> Path:
    path = _artifact_path(canticle, number)
    path.parent.mkdir(parents=True, exist_ok=True)
    out = ["\t".join(_TSV_HEADER)]
    for no, rows in lines:
        for row in rows:
            out.append("\t".join((str(no), *(getattr(row, key) for key in COLUMNS))))
    path.write_text("\n".join(out) + "\n", encoding="utf-8")
    return path


def has_morph(canticle: str, number: int) -> bool:
    return _artifact_path(canticle, number).exists()


def load_morph(canticle: str, number: int) -> dict[int, tuple[MorphRow, ...]]:
    """Load a frozen morphology artifact: line-number -> MorphRows. No model call."""
    path = _artifact_path(canticle, number)
    if not path.exists():
        raise FileNotFoundError(path)
    grouped: dict[int, list[MorphRow]] = {}
    for lineno, text in enumerate(path.read_text(encoding="utf-8").splitlines()):
        if lineno == 0 or not text:  # header / blank
            continue
        cells = text.split("\t")
        cells += [""] * (len(_TSV_HEADER) - len(cells))  # tolerate dropped trailing blanks
        no = int(cells[0])
        data = dict(zip(COLUMNS, cells[1:]))
        grouped.setdefault(no, []).append(MorphRow.from_dict(data))
    return {no: tuple(rows) for no, rows in grouped.items()}
