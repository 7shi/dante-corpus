include ../model.mk

CANTICLES = inferno purgatorio paradiso

all: np

np:
	uv run np.py $(CANTICLES) -m $(MODEL)

check:
	uv run np.py $(CANTICLES) --check

.PHONY: all np check
