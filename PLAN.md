# Plan: a shared grammatical-analysis stack in the corpus

## Status

- **Layer 1 — Tokens**: implemented (`dante_corpus/tokenizer.py`, served via `Line.tokens`).
- **Layer 2 — Morphology + lemma**: implemented; see [`morph/README.md`](morph/README.md).
  Artifacts are built for all 100 cantos.
- **Layer 3 — Noun phrases**: implemented; see [`np/README.md`](np/README.md). Build driver
  `np/np.py`, served via `Canto.np()` and `dante-corpus text np`. Artifacts generated for all 100
  cantos and committed on branch `grammar-stack-plan` (not yet merged to `main`). Generation is
  complete and the soft-check policy is frozen: `--check` reports **0 hard / 42 soft**
  violations (after `--fix-repeats`, a `--fix` pass, the `un`/`una` mistag correction, the
  function-word-head cluster review, a noun-coverage-gap mistag pass, the `NO_NP` idiom flag,
  a Layer-2-POS-aware generation-prompt hint, and the `Rife` mistag correction, all diagnosed in
  `np/README.md`) — see *Layer 3 check status* below.
- **Layers 4–5 — dependency / skeleton**: design only (this document).

**Next work**

1. **Land Layer 3** — generation is finished (0 hard) and the soft-check policy is frozen
   (recorded in `np/README.md`); commit the freeze changes (policy predicates, `--fix-clitics`
   backfill of the TSVs, docs) and merge `grammar-stack-plan` into `main` (the build is excluded
   from `make all`; artifacts are committed like `morph/`).
2. **Layers 4–5 (dependency, skeleton)** — the syntactic spine; freeze last (see *Sequencing*).
   The design must also cover artifact **versioning** (content hashes for consumer invalidation)
   and **stable skeleton tuple ids** (both specified below, under Layer 5 / Build & serve model).

### Layer 3 check status (as of 2026-07-03 — generation complete, soft policy frozen)

`uv run np/np.py inferno purgatorio paradiso --check` reports **0 hard / 418 soft** violations.
The build resumed to completion for all 100 cantos (the 6 previously-incomplete cantos closed out
once the two hard-failure mechanisms below were fixed), and the soft checks were then
measured-and-frozen (see *Soft-check freeze* below).

**Hard-failure root cause (fixed)**: every chunk that exhausted all 3 retries with "unalignable
NP row(s)" (`np/np.log`) traced to exactly two mechanisms, both now fixed in
`dante_corpus/np.py`:

- **Elision spelling drift** (e.g. inferno 18:55: the model writes `I` where the deterministic
  token is `I'`) — `_find_run`/`_head_index` now fall back to `morph.strip_word_punct` (the same
  predicate Layer 2 already uses for its own word alignment) when an exact token match fails.
- **Fused enclitic pronouns** (e.g. inferno 23:36 `volerne`, purgatorio 16:145 `udirmi`, paradiso
  28:33 `contenerlo` — Italian enclitics attach directly to infinitive/gerund/imperative verb
  forms with no apostrophe, so Layer 1 never tokenizes them separately, and no amount of
  retrying lets the model align a phrase to a token that doesn't exist). Layer 2 already tags
  these tokens with a compound POS/lemma (`udirmi` → lemma `udire+me`, pos `verb+pronoun`; 579
  such tokens across the corpus, in 7 POS shapes). Layer 3 now reads Layer 2 at build time — a
  formal extension of the layer-stack principle that later layers depend on earlier ones' results
  (Layer 1 was already a mandatory dependency; Layer 2 was previously only consulted for the soft
  checks in `np/np.py`'s `check()`). A new `clitic_mentions()` in `dante_corpus/np.py`
  **deterministically** derives one single-token `NPSpan` per bound pronoun straight from the
  frozen Layer 2 artifact (`text` = `"+"` + the lemma component, e.g. `+me`), independent of what
  the LLM proposes. `validate_line` accepts these via a dedicated `"+"`-prefixed branch (checked
  against the host token's Layer-2 lemma components instead of a verbatim source substring). This
  is additive to — not a replacement for — the existing
  soft-coverage check: since `_is_nominal` already treats any POS containing `pronoun` as
  nominal, these mentions also resolve that token's own "nominal token heads no NP" soft
  violation as a side effect. Only genuinely compound POS (arity >= 2, e.g. `verb+pronoun`)
  qualify — a bare `pronoun` token (arity 1) is already its own Layer-1 token, so the model
  aligns an ordinary NP to it and no synthetic mention is generated (avoids a redundant "+xxx"
  duplicate). `validate_line` also gained a soft "clitic coverage" check (mirrors the existing
  nominal-head coverage check): for every token whose Layer-2 POS implies a mention,
  `clitic_mentions` is re-derived and diffed against `spans` — a "missing clitic mention" tag
  violation flags any artifact (chiefly ones built before this mechanism existed) whose `"+xxx"`
  mention wasn't actually generated. Currently 620 such violations corpus-wide, matching
  expectation: only lines regenerated after this change carry mentions; existing artifacts will
  clear this on rebuild.

  A follow-up gap surfaced by re-checking `np/np.log`: `clitic_mentions()` alone doesn't stop the
  original retry-exhaustion failures, because the model's *own* table row naming the bare
  pronoun (e.g. `| 145 | mi | mi |` for `udirmi`) still can't align to any token — that row was
  still counted in `align_chunk`'s `unaligned` total, so the chunk still hard-failed and burned
  all 3 retries exactly as before, even though the correct mention now gets added independently
  once/if the chunk succeeds. Fixed by giving `align_chunk` an optional `morph_rows` parameter:
  a single-word row labelled with a line that has a fused-enclitic token (arity >= 2 compound
  POS) is no longer counted as unalignable — it's redundant with what `clitic_mentions()` already
  supplies, not an error. `np/np.py` now threads the canto's Layer-2 rows through `_try_align` (
  both the chunk attempt and the per-line retry fallback) into `align_chunk`. Verified against
  the exact failing tables recorded in `np/np.log` for purgatorio 16:145 and paradiso 28:31-33 —
  both now align with 0 unaligned rows.

**Soft-check freeze (2026-07-03)** — measured over all 100 completed cantos (9,298 raw soft
violations), then frozen in `dante_corpus/np.py` (`_needs_np` / `_can_head_np`) and recorded in
`np/README.md`:

- **6,180 × "nominal token heads no NP"** — 96% were pronouns (bare `pronoun` 5,256, compound
  `x+pronoun` ~545, `relative pronoun` 138; top lemmas `che` 2,025, `si` 1,347, `mi` 633). As
  anticipated, this is correct model behaviour, not omission: bare clitics are not noun phrases,
  and Layer 5 below admits arguments that are "layer-3 NPs **or layer-1 pronoun tokens**".
  **Frozen**: coverage applies to noun/proper-noun POS only (`_needs_np`). The surviving **241**
  noun gaps are genuine model omissions (often in repeated idioms: `a poco a poco`, `di gente in
  gente`, `tra feltro e feltro`) and stay flagged as a reviewable list.
- **2,498 × "head is not nominal"** — adjective 1,322, verb 493, adverb 284, numeral 222 are
  legitimate Dante substantivizations (`'l più basso`, `lo sperar`, `un poco`, `l'un de' canti`).
  **Frozen**: any content POS may head an NP (`_can_head_np`: nominal or
  adjective/verb/adverb/numeral). The **177** function-word heads (article 111, conjunction 47, …)
  were sampled and most `che`/`ch'` conjunction heads turned out to be a Layer-2 mistag, not a
  Layer-3 artifact — see *`che` mistag correction* below. The surviving **153** stay flagged
  (mostly article heads: `un`/`una`/`'l`/`il`/…, plus the 12 genuinely-conjunction `che` cases
  confirmed below).
- **620 × "missing clitic mention"** — artifacts built before `clitic_mentions()` existed. These
  are a pure function of the frozen Layer-2 artifact, so a new deterministic repair mode
  (`np/np.py --fix-clitics`, no model call) backfilled all 620 in place; count is now 0 and any
  future flag is a regression.

**`che` mistag correction (2026-07-03)** — all 36 `head 'che'/"ch'" is 'conjunction'` soft
violations were reviewed by hand against their terzina context: 24 were a Layer-2 mistag
(Dante's relative pronoun `che`/`ch'` frozen as `conjunction`), corrected to `relative pronoun`;
12 were genuinely `conjunction`, with the bug on the Layer-3 side instead (the model had proposed
the bare conjunction as its own NP span) — those 12 spans were removed. See
[`morph/CORRECTIONS.md`](morph/CORRECTIONS.md) for the full per-case breakdown of the Layer-2
side.

Layer 3's `--check` count is now **382** soft (down from 418: 141 function-word heads + 241 noun
coverage gaps).

**Repeat-word alignment bug + `--fix` diagnosis (2026-07-03)** — a first `--fix` pass (regenerate
each flagged line, keep the new spans only if strictly fewer tag violations) found just 16/276
improved. Root cause of most of the shortfall: `align_chunk` collapsed every proposal for a
repeated word/phrase in one line (e.g. both `poco`s in `a poco a poco`) onto its *first*
occurrence, so the second was structurally uncoverable no matter how many times `--fix` re-asked
the model — confirmed by manual line inspection and quantified corpus-wide with a Fable 5
subagent's independent investigation (~30% of remaining coverage gaps were this artifact, not
model misses). Fixed in `dante_corpus/np.py`: `_find_run`/`_align_row`/`align_chunk` now track
claimed occurrences (a per-chunk-line, per-needle `used` set of run-starts) so future builds align
each repeat to a distinct token run. `np/np.py --fix-repeats` (deterministic, no model call)
repaired the existing artifacts the same way, reassigning 204 duplicate spans corpus-wide and
clearing 80 of the then-276 soft violations for free — see `np/README.md`'s *Check* section for
the mechanism and *Things to watch* for the invariant going forward.

A subsequent full-corpus `--fix` run (after the repeat fix) improved only 6 more lines out of
~180 attempted. A second Fable 5 consult (given the full `np.log` and the `_fix_canto`/prompt
code) found 162/174 "not improved" lines came back with the byte-identical violation set: the
retry re-asks the same single-line, no-feedback prompt, so it mostly reproduces its own prior
answer rather than correcting anything. Diagnosis: this is close to the ceiling for that retry
design, not a prompt-engineering gap — most remaining violations are not Layer-3 mistakes:
- **Function-word heads (104 remaining, 89 of them `article`)**: 47 are `un`/`una` alone, mostly
  Dante's *pronominal* `un`/`una`/`el` ("ad un ch'al passo", "d'una di lor") where the flagged
  head is the actual, correct NP head — Layer 2 froze it as `article` when it should be
  `pronoun`/`numeral`. No re-generation can lower this count without deleting a legitimate NP;
  clearing it needs the same per-case hand review the `che` cases got (Layer 2 retag vs. Layer 3
  span deletion). **Next candidate for that review**, isolated by grepping `--check` output for
  `head 'un'|'una' is 'article'`.
- **Noun coverage gaps (82 remaining)**: roughly half are Layer-2 mistags the model is correctly
  declining to nominalize (`fin che` = *finché* a conjunction, the `inver'`/`'nver'`/`'ntorno`
  family, `sol`/`ben`/`U'` as adverbs, verb+clitic forms like `parlonne`) — same disposition as
  the `che` review. The other half are title/surname head-competition (`ser Brunetto`, `fra
  Dolcin`, `Argenti`, `Buoso`, `Magno`) where the model won't spontaneously split off a second,
  minimal NP for the bare title/surname; an informed retry prompt (state the specific violation,
  don't just re-ask blind) could plausibly recover these, unlike the two categories above.

Corpus-wide soft count after `--fix-repeats` and this `--fix` pass: **186** (104 function-word
heads + 82 noun coverage gaps).

**`un`/`una` mistag correction (2026-07-03)** — all 41 lines flagged `head 'un'/'una' is
'article'` were reviewed the same way: 38 corrected to `pronoun` (Dante's substantivized
indefinite pronoun `un`/`una`), 2 to `numeral` (genuine counting/predicative uses), and 1
(paradiso 31:8) was a Layer-3 alignment mismatch rather than a mistag — `align_chunk` had matched
a proposed span to the wrong occurrence of a repeated word across two different phrases, fixed by
reassigning the span. See [`morph/CORRECTIONS.md`](morph/CORRECTIONS.md) for the full breakdown.
`morph --check` and `np --check` both remained clean after every edit (0 hard throughout).

Layer 3's `--check` count is now **139** soft (down from 186: 57 function-word heads + 82 noun
coverage gaps — `un`/`una` no longer among them).

**Function-word-head cluster review (2026-07-04)** — the remaining 57 function-word-head
violations were reviewed the same way, this time with the largest, most uniform cluster (42
lines headed by a bare/elided article form: `il/la/lo/li/le/el/'l/l'/El/I`) delegated to an LLM
subagent briefed with the corpus's own precedent rows. Its classifications were spot-checked
against the raw span/morph dumps before applying: 25 corrected to `pronoun` (an Old Italian
clitic pronoun homographic with the article), 20 were Layer-3 over-inclusion (a redundant span
duplicating an already-correct larger one) and had the span removed instead, plus 2 needed direct
judgment. The remaining 15 heterogeneous cases (interjections, conjunctions, prepositions, a
determiner) were each resolved by matching an existing corpus tagging convention. See
[`morph/CORRECTIONS.md`](morph/CORRECTIONS.md) for the full per-case breakdown, including which
of these 57 were Layer-2 fixes vs. Layer-3-only fixes vs. left as an accepted soft violation
(paradiso 7:1 `Osanna`).

`morph --check` and `np --check` both remained clean (0 hard throughout, `morph --check` also 0
soft). Layer 3's `--check` count is now **83** soft (down from 139: 1 function-word head —
the accepted `Osanna` exception — + 82 noun coverage gaps).

**Noun-coverage-gap mistag pass (2026-07-04)** — the 82 remaining "noun heads no NP" cases were
classified by cause before touching anything, since only a subset are actually Layer-2 mistags:
25 are accepted non-NP function-word/idiom cases (`fin che`, apocopated prepositions, `allotta`
— no fix needed), 29 are two-token proper-name/title pairs where Layer 3 picked only one word as
head (a Layer-3 span-merge gap, left for a future pass), and 13 are single content words Layer 2
already tags correctly that Layer 3 simply never spanned (also left for a future pass). Only
**11** were genuine Layer-2 mistags, each matched against an existing precedent row before
fixing — see [`morph/CORRECTIONS.md`](morph/CORRECTIONS.md) for the full table and the two false
leads (`animal`, `forme`) caught and left alone during the check. Three more cases (`ben`/`bene`
before an infinitive) were deliberately excluded — the corpus tags that construction
inconsistently elsewhere, so there's no clean precedent to fix against without a real design
decision.

Retagging fired the frozen clitic-mention check for `parlonne` (its span had no `+ne` mention
yet); `np/np.py purgatorio --fix-clitics` backfilled it deterministically, no model call needed.

`morph --check` and `np --check` both remained clean (0 hard throughout). Layer 3's `--check`
count is now **72** soft (down from 83: the accepted `Osanna` exception + 25 accepted non-NP
function-word/idiom cases + 29 title/name span-merge gaps + 13 unspanned single nouns + 4 cases
left open — the 3 `ben`/`bene` instances pending a nominalized-infinitive tagging decision, plus
paradiso 26:10's `dia`).

**`NO_NP` idiom flag (2026-07-04)** — rather than leave the 25 accepted non-NP function-word/idiom
cases as unexplained violations, each token now carries a machine-readable `NO_NP` flag in its
Layer-2 `note` column (comma-separated alongside any existing note, matching the corpus's existing
multi-note convention). `_needs_np` (`dante_corpus/np.py`) now treats a noun as exempt from
coverage if `NO_NP` is among its note's comma-split, stripped values. This dropped Layer 3's
`--check` count to **47** soft (down from 72) with no artifact change beyond the 25 `note` edits —
see [`morph/CORRECTIONS.md`](morph/CORRECTIONS.md) for the full rationale.

**Layer-2-POS-aware generation prompt (2026-07-04)** — the remaining `Osanna` exception
(paradiso 7:1, tagged `interjection`) was traced to a genuine generation-time blind spot: Layer 3's
prompt never told the model which tokens are function-word POS, so it had no way to know `Osanna`
couldn't be a valid phrase head. Added `dante_corpus.np.non_content_tokens()` and a
"Function words (never choose as Head):" hint block to `_try_align`'s prompt (`np/np.py`), plus a
matching `SYSTEM_PROMPT` rule and worked example, so this is now a second, generation-time
dependency on Layer 2 (alongside the existing deterministic clitic-mention one). Applied via
`np/np.py inferno purgatorio paradiso --fix` — safe because of `--fix`'s no-worse-off guarantee
(keeps a regenerated line only if it strictly reduces violations with no new hard ones). Of the 47
flagged lines, **4 improved**: the `Osanna` head-POS violation itself (the model now nests a
separate single-token `sabaòth` span instead), plus three coverage gaps that incidentally gained a
nested single-token span for their previously-unspanned noun (inferno 16:95 `Viso`, inferno 28:55
`fra`, paradiso 6:134 `Ramondo`) — the other 43 flagged lines regenerated with the hint applied but
were rejected as not-improved (same violation count, sometimes shifting which token was flagged)
and so kept their original artifact, per the no-worse-off guarantee. Layer 3's `--check` count is
now **43** soft (down from 47).

**`Rife` mistag correction (2026-07-04)** — the remaining 43 violations (all noun-coverage gaps)
were checked one by one against precedent elsewhere in the corpus; only one was a genuine Layer-2
mistag: `Rife` (purgatorio 26:43, "montagne Rife"), tagged `proper noun` but agreeing in
gender/number with `montagne` like a demonym adjective ("Riphean"), matching the corpus's existing
`troiano`/`latino`/`romano` pattern. Corrected to `adjective`, exempting it from coverage. Layer
3's `--check` count is now **42** soft (down from 43) — see
[`morph/CORRECTIONS.md`](morph/CORRECTIONS.md).

## Why this lives in the corpus

`dante-corpus` is the queryable, **canon-neutral source of truth** for the *Commedia*: it serves
the normalized Italian text, the token stream, and the nested quote-span tree, all derived from
the poem itself with no external ontology. Today it stops at tokens and quotes.

Downstream projects each need to *read the source grammatically* before they can do their own
work — the formalization layer (`dante-analyze`) to extract entities and relations, the
translation layer (`dante-dravidian`) to align tokens to a reference. Both currently re-derive
the same morphosyntax from scratch, in their own prompts, every time. That re-derivation is not
project-specific: **the grammar of an Italian line is the same regardless of what you do with
it.** So it belongs here, computed once, and served like any other corpus asset.

The line that keeps this in the corpus — rather than letting it drift into an interpretation
engine — is a strict **asymmetry**:

> The corpus **enumerates and annotates** what the text's own grammar determines.
> Consumers **decide, normalize, and bind to external references** on top of that.

Everything in this plan is recoverable from the Italian source alone. Nothing here looks at a
reference translation, a knowledge-graph goal, or any external canon. The contested judgments —
*is this noun phrase an entity? which closed relation is this verb? is this a simile? what is the
English equivalent?* — are deliberately **not** computed here; they are the consumers' jobs (see
*Out of scope* below). This keeps the corpus reproducible and neutral while still removing the
duplicated reading.

## The layers

Five layers, each a function of the source text. Layers 1–3 are implemented; layers 4–5 are the
remaining work. Examples use *Inferno* I.1–6.

```
1  Nel mezzo del cammin di nostra vita
2  mi ritrovai per una selva oscura,
3  ché la diritta via era smarrita.
4  Ahi quanto a dir qual era è cosa dura
5  esta selva selvaggia e aspra e forte
6  che nel pensier rinova la paura!
```

### Layer 1 — Tokens *(implemented — no new work)*

The token stream already produced by `dante_corpus/tokenizer.py` and served via `Line.tokens`.
This is the deterministic foundation every higher layer cites and checks against; it needs no
further design. Its unit already matches what the morphology layer expects: it splits
apostrophe-linked elisions (`ch'` `i'`), keeps prepositional contractions whole (`Nel`, `del`),
and excludes punctuation (`has_alpha`).

- `mi` `ritrovai` `per` `una` `selva` `oscura` …
- **Generation**: deterministic (`tokenizer.py` over the normalized `src/`).
- **Check**: each token is a verbatim, in-order substring of its source line.

### Layer 2 — Morphology + lemma *(implemented — see [`morph/README.md`](morph/README.md))*

Per-token lemma, part of speech, and morphological features (gender, number, person, tense, mood),
plus a note for contraction / apocope / elision — generated from the Italian alone at build time,
aligned 1:1 to the Layer-1 tokens, and frozen as TSV. This is the first layer that removes
duplicated reading: the translation layer (`dante-dravidian` Step 1) currently regenerates the same
morphology inline; this is what it would consume instead. A prior local-LLM experiment produced
exactly this table from the source with no reference, evidence the layer is intrinsically
recoverable.

The mechanics — columns, generation rules, the token-alignment algorithm, validation tiers, and
usage — live in [`morph/README.md`](morph/README.md). It is served via `Canto.morph()` and
`dante-corpus text morph`.

### Layer 3 — Noun-phrase enumeration *(implemented — see [`np/README.md`](np/README.md))*

Every noun phrase in the line, with its head, source span, and modifiers — enumerated
**exhaustively and over-inclusively**. The corpus does **not** decide whether an NP is an entity;
it lists every candidate so consumers can decide. Each NP is frozen as a contiguous Layer-1 token
range (`start`/`end`) with a `head` token index and verbatim `text`; nesting is derived by span
containment at serve time. Served via `Canto.np()` and `dante-corpus text np`.

- `[nostra vita]` · `[una selva oscura]` · `[la diritta via]` · `[esta selva selvaggia e aspra e
  forte]` · `[la paura]`
- **Generation**: LLM shallow parse at build time, frozen. Nesting (e.g. `mezzo del cammin di
  nostra vita`) is represented explicitly; over-inclusion is correct behaviour, not noise.
- **Check**: each NP span reproduces a verbatim source substring; the head token lies within the
  span.
- **Scope**: NP spans are **single-line** by design (each is a verbatim substring of one source
  line), so an enjambed phrase appears as its per-line pieces and is rejoined by layer-4
  attachment. Bare clitic and relative pronouns are **not** NPs — they are layer-1/2 tokens that
  receive their clause function in layer 4.

### Layer 4 — Dependency / grammatical role

Each token and noun phrase tagged with its function in the clause and the head it attaches to.

- `[la diritta via]` = subject of `era smarrita`
- `mi` = reflexive object → `ritrovai`
- `[una selva oscura]` = locative complement → `ritrovai`
- `che` (l.6) = relative pronoun, subject of `rinova`, antecedent `[esta selva …]`
- **Pronoun mentions become enumerable here**: bare clitic / relative / personal pronoun tokens —
  deliberately not listed as layer-3 NPs — each carry a role and a head at this layer, so a
  consumer can enumerate every pronoun mention from layer-2 POS + layer-4 role. Attachment may
  cross line boundaries (a subject on one line, its predicate on the next), which is also what
  rejoins enjambed NP pieces.
- **Generation**: LLM at build time, frozen.
- **Check**: every token carries a role; every cited head id exists; relative-pronoun antecedents
  resolve to an in-scope NP.

### Layer 5 — Predicate-argument skeleton

Noun-phrase ↔ verb tuples binding layers 3 and 4 into bare propositions — citing ids, **not** raw
text. This is the *raw* skeleton only: **no semantic frame, no coreference, no vocabulary
normalization.**

- `(subject = ∅ pro-drop, predicate = ritrovare, locative = NP[una selva oscura])`
- `(subject = NP[la diritta via], predicate = smarrire)`
- `(subject = NP[esta selva …], predicate = rinovare, object = NP[la paura], locative = pensier)`
- **Ids**: each tuple is addressable by a stable id (`<line>.<ordinal>` in line order, mirroring
  layer-3 NP ids, derived at serve time), so a consumer artifact can **cite** a skeleton tuple
  rather than paraphrase it — consumers annotate tuples by id, they never re-derive them.
- **Generation**: LLM at build time, frozen.
- **Check**: cited NP ids exist in layer 3; the predicate token exists in layer 1; arguments are
  layer-3 NPs or layer-1 pronoun tokens.

## Out of scope — consumer responsibilities

These are intentionally absent from the corpus because they are not determined by the text's own
grammar; they are contested judgments, normalizations, or bindings to something external. Listing
them fixes the boundary:

- **Entity-hood and entity typing** — which layer-3 noun phrases are entities, and of what kind.
  (A formalization-layer judgment, frozen against that project's own evidence-derived vocabulary.)
- **Coreference / referent identity** — linking pronouns, pro-drop subjects, and epithets to a
  single referent. (Reading-bound interpretation; belongs to the consumer.)
- **Closed relation vocabulary** — mapping a layer-5 predicate onto a frozen relation set.
- **Frame** — literal / simile / prophecy / reported. (Interpretive.)
- **Reference equivalents and truth-conditions** — any alignment to an English (or other) reference
  translation. (Translation-layer concern; brings external canon and must not enter the corpus.)

## Build & serve model

Mirror the existing `quotes/` pipeline exactly: a build step generates each layer, the result is
**committed**, and the package then **serves it deterministically** through the `dante_corpus`
API. The LLM is a build-time tool whose output is frozen and round-trip-checked — consumers see a
stable, reproducible asset, never a live model call. This follows the *measure-then-freeze*
discipline already used for normalization and quotes.

- **Artifact**: one structured file per canto per layer, under its own directory. Rectangular
  layers freeze as TSV (Layer 2 → `morph/<canticle>/NN.tsv`, one line-numbered row per token);
  layers with nesting may use another structured form. Layers join by token order; whether later
  layers share a file or stay in sibling directories is decided per layer.
- **Versioning**: every canto×layer artifact is **content-addressed** — the serve API exposes a
  content hash alongside the data, so a consumer can record exactly which parse a derived artifact
  annotated and recompute only what a regeneration actually changed (granular invalidation, per
  `dante-analyze`'s REARCHITECTURE.md). Regenerating one canto changes only that canto's hash;
  nothing else downstream is invalidated.
- **Build driver**: each LLM-built layer's generator lives in its own step directory (Layer 2 →
  `morph/morph.py`, the reference implementation) and is **resumable from its own output** — every
  chunk's rows are written back to the artifact as soon as they validate, so an interrupted run
  skips already-committed lines and re-requests only the remainder. Progress is shown live through
  `llm7shi.statusline` (Rich) — a per-canto bar (`canticle canto/total |
  line/total …`) with the model's streamed output routed through the same console.
- **Output routing convention** (shared across all LLM build drivers): the `StatusLine` object
  (`ui`) is the single output channel throughout the build flow. `ui.log()` is used for status
  messages (skip, resume, wrote); `ui.stream` is passed as `file` to the `llm7shi.Client` so
  streamed LLM tokens flow through the same console; `ui.stream.error()` is used for error
  messages (attempt failures, giving up) so they appear in red and are visually distinct from
  normal progress output. All future layer drivers follow this same convention.
- **Multi-turn recovery** (shared pattern): the `llm7shi.Client` maintains a conversation session,
  enabling two-stage recovery when a local model fails to produce a complete response in one turn.
  First, split output is repaired before alignment (e.g. `_merge_tables()` in Layer 2 merges
  consecutive pipe-tables into one). Second, if the aligned result still has lines with fewer
  elements than expected, a follow-up turn on the same session asks the model to supply the missing
  content, and the result is concatenated before retrying. These two stages — structural repair
  then continuation — are the standard recovery pattern for all LLM-built layers.
- **API**: extend the corpus query surface (alongside `text tokens`, `quote show`) with each
  grammatical layer, addressable by canticle / canto / line range (Layer 2: `Canto.morph()` /
  `dante-corpus text morph`).
- **Strongest reader for the hard layers**: morphology (L2) is robust; NP/dependency/skeleton
  (L3–L5) are reading-bound and should use the strongest available model at build time, measured
  before freezing.

## Validation

- **Per-layer checks** (above) run over all 100 cantos; zero round-trip failures is the structural
  bar, exactly as for `quotes/`.
- **Closed tag/role sets**: features (L2) and roles (L4) validate against frozen vocabularies, so a
  drift in the build model is caught rather than silently absorbed.
- **Neutrality audit**: the build prompt for every layer takes only the Italian source as input —
  no reference translation, no entity list, no canon. This is the invariant that lets two very
  different consumers share one parse.

## Sequencing

1. **Layer 2 (morphology + lemma)** — *implemented* (`dante_corpus/morph.py` + `morph/morph.py`). Lowest risk,
   already shown feasible intrinsically, and immediately useful as a lemma-queryable index.
2. **Layer 3 (noun phrases)** — *implemented* (`dante_corpus/np.py` + `np/np.py`). The census/entity
   substrate consumers most want.
3. **Layers 4–5 (dependency, skeleton)** — the syntactic spine; freeze last, as they are the
   hardest and the most valuable to share.

Build alongside the existing assets, gate each layer on its checks, then expose through the API.
Layers 2–3 are implemented; layers 4–5 remain design only.
