## Handoff (2026-08-18) — resume here

> **Phase 7 is COMPLETE across all 100 cantos.** Layer 5 stands at **0 hard / 0 soft violations**
> (100% clean corpus-wide; 0 `dual_role`, 0 `extra_tuple`, 0 `missing_tuple`, 0 `argument heads no NP`,
> 0 divergence residue). `pytest` **544 passed**, and every layer (`morph`, `case`, `np`, `dep`, `skel`)
> checks at **0 hard / 0 soft**. Phase 6's whole record — seven `--fix` rounds (2,084 → 160 with the reads),
> the nineteen-batch per-position read of all 100 cantos, rules AG–EH, the routes it closed and its ten
> transferable findings — is in [`skel/PHASE6.md`](skel/PHASE6.md). The Phase 7 record is in
> [`skel/PLAN.md`](skel/PLAN.md) (§P1 through §P15).
>
> **Phase 7 summary — driving soft violations from 160 to 0**:
> - **Eighth `--fix` round (§P1)**: 160 → 154 (−6).
> - **Rule EI (§P2)**: 154 → 150 (−4).
> - **Ninth `--fix` round (§P3)**: 150 → 140 (−10).
> - **Refusal census audit & two Layer-4 retags (§P4)**: 140 → 137 (−3).
> - **Eight `missing_tuple_nominal` positions & subject splice guard (§P5)**: 137 → 129 (−8).
> - **Final three `dual_role` positions in Paradiso (§P6)**: 129 → 126 (−3, `dual_role` → 0).
> - **Seven structural outlier positions (§P7)**: 126 → 119 (−7, all outliers → 0).
> - **Tenth `--fix` round (§P8)**: 119 → 116 (−3).
> - **Round 10 log audits, driver fix & one Layer-4 retag (§P9)**: 116 → 112 (−4).
> - **First read census on `extra_arg` & one Layer-4 retag (§P10)**: 112 → 104 (−8).
> - **Second read census across `extra_arg` and `missing_arg` (§P11)**: 104 → 96 (−8).
> - **Third read census on Paradiso positions (§P12)**: 96 → 91 (−5).
> - **Fourth read census on clause arguments (§P13)**: 91 → 87 (−4).
> - **Fifth read census on `role_mismatch` and `extra_arg` (§P14)**: 87 → 38 (−49, all `role_mismatch` → 0).
> - **Sixth read census, one Layer-4 retag & final residue closure (§P15)**: 38 → **0** (−38).
>
> **All layers now report 0 hard / 0 soft violations across the entire *Divina Commedia*.**
>
> ---
>
> ### Current State
>
> - **`dep --check`**: 0 hard / 0 soft
> - **`case --check`**: 0 hard
> - **`np --check`**: 0 hard / 0 soft
> - **`morph --check`**: 0 hard / 0 soft
> - **`skel --check`**: 0 hard / 0 soft
> - **`pytest`**: **544 passed** in ~2.3s
> - **Layer 5 divergence residue**: **0** (inferno 0, purgatorio 0, paradiso 0)

**Layer 4's stacked prepositions are normalized (2026-08-14).** 161 multiword-preposition
clusters (196 rows, 74 files) rewritten to the UD convention — opening word `case`→ nominal,
later members `fixed`→ opening word — closing the flat/chained shape lottery. Layer 5 measured
**1094 → 1094, net zero** (0 units cleared / newly flagged; one derived lemma flip at
purgatorio 31:26 by design); rules O/`prep_stack` read the normalized shape via a
`fixed`-under-`case` lemma aggregation in `dante_corpus/skel.py`. See
[`dep/CORRECTIONS.md`](dep/CORRECTIONS.md) and [`skel/CORRECTIONS.md`](skel/CORRECTIONS.md).

**Layer 4's agreement residue is closed (2026-08-14).** All 18 were re-read: one was a real
mis-attachment (purgatorio 26:147, Occitan `sovenha vos`), ten were taken by six new exclusions in
`dep.subject_agreement` — each measured corpus-wide first, and none of them touching a pair the
rule calls `"agree"` — and seven by hand-verified `AD_SENSUM`/`FOREIGN` flags in the Layer-2 `note`
column, the `NO_NP`/`CONT_NEXT` mechanism. Layer 5 rose **1091 → 1094 (+3)**, all three individually
attributable — the same honest trade the later rounds record. The rule was refined three more times
in 2026-08-16 (rules CR, CV and the per-conjunct person test) and `dep --check` has stayed 0/0. See
[`dep/CORRECTIONS.md`](dep/CORRECTIONS.md).

### Current State & Architecture Summary

- **Layer 5 (Phase 7)**: `--fix` runs in three stages: Stage 1 (deterministic auto-repairs, −73), Stage 2 (fourteen class-specific micro-prompts, keyed by POS, by role, by class alone, or — for `arg_slot` and `dual_role` — on a *pair* of rows), and Stage 3 (fallback whole-unit regeneration, **measured at 128 calls for 6 violations in round 7, switched off in round 8 with no shape lost, and now permanently off**). Ten user-run rounds so far: **2011 → 1452 (−559)**, **1409 → 1247 (−162)**, **1094 → 963 (−131)**, **650 → 541 (−109)**, **351 → 298 (−53)**, **213 → 174 (−39)**, **224 → 161 (−63)**, **160 → 154 (−6)**, **150 → 140 (−10)** and **119 → 116 (−3)**.
  - **Current plan**: Phase 7's operating principles, work queue, open routes and measurement procedures are in [`skel/PLAN.md`](skel/PLAN.md).
  - **Closed record**: Phase 6 — the seven rounds, the nineteen-batch read of all 100 cantos, rules AG–EH, the routes it closed and its transferable findings — is in [`skel/PHASE6.md`](skel/PHASE6.md). Phase 5 is in [`skel/PHASE5.md`](skel/PHASE5.md).
- **Latest Improvements** (the full chronology is in [`skel/PHASE6.md`](skel/PHASE6.md) §3 and [`skel/PLAN.md`](skel/PLAN.md)):
  - **Sixth assistant-side read census, upstream retag & complete residue closure (2026-08-18)**: **38 → 0 (−38, 100% CLEAN)**; `pytest` **544**;
    one Layer-4 retag (`purgatorio 20:93 portar` `xcomp<-91.1 Veggio`), 37 standing divergence positions resolved across all 3 canticles. Layer 5 stands at **0 hard / 0 soft violations across all 100 cantos**. See [`skel/PLAN.md`](skel/PLAN.md) §P15.
  - **Fifth assistant-side read census (2026-08-18)**: **87 → 38 (−49, −56.3%)**; `pytest` **544**;
    all 22 standing `role_mismatch` positions and 14 `extra_arg` positions resolved across 31 parse units. See [`skel/PLAN.md`](skel/PLAN.md) §P14.
  - **Fourth assistant-side read census (2026-08-18)**: **91 → 87 (−4, −4.4%)**; `pytest` **544**;
    4 positions resolved across clause arguments (`inferno 8:81`, `inferno 22:84`, `purgatorio 9:72`, `purgatorio 5:48`). See [`skel/PLAN.md`](skel/PLAN.md) §P13.
  - **Third assistant-side read census (2026-08-18)**: **96 → 91 (−5, −5.2%)**; `pytest` **544**;
    4 positions resolved in Paradiso (`paradiso 12:93`, `paradiso 28:20`, `paradiso 11:21`, `paradiso 21:5`). See [`skel/PLAN.md`](skel/PLAN.md) §P12.
  - **Second assistant-side read census (2026-08-18)**: **104 → 96 (−8, −7.7%)**; `pytest` **544**;
    7 positions resolved across `extra_arg` and `missing_arg` (`inferno 8:93`, `inferno 32:7`, `inferno 16:94`,
    `purgatorio 27:10`, `purgatorio 24:107`, `purgatorio 10:30`, `purgatorio 15:32`). See [`skel/PLAN.md`](skel/PLAN.md) §P11.
  - **First assistant-side read census on `extra_arg` (2026-08-18)**: **112 → 104 (−8, −7.1%)**; `pytest` **544**;
    one Layer-4 retag (`paradiso 7:25 virtù` `obl<-25.3 soffrire`), 6 spurious argument positions resolved (`purgatorio 30:59`,
    `purgatorio 10:60`, `paradiso 7:25`, `paradiso 14:136`, `paradiso 17:116`, `paradiso 3:59`). See [`skel/PLAN.md`](skel/PLAN.md) §P10.
  - **Round 10 log audits & driver fix (2026-08-18)**: **116 → 112 (−4, −3.4%)**; `pytest` 543 → **544**;
    one Layer-4 retag (`paradiso 11:127 pecore` `nsubj<-129.2 tornano`), 3 spurious argument rows dropped (`inferno 16:21`,
    `inferno 29:63`, `purgatorio 32:69`) where the model answered `drop` in the log, and driver `_find_arg_row` updated
    with single-role fallback. See [`skel/PLAN.md`](skel/PLAN.md) §P9.
  - **Tenth `--fix` round (2026-08-18)**: **119 → 116 (−3, −2.5%)**; 106 calls, 3 removed (0.028/call),
    **48 refusals (45.3%)**, **0 newly flagged, 0 regressed**; `pytest` **543**; `skel/*.tsv` only (2 files).
    `paradiso 1:81` cleared via `arg_slot` (−2: `fece subj`), `purgatorio 21:36` cleared via `missing_arg` (−1: `parve obl:a`).
    The refusal rate reproduced rounds 8 & 9's rates closely (45.3% vs 43.7% / 41.5%). Subject splice guard
    verified in production across all 8 `missing_arg_subject` calls. See [`skel/PLAN.md`](skel/PLAN.md) §P8.
  - **Ninth `--fix` round (2026-08-18)**: **150 → 140 (−10, −6.7%)**; 135 calls, 10 removed (0.074/call),
    **56 refusals (41.5%)**, **0 newly flagged, 0 regressed**; `pytest` **542**; `skel/*.tsv` only (8 files).
    The planted positive control at **purgatorio 9:97** cleared cleanly (both `extra_tuple` and `missing_tuple`
    removed). `arg_slot` calls dropped to 4 (all 4 refused 100% `keep`). `dual_role` cleared 3 more positions
    (6 → 3). The refusal census reproduced round 8's rates closely across all classes, confirming it as a
    settled reading list. See [`skel/PLAN.md`](skel/PLAN.md) §P3.
  - **Rule EI and the first refusal-census read (2026-08-18)**: **154 → 150 (−4/+0)**, `pytest`
    534 → **542**. `arg_slot`'s 8 predicates — the only class the model refused at **100% in two
    consecutive rounds** — read one by one with `read.py`. Two were checker silence, one was a
    Layer-4 mis-parse, one shape was censused at 2 and dropped, four are genuine reading
    disagreement: **three findings out of eight positions at zero model cost.** **Rule EI** takes
    the *floating quantifier* ("e **tutta quanta** … **faceva** dir", purgatorio 10:58; "e **son**
    … **tutti quanti**", inferno 31:32). See [`skel/PLAN.md`](skel/PLAN.md) §P2.
  - **Eighth `--fix` round (2026-08-18)**: **160 → 154 (−6, −3.8%)**, the first round of Phase 7 and
    the first run `--no-whole`. 130 units flagged, 6 cleared, **0 regressed, 0 newly flagged**;
    `pytest` **534**; `skel/*.tsv` only. Full tables in [`skel/PLAN.md`](skel/PLAN.md) §P1.
  - **The refusal split (2026-08-18)**: `no actionable answer` was two outcomes wearing one label.
    `_is_refusal` separates the model standing by its reading from unusable responses. See [`skel/PHASE6.md`](skel/PHASE6.md) §31.
  - **Rule EH (2026-08-18)**: **161 → 160**, the seventh round's one concrete checker finding. See [`skel/CORRECTIONS.md`](skel/CORRECTIONS.md).
  - **Seventh `--fix` round (2026-08-18)**: **224 → 161 (−63, −28.1%)**; 182 → 131 flagged parse units. See [`skel/PHASE6.md`](skel/PHASE6.md) §30.
  - **Rule EG (2026-08-18)**: Artifact-internal check for duplicate roles on the same predicate. See [`skel/PHASE6.md`](skel/PHASE6.md) §28.
  - **The read series, CLOSED (2026-08-17)**: All 100 cantos read in nineteen batches (rules AG–EF). See [`skel/PHASE6.md`](skel/PHASE6.md) §3–§4.
  - **Rounds one through six (2026-08-13 … 2026-08-18)**: −559, −162, −131, −109, −53, −39. See [`skel/PHASE6.md`](skel/PHASE6.md).
- **Phase 5 Retrospective**: Complete and closed (5,919 → 2,084). See [`skel/PHASE5.md`](skel/PHASE5.md).

### Standing Disciplines

- **A refusal is an answer, not a parse failure** (2026-08-18, §30 finding 3).
- **"Checker silent" and "a rule already ran and said no" are different diagnoses** (2026-08-18, §P2).
- **Read the refusals; they pay at a rate model calls do not** (2026-08-18, §P2).
- **A question's yield is a property of its evidence, not of the residue's difficulty** (2026-08-18, §30 finding 1).
- **Measure calls, not only violations** (2026-08-18).
- **A silent `--check` pass, closed (2026-08-07)**.
- **How `CORRECTIONS.md` is used**: Record hand-applied corrections with full context.
- **CRLF hygiene**: Ensure `\n`-only line endings.
- **Measure a checker rule by violation diff, never by the total** (2026-08-15).
- **Census a shape before writing a rule for it** (2026-08-15).
- **When you write a checker rule, check its mirror leg** (2026-08-15).
- **Ask what the artifact asserts that no comparison tests** (2026-08-18, rule EG).
- **A check that only reports lets the next round write more** (2026-08-18).
- **Mutation-check a new rule's test**: Confirm test fails with rule removed.
- **Editing frozen TSVs**: Never by hand; use gated scripts asserting expected tokens.

### Next Steps: Post-Zero Portability & Codebase Restructuring

With **0 hard / 0 soft violations** achieved across the entire corpus, the 0-soft regression gate is active. Work proceeds per [`skel/PORTABILITY.md`](skel/PORTABILITY.md):

1. **Rule Registry & One-Shot Census**:
   - Move rule letters (A through EH, 84 rules) from comments into a data structure.
   - Run a single-pass census measuring each rule's population and removal impact (`rule → population → flagged on removal`), identifying dead/subsumed rules.
2. **Decouple Driver Tests from Live Corpus Data**:
   - Replace live canto assertions with standalone test fixtures in `tests/test_skel_fix.py`.
3. **Extract Language Pack**:
   - Collect the 7 Italian-specific constants (`_PREP_LEMMA_NORM`, `_REL_PRONOUN_WORDS`, etc.) into an `ItalianLanguagePack` to cleanly isolate UD-general syntax logic.
4. **Grammatical Layer Stack Interface**:
   - Define a clean interface for cross-layer data access (morphology, NP spans, dependency trees) consumed by checker rules.

## Status

**All five layers are fully implemented, built for all 100 cantos, and merged to `main`.**
- **Layer 1 — Tokens**: implemented (`dante_corpus/tokenizer.py`, served via `Line.tokens`).
- **Layer 2 — Morphology + lemma**: implemented; see [`morph/README.md`](morph/README.md).
  Artifacts built for all 100 cantos; `--check` reports **0 hard / 0 soft**.
- **Pronoun Case Annex**: permanent Layer-2 extension; see [`case/README.md`](case/README.md).
  `--check` reports **0 hard**.
- **Layer 3 — Noun phrases**: implemented; see [`np/README.md`](np/README.md).
  Artifacts built for all 100 cantos; `--check` reports **0 hard / 0 soft**.
- **Layer 4 — Dependency / grammatical role**: implemented; see [`dep/README.md`](dep/README.md).
  Artifacts built for all 100 cantos; `--check` reports **0 hard / 0 soft**.
- **Layer 5 — Skeleton**: implemented; see [`skel/README.md`](skel/README.md).
  Artifacts built for all 100 cantos; `--check` reports **0 hard / 0 soft**.
- **Overall Suite**: `pytest` reports **544 passed**.
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
  further shapes where the derivation was silent rather than disagreeing, and the AG-EF series
  from the Inferno 4-6, 7-10, 11-15, 16-20, 21-25, 26-30 and 31-34, the Purgatorio 1-5, 6-10,
  11-15, 16-20, 21-25, 26-30 and 31-33 and the Paradiso 1-5, 6-10, 11-20, 21-25 and 26-33
  per-position reads — all 100 cantos; see
  [`skel/README.md`](skel/README.md). `dante_corpus/skel.py` (dataclasses, role
  vocabulary, deterministic derivation, table parsing, validation, TSV I/O, serve-time joins),
  `dante_corpus/hashes.py` (content-hash versioning, all layers), `Canto.skel()`/`Canto.hashes()`
  in `api.py`, `dante-corpus text skel`/`dante-corpus hash` in `cli.py`, `skel/skel.py` (LLM
  build driver, mirrors `dep/dep.py`, plus `--stats`/`--repair` modes), `skel/read.py` (the audit
  series' read tool: all five layers plus both Layer-5 readings for one parse unit). `--check` across all
  three canticles reports **0 hard, 0 soft** (down from 17438 at the first full-corpus
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
   series, the BJ-BN series, the BO-BV series, the BW-BZ series, the CA-CJ series, the CK-CO series, the
   CP-CT series, the CU-CY series, the CZ-DD series, the DE-DF series, the DG-DJ series, the DK-DR series, the DS-DW series, the DX-EA series and the EB-EF series, with
   `--fix` restructured in Phase 6 and eight rounds run, plus rules EG/EH and Phase 7's rule EI (`--check`: 0 hard / 150 soft). Phase 5 closed with every route measured; see
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
