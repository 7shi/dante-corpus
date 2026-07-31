"""Pronoun case — a Layer-2 annex held in its own directory (`case/`).

Case is the one morphological feature Layer 2 omits, and the one Layer 5's parked clitic
verdicts named: `mi pesa` (dative) and `m'avea 'mmonito` (accusative) are identical in form,
and neither the token stream, the existing morphology, nor the dependency tree distinguishes
them — the tree shape is the same and the deprel *is* the disputed judgment. See
`case/PLAN.md` for why this lives in a sibling directory rather than as a `morph/*.tsv`
column (hash blast radius, visible provenance, revertibility).

The artifact is **sparse**: one row per pronoun-POS token, not per token. Which tokens those
are is decided mechanically by Layer 2's own `pos` column (`scope_slots`), so the scope needs
no hand-frozen list of word forms and no external authority — the same terms `pos` and
`deprel` are already authored on.

Like `morph.py` this module stays free of `api` and depends only on `morph`/`tokenizer`/
`_paths`; the build driver that calls a model is `case/case.py`.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ._paths import CASE_DIR
from .morph import MorphRow, Violation, read_table
from .tokenizer import has_alpha, tokenize

# --- Closed vocabulary -------------------------------------------------------------

# Frozen from the pilot's own answer census (570 calls, `google:gemma-4-31b-it`,
# 2026-07-30) rather than from a grammar book — the same measure-then-freeze order every
# other layer used. See `case/CORRECTIONS.md`: accusative 276, dative 252, ablative 28,
# nominative 7, genitive 5, locative 2, with no unmapped values. `ablative` is the model's
# own word for the partitive/locative oblique class (`ne`, `ci`/`vi`); `case/PLAN.md`
# anticipated `oblique`, and the census overruled it.
#
# Two values are **not** in that census and were added deliberately, both for the same
# structural reason — the pilot sampled only disputed and control *clitic argument*
# positions, so a pronoun that fills no argument slot could not appear in it at all:
#
# - `vocative`: direct address (`O tu che ...`), pervasive in the poem once the scope is
#   every pronoun rather than the clitic subset.
# - `reflexive`: the clitic that refers back to the subject or belongs to the verb itself
#   (`mi volsi`, `si mosse`, impersonal/passive `si`). 1411 of the 13113 in-scope tokens
#   (10.8%) are tagged `expl` by Layer 4, and the inferno-1 smoke test split them
#   accusative 6 / nominative 2 — an unstable answer to a question the vocabulary gave no
#   home. The name is the corpus's own: Layer 2's `note` column already reads `reflexive`
#   on 1271 pronoun tokens (plus `impersonal` on 174).
CASES = ("nominative", "accusative", "dative", "genitive", "ablative", "locative",
         "vocative", "reflexive")

# A token that is *entirely* one pronoun carries one case; a fused token carries one per
# pronoun component (`gliel'` = `pronoun+pronoun`), joined the way Layer 2 already joins the
# lemmas of a contraction (`Nel` -> `in+il`).
SLOT_SEP = "+"

_CASE_ALIASES = {
    "acc": "accusative",
    "accusativo": "accusative",
    "dat": "dative",
    "dativo": "dative",
    "nom": "nominative",
    "nominativo": "nominative",
    "gen": "genitive",
    "genitivo": "genitive",
    "abl": "ablative",
    "ablativo": "ablative",
    "loc": "locative",
    "locativo": "locative",
    "voc": "vocative",
    "vocativo": "vocative",
    "refl": "reflexive",
    "riflessivo": "reflexive",
    "expletive": "reflexive",
    "impersonal": "reflexive",
    "reciprocal": "reflexive",
    # The pilot's own boundary wobble: the partitive/locative class was answered as
    # `ablative` far more often than anything else, so the near-synonyms map onto it.
    # `instrumental` is a *rejected value*, not an unmeasured one: the pilot produced it
    # zero times out of 570 in positions that could have yielded it, and Italian inherits
    # no instrumental form (Latin merged it into the ablative). The archaic comitative
    # forms `meco`/`teco`/`seco` are ablative. Kept here only to absorb model drift.
    "oblique": "ablative",
    "partitive": "ablative",
    "comitative": "ablative",
    "instrumental": "ablative",
}


def canon_case(value: str) -> str:
    """Normalize one case cell to the closed vocabulary; unknown values pass through so
    `validate_line` can report them rather than silently absorbing model drift."""
    cell = value.strip().strip("*").strip().lower().rstrip(".")
    return _CASE_ALIASES.get(cell, cell)


def canon_cell(value: str) -> str:
    """Normalize a whole `case` cell, which may hold one value per pronoun slot."""
    parts = [canon_case(p) for p in value.split(SLOT_SEP)]
    return SLOT_SEP.join(p for p in parts if p)


# --- Scope -------------------------------------------------------------------------


def scope_slots(pos: str) -> int:
    """How many case values a token with this Layer-2 `pos` carries — 0 if out of scope.

    Scope is every pronoun-POS token, read off Layer 2's own column: `pronoun`,
    `relative pronoun`, and the fused tokens whose `pos` names a pronoun among its parts
    (`verb+pronoun` for an enclitic, `pronoun+pronoun` for a clitic cluster). Counting the
    parts is what makes the fused cases checkable instead of ambiguous.
    """
    parts = [p.strip() for p in pos.replace(" + ", "+").split(SLOT_SEP)]
    return sum(1 for p in parts if p.lower().endswith("pronoun"))


@dataclass(frozen=True)
class Target:
    """One in-scope position: where it is, what the word is, how many cases it needs."""

    line: int
    token: int  # 1-based over the alpha-only tokens of the line (Layer-1 numbering)
    word: str
    slots: int


def targets(line_no: int, rows: list[MorphRow] | tuple[MorphRow, ...]) -> list[Target]:
    """The in-scope positions of one line, in token order, from its frozen morphology.

    Rows are 1:1 with the line's alpha tokens (Layer 2's own hard check), so the row index
    is the token index.
    """
    out: list[Target] = []
    for index, row in enumerate(rows, start=1):
        slots = scope_slots(row.pos)
        if slots:
            out.append(Target(line_no, index, row.word, slots))
    return out


def unit_targets(
    nos: list[int], morph_rows: dict[int, tuple[MorphRow, ...]]
) -> list[Target]:
    """Every in-scope position of a parse unit, in reading order."""
    out: list[Target] = []
    for no in nos:
        out.extend(targets(no, list(morph_rows.get(no, ()))))
    return out


# --- CaseRow -----------------------------------------------------------------------

COLUMNS = ("line", "token", "word", "case")


@dataclass(frozen=True)
class CaseRow:
    line: int
    token: int
    word: str
    case: str

    def cases(self) -> tuple[str, ...]:
        return tuple(p for p in self.case.split(SLOT_SEP) if p)

    def to_dict(self) -> dict[str, object]:
        return {"line": self.line, "token": self.token, "word": self.word, "case": self.case}


# --- Table parsing / alignment -----------------------------------------------------

_HEADER_ALIASES = {
    "line": "line",
    "no": "line",
    "word": "word",
    "pronoun": "word",
    "case": "case",
    "grammatical case": "case",
}


def canon_header(header: str) -> str | None:
    return _HEADER_ALIASES.get(header.strip().lower())


def _match(word: str, token: str) -> bool:
    """Whether an LLM `Word` cell names the same token, tolerating the emphasis and the
    trailing punctuation the model copies along with it.

    A fused token is also matched by the **clitic it ends in**: asked for the case of the
    pronoun in `parlami` or `vedervi`, the model often answers with a `Word` of `mi` / `vi`,
    which is the part the question is actually about. Reading that as the position it names
    is safe because alignment is a forward walk — a row consumed by the wrong position
    leaves a later one empty, which `validate_line` reports rather than absorbs.
    """
    left = word.strip().strip("*").strip()
    if left == token:
        return True
    right = token.strip()
    left, right = left.rstrip(".,;:!?»«\"").lower(), right.rstrip(".,;:!?»«\"").lower()
    if left == right:
        return True
    return len(left) < len(right) and right.endswith(left) and len(left) >= 2


def align_unit(expected: list[Target], table_text: str) -> list[CaseRow]:
    """Align a `| Line | Word | Case |` table to the unit's in-scope positions.

    Unlike Layer 2's aligner, the expected sequence is already known exactly, so alignment
    is a forward walk: each expected position consumes the next table row whose Word names
    it, and rows that name nothing expected are dropped. A position no row reaches gets an
    empty case, which `validate_line` reports as a hard violation — so a truncated table
    fails loudly and the chunk is re-requested rather than frozen half-filled.

    Raises ValueError if no table can be parsed at all.
    """
    table = read_table(table_text)
    if table is None:
        raise ValueError("no parseable case table found")
    keys = [canon_header(cell) for cell in table[0]]
    if "word" not in keys or "case" not in keys:
        raise ValueError(f"case table lacks Word/Case columns: {table[0]}")

    body: list[dict[str, str]] = []
    for raw in table[2:]:
        cells = {key: raw[i] for i, key in enumerate(keys) if key and i < len(raw)}
        if cells.get("word", "").strip():
            body.append(cells)

    out: list[CaseRow] = []
    cursor = 0
    for target in expected:
        found = None
        for offset in range(cursor, len(body)):
            if _match(body[offset].get("word", ""), target.word):
                found = offset
                break
        if found is None:
            out.append(CaseRow(target.line, target.token, target.word, ""))
            continue
        cursor = found + 1
        out.append(
            CaseRow(target.line, target.token, target.word,
                    canon_cell(body[found].get("case", "")))
        )
    return out


# --- Validation --------------------------------------------------------------------


def validate_line(
    line_no: int,
    source_text: str,
    morph_rows: list[MorphRow] | tuple[MorphRow, ...],
    rows: list[CaseRow] | tuple[CaseRow, ...],
) -> list[Violation]:
    """Check one line's case rows against Layer 1's tokens and Layer 2's `pos`.

    There is no deterministic ground truth for case (`case/PLAN.md`, *There is no
    deterministic checker for case*), so every check here is formal:

    - `count` — exactly one row per in-scope token, in token order, and none anywhere else;
    - `word`  — the row's word is the verbatim Layer-1 token at its index;
    - `slot`  — one case value per pronoun component of the Layer-2 `pos`;
    - `tag`   — every value is in the closed vocabulary, and non-empty.
    """
    tokens = [t for t in tokenize(source_text) if has_alpha(t)]
    expected = targets(line_no, list(morph_rows))
    violations: list[Violation] = []

    if len(rows) != len(expected):
        violations.append(
            Violation(line_no, "count",
                      f"{len(rows)} rows vs {len(expected)} pronoun token(s)")
        )
    by_token = {t.token: t for t in expected}
    seen: set[int] = set()
    for row in rows:
        if row.token in seen:
            violations.append(Violation(line_no, "count", f"token {row.token} listed twice"))
        seen.add(row.token)
        target = by_token.get(row.token)
        if target is None:
            violations.append(
                Violation(line_no, "count",
                          f"token {row.token} ({row.word!r}) is not a pronoun-POS token")
            )
            continue
        if not (1 <= row.token <= len(tokens)) or row.word != tokens[row.token - 1]:
            actual = tokens[row.token - 1] if 1 <= row.token <= len(tokens) else None
            violations.append(
                Violation(line_no, "word", f"{row.word!r} != token {row.token} {actual!r}")
            )
        values = row.cases()
        if len(values) != target.slots:
            violations.append(
                Violation(line_no, "slot",
                          f"{row.word!r} has {len(values)} case(s) for {target.slots} "
                          f"pronoun slot(s): {row.case!r}")
            )
        for value in values:
            if value not in CASES:
                violations.append(
                    Violation(line_no, "tag", f"case={value!r} for {row.word!r}")
                )
        if not values:
            violations.append(Violation(line_no, "tag", f"empty case for {row.word!r}"))
    if list(rows) != sorted(rows, key=lambda r: r.token):
        violations.append(Violation(line_no, "count", "rows are not in token order"))
    return violations


# --- Artifact I/O ------------------------------------------------------------------

_TSV_HEADER = COLUMNS


def _artifact_path(canticle: str, number: int) -> Path:
    return CASE_DIR / canticle / f"{number:02d}.tsv"


artifact_path = _artifact_path


def write_case(canticle: str, number: int, lines: list[tuple[int, list[CaseRow]]]) -> Path:
    path = _artifact_path(canticle, number)
    path.parent.mkdir(parents=True, exist_ok=True)
    out = ["\t".join(_TSV_HEADER)]
    for no, rows in lines:
        for row in rows:
            out.append("\t".join((str(no), str(row.token), row.word, row.case)))
    path.write_text("\n".join(out) + "\n", encoding="utf-8")
    return path


def has_case(canticle: str, number: int) -> bool:
    return _artifact_path(canticle, number).exists()


def load_case(canticle: str, number: int) -> dict[int, tuple[CaseRow, ...]]:
    """Load a frozen case artifact: line-number -> CaseRows (no model call).

    The artifact is sparse — a line with no pronoun has no rows and so no key.
    """
    path = _artifact_path(canticle, number)
    if not path.exists():
        raise FileNotFoundError(path)
    grouped: dict[int, list[CaseRow]] = {}
    for lineno, text in enumerate(path.read_text(encoding="utf-8").splitlines()):
        if lineno == 0 or not text:  # header / blank
            continue
        cells = text.split("\t")
        cells += [""] * (len(_TSV_HEADER) - len(cells))
        no = int(cells[0])
        grouped.setdefault(no, []).append(
            CaseRow(no, int(cells[1]), cells[2], cells[3])
        )
    return {no: tuple(rows) for no, rows in grouped.items()}


def case_index(data: dict[int, tuple[CaseRow, ...]]) -> dict[tuple[int, int], str]:
    """(line, token) -> case, the serve-time shape Layer 5's checker consumes as a third
    read (`skel._classify_divergence` already takes a `morph_pos_by_position` of this shape).

    Layer 5 is a **consumer** of this column, never its owner: the adjudication report
    itself belongs to `case/case.py --stats`.
    """
    return {(row.line, row.token): row.case for rows in data.values() for row in rows}
