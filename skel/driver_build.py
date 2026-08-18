"""Build driver for Layer 5 (initial extraction and whole-unit regeneration)."""

from __future__ import annotations

from pathlib import Path

from dante_corpus import api, dep, morph, skel
from llm7shi.statusline import StatusLine

try:
    from .driver_ui import (
        _alpha_tokens,
        _case_rows,
        _dep_rows,
        _load_committed,
        _log_field_notes,
        _morph_rows,
        _np_rows,
        _split_field_notes,
        _units,
    )
except ImportError:
    from driver_ui import (
        _alpha_tokens,
        _case_rows,
        _dep_rows,
        _load_committed,
        _log_field_notes,
        _morph_rows,
        _np_rows,
        _split_field_notes,
        _units,
    )

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


def _merge_tables(text: str) -> str:
    """Merge multiple Markdown pipe-tables into one."""
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
    cont_text, _ = _split_field_notes(cont_text)
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
    """Call LLM and resolve; return rows-by-line on success, None after all retries fail."""
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
