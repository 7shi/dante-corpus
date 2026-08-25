# Stage 4: Full-Corpus Verification (99-Canto Scale-Out)

Stage-4 home document: the launch configuration, the three canticle-parallel
runs' contract, in-run monitoring, the corpus-wide readout criteria, and the
stage's milestone ledger. [`PLAN.md`](PLAN.md) keeps status and the handoff;
numbers live here, never log filenames alone.

**Status**: OPENED 2026-08-25 (operator re-scope: the 99-canto expansion
moved out of Stage 3 — closed the same day on record S3.11 in
[`STAGE3.md`](STAGE3.md)). The launch is the operator's act; nothing is in
flight on the assistant side.

---

## 1. What this stage does

Run the gated reconstruction pipeline over all 100 cantos as three
canticle-parallel streams — inferno / purgatorio / paradiso, one log per
canto — behind every Stage-3 gate, then read the corpus-wide results out.
This is **verification against the immutable gold** (`skel/`): `--write`
stays OFF, `written_cantos == 0` is the expected end state, and the 0-soft
regression gate decides each canto's pass/fail exactly as in the four
inferno-1 runs. Inferno 1 runs again like every other canto — a fifth
variance sample for the one unit with four prior measurements — and there
is no per-canto exclude flag (a canto sits out only by not invoking its
log target; see §3).

## 2. Launch configuration (carried from S3.9/S3.11; final call: operator)

| lever | value | source |
|---|---|---|
| transcripts | verbatim | S3.7 |
| payload tier | R1 (positional rows + legend; S1 fallback via `--payload-tier`) | S3.4 |
| system prompt | flat tool-spec JSON (8,954 B) | S3.7 |
| `--min-send-interval` | default 0 (reactive-only; solo tax measured 0.24%–1.6%) | S3.4/S3.9/S3.11 |
| `--token-bucket` | `harness/tokbucket.state`, shared by all three streams (R 12k tok/min, D 6.5k tok defaults) | S3.9 |
| `--max-length` | default 6000 chars (`0` disables); cap regenerations land as `max_length_retries` | S3.10/S3.11 |

Rationale in brief: reactive-only won every solo arm it ran, but a single
call peaked at 81% of the key's ceiling uncoordinated (S3.9) — three streams
sharing one TPM key need the bucket's inter-stream coordination (sustained
aggregate ≤75% by construction; no cost while headroom exists). The cap
caught its first live over-pack in S3.11 exactly as designed (114 B after
one regeneration).

## 3. Commands (make driver: `harness/recon/Makefile`)

```bash
make -f harness/recon/Makefile -j3 inferno purgatorio paradiso
```

THE Stage-4 launch: three concurrent streams (one per canticle) sharing
`harness/tokbucket.state`, aggregate ≤75% of the key's TPM by construction.
Wall-clock projection ≈ **180 ks ≈ 2.1 days compute-only** for the longest
canticle (~155 s/unit × 34 cantos), quota permitting, bucket contention
included. `make -f harness/recon/Makefile` alone prints the help; a single
canticle runs alone with `make -f harness/recon/Makefile inferno`.

- **Log layout**: one streaming JSONL log per canto at
  `harness/recon/<canticle>/NN.log` (zero-padded `01.log`–`34.log`). The
  log contract itself is reconstruct.py's, unchanged: unit / gold /
  canto_complete / llm_request|response records, per-record flush,
  summary last.
- **Completion gate lives in the log, not make timestamps** (`FORCE`
  prerequisite): a target whose log ends with the `"record": "summary"`
  line is skipped outright; anything else relaunches reconstruct on that
  same log and its unit-level resume picks up the unfinished units
  (startup compaction strips the superseded summary). **An interrupted
  launch therefore resumes by re-running the very same command.**
- **Configuration (§2) baked into the driver**: transcripts verbatim, tier
  R1, reactive-only pacing, cap 6000 are reconstruct defaults;
  `--verify-gold` and the shared bucket are passed explicitly; model
  default `google:gemma-4-31b-it`, overridable per invocation (`make ...
  inferno MODEL=ollama:gemma4:31b-it-qat`). Final call remains the
  operator's, at launch.
- **Single canto** = full-path target:
  `make -f harness/recon/Makefile harness/recon/purgatorio/12.log`.
  `-jN` above three multiplies concurrent streams; the bucket still bounds
  aggregate, but wall-clock projections assume three.
- Each target expands to
  `uv run python -m harness.extractor.reconstruct --canticle C --canto N
  --verify-gold --model M --token-bucket B --log L`, anchored at the repo
  root regardless of invocation directory; the direct-command form stays
  valid for one-off manual runs.

## 4. In-run monitoring (watch items carried from Stages 2–3)

- the fast-routed unit fails Gate 2 (routing `complete` ≠ checker-clean);
- agent-originated hard violations (`dup` self-citation, `position` (0,0))
  surface only through the checker;
- quota tax varies run-to-run (measured range 0.24%–9.4%) — burst contact,
  not steady pressure;
- 0-soft unit pass counts fluctuate ±4–5 between runs while row-level F1
  holds the band (S3.11 flag 1): judge quality by verify-gold F1, treat
  gate-pass counts as noisy;
- **bucket-under-contention is measured here for the first time** (all
  prior arms were solo): expect sustained aggregate ≤75% by construction;
  record any minute ≥100% and any `paced_seconds` ≠ 0 anomalies;
- cap triggers: Σ`max_length_retries` corpus-wide and their shape
  (expected: rare turn-1 over-packs regenerating to ~115 B openers).

## 5. Corpus-wide readout criteria (the closing act)

Inputs: the 100 per-canto logs under `harness/recon/<canticle>/` (34/33/33).
Per file, the streaming contract decides completeness — a log whose last
line parses as the `summary` record is complete; anything else (torn tail,
no summary) is an interrupted canto that still contributes its per-unit
records while flagging the corpus run not yet closable. Records carry
`canticle`/`canto`, and each canto ran as its own process, so session
numbers repeat across files: the provider-token join key
`(session, messages, attempt)` is namespaced per file before any merge,
and the TPM timeline is rebuilt by merging all files'
`llm_request`/`llm_response` records on their timestamps (the three
streams shared one bucket, so only the merged view measures contention).

- **Per-canticle verify-gold micro F1**: inferno judged against the
  established 0.744–0.796 band; purgatorio/paradiso establish their own
  baselines on this run (first measurement).
- Gate-pass rates per canto and per canticle (expect roughly half of units,
  per every prior run; canto-level pass requires ALL units clean).
- TPM pressure: per-stream averages, ×N aggregates, rolling-60 peaks,
  ceiling-minutes, api-retry tax, `paced_seconds` (expected 0 at interval 0).
- Wall clock vs projection; bucket-contention cost isolated if visible.
- Hygiene: `written_cantos == 0`, zero token assertion errors, zero empty
  responses, provider tokens present on all responses — and all 100
  expected logs present with parseable summaries (any exception means the
  stage is not closable yet).
- Cap accounting: Σ`max_length_retries` + triggering sessions corpus-wide.

Method note: readouts reuse the ephemeral-script pattern validated in
S3.11 (`/tmp/opencode/cap_readout.py`; if lost, recreate — methods reproduce
S3.9 exactly: span-average basis, sliding rolling-60 max-sum,
provider-token join on `(session, messages, attempt)`, r(generated) vs
r(total_tokens) distinction), generalized from S3.9's single-arm file to
the directory glob: per-file join first (session numbers are per-process),
then timestamp merge across streams for the TPM view. Python runs through
`uv`.

## 6. Risks / fallbacks

| risk | mitigation |
|---|---|
| quota exhausts mid-expansion | resume per canto/unit; staggered relaunch; the bucket keeps aggregate ≤75% by construction |
| one canticle's F1 collapses | isolate config vs corpus effect via the other two logs; S1 tier (`--payload-tier S1`) remains one flag away |
| bucket file corrupted/stale | fcntl releases on process death; corrupt state → recreate at defaults (depth full) |
| paradigm drift mid-run | standing constraint: session semantics change between runs, never mid-run |
| three-stream wall clock exceeds projection | longest canticle bounds it; partial logs still support per-canto readouts (summary-last contract marks completion) |

---

## Milestone Ledger (Stage 4)

- **S4.1 — 2026-08-26: make driver + per-canto log layout (pre-launch;
  operator-requested operation change).** `harness/recon/Makefile` replaces
  the three one-log-per-canticle shell commands as the launch interface:
  default target prints help; `make -j3 inferno purgatorio paradiso` is THE
  launch; aggregates run one canticle alone; single canto = full-path
  target; model override via `MODEL=`. One streaming JSONL per canto at
  `harness/recon/<canticle>/NN.log`; the recipe gates on each log's own
  summary record (`FORCE`, not timestamps), so resume = re-running the same
  command and reconstruct's unit-level resume works untouched underneath.
  §1/§3 rewritten accordingly; §5 gained the readout input contract
  (per-file session namespacing before joins, timestamp merge across the
  three streams for TPM, hygiene now requires all 100 logs present with
  parseable summaries). Launch configuration §2 unchanged — final call
  still the operator's, at launch. Nothing launched yet: no
  session-semantics exposure mid-run.
