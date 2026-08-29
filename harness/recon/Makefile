# Stage-4/5 full-corpus reconstruction driver — one committed TSV per canto.
#
# The per-canto goal is <canticle>/NN.tsv, and reconstruct writes it directly:
# each parse unit's rows are appended the moment the unit settles, so the
# artifact IS the run's state (../STAGE5.md record S5.5). Resume needs nothing
# else — a unit whose lines are already in the TSV is not re-run — so an
# interrupted launch resumes by re-running the very same make command, and a
# canto whose TSV is complete costs no model calls at all.
#
# That also makes the artifact the repair surface: **delete the lines of a
# stretch you want reconsidered, re-run, and just that unit regenerates**
# (the file is rewritten in line order when the gap is not at the tail).
#
# Each canto also gets a streaming JSONL log under <canticle>/NN.log (unit /
# gold / canto_complete / llm_request|response / summary records). It is an
# append-only debug record — never read back, no part in resume.
#
# Because the logs are gitignored and the TSVs are committed, a fresh
# checkout has the artifacts but none of the logs. That must NOT re-run a
# 164-hour corpus: a canto whose TSV exists and whose log is gone is left
# alone. Deleting a TSV is therefore the way to ask for that canto again.
#
# Launch configuration is the one carried from STAGE4.md §2 (S3.9/S3.11):
# verbatim transcripts, payload tier R1, reactive-only pacing (HTTP 429s are
# absorbed by llm7shi.Client's own backoff), max-length 6000 — all
# reconstruct.py defaults except --verify-gold, passed explicitly below.
# --write stays off: skel/ remains immutable gold, written_cantos == 0
# expected.
#
## make                                this help (run from harness/recon)
## make inferno                        all 34 inferno cantos, one TSV each
## make purgatorio                     all 33 purgatorio cantos
## make paradiso                       all 33 paradiso cantos
## make -j3 inferno purgatorio paradiso
##                                     THE Stage-4 launch: three concurrent
##                                     streams, each relying on the backend's
##                                     own 429 backoff for pacing;
##                                     wall-clock projection assumes three.
## make inferno/12.tsv                a single canto (stem = <canticle>/NN);
##                                     units already in the TSV are not re-run;
##                                     already present with no log = left alone
## Model override:  make ... inferno MODEL=ollama:gemma4:31b-it-qat
##
## Legacy log conversion (LLM-free; for the Stage-4 logs, whose cantos predate
## the streamed writer — a canto run since then already has its TSV):
## make convert                        every existing log -> its TSV
##                                     (gold-format skel; telemetry stays in
##                                     the logs, see ../STAGE5.md §2)
## make convert-check                  regenerate in memory only; non-zero exit
##                                     if a committed TSV has drifted. Valid
##                                     only for a canto produced in ONE
##                                     uninterrupted run: after a resume the
##                                     log holds just the newly run units
## make check                          validate every committed TSV against the
##                                     derived skeleton (hard/soft violations,
##                                     no model call — same check as skel/skel.py
##                                     --check, pointed at this canticle's root)
## make stats                          soft-violation counts by class (and by
##                                     role), no model call — same as
##                                     skel/skel.py --stats
## make agree                          row-level P/R/F1 of the committed TSVs
##                                     against gold — a READOUT, never a target:
##                                     repair rules are derived from the layer's
##                                     own schema with gold unopened, and this is
##                                     read afterwards (../STAGE5.md §5)
## make repair                         apply the deterministic repair rules to
##                                     the committed TSVs, in place
## make repair-check                   report unrepaired rows; non-zero exit if
##                                     any remain

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

# .PRECIOUS on the log too: without it, make deletes the target file it was
# updating when make itself receives a fatal signal (Ctrl+C, SIGTERM) mid-recipe
# — verified live: SIGINT to a running `make` deletes the target it was
# writing. Every already-settled unit streamed to disk before the interrupt
# must survive so the next `make` invocation's unit-level resume can see it.
# (A plain recipe failure, e.g. a non-zero exit with no signal, does not
# trigger this deletion — only the signal path does — but .PRECIOUS covers
# both.)
.PRECIOUS: %.log

# The per-canto goal: reconstruct writes the TSV itself, unit by unit as units
# settle (`--tsv`, ../STAGE5.md record S5.5). There is no separate conversion
# step and no `%.log` prerequisite: completion is decided *inside* reconstruct
# by the artifact — a TSV whose lines are all present settles every unit, so
# the run costs no model calls and exits fast. That makes a re-invocation the
# way to regenerate whatever is missing, and the fix gesture is to delete a
# stretch's lines from the TSV before re-running.
#
# The guard below is defense in depth for the fresh-checkout state (committed
# TSVs, no logs): reconstruct would do nothing there anyway, but skipping the
# launch entirely keeps a clone from paying for artifact loads it does not
# need.
#
# .PRECIOUS for the same reason as %.log: a fatal signal to make mid-recipe
# must not delete a committed artifact it was in the middle of refreshing.
.PRECIOUS: %.tsv
%.tsv: FORCE
	@mkdir -p $(@D) \
	&& if [ -f $@ ] && [ ! -f $*.log ]; then \
		echo "$@: present and its log is gone — keeping it, nothing to run"; \
	else \
		echo "=== $@ ==="; \
		uv run python -m harness.extractor.reconstruct \
			--canticle $(*D) \
			--canto $$((10#$(*F))) \
			--verify-gold --model $(MODEL) \
			--log $*.log --tsv $@; \
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

check:
	uv run python -m harness.recon.check

stats:
	uv run python -m harness.recon.check --stats

# Divergence reduction (STAGE5.md §5). Rules come from the layer's own schema
# and derivation contract (dante_corpus/skel/validate.py, derive.py) — never
# from reading gold and matching it: gold is harness/'s benchmark, and fitting
# to it would void every gold-referenced number the project reports. `agree` is
# therefore a readout run after the fact, not an acceptance criterion.
#
# `repair` edits the committed TSVs in
# place, so the git history keeps the "raw model output -> rules applied" diff.
# It must therefore run AFTER convert, never before: re-running convert
# regenerates from the logs and rolls the repairs back.
repair:
	uv run python -m harness.recon.repair

repair-check:
	uv run python -m harness.recon.repair --check

agree:
	uv run python -m harness.recon.agree --per-canticle

FORCE:
.PHONY: FORCE convert convert-check check stats repair repair-check agree
