# skel — Layer 5 Phase 5 plan: deterministic elimination of the residual soft violations

Status as of 2026-07-28: `make -C skel check` reports **0 hard, 4327 soft** violations across
all 100 cantos (17438 at the first full-corpus measurement → 7776 after the Phase 4a checker
refinements → 5919 after one round of Phase 4b `--fix` LLM regeneration → 5105 after Phase 5a →
4846 after Phase 5b → 4615 after the Phase 5e `--fix` round → 4327 after Phase 5f's rule L). The
project goal is unchanged: **0 soft violations** — soft divergences are rule mismatches to
eliminate, not a baseline to tolerate.

**All of Phase 5 has now run** (see [`CORRECTIONS.md`](CORRECTIONS.md) for each round's rules,
measurements and rejected candidates). Its central finding, stated up front: **`--fix` yields
about 0.11 violations per LLM call and that rate does not depend on how the flagged set is
composed** — clearing the structurally unfixable units out of it (Phases 5a/5b, Δ1073 for zero
calls) did *not* raise the success rate. What remains is closed by measuring classes and
normalizing, not by more model calls. Everything after the *Landed phases* table below is the
measurement that motivated this plan; its violation counts are **pre-5a** unless stated
otherwise.

**Resuming work? Go to [*Next session — start here*](#next-session--start-here) directly below.**
Rule L landed as Phase 5f (−288, exactly as measured); the queued task is now the
secondary-predicate gate for the `xcomp` pairs, which must be **measured before implementing**.

This plan supersedes the Phase 0–3 plan (same filename, removed in `16f1c55` once those phases
landed). It exists because Phase 4b's LLM-regeneration approach had measurably stalled, and the
measurement explained *why* in a way that changed what was done next.

---

# Next session — start here

## 0. Rule L landed — Phase 5f, 4615 → 4327 (2026-07-28)

`_oblique_lemma_refinement` in `dante_corpus/skel.py`, consulted from the `elif grole != drole:`
branch of `_classify_divergence`; `case_children` built once at the top of that function from
`dep_index_by_pos`. Three tests in `tests/test_skel.py` (accepted case, cross-lemma pair still
flagged, `case`-child case still flagged), 100 passing. Checker-side only — no `--repair` rule,
no artifact touched, no model call. The measured −288 landed exactly, entirely in
`role_mismatch` (1214 → 926). Write-up: `CORRECTIONS.md`, *Checker Phase 5f*.

## 1. Measure the secondary-predicate gate

`xcomp` vs `obj` (170) + `xcomp` vs `subj` (60) are **predicative complements**, not nominalized
infinitives (that hypothesis was measured and rejected — 8 and 15 respectively; see the *Next
round* section below for the evidence and examples). Candidate gate: accept the pair only when
the predicate already carries **another** `obj`/`subj` argument, i.e. the object-complement
configuration ("mi chiamaste **Ciacco**"). **Measure it before implementing** — a blanket
`xcomp`≡`obj` equivalence would swallow genuine object mislabeling.

### How to measure a candidate rule

There is no checked-in harness for this; every rule in this document was measured with a
throwaway script (scratchpad, not committed) that mirrors `skel/skel.py`'s `stats()` loop:
iterate `api.cantos()` × `dep.sentence_groups()`, call `skel_driver._classify_violations(...)`
per unit, and either monkeypatch `dante_corpus.skel._classify_divergence` / `derive_unit` or
filter the returned violations. Run it from `skel/` (`uv run <script>.py`) so the driver module
imports; report the full-corpus by-kind counter, and always measure the **negative** variant of
a rule too (the narrower gate) — twice in Phase 5 the two differed and that difference was the
finding.

---

## Phase 5e — `--fix` on what actually remains — **done (2026-07-28), 4846 → 4615**

One full pass, all three canticles, 2037 flagged units attempted:

| metric | measured |
|---|---|
| units accepted | **178 (8.7%)** |
| units that regressed | **0** (Phase 5c's criterion held; `unknown_role` stayed 2) |
| violations removed | **231**, i.e. ~0.11 per LLM call |
| per class | extra_arg −104 (−5.2%), missing_arg −66 (−5.1%), role_mismatch −36 (−2.9%), extra_tuple −21 (−11.9%), membership −2, missing_tuple −2 |

**The predicted rise in success rate did not happen.** This plan expected the rate to exceed the
pre-Phase-5 10.5%, because 5a/5b had removed the structurally unfixable units from the
denominator; it came in at 8.7%. The two figures are statistically indistinguishable (the
earlier one was 2 of 19 units), and the conclusion is stronger than "regeneration is expensive":
**the yield per call is flat**, so composing a better flagged set does not make `--fix` a
different tool. It stays useful as a finishing pass, not as the instrument that reaches zero.

**The stop rule applies: no second pass.** No class moved more than 11.9%, and the three large
ones moved 2.9-5.2% — by this plan's own criterion, a class that barely moves after a full pass
is checker-side, not an LLM error awaiting another attempt.

## Next round — normalize the systematic `role_mismatch` pairs

`role_mismatch` (1214) moved least of all while sitting **99.9% on edges both sides see**, and
its pair distribution is far from a scatter of one-off disagreements:

```
'xcomp'  vs 'obj'   170    'obl:a'  vs 'obl'   94    'obl:a' vs 'obj'  92
'obl:di' vs 'obl'    84    'obj'    vs 'subj'  81    'subj'  vs 'obj'  67
'xcomp'  vs 'subj'   60    'obl:di' vs 'obj'   38    'obl:da' vs 'obl' 36
```

Both large pairs were measured the same way every rule in this document was (monkeypatch +
full-corpus re-count), immediately after the 5e round:

1. **Rule L — `obl:<lemma>` given vs bare `obl` derived: −288, measured — landed as Phase 5f.**
   `derive_unit` emits a
   bare `obl` in exactly one situation: the argument has no `case` child naming the preposition.
   In **all 288** instances that is the case (the strict and loose variants of the rule return
   the identical set), and the missing preposition is typically fused into the token itself — a
   clitic dative (`che nel lago del cor **m'**era durata`: derive_unit `obl`, LLM `obl:a`) or a
   preposition+article contraction. The LLM naming it is therefore **strictly more informative,
   not a disagreement** — the same argument the Phase 2 authority model already makes for
   pro-drop subjects, and the mirror of `--repair`'s `role_label` rule, which rewrites the
   *opposite* direction (given bare `obl`, derived `obl:<lemma>`) because the dep tree makes it
   explicit. It landed as Phase 5f and removed **more than the entire 5e `--fix` pass, at zero
   calls.**
2. **`xcomp` vs `obj` (170) / `xcomp` vs `subj` (60) — the nominalized-infinitive hypothesis is
   wrong.** Gating on the argument being an infinitive removes 8; on its being any verb form,
   15. The actual population is **predicative complements**: the arguments are nouns (100),
   adjectives (73) and pronouns (31) — "mi chiamaste **Ciacco**", "**tal** mi fece la bestia",
   "si tegnon gran **regi**", "le mura mi parean che **ferro** fosse". The dep tree attaches an
   object complement as plain `obj`/`nsubj` (there is no copula to hang it from), while the LLM
   labels it a complement predicated of that argument — which Phase 1 already canonicalizes
   `attr` → `xcomp` for. A blanket `xcomp`≡`obj` equivalence would swallow genuine
   object-mislabeling, so this needs a configurational gate (e.g. the predicate already carries
   another `obj`/`subj` argument, the secondary-predicate configuration) — measure that before
   proposing it.

The `subj`/`obj` reversals (81 + 67) are genuine reading disagreements and stay `--fix` material
— but as measured above, that route removes them at 0.11 per call, so they are last, not first.

## Landed phases

| phase | what landed | measured |
|---|---|---|
| **5a** | Rule C (coordination normalization) + Rule D (`nmod` oblique of a derived argument) | 5919 → **5105** |
| **5b** | no conjunction promoted to predicate; copula/modal double-listing suppressed; adverbial obliques accepted | 5105 → **4846** |
| **5c** | `--fix` acceptance requires no new violation *kind* (`_is_improvement`) | — |
| **5d** | audit of the `expl` class: Layer 4 is right, nothing to route back | — |
| **5e** | one full-corpus `--fix` pass, 178/2037 units accepted, none regressed | 4846 → **4615** |
| **5f** | Rule L (`obl:<lemma>` given vs bare `obl` derived), checker-side, 0 calls | 4615 → **4327** |

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
| `--fix`, full corpus pass (Phase 5e, **actually measured**) | **231** | **2037 LLM calls** |
| **Phases 5a + 5b (deterministic)** | **1073** | **0 LLM calls, minutes** |
| **Phase 5f, one rule (deterministic)** | **288** | **0 LLM calls, minutes** |

The deterministic phases delivered roughly **4.6× the `--fix` pass that followed them, instantly**
— and the extrapolation above turned out to be optimistic by 2×, because the 8.7% success rate
came with fewer violations fixed per accepted unit than inferno 1 had suggested. They also cut
the `--fix` workload from 2235 to 2037 flagged units, removing precisely the units regeneration
could never have fixed; that did **not** raise the success rate (10.5% → 8.7%), which is the
Phase 5e result.

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
