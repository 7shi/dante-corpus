# case — a pronoun case annex to Layer 2

## Status

**Proposed, not started. No artifact, no driver, no module exists yet — this directory holds
only this file.** Nothing here is committed to; the plan's own first step is a pilot whose
purpose is to *kill* the idea cheaply if the measurement comes out wrong. Written 2026-07-29,
immediately after Layer 5's Phase 5 closed at **0 hard, 3551 soft**
(see [`../skel/PLAN.md`](../skel/PLAN.md)'s *Where Phase 5 ended*).

## Why this exists

Layer 5's residual is documented reading disagreement, and its largest *decidable-looking*
remnant is one question the existing layers structurally cannot answer: **is a pronominal clitic
accusative or dative?**

```
mi pesa            "it weighs on me"      -> mi is dative     (iobj)
m'avea 'mmonito    "he had warned me"     -> mi is accusative (obj)
```

`mi` / `ti` / `si` / `ci` / `vi` / `ne` are identical in form in both cases. Neither the token
stream (Layer 1), the morphology as it stands (Layer 2 has gender/number/person/tense/mood but
**no case**), nor the dependency tree (Layer 4 — the tree shape is the same; the deprel *is* the
disputed judgment) distinguishes them. What decides it is the governing verb's argument
structure.

Layer 5's audit surfaced this as a concrete population and then had to park it:

- **Phase 5h** measured 97 divergences where Layer 4 and the LLM disagree exactly here.
- **Phase 5i** closed the 26 that a *structural* argument could settle (the predicate already
  carried a second `obj`, and UD allows at most one) — hand-verified, retagged in `dep/`.
- **The other 67, plus 30 mirror-direction cases** (Layer 4 `iobj`, LLM `obj` — `mi bagna`,
  `mi tormenta`, `ti conforta`) were parked with an explicit reason: *"both need a Layer-2 case
  feature or a clitic lexicon"* ([`../skel/PLAN.md`](../skel/PLAN.md), section 1).

In the current `role_mismatch` pair table that population is `'obl:a' vs 'obj'` (61) and
`'obj' vs 'obl:a'` (30). This plan is the instrument those verdicts named.

## What it is — and what it is not

**It is:** one more Layer-2-style morphological column, authored the same way every other Layer-2
column was — an LLM reading the Italian source and nothing else, frozen as TSV, round-trip
checked, content-hashed.

**It is not a lexicon.** The rejected alternative — importing a valency dictionary that says
`pesare` takes a dative and `ammonire` an accusative — brings an external authority into a
corpus whose whole premise is that every layer is a function of the Italian source alone. This
plan does not do that, and the sibling proposal it was paired with (**a verb lexicon** for the
complement-vs-adjunct distinction) stays rejected for exactly that reason.

**The neutrality question, answered.** The *Neutrality audit* invariant in
[`../PLAN.md`](../PLAN.md) is a constraint on **inputs to the build prompt**: no reference
translation, no entity list, no external canon. A case pass over the Italian source satisfies it
on the same terms `pos` and `deprel` already do — those are model judgments too, informed by the
model's internalized knowledge of Italian. Case is not a special case of external canon; treating
it as one would condemn every existing layer.

## The real risks

Two, and neither is neutrality.

### 1. Independence — the design constraint that matters most

Layer 5 is valuable **because the LLM's skeleton is an independent read of the same text**: a
divergence can therefore indict Layer 4, not just the model. A case column can either strengthen
that or destroy it, depending entirely on how it is generated.

- **Wrong**: measure the 91 disputed positions, then ask the model about *those positions*. That
  manufactures an artifact to close violations. It is the failure mode
  [`../dep/CORRECTIONS.md`](../dep/CORRECTIONS.md) already names — *pick the deprel the corpus
  uses for that word, not the one that closes the violation* — applied one level up.
- **Right**: generate case for **every clitic in the corpus, blind** to which positions are
  disputed, in a pass that is shown neither `dep/` nor `skel/`. The result is then a genuine
  **third independent read**, and `dep` / `skel` / `case` can be adjudicated 2-of-3 mechanically.

The blind pass is the only version worth building. If cost pressure ever suggests narrowing it to
the flagged set, the correct response is to abandon the plan, not to narrow it.

### 2. There is no deterministic checker for case

Every other layer has a mechanical ground truth to check against — Layer 3 spans must reproduce
verbatim source substrings, Layer 4 is a well-formedness-checkable tree, Layer 5 has
`derive_unit`. **Case has none.** The available hard checks are formal only:

- closed vocabulary,
- 1:1 alignment to the Layer-1 token stream,
- the column is non-empty **only** on pronoun-POS tokens (Layer 2 decides which those are).

Beyond that, the only cross-check is `dep`'s `obj`/`iobj` — which is the very thing under
adjudication. So this layer's correctness rests on the model's **self-consistency**, and that is
a measurable property, not an article of faith. Measuring it is step 1 below.

## Why its own directory

Decided before writing: `case/` is a sibling directory, **not** a new column in `morph/*.tsv`,
even though case is conceptually a Layer-2 morphological feature.

1. **Hash blast radius.** Adding a column to `morph/*.tsv` changes the content hash of all 100
   morph artifacts — for a column that is empty on 97% of tokens. `morph` is read by `np`, `dep`
   and `skel`, plus the external consumers (`dante-analyze`, `dante-dravidian`) that
   [`../PLAN.md`](../PLAN.md)'s *Versioning* section promises granular invalidation to. A sibling
   directory adds one key to `hashes.LAYERS` and **moves no existing hash**.
2. **Provenance stays visible.** The existing morph columns are one pass, one model, one moment.
   This one is a later pass, a different model, covering clitics only. Since the entire value of
   the artifact is *being an independent third read*, that independence should be legible in the
   file layout rather than merged away.
3. **Revertibility.** This is an experiment that the pilot may kill. `rm -rf case/` must return
   the repo to an untouched state.

**Merging into `morph/` later stays open** and is the natural end state if the column proves out.
The reverse — extracting a column from `morph/` after consumers have recorded its hash — is much
worse, so the order is: build separately, prove, then consider merging.

## Design sketch

Mirrors the existing per-layer pattern exactly (own driver, own README, own CORRECTIONS, own
Makefile; `morph/morph.py` is the reference implementation for the driver).

```
case/            <canticle>/NN.tsv   line, token, word, case
  case.py        LLM build driver + --check / --stats   (mirrors morph/morph.py)
  README.md      closed vocabulary, generation rules, validation tiers, usage
  CORRECTIONS.md measurement and adjudication history
  Makefile       all / check / stats
dante_corpus/case.py   dataclass, TSV I/O, serve-time index
```

- **Scope**: pronoun-POS tokens. The clitic subset (`mi ti si ci vi ne lo la li le gli` and their
  elided forms) is what the adjudication needs; whether to cover *all* pronouns or only clitics is
  a decision for step 2, taken on measured cost.
- **Closed vocabulary**: to be frozen before the corpus pass, from the pilot's own output rather
  than from a grammar book — the same measure-then-freeze order every other layer used. The
  expected shape is nominative / accusative / dative / oblique, with the last covering partitive
  `ne` and locative `ci`/`vi`.
- **Serve surface**: `Canto.case()`, `dante-corpus text case`, `"case"` appended to
  `hashes.LAYERS` (additive — no existing hash changes).
- **Consumption by Layer 5**: `skel._classify_divergence` already accepts an optional
  `morph_pos_by_position`; a `case_by_position` argument fits that existing shape. **Layer 5's
  checker is a consumer, never the owner** — the adjudication report itself belongs to
  `case/ --check`.
- **Adjudication output, not exemption**: where `case` contradicts `dep`, the result is a
  candidate list for a **hand-verified Layer-4 correction round** in the style of Phases 5i/5n —
  not a checker rule that silences the violation. Layer 5's soft count falls because `dep` got
  more correct, which is the same mechanism every audit round in Phase 5 used.

## Sequencing

1. **Pilot: measure self-consistency. This is a kill gate, not a formality.**
   Over the ~97 disputed clitic positions, ask for case **three times independently** (fresh
   sessions; vary the surrounding-context presentation so the runs are not trivially correlated).
   Report per-position agreement. Throwaway script in the scratchpad, **nothing committed**,
   cost on the order of a few hundred calls / ~1 hour.
   - **Stop rule, fixed in advance**: if the model does not agree with itself on the disputed
     positions at a clearly higher rate than on a control sample of *undisputed* clitics, the
     column is measuring noise and **this plan ends here**. A case column that waffles on exactly
     the cases it was built for is worthless regardless of its aggregate accuracy.
   - Also report the *direction* of the answers: if the model systematically sides with `dep`, or
     systematically against it, that is itself the finding, and it changes what step 3 does.
2. **If the pilot passes: freeze the vocabulary and scope, then write the driver.** Sizing, from
   the current corpus:

   | population | count |
   |---|---|
   | source lines | 14233 (100 cantos) |
   | Layer-2 tokens | 101601 |
   | pronoun-POS tokens | 12332, over 8542 lines |
   | clitic-form subset | 3241, over 2998 lines |

   `morph/morph.py` runs 3 lines per LLM call, so a full Layer-2 regeneration would be ~4700
   calls. A case-only pass over the 2998 clitic-bearing lines, with one output row per clitic,
   can carry more lines per call (6–10) and lands at roughly **300–500 calls** — well under a
   quarter of Phase 5q's `--fix` pass (1702 calls, ≈28 h, 3-way parallel).
3. **Blind corpus pass, freeze, then adjudicate.** Generate, validate, commit, *then* join
   against `dep`. Never the other way round.
4. **Layer-4 correction round** over the contradictions, hand-verified against the terzine, in the
   style of Phases 5i/5n. `make -C dep check` must stay 0/0 throughout.
5. **Re-measure Layer 5** and record the delta in [`../skel/CORRECTIONS.md`](../skel/CORRECTIONS.md).

## Expected value — stated honestly before starting

**≈90–100 soft violations of the 3551**, i.e. the disputed clitic population and little else.
This does not reach 0 and does not come close: the bulk of the residual is subject resolution
across enjambment and pro-drop (`extra_arg subj` 865), which no case feature touches. Anyone
reading this plan as a route to zero has misread it — it converts **one specifically identified
undecidable class into a decidable one**, and its second, less quantifiable return is a corpus
where the clitic case of every pronominal mention is queryable at all, which is useful to
downstream consumers independently of Layer 5's violation count.

If that trade looks poor at the pilot stage, the correct outcome is to stop and leave the
residual documented as reading disagreement, which is where
[`../skel/PLAN.md`](../skel/PLAN.md) left it.
