# Stage 5: Corpus Durability

Stage-5 home document: opening scope, design work as it happens, and the
stage's milestone ledger as records accrue. [`PLAN.md`](PLAN.md) keeps
status and the handoff; detail lives here, not there — this stage writes
directly into this file as work happens, rather than accumulating in
PLAN.md and splitting off at close (the pattern Stages 1–4 used).

**Status**: OPENED 2026-08-29 (operator decision, on Stage 4's close).
Deliverable 1 shipped on record S5.1 (`harness/recon/convert.py`);
deliverable 2 was **cut** on the same day (§2, operator decision). The
script, the TSV-goaled Makefile, and all 100 generated TSVs are committed.
Record S5.2 (same day) added a `--check`/`--stats` port
(`harness/recon/check.py`) and read out the committed corpus's divergence
from gold; §4 opens a new direction on the strength of that readout — Stage
5 continues as a divergence-reduction effort over the recon TSVs, informed
by (but not repeating) [`../skel/PHASE5.md`](../skel/PHASE5.md)'s
deterministic-rule methodology. Record S5.3 is the first reduction pass:
two deterministic rules (`harness/recon/repair.py`) taking the corpus from
**897 to 70 hard** violations, gated on gold agreement rather than on the
violation count — §5 records why that distinction is the load-bearing one.
Record S5.4 audits the classification behind the residual 70 before the
clausal design pass opens ([`HARD.md`](HARD.md)); no artifact changed.
Record S5.5 then relocates the whole question: the corpus's 897 hard
violations decompose **exactly** into the three checks `validate_candidate`
was missing, so the checks moved into the agent's own session (the model
corrects its analysis instead of a rule correcting it afterwards), the
gold-format TSV became the run's artifact *and* its resume state — written
unit by unit, with deleting a stretch's lines as the fix gesture — and the
log dropped to an append-only debug record.

---

## 1. What this stage does

`harness/recon/<canticle>/NN.log` — the 100 per-canto JSONL logs from the
Stage-4 corpus run — are gitignored and disk-only, unlike the regenerable
Stage-1/2 mining logs (`harness/bench-*.log`; those hold deterministic
agent traces that `mine_artifacts()` can re-derive from scratch, so losing
them costs a re-run, not the data itself). Nothing regenerates the Stage-4
logs: they hold live LLM output that was never designed to survive past its
own corpus-wide readout ([`STAGE4.md`](STAGE4.md) record S4.3). Left as-is,
they will eventually be lost (gitignored, no backup policy, disk-only).

Opening scope, two deliverables:

1. A conversion script that turns each log's settled reconstruction output
   into `skel/`-compatible, committable form — durable storage for the
   actual predicate-argument frames the Stage-4 run produced, alongside the
   existing gold `skel/` corpus (not replacing it — `skel/` stays the
   immutable evaluation reference; see [`PLAN.md`](PLAN.md) §4 item 1).
2. ~~A separate format, design TBD, for whatever the logs carry that doesn't
   map into that skel-compatible shape~~ — **cut 2026-08-29**; §2 records
   why.

## 2. Design decisions (2026-08-29, operator)

The three questions §1 left open, and the answers the implementation is
built on:

- **Output location and shape** — one skel-format TSV per canto, written
  **beside its own log**: `harness/recon/<canticle>/NN.tsv`. Not a separate
  artifact tree and not an aggregate per canticle: the log layout already
  is the corpus layout, `.gitignore` covers only `*.log`, so the TSVs land
  as committable files with no gitignore surgery, and each stays
  canto-atomic like its source. The format is gold's byte-for-byte
  (`reconstruct.render_tsv`, the writer-parity mirror of
  `skel.io.write_skel`), so `diff harness/recon/inferno/01.tsv
  skel/inferno/01.tsv` *is* the run's divergence readout.
- **Non-mappable content — not committed at all.** Deliverable 2 was first
  implemented as a per-canto `NN.meta.json` sidecar carrying the unit
  records' routing, gate verdicts, violation detail, per-unit gold scores,
  `canto_complete`/`summary`, and a roll-up of the `llm_request`/
  `llm_response` pairs. The operator cut it on review: **this is run
  telemetry, not corpus content, and telemetry does not belong in the
  repository.** The generated sidecars (100 files, ≈5.2 MB against the
  TSVs' ≈1.2 MB) were deleted unread into git. What Stage 5 makes durable
  is therefore the *corpus* the run produced, not the run itself; the
  telemetry stays in the logs, readable by
  [`readout.py`](recon/readout.py) for as long as they exist, and is
  accepted as ephemeral.
- **One-time or repeatable** — repeatable and idempotent. Regeneration from
  unchanged logs reproduces byte-identical files (unchanged files are not
  even rewritten), so the same command refreshes the artifacts after any
  future corpus run; `--check` regenerates in memory only and exits non-zero
  on drift.

**Carry-over**: with deliverable 2 cut, nothing preserves the Stage-4 run's
cost accounting (10,581 backend calls, 60.8 M provider tokens, 164.4 h of
LLM time) or its per-unit routing and gate detail once the logs go. That is
now a deliberate acceptance rather than an oversight — but the closing
numbers for the record live in [`STAGE4.md`](STAGE4.md) S4.3 and in S5.1
below, so the headline accounting survives in prose even if the logs do not.

## 3. The conversion contract (`harness/recon/convert.py`)

    cd harness/recon && make inferno        # per canto: log -> NN.tsv
    cd harness/recon && make convert        # every existing log -> its TSV
    cd harness/recon && make convert-check  # drift check, writes nothing

    uv run python -m harness.recon.convert [--root DIR] [--canticle C]
                                           [--canto N] [--check]

**The driver's goal is the TSV, not the log** (`recon/Makefile`, reworked
with this record). `make <canticle>` now builds `<canticle>/NN.tsv` per
canto: reconstruct writes the log, then the conversion turns it into the
committed artifact — the log is the intermediate, the TSV is the output.
`%.log` is deliberately *not* a make prerequisite of `%.tsv`; it is
FORCE-driven and would relaunch reconstruct on a canto whose TSV is already
on disk. Instead the TSV rule guards first: **a canto whose TSV exists and
whose log is gone is left alone** — the normal state of a fresh checkout,
where the gitignored logs are absent and re-running would cost another
164-hour corpus for output already committed. Deleting a TSV is how you ask
for that canto again. When the log *is* present the rule recurses into it,
so the log's own resume/skip logic stays the single source of truth for
whether the model runs at all.

Deterministic and LLM-free — it reads the logs plus the frozen L1–L4
layers, never launches `reconstruct.py`, and never writes under `skel/`.

**What is converted.** Only the `unit` records: each carries the accepted
`row_keys` for its `(line_start, line_end)` span, and their union across the
canto is the reconstruction. Every other record kind in the log
(`gold`, `canto_complete`, `summary`, `llm_request`, `llm_response`) is
telemetry and contributes no rows — pinned by a test.

**Words are recomputed, not trusted.** Row keys are re-anchored on the
Layer-1 token stream through the same `reconstruct.build_rows` the run
itself used, so the `word` column comes from the frozen corpus rather than
the log, and a key that no longer indexes the token stream is reported on
the console instead of silently landing.

**Degradation is visible, never silent.** A missing log is skipped and
counted; a log with no `summary` record still converts but is flagged
`INCOMPLETE` in the console report; a resumed canto's duplicate `unit`
record for the same span is superseded by the later one. Progress streams
one line per canto on stderr, per PLAN.md §4 item 5.

## 4. Reducing recon divergence (opened 2026-08-29, operator)

S5.2's readout put the committed recon corpus at **897 hard, 5,267 soft**
violations against the same `validate_unit`/`derive_unit` check gold is
held to — measured, not estimated, by `harness/recon/check.py` over all 100
committed TSVs (§3 below records the run). The soft count sits at roughly
the same order of magnitude as `skel/`'s own starting point before Phase 5's
reduction work began (**5,919**, [`PHASE5.md`](../skel/PHASE5.md) §2 opening
figure) — a coincidence of scale, not of composition: the recon corpus was
produced by an autonomous agent reasoning from first principles (PLAN.md
§1), not the semi-manual small-model-on-rails process Phase 5 was cleaning
up after, so the violation mix need not match.

Operator decision: Stage 5's scope now extends to **reducing this
divergence**, using Phase 5 (and its Phase 6 successor) as a reference for
*method*, not a script to replay — deterministic, zero-LLM-cost checker/rule
work first, per-position reads before aggregate re-classification, and
brute-force whole-unit regeneration treated as a last resort given Phase 5's
measured flat yield (§1.1 there). What actually transfers, and what Rules
A–EI (if any) still apply unmodified to `harness/recon/`'s output, is
determined by reading the recon violations themselves — not assumed from
the gold-side ledger. §5 is the first implementation of that direction.

## 5. What the violation count is, and what gold is not (2026-08-29)

Two operator interventions shaped this section, and both are corrections to
how the reduction work was first framed. They are recorded together because
they pull in opposite directions and the resolution is the method.

**First: is `hard` a trustworthy criterion?** As a *quality* measure, no.

- **It is calibrated.** Pointing the same checker at gold
  (`uv run python -m harness.recon.check --root skel`) reports **0 hard, 0
  soft** across all 100 cantos. Passing it is a genuine necessary condition,
  not an arbitrary bar.
- **It is also gameable.** Every hard class is a property of the artifact
  alone, and all of them are cleared by *deleting rows*. Optimizing the
  counter rewards deletion, which would shrink the corpus toward vacuity
  while the number improved.

**Second: gold is the benchmark, not the target.** The first response to
that gameability was to make row-level agreement with gold the gate that
decides whether a rule ships. The operator rejected it, correctly: fitting
repair rules to gold is teaching to the test. It destroys the meaning of
every gold-referenced number `harness/` reports (Stage 1's micro F1,
S4.3's verify-gold readout, `agree.py`'s own score), and it reinstates
exactly the top-down methodology `harness/` exists to replace — a larger
intelligence reading the answers and laying rails for the pipeline to run on
(PLAN.md §1). Gold stays the immutable evaluation reference of §4 item 1,
and "immutable" has to mean *unconsulted during construction*, not merely
unwritten.

**The resolution — where a repair rule's authority comes from.** Not from
the violation counter (gameable) and not from gold (off limits), but from
the layer's own published contract: `dante_corpus/skel/validate.py`'s schema
invariants and `derive.py`'s derivation, the same L1–L4-driven machinery
that produces the violations in the first place. A rule is admissible when
the schema declares the current row impossible *and* the contract determines
what may stand in its place; where the contract is silent, the conservative
move is to withdraw the void assertion rather than invent one, and where a
derivable alternative exists, deletion is the wrong repair. Gold agreement
is then read *afterwards*, as a readout of where the gold-free work landed.

This is a real constraint, not a formality: it is why the clausal class
below is deferred rather than repaired, even though its gold reading is
obvious.

**Honest caveat on S5.3's own two rules.** They satisfy the standard —
both are re-derivable from `validate.py` alone, and `repair.py` opens no
gold file. But gold *was* consulted while they were being designed, before
the operator's second intervention. The agreement gain they show therefore
cannot be claimed as fully independent evidence that schema-driven repair
converges on gold; that claim has to be earned by the next rule, designed
gold-closed from the start.

`agree.py` is operator-side, like `benchmark.py`: it reads gold, so nothing
under `runner/` may import it (PLAN.md §4 item 1). It is read-only and
writes nothing anywhere.

### The hard 897, read position-by-position

The count decomposes exactly into four classes:

| class | count | what the agent did |
| --- | ---: | --- |
| `[dup] argument cites its own predicate` | 486 | gave an enclitic pronoun its own argument row pointing at the host verb token (`aiutami`, `trarrotti`, `venendomi`) |
| `[position] role 'X' may not use (0,0)` | 341 | used the null position for an elided non-subject (323 `obj`, 12 `iobj`, 6 others) |
| `[clausal] xcomp argument is not a predicate` | 57 | labelled a predicative adjective/participle `xcomp` |
| `[clausal] ccomp argument is not a predicate` | 13 | same, with `ccomp` |

The first two are void by schema, read position-by-position rather than in
the aggregate:

- `inferno 1:89` recon `89 1 aiutami obj 89 1` — the enclitic `-mi` is
  inside the verb token, so the row makes the predicate its own object.
  `validate.py`'s `arg == pos` test rejects it outright, and L1–L4 offer no
  other position to cite: the clitic's referent is a resolution decision,
  not a lookup. Same shape at `1:59`, `1:67`, `1:83`, `1:111`, `1:114`.
- `inferno 2:6` recon `6 2 ritrarrà obj 0 0` — the null position is the
  schema's notation for an unexpressed *subject* and is defined for no other
  role; an elided object simply has no position to name. The class is
  uniform: 323 `obj`, 12 `iobj`, 6 others, matching the violation total
  exactly.

In both classes the row asserts something the schema forbids while the
frozen layers determine no replacement, so withdrawing the assertion is the
only repair that does not fabricate one.

The clausal class is deliberately left alone, and it is the case that shows
the standard has teeth. Recon has `15 7 fanno xcomp 15 6` at `inferno
10:15`: `xcomp` requires its argument to be a predicate in the unit, and
`15 6` is not registered as one. Unlike the first two classes there *is* a
derivable alternative — the L4 tree and the role vocabulary both admit
treating the predicative participle as a predicate in its own right and
relabelling the host's relation accordingly — so deleting the row would
destroy recoverable structure, and the repair has to say which predicate
gets registered with which subject. Deriving that from L2/L4 is a design
pass of its own, so the class waits for its own record. (Gold's reading of
these positions is not the input to that design: this section deliberately
does not quote it.)

Before that design pass was opened, the *classification* producing those 70
was itself audited — what the invariant asserts, where its authority comes
from, whether `hard` is the consistent severity, and whether any of the 70
is a checker misfire: [`HARD.md`](HARD.md) (2026-08-30, evidence record
only; no rule designed, no artifact edited, every figure derived with gold
unopened). It holds — the invariant is `derive.py`'s own promotion-then-cite
closure restated as an admission condition — and it also names what the
design pass inherits: 59 of the 70 have a derivable registration
alternative, 43 cite an adjective where re-notating as `attr` is the second
admissible option, and 11 need individual reading because L4 asserts a
non-clausal relation there.

### The repair (`harness/recon/repair.py`)

    cd harness/recon && make repair        # apply both rules, in place
    cd harness/recon && make repair-check  # non-zero exit if any row remains
    cd harness/recon && make agree         # readout only: P/R/F1 against gold

    uv run python -m harness.recon.repair [--root DIR] [--canticle C]
                                          [--canto N] [--check]

Two rules, both deletions, both idempotent:

- `self_arg` — drop a role-bearing row whose `(arg_line, arg_token)` equals
  its own predicate's `(line, token)`.
- `null_nonsubj` — drop a role-bearing row whose role is not `subj` and
  whose argument position is `(0,0)`. Role-less rows — the schema's way of
  registering a predicate that takes no arguments — are never touched.

**Written in place** (operator decision): the repairs edit
`harness/recon/<canticle>/NN.tsv` directly, so the git history carries the
"raw model output → rules applied" diff rather than splitting the corpus
into two committed trees. The consequence is an ordering constraint —
**repair runs after convert, never before**; re-running `make convert`
regenerates from the logs and rolls the repairs back. The per-canto `%.tsv`
make goal is deliberately left as convert-only rather than chaining repair
into it, so `make <canticle>` and `make convert` cannot disagree about what
a TSV contains.

### The readout

| | hard | soft | rows | P | R | F1 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| before | 897 | 5,267 | 43,531 | 0.6949 | 0.7545 | 0.7235 |
| after | **70** | **4,988** | 42,704 | **0.7083** | 0.7545 | **0.7307** |

827 rows removed — 486 `self_arg` + 341 `null_nonsubj`. The residual 70 hard
are exactly the clausal class (58 `xcomp` + 12 `ccomp`; the split shifts by
one from the pre-repair 57/13 because removing rows changes which positions
count as registered predicates).

The agreement columns are the readout, taken after the fact: **not one of
the 827 removed rows exists in gold**, true positives hold at 30,249, and
recall is unchanged to four decimals, so the entire effect is precision. As
§5's caveat records, gold was consulted while these two rules were being
designed, so this is a consistency check rather than independent evidence —
but it does establish the shape of the claim a properly gold-closed rule
should be able to make.

Five predicates lost every row they had (`purgatorio 22:44.5`,
`paradiso 3:63.3`, `paradiso 6:27.7`, `paradiso 24:120.5`,
`paradiso 28:33.3`) — reported by the tool rather than discovered later.
The `missing_tuple` soft count is unchanged at 501, so the derivation does
not require those predicates to be registered; whether a repair should
nevertheless leave a role-less row behind is a question for the contract
(`derive.py`'s predicate registration), and is deliberately left open rather
than settled by looking at what gold happens to write there.

---

## Milestone Ledger (Stage 5)

### S5.1 — Log-to-TSV conversion shipped; 100 cantos converted (2026-08-29)

`harness/recon/convert.py` (+ `make convert` / `make convert-check`,
`tests/test_harness_recon_convert.py`), answering §2's questions.
Converted the full Stage-4 corpus in one pass — **100 cantos, 3,477 units,
43,549 rows** into 100 gold-format TSVs (≈1.2 MB):

- **0 incomplete logs** and **0 dropped row keys** corpus-wide: every log
  ends with its summary record, and every accepted row key still indexes
  the Layer-1 token stream, so nothing was lost or silently repaired on the
  way out of the logs.
- Idempotence verified live: a second full pass rewrote nothing, and
  `make convert-check` reports "artifacts up to date" with exit 0.

**Scope change mid-record**: the run's telemetry was first shipped as
per-canto `NN.meta.json` sidecars and then cut by the operator (§2) —
sidecar generation removed from the script, the 100 generated files deleted,
tests rewritten. The TSVs were byte-identical before and after the cut
(`--check` clean across all 100), so the conversion of the corpus content
itself never changed. The headline cost accounting recovered from the logs
during that pass, kept here as the surviving record: **10,581 backend calls,
60,849,409 provider tokens, 591,957 s (164.4 h) of LLM time.**

**`recon/Makefile` reworked to make the TSV the per-canto goal** (§3): the
canticle targets build `NN.tsv` rather than `NN.log`, with the
present-TSV-and-no-log guard that keeps a fresh checkout from re-running the
corpus. Verified on the real tree without touching a model: both guard
branches, and a full `make paradiso` (33 cantos, every log complete →
skipped, every TSV reconverted unchanged) followed by a clean
`make convert-check`.

Test suite **876 → 887 passed** (11 new: TSV/gold shape parity, Layer-1 word
re-anchoring, telemetry records contributing no rows, out-of-range key
reporting, resumed-unit supersession, incomplete-log flagging, TSV as the
only file written, idempotence, drift detection and its non-zero exit).

No gold artifact is touched, and the script itself commits nothing — the
100 TSVs were committed separately by the operator on the same day, which
is where Stage 5's durability goal is actually met: the Stage-4
reconstruction now survives its logs.

### S5.2 — `--check`/`--stats` ported to the recon corpus; full-corpus divergence read out (2026-08-29)

The recon TSVs are byte-compatible with gold (S5.1), so gold's own
`skel/skel.py --check`/`--stats` validation applies to them unchanged —
only the artifact root differs. Rather than pointing `skel.py` itself at
`harness/recon/` (its driver scripts, `skel/driver_ui.py` included, stay
untouched per PLAN.md §3's directory boundaries), the path-selection gap
was closed one layer down, in the shared package the driver already calls
into:

- `dante_corpus/skel/io.py`'s `_artifact_path`/`has_skel`/`load_skel` gained
  an optional `base_dir` parameter (default `None` keeps every existing
  caller reading gold's own `SKEL_DIR`, byte-for-byte unchanged — pinned by
  a new test). This is the only change under `dante_corpus/`; nothing under
  `skel/` was touched.
- New `harness/recon/check.py` (+ `make check` / `make stats`,
  `tests/test_harness_recon_check.py`) reimplements `skel.py`'s `check()`/
  `stats()` loops against `base_dir=<recon root>`, calling
  `dante_corpus.{api,dep,morph,np,case,skel}` directly rather than
  `skel/driver_ui.py`'s private helpers — same result shape, no dependency
  on gold's driver package. `--check` prints per-position hard/soft detail
  and fails (exit 1) on any hard violation; `--stats` prints the
  by-kind/by-role soft-violation breakdown instead (mirroring `skel.py
  --stats`) and always exits 0 on soft-only findings.

**Full-corpus readout** (`make check` / `make stats` over all 100 committed
TSVs, no model call):

```
check complete: 897 hard, 5267 soft violation(s)
stats complete: 5267 soft violation(s) (897 hard)
```

Both commands agree on the totals, as they must — same per-canto
`check_canto` under the hood, `--stats` only changes how the results print.
§4 opens what Stage 5 does with this number.

Test suite **887 → 895 passed** (8 new: `base_dir` override + default-root
isolation; clean-gold-in reports zero; a corrupted word is a hard `word`
violation; a corrupted role is a soft-only `tag` violation;
`run`/`main --check` over a synthetic root; `main --stats` exits 0 on
soft-only findings; the by-kind stats breakdown finds the injected class).

### S5.3 — First divergence-reduction pass: 897 → 70 hard, gated on gold agreement (2026-08-29)

The first implementation of §4's direction, and the record that settles what
the divergence numbers are *for*. Full design, the position-by-position
reads behind each rule, and the readout table live in §5; the ledger entry:

- **Two operator interventions set the method** (§5). First: is `hard`
  trustworthy? Calibrated but gameable — gold scores 0/0 under the same
  checker, yet every hard class clears by deleting rows. Second, on the
  first answer's proposed fix: **gold may not be the gate.** Fitting rules
  to the evaluation reference is teaching to the test and reinstates the
  top-down methodology `harness/` exists to replace. A rule's authority
  comes from the layer's own contract (`validate.py` / `derive.py`); gold
  agreement is read afterwards as a readout.
- **`harness/recon/agree.py`** (+ `make agree`) — row-level P/R/F1 of the
  committed TSVs against gold. Measurement only, in the same family as
  `benchmark.py`'s micro F1 and `--verify-gold`.
- **`harness/recon/repair.py`** (+ `make repair` / `make repair-check`) —
  two deterministic rules for the hard classes `validate.py` declares
  impossible: `self_arg` (a row making a predicate its own argument — an
  enclitic pronoun) and `null_nonsubj` (a non-`subj` role at the null
  position, which the schema defines only for an unexpressed subject). Both
  repair by withdrawing the void assertion, because L1–L4 determine no
  replacement and inventing one would fabricate structure. LLM-free,
  idempotent, in-place, never reads or writes `skel/`.
- **Applied to the corpus**: 827 rows removed across 99 cantos, taking it
  from **897 hard / 5,267 soft to 70 hard / 4,988 soft**. Readout after the
  fact: gold agreement **F1 0.7235 → 0.7307** with recall unchanged at
  0.7545 — none of the 827 removed rows exists in gold, so the gain is pure
  precision and nothing true was thrown away. §5 records the caveat that
  gold was consulted while these two rules were designed, so the agreement
  is a consistency check rather than independent evidence.
- **The residual 70 hard are entirely the clausal class**, left for its own
  record for a methodological reason, not a practical one: unlike the two
  repaired classes it has a derivable alternative, so deletion would destroy
  recoverable structure and the right repair has to be derived from L2/L4
  rather than copied from the evaluation reference (§5). Their
  classification is audited in [`HARD.md`](HARD.md) (S5.4).

Test suite **895 → 916 passed** (21 new: per-rule classification incl. the
`subj` and role-less exemptions, emptied-predicate reporting, both
injected-divergence removals end-to-end, hard violations actually cleared,
idempotence, `--check` writes nothing / exits 1, missing-TSV skip; and for
the gate — gold against itself scores 1.0, a spurious row costs precision
but not recall and is healed exactly by the repair, a dropped gold row costs
recall, an empty root scores 0).

### S5.4 — The hard classification audited before the clausal design pass (2026-08-30)

No code and no artifact change: an evidence record, [`HARD.md`](HARD.md),
answering the question §5's discipline 1 makes load-bearing — the violation
counter selects the work, so **is the classification that produces the 70
sound?** Audited on the S5.3 tree (`6323d95`), gold-closed except for the
sanctioned 0/0 calibration, and re-verified end to end by an independent
second pass on 2026-08-30 (§7 there records what that pass corrected).

- **The invariant is the derivation's own closure property.** `derive.py`
  promotes every L4 clause-head deprel to a registered predicate *before*
  `_DIRECT_ROLE_MAP` emits the `xcomp`/`ccomp` citation, so a citation it
  emits always resolves. The hard check is that property restated as an
  admission condition on a committed artifact: it may not assert a citation
  whose referent it does not itself contain.
- **The severity is consistent with the contract's taxonomy.** The nominal
  membership check is soft *because* the contract publishes exceptions for
  it (rules AF/AQ/DG/DS); a clausal argument has exactly one realization, so
  an unresolved clausal citation has no reading at all. The `xcomp`-shaped
  soft tolerances (rules M/P/Q/R) are *scoring*-register findings and never
  admission permissions.
- **Zero checker misfires in the 70.** No cited position is registered as a
  predicate anywhere in the recon corpus — the unit-boundary false-positive
  hypothesis is ruled out corpus-wide, not just in-unit.
- **What the design pass inherits**: 59 rows one registration away from
  resolving, 43 of which cite an adjective where `attr` (the canonical
  equivalent that makes no registration claim) is a second admissible
  option; 11 whose L4 deprel is not clausal and which need individual
  reading. The choice between the two alternatives is decidable from L2/L4
  alone.
- **Documentation gap found**: [`../skel/README.md`](../skel/README.md)'s
  hard bullet still describes only predicate existence and argument-position
  validity; the `clausal` invariant it enforces is unpublished there.

### S5.5 — The hard checks move into the session; the TSV becomes the artifact and the resume state (2026-08-30)

S5.4 asked whether the hard classification was sound. Reading
[`runner/tools.py`](runner/tools.py)'s `validate_candidate` against
[`../dante_corpus/skel/validate.py`](../dante_corpus/skel/validate.py)
afterwards answered a larger question: **where the hard violations came from
in the first place.** The corpus's entire hard population is the gap between
the agent-side gate and the admission checker, exactly:

| hard kind (`validate.py`) | the gate | committed violations |
|---|---|---:|
| `word`, `position` (predicate range), `dup` (identical row), `sentinel` | implemented | 0 |
| `dup` — argument cites its own predicate (107) | **absent** | 486 |
| `position` — `(0,0)` is for `subj`/`""` only (109–111) | **absent** | 341 |
| `clausal` — `xcomp`/`ccomp` argument must be a registered predicate (115–121) | **exempted** | 70 |

486 + 341 + 70 = **897**, S5.2's readout to the row. There is no other source.
The `clausal` exemption was a conflation: clausal roles are rightly exempt
from the *nominal* NP-head/pronoun rule, but that exemption was written wide
enough to cover the *registration* duty, which is a different check. All
three missing checks are closed-world — they read the submitted rows against
themselves, needing no layer beyond L1 and no derivation.

So the repair moves upstream, and its shape changes with it. A post-hoc rule
would have to decide *on the model's behalf* which position to register —
the top-down rails [`PLAN.md`](PLAN.md) §1 says `harness/` exists to replace.
The gate instead reports the violation **to the model inside its own
session**, naming both admissible repairs (register the clause, or notate the
complement `attr`, which makes no clause-hood claim), and lets it fix its own
analysis with the unit's full context in hand.

**What shipped**

- **Three checks in `validate_candidate`**, each a transcription of its
  `validate.py` counterpart, with error text the model can act on. The
  set-scoped clausal one is gated on `GrammarToolkit(clausal_registration=)`,
  which `agent_fallback` sets from the workflow: whole-unit submissions get
  it, the per-predicate workflow (benchmark-only, one predicate per call)
  gets the two row-local checks alone. Deliberately **not** implemented by
  calling `validate_unit` and filtering: that runs `derive_unit`, whose soft
  findings are the derivation's own answer — feeding those back would hand
  the agent the rule-based solution and void the autonomy premise. Only the
  three schema checks cross into the session.
- **`runner/prompts.py` is unchanged.** Teaching the rule up front and
  reporting it after submission are two different levers; mixing them would
  confound the inferno-1 measurement. Only the tool spec and docstring were
  corrected, because they stated the exemption as blanket and that is now
  false.
- **`TsvArtifact` in `reconstruct.py` + `--tsv`**: the canto's gold-format
  TSV is written unit by unit as units settle, and read back on the next run
  as the resume state. Appending in unit order is byte-identical to a
  whole-canto `render_tsv` (units are line-ordered, contiguous, cover every
  line once, and an empty line still gets its sentinel row), so the streamed
  file is the same file the post-hoc conversion produced — pinned by a test
  that runs the CLI and compares against `recon.convert.convert_canto` over
  the same run's log. Line-number presence is the settled-unit test, which
  makes **deleting a stretch's lines** the fix gesture: that unit alone
  regenerates. A gap in the middle cannot be appended around, so the file is
  rewritten whole in line order whenever one exists, and a *partially*
  deleted unit is unsettled with its survivors dropped.
- **The log is demoted to an append-only debug record** — never read back.
  `prepare_resume`, `completed_cantos`, `compact_log` and their startup
  block are gone. Units resumed from the TSV are **re-validated** (free and
  deterministic) rather than trusting a prior attempt's logged verdict, and
  are folded into this run's aggregates as `route="tsv"`.
- **`adopted_invalid`** on every `unit` record. Adopting the last submission
  whatever its verdict was already the behavior (`UnitResult.candidate_rows`
  takes the last `validate_candidate` call, valid or not); what was missing
  was the record of it. `UnitResult.final_submission_valid` now carries the
  verdict through `HybridResult` into the log. The TSV is gold-format and
  cannot hold a flag, so this is where a provisional adoption at the turn cap
  is visible — and it is the experiment's primary metric.
- **`recon/Makefile`**: `%.tsv` runs reconstruct with `--tsv`; the separate
  `%.log` goal and the conversion step are gone. Completion is decided inside
  reconstruct by the artifact (a complete TSV settles every unit and costs no
  model calls), so make needs no completion predicate. `convert`/
  `convert-check` stay for the Stage-4 logs, with the new limit recorded:
  they cross-check byte-for-byte only for a canto produced in one
  uninterrupted run.

Test suite **916 → 925 passed**. No committed artifact changed: this record
ships the mechanism, and the inferno-1 experiment that measures it is the
operator's live run.

**What the experiment measures.** inferno 1 is the designated experiment
canto. Baseline is its existing committed TSV (Stage-4 output, in git);
after `rm inferno/01.tsv inferno/01.log && make inferno/01.tsv`, the
readout is `adopted_invalid` counts and per-unit turns against `make check`
— where the two row-local classes should be **0 by construction** and the
clausal count shows how much in-session correction actually buys — with
`make agree` read afterwards, never as a criterion (§5). `make repair-check`
on inferno 1 measures the same thing from the other side: S5.3 deleted 827
rows of two classes that should now be unreachable at the source.

### S5.6 — The inferno-1 live experiment: the gate holds, gold agreement does not move (2026-08-30)

The operator re-ran inferno 1 under S5.5's gate (`rm inferno/01.{tsv,log}`,
then `make inferno/01.tsv`) and this record reads the result. Three states of
the same canto are comparable, because the pre-repair Stage-4 output is still
in git (`6323d95^`) — that, not the repaired `HEAD` file, is the honest
baseline for a run that never deletes rows:

| inferno 1 | rows | hard | soft | agree F1 (P / R) |
|---|---:|---:|---:|---|
| Stage-4 raw output (`6323d95^`) | 427 | **6** | 34 | 0.7681 (0.7330 / 0.8067) |
| S5.3 repair applied (`HEAD`) | 421 | 0 | 34 | 0.7738 (0.7435 / 0.8067) |
| **S5.5 gate, re-run** | 434 | **0** | **48** | **0.7737 (0.7327 / 0.8196)** |

**The gate holds.** `adopted_invalid` is **0 across all 34 units**, with
`final_submission_valid` true on every one: no unit ended on rows its own
gate had rejected, and the turn cap was never the reason a session ended.
`make check` gives 0 hard — the two row-local classes are 0 by construction
as predicted, and `make repair-check` confirms it from the other side
(`nothing to repair`, 0 rows), so S5.3's two deletion rules are now
unreachable at the source. **The clausal class was not measured here**:
inferno 1's 6 pre-repair hard violations were both row-local classes, so this
canto never held any of the 70, and the question S5.4/S5.5 opened about
clausal registration is still open on the other 99 cantos.

**Gold agreement did not move.** The re-run scores 0.7737 against S5.3's
0.7738 — a tie to the fourth decimal, reached by an opposite route: repair
raised precision by deleting 6 rows at unchanged recall, while in-session
correction **kept the rows and moved recall instead** (0.8067 → 0.8196, tp
313 → 318) at some cost in precision (0.7435 → 0.7327). Against the raw
Stage-4 output both are a real gain (0.7681). Read as §5 requires — a readout
taken afterwards, on checks that are gold-closed transcriptions of
`validate.py` — the honest reading is that **schema-driven in-session
correction is not better than deletion at converging on gold on this canto;
it is level with it, and differently shaped.** That is the first such
comparison the project can make honestly (the Handoff's carry-over caveat on
S5.3's rules), and it earns less than S5.5 hoped for.

**Soft violations rose 34 → 48**, which is the same trade seen from the
other side: rows the deletion rules removed cannot violate a soft check
either, and rows the model repaired in-session stay in the file to be judged.
The increase is dominated by `extra_arg obl` (4 → 13) — the bare-`obl`
over-assignment already queued as the next soft target (M1.4, Handoff) — plus
one new `membership` finding (`1:59`, an `obl` argument heading no
NP/pronoun/predicate). Soft findings are not reported into the session by
design (S5.5), so nothing in this run addressed them.

**Cost is affordable.** 114 model calls over 33 agent-routed units =
**3.45 turns/unit** (22 units at 3, 7 at 4, 4 at 5; the cap never reached).
Compute time totalled 6,267.7 s (~1 h 45 m) including 900.4 s from an
interrupted first attempt; the resumed invocation's own wall clock was
5,367.7 s, against a Stage-4 corpus mean of ~5,531 s/canto (6:09:58:51 over
100 cantos). The added gate errors did not inflate the run.

**The resume mechanism is confirmed live**, incidentally rather than as a
staged check: the operator interrupted the first attempt after 5 settled
units (lines 1–18) and re-ran the same command. The summary's
`routes: {agent: 28, fast: 1, tsv: 5}` with `reasons: {"already settled in
the artifact": 5}` is that resume — only unsettled units re-ran, and the
settled ones were re-validated from the TSV at no model cost. The
middle-of-file deletion gesture was not exercised.

**Where this leaves the stage.** The mechanism works and is cheap, but it
bought no gold convergence over the deletion rules it replaced, and it moved
soft violations up. Re-running the other 99 cantos (164 h of live model time)
cannot be justified on this evidence, and the canto that would test the
remaining open question — clausal registration — was not among them. The
cheapest next measurement is therefore **one canto that actually holds
clausal violations**, re-run the same way; the levers behind it, unchanged,
are prompt-side teaching (`runner/prompts.py`, deliberately untouched so this
run measured the gate alone) and the deterministic soft work over the
committed TSVs.

### S5.7 — Clausal cleared at the source; the fast path joins the schema gate; 0 hard corpus-wide (2026-08-30)

S5.6 left the clausal class untested, because inferno 1 held none of the 70.
This record tests it on the 52 cantos that do, finds the last 3 violations
outside the gate's reach, and closes that gap — taking the recon corpus to
**0 hard violations**, the first time since it was measured.

**The fix gesture has line granularity, not row granularity.** The first
attempt deleted the 70 violating *rows* (plus one cascade: `purgatorio 13`'s
`101 7 dir ccomp 101 8` was the predicate its neighbouring `xcomp` cited, so
removing it made a second row violate) and re-ran — and **not one model call
was made**. `TsvArtifact`'s settled-unit test is line-number presence
(`extractor/reconstruct.py`), so a line that still carries any other row is
still present and its unit still settled. Deleting every row of the offending
*line* is what unsettles the unit: 68 lines across 52 cantos, 277 rows in
total. `make check` then reports those lines as hard `missing lines` — the
deliberate pre-run state, and the signal that the re-run has something to do.

**The re-run** (operator, three canticle streams): 64 units, 61 of them
agent-routed, 225 model calls, **3.69 turns/unit** (32 at 3, 21 at 4, 6 at 5,
one at 6, one at 9), 15,306.8 s of compute. `adopted_invalid` was **0 across
all 64**, `final_submission_valid` never false — the same result S5.6 got on
inferno 1, now on the units the design was actually aimed at. Corpus-wide:
**70 hard → 3**, soft 5,002 → 5,025, agree F1 0.7307 → 0.7308.

**The 3 survivors were never in a session.** All three carry
`route="fast", reason="complete"` — the deterministic Stage-2 path, which
skips `validate_candidate` by never opening a session. So the gate resolved
**67 of the 67 clausal violations it could see**, and the residue is not a
hole in the gate but a population outside it. Splitting the Stage-4 logs by
route shows how the two sit relative to each other:

| route | units | hard violations | units with any |
|---|---:|---:|---:|
| agent | 3,232 | 888 | 701 |
| fast | 245 | 3 | 3 |

The fast path is 7% of the corpus at 1.2% of its units carrying a hard
violation against the agent's 21.7% — its output was never the problem, which
is exactly why S5.5 put the checks in the session. Clearing the 888 is what
made the 3 visible.

**What shipped.** `hybrid_engine.schema_violations(nos, texts, rows)` runs
`validate_unit` over a derivation's own rows **with L1 alone** — called that
way the validator runs its closed-world schema checks and no derivation, so
it is the admission contract, not a second opinion on the roles the fast path
chose (`tag` findings, the soft tier, are dropped). `Derivation` carries the
result, and `RoutePolicy.require_schema_valid` (on by default) routes a unit
whose own output the schema rejects to the agent with
`reason="schema_invalid"`, ordered after `conflicts` and before `no_rows`.
Gold is not opened anywhere on that path. Six tests pin it (the three schema
classes, the soft tier's exclusion, the routing decision and its toggle,
severity order): **925 → 931 passed**.

**The three units, re-run under it**: all three routed `agent /
schema_invalid` as designed, and the session cleared each one — 0 hard,
`adopted_invalid` false, 3/3/4 turns, 10 model calls and 13 minutes in total,
with every other unit in those cantos replayed from the artifact. Corpus-wide
readout afterwards:

| | hard | soft | agree F1 (corpus) |
|---|---:|---:|---|
| S5.3's corpus (the starting point) | 70 | 5,002 | 0.7307 |
| after the 52-canto clausal re-run | 3 | 5,025 | 0.7308 |
| **after the fast-path schema gate** | **0** | **5,014** | **0.7309** |

`make check` exits 0. Per-canticle agreement is inferno 0.7357 / purgatorio
0.7282 / paradiso 0.7287 (rows 42,790, gold 40,091, tp 30,289).

**What the three readouts together say.** Gold agreement moved 0.7307 →
0.7309 across all of it — the third consecutive flat result, after S5.6's tie
on inferno 1. In-session correction demonstrably *works* on what it is for:
it clears the schema's hard classes at the source, cheaply (3.69 turns/unit,
no wall-clock inflation) and without deleting rows, where S5.3's rules cleared
them by deletion. It is not, however, a route to gold: hard-clean and
gold-close are different targets, and the 5,014 soft findings — untouched by
any of this, and never reported into a session by design — are where the
remaining distance lives.

**Also shipped, observability** (`PLAN.md` §4 item 5): the reconstruction path
passed no `on_turn` at all, so a live run showed the model's streamed turn and
nothing of what came back. `progress_printer(..., result_chars=N)` now echoes
each call's rendered `<tool_result>` block — the very bytes the next user
message carries — with the payload truncated (`read_unit` is the session's
size tail); `agent_fallback(result_chars=)` wires it to the status line's
console, and `reconstruct.py --tool-result-chars` (default 400, 0 = off) is
the operator control. Display only: no prompt, tool schema, or wire change,
so Standing Invariant 6 is untouched. Three more tests: **931 → 934 passed**.
