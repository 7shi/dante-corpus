include ../model.mk

CANTICLES = inferno purgatorio paradiso

all: dep

dep:
	uv run dep.py $(CANTICLES) -m $(MODEL)

check:
	uv run dep.py $(CANTICLES) --check

.PHONY: all dep check
