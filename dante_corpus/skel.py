"""Layer 5 of the grammatical stack: predicate-argument skeleton.

An LLM proposes, per *parse unit* (the same sentence-grouped units as Layer 4 — see
`dep.sentence_groups`, reused here so the two layers stay unit-aligned), a Markdown table
listing every predicate token and its arguments, citing token positions the same way Layer 4
does (`Pred Line`/`Pred Token`/`Arg Line`/`Arg Token`; `Pred Word`/`Arg Word` are build-time
verification anchors only, never stored). Deliberately, **the model is not shown the Layer-4
parse** — it reads the source independently.

That independence is what makes this layer's check meaningful. A layer that only reformatted
Layer 4 could never disagree with it; instead, `derive_unit` computes the same predicate-
argument structure *mechanically* from the frozen Layer 2-4 artifacts, and `validate_unit`'s
soft checks report every place the LLM's tuple set diverges from that derivation. A divergence
is triage material exactly like `dep/CORRECTIONS.md`'s discipline: it may reveal a genuine
Layer-4 mis-parse, an LLM mistake (fixed by `--fix` regeneration), or a legitimate reading the
frozen vocabulary/derivation doesn't yet cover (documented exemption). See PLAN.md.

Role vocabulary is UD-derived (`subj`/`obj`/`iobj`/`attr`/`xcomp`/`ccomp`/`obl:<prep lemma>`),
not semantic (no "locative") — so the LLM's roles and the derivation's roles are directly
comparable, and the corpus stays canon-neutral (PLAN.md's asymmetry: the corpus enumerates what
the text's own grammar determines).

Unlike Layers 2-4, this module also depends on `np`/`dep` (not just `tokenizer`/`_paths`/
`morph`) because the deterministic derivation reads Layer 4 (and, for the membership check,
Layer 3); it still stays free of `api` (which imports it).
"""

from __future__ import annotations

import dataclasses
import re
from dataclasses import dataclass, field
from pathlib import Path

from ._paths import SKEL_DIR
from .case import SLOT_SEP, CaseRow
from .dep import DepRow, index as dep_index, subject_agreement
from .morph import MorphRow, Violation, read_table, strip_word_punct
from .np import NPSpan
from .tokenizer import has_alpha, tokenize

# --- Table columns -----------------------------------------------------------------

# The model emits `| Pred Line | Pred Token | Pred Word | Role | Arg Line | Arg Token |
# Arg Word |`. `Pred Line`/`Pred Token`/`Arg Line`/`Arg Token` are the authoritative indices;
# `Pred Word`/`Arg Word` are verification anchors only (checked at build time, never stored).
_HEADER_ALIASES = {
    "pred line": "line",
    "pred token": "token",
    "pred word": "word",
    "role": "role",
    "arg line": "arg_line",
    "arg token": "arg_token",
    "arg word": "arg_word",
}


def canon_header(header: str) -> str | None:
    return _HEADER_ALIASES.get(header.strip().lower())


# Frozen role vocabulary (measure-then-freeze, mirrors `dep.DEPRELS`; see PLAN.md). `subj`
# merges UD `nsubj`/`nsubj:pass`/`csubj`/`csubj:pass` — passivity/clausal-ness is derivable
# from Layer 4 at serve time, so the skeleton doesn't need separate labels for it. `""` is the
# zero-argument-predicate marker (see `SkelRow`), not a role.
ROLES = frozenset({"subj", "obj", "iobj", "attr", "xcomp", "ccomp", "obl"})
OBL_RE = re.compile(r"obl:[a-zàèéìòù']+")

# Relative-pronoun word forms accepted by the membership soft check regardless of the frozen
# Layer-2 POS tag: "che" is tagged inconsistently between `pronoun` and `conjunction` even in
# its relative use (see `morph/CORRECTIONS.md`), so the word form itself is checked too.
# "ch'" is che's elided form (trailing apostrophe replaces the final "e").
_REL_PRONOUN_WORDS = frozenset({"che", "ch'", "cui", "qual", "quale", "chi"})


def _role_valid(role: str) -> bool:
    return role == "" or role in ROLES or bool(OBL_RE.fullmatch(role))


# --- SkelRow (flat, stored) / SkelArg + SkelTuple (grouped, served) -----------------


@dataclass(frozen=True)
class SkelRow:
    """One (predicate, argument) pair — the artifact's stored unit, like `dep.DepRow`."""

    line: int
    token: int  # 1-based predicate token index; 0 marks a predicate-less-line sentinel
    word: str
    role: str  # "" for a zero-argument predicate's single row; else ROLES or "obl:<lemma>"
    arg_line: int  # (0, 0) marks a pro-drop ∅ subject or a zero-argument predicate's row
    arg_token: int

    def to_dict(self) -> dict[str, object]:
        return {
            "line": self.line,
            "token": self.token,
            "word": self.word,
            "role": self.role,
            "arg_line": self.arg_line,
            "arg_token": self.arg_token,
        }


@dataclass(frozen=True)
class SkelArg:
    role: str
    line: int
    token: int  # (0, 0) = pro-drop ∅

    def to_dict(self) -> dict[str, object]:
        return {"role": self.role, "line": self.line, "token": self.token}


@dataclass(frozen=True)
class SkelTuple:
    """One predicate and its arguments, grouped and identified at serve time."""

    line: int
    token: int
    word: str
    skel_id: str = ""  # derived at serve time: f"{line}.{ordinal}"
    args: tuple[SkelArg, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, object]:
        return {
            "id": self.skel_id,
            "line": self.line,
            "token": self.token,
            "word": self.word,
            "args": [arg.to_dict() for arg in self.args],
        }


# --- Predicate / argument derivation (deterministic; the checker, not the author) --------


def is_verb_pos(pos: str) -> bool:
    """True when a Layer-2 `pos` names `verb` as one of its components.

    A plain substring test would match **`adverb`**: Layer 2's `pos` is a `+`-joined list of
    components (`verb`, `adverb`, `verb+pronoun`, `conjunction+pronoun+verb`), so the test has to
    be on component boundaries."""
    return "verb" in re.split(r"[^a-z]+", pos.lower())


# A token is a predicate if it is a clause head (rule 1) or a non-auxiliary verb that itself
# takes an argument-bearing dependent (rule 2) — see the module docstring and PLAN.md. Both
# rules are UD-deprel-driven so they cover the corpus's two frozen copular styles alike: a
# copula-as-root clause (`è` root, `cosa` attr) and a UD-style adjectival/nominal predicate
# (`amara` head, `è` cop child).
CLAUSE_HEAD_DEPRELS = frozenset({
    "root", "ccomp", "xcomp", "csubj", "csubj:pass",
    "advcl", "acl", "acl:relcl", "parataxis",
})
_SUBJ_DEPRELS = frozenset({"nsubj", "nsubj:pass", "csubj", "csubj:pass"})
_DIRECT_ROLE_MAP = {
    "obj": "obj", "iobj": "iobj", "attr": "attr", "xcomp": "xcomp", "ccomp": "ccomp",
}
ARG_DEPRELS = frozenset(_SUBJ_DEPRELS | set(_DIRECT_ROLE_MAP) | {"obl", "obl:agent"})
_AUX_DEPRELS = frozenset({"aux", "aux:pass", "cop"})

_ROLE_RANK = {"subj": 0, "obj": 1, "iobj": 2, "attr": 3, "xcomp": 4, "ccomp": 5}


def _role_rank(role: str) -> int:
    if role == "":
        return -1
    if role in _ROLE_RANK:
        return _ROLE_RANK[role]
    return 6  # obl / obl:<prep>


def _row_sort_key(row: SkelRow) -> tuple[int, int, int, int]:
    return (row.token, _role_rank(row.role), row.arg_line, row.arg_token)


def _prep_lemma(row: MorphRow) -> str:
    return row.lemma.split("+")[0].strip().lower()


# --- Divergence-check normalization (Phase 1, PLAN.md) -------------------------------
#
# Label-level equivalences the checker treats as identical, not disagreements about the parse:
# archaic/orthographic preposition-lemma variants of the same preposition (measured via
# `--stats`'s role_mismatch pairs table), and two role-label splits for the same UD reading
# (`attr`/`xcomp` for a copular complement, `iobj`/`obl:a` for the dative alternation) — in both
# cases canonicalized to the derived side's convention, per PLAN.md's own instruction.

# Written target-first: every key is a spelling of the value, never a different preposition.
# Three kinds of key, all enumerated from what the corpus actually contains (the `case`-child
# word forms of `dep/`, cross-checked against `--stats`'s role_mismatch pair table): archaic or
# apocopated spellings (`sanz'`, `sovr'`, `ver'`, `'nnanzi`), preposition+article contractions
# (`al`, `dal`, `nel`, `col`, `sul` — the LLM names the contraction, `derive_unit` the base
# preposition, since Layer 2 lemmatizes these as `a+il` and `_prep_lemma` keeps the first part),
# and univerbations Layer 2 analyses as a compound (`inver'` -> `in+verso`, so the derivation
# reports `in`; the family is normalized onto that derived-side convention rather than onto
# `verso`, exactly as this table's docstring above prescribes).
_PREP_LEMMA_NORM = {
    **{k: "senza" for k in ("sanza", "sanz", "sanz'", "sans")},
    **{k: "sopra" for k in ("sovra", "sovr'", "sovr", "sor", "sovresso")},
    **{k: "di" for k in ("de", "de'", "d'", "del", "dei", "dello", "della", "delle", "degli")},
    **{k: "da" for k in ("dal", "da'", "dai", "dallo", "dalla", "dalle", "dagli")},
    **{k: "a" for k in ("ad", "al", "a'", "ai", "alo", "allo", "alla", "alle", "agli", "ab")},
    **{k: "con" for k in ("col", "coi", "co'", "co", "collo", "colla")},
    **{k: "su" for k in ("sul", "su'", "sù", "sui", "sullo", "sulla")},
    **{k: "per" for k in ("pel", "pei", "pe'")},
    **{k: "contro" for k in ("contra", "contr", "contr'")},
    **{k: "verso" for k in ("ver", "ver'")},
    # `in`: article contractions, the apocopated `'n`, and the `in+verso`/`in+vero` compounds.
    **{k: "in" for k in ("nel", "nei", "ne", "ne'", "n'", "nella", "nello", "nelle", "'n",
                         "inver", "inver'", "'nver", "'nver'", "inverso", "'nverso", "invero")},
    **{k: "fino" for k in ("fin", "infin", "infine", "infino", "'nfino", "insin", "insino")},
    **{k: "tra" for k in ("tr'", "fra", "intra", "infra")},
    **{k: "incontra" for k in ("incontr", "incontr'", "incontro", "'ncontro")},
    **{k: "innanzi" for k in ("'nnanzi", "nnanzi")},
    **{k: "intorno" for k in ("dintorno", "d'intorno")},
    **{k: "lungo" for k in ("lunghesso", "lungh'")},
    "sott'": "sotto",
    "apo": "appresso",
}

_ROLE_CANON = {"attr": "xcomp", "iobj": "obl:a"}


def _normalize_prep_lemma(lemma: str) -> str:
    return _PREP_LEMMA_NORM.get(lemma, lemma)


def _canonicalize_role(role: str) -> str:
    if OBL_RE.fullmatch(role):
        prep = role.split(":", 1)[1]
        return f"obl:{_normalize_prep_lemma(prep)}"
    return _ROLE_CANON.get(role, role)


def derive_unit(
    nos: list[int],
    dep_rows_by_line: dict[int, "list[DepRow] | tuple[DepRow, ...]"],
    morph_rows_by_line: dict[int, "list[MorphRow] | tuple[MorphRow, ...]"],
    case_rows_by_line: "dict[int, list[CaseRow] | tuple[CaseRow, ...]] | None" = None,
) -> dict[int, list[SkelRow]]:
    """Mechanically derive the expected skeleton for one parse unit from Layers 2 and 4.

    This is the *checker*, not the artifact's author (see module docstring): its output is
    compared against the LLM's rows by `validate_unit`'s divergence check, never written to
    the artifact itself.

    `case_rows_by_line` is the Layer-2 `case` annex, optional and read at exactly one place —
    rule CZ's slot claim for a gapped-clause remnant. Everywhere else the derivation stays a
    function of Layers 2 and 4 alone, and the annex stays what rule U made it: a third opinion
    consulted only where the other two layers leave the role genuinely undetermined.
    """
    all_rows = [row for no in nos for row in dep_rows_by_line.get(no, ())]
    index = {(row.line, row.token): row for row in all_rows}
    children: dict[tuple[int, int], list[DepRow]] = {}
    for row in all_rows:
        if not (row.head_line == 0 and row.head_token == 0):
            children.setdefault((row.head_line, row.head_token), []).append(row)

    def morph_at(line: int, token: int) -> MorphRow | None:
        rows = morph_rows_by_line.get(line)
        if rows and 1 <= token <= len(rows):
            return rows[token - 1]
        return None

    case_by_pos: dict[tuple[int, int], str] = {
        (row.line, row.token): row.case
        for rows in (case_rows_by_line or {}).values() for row in rows
    }

    # 1. clause-head predicates, plus conj chains that resolve to one.
    #
    # Rule BN: a token Layer 2 calls a **conjunction** that Layer 4 put in a clause-head deprel
    # with no arguments of its own is a connective, not an elided predicate. "**Onde** l'altro
    # lebbroso … rispuose" (inferno 29:124) is `advcl` on `rispuose`, so the derivation minted a
    # predicate at the connective and reported the LLM for not proposing it — a tuple with no
    # arguments in it, which no reading of the line can supply. The `conj` branch below already
    # refuses to promote a coordinating conjunction for the same reason; this is that refusal
    # applied to the clause-head deprels, and the argument test keeps a genuinely gapped clause
    # (a `come` with the compared phrase hanging on it) promoted.
    #
    # Rule AN's clause-head leg: the same reasoning applies to a *non*-conjunct head. "come
    # coltel [fa] le scaglie di scardova" (inferno 29:83) is a gapped comparison hanging on the
    # main clause as `advcl`, with `coltel` promoted and `le scaglie` its `orphan` remnant; there
    # is no elided verb to mint a tuple for, and unlike the `conj` case there is no coordination
    # head whose slots the remnants could fill a second time.
    orphan_heads = {
        (row.head_line, row.head_token)
        for row in all_rows
        if row.deprel == "orphan" and (row.head_line, row.head_token) in index
    }
    predicate_positions: set[tuple[int, int]] = set()
    for row in all_rows:
        if row.deprel not in CLAUSE_HEAD_DEPRELS:
            continue
        pos = (row.line, row.token)
        morph = morph_at(row.line, row.token)
        if (morph is not None and "conjunction" in morph.pos.lower()
                and not any(c.deprel in ARG_DEPRELS for c in children.get(pos, ()))):
            continue
        if pos in orphan_heads and (morph is None or not is_verb_pos(morph.pos)):
            continue
        predicate_positions.add(pos)

    def conj_resolves(row: DepRow, seen: set[tuple[int, int]]) -> bool:
        seen.add((row.line, row.token))
        head = index.get((row.head_line, row.head_token))
        if head is None:
            return False
        if (head.line, head.token) in predicate_positions or head.deprel in CLAUSE_HEAD_DEPRELS:
            return True
        if head.deprel == "conj" and (head.line, head.token) not in seen:
            return conj_resolves(head, seen)
        return False

    # Rule AN: a conjunct carrying an `orphan` child heads a *gapped* clause, not a predicate.
    # "però giri Fortuna la sua rota …, e 'l villan la sua marra" (inferno 15:96): UD promotes
    # `villan` to `conj` and hangs `marra` on it as `orphan`, precisely because the verb that
    # would govern them is elided. Promoting `villan` to a predicate invents one and then hands
    # it the coordination head's subject; the remnants are instead a second set of fillers for
    # the head's own slots, which is what the LLM lists.
    gapped_conjuncts = {
        (row.head_line, row.head_token)
        for row in all_rows
        if row.deprel == "orphan" and (row.head_line, row.head_token) in index
    }

    def promote_conjuncts(verbs_only: bool) -> None:
        for row in all_rows:
            pos = (row.line, row.token)
            if row.deprel != "conj" or pos in predicate_positions:
                continue
            if not conj_resolves(row, set()):
                continue
            # A coordinating conjunction is a function word, never a predicate: Layer 4 routinely
            # attaches a line-initial "E"/"Ed"/"Ma" to the previous clause head with deprel `conj`
            # ("E 'l mio buon duca, che già li er' al petto"), which this rule would otherwise
            # promote. Gapped/elided predicates of other POS stay promoted — those are real.
            conj_morph = morph_at(row.line, row.token)
            if conj_morph is not None and "conjunction" in conj_morph.pos.lower():
                continue
            if verbs_only and (conj_morph is None or not is_verb_pos(conj_morph.pos)
                               or not conj_morph.person):
                continue
            # Rule CA: rule BN's argument test, applied to the `conj` branch. A **non-verb**
            # conjunct with no argument child of its own is not an elided clause: "Sordel rimase
            # e **l'altre genti** forme" (purgatorio 9:58) and "sen venne suso; e **io** per le
            # sue orme" (9:60) promote a noun and a pronoun whose remnants Layer 4 left on the
            # coordination head, so the minted tuple is empty — or, worse, a lone pro-drop `subj`
            # ∅ asserting that the conjunct has a subject other than itself. The reading no
            # tuple can express is the one rules AN and BN already refuse elsewhere; a nominal
            # conjunct that *does* carry arguments ("Ed **elli**: «Vedi …»", inferno 11:15, whose
            # `ccomp` is the elided speech) is a real gapped clause and stays promoted.
            #
            # A `cop`/`aux` child is the tree's own assertion that the conjunct heads a
            # predication ("Tant' **è amara**", inferno 1:7, an adjective conjunct whose subject
            # is pro-drop), so the test is for arguments *or* a copula — the same both-readings
            # evidence rule Y reads on the acceptance side.
            if ((conj_morph is None or not is_verb_pos(conj_morph.pos))
                    and not any(c.deprel in ARG_DEPRELS or c.deprel in _AUX_DEPRELS
                                for c in children.get(pos, ()))):
                continue
            if pos in gapped_conjuncts:
                continue
            predicate_positions.add(pos)

    promote_conjuncts(verbs_only=False)

    # 2. argument-bearing non-auxiliary verbs.
    for row in all_rows:
        pos = (row.line, row.token)
        if pos in predicate_positions:
            continue
        morph = morph_at(row.line, row.token)
        if morph is None or not is_verb_pos(morph.pos) or row.deprel in _AUX_DEPRELS:
            continue
        if any(c.deprel in ARG_DEPRELS for c in children.get(pos, ())):
            predicate_positions.add(pos)

    # Rule BZ: the `conj` chain resolves against the predicate census, so it has to be walked
    # again once pass 2 has added to it. A conjunct is promoted when the chain it hangs on
    # resolves to a predicate, and a predicate reached only by pass 2 — a verb Layer 4 attached
    # with an argument deprel of its own, "com' io rimango sol, **se non restai**" (purgatorio
    # 4:45), where `rimango` is the `obj` of `rimira` and `restai` its `conj` — was not in
    # `predicate_positions` when the chain was first walked. The conjunct was therefore dropped,
    # and a finite verb whose only argument is a pro-drop subject (the one shape pass 2 cannot
    # rescue either, since it has no argument child to be found by) went underived while the LLM
    # proposed it. The 21-25 and 31-34 batches' ordering finding once more, between two passes of
    # the derivation's own predicate census rather than between two acceptance rules.
    #
    # This second walk is restricted to **finite verbs**, and the restriction is rule BN's own
    # test — would the promoted position carry a tuple at all? The first walk promotes a conjunct
    # of any POS, because a nominal conjoined to a clause head is a gapped clause of its own; but
    # a nominal conjoined to something pass 2 promoted is an ordinary coordinate *argument* of
    # that predicate ("addimandò **licenza** di combatter", paradiso 12:95, where `licenza` is the
    # object), and a non-finite conjunct with no argument child of its own ("del comperare e
    # **vender** dentro al templo", paradiso 18:122) yields an empty tuple no reading can fill —
    # the two shapes rules AN and BN stop elsewhere. A *finite* conjunct always has a subject,
    # overt or pro-drop, so its tuple is never empty.
    promote_conjuncts(verbs_only=True)

    def argument_children(pos: tuple[int, int]) -> list[DepRow]:
        """Rule AM: a predicate's own argument children, plus any stranded on its `cop`/`aux`.

        UD attaches a clause's arguments to its lexical predicate, not to the copula or auxiliary
        that carries the tense — but Layer 4 does not do so consistently: "'n la mente m'è fitta"
        (inferno 15:82) hangs both `la mente` and the dative `m'` on the copula `è`, leaving the
        adjective `fitta` with a bare subject. Reading only the predicate's own children then
        loses arguments the tree does record, and the LLM (which reads the line, not the tree) is
        flagged for naming them. Rule I already walks the same edge in the other direction, from
        an auxiliary up to its lexical head; this is that walk applied to the argument slots.
        """
        own = list(children.get(pos, ()))
        taken = {c.deprel for c in own}
        for aux in children.get(pos, ()):
            if aux.deprel not in _AUX_DEPRELS:
                continue
            for stranded in children.get((aux.line, aux.token), ()):
                if (stranded.deprel in ARG_DEPRELS and stranded.deprel not in _SUBJ_DEPRELS
                        and stranded.deprel not in taken):
                    own.append(stranded)
        return own

    def _oblique_role_of(child: DepRow) -> str:
        """`obl:<preposition lemma>` for a token carrying a `case` child, else plain `obl`."""
        case_children = sorted(
            (c for c in children.get((child.line, child.token), ()) if c.deprel == "case"),
            key=lambda c: c.token,
        )
        if case_children:
            prep_morph = morph_at(case_children[0].line, case_children[0].token)
            lemma = _prep_lemma(prep_morph) if prep_morph else ""
            if lemma:
                return f"obl:{_normalize_prep_lemma(lemma)}"
        return "obl"

    result: dict[int, list[SkelRow]] = {no: [] for no in nos}
    for line, token in predicate_positions:
        pred_row = index[(line, token)]
        pred_args: list[SkelRow] = []
        has_subj = False
        for child in argument_children((line, token)):
            if child.deprel in _SUBJ_DEPRELS:
                pred_args.append(SkelRow(line, token, pred_row.word, "subj", child.line, child.token))
                has_subj = True
            elif child.deprel in _DIRECT_ROLE_MAP:
                role = _DIRECT_ROLE_MAP[child.deprel]
                pred_args.append(SkelRow(line, token, pred_row.word, role, child.line, child.token))
            elif child.deprel in ("obl", "obl:agent"):
                role = _oblique_role_of(child)
                pred_args.append(SkelRow(line, token, pred_row.word, role, child.line, child.token))

        # 3. conj shared-subject propagation: inherit the nearest conj-ancestor's subject.
        # Rule AT: only a verb inherits. A *nominal* promoted to predicate is an elided clause of
        # its own — "Così 'l maestro; e io «Alcun compenso», dissi lui … Ed **elli**: «Vedi …»"
        # (inferno 11:13–15), where `elli` is `conj` of `dissi` and is the speaker of the elided
        # second verb of speech, not a second subject of `dissi`'s own. Handing it the head's
        # subject asserts that Dante said what Virgil says; leaving it pro-drop is what the
        # root-position twin of the same frame ("E io: «Maestro, …»", 11:67) already derives.
        own_is_verb = is_verb_pos((morph_at(line, token) or MorphRow("")).pos)
        if not has_subj and pred_row.deprel == "conj" and own_is_verb:
            seen = {(line, token)}
            cur = index.get((pred_row.head_line, pred_row.head_token))
            while cur is not None and (cur.line, cur.token) not in seen:
                seen.add((cur.line, cur.token))
                inherited = next(
                    (c for c in children.get((cur.line, cur.token), ()) if c.deprel in _SUBJ_DEPRELS),
                    None,
                )
                if inherited is not None:
                    pred_args.append(
                        SkelRow(line, token, pred_row.word, "subj", inherited.line, inherited.token)
                    )
                    has_subj = True
                    break
                if cur.deprel != "conj":
                    break
                cur = index.get((cur.head_line, cur.head_token))

        # 4. pro-drop: a finite predicate with still no subject gets an explicit ∅ row.
        if not has_subj:
            own_morph = morph_at(line, token)
            finite = bool(own_morph and own_morph.person)
            if not finite:
                for c in children.get((line, token), ()):
                    if c.deprel in _AUX_DEPRELS:
                        cm = morph_at(c.line, c.token)
                        if cm and cm.person:
                            finite = True
                            break
            if finite:
                pred_args.append(SkelRow(line, token, pred_row.word, "subj", 0, 0))

        # 5. rule AN: the remnants of a gapped conjunct fill this predicate's slots a second
        # time. A remnant carrying its own preposition claims the matching oblique slot ("'l
        # sole avëa il cerchio … lasciato al Tauro e la notte *a lo Scorpio*", purgatorio 25:3);
        # the rest take the remaining slots in the order the predicate's own arguments stand in
        # the line ("lei lo vedere, e me l'ovrare appaga", purgatorio 27:108, where the object
        # precedes the subject in both halves). Run after the subject steps so a gapped clause
        # whose head takes its subject by propagation still has a `subj` slot to fill.
        for conjunct in sorted(
            (c for c in children.get((line, token), ())
             if c.deprel == "conj" and (c.line, c.token) in gapped_conjuncts),
            key=lambda c: (c.line, c.token),
        ):
            # Rule CN: a slot the head clause fills with ∅ goes to the **back** of the queue.
            # The remnants of a gapped clause pair off against the head clause's arguments by
            # the order they stand in the line, and a pro-drop subject stands nowhere — but
            # ∅ = (0, 0) sorts before every real position, so that empty slot was taking the
            # *first* remnant of every gapped clause under a pro-drop predicate. "molti di vita
            # e **sé** di pregio priva" (purgatorio 14:63) was derived with `sé` as the subject
            # of `priva`, against two overt objects in the line and the `case` annex's
            # accusative. A ∅ slot is still offered — "tu … intende de la voglia assoluta, e
            # **io** de l'altra" (paradiso 4:113) is a genuine contrastive subject remnant under
            # a pro-drop head — but only once the overt slots are spoken for.
            slots: list[str] = []
            null_slots: list[str] = []
            for row_ in sorted(pred_args, key=_row_sort_key):
                if not row_.role:
                    continue
                bucket = (null_slots if (row_.arg_line, row_.arg_token) == (0, 0) else slots)
                if row_.role not in slots and row_.role not in null_slots:
                    bucket.append(row_.role)
            slots += null_slots
            remnants = [conjunct] + sorted(
                (c for c in children.get((conjunct.line, conjunct.token), ())
                 if c.deprel == "orphan"),
                key=lambda c: (c.line, c.token),
            )
            # A promoted conjunct that carries its own preposition is an oblique, so the subject
            # is shared with the head clause rather than gapped: "come il tempo tegna in cotal
            # testo le sue radici e *ne li altri* le fronde" (paradiso 27:118).
            if any(c.deprel == "case" for c in children.get((conjunct.line, conjunct.token), ())):
                slots = [s for s in slots if s != "subj"]
            assigned: list[tuple[str, DepRow]] = []
            for remnant in list(remnants):
                if not any(c.deprel == "case"
                           for c in children.get((remnant.line, remnant.token), ())):
                    continue
                label = _oblique_role_of(remnant)
                if label in slots:
                    slots.remove(label)
                    remnants.remove(remnant)
                    assigned.append((label, remnant))
            # Rule CZ: a remnant the `case` annex assigns a case to claims the slot that case
            # names, before the queue below hands out what is left. What the queue does is pair
            # remnants against slots in **role-rank** order — subject, then object, then the
            # obliques — which reads Dante as always putting the gapped clause's remnants in the
            # canonical order. He does not. "lei lo vedere, e me l'ovrare appaga"
            # (purgatorio 27:108) puts the object first in both halves, and the rank queue gave
            # `lei` the subject slot: *she* satisfies the seeing, the reverse of the line. The
            # annex reads `lei` as `accusative`, which settles it, and settles it without
            # assuming an order — "onde fa l'arco il Sole e Delia il cinto" (paradiso 29:78)
            # inverts the two halves chiastically, so pairing the remnants by where they stand
            # would get *that* line wrong, and there the annex holds no value for either proper
            # noun and the rank queue is left to decide, correctly. This is rule U's third
            # opinion moved to the one place in `derive_unit` that is openly guessing; unlike
            # rule U it runs in both directions, because here the annex is not overruling a
            # Layer-4 label — Layer 4 assigns a gapped remnant no role at all.
            for remnant in list(remnants):
                value = case_by_pos.get((remnant.line, remnant.token))
                if not value or SLOT_SEP in value:
                    continue
                claimed = [s for s in slots if s in ("subj", "obj", "iobj")
                           and _case_supports_role(value, s)]
                if len(claimed) == 1:
                    slots.remove(claimed[0])
                    remnants.remove(remnant)
                    assigned.append((claimed[0], remnant))
            assigned.extend(zip(slots, remnants))
            for role, remnant in assigned:
                pred_args.append(
                    SkelRow(line, token, pred_row.word, role, remnant.line, remnant.token)
                )

        if not pred_args:
            pred_args.append(SkelRow(line, token, pred_row.word, "", 0, 0))
        result.setdefault(line, []).extend(pred_args)

    for rows in result.values():
        rows.sort(key=_row_sort_key)
    return result


# --- Parsing / resolution -----------------------------------------------------------


def _alpha_tokens(text: str) -> list[str]:
    return [t for t in tokenize(text) if has_alpha(t)]


def _words_match(word: str, token: str) -> bool:
    return word == token or strip_word_punct(word, token) is not None


def _parse_int(value: str | None) -> int | None:
    if not value:
        return None
    digits = "".join(ch for ch in value if ch.isdigit())
    return int(digits) if digits else None


def resolve_chunk(
    nos: list[int], texts: list[str], table_text: str
) -> tuple[dict[int, list[SkelRow]], list[str]]:
    """Parse a skeleton table and resolve it into `SkelRow`s keyed by predicate line.

    Returns (rows-by-line, arg-word mismatch descriptions). Raises `ValueError` if no table
    can be parsed. Mirrors `dep.resolve_chunk`: `line`/`token`/`arg_line`/`arg_token` are
    authoritative citations; `word`/`arg_word` are cross-checked against the actual token
    (word here at `validate_unit` time; arg_word here at parse time, like `dep`'s head-word
    check) and reported as mismatches, never stored. A `role` cell of `-`/blank marks a
    zero-argument predicate row (`arg_line`/`arg_token` forced to `(0, 0)`).
    """
    table = read_table(table_text)
    if table is None:
        raise ValueError("no parseable skeleton table found")
    keys = [canon_header(h) for h in table[0]]
    token_lists = {no: _alpha_tokens(t) for no, t in zip(nos, texts)}

    result: dict[int, list[SkelRow]] = {no: [] for no in nos}
    mismatches: list[str] = []
    for raw in table[2:]:  # skip header + separator
        cells = dict(zip(keys, raw))
        line = _parse_int(cells.get("line"))
        token = _parse_int(cells.get("token"))
        word = (cells.get("word") or "").strip()
        if line is None or token is None or not word or line not in result:
            continue
        role_cell = (cells.get("role") or "").strip()
        role = "" if role_cell in ("-", "", "n/a", "N/A") else role_cell
        arg_line = _parse_int(cells.get("arg_line")) or 0
        arg_token = _parse_int(cells.get("arg_token")) or 0
        if role == "":
            arg_line = arg_token = 0
        arg_word = (cells.get("arg_word") or "").strip()

        result[line].append(SkelRow(line=line, token=token, word=word, role=role,
                                     arg_line=arg_line, arg_token=arg_token))

        if arg_line and arg_token:
            arg_tokens = token_lists.get(arg_line)
            if arg_tokens is not None and 1 <= arg_token <= len(arg_tokens):
                expected = arg_tokens[arg_token - 1]
                if arg_word and not _words_match(arg_word, expected):
                    mismatches.append(
                        f"{line}.{token} cites arg {arg_line}.{arg_token} as {arg_word!r}, "
                        f"actual {expected!r}"
                    )

    for rows in result.values():
        rows.sort(key=_row_sort_key)
    return result, mismatches


# --- Validation ----------------------------------------------------------------------


def _predicate_positions_in(rows_by_line: dict[int, list[SkelRow]]) -> set[tuple[int, int]]:
    return {
        (row.line, row.token)
        for rows in rows_by_line.values()
        for row in rows
        if row.token > 0
    }


def _subj_arg(by_arg_map: dict[tuple[int, int], str]) -> tuple[int, int] | None:
    return next((arg for arg, role in by_arg_map.items() if role == "subj"), None)


_CONTROL_CHAIN_LIMIT = 8


def _control_subject_candidates(
    pos: tuple[int, int], derived_by_pred: dict[tuple[int, int], list[SkelRow]],
    dep_index_by_pos: dict[tuple[int, int], DepRow],
    morph_rows: "dict[int, list[MorphRow]] | None" = None,
) -> tuple[set[tuple[int, int]], bool]:
    """Rule V: the subjects a **non-finite** predicate can inherit, walking its dep head chain.

    `derive_unit` only ever reads a predicate's own children, so a predicate with no `nsubj` of
    its own and no finite morphology gets no `subj` row at all — it is silent, not asserting
    that the predicate has no subject. Every such predicate does have one, and Italian fixes it
    structurally in exactly two ways this collects:

    - **Control / raising**: an `xcomp`/`ccomp`/`advcl`/`conj` chain of non-finite predicates
      takes its subject from an argument of the matrix predicate. Which argument is lexical
      (subject control "vuole partire", object control "fé molte genti viver grame", the
      causative's dative causee "ella mi fa tremar"), so all of `subj`/`obj`/`iobj` are
      candidates, at every link up to the first ancestor that has a subject of its own.
    - **Adnominal participle** (`acl`): the subject is the nominal the participle modifies —
      "le sue spalle *vestite* de' raggi", "io, *vinto* dal sonno", "prieghi *fatti* a Dio".

    Membership in this set is an acceptance, never an assertion: the derivation still says
    nothing, and a subject from outside the set stays flagged as a genuine disagreement.

    Returns `(candidates, unresolved)`. `unresolved` is true when the walk reaches a matrix
    predicate whose own subject derive_unit could only give as pro-drop ∅ ("chi ... *parea*
    fioco"): the controller is then a referent the derivation never resolved, so it cannot
    adjudicate the LLM's resolution of it either — exactly the case the pro-drop branch of
    `_apply_subj_authority` already treats as LLM-authoritative.
    """
    candidates: set[tuple[int, int]] = set()
    cur = dep_index_by_pos.get(pos)
    seen = {pos}
    for _ in range(_CONTROL_CHAIN_LIMIT):
        if cur is None:
            break
        head_pos = (cur.head_line, cur.head_token)
        if head_pos == (0, 0) or head_pos in seen:
            break
        seen.add(head_pos)
        if cur.deprel in ("acl", "acl:relcl"):
            candidates.add(head_pos)
            # Rule CE: the antecedent and the relative pronoun of its own relative clause are
            # one referent, so either of them names this participle's subject. "O superbi
            # cristian … **che**, de la vista de la mente **infermi**, fidanza avete"
            # (purgatorio 10:122): Layer 4 hangs both `infermi` and `avete` on `cristian` as
            # `acl:relcl`, and the LLM — reading a relative clause with a depictive inside it —
            # gives the depictive the clause's own subject, the relative `che`. Rule V's walk
            # reaches the antecedent and stops one edge short of the pronoun that stands for it.
            # This is the argument-identity route the Inferno 16-25 batches named and left
            # unopened; kept to the relative pronoun forms, so an ordinary nominal subject of
            # the relative clause (a different referent) stays flagged.
            candidates.update(
                (r.line, r.token)
                for r in dep_index_by_pos.values()
                if r.deprel in _SUBJ_DEPRELS
                and r.word.lower().rstrip("'") in ("che", "ch", "cui", "chi")
                and (rel := dep_index_by_pos.get((r.head_line, r.head_token))) is not None
                and rel.deprel == "acl:relcl"
                and (rel.head_line, rel.head_token) == head_pos
            )
        # Rule CF: the controller a fused clitic hides. "anzi ad aprir ch'a **tenerla** serrata"
        # (purgatorio 9:128): the object controlling `serrata` is the `la` inside `tenerla`, and
        # Layer 1 gives it no position of its own — the only citation for it is the host token,
        # which is what the LLM writes and what rules AL and AS already read as two roles on one
        # position. Rule V collects the matrix predicate's derived `obj`, but a clitic fused into
        # the verb never becomes one, so object control across this edge had no candidate at all.
        # Censused at 66 `xcomp` edges under a fused verb+pronoun host.
        if morph_rows is not None:
            head_line_rows = morph_rows.get(head_pos[0])
            if (head_line_rows and 1 <= head_pos[1] <= len(head_line_rows)
                    and "+pronoun" in head_line_rows[head_pos[1] - 1].pos):
                candidates.add(head_pos)
        head_rows = derived_by_pred.get(head_pos, ())
        # Rule CJ: the controller Layer 4 labelled `obl`. The three core roles were the whole
        # candidate set, but Italian's controller is often a dative or a genitive that this
        # corpus's Layer 4 writes as an oblique: "s'avacci **lor** divenir **sante**"
        # (purgatorio 6:27), where the possessor of the nominalized infinitive is the subject of
        # its predicate adjective; "**detto n'**avea **beati**" (22:5), object control whose
        # object is the `ne` clitic Layer 4 marks `obl`; "dandole biasmo" (inferno 7:93). The
        # role name is Layer 4's notation for the edge, not a claim that an oblique cannot
        # control — and this set is an *acceptance*, never an assertion, so widening it accepts
        # a reading the tree leaves open rather than asserting one.
        candidates.update(
            (row.arg_line, row.arg_token)
            for row in head_rows
            if (row.role in ("subj", "obj", "iobj") or row.role.startswith("obl"))
            and (row.arg_line, row.arg_token) != (0, 0)
        )
        head_subj = [row for row in head_rows if row.role == "subj"]
        if any((row.arg_line, row.arg_token) == (0, 0) for row in head_subj):
            return candidates, True
        if head_subj:
            break
        cur = dep_index_by_pos.get(head_pos)
    return candidates, False


def _inherited_subject(
    pos: tuple[int, int], dep_index_by_pos: dict[tuple[int, int], DepRow]
) -> bool:
    """Whether `derive_unit` could only have given `pos` a subject by conj propagation (step 3):
    the predicate is a `conj` and has no subject child of its own."""
    row = dep_index_by_pos.get(pos)
    if row is None or row.deprel != "conj":
        return False
    return not any(
        r.deprel in _SUBJ_DEPRELS and (r.head_line, r.head_token) == pos
        for r in dep_index_by_pos.values()
    )


def _finite_head_of(
    pos: tuple[int, int], children_by_pos: "dict[tuple[int, int], list[DepRow]]",
    morph_rows: dict[int, list[MorphRow]],
) -> tuple[int, int]:
    """The token that actually carries `pos`'s person/number: itself, or — for a non-finite
    predicate like `vedere` in "là i **potrai** vedere" — its `aux`/`cop` child. Mirrors the
    finiteness test `derive_unit`'s step 4 (pro-drop) already runs, so subject-agreement checks
    on a periphrastic predicate look at the token Layer 2 actually marked person/tense on."""
    own_morph = None
    line_rows = morph_rows.get(pos[0])
    if line_rows and 1 <= pos[1] <= len(line_rows):
        own_morph = line_rows[pos[1] - 1]
    if own_morph and own_morph.person:
        return pos
    for child in children_by_pos.get(pos, ()):
        if child.deprel in _AUX_DEPRELS:
            child_line_rows = morph_rows.get(child.line)
            if child_line_rows and 1 <= child.token <= len(child_line_rows):
                child_morph = child_line_rows[child.token - 1]
                if child_morph and child_morph.person:
                    return (child.line, child.token)
    return pos


def _accept_control_subjects(
    g: dict[tuple[int, int], str], pos: tuple[int, int],
    derived_by_pred: dict[tuple[int, int], list[SkelRow]],
    dep_index_by_pos: dict[tuple[int, int], DepRow],
    morph_rows: dict[int, list[MorphRow]] | None,
    np_spans_by_line: "dict[int, list[NPSpan]] | None" = None,
) -> None:
    """Rule V's acceptance, applied to every `subj` citation `g` holds for `pos`.

    Used where the derivation asserts **no** subject for a predicate: either because it is
    non-finite (rule V's own case) or because rule AG has just dropped an inherited subject that
    contradicts it (rule CL). Each citation is validated against the control/raising candidate
    set rather than accepted outright, and rule BB's plural: a slot rule V accepts it accepts for
    every citation that fills it.
    """
    g_subjs = [a for a, role in g.items() if role == "subj"]
    if not g_subjs:
        return
    reachable, unresolved = _control_subject_candidates(pos, derived_by_pred,
                                                        dep_index_by_pos, morph_rows)
    candidates = None if unresolved else {(0, 0)} | reachable
    for g_subj in g_subjs:
        # …and the citation is tested through rule C's normalization too, since the collapse
        # runs after this and would otherwise rewrite an unaccepted conjunct/`flat` member
        # onto the very position rule V does accept ("Bellincion **Berti** vid' io andar",
        # paradiso 15:112, where the matrix object is cited by the name's second word).
        # Rule DF: …and through rule AI's normalization too, for the same reason. Rule V's
        # candidates are Layer 4's attachment points; the LLM is told to cite a noun phrase by
        # its Layer-3 head, and the two do not always land on the same token of one phrase —
        # "l'altre tre si fero avanti, **danzando**" (purgatorio 31:132), where Layer 4 makes
        # `altre` the subject of `fero` and Layer 3 heads `[l'altre tre]` on `tre`. Rule AI
        # already reads that pair as one argument named twice, but it runs downstream of this
        # and only pairs citations of a role the derivation *has* — which for a gerund's
        # inherited subject is exactly the role it does not. The ordering finding again, in the
        # form the Purgatorio 6-10 batch named: ask which normalization has already run on the
        # citation a gate compares.
        if (candidates is None or g_subj in candidates
                or _coordination_head(g_subj, dep_index_by_pos) in candidates
                or (np_spans_by_line is not None
                    and any(_np_head_equivalent(g_subj, c, np_spans_by_line)
                            for c in candidates))):
            g.pop(g_subj, None)


def _apply_subj_authority(
    g: dict[tuple[int, int], str], d: dict[tuple[int, int], str],
    pos: tuple[int, int], derived_by_pred: dict[tuple[int, int], list[SkelRow]],
    dep_index_by_pos: dict[tuple[int, int], DepRow],
    given_by_pred: "dict[tuple[int, int], list[SkelRow]] | None" = None,
    morph_rows: dict[int, list[MorphRow]] | None = None,
    children_by_pos: "dict[tuple[int, int], list[DepRow]] | None" = None,
    np_spans_by_line: "dict[int, list[NPSpan]] | None" = None,
) -> None:
    """Mutate `g`/`d` in place: drop the subj arg where PLAN.md's authority model makes the slot
    LLM-authoritative (validated against a candidate set) rather than derive-authoritative (exact
    match, the default `by_arg` diff already handles).
    """
    d_subj = _subj_arg(d)
    # Rule CU: the LLM filled the subject slot **twice**, once with pro-drop ∅ and once with the
    # very token the derivation supplies — "e perché tanti secoli **giaciuto** / qui se'"
    # (purgatorio 21:80, ∅ beside the `chi` of the previous line), "tanto **ovra** poi"
    # (25:55, ∅ beside `Anima`), "**muovono** … li ordini" (paradiso 1:112). Two subjects for one
    # predicate is not two claims about the slot: it is the reading not deciding, which is rule
    # BA's principle read from the LLM's end — there the *derivation* offered two and was made to
    # require neither. Only the ∅ half is dropped, and only when the other half is exactly the
    # derived subject: a concrete subject the derivation contradicts is a claim, and stays
    # flagged. Censused at 6 predicates corpus-wide that list a ∅ beside another subject, 4 of
    # them beside the derived one.
    if d_subj not in (None, (0, 0)) and g.get((0, 0)) == "subj" and g.get(d_subj) == "subj":
        g.pop((0, 0), None)
    if d_subj == (0, 0):
        # Pro-drop antecedent: derive_unit only knows ∅; any concrete subject the LLM resolves is
        # strictly more informative, not wrong.
        g_subj = _subj_arg(g)
        if g_subj is not None:
            g.pop(g_subj, None)
        d.pop((0, 0), None)
    elif d_subj is None:
        # derive_unit asserted no subject at all: the predicate is non-finite, so ∅ is accepted
        # and so is any subject rule V's head-chain walk can reach (control/raising matrix
        # argument, or the nominal an adnominal participle modifies).
        # Rule BB, rule V's coordination leg: the LLM lists **every** conjunct of a coordinate
        # subject ("vidi cavalier muover ... né pedoni ... né nave", inferno 22:11 — three `subj`
        # rows on the one infinitive), and taking only the first one out left the rest to be
        # collapsed by rule C back onto the very citation just accepted, and reported there. A
        # slot rule V accepts it accepts for all of the citations that fill it.
        _accept_control_subjects(g, pos, derived_by_pred, dep_index_by_pos, morph_rows,
                                 np_spans_by_line)
    elif (morph_rows is not None and children_by_pos is not None
          and _inherited_subject(pos, dep_index_by_pos)
          and _subj_arg(g) != d_subj
          and subject_agreement(d_subj, _finite_head_of(pos, children_by_pos, morph_rows),
                                morph_rows, children_by_pos)[0] == "disagree"):
        # Rule AG: derive_unit's conj-subject-propagation (step 3) walks the conj chain
        # unconditionally, with no agreement gate — so it can inherit a subject whose Layer-2
        # person/number actively contradicts this predicate's own. "come tu vedi, a la pioggia
        # mi fiacco" (inferno 6:54): `fiacco` (1sg) is attached `conj` to `chiamaste` (2pl, three
        # lines up) with no subject of its own, and step 3 blindly inherits "Voi". Measured over
        # the whole corpus: of 1370 conj-inherited-subject candidates, 682 agree and 461 are
        # undecidable (left untouched, same as Stage 1's `null_subject` gate treats them) but
        # **227 actively disagree** — an inherited subject in that set is not a candidate to
        # require, so it is dropped rather than asserted.
        d.pop(d_subj, None)
        # Rule AH, AG's second leg: dropping the inherited subject makes the derivation *silent*
        # about this predicate's subject, which is exactly the state branch 2 above already treats
        # as LLM-authoritative for ∅. Leaving the LLM's ∅ standing turned one divergence into an
        # `extra_arg` the derivation had just disclaimed any opinion on — "e ora attendi qui"
        # (inferno 10:129), a 2sg imperative conj-attached to `conservi`, whose 3sg subject "La
        # mente tua" AG drops; the LLM's ∅ was then reported as a spurious extra argument. Only ∅
        # is dropped: a conjunct where the LLM resolved a *concrete* subject is making its own
        # claim about a slot the derivation no longer fills, and stays flagged.
        if _subj_arg(g) == (0, 0):
            g.pop((0, 0), None)
        else:
            # Rule CL, AG's third leg. Dropping the inherited subject leaves the derivation in
            # exactly the state branch 2 describes — asserting no subject at all — so the slot
            # is LLM-authoritative on the same terms, validated against the same candidate set
            # rather than accepted outright. "Io veggio tuo nepote che diventa / cacciator …
            # e tutti li sgomenta" (purgatorio 14:60): AG drops the 1sg "Io" that step 3
            # inherited onto the 3sg `sgomenta`, and the LLM's own reading of the subject was
            # then reported as `extra_arg` against a slot the derivation had just disclaimed.
            _accept_control_subjects(g, pos, derived_by_pred, dep_index_by_pos, morph_rows,
                                 np_spans_by_line)
    elif given_by_pred is not None and _inherited_subject(pos, dep_index_by_pos):
        # Rule AC: an inherited subject is not an independent assertion about *this* predicate.
        # `derive_unit`'s step 3 copies the coordination head's subject onto a conjunct that has
        # none of its own, and the LLM copies its own reading of the head the same way, so a
        # disagreement here is the head's disagreement restated once per conjunct — "Questa
        # chiese Lucia ... e disse" (inferno 2:97-98), where rules U and W already settled the
        # subj/obj inversion at `chiese` and `disse` reported it a second time. Gated on the
        # given subject being *literally* the one the LLM gave the head: a conjunct where the
        # LLM resolved a different subject is making its own claim and stays flagged.
        g_subj = _subj_arg(g)
        if g_subj is None or g_subj == d_subj:
            return
        head = _coordination_head(pos, dep_index_by_pos)
        head_given = next(
            ((r.arg_line, r.arg_token) for r in given_by_pred.get(head, ()) if r.role == "subj"),
            None,
        )
        if head_given == g_subj:
            g.pop(g_subj, None)
            d.pop(d_subj, None)
            return
        # Rule BU: the subject a coordination supplies from its **last** conjunct. "per fuggir
        # lui **lasciò** qui loco vòto / **quella ch'appar di qua**, e sù ricorse"
        # (inferno 34:125): `lasciò` has no subject of its own, so step 3 walks the conj chain up
        # and inherits one from three predicates away, while the overt `nsubj` Layer 4 records is
        # on `ricorse`, the conjunct *below* it. Italian postposes a shared subject freely, and a
        # conjunct's own `nsubj` is a stronger candidate for the coordination than anything the
        # chain-walk finds above it — rule AT's direction reversed for the one case where the
        # derivation has no subject of its own to defend. Gated on the derived subject being
        # inherited (this branch's own condition), so a predicate with an `nsubj` child of its own
        # is untouched, and on the LLM having cited exactly that conjunct's subject. Censused at
        # 74 coordination heads whose conjunct carries the only overt subject.
        if children_by_pos is not None and g_subj is not None:
            for child in children_by_pos.get(pos, ()):
                if child.deprel != "conj":
                    continue
                conjunct = (child.line, child.token)
                if any(k.deprel in _SUBJ_DEPRELS and (k.line, k.token) == g_subj
                       for k in children_by_pos.get(conjunct, ())):
                    g.pop(g_subj, None)
                    d.pop(d_subj, None)
                    return


_ELIDED_COPULA_DEPRELS = frozenset({"conj", "appos", "attr"})

# Rule AY: the children that make an `amod` adjective an adjective *phrase* — one governing an
# argument of its own — rather than a bare attributive.
_ADJECTIVE_COMPLEMENT_DEPRELS = frozenset(
    {"obl", "obl:agent", "nmod", "obj", "iobj", "ccomp", "xcomp", "advcl", "nsubj"}
)

# Rule Z: the deprels that put a token in an argument or adjunct *slot* rather than at a clause
# head. A verb form sitting in one of these is a predicate no reading disputes — the derivation
# is silent about it only because `derive_unit`'s rule 1 keys on `CLAUSE_HEAD_DEPRELS` and its
# rule 2 needs the verb to carry an argument child of its own.
_NOMINAL_SLOT_DEPRELS = frozenset({"obl", "obl:agent", "nmod", "nsubj", "nsubj:pass", "obj",
                                   "iobj", "advmod"})

# --- Divergence-check normalization (Phase 5, PLAN.md) --------------------------------
#
# Two further equivalences of the same shape as the Phase 1 ones above — notation conventions,
# not parse disagreements. Measured over all 100 cantos before being frozen (PLAN.md Phase 5a).

_CONJ_WALK_LIMIT = 8


def _coordination_head(
    pos: tuple[int, int], dep_index_by_pos: dict[tuple[int, int], DepRow],
    morph_pos_by_position: "dict[tuple[int, int], str] | None" = None,
) -> tuple[int, int]:
    """Rule C: the head of `pos`'s coordination, walking `conj` edges up (bounded).

    Rule AP walks `appos` with them. An apposition is the same argument named a second time —
    "onde omicide e ciascun che mal fiere, guastatori e predon, **tutti** tormenta lo giron
    primo" (inferno 11:38), where `tutti` sums up the coordination it is appositive to. Layer 4
    records the second naming as `appos` off the first, exactly as it records a conjunct as
    `conj`, and neither is a second argument of the verb; the LLM cites whichever of the two
    reads as the argument. Collapsing them together is the same notation normalization rule C
    already makes for coordination, and it preserves roles, so a genuine role disagreement on
    the merged position still surfaces.

    Rule BE walks `flat` with them, on the same reasoning one relation further in: a multiword
    name is one nominal spread over several tokens ("son Vanni Fucci", inferno 24:125, where the
    LLM gives the predicate an `attr` on each half and the tree only ever attaches the first).
    `flat` is UD's *headless* multiword relation, so its members are not modifiers of the opening
    word — they are the same nominal, and citing any of them cites it.

    **Rule CD** stops the walk where the coordination stops being one of arguments. UD promotes a
    conjunct to the *clause* head when it reads the coordination as clausal, so a `conj` step
    from a nominal onto a verb leaves the argument's own coordination and enters the predicates':
    "sen venne suso; e **io** per le sue orme" (purgatorio 9:60) walks `io` → `venne` → `tolse` →
    `rimase` and rewrites a subject citation into a citation of a predicate three lines up, which
    no reading of the line asserts. Rule CC accepts such a conjunct in the slot the LLM gives it,
    and can only see it if the collapse has left it alone.
    """
    seen = {pos}
    cur = pos
    for _ in range(_CONJ_WALK_LIMIT):
        row = dep_index_by_pos.get(cur)
        if row is None or row.deprel not in ("conj", "appos", "flat"):
            break
        head = (row.head_line, row.head_token)
        if head in seen or head not in dep_index_by_pos:
            break
        if row.deprel == "conj" and morph_pos_by_position is not None:
            head_row = dep_index_by_pos[head]
            cur_pos, head_pos = morph_pos_by_position.get(cur, ""), morph_pos_by_position.get(head, "")
            if (cur_pos and head_pos and not is_verb_pos(cur_pos) and is_verb_pos(head_pos)
                    and head_row.deprel not in ARG_DEPRELS):
                break
        seen.add(head)
        cur = head
    return cur


def _collapse_coordination(
    by_arg: dict[tuple[int, int], str], pos: tuple[int, int],
    dep_index_by_pos: dict[tuple[int, int], DepRow],
    morph_pos_by_position: "dict[tuple[int, int], str] | None" = None,
) -> dict[tuple[int, int], str]:
    """Rule C: map every argument citation onto its coordination head, de-duplicating.

    "si ciberà di terra e di sapïenza" — the LLM lists both conjuncts as `obj`, `derive_unit`
    reads only the predicate's direct children and so sees the first only. Enumerating conjuncts
    on the derived side instead was measured net-zero (PLAN.md Rule A): the LLM's own enumeration
    is inconsistent, so the divergence is a notation mismatch and normalization is the
    instrument. Roles are preserved, so a genuine role disagreement still surfaces.

    **Rule DE** decides *whose* role survives when the head is cited too. Coordination in this
    corpus is not always of like with like: a conjunct carries its own `case` marker as readily as
    it shares the head's, and 98 `conj` nominals corpus-wide have one whose lemma differs — "la
    flagellò **dal capo** infin **le piante**" (purgatorio 32:156), where Layer 4 hangs `piante`
    off `capo` as a `conj` with `infin` as its own `case`. The LLM names both, correctly, with
    two different prepositions; the collapse then had to pick one by role rank and picked the
    conjunct's, so the position the derivation reports with the *head's* preposition came back a
    `role_mismatch`. The head's own citation is the one that names the head, and a conjunct's role
    is only riding along on it — so a collapsed role never displaces an uncollapsed one. Rank
    still decides between two collapsed conjuncts, which is the case rule C was written for.

    The gate is the conjunct's **own** `case` marker, not the collapse alone: without it the rule
    also fires on an apposition whose head is the emptier of the two words ("che **l'uno** a
    l'altro raggio non ingombra", purgatorio 3:30, where the LLM's role for the `appos` is the
    right one), and rank is the better answer there.
    """
    out: dict[tuple[int, int], str] = {}
    from_head: dict[tuple[int, int], bool] = {}
    for arg, role in by_arg.items():
        key = arg
        if arg != (0, 0):
            head = _coordination_head(arg, dep_index_by_pos, morph_pos_by_position)
            if head != pos:  # never collapse an argument onto its own predicate
                key = head
        uncollapsed = key == arg
        if key not in out:
            out[key], from_head[key] = role, uncollapsed
            continue
        separately_marked = _distinctly_marked_conjunct(arg, key, dep_index_by_pos)
        if uncollapsed and not from_head[key] and separately_marked:
            out[key], from_head[key] = role, True  # rule DE: the head names its own role
        elif (uncollapsed == from_head[key] or not separately_marked) and (
                (_role_rank(role), role) < (_role_rank(out[key]), out[key])):
            out[key] = role  # rule C's rank tie-break, between citations of one provenance
    return out


def _distinctly_marked_conjunct(
    arg: tuple[int, int], head: tuple[int, int],
    dep_index_by_pos: dict[tuple[int, int], DepRow],
) -> bool:
    """Rule DE's gate: `arg` collapses onto `head` but carries a `case` marker of its own whose
    word differs from the head's, so the two are separately-marked obliques rather than one
    phrase named twice. Censused at 98 `conj` nominals corpus-wide."""
    if arg == head or arg == (0, 0):
        return False

    def marker(p: tuple[int, int]) -> str | None:
        for r in dep_index_by_pos.values():
            if r.deprel == "case" and (r.head_line, r.head_token) == p:
                return r.word.lower().rstrip("'")
        return None

    own = marker(arg)
    return own is not None and own != marker(head)


def _conj_shared_argument(
    pos: tuple[int, int], arg: tuple[int, int], grole: str,
    dep_index_by_pos: dict[tuple[int, int], DepRow],
    derived_by_pred: dict[tuple[int, int], list[SkelRow]],
    d: dict[tuple[int, int], str],
) -> bool:
    """Rule AJ: an argument gapped from the coordination head onto this conjunct.

    `derive_unit`'s step 3 propagates a shared **subject** across a coordination and nothing else,
    but Italian gaps objects and datives just as freely — "li rami *schianta*, *abbatte* e *porta*
    fori" (inferno 9:70), "m'hai sicurtà *renduta* e *tratto* d'alto periglio" (8:98), "lo spirito
    lasso *conforta* e *ciba*" (8:107). The LLM restates the shared argument under each conjunct,
    which is the correct reading; the derivation, reading only each predicate's own children,
    sees it once and reports the restatements as extra arguments.

    Accepted whatever role the conjunct assigns it: gapping genuinely changes the role, as in
    "ha *tolto* loro, e *posti* a questa zuffa" (7:59), where `loro` is the head's `iobj` and the
    conjunct's `obj`. The gate that keeps this from absorbing real disagreements is on the *slot*,
    not the role — the conjunct must have no derived filler of that role of its own. `subj` is
    excluded throughout: step 3 and the authority model (rules AC, AG, AH) already own it.
    """
    if grole == "subj" or arg == (0, 0) or grole in d.values():
        return False
    # The whole coordination cluster, not only the chain above this conjunct. Italian gaps in
    # both directions: "biscazza e *fonde* la sua facultade" (inferno 11:44) hangs the object on
    # the *second* conjunct and shares it back to the first, and "col cor *negando* e
    # bestemmiando quella" (11:47) hangs it on the conjunct and shares it up to the head. Both
    # are siblings or ancestors of `pos` in the same `conj` tree, so the cluster is the set of
    # positions reachable from `pos` by `conj` edges in either direction.
    cluster: set[tuple[int, int]] = set()
    frontier = [pos]
    while frontier and len(cluster) < _CONJ_WALK_LIMIT * 2:
        cur = frontier.pop()
        if cur in cluster:
            continue
        cluster.add(cur)
        row = dep_index_by_pos.get(cur)
        if row is not None and row.deprel == "conj":
            head = (row.head_line, row.head_token)
            if head in dep_index_by_pos:
                frontier.append(head)
        for other in dep_index_by_pos.values():
            if other.deprel == "conj" and (other.head_line, other.head_token) == cur:
                frontier.append((other.line, other.token))
    cluster.discard(pos)
    return any(
        (r.arg_line, r.arg_token) == arg and r.role not in ("", "subj")
        for member in cluster
        for r in derived_by_pred.get(member, ())
    )


def _np_head_equivalent(
    a: tuple[int, int], b: tuple[int, int], np_spans_by_line: dict[int, list[NPSpan]]
) -> bool:
    """Rule AI: whether two argument citations are the same Layer-3 noun phrase named twice.

    Layer 3's `head` and Layer 4's attachment point are computed independently and do not always
    land on the same token of one NP. `SYSTEM_PROMPT` tells the model to "prefer a noun phrase's
    head token", so the LLM cites Layer 3's head and `derive_unit` cites whatever Layer 4 hung the
    argument edge on — "Qui con **più di mille** giaccio" (inferno 10:118), where the NP
    `[più di mille]` has `head=più` and Layer 4 attaches `mille`. One argument then costs two
    violations, a `missing_arg` and an `extra_arg`, without either side having read the line
    differently.

    True only when both positions lie inside a single NP span **and** one of them is that span's
    head: two tokens that merely share a line, or two nominals inside one span neither of which is
    its head, are not each other's alternative name.
    """
    if a == (0, 0) or b == (0, 0) or a == b or a[0] != b[0]:
        return False
    for span in np_spans_by_line.get(a[0], ()):
        if span.start <= a[1] <= span.end and span.start <= b[1] <= span.end:
            if span.head in (a[1], b[1]):
                return True
    return False


def _merge_auxiliary_citations(
    by_arg: dict[tuple[int, int], str], pos: tuple[int, int],
    dep_index_by_pos: dict[tuple[int, int], DepRow],
) -> dict[tuple[int, int], str]:
    """Rule AQ: map an argument citation landing on an `aux`/`cop` onto its lexical head.

    "credendo ch'altro ne **volesse** dire" (inferno 13:110): the complement clause is headed by
    `dire`, and `volesse` is its `aux`; the LLM cites the finite word it can see carrying the
    tense, the derivation cites the lexical verb Layer 4 made the head. The two name one clause.
    Rule I already treats the same edge as identity when the *predicate* of a tuple lands on an
    auxiliary; this is that identity applied to the argument slot, and roles are preserved so a
    genuine role disagreement on the merged position still surfaces.
    """
    out: dict[tuple[int, int], str] = {}
    for arg, role in by_arg.items():
        key = arg
        if arg != (0, 0):
            row = dep_index_by_pos.get(arg)
            if row is not None and row.deprel in _AUX_DEPRELS:
                head = _aux_head(arg, dep_index_by_pos)
                if head != pos and head != arg:
                    key = head
        prev = out.get(key)
        if prev is None or (_role_rank(role), role) < (_role_rank(prev), prev):
            out[key] = role
    return out


def _nested_in_named_phrase(
    arg: tuple[int, int], g: dict[tuple[int, int], str], d: dict[tuple[int, int], str],
    np_spans_by_line: "dict[int, list[NPSpan]] | None",
) -> bool:
    """Rule BR: a derived argument buried inside a Layer-3 noun phrase whose head is another
    derived argument of the same predicate, and the LLM named that head.

    Rule AI merges two citations of one noun phrase when the **role** matches; this is the case
    where it does not. "**Gualandi con Sismondi e con Lanfranchi** s'avea messi dinanzi"
    (inferno 33:33): Layer 3 reads the whole comitative chain as one subject phrase headed by
    `Gualandi`, Layer 4 hangs `Sismondi` off the participle as a second `obl:con`, and the LLM —
    naming the phrase once, by its head — is reported as having omitted an oblique. The same shape
    covers a relative pronoun sitting inside its own antecedent's span (paradiso 12:27) and a
    modifier Layer 4 gave an argument deprel of its own (purgatorio 15:15).

    Two gates keep it from swallowing genuine omissions: the outer position must be a **derived**
    argument too, so the phrase is one Layer 4 already asserts twice rather than an over-inclusive
    Layer-3 span, and it must be one the LLM **cited**, so the phrase is on the record once. The
    structural pattern (two sibling arguments inside one NP span, one of them the head) is
    censused at 404; only 8 of those are positions where the LLM named exactly the head.
    """
    if np_spans_by_line is None or arg == (0, 0):
        return False
    for span in np_spans_by_line.get(arg[0], ()):
        if not (span.start <= arg[1] <= span.end) or span.head == arg[1]:
            continue
        outer = (arg[0], span.head)
        if outer in d and outer in g:
            return True
    return False


def _merge_np_head_citations(
    g: dict[tuple[int, int], str], d: dict[tuple[int, int], str],
    np_spans_by_line: dict[int, list[NPSpan]],
) -> None:
    """Rule AI: re-key a given citation onto the derived one when `_np_head_equivalent` says the
    two name one NP in the same role. Mutates `g` in place.

    Only unmatched positions on both sides pair up, and each is consumed once, so this can never
    silence a role disagreement or absorb a second, genuinely different argument.
    """
    roles = {role for arg, role in d.items() if arg not in g}
    for role in sorted(roles):
        unmatched_d = sorted(a for a, r in d.items() if r == role and a not in g)
        unmatched_g = sorted(a for a, r in g.items() if r == role and a not in d)
        for a_d in unmatched_d:
            match = next((a for a in unmatched_g if _np_head_equivalent(a, a_d, np_spans_by_line)),
                         None)
            if match is None:
                continue
            unmatched_g.remove(match)
            del g[match]
            g[a_d] = role


def _adverb_cluster_head(
    arg: tuple[int, int],
    dep_index_by_pos: dict[tuple[int, int], DepRow] | None,
    children_by_pos: dict[tuple[int, int], list[DepRow]] | None,
    morph_pos_by_position: dict[tuple[int, int], str] | None,
) -> tuple[int, int] | None:
    """The head of the adverb-preposition cluster `arg` belongs to, or None — see rule BJ.

    The cluster is an adverb Layer 4 put in an adjunct slot (`obl`/`obl:<lemma>`/`advmod`) with
    the phrase's nominal hanging under it by its own preposition ("fuor **del dritto amore**",
    "innanzi **a li altri**"), or a second adverb inside the same complex form ("da **qui**
    innanzi"). Local to the cluster: the caller decides what the head has to attach to.
    """
    if dep_index_by_pos is None or children_by_pos is None or morph_pos_by_position is None:
        return None
    row = dep_index_by_pos.get(arg)
    if row is None:
        return None
    head = (row.head_line, row.head_token)
    host = dep_index_by_pos.get(head)
    if host is None:
        return None
    if host.deprel not in ("advmod", "obl") and not OBL_RE.fullmatch(host.deprel):
        return None
    if "adverb" not in morph_pos_by_position.get(head, "").lower():
        return None
    if row.deprel in ("nmod", "obl") or OBL_RE.fullmatch(row.deprel):
        kids = children_by_pos.get(arg, ())
        if any(k.deprel == "case" for k in kids):
            return head
        # Rule BQ, rule BJ's other two orders. The cluster does not always put the preposition on
        # the nominal: "dinanzi **l'altro** e dietro **il braccio destro**" (inferno 31:87) has no
        # preposition at all, and "'n su **lo scoperto**" (31:89) carries it on the *adverb*, so
        # the nominal hangs bare and rule BJ's own-preposition gate never sees it. A nominal whose
        # only licence is an `obl`/`nmod` edge under an adjunct adverb is part of that adverb's
        # phrase however the preposition is distributed. Censused at 11 bare cases against rule
        # BJ's 150; the `mark` exclusion is what keeps the second term of a comparison out, where
        # the marker — not the adverb — is what opens the phrase ("vie più là **che 'l punir**",
        # paradiso 17:99), and rules BK/BL own that shape.
        if not any(k.deprel == "mark" for k in kids):
            return head
    if row.deprel == "advmod" and "adverb" in morph_pos_by_position.get(arg, "").lower():
        return head
    return None


def _merge_adverb_cluster_citations(
    g: dict[tuple[int, int], str], pos: tuple[int, int],
    dep_index_by_pos: dict[tuple[int, int], DepRow],
    children_by_pos: dict[tuple[int, int], list[DepRow]] | None,
    morph_pos_by_position: dict[tuple[int, int], str] | None,
) -> dict[tuple[int, int], str]:
    """Rule BJ: the adverb-preposition cluster names one oblique, from either of its two words.

    "**fuor** del dritto amore" (inferno 30:39), "**innanzi** a li altri" (28:68), "da **qui
    innanzi**" (29:23): Italian builds complex prepositions out of an adverb plus a simple
    preposition, and the Layer-4 prep-stack normalization of 2026-08-14 deliberately left the 40
    clusters whose opening word Layer 2 calls an *adverb* alone, because that is a Layer-2/4
    tension and not a Layer-4 shape lottery. Layer 4 therefore hangs the adverb on the predicate
    and the nominal under the adverb, so `derive_unit` reports the **adverb** as the oblique
    (30:38) — or, when the adverb sits in an `advmod` slot, reports nothing at all (28:68) —
    while the LLM names the nominal, which is what carries the meaning.

    Both citations name one adjunct, so the merge is onto the cluster head, exactly as rule AQ
    merges an auxiliary citation onto its lexical head: the role is carried across unchanged, so
    a genuine role disagreement on the merged position still surfaces, and rule J then accepts
    the `advmod` half. Gated on Layer 2 calling the head an adverb and on the moved token being
    the adverb's own `nmod`/`obl` child with a preposition of its own, or a further adverb inside
    the same cluster ("da qui innanzi"). Censused at 147 clusters corpus-wide.
    """
    if children_by_pos is None or morph_pos_by_position is None:
        return g

    def cluster_head(arg: tuple[int, int]) -> tuple[int, int]:
        head = _adverb_cluster_head(arg, dep_index_by_pos, children_by_pos, morph_pos_by_position)
        if head is None or head == pos:
            return arg
        host = dep_index_by_pos[head]
        return head if (host.head_line, host.head_token) == pos else arg

    out: dict[tuple[int, int], str] = {}
    for arg, role in g.items():
        key = arg
        if arg != (0, 0) and (role == "obl" or OBL_RE.fullmatch(role)):
            key = cluster_head(arg)
        prev = out.get(key)
        if prev is None or (_role_rank(role), role) < (_role_rank(prev), prev):
            out[key] = role
    return out


def _aux_head(
    pos: tuple[int, int], dep_index_by_pos: dict[tuple[int, int], DepRow]
) -> tuple[int, int]:
    """Rule I: the lexical head an `aux`/`aux:pass`/`cop` token attaches to (bounded walk)."""
    seen = {pos}
    cur = pos
    for _ in range(_CONJ_WALK_LIMIT):
        row = dep_index_by_pos.get(cur)
        if row is None or row.deprel not in _AUX_DEPRELS:
            break
        head = (row.head_line, row.head_token)
        if head in seen or head not in dep_index_by_pos:
            break
        seen.add(head)
        cur = head
    return cur


def _prep_stack_nominal(
    arg: tuple[int, int], dep_index_by_pos: dict[tuple[int, int], DepRow]
) -> tuple[int, int]:
    """Rule BV: the nominal a multiword preposition's own words belong to (bounded walk).

    The 2026-08-14 Layer-4 normalization writes a stacked preposition as opening word `case` ->
    nominal, later members `fixed` -> opening word, and `dante_corpus.skel`'s lemma aggregation
    already reads that shape when it names the oblique's preposition. What it did not cover is the
    LLM *citing* one of those words as the argument: "Usa **con esso** donno Michel Zanche"
    (inferno 22:88), where the reinforced `con esso` was normalized the same way and the LLM names
    `esso`. A preposition's own words are not arguments, so the citation is the nominal they open —
    the same merge rules AQ (auxiliary) and BJ (adverb cluster) make onto their phrase's head.

    Entered only from a `fixed` member, so a plain `case` preposition standing on its own — which
    the LLM cites for other reasons, and which rules L/N/O already read — is untouched.
    """
    if (dep_index_by_pos.get(arg) or DepRow(0, 0, "", "", 0, 0)).deprel != "fixed":
        return arg
    seen = {arg}
    cur = arg
    for _ in range(_CONJ_WALK_LIMIT):
        row = dep_index_by_pos.get(cur)
        if row is None or row.deprel not in ("fixed", "case"):
            break
        head = (row.head_line, row.head_token)
        if head in seen or head not in dep_index_by_pos:
            break
        seen.add(head)
        cur = head
    return cur


def _is_nominal_pos(pos_text: str) -> bool:
    """Rule CP: an adjective or a noun — the two POS a secondary predicate is written with.

    `"pronoun"` contains `"noun"`, so the pronoun leg has to be excluded explicitly rather than
    by the substring test the rest of this module uses for a single POS.
    """
    text = pos_text.lower()
    if "pronoun" in text:
        return False
    return "adjective" in text or "noun" in text


def _hosts_child(
    pos: tuple[int, int], row: DepRow, dep_index_by_pos: dict[tuple[int, int], DepRow]
) -> bool:
    """Rule BP: whether `row` is a child of the predicate at `pos`, reading an `aux`/`cop` head
    through to its lexical word.

    Every acceptance rule that asks "is this the predicate's *own* dependent" compared Layer 4's
    raw head to `pos`, and 53 arguments corpus-wide hang on an auxiliary or a copula instead of on
    the lexical verb that carries the tuple — "tre Frison **s'**averien dato mal vanto"
    (inferno 31:64), where the reflexive clitic is `expl` on `averien` while the predicate is
    `dato`. `derive_unit` already reaches through that edge (rule AM collects a stranded
    auxiliary's arguments onto the lexical head, rule AQ re-keys a citation that lands on one), so
    the gates were the only place still reading the un-normalized edge. The Inferno 26-30 batch's
    finding — *ask which checks run before a rule* — applied to a rule's own gate rather than to
    the order of two rules.
    """
    head = (row.head_line, row.head_token)
    return head == pos or _aux_head(head, dep_index_by_pos) == pos


def _adverbial_oblique(
    pos: tuple[int, int], arg: tuple[int, int], role: str,
    dep_index_by_pos: dict[tuple[int, int], DepRow],
    morph_pos_by_position: dict[tuple[int, int], str] | None,
) -> bool:
    """Rule J: a given `obl`/`obl:<prep>` whose argument is an adverb attached to that same
    predicate as `advmod` ("quivi", "là", "dinanzi") — an adverbial oblique. `derive_unit` only
    reads `obl` deprel children, so it can't produce one; the membership soft check already
    accepts exactly these tokens as `obl` arguments for the same reason.

    **Rule BC** widens the POS gate from `adverb` to any *nominal or pronominal* token. Layer 4
    uses `advmod` for adjuncts whose filler Layer 2 calls something else entirely — a bare
    adverbial nominal ("stieno i Malebranche **un poco** in cesso", inferno 22:100), a fused
    pronoun+preposition ("e dicean **seco**", 23:87, where the preposition is inside the word so
    no `case` child can carry it), a clitic pronoun ("**li** giacea un draco", 25:23). Layer 2
    saying the token is a noun or a pronoun is the whole gate: a nominal in an adjunct slot is an
    oblique whatever deprel the tree gave it, whereas rule R's caution still applies to the
    adjective and verb cases, which stay flagged as genuinely undecided."""
    if not (role == "obl" or OBL_RE.fullmatch(role)):
        return False
    row = dep_index_by_pos.get(arg)
    if row is None or row.deprel != "advmod" or not _hosts_child(pos, row, dep_index_by_pos):
        return False
    arg_pos = (morph_pos_by_position or {}).get(arg, "").lower()
    return any(tag in arg_pos for tag in ("adverb", "noun", "pronoun"))


def _predicative_advmod(
    pos: tuple[int, int], arg: tuple[int, int], role: str,
    dep_index_by_pos: dict[tuple[int, int], DepRow],
    morph_pos_by_position: dict[tuple[int, int], str] | None,
) -> bool:
    """Rule R: a given `xcomp` whose argument is an **adjective** attached to that same predicate
    as `advmod` ("e io etterno **duro**", "dinanzi polveroso va **superbo**", "il primo cerchio è
    **tutto**"). These are predicative complements — the construction rule M already covers — that
    Layer 4 attached adverbially instead; `derive_unit` only reads `ARG_DEPRELS`, so it cannot
    produce them at all.

    The adjective-POS gate is what keeps this structural rather than a blanket `advmod`
    exemption: the same shape with an adverb argument ("che fu nel cominciar cotanto **tosta**",
    "m'è **tardi**") is Layer 2 calling the word an adverb, which leaves the reading genuinely
    undecided, and stays flagged — the same caution `_adverbial_oblique` applies in reverse."""
    if role != "xcomp":  # `attr` is already canonicalized to `xcomp` before comparison
        return False
    row = dep_index_by_pos.get(arg)
    if row is None or row.deprel != "advmod" or not _hosts_child(pos, row, dep_index_by_pos):
        return False
    return "adjective" in (morph_pos_by_position or {}).get(arg, "").lower()


def _accusative_and_infinitive(
    pos: tuple[int, int], arg: tuple[int, int], role: str,
    dep_index_by_pos: dict[tuple[int, int], DepRow] | None,
    morph_features_by_position: dict[tuple[int, int], str] | None = None,
) -> bool:
    """Rule BI: the accusative-and-infinitive's shared nominal, named from the matrix side.

    "I' vidi ... **uno** aspettar così" (inferno 22:31), "trovammo risonar **quell' acqua tinta**"
    (16:104), "senta **qualunque** passa" (23:119): after a verb of perception or causation the
    nominal is the matrix verb's object *and* the infinitive's subject, and no reading has to
    choose. Layer 4 records it as the infinitive's `nsubj`, so `derive_unit` puts it on the
    infinitive only; the LLM names the same token as the matrix object, which is UD's own
    convention for the construction (object raising, `xcomp` + `obj`).

    Censused at 10 positions corpus-wide. Gated tightly on the two edges being present — the
    argument is the `nsubj` of a predicate that is *this* predicate's own `xcomp`/`ccomp` — so it
    reaches only the shape where the tree itself asserts both relations. Directional: the LLM
    naming a matrix object stays accepted; the derivation is not made to assert one."""
    if role != "obj" or dep_index_by_pos is None:
        return False
    row = dep_index_by_pos.get(arg)
    if row is None or row.deprel not in ("nsubj", "nsubj:pass"):
        return False
    host_pos = (row.head_line, row.head_token)
    host = dep_index_by_pos.get(host_pos)
    if host is None:
        return False
    if host.deprel not in ("xcomp", "ccomp"):
        # Layer 4 also writes the perception verb's complement as a plain `obj` ("Io vidi **due
        # sedere**", inferno 29:73; "vidi … **languir li spirti**", 29:66). Restricted to a host
        # Layer 2 calls an **infinitive**: the same census finds 28 finite clauses in the `obj`
        # slot, whose `nsubj` is the embedded clause's own subject and nobody's matrix object.
        if host.deprel != "obj" or "infinitive" not in (
                morph_features_by_position or {}).get(host_pos, "").lower():
            return False
    return (host.head_line, host.head_token) == pos


def _displaced_subject_pro_drop(
    grole: str, arg: tuple[int, int],
    g: dict[tuple[int, int], str], d: dict[tuple[int, int], str],
) -> bool:
    """Rule BH: rule M's mirror leg — the ∅ subject rule M's relabelling leaves behind.

    Rule M accepts the LLM calling a derived `subj` the predicative complement it is: "che mi
    parve una **lontra**" (inferno 22:36), "**Frati godenti** fummo" (23:103), "n'andavam **l'un**
    dinanzi e **l'altro** dopo" (23:2). But a clause whose only nominal has just been read as the
    complement has no overt subject left, so the LLM fills the slot with pro-drop ∅ — and that ∅
    was then reported as an extra argument, because the derivation put its one `subj` on the
    token rule M has already conceded.

    The two halves are one reading, so accepting one and reporting the other is the labeling
    split counted twice. Gated on rule M having actually fired for this predicate: some argument
    the derivation calls `subj` that the LLM calls `xcomp`. Without that, a bare ∅ subject the
    derivation contradicts with a concrete one stays flagged, which is the `extra_arg subj ∅`
    bucket the fourth `--fix` round is meant to measure."""
    if grole != "subj" or arg != (0, 0):
        return False
    return any(role == "subj" and g.get(a) == "xcomp" for a, role in d.items())


def _inverted_copula_complement(
    pos: tuple[int, int], arg: tuple[int, int], role: str,
    dep_index_by_pos: dict[tuple[int, int], DepRow] | None,
    morph_pos_by_position: dict[tuple[int, int], str] | None,
) -> bool:
    """Rule BF: a `cop` edge Layer 4 wrote the wrong way round.

    UD's `cop` points from the copula *verb* up to the nominal or adjectival predicate. In 11
    places the tree points it the other way — "poi che fu a terra sì **distrutto**" (inferno
    24:103) hangs the adjective `distrutto` as a `cop` child of `fu` — so `derive_unit`, which
    reads `cop` only to find the predicate a nominal heads, is silent about the complement
    altogether. The LLM reads `essere` as the predicate and the adjective as its `attr`, which is
    the corpus's own convention for a copular clause with an overt copula.

    The gate is the POS: a `cop` child Layer 2 calls an adjective or a noun cannot be a copula,
    so the edge is inverted on the tree's own evidence, and the token in it is the complement.
    A `cop` child that *is* a verb is the ordinary shape and stays untouched."""
    if role != "xcomp":  # `attr` is canonicalized to `xcomp` before comparison
        return False
    row = (dep_index_by_pos or {}).get(arg)
    if row is None or row.deprel != "cop" or not _hosts_child(pos, row, dep_index_by_pos):
        return False
    arg_pos = (morph_pos_by_position or {}).get(arg, "").lower()
    return "verb" not in arg_pos and any(t in arg_pos for t in ("adjective", "noun"))


def _undecided_subject_slot(
    drole: str, arg: tuple[int, int],
    g: dict[tuple[int, int], str], d: dict[tuple[int, int], str],
) -> bool:
    """Rule BA: `derive_unit` gave one predicate **two** subjects, and the LLM named one of them.

    A clause has one subject slot. When two survive coordination collapse the derivation has not
    decided between them, and requiring both is asserting more than the tree supports:

    - "E quelli: «**I'** mi partii»" (inferno 22:66) — the elided verb of speech leaves `quelli`
      with nowhere to attach, so Layer 4 hangs it on the quoted verb next to its real subject;
    - "com' elli 'ncontra ch'**una rana** rimane" (22:33) — the impersonal subject of the matrix
      verb lands on the subordinate one;
    - "come la madre ... **che** prende il figlio" (23:40) — the relative pronoun and its own
      antecedent, one referent named twice;
    - "li occhi miei ... e **l'animo** smagato" (25:146) — a gapped coordination Layer 4 wrote as
      two flat `nsubj` edges rather than a `conj`.

    Naming either one is a reading of the same slot, so this accepts *the derivation's* unnamed
    subject rather than the LLM's citation — the mirror of `_collapse_coordination`, which
    normalizes the case where the two are explicitly conjoined. Gated on the LLM having named one
    of them: an LLM that names a subject from outside the pair, or none at all, still diverges."""
    if drole != "subj" or arg == (0, 0):
        return False
    derived_subjects = [a for a, role in d.items() if role == "subj"]
    if len(derived_subjects) < 2:
        return False
    return any(g.get(a) == "subj" for a in derived_subjects)


def _gapped_second_term_argument(
    arg: tuple[int, int], d: dict[tuple[int, int], str],
) -> bool:
    """Rule CW: rule BA's oblique leg — the rest of the elided clause the second subject opens.

    "e come abete in alto si **digrada** / di ramo in ramo, così **quello in giuso**"
    (purgatorio 22:134), "che li occhi miei si **fero** a lui seguaci, / come **la mente a le
    parole sue**" (24:102), "si mosse, e **io di rietro inver' l'altura**" (9:69), "La sua
    chiarezza séguita l'ardore; / **l'ardor la visïone**" (paradiso 14:41), "ed **essi teco le
    cittadi e ' regni**" (18:84), "**ed ella primavera**" (purgatorio 28:51).

    Two subjects on one predicate is rule BA's evidence that Layer 4 has collapsed **two clauses**
    onto one head — a gapped coordination or the second term of a comparison, whose own verb the
    line does not repeat and which the tree therefore has nowhere else to put. Rule BA drew the
    conclusion for the subject slot only, and left the rest of the elided clause — its obliques,
    its object, its predicate complement — asserted as arguments of a predicate that never had
    them. The remnant is identified positionally, the one thing the tree does say about it: an
    argument standing **after** the second subject is on the second term's side of the gap, and
    the LLM, reading one clause per predicate, does not list it.

    Censused corpus-wide at 85 arguments standing after a second derived subject, 13 of which the
    LLM does not cite; every one of those 13 is a gapped second conjunct or comparison term.
    Directional, like rule BA: this accepts the derivation's uncited argument, and an argument the
    LLM cites from outside the tree stays flagged."""
    if arg == (0, 0):
        return False
    subjects = sorted(a for a, role in d.items() if role == "subj" and a != (0, 0))
    return len(subjects) >= 2 and arg > subjects[-1]


def _depictive_bare_oblique(
    grole: str, drole: str, pos: tuple[int, int], arg: tuple[int, int],
    dep_index_by_pos: dict[tuple[int, int], DepRow] | None,
    morph_pos_by_position: dict[tuple[int, int], str] | None,
    case_children: set[tuple[int, int]],
) -> bool:
    """Rule AZ: rule R's mirror leg — the depictive adjective Layer 4 hung on the predicate as a
    bare `obl` instead of as `advmod`.

    "tornò sù **convolto**" (inferno 21:46), "ei ne verranno dietro **più crudeli**" (23:17),
    "si mira tutto **smarrito**" (24:115), "**supin** si diede a la pendente roccia" (10:72, the
    open route this closes). The construction is the same secondary predication rules R, AA and
    AU already accept from the other three attachment points — `advmod` on the predicate, `acl`
    and `amod` on one of its arguments — and Layer 4 records it here with the one deprel
    `derive_unit` *can* read, so the divergence surfaces as a role mismatch rather than as
    checker silence: the derivation says `obl`, the LLM says the complement it is.

    The three gates are what keep an ordinary oblique out. **No `case` child**: a preposition in
    the tree makes the phrase a genuine adjunct ("è **per me** giocondo"), and only a bare `obl`
    is a candidate. **Nominal POS** — an adjective, exactly as in rule R, or (rule CP) a noun.
    **The predicate's own child**, so an adjective obl'd onto some other clause is not swept in.
    Directional like rules L/M: a given `obl` against a derived `xcomp` means the tree carried
    the complement explicitly and the LLM contradicted it, which stays flagged.

    Rule CP is the noun leg of exactly that shape: Italian predicates the same secondary
    predication with a bare nominal as readily as with an adjective, and Layer 4 reaches for the
    same `obl` for want of anything better — "che piuma sembran tutte l'altre some" (purgatorio
    19:105), "come fatto fui **roman pastore**" (19:107), "non uscir … **Gentili**, ma
    **Cristiani**" (paradiso 20:103), "e, quasi **amici**, dipartirsi pigri" (33:114, whose
    adjectival twin `pigri` in the same line rule AZ already takes). Censused at 245 bare nominal
    obliques corpus-wide against rule AZ's 44 adjectival ones — a larger population because the
    caseless nominal `obl` is also the corpus's adverbial accusative ("la **notte** ch'i'
    passai", inferno 1:21) — but the acceptance is not the census: it fires only where the LLM
    independently read the same token as the predicate's complement, which a temporal accusative
    does not attract.

    The **pronoun** and **adverb** legs stay out. The adverb one was declined when rule AZ was
    written ("è **fuor** di strada", paradiso 8:148, leaves the reading undecided); a pronoun in
    a bare `obl` is overwhelmingly the corpus's own clitic (509 of the 1118), where the question
    is rules AB/AW's clitic role, not secondary predication."""
    if grole != "xcomp" or drole != "obl":  # `attr` is canonicalized to `xcomp` beforehand
        return False
    if arg in case_children:
        return False
    row = (dep_index_by_pos or {}).get(arg)
    if row is None or row.deprel != "obl" or not _hosts_child(pos, row, dep_index_by_pos):
        return False
    return _is_nominal_pos((morph_pos_by_position or {}).get(arg, ""))


def _nmod_complement_of_predicate(
    pos: tuple[int, int], arg: tuple[int, int], role: str,
    dep_index_by_pos: dict[tuple[int, int], DepRow],
    case_lemmas: dict[tuple[int, int], set[str]],
) -> bool:
    """Rule S: a given `obl:<lemma>` whose argument is an `nmod` child **of the predicate itself**
    and carries a `case` child naming that same preposition. Rule D already accepts the same
    shape one edge further out (an `nmod` of one of the predicate's derived arguments); this is
    the direct-child case, which `derive_unit` cannot produce because `nmod` is outside
    `ARG_DEPRELS`.

    Two constructions make up the population, and both leave the tree uncontradicted. Most
    (58/62) are **nominal or adjectival predicates** — "furon cagione **di sua vittoria**",
    "di quanto mal fu matre", "Oppresso **di stupore**" — where UD correctly attaches the PP
    complement of the predicate nominal as `nmod`, and it is an argument of the predication all
    the same. The rest are verbal predicates where Layer 4 wrote `nmod` for what is plainly an
    oblique ("nel fermar **tra Dio e l'omo** il patto", "mischiato **di lagrime**"). Gating on
    the predicate's POS would separate those two correct readings rather than sound from
    unsound, the mistake measured for rule M's proposed gate, so this ships ungated.

    Requiring the *same* lemma as the `case` child is what keeps it structural — the LLM names
    the preposition literally present on that edge. All 62 instances in the corpus satisfy it, so
    the strict and loose variants return the identical set, exactly as for rule L."""
    if not OBL_RE.fullmatch(role):
        return False
    row = dep_index_by_pos.get(arg)
    if row is None or row.deprel != "nmod" or not _hosts_child(pos, row, dep_index_by_pos):
        return False
    return role.split(":", 1)[1] in case_lemmas.get(arg, set())


def _marked_adverbial_clause(
    pos: tuple[int, int], arg: tuple[int, int], role: str,
    dep_index_by_pos: dict[tuple[int, int], DepRow],
    marker_lemmas: dict[tuple[int, int], set[str]],
) -> bool:
    """Rule T: a given `obl:<lemma>` whose argument is an `advcl` child **of the predicate itself**
    and carries a `mark`/`case` child naming that same preposition — the prepositional infinitive
    ("s'appresta **per venir** verso noi", "**A descriver** lor forme più non spargo rime",
    "Ciascun si fida del beneficio tuo **sanza giurarlo**"). Layer 4 attaches these as adverbial
    clauses, which is outside `ARG_DEPRELS`, so `derive_unit` cannot produce them at all; the LLM
    reads the same edge as an oblique and names the preposition literally sitting on it.

    This is rule S's shape with `advcl` in place of `nmod`, and it inherits rule N's gate: the
    lemma must be one the tree itself carries. That gate is what keeps it structural rather than
    a blanket `advcl` exemption — the complement-vs-adjunct half of this deprel (a given
    `ccomp`/`xcomp` over an adverbial clause) is a lexical argument-structure judgment and stays
    flagged. The loose variant, accepting a bare given `obl` whenever the clause carries any
    marker, was measured at a further −2 and **rejected**: it admits markers that are not
    prepositions at all ("infin ch'el si raggiunge **ove** la tirannia convien che gema"), where
    nothing in the tree confirms the oblique reading."""
    if not OBL_RE.fullmatch(role):
        return False
    row = dep_index_by_pos.get(arg)
    if row is None or row.deprel != "advcl" or not _hosts_child(pos, row, dep_index_by_pos):
        return False
    return role.split(":", 1)[1] in marker_lemmas.get(arg, set())


def _marked_complement_clause(
    pos: tuple[int, int], grole: str, drole: str, arg: tuple[int, int],
    dep_index_by_pos: dict[tuple[int, int], DepRow] | None,
    marker_lemmas: dict[tuple[int, int], set[str]],
) -> bool:
    """Rule CQ: rule T's `xcomp` leg — the prepositional infinitive Layer 4 attached as a
    complement rather than as an adverbial clause.

    "mi fé **desideroso di sapere**" (purgatorio 20:146) and "Qual pare **a riguardar** la
    Carisenda" (inferno 31:136) both hang the infinitive on its governor as `xcomp` while
    writing the preposition that introduces it as a `case` child — the deprel of a *nominal*
    argument. The tree is therefore of two minds about the same edge, and the two readings split
    along that seam: `derive_unit` reads the deprel and calls it `xcomp`, the LLM reads the
    preposition sitting on the token and calls it `obl:di` / `obl:a`. Neither contradicts the
    line; the divergence is the corpus's own `mark`-vs-`case` convention for the infinitival
    complementizer, which rule T already settles one deprel over.

    The gate is rule T's, unchanged: the LLM's lemma must be one the tree itself carries on that
    token. That is what keeps rule AK's and rule V's questions out — "pare a' lor **vivagni**"
    (paradiso 9:135) is an `xcomp` the LLM calls `obl:a` on the strength of a preposition
    belonging to the *dative* beside it, and the token itself carries no marker, so it stays
    flagged. Directional, like rule T: a given `xcomp` over a derived oblique is the
    complement-vs-adjunct judgment, not this convention, and is left where rule T left it."""
    if drole != "xcomp" or not OBL_RE.fullmatch(grole):
        return False
    row = (dep_index_by_pos or {}).get(arg)
    if row is None or not _hosts_child(pos, row, dep_index_by_pos or {}):
        return False
    return grole.split(":", 1)[1] in marker_lemmas.get(arg, set())


def _gapped_coordinate_oblique(
    pos: tuple[int, int], arg: tuple[int, int], role: str,
    dep_index_by_pos: dict[tuple[int, int], DepRow],
    children_by_pos: dict[tuple[int, int], list[DepRow]],
    d: dict[tuple[int, int], str],
) -> bool:
    """Rule CG: the coordinate oblique whose noun is elided. "or dal sinistro e or dal destro
    fianco" (purgatorio 10:27) is two obliques — "from the left [side] and from the right side" —
    and Layer 4 records the ellipsis by hanging *both* prepositions on the one surviving noun,
    leaving the first phrase citable only by its adjective. The LLM names both; the derivation,
    which reads one `obl` child, names one.

    The second `case` child is the tree's own evidence for the ellipsis, so the gate is
    structural: the citation must be an adnominal modifier of a derived argument of this same
    predicate that carries two or more `case` children, and must take that argument's role.
    Censused at 56 doubly-marked obliques corpus-wide."""
    head_row = dep_index_by_pos.get(arg)
    if head_row is None or head_row.deprel not in ("amod", "det", "det:poss", "nummod"):
        return False
    host = (head_row.head_line, head_row.head_token)
    if d.get(host) != role:
        return False
    return sum(1 for c in children_by_pos.get(host, ()) if c.deprel == "case") >= 2


def _promoted_conjunct_argument(
    pos: tuple[int, int], arg: tuple[int, int],
    dep_index_by_pos: dict[tuple[int, int], DepRow],
    children_by_pos: dict[tuple[int, int], list[DepRow]],
    morph_pos_by_position: dict[tuple[int, int], str] | None,
) -> bool:
    """Rule CC: rule CA's argument leg — the coordinate nominal Layer 4 promoted to `conj` on the
    predicate itself. "Sordel rimase e **l'altre genti** forme" (purgatorio 9:58), "**qual
    merito** o **qual grazia** mi ti mostra?" (7:19): UD promotes the second conjunct to the
    clause head whenever it reads the coordination as clausal, and rule CA has just decided that
    a non-verb conjunct with no arguments of its own is *not* an elided clause — which leaves it
    a coordinate member of one of the predicate's own slots, exactly where the LLM puts it, and
    nowhere at all in the derivation.

    The gate is rule CA's own test, so the two rules cover the same positions from the two sides:
    a conjunct with arguments of its own is a real gapped clause and its citation stays flagged.
    The role is whatever the LLM assigns, as in rule AJ — the tree records no slot for the
    conjunct to disagree with."""
    row = dep_index_by_pos.get(arg)
    if row is None or row.deprel != "conj":
        return False
    if (row.head_line, row.head_token) != pos:
        return False
    pos_label = (morph_pos_by_position or {}).get(arg, "")
    if not pos_label or is_verb_pos(pos_label) or "conjunction" in pos_label.lower():
        return False
    return not any(c.deprel in ARG_DEPRELS for c in children_by_pos.get(arg, ()))


def _stranded_on_underived_complement(
    pos: tuple[int, int], arg: tuple[int, int], role: str,
    dep_index_by_pos: dict[tuple[int, int], DepRow],
    derived_preds: set[tuple[int, int]],
    case_lemmas: dict[tuple[int, int], set[str]],
) -> bool:
    """Rule CB: an oblique the tree hangs on a predicative complement the derivation never
    promotes. "li occhi e 'l naso / e **al sì e al no** discordi **fensi**" (purgatorio 10:63):
    Layer 4 attaches both obliques to `discordi`, the adjective it marks `attr` on `fensi`, and
    `derive_unit` promotes neither adjectival complements nor their arguments — so an argument
    the tree plainly records is dropped, and the LLM, which reads the line and hangs it on the
    only verb there is, is reported for naming it.

    Rule AM makes the same collection one edge over, from a predicate's own `cop`/`aux`; rule X
    accepts the *reverse* relocation, where the complement **is** a derived predicate and the
    two readings disagree about which of the two carries the argument. This is the case where
    there is no second predicate to disagree with, so the argument has exactly one home in each
    reading and they are the same predication.

    Gated the way rules S and T are gated: the given `obl:<lemma>` must name a preposition the
    tree itself carries on that edge, so nothing is accepted the Layer-4 `case` child does not
    already say."""
    if not OBL_RE.fullmatch(role):
        return False
    row = dep_index_by_pos.get(arg)
    if row is None or row.deprel not in ("obl", "obl:agent"):
        return False
    host = (row.head_line, row.head_token)
    if host == pos or host in derived_preds:
        return False
    host_row = dep_index_by_pos.get(host)
    if host_row is None or host_row.deprel not in ("attr", "xcomp"):
        return False
    if (host_row.head_line, host_row.head_token) != pos:
        return False
    return role.split(":", 1)[1] in case_lemmas.get(arg, set())


def _drop_nmod_obliques(
    g: dict[tuple[int, int], str], d: dict[tuple[int, int], str],
    derived_args: set[tuple[int, int]], dep_index_by_pos: dict[tuple[int, int], DepRow],
) -> None:
    """Rule D: accept an oblique whose argument hangs as `nmod` off one of the predicate's own
    derived arguments ("ha *bisogno* **di te**" — the dep tree attaches "te" to the noun, the
    LLM reads it as the predicate's oblique). Mutates `g` in place."""
    for arg, role in list(g.items()):
        if arg in d or not (role == "obl" or OBL_RE.fullmatch(role)):
            continue
        row = dep_index_by_pos.get(arg)
        if row is not None and row.deprel == "nmod" and (row.head_line, row.head_token) in derived_args:
            g.pop(arg)


def _oblique_lemma_refinement(
    grole: str, drole: str, arg: tuple[int, int], case_children: set[tuple[int, int]]
) -> bool:
    """Rule L: derived bare `obl` (no `case` child naming the preposition) vs a given
    `obl:<lemma>` — the LLM names a fused/clitic preposition the dep tree leaves implicit
    ("che nel lago del cor **m'**era durata": clitic dative, derive_unit `obl`, LLM `obl:a`).
    `derive_unit` emits the lemma-qualified form only when a `case` child makes the preposition
    explicit, so the given label is strictly more informative, not a disagreement — the mirror
    of `_safe_role_repair`, which rewrites the opposite direction for the same reason."""
    return drole == "obl" and bool(OBL_RE.fullmatch(grole)) and arg not in case_children


def _case_marked_object(
    grole: str, drole: str, arg: tuple[int, int],
    case_lemmas: dict[tuple[int, int], set[str]],
) -> bool:
    """Rule N: a given `obl:<lemma>` against a derived `obj`/`subj`, where the argument carries a
    `case` child naming **that same** preposition ("curan **di te**", "contastare **a Ruberto**",
    "gridavano «**A Filippo** Argenti!»"). `derive_unit` takes the role from the deprel alone, so
    a case-marked nominal Layer 4 attached as `obj`/`nsubj` is reported as a direct argument and
    the preposition sitting in the tree is dropped. The LLM reads the preposition that is there,
    so nothing in the dep tree is contradicted.

    One-directional, as for rules L and M: a given `obj`/`subj` against a derived `obl:<lemma>`
    means the LLM dropped a preposition the tree makes explicit, which stays flagged. Requiring
    the *same* lemma is what keeps it narrow — naming a different preposition than the `case`
    child (12 instances) is a real disagreement."""
    if not (OBL_RE.fullmatch(grole) and drole in ("obj", "subj")):
        return False
    return grole.split(":", 1)[1] in case_lemmas.get(arg, set())


def _co_present_preposition(
    grole: str, drole: str, arg: tuple[int, int],
    case_lemmas: dict[tuple[int, int], set[str]],
) -> bool:
    """Rule O: two different `obl:<lemma>` labels for the same argument, where the *given* lemma
    is one of the argument's own `case` children. Italian stacks prepositions ("in su le porte",
    "dietro a noi", "dentro a lo specchio", "infino al giro quinto"), and `derive_unit` reports
    exactly one of them — whichever `case` child it reaches first — so the LLM naming another
    preposition that is literally in the tree is a choice between two co-present markers, not a
    contradiction of the parse.

    One-directional like rules L/M/N: the mirror case (the *derived* lemma is a `case` child and
    the given one is not) means the LLM named a preposition the tree does not carry, which stays
    flagged."""
    if not (OBL_RE.fullmatch(grole) and OBL_RE.fullmatch(drole)):
        return False
    return grole.split(":", 1)[1] in case_lemmas.get(arg, set())


def _clausal_complement_flavor(grole: str, drole: str) -> bool:
    """Rule P: `ccomp` against `xcomp` (either way round). Both labels say "clausal complement of
    this predicate"; they differ only on whether the complement has its own subject or takes one
    by control — a judgment Layer 4 itself makes inconsistently for the same construction ("Fa
    che tu m'abbracce" is tagged `xcomp` although "tu" is overt). Neither side is more
    informative, so this is a Phase-1-style label equivalence rather than an acceptance of one
    reading over the other — the same move `_ROLE_CANON` already makes for `attr`/`xcomp`, kept
    local to the divergence check because the two roles stay distinct in the artifact."""
    return {grole, drole} == {"ccomp", "xcomp"}


def _clausal_object(
    grole: str, drole: str, arg: tuple[int, int],
    morph_pos_by_position: dict[tuple[int, int], str] | None,
) -> bool:
    """Rule Q: a given `ccomp` against a derived `obj`/`subj` whose argument is a **verb**. Layer
    4 attaches the complement clause's head verb straight to the matrix predicate as `obj`/`nsubj`
    ("or mi concedi ch'io **sappia**", "dimmi se tu **sai**", "avvien che poi nel maginare
    **abborri**"), and `derive_unit` reads the deprel alone, so a whole clause is reported as a
    direct argument. The LLM names it a clausal complement; the verb POS is what makes that
    strictly more informative rather than a competing reading.

    One-directional, as for rules L/M/N/O: a given `obj`/`subj` against a derived `ccomp` means
    the tree carried an explicit `ccomp` deprel and the LLM flattened it, which stays flagged."""
    if not (grole == "ccomp" and drole in ("obj", "subj")):
        return False
    return is_verb_pos((morph_pos_by_position or {}).get(arg, ""))


def _predicative_complement(grole: str, drole: str) -> bool:
    """Rule M: a given `xcomp` against a derived `obj`/`subj`. UD has no relation for secondary
    predication: an object complement is attached as plain `obj` ("mi chiamaste **Ciacco**", "li
    chiama **orbi**", "hanno Italia **morta**") and a copular predicate nominal as `nsubj` ("non
    son **torri**", "mi parve una **lontra**", "chi tu **se'**"), so `derive_unit` can only ever
    report the attachment. The LLM names the same token's predicative function instead — the
    labeling split Phase 1 already canonicalizes `attr` -> `xcomp` for, one step further.

    One-directional, for the same reason as `_safe_role_repair`/`_oblique_lemma_refinement`: a
    given `obj`/`subj` against a derived `xcomp` means the dep tree *did* carry an explicit
    `xcomp`/`ccomp` deprel and the LLM contradicted it, which stays flagged."""
    return grole == "xcomp" and drole in ("obj", "subj")


def _case_supports_role(case_value: str, role: str) -> bool:
    """Whether the `case/` annex's value for an argument position is compatible with a Layer-5
    role label. The mapping between the two frozen vocabularies is the obvious one and nothing
    external enters it — both were authored by a model reading the Italian alone (see PLAN.md's
    *Neutrality check*).

    `obl:a` is deliberately compatible with `dative` **and** with the locative/ablative values:
    Italian `a` marks both the indirect object and a place ("a Roma"), so the annex cannot
    adjudicate between two oblique flavors there. A fused value (`a+b`, `SLOT_SEP`-joined for a
    fused token like `gliel'`) matches nothing, so a fused position decides nothing."""
    if role == "subj":
        return case_value == "nominative"
    if role == "obj":
        return case_value == "accusative"
    if role == "iobj":
        return case_value == "dative"
    if role == "obl:a":
        return case_value in ("dative", "ablative", "locative")
    if role == "obl" or role.startswith("obl:"):
        return case_value in ("ablative", "locative")
    return False


def _bare_pronoun_position(
    pos: tuple[int, int], morph_pos_by_position: dict[tuple[int, int], str] | None
) -> bool:
    """Whether a token is a pronoun and *nothing else* — rule U's scope gate.

    The `case` annex is in scope for every token whose Layer-2 `pos` names a pronoun among its
    parts, fused tokens included (`case.scope_slots`): `venendomi` (`verb+pronoun`) carries the
    enclitic's case. But a Layer-5 argument citing that position cites the **verb** — there is no
    separate token for the clitic — so the annex's value describes something other than the role
    under dispute. 601 of the 13113 in-scope positions are fused like this; rule U skips them all.
    """
    value = (morph_pos_by_position or {}).get(pos)
    if value is None:
        return False
    return SLOT_SEP not in value and value.strip().lower().endswith("pronoun")


def _comparative_come_complement(
    grole: str, drole: str, arg: tuple[int, int],
    dep_index_by_pos: dict[tuple[int, int], DepRow] | None,
    morph_pos_by_position: dict[tuple[int, int], str] | None,
) -> bool:
    """Rule AK: a comparative `come` phrase read as a predicative complement.

    "che qui staranno *come porci* in brago" (inferno 8:50). Layer 2 tags `come` a **conjunction**
    — which is what it is, the marker of a comparative clause — while Layer 4 attaches it as a
    `case` child, so `derive_unit`'s oblique refinement mints the preposition-shaped role
    `obl:come` out of a token no layer calls a preposition. The LLM reads the phrase as the
    predicative complement it is. Gated on Layer 2's own POS, so a `come` that some other position
    genuinely tags as a preposition keeps its oblique reading.
    """
    if drole != "obl:come" or grole != "xcomp":
        return False
    if dep_index_by_pos is None or morph_pos_by_position is None:
        return False
    return any(
        row.deprel == "case" and (row.head_line, row.head_token) == arg
        and _normalize_prep_lemma(row.word.lower()) == "come"
        and "conjunction" in morph_pos_by_position.get((row.line, row.token), "").lower()
        for row in dep_index_by_pos.values()
    )


def _comparative_come_adjunct(
    pos: tuple[int, int], arg: tuple[int, int], drole: str,
    dep_index_by_pos: dict[tuple[int, int], DepRow] | None,
    children_by_pos: dict[tuple[int, int], list[DepRow]] | None,
    morph_pos_by_position: dict[tuple[int, int], str] | None,
) -> bool:
    """Rule AR: an oblique the derivation reads off a verbless comparative clause.

    Rule AK covers the `role_mismatch` leg of comparative `come`; this is the `missing_arg` leg,
    and it is about the *clause*, not the label. A comparison with no verb of its own — "son tre
    cerchietti … **come que' che lassi**" (inferno 11:17), "**Come d'un stizzo verde** ch'arso
    sia … sì de la scheggia rotta usciva" (13:43) — leaves Layer 4 no head to hang the compared
    nominal on but the main predicate, so `derive_unit` reports it as that predicate's argument.
    It is an adjunct of comparison in both readings, and the LLM (correctly) does not list it.

    Gated on a Layer-2 conjunction `come` marking the phrase: either as the compared nominal's
    own `mark` (11:17), or as the predicate's, in which case a correlative `sì`/`così` on the
    same predicate must separate the two halves and the argument must stand on the comparison's
    side of it (13:43). Without the correlative, a `come`-marked predicate is an ordinary
    comparative *clause* with its own verb, whose obliques are its own.
    """
    if drole != "obl" and not drole.startswith("obl:"):
        return False
    if dep_index_by_pos is None or children_by_pos is None or morph_pos_by_position is None:
        return False

    def come_mark(host: tuple[int, int], words: tuple[str, ...] = ("come", "com")) -> DepRow | None:
        for c in children_by_pos.get(host, ()):
            if (c.deprel == "mark" and c.word.lower().rstrip("'") in words
                    and "conjunction" in morph_pos_by_position.get((c.line, c.token), "").lower()):
                return c
        return None

    # Rule BK: `che` is the other marker of a verbless comparison, and the *second term* of a
    # comparison is the shape it marks — "vedesse altro **che la fiamma sola**" (inferno 26:38),
    # "guizzando più **che li altri suoi consorti**" (19:32), "ogn' uom v'è barattier, fuor
    # **che Bonturo**" (21:41). Censused at 51 corpus-wide, every one a comparative or exceptive
    # second term. Only the *argument* leg takes `che`: a `che`-marked clause hanging on the
    # predicate is an ordinary complement clause, so the correlative branch below stays `come`.
    if come_mark(arg, ("come", "com", "che", "ch")) is not None:
        return True
    marker = come_mark(pos)
    if marker is None:
        return False
    correlative = next(
        (c for c in children_by_pos.get(pos, ())
         if c.deprel == "advmod" and c.word.lower().rstrip("'") in ("sì", "si", "così", "cosi")),
        None,
    )
    if correlative is None:
        return False
    if (correlative.line, correlative.token + 1) == (marker.line, marker.token):
        # Rule BL: "**sì come** nuvoletta, in sù salire" (inferno 26:39). When the correlative
        # stands immediately *before* the marker the two are one word — `sì come` = "just as" —
        # so there is no `sì … come` span to place the compared nominal inside, and the
        # comparison is simply what follows the marker. Kept to the phrase `come` opens: the
        # argument must be the marker's next token but for its own determiners, so the
        # predicate's other obliques ("in sù") stay its own. Censused at 107 `sì come` clusters.
        own = {(c.line, c.token) for c in children_by_pos.get(arg, ())
               if c.deprel in ("det", "det:poss", "amod", "nummod", "case", "cc")}
        between = {(marker.line, t) for t in range(marker.token + 1, arg[1])} if marker.line == arg[0] else None
        return between is not None and arg > (marker.line, marker.token) and between <= own
    return (marker.line, marker.token) <= arg < (correlative.line, correlative.token)


def _conjunction_oblique(
    arg: tuple[int, int], drole: str,
    morph_pos_by_position: dict[tuple[int, int], str] | None,
) -> bool:
    """Rule BM: an oblique whose filler is a token Layer 2 calls a **conjunction**.

    "Nel tempo **che** Iunone era crucciata" (inferno 30:1), "**onde** Cleopatràs lussurïosa"
    (14:54): the relative adverb — "at which", "whence" — is the clause's link, and Layer 2 tags
    it a conjunction for exactly that reason. Layer 4 nonetheless parks it in an `obl` slot, so
    `derive_unit` reports it as an argument of the relative clause's verb, while the LLM lists
    the clause's own arguments and leaves the connective out.

    Restricted to the oblique slot, which is where the connective reading and the argument
    reading coincide: the same census finds 147 `nsubj` and 61 `obj` conjunction-tagged tokens,
    and those are relative pronouns doing real argument work that both readings name. This is
    the tail of the known Layer-2 route (relative `che`/`onde` tagged `conjunction`, 247 tokens),
    which can only be settled by a model read of the `case` annex; until then, an adjunct slot
    filled by a conjunction is not something the derivation can assert.
    """
    if not (drole == "obl" or OBL_RE.fullmatch(drole)):
        return False
    return "conjunction" in (morph_pos_by_position or {}).get(arg, "").lower()


def _clause_named_by_marker(
    pos: tuple[int, int], clause: tuple[int, int], role: str,
    dep_index_by_pos: dict[tuple[int, int], DepRow] | None,
    cited: dict[tuple[int, int], str],
) -> bool:
    """Rule CK: the LLM names a subordinate clause by the complementizer that opens it.

    "degno / ben è **che** 'l nome di tal valle **pèra**" (purgatorio 14:30), "**che** tu segui
    tuo corso" (18:34), "**che** più andasse al cielo" (paradiso 14:18). The clause fills one of
    the predicate's slots; `derive_unit`, reading the tree, cites its **head** (the verb Layer 4
    hangs on `pos`), and the LLM cites the `che` that introduces it. Both name the same
    constituent in the same slot, so this is a citation convention, exactly like rule AE's free
    relative cited from its two ends — and it is written as one gate read from both sides, the
    shape rules CA/CC established: without the acceptance leg the marker is an `extra_arg` and
    without the mirror the clause is a `missing_arg`, for the one disagreement.

    Two gates keep it narrow. The marker must hang **on that very clause** and the clause on
    this very predicate, so a `mark` belonging to some other clause is not swept in (rule BW
    covers the different shape where the marker hangs on the predicate itself and fills a slot
    of its own). And the roles must match: 15 of the 18 positions censused corpus-wide pair the
    LLM's `subj` against a derived `ccomp` — the impersonal subject-clause question, a second
    claim about the slot, and already accepted elsewhere where it is accepted at all.
    """
    if dep_index_by_pos is None or clause == (0, 0):
        return False
    clause_row = dep_index_by_pos.get(clause)
    if clause_row is None or (clause_row.head_line, clause_row.head_token) != pos:
        return False
    for other, other_role in cited.items():
        if other_role != role or other == clause:
            continue
        marker = dep_index_by_pos.get(other)
        if marker is None or marker.deprel != "mark":
            continue
        if (marker.head_line, marker.head_token) == clause:
            return True
    return False


def _marker_of_derived_clause(
    pos: tuple[int, int], arg: tuple[int, int], grole: str,
    dep_index_by_pos: dict[tuple[int, int], DepRow] | None,
    derived: dict[tuple[int, int], str],
) -> bool:
    """Rule CK, read from the marker's end: the cited token is the `mark` of a clause the
    derivation gives this predicate in the same role. See `_clause_named_by_marker`."""
    if dep_index_by_pos is None or arg == (0, 0):
        return False
    marker = dep_index_by_pos.get(arg)
    if marker is None or marker.deprel != "mark":
        return False
    clause = (marker.head_line, marker.head_token)
    return (clause != arg and derived.get(clause) == grole
            and _clause_named_by_marker(pos, clause, grole, dep_index_by_pos, {arg: grole}))


_COMPLEMENT_ROLES = frozenset({"obj", "ccomp", "xcomp"})


def _wh_word_of_derived_clause(
    pos: tuple[int, int], arg: tuple[int, int], grole: str,
    dep_index_by_pos: dict[tuple[int, int], DepRow] | None,
    morph_pos_by_position: dict[tuple[int, int], str] | None,
    children_by_pos: dict[tuple[int, int], list[DepRow]] | None,
    derived: dict[tuple[int, int], str],
) -> bool:
    """Rule CX: rule CK widened from the complementizer to the **interrogative word**.

    "Se tu riduci a mente **qual** fosti meco" (purgatorio 23:115): the complement of `riduci` is
    the indirect question "qual fosti meco", which `derive_unit` cites by its verb and the LLM
    cites by the `qual` that opens it. Rule CK is the same convention for a clause opened by a
    `che`, and it is written for a `mark` and for one role on both sides. Neither gate reaches
    here: an interrogative word is a constituent *inside* its clause (Layer 4 makes `qual` the
    `advmod` of `fosti`, the predicate complement it also is — rule BW's tension), and the
    complement of a verb of remembering is `obj` to one reading and `ccomp` to the other, which
    is a difference of notation about the same slot, not two claims.

    Three gates keep it to the shape. The word must be one Layer 2 calls a pronoun, adjective or
    adverb rather than a conjunction — rule BW's own POS test, which separates an interrogative
    word from a subordinator. It must **open** the clause: the leftmost token of the whole
    subtree, so a word from the middle of it is not swept in. And both roles must be complement
    roles, so a clause the derivation puts in the subject slot stays flagged."""
    if dep_index_by_pos is None or arg == (0, 0) or grole not in _COMPLEMENT_ROLES:
        return False
    row = dep_index_by_pos.get(arg)
    if row is None or row.deprel in _SUBJ_DEPRELS:
        # The embedded clause's own **subject** is the one constituent whose citation on the
        # matrix is a claim about a different slot rather than a way of naming the clause: that
        # is rule BI's accusative-and-infinitive ("I' vidi uno aspettar così"), which has its own
        # gate. The six positions this rule takes are markers and predicate complements
        # (`attr`, `mark`, `advmod`, `xcomp`, `obj`), never a subject.
        return False
    clause = (row.head_line, row.head_token)
    if clause == arg or derived.get(clause) not in _COMPLEMENT_ROLES:
        return False
    clause_row = dep_index_by_pos.get(clause)
    if clause_row is None or (clause_row.head_line, clause_row.head_token) != pos:
        return False  # rule CK's first gate: the clause hangs on this very predicate
    tag = (morph_pos_by_position or {}).get(arg, "").lower()
    if not tag or "conjunction" in tag:
        return False
    if not ("pronoun" in tag or "adjective" in tag or "adverb" in tag):
        return False
    return arg == min(_subtree(clause, children_by_pos) | {clause})


def _subtree(
    pos: tuple[int, int], children_by_pos: dict[tuple[int, int], list[DepRow]] | None
) -> set[tuple[int, int]]:
    """Every position below `pos` in the Layer-4 tree (rule CX's "opens the clause" test)."""
    seen: set[tuple[int, int]] = set()
    frontier = [pos]
    while frontier and len(seen) < 64:
        for child in (children_by_pos or {}).get(frontier.pop(), ()):
            node = (child.line, child.token)
            if node not in seen:
                seen.add(node)
                frontier.append(node)
    return seen


def _marker_slot_argument(
    pos: tuple[int, int], arg: tuple[int, int], grole: str,
    dep_index_by_pos: dict[tuple[int, int], DepRow] | None,
    morph_pos_by_position: dict[tuple[int, int], str] | None,
) -> bool:
    """Rule BW: rule BM's mirror leg — an argument Layer 4 parked in this predicate's `mark` slot.

    "un non sapeva **che** bianco" (purgatorio 2:23), "vedrai … **qual** io fossi" (paradiso
    1:68), "sappiendo … **quanto** costa" (paradiso 19:74). The interrogative or relative word
    opens the clause *and* fills one of its argument slots, which is a thing one token can do and
    a UD tree cannot say twice: Layer 4 records the connective function with `mark`, `mark` is
    outside `ARG_DEPRELS`, and so `derive_unit` cannot assert the argument function at all. The
    LLM, reading the line rather than the tree, names it.

    Rule BM is the same tension seen from the other side — an oblique slot Layer 4 filled with a
    token Layer 2 calls a *conjunction*, where the connective reading is the right one and the
    LLM's omission is accepted. Both are the tail of the known Layer-2 route (relative
    `che`/`onde` tagged `conjunction`, 247 tokens), and the POS gate is what separates them: a
    `mark` Layer 2 calls a conjunction **is** a subordinator and stays flagged, while a `mark`
    Layer 2 calls a pronoun, an adjective or an adverb is an interrogative/relative word the tree
    could only label once. Gated on the marker hanging on this very predicate (through `aux`/`cop`,
    rule BP), so a marker belonging to some other clause is not swept in.
    """
    if dep_index_by_pos is None or morph_pos_by_position is None or arg == (0, 0):
        return False
    row = dep_index_by_pos.get(arg)
    if row is None or row.deprel != "mark" or not _hosts_child(pos, row, dep_index_by_pos):
        return False
    tag = morph_pos_by_position.get(arg, "").lower()
    if not tag or "conjunction" in tag:
        return False
    return "pronoun" in tag or "adjective" in tag or "adverb" in tag


def _depictive_bare_oblique_omitted(
    pos: tuple[int, int], arg: tuple[int, int], drole: str,
    dep_index_by_pos: dict[tuple[int, int], DepRow] | None,
    morph_pos_by_position: dict[tuple[int, int], str] | None,
    case_children: set[tuple[int, int]],
) -> bool:
    """Rule BX: rule AZ's `missing_arg` leg — the depictive the LLM leaves out entirely.

    "mi cominciò **tutto rivolto**" (purgatorio 3:23), "**pien** di sonno" (inferno 1:11),
    "**disïante** … di lui" (paradiso 5:86). Rule AZ accepts the same bare `obl` when the LLM
    names it as the secondary predicate it is; this is the case where the LLM lists it not at all,
    which is equally faithful to the line: a depictive adjective is an adjunct of the predication,
    not one of its arguments, and Layer 4's `obl` is the one deprel the tree has for it (rule AZ's
    own reasoning). The same acceptance rule AR makes for a comparison the tree could only hang on
    the main predicate.

    The three gates are rule AZ's, unchanged: **no `case` child**, so a real prepositional adjunct
    is not swept in; **adjective POS**, so an adverb or a nominal in the same slot stays flagged;
    **the predicate's own child** (through `aux`/`cop`, rule BP). Censused at 44 bare adjectival
    obliques corpus-wide, 11 of them standing `missing_arg` positions.
    """
    if drole != "obl" or arg in case_children:
        return False
    row = (dep_index_by_pos or {}).get(arg)
    if row is None or row.deprel != "obl" or not _hosts_child(pos, row, dep_index_by_pos):
        return False
    return "adjective" in (morph_pos_by_position or {}).get(arg, "").lower()


def _fused_clitic_dual_role(
    grole: str, drole: str, arg: tuple[int, int],
    morph_pos_by_position: dict[tuple[int, int], str] | None,
    case_by_position: "dict[tuple[int, int], str] | None" = None,
) -> bool:
    """Rule AL: a fused clitic cluster that genuinely fills two roles at once.

    "non *gliel* celai" (inferno 10:44) is `gli` + `lo` in one Layer-1 token — the dative and the
    accusative of one verb. The LLM lists both rows, as it should; Layer 4 has one deprel per
    token, so whichever row the derivation did not pick becomes a role_mismatch on a token that
    is not in dispute at all. The `double_listed` whitelist already accepts the `extra_arg` leg of
    this shape; this is the same acceptance for the role_mismatch leg.

    Gated on Layer 2 having tagged the token as two fused pronouns, and on the two roles being
    exactly the pair such a cluster encodes.

    **Rule CM** replaces "exactly that pair" with the annex itself. `gliel'` is not the only
    cluster the shape has: "in Siena **sen** pispiglia" (purgatorio 11:111) and "**sen** va"
    (paradiso 2:20) are `si` + `ne`, whose annex value is `reflexive+ablative`, and the two
    readings split those two slots between them — the derivation takes the reflexive half as the
    verb's object (rule AB's own gate lets a bare clitic carry `obj`/`iobj`/`obl:a`) and the LLM
    takes the ablative half as the oblique `ne` marks. Each side is corroborated by a *different*
    slot, which is what makes this the same non-dispute as `gliel'` rather than a role
    disagreement: censused at 13 fused positions with a role_mismatch, 7 of which split this way,
    and requiring the two supporting slot sets to differ is what keeps a fused position whose
    annex backs only one side (or the same slot on both) flagged.
    """
    if morph_pos_by_position is None:
        return False
    tag = morph_pos_by_position.get(arg, "").lower()
    if tag.count("pronoun") < 2:
        return False
    if {grole, drole} == {"obj", "obl:a"}:
        return True
    slots = [s for s in (case_by_position or {}).get(arg, "").split(SLOT_SEP) if s]
    if len(slots) < 2:
        return False

    def supported(role: str) -> set[str]:
        # `reflexive` is not in `_case_supports_role`'s mapping — it names the clitic's own
        # nature, not a slot — but rule AB already treats a reflexive clitic as able to fill the
        # roles a bare clitic carries, and this reads the same annex the same way.
        return {s for s in slots
                if _case_supports_role(s, role)
                or (s == "reflexive" and role in ("obj", "iobj", "obl:a"))}

    given_slots, derived_slots = supported(grole), supported(drole)
    return bool(given_slots) and bool(derived_slots) and given_slots != derived_slots


def _case_corroborated_role(
    grole: str, drole: str, arg: tuple[int, int],
    case_by_position: dict[tuple[int, int], str] | None,
    morph_pos_by_position: dict[tuple[int, int], str] | None,
) -> bool:
    """Rule U: a role_mismatch whose argument is a pronoun the Layer-2 `case` annex holds a value
    for, and that value corroborates the **derived** (dep-side) role while contradicting the given
    (LLM-side) one. Phase 5's closing position parked its largest reading-disagreement population
    because deciding it "needs a Layer-2 case feature"; `case/` is that feature, built afterwards
    and hand-audited against `dep` through the annex's Steps 6-9, so a third independent read is
    now available exactly where the clitic disputes live ("mi pesa" dative vs "m'avea 'mmonito"
    accusative are identical in form, and the tree shape does not separate them).

    Gated tightly, in the same one-directional shape as rules L/M/N/O: corroborating *both* sides
    (`obl:a` under `dative`, say) or *neither* accepts nothing, and the mirror direction — the
    annex siding with the LLM against `dep` — is never an automatic accept but a `dep`-correction
    candidate for hand review, the same asymmetry Phase 5j enforced when it rejected rule O's
    two-directional variant."""
    value = (case_by_position or {}).get(arg)
    if value is None or not _bare_pronoun_position(arg, morph_pos_by_position):
        return False
    return _case_supports_role(value, drole) and not _case_supports_role(value, grole)


def _case_corroborated_swap(
    grole: str, drole: str, arg: tuple[int, int],
    given_roles: dict[tuple[int, int], str], derived_roles: dict[tuple[int, int], str],
    case_by_position: dict[tuple[int, int], str] | None,
    morph_pos_by_position: dict[tuple[int, int], str] | None,
) -> bool:
    """Rule W: the swap partner of a rule-U accept.

    Rule U is scoped to the pronoun position the annex holds a value for. But a `subj`/`obj`
    disagreement is rarely about one argument: the LLM inverts *both* legs of a transitive
    clause at once, and only one leg is usually a pronoun. "lo passo **che** non lasciò già mai
    **persona viva**" (inferno 1:27) is the type — the annex reads `che` as `nominative`, rule U
    accepts that leg, and `persona`, a noun and so out of the annex's scope, stays flagged
    although it is the *same* decision reported a second time: if `che` is the subject, the
    argument the LLM also called subject cannot be one.

    Gated on a genuine two-argument inversion under one predicate — the partner's given and
    derived roles must be exactly this argument's, exchanged — and on rule U itself accepting
    that partner. Anything looser (any annex-contradicted argument anywhere under the predicate)
    would accept disagreements the annex never adjudicated, so the gate is the exchange, not
    mere co-presence. One-directional like rule U: the annex siding with the LLM accepts
    nothing."""
    if {grole, drole} != {"subj", "obj"}:
        return False
    for other, other_given in given_roles.items():
        if other == arg:
            continue
        other_derived = derived_roles.get(other)
        # the exact inversion: the partner carries this argument's two roles, exchanged
        if other_given != drole or other_derived != grole:
            continue
        if _case_corroborated_role(other_given, other_derived, other, case_by_position,
                                   morph_pos_by_position):
            return True
    return False


def _classify_divergence(
    given: dict[int, list[SkelRow]], derived: dict[int, list[SkelRow]],
    dep_index_by_pos: dict[tuple[int, int], DepRow] | None = None,
    morph_pos_by_position: dict[tuple[int, int], str] | None = None,
    case_by_position: dict[tuple[int, int], str] | None = None,
    morph_lemma_by_position: dict[tuple[int, int], str] | None = None,
    morph_rows: dict[int, list[MorphRow]] | None = None,
    np_rows: dict[int, list[NPSpan]] | None = None,
) -> list[Violation]:
    violations: list[Violation] = []
    # Rule BI's `obj` branch: Layer 2's tense column, which is where "infinitive" is recorded.
    morph_tense_by_position: dict[tuple[int, int], str] = {
        (no, i + 1): row.tense
        for no, rows in (morph_rows or {}).items() for i, row in enumerate(rows)
    }
    # Rule BT: Layer 2's `note` column, where `relative` / `interrogative` are recorded.
    morph_note_by_position: dict[tuple[int, int], str] = {
        (no, i + 1): row.note
        for no, rows in (morph_rows or {}).items() for i, row in enumerate(rows)
    }
    children_by_pos: dict[tuple[int, int], list[DepRow]] = {}
    for row in (dep_index_by_pos or {}).values():
        if not (row.head_line == 0 and row.head_token == 0):
            children_by_pos.setdefault((row.head_line, row.head_token), []).append(row)
    # Rules L and N: the preposition lemmas each position's `case` dep children name (empty set
    # = no explicit preposition, which is what rule L turns on).
    case_lemmas: dict[tuple[int, int], set[str]] = {}
    # Rule T: the same, widened to `mark` children — the preposition of an infinitive adverbial
    # clause ("per venir", "a descriver") is a `mark`, not a `case`.
    marker_lemmas: dict[tuple[int, int], set[str]] = {}
    for row in (dep_index_by_pos or {}).values():
        if row.deprel in ("case", "mark"):
            lemma = _normalize_prep_lemma(row.word.lower())
            marker_lemmas.setdefault((row.head_line, row.head_token), set()).add(lemma)
            if row.deprel == "case":
                case_lemmas.setdefault((row.head_line, row.head_token), set()).add(lemma)
    # A `fixed` token glued to a `case` row is a later member of a multiword preposition — the
    # dep/ normalization writes "in su la cima" as `in` case-> `cima` with `su` fixed-> `in` —
    # so it names a preposition of the same nominal the `case` row marks, exactly as it did
    # when Layer 4 still attached both members flat, and rules L/N/O keep reading it either way.
    for row in (dep_index_by_pos or {}).values():
        if row.deprel != "fixed":
            continue
        head = dep_index_by_pos.get((row.head_line, row.head_token))
        while head is not None and head.deprel == "fixed":
            head = dep_index_by_pos.get((head.head_line, head.head_token))
        if head is not None and head.deprel == "case":
            lemma = _normalize_prep_lemma(row.word.lower())
            marker_lemmas.setdefault((head.head_line, head.head_token), set()).add(lemma)
            case_lemmas.setdefault((head.head_line, head.head_token), set()).add(lemma)
    # `case_children` is rule L's gate — the positions for which `derive_unit` *could* have
    # emitted a lemma-qualified oblique — so it is taken before the cluster aggregation below,
    # which adds lemmas the derivation never reads.
    case_children = set(case_lemmas)
    # Rule BJ: an adverb-preposition cluster ("di là **da**", "fuor **di**", "innanzi **a**") is
    # one complex preposition, so the preposition marking the cluster's nominal marks the cluster
    # head too — the same aggregation the `fixed` loop above does for the multiword prepositions
    # Layer 4's normalization could reshape, applied to the 40 clusters it deliberately left
    # alone because Layer 2 calls their opening word an adverb. Rule O then reads either half of
    # the complex preposition as naming the one oblique.
    for arg in list(case_lemmas):
        head = _adverb_cluster_head(arg, dep_index_by_pos, children_by_pos, morph_pos_by_position)
        if head is not None:
            case_lemmas.setdefault(head, set()).update(case_lemmas[arg])
    # Rule Y: the positions Layer 4 attaches a `cop`/`aux`/`aux:pass` token to — the tree's own
    # assertion that a predication is headed there, whatever deprel the head itself carries.
    copula_hosts: set[tuple[int, int]] = {
        (row.head_line, row.head_token)
        for row in (dep_index_by_pos or {}).values()
        if row.deprel in _AUX_DEPRELS
    }
    given_preds = _predicate_positions_in(given)
    derived_preds = _predicate_positions_in(derived)

    # Double-listing: a predicate nominal/adjective the LLM lists both as another predicate's
    # attr/xcomp row and (redundantly) as its own predicate tuple — pure restatement, not a
    # divergence. Mirrors the ccomp/xcomp missing_arg suppression below, extended to attr.
    double_listed = {
        (r.arg_line, r.arg_token)
        for rows in given.values()
        for r in rows
        if r.role in ("attr", "xcomp") and (r.arg_line, r.arg_token) != (r.line, r.token)
    }
    # The same relation, kept directional — which predicate(s) each double-listed complement
    # was listed under. Rule X below needs the host, not just the fact of double-listing.
    complement_hosts: dict[tuple[int, int], set[tuple[int, int]]] = {}
    for rows in given.values():
        for r in rows:
            arg_pos = (r.arg_line, r.arg_token)
            if r.role in ("attr", "xcomp") and arg_pos != (r.line, r.token):
                complement_hosts.setdefault(arg_pos, set()).add((r.line, r.token))

    def _elided_copula_nominal(pos: tuple[int, int]) -> bool:
        # A predicate nominal coordinate/apposed to a real clause with no copula token at all
        # (e.g. "mantoani per patrïa ambedui") — derive_unit structurally can't produce this
        # (no verb, no clause-head deprel). Gated on deprel, not just "non-verb POS": most
        # non-verb extra_tuple predicates (amod/advmod/obj/nsubj/nmod) are NP-internal modifiers
        # the LLM wrongly promoted to predicate status, a genuine error, not an elided copula.
        if dep_index_by_pos is None or morph_pos_by_position is None:
            return False
        dep_row = dep_index_by_pos.get(pos)
        if dep_row is None or dep_row.deprel not in _ELIDED_COPULA_DEPRELS:
            return False
        pos_tag = morph_pos_by_position.get(pos, "")
        return not is_verb_pos(pos_tag)

    def _complemented_adjective_phrase(pos: tuple[int, int]) -> bool:
        # Rule AY: `_elided_copula_nominal`'s adjective-phrase sibling. That rule gates on the
        # deprel because most non-verb `extra_tuple` predicates are NP-internal modifiers the
        # LLM wrongly promoted; an `amod` adjective is exactly the shape it excludes. But an
        # adjective that governs an argument of its own is not a bare attributive — it is a
        # reduced relative, and it predicates: "una figura … **maravigliosa ad ogne cor sicuro**"
        # (inferno 16:132), "**piena di duolo** e di tormento rio" (9:111), "**sì fatta, che le
        # genti lì malvage** …" (paradiso 19:17). The complement child is the structural evidence
        # rule R and rule S both read off the same construction from the argument side; without
        # it ("le tre donne benedette") the promotion stays flagged.
        if dep_index_by_pos is None or morph_pos_by_position is None:
            return False
        dep_row = dep_index_by_pos.get(pos)
        if dep_row is None or dep_row.deprel != "amod":
            return False
        if "adjective" not in morph_pos_by_position.get(pos, "").lower():
            return False
        return any(c.deprel in _ADJECTIVE_COMPLEMENT_DEPRELS
                   for c in children_by_pos.get(pos, ()))

    def _aux_of_derived_predicate(pos: tuple[int, int]) -> bool:
        # The LLM names the auxiliary/modal/copula as the predicate ("Molti *son* li animali",
        # "se tu *vorrai* salire") where derive_unit, following UD, names the lexical head it
        # attaches to — a labeling-convention split, and the head is nearly always listed by the
        # LLM as well, so this is the same double-listing as the attr/xcomp case above. Gated on
        # the head being a *derived* predicate: if it isn't, the reading is a genuine divergence.
        if dep_index_by_pos is None:
            return False
        head = _aux_head(pos, dep_index_by_pos)
        return head != pos and head in derived_preds

    def _aux_named_predicate(arg: tuple[int, int]) -> bool:
        # Rule CY: `_aux_of_derived_predicate` read from the derivation's end — one of the LLM's
        # own predicates is an `aux`/`cop` of `arg`, so the clause headed at `arg` is listed
        # after all, under the auxiliary. See the clausal-complement double-listing skip.
        if dep_index_by_pos is None:
            return False
        return any(p != arg and _aux_head(p, dep_index_by_pos) == arg for p in given_preds)

    def _predicate_complements(pos: tuple[int, int]) -> set[tuple[int, int]]:
        # Rule X's scope gate: the tokens that are `pos`'s predicate complement on **both**
        # readings — the LLM lists them as its `attr`/`xcomp`, and Layer 4 attaches them to it
        # with an `attr`/`xcomp` deprel. Requiring both sides is what keeps the rule from
        # accepting an arbitrary relocation of an argument between two predicates: the two
        # layers must already agree that these two tokens form one predication.
        if dep_index_by_pos is None:
            return set()
        out = set()
        for complement, hosts in complement_hosts.items():
            if pos not in hosts:
                continue
            dep_row = dep_index_by_pos.get(complement)
            if dep_row is None or dep_row.deprel not in ("attr", "xcomp"):
                continue
            if (dep_row.head_line, dep_row.head_token) == pos:
                out.add(complement)
        return out

    def _complement_hosted_argument(
        pos: tuple[int, int], arg: tuple[int, int], role: str,
        rows_by_pred: dict[tuple[int, int], list[SkelRow]],
        hosts: "set[tuple[int, int]] | None" = None,
    ) -> bool:
        # Rule X: the argument side of the copula convention the two rules above already accept
        # on the tuple side. The corpus's frozen style makes the **copula** the clause head and
        # the predicate nominal/adjective its `attr`/`xcomp`, so Layer 4 hangs the clause's
        # obliques on the copula: "color che **son** contenti / **nel foco**" (inferno 1:118),
        # "a costor si vuole **esser** cortese" (inferno 16:15). The LLM follows UD and hangs
        # them on the complement instead. `double_listed` and `_aux_of_derived_predicate`
        # already accept exactly this split on the tuple side; the argument side was still
        # being reported — and, where derive_unit promotes the complement too, reported
        # **twice**, as a `missing_arg` on the copula plus an `extra_arg` on the complement.
        # Both legs call this, so one convention costs nothing instead of two violations.
        #
        # The role must match. The LLM relocating the argument *and* relabelling it is two
        # claims and only the relocation is a convention, so `obl:su` against `obl:in`, or
        # `subj` against `obl`, stays flagged.
        for complement in (hosts if hosts is not None else _predicate_complements(pos)):
            for row in rows_by_pred.get(complement, ()):
                if (row.arg_line, row.arg_token) == arg and _canonicalize_role(row.role) == role:
                    return True
        return False

    def _control_partners(pos: tuple[int, int]) -> set[tuple[int, int]]:
        # Rule AX: the predicates joined to `pos` by an `xcomp` edge, either direction. A
        # control/modal periphrasis is one predication spread over two tokens — "come i Roman
        # **per l'essercito molto** … **hanno a passar** la gente" (inferno 18:30), where Layer 4
        # hangs the oblique on the finite `hanno` and the LLM on the infinitive `passar` — so
        # which of the two carries a shared adjunct is a placement convention, not a reading.
        # This is rule X's mechanism (`_complement_hosted_argument`) pointed at the `xcomp` edge
        # instead of the copula's `attr`/`xcomp` complement edge, with the same role-must-match
        # gate: relocating the argument is the convention, relabelling it is a second claim.
        # `ccomp` is deliberately excluded — a finite complement clause has its own arguments,
        # and sharing them across that edge would accept genuine mis-attachments.
        if dep_index_by_pos is None:
            return set()
        partners: set[tuple[int, int]] = set()
        row = dep_index_by_pos.get(pos)
        if row is not None and row.deprel == "xcomp":
            partners.add((row.head_line, row.head_token))
        for child in children_by_pos.get(pos, ()):
            if child.deprel == "xcomp":
                partners.add((child.line, child.token))
        return partners - {pos}

    def _free_relative_head(
        pos: tuple[int, int], arg: tuple[int, int], role: str,
        derived_roles: dict[tuple[int, int], str],
    ) -> bool:
        # Rule AE: a free relative, cited from its two ends. Layer 4 attaches the *clause's verb*
        # in the matrix role ("Galeotto fu 'l libro e **chi lo scrisse**": `scrisse` is `fu`'s
        # second `nsubj`), and the LLM cites the pronoun that heads it — which is also what the
        # prompt's relative-pronoun rule tells it to do. Both name the same constituent, in the
        # same role, so this is a citation convention, not a disagreement about the parse.
        # Gated on the pronoun being that very clause's subject and on the roles matching:
        # citing a pronoun from an *unrelated* clause, or in another role, stays flagged.
        if dep_index_by_pos is None:
            return False
        if "pronoun" not in (morph_pos_by_position or {}).get(arg, "").lower():
            return False
        row = dep_index_by_pos.get(arg)
        if row is None or row.deprel not in _SUBJ_DEPRELS:
            return False
        clause = (row.head_line, row.head_token)
        return clause != pos and derived_roles.get(clause) == role

    def _free_relative_matrix_head(pos: tuple[int, int], arg: tuple[int, int]) -> bool:
        # Rule BT: rule AE's other end. In an embedded question Layer 4 hangs the clause **under**
        # the interrogative pronoun — "se vuoi saper **chi son cotesti due**" (inferno 32:55) has
        # `chi` as `saper`'s `attr` and `son` as `acl:relcl` on `chi` — so the pronoun that fills
        # the embedded clause's own predicate-complement slot is, in the tree, that clause's
        # governor. `derive_unit` reads the edge downwards and never gives `son` an `attr`; the
        # LLM reads the question and does. Rule AE accepts the same constituent cited from the
        # matrix side; this is the embedded side.
        #
        # The gate is the free-relative census, not the deprel alone: 765 predicates corpus-wide
        # are `acl:relcl` under a pronoun, but nearly all are ordinary correlatives ("colui **che**
        # vede"), where the antecedent is emphatically *not* an argument of the relative clause and
        # the relative pronoun inside it is. The discriminator is that second pronoun: when the
        # clause holds none, the word it hangs under is the only thing that can fill the slot.
        # Requiring the head to be a bare `chi`/`che`/`quale` with no determiner of its own, and
        # the clause to hold no relative pronoun, leaves 92 — which covers the embedded question
        # (32:55) and the free relative proper ("**chi** … quello amor si spoglia", paradiso
        # 15:12) alike, and, because Layer 2 flags `relative` unevenly, a plain relative whose
        # pronoun Layer 4 left outside the clause too (paradiso 6:6).
        if dep_index_by_pos is None:
            return False
        row = dep_index_by_pos.get(pos)
        if row is None or row.deprel != "acl:relcl":
            return False
        if (row.head_line, row.head_token) != arg:
            return False
        if "pronoun" not in (morph_pos_by_position or {}).get(arg, "").lower():
            return False
        if (morph_lemma_by_position or {}).get(arg, "").lower() not in ("chi", "che", "quale"):
            return False
        if "relative" in morph_note_by_position.get(arg, "").lower():
            return False
        kids = children_by_pos.get(arg, ())
        if any(k.deprel in ("det", "amod") for k in kids):
            return False
        return not any(
            "relative" in morph_note_by_position.get((k.line, k.token), "").lower()
            for k in children_by_pos.get(pos, ())
        )

    def _copula_under_its_complement(
        pos: tuple[int, int], arg: tuple[int, int], role: str
    ) -> bool:
        # Rule CT: a copula Layer 4 hung **under** its own predicate complement. The corpus makes
        # the complement the head of a copular clause and the copula its `cop` child, and where
        # the copula carries its own clause deprel instead — "quant' **esser può** … di nuvol
        # **tenebrata**" (purgatorio 16:3), the degree clause of the adjective it predicates —
        # `derive_unit` reads the edge downwards and gives `esser` nothing but a pro-drop
        # subject, while the LLM reads the predication and names the adjective as its `attr`.
        # This is rule BT's shape (`arg` is the predicate's own governor) with the copular
        # convention in place of the free relative, and rule Y's evidence read from the other
        # side: there the `cop` edge says a predication is headed at the complement, here the
        # copular *lemma* says the same of an edge Layer 4 wrote as a clause.
        #
        # Censused at 21 `essere` clauses under an adjective head and 4 under a noun, against 294
        # `advcl` verbs under a nominal head in all — the lemma is what separates the predication
        # from an ordinary adverbial clause modifying a nominal.
        if dep_index_by_pos is None:
            return False
        if role != "xcomp":  # `attr` is canonicalized to `xcomp` beforehand
            return False
        if (morph_lemma_by_position or {}).get(pos, "").lower() != "essere":
            return False
        row = dep_index_by_pos.get(pos)
        if row is None or row.deprel not in CLAUSE_HEAD_DEPRELS:
            return False
        if (row.head_line, row.head_token) != arg:
            return False
        return _is_nominal_pos((morph_pos_by_position or {}).get(arg, ""))

    def _copular_adverb_complement(
        pos: tuple[int, int], arg: tuple[int, int], role: str
    ) -> bool:
        # Rule AD: rule R's shape with an **adverb** complement. Rule R deliberately stopped at
        # adjectives because an adverb attached `advmod` leaves the reading undecided in general
        # — but not under `essere`, which needs a complement to predicate anything at all: "che
        # l'ubidir, se già fosse, **m'è tardi**" (inferno 2:80), "m'è **uopo**". The copula lemma
        # is the whole gate; the same adverb under a lexical verb ("va **superbo**" is rule R's
        # job, "corre **tosto**" is a genuine adjunct) is untouched.
        if dep_index_by_pos is None or role != "xcomp":
            return False
        if (morph_lemma_by_position or {}).get(pos, "").lower() != "essere":
            return False
        row = dep_index_by_pos.get(arg)
        if row is None or row.deprel != "advmod" or not _hosts_child(pos, row, dep_index_by_pos):
            return False
        return "adverb" in (morph_pos_by_position or {}).get(arg, "").lower()

    def _relative_adverb_oblique(
        pos: tuple[int, int], arg: tuple[int, int], grole: str
    ) -> bool:
        # Rule DD: the relative locative adverb Layer 4 writes as a `case` on its own clause.
        # "questo mondo / **dove** poter peccar non è più nostro" (purgatorio 26:132): `dove` is
        # tagged `case` with the clause's finite verb as its head. `case` is not an argument
        # deprel, so `derive_unit` says nothing about it at all, while the LLM reads the word
        # for what it means — the clause's locative adjunct. This is rule BM's shape (an adjunct
        # whose filler Layer 2 calls something other than a nominal) and rule CK's (the LLM
        # naming a clause by the word that opens it), on the one word that is both.
        #
        # Censused corpus-wide: **21** `dove`/`ove`/`u'` rows carry `case`, and every one of
        # them attaches to a verb — so this is a Layer-4 convention applied consistently, not a
        # mis-tag to correct upstream. Gated to that: Layer 2 must call the word an adverb, the
        # head must be this predicate, and the role must be an oblique.
        if dep_index_by_pos is None:
            return False
        if grole != "obl" and not OBL_RE.fullmatch(grole):
            return False
        row = dep_index_by_pos.get(arg)
        if row is None or row.deprel != "case":
            return False
        if (row.head_line, row.head_token) != pos:
            return False
        return "adverb" in (morph_pos_by_position or {}).get(arg, "").lower()

    def _prepositional_copular_complement(
        pos: tuple[int, int], grole: str, drole: str, arg: tuple[int, int]
    ) -> bool:
        # Rule DB: rule AD's mismatch leg. Rule AD accepts the LLM calling a copula's adverb
        # complement `xcomp` where Layer 4 wrote `advmod` — the derivation says nothing about an
        # `advmod`, so its silence is not a denial. When the same adverb carries a preposition
        # ("a tutti altri sapori **esto è di sopra**", purgatorio 28:133) Layer 4 writes `obl`
        # instead, the derivation *does* name it, and the identical reading is reported as a
        # role_mismatch rather than a `missing_arg`. The gate is rule AD's, plus the one thing
        # that makes the prepositional case decidable at all: the copula must have no other
        # complement. `essere` with a predicate complement already in hand ("è pien d'amore")
        # takes prepositional phrases as ordinary adjuncts, and those stay flagged; `essere`
        # with none is predicating *this* phrase or nothing.
        if dep_index_by_pos is None or grole != "xcomp" or not drole.startswith("obl"):
            return False
        if (morph_lemma_by_position or {}).get(pos, "").lower() != "essere":
            return False
        if "adverb" not in (morph_pos_by_position or {}).get(arg, "").lower():
            return False
        row = dep_index_by_pos.get(arg)
        if row is None or row.deprel != "obl" or not _hosts_child(pos, row, dep_index_by_pos):
            return False
        return not any(_canonicalize_role(r.role) == "xcomp"
                       and (r.arg_line, r.arg_token) != arg
                       for r in derived_by_pred.get(pos, []))

    def _reflexive_clitic_argument(
        pos: tuple[int, int], arg: tuple[int, int], role: str
    ) -> bool:
        # Rule AB: the reflexive clitic. The multiple-`obj` round (2026-08-03) normalized every
        # reflexive `mi`/`ti`/`si`/`ci`/`vi` onto UD's `expl`, which is outside `ARG_DEPRELS`, so
        # `derive_unit` says nothing at all about the clitic — while the LLM reads the very same
        # token as the verb's object or dative ("tal **mi** fec' ïo", inferno 2:40). UD's `expl`
        # is a labeling convention for a clitic that is still the verb's argument in the reading
        # sense, so the derivation's silence is not a denial.
        #
        # Two gates keep it narrow: the role must be one a bare clitic can carry (`obj`, `iobj`,
        # `obl:a` — the accusative/dative pair the `case` annex's own vocabulary allows it), so
        # naming a preposition the tree does not carry (`obl:di`, `obl:in`) stays flagged; and
        # the cited token must be a Layer-2 pronoun.
        #
        # Rule AS widens the role gate for a **fused** clitic only. "poi **sen** van giù per
        # questa stretta doccia" (inferno 14:117) is `si` + `ne` in one Layer-1 token, and Layer
        # 4 can only give the token one deprel, so `expl` covers the reflexive half and the
        # ablative `ne` disappears. The `case` annex records both halves (`reflexive+ablative`),
        # and that second slot is the independent signal that licenses the oblique role — the
        # same evidence rule AL uses for the `role_mismatch` leg of a fused cluster.
        if dep_index_by_pos is None:
            return False
        row = dep_index_by_pos.get(arg)
        if row is None or row.deprel != "expl":
            return False
        if not _hosts_child(pos, row, dep_index_by_pos):
            return False
        if "pronoun" not in (morph_pos_by_position or {}).get(arg, "").lower():
            return False
        if role in ("obj", "iobj", "obl:a"):
            return True
        slots = [s for s in (case_by_position or {}).get(arg, "").split(SLOT_SEP) if s]
        return len(slots) > 1 and any(_case_supports_role(s, role) for s in slots)

    def _pronominal_verb_clitic(
        pos: tuple[int, int], arg: tuple[int, int], role: str
    ) -> bool:
        # Rule AW: rule AB's mirror leg. Layer 4 does not label the reflexive clitic
        # consistently — the 2026-08-03 round normalized most of them onto UD's `expl`, but 371
        # tokens carrying the `case` annex's `reflexive` still stand as `obj`/`iobj`, and the
        # split between the two follows nothing visible. Where the tree happens to say `obj`,
        # `derive_unit` asserts an object the LLM (reading "si partiro", "s'atterga", "si puose"
        # as the pronominal verbs they are) does not list; where it says `expl`, rule AB already
        # accepts the opposite silence. Both directions are the same labeling convention, so
        # they get the same treatment.
        #
        # Gated exactly as rule AB: the annex must call the token reflexive, Layer 2 must call
        # it a pronoun, it must be this predicate's own child, and the disputed role must be one
        # a bare clitic can carry — naming a preposition the tree does not carry stays flagged.
        #
        # **Rule BD** adds the third deprel the same split uses: 35 reflexive clitics stand as
        # `obl` ("Se l'ira sovra 'l mal voler **s'**aggueffa", inferno 23:16; "El **si** fuggì",
        # 25:16), where `derive_unit` asserts an oblique the pronominal reading has no room for.
        # `obl` joins the accepted roles on both sides for the same reason `obj` and `iobj` are
        # there — the clitic is part of the verb, and which slot the tree parked it in is
        # notation, not a claim.
        if dep_index_by_pos is None or role not in ("obj", "iobj", "obl", "obl:a"):
            return False
        row = dep_index_by_pos.get(arg)
        if row is None or row.deprel not in ("obj", "iobj", "obl"):
            return False
        if not _hosts_child(pos, row, dep_index_by_pos):
            return False
        if "pronoun" not in (morph_pos_by_position or {}).get(arg, "").lower():
            return False
        slots = [s for s in (case_by_position or {}).get(arg, "").split(SLOT_SEP) if s]
        return "reflexive" in slots

    def _secondary_predicate_over_argument(
        pos: tuple[int, int], arg: tuple[int, int], role: str,
        derived_args: set[tuple[int, int]],
    ) -> bool:
        # **Rule CI** decides *which* position the host gate reads. "ma vidi bene e l'uno e
        # l'altro **mosso**" (purgatorio 8:105): the participle hangs on `l'altro`, the second
        # conjunct of the object, and `derive_unit` reads only the coordination head, so the
        # host was not in `derived_args` and the small clause went unrecognised on a coordinate
        # object. Rule C's collapse is the corpus's own answer to which position a coordination
        # is cited by, and it already runs over the citations this gate compares against; rule
        # BP's finding, that a gate must read the same edge the derivation normalized, applied
        # to rule AA's host test.
        #
        # Rule AA: the perception/depictive small clause. "Queste parole ... vid' ïo **scritte**"
        # (inferno 3:11) — Layer 4 attaches the participle as an `acl` of the object noun, which
        # is outside `ARG_DEPRELS`, so `derive_unit` cannot report it as an argument of the
        # matrix verb at all; the LLM reads the same edge as the verb's clausal complement. Rule
        # D accepts exactly this shape one relation over (an `nmod` off a derived argument, read
        # as an oblique); this is its clausal counterpart.
        #
        # Gated on the `acl`'s host being one of *this* predicate's own derived arguments, so a
        # participle modifying some unrelated nominal is not swept in with it.
        #
        # Rule AU is the same shape one POS over: an **adjective** Layer 4 attached `amod` to one
        # of this predicate's own derived arguments, read as the predication's secondary
        # predicate — "che innanzi a buon segnor fa **servo forte**" (inferno 17:90), "ch'i' ho
        # **le cose conte**" (21:62), "e fia **la tua imagine leggera**" (purgatorio 17:7). UD's
        # `amod` is outside `ARG_DEPRELS`, so `derive_unit` is silent about the adjective
        # altogether; the LLM reads the object/subject complement the line actually asserts.
        # Rule R accepts the same complement when Layer 4 hangs it on the *predicate* as
        # `advmod`; this is the leg where it hangs on the argument instead. The three gates —
        # adjective POS, `xcomp` role, host is a derived argument of this same predicate — are
        # what keep an ordinary attributive adjective inside some other phrase out.
        if dep_index_by_pos is None:
            return False

        # Rule DC: *which* position the host gate reads, a second time — rule CI asked it of
        # rule C's coordination collapse, this asks it of rule CE's relative-pronoun identity.
        # Inside a relative clause the derived argument is the pronoun `che`, and the adjective
        # hangs on the antecedent it stands for: "come ninfe **che** si givan **sole**"
        # (purgatorio 29:4) — `sole` is `amod` on `ninfe`, `givan`'s derived subject is `che`,
        # and the two are one referent, so the host gate was failing on a distinction the corpus
        # already decided elsewhere. Gated on this predicate actually heading that pronoun's
        # relative clause, so an adjective on some other nominal is still out.
        antecedent: tuple[int, int] | None = None
        prow = dep_index_by_pos.get(pos)
        if (prow is not None and prow.deprel in ("acl", "acl:relcl")
                and any((row_ := dep_index_by_pos.get(a)) is not None
                        and row_.deprel in _SUBJ_DEPRELS or row_.deprel == "obj"
                        and (row_.head_line, row_.head_token) == pos
                        and row_.word.lower().rstrip("'") in ("che", "ch", "cui", "chi")
                        for a in derived_args)):
            antecedent = (prow.head_line, prow.head_token)

        def _hosted_by_derived_argument(r: DepRow) -> bool:
            host = (r.head_line, r.head_token)
            return (host in derived_args
                    or _coordination_head(host, dep_index_by_pos) in derived_args
                    or host == antecedent)

        row = dep_index_by_pos.get(arg)
        if row is None:
            return False
        if row.deprel in ("amod", "advmod"):
            if role != "xcomp":  # `attr` is canonicalized to `xcomp` before comparison
                return False
            if "adjective" not in (morph_pos_by_position or {}).get(arg, "").lower():
                return False
            return _hosted_by_derived_argument(row)
        if role not in ("xcomp", "ccomp"):
            return False
        if row.deprel not in ("acl", "acl:relcl"):
            return False
        return _hosted_by_derived_argument(row)

    def _copular_hosts(pos: tuple[int, int]) -> set[tuple[int, int]]:
        # Rule X's other leg, looking the other way: the predicates `pos` is the complement of.
        # Same both-readings gate as `_predicate_complements`.
        if dep_index_by_pos is None:
            return set()
        dep_row = dep_index_by_pos.get(pos)
        if dep_row is None or dep_row.deprel not in ("attr", "xcomp"):
            return set()
        head = (dep_row.head_line, dep_row.head_token)
        return {head} if head in complement_hosts.get(pos, ()) else set()

    def _auxiliary_hosts(pos: tuple[int, int]) -> set[tuple[int, int]]:
        # Rule BY: the `aux`/`cop` words of this predicate's own periphrasis. "quel da Esti **il
        # fé far**" (purgatorio 5:77): Layer 4 heads the causative on `far` and makes the finite
        # `fé` its `aux`, and the LLM — seeing a finite verb and an infinitive — writes *two*
        # tuples, putting the subject on the finite word and the object on the infinitive.
        # `derive_unit` puts both on `far` (rule AM collects what the auxiliary strands), so the
        # subject is reported missing from a tuple the LLM did supply, one row further up.
        #
        # Rule AQ merges an argument *citation* that lands on an auxiliary onto its lexical head,
        # and rules AV/BS accept the *predicate* citation when the LLM names only the auxiliary.
        # This is the third combination — the LLM names both and splits the arguments between
        # them — routed through rule X's mechanism, so it inherits that rule's role-must-match
        # gate: relocating an argument onto the finite word of one periphrasis is a convention,
        # relabelling it is a second claim and stays flagged. The auxiliary's own tuple is
        # already accepted as a double-listing by `_aux_of_derived_predicate`.
        if dep_index_by_pos is None:
            return set()
        return {(c.line, c.token) for c in children_by_pos.get(pos, ())
                if c.deprel in _AUX_DEPRELS} - {pos}

    def _named_by_its_auxiliary(pos: tuple[int, int]) -> bool:
        # Rule AV: `_aux_of_derived_predicate`'s missing leg. That rule accepts the LLM naming an
        # `aux`/`cop` as the predicate *when it also names the lexical head* — the double-listing
        # case. When it names only the auxiliary ("che spezzate **averien** ritorte e strambe",
        # inferno 19:27, where the LLM's tuple sits on `averien` and Layer 4's lexical head is
        # the participle `spezzate`), the same labeling-convention split is reported twice: once
        # as an unaccepted `extra_tuple` — no, that leg is already accepted — and once here, as a
        # derived predicate "not proposed", although the LLM proposed exactly this predication
        # under the other convention. Rule AQ makes the identical move for an *argument*
        # citation landing on an `aux`/`cop`; this is its predicate-position twin.
        if dep_index_by_pos is None:
            return False
        return any(
            _aux_head(g, dep_index_by_pos) == pos
            for g in given_preds
            if (dep_index_by_pos.get(g) or DepRow(0, 0, "", "", 0, 0)).deprel in _AUX_DEPRELS
        )

    # Rule CS: a derived predicate whose tuple is **empty** asserts nothing, so the LLM's not
    # proposing it is not a divergence. `derive_unit` writes a role-less `=(0, 0)` row for a
    # position it promoted and then found no argument for — the elliptical answer "**Nullo**,
    # però che 'l pastor … rugumar può" (purgatorio 16:98), whose verb is gapped from the
    # question it answers in the previous parse unit, and where nothing left in the line can
    # fill a slot. Rules AN, BN and CA already refuse to *mint* this shape on the `conj` and
    # gapped-remnant branches, each on the same ground — "a tuple with no arguments in it, which
    # no reading of the line can supply". Extending that refusal to the clause-head branch by
    # POS was measured at **+180** and rejected: a non-verb clause head with no argument child
    # is overwhelmingly a copular or controlled predicate whose only subject comes from rule V,
    # and the LLM proposes those correctly. Reading the derived *tuple* instead of the deprel
    # separates the two exactly.
    empty_derived = {
        (row.line, row.token)
        for rows in derived.values()
        for row in rows
        if row.token > 0 and not row.role
    }
    for line, token in sorted(derived_preds - given_preds):
        if (line, token) in empty_derived:
            continue
        if _named_by_its_auxiliary((line, token)):
            continue
        violations.append(Violation(line, "tag", f"missing_tuple: predicate {line}.{token} not proposed",
                                     predicate=(line, token)))
    def _copular_predication(pos: tuple[int, int]) -> bool:
        # Rule Y: a copular clause head Layer 4 hung under a nominal deprel. "Caccianli i ciel
        # per non esser men **belli**" (inferno 3:40) — the tree gives `belli` a `cop` child
        # (`esser`) and a `case` child (`per`) and then attaches the whole thing as `obl`, which
        # is not in `CLAUSE_HEAD_DEPRELS`, so `derive_unit` never proposes the predication even
        # though Layer 4's own `cop` edge asserts one. `_elided_copula_nominal` is the same
        # acceptance for the case where there is **no** copula token at all; this is the case
        # where there is one, and the copula edge itself is the evidence, so no deprel gate on
        # the host is needed.
        #
        # **Rule BS** reads the `cop` edge from the other end. "e cortesia fu lui **esser
        # villano**" (inferno 33:150): the predication is `lui esser villano`, and the LLM names
        # it by the copula `esser` — the same labeling convention `_aux_of_derived_predicate`
        # accepts, except that there the head is a derived predicate and here it is exactly the
        # nominal rule Y was written for. Testing the citation through `_aux_head` first is rule
        # BP's normalization applied to a tuple-side gate.
        if pos in copula_hosts:
            return True
        return (dep_index_by_pos is not None
                and _aux_head(pos, dep_index_by_pos) in copula_hosts)

    def _verb_in_argument_slot(pos: tuple[int, int]) -> bool:
        # Rule Z: a verb form Layer 4 put in an argument or adjunct slot. "ch'i' fui **per
        # ritornar** più volte vòlto" (inferno 1:36) — `ritornar` is an `obl` with `per` as its
        # `case` child, where UD would write `mark` + `advcl`; "ove **tornar** disio" has the
        # infinitive as an `nsubj`. Either way Layer 2 calls the token a verb and both readings
        # agree it heads a predication: the derivation is silent because of where the token sits
        # in the tree, not because it denies the predicate. The mirror leg, at the `missing_arg`
        # branch below, accepts the same split from the host's side — the derivation reports the
        # infinitive as its oblique/subject while the LLM gives it a tuple of its own, one
        # decision that was being reported twice.
        if dep_index_by_pos is None or morph_pos_by_position is None:
            return False
        row = dep_index_by_pos.get(pos)
        if row is None or row.deprel not in _NOMINAL_SLOT_DEPRELS:
            return False
        return is_verb_pos(morph_pos_by_position.get(pos, ""))

    def _verb_in_adnominal_slot(pos: tuple[int, int]) -> bool:
        # Rule CH: rule Z's adnominal leg. A verb Layer 4 attached as `amod`/`acl` over a nominal
        # is a reduced relative clause — "come fogliette pur mo **nate**" (purgatorio 8:28),
        # "l'ombra ... **volta**" (14:70) — and the derivation reads it as a predicate whenever
        # pass 2 can find it, that is whenever it has an argument child of its own ("che da verdi
        # penne / **percosse** traean dietro", 8:30, derived from its `obl:da`). A participle
        # with no argument but its subject is the identical reading with nothing for pass 2 to
        # catch it by, so the derivation is silent about the tuple, not opposed to it — rule Z's
        # own reasoning, one deprel family over. Rule V's `acl` branch already accepts the
        # subject such a tuple carries, so this closes the tuple side of a predication the
        # checker was otherwise half-accepting. Conjuncts of one are the same clause coordinated
        # ("**e ventilate**", 8:30), and rule BZ's finiteness gate deliberately leaves them
        # underived.
        if dep_index_by_pos is None or morph_pos_by_position is None:
            return False
        row = dep_index_by_pos.get(pos)
        seen = {pos}
        while row is not None and row.deprel == "conj":
            head = (row.head_line, row.head_token)
            if head in seen:
                return False
            seen.add(head)
            row = dep_index_by_pos.get(head)
        if row is None or row.deprel not in ("amod", "acl", "acl:relcl"):
            return False
        return (is_verb_pos(morph_pos_by_position.get(pos, ""))
                and is_verb_pos(morph_pos_by_position.get((row.line, row.token), "")))

    for line, token in sorted(given_preds - derived_preds):
        pos = (line, token)
        if (pos in double_listed or _elided_copula_nominal(pos)
                or _aux_of_derived_predicate(pos) or _copular_predication(pos)
                or _verb_in_argument_slot(pos) or _complemented_adjective_phrase(pos)
                or _verb_in_adnominal_slot(pos)):
            continue
        violations.append(Violation(line, "tag", f"extra_tuple: predicate {line}.{token} not derived",
                                     predicate=(line, token)))

    given_by_pred: dict[tuple[int, int], list[SkelRow]] = {}
    for rows in given.values():
        for row in rows:
            if row.token > 0:
                given_by_pred.setdefault((row.line, row.token), []).append(row)
    derived_by_pred: dict[tuple[int, int], list[SkelRow]] = {}
    for rows in derived.values():
        for row in rows:
            derived_by_pred.setdefault((row.line, row.token), []).append(row)

    for pos in sorted(given_preds & derived_preds):
        line, token = pos

        def by_arg(rows: list[SkelRow]) -> dict[tuple[int, int], str]:
            return {
                (r.arg_line, r.arg_token): _canonicalize_role(r.role)
                for r in rows
                if r.role and (r.arg_line, r.arg_token) != pos
            }

        g = by_arg(given_by_pred.get(pos, []))
        d = by_arg(derived_by_pred.get(pos, []))
        if dep_index_by_pos is not None:
            _apply_subj_authority(g, d, pos, derived_by_pred, dep_index_by_pos, given_by_pred,
                                  morph_rows, children_by_pos, np_rows)
            derived_args = set(d)
            g = _merge_auxiliary_citations(g, pos, dep_index_by_pos)
            g = {
                (_prep_stack_nominal(a, dep_index_by_pos) if a != (0, 0) else a): r
                for a, r in g.items()
            }  # rule BV: a `fixed`/`case` word of a multiword preposition names its nominal
            g = _merge_adverb_cluster_citations(g, pos, dep_index_by_pos, children_by_pos,
                                                morph_pos_by_position)
            g = _collapse_coordination(g, pos, dep_index_by_pos, morph_pos_by_position)
            d = _collapse_coordination(d, pos, dep_index_by_pos, morph_pos_by_position)
            # Rule BO: rule AI runs **before** rule D. Both fire on a given citation the
            # derivation does not carry, and rule D is the weaker answer of the two: it drops the
            # citation as an accepted `nmod` adjunct, which silences the `extra_arg` half of the
            # pair and leaves the derivation's own position reported as a `missing_arg`. When the
            # two positions are one Layer-3 noun phrase named twice ("torreggiavan **di mezza la
            # persona**", inferno 31:43 — Layer 4 heads the oblique on `mezza` and hangs `persona`
            # under it as `nmod`, Layer 3 heads the span on `persona`), rule AI re-keys the
            # citation onto the derived position and both halves go quiet. The 21-25 batch's
            # ordering finding in a third form: two rules that are each correct alone, in the
            # order that loses one of them.
            if np_rows is not None:
                _merge_np_head_citations(g, d, np_rows)
            _drop_nmod_obliques(g, d, derived_args, dep_index_by_pos)
        for arg, drole in sorted(d.items()):
            grole = g.get(arg)
            if grole is None:
                if drole in ("ccomp", "xcomp") and (arg in given_preds
                                                    or _aux_named_predicate(arg)):
                    # Clausal-complement double-listing: the LLM lists the clause as its own
                    # tuple instead of also citing it as this predicate's argument.
                    #
                    # **Rule CY** decides which *edge* that test reads. "«Come!», diss' elli …
                    # chi v'**ha** per la sua scala tanto **scorte**?" (purgatorio 21:21): Layer 4
                    # heads the quoted question on `scorte` with `ha` as its `aux`, and the LLM
                    # gives the clause a tuple headed by `ha` — so the clause *is* double-listed,
                    # under the auxiliary. `_aux_of_derived_predicate` already reads this very
                    # convention in the other direction, and rules AQ and BP already normalize
                    # `aux`/`cop` to the lexical word for the citation gates; this test was the
                    # one left comparing raw positions. Censused at 1 position corpus-wide — the
                    # double-listing skip above already takes 655 of the 656 uncited clausal
                    # complements — so it is kept for consistency between the two directions of
                    # one gate rather than for its count.
                    continue
                if arg in given_preds and _verb_in_argument_slot(arg):
                    # Rule Z, host leg: the derivation reports the infinitive as this
                    # predicate's argument, the LLM gives it a tuple of its own — the same
                    # double-listing the ccomp/xcomp skip above already accepts.
                    continue
                if _complement_hosted_argument(pos, arg, drole, given_by_pred):
                    continue  # rule X: the LLM hung it on this predicate's own complement
                if _comparative_come_adjunct(pos, arg, drole, dep_index_by_pos, children_by_pos,
                                             morph_pos_by_position):
                    continue  # rule AR: a verbless comparative clause's nominal
                if _conjunction_oblique(arg, drole, morph_pos_by_position):
                    continue  # rule BM: a connective Layer 4 parked in an adjunct slot
                if _pronominal_verb_clitic(pos, arg, drole):
                    continue  # rule AW: rule AB's mirror leg
                if _nested_in_named_phrase(arg, g, d, np_rows):
                    continue  # rule BR: the LLM named the phrase once, by its Layer-3 head
                if _depictive_bare_oblique_omitted(pos, arg, drole, dep_index_by_pos,
                                                   morph_pos_by_position, case_children):
                    continue  # rule BX: rule AZ's missing_arg leg
                if _undecided_subject_slot(drole, arg, g, d):
                    continue  # rule BA: the derivation offered two subjects and named neither
                if _gapped_second_term_argument(arg, d):
                    continue  # rule CW: rule BA's oblique leg — the elided clause's own argument
                if _complement_hosted_argument(pos, arg, drole, given_by_pred,
                                               hosts=_control_partners(pos)):
                    continue  # rule AX: the LLM hung it on the other end of an `xcomp` edge
                if _complement_hosted_argument(pos, arg, drole, given_by_pred,
                                               hosts=_auxiliary_hosts(pos)):
                    continue  # rule BY: the LLM hung it on this predicate's own `aux`/`cop`
                if _clause_named_by_marker(pos, arg, drole, dep_index_by_pos, g):
                    continue  # rule CK: the LLM named this clause by its complementizer
                violations.append(Violation(line, "tag", f"missing_arg: {line}.{token} {drole} {arg}",
                                             role=drole, arg=arg, predicate=pos))
            elif grole != drole:
                if (_oblique_lemma_refinement(grole, drole, arg, case_children)
                        or _predicative_complement(grole, drole)
                        or _case_marked_object(grole, drole, arg, case_lemmas)
                        or _co_present_preposition(grole, drole, arg, case_lemmas)
                        or _clausal_complement_flavor(grole, drole)
                        or _clausal_object(grole, drole, arg, morph_pos_by_position)
                        or _case_corroborated_role(grole, drole, arg, case_by_position,
                                                   morph_pos_by_position)
                        or _case_corroborated_swap(grole, drole, arg, g, d, case_by_position,
                                                   morph_pos_by_position)
                        or _comparative_come_complement(grole, drole, arg, dep_index_by_pos,
                                                        morph_pos_by_position)
                        or _fused_clitic_dual_role(grole, drole, arg, morph_pos_by_position,
                                                   case_by_position)
                        or _depictive_bare_oblique(grole, drole, pos, arg, dep_index_by_pos,
                                                   morph_pos_by_position, case_children)
                        or _marked_complement_clause(pos, grole, drole, arg, dep_index_by_pos,
                                                     marker_lemmas)
                        # rule BD's mismatch leg: both readings park the same reflexive clitic in
                        # a slot a bare clitic can carry, and disagree only about which
                        or (_pronominal_verb_clitic(pos, arg, grole)
                            and _pronominal_verb_clitic(pos, arg, drole))
                        # rule DB: rule AD's mismatch leg
                        or _prepositional_copular_complement(pos, grole, drole, arg)):
                    continue
                violations.append(
                    Violation(line, "tag", f"role_mismatch: {line}.{token} arg {arg} {grole!r} vs {drole!r}",
                              role=drole, given_role=grole, arg=arg, predicate=pos)
                )
        for arg, grole in sorted(g.items()):
            if arg not in d:
                if dep_index_by_pos is not None and (
                    _adverbial_oblique(pos, arg, grole, dep_index_by_pos, morph_pos_by_position)
                    or _predicative_advmod(pos, arg, grole, dep_index_by_pos,
                                           morph_pos_by_position)
                    or _nmod_complement_of_predicate(pos, arg, grole, dep_index_by_pos,
                                                     case_lemmas)
                    or _marked_adverbial_clause(pos, arg, grole, dep_index_by_pos,
                                                marker_lemmas)
                    or _secondary_predicate_over_argument(pos, arg, grole, derived_args)
                    or _displaced_subject_pro_drop(grole, arg, g, d)
                    or _accusative_and_infinitive(pos, arg, grole, dep_index_by_pos,
                                                  morph_tense_by_position)
                    or _inverted_copula_complement(pos, arg, grole, dep_index_by_pos,
                                                   morph_pos_by_position)
                    or _reflexive_clitic_argument(pos, arg, grole)
                    or _copular_adverb_complement(pos, arg, grole)
                    or _free_relative_head(pos, arg, grole, d)
                    or _free_relative_matrix_head(pos, arg)  # rule BT: rule AE's embedded side
                    or _copula_under_its_complement(pos, arg, grole)  # rule CT
                    or _marker_slot_argument(pos, arg, grole, dep_index_by_pos,
                                             morph_pos_by_position)  # rule BW: rule BM's mirror
                    or _conj_shared_argument(pos, arg, grole, dep_index_by_pos,
                                             derived_by_pred, d)
                    # rule X, mirror leg: derive_unit hung it on the copula this predicate
                    # is the complement of
                    or _complement_hosted_argument(pos, arg, grole, derived_by_pred,
                                                   hosts=_copular_hosts(pos))
                    # rule AX, mirror leg: derive_unit hung it on the other end of an `xcomp`
                    or _complement_hosted_argument(pos, arg, grole, derived_by_pred,
                                                   hosts=_control_partners(pos))
                    # rule CG: an elided coordinate oblique, citable only by its modifier
                    or _gapped_coordinate_oblique(pos, arg, grole, dep_index_by_pos,
                                                  children_by_pos, d)
                    # rule CC: rule CA's argument leg — a coordinate nominal UD promoted to
                    # `conj` on this predicate, which the derivation gives no slot at all
                    or _promoted_conjunct_argument(pos, arg, dep_index_by_pos, children_by_pos,
                                                   morph_pos_by_position)
                    # rule CB: the tree hangs it on a predicative complement of `pos` that the
                    # derivation never promotes, so the argument has one home in each reading
                    or _stranded_on_underived_complement(pos, arg, grole, dep_index_by_pos,
                                                         derived_preds, case_lemmas)
                    # rule CK: this is the `mark` of a clause the derivation gives the same slot
                    or _marker_of_derived_clause(pos, arg, grole, dep_index_by_pos, d)
                    # rule CX: rule CK widened — the interrogative word that opens the clause
                    or _wh_word_of_derived_clause(pos, arg, grole, dep_index_by_pos,
                                                  morph_pos_by_position, children_by_pos, d)
                    # Rule DA: rule CS's argument leg. CS reads a role-less `=(0, 0)` derived
                    # row as asserting nothing, so the LLM's *not* proposing that predicate is
                    # no divergence; the same empty tuple equally cannot contradict an argument
                    # the LLM does propose on it — "Poco parer potea lì **del di fori**"
                    # (purgatorio 27:88), where `parer`'s own tuple is empty and the LLM gives
                    # it the partitive its infinitive plainly governs.
                    #
                    # **Except in the subject slot**, which is the whole point of the boundary.
                    # An empty tuple is not the derivation having no opinion there: rule V is a
                    # decision procedure that walks the control chain for exactly this slot, and
                    # rules BB, CF and CJ each widened what it may collect. When it leaves the
                    # slot empty it has *declined*, and accepting any subject the LLM offers
                    # would undo that decision — the five near-miss tests of the rule-V family
                    # (`tests/test_skel.py`, rules BB/CF/CI/CJ) fail the moment this gate is
                    # opened to `subj`, which is how the boundary was found. No comparable
                    # procedure runs for the other roles, where an empty tuple means only that
                    # Layer 4 gave the predicate no argument child. 17 positions, against the
                    # 23 the unrestricted form took.
                    or (grole != "subj" and pos in empty_derived)
                    # rule DD: the relative locative adverb Layer 4 writes as a `case`
                    or _relative_adverb_oblique(pos, arg, grole)
                ):
                    continue
                violations.append(Violation(line, "tag", f"extra_arg: {line}.{token} {grole} {arg}",
                                             role=grole, arg=arg, predicate=pos))
    return violations


@dataclass(frozen=True)
class Repair:
    """One mechanical rewrite: `before` (the committed row) replaced by `after`.

    `kind` names the rule that produced it — see `_find_repairs` for the catalogue and for what
    each rule is allowed to assume.
    """

    kind: str
    predicate: tuple[int, int]
    before: SkelRow
    after: SkelRow


def _safe_role_repair(given_role: str, derived_role: str) -> bool:
    """Only a bare `obl` -> `obl:<lemma>` refinement is dep-tree-explicit (derive_unit only
    emits the lemma-qualified form when a `case` child makes the preposition explicit); every
    other role_mismatch pair surviving Phase 1/2 normalization (subj/obj, iobj/obj, cross-lemma
    obl pairs) is a genuine disagreement, left for Phase 4."""
    return given_role == "obl" and bool(OBL_RE.fullmatch(derived_role))


def _case_child_lemmas(
    dep_index_by_pos: dict[tuple[int, int], DepRow] | None,
) -> dict[tuple[int, int], set[tuple[tuple[int, int], str]]]:
    """`case` children per head, as (position, normalized lemma) — the input both preposition
    rules read. Keyed by *any* head, not only argument positions, because a stacked preposition
    hangs off the inner preposition rather than off the nominal. A `fixed` child of a `case`
    row — the dep/ normalization's later member of a multiword preposition, "in su la cima"
    as `in` case-> `cima` with `su` fixed-> `in` — is collected under its `case` row, so the
    transitive walk in `_stacked_prep_lemmas` still reaches every member of the stack."""
    out: dict[tuple[int, int], set[tuple[tuple[int, int], str]]] = {}
    for row in (dep_index_by_pos or {}).values():
        if row.deprel == "case":
            out.setdefault((row.head_line, row.head_token), set()).add(
                ((row.line, row.token), _normalize_prep_lemma(row.word.lower())))
        elif row.deprel == "fixed":
            head = dep_index_by_pos.get((row.head_line, row.head_token))
            if head is not None and head.deprel == "case":
                out.setdefault((head.line, head.token), set()).add(
                    ((row.line, row.token), _normalize_prep_lemma(row.word.lower())))
    return out


def _stacked_prep_lemmas(
    arg: tuple[int, int],
    case_kids: dict[tuple[int, int], set[tuple[tuple[int, int], str]]],
) -> set[str]:
    """Every preposition lemma reachable from `arg` by walking `case` children transitively.

    "in su la favola" is chained in Layer 4 — `in` is a `case` child of `su`, and only `su` is a
    `case` child of the nominal — so the flat lemma set names one preposition of the stack and
    this walk names them all. See `_prep_stack_label`.
    """
    out: set[str] = set()
    seen: set[tuple[int, int]] = set()
    frontier = list(case_kids.get(arg, ()))
    while frontier:
        token, lemma = frontier.pop()
        if token in seen:
            continue
        seen.add(token)
        out.add(lemma)
        frontier.extend(case_kids.get(token, ()))
    return out


def _prep_stack_label(
    given_role: str, derived_role: str, arg: tuple[int, int],
    case_kids: dict[tuple[int, int], set[tuple[tuple[int, int], str]]],
) -> bool:
    """Whether an `obl:X` vs `obl:Y` mismatch is the two readings naming *different prepositions
    of one stack* rather than disagreeing about the relation.

    "ch'i' fui **in su** la cima" (inferno 21:65): Layer 4 chains `in` -> `su` -> `cima`, so
    `derive_unit` reports the preposition adjacent to the nominal (`obl:su`) while the LLM names
    the one that opens the phrase (`obl:in`). Both describe the same PP, so this is a notation
    convention with no reading asserted — and the convention the corpus already fixed is the
    derived side's (`_PREP_LEMMA_NORM`'s docstring normalizes the `inver'` family onto the
    derivation's `in` for exactly this reason).

    Gated on **both** lemmas being in the same stack. When the LLM names a preposition the tree
    does not carry at all (18 positions, mostly `in su` written flat by Layer 4), the tree and
    the reading genuinely differ about what is attached, and that is the `dep/` normalization
    round PLAN.md reserves — not something to rewrite here.
    """
    if not (given_role.startswith("obl:") and derived_role.startswith("obl:")):
        return False
    stack = _stacked_prep_lemmas(arg, case_kids)
    return (given_role.split(":", 1)[1] in stack
            and derived_role.split(":", 1)[1] in stack)


def _find_repairs(
    given: dict[int, list[SkelRow]], derived: dict[int, list[SkelRow]],
    violations: list[Violation],
    morph_rows: dict[int, list[MorphRow]] | None = None,
    dep_rows: dict[int, "list[DepRow] | tuple[DepRow, ...]"] | None = None,
) -> list[Repair]:
    """Mechanical rewrite candidates, sourced purely from `_classify_divergence`'s own violation
    list (already passed through Phase 2's `_apply_subj_authority` when `dep_index_by_pos` was
    given) — does not recompute the given/derived diff independently.

    The rules divide into two tiers, and the division is the point. **Tier A asserts no
    reading**: it rewrites a label the two sides spell differently while meaning the same thing,
    so it is safe wherever it fires. **Tier B does assert a reading**, and may only do so where a
    signal *independent of Layer 4* corroborates it — because a Layer-5 divergence is evidence
    that Layer 4 might be the wrong side (see the module docstring), so "the derivation says so"
    is not on its own a reason to rewrite the artifact. PLAN.md records the concrete
    counter-example: the ungated `null_subject` rule asserted Layer 4 was right at exactly the
    positions the subject-agreement round later found Layer 4 could be wrong.

    Tier A — `role_label` (bare `obl` -> `obl:<lemma>`), `prep_stack` (one preposition of a
    stack named instead of another).

    Tier B — `null_subject` (the LLM's pro-drop ∅ resolved to the derived subject), corroborated
    by Layer 2 person/number agreement via `dep.subject_agreement`.
    """
    by_pred: dict[tuple[int, int], list[Violation]] = {}
    for v in violations:
        if v.predicate is not None:
            by_pred.setdefault(v.predicate, []).append(v)

    dep_index_by_pos = dep_index(dep_rows) if dep_rows is not None else None
    case_kids = _case_child_lemmas(dep_index_by_pos)
    dep_children: dict[tuple[int, int], list[DepRow]] = {}
    for row in (dep_index_by_pos or {}).values():
        dep_children.setdefault((row.head_line, row.head_token), []).append(row)

    def find_row(pos: tuple[int, int], role: str, arg: tuple[int, int]) -> SkelRow | None:
        # Compare canonicalized: `_classify_divergence` reports the *canonical* role, while the
        # committed row may hold any spelling that canonicalizes onto it (`obl:nel` -> `obl:in`).
        for row in given.get(pos[0], ()):
            if ((row.line, row.token) == pos and _canonicalize_role(row.role) == role
                    and (row.arg_line, row.arg_token) == arg):
                return row
        return None

    repairs: list[Repair] = []
    for pos, vs in by_pred.items():
        missing_subj = [v for v in vs if v.detail.startswith("missing_arg") and v.role == "subj"]
        extra_null_subj = [
            v for v in vs
            if v.detail.startswith("extra_arg") and v.role == "subj" and v.arg == (0, 0)
        ]
        if len(missing_subj) == 1 and len(extra_null_subj) == 1:
            subj = missing_subj[0].arg
            verdict, _ = subject_agreement(subj, pos, morph_rows, dep_children)
            # Tier B: only an *agreeing* pair is repaired. "disagree" means the two frozen layers
            # contradict each other and the derived subject is as likely to be the wrong side;
            # "undecidable" means nothing may be concluded. Both stay flagged for the LLM.
            if verdict == "agree":
                before = find_row(pos, "subj", (0, 0))
                if before is not None:
                    after = dataclasses.replace(before, arg_line=subj[0], arg_token=subj[1])
                    repairs.append(Repair("null_subject", pos, before, after))

        for v in vs:
            if not (v.detail.startswith("role_mismatch") and v.given_role is not None
                    and v.role is not None and v.arg is not None):
                continue
            if _safe_role_repair(v.given_role, v.role):
                kind = "role_label"
            elif _prep_stack_label(v.given_role, v.role, v.arg, case_kids):
                kind = "prep_stack"
            else:
                continue
            before = find_row(pos, v.given_role, v.arg)
            if before is not None:
                repairs.append(Repair(kind, pos, before, dataclasses.replace(before, role=v.role)))
    return repairs


def validate_unit(
    nos: list[int],
    texts: list[str],
    rows_by_line: dict[int, list[SkelRow]],
    morph_rows: dict[int, list[MorphRow]] | None = None,
    np_rows: dict[int, list[NPSpan]] | None = None,
    dep_rows: dict[int, list[DepRow]] | None = None,
    case_rows: dict[int, list[CaseRow]] | None = None,
) -> list[Violation]:
    """Check `rows_by_line` for one parse unit.

    Hard checks (structural bar; kinds `position`/`word`/`dup`/`clausal`/`sentinel`): predicate
    and argument positions are in-unit token positions (or the `(0, 0)` sentinel, valid only
    for a `subj` pro-drop row or a zero-argument-predicate row); the predicate word matches its
    token; no duplicate `(pred, role, arg)` row and no argument citing its own predicate
    position; a `ccomp`/`xcomp` argument must itself be a predicate token within the unit; a
    `token == 0` sentinel row may not coexist with real predicate rows on the same line.

    Soft checks (kind `tag`; measure-then-freeze): a role outside the frozen vocabulary;
    a nominal-role (`subj`/`obj`/`iobj`/`obl*`) argument that heads no Layer-3 NP, is not a
    Layer-2 pronoun or relative-pronoun word form (`che`/`ch'`/`cui`/`qual`/`quale`/`chi`,
    regardless of the frozen Layer-2 POS tag — `morph/CORRECTIONS.md` documents that "che" is
    tagged inconsistently between `pronoun` and `conjunction` even in its relative use), is not
    an adverb heading an `obl`/`obl:*` argument (an adverbial oblique like `quivi`/`là`/`sù` has
    no NP to cite), is not itself an in-unit predicate, and — rule AF, when `dep_rows` is also
    supplied — is not a position Layer 4 itself fills an argument slot with (only when *both*
    `morph_rows` and `np_rows` are supplied); and — the core of this layer's design — every divergence from
    `derive_unit`
    (only when `dep_rows`/`morph_rows` supplied): `missing_tuple`, `extra_tuple`, `missing_arg`,
    `extra_arg`, `role_mismatch`. `case_rows` (the Layer-2 `case` annex, optional) feeds rule U,
    which accepts a `role_mismatch` whose argument's frozen case value corroborates the derived
    role alone; `np_rows` additionally feeds rule AI, which pairs a `missing_arg` and an
    `extra_arg` naming one Layer-3 NP by its head and by Layer 4's attachment point. See module
    docstring and PLAN.md.
    """
    violations: list[Violation] = []
    token_lists = {no: _alpha_tokens(t) for no, t in zip(nos, texts)}
    valid_positions = {(no, i + 1) for no in nos for i in range(len(token_lists[no]))}

    all_rows = [row for no in nos for row in rows_by_line.get(no, [])]

    for no in nos:
        line_tokens = token_lists[no]
        rows = rows_by_line.get(no, [])
        for row in rows:
            if row.token == 0:
                if any(r.token > 0 for r in rows):
                    violations.append(Violation(no, "sentinel", "sentinel row coexists with predicate rows"))
                continue
            if 1 <= row.token <= len(line_tokens):
                token = line_tokens[row.token - 1]
                if row.word != token and strip_word_punct(row.word, token) is None:
                    violations.append(Violation(no, "word", f"{row.word!r} != token {token!r}"))
            else:
                violations.append(Violation(no, "position", f"predicate token {row.token} out of range"))

    seen_rows: set[tuple[int, int, str, int, int]] = set()
    for row in all_rows:
        if row.token == 0:
            continue
        pos = (row.line, row.token)
        arg = (row.arg_line, row.arg_token)
        key = (row.line, row.token, row.role, row.arg_line, row.arg_token)
        if key in seen_rows:
            violations.append(Violation(row.line, "dup", f"duplicate row {key}"))
        seen_rows.add(key)
        if arg == pos:
            violations.append(Violation(row.line, "dup", f"argument cites its own predicate {pos}"))
        if arg == (0, 0):
            if row.role not in ("subj", ""):
                violations.append(Violation(row.line, "position", f"role {row.role!r} may not use (0,0)"))
        elif arg not in valid_positions:
            violations.append(Violation(row.line, "position", f"argument {arg} not in unit"))

    predicate_positions = _predicate_positions_in(rows_by_line)
    for row in all_rows:
        if row.token > 0 and row.role in ("ccomp", "xcomp"):
            arg = (row.arg_line, row.arg_token)
            if arg not in predicate_positions:
                violations.append(
                    Violation(row.line, "clausal", f"{row.role} argument {arg} is not a predicate in this unit")
                )

    for row in all_rows:
        if row.token > 0 and not _role_valid(row.role):
            violations.append(Violation(row.line, "tag", f"role {row.role!r} not in frozen vocabulary"))

    if morph_rows is not None and np_rows is not None:
        pronoun_positions = {
            (no, i + 1)
            for no, rows in morph_rows.items()
            for i, r in enumerate(rows)
            if "pronoun" in r.pos.lower() or r.word.lower() in _REL_PRONOUN_WORDS
        }
        adverb_obl_positions = {
            (no, i + 1)
            for no, rows in morph_rows.items()
            for i, r in enumerate(rows)
            if "adverb" in r.pos.lower()
        }
        np_head_positions = {(no, s.head) for no, spans in np_rows.items() for s in spans}
        # Rule AF: positions Layer 4 itself attaches with an argument deprel. The membership
        # check asks whether a cited argument is a *nominal* — it tests Layer 3's NP heads and
        # Layer 2's pronouns, and its 47-strong residue was substantivized adjectives ("ch'io
        # v'ebbi **alcun** riconosciuto", inferno 3:58), quoted mention words, and adverbs cited
        # as objects. Layer 4 attaching that same token as an `nsubj`/`obj`/`iobj`/`obl` is the
        # corpus's own answer: a token the dependency parse fills an argument slot with is
        # admissible as a Layer-5 argument whatever its POS, so the check no longer needs Layer 3
        # to have drawn an NP around it. A citation *nothing* corroborates still fails.
        dep_argument_positions = {
            (r.line, r.token)
            for rows in (dep_rows or {}).values() for r in rows
            if r.deprel in ARG_DEPRELS
        }
        for row in all_rows:
            if row.token == 0 or row.role in ("", "attr", "xcomp", "ccomp"):
                continue
            arg = (row.arg_line, row.arg_token)
            if arg == (0, 0) or arg == (row.line, row.token):
                continue
            if arg in np_head_positions or arg in pronoun_positions or arg in predicate_positions:
                continue
            if (row.role == "obl" or row.role.startswith("obl:")) and arg in adverb_obl_positions:
                continue
            if arg in dep_argument_positions:
                continue
            # Rule AQ, applied where the citation is still raw: an argument named by the
            # `cop`/`aux` carrying its tense names the lexical head Layer 4 hung it on
            # ("vorrebbe di vedere **esser** digiuno", inferno 28:87). The divergence check
            # merges exactly this edge with `_merge_auxiliary_citations`; the membership check
            # runs before that merge and was reporting the un-normalized position.
            aux_head = _aux_head(arg, dep_index(dep_rows) if dep_rows else {})
            if aux_head != arg and (aux_head in np_head_positions or aux_head in pronoun_positions
                                    or aux_head in predicate_positions
                                    or aux_head in dep_argument_positions):
                continue
            violations.append(
                Violation(row.line, "tag", f"argument {arg} for role {row.role} heads no NP/pronoun/predicate")
            )

    if dep_rows is not None and morph_rows is not None:
        derived = derive_unit(nos, dep_rows, morph_rows, case_rows)
        morph_pos_by_position = {
            (no, i + 1): row.pos for no, rows in morph_rows.items() for i, row in enumerate(rows)
        }
        case_by_position = (
            {(row.line, row.token): row.case for rows in case_rows.values() for row in rows}
            if case_rows is not None else None
        )
        morph_lemma_by_position = {
            (no, i + 1): row.lemma for no, rows in morph_rows.items() for i, row in enumerate(rows)
        }
        violations.extend(_classify_divergence(
            rows_by_line, derived, dep_index(dep_rows), morph_pos_by_position, case_by_position,
            morph_lemma_by_position, morph_rows, np_rows,
        ))

    return violations


# --- Serve-time joins (Layer 3 <-> Layer 5, Layer 4 <-> Layer 5) --------------------


def _iter_np(spans: tuple[NPSpan, ...]):
    for span in spans:
        yield span
        yield from _iter_np(span.children)


def np_head_index(spans: tuple[NPSpan, ...]) -> dict[tuple[int, int], NPSpan]:
    """(line, head) -> the widest Layer-3 NP headed there, over the whole nested forest."""
    idx: dict[tuple[int, int], NPSpan] = {}
    for span in _iter_np(spans):
        key = (span.line, span.head)
        current = idx.get(key)
        if current is None or (span.end - span.start) > (current.end - current.start):
            idx[key] = span
    return idx


def morph_index(data: dict[int, tuple[MorphRow, ...]]) -> dict[tuple[int, int], MorphRow]:
    return {(no, i + 1): row for no, rows in data.items() for i, row in enumerate(rows)}


def arg_np(arg: SkelArg, idx: dict[tuple[int, int], NPSpan]) -> NPSpan | None:
    """The maximal Layer-3 NP headed at `arg`'s position, or None. Derived, never stored."""
    return idx.get((arg.line, arg.token))


def antecedent(pred: SkelTuple, idx: dict[tuple[int, int], DepRow]) -> tuple[int, int] | None:
    """A relative-clause predicate's antecedent: the `acl:relcl` head position, or None.

    Mirrors `dep`'s "antecedents are derived, never stored" policy — the skeleton stores the
    relative pronoun itself as `subj`; this resolves what it refers to at serve time."""
    row = idx.get((pred.line, pred.token))
    if row is not None and row.deprel == "acl:relcl":
        return (row.head_line, row.head_token)
    return None


def children_index(data: dict[int, tuple[DepRow, ...]]) -> dict[tuple[int, int], list[DepRow]]:
    idx: dict[tuple[int, int], list[DepRow]] = {}
    for rows in data.values():
        for row in rows:
            if not (row.head_line == 0 and row.head_token == 0):
                idx.setdefault((row.head_line, row.head_token), []).append(row)
    return idx


def pro_drop_features(
    pred: SkelTuple,
    morph_idx: dict[tuple[int, int], MorphRow],
    children_idx: dict[tuple[int, int], list[DepRow]],
) -> str:
    """Person/number of a pro-drop ∅ subject, from the predicate's own morphology or its
    finite aux/cop child. Not stored — recoverable from Layer 2 + Layer 4 at serve time.

    `children_idx` is `_children_index(canto.dep())` — a (line, token) -> child-DepRows map,
    the same shape `derive_unit` builds internally, exposed here for serve-time reuse."""
    own = morph_idx.get((pred.line, pred.token))
    if own and own.person:
        return " ".join(f for f in (own.person, own.number) if f)
    for child in children_idx.get((pred.line, pred.token), ()):
        if child.deprel in _AUX_DEPRELS:
            cm = morph_idx.get((child.line, child.token))
            if cm and cm.person:
                return " ".join(f for f in (cm.person, cm.number) if f)
    return ""


# --- Artifact I/O --------------------------------------------------------------------

# Tab-separated: one row per (predicate, argument) pair, plus a `token == 0` sentinel row for
# a line with no predicates at all (np's `start == 0` precedent) — a zero-argument predicate
# is instead a single row with an empty `role` and arg `(0, 0)` (token > 0 distinguishes it
# from the sentinel).
_TSV_HEADER = ("line", "token", "word", "role", "arg_line", "arg_token")


def _artifact_path(canticle: str, number: int) -> Path:
    return SKEL_DIR / canticle / f"{number:02d}.tsv"


artifact_path = _artifact_path


def write_skel(canticle: str, number: int, lines: list[tuple[int, list[SkelRow]]]) -> Path:
    path = _artifact_path(canticle, number)
    path.parent.mkdir(parents=True, exist_ok=True)
    out = ["\t".join(_TSV_HEADER)]
    for no, rows in lines:
        if not rows:
            out.append("\t".join((str(no), "0", "", "", "0", "0")))
            continue
        for row in sorted(rows, key=_row_sort_key):
            out.append(
                "\t".join((str(no), str(row.token), row.word, row.role,
                           str(row.arg_line), str(row.arg_token)))
            )
    path.write_text("\n".join(out) + "\n", encoding="utf-8")
    return path


def has_skel(canticle: str, number: int) -> bool:
    return _artifact_path(canticle, number).exists()


def load_skel(canticle: str, number: int) -> dict[int, tuple[SkelRow, ...]]:
    """Load a frozen skeleton artifact: line-number -> SkelRows (no model call). A `token == 0`
    row is the sentinel (processed, no predicates) and is not returned as data."""
    path = _artifact_path(canticle, number)
    if not path.exists():
        raise FileNotFoundError(path)
    grouped: dict[int, list[SkelRow]] = {}
    for lineno, text in enumerate(path.read_text(encoding="utf-8").splitlines()):
        if lineno == 0 or not text:  # header / blank
            continue
        cells = text.split("\t")
        cells += [""] * (len(_TSV_HEADER) - len(cells))  # tolerate dropped trailing blanks
        no = int(cells[0])
        token = int(cells[1])
        bucket = grouped.setdefault(no, [])
        if token == 0:  # sentinel: processed, no predicates
            continue
        bucket.append(
            SkelRow(line=no, token=token, word=cells[2], role=cells[3],
                    arg_line=int(cells[4]), arg_token=int(cells[5]))
        )
    return {no: tuple(rows) for no, rows in grouped.items()}


def tuples_canto(canticle: str, number: int) -> tuple[SkelTuple, ...]:
    """Serve a canto's skeleton as grouped, identified tuples, ordered by (line, token)."""
    data = load_skel(canticle, number)
    result: list[SkelTuple] = []
    for no in sorted(data):
        by_token: dict[int, list[SkelRow]] = {}
        for row in data[no]:
            by_token.setdefault(row.token, []).append(row)
        for i, token in enumerate(sorted(by_token), start=1):
            group = by_token[token]
            args = tuple(
                SkelArg(role=r.role, line=r.arg_line, token=r.arg_token)
                for r in sorted(group, key=_row_sort_key)
                if r.role
            )
            result.append(SkelTuple(line=no, token=token, word=group[0].word,
                                     skel_id=f"{no}.{i}", args=args))
    return tuple(result)
