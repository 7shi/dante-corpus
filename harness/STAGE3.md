# Stage 3: Context Optimization & Full-Corpus Scale-Out

Stage-3 home document: the compaction/pacing **design** (record S3.2, this
file), the stage's milestone ledger as records accrue, and eventually the
archived stage record at close. [`PLAN.md`](PLAN.md) keeps status and the
handoff; numbers live here, never log filenames.

**Status**: design COMPLETE (2026-08-25, record S3.2). Implementation
COMPLETE (2026-08-25, record S3.3 — this file's §4 map, all seven items
shipped; measured deviations from the §2/§3 counterfactuals documented in
the ledger's S3.3 record). **Confirmation run #1 read out (record S3.4):
every gate passes except solo rolling-60 (76% vs ≤65%), caused by a
fallback-wiring bug since fixed; `--min-send-interval` now defaults to 0 by
operator decision. Records S3.5–S3.6 (same day) narrowed the wire view
twice, and record S3.7 removed it entirely: transcript compaction in every
shape bought ≤ 0.5% of the wire, so the transcript now rides verbatim and
the bytes come out of the system prompt instead (10,706 → 8,954 B, no
wording changed). §2.A is WITHDRAWN — read it as the record of why. Live
levers: R1 payload serving (§2.B) + pacing (§2.C) + the prompt size.
Re-run #2 ran clean and passed every quality criterion, its ×3 average being
the first to pass unpaced (record S3.9); the generation-side runaway cap was
then verified, decided at 6,000 chars and implemented (record S3.10); what
remains is the inferno-1 cap experiment and the three canticle-parallel
runs.**

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

### 2.A Compaction — the continuation wire view (WITHDRAWN by record S3.7)

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

- **Per-stream min inter-send interval** (`min_send_interval`, default 0 = off
  since record S3.4 — pass e.g. `--min-send-interval 35` to enable):
  sleep before the request until the last send *start* is ≥ interval
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

**Record S3.3 — compaction/pacing implementation (milestone per §4): COMPLETE
(2026-08-25, assistant-run, deterministic; tests 833 → 867 passed, no model
touched).** All seven §4 items shipped: `runner/tools.py` serves `read_unit`
in tier R1 (positional rows + 373 B inline legend) with tier S1 (sparse named
dicts) behind `GrammarToolkit(payload_tier=...)`; `runner/prompts.py` gains
`continuation_system_prompt` (measured **8,831 B — exactly the §2.A design
figure**); new `runner/compact.py` holds the pure history policy
(`compact_view` + `digest_message` + `history_policy`); `runner/agent.py`'s
`llm7shi_generate` takes `history_policy` / `min_send_interval` /
`token_bucket` with the content-fingerprint Client sync (rebuild on
view-prefix change; append-only prefixes still reuse the Client),
`paced_seconds` + `uncompacted_bytes` on every `llm_request` (join key
`messages` keeps transcript-position meaning), one stderr line per pacing
wait, pacing state surviving `reset()`, and a `TokenBucket`
(fcntl-locked JSON `{t, tokens}`, continuous refill, over-depth debits
drain-and-proceed instead of deadlocking); `agent_fallback` passes everything
through; `reconstruct` gained `--no-compact`, `--payload-tier`,
`--min-send-interval` (default 35), `--token-bucket` + `--bucket-rate` /
`--bucket-depth` (defaults 12k tok/min, 6.5k tok) and announces the
configuration on a header line; 34 new tests (28 in
`tests/test_harness_compact.py` + 5 tier tests in the tools suite + 1 CLI
configuration test in the reconstruct suite), including an end-to-end
compacted session over the real loop and corpus.

- **Three deviations from the §2/§3 counterfactuals, all measured and gate-
  preserving.** (1) The R1 morphology row keeps a 9th element for the Layer-2
  `note` (26% of corpus rows carry one — 'reflexive', 'clitic', 'apocope'…);
  the design's 8-field spec would have silently dropped live annotation the
  Stage-1/2 wire always served, a capability change, not packing. (2)
  `format_tool_result` now renders success payloads with compact JSON
  separators — the design's §2.B sizes were measured that way, so this aligns
  the physical wire with the measurement basis (validator feedbacks shrink
  ~12% for free; parse tests are separator-agnostic). (3) Both tiers flatten
  nested NP children into sibling rows (positional rows cannot nest; content
  coverage is identical and test-pinned). Measured wire (envelope, 3,477
  units): old 27.4 MB → **R1 11.3 MB (41%), p50 2.7 / p90 4.9 / max
  10.7 kB**; S1 23.9 MB, p50 5.5 / max 23.5 kB. The design counterfactuals
  (9.6 MB / 2.3 / 9.8) were computed pre-envelope and note-free; the delta is
  the envelope overhead + the note column. **Corpus-wide tail check on the
  measured wire: max view ≈ 8.8 + 0.4 + 10.7 + 3.8 + 0.5 ≈ 24.2 kB ≈ 6.9k tok
  ≈ 43% solo — inside the restated ≤ 45% bound** (G2), and the average shift
  is ~+1 pt on G1's 66% — margin intact.
- **Confirmation-run inputs (§5) are all in place**: the tier decision runs
  `--payload-tier S1` if R1 breaks the F1 band; `--no-compact` reverts the
  whole package; `context_bytes ≪ uncompacted_bytes` is directly readable per
  request record. Residual unchanged from §2.C: internal Client retries
  bypass outer pacing (rare, counted by `wait_retry`).

**Record S3.4 — confirmation run #1 readout + wiring fix + pacing default
change: COMPLETE (2026-08-25).** Run: `recon-inf1-compact.log` — inferno 1, compact R1 + interval
35 + no bucket, 101 request/response pairs over 33 sessions, wall 5,761.8 s.
Readout: verify-gold micro F1 **0.7867** (tp 319 / fp 103 / fn 70) — inside
the pilot/recheck band → **tier decision: R1 kept**; gate-pass units **19/34**;
empty responses 0/101; compaction live everywhere (all 68 position≥7 calls
show `context_bytes < uncompacted_bytes`, openings verbatim ×33, zero
inversions; max call **18,965 B ≤ 24 kB**; note: the ≈0.7 expected ratio does
not reproduce on this basis because `uncompacted_bytes` now already carries
R1-compacted payloads — the honest comparison is against the recheck log:
Σinput 1,919.7 kB → 1,290.7 kB = **67% of the old wire**, better than the 71%
counterfactual). Gate quantities: ×3 average **72%** ≤80% PASS; peak call
**34%** ≤45% PASS; api-retry tax **1.6%** ≤~5% PASS; **solo rolling-60 max
76% vs ≤65% FAIL**.

- **Root cause of the rolling-60 miss — a fallback-wiring bug, not a design
  miss.** `agent_fallback._run` built a fresh `PromptXmlTransport` +
  `llm7shi_generate` closure per unit (`hybrid_engine.py`), so pacing state
  never spanned sessions and every session-opening send skipped the interval
  (25 measured gaps <35 s, all at session boundaries; the docstring's "one
  transport/toolkit pair serves all units" and S3.3's "pacing state surviving
  reset()" describe the intended wiring, and adapter-level tests exercise the
  closure directly, so the suite could not catch it). Fix: construction
  hoisted into the factory body — one shared pair per run; regression test
  pins transport identity across two `_run` calls; tests 867 → 868 passed.
- **Counterfactuals on run #1's own data** (same responses/durations, sends
  retimed): interval-35 enforced globally (fixed wiring) → ×3 average 67%,
  rolling-60 **54%, all gates pass**, +413 s wall over measured; interval ≈ 0
  (reactive-only, the open decision above) → ×3 average **84% > G1's 80% by
  construction**, rolling 77%, −797 s wall (= the waits).
- **Operator decision with the fix**: `--min-send-interval` defaults to
  **0** (was 35) — the re-run exercises the reactive-only arm of the A/B on
  compaction alone; the paced configuration stays one flag away. Deliberate
  waits in run #1 cost 795.6 s = 13.8% of wall across 29 calls (well above
  §2.C's +4.4% estimate, which assumed globally-enforced spacing rather than
  measuring it). §5's gate quantities were defined on the paced
  configuration; on the unpaced re-run they become observational, with the
  api-retry tax as the pressure indicator.

**Record S3.5 — results-centric wire view with a repair reference (operator
decision). SUPERSEDED THE SAME DAY BY RECORD S3.6 (below) before re-run #2
ever ran: the `last` mode and the `--assistant-turns` flag described here no
longer exist; what survives is the verbatim newest assistant turn and the
verbatim opening. Implementation shipped (2026-08-25, deterministic; tests
868 → 871 passed, no model touched); re-run #2 pending.** The operator reset
the compaction defaults after the run #1 / S3.4 discussion: **stop re-sending
thinking, stop re-sending old `<tool_call>` bodies**, then refined it with
the observation that a results-only view leaves the model blind to its own
pending submission — mid-session validator feedback would reference rows the
model can no longer see, breaking repair by construction ("dropは使い物に
ならない"). Final shape: assistant-turn handling has two modes,
**default `"last"`**:

- `"last"` (default): only the newest assistant turn rides verbatim — the
  pending candidate submission, the model's repair reference; every older
  turn is omitted entirely (thinking prose and old tool_call bodies are
  never re-sent);
- `"digest"`: the S3.3 layout (older turns as one-line digests).

(A pure results-only `"drop"` mode was also implemented in the first cut and
**removed by operator verdict the same day** — its counterfactual over run
#1 traffic had measured Σ ≈ 1,396 kB / ×3 ≈ 90% unpaced, kept here only as
decision evidence.)

Implementation:

- `runner/compact.py` — `compact_view`/`history_policy` gained
  `assistant_mode="last"|"digest"` and `continuation_system=None` support
  (None = keep the opening verbatim — system, few-shot demo, task — instead
  of swapping to the continuation prompt).
- `agent_fallback` gained `assistant_turns="last"` /
  `continuation_prompt=False` pass-throughs. `--no-compact` still reverts
  everything; `--payload-tier` unchanged.
- `reconstruct` CLI gained `--assistant-turns {last,digest}` and
  `--continuation-prompt`; the header announces the live shape ("compaction
  ON (results+last submission)" by default).
- Adapter (`runner/agent.py`): with `"last"`, result-only growth extends the
  fingerprint mirror and reuses the Client; the mirror rebuilds when the
  pending submission rotates (prefix change), which is the normal repair
  cycle. A first-cut "mirror trim" branch proved dead code once `"drop"` was
  removed and was deleted with it.

Counterfactual sizing over run #1's own traffic (same responses, unpaced),
for the **`last` default**: Σinput ≈ 1,455 kB = 113% of run #1 (the
full-opening resend outweighs everything dropped) / 76% of the recheck wire;
×3 average ≈ **94% of ceiling** unpaced — near-zero margin, so solo runs
should expect stochastic 429 contact (pilot/recheck measured 2.5–9.4% tax)
and the three-stream launch needs the shared bucket regardless of these
choices. Adding `--continuation-prompt` recovers ≈ −246 kB → ×3 ≈ 74%. The
open question re-run #2 answers is quality: does repairing against feedback
whose referenced submission IS visible (`"last"`) hold the F1 band while
older context stays dropped.

**Stage 3, record S3.6 — two modes only: digest, or no compaction
(operator decision): implementation shipped (2026-08-25, deterministic;
871 tests passed, no model touched).** S3.5's planned re-run configuration
was `--assistant-turns last`, which omits every older assistant turn. The
operator rejected it before the run on a structural argument: with only the
newest turn on the wire, each send conditions on essentially one message —
**a Markov chain**. The session's own history (what was already tried, what
the earlier turns established, why the current submission looks the way it
does) is gone from the model's view, and no per-run quality measurement can
buy that back. The `last` mode is therefore **removed**, not demoted to an
opt-in, joining the earlier `drop` mode in the record's evidence column.

The wire view now has exactly two configurations:

- **compaction on (default)** — §2.A's digest layout: user messages
  (`read_unit` payloads, `<tool_result>` feedback, nudges) verbatim, the
  newest assistant turn verbatim (the repair reference), every older
  assistant turn as a one-line digest (~150 B). The opening still rides
  verbatim unless `--continuation-prompt` swaps in the 8,831 B continuation
  system prompt.
- **compaction off** — `--no-compact`: the full transcript, Stage-1/2
  semantics, the honest baseline to compare against.

Implementation (the removal is a narrowing, so it deletes more than it
adds): `compact_view` / `history_policy` lost `assistant_mode`;
`agent_fallback` lost `assistant_turns`; `reconstruct` lost
`--assistant-turns` and now announces "compaction ON (assistant
digests+last submission)". `--no-compact`, `--payload-tier`,
`--continuation-prompt` and the pacing flags are unchanged.

Sizing: digests cost ~150 B per older assistant turn on top of S3.5's `last`
counterfactual (Σ ≈ 1,455 kB, ×3 ≈ 94% unpaced) — sessions run 2–4 assistant
turns, so this is a sub-percent addition and §5's predicted quantities carry
over unchanged. `--continuation-prompt` remains the lever that recovers
≈ −246 kB (×3 ≈ 74%) if the re-run's readout says bytes must come down.

**Stage 3, record S3.7 — transcript compaction removed; the system prompt
carries the reduction instead (operator decision): shipped 2026-08-25
(deterministic; 871 → 855 tests passed, no model touched).** S3.6 left one
compaction shape standing (digests). Measuring what it actually bought,
over run #1's own `llm_request` records, ended the line of work:

| transcript position | calls | measured `uncompacted − context` | attributable to |
|---|---|---|---|
| 5 (call 1) | 33 | 0 B | opening verbatim |
| 7 (call 2) | 33 | 2,438 B | **entirely the continuation-prompt swap** (system −1,875, demo −563); no older assistant turn exists yet |
| 9 (call 3) | 33 | 2,552 B | swap + **114 B** of digest |
| 11 (call 4) | 2 | 4,363 B | swap + 1,925 B (two turns) |

Run total: 1,464.1 → 1,290.7 kB. Of the 173.4 kB saved, **165.8 kB is the
prompt swap and 7.6 kB is the digest — 0.5% of the wire.** And the 0.5% is
spent in the worst possible place: sessions run a median of 3 calls (§1.4),
so the median session digests only the `read_unit` dispatch turn (whose
payload rides verbatim in the user message anyway — an information-free
114 B deletion), while the ~960 B digests appear exactly in the 4-call
sessions, where the deleted turn is **the earlier candidate submission the
validator feedback is talking about**. Operator verdict: the mechanism pays
its risk precisely in the repair sessions that need history most.

The continuation prompt fell with it, on the operator's standing rule that
**changing what a resend contains destabilizes behaviour**: swapping the
system prompt from call 2 on is exactly that, for 2,438 B/call.

Where the bytes actually were, re-measured: `system_prompt` = 10,706 B, of
which the `tool_specs` JSON is 5,794 B — and **1,752 B of that is
`json.dumps(..., indent=2)` whitespace carrying no meaning at all**
(`toolcall/prompts.py`). Rendering the specs flat costs nothing semantic and
runs on *every* call, call 1 included:

| rendering | specs body | system prompt | per call | run #1 (101 calls) | 99-canto (~3,000 calls) |
|---|---|---|---|---|---|
| `indent=2` (was) | 5,794 B | 10,706 B | — | — | — |
| flat (now) | 4,042 B | **8,954 B** | −1,752 B | −177 kB | ≈ −5.3 MB |

Net effect on run #1's traffic: **full verbatim transcripts with the slim
prompt ≈ 1,287 kB against the compacted run's actually-sent 1,290.7 kB** —
the same wire, with the model's whole session visible again and no
resend-time divergence anywhere. Caveat carried into the re-run: the quota
is metered in *tokens*, and indentation whitespace tokenizes cheaply, so the
byte reduction will under-deliver in tokens by an unmeasured factor; the
re-run's request records are what settle it.

Removed: `runner/compact.py` (module + `--no-compact`), `continuation_system_prompt`,
`agent_fallback(compact=, continuation_prompt=)`, the CLI's `--no-compact` /
`--continuation-prompt`, and `llm_request.uncompacted_bytes` (it now always
equalled `context_bytes`). Kept: R1 payload serving, all pacing (interval +
shared bucket), the fingerprint Client sync (it also catches same-position
retries), and `paced_seconds`. `tests/test_harness_compact.py` became
`tests/test_harness_pacing.py` (16 tests: adapter sync, pacing, bucket,
end-to-end verbatim session). The reconstruct header now announces
`transcripts verbatim, payload tier R1`.

**Stage 3, record S3.8 — the wire records now carry provider-reported token
counts (operator observation): shipped 2026-08-25 (deterministic; 855 → 859
tests passed, no model touched).** S3.7 closed with an unmeasured caveat —
the quota is metered in tokens, the records were denominated in bytes, and
every token figure in this stage (the 5.13k tok/min solo average, ×3 = 96%,
the bucket's debits) came from the 3.5 B/token convention. The counts are
not actually unavailable: they are provider-specific, and llm7shi keeps the
raw stream chunks verbatim on `Response.chunks`, where Gemini reports
`usage_metadata` (`prompt_token_count` / `candidates_token_count` /
`thoughts_token_count` / `total_token_count`, the final chunk carrying the
call's totals) and Ollama reports `prompt_eval_count` / `eval_count`.

`runner/agent.py` gained `token_usage(response)`: it scans the chunks
backwards, normalizes whichever shape it finds to `input_tokens` /
`output_tokens` / `thought_tokens` / `total_tokens`, and returns those keys
all-`None` for an unknown backend, an absent stream, or a changed provider
field — cost accounting must never break a live run. `llm7shi_generate`
stamps the result onto every `llm_response` record next to `output_bytes`,
so the schema is uniform across providers and the join key is unchanged.
Two limits are inherent, both identical to the byte figures the records
already carried: the counts describe the attempt whose text `Client`
returned (a quality regeneration's discarded attempt is invisible here, as
it always was — `wait_retry` still measures those), and they land on the
*response* record because the request record is written before the call.

What this buys the re-run readout, at no cost to the run: §5's token
quantities become measurements instead of byte-derived estimates, joined
per call as `(session, messages, attempt)`; the open S3.7 question — how
much of the −1,752 B/call flat-JSON reduction survives as tokens — is read
straight off the first-call `input_tokens` instead of inferred; and
`BYTES_PER_TOKEN = 3.5`, which the shared bucket debits with, becomes
falsifiable against `context_bytes / input_tokens` per call. The constant
itself is deliberately left alone until the re-run measures it: pacing
parameters are a between-runs decision (the standing constraint), and the
bucket must estimate *before* the send, where only bytes are known.

*Addendum (same day) — live preflight + `thought_bytes`.* The unit tests pin
`token_usage` against fabricated chunk shapes, so one two-turn live call was
run before committing the re-run to the change. It passed on every point
that matters: usage is reported (17 → 37 `input_tokens` across the two
turns, the growth being exactly the transcript resend), and the measured
ratio was **3.53 / 3.54 B/token against the 3.5 convention** — on short
Italian plain text, so it is a baseline for isolating what the harness's
XML markup and JSON schemas cost, not a confirmation for the real traffic.

The preflight also turned up something the byte records had been hiding:
**`thought_tokens` 139 / 203 against `output_tokens` 14 / 7** — an order of
magnitude more thinking than answer, none of which reaches `response.text`
and therefore none of which `output_bytes` ever counted. Thinking is billed
as output, so the 16k *input* tok/min ceiling and the whole pacing design
are untouched. What it does change is S3.1's honest negative result: the
backoff non-localization rested on a generation baseline r0 = 13.9 B/s
derived from answer bytes alone, and the per-call rate spread it could not
explain (7.6–19.5 B/s) is the expected signature of thinking volume varying
call to call while the denominator ignores it. `llm_response` therefore also
records `thought_bytes` (`Response.thoughts`, 0 when the backend returns
none), which makes the re-run's readout able to ask whether per-call
duration tracks thinking rather than output — and whether the 429s become
localizable once the real work is in the denominator. Tests 859 → 860.

**Stage 3, record S3.9 — confirmation re-run #2 readout: verbatim transcripts
+ slim prompt pass every quality criterion solo, unpaced (assistant readout
over the operator-run log; deterministic; no code changed, tests untouched at
861).** Run: `recon-inf1-verbatim.log` — inferno 1 on the post-S3.7/S3.8
state (transcripts verbatim, payload tier R1, flat-JSON system prompt,
`--min-send-interval` default 0 = the reactive-only arm, no bucket):
**104** request/response pairs over 33 sessions (+1 fast-routed unit), wall
clock **5,275.5 s ≈ 88 min** (run #1, paced interval 35: 5,761.8 s — the
unpaced arm finished ~8% faster).

Quality (Handoff checklist 1) — PASS on every criterion:

- verify-gold micro F1 **0.7728** (tp 318 / fp 116 / fn 71; P .7327 /
  R .8175; exact units 1/34) — inside the pilot/recheck band 0.744–0.796,
  floor 0.72 clear; −0.014 vs run #1's 0.7867 is noise-scale. The restored
  session history held quality; the slimmer prompt is exonerated.
- gate-pass units **18/34** (target ~18±noise); empty responses **0/104**;
  token assertion errors 0; routes agent 33 / fast 1.
- The Stage-2 watch items reproduce exactly: the fast-routed unit (L76)
  fails Gate 2 (routing `complete` ≠ checker-clean); hard violations
  dup 6 / position 1 surface only through the checker; soft 32 all tag.

Prompt size live (checklist 2): first-call `context_bytes` median
**9,769 B** (n=33, range 9,767–9,771 — only the ~250 B task varies)
= run #1's 11,519 − **1,750 B**, matching S3.7's −1,752 design figure;
consistent with system 8,954 + demo 563 + task ~252.

Gate quantities (checklist 3) — the ×3 averages gate passes for the first
time, with zero deliberate pacing:

| quantity | re-run #2 (verbatim, interval 0, no bucket) | references |
|---|---|---|
| solo average input | **4,667 tok/min = 29%** of ceiling | corrected recheck 32%; pre-R1 37% |
| 3 × average | **87% < 100% PASS** | corrected 96% (zero margin); pre-R1 112% |
| peak single call | **12,999 tok = 81%** solo alone | pre-R1 max call 94%; the compacted design's G2 ≤45% bound was defined on a withdrawn wire view |
| rolling-60 s max | **15,435 tok = 96%; wall-minutes ≥100%: 0** | recheck 132%, 14 calls ≥100%; run #1 76% FAIL |
| api-retry tax | **2 backoffs / 79 s = 1.50%**, unpaced | run #1 paced 1.6%; historical unpaced 2.5–9.4% |

Honest caveat kept in view: §3's gate table (G2 ≤45%, G3 ≤65%) was written
for the since-withdrawn compacted configuration; on the shipped verbatim
configuration the measured pressure quantities above are the operative
gates, and they pass solo — but an 81%-alone peak call shows how little
headroom an uncoordinated second stream would have (launch decision below).

Tokens (S3.8 live) — provider counts landed on all 104 responses (zero
missing):

- `context_bytes / input_tokens`: median **3.56**, aggregate **3.44**
  against `BYTES_PER_TOKEN = 3.5` → the shared bucket debits accurately;
  the constant stays.
- Σinput **409,321 tok**; generation split Σoutput 51,072 vs Σthought
  **127,448** tok — thought is **71% of generated tokens** (thought_bytes
  309 kB vs output_bytes 119 kB); the preflight's order-of-magnitude holds
  at ~2.5× on real traffic.

Duration analysis (S3.1's negative result, re-tested with real work in the
denominator):

- duration correlates **total_tokens r=+0.97**, thought_tokens +0.88,
  output only +0.60–0.64 → per-call duration tracks **thinking**, not the
  answer bytes S3.1 had.
- effective generation rate `(thought+output)/duration`: median
  **83.9 B/s**, quartiles 78.6–89.2 (±7%). With thinking counted the rate
  spread collapses — S3.1's "non-localizable" 630 s excess was mis-modeled
  generation (r0 = 13.9 B/s divided visible answer bytes by whole
  durations), not hidden quota contact. This run's actual 429 waits are
  fully visible where it matters: the counters (2 / 79 s).

S3.7's open question — how much of −1,752 B/call survives as tokens — is
**SETTLED** (operator-run offline probes, same day). Method: both renderings
metered by 1-token `generateContent` probes reading
`usage_metadata.prompt_token_count` (the same wire shape llm7shi sends,
since the Developer API's `count_tokens` endpoint rejects
`system_instruction`; `/tmp/opencode/spec_indent_tokens.py`, ephemeral).
Validation is exact on both axes: byte parity of the rendered openings
against the logged `context_bytes` is 33/33 sessions at delta 0, and the
offline flat-opening count reproduces this run's logged first-call
`input_tokens` median precisely (**2,436 vs 2,436 tok, delta +0**).

Answer: the −1,752 B/call renders as **−410 real tokens** (specs body
1,078 → 1,488 tok), the removed whitespace carrying a marginal
**4.27 B/tok** — cheap in tokens, exactly the direction S3.7 suspected,
but only mildly: **82% of the naive 3.5-convention value** (501 tok)
survives. Per call −410 tok; over this run's 104 calls ≈ −42.6k tok ≈ 10%
of Σinput. Directionally safe for pacing: the bucket, debiting bytes ÷ 3.5,
slightly *overestimates* what indentation costs — conservatism, not error.
Operationally the relief was already proven (×3 = 87%, zero ceiling-minutes);
this closes the bookkeeping.

Launch decision input (checklist 4): quality holds → expansion unblocked.
Solo reactive-only is validated (1.50% tax ≈ run #1's paced 1.6%, zero
deliberate-wait cost, wall clock −8%). But solo peaks reach 81% of the
key's ceiling on one call and 96% within a rolling minute with zero
coordination, so three parallel shells sharing one TPM ceiling need the
shared `TokenBucket` for inter-stream coordination (sustained aggregate
≤75% by construction; costs nothing while headroom exists). Wall-clock
projection on measured pace (~155 s/unit): longest canticle ≈ 34 cantos ×
5.28 ks ≈ 180 ks ≈ **2.1 days compute-only** — under the 2.8–3.2 day
estimate even with bucket contention.

**Stage 3, record S3.10 — generation-side runaway cap decided at 6,000
chars, implemented, and staged for an inferno-1 experiment (assistant
implementation, deterministic; tests 861 → 864; no model touched; operator
decision 2026-08-25).** The design note's provisional 12,000-char line was
**overturned by verification before any code change**: its "legitimate
cross-run max 6,295 B" anchor was a misclassification.

*The re-classification.* A turn-1 cross-run scan over all 99 sessions
(33 × three inferno-1 runs) shows the session opener is structurally the
~114 B `read_unit` call — median 114 B / p90 115 B in every run — with
exactly two exceptions, both first turns of the verbatim run: the 17,739 B
runaway **and** the 6,295 B response. Both >4 kB outputs are therefore the
same turn-1 over-generation pathology, not two populations. Supporting
evidence: the same unit (inferno 1, lines 109–111) opened at 115/116 B in
compact/recheck vs 6,295 B in verbatim; its subsequent sends match the other
runs almost byte-for-byte (1,197/1,201 B); and its gate outcome (hard `dup`)
reproduces identically in all three runs — unit difficulty, not answer
dependent. The natural (non-pathological) output maximum is **3,885 B ≈
3,847 chars** (p99 over 308 responses).

*Threshold verification* (`/tmp/opencode/max_length_sim.py`, ephemeral;
framework validated by reproducing S3.9's recorded counterfactual exactly —
cap >4 kB → 400 B ⇒ 2 triggers, max request context **22.3 kB**): with both
large outputs classified pathological, caps 5,000/6,000 chars catch **2/2**
with zero observed false positives (headroom ≥ 1.30× over the natural max),
while 8,000/12,000 miss the 6.3 kB event entirely. Post-cap peak context is
bounded by *organic* multi-turn sessions (~22.3–22.7 kB), so tighter caps do
not lower peaks further on this evidence — the choice is purely about
covering the observed failure family. Operator decision: **`max_length =
6000`**.

*Mechanics (confirmed in llm7shi source)*: `max_length` counts
answer-text **characters only** — thinking excluded, and tokens unusable at
runtime because a streaming chunk is not necessarily one token (provider
counts land only after the response completes). Crossing it stops the stream
at once (waste bounded by ~T chars + one chunk), `should_retry` fails the
turn, and the quality-retry loop regenerates (`DEFAULT_LLM_RETRIES = 3`;
a truncated reply enters history only if all retries also exceed — far below
any plausible threshold). Thinking-only runaways remain uncaught by design.
Byte↔char sensitivity: measured bytes/char = 1.000–1.011 on 87 agent texts,
so chars ≈ bytes for this corpus; trigger sets were invariant across a
r=1.00–1.02 sweep (matters for future non-Latin corpora).

*Implementation map*: `runner/agent.py`'s `llm7shi_generate` takes
`max_length=None` (adapter neutral — the benchmark stays uncapped until its
own decision), hands it to `Client(max_length=...)`, and makes cap-caused
regenerations durably observable: an instance-level `should_retry` wrapper
counts attempts whose `Response.max_length` is set, and each `llm_response`
record gains **`max_length_retries`** (per-call delta; `reset()` clears) —
the one Client-internal retry made visible on the wire, because the
experiment's readout needs a durable trigger count. 
`extractor/hybrid_engine.agent_fallback(max_length=None)` passes through;
the policy default lives at the operator-facing CLI:
`reconstruct --max-length` (default **6000**, `0` disables, negatives
rejected), announced in the configuration banner (`max-length 6000 chars` /
`max-length off`). Tests +3 (`test_harness_agent.py` 39 → 41,
`test_harness_reconstruct.py` 34 → 35).

*Experiment protocol (operator-run, next action)*: inferno 1 dry-run on the
new default — `uv run python -m harness.extractor.reconstruct --canticle
inferno --canto 1 --verify-gold --model google:gemma-4-31b-it --log
harness/recon-inf1-cap6k.log` (no `--write`; interval default 0, bucket off
— solo arms stay comparable to re-run #2). Readout criteria: F1 within the
0.744–0.796 band; Σ`max_length_retries` and which sessions triggered; peak
request context vs re-run #2's 37.3 kB; wall clock vs 5,275.5 s.
