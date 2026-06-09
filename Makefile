CANTICLES = inferno purgatorio paradiso

all: split quotes

download:
	$(MAKE) -C src download

split:
	$(MAKE) -C src split

quotes:
	uv run python -m dante_corpus.build_quotes $(CANTICLES)

clean:
	$(MAKE) -C src clean
	rm -f $(foreach c,$(CANTICLES),quotes/$(c).xml)

.PHONY: all download split quotes clean
