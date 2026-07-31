# Plan: a shared grammatical-analysis stack in the corpus

## Status

**All five layers are implemented, built for all 100 cantos, and merged to `main`.** Layer 5's
checker was refined through Phases 0-5q and its soft residue is at **3551** — every route the
Phase 5 plan opened now has a measured verdict and none is open (see
[`skel/PLAN.md`](skel/PLAN.md)'s *Where Phase 5 ended*). See *The layers* below and
[`skel/README.md`](skel/README.md) for the design and current status. One follow-on is **in
progress on the branch `case-pilot`**: the pronoun case annex, [`case/PLAN.md`](case/PLAN.md) —
its kill-gate pilot ran on 2026-07-30 and passed (81% self-agreement on the disputed clitics vs
95% on a control, zero three-way splits), step 2 froze the vocabulary and scope and wrote the
driver the same day, and **step 3's corpus pass is running now** (the user's job). See
*Resuming cold* below.

- **Layer 1 — Tokens**: implemented (`dante_corpus/tokenizer.py`, served via `Line.tokens`).
- **Layer 2 — Morphology + lemma**: implemented; see [`morph/README.md`](morph/README.md).
  Artifacts are built for all 100 cantos.
- **Layer 3 — Noun phrases**: implemented and complete; see [`np/README.md`](np/README.md). Build
  driver `np/np.py`, served via `Canto.np()` and `dante-corpus text np`. Artifacts generated for
  all 100 cantos. `--check` reports **0 hard / 0 soft** violations — see
  [`np/README.md`](np/README.md)'s *Check* section and [`np/CORRECTIONS.md`](np/CORRECTIONS.md)
  for the full history.
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
  three canticles reports **0 hard, 3551 soft** (down from 17438 at the first full-corpus
  measurement, 7776 at the Phase 4a checkpoint, 5919 after the Phase 4b `--fix` round) — see
  [`skel/README.md`](skel/README.md)'s *Check* section and
  [`skel/CORRECTIONS.md`](skel/CORRECTIONS.md) for the full correction history. Phase 5 (see
  [`skel/PLAN.md`](skel/PLAN.md)) is **complete**: its measured finding is that `--fix` yields a
  flat ~0.09-0.11 violations per LLM call regardless of how the flagged set is composed, so the
  residual was closed by deterministic checker rules and cross-layer corrections instead. Phases
  5a-5q landed (rules C/D/L/M/N/O/P/Q/R/S/T, two re-triage rounds, **two** full `--fix` passes,
  and the four
  Layer-4 correction rounds Layer 5's audit role produced — the clitic datives of Phase 5i, the
  `mark` mistags of Phase 5n, and Phase 5p's clausal complements and multi-edge deferrals; see
  [`dep/CORRECTIONS.md`](dep/CORRECTIONS.md)). `--fix` rounds are **LLM-regeneration work the
  user runs themselves** (`make -C skel fix`, run 3-way parallel); checker-side and audit work
  is the assistant's.

`grammar-stack-plan` was merged into `main` (fast-forward) and pushed; Layers 1–4 and their
artifacts now live on `main`.

**Next work**

**The five-layer stack has nothing outstanding. The one open item is the case annex, and step 3
— the blind corpus pass, `make -C case`, 1340 calls at the default `--chunk 12` — is running now
on the user's machine.** Concretely, on the branch `case-pilot`:

| step | what | who | state |
|---|---|---|---|
| 1 | kill-gate pilot — self-consistency on the disputed clitics vs a control | user ran the calls | **done, passed** (2026-07-30) |
| 2 | freeze vocabulary (`accusative`/`dative`/`ablative`/`nominative`/`genitive`/`locative` from the pilot census, plus `vocative` and `reflexive`) and scope (**all pronoun-POS tokens**, 13112 over 8541 lines); write the driver, `README.md`, `Makefile`, `dante_corpus/case.py` | assistant | **done** (2026-07-30) |
| 3 | blind corpus pass over the pronoun-bearing parse units (1340 calls), validate, **commit**, *then* join to `dep` via `--stats` | user runs the calls | **two runs done 2026-07-31, a third pending** — `--check` went 1236 → 70 hard; neither residue was a model failure (a driver abort, then Layer 2's `pos` undercounting its own `lemma` on 24 fused clitics). Both fixed; **30 of 1340 chunks left** |
| 4 | hand-verified Layer-4 correction round over the contradictions, `make -C dep check` staying 0/0 | assistant | not started |
| 5 | re-measure Layer 5, record the delta in [`skel/CORRECTIONS.md`](skel/CORRECTIONS.md); settle the oblique tail (`genitive`) from `--stats` before any `morph/` merge | assistant | not started |

The scope in step 2 went to the whole pronoun population rather than the clitic subset the
adjudication strictly needs: it is read off Layer 2's own `pos` column, so it draws no line of its
own, it covers the tonic forms (`cui`, `me`, `lui`, `altrui`, `lor`) the disputed *mirror* bucket
contains, and it makes the case of every pronominal mention queryable. That cost 1340 calls
instead of ~446 — still under Phase 5q's `--fix` pass (1702). See
[`case/CORRECTIONS.md`](case/CORRECTIONS.md)'s *Step 2*.

The order in step 3 is load-bearing: generating blind and freezing *before* looking at `dep` is
what keeps the column a third independent read rather than an artifact manufactured to close
violations. Expected return is ≈90–100 of the 3551, not zero — see the follow-on paragraph below.

### Resuming cold — the case annex, as of 2026-07-30

**Step 2's code and documentation are committed; the artifact is not.** The branch is
`case-pilot`, on top of `9c72cbf`. The split is deliberate and is the step-3 order made
literal: the corpus pass was still running when the code was committed, so `case/*/*.tsv` is
**deliberately untracked** and lands in its own commit once `--check` passes. Confirm the state
before assuming it:

```bash
git status --short          # expect only case/<canticle>/ untracked (the running build)
uv run pytest -q            # expect 138 passed (125 before the annex)
make -C dep check           # expect 0 hard, 0 soft   (untouched by the annex)
make -C skel check          # expect 0 hard, 3551 soft (untouched by the annex)
ls case/*/*.tsv 2>/dev/null | wc -l    # build progress, out of 100 cantos
```

Committed in step 2 — new: `dante_corpus/case.py`, `case/case.py`, `case/README.md`,
`case/Makefile`, `tests/test_case.py`; modified: `dante_corpus/_paths.py` (`CASE_DIR`),
`hashes.py` (`"case"` **appended** to `LAYERS`), `api.py` (`Canto.case()`), `cli.py`
(`text case`), `tests/test_hashes.py` (isolate `CASE_DIR`), plus this file,
[`case/PLAN.md`](case/PLAN.md) and [`case/CORRECTIONS.md`](case/CORRECTIONS.md).

**What the user is running.** `make -C case` — the blind corpus pass, resumable from its own
output, three canticles runnable in three parallel shells. **Do not run it, and do not touch
`case/*/*.tsv` while it runs**: LLM-scale generation is the user's job by the convention Phase 5
settled (cf. `make -C skel fix`).

Two runs have happened, both on 2026-07-31, taking `--check` from **1236 hard to 70 and then to
30 pending chunks**. Neither residue was a model failure. The first was a driver bug — an
unrecoverable chunk aborted every remaining chunk of its canto, so ~23 genuine failures cost 192
of the 1340; the driver now skips the chunk and carries on, and `--log` keeps the responses. The
second was **Layer 2's `pos` undercounting its own `lemma`** on 24 fused clitic clusters (`sen` =
`si+ne`, tagged `pronoun` here and `pronoun+pronoun` 15 times elsewhere), which rejected a
correct answer forever; corrected in [`morph/CORRECTIONS.md`](morph/CORRECTIONS.md) with
`morph`/`dep`/`skel` re-measured at 0/0, 0/0 and 0/3551. **The re-run of the last 30 chunks is
what is outstanding**; see [`case/CORRECTIONS.md`](case/CORRECTIONS.md)'s *Step 3 corpus pass*
entries.

**What the assistant does when the pass finishes** — in this order, because the order is the
annex's whole value:

1. `make -C case check` → must be **0 hard**. If not, `make -C case clean` drops the offending
   chunks and the user re-runs the build for those.
2. `make -C case stats` → the vocabulary census, the oblique-tail breakdown, the `dep`
   agreement rates, the contradiction list and the impossible-pairing list.
3. **Commit the artifact before adjudicating** — this is the commit step 2's code commit
   deliberately left open. Freezing precedes the join to `dep`; doing it the other way round
   manufactures the column to close violations, which is the failure mode
   [`case/PLAN.md`](case/PLAN.md)'s *Independence* section forbids.
4. Then step 4: the hand-verified Layer-4 correction round over the contradictions, verified
   against the terzine one at a time, with `make -C dep check` staying 0/0.

**Three questions parked for after the pass**, all recorded with their measurements in
[`case/CORRECTIONS.md`](case/CORRECTIONS.md):

- **The oblique tail.** `genitive` is weak under the criterion the `instrumental` rejection
  implies (*a value earns its place if it changes the slot the pronoun fills, not what the
  oblique means*). It was frozen anyway because folding it into `ablative` afterwards is a
  mechanical rewrite of the TSVs, while dropping it now and being wrong would cost a corpus
  pass. `--stats` prints the tail's share and the word forms carrying each value; decide from
  those numbers before any `morph/` merge. The same test applies to `vocative` and `locative`.
- **A third adjudication class the pilot never sampled.** Relative pronouns that are the
  subject of their clause, read `nominative` by `case` and `obj`/`obl` by Layer 4 — 3 of them
  in Inferno 1 alone. `--stats` gained `nsubj` → `nominative` and an *impossible pairings*
  report (`obl` × `nominative`) so they reach the candidate list. Whether the class is real at
  corpus scale is a step-4 question.
- **Layer-2 mistags this annex surfaced**, belonging to `morph/` and deliberately not acted on
  during the pass: the comitatives `meco`/`teco`/`seco` are tagged four different ways and
  `vosco` twice as `adjective` (once with the lemma `boscoso`), so 11 of those 43 tokens fall
  out of the case scope; and `me'` (apocopated *meglio*) is tagged `pronoun` at Inferno 1:112.

**Why Inferno 1 was built alone first.** It was the plumbing smoke test, and it earned its
keep: `--check` passed at 0 hard while the artifact was wrong in two ways the checker
structurally cannot see — the prompt's own worked example taught `accusative` for the reflexive
`mi ritrovai`, and the reflexive/impersonal clitic (1411 tokens, **10.8%** of the scope) had no
home in the seven-value vocabulary. Both were fixed (`reflexive` is now an eighth value) and the
canto rebuilt. The lesson generalizes: for this layer, **`--check` passing is not evidence the
artifact is right** — cross-tabulate against `dep` before trusting a batch.

Layer 5 Phase 5 closed at **0 hard, 3551 soft** (see
[`skel/PLAN.md`](skel/PLAN.md)'s *Where Phase 5 ended*): Phase 5o closed the last open row of the
`extra_arg` direct-child triage (`advcl`), Phase 5p ran the two hand-verified `dep/` correction
rounds its verdicts left over (−10), and Phase 5q spent the one remaining item — the user-run
`--fix` pass (−147, ≈28 h 3-way parallel) — plus a mechanical `ioj` → `iobj` typo fix (−4) that
took `unknown_role` to 0. What remains is documented reading disagreement between two independent
parses: `extra_arg` (1639) and `missing_arg` (1193) are 80% of it, and both regeneration and
deterministic rules now have a measured stop verdict against them.

**One follow-on is open, past its kill gate**: [`case/PLAN.md`](case/PLAN.md), a
**pronoun case annex to Layer 2** — the instrument Phase 5i/5h's parked verdicts named. It is the
sibling directory `case/`, not a new column in `morph/*.tsv`, so no existing artifact hash moves;
it is authored blind to the disputed positions so it stays a genuine **third independent read**;
and its contradictions with `dep` feed a hand-verified Layer-4 correction round rather than a
checker exemption. Its first step was a **kill-gate pilot** measuring whether the model agrees
with itself on the disputed clitics at all, and that pilot **ran on 2026-07-30 and passed**
(570 calls, `google:gemma-4-31b-it`, on the branch `case-pilot`): **81%** unanimity across three
presentation variants on the disputed positions with **zero** three-way splits, against **95%**
on a control group of undisputed clitics, and answers that split both ways against `dep` rather
than restating either existing read. Step 2 then froze the vocabulary at the census's own six
values plus `vocative` (which the clitic-only pilot population structurally could not produce)
and `reflexive`, and the scope at every pronoun-POS token, and wrote the driver, the shared
module (`dante_corpus/case.py`), `Canto.case()` / `dante-corpus text case`, and the tests;
step 3's corpus pass is running now. Measurement in
[`case/CORRECTIONS.md`](case/CORRECTIONS.md), design in [`case/README.md`](case/README.md). Expected value is stated up front as
**≈90–100 of the 3551** — it does not reach zero, and the rest of the residual (subject
resolution across enjambment and pro-drop) is untouched by it. The paired proposal, a **verb lexicon** for the
complement-vs-adjunct distinction, stays **rejected**: it would import an external authority,
which the *Neutrality audit* invariant below forbids. (A case pass does not — that invariant
constrains the build prompt's *inputs*, and an LLM reading case from the Italian alone meets it
on the same terms `pos` and `deprel` already do.)

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

**Annex in progress (pilot passed, driver written, corpus pass running)**: pronominal **case**,
the one morphological feature this layer omits and the instrument Layer 5's parked clitic
verdicts named. Built as the sibling directory `case/` rather than a new `morph/*.tsv` column, so no
existing artifact hash moves and the experiment stays revertible; merging into Layer 2 is the
natural end state if it proves out. Scope is every pronoun-POS token, decided from this layer's
own `pos` column; the vocabulary is the six values of the pilot's answer census plus `vocative`
and `reflexive`, the two that name a pronoun filling no argument slot. See
[`case/README.md`](case/README.md) and [`case/PLAN.md`](case/PLAN.md).

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
  not something the Italian line determines. Note the contrast with the proposed case annex
  ([`case/PLAN.md`](case/PLAN.md)), which asks a model to *read* the source rather than importing
  a dictionary, and so satisfies the *Neutrality audit* invariant below.

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
   (`--check`: 0 hard / 3551 soft). Phase 5 closed with every route measured; see
   [`skel/PLAN.md`](skel/PLAN.md) and [`skel/README.md`](skel/README.md).

5. **Pronoun case annex** — *pilot passed, driver written, corpus pass running*
   (`dante_corpus/case.py` + `case/case.py`; [`case/README.md`](case/README.md),
   [`case/PLAN.md`](case/PLAN.md), branch `case-pilot`). Not a sixth layer: a Layer-2
   morphological feature held in its own directory, worth ≈90–100 of Layer 5's 3551 soft
   violations and useful to consumers on its own terms. The kill-gate pilot ran over the rebuilt
   population (67 + 28 disputed, 95 control) and passed; step 2 froze the vocabulary and scope
   and built the driver and serve surface; step 3's corpus pass is running (Inferno 1 done);
   steps 4–5 — Layer-4 correction round, re-measure — are outstanding. The code is committed
   and **the artifact deliberately is not, until `--check` passes** — see *Resuming cold* above.

Build alongside the existing assets, gate each layer on its checks, then expose through the API.
Layers 1–5 are implemented, built for all 100 cantos, and merged to `main`; the grammatical
stack this plan describes is complete. The only follow-on is the case annex above, in progress
on the branch `case-pilot` with its kill gate passed and its corpus pass running.
