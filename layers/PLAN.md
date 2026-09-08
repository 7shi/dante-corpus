# Layer Structure Review: Plan

### Handoff (2026-09-09) — resume here

> **Where this stands.** The directory holds four documents and, as of this
> session, a first piece of code — [`README.md`](README.md) (stable
> orientation), this plan, **[`REDESIGN.md`](REDESIGN.md)** (the design
> proposal, now §1–§10), [`reads/inf-1-1-9.md`](reads/inf-1-1-9.md) (the pilot
> read, updated in place this session with this session's follow-ups),
> **[`gen2/`](gen2/)** (new this session — see *L1 implemented*, below), and
> **[`L1.md`](L1.md)** (new this session — L1's design, measurement, and
> implementation gathered in one place, superseding the L1-specific detail
> that used to sit inline in this handoff and in `REDESIGN.md` §2.1).
> §4's five items remain unstarted **as written**; the work took the shape
> described below instead, and §4 is deliberately not rewritten yet — the new
> direction is still provisional pending an implementation trial (see
> *Rollout*, below).
>
> **Premises (operator, 2026-09-07 and 2026-09-09), recorded at the head of
> `REDESIGN.md`:** (1) preserving frozen artifacts is not a constraint —
> regenerating a layer is accepted cost, terminal renumbering is on the table;
> (2) stop at phrases — no complete tree rooted at the sentence (`REDESIGN.md`
> §3 argues it, §4.1 prices it); (3) generation 2 must not depend on
> generation 1 at rebuild time — old Layers 1–5 are bootstrap-only, never a
> named input a generation-2 layer's *definition* reads.
>
> **Method: each layer examined on its own against concrete *Inferno* 1
> positions, every observation measured corpus-wide before being written
> down.** All five old layers plus `case/` have now been reviewed this way;
> each review is its own numbered section in `REDESIGN.md`, source-cited, and
> summarized below. None of the findings are corrected in the frozen
> artifacts — this is review, not repair.
>
> ---
>
> **Layer 1 (done, earlier this session).** Two corrections to this plan's
> own prior diagnosis: (1) nothing is discarded at Layer 1 — the defect is
> *address*, not loss (full finding: [`L1.md`](L1.md)). (2) the sentence unit
> already exists (`dante_corpus/dep.py:200` `sentence_groups`, Layer 4 is
> built inside it) but isn't stored or exposed. Also sharpened §1.3's
> diagnosis: Layer 4 *is* a tree; the defect is that its nodes are tokens,
> none stands for a constituent (`REDESIGN.md` §1).
>
> **Old Layer 2 review (`REDESIGN.md` §6).** Entry point *Inf* 1:3
> `smarrita`. Past participles are encoded three incompatible ways
> (`pos=verb`+`mood=participle` 724 / standalone `pos=participle` 25 /
> `pos=adjective` 573+, the last splitting its own lemma between the
> adjective form and the verb infinitive for 104 wordforms, `smarrito` itself
> 4/4). The `pos` column holds 39 values, not a closed set (subtype leakage —
> `relative pronoun`/`pronoun`, `proper noun`/`noun` — plus spacing
> duplicates and singletons). Checked `case/`'s sparseness against this and
> found it's **not** a `case/` coverage gap — `case/` is complete and closed
> (13,157 rows, exact match) — but a pass-through of Layer 2's `pos` column
> read verbatim (`case/case.py:11`): a `che` mistagged `conjunction` (finding
> B's 225 positions, `reads/inf-1-1-9.md`) never reaches `case/`'s build step
> at all. The working assumption that "later layers don't lean heavily on
> `pos`" does not hold for `case/` specifically — recorded as a correction to
> avoid deprioritizing a `pos`-vocabulary fix without checking the consumer.
>
> **Old Layer 3 review (`REDESIGN.md` §2.2, inline).** `np/`'s
> fused-enclitic-pronoun mechanism (`clitic_mentions()`, the `"+lemma"`
> sentinel span, e.g. *Inf* 1:59 `venendomi` → `np/inferno/01.tsv:59` `+mi`)
> compensates for old Layer 1 having no position for a bound pronoun. §2.1's
> L2 split table covers exactly this shape (`verb+pronoun`, 488/372
> wordforms), so under the rebuilt stack the pronoun becomes an ordinary L2
> entry and the whole synthetic-mention apparatus has nothing left to
> compensate for. Separately, corrected an overstatement made mid-session:
> rebuilt NP is not "narrower" than old Layer 3 — finding H's own example
> already folds a relative clause into one NP span (*Inf* 1:9) — the
> participle-object question is a second instance of finding H's real defect
> (no explicit hierarchy rule), folded into §4.2's bound rather than treated
> as a separate axis.
>
> **Old Layer 4 review (`REDESIGN.md` §7).** Entry point *Inf* 1:2
> `mi ritrovai` (`mi` tagged `expl`, discarded as a non-argument, 1,466
> occurrences corpus-wide) — this doubled as the falsification test
> `REDESIGN.md` had left open for its own grammatical-word hypothesis.
> **96 of 170 verb lemmas (56.5%) underlying `verb+pronoun`'s 488 fused
> tokens also occur as a separate `expl` construction with the same
> reflexive clitic** (`andare+si`, `fare+si`, `muovere+si`, …) — the
> fused/separate split is spelling, not grammar, so the hypothesis survives.
> But the two treatments are not equally good: composite POS at least records
> the pronoun, `expl` discards it outright. Once L2 splits every fused case,
> `vagliami` and `mi ritrovai` become structurally identical, so whatever
> generation 2's dependency layer turns out to be has no structural reason
> left to treat them differently — recorded as a constraint on that
> not-yet-designed layer, not a decision about it (only L1/L2 are concretely
> proposed; "L4" is a placeholder label, not a designed layer).
>
> **`case/` review (`REDESIGN.md` §8).** Entry point *Inf* 1:22 `quei`
> ("*E come **quei** che con lena affannata, … si volge*"): `case/`
> independently reads it `nominative`; `dep/` attaches it `obl` to `volse`
> two lines down — one of 25 corpus-wide "impossible pairings" (`--stats`),
> all the same shape: a nominative-form pronoun heads a relative clause and
> the whole pronoun-plus-clause unit fills an oblique/comparative slot up the
> tree (also *Par* 1:93 `tu`, plus a dozen `colui`/`quel`/`quella`/`questo`/
> `quello` instances). Neither layer is wrong — this is finding H's
> missing-hierarchy defect surfacing a third time, visible only because
> `case/` was generated blind and independently. `case/` needs no fix; where
> the rebuilt stack writes this fact is folded into §4.2.
>
> **Old Layer 5 / `skel/` gold review (`REDESIGN.md` §9, gold treated as
> benchmark per premise 1, never as authority).** Confirms the two findings
> above reach `derive_unit` **unrepaired, by design**: `mi` in
> *Inf* 1:2 produces no skeleton row at all — `derive.py` never references
> `"expl"` as a deprel. *Inf* 1:26's `obl:come=(22,3)` (citing `quei`) is
> derived purely from `dep`'s `case`+`obl` chain — `derive_unit`'s own
> docstring (`derive.py:86-89`) states `case_rows_by_line` is read "at
> exactly one place" (rule CZ), not this one. Neither is a Layer-5 defect (a
> checker inheriting Layers 2/4's decisions is its job); the consequence runs
> upward — whatever a rebuilt dependency layer decides about `expl` or the
> relative-clause case will pass through unrepaired unless caught at
> generation time or by a cross-layer check (§4.1).
>
> **`reads/inf-1-1-9.md` updated in place** with this session's follow-ups,
> noted at each finding rather than rewritten: B corrected (the `case/`
> mechanism above), C extended (the three-way participle split), F resolved
> (the hypothesis survives, plus the Layer-5 confirmation), H upgraded from
> "least confidence" to a three-times-confirmed load-bearing pattern (line 9's
> own relative clause, the participle-object question, the `case`/`dep`
> pairings). The Axes table gained a follow-up note: F was axis (iii)
> *resolved*, not open; H reads closer to axis (iii) than to axis (i) now.
> "What this read does not settle" updated accordingly — G's count and the
> *Inf* 4:5 read are still untouched.
>
> ---
>
> **L1/L2 design, decided but none implemented (`REDESIGN.md` §2.1–§2.2,
> §5).** 1. Premise 3 as above. 2. **L1** = `tokenize()`'s full output,
> punctuation included, own numbering — design, measurement, and (as of this
> session) implementation: [`L1.md`](L1.md). 3. **L2** = grammatical words as
> `(l1_index, text)` pairs, only splits, never merges (composite tokens
> 1:many, e.g. `nel`→`(0,in),(0,il)`; the `fixed` many:1 direction stays a
> relation one layer up, over L2 entries, because 37 of 170 `fixed` groups
> overlap a composite split). 4. **L2 is a three-step pipeline**: split → POS
> classify → normalize (apocope/elision to the surface form, not the lemma);
> normalization needs step 2's POS first for 159 cross-POS wordforms, which
> is why the steps are ordered, not carved into exceptions. Step 2 itself
> should be staged (coarse POS first, then per-category refinement), with
> the participle/adjective boundary pinned by an explicit rule or one-shot
> example — staging alone would just relocate the three-way split (§6) to a
> new boundary. Step 1's output should be keyed by the word
> (`nel:in+il`), not by echoing `l1_index` back, with a retry only on
> genuine ambiguity (`nel`'s two-way split). 5. **Build order**: L4
> (dependency) precedes L3 (phrases) — L3 must project from generation 2's
> own L4, never from old Layer 4. 6. **Concrete task**: build the
> 442-wordform split table, per-entry POS classification, and
> ~1,686-wordform normalization table as three independent passes, diff each
> against old Layer 2 as precedent (agree / old-generation-is-wrong / genuine
> ambiguity), via `harness/stages/09.md` §2's fixed-context step, one
> wordform per job, no batching.
>
> **Rollout decided (`REDESIGN.md` §2.1, operator 2026-09-09): Canto 1
> first, starting at *Inf* 1:1-9 and widening gradually, before any pass runs
> corpus-wide.** Run all three passes over *Inf* 1:1-9 only, hand-inspect
> every wordform's split/POS/normalization against the source, widen to all
> of *Inf* 1 (136 lines), only then the full corpus. Corpus-wide numbers
> already justify the design; a single-canto pass is what would catch a
> systematic prompt or ordering error before it's baked into
> 442 + ~1,686 wordforms' worth of calls.
>
> **L1 implemented (this session, operator instruction: "gen2/ にL1を実装して
> ください").** [`gen2/l1.py`](gen2/l1.py) implements §2.1's L1 in full and is
> verified against it; design, implementation, and verification detail all
> live in [`L1.md`](L1.md) now, not here. Tests:
> [`tests/test_gen2_l1.py`](tests/test_gen2_l1.py) (13 tests, `uv run pytest
> layers/tests`) — parallel to `harness/tests`, not part of the root suite
> (`pyproject.toml` `testpaths = ["tests"]`) until gen2 replaces the old
> stack, per operator instruction: "コードをdante_corpusと統合する際に、テス
> トもルートの tests/ と統合します."
>
> **This is a start, not yet a stack — only L1 is implemented.** L2 (the
> split/POS/normalize trial) is still exactly as designed and unstarted; the
> next session's first choice: begin the split/POS/normalize trial on
> *Inf* 1:1-9 per the rollout plan above (now with a working L1 under it to
> index against), or continue open review items first (G's real count net of
> nested coordination, the *Inf* 4:5 all-layer read `PLAN.md` §4 item 4 asks
> for, the quotes hierarchy, §4.1's cross-layer checker design, §4.3's
> VP/Layer-5 relationship, or the external consumer survey `REDESIGN.md` §5
> flags as the one genuinely unknown cost figure).
>
> **Still deferred, unrevisited against premise 3: the bootstrap safe/
> contaminated split.** Which frozen layers are safe to show the model even
> as a one-time warm start (tentatively tokens, lemma decomposition, Layer-4
> bracketing, `sentence_groups`) and which are contaminated positions it must
> not anchor to (`cop`/`attr` 953:357, the locution `obl`:`advmod`:`nmod`:`conj`
> 217:68:30:13, Layer-3 granularity, participle POS, `che` POS, `expl`) —
> including whether Layer-4 bracketing can be "safe" when the `advmod`/`obl`
> choice moves the brackets themselves. Premise 3 settles the general shape;
> this specific split does not yet reflect the layer reviews above.
>
> **A caveat that still stands.** Every measurement in `reads/` and in
> `REDESIGN.md` came from ad hoc scripts run in a scratchpad and **not kept**.
> All are re-derivable from the frozen artifacts in minutes; none is
> reproducible by re-running a committed artifact. The cross-layer checker of
> §4.1 is where that gets fixed.

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
