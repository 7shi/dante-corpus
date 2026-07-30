include ../model.mk

CANTICLES = inferno purgatorio paradiso

all: case

# --log keeps the failed responses: a chunk the model cannot get past is skipped, not fatal,
# so the log is the only record of why. Parallel shells must each pass their own file.
case:
	uv run case.py $(CANTICLES) -m $(MODEL)

check:
	uv run case.py $(CANTICLES) --check

stats:
	uv run case.py $(CANTICLES) --stats

clean:
	uv run case.py $(CANTICLES) --clean

.PHONY: all case check stats clean
