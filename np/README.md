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
  dependency on Layer 2 that touches the artifact itself (previously Layer 2 was only read for
  `--check`'s soft checks); a second, earlier dependency feeds Layer 2's POS straight into the
  generation prompt — see *Layer-2-POS-aware generation hints*, below. The model often still tries
  to name the bare pronoun as its own table row (e.g. `mi` for `udirmi`) — that
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
    left with no spans got the zero-NP sentinel) — see morph/CORRECTIONS.md's *`che`/`ch'` mistag
    correction*.
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
  `che` spans from Layer 3 — see [`../morph/CORRECTIONS.md`](../morph/CORRECTIONS.md)) — a
  reviewable list of genuine model omissions (often in repeated idioms: `a poco a poco`, `di
  gente in gente`) and residual function-word heads, kept visible rather than silenced.

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

  A hand review of all 41 lines flagged `head 'un'/'una' is 'article'` found the same split the
  `che` review did: 38 were a Layer-2 mistag (corrected to `pronoun`), 2 were genuinely `numeral`,
  and 1 was a Layer-3 alignment mismatch (a repeated-word case our per-exact-needle occurrence
  tracking doesn't cover — it matches only within one exact phrase, not across two different
  phrases sharing a word), fixed by reassigning the span. Corpus-wide soft count was then **139**
  (57 function-word heads + 82 noun coverage gaps).

  The remaining 57 function-word-head cases were reviewed the same way — the largest cluster's
  hand review (42 lines headed by a bare/elided article form) was delegated to an LLM subagent,
  spot-checked before applying: 25 Layer-2 mistags corrected to `pronoun`, 20 redundant Layer-3
  spans removed, plus a handful needing direct judgment or left as an accepted soft violation
  (paradiso 7:1 `Osanna`). Corpus-wide soft count was then **83** (1 function-word head + 82
  noun coverage gaps).

  The 82 noun-coverage-gap cases were then classified by cause before fixing anything, since most
  of them aren't Layer-2 problems at all — accepted non-NP idioms, Layer-3 span-merge gaps for
  two-token proper names, and unspanned single nouns account for most of the total. Only 11 were
  genuine Layer-2 mistags. Corpus-wide soft count is now **72**.

  Rather than leave the 25 accepted non-NP idiom cases (`fin che`, apocopated prepositions,
  `allotta`) as unexplained violations, each token now carries a machine-readable `NO_NP` flag in
  its Layer-2 `note` (comma-separated alongside any existing note); `_needs_np` treats a noun as
  exempt from coverage when `NO_NP` is among its note's stripped, comma-split values. This dropped
  the count to **47** — see [`../morph/CORRECTIONS.md`](../morph/CORRECTIONS.md)'s *`NO_NP` idiom
  flag* section.

  See [`../morph/CORRECTIONS.md`](../morph/CORRECTIONS.md) for the full per-case record of every
  Layer-2 correction made across all of these reviews (the `che`, `un`/`una`, function-word-head
  cluster, and noun-coverage-gap passes) — this file only tracks the Layer-3 soft-violation
  counts and the mechanics behind them.

- **Layer-2-POS-aware generation hints.** The one remaining function-word-head case, paradiso 7:1
  `Osanna` (tagged `interjection`), exposed a genuine generation-time gap: the prompt built by
  `_try_align` (`np/np.py`) never told the model which tokens are function-word POS, so it had no
  way to know `Osanna` couldn't be a valid phrase head — it could only be caught after the fact by
  `--check`. `dante_corpus.np.non_content_tokens()` now derives, from each line's Layer-2 rows,
  the tokens whose POS can never head an NP (`_can_head_np`), and `_try_align` appends them to the
  prompt as a "Function words (never choose as Head):" hint, with a matching `SYSTEM_PROMPT` rule
  and worked example. Since `_try_align` backs both `build()` and `fix()`, this took effect for
  both without a separate code path.

  Applied via `np/np.py inferno purgatorio paradiso --fix` (no full regeneration) against the 47
  then-flagged lines: 4 improved — `Osanna` itself (the model now nests a separate single-token
  `sabaòth` span instead of choosing `Osanna` as head), plus three unrelated coverage gaps that
  incidentally gained a nested single-token span for their previously-unspanned noun (inferno
  16:95 `Viso`, inferno 28:55 `fra`, paradiso 6:134 `Ramondo`). The other 43 lines regenerated
  under the new hint but were rejected by `--fix`'s no-worse-off guarantee (same violation count,
  sometimes on a different token) and kept their original artifact. Corpus-wide soft count is now
  **43**.

  The remaining 43 (all noun-coverage gaps) were checked one by one against precedent elsewhere in
  the corpus; only one, `Rife` (purgatorio 26:43, "montagne Rife"), was a genuine Layer-2 mistag —
  tagged `proper noun` but agreeing in gender/number with `montagne` like a demonym adjective
  ("Riphean"), matching the corpus's `troiano`/`latino`/`romano` pattern. Corrected to `adjective`,
  exempting it from coverage. Corpus-wide soft count is now **42**.

  The last case, paradiso 26:10's `dia`, is one word (archaic "divine") split across an enjambed
  line break with `regïon` on the next line — Layer 2 already records this via lemma `regione` and
  note `split word`. Since Layer 3 spans are single-line by design, `dia` can never head a
  same-line NP; a second flag, `CONT_NEXT` ("continues on next line"), was added alongside `NO_NP`
  for this structurally-distinct-but-same-shaped case. `_needs_np` exempts a noun from coverage if
  either flag is present. Corpus-wide soft count is now **41**.

  A further `--fix` rerun over the remaining 41 lines picked up 4 more this same way — the model
  nested a previously-missing single-token span for the noun that a larger span's head had
  eclipsed (inferno 4:57 `legista`, inferno 20:116 `Michele`/`Scotto`, paradiso 16:119
  `Ubertin`/`Donato`, purgatorio 13:128 `Pier`/`Pettinaio`/`orazioni`). Corpus-wide soft count is
  now **37** (36 lines, one — paradiso 13:139 — with two violations).

  The remaining 36 lines were reclassified, and every one is this same eclipsed-head shape: either
  a title/epithet word before a proper name (`ser`, `messer`, `mastro`, `San`, `fra`, `donna`)
  whose 2-token span's head is the name, or a name/noun that's the non-head half of such a span
  (`Argenti`, `Guiglielmo`, `Magno`, `ben`/`bene`/`vero`, etc.) — no Layer-2 mistags among them.
  Rerunning `--fix` again over these did **not** converge further (`np/np.log` shows all 36 lines
  unchanged, "not improved"): the model doesn't reliably add a redundant single-token span for a
  word it already covered inside a larger span, so this last batch needs the nested spans added
  directly rather than through repeated LLM regeneration.

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
