# dante-corpus

Queryable corpus package for Dante's Divine Comedy.

This project uses the following Italian text source:

- [La Divina Commedia di Dante: Complete by Dante Alighieri | Project Gutenberg](https://www.gutenberg.org/ebooks/1000)

## Layout

- `dante_corpus/` — Python package
- `src/` — normalized Italian source text, one `.txt` per canto. The normalization separates
  **quotation marks** (guillemets `«»` marking speech) from **elisions** (contractions like
  `l'altra`), and standardizes elision apostrophes to **U+0027** (ASCII `'`) throughout, so
  tokenization can split on apostrophes without confusing them with speech delimiters.
- `quotes/` — per-canticle XML that captures the **nested structure of speech** (who quotes
  whom, embedded reported speech). Generated from the guillemet spans in `src/` by
  `build_quotes.py`; consumed by dante-analyze for speaker/edge attribution.

## Plan

[PLAN.md](PLAN.md) lays out the roadmap to extend the corpus from tokens and quotes into a
shared, canon-neutral **grammatical-analysis stack** (morphology, noun phrases, dependency, and a
predicate-argument skeleton) that downstream projects consume instead of each re-deriving the same
parse.

## Usage

See [`dante_corpus/README.md`](dante_corpus/README.md) for the full CLI and API reference.

```bash
uv run dante-corpus list canticles
uv run dante-corpus list cantos inferno
uv run dante-corpus text lines inferno 1:1-3
uv run dante-corpus text tokens inferno 1
uv run dante-corpus quote show inferno 1 --format xml
uv run dante-corpus canto show inferno 1 --format json
```

## Use from another project

The intended consumer flow is to add `dante-corpus` from a local directory:

```bash
cd /path/to/dante-corpus
make

cd /path/to/other-project
uv add --editable /path/to/dante-corpus
```

That keeps `dante-corpus` as a normal package dependency while the repository still
lives locally outside the consuming project. Run `make` first so the source tree already
contains the materialized source text and quote XML that the editable install will read.

## Build assets

Source text and quote XML are materialized relative to this repository:

```bash
make
```

## Downstream Projects

- [dante-analyze](https://github.com/7shi/dante-analyze) - The formalization / knowledge-graph layer. Runs local-LLM passes (scenes → markup → reading → bullets → tags) over the corpus to produce referent-resolved data and the per-scene context lock the translation consumes (see dante-dravidian `PLAN.md`). Companion project; not required just to run the translation pipeline.
- [dante-dravidian](https://github.com/7shi/dante-dravidian) - A translation of Dante's Divine Comedy into Dravidian languages (Telugu, Tamil, Kannada, and Malayalam) using a structured 4-stage translation process powered by Large Language Models (LLMs).

## Related Previous Projects

- [dante-llm](https://github.com/7shi/dante-llm) - A comparative study of Divine Comedy translation using multiple LLMs (Gemini 1.0 Pro, Gemma 3 27B, GPT-OSS 120B), verifying that locally-runnable models can match Gemini 1.0 Pro quality, with side-by-side comparisons of translations, word tables, and etymology analysis.
- [dante-gemini-25](https://github.com/7shi/dante-gemini-25) - A complete translation of Dante's Divine Comedy using Gemini 2.5 Pro, focusing specifically on English and Japanese translations across the three canticles. This project also includes illustrations generated using Nano Banana (Gemini 2.5 Flash Image Preview) in a classical Renaissance art style inspired by Gustave Doré.
- [dante-gemini](https://github.com/7shi/dante-gemini) - A multilingual exploration of Dante's Divine Comedy using Gemini 1.0 Pro, featuring detailed linguistic analysis of the opening lines in Italian, English, Hindi, Chinese, Ancient Greek, Arabic, Bengali and other languages with word-by-word breakdowns, grammatical details, and etymologies. 
- [dante-la-el](https://github.com/7shi/dante-la-el) - Originally started as a project to transcribe historical Latin and Ancient Greek translations of Dante's Divine Comedy, but evolved into an early LLM experimentation project when AI became the primary focus, exploring computational linguistic analysis methods.
