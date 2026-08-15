# Plan: a shared grammatical-analysis stack in the corpus

## Handoff (2026-08-15) — resume here

> **The Inferno 11–15 per-position read landed: 963 → 888 soft (−75, −7.8%), 0 hard, zero model
> calls.** Eight deterministic rules (AM–AT), 16 Layer-4 rows, 2 Layer-2 rows, 20 new tests;
> Inferno 11–15 itself 37 → 17. Two things about it are new:
> 1. **Four of the eight rules are in `derive_unit` itself, not the divergence check.** Every
>    earlier batch found places the checker was *silent*; this one found the derivation **wrong** —
>    losing arguments Layer 4 stranded on a copula (AM), minting predicates out of gapping remnants
>    (AN), propagating subjects onto nominals (AT, −22 on its own and pointed at by nothing but one
>    elided verb of speech). A per-position read tests the derivation, not just the checker.
> 2. **Rule AM raises the count on purpose** (−15 spurious `extra_arg`, +22 real `missing_arg`):
>    the same honest trade the Layer-4 rounds record. Its subject leg was measured and dropped.
>
> **The next session's task is the per-position read of Inferno 16–20 — 47 soft violations at base
> 888** (16:15, 17:15, 18:6, 19:5, 20:6). Start a fresh session, list them with
> `uv run skel.py inferno --check -c <n>` from `skel/`, and read each one with
> `uv run read.py inferno <canto> <line>` (the tool added this session — it prints all five layers
> plus both Layer-5 readings for the position's whole parse unit).
>
> **The fourth `--fix` round is deliberately deferred until the reads have covered all 100 cantos**,
> five at a time, through Paradiso 33 — a decision taken 2026-08-15. Twenty batches remain, 836
> positions; the schedule table and the reasoning are in [`skel/PLAN.md`](skel/PLAN.md)'s *The Read
> Series*. In short: every batch so far removed violations at **zero model cost** (AG −43, AH–AL
> −156, AM–AT −75), and a round run before those rules exist both pays a model for positions a
> later rule takes for free and rewrites the artifact underneath any rule written afterwards, so
> the two effects can no longer be separated. Reading first lets the round run **once**, against a
> finished checker, with its per-class numbers measuring the prompt alone.
>
> **The per-batch procedure is written down** — eight steps, in [`skel/PLAN.md`](skel/PLAN.md)'s
> *How to Read a Batch*. Follow it rather than improvising: every position gets one of five
> verdicts (checker silent / derivation wrong / upstream wrong / prompt defect / genuine
> disagreement), each of which sends the fix somewhere different; no rule is written before its
> shape is censused corpus-wide; each rule is measured alone by full-corpus violation **diff**
> (not by the total), pinned by a mutation-checked test, and written up in the same session.
>
> Queued prompt work stays unmeasured until that round: the two subject-slot classes covering
> **29% of the whole residue** (`extra_arg subj` 153, `missing_arg subj` 103),
> `missing_tuple_nominal`'s rewritten *question*, and `_CONV_REPEATED`. Nothing on the prompt side
> can regress anything while no round runs.

**Layer 5 is operating under Phase 6 with 0 hard / 888 soft violations.**
Checks: `dep --check` **0 hard / 0 soft** (the subject-agreement rule's 18-position residue closed
2026-08-14; 16 further rows corrected 2026-08-15), `case --check` 0 hard, `skel --check`
0 hard/**888** soft, `np --check` 0/0, `morph --check` 0/0, `pytest` **281** passed.

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

- **Layer 5 (Phase 6)**: `--fix` runs in three stages: Stage 1 (deterministic auto-repairs, −73), Stage 2 (twelve class-specific micro-prompts, keyed by POS, by role, or by class alone), and Stage 3 (fallback whole-unit regeneration). Three user-run rounds so far: **2011 → 1452 (−559)**, **1409 → 1247 (−162)** and **1094 → 963 (−131)**.
  - **Detailed Phase 6 Plan**: For Phase 6 operating principles, architectural details, active routes, and measurement procedures, see [`skel/PLAN.md`](skel/PLAN.md).
- **Latest Improvements**:
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
- **How `CORRECTIONS.md` is used**: `*/CORRECTIONS.md` records **corrections that were actually applied**, not a place to log "found a problem, leaving it." If a review turns up a clear, decidable error, **fix it in the same session** and record what was fixed and why. The only legitimate "left alone" write-ups are ones with a genuine structural reason the text itself doesn't decide (e.g., free relatives, accusative-and-infinitive, Latin quotations, etc.).
- **CRLF hygiene**: Writing TSVs with Python's `csv` module and `newline=''` defaults to `\r\n`. Ensure `\n`-only line endings (`sed -i 's/\r$//'` or `Path.write_text` splitting/joining on `\n`) before diffing or committing.
- **Measure a checker rule by violation diff, never by the total** (2026-08-15): keep the sorted `--check` output before and after and diff it, so what a rule *newly flags* is visible next to what it removes. Two rules this session looked neutral or positive on the total and were only decidable from the diff — rule AM (−15/+22, kept: the derivation is now right) and its subject leg (dropped). A rule may be kept when it raises the count, if it makes the parse provably more correct; record that trade explicitly.
- **Census a shape before writing a rule for it** (2026-08-15): count the structural pattern over all 100 cantos first. One evidence line is not a population, and several candidate rules have been dropped at census with a population of 0.
- **Mutation-check a new rule's test**: break the rule in the source and confirm the test fails. A test that still passes with the rule removed pins nothing.
- **Editing frozen TSVs**: never by hand. Use a gated script that asserts the expected word at each `(line, token)` before rewriting the row, then re-run every layer's `--check` and `pytest`.

### Next Steps & Open Routes

- **The read series is the standing task**: per-position reads of all 100 cantos in 5-canto batches, **Inferno 16–20 next** (47 soft at base 888), running to Paradiso 33 before any `--fix` round. Twenty batches, 836 positions; schedule, reasoning and the eight-step per-batch procedure in [`skel/PLAN.md`](skel/PLAN.md)'s *The Read Series* / *How to Read a Batch*. Tool: `skel/read.py`.
- **A fourth `--fix` round is deferred until the series finishes** (`make -C skel fix`, run 3-way parallel) — the user's to run. It will then measure the queued prompt work in one pass, against a checker that is done: two subject-slot classes covering 29% of the residue, `missing_tuple_nominal`'s rewritten question, a repeated-slot convention, plus whatever the remaining batches add. See [`skel/PLAN.md`](skel/PLAN.md)'s *A Fourth `--fix` Round — Deferred, and What It Will Test*.
- **Do not re-read Inferno 1–15** (53 standing positions): already read, residue is reading error, and it is the fourth round's most direct sample.
- **Other Assistant-Side Tasks** (populations at base 888, folded into the batch that covers them):
  - Per-position read of the `missing_arg_adverb` residue (**32**) — what the `_CONV_ADVERB` repair left standing.
  - Read `extra_tuple_adjective` (**13**), position-identical after round 3's prompt clause failed to move it. Do not re-write that convention prose first. Its sibling `missing_tuple_nominal` (**25**) has had its *question* rewritten and should be read only after the fourth round measures that.
  - Measure the population of a `parataxis`→`ccomp` acceptance rule for quoted speech under verbs of speech (Inferno 8:81) before writing it.
  - Sample what the fourth round leaves of `extra_arg subj` (**153**, of which ∅ (0,0) **45**) and `missing_arg subj` (**103**) — the two buckets the new `_CONV_SUBJECT` branches target.
  - Audit remaining `extra_arg_adjective` (**45**) positions.
  - Sample `missing_arg obl` (**76**, down from 128 now that the adverb bucket is branched and repaired).
- See [`skel/PLAN.md`](skel/PLAN.md) for full descriptions of each route and testing workflows.

## Status

**All five layers are implemented, built for all 100 cantos, and merged to `main`.** Layer 5's
checker was refined through Phases 0-5r, rules V through AT, and Phase 6's restructuring plus three `--fix` rounds, bringing its soft residue to **888**
(down from 17438 at the first full-corpus measurement). See [`skel/PHASE5.md`](skel/PHASE5.md) for the full Phase 5
history, [`skel/PLAN.md`](skel/PLAN.md) for the closing positions, and *The layers* below and [`skel/README.md`](skel/README.md) for the design and current status.

**The pronoun case annex is complete and closed (2026-08-02).** It is a permanent Layer-2 sibling
extension, `case/`, on the same footing as `np/`, `dep/` and `skel/` relative to `morph/` — not a
new `morph/*.tsv` column, decided at the annex's close after two budgeted blind-regeneration
rounds were measured and rejected against a verdict rule fixed in advance. See
[`case/README.md`](case/README.md) for the design and current status and
[`case/CORRECTIONS.md`](case/CORRECTIONS.md) for the full measurement history, including *Step 5 —
the merge decision*.

**The open route is the read series**: per-position reads of all 100 cantos in 5-canto batches, Inferno 16–20 next, running to Paradiso 33 before the fourth `--fix` round (decided 2026-08-15 — see *Next Steps & Open Routes* above and [`skel/PLAN.md`](skel/PLAN.md)). All five layers plus the case extension are implemented, built for all 100
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
  further shapes where the derivation was silent rather than disagreeing, and the AG-AT series
  from the Inferno 4-6, 7-10 and 11-15 per-position reads; see
  [`skel/README.md`](skel/README.md). `dante_corpus/skel.py` (dataclasses, role
  vocabulary, deterministic derivation, table parsing, validation, TSV I/O, serve-time joins),
  `dante_corpus/hashes.py` (content-hash versioning, all layers), `Canto.skel()`/`Canto.hashes()`
  in `api.py`, `dante-corpus text skel`/`dante-corpus hash` in `cli.py`, `skel/skel.py` (LLM
  build driver, mirrors `dep/dep.py`, plus `--stats`/`--repair` modes), `skel/read.py` (the audit
  series' read tool: all five layers plus both Layer-5 readings for one parse unit). `--check` across all
  three canticles reports **0 hard, 888 soft** (down from 17438 at the first full-corpus
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
   X, the Y-AF series, AG, the AH-AL series and the AM-AT series, with `--fix` restructured in
   Phase 6 and three rounds run (`--check`: 0 hard / 888 soft). Phase 5 closed with every route measured; see
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
