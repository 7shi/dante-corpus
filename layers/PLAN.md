# Layer Structure Review: Plan

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

- **`harness/`** — a library, referenced through `uv`. The agent loop, the
  tool-calling protocol, the fixed-context execution mode, the gates, the fix
  levels, the observability contract. It is a tool, and it is finished
  (see **§1**).
- **`layers/`** — this directory. Skills and loops that *use* that tool, aimed
  at the layer stack itself: what each layer can and cannot express, and what
  the description ought to say.

The mechanics of the split — packaging `harness/` for `uv`, what moves and what
stays — are a separate discussion held after this document is written. Nothing
here specifies them.

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
reproduced. That assumption is dropped, and the note needs correcting where it
stands (`PLAN.md` Milestone Ledger item 5: nothing here is append-only).

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
  slice's reproduce-the-current-results assumption.
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
