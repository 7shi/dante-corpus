# quotes — nested speech structure

Per-canticle XML capturing the **nested structure of speech** in the *Commedia* — who quotes whom,
and the reported speech embedded inside that. It records only what the source punctuation already
marks (the quotation spans); it makes **no** judgment about *who* the speaker is — that attribution
stays with the consumer projects (e.g. dante-analyze).

## What it does

Generation is fully **deterministic** — no model. `quotes/quotes.py` scans the normalized
`src/<canticle>/NN.txt` character by character for nested quotation delimiters (`«»`, `‘’`, `“”`),
builds the nested span tree, and assigns each span a stable id:

- a span is `canto:line` (e.g. `1:65`);
- when several spans open on the **same line**, they take a suffix (`1:67A`, `1:67B`, …) plus a
  `head` attribute holding the shortest leading word prefix that disambiguates them.

The normalization in `src/` is what makes this reliable: it separates speech guillemets from
elision apostrophes (standardized to U+0027) so the scan never confuses `l'altra` with a quote.

## Output

`quotes/<canticle>.xml` — one file per canticle. Because generation is deterministic, the XML is a
**generated artifact** (git-ignored, rebuilt by `make`), not a committed one. Each `<q>` carries
its `id`, `line` (single or `start-end`), `col` range, and `marker`; nested speech nests as child
`<q>` elements. From `inferno.xml`:

```xml
<canticle name="inferno">
  <canto n="1">
    <q id="1:65" line="65" col="0-15" marker="«»"/>
    <q id="1:67" line="67-78" col="12-39" marker="«»"/>
    <q id="1:93" line="93-129" col="0-31" marker="«»"/>
  </canto>
</canticle>
```

## Check

Faithfulness is structural and enforced at build time: `build_tree` raises on a **mismatched** or
**unclosed** delimiter, so a canticle whose punctuation does not nest cleanly fails the build rather
than emitting a broken tree. The `src/` lines are also asserted to carry no leading/trailing
whitespace before scanning.

## Usage

```bash
make -C quotes                 # rebuild all three canticles' XML
uv run quotes.py inferno       # a single canticle
```

`quotes/` is part of the corpus's default build (`make` at the repo root runs `split quotes`), so
it is regenerated whenever the source changes.

Consumers read it deterministically via `Canto.quotes()` (the nested `QuoteSpan` tree) or the CLI
`dante-corpus quote show inferno 1` (`--format json` for the raw spans, `xml` for the canto subtree).
