CANTICLES = inferno purgatorio paradiso

all: quotes

quotes:
	uv run quotes.py $(CANTICLES)

clean:
	rm -f $(foreach c,$(CANTICLES),$(c).xml)

.PHONY: all quotes clean
