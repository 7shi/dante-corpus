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
3. **Generation 2 must not depend on generation 1 at rebuild time (operator,
   2026-09-09).** The finished corpus is generation 2 alone; a pipeline that can
   only be re-run while the old files still exist has quietly turned "ship a
   finished corpus" into "ship a finished corpus, plus keep the old one forever
   so the new one stays reproducible." Old Layer 1–5 may be used **once**, as
   bootstrap material during construction — a warm start for the model, a
   precedent to check a fresh annotation against — but no generation-2 layer's
   *definition* may name an old-generation file as an input. Where earlier
   drafts of this file did that (§2.1's L2 split, §2.2's L3 projection), they are
   corrected below.

**Relation to the rest of the directory.** `PLAN.md` §4-2 asks *where a
hierarchical judgement gets written* and offers three candidate homes, decided
per phenomenon. [`reads/inf-1-1-9.md`](reads/inf-1-1-9.md) §Axes proposes that
this is the wrong shape, because all three devices are keyed to token boundaries
and none to the boundary of a grammatical word, so **one** device is wanted. This
file is that hypothesis carried forward into a design. It does not replace §4-2;
it is the thing §4-2 would be replaced *by*, if the hypothesis survives.

**Terminology (operator, 2026-09-09).** From here on, `L1`, `L2`, `L3`, … name
the *rebuilt* layers this file designs. `Layer 1`, `Layer 2`, … keep naming the
existing, frozen generation (`api.py`, `morph/*.tsv`, `dep/*.tsv`, …). The two
numbering schemes are deliberately not required to line up token-for-token —
see §2.1.

**Still unwritten.** Premise 3 settles the general shape — bootstrap-only, never
a rebuild-time input — but not the specific split PLAN.md's handoff drafted:
which of the frozen layers are safe to show the model even as a one-time warm
start (tentatively tokens, lemma decomposition, Layer-4 bracketing,
`sentence_groups`) and which are contaminated positions it must not anchor to
(`cop`/`attr`, the four-way locution split, Layer-3 granularity, participle POS,
`che` POS, `expl`). Discussed 2026-09-09, not yet settled, not recorded here.

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

### 2.1 Terminals — L1 (tokens, punctuation included) and L2 (grammatical words)

**L1 is `tokenize()`'s full output, indexed** — alpha tokens and punctuation
tokens alike, each with its own `(line, token)` address. This is not the same
sequence as old Layer 1's `Line.tokens` (`api.py:52`), which applies `has_alpha`
before indexing and so never assigns punctuation a position at all; L1's
numbering therefore does not line up with old Layer 1's. See the punctuation
measurement below.

**L2 splits contractions and clitic compounds into their grammatical words, and
carries a back-reference to the L1 token it came from.** Under premise 3 this is
generation 2's own step, not a lookup into old Layer 2's lemma field — but it
should also be **independent of grammatical analysis** (operator, 2026-09-09),
kept out of the POS-tagging/dependency pass entirely, so a mistake in one is
never entangled with a mistake in the other. That independence is not an
aspiration; the vocabulary is closed enough to make it a fact. Old Layer 2's
2,681 composite-POS tokens reduce to **442 distinct wordforms** (case-folded) —
`del` 569, `al` 549, `nel` 310, `dal` 172, `col` 109, … — and **423 of 442
(95.7%) have exactly one recorded split**, with no dependence on the sentence
around them. Only 19 wordforms show more than one, and most of those are old
Layer 2's own spelling noise on the same lemma (`dimmi` as `dire+me` /
`dire+mi`) rather than real ambiguity; `dal` showing both `da+il` and `di+il` is
very likely an outright error in the old annotation (`dal` is not a form of
`di`), and `nel` genuinely splits two ways (`in+il` the ordinary contraction vs.
`ne+lo` the pronoun compound) — real but rare. **L2 is therefore a static
lookup table plus a handful of flagged exceptions, structurally the same device
`tokenizer.py`'s `quote_cases.txt` already is for apostrophe normalization** —
not a grammatical judgement, and not an LLM call. Old Layer 2's decomposition
data is precedent for building and checking that table (§2.1's cost figures
below are counted from it), not an input the running split reads. L2 is an
ordered list of `(l1_index, text)` pairs —
the L2 token number is the position in that list and is never stored separately,
only `l1_index` is data. A composite L1 token produces **several** L2 entries
sharing one `l1_index` (1:many); every other L1 token, including punctuation,
carries straight through as exactly one L2 entry (1:1). Worked example, *Inf* 1:1
`Nel mezzo del cammin di nostra vita`:

```
L1   0:Nel  1:mezzo  2:del  3:cammin  4:di  5:nostra  6:vita
L2   (0,in) (0,il) (1,mezzo) (2,di) (2,il) (3,cammin) (4,di) (5,nostra) (6,vita)
```

`Nel` (L1 index 0) and `del` (L1 index 2) each yield two L2 entries; every other
L1 token yields one. The mapping is recorded, not discarded — nothing downstream
that needs the original token (old Layer 4's `head_line`/`head_token`, say) loses
the ability to name it.

**L2 only splits; it never merges (operator, 2026-09-09).** `l1_index` is always
a single integer, never a tuple — so a many:1 direction (several L1 tokens = one
grammatical word) is not a shape L2 takes, even though the corpus already has
that phenomenon: old Layer 4's `fixed` relation, **170 groups**, almost all
complex prepositions (`in su`, `dietro a`, `presso a`, `per entro`, …), 169 of
size 2 and one of size 3 (*Par* 32:133 `Di contr'a`), every one contiguous.
Merging was tried at this level and measured to conflict with splitting: **37 of
170 fixed groups (21.8%) have a member that is itself a composite-POS token**.
*Inf* 7:130 is the clean case —

```
130:7  al = a+il  (preposition+article), fixed head
130:8  da          (preposition),        fixed child
```

— the multiword expression is `a da` ("at last"), not `al da`: only the `a` half
of `al` participates, `il` does not. A tuple `l1_index` naming both L1 tokens
would claim `il` belongs to the fixed group, which is false. Decomposition must
therefore go all the way down first — every token split to its finest
grammatical-word grain — before anything is put back together. **The merge
stays exactly where the corpus already puts it: a `fixed`-style edge one layer
up (L4, over L2 entries), not a second, conflicting join built into L2 itself.**
L4 gets this cheaply for the 133 non-conflicting groups and correctly for the 37
conflicting ones, because at the L2 level `a` and `il` are already two separate,
addressable entries and the edge can point at exactly `a`.

**L2 also normalizes apocope and elision — to the surface form, not the lemma
(operator, 2026-09-09).** `i'` is `io` with its final vowel restored, and
that stops at `io`; it does not continue on to a lemma, because for this
wordform they happen to coincide. They do not always: `son` restores to
`sono`, and `essere` stays where it already is, as the lemma a later,
independent pass assigns. The scope is larger than the apostrophe-marked cases
alone. Measured over old Layer 2's `apocope`/`elision`-noted, non-composite
rows:

```
apostrophe-marked   (l', 'l, ch', d', s', m', t', 'n, com', i', …)   300 wordforms   7,047 tokens
no apostrophe       (son, eran, avea, vuol, gran, cor, tal, …)     1,386 wordforms   6,909 tokens
```

The apostrophe-marked set is exactly as clean as §2.1's split table — the
boundary is visible, restoration is one vowel, and lemma is usually the same
closed-class word anyway. The no-apostrophe set is not: **477 of 1,510
distinct (word, lemma, pos) rows have a lemma that is not a simple extension of
the surface spelling** — `son`/`eran`/`avea`/`vuol`/`furon`/`convien` restore
to inflected forms (`sono`, `erano`, `aveva`, `vuole`, `furono`, `conviene`)
that the lemma (`essere`, `volere`, `convenire`, …) never records, because the
lemma is the infinitive and the restored form is not. Old Layer 2 is therefore
precedent for the split table but **not sufficient data** for the
normalization table — the target text has to be constructed, not read off an
existing column.

**A further 159 wordforms cross more than one POS** (`l'` → `lo`/`la`, `fuor` →
adverb `fuori` / verb, `qual` → four different POS across its occurrences), and
for these the restored spelling depends on which reading applies — `l'`
restores to `lo` or `la` only once gender is known.

**Desk check, three lines (operator, 2026-09-09): the 159 are not an exception,
they are the reason the pipeline has three steps in this order.** Worked by hand
against *Inf* 1:1 and *Inf* 1:25, one step at a time, no batching (per the
one-step-one-job principle above):

```
1. split          — L1 -> L2, closed-vocabulary, as designed above
2. POS             — per L2 entry, independent grammatical classification
3. normalize       — restore apocope/elision, keyed on (L2 text, POS from step 2)
```

*Inf* 1:1 `Nel mezzo del cammin di nostra vita`:

```
L1        0:Nel 1:mezzo 2:del 3:cammin 4:di 5:nostra 6:vita
1.split   (0,in)(0,il) (1,mezzo) (2,di)(2,il) (3,cammin) (4,di) (5,nostra) (6,vita)
2.POS     in=prep il=art mezzo=noun di=prep il=art cammin=noun di=prep nostra=adj vita=noun
3.normal. in→in il→il mezzo→mezzo di→di il→il cammin→cammino di→di nostra→nostra vita→vita
```

*Inf* 1:25 `così l'animo mio, ch'ancor fuggiva,` — no composite tokens, so step 1
is the identity, but step 3 needs step 2's answer for `l'`:

```
L1        0:così 1:l' 2:animo 3:mio 4:, 5:ch' 6:ancor 7:fuggiva 8:,
2.POS     l'=article, gender/number undetermined until agreement with 2:animo
          (masc.sg) is resolved in the same pass
3.normal. l'→lo (only decidable once step 2 has fixed masc.sg); ch'→che;
          ancor→ancora; everything else passes through unchanged
```

**So the 159 wordforms are not a scoped exception after all — normalizing
strictly after POS, for every wordform, is simply step 3 following step 2 in a
three-step pipeline.** No `(wordform, pos)`-keyed carve-out is needed; the
ordering already gives every wordform its POS before normalization asks for it.
The other 1,527 wordforms just have a trivial step 2 → step 3 dependency (the
POS doesn't change the answer), which is not a different mechanism, only a
simpler case of the same one.

**Concrete task, following from the above (operator, 2026-09-09).** Build the
442-wordform split table, the per-L2-entry POS classification, and the
~1,686-wordform normalization table as **three separate passes in that order**,
with no view of old Layer 2, then **diff each against old Layer 2's
composite-POS/lemma field** as the precedent check — the same methodology
already standing in `PLAN.md` §2 and every `*/CORRECTIONS.md`: classify by
cause before touching anything, verify each row against an existing precedent
row. Three outcomes fall out, not two: the new table agrees (423 wordforms for
the split table, expected); the new table disagrees and old Layer 2 is the one
that's wrong (`dal`'s `di+il` is the found candidate); or the disagreement is
genuine synchronic ambiguity the table must keep both branches for (`nel`, and
the 159 cross-POS wordforms above, now resolved by pipeline order rather than a
carve-out). Because normalization only ever consumes step 2's POS and never the
other way around, a disagreement is never confounded with a POS-tagging
mistake — the failure surface this task exists to keep small.

**The execution mechanism already exists (operator, 2026-09-09): `harness/`'s
fixed-context step** ([`../harness/stages/09.md`](../harness/stages/09.md) §2).
Each of the three steps above, for each wordform, is one step
`P -> O -> State Σ ()`: $P$ the single instruction for that step ("split this
token" / "classify this entry's POS" / "restore this entry's spelling"), $O$
old Layer 2's row for it (bootstrap precedent, premise 3) plus, for step 3, step
2's own output, $\Sigma$ the candidate entry, output the accepted text — and,
per §9's design, **no transcript carries between steps or between wordforms**,
because each is independent and a growing history buys nothing a stateless step
doesn't already have. This is not chat-with-memory scaled down; it is the same
architecture Stage 9 built for Layer-5 repair, pointed at a smaller, closed
problem — up to 3 × (442 + ~1,686) steps, each with a verdict (agrees /
precedent-is-wrong / genuine ambiguity) and no per-iteration context growth,
exactly the shape §2's `step` signature already gives for free.

**One step, one job, no batching (operator, 2026-09-09).** Neither the
wordforms nor the three jobs are compressed into fewer, larger requests — one
call doing several wordforms, or splitting-and-classifying-and-normalizing in
one shot, is several chances for one bad output to contaminate the rest,
against harness's own finding that batching is exactly where failures
concentrate (`harness/stages/09.md` §2, "Full rows, not a patch": 68% of the
paper it reviews attributes its failures to botched multi-key merges — errors
from doing several updates in one step). Wall-clock cost is not a reason to
batch here: this work already runs as repeated loops across a stage history
spanning weeks (`harness/stages/01.md` through `10.md`, 2026-08 to 2026-09), so
shaving one more pass does not change the project's actual timeline, and is not
worth trading away the isolation a one-job-per-step design buys.

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

**What this does and does not renumber.** Old Layer 1–5 keep the addressing they
already have; nothing here edits `dep/`, `np/`, `skel/` or `case/` in place, and
under premise 1 rebuilding a parallel generation rather than patching the old one
is accepted cost, not a blocker. What *does* shift is L1 itself against old Layer
1 — L1 has its own numbering (§2.1 above), not a superset or subset of
`Line.tokens`'s, because punctuation occupies positions old Layer 1 never
assigned. L2's split is not a second blind renumbering on top of that: every L2
entry carries the `l1_index` it came from, so the old-to-new correspondence is
data, not something a consumer has to reconstruct.

**Punctuation is why L1 and old Layer 1 diverge (operator, 2026-09-09).**
`tokenize()` (`tokenizer.py:53`) already splits punctuation into its own token
strings; the only filter old Layer 1 applies is `has_alpha` at `api.py:52`,
which drops them *before* indexing. `PLAN.md`'s Layer-1 finding — "punctuation
has no token index, so no layer can cite it" — is therefore not a tokenization
gap but an indexing one, and it is L1, not L2, that fixes it: L1 is
`tokenize()`'s output taken whole. Since the design stops at phrases rather than
a full sentence tree, punctuation belongs **beside** phrase-structure objects,
not beneath them — a comma separates coordinated phrases, a colon introduces
one, quotation marks bound a span of direct discourse; none of that is a
property of any single token. Measured over the whole corpus:

```
alpha tokens (current Line.tokens)                       101,601
punctuation tokens (tokenize(), non-alpha, non-space)      17,434
  ,  8,513   .  3,275   ;  1,628   «/» 1,062/1,062   :    988
  ?    278   !    232   ‘/’  109/109   “/”   51/51   '     51
  —     18   (/)     3/3    -      1
```

**Every quotation-mark pair is exactly balanced** — `«`/`»` 1,062/1,062,
`‘`/`’` 109/109, `“`/`”` 51/51. The closing partner Layer 1 would need to bound
a quoted span as a terminal-delimited constituent already exists one-to-one;
this is the address the open survey item "the quotes hierarchy" (`PLAN.md`
§4-1) has been missing.

### 2.2 Phrases — enumerated, not a tree

Contiguous spans of terminals with a head: NP, VP, AdvP, PP. Enumerated
over-inclusively, with nesting derived by containment, in the shape `np/` already
has. **There is no root, no requirement that every terminal belong to a phrase,
and no requirement that the enumeration cover the sentence.**

**Most of the bracketing is latent in a dependency tree — old Layer 4 shows this,
but L3 must not be built from it.** Taking the subtree of every node in old
Layer 4's dependency forest yields **40,654 groups of two or more tokens**: the
measurement that shows spans need not be annotated from scratch, they can be
*projected*. Under premise 3, though, the pipeline that produces L3 has to
project from **L4** — generation 2's own rebuilt dependency layer over L2's
grammatical words — not from old Layer 4 over old tokens; a production route
through the frozen file would make L3 permanently unreproducible without it.
This puts L4 ahead of L3 in build order despite the numbering, and old Layer 4
still earns its keep as premise 3's bootstrap case: it is a plausible warm start
for annotating L4 itself (the projection counts above stand as the size of that
bootstrap's payoff), just not an input L3 reads. What neither old nor new Layer
4 supplies on its own is the category label and the level count.

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
| terminals to split (L1 → L2) | 2,681 L1 tokens → 5,374 L2 entries (+2,693), each carrying its `l1_index` back-reference |
| multiword merges (`fixed`) | not L2's job — stays a relation over L2 entries at L4; 170 groups, 37 (21.8%) overlap a composite-POS split and need the finer L2 grain to attach correctly |
| punctuation terminals to index (old Layer 1 → L1) | 17,434, currently unindexed; already tokenized, only `has_alpha` drops them — balanced quote pairs 1,062/1,062, 109/109, 51/51 |
| old-generation artifacts | left as-is — `dep/`, `np/`, `skel/`, `case/` keep old Layer 1–5 addressing; the new generation is parallel, not an in-place edit |
| build order | L4 (dependency) precedes L3 (phrases) despite the numbering — L3 projects from L4, not from old Layer 4 |
| spans to annotate from scratch | little, once L4 exists — old Layer 4 shows 40,654 groups are projectable in principle, a bootstrap case for building L4, not an input L3 reads |
| labels to assign | NP (have it), PP (mechanical), AdvP and VP (new) |
| membership lost to contiguity | 9,495 of 347,287 (2.73%), in 1,522 spans, measured on old Layer 4 as an estimate of L4's expected shape |
| clause level | not rebuilt — stays on L4's edges |
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
