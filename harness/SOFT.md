# The Soft Classification, Audited

The companion to [`HARD.md`](HARD.md), asked before the soft reduction pass is
opened: **is the soft classification itself sound — not "is it correctly
implemented", but "does its justification hold"?** The hard track closed at 0
([`stages/05.md`](stages/05.md) S5.7), so the whole remaining mass is soft: 5,014
findings that would now select every remaining design pass. The counter selects
work but never decides it (S5.4/S5.5 discipline 1), so the classification that
produces those 5,014 was audited before being allowed to drive anything.

**Status**: audit record only, filed as [`stages/06.md`](stages/06.md) record S6.1 —
Stage 6 opens on this audit, as Stage 5 opened its clausal work on
[`HARD.md`](HARD.md)/S5.4. No repair rule was designed here, no artifact was
edited, and no rule-choosing number was read off gold. Run 2026-08-30 against the
tree at S5.8 (`ef0bf47`, working tree clean; `make check` 0 hard / 5,014 soft;
suite at 938 per [`PLAN.md`](PLAN.md), not re-run here). §§2–5 were produced
**gold-closed** apart from the two calibration sweeps HARD.md §2 already
sanctions (gold run *through the checker*, never read as an answer key); §6 is a
readout that deliberately opens gold *after* the fact and decides nothing. Full
disclosure in §7.

---

## 1. The question

`make check` splits `skel.validate_unit`'s output by `kind`: `tag` → soft,
everything else → hard ([`recon/check.py`](recon/check.py)
`_classify_violations`). HARD.md established what the hard side rests on — an
exception-free format impossibility, plus the derivation's own closure property.
The soft side — 5,014 findings against the 70 HARD.md audited, 72× as many —
rests on something else entirely, and the question has four parts, the same
four HARD.md asked: what the findings assert,
where their authority comes from, whether the severity (soft, not hard) is
consistent with the contract's own taxonomy, and whether any reading of the
positions shows the checker misfiring.

There is one extra question the hard side did not raise. Hard is a property of
the artifact alone. **Soft is, in 97% of its mass, a diff against
`derive_unit`** — a deterministic rule system tuned on this very corpus. Since
`harness/`'s stated mission is to *replace* that top-down machinery with an
autonomous model ([`PLAN.md`](PLAN.md) §1), "how far is the model from the rule
system" is exactly the measurement whose meaning cannot be assumed. So the audit
also asks: **what is the counter's zero point, and what does reaching it mean?**

## 2. What the classification is

### 2.1 Three families, very unequal

| family | what it compares | classes | count | share |
|---|---|---|---:|---:|
| divergence | artifact vs `derive_unit` | `missing_arg` 1,646, `extra_arg` 2,114, `role_mismatch` 573, `missing_tuple` 490, `extra_tuple` 43 | **4,866** | 97.0% |
| membership | artifact vs frozen L2/L3/L4 | `membership` | **146** | 2.9% |
| artifact-internal | artifact vs itself | `dual_role` 2, `unknown_role` 0 | **2** | 0.04% |

Corpus shape behind that: 3,477 parse units, of which **2,126 (61.1%) carry at
least one soft finding**, spread over **3,707 distinct predicate positions**.
This is not a residue at the edges — it is the majority of the corpus.

### 2.2 The published contract — and here there is no gap

Unlike the clausal invariant (HARD.md §2 found it unpublished),
[`skel/README.md`](../skel/README.md) 82–88 publishes the soft bar in full and
in the same three families: the nominal membership rule, `dual_role` (rule EG,
named as "the only soft check that compares the artifact with *itself*"), and
"the central check, every divergence from `derive_unit`". It also publishes the
severity: **"reported, not enforced; measure-then-freeze"**. The soft side is
therefore documented exactly as implemented; the audit's questions are about
what that documented thing measures, not about a documentation gap.

### 2.3 Parity and calibration

`recon/check.py` wraps the same `validate_unit` and the same tag→soft split that
`skel/skel.py --check` applies to gold; only the artifact root differs. Gold
scores **0 hard / 0 soft** under it (re-verified live: `uv run python -m
harness.recon.check --root skel --stats`). As in HARD.md §2 this is the
sanctioned use of gold — calibration of the bar, not a target — and it
establishes the bar is satisfiable. §4.2 examines *how* gold satisfies it, which
is where the soft side parts company with the hard side.

## 3. The 5,014 positions, audited gold-closed

Method: every soft finding in the corpus was joined, position by position,
against the frozen layers only — L1 tokens, L2 morphology, L4 dependencies —
asking of each cited argument where it sits in the frozen tree *relative to the
citing predicate*. No gold file was opened. (`missing_tuple`/`extra_tuple` name
a predicate, not an argument, and are tabulated separately.)

**`extra_arg` — 2,114** (the artifact cites an argument the derivation does not):

| evidence at the cited position | count |
|---|---:|
| the argument is `(0,0)` — pro-drop asserted, role always `subj` | 614 |
| an L4 child of the predicate under a **non-argument** deprel | 889 |
| elsewhere in the tree (not a child of the predicate or its aux/conj head) | 600 |
| an L4 child of the predicate's aux/coordination head | 11 |
| **an L4 argument-child of the predicate** | **0** |

The last row is the checker's self-consistency: had the argument been an L4
argument-child, `derive_unit` would have derived it and the finding could not be
`extra_arg`. It is 0, as it must be. The 889 are dominated by one pattern —
`advcl` cited as `obl` **568**, `advmod` as `obl` 110, `advcl` as `xcomp` 92,
`advcl` as `ccomp` 43, all others 76: the model reads adverbial clauses and
adverbs as oblique arguments, where `derive.py`'s `ARG_DEPRELS` does not.

**`missing_arg` — 1,646** (the derivation derives an argument the artifact omits):

| evidence at the derived position | count |
|---|---:|
| an L4 argument-child of the predicate | 1,233 |
| an L4 argument-child of the predicate's aux/coordination head | 359 |
| elsewhere in the tree | 52 |
| an L4 child under a non-argument deprel | 2 |

**1,592 of 1,646 (96.7%) are arguments L4 itself attaches to the predicate** and
the artifact simply does not cite. Whatever one thinks of the derivation, this
class is grounded in the model's own frozen inputs.

**`role_mismatch` — 573** (both sides cite the argument; they disagree on the label):

- 570 of 573 cite an L4 argument-child of the predicate; 2 a non-argument child;
  1 elsewhere. This class is **not** about whether there is an argument — the two
  readings agree there is one — only about its name.
- 377 of 573 (65.8%) are bare `obl` against a lemma-qualified `obl:<prep>`
  (`obl:di` 129, `obl:in` 83, `obl:come` 70, `obl:a` 24, `obl:per` 19, `obl:da`
  15, others 37). The next largest groups are genuine role disagreements:
  `obj` vs `subj` 45, `subj` vs `obj` 29, `obl` vs `obj` 19, `subj` vs `xcomp` 16.

**`membership` — 146**: every one has an oblique role (`obl`/`obl:<prep>`) and
cites a position that heads no NP, is no pronoun, and is no registered
predicate — L4 deprel `advmod` 111, `mark` 15, `case` 8, `advcl` 7, `amod` 3,
`conj` 1, `det` 1. A single construction family (obliques anchored on adverbs and
markers), not scattered noise.

**`missing_tuple` — 490**, by the size of the frame the derivation would attach
to the unregistered predicate: 1 argument 263, 2 arguments 147, 3 arguments 76,
4 arguments 3, 6 arguments 1. §4.4 uses this distribution.

**`extra_tuple` — 43**; **`dual_role` — 2** (`paradiso 1:125` `arg (125,1)`
listed as `'obj'` and `'obl'`; `paradiso 9:110` `arg (110,1)` as `'iobj'` and
`'obl:di'`); **`unknown_role` — 0**.

**Reading.** The classes are structurally distinct, not one phenomenon counted
five ways. `missing_arg` and `role_mismatch` (2,219 findings) are anchored on L4
edges both sides recognize. `extra_arg` splits into three unrelated
sub-populations, only one of which (the 600 "elsewhere") looks like plain error.
No class shows the checker flagging something that resolves.

## 4. The basis, tested

### 4.1 Soft is exactly "distance from `derive_unit`" — and the derivation is *not* quite clean

The first thing to establish is that the divergence family means what it says.
Feeding `derive_unit`'s own output back through the checker as if it were the
artifact, unit by unit over all 100 cantos, returns **0 soft violations** — so
the divergence family is a true diff whose zero is the derivation's output, with
no residue of its own.

That sweep also returned **1 hard violation**, which is a correction to
[`HARD.md`](HARD.md) §4.3. That section listed "a case where `derive_unit`
itself emits an unresolved clausal citation" as a falsification attempt and
reported none, "impossible by construction". One exists:

```
paradiso 18:83  [clausal] xcomp argument (84, 3) is not a predicate in this unit
```

In the gapped coordination *"…rendili longevi, / ed essi teco le cittadi e '
regni"*, the derivation's gapping machinery emits `rendili xcomp → (84,3)`
(`teco`, an L4 `orphan` remnant), but the promotion step (`CLAUSE_HEAD_DEPRELS`,
deprel-driven) never registers `(84,3)` as a predicate — the remnant path
bypasses the promote-then-cite ordering HARD.md §4.1 relied on. HARD.md's
argument survives at 3,476 of 3,477 units and the closure property holds for the
deprel-driven path; the unqualified "by construction" claim does not. Recorded
here rather than fixed: it is one position, it is in the derivation and not in
the recon corpus, and no rule is being designed in this record.

### 4.2 The zero point is tolerance-mediated, and the tolerances were fitted on gold

This is the audit's central finding, and it has no analogue on the hard side.

`_classify_divergence` does not report the raw diff. Every candidate divergence
is offered to a chain of named tolerance rules from the 130-rule registry — 88
of the 130 are tolerance rules for these soft classes (37 `extra_arg`, 20
`missing_arg`, 19 `role_mismatch`, 6 `extra_tuple`, 3 `membership`, 2
`missing_tuple`, 1 `dual_role`) — and a match suppresses the finding. Disabling
exactly those 88 and re-running the checker gives the raw diff:

| artifact | soft, as reported | soft, tolerances disabled | excused |
|---|---:|---:|---:|
| recon corpus | 5,014 | **11,998** | 6,984 |
| gold | **0** | **3,250** | 3,250 |

Read the gold row twice. **Gold is not what the derivation derives.** It
disagrees with `derive_unit` at 3,250 positions — 1,048 `missing_arg`, 963
`role_mismatch`, 692 `extra_arg`, 448 `extra_tuple`, 82 `membership`, 17
`missing_tuple` — and reaches 0 solely because every one of those disagreements
falls inside a published tolerance. (The independent census agrees: excluding
rule EG, whose gate is queried once per unit rather than per finding, the
registry fires **3,256** times on gold across 61 rules, and **7,000** times on
recon across 57 rules.)

So "0 soft" does not mean "agrees with the derivation". It means **"every
disagreement with the derivation has a shape that the registry names"**.

Where did those shapes come from? The contract says so itself:
[`skel/README.md`](../skel/README.md) records that the 130 rules were
"incrementally censused, **measured by violation diff**, tested, systematized",
and [`skel/PHASE5.md`](../skel/PHASE5.md) §2 prints the ledger of that process
as a descending violation count (5,919 → 5,105 → … → 2,084 → Phase 6), each step
labelled with the rule letters that produced it. The tolerance boundary was
drawn *by looking at where gold and the derivation disagreed and excusing it*.
The hit census shows the fit down to single positions: on gold, rules **DG, DH,
DN, DS, EA and ED fire exactly once each** — six rules whose entire corpus-wide
job is to excuse one gold position apiece.

Three consequences follow, and they are the reason this record exists:

1. **The soft counter is a conformance measure, not a correctness measure.** Its
   zero is "indistinguishable from `derive_unit` *modulo* the tolerances fitted
   on gold's own analyses". An analysis that is linguistically defensible but of
   a shape gold never happened to produce scores as a violation; one that is
   dubious but shaped like gold's does not.
2. **It is therefore not gold-independent in the way `make check`'s hard side
   is.** HARD.md could rest hard on format impossibility with gold used only for
   calibration. Nothing equivalent is available here: the soft bar's *boundary*
   carries gold's fingerprints even though the checker opens no gold file. This
   does not make soft findings invalid — §3 shows most of them are anchored on
   frozen-layer evidence — but it does mean that **driving the soft count toward
   0 is materially closer to teaching to the test than the hard track was**, and
   [`PLAN.md`](PLAN.md) §4 item 1's prohibition should be read with that in mind.
3. **The registry is load-bearing in different places for the two artifacts.**
   Gold's excusals concentrate in `CY` 858, `L` 341, `Y` 203, `I` 193, `J` 189;
   recon's in `J` 1,698, `I` 1,086, `AV` 923, `AB` 605, `CS` 592. Every rule that
   fires on recon also fires on gold (4 fire only on gold: DG, DI, DS, EA), so
   recon exercises a subset of the sanctioned shapes — but at very different
   weights. Any claim of the form "class X is the model's characteristic error"
   must be checked against the tolerance profile, or it will be an artifact of
   which shapes happened to get a rule.

### 4.3 The severity assignment, tested — consistent, with one latent anomaly

HARD.md §4.2 fixed the taxonomy: **hard = exception-free format impossibility;
soft = divergence within a published tolerance**. Applied in the other
direction:

- The **divergence family** is soft on that criterion by construction: 88
  published tolerances, and the finding is a disagreement between two readings,
  not a statement the format cannot interpret. Correct.
- **`membership`** is soft and has four published tolerances (AF/AQ/DG/DS) plus
  the adverbial-oblique allowance. Correct, and HARD.md §4.2 already argued the
  contrast with the clausal check from the other side.
- **`dual_role`** is an artifact-internal contradiction, which sounds hard, but
  it has a published exception (fused clitics, rules AL/CM), so it is defeasible
  and soft is right.
- **`unknown_role`** is the anomaly. `validate.py` 125–126 emits `tag` for a role
  outside the frozen vocabulary — but the vocabulary is closed (`ROLES` plus
  `obl:<lemma>`, [`models.py`](../dante_corpus/skel/models.py) 39–44), the check
  is gated by **no** `rule_active` call, and the registry publishes **no**
  tolerance for it. By the contract's own taxonomy an unparseable role is a
  format impossibility and belongs with `word`/`position`. It occurs **0 times**
  in the recon corpus and 0 in gold, so this is a latent misclassification with
  no live consequence — recorded, not repaired.

### 4.4 The count is not a distance, in three separate ways

`check.py` prints one number, and it is tempting to read it as "how far the
artifact is from correct". It is not a metric, and the failures are measurable:

1. **One disagreement, two findings.** A relocated argument scores `extra_arg`
   at the old position and `missing_arg` at the new one. Counting per predicate,
   **631** `extra_arg`/`missing_arg` findings pair off this way. The dry-run in
   §6 makes it concrete: 349 mechanical subject rewrites cleared **694**
   findings — 1.99 per rewrite.
2. **Non-monotonic under partial completion.** A predicate the artifact never
   registers scores exactly **one** `missing_tuple`, and its arguments are never
   compared at all (the argument loop runs only over `given_preds & derived_preds`).
   Registering it — a strict improvement, and exactly what a clausal repair does —
   removes 1 finding and exposes the frame: by §3's distribution, **227 of the
   490** would then carry 2 or more `missing_arg`, so **the counter rises for
   the more complete artifact**. HARD.md §6's last bullet anticipated this; it is
   now quantified.
3. **Suppression cuts the other way too.** For those 490 predicates the corpus is
   scored on 490 findings where a fully registered artifact would be scored on
   ~866 argument-level ones. The headline 5,014 is not an upper bound on the
   underlying disagreements, and not a lower bound either.

### 4.5 Falsification attempts

- *Checker misfire — a finding where the artifact and the derivation actually
  agree*: none. The self-consistency probes hold at both ends — 0 `extra_arg`
  citing an L4 argument-child (§3), and `derive_unit`'s own output scores 0 soft
  (§4.1).
- *Class collapse — the five divergence classes being one phenomenon*: refuted
  by §3; the structural profiles are disjoint (`missing_arg` 96.7% L4-anchored,
  `extra_arg` 0% by construction, `role_mismatch` 99.5% label-only).
- *Dead machinery — tolerances that never fire, i.e. a registry describing a
  corpus it no longer matches*: 57 of the 88 fire on recon, 61 on gold, 27 fire
  on neither. The registry is largely live, and its silent quarter is a
  measurement of the recon corpus's narrower construction range, not of decay.
- *Derivation conflict on the hard side*: **not refuted** — one case found, §4.1.
- *Gold-independence of the soft bar*: **not refuted** — §4.2 is the finding.

## 5. What this means for the reduction work

The classification is sound as what it is, and it is not what the headline
number suggests. Stated precisely:

- **A soft finding is a well-formed, evidence-anchored report that the artifact
  and the derivation disagree in a way the registry does not name.** §3 shows
  the anchoring is real; §4.1 shows the diff is exact; §4.5 shows no misfires.
- **It is not, and cannot be, evidence that the artifact is wrong.** Phase 5
  established this from the inside: its own per-position audits found that "in
  the majority of cases, the LLM was linguistically correct and `derive_unit` was
  simply silent" ([`PHASE5.md`](../skel/PHASE5.md) §1.2), and every such finding
  was retired by writing a *tolerance*, not by correcting an artifact.
- **So the count selects work at a coarser grain than the hard count did**, and
  discipline 5 (read positions, not aggregates) is not optional here: for each
  candidate class the design pass must first decide which of the three outcomes
  applies — the artifact is wrong, the derivation is silent (a tolerance is
  missing), or the two notations are equivalent. Only the first licenses editing
  the corpus.
- **The classes are not equally eligible.** On §3's evidence: `role_mismatch`'s
  377 oblique-refinement findings and `missing_arg`'s 1,592 L4-anchored omissions
  are questions the derivation *determines* from the frozen layers, so they are
  decidable on the contract alone (discipline 3). `extra_arg`'s 568
  `advcl`-as-`obl` findings are a systematic reading disagreement about the
  argument/adjunct boundary, where rule T already tolerates a neighbouring shape
  — that is a candidate for a *tolerance*, not for a repair, and it is exactly
  the shape Phase 5 kept misdiagnosing. The 614 pro-drop `subj` findings sit
  under `_apply_subj_authority`, the contract's own declaration that the
  subject slot is LLM-authoritative rather than derive-authoritative, and should
  be read in that light before anything is rewritten.
- **Any reduction claim must report the mechanism, not just the delta**, given
  §4.4: how many findings fell per edit, and whether registrations were added
  (which inflate the count) or rows deleted (which deflate it, discipline 1).

## 6. Readout, taken afterwards: gold opened deliberately

Everything above was produced gold-closed. This section is the sanctioned
readout ([`recon/agree.py`](recon/agree.py)) run *after* the audit, on the
rewrite pass proposed in [`PLAN.md`](PLAN.md)'s Handoff — the two mechanical
rewrites `dante_corpus/skel/repairs.py` licenses (`role_label`: bare `obl` →
`obl:<lemma>` where a `case` child makes the preposition explicit; `null_subject`:
`subj (0,0)` → the derived position, gated on `dep.subject_agreement`), applied
in memory only, under the same acceptance gate the skel drivers use (0 hard
after, no new violation class). **Nothing was written.**

| | soft total | `role_mismatch` | `extra_arg` | `missing_arg` | gold P | gold R | gold F1 |
|---|---:|---:|---:|---:|---:|---:|---:|
| corpus today | 5,014 | 573 | 2,114 | 1,646 | 0.7079 | 0.7555 | 0.7309 |
| after 720 rewrites | **3,949** | 202 | 1,770 | 1,296 | 0.7239 | 0.7726 | **0.7475** |

Per rewrite, against gold: of the 349 `null_subject` rewrites, **0 matched gold
before and 348 after**; of the 371 `role_label` rewrites, **0 before, 339
after**. 687 of 720 rewrites (95.4%) land on a gold row.

Three things follow, and none of them may be used to choose a rule:

- For these two mechanically-decidable classes the soft findings were **real
  errors**, not conventional divergence. §4.2's caveat is about the counter's
  boundary in general; it does not apply uniformly to every class inside it.
- +0.0166 F1 is larger than everything the hard track produced (0.7307 → 0.7309
  across S5.3–S5.7, three flat readings), from deterministic work costing no
  model calls. The stage's finding that "hard-clean and gold-close are different
  targets" stands; this suggests soft-clean and gold-close are *not* as
  disjoint — for the decidable classes.
- It also refutes a worry worth recording, since it was raised before the
  measurement: gold fires rule `L` 341 times, i.e. gold *itself* writes bare
  `obl` at 341 positions where the derivation determines `obl:<prep>`, so the
  `role_label` rewrite could have moved the corpus away from gold. Net it does
  not (+339). The prediction was wrong and the readout says so.

## 7. Method notes

- Every §3–§4 figure comes from scratch scripts (run from the scratchpad, not
  committed) built on `recon.check`'s own helpers plus `morph.load_morph` /
  `dep.load_dep` joins, and is reproducible from them. The tolerance-disabled
  sweeps use the registry's own `RULES.disable()` / `hit_count()` API
  ([`registry.py`](../dante_corpus/skel/registry.py)); rule EG is excluded from
  every excusal count because its gate is queried once per unit (3,477 hits on
  every artifact) rather than once per finding.
- The audit read gold **through the checker** twice — `check --root skel`
  (0 hard / 0 soft, HARD.md §2's calibration) and the tolerance-disabled sweep
  (3,250) — and read gold **as rows** once, in §6, deliberately and after the
  fact. §6's numbers decided nothing here, and the next design pass should still
  open gold-closed; if §6's result is what makes a rule attractive, that rule
  needs an independent derivation from the contract before it ships, and the
  same S5.3-style transparency ([`stages/05.md`](stages/05.md) §5) applies to it.
- Two items are corrections to existing records rather than new findings, and
  both are recorded, not repaired: HARD.md §4.3's "impossible by construction"
  (§4.1, one counterexample at `paradiso 18:83`) and `unknown_role`'s severity
  (§4.3, latent, 0 occurrences).
