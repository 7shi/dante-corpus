# Plan: a shared grammatical-analysis stack in the corpus

## Status

**Next up: Layer 5 (predicate-argument skeleton) — core module done, LLM build driver and
100-canto artifacts remain.** Layers 1–4 are implemented and merged to `main`; see *The
layers* below for Layer 5's design and the *Handoff* section at the end of this document for
exactly what a fresh session needs to pick up next.

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
- **Layer 5 — skeleton**: **core module implemented and committed** (`f7819b0`,
  "Add Layer 5 (skel) core module: predicate-argument skeleton + content hashes"):
  `dante_corpus/skel.py` (dataclasses, role vocabulary, deterministic derivation, table
  parsing, validation, TSV I/O, serve-time joins), `dante_corpus/hashes.py` (content-hash
  versioning, all layers), `Canto.skel()`/`Canto.hashes()` in `api.py`, `dante-corpus text
  skel`/`dante-corpus hash` in `cli.py`, `tests/test_skel.py` + `tests/test_hashes.py` (28
  tests, all passing; 64 total in the suite, no regressions). **Not yet done**: the LLM build
  driver (`skel/skel.py`), `skel/README.md`/`Makefile`/`CORRECTIONS.md`, and the 100-canto
  build run. See *Handoff* below.

`grammar-stack-plan` was merged into `main` (fast-forward) and pushed; Layers 1–4 and their
artifacts now live on `main`.

**Next work**

1. **Layer 5 build driver** (`skel/skel.py`) — write the LLM-facing half of Layer 5, structurally
   mirroring `dep/dep.py`, then pilot-build Inferno canto 1, measure the divergence-from-
   `derive_unit` soft-check count, and triage per the *Handoff* section's plan. See *Sequencing*.

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

### Layer 5 — Predicate-argument skeleton *(core module implemented — see `dante_corpus/skel.py`)*

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
- **Generation**: LLM at build time, frozen (build driver **not yet written** — see *Handoff*).
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
   `dante_corpus/hashes.py`); the LLM build driver (`skel/skel.py`) and the 100-canto artifact
   build are the remaining work. See *Handoff*.

Build alongside the existing assets, gate each layer on its checks, then expose through the API.
Layers 2–4 are implemented and merged to `main`; layer 5's core module is implemented and
committed (`f7819b0`) — its build driver and artifacts are the remaining work.

## Handoff (2026-07-13, for a fresh session)

Layer 5's **core module** (the deterministic/served half) is done, committed, and tested. What's
left is entirely the **LLM-facing build driver** and the resulting artifacts. A new session
picking this up needs no further design discussion — the design is finished and verified; this
section is a concrete punch list.

**What exists now** (commit `f7819b0`, "Add Layer 5 (skel) core module: predicate-argument
skeleton + content hashes"):

- `dante_corpus/skel.py` — read its module docstring first; it explains the LLM-authors /
  derivation-checks design. Key entry points a build driver will call: `resolve_chunk` (parse
  the LLM's Markdown table into `SkelRow`s), `validate_unit` (hard + soft checks, call with
  `morph_rows`/`np_rows`/`dep_rows` all supplied once artifacts exist to get every soft check),
  `derive_unit` (the deterministic checker — also useful standalone for measuring how far off
  an un-triaged canto is), `write_skel`/`has_skel`/`load_skel` (TSV I/O, same shape as
  `dep.py`'s), `tuples_canto` (serve-time grouping + id assignment).
- `dante_corpus/hashes.py` — `artifact_hash`/`canto_hashes`, already wired to all four TSV
  layers plus `text`; needs no further work for Layer 5.
- `Canto.skel()` / `Canto.hashes()` in `api.py`; `dante-corpus text skel` / `dante-corpus hash`
  in `cli.py` — both manually smoke-tested against a hand-generated pilot artifact for Inferno
  I.1–9 (matches the worked example above exactly; that pilot artifact was deleted after
  verification, it is not committed).
- `tests/test_skel.py` (25 tests) + `tests/test_hashes.py` (3 tests) — all passing, no
  regressions in the existing 61.

**What's not started**: the build driver itself. Concretely, in order:

1. **`skel/skel.py`** — structurally copy `dep/dep.py` (same file the design plan cited as the
   template): `SYSTEM_PROMPT` with one full worked example (use Inferno I.1–3: `ritrovai`
   subj-∅/obl:in/obl:per, `smarrita` subj), reuse `dep.sentence_groups` verbatim for parse units
   (must stay unit-aligned with Layer 4 for the divergence check to mean anything), a prompt
   builder that shows numbered lines + POS-annotated token list (dep's format) + the Layer-3 NP
   list as citation anchors — **deliberately omit the Layer-4 parse** from the prompt (that's
   what makes the divergence check meaningful; see `skel.py`'s docstring). Output table columns:
   `Pred Line | Pred Token | Pred Word | Role | Arg Line | Arg Token | Arg Word` (zero-arg
   predicate = Role `-`; pro-drop = Arg Line/Token `0`/`0`, Arg Word `∅`). Recovery: copy
   `_merge_tables` verbatim; `_continue_if_missing` should be keyed off `derive_unit`'s
   predicate set (request rows for derived predicates the model's output is missing). `RETRIES
   = 2`; per-unit `write_skel` after zero hard violations; resume from committed TSV; modes
   `--check`/`--clean`/`--fix`/`--dry-run`/`--log`; `--fix` keeps a unit only under the
   no-worse-off guarantee (strictly fewer soft, zero hard) exactly like `dep/dep.py`'s `_fix_canto`.
2. **`skel/Makefile`** — mirror `dep/Makefile` (`include ../model.mk`; `all`/`skel`/`check`/`fix`
   targets).
3. **Pilot build**: `uv run skel/skel.py inferno -c 1 -m ollama:gemma4:31b-it-qat` (the local
   model in `model.mk`), then `--check`. **Expect a nontrivial soft-divergence count on the
   first pass** — the mixed copular styles frozen into the Layer-4 corpus (UD-style `amara`/`è
   cop` vs spaCy-style `è root`/`cosa attr`, see `dep.py`'s `attr` comment) are the likely
   largest single source, by analogy with `dep/CORRECTIONS.md`'s `attr`-vocabulary story. Record
   the raw count before touching anything (measure-then-freeze).
4. **Triage the divergences**, same ladder as `dep/CORRECTIONS.md`: deterministic fix first (if
   a divergence class turns out to be a `derive_unit` bug, fix `skel.py`, not the artifact) →
   LLM `--fix` regeneration (no-worse-off guaranteed) → hand-verified exemption (only if a
   genuine reading `derive_unit` structurally can't express) → hand-edit as an absolute last
   resort (document in `skel/CORRECTIONS.md`, following `dep/CORRECTIONS.md`'s precedent of
   checking each instance against its terzina rather than blanket-applying a rule).
5. **`skel/README.md`** — write once the first canto's numbers are known; follow the structure
   of `dep/README.md` (artifact format, generation approach, validation tiers, CLI usage,
   *Check* section with the measured hard/soft counts).
6. **Scale to all 100 cantos**, gate on `--check` = 0 hard (soft count reported, triaged same as
   above until it converges or is exemption-flagged).
7. **Final `dante_corpus/README.md` update** — add `text skel` / `hash` CLI sections and
   `Canto.skel()`/`Canto.hashes()`/`SkelTuple` to the Public API listing (Layers 2–4's sections
   there are the template).
8. **This document** — once the build is complete, update the *Status* section's Layer 5 entry
   to "implemented and complete" with the final hard/soft counts, matching how Layers 3–4 are
   currently described.

No further design decisions are expected to be needed for any of the above — every open question
(role vocabulary, artifact schema, predicate definition, checker semantics, id scheme, hashing)
was resolved and implemented in commit `f7819b0`. If a build-time surprise contradicts something
this document states, prefer what the code and tests actually do (they're authoritative) and
update this document to match, rather than re-deriving the design from scratch.
