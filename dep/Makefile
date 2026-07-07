include ../model.mk

CANTICLES = inferno purgatorio paradiso

all: dep

dep:
	uv run dep.py $(CANTICLES) -m $(MODEL)

check:
	uv run dep.py $(CANTICLES) --check

fix-labels:
	uv run dep.py $(CANTICLES) --fix-labels

fix:
	uv run dep.py $(CANTICLES) --fix -m $(MODEL)

.PHONY: all dep check fix-labels fix
