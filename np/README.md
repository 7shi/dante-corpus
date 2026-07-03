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
- **Soft** (reported, not enforced). The policy was frozen 2026-07-03 after measuring all 100
  cantos (measure-then-freeze; raw pre-freeze counts in PLAN.md's *Layer 3 check status*):
  - **Head POS** — a head may be any *content* POS: nominal (`noun`/`pronoun` in the label) or
    adjective/verb/adverb/numeral, since Dante substantivizes all of these (`'l più basso`,
    `lo sperar`, `un poco`, `l'un de' canti`). Function-word heads (article, conjunction,
    preposition, …) are flagged; a hand review of every `che`/`ch'` conjunction head (36 cases)
    found 24 were a genuine Layer-2 mistag (Dante's relative pronoun `che`, not the subordinating
    conjunction) and corrected the frozen `morph/` TSVs directly to `relative pronoun`; the other
    12 are real conjunctions (consecutive `tanto/sì … che`, the idiom `secondo che`, complementizer
    `che`, causal `poi che`) where Layer 3 had wrongly proposed the bare conjunction as its own
    single-token NP — those 12 spans were removed directly from the frozen `np/` TSVs (4 lines
    left with no spans got the zero-NP sentinel) — see PLAN.md's *`che` mistag correction*.
    Remaining function-word heads are mostly articles (`un`/`una`/`'l`/…).
  - **Coverage** — every *noun/proper-noun* token should head at least one NP (catches omissions,
    since over-inclusion means there is no one-row-per-token count anchor as in Layer 2).
    Pronouns are excluded by policy: bare clitic and relative pronouns (`che`, `si`, `mi`, …)
    were ~96% of the raw misses and are not noun phrases — Layer 5 admits arguments that are
    "Layer-3 NPs or Layer-1 pronoun tokens", so they are layer-2/4 objects, not Layer-3 gaps.
  - **Clitic coverage** — every fused-enclitic mention that Layer 2's compound POS implies must
    actually be present among the artifact's spans. Artifacts built before `clitic_mentions()`
    existed lacked them; `--fix-clitics` backfills them deterministically (done for all 100
    cantos), so any new flag here is a regression.

  Under the frozen policy the corpus-wide soft count was **382** (141 function-word heads + 241
  noun coverage gaps, after correcting 24 `che` mistags in Layer 2 and removing 12 over-included
  `che` spans from Layer 3 — see PLAN.md) — a reviewable list of genuine model omissions (often
  in repeated idioms: `a poco a poco`, `di gente in gente`) and residual function-word heads,
  kept visible rather than silenced.

  A first `--fix` pass found only 16/276 lines improved — suspiciously low. Investigating showed
  ~30% of the remaining coverage gaps were not model misses at all: `align_chunk` collapsed every
  proposal for a repeated word/phrase in one line (e.g. both `poco`s in `a poco a poco`) onto its
  *first* occurrence, so the second was structurally uncoverable no matter how many times `--fix`
  re-asked the model. `align_chunk` now tracks claimed occurrences per chunk-line so future builds
  align each repeat to a distinct token run (see *Things to watch*); `--fix-repeats`
  (deterministic, no model call) repairs existing artifacts the same way — reassigning 204
  duplicate spans corpus-wide and clearing 80 of the then-276 soft violations for free.

  `--fix` (`make -C np fix`) regenerates just the flagged lines and keeps the new spans only when
  they carry strictly fewer tag violations than before, with no new hard ones — the `che` review
  showed a flagged line can be either a genuine miss or a legitimate substantivized reading, and
  a fresh model pass can't reliably tell those apart in bulk, so this is a best-effort pass with a
  no-worse-off guarantee rather than a promise every case clears. Anything still flagged after
  `--fix` is a candidate for the same kind of hand review the `che` cases got.

  A full-corpus `--fix` run after the repeat-word fix improved only 6 more lines (of ~180
  attempted), logging the rest as "not improved" (`np.log`, gitignored). Diagnosis: 162/174 of
  those lines came back with the byte-identical violation set — the retry re-asks the same
  single-line prompt with no feedback about what was flagged, so it is mostly re-rolling dice, not
  correcting a mistake. Two structural reasons this ceiling is expected rather than a prompt bug:
  a flagged span's head is often *correct* (Dante using `un`/`el` pronominally — 47 of the 89
  remaining article-head violations are `un`/`una` alone), so no re-generation can lower the count
  without deleting a legitimate NP; and several coverage gaps (`fin che`, `inver'`, verb+clitic
  forms) are function words the model correctly declines to treat as nouns — the flag traces to a
  Layer-2 POS question, not a Layer-3 omission, exactly the pattern the `che` review already found.
  The corpus-wide soft count after `--fix-repeats` and this `--fix` pass was **186** (104
  function-word heads + 82 noun coverage gaps).

  A hand review of all 41 lines flagged `head 'un'/'una' is 'article'` (see PLAN.md's `un`/`una`
  mistag correction) found the same split the `che` review did: **38** are Dante's substantivized
  indefinite pronoun (`un de' tuoi`, `l'una e l'altra milizia`) mistagged `article` by Layer 2,
  corrected to `pronoun`; **2** are genuinely `numeral` (predicative "become as one", and a
  counting context parallel to an already-`numeral` `tre`); **1** was a Layer-3 alignment
  mismatch (a repeated-word case our per-exact-needle occurrence tracking doesn't cover — it
  matches only within one exact phrase, not across two different phrases sharing a word), fixed
  by reassigning the span to the correct token. Corpus-wide soft count was then **139** (57
  function-word heads + 82 noun coverage gaps).

  The remaining 57 function-word-head cases were reviewed the same way (see PLAN.md's
  *Function-word-head cluster review*), this time delegating the largest cluster's hand review
  (42 lines headed by a bare/elided article form `il/la/lo/li/le/el/'l/l'/El/I`) to an LLM
  subagent briefed with the corpus's own precedent rows, since Old Italian frequently uses these
  same word forms as unstressed clitic pronouns homographic with the article. Its output — 25
  Layer-2 mistags corrected to `pronoun`, 20 redundant Layer-3 spans removed — was spot-checked
  against the raw data before applying, plus 2 cases it flagged as needing direct judgment. The
  remaining 15 heterogeneous cases (interjections, conjunctions, prepositions, a determiner)
  were each resolved by matching an existing corpus tagging convention (`guai`/`tutto`/`perché`/
  `onde`/`capo`/`quantunque` all already have precedent rows for the target POS elsewhere in the
  corpus) rather than inventing new categories; one case (paradiso 7:1 `Osanna`, a
  self-contained quoted interjection with no content word to shift the span head to) was left as
  an accepted soft violation. Corpus-wide soft count was then **83** (1 function-word head — the
  accepted `Osanna` exception — + 82 noun coverage gaps).

  The 82 noun-coverage-gap cases were then classified by cause (see PLAN.md's *Noun-coverage-gap
  mistag pass*) before fixing anything, since most of them aren't Layer-2 problems at all: 25 are
  accepted non-NP function-word/idiom cases (`fin che`, apocopated prepositions, `allotta`), 29
  are two-token proper-name/title pairs where Layer 3 picked only one word as head (a span-merge
  gap, left for a future pass), and 13 are single content words Layer 2 already tags correctly
  but Layer 3 never spanned (also left for a future pass). Only **11** were genuine Layer-2
  mistags — each checked against its own corpus-wide precedent before fixing, catching two false
  leads (`animal`, `forme`) that turned out to already match established convention and were left
  alone. 3 more (`ben`/`bene` before an infinitive) were deliberately left unfixed: the corpus
  tags the same "ben/bene + infinitive" construction inconsistently in different places, so
  there's no clean precedent to match without a real design decision. Corpus-wide soft count is
  now **72**.

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
- If the same exact token subsequence appears twice in one line, `align_chunk` aligns each
  proposal to a distinct occurrence in table-row order (a per-chunk-line, per-needle `used` set of
  claimed run-starts) rather than collapsing them all onto the first. `--fix-repeats` repairs
  artifacts built before this tracking existed (`dedupe_repeats`, no model call).
- The soft-check predicates (`_can_head_np`, `_needs_np` in `dante_corpus/np.py`) match POS by
  substring, so contracted POS like `preposition+noun` still require coverage and
  `verb+pronoun` counts as a content head. This is intentional under the frozen policy; the
  edge cases are few (10 `preposition+noun` tokens corpus-wide).
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
make -C np fix                      # regenerate lines with soft violations (model from model.mk)

uv run np/np.py inferno [-c 1] [-m MODEL] [--force] [--check] [--fix-clitics] [--fix-repeats] [--fix]
```

Consumers read it deterministically via `Canto.np()` (a nested `NPSpan` forest, ordered by line)
or the CLI `dante-corpus text np inferno 1:1-3` (`--format json` for the nested rows).
