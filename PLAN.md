# Dante Corpus: Unified Grammatical Layers & Post-Zero Architecture Plan

### Handoff (2026-08-19) — resume here

> **Current State & Baseline**:
> - **All five layers & pronoun case annex**: **0 hard / 0 soft violations across all 100 cantos** (Inferno 0, Purgatorio 0, Paradiso 0; `pytest` **547 passed**).
> - **Documentation reorganized**: Phase 7 completed record is closed in [`skel/PHASE7.md`](skel/PHASE7.md). Phase 8 refactoring record is closed in [`skel/PHASE8.md`](skel/PHASE8.md). [`skel/RULES.md`](skel/RULES.md) compiles the full 130-rule grammar handbook and tree taxonomy. [`skel/PLAN.md`](skel/PLAN.md) and [`skel/PORTABILITY.md`](skel/PORTABILITY.md) organized for upcoming work and portability design.
> - **Active Regression Gate**: The **0-soft regression gate** is active corpus-wide. Any refactoring must preserve 0 hard / 0 soft violations and pass all 547 tests.
>
> **Immediate Next Priority: Phase 9 — Grammatical Parsing Harness for Local LLMs**:
> *(Full architectural specifications and templates: [`skel/HARNESS.md`](skel/HARNESS.md) and [`skel/PLAN.md`](skel/PLAN.md)).*
>
> 1. **9.1 Multi-Layer Context Packager (`skel/harness.py`)**:
>    - Build context builder providing local models (e.g. **Gemma 4**) with integrated 5-layer diagnostic context (text + morphology + case annex + NP spans + UD dependency trees).
>    - Render structured markdown/JSON prompts that present full syntax context without withholding evidence.
>
> 2. **9.2 Autonomous Reasoning Protocol (CoT)**:
>    - Implement structured chain-of-thought prompt templates (Agreement & Voice, Head Token Citation, Complement vs. Adjunct, Full Frame Generation).
>
> 3. **9.3 Interactive Validation & Self-Correction Loop**:
>    - Harness executes `validate_unit()` in-process on model-generated frames.
>    - Automatically feed back diagnostic strings to the LLM for autonomous multi-turn repair until 0-soft is reached.
>
> 4. **9.4 Gemma 4 Benchmarking & Evaluation**:
>    - Benchmark Gemma 4 against the 87 historical Phase 7 divergence positions.

## Current Status (2026-08-19)

**All five grammatical layers and the pronoun case annex are fully implemented, built for all 100 cantos of the *Divina Commedia*, modularized, and merged to `main`.**

- **Layer 1 — Tokens**: 0 check failures (`dante_corpus/tokenizer.py`, served via `Line.tokens`).
- **Layer 2 — Morphology + Lemma**: 0 hard / 0 soft violations across all 100 cantos ([`morph/README.md`](morph/README.md)).
- **Pronoun Case Annex**: 0 hard violations across all 100 cantos ([`case/README.md`](case/README.md)).
- **Layer 3 — Noun Phrases**: 0 hard / 0 soft violations across all 100 cantos ([`np/README.md`](np/README.md)).
- **Layer 4 — Dependency Trees**: 0 hard / 0 soft violations across all 100 cantos ([`dep/README.md`](dep/README.md)). Stacked prepositions normalized and subject-agreement residue closed (see [`dep/CORRECTIONS.md`](dep/CORRECTIONS.md)).
- **Layer 5 — Predicate-Argument Skeleton**: **0 hard / 0 soft violations across all 100 cantos** ([`skel/README.md`](skel/README.md), [`skel/RULES.md`](skel/RULES.md)).
- **Test Suite**: `pytest` **547 passed** in ~1.5s.
- **Layer 5 Divergence Residue**: **0** (Inferno 0, Purgatorio 0, Paradiso 0).

### Layer 5 Phase Retrospectives
- **Phase 5 (5,919 → 2,084 soft)**: Deterministic Elimination vs. Monolithic LLM Regeneration ([`skel/PHASE5.md`](skel/PHASE5.md)).
- **Phase 6 (2,084 → 160 soft)**: Targeted Micro-Fixes, Full-Corpus Read Series (Rules AG–EH), and Refusal Split ([`skel/PHASE6.md`](skel/PHASE6.md)).
- **Phase 7 (160 → 0 soft)**: Refusal Census Audits, Outlier Elimination, Upstream Retags, and Complete Residue Closure ([`skel/PHASE7.md`](skel/PHASE7.md)).
- **Phase 8 (Modular Restructuring & Portability)**: Rule Registry (130 rules), Test Fixtures, `ItalianLanguagePack`, `GrammarContext`, Modular Decomposition into `dante_corpus/skel/` and `skel/driver_*.py` ([`skel/PHASE8.md`](skel/PHASE8.md)).

---

## Next Steps: Autonomous Local LLM Grammar Harness

With **0 hard / 0 soft violations** achieved corpus-wide and codebase restructuring completed in Phase 8, the active 0-soft regression gate enables downstream tooling:

1. **Autonomous Grammar Parsing Harness for Local LLMs (Phase 9)**:
   - Build a specialized CLI harness (`skel/harness.py`) providing local models (e.g. **Gemma 4**) with integrated 5-layer diagnostic context (text + morphology + dependency trees).
   - Implement autonomous reasoning protocol (CoT) and interactive validation/self-correction loops.
   - Benchmark Gemma 4 on the historical Phase 7 divergence dataset.
   - *Details*: [`skel/HARNESS.md`](skel/HARNESS.md) and [`skel/PLAN.md`](skel/PLAN.md).

2. **Long-Term Portability & Cross-Corpus Extensions**:
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
6. **Phase 8 (Codebase Restructuring & Portability)** — *Complete (8.1–8.5)* ([`skel/PLAN.md`](skel/PLAN.md), [`skel/PORTABILITY.md`](skel/PORTABILITY.md)):
   - Rule Registry & Census (130 rules registered, measured via `census_rules.py`, documented in [`skel/RULES.md`](skel/RULES.md)).
   - Self-contained test fixtures (`tests/fixtures/skel_fixtures.py`).
   - Language pack extraction (`ItalianLanguagePack`).
   - Layer stack interface (`GrammarContext`).
   - Modular decomposition: `dante_corpus/skel/` subpackage (models, registry, derive, rules, repairs, validate, io) & `skel/` CLI drivers (`driver_ui.py`, `driver_build.py`, `driver_fix.py`, `skel.py`).
   - Verified at 0 hard / 0 soft violations and 547 pytest passing.
7. **Phase 9 (Autonomous Local LLM Harness)** — *Next Active Step* ([`skel/PLAN.md`](skel/PLAN.md), [`skel/HARNESS.md`](skel/HARNESS.md)).
