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
from .dep import DepRow, index as dep_index
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
) -> dict[int, list[SkelRow]]:
    """Mechanically derive the expected skeleton for one parse unit from Layers 2 and 4.

    This is the *checker*, not the artifact's author (see module docstring): its output is
    compared against the LLM's rows by `validate_unit`'s divergence check, never written to
    the artifact itself.
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

    # 1. clause-head predicates, plus conj chains that resolve to one.
    predicate_positions: set[tuple[int, int]] = {
        (row.line, row.token) for row in all_rows if row.deprel in CLAUSE_HEAD_DEPRELS
    }

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

    for row in all_rows:
        pos = (row.line, row.token)
        if row.deprel == "conj" and pos not in predicate_positions and conj_resolves(row, set()):
            # A coordinating conjunction is a function word, never a predicate: Layer 4 routinely
            # attaches a line-initial "E"/"Ed"/"Ma" to the previous clause head with deprel `conj`
            # ("E 'l mio buon duca, che già li er' al petto"), which this rule would otherwise
            # promote. Gapped/elided predicates of other POS stay promoted — those are real.
            conj_morph = morph_at(row.line, row.token)
            if conj_morph is not None and "conjunction" in conj_morph.pos.lower():
                continue
            predicate_positions.add(pos)

    # 2. argument-bearing non-auxiliary verbs.
    for row in all_rows:
        pos = (row.line, row.token)
        if pos in predicate_positions:
            continue
        morph = morph_at(row.line, row.token)
        if morph is None or "verb" not in morph.pos.lower() or row.deprel in _AUX_DEPRELS:
            continue
        if any(c.deprel in ARG_DEPRELS for c in children.get(pos, ())):
            predicate_positions.add(pos)

    result: dict[int, list[SkelRow]] = {no: [] for no in nos}
    for line, token in predicate_positions:
        pred_row = index[(line, token)]
        pred_args: list[SkelRow] = []
        has_subj = False
        for child in children.get((line, token), ()):
            if child.deprel in _SUBJ_DEPRELS:
                pred_args.append(SkelRow(line, token, pred_row.word, "subj", child.line, child.token))
                has_subj = True
            elif child.deprel in _DIRECT_ROLE_MAP:
                role = _DIRECT_ROLE_MAP[child.deprel]
                pred_args.append(SkelRow(line, token, pred_row.word, role, child.line, child.token))
            elif child.deprel in ("obl", "obl:agent"):
                case_children = sorted(
                    (c for c in children.get((child.line, child.token), ()) if c.deprel == "case"),
                    key=lambda c: c.token,
                )
                role = "obl"
                if case_children:
                    prep_morph = morph_at(case_children[0].line, case_children[0].token)
                    lemma = _prep_lemma(prep_morph) if prep_morph else ""
                    if lemma:
                        role = f"obl:{_normalize_prep_lemma(lemma)}"
                pred_args.append(SkelRow(line, token, pred_row.word, role, child.line, child.token))

        # 3. conj shared-subject propagation: inherit the nearest conj-ancestor's subject.
        if not has_subj and pred_row.deprel == "conj":
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


def _apply_subj_authority(
    g: dict[tuple[int, int], str], d: dict[tuple[int, int], str],
    pos: tuple[int, int], derived_by_pred: dict[tuple[int, int], list[SkelRow]],
    dep_index_by_pos: dict[tuple[int, int], DepRow],
) -> None:
    """Mutate `g`/`d` in place: drop the subj arg where PLAN.md's authority model makes the slot
    LLM-authoritative (validated against a candidate set) rather than derive-authoritative (exact
    match, the default `by_arg` diff already handles).
    """
    d_subj = _subj_arg(d)
    if d_subj == (0, 0):
        # Pro-drop antecedent: derive_unit only knows ∅; any concrete subject the LLM resolves is
        # strictly more informative, not wrong.
        g_subj = _subj_arg(g)
        if g_subj is not None:
            g.pop(g_subj, None)
        d.pop((0, 0), None)
    elif d_subj is None:
        # derive_unit asserted no subject at all: non-finite ∅, or an xcomp/ccomp control subject
        # inherited from the matrix predicate's subj/obj.
        g_subj = _subj_arg(g)
        if g_subj is None:
            return
        candidates = {(0, 0)}
        dep_row = dep_index_by_pos.get(pos)
        if dep_row is not None and dep_row.deprel in ("xcomp", "ccomp"):
            matrix_pos = (dep_row.head_line, dep_row.head_token)
            for row in derived_by_pred.get(matrix_pos, ()):
                if row.role in ("subj", "obj"):
                    candidates.add((row.arg_line, row.arg_token))
        if g_subj in candidates:
            g.pop(g_subj, None)


_ELIDED_COPULA_DEPRELS = frozenset({"conj", "appos", "attr"})

# --- Divergence-check normalization (Phase 5, PLAN.md) --------------------------------
#
# Two further equivalences of the same shape as the Phase 1 ones above — notation conventions,
# not parse disagreements. Measured over all 100 cantos before being frozen (PLAN.md Phase 5a).

_CONJ_WALK_LIMIT = 8


def _coordination_head(
    pos: tuple[int, int], dep_index_by_pos: dict[tuple[int, int], DepRow]
) -> tuple[int, int]:
    """Rule C: the head of `pos`'s coordination, walking `conj` edges up (bounded)."""
    seen = {pos}
    cur = pos
    for _ in range(_CONJ_WALK_LIMIT):
        row = dep_index_by_pos.get(cur)
        if row is None or row.deprel != "conj":
            break
        head = (row.head_line, row.head_token)
        if head in seen or head not in dep_index_by_pos:
            break
        seen.add(head)
        cur = head
    return cur


def _collapse_coordination(
    by_arg: dict[tuple[int, int], str], pos: tuple[int, int],
    dep_index_by_pos: dict[tuple[int, int], DepRow],
) -> dict[tuple[int, int], str]:
    """Rule C: map every argument citation onto its coordination head, de-duplicating.

    "si ciberà di terra e di sapïenza" — the LLM lists both conjuncts as `obj`, `derive_unit`
    reads only the predicate's direct children and so sees the first only. Enumerating conjuncts
    on the derived side instead was measured net-zero (PLAN.md Rule A): the LLM's own enumeration
    is inconsistent, so the divergence is a notation mismatch and normalization is the
    instrument. Roles are preserved, so a genuine role disagreement still surfaces.
    """
    out: dict[tuple[int, int], str] = {}
    for arg, role in by_arg.items():
        key = arg
        if arg != (0, 0):
            head = _coordination_head(arg, dep_index_by_pos)
            if head != pos:  # never collapse an argument onto its own predicate
                key = head
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


def _adverbial_oblique(
    pos: tuple[int, int], arg: tuple[int, int], role: str,
    dep_index_by_pos: dict[tuple[int, int], DepRow],
    morph_pos_by_position: dict[tuple[int, int], str] | None,
) -> bool:
    """Rule J: a given `obl`/`obl:<prep>` whose argument is an adverb attached to that same
    predicate as `advmod` ("quivi", "là", "dinanzi") — an adverbial oblique. `derive_unit` only
    reads `obl` deprel children, so it can't produce one; the membership soft check already
    accepts exactly these tokens as `obl` arguments for the same reason."""
    if not (role == "obl" or OBL_RE.fullmatch(role)):
        return False
    row = dep_index_by_pos.get(arg)
    if row is None or row.deprel != "advmod" or (row.head_line, row.head_token) != pos:
        return False
    return "adverb" in (morph_pos_by_position or {}).get(arg, "").lower()


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
    if row is None or row.deprel != "advmod" or (row.head_line, row.head_token) != pos:
        return False
    return "adjective" in (morph_pos_by_position or {}).get(arg, "").lower()


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
    if row is None or row.deprel != "nmod" or (row.head_line, row.head_token) != pos:
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
    if row is None or row.deprel != "advcl" or (row.head_line, row.head_token) != pos:
        return False
    return role.split(":", 1)[1] in marker_lemmas.get(arg, set())


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
    return "verb" in (morph_pos_by_position or {}).get(arg, "").lower()


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


def _classify_divergence(
    given: dict[int, list[SkelRow]], derived: dict[int, list[SkelRow]],
    dep_index_by_pos: dict[tuple[int, int], DepRow] | None = None,
    morph_pos_by_position: dict[tuple[int, int], str] | None = None,
    case_by_position: dict[tuple[int, int], str] | None = None,
) -> list[Violation]:
    violations: list[Violation] = []
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
    case_children = set(case_lemmas)
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
        return "verb" not in pos_tag.lower()

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

    for line, token in sorted(derived_preds - given_preds):
        violations.append(Violation(line, "tag", f"missing_tuple: predicate {line}.{token} not proposed",
                                     predicate=(line, token)))
    for line, token in sorted(given_preds - derived_preds):
        pos = (line, token)
        if pos in double_listed or _elided_copula_nominal(pos) or _aux_of_derived_predicate(pos):
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
            _apply_subj_authority(g, d, pos, derived_by_pred, dep_index_by_pos)
            derived_args = set(d)
            g = _collapse_coordination(g, pos, dep_index_by_pos)
            d = _collapse_coordination(d, pos, dep_index_by_pos)
            _drop_nmod_obliques(g, d, derived_args, dep_index_by_pos)
        for arg, drole in sorted(d.items()):
            grole = g.get(arg)
            if grole is None:
                if drole in ("ccomp", "xcomp") and arg in given_preds:
                    # Clausal-complement double-listing: the LLM lists the clause as its own
                    # tuple instead of also citing it as this predicate's argument.
                    continue
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
                                                   morph_pos_by_position)):
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
                ):
                    continue
                violations.append(Violation(line, "tag", f"extra_arg: {line}.{token} {grole} {arg}",
                                             role=grole, arg=arg, predicate=pos))
    return violations


@dataclass(frozen=True)
class Repair:
    """One Phase 3 (PLAN.md) mechanical rewrite: `before` (the committed row) replaced by
    `after`. `kind` is "null_subject" (rule 1) or "role_label" (rule 2)."""

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


def _find_repairs(
    given: dict[int, list[SkelRow]], derived: dict[int, list[SkelRow]],
    violations: list[Violation],
) -> list[Repair]:
    """Phase 3 repair candidates, sourced purely from `_classify_divergence`'s own violation
    list (already passed through Phase 2's `_apply_subj_authority` when `dep_index_by_pos` was
    given) — does not recompute the given/derived diff independently."""
    by_pred: dict[tuple[int, int], list[Violation]] = {}
    for v in violations:
        if v.predicate is not None:
            by_pred.setdefault(v.predicate, []).append(v)

    def find_row(pos: tuple[int, int], role: str, arg: tuple[int, int]) -> SkelRow | None:
        for row in given.get(pos[0], ()):
            if (row.line, row.token) == pos and row.role == role and (row.arg_line, row.arg_token) == arg:
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
            before = find_row(pos, "subj", (0, 0))
            if before is not None:
                arg_line, arg_token = missing_subj[0].arg
                after = dataclasses.replace(before, arg_line=arg_line, arg_token=arg_token)
                repairs.append(Repair("null_subject", pos, before, after))

        for v in vs:
            if (v.detail.startswith("role_mismatch") and v.given_role is not None
                    and v.role is not None and v.arg is not None
                    and _safe_role_repair(v.given_role, v.role)):
                before = find_row(pos, v.given_role, v.arg)
                if before is not None:
                    after = dataclasses.replace(before, role=v.role)
                    repairs.append(Repair("role_label", pos, before, after))
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
    no NP to cite), and is not itself an in-unit predicate (only when *both* `morph_rows` and
    `np_rows` are supplied); and — the core of this layer's design — every divergence from
    `derive_unit`
    (only when `dep_rows`/`morph_rows` supplied): `missing_tuple`, `extra_tuple`, `missing_arg`,
    `extra_arg`, `role_mismatch`. `case_rows` (the Layer-2 `case` annex, optional) feeds rule U,
    which accepts a `role_mismatch` whose argument's frozen case value corroborates the derived
    role alone. See module docstring and PLAN.md.
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
            violations.append(
                Violation(row.line, "tag", f"argument {arg} for role {row.role} heads no NP/pronoun/predicate")
            )

    if dep_rows is not None and morph_rows is not None:
        derived = derive_unit(nos, dep_rows, morph_rows)
        morph_pos_by_position = {
            (no, i + 1): row.pos for no, rows in morph_rows.items() for i, row in enumerate(rows)
        }
        case_by_position = (
            {(row.line, row.token): row.case for rows in case_rows.values() for row in rows}
            if case_rows is not None else None
        )
        violations.extend(_classify_divergence(
            rows_by_line, derived, dep_index(dep_rows), morph_pos_by_position, case_by_position,
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
