# Layer Structure Review: Plan

### Handoff (2026-09-09) — resume here

> **Where this stands.** The directory holds four documents and no code:
> [`README.md`](README.md) (stable orientation), this plan (the source of truth,
> and the file that gets updated), **[`REDESIGN.md`](REDESIGN.md)** — new, a
> design proposal with its own measurements — and `reads/`, still one all-layer
> read ([`reads/inf-1-1-9.md`](reads/inf-1-1-9.md)). §4's five items remain
> unstarted **as written**, but the work has taken a shape §4 does not describe;
> see *Method* below. §4 is not rewritten yet, deliberately — the new direction is
> provisional.
>
> **Two premises were set by the operator (2026-09-09)**, and are recorded at the
> head of [`REDESIGN.md`](REDESIGN.md) rather than in §2, because they constrain
> the redesign rather than the review:
> 1. **Preserving the frozen artifacts is not a constraint.** Regenerating a layer
>    is acceptable even where it overlaps what is frozen, and the time cost is
>    accepted. This supersedes the earlier working assumption — held for most of
>    the 2026-09-09 session — that the TSVs stay fixed and the API only grows
>    additively. Terminal renumbering is therefore on the table.
> 2. **Stop at phrases.** The redesign enumerates phrases and does **not** build a
>    complete tree rooted at the sentence. The argument is `REDESIGN.md` §3; the
>    price is §4.1.
>
> **Method now in use.** Layers 1–4 are examined **one at a time**, each against
> *Inferno* 1:1–3, quoting concrete positions, with every observation measured
> corpus-wide before it is written down. This replaces the previous handoff's
> question 4 (*which passage gets the next all-layer read*): the axis of iteration
> is now the layer, not the passage. `reads/` keeps its own purpose and its
> promotion rule; the layer-by-layer notes have so far gone into `REDESIGN.md`
> rather than into `reads/`.
>
> **Layer 1 is done. It corrected two things this plan and the pilot read both
> got wrong:**
> - **Nothing is discarded at Layer 1.** `Line.text` holds the normalized source
>   verbatim, punctuation and guillemets included (`api.py:249`); only the
>   `Line.tokens` view filters non-alpha (`api.py:52`). The defect is not loss but
>   **address**: punctuation has no token index, so no layer can cite it.
> - **The sentence unit already exists.** `dante_corpus/dep.py:200`
>   `sentence_groups` splits on line-final `.`/`!`/`?`, sub-splits at `;`/`:`, caps
>   at 12 lines with a hard-split fallback. **Layer 4 was built inside these
>   units.** It is not stored in `dep/*.tsv`, not on `Canto`, not in `__all__` — a
>   consumer must import a private function and recompute it. It needs storing and
>   exposing, not designing; the 12-line cap should be dropped.
>
> **And it sharpened §1.3's diagnosis.** "Flat encoding" is imprecise: Layer 4 *is*
> a tree. The accurate statement is **the tree's nodes are tokens; no node stands
> for a constituent** — and Layer 3 is already a partial constituent layer, in the
> right shape (enumeration, nesting by containment), stopped at NPs and at the
> line. `REDESIGN.md` §1 carries this.
>
> **The previous handoff's four questions.** (1) Prioritise (iii), hand (i)/(ii)
> to the per-layer `CORRECTIONS.md` files — **still open**. (2) Design §4-1 as a
> cross-layer readout — **answered by force**: `REDESIGN.md` §4.1 makes the
> cross-layer checker part of the design, since enumeration has no tree to enforce
> coherence. (3) State the hypothesis up front — **answered**: `REDESIGN.md` states
> it and §6 lists what would falsify it. (4) Next passage — **superseded** by
> *Method* above.
>
> **"Next: Layer 2" happened, but not as a review — see below.** The composite
> POS inventory (2,681 tokens) and the `note`-field noise are now consumed by
> the L1/L2 design work below; the participle POS split, the `che` mistag
> (finding B's 225), the unfrozen POS vocabulary, and `case/`'s sparseness are
> **still untouched** and remain candidates either for an old-Layer-2 review
> write-up or for absorption into L2's POS-classification step — not decided.
>
> **Deferred, deliberately, and now partly settled.** How generation 1 is shown
> to the model while generation 2 is built — which frozen layers are safe input
> and which are the undecided positions it must not anchor to. A split was
> drafted 2026-09-09 (safe: tokens, lemma decomposition, Layer-4 bracketing,
> `sentence_groups`; contaminated: `cop`/`attr` 953:357, the locution
> `obl`:`advmod`:`nmod`:`conj` 217:68:30:13, Layer-3 granularity, participle POS,
> `che` POS, `expl`), with the unresolved question of whether Layer-4 bracketing
> can be "safe" when the `advmod`/`obl` choice moves the brackets themselves.
> **Premise 3 below settles the general shape** (bootstrap-only, never a
> rebuild-time input); the specific safe/contaminated split above is still
> unrevisited against it. `REDESIGN.md`'s Status records the residue as
> unwritten.
>
> ---
>
> **L1/L2 design (2026-09-09, same session, continued past Layer 1).** The
> *Method* above says Layers 1–4 are reviewed one at a time against the old
> generation; in practice, once Layer 1's review turned up the punctuation and
> `l1_index` questions, the work did not stay a review of old Layer 2 — it
> became direct design of the **rebuilt** `L1`/`L2` (terminology: `L1`, `L2`, …
> name the rebuilt layers from here on; `Layer 1`, `Layer 2`, … keep naming the
> frozen generation). Old Layer 2's known material (composite POS, the `che`
> mistag, participle POS, the `note`-field noise) fed this as precedent, not as
> a standalone review write-up — **the `che` mistag and the participle POS
> split are still not separately reviewed**, and may end up folded into L2's
> POS-classification step below rather than written up as old-Layer-2
> corrections; that is not decided.
>
> Decisions recorded in `REDESIGN.md`, **none implemented**:
>
> 1. **Premise 3 (new): generation 2 must not depend on generation 1 at rebuild
>    time.** Old Layer 1–5 may be used once, as bootstrap material during
>    construction (a warm start, a precedent to diff against) — never as a
>    named input a generation-2 layer's *definition* reads. (§Status,
>    `REDESIGN.md`)
> 2. **L1 = `tokenize()`'s full output, punctuation included, own numbering.**
>    Diverges from old Layer 1's `Line.tokens` (`api.py:52` drops punctuation
>    before indexing), by design — this is what makes punctuation citable at
>    all. 17,434 punctuation terminals newly addressable; quote-mark pairs
>    exactly balanced (`«`/`»` 1,062/1,062, `‘`/`’` 109/109, `“`/`”` 51/51),
>    which is the address the open survey item "the quotes hierarchy" (§4 item
>    1 below) has been missing. (`REDESIGN.md` §2.1)
> 3. **L2 = grammatical words, as `(l1_index, text)` pairs, only splits, never
>    merges.** 1:many for composite tokens (`nel` → `(0,in),(0,il)`), 1:1
>    otherwise. Many:1 (e.g. `fixed`'s complex prepositions, 170 groups) stays
>    a relation one layer up, over L2 entries, because 37 of those 170 groups
>    (21.8%) have a member that is itself a composite split and a tuple
>    `l1_index` would misattribute part of a token. (`REDESIGN.md` §2.1)
> 4. **L2 is a three-step pipeline: split → POS classify → normalize.**
>    Normalization (apocope/elision restored to the inflected *surface* form,
>    stopping short of lemma — `i'`→`io`, `son`→`sono` while `essere` stays the
>    lemma) needs step 2's POS for wordforms spanning more than one POS (`l'` →
>    `lo`/`la` depending on gender, 159 such wordforms) — desk-checked by hand
>    against *Inf* 1:1 and *Inf* 1:25, which is what showed this is an ordering
>    consequence, not a special case. Scope: split table 442 wordforms (423
>    deterministic), normalization tables 300 wordforms (apostrophe-marked) +
>    1,386 (apocope without apostrophe, 477 of which need a lemma-independent
>    reconstruction). (`REDESIGN.md` §2.1)
> 5. **Build order: L4 (dependency) precedes L3 (phrases), despite the
>    numbering.** L3 must project from generation 2's own L4, never from old
>    Layer 4, or L3 stays permanently dependent on the old file (premise 3).
>    Old Layer 4's 40,654 projectable subtree groups remain useful as the
>    bootstrap case for building L4 itself. (`REDESIGN.md` §2.2, §5)
> 6. **Concrete next task, decided but not started:** build the split table,
>    the per-L2-entry POS classification, and the normalization tables as
>    three independent passes (no view of old Layer 2 while building), then
>    diff each against old Layer 2 as the precedent check — three outcomes,
>    same methodology as every `*/CORRECTIONS.md` (agree / old-generation-is-
>    wrong, e.g. `dal`'s `di+il` / genuine synchronic ambiguity, e.g. `nel`).
>    Execution mechanism: `harness/stages/09.md` §2's fixed-context step
>    (`P -> O -> State Σ ()`), **one step per wordform per job, no batching**
>    — batching is exactly where the paper `09.md` reviews places 68% of its
>    failures, and wall-clock cost is not a constraint this project is short
>    on. (`REDESIGN.md` §2.1, end)
>
> **This is a plan, not a start.** The operator's instruction closing this
> session: record the decisions, do not implement. The next session's first
> choice is whether to begin the split/POS/normalize tables, continue the
> Layer 1–4 review method into old Layer 2/3/4, or design L3/L4 further first.
>
> ---
>
> **A caveat that still stands.** Every measurement in `reads/` and in
> `REDESIGN.md` came from ad hoc scripts run in a scratchpad and **not kept**. All
> are re-derivable from the frozen artifacts in minutes; none is reproducible by
> re-running a committed artifact. The cross-layer checker of §4.1 is where that
> gets fixed.

## Why this directory exists

`layers/` opens because `harness/` finished the thing it was actually built for
and ran out of a subject worth pointing it at unchanged.

`harness/` is named for the apparatus, not for Layer 5. Its own mission
statement ([`../harness/PLAN.md`](../harness/PLAN.md) §1) says the goal is "a
reproducible, fully automated, and generalizable reconstruction pipeline";
Layer 5 was the first subject, chosen because it is the richest target in this
corpus. That mission is met. What is *not* met — and what this directory takes
up — is the assumption printed in the same paragraph: that `skel/` and the
layers beneath it are an **immutable** reference the pipeline reproduces.

The division of labour from here:

- **`dante_corpus.harness`** — the library. The canto loop, the fixed-context
  execution mode, the gates' shape, the `--fix` machinery, the artifact and
  resume machinery, the observability contract. It is a tool, and it is finished
  (see **§1**). Since 2026-09-07 it is literally a package: the apparatus was
  split out of `harness/` and imports nothing else from `dante_corpus`, so it
  ships with the distribution. What stays in top-level **`harness/`** is Layer
  5's own side — the gates' content, the fix levels, the toolset, the skill
  files, the CLI and the `recon/` artifacts — which is what a *subject* looks
  like to this library.
- **`layers/`** — this directory. Skills and loops that *use* that tool, aimed
  at the layer stack itself: what each layer can and cannot express, and what
  the description ought to say.

The mechanics of the split — what moves and what stays — were a separate
discussion, held after this document was written and settled on 2026-09-07;
[`../harness/PLAN.md`](../harness/PLAN.md) §2, *After the last stage*, is the
record. Nothing here specifies them.

---

## 1. What the last two sessions established

Two findings, and they point in opposite directions. Recording both is the
reason this document exists.

### 1.1 The apparatus is stable (2026-09-06, `harness/stages/10.md` §S10.4)

Level 3's first corpus-wide `--fix` run is the readout. It was not a trial of
the corpus; it was a trial of the machine, and the machine passed every check
put to it in advance:

| | |
|---|---|
| findings (the criterion) | **334 → 225** |
| corpus | 3,126 → **2,982 soft**, **0 hard** |
| levels 1 and 2 after the pass | **0 / 0**, unmoved |
| suite | **1,029 passed** |
| gold agreement (readout only) | 0.7610 → 0.7628 |
| units reopened | **293** across 94 cantos |
| verdicts | 62 accepted, 20 salvaged, 206 no improvement, 5 refused |
| `FixClass.exempts` (first live use) | fired at **exactly 3** units, each at a predicate the level's own findings named |
| the 5 `new_class:extra_arg` refusals | all at *other* predicates — correctly refused |
| units ending worse | **0** (hard 0 everywhere; no unit's own findings rose) |
| concurrency (first ever) | 3 streams, 16.82 h elapsed in **6.72 h wall = 2.50×**, **0 `api_retries`**, ≈ 8,800 tokens/min against the 16K TPM quota |

The mechanism does what it is told, and what it is told is auditable after the
fact. **The apparatus is no longer the open question.**

### 1.2 The object is not stable

The same session, asked to settle one narrow gate question (`harness/stages/10.md`
§S10.2), measured the layers instead and found the description undecided at the
positions the question was about. Every number below is from the frozen layers
and the recon artifact; gold was not opened.

**The 133 `membership` violations** (all of them bare `obl` — that is S10.2's
own finding), by the Layer-4 deprel of the argument:

```
advmod 108    mark 12    advcl 7    amod 2    case 2    conj 1    det 1
```

The 108 `advmod` ones, by the Layer-2 pos of the argument:

```
adjective 87    conjunction 9    preposition 8    verb 2    noun 1    preposition+noun 1
```

**Layer 2 contradicts itself at these positions.** Corpus-wide there are
**9,249** `advmod` tokens; Layer 2 calls 90.8% of them `adverb`, 5.1%
`adjective`. Splitting the 108 by how the *same word* is tagged at its other
`advmod` positions:

| | count | shape |
|---|---:|---|
| **A** | **15** | the word is usually `adverb` at `advmod`; this instance is not (`forte` ×3, `certo` ×3, `come` ×3, `entro` ×2, `presso` ×2, `tanto` ×1) |
| **B** | **41** | the word is tagged both ways and this is the majority (`tutto` ×10, `solo` ×7, `ratto` ×5, …) |
| **C** | **52** | the word is never tagged `adverb` at `advmod` anywhere (`fiso` ×3, `dritta` ×2, `lento` ×2, `veloci` ×2, …) |

Group A is the shape [`../morph/CORRECTIONS.md`](../morph/CORRECTIONS.md)
already treats as a mistag — "`giuso` … **the only one of 33 occurrences** in the
corpus tagged noun". `certo` at `advmod` is `adverb` 15 / `adjective` 9; `forte`
is 15 / 8. Same word, same function, two descriptions.

### 1.3 The root cause is a flat encoding, not a wrong rule

`per certo` is `preposition + adjective` at the token level — correctly so — and
an **adverb** as a whole. The stack is token-indexed, so it has nowhere to say
the second thing, and the annotation has to push the phrase's category onto one
of its tokens or onto the edge above it. Both were tried, inconsistently.

**The corpus already owns three devices for this, and only one direction is
built out:**

| device | expresses | usage |
|---|---|---|
| Layer 2 composite pos | **1 token = several categories** | `preposition+article` 1,984, `verb+pronoun` 488, `pronoun+preposition` 58, `adverb+pronoun` 42, `preposition+noun` 12, `preposition+adverb` 4, `adverb+adjective` 1 |
| Layer 4 `fixed` | **several tokens = 1 grammatical word** | **171 edges, 168 of them complex prepositions** (`in su` 51, `dietro a` 15, `presso a` 11, `per entro` 8 …), all with `head_deprel=case` |
| Layer 3 spans | **several tokens = 1 phrase, with a head** | noun phrases only (columns are `line, start, end, head, text` — the shape is general) |

The same word takes both treatments depending on which direction it grammaticalised
in:

```
Inf 23:148  dietro a le poste …   dietro pos=preposition deprel=case   FIXED child 'a'    hierarchy expressed
Inf  9:55   Volgiti 'n dietro …   dietro pos=adverb      deprel=obl    case  child "'n"   flattened
Inf 11:6    ci raccostammo, in dietro, ad un coperchio
                                  dietro pos=adverb      deprel=advmod case  child 'in'   flattened
```

**The cost is measurable.** Of 9,249 `advmod` tokens, **68 (0.7%) carry a `case`
child** and every one is an Italian adverbial locution — `di sùbito` 8,
`del tutto` 6, `di più` 5, `a pena` 5, `per certo` 3, `in dietro` 2, `di rado` 1,
… Widening to every position where such a locution head appears (32 distinct
locutions, **330 positions**), Layer 4 attaches the *same phrase* four different
ways:

```
obl 217    advmod 68    nmod 30    conj 13    xcomp 1    obj 1
```

```
di retro   obl=27  nmod=2  advmod=1        a pena     obl=10  advmod=5
di fuor    obl=17  nmod=5  advmod=1        del tutto  advmod=6  obl=2
di sotto   obl=15  nmod=6  advmod=2        di sùbito  advmod=8
in dietro  obl=14  advmod=2  conj=1        di più     advmod=5
```

A flat encoding gives the annotator two half-truths — *the phrase is adverbial*
(→ `advmod`) and *the head carries a `case` child, so it is a PP* (→ `obl`) — and
no way to hold both. 217 : 68 : 30 : 13 is the record of that choice being made
without a criterion.

### 1.4 The consequence reaches Layer 5, and it is arbitrary

`obl` is in `ARG_DEPRELS`, so `derive.py` derives it as an argument and an agent
row matching it is clean. `advmod` is not, so the *identical* row becomes
**`membership` + `extra_arg` — two violations**.

> The same phrase scores 0 or 2 violations depending on a Layer-4 choice that
> has no criterion behind it.

**Inferno 28:4** carries three `advmod` arguments and all three outcomes:

```
Ogne lingua per certo verria meno            per lo nostro sermone e per la mente
                                             c'hanno a tanto comprender poco seno.
```

| | what it is | agent wrote | checker says | correct? |
|---|---|---|---|---|
| `per certo` (4.4) | adverbial locution, sentence-modifying — **not an argument** | `obl` | membership + extra_arg (**2**) | right conclusion, by accident of `pos` |
| `meno` (4.6) | part of the verbal idiom *venir meno* — **not an argument** | `obl` | **0** (pos=`adverb` → exempt) | **wrong** |
| `tanto` (6.4) | what *comprender* comprehends — **is an argument** | `obl` | **0** | right |

And the agent is not over-generating: writing `obl` at `per certo` follows the
corpus's own majority treatment, **217 of 330**. It is penalised only where
Layer 4 happened to pick the minority label.

### 1.5 What `validate.py:158` actually is

The membership check exempts a bare `obl` whose argument's Layer-2 pos is
`adverb` (`dante_corpus/skel/validate.py:158`). Read against the above, that
condition is **a proxy for "is this phrase lexicalised?" expressed in the only
vocabulary a token layer has**. The proxy is needed because there is no place to
write the judgement itself. Registry rules J and R are two more proxies for the
same phenomenon with two more form conditions:

| | role | required pos |
|---|---|---|
| `validate.py:158` (contract, ungated) | `obl` / `obl:*` | `adverb` |
| rule J `_adverbial_oblique` | `obl` / `obl:*` | `adverb` / `noun` / `pronoun` |
| rule R `_predicative_advmod` | **`xcomp`** | `adjective` / `noun` |

Three conditions for one phenomenon is the signature of a judgement with no home.

**This is why S10.2 cannot be decided inside Layer 5**, and why the harness's
gate (`runner/tools.py`) cannot simply be aligned to the contract: the contract
is a proxy, and aligning to it would freeze the proxy.

---

## 2. The premises this work runs on

Set by the operator (2026-09-07), before any decision, and adopted here as
standing:

1. **Gold has no authority.** It is the product of ad hoc work. A rule change
   that puts gold in violation is information, not a problem.
2. **The other layers are not necessarily right either.** Do not force
   consistency inside the layer under work. The precedent is on disk: the
   Layer-5 read revised the layers beneath it, and each keeps its own record —
   [`../dep/CORRECTIONS.md`](../dep/CORRECTIONS.md) **42** correction sections,
   [`../case/CORRECTIONS.md`](../case/CORRECTIONS.md) **34**,
   [`../morph/CORRECTIONS.md`](../morph/CORRECTIONS.md) **30**,
   [`../np/CORRECTIONS.md`](../np/CORRECTIONS.md) **19** — with a methodology
   already stated there: classify by cause before touching anything, verify each
   row against an existing precedent row, re-run the layer's `--check`
   afterwards.
3. **Rules are decided by linguistic validity.** There is no a priori guiding
   principle to derive them from.

**One engineering constraint sits beside premise 3, and is not a fourth
premise:** a rule the agent cannot reach from the frozen layers is a rule the
agent cannot satisfy. Linguistic validity decides *what* the description says;
it does not decide *which layer it is written in*. Keeping those two apart is
what S10.2 failed to do.

---

## 3. The termination condition, and how it changes

**`harness/`'s termination condition was never written down.** It operated as
"Layer 5 conforms to the layer's own contract", implemented as "the soft
findings a fix level can reach are exhausted" — the stage structure, levels
1 → 2 → 3 → …

That condition presupposes §1.2's negation: that the contract and the layers
beneath it are fixed and correct. Where they are not, remaining findings are a
mixture of *the artifact is incomplete* and *the description is undecided*, and
a fix level cannot tell the two apart. Continuing would have the agent fit the
encoding's arbitrary choices — the ad hoc method of gold construction,
automated. That is the reason the condition changes rather than the reason a
level was hard.

**The new one, in scope and in kind:**

| | was | becomes |
|---|---|---|
| scope | Layer 5 | the whole layer stack |
| target | reproduce the current description | **review the description itself** |

[`../harness/FUTURE.md`](../harness/FUTURE.md)'s vertical-slice note already
planned the first half — the harness building every layer over a narrow range —
but assumed the second half away: it expected the current results to be
reproduced. That assumption is dropped, and the correction stands in that file
as a dated standing note at its head (2026-09-07), which also records what
survives it unchanged — the machinery inventory, the swap costs, the
feasibility gradient, and the own-precedent store.

### 3.1 What the change costs

Three things stop working, and each needs a successor.

1. **Standing Invariant §1 becomes provisional.** §1 keeps gold out of rule
   construction by naming `validate.py` / `derive.py` as the substitute
   authority. If the layers are under review, that substitute is under review
   too. §1 must not simply empty: the successor is premise 3 written as a rule —
   **rules are decided by linguistic argument from the primary text, and the
   argument is recorded**. The prohibition on fitting to gold survives intact;
   what changes is that the contract drops from *authority* to *current
   description*.
2. **The progress metric is gone.** Soft counts are not comparable across a
   moving contract, and `make agree` loses its baseline. The successor is
   already designed, in `FUTURE.md`'s horizon memo: the correlation between
   **settled by intrinsic criteria** (clean validation plus convergence, no gold
   consulted) and agreeing with gold. It was written for rungs (2)–(4) of that
   memo's ladder, where no gold exists. It is needed at rung (1) now.
3. **The stage structure retires with the condition it served.** "Pick a soft
   class, argue it from the contract, make it a level" works only while the
   contract is fixed. Stage 10's residue — **225 findings at level 3, 2,982 soft
   corpus-wide** — is a readout of where the current description and the current
   artifact disagree. **It is not a to-do list.**

---

## 4. What is open

Nothing below is started. The order is not fixed either, except that the last
one waits.

One all-layer read exists, as a pilot rather than as work on any item:
[`reads/inf-1-1-9.md`](reads/inf-1-1-9.md) — nine lines, eight findings, five
corpus-wide measurements. It proposes a classification axis for item 3 and a
hypothesis that would reshape item 2, and it is one passage, so neither is
adopted here.

1. **Which phenomena are hierarchical, and how many.** §1.3 measured one family
   (adverbial locutions, 330 positions). Others are visible and unmeasured:
   verbal idioms (*venir meno*), secondary predicates (`dritto levato` vs `fiso`
   in the same line, Inf 4:5 — depictive and manner both under `advmod`), the
   714 `advcl`-as-`obl` population Layer 5 declines on principle, the quotes
   hierarchy. A survey is the first work item.
2. **Where a hierarchical judgement gets written.** Three candidate homes, all
   already in the corpus (§1.3's table): Layer 4 `fixed` (UD's own device, in use
   for the mirror-image case), a Layer-3-style span layer generalised beyond NPs,
   or a Layer-2 composite pos (only for one-token cases). The decision is per
   phenomenon, not global.
3. **The classification readout.** Split today's 2,982 soft violations by a new
   axis — *disagreement about the language* vs *disagreement about the
   encoding*. Distinct from S6.1's three outcomes, which assumed a fixed
   contract. Stratified sampling by class is the practical form; the whole
   population is too heavy.
4. **The non-locution `advmod` residue.** Group C's 52 (§1.2) — bare adverbially
   used adjectives with no `case` child — are not multiword expressions and the
   flat encoding is adequate for them. What is undecided is whether Layer 5
   counts an `advmod` modifier as an argument at all. Inf 4:5 is the exemplar
   and needs its own all-layer read.
5. **`layers/` as a working directory.** Skills and loops that drive `harness/`
   as a library. Deferred until the harness split is settled.

---

## 5. Relationship to the existing documents

- [`../harness/PLAN.md`](../harness/PLAN.md) — the harness's own plan and stage
  history. Stays where it is; its closing discussion is the next conversation.
  Its §1 statement that `skel/` is an *immutable* Gold Standard is what §3 above
  supersedes.
- [`../harness/FUTURE.md`](../harness/FUTURE.md) — the layer swap, the vertical
  slice, and the horizon memo. §3 above promotes the horizon memo's intrinsic
  settlement criterion from future work to present need, and drops the vertical
  slice's reproduce-the-current-results assumption; both are recorded there in
  the standing correction at the file's head, so the notes below it are read
  through it.
- [`../harness/stages/10.md`](../harness/stages/10.md) — S10.1–S10.4 for level 3
  and its run; **S10.2** is the gate question this document answers by
  dissolving it, and that answer belongs in Stage 10's ledger as well as here.
- `*/CORRECTIONS.md` — the five per-layer correction records. They are the
  precedent for how a layer gets revised, and the methodology to keep:
  classify by cause before touching anything, verify against an existing
  precedent row, re-run each layer's `--check` afterwards.
- [`../ARCHITECTURE.md`](../ARCHITECTURE.md) — model access, wire protocol,
  observability. Unaffected; it describes the apparatus, which is what carries
  over.
