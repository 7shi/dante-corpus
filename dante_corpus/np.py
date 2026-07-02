"""Layer 3 of the grammatical stack: noun-phrase enumeration.

An LLM proposes, per chunk of source lines, a Markdown table listing *every* noun phrase —
exhaustively and over-inclusively, including nested NPs (PLAN.md). This module parses that
table and **aligns** each NP to the deterministic Layer-1 tokens (`tokenizer.tokenize`): an
NP is a contiguous run of tokens, recorded as 1-based `start`/`end` indices plus a `head`
token index and the verbatim source `text` it spans. Nesting (parent/children) is *derived*
deterministically by span containment at serve time, exactly as the quote tree is built in
`api.py` — it is not stored.

Like `dante_corpus/morph.py`, this stays free of `api` (which imports it) and depends only on
`tokenizer`/`_paths`/`morph` (the generic Markdown-table parser is reused from `morph`).
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace as dc_replace
from pathlib import Path

from ._paths import NP_DIR
from .morph import Violation, read_table
from .tokenizer import has_alpha, tokenize

# --- Table columns -----------------------------------------------------------------

# The model emits `| Line | Noun Phrase | Head |`. `text` is the NP surface (alignment
# anchor); `head` is one word of the phrase; `line` attributes the row to a source line.
_HEADER_ALIASES = {
    "line": "line",
    "noun phrase": "text",
    "phrase": "text",
    "np": "text",
    "head": "head",
}


def canon_header(header: str) -> str | None:
    return _HEADER_ALIASES.get(header.strip().lower())


# A head token is expected to be nominal. Soft check only (measure-then-freeze): any POS whose
# label contains "noun" or "pronoun" (noun, proper noun, pronoun, relative pronoun, …).
def _is_nominal(pos: str) -> bool:
    p = pos.lower()
    return "noun" in p or "pronoun" in p


# --- NPSpan ------------------------------------------------------------------------


@dataclass(frozen=True)
class NPSpan:
    line: int
    start: int  # 1-based token index of first token (inclusive)
    end: int  # 1-based token index of last token (inclusive)
    head: int  # 1-based token index of the head (start <= head <= end)
    text: str  # verbatim source substring spanning [start, end]
    np_id: str = ""  # derived at serve time: f"{line}.{ordinal}"
    children: tuple["NPSpan", ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, object]:
        data: dict[str, object] = {
            "id": self.np_id,
            "line": self.line,
            "start": self.start,
            "end": self.end,
            "head": self.head,
            "text": self.text,
        }
        if self.children:
            data["children"] = [child.to_dict() for child in self.children]
        return data


# --- Token offsets -----------------------------------------------------------------


def token_spans(text: str) -> list[tuple[str, int, int]]:
    """Attach char offsets to each Layer-1 (alpha) token: (token, start_char, end_char).

    Re-scans `text` token by token with an advancing cursor (the same advance idiom as
    morph's aligner), so repeated tokens map to distinct, in-order offsets. Non-alpha tokens
    are skipped but still advance the cursor.
    """
    spans: list[tuple[str, int, int]] = []
    cursor = 0
    for tok in tokenize(text):
        i = text.find(tok, cursor)
        if i < 0:
            i = text.find(tok, 0)
        end = i + len(tok)
        cursor = end
        if has_alpha(tok):
            spans.append((tok, i, end))
    return spans


# --- Alignment ---------------------------------------------------------------------


def _alpha_tokens(text: str) -> list[str]:
    return [t for t in tokenize(text) if has_alpha(t)]


def _find_run(tokens: list[str], needle: list[str]) -> int:
    """Index of the first contiguous occurrence of `needle` within `tokens`, or -1."""
    if not needle:
        return -1
    last = len(tokens) - len(needle)
    for i in range(last + 1):
        if tokens[i : i + len(needle)] == needle:
            return i
    return -1


def _align_row(
    line_numbers: list[int],
    token_lists: list[list[str]],
    span_lists: list[list[tuple[str, int, int]]],
    line_texts: list[str],
    labelled_line: int | None,
    np_text: str,
    head_text: str,
) -> tuple[int, NPSpan] | None:
    """Align one NP table row to a (line, NPSpan). Returns None if no contiguous run is found."""
    needle = _alpha_tokens(np_text)
    if not needle:
        return None
    # Try the labelled line first, then salvage by scanning the other chunk lines.
    order = list(range(len(line_numbers)))
    if labelled_line in line_numbers:
        idx = line_numbers.index(labelled_line)
        order = [idx] + [i for i in order if i != idx]
    for li in order:
        run = _find_run(token_lists[li], needle)
        if run < 0:
            continue
        start = run + 1
        end = run + len(needle)
        spans = span_lists[li]
        text = line_texts[li][spans[run][1] : spans[end - 1][2]]
        head = _head_index(token_lists[li], head_text, start, end)
        return line_numbers[li], NPSpan(
            line=line_numbers[li], start=start, end=end, head=head, text=text
        )
    return None


def _head_index(tokens: list[str], head_text: str, start: int, end: int) -> int:
    """1-based token index of the head within [start, end]; defaults to `end` if not found."""
    head_tokens = _alpha_tokens(head_text)
    if head_tokens:
        word = head_tokens[0]
        for i in range(start - 1, end):
            if tokens[i] == word:
                return i + 1
    return end


def align_chunk(
    line_numbers: list[int],
    line_texts: list[str],
    table_text: str,
) -> tuple[dict[int, list[NPSpan]], int]:
    """Parse an NP table and align its rows to the given source lines.

    Returns (mapping line-number -> aligned NPSpans, count of unalignable rows). Raises
    ValueError if the table cannot be parsed at all. Every requested line gets an entry (an
    empty list if it has no NPs).
    """
    table = read_table(table_text)
    if table is None:
        raise ValueError("no parseable noun-phrase table found")
    keys = [canon_header(h) for h in table[0]]
    token_lists = [_alpha_tokens(t) for t in line_texts]
    span_lists = [token_spans(t) for t in line_texts]

    result: dict[int, list[NPSpan]] = {no: [] for no in line_numbers}
    unaligned = 0
    for raw in table[2:]:  # skip header + separator
        cells = dict(zip(keys, raw))
        np_text = (cells.get("text") or "").strip()
        if not np_text:
            continue
        head_text = (cells.get("head") or "").strip()
        labelled = _parse_int(cells.get("line"))
        aligned = _align_row(
            line_numbers, token_lists, span_lists, line_texts, labelled, np_text, head_text
        )
        if aligned is None:
            unaligned += 1
            continue
        no, span = aligned
        result[no].append(span)
    return result, unaligned


def _parse_int(value: str | None) -> int | None:
    if not value:
        return None
    digits = "".join(ch for ch in value if ch.isdigit())
    return int(digits) if digits else None


# --- Validation --------------------------------------------------------------------


def validate_line(
    line_no: int,
    source_text: str,
    spans: list[NPSpan],
    morph_rows: list | None = None,
) -> list[Violation]:
    """Check that `spans` are well-formed against the deterministic tokens of `source_text`.

    Hard checks (structural bar): each NP's token range is in-bounds and ordered; the head lies
    within the range; `text` is the verbatim source substring of that range. Soft checks (only
    when `morph_rows` — the Layer-2 row per token — is supplied): the head token is nominal, and
    every nominal token is the head of at least one NP (coverage). Soft violations use kind
    "tag"; hard ones use "range"/"head"/"word".
    """
    tokens = _alpha_tokens(source_text)
    tspans = token_spans(source_text)
    n = len(tokens)
    violations: list[Violation] = []
    for span in spans:
        if not (1 <= span.start <= span.end <= n):
            violations.append(
                Violation(line_no, "range", f"[{span.start},{span.end}] vs {n} tokens for {span.text!r}")
            )
            continue
        if not (span.start <= span.head <= span.end):
            violations.append(
                Violation(line_no, "head", f"head {span.head} outside [{span.start},{span.end}]")
            )
        expected = source_text[tspans[span.start - 1][1] : tspans[span.end - 1][2]]
        if span.text != expected:
            violations.append(
                Violation(line_no, "word", f"{span.text!r} != source {expected!r}")
            )

    if morph_rows is not None and len(morph_rows) == n:
        for span in spans:
            if 1 <= span.head <= n and not _is_nominal(morph_rows[span.head - 1].pos):
                pos = morph_rows[span.head - 1].pos
                violations.append(
                    Violation(line_no, "tag", f"head {tokens[span.head - 1]!r} is {pos!r}, not nominal")
                )
        heads = {span.head for span in spans}
        for i, row in enumerate(morph_rows, start=1):
            if _is_nominal(row.pos) and i not in heads:
                violations.append(
                    Violation(line_no, "tag", f"nominal {tokens[i - 1]!r} (token {i}) heads no NP")
                )
    return violations


# --- Nesting (derived at serve time) -----------------------------------------------


def _contains(a: NPSpan, b: NPSpan) -> bool:
    return a.start <= b.start and b.end <= a.end and (a.start, a.end) != (b.start, b.end)


def nest(spans: list[NPSpan]) -> tuple[NPSpan, ...]:
    """Derive the parent/children forest of one line's NPs by span containment.

    Siblings are ordered by (start asc, end desc); the smallest enclosing span is the parent.
    Returns the top-level spans, each with `children` populated. Pure function of the spans —
    the analogue of building the quote tree in `api.py`.
    """
    ordered = sorted(spans, key=lambda s: (s.start, -s.end))
    children_map: dict[int, list[NPSpan]] = {id(s): [] for s in ordered}
    stack: list[NPSpan] = []
    roots: list[NPSpan] = []
    for s in ordered:
        while stack and not _contains(stack[-1], s):
            stack.pop()
        (children_map[id(stack[-1])] if stack else roots).append(s)
        stack.append(s)

    def build(s: NPSpan) -> NPSpan:
        return dc_replace(s, children=tuple(build(c) for c in children_map[id(s)]))

    return tuple(build(r) for r in roots)


def nest_canto(canticle: str, number: int) -> tuple[NPSpan, ...]:
    """Serve a canto's NPs as a nested forest with stable ids, ordered by (line, start, -end)."""
    data = load_np(canticle, number)
    roots: list[NPSpan] = []
    for no in sorted(data):
        spans = sorted(data[no], key=lambda s: (s.start, -s.end))
        identified = [dc_replace(s, np_id=f"{no}.{i}") for i, s in enumerate(spans, start=1)]
        roots.extend(nest(identified))
    return tuple(roots)


# --- Artifact I/O ------------------------------------------------------------------


# Tab-separated: a `line` column plus token-index span columns and the verbatim `text`. A
# processed line with no NPs is stored as a single sentinel row with start==0 (see load_np),
# so resumption can tell "no NPs here" from "not yet processed". See PLAN.md.
_TSV_HEADER = ("line", "start", "end", "head", "text")


def _artifact_path(canticle: str, number: int) -> Path:
    return NP_DIR / canticle / f"{number:02d}.tsv"


def write_np(canticle: str, number: int, lines: list[tuple[int, list[NPSpan]]]) -> Path:
    path = _artifact_path(canticle, number)
    path.parent.mkdir(parents=True, exist_ok=True)
    out = ["\t".join(_TSV_HEADER)]
    for no, spans in lines:
        if not spans:
            out.append("\t".join((str(no), "0", "0", "0", "")))
            continue
        for span in sorted(spans, key=lambda s: (s.start, -s.end)):
            out.append("\t".join((str(no), str(span.start), str(span.end), str(span.head), span.text)))
    path.write_text("\n".join(out) + "\n", encoding="utf-8")
    return path


def has_np(canticle: str, number: int) -> bool:
    return _artifact_path(canticle, number).exists()


def load_np(canticle: str, number: int) -> dict[int, tuple[NPSpan, ...]]:
    """Load a frozen NP artifact: line-number -> NPSpans (no model call). start==0 is the
    zero-NP sentinel: the line is present with an empty tuple."""
    path = _artifact_path(canticle, number)
    if not path.exists():
        raise FileNotFoundError(path)
    grouped: dict[int, list[NPSpan]] = {}
    for lineno, text in enumerate(path.read_text(encoding="utf-8").splitlines()):
        if lineno == 0 or not text:  # header / blank
            continue
        cells = text.split("\t")
        cells += [""] * (len(_TSV_HEADER) - len(cells))  # tolerate dropped trailing blanks
        no = int(cells[0])
        start = int(cells[1])
        bucket = grouped.setdefault(no, [])
        if start == 0:  # sentinel: processed, no NPs
            continue
        bucket.append(
            NPSpan(line=no, start=start, end=int(cells[2]), head=int(cells[3]), text=cells[4])
        )
    return {no: tuple(spans) for no, spans in grouped.items()}
