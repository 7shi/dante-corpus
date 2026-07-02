# np — Layer 3: noun-phrase enumeration

Every **noun phrase** in every line of the *Commedia* — the next layer of the grammatical stack
([PLAN.md](../PLAN.md)) after morphology. It enumerates NP candidates **exhaustively and
over-inclusively**, including nested phrases; it makes **no** interpretive judgment (which NP is an
entity, coreference, reference equivalents) — those stay with the consumer projects. The corpus
lists every candidate so consumers can decide.

## What it does

One LLM pass per chunk of source lines (default 3) emits a Markdown table, one row per noun phrase,
with columns `Line | Noun Phrase | Head`. Local models cannot reliably produce structured
(JSON-schema) output, so the table is the interface; code parses and aligns it. The generation
driver lives in this directory (`np/np.py`); the parsing, alignment, nesting, and I/O it depends on
stay in the shared package (`dante_corpus/np.py`), which is what the runtime API consumes.

Two things are deliberately **code's job**, never the model's:

- **Alignment to tokens.** Layer 1 (`tokenizer.py`) is the deterministic anchor: each phrase is
  located as a *contiguous run* of Layer-1 tokens, recorded as 1-based `start`/`end` indices, a
  `head` token index, and the verbatim source `text` it spans. The model's free-text phrase is thus
  bound to exact token positions even when it transforms spacing or punctuation. Alignment tolerates
  elision-spelling drift (e.g. the model writes `I` where the token is `I'`) by falling back to
  `morph.strip_word_punct` — the same predicate Layer 2 uses for its own word alignment — when an
  exact match fails.
- **Nesting.** Parent/child structure is *derived* by span containment at serve time (the smallest
  enclosing phrase is the parent), exactly as the quote tree is built — it is not asked of the model
  or stored. The model only needs to list the phrases, including the nested ones.
- **Fused enclitic pronouns.** Italian enclitics attach directly to infinitive/gerund/imperative verb
  forms with no apostrophe (e.g. `udirmi`), so Layer 1 never tokenizes them separately — the model
  cannot align a phrase to a token that doesn't exist. Layer 3 build reads Layer 2's morphology for
  each line: any token whose POS is a genuinely compound `x+pronoun[+...]` shape (arity >= 2, e.g.
  `udirmi` → lemma `udire+me`, pos `verb+pronoun`) gets a synthetic single-token mention generated
  **deterministically** from the frozen Layer 2 artifact, independent of what the model proposed —
  see *Output* and `clitic_mentions()` in `dante_corpus/np.py`. This is Layer 3's first build-time
  dependency on Layer 2 (previously Layer 2 was only read for `--check`'s soft checks). The model
  often still tries to name the bare pronoun as its own table row (e.g. `mi` for `udirmi`) — that
  row can never align to a token, so `align_chunk` is given the line's Layer-2 rows and excuses a
  single-word row labelled on a fused-enclitic line from the `unaligned` count instead of failing
  the whole chunk; the mention it would have added is already covered deterministically.

## Output

`np/<canticle>/NN.tsv` — one tab-separated row per noun phrase, prefixed with its line number; the
file is the committed, frozen artifact (no model call at runtime). A processed line with no noun
phrases is stored as a single sentinel row with `start == 0`, so resumption can tell "no NPs here"
from "not yet processed". Example for *Inferno* I.1–3:

```
line	start	end	head	text
1	2	7	2	mezzo del cammin di nostra vita
1	4	7	4	cammin di nostra vita
1	6	7	7	nostra vita
2	4	6	5	una selva oscura
3	2	4	4	la diritta via
```

(`start`/`end`/`head` index into `Line.tokens`; e.g. line 1 token 2 is `mezzo`, token 7 is `vita`.)

A fused-enclitic mention is a single-token row (`start == end == head`) whose `text` is `"+"`
followed by the pronoun's lemma, e.g. for `udirmi` (token 7 of purgatorio 16.145):

```
line	start	end	head	text
145	7	7	7	+me
```

This is not a substring of the source line by construction — it stands for the bound pronoun that
Layer 1 couldn't split out on its own.

## Check

`--check` validates every committed artifact against the deterministic tokens, with **no model
call** (`validate_line`):

- **Hard** (the structural bar): each NP is a contiguous, in-order run of Layer-1 tokens; the head
  index lies inside the range; the stored `text` is the verbatim source substring of that range —
  except a `"+"`-prefixed clitic mention, which is checked against the host token's Layer-2 lemma
  components instead (it is never a source substring by construction). Every source line must be
  present (or carry the zero-NP sentinel). `0 hard` is required before an artifact is trusted.
- **Soft** (reported, not enforced — *measure-then-freeze*): when Layer-2 morphology is present, the
  head token is expected to be nominal (POS containing `noun`/`pronoun`); **coverage** — every
  nominal token should head at least one NP (catches omissions, since over-inclusion means there is
  no one-row-per-token count anchor as in Layer 2); and **clitic coverage** — every fused-enclitic
  mention that Layer 2's compound POS implies must actually be present among the artifact's spans.
  This mainly flags artifacts built before `clitic_mentions()` existed; it clears on rebuild.

The build retries a chunk (max 2) when alignment fails, then falls back to per-line requests. Each
chunk's spans are written back to the TSV as soon as they validate, so an interrupted run resumes
from its own output: already-committed lines are skipped and only the remaining chunks are requested.

## Output recovery

Local models occasionally produce incomplete or split output. Two recovery steps (the shared
pattern, see [PLAN.md](../PLAN.md)) run before every alignment attempt:

**1. Table merging (`_merge_tables`)** — a model that restarts the table mid-output with a fresh
header/separator is merged back into one continuous table.

**2. Multi-turn continuation (`_continue_if_truncated`)** — if the chunk's last line produced no NP
rows (the table was likely cut off), the driver sends a follow-up turn on the same `llm7shi.Client`
session asking it to continue with the remaining lines; the response is merged before alignment is
retried.

## Design decisions

- **Artifact**: TSV `np/<canticle>/NN.tsv`, columns `line  start  end  head  text` (token-index
  spans + verbatim text) — chosen over storing id/parent explicitly or text-only, since nesting and
  ids are cheap to derive by span containment at serve time (see *What it does*).
- **Zero-NP sentinel**: a processed line with no NPs is stored as one row with `start == 0` (empty
  text), so resume distinguishes "no NPs here" from "not yet processed".
- **Modifiers** are not stored or asked of the model — they are derivable (span tokens minus the
  head, joinable with Layer-2 POS).
- **NPs are single-line**, matching morph's per-line invariant and the "verbatim source substring"
  check (see PLAN.md's *Scope* note under Layer 3). Cross-line enjambed phrases are intentionally
  not represented; Layer 4 attachment is what rejoins them.

## Things to watch

- `_continue_if_truncated` treats "last line of chunk has no NPs" as the truncation signal. A chunk
  whose final line genuinely has no NPs triggers one wasted continuation turn per attempt —
  harmless (it writes the sentinel) but worth knowing.
- If the same exact token subsequence appears twice in one line, `align_chunk` picks the first
  occurrence. Extremely rare in a hendecasyllable; revisit only if `--check` surfaces it.
- `_is_nominal` matches POS substrings `noun`/`pronoun`, so contracted POS like `preposition+noun`
  count as nominal heads. Adjust in `dante_corpus/np.py` if the frozen soft-check policy (see
  PLAN.md's *Layer 3 check status*) demands stricter matching.
- `clitic_mentions()` only fires on genuinely compound POS (arity >= 2). A bare `pronoun` token
  (arity 1) is already its own Layer-1 token and gets an ordinary NP from the model, so it's
  intentionally excluded — including it would emit a redundant `"+xxx"` duplicate of that NP.

## Model

Build-time only, set in [`../model.mk`](../model.mk) (the `vendor:name` form routed by `llm7shi`),
overridable with `make np MODEL=...`. NP/dependency/skeleton layers are reading-bound, so the
strongest available model should be used and measured before freezing (PLAN.md). The model is a
build tool whose output is frozen and round-trip-checked; consumers see a stable asset.

## Usage

```bash
make -C np                          # build all three canticles (model from model.mk)
make -C np MODEL=ollama:gpt-oss     # override the model
make -C np check                    # validate artifacts, no model call

uv run np/np.py inferno [-c 1] [-m MODEL] [--force] [--check]
```

Consumers read it deterministically via `Canto.np()` (a nested `NPSpan` forest, ordered by line)
or the CLI `dante-corpus text np inferno 1:1-3` (`--format json` for the nested rows).
