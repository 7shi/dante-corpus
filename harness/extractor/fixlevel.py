"""Stage-6 soft repair levels: which soft findings a `--fix <level>` run acts on.

The recon corpus is hard-clean and everything left is soft (`../stages/06.md`), but
[`../SOFT.md`](../SOFT.md) record S6.1 established that the soft counter is a
*conformance* measure, not a referee: each class must first be resolved to one of
three outcomes — the artifact is wrong, the derivation is silent (a tolerance is
missing), or the two notations are equivalent — and only the first licenses an
edit. Levels are that resolution, made explicit and cumulative: a level names the
classes whose outcome has been argued from the layer's own contract, and
`--fix N` acts on levels 1..N.

**Level 1 — `oblique_qualification`.** The artifact writes bare `obl` where the
derivation determines `obl:<prep>` (377 findings, SOFT.md §3). Its authority:
`derive.py`'s `_oblique_role_of` qualifies an oblique with the lemma of its
Layer-4 `case` child and emits bare `obl` only when there is none, and registry
rule **L** (`rules.py` `_oblique_lemma_refinement`) tolerates strictly the
*opposite* direction — a given `obl:<lemma>` against a derived bare `obl` at an
argument with no case child. The direction repaired here is one the registry
deliberately does not excuse, the evidence sits in the frozen layers (an L4 `case`
edge plus its L2 lemma), and the under-specified side is the artifact. Outcome 1.

**Level 2 — `omitted_l4_argument`.** The artifact registers the predicate but omits
an argument Layer 4 attaches to it directly (1,126 findings, `../stages/08.md` S8.1).
Its authority: `derive.py`'s step 2 collects a predicate's arguments as its own
Layer-4 children under `ARG_DEPRELS`, so a child under one of those relations *is*
an argument of that predicate on the frozen tree — and the 20 `missing_arg`
tolerances of the registry have already been offered this position and declined it.
The evidence is a single tree edge the model already reads, and the under-complete
side is the artifact. Outcome 1.

Two restrictions, both from the contract rather than from taste. **The argument must
be the predicate's own Layer-4 child**: `derive_unit` also reaches arguments stranded
on a `cop`/`aux` head (rule AM) and propagates a subject down a `conj` chain (step 3),
but those are inferences of the derivation, not edges — 404 of the corpus's
`missing_arg` findings are the propagated subject, and no reading of one tree edge
settles them. **The derived role must be nominal**: a `ccomp`/`xcomp` citation is
hard-invalid unless the argument is *also* registered as a predicate of the unit, so
those 74 findings are a compound repair whose second half is `missing_tuple`'s
unargued question. Every row this level asks for is anchored on a Layer-4 argument
position, which is clause AF of `validate.py`'s own anchor rule — so the session's
gate cannot refuse it, which is the alignment S6.10 says to check before running.

**What may cross into a session.** S5.5 kept soft findings out of the agent's
session because they are `derive_unit`'s own answer, and handing those back would
void the autonomy premise (`../PLAN.md` §1). This module keeps that line: a notice
names the *invariant and the position*, with the frozen-layer evidence that the
position triggers it. The derived label is never rendered — the model re-derives
it from the layers it already reads. Nothing here opens gold.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable

from dante_corpus.dep import DepRow
from dante_corpus.morph import Violation
from dante_corpus.skel.derive import ARG_DEPRELS
from dante_corpus.skel.models import OBL_RE, SkelRow

# The TSV column names, mirrored from `artifact._TSV_HEADER` (imported there
# rather than here to keep this module free of the driver's import weight).
_TABLE_HEADER = ("line", "token", "word", "role", "arg_line", "arg_token")


def case_children(
    dep_rows: dict[int, Iterable[DepRow]], position: tuple[int, int]
) -> list[DepRow]:
    """The Layer-4 `case` children of `position`, in token order.

    The evidence `derive.py`'s `_oblique_role_of` reads to decide between bare
    `obl` and `obl:<prep>`; recomputed here from the frozen layer rather than
    imported from the derivation, so a notice cites the tree and not the answer.
    """
    line, token = position
    kids = [
        row
        for rows in dep_rows.values()
        for row in rows
        if row.deprel == "case"
        and (row.head_line, row.head_token) == (line, token)
    ]
    kids.sort(key=lambda row: (row.line, row.token))
    return kids


def argument_edge(
    dep_rows: dict[int, Iterable[DepRow]],
    predicate: tuple[int, int],
    position: tuple[int, int],
) -> DepRow | None:
    """The Layer-4 edge making `position` an argument-child of `predicate`, if any.

    The evidence `derive.py`'s step 2 reads to collect a predicate's arguments: a
    child of the predicate under one of `ARG_DEPRELS`. Recomputed here from the
    frozen layer rather than imported from the derivation, so a notice cites the
    tree and not the answer. `None` when Layer 4 draws no such edge — including
    when the derivation reached the position some other way (rule AM's `cop`/`aux`
    stranding, the `conj` subject propagation), which level 2 does not select.
    """
    for rows in dep_rows.values():
        for row in rows:
            if (
                (row.line, row.token) == position
                and (row.head_line, row.head_token) == predicate
                and row.deprel in ARG_DEPRELS
            ):
                return row
    return None


# --- the classes ------------------------------------------------------------------------


# One artifact row, identified the way `reconstruct.row_delta` identifies it:
# predicate and argument, without the role — so a relabel keeps its key.
RowKey = tuple[int, int, int, int]


@dataclass(frozen=True)
class FixClass:
    """One soft class a fix level acts on, with the notice that describes it."""

    name: str
    # Selects the findings this class owns, out of `validate_unit`'s soft output.
    # Takes the canto's Layer-4 rows too, because a class may be defined by the
    # tree and not by the finding's own text (level 2 is: the same `missing_arg`
    # detail is one class when the argument is the predicate's own argument-child
    # and another when the derivation reached it by inference). Pass the layer
    # wherever the definition is applied — `fix_verdict` included, since it must
    # apply one definition to the before- and after-count.
    matches: Callable[[Violation, dict[int, Iterable[DepRow]]], bool]
    # Renders the position's notice: the invariant + the frozen-layer evidence,
    # never the derived label.
    notice: Callable[[Violation, dict[int, Iterable[DepRow]]], str]
    # The artifact rows one finding of this class governs, as
    # `(pred_line, pred_token, arg_line, arg_token)` keys. A level names a *row*
    # while a session answers a whole *unit*, and this is where that difference
    # is written down: a refused whole-unit answer may still be taken at exactly
    # these keys and nowhere else (`reconstruct.salvage_rows`, `../stages/06.md`).
    keys: Callable[[Violation], frozenset[RowKey]]
    # Does the artifact actually hold the row this class would repair? A repair
    # level acts on a row, so a finding naming a row the artifact does not have
    # is not work this level can do — the precondition `select` applies wherever
    # the rows are in hand (`../stages/06.md` S6.9).
    holds: Callable[[Violation, dict[int, list[SkelRow]]], bool]


def _is_oblique_qualification(
    v: Violation, dep_rows: dict[int, Iterable[DepRow]] | None = None
) -> bool:
    """`role_mismatch` where the artifact wrote bare `obl` and the derivation qualifies it.

    The direction rule L does *not* excuse (see the module docstring). `given_role`
    is the artifact's label and `role` the derived one — `rules.py`'s
    `_classify_divergence` fills both only for this class.
    """
    return (
        v.kind == "tag"
        and v.detail.startswith("role_mismatch:")
        and v.given_role == "obl"
        and v.role is not None
        and bool(OBL_RE.fullmatch(v.role))
    )


def _oblique_qualification_notice(
    v: Violation, dep_rows: dict[int, Iterable[DepRow]]
) -> str:
    arg = v.arg or (0, 0)
    pred = v.predicate or (v.line, 0)
    where = f"predicate {pred[0]}.{pred[1]}, argument {arg[0]}.{arg[1]}, role 'obl'"
    kids = case_children(dep_rows, arg)
    if kids:
        evidence = ", ".join(f"{row.line}.{row.token} {row.word!r}" for row in kids)
        return (
            f"{where}: this oblique argument carries a Layer-4 `case` child "
            f"({evidence}). A bare 'obl' is reserved for an oblique with no case "
            f"marker; an oblique that has one must name it — qualify the role with "
            f"that preposition's Layer-2 lemma in its base, non-articulated form "
            f"('obl:<lemma>')."
        )
    # No `case` edge: the qualification is carried by the argument itself — an
    # oblique clitic whose own case marking names the relation. Same invariant
    # (a bare 'obl' claims there is nothing to name), different evidence, and the
    # relation is still the model's to read off Layers 1-4 and the case annex.
    return (
        f"{where}: this oblique argument is a form whose own case marking names "
        f"the relation, though no `case` token stands beside it. A bare 'obl' "
        f"claims there is nothing to name — read the argument's case (Layer 2 and "
        f"the pronoun case annex) and qualify the role with the preposition that "
        f"relation would take ('obl:<lemma>'), or choose the direct role if that "
        f"is what the case supports."
    )


def _oblique_qualification_keys(v: Violation) -> frozenset[RowKey]:
    """The single row the finding is about: this predicate's oblique argument.

    The repair is a relabel in place — `obl` to `obl:<lemma>` at one predicate /
    argument pair — so the finding governs exactly one key, and a position-scoped
    replacement can neither add nor remove a row of this unit.
    """
    pred = v.predicate or (v.line, 0)
    arg = v.arg or (0, 0)
    return frozenset({(pred[0], pred[1], arg[0], arg[1])})


def _oblique_qualification_holds(
    v: Violation, rows_by_line: dict[int, list[SkelRow]]
) -> bool:
    """Is there a bare `obl` row at the position this finding names?

    Normally yes — the finding *is* that row. But `rules.py`'s divergence classifier
    compares two maps keyed by argument position, and registry rules C
    (`_collapse_coordination`) and BJ (`_merge_adverb_cluster_citations`) rewrite
    those keys before the comparison: two of the artifact's own citations can be
    collapsed onto one key, where the surviving role silently replaces the other.
    The finding then reports `'obl' vs 'obl:<prep>'` at a position whose artifact
    row already *is* `obl:<prep>`, and the notice built from it describes a row
    that does not exist — the session reads its own rows in the same block, sees
    the work already done, and correctly changes nothing (`../stages/06.md` S6.9:
    both of the two non-deadlocked survivors, and 2 of the 14 in total).

    Whether the artifact is over-complete at those positions or the two notations
    are equivalent is a question for §2's three outcomes, unargued either way — so
    this is not a repair to make quietly, and the level declines it.
    """
    key = next(iter(_oblique_qualification_keys(v)))
    return any(
        (r.line, r.token, r.arg_line, r.arg_token) == key and r.role == "obl"
        for rows in rows_by_line.values()
        for r in rows
    )


OBLIQUE_QUALIFICATION = FixClass(
    name="oblique_qualification",
    matches=_is_oblique_qualification,
    notice=_oblique_qualification_notice,
    keys=_oblique_qualification_keys,
    holds=_oblique_qualification_holds,
)


# Roles a level-2 repair may not be asked for: `''` is the zero-argument marker,
# `attr` needs no anchor, and a `ccomp`/`xcomp` citation is hard-invalid unless the
# argument is registered as a predicate of the unit too (`validate.py`'s clausal
# check) — a compound repair this level does not define.
_NON_NOMINAL_ROLES = frozenset({"", "attr", "xcomp", "ccomp"})


def _is_omitted_l4_argument(
    v: Violation, dep_rows: dict[int, Iterable[DepRow]] | None = None
) -> bool:
    """`missing_arg` at a nominal role whose argument is the predicate's own L4 child.

    The module docstring carries the argument; this is where its two restrictions
    are enforced. Without the tree the class selects nothing — the finding's own
    text cannot tell an argument-child from a position the derivation inferred, and
    a class that cannot see its evidence declines rather than guesses.
    """
    if (
        v.kind != "tag"
        or not v.detail.startswith("missing_arg:")
        or v.predicate is None
        or v.arg is None
        or v.role is None
        or v.role in _NON_NOMINAL_ROLES
    ):
        return False
    return argument_edge(dep_rows or {}, v.predicate, v.arg) is not None


def _omitted_l4_argument_notice(
    v: Violation, dep_rows: dict[int, Iterable[DepRow]]
) -> str:
    pred = v.predicate or (v.line, 0)
    arg = v.arg or (0, 0)
    edge = argument_edge(dep_rows, pred, arg)
    word = f" {edge.word!r}" if edge is not None else ""
    relation = f"`{edge.deprel}`" if edge is not None else "an argument relation"
    return (
        f"predicate {pred[0]}.{pred[1]}, argument {arg[0]}.{arg[1]}{word}: Layer 4 "
        f"hangs this token on that predicate under {relation}, one of the relations "
        f"that carries an argument of its head, and the analysis on record gives "
        f"the predicate no argument at that position at all. An argument the tree "
        f"attaches here belongs in the predicate's frame: cite it, with the role "
        f"its relation and its own morphology support. If your reading makes it "
        f"something the predicate does not govern, leave the frame as it stands."
    )


def _omitted_l4_argument_keys(v: Violation) -> frozenset[RowKey]:
    """The row the finding asks for, and — for a subject — the null slot it fills.

    The repair adds a row, so the governed key is one the artifact does not yet
    hold; a position-scoped splice takes the answer's row there and nothing else.
    A derived **subject** governs the predicate's `(0, 0)` key as well, because a
    pro-drop `subj (0, 0)` on record and an overt subject the tree attaches are two
    fillings of one slot: without that key a splice would keep both and leave the
    predicate with two subjects. Every other role leaves `(0, 0)` alone — the null
    position is for a dropped subject only (`validate.py`'s `NULL_ARG_ROLES`), so
    it is never the slot an object or an oblique would vacate.
    """
    pred = v.predicate or (v.line, 0)
    arg = v.arg or (0, 0)
    keys = {(pred[0], pred[1], arg[0], arg[1])}
    if v.role == "subj":
        keys.add((pred[0], pred[1], 0, 0))
    return frozenset(keys)


def _omitted_l4_argument_holds(
    v: Violation, rows_by_line: dict[int, list[SkelRow]]
) -> bool:
    """Is there a registered predicate here with no row at the named position?

    Two preconditions, both about the row rather than the finding. The predicate
    must be **registered**: an argument missing from a tuple the artifact never
    wrote is `missing_tuple`'s question, and a level that adds the argument alone
    would be inventing the frame. And the artifact must hold **no row at the named
    position** for it: `rules.py`'s key rewrites (C, BJ, AI, BV, EI) can report a
    `missing_arg` at a position whose citation the artifact does carry under a key
    the classifier merged away, and the notice built from it would ask for a row
    that is already there (the level-1 shape of this, `../stages/06.md` S6.9/S6.10).
    """
    pred = v.predicate or (v.line, 0)
    arg = v.arg or (0, 0)
    rows = [r for rs in rows_by_line.values() for r in rs]
    registered = any((r.line, r.token) == pred for r in rows)
    cited = any(
        (r.line, r.token) == pred and (r.arg_line, r.arg_token) == arg for r in rows
    )
    return registered and not cited


OMITTED_L4_ARGUMENT = FixClass(
    name="omitted_l4_argument",
    matches=_is_omitted_l4_argument,
    notice=_omitted_l4_argument_notice,
    keys=_omitted_l4_argument_keys,
    holds=_omitted_l4_argument_holds,
)

# Cumulative: level N acts on levels 1..N. A class joins the table only once its
# outcome has been argued from the contract (`../stages/06.md` §2).
LEVELS: dict[int, tuple[FixClass, ...]] = {
    1: (OBLIQUE_QUALIFICATION,),
    2: (OMITTED_L4_ARGUMENT,),
}

MAX_LEVEL = max(LEVELS)


MAX_ALIASES = ("max", "all")


def resolve_level(value: str | int) -> int:
    """A CLI level: a number, or `max`/`all` for every level defined so far.

    The level table is the single source of truth for how far repair currently
    reaches, so the drivers ask for `max` rather than restating a number that
    would drift the moment a level is added. Raises `ValueError` on anything else.
    """
    if isinstance(value, str) and value.strip().lower() in MAX_ALIASES:
        return MAX_LEVEL
    try:
        level = int(value)
    except (TypeError, ValueError):
        raise ValueError(
            f"expected a level in 1..{MAX_LEVEL} or "
            f"{'/'.join(MAX_ALIASES)}, got {value!r}"
        ) from None
    if not 1 <= level <= MAX_LEVEL:
        raise ValueError(f"unknown fix level: {level} (1..{MAX_LEVEL})")
    return level


def classes_for(level: int) -> tuple[FixClass, ...]:
    """Every class at `level` and below."""
    if level < 1 or level > MAX_LEVEL:
        raise ValueError(f"unknown fix level: {level} (1..{MAX_LEVEL})")
    return tuple(
        cls for n in range(1, level + 1) for cls in LEVELS.get(n, ())
    )


def toolkit_flags(level: int) -> dict[str, bool]:
    """`GrammarToolkit` kwargs that add this level's bar to the session gate.

    The in-session counterpart of the classes above: while a fix run is live the
    model's own `validate_candidate` rejects the shape the level repairs, exactly
    as S5.5 moved the hard checks into the session. Each flag is a transcription
    of the level's published invariant, never a call into `derive_unit`.

    **Level 2 deliberately adds none**, and that is the S6.10 alignment check made
    before the runs rather than after four of them. A session-side bar sees the
    frozen layers and not the registry, so the only bar it could carry is "cite
    every Layer-4 argument-child of every predicate you register" — measured over
    the committed corpus that demands **2,089** positions where the level selects
    **1,126**, the rest being omissions the checker's own tolerances excuse. That
    is S6.10's second asymmetry — a level's bar and its selection naming different
    positions — at 46% of the pool instead of 2 units in 10, so level 2's ask stays
    in the notice, which names exactly the positions the checker selected.
    """
    names = {cls.name for cls in classes_for(level)}
    return {
        "oblique_case_qualification": "oblique_qualification" in names,
    }


def select(
    violations: Iterable[Violation],
    level: int,
    rows_by_line: dict[int, list[SkelRow]] | None = None,
    dep_rows: dict[int, Iterable[DepRow]] | None = None,
) -> list[Violation]:
    """The findings a `--fix level` run acts on, in the order they were reported.

    With `rows_by_line`, each class's `holds` precondition is applied as well: a
    finding naming a row the artifact does not have is not work this level can do.
    Pass the rows wherever the *selection* is being made — which cantos to launch,
    which units to reopen, which keys a splice may touch. The acceptance test
    (`reconstruct.fix_verdict`) deliberately does not: it compares a before-count
    with an after-count and must apply one definition to both sides, where the two
    sides are different sets of rows.

    `dep_rows` is the class *definition*'s input, not a precondition, so it belongs
    everywhere the definition is applied — the acceptance test included. A class
    that reads the tree selects nothing without it (`_is_omitted_l4_argument`), so
    a caller that forgets it under-selects rather than mis-selects.
    """
    classes = classes_for(level)
    return [
        v
        for v in violations
        if any(
            cls.matches(v, dep_rows or {})
            and (rows_by_line is None or cls.holds(v, rows_by_line))
            for cls in classes
        )
    ]


_DIVERGENCE_KINDS = (
    "missing_tuple", "extra_tuple", "missing_arg", "extra_arg", "role_mismatch"
)


def governed_keys(
    findings: Iterable[Violation],
    level: int,
    dep_rows: dict[int, Iterable[DepRow]] | None = None,
) -> frozenset[RowKey]:
    """Every artifact row this run's own findings name, across their classes.

    The scope a position-scoped replacement is confined to: outside these keys
    the unit's recorded rows stand, whatever else the session's answer proposed.
    """
    keys: set[RowKey] = set()
    for v in findings:
        cls = class_of(v, level, dep_rows)
        if cls is not None:
            keys |= cls.keys(v)
    return frozenset(keys)


def violation_class(v: Violation) -> str:
    """The class name a soft finding is counted under (`recon/check.py --stats`).

    One implementation, used both by the stats readout and by the fix
    acceptance test (which refuses any submission introducing a class the unit
    did not carry before).
    """
    prefix = v.detail.split(":", 1)[0]
    if prefix in _DIVERGENCE_KINDS:
        return prefix
    if prefix == "dual_role":
        return "dual_role"
    if "heads no NP" in v.detail:
        return "membership"
    if "not in frozen vocabulary" in v.detail:
        return "unknown_role"
    return "other"


def class_of(
    v: Violation,
    level: int,
    dep_rows: dict[int, Iterable[DepRow]] | None = None,
) -> FixClass | None:
    for cls in classes_for(level):
        if cls.matches(v, dep_rows or {}):
            return cls
    return None


# --- what the session is shown ------------------------------------------------------------


def render_rows(rows_by_line: dict[int, list[SkelRow]]) -> str:
    """The unit's committed rows as the TSV table the artifact itself holds."""
    out = ["\t".join(_TABLE_HEADER)]
    for no in sorted(rows_by_line):
        rows = rows_by_line[no]
        if not rows:
            out.append(f"{no}\t0\t\t\t0\t0")
            continue
        for row in rows:
            out.append(
                f"{row.line}\t{row.token}\t{row.word}\t{row.role}\t"
                f"{row.arg_line}\t{row.arg_token}"
            )
    return "\n".join(out)


def revision_block(
    rows_by_line: dict[int, list[SkelRow]],
    findings: list[Violation],
    dep_rows: dict[int, Iterable[DepRow]],
    level: int,
) -> str:
    """The prompt block for a fix run: current rows + one notice per finding.

    Deliberately carries no derived role, no `given vs derived` string and no
    count — the model is told which invariant a position breaks and re-derives the
    label itself from Layers 1-4 (module docstring).
    """
    notices = []
    for v in findings:
        cls = class_of(v, level, dep_rows)
        if cls is None:
            continue
        notices.append(f"- {cls.notice(v, dep_rows)}")
    return (
        "<revision>\n"
        "An earlier analysis of this unit is already on record:\n\n"
        f"{render_rows(rows_by_line)}\n\n"
        "Reviewing it against the frozen layers raised these points:\n"
        + "\n".join(notices)
        + "\n\n"
        "Re-solve the unit with that in hand. Keep every row your own reading "
        "still supports, change what the points above concern, and submit the "
        "whole unit — not just the changed rows — through validate_candidate.\n"
        "\n"
        "How your answer will be used: it replaces the rows above only if it "
        "breaks no schema rule, actually settles the points listed, and raises "
        "no *kind* of problem this unit did not already have. If it settles the "
        "points but introduces a different kind elsewhere, only the rows the "
        "points name are taken from it and the rest of the record stands. So "
        "revise beyond those points where your reading genuinely supports it, "
        "and not otherwise.\n"
        "</revision>"
    )
