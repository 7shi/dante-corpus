# skel — Layer 5 Phase 5 plan: deterministic elimination of the residual soft violations

Status as of 2026-07-28: `make -C skel check` reports **0 hard, 3876 soft** violations across
all 100 cantos (17438 at the first full-corpus measurement → 7776 after the Phase 4a checker
refinements → 5919 after one round of Phase 4b `--fix` LLM regeneration → 5105 after Phase 5a →
4846 after Phase 5b → 4615 after the Phase 5e `--fix` round → 4327 after Phase 5f's rule L →
4097 after Phase 5g's rule M → 4068 after Phase 5h's rule N → 4042 after Phase 5i's Layer-4
correction → 3924 after Phase 5j's rule O and lemma normalization → 3876 after Phase 5k's rules
P and Q). The project goal is unchanged:
**0 soft violations** — soft divergences are rule mismatches to eliminate, not a baseline to
tolerate.

**Phases 5a-5k have run** (see [`CORRECTIONS.md`](CORRECTIONS.md) for each round's rules,
measurements and rejected candidates). The central finding, stated up front: **`--fix` yields
about 0.11 violations per LLM call and that rate does not depend on how the flagged set is
composed** — clearing the structurally unfixable units out of it (Phases 5a/5b, Δ1073 for zero
calls) did *not* raise the success rate. What remains is closed by measuring classes and
normalizing, not by more model calls.

**How to read this file.** Only *Next session — start here* describes work still to do;
everything from *Phase 5e* onward is the historical record that produced it, and **its violation
counts are stale by construction** — each section states the state it was written at. The
authoritative current numbers are the status line above and `--stats`.

**Resuming work? Go to [*Next session — start here*](#next-session--start-here) directly below.**
Rules L, M, N, O, P and Q landed as Phases 5f/5g/5h/5j/5k (−288, −230, −29, −118, −48; all
checker-side, zero model calls), and Phase 5i closed the decidable half of the **clitic-case
question** by correcting Layer 4 (−26, zero model calls, no checker change). `role_mismatch` is
down from 1214 to **475**: the `obl:<lemma>` pairs are exhausted and so is the mechanical half
of the clausal cluster. **The queued item is now the two big classes, `extra_arg` (1887) and
`missing_arg` (1239) — together 80% of what is left, and untouched since Phase 5b.**

This plan supersedes the Phase 0–3 plan (same filename, removed in `16f1c55` once those phases
landed). It exists because Phase 4b's LLM-regeneration approach had measurably stalled, and the
measurement explained *why* in a way that changed what was done next.

---

# Next session — start here

## Where the tree is

Everything through Phase 5k is **committed** — the rule commits and the Layer-4 correction are
the most recent `skel:`/`dep:` entries in `git log`, and nothing is left uncommitted for a next
session to discover. Confirm before starting:

```bash
make -C skel check      # expect: 0 hard, 3876 soft
make -C dep check       # expect: 0 hard, 0 soft  (Phase 5i edited dep artifacts)
uv run pytest -q        # expect: 115 passed
make -C skel stats      # by-kind + the role_mismatch pair table the sections below cite
```

If those numbers differ, the sections below are describing a different state — re-measure before
trusting any count in this file.

## 0. Rules L, M and N landed — Phases 5f/5g/5h, 4615 → 4068 (2026-07-28)

Three checker-side acceptances in the `elif grole != drole:` branch of `_classify_divergence`,
all one-directional, all zero model calls and zero artifacts touched:

- `_oblique_lemma_refinement` (rule L, −288): given `obl:<lemma>` vs derived bare `obl`.
- `_predicative_complement` (rule M, −230): given `xcomp` vs derived `obj`/`subj`. **Shipped
  ungated** — the secondary-predicate gate this plan proposed was measured and abandoned; see
  `CORRECTIONS.md`'s Phase 5g section for the 230/227/163 measurement and why the gate separates
  the wrong thing (object complements from copular predicate nominals, both correct readings).
- `_case_marked_object` (rule N, −29): given `obl:<lemma>` vs derived `obj`/`subj` **when the
  argument carries a `case` child naming that same preposition**.

`case_lemmas` (position → normalized `case`-child lemmas, built once at the top of
`_classify_divergence`) serves L and N both. Nine tests in `tests/test_skel.py`, 106 passing.
`role_mismatch` 1214 → **667**.

Phase 5j then finished the `obl:<lemma>` pairs off (−118, `role_mismatch` 641 → **523**): rule O
(`_co_present_preposition`, −61) accepts a given lemma that is *another* `case` child of the same
argument ("**in su** le porte", "dietro **a** noi" — the tree carries both markers,
`derive_unit` reports one), and `_PREP_LEMMA_NORM` was rebuilt from every `case`-child word form
in `dep/` (−57), so contractions (`nel` → `in`, `dal` → `da`) and archaic spellings stop reading
as disagreements. `case_lemmas` now serves L, N and O. The two-directional variant of rule O was
measured at a further −30 and **rejected**: in the mirror direction the given preposition sits
elsewhere in the unit (17), is an `advmod`/`obl` token (7), or is absent from the unit
altogether (5), and one gate cannot separate the Layer-4 inconsistency from the LLM invention.

## 1. The clitic-case question — half closed as Phase 5i, half parked

**Done (−26).** Reading the 97 answered the question this section used to ask: the population is
**mixed**, not uniformly dative — `mi pesa`, `ti noccia`, `li convien fuggire` are Layer-4
mistags, but `m'avea 'mmonito` and `ti priego` are plain accusatives where the LLM is wrong. So
neither a checker rule nor a blanket reroute was available. What *is* available is a structural
subset needing no case feature: in **30** of the 97 the predicate carries a **second** `obj`
child, and UD allows at most one `obj` per predicate — the tree contradicts itself regardless of
the LLM, and the non-clitic object is the direct one. 26 survived hand-verification against
their terzine and were retagged in `dep/` (22 → `iobj`, 4 → `obl` for partitive `ne`); the other
4 were rejected. Each closed its Layer-5 divergence, `dep --check` stayed 0/0, and no checker
code or skel artifact changed. Full list in [`../dep/CORRECTIONS.md`](../dep/CORRECTIONS.md).

**Parked, with a measured reason.** The other **67** (no second `obj`, nothing structural to go
on) and the **30** mirror-direction cases (Layer 4 `iobj`, LLM `obj` — `mi bagna`, `mi
tormenta`, `ti conforta`, `lui non aita`; several look like Layer-4 datives over real
accusatives) both need a Layer-2 case feature or a clitic lexicon. The project has twice
preferred a structural check to a lexicon (the control-subject authority model, Phase 2), so
neither is opened here.

**A wider Layer-4 finding, not acted on**: corpus-wide, **231** predicates carry two or more
`obj` children — 84 with a clitic, 147 without. The non-clitic majority splits into flattened
coordinations (`Ali hanno late, e colli e visi umani`) and object complements (`mi chiamaste
Ciacco`, `li chiama orbi`), the latter being exactly what skel's rule M already accepts
checker-side. A dep `--check` rule for "at most one `obj` per predicate" would put Layer 4 at
231 soft; opening it is its own round, and it would need the coordination half re-attached
(`conj`) rather than exempted.

**How to regenerate any of these populations** (the measurement scripts were throwaways; see
*How to measure a candidate rule* below): keep the violations whose detail starts with
`role_mismatch` where one side is `obl:<lemma>` and the other is `obj`/`subj`, and bucket by
(a) whether `dep_index_by_pos` holds a `case` child of the argument and with which normalized
lemma, (b) the argument's Layer-2 POS, and (c) whether the predicate has another `obj` child.
The 67 are `given obl:* / derived obj|subj` + no `case` child + pronoun POS + no second `obj`;
the 30 mirror cases are `given obj|subj / derived obl:*` with dep deprel `iobj`.

## 2. Next: the two big classes — `extra_arg` and `missing_arg`

**This is the head item now.** `extra_arg` **1887** (of which `subj` 896, ∅ 131) and
`missing_arg` **1239** are untouched since Phase 5b and together are **80%** of what is left.
The move is a Phase-5b-style full re-triage by dep-tree context — classify every instance by how
the cited argument attaches to the predicate (direct child with a deprel `derive_unit`'s map
omits / indirect descendant at depth 2 / `conj`-relative / unrelated / pro-drop ∅), exactly as
the *Measured cost* section below did for `extra_arg` at 5919, and re-read that table's shape at
the current count before proposing anything. Do **not** guess further rules from the pair table:
what remains there is thin and each surviving pair has been triaged already.

Post-5k pair table (`role_mismatch` 475 — the `obl:<lemma>` pairs and the mechanical half of the
clausal cluster are gone):

```
'obj' vs 'subj'  81    'subj' vs 'obj'  67    'obl:a' vs 'obj'  61
'obj' vs 'obl:a' 30    'xcomp' vs 'obl' 25    'subj' vs 'xcomp' 22
'obj' vs 'obl'   15    'obj' vs 'xcomp' 15    'xcomp' vs 'obl:di' 13
```

Everything in it has a recorded verdict, so read them as *closed*, not as candidates:

- `obl:a` vs `obj` (61) and its mirror (30) are the clitic-case population section 1 parked.
- `xcomp` vs `obl`/`obl:<lemma>` (≈55, spread across several rows) is the predicative-PP half of
  the clausal cluster Phase 5k deliberately left flagged: separating the copular readings needs
  a verb lexicon (`essere`/`stare`/`parere`), which this project refuses on principle.
- `subj` vs `xcomp` (22) and `obj` vs `xcomp` (15) are the mirror directions rules M and Q keep
  flagged on purpose — there the dep tree is explicit and the LLM contradicts it.
- The `subj`/`obj` reversals (148) are genuine reading disagreements and the one class that is
  real `--fix` material. They stay **last**: that route removes them at 0.11 violations per
  call, so they are worth one user-run regeneration pass only once the deterministic work is
  exhausted.

### How to measure a candidate rule

There is no checked-in harness for this; every rule in this document was measured with a
throwaway script (scratchpad, not committed) that mirrors `skel/skel.py`'s `stats()` loop and
monkeypatches `dante_corpus.skel._classify_divergence`. Run it **from `skel/`** (`uv run
<script>.py`) so the driver module imports. The skeleton, which every Phase 5 measurement used:

```python
import sys; sys.path.insert(0, ".")
import skel as driver
from dante_corpus import api, dep, skel

orig = skel._classify_divergence

def wrapper(given, derived, dep_index_by_pos=None, morph_pos_by_position=None):
    vs = orig(given, derived, dep_index_by_pos, morph_pos_by_position)
    ...  # classify/filter vs; `dep_index_by_pos` is the whole dep tree of the unit,
         # `morph_pos_by_position` the Layer-2 POS, both keyed by (line, token)
    return vs

skel._classify_divergence = wrapper
driver.skel._classify_divergence = wrapper   # both bindings, or the driver keeps the original

for canticle in api.canticles():
    for number in api.cantos(canticle):
        data = skel.load_skel(canticle, number)
        morph_rows, np_rows = driver._morph_rows(canticle, number), driver._np_rows(canticle, number)
        dep_rows = driver._dep_rows(canticle, number)
        lines = api.canto(canticle, number).lines()
        text_by_no = {ln.no: ln.text for ln in lines}
        nos, texts = [ln.no for ln in lines], [ln.text for ln in lines]
        for unit in dep.sentence_groups(nos, texts, dep.MAX_UNIT_LINES):
            if any(no not in data for no in unit):
                continue
            driver._classify_violations(
                unit, [text_by_no[no] for no in unit],
                {no: list(data[no]) for no in unit}, morph_rows, np_rows, dep_rows)
```

Token positions are 1-based over the **alpha-only** tokens of a line
(`[t for t in tokenize(text) if has_alpha(t)]`, `dante_corpus.tokenizer`) — indexing raw
`tokenize` output instead silently misaligns every word you print.

Report the full-corpus by-kind counter, and always measure the **negative** variant of a rule
too (the narrower gate). Three times in Phase 5 that mattered: rule L's two variants were
identical (which was the evidence), rule M's gate turned out to separate the wrong thing, and
rule N's "narrow" bucket was the only sound part of its class.

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

## Next round — normalize the systematic `role_mismatch` pairs — **historical, written at 4615**

*(Both items below have since landed, as Phases 5f and 5g. Kept for the measurements and the
rejected variants; the pair counts are pre-5f.)*

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
   `attr` → `xcomp` for. The configurational gate proposed here (the predicate already carrying
   another `obj`/`subj` argument) **was measured and abandoned** — it admits 227 of 230 on the
   given side and separates the wrong thing on the derived side. Landed ungated as Phase 5g's
   rule M, −230; see `CORRECTIONS.md`.

The `subj`/`obj` reversals (81 + 67) are genuine reading disagreements and stay `--fix` material
— but as measured above, that route removes them at 0.11 per call, so they are last, not first.
(Still true post-5h, and still the plan: see *Next session*, section 2.)

## Landed phases

| phase | what landed | measured |
|---|---|---|
| **5a** | Rule C (coordination normalization) + Rule D (`nmod` oblique of a derived argument) | 5919 → **5105** |
| **5b** | no conjunction promoted to predicate; copula/modal double-listing suppressed; adverbial obliques accepted | 5105 → **4846** |
| **5c** | `--fix` acceptance requires no new violation *kind* (`_is_improvement`) | — |
| **5d** | audit of the `expl` class: Layer 4 is right, nothing to route back | — |
| **5e** | one full-corpus `--fix` pass, 178/2037 units accepted, none regressed | 4846 → **4615** |
| **5f** | Rule L (`obl:<lemma>` given vs bare `obl` derived), checker-side, 0 calls | 4615 → **4327** |
| **5g** | Rule M (given `xcomp` vs derived `obj`/`subj` — secondary predication), 0 calls | 4327 → **4097** |
| **5h** | Rule N (given `obl:<lemma>` vs derived `obj`/`subj` with a matching `case` child) | 4097 → **4068** |
| **5i** | Layer-4 correction: 26 double-`obj` clitics retagged `iobj`/`obl` in `dep/` | 4068 → **4042** |
| **5j** | Rule O (co-present prepositions) + `_PREP_LEMMA_NORM` rebuilt from the corpus | 4042 → **3924** |
| **5k** | Rule P (`ccomp`≡`xcomp`) + rule Q (clause attached as `obj`/`subj`) | 3924 → **3876** |

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

## Measured violation anatomy — **historical, measured 2026-07-26 at 5919 (pre-5a)**

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

## Candidate rules — all measured before proposing — **historical, measured at 5919 (pre-5a)**

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
| **Phase 5g, one rule (deterministic)** | **230** | **0 LLM calls, minutes** |
| **Phase 5h, one rule (deterministic)** | **29** | **0 LLM calls, minutes** |
| **Phase 5i, Layer-4 correction (hand-verified)** | **26** | **0 LLM calls, 26 dep rows** |
| **Phase 5j, one rule + normalization (deterministic)** | **118** | **0 LLM calls, minutes** |
| **Phase 5k, two rules (deterministic)** | **48** | **0 LLM calls, minutes** |

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
