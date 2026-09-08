"""Generation 2, Layer 2, step 1: the split — L1 tokens to grammatical words.

`L2.md`: L2 is an ordered list of `(l1_index, text)` pairs. A composite L1 token produces
several L2 entries sharing one `l1_index` (1:many); every other L1 token, punctuation
included, carries straight through as exactly one entry (1:1). L2 **only splits** — a
many:1 merge (old Layer 4's `fixed`) stays a relation one layer up, over L2 entries, so
`l1_index` is always a single integer and never a tuple.

L2's full design is a three-pass pipeline — split, then POS, then normalize — in that order
and never entangled. **This module is step 1 only.** Apocope and elision are step 3's
business: `ch'` stays `ch'`, `i'` stays `i'`, `cammin` stays `cammin`. Nothing here assigns
a part of speech or a lemma.

**What the model is asked, and what it is not shown.** One **chunk of lines** per step —
`--chunk`, default 3 — which is old Layer 2's own granularity (`morph/morph.py`'s
`--chunk 3`, "a Markdown word table per chunk of lines"). `L2.md`'s *Execution mechanism*
argued for one wordform per step; **that is overridden** (operator, 2026-09-09): a wordform
is too small a unit to spend a request on, and at 442 wordforms corpus-wide the pass runs
into request-rate limits before it runs into anything interesting. The reason batching was
argued against — bundling several jobs into one answer — does not apply, because this is
still *one* job (split these tokens) asked over more material, not split-plus-POS-plus-
normalize merged into one request.

Answers stay **keyed by the word, never by an index** — the model answers `nel:in+il` and
the program attaches the `l1_index` from the token's own position, so getting the split
right and copying a number correctly are never bundled into one answer. The chunk's tokens
are listed for it, and it names **only the ones that split**: a token with no row is a
single word, which is the right answer for the large majority of them. A key that names two
places in the passage is refused with instructions to prefix it with the tokens that come
before it, which is also how a wordform that genuinely splits two ways in one passage gets
said (`per trattar del:di+il`).

**Why that differs from old Layer 2, precisely.** Not because tokens were unavailable then:
`tokenizer.tokenize()` predates both layers, and `morph.validate_line` already checks a
row against it. The difference is that `morph/morph.py`'s prompt shows the model only the
raw lines and asks it to *do the tokenizing* ("emit exactly one row per word … separate
words linked by an apostrophe into separate rows"), so the returned table has to be mapped
back onto the lines afterwards — `morph.split_table` substring-matches the `Word` column
into the line text with FIFO salvage at line boundaries, "tolerating LLM word transforms/
hallucinations", and `validate_line` reports the damage after the fact. Listing the tokens
in the request moves that from a tolerant post-hoc match to a gate the answer either passes
or is refused by.

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
the gate and the model's whole output is one `<split>` block, the same way Layer 5's is one
`<rows>` block.

The command line is the corpus's own driver shape (`skel/skel.py`, `dep/dep.py`):
canticles positional, `-c` a canto spec resolved by `api.select_cantos`, and every
selection a filter over what the corpus has rather than a count anyone has to know.

    uv run python -m layers.gen2.l2 inferno -m ...        # all of Inferno
    uv run python -m layers.gen2.l2 inferno -c 1 -m ...   # just canto 1
    uv run python -m layers.gen2.l2 inferno -c 12- -m ... # canto 12 on
    uv run python -m layers.gen2.l2 inferno -c 1 --lines 1-9 -m ...  # a line range
    uv run python -m layers.gen2.l2 inferno -c 1 -m ... --force  # ask again, from line 1
    uv run python -m layers.gen2.l2 inferno -c 1 -m ... --no-log  # no log at all
    uv run python -m layers.gen2.l2 inferno --check       # code-only, no model

A run **resumes**: the committed artifact is read back and a chunk every one of whose
lines it already answers is skipped before any request, its entries carried through
verbatim. `--force` is how a run is made to ask from the first line again.

The log is written **by default** and names no file: each canto's records go beside its
own artifact, `NN.tsv` to `NN.log`. A run whose numbers were never recorded cannot be
reported afterwards, and one named file could not hold a run over several cantos anyway.
`--no-log` turns it off.

**Bootstrap status (premise 3).** The running split reads L1 and nothing else: no old-layer
file is named as an input, and the model is shown no old Layer 2 row. Old Layer 2 enters
once, afterwards and offline, through `--check`, which diffs this artifact against
`morph/<canticle>/<NN>.tsv` and reports `L2.md`'s three outcomes (agrees /
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

# The split step's own model default. `dante_corpus.harness.llm.DEFAULT_MODEL` is the
# local Ollama build; this pass runs against the hosted one, where wall clock matters
# over 442 corpus-wide wordforms (`ARCHITECTURE.md` §3).
DEFAULT_MODEL = "google:gemma-4-31b-it"

# Lines per request — old Layer 2's own granularity (`morph/morph.py --chunk`, default 3).
# The unit of work, and therefore what a request costs and what one failure loses.
CHUNK_SIZE = 3

# How many times one chunk may be asked. A cost cap, not a target: a chunk that passes the
# gate stops at once, and one that never does degrades to line-by-line rather than being
# quietly defaulted to the identity split.
MAX_ITERATIONS = 3

MAX_PARTS = 3

SKILL_DIR = Path(__file__).resolve().parent / "skills" / "l2-split"

ARTIFACT_HEADER = ("line", "l1_index", "l2_index", "text")

_SPLIT_BLOCK = re.compile(r"<split>(.*?)</split>", re.DOTALL | re.IGNORECASE)


# --- The L2 objects ------------------------------------------------------------------


@dataclass(frozen=True)
class L2Entry:
    """One grammatical word, and the L1 token it came from."""

    l1_index: int
    text: str

    def to_dict(self) -> dict[str, object]:
        return {"l1_index": self.l1_index, "text": self.text}


@dataclass(frozen=True)
class L2Line:
    """A line's L2 entries in order. The L2 token number is the position in this list."""

    no: int
    entries: tuple[L2Entry, ...]

    def to_dict(self) -> dict[str, object]:
        return {"no": self.no, "entries": [entry.to_dict() for entry in self.entries]}


# --- Which wordforms the model is asked about ------------------------------------------


def is_splittable(token: str) -> bool:
    """Can this L1 token be a fusion of grammatical words at all?

    Only a token carrying a letter can. Punctuation never splits, and saying so here is a
    deterministic reading of L1's own output — not a fact borrowed from old Layer 2 — so it
    costs no model call and no premise.
    """
    return any(character.isalpha() for character in token)


def wordform_key(token: str) -> str:
    """The table's key for a token: case-folded, since `Nel` and `nel` split alike."""
    return token.casefold()


def distinct_wordforms(lines: Iterable[L1Line]) -> list[str]:
    """The splittable wordforms to ask about, in first-appearance order.

    The surface spelling of the first occurrence is what the model is shown — the key is
    case-folded, the question is not, because a word is asked about as it is written.
    """
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


# --- $\Sigma$: applying the splits ------------------------------------------------------

# Where a split applies: the token at `(line number, l1_index)`. Splits are recorded per
# occurrence rather than per wordform because a wordform can genuinely split two ways in
# the same passage (`nel` = `in+il` vs `ne+lo`), and a wordform-keyed table cannot hold
# both. The table `L2.md` describes is then what a corpus-wide run *derives* from these
# occurrences, with the disagreements visible instead of averaged away.
Position = tuple[int, int]


def apply_splits(line: L1Line, splits: Mapping[Position, Sequence[str]]) -> L2Line:
    """One line's L2, given the splits found for its tokens. Pure: no model, no I/O.

    A token with no split recorded passes through verbatim, original casing and apostrophe
    kept — which is also what an unanswered token gets, so a failed step degrades to the
    identity rather than to a hole in the line.
    """
    entries: list[L2Entry] = []
    for token in line.tokens:
        parts = splits.get((line.no, token.index))
        if not parts or len(parts) == 1:
            entries.append(L2Entry(l1_index=token.index, text=token.text))
            continue
        for part in parts:
            entries.append(L2Entry(l1_index=token.index, text=part))
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
    """The chunk's splittable tokens in L1 order — the rows the answer must have."""
    return [
        Asked(line=line.no, l1_index=token.index, text=token.text)
        for line in chunk
        for token in line.tokens
        if is_splittable(token.text)
    ]


# --- $O$: the question, and the gate on the answer -------------------------------------


def ask_message(chunk: Sequence[L1Line], *, refusal: str = "") -> str:
    """The single user message for one attempt at one chunk.

    The lines are shown for context and the tokens are listed so the model never has to
    re-tokenize — the token list is what fixes the boundaries (`ch'` and `i'` are two
    tokens, not one). The answer names **only the tokens that split**. Two shapes, and the
    wording says which, because the next move differs: a fresh question, and a refused
    answer to repair.
    """
    lines = "\n".join(f"{line.no} {line.text}" for line in chunk)
    tokens = " ".join(token.text for token in asked_tokens(chunk))
    parts = [
        f"<lines>\n{lines}\n</lines>",
        f"<tokens>\n{tokens}\n</tokens>",
    ]
    if refusal:
        parts.append(
            "<verdict>\n"
            "The check refused your last answer, so nothing was recorded. It reported:\n"
            f"- {refusal}\n"
            "Send the whole block again, corrected.\n"
            "</verdict>"
        )
    else:
        parts.append(
            "<verdict>\n"
            "Nothing is on record for these lines. Read every token above and list the "
            "ones that are several grammatical words written together. Tokens you do not "
            "list are recorded as single words, so an empty block means you found none.\n"
            "</verdict>"
        )
    return "\n\n".join(parts)


def locate_key(key: str, tokens: Sequence[Asked]) -> tuple[int, str]:
    """Which asked token a row's key names, or why it names none (or too many).

    A key is one token, or a run of consecutive tokens **ending with** the one being split
    — `del` normally, `trattar del` when a bare `del` would name two places. Returns
    `(index into tokens, error)`; a non-empty error means the caller refuses the answer.

    Requiring the run to be unique is what lets the answer carry differences only. A bare
    key matching two occurrences is refused rather than applied to both, because those two
    occurrences are exactly where a wordform can genuinely split two ways.
    """
    words = key.split()
    if not words:
        return -1, "a row with an empty key"
    span = len(words)
    hits = [
        start
        for start in range(len(tokens) - span + 1)
        if all(
            wordform_key(tokens[start + offset].text) == wordform_key(words[offset])
            for offset in range(span)
        )
    ]
    if not hits:
        return -1, (
            f"{key!r} is not a run of consecutive tokens in this passage; keys must be "
            "copied from the token list"
        )
    if len(hits) > 1:
        places = ", ".join(f"line {tokens[start + span - 1].line}" for start in hits)
        return -1, (
            f"{key!r} names {len(hits)} places ({places}); put the tokens that come "
            "before it in front of it until the key names exactly one"
        )
    return hits[0] + span - 1, ""


def parse_split_answer(
    text: str, *, tokens: Sequence[Asked]
) -> tuple[dict[int, list[str]], str]:
    """The `<split>` block's rows — **only the tokens that split** — or the gate's reason.

    Returns `(splits, error)` where `splits` maps an index into `tokens` to that token's
    grammatical words. A token with no row is a single word; an empty block means the
    passage holds no composite token at all. A non-empty `error` means nothing is recorded
    and the caller re-asks with it.

    Each key is resolved by `locate_key` against the tokens the request listed, so a key is
    either exactly one token of this passage or the answer is refused — there is no tolerant
    matching. Old Layer 2 needed `morph.split_table`'s substring matching with FIFO salvage
    because its prompt asked the model to tokenize as well as analyse; this one does not ask
    that, so it does not have to guess.

    **What listing differences only gives up, stated.** The previous contract — one row per
    token — proved the model had at least produced a judgment for every token. It cannot any
    more: an empty block is indistinguishable from a model that did not look. That is the
    price of not spending 27 rows to convey one fact, and the detector for it is `--check`
    against old Layer 2 after the fact, where a missed split shows up as `differs`.
    """
    matches = _SPLIT_BLOCK.findall(text or "")
    if not matches:
        return {}, "no <split> block in the answer"
    if len(matches) > 1:
        return {}, f"{len(matches)} <split> blocks in the answer; send exactly one"
    body = [
        line.strip()
        for line in matches[0].splitlines()
        if line.strip()
        and not line.strip().startswith(("#", "```"))
        and line.strip().casefold() not in ("none", "(none)", "-")
    ]
    splits: dict[int, list[str]] = {}
    for position, raw in enumerate(body, start=1):
        key, separator, value = raw.partition(":")
        if not separator:
            return {}, f"row {position} is not 'word:part+part' — no ':' in {raw!r}"
        key, value = key.strip(), value.strip()
        index, error = locate_key(key, tokens)
        if error:
            return {}, f"row {position}: {error}"
        token = tokens[index]
        if index in splits:
            return {}, (
                f"row {position} names {token.text!r} (line {token.line}) a second time; "
                "each token takes at most one row"
            )
        if not value:
            return {}, f"row {position} ({key!r}) has nothing after the ':'"
        parts = [part.strip() for part in value.split("+")]
        if any(not part for part in parts):
            return {}, f"row {position} ({key!r}): {value!r} has an empty part"
        if any(any(character.isspace() for character in part) for part in parts):
            return {}, f"row {position} ({key!r}): {value!r} has a space inside a part"
        if len(parts) < 2:
            return {}, (
                f"row {position} ({key!r}): {value!r} is one word, so the row says nothing "
                "— list only the tokens that split"
            )
        if len(parts) > MAX_PARTS:
            return {}, (
                f"row {position} ({key!r}): {value!r} has {len(parts)} parts; at most "
                f"{MAX_PARTS} are accepted"
            )
        splits[index] = parts
    return splits, ""


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
    """One chunk's settled answer, or the record of it never settling.

    `answers` holds only the tokens that split, keyed by index into `tokens`. "Settled with
    no answers" is a real and common outcome — a passage with no composite token — which is
    why acceptance is `accepted`, a fact about the gate, and not `bool(answers)`.
    """

    lines: list[int] = field(default_factory=list)
    tokens: list[Asked] = field(default_factory=list)
    answers: dict[int, list[str]] = field(default_factory=dict)
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
        return len(self.answers)

    @property
    def seconds(self) -> float:
        return sum(attempt.seconds for attempt in self.attempts)

    def pairs(self) -> list[tuple[Asked, list[str]]]:
        """The tokens that split, with their parts, in L1 order."""
        return [(self.tokens[index], self.answers[index]) for index in sorted(self.answers)]

    def positions(self) -> dict[Position, list[str]]:
        """The splits as `(line, l1_index) -> parts`, ready for `apply_splits`."""
        return {(token.line, token.l1_index): parts for token, parts in self.pairs()}

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
                 "parts": parts}
                for token, parts in self.pairs()
            ],
            "attempts": [attempt.to_dict() for attempt in self.attempts],
            "seconds": round(self.seconds, 3),
        }


def split_chunk(
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
        splits, error = parse_split_answer(answer, tokens=tokens)
        if error:
            result.attempts.append(
                AttemptRecord(attempt=attempt, kind=kind, accepted=False, error=error,
                              seconds=elapsed)
            )
            refusal = error
            continue
        result.attempts.append(
            AttemptRecord(attempt=attempt, kind=kind, accepted=True, rows=len(splits),
                          seconds=elapsed)
        )
        result.answers = splits
        result.accepted = True
        result.stop_reason = "settled"
        return result
    result.stop_reason = "budget" if result.attempts else "unanswered"
    return result


def build_splits(
    lines: Sequence[L1Line],
    *,
    generate: Callable[[list[dict]], str],
    system_prompt: str,
    chunk_size: int = CHUNK_SIZE,
    max_iterations: int = MAX_ITERATIONS,
    on_settled: Callable[[ChunkResult], None] | None = None,
    already_answered: Callable[[Sequence[L1Line]], bool] | None = None,
    on_skipped: Callable[[Sequence[L1Line]], None] | None = None,
) -> dict[Position, list[str]]:
    """Every split these lines contain, by position: one bounded step per chunk of lines.

    A chunk that never passes the gate is retried line by line — `morph.py`'s own
    degradation ("chunk failed, retrying line by line") — so one bad group costs its own
    lines, not the run.

    Splits are recorded **per occurrence**, so a wordform answered two ways in different
    passages keeps both. The first reading of a wordform is remembered only to notice the
    second: a later occurrence answered differently is recorded as a **conflict** on that
    chunk — the disagreement `L2.md` expects a handful of (`nel` = `in+il` vs `ne+lo`, old
    Layer 2's own `dimmi` noise) — and then applied as answered, because the model had that
    passage in front of it and this one is the reading it gave for *this* line.

    `on_settled` is called as each chunk settles, so the run's records reach disk when they
    settle rather than when the pass ends (`ARCHITECTURE.md` §5).

    `already_answered` is the resume test, asked once per chunk **before** any request: a
    chunk every one of whose lines the artifact already holds costs nothing and is reported
    through `on_skipped`. The chunk boundaries do not move when a run resumes — they are cut
    over all the lines selected, answered or not — so the chunk is the unit of resumption as
    well as of asking, and a chunk only *partly* on disk is asked again whole rather than
    half-asked. The caller keeps the answered lines' entries: this function returns splits
    only for what it asked about.
    """
    splits: dict[Position, list[str]] = {}
    first_reading: dict[str, list[str]] = {}

    def absorb(result: ChunkResult) -> None:
        for token, parts in result.pairs():
            key = wordform_key(token.text)
            seen = first_reading.setdefault(key, list(parts))
            if seen != parts:
                result.conflicts.append(
                    {"word": token.text, "line": token.line, "first": list(seen),
                     "here": list(parts)}
                )
            splits[(token.line, token.l1_index)] = list(parts)
        if on_settled is not None:
            on_settled(result)

    for chunk in chunks(lines, chunk_size):
        if already_answered is not None and already_answered(chunk):
            if on_skipped is not None:
                on_skipped(chunk)
            continue
        result = split_chunk(
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
                split_chunk(
                    (line,),
                    generate=generate,
                    system_prompt=system_prompt,
                    max_iterations=max_iterations,
                    fallback=True,
                )
            )
    return splits


# --- The artifact -----------------------------------------------------------------------


def render_artifact(l2_lines: Sequence[L2Line]) -> str:
    """The artifact TSV: one row per L2 entry, in line and entry order.

    `l2_index` is the entry's position within its line. `L2.md` says the L2 token number
    "is never stored separately, only `l1_index` is data" — true of the in-memory list,
    whose order *is* the numbering; a flat file has no order to lean on, so the position
    is written down. It is derived, not decided.
    """
    out = ["\t".join(ARTIFACT_HEADER)]
    for line in l2_lines:
        for l2_index, entry in enumerate(line.entries):
            out.append(f"{line.no}\t{entry.l1_index}\t{l2_index}\t{entry.text}")
    return "\n".join(out) + "\n"


def parse_artifact(text: str) -> list[L2Line]:
    """Read back `render_artifact`'s output, so `--check` runs off the file."""
    lines: list[L2Line] = []
    entries: list[L2Entry] = []
    current: int | None = None
    for raw in text.splitlines():
        cells = raw.split("\t")
        if len(cells) != 4 or tuple(c.strip() for c in cells) == ARTIFACT_HEADER:
            continue
        no, l1_index, _l2_index, entry_text = cells
        try:
            no_i, l1_i = int(no), int(l1_index)
        except ValueError:
            continue
        if current is not None and no_i != current:
            lines.append(L2Line(no=current, entries=tuple(entries)))
            entries = []
        current = no_i
        entries.append(L2Entry(l1_index=l1_i, text=entry_text))
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
    verdict: str  # agrees | differs | ours-ambiguous | precedent-ambiguous | absent

    def to_dict(self) -> dict:
        return {
            "wordform": self.wordform,
            "ours": [list(reading) for reading in self.ours],
            "theirs": [list(reading) for reading in self.theirs],
            "verdict": self.verdict,
        }


def _fold(parts: Sequence[str]) -> tuple[str, ...]:
    return tuple(part.casefold() for part in parts)


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
    splits are recorded per occurrence, so a wordform this artifact splits two ways must
    show as two, not as whichever came first.
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
            out.setdefault(wordform_key(token), set()).add(tuple(parts))
    return {key: tuple(sorted(readings)) for key, readings in out.items()}


def check_against_precedent(
    l1_lines: Sequence[L1Line],
    l2_lines: Sequence[L2Line],
    morph_rows: Mapping[int, Sequence[object]],
    *,
    line_range: tuple[int, int] | None = None,
) -> list[PrecedentRow]:
    """Diff this artifact's splits against old Layer 2's, wordform by wordform.

    Reports what is the case; it does not adjudicate. `L2.md` names three outcomes —
    agrees, precedent-is-wrong, genuine ambiguity — and only the first is mechanical. A
    `differs` row is the evidence for one of the other two, and which one it is is a
    judgment recorded in `L2.md` by a person.
    """
    ours = our_splits(l1_lines, l2_lines, line_range=line_range)
    theirs = precedent_splits(morph_rows, line_range)
    rows: list[PrecedentRow] = []
    for key in sorted(set(ours) | set(theirs)):
        mine = ours.get(key, ())
        readings = theirs.get(key, ())
        if not mine or not readings:
            verdict = "absent"
        elif len(mine) > 1:
            verdict = "ours-ambiguous"
        elif len(readings) > 1:
            verdict = "precedent-ambiguous"
        elif _fold(mine[0]) == _fold(readings[0]):
            verdict = "agrees"
        else:
            verdict = "differs"
        rows.append(
            PrecedentRow(wordform=key, ours=mine, theirs=readings, verdict=verdict)
        )
    return rows


# --- Reporting: the two faces of one aggregate (`ARCHITECTURE.md` §6) -----------------------


# A step slower than this is worth counting separately — the benchmark standard
# `ARCHITECTURE.md` §4 names. Nothing here is gated on it; it is a measurement.
SLOW_STEP_SECONDS = 300.0


@dataclass
class SplitReport:
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
    conflicts: list[dict] = field(default_factory=list)
    attempts: int = 0
    refusals: int = 0
    step_seconds: list[float] = field(default_factory=list)
    api_retries: int = 0
    api_retry_seconds: float = 0.0
    wordforms: int = 0
    l1_tokens: int = 0
    l2_entries: int = 0
    context: dict = field(default_factory=dict)

    def add_chunk(self, record: dict) -> None:
        self.chunks += 1
        self.fallback_chunks += int(bool(record.get("fallback")))
        if record.get("resolved"):
            self.settled_chunks += 1
            # A settled chunk answers for every one of its lines, including by saying
            # nothing splits there; a group that failed and was then retried line by
            # line clears its own lines when those retries settle.
            answered = set(record.get("lines") or [])
            self.unresolved_lines = [
                no for no in self.unresolved_lines if no not in answered
            ]
            # Only a settled chunk's tokens have an answer; a refused group's tokens are
            # counted when its line-by-line retries settle, so nothing is counted twice.
            self.tokens_answered += int(record.get("tokens") or 0)
            self.split += len(record.get("answers") or [])
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
            "passed_through": self.tokens_answered - self.split,
            "conflicts": list(self.conflicts),
            "attempts": self.attempts,
            "refusals": self.refusals,
            "wordforms": self.wordforms,
            "l1_tokens": self.l1_tokens,
            "l2_entries": self.l2_entries,
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
        lines = [
            f"chunks: {m['chunks']} — {m['settled_chunks']} settled, "
            f"{m['unresolved_chunks']} refused, {m['fallback_chunks']} line-by-line "
            f"after a group failed, {m['skipped_chunks']} already in the artifact "
            f"({len(m['skipped_lines'])} line(s))",
            f"tokens: {m['tokens_answered']} answered — {m['split']} split, "
            f"{m['passed_through']} left whole; {m['wordforms']} distinct wordforms, "
            f"{len(m['conflicts'])} answered two ways",
            f"terminals: {m['l1_tokens']} L1 tokens -> {m['l2_entries']} L2 entries "
            f"(+{m['l2_entries'] - m['l1_tokens']})",
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


def _run_check(args, canticle: str, number: int, l1_lines, line_range) -> int:
    from dante_corpus.morph import load_morph

    path = Path(args.out) if args.out else artifact_path(canticle, number)
    if not path.is_file():
        print(f"no artifact at {path} — run the split pass first")
        return 1
    l2_lines = parse_artifact(path.read_text(encoding="utf-8"))
    rows = check_against_precedent(
        l1_lines, l2_lines, load_morph(canticle, number), line_range=line_range
    )
    surface = {
        wordform_key(token.text): token.text
        for line in l1_lines
        for token in line.tokens
    }
    counts: dict[str, int] = {}
    print(f"{'wordform':<14}{'ours':<22}{'old Layer 2':<22}verdict")
    for row in rows:
        counts[row.verdict] = counts.get(row.verdict, 0) + 1
        shown = surface.get(row.wordform, row.wordform)
        ours_text = " / ".join("+".join(reading) for reading in row.ours)
        theirs = " / ".join("+".join(reading) for reading in row.theirs)
        print(f"{shown:<14}{ours_text or '-':<22}{theirs or '-':<22}{row.verdict}")
    print()
    for verdict in ("agrees", "differs", "ours-ambiguous", "precedent-ambiguous",
                    "absent"):
        print(f"{verdict:<22}{counts.get(verdict, 0)}")
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
    parser.add_argument("--lines", default=None,
                        help="line range within a single canto, e.g. '1-9' or '10' "
                             "(default: the whole canto)")
    parser.add_argument("-m", "--model", default=DEFAULT_MODEL,
                        help=f"LLM, e.g. {DEFAULT_MODEL} (the default)")
    parser.add_argument("--temperature", type=float, default=None)
    parser.add_argument("--chunk", type=int, default=CHUNK_SIZE,
                        help=f"lines per request (default {CHUNK_SIZE}, old Layer 2's)")
    parser.add_argument("--max-iterations", type=int, default=MAX_ITERATIONS)
    parser.add_argument("--out", help="artifact TSV (default: layers/l2/<canticle>/NN.tsv)")
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
    """One canto's split pass: its own artifact, its own log, its own bar and summary.

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
    done = (
        {line.no: line for line in parse_artifact(out_path.read_text(encoding="utf-8"))}
        if out_path.is_file() and not args.force
        else {}
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

    report = SplitReport(
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
            f"[l2-split] {report.l1_tokens} L1 tokens, {len(wordforms)} distinct "
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
                span = (
                    f"{result.lines[0]}-{result.lines[-1]}"
                    if len(result.lines) > 1 else f"{result.lines[0]}"
                )
                if result.accepted:
                    settled_lines.update(result.lines)
                    found = (
                        ", ".join(
                            f"{token.text}={'+'.join(parts)}"
                            for token, parts in result.pairs()
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
                settled_lines.update(record["lines"])
                if progress is not None:
                    progress.update(len(settled_lines))
                if sink is not None:
                    sink.write(json.dumps(record, ensure_ascii=False) + "\n")
                    sink.flush()

            splits = build_splits(
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
        # never asked about it, so `splits` says nothing about it and applying them would
        # silently un-split it. Every other line is built from this run's answers.
        kept = set(report.skipped_lines)
        l2_lines = [
            done[line.no] if line.no in kept else apply_splits(line, splits)
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
            print(f"NO ANSWER: line {no} — its tokens pass through unsplit", file=sys.stderr)
        for conflict in metrics["conflicts"]:
            print(
                f"TWO READINGS: {conflict['word']} was {'+'.join(conflict['first'])} earlier "
                f"and {'+'.join(conflict['here'])} at line {conflict['line']}; both stand",
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
