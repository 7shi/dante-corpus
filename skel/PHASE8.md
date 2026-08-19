# Phase 8 Retrospective: Codebase Restructuring, Rule Registry & Modular Decomposition

This document provides a comprehensive post-mortem and reference report on Layer 5 (predicate-argument skeleton) **Phase 8**, tracking the architectural transformation of the Layer-5 codebase following the achievement of **0 hard / 0 soft violations** in Phase 7.

- **Baseline at opening (2026-08-18)**: 0 hard / 0 soft violations across all 100 cantos. Monolithic `dante_corpus/skel.py` (4,484 lines) with 84 rule letters in comments, tightly coupled driver tests, and scattered language constants.
- **Final result (2026-08-19)**: **0 hard / 0 soft violations preserved corpus-wide**; `pytest` **547 passed**; 130 registered rules with dynamic census; self-contained test fixtures; `ItalianLanguagePack` extracted; `GrammarContext` unified interface; modular package `dante_corpus/skel/` (8 modules) and modular CLI drivers (`driver_fix.py`, `driver_build.py`, `driver_ui.py`, `skel.py`).
- **Related Phase records**:
  - Phase 5: 5,919 → 2,084 soft violations — [`PHASE5.md`](PHASE5.md).
  - Phase 6: 2,084 → 160 soft violations (Rounds 1–7, nineteen read batches) — [`PHASE6.md`](PHASE6.md).
  - Phase 7: 160 → 0 soft violations (100% clean corpus-wide) — [`PHASE7.md`](PHASE7.md).
  - Future Roadmap & Local LLM Harness: [`PLAN.md`](PLAN.md), [`PORTABILITY.md`](PORTABILITY.md).
  - Grammar Handbook: [`RULES.md`](RULES.md) (Japanese edition: [`RULES-ja.md`](RULES-ja.md)).

---

## 1. Executive Summary & Objectives

With the achievement of **0 hard / 0 soft violations** across all 100 cantos of the *Divina Commedia* at the close of Phase 7, the 0-soft verification status transitioned into an active **regression gate**. Phase 8 leveraged this safety net to perform deep architectural refactoring that would have been unsafe during active residue reduction:

1. **Eliminate Rule Opacity**: Move rule identities and logic from inline comments into an introspectable, measurable `@rule` registry.
2. **Decouple Test Suites**: Replace driver tests pinned to live canto data with self-contained, frozen parse unit fixtures.
3. **Isolate Language Dependencies**: Separate Italian-specific syntax constants from Universal Dependencies (UD) algorithms into a formal `LanguagePack`.
4. **Unify Cross-Layer Access**: Encapsulate multi-layer token queries (Layers 1–4) behind a clean `GrammarContext` interface.
5. **Decompose Monolithic Modules**: Break down the ~4,900-line `dante_corpus/skel.py` and ~2,130-line `skel/skel.py` into cohesive, well-defined submodules while maintaining 100% backward compatibility.

---

## 2. Phase 8 Chronological Milestones (§P8.1 – §P8.5)

### §P8.1 — Rule Registry & Dynamic One-Shot Census
- **Implementation**: Created formal `@rule` registration framework (`Rule`, `RuleRegistry`, `RULES`, `rule_active`) in `dante_corpus/skel/registry.py`.
- **Dynamic Census Tool (`skel/census_rules.py`)**: Built an in-memory census tool that disables each rule one-by-one and runs `--check` across all 100 cantos (3,477 parse units) in ~2 seconds.
- **Findings**:
  - Registered **130 rules** spanning 6 operational branches:
    - **Active (82 rules)**: Directly prevent violations (`count_on_removal > 0`), holding off 5,888 total regressions when combined.
    - **Auxiliary / Structural (5 rules)**: Maintain pipeline invariants or structural checks (`I`, `AN`, `BN`, `CN`, `EG`).
    - **Dormant / Subsumed (43 rules)**: Historical sub-predicates or conceptual variants now covered by broader gates.
- **Documentation**: Generated the full 130-rule grammar handbook and hierarchical tree taxonomy in [`RULES.md`](RULES.md) and [`RULES-ja.md`](RULES-ja.md).

### §P8.2 — Test Fixture Decoupling
- **Problem**: Driver tests in `tests/test_skel_fix.py` asserted counts directly against live canto files (e.g. `purgatorio 1`, `inferno 5`). When fixes improved those cantos, test assertions broke.
- **Implementation**:
  - Created `tests/fixtures/skel_fixtures.py` containing frozen, self-contained `ParseUnit` fixtures (`make_purgatorio_1_adverb_fixture()`, `make_inferno_5_arg_slot_fixture()`, etc.).
  - Rewrote driver unit tests in `tests/test_skel_fix.py` to run exclusively against fixtures.
  - Retained a single, dedicated integration test (`test_live_canto_integration`) to verify end-to-end driver operation against real corpus artifacts.

### §P8.3 — Language Pack Extraction (`ItalianLanguagePack`)
- **Problem**: 7 Italian-specific surface vocabulary constants were scattered across general UD derivation and validation logic.
- **Implementation**:
  - Defined `LanguagePack` base class and concrete `ItalianLanguagePack` in `dante_corpus/skel/models.py`.
  - Extracted all 7 Italian syntactic constants:
    1. `prep_lemma_norm`: Preposition lemma normalizations and article contractions.
    2. `rel_pronoun_words`: Relative pronoun word forms for nominal head acceptance.
    3. `relative_pronouns`: Relative pronoun forms for control and antecedent linking.
    4. `relativizers`: Broader relativizing particles for negative clausal gates.
    5. `comparative_particles`: Comparison markers in Layer-4 `case` slots.
    6. `comparative_lemmas`: Comparison markers by Layer-2 lemma.
    7. `locative_relative_lemmas`: Locative relative markers by lemma.
  - Decoupled core derivation and validation algorithms to operate via the active `LanguagePack`. Added unit tests in `tests/test_skel.py`.

### §P8.4 — Grammatical Layer Stack Interface (`GrammarContext`)
- **Problem**: Helper functions took up to 10 positional dictionary and list arguments (`dep_index_by_pos`, `morph_pos_by_position`, `case_by_position`, `children_by_pos`, etc.) to query Layers 1–4.
- **Implementation**:
  - Implemented `GrammarContext` class wrapping token, morphology, case annex, NP span, and dependency tree lookups.
  - Provided structured query methods: `ctx.dep_at()`, `ctx.morph_at()`, `ctx.head_of()`, `ctx.deprel_of()`, `ctx.is_verb()`, `ctx.is_pronoun()`, `ctx.case_slot()`, `ctx.children_of()`, `ctx.find_ancestor()`.
  - Refactored derivation and rule evaluation routines to pass `GrammarContext`. Verified 0 regressions across all 547 unit tests.

### §P8.5 — Modular Decomposition of `dante_corpus/skel` and `skel/` CLI Driver
- **Problem**: `dante_corpus/skel.py` (~4,880 lines) and `skel/skel.py` (~2,130 lines) were monolithic single files mixing data models, derivation algorithms, 130 rules, validation checks, repair routines, I/O serializers, prompt templates, terminal UI, and CLI orchestration.
- **Implementation**:
  1. **Subpackage `dante_corpus/skel/`**:
     - `models.py` (338 lines): Core dataclasses (`SkelRow`, `Repair`, `Violation`, `LanguagePack`, `ItalianLanguagePack`, `GrammarContext`).
     - `registry.py` (220 lines): Rule registration engine (`Rule`, `RuleRegistry`, `RULES`, `rule_active`).
     - `derive.py` (528 lines): Deterministic predicate-argument derivation engine (`derive_unit`, control propagation, coordination subject mapping, gapped remnants).
     - `rules.py` (2,176 lines): Divergence classification rules (Rules A–EI) and subject authority predicates.
     - `repairs.py` (255 lines): Deterministic auto-repair engine (`_find_repairs`, `_apply_unit_repairs`, Tier A/B rules).
     - `validate.py` (811 lines): Validation engine (`validate_unit`, token/predicate checks, argument membership, dual-role check EG).
     - `io.py` (396 lines): File serialization/deserialization (`load_skel`, `write_skel`, `has_skel`, `resolve_chunk`, markdown parser).
     - `__init__.py` (144 lines): Clean public API re-export preserving 100% backward compatibility.
  2. **Modularized CLI Drivers in `skel/`**:
     - `skel/skel.py` (352 lines): Thin CLI entry point handling `argparse` and subcommands (`check`, `repair`, `build`, `fix`, `stats`, `diff`).
     - `skel/driver_fix.py` (1,290 lines): Stage 2 `--fix` driver, prompt generator, answer parsing, refusal classification, field notes logging.
     - `skel/driver_build.py` (350 lines): Stage 3 whole-unit regeneration, LLM API client, retry loop.
     - `skel/driver_ui.py` (155 lines): Terminal UI formatting, streaming status lines, progress indicators.

---

## 3. Dynamic Rule Census Metrics (Phase 8 Final)

Measurement executed in-memory across all 100 cantos (3,477 parse units, 18,340 tuples) via `skel/census_rules.py`:

| Category | Count | Description |
| :--- | :---: | :--- |
| **Active Rules** | **82** | Directly prevent violations (`count_on_removal > 0`). Hold off 5,888 total regressions. |
| **Auxiliary / Invariant Rules** | **5** | Enforce pipeline invariants and internal consistency (`I`, `AN`, `BN`, `CN`, `EG`). |
| **Dormant / Subsumed Rules** | **43** | Sub-predicates or conceptual variants covered by broader classification gates. |
| **Total Registered Rules** | **130** | Full catalog systematized in [`RULES.md`](RULES.md). |

### Top 15 Load-Bearing Rules by Removal Impact

| Rule ID | Name | Category | Removal Impact | Operational Function |
| :--- | :--- | :--- | :---: | :--- |
| `V` | `control_subject_inheritance` | `subject_authority` | **+2,137** | Inherit subject along non-finite control head chains |
| `CY` | `clausal_complement_aux_double_listing` | `missing_arg` | **+834** | Tolerate clausal complements double-listed under aux/cop |
| `C` | `coordination_collapse` | `normalization` | **+705** | Map argument citations across `conj` edges onto coordination head |
| `L` | `oblique_lemma_refinement` | `role_mismatch` | **+340** | Reconcile bare `obl` with lemma-qualified `obl:<prep>` |
| `Y` | `copular_nominal_predication` | `extra_tuple` | **+202** | Accept nominal clause heads attached under copular deprel |
| `J` | `adverbial_oblique` | `extra_arg` | **+179** | Tolerate adverbial obliques in locative/directional slots |
| `U` | `case_corroborated_role` | `role_mismatch` | **+144** | Adjudicate pronoun role discrepancies via Layer-2 case annex |
| `D` | `drop_nmod_obliques` | `normalization` | **+142** | Drop `nmod` obliques whose parent nominal is cited as argument |
| `M` | `predicative_complement` | `role_mismatch` | **+133** | Reconcile predicative complement `xcomp` against `obj`/`subj` |
| `O` | `co_present_preposition` | `role_mismatch` | **+127** | Permit co-present prepositional variants for one argument |
| `R` | `predicative_advmod` | `extra_arg` | **+90** | Tolerate predicative adjectives/adverbs attached as `advmod` |
| `AF` | `dep_argument_membership` | `membership` | **+80** | License Layer-4 argument deprels as valid Layer-5 arguments |
| `AB` | `reflexive_clitic_argument` | `extra_arg` | **+74** | Tolerate reflexive clitics on pronominal verbs |
| `Z` | `verb_in_argument_slot` | `extra_tuple` | **+69** | Suppress false predicates for verbs in argument/adjunct slots |
| `AJ` | `conj_shared_argument` | `extra_arg` | **+53** | Tolerate arguments shared across coordinate conjuncts |

---

## 4. Phase 8 Artifact State & Verified Invariants

At the conclusion of Phase 8:
- **Corpus Verification**: `skel/skel.py inferno purgatorio paradiso --check` reports **0 hard, 0 soft violations** across all 100 cantos (100% clean).
- **Other Layers**: `dep --check` 0/0, `case --check` 0, `np --check` 0/0, `morph --check` 0/0.
- **Test Suite**: `pytest` **547 passed** in ~1.5s across all 12 test modules.
- **Backward Compatibility**: All external imports (`from dante_corpus.skel import ...`) operate identically.
- **Phase Status**: Phase 8 is formally closed. Development transitions to Phase 9 (Autonomous Grammar Agent Harness for Local LLMs, [`PLAN.md`](PLAN.md)).
