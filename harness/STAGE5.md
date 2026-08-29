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
deterministic-rule methodology.

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
the gold-side ledger. No implementation has started; this section records
the direction only.

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
