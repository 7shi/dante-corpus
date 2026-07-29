# dante_corpus

Source text library for Dante's *Divina Commedia*. Provides line-level access to
the Italian source, tokenization, quote-span (speech attribution) data, and the frozen
grammatical-analysis stack (morphology, noun phrases, dependencies, predicate-argument
skeleton, plus the pronoun-case annex — see PLAN.md), plus a content hash per canto×layer.

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
dante-corpus text case   <canticle> <reference> [--format text|json]
dante-corpus text np     <canticle> <reference> [--format text|json]
dante-corpus text dep    <canticle> <reference> [--format text|json]
dante-corpus text skel   <canticle> <reference> [--format text|json]
```

Prints source lines, tokens, or a grammatical layer (morphology, pronoun case, noun phrases,
dependencies, predicate-argument skeleton)
for a reference range. `reference` is a canto number or `canto:start-end`, e.g. `1`, `1:1-12`.
Default format: `text`. `morph`/`case`/`np`/`dep`/`skel` read the frozen artifacts under
`morph/`, `case/`, `np/`, `dep/`, `skel/` (see their own READMEs); no model call happens at
query time.

**Examples**

```bash
dante-corpus text lines  inferno 1
dante-corpus text lines  inferno 1:1-12 --format json
dante-corpus text tokens inferno 1:8-9
dante-corpus text morph  inferno 1:1-2
dante-corpus text case   inferno 1:1-12
dante-corpus text np     inferno 1:1-2
dante-corpus text dep    inferno 1:1-2
dante-corpus text skel   inferno 1:1-3
```

Text format: `<no>: <text>` per line. Token format: `<no>: tok | tok | …`.

**`text morph`** prints one indented line per token: `word  lemma  pos  features  note`.

```
1: Nel mezzo del cammin di nostra vita
    Nel  in+il  preposition+article  m. sg.  contraction
    mezzo  mezzo  noun  m. sg.
    ...
```

**`text case`** prints one indented line per pronoun: `token  word  case`. The artifact is
sparse, so a line with no pronoun prints only its text. A token fusing two pronouns carries one
case per pronoun, joined with `+` (`gliel'` -> `dative+accusative`).

```
2: mi ritrovai per una selva oscura,
    1  mi  accusative
8: ma per trattar del ben ch'i' vi trovai,
    7  i'  nominative
    8  vi  locative
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

**`text skel`** prints one block per predicate, indented under its line: the predicate's id
(`<line>.<ordinal>`) and word, then one row per argument — its role and the argument itself,
shown as the Layer-3 NP headed there (with that NP's id) when one exists, else as a bare
`line.token` position. A pro-drop subject prints as `∅`, with the person/number Layer 2 gives
the verb when it can be read. A relative-clause predicate prints its derived antecedent after
the word; like `dep`'s antecedents it is resolved at serve time, never stored.

```
2: mi ritrovai per una selva oscura,
    (2.1) ritrovai
        subj     ∅ (1 sg.)
        obl:in   [mezzo del cammin di nostra vita] (1.1)
        obl:per  [una selva oscura] (2.1)
6: che nel pensier rinova la paura!
    (6.1) rinova (antecedent [esta selva selvaggia e aspra e forte] (5.1))
        subj     6.1
        obj      [la paura] (6.2)
        obl:in   [pensier] (6.1)
```

Roles are **UD-derived, not semantic**: `subj`, `obj`, `iobj`, `attr`, `xcomp`, `ccomp`, and
`obl:<preposition lemma>` (bare `obl` when no preposition is recoverable). See
[`skel/README.md`](../skel/README.md).

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

### `hash`

```bash
dante-corpus hash <canticle> <canto> [--format text|json]
```

Prints the content hash (sha256) of every layer artifact that exists for the canto, one
`<layer>\t<hash>` row per line (`text`, `morph`, `np`, `dep`, `skel`, `case`). Consumers record these to
tell exactly which parse a derived artifact annotated, and to recompute only what a regeneration
actually changed — regenerating one canto changes only that canto's hashes. Default format:
`text`.

**Examples**

```bash
dante-corpus hash inferno 1
dante-corpus hash inferno 1 --format json
```

---

## Directory layout

```
src/       <canticle>/NN.txt    Italian source lines (one line per file line)
quotes/    <canticle>.xml       Speech-quote tree (built by dante-build-quotes)
morph/     <canticle>/NN.tsv    Layer 2: per-token morphology + lemma (see morph/README.md)
case/      <canticle>/NN.tsv    Layer-2 annex: pronoun case, sparse (see case/README.md)
np/        <canticle>/NN.tsv    Layer 3: noun phrases (see np/README.md)
dep/       <canticle>/NN.tsv    Layer 4: dependency relations (see dep/README.md)
skel/      <canticle>/NN.tsv    Layer 5: predicate-argument skeleton (see skel/README.md)
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
canto.case()  -> dict[int, tuple[CaseRow, ...]]    # Layer-2 annex, sparse: pronouns only
canto.np()    -> tuple[NPSpan, ...]                # Layer 3, nested forest
canto.dep()   -> dict[int, tuple[DepRow, ...]]     # Layer 4, line no -> per-token rows
canto.skel()  -> tuple[SkelTuple, ...]             # Layer 5, grouped tuples by (line, token)
canto.hashes() -> dict[str, str]                   # layer name -> sha256 of its artifact
```

`morph`/`case`/`np`/`dep`/`skel` load the frozen build-time artifacts (see
[`morph/README.md`](../morph/README.md), [`case/README.md`](../case/README.md),
[`np/README.md`](../np/README.md), [`dep/README.md`](../dep/README.md),
[`skel/README.md`](../skel/README.md)); no model call happens on
these calls, and they raise `FileNotFoundError` if the canto's artifact hasn't been built.
`hashes()` covers only the layers whose artifact exists, so a partially built canto simply
yields fewer keys.

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
class CaseRow:  # Layer-2 annex — one per pronoun-POS token (sparse, not per token)
    line: int
    token: int   # 1-based alpha-token index within `line` (matches Line.tokens order)
    word: str
    case: str    # closed: nominative / accusative / dative / genitive / ablative / locative;
                 # one value per pronoun component of the Layer-2 pos, joined with "+"
```

Helpers in `case.py`: `scope_slots(pos) -> int` decides from Layer 2's `pos` how many case
values a token carries (0 = out of scope); `case_index(canto.case()) -> dict[tuple[int, int], str]`
builds the `(line, token) -> case` lookup Layer 5's checker consumes as a third read. See
[`case/README.md`](../case/README.md).

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

```python
@dataclass(frozen=True)
class SkelArg:  # Layer 5 — one argument of a predicate
    role: str    # subj/obj/iobj/attr/xcomp/ccomp, or obl[:<preposition lemma>]
    line: int
    token: int   # 1-based token index; (0, 0) marks a pro-drop ∅ subject


@dataclass(frozen=True)
class SkelTuple:  # Layer 5 — one predicate with its arguments
    line: int
    token: int   # 1-based token index of the predicate
    word: str
    skel_id: str                  # derived at serve time: f"{line}.{ordinal}"
    args: tuple[SkelArg, ...]
```

The on-disk row (`skel/<canticle>/NN.tsv`, one line per predicate×argument) is `SkelRow`
(`line`, `token`, `word`, `role`, `arg_line`, `arg_token`); `canto.skel()` groups those rows into
`SkelTuple`s. A `token == 0` row is the "processed, no predicates" sentinel and is never served
as data.

Serve-time helpers in `skel.py` — all derived, never stored, mirroring `dep`'s antecedent policy:

```python
np_head_index(canto.np())  -> dict[tuple[int, int], NPSpan]   # (line, head) -> widest NP
arg_np(arg, np_idx)        -> NPSpan | None                   # the NP an argument heads
antecedent(pred, dep_idx)  -> tuple[int, int] | None          # acl:relcl head of a relative clause
morph_index(canto.morph()) -> dict[tuple[int, int], MorphRow]
children_index(canto.dep())-> dict[tuple[int, int], list[DepRow]]
pro_drop_features(pred, morph_idx, children_idx) -> str       # e.g. "1 sg." for a ∅ subject
```

`derive_unit(nos, dep_rows_by_line, morph_rows_by_line)` computes the same skeleton
**deterministically** from Layers 2-4; it is the build-time checker, not a serve path — the
served artifact is always the frozen, LLM-authored table (see [`skel/README.md`](../skel/README.md)).

### Content hashes (`hashes.py`)

```python
LAYERS = ("text", "morph", "np", "dep", "skel", "case")

artifact_path(layer: str, canticle: str, number: int) -> Path
artifact_hash(layer: str, canticle: str, number: int) -> str        # sha256 of the file bytes
canto_hashes(canticle: str, number: int) -> dict[str, str]          # every layer that exists
```

Backs `Canto.hashes()` and `dante-corpus hash`. See PLAN.md's *Versioning*.

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
