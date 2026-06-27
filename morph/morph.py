"""Build driver for Layer 2 (morphology) — a per-step generation script.

Like `02-markup/markup.py` in the dante-analyze project, the script that *generates* an
artifact lives in its own step directory (here `morph/`), while the parsing, alignment, and
I/O it depends on stay in the shared package (`dante_corpus/morph.py`, consumed by the
runtime API). A local LLM proposes a Markdown word table per chunk of lines, which is parsed
and aligned to the deterministic tokens (`morph.align_chunk`) and frozen as
`morph/<canticle>/NN.tsv`. The runtime API never calls a model.

Generation resumes from its own output: each chunk's rows are written back to the TSV as
soon as they validate, so an interrupted run continues where it stopped — already-committed
lines are skipped and only the remaining chunks are requested.

    uv run morph.py inferno -m ollama:gpt-oss        # all of Inferno (resumes)
    uv run morph.py inferno -c 1 -m ollama:gpt-oss   # just canto 1
    uv run morph.py inferno --force -m ...           # rebuild from scratch
    uv run morph.py inferno --check                  # code-only, no model
    uv run morph.py inferno -n                       # dry run: show pending chunks, no LLM
    uv run morph.py inferno --clean                  # remove chunks with count violations

`--check` validates committed artifacts against the deterministic tokens (every token gets
exactly one row; words are verbatim; closed-tag membership) — the structural verification bar.
"""

import argparse
import sys
from pathlib import Path

from dante_corpus import api, morph
from dante_corpus.statusline import StatusLine

SYSTEM_PROMPT = """\
You are a morphological analyzer for archaic Italian (Dante's Divine Comedy).
For the given source lines, output ONLY a Markdown table, one row per word, with columns:
| Word | Lemma | Part of Speech | Gender | Number | Person | Tense | Mood | Note |

Rules:
* Process words strictly left to right; emit exactly one row per word and copy Word verbatim
  from the source (do not include the leading line number).
* Decompose contractions in the Lemma (e.g. Nel -> in+il); keep the Word itself intact.
* Separate words linked by an apostrophe into separate rows (e.g. ch' and i').
* Exclude quotation marks. Apostrophes in contractions or elisions are not quotation marks.
* Leave a cell blank when not applicable.
* Keep Note brief (e.g. archaic, apocope, contraction, elision).
* Output only the table, with no commentary before or after it.

Example input:
1 Nel mezzo del cammin di nostra vita
2 mi ritrovai per una selva oscura,

Example output:
| Word | Lemma | Part of Speech | Gender | Number | Person | Tense | Mood | Note |
|---|---|---|---|---|---|---|---|---|
| Nel | in+il | preposition+article | m. | sg. | | | | contraction |
| mezzo | mezzo | noun | m. | sg. | | | | |
| del | di+il | preposition+article | m. | sg. | | | | contraction |
| cammin | cammino | noun | m. | sg. | | | | apocope |
| di | di | preposition | | | | | | |
| nostra | nostro | adjective | f. | sg. | | | | |
| vita | vita | noun | f. | sg. | | | | |
| mi | mi | pronoun | | sg. | 1 | | | reflexive |
| ritrovai | ritrovare | verb | | sg. | 1 | remote past | indicative | |
| per | per | preposition | | | | | | |
| una | uno | article | f. | sg. | | | | indefinite |
| selva | selva | noun | f. | sg. | | | | |
| oscura | oscuro | adjective | f. | sg. | | | | |
"""

RETRIES = 2


def _chunks(lines: tuple[api.Line, ...], size: int):
    for start in range(0, len(lines), size):
        yield lines[start : start + size]


def _generate_table(prompt: str, model: str, stream) -> str:
    from llm7shi import Client

    client = Client(
        model=model,
        file=stream,
        show_params=False,
    )
    client.set_system_prompt(SYSTEM_PROMPT)

    response = client(prompt)
    return response.text


def _load_committed(canticle: str, number: int) -> list[tuple[int, list[morph.MorphRow]]]:
    """Already-frozen rows for a canto, ordered by line number — the checkpoint to resume from."""
    if not morph.has_morph(canticle, number):
        return []
    data = morph.load_morph(canticle, number)
    return [(no, list(rows)) for no, rows in sorted(data.items())]


def _try_align(nos: list[int], texts: list[str], model: str,
               ui: StatusLine, label: str,
               log_path: Path | None = None) -> dict | None:
    """Call LLM and align; return aligned dict on success, None after all retries fail."""
    prompt = "Create a word table for these lines:\n\n" + "\n".join(
        f"{no} {text}" for no, text in zip(nos, texts)
    )
    for attempt in range(RETRIES + 1):
        table_text = _generate_table(prompt, model, ui.stream)
        ui.stream.end()
        try:
            aligned = morph.align_chunk(nos, texts, table_text)
            aligned, word_errors = morph.fix_aligned_words(nos, texts, aligned)
            count_errors = [
                f"{no}:{v.detail}"
                for no, text in zip(nos, texts)
                for v in morph.validate_line(no, text, list(aligned.get(no, [])))
                if v.kind == "count"
            ]
            hard = word_errors + count_errors
            if hard:
                raise ValueError("; ".join(hard))
            return aligned
        except ValueError as exc:
            msg = (f"  {label} lines {nos[0]}-{nos[-1]}: {exc} "
                   f"(attempt {attempt + 1}/{RETRIES + 1})")
            ui.log(msg)
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
    line_no: int, text: str, rows: list[morph.MorphRow]
) -> tuple[list[morph.Violation], list[morph.Violation]]:
    """Split validate_line results into (hard, soft). tag -> soft; count/word -> hard."""
    hard, soft = [], []
    for v in morph.validate_line(line_no, text, rows):
        (soft if v.kind == "tag" else hard).append(v)
    return hard, soft


def _build_canto(canticle: str, number: int, n_cantos: int, model: str, size: int,
                 force: bool, dry_run: bool, ui: StatusLine,
                 log_path: Path | None = None) -> bool:
    canto = api.canto(canticle, number)
    lines = canto.lines()
    out = [] if force else _load_committed(canticle, number)
    done = {no for no, _ in out}

    # Chunks are atomic — a chunk is written back only after all its lines validate — so a
    # previously-finished chunk has every line in `done`. Re-request only the rest.
    pending = [chunk for chunk in _chunks(lines, size)
               if any(line.no not in done for line in chunk)]
    label = f"{canticle} {number}/{n_cantos}"
    if not pending:
        ui.log(f"[dim]Skip (complete): morph/{canticle}/{number:02d}.tsv[/dim]")
        return True
    if done:
        ui.log(f"Resume: morph/{canticle}/{number:02d}.tsv "
               f"({len(done)} line(s) done, {len(pending)} chunk(s) left)")

    if dry_run:
        for chunk in pending:
            nos = [line.no for line in chunk]
            ui.log(f"  [dry-run] morph/{canticle}/{number:02d}.tsv "
                   f"lines {nos[0]}-{nos[-1]} ({len(nos)} line(s))")
        return True

    with ui.progress(len(lines), start=pending[0][0].no, label=label) as prog:
        for chunk in pending:
            nos = [line.no for line in chunk]
            prog.update(nos[0])
            texts = [line.text for line in chunk]
            label = f"{canticle} {number}"
            aligned = _try_align(nos, texts, model, ui, label, log_path)
            if aligned is None and len(chunk) > 1:
                ui.log(f"  {label}: chunk failed, retrying line by line")
                aligned = {}
                for line in chunk:
                    result = _try_align([line.no], [line.text], model, ui, label, log_path)
                    if result is None:
                        ui.log(f"  {label}: giving up at line {line.no}; "
                               f"earlier lines saved for resume")
                        return False
                    aligned.update(result)
            elif aligned is None:
                ui.log(f"  {label}: giving up at line {nos[0]}; "
                       f"earlier lines saved for resume")
                return False
            chunk_nos = {line.no for line in chunk}
            out = [(no, rows) for no, rows in out if no not in chunk_nos]
            out.extend((line.no, aligned[line.no]) for line in chunk)
            out.sort(key=lambda item: item[0])
            morph.write_morph(canticle, number, out)
    ui.log(f"Wrote: morph/{canticle}/{number:02d}.tsv")
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
            if not morph.has_morph(canticle, number):
                print(f"Missing: morph/{canticle}/{number:02d}.tsv", file=sys.stderr)
                hard += 1
                continue
            data = morph.load_morph(canticle, number)
            missing: list[int] = []
            for line in api.canto(canticle, number).lines():
                rows = list(data.get(line.no, ()))
                hard_vs, soft_vs = _classify_violations(line.no, line.text, rows)
                for v in hard_vs:
                    if not rows and v.kind == "count":
                        missing.append(v.line)
                    else:
                        print(f"{canticle} {number}:{v.line} [{v.kind}] {v.detail}",
                              file=sys.stderr)
                    hard += 1
                for v in soft_vs:
                    soft += 1
                    print(f"{canticle} {number}:{v.line} [{v.kind}] {v.detail}",
                          file=sys.stderr)
            if missing:
                print(f"{canticle} {number}: missing lines {missing}", file=sys.stderr)
    print(f"check complete: {hard} hard, {soft} soft violation(s)")
    return 1 if hard else 0


def clean(canticles: list[str], size: int, only: int | None) -> int:
    removed = 0
    fixed = 0
    for canticle in canticles:
        numbers = [only] if only else list(api.cantos(canticle))
        for number in numbers:
            if not morph.has_morph(canticle, number):
                continue
            data = morph.load_morph(canticle, number)
            lines = api.canto(canticle, number).lines()

            # Remove chunks with any violation (hard or soft)
            bad: set[int] = set()
            for chunk in _chunks(lines, size):
                for line in chunk:
                    rows = list(data.get(line.no, ()))
                    hard_vs, soft_vs = _classify_violations(line.no, line.text, rows)
                    if hard_vs or soft_vs:
                        for l in chunk:
                            bad.add(l.no)
                        break
            has_data = bad & data.keys()
            if has_data:
                for no in bad:
                    data.pop(no, None)

            # Fix trailing punctuation in remaining lines
            present = [l for l in lines if l.no in data]
            fixed_data, _ = morph.fix_aligned_words(
                [l.no for l in present],
                [l.text for l in present],
                {no: list(rows) for no, rows in data.items()},
            )
            word_fixed = [no for no, rows in fixed_data.items()
                          if any(r.word != f.word
                                 for r, f in zip(data[no], rows))]
            for no in word_fixed:
                data[no] = tuple(fixed_data[no])

            if has_data or word_fixed:
                out = sorted(data.items())
                morph.write_morph(canticle, number, [(no, list(rows)) for no, rows in out])
                if has_data:
                    print(f"Cleaned morph/{canticle}/{number:02d}.tsv"
                          f" — removed lines {sorted(bad)}")
                if word_fixed:
                    print(f"Fixed words morph/{canticle}/{number:02d}.tsv"
                          f" — lines {sorted(word_fixed)}")
            removed += len(has_data)
            fixed += len(word_fixed)
    print(f"clean complete: {removed} line(s) removed, {fixed} line(s) word-fixed")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(prog="morph.py")
    parser.add_argument("canticles", nargs="+", help="canticle names, e.g. inferno")
    parser.add_argument("-m", "--model", help="LLM, e.g. ollama:gpt-oss (required unless --check)")
    parser.add_argument("--chunk", type=int, default=3, help="lines per LLM call (default 3)")
    parser.add_argument("-c", "--canto", type=int, help="limit to a single canto number")
    parser.add_argument("--force", action="store_true", help="rebuild even if artifact exists")
    parser.add_argument("--check", action="store_true", help="validate artifacts, no model call")
    parser.add_argument("--clean", action="store_true",
                        help="remove chunks with count violations, then exit")
    parser.add_argument("-n", "--dry-run", action="store_true",
                        help="show pending chunks without calling the LLM")
    parser.add_argument("--log", nargs="?", const="morph.log", metavar="FILE",
                        help="append failed LLM responses to FILE (default: morph.log)")
    args = parser.parse_args()

    if args.check:
        return check(args.canticles, args.canto)
    if args.clean:
        return clean(args.canticles, args.chunk, args.canto)
    if args.dry_run:
        return build(args.canticles, args.model or "", args.chunk, args.force, True, args.canto)
    if not args.model:
        parser.error("--model is required for building (or pass --check / --dry-run)")
    log_path = Path(args.log) if args.log else None
    return build(args.canticles, args.model, args.chunk, args.force, False, args.canto,
                 log_path)


if __name__ == "__main__":
    sys.exit(main())
