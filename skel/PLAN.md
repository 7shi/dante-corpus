# skel — Layer 5 Plan: Deterministic Derivation & Targeted Micro-Fixes

## Status

- **Current State**: `make -C skel check` reports **0 hard, 963 soft** violations across all 100 cantos (down from 17,438 at the first full-corpus measurement), after the **third `--fix` round landed 2026-08-15** (1094 → 963, −131, −12.0%; 0 regressed / 0 newly flagged). See *Third User-Run `--fix` Round* below.
- **Other Layers**: `dep --check` **0 hard / 0 soft**. The subject-agreement rule's 18-position residue closed 2026-08-14 (Layer 5 1091 → 1094), and **Layer 4's stacked prepositions were normalized the same day** — 161 multiword-preposition clusters rewritten to one UD shape (opening word `case`, later members `fixed`), moving Layer 5 by zero (see [`CORRECTIONS.md`](CORRECTIONS.md) and [`../dep/CORRECTIONS.md`](../dep/CORRECTIONS.md)). `case --check` 0 hard, `np --check` 0/0, `morph --check` 0/0, `pytest` 268 passed.
- **Phase 5**: Complete and closed (reduced soft violations from 5,919 to 2,084). Full historical record, per-phase measurement tables, cost comparisons, and lessons learned are documented in [`PHASE5.md`](PHASE5.md).
- **Phase 6**: Rebuilt `--fix` into a three-stage driver (Stage 1 deterministic, Stage 2 class-specific POS-keyed micro-prompts, Stage 3 fallback). Three user-run rounds so far: **2011 → 1452 (−27.8%)**, **1409 → 1247 (−11.5%)**, **1094 → 963 (−12.0%)**.
- **Latest Work**:
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
  - Sends a concise 20–30 line prompt specific to the violation class (`extra_tuple_adverb`, `extra_tuple_adjective`, `extra_arg_adjective`, `missing_arg_adverb`, `role_mismatch`, `missing_arg`, `missing_tuple_nominal`).
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
- Exhaustive position-by-position reads of small canto batches (Inferno 1, 1–3, 4–6, 7–10, and next 11–15) uncover genuine checker silence (e.g., Rules V, W, X, Y–AF, AG, AH–AL) and upstream layer errors. The Inferno 7–10 read also found the reverse case: a defect in the *prompt* (`_CONV_ADVERB`'s omission licence) responsible for the single largest bucket in the residue, which no aggregate statistic had attributed to anything.

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

## Active & Open Routes

**Next up: the per-position read of Inferno 11–15** (37 soft at base 963; see the route below for
the per-canto and per-class breakdown). Everything in this section is measured at base 963.

**A fourth `--fix` round is not the next move.** Nothing new precedes it: the prompt work is now
measured, and what it left standing (below) is read-work, not prompt-work. A round launched today
would repeat round 3's classes at a lower rate.

### Open Assistant-Side Routes

*(populations re-measured at base 963 after the third round)*

- **`missing_arg_adverb` residue (28)**: the 27 survivors of the `_CONV_ADVERB` repair plus one new
  position. The licence that caused the class is gone, so this is now a per-position read — the
  first thing to establish is whether these are locative adverbs the model still omits or a
  different shape the branch is over-collecting.
- **`missing_tuple_nominal` (36) and `extra_tuple_adjective` (13)**: both untouched by round 3's
  prompt clauses and both position-identical to their pre-round sets. Do not re-write convention
  prose for either; read the positions, or move the instruction into `_HINT_PHRASING`/the class
  question where Phase 5w says it has to be to move a class.
- **`extra_arg subj` with `∅ (0,0)` — 52 standing, down from 69**: rule AH took the 14 that were
  AG-dropped inherited subjects (55 remained), and the rest fell to upstream corrections and round
  3. The residue is a different shape — the derivation found a genuine overt subject, often long-distance
  (e.g. Inferno 9:20, where `alcun` at 21.4 is the subject of `incontra`). Read a sample before
  writing anything; this is no longer one homogeneous bucket.
- **`role_mismatch` `xcomp` vs `obl` (21) and `obj` ↔ `subj` (31 across both directions)**: the two
  dominant mismatch shapes. The `obj`/`subj` swap is a symmetric pair, which suggests one
  systematic cause rather than scattered slips. Inferno 9:41 and 9:72, both fixed in `dep/` this
  session, were instances — worth checking whether the rest are too.
- **Quoted speech attached as `parataxis` (Inferno 8:81)**: `«qui è l'intrata», gridò` — Layer 4
  hangs the quotation as `parataxis`, which is a clause-head deprel but not an argument deprel, so
  the derivation never makes it the verb's `ccomp` while the LLM (rightly) does. A
  `parataxis`→`ccomp` acceptance rule for verbs of speech is plausibly large; **measure the
  population before writing it.**
- **Depictive adjectives under bare `obl` (Inferno 10:72 `supin ricadde`)**: candidate derivation
  rule "bare `obl` child with adjective POS and no `case` child → derive `attr`". Interacts with
  rule R and with the 48 `missing_arg` positions whose argument is an adjective; measure separately.
- **Relative `che`/`ch'`/`onde` tagged `conjunction` (247 tokens)**: unblocked only by an
  independent model read of the `case` annex over the 243 positions the retag would add. That is a
  build round, not an edit — see [`../morph/CORRECTIONS.md`](../morph/CORRECTIONS.md).
- **Attributive vs. Predicative Adjectives (13 `extra_tuple_adjective` remaining, down from 37)**:
  - True reading disagreements with no `cop` edge (e.g., Inferno 2:109 *"non fur mai persone ratte / a far lor pro"*).
  - Round 3's appositive clause moved none of them — see above. Conduct a per-position read of the
    remaining 13 before writing any checker rule.
- **`extra_arg_adjective` residue (49)**: two rounds have now each taken a couple of positions
  (−20.0%, then −3.9%), which is itself evidence that the residue is genuine reading disagreement
  rather than prompt weakness. Per-position read to settle it.
- **Adverbs Promoted to Predicates (3 `extra_tuple_adverb` remaining, down from 33)**:
  - Effectively closed by the Stage 2 micro-prompt. Read the final 3 positions to decide whether any residue warrants prompt tweaks or checker acceptance.
- **Stacked Prepositions in Layer 4 — CLOSED (2026-08-14)**: 161 multiword-preposition clusters
  normalized to the UD shape (opening word `case`→ nominal, later members `fixed`→ opening word),
  Layer 5 1094 → 1094 net zero; the old 14-role_mismatch count was Phase-5j-era and already
  absorbed by rules O/`prep_stack`. The standing obl-vs-obl residue is 3 genuine disagreements
  (inferno 14:103, purgatorio 32:156, paradiso 32:57). See
  [`../dep/CORRECTIONS.md`](../dep/CORRECTIONS.md) and [`CORRECTIONS.md`](CORRECTIONS.md).
  One deliberate leftover: the 40 adverb-prep clusters (`dentro a`, `dinanzi a`, `dietro a`,
  `intorno a`, `fuor di`, `infino al` …) Layer 2 tags `adverb` were excluded from the rewrite —
  a Layer-2/4 tension to decide separately if it ever matters.
- **Per-Position Read of Inferno 11–15 — the next session's task**: continue the audit discipline.
  Inferno 1, 1–3, 4–6 and 7–10 have each produced rules no aggregate statistic suggested. The batch
  holds **37 soft violations** at base 963 — coincidentally the same size as the 7–10 read:

  | canto | 11 | 12 | 13 | 14 | 15 |
  |---|---:|---:|---:|---:|---:|
  | soft | 8 | 5 | 4 | 13 | 7 |

  By class: `extra_arg` 17, `missing_arg` 11, `missing_tuple_nominal` 3, `extra_arg_adjective` 2,
  `role_mismatch` 2, `extra_tuple_adjective` 1, `missing_arg_adverb` 1. Note that four of the
  standing routes above (`missing_tuple_nominal`, `extra_tuple_adjective`, `extra_arg_adjective`,
  `missing_arg_adverb`) have positions inside this batch, so the read doubles as a sample of each.
  List them with `uv run skel.py inferno --check -c <n>` per canto.
- **`missing_arg obl` Sample Audit (77 standing, down from 128)**: the adverb bucket that dominated
  it is branched and largely repaired, so this is now measurable on its own terms. Sample the 77
  before writing anything.

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
