# Stage 4: Full-Corpus Verification (99-Canto Scale-Out)

Stage-4 home document: the launch configuration, the three canticle-parallel
runs' contract, in-run monitoring, the corpus-wide readout criteria, and the
stage's milestone ledger. [`PLAN.md`](PLAN.md) keeps status and the handoff;
numbers live here, never log filenames alone.

**Status**: CLOSED 2026-08-29 on record S4.3 (opened 2026-08-25 — operator
re-scope: the 99-canto expansion moved out of Stage 3, closed the same day
on record S3.11 in [`STAGE3.md`](STAGE3.md)). Scope closed as **full-corpus
run only**: the low-F1/cap-anomaly follow-up investigation named in S4.3 is
deferred to Stage 5+, not part of this stage.

**Pre-launch operation changes (2026-08-26, no ledger record cut at the
time — folded in here during the Stage-4 doc-organization pass)**: (0) the
shared `TokenBucket` pre-emptive pacing mechanism removed entirely
(operator decision) — `harness/runner/agent.py`'s `TokenBucket` class and
its constants, the `token_bucket` parameter threaded through
`llm7shi_generate`/`agent_fallback`/`reconstruct.main`, the
`--token-bucket`/`--bucket-rate`/`--bucket-depth` CLI flags, and the
Makefile's `--token-bucket $(BUCKET)` wiring are all gone; rely on
`llm7shi.Client`'s existing HTTP-429 backoff alone (a "wait on 429"
reactive discipline) rather than pre-emptive cross-process token-rate
pacing — `--min-send-interval` (default 0) is untouched. Test suite: 857
passed (down from 864 — seven `TokenBucket`-only tests in
`test_harness_pacing.py` removed with the mechanism). §2's table above
reflects this as the launch configuration throughout.

Two durability fixes also shipped ahead of the real launch, both promoted
to standing rules in [`../ARCHITECTURE.md`](../ARCHITECTURE.md) (full
technical detail lives there, not duplicated here). (1) Mid-canto kill resilience in
`reconstruct.py`: settled units now stream to disk as they settle
(`emit_unit` callback + a `settle` closure in `main`) instead of only after
a whole canto returns, so a kill mid-canto no longer discards already-settled
units; regression test
`test_cli_mid_canto_kill_keeps_settled_units_on_disk` pins it. (2)
`harness/recon/Makefile`'s per-canto log target marked `.PRECIOUS`, because
GNU Make deletes the target file a recipe was updating on a fatal signal
(verified live) — without the mark, a Ctrl+C/SIGTERM mid-run would erase
`reconstruct.py`'s just-shipped streamed records before its own resume logic
ever saw them. Test suite after both fixes: 858 passed (857 + 1, the
mid-canto kill regression test).

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
| `--max-length` | default 6000 chars (`0` disables); cap regenerations land as `max_length_retries` | S3.10/S3.11 |

Rationale in brief: reactive-only won every solo arm it ran (S3.9/S3.11); a
single call peaked at 81% of the key's ceiling uncoordinated (S3.9), but the
shared `TokenBucket` that once coordinated the three concurrent streams over
one TPM key was removed 2026-08-26 (operator decision — see PLAN.md
Handoff) in favor of relying on `llm7shi.Client`'s own HTTP-429 backoff
alone across all three streams; genuine three-stream contention without a
shared pacer is measured for the first time at this launch (§4/§5). The cap
caught its first live over-pack in S3.11 exactly as designed (114 B after
one regeneration).

## 3. Commands (make driver: `harness/recon/Makefile`)

```bash
make -C harness/recon -j3 inferno purgatorio paradiso
```

THE Stage-4 launch: three concurrent streams (one per canticle), each
relying on `llm7shi.Client`'s own HTTP-429 backoff for pacing (the shared
`TokenBucket` that once coordinated them was removed 2026-08-26 — see
PLAN.md Handoff). Wall-clock projection ≈ **180 ks ≈ 2.1 days
compute-only** for the longest canticle (~155 s/unit × 34 cantos), quota
permitting. `make -C harness/recon` alone prints the help; a single
canticle runs alone with `make -C harness/recon inferno`. The Makefile also
runs directly from inside `harness/recon` (plain `make -j3 ...`) — `-C` is
just the usual way to drive it from elsewhere.

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
  `--verify-gold` is passed explicitly; model default
  `google:gemma-4-31b-it`, overridable per invocation (`make ...
  inferno MODEL=ollama:gemma4:31b-it-qat`). Final call remains the
  operator's, at launch.
- **Single canto** = target relative to `harness/recon`:
  `make -C harness/recon purgatorio/12.log`.
  `-jN` above three multiplies concurrent streams; wall-clock projections
  assume three.
- Each target expands to
  `uv run python -m harness.extractor.reconstruct --canticle C --canto N
  --verify-gold --model M --log L`; `harness` is editable-installed, so
  `uv run` resolves the module regardless of invocation directory, and log
  paths resolve relative to wherever the Makefile runs (`harness/recon`
  under `-C`); the direct-command form stays valid for one-off manual runs.

## 4. In-run monitoring (watch items carried from Stages 2–3)

- the fast-routed unit fails Gate 2 (routing `complete` ≠ checker-clean);
- agent-originated hard violations (`dup` self-citation, `position` (0,0))
  surface only through the checker;
- quota tax varies run-to-run (measured range 0.24%–9.4%) — burst contact,
  not steady pressure;
- 0-soft unit pass counts fluctuate ±4–5 between runs while row-level F1
  holds the band (S3.11 flag 1): judge quality by verify-gold F1, treat
  gate-pass counts as noisy;
- **three-stream API contention is measured here for the first time** (all
  prior arms were solo): with the shared `TokenBucket` removed, all
  cross-stream pacing now comes from `llm7shi.Client`'s own 429 backoff;
  record aggregate TPM pressure from the merged timeline (§5) and any
  `paced_seconds` ≠ 0 anomalies (expected 0 at interval 0);
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
streams share one API key/quota with no shared pacer, so only the merged
view measures contention).

- **Per-canticle verify-gold micro F1**: inferno judged against the
  established 0.744–0.796 band; purgatorio/paradiso establish their own
  baselines on this run (first measurement).
- Gate-pass rates per canto and per canticle (expect roughly half of units,
  per every prior run; canto-level pass requires ALL units clean).
- TPM pressure: per-stream averages, ×N aggregates, rolling-60 peaks,
  ceiling-minutes, api-retry tax, `paced_seconds` (expected 0 at interval 0).
- Wall clock vs projection; three-stream contention cost isolated if visible.
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
| quota exhausts mid-expansion | resume per canto/unit; staggered relaunch; `llm7shi.Client`'s own 429 backoff absorbs bursts per stream |
| one canticle's F1 collapses | isolate config vs corpus effect via the other two logs; S1 tier (`--payload-tier S1`) remains one flag away |
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
- **S4.2 — 2026-08-26: Makefile runs from `harness/recon` directly;
  doc catch-up on the TokenBucket removal (pre-launch, operator-requested
  operation change + doc fix).** `harness/recon/Makefile` no longer takes
  `-f`/`ROOT`-relative paths: it's driven with plain `make` from inside
  `harness/recon` (targets `inferno/NN.log`, etc.), or `make -C
  harness/recon ...` from elsewhere — `harness` being editable-installed
  means `uv run python -m harness.extractor.reconstruct` resolves
  regardless of invocation directory, so the `cd`-to-repo-root plumbing
  the recipe carried was dropped along with it. Verified LLM-free: help
  text from both invocation forms, live single-canto skip-branch smoke
  test against a real complete log. Separately, this file's §2–§6 still
  described the shared `TokenBucket` (`--token-bucket`, `tokbucket.state`,
  bucket-contention monitoring/risk rows) as live launch configuration —
  stale since the mechanism's actual removal (commit predating this entry;
  see the pre-launch operation-changes note above this ledger) never
  propagated here. Brought
  in line: §2's table and rationale, §3's command block and flag list,
  §4's contention-monitoring bullet, §5's merge-rationale wording, and
  §6's risk table (the bucket-file-corruption row dropped, having no
  referent) now describe reactive-only pacing via `llm7shi.Client`'s own
  429 backoff across all three streams, with genuine three-stream
  contention still measured for the first time at the corpus-wide readout.
  Launch commands throughout now read `make -C harness/recon -j3 inferno
  purgatorio paradiso` (PLAN.md's Handoff updated to match). Nothing
  launched yet.
- **S4.3 — 2026-08-29: corpus-wide readout tool + results; STAGE 4 CLOSED on
  this record (operator decision: scope stays full-corpus run only).**
  Between S4.2 and this record the operator launched and completed the full
  run (`make -C harness/recon -j3 inferno purgatorio paradiso`, mid-run
  switched 3-way → 2-way parallelism in response to TPM pressure, switch
  time not logged/tracked by operator instruction): all 100 logs (34/33/33)
  present, each ending in a parseable `summary` record, timestamps spanning
  2026-08-25T21:19Z → 2026-08-29T07:57Z. New durable tool (committed, not
  the ephemeral `/tmp` pattern §5 originally described — a corpus-wide,
  stage-closing readout warranted a re-runnable script instead):
  `harness/recon/readout.py` (+ `harness/recon/__init__.py`, importable as
  `python -m harness.recon.readout`), tested by
  `tests/test_harness_recon_readout.py` (18 cases, pure aggregation math on
  synthetic in-memory records, no real logs read in the test suite). Test
  suite: 876 passed (858 + 18). Reads every `harness/recon/<canticle>/NN.log`
  LLM-free and reports hygiene, per-canticle micro F1 (pooled tp/fp/fn) +
  lowest-F1 outlier cantos, gate-pass rates, pooled violation/routing
  breakdowns, TPM pressure, api-retry tax, peak context/token joins,
  per-canto wall-clock stats, and cap accounting.

  **Results**: hygiene all-clear on every check (zero token-assertion
  errors, zero empty responses, provider tokens present throughout,
  `written_cantos == 0`, all 100 logs present/parseable). Per-canticle
  verify-gold micro F1: inferno 0.7269, purgatorio 0.7186, paradiso 0.7201,
  corpus-wide 0.7219. **Inferno's 0.7269 falls just under the 0.744–0.796
  expected-variation band** established from the four single-canto
  confirmation runs (S3.4/S3.9/S3.10/S3.11 in [`STAGE3.md`](STAGE3.md)) —
  unlike gate-pass-count noise (already characterized/dismissed), F1 was
  established as "the reliable judge," so this miss is not automatically
  dismissable the same way; the operator's call, made on this record, is to
  **accept it and close the stage rather than block on it**. Lowest-F1
  cantos, carried forward for Stage 5+ investigation only (not acted on
  here): inferno 10/31/33, purgatorio 11/15/2, paradiso 17/7/10. Two
  cap-accounting anomalies flagged, also deferred: inferno canto 7 session
  15 and purgatorio canto 4 session 23 both regenerated to ~550 B instead
  of the expected ~115 B opener. Gate-pass rates ran low (units 30–34%,
  0/100 cantos canto-clean) — read per standing policy as the noisy
  instrument, not the quality judge. Fast-path routing held at 7.0%
  corpus-wide, matching the original Stage-2 measurement. TPM: the §5
  "one shared quota" framing was corrected in-session to the
  operator-confirmed reality that **each concurrent stream is
  rate-limited independently** (`STREAM_TPM_LIMIT = 16,000` tokens/min,
  checked per canticle) — paradiso's stream spent 48.8% of its 60-second
  windows over that limit (inferno 18.2%, purgatorio 20.1%); the merged
  three-stream timeline stays informational-throughput-only, not a
  contention measurement, under this correction. Compute-only wall time
  summed 6:09:58:51 across all three streams against an observed run span
  of 3:12:06:26 (~1.83× effective parallelism).

  **Stage 4 scope decision (operator, this record): CLOSED as full-corpus
  run only.** The low-F1-canto and cap-anomaly follow-ups above are
  explicitly out of Stage 4's scope — carried forward as Stage 5+ candidate
  work, not reopened here. Stage 5 itself opens on a different track first
  (skel-compatible log→artifact conversion, since `harness/recon/*.log` is
  gitignored/disk-only and would otherwise be lost); see PLAN.md §2 Stage 5
  and Handoff for the opening scope.
