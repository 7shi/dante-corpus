include ../model.mk

CANTICLES = inferno purgatorio paradiso

all: morph

morph:
	uv run python -m dante_corpus.build_morph $(CANTICLES) -m $(MODEL)

check:
	uv run python -m dante_corpus.build_morph $(CANTICLES) --check

.PHONY: all morph check
