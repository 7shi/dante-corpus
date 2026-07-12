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

import re
from dataclasses import dataclass, field
from pathlib import Path

from ._paths import SKEL_DIR
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
                        role = f"obl:{lemma}"
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


def _classify_divergence(
    given: dict[int, list[SkelRow]], derived: dict[int, list[SkelRow]]
) -> list[Violation]:
    violations: list[Violation] = []
    given_preds = _predicate_positions_in(given)
    derived_preds = _predicate_positions_in(derived)

    for line, token in sorted(derived_preds - given_preds):
        violations.append(Violation(line, "tag", f"missing_tuple: predicate {line}.{token} not proposed"))
    for line, token in sorted(given_preds - derived_preds):
        violations.append(Violation(line, "tag", f"extra_tuple: predicate {line}.{token} not derived"))

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
                (r.arg_line, r.arg_token): r.role
                for r in rows
                if r.role and (r.arg_line, r.arg_token) != pos
            }

        g = by_arg(given_by_pred.get(pos, []))
        d = by_arg(derived_by_pred.get(pos, []))
        for arg, drole in sorted(d.items()):
            grole = g.get(arg)
            if grole is None:
                violations.append(Violation(line, "tag", f"missing_arg: {line}.{token} {drole} {arg}"))
            elif grole != drole:
                violations.append(
                    Violation(line, "tag", f"role_mismatch: {line}.{token} arg {arg} {grole!r} vs {drole!r}")
                )
        for arg, grole in sorted(g.items()):
            if arg not in d:
                violations.append(Violation(line, "tag", f"extra_arg: {line}.{token} {grole} {arg}"))
    return violations


def validate_unit(
    nos: list[int],
    texts: list[str],
    rows_by_line: dict[int, list[SkelRow]],
    morph_rows: dict[int, list[MorphRow]] | None = None,
    np_rows: dict[int, list[NPSpan]] | None = None,
    dep_rows: dict[int, list[DepRow]] | None = None,
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
    Layer-2 pronoun, and is not itself an in-unit predicate (only when *both* `morph_rows` and
    `np_rows` are supplied); and — the core of this layer's design — every divergence from
    `derive_unit`
    (only when `dep_rows`/`morph_rows` supplied): `missing_tuple`, `extra_tuple`, `missing_arg`,
    `extra_arg`, `role_mismatch`. See module docstring and PLAN.md.
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
            if "pronoun" in r.pos.lower()
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
            violations.append(
                Violation(row.line, "tag", f"argument {arg} for role {row.role} heads no NP/pronoun/predicate")
            )

    if dep_rows is not None and morph_rows is not None:
        derived = derive_unit(nos, dep_rows, morph_rows)
        violations.extend(_classify_divergence(rows_by_line, derived))

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
