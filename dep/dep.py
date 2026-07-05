"""Build driver for Layer 4 (dependency / grammatical role) — a per-step generation script.

Like `morph/morph.py` (Layer 2) and `np/np.py` (Layer 3), the script that *generates* an
artifact lives in its own step directory (here `dep/`), while parsing, resolution, validation,
and I/O stay in the shared package (`dante_corpus/dep.py`, consumed by the runtime API). The
runtime API never calls a model.

Unlike Layer 2/3, which chunk source lines into fixed-size groups and align free-text model
output back to them by substring search, a dependency tree needs every head to resolve within
its parse unit — so lines are grouped into *sentences* (`dep.sentence_groups`) and the model is
given an authoritative numbered token list to cite indices from, rather than being asked to
reproduce words the code then has to re-find.

Generation resumes from its own output: each parse unit's rows are written back to the TSV as
soon as they validate, so an interrupted run continues where it stopped.

    uv run dep.py inferno -m ollama:gpt-oss        # all of Inferno (resumes)
    uv run dep.py inferno -c 1 -m ollama:gpt-oss   # just canto 1
    uv run dep.py inferno --force -m ...           # rebuild from scratch
    uv run dep.py inferno --check                  # code-only, no model
    uv run dep.py inferno -n                       # dry run: show pending units, no LLM
    uv run dep.py inferno --clean                  # remove parse units with hard violations

`--check` validates committed artifacts against the deterministic tokens (every token has
exactly one row, every head resolves in-unit, no cycles, at least one root per unit) and reports
soft violations (deprel outside the frozen UD vocabulary, more than one root in a unit,
`acl:relcl` heads that are not nominal).

When Layer-2 morphology is present, generation annotates the numbered token list with each
token's part of speech, and the `acl:relcl`-head soft check uses it too.
"""

import argparse
import sys
from pathlib import Path

from dante_corpus import api, dep, morph
from dante_corpus.tokenizer import has_alpha, tokenize
from llm7shi.statusline import StatusLine

SYSTEM_PROMPT = """\
You are a dependency parser for archaic Italian (Dante's Divine Comedy), following Universal
Dependencies (UD) relations as used for Italian.
For the given sentence you receive numbered source lines and a numbered token list. Output
ONLY a Markdown table with exactly one row per listed token, in order:
| Line | Token | Word | Deprel | Head Line | Head Token | Head Word |

Rules:
* Line and Token are copied from the token list; Word is copied verbatim from it.
* Deprel is a UD relation label (nsubj, obj, iobj, obl, det, amod, advmod, acl:relcl, aux, cop,
  mark, case, cc, conj, expl, nmod, xcomp, ccomp, advcl, appos, vocative, ...).
* Head Line / Head Token cite another listed token; Head Word is that token's word, copied
  verbatim, so the citation can be checked.
* The sentence's main predicate takes Deprel root with Head Line 0, Head Token 0, Head Word -.
* Heads may be on a different line than the token — enjambment is common in this text.
* A contracted preposition+article token (Nel, del, ...) acts as the preposition: case. A verb
  with a fused enclitic pronoun keeps the verb's own relation.
* A relative clause's verb attaches to its antecedent noun with acl:relcl; the relative pronoun
  (che, cui, qual, ...) takes its own role inside the clause (nsubj, obj, obl, ...).
* Output only the table, with no commentary before or after it.

Example input:
Parse the dependencies for this sentence:

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

Example output:
| Line | Token | Word | Deprel | Head Line | Head Token | Head Word |
|---|---|---|---|---|---|---|
| 1 | 1 | Nel | case | 1 | 2 | mezzo |
| 1 | 2 | mezzo | obl | 2 | 2 | ritrovai |
| 1 | 3 | del | case | 1 | 4 | cammin |
| 1 | 4 | cammin | nmod | 1 | 2 | mezzo |
| 1 | 5 | di | case | 1 | 7 | vita |
| 1 | 6 | nostra | det:poss | 1 | 7 | vita |
| 1 | 7 | vita | nmod | 1 | 4 | cammin |
| 2 | 1 | mi | expl | 2 | 2 | ritrovai |
| 2 | 2 | ritrovai | root | 0 | 0 | - |
| 2 | 3 | per | case | 2 | 5 | selva |
| 2 | 4 | una | det | 2 | 5 | selva |
| 2 | 5 | selva | obl | 2 | 2 | ritrovai |
| 2 | 6 | oscura | amod | 2 | 5 | selva |
| 3 | 1 | ché | mark | 3 | 6 | smarrita |
| 3 | 2 | la | det | 3 | 4 | via |
| 3 | 3 | diritta | amod | 3 | 4 | via |
| 3 | 4 | via | nsubj | 3 | 6 | smarrita |
| 3 | 5 | era | aux | 3 | 6 | smarrita |
| 3 | 6 | smarrita | advcl | 2 | 2 | ritrovai |
"""

RETRIES = 2


def _alpha_tokens(text: str) -> list[str]:
    return [t for t in tokenize(text) if has_alpha(t)]


def _units(lines: tuple[api.Line, ...], size: int) -> list[tuple[api.Line, ...]]:
    """Group a canto's lines into dependency parse units (see `dep.sentence_groups`)."""
    nos = [line.no for line in lines]
    texts = [line.text for line in lines]
    by_no = {line.no: line for line in lines}
    return [tuple(by_no[no] for no in group) for group in dep.sentence_groups(nos, texts, size)]


def _load_committed(canticle: str, number: int) -> list[tuple[int, list[dep.DepRow]]]:
    """Already-frozen rows for a canto, ordered by line number — the checkpoint to resume from."""
    if not dep.has_dep(canticle, number):
        return []
    data = dep.load_dep(canticle, number)
    return [(no, list(rows)) for no, rows in sorted(data.items())]


def _morph_rows(canticle: str, number: int) -> dict[int, list]:
    """Layer-2 rows per line for POS hints and the acl:relcl soft check, or {} when absent."""
    if not morph.has_morph(canticle, number):
        return {}
    return {no: list(rows) for no, rows in morph.load_morph(canticle, number).items()}


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


def _prompt(nos: list[int], texts: list[str], morph_rows: dict[int, list]) -> str:
    lines_block = "\n".join(f"{no} {text}" for no, text in zip(nos, texts))
    token_lines: list[str] = []
    for no, text in zip(nos, texts):
        tokens = _alpha_tokens(text)
        rows = morph_rows.get(no)
        for i, tok in enumerate(tokens, start=1):
            pos = f" ({rows[i - 1].pos})" if rows and i - 1 < len(rows) else ""
            token_lines.append(f"{no}.{i} {tok}{pos}")
    return (
        "Parse the dependencies for this sentence:\n\n"
        + lines_block
        + "\n\nTokens (Line.Token Word (POS)):\n"
        + "\n".join(token_lines)
    )


def _continue_if_missing(
    client, nos: list[int], texts: list[str], table_text: str, ui: StatusLine
) -> str:
    """If any listed token got no row (likely truncation), ask the client to continue."""
    try:
        partial, _ = dep.resolve_chunk(nos, texts, table_text)
    except ValueError:
        return table_text
    missing: list[str] = []
    for no, text in zip(nos, texts):
        tokens = _alpha_tokens(text)
        have = {row.token for row in partial.get(no, [])}
        for i, tok in enumerate(tokens, start=1):
            if i not in have:
                missing.append(f"{no}.{i} {tok}")
    if not missing:
        return table_text
    cont_prompt = (
        "The table was truncated. Please continue with rows for these tokens:\n\n"
        + "\n".join(missing)
    )
    cont_text = client(cont_prompt).text
    ui.stream.end()
    return _merge_tables(table_text + "\n" + cont_text)


def _hard_violations(
    nos: list[int], texts: list[str], rows_by_line: dict[int, list[dep.DepRow]],
    mismatches: list[str], morph_rows: dict[int, list] | None,
) -> list[str]:
    hard = list(mismatches)
    for v in dep.validate_unit(nos, texts, rows_by_line, morph_rows):
        if v.kind != "tag":
            hard.append(f"{v.line}:[{v.kind}] {v.detail}")
    return hard


def _try_parse(
    nos: list[int], texts: list[str], model: str, ui: StatusLine, label: str,
    log_path: Path | None = None, morph_rows: dict[int, list] | None = None,
) -> dict[int, list[dep.DepRow]] | None:
    """Call LLM and resolve; return rows-by-line on success, None after all retries fail."""
    from llm7shi import Client

    prompt = _prompt(nos, texts, morph_rows or {})
    for attempt in range(RETRIES + 1):
        client = Client(model=model, file=ui.stream, show_params=False)
        client.set_system_prompt(SYSTEM_PROMPT)
        table_text = client(prompt).text
        ui.stream.end()
        table_text = _merge_tables(table_text)
        table_text = _continue_if_missing(client, nos, texts, table_text, ui)
        try:
            rows_by_line, mismatches = dep.resolve_chunk(nos, texts, table_text)
            hard = _hard_violations(nos, texts, rows_by_line, mismatches, morph_rows)
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
    nos: list[int], texts: list[str], rows_by_line: dict[int, list[dep.DepRow]],
    morph_rows: dict[int, list] | None,
) -> tuple[list[morph.Violation], list[morph.Violation]]:
    """Split validate_unit results into (hard, soft). tag -> soft; rest -> hard."""
    hard, soft = [], []
    for v in dep.validate_unit(nos, texts, rows_by_line, morph_rows):
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

    units = _units(lines, size)
    pending = [unit for unit in units if any(line.no not in done for line in unit)]
    label = f"{canticle} {number}/{n_cantos}"
    if not pending:
        ui.log(f"[dim]Skip (complete): dep/{canticle}/{number:02d}.tsv[/dim]")
        return True
    if done:
        ui.log(f"Resume: dep/{canticle}/{number:02d}.tsv "
               f"({len(done)} line(s) done, {len(pending)} unit(s) left)")

    if dry_run:
        for unit in pending:
            nos = [line.no for line in unit]
            ui.log(f"  [dry-run] dep/{canticle}/{number:02d}.tsv "
                   f"lines {nos[0]}-{nos[-1]} ({len(nos)} line(s))")
        return True

    with ui.progress(len(lines), start=pending[0][0].no, label=label) as prog:
        for unit in pending:
            nos = [line.no for line in unit]
            prog.update(nos[0])
            texts = [line.text for line in unit]
            label = f"{canticle} {number}"
            rows_by_line = _try_parse(nos, texts, model, ui, label, log_path, morph_rows)
            if rows_by_line is None:
                # No per-line fallback: a lone line cannot host cross-line heads, so a parse
                # unit is the smallest unit worth retrying.
                ui.stream.error(f"  {label}: giving up at lines {nos[0]}-{nos[-1]}; "
                                f"earlier units saved for resume")
                return False
            unit_nos = set(nos)
            out = [(no, rows) for no, rows in out if no not in unit_nos]
            out.extend((no, rows_by_line.get(no, [])) for no in nos)
            out.sort(key=lambda item: item[0])
            dep.write_dep(canticle, number, out)
    ui.log(f"Wrote: dep/{canticle}/{number:02d}.tsv")
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
            _build_canto(canticle, number, n_cantos, model, size, force, dry_run, ui, log_path)
    return 0


def check(canticles: list[str], only: int | None) -> int:
    hard = 0
    soft = 0
    for canticle in canticles:
        numbers = [only] if only else list(api.cantos(canticle))
        for number in numbers:
            if not dep.has_dep(canticle, number):
                print(f"Missing: dep/{canticle}/{number:02d}.tsv", file=sys.stderr)
                hard += 1
                continue
            data = dep.load_dep(canticle, number)
            morph_rows = _morph_rows(canticle, number)
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
                hard_vs, soft_vs = _classify_violations(unit, unit_texts, rows_by_line, morph_rows)
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


def clean(canticles: list[str], size: int, only: int | None) -> int:
    removed = 0
    for canticle in canticles:
        numbers = [only] if only else list(api.cantos(canticle))
        for number in numbers:
            if not dep.has_dep(canticle, number):
                continue
            data = dep.load_dep(canticle, number)
            lines = api.canto(canticle, number).lines()
            nos_all = [line.no for line in lines]
            texts_all = [line.text for line in lines]
            text_by_no = dict(zip(nos_all, texts_all))

            # Remove parse units with any hard violation (soft is reported, not cleaned).
            bad: set[int] = set()
            for unit in dep.sentence_groups(nos_all, texts_all, size):
                unit_texts = [text_by_no[no] for no in unit]
                rows_by_line = {no: list(data.get(no, ())) for no in unit}
                hard_vs, _ = _classify_violations(unit, unit_texts, rows_by_line, None)
                if hard_vs:
                    bad.update(unit)
            has_data = bad & data.keys()
            if has_data:
                for no in bad:
                    data.pop(no, None)
                out = sorted(data.items())
                dep.write_dep(canticle, number, [(no, list(rows)) for no, rows in out])
                print(f"Cleaned dep/{canticle}/{number:02d}.tsv — removed lines {sorted(bad)}")
            removed += len(has_data)
    print(f"clean complete: {removed} line(s) removed")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(prog="dep.py")
    parser.add_argument("canticles", nargs="+", help="canticle names, e.g. inferno")
    parser.add_argument("-m", "--model", help="LLM, e.g. ollama:gpt-oss (required unless --check)")
    parser.add_argument("--chunk", type=int, default=dep.MAX_UNIT_LINES,
                        help=f"max lines per parse unit (default {dep.MAX_UNIT_LINES})")
    parser.add_argument("-c", "--canto", type=int, help="limit to a single canto number")
    parser.add_argument("--force", action="store_true", help="rebuild even if artifact exists")
    parser.add_argument("--check", action="store_true", help="validate artifacts, no model call")
    parser.add_argument("--clean", action="store_true",
                        help="remove parse units with hard violations, then exit")
    parser.add_argument("-n", "--dry-run", action="store_true",
                        help="show pending parse units without calling the LLM")
    parser.add_argument("--log", nargs="?", const="dep.log", metavar="FILE",
                        help="append failed LLM responses to FILE (default: dep.log)")
    args = parser.parse_args()

    if args.check:
        return check(args.canticles, args.canto)
    if args.clean:
        return clean(args.canticles, args.chunk, args.canto)
    if args.dry_run:
        return build(args.canticles, args.model or "", args.chunk, args.force, True, args.canto)
    log_path = Path(args.log) if args.log else None
    if not args.model:
        parser.error("--model is required for building (or pass --check / --dry-run)")
    return build(args.canticles, args.model, args.chunk, args.force, False, args.canto, log_path)


if __name__ == "__main__":
    sys.exit(main())
