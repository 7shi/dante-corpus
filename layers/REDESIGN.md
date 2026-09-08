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
numbering therefore does not line up with old Layer 1's. Full diagnosis, the
corpus-wide punctuation census, and (as of 2026-09-09) the implementation:
[`L1.md`](L1.md).

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

**Step 2 itself should be staged, not one classification (operator,
2026-09-09).** Old Layer 2 asked for the whole row — POS, gender, number,
person, tense, mood — in a single judgment, and §6's participle finding is
what that produces: deciding `verb`, `present participle`, `m.`, `sg.`
together gives the model enough surface area to substitute `adjective` for
`verb`+participle right at the one boundary where the two readings overlap (a
participle used predicatively reads like an adjective). The fix is not asking
for less, it is asking **in stages** — a coarse category first, from a closed
set, then a further classification *within* that category (verb:
tense/mood/person/number; noun: gender/number; …), with the granularity of
the second stage decided separately, later. A coarse-only first pass is also
what would have kept §6's 39-value drift closed in the first place.

**The participle/adjective boundary needs pinning down explicitly, not just
staging (operator, 2026-09-09).** Staging alone does not settle it: a
participle stays `verb` at the coarse stage only if the coarse-stage prompt
or a one-shot example states the rule, because "is this a verb or an
adjective" is exactly the judgment §6 shows the model already answers both
ways for the identical wordform (`smarrito` split 4/4). A bare few-shot with
no participle example would just relocate the same three-way split from a
`pos` value to a coarse/fine boundary instead of closing it. The design needs
a stated convention — participles are `verb` at the coarse stage regardless
of predicative or attributive use, with the surface reading recorded as a
fine-grained tag under `verb`, never by relabeling the coarse category — and
a one-shot example enforcing it, not left implicit the way old Layer 2 left
it.

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

**Rollout: Canto 1 first, starting at lines 1-9 and widening gradually
(operator, 2026-09-09) — before any of the three passes runs corpus-wide.**
Every measurement in this file was corpus-wide from the start, but running
the three-step pipeline itself corpus-wide first would repeat the mistake
premise-checking exists to avoid: 442 + ~1,686 wordforms is enough surface
area that a systematic prompt or pipeline-ordering error could pass a spot
check and still be wrong at scale. `reads/inf-1-1-9.md` already established
the same discipline for reading — nine lines, findings measured corpus-wide
only *after* being seen concretely — and the split/POS/normalize build
should follow it rather than start from the opposite end. Concretely: run
all three passes over *Inf* 1:1-9 only, inspect every wordform's split, POS,
and normalization by hand against the source (the same worked examples
above, *Inf* 1:1 and 1:25, are the first two data points), widen to the rest
of *Inf* 1 (136 lines, still small enough to read end to end), and only then
move to the full corpus. Corpus-wide numbers already justify the design;
what a single-canto pass buys is catching a systematic error — a prompt
that's subtly wrong in a way a handful of wordforms won't reveal — before
it's baked into 442 + ~1,686 calls' worth of output.

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

**The split step's output should be keyed by the word, not by `l1_index`
(operator, 2026-09-09).** Writing the answer as `1:in`, `1:il` — echoing the
numeric index back for each half of the split — puts load on the model that
the task doesn't need: getting the split right and copying a number
correctly are two different failure modes bundled into one answer, and only
the first is what step 1 is actually asking. The step should instead ask for
`nel:in+il` — the surface word as the key, its split as the value — with
`l1_index` attached by code afterward from the wordform's own position, the
same way alignment already anchors Layer 3 spans to tokens without asking
the model to state indices. **Retry only on ambiguity, not by default**: if
a wordform's split isn't uniquely determined in isolation (the `nel`
two-way case, §2.1 above), the single retry turn says so explicitly and asks
the model to pick, rather than building index-correctness into every one of
the 442 calls to cover the rare case. This is an implementation detail of
step 1 specifically — it does not change the split table's scope or the
three-step ordering.

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
is accepted cost, not a blocker. L1's own numbering diverges from old Layer 1's
because punctuation occupies positions old Layer 1 never assigned — the full
diagnosis, the corpus-wide punctuation census, and why punctuation belongs
beside phrase-structure objects rather than beneath them are in
[`L1.md`](L1.md), not repeated here. L2's split is not a second blind
renumbering on top of that: every L2 entry carries the `l1_index` it came
from, so the old-to-new correspondence is data, not something a consumer has
to reconstruct.

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

**Old Layer 3's fused-enclitic-pronoun mechanism is a compensation for old
Layer 1, and L2's split table already removes what it compensates for.**
`np/README.md` (*What it does*, *Output*, *Check*) describes a dedicated
device: because a token like `venendomi` (*Inf* 1:59, `morph/inferno/01.tsv:59`
`venire+mi`, `pos=verb+pronoun`) is one Layer-1 token with no position of its
own for the bound pronoun, Layer 3 generates a synthetic single-token mention
— `np/inferno/01.tsv:59` stores `2 2 2 +mi`, a row whose `text` is not a
source substring by construction and is checked against the host's Layer-2
lemma components instead of the tokens (`clitic_mentions()`,
`dante_corpus/np.py`; a dedicated hard-check branch and a `--fix-clitics`
reconciliation exist solely for this row shape). **This is the same class of
device §1's table already names** — a composite-POS token folding several
grammatical words into one — worked around one layer up because Layer 1 has
nowhere to put the second word. Under §2.1's design, `venire+mi` is exactly
the `verb+pronoun` shape the L2 split table covers (488 tokens, 372 distinct
wordforms, part of the 442-wordform table) and it becomes **two ordinary L2
entries** — `(58,venire)`, `(58,mi)` in `(l1_index, text)` form — each with a
real address. L3, rebuilt over L2 rather than over old Layer 1 tokens, would
enumerate the pronoun as an ordinary entry the way it enumerates any other
one-word NP; there is no missing position left to synthesize a mention for,
and the `"+"`-prefixed sentinel, its separate hard-check branch, and
`--fix-clitics` have no counterpart to build. Old Layer 3's own design notes
call this "Layer 3's first build-time dependency on Layer 2 that touches the
artifact itself" — under premise 3 that dependency is gone too, absorbed into
L2's own split step before L3 ever runs.

**NP exists** (Layer 3). **PP is mechanical** — a `case` child marks it.
**VP has no counterpart anywhere in the corpus**; Layer 5 holds
predicate-argument tuples, which are argument structure, not a verb phrase.
Introducing VP requires deciding its relation to Layer 5 (§4.3).

**Not a narrower NP — a second instance of finding H's own problem (operator,
corrected 2026-09-09) — deferred.** Finding H's diagnosis was never "NP is
too small," it was **old Layer 3 never had an explicit rule for what
hierarchy to build**: *Inf* 1:9 gets a relative clause folded straight into
one NP span (`np/inferno/01.tsv` enumerates `l'altre cose ch'i' v'ho scorte`
as a single nested NP, clause and all) while a sibling line gets a flatter
reading, and nothing in the layer says which is the rule. **The participle
case is the same gap surfacing again, not a second, unrelated axis**: whether
a participle-headed phrase's object nests inside the NP the way *Inf* 1:9's
relative clause does, sits outside it as a separate constituent, or is left
to Layer 4's edges the way §2.4 already treats clauses, is exactly the
undefined choice §4.2 ("'All projections' needs a bound") is waiting to
settle — this is one more concrete case for that section to resolve, not a
new question next to it. **Deferred to a later session, not decided here**:
folding the participle-object question into §4.2's bound, alongside the
relative-clause case, once both are on the table together.

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

## 6. Old Layer 2 review, continued past the pilot (2026-09-09)

`PLAN.md`'s *Method* — examine a layer against a concrete passage, measure
every observation corpus-wide before writing it down — was applied to old
Layer 2 (`morph/`), the review deferred when the session turned to designing
L1/L2 instead (`PLAN.md`:83-94). Entry point: *Inf* 1:3 `smarrita`.

**Finding: past participles are encoded three incompatible ways.** The same
grammatical function — a past participle, whether verbal (passive/compound
tense) or adjectival (predicative) — appears under three different `pos`
values corpus-wide:

| encoding | rows | example |
|---|---:|---|
| `pos=verb`, `tense=past`, `mood=participle` | 724 | the majority convention |
| `pos=participle` (the POS column itself holds "participle"; `tense`/`mood` empty) | 25 | *Inf* 5:49 `portate`, 10:88/90 `mosso`, 17:34 `venuti`, 34:16 `fatti` |
| `pos=adjective` | 573+ | *Inf* 1:3 `smarrita` |

Within the third encoding, the **lemma itself splits**: some rows lemmatize to
the adjective's own form (`smarrito`), others to the verb infinitive
(`smarrire`), for the identical wordform. **104 distinct wordforms carry both
treatments** with no visible criterion — `smarrito` itself is split 4/4
(`inferno/02.tsv:64`, `24.tsv:116` → lemma `smarrito`; `05.tsv:72`,
`10.tsv:125`, `13.tsv:24`, `purgatorio/12.tsv:35` → lemma `smarrire`). One row
(`purgatorio/08.tsv:63` `smarrita`) even keeps `mood=past participle` while
`pos=adjective`, crossing the second and third encodings in a single row.

**Finding: the POS vocabulary is not closed, beyond what `README.md` already
disclosed.** `--check` collects `pos` but does not enforce it
(measure-then-freeze, `morph/README.md` "Check"). Measured directly, the
column holds **39 distinct values**, not a stable open set:

- subtype leakage onto the main axis: `relative pronoun` (176) beside
  `pronoun` (12,316) — `che` alone splits `pronoun` 1,953 / `relative pronoun`
  116 / `conjunction` 1,618 / `adjective` 10, with no distinguishing rule
  found; `proper noun` (807) beside `noun` (17,673); `possessive adjective`
  (6) and `demonstrative adjective` (1) beside `adjective`
- spacing duplicates: `verb+pronoun` 488 vs `verb + pronoun` 2;
  `preposition+article` 1,984 vs `preposition + article` 1 (already noted as
  Layer-2 hygiene in §2.1)
- singleton mistags: `determiner` (2), `particle` (1), `number` (1)

The participle split and the vocabulary drift are one phenomenon seen from
two sides: `participle` and `past participle` are used inconsistently as
*both* a `pos` value and a `mood` value for the same grammatical fact.

**Context from the operator (2026-09-09), recorded because it bears on
priority, not on the measurement above — and then corrected by the very next
finding.** This was never reviewed because the early build prioritized
establishing a corpus-wide picture over per-tag precision, on the working
assumption that later layers don't lean heavily on the `pos` field. **`case/`
is a direct counterexample** (operator, 2026-09-09): its build step reads
Layer 2's `pos` column verbatim as the gate for which tokens it ever sees
(`case/case.py:11`), so the `che` mistag below is not inert drift — it
silently narrows `case/`'s coverage, exactly as `reads/inf-1-1-9.md` finding
B already noted before this file corrected *how*. The general claim
("downstream barely uses `pos`") does not hold for every consumer and should
not be used to deprioritize a `pos`-vocabulary fix without checking the
specific consumer first. Whether it is worth fixing old Layer 2 on its own,
or only matters once folded into rebuilt L2's POS-classification step (§2.1
step 2), is not decided here.

**`che`'s mistag and `case/`'s sparseness are the same root cause, not two
items.** [`reads/inf-1-1-9.md`](reads/inf-1-1-9.md) finding B already measured
**225 positions** where `che`/`ch'` fills a nominal role (`nsubj`/`obj`/`obl`)
but is tagged `pos=conjunction` instead of `pronoun`/`relative pronoun` — the
same three-way POS split as above, on the corpus's single highest-frequency
function word. That read states the consequence as "the case annex is sparse
over pronoun-POS tokens" — checked here and **imprecise**: `case/` is not
sparse over pronoun-POS tokens at all. Measured directly, every token whose
Layer-2 `pos` contains `pronoun` (plain `pronoun` 12,316, `relative pronoun`
176, and every composite carrying it — `verb+pronoun` 488, `pronoun+pronoun`
61, …) has **exactly one** `case/` row, matching `case/README.md`'s own
"complete and closed" claim (13,157 keys, an exact match to that count) and
`case/case.py:11`'s stated construction: *"one pronoun-POS token, read off
Layer 2's own `pos` column."* **The gate is Layer 2's `pos` tag itself, read
verbatim, not a coverage gap inside `case/`.** A `che` mistagged `conjunction`
is not a pronoun short one case value; it is never presented to `case/`'s
build step at all, because that step only ever sees what Layer 2 already
called a pronoun. `case/`'s own sparseness (one row per pronoun, not per
token) is by design and is complete on its own terms; what reaches it is
what Layer 2's POS split already decided upstream.

**Status: measured, not corrected.** The participle split, the POS-vocabulary
drift, and the `che`/`case` gating are three faces of one thing — old Layer
2's `pos` column is not a closed vocabulary, and everything downstream that
keys off it (here, `case/`'s build gate) inherits whatever the column
decided, silently. Where this gets written up permanently
(`morph/CORRECTIONS.md`, a dedicated old-Layer-2 review note, or absorption
into rebuilt L2's POS-classification step, §2.1 step 2) is still open.

---

## 7. Old Layer 4 review (2026-09-09)

Method applied to old Layer 4 (`dep/`): *Inf* 1:2 `mi ritrovai` (`dep/inferno/01.tsv:67-68`)
tags `mi` `deprel=expl`, `head=(2,2)` — the same token, the same relation
`PLAN.md` §1.3's device table (§1 above) already lists as **discarding a
token that belongs to a constituent's head**, 1,466 occurrences corpus-wide.
This is the entry point for the measurement §10 (below) asked for as the
hypothesis's own falsification test.

**Measured: `expl` and composite-POS `verb+pronoun` are largely the same
verbs, split by clitic attachment, not by grammar — the hypothesis
survives.** Every `expl` token's head lemma, paired with the `expl` token's
own lemma, gives **687 distinct (verb, pronoun) pairs across 582 verb
lemmas** — `fare+si` 68, `muovere+si` 40, `potere+si` 30, `volgere+si` 26,
`vedere+si` 21, … Comparing verb lemmas against the 170 distinct verbs
underlying `verb+pronoun`'s 488 fused tokens: **96 of 170 (56.5%) also occur
as a separate `expl` construction with the same verb**, e.g. `andare+si`
appears both fused (`vassi`-type enclitics) and as a separate `expl` pronoun
(`si andò`-type). The same lemma, the same reflexive clitic, attaches
enclitically in one line and proclitically in another — an orthographic fact
about Old Italian spelling, not a different grammatical construction. This
is the result §10's bullet below asked for and updates.

**But this also means `expl` and composite POS are two different
compensations for the *same* fact, not just two names for it — and only one
of them keeps the information.** Composite POS (`verb+pronoun`) at least
records that the pronoun exists, folded into one token; `expl` **discards**
it — the relation exists only to say "this token is not an argument," and
the pronoun's own referential content (reflexive, reciprocal, or genuinely
expletive — UD distinguishes these; old Layer 4 does not) goes unrecorded
either way. `ritrovarsi` and `vagliami` are the identical construction
written two ways, and old Layer 4 currently preserves the fact for neither:
the fused case loses it to a flat composite tag, the separate case loses it
to `expl`'s blanket discard.

**Consequence for whatever generation 2's dependency layer turns out to be,
following directly from §2.1's L2 design — a constraint on that future
design, not a design of it.** Only L1 and L2 have a concrete proposal in
this file; the label "L4" used elsewhere here (§2.2's build-order note, the
device table in §1) names *generation 2's dependency layer* as a
placeholder, borrowed from old Layer 4's position in the stack, not a
layer whose relation vocabulary or behavior has been designed — `PLAN.md` §4
item 2 still lists "where a hierarchical judgement gets written" as
undecided, and nothing here settles it. What this finding does establish,
independent of that layer's numbering or eventual shape: once L2 splits
every fused `verb+pronoun` token into two ordinary entries (§2.1), the
orthographic distinction old Layer 4 currently treats so differently — fold
into one token vs. leave as two — disappears at the terminal level;
`vagliami` and `mi ritrovai` become an ordinary verb entry plus an ordinary
pronoun entry, indistinguishable in shape. **Whatever assigns dependency
relations over L2 no longer has a structural reason to treat them
differently** the way old Layer 4 does (one spelling gets a composite POS
tag, the other gets `expl`) — that asymmetry was forced by old Layer 1's
token shape, not by anything about the construction itself. This is a
constraint worth carrying into that layer's design, whenever it happens, not
an argument about what its relation vocabulary should be.

**Status: measured, not corrected — resolves §10's falsification bullet;
the design question it opens belongs to a not-yet-designed layer, not to L4
specifically.**

---

## 8. `case/` review (2026-09-09)

Method applied to `case/`, the pronoun-case annex. §6 already found one
`case/` finding while reviewing old Layer 2 (the `che` mistag silently gates
`case/`'s coverage, since scope is read verbatim off Layer 2's `pos`). This
section is `case/`'s own review, on its own terms, using `--stats`'s
adjudication against `dep` — the one cross-check `case/README.md` says
exists (*Check*: "there is no deterministic checker for case").

**Finding: 25 of `--stats`'s "impossible pairings" are one construction, and
it is finding H's problem again, one level down.** Entry point *Inf* 1:22
`quei` — "*E come **quei** che con lena affannata, … si volge*" — `case/`
reads `quei` `nominative`; `dep/` attaches it `obl` to `volse` (line 26,
`dep/inferno/01.tsv:22-26`), an "impossible pairing" by `--stats`'s own
count (`obl` cannot govern a nominative). Corpus-wide, `--stats` lists 25
such pairings, all `nominative` vs `dep=obl`, and the ones checked
(`inferno` 1:22 `quei`, `paradiso` 1:93 `tu`, plus `colui`/`quel`/`quella`/
`questo`/`quello` instances at `inferno` 16:45, 19:17, 20:29, 24:25/63, 26:87,
31:104; `purgatorio` 2:54, 7:107, 12:127, 17:45, 23:126, 24:13, 25:41, 30:71,
31:25; `paradiso` 1:62, 1:93, 3:44) share one shape: **a nominative-form
pronoun heads a relative clause (`acl:relcl`), and the whole
pronoun-plus-clause unit fills a comparative or oblique slot one level up**
— *Inf* 1:22's `quei` is simultaneously the antecedent `che` (22:4, `nsubj`
of `volge`, 24:2) refers back to, and the standard of comparison `come`
introduces for the main verb `volse` (26:2); *Par* 1:93's `tu` is
simultaneously what `ch'` (93:5, `nsubj` of `riedi`, 93:8) refers back to,
and what `come` attaches obliquely to `corse` (93:2).

**Neither layer is wrong; there is no token to write the fact on.** The
pronoun's own case is correctly nominative — it is coreferential with the
clause's subject — and the whole `[pronoun + relative clause]` constituent's
external role is correctly oblique. A flat, token-indexed dependency tree can
only attach one deprel to `quei` itself, so it picks the external role
(`obl`) and the internal one (the nominative reading `case/`'s independent
read still recorded) becomes structurally invisible to `dep/` — visible only
because a *second*, independently-generated column happens to disagree.
`case/README.md`'s own design principle — generate blind, adjudicate after —
is what surfaced this at all; a merged `morph/*.tsv` column read against
`dep` at build time never would have.

**This is the same missing-hierarchy defect already on the table, not a
third, unrelated finding.** §2.2's participle-object note (added earlier
this session, itself finding H's defect recurring) already named the general
shape: old Layer 3 never had an explicit rule for what a phrase node should
contain, so a relative clause sometimes folds into an NP span (*Inf* 1:9) and
sometimes doesn't. Here the same absence of a constituent node — nothing
stands for "`quei che si volge`" as a unit — forces `dep/` to pick one of two
true facts about `quei` and let the other one only survive because `case/`
was generated independently. **A phrase/clause node for the relative-clause
unit would hold both facts at once**: `nominative` (or whatever case) at the
unit's head, `obl` on the unit as a whole. This is one more concrete case for
§4.2's bound to resolve, and arguably the clearest evidence yet that
enumeration (§2.2, §3) needs to reach at least this far — a bare NP/PP
enumeration with clauses left entirely to `dep/`'s edges (§2.4) would
reproduce this exact contradiction in the rebuilt stack too.

**Status: measured, not corrected.** `case/` itself needs no fix — its
"impossible pairing" list already does the diagnostic work it was designed
to do (`README.md`'s *Independence* section states this is the annex's whole
value). What's open is where the rebuilt stack writes the fact `case/` is
catching here, and that question is now folded into §4.2's, not separate
from it.

---

## 9. Old Layer 5 (`skel/` gold) review (2026-09-09)

Method applied to `skel/`. Per standing premise 1 (`PLAN.md` §2), gold is a
benchmark, not a target — this reviews `derive_unit` (`dante_corpus/skel/derive.py`),
the deterministic derivation `skel/`'s own artifact is checked against, not
gold as an authority to fit. Entry point: the same *Inf* 1:1-3/22-26 material
§7 and §8 already opened.

**Finding: §7's `expl` discard and §8's case/dep tension both reach Layer 5
unchanged, because `derive_unit` is a narrow function of Layers 2 and 4 by
design, and touches `case/` at exactly one rule.**

- **`expl` (§7) produces no skeleton row at all, not just no argument slot.**
  `skel/inferno/01.tsv:2` gives `ritrovai` (2.2) `subj=∅` (pro-drop),
  `obl:in=(1,2)`, `obl:per=(2,5)` — no row of any kind cites `mi` (2.1,
  `deprel=expl`). `derive.py` never references `"expl"` as a deprel at all
  (checked directly in the source): the token is not filtered out by a rule,
  it is simply never matched by anything that mints a tuple. §7's "discarded
  outright" is confirmed one layer further down — the reflexive clitic's
  content doesn't survive as far as a skeleton position either.
- **§8's case/dep tension is invisible to Layer 5 by explicit design, not by
  accident.** `derive_unit`'s own docstring (`derive.py:86-89`) states
  `case_rows_by_line` is "read at exactly one place — rule CZ's slot claim
  for a gapped-clause remnant. Everywhere else the derivation stays a
  function of Layers 2 and 4 alone." *Inf* 1:26 confirms it directly:
  `skel/inferno/01.tsv:26` derives `volse`'s `obl:come = (22,3)` — citing
  `quei` as the argument — purely from `dep`'s `case`+`obl` chain (`case` on
  `quei` at 22:2→22:3, `obl` from 22:3 to 26:2); `case/`'s own independent
  `nominative` reading of `quei` (§8) is never consulted for this tuple.
  Layer 5 does not resolve the tension §8 found; it simply never looks at
  the column that would raise it.

**Neither finding is a Layer-5 defect — both are consequences of `derive_unit`
inheriting whatever Layer 4 already decided, which is exactly what a
*checker* should do (it is derived from Layers 2/4, never authored against
gold, per the module's own docstring at `derive.py:82-84`).** The
consequence worth recording is upward, not downward: **whatever a rebuilt
dependency layer decides about `expl` (§7) or about the relative-clause
antecedent case (§8) will pass through to whatever derives skeleton tuples
from it unchanged, with no independent correction available at that stage**
— `case/`-style independent generation is the only mechanism in the current
stack that ever surfaces such a tension at all, and it does so for exactly
one narrow rule (CZ). If the redesign wants these phenomena caught rather
than silently inherited, the catching has to happen where they are
generated (the dependency/relation layer itself, or a cross-layer check per
§4.1) — not assumed to surface later at whatever plays Layer 5's role.

**Status: measured, not corrected.** No new finding independent of §7/§8;
this section's contribution is confirming, with source citations, that both
already-found compensations propagate through `derive_unit` unchanged rather
than being caught or repaired there.

---

## 10. What would falsify this

- **The checks cannot replace the tree.** §4.1 is the load-bearing bet. If no
  practical set of cross-layer checks catches the incoherences a tree would have
  made unrepresentable, enumeration reproduces finding H at three phrase types
  instead of one, and the tree is worth its cost after all.
- **The grammatical-word hypothesis fails on a full family.** ~~`reads/`'s
  next read should measure the pronominal verbs in full (`expl` 1,466 vs
  `verb+pronoun` 488). If the split turns out to be conditioned by something
  grammatical rather than by the scribe's spacing, §2.1 loses its
  motivation.~~ **Measured, §7: the hypothesis survives.** 96 of 170 verb
  lemmas underlying `verb+pronoun` also occur as a separate `expl`
  construction with the same reflexive clitic — the fused/separate split is
  conditioned by spelling, not grammar. §7 also surfaces a distinct,
  unresolved question this bullet did not anticipate: `expl` discards the
  pronoun's content outright rather than folding it, so the two old-Layer-4
  treatments of the same fact are not just differently shaped, one of them
  loses information the other keeps.
- **The 2.73% is in the wrong places.** §4.4's `nsubj` 365 and `obj` 289 are what
  downstream needs most. If the discontinuous cases are disproportionately the
  ones a knowledge graph or a translation must resolve, a bounded average loss is
  the wrong summary statistic.
