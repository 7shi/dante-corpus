# Manual Layer-2 corrections

Layer 2 (`morph/`) is build-time output — an LLM pass per chunk, frozen to `morph/<canticle>/NN.tsv`
and never touched at runtime (see [`README.md`](README.md)). Its own `--check` only enforces
structural/closed-tag correctness (one row per token, closed vocabularies for gender/number/person);
it cannot catch a token that's *structurally* fine but tagged the wrong part of speech.

Those mistakes surfaced instead through **Layer 3**'s (`np/`) soft-check policy: `np/np.py --check`
flags every NP span whose head is a function-word POS (article/conjunction/preposition/
interjection/determiner), since a genuine noun phrase's head must be a content POS. Most such
flags are Dante using a function word substantively (`'l più basso`, `un de' tuoi`) — correct as
flagged, nothing to fix. But a recurring minority turned out to be Layer 2 itself mistagging a
token that was actually functioning as a pronoun/verb/adjective/adverb/noun. This file is the
record of every one of those corrections: what was retagged, to what, and why — each one verified
against an existing precedent row elsewhere in the corpus before being applied, never guessed.

Every correction below was made directly in the committed `morph/<canticle>/NN.tsv` artifacts —
no model call, no Layer-2 rebuild — and `morph --check` was re-run after each batch to confirm
0 hard / 0 soft throughout. Several of the same review passes *also* found genuine Layer-3 span
errors (over-inclusion, wrong head index, missing merges) sitting alongside the Layer-2 mistags on
the same flagged lines; those are only summarized here for context — see
[`../np/README.md`](../np/README.md) and [`../PLAN.md`](../PLAN.md) for the Layer-3 side and the
running soft-violation counts.

## `che`/`ch'` mistag correction (2026-07-03)

All 36 lines flagged `head 'che'/"ch'" is 'conjunction'` were reviewed by hand against their
terzina context. **24** are Dante's relative pronoun `che`/`ch'` (subject/object of the following
clause, referring back to an antecedent — e.g. inferno 2:72 `amor mi mosse, che mi fa parlare`,
paradiso 33:120 `foco che quinci e quindi igualmente si spiri`), mistagged `conjunction` by the
build model. Corrected to `relative pronoun` (the label the corpus already uses elsewhere for
unambiguous cases).

The other **12** are genuinely `conjunction` — left untouched here since the underlying issue was
Layer 3 over-including them as NP heads, not a Layer-2 error:
- **6** consecutive `tanto`/`sì … che` ("so … that"): inferno 3:54, 19:27; purgatorio 17:51;
  paradiso 21:141, 23:53; plus the comparative-adjacent paradiso 27:110 `non ha altro dove che`.
- **3** the fixed idiom `secondo che` ("according to how/the extent that"): inferno 5:6;
  paradiso 14:3, 28:35.
- **2** complementizer `che` introducing a noun clause (`sappie che …`, `pensa che …`):
  purgatorio 22:49; paradiso 18:131.
- **1** causal `poi che` ("since"): paradiso 4:9.

## `un`/`una` mistag correction (2026-07-03)

All 41 lines flagged `head 'un'/'una' is 'article'` were reviewed by hand the same way. **38** are
Dante's substantivized indefinite pronoun `un`/`una` ("one [of them]", partitive or anaphoric —
`un de' tuoi`, `un di quelli spirti`, `l'una e l'altra milizia`, `l'un l'altro`), mistagged
`article`; corrected to `pronoun` (lemma stays `uno`, the `indefinite` note cleared — matching the
corpus's existing `pronoun`-tagged `un`/`una` rows elsewhere, e.g. inferno 7:66 `farne posare
una`). **2** (paradiso 3:81 `per ch'una fansi nostre voglie stesse` — predicative "become as one";
purgatorio 32:144 `tre sovra 'l temo e una in ciascun canto` — counting, parallel to the
already-`numeral` `tre`) are genuinely `numeral`, matching the corpus's existing
`numeral`-tagged standalone `uno` (inferno 2:3 `io sol uno`).

The remaining flagged line, paradiso 31:8, was a Layer-3 alignment mismatch rather than a Layer-2
mistag (`align_chunk` matched a proposed span to the wrong occurrence of a repeated word across two
different phrases) — fixed by reassigning the Layer-3 span; its Layer-2 POS was then corrected to
`numeral` to match the corrected reading.

## Function-word-head cluster review (2026-07-04)

The next 57 function-word-head violations were reviewed the same way. The largest, most uniform
cluster — 42 lines headed by a bare/elided article form (`il/la/lo/li/le/el/'l/l'/El/I`) — was
delegated to an LLM subagent, briefed with the corpus's own precedent rows: Old Italian frequently
uses these same word forms as unstressed clitic pronouns homographic with the article (e.g.
`morph/inferno/08.tsv` `il`→lemma `lo`, note "archaic"). Its classifications were spot-checked
against the raw span/morph data before applying: **25** corrected to `pronoun`; the other **20**
were Layer-3 over-inclusion (a redundant single-token span duplicating an already-correct larger
span), left as Layer-2-correct and fixed on the Layer-3 side instead. Two cases needed direct
judgment:
- inferno 24:100 `Né O sì tosto mai né I si scrisse` — both `O` and `I` are cited letter shapes
  (mentioned, not used); retagged `noun`.
- purgatorio 23:87 `la Nella mia` — the real bug was token 2 `Nella`, mistagged
  `preposition+article` ("in+la") instead of the proper noun (Forese's wife's name, in Tuscan
  article-before-name style); retagged `proper noun`.

The remaining 15 heterogeneous cases (interjections, conjunctions, prepositions, a determiner)
were each resolved by matching an existing corpus tagging convention rather than inventing a new
category:
- `Guai a voi` (inferno 3:84) → `noun` (cf. many other `guai`/`guaio` noun rows, including one for
  the *same* line's earlier duplicate token).
- `Tutti son pien...` (inferno 11:19) → `pronoun` (substantivized `tutto`, cf. existing
  `tutto`-as-pronoun rows).
- `lo 'mperché` (purgatorio 3:84) → `noun` (substantivized "the wherefore", cf. `perché`-as-noun
  rows — one nine lines later in the very same canto).
- `un «oh!» lungo e roco` (purgatorio 5:27) / `strinse in «uhi!»` (purgatorio 16:64) → `noun`
  (nominalized cries, syntactically real nouns inside their sentences, unlike a bare quoted
  exclamation).
- `sensibile onde` (purgatorio 32:15) → `adverb` (relative "whereby", cf. an existing
  `onde`/adverb row already noted "relative").
- `infino a co` (paradiso 3:96) → `noun` (apocope of `capo`, "to the end", cf. `capo`-as-noun
  rows).
- `quantunque vedi` (paradiso 32:56) → `pronoun` (indefinite relative "whatever", cf. existing
  `quantunque`-as-pronoun rows).

Three more in that batch of 15 needed no Layer-2 change at all — the flag was purely Layer-3
(two duplicate `verso di quella...` spans, purgatorio 3:51 and 28:30; one wrong span-head index
on a Latin quotation, purgatorio 19:137 `Neque nubent`). One, paradiso 7:1 `Osanna`, was left as
an accepted soft violation with no fix on either layer.

## Noun-coverage-gap mistag pass (2026-07-04)

The 82 "noun heads no NP" violations were classified by cause before touching anything, since most
aren't Layer-2 problems: `fin che`/apocopated-preposition/`allotta` idioms (25, no real NP
expected), two-token proper-name/title pairs where Layer 3 picked only one word as head (29, a
Layer-3 span-merge gap), and single content words Layer 2 already tags correctly that Layer 3
simply never spanned (13, including `animal` and `forme`, which first looked like adjective-mistag
candidates but matched established corpus convention on closer check and were left alone).

Only **11** were genuine Layer-2 mistags, each matched against an existing precedent row before
fixing:

| Token | Location | Context | Old → New POS | Notes |
|---|---|---|---|---|
| `stato` | inferno 27:117 | "stato...sono a' crini" | noun → verb | `essere`, past participle |
| `conte` | inferno 33:31 | "cagne...studïose e conte" | noun → adjective | `conto` (archaic "wise"), agrees with fem. pl. `cagne` |
| `giuso` | purgatorio 2:40 | "chinail giuso" | noun → adverb | `giù`, archaic — the *only* one of 33 `giuso` occurrences in the corpus tagged noun |
| `U'` | paradiso 11:139 | "U' ben s'impingua" | noun (`uomo`) → adverb | apocope of `ove` |
| `luce` | paradiso 20:37 | "Colui che luce in mezzo" | noun → verb | `lucere` ("shines"), matches 5 other `luce`/verb rows |
| `via` | paradiso 21:37 | "vanno via sanza ritorno" | noun → adverb | the `andare via` ("go away") idiom |
| `vòlto` | paradiso 22:94 | "Iordan vòlto retrorso più fu" (enjambed) | noun → verb | `volgere`, past participle, periphrastic passive |
| `reflesso` | paradiso 30:107 | "di raggio...reflesso al sommo" | noun → adjective | `riflesso`, agrees with masc. `raggio` not fem. `parvenza` |
| `dia` | paradiso 14:34 | "la luce più dia" | noun (`dì`) → adjective | `divo` (archaic "divine/radiant") |
| `parlonne` | purgatorio 19:47 | "colui che sì parlonne" | noun → verb+pronoun | `parlare+ne`, enclitic, matches sibling `volseci`→`volgere+ci` on the same line |
| `mundo` | purgatorio 27:8 | "Beati mundo corde" (Matthew 5:8) | noun (`mondo`="world") → adjective | `mondo` (archaic "pure"), agreeing with `corde` |

Note on `dia`: a *second* flagged occurrence (paradiso 26:10) was deliberately left untouched — it
carries an existing note="split word" that looks like an intentional prior design choice, not an
obvious mistag.

Three cases were deliberately excluded despite superficially looking similar, because the corpus
is internally inconsistent about them: `ben`/`bene` before an infinitive (inferno 15:64,
paradiso 9:24, paradiso 20:59 — "ben far"/"bene operar") is tagged noun+noun in some places and
noun+verb-infinitive in others across the corpus, so there's no clean precedent to match — fixing
it needs a real design decision about how nominalized infinitives are tagged, not a mechanical
lookup.

Retagging `parlonne` triggered the frozen clitic-mention check (its span had no `+ne` mention yet);
`np/np.py purgatorio --fix-clitics` backfilled it deterministically, no model call needed.

## `NO_NP` idiom flag (2026-07-04)

The 25 "no real NP expected" cases identified in the pass above are not a Layer-2 tagging error at
all: Layer 2 correctly tags each token's part of speech (`fin`→`noun` "fine", apocope; `inver'`/
`incontr'`/`inverso`/`incontro`→`noun` "inverso", contraction/apocope; `'nver'`/`'ntorno`→`noun`,
elision/contraction; `allotta`→`noun`, contraction). The token is simply never the head of a genuine
noun phrase, because it only ever occurs as a fixed piece of an idiom — `fin che` ("until"), `inver'
di`/`incontr'a` ("toward"), `allotta` ("at that time") — not as a standalone referring expression.
Layer 3's coverage check (`_needs_np` in `dante_corpus/np.py`) has no way to know that from the POS
alone, so it flagged all 25 as "noun heads no NP" even though Layer 3 correctly chose not to span
them.

Rather than leave these as unexplained accepted violations, each of the 25 rows now carries a
machine-readable `NO_NP` flag in its `note` column, comma-separated alongside any existing note
(e.g. `apocope` → `apocope, NO_NP`; an empty note becomes `NO_NP` on its own) — the same
comma-separated convention the corpus already uses for multi-note rows (`reflexive, elision`, etc.).
`_needs_np` now splits `note` on `,`, strips each piece, and treats a POS that would otherwise need
an NP as exempt if `NO_NP` is among them. This is a targeted, hand-verified exemption — each of the
25 lines was checked against its terzina context (see the classification above) before flagging —
not a blanket rule for these word forms in general.

Layer 3's `--check` count is now **47** soft (down from 72: 25 idiom-flagged noun-coverage gaps
removed by the `NO_NP` exemption, leaving 30 title/proper-name span-merge gaps, 12 unspanned single
content words, 3 `ben`/`bene` cases, the `dia` at paradiso 26:10, and the accepted `Osanna` exception).

## Layer-2-POS-aware generation prompt resolves `Osanna` (2026-07-04)

The `Osanna` exception noted throughout this file (function-word-head cluster review, above) and
in `np/README.md`/`PLAN.md` as "an accepted soft violation with no fix on either layer" is now
resolved — not by a Layer-2 change, but by making Layer 3's generation prompt aware of Layer 2's
POS data in the first place (see `PLAN.md`'s Layer 3 check status for the design). Given a
"Function words (never choose as Head)" hint listing `Osanna (interjection)`, the local model
regenerated paradiso 7:1 without ever choosing `Osanna` as a head, and — as a side effect — also
added a nested single-token span for `sabaòth`, closing what would otherwise have become a new
noun-coverage gap.

Running `--fix` with the new hint across all 47 then-flagged lines improved 4 of them: `Osanna`
itself, plus three unrelated noun-coverage gaps that incidentally picked up a nested single-token
span for their previously-unspanned noun (inferno 16:95 `Viso`, inferno 28:55 `fra`, paradiso
6:134 `Ramondo`). The other 43 lines regenerated but were rejected by `--fix`'s no-worse-off
guarantee (same violation count, sometimes on a different token) and kept their original artifact.
Layer 3's `--check` count is now **43** soft (down from 47).
