CANTICLES = inferno purgatorio paradiso

all: split quotes

download:
	$(MAKE) -C src download

split:
	$(MAKE) -C src split

quotes:
	uv run python -m dante_corpus.build_quotes $(CANTICLES)

# Layer 2 morphology. LLM-built, so kept out of `all`; the TSV under morph/ is committed.
# The model is set in model.mk (included by morph/Makefile); override with `make morph MODEL=...`.
morph:
	$(MAKE) -C morph morph

morph-check:
	$(MAKE) -C morph check

clean:
	$(MAKE) -C src clean
	rm -f $(foreach c,$(CANTICLES),quotes/$(c).xml)

.PHONY: all download split quotes morph morph-check clean
