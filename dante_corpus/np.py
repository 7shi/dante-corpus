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
from .morph import MorphRow, Violation, read_table, strip_word_punct
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


# Frozen soft-check policy (measured 2026-07-03 over all 100 cantos; see np/README.md *Check*
# and PLAN.md *Layer 3 check status*):
#
# - Coverage ("heads no NP") applies to nouns/proper nouns only. Bare clitic and relative
#   pronouns were ~96% of the raw coverage misses (`che`, `si`, `mi`, …) and are not noun
#   phrases — Layer 5 admits arguments that are "Layer-3 NPs or Layer-1 pronoun tokens" — so a
#   pronoun heading no NP is by policy not a Layer-3 gap.
# - A noun/proper-noun token whose Layer-2 `note` carries the `NO_NP` flag (comma-separated,
#   alongside other notes like `apocope`) is also exempt from coverage: Layer 2 tags its part
#   of speech correctly, but the token only ever occurs as part of a fixed idiom (`fin che`,
#   `'nver'`, `allotta`, …) and never heads a genuine noun phrase — see morph/CORRECTIONS.md.
# - A noun token whose Layer-2 `note` carries the `CONT_NEXT` flag is exempt from coverage for a
#   different structural reason: it is one half of a single word split by an enjambed line break
#   (e.g. `dia` / `regïon`), so it can never head a same-line NP — Layer 3 spans are single-line
#   by design (see PLAN.md's Layer 3 *Scope* note) — see morph/CORRECTIONS.md.
# - A head may be any content POS: nominal, or adjective/verb/adverb/numeral — Dante
#   substantivizes all of these (`'l più basso`, `lo sperar`, `un poco`, `l'un de' canti`).
#   Function-word heads (article, conjunction, preposition, …) stay flagged: they are either
#   alignment slips or Layer-2 mistags (most are `che` tagged `conjunction` where the model
#   correctly read a relative pronoun).
def _is_nominal(pos: str) -> bool:
    p = pos.lower()
    return "noun" in p or "pronoun" in p


_CONTENT_POS = ("adjective", "verb", "adverb", "numeral")


def _can_head_np(pos: str) -> bool:
    p = pos.lower()
    return _is_nominal(p) or any(c in p for c in _CONTENT_POS)


def _needs_np(pos: str, note: str = "") -> bool:
    p = pos.lower()
    if not ("noun" in p and "pronoun" not in p):
        return False
    flags = {f.strip() for f in note.split(",")}
    return not flags & {"NO_NP", "CONT_NEXT"}


def non_content_tokens(text: str, morph_rows: list[MorphRow]) -> list[tuple[str, str]]:
    """(word, pos) pairs for `text`'s tokens whose Layer-2 POS can never head an NP.

    Used to warn the Layer-3 generation prompt away from picking a function-word token as a
    phrase's head (`_can_head_np`), rather than only catching it after the fact in
    `validate_line`.
    """
    tokens = _alpha_tokens(text)
    if len(tokens) != len(morph_rows):
        return []
    return [(tokens[i], morph_rows[i].pos)
            for i in range(len(tokens)) if not _can_head_np(morph_rows[i].pos)]


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


def _tokens_match(word: str, token: str) -> bool:
    """Loose token equality: exact match, or an elision-spelling difference (e.g. `I` / `I'`)
    that `morph.strip_word_punct` already reconciles for Layer 2."""
    return word == token or strip_word_punct(word, token) is not None


def _find_run(tokens: list[str], needle: list[str], exclude: set[int] | None = None) -> int:
    """Index of the first contiguous occurrence of `needle` within `tokens`, or -1.

    `exclude` skips run-start indices already claimed by an earlier occurrence of this same
    needle (see `align_chunk`'s `used` tracking) so a repeated word/phrase within one line
    (e.g. "a poco a poco") aligns each proposal to a distinct occurrence instead of collapsing
    them all onto the first.
    """
    if not needle:
        return -1
    exclude = exclude or set()
    last = len(tokens) - len(needle)
    for i in range(last + 1):
        if i in exclude:
            continue
        if all(_tokens_match(needle[j], tokens[i + j]) for j in range(len(needle))):
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
    used: dict[int, dict[tuple[str, ...], set[int]]],
) -> tuple[int, NPSpan] | None:
    """Align one NP table row to a (line, NPSpan). Returns None if no contiguous run is found.

    `used` tracks, per chunk-line index and exact needle, which run-start indices earlier rows
    already claimed in this same chunk — so two rows proposing the same repeated word/phrase
    (e.g. "poco" occurring twice in one line) land on distinct occurrences instead of both
    aligning to the first.
    """
    needle = _alpha_tokens(np_text)
    if not needle:
        return None
    needle_key = tuple(needle)
    # Try the labelled line first, then salvage by scanning the other chunk lines.
    order = list(range(len(line_numbers)))
    if labelled_line in line_numbers:
        idx = line_numbers.index(labelled_line)
        order = [idx] + [i for i in order if i != idx]
    for li in order:
        exclude = used.get(li, {}).get(needle_key, set())
        run = _find_run(token_lists[li], needle, exclude)
        if run < 0:
            continue
        start = run + 1
        end = run + len(needle)
        spans = span_lists[li]
        text = line_texts[li][spans[run][1] : spans[end - 1][2]]
        head = _head_index(token_lists[li], head_text, start, end)
        used.setdefault(li, {}).setdefault(needle_key, set()).add(run)
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
            if _tokens_match(word, tokens[i]):
                return i + 1
    return end


def align_chunk(
    line_numbers: list[int],
    line_texts: list[str],
    table_text: str,
    morph_rows: dict[int, list[MorphRow]] | None = None,
) -> tuple[dict[int, list[NPSpan]], int]:
    """Parse an NP table and align its rows to the given source lines.

    Returns (mapping line-number -> aligned NPSpans, count of unalignable rows). Raises
    ValueError if the table cannot be parsed at all. Every requested line gets an entry (an
    empty list if it has no NPs).

    When `morph_rows` (per-line Layer-2 rows) is supplied, a single-word row labelled with a
    line that has a fused enclitic pronoun (a compound `x+pronoun[+...]` POS, arity >= 2) is
    *not* counted as unalignable even if no matching token exists: the model is correctly
    naming the bound pronoun, but Layer 1 never tokenized it separately, so it can never align
    — `clitic_mentions()` already supplies the equivalent span deterministically from Layer 2,
    making the model's own attempt redundant rather than an error.
    """
    table = read_table(table_text)
    if table is None:
        raise ValueError("no parseable noun-phrase table found")
    keys = [canon_header(h) for h in table[0]]
    token_lists = [_alpha_tokens(t) for t in line_texts]
    span_lists = [token_spans(t) for t in line_texts]
    clitic_lines = {
        no
        for no, rows in (morph_rows or {}).items()
        for row in rows
        for part in row.pos.split("+")
        if len(row.pos.split("+")) >= 2 and part.strip().lower() == "pronoun"
    }

    result: dict[int, list[NPSpan]] = {no: [] for no in line_numbers}
    used: dict[int, dict[tuple[str, ...], set[int]]] = {}
    unaligned = 0
    for raw in table[2:]:  # skip header + separator
        cells = dict(zip(keys, raw))
        np_text = (cells.get("text") or "").strip()
        if not np_text:
            continue
        head_text = (cells.get("head") or "").strip()
        labelled = _parse_int(cells.get("line"))
        aligned = _align_row(
            line_numbers, token_lists, span_lists, line_texts, labelled, np_text, head_text, used
        )
        if aligned is None:
            if labelled in clitic_lines and len(_alpha_tokens(np_text)) == 1:
                continue
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


# --- Clitic mentions (derived deterministically from Layer 2) ----------------------


def clitic_mentions(line_no: int, tokens: list[str], morph_rows: list[MorphRow]) -> list[NPSpan]:
    """Bound-pronoun mentions for tokens Layer 2 tagged with a compound `x+pronoun[+...]` POS
    (e.g. `udirmi` -> lemma `udire+me`, pos `verb+pronoun` — an enclitic fused to a verb with no
    apostrophe, so Layer 1 never split it into its own token). Unlike ordinary NPs, these are not
    proposed by the model: they are generated purely from the already-frozen Layer 2 artifact, so
    they exist regardless of what the LLM did or didn't align for that line.

    Each qualifying component yields a single-token NPSpan whose `text` is `"+"` followed by that
    component's lemma, copied verbatim from Layer 2 (no surface-form normalization — Layer 2's own
    `mi`/`me` inconsistency is a Layer-2 concern, not fixed here). Tokens where the pos/lemma
    `+`-split arity disagrees (a rare Layer-2 data slip) are skipped rather than guessed at. A
    token whose POS is bare `pronoun` (no `+`, arity 1) is *not* compound — Layer 1 already
    tokenized it on its own, so the model can (and does) align an ordinary NP to it; only
    genuine fusions (arity >= 2) get a synthetic mention here, to avoid a redundant "+xxx"
    duplicate of that ordinary NP.
    """
    mentions: list[NPSpan] = []
    if len(morph_rows) != len(tokens):
        return mentions
    for i, row in enumerate(morph_rows, start=1):
        pos_parts = row.pos.split("+")
        lemma_parts = row.lemma.split("+")
        if len(pos_parts) < 2 or len(pos_parts) != len(lemma_parts):
            continue
        for pos_part, lemma_part in zip(pos_parts, lemma_parts):
            if pos_part.strip().lower() == "pronoun":
                mentions.append(NPSpan(line=line_no, start=i, end=i, head=i, text="+" + lemma_part))
    return mentions


# --- Repeat-word dedupe (deterministic repair of a fixed `align_chunk` bug) ---------


def dedupe_repeats(line_no: int, text: str, spans: list[NPSpan]) -> tuple[list[NPSpan], int]:
    """Reassign exact-duplicate spans to a further, unclaimed occurrence of the same run.

    Before `align_chunk` tracked claimed occurrences, every proposal for a repeated word or
    phrase in one line (e.g. "a poco a poco", "feltro e feltro") collapsed onto the *first*
    occurrence, leaving identical duplicate rows in artifacts built earlier. This repairs those
    in place with the same first-available-occurrence search `align_chunk` now uses at build
    time — no model call. A duplicate with no further occurrence to move to (e.g. the model's own
    row was itself redundant) is left unchanged. Returns (possibly-updated spans, count changed).
    """
    tokens = [tok for tok, _, _ in token_spans(text)]
    char_spans = token_spans(text)
    used: dict[tuple[str, ...], set[int]] = {}
    for s in spans:
        needle = tuple(tokens[s.start - 1 : s.end])
        used.setdefault(needle, set()).add(s.start - 1)

    seen: dict[tuple, int] = {}
    result: list[NPSpan] = []
    changed = 0
    for s in spans:
        key = (s.start, s.end, s.head, s.text)
        seen[key] = seen.get(key, 0) + 1
        if seen[key] == 1:
            result.append(s)
            continue
        needle = tuple(tokens[s.start - 1 : s.end])
        run = _find_run(tokens, list(needle), used.get(needle, set()))
        if run < 0:
            result.append(s)
            continue
        new_start = run + 1
        new_end = run + len(needle)
        new_head = new_start + (s.head - s.start)
        new_text = text[char_spans[run][1] : char_spans[new_end - 1][2]]
        result.append(NPSpan(line=line_no, start=new_start, end=new_end, head=new_head, text=new_text))
        used.setdefault(needle, set()).add(run)
        changed += 1
    return result, changed


# --- Validation --------------------------------------------------------------------


def validate_line(
    line_no: int,
    source_text: str,
    spans: list[NPSpan],
    morph_rows: list | None = None,
) -> list[Violation]:
    """Check that `spans` are well-formed against the deterministic tokens of `source_text`.

    Hard checks (structural bar): each NP's token range is in-bounds and ordered; the head lies
    within the range; `text` is the verbatim source substring of that range. A span whose `text`
    starts with `"+"` is a clitic mention (see `clitic_mentions`) rather than an ordinary NP: it
    must be single-token, and — when `morph_rows` is supplied — its suffix must be one of the
    host token's Layer-2 lemma components, in place of the verbatim-substring check (by
    construction, `"+xxx"` is never itself a source substring). Soft checks (only when
    `morph_rows` — the Layer-2 row per token — is supplied, under the frozen policy above):
    the head token is a content POS (`_can_head_np`), every noun/proper-noun token is the head
    of at least one NP (coverage, `_needs_np`), and every clitic mention Layer 2's compound POS
    implies (see `clitic_mentions`) is actually present among `spans` (clitic coverage — catches
    artifacts built before this mechanism existed, or any future regression; `np.py
    --fix-clitics` backfills them deterministically). Soft violations use kind "tag"; hard ones
    use "range"/"head"/"word".
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
        if span.text.startswith("+"):
            if span.start != span.end:
                violations.append(
                    Violation(line_no, "word", f"clitic mention {span.text!r} spans more than one token")
                )
            elif morph_rows is not None and len(morph_rows) == n:
                lemma_parts = morph_rows[span.head - 1].lemma.split("+")
                if span.text[1:] not in lemma_parts:
                    violations.append(
                        Violation(line_no, "word", f"{span.text!r} not in lemma parts {lemma_parts!r}")
                    )
            continue
        expected = source_text[tspans[span.start - 1][1] : tspans[span.end - 1][2]]
        if span.text != expected:
            violations.append(
                Violation(line_no, "word", f"{span.text!r} != source {expected!r}")
            )

    if morph_rows is not None and len(morph_rows) == n:
        for span in spans:
            if 1 <= span.head <= n and not _can_head_np(morph_rows[span.head - 1].pos):
                pos = morph_rows[span.head - 1].pos
                violations.append(
                    Violation(line_no, "tag", f"head {tokens[span.head - 1]!r} is {pos!r}, not a content POS")
                )
        heads = {span.head for span in spans}
        for i, row in enumerate(morph_rows, start=1):
            if _needs_np(row.pos, row.note) and i not in heads:
                violations.append(
                    Violation(line_no, "tag", f"noun {tokens[i - 1]!r} (token {i}) heads no NP")
                )
        expected = {(m.head, m.text) for m in clitic_mentions(line_no, tokens, morph_rows)}
        actual = {(span.head, span.text) for span in spans if span.text.startswith("+")}
        for head, text in sorted(expected - actual):
            violations.append(
                Violation(line_no, "tag", f"token {head} {tokens[head - 1]!r} missing clitic mention {text!r}")
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


artifact_path = _artifact_path


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
