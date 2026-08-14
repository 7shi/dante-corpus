# skel — Layer 5 Plan: Deterministic Derivation & Targeted Micro-Fixes

## Status

- **Current State**: `make -C skel check` reports **0 hard, 1091 soft** violations across all 100 cantos (down from 17,438 at the first full-corpus measurement).
- **Other Layers**: `dep --check` 0 hard / 18 soft (verified standing residue), `case --check` 0 hard, `np --check` 0/0, `morph --check` 0/0, `pytest` 257 passed.
- **Phase 5**: Complete and closed (reduced soft violations from 5,919 to 2,084). Full historical record, per-phase measurement tables, cost comparisons, and lessons learned are documented in [`PHASE5.md`](PHASE5.md).
- **Phase 6**: Rebuilt `--fix` into a three-stage driver (Stage 1 deterministic, Stage 2 class-specific POS-keyed micro-prompts, Stage 3 fallback). Two user-run rounds so far: **2011 → 1452 (−27.8%)**, then **1409 → 1247 (−11.5%)**.
- **Latest Work**:
  - **Rule AG (Inferno 4–6 Read)**: Gated `conj` subject propagation on Layer-2 person/number agreement (`dep.subject_agreement` + `_finite_head_of`), scoring **1452 → 1409 soft (−43)** with zero model calls.
  - **Second `--fix` round (2026-08-14)**: First live pass of the `extra_arg_adjective` micro-prompt; **1409 → 1247 (−162)**, 0 regressed / 0 newly flagged. See *Second User-Run `--fix` Round* below.
  - **Rules AH–AL + Inferno 7–10 read (2026-08-14)**: Five deterministic rules, five Layer-2 mistags and eight Layer-4 retags, scoring **1247 → 1091 (−156, −12.5%)** with zero model calls. Plus three prompt defects fixed and one new Stage-2 class (`missing_arg_adverb`, population 82), which move nothing until the next `--fix` round. See *Rules AH–AL and the Inferno 7–10 Read* below and [`CORRECTIONS.md`](CORRECTIONS.md).

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
- Exhaustive position-by-position reads of small canto batches (Inferno 1, 1–3, 4–6, 7–10, and next 11–13) uncover genuine checker silence (e.g., Rules V, W, X, Y–AF, AG, AH–AL) and upstream layer errors. The Inferno 7–10 read also found the reverse case: a defect in the *prompt* (`_CONV_ADVERB`'s omission licence) responsible for the single largest bucket in the residue, which no aggregate statistic had attributed to anything.

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

Prompt side, moving nothing until the next `--fix` round: the `_CONV_ADVERB` omission licence
(82 positions), the addressee-less elided-speech frame (4 of the 37 read), and appositive
adjectives.

---

## Active & Open Routes

**The third `--fix` round is in flight.** Both previous rounds repeated the previous round's
pattern at a lower rate; this is the first time since Phase 6 opened that new checker rules *and* a
sharpened prompt *and* a new Stage-2 class all precede the round rather than follow it.

### In Flight — the third `--fix` round (started 2026-08-14, user-side)

`make -C skel fix`, 3-way parallel, against base **1091 soft** (commit `skel: rules AH-AL +
prompt work from the Inferno 7-10 read`). What is new since the second round:

| change | target class | population at base |
| --- | --- | ---: |
| new Stage-2 class `missing_arg_adverb` + `_CONV_ADVERB_ARG` | `missing_arg_adverb` | **82** |
| `_CONV_ADVERB` / `SYSTEM_PROMPT` omission-licence rewrite | same, and `missing_arg` generally | 429 total |
| addressee-less elided-speech frame (`_CONV_VERBLESS`, `SYSTEM_PROMPT`, hint) | `missing_tuple_nominal` | 39 |
| appositive-adjective clause (`_CONV_ADJECTIVE`, `SYSTEM_PROMPT`) | `extra_tuple_adjective` | 13 |

**When the round lands**, measure per *How to Measure a `--fix` Round* below and record the
subclass table here, as for rounds 1 and 2. Two things this round is specifically a test of:

- **`missing_arg_adverb` is the first class whose population was traced to a defect in the
  corpus's own prompt** rather than to the model — `_CONV_ADVERB` ended with "or it is left out",
  licensing exactly the 82 omissions the checker was flagging. A large drop confirms the
  diagnosis; a flat result means the rewrite did not reach the model at the flagged position, and
  Phase 5w's finding applies (a prose rule already in the prompt does not move its class unless an
  instruction also reaches the model *at* the position) — re-read `_HINT_PHRASING` and the class
  question before touching the convention text again.
- **Per-unit yield against 0.66 (round 1) and 0.193 (round 2).** Both previous rounds repeated the
  previous round's pattern at a lower rate. This is the first round preceded by new checker rules
  *and* a sharpened prompt *and* a new class, so a yield at or above round 2's would be the first
  evidence that the decline is a function of what precedes a round rather than of residue depth.

### Open Assistant-Side Routes
- **`extra_arg subj` with `∅ (0,0)` — 54 standing, down from 69**: rule AH took the 14 that were
  AG-dropped inherited subjects (55 remained), and one more fell to the upstream corrections. The
  residue is a different shape — the derivation found a genuine overt subject, often long-distance
  (e.g. Inferno 9:20, where `alcun` at 21.4 is the subject of `incontra`). Read a sample before
  writing anything; this is no longer one homogeneous bucket.
- **`role_mismatch` `xcomp` vs `obl` (21) and `obj` ↔ `subj` (36 across both directions)**: the two
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
  - Target: Conduct a per-position read of the remaining 13 before writing any checker rule.
- **`extra_arg_adjective` residue (52)**: per-position read to separate prompt weakness from genuine
  reading disagreement — see the reading of its −20.0% above.
- **Adverbs Promoted to Predicates (4 `extra_tuple_adverb` remaining, down from 33)**:
  - Effectively closed by the Stage 2 micro-prompt. Read the final 4 positions to decide whether any residue warrants prompt tweaks or checker acceptance.
- **Stacked Prepositions in Layer 4 (14 `role_mismatch` / 18 unattached)**:
  - Where Layer 4 inconsistently writes stacked prepositions (flat vs. chained, e.g., *"in su"*). Requires a `dep/` normalization pass.
- **Per-Position Read of Inferno 11–13**: continue the audit discipline. Inferno 1, 1–3, 4–6 and
  7–10 have each produced rules no aggregate statistic suggested.
- **`missing_arg obl` Sample Audit**:
  - 82 of the 128 bare-`obl` omissions were the adverb bucket now branched as `missing_arg_adverb`.
    Re-measure the remainder after the next `--fix` round rather than branching twice.

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
