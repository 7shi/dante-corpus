# Stage 5: Corpus Durability

Stage-5 home document: opening scope, design work as it happens, and the
stage's milestone ledger as records accrue. [`PLAN.md`](PLAN.md) keeps
status and the handoff; detail lives here, not there — this stage writes
directly into this file as work happens, rather than accumulating in
PLAN.md and splitting off at close (the pattern Stages 1–4 used).

**Status**: OPENED 2026-08-29 (operator decision, on Stage 4's close).
Nothing shipped yet; no design finalized. Nothing is in flight on the
assistant side.

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
2. A separate format, design TBD, for whatever the logs carry that doesn't
   map into that skel-compatible shape: the wire/cost instrumentation
   (`llm_request`/`llm_response` pairs — full field shape in PLAN.md's
   Orientation item 5), per-turn timings, and violation/routing detail. None
   of this should be silently dropped when the source logs go away.

## 2. Open design questions

Carried forward, unresolved:

- What `skel/`-compatible shape the conversion targets — same TSV
  conventions as gold `skel/`, a parallel directory, or something else;
  whether canto-atomicity and the existing 0-soft-style invariants apply.
- What the separate format for non-mappable log content looks like — one
  file per canto mirroring the log layout, an aggregated summary, or
  something else; how it's kept in sync if the conversion script is re-run.
- Whether conversion is a one-time migration or a repeatable step meant to
  run after every future Stage-4-style corpus run.

---

## Milestone Ledger (Stage 5)

*No records yet — accrues as design and implementation work lands.*
