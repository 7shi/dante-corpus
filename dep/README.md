# dep — Layer 4: dependency / grammatical role

Every token's clause function and the head token it attaches to — the next layer of the
grammatical stack ([PLAN.md](../PLAN.md)) after noun phrases. It uses **Universal Dependencies
(UD)** relation labels. It makes **no** interpretive judgment (entity roles, coreference, frame,
closed relation vocabulary) — those stay with the consumer projects; Layer 4 only exposes the
text's own syntactic structure.

**Status: implemented and built.** All 100 cantos are committed. `--check` across the full corpus:
**0 hard, 0 soft** violations (see *Check* below for the breakdown, and
[dep/CORRECTIONS.md](CORRECTIONS.md) for the correction history — frozen-vocabulary adjustment,
deterministic respelling cleanup, LLM `--fix` regeneration, the `RELCL_HEAD` substantivization
flag, one hand-corrected mis-attachment, the subject/head agreement rule, and the six exclusions
plus two `note` flags that closed its residue).

## What it does

One LLM pass per **parse unit** (a sentence, or a sentence fragment for unusually long sentences —
see *Design decisions*) emits a Markdown table, one row per token, with columns
`Line | Token | Word | Deprel | Head Line | Head Token | Head Word`. Unlike Layer 2/3, which give
the model free-text source lines and align its output back to tokens by substring search, Layer 4
gives the model an authoritative **numbered token list** (`line.token word (POS)`, POS from
Layer 2) up front and has it *cite* indices back. A dependency row names two positions; free-text
matching two words per row — against a source line full of repeated `che`/`e`/`si` — would be far
more ambiguous than Layer 2/3's single-word alignment. The `Word`/`Head Word` table cells are kept
only as build-time verification anchors (a disagreement means the model mis-cited an index); they
are not stored in the frozen artifact. The generation driver lives in this directory (`dep/dep.py`);
the parsing, resolution, validation, and I/O it depends on stay in the shared package
(`dante_corpus/dep.py`), which is what the runtime API consumes.

Three things PLAN.md asks for are deliberately **derived, never stored**:

- **Enjambed attachment.** A head may be on a different line than its dependent (a subject on one
  line, its predicate on the next) — this is what rejoins Layer 3's single-line noun phrases across
  enjambment. A noun phrase's clause function is simply the deprel of the Layer-4 row at
  `(span.line, span.head)` — see `np_role()` in `dante_corpus/dep.py`, joined at serve time.
- **Relative-pronoun antecedents.** UD encodes them structurally: a relative clause's verb attaches
  to its antecedent noun via `acl:relcl`, and the relative pronoun gets its own role inside the
  clause. So PLAN.md's "relative-pronoun antecedents resolve to an in-scope NP" becomes the soft
  check that every `acl:relcl` head is a nominal Layer-2 POS — or carries the `RELCL_HEAD` note
  flag for hand-verified substantivized exceptions (see [CORRECTIONS.md](CORRECTIONS.md)) — rather
  than anything stored.
- **Pronoun mentions.** Bare clitic / relative / personal pronouns are deliberately not Layer-3
  NPs; here each is just an ordinary token row with a deprel and a head. A consumer enumerates
  every pronoun mention by joining Layer-2 POS (`PRON`) with the Layer-4 role — no separate
  mention list is stored.

## Output

`dep/<canticle>/NN.tsv` — one tab-separated row per alpha token: `line  token  word  deprel
head_line  head_token`. `token`/`head_token` are 1-based indices matching `Line.tokens` order
(the same indexing Layer 2/3 use). The sentence's main predicate takes `deprel = root` with
`head_line = head_token = 0`; no other row uses that pair. Head words are not stored (derivable
via `(head_line, head_token)`). Unlike Layer 3, **no sentinel is needed**: every source line has
at least one alpha token, so "rows present for this line" already means "processed". Example for
*Inferno* I.1–3:

```
line	token	word	deprel	head_line	head_token
1	1	Nel	case	1	2
1	2	mezzo	obl	2	2
1	3	del	case	1	4
1	4	cammin	nmod	1	2
1	5	di	case	1	7
1	6	nostra	det:poss	1	7
1	7	vita	nmod	1	4
2	1	mi	expl	2	2
2	2	ritrovai	root	0	0
2	3	per	case	2	5
2	4	una	det	2	5
2	5	selva	obl	2	2
2	6	oscura	amod	2	5
3	1	ché	mark	3	6
3	2	la	det	3	4
3	3	diritta	amod	3	4
3	4	via	nsubj	3	6
3	5	era	aux	3	6
3	6	smarrita	advcl	2	2
```

Line 3 token 6 (`smarrita`) heads back to line 2 token 2 (`ritrovai`) — a cross-line attachment,
exactly the enjambment case PLAN.md calls out.

## Check

`--check` validates every committed artifact against the deterministic tokens, with **no model
call** (`validate_unit`):

- **Hard** (the structural bar): every line has exactly one row per token, in order (`count`); each
  row's word matches its token, elision spelling tolerated via `morph.strip_word_punct` as Layer 3
  does (`word`); every head cites an in-unit `(line, token)` position or is the `(0, 0)` root
  sentinel, consistently with `deprel == "root"`, and no token is its own head (`head`); the head
  chain from every token reaches a root with no cycle (`cycle`); the unit has at least one root
  (`root`). `0 hard` is required before an artifact is trusted.
- **Soft** (reported, not enforced; measure-then-freeze, matching Layer 2/3's policy):
  - **Deprel vocabulary** — `deprel` must be one of the frozen `DEPRELS` (UD v2 universal relations
    plus the subtypes used by Italian UD treebanks; `dep` is kept as UD's own escape hatch).
  - **Multiple roots per unit** — expected for `;`/`:`-sub-split long sentences (see *Design
    decisions*), so reported rather than hard-failed.
  - **Non-nominal `acl:relcl` head** — only checked when Layer-2 morphology is present; flags a
    relative clause whose antecedent's POS is not nominal and does not carry the `RELCL_HEAD` note
    flag (a likely mis-attachment; see [CORRECTIONS.md](CORRECTIONS.md)).
  - **More than one `obj` per predicate** — UD does not allow it: coordinated objects attach the
    later conjuncts to the first with `conj`, and a secondary predicate over an object is `attr`
    (the corpus's frozen label; see *Design decisions*). A flattened pair is therefore a mis-parse,
    not a second house style — the corpus already uses the UD shape everywhere else. Opened and
    closed in one round (203 predicates → 0); see [CORRECTIONS.md](CORRECTIONS.md).
  - **Subject/head agreement** — only checked when Layer-2 morphology is present: an
    `nsubj`/`nsubj:pass` whose person or number contradicts its **finite** head's. Italian
    agreement is obligatory, so the two frozen layers cannot both be right: either the attachment
    is a mis-parse (a predicate nominal, a vocative, a dislocated topic, or the subject of a
    *different* clause) or one of the two Layer-2 rows carries the wrong feature. Which side is
    wrong is not mechanically decidable, so the position is reported, never repaired. **Twelve
    exclusions**, all cases where the two rows genuinely need not match. Six were established when
    the rule opened: a non-finite head (it asserts nothing), a relative/interrogative pronoun
    subject (`che`/`chi`/`cui`/`quale` take their person from the antecedent), a coordinated
    subject (agreement is with the whole coordination), a head carrying more than one subject, a
    fused token whose verb part is non-finite (its `person` is the enclitic's), and a 1st/2nd
    person **plural** head (a singular nominal may name one member of the group: "e io con lui /
    volgemmo"). Six more closed the residue in 2026-08-14: a hand-verified `AD_SENSUM`/`FOREIGN`
    flag on either Layer-2 row, a distributive subject (`ciascuna`) under a plural head,
    coordination *inside* the subject phrase ("l'uno e l'altro coro"), a comitative `con`-phrase
    on a plural head, a plural subject quantified into one measure ("cento miglia … sazia"), an
    `attr` predicate nominal the copula agrees with instead ("La prova … son l'opere"), and an
    impersonal `si` with a postposed plural subject ("non si convenia più dolci salmi"). Each of
    the six was measured corpus-wide before it was written and touches **no** pair the rule calls
    "agree", so Layer 5's Tier-B repairs keep every position they had. Opened 2026-08-07 at
    **173** positions (106 person, 67 number), worked to **18** in one round and to **0** in a
    second; see [CORRECTIONS.md](CORRECTIONS.md).

**Measured over the full 100-canto build** (`--check`): **0 hard, 0 soft** — every class at 0,
including the agreement rule, whose 18-position residue was closed on 2026-08-14: one real
mis-attachment corrected (purgatorio 26:147, Occitan `sovenha vos`, where `vos` is the experiencer
and not the subject), ten positions taken by the six new exclusions above, and seven positions
closed by `AD_SENSUM`/`FOREIGN` flags on **70** Layer-2 rows — the two classes (notional agreement
with a collective, and non-Italian text) no structural rule can state without importing a lexicon
or a language identifier, so they were read against their terzine and flagged by hand, exactly as
`NO_NP`/`CONT_NEXT` were in Layer 3. `FOREIGN` marks every token of a non-Italian passage, not
only the tokens a violation happened to name: it is a property of the token, not of the check. See
[CORRECTIONS.md](CORRECTIONS.md) for the full path from the initial pilot measurement (636 soft)
down to this: the `attr` vocabulary freeze, `--fix-labels`' deterministic respelling cleanup, the
LLM `--fix` regeneration pass, the `RELCL_HEAD` substantivization flag, and one hand-corrected
mis-attachment (inferno 19:73-74, an `acl:relcl`/`nsubj` chain that had attached to a passive
participle instead of its more plausible nominal antecedent), and the 203 multiple-`obj` predicates
that rule opened and closed.

The build retries a parse unit (max 2) before giving up on the canto; there is **no per-line
fallback** — a lone line cannot host cross-line heads, so the parse unit is the smallest thing
worth retrying (contrast Layer 3's per-line fallback). Each unit's rows are written back to the TSV
as soon as they validate, so an interrupted run resumes from its own output.

## Output recovery

Local models occasionally produce incomplete or split output. Two recovery steps (the shared
pattern, see [PLAN.md](../PLAN.md)) run before every resolution attempt:

**1. Table merging (`_merge_tables`)** — a model that restarts the table mid-output with a fresh
header/separator is merged back into one continuous table.

**2. Multi-turn continuation (`_continue_if_missing`)** — if any listed token got no row (the table
was likely cut off), the driver sends a follow-up turn on the same `llm7shi.Client` session naming
the missing `line.token word` entries and asking it to continue; the response is merged before
resolution is retried.

## Design decisions

- **Parse unit = sentence, not a fixed-size chunk.** A dependency tree needs every head to resolve
  within its chunk, so lines are grouped by sentence (`dep.sentence_groups`) rather than sliced at a
  fixed line count as Layer 2/3 do. A unit ends at a line whose *final character* is `.`/`!`/`?`
  (sentence-final punctuation in this edition follows a closing guillemet, e.g. `elegge!».` ends in
  `.`; a line ending in a bare `»`/`'` is an embedded quote transition and does not break). Measured
  over all 100 cantos: sentence length is mode 3/6 lines, 99.7% <= 12; the remaining long sentences
  (up to 24 lines on `.`/`!`/`?` alone) are sub-split greedily at line-final `;`/`:` (with those
  included, the corpus max is 12) — `MAX_UNIT_LINES = 12`. A unit with no soft break in its window
  is hard-split as a last resort. Each split-off segment becomes its own tree with its own root,
  which is why >1 root per unit is a soft check rather than hard.
- **The model cites indices, code does not search for text.** Inverting Layer 2/3's substring
  alignment: the code numbers every token up front (`line.token`), and the model's job is only to
  assign each a deprel and a head index. `Word`/`Head Word` are verification anchors, checked at
  build time, never stored.
- **Head stored as a `(head_line, head_token)` pair**, not a flat sentence-position id — this keeps
  every row joinable with Layers 1–3 by key alone and makes the artifact independent of how a
  sentence happens to be segmented into parse units.
- **No sentinel row.** Contrast Layer 3 (an NP-less line needs a marker to distinguish "processed"
  from "pending"): every line has >= 1 alpha token, so a line with any rows present is, by
  construction, fully processed.

## Things to watch

- One known long sentence (Purgatorio 23) ends a mid-sentence line in a bare `'`-quoted exclamation
  (`diè di becco!'`); the splitter treats it as an embedded quote and does not break there, merging
  what a human reader would call two sentences into one parse unit. Harmless under the multi-root
  soft policy, but worth knowing if a `--check` soft count spikes for that canto.
- Mid-line `.`/`!`/`?` (rhetorical questions, quote transitions within a line) are ignored by
  design — only the line's *final* character is a sentence boundary, keeping every parse unit
  line-aligned so the resume/checkpoint machinery stays identical to Layer 2/3's.

## Model

Build-time only, set in [`../model.mk`](../model.mk) (the `vendor:name` form routed by `llm7shi`),
overridable with `make dep MODEL=...`. Dependency parsing is reading-bound like Layer 3, so the
strongest available model should be used and measured before freezing (PLAN.md). The model is a
build tool whose output is frozen and round-trip-checked; consumers see a stable asset.

## Usage

```bash
make -C dep                          # build all three canticles (model from model.mk)
make -C dep MODEL=ollama:gpt-oss     # override the model
make -C dep check                    # validate artifacts, no model call
make -C dep fix-labels                # relabel off-vocabulary respellings, no model call
make -C dep fix                      # regenerate parse units carrying soft violations

uv run dep/dep.py inferno [-c 1] [-m MODEL] [--chunk 12] [--force] [--check] [--clean] [-n]
uv run dep/dep.py inferno purgatorio paradiso --fix-labels   # relabel respellings, no model call
uv run dep/dep.py inferno -m ollama:gpt-oss --fix            # regenerate flagged units
```

Consumers read it deterministically via `Canto.dep()` (line-number -> `DepRow` tuples) or the CLI
`dante-corpus text dep inferno 1:1-3` (`--format json` for the row dicts, `head_word` included for
readability). `dante-corpus text np` shows each noun phrase's `role=` (its head token's deprel)
whenever a Layer-4 artifact for that canto exists.
