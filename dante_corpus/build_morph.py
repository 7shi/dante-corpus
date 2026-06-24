"""Build driver for Layer 2 (morphology). Mirrors `build_quotes.py`.

Generation is a build-time, user-run step: a local LLM proposes a Markdown word table per
chunk of lines, which is parsed and aligned to the deterministic tokens (`morph.align_chunk`)
and frozen as `morph/<canticle>/NN.json`. The runtime API never calls a model.

    uv run python -m dante_corpus.build_morph inferno -m ollama:gpt-oss        # all of Inferno
    uv run python -m dante_corpus.build_morph inferno -c 1 -m ollama:gpt-oss   # just canto 1
    uv run python -m dante_corpus.build_morph inferno --check                  # code-only, no model

`--check` validates committed artifacts against the deterministic tokens (every token gets
exactly one row; words are verbatim; closed-tag membership) — the structural verification bar.
"""

import argparse
import sys

from . import api, morph

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


def _generate_table(prompt: str, model: str) -> str:
    from llm7shi.compat import generate_with_schema

    response = generate_with_schema(
        [prompt],
        None,
        model=model,
        system_prompt=SYSTEM_PROMPT,
        show_params=False,
    )
    return response.text


def _build_canto(canticle: str, number: int, model: str, size: int) -> bool:
    canto = api.canto(canticle, number)
    out: list[tuple[int, list[morph.MorphRow]]] = []
    for chunk in _chunks(canto.lines(), size):
        nos = [line.no for line in chunk]
        texts = [line.text for line in chunk]
        prompt = "Create a word table for these lines:\n\n" + "\n".join(
            f"{line.no} {line.text}" for line in chunk
        )
        for attempt in range(RETRIES + 1):
            table_text = _generate_table(prompt, model)
            try:
                aligned = morph.align_chunk(nos, texts, table_text)
                break
            except ValueError as exc:
                print(
                    f"  {canticle} {number} lines {nos[0]}-{nos[-1]}: {exc} "
                    f"(attempt {attempt + 1}/{RETRIES + 1})",
                    file=sys.stderr,
                )
        else:
            print(f"  {canticle} {number}: giving up, canto not written", file=sys.stderr)
            return False
        out.extend((line.no, aligned[line.no]) for line in chunk)
    path = morph.write_morph(canticle, number, out)
    print(f"Wrote: morph/{canticle}/{number:02d}.json ({path})")
    return True


def build(canticles: list[str], model: str, size: int, force: bool, only: int | None) -> int:
    for canticle in canticles:
        numbers = [only] if only else list(api.cantos(canticle))
        for number in numbers:
            if not force and morph.has_morph(canticle, number):
                print(f"Skip (exists): morph/{canticle}/{number:02d}.json")
                continue
            _build_canto(canticle, number, model, size)
    return 0


def check(canticles: list[str], only: int | None) -> int:
    hard = 0
    soft = 0
    for canticle in canticles:
        numbers = [only] if only else list(api.cantos(canticle))
        for number in numbers:
            if not morph.has_morph(canticle, number):
                print(f"Missing: morph/{canticle}/{number:02d}.json", file=sys.stderr)
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
    parser = argparse.ArgumentParser(prog="dante_corpus.build_morph")
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
