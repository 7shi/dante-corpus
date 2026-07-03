# morph — Layer 2: morphology + lemma

Per-token **morphology and lemma** for every line of the *Commedia* — the first new layer of the
grammatical stack ([PLAN.md](../PLAN.md)). It annotates only what the Italian's own grammar
determines (lemma, part of speech, gender/number/person/tense/mood); it makes **no** interpretive
judgment (entity-hood, coreference, reference equivalents) — those stay with the consumer projects.

## What it does

One LLM pass per chunk of source lines (default 3) emits a Markdown **word table**, one row per
word, with columns `Word | Lemma | Part of Speech | Gender | Number | Person | Tense | Mood | Note`.
Local models cannot reliably produce structured (JSON-schema) output, so the table is the
interface; code parses and aligns it. The generation driver lives in this directory
(`morph/morph.py`); the parsing, alignment, and I/O it depends on stay in the shared
package (`dante_corpus/morph.py`), which is what the runtime API consumes.

Two things are deliberately **code's job**, never the model's:

- **Lemma decomposition** is recorded but the surface word is kept intact — `Nel → in+il`,
  `del → di+il`; apostrophe-linked words (`ch'`, `i'`) are separate rows; quotation marks excluded.
- **Token alignment.** Layer 1 (`tokenizer.py`) is the deterministic anchor: each table row's
  `Word` is bound to a Layer-1 token by anchor-substring matching with FIFO salvage (`split_table`),
  so **every token receives exactly one morphology row** even when the model transforms or
  hallucinates a word.

## Output

`morph/<canticle>/NN.tsv` — one tab-separated row per token, prefixed with its line number; the file
is the committed, frozen artifact (no model call at runtime). The data is fully rectangular, so TSV
round-trips without quoting and keeps git diffs token-granular. From `inferno/01.tsv`:

```
line	word	lemma	pos	gender	number	person	tense	mood	note
1	Nel	in+il	preposition+article	m.	sg.				contraction
1	mezzo	mezzo	noun	m.	sg.				
2	mi	mi	pronoun		sg.	1			reflexive
2	ritrovai	ritrovare	verb		sg.	1	remote past	indicative	
```

## Check

`--check` validates every committed artifact against the deterministic tokens, with **no model
call** (`validate_line`):

- **Hard** (the structural bar): one row per token, in order, each row's word a verbatim token —
  `0 hard` is required before an artifact is trusted.
- **Soft**: closed-tag membership for gender (`m./f./n.`), number (`sg./pl.`), person (`1/2/3`).
  POS / tense / mood are collected for later *measure-then-freeze*, reported but not yet enforced.

The build itself retries a chunk (max 2) when alignment raises. Each chunk's rows are written
back to the TSV as soon as they validate, so an interrupted run resumes from its own output:
already-committed lines are skipped and only the remaining chunks are requested.

`--check`'s own POS check is only a closed-tag membership test, so it can't catch a token that's
structurally fine but tagged the wrong part of speech. Those surfaced instead through Layer 3's
soft-check review and were hand-corrected directly in the frozen artifacts — see
[`CORRECTIONS.md`](CORRECTIONS.md) for the full record of every such correction.

## Output recovery

Local models occasionally produce incomplete or split output. Two recovery steps run before
every alignment attempt:

**1. Table merging (`_merge_tables`)**

A model that hits its token limit mid-table will sometimes restart with a fresh header and
separator rather than continuing the existing table. The merge step detects any repeated
occurrence of the first header row (whether preceded by a blank line or appearing inline without
one) and removes the duplicate header and separator, concatenating the body rows into a single
continuous table. This handles the most common failure mode: the model emits six words, emits a
new `| Word | Lemma | … |` / `|---|…|` pair, then continues from the seventh word.

**2. Multi-turn continuation (`_continue_if_truncated`)**

After merging, if any line still has fewer table rows than Layer-1 tokens (output was genuinely
cut off), the driver sends a follow-up turn on the same `llm7shi.Client` session asking the
model to continue with the remaining lines. The continuation response is itself passed through
`_merge_tables` before being appended, then alignment is retried on the combined text. If the
result still fails after all retries, the chunk falls through to the per-line fallback.

## Model

Build-time only, set in [`../model.mk`](../model.mk) (the `vendor:name` form routed by `llm7shi`,
defaulting to `ollama:gemma4:31b-it-qat`) and overridable with `make morph MODEL=...`. The model is
a build tool whose output is frozen and round-trip-checked; consumers see a stable asset, exactly
like `quotes/`.

## Usage

```bash
make -C morph                          # build all three canticles (model from model.mk)
make -C morph MODEL=ollama:gpt-oss     # override the model
make -C morph check                    # validate artifacts, no model call

uv run morph/morph.py inferno [-c 1] [-m MODEL] [--force] [--check]
```

Consumers read it deterministically via `Canto.morph()` (line-number → `MorphRow` tuples) or the
CLI `dante-corpus text morph inferno 1:1-3` (`--format json` for the raw rows).
