"""Layer 4 of the grammatical stack: dependency / grammatical role.

An LLM proposes, per *parse unit* (a sentence, or a sentence fragment for long sentences — see
`sentence_groups`), a Markdown table naming a Universal-Dependencies relation (`deprel`) and a
head token for every alpha token in the unit. Unlike Layers 2-3, which align free-text model
output to source substrings, this layer gives the model an authoritative *numbered* token list
(`line.token`) up front and has it cite indices back — a dependency row names two positions, and
free-text matching two words per row (against a source full of repeated `che`/`e`) would be far
more ambiguous than Layer 2/3's single-word alignment. `Word`/`Head Word` table cells are kept
only as build-time verification anchors; they are not stored in the frozen artifact.

Attachment may cross line boundaries (PLAN.md) — a subject on one line, its predicate on the
next — which is what rejoins Layer-3's single-line noun phrases across enjambment: an NP's
clause function is *derived* at serve time as the deprel of the Layer-4 row at
`(span.line, span.head)` (see `np_role`), not stored.

Relative-pronoun antecedents are likewise not stored: UD encodes them structurally (a relative
clause's verb attaches to its antecedent noun via `acl:relcl`; the pronoun gets its own role
inside the clause), so PLAN.md's "antecedent resolves to an in-scope NP" check becomes the soft
check that every `acl:relcl` head is a nominal Layer-2 POS — or carries the `RELCL_HEAD` flag in
its Layer-2 `note` (mirroring `np.py`'s `NO_NP`/`CONT_NEXT` convention), a hand-verified exemption
for archaic substantivized adjectives/numerals/participles/adverbs (`quel`, `altri`, `due`,
`eletti`, `là dove`, …) that function as the antecedent despite a non-nominal part of speech (see
dep/CORRECTIONS.md).

Like `dante_corpus/np.py`, this stays free of `api` (which imports it) and depends only on
`tokenizer`/`_paths`/`morph` (the generic Markdown-table parser is reused from `morph`).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ._paths import DEP_DIR
from .morph import MorphRow, Violation, read_table, strip_word_punct
from .tokenizer import has_alpha, tokenize

# --- Table columns -----------------------------------------------------------------

# The model emits `| Line | Token | Word | Deprel | Head Line | Head Token | Head Word |`.
# `line`/`token` are the authoritative indices the model must cite; `word` and `head word` are
# verification anchors only (checked at build time, never stored).
_HEADER_ALIASES = {
    "line": "line",
    "token": "token",
    "word": "word",
    "deprel": "deprel",
    "relation": "deprel",
    "head line": "head_line",
    "head token": "head_token",
    "head word": "head_word",
}


def canon_header(header: str) -> str | None:
    return _HEADER_ALIASES.get(header.strip().lower())


# Frozen soft-check vocabulary (UD v2 universal relations plus the subtypes used by Italian UD
# treebanks; measure-then-freeze — see dep/README.md and PLAN.md). `punct`/`goeswith`/`clf`/
# `list`/`reparandum` are excluded: punctuation is never tokenized here. `dep` is kept as the
# generic escape hatch UD itself defines for a relation that resists closed-set classification.
# `attr` (non-UD, spaCy-style) is kept too: measured across the full 100-canto build it was the
# model's single dominant, systematic label for predicate-nominal/adjective complements of a
# copula (340 of 637 soft violations, an order of magnitude above any other off-vocabulary
# label) — frozen in as a one-time adjustment rather than left as permanent noise.
DEPRELS = frozenset({
    "acl", "acl:relcl", "advcl", "advmod", "amod", "appos", "attr",
    "aux", "aux:pass", "case", "cc", "ccomp", "compound", "conj", "cop",
    "csubj", "csubj:pass", "dep", "det", "det:poss", "det:predet",
    "discourse", "dislocated", "expl", "expl:impers", "expl:pass",
    "fixed", "flat", "flat:foreign", "flat:name", "iobj", "mark",
    "nmod", "nsubj", "nsubj:pass", "nummod", "obj", "obl", "obl:agent",
    "orphan", "parataxis", "root", "vocative", "xcomp",
})


def _note_flags(note: str) -> set[str]:
    """The machine-readable flags in a Layer-2 `note` cell (comma-separated, alongside free-text
    notes like `apocope`) — the convention `np.py`'s `NO_NP`/`CONT_NEXT` established."""
    return {f.strip() for f in note.split(",")}


def _is_nominal(pos: str, note: str = "") -> bool:
    p = pos.lower()
    if "noun" in p or "pronoun" in p:
        return True
    return "RELCL_HEAD" in _note_flags(note)


# Subject relations the agreement check applies to (`csubj` is excluded: a clausal subject has no
# person/number of its own).
_NSUBJ_DEPRELS = frozenset({"nsubj", "nsubj:pass"})

# Relative and interrogative pronouns take their person from the antecedent, not from their own
# Layer-2 row (which tags them 3rd by default), so their agreement with a finite head is not
# decidable from the two rows alone — see the agreement check in `validate_unit`.
_ANTECEDENT_PERSON_LEMMAS = frozenset({"che", "chi", "cui", "quale"})

# Distributive pronouns: they resume a plural subject one member at a time, so a singular one
# under a plural verb is the construction working, not a disagreement — "vanno a vicenda
# ciascuna al giudizio" (inferno 5:14). A closed function-word list, like the set above.
#
# `ambedue`/`amendue` and the distributive `uno` join them with rule CR (2026-08-16), which is
# what first asks the *person* question of a 1st/2nd plural head: all three stand in for the
# whole of a "we" the verb already carries — "A seder ci **ponemmo** ivi **ambedui**"
# (purgatorio 4:52), "e **amendue** già **mostravam**" (12:11), "**uno** innanzi altro, ce
# n'**andavamo**" (26:1) — so their 3rd person is the quantifier's, not the subject's, exactly
# the notional reading this set already names for `ciascuno`.
_DISTRIBUTIVE_LEMMAS = frozenset({"ciascuno", "ognuno", "catuno", "ambedue", "amendue", "uno"})

# Quantity determiners that make a plural noun a single measure — "non è molt' anni"
# (inferno 19:19). Numerals are recognized structurally instead, by their `nummod` edge.
_QUANTITY_LEMMAS = frozenset({"molto"})

# Layer-2 `note` flags this layer reads, hand-verified per row (see dep/CORRECTIONS.md and
# morph/CORRECTIONS.md), following `np.py`'s `NO_NP`/`CONT_NEXT` convention:
#   AD_SENSUM — agreement is notional rather than grammatical at this token, in either direction
#               (a collective singular under a plural verb, a plural aggregate under a singular
#               one). Stating it as a rule would need a collective-noun lexicon, which PLAN.md's
#               *Neutrality audit* rules out, so each row is read and flagged individually.
#   FOREIGN   — the token is not Italian (Arnaut's Occitan, a Latin quotation, Nimrod's
#               gibberish), so no Italian agreement rule applies to it.
_AGREEMENT_EXEMPT_FLAGS = frozenset({"AD_SENSUM", "FOREIGN"})


# --- DepRow --------------------------------------------------------------------------


@dataclass(frozen=True)
class DepRow:
    line: int
    token: int  # 1-based alpha-token index within `line` (matches Line.tokens / MorphRow order)
    word: str
    deprel: str
    head_line: int  # 0 together with head_token == 0 marks the sentence root
    head_token: int

    def to_dict(self) -> dict[str, object]:
        return {
            "line": self.line,
            "token": self.token,
            "word": self.word,
            "deprel": self.deprel,
            "head_line": self.head_line,
            "head_token": self.head_token,
        }


# --- Sentence splitting (parse units) -----------------------------------------------

# A dependency tree needs every head resolvable within its parse unit, so lines are grouped by
# sentence rather than sliced into fixed-size chunks (contrast morph/np). Measured over all 100
# cantos: sentence length (line-final `.`/`!`/`?`) is mode 3/6 lines, 99.7% <= 12; the remaining
# long sentences are sub-split at line-final `;`/`:` (with those included the corpus max is 12).
MAX_UNIT_LINES = 12

_TERMINAL = (".", "!", "?")
_SOFT_BREAK = (";", ":")


def _ends_with(text: str, chars: tuple[str, ...]) -> bool:
    return bool(text) and text[-1] in chars


def _split_long(group: list[int], texts: dict[int, str], max_lines: int) -> list[list[int]]:
    """Sub-split a too-long sentence at line-final `;`/`:`, as large as possible per piece."""
    if len(group) <= max_lines:
        return [group]
    out: list[list[int]] = []
    start = 0
    n = len(group)
    while n - start > max_lines:
        limit = start + max_lines
        split_at = None
        for i in range(start, limit):
            if _ends_with(texts[group[i]], _SOFT_BREAK):
                split_at = i
        if split_at is None:  # no soft break in range: fall back to a hard split
            split_at = limit - 1
        out.append(group[start : split_at + 1])
        start = split_at + 1
    out.append(group[start:])
    return out


def sentence_groups(
    nos: list[int], texts: list[str], max_lines: int = MAX_UNIT_LINES
) -> list[list[int]]:
    """Group line numbers into dependency parse units.

    A unit ends at a line whose *final character* is `.`/`!`/`?` (sentence-final punctuation in
    this edition follows a closing guillemet, e.g. `elegge!».` ends in `.`; a line ending in a
    bare `»`/`'` is an embedded quote transition and does not break). The final group is always
    flushed at end of input, even without terminal punctuation. Units longer than `max_lines`
    are sub-split at line-final `;`/`:` (see `_split_long`).
    """
    groups: list[list[int]] = []
    current: list[int] = []
    for no, text in zip(nos, texts):
        current.append(no)
        if _ends_with(text, _TERMINAL):
            groups.append(current)
            current = []
    if current:
        groups.append(current)

    text_by_no = dict(zip(nos, texts))
    result: list[list[int]] = []
    for group in groups:
        result.extend(_split_long(group, text_by_no, max_lines))
    return result


# --- Parsing / resolution ------------------------------------------------------------


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
) -> tuple[dict[int, list[DepRow]], list[str]]:
    """Parse a dependency table and resolve it into `DepRow`s keyed by line number.

    Returns (rows-by-line, head-word mismatch descriptions). Raises `ValueError` if no table can
    be parsed at all (mirrors `np.align_chunk`). Unlike Layer 2/3, resolution is index lookup,
    not substring search: `line`/`token` are taken as authoritative, and the `Head Word` cell is
    only cross-checked against the token actually found at `(head_line, head_token)` — a
    disagreement means the model mis-cited an index, reported here as a build-time warning that
    the driver treats as a hard violation (index citations must be trustworthy)."""
    table = read_table(table_text)
    if table is None:
        raise ValueError("no parseable dependency table found")
    keys = [canon_header(h) for h in table[0]]
    token_lists = {no: _alpha_tokens(t) for no, t in zip(nos, texts)}

    result: dict[int, list[DepRow]] = {no: [] for no in nos}
    mismatches: list[str] = []
    for raw in table[2:]:  # skip header + separator
        cells = dict(zip(keys, raw))
        line = _parse_int(cells.get("line"))
        token = _parse_int(cells.get("token"))
        word = (cells.get("word") or "").strip()
        deprel = (cells.get("deprel") or "").strip()
        head_line = _parse_int(cells.get("head_line")) or 0
        head_token = _parse_int(cells.get("head_token")) or 0
        head_word = (cells.get("head_word") or "").strip()
        if line is None or token is None or not word or not deprel or line not in result:
            continue
        result[line].append(
            DepRow(line=line, token=token, word=word, deprel=deprel,
                   head_line=head_line, head_token=head_token)
        )
        if head_line and head_token:
            head_tokens = token_lists.get(head_line)
            if head_tokens is not None and 1 <= head_token <= len(head_tokens):
                expected = head_tokens[head_token - 1]
                if head_word and not _words_match(head_word, expected):
                    mismatches.append(
                        f"{line}.{token} cites head {head_line}.{head_token} as {head_word!r}, "
                        f"actual {expected!r}"
                    )

    for rows in result.values():
        rows.sort(key=lambda r: r.token)
    return result, mismatches


# --- Validation ------------------------------------------------------------------------


def validate_unit(
    nos: list[int],
    texts: list[str],
    rows_by_line: dict[int, list[DepRow]],
    morph_rows: dict[int, list[MorphRow]] | None = None,
) -> list[Violation]:
    """Check `rows_by_line` for one parse unit against its deterministic tokens.

    Hard checks (structural bar; kinds `count`/`word`/`head`/`cycle`/`root`): each line has
    exactly one row per token, in order; each row's word matches its token (elision spelling
    tolerated via `morph.strip_word_punct`, as Layer 3 does); every head cites an in-unit
    `(line, token)` or is the `(0, 0)` root sentinel, consistently with `deprel == "root"`; no
    token is its own head; the head chain from every token reaches a root with no cycle; the
    unit has at least one root. Soft checks (kind `tag`): more than one root in a unit (expected
    for `;`/`:`-sub-split long sentences, see `sentence_groups`); `deprel` outside the frozen
    `DEPRELS` vocabulary; an `acl:relcl` relation whose head token is not a nominal Layer-2 POS
    (only checked when `morph_rows` is supplied, the Layer 2-aware policy PLAN.md calls for
    resolving relative-pronoun antecedents structurally rather than storing them); a predicate
    carrying more than one `obj` child, which UD does not allow — coordinated objects attach the
    later conjuncts to the first with `conj`, and an object complement is `xcomp`, so a flattened
    pair is a mis-parse rather than a convention difference (the corpus already uses the UD shape
    everywhere else: 304 `conj` children of an `obj`); and an `nsubj`/`nsubj:pass` whose Layer-2
    person or number contradicts its finite head's (also Layer 2-aware — see
    `_subject_agreement_violations`).
    """
    violations: list[Violation] = []
    token_lists = {no: _alpha_tokens(t) for no, t in zip(nos, texts)}
    valid_positions = {(no, i + 1) for no in nos for i in range(len(token_lists[no]))}

    for no in nos:
        tokens = token_lists[no]
        rows = sorted(rows_by_line.get(no, []), key=lambda r: r.token)
        if [r.token for r in rows] != list(range(1, len(tokens) + 1)):
            violations.append(Violation(no, "count", f"{len(rows)} rows vs {len(tokens)} tokens"))
        for row in rows:
            if 1 <= row.token <= len(tokens):
                token = tokens[row.token - 1]
                if row.word != token and strip_word_punct(row.word, token) is None:
                    violations.append(Violation(no, "word", f"{row.word!r} != token {token!r}"))

    all_rows = [row for no in nos for row in rows_by_line.get(no, [])]
    index_map = {(row.line, row.token): row for row in all_rows}
    root_count = 0
    for row in all_rows:
        is_root_head = row.head_line == 0 and row.head_token == 0
        if is_root_head != (row.deprel == "root"):
            violations.append(
                Violation(row.line, "head",
                          f"token {row.token} head {row.head_line}.{row.head_token} "
                          f"inconsistent with deprel {row.deprel!r}")
            )
        if is_root_head:
            root_count += 1
            continue
        if (row.head_line, row.head_token) not in valid_positions:
            violations.append(
                Violation(row.line, "head",
                          f"token {row.token} head {row.head_line}.{row.head_token} not in unit")
            )
        elif (row.head_line, row.head_token) == (row.line, row.token):
            violations.append(Violation(row.line, "head", f"token {row.token} is its own head"))

    for row in all_rows:
        seen: set[tuple[int, int]] = set()
        cur: DepRow | None = row
        while cur is not None and not (cur.head_line == 0 and cur.head_token == 0):
            key = (cur.line, cur.token)
            if key in seen:
                violations.append(
                    Violation(row.line, "cycle", f"cycle detected from token {row.token}")
                )
                cur = None
                break
            seen.add(key)
            cur = index_map.get((cur.head_line, cur.head_token))

    if root_count == 0:
        violations.append(Violation(nos[0], "root", f"no root token in unit {nos[0]}-{nos[-1]}"))
    elif root_count > 1:
        violations.append(
            Violation(nos[0], "tag", f"{root_count} root tokens in unit {nos[0]}-{nos[-1]}")
        )

    for row in all_rows:
        if row.deprel not in DEPRELS:
            violations.append(Violation(row.line, "tag", f"deprel {row.deprel!r} not in frozen set"))
        if row.deprel == "acl:relcl" and morph_rows is not None:
            head_rows = morph_rows.get(row.head_line)
            if head_rows and 1 <= row.head_token <= len(head_rows):
                head_row = head_rows[row.head_token - 1]
                if not _is_nominal(head_row.pos, head_row.note):
                    violations.append(
                        Violation(row.line, "tag",
                                  f"acl:relcl head {row.head_line}.{row.head_token} "
                                  f"is {head_row.pos!r}, not nominal")
                    )

    obj_children: dict[tuple[int, int], list[DepRow]] = {}
    for row in all_rows:
        if row.deprel == "obj":
            obj_children.setdefault((row.head_line, row.head_token), []).append(row)
    for (head_line, head_token), objs in sorted(obj_children.items()):
        if len(objs) < 2:
            continue
        cited = ", ".join(f"{o.line}.{o.token} {o.word!r}"
                          for o in sorted(objs, key=lambda r: (r.line, r.token)))
        violations.append(
            Violation(head_line, "tag",
                      f"predicate {head_line}.{head_token} has {len(objs)} obj children: {cited}")
        )

    violations.extend(_subject_agreement_violations(all_rows, morph_rows))

    return violations


def _morph_at(
    morph_rows: dict[int, list[MorphRow]], line: int, token: int
) -> MorphRow | None:
    rows = morph_rows.get(line)
    if not rows or not 1 <= token <= len(rows):
        return None
    return rows[token - 1]


def _is_fused_non_finite(row: MorphRow) -> bool:
    """Whether a `person` on this row is the enclitic's rather than a verb's own: a fused token
    (`verb+pronoun`, `adverb+pronoun`, ...) whose verb part carries neither tense nor mood."""
    return "+" in row.pos and not row.tense and not row.mood


def _case_lemma(
    row: DepRow, children: dict[tuple[int, int], list[DepRow]],
    morph_rows: dict[int, list[MorphRow]],
) -> str:
    """The lemma of the preposition introducing an oblique/nominal token — its `case` child."""
    for child in children.get((row.line, row.token), ()):
        if child.deprel == "case":
            child_morph = _morph_at(morph_rows, child.line, child.token)
            if child_morph is not None:
                return child_morph.lemma
    return ""


def subject_agreement(
    subj: tuple[int, int], head: tuple[int, int],
    morph_rows: dict[int, list[MorphRow]] | None,
    children: dict[tuple[int, int], list[DepRow]],
) -> tuple[str, str]:
    """Whether Layer 2 says a subject token agrees with a (finite) predicate token.

    Returns `("agree", "")`, `("disagree", <feature>)`, or `("undecidable", <reason>)`. The
    exclusions that yield "undecidable" are the twelve enumerated in
    `_subject_agreement_violations`, which is the check this function was extracted from — it is
    the *only* implementation of the test, so a caller asking the positive question (does this
    pair agree?) and the checker asking the negative one cannot drift apart.

    "undecidable" is not a weak "disagree": it means the two frozen rows genuinely do not have to
    match, so nothing may be concluded either way. `skel._find_repairs` relies on that
    distinction — it repairs only on "agree".
    """
    if morph_rows is None:
        return ("undecidable", "no morph")
    head_morph = _morph_at(morph_rows, *head)
    if head_morph is None or not head_morph.person or "verb" not in head_morph.pos:
        return ("undecidable", "head is not a finite verb")
    subj_morph = _morph_at(morph_rows, *subj)
    if subj_morph is None:
        return ("undecidable", "no morph row for the subject")
    if _is_fused_non_finite(head_morph) or _is_fused_non_finite(subj_morph):
        return ("undecidable", "fused non-finite token")
    if subj_morph.lemma in _ANTECEDENT_PERSON_LEMMAS:
        return ("undecidable", "person comes from the antecedent")
    conjuncts = [c for c in children.get(subj, ()) if c.deprel == "conj"]
    if head_morph.person in ("1", "2") and head_morph.number == "pl.":
        # A 1st/2nd person plural verb may be written with only one member of its subject in the
        # tree — "io e tu" reduced to "io" — so *number* is undecidable here. **Person** is not,
        # and only for a subject that could be such a member: a 1st or 2nd person word, or a
        # coordination (whose own person the conjunct branch below tests member by member). A
        # lone third-person subject cannot be a member of a "we"/"you" at all, and Layer 4
        # attaching one to a 1/2 plural verb is the same real question the rest of this check
        # asks — "Ciò ch'io dicea … tanto è risposto … ma … contrario suon **prendemo**"
        # (purgatorio 20:102), where `Ciò` is the subject of the *first* conjunct and the second
        # is the pilgrims' own "we". Rule CR; before it, this exclusion swallowed the person
        # test along with the number test.
        if conjuncts or (subj_morph.person or "3") in ("1", "2"):
            return ("undecidable", "1/2 plural head admits a singular member")
    if len([c for c in children.get(head, ()) if c.deprel in _NSUBJ_DEPRELS]) > 1:
        return ("undecidable", "head carries more than one subject")
    if _AGREEMENT_EXEMPT_FLAGS & (_note_flags(subj_morph.note) | _note_flags(head_morph.note)):
        return ("undecidable", "hand-verified Layer-2 exemption flag")

    subj_children = children.get(subj, ())
    head_children = children.get(head, ())
    sg_subj_pl_head = subj_morph.number == "sg." and head_morph.number == "pl."
    pl_subj_sg_head = subj_morph.number == "pl." and head_morph.number == "sg."

    if subj_morph.lemma in _DISTRIBUTIVE_LEMMAS and head_morph.number == "pl.":
        return ("undecidable", "distributive subject resuming a plural")
    if sg_subj_pl_head and any(c.deprel == "cc" for c in subj_children) and any(
            c.deprel in ("nmod", "conj", "appos") for c in subj_children):
        return ("undecidable", "coordination inside the subject phrase")
    if sg_subj_pl_head and any(
            c.deprel in ("obl", "nmod") and _case_lemma(c, children, morph_rows) == "con"
            for c in head_children):
        return ("undecidable", "comitative phrase on a plural head")
    if pl_subj_sg_head and (
            any(c.deprel == "nummod" for c in subj_children)
            or any(c.deprel in ("det", "amod")
                   and (m := _morph_at(morph_rows, c.line, c.token)) is not None
                   and m.lemma in _QUANTITY_LEMMAS
                   for c in subj_children)):
        return ("undecidable", "quantified subject read as one measure")
    if (subj_morph.number and head_morph.number
            and subj_morph.number != head_morph.number
            and any(c.deprel == "attr"
                    and (m := _morph_at(morph_rows, c.line, c.token)) is not None
                    and m.number == head_morph.number
                    for c in head_children)):
        return ("undecidable", "copula agreeing with its predicate nominal")
    if pl_subj_sg_head and any(
            c.deprel == "expl:impers"
            or (c.deprel == "expl"
                and (m := _morph_at(morph_rows, c.line, c.token)) is not None
                and "impersonal" in _note_flags(m.note))
            for c in head_children):
        return ("undecidable", "impersonal `si` with a postposed notional subject")

    # A nominal with no `person` of its own is 3rd person by default.
    subj_person = subj_morph.person or "3"
    if conjuncts:
        # A **coordinated** subject leaves the number test undecidable — "'l duca e io" is two
        # singulars governing a plural verb, and Italian lets the verb take either — but not the
        # person test: a coordination has a person, and the finite verb agrees with *one* of its
        # members. Dante uses last/nearest-conjunct agreement freely in both directions ("Tosto
        # che 'l duca e io nel legno **fui**", inferno 8:28, 1sg on the second conjunct; "né io né
        # altri 'l **crede**", 2:33, 3sg on the second), so the test is satisfied by any member.
        # It fails only when no conjunct carries the head's person at all, which is a real
        # question about the attachment.
        persons = {subj_person} | {
            (m.person or "3") for c in conjuncts
            if (m := _morph_at(morph_rows, c.line, c.token)) is not None
        }
        if head_morph.person not in persons:
            return ("disagree",
                    f"person {'/'.join(sorted(persons))} vs {head_morph.person}")
        return ("undecidable", "coordinated subject")
    if subj_person != head_morph.person:
        return ("disagree", f"person {subj_person} vs {head_morph.person}")
    if subj_morph.number and head_morph.number and subj_morph.number != head_morph.number:
        return ("disagree", f"number {subj_morph.number} vs {head_morph.number}")
    return ("agree", "")


def _subject_agreement_violations(
    all_rows: list[DepRow], morph_rows: dict[int, list[MorphRow]] | None
) -> list[Violation]:
    """Soft check: an `nsubj`/`nsubj:pass` whose Layer-2 person or number contradicts the person
    or number of its **finite** head.

    Italian agreement is obligatory, so the two frozen layers cannot both be right here: either
    the attachment is a mis-parse (the token is a predicate nominal, a vocative, a dislocated
    topic or the subject of a *different* clause) or one of the two Layer-2 rows carries the wrong
    feature (Dante's `quei`/`altri` are singular despite the plural-looking ending). Which side
    is wrong is not mechanically decidable, so this reports the position rather than repairing it.

    Twelve exclusions, all cases where the two rows genuinely do not have to match. The first six
    were established when the rule opened (2026-08-07); the rest closed its 18-position residue
    (2026-08-14), each measured corpus-wide before it was written — none of them touches a pair
    the rule currently calls "agree", so `skel`'s Tier-B repairs keep every position they had.

    - the head is not a finite verb — no Layer-2 `person`, or not a verb at all (the corpus makes
      the *predicate* the head of a copular clause, so a subject can hang off a noun, an adjective
      or a fused `vosco` = "con voi", none of which conjugates);
    - either side is a **fused** token whose verb part is non-finite (`pos` containing `+`, with no
      tense or mood): there the `person` cell is the enclitic's, not a subject-agreement feature —
      `aprirmi` = *aprire* + *mi* is tagged 1sg for the clitic. A finite fused token
      (`parvemi`, `Presemi`) carries the verb's own person and stays in scope;
    - the subject is a relative/interrogative pronoun (`_ANTECEDENT_PERSON_LEMMAS`), whose person
      comes from its antecedent — "tu che *onori* scïenza e arte" is 2nd person on a `che` Layer 2
      tags 3rd;
    - the subject is coordinated (it carries a `conj` child, or its head carries more than one
      subject child), where agreement is with the whole coordination:
      "superbia, invidia e avarizia **sono**";
    - the head is 1st or 2nd person **plural**, where a singular or 3rd-person nominal regularly
      names one member of the group the verb agrees with — comitative "e io con lui / **volgemmo**
      i passi", inclusive "e amendue / **mostravam**", "uno innanzi altro **andavamo**". Only the
      plural allows this, so a singular head stays in scope;
    - either row carries a hand-verified `_AGREEMENT_EXEMPT_FLAGS` flag in its Layer-2 `note`
      (`AD_SENSUM`, `FOREIGN`) — the two classes no structural rule can state without importing a
      lexicon or a language identifier;
    - the subject is a **distributive** pronoun (`_DISTRIBUTIVE_LEMMAS`) under a plural head, which
      resumes the plural one member at a time: "vanno a vicenda **ciascuna** al giudizio";
    - the subject phrase **coordinates internally** — a `cc` child alongside an `nmod`/`conj`/
      `appos` child — under a plural head: "e l'uno e l'altro **coro**" is two choirs on one noun;
    - the plural head carries a **comitative** `con`-phrase and the subject is singular: "necesse
      con contingente … **fenno**". The third-person case of the 1/2-plural exclusion above;
    - the plural subject is **quantified** into a single measure — a `nummod` child, or a
      `_QUANTITY_LEMMAS` determiner — under a singular head: "cento miglia di corso nol **sazia**",
      "mille dugento con sessanta sei / anni **compié**", "non **è** molt' anni";
    - the head carries an `attr` **predicate nominal** agreeing with it while the subject does not,
      the attraction of a copula to its complement: "La prova … **son** l'opere seguite";
    - the head carries an **impersonal `si`** (`expl:impers`, or an `expl` Layer 2 notes as
      `impersonal`) with a plural subject postposed after it: "non si **convenia** più dolci salmi".
    """
    if morph_rows is None:
        return []

    children: dict[tuple[int, int], list[DepRow]] = {}
    for row in all_rows:
        children.setdefault((row.head_line, row.head_token), []).append(row)

    violations: list[Violation] = []
    for row in all_rows:
        if row.deprel not in _NSUBJ_DEPRELS:
            continue
        head = (row.head_line, row.head_token)
        verdict, feature = subject_agreement(
            (row.line, row.token), head, morph_rows, children)
        if verdict != "disagree":
            continue
        head_morph = _morph_at(morph_rows, *head)
        violations.append(
            Violation(row.line, "tag",
                      f"{row.deprel} {row.line}.{row.token} {row.word!r} disagrees with head "
                      f"{head[0]}.{head[1]} {head_morph.word!r}: {feature}")
        )
    return violations


# --- Noun-phrase role join (serve-time; Layer 3 <-> Layer 4) ------------------------


def index(data: dict[int, tuple[DepRow, ...]]) -> dict[tuple[int, int], DepRow]:
    """Flatten a loaded canto's rows into a `(line, token) -> DepRow` lookup."""
    return {(row.line, row.token): row for rows in data.values() for row in rows}


def np_role(span: Any, idx: dict[tuple[int, int], DepRow]) -> str:
    """A Layer-3 NP's clause function: the deprel of the Layer-4 row at its head token.

    Derived, not stored — `span` need only expose `.line`/`.head` (an `np.NPSpan`). Returns ""
    when no Layer-4 artifact covers that token."""
    row = idx.get((span.line, span.head))
    return row.deprel if row else ""


# --- Artifact I/O --------------------------------------------------------------------

# Tab-separated: one row per alpha token. Rectangular and free of tabs/newlines, so plain TSV
# round-trips without quoting and keeps git diffs token-granular, exactly like Layer 2. No
# sentinel is needed (contrast Layer 3): every source line has >= 1 alpha token, so "rows
# present for this line" already means "processed".
_TSV_HEADER = ("line", "token", "word", "deprel", "head_line", "head_token")


def _artifact_path(canticle: str, number: int) -> Path:
    return DEP_DIR / canticle / f"{number:02d}.tsv"


artifact_path = _artifact_path


def write_dep(canticle: str, number: int, lines: list[tuple[int, list[DepRow]]]) -> Path:
    path = _artifact_path(canticle, number)
    path.parent.mkdir(parents=True, exist_ok=True)
    out = ["\t".join(_TSV_HEADER)]
    for no, rows in lines:
        for row in sorted(rows, key=lambda r: r.token):
            out.append(
                "\t".join((str(no), str(row.token), row.word, row.deprel,
                           str(row.head_line), str(row.head_token)))
            )
    path.write_text("\n".join(out) + "\n", encoding="utf-8")
    return path


def has_dep(canticle: str, number: int) -> bool:
    return _artifact_path(canticle, number).exists()


def load_dep(canticle: str, number: int) -> dict[int, tuple[DepRow, ...]]:
    """Load a frozen dependency artifact: line-number -> DepRows (no model call)."""
    path = _artifact_path(canticle, number)
    if not path.exists():
        raise FileNotFoundError(path)
    grouped: dict[int, list[DepRow]] = {}
    for lineno, text in enumerate(path.read_text(encoding="utf-8").splitlines()):
        if lineno == 0 or not text:  # header / blank
            continue
        cells = text.split("\t")
        cells += [""] * (len(_TSV_HEADER) - len(cells))  # tolerate dropped trailing blanks
        no = int(cells[0])
        grouped.setdefault(no, []).append(
            DepRow(line=no, token=int(cells[1]), word=cells[2], deprel=cells[3],
                   head_line=int(cells[4]), head_token=int(cells[5]))
        )
    return {no: tuple(rows) for no, rows in grouped.items()}
