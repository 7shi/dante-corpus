"""Core dataclasses and constants for Layer 5 skeleton."""

from __future__ import annotations

import dataclasses
import re
from dataclasses import dataclass, field

from .._paths import SKEL_DIR
from ..case import CaseRow
from ..dep import DepRow, index as dep_index
from ..morph import MorphRow, Violation
from ..np import NPSpan

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


_ROLE_RANK = {"subj": 0, "obj": 1, "iobj": 2, "attr": 3, "xcomp": 4, "ccomp": 5}


def _role_rank(role: str) -> int:
    if role == "":
        return -1
    if role in _ROLE_RANK:
        return _ROLE_RANK[role]
    return 6  # obl / obl:<prep>


def _row_sort_key(row: SkelRow) -> tuple[int, int, int, int]:
    return (row.token, _role_rank(row.role), row.arg_line, row.arg_token)


# --- Language Pack Interface & Italian Constants ----------------------------------

# 1. NP-head relative-pronoun word forms accepted by the membership soft check.
_REL_PRONOUN_WORDS = frozenset({"che", "ch'", "cui", "qual", "quale", "chi"})

# 2. Preposition normalization map (Layer-4 case-child word forms to canonical lemma).
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

# 3. Clausal relative-pronoun word forms (rules CE, DC, DK).
_RELATIVE_PRONOUNS = ("che", "ch", "cui", "chi")

# 4. Comparative particles in Layer-4 case slot (rules AK, DM).
_COMPARATIVE_PARTICLES = ("come", "com", "qual", "quale", "quali")

# 5. Comparative lemmas (rules AK, DM).
_COMPARATIVE_LEMMAS = ("come", "quale")

# 6. Clausal relativizers (rule DP negative gate).
_RELATIVIZERS = _RELATIVE_PRONOUNS + ("qual", "quale", "quali", "quanto", "quanta", "quanti",
                                      "quante", "quantunque", "onde", "dove", "ove", "u")

# 7. Locative relative lemmas (rules DD, CX).
_LOCATIVE_RELATIVE_LEMMAS = frozenset({"dove", "ove", "onde"})


@dataclass(frozen=True)
class LanguagePack:
    """Language-specific constants for Layer 5 skeleton derivation and verification."""

    prep_lemma_norm: dict[str, str]
    rel_pronoun_words: frozenset[str]
    relative_pronouns: tuple[str, ...]
    relativizers: tuple[str, ...]
    comparative_particles: tuple[str, ...]
    comparative_lemmas: tuple[str, ...]
    locative_relative_lemmas: frozenset[str]

    def normalize_prep_lemma(self, lemma: str) -> str:
        return self.prep_lemma_norm.get(lemma, lemma)


ItalianLanguagePack = LanguagePack(
    prep_lemma_norm=_PREP_LEMMA_NORM,
    rel_pronoun_words=_REL_PRONOUN_WORDS,
    relative_pronouns=_RELATIVE_PRONOUNS,
    relativizers=_RELATIVIZERS,
    comparative_particles=_COMPARATIVE_PARTICLES,
    comparative_lemmas=_COMPARATIVE_LEMMAS,
    locative_relative_lemmas=_LOCATIVE_RELATIVE_LEMMAS,
)


_ROLE_CANON = {"attr": "xcomp", "iobj": "obl:a"}


def _normalize_prep_lemma(lemma: str) -> str:
    return _PREP_LEMMA_NORM.get(lemma, lemma)


def _canonicalize_role(role: str) -> str:
    if OBL_RE.fullmatch(role):
        prep = role.split(":", 1)[1]
        return f"obl:{_normalize_prep_lemma(prep)}"
    return _ROLE_CANON.get(role, role)


@dataclass
class GrammarContext:
    """Encapsulates multi-layer grammatical annotations (Layers 1-4) for a parse unit."""

    nos: list[int]
    texts: list[str]
    morph_rows: dict[int, list[MorphRow]] | None = None
    np_rows: dict[int, list[NPSpan]] | None = None
    dep_rows: dict[int, list[DepRow]] | None = None
    case_rows: dict[int, list[CaseRow]] | None = None
    lang: LanguagePack = ItalianLanguagePack

    def __post_init__(self) -> None:
        self._dep_index: dict[tuple[int, int], DepRow] | None = None
        self._children: dict[tuple[int, int], list[DepRow]] | None = None
        self._morph_pos: dict[tuple[int, int], str] | None = None
        self._morph_lemma: dict[tuple[int, int], str] | None = None
        self._case_by_pos: dict[tuple[int, int], str] | None = None

    @property
    def dep_index(self) -> dict[tuple[int, int], DepRow]:
        if self._dep_index is None:
            self._dep_index = dep_index(self.dep_rows) if self.dep_rows is not None else {}
        return self._dep_index

    @property
    def children(self) -> dict[tuple[int, int], list[DepRow]]:
        if self._children is None:
            self._children = {}
            for r in self.dep_index.values():
                self._children.setdefault((r.head_line, r.head_token), []).append(r)
        return self._children

    @property
    def morph_pos(self) -> dict[tuple[int, int], str]:
        if self._morph_pos is None:
            self._morph_pos = {
                (no, i + 1): r.pos for no, rows in (self.morph_rows or {}).items() for i, r in enumerate(rows)
            }
        return self._morph_pos

    @property
    def morph_lemma(self) -> dict[tuple[int, int], str]:
        if self._morph_lemma is None:
            self._morph_lemma = {
                (no, i + 1): r.lemma or "" for no, rows in (self.morph_rows or {}).items() for i, r in enumerate(rows)
            }
        return self._morph_lemma

    @property
    def case_by_pos(self) -> dict[tuple[int, int], str]:
        if self._case_by_pos is None:
            self._case_by_pos = {
                (r.line, r.token): r.slot for rows in (self.case_rows or {}).values() for r in rows
            }
        return self._case_by_pos

    def dep_at(self, pos: tuple[int, int]) -> DepRow | None:
        return self.dep_index.get(pos)

    def morph_at(self, pos: tuple[int, int]) -> MorphRow | None:
        if not self.morph_rows:
            return None
        rows = self.morph_rows.get(pos[0], [])
        if 1 <= pos[1] <= len(rows):
            return rows[pos[1] - 1]
        return None

    def head_of(self, pos: tuple[int, int]) -> tuple[int, int] | None:
        row = self.dep_at(pos)
        return (row.head_line, row.head_token) if row is not None else None

    def deprel_of(self, pos: tuple[int, int]) -> str | None:
        row = self.dep_at(pos)
        return row.deprel if row is not None else None

    def pos_tag(self, pos: tuple[int, int]) -> str:
        return self.morph_pos.get(pos, "")

    def is_verb(self, pos: tuple[int, int]) -> bool:
        return "verb" in self.pos_tag(pos).lower()

    def is_pronoun(self, pos: tuple[int, int]) -> bool:
        tag = self.pos_tag(pos).lower()
        if "pronoun" in tag:
            return True
        m = self.morph_at(pos)
        return m is not None and m.word.lower() in self.lang.rel_pronoun_words

    def case_slot(self, pos: tuple[int, int]) -> str | None:
        return self.case_by_pos.get(pos)
