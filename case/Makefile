include ../model.mk

CANTICLES = inferno purgatorio paradiso

all: case

case:
	uv run case.py $(CANTICLES) -m $(MODEL)

check:
	uv run case.py $(CANTICLES) --check

stats:
	uv run case.py $(CANTICLES) --stats

clean:
	uv run case.py $(CANTICLES) --clean

.PHONY: all case check stats clean
