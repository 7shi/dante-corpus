# Stage-4 full-corpus reconstruction driver — one log per canto.
#
# Each canto gets its own streaming JSONL log under
# harness/recon/<canticle>/NN.log (unit / gold / canto_complete /
# llm_request|response / summary records), so resume is per-canto by
# construction: a target whose log already ends with the contract's summary
# record is skipped outright; anything else relaunches reconstruct on the
# same log and its unit-level resume picks up the unfinished units
# (reconstruct.py's startup compaction strips the superseded summary on the
# way in). An interrupted launch therefore resumes by re-running the very
# same make command.
#
# Launch configuration is the one carried from STAGE4.md §2 (S3.9/S3.11):
# verbatim transcripts, payload tier R1, reactive-only pacing, shared
# TokenBucket, max-length 6000 — all reconstruct.py defaults except
# --verify-gold and the bucket, passed explicitly below. --write stays off:
# skel/ remains immutable gold, written_cantos == 0 expected.
#
## make -f harness/recon/Makefile                 this help (run from anywhere)
## make -f harness/recon/Makefile inferno         all 34 inferno cantos, one log each
## make -f harness/recon/Makefile purgatorio      all 33 purgatorio cantos
## make -f harness/recon/Makefile paradiso        all 33 paradiso cantos
## make -f .../Makefile -j3 inferno purgatorio paradiso
##                                     THE Stage-4 launch: three concurrent
##                                     streams sharing harness/tokbucket.state
##                                     (aggregate <=75% of TPM by construction);
##                                     wall-clock projection assumes three.
## make -f .../Makefile harness/recon/inferno/12.log
##                                     a single canto (stem = <canticle>/NN)
## Model override:  make ... inferno MODEL=ollama:gemma4:31b-it-qat

ROOT := $(patsubst %/,%,$(abspath $(dir $(lastword $(MAKEFILE_LIST)))/../..))

LOGDIR := harness/recon
BUCKET := harness/tokbucket.state
MODEL ?= google:gemma-4-31b-it
HELPFILE := $(lastword $(MAKEFILE_LIST))

SHELL := /bin/bash
.DEFAULT_GOAL := help

CANTICLES := inferno purgatorio paradiso

inferno:    $(foreach n,$(shell seq -w 1 34),$(LOGDIR)/inferno/$(n).log)
purgatorio: $(foreach n,$(shell seq -w 1 33),$(LOGDIR)/purgatorio/$(n).log)
paradiso:   $(foreach n,$(shell seq -w 1 33),$(LOGDIR)/paradiso/$(n).log)
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
$(LOGDIR)/%.log: FORCE
	@cd $(ROOT) \
	&& mkdir -p $(@D) \
	&& if [ -f $@ ] && tail -n 1 $@ | grep -q '"record": "summary"'; then \
		echo "$@: summary record present — complete, skipping"; \
	else \
		echo "=== $@ ==="; \
		uv run python -m harness.extractor.reconstruct \
			--canticle $(*D) \
			--canto $$((10#$(*F))) \
			--verify-gold --model $(MODEL) \
			--token-bucket $(BUCKET) \
			--log $@; \
	fi

FORCE:
.PHONY: FORCE
