CANTICLES = inferno purgatorio paradiso

all: split quotes

download:
	$(MAKE) -C src download

split:
	$(MAKE) -C src split

quotes:
	$(MAKE) -C quotes

# Layer 2 morphology. LLM-built, so kept out of `all`; the TSV under morph/ is committed.
# The model is set in model.mk (included by morph/Makefile); override with `make morph MODEL=...`.
morph:
	$(MAKE) -C morph

# Layer 3 noun phrases. LLM-built, so kept out of `all`; the TSV under np/ is committed.
# The model is set in model.mk (included by np/Makefile); override with `make np MODEL=...`.
np:
	$(MAKE) -C np

clean:
	$(MAKE) -C src clean
	$(MAKE) -C quotes clean

.PHONY: all download split quotes morph np clean
