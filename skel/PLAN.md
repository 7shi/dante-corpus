# skel — Layer 5 Plan: Deterministic Derivation & Targeted Micro-Fixes

## Status

- **Current State**: `make -C skel check` reports **0 hard, 691 soft** violations across all 100 cantos (down from 17,438 at the first full-corpus measurement), after the **Inferno 21–25 read landed rules AZ–BI 2026-08-15** (834 → 691, −143, −17.1%, zero model calls) on top of rules AU–AY (888 → 834), AM–AT (963 → 888) and the third `--fix` round (1094 → 963). See *Rules AZ–BI and the Inferno 21–25 Read* below.
- **Other Layers**: `dep --check` **0 hard / 0 soft** (16 rows corrected 2026-08-15 by the Inferno 11–15 read, 25 more by the Inferno 16–20 read and 20 more by the Inferno 21–25 read the same day). The subject-agreement rule's 18-position residue closed 2026-08-14 (Layer 5 1091 → 1094), and **Layer 4's stacked prepositions were normalized the same day** — 161 multiword-preposition clusters rewritten to one UD shape (opening word `case`, later members `fixed`), moving Layer 5 by zero (see [`CORRECTIONS.md`](CORRECTIONS.md) and [`../dep/CORRECTIONS.md`](../dep/CORRECTIONS.md)). `case --check` 0 hard, `np --check` 0/0, `morph --check` 0/0 (3 rows corrected 2026-08-15 by the 11–15/16–20 reads, 5 more by the 21–25 read), `pytest` **311** passed.
- **Phase 5**: Complete and closed (reduced soft violations from 5,919 to 2,084). Full historical record, per-phase measurement tables, cost comparisons, and lessons learned are documented in [`PHASE5.md`](PHASE5.md).
- **Phase 6**: Rebuilt `--fix` into a three-stage driver (Stage 1 deterministic, Stage 2 class-specific POS-keyed micro-prompts, Stage 3 fallback). Three user-run rounds so far: **2011 → 1452 (−27.8%)**, **1409 → 1247 (−11.5%)**, **1094 → 963 (−12.0%)**.
- **Latest Work**:
  - **Rules AZ–BI + Inferno 21–25 read (2026-08-15)**: nine deterministic rules, 20 Layer-4 rows and 5 Layer-2 rows, scoring **834 → 691 (−143, −17.1%)** with zero model calls; Inferno 21–25 itself 44 → 16 — the largest batch of the series so far. Three of the nine are again mirror legs (AZ of rule R, BD of AW, BH of rule M), but the batch's new finding is **rule BB**: rule V was not missing a direction, it was written to pop *one* citation out of a map where a coordinate subject supplies three, and rule C then collapsed the survivors back onto the position it had just accepted. Two censused rules were dropped (the elided speech verb's `missing_tuple`, and result-clause `ccomp` at population 2), and a `dep.subject_agreement` refinement was measured at 12 new Layer-4 soft violations and deferred. See *Rules AZ–BI and the Inferno 21–25 Read* below and [`CORRECTIONS.md`](CORRECTIONS.md).
  - **Rules AU–AY + Inferno 16–20 read (2026-08-15)**: five deterministic rules, 25 Layer-4 rows and 1 Layer-2 row, scoring **888 → 834 (−54, −6.1%)** with zero model calls and **zero newly-flagged positions**; Inferno 16–20 itself 47 → 31. Three of the five are *mirror legs* of rules the checker already had (AV of `_aux_of_derived_predicate`, AW of AB, AY of `_elided_copula_nominal`), which is the batch's finding: a checker rule written for one direction of a labeling convention leaves the other direction reported. One censused rule was measured and **dropped** (gapped-clause remnants, population 12 — rule AN's assignment is right and the LLM's omission is reading error). See *Rules AU–AY and the Inferno 16–20 Read* below and [`CORRECTIONS.md`](CORRECTIONS.md).
  - **Rules AM–AT + Inferno 11–15 read (2026-08-15)**: eight deterministic rules, 16 Layer-4 rows and 2 Layer-2 rows, scoring **963 → 888 (−75, −7.8%)** with zero model calls; Inferno 11–15 itself 37 → 17. Four of the eight are in `derive_unit` itself — the first batch where the read found the derivation *wrong* rather than silent. Plus the fix side's first subject-slot branches (`missing_arg_subject`, `extra_arg_subject`, together 29% of the residue), a rewritten `missing_tuple_nominal` question, and a `_fix_hint` bug. See *Rules AM–AT and the Inferno 11–15 Read* below and [`CORRECTIONS.md`](CORRECTIONS.md).
  - **Third `--fix` round (2026-08-15)**: **1094 → 963 (−131)**, the first round preceded by new checker rules, a sharpened prompt and a new Stage-2 class. `missing_arg_adverb` **83 → 28 (−66.3%)** confirms the `_CONV_ADVERB` prompt-defect diagnosis; the elided-speech and appositive-adjective clauses moved ~nothing. See *Third User-Run `--fix` Round* below.
  - **Layer-4 prep-stack normalization (2026-08-14)**: closed the stacked-preposition route — 161 clusters, 196 rows, Layer 5 **1094 → 1094 net zero** by design; `dante_corpus/skel.py` gained a `fixed`-under-`case` lemma aggregation so rules O/`prep_stack` read the normalized shape (3 new tests). The route's old "14 role_mismatch / 18 unattached" count was Phase-5j-era and already absorbed.
  - **Rule AG (Inferno 4–6 Read)**: Gated `conj` subject propagation on Layer-2 person/number agreement (`dep.subject_agreement` + `_finite_head_of`), scoring **1452 → 1409 soft (−43)** with zero model calls.
  - **Second `--fix` round (2026-08-14)**: First live pass of the `extra_arg_adjective` micro-prompt; **1409 → 1247 (−162)**, 0 regressed / 0 newly flagged. See *Second User-Run `--fix` Round* below.
  - **Rules AH–AL + Inferno 7–10 read (2026-08-14)**: Five deterministic rules, five Layer-2 mistags and eight Layer-4 retags, scoring **1247 → 1091 (−156, −12.5%)** with zero model calls. Plus three prompt defects fixed and one new Stage-2 class (`missing_arg_adverb`), which move nothing until the next `--fix` round. See *Rules AH–AL and the Inferno 7–10 Read* below and [`CORRECTIONS.md`](CORRECTIONS.md).

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
  - Sends a concise 20–30 line prompt specific to the violation class — twelve of them, keyed by POS (`extra_tuple_adverb`, `extra_tuple_adjective`, `extra_arg_adjective`, `missing_arg_adverb`), by role (`extra_arg_subject`, `missing_arg_subject`), by predicate POS (`missing_tuple_nominal`), or by class alone (`role_mismatch`, `extra_arg`, `missing_arg`, `extra_tuple`, `missing_tuple`).
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
- Exhaustive position-by-position reads of small canto batches (Inferno 1, 1–3, 4–6, 7–10, 11–15, and next 16–20) uncover genuine checker silence (e.g., Rules V, W, X, Y–AF, AG, AH–AL) and upstream layer errors. The Inferno 7–10 read also found the reverse case: a defect in the *prompt* (`_CONV_ADVERB`'s omission licence) responsible for the single largest bucket in the residue, which no aggregate statistic had attributed to anything. The Inferno 11–15 read found a third kind: four defects in `derive_unit` itself (rules AM, AN, AT and rule AJ's missing directions), where the derivation was not silent but **wrong**.
- **As of 2026-08-15 the reads are a planned series covering all 100 cantos, and they run *before* the next `--fix` round** — see *The Read Series* below for the reasoning, the schedule, and the eight-step per-batch procedure. `skel/read.py` is the tool; `--check` names a position, `read.py` shows all five layers for its parse unit.

### 5. Immediate Cross-Layer Remediation
- Upstream defects in Layer 2 (`morph/`), Layer 4 (`dep/`), or the pronoun case annex (`case/`) discovered during audits must be corrected in the same session, re-validated, and documented in `*/CORRECTIONS.md`.

### 6. Strict Division of Labor
- **Assistant**: Conduct per-position audits, implement deterministic checker/derivation rules, develop Stage 2 micro-prompts/hints, and maintain upstream layer data.
- **User**: Execute parallel `--fix` regeneration passes (`make -C skel fix`) and commit updated TSVs.
- A read batch is therefore entirely the assistant's, start to finish: the eight steps in *How to Read a Batch* need no model call and no user action, and a batch is not finished until its write-ups and count updates are in.

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

### 6. Rules AH–AL and the Inferno 7–10 Read (2026-08-14)

Per-position read of all **37** soft violations in Inferno 7–10. **1247 → 1091 (−156, −12.5%)**,
zero model calls; Inferno 7–10 itself went 37 → 17. Full write-up, with the evidence line for each
rule, in [`CORRECTIONS.md`](CORRECTIONS.md).

| rule | shape | population | moved |
|---|---|---:|---:|
| **AH** | `extra_arg subj ∅` left standing after rule AG dropped the inherited subject | 69 | −14 |
| **AI** | Layer-3 NP head vs Layer-4 attachment naming one argument twice | 92 slots / 184 | −71 |
| **AJ** | an object or dative gapped from the coordination head onto a conjunct | — | −59 |
| **AK** | comparative `come` minted into `obl:come` from a Layer-2 conjunction | 7 | −6 |
| **AL** | a fused clitic cluster (`gliel` = `gli`+`lo`) genuinely filling two roles | 4 | −4 |

Upstream: 5 Layer-2 mistags (Inferno 7:38–39 `fuor`/`cherci`/`chercuti`, 8:71 `entro`, 10:23 `ten`)
and 9 Layer-4 rows (Inferno 8:78, 9:41 ×3, 9:72, 9:103, 10:23, 10:85, 10:87), plus 3 further
`come`/`perché` structures (8 rows: Inferno 30:59, Paradiso 3:36, 32:54) found by the
conjunction-in-argument-slot census. Two candidate rules were measured and **dropped**: a Stage-1
conjunction-anchored-predicate repair (population 0) and a 247-token relative-`che` retag (blocked
by the `case` annex — filling those rows from Layer 4 would make rule U circular).

Prompt side, unmeasured until the third round: the `_CONV_ADVERB` omission licence (82 positions),
the addressee-less elided-speech frame (4 of the 37 read), and appositive adjectives. Round 3
settled all three — the licence was the real defect, the other two moved nothing (see below).

---

### 7. Third User-Run `--fix` Round (2026-08-15)

- **1094 → 963 soft, −131 (−12.0%)**, 72 files touched (181 insertions / 76 deletions), 0 hard,
  `pytest` 268 passed.
- Unit-level: **696 → 618 flagged**; 78 cleared outright, 42 improved, 576 unchanged,
  **0 regressed, 0 newly flagged**.
- Per-unit yield **0.188**, against 0.66 (round 1) and 0.193 (round 2) — flat rather than
  declining, even though the base was already stripped of the 156 positions rules AH–AL had taken.
- Per canticle: inferno 303 → 264, purgatorio 410 → 360, paradiso 381 → 339.
- **Subclass results** (before → after):

  | subclass | before | after | delta |
  | --- | ---: | ---: | ---: |
  | `extra_arg` | 424 | 406 | −18 (−4.2%) |
  | `missing_arg` | 349 | 306 | −43 (−12.3%) |
  | `role_mismatch` | 105 | 100 | −5 (−4.8%) |
  | `missing_arg_adverb` | 83 | 28 | **−55 (−66.3%)** |
  | `extra_arg_adjective` | 51 | 49 | −2 (−3.9%) |
  | `missing_tuple_nominal` | 39 | 36 | −3 (−7.7%) |
  | `extra_tuple` | 14 | 12 | −2 (−14.3%) |
  | `extra_tuple_adjective` | 13 | 13 | ±0 |
  | `membership` | 7 | 7 | ±0 |
  | `missing_tuple` | 5 | 3 | −2 (−40.0%) |
  | `extra_tuple_adverb` | 4 | 3 | −1 (−25.0%) |

**What the round was a test of, and what it decided:**

- **`missing_arg_adverb` (−66.3%) — the prompt-defect diagnosis is confirmed.** This was the first
  class whose population was traced to a defect in the corpus's own prompt (`_CONV_ADVERB`'s "or it
  is left out" licence) rather than to the model, and removing the licence took 56 of its 83
  positions in one round — the second-largest single-class drop on record after
  `extra_tuple_adverb`'s debut. It is also the first confirmation that **an aggregate class can be
  caused by our own instructions**, which makes a prompt read a standing move alongside per-position
  checker reads. The 27 that survived are the same positions as before plus one new one; they are
  now a residue to read, not a licence to withdraw.
- **Per-unit yield held at 0.188 vs 0.193**, on a base the AH–AL rules had already stripped of its
  easy positions. Two rounds of decline (0.66 → 0.193) did not continue, which is the first evidence
  that the fall is a function of *what precedes a round* rather than of residue depth alone. One
  caveat against over-reading it: 55 of the 131 removed (42%) came from one class, so this is
  evidence for prompt repair specifically, not for pre-round work in general.
- **The elided-speech frame moved almost nothing** (`missing_tuple_nominal` −3, and all 36
  survivors are the same positions as before). **The appositive-adjective clause moved exactly
  nothing** (`extra_tuple_adjective` 13 → 13, position-identical). Both were prose added to a
  convention block with no instruction reaching the model *at* the flagged position — precisely the
  shape Phase 5w said does not move a class. Before touching either convention text again, they
  need `_HINT_PHRASING`/class-question work or a per-position read; a fourth round will not move
  them as they stand.

---

### 8. Rules AM–AT and the Inferno 11–15 Read (2026-08-15)

Per-position read of all **37** soft violations in Inferno 11–15. **963 → 888 (−75, −7.8%)**, zero
model calls; Inferno 11–15 itself 37 → 17. Full write-up, with the evidence line for each rule and
the variant measurements, in [`CORRECTIONS.md`](CORRECTIONS.md).

| rule | shape | moved |
|---|---|---:|
| **AM** | arguments Layer 4 stranded on a `cop`/`aux` never reach the lexical predicate | +7 |
| **AN** | a conjunct with an `orphan` child heads a *gapped clause*, not a predicate | −9 |
| **AJ′** | rule AJ's other two directions — gapping from a sibling conjunct, and up onto the head | −8 |
| **AP** | an apposition is the same argument named twice, and collapses like a conjunct | −15 |
| **AQ** | an argument citation landing on an `aux`/`cop` names its lexical head | −11 |
| **AR** | an oblique read off a *verbless* comparative clause is an adjunct (rule AK's `missing_arg` leg) | −8 |
| **AS** | a fused clitic's second `case` slot licenses the oblique Layer 4's single `expl` cannot record | −2 |
| **AT** | only a **verb** inherits a subject across `conj` | −22 |

Two findings worth carrying forward:

- **Four of the eight rules are in `derive_unit`, not the divergence check.** Every earlier batch
  produced acceptance rules — places the checker was *silent*. This one found the derivation
  **wrong**: it lost arguments Layer 4 records (AM), invented predicates out of gapping remnants
  (AN), and propagated subjects onto nominals (AT, the largest single mover in the batch and one no
  aggregate statistic pointed at). A per-position read is now known to test the derivation as well
  as the checker.
- **Rule AM raises the count on purpose** (−15 spurious `extra_arg`, +22 real `missing_arg`) — the
  same honest trade the Layer-4 rounds record. Its subject leg was measured separately and dropped
  (+11 on its own): the authority model already owns that slot.

Prompt side, unmeasured until the next round: two new subject classes (`missing_arg_subject`,
`extra_arg_subject`) covering 29% of the residue, `missing_tuple_nominal`'s own question, a
repeated-slot convention, and a `_fix_hint` branch that had been missing since round 3.

---

### 9. Rules AU–AY and the Inferno 16–20 Read (2026-08-15)

Per-position read of all **47** soft violations in Inferno 16–20. **888 → 834 (−54, −6.1%)**, zero
model calls, **zero newly-flagged positions**; Inferno 16–20 itself 47 → 31. Full write-up, with
the evidence line for each rule and the rule that was censused and dropped, in
[`CORRECTIONS.md`](CORRECTIONS.md).

| rule | shape | census | moved |
|---|---|---:|---:|
| **AU** | an adjective Layer 4 hangs `amod` on one of this predicate's own derived arguments is its secondary predicate | 19 | −17 |
| **AV** | the LLM names only the `aux`/`cop`; the lexical head is then "not proposed" | 4 | −4 |
| **AW** | rule AB's mirror: a reflexive clitic Layer 4 left as `obj`/`iobj` rather than `expl` | 9 | −9 |
| **AX** | an argument shared across an `xcomp` control edge, same role, either direction | 11 | −5 |
| **AY** | an `amod` adjective governing an argument of its own is a reduced relative, and predicates | 5 | −5 |

Three findings worth carrying forward:

- **Three of the five rules are *mirror legs* of rules the checker already had.** AV is
  `_aux_of_derived_predicate` looking the other way, AW is rule AB looking the other way, AY is
  `_elided_copula_nominal`'s adjective-phrase case. A labeling convention has two directions, and
  a rule written for one of them leaves the other reported — so **when a rule is written, check
  its mirror**. This is cheap to test and was worth 18 of the batch's 54.
- **Rule AU is the third leg of the secondary-predicate construction** (R takes it off the
  predicate as `advmod`, AA off an argument as `acl`, AU off an argument as `amod`) and is the
  batch's largest mover. `extra_arg` positions whose argument Layer 4 calls `amod` were the third
  largest bucket in the residue by deprel, after `obl` and `nsubj`.
- **A censused rule was dropped at population 12**: rule AN hands a gapped conjunct's remnants to
  the coordination head's slots, and the LLM sometimes lists none of them (inferno 19:114). Rule
  AN's assignment is right; the divergence is reading error, so it stays flagged. The census
  decided this, not the count.

Prompt side, unmeasured until the next round: nothing new — this batch's diagnoses were all
checker-side or upstream.

---

### 10. Rules AZ–BI and the Inferno 21–25 Read (2026-08-15)

Per-position read of all **44** soft violations in Inferno 21–25. **834 → 691 (−143, −17.1%)**,
zero model calls; Inferno 21–25 itself 44 → 16. The largest batch of the series. Full write-up,
with the evidence line for each rule, the two rules censused and dropped, and the honest trades
the upstream retags make, in [`CORRECTIONS.md`](CORRECTIONS.md).

| rule | shape | census | net |
|---|---|---:|---:|
| **AZ** | rule R's mirror leg: a depictive adjective on the predicate as a **bare `obl`** | 43 | −13 |
| **BA** | a predicate with **two** derived `subj` rows — the derivation has not decided | 99 | −41 |
| **BB** | rule V's coordination leg: *every* conjunct of a controlled infinitive's subject | — | −26 |
| **BC** | an `advmod` whose filler Layer 2 calls a **noun or pronoun** is an oblique | 117 | −14 |
| **BD** | rule AW's third deprel: a reflexive clitic Layer 4 left as `obl` | 35 | −10 |
| **BE** | `flat` collapses onto its head like `conj`/`appos` | 31 | (in BB) |
| **BF** | a `cop` edge pointed the wrong way: the non-verb in the `cop` slot is the `attr` | 11 | −8 |
| **BH** | rule M's mirror leg: the pro-drop ∅ subject rule M's relabelling leaves behind | — | −14 |
| **BI** | the accusative-and-infinitive's shared nominal, named from the matrix side | 10 | −10 |

Plus 20 Layer-4 rows and 5 Layer-2 rows (**−11 / +4** together), and `pytest` 311.

Three findings worth carrying forward:

- **When you write a rule, check the *plural* as well as the mirror.** Rules AZ, BD and BH are
  more mirror legs (37 positions), which the previous batch already taught. Rule BB is new in
  kind: rule V was correct in direction and simply **applied once to a shape that supplies
  several citations** — `_subj_arg` returns the first `subj` in the map, and a coordinate subject
  has three. Any rule that pops a single entry out of `g`/`d` should be asked what it does when
  the shape produces two.
- **Rule ordering is a defect surface, and only the diff shows it.** Rule BE alone measured
  −7/**+2**: `_apply_subj_authority` runs *before* `_collapse_coordination`, so the collapse
  rewrote citations rule V had refused onto the very position it accepts (paradiso 15:112).
  Testing rule V's candidate set through `_coordination_head` too took the pair to −23/0. A rule
  that tests a **raw** citation for membership must test the normalized one as well.
- **Two rules were censused and dropped, and one upstream refinement was measured and deferred.**
  The elided speech verb's `missing_tuple` (inferno 24:72) has a census of 164 and the LLM
  proposes nearly all of them, so the four omissions are reading error, not checker silence; the
  result-clause `ccomp` (22:84) has a census of 2. Restricting `dep.subject_agreement`'s
  *coordinated subject* exclusion to the number test — a coordination of nominals is third person
  however many members it has — was implemented and measured at **12 new `dep --check` soft
  violations**, all real Layer-4 questions, and reverted rather than landed against the standing
  0-soft invariant.

Prompt side, unmeasured until the next round: nothing new — every diagnosis was checker-side or
upstream.

---

## The Read Series — read the whole corpus first, then fix (decided 2026-08-15)

**The fourth `--fix` round is deferred until per-position reads have covered all 100 cantos in
5-canto batches.** Inferno 1–25 is done (batches 1, 1–3, 4–6, 7–10, 11–15, 16–20, 21–25);
**Inferno 26–30 is the next batch**, and the series then runs to Paradiso 33 before any round is
launched.

**Why read first.** Every batch so far has produced deterministic rules that remove violations at
**zero model cost** (AG: −43; AH–AL: −156; AM–AT: −75; AU–AY: −54; AZ–BI: −143), the 11–15 batch
showed the reads also find `derive_unit` itself to be wrong rather than merely silent, the 16–20
batch showed they find existing rules to be **half-written** — three of its five rules are the
mirror leg of a rule already in the checker — and the 21–25 batch found a rule that was neither
silent nor half-written but *singular where the shape is plural*, plus an ordering defect between
two rules that were each correct alone. A `--fix` round run before those rules
exist pays a model for positions a later rule would have taken for free, and worse: a round rewrites
the artifact, so a rule written afterwards is measured against a base the round already moved, and
the two effects can no longer be told apart. Reading the whole corpus first means the round runs
**once**, against a checker that is finished, with every prompt defect the reads found already in
place — and its per-class numbers then measure the prompt alone.

The cost of deferring is that the prompt-side work already queued (the subject branches,
`missing_tuple_nominal`'s question, `_CONV_REPEATED`) stays unmeasured until then. That is accepted:
those changes cannot regress anything while no round runs, and the reads will very likely add more
of them.

### Schedule — 16 batches, 602 positions at base 691

Inferno 1–25 (73 + 16 = 89 remaining positions) has been read and is **not** re-read; its residue
is reading error, and it is the fourth round's most direct sample afterwards.

| batch | soft | | batch | soft | | batch | soft |
|---|---:|---|---|---:|---|---|---:|
| **inferno 26–30** | **23** | | purgatorio 1–5 | 26 | | paradiso 1–5 | 46 |
| inferno 31–34 | 44 | | purgatorio 6–10 | 45 | | paradiso 6–10 | 25 |
| | | | purgatorio 11–15 | 41 | | paradiso 11–15 | 51 |
| | | | purgatorio 16–20 | 34 | | paradiso 16–20 | 36 |
| | | | purgatorio 21–25 | 50 | | paradiso 21–25 | 35 |
| | | | purgatorio 26–30 | 45 | | paradiso 26–30 | 45 |
| | | | purgatorio 31–33 | 30 | | paradiso 31–33 | 26 |

Per canto, get the current numbers with `uv run skel.py <canticle> --check -c <n>` from `skel/`;
the table is a base-691 snapshot and every landed rule shrinks the batches after it. The AZ–BI
rules cut every remaining batch by roughly a fifth, which is why re-measuring before a batch is
part of step 1.

### How to Read a Batch

The procedure below is what produced rules AG through BI. Steps 4–7 are the part that must not be
skipped: a rule that is not censused, measured, tested and written up is not a rule.

1. **List the batch.** `uv run skel.py <canticle> --check -c <n>` for each canto, from `skel/`.
   Record the per-canto counts and the class/role breakdown (`--stats`) before touching anything —
   this is the batch's baseline.
2. **Read every position, in parse-unit order,** with `uv run read.py <canticle> <canto> <line>`
   (`skel/read.py`, added 2026-08-15). It prints the unit's source, Layer-2 morphology + the `case`
   annex, Layer-4 deprels, Layer-3 NP spans, and both Layer-5 readings — the artifact rows and
   `derive_unit`'s — which is exactly the pair `--check` diffs. Never diagnose a position from the
   violation line alone.
3. **Give every position one of five verdicts.** The verdict decides where the fix goes, and
   mixing them up is how earlier phases wasted rounds:
   - **checker silent** — Layer 4 records something the derivation cannot express, and the reading
     is right → an *acceptance* rule in `_classify_divergence`;
   - **derivation wrong** — the derivation contradicts the tree it reads, or invents structure →
     a fix in `derive_unit` (rules AM, AN, AT are of this kind);
   - **upstream wrong** — Layer 2 or Layer 4 mis-tagged the line → an upstream retag, applied in
     the same session (see *Operating Principle 5*);
   - **prompt defect** — the corpus's own instructions caused the reading (`_CONV_ADVERB`'s
     omission licence was worth 82 positions) → Stage-2/convention work, which moves nothing until
     a round runs;
   - **genuine reading disagreement** — leave it flagged, and record the shape so a later batch can
     recognise a population.
4. **Census the shape corpus-wide before writing a rule.** A one-line script over
   `api.cantos()` counting the structural pattern (`orphan` deprels, argument children of a
   `cop`, `appos` on an argument, …). One instance is not a population; a rule whose census is
   0 is dropped, and several have been.
5. **Measure every rule on its own,** by full-corpus violation diff — not by the total alone:
   ```bash
   uv run skel.py inferno purgatorio paradiso --check | grep '\[tag\]' | sort > after.txt
   diff before.txt after.txt          # what it removed AND what it newly flagged
   ```
   Keep a rule when it is net negative, **or** when it makes the derivation provably more correct
   even at a cost (rule AM: −15/+22). Record such a trade explicitly in `CORRECTIONS.md`; the count
   is not the measure, the correctness of the parse is. Try variants and keep the numbers: rule
   AN's slot assignment was measured four ways.
6. **Pin every rule with a test, and mutation-check it.** Add to `tests/test_skel.py` a fixture
   built from the evidence line, one test that the rule fires and one that a near-miss still gets
   flagged. Then break the rule in the source and confirm the test fails — a test that passes with
   the rule removed pins nothing.
7. **Apply upstream retags with a gated script**, never by hand: assert the word at each
   `(line, token)` before rewriting the row, then re-run `morph`/`np`/`dep`/`case --check` (all must
   stay 0) and `pytest`. Watch CRLF hygiene (see the root PLAN's *Standing Disciplines*).
8. **Write it up in the same session**: the layer's `CORRECTIONS.md` for each layer touched, a
   numbered subsection in this file's *Phase 6 Implementation & Results*, the rule catalogue in
   [`README.md`](README.md), and the counts in both PLAN files. `CORRECTIONS.md` records
   corrections that were *applied* — see the root PLAN's *Standing Disciplines*.

### A Fourth `--fix` Round — Deferred, and What It Will Test

Round 3 confirmed that a class caused by the corpus's own prompt collapses when the prompt is
fixed (`missing_arg_adverb`, −66.3%), and that prose added to a convention block **without** an
instruction reaching the flagged position moves nothing. The queued prompt work puts three more
things on that scale, and the read series will add to the list:

1. **The subject branches.** `extra_arg subj` (147) and `missing_arg subj` (100) are the two
   largest buckets in the residue and had no class of their own. If `_CONV_SUBJECT`'s three
   diagnoses are the real causes, this should be the largest single-round drop since
   `extra_tuple_adverb`'s debut; if they are genuine reading disagreements, it will barely move
   and the buckets become read-work.
2. **`missing_tuple_nominal`'s rewritten question** (20 positions, position-identical across two
   rounds). This tests Phase 5w's law on a *question* rather than a convention — the class already
   had both a correct convention and a correct hint and still did not move.
3. **`_CONV_REPEATED`** against the `missing_arg obl` family (77 + 26 `obl:a` + 24 `obl:in` + …).

When the series finishes, re-measure the base, then run `make -C skel fix` 3-way parallel (the
user's job) and measure per *How to Measure a `--fix` Round* below.

---

## Active & Open Routes

Everything in this section is measured at base 691. These are shapes the reads have already named
but not settled; a batch that runs into one of them should fold it in rather than open a new route.

### Open Assistant-Side Routes

*(populations re-measured at base 691 after the Inferno 21–25 read)*

- **The 89 positions Inferno 1–25 still holds** are the read batches' own residue and are almost
  all reading error, which is what the prompt branches were built from. Do **not** re-read them
  during the series: they are the fourth round's most direct sample, and reading them again before
  it runs would only re-derive what the batches already recorded.
- **Check the mirror leg of every rule you write** (2026-08-15, from the Inferno 16–20 batch;
  three more legs in the 21–25 batch, worth 37 positions). When a rule accepts "the LLM names X
  where the derivation names Y", ask what happens when the derivation names X and the LLM names Y.
- **Check the *plural* too, and the rule's place in the pipeline** (2026-08-15, from the Inferno
  21–25 batch). Rule V popped one `subj` out of a map a coordinate subject fills three times, and
  the collapse that runs after it put the survivors back on the accepted position. Two questions
  for every rule: what does it do when the shape supplies **several** citations, and does it test
  a raw citation that a later normalization step will rewrite?
- **Subject vs. predicate nominal under a copula** (inferno 19:85 *«Nuovo Iasón sarà»*, 20:77
  *«ma Mencio si chiama»*): Layer 4 calls the single nominal `nsubj`, the LLM calls it the
  complement of an elided pro-drop subject, and the line does not decide. Feeds the
  `extra_arg subj ∅ (0,0)` bucket; census it there rather than as a route of its own.
- **A relative pronoun's subject named by its antecedent** (inferno 16:94 *«quel fiume c'ha
  proprio cammino»*): the derivation cites the relative `c'`, the LLM cites `fiume`. An acceptance
  rule keyed on `skel.antecedent` is plausible — **census it before writing it**.
- **Accusative-and-infinitive — CLOSED by rule BI (2026-08-15)**: censused at 10 (inferno 5:48,
  16:104, 22:31, 23:119, 26:78; purgatorio 18:24; paradiso 15:112, 19:39 …) and all 10 taken. The
  tree asserts both edges, so neither reading is wrong.
- **An argument named by its Layer-3 NP head against a clause the derivation cites by its clause
  head** (inferno 13:52, *«Ma dilli chi tu fosti»*): rule AI merges these only when the *role*
  matches, and here the LLM's `obj` on `chi` faces the derivation's `ccomp` on `fosti`. Measure how
  many `extra_arg` positions are NP-head-equivalent to a derived argument in a different role
  before extending AI — one instance is not a population.
- **`onde` is tagged five ways in Layer 2** (conjunction 56, pronoun 43, adverb 23, noun 11,
  relative pronoun 7). The noun rows are right; the 129 relative ones split three ways by nothing
  visible, and inferno 14:54's `missing_arg obl` is one consequence. A measured vocabulary pass,
  not a per-line edit — see [`../morph/CORRECTIONS.md`](../morph/CORRECTIONS.md).
- **Rule AN's two unresolved gapping clusters** (purgatorio 25:3, 27:108): 2-slot ambiguities that
  only word order settles, and Italian inverts word order freely. Left standing deliberately.

- **`missing_arg_adverb` residue**: the survivors of the `_CONV_ADVERB` repair. The licence
  that caused the class is gone, so this is now a per-position read — the first thing to establish
  is whether these are locative adverbs the model still omits or a different shape the branch is
  over-collecting. The class now also carries `_CONV_REPEATED`, so read it after the fourth round.
- **`missing_tuple_nominal` and `extra_tuple_adjective`** (`missing_tuple` 23 / `extra_tuple` 22
  at base 691): both untouched by round 3's
  prompt clauses and both position-identical to their pre-round sets. `missing_tuple_nominal` has
  now had its *question* rewritten (round 3 had only given it convention prose and a hint), which
  is the fourth round's cleanest test of Phase 5w's law; `extra_tuple_adjective` has had no such
  change, so read those positions rather than writing more prose.
- **`extra_arg subj` (111, of which `∅ (0,0)` 28 — rule BH took the half rule M had created) and `missing_arg subj` (60)**: the two largest
  buckets in the residue, now branched as `extra_arg_subject`/`missing_arg_subject` with
  `_CONV_SUBJECT` behind them. The Inferno 11–15 read supplied three diagnoses (postverbal
  subjects, proclitics read as subjects, coordination-shared subjects) but read only a handful of
  positions; the fourth round measures whether those three cover the buckets. What survives it is
  read-work — start with the `∅ (0,0)` half, where the derivation found a genuine overt subject,
  often long-distance (e.g. Inferno 9:20, where `alcun` at 21.4 is the subject of `incontra`).
- **`role_mismatch` `xcomp` vs `obl` (8, down from 21 after rule AZ) and `obj` ↔ `subj` (31 across both directions)**: the two
  dominant mismatch shapes. The `obj`/`subj` swap is a symmetric pair, which suggests one
  systematic cause rather than scattered slips. Inferno 9:41 and 9:72, both fixed in `dep/` this
  session, were instances — worth checking whether the rest are too.
- **Quoted speech attached as `parataxis` (Inferno 8:81)**: `«qui è l'intrata», gridò` — Layer 4
  hangs the quotation as `parataxis`, which is a clause-head deprel but not an argument deprel, so
  the derivation never makes it the verb's `ccomp` while the LLM (rightly) does. A
  `parataxis`→`ccomp` acceptance rule for verbs of speech is plausibly large; **measure the
  population before writing it.** Its neighbour, the *result* clause read as `ccomp`
  (`sì … che`, inferno 22:84), was censused at **2** and dropped.
- **`dep.subject_agreement`'s *coordinated subject* exclusion (12 positions)**: restricting it to
  the number test — a coordination of nominals is third person however many members it has — was
  implemented and measured, and takes `dep --check` from 0 to 12 soft. Each is a real Layer-4
  question (inferno 2:33, 8:28, 21:121, 25:36; purgatorio 4:102, 5:82, 10:62, 23:113, 29:37;
  paradiso 14:125, 19:12, 31:96); reverted rather than landed against the 0-soft invariant. It is
  what keeps rule AG from dropping the wrong inherited subject at inferno 24:125.
- **Depictive adjectives under bare `obl` — CLOSED by rule AZ (2026-08-15)**: censused at 43 and
  worth −13 as a role-mismatch acceptance rather than a derivation change (inferno 10:72
  `supin ricadde`, 21:46, 23:17, 24:115).
- **Relative `che`/`ch'`/`onde` tagged `conjunction` (247 tokens)**: unblocked only by an
  independent model read of the `case` annex over the 243 positions the retag would add. That is a
  build round, not an edit — see [`../morph/CORRECTIONS.md`](../morph/CORRECTIONS.md).
- **Attributive vs. Predicative Adjectives** (`extra_tuple` is 22 at base 691, down from 37 for the adjective subclass alone):
  - True reading disagreements with no `cop` edge (e.g., Inferno 2:109 *"non fur mai persone ratte / a far lor pro"*).
  - Round 3's appositive clause moved none of them — see above. Conduct a per-position read of the
    remainder before writing any checker rule.
- **`extra_arg_adjective` residue** (`extra_arg xcomp` is 38 at base 691; rule AU took the object/subject complements and rule BF the inverted copulas): two rounds have now each taken a couple of positions
  (−20.0%, then −3.9%), which is itself evidence that the residue is genuine reading disagreement
  rather than prompt weakness. Per-position read to settle it.
- **Adverbs Promoted to Predicates (2 `extra_tuple_adverb` remaining, down from 33)**:
  - Effectively closed by the Stage 2 micro-prompt. Read the final 2 positions to decide whether any residue warrants prompt tweaks or checker acceptance.
- **Stacked Prepositions in Layer 4 — CLOSED (2026-08-14)**: 161 multiword-preposition clusters
  normalized to the UD shape (opening word `case`→ nominal, later members `fixed`→ opening word),
  Layer 5 1094 → 1094 net zero; the old 14-role_mismatch count was Phase-5j-era and already
  absorbed by rules O/`prep_stack`. The standing obl-vs-obl residue is 3 genuine disagreements
  (inferno 14:103, purgatorio 32:156, paradiso 32:57). See
  [`../dep/CORRECTIONS.md`](../dep/CORRECTIONS.md) and [`CORRECTIONS.md`](CORRECTIONS.md).
  One deliberate leftover: the 40 adverb-prep clusters (`dentro a`, `dinanzi a`, `dietro a`,
  `intorno a`, `fuor di`, `infino al` …) Layer 2 tags `adverb` were excluded from the rewrite —
  a Layer-2/4 tension to decide separately if it ever matters.
- **`missing_arg obl` Sample Audit (68 standing, down from 128)**: the adverb bucket that dominated
  it is branched and largely repaired, and `_CONV_REPEATED` now addresses the duplicate-slot half
  of it. The read series will walk these positions in batch order anyway, so this is no longer a
  separate route — fold what it finds into the batch that covers it.

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
