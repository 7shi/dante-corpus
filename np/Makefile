include ../model.mk

CANTICLES = inferno purgatorio paradiso

all: np

np:
	uv run np.py $(CANTICLES) -m $(MODEL)

check:
	uv run np.py $(CANTICLES) --check

fix:
	uv run np.py $(CANTICLES) --fix -m $(MODEL)

.PHONY: all np check fix
