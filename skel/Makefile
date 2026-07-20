include ../model.mk

CANTICLES = inferno purgatorio paradiso

all: skel

skel:
	uv run skel.py $(CANTICLES) -m $(MODEL)

check:
	uv run skel.py $(CANTICLES) --check

stats:
	uv run skel.py $(CANTICLES) --stats

repair:
	uv run skel.py $(CANTICLES) --repair

fix:
	uv run skel.py $(CANTICLES) --fix -m $(MODEL)

.PHONY: all skel check stats repair fix
