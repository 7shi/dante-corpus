# Proper Noun Extraction

`proper_noun.py` collects the proper nouns of Dante's *Divine Comedy* from the
Italian original, one row per Italian line, and writes them as a
variable-length TSV per canto.

## Overview

The canto's Italian lines (read through the
[`dante_corpus`](../dante_corpus/README.md) API) are handed to
an LLM in `--block-size`-line groups (default 3, normally a tercet),
numbered by their canto-wide line number. The model answers in the output
format itself - one tab-separated row per line, that line's number
followed by the proper nouns occurring in it - so the reply's rows are the
output file's rows, with no intermediate representation to convert. This
is why the script asks for plain TSV rather than structured output.

Two decisions shape everything else:

- **Names, not entities.** Only literal proper nouns are collected: people,
  mythological and biblical figures, deities, peoples and factions, places
  (cities, regions, rivers, mountains, realms of the afterlife), stars and
  planets, titles of works. A periphrasis or epithet standing for a named
  person (`il maestro`, `quel savio gentil`, `colui che ...`) is *not*
  collected even though a reader knows who it means, and neither is a
  common noun that merely happens to be capitalized.
- **The line's own spelling.** A reported noun is located in its line and
  the matching substring is sliced out of the line, so every noun in the
  TSV is verbatim text of that line. Matching ignores case and apostrophe
  variants (`dell'` / `dell’`), but a noun that does not occur in its line
  at all - a hallucination, or a name normalized to its dictionary form -
  fails the reply.

## Usage

```bash
uv run proper_noun/proper_noun.py -m openai:gpt-5.6-terra -b 30 inferno -c 1-2
```

Positional argument: one or more canticle names (`inferno`, `purgatorio`,
`paradiso`). Options:

- `-c`/`--canto`: canto selection (`N`, `N-M`, `N-`, `-M`, or a
  comma-separated mix). Omit to run every canto of the canticle in turn, in
  one process.
- `-m`/`--model`: LLM model, passed through to `llm7shi`; use an `ollama:`,
  `google:`, or `openai:` prefix to select the backend. Cloud backends need
  the corresponding API key set in the environment.
- `--temperature` (default: 1.0)
- `--think`: enable LLM thinking (off by default)
- `-b`/`--block-size` (default: 3): Italian lines per LLM call. A rerun asks
  about at most this many lines, and only about missing ones.
- `--test`: process only the first pending group, for a quick smoke test

## Output

Written to `proper_noun/<canticle>/`, canto-number-prefixed (e.g. Inferno
Canto 1 -> `proper_noun/inferno/01.*`):

- **`<NN>.tsv`**: variable-length TSV, one row per *processed* Italian
  line, in line order:

  ```
  1	Foo	Bar
  2
  3	Baz
  ```

  A line with no proper noun keeps its row, holding just the line number -
  that row is what records the line as processed. A line that has not been
  processed yet simply has no row; nothing is ever written as a
  placeholder.
- **`<NN>.log`**: the full processing trace (per-group lines, the accepted
  nouns, rejections and retries), a final listing of the lines that carry
  nouns, and summary counts. Unconditionally overwritten on every run
  (gitignored via the repo root `.gitignore`'s `*.log`).

Progress and errors are also printed to the console as the script runs, via
a live `llm7shi.statusline.StatusLine` progress bar whose numerator walks
the canto's Italian lines.

## Validation and retries

Every reply is checked mechanically before it is accepted:

- one row per line asked about, each starting with that line's own number,
  in order (a Markdown code fence around the rows is tolerated)
- every noun non-empty and occurring verbatim in its line

These checks live in `BlockClient.should_retry`, which extends
`llm7shi.Client`'s own retry loop, so a malformed row, a wrong line number
or a hallucinated noun is regenerated exactly as an empty reply is. There
is deliberately no second retry loop in this script: one client, built once
with `keep_history=False`, serves the whole run (every call is an
independent single-shot Q&A). A group where no attempt validates is left
unwritten and the run moves on - a later run retries just those lines.

## Resuming

A missing row is the pending marker. Rows are appended group by group as
they are extracted, so a failed or interrupted run simply stops writing and
leaves a file that is correct as far as it goes.

On the next run:

- a canto whose file holds a row for every line is skipped with a single
  console line, without any LLM call;
- otherwise only the lines that have no row are asked about - each block's
  missing lines, split into contiguous runs, so a single missing line in
  the middle of a block costs a one-line call rather than a whole block;
- rows stay sorted by line number: a group that extends the file is
  appended, while one filling a gap (or a file that was not in order to
  begin with) triggers a full rewrite in line order.

Delete a row by hand to force just that line to be redone; delete the file
to redo the canto. A file that does not check out - a row whose first field
is not a line number of this canto, or the same line twice - stops that
canto with a message instead of being appended to.

## Requirements

- `dante_corpus` for the Italian source text
- `llm7shi` (with the `statusline` extra) for the LLM backends and the
  progress display
- an LLM backend: a local `ollama:` model, or an API key for a `google:` /
  `openai:` one

The script depends on nothing else in this repository: it reads its text
through `dante_corpus`, talks to the LLM through `llm7shi`, and writes its
output beside itself.

## Relation to ARCHITECTURE.md

[`../ARCHITECTURE.md`](../ARCHITECTURE.md) is binding for the layer build
drivers (`skel/`, `dep/`) and the Grammar Agent Harness (`harness/`) — this
script is neither, and is not held to it. Where the two happen to overlap:

- **Followed** — progress display: one `llm7shi.statusline.StatusLine` bar
  per canto labeled `{canticle} {canto}/{n_cantos}` whose numerator walks the
  canto's Italian lines (ARCHITECTURE.md §4's Canticle-Canto-Line pattern).
- **Followed in spirit, different shape** — interruption resilience: each
  extracted group is written to the TSV as soon as it settles (§5's core
  requirement), but the artifact is a variable-length TSV whose completion
  marker is "every line has a row," not an appended JSONL log with a
  trailing `summary` record.
- **Not applicable** — model access goes straight through a plain
  `llm7shi.Client` subclass imported at module load (not lazily, and not the
  stateful `runner.agent.llm7shi_generate` adapter of §2); there is no
  tool-call wire protocol (§3, this is single-shot text Q&A, not an agent
  loop); there are no `Report.metrics()`/`summary()` classes (§6); the CLI
  skeleton (§9) omits `--max-turns`/`--verbose` and headers per-canto rather
  than per-run.

None of this is a gap to close — §0's checklist targets the harness lineage
this script deliberately sits outside of (see the root
[`README.md`](../README.md#layout)).
