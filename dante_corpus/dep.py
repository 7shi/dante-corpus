"""Layer 4 of the grammatical stack: dependency / grammatical role.

An LLM proposes, per *parse unit* (a sentence, or a sentence fragment for long sentences — see
`sentence_groups`), a Markdown table naming a Universal-Dependencies relation (`deprel`) and a
head token for every alpha token in the unit. Unlike Layers 2-3, which align free-text model
output to source substrings, this layer gives the model an authoritative *numbered* token list
(`line.token`) up front and has it cite indices back — a dependency row names two positions, and
free-text matching two words per row (against a source full of repeated `che`/`e`) would be far
more ambiguous than Layer 2/3's single-word alignment. `Word`/`Head Word` table cells are kept
only as build-time verification anchors; they are not stored in the frozen artifact.

Attachment may cross line boundaries (PLAN.md) — a subject on one line, its predicate on the
next — which is what rejoins Layer-3's single-line noun phrases across enjambment: an NP's
clause function is *derived* at serve time as the deprel of the Layer-4 row at
`(span.line, span.head)` (see `np_role`), not stored.

Relative-pronoun antecedents are likewise not stored: UD encodes them structurally (a relative
clause's verb attaches to its antecedent noun via `acl:relcl`; the pronoun gets its own role
inside the clause), so PLAN.md's "antecedent resolves to an in-scope NP" check becomes the soft
check that every `acl:relcl` head is a nominal Layer-2 POS.

Like `dante_corpus/np.py`, this stays free of `api` (which imports it) and depends only on
`tokenizer`/`_paths`/`morph` (the generic Markdown-table parser is reused from `morph`).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ._paths import DEP_DIR
from .morph import MorphRow, Violation, read_table, strip_word_punct
from .tokenizer import has_alpha, tokenize

# --- Table columns -----------------------------------------------------------------

# The model emits `| Line | Token | Word | Deprel | Head Line | Head Token | Head Word |`.
# `line`/`token` are the authoritative indices the model must cite; `word` and `head word` are
# verification anchors only (checked at build time, never stored).
_HEADER_ALIASES = {
    "line": "line",
    "token": "token",
    "word": "word",
    "deprel": "deprel",
    "relation": "deprel",
    "head line": "head_line",
    "head token": "head_token",
    "head word": "head_word",
}


def canon_header(header: str) -> str | None:
    return _HEADER_ALIASES.get(header.strip().lower())


# Frozen soft-check vocabulary (UD v2 universal relations plus the subtypes used by Italian UD
# treebanks; measure-then-freeze — see dep/README.md and PLAN.md). `punct`/`goeswith`/`clf`/
# `list`/`reparandum` are excluded: punctuation is never tokenized here. `dep` is kept as the
# generic escape hatch UD itself defines for a relation that resists closed-set classification.
# `attr` (non-UD, spaCy-style) is kept too: measured across the full 100-canto build it was the
# model's single dominant, systematic label for predicate-nominal/adjective complements of a
# copula (340 of 637 soft violations, an order of magnitude above any other off-vocabulary
# label) — frozen in as a one-time adjustment rather than left as permanent noise.
DEPRELS = frozenset({
    "acl", "acl:relcl", "advcl", "advmod", "amod", "appos", "attr",
    "aux", "aux:pass", "case", "cc", "ccomp", "compound", "conj", "cop",
    "csubj", "csubj:pass", "dep", "det", "det:poss", "det:predet",
    "discourse", "dislocated", "expl", "expl:impers", "expl:pass",
    "fixed", "flat", "flat:foreign", "flat:name", "iobj", "mark",
    "nmod", "nsubj", "nsubj:pass", "nummod", "obj", "obl", "obl:agent",
    "orphan", "parataxis", "root", "vocative", "xcomp",
})


def _is_nominal(pos: str) -> bool:
    p = pos.lower()
    return "noun" in p or "pronoun" in p


# --- DepRow --------------------------------------------------------------------------


@dataclass(frozen=True)
class DepRow:
    line: int
    token: int  # 1-based alpha-token index within `line` (matches Line.tokens / MorphRow order)
    word: str
    deprel: str
    head_line: int  # 0 together with head_token == 0 marks the sentence root
    head_token: int

    def to_dict(self) -> dict[str, object]:
        return {
            "line": self.line,
            "token": self.token,
            "word": self.word,
            "deprel": self.deprel,
            "head_line": self.head_line,
            "head_token": self.head_token,
        }


# --- Sentence splitting (parse units) -----------------------------------------------

# A dependency tree needs every head resolvable within its parse unit, so lines are grouped by
# sentence rather than sliced into fixed-size chunks (contrast morph/np). Measured over all 100
# cantos: sentence length (line-final `.`/`!`/`?`) is mode 3/6 lines, 99.7% <= 12; the remaining
# long sentences are sub-split at line-final `;`/`:` (with those included the corpus max is 12).
MAX_UNIT_LINES = 12

_TERMINAL = (".", "!", "?")
_SOFT_BREAK = (";", ":")


def _ends_with(text: str, chars: tuple[str, ...]) -> bool:
    return bool(text) and text[-1] in chars


def _split_long(group: list[int], texts: dict[int, str], max_lines: int) -> list[list[int]]:
    """Sub-split a too-long sentence at line-final `;`/`:`, as large as possible per piece."""
    if len(group) <= max_lines:
        return [group]
    out: list[list[int]] = []
    start = 0
    n = len(group)
    while n - start > max_lines:
        limit = start + max_lines
        split_at = None
        for i in range(start, limit):
            if _ends_with(texts[group[i]], _SOFT_BREAK):
                split_at = i
        if split_at is None:  # no soft break in range: fall back to a hard split
            split_at = limit - 1
        out.append(group[start : split_at + 1])
        start = split_at + 1
    out.append(group[start:])
    return out


def sentence_groups(
    nos: list[int], texts: list[str], max_lines: int = MAX_UNIT_LINES
) -> list[list[int]]:
    """Group line numbers into dependency parse units.

    A unit ends at a line whose *final character* is `.`/`!`/`?` (sentence-final punctuation in
    this edition follows a closing guillemet, e.g. `elegge!».` ends in `.`; a line ending in a
    bare `»`/`'` is an embedded quote transition and does not break). The final group is always
    flushed at end of input, even without terminal punctuation. Units longer than `max_lines`
    are sub-split at line-final `;`/`:` (see `_split_long`).
    """
    groups: list[list[int]] = []
    current: list[int] = []
    for no, text in zip(nos, texts):
        current.append(no)
        if _ends_with(text, _TERMINAL):
            groups.append(current)
            current = []
    if current:
        groups.append(current)

    text_by_no = dict(zip(nos, texts))
    result: list[list[int]] = []
    for group in groups:
        result.extend(_split_long(group, text_by_no, max_lines))
    return result


# --- Parsing / resolution ------------------------------------------------------------


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
) -> tuple[dict[int, list[DepRow]], list[str]]:
    """Parse a dependency table and resolve it into `DepRow`s keyed by line number.

    Returns (rows-by-line, head-word mismatch descriptions). Raises `ValueError` if no table can
    be parsed at all (mirrors `np.align_chunk`). Unlike Layer 2/3, resolution is index lookup,
    not substring search: `line`/`token` are taken as authoritative, and the `Head Word` cell is
    only cross-checked against the token actually found at `(head_line, head_token)` — a
    disagreement means the model mis-cited an index, reported here as a build-time warning that
    the driver treats as a hard violation (index citations must be trustworthy)."""
    table = read_table(table_text)
    if table is None:
        raise ValueError("no parseable dependency table found")
    keys = [canon_header(h) for h in table[0]]
    token_lists = {no: _alpha_tokens(t) for no, t in zip(nos, texts)}

    result: dict[int, list[DepRow]] = {no: [] for no in nos}
    mismatches: list[str] = []
    for raw in table[2:]:  # skip header + separator
        cells = dict(zip(keys, raw))
        line = _parse_int(cells.get("line"))
        token = _parse_int(cells.get("token"))
        word = (cells.get("word") or "").strip()
        deprel = (cells.get("deprel") or "").strip()
        head_line = _parse_int(cells.get("head_line")) or 0
        head_token = _parse_int(cells.get("head_token")) or 0
        head_word = (cells.get("head_word") or "").strip()
        if line is None or token is None or not word or not deprel or line not in result:
            continue
        result[line].append(
            DepRow(line=line, token=token, word=word, deprel=deprel,
                   head_line=head_line, head_token=head_token)
        )
        if head_line and head_token:
            head_tokens = token_lists.get(head_line)
            if head_tokens is not None and 1 <= head_token <= len(head_tokens):
                expected = head_tokens[head_token - 1]
                if head_word and not _words_match(head_word, expected):
                    mismatches.append(
                        f"{line}.{token} cites head {head_line}.{head_token} as {head_word!r}, "
                        f"actual {expected!r}"
                    )

    for rows in result.values():
        rows.sort(key=lambda r: r.token)
    return result, mismatches


# --- Validation ------------------------------------------------------------------------


def validate_unit(
    nos: list[int],
    texts: list[str],
    rows_by_line: dict[int, list[DepRow]],
    morph_rows: dict[int, list[MorphRow]] | None = None,
) -> list[Violation]:
    """Check `rows_by_line` for one parse unit against its deterministic tokens.

    Hard checks (structural bar; kinds `count`/`word`/`head`/`cycle`/`root`): each line has
    exactly one row per token, in order; each row's word matches its token (elision spelling
    tolerated via `morph.strip_word_punct`, as Layer 3 does); every head cites an in-unit
    `(line, token)` or is the `(0, 0)` root sentinel, consistently with `deprel == "root"`; no
    token is its own head; the head chain from every token reaches a root with no cycle; the
    unit has at least one root. Soft checks (kind `tag`): more than one root in a unit (expected
    for `;`/`:`-sub-split long sentences, see `sentence_groups`); `deprel` outside the frozen
    `DEPRELS` vocabulary; an `acl:relcl` relation whose head token is not a nominal Layer-2 POS
    (only checked when `morph_rows` is supplied, the Layer 2-aware policy PLAN.md calls for
    resolving relative-pronoun antecedents structurally rather than storing them).
    """
    violations: list[Violation] = []
    token_lists = {no: _alpha_tokens(t) for no, t in zip(nos, texts)}
    valid_positions = {(no, i + 1) for no in nos for i in range(len(token_lists[no]))}

    for no in nos:
        tokens = token_lists[no]
        rows = sorted(rows_by_line.get(no, []), key=lambda r: r.token)
        if [r.token for r in rows] != list(range(1, len(tokens) + 1)):
            violations.append(Violation(no, "count", f"{len(rows)} rows vs {len(tokens)} tokens"))
        for row in rows:
            if 1 <= row.token <= len(tokens):
                token = tokens[row.token - 1]
                if row.word != token and strip_word_punct(row.word, token) is None:
                    violations.append(Violation(no, "word", f"{row.word!r} != token {token!r}"))

    all_rows = [row for no in nos for row in rows_by_line.get(no, [])]
    index_map = {(row.line, row.token): row for row in all_rows}
    root_count = 0
    for row in all_rows:
        is_root_head = row.head_line == 0 and row.head_token == 0
        if is_root_head != (row.deprel == "root"):
            violations.append(
                Violation(row.line, "head",
                          f"token {row.token} head {row.head_line}.{row.head_token} "
                          f"inconsistent with deprel {row.deprel!r}")
            )
        if is_root_head:
            root_count += 1
            continue
        if (row.head_line, row.head_token) not in valid_positions:
            violations.append(
                Violation(row.line, "head",
                          f"token {row.token} head {row.head_line}.{row.head_token} not in unit")
            )
        elif (row.head_line, row.head_token) == (row.line, row.token):
            violations.append(Violation(row.line, "head", f"token {row.token} is its own head"))

    for row in all_rows:
        seen: set[tuple[int, int]] = set()
        cur: DepRow | None = row
        while cur is not None and not (cur.head_line == 0 and cur.head_token == 0):
            key = (cur.line, cur.token)
            if key in seen:
                violations.append(
                    Violation(row.line, "cycle", f"cycle detected from token {row.token}")
                )
                cur = None
                break
            seen.add(key)
            cur = index_map.get((cur.head_line, cur.head_token))

    if root_count == 0:
        violations.append(Violation(nos[0], "root", f"no root token in unit {nos[0]}-{nos[-1]}"))
    elif root_count > 1:
        violations.append(
            Violation(nos[0], "tag", f"{root_count} root tokens in unit {nos[0]}-{nos[-1]}")
        )

    for row in all_rows:
        if row.deprel not in DEPRELS:
            violations.append(Violation(row.line, "tag", f"deprel {row.deprel!r} not in frozen set"))
        if row.deprel == "acl:relcl" and morph_rows is not None:
            head_rows = morph_rows.get(row.head_line)
            if head_rows and 1 <= row.head_token <= len(head_rows):
                pos = head_rows[row.head_token - 1].pos
                if not _is_nominal(pos):
                    violations.append(
                        Violation(row.line, "tag",
                                  f"acl:relcl head {row.head_line}.{row.head_token} "
                                  f"is {pos!r}, not nominal")
                    )

    return violations


# --- Noun-phrase role join (serve-time; Layer 3 <-> Layer 4) ------------------------


def index(data: dict[int, tuple[DepRow, ...]]) -> dict[tuple[int, int], DepRow]:
    """Flatten a loaded canto's rows into a `(line, token) -> DepRow` lookup."""
    return {(row.line, row.token): row for rows in data.values() for row in rows}


def np_role(span: Any, idx: dict[tuple[int, int], DepRow]) -> str:
    """A Layer-3 NP's clause function: the deprel of the Layer-4 row at its head token.

    Derived, not stored — `span` need only expose `.line`/`.head` (an `np.NPSpan`). Returns ""
    when no Layer-4 artifact covers that token."""
    row = idx.get((span.line, span.head))
    return row.deprel if row else ""


# --- Artifact I/O --------------------------------------------------------------------

# Tab-separated: one row per alpha token. Rectangular and free of tabs/newlines, so plain TSV
# round-trips without quoting and keeps git diffs token-granular, exactly like Layer 2. No
# sentinel is needed (contrast Layer 3): every source line has >= 1 alpha token, so "rows
# present for this line" already means "processed".
_TSV_HEADER = ("line", "token", "word", "deprel", "head_line", "head_token")


def _artifact_path(canticle: str, number: int) -> Path:
    return DEP_DIR / canticle / f"{number:02d}.tsv"


def write_dep(canticle: str, number: int, lines: list[tuple[int, list[DepRow]]]) -> Path:
    path = _artifact_path(canticle, number)
    path.parent.mkdir(parents=True, exist_ok=True)
    out = ["\t".join(_TSV_HEADER)]
    for no, rows in lines:
        for row in sorted(rows, key=lambda r: r.token):
            out.append(
                "\t".join((str(no), str(row.token), row.word, row.deprel,
                           str(row.head_line), str(row.head_token)))
            )
    path.write_text("\n".join(out) + "\n", encoding="utf-8")
    return path


def has_dep(canticle: str, number: int) -> bool:
    return _artifact_path(canticle, number).exists()


def load_dep(canticle: str, number: int) -> dict[int, tuple[DepRow, ...]]:
    """Load a frozen dependency artifact: line-number -> DepRows (no model call)."""
    path = _artifact_path(canticle, number)
    if not path.exists():
        raise FileNotFoundError(path)
    grouped: dict[int, list[DepRow]] = {}
    for lineno, text in enumerate(path.read_text(encoding="utf-8").splitlines()):
        if lineno == 0 or not text:  # header / blank
            continue
        cells = text.split("\t")
        cells += [""] * (len(_TSV_HEADER) - len(cells))  # tolerate dropped trailing blanks
        no = int(cells[0])
        grouped.setdefault(no, []).append(
            DepRow(line=no, token=int(cells[1]), word=cells[2], deprel=cells[3],
                   head_line=int(cells[4]), head_token=int(cells[5]))
        )
    return {no: tuple(rows) for no, rows in grouped.items()}
