include ../../model.mk

CANTICLE = inferno
CANTO = 1

help:
	@echo "Layer 2 (generation 2, step 1: the split), layers/gen2/l2.py."
	@echo "Fixed to $(CANTICLE) $(CANTO) for now — the only canto generated so far"
	@echo "(layers/PLAN.md); override CANTICLE/CANTO once more are."
	@echo ""
	@echo "  make help   this message (the default target)"
	@echo "  make all    generate (resumes: skips lines already in the artifact)"
	@echo "  make check  diff the artifact against old Layer 2"
	@echo "  make clean  delete the run log — never the artifact (NN.tsv)"
	@echo ""
	@echo "MODEL is set in ../../model.mk; override with e.g. make all MODEL=..."

all: l2

l2:
	uv run python -m layers.gen2.l2 $(CANTICLE) -c $(CANTO) -m $(MODEL)

check:
	uv run python -m layers.gen2.l2 $(CANTICLE) -c $(CANTO) --check

clean:
	rm -f $(CANTICLE)/*.log

.PHONY: help all l2 check clean
