# Plan: a shared grammatical-analysis stack in the corpus

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

Five layers, each a function of the source text. Layer 1 exists today; layers 2–5 are the new
work. Examples use *Inferno* I.1–6.

```
1  Nel mezzo del cammin di nostra vita
2  mi ritrovai per una selva oscura,
3  ché la diritta via era smarrita.
4  Ahi quanto a dir qual era è cosa dura
5  esta selva selvaggia e aspra e forte
6  che nel pensier rinova la paura!
```

### Layer 1 — Tokens *(existing)*

The token stream already served by the package. The foundation every higher layer cites.

- `mi` `ritrovai` `per` `una` `selva` `oscura` …
- **Generation**: deterministic (from the normalized `src/`).
- **Check**: token concatenation round-trips to the source line.

### Layer 2 — Morphology + lemma

Per-token lemma, part of speech, and morphological features (gender, number, person, tense,
mood), plus a note for contraction / apocope / elision.

| Word | Lemma | POS | Features |
|---|---|---|---|
| ritrovai | ritrovare | verb | 1sg, passato remoto, indicative |
| oscura | oscuro | adjective | f. sg. |
| Nel | in + il | prep + article | m. sg. (contraction) |

- **Generation**: LLM at build time, then frozen. (A prior local-LLM experiment produced exactly
  this table from the Italian alone, with no reference — evidence the layer is intrinsically
  recoverable.)
- **Check**: the `Word` column round-trips to the layer-1 token; features come from a closed tag
  set.

### Layer 3 — Noun-phrase enumeration

Every noun phrase in the line, with its head, source span, and modifiers — enumerated
**exhaustively and over-inclusively**. The corpus does **not** decide whether an NP is an entity;
it lists every candidate so consumers can decide.

- `[nostra vita]` · `[una selva oscura]` · `[la diritta via]` · `[esta selva selvaggia e aspra e
  forte]` · `[la paura]`
- **Generation**: LLM shallow parse at build time, frozen. Nesting (e.g. `mezzo del cammin di
  nostra vita`) is represented explicitly; over-inclusion is correct behaviour, not noise.
- **Check**: each NP span reproduces a verbatim source substring; the head token lies within the
  span.

### Layer 4 — Dependency / grammatical role

Each token and noun phrase tagged with its function in the clause and the head it attaches to.

- `[la diritta via]` = subject of `era smarrita`
- `mi` = reflexive object → `ritrovai`
- `[una selva oscura]` = locative complement → `ritrovai`
- `che` (l.6) = relative pronoun, subject of `rinova`, antecedent `[esta selva …]`
- **Generation**: LLM at build time, frozen.
- **Check**: every token carries a role; every cited head id exists; relative-pronoun antecedents
  resolve to an in-scope NP.

### Layer 5 — Predicate-argument skeleton

Noun-phrase ↔ verb tuples binding layers 3 and 4 into bare propositions — citing ids, **not** raw
text. This is the *raw* skeleton only: **no semantic frame, no coreference, no vocabulary
normalization.**

- `(subject = ∅ pro-drop, predicate = ritrovare, locative = NP[una selva oscura])`
- `(subject = NP[la diritta via], predicate = smarrire)`
- `(subject = NP[esta selva …], predicate = rinovare, object = NP[la paura], locative = pensier)`
- **Generation**: LLM at build time, frozen.
- **Check**: cited NP ids exist in layer 3; the predicate token exists in layer 1; arguments are
  layer-3 NPs or layer-1 pronoun tokens.

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

## Build & serve model

Mirror the existing `quotes/` pipeline exactly: a build step generates each layer, the result is
**committed**, and the package then **serves it deterministically** through the `dante_corpus`
API. The LLM is a build-time tool whose output is frozen and round-trip-checked — consumers see a
stable, reproducible asset, never a live model call. This follows the *measure-then-freeze*
discipline already used for normalization and quotes.

- **Artifact**: one structured file per canto (JSON/JSONL), with the five layers keyed to token
  offsets so any layer can be queried independently or joined.
- **API**: extend the corpus query surface (alongside `text tokens`, `quote show`) with the
  grammatical layers, addressable by canticle / canto / line range.
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

1. **Layer 2 (morphology + lemma)** first — lowest risk, already shown feasible intrinsically, and
   immediately useful as a lemma-queryable index.
2. **Layer 3 (noun phrases)** — the census/entity substrate consumers most want.
3. **Layers 4–5 (dependency, skeleton)** — the syntactic spine; freeze last, as they are the
   hardest and the most valuable to share.

Build alongside the existing assets, gate each layer on its checks, then expose through the API.
This is a design plan; no implementation here.
