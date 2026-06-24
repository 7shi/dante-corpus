CANTICLES = inferno purgatorio paradiso

all: split quotes

download:
	$(MAKE) -C src download

split:
	$(MAKE) -C src split

quotes:
	uv run python -m dante_corpus.build_quotes $(CANTICLES)

# Layer 2 morphology. LLM-built, so kept out of `all`; the JSON under morph/ is committed.
# Override MODEL to pick the local model, e.g. `make morph MODEL=ollama:gpt-oss`.
MODEL ?= ollama:gpt-oss
morph:
	uv run python -m dante_corpus.build_morph $(CANTICLES) --model $(MODEL)

morph-check:
	uv run python -m dante_corpus.build_morph $(CANTICLES) --check

clean:
	$(MAKE) -C src clean
	rm -f $(foreach c,$(CANTICLES),quotes/$(c).xml)

.PHONY: all download split quotes morph morph-check clean
