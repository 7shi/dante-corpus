# Stage-4/5 full-corpus reconstruction driver — one committed TSV per canto.
#
# The per-canto goal is <canticle>/NN.tsv, and reconstruct writes it directly:
# each parse unit's rows are appended the moment the unit settles, so the
# artifact IS the run's state (../stages/05.md record S5.5). Resume needs nothing
# else — a unit whose lines are already in the TSV is not re-run — so an
# interrupted launch resumes by re-running the very same make command, and a
# canto whose TSV is complete costs no model calls at all.
#
# That also makes the artifact the repair surface: **delete the lines of a
# stretch you want reconsidered, re-run, and just that unit regenerates**
# (the file is rewritten in line order when the gap is not at the tail).
#
# Each canto also gets a streaming JSONL log under <canticle>/NN.log (unit /
# gold / canto_complete / llm_request|response / summary records). It is a
# pure by-product: append-only, gitignored, never read back, no part in
# resume and no part in any goal or prerequisite here. Deleting the logs —
# all of them, at any time — changes nothing this Makefile does.
#
# Launch configuration is the one carried from ../stages/04.md §2 (S3.9/S3.11):
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
##                                     units already in the TSV are not re-run,
##                                     so a complete TSV costs no model calls;
##                                     delete a stretch's lines to ask for it back
## Model override:  make ... inferno MODEL=ollama:gemma4:31b-it-qat
##
## make clean-log                      delete the by-product logs
##                                     (<canticle>/NN.log). Touches no TSV and
##                                     changes nothing any target does — but
##                                     the logs are the only copy of their
##                                     run's telemetry, so it is irreversible
##
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
##                                     read afterwards (../stages/05.md §5)
## make fix-level                      per-canto counts of the soft findings a
##                                     fix run would act on — no model call,
##                                     the selection readout
## make fix-canto CANTICLE=inferno CANTO=12
##                                     reopen that canto's units carrying a
##                                     finding at the level in a live session
##                                     and REPLACE their rows with what it
##                                     re-solves; an answer that is not
##                                     hard-clean, does not reduce the level's
##                                     findings, or adds a violation class is
##                                     refused and the recorded rows stand
## make fix-inferno                    every canto of one canticle, in order
##                                     (a canto with no findings at the level
##                                     costs no model call)
## make -j3 fix-inferno fix-purgatorio fix-paradiso
##                                     the three streams in parallel, as the
##                                     Stage-4 launch runs them
## make fix                            all 100 cantos — hours of live model
##                                     time over committed artifacts; read
##                                     `make fix-level` first
## Level:  FIX defaults to `max` (every level the contract has argued, today 2;
##         levels are cumulative). Pin one with FIX=1 on any fix target.
## make repair                         apply the deterministic repair rules to
##                                     the committed TSVs, in place
## make repair-check                   report unrepaired rows; non-zero exit if
##                                     any remain

MODEL ?= google:gemma-4-31b-it
HELPFILE := $(lastword $(MAKEFILE_LIST))

# The run's true start, held across every canto recipe of one invocation
# (including the three -j3 canticle streams) — each canto still runs
# reconstruct.py as its own process, so reconstruct's own per-process clock
# alone cannot show this; passed through as --started-at so the status bar's
# label-side elapsed time reads the run's cumulative time instead of just
# this canto's. `?=` + `export`, not `:=`, because fix-inferno/-purgatorio/
# -paradiso recurse into `$(MAKE) fix-canto` per canto (FIX_CANTICLE below):
# without the export, that child make would re-run `date +%s` on every
# canto and lose the cumulative value; `?=` lets the exported one from the
# parent invocation win instead of being recomputed.
STARTED_AT ?= $(shell date +%s)
export STARTED_AT

SHELL := /bin/bash
.DEFAULT_GOAL := help

CANTICLES := inferno purgatorio paradiso

inferno:    $(foreach n,$(shell seq -w 1 34),inferno/$(n).tsv)
purgatorio: $(foreach n,$(shell seq -w 1 33),purgatorio/$(n).tsv)
paradiso:   $(foreach n,$(shell seq -w 1 33),paradiso/$(n).tsv)
.PHONY: $(CANTICLES) help

help:
	@sed -n 's/^## //p' $(HELPFILE)

# The per-canto goal: reconstruct writes the TSV itself, unit by unit as units
# settle (`--tsv`, ../stages/05.md record S5.5). There is no separate conversion
# step, and the log is neither goal nor prerequisite — completion is decided
# *inside* reconstruct by the artifact alone: a TSV whose lines are all
# present settles every unit, so the run costs no model calls and exits after
# the deterministic re-validation. That makes a re-invocation the way to
# regenerate whatever is missing, and the fix gesture is to delete a stretch's
# lines from the TSV before re-running — which now works the same whether or
# not a log happens to sit beside it.
#
# The fresh-checkout state (committed TSVs, no logs) therefore needs no guard:
# every unit is settled, reconstruct calls no model, and the only cost is the
# artifact mining each invocation does at startup.
#
# .PRECIOUS: without it, make deletes the target file it was updating when
# make itself receives a fatal signal (Ctrl+C, SIGTERM) mid-recipe — verified
# live: SIGINT to a running `make` deletes the target it was writing. Every
# already-settled unit streamed to disk before the interrupt must survive so
# the next invocation's unit-level resume can see it, and a committed artifact
# must not be destroyed mid-refresh. (A plain recipe failure with no signal
# does not trigger the deletion — only the signal path does — but .PRECIOUS
# covers both.)
.PRECIOUS: %.tsv
%.tsv: FORCE
	@mkdir -p $(@D)
	@echo "=== $@ ==="
	uv run python -m harness.extractor.reconstruct \
		--canticle $(*D) \
		--canto $$((10#$(*F))) \
		--verify-gold --model $(MODEL) \
		--started-at $(STARTED_AT) \
		--log $*.log --tsv $@

# The logs are a by-product (header): nothing here reads them, and their
# absence is the normal fresh-checkout state, so sweeping them changes nothing
# any target does. It is not recoverable, though — a log carries its run's
# telemetry and nothing else holds it, accepted as ephemeral by ../stages/05.md
# §2's decision rather than committed.
LOGS := $(CANTICLES:%=%/*.log)
clean-log:
	@n=$$(ls $(LOGS) 2>/dev/null | wc -l); \
	rm -f $(LOGS); \
	echo "clean-log: removed $$n log(s); TSVs untouched"

# `harness.recon.convert` (log -> gold-format TSV, ../stages/05.md record S5.1)
# has NO target here any more, deliberately (2026-08-30). Since S5.5
# reconstruct writes the TSV itself, so conversion is dead for anything run
# since; and over the committed corpus it is actively destructive — it
# regenerates from the logs, which rolls back S5.3's repairs and, for a canto
# resumed off its TSV, writes a file holding only the newly run units. The
# module and its tests stay for the legacy Stage-4 logs; invoke it directly and
# narrowly, knowing both hazards:
#   uv run python -m harness.recon.convert --canticle C --canto N [--check]

check:
	uv run python -m harness.recon.check

stats:
	uv run python -m harness.recon.check --stats

# Divergence reduction (../stages/05.md §5). Rules come from the layer's own schema
# and derivation contract (dante_corpus/skel/validate.py, derive.py) — never
# from reading gold and matching it: gold is harness/'s benchmark, and fitting
# to it would void every gold-referenced number the project reports. `agree` is
# therefore a readout run after the fact, not an acceptance criterion.
#
# `repair` edits the committed TSVs in
# place, so the git history keeps the "raw model output -> rules applied" diff.
# Anything that regenerates a TSV from its log therefore rolls the repairs
# back — which is half of why `convert` no longer has a target here (above).
repair:
	uv run python -m harness.recon.repair

repair-check:
	uv run python -m harness.recon.repair --check

agree:
	uv run python -m harness.recon.agree --per-canticle

# Stage-6 soft repair (../stages/06.md record S6.2). `fix-level` is the free
# selection readout: which cantos carry findings at this level, and how many.
# The `fix*` targets then reopen exactly those units in a live session — the
# model is shown its own recorded rows plus the invariants they break (never the
# derivation's answer, ../SOFT.md §4.2) and its answer REPLACES them, unless it
# is not hard-clean, does not reduce the level's findings, or introduces a new
# violation class, in which case the recorded rows stand.
#
# Every fix target is live model time and edits committed TSVs in place, so they
# are operator launches like the canticle targets. A canto with no findings at
# the level costs no model call — reconstruct reopens nothing and exits — so the
# aggregates are safe to point at everything and let the level decide.
#
# Deliberately NOT a pattern rule over file names: these targets do not produce
# a file, and `fix/inferno/12` would read as a path that never appears on disk.
# The canto is named the way the CLI names it, in variables.
#
# FIX defaults to `max`, resolved by the level table itself
# (`harness/extractor/fixlevel.py`) rather than restated here, so the Makefile
# carries no copy of how far repair currently reaches. Levels are cumulative, so
# `max` means "every repair whose outcome has been argued from the contract" —
# and it widens by itself when a level is added, which is the point. Pin
# `FIX=<n>` to hold a run to one level; every run announces the level it
# resolved, and each canto record stores it.
FIX ?= max

fix-level:
	uv run python -m harness.recon.check --fix-level $(FIX)

fix-canto:
	@test -n "$(CANTICLE)" -a -n "$(CANTO)" || { \
		echo "usage: make fix-canto CANTICLE=<canticle> CANTO=<n> [FIX=1]"; exit 2; }
	@n=$$(printf %02d $$((10#$(CANTO)))); \
	echo "=== fix level $(FIX): $(CANTICLE) $$n ==="; \
	uv run python -m harness.extractor.reconstruct \
		--canticle $(CANTICLE) \
		--canto $$((10#$(CANTO))) \
		--fix $(FIX) \
		--verify-gold --model $(MODEL) \
		--started-at $(STARTED_AT) \
		--log $(CANTICLE)/$$n.log --tsv $(CANTICLE)/$$n.tsv

# One canticle, canto by canto. Sequential by design: each canto is a live
# session, and the three canticles are the parallel streams (make -j3), exactly
# as the Stage-4 launch runs them.
define FIX_CANTICLE
	@for n in $$(seq -w 1 $(2)); do \
		$(MAKE) --no-print-directory fix-canto \
			CANTICLE=$(1) CANTO=$$n FIX=$(FIX) MODEL=$(MODEL) || exit $$?; \
	done
endef

fix-inferno:
	$(call FIX_CANTICLE,inferno,34)

fix-purgatorio:
	$(call FIX_CANTICLE,purgatorio,33)

fix-paradiso:
	$(call FIX_CANTICLE,paradiso,33)

# The whole corpus at one level. Hours of live model time over 100 committed
# artifacts: run `make fix-level` first and know what it is about to touch.
fix: fix-inferno fix-purgatorio fix-paradiso

FORCE:
.PHONY: FORCE check stats repair repair-check agree clean-log \
        fix fix-level fix-canto fix-inferno fix-purgatorio fix-paradiso
