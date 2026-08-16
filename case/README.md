# case — pronoun case, a Layer-2 annex

The **grammatical case of every pronoun** in the *Commedia* — the one morphological feature
[`morph/`](../morph/README.md) omits, and the instrument Layer 5's parked clitic verdicts named
(see [CORRECTIONS.md](CORRECTIONS.md)'s *Pilot*). It annotates only what the Italian's own grammar determines; like every
other layer it makes no interpretive judgment and reads no external canon.

```
mi pesa            "it weighs on me"      -> mi is dative
m'avea 'mmonito    "he had warned me"     -> mi is accusative
```

The two are identical in form. Neither the token stream (Layer 1), the morphology as it stands
(Layer 2 has gender/number/person/tense/mood but no case), nor the dependency tree (Layer 4 — the
tree shape is the same and the deprel *is* the disputed judgment) distinguishes them.

**Not a sixth layer**, and **not a new `morph/*.tsv` column**: a permanent sibling directory, on
the same footing as `np/`, `dep/` and `skel/` relative to `morph/`. No existing artifact hash
moves, provenance stays visible, and `rm -rf case/` would return the repo to an untouched state.
A physical merge into `morph/*.tsv` was considered and **rejected** (2026-08-02) — the hash-blast-
radius and provenance arguments for a sibling directory hold regardless of the column's measured
quality, and every other layer already lives apart from `morph/` too; see
[CORRECTIONS.md](CORRECTIONS.md)'s *Step 5 — the merge decision* for the full reasoning.

**Not a lexicon.** The rejected alternative was importing a valency dictionary that says `pesare`
takes a dative and `ammonire` an accusative — that would bring an external authority into a
corpus whose whole premise is that every layer is a function of the Italian source alone. This
layer does not do that: it is one more Layer-2-style morphological column, authored the same way
every other Layer-2 column was — an LLM reading the Italian source and nothing else, frozen as
TSV, round-trip checked, content-hashed. The [`../PLAN.md`](../PLAN.md) *Neutrality audit*
invariant constrains the build prompt's *inputs* (no reference translation, no entity list, no
external canon); a model reading case from the Italian alone meets it on the same terms `pos` and
`deprel` already do.

## Status

**The annex is complete and closed (2026-08-02), and still gets hand corrections when a position
is a plain error.** All 100 cantos, `--check` **0 hard**, **13158 pronoun tokens, 13224 case
values**. Step 4's hand-verified Layer-4 correction round spent all 510 adjudication candidates
across three slices (215 positions / 270 rows in `dep/`); step 5 settled the oblique tail (fold
nothing), ran the owed `morph/`-driven chunk regeneration, tried and rejected two blind
regenerations under a corrected prompt (two named weaknesses recorded rather than chased past
their budget), and closed the merge decision above — no schema change, `case/` stays a permanent
sibling directory. Step 6 (2026-08-03) then hand-corrected the 50 bare-clitic
accusative/dative contradictions Step 4 had already identified but never written into
`case/*.tsv` (that round only ever edited `dep/`); **"frozen" means no wholesale regeneration**,
not that a demonstrable per-position error stands uncorrected. Steps 7-9 then worked through the
remaining named residue shape by shape, closing the last one (`accusative`-vs-`nsubj`) on
2026-08-03; Step 10 the same day spent four more corrections that Layer 5's rule-U round surfaced
(see [`../skel/CORRECTIONS.md`](../skel/CORRECTIONS.md)'s *Phase 5r*, which also made this column
a third read in Layer 5's checker). `--stats` now reports **32 contradictions / 26 impossible
pairings** against `dep`,
recorded as measured residue: every one of them is a position read individually and left standing
for a stated structural reason (accusative-and-infinitive, fused infinitive+clitic, free relatives,
causative causees, impersonal dative-experiencers, Latin quotations), not an uninspected remainder.
See [CORRECTIONS.md](CORRECTIONS.md) for the full history.

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

Measured on the frozen `morph/*.tsv`. The scope was **13112 tokens over 8540 lines** when the
artifact was built and frozen at `0027494`; two Layer-2 correction rounds have moved it since —
2026-08-02's, and 2026-08-09's membership round, which added 32 rows over 12 new lines (see
[`../morph/CORRECTIONS.md`](../morph/CORRECTIONS.md) and
[`CORRECTIONS.md`](CORRECTIONS.md)). The scope is what `--check` counts against, so a Layer-2
retag into or out of a pronoun POS shows up there as a `[count]` mismatch until the row is written:

| population | tokens | lines |
|---|---|---|
| Layer-2 tokens | 101601 | 14233 |
| **pronoun-POS tokens (in scope)** | **13158** | **8558** |
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

**`ablative` is a residual class, and the tail was the vocabulary's open question.** 93% of the
pilot's answers were `accusative` or `dative` — the question the annex exists to answer — and the
whole oblique tail was 6%, which is also exactly where the pilot found the model unstable. A
value earns its place in this vocabulary if it changes the **slot** the pronoun fills, not what
the oblique *means*.

Step 3 measured it and Step 5 closed it, and the answer is **fold nothing**. The deciding
evidence is the `dep` deprel
distribution, which `--stats` now prints alongside the word forms:

| deprel | `ablative` 1805 | `genitive` 267 | `locative` 81 |
|---|---|---|---|
| `obl` | 1481 | 59 | 45 |
| `nmod` | 94 | 139 | — |
| `det:poss` | 0 | 50 | — |

`genitive` is **earned** — 71% of it is adnominal, and `det:poss` is a slot `ablative` fills zero
times (`lor danno`, `il senso lor`, `le gambe loro` are possessive determiners, not obliques).
`locative` is **earned too** (settled 2026-08-02), but not by the deprel test — by that test it
opens no slot at all: **there is no deprel `locative` fills that `ablative` does not**, and its 2%
adposition rate against `ablative`'s 74% is only a clitic-vs-tonic confound (against `ablative`'s
own bare clitic `ne` the profiles converge). What earns it is that **Layer 2's `lemma` collapses
the readings of its word forms and nothing else in the stack separates them**: the lemma `vi`
spans `locative` 44 / `accusative` 21 / `dative` 15 / `reflexive` 4, and the lemma `ci` spans
`locative` 21 / `accusative` 29 / `dative` 24 / `reflexive` 15 / `nominative` 5. Whether a given
`vi` means *there* or *to you* is recorded **only** in this column. The deprel test answers "does
this value open a slot"; for a value whose work is splitting one form into several readings, that
is the wrong question. See [CORRECTIONS.md](CORRECTIONS.md)'s *Step 5 — the `locative` question*,
which records the fold verdict this round reached first and why it was wrong.

An earlier reading of the same tail recommended folding `genitive` into `ablative`, on the
grounds that its word forms are a subset of `ablative`'s. That was wrong — the same form under
two values is precisely what a case column records — and the argument, its refutation and the
lesson are kept in [CORRECTIONS.md](CORRECTIONS.md)'s *The subset argument was wrong*. **Word
forms do not decide this question; deprels do.**

`ablative` is the **model's own** word for the partitive/locative oblique class; the design
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
blindness is the design constraint the annex's whole value rests on (*Independence*, below): it is
what makes this a genuine **third independent read** that can indict Layer 4, rather than an
artifact manufactured to close Layer-5 violations.

### Independence — the design constraint that matters most

Layer 5 is valuable **because the LLM's skeleton is an independent read of the same text**: a
divergence can therefore indict Layer 4, not just the model. A case column can either strengthen
that or destroy it, depending entirely on how it is generated.

- **Wrong**: measure the disputed positions, then ask the model about *those positions*. That
  manufactures an artifact to close violations — the failure mode
  [`../dep/CORRECTIONS.md`](../dep/CORRECTIONS.md) already names (*pick the deprel the corpus uses
  for that word, not the one that closes the violation*), applied one level up.
- **Right**: generate case for **every pronoun in the corpus, blind** to which positions are
  disputed, in a pass that is shown neither `dep/` nor `skel/`. The result is then a genuine third
  independent read, and `dep` / `skel` / `case` can be adjudicated 2-of-3.

This is what the build actually did (see *Status* above), and it is why a contradiction with `dep`
is a candidate for a hand-verified Layer-4 correction round — never an automatic edit to
`case/*.tsv`, and never a checker exemption that silences a Layer-5 violation.

**Where this column *may* silence a Layer-5 violation is the opposite configuration**, and it is
the 2-of-3 adjudication the bullets above authorize: `case` and `dep` **agreeing** against the
LLM's skeleton. That is Layer 5's rule U (`skel._case_corroborated_role`, 2026-08-03) — it accepts
a `role_mismatch` only when this column corroborates the `dep`-derived role *and not* the LLM's,
and it is one-directional by construction, so a position where `case` dissents from `dep` is never
silenced by it; those go to a hand-verified round exactly as the paragraph above requires.

**The prompt matches the frozen artifact.** Two word-order rules — a relative pronoun is
nominative only when its clause has no other subject; a verb takes at most one direct object, so a
clitic beside an explicit object noun is the dative of possession — were tried for the `morph/`
merge's blind regeneration, against the two error shapes step 4 counted at corpus scale
([CORRECTIONS.md](CORRECTIONS.md), *Step 4, slice 3*). Both rounds were rejected against a verdict
rule fixed in advance, and the prompt was reverted to the version the frozen artifact was actually
built under — see [CORRECTIONS.md](CORRECTIONS.md)'s *Step 5 — the merge decision* and *the prompt
was reverted too*. The rule text and its rationale are kept in git history (`038d1ec`, `ffc8180`),
not in the live prompt.

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

**There is no deterministic checker for case** and this layer does not pretend otherwise. Every other layer has a
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

The candidate lists are truncated to the first 40 contradictions and 20 impossible pairings so
the report stays readable; **`--stats --full` lists every one** (510 as of the freeze), which is
what a correction round works from.

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
make -C case regen CANTICLES=inferno   # prompt change: drop the artifacts, then rebuild

uv run case/case.py inferno [-c SPEC] [-m MODEL] [--chunk 12] [--force] [--check] [-n]
uv run case/case.py inferno -m MODEL --log case.inferno.log   # parallel shells: own log each
```

`-c`/`--canto` selects which cantos to process: `1`, `11-20`, `12-` (from 12 on), `-20` (up to
20), or a comma-separated mix such as `1,3-5,11-`. It is the same selection syntax in every build
driver, and a spec matching no canto is a command-line error rather than a silent no-op.

Consumers read it deterministically via `Canto.case()` (line-number → `CaseRow` tuples, sparse) or
the CLI `dante-corpus text case inferno 1:1-12` (`--format json` for the raw rows). The artifact is
content-hashed like every other layer — `"case"` is **appended** to `hashes.LAYERS`, so no existing
hash moves — and `case.case_index()` gives the `(line, token) → case` shape Layer 5's checker
consumes as a third read. **Layer 5 is a consumer of this column, never its owner**: the
adjudication report itself belongs here.
