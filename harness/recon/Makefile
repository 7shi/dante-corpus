# Stage-4 full-corpus reconstruction driver — one log per canto.
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
# Launch configuration is the one carried from STAGE4.md §2 (S3.9/S3.11):
# verbatim transcripts, payload tier R1, reactive-only pacing (HTTP 429s are
# absorbed by llm7shi.Client's own backoff), max-length 6000 — all
# reconstruct.py defaults except --verify-gold, passed explicitly below.
# --write stays off: skel/ remains immutable gold, written_cantos == 0
# expected.
#
## make                                this help (run from harness/recon)
## make inferno                        all 34 inferno cantos, one log each
## make purgatorio                     all 33 purgatorio cantos
## make paradiso                       all 33 paradiso cantos
## make -j3 inferno purgatorio paradiso
##                                     THE Stage-4 launch: three concurrent
##                                     streams, each relying on the backend's
##                                     own 429 backoff for pacing;
##                                     wall-clock projection assumes three.
## make inferno/12.log                a single canto (stem = <canticle>/NN)
## Model override:  make ... inferno MODEL=ollama:gemma4:31b-it-qat

MODEL ?= google:gemma-4-31b-it
HELPFILE := $(lastword $(MAKEFILE_LIST))

SHELL := /bin/bash
.DEFAULT_GOAL := help

CANTICLES := inferno purgatorio paradiso

inferno:    $(foreach n,$(shell seq -w 1 34),inferno/$(n).log)
purgatorio: $(foreach n,$(shell seq -w 1 33),purgatorio/$(n).log)
paradiso:   $(foreach n,$(shell seq -w 1 33),paradiso/$(n).log)
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

FORCE:
.PHONY: FORCE
