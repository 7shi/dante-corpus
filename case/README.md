# case — pronoun case, a Layer-2 annex

The **grammatical case of every pronoun** in the *Commedia* — the one morphological feature
[`morph/`](../morph/README.md) omits, and the instrument Layer 5's parked clitic verdicts named
([PLAN.md](PLAN.md)). It annotates only what the Italian's own grammar determines; like every
other layer it makes no interpretive judgment and reads no external canon.

```
mi pesa            "it weighs on me"      -> mi is dative
m'avea 'mmonito    "he had warned me"     -> mi is accusative
```

The two are identical in form. Neither the token stream (Layer 1), the morphology as it stands
(Layer 2 has gender/number/person/tense/mood but no case), nor the dependency tree (Layer 4 — the
tree shape is the same and the deprel *is* the disputed judgment) distinguishes them.

**Not a sixth layer**, and **not a new `morph/*.tsv` column**: a sibling directory, so no existing
artifact hash moves, provenance stays visible, and `rm -rf case/` returns the repo to an untouched
state. Merging into Layer 2 later is the natural end state if the column proves out; see
[PLAN.md](PLAN.md)'s *Why its own directory*.

## Status

Step 3 of [PLAN.md](PLAN.md) is **done**: the artifact is built for all 100 cantos, `--check` is
**0 hard**, and it is committed (`0027494`) — frozen *before* `--stats` joined it to `dep`, which
is the order [PLAN.md](PLAN.md)'s *Independence* section exists to enforce. **13112 pronoun
tokens, 13176 case values.** Step 4, the hand-verified Layer-4 correction round over the **461
contradictions and 49 impossible pairings**, is the open work.

The vocabulary and scope are **frozen**, and the
driver, the shared module, the serve surface and the tests exist. **Inferno 1 was built first** as
the smoke test, and it caught two things `--check` structurally cannot see (a wrong worked example
in the prompt, and the reflexive clitic having no home in the vocabulary); both are fixed and the
canto was rebuilt.

The corpus pass took four runs, all on 2026-07-31, and no residue was ever a model failure:

| run | `--check` | cause | fix |
|---|---|---|---|
| 1 | 1236 hard over 23 cantos | a chunk the model could not get past aborted the whole remaining canto, so ~23 genuine failures cost 192 of the 1340 chunks | the driver skips the failed chunk and carries on; pass `--log` to keep the responses |
| 2 | 70 hard over 19 cantos | Layer 2's `pos` undercounted its own `lemma` on 24 fused clitic clusters (`sen` = `si+ne`), so a right answer was rejected forever; and the model sometimes writes the `Word` cell as the clitic (`mi`) rather than the fused token (`parlami`) | corrected in [`../morph/CORRECTIONS.md`](../morph/CORRECTIONS.md); `_match` now also accepts the clitic a fused token ends in |
| 3 | 13 hard over 3 cantos | the same defect in shapes round 2 did not cover — the *lemma* undercounting too (`sen` with the lemma `si`), a three-part lemma under a two-part `pos` (`Vattene`), and `nol` = `non lo` demanding two cases for one pronoun | 14 more tokens, audited as a family; one of them also closed a Layer-5 soft violation (3551 → 3550) |

Run 4 re-requested the last 12 chunks — under 1% of the original 1340 — and all of them
validated. See [CORRECTIONS.md](CORRECTIONS.md)'s *Step 3 corpus pass* entries.

Worth carrying forward: **`--check` failing is not evidence the model is wrong.** A formal check
compares the answer against the frozen layers, so it fails whenever *either* side is at fault,
and on this layer the frozen side was at fault three runs running.

## Scope — every pronoun-POS token

Which tokens carry a case is decided mechanically from Layer 2's own `pos` column
(`case.scope_slots`), so the scope needs no hand-frozen list of word forms and imports no outside
authority. In scope: `pronoun`, `relative pronoun`, and every fused token whose `pos` names a
pronoun among its parts (`verb+pronoun` for an enclitic, `pronoun+pronoun` for a clitic cluster).

Measured on the frozen `morph/*.tsv`:

| population | tokens | lines |
|---|---|---|
| Layer-2 tokens | 101601 | 14233 |
| **pronoun-POS tokens (in scope)** | **13112** | **8540** |
| of which the clitic forms `mi ti si ci vi ne lo la li le gli` + elisions | 3710 | 3481 |

The clitic subset is what the Layer-5 adjudication needs, but the scope is the whole pronoun
population: it is the version with no arbitrary line to draw, it covers the tonic forms
(`cui`, `me`, `lui`, `altrui`, `lor`) the disputed *mirror* bucket contains, and it makes the case
of **every pronominal mention** queryable, which is worth something to consumers independently of
Layer 5's violation count. Cost at the default chunk size is **1340 calls** (see *Model and cost*).

A fused token carries **one case per pronoun component**, joined with `+` in reading order the way
Layer 2 already joins the lemmas of a contraction (`Nel` → `in+il`): `gliel'` → `dative+accusative`.
Counting the components is what makes those tokens checkable rather than ambiguous.

## Closed vocabulary

Eight values — six **frozen from the pilot's own answer census** rather than from a grammar book
(the same measure-then-freeze order every other layer used: 570 answers, no unmapped values), plus
two added deliberately. Both additions name a pronoun that fills **no argument slot of the verb**,
which is exactly what the pilot's clitic-argument population could not contain; see
[CORRECTIONS.md](CORRECTIONS.md):

| case | pilot census | typical bearer |
|---|---|---|
| `accusative` | 276 | direct object |
| `dative` | 252 | indirect object; the person something happens to |
| `ablative` | 28 | partitive / prepositional oblique — `ne` "of it", "from there" |
| `nominative` | 7 | subject |
| `genitive` | 5 | possessor |
| `locative` | 2 | `ci` / `vi` meaning "here" / "there" |
| `vocative` | — | direct address — `O tu che ...` |
| `reflexive` | — | a clitic referring back to the subject, or belonging to the verb — `mi volsi`, `si mosse`, impersonal `si` |

`reflexive` is the second value the census does not contain, added for the same structural
reason and on the evidence of the inferno-1 smoke test — 1411 of the 13112 in-scope tokens
(10.8%) are the reflexive / impersonal clitic Layer 4 tags `expl`, which fills no argument slot,
and with no home in the vocabulary the model split them `accusative` 6 / `nominative` 2. The name
is the corpus's own: Layer 2's `note` column already reads `reflexive` on 1271 pronoun tokens
(plus `impersonal` on 174). The boundary the prompt draws is participant-based, not
theory-based — a clitic that introduces nobody distinct from the subject is `reflexive`, and one
naming someone else keeps its ordinary case, so in `mi si fu offerto` the `si` is `reflexive`
while the `mi` is `dative`. See [CORRECTIONS.md](CORRECTIONS.md)'s *Step 3 smoke test*.

`vocative` is the first value the census does not contain, and it is **added rather than measured**.
The pilot sampled only disputed and control *clitic argument* positions, which structurally cannot
hold a term of address, so its silence is a property of that sample and not of the corpus: direct
address is pervasive in the poem, and the scope frozen here (every pronoun, not just clitics) walks
straight into it. Without the value the build would have to force `O tu che ...` into `nominative`.
The build prompt draws the line explicitly — a pronoun that is the verb's subject stays
`nominative` even in a sentence addressed to someone.

**`instrumental` is deliberately not a value.** The pilot produced it zero times out of 570 in
positions that could have yielded it; Italian inherits no instrumental form (Latin merged it into
the ablative); and the archaic comitatives `meco` / `teco` / `seco` (43 tokens corpus-wide, all
accompaniment) are ablatives. Splitting `ablative` into instrument / source / accompaniment would
be a *semantic* reading with no formal support in the Italian, which
[`../PLAN.md`](../PLAN.md)'s *Out of scope* assigns to the consumer — the contrast with
`vocative`, a syntactic distinction the line carries. `canon_case` maps `instrumental`,
`comitative`, `oblique` and `partitive` onto `ablative` to absorb drift.

**`ablative` is a residual class, and the tail is an open question.** 93% of the pilot's answers
were `accusative` or `dative` — the question the annex exists to answer — and the whole oblique
tail was 6%, which is also exactly where the pilot found the model unstable. A value earns its
place in this vocabulary if it changes the **slot** the pronoun fills, not what the oblique
*means*; by that criterion `genitive` (a `ne` meaning "of it" rather than "from there") is weak,
and it is frozen anyway only because folding it into `ablative` later is a mechanical rewrite of
the TSVs while dropping it now and being wrong would cost a corpus pass. `--stats` prints the
tail's share and the word forms carrying each value, so the verdict after step 3 is numeric. See
[CORRECTIONS.md](CORRECTIONS.md)'s *The oblique tail*.

`ablative` is the **model's own** word for the partitive/locative oblique class; [PLAN.md](PLAN.md)
anticipated `oblique`, and the census overruled it. The pilot's one real instability was where the
boundary between `ablative`, `genitive` and `locative` falls on `ne`/`vi` — a *labeling* boundary,
not a reading disagreement (the model was stably reading a third thing and varying in what to call
it), so it is settled in the build prompt's rules rather than left to the model. Near-synonyms the
pilot produced (`oblique`, `partitive`, `instrumental`) normalize onto `ablative` in `canon_case`.

## What it does

One LLM pass per chunk of source lines emits a Markdown table, one row per **marked** pronoun:

```
| Line | Word | Case |
```

The unit of work is the **parse unit** (`dep.sentence_groups`, derived from the source punctuation
alone — not from the `dep/` artifact), because the case of a clitic is decided by its governing
verb, which is frequently on another line. Consecutive units are merged up to `--chunk` lines per
call and a unit is never split. A chunk with no pronoun is never sent.

The prompt shows the passage line-numbered with every in-scope pronoun wrapped in `**…**` and
**nothing else** — no `dep/` row, no `skel/` row, no hint that a position is disputed. That
blindness is the design constraint the annex's whole value rests on ([PLAN.md](PLAN.md),
*Independence*): it is what makes this a genuine **third independent read** that can indict Layer 4,
rather than an artifact manufactured to close Layer-5 violations.

Alignment is a forward walk (`case.align_unit`): the expected sequence of positions is already
known exactly from Layer 2, so each expected position consumes the next table row naming it, and
rows naming nothing expected are dropped. A position no row reaches is left empty, which
`--check` reports as a hard violation — a truncated table fails loudly and the chunk is
re-requested rather than frozen half-filled.

## Output

`case/<canticle>/NN.tsv` — **sparse**: one row per pronoun, not per token, so a line without a
pronoun has no rows at all. `token` is 1-based over the alpha-only Layer-1 tokens of the line.

```
line	token	word	case
2	1	mi	accusative
6	1	che	nominative
8	7	i'	nominative
8	8	vi	locative
```

## Check

`--check` validates every committed artifact with **no model call** (`case.validate_line`). Every
check is **formal**, and all of them are hard:

- `count` — exactly one row per in-scope token, in token order, and none anywhere else;
- `word` — the row's word is the verbatim Layer-1 token at its index;
- `slot` — one case value per pronoun component of the Layer-2 `pos`;
- `tag` — every value is in the closed vocabulary above, and non-empty.

**There is no deterministic checker for case** and this layer does not pretend otherwise
([PLAN.md](PLAN.md), *There is no deterministic checker for case*). Every other layer has a
mechanical ground truth — Layer 3's spans must reproduce verbatim source substrings, Layer 4 is a
well-formedness-checkable tree, Layer 5 has `derive_unit`. Case has none. The only cross-check that
exists is `dep`'s `obj`/`iobj`, which is **the very judgment under adjudication**, so it is
deliberately kept out of `--check` and lives in `--stats` instead. This layer's correctness rests
on the model's self-consistency, which the kill-gate pilot measured before any of this was written:
**81% unanimity across three presentation variants on the disputed positions, zero three-way
splits, against 95% on a control** ([CORRECTIONS.md](CORRECTIONS.md)).

`--clean` drops every chunk holding a violation so the next build re-requests exactly those. A
position a truncated table never reached is left empty rather than guessed, so it shows up here as
`missing lines`; a chunk whose retries are all exhausted is **skipped, not fatal** — the build
carries on through the rest of the canto and the next run re-requests only the skipped chunks.

## Adjudication — `--stats`, and only after freezing

`--stats` prints the vocabulary census, the coverage, and the join against `dep`: `obj` should
correspond to `accusative`, `iobj` to `dative` and `nsubj` to `nominative`; it separately reports
*impossible pairings*, combinations no expected case covers but which still cannot both be right
(`obl` × `nominative`). `reflexive` against `obj` is deliberately **not** a contradiction — a true
reflexive object is defensible in both vocabularies. Every position where the mapping fails is a
**candidate for a hand-verified Layer-4 correction round** in the style of Phases 5i/5n — never an
automatic edit, and never a checker exemption that silences a Layer-5 violation. Layer 5's soft
count falls because `dep` got more correct, which is the mechanism every audit round in Phase 5
used.

The order is load-bearing and is the reason `--stats` is a separate mode: **generate, validate,
commit, *then* join against `dep`.** Looking at `dep` first, or narrowing the pass to the flagged
positions, would manufacture the artifact to close violations — the failure mode
[`../dep/CORRECTIONS.md`](../dep/CORRECTIONS.md) already names one level down. If cost pressure
ever suggests narrowing the pass, the correct response is to abandon the annex, not to narrow it.

## Model and cost

Build-time only, set in [`../model.mk`](../model.mk) and overridable with `make case MODEL=...`.
The pilot used **`google:gemma-4-31b-it`**, the model the production layers were built with; the
`ollama:` default there is the quantized local debug backend, for smoke tests.

`--chunk` trades calls against the risk of a truncated table. Measured pending-chunk counts over
all 100 cantos:

| `--chunk` | calls |
|---|---|
| 9 | 1772 |
| **12 (default)** | **1340** |
| 15 | 1069 |
| 18 | 888 |

For comparison, Layer 5's Phase 5q `--fix` pass was 1702 calls (≈28 h, 3-way parallel). The build
is resumable from its own output, so a run can be interrupted and restarted, and the three
canticles can be run in three shells in parallel.

## Usage

```bash
make -C case                           # build all three canticles (model from model.mk)
make -C case MODEL=google:gemma-4-31b-it
make -C case check                     # validate artifacts, no model call
make -C case stats                     # census + the post-freeze dep adjudication
make -C case clean                     # drop chunks with violations

uv run case/case.py inferno [-c 1] [-m MODEL] [--chunk 12] [--force] [--check] [-n]
uv run case/case.py inferno -m MODEL --log case.inferno.log   # parallel shells: own log each
```

Consumers read it deterministically via `Canto.case()` (line-number → `CaseRow` tuples, sparse) or
the CLI `dante-corpus text case inferno 1:1-12` (`--format json` for the raw rows). The artifact is
content-hashed like every other layer — `"case"` is **appended** to `hashes.LAYERS`, so no existing
hash moves — and `case.case_index()` gives the `(line, token) → case` shape Layer 5's checker
consumes as a third read. **Layer 5 is a consumer of this column, never its owner**: the
adjudication report itself belongs here.
