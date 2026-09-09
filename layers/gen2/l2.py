"""Generation 2, Layer 2: grammatical words and their coarse part of speech, in one pass.

`L2.md`: L2 is an ordered list of `(l1_index, text, pos)` triples. A composite L1 token
produces several L2 entries sharing one `l1_index` (1:many); every other L1 token,
punctuation included, carries straight through as exactly one entry (1:1). L2 **only
splits** — a many:1 merge (old Layer 4's `fixed`) stays a relation one layer up, over L2
entries, so `l1_index` is always a single integer and never a tuple.

**Why the split and the POS are one question (operator, 2026-09-09).** The earlier version
of this module asked the split alone, and `pel` (*Inf* 1:33, `che di pel macolato era
coverta`) is what that costs: asked only about shape, three separate runs all answered
`per+il`, because a truncated *pelo* is exactly `del`-shaped. Once that split is written
down there is no route back — a later pass meets `per` and `il`, not `pel`. What made old
Layer 2 right at this position is that `morph/morph.py` never asks whether a token splits:
it asks for a whole row, so `di` + `preposition+article` is unwritable at a position whose
line reads `di per il macolato` — two prepositions and an article in a row, and an
adjective left with no noun. The contentful second column is the guard, and it only guards
if it is answered **at the same time**, in the line.

**Lemmas are excluded, restorations are not** (operator, 2026-09-09). Old Layer 2 carried
the guard in a `lemma` column; that column also carries a dictionary judgment this layer
does not want — it is what splits one wordform's rows between an adjective form and a verb
infinitive (`REDESIGN.md` §6, `smarrito` 4/4), and "the standard form" is the framing
already rejected for `sanza`/`core`/`giuso`. The POS column alone blocks `per+il`, so the
guard is kept and the lexicon is not.

What a single word may be is therefore not "the token verbatim" but "the token, with the
letters it drops put back": `ben` -> `bene` and `ch'` -> `che` are answers this pass
accepts, and the boundary is mechanical, not asked for — `is_restoration` requires the
token's own letters to read straight through the answer, growing only at an end the
token's own spelling opens, so `sanza` -> `senza`, `smarrita` -> `smarrito` and `era` ->
`essere` are refused (operator: 「ben→bene 禁止する必要はないのでは？restoreを包含して
いるので」). This is `L2.md`'s step 3 folded in: **the normalization is one of the things
this answer decides**, and folding it in is what finally reaches the case no separate pass
could — a truncation hidden *inside* a fusion, `farne` -> `fare`+`ne`, invisible before the
split and unreachable by a pass that never sees the token whole.

**Coarse POS only.** `L2.md`'s *Step 2 should be staged* stands: the tag set here is a
closed set of ten (`POS_TAGS`), subtypes and features (gender, number, person, tense, mood)
belong to a later stage over these entries. Old Layer 2's own `pos` column is *not* that —
39 values with `relative pronoun`/`pronoun` and `proper noun`/`noun` leaking in — so this
pass writes its own vocabulary and `--check` maps old Layer 2's onto it to compare.
A participle is `verb` here whatever its use, which is the one boundary the model answers
both ways when nothing says so.

**What the model is asked.** One **chunk of lines** per step — `--chunk`, default 3, old
Layer 2's own granularity — with the lines for context and the chunk's splittable tokens
listed, and it answers a Markdown table, **one row per token, in order**: the token, the
grammatical words it is made of, and one coarse tag per word. Dense, unlike the split-only
contract that preceded it: a token with no row is not a silent "single word" any more, so
every token carries a judgment that can be read back and, at `pel`, contradicted.

Answers are never keyed by an index. Row *n* answers token *n* of the list the request
carried, and the program attaches the `l1_index` from the token's own position, so getting
the analysis right and copying a number correctly are never bundled into one answer.

No transcript crosses a chunk or a retry: every attempt sends exactly `[system, user]`. The
runtime, not the model, holds the gate — a refused answer records nothing and leaves the
table exactly as it was, which is `harness/stages/09.md` §2.1's "refusal is the identity
morphism" at the scale of a chunk. **A chunk that never passes degrades to line-by-line**,
which is `morph.py`'s own fallback ("chunk failed, retrying line by line").

**Standing patterns, and the one override.** This CLI holds `ARCHITECTURE.md`'s standards:
model access through llm7shi's adapter with lazy imports (§2), a shared status-bar stream
and per-step progress on stderr (§4), the streaming JSONL `--log` contract with a final
`summary` record (§5), a report class with both faces (§6), gate errors fed back verbatim
rather than raised (§7), stub-driven tests over frozen data (§8), and §9's CLI skeleton.
**The override is §3's wire protocol**: there is no `<tool_call>` XML because there are no
tools — this is the fixed-context mode (`harness/stages/09.md` §2), where the runtime holds
the gate and the model's whole output is one `<words>` block.

The command line is the corpus's own driver shape (`skel/skel.py`, `dep/dep.py`):
canticles positional, `-c` a canto spec resolved by `api.select_cantos`, and every
selection a filter over what the corpus has rather than a count anyone has to know.

    uv run python -m layers.gen2.l2 inferno -m ...        # all of Inferno
    uv run python -m layers.gen2.l2 inferno -c 1 -m ...   # just canto 1
    uv run python -m layers.gen2.l2 inferno -c 12- -m ... # canto 12 on
    uv run python -m layers.gen2.l2 inferno -c 1 -l 1-9 -m ...   # a line range
    uv run python -m layers.gen2.l2 inferno -c 1 -m ... --force  # ask again, from line 1
    uv run python -m layers.gen2.l2 inferno -c 1 -m ... --no-log # no log at all
    uv run python -m layers.gen2.l2 inferno --check       # code-only, no model

A run **resumes**: the committed artifact is read back and a chunk every one of whose
lines it already answers is skipped before any request, its entries carried through
verbatim. `--force` is how a run is made to ask from the first line again.

The log is written **by default** and names no file: each canto's records go beside its
own artifact, `NN.tsv` to `NN.log`. A run whose numbers were never recorded cannot be
reported afterwards, and one named file could not hold a run over several cantos anyway.
`--no-log` turns it off.

**Bootstrap status (premise 3).** The running pass reads L1 and nothing else: no old-layer
file is named as an input, and the model is shown no old Layer 2 row. Old Layer 2 enters
once, afterwards and offline, through `--check`, which diffs this artifact against
`morph/<canticle>/<NN>.tsv` — the splits off its `lemma` column, the tags off its `pos`
column through `COARSE_POS` — and reports `L2.md`'s three outcomes (agrees /
precedent-is-wrong / genuine ambiguity). Keeping the diff after the run is what makes
agreement evidence rather than an echo.
"""

from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Iterable, Mapping, Sequence

from .l1 import L1Line, l1_canto

# The pass's own model default. `dante_corpus.harness.llm.DEFAULT_MODEL` is the local
# Ollama build; this pass runs against the hosted one, where wall clock matters over a
# corpus of 14,233 lines (`ARCHITECTURE.md` §3).
DEFAULT_MODEL = "google:gemma-4-31b-it"

# Lines per request — old Layer 2's own granularity (`morph/morph.py --chunk`, default 3).
# The unit of work, and therefore what a request costs and what one failure loses.
CHUNK_SIZE = 3

# How many times one chunk may be asked. A cost cap, not a target: a chunk that passes the
# gate stops at once, and one that never does degrades to line-by-line rather than being
# quietly defaulted to the identity analysis.
MAX_ITERATIONS = 3

# At most three grammatical words in one written token (`dirtelo` = `dir`+`te`+`lo`); old
# Layer 2's own composite `pos` column reaches three and stops there.
MAX_PARTS = 3

# The closed coarse vocabulary. Ten values, one stage: subtypes (`proper noun`, `relative
# pronoun`, `possessive adjective`) and features (gender, number, person, tense, mood) are
# a later stage's, over these entries — `L2.md`, *Step 2 should be staged*. Old Layer 2's
# 39-value drift (`REDESIGN.md` §6) is what an open column produces.
POS_TAGS = (
    "noun",
    "verb",
    "adjective",
    "adverb",
    "pronoun",
    "preposition",
    "article",
    "conjunction",
    "numeral",
    "interjection",
)

# Old Layer 2's `pos` values mapped onto that set, for `--check` only. Every entry is a
# subtype folded into its coarse category — never a re-decision — so a disagreement the
# check reports is a real disagreement and not a vocabulary difference.
COARSE_POS = {
    "proper noun": "noun",
    "relative pronoun": "pronoun",
    "possessive adjective": "adjective",
    "demonstrative adjective": "adjective",
    "participle": "verb",
    "past participle": "verb",
    "present participle": "verb",
    "determiner": "article",
    "number": "numeral",
    "particle": "adverb",
}

SKILL_DIR = Path(__file__).resolve().parent / "skills" / "l2-words"

ARTIFACT_HEADER = ("line", "l1_index", "l2_index", "text", "pos")

_WORDS_BLOCK = re.compile(r"<words>(.*?)</words>", re.DOTALL | re.IGNORECASE)


# --- The L2 objects ------------------------------------------------------------------


@dataclass(frozen=True)
class L2Entry:
    """One grammatical word: the L1 token it came from, its text, its coarse POS."""

    l1_index: int
    text: str
    pos: str = ""

    def to_dict(self) -> dict[str, object]:
        return {"l1_index": self.l1_index, "text": self.text, "pos": self.pos}


@dataclass(frozen=True)
class L2Line:
    """A line's L2 entries in order. The L2 token number is the position in this list."""

    no: int
    entries: tuple[L2Entry, ...]

    def to_dict(self) -> dict[str, object]:
        return {"no": self.no, "entries": [entry.to_dict() for entry in self.entries]}


@dataclass(frozen=True)
class Analysis:
    """One token's answer: its grammatical words, and one coarse tag for each.

    `parts` and `tags` are the same length by construction — the gate refuses a row where
    they are not — so an entry never exists without a tag, and a tag never floats free of
    the word it describes.
    """

    parts: tuple[str, ...]
    tags: tuple[str, ...]

    @property
    def split(self) -> bool:
        return len(self.parts) > 1

    def to_dict(self) -> dict[str, object]:
        return {"parts": list(self.parts), "pos": list(self.tags)}


# --- Which tokens the model is asked about ----------------------------------------------


def is_splittable(token: str) -> bool:
    """Can this L1 token be a grammatical word at all?

    Only a token carrying a letter can. Punctuation is neither split nor tagged, and saying
    so here is a deterministic reading of L1's own output — not a fact borrowed from old
    Layer 2 — so it costs no model call and no premise.
    """
    return any(character.isalpha() for character in token)


def wordform_key(token: str) -> str:
    """The table's key for a token: case-folded, since `Nel` and `nel` analyse alike."""
    return token.casefold()


# Both apostrophes the corpus writes: the typewriter one it actually uses, and the
# typographic one a model may answer with.
_APOSTROPHES = "'’"


def letters_of(token: str) -> str:
    """The token's letters with its apostrophes removed — what a restoration must keep."""
    return "".join(character for character in token if character not in _APOSTROPHES)


def _ascii_fold(text: str) -> str:
    """Case- and accent-insensitive comparison key, so `Tant'` -> `Tanto` reads through."""
    import unicodedata

    decomposed = unicodedata.normalize("NFD", text.casefold())
    return "".join(c for c in decomposed if not unicodedata.combining(c))


def is_restoration(token: str, restored: str) -> bool:
    """Is `restored` the same word with its dropped letters put back where they were dropped?

    The token's own letters must read straight through the answer, unbroken and in order —
    that is what keeps the pass off lexical substitution without enumerating the words it
    must not touch (`pel` -> `pelo` reads through; `sanza` -> `senza` does not, and neither
    does a lemma that changes an ending: `smarrita` -> `smarrito`, `nostra` -> `nostro`,
    `era` -> `essere`). But reading through is not enough on its own, because it does not
    say **which end** grew: `ch'` -> `ache` reads through just as well as `ch'` -> `che`.

    **The apostrophe is what says where the letters went** (operator, 2026-09-09), so it is
    read as a marker rather than stripped and forgotten:

    - a **leading** apostrophe stands for letters dropped at the start, so the answer must
      grow there — `'l` -> `il`, `'ncontro` -> `incontro` — and no answer may grow at the
      start without one, which is what refuses `ch'` -> `ache`;
    - a **trailing** apostrophe stands for letters dropped at the end, so the answer must
      grow there — `ch'` -> `che`, `l'` -> `lo`;
    - the end may also grow with no apostrophe at all, because that is the other phenomenon
      in scope: an unmarked dropped final syllable, `cammin` -> `cammino`, `ben` -> `bene`.

    A token elided at both ends is therefore allowed to grow at both, and only there.

    This lives here rather than in `restore.py` because the words pass is now what applies
    it — `restore.py` imports it — and because it is what makes "no lemma" a mechanical
    rule rather than a request: an answer may put letters back, and may do nothing else.
    """
    stem = _ascii_fold(letters_of(token))
    target = _ascii_fold(restored)
    if not stem or not target or len(target) <= len(stem):
        return False
    leading = token[:1] in _APOSTROPHES
    trailing = token[-1:] in _APOSTROPHES
    start = target.find(stem)
    while start != -1:
        grew_at_start = start > 0
        grew_at_end = start + len(stem) < len(target)
        if grew_at_start == leading and (grew_at_end or not trailing):
            return True
        start = target.find(stem, start + 1)
    return False


def distinct_wordforms(lines: Iterable[L1Line]) -> list[str]:
    """The wordforms this run asks about, in first-appearance order."""
    seen: set[str] = set()
    out: list[str] = []
    for line in lines:
        for token in line.tokens:
            if not is_splittable(token.text):
                continue
            key = wordform_key(token.text)
            if key in seen:
                continue
            seen.add(key)
            out.append(token.text)
    return out


# --- $\Sigma$: applying the answers -----------------------------------------------------

# Where an answer applies: the token at `(line number, l1_index)`. Answers are recorded per
# occurrence rather than per wordform because a wordform genuinely reads two ways in
# different passages (`nel` = `in+il` vs `ne+lo`, `che` conjunction vs relative pronoun),
# and a wordform-keyed table cannot hold both. The table `L2.md` describes is then what a
# corpus-wide run *derives* from these occurrences, with the disagreements visible instead
# of averaged away.
Position = tuple[int, int]


def apply_analyses(line: L1Line, analyses: Mapping[Position, Analysis]) -> L2Line:
    """One line's L2, given the analyses found for its tokens. Pure: no model, no I/O.

    A token with no analysis recorded passes through verbatim with an empty tag — which is
    what an unanswered token gets, so a failed step degrades to the identity rather than to
    a hole in the line. Punctuation is that case by construction and always will be.
    """
    entries: list[L2Entry] = []
    for token in line.tokens:
        analysis = analyses.get((line.no, token.index))
        if analysis is None:
            entries.append(L2Entry(l1_index=token.index, text=token.text))
            continue
        for part, tag in zip(analysis.parts, analysis.tags):
            entries.append(L2Entry(l1_index=token.index, text=part, pos=tag))
    return L2Line(no=line.no, entries=tuple(entries))


# --- Chunks: the unit of work ------------------------------------------------------------


def chunks(lines: Sequence[L1Line], size: int) -> list[tuple[L1Line, ...]]:
    """Consecutive line groups of `size`, old Layer 2's own unit (`morph.py::_chunks`)."""
    return [tuple(lines[start : start + size]) for start in range(0, len(lines), size)]


@dataclass(frozen=True)
class Asked:
    """One token the chunk asks about: where it is, and how it is written."""

    line: int
    l1_index: int
    text: str


def asked_tokens(chunk: Sequence[L1Line]) -> list[Asked]:
    """The chunk's splittable tokens in L1 order — the rows the answer must have, in order.

    The answer is positional against exactly this list: row *n* is token *n*. That is why
    nothing here is renumbered or reordered, and why the request prints the same list.
    """
    return [
        Asked(line=line.no, l1_index=token.index, text=token.text)
        for line in chunk
        for token in line.tokens
        if is_splittable(token.text)
    ]


# --- $O$: the question, and the gate on the answer -------------------------------------


TABLE_HEADER = ("Line", "Token", "Words", "Part of Speech")


def render_blank_table(tokens: Sequence[Asked]) -> str:
    """The question as the table it asks for, with the two known columns already filled.

    Handing the model the skeleton rather than a token list (operator, 2026-09-09) does
    three things at once. The row set stops being something to reconstruct — the answer is
    a fill-in, so a dropped or duplicated row is a visible edit rather than a miscount. The
    **line number rides on every row**, so a row is never adrift from the verse it belongs
    to; a flat token list loses the line boundaries exactly where the analysis needs them
    (`pel` is decidable only from `di pel macolato`). And the shape of the answer needs no
    describing, because it is the shape of the question.

    Punctuation is not listed: it is neither split nor tagged (`is_splittable`).
    """
    rows = ["| " + " | ".join(TABLE_HEADER) + " |", "|" + "---|" * len(TABLE_HEADER)]
    rows += [f"| {token.line} | {token.text} |  |  |" for token in tokens]
    return "\n".join(rows)


def ask_message(chunk: Sequence[L1Line], *, refusal: str = "") -> str:
    """The single user message for one attempt at one chunk.

    The lines are shown because the analysis is *of the line* — `pel` is decidable only
    from `di pel macolato` — and the tokens come as the blank table to fill in, so the model
    never has to re-tokenize (`ch'` and `i'` are two tokens, not one) nor rebuild the row
    set. Two shapes, and the wording says which, because the next move differs: a fresh
    question, and a refused answer to repair.
    """
    lines = "\n".join(f"{line.no} {line.text}" for line in chunk)
    parts = [
        f"<lines>\n{lines}\n</lines>",
        f"<tokens>\n{render_blank_table(asked_tokens(chunk))}\n</tokens>",
    ]
    if refusal:
        parts.append(
            "<verdict>\n"
            "The check refused your last answer, so nothing was recorded. It reported:\n"
            f"- {refusal}\n"
            "Send the whole table again, corrected.\n"
            "</verdict>"
        )
    else:
        parts.append(
            "<verdict>\n"
            "Nothing is on record for these lines. Answer one row for every token listed "
            "above with its last two columns filled in: the grammatical words each token "
            "is written from, and one part of speech for each of those words.\n"
            "</verdict>"
        )
    return "\n\n".join(parts)


def _table_rows(body: str) -> list[list[str]]:
    """The pipe-table rows of a `<words>` block: cells stripped, rulers and headers gone."""
    rows: list[list[str]] = []
    for raw in body.splitlines():
        line = raw.strip()
        if not line.startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if not any(cells):
            continue
        if all(set(cell) <= set("-: ") and cell for cell in cells):
            continue  # the ruler under the header
        if [cell.casefold() for cell in cells[:2]] == ["line", "token"]:
            continue  # the header, repeated or not
        rows.append(cells)
    return rows


def parse_words_answer(
    text: str, *, tokens: Sequence[Asked]
) -> tuple[dict[int, Analysis], str]:
    """The `<words>` table — the question's own table, filled in — or the gate's reason.

    Returns `(analyses, error)` where `analyses` maps an index into `tokens` to that
    token's grammatical words and their coarse tags. A non-empty `error` means nothing is
    recorded and the caller re-asks with it.

    The contract is dense on purpose. The split-only pass that preceded this one listed
    differences only, and an empty block was indistinguishable from a model that never
    looked; here every token is answered, and the tag column is what a wrong split has to
    survive — `di | di | preposition`, `per | per | preposition`, `il | il | article`
    cannot be written across `di pel macolato` without saying something false about the
    line.

    Rows are matched by position, not by key, so nothing is refused for naming a place
    ambiguously and a wordform occurring twice in one chunk simply gets two rows. What the
    gate does check, in order: the row count, the token column (case-insensitively — the
    model copies it, but a capital is never a reason to spend another request), the line
    column (which the request filled in, so a disagreement means rows moved), the part
    count, a single part being the token or a **restoration** of it (`is_restoration`: the
    letters read straight through, so `ben` -> `bene` passes and `sanza` -> `senza` or
    `smarrita` -> `smarrito` does not), and the tag column, one closed-set tag per part.
    """
    matches = _WORDS_BLOCK.findall(text or "")
    if not matches:
        return {}, "no <words> block in the answer"
    if len(matches) > 1:
        return {}, f"{len(matches)} <words> blocks in the answer; send exactly one"
    rows = _table_rows(matches[0])
    if len(rows) != len(tokens):
        return {}, (
            f"the table has {len(rows)} row(s) for {len(tokens)} token(s); send the table "
            "you were given, filled in — every row, in the same order, none added"
        )
    analyses: dict[int, Analysis] = {}
    for index, (row, token) in enumerate(zip(rows, tokens)):
        position = index + 1
        if len(row) != 4:
            return {}, (
                f"row {position} has {len(row)} column(s); every row is "
                "| " + " | ".join(TABLE_HEADER) + " |"
            )
        line_no, written, words, tags = row
        if wordform_key(written) != wordform_key(token.text):
            return {}, (
                f"row {position} says {written!r} where token {position} is "
                f"{token.text!r} (line {token.line}); fill in the table as given, one row "
                "per token, in that order"
            )
        if line_no.strip() != str(token.line):
            return {}, (
                f"row {position} ({token.text!r}) says line {line_no!r}, but that token "
                f"is on line {token.line}; the Line column is copied from the table you "
                "were given"
            )
        parts = [part.strip() for part in words.split("+")]
        if any(not part for part in parts):
            return {}, f"row {position} ({token.text!r}): {words!r} has an empty part"
        if any(any(ch.isspace() for ch in part) for part in parts):
            return {}, f"row {position} ({token.text!r}): {words!r} has a space in a part"
        if len(parts) > MAX_PARTS:
            return {}, (
                f"row {position} ({token.text!r}): {words!r} has {len(parts)} parts; at "
                f"most {MAX_PARTS} are accepted"
            )
        if (
            len(parts) == 1
            and wordform_key(parts[0]) != wordform_key(token.text)
            and not is_restoration(token.text, parts[0])
        ):
            return {}, (
                f"row {position} ({token.text!r}): {parts[0]!r} is neither the token as it "
                "stands nor the token with its dropped letters put back — the word's own "
                "letters must read straight through the answer, so this pass can restore "
                "an ending or an elision but never substitute a different word or a "
                "dictionary form"
            )
        tag_list = [tag.strip().casefold() for tag in tags.split("+")]
        if len(tag_list) != len(parts):
            return {}, (
                f"row {position} ({token.text!r}): {len(parts)} word(s) but "
                f"{len(tag_list)} part(s) of speech; one tag per word, joined by '+'"
            )
        unknown = [tag for tag in tag_list if tag not in POS_TAGS]
        if unknown:
            return {}, (
                f"row {position} ({token.text!r}): {', '.join(repr(t) for t in unknown)} "
                f"is not one of the accepted tags ({', '.join(POS_TAGS)})"
            )
        analyses[index] = Analysis(parts=tuple(parts), tags=tuple(tag_list))
    return analyses, ""


# --- The bounded step -------------------------------------------------------------------


@dataclass
class AttemptRecord:
    """What one attempt at one chunk did."""

    attempt: int
    kind: str  # "ask" | "refused"
    accepted: bool
    rows: int = 0
    error: str = ""
    seconds: float = 0.0

    def to_dict(self) -> dict:
        return {
            "attempt": self.attempt,
            "kind": self.kind,
            "accepted": self.accepted,
            "rows": self.rows,
            "error": self.error,
            "seconds": round(self.seconds, 3),
        }


@dataclass
class ChunkResult:
    """One chunk's settled answer, or the record of it never settling."""

    lines: list[int] = field(default_factory=list)
    tokens: list[Asked] = field(default_factory=list)
    answers: dict[int, Analysis] = field(default_factory=dict)
    accepted: bool = False
    attempts: list[AttemptRecord] = field(default_factory=list)
    stop_reason: str = "settled"  # settled | budget | unanswered
    fallback: bool = False  # this chunk is a single line retried after its group failed
    conflicts: list[dict] = field(default_factory=list)

    @property
    def resolved(self) -> bool:
        return self.accepted

    @property
    def splits(self) -> int:
        return sum(1 for analysis in self.answers.values() if analysis.split)

    @property
    def seconds(self) -> float:
        return sum(attempt.seconds for attempt in self.attempts)

    def pairs(self) -> list[tuple[Asked, Analysis]]:
        """The tokens answered, with their analyses, in L1 order."""
        return [(self.tokens[index], self.answers[index]) for index in sorted(self.answers)]

    def positions(self) -> dict[Position, Analysis]:
        """The answers as `(line, l1_index) -> Analysis`, ready for `apply_analyses`."""
        return {(token.line, token.l1_index): analysis for token, analysis in self.pairs()}

    def to_dict(self) -> dict:
        return {
            "record": "chunk",
            "lines": list(self.lines),
            "tokens": len(self.tokens),
            "resolved": self.resolved,
            "splits": self.splits,
            "stop_reason": self.stop_reason,
            "fallback": self.fallback,
            "conflicts": list(self.conflicts),
            "answers": [
                {"line": token.line, "l1_index": token.l1_index, "word": token.text,
                 **analysis.to_dict()}
                for token, analysis in self.pairs()
            ],
            "attempts": [attempt.to_dict() for attempt in self.attempts],
            "seconds": round(self.seconds, 3),
        }


def analyze_chunk(
    chunk: Sequence[L1Line],
    *,
    generate: Callable[[list[dict]], str],
    system_prompt: str,
    max_iterations: int = MAX_ITERATIONS,
    fallback: bool = False,
) -> ChunkResult:
    """Ask one chunk until the gate accepts an answer, or the budget runs out.

    Every attempt resets the backend and sends exactly `[system, user]`, so per-request size
    is a function of the chunk and never of the attempt count, and a refused attempt leaves
    the caller's table untouched.
    """
    tokens = asked_tokens(chunk)
    result = ChunkResult(lines=[line.no for line in chunk], tokens=tokens,
                         fallback=fallback)
    if not tokens:
        # A chunk of pure punctuation asks nothing; that is an answer, not a failure.
        result.accepted = True
        result.stop_reason = "settled"
        return result
    refusal = ""
    for attempt in range(1, max_iterations + 1):
        kind = "refused" if refusal else "ask"
        message = ask_message(chunk, refusal=refusal)
        reset = getattr(generate, "reset", None)
        if reset is not None:
            reset()
        began = time.monotonic()
        answer = generate(
            [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message},
            ]
        )
        elapsed = time.monotonic() - began
        analyses, error = parse_words_answer(answer, tokens=tokens)
        if error:
            result.attempts.append(
                AttemptRecord(attempt=attempt, kind=kind, accepted=False, error=error,
                              seconds=elapsed)
            )
            refusal = error
            continue
        result.attempts.append(
            AttemptRecord(attempt=attempt, kind=kind, accepted=True, rows=len(analyses),
                          seconds=elapsed)
        )
        result.answers = analyses
        result.accepted = True
        result.stop_reason = "settled"
        return result
    result.stop_reason = "budget" if result.attempts else "unanswered"
    return result


def build_l2(
    lines: Sequence[L1Line],
    *,
    generate: Callable[[list[dict]], str],
    system_prompt: str,
    chunk_size: int = CHUNK_SIZE,
    max_iterations: int = MAX_ITERATIONS,
    on_settled: Callable[[ChunkResult], None] | None = None,
    already_answered: Callable[[Sequence[L1Line]], bool] | None = None,
    on_skipped: Callable[[Sequence[L1Line]], None] | None = None,
) -> dict[Position, Analysis]:
    """Every analysis these lines yield, by position: one bounded step per chunk of lines.

    A chunk that never passes the gate is retried line by line — `morph.py`'s own
    degradation ("chunk failed, retrying line by line") — so one bad group costs its own
    lines, not the run.

    Analyses are recorded **per occurrence**, so a wordform answered two ways in different
    passages keeps both. The first reading of a wordform is remembered only to notice the
    second: a later occurrence answered differently is recorded as a **conflict** on that
    chunk — the disagreement `L2.md` expects a handful of (`nel` = `in+il` vs `ne+lo`,
    `che` conjunction vs pronoun, which the POS column now makes visible where the split
    column alone saw nothing) — and then applied as answered, because the model had that
    passage in front of it and this one is the reading it gave for *this* line.

    `on_settled` is called as each chunk settles, so the run's records reach disk when they
    settle rather than when the pass ends (`ARCHITECTURE.md` §5).

    `already_answered` is the resume test, asked once per chunk **before** any request: a
    chunk every one of whose lines the artifact already holds costs nothing and is reported
    through `on_skipped`. The chunk boundaries do not move when a run resumes — they are cut
    over all the lines selected, answered or not — so the chunk is the unit of resumption as
    well as of asking, and a chunk only *partly* on disk is asked again whole rather than
    half-asked. The caller keeps the answered lines' entries: this function returns analyses
    only for what it asked about.
    """
    found: dict[Position, Analysis] = {}
    first_reading: dict[str, Analysis] = {}

    def absorb(result: ChunkResult) -> None:
        for token, analysis in result.pairs():
            key = wordform_key(token.text)
            seen = first_reading.setdefault(key, analysis)
            if seen != analysis:
                result.conflicts.append(
                    {"word": token.text, "line": token.line,
                     "first": seen.to_dict(), "here": analysis.to_dict()}
                )
            found[(token.line, token.l1_index)] = analysis
        if on_settled is not None:
            on_settled(result)

    for chunk in chunks(lines, chunk_size):
        if already_answered is not None and already_answered(chunk):
            if on_skipped is not None:
                on_skipped(chunk)
            continue
        result = analyze_chunk(
            chunk,
            generate=generate,
            system_prompt=system_prompt,
            max_iterations=max_iterations,
        )
        absorb(result)
        if result.accepted or len(chunk) == 1:
            continue
        # The group was refused; its lines are still unanswered. Retry them one at a time.
        for line in chunk:
            absorb(
                analyze_chunk(
                    (line,),
                    generate=generate,
                    system_prompt=system_prompt,
                    max_iterations=max_iterations,
                    fallback=True,
                )
            )
    return found


# --- The artifact -----------------------------------------------------------------------


def render_artifact(l2_lines: Sequence[L2Line]) -> str:
    """The artifact TSV: one row per L2 entry, in line and entry order.

    `l2_index` is the entry's position within its line. `L2.md` says the L2 token number
    "is never stored separately, only `l1_index` is data" — true of the in-memory list,
    whose order *is* the numbering; a flat file has no order to lean on, so the position
    is written down. It is derived, not decided. `pos` is empty for punctuation and for a
    token no attempt ever answered.
    """
    out = ["\t".join(ARTIFACT_HEADER)]
    for line in l2_lines:
        for l2_index, entry in enumerate(line.entries):
            out.append(f"{line.no}\t{entry.l1_index}\t{l2_index}\t{entry.text}\t{entry.pos}")
    return "\n".join(out) + "\n"


def parse_artifact(text: str) -> list[L2Line]:
    """Read back `render_artifact`'s output, so `--check` and resume run off the file.

    Five columns exactly. A four-column file is the split-only artifact this pass replaced;
    it parses as nothing rather than as an answer with no tags, so a run over it asks again
    instead of resuming from a shape that predates the POS column.
    """
    lines: list[L2Line] = []
    entries: list[L2Entry] = []
    current: int | None = None
    for raw in text.splitlines():
        cells = raw.split("\t")
        if len(cells) != 5 or tuple(c.strip() for c in cells) == ARTIFACT_HEADER:
            continue
        no, l1_index, _l2_index, entry_text, pos = cells
        try:
            no_i, l1_i = int(no), int(l1_index)
        except ValueError:
            continue
        if current is not None and no_i != current:
            lines.append(L2Line(no=current, entries=tuple(entries)))
            entries = []
        current = no_i
        entries.append(L2Entry(l1_index=l1_i, text=entry_text, pos=pos.strip()))
    if current is not None:
        lines.append(L2Line(no=current, entries=tuple(entries)))
    return lines


def artifact_path(canticle: str, number: int) -> Path:
    """`layers/l2/<canticle>/NN.tsv` — beside `gen2/`, never inside it.

    `gen2/` is a code directory: no artifact and no run log is written into it
    (operator, 2026-09-09). The tree outside it keeps the shape every other layer in
    this repository already uses, `<layer>/<canticle>/NN.tsv`.
    """
    return Path(__file__).resolve().parent.parent / "l2" / canticle / f"{number:02d}.tsv"


# --- The precedent check: offline, after the fact -----------------------------------------


@dataclass(frozen=True)
class PrecedentRow:
    """One wordform, as this artifact splits it and as old Layer 2 splits it."""

    wordform: str
    ours: tuple[tuple[str, ...], ...]
    theirs: tuple[tuple[str, ...], ...]
    verdict: str  # agrees | differs | l2-ambiguous | layer2-ambiguous | absent

    def to_dict(self) -> dict:
        return {
            "wordform": self.wordform,
            "ours": [list(reading) for reading in self.ours],
            "theirs": [list(reading) for reading in self.theirs],
            "verdict": self.verdict,
        }


@dataclass(frozen=True)
class PosMismatch:
    """One position where this artifact's coarse tag and old Layer 2's, folded onto the
    same vocabulary by `COARSE_POS`, disagree."""

    line: int
    word: str
    ours: tuple[str, ...]
    theirs: tuple[str, ...]

    def to_dict(self) -> dict:
        return {
            "line": self.line,
            "word": self.word,
            "ours": list(self.ours),
            "theirs": list(self.theirs),
        }


def _fold(parts: Sequence[str]) -> tuple[str, ...]:
    return tuple(part.casefold() for part in parts)


def coarse_pos(value: str) -> tuple[str, ...]:
    """Old Layer 2's `pos` cell as this pass's vocabulary: `preposition+article` is two
    tags, `relative pronoun` is `pronoun`, and anything with no coarse equivalent stays as
    written so the check reports it rather than hiding it under a fold."""
    out: list[str] = []
    for raw in str(value or "").split("+"):
        tag = " ".join(raw.split()).casefold()
        out.append(COARSE_POS.get(tag, tag))
    return tuple(out)


def precedent_splits(
    morph_rows: Mapping[int, Sequence[object]],
    line_range: tuple[int, int] | None = None,
) -> dict[str, tuple[tuple[str, ...], ...]]:
    """Old Layer 2's own split for each wordform, read off its `lemma` column.

    A composite token is one morph row whose `lemma` and `pos` carry `+` (e.g.
    `Nel  in+il  preposition+article`); every other row is a single grammatical word, and
    its `lemma` is a lemma rather than a split, so the wordform stands for itself.

    Every distinct reading is kept, not collapsed: a wordform old Layer 2 records two ways
    is exactly `L2.md`'s genuine-ambiguity outcome, and hiding it behind a majority pick is
    the one thing this check must not do.
    """
    out: dict[str, set[tuple[str, ...]]] = {}
    for no in sorted(morph_rows):
        if line_range is not None and not (line_range[0] <= no <= line_range[1]):
            continue
        for row in morph_rows[no]:
            word = str(getattr(row, "word", "") or "")
            lemma = str(getattr(row, "lemma", "") or "")
            if not word:
                continue
            parts = tuple(lemma.split("+")) if "+" in lemma else (word,)
            out.setdefault(wordform_key(word), set()).add(parts)
    return {
        key: tuple(sorted(readings)) for key, readings in out.items()
    }


def our_splits(
    l1_lines: Sequence[L1Line],
    l2_lines: Sequence[L2Line],
    *,
    line_range: tuple[int, int] | None = None,
) -> dict[str, tuple[tuple[str, ...], ...]]:
    """This artifact's splits for each wordform, keyed by the L1 surface form.

    The artifact records `l1_index`, not the token it came from, so L1 supplies the key —
    which is the same asymmetry the design intends: `l1_index` is data, the original
    spelling is always one lookup away in a layer that is a pure function of the source.

    Every distinct reading is kept, the same way `precedent_splits` keeps old Layer 2's:
    answers are recorded per occurrence, so a wordform this artifact splits two ways must
    show as two, not as whichever came first.

    **A token that stayed one word is folded back to the token**, whatever the answer
    restored it to. Restoring `l'` to `lo` here and `le` there is not a split decision, and
    letting it through would make every restored wordform `l2-ambiguous` and mask the split
    disagreements this table exists to find. Restorations have their own section
    (`restorations`).
    """
    tokens = {
        (line.no, token.index): token.text
        for line in l1_lines
        for token in line.tokens
    }
    out: dict[str, set[tuple[str, ...]]] = {}
    for line in l2_lines:
        if line_range is not None and not (line_range[0] <= line.no <= line_range[1]):
            continue
        grouped: dict[int, list[str]] = {}
        for entry in line.entries:
            grouped.setdefault(entry.l1_index, []).append(entry.text)
        for l1_index, parts in grouped.items():
            token = tokens.get((line.no, l1_index))
            if token is None or not is_splittable(token):
                continue
            reading = (token,) if len(parts) == 1 else tuple(parts)
            out.setdefault(wordform_key(token), set()).add(reading)
    return {key: tuple(sorted(readings)) for key, readings in out.items()}


def _aligned_rows(
    l1_lines: Sequence[L1Line],
    l2_lines: Sequence[L2Line],
    morph_rows: Mapping[int, Sequence[object]],
    *,
    line_range: tuple[int, int] | None = None,
):
    """Every compared position, yielded as `(line, token, our entries, morph row)`.

    The pairing is purely positional — this line's *n*-th splittable L1 token against old
    Layer 2's *n*-th row for that line, uniformly, with no notion of "first occurrence" —
    and it is the one pairing both the split check and the POS check use, so the per-line
    view and the tables can never be reading different positions.
    """
    l2_by_line = {line.no: line for line in l2_lines}
    for line in l1_lines:
        if line_range is not None and not (line_range[0] <= line.no <= line_range[1]):
            continue
        l2_line = l2_by_line.get(line.no)
        grouped: dict[int, list[L2Entry]] = {}
        if l2_line is not None:
            for entry in l2_line.entries:
                grouped.setdefault(entry.l1_index, []).append(entry)
        rows_iter = iter(morph_rows.get(line.no, ()))
        for token in line.tokens:
            if not is_splittable(token.text):
                continue
            yield line, token, grouped.get(token.index, []), next(rows_iter, None)


def readings_agree(ours: Sequence[str], theirs: Sequence[str]) -> bool:
    """Do two readings of one token say the same thing about how it splits?

    Same number of words, and each word either identical or one side's restoration of the
    other — `dei` against old Layer 2's `de'`, our `far`+`ne` against its lemma `fare`+`ne`.
    Putting letters back is not a disagreement about the split, and this check is only about
    the split; the restorations themselves are listed by `restorations`, and the tags by
    `check_pos_against_precedent`.
    """
    if len(ours) != len(theirs):
        return False
    return all(
        wordform_key(mine) == wordform_key(other)
        or is_restoration(other, mine)
        or is_restoration(mine, other)
        for mine, other in zip(ours, theirs)
    )


def restorations(
    l1_lines: Sequence[L1Line],
    l2_lines: Sequence[L2Line],
    *,
    line_range: tuple[int, int] | None = None,
) -> list[tuple[int, str, str]]:
    """`(line, token, restored)` for every token this artifact put letters back into.

    Only tokens that stayed one grammatical word: inside a split there is no per-part
    surface to compare against, so `far` -> `fare` inside `farne` is invisible here and
    shows up, if anywhere, as agreement with old Layer 2's lemma column instead.
    """
    out: list[tuple[int, str, str]] = []
    l2_by_line = {line.no: line for line in l2_lines}
    for line in l1_lines:
        if line_range is not None and not (line_range[0] <= line.no <= line_range[1]):
            continue
        l2_line = l2_by_line.get(line.no)
        if l2_line is None:
            continue
        grouped: dict[int, list[L2Entry]] = {}
        for entry in l2_line.entries:
            grouped.setdefault(entry.l1_index, []).append(entry)
        for token in line.tokens:
            entries = grouped.get(token.index, [])
            if len(entries) != 1:
                continue
            if entries[0].text != token.text:
                out.append((line.no, token.text, entries[0].text))
    return out


def _positionally_mismatched_wordforms(
    l1_lines: Sequence[L1Line],
    l2_lines: Sequence[L2Line],
    morph_rows: Mapping[int, Sequence[object]],
    *,
    line_range: tuple[int, int] | None = None,
) -> set[str]:
    """Wordforms with at least one occurrence whose split, matched positionally to old
    Layer 2's row for the same place in the line, disagrees with it. A wordform this
    artifact answers two ways is only in here if one of those answers is the one that lost
    that positional comparison — never for two readings that each agree with old Layer 2 at
    their own position (a `di`/`a`-style case-folding artifact of pooling by wordform, not
    a real disagreement).
    """
    mismatched: set[str] = set()
    for _line, token, entries, row in _aligned_rows(
        l1_lines, l2_lines, morph_rows, line_range=line_range
    ):
        if row is None:
            continue
        parts = tuple(entry.text for entry in entries) or (token.text,)
        if not readings_agree(parts, _row_reading(row)):
            mismatched.add(wordform_key(token.text))
    return mismatched


def check_pos_against_precedent(
    l1_lines: Sequence[L1Line],
    l2_lines: Sequence[L2Line],
    morph_rows: Mapping[int, Sequence[object]],
    *,
    line_range: tuple[int, int] | None = None,
) -> tuple[int, list[PosMismatch]]:
    """`(positions compared, the ones whose coarse tags disagree)`.

    Only positions where the two sides split the token the same way are compared: where the
    splits differ the tags describe different words, and reporting that as a POS
    disagreement would count one finding twice. Old Layer 2's tag is folded through
    `COARSE_POS` first, so `proper noun` against `noun` is agreement and only a real
    difference of category — the participle read as an adjective, `che` read as a
    conjunction — is reported.
    """
    compared = 0
    out: list[PosMismatch] = []
    for line, token, entries, row in _aligned_rows(
        l1_lines, l2_lines, morph_rows, line_range=line_range
    ):
        if row is None or not entries:
            continue
        ours = tuple(entry.pos.casefold() for entry in entries)
        if not all(ours):
            continue
        parts = tuple(entry.text for entry in entries)
        if not readings_agree(parts, _row_reading(row)):
            continue
        theirs = coarse_pos(str(getattr(row, "pos", "") or ""))
        if len(theirs) != len(ours):
            continue
        compared += 1
        if ours != theirs:
            out.append(
                PosMismatch(line=line.no, word=token.text, ours=ours, theirs=theirs)
            )
    return compared, out


def check_against_precedent(
    l1_lines: Sequence[L1Line],
    l2_lines: Sequence[L2Line],
    morph_rows: Mapping[int, Sequence[object]],
    *,
    line_range: tuple[int, int] | None = None,
) -> list[PrecedentRow]:
    """Diff this artifact's splits against old Layer 2's, wordform by wordform.

    Two verdicts are properties of one side alone, checked before `differs`, each
    case-folded so `A`/`a` never count as two readings:

    - **`l2-ambiguous`**: this wordform's own readings, in this artifact, are genuinely
      distinct somewhere in `line_range` — independent of whether either of them agrees with
      old Layer 2 at its own position, so a wordform this artifact correctly reads two
      different ways in two different contexts is `l2-ambiguous` even where old Layer 2 agrees
      with both.
    - **`layer2-ambiguous`**: symmetric, but old Layer 2's own readings for the wordform are
      the ones genuinely distinct within the same `line_range` — visible because both readings
      are positions this run actually compared, not old Layer 2 disagreeing with itself
      somewhere this artifact never looked.

    `differs` is what is left once both are ruled out: neither side is internally ambiguous, but
    `_positionally_mismatched_wordforms` finds a real disagreement at an actual position — the
    same pairing `render_check_lines` marks with `[...]`.
    """
    ours = our_splits(l1_lines, l2_lines, line_range=line_range)
    theirs = precedent_splits(morph_rows, line_range)
    mismatched = _positionally_mismatched_wordforms(
        l1_lines, l2_lines, morph_rows, line_range=line_range
    )
    rows: list[PrecedentRow] = []
    for key in sorted(set(ours) | set(theirs)):
        mine = ours.get(key, ())
        readings = theirs.get(key, ())
        if not mine or not readings:
            verdict = "absent"
        elif len({_fold(reading) for reading in mine}) > 1:
            verdict = "l2-ambiguous"
        elif len({_fold(reading) for reading in readings}) > 1:
            verdict = "layer2-ambiguous"
        elif key in mismatched:
            verdict = "differs"
        else:
            verdict = "agrees"
        rows.append(
            PrecedentRow(wordform=key, ours=mine, theirs=readings, verdict=verdict)
        )
    return rows


# --- Reporting: the two faces of one aggregate (`ARCHITECTURE.md` §6) -----------------------


# A step slower than this is worth counting separately — the benchmark standard
# `ARCHITECTURE.md` §4 names. Nothing here is gated on it; it is a measurement.
SLOW_STEP_SECONDS = 300.0


@dataclass
class L2Report:
    """Aggregates the streamed `chunk` records; ships `metrics()` and `summary()`.

    Fed from exactly the records the log carries, so the machine-readable metrics in the
    summary record and the human-readable text the CLI prints are two renderings of one
    aggregate and cannot drift from each other or from the log (`ARCHITECTURE.md` §6).
    """

    chunks: int = 0
    settled_chunks: int = 0
    unresolved_chunks: int = 0
    fallback_chunks: int = 0
    skipped_chunks: int = 0
    skipped_lines: list[int] = field(default_factory=list)
    unresolved_lines: list[int] = field(default_factory=list)
    tokens_answered: int = 0
    split: int = 0
    restored: int = 0
    conflicts: list[dict] = field(default_factory=list)
    attempts: int = 0
    refusals: int = 0
    step_seconds: list[float] = field(default_factory=list)
    api_retries: int = 0
    api_retry_seconds: float = 0.0
    wordforms: int = 0
    l1_tokens: int = 0
    l2_entries: int = 0
    tags: dict[str, int] = field(default_factory=dict)
    context: dict = field(default_factory=dict)

    def add_chunk(self, record: dict) -> None:
        self.chunks += 1
        self.fallback_chunks += int(bool(record.get("fallback")))
        if record.get("resolved"):
            self.settled_chunks += 1
            # A settled chunk answers for every one of its lines; a group that failed and
            # was then retried line by line clears its own lines when those retries settle.
            answered = set(record.get("lines") or [])
            self.unresolved_lines = [
                no for no in self.unresolved_lines if no not in answered
            ]
            # Only a settled chunk's tokens have an answer; a refused group's tokens are
            # counted when its line-by-line retries settle, so nothing is counted twice.
            self.tokens_answered += int(record.get("tokens") or 0)
            self.split += int(record.get("splits") or 0)
            for answer in record.get("answers") or []:
                parts = answer.get("parts") or []
                # A word put back together: one grammatical word, spelled fuller than the
                # token. Inside a split there is no per-part surface to compare against.
                if len(parts) == 1 and parts[0] != answer.get("word"):
                    self.restored += 1
                for tag in answer.get("pos") or []:
                    self.tags[tag] = self.tags.get(tag, 0) + 1
        else:
            self.unresolved_chunks += 1
            self.unresolved_lines.extend(record.get("lines") or [])
        self.conflicts.extend(record.get("conflicts") or [])
        attempts = record.get("attempts") or []
        self.attempts += len(attempts)
        self.refusals += sum(1 for a in attempts if not a.get("accepted"))
        seconds = record.get("seconds")
        if seconds is not None:
            self.step_seconds.append(float(seconds))

    def add_skipped(self, record: dict) -> None:
        """A chunk the artifact already answers: counted, never a request, never an
        attempt. It is not a settled chunk — nothing was asked — so it stays out of the
        request and token figures, which describe *this* run and not the file."""
        self.skipped_chunks += 1
        self.skipped_lines.extend(record.get("lines") or [])

    def add_retries(self, delta) -> None:
        """§4 make-the-invisible-measurable: 429 backoffs, when a status line saw them."""
        if delta is None:
            return
        count, seconds = delta
        self.api_retries += int(count)
        self.api_retry_seconds += float(seconds)

    def metrics(self) -> dict:
        total = sum(self.step_seconds)
        return {
            **self.context,
            "chunks": self.chunks,
            "settled_chunks": self.settled_chunks,
            "unresolved_chunks": self.unresolved_chunks,
            "fallback_chunks": self.fallback_chunks,
            "skipped_chunks": self.skipped_chunks,
            "skipped_lines": sorted(set(self.skipped_lines)),
            "unresolved_lines": sorted(set(self.unresolved_lines)),
            "tokens_answered": self.tokens_answered,
            "split": self.split,
            "restored": self.restored,
            "passed_through": self.tokens_answered - self.split,
            "conflicts": list(self.conflicts),
            "attempts": self.attempts,
            "refusals": self.refusals,
            "wordforms": self.wordforms,
            "l1_tokens": self.l1_tokens,
            "l2_entries": self.l2_entries,
            "tags": dict(sorted(self.tags.items(), key=lambda kv: (-kv[1], kv[0]))),
            # Summed per-step seconds, never a start-to-end wall span: an interrupted
            # run's span is meaningless and idle gaps must not count (§5).
            "step_seconds_total": round(total, 1),
            "step_seconds_mean": (
                round(total / len(self.step_seconds), 1) if self.step_seconds else None
            ),
            "step_seconds_max": (
                round(max(self.step_seconds), 1) if self.step_seconds else None
            ),
            "slow_steps": sum(1 for s in self.step_seconds if s >= SLOW_STEP_SECONDS),
            "api_retries": self.api_retries,
            "api_retry_seconds": round(self.api_retry_seconds, 1),
        }

    def summary(self) -> str:
        m = self.metrics()
        gate = "PASS" if not m["unresolved_lines"] else "FAIL"
        tags = ", ".join(f"{tag} {count}" for tag, count in m["tags"].items()) or "none"
        lines = [
            f"chunks: {m['chunks']} — {m['settled_chunks']} settled, "
            f"{m['unresolved_chunks']} refused, {m['fallback_chunks']} line-by-line "
            f"after a group failed, {m['skipped_chunks']} already in the artifact "
            f"({len(m['skipped_lines'])} line(s))",
            f"tokens: {m['tokens_answered']} answered — {m['split']} split, "
            f"{m['passed_through']} left whole ({m['restored']} of them restored); "
            f"{m['wordforms']} distinct wordforms, "
            f"{len(m['conflicts'])} answered two ways",
            f"terminals: {m['l1_tokens']} L1 tokens -> {m['l2_entries']} L2 entries "
            f"(+{m['l2_entries'] - m['l1_tokens']})",
            f"tags: {tags}",
            f"lines with no answer: {len(m['unresolved_lines'])} "
            f"(gate == 0 lines: {gate})",
            f"requests: {m['attempts']} attempts, {m['refusals']} refused",
            f"seconds: {m['step_seconds_total']} total / "
            f"{m['step_seconds_mean']} mean / {m['step_seconds_max']} max, "
            f"{m['slow_steps']} slower than {SLOW_STEP_SECONDS:.0f}s",
            f"api retries: {m['api_retries']} ({m['api_retry_seconds']}s backoff)",
        ]
        return "\n".join(lines)


# --- CLI ------------------------------------------------------------------------------------


def _parse_range(spec: str) -> tuple[int, int]:
    start, _, end = spec.partition("-")
    return (int(start), int(end or start))


def _system_prompt() -> str:
    from dante_corpus.harness.skills import Skill

    skill = Skill.load(SKILL_DIR)
    return "\n\n".join([skill.body, skill.resource("answer.md")])


def _skill_digest() -> str:
    from dante_corpus.harness.skills import Skill

    return Skill.load(SKILL_DIR).digest()


def _row_reading(row: object) -> tuple[str, ...]:
    """Old Layer 2's split for one morph row: `+` in `lemma` means composite, else the word."""
    lemma = str(getattr(row, "lemma", "") or "")
    word = str(getattr(row, "word", "") or "")
    return tuple(lemma.split("+")) if "+" in lemma else (word,)


def render_check_lines(
    l1_lines: Sequence[L1Line],
    l2_lines: Sequence[L2Line],
    morph_rows: Mapping[int, Sequence[object]],
    *,
    line_range: tuple[int, int] | None = None,
) -> str:
    """One line per source line with at least one mismatch, tokens joined by a plain space
    (punctuation untouched); a line where every token agrees is omitted.

    A token this artifact splits shows its reading as `word(parts)`. A `[...]` is appended when
    *this exact occurrence* differs from old Layer 2 at the same position — matched purely by
    position (`_aligned_rows`) and compared by `readings_agree`, so putting letters back is not
    a difference but a different split is. Old Layer 2 has no row for punctuation, so its rows
    are zipped against this line's splittable tokens only. Tags and restorations are not shown
    here — each has its own section, and a line is listed here only for a split disagreement.
    """
    l2_by_line = {line.no: line for line in l2_lines}
    theirs_by_position = {
        (line.no, token.index): _row_reading(row)
        for line, token, _entries, row in _aligned_rows(
            l1_lines, l2_lines, morph_rows, line_range=line_range
        )
        if row is not None
    }
    out: list[str] = []
    for line in l1_lines:
        if line_range is not None and not (line_range[0] <= line.no <= line_range[1]):
            continue
        l2_line = l2_by_line.get(line.no)
        grouped: dict[int, list[str]] = {}
        if l2_line is not None:
            for entry in l2_line.entries:
                grouped.setdefault(entry.l1_index, []).append(entry.text)
        pieces: list[str] = []
        mismatch = False
        for token in line.tokens:
            parts = tuple(grouped.get(token.index, [token.text]))
            piece = token.text
            if len(parts) > 1:
                piece += f"({' '.join(parts)})"
            theirs = theirs_by_position.get((line.no, token.index))
            if theirs is not None and not readings_agree(parts, theirs):
                piece += f"[{'+'.join(theirs)}]"
                mismatch = True
            pieces.append(piece)
        if mismatch:
            out.append(f"{line.no:3d} {' '.join(pieces)}")
    return "\n".join(out)


def _run_check(args, canticle: str, number: int, l1_lines, line_range) -> int:
    from dante_corpus.morph import load_morph

    path = Path(args.out) if args.out else artifact_path(canticle, number)
    if not path.is_file():
        print(f"no artifact at {path} — run the pass first")
        return 1
    l2_lines = parse_artifact(path.read_text(encoding="utf-8"))
    if not l2_lines:
        print(f"nothing to check in {path} — it holds no {len(ARTIFACT_HEADER)}-column row")
        return 1
    morph_rows = load_morph(canticle, number)
    rows = check_against_precedent(l1_lines, l2_lines, morph_rows, line_range=line_range)
    print(render_check_lines(l1_lines, l2_lines, morph_rows, line_range=line_range))
    print("\nword(parts) = this artifact's split   [...] = old Layer 2's reading, where it differs\n")
    surface = {
        wordform_key(token.text): token.text
        for line in l1_lines
        for token in line.tokens
    }
    counts: dict[str, int] = {}
    for row in rows:
        counts[row.verdict] = counts.get(row.verdict, 0) + 1

    differs_rows = [row for row in rows if row.verdict == "differs"]
    if differs_rows:
        print("[differs]")
        print(f"{'wordform':<14}{'L2':<22}old Layer 2")
        for row in differs_rows:
            shown = surface.get(row.wordform, row.wordform)
            l2_text = " / ".join("+".join(reading) for reading in row.ours)
            theirs_text = " / ".join("+".join(reading) for reading in row.theirs)
            print(f"{shown:<14}{l2_text:<22}{theirs_text}")
        print()

    for label, verdict, attribute in (
        ("L2 ambiguous", "l2-ambiguous", "ours"),
        ("Layer 2 ambiguous", "layer2-ambiguous", "theirs"),
    ):
        ambiguous_rows = [row for row in rows if row.verdict == verdict]
        if not ambiguous_rows:
            continue
        print(f"[{label}]")
        for row in ambiguous_rows:
            shown = surface.get(row.wordform, row.wordform)
            readings = ", ".join(" ".join(reading) for reading in getattr(row, attribute))
            print(f"{shown}: {readings}")
        print()

    for verdict in ("agrees", "differs", "l2-ambiguous", "layer2-ambiguous", "absent"):
        print(f"{verdict:<22}{counts.get(verdict, 0)}")

    restored = restorations(l1_lines, l2_lines, line_range=line_range)
    if restored:
        print()
        print("[restored]  (tokens that stayed one word and had letters put back)")
        seen: dict[tuple[str, str], int] = {}
        for _line, token, form in restored:
            seen[(token, form)] = seen.get((token, form), 0) + 1
        for (token, form), count in sorted(seen.items()):
            print(f"{token:<14}-> {form}" + (f"  ({count})" if count > 1 else ""))
        print(f"\n{'restored':<22}{len(restored)} position(s), {len(seen)} distinct")

    compared, mismatches = check_pos_against_precedent(
        l1_lines, l2_lines, morph_rows, line_range=line_range
    )
    print()
    if mismatches:
        print("[pos differs]  (positions where both sides split the token the same way)")
        print(f"{'line':<6}{'word':<14}{'L2':<22}old Layer 2")
        for item in mismatches:
            print(
                f"{item.line:<6}{item.word:<14}"
                f"{'+'.join(item.ours):<22}{'+'.join(item.theirs)}"
            )
        print()
    print(f"{'pos agrees':<22}{compared - len(mismatches)} of {compared} position(s) compared")
    print(
        "\n'differs' rows are evidence for one of L2.md's two non-agreement outcomes "
        "(precedent-is-wrong / genuine ambiguity); which one is a judgment for L2.md, "
        "not for this checker."
    )
    return 0


def _selected_lines(canticle: str, number: int, line_range) -> list[L1Line]:
    """The canto's L1 lines a `--lines` filter selects; all of them when it is `None`."""
    return [
        line
        for line in l1_canto(canticle, number)
        if line_range is None or line_range[0] <= line.no <= line_range[1]
    ]


def _main(argv=None) -> int:
    import argparse
    import sys

    from dante_corpus import api

    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    # The corpus's own driver shape (`skel/skel.py`, `dep/dep.py`): canticles positional,
    # `-c` a canto *spec* rather than a number — `12-`, `-20`, `1,3-5,11-` — resolved by
    # `api.select_cantos` against the cantos the canticle actually has. A canticle's
    # length and a canto's are both facts of the corpus, so neither is asked for.
    parser.add_argument("canticles", nargs="+", help="canticle names, e.g. inferno")
    parser.add_argument("-c", "--canto", metavar="SPEC", help=api.CANTO_SPEC_HELP)
    parser.add_argument("-l", "--lines", default=None,
                        help="line range within a single canto, e.g. '1-9' or '10' "
                             "(default: the whole canto)")
    parser.add_argument("-m", "--model", default=DEFAULT_MODEL,
                        help=f"LLM, e.g. {DEFAULT_MODEL} (the default)")
    parser.add_argument("--temperature", type=float, default=None)
    parser.add_argument("--chunk", type=int, default=CHUNK_SIZE,
                        help=f"lines per request (default {CHUNK_SIZE}, old Layer 2's)")
    parser.add_argument("--max-iterations", type=int, default=MAX_ITERATIONS)
    parser.add_argument("-o", "--out", help="artifact TSV (default: layers/l2/<canticle>/NN.tsv)")
    parser.add_argument("--force", action="store_true",
                        help="ask again from the first line, ignoring what the artifact "
                             "already answers (default: resume, skipping those chunks)")
    parser.add_argument("--log", action=argparse.BooleanOptionalAction, default=True,
                        help="write each canto's streaming JSONL log beside its artifact, "
                             "same path with .log, e.g. layers/l2/<canticle>/NN.log "
                             "(default: enabled)")
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--started-at", type=float, default=None,
                        help="unix time the enclosing run began, for the bar's run clock")
    parser.add_argument("--check", action="store_true",
                        help="offline: diff an existing artifact against old Layer 2")
    args = parser.parse_args(argv)

    if err := api.check_canto_spec(args.canticles, args.canto):
        parser.error(err)
    targets = [
        (canticle, number)
        for canticle in args.canticles
        for number in api.select_cantos(canticle, args.canto)
    ]

    # A canto's length is its own; a range asked for by default would have to be
    # looked up per canto, so the default is the canto itself and `None` means
    # exactly that everywhere below (`our_splits`, `precedent_splits`). For the same
    # reason a line range only means anything against one canto.
    line_range = _parse_range(args.lines) if args.lines else None
    if line_range is not None and (line_range[0] > line_range[1] or line_range[0] < 1):
        parser.error(f"--lines {args.lines!r} is not a range")
    if line_range is not None and len(targets) != 1:
        parser.error("--lines applies to one canto; narrow -c")
    if args.out and len(targets) != 1:
        parser.error("--out names one file; narrow -c")
    if args.max_iterations < 1:
        parser.error("--max-iterations must be >= 1")
    if args.chunk < 1:
        parser.error("--chunk must be >= 1")

    if args.check:
        status = 0
        for canticle, number in targets:
            l1_lines = _selected_lines(canticle, number, line_range)
            if len(targets) > 1:
                print(f"== {canticle} {number} ==")
            status |= _run_check(args, canticle, number, l1_lines, line_range)
        return status

    from dante_corpus.harness.llm import llm7shi_generate
    from dante_corpus.harness.statusline import HarnessStatusLine

    status_line = HarnessStatusLine() if HarnessStatusLine is not None else None
    if status_line is not None and args.started_at is not None:
        status_line.run_started_at = args.started_at
    # §4: the display's stream is shared with llm7shi, so streamed model output
    # coexists with the bar instead of clobbering it. Without the extra installed
    # there is no bar and everything falls back to plain stderr.
    ui_stream = status_line.stream if status_line is not None else sys.stderr

    # The log follows the artifact, one per canto: a run over several cantos would
    # otherwise pour every canto's records into whichever single file the command
    # line happened to name. `_LogRelay` is what lets the adapter keep one `generate`
    # across the run while each canto's records land in its own file.
    relay = _LogRelay() if args.log else None
    generate = llm7shi_generate(
        model=args.model,
        temperature=args.temperature,
        quiet=not args.verbose,
        file=ui_stream,
        request_log=relay,
    )
    status = 0
    for index, (canticle, number) in enumerate(targets, start=1):
        status |= _build_canto(
            args,
            canticle,
            number,
            index,
            len(targets),
            line_range=line_range,
            generate=generate,
            relay=relay,
            ui_stream=ui_stream,
            status_line=status_line,
        )
    return status


class _LogRelay:
    """A write/flush sink that forwards to whichever canto's log is open right now.

    `llm7shi_generate` takes its `request_log` once, at construction; the log changes
    per canto. Handing it this relay keeps the adapter — and its pacing state — one
    object for the whole run.
    """

    def __init__(self) -> None:
        self.sink = None

    def write(self, text: str) -> None:
        if self.sink is not None:
            self.sink.write(text)

    def flush(self) -> None:
        if self.sink is not None:
            self.sink.flush()


def _build_canto(
    args,
    canticle: str,
    number: int,
    index: int,
    total: int,
    *,
    line_range,
    generate,
    relay,
    ui_stream,
    status_line,
) -> int:
    """One canto's pass: its own artifact, its own log, its own bar and summary.

    The run's shared things — the model adapter and the status line — are passed in; the
    log is not, because it belongs to the artifact: `NN.tsv`'s records go to `NN.log`
    beside it.
    """
    import sys
    from contextlib import nullcontext

    from dante_corpus.harness.pipeline import (
        progress_separator,
        retry_delta,
        retry_snapshot,
    )

    l1_lines = _selected_lines(canticle, number, line_range)
    if not l1_lines:
        print(f"{canticle} {number}: no lines to build", file=sys.stderr)
        return 1
    # What the run actually covers, for the log and the header: the range asked for
    # is a filter, the lines are the fact.
    line_span = (min(line.no for line in l1_lines), max(line.no for line in l1_lines))
    out_path = Path(args.out) if args.out else artifact_path(canticle, number)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    wordforms = distinct_wordforms(l1_lines)
    label = f"{canticle} {number}"
    # `ARCHITECTURE.md` §0's interruption resilience: a canto is ~46 chunks and a dozen
    # minutes, so a run interrupted part-way must not have to buy its answered lines
    # again. What is on disk is read back and every chunk it already answers is skipped;
    # `--force` is how a run is made to ask again from the first line.
    existing = out_path.is_file() and not args.force
    done = (
        {line.no: line for line in parse_artifact(out_path.read_text(encoding="utf-8"))}
        if existing
        else {}
    )
    if existing and not done:
        print(
            f"{out_path}: no row this pass can read back (a split-only artifact has no "
            f"pos column) — asking from the first line",
            file=sys.stderr,
        )
    # The log follows the artifact — `NN.tsv` -> `NN.log` — and §5's resume-or-truncate
    # choice, which is about this file, is **append, always** (operator, 2026-09-09):
    # truncating would erase exactly the records worth keeping, an attempt that failed
    # and the attempt that then fixed it. Nothing but an explicit delete shortens this
    # file, `--force` included. A file therefore holds several `summary` records, one
    # per attempt at the canto; the last one is the current state.
    log_path = out_path.with_suffix(".log") if args.log else None
    sink = open(log_path, "a", encoding="utf-8") if log_path is not None else None
    if relay is not None:
        relay.sink = sink

    report = L2Report(
        context={
            "record": "summary",
            "canticle": canticle,
            "canto": number,
            "line_start": line_span[0],
            "line_end": line_span[1],
            "model": args.model,
            "skill_digest": _skill_digest(),
        }
    )
    report.l1_tokens = sum(len(line.tokens) for line in l1_lines)
    report.wordforms = len(wordforms)
    planned = chunks(l1_lines, args.chunk)
    results: list[ChunkResult] = []

    try:
        # §4's major separator names the corpus position; §9's header line, right
        # under it, announces what the run is about to do. Keeping the counts off
        # the separator keeps it one line at any console width.
        progress_separator(
            f"{label} lines {line_span[0]}-{line_span[1]}", index, total, stream=ui_stream
        )
        pending = sum(1 for chunk in planned if not all(line.no in done for line in chunk))
        print(
            f"[l2-words] {report.l1_tokens} L1 tokens, {len(wordforms)} distinct "
            f"wordforms, {pending} of {len(planned)} chunk(s) of {args.chunk} line(s) "
            f"to ask ({len(planned) - pending} already in the artifact), "
            f"model={args.model}, max {args.max_iterations} attempt(s) each",
            file=ui_stream,
            flush=True,
        )
        retries_before = retry_snapshot(status_line)

        # One bar for this canto, labelled by its corpus position, its numerator walking
        # this canto's Dante lines as each chunk settles — the `skel/`-driver pattern
        # §4 names. `[index/total]` separators keep whole-run positions.
        settled_lines: set[int] = set()
        # Written back to `out_path` after every chunk, settled or skipped, so an
        # interrupted run's answers up to that point are already on disk — not just in
        # the log — rather than only at the very end.
        line_by_no = {line.no: line for line in l1_lines}
        built: dict[int, L2Line] = {}

        def flush_artifact() -> None:
            out_path.write_text(
                render_artifact([built[line.no] for line in l1_lines if line.no in built]),
                encoding="utf-8",
            )

        bar = (
            status_line.progress(len(l1_lines), label=label)
            if status_line is not None
            else nullcontext()
        )
        with bar as progress:
            def settled(result: ChunkResult) -> None:
                results.append(result)
                record = result.to_dict()
                report.add_chunk(record)
                positions = result.positions()
                for line_no in result.lines:
                    built[line_no] = apply_analyses(line_by_no[line_no], positions)
                flush_artifact()
                span = (
                    f"{result.lines[0]}-{result.lines[-1]}"
                    if len(result.lines) > 1 else f"{result.lines[0]}"
                )
                if result.accepted:
                    settled_lines.update(result.lines)
                    found = (
                        ", ".join(
                            f"{token.text}={'+'.join(analysis.parts)}"
                            for token, analysis in result.pairs()
                            if analysis.split
                        )
                        or "nothing splits"
                    )
                    mark = found + (" [line-by-line]" if result.fallback else "")
                else:
                    mark = f"REFUSED ({result.stop_reason})"
                print(
                    f"[{len(results)}] lines {span}: {mark}  "
                    f"({result.seconds:.1f}s, {len(result.attempts)} attempt(s))",
                    file=ui_stream,
                    flush=True,
                )
                if progress is not None:
                    progress.update(len(settled_lines))
                if sink is not None:
                    sink.write(json.dumps(record, ensure_ascii=False) + "\n")
                    sink.flush()

            def skipped(chunk: Sequence[L1Line]) -> None:
                record = {
                    "record": "chunk",
                    "lines": [line.no for line in chunk],
                    "skipped": True,
                }
                report.add_skipped(record)
                for line in chunk:
                    built[line.no] = done[line.no]
                flush_artifact()
                settled_lines.update(record["lines"])
                if progress is not None:
                    progress.update(len(settled_lines))
                if sink is not None:
                    sink.write(json.dumps(record, ensure_ascii=False) + "\n")
                    sink.flush()

            analyses = build_l2(
                l1_lines,
                generate=generate,
                system_prompt=_system_prompt(),
                chunk_size=args.chunk,
                max_iterations=args.max_iterations,
                on_settled=settled,
                already_answered=lambda chunk: all(line.no in done for line in chunk),
                on_skipped=skipped,
            )
        report.add_retries(retry_delta(retries_before, status_line))

        # A skipped line keeps the entries the artifact already holds, verbatim: this run
        # never asked about it, so `analyses` says nothing about it and applying them would
        # silently un-split it. Every other line is built from this run's answers.
        kept = set(report.skipped_lines)
        l2_lines = [
            done[line.no] if line.no in kept else apply_analyses(line, analyses)
            for line in l1_lines
        ]
        report.l2_entries = sum(len(line.entries) for line in l2_lines)
        out_path.write_text(render_artifact(l2_lines), encoding="utf-8")

        if sink is not None:
            sink.write(json.dumps(report.metrics(), ensure_ascii=False) + "\n")
            sink.flush()

        print(f"artifact written to {out_path}", file=sys.stderr)
        print(report.summary(), file=sys.stderr)
        metrics = report.metrics()
        for no in metrics["unresolved_lines"]:
            print(f"NO ANSWER: line {no} — its tokens pass through untagged", file=sys.stderr)
        for conflict in metrics["conflicts"]:
            first = "+".join(conflict["first"]["parts"])
            here = "+".join(conflict["here"]["parts"])
            first_pos = "+".join(conflict["first"]["pos"])
            here_pos = "+".join(conflict["here"]["pos"])
            print(
                f"TWO READINGS: {conflict['word']} was {first} ({first_pos}) earlier and "
                f"{here} ({here_pos}) at line {conflict['line']}; both stand",
                file=sys.stderr,
            )
    finally:
        if relay is not None:
            relay.sink = None
        if sink is not None:
            sink.close()
    if log_path is not None:
        print(f"records written to {log_path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
