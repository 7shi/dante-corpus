URL = https://www.gutenberg.org/ebooks/1000
TARGET = pg1000.txt
CANTICLES = inferno purgatorio paradiso

all: split

download: $(TARGET)

$(TARGET):
	wget --trust-server-names $(URL).txt.utf-8 -O $(TARGET)

split: $(TARGET)
	uv run split.py

clean:
	rm -f $(foreach c,$(CANTICLES),$(wildcard $(c)/*.txt))

.PHONY: all download split clean
