"""Frozen-layer observation of a unit's rows: the half of $O$ that is not the schema verdict.

Stage 9 (`../stages/09.md` record S9.1) settles what a fixed-context iteration may
carry back to the model as its per-iteration signal $O$:

1. the **hard schema verdict** — closed-world, the rows read against themselves and
   Layer 1 (`runner/tools.py` `validate_candidate`), which the runtime runs rather
   than the model electing to; and
2. a **frozen-layer observation** of the rows, recomputed here from Layers 2-4 in the
   style of `extractor/fixlevel.py`'s `case_children` / `argument_edge` — *never*
   `derive.py`'s own answer, and never the registry-mediated soft counter, which is
   Standing Invariant §4 item 1 through one indirection (`../SOFT.md` S6.1).

This module is that second half, and it is deliberately *not* a fix level. A level
selects `validate_unit` findings, so it inherits the registry's tolerances and its
count; an observation reads the submitted rows against the tree directly, so it says
only "Layer 4 draws this edge and your rows do not cite it" — a statement whose truth
the model can check against evidence it was handed. That is also why the loop's
stopping rule is a fixed point rather than a shrinking count (S9.1): these
observations are not a metric anyone has calibrated, and treating them as one would
smuggle a target back in.

Two observations are implemented, one per class `fixlevel.py` has argued from the
layer's contract:

- **`unqualified_oblique`** — a bare `obl` row whose argument carries a Layer-4
  `case` child (level 1's invariant, its evidence read the same way).
- **`uncited_l4_argument`** — a registered predicate with a Layer-4 argument-child
  inside the unit that none of its rows cite (level 2's invariant).

The counts differ from the levels' by construction, and that is expected rather than
a defect: `fixlevel.toolkit_flags`'s docstring measured the same asymmetry at 2,089
positions against the level's 1,126. A level must agree with the checker it reports
to; an observation answers to the tree alone.

Nothing here opens gold, imports `dante_corpus.skel.derive`'s answer, or reads
`skel/`: the only inputs are the submitted rows and the frozen layers.
"""

from __future__ import annotations

from typing import Iterable, Sequence

from dante_corpus.dep import DepRow, load_dep
from dante_corpus.skel.derive import ARG_DEPRELS

from harness.extractor.fixlevel import case_children

__all__ = [
    "Observation",
    "SkelObserver",
    "observe_rows",
    "render_observations",
]

Position = tuple[int, int]


class Observation:
    """One point the frozen layers raise about the rows as submitted.

    `kind` names the invariant, `position` the (predicate, argument) pair it is
    about, and `text` is what the model is shown — the invariant and the tree
    evidence that triggers it, with no derived label (`fixlevel.py`'s line).
    """

    __slots__ = ("kind", "predicate", "argument", "text")

    def __init__(
        self, kind: str, predicate: Position, argument: Position, text: str
    ) -> None:
        self.kind = kind
        self.predicate = predicate
        self.argument = argument
        self.text = text

    def key(self) -> tuple[str, Position, Position]:
        return (self.kind, self.predicate, self.argument)

    def to_dict(self) -> dict:
        return {
            "kind": self.kind,
            "predicate": list(self.predicate),
            "argument": list(self.argument),
            "text": self.text,
        }

    def __eq__(self, other) -> bool:
        return isinstance(other, Observation) and self.key() == other.key()

    def __hash__(self) -> int:
        return hash(self.key())

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"Observation({self.kind!r}, {self.predicate}, {self.argument})"


def _pred(row: dict) -> Position:
    return (int(row.get("line", 0)), int(row.get("token", 0)))


def _arg(row: dict) -> Position:
    return (int(row.get("arg_line", 0)), int(row.get("arg_token", 0)))


def _unqualified_obliques(
    rows: Sequence[dict], dep_rows: dict[int, Iterable[DepRow]]
) -> list[Observation]:
    """Bare `obl` rows whose argument carries a Layer-4 `case` child.

    The same evidence `fixlevel._oblique_qualification_notice` cites, reached from
    the row rather than from a finding: there is no violation object here, because
    nothing has consulted the derivation.
    """
    found: list[Observation] = []
    for row in rows:
        if str(row.get("role", "")) != "obl":
            continue
        arg = _arg(row)
        if arg == (0, 0):
            continue
        kids = case_children(dep_rows, arg)
        if not kids:
            continue
        pred = _pred(row)
        evidence = ", ".join(f"{k.line}.{k.token} {k.word!r}" for k in kids)
        found.append(
            Observation(
                "unqualified_oblique",
                pred,
                arg,
                f"predicate {pred[0]}.{pred[1]}, argument {arg[0]}.{arg[1]}, role "
                f"'obl': this oblique argument carries a Layer-4 `case` child "
                f"({evidence}). A bare 'obl' is reserved for an oblique with no "
                f"case marker; an oblique that has one must name it — qualify the "
                f"role with that preposition's Layer-2 lemma in its base, "
                f"non-articulated form ('obl:<lemma>').",
            )
        )
    return found


def _uncited_l4_arguments(
    rows: Sequence[dict],
    dep_rows: dict[int, Iterable[DepRow]],
    line_start: int,
    line_end: int,
) -> list[Observation]:
    """Layer-4 argument-children of a registered predicate that no row cites.

    Level 2's invariant, read off the tree: a child of the predicate under one of
    `ARG_DEPRELS` *is* an argument of its head on the frozen layer. Restricted to
    the unit's own lines, because a row may not cite outside them, and to
    predicates the submission registers — an argument of a frame that was never
    written is `missing_tuple`'s unargued question (`fixlevel.py` §2), not this.
    """
    predicates = {_pred(row) for row in rows if _pred(row)[1] > 0}
    cited: set[tuple[Position, Position]] = {
        (_pred(row), _arg(row)) for row in rows
    }
    found: list[Observation] = []
    seen: set[tuple[str, Position, Position]] = set()
    for predicate in sorted(predicates):
        for line in sorted(dep_rows):
            for dep in dep_rows[line]:
                if (dep.head_line, dep.head_token) != predicate:
                    continue
                if dep.deprel not in ARG_DEPRELS:
                    continue
                position = (dep.line, dep.token)
                if not line_start <= position[0] <= line_end:
                    continue
                if (predicate, position) in cited:
                    continue
                observation = Observation(
                    "uncited_l4_argument",
                    predicate,
                    position,
                    f"predicate {predicate[0]}.{predicate[1]}, argument "
                    f"{position[0]}.{position[1]} {dep.word!r}: Layer 4 hangs this "
                    f"token on that predicate under `{dep.deprel}`, one of the "
                    f"relations that carries an argument of its head, and your "
                    f"rows give the predicate no argument at that position at "
                    f"all. An argument the tree attaches here belongs in the "
                    f"predicate's frame: cite it, with the role its relation and "
                    f"its own morphology support. If your reading makes it "
                    f"something the predicate does not govern, leave the frame as "
                    f"it stands and say why.",
                )
                if observation.key() in seen:
                    continue
                seen.add(observation.key())
                found.append(observation)
    return found


def observe_rows(
    rows: Sequence[dict],
    dep_rows: dict[int, Iterable[DepRow]],
    *,
    line_start: int,
    line_end: int,
) -> list[Observation]:
    """Every frozen-layer point the submitted rows raise, in a stable order.

    `rows` are candidate-row dicts (`line`, `token`, `role`, `arg_line`,
    `arg_token`), the same shape `validate_candidate` takes; `dep_rows` is the
    canto's Layer 4 (`dante_corpus.dep.load_dep`). Empty rows yield no
    observations — an empty record raises nothing about itself, and the loop that
    calls this knows an empty unit is unanswered rather than settled.
    """
    if not rows:
        return []
    return _unqualified_obliques(rows, dep_rows) + _uncited_l4_arguments(
        rows, dep_rows, line_start, line_end
    )


def render_observations(observations: Sequence[Observation]) -> str:
    """The observation notices as the verdict's bullet list."""
    return "\n".join(f"- {o.text}" for o in observations)


class SkelObserver:
    """Layer 5 as the fixed-context loop's `Observer` (`dante_corpus.harness`).

    The loop asks for points per unit and hands back the wording; both of those
    are the layer's, so this is where they stay. It also owns the Layer-4 cache
    the two observation functions read, which is why the loop no longer carries
    a `dep_cache` of its own: one observer serves a whole run, and the cache is
    warm for every unit of a canto after its first.
    """

    def __init__(self) -> None:
        self._dep_cache: dict[tuple[str, int], dict] = {}

    def dep_rows(self, canticle: str, canto: int) -> dict[int, Iterable[DepRow]]:
        key = (canticle, canto)
        if key not in self._dep_cache:
            self._dep_cache[key] = load_dep(canticle, canto)
        return self._dep_cache[key]

    def observe(
        self,
        rows: Sequence[dict],
        *,
        canticle: str,
        canto: int,
        line_start: int,
        line_end: int,
    ) -> list[Observation]:
        return observe_rows(
            rows,
            self.dep_rows(canticle, canto),
            line_start=line_start,
            line_end=line_end,
        )

    def render(self, observations: Sequence[Observation]) -> str:
        return render_observations(observations)
