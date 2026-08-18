"""Stage 2 and Stage 3 fix driver for Layer 5 (prompt-guided violation reduction)."""

from __future__ import annotations

import dataclasses
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from dante_corpus import api, dep, morph, skel
from llm7shi.statusline import StatusLine

try:
    from .driver_build import _merge_tables, _try_parse
    from .driver_ui import (
        _alpha_tokens,
        _apply_unit_repairs,
        _case_rows,
        _classify_violations,
        _dep_rows,
        _is_improvement,
        _log_field_notes,
        _log_rejection,
        _morph_rows,
        _np_rows,
        _print_fix_summary,
        _split_field_notes,
        _violation_class,
    )
except ImportError:
    from driver_build import _merge_tables, _try_parse
    from driver_ui import (
        _alpha_tokens,
        _apply_unit_repairs,
        _case_rows,
        _classify_violations,
        _dep_rows,
        _is_improvement,
        _log_field_notes,
        _log_rejection,
        _morph_rows,
        _np_rows,
        _print_fix_summary,
        _split_field_notes,
        _violation_class,
    )

_HINT_PHRASING = {
    "missing_tuple": "may be missing a predicate near '{word}' ({line}.{token}) — check whether "
                      "it heads its own clause",
    "missing_tuple_nominal": "'{word}' ({line}.{token}) may head a VERBLESS clause — most often "
                             "the subject of an elided verb of speech (then: subj ∅, the quotation "
                             "as ccomp, the addressee as obl:a), otherwise a noun or pronoun "
                             "predicated with no copula written ('e te cortese', 'mantoani per "
                             "patrïa ambedui'). Either way it is itself the predicate row",
    "extra_tuple": "the predicate '{word}' ({line}.{token}) you proposed may not be warranted — "
                   "reconsider whether it is really an independent predicate",
    "extra_tuple_adverb": "'{word}' ({line}.{token}) is an ADVERB, so it is never a predicate — "
                          "cite it as an argument of the verb it modifies, or leave it out, but "
                          "do not open a Pred row for it",
    "extra_tuple_adjective": "'{word}' ({line}.{token}) is an adjective, and an adjective is a "
                             "predicate only when a copula links it ('è degna', 'son presto') — an "
                             "attributive one modifying a noun is not. If it is predicated of "
                             "something, give it as attr/xcomp on that verb rather than a Pred row",
    "missing_arg": "the predicate '{word}' ({line}.{token}) may be missing a '{role}' argument — "
                   "check for one",
    "missing_arg_adverb": "the predicate '{word}' ({line}.{token}) may be missing a '{role}' "
                          "argument — a locative or directional adverb (là, fuor, dentro, dinanzi, "
                          "suso, dove, ...) answering where/whither for it counts as one, and is "
                          "not to be skipped as a mere modifier",
    "missing_arg_subject": "the predicate '{word}' ({line}.{token}) may be missing its SUBJECT — "
                           "look after the verb as well as before it, and remember a verb joined "
                           "by e/né/ma to an earlier one shares that one's written subject",
    "extra_arg_subject": "the SUBJECT currently given for '{word}' ({line}.{token}) may be wrong — "
                         "check whether the sentence writes one after the verb, and that what is "
                         "cited is not an unstressed clitic (lo, la, 'l, mi, si, ne)",
    "extra_arg": "the predicate '{word}' ({line}.{token})'s '{role}' argument may not belong — "
                "recheck it",
    "extra_arg_adjective": "'{word}' ({line}.{token})'s argument at the '{role}' slot may be an "
                           "ATTRIBUTIVE adjective, not a secondary predicate of it — an "
                           "attributive adjective modifying a noun inside that argument's own "
                           "phrase is not a separate predication",
    "role_mismatch": "the predicate '{word}' ({line}.{token})'s argument currently labeled "
                     "'{given_role}' may need a different role — recheck it",
    "dual_role": "one token has been given TWO roles ('{role}' and '{given_role}') for the "
                 "predicate '{word}' ({line}.{token}) — one token fills one role, unless it is a "
                 "fused clitic (gliel' = gli + lo, sen = si + ne)",
}


def _fix_hint(
    nos: list[int], texts: list[str], violations: list[morph.Violation],
    morph_rows: dict[int, list] | None = None,
) -> str | None:
    token_lists = {no: _alpha_tokens(t) for no, t in zip(nos, texts)}

    def word_at(pos: tuple[int, int]) -> str:
        line, token = pos
        tokens = token_lists.get(line)
        return tokens[token - 1] if tokens and 1 <= token <= len(tokens) else "?"

    def pos_at(pos: tuple[int, int]) -> str:
        line, token = pos
        rows = (morph_rows or {}).get(line) or []
        return rows[token - 1].pos if 1 <= token <= len(rows) else ""

    lines: list[str] = []
    seen: set[tuple[str, tuple[int, int], str | None]] = set()
    for v in violations:
        if v.predicate is None:
            continue
        kind = _violation_class(v)
        if kind == "missing_tuple" and not skel.is_verb_pos(pos_at(v.predicate)):
            kind = "missing_tuple_nominal"
        elif kind == "extra_tuple":
            tag = pos_at(v.predicate).lower()
            if "adverb" in tag:
                kind = "extra_tuple_adverb"
            elif "adjective" in tag:
                kind = "extra_tuple_adjective"
        elif (kind == "extra_arg" and v.role in ("xcomp", "attr") and v.arg is not None
              and "adjective" in pos_at(v.arg).lower()):
            kind = "extra_arg_adjective"
        elif kind == "missing_arg" and v.arg is not None and "adverb" in pos_at(v.arg).lower():
            kind = "missing_arg_adverb"
        if kind in ("missing_arg", "extra_arg") and (v.role or v.given_role) == "subj":
            kind = f"{kind}_subject"
        phrasing = _HINT_PHRASING.get(kind)
        if phrasing is None:
            continue
        key = (kind, v.predicate, v.role)
        if key in seen:
            continue
        seen.add(key)
        line, token = v.predicate
        lines.append("- " + phrasing.format(
            word=word_at(v.predicate), line=line, token=token,
            role=v.role or v.given_role, given_role=v.given_role or v.role,
        ))
    if not lines:
        return None
    return (
        "A previous independent reading of this sentence had issues in these spots (read the "
        "sentence fresh and decide for yourself — this is a pointer to re-examine, not the "
        "answer):\n" + "\n".join(lines)
    )


class _UnitContext:
    """The frozen Layer 1-3 view of one parse unit, shared by every class prompt."""

    def __init__(self, nos, texts, morph_rows, np_rows):
        self.nos = nos
        self.texts = texts
        self.morph_rows = morph_rows or {}
        self.np_rows = np_rows or {}
        self.tokens = {no: _alpha_tokens(t) for no, t in zip(nos, texts)}

    def word(self, pos: tuple[int, int]) -> str:
        toks = self.tokens.get(pos[0])
        return toks[pos[1] - 1] if toks and 1 <= pos[1] <= len(toks) else "?"

    def pos_tag(self, pos: tuple[int, int]) -> str:
        rows = self.morph_rows.get(pos[0]) or []
        return rows[pos[1] - 1].pos if 1 <= pos[1] <= len(rows) else ""

    def cite(self, pos: tuple[int, int]) -> str:
        return f"{pos[0]}.{pos[1]} '{self.word(pos)}'"

    def morph_pos_by_position(self) -> dict[tuple[int, int], str]:
        return {(no, i + 1): r.pos
                for no, rows in self.morph_rows.items() for i, r in enumerate(rows)}

    def source_block(self) -> str:
        lines = "\n".join(f"{no} {t}" for no, t in zip(self.nos, self.texts))
        toks = "\n".join(
            f"{no}.{i} {tok}" + (f" ({self.pos_tag((no, i))})" if self.pos_tag((no, i)) else "")
            for no in self.nos for i, tok in enumerate(self.tokens[no], start=1)
        )
        parts = [f"Sentence:\n{lines}", f"Tokens (Line.Token Word (POS)):\n{toks}"]
        nps = [f"{no}.{s.head} [{s.text}]"
               for no in self.nos
               for s in sorted(self.np_rows.get(no, ()), key=lambda s: (s.start, -s.end))]
        if nps:
            parts.append("Noun phrases (Line.Head [text]):\n" + "\n".join(nps))
        return "\n\n".join(parts)


_ROLE_MENU = ("subj, obj, iobj, attr, xcomp, ccomp, or obl:<preposition lemma> "
              "(obl:in, obl:di, obl:a, obl:per, ...)")

_ANSWER_RE = re.compile(r"^\s*Q(\d+)\s*[:.)]\s*(.+?)\s*$", re.MULTILINE)
_TOKEN_REF_RE = re.compile(r"^(\d+)\s*[.,]\s*(\d+)$")


def _parse_answers(text: str) -> dict[int, str]:
    return {int(n): body.strip().strip("`*") for n, body in _ANSWER_RE.findall(text)}


_STAND_PAT = {
    "extra_arg": "keep", "extra_arg_subject": "keep", "extra_arg_adjective": "keep",
    "arg_slot": "keep",
    "missing_arg": "none", "missing_arg_adverb": "none", "missing_arg_subject": "none",
    "dual_role": "both",
    "extra_tuple": "yes", "extra_tuple_adverb": "yes", "extra_tuple_adjective": "yes",
}


def _is_refusal(cls: str, vs: list[morph.Violation], text: str) -> bool:
    answers = _parse_answers(text)
    if not answers:
        return False
    word = _STAND_PAT.get(cls)
    given = {i: skel._canonicalize_role(v.given_role or "").lower()
             for i, v in enumerate(vs, start=1)}
    for i, raw in answers.items():
        ans = raw.strip().strip("`*'\"").lower()
        if word is not None and ans == word:
            continue
        if cls == "role_mismatch" and ans and skel._canonicalize_role(ans).lower() == given.get(i):
            continue
        return False
    return True


def _token_ref(answer: str) -> tuple[int, int] | None:
    m = _TOKEN_REF_RE.match(answer.strip().strip("'\"“”"))
    return (int(m.group(1)), int(m.group(2))) if m else None


def _rows_of_predicate(rows_by_line, pos: tuple[int, int]) -> list[skel.SkelRow]:
    return [r for r in rows_by_line.get(pos[0], []) if (r.line, r.token) == pos]


def _find_arg_row(rows_by_line, pos: tuple[int, int], role: str, arg: tuple[int, int]):
    pred_rows = _rows_of_predicate(rows_by_line, pos)
    for row in pred_rows:
        if (row.arg_line, row.arg_token) == arg and skel._canonicalize_role(row.role) == role:
            return row
    matching_role = [r for r in pred_rows if skel._canonicalize_role(r.role) == role]
    if len(matching_role) == 1:
        return matching_role[0]
    return None


_ASK_HEADER = """\
You are reading archaic Italian (Dante's Divine Comedy) and answering a few precise questions \
about the grammar of ONE sentence. You are given the sentence, its tokens with parts of speech, \
and its noun phrases.

Answer ONLY with one line per question, in the form
Q1: <answer>
Q2: <answer>
Nothing else — no explanation, no table, no repetition of the question.

One exception. If a question cannot be answered cleanly, answer it anyway with your best reading \
AND add one extra line, after all the answers, in the form
N1: <what is wrong with that question, in one sentence>
numbered for the question it is about. Write one when the sentence offers nothing of the shape the \
question asks for, when two answers are equally defensible, or when the conventions you were given \
do not fit what the sentence actually does — and only then. A note never replaces an answer and \
never changes it; it is read separately by a human.
"""

_TABLE_HEADER = """\
You are reading archaic Italian (Dante's Divine Comedy). You are given one sentence, its tokens \
with parts of speech, and its noun phrases.

Output ONLY a Markdown table with one row per (predicate, argument) pair:
| Pred Line | Pred Token | Pred Word | Role | Arg Line | Arg Token | Arg Word |
Role is one of: subj, obj, iobj, attr, xcomp, ccomp, obl:<preposition lemma>. Cite token \
positions from the token list; Arg Word is that token's word copied verbatim. A pro-drop \
(missing) subject is its own row with Arg Line 0, Arg Token 0, Arg Word ∅. Output only the \
table, with no commentary.

One exception. If some part of what you were asked about cannot be given rows cleanly, output \
your best reading as rows anyway, and add note lines AFTER the table (never before it, never \
between rows), one per problem, in the form
N<line>.<token>: <what is wrong, in one sentence>
citing the token it is about. Write one when the sentence offers nothing of the shape asked for, \
when two analyses are equally defensible, or when the conventions you were given do not fit what \
the sentence actually does — and only then. A note never replaces a row; it is read separately \
by a human.
"""

_CONV_ROLES = f"""\
Role vocabulary: {_ROLE_MENU}. `attr` is a secondary predicate over an argument — an adjective \
or noun predicated of the verb's object or subject with no copula of its own ("faceva dir l'un \
'No'", "vidi lui contento"). `xcomp`/`ccomp` are clausal complements, and their argument must \
itself be a predicate. Use bare `obl` only if there truly is no preposition to name.\
"""

_CONV_PRODROP = """\
A pro-drop (unwritten) subject of a finite verb is still a real subject slot, cited as 0.0. But \
a NON-finite predicate (infinitive, participle, gerund) usually takes its subject from the verb \
it depends on ("i' cominciai a dir" — the subject of `dir` is `i'`; the causee of fare/lasciare \
+ infinitive; the noun a participle modifies); use 0.0 only when nothing in the sentence \
supplies one.\
"""

_CONV_RELPRON = """\
A relative pronoun (che, cui, qual, ...) that is a clause's subject/object/oblique is cited as \
the argument itself — never resolved to its antecedent. A verb token with a fused enclitic \
(venendomi = venire + mi) encodes that pronoun internally; it gets no separate argument row.\
"""

_CONV_ADVERB = """\
An ADVERB is never a predicate — not a comparative (più, meno, sì), not a locative (dentro, \
dinanzi, dietro, fuor). It is an argument of the verb it modifies, or, if it is a manner or \
degree adverb, it is left out.\
"""

_CONV_ADVERB_ARG = """\
A LOCATIVE OR DIRECTIONAL adverb — là, qui, qua, dentro, fuor, dinanzi, dietro, suso, giù, oltre, \
intorno, and the relative dove/ove/u'/v' — that answers *where* or *whither* for the verb IS one \
of its arguments, not a modifier to be skipped: cite it as `obl:<preposition>` if a preposition is \
written and as bare `obl` if none is. Only a manner, degree or negation adverb (più, non, ben, \
così, sì) is left out.\
"""

_CONV_SUBJECT = """\
Italian writes the subject AFTER its verb freely, and a postverbal subject is still the subject, \
not a predicate nominal or an object: "no i fia riguardo", "Bene ascolta chi la nota", "fannomi \
onore", "sono ei puniti". Before answering that a subject is unwritten (0.0), look for one \
standing after the verb. An unstressed proclitic pronoun (lo, la, li, le, 'l, mi, ti, ci, vi, ne, \
si) is NEVER the subject — it is the object or dative; a written subject is a full noun phrase or \
a nominative pronoun (io, tu, elli, ei, quei, chi). And in a coordination the subject is normally \
written once, at the FIRST conjunct: every later verb joined by e/né/ma to it takes that same \
subject, cited at its own token position, not 0.0.\
"""

_CONV_REPEATED = """\
A predicate may carry the SAME role twice, and each occurrence needs its own row: two obliques \
with the same preposition ("pur a sinistra, giù calando al fondo"), two objects, two places. \
Having already listed one filler of a slot is not a reason to leave a second one out.\
"""

_CONV_ADJUNCT = """\
A PREPOSITIONAL PHRASE hanging on the verb is one of its arguments even when it only sets the \
scene — a place ("tra i cantor del cielo", "in quel che forato fu"), a source ("dal corno che 'n \
destro si stende"), a time, or a manner ("a guisa del parlar di quella vaga"). Cite it as \
`obl:<preposition lemma>` at the head noun of the phrase. Being inessential to the sense, or \
standing far from its verb, or already having a comparison or a relative clause of its own, is \
not a reason to leave it out.\
"""

_CONV_DATIVE = """\
An unstressed DATIVE clitic (mi, ti, ci, vi, gli, le, si, ne) is an argument of its verb even when \
it is the dative of the person concerned rather than a true recipient: "ch'io **le** porsi ordita", \
"se loco **m'**è tolto", "l'occhio in testa **mi** scintilla". When a question asks which token \
fills a verb's dative slot — `iobj` or `obl:a` — that clitic, at its own token position, is the \
answer; never skip it as a mere particle.\
"""

_CONV_ADJECTIVE = """\
An ATTRIBUTIVE ADJECTIVE is not a predicate: "una lonza leggera", "l'antica Rachele", "persone \
ratte" head no clause. Neither is an APPOSITIVE one — an adjective phrase set off by a comma from \
the noun it modifies ("grande campagna, piena di duolo e di tormento rio") is still that noun's \
modifier. An adjective is a predicate only where a copula links it ("anima fia degna", "e pronti \
sono"). An adjective predicated of another verb's argument is that verb's `attr`, not a predicate \
of its own.\
"""

_CONV_VERBLESS = """\
An ELIDED VERB OF SPEECH ("Ed elli a me: «…»", "E io a lui:", where the verb of saying is left \
out) IS a clause, and the corpus makes the SUBJECT token its predicate: Pred = elli / io / the \
speaker's noun, with `subj` 0.0 (the verb is missing, so its subject slot is empty), the \
quotation's main verb as `ccomp`, and the addressee as `obl:a`. The ADDRESSEE IS OPTIONAL: "E io: \
«Maestro, …»", "e quei: «Di rado …»" are the same frame with no a-phrase written — same Pred row, \
same `ccomp`, just no `obl:a`. The Pred token is always the pronoun or noun naming the speaker, \
never the conjunction in front of it ("E", "Ed", "Ma"). The same holds for any other \
verbless clause predicated with no copula written ("e te cortese ch'ubidisti tosto", "mantoani \
per patrïa ambedui"): the noun or pronoun is the Pred token, with `subj` 0.0.\
"""


@dataclass(frozen=True)
class _ClassPrompt:
    system: str
    ask: Callable
    apply: Callable


def _numbered(items: list[str]) -> str:
    return "\n".join(f"Q{i}: {t}" for i, t in enumerate(items, start=1))


# --- role_mismatch ---------------------------------------------------------------------------

def _ask_role_mismatch(ctx: _UnitContext, vs: list[morph.Violation]) -> str:
    body = _numbered([f"predicate {ctx.cite(v.predicate)} — argument {ctx.cite(v.arg)}"
                      for v in vs])
    return (
        f"{ctx.source_block()}\n\n"
        "For each question below, name the grammatical role the cited argument fills for the "
        "cited predicate. Answer with exactly one role, or `none` if the cited token is not an "
        f"argument of that predicate at all.\n\n{body}"
    )


def _apply_role_mismatch(ctx, vs, rows_by_line, text: str) -> bool:
    answers = _parse_answers(text)
    changed = False
    for i, v in enumerate(vs, start=1):
        ans = answers.get(i)
        if ans is None:
            continue
        row = _find_arg_row(rows_by_line, v.predicate, v.given_role, v.arg)
        if row is None:
            continue
        rows = rows_by_line[row.line]
        if ans.lower() == "none":
            rows.remove(row)
            changed = True
        elif ans and skel._role_valid(ans) and ans != row.role:
            rows[rows.index(row)] = dataclasses.replace(row, role=ans)
            changed = True
    return changed


# --- extra_arg -------------------------------------------------------------------------------

def _ask_extra_arg(ctx: _UnitContext, vs: list[morph.Violation]) -> str:
    body = _numbered([f"predicate {ctx.cite(v.predicate)} — {ctx.cite(v.arg)} listed as "
                      f"'{v.role}'" if v.arg != (0, 0) else
                      f"predicate {ctx.cite(v.predicate)} — an unwritten (pro-drop) '{v.role}'"
                      for v in vs])
    return (
        f"{ctx.source_block()}\n\n"
        "Each question names a predicate and a token currently listed as one of its arguments, "
        "with the role it was given. Decide whether that is right. Answer one of:\n"
        "  keep    — the token really is that predicate's argument in that role\n"
        "  <role>  — it is that predicate's argument, but in a different role\n"
        "  drop    — it is not an argument of that predicate at all\n"
        f"\n{body}"
    )


def _apply_extra_arg(ctx, vs, rows_by_line, text: str) -> bool:
    answers = _parse_answers(text)
    changed = False
    for i, v in enumerate(vs, start=1):
        ans = answers.get(i)
        if ans is None or ans.lower() == "keep":
            continue
        row = _find_arg_row(rows_by_line, v.predicate, v.role, v.arg)
        if row is None:
            continue
        rows = rows_by_line[row.line]
        if ans.lower() == "drop":
            rows.remove(row)
            changed = True
        elif ans and skel._role_valid(ans) and ans != row.role:
            rows[rows.index(row)] = dataclasses.replace(row, role=ans)
            changed = True
    return changed


# --- missing_arg -----------------------------------------------------------------------------

def _ask_missing_arg(ctx: _UnitContext, vs: list[morph.Violation]) -> str:
    body = _numbered([f"predicate {ctx.cite(v.predicate)} — which token is its '{v.role}'?"
                      for v in vs])
    return (
        f"{ctx.source_block()}\n\n"
        "Each question names a predicate and a role slot that may be filled in this sentence "
        "but is currently unlisted. Answer the token position that fills it, as Line.Token "
        "(for example 3.4); answer 0.0 for a subject that is not written out; answer `none` if "
        f"the sentence does not fill that slot at all.\n\n{body}"
    )


def _apply_missing_arg(ctx, vs, rows_by_line, text: str) -> bool:
    answers = _parse_answers(text)
    changed = False
    for i, v in enumerate(vs, start=1):
        ans = answers.get(i)
        if ans is None or ans.lower() == "none":
            continue
        arg = _token_ref(ans)
        if arg is None:
            continue
        if v.role == "subj" and arg == (0, 0) and v.arg != (0, 0):
            continue
        line, token = v.predicate
        new = skel.SkelRow(line, token, ctx.word(v.predicate), v.role, arg[0], arg[1])
        rows = rows_by_line.setdefault(line, [])
        if new in rows:
            continue
        existing_subj = next((r for r in rows if (r.line, r.token) == (line, token) and r.role == "subj"), None)
        if v.role == "subj" and existing_subj is not None:
            if existing_subj.arg_line == 0 and existing_subj.arg_token == 0 and arg != (0, 0):
                rows[rows.index(existing_subj)] = new
                changed = True
                continue
            else:
                continue
        if any((r.line, r.token) == (line, token) and (r.arg_line, r.arg_token) == arg
               and r.role != v.role
               and not skel._fused_clitic_dual_role(r.role, v.role, arg,
                                                    ctx.morph_pos_by_position(), None)
               for r in rows):
            continue
        rows.append(new)
        changed = True
    return changed


# --- arg_slot --------------------------------------------------------------------------------

def _ask_arg_slot(ctx: _UnitContext, vs: list[morph.Violation]) -> str:
    body = _numbered([
        f"predicate {ctx.cite(v.predicate)} — its '{v.role}' is currently "
        + (f"{ctx.cite(v.arg)}" if v.arg != (0, 0) else "unwritten (pro-drop)")
        for v in vs
    ])
    return (
        f"{ctx.source_block()}\n\n"
        "Each question names a predicate, one role slot, and the token currently given in that "
        "slot. Read the sentence and decide what really fills it. Answer one of:\n"
        "  keep       — the token already given is right\n"
        "  <line>.<token>  — a different token fills that slot (for example 3.4)\n"
        "  0.0        — the slot is a subject that is not written out\n"
        "  none       — the predicate has no argument in that slot at all\n"
        f"\n{body}"
    )


def _apply_arg_slot(ctx, vs, rows_by_line, text: str) -> bool:
    answers = _parse_answers(text)
    changed = False
    for i, v in enumerate(vs, start=1):
        ans = (answers.get(i) or "").strip()
        if not ans or ans.lower() == "keep":
            continue
        row = _find_arg_row(rows_by_line, v.predicate, v.role, v.arg)
        if row is None:
            continue
        rows = rows_by_line[row.line]
        if ans.lower() in ("none", "drop"):
            rows.remove(row)
            changed = True
            continue
        arg = _token_ref(ans)
        if arg is None or arg == v.arg:
            continue
        if arg != (0, 0) and arg == v.predicate:
            continue
        if arg == (0, 0) and v.role != "subj":
            continue
        rows[rows.index(row)] = dataclasses.replace(row, arg_line=arg[0], arg_token=arg[1])
        changed = True
    return changed


# --- dual_role -------------------------------------------------------------------------------

def _ask_dual_role(ctx: _UnitContext, vs: list[morph.Violation]) -> str:
    body = _numbered([
        f"predicate {ctx.cite(v.predicate)} — {ctx.cite(v.arg)} is listed as BOTH "
        f"'{v.role}' and '{v.given_role}'"
        for v in vs
    ])
    return (
        f"{ctx.source_block()}\n\n"
        "Each question names a predicate and one token that has been given two different roles for "
        "it. One token normally fills one role, so one of the two is wrong. Answer with the single "
        "role that is right, or `both` if the token really does fill both at once (only a fused "
        "clitic does: gliel' = gli + lo, sen = si + ne).\n\n"
        f"{body}"
    )


def _apply_dual_role(ctx, vs, rows_by_line, text: str) -> bool:
    answers = _parse_answers(text)
    changed = False
    for i, v in enumerate(vs, start=1):
        ans = (answers.get(i) or "").strip()
        if not ans or ans.lower() == "both":
            continue
        if not skel._role_valid(ans):
            continue
        rows = rows_by_line.get(v.predicate[0]) or []
        clash = [r for r in rows
                 if (r.line, r.token) == v.predicate and (r.arg_line, r.arg_token) == v.arg]
        if len(clash) < 2:
            continue
        keep = next((r for r in clash if r.role == ans), None)
        for r in clash:
            if keep is not None and r.role == keep.role:
                continue
            if keep is None:
                keep = dataclasses.replace(r, role=ans)
                rows[rows.index(r)] = keep
            else:
                rows.remove(r)
            changed = True
    return changed


# --- extra_tuple -----------------------------------------------------------------------------

def _ask_extra_tuple(ctx: _UnitContext, vs: list[morph.Violation]) -> str:
    body = _numbered([f"{ctx.cite(v.predicate)}"
                      + (f" ({ctx.pos_tag(v.predicate)})" if ctx.pos_tag(v.predicate) else "")
                      for v in vs])
    return (
        f"{ctx.source_block()}\n\n"
        "Each question names a token the current analysis treats as an independent predicate — "
        "a token heading a clause of its own. Decide whether it really does. Answer one of:\n"
        "  yes                     — it heads a clause of its own\n"
        "  no <Line.Token> <role>  — it does not; it is an argument of that predicate, in that "
        "role\n"
        "  no -                    — it heads no clause and is not an argument of anything\n"
        f"\n{body}"
    )


def _apply_extra_tuple(ctx, vs, rows_by_line, text: str) -> bool:
    answers = _parse_answers(text)
    changed = False
    for i, v in enumerate(vs, start=1):
        ans = answers.get(i)
        if ans is None or not ans.lower().startswith("no"):
            continue
        pos = v.predicate
        for row in _rows_of_predicate(rows_by_line, pos):
            rows_by_line[row.line].remove(row)
            changed = True
        rest = ans[2:].strip().strip(":,").split()
        if len(rest) == 2:
            host, role = _token_ref(rest[0]), rest[1]
            if host and host != pos and skel._role_valid(role) and role:
                new = skel.SkelRow(host[0], host[1], ctx.word(host), role, pos[0], pos[1])
                rows = rows_by_line.setdefault(host[0], [])
                if new not in rows:
                    rows.append(new)
                    changed = True
    return changed


# --- missing_tuple ---------------------------------------------------------------------------

def _ask_missing_tuple(ctx: _UnitContext, vs: list[morph.Violation]) -> str:
    targets = "\n".join(f"- {ctx.cite(v.predicate)}"
                        + (f" ({ctx.pos_tag(v.predicate)})" if ctx.pos_tag(v.predicate) else "")
                        for v in vs)
    return (
        f"{ctx.source_block()}\n\n"
        "The current analysis lists no clause headed by the token(s) below, and it may be wrong "
        "about that. For each one that DOES head a clause of its own, output its rows: the token "
        "as Pred, with one row per argument. Output nothing for a token that heads no clause. "
        "Output rows for these tokens only — do not restate the rest of the sentence.\n\n"
        f"{targets}"
    )


def _ask_missing_tuple_nominal(ctx: _UnitContext, vs: list[morph.Violation]) -> str:
    targets = "\n".join(f"- {ctx.cite(v.predicate)}"
                        + (f" ({ctx.pos_tag(v.predicate)})" if ctx.pos_tag(v.predicate) else "")
                        for v in vs)
    return (
        f"{ctx.source_block()}\n\n"
        "Each token below is a noun or pronoun that the current analysis gives no rows at all. "
        "In this corpus such a token IS the Pred of a verbless clause whenever a verb is elided "
        "around it — above all a verb of speech ('Ed elli: «…»', 'E io: «Maestro, …»', with or "
        "without an addressee), and otherwise a predication with no copula written. Write its "
        "rows in that frame: the token as Pred, `subj` 0.0, the quotation's main verb as `ccomp`, "
        "and an addressee introduced by 'a' (e.g. 'Ed elli a me'), if one is written, as `obl:a` "
        "(do NOT list vocative address like 'Maestro' as an argument). Output nothing only if the "
        "token is genuinely an argument of some other predicate already listed. Output rows for these "
        "tokens only — do not restate the rest of the sentence.\n\n"
        f"{targets}"
    )


def _apply_missing_tuple(ctx, vs, rows_by_line, text: str) -> bool:
    try:
        parsed, _ = skel.resolve_chunk(ctx.nos, ctx.texts, _merge_tables(text))
    except ValueError:
        return False
    wanted = {v.predicate for v in vs}
    changed = False
    for rows in parsed.values():
        for row in rows:
            if (row.line, row.token) not in wanted:
                continue
            target = rows_by_line.setdefault(row.line, [])
            if row not in target:
                target.append(row)
                changed = True
    return changed


_CLASS_PROMPTS: dict[str, _ClassPrompt] = {
    "role_mismatch": _ClassPrompt(
        system=f"{_ASK_HEADER}\n{_CONV_ROLES}\n\n{_CONV_RELPRON}",
        ask=_ask_role_mismatch, apply=_apply_role_mismatch),
    "extra_arg": _ClassPrompt(
        system=f"{_ASK_HEADER}\n{_CONV_ROLES}\n\n{_CONV_PRODROP}\n\n{_CONV_RELPRON}",
        ask=_ask_extra_arg, apply=_apply_extra_arg),
    "extra_arg_adjective": _ClassPrompt(
        system=f"{_ASK_HEADER}\n{_CONV_ADJECTIVE}\n\n{_CONV_ROLES}\n\n{_CONV_PRODROP}",
        ask=_ask_extra_arg, apply=_apply_extra_arg),
    "missing_arg": _ClassPrompt(
        system=f"{_ASK_HEADER}\n{_CONV_ROLES}\n\n{_CONV_PRODROP}\n\n{_CONV_RELPRON}\n\n"
               f"{_CONV_REPEATED}\n\n{_CONV_ADJUNCT}\n\n{_CONV_DATIVE}",
        ask=_ask_missing_arg, apply=_apply_missing_arg),
    "missing_arg_adverb": _ClassPrompt(
        system=f"{_ASK_HEADER}\n{_CONV_ADVERB_ARG}\n\n{_CONV_ROLES}\n\n{_CONV_REPEATED}",
        ask=_ask_missing_arg, apply=_apply_missing_arg),
    "missing_arg_subject": _ClassPrompt(
        system=f"{_ASK_HEADER}\n{_CONV_SUBJECT}\n\n{_CONV_PRODROP}\n\n{_CONV_ROLES}",
        ask=_ask_missing_arg, apply=_apply_missing_arg),
    "extra_arg_subject": _ClassPrompt(
        system=f"{_ASK_HEADER}\n{_CONV_SUBJECT}\n\n{_CONV_PRODROP}\n\n{_CONV_ROLES}",
        ask=_ask_extra_arg, apply=_apply_extra_arg),
    "arg_slot": _ClassPrompt(
        system=f"{_ASK_HEADER}\n{_CONV_ROLES}\n\n{_CONV_SUBJECT}\n\n{_CONV_PRODROP}\n\n"
               f"{_CONV_RELPRON}",
        ask=_ask_arg_slot, apply=_apply_arg_slot),
    "dual_role": _ClassPrompt(
        system=f"{_ASK_HEADER}\n{_CONV_ROLES}\n\n{_CONV_RELPRON}\n\n{_CONV_SUBJECT}",
        ask=_ask_dual_role, apply=_apply_dual_role),
    "extra_tuple": _ClassPrompt(
        system=f"{_ASK_HEADER}\n{_CONV_ROLES}",
        ask=_ask_extra_tuple, apply=_apply_extra_tuple),
    "extra_tuple_adverb": _ClassPrompt(
        system=f"{_ASK_HEADER}\n{_CONV_ADVERB}\n\n{_CONV_ROLES}",
        ask=_ask_extra_tuple, apply=_apply_extra_tuple),
    "extra_tuple_adjective": _ClassPrompt(
        system=f"{_ASK_HEADER}\n{_CONV_ADJECTIVE}\n\n{_CONV_ROLES}",
        ask=_ask_extra_tuple, apply=_apply_extra_tuple),
    "missing_tuple": _ClassPrompt(
        system=f"{_TABLE_HEADER}\n{_CONV_ROLES}\n\n{_CONV_PRODROP}",
        ask=_ask_missing_tuple, apply=_apply_missing_tuple),
    "missing_tuple_nominal": _ClassPrompt(
        system=f"{_TABLE_HEADER}\n{_CONV_VERBLESS}\n\n{_CONV_ROLES}",
        ask=_ask_missing_tuple_nominal, apply=_apply_missing_tuple),
}


def _violation_subclass(v: morph.Violation, ctx: _UnitContext) -> str:
    kind = _violation_class(v)
    if v.predicate is None:
        return kind
    tag = ctx.pos_tag(v.predicate).lower()
    if kind == "missing_tuple" and not skel.is_verb_pos(tag):
        return "missing_tuple_nominal"
    if kind == "extra_tuple":
        if "adverb" in tag:
            return "extra_tuple_adverb"
        if "adjective" in tag:
            return "extra_tuple_adjective"
    if (kind == "extra_arg" and v.role in ("xcomp", "attr") and v.arg is not None
            and "adjective" in ctx.pos_tag(v.arg).lower()):
        return "extra_arg_adjective"
    if (kind == "missing_arg" and v.arg is not None
            and "adverb" in ctx.pos_tag(v.arg).lower()):
        return "missing_arg_adverb"
    if kind in ("missing_arg", "extra_arg") and (v.role or v.given_role) == "subj":
        return f"{kind}_subject"
    return kind


def _ask_class(
    cls: str, ctx: _UnitContext, vs: list[morph.Violation],
    rows_by_line: dict[int, list[skel.SkelRow]], model: str, ui: StatusLine, label: str,
    log_path: Path | None = None, stats: Counter[str] | None = None,
) -> dict[int, list[skel.SkelRow]] | None:
    from llm7shi import Client

    prompt = _CLASS_PROMPTS[cls]
    question = prompt.ask(ctx, vs)
    client = Client(model=model, file=ui.stream, show_params=False)
    client.set_system_prompt(prompt.system)
    ui.log("")
    answer = client(question).text
    ui.stream.end()
    answer, notes = _split_field_notes(answer)
    _log_field_notes(
        log_path, label, ctx.nos, cls, notes,
        {i: f"{ctx.cite(v.predicate)} {v.role or v.given_role or '-'}"
         for i, v in enumerate(vs, start=1) if v.predicate is not None},
        ctx.word,
    )
    trial = {no: list(rows) for no, rows in rows_by_line.items()}
    if not prompt.apply(ctx, vs, trial, answer):
        refused = _is_refusal(cls, vs, answer)
        if stats is not None:
            stats[f"{'refused' if refused else 'unusable'}:{cls}"] += 1
        if log_path:
            verdict = ("refused: the reading stands" if refused else "no usable answer")
            with log_path.open("a", encoding="utf-8") as f:
                f.write(f"=== {label} lines {ctx.nos[0]}-{ctx.nos[-1]} [{cls}]: "
                        f"{verdict} ===\n{answer.strip()}\n\n")
        return None
    return trial


_CLASS_ORDER = (
    "missing_tuple", "missing_tuple_nominal",
    "extra_tuple_adverb", "extra_tuple_adjective", "extra_tuple",
    "dual_role", "arg_slot",
    "role_mismatch", "extra_arg_subject", "extra_arg_adjective", "extra_arg",
    "missing_arg_subject", "missing_arg_adverb", "missing_arg",
)

_EXTRA_ARG_CLASSES = ("extra_arg", "extra_arg_subject", "extra_arg_adjective")
_MISSING_ARG_CLASSES = ("missing_arg", "missing_arg_subject", "missing_arg_adverb")


def _split_slot_conflicts(
    by_class: dict[str, list[morph.Violation]],
) -> dict[str, list[morph.Violation]]:
    extra_keys = {
        (v.predicate, v.role): (cls, v)
        for cls in _EXTRA_ARG_CLASSES for v in by_class.get(cls, [])
        if v.predicate is not None and v.role
    }
    out = {cls: list(vs) for cls, vs in by_class.items()}
    for cls in _MISSING_ARG_CLASSES:
        for v in list(out.get(cls, [])):
            hit = extra_keys.get((v.predicate, v.role))
            if hit is None:
                continue
            extra_cls, extra_v = hit
            out[cls].remove(v)
            if extra_v in out.get(extra_cls, []):
                out[extra_cls].remove(extra_v)
                out.setdefault("arg_slot", []).append(extra_v)
    return {cls: vs for cls, vs in out.items() if vs}


def _fix_canto(
    canticle: str, number: int, n_cantos: int, model: str, ui: StatusLine,
    log_path: Path | None = None, whole: bool = True,
) -> Counter[str]:
    data = skel.load_skel(canticle, number)
    morph_rows = _morph_rows(canticle, number)
    np_rows = _np_rows(canticle, number)
    dep_rows = _dep_rows(canticle, number)
    case_rows = _case_rows(canticle, number)
    lines = api.canto(canticle, number).lines()
    text_by_no = {line.no: line.text for line in lines}
    nos_all = [line.no for line in lines]
    texts_all = [line.text for line in lines]
    out = dict(data)
    stats: Counter[str] = Counter()
    changed = False
    label = f"{canticle} {number}/{n_cantos}"

    def commit(rows_by_line: dict[int, list[skel.SkelRow]]) -> None:
        nonlocal changed
        for no, rows in rows_by_line.items():
            out[no] = tuple(rows)
        changed = True
        skel.write_skel(canticle, number,
                        [(no, list(rows)) for no, rows in sorted(out.items())])

    with ui.progress(len(lines), label=label) as prog:
        for unit in dep.sentence_groups(nos_all, texts_all, dep.MAX_UNIT_LINES):
            prog.update(unit[0])
            if any(no not in out for no in unit):
                continue
            unit_texts = [text_by_no[no] for no in unit]
            rows_by_line = {no: list(out[no]) for no in unit}

            def classify():
                return _classify_violations(unit, unit_texts, rows_by_line, morph_rows,
                                            np_rows, dep_rows, case_rows)

            _, soft = classify()
            if not soft:
                continue
            stats["units:flagged"] += 1
            opened = len(soft)

            for r in _apply_unit_repairs(unit, unit_texts, rows_by_line, morph_rows, np_rows,
                                         dep_rows, case_rows):
                stats[f"repair:{r.kind}"] += 1
            _, after_det = classify()
            if len(after_det) < len(soft):
                stats["removed:_deterministic"] += len(soft) - len(after_det)
                commit(rows_by_line)
                ui.log(f"Repaired {canticle} {number}:{unit[0]}-{unit[-1]} — "
                       f"{len(soft)} -> {len(after_det)} soft, no model call")
            soft = after_det
            if not soft:
                stats["units:cleared_deterministically"] += 1
                continue

            ctx = _UnitContext(unit, unit_texts, morph_rows, np_rows)
            by_class: dict[str, list[morph.Violation]] = {}
            for v in soft:
                by_class.setdefault(_violation_subclass(v, ctx), []).append(v)
            by_class = _split_slot_conflicts(by_class)
            moved = False
            for cls in _CLASS_ORDER:
                vs = by_class.get(cls)
                if not vs or cls not in _CLASS_PROMPTS:
                    continue
                stats[f"calls:{cls}"] += 1
                trial = _ask_class(cls, ctx, vs, rows_by_line, model, ui, label, log_path,
                                   stats)
                if trial is None:
                    continue
                hard_after, soft_after = _classify_violations(
                    unit, unit_texts, trial, morph_rows, np_rows, dep_rows, case_rows)
                if hard_after or not _is_improvement(soft, soft_after):
                    _log_rejection(log_path, label, unit, cls, soft, soft_after, hard_after)
                    continue
                stats[f"removed:{cls}"] += len(soft) - len(soft_after)
                rows_by_line = trial
                soft = soft_after
                moved = True
                commit(rows_by_line)
                ui.log(f"Fixed {canticle} {number}:{unit[0]}-{unit[-1]} [{cls}] — "
                       f"{len(soft_after)} soft left")
                if not soft:
                    break
            if moved:
                stats["units:improved_by_class"] += 1
            if not soft:
                stats["units:cleared"] += 1
                continue

            if not whole or moved:
                continue
            stats["calls:_whole"] += 1
            hint = _fix_hint(unit, unit_texts, soft, morph_rows)
            new_rows = _try_parse(unit, unit_texts, model, ui, label, log_path, morph_rows,
                                  np_rows, dep_rows, hint, case_rows, "_whole")
            if new_rows is None:
                continue
            _, soft_after = _classify_violations(
                unit, unit_texts, new_rows, morph_rows, np_rows, dep_rows, case_rows)
            if _is_improvement(soft, soft_after):
                stats["removed:_whole"] += len(soft) - len(soft_after)
                stats["units:improved_by_whole"] += 1
                commit({no: list(new_rows.get(no, [])) for no in unit})
                ui.log(f"Fixed {canticle} {number}:{unit[0]}-{unit[-1]} [whole] — "
                       f"{opened} -> {len(soft_after)} soft violation(s)")
            else:
                _log_rejection(log_path, label, unit, "whole", soft, soft_after, [])
    if changed:
        ui.log(f"Wrote: skel/{canticle}/{number:02d}.tsv")
    return stats


def fix(canticles: list[str], model: str, spec: str | None, log_path: Path | None = None,
        whole: bool = True) -> int:
    if log_path:
        log_path.write_text("", encoding="utf-8")
    ui = StatusLine()
    totals: Counter[str] = Counter()
    for canticle in canticles:
        n_cantos = len(api.cantos(canticle))
        for number in api.select_cantos(canticle, spec):
            if not skel.has_skel(canticle, number):
                continue
            totals += _fix_canto(canticle, number, n_cantos, model, ui, log_path, whole)
    _print_fix_summary(totals, log_path)
    return 0
