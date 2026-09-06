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

**Level 3 — `unregistered_predicate`.** The artifact never registers a predicate
Layer 4 makes the head of a clause (334 of the 401 `missing_tuple` findings,
`../stages/10.md` S10.1). Its authority: `derive.py`'s step 1 promotes to a
predicate every token whose own Layer-4 deprel is in `CLAUSE_HEAD_DEPRELS`, so a
token under one of those relations *heads a clause* on the frozen tree, and the
two `missing_tuple` tolerances of the registry (CS, AV) have already been offered
this position and declined it. The evidence is again a single tree edge — the
token's own — and the under-complete side is the artifact. Outcome 1.

One restriction, the same one level 2 makes and for the same reason. **The
predicate must be a clause head by its own deprel**: `derive_unit`'s census also
promotes a conjunct whose `conj` chain resolves against the census (rules CA, AN,
BZ) and, in a second pass, any non-auxiliary verb carrying an argument child, but
the first is a chain walk rather than an edge and the second needs the Layer-2
`pos` a class defined over the tree cannot see. 67 findings sit on those two
routes — 58 `conj` and 9 elsewhere — and the level declines them rather than
guessing, exactly as level 2 declines the propagated subject.

**Why this level's repair is allowed to raise the soft count**, and what still
holds it. Registering a predicate exposes its frame: S6.1 measured 2+ new
`missing_arg` at 227 of the then-490 `missing_tuple` positions, which is why the
soft counter is not a distance and rises on a strict improvement. `fix_verdict`'s
third refusal — no violation *class* the unit did not carry before — would
therefore refuse precisely the answers that do this repair correctly. `exempts` is
where a class declares that narrowly: a new divergence finding **at a predicate
this level's own findings named** is arithmetic, not a traded class, because that
predicate contributed no findings of any of those classes before for the plain
reason that it was not on record. A new class anywhere else is still a refusal,
the submission must still be hard-clean, and the level's own findings must still
strictly fall — so the standing guarantee is unchanged: a fix run cannot leave the
artifact worse than it found it.

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
from dante_corpus.skel.derive import ARG_DEPRELS, CLAUSE_HEAD_DEPRELS
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


def clause_head_edge(
    dep_rows: dict[int, Iterable[DepRow]], position: tuple[int, int]
) -> DepRow | None:
    """`position`'s own Layer-4 edge, when that edge makes it a clause head.

    The evidence `derive.py`'s step 1 reads to promote a token to a predicate: its
    own deprel is one of `CLAUSE_HEAD_DEPRELS`. Recomputed here from the frozen
    layer rather than imported from the derivation, so a notice cites the tree and
    not the answer. `None` when the token heads no clause by its own edge —
    including when the census reached it some other way (the `conj` chain walk, the
    second pass's argument-bearing verb), which level 3 does not select.
    """
    for rows in dep_rows.values():
        for row in rows:
            if (row.line, row.token) == position:
                return row if row.deprel in CLAUSE_HEAD_DEPRELS else None
    return None


def argument_children(
    dep_rows: dict[int, Iterable[DepRow]], predicate: tuple[int, int]
) -> list[DepRow]:
    """Every Layer-4 argument-child of `predicate`, in token order.

    The frame `derive.py`'s step 2 would collect for a predicate — the positions a
    newly registered predicate's rows may land on, which is what makes them the
    keys level 3's findings govern.
    """
    kids = [
        row
        for rows in dep_rows.values()
        for row in rows
        if (row.head_line, row.head_token) == predicate
        and row.deprel in ARG_DEPRELS
    ]
    kids.sort(key=lambda row: (row.line, row.token))
    return kids


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
    # Takes the tree for the same reason `matches` does: level 3's row does not
    # exist in the artifact yet, so the keys it may occupy have to be enumerated
    # from the frozen layer rather than read off the rows.
    keys: Callable[[Violation, dict[int, Iterable[DepRow]]], frozenset[RowKey]]
    # Does the artifact actually hold the row this class would repair? A repair
    # level acts on a row, so a finding naming a row the artifact does not have
    # is not work this level can do — the precondition `select` applies wherever
    # the rows are in hand (`../stages/06.md` S6.9).
    holds: Callable[[Violation, dict[int, list[SkelRow]]], bool]
    # Is a violation class appearing only *after* the repair an arithmetic
    # consequence of this class's own finding, rather than a class traded for
    # another? Takes `(finding, new_violation)`. The default answer is no, which is
    # `fix_verdict`'s third refusal unrelaxed and what levels 1 and 2 both want: a
    # relabel and a single added row have no arithmetic of their own. Level 3 is the
    # exception the field exists for — see the module docstring.
    exempts: Callable[[Violation, Violation], bool] = lambda finding, new: False


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


def _oblique_qualification_keys(
    v: Violation, dep_rows: dict[int, Iterable[DepRow]] | None = None
) -> frozenset[RowKey]:
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


def _omitted_l4_argument_keys(
    v: Violation, dep_rows: dict[int, Iterable[DepRow]] | None = None
) -> frozenset[RowKey]:
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
def _is_unregistered_predicate(
    v: Violation, dep_rows: dict[int, Iterable[DepRow]] | None = None
) -> bool:
    """`missing_tuple` at a token whose own Layer-4 deprel makes it a clause head.

    The module docstring carries the argument; this is where its restriction is
    enforced. Without the tree the class selects nothing — the finding's own text
    cannot tell a clause head from a conjunct the census resolved by walking a
    chain, and a class that cannot see its evidence declines rather than guesses.
    """
    if (
        v.kind != "tag"
        or not v.detail.startswith("missing_tuple:")
        or v.predicate is None
    ):
        return False
    return clause_head_edge(dep_rows or {}, v.predicate) is not None


def _unregistered_predicate_notice(
    v: Violation, dep_rows: dict[int, Iterable[DepRow]]
) -> str:
    pred = v.predicate or (v.line, 0)
    edge = clause_head_edge(dep_rows, pred)
    word = f" {edge.word!r}" if edge is not None else ""
    relation = f"`{edge.deprel}`" if edge is not None else "a clause-head relation"
    kids = argument_children(dep_rows, pred)
    if kids:
        frame = ", ".join(f"{r.line}.{r.token} {r.word!r} ({r.deprel})" for r in kids)
        frame_note = (
            f" Layer 4 hangs {len(kids)} argument-bearing dependent(s) on it "
            f"({frame}); read them, and any the tree leaves implicit, as its frame."
        )
    else:
        frame_note = (
            " Layer 4 hangs no argument-bearing dependent on it, so its frame may "
            "well be a dropped subject or nothing at all — say which."
        )
    return (
        f"predicate {pred[0]}.{pred[1]}{word}: Layer 4 attaches this token under "
        f"{relation}, one of the relations that makes a token the head of its own "
        f"clause, and the analysis on record gives the unit no predicate at that "
        f"position at all. A token heading a clause is a predicate of this unit: "
        f"register it and give it its frame.{frame_note} If your reading makes it "
        f"something other than a clause head, leave the analysis as it stands."
    )


def _unregistered_predicate_keys(
    v: Violation, dep_rows: dict[int, Iterable[DepRow]] | None = None
) -> frozenset[RowKey]:
    """Every key a newly registered predicate's own rows may occupy — the tree's.

    A level names a *row*, and this level's row does not exist yet, so the keys it
    governs have to be enumerated from the frozen layer rather than read off the
    artifact: the predicate paired with each of its Layer-4 argument-children, plus
    its `(0, 0)` slot for a dropped subject or the zero-argument marker. A
    position-scoped splice therefore takes the new predicate's frame exactly where
    the tree attaches one and nowhere else — an argument the derivation reaches by
    inference is `omitted_l4_argument`'s restriction all over again, and a splice
    is not the place to relax it. The whole-unit acceptance path is unaffected: an
    answer that survives `fix_verdict` entire is taken entire.

    Without the tree only the null slot is named, which is `select`'s own rule for
    a class that cannot see its evidence: under-reach rather than mis-reach.
    """
    dep_rows = dep_rows or {}
    pred = v.predicate or (v.line, 0)
    keys = {(pred[0], pred[1], 0, 0)}
    for row in argument_children(dep_rows, pred):
        keys.add((pred[0], pred[1], row.line, row.token))
    return frozenset(keys)


def _unregistered_predicate_holds(
    v: Violation, rows_by_line: dict[int, list[SkelRow]]
) -> bool:
    """Is the predicate really absent from the artifact?

    The mirror of level 2's precondition. `rules.py` compares two predicate
    censuses, and its own key rewrites (I, AV) can report a `missing_tuple` at a
    position the artifact does carry under a token the classifier merged away; the
    notice built from such a finding would ask for a tuple that is already there.
    """
    pred = v.predicate or (v.line, 0)
    return not any(
        (r.line, r.token) == pred
        for rows in rows_by_line.values()
        for r in rows
        if r.token > 0
    )


def _unregistered_predicate_exempts(finding: Violation, new: Violation) -> bool:
    """Is `new` the exposed frame of the predicate `finding` asked to register?

    The narrow exemption the module docstring argues for, keyed on the predicate
    position and nothing else: a divergence finding at a predicate that was not on
    record before is arithmetic the repair itself produced, not a class traded away.
    Anything at another predicate, and anything outside the divergence family, is
    refused as before.
    """
    return (
        new.predicate is not None
        and new.predicate == finding.predicate
        and violation_class(new) in _DIVERGENCE_KINDS
    )


UNREGISTERED_PREDICATE = FixClass(
    name="unregistered_predicate",
    matches=_is_unregistered_predicate,
    notice=_unregistered_predicate_notice,
    keys=_unregistered_predicate_keys,
    holds=_unregistered_predicate_holds,
    exempts=_unregistered_predicate_exempts,
)



# Cumulative: level N acts on levels 1..N. A class joins the table only once its
# outcome has been argued from the contract (`../stages/06.md` §2).
LEVELS: dict[int, tuple[FixClass, ...]] = {
    1: (OBLIQUE_QUALIFICATION,),
    2: (OMITTED_L4_ARGUMENT,),
    3: (UNREGISTERED_PREDICATE,),
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

    **Level 3 adds none either, on the same measurement and a wider margin.** The
    only bar a session-side gate could carry is "register every clause-head token
    of this unit as a predicate" — over the committed corpus that demands **1,715**
    positions where the level selects **334**, a fivefold over-demand, because the
    derivation's own census refuses clause heads its carve-outs (BN, AN) exclude
    and the checker excuses two more classes (CS, AV) on top. A bar that wrong
    would refuse the model's correct answers, which is S6.9's deadlock built on
    purpose, so level 3's ask also stays in the notice. The alignment that *does*
    matter for it — the gate admitting the row it asks for — is the easy direction
    here: `validate.py` puts no anchor condition on a predicate token, only that
    the token exists and matches its word, so a registration is admissible by
    construction (`../stages/10.md` S10.1).
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
            keys |= cls.keys(v, dep_rows or {})
    return frozenset(keys)


def traded_classes(
    before: Iterable[Violation],
    soft_after: Iterable[Violation],
    level: int,
    dep_rows: dict[int, Iterable[DepRow]] | None = None,
) -> set[str]:
    """Violation classes the answer introduced that the unit did not carry — minus
    the ones this level's own repair necessarily exposes.

    The one implementation of `fix_verdict`'s third refusal, shared with
    `salvage_by_row`'s per-step copy of it so the two scopes cannot drift apart. A
    class is *traded* unless some finding of this level's own selection declares it
    arithmetic (`FixClass.exempts`) — which levels 1 and 2 never do, so for them
    this is the plain set difference it has always been.
    """
    before = list(before)
    seen = {violation_class(v) for v in before}
    findings = select(before, level, dep_rows=dep_rows)
    traded: set[str] = set()
    for v in soft_after:
        name = violation_class(v)
        if name in seen:
            continue
        exempt = False
        for finding in findings:
            cls = class_of(finding, level, dep_rows)
            if cls is not None and cls.exempts(finding, v):
                exempt = True
                break
        if not exempt:
            traded.add(name)
    return traded


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
