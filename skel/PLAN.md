# skel — Layer 5 Plan: Deterministic Derivation & Targeted Micro-Fixes

## Status

- **Current State**: `make -C skel check` reports **0 hard, 1247 soft** violations across all 100 cantos (down from 17,438 at the first full-corpus measurement).
- **Other Layers**: `dep --check` 0 hard / 18 soft (verified standing residue), `case --check` 0 hard, `np --check` 0/0, `morph --check` 0/0, `pytest` 243 passed.
- **Phase 5**: Complete and closed (reduced soft violations from 5,919 to 2,084). Full historical record, per-phase measurement tables, cost comparisons, and lessons learned are documented in [`PHASE5.md`](PHASE5.md).
- **Phase 6**: Rebuilt `--fix` into a three-stage driver (Stage 1 deterministic, Stage 2 class-specific POS-keyed micro-prompts, Stage 3 fallback). Two user-run rounds so far: **2011 → 1452 (−27.8%)**, then **1409 → 1247 (−11.5%)**.
- **Latest Work**:
  - **Rule AG (Inferno 4–6 Read)**: Gated `conj` subject propagation on Layer-2 person/number agreement (`dep.subject_agreement` + `_finite_head_of`), scoring **1452 → 1409 soft (−43)** with zero model calls.
  - **Second `--fix` round (2026-08-14)**: First live pass of the `extra_arg_adjective` micro-prompt; **1409 → 1247 (−162)**, 0 regressed / 0 newly flagged. See *Second User-Run `--fix` Round* below.

---

## Phase 6 Operating Principles & Architecture

Building on Phase 5's hard-won lessons, Phase 6 eliminates brute-force whole-unit regeneration in favor of targeted, cost-effective interventions:

### 1. Three-Stage `--fix` Hierarchy
Every flagged parse unit passes through three stages, cheapest first, under the same acceptance gate (0 hard violations, `_is_improvement`):
- **Stage 1 (Deterministic Auto-Repair)**: Runs before any model call.
  - **Tier A (No Reading Asserted)**: Label canonicalizations (`role_label` 7, `prep_stack` 4).
  - **Tier B (Corroborated Reading)**: Independent signal required (e.g., `null_subject` 31 gated on `dep.subject_agreement`). Verified and idempotent.
  - `--repair` is this stage executed in isolation.
- **Stage 2 (Class-Specific POS-Keyed Micro-Prompts)**:
  - Bypasses monolithic `SYSTEM_PROMPT`.
  - Sends a concise 20–30 line prompt specific to the violation class (`extra_tuple_adverb`, `extra_tuple_adjective`, `extra_arg_adjective`, `role_mismatch`, `missing_arg`, `missing_tuple_nominal`).
  - Solves one question at a time and splices answers row-by-row, eliminating the all-or-nothing unit rejection penalty.
- **Stage 3 (Fallback Whole-Unit Regeneration)**:
  - Opt-in fallback for complex multi-violation interactions. Can be disabled with `--no-whole` for benchmarking.

### 2. Independence Rule
A question may name the predicate, the argument the LLM itself cited, and the role slot in dispute (what `_fix_hint` already disclosed), but **never** `derive_unit`'s own derived argument position.

### 3. Evaluation at Subclass Granularity
- Never evaluate passes or rules by overall pass averages alone.
- Measure changes at `_violation_subclass` granularity against their specific target population.

### 4. Per-Position Manual Reads as Primary Discovery Engine
- Aggregate statistics frequently misdiagnose checker silence as LLM error.
- Exhaustive position-by-position reads of small canto batches (Inferno 1, 1–3, 4–6, and next 7–9) uncover genuine checker silence (e.g., Rules V, W, X, Y–AF, AG) and upstream layer errors.

### 5. Immediate Cross-Layer Remediation
- Upstream defects in Layer 2 (`morph/`), Layer 4 (`dep/`), or the pronoun case annex (`case/`) discovered during audits must be corrected in the same session, re-validated, and documented in `*/CORRECTIONS.md`.

### 6. Strict Division of Labor
- **Assistant**: Conduct per-position audits, implement deterministic checker/derivation rules, develop Stage 2 micro-prompts/hints, and maintain upstream layer data.
- **User**: Execute parallel `--fix` regeneration passes (`make -C skel fix`) and commit updated TSVs.

---

## Phase 6 Implementation & Results

### 1. The Restructuring (2026-08-12)
- Rebuilt `skel/skel.py` driver to replace monolithic prompt regeneration with Stage 1 auto-repairs and Stage 2 micro-prompts.
- Stage 1 deterministic pass measured at **2084 → 2011 (−73)** with zero LLM calls.
- Two candidate rules measured and deliberately dropped: a case-annex relabel (106 rewrites for 0 violations eliminated) and a `role_alias` rule (population 0).

### 2. First User-Run `--fix` Round (2026-08-13)
- **2011 → 1452 soft, −559 (−27.8%)**, 98 cantos touched, 259 units cleared outright, 197 improved. 0 units regressed, 0 newly flagged.
- **Subclass Results**:
  - `extra_tuple_adverb`: **37 → 7 (−78.8%)** (largest single-class drop on record).
  - `extra_tuple_adjective`: **37 → 17 (−54.1%)**.
  - `role_mismatch`: −40.8%.
  - `missing_tuple_nominal`: −40.3%.
  - Classes without dedicated stage-2 prompts (`extra_tuple`, `missing_tuple`, `membership`): ~0% (confirming gains stemmed from targeted prompts).

### 3. Rule AG & Inferno 4–6 Read (2026-08-13)
- Position-by-position audit of all 19 remaining soft violations in Inferno 4–6.
- **Rule AG (−43, 1452 → 1409)**: Gated `conj` shared-subject propagation on Layer-2 person/number agreement (`dep.subject_agreement` + `_finite_head_of` for periphrastic verbs). Out of 1370 candidates, 682 agreed, 461 were undecidable (untouched), and **227 actively disagreed** and were dropped.
- **Cross-Layer Correction**: Retagged `fiacco` (Inferno 6:54) from adjective to 1sg verb in `morph/inferno/06.tsv`.
- Remaining 17 positions verified as real LLM omissions or genuine reading disagreements.

### 4. Third POS-Keyed Class: `extra_arg_adjective`
- From Inferno 6:70 ("Alte terrà... le fronti"), identified that 65 of 107 `extra_arg xcomp`/`attr` violations cite an adjective argument.
- Implemented `extra_arg_adjective` class in `skel/skel.py` (`_violation_subclass`, `_CLASS_PROMPTS` with `_CONV_ADJECTIVE` fronted, `_fix_hint`).

### 5. Second User-Run `--fix` Round (2026-08-14)
- **1409 → 1247 soft, −162 (−11.5%)**, 76 files touched (161 insertions / 158 deletions).
- Unit-level: **841 → 765 flagged**; 76 cleared outright, 62 improved, 703 unchanged, **0 regressed, 0 newly flagged**.
- Per-unit yield **0.193 violations removed per unit flagged before** — less than half the first round's rate, as expected: the first round consumed the easy population of the classes that had just been given prompts, and what remains is progressively harder residue.
- **Subclass results** (before → after):

  | subclass | before | after | delta |
  | --- | ---: | ---: | ---: |
  | `extra_arg` | 597 | 535 | −62 (−10.4%) |
  | `missing_arg` | 522 | 465 | −57 (−10.9%) |
  | `role_mismatch` | 132 | 115 | −17 (−12.9%) |
  | `extra_arg_adjective` | 65 | 52 | −13 (−20.0%) |
  | `missing_tuple_nominal` | 40 | 39 | −1 (−2.5%) |
  | `extra_tuple_adjective` | 17 | 13 | −4 (−23.5%) |
  | `extra_tuple` | 14 | 12 | −2 (−14.3%) |
  | `membership` | 8 | 7 | −1 (−12.5%) |
  | `extra_tuple_adverb` | 7 | 4 | −3 (−42.9%) |
  | `missing_tuple` | 7 | 5 | −2 (−28.6%) |

- **Reading of `extra_arg_adjective` (−20.0%)**: the new prompt works but is far from the −54% its sibling `extra_tuple_adjective` scored on its debut round. Its population was already the *residue* of a class the first round had worked over, so −20% on a pre-filtered population is not evidence the prompt is weak. Deciding between "prompt needs sharpening" and "the remaining 52 are genuine reading disagreements" requires a per-position read, not another pass.
- Two structurally identical repairs seen in the diff, illustrating both halves of the round: Inferno 3:13 replaced an empty placeholder row with a four-tuple predicate on `elli` (`missing_tuple`), and Inferno 6:70 dropped a spurious `attr` on `terrà` while 6:72 specialized a bare `obl` to `obl:di`.

---

## Active & Open Routes

No `--fix` round is queued. Both rounds so far have shown that a pass repeats the previous round's
pattern at a lower rate; the next one should follow new checker rules or a sharpened prompt, not
precede them.

### Open Assistant-Side Routes
- **`extra_arg subj` with `∅ (0,0)` (69 of 215 `extra_arg subj`)**: the largest single homogeneous
  bucket left. These are pro-drop subjects the LLM wrote as the null position while the derivation
  found an overt one (or vice versa). Read a sample to decide whether this is a checker rule
  (accept `∅` where Layer 4 has no overt `nsubj`) or a real divergence.
- **`role_mismatch` `xcomp` vs `obl` (21) and `obj` ↔ `subj` (36 across both directions)**: the two
  dominant mismatch shapes. The `obj`/`subj` swap is a symmetric pair, which suggests one
  systematic cause rather than scattered slips.
- **Attributive vs. Predicative Adjectives (13 `extra_tuple_adjective` remaining, down from 37)**:
  - True reading disagreements with no `cop` edge (e.g., Inferno 2:109 *"non fur mai persone ratte / a far lor pro"*).
  - Target: Conduct a per-position read of the remaining 13 before writing any checker rule.
- **`extra_arg_adjective` residue (52)**: per-position read to separate prompt weakness from genuine
  reading disagreement — see the reading of its −20.0% above.
- **Adverbs Promoted to Predicates (4 `extra_tuple_adverb` remaining, down from 33)**:
  - Effectively closed by the Stage 2 micro-prompt. Read the final 4 positions to decide whether any residue warrants prompt tweaks or checker acceptance.
- **Stacked Prepositions in Layer 4 (14 `role_mismatch` / 18 unattached)**:
  - Where Layer 4 inconsistently writes stacked prepositions (flat vs. chained, e.g., *"in su"*). Requires a `dep/` normalization pass.
- **Per-Position Read of Inferno 7–9**:
  - Continue the per-position audit discipline to uncover new checker rules and upstream mistags (specifically checking adverb-headed obliques with nested `nmod` and locative clitics tagged `advmod`).
- **`missing_arg obl` Sample Audit**:
  - Sample the largest remaining unexplained bucket to classify whether omissions are structural or LLM recall limits.

---

## How to Measure a `--fix` Round

1. Create a clean worktree at base HEAD:
   ```bash
   git worktree add <scratch>/base HEAD
   # Symlink generated src/ directories into worktree if needed
   ```
2. Run validation across all cantos in both trees:
   ```bash
   uv run skel.py inferno purgatorio paradiso --check
   ```
3. Diff at the **parse-unit** level (`dep.sentence_groups`):
   - Units flagged before / after.
   - Units improved / cleared.
   - Units that regressed or were newly flagged (must remain **0**).
4. Compute per-unit yield (violations removed ÷ units flagged before).
5. Output results broken down by `_violation_subclass`.
