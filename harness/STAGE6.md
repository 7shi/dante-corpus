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

### Infrastructure note — llm7shi 0.15.0 lands the status-bar hooks (2026-08-31)

Not a milestone record and not stage work: no corpus artifact, no rule, no
level. Filed here only so the next session isn't surprised that
`runner/statusline.py` and the §4 display standard both moved while the
`make fix` run was in flight. **S6.3 stays reserved for that run's readout.**

The upstream change [`../ARCHITECTURE.md`](../ARCHITECTURE.md) §4 recorded as
"under consideration on the llm7shi side, not yet actioned" shipped in llm7shi
**0.15.0**, and the harness now sits on it:

- **The bar needs no subclassing.** `progress(started_at=...)` places the run
  clock beside the label, so `_HarnessProgressContext` and the local
  elapsed-since-`STARTED_AT` column are gone, along with the imports of
  llm7shi's private `_MofNColumn` / `_ProcessElapsedColumn` / `_ProgressContext`
  (which 0.15.0 renames — the guarded import would otherwise have degraded the
  bar to plain stderr lines *silently*, which is why this could not wait).
  A bar that does need more now overrides `ProgressContext.columns()` and points
  `StatusLine.progress_context_class` at it.
- **Markup-off is upstream's default**, so the `print`/`error` overrides that
  existed to keep `[obl:a=(126,3)]` from vanishing and `[/b]` from raising
  `MarkupError` are deleted. The guarantee is unchanged and still tested.
- **The console is no longer pinned to stderr.** It carries streamed model
  output as well as the bar, so pinning it moved that too, and no artifact's
  durability depends on where the display lands (§5's contract is about `--log`
  files, not the console).
- What remains local is the `wait_retry` retry accounting (`api_retries` /
  `api_retry_seconds`) — application measurement, not a workaround.
  `runner/statusline.py` is 102 → 61 lines.

Docs updated to match: ARCHITECTURE.md §0 checklist + §4, and
[`PLAN.md`](PLAN.md) §4 item 5's summary of it. Stage records are left as
written — STAGE2.md's 2026-08-24 wiring description is a record of what shipped
then. Suite **957 passed**, count unchanged by this work (one existing test's
stderr expectation updated); `harness/recon/` untouched.

### S6.3 — `make fix` level 1 over the whole corpus: 294 of 377 cleared (2026-09-01)

The operator's run of S6.2's mechanism over all 100 cantos, read out here. It is
the first time a soft finding has reached a live session, and the first
corpus-wide edit since S5.7. **The corpus moved; no code did.**

**The numbers, against the S6.2 baseline (`007d973`, verified by re-checking
that commit's TSVs rather than trusting the prose):**

| | before | after |
|---|---:|---:|
| hard violations | 0 | **0** |
| soft violations | 5,014 | **4,706** (−308) |
| level-1 findings (`make fix-level`) | 377 | **83** (−294, 78.0%) |
| cantos carrying a level-1 finding | 95 | 50 (45 cleared outright, **none worse**) |
| gold agreement (readout, §5 discipline 4) | 0.7309 | 0.7372 |

`make check` exits 0, so the regression signal the hard track leaves behind is
intact. The level's own measure — how many of the 377 survive — is the honest
headline: **83**, and no canto and no unit carries a level-1 finding it did not
carry before.

**Per soft class** (nothing rose): `role_mismatch` 573 → **287** (−286);
`missing_arg` 1,646 → 1,636; `extra_arg` 2,114 → 2,107; `membership` 146 → 143;
`missing_tuple` 490 → 488; `extra_tuple` 43 and `dual_role` 2 unchanged. The
level's class carries −286 of the −308, and the other −22 are collateral gains
in classes the run was not aiming at. Per §2 this near-agreement between −294
findings and −308 soft is *not* evidence the two measure the same thing: soft is
not a distance, and a relocated argument still scores twice.

**The mechanism, from the 100 per-canto logs** (fix run only; 13 cantos were
re-invoked after an interruption, so the aggregates below sum every fix
invocation and the unit counts are deduplicated by span):

- **337 unique units reopened across 95 cantos**, 360 unit records (22 units
  reopened a second time by a re-invocation). Final verdict per unique unit:
  **265 accepted (78.6%), 46 `new_class`, 26 `no_improvement`, 0 `hard`**.
- **Zero `hard` refusals is the first result.** S5.5/S5.7 moved the schema
  checks into the session, so a fix session's answers are hard-clean by
  construction — the acceptance test's first refusal never fired once in 360
  attempts, and the corpus is still 0 hard afterwards. The gate now costs
  nothing and guards a real invariant; that is what a settled gate looks like.
- **The dominant refusal is `new_class`, not `no_improvement`** (46 vs 26):
  `missing_arg` 27, `extra_arg` 21, `membership` 7, `missing_tuple` 1 (a unit
  may bring more than one). The limiting factor is therefore *not* the model failing
  to derive the qualification from the notice — it derives it — but the fact
  that it re-answers the **whole unit** while the level names a single row, and
  the re-answer trades the cleared class for an argument-level one. That is the
  interesting negative result, and it belongs to the design, not to the model:
  §S6.2's "replaces those rows" is a whole-unit replacement.
- **Row-level** (the diff against `007d973`, 93 files, +484/−455 lines):
  **322 relabels, 188 rows added, 151 removed, net +37 rows.** Only **235** of
  the relabels are the level's own `obl` → `obl:<prep>` (`obl:come` 68,
  `obl:di` 56, `obl:in` 49, `obl:a` 10, `obl:che` 9, `obl:per`/`obl:da` 7 each,
  …). The other 87 are the re-solve reaching past its brief: `obl` → `attr` 12,
  `obl` → `xcomp` 12, `obl` → `ccomp` 7, `obl:ne` → `obl:in` 5, `subj` ↔ `obj`
  8, plus normalisations of the preposition itself (`obl:col` → `obl:con` 3,
  `obl:sovra` → `obl:sopra` 2, `obl:ad` → `obl:a` 2, `obl:de` → `obl:di` 2).
- **So PLAN.md's readout expectation — "expect only role relabels; an added or
  deleted row is a finding worth explaining" — is falsified, benignly.** The
  explanation is the same whole-unit replacement: 339 rows moved without a
  counterpart. One of them is worth naming, `purgatorio 21:87`, where the
  empty-line placeholder (`87 0 <> 0 0`) was replaced by two rows for the
  predicate `famoso` — a predicate *registered*, which §2 records as the exact
  move that **raises** the soft count while being a strict improvement.

**`adopted_invalid` means something different under `--fix`, and the number must
not be compared across runs.** 99 of 360 attempts (27.5%) ended on rows the
session's own gate rejected, 66 of them on units the acceptance test then
accepted. There is no contradiction: the level-1 bar is added to
`validate_candidate` as an **error**, so `valid: false` under `--fix 1` usually
means "a bare `obl` with a lemma-bearing `case` child is still on the sheet",
not the schema failure the S5.5-era number reported. It correlates with the
refusals exactly as it should — 25 of the 30 `no_improvement` records are
`adopted_invalid`, i.e. the session ran out of room still failing its own check.

**Cost.** 2,287 LLM calls, **23.87 M tokens** (16.24 M input / 1.55 M output /
6.08 M thought), **61.5 h** of summed per-canto elapsed (inferno 22.0 /
purgatorio 28.5 / paradiso 10.9), so ≈28.5 h wall clock on the three `-j3`
streams. 170 `api_retries` absorbing 6,469 s of 429 backoff, 21 max-length
retries, 0 paced seconds. The ~3,140 units carrying no level-1 finding cost no
model call, as designed.

**Gold agreement, opened afterwards and cited as nothing else** (§5 discipline
4): corpus-wide **0.7309 → 0.7372** (P 0.7079 → 0.7136, R 0.7555 → 0.7624;
+275 true positives on +38 rows); inferno 0.7357 → 0.7437, purgatorio
0.7282 → 0.7343, paradiso 0.7287 → 0.7334. This is the largest agreement move
the project has recorded — the whole hard track was 0.7307 → 0.7309 — which
says only that the soft residue is where the remaining distance to gold lives,
as S5.7 predicted. It is **not** the reason the level shipped: that was argued
from `derive.py`'s contract in S6.2, gold-closed.

**What the two available routes to this class now measure.** §3's dry run of
`skel/repairs.py` (`role_label` + `null_subject`, two classes) projected soft
5,014 → 3,949 with 720 rewrites and +0.0166 agreement, deterministically and in
seconds. The live route cleared 294 findings of one class for ~28 h and
+0.0063. They are not the same scope and the comparison cannot decide the open
authority question in §3 — but it does price it: the deterministic rewrite
transcribes `derive_unit`, and this run is the measurement of a model
re-deriving the qualification from the frozen layers, which is what §1 says the
project exists to obtain.

**State at close.** Corpus **0 hard / 4,706 soft**, 93 TSVs modified in the
working tree and uncommitted; suite **957 passed** (unchanged — no code moved);
the per-canto logs on disk are this run's only telemetry and everything above
is read out of them. Level 2 is not opened: on this evidence its class must be
argued from the contract first (§2's three outcomes), and the `new_class`
refusal rate says the *unit* granularity of replacement, not the level table,
is the next thing worth designing.

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

**The mechanism.** A `FixClass` now also declares the artifact rows one of its
findings governs (`fixlevel.FixClass.keys`; level 1 returns the single
`(predicate, argument)` key it relabels, since its repair is a relabel in
place). Acceptance runs in two scopes:

1. **the whole unit**, exactly as before — the answer the session stands behind,
   taken entire when it passes, so the row additions and removals S6.3 measured
   on the 265 accepted units are untouched;
2. on refusal, **a position-scoped splice** (`salvage_rows`): the recorded rows
   stand everywhere except the governed keys, where the answer's rows replace
   them. Outside those keys nothing is added or removed, so a salvage cannot
   import a class the unit never carried — but that is a property of the
   mechanism, not an assumption it makes: the spliced rows go back through
   `_validate_rows` and the *same* `fix_verdict`, and a salvage that fails it is
   reverted like any other refusal.

Verdicts gain `salvaged`, with the whole-unit refusal kept beside it as
`fix.unit_verdict` in the unit record — the salvage rate is only readable
against what the unit answer was refused for — and `verdict:salvaged` in the
canto's fix stats and the summary line. Salvage is refused outright when the
submission's own token assertions failed: its words disagree with Layer 1, so
none of its rows may be spliced into the record.

**What this does not claim.** The 46 units' submissions are not in the logs
(a refused unit is logged as the reverted rows it kept), so how many of the 52
findings a salvage would actually have taken is **not measurable without a
re-run** — 46 is the floor the verdict order guarantees, 52 the ceiling. The 26
`no_improvement` units may be salvageable too (a level finding fixed at one
position and lost at another scores no improvement unit-wide) and are equally
unmeasurable from here. Nothing about the level table changed, no gold was
opened, and no derived label crosses into a session.

Suite **957 → 960** (the governed-key mapping, the splice, and one end-to-end
`--fix` run whose stub answer repairs the oblique and brings an extra row).
`harness/recon/` untouched: corpus still **0 hard / 4,706 soft**.

### S6.5 — The `--fix 1` re-run on S6.4's mechanism: 46 of 83 cleared, 12 of them by salvage (2026-09-01)

The operator's re-run of level 1 over all 100 cantos on the S6.4 splice,
read out here. **The corpus moved; no code did.** The headline the re-run was
launched for is the salvage yield, and it is much smaller than the delta:
S6.4 could bound the 46–52 band but not predict how a *fresh set of live
sessions* would partition it, and most of what moved this time moved for a
different reason.

**The numbers, against S6.3's close (`b1ef280`, re-checked from that commit's
TSVs rather than trusted from prose):**

| | before | after |
|---|---:|---:|
| hard violations | 0 | **0** |
| soft violations | 4,706 | **4,660** (−46) |
| level-1 findings (`make fix-level`) | 83 | **37** (−46, 55.4%) |
| cantos carrying a level-1 finding | 50 | 28 (22 cleared outright, **none worse**) |
| TSVs modified | — | 32 |
| gold agreement (readout, §5 discipline 4) | 0.7372 | 0.7382 |

`make check` exits 0.

**Per soft class** (nothing rose): `role_mismatch` 287 → **242** (−45),
`extra_arg` 2,107 → 2,106 (−1), everything else unchanged (`missing_arg` 1,636,
`missing_tuple` 488, `membership` 143, `extra_tuple` 43, `dual_role` 2). Note
the level's own subset fell by 46 while `role_mismatch` as a whole fell by 45:
one *non*-level-1 `role_mismatch` appeared (204 → 205). Soft is not a distance
(§2), so the −46/−46 coincidence is arithmetic, not corroboration.

**The mechanism, from the 100 per-canto logs.** S6.4's deduplication caution did
not bite: the run wrote exactly **one segment per canto** and no canto was
re-invoked, so the 74 `unit` records are 74 distinct units, across the 50 cantos
that carried a finding. Final verdicts:

| verdict | units | findings before | after |
|---|---:|---:|---:|
| `accepted` (whole unit) | 33 | 34 | **0** |
| `salvaged` (S6.4's splice) | 9 | 13 | **1** |
| `no_improvement` (reverted) | 17 | 20 | 20 |
| `new_class` (reverted) | 15 | 16 | 16 |
| `hard` | 0 | — | — |

**So the salvage mechanism collected 12 of the 46.** The other 34 came from the
whole-unit answer simply passing this time on units S6.3's answer had failed —
live-session variance, not S6.4. Zero `hard` refusals again, as in S6.3.

**What happened to the 83, by where they sat in S6.3** (the question S6.4 could
not answer without this run):

| S6.3 verdict | → `accepted` | → `salvaged` | → `no_improvement` | → `new_class` |
|---|---:|---:|---:|---:|
| `new_class` (52) | 20 | 13 | 8 | 11 |
| `no_improvement` (28) | 14 | — | 9 | 5 |
| `accepted` (3) | — | — | 3 | — |

**33 of S6.4's 52 cleared — but only 13 findings' worth went through the
salvage path, and one of those survived it.** S6.4's "at least 46 of the 52 are
repairs the level itself calls correct" was a claim about *S6.3's* discarded
answers; those answers are not in the logs and were never re-offered, so the
re-run could not collect them. It collected what its own sessions produced. The
floor was a floor on a population that no longer exists — worth recording as the
limit of what a refused-and-unlogged answer can be reasoned about at all.

**Salvage's own rate: 9 of the 41 whole-unit refusals (22%)**, and every one of
the 9 rescued a `new_class:extra_arg` refusal (`fix.unit_verdict`) — the splice
is doing exactly the job it was designed for, dropping the extra argument the
re-answer brought while keeping the relabel. No other refusal class was
salvageable in this run.

**Row-level** (the diff against `b1ef280`, 32 files): **44 relabels, 19 rows
added, 21 removed, net −2.** **39 of the 44 relabels are the level's own**
`obl` → `obl:<prep>` (`obl:di` 12, `obl:in` 8, `obl:a` 5, `obl:per` 4,
`obl:come` 3, `obl:da`/`obl:con` 2 each, `obl:senza`/`obl:verso`/`obl:quale` 1
each); the 5 others are `obl:de` → `obl:di` 2, `obl:sanza` → `obl:senza`,
`subj` → `ccomp`, `attr` → `xcomp`. Attributed by verdict:

- `accepted` units: 34 relabels, 19 added, 19 removed — the whole-unit
  replacement still reaches past its brief, exactly as S6.3 recorded.
- `salvaged` units: **10 relabels, 0 added, 2 removed, and nothing outside the
  governed keys** — 12 row changes for 12 findings collected, one-to-one. That
  is the S6.4 invariant holding in the field, not just in its tests.

**`adopted_invalid`** (read as S6.3 defines it under `--fix`, not as the S5.5
number): 36 of 74. It still tracks the refusals — 14 of the 17
`no_improvement` sessions ended on rows their own gate rejected, against 1 of
the 15 `new_class` — so `no_improvement` remains "the session ran out of room
still failing its own check" while `new_class` is a session that satisfied
itself and paid for it elsewhere.

**Cost.** 584 LLM calls, **6.94 M tokens** (4.75 M input / 0.47 M output /
1.72 M thought), **18.3 h** of summed per-canto elapsed (inferno 6.0 /
purgatorio 9.7 / paradiso 2.6). 75 `api_retries` absorbing 2,799 s of 429
backoff, 4 max-length retries, 0 paced seconds. The 50 cantos with no finding
cost no model call.

**Gold agreement, opened afterwards and cited as nothing else** (§5 discipline
4): corpus-wide **0.7372 → 0.7382** (P 0.7136 → 0.7146, R 0.7624 → 0.7633;
+39 true positives on −2 rows); inferno 0.7437 → 0.7444, purgatorio
0.7343 → 0.7356, paradiso 0.7334 → 0.7343. A tenth of S6.3's move, on a tenth
of the findings.

**State at close.** Corpus **0 hard / 4,660 soft**, 32 TSVs modified in the
working tree and uncommitted; suite **960**, unchanged and not re-run — no code
moved. The per-canto logs now carry both fix runs; everything above is read out
of them, and S6.3's record is read out of the same files, so `make clean-log`
discards only what the two records already carry.

**What this says about level 1.** 32 units and 36 findings are refused twice
over, by two independent sets of sessions, and the second pass gained 46 mostly
by re-rolling the first pass's dice rather than by the new mechanism. A third
`--fix 1` run would likely gain again and by less; that is a convergence curve,
not progress.

**And the residue is a fact about the mechanism, not a worklist.** The
temptation a twice-refused position invites is to settle it by hand — read it,
argue its outcome from the contract, and write the row. That is precisely the
frontier-LLM/human triage loop of Phases 5–8 that `../PLAN.md` §1 says this
harness exists to replace, and being deterministic and contract-derived does not
rescue it: the point of the autonomy premise is that the *model* reaches the
position, so a repair we apply on its behalf measures nothing.

**But "the agent cannot reach it" is the wrong conclusion** (operator's
correction on this record: *if an assistant session can settle these, the agent
can in principle be made to*). That is the right way round, and it makes what an
assistant could do here a **specification for the mechanism**. Decomposed
against this run's own logs:

| what a frontier session has here | transferable? | evidence in S6.5 |
|---|---|---|
| **the derived answer** (`check.py` prints `'obl' vs 'obl:di'`) | **no** — S6.2 keeps it out of the session by design, a test asserts its absence; crossing it makes the run a transcription of `derive_unit` | — |
| **a one-row question** instead of a whole-unit re-answer | yes | 15 `new_class` refusals, only **1** `adopted_invalid`: the level's job was done and something else broke. S6.4 rescues this after the fact, 9 of 41 |
| **not stopping while its own gate says invalid** | yes | 17 `no_improvement`, **14** `adopted_invalid` but only **5** at the 12-turn ceiling — sessions stop early, so the lever is the stopping rule, not the budget |
| **the corpus-wide view of all 37 at once** | yes | a session sees one unit; feeding the level's own settled cases into the notice opens no gold and shows no derived label |

So the untried mechanism change is to make the **ask** row-scoped, not just the
acceptance — S6.4 narrowed the second and left the first alone — and to revisit
why a session ends on rows it has itself judged invalid. Reading the 37 is
admissible as design input under §5 discipline 5 on exactly that footing, and
whatever comes of it, the corpus edit still comes from a session.

**A correction this table forces**: the first draft of this record described
`no_improvement` as the session "running out of room". The turn counts above do
not support that for 12 of the 17.

### S6.6 — Two levers from S6.5's table: the invalid-final resume, and the acceptance rule told to the session (2026-09-01)

S6.5 ended by decomposing what an assistant session has at these positions into
one thing that may not cross and three that may. This record ships the two that
are cheapest and least speculative. **Code only; the corpus is untouched and
running anything over it stays the operator's act.**

**Why the session stops early — the actual mechanism, not an inference.**
`run_unit`'s loop ends as soon as the model gives a prose answer after *any*
successful `validate_candidate` dispatch (`agent.py`: "worked through
validation; prose ending is legitimate"). Nothing checks the verdict of that
last submission, and `candidate_rows` takes the last submission *whatever* its
verdict. So a session can end on rows its own gate called invalid, with turns
unspent, and those rows go to the artifact. Measured across both fix runs:
**77 units ended `adopted_invalid` with budget left** (S6.5: 20 of 74; S6.3: 57
of 337).

**That behaviour is deliberate, and it stays the default.** The module docstring
is explicit — "giving up after failed validations is a capability failure the
benchmark must measure, so it is never nudged", with
`test_giving_up_after_failed_validation_is_never_nudged` guarding it. The
resolution is not to overrule it but to separate the two jobs:

| | measuring a session | producing corpus |
|---|---|---|
| caller | `benchmark.py`, `agent.py --…` | `reconstruct.py` |
| `max_invalid_nudges` | **0** (`MAX_INVALID_NUDGES`) | **1** (CLI default) |
| rationale | the give-up *is* the measurement | the give-up ships to the artifact |

**Lever 1 — the invalid-final resume.** Where switched on, a session that ends
with turns remaining on a submission its own gate rejected is resumed once with
`INVALID_NUDGE_MESSAGE`, which names only its own situation: your last
validation reported invalid, that is the candidate that will be kept, turns
remain, re-read *the errors that call returned* and resubmit — and, explicitly,
"if you conclude the errors are wrong about this unit, say so and submit the
rows you stand behind." It carries no derived label and no invariant the model's
own tool has not already told it. Counted separately as `result.invalid_nudges`
(trace record and CLI summary), so it can never be confused with the no-call
nudge, and announced as its own pass boundary on a watched run.

**Lever 2 — the session is told how its answer will be judged.** S6.5's sharpest
number is that of the 15 `new_class` refusals only **1** was `adopted_invalid`:
those sessions satisfied their own gate and were then refused for a class they
introduced elsewhere — a rule they were never told. `revision_block` now states
`fix_verdict` in the session's own words: the answer replaces the record only if
it breaks no schema rule, settles the points listed, and raises no *kind* of
problem the unit did not already have; and if it settles the points but brings a
different kind, only the rows the points name are taken (S6.4's splice). This is
the acceptance contract, not the answer — the test that asserts `derive_unit`'s
label never appears in the block still passes, and a new test pins both halves.

**Why not the row-scoped ask** (S6.5's own first suggestion): narrowing the ask
to "change only these rows" would also suppress the off-brief gains S6.3
measured on accepted units — 87 relabels beyond the level, and the
`purgatorio 21:87` predicate registration §2 calls a strict improvement. Telling
the session the rule instead is strictly more information and narrows nothing,
so it is the version that ships. The row-scoped ask stays open, and is now an
experiment with a control rather than a guess.

**What this does not claim.** Both levers are prompt- and loop-side, gold-closed,
and **unmeasured** — no run has been made. Their effect is a live-run question
and the run is the operator's. Neither touches the level table, the classes, or
the corpus; a `--fix 1` re-run under them is the experiment, and S6.5's caution
applies to reading it: a third pass would gain something by re-rolling alone, so
the comparison worth making is the *refusal mix* (`no_improvement` /
`new_class` / `adopted_invalid`), not the finding count.

Suite **960 → 969**. `harness/recon/` untouched: corpus still **0 hard / 4,660
soft**.

### S6.7 — The `--fix 1` run under S6.6's two levers: 12 of 37 cleared, and the refusal mix moved the wrong way (2026-09-02)

The operator's run of level 1 over all 100 cantos on the S6.6 loop and prompt,
read out here. **The corpus moved; no code did.** S6.6 said in advance that the
finding count could not judge these levers — a fresh pass gains by re-rolling
alone — so the readout below leads with the refusal mix and treats the delta as
context.

**The numbers, against S6.5's close (`2fd689f`):**

| | before | after |
|---|---:|---:|
| hard violations | 0 | **0** |
| soft violations | 4,706 → 4,660 | **4,649** (−11) |
| level-1 findings (`make fix-level`) | 37 | **25** (−12, 32.4%) |
| cantos carrying a level-1 finding | 28 | 20 |
| TSVs modified | — | 9 |
| gold agreement (readout, §5 discipline 4) | 0.7382 | 0.7384 |

`make check` exits 0. **Per soft class the entire −11 is `role_mismatch`**
(242 → **231**); `extra_arg` 2,106, `missing_arg` 1,636, `missing_tuple` 488,
`membership` 143, `extra_tuple` 43, `dual_role` 2 are all unchanged to the unit.
As in S6.5 the level's own subset fell by one more than the class did, so one
non-level-1 `role_mismatch` appeared. Soft is not a distance (§2); the
near-coincidence is arithmetic.

**A housekeeping fact first.** The per-canto logs were swept before this run:
all 100 carry timestamps from 2026-09-01 06:36–15:36 UTC only, i.e. this run
alone, the first record starting one minute after S6.6's commit. S6.3's and
S6.5's telemetry is therefore gone from disk — the ephemerality §2 accepted,
and both records were read out of it in full before it went. Ten purgatorio logs
(01–10) carry **two** segments: the canticle stream was relaunched, and
purgatorio 1, 3 and 10 have `unit` records in the earlier segment that the later
one does not repeat. So S6.4's caution *did* bite this time, and in the opposite
direction to the one the handoff warned about — taking the last segment per
canto silently drops units. The numbers below dedupe `unit` records by
`(canticle, canto, line_start, line_end)` across the whole file, keeping the
last, which is the only rule that survives both shapes.

**The refusal mix — the headline.** 33 units reopened across 27 cantos:

| verdict | S6.5 (74 units) | S6.7 (33 units) | share |
|---|---:|---:|---:|
| `accepted` (whole unit) | 33 | **8** | 45% → 24% |
| `salvaged` (S6.4's splice) | 9 | **3** | 12% → 9% |
| `no_improvement` (reverted) | 17 | **7** | 23% → 21% |
| `new_class` (reverted) | 15 | **15** | 20% → **45%** |
| `hard` | 0 | **0** | — |

**`new_class` did not move at all.** Its absolute count is identical across the
two runs while the pool halved, so as a share of what is left it more than
doubled — and lever 2 was aimed at it directly. Telling the session the
acceptance rule in its own words bought nothing measurable. Worse for the
diagnosis S6.6 wrote: every one of the 15 is `missing_arg`
(13 `new_class:missing_arg`, 2 `new_class:extra_arg,missing_arg`), where S6.5's
were `extra_arg`-dominant — the shape S6.4's splice was built for. That is why
salvage collected 3 rather than 9: dropping an argument the re-answer brought is
recoverable by a row splice; **an argument the re-answer removed is not, when
the row the splice governs is the very row it moved.**

**Lever 1 fired and did not convert.** `invalid_nudges` (added in S6.6 precisely
so this would be visible) is 1 on **7** of the 33 units and 0 on the rest, and
**all 7 still ended `adopted_invalid`** — the resume happened, the session
re-submitted, and its own gate still said invalid. Against the target it was
built for:

| | S6.5 | S6.7 |
|---|---:|---:|
| `adopted_invalid` | 36 / 74 (49%) | **14 / 33 (42%)** |
| …with turns unspent | 20 (27%) | **6 (18%)** |
| …at the 12-turn ceiling | 16 | 8 |
| `no_improvement` reaching the ceiling | 5 / 17 | 2 / 7 |

So "ends early on rows its own gate rejected" fell from 27% to 18% of units, but
the resume is not why: it fired 7 times, converted 0, and the 7 it fired on are
counted in the 14. The honest reading is that lever 1 works mechanically and
changes no verdict, and that `adopted_invalid` is **not** the same story it was
in S6.5 — there it tracked the refusals (14 of 17 `no_improvement`), here **all
8 `accepted` units are `adopted_invalid`**: the answer that reduced the findings
was one its own gate rejected. `no_improvement` is no longer "ran out of room"
either — 5 of its 7 stopped short of the ceiling.

**Row-level** (the diff against `2fd689f`, 9 files): **19 rows removed, 19
added, net 0** — 14 relabels in place, 3 arguments relocated, 2 rows added, 2
removed. **11 of the 14 relabels are the level's own** (`obl` → `obl:di` 7,
`obl:in` 3, `obl:a` 1), plus one level-1 position settled by dropping the
oblique reading entirely (`purgatorio 1:80` `obl` → `attr`) — 12 findings
cleared, one row each. The 2 off-brief relabels are `obl:sanza` → `obl:senza`
and `obj` → `obl`. Attributed by verdict:

- `salvaged` units (3): **exactly one row change each, nothing outside the
  governed keys** — inferno 32:113, purgatorio 1:80, purgatorio 22:120. The
  S6.4 invariant holds in the field for the second run running.
- `accepted` units (8): the other 16 row changes, including every relocation,
  both additions and both removals — the whole-unit replacement still reaches
  past its brief, as in S6.3 and S6.5.

**Cost.** 323 LLM calls, **4.00 M tokens** (2.77 M input / 0.27 M output /
0.97 M thought), **10.4 h** of summed per-canto elapsed (inferno 3.5 /
purgatorio 5.8 / paradiso 1.1). 57 `api_retries`, 0 max-length retries, 0 paced
seconds. The 73 cantos with no finding cost no model call.

**Gold agreement, opened afterwards and cited as nothing else** (§5 discipline
4): corpus-wide **0.7382 → 0.7384**; inferno 0.7444 → 0.7447, purgatorio
0.7356 → 0.7360, paradiso 0.7343 → 0.7343. Flat, as a 12-row change should be.

**What this settles about the three levers S6.5 named.** Two are now measured
and neither is the bottleneck: the stopping rule fires and changes no verdict,
and stating the acceptance contract leaves `new_class` exactly where it was. The
**row-scoped ask** is the one still untried, and this run sharpens the case for
it rather than weakening it — the refusals are now overwhelmingly "the re-answer
dropped an argument elsewhere in the unit", which is precisely what a whole-unit
re-answer risks and a row-scoped one cannot. S6.6's objection to it (narrowing
the ask suppresses the off-brief gains S6.3 measured) is now priced: this run's
off-brief yield was **2 relabels, 2 rows added, 2 removed and 3 relocations** on
8 accepted units, against 12 findings cleared. That is a much smaller thing to
protect than S6.3's 87.

**And a mechanism gap this record should not repeat.** Why an answer earned
`new_class:missing_arg` — which argument it dropped, and whether the drop sits
on the row the finding names — is *not in the logs*: `fix` carries only `level`
and `verdict`. That is S6.4's mistake in a new place (S6.6 fixed it for
`invalid_nudges` and not for this). Before any run is made on the row-scoped
ask, the refused candidate's own rows, or a diff of them against the record,
should be logged — otherwise the same question will be unanswerable a third
time.

**State at close.** Corpus **0 hard / 4,649 soft**, 9 TSVs modified in the
working tree and uncommitted; suite **969**, unchanged and not re-run — no code
moved. **Level 1 has now been run three times.** 377 → 83 → 37 → 25, with the
third pass gaining 12 where the second gained 46; 25 findings across
20 cantos have been refused by three independent sets of sessions. The
convergence curve S6.5 called is confirmed, and a fourth run of the same
mechanism is not the next move.

### S6.8 — The refusal, on record: why an answer was refused, not just that it was (2026-09-02)

S6.7's closing item, shipped. **Code only; the corpus is untouched and running
anything over it stays the operator's act.** Three runs of level 1 have now
reported *that* an answer introduced a class the unit did not carry, and none of
them could say **which row it came from**. That single missing fact is what
separates the two live hypotheses — the ask is too wide (the answer broke
something beside the level's own row) versus the model is wrong at the position
itself — and it is the hypothesis the untried row-scoped ask is aimed at. The
next run cannot decide it without this, and S6.6 had already learned the lesson
in the neighbouring case: `invalid_nudges` was added *before* the run that
measured it, precisely so the run would be readable.

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

Two smaller additions beside it. `record["fix"]["delta"]` now carries
`row_delta` **per unit and under every verdict** (zeros on a reverted one), so an
accepted unit's off-brief reach — the thing S6.3 measured at 87 relabels and
S6.7 at 2 — is readable from the log instead of from a `git diff` against the
right commit. And the `unit` record carries `final_validation_errors`: the gate
errors on the submission the session handed downstream, read off the same last
`validate_candidate` dispatch `final_submission_valid` reads its verdict from, so
the two can never describe different submissions. S6.7's second finding needs
it — all 8 of its accepted units were `adopted_invalid`, i.e. the answers that
cleared findings were answers the session's own gate rejected, and nothing on
record says what it was rejecting them over.

The watched-run console line gains the same in one clause —
`new_class:missing_arg [answer: ~1 +0 -1; 1 introduced, 0 on named rows]` — so
the pattern is visible while the run is happening, not only in the readout.

**What this does not do.** Nothing here reaches a session: the diagnosis is
computed after `fix_verdict` has already decided, it is written to the log and
nowhere else, and it changes no verdict, no acceptance rule, and no notice. The
derived label stays out of the session exactly as before, and the tests that
assert its absence are untouched. Suite **969 → 971**; `harness/recon/` untouched
at **0 hard / 4,649 soft**.

**The run this is for.** A `--fix 1` re-run under it, with the per-canto logs
deliberately swept first (the operator's call, and the right one — S6.7 had to
reconstruct which run a log belonged to from timestamps). Read it out as **S6.9**,
and read `introduced[].governed` first: if the classes the answers introduce sit
mostly *off* the named rows, the row-scoped ask is the mechanism to build next
and this run is its baseline; if they sit *on* them, the ask's scope is not the
problem and the level's own premise at those positions is what needs arguing.

### S6.9 — The `--fix 1` run under S6.8's logging: 11 of 25 cleared, and level 1's own premise fails at the survivors (2026-09-02)

The operator's fourth level-1 run over all 100 cantos, on the S6.8 logging and
with the per-canto logs deliberately swept first. **The corpus moved; no code
did.** S6.8 set the reading order in advance and named the question the run
exists to answer, so this record follows it: `introduced[].governed` first, the
finding count as context.

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

Salvage collected nothing at all: the splice ran on all 12 refused units and
`fix_verdict` refused every candidate — 7 still `new_class:missing_arg`, 5
`no_improvement`. S6.7 predicted exactly this and the diagnosis now proves the
mechanism rather than inferring it (below).

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

**Not one refused answer ever relabelled a row the level named.** Every refused
unit either dropped that row entirely — 10 of them, which is precisely the
`missing_arg` it is then refused for — or left it exactly as it found it (4, the
`no_improvement` units). That is why the splice cannot help: S6.4 splices *the
answer's rows at the governed keys*, and at those keys the answer has no row.

Read against S6.8's stated rule, the verdict is unambiguous: the introduced
classes sit **on** the named rows, not beside them. **The row-scoped ask is not
the mechanism this evidence calls for** — narrowing the brief to the row the
level names cannot help when the row the level names is the one the session
declines to write. What needs arguing is the level's own premise at those
positions.

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
unit; every answer that cleared findings but one was an answer its own gate
rejected. The two gates are pulling in opposite directions, and the level is the
thing between them.

**Why, read as positions and not as aggregates** (§5 discipline 5). All 14
surviving findings sit in the 12 refused units — the accepted units cleared
every finding they were given. Taking each survivor's argument and applying the
gate's own test:

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

`harness/runner/tools.py:requires_nominal_anchor` carries none of that. It
admits an L3 NP head or a pronoun and nothing else, where `validate.py` also
passes predicate positions, adverbial obliques, dep-argument positions (rule
AF), aux heads (AQ), coordination heads (DG) and marker slots (DS). **The
session's gate is strictly narrower than the layer's own contract, and the
survivors sit in the gap.** At those 12 positions the row level 1 asks for is
one the corpus contract permits and the session's own gate forbids, so the model
has exactly two moves: drop the row (`new_class:missing_arg`, 10 of them) or
override its gate and submit anyway (`adopted_invalid`, which is how the 9
accepted units cleared their findings). Three independent sets of sessions have
now produced both, and neither is a model error.

The remaining 2 survivors are ordinary: `purgatorio 30` (`sogno`) and
`paradiso 6` (`anni`) are nouns with an NP head, nothing blocks the row, and
both units came back `no_improvement` — the session simply did not change them.

**Row-level** (the diff against `7edf773`, 10 files): **20 rows added, 17
removed, net +3**, every one of them from an `accepted` unit — `fix.delta` is
zero on all 12 refused units, so the reverts are clean and no salvage happened.
14 relabels in place, of which **12 are the level's own shape** (`obl` →
`obl:in` 5, `obl:di` 4, `obl:a` 2, `obl:da` 1) against 11 findings cleared, and
2 off-brief (`obl:di` → `obl` at paradiso 10:30, `obj` → `subj` at
inferno 34:90). Beside them 6 rows added and 3 removed, three of the additions
pairing with the removals as subject relocations. The level's relabels
outnumbering the findings it cleared is the non-distance property of the counter
again (§2), not an accounting error.

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
levers are now measured, and none of them is the bottleneck — the stopping rule
fires and converts nothing, stating the acceptance rule moved `new_class` not at
all, and the row-scoped ask is ruled out by its own intended evidence. The
bottleneck is a **contract seam inside `harness/`**, not the ask, the loop, or
the model: `requires_nominal_anchor` is a transcription of `validate.py`'s anchor
rule that kept the NP-head/pronoun clause and dropped every exemption beside it,
so the agent-side gate and the corpus-side checker disagree about which rows are
writable. Two ways out, and they are §2's outcomes 1 and 2 wearing different
clothes:

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
