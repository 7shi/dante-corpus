include ../model.mk

CANTICLES = inferno purgatorio paradiso

all: case

# --log keeps the failed responses: a chunk the model cannot get past is skipped, not fatal,
# so the log is the only record of why. Parallel shells must each pass their own file.
case:
	uv run case.py $(CANTICLES) -m $(MODEL)

# A prompt change invalidates every frozen chunk, and nothing in the artifact is *invalid*, so
# `clean` (which drops only chunks holding a violation) removes nothing and `case` skips
# everything. The regeneration therefore drops the artifacts first and then builds normally —
# `--force` would restart from scratch on every resumed run, and this job is 1340 chunks. The
# frozen column is committed, so `git checkout case/` restores it.
regen:
	rm -f $(foreach c,$(CANTICLES),$(c)/*.tsv)
	uv run case.py $(CANTICLES) -m $(MODEL)

check:
	uv run case.py $(CANTICLES) --check

stats:
	uv run case.py $(CANTICLES) --stats

clean:
	uv run case.py $(CANTICLES) --clean

.PHONY: all case regen check stats clean
