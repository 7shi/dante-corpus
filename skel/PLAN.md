# skel — Layer 5 Phase 5 plan: deterministic elimination of the residual soft violations

Status as of 2026-07-26: `make -C skel check` reports **0 hard, 4846 soft** violations across
all 100 cantos (17438 at the first full-corpus measurement → 7776 after the Phase 4a checker
refinements → 5919 after one round of Phase 4b `--fix` LLM regeneration → 5105 after Phase 5a →
4846 after Phase 5b). The project goal is unchanged: **0 soft violations** — soft divergences
are rule mismatches to eliminate, not a baseline to tolerate.

**Phases 5a, 5b, 5c and 5d have landed** (see [`CORRECTIONS.md`](CORRECTIONS.md) for each
round's rules, measurements and rejected candidates); **only 5e remains open**. Everything below
is the measurement that motivated the phase plan, kept as the record of what was tried and
rejected. All violation counts in the analysis sections are the **pre-5a** figures unless
stated otherwise.

This plan supersedes the Phase 0–3 plan (same filename, removed in `16f1c55` once those phases
landed). It exists because Phase 4b's LLM-regeneration approach has measurably stalled, and the
measurement explains *why* in a way that changes what should be done next.

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
and the LLM call is spent for nothing. This is the mechanism behind the 10.5%.

## Measured violation anatomy (2026-07-26, 5919 total)

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
`_apply_subj_authority` and re-measured across all 100 cantos. Nothing below is frozen yet.

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
(enjambment, pro-drop resolution) and belong to hand/LLM triage.

## Cost comparison

| approach | violations removed | cost |
|---|---|---|
| `--fix`, measured (inferno 1, serial, local) | 4 | 3 h, 19 LLM calls |
| `--fix`, full corpus pass (extrapolated) | ~450 | **2235 LLM calls** |
| **Rules C + D** | **820** | **0 LLM calls, minutes** |

The deterministic phase delivers roughly **1.8× an entire `--fix` pass, instantly**. It also
shrinks the `--fix` workload from 2235 to **2081 flagged units**, and the units it removes are
precisely the ones regeneration could never have fixed — so the success rate of any subsequent
`--fix` pass should rise as well.

## Plan

### Phase 5a — implement Rules C and D (deterministic, no model call) — **done (2026-07-26)**

Add both to `dante_corpus/skel.py` as normalization applied before the divergence comparison,
alongside `_canonicalize_role`/`_normalize_prep_lemma`:

- **Rule C** in `_classify_divergence`: map each `(arg_line, arg_token)` to its coordination
  head by walking `conj` edges up (bounded), on both the given and derived side, de-duplicating
  the resulting rows. Roles are preserved, so a real role disagreement still surfaces.
- **Rule D**: suppress a given `obl`/`obl:<prep>` row whose argument is an `nmod` dependent of a
  token that `derive_unit` already derived as an argument of the same predicate.

Tests mirroring `tests/test_skel.py`'s existing per-rule cases, and a measured before/after
recorded in `CORRECTIONS.md`. Expected: **0 hard, 5099 soft**.

**Landed**: measured **0 hard, 5105 soft** — 6 above the monkeypatched estimate, because the
implementation applies `_apply_subj_authority` *before* collapsing, leaving Phase 2's behaviour
exactly intact. Five tests, each rule paired with a negative case.

### Phase 5b — re-triage on the reduced set — **done (2026-07-26)**

Re-run `--stats` after 5a and re-classify what remains before spending any further model calls.
The classes standing after 5a, in descending order, are `extra_arg` (2065; `subj` 936 of them),
`missing_arg` (1317), `role_mismatch` (1250). Determine for each whether it is an LLM error, a
`derive_unit` gap, or a Layer-4 error, and route accordingly — Phase 4a's whitelist work is the
model for how narrowly such a decision should be scoped.

**Landed**: classifying every violation by its dep-tree context isolated three mechanical
classes — a `derive_unit` over-generation (coordinating conjunctions promoted to predicates,
−93), a copula/modal double-listing (−99), and adverbial obliques (−67) — for **5105 → 4846**.
Two variants of the copula rule that *remap* rather than suppress were measured and rejected
(−6 and −2). Six tests. See `CORRECTIONS.md`.

### Phase 5c — tighten `--fix`'s acceptance criterion — **done (2026-07-26)**

`_fix_canto` accepts a regeneration when `len(soft_after) < len(soft_before)`. This total-count
test admits regressions in kind: the Phase 4b round introduced `unknown_role` 0 → 2, a role
outside the frozen vocabulary, in exchange for a net count drop. Require no new violation
*kind* in addition to the count decrease. (Landed as `_is_improvement` in `skel/skel.py`.)

(The related per-unit checkpointing bug — `_fix_canto` wrote the TSV only after finishing an
entire canto, losing hours of work on any interruption — was fixed in `1955ff5`.)

### Phase 5d — route Layer-4 errors back to Layer 4 — **done (2026-07-26): nothing to route**

Some residual classes are likely `dep` errors rather than `skel` errors — most visibly the 105
`expl` cases, where the dep tree marks a clitic pleonastic and the LLM reads it as a real
object. Layer 5 doubling as an audit of Layer 4 is the stated design intent (see
[`README.md`](README.md) and [`../PLAN.md`](../PLAN.md)); such cases belong in
`dep/CORRECTIONS.md`, not in a skel whitelist.

**Measured, and the hypothesis is disproved**: 99 of the 107 such violations cite the clitic of
an inherently pronominal verb (`si`/`mi`/`s'`/`ti`/`ci` — `andarsene`, `muoversi`, `rimanersi`),
which Layer 4 tags correctly as `expl`; the LLM promotes it to `obj` (78) or an oblique (18).
That is an LLM reading against the frozen UD convention, so the class belongs to 5e, and no
Layer-4 correction was opened.

### Phase 5e — `--fix` on what actually remains — **open, the only phase left**

Only after 5a–5d, and only on classes triage has confirmed are genuine LLM misreadings. As of
4846 those are: `extra_arg subj` 936 (73% citing a token unrelated to the predicate in the dep
tree — enjambment and pro-drop resolution), `missing_arg` on explicit `obl` (716) and `obj`
(265) dep edges the LLM simply did not list, `role_mismatch` 1250 (99.9% on edges both sides
see), and the `expl` clitics from 5d. `--fix` now runs under the Phase 5c acceptance criterion,
and its flagged-unit workload is down from 2235 to what remains after Δ1073 of Phase 5.

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
