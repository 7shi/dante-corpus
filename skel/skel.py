"""Build driver for Layer 5 (predicate-argument skeleton) — a per-step generation script.

Like `dep/dep.py` (Layer 4), the script that *generates* an artifact lives in its own step
directory (here `skel/`), while parsing, resolution, validation, and I/O stay in the shared
package (`dante_corpus/skel.py`, consumed by the runtime API). The runtime API never calls a
model.

Unlike Layers 2-4, this layer's checker is *not* the LLM's own output reformatted: `skel.
derive_unit` computes the same predicate-argument structure mechanically from the frozen
Layers 2-4, and the LLM proposes its own, independent reading of the same parse unit — it is
deliberately **not shown** the Layer-4 parse, only the numbered source lines, a POS-annotated
token list (Layer 2), and the Layer-3 noun-phrase list as citation anchors. A divergence
between the two is triage material (see `dante_corpus/skel.py`'s module docstring and
PLAN.md), not necessarily an LLM mistake.

Parse units are the same sentence groups as Layer 4 (`dep.sentence_groups`, reused verbatim) —
staying unit-aligned with Layer 4 is what makes the divergence check meaningful.

Generation resumes from its own output: each parse unit's rows are written back to the TSV as
soon as they validate (zero hard violations), so an interrupted run continues where it stopped.

    uv run skel.py inferno -m ollama:gpt-oss        # all of Inferno (resumes)
    uv run skel.py inferno -c 1 -m ollama:gpt-oss   # just canto 1
    uv run skel.py inferno -c 12- -m ollama:gpt-oss # canto 12 on (resume after a failure)
    uv run skel.py inferno -c 11-15 --stats         # a canto range, inclusive
    uv run skel.py inferno --force -m ...           # rebuild from scratch
    uv run skel.py inferno --check                  # code-only, no model
    uv run skel.py inferno --stats                  # code-only; soft violations by class
    uv run skel.py inferno -n                        # dry run: show pending units, no LLM
    uv run skel.py inferno --clean                   # remove parse units with hard violations
    uv run skel.py inferno --repair                  # deterministic rewrites only, no model
    uv run skel.py inferno --fix -m ollama:gpt-oss   # reduce soft violations (three stages)
    uv run skel.py inferno --fix --no-whole -m ...   # ... without the regeneration fallback

`--fix` works in three stages, cheapest first: the deterministic rewrites that need no reading
(`--repair`'s own rules, run inline), then one narrow question per remaining violation *class* —
each with its own system prompt and its own small answer, spliced back in at row level — and
only then, for units neither stage moved, the whole-unit regeneration this mode originally
consisted of. Splitting by class is what lets an instruction reach the model at the flagged
position, and lets a unit keep the classes that were settled instead of discarding a partial
improvement.

`--check` validates committed artifacts against the deterministic derivation (`skel.
derive_unit`) and reports soft violations (role outside the frozen vocabulary, a nominal-role
argument heading no NP/pronoun/predicate, and — the central check — every divergence from
the derivation: `missing_tuple`/`extra_tuple`/`missing_arg`/`extra_arg`/`role_mismatch`).

`--log FILE` collects two things: the responses that failed to validate, and the model's own
`NOTE` lines — one per question it could not answer in the shape asked for (see the *field
notes* section below). The second is a discovery instrument, not telemetry: it names positions
worth reading without anyone having to read the canticle to find them.
"""

import argparse
import dataclasses
import re
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from dante_corpus import api, case, dep, morph, np, skel
from dante_corpus.tokenizer import has_alpha, tokenize
from llm7shi.statusline import StatusLine

SYSTEM_PROMPT = """\
You are a predicate-argument skeleton extractor for archaic Italian (Dante's Divine Comedy).
For the given sentence you receive numbered source lines, a numbered token list, and a list of
noun phrases. Output ONLY a Markdown table with one row per (predicate, argument) pair:
| Pred Line | Pred Token | Pred Word | Role | Arg Line | Arg Token | Arg Word |

Rules:
* A predicate is any token that heads a clause: a finite or non-finite verb, or a copular
  adjective/noun predicate (the thing an "è"/"era"/etc. links to).
* Role is one of: subj, obj, iobj, attr, xcomp, ccomp, obl:<preposition lemma> (e.g. obl:in,
  obl:per, obl:di); use bare obl only if there truly is no preposition to name.
* Pred Line / Pred Token / Pred Word are copied from the token list.
* Arg Line / Arg Token cite another listed token — prefer a noun phrase's head token when the
  argument is a noun phrase (use the Noun phrases list to find it); Arg Word is that token's
  word, copied verbatim, so the citation can be checked.
* A pro-drop (missing) subject of a finite verb is still reported as its own row: Role subj,
  Arg Line 0, Arg Token 0, Arg Word ∅.
* A NON-finite predicate (infinitive, participle, gerund) usually has no subject of its own: cite
  the token that controls it — the subject or object of the verb it depends on ("i' cominciai a
  dir" → subj of dir is i'; "vidi lui venire" → subj of venire is lui; the causee of fare/lasciare
  + infinitive; the noun a participle modifies). Use the ∅ row only when nothing in the sentence
  supplies a subject; do not write ∅ for a subject that is expressed elsewhere in the sentence.
* An ADVERB is never a predicate — not a comparative (più, meno, sì), not a locative (dentro,
  dinanzi, dietro, fuor); never open a row for it as Pred. But a LOCATIVE OR DIRECTIONAL adverb
  that answers *where* or *whither* for the verb IS one of its arguments and gets its own row:
  là, qui, qua, dentro, fuor, dinanzi, dietro, suso, giù, oltre, intorno, and the relative
  dove/ove/u'/v'. Give it as obl:<preposition> if a preposition is written, and as bare obl if
  none is ("Così girammo... **dentro**"). Only a manner, degree or negation adverb (più, non,
  ben, così, sì) is left out.
* attr is the role for a secondary predicate over an argument — an adjective or noun predicated of
  the verb's object or subject without its own copula ("faceva dir l'un ‘No’", "vidi lui contento").
  Give it as attr on the matrix verb; do not make it a predicate of its own.
* An ELIDED VERB OF SPEECH ("Ed elli a me: «…»", "E io a lui:", where the verb of saying is left
  out) is reported with the SUBJECT token itself as the predicate: Pred = elli / io / the speaker's
  noun, with Role subj Arg 0 0 ∅ (the verb is missing, so its own subject slot is empty), the
  quotation's main verb as ccomp, and the addressee as obl:a. Do not skip these frames — they are
  predicates even though no verb is written. The ADDRESSEE IS OPTIONAL: "E io: «Maestro, …»",
  "e quei: «Di rado …»" are the same frame with no a-phrase written, so they get the same Pred row
  and the same ccomp, just no obl:a. Never anchor the frame on the conjunction ("E", "Ed", "Ma") —
  the Pred token is the pronoun or noun that names the speaker.
* The same holds for any other VERBLESS clause: an exclamation or apposition predicated with no
  copula written ("e te cortese ch'ubidisti tosto", "mantoani per patrïa ambedui") has its noun or
  pronoun as the Pred token, with Role subj Arg 0 0 ∅.
* An ATTRIBUTIVE ADJECTIVE is not a predicate: "una lonza leggera", "l'antica Rachele", "persone
  ratte" open no Pred row of their own. Neither is an APPOSITIVE one — an adjective phrase set off
  by a comma from the noun it modifies ("grande campagna, piena di duolo e di tormento rio") is
  still that noun's modifier, not a clause. An adjective is a predicate only where a copula links
  it ("anima fia degna", "e pronti sono"); a secondary predicate over an argument is the matrix
  verb's attr, per the rule above.
* A predicate with no arguments at all gets exactly one row: Role -, Arg Line 0, Arg Token 0,
  Arg Word -.
* A relative pronoun (che, cui, qual, ...) that is a clause's subject/object/oblique is cited
  as the argument itself — never resolve it to its antecedent.
* A verb token that already contains a fused enclitic pronoun (e.g. venendomi = venire + mi)
  encodes that pronoun's role internally; do not add a separate row citing the pronoun or the
  predicate's own token position as its argument — there is no separate token for it.
* Arguments may be on a different line than the predicate — enjambment is common in this text.
* Output only the table, with no commentary before or after it — with ONE exception. If some part
  of the sentence cannot be given rows cleanly, output your best reading as rows anyway, and add
  note lines AFTER the table (never before it, never between rows), one per problem:
  N<line>.<token>: <what is wrong, in one sentence>
  Write one when the sentence offers nothing of the shape these rules ask for, when two analyses
  are equally defensible, or when the rules above do not fit what the sentence actually does — and
  only then. A note never replaces a row and never changes one; it is read separately by a human.

Example input:
Give the predicate-argument skeleton for this sentence:

1 Nel mezzo del cammin di nostra vita
2 mi ritrovai per una selva oscura,
3 ché la diritta via era smarrita.

Tokens (Line.Token Word (POS)):
1.1 Nel (preposition+article)
1.2 mezzo (noun)
1.3 del (preposition+article)
1.4 cammin (noun)
1.5 di (preposition)
1.6 nostra (adjective)
1.7 vita (noun)
2.1 mi (pronoun)
2.2 ritrovai (verb)
2.3 per (preposition)
2.4 una (article)
2.5 selva (noun)
2.6 oscura (adjective)
3.1 ché (conjunction)
3.2 la (article)
3.3 diritta (adjective)
3.4 via (noun)
3.5 era (verb)
3.6 smarrita (verb (past participle))

Noun phrases (Line.Head [text]):
1.2 [mezzo del cammin di nostra vita]
1.4 [cammin di nostra vita]
1.7 [nostra vita]
2.5 [una selva oscura]
3.4 [la diritta via]

Example output:
| Pred Line | Pred Token | Pred Word | Role | Arg Line | Arg Token | Arg Word |
|---|---|---|---|---|---|---|
| 2 | 2 | ritrovai | subj | 0 | 0 | ∅ |
| 2 | 2 | ritrovai | obl:in | 1 | 2 | mezzo |
| 2 | 2 | ritrovai | obl:per | 2 | 5 | selva |
| 3 | 6 | smarrita | subj | 3 | 4 | via |

Second example input (an elided verb of speech):
Give the predicate-argument skeleton for this sentence:

34 Ed elli a me: «Questo misero modo
35 tegnon l'anime triste di coloro

Tokens (Line.Token Word (POS)):
34.1 Ed (conjunction)
34.2 elli (pronoun)
34.3 a (preposition)
34.4 me (pronoun)
34.5 Questo (adjective)
34.6 misero (adjective)
34.7 modo (noun)
35.1 tegnon (verb)
35.2 l' (article)
35.3 anime (noun)
35.4 triste (adjective)
35.5 di (preposition)
35.6 coloro (pronoun)

Second example output:
| Pred Line | Pred Token | Pred Word | Role | Arg Line | Arg Token | Arg Word |
|---|---|---|---|---|---|---|
| 34 | 2 | elli | subj | 0 | 0 | ∅ |
| 34 | 2 | elli | ccomp | 35 | 1 | tegnon |
| 34 | 2 | elli | obl:a | 34 | 4 | me |
| 35 | 1 | tegnon | subj | 35 | 3 | anime |
| 35 | 1 | tegnon | obj | 34 | 7 | modo |
"""

RETRIES = 2


def _alpha_tokens(text: str) -> list[str]:
    return [t for t in tokenize(text) if has_alpha(t)]


def _units(lines: tuple[api.Line, ...], size: int) -> list[tuple[api.Line, ...]]:
    """Group a canto's lines into skeleton parse units (same sentence groups as Layer 4)."""
    nos = [line.no for line in lines]
    texts = [line.text for line in lines]
    by_no = {line.no: line for line in lines}
    return [tuple(by_no[no] for no in group) for group in dep.sentence_groups(nos, texts, size)]


def _load_committed(canticle: str, number: int) -> list[tuple[int, list[skel.SkelRow]]]:
    """Already-frozen rows for a canto, ordered by line number — the checkpoint to resume from."""
    if not skel.has_skel(canticle, number):
        return []
    data = skel.load_skel(canticle, number)
    return [(no, list(rows)) for no, rows in sorted(data.items())]


def _morph_rows(canticle: str, number: int) -> dict[int, list]:
    """Layer-2 rows per line, or {} when absent."""
    if not morph.has_morph(canticle, number):
        return {}
    return {no: list(rows) for no, rows in morph.load_morph(canticle, number).items()}


def _np_rows(canticle: str, number: int) -> dict[int, list]:
    """Layer-3 rows per line, or {} when absent."""
    if not np.has_np(canticle, number):
        return {}
    return {no: list(rows) for no, rows in np.load_np(canticle, number).items()}


def _dep_rows(canticle: str, number: int) -> dict[int, list]:
    """Layer-4 rows per line, or {} when absent."""
    if not dep.has_dep(canticle, number):
        return {}
    return {no: list(rows) for no, rows in dep.load_dep(canticle, number).items()}


def _case_rows(canticle: str, number: int) -> dict[int, list]:
    """Layer-2 `case`-annex rows per line, or {} when absent — the third read rule U consumes
    (see `skel._case_corroborated_role`). Sparse: a line with no pronoun has no key."""
    if not case.has_case(canticle, number):
        return {}
    return {no: list(rows) for no, rows in case.load_case(canticle, number).items()}


def _merge_tables(text: str) -> str:
    """Merge multiple Markdown pipe-tables into one (shared recovery pattern; see PLAN.md).

    Handles two failure modes:
    - Blank line between tables: gap + repeated header + separator are removed.
    - No blank line: repeated header appears inline within the body and is removed in place.
    In both cases trailing blank lines before the repeated header are also stripped.
    """
    lines = text.splitlines(keepends=True)
    out: list[str] = []
    first_header: list[str] | None = None

    i = 0
    while i < len(lines):
        stripped = lines[i].rstrip()
        if stripped.startswith("|"):
            cells = [c.strip() for c in stripped.split("|")[1:-1]]
            if (first_header is not None
                    and cells == first_header
                    and i + 1 < len(lines)
                    and lines[i + 1].rstrip().startswith("|")
                    and "---" in lines[i + 1]):
                while out and out[-1].rstrip() == "":
                    out.pop()
                i += 2
                continue
            if (first_header is None
                    and i + 1 < len(lines)
                    and lines[i + 1].rstrip().startswith("|")
                    and "---" in lines[i + 1]):
                first_header = cells
            out.append(lines[i])
        else:
            out.append(lines[i])
        i += 1

    return "".join(out)


# --- Field notes: the model's own report on a question it could not answer cleanly ------------
#
# Every instrument in this file asks for an answer of a fixed shape, and every one of them is
# answerable in that shape whether or not the sentence supports it: asked *which token is this
# predicate's `subj`*, a model with no way to say "none of them, and here is why" names a token.
# The residue's own shape says this happens — the sixth round left 62 subject positions, 13 of
# them `subj` <-> `obj` in both directions on one predicate — and six rounds of per-class numbers
# cannot tell a wrong answer from an unanswerable question, because both look like a violation
# that did not move.
#
# So every prompt now carries one extra, *conditional* slot: a note line for a question the
# sentence does not support, one where two answers are equally defensible, or one whose convention
# does not fit. Three properties keep it honest, and each is stated in the prompts themselves:
#
#   * It is not an escape hatch. The model still answers every question, so a note cannot buy its
#     way out of the work — which is the failure mode an optional "report if you cannot" invites.
#   * It changes nothing. Notes are stripped before the answer reaches `prompt.apply` or
#     `skel.resolve_chunk`, so splices, the acceptance gate and a round's per-class numbers are
#     bit-for-bit what they were without this. A round remains comparable with the six before it.
#   * It is a hypothesis about the *question*, never evidence about the corpus. What it buys is a
#     position to read — `uv run read.py <canticle> <canto> <line>` — chosen by something other
#     than reading all 100 cantos to find it.
#
# One tab-separated line per note, so a round's log is counted without a parser:
#
#     grep '^NOTE' skel.log | cut -f4 | sort | uniq -c    # which class reports the most
#     grep '^NOTE' skel.log | cut -f2,3,5                 # positions to hand to read.py

_NOTE_RE = re.compile(r"^[ \t]*N(\d+)(?:[ \t]*\.[ \t]*(\d+))?[ \t]*[:.)][ \t]*(.+?)[ \t]*$",
                      re.MULTILINE)


@dataclass(frozen=True)
class _FieldNote:
    """One report. `index` is the question number it answers back to (the `_ASK_HEADER` classes,
    which number their questions); `pos` is the token it cites (the table classes, which do not).
    Exactly one of the two is set."""

    index: int | None
    pos: tuple[int, int] | None
    text: str


def _split_field_notes(text: str) -> tuple[str, list[_FieldNote]]:
    """Take the `N…` lines out of a response and return them beside the response without them.

    The removal is what makes this instrument inert. `_parse_answers` never matched an `N` line
    anyway, but the table classes hand the whole response to `skel.resolve_chunk`, and a note left
    in place would reach a parser that has never seen one.
    """
    notes: list[_FieldNote] = []
    for m in _NOTE_RE.finditer(text):
        body = " ".join(m.group(3).split())
        if not body:
            continue
        pos = (int(m.group(1)), int(m.group(2))) if m.group(2) else None
        notes.append(_FieldNote(None if pos else int(m.group(1)), pos, body[:300]))
    return _NOTE_RE.sub("", text), notes


def _log_field_notes(
    log_path: Path | None, label: str, nos: list[int], cls: str, notes: list[_FieldNote],
    anchors: dict[int, str] | None = None,
    word_at: Callable[[tuple[int, int]], str] | None = None,
) -> None:
    """Append one line per note. Written for accepted and rejected candidates alike, and for a
    call that validated first time, because the note is about the *question* rather than about
    what became of the answer."""
    if not log_path or not notes:
        return
    with log_path.open("a", encoding="utf-8") as f:
        for note in notes:
            if note.pos is not None:
                word = word_at(note.pos) if word_at else "?"
                anchor = f"{note.pos[0]}.{note.pos[1]} '{word}'"
            else:
                anchor = (anchors or {}).get(note.index, "-")
            f.write(f"NOTE\t{label}\t{nos[0]}-{nos[-1]}\t{cls}\t{anchor}\t{note.text}\n")


def _prompt(
    nos: list[int], texts: list[str], morph_rows: dict[int, list], np_rows: dict[int, list],
    hint: str | None = None,
) -> str:
    lines_block = "\n".join(f"{no} {text}" for no, text in zip(nos, texts))
    token_lines: list[str] = []
    for no, text in zip(nos, texts):
        tokens = _alpha_tokens(text)
        rows = morph_rows.get(no)
        for i, tok in enumerate(tokens, start=1):
            pos = f" ({rows[i - 1].pos})" if rows and i - 1 < len(rows) else ""
            token_lines.append(f"{no}.{i} {tok}{pos}")
    np_lines: list[str] = []
    for no in nos:
        for span in sorted(np_rows.get(no, ()), key=lambda s: (s.start, -s.end)):
            np_lines.append(f"{no}.{span.head} [{span.text}]")
    parts = [
        "Give the predicate-argument skeleton for this sentence:\n\n" + lines_block,
        "Tokens (Line.Token Word (POS)):\n" + "\n".join(token_lines),
    ]
    if np_lines:
        parts.append("Noun phrases (Line.Head [text]):\n" + "\n".join(np_lines))
    if hint:
        parts.append(hint)
    return "\n\n".join(parts)


# --- --fix hints (Phase 4b): point a regeneration attempt at what needs re-reading, without ----
# --- revealing the derivation's actual answer (arg citations), so it isn't just parroted back ---

_HINT_PHRASING = {
    "missing_tuple": "may be missing a predicate near '{word}' ({line}.{token}) — check whether "
                      "it heads its own clause",
    # The promoted head of an elided verb of speech is a pronoun/noun, so the generic phrasing
    # above ("check whether it heads its own clause") asks the wrong question: the token is a
    # subject, and what is missing is the frame around it. 63 of the 94 surviving `missing_tuple`
    # violations cite a pronoun (io, elli) and 16 a noun — see CORRECTIONS.md's Phase 5v.
    "missing_tuple_nominal": "'{word}' ({line}.{token}) may head a VERBLESS clause — most often "
                             "the subject of an elided verb of speech (then: subj ∅, the quotation "
                             "as ccomp, the addressee as obl:a), otherwise a noun or pronoun "
                             "predicated with no copula written ('e te cortese', 'mantoani per "
                             "patrïa ambedui'). Either way it is itself the predicate row",
    "extra_tuple": "the predicate '{word}' ({line}.{token}) you proposed may not be warranted — "
                   "reconsider whether it is really an independent predicate",
    # Two POS-keyed variants. Phase 5w measured that a prose rule already in the prompt does not
    # move its class unless an instruction also reaches the model at the flagged position: the
    # adverb rule was in the prompt throughout and 33 adverb `extra_tuple`s survived it.
    "extra_tuple_adverb": "'{word}' ({line}.{token}) is an ADVERB, so it is never a predicate — "
                          "cite it as an argument of the verb it modifies, or leave it out, but "
                          "do not open a Pred row for it",
    "extra_tuple_adjective": "'{word}' ({line}.{token}) is an adjective, and an adjective is a "
                             "predicate only when a copula links it ('è degna', 'son presto') — an "
                             "attributive one modifying a noun is not. If it is predicated of "
                             "something, give it as attr/xcomp on that verb rather than a Pred row",
    "missing_arg": "the predicate '{word}' ({line}.{token}) may be missing a '{role}' argument — "
                   "check for one",
    # A fourth POS-keyed variant, again on the argument's POS. `_CONV_ADVERB`'s old closing clause
    # ("or it is left out") gave blanket licence to omit an adverb argument; Layer 4 has no such
    # licence, and the Inferno 7-10 read measured 82 `missing_arg` positions whose argument is an
    # adverb — almost all locatives. The phrasing must not name the position (independence rule),
    # so it names the *kind* of word to look for.
    "missing_arg_adverb": "the predicate '{word}' ({line}.{token}) may be missing a '{role}' "
                          "argument — a locative or directional adverb (là, fuor, dentro, dinanzi, "
                          "suso, dove, ...) answering where/whither for it counts as one, and is "
                          "not to be skipped as a mere modifier",
    # The subject branches (see `_CONV_SUBJECT`). Neither may name the derivation's own position,
    # so each names what to re-read for instead: where a written subject may stand, and which
    # tokens cannot be one.
    "missing_arg_subject": "the predicate '{word}' ({line}.{token}) may be missing its SUBJECT — "
                           "look after the verb as well as before it, and remember a verb joined "
                           "by e/né/ma to an earlier one shares that one's written subject",
    "extra_arg_subject": "the SUBJECT currently given for '{word}' ({line}.{token}) may be wrong — "
                         "check whether the sentence writes one after the verb, and that what is "
                         "cited is not an unstressed clitic (lo, la, 'l, mi, si, ne)",
    "extra_arg": "the predicate '{word}' ({line}.{token})'s '{role}' argument may not belong — "
                "recheck it",
    # A third POS-keyed variant, on the argument's POS rather than the predicate's — rule AG's
    # write-up (CORRECTIONS.md) found this shape at inferno 6:70 ("Alte terrà... le fronti"):
    # Layer 4 attaches the adjective `amod` inside the object NP, the LLM reads it as a depictive
    # secondary predicate (`xcomp`/`attr`) of the verb. Same misreading as `extra_tuple_adjective`,
    # one level down — the adjective isn't promoted to its own Pred row, just wrongly attached as
    # an argument of one. 65 of the corpus's 107 `extra_arg xcomp`/`attr` violations cite an
    # adjective as the argument.
    "extra_arg_adjective": "'{word}' ({line}.{token})'s argument at the '{role}' slot may be an "
                           "ATTRIBUTIVE adjective, not a secondary predicate of it — an "
                           "attributive adjective modifying a noun inside that argument's own "
                           "phrase is not a separate predication",
    "role_mismatch": "the predicate '{word}' ({line}.{token})'s argument currently labeled "
                     "'{given_role}' may need a different role — recheck it",
    # Rule EG. Internal to the reading, so the hint may state the contradiction outright: nothing
    # about the derivation is disclosed by saying the same token was given two roles.
    "dual_role": "one token has been given TWO roles ('{role}' and '{given_role}') for the "
                 "predicate '{word}' ({line}.{token}) — one token fills one role, unless it is a "
                 "fused clitic (gliel' = gli + lo, sen = si + ne)",
}


def _fix_hint(
    nos: list[int], texts: list[str], violations: list[morph.Violation],
    morph_rows: dict[int, list] | None = None,
) -> str | None:
    """Summarize a prior attempt's divergence violations into a re-read hint: which predicates
    and role slots to re-examine, without citing the derivation's actual argument positions —
    the model still reads the sentence independently, it just isn't blind on a retry."""
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
            # The two POS-keyed variants above: 33 of the 91 surviving `extra_tuple` violations
            # cite an adverb and 37 an adjective (see CORRECTIONS.md's rules Y-AF).
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


# --- Stage 2: class-targeted pinpoint questions ---------------------------------------------
#
# `--fix`'s original instrument regenerated a whole parse unit from one monolithic prompt and
# kept the result only if the *entire* unit improved. Phase 5w measured what that costs: 1290
# calls removed 123 violations, and the one class whose instruction had been rewritten moved six
# times the pass average while the rest did not move at all. The finding it recorded — a pass
# moves a class only when something about *that class* changed — is an argument against ever
# asking one prompt to fix everything at once.
#
# So a flagged unit is not regenerated here. Its violations are grouped by class, and each group
# gets its own short system prompt (only the conventions bearing on that class), its own narrow
# question, and its own small answer, spliced back in at row level and re-validated on its own.
# Two consequences: an instruction always reaches the model at the flagged position, and a unit
# with five violations where one class is settled keeps that gain instead of discarding it.
#
# The independence rule the module docstring states still binds. A question may name the
# predicate, the argument the LLM itself cited, and the role slot under dispute — exactly what
# `_fix_hint` already discloses — but must NEVER cite the derivation's own argument position,
# which would reduce the model to confirming Layer 4. `test_class_question_never_leaks_derived_
# argument` pins this.


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
        """The whole-unit POS map in the shape `dante_corpus.skel`'s rule gates take, so a splice
        guard can consult one of those rules (rule AL, in `_apply_missing_arg`) instead of
        re-implementing its condition."""
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
    """Read back `Q<n>: <answer>` lines, ignoring any prose the model wrapped them in."""
    return {int(n): body.strip().strip("`*") for n, body in _ANSWER_RE.findall(text)}


# The one answer each class's own vocabulary defines as *leave the artifact as it is*. A response
# made entirely of these is the model's verdict — "the checker is wrong here" — and not a response
# the driver failed to parse. `role_mismatch` has no such word: standing pat there is answering the
# role the artifact already carries, which `_is_refusal` compares against `given_role`.
#
# Round 7 measured what this distinction is worth: 101 of 332 calls produced no splice, and 57 of
# them were an answer from this table (`skel/PLAN.md` §30 finding 3). Filing those as unusable threw
# away a position-by-position list of where the model thinks `--check` is wrong.
_STAND_PAT = {
    "extra_arg": "keep", "extra_arg_subject": "keep", "extra_arg_adjective": "keep",
    "arg_slot": "keep",
    "missing_arg": "none", "missing_arg_adverb": "none", "missing_arg_subject": "none",
    "dual_role": "both",
    "extra_tuple": "yes", "extra_tuple_adverb": "yes", "extra_tuple_adjective": "yes",
}


def _is_refusal(cls: str, vs: list[morph.Violation], text: str) -> bool:
    """Whether a response that changed nothing is the model **standing by its reading**.

    Deliberately strict: it must have answered, and *every* answer it gave must be one that asserts
    the artifact as written. Anything else — an unparseable response, or an answer that tried to
    change something the splice could not use — is not a refusal, because the model did not decline.
    A `drop` that failed to apply is a splice failure, not a verdict.

    Question numbers are only consulted for `role_mismatch`, whose questions are one per violation.
    `arg_slot` asks one question for a *pair*, so the count of answers is not compared to `vs`.
    """
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
    """Parse a `<line>.<token>` citation; `0.0` is the ∅ sentinel and parses as (0, 0)."""
    m = _TOKEN_REF_RE.match(answer.strip().strip("'\"“”"))
    return (int(m.group(1)), int(m.group(2))) if m else None


def _rows_of_predicate(rows_by_line, pos: tuple[int, int]) -> list[skel.SkelRow]:
    return [r for r in rows_by_line.get(pos[0], []) if (r.line, r.token) == pos]


def _find_arg_row(rows_by_line, pos: tuple[int, int], role: str, arg: tuple[int, int]):
    """The committed row a violation refers to. Roles are compared canonicalized, because a
    violation reports the canonical role while the row may hold any spelling of it."""
    for row in _rows_of_predicate(rows_by_line, pos):
        if (row.arg_line, row.arg_token) == arg and skel._canonicalize_role(row.role) == role:
            return row
    return None


# The shared half of every class prompt: what the model is looking at and how to answer.
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


# Conventions lifted verbatim from SYSTEM_PROMPT, so a class prompt states the corpus's frozen
# reading of its own subject rather than paraphrasing it. Each class assembles only the ones
# that bear on it — that selectivity is the whole point of splitting the prompt up.
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

# The argument-side half of the adverb convention. `_CONV_ADVERB` bans adverb *predicates*, and
# its old closing clause ("or it is left out") also handed the model blanket licence to omit an
# adverb argument — which Layer 4 does not have: wherever it attaches an adverb with deprel `obl`,
# the derivation emits an oblique. That licence was measured as 82 `missing_arg` positions across
# the corpus, almost all of them locatives (là, fuor, dentro, dinanzi, dove, suso, …), the largest
# unbranched bucket in the residue at the Inferno 7-10 read.
_CONV_ADVERB_ARG = """\
A LOCATIVE OR DIRECTIONAL adverb — là, qui, qua, dentro, fuor, dinanzi, dietro, suso, giù, oltre, \
intorno, and the relative dove/ove/u'/v' — that answers *where* or *whither* for the verb IS one \
of its arguments, not a modifier to be skipped: cite it as `obl:<preposition>` if a preposition is \
written and as bare `obl` if none is. Only a manner, degree or negation adverb (più, non, ben, \
così, sì) is left out.\
"""

# The subject slot's own convention. `_CONV_PRODROP` tells the model a pro-drop subject is a real
# slot, and nothing tells it where a *written* subject may stand — so the two largest buckets in
# the residue are both subjects: 153 `extra_arg subj` (45 of them asserting pro-drop over a
# subject the sentence writes) and 103 `missing_arg subj`. The Inferno 11-15 read found three
# recurring causes, one per sentence below: postverbal subjects read as predicate nominals
# ("no i fia riguardo" 11:12, "Bene ascolta chi la nota" 15:99), a proclitic object read as the
# subject ("poco par che 'l pregi" 14:70), and a coordination whose subject is written once at
# its head ("Quei fu l'un d'i sette regi; ed ebbe e par ch'elli abbia…" 14:69).
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

# One predicate may fill the same slot twice, and the model tends to answer only once. "pur a
# sinistra, giù calando al fondo" (inferno 14:126) gives `calando` two `obl:a` phrases and the
# reading lists one; the same shape accounts for part of the 76 standing `missing_arg obl`.
_CONV_REPEATED = """\
A predicate may carry the SAME role twice, and each occurrence needs its own row: two obliques \
with the same preposition ("pur a sinistra, giù calando al fondo"), two objects, two places. \
Having already listed one filler of a slot is not a reason to leave a second one out.\
"""

# The convention clause the Purgatorio 16-20 read proposed and the Paradiso 11-20 read finally
# wrote (2026-08-17). Its target is `missing_arg obl*`, still the residue's largest single bucket
# (57 of 261 when the Paradiso 6-10 batch last measured it). Layer 4 attaches a prepositional
# phrase of time, place or manner to the verb with deprel `obl`, so the derivation always emits an
# oblique for it; the reading treats it as scene-setting and leaves it out. Evidence from the
# Paradiso 11-20 read: "a guisa del parlar di quella vaga" (12:14), "in quel che, forato da la
# lancia" (13:40, the second of two coordinate obliques), "tale dal corno che 'n destro si stende"
# (15:19), "qual era tra i cantor del cielo artista" (18:51).
_CONV_ADJUNCT = """\
A PREPOSITIONAL PHRASE hanging on the verb is one of its arguments even when it only sets the \
scene — a place ("tra i cantor del cielo", "in quel che forato fu"), a source ("dal corno che 'n \
destro si stende"), a time, or a manner ("a guisa del parlar di quella vaga"). Cite it as \
`obl:<preposition lemma>` at the head noun of the phrase. Being inessential to the sense, or \
standing far from its verb, or already having a comparison or a relative clause of its own, is \
not a reason to leave it out.\
"""

# The same omission one clitic over, and a finding of the Paradiso 11-20 read itself: three of
# that batch's positions (17:102 "ch'io **le** porsi ordita", 17:110 "se loco **m'**è tolto",
# 20:35 "l'occhio in testa **mi** scintilla") are a non-core dative clitic Layer 4 records and the
# reading drops. It surfaces as `missing_arg obl:a`, so a round can score it apart from
# `_CONV_ADJUNCT` above even though both hang on the generic `missing_arg` class.
#
# **The sixth round measured the first wording at -8.3%, and the wording was the reason** (2026-08-18).
# It ended "Cite it as `iobj` at its own token position" — an instruction the class it hangs on
# cannot carry out. The generic `missing_arg` question asks *which token* fills a named slot
# (`_ask_missing_arg`) and `_apply_missing_arg` splices the role from the violation, not from the
# answer; the slot named at these positions is `obl:a`, because that is what the derivation emits
# for a bare dative clitic (rule AB). So the clause was telling the model to write a role the
# question never asks for, while the checker's own name for that slot went unmentioned. Rewritten to
# name the slot the way the question does and to say nothing about a role the answer cannot set.
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
    """One violation class's own instrument: what the model is told, what it is asked, and how
    its answer becomes rows. Keyed by `_violation_class` (plus the POS refinements `_fix_hint`
    already makes), so adding a class means adding an entry, not editing a shared prompt."""

    system: str
    ask: Callable      # (ctx, violations) -> question text
    apply: Callable    # (ctx, violations, rows_by_line, answer_text) -> bool (anything changed)


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
        line, token = v.predicate
        new = skel.SkelRow(line, token, ctx.word(v.predicate), v.role, arg[0], arg[1])
        rows = rows_by_line.setdefault(line, [])
        if new in rows:
            continue
        # **Rule EG's splice guard.** This class appends a row and never removes the one it may
        # contradict, so answering "which token is its subj" with a token the predicate already
        # holds in another role writes one token into two roles of one predicate — the artifact
        # contradicting itself, which no divergence check can see. The sixth `--fix` round did
        # exactly that at paradiso 1:81 (`alcun` as both `subj` and `obj` of `fece`) and the
        # per-unit acceptance gate let it through because the unit netted an improvement. The
        # licensed exception is rule AL's fused clitic, and it is licensed by that rule's own gate
        # rather than by a condition copied here; anything else is refused at the splice.
        if any((r.line, r.token) == (line, token) and (r.arg_line, r.arg_token) == arg
               and r.role != v.role
               and not skel._fused_clitic_dual_role(r.role, v.role, arg,
                                                    ctx.morph_pos_by_position(), None)
               for r in rows):
            continue
        rows.append(new)
        changed = True
    return changed


# --- arg_slot: the two sides of one slot, asked once -----------------------------------------

def _ask_arg_slot(ctx: _UnitContext, vs: list[morph.Violation]) -> str:
    """A predicate carrying **both** a `missing_arg` and an `extra_arg` on the *same* role is one
    disagreement — *which token fills this slot* — and `_CLASS_ORDER` used to ask it twice, in two
    separate calls that could not see each other: the `extra_arg` question offers `keep` and the
    `missing_arg` question invites the token the reading already wrote, so neither answer alone can
    remove both rows and the pair sat frozen through three rounds (16 of the 174 positions the sixth
    round left, on 8 predicates).

    One question instead, and still inside the independence rule: it names the predicate, the slot,
    and the filler **the reading itself supplied** — never the derivation's.
    """
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


# --- dual_role: the artifact contradicting itself (rule EG) ----------------------------------

def _ask_dual_role(ctx: _UnitContext, vs: list[morph.Violation]) -> str:
    """Rule EG's repair question. The violation is internal to the reading — one token written into
    two roles of one predicate — so the question can quote both rows verbatim without telling the
    model anything about the derivation."""
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


# --- extra_tuple (three POS-keyed variants sharing one question shape) ------------------------

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


# --- missing_tuple (answered as a table, because whole rows are being added) ------------------

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
    """The nominal branch's own question. The generic one asks whether the token "heads a clause
    of its own", which a bare `io`/`elli` visibly does not — so the model answers no and
    `_CONV_VERBLESS` never gets applied at the flagged position, which is exactly the failure
    Phase 5w describes and which round 3 measured (`missing_tuple_nominal` 39 -> 36, the
    survivors position-identical). This question states the frame instead of asking about it.
    """
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
        "and the addressee, if one is written, as `obl:a`. Output nothing only if the token is "
        "genuinely an argument of some other predicate already listed. Output rows for these "
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
                continue  # only the predicates that were asked about
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
    # The class is keyed on the *argument's* POS, which the question may not name (the
    # independence rule) — so the convention block, not the question, is what points the model at
    # the adverb. It reads the sentence and supplies the position itself, exactly as for the
    # generic `missing_arg`.
    "missing_arg_adverb": _ClassPrompt(
        system=f"{_ASK_HEADER}\n{_CONV_ADVERB_ARG}\n\n{_CONV_ROLES}\n\n{_CONV_REPEATED}",
        ask=_ask_missing_arg, apply=_apply_missing_arg),
    # The two subject branches. Same instruments as their generic parents — only the convention
    # block and the hint change, which is the shape `missing_arg_adverb` was built in and the
    # third round measured at -66.3%.
    "missing_arg_subject": _ClassPrompt(
        system=f"{_ASK_HEADER}\n{_CONV_SUBJECT}\n\n{_CONV_PRODROP}\n\n{_CONV_ROLES}",
        ask=_ask_missing_arg, apply=_apply_missing_arg),
    "extra_arg_subject": _ClassPrompt(
        system=f"{_ASK_HEADER}\n{_CONV_SUBJECT}\n\n{_CONV_PRODROP}\n\n{_CONV_ROLES}",
        ask=_ask_extra_arg, apply=_apply_extra_arg),
    # One slot, one question. See `_ask_arg_slot`: the two sides of a filler dispute used to be two
    # calls that could not see each other, and neither answer alone could clear the pair.
    "arg_slot": _ClassPrompt(
        system=f"{_ASK_HEADER}\n{_CONV_ROLES}\n\n{_CONV_SUBJECT}\n\n{_CONV_PRODROP}\n\n"
               f"{_CONV_RELPRON}",
        ask=_ask_arg_slot, apply=_apply_arg_slot),
    # Rule EG's class: the artifact contradicting itself, so the question may quote both rows.
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
    # `membership` and `unknown_role` have no entry on purpose. `_fix_hint` has always skipped
    # them (they carry no predicate), rule AF closed the membership question down to 8 positions,
    # and `unknown_role` stands at 0 — there is nothing for a prompt to move.
}


def _violation_subclass(v: morph.Violation, ctx: _UnitContext) -> str:
    """`_violation_class` plus the two POS refinements, which is the key `_CLASS_PROMPTS` and
    `_HINT_PHRASING` are both keyed by. Phase 5w measured that these two splits matter: an
    adverb and an adjective wrongly promoted to a predicate need opposite instructions."""
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
    # The subject slot's own branch, on the *role* rather than a POS — see `_CONV_SUBJECT`.
    if kind in ("missing_arg", "extra_arg") and (v.role or v.given_role) == "subj":
        return f"{kind}_subject"
    return kind


def _ask_class(
    cls: str, ctx: _UnitContext, vs: list[morph.Violation],
    rows_by_line: dict[int, list[skel.SkelRow]], model: str, ui: StatusLine, label: str,
    log_path: Path | None = None, stats: Counter[str] | None = None,
) -> dict[int, list[skel.SkelRow]] | None:
    """Put one class's question to the model and splice the answer into a *copy* of the unit's
    rows. Returns the modified copy, or None if the model said nothing actionable.

    Acceptance is the caller's job — this only produces a candidate.
    """
    from llm7shi import Client

    prompt = _CLASS_PROMPTS[cls]
    question = prompt.ask(ctx, vs)
    client = Client(model=model, file=ui.stream, show_params=False)
    client.set_system_prompt(prompt.system)
    ui.log("")
    answer = client(question).text
    ui.stream.end()
    # The field notes come out before anything else looks at the response: `apply` must see the
    # same text it would have seen without this instrument. The question number a note answers
    # back to is resolved here, where `vs` still gives its predicate and role slot.
    answer, notes = _split_field_notes(answer)
    _log_field_notes(
        log_path, label, ctx.nos, cls, notes,
        {i: f"{ctx.cite(v.predicate)} {v.role or v.given_role or '-'}"
         for i, v in enumerate(vs, start=1) if v.predicate is not None},
        ctx.word,
    )
    trial = {no: list(rows) for no, rows in rows_by_line.items()}
    if not prompt.apply(ctx, vs, trial, answer):
        # Two different outcomes wore one label until 2026-08-18. A **refusal** is an answer —
        # the model asserting the artifact against the checker — and its census is a reading list;
        # an **unusable** response is one the driver could not act on. Only the second is a failure.
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


def _continue_if_missing(
    client, nos: list[int], texts: list[str], table_text: str, ui: StatusLine,
    derived: dict[int, list[skel.SkelRow]],
) -> str:
    """If any derived predicate got no row (likely truncation), ask the client to continue."""
    try:
        partial, _ = skel.resolve_chunk(nos, texts, table_text)
    except ValueError:
        return table_text
    have = {(row.line, row.token) for rows in partial.values() for row in rows if row.token > 0}
    missing: list[str] = []
    for no in nos:
        tokens = _alpha_tokens(texts[nos.index(no)])
        for row in derived.get(no, []):
            if (row.line, row.token) not in have:
                word = tokens[row.token - 1] if 1 <= row.token <= len(tokens) else row.word
                missing.append(f"{no}.{row.token} {word}")
    missing = sorted(set(missing))
    if not missing:
        return table_text
    cont_prompt = (
        "The table was truncated. Please continue with rows for these predicates:\n\n"
        + "\n".join(missing)
    )
    ui.log("")
    cont_text = client(cont_prompt).text
    ui.stream.end()
    cont_text, _ = _split_field_notes(cont_text)  # a truncation repair, not a question
    return _merge_tables(table_text + "\n" + cont_text)


def _hard_violations(
    nos: list[int], texts: list[str], rows_by_line: dict[int, list[skel.SkelRow]],
    mismatches: list[str], morph_rows: dict[int, list] | None,
    np_rows: dict[int, list] | None, dep_rows: dict[int, list] | None,
) -> list[str]:
    hard = list(mismatches)
    for v in skel.validate_unit(nos, texts, rows_by_line, morph_rows, np_rows, dep_rows):
        if v.kind != "tag":
            hard.append(f"{v.line}:[{v.kind}] {v.detail}")
    return hard


def _try_parse(
    nos: list[int], texts: list[str], model: str, ui: StatusLine, label: str,
    log_path: Path | None = None, morph_rows: dict[int, list] | None = None,
    np_rows: dict[int, list] | None = None, dep_rows: dict[int, list] | None = None,
    hint: str | None = None, case_rows: dict[int, list] | None = None,
    note_class: str = "_build",
) -> dict[int, list[skel.SkelRow]] | None:
    """Call LLM and resolve; return rows-by-line on success, None after all retries fail.

    `hint` (set only by `--fix`, see `_fix_hint`) points a regeneration attempt at which
    predicates/roles a prior attempt got wrong, without citing the derivation's actual argument
    positions — `build`'s initial parse never gets one, preserving the independent-reading
    design the module docstring describes.

    `note_class` is the column a field note is filed under: `_build` for the initial parse,
    `_whole` for `--fix`'s stage-3 regeneration, matching `calls:_whole` in the fix summary.
    """
    from llm7shi import Client

    token_lists = {no: _alpha_tokens(t) for no, t in zip(nos, texts)}

    def word_at(pos: tuple[int, int]) -> str:
        tokens = token_lists.get(pos[0])
        return tokens[pos[1] - 1] if tokens and 1 <= pos[1] <= len(tokens) else "?"

    derived = (
        skel.derive_unit(nos, dep_rows, morph_rows, case_rows) if dep_rows is not None and morph_rows is not None
        else {}
    )
    prompt = _prompt(nos, texts, morph_rows or {}, np_rows or {}, hint)
    for attempt in range(RETRIES + 1):
        client = Client(model=model, file=ui.stream, show_params=False)
        client.set_system_prompt(SYSTEM_PROMPT)
        ui.log("")
        table_text = client(prompt).text
        ui.stream.end()
        table_text, notes = _split_field_notes(table_text)
        _log_field_notes(log_path, label, nos, note_class, notes, word_at=word_at)
        table_text = _merge_tables(table_text)
        table_text = _continue_if_missing(client, nos, texts, table_text, ui, derived)
        try:
            rows_by_line, mismatches = skel.resolve_chunk(nos, texts, table_text)
            hard = _hard_violations(nos, texts, rows_by_line, mismatches, morph_rows, np_rows, dep_rows)
            if hard:
                raise ValueError("; ".join(hard))
            return rows_by_line
        except ValueError as exc:
            msg = (f"  {label} lines {nos[0]}-{nos[-1]}: {exc} "
                   f"(attempt {attempt + 1}/{RETRIES + 1})")
            ui.stream.error(msg)
            if log_path:
                with log_path.open("a", encoding="utf-8") as f:
                    f.write(f"=== {label} lines {nos[0]}-{nos[-1]} "
                            f"attempt {attempt + 1}/{RETRIES + 1} ===\n")
                    f.write(f"Error: {exc}\n")
                    f.write("--- response ---\n")
                    f.write(table_text.strip())
                    f.write("\n\n")
    return None


def _classify_violations(
    nos: list[int], texts: list[str], rows_by_line: dict[int, list[skel.SkelRow]],
    morph_rows: dict[int, list] | None, np_rows: dict[int, list] | None,
    dep_rows: dict[int, list] | None, case_rows: dict[int, list] | None = None,
) -> tuple[list[morph.Violation], list[morph.Violation]]:
    """Split validate_unit results into (hard, soft). tag -> soft; rest -> hard."""
    hard, soft = [], []
    for v in skel.validate_unit(nos, texts, rows_by_line, morph_rows, np_rows, dep_rows, case_rows):
        (soft if v.kind == "tag" else hard).append(v)
    return hard, soft


def _build_canto(
    canticle: str, number: int, n_cantos: int, model: str, size: int,
    force: bool, dry_run: bool, ui: StatusLine, log_path: Path | None = None,
) -> bool:
    canto = api.canto(canticle, number)
    lines = canto.lines()
    out = [] if force else _load_committed(canticle, number)
    done = {no for no, _ in out}
    morph_rows = _morph_rows(canticle, number)
    np_rows = _np_rows(canticle, number)
    dep_rows = _dep_rows(canticle, number)
    case_rows = _case_rows(canticle, number)

    units = _units(lines, size)
    pending = [unit for unit in units if any(line.no not in done for line in unit)]
    label = f"{canticle} {number}/{n_cantos}"
    if not pending:
        ui.log(f"[dim]Skip (complete): skel/{canticle}/{number:02d}.tsv[/dim]")
        return True
    if done:
        ui.log(f"Resume: skel/{canticle}/{number:02d}.tsv "
               f"({len(done)} line(s) done, {len(pending)} unit(s) left)")

    if dry_run:
        for unit in pending:
            nos = [line.no for line in unit]
            ui.log(f"  [dry-run] skel/{canticle}/{number:02d}.tsv "
                   f"lines {nos[0]}-{nos[-1]} ({len(nos)} line(s))")
        return True

    with ui.progress(len(lines), start=pending[0][0].no, label=label) as prog:
        for unit in pending:
            nos = [line.no for line in unit]
            prog.update(nos[0])
            texts = [line.text for line in unit]
            label = f"{canticle} {number}"
            rows_by_line = _try_parse(
                nos, texts, model, ui, label, log_path, morph_rows, np_rows, dep_rows,
                case_rows=case_rows,
            )
            if rows_by_line is None:
                # No per-line fallback: a lone line cannot host cross-line arguments, so a
                # parse unit is the smallest unit worth retrying.
                ui.stream.error(f"  {label}: giving up at lines {nos[0]}-{nos[-1]}; "
                                f"earlier units saved for resume")
                return False
            unit_nos = set(nos)
            out = [(no, rows) for no, rows in out if no not in unit_nos]
            out.extend((no, rows_by_line.get(no, [])) for no in nos)
            out.sort(key=lambda item: item[0])
            skel.write_skel(canticle, number, out)
    ui.log(f"Wrote: skel/{canticle}/{number:02d}.tsv")
    return True


def build(canticles: list[str], model: str, size: int, force: bool, dry_run: bool,
          spec: str | None, log_path: Path | None = None) -> int:
    if log_path:
        log_path.write_text("", encoding="utf-8")
    ui = StatusLine()
    for canticle in canticles:
        n_cantos = len(api.cantos(canticle))
        for number in api.select_cantos(canticle, spec):
            _build_canto(canticle, number, n_cantos, model, size, force, dry_run, ui, log_path)
    return 0


def check(canticles: list[str], spec: str | None) -> int:
    hard = 0
    soft = 0
    for canticle in canticles:
        for number in api.select_cantos(canticle, spec):
            if not skel.has_skel(canticle, number):
                print(f"Missing: skel/{canticle}/{number:02d}.tsv", file=sys.stderr)
                hard += 1
                continue
            data = skel.load_skel(canticle, number)
            morph_rows = _morph_rows(canticle, number)
            np_rows = _np_rows(canticle, number)
            dep_rows = _dep_rows(canticle, number)
            case_rows = _case_rows(canticle, number)
            lines = api.canto(canticle, number).lines()
            text_by_no = {line.no: line.text for line in lines}
            nos_all = [line.no for line in lines]
            texts_all = [line.text for line in lines]
            missing = [no for no in nos_all if no not in data]
            hard += len(missing)
            for unit in dep.sentence_groups(nos_all, texts_all, dep.MAX_UNIT_LINES):
                if any(no in missing for no in unit):
                    continue  # already counted above; don't double-report as a count violation
                unit_texts = [text_by_no[no] for no in unit]
                rows_by_line = {no: list(data[no]) for no in unit}
                hard_vs, soft_vs = _classify_violations(
                    unit, unit_texts, rows_by_line, morph_rows, np_rows, dep_rows, case_rows,
                )
                for v in hard_vs:
                    print(f"{canticle} {number}:{v.line} [{v.kind}] {v.detail}", file=sys.stderr)
                    hard += 1
                for v in soft_vs:
                    soft += 1
                    print(f"{canticle} {number}:{v.line} [{v.kind}] {v.detail}", file=sys.stderr)
            if missing:
                print(f"{canticle} {number}: missing lines {missing}", file=sys.stderr)
    print(f"check complete: {hard} hard, {soft} soft violation(s)")
    return 1 if hard else 0


# Divergence-check details all start with one of these prefixes (see `skel._classify_divergence`);
# membership/unknown-role soft checks don't, so they're recognized by a detail substring instead.
_DIVERGENCE_KINDS = ("missing_tuple", "extra_tuple", "missing_arg", "extra_arg", "role_mismatch")


def _violation_class(v: morph.Violation) -> str:
    prefix = v.detail.split(":", 1)[0]
    if prefix in _DIVERGENCE_KINDS:
        return prefix
    # Rule EG's artifact-internal check (`skel._dual_role_violations`). Not a divergence — the two
    # rows contradict each other, with no reference to `derive_unit` — so it is named separately
    # and keyed by the same string in `_CLASS_PROMPTS`/`_CLASS_ORDER`.
    if prefix == "dual_role":
        return "dual_role"
    if "heads no NP" in v.detail:
        return "membership"
    if "not in frozen vocabulary" in v.detail:
        return "unknown_role"
    return "other"


def _print_stats(violations: list[morph.Violation]) -> None:
    by_kind: Counter[str] = Counter()
    by_role: Counter[tuple[str, str]] = Counter()
    by_role_null: Counter[tuple[str, str]] = Counter()
    role_mismatch_pairs: Counter[tuple[str | None, str | None]] = Counter()

    for v in violations:
        kind = _violation_class(v)
        by_kind[kind] += 1
        if kind in ("extra_arg", "missing_arg") and v.role is not None:
            by_role[(kind, v.role)] += 1
            if v.arg == (0, 0):
                by_role_null[(kind, v.role)] += 1
        if kind == "role_mismatch":
            role_mismatch_pairs[(v.given_role, v.role)] += 1

    print("By kind:", file=sys.stderr)
    for kind, count in by_kind.most_common():
        print(f"  {kind:15s} {count:6d}", file=sys.stderr)

    print("\nBy role (extra_arg / missing_arg):", file=sys.stderr)
    for (kind, role), count in by_role.most_common():
        null_count = by_role_null[(kind, role)]
        null_tag = f" (of which ∅ (0,0): {null_count})" if null_count else ""
        print(f"  {kind:12s} {role:12s} {count:6d}{null_tag}", file=sys.stderr)

    if role_mismatch_pairs:
        print("\nTop role_mismatch pairs (given vs derived):", file=sys.stderr)
        for (grole, drole), count in role_mismatch_pairs.most_common():
            print(f"  {grole!r:14s} vs {drole!r:14s} {count:6d}", file=sys.stderr)


def stats(canticles: list[str], spec: str | None) -> int:
    hard = 0
    all_soft: list[morph.Violation] = []
    for canticle in canticles:
        for number in api.select_cantos(canticle, spec):
            if not skel.has_skel(canticle, number):
                hard += 1
                continue
            data = skel.load_skel(canticle, number)
            morph_rows = _morph_rows(canticle, number)
            np_rows = _np_rows(canticle, number)
            dep_rows = _dep_rows(canticle, number)
            case_rows = _case_rows(canticle, number)
            lines = api.canto(canticle, number).lines()
            text_by_no = {line.no: line.text for line in lines}
            nos_all = [line.no for line in lines]
            texts_all = [line.text for line in lines]
            missing = [no for no in nos_all if no not in data]
            hard += len(missing)
            for unit in dep.sentence_groups(nos_all, texts_all, dep.MAX_UNIT_LINES):
                if any(no in missing for no in unit):
                    continue
                unit_texts = [text_by_no[no] for no in unit]
                rows_by_line = {no: list(data[no]) for no in unit}
                hard_vs, soft_vs = _classify_violations(
                    unit, unit_texts, rows_by_line, morph_rows, np_rows, dep_rows, case_rows,
                )
                hard += len(hard_vs)
                all_soft.extend(soft_vs)
    _print_stats(all_soft)
    print(f"stats complete: {len(all_soft)} soft violation(s) ({hard} hard)")
    return 1 if hard else 0


def clean(canticles: list[str], size: int, spec: str | None) -> int:
    removed = 0
    for canticle in canticles:
        for number in api.select_cantos(canticle, spec):
            if not skel.has_skel(canticle, number):
                continue
            data = skel.load_skel(canticle, number)
            lines = api.canto(canticle, number).lines()
            nos_all = [line.no for line in lines]
            texts_all = [line.text for line in lines]
            text_by_no = dict(zip(nos_all, texts_all))

            # Remove parse units with any hard violation (soft is reported, not cleaned).
            bad: set[int] = set()
            for unit in dep.sentence_groups(nos_all, texts_all, size):
                unit_texts = [text_by_no[no] for no in unit]
                rows_by_line = {no: list(data.get(no, ())) for no in unit}
                hard_vs, _ = _classify_violations(unit, unit_texts, rows_by_line, None, None, None)
                if hard_vs:
                    bad.update(unit)
            has_data = bad & data.keys()
            if has_data:
                for no in bad:
                    data.pop(no, None)
                out = sorted(data.items())
                skel.write_skel(canticle, number, [(no, list(rows)) for no, rows in out])
                print(f"Cleaned skel/{canticle}/{number:02d}.tsv — removed lines {sorted(bad)}")
            removed += len(has_data)
    print(f"clean complete: {removed} line(s) removed")
    return 0


def _describe_repair(r: skel.Repair) -> str:
    """One line naming what a rewrite changed, for the `--repair` log and `--fix`'s stage 1."""
    where = f"{r.before.line}.{r.before.token}"
    if r.kind == "null_subject":
        return (f"{where} [null_subject] subj (0,0) -> "
                f"({r.after.arg_line},{r.after.arg_token})")
    return (f"{where} [{r.kind}] {r.before.role} -> {r.after.role} "
            f"arg ({r.before.arg_line},{r.before.arg_token})")


def _apply_unit_repairs(
    unit: list[int], unit_texts: list[str], rows_by_line: dict[int, list[skel.SkelRow]],
    morph_rows: dict[int, list], np_rows: dict[int, list], dep_rows: dict[int, list],
    case_rows: dict[int, list] | None = None,
) -> list[skel.Repair]:
    """Stage 1 of `--fix`, and the whole of `--repair`: apply the deterministic rewrites
    `skel._find_repairs` proposes for one parse unit, **verifying each one**.

    Rewrites are applied one at a time and re-validated, each kept only if it clears violations
    without introducing a class that was not already there (`_is_improvement`, the same bar an
    LLM regeneration has to clear) and leaves zero hard violations. A rejected candidate is
    remembered so the loop terminates, and rejecting one does not sink the rest — which is why
    this is a loop over single repairs rather than one batch application.

    `rows_by_line` is mutated in place; the returned list is what was accepted.
    """
    applied: list[skel.Repair] = []
    rejected: set[tuple[str, skel.SkelRow]] = set()
    while True:
        _, soft = _classify_violations(
            unit, unit_texts, rows_by_line, morph_rows, np_rows, dep_rows, case_rows)
        derived = skel.derive_unit(unit, dep_rows, morph_rows, case_rows)
        candidates = [
            r for r in skel._find_repairs(rows_by_line, derived, soft, morph_rows, dep_rows)
            if (r.kind, r.before) not in rejected
        ]
        if not candidates:
            return applied
        r = candidates[0]
        rows = rows_by_line.get(r.before.line, [])
        if r.before not in rows:
            rejected.add((r.kind, r.before))
            continue
        i = rows.index(r.before)
        rows[i] = r.after
        hard_after, soft_after = _classify_violations(
            unit, unit_texts, rows_by_line, morph_rows, np_rows, dep_rows, case_rows)
        if not hard_after and _is_improvement(soft, soft_after):
            applied.append(r)
        else:
            rows[i] = r.before
            rejected.add((r.kind, r.before))


def repair(canticles: list[str], spec: str | None) -> int:
    """Mechanically rewrite committed TSVs for divergences that need no reading — no model call,
    one deterministic pass. This is exactly `--fix`'s stage 1, run on its own; see
    `skel._find_repairs` for the rule catalogue and its tier-A/tier-B division."""
    totals: Counter[str] = Counter()
    cantos_touched = 0
    for canticle in canticles:
        for number in api.select_cantos(canticle, spec):
            if not skel.has_skel(canticle, number):
                continue
            data = skel.load_skel(canticle, number)
            morph_rows = _morph_rows(canticle, number)
            np_rows = _np_rows(canticle, number)
            dep_rows = _dep_rows(canticle, number)
            case_rows = _case_rows(canticle, number)
            lines = api.canto(canticle, number).lines()
            text_by_no = {line.no: line.text for line in lines}
            nos_all = [line.no for line in lines]
            texts_all = [line.text for line in lines]
            missing = [no for no in nos_all if no not in data]
            out = {no: list(rows) for no, rows in data.items()}
            n_canto = 0
            for unit in dep.sentence_groups(nos_all, texts_all, dep.MAX_UNIT_LINES):
                if any(no in missing for no in unit):
                    continue
                unit_texts = [text_by_no[no] for no in unit]
                rows_by_line = {no: out[no] for no in unit}  # mutated in place
                for r in _apply_unit_repairs(unit, unit_texts, rows_by_line, morph_rows,
                                             np_rows, dep_rows, case_rows):
                    totals[r.kind] += 1
                    n_canto += 1
                    print(f"{canticle} {number}:{_describe_repair(r)}")
            if n_canto:
                skel.write_skel(canticle, number, [(no, rows) for no, rows in sorted(out.items())])
                print(f"Repaired skel/{canticle}/{number:02d}.tsv — {n_canto} rewrite(s)")
                cantos_touched += 1
    summary = ", ".join(f"{n} {kind}" for kind, n in sorted(totals.items())) or "no"
    print(f"repair complete: {summary} rewrite(s) across {cantos_touched} canto(s)")
    return 0


def _is_improvement(
    soft_before: list[morph.Violation], soft_after: list[morph.Violation]
) -> bool:
    """A regeneration is accepted only if it removes violations *without* introducing a class
    that was not already there (PLAN.md Phase 5c). The plain count test admitted regressions in
    kind — the Phase 4b round traded a net count drop for `unknown_role` 0 -> 2, a role outside
    the frozen vocabulary."""
    if len(soft_after) >= len(soft_before):
        return False
    before_classes = {_violation_class(v) for v in soft_before}
    return all(_violation_class(v) in before_classes for v in soft_after)


# Tuple-level classes are settled before argument-level ones: adding or withdrawing a predicate
# changes which arguments exist to dispute, so asking about roles first would ask about slots
# that are about to move.
_CLASS_ORDER = (
    "missing_tuple", "missing_tuple_nominal",
    "extra_tuple_adverb", "extra_tuple_adjective", "extra_tuple",
    # `dual_role` and `arg_slot` run before the per-side argument classes on purpose: both are one
    # question standing in for two rows, and asking either side alone is what froze their positions.
    "dual_role", "arg_slot",
    "role_mismatch", "extra_arg_subject", "extra_arg_adjective", "extra_arg",
    "missing_arg_subject", "missing_arg_adverb", "missing_arg",
)

_EXTRA_ARG_CLASSES = ("extra_arg", "extra_arg_subject", "extra_arg_adjective")
_MISSING_ARG_CLASSES = ("missing_arg", "missing_arg_subject", "missing_arg_adverb")


def _split_slot_conflicts(
    by_class: dict[str, list[morph.Violation]],
) -> dict[str, list[morph.Violation]]:
    """Move each *same-slot* pair into the `arg_slot` class, and drop its `missing_arg` half.

    A predicate with a `missing_arg` and an `extra_arg` on the **same** role is one disagreement
    about which token fills that slot, and the sixth round measured what asking it as two questions
    costs: 8 such predicates (16 of the 174 remaining positions) had survived three rounds
    untouched. The `extra_arg` half is the one kept, because it carries the filler the reading
    itself wrote — which is what `_ask_arg_slot` is allowed to quote. The `missing_arg` half names
    only the slot, which the merged question already names, so re-asking it is the duplicate.
    """
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
    """Fix one canto's flagged parse units under a progress bar, in three stages.

    1. **Deterministic** (`_apply_unit_repairs`, no model call) — the rewrites that need no
       reading. A unit this clears never reaches the model at all.
    2. **Class-targeted** (`_ask_class`) — one narrow question per remaining violation *class*,
       each with its own prompt, spliced in at row level and accepted per class. This is where
       partial credit comes from: settling one class is kept even when the others fail.
    3. **Whole-unit regeneration** (`_try_parse`) — the original instrument, kept as a fallback
       for units stages 1 and 2 left untouched, and disableable with `--no-whole` so a round can
       be measured with and without it.

    Every acceptance is gated the same way — zero hard violations and `_is_improvement` — so the
    no-worse-off guarantee holds stage by stage, not just for the pass. The TSV is written after
    every accepted change, mirroring `_build_canto`'s resumability.

    Returns a Counter of measurement keys (`units:*`, `repair:<kind>`, `calls:<class>`,
    `removed:<class>`), because the finding of Phase 5w was that a pass average conceals what
    each class did — see `fix`'s summary.
    """
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
                continue  # unit incomplete; leave it to `build`/resume
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

            # --- stage 1: deterministic ---------------------------------------------------
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

            # --- stage 2: one narrow question per class -----------------------------------
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

            # --- stage 3: whole-unit regeneration, the original instrument ----------------
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


def _log_rejection(log_path, label, unit, cls, soft_before, soft_after, hard_after) -> None:
    """Record a candidate the acceptance gate turned down — the material for the next round's
    per-class read, which is how rules V through AF were found."""
    if not log_path:
        return
    with log_path.open("a", encoding="utf-8") as f:
        f.write(f"=== {label} lines {unit[0]}-{unit[-1]} [{cls}]: not accepted "
                f"({len(soft_before)} -> {len(soft_after)}"
                f"{f', {len(hard_after)} hard' if hard_after else ''}) ===\n")
        for v in hard_after:
            f.write(f"hard:   {v.detail}\n")
        for v in soft_before:
            f.write(f"before: {v.detail}\n")
        for v in soft_after:
            f.write(f"after:  {v.detail}\n")
        f.write("\n")


def fix(canticles: list[str], model: str, spec: str | None, log_path: Path | None = None,
        whole: bool = True) -> int:
    """Reduce the soft residue of already-built parse units, deterministically first and with a
    class-targeted question second — see `_fix_canto` for the three stages.

    The summary is reported **per class**, with calls beside violations removed. That is the
    measurement Phase 5w's finding demands: a pass average conceals which instrument worked, and
    the ratio per class is the only number that says whether a given prompt is earning its call.
    """
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


def _fix_summary_lines(totals: Counter[str]) -> list[str]:
    """The per-class `calls / removed / per call / refused` table, as lines.

    Separated from the printing so the same text reaches the terminal and `--log`. The table is
    the round's only record of what a call *cost*: the violation diff says which positions moved,
    never how many questions were asked to move them, and a round's yield can be carried entirely
    by one class while every other sits at zero.

    The `refused` column is the round's second product (2026-08-18, `skel/PLAN.md` §30 finding 3):
    calls where the model answered and its answer was *the artifact as written*. Those are not
    failures — they are the model naming, position by position, where it thinks `--check` is wrong,
    and a class that is all refusals is checker-side work rather than a prompt population.
    """
    flagged = totals["units:flagged"]
    calls = sum(n for k, n in totals.items() if k.startswith("calls:"))
    removed = sum(n for k, n in totals.items() if k.startswith("removed:"))
    refused = sum(n for k, n in totals.items() if k.startswith("refused:"))
    repairs = {k.split(":", 1)[1]: n for k, n in totals.items() if k.startswith("repair:")}

    lines = [f"units flagged: {flagged}; "
             f"cleared with no model call: {totals['units:cleared_deterministically']}; "
             f"cleared outright: {totals['units:cleared']}"]
    if repairs:
        lines.append("stage 1 (deterministic, 0 calls): "
                     + ", ".join(f"{n} {kind}" for kind, n in sorted(repairs.items()))
                     + f" -> {totals['removed:_deterministic']} violation(s)")
    lines.append(f"{'class':24s} {'calls':>7s} {'removed':>8s} {'per call':>9s} {'refused':>8s}")
    for key in sorted(k for k in totals if k.startswith("calls:")):
        cls = key.split(":", 1)[1]
        n_calls = totals[key]
        n_removed = totals[f"removed:{cls}"]
        rate = n_removed / n_calls if n_calls else 0.0
        lines.append(f"{cls:24s} {n_calls:7d} {n_removed:8d} {rate:9.3f} "
                     f"{totals[f'refused:{cls}']:8d}")
    rate = removed / calls if calls else 0.0
    lines.append(f"{'TOTAL':24s} {calls:7d} {removed:8d} {rate:9.3f} {refused:8d}")
    lines.append(f"fix complete: {removed} soft violation(s) removed over {calls} LLM call(s); "
                 f"{refused} refused (the reading stands)")
    return lines


def _print_fix_summary(totals: Counter[str], log_path: Path | None = None) -> None:
    lines = _fix_summary_lines(totals)
    print("\n" + "\n".join(lines))
    if log_path:
        # Appended last, after every `NOTE` and rejected candidate, so a log is self-contained:
        # what was asked, what came back, and what the asking cost.
        with log_path.open("a", encoding="utf-8") as f:
            f.write("=== fix summary ===\n" + "\n".join(lines) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(prog="skel.py")
    parser.add_argument("canticles", nargs="+", help="canticle names, e.g. inferno")
    parser.add_argument("-m", "--model", help="LLM, e.g. ollama:gpt-oss (required unless --check)")
    parser.add_argument("--chunk", type=int, default=dep.MAX_UNIT_LINES,
                        help=f"max lines per parse unit (default {dep.MAX_UNIT_LINES})")
    parser.add_argument("-c", "--canto", metavar="SPEC", help=api.CANTO_SPEC_HELP)
    parser.add_argument("--force", action="store_true", help="rebuild even if artifact exists")
    parser.add_argument("--check", action="store_true", help="validate artifacts, no model call")
    parser.add_argument("--stats", action="store_true",
                        help="validate artifacts, no model call; print soft-violation counts by class")
    parser.add_argument("--clean", action="store_true",
                        help="remove parse units with hard violations, then exit")
    parser.add_argument("--repair", action="store_true",
                        help="run --fix's deterministic stage on its own: rewrite committed TSVs "
                             "for divergences that need no reading, no model call")
    parser.add_argument("--fix", action="store_true",
                        help="reduce soft violations in built units: deterministic repairs, then "
                             "one targeted question per violation class, keeping only improvements")
    parser.add_argument("--whole", action=argparse.BooleanOptionalAction, default=True,
                        help="with --fix, fall back to whole-unit regeneration for units the "
                             "targeted questions did not move (default: enabled)")
    parser.add_argument("-n", "--dry-run", action="store_true",
                        help="show pending parse units without calling the LLM")
    parser.add_argument("--log", nargs="?", const="skel.log", metavar="FILE",
                        help="append failed LLM responses, and the model's own NOTE lines for "
                             "questions it could not answer cleanly, to FILE (default: skel.log)")
    args = parser.parse_args()

    if err := api.check_canto_spec(args.canticles, args.canto):
        parser.error(err)

    if args.check:
        return check(args.canticles, args.canto)
    if args.stats:
        return stats(args.canticles, args.canto)
    if args.clean:
        return clean(args.canticles, args.chunk, args.canto)
    if args.repair:
        return repair(args.canticles, args.canto)
    log_path = Path(args.log) if args.log else None
    if args.fix:
        if not args.model:
            parser.error("--model is required for --fix")
        return fix(args.canticles, args.model, args.canto, log_path, args.whole)
    if args.dry_run:
        return build(args.canticles, args.model or "", args.chunk, args.force, True, args.canto)
    if not args.model:
        parser.error("--model is required for building (or pass --check / --dry-run)")
    return build(args.canticles, args.model, args.chunk, args.force, False, args.canto, log_path)


if __name__ == "__main__":
    sys.exit(main())
