include ../model.mk

CANTICLES = inferno purgatorio paradiso

help: ## Show this help
	@grep -hE '^[a-zA-Z0-9_ -]+:.*## ' $(MAKEFILE_LIST) | \
		awk -F ':.*## ' '{printf "  %-12s %s\n", $$1, $$2}'

all: $(CANTICLES) ## Build all canticles

inferno purgatorio paradiso: ## Extract proper nouns for one canticle
	uv run proper_noun.py $@ -m $(MODEL)

.PHONY: help all $(CANTICLES)
