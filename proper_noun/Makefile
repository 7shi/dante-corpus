include ../model.mk

CANTICLES = inferno purgatorio paradiso

help: ## Show this help
	@grep -hE '^[a-zA-Z0-9_ -]+:.*## ' $(MAKEFILE_LIST) | \
		awk -F ':.*## ' '{printf "  %-12s %s\n", $$1, $$2}'

all: $(CANTICLES) aggregate ## Build all canticles and aggregate

inferno purgatorio paradiso: ## Extract proper nouns for one canticle
	uv run proper_noun.py $@ -m $(MODEL)

aggregate: ## Aggregate per-canto TSVs into proper_noun.tsv
	uv run aggregate.py

.PHONY: help all $(CANTICLES) aggregate
