# dante_corpus

Source text library for Dante's *Divina Commedia*. Provides line-level access to
the Italian source, tokenization, and quote-span (speech attribution) data.

---

## CLI

```
dante-corpus <command> <action> [args] [--format ...]
```

### `list`

```bash
dante-corpus list canticles
dante-corpus list cantos <canticle>
```

Lists available canticles or canto numbers, one per line.

### `text`

```bash
dante-corpus text lines  <canticle> <reference> [--format text|json]
dante-corpus text tokens <canticle> <reference> [--format text|json]
```

Prints source lines or their tokens for a reference range.
`reference` is a canto number or `canto:start-end`, e.g. `1`, `1:1-12`.
Default format: `text`.

**Examples**

```bash
dante-corpus text lines  inferno 1
dante-corpus text lines  inferno 1:1-12 --format json
dante-corpus text tokens inferno 1:8-9
```

Text format: `<no>: <text>` per line. Token format: `<no>: tok | tok | …`.

### `quote`

```bash
dante-corpus quote show <canticle> <canto> [--format xml|json]
```

Prints the speech-quote tree for a canto. Default format: `xml`.

**Examples**

```bash
dante-corpus quote show inferno 1
dante-corpus quote show inferno 1 --format json
```

### `canto`

```bash
dante-corpus canto show <canticle> <canto> [--format text|json]
```

Prints all lines of a canto with line numbers and tokens. Default format: `json`.

**Examples**

```bash
dante-corpus canto show inferno 1
dante-corpus canto show inferno 1 --format text
```

---

## Directory layout

```
src/       <canticle>/NN.txt    Italian source lines (one line per file line)
quotes/    <canticle>.xml       Speech-quote tree (built by dante-build-quotes)
```

---

## Public API

### Corpus access (`api.py`)

```python
canticles() -> tuple[str, ...]
```
Returns the canticle names present on disk: a subset of
`("inferno", "purgatorio", "paradiso")`.

```python
cantos(canticle: str) -> tuple[int, ...]
```
Returns the canto numbers available for `canticle`, sorted.

```python
canto(canticle: str, number: int) -> Canto
```
Loads and returns a `Canto` object.

```python
ref(spec: str) -> tuple[Line, ...]
```
Looks up lines by a text reference such as `"inferno 1"` or `"inferno 1:1-12"`.
Format: `"<canticle> <canto>[:<start>[-<end>]]"`.

---

### Data classes

```python
@dataclass(frozen=True)
class Line:
    no: int          # 1-based line number within the canto
    text: str        # raw source text of the line
    tokens: tuple[str, ...]  # alpha-only tokens (cached_property)
```

```python
@dataclass(frozen=True)
class Canto:
    canticle: str
    number: int
```

`Canto` methods:

```python
canto.line(number: int) -> Line
canto.lines(start: int = 1, end: int | None = None) -> tuple[Line, ...]
canto.quotes() -> tuple[QuoteSpan, ...]
```

```python
@dataclass(frozen=True)
class QuoteSpan:
    quote_id: str
    start_line: int
    end_line: int
    marker: str               # opening+closing pair, e.g. "«»" or "''"
    head: str | None          # disambiguating head tokens (if needed)
    children: tuple[QuoteSpan, ...]
```

---

### Tokenizer (`tokenizer.py`)

```python
tokenize(text: str) -> list[str]
```
Splits Italian source text into tokens. Trailing apostrophes stay with the
preceding token (`m'`, `i'`, `ch'`); leading apostrophes start the next token
(`'l`, `'mpediva`). Non-alpha runs (spaces, punctuation) are separate tokens.

```python
has_alpha(text: str) -> bool
```
Returns `True` if the string contains at least one letter.
Useful for filtering punctuation tokens out of `tokenize` results.

**Example**

```python
from dante_corpus import tokenize, has_alpha, ref

lines = ref("inferno 1:8-9")
for line in lines:
    print(line.no, [t for t in tokenize(line.text) if has_alpha(t)])
```
