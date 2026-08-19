# Layer 3 soft-violation correction history

Layer 3 (`np/`) freezes its soft-check policy (`_can_head_np`/`_needs_np` in `dante_corpus/np.py`)
against a corpus-wide count, then works that count down to 0 through a sequence of hand reviews,
code fixes, and targeted `--fix` reruns (see [`README.md`](README.md)'s *Check* section for what
each check means and how `--fix`/`--fix-repeats`/`--fix-clitics` work). This file is the
chronological record of every pass, so the running count in `README.md` and `../PLAN.md` is
traceable back to what actually changed and why. Layer-2 mistags found along the way are recorded
in [`../morph/CORRECTIONS.md`](../morph/CORRECTIONS.md) instead — this file covers the Layer-3
side: span fixes, clitic mentions, and classification of what's left.

## 4 spans from the Layer-5 Paradiso 26-33 read (2026-08-17)

Found in the per-position read of Paradiso 26-33 (see
[`../skel/CORRECTIONS.md`](../skel/CORRECTIONS.md)). `np --check` stays **0/0**.

Two spans **dropped**, both drawn around a token Layer 2 had called a noun and the same read
retagged a verb (see [`../morph/CORRECTIONS.md`](../morph/CORRECTIONS.md)):

- `[tocchi]` (paradiso 28:13, 8-8) — the past participle of `toccare`;
- `[saper che tutti hanno diletto]` (paradiso 28:106, 3-7, head 3) — the infinitive of a modal
  periphrasis, whose `che`-clause is a complement clause and not part of any noun phrase.

One span **dropped** for the same reason at the other layer:

- `[mei che dinanzi vidi poi]` (paradiso 26:79, 2-6, head 2) — `mei` is the comparative adverb
  *meglio*, so there is no nominal head for the span to hang on.

Two spans **rewritten**:

- `[quel tanto]` (paradiso 29:112, 2-3, head 3) → `[quel]` (2-2, head 2). `tanto` is the
  correlative adverb of the "sì che" in 113, not the phrase's head; `quel` is the pronoun standing
  for the "verace fondamento" of 111.
- `[quantunque]` (paradiso 33:21, 1-1) → `[quantunque in creatura è di bontate]` (1-6, head 1). A
  free relative is one phrase, headed by the pronoun that opens it — the shape Layer 3 already
  draws at paradiso 21:130, and the one rules AI/DZ read when the clause is a conjunct of a
  coordination whose head lies outside it.

## 1 span dropped from the Layer-5 Paradiso 21-25 read (2026-08-17)

`[che raggio]` (paradiso 21:28, span 6-7, head 7) was drawn while Layer 4 read `che` as a
determiner of `raggio`. The same read corrected that — `che` is the relative pronoun `in` governs,
antecedent `color d'oro` (see [`../dep/CORRECTIONS.md`](../dep/CORRECTIONS.md)) — and Layer 3's own
scope rule keeps **bare relative pronouns out of noun phrases**, so the span is not over-inclusive
but wrong: it joins a pronoun of the matrix clause to the subject of the relative one. Dropped;
`[raggio]` (7-7) was already present as its own span, and rules AI/BR/DZ read span heads, so
leaving it would have made `che` and `raggio` each other's alternative name.

`np --check` stays **0/0**.

## 1 clitic-cluster enumeration from the Layer-5 Paradiso 1-5 read (2026-08-17)

`convienti` (paradiso 5:37) was retagged `convenire+ti` / `verb+pronoun` at Layer 2 (see
[`../morph/CORRECTIONS.md`](../morph/CORRECTIONS.md)), which makes the enclitic a pronoun Layer 3
must enumerate; `np --check` said so immediately ("token 1 'convienti' missing clitic mention
'+ti'"). Added `37 1 1 1 +ti`, the same one-token span `parvemi` (paradiso 1:79) already carries.
`np --check` back to **0/0**.

## 2 spans from the Layer-5 Purgatorio 31-33 read (2026-08-17)

Layer 3 is over-inclusive by design, and an over-wide span is normally left alone. These two are
not over-inclusive: neither is a noun phrase at all, and Layer 5's rules AI and DF read a span's
`head` as an argument's alternative name, so a span that is not a phrase makes two different
nominals equivalent.

- **inferno 18:30** `[la gente modo colto]`, head `gente` — "hanno a passar **la gente** **modo
  colto**" holds two objects of two different predicates, `gente` of `passar` and `modo` of
  `hanno`. Both correct halves were already present as their own rows; the outer span is dropped.
  It was making rule DF accept `gente` as the subject of `passar`, which is why the position's
  class changed under that rule and changed back under this fix.
- **purgatorio 33:26** `[suo maggior parlando]` / `[maggior parlando]` / `[parlando]`, all headed
  on `parlando` — a gerund verb, "dinanzi a **suo maggior** **parlando** sono", "are speaking
  before their superior". Replaced by `[suo maggior]` / `[maggior]`, headed on `maggior`, the
  nominal the multiword preposition `dinanzi a` governs.

`np --check` stays 0/0.

## One span from Layer 5's Purgatorio 16-20 read (2026-08-16)

`np/purgatorio/18.tsv` 117 `[villania nostra]` (start 2, end 3, head 2) moved to
`[nostra giustizia]` (3-4, head 4). "perdona / se **villania nostra giustizia** tieni" is "forgive
us if you take our justice for discourtesy": the possessive belongs to `giustizia`, the object,
not to `villania`, the predicative complement, and the Layer-4 attachment moved with it (see
[`../dep/CORRECTIONS.md`](../dep/CORRECTIONS.md)). `np --check` stays 0 hard / 0 soft; the Layer-5
position stays flagged, because the LLM read the object and the complement the other way round,
which is its own claim rather than a consequence of the span.

## Two spans from Layer 5's Purgatorio 11-15 read (2026-08-16)

`np/purgatorio/14.tsv` 69 `[qual]` (start 2, end 2, head 2) widened to `[qual che parte]`
(2-4, head 4). Layer 2 had read `parte` as the verb `partire`, so the phrase "da **qual che
parte**" ("from whatever side") had no nominal head and Layer 3 spanned only the determiner; with
`parte` retagged as a noun the span is the whole phrase (see
[`../morph/CORRECTIONS.md`](../morph/CORRECTIONS.md) and
[`../dep/CORRECTIONS.md`](../dep/CORRECTIONS.md)).

`np/purgatorio/14.tsv` 90 `[reda]` (4-4, head 4) added. "nullo / fatto s'è **reda** poi del suo
valore": `reda` is the noun *erede*, retagged from a past participle in the same read, and a noun
must head an NP. Found by `np --check` reporting it the moment the Layer-2 row changed.
`np --check` stays 0 hard / 0 soft.

## One span from Layer 5's Inferno 31-34 read (2026-08-16)

`np/inferno/34.tsv` 105 `[il sol tragitto]` (start 7, end 9, head 9) split into `[il sol]`
(7-8, head 8) and `[tragitto]` (9-9, head 9). "da sera a mane ha fatto **il sol tragitto**?" is
"has the sun made the passage", not "has [it] made the sun-passage": `il sol` is the subject of
`ha fatto` and `tragitto` its object. Found by the per-position read of Inferno 31-34's Layer-5
soft violations, and applied together with the matching Layer-4 rows (see
[`../dep/CORRECTIONS.md`](../dep/CORRECTIONS.md)). `np --check` stays 0 hard / 0 soft.


## Four clitic mentions from Layer 5's membership audit (2026-08-09)

Layer 2's membership round (see [`../morph/CORRECTIONS.md`](../morph/CORRECTIONS.md)) retagged two
tokens as fused clitic clusters — inferno 29:34 *sen* (`se+ne`, previously the preposition *senza*)
and purgatorio 12:48 *nel* (`ne+lo`, previously the contraction *in+il*). `clitic_mentions` derives
one synthetic `+lemma` span per pronoun component of a fused token straight from Layer 2, so both
tokens immediately owed two spans each and `np --check` reported 4 soft violations. Added
`34 6 6 6 +se` / `34 6 6 6 +ne` and `48 1 1 1 +ne` / `48 1 1 1 +lo`; no model call, and no other
span on either line was touched. Back to **0 hard / 0 soft**.

## Two spans from Layer 4's subject-agreement round (2026-08-07)

Layer 4's new subject-agreement check (see [`../dep/CORRECTIONS.md`](../dep/CORRECTIONS.md))
retagged two tokens as nouns in Layer 2, and `np --check` immediately flagged both as heading no
NP — correctly, because each is one:

- purgatorio 16:35 *fummo* (= *fumo*, smoke; had been read as 1pl of *essere*) — new span
  `35 5 5 5`.
- paradiso 14:23 *cerchi* (the noun, with *santi* now its adjective; had been read as a verb) —
  the span `li santi` (head *santi*) became `li santi cerchi` (head *cerchi*), and `santi` became
  `cerchi`.

`np --check` back to **0 hard / 0 soft**.

## The case annex's Layer-2 fallout: 5 hard / 96 soft back to 0/0 (2026-08-02)

Layer 3 had been at 0 hard / 0 soft since the eclipsed-head pass below, and it was **not**
re-measured while the `case` annex corrected Layer 2 three times (`880fc2e` and `a97b80e` in its
step 3, and the 2026-08-02 round in its step 5). It read **5 hard / 96 soft** when the whole stack
was finally checked. Nothing here is a Layer-3 build error: every violation is this layer's
artifacts being correct against the Layer 2 they were built on and stale against the Layer 2 that
now exists.

**94 of the 96 soft, and all 5 hard, are clitic mentions** — the `+lemma` spans `clitic_mentions()`
derives from Layer 2's compound POS. They move whenever a fused token is re-split (`sen` → `si+ne`,
`meco` → `me+con`) or re-read (`nol` from `non+ne` to `non+lo`, `seco` from `con+se` to `sé+con`).
The instrument was already here, in one direction only: `--fix-clitics` backfilled what Layer 2
implies and had no way to drop what it no longer implies, which is exactly what the 5 hard were.
It is now **symmetric** — it adds missing mentions and drops stale ones — and the hard check it
answers to was tightened at the same time:

- **The old hard check accepted any lemma component**, so `meco` carrying `+con` (`pronoun+
  preposition` / `me+con`) passed while naming the *preposition*. `_mention_lemmas()` now admits
  only the **pronoun** components of a genuine fusion, which turned that one silent case into a
  sixth hard violation before the fix ran. Result: **94 added, 6 removed, 43 cantos**.

**A deliberate limit: the drop side only touches hosts with a compound POS.** A full reconcile
would also have deleted **160** `+lemma` spans on ordinary single-token pronouns, and those turn
out to exist in exactly two cantos — **Inferno 18 (63) and 23 (97)**, and nowhere else in the
corpus. They are a canto-local build convention, not annex fallout: those two cantos give a bare
`che`/`io`/`si` a `+lemma` mention *as well as* an ordinary NP 101 times over. They pass every
check, they predate all of this, and deciding whether the corpus wants them is a Layer-3 question
this pass is not the instrument for. **They were left untouched and are recorded here as a
finding.**

**The remaining 2 soft were the same fallout, non-clitic**, both from the step-5 round and both
fixed by hand against the terzina:

- **purgatorio 20:83** *poscia c'ha' il mio sangue a te sì tratto* — `c'` was retagged from the
  pronoun `ci` to the conjunction *che* of *poscia che*, so its frozen single-token NP was headed
  by a conjunction. **Span removed**: it is not a noun phrase. (This also unblocked a Layer-4
  deferral recorded in [`../dep/CORRECTIONS.md`](../dep/CORRECTIONS.md) as *the Layer-2 block*, and
  moved Layer 5 — see [`../skel/CORRECTIONS.md`](../skel/CORRECTIONS.md).)
- **purgatorio 31:25** *quai fossi attraversati o quai catene* — `fossi` was retagged from the verb
  `essere` to the noun `fosso` (*ditches*), so it needed to head an NP and headed none. **Added
  `quai fossi` and `fossi`**, mirroring the `quai catene` / `catene` pair already on the same line.

`np --check`: **0 hard, 0 soft**. `morph`, `dep` and `case` re-measured unchanged; `skel` moved
3633 → 3635, for the reason recorded on its own side.

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

## One clitic-cluster enumeration from Layer 5's Inferno 7-10 read (2026-08-14)

`morph/inferno/10.tsv` retagged 10:23 `ten` from a form of *tenere* to the clitic cluster `te+ne`
(see [`morph/CORRECTIONS.md`](../morph/CORRECTIONS.md)), which brings the token under this layer's
clitic-mention rule. Added `[+te]` and `[+ne]` alongside the existing `[ten]` span, exactly as
`gliel` (10:44) and `sen` (10:1) are already enumerated. `np --check` stays 0 hard / 0 soft.
