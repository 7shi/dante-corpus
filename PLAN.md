# Plan: a shared grammatical-analysis stack in the corpus

## Handoff (2026-08-03) — resume here

**Everything is committed** (Step 9 = `0dca943`). Checks at commit time: `dep --check` 0 hard/0
soft, `case --check` 0 hard, `skel --check` 0 hard/**3633** soft, `np --check` 0/0, `pytest` 142
passed. If `git status` shows anything uncommitted when this session resumes, that's new work from
*after* this handoff was written — check `git log` for the latest commit before assuming otherwise.

**Start here: [*The next task — a `case`-driven `skel` checker rule*](#the-next-task--a-case-driven-skel-checker-rule)
below.** It is measured, scoped, and assistant-side (no model calls). Everything between here and
it is the record of how the `case`/`dep` correction rounds ended.

**What the last four batches did.** The user's standing goal is Layer 5's soft residue at **0**
([[project_skel_soft_violations_goal]] — soft checks are rule mismatches to fix, not a baseline to
tolerate). Investigating the "clitic-case question" turned up that the case annex's own Step 4
(2026-07-31) had already found, and never acted on, many positions where **`case/*.tsv` itself is
wrong** — named in `dep/CORRECTIONS.md` ("`case` is the dissenting read... `dep` is right") but
never corrected because the column was frozen at the time. Four sessions have now worked through
this residue, and it is finished — all four named contradiction shapes are closed:

- **Step 6**: the 50 bare-clitic (`mi ti ci vi si li` + elisions) contradictions — 1 genuine
  `dep/` mistag, 49 `case/*.tsv` errors. See `case/CORRECTIONS.md` Step 6.
- **Step 7**: the 40 "impossible pairings" (`obl`×`nominative`) and the remaining 208 named
  contradictions — mechanized the `nominative`-vs-`obj` word-order shape. **12** impossible
  pairings and **99** contradictions were `case/*.tsv` errors — corrected. **9** more turned out to
  be `dep/` mistags (predicative pronoun under a copula, or a subject plainly tagged object)
  surfaced while verifying the `case` reading — retagged. See `case/CORRECTIONS.md`'s *Step 7* and
  `dep/CORRECTIONS.md`'s matching entry. Contradictions: 208→100; impossible pairings: 40→28.
- **Step 8** (previous session): the `dative`-vs-`nsubj` (8), `accusative`-vs-`iobj` (12), and
  `dative`-vs-`obj` (24) shapes — 44 candidates. Applied a transitivity test (does the head verb
  already have an explicit object filled? if yes the flagged clitic is genuinely the dative/second
  argument; if no it takes the verb's basic valency) at each position read individually against its
  terzina. **33** `case/*.tsv` corrections (19 → `accusative`, 2 → `reflexive` for inherently
  pronominal verbs, 2 → `nominative` for plain misread subject pronouns) and **3** `dep/` retags (2
  `obj`→`iobj`, 1 `iobj`→`obj`). **11** positions left alone for stated structural reasons (fused
  infinitive+clitic scope mismatch, free relative, causative-construction ambiguity, impersonal
  dative-experiencer/passive ambiguity, one Latin quotation). See `case/CORRECTIONS.md`'s *Step 8*
  and `dep/CORRECTIONS.md`'s matching entry. Contradictions: 100→63.
- **Step 9** (this session): **`accusative`-vs-`nsubj`**, the last shape — all 43 candidates read
  individually. **31** `case/*.tsv` corrections to `nominative` (relative/demonstrative subjects
  whose clause already had its object filled, plain subject pronouns, and three si-passives decided
  by Step 7's inferno 3:96.2 verdict), **0** `dep` retags. **12** left alone under exceptions
  already on record: accusative-and-infinitive (6), fused infinitive+clitic (2), free relative /
  the *non so che* idiom (2), causative causee (1), Latin quotation (1). See `case/CORRECTIONS.md`'s
  *Step 9*. Contradictions: 63→**32**.

**The `case`/`dep` contradiction work itself is finished — nothing shape-driven is open.** The 32
remaining contradictions and 28 impossible pairings are the accumulated *verified-and-left-alone*
residue: every one has been read against its terzina and left standing for a stated structural
reason (accusative-and-infinitive, fused infinitive+clitic, free relatives, causative causees,
impersonal dative-experiencers, Latin quotations, comparative standards, family F entangled). A
further pass would have to re-litigate framework conventions the corpus deliberately fixed — don't.
If a *new* `case`/`dep`/`skel` error surfaces while working something else, the standing rule below
applies: fix it there, record it there.

Should another batch of per-position work come up, each batch still ends in: `case --check` still
0 hard, `dep --check` still 0/0, `pytest` still passing, and a new dated section in
`case/CORRECTIONS.md` (+ `dep/CORRECTIONS.md` for any `dep` retag) recording what was fixed, what
was verified-and-left-alone and why, and the before/after count from `case --stats`.
**Also watch for CRLF line endings**: writing TSVs with Python's `csv` module and `newline=''`
still defaults to `\r\n` — the originals are `\n`-only, so `sed -i 's/\r$//'` (or an explicit
`lineterminator='\n'`) is needed on any touched file before diffing/committing, or `git diff` will
show the whole file changed. (In-place `sed -i 's/pattern/replacement/'` edits, and a Python script
that splits/joins on `\n` and writes back with `Path.write_text` — Step 9's method — don't have
this problem; they preserve the original line endings.)

**How `CORRECTIONS.md` is used — this is the point the user asked to be explicit about.**
`*/CORRECTIONS.md` records **corrections that were actually applied**, not a place to log "found a
problem, leaving it." If a review turns up a clear, decidable error, **fix it in the same session**
and record what was fixed and why — do not write a "known issue" entry and move on. The only
legitimate "left alone" write-ups are ones with a genuine structural reason the text itself doesn't
decide (the existing *tier-A candidates left alone* and *201 positions left alone* sections explain
this correctly: free relatives, the accusative-and-infinitive convention, Latin quotations, fused
tokens `dep` can't align component-wise) — never "this is wrong but out of scope for today." Step 5
"froze" the case annex's **regeneration and merge** questions, not its **correctness**: "frozen"
means no wholesale drop-and-rebuild (that would erase every hand correction on record, per Step 6's
own framing above), not that a per-position error is untouchable. If a future session finds another
clear `case/`, `dep/`, or `skel` error while working something else, the same rule applies: fix it
there, record it there, don't defer it to a separate pass unless it's genuinely undecidable from the
text alone.

## The next task — a `case`-driven `skel` checker rule

**Why this is open now when [`skel/PLAN.md`](skel/PLAN.md) says nothing is.** Phase 5's closing
position (*Where Phase 5 ended*, and its section 1, *The clitic-case question — half closed as
Phase 5i, half parked*) parked its largest remaining reading-disagreement population with an
explicit reason: it "needs a Layer-2 case feature or a clitic lexicon", and the project had twice
declined to open one. **That feature now exists** — `case/` was built after that verdict was
written, and Steps 6-9 above have just hand-corrected 164 of its positions against `dep`. So the
instrument Phase 5 named as missing is present, freshly audited, and **not yet wired into the
Layer-5 checker at all**: `dante_corpus/skel.py` never imports `dante_corpus.case`. That is the
one genuinely new route, and it is checker-side work (the assistant's), not `--fix` regeneration
(the user's). Update `skel/PLAN.md`'s closing section when this lands — its "every route is
closed" statement is what this task reopens.

**The measurement (2026-08-03, on the post-Step-9 tree).** Of the **516** `role_mismatch`
violations, **210** sit on an argument position the `case` annex holds a value for. Classifying
each by whether that value corroborates the derived (`dep`-side) or the given (LLM-side) role,
under the obvious mapping between two frozen vocabularies — `nominative`↔`subj`,
`accusative`↔`obj`, `dative`↔`obl:a`/`iobj`, `ablative`/`locative`↔`obl*`:

| | count |
|---|---|
| `case` corroborates the **derived** side → checker-rule candidate | **161** |
| `case` corroborates the **given** side → `dep`-correction candidate | **17** |
| value has no role mapping (`reflexive`/`vocative`/`genitive`/fused `a+b`) | 23 |
| decides neither (both or neither side match) | 9 |

The four biggest buckets, all in the first row: given `obj` / derived `obl:a` with `case=dative`
(55), given `obj` / derived `subj` with `nominative` (43), given `subj` / derived `obj` with
`accusative` (21), given `obl:a` / derived `obj` with `accusative` (20).

**How to reproduce the measurement.** Parse `uv run skel/skel.py <canticle> --check` output with
`^(\w+) (\d+):(\d+) \[tag\] role_mismatch: [\d.]+ arg \((\d+), (\d+)\) '([^']+)' vs '([^']+)'`
(given role first, derived second), and join each `(line, token)` against
`case.case_index(case.load_case(canticle, canto))`. **Gotcha: `--check` writes its violation lines
to stderr**, only the `check complete:` summary goes to stdout — capture `stderr`, not `stdout`,
or the join silently measures nothing.

**The task, in two parts, both in one batch:**

1. **The rule** (expected −161). A new one-directional acceptance in `_classify_divergence`'s
   `elif grole != drole:` branch, in the same shape as rules L/M/N/O: accept the divergence when
   the `case` annex's value for that argument position corroborates the **derived** role and not
   the given one. Gate it exactly that tightly — corroborating *both* or *neither* accepts
   nothing, and the mirror direction is part 2's hand-verified round, never an automatic accept
   (the same asymmetry Phase 5j measured and enforced when it rejected rule O's two-directional
   variant). `skel.py` will need `case` data threaded into the checker the way
   `dep_index_by_pos`/`morph_pos_by_position` already are. Tests in `tests/test_skel.py` alongside
   the existing rule tests.
2. **The 17 `dep`-correction candidates** (the rule's by-product). Positions where `case` sides
   with the LLM against `dep` — i.e. `dep` mistag candidates, the same shape Steps 7 and 8 worked.
   Read each against its terzina, retag the genuine ones in `dep/`, and leave the rest with a
   stated structural reason. **Do not skip this half**: leaving it would be exactly the "found a
   problem, leaving it" the section above forbids.

**Neutrality check before starting.** This stays inside the *Neutrality audit* invariant: it maps
one frozen corpus vocabulary onto another, both authored by a model reading the Italian alone. It
is **not** the imported verb-valency lexicon *Out of scope* rejects — nothing external enters.

**Batch ends in**: `skel --check` 0 hard and a lower soft count, `dep --check` still 0/0,
`case --check` still 0 hard, `pytest` passing with the new tests, a dated section in
`skel/CORRECTIONS.md` (+ `dep/CORRECTIONS.md` for the retags) recording the rule, its measured
yield and the hand-verified round, and the counts in this file, `skel/README.md` and
`skel/PLAN.md` updated to match.

**Other routes, for reference — not recommended over the above.** (a) A `dep` `--check` rule for
"at most one `obj` per predicate": corpus-wide 231 predicates violate it (84 with a clitic, 147
without); it is its own round and needs the coordination half re-attached as `conj` rather than
exempted — see `skel/PLAN.md` section 1's *A wider Layer-4 finding*. (b) Another `--fix`
regeneration pass: measured at 0.086 violations per call in Phase 5q, so ~1600 calls for ~130, and
it is user-run work.

## Status

**All five layers are implemented, built for all 100 cantos, and merged to `main`.** Layer 5's
checker was refined through Phases 0-5q and its soft residue is **3633** (down from 17438 at the
first full-corpus measurement, and still moving as the `case`/`dep` correction rounds above find
and fix cross-layer errors) — every route the Phase 5 plan opened has a measured verdict and none
is open (see [`skel/PLAN.md`](skel/PLAN.md)'s *Where Phase 5 ended*). See *The layers* below and
[`skel/README.md`](skel/README.md) for the design and current status.

**The pronoun case annex is complete and closed (2026-08-02).** It is a permanent Layer-2 sibling
extension, `case/`, on the same footing as `np/`, `dep/` and `skel/` relative to `morph/` — not a
new `morph/*.tsv` column, decided at the annex's close after two budgeted blind-regeneration
rounds were measured and rejected against a verdict rule fixed in advance. See
[`case/README.md`](case/README.md) for the design and current status and
[`case/CORRECTIONS.md`](case/CORRECTIONS.md) for the full measurement history, including *Step 5 —
the merge decision*.

**Nothing is open.** All five layers plus the case extension are implemented, built for all 100
cantos, every route any of their plans opened has a measured verdict, and everything is merged to
`main`.

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
  built for all 100 cantos; `--check` reports **0 hard / 0 soft** violations — see
  [`dep/README.md`](dep/README.md)'s *Check* section and
  [`dep/CORRECTIONS.md`](dep/CORRECTIONS.md) for the full correction history.
- **Layer 5 — skeleton**: implemented, all 100 cantos built, checker refined through Phases 0-5q
  — the four mechanical phases (normalization, authority model, `--repair`,
  double-listing/elided-copula whitelist) plus Phase 5's rule series; see
  [`skel/README.md`](skel/README.md). `dante_corpus/skel.py` (dataclasses, role
  vocabulary, deterministic derivation, table parsing, validation, TSV I/O, serve-time joins),
  `dante_corpus/hashes.py` (content-hash versioning, all layers), `Canto.skel()`/`Canto.hashes()`
  in `api.py`, `dante-corpus text skel`/`dante-corpus hash` in `cli.py`, `skel/skel.py` (LLM
  build driver, mirrors `dep/dep.py`, plus `--stats`/`--repair` modes). `--check` across all
  three canticles reports **0 hard, 3633 soft** (down from 17438 at the first full-corpus
  measurement) — see [`skel/README.md`](skel/README.md)'s *Check* section and
  [`skel/CORRECTIONS.md`](skel/CORRECTIONS.md) for the full correction history, including the
  case annex's contribution to that count. Phase 5 (see [`skel/PLAN.md`](skel/PLAN.md)) is
  **complete**: its measured finding is that `--fix` yields a flat ~0.09-0.11 violations per LLM
  call regardless of how the flagged set is composed, so the residual was closed by deterministic
  checker rules and cross-layer corrections instead. `--fix` rounds are **LLM-regeneration work
  the user runs themselves** (`make -C skel fix`, run 3-way parallel); checker-side and audit
  work is the assistant's.

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
   `skel/skel.py`), all 100 cantos built, checker refined through Phases 0-5q
   (`--check`: 0 hard / 3633 soft). Phase 5 closed with every route measured; see
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
