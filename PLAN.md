# Plan: a shared grammatical-analysis stack in the corpus

## Handoff (2026-08-16) — resume here

> **The fourth `--fix` round was run by the user ahead of the read series: 650 → 541 soft (−109,
> −16.8%), 0 hard, `pytest` 326.** Units 443 → 388 (55 cleared, 38 improved, **0 regressed, 0
> newly flagged**); per-unit yield **0.246**, the first rise of the series (0.66 → 0.193 → 0.188 →
> 0.246). It emptied the queued prompt work and decided it, mostly negative:
> 1. **The subject branches are not a prompt problem.** `extra_arg_subject` −12.7% and
>    `missing_arg_subject` −10.0% is the round average, not the large drop `_CONV_SUBJECT`'s three
>    diagnoses predicted. By the test's own stated branch, the residue's two largest buckets — 96
>    `extra_arg subj` (22 of them ∅ (0,0)) and 54 `missing_arg subj` — **become read-work**.
> 2. **Neither is `missing_tuple_nominal`.** Its rewritten *question* moved it 18 → 16, after a
>    convention and a hint had each moved it by single digits. Phase 5w's law is not specific to
>    convention prose: a class of genuine reading disagreements moves for no prompt surface.
> 3. **`_CONV_REPEATED` worked.** `missing_arg` −28.3% carried −49 of the round's −109, while its
>    branched adverb sibling fell only 12.5% — the attribution is the repeated-slot convention.
> 4. **`extra_tuple_adjective` 7 → 0**, unqueued. Rules AU/AY/AZ took it 13 → 7 and the round took
>    the rest; a route that was waiting for a read closes without one.
>
> **The cost of running it early is real and not recoverable**: a round rewrites the artifact, so
> every rule the fifteen unread batches produce is now measured against a base this round moved,
> and the rule's effect and the round's cannot be separated. What was bought is that the prompt
> queue is answered now, and two of three answers convert prompt work into read work. See
> [`skel/PLAN.md`](skel/PLAN.md) §12.
>
> **The next session's task is unchanged: the per-position read of Inferno 31–34 — 37 soft
> violations at base 541.** Start a fresh session, list them with
> `uv run skel.py inferno --check -c <n>` from `skel/`, and read each one with
> `uv run read.py inferno <canto> <line>` (it prints all five layers plus both Layer-5 readings for
> the position's whole parse unit). The read series then runs to Paradiso 33 — fifteen batches,
> 469 positions, schedule rebased to 541 in [`skel/PLAN.md`](skel/PLAN.md)'s *The Read Series*.
> **Re-measure the batch first**; every landed rule shrinks the batches after it.
>
> **A fifth `--fix` round has nothing to test yet.** The prompt queue is empty, and checker rules
> are measured by violation diff at zero model cost. Wait until the series finishes *and* has
> produced new prompt-side diagnoses — the standing form of the rule is: **do not run a round while
> checker rules are being written against the base it would move.**
>
> **The per-batch procedure is written down** — eight steps, in [`skel/PLAN.md`](skel/PLAN.md)'s
> *How to Read a Batch*. Follow it rather than improvising: every position gets one of five
> verdicts (checker silent / derivation wrong / upstream wrong / prompt defect / genuine
> disagreement), each of which sends the fix somewhere different; no rule is written before its
> shape is censused corpus-wide; each rule is measured alone by full-corpus violation **diff**
> (not by the total), pinned by a mutation-checked test, and written up in the same session.

**Layer 5 is operating under Phase 6 with 0 hard / 541 soft violations.**
Checks: `dep --check` **0 hard / 0 soft** (the subject-agreement rule's 18-position residue closed
2026-08-14; 16 + 25 + 20 + 10 further rows corrected 2026-08-15), `case --check` 0 hard,
`skel --check` 0 hard/**541** soft, `np --check` 0/0, `morph --check` 0/0 (3 + 5 + 1 rows
corrected 2026-08-15), `pytest` **326** passed. The fourth `--fix` round (2026-08-16) touched
`skel/*.tsv` only; no other layer moved.

**Layer 4's stacked prepositions are normalized (2026-08-14).** 161 multiword-preposition
clusters (196 rows, 74 files) rewritten to the UD convention — opening word `case`→ nominal,
later members `fixed`→ opening word — closing the flat/chained shape lottery. Layer 5 measured
**1094 → 1094, net zero** (0 units cleared / newly flagged; one derived lemma flip at
purgatorio 31:26 by design); rules O/`prep_stack` read the normalized shape via a
`fixed`-under-`case` lemma aggregation in `dante_corpus/skel.py`. The old "14 role_mismatch /
18 unattached" note was a Phase-5j-era count already absorbed by those rules. See
[`dep/CORRECTIONS.md`](dep/CORRECTIONS.md) and [`skel/CORRECTIONS.md`](skel/CORRECTIONS.md).

**Layer 4's agreement residue is closed (2026-08-14).** All 18 were re-read: one was a real
mis-attachment (purgatorio 26:147, Occitan `sovenha vos`), ten were taken by six new exclusions in
`dep.subject_agreement` — each measured corpus-wide first, and none of them touching a pair the
rule calls `"agree"`, so Layer 5's Tier-B repairs are untouched — and seven by hand-verified
`AD_SENSUM`/`FOREIGN` flags in the Layer-2 `note` column, the `NO_NP`/`CONT_NEXT` mechanism. Layer
5 rose **1091 → 1094 (+3)**, all three individually attributable (rule AG at inferno 6:87, and the
two obliques the purgatorio 26:147 re-parse gives `sovenha`) — the same honest trade earlier
Layer-4 rounds recorded. See [`dep/CORRECTIONS.md`](dep/CORRECTIONS.md).

### Current State & Architecture Summary

- **Layer 5 (Phase 6)**: `--fix` runs in three stages: Stage 1 (deterministic auto-repairs, −73), Stage 2 (twelve class-specific micro-prompts, keyed by POS, by role, or by class alone), and Stage 3 (fallback whole-unit regeneration). Four user-run rounds so far: **2011 → 1452 (−559)**, **1409 → 1247 (−162)**, **1094 → 963 (−131)** and **650 → 541 (−109)**.
  - **Detailed Phase 6 Plan**: For Phase 6 operating principles, architectural details, active routes, and measurement procedures, see [`skel/PLAN.md`](skel/PLAN.md).
- **Latest Improvements**:
  - **Fourth `--fix` round (2026-08-16)**: **650 → 541 (−109, −16.8%)**; 443 → 388 flagged parse
    units (55 cleared, 38 improved, **0 regressed, 0 newly flagged**); per-unit yield **0.246**,
    the first rise of the series. Run by the user ahead of the read series it had been deferred
    behind. It decided all three queued prompt questions: the subject branches (−12.7% / −10.0%)
    and `missing_tuple_nominal`'s rewritten question (18 → 16) both **negative**, which turns the
    residue's two largest buckets into read-work, and `_CONV_REPEATED` **positive**
    (`missing_arg` −28.3%, −49 of the round). `extra_tuple_adjective` reached **0**. The cost of
    running early: the fifteen unread batches' rules are now measured against a base a round has
    moved. Full subclass table in [`skel/PLAN.md`](skel/PLAN.md) §12.
  - **Rules BJ–BN (Inferno 26–30 read, 2026-08-15)**: Per-position read of all 23 soft violations in
    Inferno 26–30 produced five deterministic rules — BJ (the adverb-preposition cluster names one
    oblique from either of its two words, −21), BK (rule AR's other marker: `che` opens the second
    term of a comparison, −4), BL (rule AR's other order: `sì come` is one word, −1), BM (an
    oblique whose filler Layer 2 calls a conjunction is the clause's connective, −11), BN (a
    conjunction in a clause-head deprel with no arguments is not an elided predicate, ±0) — plus
    three legs added to rules already in the checker (BI′ the `obj`-attached infinitive, AN′ the
    gapped comparison under `advcl`, AQ′ the `cop` merge applied to the membership check), 10
    Layer-4 rows and 1 Layer-2 row. **691 → 650 (−41, −5.9%)** with zero model calls; Inferno
    26–30 itself 23 → 11. One rule was censused and dropped (an `iobj` ↔ `obl:a` equivalence,
    population 0). See [`skel/CORRECTIONS.md`](skel/CORRECTIONS.md),
    [`dep/CORRECTIONS.md`](dep/CORRECTIONS.md), [`morph/CORRECTIONS.md`](morph/CORRECTIONS.md).
  - **Rules AZ–BI (Inferno 21–25 read, 2026-08-15)**: Per-position read of all 44 soft violations in
    Inferno 21–25 produced nine deterministic rules — AZ (rule R's mirror: a depictive adjective
    Layer 4 hung on the predicate as a bare `obl`, −13), BA (a predicate with two derived subjects
    has not decided between them, −41), BB (rule V's coordination leg, with rule BE, −26), BC (an
    `advmod` whose filler Layer 2 calls a noun or pronoun is an oblique, −14), BD (rule AW's third
    deprel, −10), BE (`flat` collapses like `conj`), BF (an inverted `cop` edge, −8), BH (rule M's
    mirror: the pro-drop ∅ subject its relabelling leaves behind, −14), BI (the
    accusative-and-infinitive's shared nominal, −10) — plus 20 Layer-4 rows and 5 Layer-2 rows.
    **834 → 691 (−143, −17.1%)** with zero model calls; Inferno 21–25 itself 44 → 16, the largest
    batch of the series. Two rules were censused and dropped and one `dep.subject_agreement`
    refinement was measured (12 new Layer-4 soft violations) and deferred. See
    [`skel/CORRECTIONS.md`](skel/CORRECTIONS.md), [`dep/CORRECTIONS.md`](dep/CORRECTIONS.md),
    [`morph/CORRECTIONS.md`](morph/CORRECTIONS.md).
  - **Rules AU–AY (Inferno 16–20 read, 2026-08-15)**: Per-position read of all 47 soft violations in
    Inferno 16–20 produced five deterministic rules — AU (an `amod` adjective over one of the
    predicate's own arguments is its secondary predicate, −17), AV (the LLM naming only an
    `aux`/`cop` as the predicate), AW (rule AB's mirror: a reflexive clitic Layer 4 left as `obj`),
    AX (an argument shared across an `xcomp` control edge), AY (an `amod` adjective governing an
    argument of its own predicates) — plus 25 Layer-4 rows and 1 Layer-2 row retagged.
    **888 → 834 (−54, −6.1%)** with zero model calls and **zero newly-flagged positions**; Inferno
    16–20 itself 47 → 31. Three of the five are mirror legs of rules already in the checker, which
    is the batch's transferable finding; one censused rule was measured and dropped at population
    12. See [`skel/CORRECTIONS.md`](skel/CORRECTIONS.md), [`dep/CORRECTIONS.md`](dep/CORRECTIONS.md),
    [`morph/CORRECTIONS.md`](morph/CORRECTIONS.md).
  - **Rules AM–AT (Inferno 11–15 read, 2026-08-15)**: Per-position read of all 37 soft violations in
    Inferno 11–15 produced eight deterministic rules — AM (arguments stranded on a `cop`/`aux`),
    AN (`orphan`-marked gapped coordination), AJ′ (rule AJ's sibling and downward directions),
    AP (apposition collapsed like coordination), AQ (a citation on an auxiliary names its lexical
    head), AR (verbless comparative clauses), AS (a fused clitic's second `case` slot), AT (only a
    verb inherits a subject across `conj`) — plus 16 Layer-4 rows and 2 Layer-2 rows retagged.
    **963 → 888 (−75, −7.8%)** with zero model calls; Inferno 11–15 itself 37 → 17. Four of the
    eight are in `derive_unit` itself, the first batch to find the derivation wrong rather than
    silent. Prompt side, unmeasured: the first subject-slot Stage-2 classes and a rewritten
    `missing_tuple_nominal` question. See [`skel/CORRECTIONS.md`](skel/CORRECTIONS.md),
    [`dep/CORRECTIONS.md`](dep/CORRECTIONS.md), [`morph/CORRECTIONS.md`](morph/CORRECTIONS.md).
  - **Third `--fix` round (2026-08-15)**: **1094 → 963 (−131, −12.0%)**; 696 → 618 flagged parse
    units (78 cleared, 42 improved, **0 regressed, 0 newly flagged**); per-unit yield 0.188, flat
    against round 2's 0.193. `missing_arg_adverb` **83 → 28 (−66.3%)** carried 42% of the round on
    its own and confirmed that the class was caused by the corpus's own prompt; the two other
    prompt clauses tested moved nothing. Full subclass table in [`skel/PLAN.md`](skel/PLAN.md).
  - **Layer-4 stacked-preposition normalization (2026-08-14)**: 161 multiword-preposition clusters rewritten to one UD shape (opening word `case`, later members `fixed`), closing the flat/chained lottery. Layer 5: **1094 → 1094, net zero** by design; `skel.py`'s lemma aggregation reads the new shape (rules O/`prep_stack` unchanged in behaviour). See [`dep/CORRECTIONS.md`](dep/CORRECTIONS.md), [`skel/CORRECTIONS.md`](skel/CORRECTIONS.md).
  - **Rules AH–AL (Inferno 7–10 read, 2026-08-14)**: Per-position read of all 37 soft violations in Inferno 7–10 produced five deterministic checker rules — AH (rule AG's second leg), AI (Layer-3 NP head vs Layer-4 attachment), AJ (coordination gapping of objects and datives), AK (comparative `come`), AL (dual-role fused clitics) — plus 5 Layer-2 mistags and 17 Layer-4 rows retagged. **1247 → 1091 (−156, −12.5%)** with zero model calls; Inferno 7–10 itself 37 → 17. Two candidates were measured and dropped, including a 247-token relative-`che` retag the `case` annex blocks. See [`skel/CORRECTIONS.md`](skel/CORRECTIONS.md).
  - **Prompt work in the same read**: `_CONV_ADVERB`'s "or it is left out" clause was found responsible for **82 `missing_arg` positions whose argument is a locative adverb** — the largest unbranched bucket in the residue. Fixed prompt-side, with a new Stage-2 class `missing_arg_adverb`; also the addressee-less elided-speech frame (`E io: «…»`, 4 of the 37) and appositive adjectives. **Round 3 measured all three: the adverb licence was the real defect (−66.3%), the other two moved nothing.**
  - **Rule AG (Inferno 4–6 read)**: Gated `conj` subject propagation on Layer-2 person/number agreement (`dep.subject_agreement` + `_finite_head_of`), reducing soft violations **1452 → 1409 (−43)** with zero model calls.
  - **Second `--fix` round (2026-08-14)**: First live pass of the `extra_arg_adjective` micro-prompt. **1409 → 1247 (−162, −11.5%)**; 841 → 765 flagged parse units (76 cleared, 62 improved, **0 regressed, 0 newly flagged**); per-unit yield 0.193, under half the first round's rate. Full subclass table in [`skel/PLAN.md`](skel/PLAN.md).
- **Phase 5 Retrospective**: Complete and closed (5,919 → 2,084). Established the flat yield ceiling of monolithic regeneration and the provenance law of yield. For full details, measurement tables, and lessons learned, see [`skel/PHASE5.md`](skel/PHASE5.md).

### Standing Disciplines

- **A silent `--check` pass, closed (2026-08-07)**: Found while re-measuring from a `git worktree` (where `src/` is unbuilt because per-canticle source directories are generated, not tracked). `api.cantos()` now raises `FileNotFoundError` if the directory is missing, preventing checks from silently returning `0 hard, 0 soft`. `tests/test_api.py` pins this behaviour.
- **How `CORRECTIONS.md` is used**: `*/CORRECTIONS.md` records **hand-applied corrections**, not a place to log "found a problem, leaving it." If a review turns up a clear, decidable error, **fix it in the same session** and record what was fixed and why. The only legitimate "left alone" write-ups are ones with a genuine structural reason the text itself doesn't decide (e.g., free relatives, accusative-and-infinitive, Latin quotations, etc.).
  - **A `--fix` round is not a correction and is never written there** (2026-08-16). It is LLM regeneration of the artifact, decided by the acceptance gate rather than by a person reading a line. Round measurements belong in [`skel/PLAN.md`](skel/PLAN.md)'s *Phase 6 Implementation & Results* and in this file's *Latest Improvements*. What does go in `CORRECTIONS.md` is what a human decided: upstream retags, gated-script rewrites, checker and derivation rules, and the shapes deliberately left standing.
- **CRLF hygiene**: Writing TSVs with Python's `csv` module and `newline=''` defaults to `\r\n`. Ensure `\n`-only line endings (`sed -i 's/\r$//'` or `Path.write_text` splitting/joining on `\n`) before diffing or committing.
- **Measure a checker rule by violation diff, never by the total** (2026-08-15): keep the sorted `--check` output before and after and diff it, so what a rule *newly flags* is visible next to what it removes. Two rules this session looked neutral or positive on the total and were only decidable from the diff — rule AM (−15/+22, kept: the derivation is now right) and its subject leg (dropped). A rule may be kept when it raises the count, if it makes the parse provably more correct; record that trade explicitly.
- **Census a shape before writing a rule for it** (2026-08-15): count the structural pattern over all 100 cantos first. One evidence line is not a population, and several candidate rules have been dropped at census — with a population of 0, and once (gapped-clause remnants, Inferno 16–20 batch) with a population of 12 that the census itself showed was reading error rather than checker silence.
- **When you write a checker rule, check its mirror leg** (2026-08-15): a labeling convention has two directions, and a rule that accepts "the LLM names X where the derivation names Y" leaves the reverse reported. Three of the Inferno 16–20 batch's five rules were mirror legs of rules already in the checker (AV, AW, AY), worth 18 positions between them.
- **Mutation-check a new rule's test**: break the rule in the source and confirm the test fails. A test that still passes with the rule removed pins nothing.
- **Editing frozen TSVs**: never by hand. Use a gated script that asserts the expected word at each `(line, token)` before rewriting the row, then re-run every layer's `--check` and `pytest`.

### Next Steps & Open Routes

- **The read series is the standing task**: per-position reads of all 100 cantos in 5-canto batches, **Inferno 31–34 next** (37 soft at base 541), running to Paradiso 33. Fifteen batches, 469 positions; schedule, reasoning and the eight-step per-batch procedure in [`skel/PLAN.md`](skel/PLAN.md)'s *The Read Series* / *How to Read a Batch*. Tool: `skel/read.py`.
- **A fifth `--fix` round has nothing queued to test** (`make -C skel fix`, run 3-way parallel — the user's to run). The fourth round emptied the prompt queue on 2026-08-16, and checker rules are measured by violation diff at zero model cost, so a round now would measure nothing the diff does not. Wait until the series finishes *and* has produced new prompt-side diagnoses. See [`skel/PLAN.md`](skel/PLAN.md)'s *A Fifth `--fix` Round*.
- **Inferno 1–30's 72 standing positions** are the read batches' residue with a `--fix` round now over them — the most direct sample of what a round leaves behind. Not urgent: the fifteen unread batches come first.
- **Other Assistant-Side Tasks** (populations at base 541; folded into the batch that covers them):
  - **Check the mirror leg of every new rule** — the Inferno 16–20 batch's finding, worth 18 positions there and 37 more in the 21–25 batch.
  - **Check the *plural*, and the rule's place in the pipeline** — the Inferno 21–25 batch's finding: rule V was written to pop one citation where a coordinate subject supplies three, and the collapse that runs after it put the survivors back on the accepted position.
  - Per-position read of the `missing_arg_adverb` residue (**21**) — what the `_CONV_ADVERB` and `_CONV_REPEATED` repairs left standing.
  - Read `missing_tuple_nominal` (**16**; `missing_tuple` **18** total): a convention, a hint and a rewritten question have each moved it by single digits, so it is genuine reading disagreement until a read says otherwise. Its old sibling `extra_tuple_adjective` is **closed at 0**.
  - Measure the population of a `parataxis`→`ccomp` acceptance rule for quoted speech under verbs of speech (Inferno 8:81) before writing it. Its neighbour, the `sì … che` result clause read as `ccomp`, was censused at **2** and dropped.
  - Census a relative-pronoun ↔ antecedent argument-identity rule (Inferno 16:94) before writing it.
  - Ask which checks run *before* every acceptance rule — the Inferno 26–30 batch's finding: rule AQ was complete inside `_classify_divergence` and absent from the membership check that runs first.
  - **Read `extra_arg subj` (**96**, of which ∅ (0,0) **22**) and `missing_arg subj` (**54**)** — the residue's two largest buckets. Round 4 measured `_CONV_SUBJECT`'s three diagnoses at the round average, which by the test's own branch makes these read-work rather than prompt-work. Start with the ∅ (0,0) half.
  - Audit remaining `extra_arg_adjective` positions (**19**; `extra_arg xcomp` is **35**) — three rounds have each taken only a couple, which is itself evidence of genuine disagreement.
  - Sample `missing_arg obl` (**40**, down from 128; `_CONV_REPEATED` took the duplicate-slot half in round 4).
  - Clear the 12 Layer-4 positions that block the measured `dep.subject_agreement` *coordinated subject* refinement — see [`dep/CORRECTIONS.md`](dep/CORRECTIONS.md).
- See [`skel/PLAN.md`](skel/PLAN.md) for full descriptions of each route and testing workflows.

## Status

**All five layers are implemented, built for all 100 cantos, and merged to `main`.** Layer 5's
checker was refined through Phases 0-5r, rules V through BN, and Phase 6's restructuring plus four `--fix` rounds, bringing its soft residue to **541**
(down from 17438 at the first full-corpus measurement). See [`skel/PHASE5.md`](skel/PHASE5.md) for the full Phase 5
history, [`skel/PLAN.md`](skel/PLAN.md) for the closing positions, and *The layers* below and [`skel/README.md`](skel/README.md) for the design and current status.

**The pronoun case annex is complete and closed (2026-08-02).** It is a permanent Layer-2 sibling
extension, `case/`, on the same footing as `np/`, `dep/` and `skel/` relative to `morph/` — not a
new `morph/*.tsv` column, decided at the annex's close after two budgeted blind-regeneration
rounds were measured and rejected against a verdict rule fixed in advance. See
[`case/README.md`](case/README.md) for the design and current status and
[`case/CORRECTIONS.md`](case/CORRECTIONS.md) for the full measurement history, including *Step 5 —
the merge decision*.

**The open route is the read series**: per-position reads of all 100 cantos in 5-canto batches, Inferno 31–34 next, running to Paradiso 33 before the fourth `--fix` round (decided 2026-08-15 — see *Next Steps & Open Routes* above and [`skel/PLAN.md`](skel/PLAN.md)). All five layers plus the case extension are implemented, built for all 100
cantos and merged to `main`. Detailed open routes and measurement instructions live in [`skel/PLAN.md`](skel/PLAN.md).

- **Layer 1 — Tokens**: implemented (`dante_corpus/tokenizer.py`, served via `Line.tokens`).
- **Layer 2 — Morphology + lemma**: implemented; see [`morph/README.md`](morph/README.md).
  Artifacts are built for all 100 cantos. Its pronoun-case feature is served separately, as the
  permanent Layer-2 sibling extension `case/` — see [`case/README.md`](case/README.md).
- **Layer 3 — Noun phrases**: implemented; see [`np/README.md`](np/README.md). Build
  driver `np/np.py`, served via `Canto.np()` and `dante-corpus text np`. Artifacts generated for
  all 100 cantos. `--check` reports **0 hard / 0 soft** — see
  [`np/README.md`](np/README.md)'s *Check* section and [`np/CORRECTIONS.md`](np/CORRECTIONS.md).
- **Layer 4 — Dependency / grammatical role**: implemented and complete; see
  [`dep/README.md`](dep/README.md). Build driver `dep/dep.py`, served via `Canto.dep()` and
  `dante-corpus text dep` (with `text np` gaining a derived `role=` per noun phrase). Artifacts
  built for all 100 cantos; `--check` reports **0 hard / 0 soft** violations — every class at 0,
  including the subject-agreement rule, whose 18-position residue was closed 2026-08-14 — see
  [`dep/README.md`](dep/README.md)'s *Check* section and
  [`dep/CORRECTIONS.md`](dep/CORRECTIONS.md) for the full correction history.
- **Layer 5 — skeleton**: implemented, all 100 cantos built, checker refined through Phases 0-5r
  — the four mechanical phases (normalization, authority model, `--repair`,
  double-listing/elided-copula whitelist) plus Phase 5's rule series, 5r's rule U, which reads the
  `case` annex as a third opinion on a disputed argument role, rule V, which supplies the
  control/participial subject of a non-finite predicate, the Y-AF series, which closes eight
  further shapes where the derivation was silent rather than disagreeing, and the AG-BN series
  from the Inferno 4-6, 7-10, 11-15, 16-20, 21-25 and 26-30 per-position reads; see
  [`skel/README.md`](skel/README.md). `dante_corpus/skel.py` (dataclasses, role
  vocabulary, deterministic derivation, table parsing, validation, TSV I/O, serve-time joins),
  `dante_corpus/hashes.py` (content-hash versioning, all layers), `Canto.skel()`/`Canto.hashes()`
  in `api.py`, `dante-corpus text skel`/`dante-corpus hash` in `cli.py`, `skel/skel.py` (LLM
  build driver, mirrors `dep/dep.py`, plus `--stats`/`--repair` modes), `skel/read.py` (the audit
  series' read tool: all five layers plus both Layer-5 readings for one parse unit). `--check` across all
  three canticles reports **0 hard, 541 soft** (down from 17438 at the first full-corpus
  measurement) — see [`skel/README.md`](skel/README.md)'s *Check* section and
  [`skel/CORRECTIONS.md`](skel/CORRECTIONS.md) for the full correction history, including the
  case annex's contribution to that count. Phase 5 (see [`skel/PHASE5.md`](skel/PHASE5.md)) is
  **complete**: its measured finding was that monolithic `--fix` yields a flat ~0.09-0.11 violations per
  LLM call on static residue, leading to the adoption of deterministic checker rules and upstream corrections.
  **Phase 6 (2026-08-12) restructured `--fix` itself** into deterministic repairs (Stage 1), class-specific
  POS-keyed micro-prompts (Stage 2), and fallback whole-unit regeneration (Stage 3). `--fix` rounds are
  **LLM-regeneration work the user runs themselves** (`make -C skel fix`, run 3-way parallel); checker-side
  and audit work is the assistant's.

`grammar-stack-plan` was merged into `main` (fast-forward) and pushed; Layers 1–4 and their
artifacts now live on `main`.

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

Five layers, each a function of the source text. All five are implemented and built for all 100
cantos. Examples use *Inferno* I.1–6.

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

**Pronoun case** is served as a Layer-2 morphological feature — the one this layer's own columns
omit — but held in its own permanent sibling directory rather than a `morph/*.tsv` column, so no
existing artifact hash moves. See [`case/README.md`](case/README.md) for the design, scope, and
vocabulary, and [`case/CORRECTIONS.md`](case/CORRECTIONS.md) for why a sibling directory over a
merged column.

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

### Layer 5 — Predicate-argument skeleton *(implemented — see [`skel/README.md`](skel/README.md))*

Predicate ↔ argument tuples binding layers 2–4 into bare propositions, citing **token
positions**, not raw text or lemmas — `[la diritta via]` = subject of `smarrita`; `che` (l.6) =
relative pronoun, subject of `rinova`, antecedent `[esta selva …]` (derived at serve time via
`skel.antecedent`, not stored). This is the *raw* skeleton only: **no semantic frame, no
coreference, no vocabulary normalization.** Role labels are **UD-derived**
(`subj`/`obj`/`iobj`/`attr`/`xcomp`/`ccomp`/`obl:<preposition lemma>`), not semantic, so they
stay directly comparable with the deterministic derivation below and the vocabulary stays
canon-neutral.

Unlike Layers 2–4, **the LLM authors the artifact but a deterministic derivation is the
checker**: `derive_unit` in `dante_corpus/skel.py` computes the same predicate-argument
structure mechanically from the frozen Layers 2–4, and the LLM proposes its own, independent
reading of the same parse unit (it is **not shown** the Layer-4 parse). Soft checks report every
divergence between the two. A purely deterministic Layer 5 would just be `f(dep)` and could
never disagree with Layer 4; giving the LLM an independent read means a divergence can surface
a genuine Layer-4 mis-parse, not just an LLM slip — Layer 5 doubles as an audit of Layer 4,
triaged with the same measure-then-freeze discipline as `dep/CORRECTIONS.md`. The mechanics —
parse units, table format, the derivation, the divergence-normalization/authority-model/
`--repair` checker phases, and usage — live in [`skel/README.md`](skel/README.md). It is served
via `Canto.skel()` and `dante-corpus text skel`.

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
- **An imported verb-valency lexicon** — the instrument that would settle Layer 5's remaining
  complement-vs-adjunct disagreements (`essere`/`stare`/`parere` as copulas, and the ~37 lemmas
  behind the residual `advcl` cases). Rejected on the same grounds: it is an external authority,
  not something the Italian line determines. Note the contrast with the case extension
  ([`case/README.md`](case/README.md)), which asks a model to *read* the source rather than
  importing a dictionary, and so satisfies the *Neutrality audit* invariant below.

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
4. **Layer 5 (skeleton)** — *implemented* (`dante_corpus/skel.py` + `dante_corpus/hashes.py` +
   `skel/skel.py`), all 100 cantos built, checker refined through Phases 0-5r plus rules V, W,
   X, the Y-AF series, AG, the AH-AL series, the AM-AT series, the AU-AY series, the AZ-BI
   series and the BJ-BN series, with `--fix`
   restructured in Phase 6 and four rounds run (`--check`: 0 hard / 541 soft). Phase 5 closed with every route measured; see
   [`skel/PLAN.md`](skel/PLAN.md) and [`skel/README.md`](skel/README.md).
5. **Pronoun case extension** — *complete and closed, 2026-08-02*
   (`dante_corpus/case.py` + `case/case.py`; [`case/README.md`](case/README.md),
   [`case/CORRECTIONS.md`](case/CORRECTIONS.md)). Not a sixth layer: a
   Layer-2 morphological feature held in its own **permanent** directory, useful to consumers on
   its own terms independently of Layer 5's violation count. See [`case/README.md`](case/README.md)
   for the full status.

Build alongside the existing assets, gate each layer on its checks, then expose through the API.
Layers 1–5 are implemented, built for all 100 cantos, and merged to `main`; the grammatical
stack this plan describes is complete. **The pronoun case extension is also complete and closed**,
merged to `main`.
