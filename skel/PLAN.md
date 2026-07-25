# skel — Layer 5 Phase 5 plan: deterministic elimination of the residual soft violations

Status as of 2026-07-26: `make -C skel check` reports **0 hard, 4846 soft** violations across
all 100 cantos (17438 at the first full-corpus measurement → 7776 after the Phase 4a checker
refinements → 5919 after one round of Phase 4b `--fix` LLM regeneration → 5105 after Phase 5a →
4846 after Phase 5b). The project goal is unchanged: **0 soft violations** — soft divergences
are rule mismatches to eliminate, not a baseline to tolerate.

**Phases 5a–5d have landed** (see [`CORRECTIONS.md`](CORRECTIONS.md) for each round's rules,
measurements and rejected candidates). **Phase 5e — a `--fix` regeneration pass — is running
now.** Everything after the *Landed phases* table below is the measurement that motivated this
plan, kept as the record of what was tried and rejected; its violation counts are **pre-5a**
unless stated otherwise.

This plan supersedes the Phase 0–3 plan (same filename, removed in `16f1c55` once those phases
landed). It exists because Phase 4b's LLM-regeneration approach had measurably stalled, and the
measurement explained *why* in a way that changed what was done next.

## Phase 5e — `--fix` on what actually remains (in progress)

The four deterministic phases removed exactly the violations regeneration could never have
fixed, so what is left is the material `--fix` exists for. Workload as of 4846, re-measured
after 5b:

| | before Phase 5 | now |
|---|---|---|
| flagged parse units (1 LLM call each) | 2235 of 3477 (64.3%) | **2037 of 3477 (58.6%)** |
| soft violations | 5919 | **4846** |

Flagged units split evenly across the canticles — inferno 659, purgatorio 727, paradiso 651 —
which is what makes the usual 3-way parallel run (one process per canticle) balanced. The
per-unit tail is short: 838 units carry exactly one violation, 1364 carry two or fewer, and the
maximum is 14.

```bash
make -C skel fix                                  # all three canticles, MODEL from ../model.mk
uv run skel.py inferno --fix -m <model> --log     # one canticle; --log appends to skel.log
```

Both write each unit's rows back to the TSV as soon as they are accepted (`1955ff5`), so an
interrupted run loses at most one unit. Acceptance is now Phase 5c's criterion: the soft count
must drop **and** no violation class may appear that wasn't already in the unit.

### What the residue is, by class

Triage (Phase 5b) says these are genuine reading disagreements, not derivation blind spots:

| class | count | what it is |
|---|---|---|
| `extra_arg` | 1991 | 936 are `subj`, of which 73% cite a token *unrelated* to the predicate in the dep tree — enjambment and pro-drop resolution. 107 are the `expl` clitics of pronominal verbs (5d), read as `obj`/oblique against the frozen UD convention. |
| `missing_arg` | 1305 | 716 obliques and 265 objects sitting on **explicit** dep edges the LLM simply did not list. |
| `role_mismatch` | 1250 | 99.9% on edges both sides see — pure label disagreement (`subj`/`obj` reversals, cross-lemma `obl` pairs). |
| `extra_tuple` | 176 | mostly NP-internal modifiers (`amod`) promoted to predicate status. |
| `membership` | 96 | a scattered long tail of individual boundary cases, no mechanical pattern left. |
| `missing_tuple` | 26 | residual after 5b removed the conjunction-promotion class. |
| `unknown_role` | 2 | roles outside the frozen vocabulary; Phase 5c stops `--fix` from adding more. |

### What to measure when the pass finishes

The **unit success rate** is the number that decides whether a second pass is worth its calls —
it was 10.5% before Phase 5, and the deterministic phases should have raised it by removing the
structurally unfixable units from the denominator. `--fix` prints `fix complete: N/M unit(s)
improved`; record N/M alongside the `--stats` before/after in `CORRECTIONS.md`.

Then re-run `--stats` and compare the **per-class** deltas, not just the total:

- A class that barely moves after a full pass is evidence it is *checker-side*, not an LLM
  error — the same signal that produced Rules C/D and the Phase 5b rules. Route it to a new
  deterministic rule, not to more calls.
- A class that moves well is worth a second targeted pass.
- Watch `role_mismatch`: it is the class most likely to churn (a regeneration can trade one
  label disagreement for another) and Phase 5c only blocks *new kinds*, not swapped roles.

Do not start a second full pass before that measurement exists.

## Landed phases

| phase | what landed | measured |
|---|---|---|
| **5a** | Rule C (coordination normalization) + Rule D (`nmod` oblique of a derived argument) | 5919 → **5105** |
| **5b** | no conjunction promoted to predicate; copula/modal double-listing suppressed; adverbial obliques accepted | 5105 → **4846** |
| **5c** | `--fix` acceptance requires no new violation *kind* (`_is_improvement`) | — |
| **5d** | audit of the `expl` class: Layer 4 is right, nothing to route back | — |

Details, per-rule negative tests and the rejected variants are in
[`CORRECTIONS.md`](CORRECTIONS.md).

## Why Phase 4b (`--fix`) stalled

### Measured cost

One canto run serially against the local debug model (`ollama:gemma4:31b-it-qat`, inferno 1,
136 lines, 19 flagged units):

| metric | measured |
|---|---|
| wall time | **3 hours** |
| units attempted | 19 |
| units improved | **2 (10.5%)** |
| soft violations removed | **4** (37 → 33) |

Extrapolated to the corpus: 2235 flagged units × 1 LLM call each, yielding on the order of
**450 violations removed per full pass**. The production runs use the Gemini API rather than
the local model, so the wall time differs — but the **10.5% unit success rate is a property of
the method, not of the backend**, and it is the term that dominates.

### Measured cause

The success rate is low because **a large share of flagged units cannot be fixed by
regeneration at all** — the LLM's reading is already correct and the divergence is on the
checker's side. Classifying every `extra_arg` (2848 = 48% of all soft violations) by how the
cited argument token attaches to the predicate in the frozen dep tree:

| relation of cited token to predicate | count | share |
|---|---|---|
| indirect descendant, depth 2 | 1097 | 38.5% |
| unrelated | 902 | 31.7% |
| direct child (deprel outside `derive_unit`'s map) | 495 | 17.4% |
| pro-drop ∅ | 129 | 4.5% |
| child of a `conj`-relative of the predicate | 122 | 4.3% |
| indirect descendant, depth ≥ 3 | 103 | 3.6% |

The dominant depth-2 bucket is overwhelmingly **coordination**:

```
inferno 1:103  ciberà -[obj]->   terra  -[conj]-> sapïenza   (LLM: obj)
inferno 1:128  è      -[nsubj]-> città  -[conj]-> seggio     (LLM: subj)
inferno 1:114  onora  -[obj]->   te     -[conj]-> quei       (LLM: obj)
```

"si ciberà di terra e di sapïenza" — both conjuncts are objects, and the LLM is right.
`derive_unit` propagates a subject across coordinated *predicates* (its rule 3) but has no rule
propagating a coordinated *argument*, and it only ever reads a predicate's **direct** dep
children. So the second conjunct can never appear on the derived side.

**These units are structurally unfixable by `--fix`.** A regeneration reproduces the same
correct reading, the violation survives, `_fix_canto` rejects the attempt as "not improved",
and the LLM call is spent for nothing. This is the mechanism behind the 10.5%. Phase 5a's Rule
C is what removed this class.

## Measured violation anatomy (2026-07-26, at 5919 — pre-5a)

By kind:

| kind | count |
|---|---|
| extra_arg | 2848 |
| missing_arg | 1353 |
| role_mismatch | 1245 |
| extra_tuple | 275 |
| missing_tuple | 100 |
| membership | 96 |
| unknown_role | 2 |

Where the *other* two large kinds attach — both are almost entirely on edges `derive_unit`
already sees, i.e. genuine label/citation disagreements rather than derivation blind spots:

| kind | direct child | conj-relative |
|---|---|---|
| missing_arg | 89.8% | 10.2% |
| role_mismatch | 99.9% | 0.1% |

Per parse unit (the `--fix` regeneration granularity): **2235 of 3477 units (64.3%) carry at
least one violation**; 788 carry exactly one, and the tail reaches 15.

`extra_arg` direct-child cases by the dep deprel that `derive_unit`'s map omits: `advmod` 190,
`expl` 105, `nmod` 66, `advcl` 54, `mark` 36, then a thin tail.

## Candidate rules — all measured before proposing

Each rule was implemented as a monkeypatch over `derive_unit` / `_classify_divergence` /
`_apply_subj_authority` and re-measured across all 100 cantos. C and D landed as Phase 5a.

| rule | what it does | measured |
|---|---|---|
| **C — coordination normalization** | collapse every argument citation onto its coordination head (walk `conj` up) on **both** sides before comparing | **−665** (5919 → 5254) |
| **D — `nmod` oblique of an argument** | accept a given `obl:<prep>` whose arg is an `nmod` dependent of one of that predicate's own derived arguments ("ha *bisogno* **di te**") | **−155** (5919 → 5764) |
| **C + D** | | **−820 → 5099 (−13.9%)** |
| A — enumerate conjuncts in `derive_unit` | emit a derived row for each `conj` dependent of a derived argument | −2 ❌ |
| B — share non-subject args across `conj` predicates | | **+2326** ❌ |
| E — widen the control-subject authority | let the xcomp/ccomp candidate set apply when `derive_unit` did resolve a subject | −22 (on top of C+D) ❌ |

**Rule A's failure is the key result.** Enumerating conjuncts on the derived side moved
`extra_arg` −554 but drove `missing_arg` +529, for a net −2: the LLM itself enumerates
coordinations inconsistently, listing every conjunct in some units and only the first in
others. So the divergence is a **notation-convention mismatch, not a parse disagreement**, and
the correct instrument is normalization before comparison — exactly what Phase 1 already does
for preposition-lemma variants and the `attr`≡`xcomp` labeling split — not adding rows.

Rule C is the same shape as those Phase 1 equivalences and inherits their justification. Note
that under Rule C `role_mismatch` rises slightly (1245 → 1261): collapsing a coordination
exposes role disagreements previously split across an `extra_arg`/`missing_arg` pair. That is
the rule classifying more precisely, not suppressing — a useful sign it is not simply
swallowing violations.

Rule E is reported because it disproves a plausible hypothesis: the residual
`extra_arg subj` mass (1105, the single largest role bucket) is **not** control-licensed, so
widening the authority model is not the lever. Those are genuine subject disagreements
(enjambment, pro-drop resolution) and belong to hand/LLM triage — i.e. to Phase 5e.

## Cost comparison

| approach | violations removed | cost |
|---|---|---|
| `--fix`, measured (inferno 1, serial, local) | 4 | 3 h, 19 LLM calls |
| `--fix`, full corpus pass (extrapolated from that rate) | ~450 | **2235 LLM calls** |
| **Phases 5a + 5b (deterministic)** | **1073** | **0 LLM calls, minutes** |

The deterministic phases delivered roughly **2.4× an entire `--fix` pass, instantly**, and cut
the `--fix` workload from 2235 to 2037 flagged units — removing precisely the units regeneration
could never have fixed, which is why the Phase 5e success rate should come in above 10.5%.

## What is deliberately not proposed

- **Enumerating conjuncts on the derived side** (Rule A) — measured net-zero, for the reason
  above.
- **Sharing non-subject arguments across coordinated predicates** (Rule B) — measured +2326.
- **Widening the control-subject authority model** (Rule E) — measured −22; the hypothesis that
  the large `extra_arg subj` bucket is control-licensed is disproved.
- **A blanket rule over the `advmod`/`expl`/`mark` direct-child deprels** — these are a mix of
  genuine LLM over-promotion and probable Layer-4 mistags; a blanket exemption would swallow
  both. Phase 5b/5d triaged them instead, and the outcome vindicates the caution: of the
  `advmod` mass only the *adverbial oblique* half (adverb POS, `obl` role — 67) was accepted,
  the `xcomp`-over-`advmod` half (91) stays flagged; the `expl` cases turned out to be neither
  exemptible nor Layer-4 errors but plain LLM misreadings; `mark` was left untouched.
- **Remapping a given `aux`/`cop` predicate onto its lexical head** (as opposed to suppressing
  the redundant tuple) — measured −6, and −2 in its narrower variant; see 5b.
