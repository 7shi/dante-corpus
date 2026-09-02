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

The corpus opened this stage at **0 hard / 5,014 soft** and stands at **0 hard /
4,660 soft** (S6.5); `make check` exits 0 throughout. Soft
findings are never reported into an agent session by design
([`STAGE5.md`](STAGE5.md) S5.5), so unlike the hard track the stage's **default
mode** is deterministic work over the committed TSVs: no canto is re-run, no
model is called, and the 164 hours of live model time behind the corpus are not
spent again. Record S6.2 added the one sanctioned exception — `--fix <level>`
reopens just the units carrying a level's findings, showing the invariant and
the frozen-layer evidence but never the derivation's answer — and S6.3/S6.5 are
the two runs of it.

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

**Two scopes of replacement (record S6.4).** A level names a *row* and a session
answers a *unit*, so acceptance runs twice: the whole answer first, and on
refusal a splice that takes it only at the rows the findings themselves name
(`FixClass.keys` → `salvage_rows`), re-measured by the same `fix_verdict` and
reported as `verdict: salvaged`. A class joining the table therefore declares
which rows its findings govern, alongside its matcher and its notice.

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
  `missing_tuple` 490, `extra_tuple` 43); 146 nominal membership (L2/L3/L4);
  2 artifact-internal (`dual_role`); `unknown_role` 0. **2,126 of 3,477 units
  (61%)**, 3,707 predicate positions — not an edge residue.
- **Evidence-anchored.** 1,592 of 1,646 `missing_arg` (96.7%) are arguments L4
  attaches to the predicate and the artifact omits; 570 of 573 `role_mismatch`
  cite an L4 argument-child (an argument is there, only its name disagrees);
  `extra_arg` splits into three sub-populations (614 pro-drop `subj (0,0)`,
  889 non-argument-deprel L4 children — 568 `advcl` read as `obl` — 600
  elsewhere). Zero checker misfires: no `extra_arg` cites an L4
  argument-child, and `derive_unit`'s own output scores 0 soft.
- **The zero point is tolerance-mediated, fitted on gold.** 88 of the 130
  registry rules are tolerances for these classes; disabling them gives recon
  **11,998**, gold **3,250** — gold disagrees with the derivation at 3,250
  positions and reaches 0 only because every disagreement has a registry
  shape, six rules firing exactly once on gold apiece. §2 carries the
  consequence.
- **Not a distance.** One relocated argument scores twice (631
  `extra_arg`/`missing_arg` pairs), and it's non-monotonic: registering a
  `missing_tuple` predicate (a strict improvement) exposes its frame, 2+
  `missing_arg` at **227 of the 490**.
- **Two Stage-5 corrections, recorded not repaired.** `derive_unit` itself
  carries **1 hard violation** (`paradiso 18:83 [clausal] xcomp argument
  (84,3) is not a predicate`, a gapped-coordination remnant), falsifying
  [`HARD.md`](HARD.md) §4.3's "impossible by construction" (closure still
  holds at 3,476/3,477 units); `unknown_role` is emitted as `tag` despite
  being an exception-free impossibility with no tolerance — latent, 0
  occurrences today.
- **Readout, gold opened afterwards (SOFT.md §6), decides nothing.**
  `repairs.py`'s `role_label` + `null_subject`, applied in memory: 5,014 →
  **3,949** soft, agreement 0.7309 → **0.7475** (+0.0166, +687 rows) against
  0.7307 → 0.7309 for the whole hard track; of 720 rewrites, 0 matched gold
  before, 687 (95.4%) after. For these two classes the findings were real
  errors — §2's caveat is about the boundary in general, not every class in
  it — but a rule still needs its own contract-derived design, opened
  gold-closed.

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

- **Selection** (`fixlevel.select` + `reconstruct.plan_fix`) unsettles a
  carrying unit so the ordinary loop re-runs it (`TsvArtifact.reopen()`).
- **Routing** (`RoutePolicy.force_fallback`) forces a reopened unit to the
  model — the fast path would just answer with `derive_unit`'s own rows.
- **The gate** (`GrammarToolkit(oblique_case_qualification=True)`) adds the
  level's own bar to `validate_candidate`, reporting the invariant and the
  case child's position (never the qualified label), silent when the case
  child carries no lemma (the derivation leaves that oblique bare too).
- **Acceptance** (`reconstruct.fix_verdict`) has three refusals — not
  hard-clean, the level's findings didn't fall, or a class the unit didn't
  carry is now present — reverting to the recorded rows on any of them
  (`verdict: no_improvement` / `hard` / `new_class:<name>`); **a fix run
  cannot leave the artifact worse than it found it.**
- **Reporting** (discipline 6): every canto record carries units reopened,
  accepted vs reverted, findings and soft before/after, and the row mechanism.

**Measured before launch.** The notice (checker's selection, 377 positions)
and the gate (the invariant, uniformly, 504 positions on today's rows, 369
shared) answer to different masters and neither subsumes the other: the 135
gate-only positions are bare obliques the checker scores under another class
or excuses, the 4 selection-only ones are oblique clitics with no `case` edge
at all. No unit is selected by the gate — selection is the checker's alone.

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

### Infrastructure note — llm7shi 0.15.0 lands the status-bar hooks (2026-08-31)

Not a milestone record and not stage work — filed only so the next session
isn't surprised that `runner/statusline.py` moved while the `make fix` run was
in flight. **S6.3 stays reserved for that run's readout.** llm7shi **0.15.0**
absorbed the status-bar change [`../ARCHITECTURE.md`](../ARCHITECTURE.md) §4
had flagged as pending: the run clock now comes from upstream's own
`progress(started_at=...)`, so the local subclass and its private-API imports
are gone (`runner/statusline.py` 102 → 61 lines); markup-off is upstream's
default, so the print/error overrides for it are deleted (guarantee unchanged,
still tested); and the console is no longer pinned to stderr, which is safe
since durability is about `--log` files, not the console. Only the
`wait_retry` accounting stays local — genuine application measurement, not a
workaround. Docs updated to match (ARCHITECTURE.md §0/§4). Suite **957**
(unchanged in count, one stderr expectation updated); `harness/recon/`
untouched.

### S6.3 — `make fix` level 1 over the whole corpus: 294 of 377 cleared (2026-09-01)

The operator's run of S6.2's mechanism over all 100 cantos — the first time a
soft finding reached a live session, and the first corpus-wide edit since
S5.7. **The corpus moved; no code did.**

**The numbers** (against the S6.2 baseline `007d973`, re-verified from that
commit's TSVs):

| | before | after |
|---|---:|---:|
| hard violations | 0 | **0** |
| soft violations | 5,014 | **4,706** (−308) |
| level-1 findings (`make fix-level`) | 377 | **83** (−294, 78.0%) |
| cantos carrying a level-1 finding | 95 | 50 (45 cleared outright, none worse) |
| gold agreement (readout, §5 discipline 4) | 0.7309 | 0.7372 |

`make check` exits 0.

**Per soft class** (nothing rose): `role_mismatch` 573 → **287** (−286);
`missing_arg` 1,646 → 1,636; `extra_arg` 2,114 → 2,107; `membership` 146 → 143;
`missing_tuple` 490 → 488; `extra_tuple` 43 and `dual_role` 2 unchanged. The
level's class carries −286 of −308; the other −22 are collateral, outside the
class the run aimed at. Soft is not a distance (§2) — the near-agreement
between −294 findings and −308 soft is arithmetic, not corroboration.

**The mechanism**, from the 100 per-canto logs (13 cantos re-invoked after an
interruption; unit records deduplicated by span). **337 unique units reopened
across 95 cantos**, 360 unit records. Final verdict per unique unit: **265
accepted (78.6%), 46 `new_class`, 26 `no_improvement`, 0 `hard`**.

Zero `hard` refusals: S5.5/S5.7's schema checks make a fix session's answer
hard-clean by construction, so this refusal never fired in 360 attempts — a
settled gate that costs nothing and guards a real invariant.

`new_class` (46) outnumbers `no_improvement` (26): `missing_arg` 27,
`extra_arg` 21, `membership` 7, `missing_tuple` 1 (a unit may bring more than
one). The model derives the qualification correctly; the limiting factor is
that the level names a single row while the session re-answers the **whole
unit**, trading the cleared class for an argument-level one elsewhere — a
design property (S6.2's "replaces those rows" is whole-unit), not a model
failure.

**Row-level** (diff against `007d973`, 93 files, +484/−455 lines): **322
relabels, 188 rows added, 151 removed, net +37**. Only **235** of the relabels
are the level's own `obl` → `obl:<prep>` (`obl:come` 68, `obl:di` 56,
`obl:in` 49, `obl:a` 10, `obl:che` 9, `obl:per`/`obl:da` 7 each, …); the other
87 reach past the brief: `obl` → `attr` 12, `obl` → `xcomp` 12, `obl` →
`ccomp` 7, `obl:ne` → `obl:in` 5, `subj` ↔ `obj` 8, plus preposition
normalisations (`obl:col` → `obl:con` 3, `obl:sovra` → `obl:sopra` 2,
`obl:ad` → `obl:a` 2, `obl:de` → `obl:di` 2).

**Falsifies, benignly, PLAN.md's readout expectation** ("expect only role
relabels; an added/deleted row is worth explaining") — same whole-unit cause.
Worth naming: `purgatorio 21:87` replaced an empty placeholder with two rows
for `famoso` — a predicate *registered*, the move §2 says **raises** the soft
count while being a strict improvement.

**`adopted_invalid` means something different under `--fix` from here on** —
the level-1 bar is added to `validate_candidate` as an error, so it usually
means "a bare `obl` with a lemma-bearing case child is still on the sheet."
99 of 360 attempts (27.5%) ended `adopted_invalid`, 66 accepted anyway; it
correlates with refusal as expected — 25 of 30 `no_improvement` are
`adopted_invalid`.

**Cost.** 2,287 LLM calls, **23.87 M tokens** (16.24 M input / 1.55 M output /
6.08 M thought), **61.5 h** summed per-canto elapsed (inferno 22.0 /
purgatorio 28.5 / paradiso 10.9), ≈28.5 h wall clock on three `-j3` streams.
170 `api_retries` absorbing 6,469 s of 429 backoff, 21 max-length retries, 0
paced. The ~3,140 units with no level-1 finding cost no model call.

**Gold agreement** (§5 discipline 4, opened afterwards, cited as nothing
else): corpus-wide **0.7309 → 0.7372** (P 0.7079 → 0.7136, R 0.7555 → 0.7624;
+275 TPs on +38 rows); inferno 0.7357 → 0.7437, purgatorio 0.7282 → 0.7343,
paradiso 0.7287 → 0.7334 — the largest agreement move the project has
recorded (the whole hard track was 0.7307 → 0.7309), confirming the soft
residue is where the remaining distance to gold lives, as S5.7 predicted. Not
the reason the level shipped — that was argued from `derive.py`'s contract in
S6.2, gold-closed.

**Prices the open authority question** (§3), decides nothing: the
`skel/repairs.py` dry run projected 5,014 → 3,949 with 720 rewrites and
+0.0166 agreement, deterministically, in seconds; this live run cleared 294
findings of one class for ~28 h and +0.0063 — different scope, but the
deterministic rewrite transcribes `derive_unit` while this run measures a
model re-deriving the qualification from the frozen layers, which is what §1
says the project exists to obtain.

**State at close.** Corpus **0 hard / 4,706 soft**, 93 TSVs modified in the
working tree and uncommitted; suite **957** (unchanged). Level 2 is not
opened: its class must be argued from the contract first, and the `new_class`
refusal rate says the *unit* granularity of replacement — not the level table
— is the next thing worth designing.

### S6.4 — Replacement granularity: a refused answer is salvaged at the rows its findings name (2026-09-01)

S6.3 closed by naming the seam rather than a next level: **a level names a row,
a session answers a unit**, and `--fix` could only take or leave the whole unit.
This record narrows that, gold-closed, with no corpus edit — the mechanism
changes what a *future* fix run does, and running it stays the operator's act.

**What the seam costs, measured from the run's own logs** (100 per-canto logs,
unit records deduplicated by span, last verdict wins — reproducing S6.3's
337 reopened / 265 accepted / 26 `no_improvement` / 46 `new_class` exactly):

| where the 83 remaining level-1 findings sit | findings |
|---|---:|
| in a unit reverted `new_class` | **52** |
| in a unit reverted `no_improvement` | 28 |
| in a unit whose repair was accepted | 3 |

The classes those 46 answers brought with them: `missing_arg` 27, `extra_arg`
21, `membership` 7, `missing_tuple` 1. `fix_verdict` checks in order — hard,
then `no_improvement`, then `new_class` — so every one of those 46 submissions
was **hard-clean and did reduce the level's own findings**. At least 46 of the
52 were therefore repairs the level itself calls correct, discarded with the
unit that carried them.

**The mechanism.** A `FixClass` now also declares the rows one of its findings
governs (`fixlevel.FixClass.keys`; level 1 returns the single
`(predicate, argument)` key it relabels). Acceptance runs in two scopes:
(1) **the whole unit**, as before, taken entire when it passes; (2) on
refusal, **a position-scoped splice** (`salvage_rows`) — recorded rows stand
everywhere except the governed keys, where the answer's rows replace them, so
a salvage cannot import a class the unit never carried; the spliced rows go
back through `_validate_rows` and the same `fix_verdict`, reverted like any
other refusal if they fail it. Verdicts gain `salvaged`, with the whole-unit
refusal kept beside it as `fix.unit_verdict`. Salvage is refused outright when
the submission's own token assertions fail.

**What this does not claim.** The 46 units' submissions are not in the logs
(a refusal is logged only as the reverted rows kept), so how many of the 52 a
salvage would actually take is **not measurable without a re-run** — 46 is the
floor the verdict order guarantees, 52 the ceiling; the 26 `no_improvement`
units are equally unmeasurable here. Nothing about the level table changed, no
gold opened, no derived label crosses into a session.

Suite **957 → 960** (the governed-key mapping, the splice, and one end-to-end
`--fix` run whose stub answer repairs the oblique and brings an extra row).
`harness/recon/` untouched: corpus still **0 hard / 4,706 soft**.

### S6.5 — The `--fix 1` re-run on S6.4's mechanism: 46 of 83 cleared, 12 of them by salvage (2026-09-01)

The operator's re-run of level 1 over all 100 cantos on the S6.4 splice.
**The corpus moved; no code did.** The salvage yield is much smaller than the
delta: most of what moved this run moved because a *fresh* set of live
sessions re-rolled, not because of the new mechanism.

**The numbers** (against S6.3's close `b1ef280`, re-checked from TSVs):

| | before | after |
|---|---:|---:|
| hard violations | 0 | **0** |
| soft violations | 4,706 | **4,660** (−46) |
| level-1 findings (`make fix-level`) | 83 | **37** (−46, 55.4%) |
| cantos carrying a level-1 finding | 50 | 28 (22 cleared outright, none worse) |
| TSVs modified | — | 32 |
| gold agreement (readout, §5 discipline 4) | 0.7372 | 0.7382 |

`make check` exits 0. Per soft class: `role_mismatch` 287 → **242** (−45),
`extra_arg` 2,107 → 2,106 (−1), everything else unchanged (`missing_arg`
1,636, `missing_tuple` 488, `membership` 143, `extra_tuple` 43, `dual_role`
2) — one non-level-1 `role_mismatch` appeared, so the level's own −46 and the
class's −45 are arithmetic (§2), not corroboration.

**The mechanism** — exactly one segment per canto, 74 distinct `unit` records
across the 50 cantos with a finding:

| verdict | units | findings before | after |
|---|---:|---:|---:|
| `accepted` (whole unit) | 33 | 34 | **0** |
| `salvaged` (S6.4's splice) | 9 | 13 | **1** |
| `no_improvement` (reverted) | 17 | 20 | 20 |
| `new_class` (reverted) | 15 | 16 | 16 |
| `hard` | 0 | — | — |

**Salvage collected 12 of the 46; the other 34 came from the whole-unit
answer simply passing this time** on units S6.3's answer had failed —
live-session variance, not the new mechanism. Zero `hard` again.

**What happened to the 83, by their S6.3 verdict** (the question S6.4 could
not answer without a re-run):

| S6.3 verdict | → `accepted` | → `salvaged` | → `no_improvement` | → `new_class` |
|---|---:|---:|---:|---:|
| `new_class` (52) | 20 | 13 | 8 | 11 |
| `no_improvement` (28) | 14 | — | 9 | 5 |
| `accepted` (3) | — | — | 3 | — |

Only 13 findings' worth went through salvage (one survived it), not S6.4's
46-of-52 floor — that floor bounded *S6.3's* discarded, unlogged, never
re-offered answers; the re-run could only collect what its own fresh sessions
produced. The limit of what a refused-and-unlogged answer can be reasoned
about at all.

**Salvage's own rate: 9 of 41 whole-unit refusals (22%), every one rescuing a
`new_class:extra_arg`** — dropping the extra argument the re-answer brought
while keeping the relabel, exactly the designed job. No other refusal class
was salvageable this run.

**Row-level** (diff against `b1ef280`, 32 files): **44 relabels, 19 added, 21
removed, net −2**. **39 of 44 relabels are the level's own** `obl` →
`obl:<prep>` (`obl:di` 12, `obl:in` 8, `obl:a` 5, `obl:per` 4, `obl:come` 3,
`obl:da`/`obl:con` 2 each, `obl:senza`/`obl:verso`/`obl:quale` 1 each); 5
others are `obl:de` → `obl:di` 2, `obl:sanza` → `obl:senza`, `subj` →
`ccomp`, `attr` → `xcomp`. `accepted` units: 34 relabels, 19 added, 19
removed — the whole-unit reach past its brief again. `salvaged` units: **10
relabels, 0 added, 2 removed, nothing outside the governed keys** — the S6.4
invariant holding in the field, not just in tests.

**`adopted_invalid`** (S6.3's `--fix` meaning): 36 of 74, still tracking
refusal — 14 of 17 `no_improvement` sessions ended on rows their own gate
rejected, against 1 of 15 `new_class`.

**Cost.** 584 LLM calls, **6.94 M tokens** (4.75 M input / 0.47 M output /
1.72 M thought), **18.3 h** summed per-canto elapsed (inferno 6.0 /
purgatorio 9.7 / paradiso 2.6). 75 `api_retries` absorbing 2,799 s of 429
backoff, 4 max-length retries, 0 paced. 50 cantos with no finding cost no
model call.

**Gold agreement** (§5 discipline 4): corpus-wide **0.7372 → 0.7382** (P
0.7136 → 0.7146, R 0.7624 → 0.7633; +39 TPs on −2 rows); inferno 0.7437 →
0.7444, purgatorio 0.7343 → 0.7356, paradiso 0.7334 → 0.7343 — a tenth of
S6.3's move, on a tenth of the findings.

**State at close.** Corpus **0 hard / 4,660 soft**, 32 TSVs modified; suite
**960**, unchanged. 32 units and 36 findings are now refused twice over by two
independent sets of sessions, and the second pass gained 46 mostly by
re-rolling the first pass's dice — a convergence curve, not progress.

**The residue is a fact about the mechanism, not a worklist**: settling it by
hand, even deterministically and contract-derived, is the frontier-LLM/human
triage loop §1 says this harness exists to replace — the autonomy premise
needs the *model* to reach the position, so a repair applied on its behalf
measures nothing. **But "the agent cannot reach it" would be the wrong
conclusion** (operator's correction: *if an assistant session can settle
these, the agent can in principle be made to*) — which makes what an
assistant could do here a **specification for the mechanism**, decomposed
against this run's own logs:

| what a frontier session has here | transferable? | evidence in S6.5 |
|---|---|---|
| **the derived answer** (`check.py` prints `'obl' vs 'obl:di'`) | **no** — S6.2 keeps it out of the session by design, a test asserts its absence; crossing it makes the run a transcription of `derive_unit` | — |
| **a one-row question** instead of a whole-unit re-answer | yes | 15 `new_class` refusals, only **1** `adopted_invalid`: the level's job was done and something else broke. S6.4 rescues 9 of 41 after the fact |
| **not stopping while its own gate says invalid** | yes | 17 `no_improvement`, **14** `adopted_invalid` but only **5** at the 12-turn ceiling — sessions stop early, so the lever is the stopping rule, not the budget |
| **the corpus-wide view of all 37 at once** | yes | a session sees one unit; feeding the level's own settled cases into the notice opens no gold and shows no derived label |

So the untried change is to make the **ask** row-scoped (S6.4 narrowed only
the acceptance), and to revisit why a session ends on rows it has itself
judged invalid. Reading the 37 is admissible as design input under §5
discipline 5 on that footing only — never as a worklist. *(Correction to this
record's first draft: it called `no_improvement` "running out of room" — the
turn counts don't support that for 12 of the 17.)*

### S6.6 — Two levers from S6.5's table: the invalid-final resume, and the acceptance rule told to the session (2026-09-01)

S6.5 ended by decomposing what an assistant session has at these positions into
one thing that may not cross and three that may. This record ships the two that
are cheapest and least speculative. **Code only; the corpus is untouched and
running anything over it stays the operator's act.**

**Why the session stops early.** `run_unit`'s loop ends as soon as the model
gives a prose answer after *any* successful `validate_candidate` dispatch;
nothing checks that last submission's verdict, and `candidate_rows` takes it
regardless. So a session can end on rows its own gate called invalid, with
turns unspent. Measured across both fix runs: **77 units ended
`adopted_invalid` with budget left** (S6.5: 20 of 74; S6.3: 57 of 337).

**Deliberate, and stays the default** — the module docstring: "giving up
after failed validations is a capability failure the benchmark must measure,
so it is never nudged" (`test_giving_up_after_failed_validation_is_never_nudged`
guards it). The resolution separates the two jobs instead of overruling it:

| | measuring a session | producing corpus |
|---|---|---|
| caller | `benchmark.py`, `agent.py --…` | `reconstruct.py` |
| `max_invalid_nudges` | **0** (`MAX_INVALID_NUDGES`) | **1** (CLI default) |
| rationale | the give-up *is* the measurement | the give-up ships to the artifact |

**Lever 1 — the invalid-final resume.** A session that ends with turns
remaining on a rejected submission is resumed once with `INVALID_NUDGE_MESSAGE`
(your last validation reported invalid, re-read *the errors that call
returned* and resubmit — or say the errors are wrong and stand behind the
rows). No derived label, no invariant the model's own tool hasn't already
told it. Counted separately as `result.invalid_nudges` so it's never confused
with the no-call nudge.

**Lever 2 — the session is told how its answer will be judged.** S6.5's
sharpest number: of the 15 `new_class` refusals only **1** was
`adopted_invalid` — those sessions satisfied their own gate and were refused
for a class introduced elsewhere, a rule they were never told. `revision_block`
now states `fix_verdict` in the session's own words (replaces only if no
schema break, the named points settle, and no new *kind* of problem — else
only the named rows are taken, S6.4's splice). This is the acceptance
contract, not the answer — the test asserting `derive_unit`'s label never
appears still passes.

**Why not the row-scoped ask** (S6.5's own suggestion): it would also
suppress the off-brief gains S6.3 measured on accepted units — 87 relabels
beyond the level, including the `purgatorio 21:87` registration §2 calls a
strict improvement. Telling the session the rule is strictly more information
and narrows nothing, so it ships instead; the row-scoped ask stays open as an
experiment with a control now, not a guess.

**Unmeasured** — both levers are prompt/loop-side, gold-closed, no run made
yet; a `--fix 1` re-run under them is the experiment, and per S6.5's caution
the comparison worth making is the *refusal mix*, not the finding count.

Suite **960 → 969**. `harness/recon/` untouched: corpus still **0 hard / 4,660
soft**.

### S6.7 — The `--fix 1` run under S6.6's two levers: 12 of 37 cleared, and the refusal mix moved the wrong way (2026-09-02)

The operator's run of level 1 over all 100 cantos on the S6.6 loop and
prompt. **The corpus moved; no code did.** S6.6 said the finding count could
not judge these levers — a fresh pass gains by re-rolling alone — so this
record leads with the refusal mix.

**The numbers** (against S6.5's close `2fd689f`):

| | before | after |
|---|---:|---:|
| hard violations | 0 | **0** |
| soft violations | 4,706 → 4,660 | **4,649** (−11) |
| level-1 findings (`make fix-level`) | 37 | **25** (−12, 32.4%) |
| cantos carrying a level-1 finding | 28 | 20 |
| TSVs modified | — | 9 |
| gold agreement (readout, §5 discipline 4) | 0.7382 | 0.7384 |

`make check` exits 0. Per soft class, the entire −11 is `role_mismatch`
(242 → **231**); everything else unchanged to the unit. As in S6.5 the
level's own subset fell by one more than the class did (soft is not a
distance, §2).

**Housekeeping**: logs swept before this run (all 100 carry only 2026-09-01
06:36–15:36 UTC). Ten purgatorio logs carry two segments (a relaunched
stream); purgatorio 1, 3, 10 have `unit` records in the earlier segment the
later one doesn't repeat, so the dedup rule (keep the last record per
`(canticle, canto, line_start, line_end)` across the whole file) *did* bite
this time.

**The refusal mix — the headline.** 33 units reopened across 27 cantos:

| verdict | S6.5 (74 units) | S6.7 (33 units) | share |
|---|---:|---:|---:|
| `accepted` (whole unit) | 33 | **8** | 45% → 24% |
| `salvaged` (S6.4's splice) | 9 | **3** | 12% → 9% |
| `no_improvement` (reverted) | 17 | **7** | 23% → 21% |
| `new_class` (reverted) | 15 | **15** | 20% → **45%** |
| `hard` | 0 | **0** | — |

**`new_class` did not move at all** — identical absolute count while the pool
halved, so lever 2 (telling the session the acceptance rule) bought nothing
measurable. Worse: every one of the 15 is now `missing_arg` (13
`new_class:missing_arg`, 2 mixed), where S6.5's were `extra_arg`-dominant, the
shape S6.4's splice was built for — dropping an argument the re-answer
*brought* is recoverable by a row splice; one it *removed* is not, when the
splice's own key is the row that moved.

**Lever 1 fired and did not convert.** `invalid_nudges` is 1 on **7** of 33
units, 0 on the rest, and **all 7 still ended `adopted_invalid`** — the
resume happened, the session re-submitted, its own gate still said invalid.

| | S6.5 | S6.7 |
|---|---:|---:|
| `adopted_invalid` | 36 / 74 (49%) | **14 / 33 (42%)** |
| …with turns unspent | 20 (27%) | **6 (18%)** |
| …at the 12-turn ceiling | 16 | 8 |
| `no_improvement` reaching the ceiling | 5 / 17 | 2 / 7 |

"Ends early on rows its own gate rejected" fell 27% → 18%, but not from the
resume — it fired 7 times, converted 0. `adopted_invalid` no longer tracks
refusal as it did in S6.5 (14 of 17 `no_improvement`); here **all 8
`accepted` units are `adopted_invalid`**, and `no_improvement` is no longer
"ran out of room" — 5 of 7 stopped short of the ceiling.

**Row-level** (diff against `2fd689f`, 9 files): **19 removed, 19 added, net
0** — 14 relabels, 3 arguments relocated, 2 added, 2 removed. **11 of 14
relabels are the level's own** (`obl` → `obl:di` 7, `obl:in` 3, `obl:a` 1),
plus `purgatorio 1:80` `obl` → `attr` — 12 findings cleared, one row each.
The 2 off-brief relabels: `obl:sanza` → `obl:senza`, `obj` → `obl`.
`salvaged` units (3): **exactly one row change each, nothing outside the
governed keys** (inferno 32:113, purgatorio 1:80, purgatorio 22:120), the
invariant holding a second time; `accepted` units (8) carry the other 16
changes, every relocation and both additions/removals.

**Cost.** 323 LLM calls, **4.00 M tokens** (2.77 M input / 0.27 M output /
0.97 M thought), **10.4 h** summed per-canto elapsed (inferno 3.5 /
purgatorio 5.8 / paradiso 1.1). 57 `api_retries`, 0 max-length retries, 0
paced. 73 cantos with no finding cost no model call.

**Gold agreement**: corpus-wide **0.7382 → 0.7384**; inferno 0.7444 → 0.7447,
purgatorio 0.7356 → 0.7360, paradiso 0.7343 → 0.7343 — flat, as a 12-row
change should be.

**What this settles.** Two of S6.5's three levers are measured and neither is
the bottleneck: the stopping rule fires and changes no verdict; stating the
acceptance contract leaves `new_class` unmoved. The row-scoped ask is the one
still untried, and this run sharpens the case for it — the refusals are now
overwhelmingly "the re-answer dropped an argument elsewhere in the unit,"
exactly what a whole-unit re-answer risks and a row-scoped one cannot. S6.6's
objection to it (narrowing suppresses off-brief gains) is now priced: this
run's off-brief yield was 2 relabels/2 added/2 removed/3 relocations on 8
accepted units against 12 findings cleared — much smaller than S6.3's 87.

**A mechanism gap.** Why an answer earned `new_class:missing_arg` — which
argument it dropped, whether on the named row — is not in the logs; `fix`
carries only `level` and `verdict` (S6.4's mistake in a new place, S6.6 fixed
it only for `invalid_nudges`). The refused candidate's own rows need logging
before the row-scoped ask is tried.

**State at close.** Corpus **0 hard / 4,649 soft**, 9 TSVs modified; suite
**969**, unchanged. **Level 1 has now been run three times, 377 → 83 → 37 →
25** — the third pass gaining 12 where the second gained 46, 25 findings
across 20 cantos refused by three independent sets of sessions. The
convergence curve S6.5 called is confirmed; a fourth run of the same
mechanism is not the next move.

### S6.8 — The refusal, on record: why an answer was refused, not just that it was (2026-09-02)

S6.7's closing item, shipped. **Code only; the corpus is untouched and running
anything over it stays the operator's act.** Three runs of level 1 have
reported *that* an answer introduced a class the unit didn't carry, none
saying **which row it came from** — the fact that separates the two live
hypotheses (the ask is too wide vs. the model is wrong at the position
itself), and the one the untried row-scoped ask is aimed at. S6.6 already
learned this lesson once: `invalid_nudges` was added *before* the run that
measured it, precisely so that run would be readable.

**What is written, and when.** On a refused whole-unit answer — `no_improvement`,
`new_class`, `hard`, and the refusals a splice later rescues — `record["fix"]`
gains `refused`, from `reconstruct.fix_diagnosis`:

| field | the question it answers |
|---|---|
| `rows.added` / `.removed` / `.relabelled` | what the answer actually proposed, each row marked `governed` (inside `fixlevel.governed_keys`) or not |
| `governed_rows` | what the answer did with the rows the level *named*: `relabelled` / `removed` / `untouched` / `missing`, against `named` |
| `introduced` | every violation class the answer brought that the unit did not carry, with the position it sits on and whether that position is one the level asked about |
| `findings_before` / `_after`, `soft_before` / `_after`, `hard_after` | the verdict's own inputs, per unit rather than only in the canto aggregate |
| `salvage` | what the position-scoped splice then made of it — its `fix_verdict` reason, or why it could not be measured (`token_assertions` / `no_governed_rows`) |

Two smaller additions. `record["fix"]["delta"]` now carries `row_delta` per
unit under every verdict (zeros on a reverted one), so an accepted unit's
off-brief reach — S6.3's 87 relabels, S6.7's 2 — reads from the log directly.
And the `unit` record carries `final_validation_errors`, off the same last
`validate_candidate` dispatch `final_submission_valid` reads its verdict from
— S6.7's second finding needs it: all 8 of its accepted units were
`adopted_invalid` and nothing on record said what was being rejected. The
watched-run console line gains the same in one clause.

**Nothing here reaches a session** — the diagnosis is computed after
`fix_verdict` decides, written only to the log, changing no verdict, rule, or
notice. Suite **969 → 971**; `harness/recon/` untouched at **0 hard / 4,649
soft**.

**The run this is for**: a `--fix 1` re-run, logs swept first, read out as
**S6.9**, reading `introduced[].governed` first — off the named rows means the
row-scoped ask is the mechanism to build next; on them means the level's own
premise at those positions needs arguing.

### S6.9 — The `--fix 1` run under S6.8's logging: 11 of 25 cleared, and level 1's own premise fails at the survivors (2026-09-02)

The operator's fourth level-1 run, on the S6.8 logging, logs swept first.
**The corpus moved; no code did.** S6.8 set the reading order in advance, so
this record follows it: `introduced[].governed` first, the finding count as
context.

**The numbers, against S6.7's close (`7edf773`):**

| | before | after |
|---|---:|---:|
| hard violations | 0 | **0** |
| soft violations | 4,649 | **4,640** (−9) |
| level-1 findings (`make fix-level`) | 25 | **14** (−11, 44%) |
| cantos carrying a level-1 finding | 20 | 12 |
| TSVs modified | — | 10 |
| gold agreement (readout, §5 discipline 4) | 0.7384 | 0.7386 |

`make check` exits 0. The logs are unambiguous this time: all 100 carry
timestamps from 2026-09-01 15:58–20:14 UTC, one `summary` segment each, no
canticle stream relaunched — so the dedup rule still applied below has nothing
to do. (It is still the right rule; S6.7's shape is the one that needs it.)

**The refusal mix.** 22 units reopened across 20 cantos:

| verdict | S6.7 (33 units) | S6.9 (22 units) | share |
|---|---:|---:|---:|
| `accepted` (whole unit) | 8 | **10** | 24% → 45% |
| `salvaged` (S6.4's splice) | 3 | **0** | 9% → **0%** |
| `no_improvement` (reverted) | 7 | **4** | 21% → 18% |
| `new_class` (reverted) | 15 | **8** | 45% → 36% |
| `hard` | 0 | **0** | — |

Salvage collected nothing: it ran on all 12 refused units and `fix_verdict`
refused every candidate — 7 still `new_class:missing_arg`, 5
`no_improvement`, as S6.7 predicted; the diagnosis below now proves the
mechanism rather than inferring it.

**`refused.introduced[].governed` — the question S6.8 was built for.** The 12
refused answers introduced **14** violations between them, itemised in full:

| class | count | on a row the level named |
|---|---:|---:|
| `missing_arg` | 9 | **9** |
| `extra_arg` | 4 | 0 |
| `membership` | 1 | 0 |

**Nine of the fourteen sit on the level's own rows**, and `governed_rows` says
the same thing without the sampling:

| | |
|---|---:|
| `named` (rows the level asked about, across the 12 units) | 14 |
| `relabelled` | **0** |
| `removed` | 10 |
| `untouched` | 4 |
| `missing` | 10 |

**Not one refused answer ever relabelled a row the level named.** It either
dropped the row entirely (10, precisely the `missing_arg` it's then refused
for) or left it untouched (4, `no_improvement`). That is why the splice
cannot help: S6.4 splices *the answer's rows at the governed keys*, and at
those keys the answer has no row. **The row-scoped ask is not the mechanism
this evidence calls for** — narrowing the brief to a row the session declines
to write cannot help. What needs arguing is the level's own premise there.

**`final_validation_errors` — S6.7's second finding, answered.** 9 of the 10
`accepted` units are `adopted_invalid`, and every error on every one of them is
the *same* gate, `harness/runner/tools.py:879`:

> `argument X.Y cites neither a Layer 3 NP head nor a pronoun (nominal role
> 'obl:<prep>' requires one; clausal and adverbial roles may anchor on any
> token)`

Put beside the verdict, `adopted_invalid` is not noise — it is **anti-correlated
with acceptance**:

| session's own gate on the final submission | `accepted` | `no_improvement` | `new_class` |
|---|---:|---:|---:|
| passed (`final_submission_valid`) | 1 | 2 | **8** |
| failed (`adopted_invalid`) | **9** | 2 | 0 |

Every answer the session's gate passed was refused downstream on all but one
unit; every answer that cleared findings but one was refused by its own gate.
The two gates pull in opposite directions, and the level sits between them.

**Why, as positions not aggregates** (§5 discipline 5). All 14 surviving
findings sit in the 12 refused units — accepted units cleared every finding
they were given. Each survivor's argument against the gate's own test:

| | |
|---|---:|
| argument is neither an L3 NP head nor a pronoun | **12 / 14** |
| Layer-2 POS of those 12 arguments | adverb 11, preposition 1 |

They are `giuso`, `giù`, `qua`, `suso`, `entro`, `dietro`, `là`, `qui`, `fuor`,
`presso` — the locative adverbs. `derive.py`'s `_oblique_role_of` qualifies such
an oblique from its Layer-4 `case` child like any other, which is what makes it
a level-1 finding; `validate.py`'s own anchor check then **explicitly exempts
it** (line 158):

```python
if (row.role == "obl" or row.role.startswith("obl:")) and arg in adverb_obl_positions:
    continue
```

`harness/runner/tools.py:requires_nominal_anchor` carries none of that
exemption — it admits only an L3 NP head or a pronoun, where `validate.py`
also passes predicate positions, adverbial obliques, dep-argument positions
(rule AF), aux heads (AQ), coordination heads (DG) and marker slots (DS).
**The session's gate is strictly narrower than the layer's own contract, and
the survivors sit in the gap.** The row level 1 asks for at these 12
positions is one the contract permits and the session's own gate forbids, so
the model has exactly two moves: drop it (`new_class:missing_arg`, 10) or
override the gate and submit anyway (`adopted_invalid`, how the 9 accepted
units cleared their findings). Three independent sets of sessions have now
produced both, and neither is a model error.

The remaining 2 are ordinary: `purgatorio 30` (`sogno`) and `paradiso 6`
(`anni`) are nouns with an NP head, nothing blocks the row, and both came
back `no_improvement` — the session simply didn't change them.

**Row-level** (diff against `7edf773`, 10 files): **20 rows added, 17
removed, net +3**, all from `accepted` units — `fix.delta` is zero on all 12
refused units, so the reverts are clean. 14 relabels in place, **12 the
level's own shape** (`obl` → `obl:in` 5, `obl:di` 4, `obl:a` 2, `obl:da` 1)
against 11 findings cleared, 2 off-brief (`obl:di` → `obl` at paradiso 10:30,
`obj` → `subj` at inferno 34:90). Beside them 6 added, 3 removed, three
additions pairing as subject relocations — the relabels outnumbering findings
cleared is the non-distance property again (§2).

**Lever 1, third measurement.** `invalid_nudges` is 1 on **7** of the 22 units
and 0 on the rest; all 7 still ended `adopted_invalid`, as in S6.7. It fires,
the session re-submits, its gate still says invalid — and on this evidence it
never could, because at these positions the gate is refusing a row the level
requires. 6 of those 7 nonetheless ended `accepted`.

**Cost.** 202 LLM calls, **2.56 M tokens** (1.77 M input / 0.17 M output /
0.62 M thought), **6.44 h** of summed per-canto elapsed (inferno 2.74 /
purgatorio 2.20 / paradiso 1.50). 20 `api_retries`, 0 max-length retries, 0
paced seconds. The 80 cantos with no finding cost no model call.

**Gold agreement, opened afterwards and cited as nothing else** (§5 discipline
4): corpus-wide **0.7384 → 0.7386**; inferno 0.7448, purgatorio 0.7363,
paradiso 0.7345. Flat, as a 20-row change should be.

**State at close.** Corpus **0 hard / 4,640 soft**, 10 TSVs modified; suite
**971**, unchanged and not re-run — no code moved. **Level 1 has now been run
four times: 377 → 83 → 37 → 25 → 14.**

**What this settles, and what it opens.** All three of S6.5's transferable
levers are now measured and none is the bottleneck. The bottleneck is a
**contract seam inside `harness/`**: `requires_nominal_anchor` transcribes
`validate.py`'s anchor rule but kept only the NP-head/pronoun clause, dropping
every exemption beside it, so the agent-side gate and the corpus-side checker
disagree about which rows are writable. Two ways out — §2's outcomes 1 and 2
wearing different clothes:

1. **Widen the gate to what it transcribes.** `requires_nominal_anchor` (or the
   check that calls it) admits what `validate.py` admits — at minimum the
   `obl`/`obl:*` adverbial exemption, which is written for this exact shape. Its
   authority is the layer's own contract read directly, discipline 3's
   cleanest case, and it opens no gold. This is the move this record
   recommends.
2. **Narrow the level.** Declare the anchor-less oblique a position where the
   derivation and the artifact format disagree — outcome 2, a missing
   tolerance — and take those positions out of level 1's selection.

They are not equivalent and the difference is the point: (1) says the harness
mis-transcribed its own contract and the findings are real; (2) says the
findings should never have been selected. **(1) is the honest reading of the
evidence** — `validate.py` permits the row, `derive.py` determines it, and only
`tools.py` objects — and (2) would leave the same disagreement live everywhere
else the gate is narrower than the contract, where no level has looked yet. The
choice, and whether a fifth level-1 run follows it, is the operator's.

### S6.10 — The gate made a faithful transcription, and the level given a precondition (2026-09-02)

S6.9's two findings, answered. **Code and tests only; the corpus is untouched at
0 hard / 4,640 soft and `dante_corpus/` is not modified** — both defects were in
`harness/`'s own transcriptions of the contract, so both fixes are harness-side
and the shared checker keeps its numbers.

**Patch 1 — the anchor rule (`harness/runner/tools.py`), for the 12.**
`requires_nominal_anchor` still says which *roles* demand an anchor; what counts
*as* one now goes through `anchor_admits`, which transcribes `validate.py`
155-179 rather than half of it:

| clause | `validate.py` | before | after |
|---|---|:-:|:-:|
| Layer-3 NP head | 156 | ✓ | ✓ |
| pronoun | 156 | ✓ | ✓ |
| a predicate of the submission itself | 156 | — | ✓ |
| an adverb under `obl`/`obl:*` (**unconditional**) | 158 | — | ✓ |
| a Layer-4 argument position (`ARG_DEPRELS`, rule AF) | 160 | — | ✓ |
| aux head (AQ) / coordination head (DG) / marker slot (DS) | 163-181 | — | — |

The last row is a deliberate gap — tree walks no committed position needs.
`ARG_DEPRELS` is transcribed as a literal, not imported (this module imports
nothing from `skel/` but the frozen role vocabulary), and the symmetry test
below keeps the copy honest.

**Measured over the 100 committed TSVs, 31,242 rows:** the gate now rejects **0**
rows `validate.py` accepts, and accepts **0** it rejects. The untranscribed
clauses cost nothing today, and the test says if that changes.

At the 12 deadlocked positions the anchor error is gone — **12 of 12** — and with
every level-1 governed row of a unit relabelled to the qualification the
derivation determines, **8 of the 10 units now clear `validate_candidate`
entirely**. The session has an admissible answer where before it had none.

**Patch 2 — the level's precondition (`harness/extractor/fixlevel.py`), for
the 2.** `FixClass` gains `holds`, and `select` takes the artifact's rows: a
finding naming a row the artifact does not have is not work a repair level can
do (for `oblique_qualification`: "there is a bare `obl` row at this key").
`select` without rows stays unchanged deliberately — the precondition belongs
at *selection* (`print_fix_level`, `build_fix_plan`, the keys a splice may
touch), not the acceptance test, since `fix_verdict` compares a before/after
count and must apply one definition to both. `check_canto` now returns the
canto's rows so the readout and plan cannot disagree about the pool.

**`make fix-level FIX=1`: 14 → 12** across 10 cantos. Both declined findings are
S6.9's mis-paired pair (purgatorio 30, paradiso 6), and this is a **selection**
change, not a corpus one: `make check` still reports 0 hard / 4,640 soft and
both positions remain soft `role_mismatch`. Whether the artifact is
over-complete there or the two notations are equivalent is a §2 question nobody
has argued, which is exactly why the level declines it rather than repairing it.

**A second asymmetry, found while verifying and deliberately not fixed.** Two
units still fail their gate — inferno 12 (`132.4`, case child `132.1 'ove'`)
and inferno 18 (`34.4`, case child `34.3 'di'`) — where
`oblique_case_qualification` demands a qualification at a bare `obl` that
`check.py` reports **no level-1 finding for**: the classifier's registry
tolerances excuse those positions and the session's bar carries no such
tolerance. S6.9's asymmetry in the other rule, one grade milder — the session
*can* satisfy both, so it's off-brief pressure not a deadlock, which is why 8
of 10 rather than 10 of 10. A level's bar and its selection ought to name the
same positions; arguing that is its own piece of work.

**Tests: 971 → 975.**

- `test_anchor_gate_is_never_stricter_than_validate` — over the twelve cantos
  that carried the deadlock plus one control, every row the gate refuses must be
  a row `validate.py` refuses too. **This is the guard the mechanism was
  missing**: S6.2 added a level-1 bar to the session gate without checking it
  against the rule already there, and three runs and ~29 findings' worth of
  refusals went by before the contradiction was visible.
- `test_validate_candidate_admits_a_qualified_adverbial_oblique` — the concrete
  S6.9 position (`riguardando ... giuso`, `case` child 53.4 'in').
- `test_select_declines_a_finding_whose_row_the_artifact_lacks` and
  `test_fix_level_readout_and_plan_agree_on_the_pool`.
- `test_validate_candidate_still_rejects_non_nominal_anchor_on_nominal_role`
  became `test_validate_candidate_admits_layer4_argument_as_nominal_anchor`: it
  asserted the gate holding the NP-head/pronoun line at a position Layer 4 makes
  a `ccomp`, which is the bug, not the contract. The neighbouring test that a
  non-argument adjective (`oscura`, `amod`) is still refused is unchanged apart
  from the error's new wording.

**What this is worth, stated as a prediction and not a result.** 12 findings are
now writable that were not; nothing here makes the model choose the right lemma,
and the fix run is the operator's. The evidence for optimism is that S6.9's
accepted units produced exactly this relabel 12 times, and the level-1 bar's own
error names the case child and its word. The evidence for caution is the second
asymmetry above, which is live at 2 of the 10 units.

### S6.11 — The `--fix 1` run under S6.10's gate: 12 of 12 cleared, and level 1 closes (2026-09-02)

The operator's fifth level-1 run, on the S6.10 gate and with the per-canto logs
swept first. **The corpus moved; no code did.** S6.10 named three readings and a
predicted residue in advance, so this record answers those before it reports the
count.

**The numbers, against S6.10's close (`a9c3b1c`):**

| | before | after |
|---|---:|---:|
| hard violations | 0 | **0** |
| soft violations | 4,649 → 4,640 | **4,627** (−13) |
| level-1 findings (`make fix-level`) | 12 | **0** |
| cantos carrying a level-1 finding | 10 | **0** |
| TSVs modified | — | 10 |
| gold agreement (readout, §5 discipline 4) | 0.7386 | 0.7389 |

`make check` exits 0. Logs unambiguous (all 100 carry 2026-09-02 07:26–07:46
UTC, one `summary` segment each — the dedup rule has nothing to do). Cost:
**34 model calls** across 10 reopened units (3–4 per unit), 224,423 tokens
(151,564 in / 15,070 out / 57,789 thought), 2,065 s session wall clock. The
other 90 cantos reopened nothing, as `fix-level` said.

**The refusal mix — there is none.** 10 units reopened across 10 cantos:

| verdict | S6.9 (22 units) | S6.11 (10 units) |
|---|---:|---:|
| `accepted` (whole unit) | 10 | **10** |
| `salvaged` (S6.4's splice) | 0 | 0 |
| `no_improvement` (reverted) | 4 | **0** |
| `new_class` (reverted) | 8 | **0** |
| `hard` | 0 | **0** |
| `adopted_invalid` | 11 / 22 | **0 / 10** |

Every unit passed its own gate: `final_submission_valid` is true 10 of 10,
`final_validation_errors` is empty on every one, and `invalid_nudges` is 0 — the
S6.6 resume never had to fire. No answer was refused, so `fix.refused` is absent
throughout and S6.8's diagnosis block has nothing to describe.

**S6.10's three readings, in the order it set them.**

1. **`refused.governed_rows.relabelled` becomes non-zero** — satisfied in the
   limit case: there are no refused units, and `fix.delta` says the same thing
   for the accepted ones. **15 rows relabelled, 1 removed, 0 added** across the
   ten. S6.9's 12 refused answers relabelled a named row 0 times; here every
   named row is relabelled to exactly the qualification the derivation
   determines (below).
2. **`new_class:missing_arg` collapses** — 0 introduced classes, and no unit
   dropped a governed row. The deletion S6.9 saw was the gate refusing to write
   the level's own row, and that reason is gone.
3. **`adopted_invalid` stops tracking acceptance** — it stops occurring at all.
   S6.9's anti-correlation (9 of 10 accepted units failing their own gate, every
   error naming the one anchor rule) does not survive the transcription fix, as
   S6.10 predicted it would not.

**The 12 findings, position by position** (§5 discipline 5) — recomputed against
the pre-run artifacts at `a9c3b1c`, so the pairing is measured and not inferred:

| canto | finding | written |
|---|---|---|
| inferno 9 | `53.3 arg (53,5) 'obl' vs 'obl:in'` | `obl:in` |
| inferno 12 | `130.10 arg (130,9) 'obl' vs 'obl:a'` | `obl:a` |
| inferno 18 | `35.1 arg (34,2) 'obl' vs 'obl:di'` | `obl:di` |
| inferno 26 | `140.4 arg (140,8) 'obl' vs 'obl:in'` | `obl:in` |
| inferno 26 | `141.4 arg (141,6) 'obl' vs 'obl:in'` | `obl:in` |
| inferno 33 | `96.2 arg (96,4) 'obl' vs 'obl:in'` | `obl:in` |
| purgatorio 10 | `71.2 arg (71,4) 'obl' vs 'obl:da'` | `obl:da` |
| purgatorio 10 | `72.7 arg (72,3) 'obl' vs 'obl:di'` | `obl:di` |
| purgatorio 13 | `143.8 arg (144,2) 'obl' vs 'obl:di'` | `obl:di` |
| purgatorio 14 | `66.7 arg (65,5) 'obl' vs 'obl:di'` | `obl:di` |
| purgatorio 17 | `13.5 arg (14,4) 'obl' vs 'obl:di'` | `obl:di` |
| purgatorio 22 | `85.9 arg (85,5) 'obl' vs 'obl:di'` | `obl:di` |

**12 of 12, each to the preposition the derivation names** — without ever
being shown it (the session sees the case child, not `check.py`'s line). What
S6.10 called the evidence for optimism is now the result, not the prediction.

**The predicted residue did not appear.** S6.10 named the two units carrying its
second asymmetry — inferno 12 (`132.4`, case child `132.1 'ove'`) and inferno 18
(`34.4`, case child `34.3 'di'`) — and predicted they would be the only two of
the ten to fail `validate_candidate`. **Both were accepted and both passed their
own gate.** What the bar's extra demand produced was an off-brief relabel, not a
deadlock: `131.8 (132,4) obl → obl:ove` and `35.1 (34,4) obl → obl:di`. The
asymmetry is therefore confirmed as *real but benign* in the field, exactly the
grade S6.10 assigned it ("the session can satisfy both there"), and the ten-unit
run is the falsification test it asked for.

**The off-brief reach, and where the −13 comes from** (`fix.delta.row_delta`
under an accepted verdict, S6.8's addition, so no `git diff` is needed to see
it). 15 relabels and 1 removal against 12 findings — 4 row changes lie off the
level's rows:

| off-brief change | soft effect |
|---|---|
| inferno 12 `131.8 (132,4) obl → obl:ove` | **−1** (it was an `extra_arg`; the relabel matches the derivation) |
| inferno 18 `35.1 (34,4) obl → obl:di` | 0 (a tolerated position, tolerated still) |
| purgatorio 14 `65.1 (66,7) obl → ccomp` | 0 (`role_mismatch` out, `extra_arg: 65.1 ccomp (66,7)` in) |
| inferno 9 `54.3 (54,1) obl` removed | 0 (an untolerated row that carried no finding) |

So **−12 from the governed rows and −1 from off-brief reach**, and the only
class this run introduced anywhere is the one `extra_arg` above, inside an
accepted unit. Two of the four off-brief changes are the second asymmetry's own
positions, which is the mechanism S6.10 described doing exactly what it said.

**Level 1 is closed: 377 → 83 → 37 → 25 → 14 → 12 → 0**, over five fix runs and
four mechanism changes (S6.4's splice, S6.6's two levers, S6.8's logging,
S6.10's transcription). Read against the stage's method, the decisive change was
the last one and it was not a prompting change at all: the gate the session is
judged by had to say what the corpus contract says. The three levers S6.5
proposed are all measured and none of them moved the count; **the seam between
`harness/`'s transcription and `skel/`'s contract did.** That is the transferable
finding for level 2 — before a level is tuned, check that its bar and its
selection name the same positions and that both agree with `validate.py`
(`test_anchor_gate_is_never_stricter_than_validate` is the shape of that check).

**Nothing here changes the tolerance-mediated zero point (S6.1).** 4,627 soft is
a conformance number; level 1 removed the class it was argued for under §2's
first outcome (the artifact is wrong) and nothing else. The next candidate class
must be argued from `validate.py` / `derive.py` with gold unopened, as always.
