include ../model.mk

CANTICLES = inferno purgatorio paradiso

all: morph

morph:
	uv run morph.py $(CANTICLES) -m $(MODEL)

check:
	uv run morph.py $(CANTICLES) --check

.PHONY: all morph check
