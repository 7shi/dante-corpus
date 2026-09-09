"""Generation 2, Layer 2: restore the letters a token drops at its ends.

**Where this runs, and why it is not in front of the split any more** (operator,
2026-09-09). It was built as a step 0: the split pass of the time asked a question about
*shape* — "is this token several grammatical words written together?" — and `pel`
(*Inf* 1:33) is the proof that shape is not enough, since it is `pelo` with its final vowel
gone and looks exactly like `del`/`nel`/`col`. Restoring the letters first was one of two
candidate guards. **It ran over all of *Inf* 1 and did not restore `pel`** (`L2.md`, *Step
0*), at 6.2x the split's cost, and the other candidate was taken instead: `l2.py` now asks
the words and their coarse part of speech in the same answer, so `di per il macolato` is
contradicted by the tags in the line the way old Layer 2's second column contradicted it.

**And then the words pass absorbed the rest of it** (operator, 2026-09-09). What was left
for a separate pass was the position *after* the split — a fused token can hide a
truncation inside it (`farne` is `far`+`ne` and `far` is `fare` shortened; the corpus has
`farsi` 8, `farne` 3, `farmi` 3, `dirne` 2, `udirti` 2, `vederti`, `vedervi`, … all of this
shape), and nothing before the split can see it. But `l2.py` writes each part whole, so it
answers that in the same row: `farne` -> `fare`+`ne`. **This module is therefore unused.**
It stays because its run is measured work (`L2.md`, *Step 0*) and because its gate's
criterion is the one `l2.py` now applies — `is_restoration` moved to `l2.py`, and this
module imports it, so the two cannot drift on what counts as putting letters back.

**The scope is stated as an operation on letters, never as "the standard form"**
(operator, 2026-09-09): calling it alignment to a standard invites lexical substitution,
and most of what looks archaic here is not a shortened word at all — modern Italian
descends from this language, so `sanza`, `core`, `giuso` are simply its words. Only two
things are restored: the letters an apostrophe stands for, at either end of the token
(`ch'` -> `che`, `'ncontro` -> `incontro`), and a dropped final syllable with no apostrophe
(`cammin` -> `cammino`). The boundary is enforced mechanically rather than merely stated:
`is_restoration` requires the token's own letters to read straight through the answer,
unbroken and in order, so `pel` -> `pelo` passes and `sanza` -> `senza` is refused — and it
reads the apostrophe as the marker of *where* the letters were dropped, so an answer may
only grow at an end the token's own spelling opens (`ch'` -> `che`, never `ache`).

**What this pass does not decide.** It assigns no part of speech and no lemma, and it never
splits: its answer is always one word. `nel` comes out of it as `nel`.

The machinery is `l2.py`'s, deliberately: the same chunk of lines per request (`--chunk`,
default 3), no transcript across a chunk or a retry, the gate in the runtime, refusal as
the identity, and a line-by-line fallback when a group never passes. `l2.py`'s own
primitives are imported rather than copied, so the two passes cannot drift on what a token
is. Answers here are keyed by the word (`locate_key`, which lives in this module now) —
`l2.py` answers a row per token and matches by position instead.

    uv run python -m layers.gen2.restore inferno -c 1 -m ...
    uv run python -m layers.gen2.restore inferno -c 1 --lines 1-9 -m ...
    uv run python -m layers.gen2.restore inferno -c 1 -m ... --force

The artifact is `layers/l2/<canticle>/NN-restore.tsv`, one row per L1 token with the
restored form beside it — every token, not only the changed ones, so the file says what was
*considered* and a run can resume off it. Nothing consumes it yet: it was `l2.py -r`'s
input while this pass ran in front of the split, and that option is gone with the step-0
position.

**Bootstrap status (premise 3).** This pass reads L1 and nothing else. No old-layer file is
named as an input and the model is shown no old Layer 2 row; `morph/`'s own `apocope` notes
are precedent to check against afterwards, never an input.
"""

from __future__ import annotations

import json
import re
import time
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Iterable, Mapping, Sequence

from .l1 import L1Line, l1_canto
from .l2 import (
    CHUNK_SIZE,
    MAX_ITERATIONS,
    Asked,
    Position,
    _LogRelay,
    chunks,
    is_restoration,
    is_splittable,
    letters_of,
    wordform_key,
)
from .l2 import _ascii_fold as _fold

DEFAULT_MODEL = "google:gemma-4-31b-it"

SKILL_DIR = Path(__file__).resolve().parent / "skills" / "l2-restore"

ARTIFACT_HEADER = ("line", "l1_index", "text", "restored")

SLOW_STEP_SECONDS = 60.0

_RESTORE_BLOCK = re.compile(r"<restore>(.*?)</restore>", re.DOTALL | re.IGNORECASE)

# --- $O$: the question, and the gate on the answer -----------------------------------------


def asked_tokens(chunk: Sequence[L1Line]) -> list[Asked]:
    """The chunk's word tokens in L1 order — punctuation has nothing to restore."""
    return [
        Asked(line=line.no, l1_index=token.index, text=token.text)
        for line in chunk
        for token in line.tokens
        if is_splittable(token.text)
    ]


def locate_key(key: str, tokens: Sequence[Asked]) -> tuple[int, str]:
    """Which asked token a row's key names, or why it names none (or too many).

    A key is one token, or a run of consecutive tokens **ending with** the one being
    answered — `de'` normally, `trattar de'` when a bare `de'` would name two places.
    Returns `(index into tokens, error)`; a non-empty error means the caller refuses the
    answer.

    Requiring the run to be unique is what lets the answer carry differences only. A bare
    key matching two occurrences is refused rather than applied to both, because those two
    occurrences are exactly where one wordform can genuinely read two ways. (This pass is
    the only one that keys its answers: `l2.py` asks for a row per token and matches by
    position, so the function lives here, with its user.)
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


def ask_message(chunk: Sequence[L1Line], *, refusal: str = "") -> str:
    """The single user message for one attempt at one chunk.

    The lines are shown for context — the trap this pass exists for (`pel`) is only
    decidable from the line — and the tokens are listed so the model never re-tokenizes.
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
            "ones that have dropped letters at their beginning or their end. Tokens you "
            "do not list are recorded exactly as written, so an empty block means you "
            "found none.\n"
            "</verdict>"
        )
    return "\n\n".join(parts)


def parse_restore_answer(
    text: str, *, tokens: Sequence[Asked]
) -> tuple[dict[int, str], str]:
    """The `<restore>` block's rows — only the tokens that changed — or the gate's reason.

    Returns `(restorations, error)` where `restorations` maps an index into `tokens` to that
    token's restored spelling. A non-empty `error` means nothing is recorded and the caller
    re-asks with it, so a refused answer is the identity on the table.

    Keys are resolved by `locate_key` — this module's own function — against the tokens the
    request listed, so a key either names exactly one token of this passage or the answer is
    refused. Values go through `is_restoration`, which is where the pass's whole scope lives.
    """
    matches = _RESTORE_BLOCK.findall(text or "")
    if not matches:
        return {}, "no <restore> block in the answer"
    if len(matches) > 1:
        return {}, f"{len(matches)} <restore> blocks in the answer; send exactly one"
    body = [
        line.strip()
        for line in matches[0].splitlines()
        if line.strip()
        and not line.strip().startswith(("#", "```"))
        and line.strip().casefold() not in ("none", "(none)", "-")
    ]
    restorations: dict[int, str] = {}
    for position, raw in enumerate(body, start=1):
        key, separator, value = raw.partition(":")
        if not separator:
            return {}, f"row {position} is not 'word:restored' — no ':' in {raw!r}"
        key, value = key.strip(), value.strip()
        index, error = locate_key(key, tokens)
        if error:
            return {}, f"row {position}: {error}"
        token = tokens[index]
        if index in restorations:
            return {}, (
                f"row {position} names {token.text!r} (line {token.line}) a second time; "
                "each token takes at most one row"
            )
        if not value:
            return {}, f"row {position} ({key!r}) has nothing after the ':'"
        if any(character.isspace() for character in value):
            return {}, (
                f"row {position} ({key!r}): {value!r} is two words — a restored token is "
                "always one word, and splitting it is a different job"
            )
        if "+" in value:
            return {}, (
                f"row {position} ({key!r}): {value!r} splits the token; this pass only "
                "puts back dropped letters, it never splits"
            )
        if _fold(value) == _fold(token.text):
            return {}, (
                f"row {position} ({key!r}): {value!r} is the token unchanged, so the row "
                "says nothing — list only the tokens you restored"
            )
        if not is_restoration(token.text, value):
            return {}, (
                f"row {position} ({key!r}): {value!r} is not {token.text!r} with its "
                "dropped letters put back. The token's own letters must read straight "
                "through it, unbroken and in order — nothing may be respelled — and the "
                "letters go where the apostrophe is: at the end for a trailing apostrophe, "
                "at the beginning for a leading one, and at the end only when there is no "
                "apostrophe at all"
            )
        restorations[index] = value
    return restorations, ""


# --- The bounded step ----------------------------------------------------------------------


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
    answers: dict[int, str] = field(default_factory=dict)
    accepted: bool = False
    attempts: list[AttemptRecord] = field(default_factory=list)
    stop_reason: str = "settled"  # settled | budget | unanswered
    fallback: bool = False
    conflicts: list[dict] = field(default_factory=list)

    @property
    def resolved(self) -> bool:
        return self.accepted

    @property
    def restored(self) -> int:
        return len(self.answers)

    @property
    def seconds(self) -> float:
        return sum(attempt.seconds for attempt in self.attempts)

    def pairs(self) -> list[tuple[Asked, str]]:
        return [(self.tokens[index], self.answers[index]) for index in sorted(self.answers)]

    def positions(self) -> dict[Position, str]:
        return {(token.line, token.l1_index): value for token, value in self.pairs()}

    def to_dict(self) -> dict:
        return {
            "record": "chunk",
            "lines": list(self.lines),
            "tokens": len(self.tokens),
            "resolved": self.resolved,
            "restored": self.restored,
            "stop_reason": self.stop_reason,
            "fallback": self.fallback,
            "conflicts": list(self.conflicts),
            "answers": [
                {"line": token.line, "l1_index": token.l1_index, "word": token.text,
                 "restored": value}
                for token, value in self.pairs()
            ],
            "attempts": [attempt.to_dict() for attempt in self.attempts],
            "seconds": round(self.seconds, 3),
        }


def restore_chunk(
    chunk: Sequence[L1Line],
    *,
    generate: Callable[[list[dict]], str],
    system_prompt: str,
    max_iterations: int = MAX_ITERATIONS,
    fallback: bool = False,
) -> ChunkResult:
    """Ask one chunk until the gate accepts an answer, or the budget runs out.

    Every attempt resets the backend and sends exactly `[system, user]`, so per-request size
    is a function of the chunk and never of the attempt count.
    """
    tokens = asked_tokens(chunk)
    result = ChunkResult(lines=[line.no for line in chunk], tokens=tokens, fallback=fallback)
    if not tokens:
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
        restorations, error = parse_restore_answer(answer, tokens=tokens)
        if error:
            result.attempts.append(
                AttemptRecord(attempt=attempt, kind=kind, accepted=False, error=error,
                              seconds=elapsed)
            )
            refusal = error
            continue
        result.attempts.append(
            AttemptRecord(attempt=attempt, kind=kind, accepted=True,
                          rows=len(restorations), seconds=elapsed)
        )
        result.answers = restorations
        result.accepted = True
        result.stop_reason = "settled"
        return result
    result.stop_reason = "budget" if result.attempts else "unanswered"
    return result


def build_restorations(
    lines: Sequence[L1Line],
    *,
    generate: Callable[[list[dict]], str],
    system_prompt: str,
    chunk_size: int = CHUNK_SIZE,
    max_iterations: int = MAX_ITERATIONS,
    on_settled: Callable[[ChunkResult], None] | None = None,
    already_answered: Callable[[Sequence[L1Line]], bool] | None = None,
    on_skipped: Callable[[Sequence[L1Line]], None] | None = None,
) -> dict[Position, str]:
    """Every restoration these lines contain, by position: one bounded step per chunk.

    Restorations are recorded **per occurrence**, because `l'` is genuinely `lo` in one line
    and `la` in the next; a wordform answered two ways elsewhere in the run is recorded as a
    **conflict** on that chunk and then applied as answered, since the model had this
    passage in front of it. A chunk that never passes the gate is retried line by line.
    """
    restorations: dict[Position, str] = {}
    first_reading: dict[str, str] = {}

    def absorb(result: ChunkResult) -> None:
        for token, value in result.pairs():
            key = wordform_key(token.text)
            seen = first_reading.setdefault(key, value)
            if seen != value:
                result.conflicts.append(
                    {"word": token.text, "line": token.line, "first": seen, "here": value}
                )
            restorations[(token.line, token.l1_index)] = value
        if on_settled is not None:
            on_settled(result)

    for chunk in chunks(lines, chunk_size):
        if already_answered is not None and already_answered(chunk):
            if on_skipped is not None:
                on_skipped(chunk)
            continue
        result = restore_chunk(
            chunk,
            generate=generate,
            system_prompt=system_prompt,
            max_iterations=max_iterations,
        )
        absorb(result)
        if result.accepted or len(chunk) == 1:
            continue
        for line in chunk:
            absorb(
                restore_chunk(
                    (line,),
                    generate=generate,
                    system_prompt=system_prompt,
                    max_iterations=max_iterations,
                    fallback=True,
                )
            )
    return restorations


# --- The artifact ---------------------------------------------------------------------------


def render_artifact(
    lines: Sequence[L1Line], restorations: Mapping[Position, str]
) -> str:
    """One row per L1 token: where it is, how it is written, and how it reads restored.

    Every token is written, not only the changed ones. A changed-only file could not say
    whether a line had been *asked* — which is what resumption needs — and it would hide the
    pass's main result, that most tokens are left exactly as written.
    """
    out = ["\t".join(ARTIFACT_HEADER)]
    for line in lines:
        for token in line.tokens:
            restored = restorations.get((line.no, token.index), token.text)
            out.append(f"{line.no}\t{token.index}\t{token.text}\t{restored}")
    return "\n".join(out) + "\n"


def parse_artifact(text: str) -> dict[Position, str]:
    """Read back `render_artifact`'s output as `(line, l1_index) -> restored`.

    Unchanged tokens are kept, so a caller can tell "answered, nothing to restore" from
    "never asked" by whether the position is present at all.
    """
    out: dict[Position, str] = {}
    for raw in text.splitlines():
        cells = raw.split("\t")
        if len(cells) != 4 or tuple(c.strip() for c in cells) == ARTIFACT_HEADER:
            continue
        no, l1_index, _text, restored = cells
        try:
            out[(int(no), int(l1_index))] = restored
        except ValueError:
            continue
    return out


def load_restorations(path: Path | str) -> dict[Position, str]:
    """The restore artifact as the split pass consumes it: only the tokens that changed.

    Nothing consumes these yet (the `l2.py -r` reader is gone), so a position that restored to
    itself must not appear — it would be a no-op substitution that only slows the lookup.
    """
    text = Path(path).read_text(encoding="utf-8")
    rows = parse_artifact(text)
    keep: dict[Position, str] = {}
    for raw in text.splitlines():
        cells = raw.split("\t")
        if len(cells) != 4 or tuple(c.strip() for c in cells) == ARTIFACT_HEADER:
            continue
        no, l1_index, token, restored = cells
        try:
            position = (int(no), int(l1_index))
        except ValueError:
            continue
        if rows.get(position) != token:
            keep[position] = restored
    return keep


def artifact_path(canticle: str, number: int) -> Path:
    """`layers/l2/<canticle>/NN-restore.tsv` — beside the split's own artifact.

    `gen2/` is a code directory: no artifact and no run log is written into it (operator,
    2026-09-09).
    """
    return (
        Path(__file__).resolve().parent.parent
        / "l2"
        / canticle
        / f"{number:02d}-restore.tsv"
    )


# --- The report ------------------------------------------------------------------------------


@dataclass
class RestoreReport:
    """Both faces of one run's numbers — the JSONL `summary` record and the console
    summary — computed from the same aggregate, so they cannot drift (`ARCHITECTURE.md` §6).
    """

    chunks: int = 0
    settled_chunks: int = 0
    unresolved_chunks: int = 0
    fallback_chunks: int = 0
    skipped_chunks: int = 0
    skipped_lines: list[int] = field(default_factory=list)
    unresolved_lines: list[int] = field(default_factory=list)
    tokens_answered: int = 0
    restored: int = 0
    conflicts: list[dict] = field(default_factory=list)
    attempts: int = 0
    refusals: int = 0
    step_seconds: list[float] = field(default_factory=list)
    api_retries: int = 0
    api_retry_seconds: float = 0.0
    l1_tokens: int = 0
    context: dict = field(default_factory=dict)

    def add_chunk(self, record: dict) -> None:
        self.chunks += 1
        self.fallback_chunks += int(bool(record.get("fallback")))
        if record.get("resolved"):
            self.settled_chunks += 1
            answered = set(record.get("lines") or [])
            self.unresolved_lines = [
                no for no in self.unresolved_lines if no not in answered
            ]
            self.tokens_answered += int(record.get("tokens") or 0)
            self.restored += len(record.get("answers") or [])
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
        self.skipped_chunks += 1
        self.skipped_lines.extend(record.get("lines") or [])

    def add_retries(self, delta) -> None:
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
            "restored": self.restored,
            "left_as_written": self.tokens_answered - self.restored,
            "conflicts": list(self.conflicts),
            "attempts": self.attempts,
            "refusals": self.refusals,
            "l1_tokens": self.l1_tokens,
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
        return "\n".join(
            [
                f"chunks: {m['chunks']} — {m['settled_chunks']} settled, "
                f"{m['unresolved_chunks']} refused, {m['fallback_chunks']} line-by-line "
                f"after a group failed, {m['skipped_chunks']} already in the artifact "
                f"({len(m['skipped_lines'])} line(s))",
                f"tokens: {m['tokens_answered']} answered — {m['restored']} restored, "
                f"{m['left_as_written']} left as written; "
                f"{len(m['conflicts'])} answered two ways",
                f"lines with no answer: {len(m['unresolved_lines'])} "
                f"(gate == 0 lines: {gate})",
                f"requests: {m['attempts']} attempts, {m['refusals']} refused",
                f"seconds: {m['step_seconds_total']} total / "
                f"{m['step_seconds_mean']} mean / {m['step_seconds_max']} max, "
                f"{m['slow_steps']} slower than {SLOW_STEP_SECONDS:.0f}s",
                f"api retries: {m['api_retries']} ({m['api_retry_seconds']}s backoff)",
            ]
        )


# --- CLI ---------------------------------------------------------------------------------------


def _system_prompt() -> str:
    from dante_corpus.harness.skills import Skill

    skill = Skill.load(SKILL_DIR)
    return "\n\n".join([skill.body, skill.resource("answer.md")])


def _skill_digest() -> str:
    from dante_corpus.harness.skills import Skill

    return Skill.load(SKILL_DIR).digest()


def _parse_range(spec: str) -> tuple[int, int]:
    start, _, end = spec.partition("-")
    return (int(start), int(end or start))


def _selected_lines(canticle: str, number: int, line_range) -> list[L1Line]:
    return [
        line
        for line in l1_canto(canticle, number)
        if line_range is None or line_range[0] <= line.no <= line_range[1]
    ]


def _check(canticle: str, number: int, l1_lines: Sequence[L1Line], out: Path) -> int:
    """Offline: what this pass restored, against old Layer 2's own `note` column.

    `morph/` writes `apocope`, `elision` and `contraction` in its notes, so the precedent
    for "letters were dropped here" already exists row by row — the one thing it does not
    record is *what* they read restored (its `lemma` is a dictionary form, `ritrovare` for
    `ritrovai`), which is why agreement is counted on the position and never on the string.
    """
    from dante_corpus.morph import load_morph

    if not out.is_file():
        print(f"no artifact at {out} — run the restore pass first")
        return 1
    restored = load_restorations(out)
    morph_rows = load_morph(canticle, number)
    both, ours_only, theirs_only = [], [], []
    for line in l1_lines:
        rows = iter(morph_rows.get(line.no, ()))
        for token in line.tokens:
            if not is_splittable(token.text):
                continue
            row = next(rows, None)
            note = str(getattr(row, "note", "") or "").casefold()
            theirs = "apocope" in note or "elision" in note
            ours = (line.no, token.index) in restored
            entry = (line.no, token.text, restored.get((line.no, token.index), ""), note)
            if ours and theirs:
                both.append(entry)
            elif ours:
                ours_only.append(entry)
            elif theirs:
                theirs_only.append(entry)
    for label, group in (
        ("restored here, marked apocope/elision by old Layer 2", both),
        ("restored here, not marked by old Layer 2", ours_only),
        ("marked by old Layer 2, left as written here", theirs_only),
    ):
        print(f"[{label}]  {len(group)}")
        for no, word, value, note in group:
            print(f"{no:4d}  {word:<12}{value:<12}{note}")
        print()
    return 0


def _main(argv=None) -> int:
    import argparse
    import sys

    from dante_corpus import api

    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
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
    parser.add_argument("-o", "--out",
                        help="artifact TSV (default: layers/l2/<canticle>/NN-restore.tsv)")
    parser.add_argument("--force", action="store_true",
                        help="ask again from the first line, ignoring what the artifact "
                             "already answers (default: resume, skipping those chunks)")
    parser.add_argument("--log", action=argparse.BooleanOptionalAction, default=True,
                        help="write each canto's streaming JSONL log beside its artifact "
                             "(default: enabled)")
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--started-at", type=float, default=None)
    parser.add_argument("--check", action="store_true",
                        help="offline: diff an existing artifact against old Layer 2's "
                             "apocope/elision notes")
    args = parser.parse_args(argv)

    if err := api.check_canto_spec(args.canticles, args.canto):
        parser.error(err)
    targets = [
        (canticle, number)
        for canticle in args.canticles
        for number in api.select_cantos(canticle, args.canto)
    ]
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
            out = Path(args.out) if args.out else artifact_path(canticle, number)
            status |= _check(canticle, number, l1_lines, out)
        return status

    from dante_corpus.harness.llm import llm7shi_generate
    from dante_corpus.harness.statusline import HarnessStatusLine

    status_line = HarnessStatusLine() if HarnessStatusLine is not None else None
    if status_line is not None and args.started_at is not None:
        status_line.run_started_at = args.started_at
    ui_stream = status_line.stream if status_line is not None else sys.stderr
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
            args, canticle, number, index, len(targets),
            line_range=line_range, generate=generate, relay=relay,
            ui_stream=ui_stream, status_line=status_line,
        )
    return status


def _build_canto(
    args, canticle: str, number: int, index: int, total: int, *,
    line_range, generate, relay, ui_stream, status_line,
) -> int:
    """One canto's restore pass: its own artifact, its own log, its own bar and summary."""
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
    line_span = (min(line.no for line in l1_lines), max(line.no for line in l1_lines))
    out_path = Path(args.out) if args.out else artifact_path(canticle, number)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    label = f"{canticle} {number}"
    on_disk = (
        parse_artifact(out_path.read_text(encoding="utf-8"))
        if out_path.is_file() and not args.force
        else {}
    )
    done_lines = {no for no, _ in on_disk}
    log_path = out_path.with_suffix(".log") if args.log else None
    sink = open(log_path, "a", encoding="utf-8") if log_path is not None else None
    if relay is not None:
        relay.sink = sink

    report = RestoreReport(
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
    planned = chunks(l1_lines, args.chunk)
    results: list[ChunkResult] = []
    # Carried through from the file for the lines this run does not ask about again.
    built: dict[Position, str] = {}
    settled_lines: set[int] = set()

    try:
        progress_separator(
            f"{label} lines {line_span[0]}-{line_span[1]}", index, total, stream=ui_stream
        )
        pending = sum(
            1 for chunk in planned if not all(line.no in done_lines for line in chunk)
        )
        print(
            f"[l2-restore] {report.l1_tokens} L1 tokens, {pending} of {len(planned)} "
            f"chunk(s) of {args.chunk} line(s) to ask "
            f"({len(planned) - pending} already in the artifact), model={args.model}, "
            f"max {args.max_iterations} attempt(s) each",
            file=ui_stream,
            flush=True,
        )
        retries_before = retry_snapshot(status_line)

        def flush_artifact() -> None:
            covered = [line for line in l1_lines if line.no in settled_lines]
            out_path.write_text(render_artifact(covered, built), encoding="utf-8")

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
                if result.accepted:
                    settled_lines.update(result.lines)
                    built.update(result.positions())
                flush_artifact()
                span = (
                    f"{result.lines[0]}-{result.lines[-1]}"
                    if len(result.lines) > 1 else f"{result.lines[0]}"
                )
                if result.accepted:
                    found = (
                        ", ".join(
                            f"{token.text}->{value}" for token, value in result.pairs()
                        )
                        or "nothing restored"
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
                    settled_lines.add(line.no)
                    for token in line.tokens:
                        position = (line.no, token.index)
                        value = on_disk.get(position)
                        if value is not None and value != token.text:
                            built[position] = value
                flush_artifact()
                if progress is not None:
                    progress.update(len(settled_lines))
                if sink is not None:
                    sink.write(json.dumps(record, ensure_ascii=False) + "\n")
                    sink.flush()

            build_restorations(
                l1_lines,
                generate=generate,
                system_prompt=_system_prompt(),
                chunk_size=args.chunk,
                max_iterations=args.max_iterations,
                on_settled=settled,
                already_answered=lambda chunk: all(
                    line.no in done_lines for line in chunk
                ),
                on_skipped=skipped,
            )
        report.add_retries(retry_delta(retries_before, status_line))
        flush_artifact()
        print(f"\n{report.summary()}", file=ui_stream, flush=True)
        if sink is not None:
            sink.write(json.dumps(report.metrics(), ensure_ascii=False) + "\n")
            sink.flush()
        return 0 if not report.metrics()["unresolved_lines"] else 1
    finally:
        if relay is not None:
            relay.sink = None
        if sink is not None:
            sink.close()


if __name__ == "__main__":
    raise SystemExit(_main())
