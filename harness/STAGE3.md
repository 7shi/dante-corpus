# Stage 3: Context Optimization & Full-Corpus Scale-Out

Stage-3 home document: the compaction/pacing **design** (record S3.2, this
file), the stage's milestone ledger as records accrue, and eventually the
archived stage record at close. [`PLAN.md`](PLAN.md) keeps status and the
handoff; numbers live here, never log filenames.

**Status**: design COMPLETE (2026-08-25, deterministic log work + corpus
scans; no code changed yet). Implementation is the next milestone (S3.3).

---

## 1. Measured ground truth (and two corrections to S3.1)

Everything below is deterministic over the gitignored recheck log
(`llm_request`/`llm_response` pairs, join key `(session, messages, attempt)`),
the four benchmark logs' trace outcomes, and a fresh full-corpus
`read_unit` scan; method notes inline, scripts ephemeral.

### 1.1 Accounting correction — the physical input is `context_bytes`, not `context + new`

`runner/agent.py llm7shi_generate` logs `context_bytes` = **sum over all
messages of the request, including the newest one** (verified: the rendered
opening — system 10,706 + demo 563 + task 250 — is exactly the logged
11,519 B first-call `context_bytes`). S3.1's "additive `context+new`" therefore
double-counts every newest message. Corrected headline numbers:

| quantity | S3.1 (additive) | corrected (`context_bytes`) |
|---|---|---|
| total input (103 calls) | 2,239.8 kB | **1,919.7 kB** |
| solo average | 6.0k tok/min (37%) | **5.13k tok/min (32%)** |
| 3 × average vs 16k ceiling | 112% | **96%** |
| peak wall minute | 107–115% | **102%** (56.9 kB; rolling-60 max 58.2 kB = 104%) |
| max single call | 94% solo | **63% solo** (35.2 kB) |

The M2.5 readout's figures were right; the **launch-gate conclusion is
unchanged** — ×3 = 96% is zero margin, peaks trip the ceiling solo — but the
gate fails at "no margin", not at 112%.

### 1.2 Label correction — the 15–20.6 kB turn-2 messages are `read_unit` payloads, not validator feedback

The recheck's five largest `new_bytes` (15.0–20.6 kB, all at transcript
position 7) are the **L1–L4 unit contexts** served by `read_unit` for multi-line
units (e.g. inferno 1 L37–45, L91–99, L112–120). Validator feedbacks (position
9+) measure **p50 0.18 kB / max 0.5 kB** — the "~4 kB feedback cap" lever is
moot. Consequently S3.1's "any call ≤ ~28% solo" projection (floor + cap) does
not describe the wire: the real per-call floor is the **opening resent on every
call** plus the unit payload. Also corrected: "0–20 ms inter-send gaps" is the
response→request dispatch latency; actual inter-send gaps are response-
dominated (p50 50 s, min 3.8 s, p90 135 s), and the "floor 11.8 kB" figure is
not reproducible from any slice — superseded by the table below.

### 1.3 Where the input bytes actually go (recheck, 103 calls, 1,919.7 kB)

| component | bytes | share | notes |
|---|---|---|---|
| opening resent × 103 calls (11.52 kB each) | 1,185 kB | **62%** | system 10.7 + demo 0.56 + task 0.25 |
| `read_unit` payloads (33 fresh serves) | ~260 kB | 13% | corpus-wide wire sizes: p50 7.1 / p90 14.3 / max 30.0 kB |
| assistant outputs (87 kB Σ, max 3.8 kB) + replay | ~130 kB | 7% | validate turns are the big ones |
| validator feedbacks + replay | ~7 kB | 0.4% | negligible by measurement |
| everything else (replay overlap) | rest | — | Σcontext − Σfinal-call-contexts = 1,167 kB replayed |

**Implication**: the dominant levers are (i) the fixed opening (mostly the
5.8 kB tool-specs + 1.3 kB role + 1.2 kB wire-contract + 2.3 kB 5-step
protocol), (ii) the `read_unit` rendering for multi-line units, (iii) replay.
Validator-feedback capping is pointless; pacing alone cannot recover averages.

### 1.4 Session/turn structure (holds the design's complexity bound)

33 sessions (median 3 calls: 30×3, 2×4, 1×5; max 5), response durations p50
49 s / min 3.8 s / max 212 s; dispatch latency p50 5 ms. Sessions are short —
compaction is a *small-view* construction, not a rolling summarizer.

---

## 2. The design

Three levers plus launch hardening. Session semantics change **between runs**
only (standing constraint); every lever ships behind explicit wiring and one
confirmation run gates the whole package before the 99-canto launch.

### 2.A Compaction — the continuation wire view

The loop's transcript stays the single source of truth (`LoopResult.messages`,
traces, mining, nudge resumes unchanged). Only what the backend physically
receives changes, computed per call by a pure **history policy**
(`messages → wire view`), applied inside the adapter (`llm7shi_generate`) —
the one send point:

- **Call 1** (transcript position = opening length): the verbatim opening.
  Planning semantics are exactly Stage-1/2's.
- **Calls 2+**: `[continuation-system] [task] [compacted history] [newest]`:
  - **continuation-system** (8,831 B measured) = ROLE_INTRO + Step 5 (the
    validation/self-correction protocol — load-bearing on repair turns) + the
    XML wire contract + the **full** tool specs. Dropped vs the full system:
    Steps 1–4 (planning is done; the plan lives in the transcript) and the
    few-shot demo (the live transcript itself demonstrates the format). The
    tool specs stay **in full** — mid-session `validate_candidate` calls carry
    the most complex schema the model emits.
  - **compacted history**: the `read_unit` payload **verbatim** (the model's
    working data), every `<tool_result>` feedback **verbatim** (measured ≤ 0.5
    kB each), the **last assistant turn verbatim** (≤ ~3.8 kB; the newest
    candidate submission the model repairs from), and every older assistant
    turn as a one-line digest (~150 B: turn number, dispatched tool names,
    80-char prose head).
  - **newest message** verbatim, last position — the loop's contract.

Per-call view sizes (counterfactual over the recheck, §3): p50 ≈ 12.3 kB,
p90 ≈ 16.8 kB, **max ≈ 21.0 kB** (was p50 18.6 / max 35.2).

Adapter mechanics: the Client-history length-sync becomes a **content
fingerprint sync** (the view's prefix legitimately changes between calls, so
length alone can no longer detect staleness); on mismatch the Client is
rebuilt from the view (system prompt + history re-append) — the existing
rebuild path, now content-triggered. `llm_request.context_bytes` continues to
measure **what is physically sent** (the view) and gains `uncompacted_bytes`
(full transcript) as the savings audit; `messages` keeps its meaning
(transcript position), so the join key is unchanged.

### 2.B Payload compaction — positional `read_unit` serving (tier R1, primary)

`read_unit` serves the same content in compact form with an inline legend
(~220 B) inside the tool result:

- `morphology` rows: `[word, lemma, pos, gender, number, person, tense, mood]`
  (empty-valued trailing fields may be omitted);
- `dependencies` rows: `[token, head_token, deprel]`, plus `head_line` as a
  4th element **only when ≠ line**;
- `noun_phrases`: `[line, start, end, head]`;
- `lines`, `unit`, `quotes`, `case` keep their (sparse-dict) shapes — drop
  empty-valued keys and empty top-level sections only.

Corpus-wide measured effect (3,477 units): payload Σ 31.4 → **9.6 MB (31%)**;
p50 7.1 → 2.3 kB, p90 14.3 → 4.3 kB, **max 30.0 → 9.8 kB**. The one-line
columnar shape is CoNLL-like; the legend makes the result self-describing, so
no system-prompt change is needed to teach it.

**Fallback tier S1** (sparse named dicts, no positional arrays): Σ 19.5 MB
(62%), p50 4.5 / p90 8.8 / max 19.7 kB — same schema family as today, near-zero
comprehension risk, but leaves the heavy-unit tail high (§3). The confirmation
run picks the tier: R1 unless it breaks the F1 band, else S1.

### 2.C Pacing — min inter-send interval (default) + shared token bucket (launch)

The burst mechanism (S3.1, confirmed): a fast model response (min 3.8 s) puts
the next — bigger — send into the same rolling minute. Both mechanisms live in
the adapter, at the single send point; pacing state deliberately survives
`transport.reset()` (session boundaries are also sends).

- **Per-stream min inter-send interval** (`min_send_interval`, default 35 s,
  0 = off): sleep before the request until the last send *start* is ≥ interval
  past. Measured effect (recheck timeline, R1 views): solo rolling-60 max
  40.8 → 32.5 kB (73% → 58% of solo ceiling) at **+4.4% wall clock**.
  45 s costs +13%, 60 s +27% for no further rolling-max gain (two sends still
  share a 60 s window) — 35 s is the knee.
- **Shared token bucket** (`--token-bucket PATH`, off by default; the three
  parallel shells share one file — fcntl-locked JSON `{t, tokens}`, refill at
  rate R, capacity D, debit before send, sleep until funded): the TPM ceiling
  is a property of the **model API key**, which all three streams share, so the
  pacing instrument for the launch is the shared one. Launch parameters:
  **R = 12k tok/min (42 kB/min at the 3.5 B/tok convention), D = 6.5k tok
  (≥ max single call)** — sustained aggregate ≤ 75% of ceiling by construction;
  worst rolling minute ≤ R + D ≈ 116% (rare burst; the proven 429 auto-retry
  backstop absorbs it — solo runs already survived 102–104% minutes at a
  2.5–9.4% tax).
- Observability (§4 discipline): every pacing wait prints one stderr line and
  is logged as `paced_seconds` on the `llm_request` record, so the readout can
  separate deliberate waits from 429 backoffs (`api_retry_seconds`).

Residual, accepted: quality-retry regeneration and 429 backoffs *inside*
`llm7shi.Client` issue wire requests the outer pacing cannot see (measured
rare: 7 backoffs + a handful of regenerations per 103 calls).

### 2.D What is deliberately NOT in this design

- **Terminating on a valid validation** (dropping the final-answer turn,
  TOOLCALL.md §7.1) would cut ~1/3 of calls — the single biggest remaining
  lever — but reopens the protocol question and changes trace shape; tracked
  as a post-expansion follow-up, not a launch dependency.
- **Slimming the continuation specs** (5.8 kB → signatures): rejected for
  calls 2+ (the candidate-rows schema is the model's reference for its most
  complex emission); documented as unused headroom.
- Reacting to 429s (adaptive pacing): rejected — S3.1's negative result stands
  (backoffs are stochastic rolling-window contact); the design keeps the
  stream under the ceiling by construction instead.

---

## 3. Deterministic gate re-check (counterfactual)

Method: hold the recheck's measured structure fixed — session/turn counts,
response durations, validator-feedback sizes (logged `new_bytes` at position
≥ 9), assistant turn sizes (logged `output_bytes`) — and replace each call's
physical input with the §2 wire view, sizing `read_unit` payloads by
re-serving all 33 units in each tier. Pacing re-times the send sequence
(send_k = max(natural, send_{k-1} + interval); responses follow sends). This
is conservative (shorter views plausibly prefill faster; turn counts held).
Re-derivable from the log + §2.2's schemas.

| configuration | total input | solo average | 3 × average | peak single call | solo rolling-60 max |
|---|---|---|---|---|---|
| measured (no compaction) | 1,919.7 kB | 5.13k tok/min (32%) | **96%** | 63% solo | 104% |
| S1 + interval 35 s | ~1,511 kB | ~3.6k tok/min | ~72% | **45% solo** (7.2k tok) | ~80% |
| **R1 + interval 35 s** | **1,367 kB (71%)** | **3.5k tok/min (22%)** | **66%** | **38% solo (6.0k tok)** | **58%** |
| R1 + interval 60 s | 1,367 kB | 3.0k tok/min | 54% | 38% solo | 58% |

Corpus-wide tail check (R1, worst unit in all 100 cantos): max view
≈ 8.8 + 0.4 + 9.8 + 3.8 + 0.5 ≈ **23 kB ≈ 6.6k tok ≈ 41% solo** — under the
restated per-call bound even for the heaviest unit (S1's equivalent ≈ 61%).

**Gate verdicts (restated honestly):**

- **G1 aggregate average**: 3 × compacted average ≤ 80% of the 16k ceiling →
  **PASS at 66%** (R1 + 35 s; 54–72% across the tested range). The original
  "with margin" intent is met.
- **G2 peak single call ≤ ~30% solo**: **infeasible as stated and restated to
  ≤ 45%**. The 30% figure derived from S3.1's mislabeled-feedback arithmetic;
  the true wire floor (contract + full specs + payload + last submission)
  lands every workable design at 38–45%. R1 measures 38% (41% corpus-wide
  tail) — PASS under the restated bound.
- **G3 burst bound**: per-stream rolling-60 ≤ 58% solo (from 104%); with the
  launch bucket, sustained aggregate ≤ 75% by construction and the residual
  aligned-tail (≤ ~116%, rare) rides the proven retry backstop. PASS.

Wall clock: +4.4% single-stream (interval 35 s); the 99-canto three-parallel
estimate moves from ~2.5–3 days to ≈ **2.8–3.2 days** (bucket contention
included); compaction's prefill savings are not credited.

---

## 4. Implementation map (milestone S3.3 — next)

Modules and seams, in dependency order; all deterministic-testable, live faces
operator-run as always:

1. `runner/tools.py` — `read_unit` serves the R1 compact form + legend
   (envelopes/outcomes/traces carry the compact shape; mining consumers are
   done, benchmark comparability is re-anchored by the confirmation run).
2. `runner/prompts.py` — `continuation_system_prompt(specs, workflow)`
   (ROLE_INTRO + Step 5[workflow] + contract + specs; 8.8 kB).
3. `runner/compact.py` (new) — the pure history policy
   `compact_view(messages, *, opening_len, continuation_system) -> list[dict]`
   implementing §2.A, including digest rendering; no I/O, no model.
4. `runner/agent.py` — `llm7shi_generate(..., history_policy=None,
   min_send_interval=0.0, token_bucket=None)`: fingerprint sync (rebuild on
   view-prefix change), interval sleep (state survives reset), bucket
   (locked-file refill/debit), `paced_seconds` + `uncompacted_bytes` on
   `llm_request`, one stderr line per wait (shared stream).
5. `extractor/hybrid_engine.py` — `agent_fallback(...)` pass-through of the
   new parameters.
6. `extractor/reconstruct.py` — CLI flags `--no-compact` (default: compact
   ON), `--min-send-interval` (default 35), `--token-bucket PATH` with
   `--bucket-rate/--bucket-depth`; header line announces the configuration;
   existing resume/log contract untouched (new record fields are additive).
7. Tests (repo root, `tests/test_harness_*`): policy view shapes (opening
   verbatim; payload/feedback/last-assistant verbatim; digests; newest last;
   nudge transcripts), adapter fingerprint sync + rebuild, interval timing via
   injected clock, bucket via tmp file (sequential "processes"), compact
   `read_unit` rendering + legend + parity of content coverage, CLI flags,
   `render` of `paced_seconds`/`uncompacted_bytes`. No test touches a model.

## 5. Confirmation protocol (operator-run, live) — the gate before launch

One inferno-1 re-run, fresh `--log`, compact + interval 35 + no bucket
(single stream), same command shape as the M2.5 recheck:

- **Compaction live**: every position-7+ request shows
  `context_bytes ≪ uncompacted_bytes` (expected ratio ≈ 0.7); no request
  exceeds ~24 kB.
- **Quality band**: `--verify-gold` micro F1 within the pilot/recheck band
  (0.744–0.796; floor 0.72); parse-error turn rate not above the M1.4 band;
  gate-pass unit count in the usual range (18 ± noise of 34). **If R1 breaks
  the band → re-run once on S1** (tier decision, §2.B).
- **Gate quantities on the fresh log**: 3 × average ≤ 80%, peak call ≤ 45%
  solo, solo rolling-60 ≤ 65%, api-retry tax ≤ ~5%.
- Then the three canticle-parallel launch (PLAN.md Handoff command shape)
  with `--min-send-interval 35 --token-bucket <shared path>` on all three
  shells.

## 6. Risks and fallbacks

| risk | likelihood | mitigation |
|---|---|---|
| R1 payload comprehension degrades quality | medium | S1 fallback tier (§2.B) at 72% ×3 / 45% peak — still passes G1/G2-restated; bucket backstops the tail |
| continuation prompt (no Steps 1–4) shifts mid-session behavior | low-medium | Steps 5 + specs retained; confirmation run's parse-error + F1 criteria catch it; `--no-compact` reverts the whole package |
| bytes→token convention drift (3.5 B/tok) | low | all gates carry ≥ 20 pt margin at 3.5; at 4 B/tok every number drops 12% |
| internal Client retries bypass pacing | measured rare | accepted residual; `wait_retry` counters keep it visible |
| bucket file stale/locked | low | fcntl releases on process death; corrupt state → recreate at defaults (depth full); single machine, wall clock |

---

## Milestone Ledger (Stage 3)

**Record S3.1 — context-growth × 429 correlation analysis: COMPLETE
(2026-08-25, assistant-run).** As recorded in [`PLAN.md`](PLAN.md)'s ledger at
the time; **two accounting corrections land in S3.2** (§1.1 double-count,
§1.2 feedback mislabel). The record's mechanism findings stand: burst =
fast-response + big-send pairing, backoffs = stochastic rolling-window
contact, mitigation = under-the-ceiling by construction.

**Record S3.2 — compaction/pacing design + deterministic gate re-check:
COMPLETE (2026-08-25, assistant-run, this file).** Inputs: S3.1 (corrected),
the recheck log at request granularity, the four benchmark logs' trace
outcomes, and a fresh full-corpus `read_unit` scan. Findings: §1 (input is
62% opening resend; payloads are the size tail; feedbacks negligible; wire
floor bounds peak calls at 38–45% solo, not 30%). Design: §2 (continuation
wire view, positional payload R1 with S1 fallback, 35 s interval + shared
12k/6.5k bucket). Gate re-check: §3 — G1 PASS (66%), G2 restated-and-PASS
(38–45%), G3 PASS. No code changed; tests untouched at 833 passed. Next:
S3.3 implementation per §4, then the §5 confirmation run (operator), then the
launch.
