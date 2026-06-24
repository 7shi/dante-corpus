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

`--check` validates committed artifacts against the deterministic tokens (every token gets
exactly one row; words are verbatim; closed-tag membership) — the structural verification bar.
"""

import argparse
import sys

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
    from llm7shi.compat import generate_with_schema

    response = generate_with_schema(
        [prompt],
        None,
        model=model,
        system_prompt=SYSTEM_PROMPT,
        show_params=False,
        file=stream,
    )
    return response.text


def _load_committed(canticle: str, number: int) -> list[tuple[int, list[morph.MorphRow]]]:
    """Already-frozen rows for a canto, ordered by line number — the checkpoint to resume from."""
    if not morph.has_morph(canticle, number):
        return []
    data = morph.load_morph(canticle, number)
    return [(no, list(rows)) for no, rows in sorted(data.items())]


def _build_canto(canticle: str, number: int, n_cantos: int, model: str, size: int,
                 force: bool, ui: StatusLine) -> bool:
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

    with ui.progress(len(lines), start=max(done, default=0), label=label) as prog:
        for chunk in pending:
            nos = [line.no for line in chunk]
            texts = [line.text for line in chunk]
            prompt = "Create a word table for these lines:\n\n" + "\n".join(
                f"{line.no} {line.text}" for line in chunk
            )
            for attempt in range(RETRIES + 1):
                table_text = _generate_table(prompt, model, ui.stream)
                ui.stream.end()
                try:
                    aligned = morph.align_chunk(nos, texts, table_text)
                    break
                except ValueError as exc:
                    ui.log(f"  {canticle} {number} lines {nos[0]}-{nos[-1]}: {exc} "
                           f"(attempt {attempt + 1}/{RETRIES + 1})")
            else:
                ui.log(f"  {canticle} {number}: giving up at line {nos[0]}; "
                       f"earlier lines saved for resume")
                return False
            out.extend((line.no, aligned[line.no]) for line in chunk)
            out.sort(key=lambda item: item[0])
            morph.write_morph(canticle, number, out)
            prog.update(nos[-1])
    ui.log(f"Wrote: morph/{canticle}/{number:02d}.tsv")
    return True


def build(canticles: list[str], model: str, size: int, force: bool, only: int | None) -> int:
    ui = StatusLine()
    for canticle in canticles:
        all_numbers = list(api.cantos(canticle))
        n_cantos = len(all_numbers)
        numbers = [only] if only else all_numbers
        for number in numbers:
            _build_canto(canticle, number, n_cantos, model, size, force, ui)
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
            for line in api.canto(canticle, number).lines():
                rows = list(data.get(line.no, ()))
                for v in morph.validate_line(line.no, line.text, rows):
                    bucket = "soft" if v.kind == "tag" else "hard"
                    if bucket == "hard":
                        hard += 1
                    else:
                        soft += 1
                    print(f"{canticle} {number}:{v.line} [{v.kind}] {v.detail}", file=sys.stderr)
    print(f"check complete: {hard} hard, {soft} soft violation(s)")
    return 1 if hard else 0


def main() -> int:
    parser = argparse.ArgumentParser(prog="morph.py")
    parser.add_argument("canticles", nargs="+", help="canticle names, e.g. inferno")
    parser.add_argument("-m", "--model", help="LLM, e.g. ollama:gpt-oss (required unless --check)")
    parser.add_argument("--chunk", type=int, default=3, help="lines per LLM call (default 3)")
    parser.add_argument("-c", "--canto", type=int, help="limit to a single canto number")
    parser.add_argument("--force", action="store_true", help="rebuild even if artifact exists")
    parser.add_argument("--check", action="store_true", help="validate artifacts, no model call")
    args = parser.parse_args()

    if args.check:
        return check(args.canticles, args.canto)
    if not args.model:
        parser.error("--model is required for building (or pass --check)")
    return build(args.canticles, args.model, args.chunk, args.force, args.canto)


if __name__ == "__main__":
    sys.exit(main())
