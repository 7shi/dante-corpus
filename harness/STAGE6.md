# Stage 6: Soft Divergence Reduction

Stage-6 home document: opening scope, design work as it happens, and the
stage's milestone ledger as records accrue. [`PLAN.md`](PLAN.md) keeps status
and the handoff; detail lives here, not there — the convention Stage 5
established and this stage continues.

**Status**: OPENED 2026-08-30 (operator decision, on Stage 5's close). Stage 5
took the recon corpus to **0 hard violations** and closed there
([`STAGE5.md`](STAGE5.md) S5.8); everything left is soft, and it is a large
enough body of work — and a different enough kind of work — to be its own
stage. Record S6.1 is the audit of the classification that would otherwise
drive it ([`SOFT.md`](SOFT.md)), filed before any rule was designed.

---

## 1. What this stage does

The corpus stands at **0 hard / 5,014 soft** and `make check` exits 0. Soft
findings are never reported into an agent session by design
([`STAGE5.md`](STAGE5.md) S5.5), so unlike the hard track this is entirely
deterministic work over the committed TSVs: no canto is re-run, no model is
called, and the 164 hours of live model time behind the corpus are not spent
again.

The nominal target is 0 soft — the bar gold meets. §2 is the reason that
target may not be pursued naively, and it is the first thing this stage
established rather than something discovered later.

## 2. What the soft counter is (record S6.1)

Stage 5 §5 asked two questions of the *hard* counter — is it calibrated, is it
gameable — and the answers set that stage's method. Record S6.1 asks the same
two of the soft counter, and the answers differ enough to change how this
stage works. Full evidence in [`SOFT.md`](SOFT.md); the load-bearing part:

**Is it calibrated?** Yes, but through a mechanism the hard side does not
have. Gold reaches 0 soft only because 88 of the 130 registry rules are
*tolerances* that excuse the **3,250** positions where gold itself diverges
from `derive_unit`, and those tolerances were written by measuring that very
diff (`skel/README.md`: the rules were "incrementally censused, measured by
violation diff"; [`../skel/PHASE5.md`](../skel/PHASE5.md) §2 prints the
descending ledger). Six of them fire exactly once on gold apiece. So
`soft == 0` means **"every disagreement with the derivation has a shape the
registry names"**, not "agrees with the derivation".

**Is it gameable?** Not by deletion the way hard was — deleting a row trades
`extra_arg` for `missing_arg` — but it is not a distance either. One relocated
argument scores twice (631 such pairs), and registering a `missing_tuple`
predicate — a strict improvement — *raises* the count at 227 of 490 positions.

**Consequence for method.** [`STAGE5.md`](STAGE5.md) §5's resolution still
holds and is still the only admissible source of authority: a rule derives
from `validate.py`'s schema invariants and `derive.py`'s derivation, with gold
unopened and `make agree` read only afterwards. But on this side the
derivation *is* the comparand and the tolerance boundary around it carries
gold's fingerprints, so the counter cannot be appealed to as a neutral
referee. Each candidate class has **three** possible outcomes, and the design
pass must decide which before writing anything:

1. **the artifact is wrong** — the only outcome that licenses editing a TSV;
2. **the derivation is silent** — the finding is the checker's, not the
   model's, and the right answer is a *tolerance*, not a repair (this is what
   Phase 5 repeatedly misdiagnosed as "LLM error",
   [`../skel/PHASE5.md`](../skel/PHASE5.md) §1.2);
3. **the two notations are equivalent** — nothing to do but say so.

Any reduction claim reports the mechanism, not just the delta: how many
findings fell per edit, and whether rows were rewritten, added or deleted.

## 3. The candidate classes, and what makes them eligible

From S6.1's position-by-position reading (frozen layers only, gold unopened):

| class | count | structural reading |
|---|---:|---|
| `extra_arg` | 2,114 | 614 pro-drop `subj (0,0)`; 889 L4 children of the predicate under a non-argument deprel (**568** of them `advcl` read as `obl`); 600 elsewhere; 11 via the aux/conj head |
| `missing_arg` | 1,646 | **1,592 (96.7%)** are arguments L4 itself attaches to the predicate (or its aux/conj head) and the artifact omits |
| `role_mismatch` | 573 | 570 are label-only disagreements at an L4 argument-child; **377** are bare `obl` vs `obl:<prep>` |
| `missing_tuple` | 490 | predicates the artifact never registers; derived frame size 1 (263), 2 (147), 3 (76), ≥4 (4) |
| `membership` | 146 | all oblique roles citing adverbs (111) or markers — one construction family |
| `extra_tuple` | 43 | |
| `dual_role` | 2 | `paradiso 1:125`, `paradiso 9:110` |

Eligibility, in the order the evidence supports:

1. **Determined by the contract** — `role_mismatch`'s 377 oblique refinements
   (`derive.py`'s `_oblique_role_of` fixes `obl:<prep>` from the `case` child)
   and `missing_arg`'s 1,592 L4-anchored omissions. Outcome 1 applies:
   discipline 3 decides them without reading gold.
2. **Likely a missing tolerance** — `extra_arg`'s 568 `advcl`-as-`obl`, next
   to rule T which already tolerates a neighbouring shape. Outcome 2.
3. **Reserved to the model by the contract itself** — the 614 pro-drop `subj`
   findings sit under `_apply_subj_authority`, which declares the subject slot
   LLM-authoritative rather than derive-authoritative. Read that before
   rewriting anything there.

**Levels (record S6.2).** The operator's frame for the reduction: soft classes
are graded, and `reconstruct --fix <level>` repairs everything at that level and
below. A class joins a level only once its outcome has been argued from the
contract — the level table is where §2's three-outcome question is answered, once,
in code (`harness/extractor/fixlevel.py`). Level 1 is
`oblique_qualification`; nothing above it is defined yet.

**One decision is open and is the operator's.** Is
`dante_corpus/skel/repairs.py` an admissible authority under discipline 3? It
opens no gold file and its two rewrites are re-derivable from `derive.py`
alone (`role_label` from `_oblique_role_of`; `null_subject` gated on
`dep.subject_agreement`), but it is the same `skel/` toolchain that built
gold. Either it is used directly, or the rules are re-derived independently in
`harness/recon/repair.py`.

---

## Milestone Ledger (Stage 6)

### S6.1 — The soft classification audited; its zero point is tolerance-mediated (2026-08-30)

The counterpart to [`STAGE5.md`](STAGE5.md) S5.4, and the same reason for
existing: 5,014 soft findings now select every remaining design pass, and
discipline 1 says the counter that selects work must itself be audited before
it drives anything. No code and no artifact change — an evidence record,
[`SOFT.md`](SOFT.md), on the S5.8 tree (`ef0bf47`, clean; `make check` 0 hard /
5,014 soft). §§2–5 there are gold-closed apart from the sanctioned calibration
sweeps; §6 opens gold deliberately afterwards as a readout and decides nothing.

- **What the 5,014 are.** 97.0% (4,866) is a diff against `derive_unit`
  (`extra_arg` 2,114, `missing_arg` 1,646, `role_mismatch` 573,
  `missing_tuple` 490, `extra_tuple` 43); 146 are the nominal membership
  check against L2/L3/L4; 2 are artifact-internal (`dual_role`), and
  `unknown_role` is 0. They touch **2,126 of 3,477 units (61%)** across 3,707
  predicate positions — not a residue at the edges.
- **The findings are evidence-anchored.** Read position by position against
  the frozen layers, gold unopened: 1,592 of 1,646 `missing_arg` (96.7%) are
  arguments L4 itself attaches to the predicate and the artifact omits; 570 of
  573 `role_mismatch` cite an L4 argument-child, so both readings agree an
  argument is there and disagree only about its name; `extra_arg` splits into
  three unrelated sub-populations (614 pro-drop `subj (0,0)`, 889 L4 children
  under a non-argument deprel — 568 of them `advcl` read as `obl` — and 600
  elsewhere in the tree). Zero checker misfires: no `extra_arg` cites an L4
  argument-child, and `derive_unit`'s own output scores 0 soft.
- **The central finding: the zero point is tolerance-mediated, and the
  tolerances were fitted on gold.** 88 of the 130 registry rules are
  tolerances for these classes. Disabling exactly those and re-running gives
  recon **11,998** and **gold 3,250** — gold disagrees with the derivation at
  3,250 positions and reaches 0 solely because every disagreement has a shape
  the registry names, six of those rules firing exactly once on gold apiece.
  §2 above carries the consequence.
- **The count is not a distance.** One relocated argument scores twice (631
  `extra_arg`/`missing_arg` pairs; the §6 dry-run cleared 694 findings with
  349 rewrites, 1.99 each), and it is non-monotonic: registering a
  `missing_tuple` predicate — a strict improvement — removes one finding and
  exposes its frame, which for **227 of the 490** is 2 or more `missing_arg`.
- **Two corrections to Stage-5 records, both recorded rather than repaired.**
  `derive_unit`'s own output carries **1 hard violation** —
  `paradiso 18:83 [clausal] xcomp argument (84,3) is not a predicate`, a
  gapped-coordination `orphan` remnant cited but never promoted — so
  [`HARD.md`](HARD.md) §4.3's "impossible by construction" is falsified,
  though the closure property holds for the deprel-driven path at 3,476 of
  3,477 units. And `unknown_role` is emitted as `tag` while being an
  exception-free format impossibility with no tolerance behind it: latent
  misclassification, 0 occurrences in both artifacts.
- **Readout, gold opened afterwards (SOFT.md §6).** The rewrite pass the
  Stage-5 handoff had proposed — `repairs.py`'s `role_label` and
  `null_subject`, applied in memory under the skel drivers' own acceptance
  gate, nothing written — takes 5,014 → **3,949** soft and gold agreement
  0.7309 → **0.7475** (+0.0166, +687 exact rows), against 0.7307 → 0.7309 for
  the whole hard track. Of 720 rewrites, **0 matched a gold row before and 687
  (95.4%) after**. For these two mechanically-decidable classes the soft
  findings were real errors, so §2's caveat is about the counter's boundary in
  general and does not transfer uniformly to every class inside it. The
  numbers decided nothing: a rule still needs its own contract-derived design,
  opened gold-closed.

### S6.2 — Fix levels; `--fix 1` repairs the unqualified oblique in-session (2026-08-30)

The stage's first reduction pass, and the mechanism the rest of it will reuse.
Soft classes are **graded**: `reconstruct --fix <level>` reopens the units of a
committed TSV that carry a finding at that level or below, shows the session its
own recorded rows plus the invariants they break, and **replaces** those rows
with what it re-solves. Nothing is deleted, no canto is regenerated wholesale,
and a unit whose answer does not survive the acceptance test keeps the rows it
had. Ships the machinery plus level 1; no committed artifact was touched.

**Level 1 — `oblique_qualification`, 377 findings.** `role_mismatch` where the
artifact wrote bare `obl` and the derivation determines `obl:<prep>`. Its
authority is the contract's, read gold-closed: `derive.py`'s `_oblique_role_of`
qualifies an oblique from its Layer-4 `case` child and leaves it bare only when
there is none, and registry rule **L** (`rules.py` `_oblique_lemma_refinement`)
tolerates strictly the *opposite* direction. The direction repaired here is one
the registry deliberately does not excuse, the evidence is in the frozen layers,
and the under-specified side is the artifact — §2's outcome 1. The selection
readout (`make fix-level FIX=1`) reproduces the count exactly: **377**.

**What crosses into the session, and what does not.** S5.5 kept soft findings out
of the session because they are `derive_unit`'s own answer. This pass crosses
that line **narrowly and deliberately**, and the record should say so plainly: the
session is shown the unit's recorded rows, and per position the *invariant and
the frozen-layer evidence* — "this oblique argument carries a Layer-4 `case`
child (3.1 'come'); a bare 'obl' is reserved for an oblique with no case marker".
The derived label is never rendered, in the notice or in the gate, and a test
asserts its absence. The model re-derives the qualification itself; that is the
measurement the autonomy premise asks for, and a transcription of `derive_unit`
would not be.

- **Selection** (`fixlevel.select` + `reconstruct.plan_fix`): settled units
  carrying a level-1 finding are unsettled again, so the ordinary unit loop
  re-runs them. `TsvArtifact.reopen()` leaves the append path — an overwrite in
  the middle of the file cannot be appended, it would duplicate the lines.
- **Routing** (`RoutePolicy.force_fallback`): a reopened unit must reach the
  model. The fast path would answer it with `derive_unit`'s own rows, which
  clears the class by definition and measures nothing.
- **The gate** (`GrammarToolkit(oblique_case_qualification=True)`): the level's
  own bar added to `validate_candidate` on top of S5.5's three schema checks —
  the generation-time check *plus* the level, exactly as the hard track moved its
  checks into the session. It reports the invariant and the case child's
  position, never the qualified label, and stays silent when the case child
  carries no Layer-2 lemma (the derivation leaves that oblique bare too, so
  demanding a label there would be unsatisfiable).
- **Acceptance** (`reconstruct.fix_verdict`): three refusals — the answer is not
  hard-clean, the level's findings did not fall, or a violation class the unit
  did not carry is now present. A refused unit is reverted to its recorded rows,
  gate verdicts included, and reported as `verdict: no_improvement` /
  `hard` / `new_class:<name>`. A fix run cannot leave the artifact worse than it
  found it.
- **Reporting** (discipline 6): every canto record carries units reopened,
  accepted vs reverted, level findings and total soft before → after, and the
  row-level mechanism — `rows_relabelled`, `rows_added`, `rows_removed`. A delta
  alone is not a reportable result.

**Measured before launch, over the committed corpus.** The notice and the gate
answer to different masters and neither subsumes the other, which is worth having
on record: the notice follows the **checker's selection** (377 positions), the
gate states the **invariant** uniformly over whatever the session submits (504
positions on today's rows, 369 of them shared). The 135 gate-only positions are
bare obliques with a lemma-bearing case child that the checker scores under
another class or excuses; the 4 selection-only ones are oblique clitics
(`ci`/`ne`/`men` read as `obl:a`) with no `case` edge at all, which get a notice
worded for that evidence instead. No unit is selected by the gate — selection is
the checker's alone.

Suite **938 → 955**. `make check` unchanged at **0 hard / 5,014 soft**: this
record ships the mechanism, and applying it to the committed corpus is a separate
act needing its own go-ahead. The pilot is one canto under `make fix-canto
CANTICLE=<canticle> CANTO=<n> FIX=1`, with `make check` after it and `make agree`
read afterwards only, never as the criterion.

**The targets** (`recon/Makefile`): `fix-level` is the free readout; `fix-canto`
takes the canto in variables the way the CLI does; `fix-inferno` /
`fix-purgatorio` / `fix-paradiso` walk one canticle in order, and `fix` walks all
100 — the three canticles are the parallel streams (`make -j3`), as in Stage 4. A
canto with no findings at the level costs no model call, so the aggregates may be
pointed at everything and the level decides what is touched. There is deliberately
no pattern rule over file names: a fix target produces no file, and
`fix/inferno/12` would read as a path that never exists on disk.

**`FIX` defaults to `max`**, resolved by the level table itself
(`fixlevel.resolve_level`; `--fix max` / `--fix-level max` on either CLI) rather
than restated in the Makefile, which would drift the moment a level is added.
Since levels are cumulative and a class joins one only after its outcome has been
argued from the contract, `max` means "every repair this project can currently
justify" — and it widens by itself as levels land, which is the intent. The cost
is that `make fix` does not name a fixed scope, so every run announces the level
it resolved and each canto record stores `fix.level`; pin `FIX=<n>` to hold a run
to one level.
