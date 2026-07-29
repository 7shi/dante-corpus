"""Build driver for the pronoun case annex — a per-step generation script.

Mirrors `morph/morph.py`: the model proposes a Markdown table per chunk of source lines,
the table is aligned to the deterministic positions (`case.align_unit`) and frozen as
`case/<canticle>/NN.tsv`. The runtime API never calls a model.

What differs from Layer 2 is the *unit* and the *scope*. The unit is the parse unit
(`dep.sentence_groups`, derived from the source punctuation alone, not from the `dep/`
artifact) because case is decided by the governing verb, which is frequently on another
line; consecutive units are merged up to `--chunk` lines per call. The scope is every
pronoun-POS token, read off Layer 2's own `pos` column, so a line with no pronoun costs
nothing and produces no rows.

    uv run case.py inferno -m google:gemma-4-31b-it     # all of Inferno (resumes)
    uv run case.py inferno -c 1 -m ...                  # just canto 1
    uv run case.py inferno --force -m ...               # rebuild from scratch
    uv run case.py inferno --check                      # code-only, no model
    uv run case.py inferno -n                           # dry run: pending chunks, no LLM
    uv run case.py inferno --clean                      # drop chunks with violations
    uv run case.py inferno --stats                      # census + the dep adjudication

**Blind by construction.** The prompt carries the passage and the marked pronouns and
nothing else — no `dep/` row, no `skel/` row, no hint that a position is disputed. That
blindness is what makes the column a genuine third independent read rather than an artifact
manufactured to close Layer-5 violations, and it is the design constraint the whole annex
rests on (`case/PLAN.md`, *Independence*). `--stats`' adjudication section is therefore a
**post-freeze** report: generate, validate, commit, *then* join against `dep`.
"""

import argparse
import sys
from collections import Counter
from pathlib import Path

from dante_corpus import api, case, dep, morph
from llm7shi.statusline import StatusLine

SYSTEM_PROMPT = """\
You are a morphological analyzer for archaic Italian (Dante's Divine Comedy).
For the given passage, name the grammatical case of every pronoun marked between ** and **.
Output ONLY a Markdown table, one row per marked pronoun, with columns:
| Line | Word | Case |

Rules:
* Process the marked pronouns strictly left to right, line by line; emit exactly one row per
  marked pronoun, and none for any unmarked word.
* Copy Word verbatim from the source, without the ** markers and without the line number.
* Case must be exactly one of: nominative, accusative, dative, genitive, ablative, locative,
  vocative, reflexive.
* Use nominative for a subject, accusative for a direct object, dative for an indirect
  object or the person something happens to, genitive for a possessor.
* Use reflexive for a clitic that refers back to the subject or belongs to the verb itself,
  introducing no participant distinct from the subject: "io **mi** volsi", "**si** mosse",
  and impersonal or passive si ("**si** vede" = "one sees"). A clitic naming someone other
  than the subject is accusative or dative as usual — in "**mi** si fu offerto" the si is
  reflexive but the mi is dative, and in "aiuta**mi**" the mi is accusative.
* Use ablative for a partitive or prepositional oblique (ne = "of it", "from there"), and
  locative only where ci / vi means "here" / "there". Ablative also covers accompaniment and
  means, including the archaic fused forms meco / teco / seco / nosco / vosco ("with me",
  "with you", "with him"): there is no separate instrumental.
* Use vocative for a pronoun addressing the hearer directly, not filling a slot of the verb
  (e.g. "O **tu** che ..."). A pronoun that is the subject of the verb is nominative even
  when the sentence is addressed to someone.
* A word may fuse two pronouns (e.g. gliel'). Give one case per pronoun, in reading order,
  joined with + (e.g. dative+accusative).
* A word may fuse a verb and a pronoun (e.g. andarmi, dissemi). Give the case of the
  pronoun only.
* Output only the table, with no commentary before or after it.

Example input:
1 Nel mezzo del cammin di nostra vita
2 **mi** ritrovai per una selva oscura,
3 ché la diritta via era smarrita.
4 Ahi quanto a dir qual era è cosa dura
5 esta selva selvaggia e aspra e forte
6 **che** nel pensier rinova la paura!

Example output:
| Line | Word | Case |
|---|---|---|
| 2 | mi | reflexive |
| 6 | che | nominative |
"""

RETRIES = 2


def _morph_rows(canticle: str, number: int) -> dict[int, tuple[morph.MorphRow, ...]]:
    return morph.load_morph(canticle, number) if morph.has_morph(canticle, number) else {}


def _units(canticle: str, number: int) -> list[list[int]]:
    """The canto's parse units, from the source punctuation alone (no `dep/` artifact)."""
    lines = api.canto(canticle, number).lines()
    return dep.sentence_groups([l.no for l in lines], [l.text for l in lines])


def _chunks(units: list[list[int]], size: int) -> list[list[int]]:
    """Merge consecutive parse units up to `size` lines. A unit is never split: the whole
    point of the unit is that the governing verb of a clitic stays in the same call."""
    out: list[list[int]] = []
    current: list[int] = []
    for unit in units:
        if current and len(current) + len(unit) > size:
            out.append(current)
            current = []
        current.extend(unit)
    if current:
        out.append(current)
    return out


def _marked(text: str, tokens: set[int]) -> str:
    """`text` with each listed alpha token (1-based, Layer-1 numbering) wrapped in `**`."""
    from dante_corpus.tokenizer import has_alpha, tokenize

    out, seen = [], 0
    for tok in tokenize(text):
        if has_alpha(tok):
            seen += 1
            if seen in tokens:
                out.append(f"**{tok}**")
                continue
        out.append(tok)
    return "".join(out)


def _prompt(nos: list[int], texts: dict[int, str], expected: list[case.Target]) -> str:
    by_line: dict[int, set[int]] = {}
    for target in expected:
        by_line.setdefault(target.line, set()).add(target.token)
    body = "\n".join(
        f"{no} {_marked(texts[no], by_line.get(no, set()))}" for no in nos
    )
    return "Name the case of every marked pronoun in this passage:\n\n" + body


def _try_chunk(nos: list[int], texts: dict[int, str],
               morph_rows: dict[int, tuple[morph.MorphRow, ...]],
               model: str, ui: StatusLine, label: str,
               log_path: Path | None = None) -> dict[int, list[case.CaseRow]] | None:
    """Call the LLM for one chunk and align; None after all retries fail."""
    from llm7shi import Client

    expected = case.unit_targets(nos, morph_rows)
    if not expected:
        return {}
    prompt = _prompt(nos, texts, expected)

    for attempt in range(RETRIES + 1):
        client = Client(model=model, file=ui.stream, show_params=False)
        client.set_system_prompt(SYSTEM_PROMPT)
        table_text = client(prompt).text
        ui.stream.end()
        try:
            rows = case.align_unit(expected, table_text)
            grouped: dict[int, list[case.CaseRow]] = {}
            for row in rows:
                grouped.setdefault(row.line, []).append(row)
            errors = [
                f"{no}:{v.kind}:{v.detail}"
                for no in nos
                for v in case.validate_line(no, texts[no], morph_rows.get(no, ()),
                                            grouped.get(no, []))
            ]
            if errors:
                raise ValueError("; ".join(errors[:6]))
            return grouped
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


def _build_canto(canticle: str, number: int, n_cantos: int, model: str, size: int,
                 force: bool, dry_run: bool, ui: StatusLine,
                 log_path: Path | None = None) -> bool:
    lines = api.canto(canticle, number).lines()
    texts = {line.no: line.text for line in lines}
    morph_rows = _morph_rows(canticle, number)
    if not morph_rows:
        ui.stream.error(f"  {canticle} {number}: no morph artifact; skipped")
        return False

    committed: dict[int, list[case.CaseRow]] = {}
    if not force and case.has_case(canticle, number):
        committed = {no: list(rows)
                     for no, rows in case.load_case(canticle, number).items()}
    done = set(committed)

    units = _units(canticle, number)
    all_chunks = _chunks(units, size)
    # A chunk is pending when a line that *should* carry rows has none yet. Lines with no
    # pronoun never appear in the artifact, so they can't be used as the resume marker.
    pending = []
    for chunk in all_chunks:
        wanted = {t.line for t in case.unit_targets(chunk, morph_rows)}
        if wanted and not wanted <= done:
            pending.append(chunk)

    label = f"{canticle} {number}/{n_cantos}"
    if not pending:
        ui.log(f"[dim]Skip (complete): case/{canticle}/{number:02d}.tsv[/dim]")
        return True
    if done:
        ui.log(f"Resume: case/{canticle}/{number:02d}.tsv "
               f"({len(done)} line(s) done, {len(pending)} chunk(s) left)")

    if dry_run:
        for chunk in pending:
            n = len(case.unit_targets(chunk, morph_rows))
            ui.log(f"  dry-run: case/{canticle}/{number:02d}.tsv "
                   f"lines {chunk[0]}-{chunk[-1]} ({n} pronoun(s))")
        return True

    def flush() -> None:
        case.write_case(canticle, number,
                        [(no, committed[no]) for no in sorted(committed)])

    with ui.progress(len(lines), start=pending[0][0], label=label) as prog:
        for chunk in pending:
            prog.update(chunk[0])
            short = f"{canticle} {number}"
            grouped = _try_chunk(chunk, texts, morph_rows, model, ui, short, log_path)
            if grouped is None and len(chunk) > 1:
                ui.stream.error(f"  {short}: chunk failed, retrying unit by unit")
                grouped = {}
                for unit in [u for u in units if u[0] in chunk]:
                    result = _try_chunk(unit, texts, morph_rows, model, ui, short, log_path)
                    if result is None:
                        ui.stream.error(f"  {short}: giving up at line {unit[0]}; "
                                        f"earlier lines saved for resume")
                        flush()
                        return False
                    grouped.update(result)
            elif grouped is None:
                ui.stream.error(f"  {short}: giving up at line {chunk[0]}; "
                                f"earlier lines saved for resume")
                flush()
                return False
            for no in chunk:
                committed.pop(no, None)
            committed.update({no: rows for no, rows in grouped.items() if rows})
            flush()
    ui.log(f"Wrote: case/{canticle}/{number:02d}.tsv")
    return True


def build(canticles: list[str], model: str, size: int, force: bool, dry_run: bool,
          only: int | None, log_path: Path | None = None) -> int:
    if log_path:
        log_path.write_text("", encoding="utf-8")
    ui = StatusLine()
    for canticle in canticles:
        all_numbers = list(api.cantos(canticle))
        n_cantos = len(all_numbers)
        numbers = [only] if only else all_numbers
        for number in numbers:
            _build_canto(canticle, number, n_cantos, model, size, force, dry_run, ui,
                         log_path)
    return 0


def check(canticles: list[str], only: int | None) -> int:
    """Formal checks only — there is no deterministic ground truth for case, and the one
    cross-check that exists (`dep`'s obj/iobj) is the very judgment under adjudication, so
    it belongs in `--stats`, never here (see case/PLAN.md)."""
    hard = 0
    for canticle in canticles:
        numbers = [only] if only else list(api.cantos(canticle))
        for number in numbers:
            if not case.has_case(canticle, number):
                print(f"Missing: case/{canticle}/{number:02d}.tsv", file=sys.stderr)
                hard += 1
                continue
            data = case.load_case(canticle, number)
            morph_rows = _morph_rows(canticle, number)
            missing: list[int] = []
            for line in api.canto(canticle, number).lines():
                rows = list(data.get(line.no, ()))
                expected = case.targets(line.no, list(morph_rows.get(line.no, ())))
                if expected and not rows:
                    missing.append(line.no)
                    hard += 1
                    continue
                for v in case.validate_line(line.no, line.text,
                                            morph_rows.get(line.no, ()), rows):
                    print(f"{canticle} {number}:{v.line} [{v.kind}] {v.detail}",
                          file=sys.stderr)
                    hard += 1
            if missing:
                print(f"{canticle} {number}: missing lines {missing}", file=sys.stderr)
    print(f"check complete: {hard} hard violation(s)")
    return 1 if hard else 0


def clean(canticles: list[str], size: int, only: int | None) -> int:
    """Drop every chunk holding a violation, so the next build re-requests exactly those."""
    removed = 0
    for canticle in canticles:
        numbers = [only] if only else list(api.cantos(canticle))
        for number in numbers:
            if not case.has_case(canticle, number):
                continue
            data = {no: list(rows)
                    for no, rows in case.load_case(canticle, number).items()}
            morph_rows = _morph_rows(canticle, number)
            texts = {line.no: line.text
                     for line in api.canto(canticle, number).lines()}
            bad: set[int] = set()
            for chunk in _chunks(_units(canticle, number), size):
                for no in chunk:
                    rows = data.get(no, [])
                    if case.validate_line(no, texts[no], morph_rows.get(no, ()), rows):
                        bad.update(chunk)
                        break
            hit = bad & data.keys()
            if hit:
                for no in hit:
                    data.pop(no, None)
                case.write_case(canticle, number,
                                [(no, data[no]) for no in sorted(data)])
                print(f"Cleaned case/{canticle}/{number:02d}.tsv "
                      f"— removed lines {sorted(hit)}")
            removed += len(hit)
    print(f"clean complete: {removed} line(s) removed")
    return 0


# `dep` names the same distinctions with a different vocabulary. This is the only cross-check
# that exists, and it is exactly what step 4 hand-verifies — a contradiction here is a
# *candidate* for a Layer-4 correction round, never an automatic edit and never a checker
# exemption (case/PLAN.md, *Adjudication output, not exemption*).
#
# `nsubj` was added after the Inferno-1 smoke test: three of its rows are relative pronouns
# that are plainly the subject of their clause, read `nominative` by `case` and `obj` by
# Layer 4. The pilot sampled clitics only and so never saw that class, and with the original
# obj/iobj-only mapping it fell out of the candidate list entirely.
_DEP_EXPECTS = {"obj": "accusative", "iobj": "dative", "nsubj": "nominative"}

# Only a value that competes for the same slot counts as a contradiction. `reflexive` against
# `obj` is not one: it is a level difference (the reflexive of `mi volsi` may well be Layer 4's
# `obj`), and folding it in would manufacture candidates out of a distinction both layers get
# right in their own terms.
_CORE = frozenset({"nominative", "accusative", "dative"})

# Pairs that cannot both be right, for deprels with no single expected case. `obl` admits
# `ablative` / `dative` / `locative` and so has no entry above, but a pronoun Layer 4 attached
# as an oblique cannot bear the subject case. Reported separately so it does not distort the
# agreement rates.
_IMPOSSIBLE = frozenset({("obl", "nominative")})


# The oblique tail is the vocabulary's open question, deferred to after the corpus pass by
# an explicit decision (case/CORRECTIONS.md, *The oblique tail*). `ablative` is a residual
# class, and whether `genitive` earns a separate value is decided from these counts — by word
# form, because the whole question is whether one clitic (`ne`) is being split on meaning
# alone. Folding a value into `ablative` afterwards is a mechanical rewrite of the frozen
# TSVs, not a regeneration, so measuring first costs nothing.
_OBLIQUE = ("ablative", "genitive", "locative")


def stats(canticles: list[str], only: int | None) -> int:
    census = Counter()
    by_word = Counter()
    pos_census = Counter()
    oblique_by_word = Counter()
    covered = 0
    agree = Counter()
    contradictions: list[str] = []
    impossible: list[str] = []

    for canticle in canticles:
        numbers = [only] if only else list(api.cantos(canticle))
        for number in numbers:
            if not case.has_case(canticle, number):
                continue
            data = case.load_case(canticle, number)
            morph_rows = _morph_rows(canticle, number)
            dep_rows = dep.load_dep(canticle, number) if dep.has_dep(canticle, number) else {}
            dep_idx = {(r.line, r.token): r for rows in dep_rows.values() for r in rows}
            for no, rows in data.items():
                by_pos = {index: row.pos
                          for index, row in enumerate(morph_rows.get(no, ()), start=1)}
                for row in rows:
                    covered += 1
                    for value in row.cases():
                        census[value] += 1
                        if value in _OBLIQUE:
                            oblique_by_word[(value, row.word.lower())] += 1
                    by_word[(row.word.lower(), row.case)] += 1
                    pos_census[by_pos.get(row.token, "")] += 1
                    dep_row = dep_idx.get((row.line, row.token))
                    if dep_row is None:
                        continue
                    for value in row.cases():
                        if (dep_row.deprel, value) in _IMPOSSIBLE:
                            impossible.append(
                                f"{canticle} {number}:{row.line}.{row.token} {row.word!r} "
                                f"case={value} vs dep={dep_row.deprel}")
                    want = _DEP_EXPECTS.get(dep_row.deprel)
                    if want is None:
                        continue
                    values = row.cases()
                    if want in values:
                        agree[dep_row.deprel] += 1
                    elif any(v in _CORE for v in values):
                        agree[f"{dep_row.deprel}!"] += 1
                        contradictions.append(
                            f"{canticle} {number}:{row.line}.{row.token} {row.word!r} "
                            f"case={row.case} vs dep={dep_row.deprel}")

    print(f"rows: {covered}")
    print(f"vocabulary: {census.most_common()}")
    print(f"pos: {pos_census.most_common(10)}")

    total = sum(census.values())
    tail = sum(census[v] for v in _OBLIQUE)
    print(f"\noblique tail: {tail} of {total} "
          f"({tail / total:.1%} — the vocabulary's open question)" if total else "")
    for value in _OBLIQUE:
        forms = [(w, n) for (v, w), n in oblique_by_word.items() if v == value]
        forms.sort(key=lambda item: -item[1])
        print(f"  {value:<10} {census[value]:>5}  {forms[:8]}")
    print("  -> a value whose forms are a subset of another's is a *meaning* split of it,")
    print("     not a slot it fills, and folds into `ablative` by a mechanical rewrite.")
    print("\nagreement with dep (post-freeze adjudication input, not a check):")
    for deprel, want in _DEP_EXPECTS.items():
        ok, no = agree[deprel], agree[f"{deprel}!"]
        total = ok + no
        rate = f"{ok / total:.0%}" if total else "n/a"
        print(f"  dep={deprel:<5} ({want}): {ok} agree, {no} contradict ({rate})")
    print(f"\ncontradictions: {len(contradictions)} "
          f"— candidates for a hand-verified Layer-4 round, not automatic edits")
    for item in contradictions[:40]:
        print(f"  {item}")
    if len(contradictions) > 40:
        print(f"  ... and {len(contradictions) - 40} more")

    print(f"\nimpossible pairings: {len(impossible)} "
          f"— combinations neither layer can be right about together")
    for item in impossible[:20]:
        print(f"  {item}")
    if len(impossible) > 20:
        print(f"  ... and {len(impossible) - 20} more")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(prog="case.py")
    parser.add_argument("canticles", nargs="+", help="canticle names, e.g. inferno")
    parser.add_argument("-m", "--model", help="LLM, e.g. google:gemma-4-31b-it")
    parser.add_argument("--chunk", type=int, default=12,
                        help="max lines per LLM call; parse units are never split (default 12)")
    parser.add_argument("-c", "--canto", type=int, help="limit to a single canto number")
    parser.add_argument("--force", action="store_true", help="rebuild even if artifact exists")
    parser.add_argument("--check", action="store_true", help="validate artifacts, no model call")
    parser.add_argument("--clean", action="store_true",
                        help="remove chunks with violations, then exit")
    parser.add_argument("--stats", action="store_true",
                        help="census + the post-freeze dep adjudication, no model call")
    parser.add_argument("-n", "--dry-run", action="store_true",
                        help="show pending chunks without calling the LLM")
    parser.add_argument("--log", nargs="?", const="case.log", metavar="FILE",
                        help="append failed LLM responses to FILE (default: case.log)")
    args = parser.parse_args()

    if args.check:
        return check(args.canticles, args.canto)
    if args.stats:
        return stats(args.canticles, args.canto)
    if args.clean:
        return clean(args.canticles, args.chunk, args.canto)
    if args.dry_run:
        return build(args.canticles, args.model or "", args.chunk, args.force, True,
                     args.canto)
    if not args.model:
        parser.error("--model is required for building (or pass --check / --stats / --dry-run)")
    log_path = Path(args.log) if args.log else None
    return build(args.canticles, args.model, args.chunk, args.force, False, args.canto,
                 log_path)


if __name__ == "__main__":
    sys.exit(main())
