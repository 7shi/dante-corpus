# Phase 5 Retrospective: Deterministic Elimination vs. Monolithic LLM Regeneration

This document provides a comprehensive post-mortem and reference report on Layer 5 (predicate-argument skeleton) **Phase 5**, tracking the reduction of soft validation violations from **5,919** down to **2,084** before the Phase 6 restructuring.

---

## 1. Key Findings & Core Lessons Learned

Phase 5 was the project's most prolonged and iterative phase. It began with the hypothesis that remaining soft divergences could be resolved by repeated LLM regeneration (`--fix`) against refined system prompts. Over dozens of subphases and empirical measurements, Phase 5 disproved this hypothesis and established the architectural principles that govern the current stack.

### 1.1 The Inefficiency and Flat Yield of Monolithic LLM Regeneration
- **The Flat Yield Ceiling**: Across static residues, full-corpus monolithic `--fix` passes consistently delivered a flat yield of **~0.08 to 0.11 violations removed per LLM call** (Phase 5e: 0.11; Phase 5q: 0.086; Phase 5t: 0.085; Phase 5w: 0.095; Phase 5u: 0.068). Over 90% of model calls produced zero net improvement.
- **Structural All-or-Nothing Penalty**: The legacy `--fix` driver evaluated parse units as indivisible blocks, accepting a regeneration only if total unit violations decreased (`_is_improvement`). A model resolving 1 of 4 violations while leaving the other 3 intact was discarded completely, wasting the call.
- **Prose Rules in Monolithic Prompts Fail**: Adding lengthy prose rules to a massive monolithic system prompt did not improve LLM adherence (Phase 5v/5w). Models only responded when instructions and worked examples were delivered directly at the flagged position via per-violation hints or dedicated class prompts.

### 1.2 "LLM Error" Was Overwhelmingly Checker Silence or Upstream Mistags
- **Checker Silence**: Aggregate statistics initially categorized huge violation clusters (such as `extra_arg subj`) as "LLM hallucinations" or "reading disagreements". Per-position audits (Inferno 1, 1–3, 4–6) proved that in the majority of cases, the LLM was linguistically correct and `derive_unit` was simply silent (e.g., non-finite predicates lacking subject propagation, coordinated arguments not tracked down `conj` chains, copular complements hosting obliques).
- **Zero-Cost Deterministic Power**: Deterministic checker rules (Rules C–T, U, V, W, X, Y–AF) and cross-layer corrections resolved **thousands of violations in seconds at zero LLM cost**, outperforming months of LLM regeneration passes.
- **Upstream Layer Hygiene**: Many divergences stemmed from errors in Layer 2 morphology or Layer 4 dependency annotations (e.g., multiple `obj` tokens on a single predicate, relative pronouns mistagged as `mark`, clitics tagged with wrong POS). Correcting upstream layers immediately dissolved downstream Layer 5 conflicts.

### 1.3 The Provenance Law of Regeneration Yield
- An LLM regeneration pass achieves high yield (e.g., Phase 5s: **0.199 / call**) **only when run immediately after an upstream intervention introduces fresh, LLM-authored artifact errors** (such as surfaced extra tuples from bug fixes or newly promoted speech frames).
- When run after a checker acceptance rule that creates no new LLM-authored rows (e.g., Phase 5u following Rule V: **0.068 / call**), yield hits an all-time low because the remaining set is hardened, static residue. Provenance of the violation set, not its raw magnitude, dictates regeneration efficiency.

### 1.4 In Hindsight: What Should Have Been Done (View from Phase 6)
Phase 6's subsequent success — achieving **−78.8%** on `extra_tuple_adverb` and **−54.1%** on `extra_tuple_adjective` in a single pass while clearing 73 violations deterministically at zero LLM cost — provides clear hindsight on how Phase 5 should have been executed:

1. **Terminate Brute-Force Monolithic Regeneration Early**:
   - As soon as Phase 5e established the flat **0.11 / call** ceiling, monolithic whole-unit regeneration should have been permanently halted. Thousands of LLM calls across Phases 5q, 5t, 5u, and 5w were spent on a method already proven incapable of resolving static residue.
2. **Adopt Class-Specific Micro-Prompts and Row Splicing Immediately**:
   - Instead of asking a model to re-author an entire multi-line parse unit against an ever-expanding `SYSTEM_PROMPT`, the tool should have isolated individual flagged positions with focused micro-prompts (Stage 2) and accepted improvements row-by-row. This would have eliminated the all-or-nothing penalty where one unsolved violation discarded several valid fixes.
3. **Prioritize Per-Position Manual Reads over Aggregate Statistics**:
   - Aggregate statistical classification repeatedly misdiagnosed root causes (e.g., misclassifying 479 non-finite subject omissions as "LLM hallucinations" until Rule V read them manually). Exhaustive, position-by-position reads of small samples (Inferno 1, 1–3, 4–6) should have been the first exploratory step to uncover checker silence and upstream mistags, rather than the last resort.
4. **Deploy Deterministic Pre-Passes Before Model Calls**:
   - Deterministic repairs (Phase 6 Stage 1: Tier A label canonicalizations like `prep_stack` and Tier B agreement-gated repairs like `null_subject`) should have been mechanized upfront, ensuring no model call was ever spent on a mechanically decidable pattern.

---

## 2. Chronological Summary of Subphases & Interventions

```
5919 (Pre-5a) ──► 5105 (5a) ──► 4846 (5b) ──► 4615 (5e, LLM) ──► 4327 (5f)
──► 4097 (5g) ──► 4068 (5h) ──► 4042 (5i, Dep) ──► 3924 (5j) ──► 3876 (5k)
──► 3808 (5l) ──► 3746 (5m) ──► 3725 (5n, Dep) ──► 3712 (5o) ──► 3702 (5p, Dep)
──► 3551 (5q, LLM) ──► 3465 (5r/Case Annex) ──► 3545 (Multi-Obj/Bug Fix)
──► 3215 (5s, LLM) ──► 3270 (Subject-Agreement) ──► 3136 (5t, LLM)
──► 2623 (Rule V/Audit) ──► 2531 (5u, LLM) ──► 2408 (5w, LLM)
──► 2330 (Rules W/X) ──► 2084 (Rules Y–AF) ──► [Phase 6]
```

### 2.1 Foundational Structural Normalizations (Phases 5a – 5d)
- **Phase 5a (5919 → 5105, Δ −814)**:
  - **Rule C (Coordination Normalization, −665)**: Normalized argument citations along `conj` dependency chains before comparing. Addressed the dominant failure where `derive_unit` only saw direct children while LLMs cited second/third conjuncts.
  - **Rule D (`nmod` Oblique of an Argument, −155)**: Accepted an oblique dependent attached via `nmod` to a derived argument (`ha bisogno di te`).
- **Phase 5b (5105 → 4846, Δ −259)**:
  - Suppressed conjunctions promoted to predicates, double-listing of copula/modal structures, and accepted adverbial obliques.
- **Phases 5c & 5d (Validation & Audit)**:
  - Established Phase 5c acceptance gate (`_is_improvement`: zero hard violations, no net increase in soft violations).
  - Audited `expl` class; confirmed Layer 4 was correct and divergences were genuine LLM misreadings.

### 2.2 First Full-Corpus `--fix` Pass & Systematic Role Mismatch Rules (Phases 5e – 5k)
- **Phase 5e (4846 → 4615, Δ −231)**:
  - Full-corpus monolithic `--fix` pass (2,037 units attempted, 178 accepted, yield: 0.11 / call). Proved that clearing structurally unfixable units did not lift the baseline LLM yield.
- **Phase 5f (4615 → 4327, Δ −288)**:
  - **Rule L (`_oblique_lemma_refinement`)**: Accepted given `obl:<lemma>` against derived bare `obl` when the preposition was fused into a clitic or contraction missing from explicit dependency case edges.
- **Phase 5g (4327 → 4097, Δ −230)**:
  - **Rule M (`_predicative_complement`)**: Accepted given `xcomp` vs derived `obj`/`subj` for secondary predicates and copular predicate nominals.
- **Phase 5h (4097 → 4068, Δ −29)**:
  - **Rule N (`_case_marked_object`)**: Accepted given `obl:<lemma>` against derived `obj`/`subj` when the argument carried a matching `case` child.
- **Phase 5i (4068 → 4042, Δ −26)**:
  - Upstream Layer 4 correction: Retagged 26 double-`obj` clitics in `dep/` to `iobj` or `obl`.
- **Phase 5j (4042 → 3924, Δ −118)**:
  - **Rule O (`_co_present_preposition`, −61)**: Accepted secondary prepositions in stacked prepositions (`in su le porte`).
  - Corpus-wide rebuild of `_PREP_LEMMA_NORM` (−57).
- **Phase 5k (3924 → 3876, Δ −48)**:
  - **Rule P (`ccomp` ≡ `xcomp`)** and **Rule Q (Clausal arguments attached as `obj`/`subj`)**.

### 2.3 Direct-Child Bucket Exhaustion & Upstream Retagging (Phases 5l – 5p)
- **Phase 5l (3876 → 3808, Δ −68)**:
  - **Rule R**: Accepted predicative adjectives attached in Layer 4 as `advmod`.
- **Phase 5m (3808 → 3746, Δ −62)**:
  - **Rule S**: Accepted `nmod` complements attached directly to the predicate head.
- **Phase 5n (3746 → 3725, Δ −21)**:
  - Upstream Layer 4 correction: Audited the `mark` bucket; retagged 22 relative/interrogative pronouns filling argument slots off `mark` in `dep/`.
- **Phase 5o (3725 → 3712, Δ −13)**:
  - **Rule T**: Accepted `obl:<lemma>` over marker-matching `advcl` clauses (prepositional infinitives like `per venir`).
- **Phase 5p (3712 → 3702, Δ −10)**:
  - Upstream Layer 4 corrections on 6 clausal complements plus 2 multi-edge deferrals.

### 2.4 Second `--fix` Pass, Case Annex Audits & Phase 5r (3702 → 3465)
- **Phase 5q (3702 → 3551, Δ −151)**:
  - Monolithic `--fix` pass across 1,702 flagged units (yield: 0.086 / call, Δ −147) + typo fix `ioj` → `iobj` (−4, reducing `unknown_role` to 0).
- **The Case Annex Pre-History (Steps 6–9, 2026-07-31 … 2026-08-02)**:
  - Before integrating `case/` into Layer 5, four cross-layer audit batches cleaned systematic errors in `case/*.tsv` against `dep/`:
    - **Step 6 (Bare Clitics)**: 50 bare clitic contradictions (`mi, ti, ci, vi, si, li`) → 1 `dep/` mistag, 49 `case/` corrections.
    - **Step 7 (Word-Order & Impossible Pairings)**: 40 `obl` × `nominative` impossible pairings and 208 named contradictions → 12 impossible pairings and 99 contradictions corrected in `case/`, 9 `dep/` retags.
    - **Step 8 (Transitivity Checks)**: `dative` vs `nsubj` (8), `accusative` vs `iobj` (12), and `dative` vs `obj` (24) → 33 `case/` corrections, 3 `dep/` retags, 11 verified and left standing for structural reasons.
    - **Step 9 (`accusative` vs `nsubj`)**: 43 candidates read individually → 31 `case/` corrections to `nominative`, 12 verified exceptions. Contradictions closed at 32, impossible pairings at 26 (frozen, verified residue).
- **Phase 5r Integration (3633 → 3465, Δ −168)**:
  - **Rule U (`_case_corroborated_role`, −160)**: Integrated the frozen `case/` annex as a third arbiter. Accepted a `role_mismatch` when the annex corroborated the derived (`dep`) role against the LLM. Excluded fused verb+clitic tokens (`venendomi`) via `_bare_pronoun_position`.
  - **17 Mirror Candidates Hand-Audited (−8)**: 10 `dep` retags (clitics, causative *fare*), 4 `case` corrections, 8 verified and left alone (e.g., copular predicate nominals being nominative like subjects).

### 2.5 Upstream Audits & Provenance Oscillations (Phases 5s – 5u)
- **Multiple-`obj` Audit & Adverb Bug Fix (3465 → 3545, Honest Count Rise +80)**:
  - **Multiple `obj` Check in `dep/`**: Flagged 203 predicates carrying >1 `obj` child. All 203 corrected across 316 row edits in `dep/` (88 `conj` coordinations, 63 secondary predicates relabeled **`attr`** rather than `xcomp` so `derive_unit` would not invent adjective predicates, 22 reflexive `expl`, 27 partitive/locative `obl`, 9 clitic `iobj`, 14 gapping `orphan`). `dep --check` returned to 0 soft.
  - **Adverb Bug Fix**: Fixed `"verb" in pos.lower()` matching `adverb`, which had caused `derive_unit` to invent spurious predicate tuples matching 72 LLM tuples. Removing it surfaced them as `extra_tuple` (+36 net).
- **Phase 5s (3545 → 3215, Δ −330)**:
  - Full-corpus `--fix` pass on fresh LLM-authored errors (1,659 units attempted; yield **0.199 / call**). `extra_tuple` fell 19.8%, proving fresh error is highly responsive to regeneration.
- **Subject-Agreement Round (3215 → 3270, Honest Count Rise +55)**:
  - Added Layer 4 `nsubj` person/number agreement check against finite heads (173 flagged → 18 verified residue).
  - 155 corrections applied (77 Layer-2 rows, 424 Layer-4 rows across 66 cantos).
  - **Speech Frame Promotion**: Normalized 99 elided speech frames ("Ed elli a me: «…»") corpus-wide to UD ellipsis promotion (+105 `missing_tuple` on Layer 5).
- **Phase 5t (3270 → 3136, Δ −134)**:
  - Full-corpus `--fix` pass (1,575 units; yield **0.085 / call**). The newly added speech frames (`missing_tuple`) dropped 22.1% (33 of 99 promoted frames absorbed), while older static residue stayed flat.
- **Rule V & Membership Audit (3136 → 2623, Δ −513)**:
  - **Rule V (`_control_subject_candidates`, −479)**: Discovered via per-position read of Inferno 1. `derive_unit` previously derived no subject for non-finite verbs without explicit `nsubj` children, reporting every LLM-resolved subject as `extra_arg subj` (805 instances). Rule V traversed ancestor chains to accept control/raising subjects (289), `acl` participles (155), and causative datives (13), keeping 316 genuine disagreements flagged.
  - **Cross-Layer Membership Audit (−34)**: Classified 82 `membership` violations by POS; corrected 37 Layer-2 mistags (`onde`, proclitic pronouns, `quantunque`), 8 Layer-4 rows, 32 `case/` rows, and 4 Layer-3 spans. Left 47 genuine checker questions.
- **Phase 5u (2623 → 2531, Δ −92)**:
  - Full-corpus `--fix` pass following Rule V (1,347 units; yield **0.068 / call** — historical low). Confirmed that checker acceptance rules create no new LLM-authored material for regeneration to harvest.

### 2.6 Prompt Alignment & Targeted Instruction Delivery (Phases 5v – 5w)
- **Phase 5v (Prompt Rewrite)**:
  - Audited conventions missing from `SYSTEM_PROMPT`: elided speech frames, non-finite subjects, adverb predicates, and `attr` gloss. Rewrote `--fix` hints.
- **Phase 5w (2531 → 2408, Δ −123)**:
  - Full-corpus `--fix` pass on rewritten prompt (1,290 calls; yield **0.095 / call**).
  - **Critical Finding**: The single class provided with a worked table and rewritten hint (`missing_tuple`) dropped **28.6%**, while prose-only rules moved at the pass average (~4.9%). Proved that prose buried in prompts does not change model behavior; instructions must reach the model at the flagged position.

### 2.7 Per-Position Reading Rounds (Rules W, X, Y–AF)
- **Rules W & X (2408 → 2330, Δ −78)**:
  - Per-position read of Inferno 1's remaining 5 violations.
  - **Rule W (`_case_corroborated_swap`, −24)**: When a transitive clause has inverted subject/object roles and one leg is a pronoun corroborated by the case annex (e.g., `che` in "lo passo che non lasciò già mai persona viva"), accepted the matching noun leg (`persona`).
  - **Rule X (`_complement_hosted_argument`, −54)**: Accepted arguments of copular constructions attached in Layer 4 to the copula but cited by LLM under the predicate complement.
  - **Procedural Lesson**: A per-position read must investigate *which rule declined to fire*, rather than just interpreting the line.
- **Rules Y–AF (2330 → 2084, Δ −246)**:
  - Per-position audit of all 26 remaining soft violations in Inferno 1–3.
  - **The Core Finding on `role_mismatch`**: `role_mismatch` did not move at all (234 before and after). Because both layers explicitly speak, it represents genuine disagreement rather than checker silence.
  - **8 New Checker Rules**:
    - **Rule Y (`_copular_predication`, −8)**: Accepted copular clause heads Layer 4 attached under a nominal deprel ("per non esser men belli").
    - **Rule Z (`_verb_in_argument_slot`, −77)**: Accepted verbal arguments in argument/adjunct slots (generalizing `per` + infinitive, "fui per ritornar più volte vòlto").
    - **Rule AA (`_secondary_predicate_over_argument`, −3)**: Accepted depictive small clauses attached in Layer 4 as `acl` of an object ("vid' ïo scritte").
    - **Rule AB (`_reflexive_clitic_argument`, −63)**: Accepted reflexive clitics tagged `expl` in Layer 4 read by LLM as `obj`/`iobj`/`obl:a` ("tal mi fec' ïo").
    - **Rule AC (`_inherited_subject`, −26)**: Absorbed echo disagreements where conj-propagated subjects match the head predicate ("chiese Lucia ... e disse").
    - **Rule AD (`_copular_adverb_complement`, −14)**: Accepted adverb complements of copular `essere` ("m'è tardi").
    - **Rule AE (`_free_relative_head`, −12)**: Accepted free relatives cited at either the pronoun head or clause verb ("chi lo scrisse").
    - **Rule AF (`membership` check, −39, 47 → 8)**: Admitted any token Layer 4 places in an argument slot regardless of POS.
  - **7 Cross-Layer Corrections**: Fixed 4 Layer-2 rows, 11 Layer-4 rows (including an elided speech frame at Inferno 3:13 missed earlier), and 1 `case/` row.
  - **POS-Keyed Hints**: Introduced POS-keyed `_fix_hint` phrasings for surviving `extra_tuple` adverbs (33) and adjectives (37).

---

## 3. Cost and Efficiency Comparison

| Approach / Intervention | Violations Removed | Computational & Human Cost | Yield (Δ / Call) |
|---|---|---|---|
| **Phase 5e `--fix` pass** (Monolithic LLM) | 231 | 2,037 LLM calls | 0.113 |
| **Phase 5q `--fix` pass** (Monolithic LLM) | 147 | 1,702 LLM calls (~28 h) | 0.086 |
| **Phase 5s `--fix` pass** (Fresh Error Harvest) | 330 | 1,659 LLM calls | **0.199** |
| **Phase 5t `--fix` pass** (Monolithic LLM) | 134 | 1,575 LLM calls | 0.085 |
| **Phase 5u `--fix` pass** (Post-Rule V Residue) | 92 | 1,347 LLM calls | **0.068** |
| **Phase 5w `--fix` pass** (Rewritten Prompt) | 123 | 1,290 LLM calls | 0.095 |
| **Phases 5a + 5b** (Rules C, D, normalizations) | **1,073** | 0 calls (instant) | $\infty$ |
| **Phase 5f** (Rule L: `obl` lemma refinement) | **288** | 0 calls (instant) | $\infty$ |
| **Phase 5g** (Rule M: secondary predicates) | **230** | 0 calls (instant) | $\infty$ |
| **Phase 5j** (Rule O + prep lemma normalization) | **118** | 0 calls (instant) | $\infty$ |
| **Phase 5r** (Rule U: case annex integration) | **160** | 0 calls (instant) | $\infty$ |
| **Rule V** (Non-finite control subjects) | **479** | 0 calls (instant) | $\infty$ |
| **Rules W + X** (Case swap + Copula args) | **78** | 0 calls (instant) | $\infty$ |
| **Rules Y–AF** (Inferno 1–3 audit rules) | **246** | 0 calls (instant) | $\infty$ |

---

## 4. Architectural Legacy: The Bridge to Phase 6

Phase 5 exhaustively demonstrated that attempting to solve residual soft violations via brute-force whole-unit regeneration was economically unviable and technically flawed. Its hard-won insights directly informed the three-stage architecture implemented in **Phase 6**:

1. **Stage 1 (Deterministic Auto-Repair)**: Runs deterministic rewrites first (Tier A label canonicalization, Tier B agreement-gated repairs), resolving dozens of violations before any model invocation.
2. **Stage 2 (Class-Specific POS-Keyed Micro-Prompts)**: Completely replaces monolithic prompts with narrow, single-question queries focused on specific violation subclasses (`extra_tuple_adverb`, `extra_tuple_adjective`, `extra_arg_adjective`, `role_mismatch`). Splicing answers row-by-row eliminates the all-or-nothing penalty.
3. **Stage 3 (Fallback Whole-Unit Regeneration)**: Reserved strictly as an opt-in fallback for complex multi-violation units.

---

## 5. Technical Deep-Dive: Why Early Regeneration Stalled

### 5.1 The Measured Baseline (Phase 4b Benchmarks)
Initial empirical tests on a local model (`ollama:gemma4:31b-it-qat`, Inferno 1, 136 lines, 19 flagged units) measured the baseline performance of monolithic `--fix`:
- **Wall Time**: 3 hours (serial).
- **Units Attempted**: 19.
- **Units Improved**: 2 (10.5% success rate).
- **Soft Violations Removed**: 4 (37 → 33).
- **Extrapolation**: Across 2,235 flagged units, a full pass would require ~2,235 calls to remove ~450 violations. Phase 5e later verified this empirically (2,037 calls removed 231 violations, 8.7% success rate).

### 5.2 Root Cause: Structurally Unfixable Parse Units
The low success rate was not a model limitation, but a structural property of the flagged population. Analysis of the 2,848 `extra_arg` violations (48% of the corpus residue) showed:
- **Depth-2 Indirect Descendants**: 38.5% (1,097)
- **Unrelated Tokens**: 31.7% (902)
- **Direct Child (outside `derive_unit`'s map)**: 17.4% (495)
- **Pro-drop ∅**: 4.5% (129)
- **`conj`-relative Child**: 4.3% (122)

The dominant depth-2 bucket was overwhelmingly **coordination**:
```
inferno 1:103  ciberà -[obj]->   terra  -[conj]-> sapïenza   (LLM: obj)
inferno 1:128  è      -[nsubj]-> città  -[conj]-> seggio     (LLM: subj)
inferno 1:114  onora  -[obj]->   te     -[conj]-> quei       (LLM: obj)
```
In `"si ciberà di terra e di sapïenza"`, both conjuncts are semantic objects. The LLM was correct, but `derive_unit` only read direct children. Regenerating the unit reproduced the same correct reading, failed the `_is_improvement` check, and discarded the LLM call. Rule C (Phase 5a) resolved this deterministically.

---

## 6. Systematic Audits & Deliberately Rejected Candidates

### 6.1 Direct-Child Deprel Exhaustion (Section 2a Audit)
Every direct-child deprel omitted by `derive_unit` was systematically audited and resolved:

| Deprel | Pre-5l Count | Final Resolution |
|---|---|---|
| `expl` | 87 | **Closed**: Audited in Phase 5d; Layer 4 was correct (59 clitic misreadings). |
| `nmod` | 62 | **Closed**: Resolved by Rule S (Phase 5m). |
| `advcl` | 51 | **Closed**: 13 prepositional infinitives resolved by Rule T (Phase 5o); 6 clausal complements retagged in Layer 4 (Phase 5p); 35 complement-vs-adjunct cases classified. |
| `advmod` | 50 | **Closed**: Predicative adjectives accepted by Rule R (Phase 5l); adverb predicatives left flagged. |
| `mark` | 35 | **Closed**: 22 relative/interrogative pronouns retagged off `mark` in Layer 4 (Phase 5n). |
| `cop`, `conj`, `vocative`, tail | 39 | **Closed**: Tail one-offs and minor configurations. |

### 6.2 Deliberately Rejected Candidate Rules
Several plausible rules were implemented, tested across all 100 cantos, and deliberately rejected:

- **Rule A (Enumerate conjuncts in `derive_unit`)**: Emitting a derived row for each `conj` child moved `extra_arg` −554 but caused `missing_arg` +529 (net −2). LLMs enumerate coordinated arguments inconsistently (sometimes listing all conjuncts, sometimes only the first). Normalization (Rule C) was the proper solution.
- **Rule B (Share non-subject args across coordinated predicates)**: Measured at **+2,326 violations ❌**; caused massive false derivations across coordinated clauses.
- **Rule E (Widen control-subject authority)**: Allowing xcomp/ccomp candidate sets when `derive_unit` resolved a subject yielded only −22 ❌, disproving the hypothesis that the residual `extra_arg subj` mass was control-licensed.
- **Loose Rule T (Bare `obl` over any `advcl`)**: Measured at −2; rejected because subordinator markers (`ove`, `quando`) are not prepositions and lack tree corroboration.
- **Imported Verb-Valency Lexicon**: Rejected on architectural neutrality grounds. External lexicons violate the principle that the corpus must be derived solely from the Italian source text.

---

## 7. Measurement Methodology & Candidate Rule Harness

To test candidate rules without altering persistent artifacts, Phase 5 established a standard monkeypatch testing pattern across all 100 cantos:

```python
import sys; sys.path.insert(0, ".")
import skel as driver
from dante_corpus import api, dep, skel

orig = skel._classify_divergence

def wrapper(given, derived, dep_index_by_pos=None, morph_pos_by_position=None):
    vs = orig(given, derived, dep_index_by_pos, morph_pos_by_position)
    # Apply candidate rule filter / logic here
    return vs

skel._classify_divergence = wrapper
driver.skel._classify_divergence = wrapper

for canticle in api.canticles():
    for number in api.cantos(canticle):
        data = skel.load_skel(canticle, number)
        morph_rows, np_rows = driver._morph_rows(canticle, number), driver._np_rows(canticle, number)
        dep_rows = driver._dep_rows(canticle, number)
        lines = api.canto(canticle, number).lines()
        text_by_no = {ln.no: ln.text for ln in lines}
        nos, texts = [ln.no for ln in lines], [ln.text for ln in lines]
        for unit in dep.sentence_groups(nos, texts, dep.MAX_UNIT_LINES):
            if any(no not in data for no in unit):
                continue
            driver._classify_violations(
                unit, [text_by_no[no] for no in unit],
                {no: list(data[no]) for no in unit}, morph_rows, np_rows, dep_rows)
```

This harness allowed rapid, risk-free validation of every proposed rule before committing changes to `dante_corpus/skel.py`.
