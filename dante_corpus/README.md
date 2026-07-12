# dante_corpus

Source text library for Dante's *Divina Commedia*. Provides line-level access to
the Italian source, tokenization, quote-span (speech attribution) data, and the frozen
grammatical-analysis stack (morphology, noun phrases, dependencies — see PLAN.md).

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
dante-corpus text morph  <canticle> <reference> [--format text|json]
dante-corpus text np     <canticle> <reference> [--format text|json]
dante-corpus text dep    <canticle> <reference> [--format text|json]
```

Prints source lines, tokens, or a grammatical layer (morphology, noun phrases, dependencies)
for a reference range. `reference` is a canto number or `canto:start-end`, e.g. `1`, `1:1-12`.
Default format: `text`. `morph`/`np`/`dep` read the frozen artifacts under `morph/`, `np/`,
`dep/` (see their own READMEs); no model call happens at query time.

**Examples**

```bash
dante-corpus text lines  inferno 1
dante-corpus text lines  inferno 1:1-12 --format json
dante-corpus text tokens inferno 1:8-9
dante-corpus text morph  inferno 1:1-2
dante-corpus text np     inferno 1:1-2
dante-corpus text dep    inferno 1:1-2
```

Text format: `<no>: <text>` per line. Token format: `<no>: tok | tok | …`.

**`text morph`** prints one indented line per token: `word  lemma  pos  features  note`.

```
1: Nel mezzo del cammin di nostra vita
    Nel  in+il  preposition+article  m. sg.  contraction
    mezzo  mezzo  noun  m. sg.
    ...
```

**`text np`** prints noun phrases nested under their line, most-specific innermost. Each span
shows its text, id (`<line>.<ordinal>`), head token, and — when a Layer-4 `dep/` artifact exists
for the canto — its derived grammatical `role`.

```
1: Nel mezzo del cammin di nostra vita
    [mezzo del cammin di nostra vita]  (1.1) head=mezzo role=obl
        [cammin di nostra vita]  (1.2) head=cammin role=nmod
            [nostra vita]  (1.3) head=vita role=nmod
```

**`text dep`** prints one indented line per token: the Universal Dependencies relation and the
head it attaches to (as `word (line.token)`); the sentence root has no head.

```
2: mi ritrovai per una selva oscura,
    mi         expl       -> ritrovai (2.2)
    ritrovai   root
    per        case       -> selva (2.5)
```

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
morph/     <canticle>/NN.tsv    Layer 2: per-token morphology + lemma (see morph/README.md)
np/        <canticle>/NN.tsv    Layer 3: noun phrases (see np/README.md)
dep/       <canticle>/NN.tsv    Layer 4: dependency relations (see dep/README.md)
```

### XML format (`quotes/<canticle>.xml`)

Each `<q>` element has these attributes:

| Attribute | Description |
|-----------|-------------|
| `id`      | Unique span id: `<canto>:<start_line>[A-Z]` |
| `line`    | Line range: `N` (single) or `N-M` (multi-line) |
| `col`     | Column range: `scol-ecol` (0-based offsets of the opening/closing quote chars on their respective lines) |
| `marker`  | Opening+closing quote pair, e.g. `«»` or `""` |
| `head`    | Disambiguating leading tokens (only when two spans share a start line) |

Nested `<q>` elements represent embedded quotes (direct children only; deeper nesting is recursive).

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
canto.morph() -> dict[int, tuple[MorphRow, ...]]   # Layer 2, line no -> per-token rows
canto.np()    -> tuple[NPSpan, ...]                # Layer 3, nested forest
canto.dep()   -> dict[int, tuple[DepRow, ...]]     # Layer 4, line no -> per-token rows
```

`morph`/`np`/`dep` load the frozen build-time artifacts (see [`morph/README.md`](../morph/README.md),
[`np/README.md`](../np/README.md), [`dep/README.md`](../dep/README.md)); no model call happens on
these calls, and they raise `FileNotFoundError` if the canto's artifact hasn't been built.

```python
@dataclass(frozen=True)
class QuoteSpan:
    quote_id: str
    start_line: int
    end_line: int
    start_col: int            # 0-based column of the opening quote char on start_line
    end_col: int              # 0-based column of the closing quote char on end_line
    marker: str               # opening+closing pair, e.g. "«»" or "''"
    head: str | None          # disambiguating head tokens (if needed)
    children: tuple[QuoteSpan, ...]
```

```python
@dataclass(frozen=True)
class MorphRow:  # Layer 2 — one per Layer-1 token, aligned 1:1
    word: str
    lemma: str = ""
    pos: str = ""
    gender: str = ""    # closed: m. / f. / n.
    number: str = ""    # closed: sg. / pl.
    person: str = ""    # closed: 1 / 2 / 3
    tense: str = ""
    mood: str = ""
    note: str = ""       # e.g. contraction / apocope / elision
```

```python
@dataclass(frozen=True)
class NPSpan:  # Layer 3 — noun phrase, over-inclusive, single-line
    line: int
    start: int   # 1-based token index of first token (inclusive)
    end: int     # 1-based token index of last token (inclusive)
    head: int    # 1-based token index of the head (start <= head <= end)
    text: str    # verbatim source substring spanning [start, end]
    np_id: str   # derived at serve time: f"{line}.{ordinal}"
    children: tuple["NPSpan", ...]  # nested NPs, by span containment
```

```python
@dataclass(frozen=True)
class DepRow:  # Layer 4 — one per Layer-1 token (incl. bare pronouns not in any NP)
    line: int
    token: int       # 1-based alpha-token index within `line` (matches Line.tokens order)
    word: str
    deprel: str      # Universal Dependencies relation, or "root"
    head_line: int   # 0 together with head_token == 0 marks the sentence root
    head_token: int
```

Helpers in `dep.py`: `index(canto.dep()) -> dict[tuple[int, int], DepRow]` builds a
`(line, token)` lookup; `np_role(span, idx) -> str` derives an `NPSpan`'s grammatical role from
that index (used by `text np`'s `role=` column).

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
