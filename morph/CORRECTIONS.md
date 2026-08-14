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
[`../np/CORRECTIONS.md`](../np/CORRECTIONS.md) for the Layer-3 side and the
running soft-violation counts.

## `fiacco` mistag correction (2026-08-13)

Found during a Layer-5 per-position read of Inferno 4-6 (see
[`../skel/CORRECTIONS.md`](../skel/CORRECTIONS.md)'s *Rule AG*), not the NP-head route. Inferno
6:54, "a la pioggia mi fiacco", had `fiacco` tagged the adjective *fiacco* ("weak") — impossible
next to the reflexive clitic `mi`, which adjectives don't take. Retagged `verb`/`fiaccare`/
1sg/present/indicative (*fiaccarsi*, "to wear oneself down": "in the rain I wear myself down").
`morph --check` 0 hard/0 soft, unchanged.

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

## `Rife` mistag correction (2026-07-04)

The remaining 43 soft violations (all noun-coverage gaps, no function-word heads left) were
classified by cause: 24 are title/proper-name span-merge gaps (`ser Brunetto`, `Carlo Magno`, …),
15 are single content words Layer 2 already tags correctly that Layer 3 simply never spanned, 3
are the still-unresolved `ben`/`bene`-before-infinitive cases, and 1 is the deliberately-untouched
`dia` at paradiso 26:10. Checking each violation's actual Layer-2 POS against precedent elsewhere
in the corpus found exactly one genuine mistag: `Rife` (purgatorio 26:43, "come grue ch'a le
montagne Rife"), tagged `proper noun` (f. pl.), agrees in gender/number with `montagne` (f. pl.) —
a demonym adjective ("Riphean"), not a proper noun, matching the corpus's existing pattern for
other place-derived adjectives (`troiano`, `latino`, `romano`, all tagged `adjective`). Corrected
to `adjective`, which exempts it from `_needs_np`'s coverage check. Layer 3's `--check` count is
now **42** soft (down from 43); `morph --check` remained 0 hard / 0 soft.

## `CONT_NEXT` split-word flag (2026-07-04)

The last remaining case, paradiso 26:10's `dia`, is not a mistag either: "questa dia / regïon" is
one word (archaic `dia`/`dio` "divine", modifying `regïon`, i.e. "questa dia regïon" — "this divine
region") split across an enjambed line break. Layer 2 already records this by giving both halves
the lemma `regione` and the note `split word`. Layer 3 spans are single-line by design (see
PLAN.md's Layer 3 *Scope* note), so `dia` can never head a same-line NP no matter what Layer 3
does — a structural impossibility, not a generation gap, exactly the same shape of problem the
`NO_NP` idiom flag solves, just for a different reason.

Rather than reuse `NO_NP` (whose docstring specifically means "part of a fixed idiom"), a second,
distinct flag `CONT_NEXT` ("continues on next line") was added to the same comma-separated `note`
convention — `dia`'s note becomes `split word, CONT_NEXT`. `_needs_np` now exempts a noun from
coverage if either `NO_NP` or `CONT_NEXT` is among its note's flags. Layer 3's `--check` count is
now **41** soft (down from 42); `morph --check` remained 0 hard / 0 soft.

## Fused clitic clusters — `pos` undercounting its own `lemma` (2026-07-31)

Surfaced by the [`case/`](../case/README.md) annex's corpus pass, which is the first consumer to
read `pos` as a **count** of a fused token's components rather than as a label.

On 24 tokens Layer 2's `pos` disagreed with Layer 2's own `lemma`. The lemma named two clitics —
`si+ne`, `me+ne`, `ci+ne`, `gli+lo`, `gli+ne` — while the `pos` named one pronoun:

| form | lemma | wrong `pos` | n |
|---|---|---|---|
| `sen` | `si+ne` / `se+ne` | `pronoun` (14), `pronoun+adverb` (1), `pronoun+particle` (1) | 16 |
| `men` | `me+ne` | `pronoun` | 2 |
| `gliel` | `gli+lo` | `pronoun` | 2 |
| `cen` | `ci+ne` | `pronoun` | 1 |
| `gliene` | `gli+ne` | `pronoun` | 1 |

The corpus already held the right answer: the identical form `sen` with the identical lemma
`si+ne` is tagged `pronoun+pronoun` **15 times elsewhere**, so this is Layer 2 made consistent
with its own majority reading, not a new judgment imported from outside. All 24 were verified one
at a time against the terzina — every one is a preverbal clitic pair on a verb of motion or
giving (`sen va`, `cen porta`, `men duol`, `gliene diè`, `gliel discoperse`). Only the `pos`
column was changed; the feature columns are a separate question and were left alone.

**One token in the same family was not a cluster at all.** *Purgatorio* 20:85, "Perché men paia
il mal futuro e 'l fatto" — Layer 2 read `men` as `me+ne`, but the sense is "so that the evil,
future and past, may seem **less**": `men` is apocopated `meno`, the comparative adverb, which
the corpus tags `adverb` / `meno` / `apocope` on 55 other tokens. Corrected to match, which also
takes it out of the pronoun scope entirely. `parere` with a `me ne` clitic pair does not read
here — the subject is `il mal futuro e 'l fatto`.

**Effect.** `morph --check` stays **0 hard / 0 soft**; `dep --check` stays **0/0** and
`skel --check` stays **0 hard / 3551 soft**, both re-measured after the edit — no other layer's
verdict moved. 22 canto artifacts change, so their `morph` content hashes move. The pronoun scope
`case/` derives from this column goes from 13113 tokens over 8542 lines to **13112 over 8541**,
and the case-value count (one per pronoun component) to **13171**.

## Fused-token component counts, round 2 (2026-07-31)

The [previous round](#fused-clitic-clusters--pos-undercounting-its-own-lemma-2026-07-31) keyed on
`pos` naming fewer pronouns than a **two-part lemma**. That missed every token where the *lemma*
undercounts too, so `case/`'s next pass hit the same wall on a different set. This round audits
the whole family instead of one symptom of it — 14 tokens, each verified against the terzina.

**Cluster forms whose lemma names only one component** (7). `sen` = `se ne`, `men` = `me ne`,
`ten` = `te ne`, all preverbal clitic pairs. `pos` → `pronoun+pronoun`, lemma → the pair:

| | line | lemma was |
|---|---|---|
| `sen` | *Purg* 24:74, *Purg* 32:89, *Par* 11:5, *Par* 11:85 | `si` |
| `men` | *Inf* 19:128 "sì men portò sovra 'l colmo de l'arco" | `me` |
| `ten` | *Inf* 26:65 "assai ten priego", *Inf* 27:21 "Istra ten va" | `te`, `tu` |

**Enclitics carrying two clitics** (2). *Purg* 19:139 `Vattene` (`andare+ti+ne`) was
`verb+pronoun` — the lemma already named three components — and becomes `verb+pronoun+pronoun`.
*Inf* 30:11 `percosselo` is the mirror error: "e rotollo e percosselo ad un sasso" is
`percosse` + `lo`, one clitic, so the lemma's `percuotere+si+lo` loses its spurious `si`. Its
`pos` was already right, so the case scope does not move.

**`nol` = `non lo`, one pronoun and not two** (4). 37 of the corpus's 41 `nol` tokens read
`non+lo` / `adverb+pronoun`; the outliers do not survive their context — *Purg* 16:139 "io nol
conosco", 16:140 "s'io nol togliessi", *Purg* 31:99 "che nol so rimembrar" were
`ne+lo` / `pronoun+pronoun`, and *Par* 17:92 "e nol dirai" was `non+il` / `adverb+article`,
reading the clitic `lo` as an article. All four corrected to the majority form.

**One more `men` that is the adverb** (1), the same finding as the previous round's *Purg* 20:85.
*Purg* 30:46, "‘Men che dramma / di sangue m'è rimaso che non tremi'" — "less than a dram of
blood is left in me": `Men` is apocopated `meno`, and the lemma `quale` it carried is not a
reading of anything. Corrected to `adverb` / `meno` / `apocope`, which takes it out of the
pronoun scope.

**Left alone, and why.** The comitatives `meco` / `teco` / `seco` are still tagged four ways and
`ne` at *Par* 14:55 still has the lemma `in+esso`, but all of them are single-pronoun tokens
whose `pos` gives the right count, so no consumer is blocked and correcting them is a `morph/`
question of its own. `voialtri` (*Par* 2:10, `voi+altro`) is not a defect: one compound pronoun,
one case.

**Effect.** `morph --check` stays **0 hard / 0 soft** and `dep --check` **0/0**;
`skel --check` goes **3551 → 3550**, the `nol` at *Par* 17:92 having also been the cause of one
Layer-5 membership violation (see [`../skel/CORRECTIONS.md`](../skel/CORRECTIONS.md)). 12 canto
artifacts change. The pronoun scope stays at **13112 tokens**, over **8540** lines, and the
case-value count goes to **13176**.

## The mistags the case annex surfaced and parked (2026-08-02)

The [`case/`](../case/README.md) annex ran three steps over this column without touching it, and
each one left behind Layer-2 positions it had no mandate to fix: step 3's corpus pass found single
tokens whose `pos` was wrong but whose *count* was right (so nothing was blocked), and step 4's
three adjudication slices found six more, **two of which blocked a Layer-4 edit outright**
(see [`../case/CORRECTIONS.md`](../case/CORRECTIONS.md)'s *Layer-2 items this slice surfaced*
entries). This round is the one those entries owe.
It is 10 hand-verified singletons plus one family sweep, every one checked against its terzina and
against what the corpus already does with the same word elsewhere.

### The ten singletons

Each row names the reading and the corpus-internal precedent that makes the tag defensible; the
precedent is what decided the exact lemma and features, not a grammar book.

| position | word | was | now | why |
|---|---|---|---|---|
| *Purg* 31:25.2 | `fossi` | `essere`/`verb` | `fosso`/`noun`/m./pl. | "quai fossi attraversati o quai catene / trovasti" — the noun *ditches*, coordinated with `catene`. Precedent *Inf* 18:17.7, the corpus's only other plural `fossi` |
| *Purg* 23:126.8 | `torti` | `torto`/`noun` | `torto`/`adjective`/m./pl. | "che drizza voi che 'l mondo fece torti" — *made you crooked*, a predicative adjective. Precedent *Par* 13:129.3, and `torto` is `adjective` 14× against `noun` 5× |
| *Inf* 8:4.5 | `i` | `lo`/`pronoun`/m./pl. | `ivi`/`adverb`/apocope | "per due fiammette che i vedemmo porre" — `i` is *ivi*, "there". `che` is already the object and `vedemmo` is 1pl, so the clitic reading has no slot to fill. Precedent *Purg* 10:41.2 `iv'` |
| *Purg* 31:90.1 | `salsi` | `salutare`/`verb` | `sapere+si`/`verb+pronoun`/enclitic | "salsi colei che la cagion mi porse" — *she knows it*. Precedent `sallo` = `sapere+lo`/`verb+pronoun` |
| *Purg* 5:135.1 | `salsi` | `salire+si`/`verb+pronoun` | `sapere+si`/`verb+pronoun`/enclitic | "salsi colui che 'nnanellata pria" — the identical formula, La Pia's. Found by sweeping the first one |
| *Purg* 20:83.2 | `c'` | `ci`/`pronoun` | `che`/`conjunction`/elision | "poscia c'ha' il mio sangue a te sì tratto" — the `che` of *poscia che*. Follows `ch'`/`che`/`conjunction`/elision, 660× |
| *Purg* 11:137.2 | `e'` | `essere`/`verb` | `egli`/`pronoun`/m./sg./3 | "ch'e' sostenea ne la prigion di Carlo" — *which **he** endured*. Precedent `e'`/`egli`/`pronoun`, 11× |
| *Par* 14:55.6 | `ne` | `in+esso`/`pronoun` | `noi`/`pronoun`/pl./1 | "questo folgór che già ne cerchia" — *encircles **us***. Precedent `ne`/`noi`/`pronoun`/archaic, 5× |
| *Inf* 1:112.6 | `me'` | `me`/`pronoun` | `meglio`/`noun`/m./sg./apocope | "per lo tuo me'" — *for your **better***, nominal under `lo`/`tuo`. Precedent *Par* 10:38.4 |
| *Inf* 2:36.4 | `me'` | `me`/`pronoun` | `meglio`/`adverb`/apocope | "intendi me' ch'i' non ragiono" — *you understand **better***. Precedent `meglio`/`adverb`, 14× |

**Two of these were found by sweeping a reported one, not by being reported.** Only *Purg* 31:90's
`salsi` and *Inf* 1:112's `me'` were on the annex's list; sweeping each word form corpus-wide
turned up *Purg* 5:135 (the same *salsi colui/colei che…* idiom, mistagged a different way) and
*Inf* 2:36 (the other `me'`, and also *meglio*). **Neither `me'` in the corpus is the pronoun
`me`, and neither `salsi` is `salire`** — each is a family of two, which is why they are recorded
as families rather than as the singletons they were reported as.

### The comitatives — one family, 58 tokens, 34 distinct taggings

`meco` / `teco` / `seco` / `nosco` / `vosco` are the fused *pronoun + con* forms (Latin *mecum*).
The annex reported them as "tagged four different ways"; the actual count is **34 distinct
`lemma`/`pos`/feature combinations over 58 tokens**, including `seco` as an `adverb` (7×), `nosco`
and `vosco` as an `adjective` (5×, one of them with the lemma `boscoso`), and `seco` as a bare
`preposition`.

All 58 are normalized to a single shape — **`<pronoun>+con` / `pronoun+preposition` / `archaic`**,
with number and person from the pronoun:

| form | lemma | number | person |
|---|---|---|---|
| `meco` (26) | `me+con` | sg. | 1 |
| `teco` (12) | `te+con` | sg. | 2 |
| `seco` (15) | `sé+con` | sg. | 3 |
| `nosco` (2) | `noi+con` | pl. | 1 |
| `vosco` (3) | `voi+con` | pl. | 2 |

**The order is not a preference.** [`README.md`](README.md)'s decomposition rule records the
components in the order the surface word holds them — `Nel → in+il`, `del → di+il` — and *meco* is
*me* followed by *co(n)*. That rule and the plurality tag already in the file agree: `me+con` /
`pronoun+preposition` was already on 17 of the 27 `meco` tokens. `sé` is the corpus's tonic-`se`
lemma at 210 occurrences against 6, which is what settles `sé+con` over `se+con`. 46 of the 58 rows
changed; the other 12 already had this shape.

### Effect

`morph --check` stays **0 hard / 0 soft** and `dep --check` stays **0/0**. 41 canto artifacts
change, so their `morph` content hashes move. `uv run pytest -q` stays at 138 passed.

**`skel --check` goes 3634 → 3633**, and the composition of that −1 is the useful part, because
Layer 5's LLM is an independent read and it had already flagged two of these positions:

- **closed** — *Purg* 11:137 `argument (137, 2) for role subj heads no NP/pronoun/predicate`. The
  Layer-5 read called `e'` the subject of `sostenea`; Layer 2 called it a verb, so the argument
  headed nothing. The `egli` correction closes it. **Independent confirmation of the reading.**
- **closed** — *Purg* 16:141 `argument (141, 9) for role obl heads no NP/pronoun/predicate`, the
  same shape for `vosco`, which was tagged `adjective`.
- **opened** — *Inf* 23:87 `extra_arg: 87.7 obl (87, 8)`. `seco` is now a pronoun, so the
  deterministic derivation produces an `obl` argument the LLM's skeleton does not carry. This is
  the divergence-measure behaviour [`../skel/CORRECTIONS.md`](../skel/CORRECTIONS.md) describes: a
  correct Layer-2 round can move the count either way, and the count is a diagnostic, not the
  objective.

**The pronoun scope this column hands to `case/` moves**, which is the consequential part:
**13112 → 13125 tokens**, **13176 → 13189 values**, over **8540 → 8545 lines**. 14 comitatives that
were `adverb` / `adjective` / `preposition` enter the scope, `salsi` and `e'` add one each, and
`i`, `c'` and the two `me'` leave it. **`case --check` therefore goes 0 hard → 25 hard over 20
lines** — every one a `[count]` mismatch, none of them a wrong answer by the model. Closing them is
a regeneration of exactly those chunks (`make -C case clean` then `make -C case`), which is
LLM-scale work and so the user's, by the convention Phase 5 settled. This is the same sequence
step 3's two rounds went through.

**`np --check` goes 3 hard / 64 soft → 5 hard / 96 soft**, widening the stack's one open defect
rather than adding a new kind. `np` derives its expected `+X` clitic mentions from this column's
lemma parts, so giving `meco` the parts `me`/`con` makes `np` owe a `+me` mention it was never
built with — correct behaviour on `np`'s part, and it resolves with the same deterministic
regeneration of the derived spans that the existing 3 hard / 64 soft is already waiting on. The 2
new hard are *Inf* 24:23 and *Par* 5:84, where the frozen span reads `+se` and the lemma now reads
`sé`. See [`../PLAN.md`](../PLAN.md)'s *Open item*.

## What Layer 4's subject-agreement rule surfaced (2026-08-07)

A new `dep` soft check — an `nsubj` whose person or number contradicts its finite head's (see
[`../dep/CORRECTIONS.md`](../dep/CORRECTIONS.md)) — flagged 173 positions, and at 77 of them the
Layer-2 row was the wrong side rather than the attachment. All were corrected directly in the
committed TSVs, no model call; `morph --check` 0 hard / 0 soft after each batch.

- **An archaic 1sg form tagged 3rd person (17).** Dante's 1sg imperfect ends in `-a` (*io era*,
  *m'apparecchiava*, *m'andava io*) and his 1sg remote past is elided or apocopated (*diss' io*,
  *mi fec' io*, *puosi*, *porsi*); the present subjunctive is syncretic across 1/2/3sg and the
  explicit pronoun is what resolves it (*prima ch'io … mi divella*). One of these also carried the
  wrong lemma: purgatorio 1:127 *porsi* is 1sg of **porgere**, not `porre` + clitic.
- **`altri` and `quei` tagged plural (15).** `altri` is Dante's singular indefinite ("someone",
  always with a singular verb) and `quei` is the nominative singular of `quello` (= *colui*; the
  plural nominative is `quelli`/`ei`).
- **An apocopated 3pl form tagged singular (10).** *levorsi* = *si levaro*, *Volsersi* = *si
  volsero*, *vider*, *strinsermi*, *fensi* = *si fenno*, *sortiro*, and the plural participle
  *rimase*; plus the apocopated plural nouns *splendor* (= *splendori*) and *parlar* (=
  *parlari*), the plural `cento` (three positions) and `l'altr'` = *le altre*.
- **A 3sg verb tagged 2sg, or the reverse (10).** The subject decides: *La mente tua conservi*,
  *se la lucerna … truovi*, *più d'ammirazion … che ti pigli*, *accender ne dovria il disio*,
  *perché non ti facci maraviglia* are all 3sg; *se tu … circonde*, *a tuo piacer ti sazia*
  (imperative) and inferno 10:82 *se tu mai nel dolce mondo regge* = *riedi* (of **redire**, so the
  lemma moved too) are 2nd person.
- **A fused verb+enclitic given the enclitic's person although the verb is finite (7).**
  *Presemi*, *sforzami*, *fuggiemi*, *cresciemi*, *conducemi*, *pareami*, *parmi* — the enclitic is
  the object, so the verb is 3rd person, and none of them is an imperative. This fixes the
  convention rather than inventing one: a **non**-finite fused token (*aprirmi*, *dirci*, 70 of
  them corpus-wide) does carry the enclitic's person, because its verb has none.
- **Six words read as the wrong part of speech.** purgatorio 16:35 *fummo* is the noun **fumo**
  (smoke), not 1pl of *essere*; paradiso 5:119 *disii* is 2sg of **desiderare**, not the plural
  noun; paradiso 6:136 *il* is the clitic object **lo**, not an article; paradiso 14:23 *cerchi* is
  the noun (with *santi* its adjective and *mostrar* the 3pl remote past), not 3sg of *cercare*;
  paradiso 15:51 *du'* is **dove**, not *due*; paradiso 15:55 *mei* is 3sg present subjunctive of
  **meare**, not the possessive. inferno 28:52 *fuor* is *furono* (as it is already tagged at
  inferno 7:40) and, standing for "a hundred [of them]", took the `RELCL_HEAD` flag.
- **One lemma/person pair on a relative pronoun**: inferno 2:68 *c'* is `che`, not the clitic `ci`.

Four of these changed a token's POS, which had consequences one layer up and one layer sideways:
two Layer-3 spans (`fummo`, *li santi cerchi*) and one `case` row (paradiso 6:136 *il*,
accusative). See [`../np/CORRECTIONS.md`](../np/CORRECTIONS.md) and
[`../case/CORRECTIONS.md`](../case/CORRECTIONS.md).

## The 37 mistags Layer 5's membership check surfaced (2026-08-09)

Layer 5's `membership` soft check — *an argument position that heads no NP, is no pronoun and is
no predicate* — stood at **82**. Classifying all 82 by the Layer-2 POS of the cited token turned
the class into a small number of shapes, and five of them are Layer 2 being wrong about the token
rather than Layer 5 being wrong about the argument. All 37 were read against their line before
being retagged; the interpretive remainder (substantivized adjectives, quoted mention words,
adverbs cited as objects) is *not* touched here — see
[`../skel/CORRECTIONS.md`](../skel/CORRECTIONS.md) for why those are a checker question.

- **`onde`/`ond'` read as a conjunction where it is a relative pro-form (16)** — inferno 23:130,
  24:42, 30:121, 31:132; purgatorio 1:30, 4:53, 10:51, 15:99, 23:63; paradiso 16:36, 16:150,
  18:102, 21:38, 21:46, 32:22, 32:25. In every one of them `onde` = *da cui / per cui* and heads
  an oblique of its own clause ("la sete **onde** ti crepa", "parte **onde** 'l fiore è maturo"),
  which a conjunction cannot do. Retagged `pronoun`, lemma `onde` — the corpus's own majority
  tagging for this use (32 rows against 7 `relative pronoun` and 23 `adverb`). The sentence-initial
  connective is a different word: paradiso 9:22 *Onde* = "wherefore" was tagged `preposition`,
  which is wrong in the other direction, and is now `conjunction`.
- **`quantunque` = "as much as / whatever" (2)** — inferno 32:84, paradiso 22:82. It is the object
  of its own clause ("**quantunque** la Chiesa guarda"), so `pronoun`, not `conjunction`. Paradiso
  32:56 already carried that reading.
- **Proclitic pronouns tagged as articles (8)** — inferno 1:110 *l'* ("fin che **l'**avrà
  rimessa"), 13:97 *l'* ("non **l'**è parte scelta", the dative *le*), 20:80 *la* ("e **la**
  'mpaluda"); purgatorio 19:24 *l'* ("sì tutto **l'**appago"), 32:116 *el* ("ond' **el** piegò");
  paradiso 22:6 *'l*, 28:24 *'l*, 29:136 *la*. An article cannot stand before a finite verb with
  no noun of its own. Same shape as the paradiso 6:136 *il* the subject-agreement round found.
- **`e'` = *ei/egli* read as a form of `essere` (2)** — purgatorio 21:120 and paradiso 5:21, both
  "quel ch'**e'** …", where `e'` is the subject of the relative clause and the corpus already has
  23 `pronoun` rows for that form.
- **Fused clitic clusters read as prepositions (4)** — inferno 29:34 *sen* (`se+ne`, lemma had been
  `senza`) and purgatorio 12:48 *nel* ("pien di spavento **nel** porta un carro" = *ne lo porta*,
  lemma had been `in+il`) are `pronoun+pronoun`; paradiso 10:111 *ne* ("là giù **ne** gola", the
  dative *ci*) and 30:69 *n'* ("un'altra **n'**uscia fori") are bare `pronoun`.
- **Adverbs tagged as prepositions (3)** — purgatorio 2:45 *entro* ("più di cento spirti **entro**
  sediero"), 30:30 *dentro*, paradiso 25:98 *sopr'* ("di **sopr'** a noi"). No nominal is governed
  at any of the three. Also paradiso 19:74 *quanto* ("**quanto** ragione umana vede"), an adverbial
  relative tagged `conjunction`, now `adverb`.

`morph --check` 0 hard / 0 soft throughout. The retags moved 32 tokens into the case annex's scope
and 2 fused tokens into Layer 3's clitic-mention rule; both are recorded in
[`../case/CORRECTIONS.md`](../case/CORRECTIONS.md) and [`../np/CORRECTIONS.md`](../np/CORRECTIONS.md).
Layer 5's `membership` class went **82 → 47**.

## Five mistags from Layer 5's Inferno 1-3 read (2026-08-12)

Surfaced by the per-position read of all 26 Layer-5 soft violations standing in Inferno 1-3 (see
[`skel/CORRECTIONS.md`](../skel/CORRECTIONS.md)'s *Rules Y-AF*). Each was verified against its
terzina and corrected in place; `morph --check` stays 0 hard / 0 soft, and the accompanying
Layer-4 retags are in [`dep/CORRECTIONS.md`](../dep/CORRECTIONS.md).

| position | was | now | why |
|---|---|---|---|
| inferno 2:42 `tosta` | `adverb` | `adjective`, f. sg. | *"la 'mpresa che fu nel cominciar cotanto tosta"* — it agrees with `'mpresa` as the copula's predicate adjective. Layer 5's rule R deliberately declines to accept a predicative **adverb**, so this mistag was the whole violation; its docstring cites this very line as the case it leaves undecided. |
| inferno 2:71 `disio` | `desiderio`, `noun` | `disiare`, `verb`, 1sg present indicative | *"ove tornar disio"* = "where I long to return". Read as a noun, the infinitive next to it became its `nsubj`, which is not a possible parse of the line. |
| inferno 2:102 `che` | `conjunction` | `pronoun` | *"che mi sedea con l'antica Rachele"*: the relative subject of `sedea`. Same family as the `che` retags this file already records — and the retag pulls the position into the `case` annex's scope (one new row, `nominative`; see [`case/CORRECTIONS.md`](../case/CORRECTIONS.md)). |
| inferno 3:76 `fier` | `fare`, 1sg future | `essere`, 3pl future | *"Le cose ti fier conte"* = "the things will be made known to you". `fier` is the archaic 3pl of `essere` (beside `fia`, `fieno`), agreeing with `cose`. |
| inferno 3:76 `conte` | `conto`, `noun` m. sg., apocope | `conto`, `adjective`, f. pl. | The predicate adjective ("known"), agreeing with `cose` — not a masculine noun. |

## Three mistags from Layer 5's Inferno 7-10 read (2026-08-14)

Surfaced by the per-position read of all 37 Layer-5 soft violations standing in Inferno 7-10 (see
[`skel/CORRECTIONS.md`](../skel/CORRECTIONS.md)'s *Rules AH-AL*). Each was verified against its
terzina and corrected in place; `morph --check` stays 0 hard / 0 soft, and the accompanying
Layer-3/4/annex rows for `ten` are in [`np/CORRECTIONS.md`](../np/CORRECTIONS.md),
[`dep/CORRECTIONS.md`](../dep/CORRECTIONS.md) and [`case/CORRECTIONS.md`](../case/CORRECTIONS.md).

| position | was | now | why |
|---|---|---|---|
| inferno 7:38 `fuor` | `fuori`, `adverb`, apocope | `essere`, `verb`, 3pl remote past indicative | *"e se tutti fuor cherci"* = "and whether they were all clerics". `fuor` is the apocopated *furono*. The corpus already tags the identical `fuor` **two lines later** (7:40, *"Tutti quanti fuor guerci"*) as `essere`, and Layer 4 makes that one a `cop` — the two adjacent instances of one word were simply tagged differently. |
| inferno 7:38 `cherci` | lemma `cerchio` | lemma `cherico` | The clerics of the line, not circles: *"se tutti fuor cherci / questi chercuti"*. |
| inferno 7:39 `chercuti` | lemma `cercare`, note `past participle` | lemma `chercuto`, note `archaic` | "the tonsured ones" (from *chierica*, the tonsure) — not a participle of *cercare*, which the line's sense does not admit. |
| inferno 8:71 `entro` | `preposition` | `adverb` | *"là entro certe ne la valle cerno"*: `là entro` is adverbial ("in there"), and `certe` modifies `meschite`, not `entro`. Layer 4 already said `advmod`; the mistag is what let Layer 5 mint a spurious `obl:entro`. |
| inferno 10:23 `ten` | `tenere`, `verb`, 2sg present indicative | `te+ne`, `pronoun+pronoun`, contraction | *"vivo ten vai"* = *te ne vai*, "you go (from here) alive" — a clitic cluster, not a form of *tenere*. Tagged exactly like `sen` (`si+ne`) at 10:1 of the same canto. |

### A retag measured and **not** applied: relative `che`/`ch'`/`onde` tagged `conjunction`

The read also confirmed at scale the `che`/`ch'` mistag family this file already records: **250
tokens** across the corpus carry Layer-2 POS `conjunction` while Layer 4 fills an argument slot
(`nsubj`/`obj`/`iobj`/`attr`/`xcomp`/`ccomp`/`obl`) with them — 139 `che`, 92 `ch'`, 16
`onde`/`ond'`, and 3 outliers. Retagging the 247 relative ones was implemented and measured, then
**reverted**, for a reason worth freezing:

> The `case` annex requires one row per Layer-2 pronoun token, so the retag turned `case --check`
> into **243 hard violations**. Those values may not be filled in from Layer 4's deprels: rule U
> uses the annex precisely as a *third, independent* opinion when Layer 4 and the LLM disagree
> about a role, and deriving it from Layer 4 would make that adjudication circular.

The retag is therefore gated on an independent model read of the annex over those 243 positions —
a build round, not an edit. Until then the checker's existing workaround stands (`validate_unit`
accepts the word forms `che`/`ch'`/`cui`/`qual`/`quale`/`chi` regardless of the frozen POS tag).
The 3 outliers were not Layer-2 defects at all and were fixed in Layer 4 instead; see
[`dep/CORRECTIONS.md`](../dep/CORRECTIONS.md).
