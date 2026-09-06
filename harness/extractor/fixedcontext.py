"""Stage 9's fixed-context execution loop: one bounded step, iterated by the runtime.

`../stages/09.md` §2. The per-unit tool-calling session is replaced by a request
whose size does not grow with the number of iterations:

| component | what it holds | where it comes from |
|---|---|---|
| $P$ — specification | role, the 4-step protocol, the answer contract | `runner/prompts.py` `fixed_system_prompt` (the `grammar-fixed` skill, entire) |
| $O$ — observation | the unit's frozen-layer evidence, plus the verdict on the rows on record | `runner/tools.py` `read_unit` + `validate_candidate`, `observe.py` |
| $\\Sigma$ — the object under repair | the unit's current rows, as the artifact's own TSV columns | the caller (`--fix`: the recorded rows; a fresh unit: empty) |
| output | the rewritten rows, in full | the model's `<rows>` block |

Everything the design argues for follows from where the pieces sit, so the
implementation notes are about exactly that:

**The gate is the runtime's, not the model's.** `validate_candidate` is called here,
on every answer, before anything is accepted — so "settled without ever validating"
is unrepresentable, and the flags the elective version needed (`valid_seen`,
`exhausted`, `protocol_complete`) have no counterpart. The model never dispatches a
tool; there are none in $P$.

**Full rows, not a patch.** The model rewrites $\\Sigma$ entire and the merge operator
is the identity, so the paper's dominant failure mode (68% botched merges) cannot
occur — there is no merge. `parse_rows` reads the block; nothing is diffed.

**Refusal is the identity morphism** (§2.1). A step that fails — no parsable block, or
a schema-invalid answer — leaves $\\Sigma$ exactly as it was and reports why; the loop
then re-asks with the failure in $O$. So the loop is an endomorphism on $\\Sigma$ whose
failure case is `id`, which is `fixrun.py`'s standing "never worse than it found it"
guarantee inherited by construction rather than re-argued.

**Nothing crosses an iteration but $\\Sigma$.** Each iteration resets the backend
adapter and sends `[system, user]` — the same two messages, differing only in the
verdict and the rows. There is no transcript, so per-request size is a function of
the unit, never of the iteration count. That is the whole point of the stage; a
change here that lets history accumulate gives the property away silently.

**The stopping rule is a fixed point, not a count** (S9.1). The loop stops when the
verdict is empty (schema-clean with no frozen-layer observation), when the model
returns the rows it was given ($\\Sigma_{t+1} = \\Sigma_t$), or when the iteration
budget runs out. It never stops on "the number went down": the observations are not a
calibrated metric, and the soft counter — which is calibrated, against the registry —
is exactly what may not enter (`../SOFT.md` S6.1, Standing Invariant §4 item 1).

**The budget is a cap, not a measurement.** `MAX_ITERATIONS` below is bounded by what
the corpus's units cost, not by a measured per-request ceiling: S9.2 found no logged
request within a factor of two of any token limit anyone has tested, and sizing this
against a real ceiling waits on a live run at higher volumes (`../stages/09.md` §5).

Gold is not opened here, transitively or otherwise: the toolkit is the masked path
`runner/llm.py` carries, and `observe.py` reads Layers 2-4.
"""

from __future__ import annotations

import contextlib
import json
import re
import sys
import time
from contextlib import AbstractContextManager, nullcontext
from dataclasses import dataclass, field
from typing import Callable, Iterable, Sequence

from dante_corpus.dep import DepRow, load_dep
from dante_corpus.skel.models import SkelRow

from harness.extractor.observe import Observation, observe_rows, render_observations
from harness.runner.prompts import fixed_system_prompt

__all__ = [
    "MAX_ITERATIONS",
    "FixedUnitResult",
    "IterationRecord",
    "fixed_fallback",
    "parse_rows",
    "render_sigma",
    "rows_from_skel",
    "run_unit_fixed",
    "unit_message",
    "verdict_block",
]

# How many times one unit may be asked. A cap on cost, not a target: a unit that
# settles stops earlier, and one that does not is left as it stands (module
# docstring, "the budget is a cap").
MAX_ITERATIONS = 4

_TSV_HEADER = ("line", "token", "word", "role", "arg_line", "arg_token")
_ROWS_BLOCK = re.compile(r"<rows>(.*?)</rows>", re.DOTALL | re.IGNORECASE)


# --- $\Sigma$: rows in, rows out --------------------------------------------------------


def rows_from_skel(rows_by_line: dict[int, list[SkelRow]] | None) -> list[dict]:
    """Candidate-row dicts for the artifact's own `SkelRow`s (the `--fix` $\\Sigma_0$)."""
    if not rows_by_line:
        return []
    out: list[dict] = []
    for no in sorted(rows_by_line):
        for row in rows_by_line[no]:
            out.append(
                {
                    "line": row.line,
                    "token": row.token,
                    "word": row.word,
                    "role": row.role,
                    "arg_line": row.arg_line,
                    "arg_token": row.arg_token,
                }
            )
    return out


def _row_key(row: dict) -> tuple:
    return (
        int(row.get("line", 0)),
        int(row.get("token", 0)),
        str(row.get("role", "")),
        int(row.get("arg_line", 0)),
        int(row.get("arg_token", 0)),
    )


def _same_rows(left: Sequence[dict], right: Sequence[dict]) -> bool:
    """Are these the same analysis? The word column is an anchor, not content."""
    return sorted(_row_key(r) for r in left) == sorted(_row_key(r) for r in right)


def render_sigma(rows: Sequence[dict]) -> str:
    """$\\Sigma$ as the TSV table the artifact itself holds."""
    if not rows:
        return "(no rows on record for this unit yet)"
    out = ["\t".join(_TSV_HEADER)]
    for row in sorted(rows, key=_row_key):
        out.append(
            f"{row.get('line', 0)}\t{row.get('token', 0)}\t{row.get('word', '')}\t"
            f"{row.get('role', '')}\t{row.get('arg_line', 0)}\t"
            f"{row.get('arg_token', 0)}"
        )
    return "\n".join(out)


def parse_rows(text: str) -> list[dict]:
    """The rows of the answer's `<rows>` block, or [] when there is none to read.

    Tolerant in exactly the ways a tab-separated block goes wrong and no others:
    the block may be fenced or indented, a repeated header line is dropped, and
    lines whose predicate token is 0 (the artifact's "this line has no rows"
    filler) are not rows. Anything else that does not parse as six fields with
    four integers among them is skipped — the schema gate then sees a submission
    missing those rows, which is the honest report.
    """
    match = _ROWS_BLOCK.search(text or "")
    if match is None:
        return []
    rows: list[dict] = []
    for raw in match.group(1).splitlines():
        line = raw.strip("\r").strip()
        if not line or line.startswith("#") or line.startswith("```"):
            continue
        fields = [f.strip() for f in raw.strip("\r").split("\t")]
        if len(fields) < 6:
            # A model that used spaces instead of tabs still gets read, provided
            # the row is unambiguous: six whitespace-separated fields, or five
            # with the optional word column left out.
            fields = line.split()
            if len(fields) == 5:
                fields = [fields[0], fields[1], "", fields[2], fields[3], fields[4]]
            if len(fields) != 6:
                continue
        fields = fields[:6]
        if [f.lower() for f in fields] == list(_TSV_HEADER):
            continue
        try:
            line_no, token = int(fields[0]), int(fields[1])
            arg_line, arg_token = int(fields[4]), int(fields[5])
        except ValueError:
            continue
        if token <= 0:
            continue  # the empty-line filler, not a row
        rows.append(
            {
                "line": line_no,
                "token": token,
                "word": fields[2],
                "role": fields[3],
                "arg_line": arg_line,
                "arg_token": arg_token,
            }
        )
    return rows


# --- $O$: evidence + verdict ---------------------------------------------------------------


def verdict_block(
    *,
    schema_errors: Sequence[str],
    observations: Sequence[Observation],
    empty: bool,
    unparsed: bool = False,
) -> str:
    """The verdict half of $O$: what the runtime found in the rows on record.

    Three states, and the wording says which one it is, because the model's next
    move differs: nothing on record yet (analyse the unit), the schema gate
    refused the last answer (that answer was not recorded — repair it), or the
    rows stand and the frozen layers raise these points.
    """
    if unparsed:
        return (
            "<verdict>\n"
            "Your last answer carried no readable <rows> block, so nothing was "
            "recorded. Send the whole unit's rows inside one <rows> block, six "
            "tab-separated fields per row.\n"
            "</verdict>"
        )
    if empty and not schema_errors:
        return (
            "<verdict>\n"
            "Nothing is on record for this unit yet. Analyse it and submit the "
            "rows you stand behind.\n"
            "</verdict>"
        )
    parts: list[str] = []
    if schema_errors:
        parts.append(
            "The schema check refused your last answer, so it was NOT recorded "
            "and the rows above still stand. It reported:\n"
            + "\n".join(f"- {e}" for e in schema_errors)
        )
    if observations:
        parts.append(
            "Reviewing the rows above against the frozen layers raised these "
            "points:\n" + render_observations(observations)
        )
    if not parts:
        parts.append(
            "The rows above pass the schema check and the frozen layers raise "
            "nothing against them."
        )
    parts.append(
        "Re-solve the unit with that in hand. Keep every row your own reading "
        "still supports, change what the points above concern, and send the "
        "whole unit — not just the changed rows."
    )
    return "<verdict>\n" + "\n\n".join(parts) + "\n</verdict>"


def unit_message(*, evidence: dict, rows: Sequence[dict], verdict: str) -> str:
    """The single user message: evidence, the rows on record, the verdict.

    Its size is a function of the unit, never of the iteration — which is the
    property the whole stage exists for.
    """
    return (
        "<evidence>\n"
        + json.dumps(evidence, ensure_ascii=False)
        + "\n</evidence>\n\n"
        "<rows_on_record>\n"
        + render_sigma(rows)
        + "\n</rows_on_record>\n\n"
        + verdict
    )


# --- the loop -------------------------------------------------------------------------------


@dataclass
class IterationRecord:
    """What one step did, in the terms §2.1 states it in."""

    iteration: int
    rows_in: int
    rows_out: int
    accepted: bool
    valid: bool
    reason: str  # "accepted" | "schema_invalid" | "unparsed"
    schema_errors: list[str] = field(default_factory=list)
    observations: list[dict] = field(default_factory=list)
    seconds: float = 0.0

    def to_dict(self) -> dict:
        return {
            "iteration": self.iteration,
            "rows_in": self.rows_in,
            "rows_out": self.rows_out,
            "accepted": self.accepted,
            "valid": self.valid,
            "reason": self.reason,
            "schema_errors": list(self.schema_errors),
            "observations": list(self.observations),
            "seconds": round(self.seconds, 3),
        }


@dataclass
class FixedUnitResult:
    """One unit's fixed-context run — the `UnitResult` surface `reconstruct.py` reads.

    `candidate_rows`, `final_submission_valid` and `validations` carry the same
    meaning as their tool-calling counterparts had, so `reconstruct_canto` and
    `outcome.final_validation_errors` consume this unchanged. What has no
    counterpart is deliberate: there is no transcript, no nudge and no turn
    budget, because there is no session.
    """

    unit: dict
    rows: list[dict] = field(default_factory=list)
    iterations: list[IterationRecord] = field(default_factory=list)
    turn_seconds: list[float] = field(default_factory=list)
    stop_reason: str = "settled"  # settled | fixed_point | budget | unanswered
    observations: list[dict] = field(default_factory=list)
    invalid_nudges: int = 0  # no such policy here; kept for the record shape

    @property
    def candidate_rows(self) -> list[dict]:
        return self.rows

    @property
    def validations(self) -> list[dict]:
        """Every gate verdict, in call order — the shape `outcome.py` reads."""
        return [
            {
                "ok": True,
                "tool": "validate_candidate",
                "result": {
                    "valid": record.valid,
                    "errors": list(record.schema_errors),
                },
            }
            for record in self.iterations
            if record.reason != "unparsed"
        ]

    @property
    def final_submission_valid(self) -> bool | None:
        """Did any answer pass the gate, or None if no iteration ran.

        The rows handed downstream are the last *accepted* ones, so this reports
        acceptance rather than the last answer — which may have been refused and
        discarded, leaving $\\Sigma$ as it was (refusal is the identity).
        """
        if not self.iterations:
            return None
        return any(record.accepted for record in self.iterations)

    def to_dict(self) -> dict:
        return {
            "unit": dict(self.unit),
            "rows": len(self.rows),
            "stop_reason": self.stop_reason,
            "iterations": [r.to_dict() for r in self.iterations],
            "observations": list(self.observations),
        }


def _dep_rows(canticle: str, canto: int, cache: dict) -> dict[int, Iterable[DepRow]]:
    key = (canticle, canto)
    if key not in cache:
        cache[key] = load_dep(canticle, canto)
    return cache[key]


def run_unit_fixed(
    *,
    toolkit,
    generate: Callable[[list[dict]], str],
    canticle: str,
    canto: int,
    line_start: int,
    line_end: int | None = None,
    rows: Sequence[dict] | None = None,
    max_iterations: int = MAX_ITERATIONS,
    dep_cache: dict | None = None,
    session_scope: Callable[[], AbstractContextManager] | None = None,
    progress_stream=None,
) -> FixedUnitResult:
    """Iterate the bounded step over one parse unit until it settles.

    `toolkit` is a `runner.tools.GrammarToolkit` (the masked path: `read_unit`
    for the evidence, `validate_candidate` as the runtime gate). `generate` takes
    a `[system, user]` message list and returns the answer text — the same
    callable `runner.llm.llm7shi_generate` builds, whose `reset()` is called
    before every iteration so no history accumulates.

    `rows` is $\\Sigma_0$: the unit's recorded rows for a repair, empty (the
    default) for a fresh unit. The return value's `rows` is $\\Sigma_n$, which is
    $\\Sigma_0$ unchanged when every step refused.
    """
    evidence = toolkit.read_unit(canticle, canto, line_start, line_end)
    bounds = evidence["unit"]
    start, end = bounds["line_start"], bounds["line_end"]
    deps = _dep_rows(canticle, canto, dep_cache if dep_cache is not None else {})

    result = FixedUnitResult(
        unit={
            "canticle": canticle,
            "canto": canto,
            "line_start": start,
            "line_end": end,
        },
        rows=[dict(r) for r in (rows or [])],
    )
    system = fixed_system_prompt()
    schema_errors: list[str] = []
    unparsed = False

    for iteration in range(1, max_iterations + 1):
        rows_in = len(result.rows)
        observations = observe_rows(
            result.rows, deps, line_start=start, line_end=end
        )
        if (
            iteration > 1
            and result.rows
            and not schema_errors
            and not observations
            and not unparsed
        ):
            result.stop_reason = "settled"
            break
        verdict = verdict_block(
            schema_errors=schema_errors,
            observations=observations,
            empty=not result.rows,
            unparsed=unparsed,
        )
        user = unit_message(
            evidence=evidence, rows=result.rows, verdict=verdict
        )
        reset = getattr(generate, "reset", None)
        if callable(reset):
            # The fixed context, enforced rather than assumed: the backend
            # adapter starts each iteration with no history, so what goes on the
            # wire is exactly [system, user].
            reset()
        began = time.monotonic()
        scope = session_scope() if session_scope is not None else nullcontext()
        with scope:
            text = generate([
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ])
        seconds = time.monotonic() - began
        result.turn_seconds.append(seconds)

        proposed = parse_rows(text or "")
        if not proposed:
            unparsed = True
            schema_errors = []
            record = IterationRecord(
                iteration=iteration,
                rows_in=rows_in,
                rows_out=0,
                accepted=False,
                valid=False,
                reason="unparsed",
                observations=[o.to_dict() for o in observations],
                seconds=seconds,
            )
            result.iterations.append(record)
            _announce(progress_stream, canticle, canto, start, end, record)
            continue

        unparsed = False
        verdict_result = toolkit.validate_candidate(
            canticle, canto, start, proposed
        )
        valid = bool(verdict_result.get("valid"))
        errors = [str(e) for e in verdict_result.get("errors", [])]
        settled_now = False
        if valid:
            # The step's only state transition. Everything else is `id`.
            same = _same_rows(proposed, result.rows)
            result.rows = proposed
            schema_errors = []
            if same:
                settled_now = True
        else:
            schema_errors = errors
        record = IterationRecord(
            iteration=iteration,
            rows_in=rows_in,
            rows_out=len(proposed),
            accepted=valid,
            valid=valid,
            reason="accepted" if valid else "schema_invalid",
            schema_errors=errors,
            observations=[o.to_dict() for o in observations],
            seconds=seconds,
        )
        result.iterations.append(record)
        _announce(progress_stream, canticle, canto, start, end, record)
        if settled_now:
            # $\Sigma_{t+1} = \Sigma_t$: the model, shown the points, stands by
            # what it has. Iterating again would ask the same question.
            result.stop_reason = "fixed_point"
            break
    else:
        result.stop_reason = "budget"

    final = observe_rows(result.rows, deps, line_start=start, line_end=end)
    result.observations = [o.to_dict() for o in final]
    if result.stop_reason == "budget" and not result.rows:
        result.stop_reason = "unanswered"
    elif result.stop_reason == "budget" and not final and not schema_errors:
        result.stop_reason = "settled"
    return result


def _announce(stream, canticle: str, canto: int, start: int, end: int, record) -> None:
    if stream is None:
        return
    print(
        f"[fixed] {canticle} {canto} L{start}-{end} iter {record.iteration}: "
        f"{record.rows_out} row(s), {record.reason}"
        + (
            f", {len(record.observations)} observation(s)"
            if record.observations
            else ""
        ),
        file=stream,
        flush=True,
    )


# --- the callable `reconstruct.py` drives ---------------------------------------------------


def fixed_fallback(
    *,
    model: str | None = None,
    verbose: bool = False,
    file=None,
    request_log=None,
    payload_tier: str = "R1",
    min_send_interval: float = 0.0,
    max_length: int | None = None,
    max_iterations: int = MAX_ITERATIONS,
    rows_for: Callable[[str, int, int, int], Sequence[dict] | None] | None = None,
):
    """Build the live fixed-context callable, shaped like `agent_fallback`'s.

    Same seam, same signature (`canticle`, `canto`, `line_start`, `line_end`), so
    `HybridEngine.run_unit` and `reconstruct.py`'s gates consume it unchanged —
    what differs is entirely behind it: no transport, no tool specs, no session.

    `rows_for`, when given, supplies $\\Sigma_0$ per unit (the recorded rows under
    `--fix`); without it every unit starts empty, which is a fresh reconstruction.
    Model-facing imports stay lazy, so importing this module touches no network.
    """
    from harness.runner.llm import (
        _LLM_REQUEST_CONTEXT,
        _SESSION_SEQ,
        DEFAULT_MODEL,
        llm7shi_generate,
    )
    from harness.runner.tools import GrammarToolkit

    model = DEFAULT_MODEL if model is None else model
    generate = llm7shi_generate(
        model,
        quiet=not verbose,
        file=file,
        request_log=request_log,
        min_send_interval=min_send_interval,
        max_length=max_length,
    )
    # `clausal_registration` stays on: every answer carries the whole unit here
    # by construction, which is the condition that check needs. No fix-level
    # flag is passed — the level's bar is the frozen-layer observation the
    # runtime recomputes each iteration (`observe.py`), not a gate the model
    # must satisfy to be heard at all.
    toolkit = GrammarToolkit(payload_tier=payload_tier, clausal_registration=True)
    dep_cache: dict = {}

    def _run(*, canticle: str, canto: int, line_start: int, line_end: int):
        @contextlib.contextmanager
        def _session():
            # One session id per iteration: each request IS an independent
            # single-turn session here, so the log's (session, messages,
            # attempt) join key stays unique instead of colliding on a
            # transcript position that never advances.
            token = _LLM_REQUEST_CONTEXT.set(
                {
                    "session": next(_SESSION_SEQ),
                    "canticle": canticle,
                    "canto": canto,
                    "line_start": line_start,
                    "line_end": line_end,
                }
            )
            try:
                yield
            finally:
                _LLM_REQUEST_CONTEXT.reset(token)

        rows = (
            rows_for(canticle, canto, line_start, line_end)
            if rows_for is not None
            else None
        )
        return run_unit_fixed(
            toolkit=toolkit,
            generate=generate,
            canticle=canticle,
            canto=canto,
            line_start=line_start,
            line_end=line_end,
            rows=rows,
            max_iterations=max_iterations,
            dep_cache=dep_cache,
            session_scope=_session,
            progress_stream=file if file is not None else sys.stderr,
        )

    return _run
