# Layer 3 soft-violation correction history

Layer 3 (`np/`) freezes its soft-check policy (`_can_head_np`/`_needs_np` in `dante_corpus/np.py`)
against a corpus-wide count, then works that count down to 0 through a sequence of hand reviews,
code fixes, and targeted `--fix` reruns (see [`README.md`](README.md)'s *Check* section for what
each check means and how `--fix`/`--fix-repeats`/`--fix-clitics` work). This file is the
chronological record of every pass, so the running count in `README.md` and `../PLAN.md` is
traceable back to what actually changed and why. Layer-2 mistags found along the way are recorded
in [`../morph/CORRECTIONS.md`](../morph/CORRECTIONS.md) instead — this file covers the Layer-3
side: code/policy changes, span fixes, and classification of what's left.

## Initial freeze and repeat-word alignment bug (2026-07-03)

The soft-check policy was measured once over all 100 cantos and frozen: **418** soft violations,
before any correction pass. (Two hard-failure mechanisms — elision-spelling drift and fused
enclitic pronouns not tokenized by Layer 1 — were found and fixed first so all 100 cantos could
complete generation; see `README.md`'s *What it does*.) The `che`/`ch'` review (below) ran
immediately alongside this first measurement, bringing the count to **382** (141 function-word
heads + 241 noun coverage gaps) by the time it was first reported as a checkpoint.

A first `--fix` pass improved only 16/276 lines — suspiciously low. Investigating showed ~30% of
the remaining coverage gaps weren't model misses at all: `align_chunk` collapsed every proposal
for a repeated word/phrase in one line (e.g. both `poco`s in `a poco a poco`) onto its *first*
occurrence, so the second was structurally uncoverable no matter how many times `--fix` re-asked
the model. `align_chunk` now tracks claimed occurrences per chunk-line so future builds align each
repeat to a distinct token run (see `README.md`'s *Things to watch*); `--fix-repeats`
(deterministic, no model call) repairs existing artifacts the same way — reassigning 204 duplicate
spans corpus-wide and clearing 80 of the then-276 soft violations for free.

A full-corpus `--fix` run after the repeat-word fix improved only 6 more lines (of ~180
attempted). Diagnosis: 162/174 of those lines came back with the byte-identical violation set —
the retry re-asks the same single-line prompt with no feedback about what was flagged, so it is
mostly re-rolling dice, not correcting a mistake. Two structural reasons this ceiling is expected
rather than a prompt bug: a flagged span's head is often *correct* (Dante using `un`/`el`
pronominally — 47 of the 89 remaining article-head violations were `un`/`una` alone), so no
re-generation can lower the count without deleting a legitimate NP; and several coverage gaps
(`fin che`, `inver'`, verb+clitic forms) are function words the model correctly declines to treat
as nouns — the flag traces to a Layer-2 POS question, not a Layer-3 omission. Soft count after
`--fix-repeats` and this `--fix` pass: **186** (104 function-word heads + 82 noun coverage gaps).

## `che`/`ch'` and `un`/`una` reviews (2026-07-03)

Every `che`/`ch'`-headed (36 cases) and `un`/`una`-headed (41 cases) function-word violation was
hand-reviewed against its terzina context — the Layer-2 mistag corrections are recorded in
[`../morph/CORRECTIONS.md`](../morph/CORRECTIONS.md)'s *`che`/`ch'` mistag correction* and
*`un`/`una` mistag correction* sections. On the Layer-3 side: 12 lines had a redundant
single-token NP for a genuinely-conjunction `che` removed directly from the frozen `np/` TSVs (4
left with no spans got the zero-NP sentinel), and one line (paradiso 31:8) had a Layer-3 alignment
mismatch — `align_chunk` matched a proposed span to the wrong occurrence of a repeated word across
two different phrases — fixed by reassigning the span. Soft count after the `un`/`una` review:
**139** (57 function-word heads + 82 noun coverage gaps).

## Function-word-head cluster review (2026-07-04)

The remaining 57 function-word-head violations were reviewed the same way (Layer-2 mistag
corrections in `../morph/CORRECTIONS.md`'s *Function-word-head cluster review*). On the Layer-3
side: 20 redundant single-token spans (duplicating an already-correct larger span) were removed,
plus three more purely-Layer-3 fixes (two duplicate `verso di quella...` spans, one wrong
span-head index on a Latin quotation). One case, paradiso 7:1 `Osanna`, was left as an accepted
soft violation with no fix on either layer (resolved later, see *Layer-2-POS-aware generation
hints* below). Soft count: **83** (1 function-word head + 82 noun coverage gaps).

## Noun-coverage-gap classification and `NO_NP` flag (2026-07-04)

The 82 noun-coverage-gap violations were classified by cause before fixing anything: `fin
che`/apocopated-preposition/`allotta` idioms (25, no real NP expected), two-token
proper-name/title pairs where Layer 3 picked only one word as head (29, a Layer-3 span-merge gap),
and single content words Layer 2 already tags correctly that Layer 3 simply never spanned (13,
including `animal` and `forme`, which first looked like adjective-mistag candidates but matched
established corpus convention on closer check). Only 11 were genuine Layer-2 mistags (see
`../morph/CORRECTIONS.md`'s *Noun-coverage-gap mistag pass*). Soft count: **72**.

The 25 idiom cases aren't a Layer-2 tagging error at all: Layer 2 correctly tags each token's POS
(`fin`→`noun`, `inver'`/`incontr'`→`noun`, `allotta`→`noun`), but the token only ever occurs as a
fixed piece of an idiom, never as a standalone referring expression — `_needs_np` has no way to
know that from POS alone. Rather than leave these as unexplained violations, each of the 25 rows
now carries a machine-readable `NO_NP` flag in its Layer-2 `note` (comma-separated alongside any
existing note, e.g. `apocope` → `apocope, NO_NP`); `_needs_np` splits `note` on `,` and treats a
POS that would otherwise need an NP as exempt if `NO_NP` is among the flags. Each of the 25 lines
was checked against its terzina context before flagging — a targeted, hand-verified exemption, not
a blanket rule for these word forms in general. Soft count: **47** (30 title/proper-name
span-merge gaps, 12 unspanned single content words, 3 `ben`/`bene` cases, the `dia` at paradiso
26:10, and the accepted `Osanna` exception).

## Layer-2-POS-aware generation hints resolve `Osanna` (2026-07-04)

The `Osanna` exception (function-word-head cluster review, above) is resolved not by a Layer-2
change but by making Layer 3's generation prompt aware of Layer 2's POS data in the first place.
`dante_corpus.np.non_content_tokens()` derives, from each line's Layer-2 rows, the tokens whose POS
can never head an NP (`_can_head_np`); `_try_align` (`np/np.py`) appends them to the prompt as a
"Function words (never choose as Head):" hint, with a matching `SYSTEM_PROMPT` rule and worked
example. Since `_try_align` backs both `build()` and `fix()`, this took effect for both without a
separate code path.

Running `--fix` with the new hint across all 47 then-flagged lines improved 4 of them: `Osanna`
itself (the model now nests a separate single-token `sabaòth` span instead of choosing `Osanna` as
head), plus three unrelated coverage gaps that incidentally picked up a nested single-token span
for their previously-unspanned noun (inferno 16:95 `Viso`, inferno 28:55 `fra`, paradiso 6:134
`Ramondo`). The other 43 lines regenerated under the new hint but were rejected by `--fix`'s
no-worse-off guarantee (same violation count, sometimes on a different token) and kept their
original artifact. Soft count: **43**.

## `Rife` mistag correction (2026-07-04)

The remaining 43 soft violations (all noun-coverage gaps) were classified by cause: 24 title/
proper-name span-merge gaps, 15 unspanned single content words, 3 `ben`/`bene`-before-infinitive
cases, and the `dia` at paradiso 26:10. Checking each against precedent elsewhere in the corpus
found exactly one genuine mistag, `Rife` (see `../morph/CORRECTIONS.md`). Soft count: **42**.

## `CONT_NEXT` split-word flag (2026-07-04)

The last case, paradiso 26:10's `dia`, is one word (archaic "divine") split across an enjambed
line break with `regïon` on the next line — Layer 2 already records this via lemma `regione` and
note `split word`. Since Layer 3 spans are single-line by design (`README.md`'s Layer 3 *Scope*
note), `dia` can never head a same-line NP — a structural impossibility, not a generation gap, the
same shape of problem `NO_NP` solves but for a different reason. A second, distinct flag
`CONT_NEXT` ("continues on next line") was added to the same comma-separated `note` convention —
`dia`'s note becomes `split word, CONT_NEXT`. `_needs_np` exempts a noun from coverage if either
`NO_NP` or `CONT_NEXT` is among its note's flags. Soft count: **41**.

## Eclipsed-head nouns: `--fix` rerun then a deterministic script (2026-07-04)

The remaining 41 lines are a single recurring shape: a noun that's the non-head half of a larger
2-token span — either a title/epithet word before a proper name (`ser`, `messer`, `mastro`, `San`,
`fra`, `donna`) whose span's head is the name, or the other half of a name/noun pair (`Argenti`,
`Guiglielmo`, `Magno`, `ben`/`bene`/`vero`, etc.) — never got its own single-token span. None are
Layer-2 mistags.

A `--fix` rerun over these 41 lines picked up 4 this way — the model nested a previously-missing
single-token span for the eclipsed noun (inferno 4:57 `legista`, inferno 20:116
`Michele`/`Scotto`, paradiso 16:119 `Ubertin`/`Donato`, purgatorio 13:128
`Pier`/`Pettinaio`/`orazioni`). Soft count: **37** (36 lines, one — paradiso 13:139 — with two
violations).

Rerunning `--fix` again over the remaining 36 lines did **not** converge further (`np/np.log`
showed all 36 unchanged, "not improved"): the model doesn't reliably add a redundant single-token
span for a word it already covered inside a larger span. Since every one is the same eclipsed-head
shape with no Layer-2 mistag among them, a small deterministic script closed the rest instead —
for every noun/proper-noun token flagged by `_needs_np` and not already a span's head, it appended
`NPSpan(line, i, i, i, tokens[i - 1])` and rewrote the artifact via `write_np`. This resolved all
37 in one pass, matching the classification exactly (paradiso 13:139 needed two). Soft count:
**0**.
