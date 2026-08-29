# Stage-4/5 full-corpus reconstruction driver — one committed TSV per canto.
#
# The per-canto goal is <canticle>/NN.tsv, not the log: reconstruct writes a
# streaming JSONL log, and the Stage-5 conversion turns that log's settled
# reconstruction into the gold-format TSV that actually gets committed. The
# log is the intermediate; the TSV is the artifact.
#
# Each canto gets its own streaming JSONL log under
# <canticle>/NN.log (unit / gold / canto_complete / llm_request|response /
# summary records), so resume is per-canto by construction: a target whose
# log already ends with the contract's summary record is skipped outright;
# anything else relaunches reconstruct on the same log and its unit-level
# resume picks up the unfinished units (reconstruct.py's startup compaction
# strips the superseded summary on the way in). An interrupted launch
# therefore resumes by re-running the very same make command.
#
# Because the logs are gitignored and the TSVs are committed, a fresh
# checkout has the artifacts but none of the logs. That must NOT re-run a
# 164-hour corpus: a canto whose TSV exists and whose log is gone is left
# alone — the TSV is the durable output and there is nothing left to convert
# from. Deleting a TSV is therefore the way to ask for that canto again.
#
# Launch configuration is the one carried from STAGE4.md §2 (S3.9/S3.11):
# verbatim transcripts, payload tier R1, reactive-only pacing (HTTP 429s are
# absorbed by llm7shi.Client's own backoff), max-length 6000 — all
# reconstruct.py defaults except --verify-gold, passed explicitly below.
# --write stays off: skel/ remains immutable gold, written_cantos == 0
# expected.
#
## make                                this help (run from harness/recon)
## make inferno                        all 34 inferno cantos, log -> TSV each
## make purgatorio                     all 33 purgatorio cantos
## make paradiso                       all 33 paradiso cantos
## make -j3 inferno purgatorio paradiso
##                                     THE Stage-4 launch: three concurrent
##                                     streams, each relying on the backend's
##                                     own 429 backoff for pacing;
##                                     wall-clock projection assumes three.
## make inferno/12.tsv                a single canto (stem = <canticle>/NN);
##                                     already present with no log = left alone
## make inferno/12.log                the log alone, no conversion
## Model override:  make ... inferno MODEL=ollama:gemma4:31b-it-qat
## 
## Stage-5 conversion only (LLM-free, deterministic, safe to re-run any time):
## make convert                        every existing log -> its TSV
##                                     (gold-format skel; telemetry stays in
##                                     the logs, see ../STAGE5.md §2)
## make convert-check                  regenerate in memory only; non-zero exit
##                                     if a committed TSV has drifted

MODEL ?= google:gemma-4-31b-it
HELPFILE := $(lastword $(MAKEFILE_LIST))

SHELL := /bin/bash
.DEFAULT_GOAL := help

CANTICLES := inferno purgatorio paradiso

inferno:    $(foreach n,$(shell seq -w 1 34),inferno/$(n).tsv)
purgatorio: $(foreach n,$(shell seq -w 1 33),purgatorio/$(n).tsv)
paradiso:   $(foreach n,$(shell seq -w 1 33),paradiso/$(n).tsv)
.PHONY: $(CANTICLES) help

help:
	@sed -n 's/^## //p' $(HELPFILE)

# One pattern rule serves every canto log; stem $* = <canticle>/NN.
# FORCE makes the recipe run on every invocation — completion is decided by
# the log itself, not make's timestamps: complete = the last line carries
# the summary record (the streaming contract's completion marker), anything
# else relaunches and lets reconstruct's unit-level resume take over.
# Known hairline: a summary line truncated mid-write by a crash could still
# contain the marker and read as complete; the corpus-wide readout catches
# that case (a log without a parseable summary record is an interrupted run).
#
# .PRECIOUS on the pattern: without it, make deletes the target file it was
# updating when make itself receives a fatal signal (Ctrl+C, SIGTERM) mid-recipe
# — verified live: SIGINT to a running `make` deletes the target it was
# writing. That would erase reconstruct.py's unit-level durability work (§5
# durability seam) right along with it. Every already-settled unit record
# streamed to $@ before the interrupt must survive so the next `make`
# invocation's unit-level resume can see it. (A plain recipe failure, e.g. a
# non-zero exit with no signal, does not trigger this deletion — only the
# signal path does — but .PRECIOUS covers both.)
.PRECIOUS: %.log
%.log: FORCE
	@mkdir -p $(@D) \
	&& if [ -f $@ ] && tail -n 1 $@ | grep -q '"record": "summary"'; then \
		echo "$@: summary record present — complete, skipping"; \
	else \
		echo "=== $@ ==="; \
		uv run python -m harness.extractor.reconstruct \
			--canticle $(*D) \
			--canto $$((10#$(*F))) \
			--verify-gold --model $(MODEL) \
			--log $@; \
	fi

# The per-canto goal: reconstruct into the log, then convert the log to the
# committed TSV. `%.log` is NOT a make prerequisite here — that rule is
# FORCE-driven and would relaunch reconstruct even for a canto whose TSV is
# already on disk with its log discarded (the normal state of a fresh
# checkout). The guard below decides instead, and only then recurses into the
# log rule, so the log's own resume/skip logic stays the single source of
# truth for whether reconstruct runs at all.
#
# .PRECIOUS for the same reason as %.log: a fatal signal to make mid-recipe
# must not delete a committed artifact it was in the middle of refreshing.
.PRECIOUS: %.tsv
%.tsv: FORCE
	@if [ -f $@ ] && [ ! -f $*.log ]; then \
		echo "$@: present and its log is gone — keeping it, nothing to run"; \
	else \
		$(MAKE) --no-print-directory $*.log \
		&& uv run python -m harness.recon.convert \
			--canticle $(*D) --canto $$((10#$(*F))); \
	fi

# Stage-5 conversion over whatever logs are on disk, without touching the
# model: the logs are gitignored and disk-only, so their settled
# reconstruction is converted into a committable gold-format TSV beside each
# one. Only the corpus content is committed — the run telemetry the logs also
# carry (routing, gate verdicts, gold scores, wire/cost records) is not.
# Idempotent — regenerating from unchanged logs reproduces byte-identical
# files, so this is a repeatable step after any corpus run, not a migration.
convert:
	uv run python -m harness.recon.convert

convert-check:
	uv run python -m harness.recon.convert --check

FORCE:
.PHONY: FORCE convert convert-check
