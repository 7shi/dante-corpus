# Dante Corpus: Unified Grammatical Layers & Post-Zero Architecture Plan

### Handoff (2026-09-08) — resume here

> **Current State & Baseline**:
> - **All five layers & pronoun case annex**: **0 hard / 0 soft violations across all 100 cantos** (Inferno 0, Purgatorio 0, Paradiso 0; `pytest` **739 passed** — 552 corpus + 187 harness).
> - **Documentation reorganized**: Phase 7 completed record is closed in [`skel/PHASE7.md`](skel/PHASE7.md). Phase 8 refactoring record is closed in [`skel/PHASE8.md`](skel/PHASE8.md). [`skel/RULES.md`](skel/RULES.md) compiles the full 130-rule grammar handbook and tree taxonomy. [`harness/PLAN.md`](harness/PLAN.md) and [`skel/PORTABILITY.md`](skel/PORTABILITY.md) organized for upcoming work and portability design.
> - **Tool Call Protocol sub-project COMPLETE** (T1–T5; both live gates PASSED), and now **historical**: the prompt-instructed XML protocol was the adopted wire format (Gemini API executed it ~3x faster than local Ollama), but both transports and the session that used them were deleted on 2026-09-07 — there is no wire protocol to choose any more. The record stays in [`harness/TOOLCALL.md`](harness/TOOLCALL.md).
> - **Active Regression Gate**: The **0-soft regression gate** is active corpus-wide. Any refactoring must preserve 0 hard / 0 soft violations and pass all tests.
>
> **`harness/` is CLOSED (2026-09-08); active work moves to `layers/`.** Stages
> 1–10 all closed and Stage 10 was the last: autonomous inference benchmark,
> rule/lexicon extraction, context optimization, full-corpus verification, corpus
> durability, soft divergence reduction, refactoring, soft `--fix` levels 2 and 3,
> and fixed-context execution — which replaced the per-unit tool-calling session
> with a bounded step whose request size is a function of the unit rather than the
> iteration count. Three pieces of closing work followed: the harness was **cut**
> to the run and fix paths it is actually driven by, the generic apparatus was
> **split out** into `dante_corpus/harness/` (a library that imports nothing else
> from `dante_corpus`), and both changes were **verified live**. The harness's own
> reconstruction of Layer 5 is hard-clean (0 hard / **2,954** soft against the
> derivation contract) and never touched gold `skel/` — which since 2026-09-07 it
> does not open at all.
> *All harness planning, progress, and stage records are consolidated in
> [`harness/PLAN.md`](harness/PLAN.md) — refer to it (and only it) for
> harness work. This file is not kept in sync with harness-internal
> progress; it only reflects the coarse status above.*
>
> **Active work: Layer Structure Review (`layers/`)** — opened 2026-09-07,
> because the harness finished what it was built for and the thing it was
> pointed at turned out to be undecided. Its subject is the layer structure
> itself rather than one layer's contents: what each layer can and cannot
> express, and what the description ought to say. The assumption it drops is the
> one this file has carried throughout — that `skel/` and the layers beneath it
> are an *immutable* reference. See [`layers/PLAN.md`](layers/PLAN.md), which is
> the single reference for that work.

## Current Status (2026-09-08)

**All five grammatical layers and the pronoun case annex are fully implemented, built for all 100 cantos of the *Divina Commedia*, modularized, and merged to `main`.**

- **Layer 1 — Tokens**: 0 check failures (`dante_corpus/tokenizer.py`, served via `Line.tokens`).
- **Layer 2 — Morphology + Lemma**: 0 hard / 0 soft violations across all 100 cantos ([`morph/README.md`](morph/README.md)).
- **Pronoun Case Annex**: 0 hard violations across all 100 cantos ([`case/README.md`](case/README.md)).
- **Layer 3 — Noun Phrases**: 0 hard / 0 soft violations across all 100 cantos ([`np/README.md`](np/README.md)).
- **Layer 4 — Dependency Trees**: 0 hard / 0 soft violations across all 100 cantos ([`dep/README.md`](dep/README.md)). Stacked prepositions normalized and subject-agreement residue closed (see [`dep/CORRECTIONS.md`](dep/CORRECTIONS.md)).
- **Layer 5 — Predicate-Argument Skeleton**: **0 hard / 0 soft violations across all 100 cantos** ([`skel/README.md`](skel/README.md), [`skel/RULES.md`](skel/RULES.md)).
- **Test Suite**: `pytest` **739 passed** (552 corpus + 187 harness; corpus tests ~1 s). The harness count fell from 471 as the modules it covered were deleted on 2026-09-07; no surviving test was weakened.
- **Layer 5 Divergence Residue**: **0** (Inferno 0, Purgatorio 0, Paradiso 0).

### Layer 5 Phase Retrospectives
- **Phase 5 (5,919 → 2,084 soft)**: Deterministic Elimination vs. Monolithic LLM Regeneration ([`skel/PHASE5.md`](skel/PHASE5.md)).
- **Phase 6 (2,084 → 160 soft)**: Targeted Micro-Fixes, Full-Corpus Read Series (Rules AG–EH), and Refusal Split ([`skel/PHASE6.md`](skel/PHASE6.md)).
- **Phase 7 (160 → 0 soft)**: Refusal Census Audits, Outlier Elimination, Upstream Retags, and Complete Residue Closure ([`skel/PHASE7.md`](skel/PHASE7.md)).
- **Phase 8 (Modular Restructuring & Portability)**: Rule Registry (130 rules), Test Fixtures, `ItalianLanguagePack`, `GrammarContext`, Modular Decomposition into `dante_corpus/skel/` and `skel/driver_*.py` ([`skel/PHASE8.md`](skel/PHASE8.md)).

---

## Next Steps: From the Harness to the Layer Structure

With **0 hard / 0 soft violations** achieved corpus-wide and codebase restructuring completed in Phase 8, the active 0-soft regression gate enabled downstream tooling. The first of those, the harness, is now finished; what it found is what opens the next item.

1. **Dedicated Grammar Agent Harness for Local LLMs (`harness/`)** — *Closed
   2026-09-08*:
   - A specialized agent harness in `harness/` adopting a staged bottom-up
     architecture: Stage 1 autonomous inference (`runner/`) ➔ Stage 2 rule &
     lexicon extraction (`extractor/`) ➔ Stage 3 context optimization ➔
     Stage 4 full-corpus verification ➔ Stage 5 corpus durability ➔ Stage 6
     soft divergence reduction ➔ Stage 7 refactoring ➔ Stage 8 soft
     `--fix` level 2 ➔ Stage 9 fixed-context execution ➔ Stage 10 soft
     `--fix` level 3 — **all ten closed, and 10 was the last**.
   - Reconstructed Layer 5 against the 0-soft ground truth (`skel/`) without
     ever writing to it, and stopped reading it entirely on 2026-09-07.
   - What survives is a **library**: the generic apparatus now lives in
     `dante_corpus/harness/` and ships with the distribution, while top-level
     `harness/` holds Layer 5's side of it — the gates' content, the fix
     levels, the toolset, the skill files, the CLI and the `recon/` artifacts.
   - *Details, closing readouts & records*: [`harness/PLAN.md`](harness/PLAN.md)
     — the single reference for all harness work; not duplicated or kept in
     sync here.

2. **Layer Structure Review (`layers/`)** — *Active, opened 2026-09-07*:
   - The harness met its mission (a reproducible, automated, generalizable
     reconstruction pipeline) but not the assumption printed beside it: that the
     layer stack it reconstructs is an immutable reference. Stage 10 closed on
     a finding of exactly that shape — a class the token-indexed layers have no
     vocabulary to decide.
   - Subject: the layer structure itself — what each layer can and cannot
     express, and what the description ought to say — with
     `dante_corpus.harness` used as the tool rather than developed as one.
   - *Details*: [`layers/PLAN.md`](layers/PLAN.md), the single reference.

3. **Long-Term Portability & Cross-Corpus Extensions**:
   - Declarative rule scheduling DAG, additional language packs (Latin, etc.).
   - *Details*: [`skel/PORTABILITY.md`](skel/PORTABILITY.md).

---

## Standing Disciplines

- **0-Soft Regression Gate**: Any refactoring or layer update must preserve 0 hard / 0 soft violations across all layers.
- **Measure by Violation Diff**: Measure checker rules and interventions by violation diff, never by total count alone.
- **Mutation Testing**: Pin every rule with tests that fail when the rule is removed or broken.
- **Cross-Layer Hygiene**: Correct upstream defects in Layer 2 (`morph/`), Layer 4 (`dep/`), or `case/` immediately and document in `*/CORRECTIONS.md`.
- **CRLF Hygiene**: Ensure strict `\n` line endings.
- **Editing Frozen TSVs**: Never edit frozen TSVs by hand; use gated scripts asserting expected tokens.

---

## Why this lives in the corpus

`dante-corpus` is the queryable, **canon-neutral source of truth** for the *Commedia*: it serves
the normalized Italian text, the token stream, the nested quote-span tree, morphology, pronoun case,
noun phrases, dependency syntax trees, and predicate-argument skeletons, all derived from
the poem itself with no external ontology. All five layers and the pronoun case annex are now fully
computed, frozen, and verified at **0 hard / 0 soft violations across all 100 cantos** (suite now
at `pytest` 739 passed including the harness).

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

---

## The layers

Five grammatical layers, each a deterministic or verified function of the source text. Examples use *Inferno* I.1–6.

```
1  Nel mezzo del cammin di nostra vita
2  mi ritrovai per una selva oscura,
3  ché la diritta via era smarrita.
4  Ahi quanto a dir qual era è cosa dura
5  esta selva selvaggia e aspra e forte
6  che nel pensier rinova la paura!
```

- **Layer 1 — Tokens** (`dante_corpus/tokenizer.py`): Deterministic token stream served via `Line.tokens`. Splits apostrophe-linked elisions (`ch'`, `i'`), preserves contractions (`Nel`, `del`), excludes punctuation (`has_alpha`). Verified against source lines.
- **Layer 2 — Morphology + Lemma** ([`morph/README.md`](morph/README.md)): Per-token lemma, part of speech, and inflectional features (gender, number, person, tense, mood), frozen as `morph/<canticle>/NN.tsv`.
- **Pronoun Case Annex** ([`case/README.md`](case/README.md)): Permanent Layer-2 sibling directory (`case/<canticle>/NN.tsv`) annotating grammatical case for every pronoun and clitic token.
- **Layer 3 — Noun-Phrase Enumeration** ([`np/README.md`](np/README.md)): Exhaustive and over-inclusive noun phrases with heads and spans (`np/<canticle>/NN.tsv`). Nesting is derived at serve time by span containment.
- **Layer 4 — Dependency / Grammatical Role** ([`dep/README.md`](dep/README.md)): Universal Dependencies syntactic trees (`dep/<canticle>/NN.tsv`) with clause functions and head attachments rejoining enjambed noun phrases across lines.
- **Layer 5 — Predicate-Argument Skeleton** ([`skel/README.md`](skel/README.md)): Predicate ↔ argument tuples (`skel/<canticle>/NN.tsv`) in UD-derived roles, validated by deterministic derivation (`derive_unit`). All 100 cantos verified at 0 hard / 0 soft violations.

---

## Out of scope — consumer responsibilities

These are intentionally absent from the corpus because they are not determined by the text's own
grammar; they are contested judgments, normalizations, or bindings to something external:

- **Entity-hood and entity typing** — which layer-3 noun phrases are entities, and of what kind.
- **Coreference / referent identity** — linking pronouns, pro-drop subjects, and epithets to a single referent.
- **Closed relation vocabulary** — mapping a layer-5 predicate onto a frozen relation set.
- **Frame** — literal / simile / prophecy / reported.
- **Reference equivalents and truth-conditions** — any alignment to an English (or other) reference translation.
- **An imported verb-valency lexicon** — complement-vs-adjunct dictionaries not determined by the Italian line.

---

## Build & serve model

- **Artifact**: one structured file per canto per layer under its own directory.
- **Versioning**: every canto × layer artifact is **content-addressed** with content hashes (`dante_corpus/hashes.py`).
- **Build driver**: resumable, streaming UI progress via `llm7shi.statusline`.
- **Validation**: per-layer check tools verifying zero hard and zero soft violations across all 100 cantos.
- **API**: queryable via Python SDK (`Canto.morph()`, `Canto.dep()`, `Canto.skel()`, etc.) and CLI (`dante-corpus text skel`).

---

## Sequencing & Completed Roadmap

1. **Layer 2 (morphology + lemma)** — *Complete and verified* ([`morph/README.md`](morph/README.md)).
2. **Pronoun case extension** — *Complete and verified* ([`case/README.md`](case/README.md)).
3. **Layer 3 (noun phrases)** — *Complete and verified* ([`np/README.md`](np/README.md)).
4. **Layer 4 (dependency)** — *Complete and verified* ([`dep/README.md`](dep/README.md)).
5. **Layer 5 (skeleton)** — *Complete and verified at 0 hard / 0 soft* ([`skel/README.md`](skel/README.md), [`skel/PHASE5.md`](skel/PHASE5.md), [`skel/PHASE6.md`](skel/PHASE6.md), [`skel/PHASE7.md`](skel/PHASE7.md)).
6. **Phase 8 (Codebase Restructuring & Portability)** — *Complete (8.1–8.5)* ([`skel/PHASE8.md`](skel/PHASE8.md), [`skel/PORTABILITY.md`](skel/PORTABILITY.md)):
   - Rule Registry & Census (130 rules registered, measured via `census_rules.py`, documented in [`skel/RULES.md`](skel/RULES.md)).
   - Self-contained test fixtures (`tests/fixtures/skel_fixtures.py`).
   - Language pack extraction (`ItalianLanguagePack`).
   - Layer stack interface (`GrammarContext`).
   - Modular decomposition: `dante_corpus/skel/` subpackage (models, registry, derive, rules, repairs, validate, io) & `skel/` CLI drivers (`driver_ui.py`, `driver_build.py`, `driver_fix.py`, `skel.py`).
   - Verified at 0 hard / 0 soft violations and 547 pytest passing.
7. **Dedicated Grammar Agent Harness (`harness/`)** — *Complete and closed
   (Stages 1–10, 2026-09-08)*; the generic apparatus split out into
   `dante_corpus/harness/` as a library ([`harness/PLAN.md`](harness/PLAN.md),
   single reference for status).
8. **Layer Structure Review (`layers/`)** — *In progress* ([`layers/PLAN.md`](layers/PLAN.md), single reference for status).
