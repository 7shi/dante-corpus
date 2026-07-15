# Plan: a shared grammatical-analysis stack in the corpus

## Status

**Next up: Layer 5 (predicate-argument skeleton) — build driver written, all 100 cantos built
(0 hard), corpus-wide soft-divergence triage and `skel/README.md` remain.** Layers 1–4 are
implemented and merged to `main`; see *The layers* below for Layer 5's design and the
*Handoff* section at the end of this document for exactly what a fresh session needs to pick
up next.

- **Layer 1 — Tokens**: implemented (`dante_corpus/tokenizer.py`, served via `Line.tokens`).
- **Layer 2 — Morphology + lemma**: implemented; see [`morph/README.md`](morph/README.md).
  Artifacts are built for all 100 cantos.
- **Layer 3 — Noun phrases**: implemented and complete; see [`np/README.md`](np/README.md). Build
  driver `np/np.py`, served via `Canto.np()` and `dante-corpus text np`. Artifacts generated for
  all 100 cantos. `--check` reports **0 hard / 0 soft** violations — see
  [`np/README.md`](np/README.md)'s *Check* section and [`np/CORRECTIONS.md`](np/CORRECTIONS.md)
  for the full history.
- **Layer 4 — Dependency / grammatical role**: implemented and complete; see
  [`dep/README.md`](dep/README.md). Build driver `dep/dep.py`, served via `Canto.dep()` and
  `dante-corpus text dep` (with `text np` gaining a derived `role=` per noun phrase). Artifacts
  built for all 100 cantos; `--check` reports **0 hard / 0 soft** violations — see
  [`dep/README.md`](dep/README.md)'s *Check* section and
  [`dep/CORRECTIONS.md`](dep/CORRECTIONS.md) for the full correction history.
- **Layer 5 — skeleton**: **core module implemented** (`f7819b0`) and **build driver written,
  all 100 cantos built** (`e4dece2` pilot + a follow-up build covering the remaining 99
  cantos): `dante_corpus/skel.py` (dataclasses, role vocabulary, deterministic derivation,
  table parsing, validation, TSV I/O, serve-time joins), `dante_corpus/hashes.py`
  (content-hash versioning, all layers), `Canto.skel()`/`Canto.hashes()` in `api.py`,
  `dante-corpus text skel`/`dante-corpus hash` in `cli.py`, `skel/skel.py` (LLM build driver,
  mirrors `dep/dep.py`), `skel/Makefile`, `skel/CORRECTIONS.md`, `tests/test_skel.py` +
  `tests/test_hashes.py` (68 tests total, all passing, no regressions). `skel/<canticle>/NN.tsv`
  now exists for all 100 cantos; `--check` across all three canticles reports **0 hard, 17438
  soft** (inferno 5644, purgatorio 6295, paradiso 5499). **Not yet done**: corpus-wide
  soft-divergence triage beyond Inferno canto 1 (only canto 1 has been hand-inspected and
  documented in `skel/CORRECTIONS.md`, at 125 soft after its own fixes — the other 99 cantos'
  ~17.3k remaining soft violations are unclassified), `skel/README.md`, and the final
  `dante_corpus/README.md` update. See *Handoff* below.

`grammar-stack-plan` was merged into `main` (fast-forward) and pushed; Layers 1–4 and their
artifacts now live on `main`.

**Next work**

1. **Corpus-wide soft-divergence triage** — classify the ~17.3k soft violations across
   purgatorio/paradiso and the rest of inferno against the four root-cause categories
   `skel/CORRECTIONS.md` established from canto 1 (xcomp control, elliptical predicate
   nominals, NP-membership false positives, single-instance boundary cases), fixing what's
   deterministic and exempting/documenting the rest, per the *Handoff* section's plan.

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

Five layers, each a function of the source text. Layers 1–4 are implemented; layer 5 is the
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

### Layer 4 — Dependency / grammatical role *(implemented — see [`dep/README.md`](dep/README.md))*

Each token tagged with its function in the clause (a Universal Dependencies relation) and the head
it attaches to — `[la diritta via]` = subject of `era smarrita`; `che` (l.6) = relative pronoun,
subject of `rinova`, antecedent `[esta selva …]`. Attachment may cross line boundaries, which is
what rejoins layer-3's single-line enjambed NP pieces; bare pronoun tokens (deliberately not
layer-3 NPs) each carry a role and a head here, making every pronoun mention enumerable. The
mechanics — parse units, index-citing generation, validation tiers, and usage — live in
[`dep/README.md`](dep/README.md). It is served via `Canto.dep()` and `dante-corpus text dep`.

### Layer 5 — Predicate-argument skeleton *(built for all 100 cantos — see `dante_corpus/skel.py` and `skel/CORRECTIONS.md`)*

Predicate ↔ argument tuples binding layers 2–4 into bare propositions, citing **token
positions**, not raw text or lemmas. This is the *raw* skeleton only: **no semantic frame, no
coreference, no vocabulary normalization.** Role labels are **UD-derived**
(`subj`/`obj`/`iobj`/`attr`/`xcomp`/`ccomp`/`obl:<preposition lemma>`), not semantic — an
earlier draft of this section used a semantic label (`locative`) for the oblique example below;
that was replaced with `obl:in`/`obl:per` etc. once the design was implemented, to keep the
vocabulary canon-neutral and directly comparable with the deterministic derivation below.

Unlike Layers 2–4, **the LLM authors the artifact but a deterministic derivation is the
checker**: `derive_unit` in `dante_corpus/skel.py` computes the same predicate-argument
structure mechanically from the frozen Layers 2–4, and the LLM proposes its own, independent
reading of the same parse unit (it is **not shown** the Layer-4 parse). Soft checks report every
divergence between the two. A purely deterministic Layer 5 would just be `f(dep)` and could
never disagree with Layer 4; giving the LLM an independent read means a divergence can surface
a genuine Layer-4 mis-parse, not just an LLM slip — Layer 5 doubles as an audit of Layer 4,
triaged with the same measure-then-freeze discipline as `dep/CORRECTIONS.md`.

Worked example, Inferno I.1–9 (verified by hand against the frozen `dep`/`np`/`morph` artifacts;
reproduced exactly by `derive_unit`, see `tests/test_skel.py::test_derive_unit_inferno_1_1_9`):

- `ritrovai` (2.2): `subj = ∅` (pro-drop), `obl:in = [mezzo del cammin di nostra vita]` (1.1),
  `obl:per = [una selva oscura]` (2.1)
- `smarrita` (3.6): `subj = [la diritta via]` (3.1)
- `rinova` (6.4): `subj = che` (the relative pronoun token itself — its antecedent, `[esta selva
  selvaggia e aspra e forte]`, is *derived*, not stored, via `skel.antecedent`), `obj = [la
  paura]` (6.2), `obl:in = pensier` (6.1)
- **Ids**: each tuple is addressable by a stable id (`<line>.<ordinal>` in line order, mirroring
  layer-3 NP ids, derived at serve time via `skel.tuples_canto`), so a consumer artifact can
  **cite** a skeleton tuple rather than paraphrase it — consumers annotate tuples by id, they
  never re-derive them.
- **Generation**: LLM at build time, frozen (`skel/skel.py`, mirroring `dep/dep.py`). Built for
  all 100 cantos; `--check` reports **0 hard, 17438 soft** across the corpus — see *Handoff*
  for the triage status (only Inferno canto 1 has been fully triaged so far, in
  `skel/CORRECTIONS.md`).
- **Check**: hard — the predicate token exists in layer 1 and every argument position is a
  valid in-unit token position (or the `(0,0)` pro-drop/zero-argument sentinel). Soft — an
  argument citing a nominal role must be a layer-3 NP head, a layer-1 pronoun token, or an
  in-unit predicate (clausal argument); and, the central check, every divergence from
  `derive_unit` (`missing_tuple`/`extra_tuple`/`missing_arg`/`extra_arg`/`role_mismatch`).

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
3. **Layer 4 (dependency)** — *implemented* (`dante_corpus/dep.py` + `dep/dep.py`). The syntactic
   spine that rejoins enjambed NPs and makes pronoun mentions enumerable.
4. **Layer 5 (skeleton)** — *core module implemented* (`dante_corpus/skel.py` +
   `dante_corpus/hashes.py`) and *build driver written, all 100 cantos built* (`skel/skel.py`,
   `skel/<canticle>/NN.tsv`, 0 hard / 17438 soft); corpus-wide soft-divergence triage and
   `skel/README.md` are the remaining work. See *Handoff*.

Build alongside the existing assets, gate each layer on its checks, then expose through the API.
Layers 2–4 are implemented and merged to `main`; layer 5's core module and build driver are
implemented, and its artifacts are built for all 100 cantos — soft-divergence triage beyond
canto 1, `skel/README.md`, and the final `dante_corpus/README.md` update are the remaining work.

## Handoff (2026-07-15, for a fresh session)

Layer 5's **core module** and **LLM build driver** are both done, committed, and all 100
cantos are built. What's left is **corpus-wide soft-divergence triage** (only Inferno canto 1
has been hand-triaged so far), `skel/README.md`, and the final `dante_corpus/README.md`
update. A new session picking this up needs no further design discussion — the design is
finished and verified; this section is a concrete punch list.

**What exists now**:

- `dante_corpus/skel.py` (`f7819b0`) — read its module docstring first; it explains the
  LLM-authors / derivation-checks design. Key entry points: `resolve_chunk` (parse the LLM's
  Markdown table into `SkelRow`s), `validate_unit` (hard + soft checks), `derive_unit` (the
  deterministic checker, also useful standalone for measuring an un-triaged canto's
  divergence), `write_skel`/`has_skel`/`load_skel` (TSV I/O), `tuples_canto` (serve-time
  grouping + id assignment).
- `dante_corpus/hashes.py` — `artifact_hash`/`canto_hashes`, wired to all four TSV layers plus
  `text`.
- `Canto.skel()` / `Canto.hashes()` in `api.py`; `dante-corpus text skel` / `dante-corpus hash`
  in `cli.py`.
- `skel/skel.py` (`e4dece2`) — the LLM-facing build driver, structurally mirrors `dep/dep.py`:
  `SYSTEM_PROMPT` with a worked example, parse units reused verbatim from
  `dep.sentence_groups`, prompt shows POS-annotated tokens and Layer-3 NP anchors but
  **deliberately omits the Layer-4 parse** (so `derive_unit`'s divergence check stays
  meaningful), includes a rule against citing a fused-enclitic-pronoun verb (e.g.
  `venendomi`) as its own argument (added after the canto-1 pilot hit a hard self-citation
  violation). Same recovery/resume/mode conventions as `dep/dep.py` (`--check`/`--clean`/
  `--fix`/`--dry-run`/`--log`, `--fix` under the no-worse-off guarantee).
- `skel/Makefile` — mirrors `dep/Makefile`.
- `skel/CORRECTIONS.md` — documents the **Inferno canto 1** triage only: four root-cause
  categories found (xcomp-complement subject/object control — the largest class and an open
  design question, deferred not fixed; elliptical predicate nominals with no verb token —
  exemption, not fixable by `derive_unit`; two NP-membership soft-check false positives, fixed
  deterministically in `validate_unit`; two single-instance boundary cases left as-is). Canto 1
  itself: **0 hard, 125 soft** after the deterministic fixes.
- `skel/<canticle>/NN.tsv` — **all 100 cantos built** (43037 rows total). `--check` across all
  three canticles: **0 hard, 17438 soft** (inferno 5644, purgatorio 6295, paradiso 5499). The
  **other 99 cantos' soft violations are not yet classified** — canto 1's 125 (after its own
  fixes) is the only triaged data point; the remaining ~17.3k across the corpus have not been
  inspected against canto 1's four categories or for new ones.
- `tests/test_skel.py` + `tests/test_hashes.py` — 68 tests total in the suite, all passing, no
  regressions.

**What's left**, concretely, in order:

1. **Corpus-wide soft-divergence triage** — for purgatorio, paradiso, and inferno cantos 2–34,
   classify soft violations against `skel/CORRECTIONS.md`'s four established categories
   (xcomp control, elliptical predicate nominals, NP-membership false positives,
   single-instance boundary cases), watching for new categories the single-canto sample
   didn't surface. Same triage ladder as `dep/CORRECTIONS.md` and canto 1's own triage:
   deterministic fix first (if a divergence class is actually a `derive_unit` bug, fix
   `skel.py`, not the artifact) → LLM `--fix` regeneration (no-worse-off guaranteed) →
   hand-verified exemption (only if a genuine reading `derive_unit` structurally can't
   express) → hand-edit as an absolute last resort, checking each instance against its terzina
   rather than blanket-applying a rule. At 17.3k soft violations, expect this to be
   categorized and mostly resolved/exempted in bulk by pattern, not violation-by-violation.
2. **`skel/README.md`** — write once triage has converged enough to report stable numbers;
   follow the structure of `dep/README.md` (artifact format, generation approach, validation
   tiers, CLI usage, *Check* section with final hard/soft counts).
3. **Final `dante_corpus/README.md` update** — add `text skel` / `hash` CLI sections and
   `Canto.skel()`/`Canto.hashes()`/`SkelTuple` to the Public API listing (Layers 2–4's sections
   there are the template).
4. **This document** — once triage converges (or the remainder is exemption-flagged) and
   `skel/README.md` exists, update the *Status* section's Layer 5 entry to "implemented and
   complete" with the final hard/soft counts, matching how Layers 3–4 are currently described.

No further design decisions are expected to be needed for any of the above — every open
question (role vocabulary, artifact schema, predicate definition, checker semantics, id
scheme, hashing) was resolved and implemented in commit `f7819b0`, and the build driver's
conventions were validated against the canto-1 pilot. This is now a measurement/triage task at
scale, not a design task. If a build-time surprise contradicts something this document states,
prefer what the code and tests actually do (they're authoritative) and update this document to
match, rather than re-deriving the design from scratch.
