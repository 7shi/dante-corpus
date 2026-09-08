# Redesign: phrase enumeration over the layer stack

**Status.** A proposal, not a decision. Nothing here is adopted; `PLAN.md` §4
still stands as written. This file exists because the Layer-1 review produced a
design sketch that does not fit either of the directory's two existing document
kinds — it is not the plan (`PLAN.md` is the source of truth for *what is open*)
and it is not a read (`reads/` displays one passage at every layer). It is the
target structure being argued for, with the measurements that support it.

**Two premises, set by the operator (2026-09-09):**

1. **Preserving the existing artifacts is not a constraint.** Regenerating a
   layer is acceptable even where the new layer's information overlaps what is
   already frozen, and the time cost of that regeneration is accepted. This
   supersedes the working assumption of the preceding discussion — that the
   frozen TSVs are held fixed and the review proceeds by additive API changes
   only. Every cost figure below is stated so that decision can be revisited with
   numbers rather than impressions.
2. **Stop at phrases; do not build a complete tree rooted at the sentence.** The
   new layer enumerates phrases. Clause and sentence structure are not rebuilt in
   a new formalism, because they already exist — see §2.4. §3 is the argument for
   this; §4.1 is what it costs.

**Relation to the rest of the directory.** `PLAN.md` §4-2 asks *where a
hierarchical judgement gets written* and offers three candidate homes, decided
per phenomenon. [`reads/inf-1-1-9.md`](reads/inf-1-1-9.md) §Axes proposes that
this is the wrong shape, because all three devices are keyed to token boundaries
and none to the boundary of a grammatical word, so **one** device is wanted. This
file is that hypothesis carried forward into a design. It does not replace §4-2;
it is the thing §4-2 would be replaced *by*, if the hypothesis survives.

**Still unwritten.** How generation 1 is used while generation 2 is built —
which of the frozen layers may be shown to the model as input, and which are the
undecided positions it must not be anchored to. Discussed 2026-09-09, not yet
settled, not recorded here.

**On the numbers.** Every figure is derived from the frozen artifacts
(`morph/*/*.tsv`, `dep/*/*.tsv`, `src/*/*.txt`) and from
`dante_corpus.dep.sentence_groups`. Gold `skel/` is not consulted anywhere in
this file. The derivations were ad hoc scripts and are not committed — the same
caveat `PLAN.md`'s handoff records for the pilot read. They are re-derivable in
minutes; reproducibility is one of the things a cross-layer checker would fix.

---

## 1. The diagnosis, restated precisely

`PLAN.md` §1.3 names the root cause a **flat encoding**. That phrasing is
imprecise in one way worth correcting, because the correction is what the design
follows from.

**The stack is not missing a tree.** Layer 4 *is* a tree — a Universal
Dependencies tree with `head_line`/`head_token`, rejoining phrases across verse
lines. What it is missing is a different thing:

> There is a tree, and its nodes are tokens. **No node stands for a
> constituent.**

Every device the corpus improvised is an attempt to name a constituent that has
no node:

| device | what it is really doing | count |
|---|---|---:|
| Layer 2 composite POS (`preposition+article`, `verb+pronoun`, …) | folding several nodes **into** one token | **2,681** tokens |
| Layer 4 `fixed` | naming a constituent by marking its edges | **171** edges |
| Layer 4 `expl` | discarding a token that belongs to a constituent's head | **1,466** |
| Layer 3 spans | actual constituent nodes — but **NPs only, and per line** | 12,478 child spans |

The first and third pull in opposite directions: the composite POS exists because
a token is *larger* than a grammatical word, `expl` because a token is *smaller*
than one. Two compensations in two layers for one mismatch is what locates the
mismatch at Layer 1.

**Layer 3 is the encouraging part.** `NPSpan(line, start, end, head, children)`
is a constituent node, and the layer is already an *enumeration* rather than a
tree — nesting is derived at serve time by span containment. The corpus began
building constituent structure in the right shape and stopped at noun phrases,
inside a single line, with the granularity rule left unwritten (read finding H:
**8,319 of 12,478** child spans share their parent's head; nesting reaches depth
6). What §2 proposes is to carry that through, not to replace it.

---

## 2. The proposed structure

### 2.1 Terminals — a token, decomposed

The leaf is a single token, **except that contractions and clitic compounds are
split into their grammatical words**. Layer 2 already records the decomposition
in the lemma (`Nel → in+il`, `Rispuosemi → rispondere+mi`) but Layer 1 does not
act on it, and every consequence lands downstream.

The cost of splitting is small and exactly known:

```
composite-POS tokens          2,681
terminals after splitting     5,374   (+2,693)
corpus                      101,601 → 104,294   (+2.65%)
```

Almost all are two-way splits; three-way ones are `verb+pronoun+pronoun` (6) and
`preposition+article+noun` (4). The largest classes:

```
preposition+article 1,984   verb+pronoun 488   pronoun+pronoun 61
pronoun+preposition 58      adverb+pronoun 42  preposition+noun 12
```

**What the current merge costs, measured.** Of the 1,984 `preposition+article`
tokens, Layer 4 can only give the token one `deprel`, which goes to the
preposition half; the article half gets no edge. The noun it determines therefore
has **no determiner child in 1,666 cases**. The 318 exceptions carry a separate
`det:poss` (294) or an actual second determiner (24 — these want checking). So:

> The relation `la → via` is an edge at *Inf* 1:3 and is absent at *Inf* 1:1,
> and the only difference is that a contraction happened.

This holds under enumeration too: without the split, `il` cannot be a member of
the phrase it determines. The terminal decomposition is motivated independently
of what is built above it.

The tail of the composite-POS inventory also contains spacing variants
(`verb + pronoun` 2, `preposition + article` 1), which is Layer-2 hygiene rather
than a design matter, but it belongs on the list.

**This is the change that renumbers everything.** Splitting terminals invalidates
every `(line, token)` reference in `dep/`, `np/`, `skel/` and `case/`. Under
premise 1 that is a cost, not a blocker.

### 2.2 Phrases — enumerated, not a tree

Contiguous spans of terminals with a head: NP, VP, AdvP, PP. Enumerated
over-inclusively, with nesting derived by containment, in the shape `np/` already
has. **There is no root, no requirement that every terminal belong to a phrase,
and no requirement that the enumeration cover the sentence.**

**Most of the bracketing is already latent in Layer 4.** Taking the subtree of
every node in the dependency forest yields **40,654 groups of two or more
tokens**. The spans do not need to be annotated from scratch; they need to be
*projected*. What Layer 4 does not supply is the category label and the level
count.

**NP exists** (Layer 3). **PP is mechanical** — a `case` child marks it.
**VP has no counterpart anywhere in the corpus**; Layer 5 holds
predicate-argument tuples, which are argument structure, not a verb phrase.
Introducing VP requires deciding its relation to Layer 5 (§4.3).

### 2.3 The verse line is not a boundary, and barely needs to be crossed

The *Commedia* is verse, so phrases run past line ends. The question is how far.
Measuring the line span of every phrasal constituent implied by Layer 4 (21,869
of the 40,654, the rest being clausal):

| lines covered | count | share | cumulative |
|---:|---:|---:|---:|
| 1 | 18,841 | 86.15% | 86.15% |
| 2 | 2,222 | 10.16% | 96.31% |
| 3 | 676 | 3.09% | 99.41% |
| ≥4 | 129 | 0.59% | 100% |

**A phrase spanning four or more lines occurs 129 times in 21,869.** Layer 3's
per-line design was therefore nearly adequate and wrong at the margin: the
`NPSpan(line, start, end)` shape cannot express the 13.85% that cross a line at
all, which is why Layer 4 exists to rejoin them. A phrase span must carry
`(line, token)` at both ends, not one line and two offsets.

Dependency edges say the same from the other side — 82.54% of the 98,124 edges
are within a line, 96.24% within one line of their head, 98.69% within two. The
maximum in the corpus is 10.

### 2.4 What sits above phrases, and why it is not rebuilt

Clause and sentence structure are **not** part of the new layer, because both
already exist and neither is in dispute.

**Clauses are Layer 4's.** `advcl`, `acl`, `acl:relcl`, `ccomp`, `xcomp`,
`csubj`, `parataxis` mark subordination on the dependency edges — 18,785 clausal
constituents against 21,869 phrasal ones. Re-expressing them as a second
formalism would duplicate the information without deciding anything.

**Sentences are already computed and invisible.** `dante_corpus/dep.py:200`
`sentence_groups` splits on line-final `.`/`!`/`?`, sub-splits long sentences at
line-final `;`/`:`, and caps units at `MAX_UNIT_LINES = 12` with a **hard split**
when no soft break is available. Layer 4 was built inside these units — every
head must resolve within one — yet the unit is not stored in `dep/*.tsv`, is not
on `Canto`, and is not in `dante_corpus.__init__.__all__`. A consumer must import
a private function and recompute it. The sentence level therefore needs
**storing and exposing**, not designing. The 12-line cap is an implementation
artefact and should be dropped when it is.

**The terzina is underneath both.** Clausal constituents spike at multiples of
three lines — 20.45% at 3, 5.48% at 6, 1.12% at 9, 0.22% at 12 — and the
sentence unit far more sharply. Over all 100 cantos, 3,477 sentences:

| lines | count | share |
|---:|---:|---:|
| 3 | 2,054 | 59.07% |
| 6 | 800 | 23.01% |
| 9 | 182 | 5.23% |
| 12 | 41 | 1.18% |
| other | 400 | 11.51% |

**3,077 of 3,477 sentences (88.5%) are an exact multiple of three lines.** The
metrical unit and the syntactic unit coincide most of the time — a fact about
this text that a general design would not predict, and one a redesign should be
able to state rather than rediscover.

---

## 3. Why enumeration rather than a tree

### 3.1 The corpus's own charter forbids the tree

`PLAN.md`:135 states the line that keeps this work in the corpus:

> The corpus **enumerates and annotates** what the text's own grammar determines.
> Consumers **decide, normalize, and bind to external references** on top of that.

A complete tree with a unique root **forces a decision at every attachment
ambiguity**, because a tree has nowhere to be silent: every node has exactly one
parent, and undecided is not a value. Enumeration records what is determined and
omits what is not. The proposal is the charter's own shape.

Two of the pilot read's findings stop being problems under it:

- **Finding E (ellipsis).** *Inf* 1:7 `poco è più morte` gaps the predicate. A
  tree needs a node for a predicate that has no token; the current stack instead
  promotes `morte` to head the clause and emits `(7.2) morte subj [poco]`, which
  is not a possible reading. An enumeration is not obliged to produce a phrase
  where the language produced none.
- **Finding H (granularity).** A tree must pick one level count. An enumeration
  can answer *all projections*, which is a complete and checkable rule — the
  thing `np/README.md`'s "over-inclusively" was reaching for and never stated
  (§4.2 bounds it).

### 3.2 The cost is bounded and measured

A phrase is a contiguous span, and 1,522 of the 40,654 dependency subtrees
(3.74%) are not contiguous. Under enumeration those are not a mechanism to
design; they are simply spans that get enumerated as their contiguous core around
the head. The loss:

```
token memberships across all 40,654 subtrees   347,287
memberships falling outside the contiguous core   9,495   (2.73%)
subtrees affected                                 1,522
```

**2.73%, known in advance.** A complete tree must instead give each of the 1,522
a mechanism — discontinuous constituents, traces, or dependency edges kept
alongside — and pay for it everywhere.

### 3.3 An argument that does not work, recorded so it is not retried

It is natural to suppose that stopping at phrases is what buys contiguity: cut
the descent at clausal children and the crossings should go away. **Measured, it
is worse**, because removing a clausal subtree from the middle of a span leaves a
hole where it stood:

```
full subtrees                      40,654   discontinuous 1,522  ( 3.74%)
phrase projection, cut at clausal  39,506   discontinuous 4,486  (11.36%)
```

Contiguity is not bought by stopping at phrases. It is bought by **dropping the
obligation to cover everything**, which is §3.2.

---

## 4. What the design does not settle

### 4.1 Nothing enforces consistency between enumerated phrases

This is the price of §3.1 and the top open question. A tree makes incoherence
unrepresentable: two contradictory analyses cannot both be attached. An
enumeration can hold two overlapping phrases that no single analysis licenses,
and nothing in the layer notices.

**Layer 3 is already in that state.** Finding H is exactly this failure — the
same NP-plus-relative-clause shape enumerated with 3 spans at *Inf* 1:8 and 7 at
*Inf* 1:9, with no structure to make the disagreement visible.

So the cross-layer checker discussed as `layers/`'s first tool is not a
convenience here; it is **part of the design**. It takes over the coherence role
a tree would have played, and the design is only as good as the checks that
replace the tree. Naming those checks is work this file does not do.

### 4.2 "All projections" needs a bound

Enumerating every projection is well-defined but not automatically finite in a
useful way: Layer 3 already reaches depth 6, and 8,319 of 12,478 child spans
share their parent's head — the peeling shape, one determiner or adjective per
level. Extending that to VP and AdvP multiplies it. A rule is needed for which
projections are worth materialising, and unlike the tree case it can be a rule
about *storage*, not about *truth* — which is why it is a smaller problem here
than §4.1.

### 4.3 VP against Layer 5

Layer 5 is predicate-argument structure over tokens. A VP node covers overlapping
ground without being the same object. Either Layer 5 is re-expressed over the new
phrases, or the two coexist and their relationship is stated. Nothing in the
current stack decides this, because nothing in the current stack has a VP.

### 4.4 Non-projectivity — downgraded, not dismissed

The 1,522 discontinuous subtrees (3.74%) were the largest threat while the target
was a tree. Under enumeration they cost §3.2's bounded 2.73% instead. They are
still worth watching, because of where they fall:

```
tokens skipped:  1 → 566    2 → 359    3 → 205    4 → 145    ≥5 → 247
by deprel:  nsubj 365  obj 289  xcomp 231  ccomp 182  conj 112  obl 101
            amod 35  advcl 33  attr 31  acl:relcl 25  cop 23  advmod 18
```

`nsubj` and `obj` lead, and those are precisely what a knowledge graph and a
translation alignment need. The fourth line of the poem is already a double
instance:

```
Ahi quanto a dir qual era è cosa dura
  4.2  quanto  advmod -> 4.9 dura
  4.4  dir     nsubj  -> 4.7 è
  4.8  cosa    attr   -> 4.7 è
```

`quanto … cosa dura` and `a dir qual era [esta selva …]` interleave: the subtree
of `dir` skips 4.7–4.9, the subtree of `cosa` skips 4.3–4.7. Hyperbaton is
unavoidable in verse. Under enumeration each is recorded as its contiguous core
and the crossing stays on Layer 4's edges, where it already is.

---

## 5. Cost, stated once

| | |
|---|---|
| terminals to split | 2,681 tokens → 5,374 (+2.65% corpus size) |
| references invalidated | every `(line, token)` in `dep/`, `np/`, `skel/`, `case/` |
| spans to annotate from scratch | little — 40,654 groups are projectable from Layer 4 |
| labels to assign | NP (have it), PP (mechanical), AdvP and VP (new) |
| membership lost to contiguity | 9,495 of 347,287 (2.73%), in 1,522 spans |
| clause level | not rebuilt — stays on Layer 4's edges |
| sentence level | already computed (`sentence_groups`); needs storing and exposing |
| in-repo API call sites touching layer accessors | **19** (`dep()` 6, `np()` 4, `morph()` 4, `case()` 3, `skel()` 2) |
| external consumer | `dante-analyze` — dependency surface **not surveyed**; needed before any breaking change |

The in-repo cost is small; artifact regeneration is the expensive half, and
premise 1 accepts it. The one genuinely unknown figure is the external
consumer's.

---

## 6. What would falsify this

- **The checks cannot replace the tree.** §4.1 is the load-bearing bet. If no
  practical set of cross-layer checks catches the incoherences a tree would have
  made unrepresentable, enumeration reproduces finding H at three phrase types
  instead of one, and the tree is worth its cost after all.
- **The grammatical-word hypothesis fails on a full family.** `reads/`'s next
  read should measure the pronominal verbs in full (`expl` 1,466 vs
  `verb+pronoun` 488). If the split turns out to be conditioned by something
  grammatical rather than by the scribe's spacing, §2.1 loses its motivation.
- **The 2.73% is in the wrong places.** §4.4's `nsubj` 365 and `obj` 289 are what
  downstream needs most. If the discontinuous cases are disproportionately the
  ones a knowledge graph or a translation must resolve, a bounded average loss is
  the wrong summary statistic.
