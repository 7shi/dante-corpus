"""The canto loop: drive a bounded step over every parse unit, behind two gates.

Lifted out of `harness/extractor/reconstruct.py`, which keeps the CLI, gate 3
(the hash-verified atomic write) and everything else that is Layer 5's. What is
here is the part that is nobody's layer in particular: walk a canto's parse
units, resume the ones already settled in the artifact, ask the fallback for the
rest, anchor what comes back (gate 1), measure it (gate 2), and hand each
settled unit to the caller the moment it settles.

The subject arrives as a `Subject`: its row codec, how to load a canto's frozen
layers, and the three functions that turn an answer into measured rows. The
layers bundle itself is opaque — this module receives one from `load_layers` and
hands it straight back, never looking inside except for the `units()` grouping
and the `nos` it labels progress with.

Gold is not opened here, and cannot be: nothing in this package can reach it.
"""

from __future__ import annotations

import contextlib
import sys
import time
from dataclasses import dataclass
from typing import Any, Callable, TextIO

from .fixedcontext import FixedUnitResult
from .outcome import (
    CantoReconstruction,
    UnitOutcome,
    final_validation_errors,
    replay_unit_outcome,
)
from .rows import RowCodec, RowKey

__all__ = [
    "AgentFallback",
    "Span",
    "Subject",
    "progress_separator",
    "reconstruct_canto",
]

Span = tuple[int, int]

# `(canticle, canto, line_start, line_end) -> UnitResult`-shaped object. The live
# one is `fixedcontext.fixed_fallback`; tests inject deterministic stubs.
AgentFallback = Callable[..., object]


@dataclass(frozen=True)
class Subject:
    """The layer under reconstruction, as the canto loop needs it.

    `load_layers` returns the frozen-layer bundle for one canto — opaque here,
    beyond `units()` and `nos`. `candidate_keys` normalises a submission to
    comparable keys, `build_rows` is gate 1 (anchor the keys on the token
    stream) and `validate` is gate 2. Layer 5's are in
    `harness/extractor/layers.py`.
    """

    codec: RowCodec
    load_layers: Callable[[str, int], Any]
    candidate_keys: Callable[[list[dict], int, int], tuple[set, int, int]]
    build_rows: Callable[..., tuple[dict[int, list], list[str]]]
    validate: Callable[..., tuple[list, list]]


def progress_separator(label: str, index: int, total: int, stream=None) -> None:
    """Announce one canto's start with its position in the run.

    A corpus run processes a hundred cantos over hours; without a marker between
    them there is no way to tell where it currently is. The line goes to stderr
    (JSONL logs stay clean) and names the canto plus its `[index/total]`
    position.
    """
    stream = sys.stderr if stream is None else stream
    print(f"\n===== [{index}/{total}] {label} =====", file=stream, flush=True)


def retry_snapshot(status_line) -> tuple[int, float] | None:
    """`(count, seconds)` of api-retry backoffs seen so far, or None if untracked.

    llm7shi auto-retries 429 backoffs silently; the status line's stream counts
    them via `wait_retry`.
    """
    stream = getattr(status_line, "stream", None)
    count = getattr(stream, "api_retries", None)
    if count is None:
        return None
    return count, getattr(stream, "api_retry_seconds", 0.0)


def retry_delta(
    snapshot: tuple[int, float] | None, status_line
) -> tuple[int, float] | None:
    """Backoff `(count, seconds)` accumulated since `snapshot`; None if untracked."""
    if snapshot is None:
        return None
    now = retry_snapshot(status_line)
    if now is None:
        return 0, 0.0
    return max(now[0] - snapshot[0], 0), max(now[1] - snapshot[1], 0.0)


def reconstruct_canto(
    canticle: str,
    canto: int,
    *,
    subject: Subject,
    fallback: AgentFallback | None = None,
    progress_stream: TextIO | None = sys.stderr,
    status_line=None,
    settled_units: dict[Span, dict[int, list]] | None = None,
    fix_spans: set[Span] | None = None,
    emit_unit: Callable[[UnitOutcome], None] | None = None,
) -> CantoReconstruction:
    """Drive the bounded step over every parse unit of one canto, gated.

    Loads the frozen layers only; gold is never touched. Each unit runs the
    `fallback` callable, its accepted rows are anchored on the token stream
    (gate 1), and the unit is verified through the subject's validator with all
    layers attached (gate 2). `status_line`, when given (a
    `harness.statusline.HarnessStatusLine`), owns the display the way the
    `skel/` drivers do: a bar labeled `{canticle} {canto}` counting the canto's
    lines, advanced to each unit's first line, with the per-unit progress lines
    routed through its console stream so they coexist with it.

    `emit_unit`, when given, is called with each freshly computed outcome the
    moment it settles — before the next unit starts. This is §5's durability
    seam: the caller streams the unit's records to disk here, so a kill
    mid-canto leaves every already-settled unit on disk for unit-level resume
    instead of losing them all to a post-canto flush. Replayed units are never
    passed (their records already sit in the caller's log from the prior
    attempt).

    `settled_units`, when given, maps `(line_start, line_end)` to the rows a
    previous attempt already wrote to the canto's TSV: unit-level resume off
    the artifact itself (`TsvArtifact.settled`). Matching units are rebuilt
    from those rows (`replay_unit_outcome`, gates re-run) instead of being
    re-solved — the caller must not re-emit them, since the artifact already
    holds them.

    With `fallback=None` no unit is solved at all: every unsettled unit records
    empty rows. That is the dry mode the deterministic tests use.
    """
    stream = status_line.stream if status_line is not None else progress_stream
    layers = subject.load_layers(canticle, canto)
    recon = CantoReconstruction(
        canticle=canticle, canto=canto, nos=list(layers.nos), codec=subject.codec
    )
    units = layers.units()
    # Skel-driver display (`driver_build._build_canto`): the bar's label names
    # Canticle Canto and its numerator walks the canto's Dante lines as each
    # parse unit starts; whole-run `[i/N]` positions stay with the separators.
    bar = (
        status_line.progress(len(layers.nos), label=f"{canticle} {canto}")
        if status_line is not None
        else contextlib.nullcontext()
    )
    with bar as prog:
        for pos, group in enumerate(units, start=1):
            if prog is not None:
                prog.update(group[0])
            if stream is not None and pos % 5 == 0:
                print(
                    f"[reconstruct] {canticle} {canto} units {pos}/{len(units)}",
                    file=stream,
                    flush=True,
                )
            line_start, line_end = group[0], group[-1]
            settled = (
                settled_units.get((line_start, line_end)) if settled_units else None
            )
            if settled is not None:
                recon.outcomes.append(
                    replay_unit_outcome(
                        settled, layers, group, validate=subject.validate
                    )
                )
                continue
            started = time.monotonic()
            reason = (
                "fix" if fix_spans and (line_start, line_end) in fix_spans
                else "generate"
            )
            agent_result = None
            row_keys: frozenset[RowKey] = frozenset()
            if fallback is not None:
                agent_result = fallback(
                    canticle=canticle,
                    canto=canto,
                    line_start=line_start,
                    line_end=line_end,
                )
                keys, _malformed, _out_of_unit = subject.candidate_keys(
                    agent_result.candidate_rows, line_start, line_end
                )
                row_keys = frozenset(keys)
            elapsed = time.monotonic() - started
            rows, assertions = subject.build_rows(
                row_keys, layers, line_start, line_end
            )
            unit_rows = {no: rows.get(no, []) for no in group}
            hard, soft = subject.validate(layers, group, unit_rows)
            fallback_seconds: float | None = None
            turn_seconds = getattr(agent_result, "turn_seconds", None)
            if agent_result is not None and turn_seconds is not None:
                fallback_seconds = sum(turn_seconds)
            elif agent_result is not None:
                fallback_seconds = elapsed
            outcome = UnitOutcome(
                unit={
                    "canticle": canticle,
                    "canto": canto,
                    "line_start": line_start,
                    "line_end": line_end,
                },
                route="agent",
                reason=reason,
                origin="agent",
                fallback_ran=agent_result is not None,
                row_keys=row_keys,
                rows=unit_rows,
                token_assertions=assertions,
                hard=hard,
                soft=soft,
                fallback_seconds=fallback_seconds,
                final_submission_valid=getattr(
                    agent_result, "final_submission_valid", None
                ),
                invalid_nudges=getattr(agent_result, "invalid_nudges", None),
                final_validation_errors=final_validation_errors(agent_result),
                # The fixed-context loop's own record of what each step did
                # (`fixedcontext.FixedUnitResult`). None when a test's stub
                # fallback stands in for it.
                fixed=(
                    agent_result.to_dict()
                    if isinstance(agent_result, FixedUnitResult)
                    else None
                ),
            )
            recon.outcomes.append(outcome)
            # §5 durability seam: hand the settled outcome to the caller while
            # the canto is still running, so the record is on disk before the
            # next unit's (possibly hours-long) fallback begins.
            if emit_unit is not None:
                emit_unit(outcome)
    return recon
