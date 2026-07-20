include ../model.mk

CANTICLES = inferno purgatorio paradiso

all: skel

skel:
	uv run skel.py $(CANTICLES) -m $(MODEL)

check:
	uv run skel.py $(CANTICLES) --check

stats:
	uv run skel.py $(CANTICLES) --stats

fix:
	uv run skel.py $(CANTICLES) --fix -m $(MODEL)

.PHONY: all skel check stats fix
