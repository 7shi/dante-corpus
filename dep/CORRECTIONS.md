# dep — Layer 4 correction history

## purgatorio 20:93 — infinitive complement attached to consecutive clause rather than perception verb (2026-08-18)

Found during the final Phase 7 census closing Layer 5 soft violations (purgatorio 20:93; see [`../skel/PLAN.md`](../skel/PLAN.md) §P15).

> Veggio il novo Pilato sì crudele, / che ciò nol sazia, ma sanza decreto / **portar** nel Tempio le cupide vele.  (purgatorio 20:91-93)

In *Veggio il novo Pilato … portar nel Tempio le cupide vele*, `93.1 portar` is the infinitive complement of the perception verb `91.1 Veggio` (`xcomp<-91.1`), with `91.4 Pilato` as its controller/subject. Layer 4 had attached `93.1 portar` as `conj` of the subordinate consecutive clause verb `92.4 sazia` (*che ciò nol sazia*). Because of this attachment, `derive_unit` propagated `92.2 ciò` as the subject of `portar`, generating `missing_arg: 93.1 subj (92, 2)`.

Attaching `93.1 portar` as `xcomp` of `91.1 Veggio` aligned the derivation with Italian control syntax and cleared the violation.

| token | was | now |
|---|---|---|
| 93.1 `portar` | `conj` ← 92.4 `sazia` | **`xcomp` ← 91.1 `Veggio`** |

## paradiso 7:25 — inverted prepositional argument attached to noun instead of verb (2026-08-18)

Found during the audit of Layer 5 extra_arg positions (paradiso 7:25; see [`../skel/PLAN.md`](../skel/PLAN.md) §P10).

> Per non soffrire **a la virtù che vole** / **freno** a suo prode, quell' uom che non nacque,  (paradiso 7:25-26)

In the hyperbaton (*"Per non soffrire freno a suo prode a la virtù che vole"*), `25.6 virtù` (*a la virtù*) is an oblique argument of the infinitive `25.3 soffrire` (*non soffrire freno a la virtù*), not a modifier of the inverted direct object `26.1 freno`. Layer 4 attached `25.6 virtù` as `obl` of the noun `26.1 freno`. Because of this attachment, `derive_unit` did not derive `obl:a` for `soffrire`, causing the LLM's correct reading `soffrire: obl:a=(25,6)` to be flagged as `extra_arg: 25.3 obl:a (25, 6)`.

Attaching `25.6 virtù` as `obl` of the verb `25.3 soffrire` aligned the derivation with clause syntax and cleared **1 soft violation** in Layer 5 (111 → 110).

| token | was | now |
|---|---|---|
| 25.6 `virtù` | `obl` ← 26.1 `freno` | **`obl` ← 25.3 `soffrire`** |

## paradiso 11:127 — correlative comparative clause subject attached to subordinate verb (2026-08-18)

Found during the audit of Round 10 log failures (`extra_arg_subject` at paradiso 11:129; see [`../skel/PLAN.md`](../skel/PLAN.md) §P9).

> e quanto le sue **pecore** remote / e vagabunde più da esso vanno, / più **tornano** a l'ovil di latte vòte.  (paradiso 11:127-129)

In the correlative comparative construction (*"e quanto le sue pecore … vanno, più tornano …"*), `127.5 pecore` (3pl) is the subject of the main correlative clause verb `129.2 tornano` (3pl), which was modified by the subordinate comparative clause `128.6 vanno` (3pl, `advcl`). Layer 4 attached `127.5 pecore` as `nsubj` of `128.6 vanno`. Because `129.2 tornano` was attached as `conj` to the earlier 3sg clause `125.2 fatto`, `derive_unit` propagated `124.4 pecuglio` (3sg) as the subject of `tornano`, flagging the LLM's correct reading `tornano: subj=(127,5)` as `extra_arg: 129.2 subj (127, 5)`.

Attaching `127.5 pecore` as `nsubj` of the main matrix clause verb `129.2 tornano` aligned the derivation with the true clause syntax and cleared **1 soft violation** in Layer 5 (116 → 115).

| token | was | now |
|---|---|---|
| 127.5 `pecore` | `nsubj` ← 128.6 `vanno` | **`nsubj` ← 129.2 `tornano`** |

## 2 rows from the Phase 7 refusal census audit (2026-08-18)

Found during the per-position audit of the 38 standing Layer-5 refusal positions (`extra_arg`, `extra_arg_subject`, `missing_arg`; see [`../skel/PLAN.md`](../skel/PLAN.md) §P4). Two Layer-4 rows were mis-parsed. Both were applied and re-validated: `morph`/`np`/`dep`/`case --check` all 0 hard / 0 soft; `pytest` 542 passed; Layer 5 **−3 soft violations** (140 → 137).

### inferno 2:60 — temporal adverbial extent tagged as subject

> di cui la fama ancor nel mondo dura, / e durerà quanto 'l **mondo** lontana  (inferno 2:59-60)

Layer 4 tagged `60.5 mondo` as `nsubj` of `60.2 durerà`. In Italian comparative/temporal extent expressions (*"durerà [tanto] quanto [dura] 'l mondo"*), the bare noun phrase `mondo` is an adverbial temporal nominal (`obl`), not the subject of `durerà`. The subject of `durerà` is `59.4 fama`, shared across the coordination from `59.8 dura`. Tagging `mondo` as `nsubj` blocked subject propagation in `derive_unit` and generated two spurious Layer-5 soft violations (`extra_arg: 60.2 subj (59, 4)` and `role_mismatch: 60.2 arg (60, 5) 'obl' vs 'subj'`).

| token | was | now |
|---|---|---|
| 60.5 `mondo` | `nsubj` ← 60.2 `durerà` | **`obl` ← 60.2 `durerà`** |

### purgatorio 14:60 — 3sg coordinate relative attached to 1sg matrix root

> Io veggio tuo nepote che diventa / cacciator di quei lupi … / e tutti li **sgomenta**.  (purgatorio 14:58-60)

Layer 4 attached `60.7 sgomenta` (3sg present indicative) as `conj` of `58.2 veggio` (1sg present indicative), rather than to the coordinate relative clause verb `58.6 diventa` (3sg present indicative). Because of this cross-person attachment, `derive_unit`'s step 3 propagated `58.1 io` as the subject of `sgomenta`, whereas the true subject is `58.5 che/nepote`. The LLM's correct reading `sgomenta: subj=(58,5)` was then flagged as `extra_arg: 60.7 subj (58, 5)`.

| token | was | now |
|---|---|---|
| 60.7 `sgomenta` | `conj` ← 58.2 `veggio` | **`conj` ← 58.6 `diventa`** |

## purgatorio 9:97 — the comparative standard made the root (2026-08-18)

Found in Phase 7's first checker-side batch, reading the eight `arg_slot` positions the model
refused in both the seventh and the eighth Layer-5 `--fix` round (see
[`../skel/CORRECTIONS.md`](../skel/CORRECTIONS.md), rule EI).

> Era il secondo **tinto** più che perso  (purgatorio 9:97)

Layer 4 made **`perso` the root** with `tinto` as its `nsubj`, which reads the line as *"the coloured
one was more than perse"*, buries the real subject `il secondo` as an `amod` inside `tinto`, and hangs
the following line's `petrina` on the comparative standard. The line is an ordinary copular
predication: `il secondo` — the second step of Purgatory's gate — is the subject, `tinto` the
predicate adjective, and `più che perso` the comparative adverbial modifying it.

Two independent things say so. Layer 3 already gives `[il secondo]` a span of its own with `secondo`
as its head and leaves `tinto` outside it. And **the corpus carries the same construction already
tagged the other way**:

> L'acqua era buia assai più che persa  (inferno 7:103)

— `buia` the head with `era` as its `cop`, `L'acqua` its `nsubj`, `più` an `advmod` on `buia`, `che`
a `mark` on `persa`, and `persa` an `advmod` on `più`. 9:97 is now tagged on that precedent:

| row | was | now |
|---|---|---|
| 97.1 `Era` | `cop`→97.7 | `cop`→97.4 |
| 97.2 `il` | `det`→97.4 | `det`→97.3 |
| 97.3 `secondo` | `amod`→97.4 | **`nsubj`→97.4** |
| 97.4 `tinto` | `nsubj`→97.7 | **`root`** |
| 97.5 `più` | `advmod`→97.7 | `advmod`→97.4 |
| 97.6 `che` | `mark`→97.7 | `mark`→97.7 |
| 97.7 `perso` | `root` | **`advmod`→97.5** |
| 98.3 `petrina` | `obl`→97.7 | `obl`→97.4 |

Applied with a gated script asserting the word **and** the current deprel **and** the current head at
each of the 8 rows before rewriting, and checking that no row outside the plan pointed into line 97.
`morph`/`np`/`dep`/`case --check` all re-run at **0 hard / 0 soft**; `pytest` 542.

**Layer 5 measured ±0** and the trade is recorded rather than hidden: the two `subj` violations became
an `extra_tuple`/`missing_tuple` pair, because the Layer-5 reading names the predicate `perso` while
the derivation now — correctly — names `tinto`. The count is not the measure; the correctness of the
parse is. This is the rule-AM precedent, and the residual disagreement is one a `--fix` round can
repair.

## 16 rows from the Layer-5 Paradiso 26-33 read (2026-08-17)

The per-position read of Paradiso 26-33's 32 Layer-5 soft violations (see
[`../skel/CORRECTIONS.md`](../skel/CORRECTIONS.md)) — the batches that finish the read series —
found sixteen Layer-4 rows wrong, in eleven places. Applied with a gated script that asserts the
word, the current deprel and the current head at each `(line, token)` before rewriting;
`morph`/`np`/`dep`/`case --check` all re-run at 0 and `pytest` at 494. Layer 5 **−14/+2** together
with the Layer-2 and Layer-3 rows.

### paradiso 26:56 and 31:116 — the accusative-and-infinitive's shared nominal

"che posson far **lo cor** volgere a Dio" and "tanto che veggi seder **la regina**": after a verb
of perception or causation the nominal is the matrix verb's object *and* the infinitive's subject.
The corpus's own convention for the construction — the one rule BI is written against, censused
there at 10 positions — is `nsubj` on the infinitive. In these two places Layer 4 wrote `obj`
instead, on infinitives (`volgere` of a heart, `sedere`) that do not take one.

| token | was | now |
|---|---|---|
| 26:56.5 `cor` | `obj` ← 56.6 `volgere` | `nsubj` ← 56.6 `volgere` |
| 31:116.6 `regina` | `obj` ← 116.4 `seder` | `nsubj` ← 116.4 `seder` |

### paradiso 28:13 — `furon tocchi` is a passive, not a copula with a noun

"E com' io mi rivolsi e **furon tocchi** / **li miei** da ciò che pare in quel volume": `tocchi`
is the past participle of `toccare` and `li miei` (Dante's eyes) is what was touched. Layer 2 had
`tocchi` as the noun `tocco` (corrected in [`../morph/CORRECTIONS.md`](../morph/CORRECTIONS.md)),
and Layer 4 followed it — `furon` heading the clause with `tocchi` as its `nsubj` and `li miei`
hanging under `tocchi` as an `nmod`. The periphrasis heads on the participle.

| token | was | now |
|---|---|---|
| 13.7 `furon` | `conj` ← 13.5 `rivolsi` | `aux` ← 13.8 `tocchi` |
| 13.8 `tocchi` | `nsubj` ← 13.7 `furon` | `conj` ← 13.5 `rivolsi` |
| 14.2 `miei` | `nmod` ← 13.8 `tocchi` | `nsubj` ← 13.8 `tocchi` |
| 14.4 `ciò` | `obl` ← 13.7 `furon` | `obl` ← 13.8 `tocchi` |

### paradiso 28:106 — `dei saper` is a modal periphrasis, not a partitive

"e **dei saper** che tutti hanno diletto": `dei` is `dovere` 2sg ("you must"), not the contraction
`di+i`, and `saper` is its infinitive complement, not a noun. Layer 2 is corrected alongside. The
modal heads the periphrasis, which is the shape Layer 4 already writes at 26:56 (`posson` head,
`far` its `xcomp`).

| token | was | now |
|---|---|---|
| 106.2 `dei` | `case` ← 106.3 `saper` | `conj` ← 104.2 `chiaman` |
| 106.3 `saper` | `obl` ← 104.2 `chiaman` | `xcomp` ← 106.2 `dei` |

This correction deliberately **raises** Layer 5 by 2: with `dei` and `saper` both predicates, the
LLM's having proposed neither is now reported as two `missing_tuple`s, where before the wrong tree
had absorbed the omission into a single oblique. The trade rule AM recorded.

### paradiso 29:112 — `quel` is the subject and `tanto` the correlative adverb

"e **quel tanto** sonò ne le sue guance, / **sì ch'**a pugnar … fero scudo e lance": `quel` is the
pronoun standing for the "verace fondamento" of 111, and `tanto` is the adverb the `sì che` of 113
correlates with. Layer 4 read the two as a determiner phrase headed by `tanto`, which left the
subject slot on a token no layer calls a nominal.

| token | was | now |
|---|---|---|
| 112.2 `quel` | `det` ← 112.3 `tanto` | `nsubj` ← 112.4 `sonò` |

### paradiso 29:138, 30:127 — the correlative predicate complement

"quanti son li splendori" and "**qual** è colui che tace e dicer vole": the correlative word is the
copular clause's predicate complement, which is the shape Layer 4 itself writes eight lines earlier
at 28:19 ("e quale stella **par** quinci più **poca**", `poca` `xcomp` ← `par`). Both had been
written as determiners of the subject.

| token | was | now |
|---|---|---|
| 29:138.1 `quanti` | `det` ← 138.4 `splendori` | `xcomp` ← 138.2 `son` |
| 30:127.1 `qual` | `det` ← 127.3 `colui` | `xcomp` ← 127.2 `è` |

### paradiso 30:35 — the standard of a comparison is not the verb's object

"Cotal qual io lascio a **maggior bando** / **che quel** de la mia tuba": `quel` is what `maggior`
is measured against, not something `lascio` leaves. UD attaches a phrasal comparative's standard to
the comparative word with the marker as its `case`.

| token | was | now |
|---|---|---|
| 35.1 `che` | `mark` ← 34.4 `lascio` | `case` ← 35.2 `quel` |
| 35.2 `quel` | `obj` ← 34.4 `lascio` | `obl` ← 34.6 `maggior` |

### paradiso 31:20 — the genitive belongs to the nominalized infinitive

"Né **l'interporsi** tra 'l disopra e 'l fiore / **di tanta moltitudine volante** / impediva la
vista": the multitude is what interposes. Layer 4 hung the genitive on `'l fiore`, the nearer of
the two nominals the interposition stands between.

| token | was | now |
|---|---|---|
| 20.3 `moltitudine` | `nmod` ← 19.9 `fiore` | `nmod` ← 19.3 `interporsi` |

### paradiso 32:128 — a genitive two tercets from its head

"E quei che vide **tutti i tempi gravi**, / pria che morisse, **de la bella sposa** / che
s'acquistò con la lancia e coi clavi, / siede lungh' esso": the times are the bride's. Layer 4 read
the genitive as an oblique of `posa`, the verb that closes 130.

| token | was | now |
|---|---|---|
| 128.7 `sposa` | `obl` ← 130.8 `posa` | `nmod` ← 127.7 `tempi` |

### paradiso 33:63 — `il dolce` is what distils

"e ancor mi distilla / nel core **il dolce** che nacque da essa": the sweetness is the subject of
`distilla`, not its object. With the row corrected the conjunct no longer inherits `mia visïone`
from `cessa` either, so two Layer-5 positions close on one edge.

| token | was | now |
|---|---|---|
| 63.4 `dolce` | `obj` ← 62.6 `distilla` | `nsubj` ← 62.6 `distilla` |

## 10 rows from the Layer-5 Paradiso 21-25 read (2026-08-17)

The per-position read of Paradiso 21-25's 21 Layer-5 soft violations (see
[`../skel/CORRECTIONS.md`](../skel/CORRECTIONS.md)) found ten Layer-4 rows wrong, in five places.
Applied with a gated script that asserts the word — and that the row is not already the target
value — at each `(line, token)` before rewriting; `morph`/`np`/`dep`/`case --check` all re-run at 0
and `pytest` at 483. Layer 5 **−6/+1** together with the Layer-2 and Layer-3 rows.

### paradiso 21:28 — `in che` is the relative pronoun, not a determiner

"di color d'oro **in che** raggio traluce" — gold colour *in which* a ray shines through. `che` is
the relative pronoun the preposition `in` governs, with `color d'oro` as its antecedent; Layer 4
read it as a determiner of `raggio` ("in which ray"), which left the relative clause with no
record of its own oblique.

| token | was | now |
|---|---|---|
| 28.6 `che` | `det` ← 28.7 `raggio` | `obl` ← 28.8 `traluce` |

Layer 5 **−2/+3**, deliberately. With the tree right, the derivation gives `traluce` the subject
`raggio` and the oblique `che`, and the LLM's own misreading — `raggio` as the oblique, with a ∅
subject — is now fully reported instead of half-matching a wrong tree. The same honest trade as
paradiso 11:92 in the previous batch. The Layer-3 span `[che raggio]` was dropped in the same pass
(see [`../np/CORRECTIONS.md`](../np/CORRECTIONS.md)).

### paradiso 21:105 — an indirect question is an object, not a predicative complement

"a dimandarla umilmente **chi** fue". `attr` is the corpus's deprel for a predicate complement;
censused corpus-wide, **448** rows carry it and 447 sit on a copular or predicative verb (`essere`
351, `fare` 32, `parere` 15, `vedere`, `divenire`, `chiamare`, `tenere`, `rendere`, `appellare`,
`stimare`, …). `dimandare` is the single outlier.

| token | was | now |
|---|---|---|
| 105.4 `chi` | `attr` ← 105.2 `dimandarla` | `obj` ← 105.2 `dimandarla` |

Layer 5 **−1**.

### paradiso 23:17 — the parenthetical gloss belongs to the interval, not to the brightening

"Ma poco fu tra uno e altro quando, / **del mio attender**, dico, e del vedere / lo ciel venir più
e più rischiarando". The gloss says what the two moments were, so it modifies what `fu` states;
`dico`, the word that marks it as a gloss, is already `parataxis` on `fu`.

| token | was | now |
|---|---|---|
| 17.3 `attender` | `obl` ← 18.7 `rischiarando` | `obl` ← 16.3 `fu` |

Layer 5 **−2** — one violation at each end of the pair (`extra_arg` on `fu`, `missing_arg` on
`rischiarando`).

### paradiso 24:19 — two prepositional phrases, one inside the other's relative clause

"**Di quella** ch'io notai **di più carezza** / vid' ïo uscire un foco". Layer 4 made `quella` a
determiner of `carezza` *across* the intervening relative clause and split "di più carezza" in
half, giving `carezza` to the matrix verb and `di più` to `notai`. Line 21 carries the parallel
phrase — "che nullo vi lasciò **di più chiarezza**", with `di` `case` on `chiarezza` and `più`
`amod` on it — parsed correctly, which is what decides the line.

| token | was | now |
|---|---|---|
| 19.1 `Di` | `case` ← 19.8 `carezza` | `case` ← 19.2 `quella` |
| 19.2 `quella` | `det` ← 19.8 `carezza` | `obl` ← 20.1 `vid'` |
| 19.5 `notai` | `acl:relcl` ← 19.8 `carezza` | `acl:relcl` ← 19.2 `quella` |
| 19.6 `di` | `case` ← 19.7 `più` | `case` ← 19.8 `carezza` |
| 19.7 `più` | `advmod` ← 19.5 `notai` | `amod` ← 19.8 `carezza` |
| 19.8 `carezza` | `obl` ← 20.1 `vid'` | `obl` ← 19.5 `notai` |

Layer 5 **−1**.

### paradiso 24:147 — the second verb of a relative clause, not a conjunct of its antecedent

"quest' è la favilla / che si dilata in fiamma poi vivace, / e come stella in cielo in me
**scintilla**". Both verbs describe the spark, under the one relative pronoun `che`; Layer 4
coordinated the second onto the noun `favilla` instead, so the derivation propagated `favilla`'s
own subject (`quest'`) into it.

| token | was | now |
|---|---|---|
| 147.8 `scintilla` | `conj` ← 145.8 `favilla` | `conj` ← 146.3 `dilata` |

Layer 5 **−2** — the shared subject `che` now propagates, and both halves of the pair go.

## 9 rows from the Layer-5 Paradiso 11-20 read (2026-08-17)

The per-position read of Paradiso 11-20's 43 Layer-5 soft violations (see
[`../skel/CORRECTIONS.md`](../skel/CORRECTIONS.md)) found nine Layer-4 rows wrong, in nine places.
Applied with a gated script that asserts the word — and the old deprel and head — at each
`(line, token)` before rewriting; `morph`/`np`/`dep`/`case --check` all re-run at 0 and `pytest`
at 475. Layer 5 **−9/+5**.

### paradiso 11:92 — Francis disclosed his *intention* to Innocent

"ma regalmente **sua dura intenzione** / ad Innocenzio **aperse**". The intention is what is
disclosed, not what discloses; the subject is the pro-drop Francis.

| token | was | now |
|---|---|---|
| 91.5 `intenzione` | `nsubj` ← 92.3 `aperse` | `obj` ← 92.3 `aperse` |

Layer 5 **−2/+3**, deliberately, and the honest trade this series has recorded before. The
`role_mismatch` and the `extra_arg subj (0,0)` at 92.3 both go. What appears is the derivation's
own weakness, now unmasked: `aperse` and `ebbe` are `conj` of `gravò`, whose subject is `viltà`,
so both inherit *«viltà di cuor»* — and the LLM's `92.7 ebbe: subj=(91,5)` is a misreading that the
wrong tree had been matching. The object reading is not in doubt; the count is.

### paradiso 12:38 — `caro` is an adverb of price, like the three in the next line

"L'essercito di Cristo, che **sì caro** / **costò** a rïarmar … si movea **tardo, sospeccioso e
raro**". Line 39 gives three adjectives in the same adverbial function and Layer 4 writes all three
`advmod`; `caro` in line 37 was the odd one out.

| token | was | now |
|---|---|---|
| 37.7 `caro` | `obj` ← 38.1 `costò` | `advmod` ← 38.1 `costò` |

Layer 5 **−1**.

### paradiso 13:131 — the comparison's second term is its subject

"sì come **quei** che stima / le biade in campo pria che sien mature" — "like the one who judges
the crops in the field before they are ripe". `quei` is the subject of the elided comparative
clause, and Layer 4 already writes the parallel case (16:71 `agnello`) as `nsubj`.

| token | was | now |
|---|---|---|
| 131.5 `quei` | `obj` ← 131.4 `come` | `nsubj` ← 131.4 `come` |

Layer 5 **−1**.

### paradiso 14:134 — `suso` is a locative adverb, not an object

"che i vivi suggelli / d'ogne bellezza **più fanno più suso**".

| token | was | now |
|---|---|---|
| 134.7 `suso` | `obj` ← 134.5 `fanno` | `advmod` ← 134.5 `fanno` |

Layer 5 **−1**.

### paradiso 15:12 — what the lover strips off is *that love*

"Bene è che sanza termine si doglia / **chi**, per amor di cosa che non duri / etternalmente,
**quello amor si spoglia**" — "he who, for love of a thing that does not last for ever, strips
himself of that love". The subject of `spoglia` is the antecedent `chi`, which the `acl:relcl`
edge already supplies.

| token | was | now |
|---|---|---|
| 12.3 `amor` | `nsubj` ← 12.5 `spoglia` | `obj` ← 12.5 `spoglia` |

Layer 5 **−1**.

### paradiso 15:51 — `bianco né bruno` is what does not change

"du' non **si muta** mai **bianco né bruno**". The two adjectives were an apposition to the
relative adverb `du'`, which predicates nothing of them.

| token | was | now |
|---|---|---|
| 51.6 `bianco` | `appos` ← 51.1 `du'` | `nsubj` ← 51.4 `muta` |

Layer 5 **−1/+1**, deliberately: the `extra_arg xcomp` goes and the LLM's own subject citation
(`du'`) becomes the divergence. The parse is right and the count is unchanged.

### paradiso 15:56 — the thought flows *from Him who is first* to the speaker

"Tu credi che a me tuo pensier **mei** / **da quel ch'è primo**, così come **raia** / **da l'un** …
il cinque e 'l sei". Each verb has its own source phrase; Layer 4 had given both to `raia`.

| token | was | now |
|---|---|---|
| 56.2 `quel` | `obl` ← 56.8 `raia` | `obl` ← 55.8 `mei` |

Layer 5 **±0**: the LLM lists the phrase on *both* verbs, so exactly one of the two listings is
reported either way. Applied for the parse.

### paradiso 16:71-72 — the five blades are the comparison's subject

"e molte volte **taglia** / più e meglio **una** **che le cinque spade**" — one blade cuts more and
better than five [cut]. Layer 4 already writes 71.3 `agnello`, the same shape two lines up, as
`nsubj` of the same verb.

| token | was | now |
|---|---|---|
| 72.8 `spade` | `obj` ← 71.7 `taglia` | `nsubj` ← 71.7 `taglia` |

Layer 5 **−1**: rule AR/BA accept a second subject that is a comparison's second term, which is
how 71.3 was already passing.

### paradiso 19:94-95 — the blessed image is the subject of `si fece`

"e come quel ch'è pasto la rimira; / **cotal si fece**, e sì leväi i cigli, / **la benedetta
imagine**" — the image did likewise; *«leväi i cigli»* is the poet's parenthetical 1sg.

| token | was | now |
|---|---|---|
| 95.3 `imagine` | `obl` ← 94.6 `leväi` | `nsubj` ← 94.3 `fece` |

Layer 5 **−1**.

## 10 rows from the Layer-5 Paradiso 6-10 read (2026-08-17)

The per-position read of Paradiso 6-10's 18 Layer-5 soft violations (see
[`../skel/CORRECTIONS.md`](../skel/CORRECTIONS.md)) found ten Layer-4 rows wrong, in five places.
Applied with a gated script that asserts the word — and the old cell value — at each
`(line, token)` before rewriting; `morph`/`np`/`dep`/`case --check` all re-run at
0 and `pytest` at 465.

### paradiso 7:74-75 — the preposition governs the phrase that follows it

"ché l'ardor santo ch'ogne cosa raggia, / **ne la più somigliante** è più vivace" — "for the holy
ardour that irradiates everything is most alive in the most similar [creature]". Layer 4 had `ne`
governing `ardor`, three tokens to its left and across a line break, which left the adjective
inside the prepositional phrase as the subject of the copular clause:

| token | was | now |
|---|---|---|
| 75.1 `ne` | `case` ← 74.3 `ardor` | `case` ← 75.4 `somigliante` |
| 75.4 `somigliante` | `nsubj` ← 75.7 `vivace` | `obl` ← 75.7 `vivace` |
| 74.3 `ardor` | `obl` ← 75.7 `vivace` | `nsubj` ← 75.7 `vivace` |

Layer 5 **−2**: the LLM had read the line correctly and both of its `role_mismatch` positions were
the tree's error, not its own.

### paradiso 7:142-143 — the supreme beneficence is the subject of `spira`

"ma **vostra vita** sanza mezzo **spira** / **la somma beninanza**, e la innamora / di sé" — the
beneficence breathes forth your life without an intermediary, and then *enamours it* (`la` = the
life) of itself. Layer 4 had the two nominals the other way round:

| token | was | now |
|---|---|---|
| 142.3 `vita` | `nsubj` ← 142.6 `spira` | `obj` ← 142.6 `spira` |
| 143.3 `beninanza` | `obj` ← 142.6 `spira` | `nsubj` ← 142.6 `spira` |

Layer 5 **±0**, deliberately. The two `role_mismatch` positions at 142 go, and two new ones appear
at 143: the LLM reads `spira` correctly but then gives the conjoined `innamora` the *life* as its
subject, which is the same slip the old tree made — so with the tree corrected the LLM's own
misreading surfaces where it had been hidden by agreement. The fifth batch in the series to record
that trade.

### paradiso 9:87 — `far suole` is modal plus lexical verb, not the reverse

"là dove l'orizzonte pria **far suole**" — where the horizon is wont to make [midday]. Layer 4 had
`far`, a full lexical infinitive, as the **auxiliary** of `suole`:

| token | was | now |
|---|---|---|
| 87.6 `far` | `aux` ← 87.7 `suole` | `xcomp` ← 87.7 `suole` |

Censused before applying: `solere` heads its own clause with a complement 23 times corpus-wide and
is an `aux` 18 times, so both directions are in use and only the *inner* label is wrong here;
`fare` is an `aux` 13 times and every one of those is the causative ("il fé far", purgatorio
5:77), which this is not. Layer 5 **−1**.

### paradiso 9:135 — `a' lor vivagni` is one prepositional phrase

"sì che pare **a' lor vivagni**" — so that it shows in their margins. Layer 4 had the contraction
`a'` governing `lor` alone, `lor` as a dative oblique of `pare`, and `vivagni` as the copular-style
`xcomp` of a verb that has no copula. Layer 3 already read the three words as one NP
(`[6-8] head=8`):

| token | was | now |
|---|---|---|
| 135.6 `a'` | `case` ← 135.7 `lor` | `case` ← 135.8 `vivagni` |
| 135.7 `lor` | `obl` ← 135.5 `pare` | `det:poss` ← 135.8 `vivagni` |
| 135.8 `vivagni` | `xcomp` ← 135.5 `pare` | `obl` ← 135.5 `pare` |

`lor` is the invariant possessive, which this corpus already writes `det:poss` in 114 of its 199
rows; Layer 2 and the case annex move with it (see [`../morph/CORRECTIONS.md`](../morph/CORRECTIONS.md),
[`../case/CORRECTIONS.md`](../case/CORRECTIONS.md)). Layer 5 **±0**: the `role_mismatch` goes and
an `extra_tuple` takes its place, the LLM's own row treating `vivagni` as a predicate — a reading
only the wrong tree supported.

### paradiso 10:147 — the relative clause modifies the conjunct it follows

"e in tempra / e in **dolcezza ch'esser non pò nota**" — Layer 4 hung the relative clause on
`tempra`, the coordination head, rather than on `dolcezza`, the conjunct it immediately follows and
plainly qualifies:

| token | was | now |
|---|---|---|
| 147.7 `pò` | `acl:relcl` ← 146.8 `tempra` | `acl:relcl` ← 147.3 `dolcezza` |

`ch'` is retagged from conjunction to relative pronoun at Layer 2, with a `nominative` case-annex
row. Layer 5 **±0** on its own — and it is the correction that shaped rule DK, because moving the
antecedent onto a conjunct moved it *off* the position rule C's coordination collapse rewrites the
LLM's citation to. The rule reads the antecedent through `_coordination_head` for that reason; the
uncorrected tree would never have shown the need.

## 6 rows from the Layer-5 Paradiso 1-5 read (2026-08-17)

The per-position read of Paradiso 1-5's 26 Layer-5 soft violations (see
[`../skel/CORRECTIONS.md`](../skel/CORRECTIONS.md)) found six Layer-4 rows wrong, in five places.
Applied with a gated script that asserts the word at each `(line, token)` before rewriting;
`morph`/`np`/`dep`/`case --check` all re-run at 0 and `pytest` at 449.

### paradiso 1:81 — `alcun lago` is the object, not a third conjunct of the subject

"che pioggia o fiume / **lago** non fece **alcun** tanto disteso" — "that neither rain nor river
ever made **any lake** so widespread". The object is the discontinuous `lago … alcun`, fronted
across its own verb, and Layer 4 had read the two halves as belonging to the subject instead:

| token | was | now |
|---|---|---|
| 81.1 `lago` | `conj` ← 80.9 `fiume` | `obj` ← 81.3 `fece` |
| 81.4 `alcun` | `det` ← 80.7 `pioggia` | `det` ← 81.1 `lago` |

Layer 5 **+1**, deliberately. The old tree gave `fece` a three-member subject and no object; the
LLM read `alcun` as the subject and omitted `pioggia`, so its own misreading matched the wrong
tree closely enough that only part of it was reported. With the tree correct the derivation says
`subj=pioggia, obj=lago, xcomp=disteso` and all four of the LLM's divergences surface — the honest
trade rule AM recorded. The Layer-3 span `[4-6] alcun tanto disteso` is left alone: it is the
object's second, contiguous piece, which is exactly what Layer 3 can represent of a discontinuous
phrase.

### paradiso 1:90 — `ciò che vedresti` is a relative *object*

"sì che non vedi / ciò **che** vedresti se l'avessi scosso" — "so that you do not see what you
would see". `vedresti` is 2sg and `ciò` 3sg, so the relative pronoun cannot be its subject; it is
the object, and the clause's subject is the pro-drop *tu*. `90.2 che` was `nsubj` ← 90.3 and is
now `obj` ← 90.3, with the case-annex row moving `nominative` → `accusative` (see
[`../case/CORRECTIONS.md`](../case/CORRECTIONS.md)). Layer 5 **−1**: the LLM had read it this way.

### paradiso 2:45 — `a guisa di` modifies the predicate it stands next to

"non dimostrato, ma fia per sé noto / **a guisa** del ver primo che l'uom crede" — "not
demonstrated, but self-evident, **in the manner of** the primal truth which man believes". `45.2
guisa` was `obl` ← 43.3 `vedrà`, two lines and one coordination away; it is now `obl` ← 44.7
`noto`, the adjective it qualifies. Layer 5 **−1**.

### paradiso 3:95 — `qual` is the indirect question's predicate complement

"per apprender da lei **qual fu la tela**" — "to learn from her what the web was". `95.5 qual`
was `det` ← 95.8 `tela`, a determiner reaching across its own copula; it is now `xcomp` ← 95.6
`fu`, the predicate complement it is. Layer 5 **−1**.

### paradiso 5:120 — `di noi` is what the enlightenment is *about*

"e però, se disii / **di noi** chiarirti" — "if you desire to be enlightened **about us**".
`chiarir-ti` already carries its object in the enclitic, so `noi` cannot be a second one; the
case annex reads it `ablative`, which is the oblique.

| token | was | now |
|---|---|---|
| 120.1 `di` | `case` ← 120.3 `chiarirti` | `case` ← 120.2 `noi` |
| 120.2 `noi` | `obj` ← 120.3 | `obl` ← 120.3 |

Layer 5 **−1**.

## 4 rows from the Layer-5 Purgatorio 31-33 read (2026-08-17)

The per-position read of Purgatorio 31-33's 14 Layer-5 soft violations (see
[`../skel/CORRECTIONS.md`](../skel/CORRECTIONS.md)) found four Layer-4 rows wrong, in three
places. Applied with a gated script that asserts the word *and* the current cell value at each
`(line, token)` before rewriting; `morph`/`np`/`dep`/`case --check` all re-run at 0 and `pytest`
at 441.

### purgatorio 31:15 — `fuor` is "furono", and the clause is copular

"al quale intender **fuor mestier** le viste" — "to understand which, the eyes were needed".
Layer 2 read `fuor` as an apocopated `fuori` (the adverb, correct one line earlier in "pinsero …
**fuor** de la bocca") and Layer 4 built the clause around `intender` accordingly. `fuor mestier`
is `essere` + a predicate nominal, so the clause head is `mestier` and the rest hangs off it, in
this corpus's copula-as-`cop` convention:

| token | was | now |
|---|---|---|
| 15.5 `mestier` | `obj` ← 15.3 | `acl:relcl` ← 14.5 |
| 15.4 `fuor` | `advmod` ← 15.3 | `cop` ← 15.5 |
| 15.7 `viste` | `nsubj` ← 15.3 | `nsubj` ← 15.5 |
| 15.3 `intender` | `acl:relcl` ← 14.5 | `advcl` ← 15.5 |
| 15.1 `al` | `case` ← 15.2 | `case` ← 15.3 |
| 15.2 `quale` | `obl` ← 15.3 | `obj` ← 15.3 |

The Layer-2 row and the case-annex row move with it (see
[`../morph/CORRECTIONS.md`](../morph/CORRECTIONS.md),
[`../case/CORRECTIONS.md`](../case/CORRECTIONS.md)). Layer 5 is unchanged in count: the position
turns from a `missing_arg` into a `missing_tuple`, because the LLM's own reading of the line was
built on the same mistag.

### purgatorio 32:67 — the simile belongs to the apodosis

"S'io potessi ritrar … **come pintor** che con essempro pinga / disegnerei com' io
m'addormentai". The comparison is with the drawing, not with the wishing: `pintor` was `obl` ←
64.4 `ritrar`, the protasis's verb, and is now `obl` ← 68.1 `disegnerei`. Layer 5 **−2** — the
LLM had it on `disegnerei` all along, and the mis-attachment was costing both halves of the pair.

### purgatorio 33:18 — the dative of possession

"quando con li occhi **li occhi mi** percosse" — "when she struck my eyes with her eyes". `mi` was
`det:poss` ← 18.6 `occhi`, the only clitic pronoun in a `det:poss` slot in the whole corpus (a
census of the shape returned exactly this one row); it is the *dativus sympatheticus*, an argument
of the verb. Now `iobj` ← 18.8 `percosse`, which is what the LLM read. Layer 5 **−1**. Because
the population was 1, this is an upstream anomaly and not a checker rule.

### purgatorio 33:109 — the seven ladies stop, they are not "made"

"quando s'**affisser** … / le sette **donne** al **fin** d'un'ombra smorta". Layer 4 had both
nominals as arguments of 105.8 `fassi`, four lines and two clauses away: `donne` as its `obj` and
`fin` as its `obl`. They are the subject and the locative of 106.3 `s'affisser`.

| token | was | now |
|---|---|---|
| 109.3 `donne` | `obj` ← 105.8 | `nsubj` ← 106.3 |
| 109.5 `fin` | `obl` ← 105.8 | `obl` ← 106.3 |

**This correction deliberately raises Layer 5's count**, −2 / +3. The two `missing_arg`s on
`fassi` go away and three positions open on `affisser`, because the LLM had given that clause the
subject `chi` from line 107 — its own misreading, which the wrong tree had been matching by
having no opinion at all. The same honest trade the Purgatorio 21-25 and 26-30 batches recorded:
the count is not the measure, the correctness of the parse is.

## 27 rows from the Layer-5 Purgatorio 21-25 read, and rule CV (2026-08-16)

The per-position read of Purgatorio 21-25's 33 Layer-5 soft violations (see
[`../skel/CORRECTIONS.md`](../skel/CORRECTIONS.md)) found 27 Layer-4 rows wrong — the largest
upstream count of the series, because two of its censuses swept shapes the read itself had only
one instance of. Applied with gated scripts that assert the word and the current cell value at
each `(line, token)` before rewriting; `morph`/`np`/`dep`/`case --check` all re-run at 0 and
`pytest` at 427.

### Eleven predicate nominals of `essere` (10 `obj`, 1 `nsubj`)

Rule CV (below) newly reported **inferno 23:103**, "**Frati godenti** fummo, e bolognesi" — where
`Frati` was the `nsubj` of a 1st-plural verb, and is in fact the predicate nominal of a pro-drop
"noi", the very mis-parse the subject-agreement check exists to find. Censusing the same shape
from the other side — a token in a *core* role under a finite `essere` — found 15 more, ten of
them predicate nominals recorded as `obj`, against **346** already recorded as `attr`, which is
this corpus's convention for the complement of a copula-as-head:

| line | row | line text |
|---|---|---|
| inferno 14:119 | `qual` | "e **qual sia** quello stagno" |
| inferno 23:93 | `chi` | "dir **chi tu se'** non avere in dispregio" |
| inferno 23:103 | `Frati` | "**Frati godenti fummo**, e bolognesi" (`nsubj` → `attr`) |
| inferno 23:107 | `tali` | "e **fummo tali**" |
| inferno 34:93 | `qual` | "**qual è** quel punto ch'io avea passato" |
| purgatorio 4:111 | `serocchia` | "che se pigrizia **fosse sua serocchia**" |
| purgatorio 17:36 | `nulla` | "perché per ira hai voluto **esser nulla**?" |
| purgatorio 20:22 | `Povera` | "**Povera fosti** tanto" |
| purgatorio 28:45 | `testimon` | "che soglion **esser testimon** del core" |
| paradiso 3:108 | `qual` | "Iddio si sa **qual** poi mia vita **fusi**" |
| paradiso 5:132 | `ch'` | "lucente più assai di quel **ch'ell' era**" |

The census's other five rows are **not** predicate nominals — a dative clitic ("che già **li** er'
al petto", inferno 12:83), a subject ("Quell' **altro** … fu Michele Scotto", 20:115), a reflexive
("e io **mi** fora", purgatorio 26:25) and two relative obliques (inferno 4:104, paradiso 3:21) —
each a different question, and none of them decided here. Layer 5 moved **±0**.

### Six reflexive clitics recorded as the clause's `nsubj`

The Purgatorio 21:12 position ("né **ci** addemmo di lei") is one of ten tokens the `case` annex
calls reflexive while Layer 4 gives them `nsubj`. Three of the ten are fused infinitives that
really are clausal subjects ("al maestro parve **di partirsi**", inferno 16:90; purgatorio 16:143;
paradiso 3:80) and one is a Layer-2 question left standing (inferno 32:66, where `se tosco **se'**`
is read as the pronoun *sé* twice over). The other six are the clitic of a pronominal verb, which
cannot be its own clause's subject, and become `expl`:

| line | row | line text |
|---|---|---|
| inferno 34:21 | `t'` | "ove convien che di fortezza **t'armi**" |
| purgatorio 21:12 | `ci` | "né **ci addemmo** di lei" |
| purgatorio 22:90 | `mi` | "ma per paura chiuso cristian **fu'mi**" |
| purgatorio 27:138 | `ti` | "**seder ti puoi** e puoi andar tra elli" |
| paradiso 1:22 | `ti` | "se mi **ti presti**" |
| paradiso 17:11 | `t'` | "ma perché **t'ausi**" |

Rules AB/AW/BD deliberately leave the 371 reflexive clitics Layer 4 parks in `obj`/`iobj`/`obl` as
notation rather than retagging them — which slot a clitic sits in is not a claim. `nsubj` is
different in kind: it asserts that the clause's subject is the clitic, which competes with the
pro-drop reading the verb's own person carries. Layer 5 moved **−2 / +4**; the four are at 22:90,
where the wrong `nsubj` had been hiding the LLM's own reading of `mi` as the subject of a
first-person verb.

### Nine rows from the read itself

| line | rows | what was wrong |
|---|---|---|
| 22:17 | `persona` | "quale / più strinse mai **di non vista persona**" was the `nsubj` of `strinse` while carrying its own `di` `case` child; it is the oblique the goodwill is felt toward |
| 22:26 | `poco`, `a`, `riso`, `pria`, `rispuose` | "Queste parole Stazio mover fenno / un poco **a riso** pria" — `a` was an `aux` and `riso` a past participle coordinated with `fenno`; with Layer 2's retag of `riso` to the noun, it is the prepositional goal of `mover`, and `rispuose` coordinates with `fenno` rather than with it |
| 24:71, 24:73 | `compagni`, `greggia` | "**lascia andar li compagni**", "sì lasciò **trapassar la santa greggia**" — the nominal was the `obj` of an intransitive infinitive; it is the infinitive's subject (and the matrix verb's object, which rule BI reads) |
| 25:67 | `che`, `petto` | "Apri a la verità **che** viene **il petto**" — the two were swapped: `il petto` is the object of the imperative and `che` the subject of `viene` |

The `fare`/`lasciare` + infinitive census this last row opened found **32** infinitives with an
`obj` child under a causative head, and the population is genuinely mixed — "vi facea **far le
grida**" is a real object, "lascia **muover li anni**" is not. It is a per-position reading job,
not a sweep, and only the two positions this batch read are retagged.

### Rule CV — the number exclusions ran before the person test

Rule CR (2026-08-16) narrowed the "1/2 plural head admits a singular member" exclusion to the
*number* test and delegated the coordinate case to "the conjunct branch below", which tests person
member by member. Returning from the exclusion is what stops that branch from running, so a
coordinated subject reached it and left with no person test at all: "Né 'l dir l'andar, né l'andar
lui più lento / facea, ma ragionando **andavam** forte" (purgatorio 24:2), where `derive_unit`
inherits two third-person nouns onto a first-plural verb.

The same defect was in **five more** exclusions, every one of them a *number* licence —
*coordination inside the subject phrase*, *comitative phrase on a plural head*, *quantified subject
read as one measure*, *copula agreeing with its predicate nominal*, *impersonal `si` with a
postposed notional subject*. Each returned "undecidable" for both features. They now record that
the number half is undecidable and let the person test run first; a pair that clears the person
test and holds one of these licences comes out undecidable from exactly the reason it did before.

Two further halves of the same rule, both found by measuring:

- **a coordination is a chain, not a fan** — Layer 4 writes "La bella donna … e Stazio e io"
  (purgatorio 32:28) as `donna` ← `Stazio` ← `io`, so the members are reached by walking `conj`
  transitively. The direct-children walk lost the `io` that carries the coordination's person and
  reported the pair.
- **`tutto` joins `_DISTRIBUTIVE_LEMMAS`** — "là 've già **tutti e cinque sedavamo**" (9:12), "e
  **tutti eravamo** già vòlti" (27:85). "Tutti e cinque" names the whole of the "we" the verb
  carries, so its third person is the quantifier's, exactly as `ambedue`'s is; neither member of
  the coordination is a first-person word the person test could find.

With those two in place the refinement leaves **one** new position, inferno 23:103, corrected
above, and the check returns to **0 hard / 0 soft**. Layer 5 moved **−3**.

## 17 rows from the Layer-5 Purgatorio 16-20 read, and rule CR (2026-08-16)

The per-position read of Purgatorio 16-20's 26 Layer-5 soft violations (see
[`../skel/CORRECTIONS.md`](../skel/CORRECTIONS.md)) found 17 Layer-4 rows wrong, ten of them
in canto 16 — the second batch running where one canto carries the tree's errors while
`dep --check` stands at 0. Applied with a gated script that asserts the word and the
current cell value at each `(line, token)` before rewriting; `morph`/`np`/`dep`/`case
--check` all re-run at 0 and `pytest` at 414.

| line | rows | what was wrong |
|---|---|---|
| 16:43 | `anzi`, `morte` | "chi fosti **anzi la morte**" was an `advmod` plus a `vocative`; it is a prepositional phrase on `fosti` |
| 16:64 | `sospir` | "**Alto sospir** … mise fuor prima" — the sigh was the `nsubj` of `mise`; it is its object |
| 16:98-99 | `Nullo`, `però`, `che`, `può`, `ha` | "Nullo, **però che** 'l pastor … rugumar può, ma non ha l'unghie fesse" — `che` was the `obj` of `rugumar`; it is the second word of the causal conjunction. `Nullo` is the elliptical answer to "chi pon mano ad esse?" and heads its clause, `può` is the because-clause under it, and `ha` is `può`'s coordinate, sharing `'l pastor` |
| 16:129 | `sé`, `soma` | with Layer 2's retag of `brutta` to the verb *bruttare*, its two objects |
| 17:111 | `da`, `quello`, `odiare` | "**da quello odiare** ogne effetto è deciso" — the `da` was on `quello`; it governs the infinitive, whose own object `quello` is |
| 18:50 | `è`, `unita` | "ed **è** con lei **unita**" — `unita` was an `amod` on the verb; it is the participial predicate and `è` its `cop`, the convention the rest of the corpus uses |
| 18:117 | `nostra` | "se villania **nostra giustizia** tieni" — the possessive belongs to the object, not to the predicative complement (the Layer-3 span moved with it) |
| 18:140 | `che` | "tanto divise … **che** veder più non potiersi" — the consecutive `che` of "tanto … che" was the `obj` of `veder`; it is the clause's `mark` |

### Rule CR — `subject_agreement`'s 1/2-plural exclusion covers number, not person

The exclusion "a 1st/2nd person **plural** head admits a singular member" exists because the tree
may hold only one member of the "io e tu" the verb agrees with. That is a statement about
*number*, and it was swallowing the *person* test with it: a lone third-person subject cannot be a
member of a "we" at all. "Ciò ch'io dicea … contrario suon **prendemo**" (purgatorio 20:102) is
the evidence — `Ciò` is the subject of the *first* conjunct, and Layer 5's rule AG could not drop
it because this function called the pair undecidable. The exclusion now applies only to a subject
that could be such a member: a 1st or 2nd person word, or a coordination, whose person the
conjunct branch tests member by member.

Narrowing it surfaced **3** new soft violations, all one shape — `ambedui` (purgatorio 4:52),
`amendue` (12:11) and the distributive `uno` ("**uno** innanzi altro, ce n'andavamo", 26:1)
standing in for the whole of a "we" the verb already carries. That is the notional reading
`_DISTRIBUTIVE_LEMMAS` already names for `ciascuno`/`ognuno`/`catuno`, so the three lemmas join
that set, read one by one, and the check returns to **0 hard / 0 soft**. Layer 5 moved **−2**.

## 11 rows from the Layer-5 Purgatorio 11-15 read, and the coordinated-subject refinement (2026-08-16)

The per-position read of Purgatorio 11-15's 30 Layer-5 soft violations (see
[`../skel/CORRECTIONS.md`](../skel/CORRECTIONS.md)) found 11 Layer-4 rows wrong, ten of them in
Purgatorio 14. Applied with a gated script that asserts the word at each `(line, token)` before
rewriting; `morph`/`np`/`dep`/`case --check` all re-run at 0 and `pytest` at 384.

| position | was | now | why |
|---|---|---|---|
| purgatorio 11:19.2 `virtù` | `vocative` <- 20.2 | `obj` <- 20.2 | "Nostra virtù … **non spermentar** con l'antico avversaro" — the Paternoster asks that our strength not be *put to the test*; the addressee is God, unnamed in the line |
| purgatorio 12:26.1 `più` | `advmod` <- 27.2 | `advmod` <- 25.5 | the comparison belongs to `nobil creato`, not to the `scender` three words later |
| purgatorio 12:26.4 `creatura` | `obj` <- 27.2 | `obl` <- 25.5 | with `più` on the infinitive, the second term of the comparison had become its object |
| purgatorio 12:136.2 `che` | `obl` <- 136.7 | `obl` <- 136.3 | "**a che guardando**, il mio duca sorrise": the gerund governs it, not the matrix verb |
| purgatorio 14:11.2 `corpo` | `obl` <- 11.8 | `obl` <- 10.8 | "O anima che **fitta** / **nel corpo** ancora … ten vai" — the participle takes the oblique |
| purgatorio 14:15.3 `cosa` | `obj` <- 15.2 | `nsubj` <- 15.2 | "quanto vuol **cosa** che non fu più mai": the thing is what requires |
| purgatorio 14:69.1-.6 (5 rows) | see below | | the `parte` re-parse |
| purgatorio 14:89.7 `nullo` | `det` <- 90.1 | `nsubj` <- 90.1 | a pronoun is not a determiner of a participle; `nullo` is who has not become heir |
| purgatorio 14:90.1-.5 (4 rows) | see below | | the `fatto s'è reda` re-parse |
| purgatorio 14:131.5 `aere` | `nsubj` <- 131.6 | `obj` <- 131.6 | "quando **l'aere fende**": the lightning cleaves the air |
| purgatorio 29:37.5 `fami` | `nsubj` <- 38.7 | `obj` <- 38.7 | "se **fami**, / freddi o vigilie mai per voi **soffersi**" — "if I ever suffered hunger for you" |

**purgatorio 14:69**, "da qual che parte il periglio l'assanni". Layer 2 read `parte` as the verb
`partire` (corrected in [`../morph/CORRECTIONS.md`](../morph/CORRECTIONS.md)), which made "from
whatever side" a clause: `da` marked `qual`, `qual` was the clause's oblique, `che` its `mark`,
`parte` an `advcl`, and `il periglio` its subject — leaving `assanni` with no subject of its own
and inheriting one across `conj`. Rewritten as one nominal: `da` `case`-> `parte`, `qual` `det`->
`parte` with `che` `fixed`-> `qual`, `parte` `obl`-> `assanni`, and `il periglio` `nsubj`->
`assanni`. Three Layer-5 violations cleared.

**purgatorio 14:90**, "ove nullo / fatto s'è reda poi del suo valore" — "where no one has since
made himself heir to his worth". Layer 4 headed the clause on `reda` (which Layer 2 read as a past
participle; it is the noun *erede*) and made the participle `fatto` its subject. Rewritten with
`fatto` as the clause head (`acl:relcl`-> `casa`), `s'`/`è`/`poi` moved onto it, `reda` its
`xcomp`, and `nullo` its subject.

**The coordinated-subject person test.** `subject_agreement` returned "undecidable" for any
subject carrying a `conj` child, which suppressed the *person* test along with the number one. A
coordination has no fixed number — "'l duca e io" is two singulars governing a plural verb —
but it does have a person, and Italian lets the finite verb agree with **one member** of it, in
either direction. The test now compares the head's person against **every conjunct** and reports
only when none matches.

The 2026-08-15 Inferno 21-25 measurement of the *number*-only restriction (12 new soft violations,
reverted, and a standing route since) was therefore half right: the same 12 positions under the
any-conjunct rule leave **6**, and all 6 are real upstream errors, corrected in the same session —
five Layer-2 rows (inferno 21:121, purgatorio 5:83, 10:63, paradiso 14:125 ×2, 31:96, see
[`../morph/CORRECTIONS.md`](../morph/CORRECTIONS.md)) and one Layer-4 row (purgatorio 29:37,
above). `dep --check` is back to **0 hard / 0 soft** with the refinement landed. Layer 5 moved
**−3 / +1**.

## 1 row from the Layer-5 Purgatorio 6-10 read (2026-08-16)

The per-position read of Purgatorio 6-10's 35 Layer-5 soft violations (see
[`../skel/CORRECTIONS.md`](../skel/CORRECTIONS.md)) found 1 Layer-4 row wrong. Applied with a gated
script that asserts the expected word *and* deprel *and* head at `(line, token)` before rewriting;
`morph`, `np`, `dep` and `case --check` all stay 0 afterwards, `pytest` 372.

**A participle attached to a noun it cannot agree with** — purgatorio 9:4-5, "di gemme la sua
fronte era lucente, / **poste** in figura del freddo animale": `poste` is f. **pl.** and `fronte`
is f. sg., so the adnominal participle cannot modify the head Layer 4 gave it; `gemme` (f. pl.) is
the only nominal in the parse unit it agrees with, and it is the gems that are *set* in the figure
of the cold animal. `poste` moved from `acl<-4.5` (`fronte`) to `acl<-4.2` (`gemme`). Layer 3's
spans read the same way, and the Layer-5 artifact had already named `gemme` as its subject.

Layer 5 fell by 1 with it.

## 2 rows from the Layer-5 Purgatorio 1-5 read (2026-08-16)

The per-position read of Purgatorio 1-5's 14 Layer-5 soft violations (see
[`../skel/CORRECTIONS.md`](../skel/CORRECTIONS.md)) found 2 Layer-4 rows wrong. Applied with a
gated script that asserts the expected word *and* deprel *and* head at each `(line, token)` before
rewriting; `morph`, `np`, `dep` and `case --check` all stay 0 afterwards, `pytest` 351.

**An epithet's modifier read as the verb's oblique** — purgatorio 5:77, "**quel da Esti** il fé
far": `da Esti` says *which* `quel`, it is not an oblique of the causative. `Esti` moved from
`obl<-77.6` (`far`) to `nmod<-77.1` (`quel`); its `case` child `da` already pointed at it. Layer 3
reads the same span as one noun phrase, `[quel da Esti]` headed on `quel`.

**A postposed subject read as the object** — purgatorio 5:135, "**salsi colui** che 'nnanellata
pria / disposando m'avea con la sua gemma": `salsi` is `sa` + the pronominal `si`, and the line
means "lo sa colui" — the one who first wedded me *knows* it. `colui` moved from `obj<-135.1` to
`nsubj<-135.1`, and the `case` annex row moved accusative → nominative with it (see
[`../case/CORRECTIONS.md`](../case/CORRECTIONS.md)).

Layer 5 fell by 2 with the pair.

## 15 rows from the Layer-5 Inferno 31-34 read (2026-08-16)

The per-position read of Inferno 31-34's 37 Layer-5 soft violations (see
[`../skel/CORRECTIONS.md`](../skel/CORRECTIONS.md)) found 6 Layer-4 rows wrong and normalized 9
more. Applied with gated scripts that assert the expected word *and* deprel *and* head at each
`(line, token)` before rewriting; `morph`, `np`, `dep` and `case --check` all stay 0 afterwards,
`pytest` 342.

**A prepositional phrase on the wrong clause** — inferno 31:89, "d'una catena che 'l tenea avvinto
/ **dal collo in giù**, sì che 'n su lo scoperto / si ravvolgëa": the phrase says how the chain
bound him, not how it wound round. `collo` moved from `obl<-90.2` (`ravvolgëa`) to `obl<-88.6`
(`tenea`), and `giù` from `obl<-90.2` onto `collo` — which is also the convention this very canto
already uses at 31:62 ("dal mezzo in giù") and 31:66 ("dal loco in giù"), where `giù` hangs on the
nominal.

**An embedded question on the outer verb of speech** — inferno 32:44, «Ditemi, voi che sì
strignete i petti», / diss' io, «**chi siete**?». `siete` was `ccomp<-44.1` (`diss'`), which
already carries the whole quotation; the question is what `Ditemi` asks for, so it is
`ccomp<-43.1`.

**A subject read as a modifier inside the object phrase** — inferno 34:105, "da sera a mane ha
fatto **il sol** tragitto?". `sol` was `amod<-105.9`, making "il sol tragitto" one noun phrase;
the sun is the subject of `ha fatto` and `tragitto` its object. `sol` → `nsubj<-105.6`, `il` →
`det<-105.8`. Layer 3's span was split to match (see [`../np/CORRECTIONS.md`](../np/CORRECTIONS.md)).

**An object read as the next clause's subject** — inferno 31:143, "al fondo che divora /
**Lucifero con Giuda**, ci sposò". `Lucifero` was `nsubj<-143.5` (`sposò`, whose subject is the
pro-drop Antaeus) and is the object of `divora`; `Giuda` moved with it. **Count-neutral by
construction** (−1 / +1: the LLM had read `con Giuda` as `sposò`'s oblique, which is now correctly
reported) and kept anyway — the count is not the measure, the correctness of the parse is.

**`con esso` normalized to the prep-stack shape — 9 rows, 4 cantos, 3 canticles.** The reinforced
preposition "con esso" ("con esso i piè", "con esso un colpo") carried four different Layer-4
shapes in its four occurrences: `esso` as an `obl` sibling of the nominal (inferno 32:62,
purgatorio 4:27), the nominal as `appos` under `esso` (purgatorio 24:98), and the nominal as the
verb's `nsubj` (inferno 22:88). This is the same shape lottery the 2026-08-14 multiword-preposition
normalization closed, so it gets the same shape: opening word `con` → `case` on the nominal, later
member `esso` → `fixed` on `con`, and the nominal takes the role. The fifth "con esso" (paradiso
25:131, "si quïetò con esso il dolce mischio") is genuinely pronominal — `esso` is "with it" and
`il dolce mischio` the subject — and was left alone. Layer 5 reads the new shape through rule BV.

## 10 rows from the Layer-5 Inferno 26-30 read (2026-08-15)

The per-position read of Inferno 26-30's 23 Layer-5 soft violations (see
[`../skel/CORRECTIONS.md`](../skel/CORRECTIONS.md)) found 10 Layer-4 rows wrong, in two groups.
Applied with a gated script that asserts the expected word *and* deprel *and* head at each
`(line, token)` before rewriting; `morph`, `np`, `dep` and `case --check` all stay 0 afterwards,
`pytest` 326.

**Reflexive clitics parked in the subject slot** — `piegarsi`, `rissarsi`, `assidersi` are
pronominal verbs, so the clitic is the `expl` the lemma carries and the subject is pro-drop,
which is how every other reflexive in the corpus is recorded. Found by censusing `nsubj` rows
whose Layer-2 note says `reflexive`: 9 hits, of which these 3 are bare clitics and the rest are
infinitives with an enclitic, correctly `nsubj` of an impersonal verb.

| position | word | before | after | why |
|---|---|---|---|---|
| inferno 26:69.7 | `mi` | `nsubj<-69.8` | `expl<-69.8` | "del disio ver' lei **mi** piego" — the reflexive of `piegarsi` |
| inferno 30:132.7 | `mi` | `nsubj<-132.8` | `expl<-132.8` | "per poco che teco non **mi** risso" — the reflexive of `rissarsi`; the subject slot it occupied produced both of that position's violations |
| paradiso 1:140.4 | `ti` | `nsubj<-140.6` | `expl<-140.6` | "giù **ti** fossi assiso" — the reflexive of `assidersi` |

**The accusative-and-infinitive at inferno 29:73**, and the `scardova` re-parse:

| position | word | before | after | why |
|---|---|---|---|---|
| inferno 29:73.3 | `due` | `nummod<-73.4` | `nsubj<-73.4` | "Io vidi **due** sedere" — the shared nominal is the infinitive's subject, not a numeral modifying it; this is the shape rule BI reads |
| inferno 29:83.1 | `come` | `mark<-83.4` | `mark<-83.2` | the comparison's marker follows its new head |
| inferno 29:83.2 | `coltel` | `nsubj<-83.4` | `advcl<-82.3` | "come coltel [fa] le scaglie" is a *gapped* clause: `coltel` is the promoted remnant that heads it |
| inferno 29:83.4 | `scardova` | `advcl<-82.3` | `nmod<-83.2` | the fish, not a verb (Layer 2 retagged with it) — and `di scardova` modifies `coltel`, which is what Layer 3's NP span already says |
| inferno 29:83.6 | `scaglie` | `obj<-83.4` | `orphan<-83.2` | UD's own marking for a gapped clause's second remnant |
| inferno 29:84.1, 84.4 | `o`, `pesce` | `cc<-84.9`, `obl<-84.9` | `cc<-84.4`, `conj<-83.4` | "di scardova **o d'altro pesce**" coordinates the two genitives, not the relative clause |
| inferno 29:84.9 | `abbia` | `conj<-83.4` | `acl:relcl<-84.4` | "che più larghe l'abbia" is the relative clause of `pesce` |

## 20 rows from the Layer-5 Inferno 21-25 read (2026-08-15)

The per-position read of Inferno 21-25's 44 Layer-5 soft violations (see
[`../skel/CORRECTIONS.md`](../skel/CORRECTIONS.md)) found 20 Layer-4 rows wrong. Applied with a
gated script that asserts the expected word at each `(line, token)` before rewriting; `morph`,
`np`, `dep` and `case --check` all stay 0 afterwards, `pytest` 311.

| position | word | before | after | why |
|---|---|---|---|---|
| inferno 21:53.2 | `Coverto` | `vocative<-53.1` | `obl<-53.6` | "Coverto convien che qui balli" — a depictive on the subject of `balli`, not an address |
| inferno 22:27.7-9 | `l'altro grosso` | `grosso amod<-altro` | `grosso conj<-piedi`, `altro amod<-grosso` | Layer 3 already reads `grosso` as the phrase head; `altro` modifies it |
| inferno 22:32.4-6, 33.4 | `com' elli 'ncontra ch'…` | `'ncontra advmod<-rimane` | `'ncontra advcl<-aspettar`, `elli nsubj<-'ncontra`, `rimane ccomp<-'ncontra` | `'ncontra` is the impersonal verb (Layer 2 retagged with it), so it heads its own clause |
| inferno 22:99.1 | `Toschi` | `obj<-venire` | `nsubj<-venire` | causative `far venire`: the causee is the infinitive's subject |
| inferno 22:103.9 | `sette` | `obj<-venir` | `nsubj<-venir` | the same construction, four lines on |
| inferno 23:138.8 | `soperchia` | `amod<-ruina` | `conj<-giace` | the verb `soperchia`, not the adjective `soperchio` (Layer 2 retagged with it) |
| inferno 23:141.6 | `qua` | `obl<-uncina` | `nmod<-peccator` | "i peccator **di qua**" modifies the noun, not the verb |
| inferno 24:22.2-3 | `Le braccia aperse` | `aperse acl<-braccia`, `braccia obl<-diedemi` | `aperse conj<-diedemi`, `braccia obj<-aperse` | "he opened his arms": `aperse` is the verb (Layer 2 retagged with it) |
| inferno 24:25.2 | `come` | `advmod<-avvisava` | `mark<-quei` | comparative `come` marks its own nominal, as at 24:11 — and Layer 2 calls it a conjunction, which is what rules AK/AR read |
| inferno 24:37.4, 37.6 | `inver' la porta` | `inver' advmod<-pende`, `porta obj<-pende` | `inver' case<-porta`, `porta obl<-pende` | `pendere` takes no object; `inver'` is the phrase's preposition |
| inferno 24:124.7 | `umana` | `conj<-bestial` | `conj<-Vita` | "e non umana" is gapped `[vita] umana`, a conjunct of the noun, not of its adjective |
| inferno 25:68.5 | `ti` | `nsubj<-muti` | `expl<-muti` | a reflexive clitic is never a subject ("come ti muti") |

Layer 5 measured the whole set together at **−11 / +4** — three of the four new positions are the
retags exposing a divergence the wrong parse had hidden, written up in
[`../skel/CORRECTIONS.md`](../skel/CORRECTIONS.md).

**Left standing, measured**: restricting `subject_agreement`'s *coordinated subject* exclusion to
the number test only (a coordination of nominals is third person however many members it has)
takes `dep --check` from 0 to **12** soft violations. Each is a real question about a Layer-4
subject attachment, and clearing them is a read of its own; the refinement was reverted rather
than landed with a non-zero check. Positions: inferno 2:33, 8:28, 21:121, 25:36; purgatorio
4:102, 5:82, 10:62, 23:113, 29:37; paradiso 14:125, 19:12, 31:96.

## `RELCL_HEAD` substantivization flag (2026-07-12)

After the LLM-based `--fix` pass (unit regeneration, `make -C dep fix`) resolved every
deprel-vocabulary and multiple-root soft violation, all **132** remaining soft violations were
of a single kind: `acl:relcl head is 'POS', not nominal`. Mechanically enumerating every case
(canticle, canto, head word, head POS, head's own deprel — no model call, just reading the
committed TSVs) showed these were not parse errors at all, and the model had made the same
judgment call every time `--fix` regenerated the unit, which is why blind regeneration never
improved them:

- **Closed-class substantivized pronouns/quantifiers (95 of 132)** — demonstratives (`quel`,
  `quello`, `quelli`, `que'`, `tal`, `tale`, `cotesti`, …), indefinites (`altro`, `altri`, `molti`,
  `alcuna`, …), and cardinal/quantifier numerals (`due`, `tre`, `cinque`, `mille`, …) used
  pronominally with an elided noun (`quei due che 'nsieme vanno` — "those two who go together";
  `più di mille... piovuti` — "more than a thousand... fallen"). Archaic/poetic Italian relies on
  this ellipsis constantly; Layer 2 correctly tags the word's literal part of speech
  (adjective/numeral), which is simply not what UD's "nominal antecedent" check expects.
- **One-off substantivized adjectives/participles/infinitives (26 of 132)**, checked individually
  against their terzina context, same shape: `le triste` ("the sad women", inferno 20:121),
  `li 'mpaniati` ("the birdlime-caught", inferno 22:149), `li eletti` ("the elect", purgatorio
  19:76), `libero voler` (infinitive-as-noun "free will", purgatorio 16:76), `il primo` ("the
  first one", paradiso 8:111), etc.
- **Locative/quotative antecedents (10 of 132)** — `là dove`/`là 've`/`là onde` ("there where"),
  a fixed relative-locative construction where the place adverb stands in for a place noun-phrase,
  plus one quoted-word-as-noun case (`un tal «sì»`, purgatorio 31:14). Same non-nominal-POS,
  legitimate-antecedent shape as the two categories above, so folded into the same flag rather
  than inventing a second mechanism.

Each of the 131 candidate positions was checked against its terzina context before flagging (not
a blanket rule for these word forms in general — the same caution `NO_NP`/`CONT_NEXT` used in
`morph/CORRECTIONS.md`). One case did **not** qualify: inferno 19:73-74
(`son li altri tratti / che precedetter me simoneggiando`) attached the relative clause to
`tratti` (a passive participle, "[they are] dragged") rather than to `altri` ("the others"), its
more plausible antecedent — a genuine mis-attachment, not a substantivization, reproduced
identically across `--fix` regenerations (see below for its resolution).

Following `np.py`'s `NO_NP`/`CONT_NEXT` precedent, each qualifying token's Layer-2 `note` column
now carries a machine-readable `RELCL_HEAD` flag, comma-separated alongside any existing note
(e.g. `archaic` -> `archaic, RELCL_HEAD`; an empty note becomes `RELCL_HEAD` on its own).
`dante_corpus/dep.py`'s `_is_nominal` now treats a non-nominal-POS head as valid for `acl:relcl`
if its note carries `RELCL_HEAD`. 129 distinct `(line, token)` positions were flagged across 71
cantos (a few positions are the head of more than one relative clause, e.g. inferno 11:62-63 both
citing `62.5 quel`, so the flagged-position count is slightly below the 131 qualifying rows).

`dep --check` after this flagging pass: **0 hard, 1 soft** (down from 132; the `tratti` case
above). `morph --check` and `np --check` remain 0 hard / 0 soft — the new flag doesn't intersect
`_needs_np`'s exemption set, so Layer 3 is unaffected.

## Inferno 19:73-74 `tratti`/`altri` mis-attachment, hand-corrected (2026-07-12)

The last soft violation, re-run through `make -C dep fix` once more, was unchanged
(`0/1 unit(s) improved`) — confirming it wasn't build noise but a systematic, reproducible parse
choice. Unlike the `RELCL_HEAD` cases, `tratti` here is a genuine passive-voice predicate
(`son... tratti` = "are dragged"), not a substantivized noun standing on its own — `altri` ("the
others") is the real subject and the relative clause's real antecedent. Following the same
hand-verified, single-instance correction the `Rife` mistag used (`morph/CORRECTIONS.md`), the
three affected rows in `dep/inferno/19.tsv` were corrected directly (no model call): `li` (det)
and `precedetter` (`acl:relcl`) now point to `altri` (73.8) instead of `tratti` (73.9); `altri`
itself becomes `nsubj` of `son`; `tratti` becomes `acl` of `altri` (a participial modifier, "the
others, dragged"). `altri`'s Layer-2 `note` picked up `RELCL_HEAD` (it wasn't previously an
`acl:relcl` head anywhere, so hadn't needed the flag).

`dep --check`: **0 hard, 0 soft** — Layer 4 fully clean across all 100 cantos.

## Double-`obj` clitic datives, retagged from the Layer-5 audit (2026-07-28)

Layer 5 is designed so a divergence can surface a genuine Layer-4 mis-parse (see
[`../skel/README.md`](../skel/README.md)); this is the first correction it produced. The skel
checker's Phase 5h measurement left 97 instances where the LLM — which never sees this parse —
labels a **clitic** `obl:a`/`obl:di` and Layer 4 tags it `obj`. Italian clitics are
case-syncretic and Layer 2 records no case feature, so most of those are undecidable here. **30
are not**, and the discriminator is structural, not lexical: in those the predicate carries
**another** `obj` child as well, and UD allows at most one `obj` per predicate — the tree is
internally inconsistent regardless of what the LLM says, and the non-clitic object is the direct
one.

All 30 were read against their terzina before any edit, and **four were rejected**:

- purgatorio 21:21 `chi v'ha per la sua scala tanto scorte?` — `v'` is accusative "you (pl)";
  the other `obj`, `scorte`, is the participle of the periphrasis, itself the questionable tag.
- purgatorio 22:102 `che le Muse lattar più ch'altri mai` — `altri` is the comparative term,
  not an argument.
- paradiso 28:106 `e dei saper che tutti hanno diletto` — `che` is the complementizer.
- paradiso 30:140 `simili fatti v'ha al fantolino` — existential `v'ha`; `v'` is locative, so
  neither side's label is right and nothing is decided.

The remaining **26** rows in `dep/<canticle>/NN.tsv` were rewritten directly, no model call, in
the same hand-verified single-instance style as the `tratti`/`altri` correction above:

- **22 → `iobj`** — dative clitic with a real direct object beside it: `li arruncigliò le
  'mpegolate chiome`, `li avvinse la pancia`, `li volse le novelle spalle`, `il collo li
  avvinghiai`, `m'impedì l'andare`, `Quest' opera li tolse quei confini`, `lume il volto mi
  percosse`, `li assegnò sette e cinque`, `qual ti negasse il vin`, `Dio li aperse` (l'occhio),
  `morte tempo li prescriba`, `li danno guerra`, `mi girò la fronte`, `li dice il vero`, `ogne
  nube li disleghi`, and the enclitic-fused `gliel'` of `tutto gliel' apersi`.
- **4 → `obl`** — partitive/ablative `ne`, where no dative reading applies: `voi ne orate
  cento`, `ne portò un lacerto`, `tante n'abbia`, `Ben te ne puoi accorger`. `derive_unit`
  emits a bare `obl` for these (no `case` child), which skel's rule L already reconciles with
  the LLM's `obl:di`/`obl:da`.

`dep --check` after the retag: **0 hard, 0 soft** — unchanged. `skel --check`: **4068 → 4042
soft** (−26, all `role_mismatch`), i.e. every corrected row also closed its Layer-5 divergence.
The 26 cantos' content hashes change, as expected for an artifact correction.

**Left open, deliberately**: the other 67 of the 97 (predicate has no second `obj`, so nothing
structural decides the case), and the 30 mirror-direction instances where Layer 4 says `iobj`
and the LLM says `obj` (`mi bagna`, `mi tormenta`, `ti conforta`, `m'avean pregato` — several
of which look like genuine Layer-4 datives over accusatives). Both need a Layer-2 case feature
or a clitic lexicon; see [`../skel/PLAN.md`](../skel/PLAN.md).

**A wider finding, not acted on here**: enumerating the whole corpus, **231** predicates carry
two or more `obj` children — 84 of them involving a clitic, 147 not. The non-clitic majority is
a mix of flattened coordinations (`Ali hanno late, e colli e visi umani` — every conjunct
attached straight to the verb instead of chaining with `conj`) and object complements (`mi
chiamaste Ciacco`, `li chiama orbi`, `si tegnon gran regi` — the predicative noun tagged `obj`).
Neither is decidable by the double-`obj` signal alone, and the second class is exactly what
skel's rule M already accepts checker-side. A `--check` rule for "at most one `obj` per
predicate" would put Layer 4 at 231 soft violations; opening it is a separate round.

## Relative/interrogative words mistagged `mark`, retagged from the Layer-5 audit (2026-07-28)

The second Layer-4 correction Layer 5's audit role produced (see the double-`obj` round above
for the procedure). skel's Phase 5m triage of the `extra_arg` **direct-child** bucket left 35
instances where Layer 4 tags a relative or interrogative word `mark` on a predicate while the
LLM — which never sees this parse — cites that same token as an argument of it. Layer 2's POS
is not a usable discriminator here: it calls most of these words "conjunction", including the
ones that are plainly relative pronouns. So all 35 were read against their terzine by hand, and
the population turned out **mixed**, exactly as the clitic one had been.

**22 retagged** in `dep/<canticle>/NN.tsv`, no model call, one row each — the word fills an
argument slot of the predicate and `mark` is a mistag. The target deprel is the one it fills,
and each was checked not to duplicate a core argument the predicate already carries:

- **8 → `obl`** — relative/interrogative adverbs and temporal relatives: `domandollo **ond'** ei
  fosse` (inferno 22:47), `volse la testa **ov'** elli avea le zanche` (inferno 34:79), `là
  **onde** vegnon tali a la scrittura` (paradiso 12:125), `dì **onde** a te venne` (paradiso
  25:47), `Da l'ora **ch'**ïo avea guardato prima` (paradiso 27:79), `Dal primo giorno **ch'**i'
  vidi il suo viso` (paradiso 30:28), `**ond'** io mi feci ancor più là sentire` (purgatorio
  13:99), `ne li occhi **ove** 'l sembiante più si ficca` (purgatorio 21:111).
- **7 → `obj`** — relative and quantifier pronouns filling the direct-object slot: `poi mi
  farai, **quantunque** vorrai, fretta` (inferno 32:84), `**qual** fece la figliuola di Minoi`
  (paradiso 13:14), `miri a ciò **ch'**io dissi suso` (paradiso 13:46), `ché **quantunque** la
  Chiesa guarda` (paradiso 22:82), `dal punto **che** 'l cenìt inlibra` (paradiso 29:4), `per la
  ragion **che** di'` (purgatorio 4:82), `non per conforto **ch'**io attenda di là` (purgatorio
  20:41).
- **7 → `attr`** — predicative `qual`/`quai`/`che` on a copular or change-of-state predicate:
  `che **qual** voi siete, tal gente venisse` (inferno 16:57), `**quai** son color che stanno`
  (inferno 19:58), `per un **ch'**io son` (inferno 22:103), `ciascuna cosa **qual** ell' è
  diventa` (paradiso 20:78), `**qual** diverrebbe Iove` (paradiso 27:14), `mi specchiai in esso
  **qual** io paio` (purgatorio 9:96), `dimmi **che** è cagion` (purgatorio 26:110).

**11 left as they are** — Layer 4 is right, or nothing decides:

- complex subordinators, where the LLM citing the second element as an argument is a plain
  misreading: `secondo **ch'**avea detto la mia scorta` (inferno 12:54), `secondo **ch'**elli
  ascolta` (purgatorio 24:144).
- comparative and consecutive `che`: `più speso **che** non stimava l'animo` (purgatorio 12:75),
  `lo più **che** padre mi dicea` (purgatorio 23:4), `volse a lei, **che** ' miei ... fé più
  ardenti` (paradiso 31:142), `l'ultimo **che** voli` (paradiso 24:15).
- idiomatic concessives, undecidable: `**qual che** si sia` (paradiso 22:114), `**che che** li
  appaia` (purgatorio 25:5), and the frozen `un non sapeva **che** bianco` (purgatorio 2:23).
- degree `quanto` as a subordinator: `**quanto** ragione umana vede` (paradiso 19:74).
- `**che** vedrai non capere in questi giri` (paradiso 3:76) — the editorial reading `ché`
  (causal) versus relative `che` is itself disputed; not decided here.

**2 read but deliberately not acted on**, because a sound fix needs a multi-edge restructuring
rather than the single-row retag this round is scoped to, and a partial one would create a
second core argument on the same predicate:

- purgatorio 8:114 `tanta cera **quant'** è mestiere` — `quant'` is the subject of `è`, but
  Layer 4 already has `mestiere` as `nsubj` where it is the predicate nominal (`attr`).
- purgatorio 22:15 `Giovenale, **che** la tua affezion mi fé palese` — `che` is the subject
  (antecedent Giovenale), `affezion` the object and `palese` the predicative complement; Layer 4
  has `affezion` as `nsubj`, `palese` as `obj`, and attaches `fé` to `ora` rather than to
  `Giovenale`.

`dep --check` after the retag: **0 hard, 0 soft** — unchanged. `skel --check`: **3746 → 3725
soft** (−21). All 22 closed their `extra_arg`; the net is −21 because paradiso 27:79 converts
rather than closes — there `ch'` is a temporal oblique, and the LLM had cited it as an `obj`, so
the divergence is now correctly reported as a `role_mismatch` against a reading that is still
wrong. The 19 cantos' content hashes change, as expected for an artifact correction.

## Clausal complements mistagged `advcl`, plus the two `mark` deferrals (2026-07-28)

The third and fourth Layer-4 correction rounds Layer 5's audit produced, run together (same
procedure as the two rounds above). Two populations, 14 rows across 7 cantos, no model call:

**Round A — `advcl` over a clausal complement (7 rows, 6 units).** skel's Phase 5o verdict on the
`extra_arg` direct-child `advcl` bucket left 35 instances where Layer 4 attaches a clause as an
adverbial (`advcl`) while the LLM — which never sees this parse — cites it as a complement
(`ccomp` 18, `xcomp` 14, `subj` 2, `obj` 1) of the same predicate. The complement-vs-adjunct
distinction is not mechanizable here (it needs a verb lexicon; see [`../skel/PLAN.md`](../skel/PLAN.md)),
so all 35 were read against their terzine with the whole dep sub-tree, and the corpus-wide
convention was measured first: `ccomp` is a live tag for clauses marked by `che`/`ch'` (520),
`se` (45) and `come` (48), and `csubj` for `che` (24), so each retag below uses a deprel the
corpus already uses for that marker.

**6 retagged**, each an argument slot of the matrix predicate that no other core argument
occupied:

- **5 → `ccomp`** — an indirect question or content clause read as the complement of a verb of
  saying, showing, recalling or enduring: `nota … **come natura lo suo corso prende**` (inferno
  11:99), `Ch'avete … sofferto … **che 'l giardin de lo 'mperio sia diserto**` (purgatorio
  6:105, with `Ch'` retagged below), `Ricorditi, lettor, **se mai … ti colse nebbia**`
  (purgatorio 17:2), `mostrommi l'alma … **qual era … artista**` (paradiso 18:51), `ciascuna
  cosa **qual ell' è** diventa` (paradiso 20:78 — the companion edge to the `qual` → `attr`
  retag of the round above).
- **1 → `csubj`** — `Quant' è **che tu venisti**` (purgatorio 8:56): the `che` clause is the
  logical subject of `è`, so `Quant'` (Layer 4's `nsubj`) is retagged `attr` in the same unit,
  the predicative it actually is.

Plus **1 supporting row**: purgatorio 6:103 `Ch'` `obj` → `mark`. The line reads "**Ch'**avete tu
e 'l tuo padre sofferto … che 'l giardin … sia diserto" — the initial `Ch'` is causal *ché*
("for"), not the object of `sofferto`; the object slot is the `che` clause. Retagging the clause
alone would have given `sofferto` both an `obj` and a `ccomp` for one slot, which is the gate the
previous round's deferrals were held on.

**29 left as they are** — Layer 4 is right, or nothing decides. They fall into recurring shapes
worth recording so they are not re-triaged: purposive `per`/`a` + infinitive (`vegno **per
menarvi**`, `Correte al monte **a spogliarvi**`, `dimandai **per darti forza**` — 10),
consecutive `sì`/`tanto` … `che` (`non sì **ch'io non discernissi**`, `tanto puote **che … l'aura
impregna**` — 8), conditional and temporal adverbials the LLM promotes to complements (`non ti
maravigliar **s'io la rincalzo**`, `dimmi, **se tu sai**, perché…`, `quanto mi piacque **quando ti
vidi**`), gerunds after a perception or inceptive verb (`udi' **cantando**`, `cominciò «Ave
Maria» **cantando**`, `vedine due venir **dando**`), and depictive adjectives (`Già **contento**
requïevi`) — the last confirmed conventional rather than anomalous by the corpus sweep, which
finds 350 `advcl` heads with an adjective POS. `supplica … tanto **che possa levarsi**`
(paradiso 33:26) was read and left with the consecutives: `tanto … che` is the same shape, and
the content-of-supplication reading is not decided by anything in the tree.

**Round B — the two multi-edge deferrals of the `mark` round (6 rows, 2 units).** Both were read
in that round and left because a single-row retag would have created a second core argument;
each is now closed with the full restructuring:

- purgatorio 8:114 `tanta cera **quant'** è mestiere` — `quant'` `mark` → `nsubj` and `mestiere`
  `nsubj` → `attr`: "as much wax **as is needful**", where `quanto` is the subject of `è` and
  `mestiere` its predicate nominal. (`è` stays attached to `tanta`; the correlative's attachment
  is not what the divergence is about.)
- purgatorio 22:15 `Giovenale, **che** la tua affezion mi fé palese` — four rows: `che` `mark` →
  `nsubj` (relative subject, antecedent Giovenale), `affezion` `nsubj` → `obj`, `palese` `obj` →
  `attr` (predicative complement), and `fé` re-attached from `ora` (13:4) to `Giovenale` (14:6),
  its actual antecedent.

`dep --check` after both rounds: **0 hard, 0 soft** — unchanged. `skel --check`: **3712 → 3702
soft** (−10; Round A −7, Round B −3). The one violation these rounds could not close is Layer 2's,
not Layer 4's: purgatorio 8:114 `quant'` still reports `argument (114, 1) for role subj heads no
NP/pronoun/predicate`, because that check reads the morphology POS, which calls the word a
conjunction. The 7 cantos' content hashes change, as expected for an artifact correction.

## The `obl` × `nominative` impossible pairings, from the `case` annex (2026-07-31)

The first slice of [`../case/CORRECTIONS.md`](../case/CORRECTIONS.md)'s step 4 — the hand-verified Layer-4
round the pronoun case annex was built to feed. Input: the **49** positions where `case` reads a
pronoun `nominative` and Layer 4 attaches it `obl`, reported separately by `case.py --stats`
because a pronoun attached as an oblique cannot bear the subject case. Every one was opened
against its terzina; nothing was applied from the aggregate.

**10 positions, 11 rows.** `dep --check` stays **0 hard, 0 soft**; `pytest` stays 138.

| position | word | change | why |
|---|---|---|---|
| inferno 1:80.1 | `che` | `obl` → `nsubj` | *quel Virgilio … **che** spandi*: `spandi` has only `fiume`:`obj`, no subject |
| inferno 14:80.1 | `che` | `obl` → `obj` | *ruscello **che** parton … le peccatrici*: `peccatrici` is the subject; `che` (= the stream) is what is divided |
| inferno 16:94.4 | `c'` | `obl` → `nsubj` | *quel fiume **c'**ha proprio cammino*: `ha` has no subject |
| inferno 20:14.5 | `li` | `obl` → `iobj` | *venir **li** convenia* — the **same canto**'s 20:43 *ribatter **li** convenne* is `nsubj`+`iobj`; corpus-wide `li`/`gli` with the *convenire* class is `iobj` 6 / `obl` 2 |
| inferno 27:52.2 | `quella` | `obl` → `nsubj` | *E **quella** … tra tirannia si vive*: `vive` has `si`:`expl` and `tirannia`:`obl`, no subject |
| purgatorio 4:37.2 | `elli` | `obl` → `nsubj` | *Ed **elli** a me:* — see below |
| purgatorio 4:61.2 | `elli` | `obl` → `nsubj` | *Ond' **elli** a me:* — same frame |
| purgatorio 25:8.1 | `uno` | `obl` → `nsubj` | ***uno** innanzi altro* — purgatorio 26:1 has the identical phrase as `uno`:`nsubj` + `altro`:`obl`, with the same Layer-2 POS on both tokens |
| paradiso 3:42.2 | `ella` | `obl` → `nsubj` | *Ond' **ella**, pronta …:* — same elided-speech-verb frame |
| purgatorio 5:14.5 | `che` | `obl` → `nsubj` | *torre ferma, **che** non crolla già mai la cima* — see below |
| purgatorio 5:15.4 | `cima` | `nsubj` → `obj` | … so the top is what is shaken, not what shakes |

**The elided speech verb (4 of the 11).** *Ed elli a me: «…»* — "And he [said] to me" — has no
overt verb, so Layer 4 attaches its subject to a verb inside the quotation. The corpus does this
**40+ times** and reads the pronoun `nsubj` (or `root`, once `dislocated`) every single time;
`obl` occurs only at purgatorio 4:37, 4:61 and paradiso 3:42, all three of which are in this
list. Two `nsubj` children on the quoted verb is the shape the convention already produces
(inferno 6:49, purgatorio 2:94), so the retag introduces nothing new. This is
`dep/CORRECTIONS.md`'s own rule applied literally: **pick the deprel the corpus uses for that
word.**

**`crollare` is transitive here (purgatorio 5:14–15).** Layer 5's independent skeleton reads
`cima` as the subject, i.e. "whose top never shakes". Every non-reflexive use of the verb in the
corpus is transitive with a thing or body part as object — *crollando 'l capo* (inferno 22:107),
*crollò la fronte* (purgatorio 27:43), *crollonne* (purgatorio 32:27) — the only intransitive is
the reflexive *crollarsi* (inferno 26:86). So the tower shakes its top, and the two rows move
together because retagging `che` alone would give `crolla` two subjects.

### One edit was made and reverted — purgatorio 23:126

*voi **che** 'l mondo fece **torti*** was read as "you **whom the world made crooked**", giving
`che` `obl` → `obj` and `torti` `obj` → `xcomp` (predicative complement, since one predicate
takes at most one `obj`). **Reverted.** Layer 2 tags `torti` **`noun`**, lemma `torto` — the
"wrong, injury" noun it uses at inferno 19:36, inferno 27:114 and paradiso 18:6 — and it tags the
predicative-adjective use differently where that is what the line has (*render **torti** li
diritti volti*, paradiso 13:129, `adjective`). The reading may be the better one, but it requires
Layer 2 to be wrong, which makes it a `morph/` question and not a Layer-4 edit. It is recorded
with the other Layer-2-blocked positions in [`../case/CORRECTIONS.md`](../case/CORRECTIONS.md).

The same criterion excluded purgatorio 31:25 *quai fossi attraversati* before any edit was made:
the second half-line's *quai catene* is `det`+`obj`, the first should be parallel, but Layer 2
tags `fossi` `verb` (the auxiliary, not the noun "ditches"), so Layer 4's `aux` follows Layer 2
rather than misreading the line.

**Effect on Layer 5: 3550 → 3555 soft, i.e. it went up.** That is the round working, not
failing; the reason is in [`../skel/CORRECTIONS.md`](../skel/CORRECTIONS.md)'s entry of the same
date and it changes how the remaining slices should be selected.

## The `skel`-flagged contradictions, from the `case` annex (2026-07-31)

Step 4's **slice 2**, and the first round selected by the criterion slice 1 corrected: rank the
`case` × `dep` contradictions not by whether they contradict, but by **whether `skel` already
diverges from `dep` at that position**. Of the 462 contradictions, **138** are positions Layer 5
also flags, and **102** of those are ones where `skel`'s own *given* role sides with what `case`
says — the 2-1 configuration. That 102 is the population the annex's ≈90–100 estimate always
described. Every one was opened against its terzina; nothing was applied from the aggregate.

**81 positions, 92 rows** (11 rows are supporting edits on a position's partner token).
`dep --check` stays **0 hard, 0 soft**; `pytest` stays 138. **Layer 5: 3555 → 3469 soft, −86.**

### 40 rows — the clitic dative under a verb that cannot take an object

`dep`=`obj`, `case`=`dative`, `skel`=`obl:a`: the accusative-vs-dative class the annex exists to
adjudicate, at 46 candidates. The corpus's own convention decides the target deprel — a bare
clitic (no `case` child) under the verbs involved is `iobj` **181** times against `obj` **42**,
and that 42 is largely this same mistag class plus the genuine accusatives (*dirlo*, *darla*).

Retagged `obj` → `iobj`: inferno 2:17.2, 6:59.1, 7:4.5, 7:59.3, 19:97.2, 21:26.5, 23:110.9,
28:51.8, 29:32.3, 30:121.8, 34:102.7; paradiso 3:48.2, 5:136.5, 5:138.5, 8:137.7, 11:62.4,
14:87.2, 14:95.1, 15:133.2, 21:69.5, 26:95.2, 30:89.6, 33:33.6; purgatorio 7:47.2, 9:41.1,
10:72.6, 12:9.1, 13:138.8, 15:26.6, 15:94.2, 16:34.5, 19:145.6, 21:131.6, 27:42.6, 27:46.6,
29:56.6, 30:32.2, 32:150.1, 33:20.1. The head is intransitive or impersonal in almost all of them
(*mi pesa*, *ti noccia*, *li convien*, *mi favella*, *mi parve*, *m'apparve*, *mi lece*), so `obj`
was structurally impossible, not merely a worse reading.

Two rows are one edit: **paradiso 3:48** *non **mi ti** celerà* had `mi`:`obj` + `ti`:`iobj`,
exactly inverted. **Purgatorio 23:112** *non **mi ti** celi* — the same verb, the same clitic
pair, the same order — is already `mi`:`iobj` + `ti`:`obj` in the corpus, so the convention
decided it rather than the reading.

**Inferno 2:17.2** *cortese **i** fu* is the one non-verbal head: a bare clitic under a true
adjective predicate is `iobj` **36** times in the corpus, and the 19 `obj` cases under an
adjective head are all past participles used verbally (*udito*, *soluto*, *sciolta*).

### 19 rows — the relative pronoun that is the subject of its clause

`dep`=`obj`, `case`=`nominative`, `skel`=`subj`, at 18 candidates. Seven are **swaps**, where the
relative and the noun tagged `nsubj` hold each other's roles, so the two rows move together:
paradiso 1:105 (`che`↔`universo`), 2:101 (`che`↔`specchi`), 3:124 (`che`↔`lei`), 21:71
(`che`↔`mondo`), 33:4 (`che`↔`natura` — decisive, since *nobilitasti* is 2sg and `natura` cannot
be its subject); purgatorio 12:134-135 (`che`↔`quel da le chiavi`), 25:132 (`che`↔`tòsco`).
Four have no competing subject on the predicate and move alone: paradiso 3:39.1, purgatorio
29:6.1, 29:6.4, 31:90.2.

**Purgatorio 10:90.3** *L'altrui bene a te **che** fia* went `obj` → **`attr`**, not `nsubj`:
`che` is the interrogative predicate of a copula, and the corpus writes that `attr` (26 instances
— *Qual è*, *chi son*, *chi siete*) against a residual `obj` (17). It is the one edit in the round
that sides with neither `case` nor `skel`; `obj` under a copula was wrong on any reading.

### 22 rows — the object read as a subject

`dep`=`nsubj`, `case`=`accusative`, `skel`=`obj`, at 19 candidates edited. Mostly relative objects
whose clause has a pro-drop or postposed subject (inferno 15:88.2, 29:57.4; paradiso 1:73.8,
3:72.3, 20:138.3, 21:95.6; purgatorio 5:49.3, 7:92.5, 14:35.3, 21:129.3), plus inferno 17:104.2
*e **quella** tesa … mosse* and paradiso 6:82 (`che`↔`segno`, another swap).

Five rows re-attach as well as retag, because the retag alone would have given one predicate two
objects or left a dependent on an auxiliary:

| position | change | why |
|---|---|---|
| inferno 34:125.3 | `lui` `nsubj` → `obj`, head `lasciò` → `fuggir` | *per **fuggir lui** lasciò qui loco vòto*: `lasciò` already has `loco`:`obj` |
| purgatorio 4:72.1/.6 | `che` → `obj`; `Fetòn` re-headed from the aux `seppe` to `carreggiar` | *la strada **che** mal non seppe carreggiar **Fetòn*** |
| purgatorio 5:62.1 | `che` `nsubj` → `obj`, head `face` → `cercar` | *quella pace **che** … cercar mi si face* |
| purgatorio 5:63.6 | `mi` `obj` → `iobj`, head `cercar` → `face` | the causee of *far cercare*: transitive infinitive → dative causee |

That last pair is worth keeping together with **paradiso 6:82.8**, where *'l segno che parlar
**mi** face* went `iobj` → `obj`: same causative, and the causee takes the accusative because
*parlare* is intransitive. The corpus now distinguishes the two by the infinitive's valency
rather than by the clitic's form.

Supporting rows on positions `case` did not itself flag: inferno 19:84.7 (`me`, coordinated with
`lui`), inferno 31:116.3 (`Scipïon` → `obj`; `che` was already the correct subject and stays),
paradiso 6:82.5, purgatorio 4:72.6.

### 11 rows — the mirror direction

`dep`=`iobj`, `case`=`accusative`, `skel`=`obj`: the *mi bagna* / *mi tormenta* population
[`../skel/PLAN.md`](../skel/PLAN.md) section 1 parked. Nine of ten were plain transitives and went
`iobj` → `obj`: inferno 3:132.6, 10:78.2; paradiso 3:62.3, 6:82.8, 12:96.3, 26:11.2; purgatorio
17:2.1, 26:50.4, 29:39.2. One supporting row: paradiso 26:11.1, where `regïon` carried a `per`
`case` child yet was tagged `obj`, so it went `obj` → `obl`.

**Paradiso 10:22.2** *Or **ti** riman, lettor* went `nsubj` → **`expl`**: pronominal *rimanersi*,
which the corpus writes `expl` at inferno 8:38 and purgatorio 24:91. `nsubj` was impossible (the
subject is the addressed *lettor*), and this is a second edit siding with neither `case` (dative)
nor `skel` (`obl:a`).

### 21 tier-A candidates were left alone, and why

Not every 2-1 tie goes against `dep`. **`case` is the dissenting read in eleven of them**, and
saying so is the round's own control:

- **inferno 17:77.6** *m'avea 'mmonito* — the accusative that [`../case/README.md`](../case/README.md)
  used as its worked example of an accusative. `case` reads it dative; `dep` is right.
- **inferno 19:44.5** *sì mi giunse al rotto*, **26:110.5** *mi lasciai Sibilia* (the corpus tags
  every *lasciare* clitic `obj`, 12 of them), **30:126.8** *omor mi rinfarcia*,
  **purgatorio 13:108.5** *che sé ne presti*, **paradiso 15:96.2** *tu **li** raccorci* (dative,
  with `fatica` already the object) — `dep` is right in each.
- **paradiso 19:59.3** *la vista che riceve il vostro mondo*, **21:12.3** *fronda che trono
  scoscende*, **purgatorio 7:99.1** *l'acqua che Molta … porta*, **23:92.2** *ambo le luci mi
  dipinse il quale e il quanto* — the postposed noun really is the subject and `che` really is the
  object; `case` inverted them.

The rest are structural rather than wrong: **free relatives** (inferno 11:51.2 *e chi … favella*,
paradiso 32:56.1 *quantunque vedi*, 33:17.2 *a chi domanda*), where the pronoun is simultaneously
an argument of the matrix and the subject of its own clause and `dep` has picked one coherently;
the **accusative-and-infinitive** (inferno 22:32.1 *uno aspettar*, paradiso 30:57.1 *me
sormontar*), where `case` is morphologically right but the corpus writes the notional subject of a
perception verb's infinitive `nsubj` **141** times against `obj` 100; the **standard of
comparison** (purgatorio 28:75.2, paradiso 13:131.5), which slice 1 already settled and which is
not reopened; **inferno 20:14.5** *venir **li** convenia*, `iobj` by slice 1's own edit and correct;
and **inferno 8:4.5** *che i vedemmo porre*, where `nsubj` is certainly wrong but `che` already
holds `obj` and Layer 2's `pronoun` tag on `i` (for *ivi*) is what blocks a clean target — a
`morph/` item, recorded in [`../case/CORRECTIONS.md`](../case/CORRECTIONS.md).

**Layer 2 blocked nothing this round**, unlike slice 1. One Layer-2 observation was collected in
passing: purgatorio 31:90.1 *salsi* carries the lemma `salutare` where the line needs *sapere*.

## The contradictions `skel` does not flag, from the `case` annex (2026-08-01)

Step 4's **slice 3**, and the honest completion of the round: the **325** `case` × `dep`
contradictions that Layer 5 does *not* flag — everything outside slice 2's tiers A/B/C. This is
slice 1's configuration by construction: `dep` and `skel` agree and only `case` dissents, so a
correct fix here breaks an agreement and **raises** Layer 5's soft count. It was run anyway,
because the deliverable is a more correct Layer 4 and the alternative was leaving 325 measured
positions with no verdict.

**124 positions, 167 rows.** `dep --check` stays **0 hard, 0 soft**; `morph --check` 0/0;
`pytest` stays 138. **Layer 5: 3469 → 3634 soft, +165** — see
[`../skel/CORRECTIONS.md`](../skel/CORRECTIONS.md).

Every position was opened against its terzina one at a time. The partition and the per-position
readings are in [`../case/CORRECTIONS.md`](../case/CORRECTIONS.md)'s *Step 4, slice 3*.

### 34 + 31 rows — the relative pronoun and the postposed noun, inverted

The largest family and the round's clearest finding. `dep`=`obj`, `case`=`nominative` on a
relative pronoun whose clause has a postverbal noun: the question every time is whether that noun
is the postposed **subject** (`dep` right) or the semantic **patient** (`case` right). It was the
patient 34 times, and in 31 of those the two rows hold each other's roles and move together:

inferno 1:27 (`che`↔`persona` — *lo passo che non lasciò già mai persona viva*), 2:97
(`Questa`↔`Lucia`), 4:24 (`che`↔`abisso`), 7:69 (`che`↔`ben`), 9:114 (`ch'`↔`Italia`), 12:4-5
(`che`↔`Adice`), 30:123 (`che`↔`ventre`), 31:75 (`che`↔`petto`), 33:108 (`che`↔`fiato`), 33:113
(`che`↔`cor`), 34:117 (`che`↔`faccia`); purgatorio 3:11 (`che`↔`onestade`), 4:48 (`che`↔`poggio`),
6:39 (`chi`↔`che`), 8:1 (`che`↔`disio`), 8:124 (`che`↔`casa`), 9:142-143 (`ciò`↔`imagine`),
16:104 (`che`↔`mondo`), 20:44 (`che`↔`terra`), 22:112 (`che`↔`Langia`), 24:56 (`che`↔`Notaro`),
24:122-123 (`che`↔`Tesëo`), 33:125 (`che`↔`memoria`); paradiso 6:77-78 (`che`↔`morte`), 9:84
(`che`↔`terra`), 18:120 (`che`↔`raggio`), 19:118-120 (`quel`↔`che`), 21:25 (`che`↔`vocabol`),
24:100 (`che`↔`ver`), 33:96 (`che`↔`Nettuno`).

Three move alone because the clause has no competing subject: **purgatorio 3:120.4** *a quei che
volontier perdona* (intransitive `perdonare`), **inferno 15:99.5** *Bene ascolta chi la nota*
(the free relative is `ascolta`'s subject, not its object), **paradiso 21:135.3** *oh pazïenza
che tanto sostieni* (`sostieni` is 2sg and can only agree with `pazïenza`).

Two re-attach as well as retag:

| position | change | why |
|---|---|---|
| purgatorio 12:65.7 | `ch'` `obj` → `nsubj`, head `mirar` → `farieno` | *l'ombre e ' tratti ch'ivi mirar **farieno** uno ingegno sottile*: `farieno` is 3pl and only the plural antecedent can be its subject |
| paradiso 11:41.4 | `un` `nsubj` → `obj`, head `dice` → `pregiando` | *d'amendue si dice **l'un pregiando*** — the one praised is the gerund's object |

**Paradiso 33:96** takes its partner to `iobj`, not `obj`: *la 'mpresa che fé **Nettuno** ammirar
l'ombra d'Argo* is a causative `fare` whose infinitive carries its own object, which the corpus
writes with a dative causee (see below).

### 40 rows — the clitic dative, again, where `skel` sides with `dep`

`dep`=`obj`, `case`=`dative`, and this time Layer 5 agrees with `dep`. It is the same class slice
2 spent 40 rows on, and the same convention decided it: the head is intransitive, impersonal or
already carries an object, so `obj` was structurally impossible.

Retagged `obj` → `iobj`: inferno 1:90.3, 2:51.7, 2:141.2, 3:110.1, 5:96.7, 6:58.2, 7:6.2,
8:111.7, 10:113.2, 11:93.7, 13:122.5, 16:110.5, 17:117.9, 22:46.4, 22:114.3, 22:127.3, 23:19.2,
24:151.7, 26:12.3, 29:135.7, 29:138.2, 30:145.6, 34:19.3; purgatorio 14:5.5, 14:119.1, 16:9.1,
19:90.6, 22:68.7, 22:86.2, 23:50.2, 24:53.2, 25:5.9, 26:140.2, 28:89.7; paradiso 5:1.3, 6:114.5,
20:127.4, 26:101.1, 29:66.5, 31:77.3.

Two sub-conventions were measured before the target deprel was chosen, and both are worth keeping:

- **The causative `fare`.** With a *bare* infinitive the causee is accusative — the corpus writes
  it `obj` **38** times against `iobj` 3 — and with an infinitive that carries its own object it
  is dative, `iobj` **7** times (purgatorio 5:63, 29:24; paradiso 11:3, 12:30, 19:24, 24:18,
  26:42) against an `obj` residue that is largely this mistag class. Slice 2 opened this
  distinction at paradiso 6:82; slice 3 applies it in both directions, and it is why inferno
  9:26.3 *mi fece intrar*, purgatorio 21:116.3 *mi fa tacer* and paradiso 20:101.1 *ti fa
  maravigliar* were **left alone** while inferno 1:90.3 *mi fa tremar le vene* and purgatorio
  19:90.6 *notar mi fenno* were changed.
- **Two `obj` children under one head.** inferno 22:46 *li s'accostò*, 34:19 *d'innanzi mi si
  tolse* had the reflexive and the dative both tagged `obj`; the dative moved.

**Paradiso 9:110.1** *ten porti* went `iobj` → **`expl`**: a fused `te`+`ne` under *portarsene*,
which the corpus tags `expl` 20 times (and `obl` 14, `obj` 6) on `sen` and never `iobj`.

### 11 rows — the predicative pronoun under a copula

`obj` → **`attr`**, extending the single instance slice 2 made at purgatorio 10:90: a pronoun
predicated of a copular *essere* is `attr` **48** times in the corpus against `obj` 20, and
Layer 5's LLM reads every one of these as `attr` already. `obj` under a copula was wrong on any
reading, so these side with neither layer's case claim.

inferno 2:37.2 *E qual è quei*, 3:32.3 *che è quel ch'i' odo*, 7:60.1 *qual ella sia*, 25:37.5
*Chi siete voi*, 30:136.1 *Qual è colui*; purgatorio 12:18.4 *quel ch'elli eran pria*, 15:25.1
*Che è quel*, 26:65.1 and 26:65.5 *chi siete voi, e chi è quella turba*; paradiso 16:44.1 *chi ei
si fosser*, 25:46.3 *di' quel ch'ell' è*.

### 9 rows — the mirror direction, where `case` was right

`dep`=`iobj`, `case`=`accusative`, retagged `iobj` → `obj`: purgatorio 13:103.7 *che per salir ti
dome* (a true reflexive of a transitive verb), 20:98.7 *che ti fece verso me volger* (the bare
causative), 28:70.3 *ci facea il fiume lontani* (`lontani` agrees with `ci`; its own row went
`obj` → `xcomp`), 31:94.2 *Tratto m'avea nel fiume infin la gola* (with `gola` `obj` → `obl`),
33:55.7 *quando tu le scrivi*; paradiso 5:38.6 *'l cibo rigido c'hai preso*, 18:18.1 *mi
contentava*, 24:103.5 *chi t'assicura*, 30:49.2 *mi circunfulse luce viva* (the Vulgate's
*circumfulsit eum*).

### 8 rows — the dative read as a subject

`dep`=`nsubj`, `case`=`dative`, retagged `nsubj` → `iobj`, all of them impersonal or
dative-governing predicates where the grammatical subject is elsewhere: inferno 21:25.7 *l'uom
cui tarda*, 26:141.8 and purgatorio 1:133.6 *com' altrui piacque* (the corpus writes `piacere`'s
dative `iobj` 21 times and `obl` 12; these two were its only `nsubj` clitics), inferno 33:150.4
*cortesia fu lui esser villano*; paradiso 5:113.1 *m'era in disio*, 7:73.2 *Più l'è conforme*,
25:61.7 *non li saran forti*.

### The five edits that side with neither layer

Worth listing because they are the round's evidence that the contradiction list is an
adjudication input and not an edit list: the 11 `attr` rows above, plus

| position | change | why |
|---|---|---|
| purgatorio 17:45.4 | `quel` `obj` → `obl` | standard of comparison — the deprel slice 1 measured as the corpus's own, and the one edit that *created* an impossible pairing (39 → 40) |
| purgatorio 31:24.8 | `che` `obj` → `obl` | *a che s'aspiri*: `a` at 24.7 is already tagged `case` → 24.8, so `obj` was internally inconsistent |
| paradiso 16:146.5 | `che` `obj` → `mark` | *conveniesi … che Fiorenza fesse vittima* — the conjunction; `vittima` already holds `obj` |
| paradiso 18:119.6 | `che` `obj` → `mark` | *prego la mente … che rimiri* — the subjunctive prayer clause |
| paradiso 14:48.3 | `a` `case` → `mark`, head 48.4 → 48.5 | *a lui veder*: `a` marks the infinitive, not `lui` |

### 201 positions were left alone, and why

**`case` is the dissenting read in 171 of them** — 53% of the slice. That number is the slice's
most useful measurement and it is exactly what the selector predicts: inside the `skel`-flagged
intersection `case` was wrong 11 times in 102 (11%); outside it, 171 in 325. Recorded per
position in [`../case/CORRECTIONS.md`](../case/CORRECTIONS.md), with the two coherent shapes the
errors take.

The other 30 are structural: **19 conventions** the corpus applies consistently (free relatives,
where the pronoun is an argument of the matrix and the subject of its own clause; the
accusative-and-infinitive under a perception verb, `nsubj` 141 / `obj` 100; `si` passivante;
presentative *ecco*; `credere` + person, which the corpus writes `obj` four times and `iobj`
never), **5 fused tokens** where `case` annotates a clitic and `dep` the whole word
(inferno 2:81.7 *aprirmi*, 23:128.7 *dirci*; purgatorio 8:45.4 *vedervi*, 14:20.1 *dirvi*;
paradiso 29:92.1 *seminarla*), **3 deferrals**, **2 Latin quotations** (purgatorio 8:13.1 *Te
lucis ante*, paradiso 32:12.5 *Miserere mei* — a Latin genitive no value in the vocabulary
covers), and **1 Layer-2 block**.

The three deferrals are recorded rather than forced, because each needs a restructure the reading
does not by itself settle: **inferno 1:117.1** *ch'a la seconda morte ciascun grida* (`obj` under
an intransitive is wrong, but the fix turns `ciascun` into an appositive), **paradiso 22:55.2**
*m'ha dilatata mia fidanza* (the commentary reading needs four rows and `dep`'s parse is
internally coherent), **paradiso 11:118.3** *Pensa oramai qual fu colui* (an indirect question
attached straight to `Pensa`).

The Layer-2 block is **purgatorio 20:83.2** *poscia c'ha' il mio sangue a te sì tratto*: `c'` is
the conjunction of *poscia che* and wants `mark`, but Layer 2 tags it `pronoun`, which is what
put it in the case scope at all. Its partner row was taken anyway (`sangue` `nsubj` → `obj`).
One further Layer-2 observation: **purgatorio 11:137.2** *ch'e' sostenea* has `e'` (= *ei*) tagged
as an auxiliary.

## The Layer-2 block, unblocked — purgatorio 20:83 (2026-08-02)

**One position, two rows.** The deferral recorded just above as *the Layer-2 block* is closed:
Layer 2's step-5 round retagged `c'` in *poscia c'ha' il mio sangue a te sì tratto* from the
pronoun `ci` to the conjunction *che*, which is what the reading wanted all along. With the tag
corrected, the row it blocked was taken:

| line.tok | word | was | now |
|---|---|---|---|
| 83.1 | `poscia` | `mark` | `advmod` |
| 83.2 | `c'` | `obj` | `mark` |

Both keep their head (83.10 `tratto`). The pair follows the corpus's own dominant convention for
*poscia che* / *però che*: `advmod` + `mark`, **27** times for *poscia* against one `mark` + `mark`.
It also removes a double `obj` on `tratto` — `sangue` had already been corrected to `obj` in the
slice above, so the conjunction was the second one.

Surfaced by Layer 3's clitic reconciliation (see [`../np/CORRECTIONS.md`](../np/CORRECTIONS.md)),
which had to drop the same token's NP span for the same reason. `dep --check` stays **0 hard, 0
soft**; Layer 5 moved 3633 → 3635 because its own frozen row still holds the pronoun reading, which
is left standing as measured divergence.

## One `vi` mistag, from the `case` annex's clitic residue (2026-08-03)

**Purgatorio 11:39.6** *che secondo il disio vostro **vi** lievi* had `vi` tagged `nsubj` — a
hapax: `vi` carries `nsubj` nowhere else in the corpus, against 906 instances of `si` tagged
`expl` for the identical reflexive *levarsi* construction with a pro-dropped subject. Retagged
`nsubj` → `expl`. `dep --check` stays **0 hard, 0 soft**; `pytest` stays 142; **Layer 5: 3635 →
3634, −1**.

Surfaced while hand-verifying the 50 bare-clitic `case`×`dep` contradictions (`mi ti ci vi si li` +
elisions) left over from the annex's Step 4/5 rounds; the other 49 turned out to be `case`-side
errors, corrected in [`../case/CORRECTIONS.md`](../case/CORRECTIONS.md)'s *Step 6* rather than
here — two other plausible `dep` fixes from the same pass (the `gravare` population at
purgatorio 31:58, inferno 6:86, purgatorio 18:6; and the *mi lasciai Sibilia* / *m'avea lasciata
Setta* reflexive reading at inferno 26:110-111) were tried and **reverted** after re-running
`skel --check` showed them moving the soft count against the change, or not moving it at all.

## Nine mistags surfaced while correcting `case`'s word-order errors (2026-08-03)

[`../case/CORRECTIONS.md`](../case/CORRECTIONS.md)'s *Step 7* opened ~180 named `case`-side
errors from the slice-2/3 residue against their terzine and corrected `case/*.tsv`. Reading each
position individually (rather than trusting the stored parse) turned up nine `dep` rows that were
themselves wrong, in two small families already established elsewhere in this file:

**Predicative pronoun under a copula, `obj` → `attr`** — the same convention an earlier round
spent 11 rows on (*the predicative pronoun under a copula* section above), missed at four more
positions, all "tell me who you were/are" indirect questions with `chi` predicated of *essere*:
inferno 13:52.3 *chi tu fosti*, 16:32.3 *chi tu se'*, 32:55.4 *chi son cotesti due*; paradiso
21:105.4 *chi fue*.

**A subject plainly mistagged object, `obj` → `nsubj`** — five positions where the flagged token
could not be its head verb's object, either because it is unambiguously a subject pronoun (`I'` =
apocopated *io*) or because the head verb's object slot was already filled by a separate, explicit
token: inferno 9:10.1 *I' vidi ben sì...*, 22:31.1 *I' vidi, e anco il cor...*, 12:23.1 *c'ha
ricevuto già 'l colpo mortale* (*'l colpo mortale* is already the object), purgatorio 26:105.4
*l'affermar che fa credere altrui* (*credere* already has its own subject-complement, and the
head being `fa` leaves no second object slot), paradiso 9:106.7 *l'arte ch'addorna* (*cotanto
affetto* two lines down is already `addorna`'s object).

`dep --check` stays **0 hard, 0 soft**; `pytest` stays 142; **Layer 5: 3634 → 3631, −3**. `case`
was already correct (`nominative`) at all nine and was left untouched.

## Three retags surfaced correcting `case`'s dative/accusative confusions (2026-08-03)

[`../case/CORRECTIONS.md`](../case/CORRECTIONS.md)'s *Step 8* worked through the `dative`-vs-`obj`
and `accusative`-vs-`iobj` shapes, applying a transitivity test at each position (does the head
verb already have an explicit object filled?). Two positions came out the other way — `case` was
already right and the deprel was wrong:

- **`obj` → `iobj`** (×2): inferno 10:114.6 *l'error che m'avete soluto* (*sciogliere un dubbio a
  qualcuno* — the doubt, `che`, is `soluto`'s real direct object even though tagged `obl` for its
  relative-clause fronting, leaving `m'` as the dative beneficiary, not a second direct object),
  paradiso 4:32.6 *questi spirti che... t'appariro* (*apparire*, "to appear", is inherently
  intransitive/unaccusative in Italian — it has no direct-object valency at all, so a clitic next
  to it can only be the dative "to whom it appears").

One position came out the reverse direction, surfaced by the mirrored `accusative`-vs-`iobj` test:

- **`iobj` → `obj`**: inferno 26:9.8 *Prato... t'agogna* (*agognare*, "to long for", is a plain
  transitive verb taking a direct object — no dative sense — so the `iobj` tag was simply wrong;
  `case`'s `accusative` had it right).

`dep --check` stays **0 hard, 0 soft**; `pytest` stays 142; **Layer 5: 3631 → 3633, +2** (two of
the three retags moved a divergence in against Layer 5's own frozen reading; the third moved one
out — net effect recorded as measured, not chased further this round, per the same standing that
governs every other retag in this file).

## Ten retags from Layer 5's rule-U round (2026-08-03)

[`../skel/CORRECTIONS.md`](../skel/CORRECTIONS.md)'s *Phase 5r* wired the `case` annex into Layer
5's divergence checker and, as the rule's by-product, produced **17 positions where `case` sides
with the LLM against `dep`** — the same `dep`-mistag shape Steps 7 and 8 of the case annex worked.
Each was read against its terzina. Ten rows were genuinely wrong, in four families already
established in this file:

**A locative/partitive clitic tagged `obj`** (4) — `obj` → `obl`, the majority convention for this
class in the corpus (`ne`/`n'` locative-partitive: 136 `obl` against 44 `obj`): inferno 4:53.2
*quando **ci** vidi venire un possente* (*ci* = "here", and the perception's content is *un
possente* under the `xcomp`), 9:106.2 *Dentro **li** 'ntrammo* (*intrare* is intransitive; *li* is
the complement of *Dentro*), 17:116.7 *non me **n'**accorgo* (*accorgersi **di** ciò*), purgatorio
3:139.4 *per ognun tempo **ch'**elli è stato* (a temporal relative under *essere*, which has no
object valency at all).

**A causative `fare` misassembled** (4) — the corpus's own convention for causative *fare* +
infinitive is agent `nsubj`, causee `obj`, infinitive `xcomp` (inferno 1:102 *che **la** farà
morir*, 2:72 *che **mi** fa parlare*). Two positions did not follow it: inferno 10:136 *che 'nfin
là sù facea spiacer suo lezzo* — `che` `obl` → `nsubj`, `spiacer` `obj` → `xcomp`, `lezzo` `nsubj`
→ `obj` (the valley makes its stench offensive, so the relative is the agent and the stench the
causee); purgatorio 14:13.8 *ché tu **ne** fai tanto maravigliar* — `ne` `obl` → `obj`, the causee
of *far maravigliare*, here the Tuscan *ne* = *ci* ("us"), not the partitive.

**A clitic dative tagged `obj`** (1) — purgatorio 14:12.6 *ne ditta / onde vieni e chi se'*:
*dittare* already has its object in the `ccomp` content clause, so the clitic is the dative
addressee (Step 8's transitivity test, applied in `../case/CORRECTIONS.md`). `obj` → `iobj`.

**A subject plainly tagged something else** (1) — paradiso 23:68.1 *non è pareggio da picciola
barca **quel** che fendendo va l'ardita prora*: `quel` is the subject of *è*, and `obl` with no
preposition in the tree cannot be right. `obl` → `nsubj`. The predicate nominal *pareggio* keeps
its `nsubj` per the copular convention (`skel`'s rule M), leaving two `nsubj` on one head — 152
predicates in the corpus already have that shape, so it is not a new one.

The other eight of the 17 were left alone with stated structural reasons — five of them because a
copular predicate nominal is nominative just as a subject is, so the annex adjudicates nothing
there; see `../skel/CORRECTIONS.md`'s *Phase 5r* for all four families.

`dep --check` stays **0 hard, 0 soft**; `pytest` 149 passed; **Layer 5: 3473 → 3465, −8** (with
the four `case` corrections recorded in [`../case/CORRECTIONS.md`](../case/CORRECTIONS.md)).

## The "at most one `obj` per predicate" rule, and the 203 predicates it flagged (2026-08-03)

[`../skel/PLAN.md`](../skel/PLAN.md) section 1 had recorded, without acting on it, that
corpus-wide a number of predicates carry two or more `obj` children — a shape UD does not allow.
This round opened it: a new **soft check** in `validate_unit` reports any predicate with more than
one `obj` child, and every position it flagged was read against its terzina and corrected.

**Why a mis-parse and not a convention difference.** The corpus already uses the UD shape
everywhere else — measured before opening the round, `conj` attaches to a first conjunct tagged
`obj` in 304 places, and `cc` attaches to its conjunct in 3471. A flattened `V → obj, obj` pair is
the model failing to build the coordination, not a second house style. First-conjunct attachment
(UD's own rule) is what the corrections use; the corpus's existing 740 *chained* `conj → conj`
coordinations are left alone, since neither the rule nor anything else checks that choice.

**Population: 203 predicates** (188 with two `obj`, 15 with three or more), in three shapes:

| shape | count | what it was |
|---|---|---|
| flattened coordination | 68 | a coordinator stands between the two `obj` |
| object complement etc. | 70 | no coordinator; dominated by predicative complements |
| clitic | 65 | one of the two `obj` is a clitic pronoun |

**316 row edits across the 203 predicates.** The recurring families:

- **Later conjuncts re-attached (88 `conj`, 11 `cc` head fixes)** — *Bestemmiavano Dio e lor
  parenti, l'umana spezie e 'l loco e 'l tempo e 'l seme* (inferno 3:103) had six `obj` on one
  verb; five become `conj` on the first. Four `e`/`ed` tokens tagged `conj` become `cc`.
- **Object complements → `attr` (63)** — *mi chiamaste Ciacco*, *li chiama orbi*, *fa la valle
  inferna nera*, *fé i Romani reverendi*. UD has no relation for a secondary predicate over an
  object; `attr` is the corpus's own frozen label for a predicative nominal/adjective, and Layer 5
  canonicalizes it to `xcomp` for role comparison anyway (`_ROLE_CANON`). **`xcomp` is wrong here**:
  it is a `CLAUSE_HEAD_DEPRELS` member, so an adjective tagged `xcomp` makes `derive_unit` invent a
  predicate tuple for it — measured at +62 `missing_tuple` before the labels were corrected to
  `attr`. Only three genuinely *verbal* complements keep `xcomp`.
- **Reflexive/middle clitics → `expl` (22)** — chiefly `farsi` = "become" (*tal mi fec' io*,
  *cotai si fecer quelle facce*, *si fa vino*), where the clitic is not an argument and the
  predicative is the `attr`.
- **Clitic datives → `iobj` (9)** and **partitive/locative `ne`/`vi` → `obl` (27)** — the same two
  families this file's *Double-`obj` clitic datives* (2026-07-28) and the `case`-annex rounds
  worked; the new rule finds the residue they did not reach.
- **Gapping, given UD's treatment (14 `orphan`)** — *giri Fortuna la sua rota ..., e 'l villan la
  sua marra*; *La sua chiarezza séguita l'ardore; l'ardor la visïone*; *fa l'arco il Sole e Delia
  il cinto*. The first remnant of the elided clause is promoted to `conj` of the full clause's
  verb and the other remnants attach to it with `orphan`.
- **A subject or oblique read as an object (18 `nsubj`, and the `obl` rows above)** — *Ora cen
  porta l'un de' duri margini*, *poscia la luce ... Ruppe il silenzio*, *quello amor si spoglia*.
- **Indirect questions and quoted clauses → `ccomp` (10)** — *pensa chi era*, *sappia chi fosti*,
  *«Usciteci», gridò*.
- **Four compound-tense mis-assemblies** where the finite `avere` had been made the head and the
  participle its `obj`: inferno 19:27 *che spezzate averien ritorte*, purgatorio 21:21 *chi v'ha
  ... tanto scorte*, paradiso 30:140 *simili fatti v'ha al fantolino*, plus paradiso 22:21 *se
  com' io dico l'aspetto redui*, where a finite verb had been tagged `amod`. In each the
  participle becomes the clause head and `avere` its `aux`.
- Singletons: two left dislocations (`dislocated`), one vocative that had been tagged `obj`
  (inferno 19:46 *«O qual che se'…»*), one Latin quotation (*Te **Deum** laudamus* → `appos`),
  one `tutto quanto` (`fixed`), and one misassembled NP (paradiso 13:129 *li diritti volti*).

**Nothing was left alone.** Every one of the 203 had a decidable reading.

`dep --check` reports **0 hard, 0 soft** with the new rule in place (203 → 0); `pytest` 154 passed
(three new tests for the rule). **Eleven `case` rows were corrected alongside** — the retags moved
ten positions into contradiction with the annex and every one of the ten was the annex's error, not
the retag's; plus inferno 29:125.6 *Tra'**mene** Stricca*, `accusative+ablative` →
`dative+ablative`. See [`../case/CORRECTIONS.md`](../case/CORRECTIONS.md); `case --stats`
contradictions 32 → **31**, impossible pairings **26** unchanged.

**Layer 5's soft count rose, 3465 → 3509 (+44)**, and that is the honest reading of the round, not
a regression: `derive_unit` reads Layer 4, so where the LLM had agreed with a *wrong* `obj` the two
now genuinely disagree. By kind: `missing_arg` 1206 → 1156 (−50, arguments the derivation now
supplies), against `extra_arg` 1649 → 1709 (+60, mostly the 22 clitics that are no longer arguments
at all), `role_mismatch` 347 → 362 (+15) and `missing_tuple` 26 → 45 (+19, the gapping promotions
of the paragraph above, which `derive_unit` deliberately treats as elided predicates);
`extra_tuple` 145 and `argument` 92 unchanged. See
[`../skel/CORRECTIONS.md`](../skel/CORRECTIONS.md)'s entry of the same date.

## The subject/head agreement rule, and the 173 positions it flagged (2026-08-07)

A new Layer-2-aware soft check (`_subject_agreement_violations` in `dante_corpus/dep.py`): an
`nsubj`/`nsubj:pass` whose Layer-2 **person or number contradicts its finite head's**. Italian
agreement is obligatory, so the two frozen layers cannot both be right at such a position — either
the attachment is a mis-parse or one of the two Layer-2 rows carries the wrong feature. Which side
is wrong is not mechanically decidable, so the rule reports the position and never repairs it.

It opened at **173** positions (106 person, 67 number) and every one was read against its terzina.
**155 were corrected** (77 Layer-2 rows, 424 Layer-4 rows across 66 cantos, 2 Layer-3 spans and 1
`case` row); **18 were verified and left alone**, listed at the end.

The rule came out of a Layer-5 audit: of `skel`'s 133 `extra_arg subj (0,0)` violations — the LLM
writing a pro-drop ∅ subject where the derivation had found an overt one — 43 had a derived subject
that could not agree with its own predicate, which made the *generalized* test worth running over
all 6 000 `nsubj` edges rather than only those 133.

### What was corrected, by family

- **The elided verb of speech (99 frames, ~300 rows).** "Ed elli a me: «…»" is a clause whose verb
  of speech is elided; UD promotes a dependent to head it, and the corpus already did that in 42
  places. In 99 others the frame's subject had instead been attached as `nsubj` **inside the
  quotation**, where it can be neither the quoted verb's subject nor its dependent. Normalized
  mechanically and corpus-wide, not only where agreement exposed it: the subject takes over the
  quoted head's external attachment, the quoted head becomes its `ccomp`, and the frame's own
  dependents (`cc`, `a me`, …) re-point to the subject. Three frames matching the same surface
  shape were **excluded after reading**, because their speech verb is real and merely displaced:
  purgatorio 3:22 ("a dir mi *cominciò*", after the quote), purgatorio 33:121 ("E qui *rispuose*
  … la bella donna", before it) and paradiso 31:94 (*«…», disse, «…»*, parenthetical).
- **An object read as a subject (24 positions).** "che l'aura etterna *facevan* tremare" (the sighs
  are the subject), "fanno *Cocito*", "mi lasciai *Sibilia*", "e *quelle* svolazzava", "Fa che le
  *ginocchia* cali", "quando i primi *raggi* vibra". Retagged `obj`; where the retag then left two
  objects on one predicate, the other object was the mis-parse and was corrected too (subjects at
  purgatorio 8:80/22:25 and paradiso 2:67, an `xcomp` causative at paradiso 16:2, a reflexive
  clitic `expl` at inferno 26:110).
- **Other functions read as a subject (10).** A vocative (inferno 20:34 *Anfïarao*), a clausal
  subject (`csubj`, inferno 21:59), two predicate nominals (`attr`: *son Vanni Fucci*, *ben son
  Beatrice*), a depictive (`attr`, purgatorio 11:103), an oblique (purgatorio 15:55), a reflexive
  clitic (`expl`, purgatorio 17:73), the adverbs `i` = *ivi* and `du'` = *dove*, and a raised
  subject (paradiso 14:73, *parvemi … sussistenze cominciare a vedere*).
- **Gapping (2).** "si mosse, e io [mi mossi] di rietro" and "…intende, e io [intendo] de l'altra"
  got UD's promoted-conjunct + `orphan` treatment, the shape the multiple-`obj` round already
  established.
- **Misassembled phrases (6).** inferno 28:52 (*Più fuor di cento che…*: `fuor` = *furono*, as it
  is already tagged at inferno 7:40, so the relative clause hangs off `cento`), purgatorio 8:124
  (subject and objects inverted), purgatorio 13:32 (a quoted cry parsed as the head of its own
  subject NP), paradiso 4:29 (`appos` → `conj` in the list *colui, Moïsè, Samuel, e quel
  Giovanni*), paradiso 5:119 and paradiso 15:55 (both a Layer-2 mistag, below, plus the clause
  structure that followed from it).

The Layer-2 half of the round — archaic 1sg forms tagged 3rd person, `altri`/`quei` tagged plural,
apocopated 3pl forms tagged singular, and six words read as the wrong part of speech — is recorded
in [`../morph/CORRECTIONS.md`](../morph/CORRECTIONS.md). Two Layer-3 spans and one `case` row
followed from the POS changes; see [`../np/CORRECTIONS.md`](../np/CORRECTIONS.md) and
[`../case/CORRECTIONS.md`](../case/CORRECTIONS.md).

### Three exclusions added to the rule while working the list

Each is a case where the two rows genuinely need not match, and each has corpus-wide precedent
rather than being fitted to a single position:

- **The head must be a verb.** The corpus makes the *predicate* the head of a copular clause, so a
  subject can hang off a noun, an adjective, or a fused `vosco` = *con voi* (purgatorio 11:60) —
  none of which conjugates.
- **A fused token whose verb part is non-finite** (`pos` containing `+`, no tense, no mood) carries
  the **enclitic's** person: `aprirmi` = *aprire* + *mi* is tagged 1sg for the clitic. Measured
  corpus-wide: 70 such tokens, consistently annotated that way. A *finite* fused token (`parvemi`,
  `Presemi`) carries the verb's own person and stays in scope.
- **A 1st/2nd person plural head**, where a singular or 3rd-person nominal regularly names one
  member of the group the verb agrees with: comitative "e io con lui / **volgemmo** i passi",
  inclusive "e amendue / **mostravam**", "uno innanzi altro **andavamo**". Only the plural allows
  this, so a singular head stays in scope.

### The 18 verified and left alone

All read against their terzine; each disagreement is a property of the text, not of the parse:

- **Constructio ad sensum — a collective singular with a plural verb** (5): inferno 3:115 *il mal
  seme d'Adamo gittansi*, purgatorio 26:76 *La gente … si parton*, purgatorio 32:62 *quella gente
  allor cantaro*, paradiso 14:62 *l'uno e l'altro coro … parver*, paradiso 13:98 *necesse con
  contingente … fenno* (a comitative pair taking a plural verb).
- **A plural or measure subject with a singular verb** (5): inferno 6:86 *diverse colpe … grava*,
  inferno 19:19 *non è molt' anni* (impersonal time idiom), inferno 21:114 *mille dugento con
  sessanta sei / anni compié*, inferno 31:69 *non si convenia più dolci salmi*, purgatorio 14:18
  *cento miglia di corso nol sazia*.
- **Distributive `ciascuna` resuming a plural subject** (2): inferno 5:14, paradiso 1:113.
- **The copula agreeing with its plural predicate nominal** (1): paradiso 24:100 *La prova … son
  l'opere seguite*.
- **An anacoluthon Dante writes himself** (1): purgatorio 10:112 *quel ch'io veggio … non mi
  sembian persone*.
- **Non-Italian text** (4): the Provençal of purgatorio 26:142/147 (*que plor*, *sovenha vos*), the
  Latin quotation *‘Sperent in te’* (paradiso 25:98) and Nimrod's *Raphèl maì amècche zabì almi*
  (inferno 31:67). Layer 2 tags these as best it can; no Italian agreement rule applies.

`dep --check` reports **0 hard, 18 soft** (173 → 18, all remaining ones the list above);
`morph --check` 0/0, `np --check` 0/0, `case --check` 0 hard, `pytest` 168 passed (nine new tests
for the rule and its exclusions).

**Layer 5's soft count rose, 3215 → 3270 (+55)**, the same honest reading as the multiple-`obj`
round: `derive_unit` reads Layer 4, so correcting an attachment turns a spurious agreement with the
LLM into a real disagreement. `missing_arg` fell 1053 → 985 (−68) while `missing_tuple` rose
35 → 140 (+105, the 99 promoted speech frames, which the derivation treats as elided predicates).
See [`../skel/CORRECTIONS.md`](../skel/CORRECTIONS.md)'s entry of the same date.

## Eight retags from Layer 5's membership and Inferno-1 audits (2026-08-09)

Two audits ran against Layer 5's soft classes (see
[`../skel/CORRECTIONS.md`](../skel/CORRECTIONS.md)): a per-position read of Inferno 1's twelve
violations, and a corpus-wide classification of the 82 `membership` violations. Most of what they
found was Layer 2's or the checker's, but eight `dep` rows were wrong and are corrected here.

- **inferno 1:112, "Ond' io per lo tuo me' penso e discerno" (4 rows)** — *me'* (= *meglio*, a
  noun) was tagged `expl` with *tuo* carrying the oblique instead, so `per lo tuo me'` had no head.
  Now `per` `case` → *me'*, `lo` `det` → *me'*, `tuo` `det:poss` → *me'*, `me'` `obl` → *penso*,
  which is also what Layer 3's `[lo tuo me']` span (head *me'*) says. Closed the position's
  `missing_arg`/`extra_arg obl:per` pair.
- **inferno 13:97, "Cade in la selva, e non l'è parte scelta"** — *l'* was `det` of *parte*; an
  article cannot precede *è*. It is the dative clitic (*le*, "for it"): now `iobj` → *parte*, the
  copular predicate's head. Layer 2 retagged with it.
- **inferno 20:80, "ne la qual si distende e la 'mpaluda"** — *la* was `nsubj` of *'mpaluda*; it is
  the object clitic (the *lama* the Mincio turns to marsh). Now `obj`.
- **inferno 30:121, "la sete onde ti crepa"** — *onde* was `nsubj` of *crepa*. It is "from which",
  an oblique; the clause's subject is pro-drop. Now `obl`.
- **paradiso 21:54, "ma per colei che 'l chieder mi concede"** — *'l* was `obj` of *chieder*. Here
  *'l* really is an article, of the nominalized infinitive *'l chieder*, which is itself the object
  of *concede*: now `det` → *chieder*. (The one position in the audit where the article reading was
  the right one.)

`dep --check` stays 0 hard / 18 soft (the subject-agreement rule's verified-and-left-alone
residue). Layer 5's soft count fell 2625 → 2623 on the inferno 1:112 rows; the other four are
inside the `membership` movement recorded in [`../morph/CORRECTIONS.md`](../morph/CORRECTIONS.md).

## Eleven retags from Layer 5's Inferno 1-3 read (2026-08-12)

The per-position read of all 26 Layer-5 soft violations standing in Inferno 1-3 (full write-up in
[`skel/CORRECTIONS.md`](../skel/CORRECTIONS.md)'s *Rules Y-AF*). Eight of the 26 turned out to be
checker silence and produced rules; these are the ones where **Layer 4 was wrong**. `dep --check`
stays 0 hard / 18 soft — the subject-agreement rule's verified-and-left-alone residue, unchanged.
(The 3:76 retag below opened a nineteenth agreement violation on the way through: making `cose`
the subject of `fier` exposed that Layer 2 had read `fier` as 1sg of `fare`. Correcting Layer 2
closed it again, which is the agreement rule doing exactly the job it was built for.)

| position | was | now | why |
|---|---|---|---|
| inferno 2:59.2 `cui` | `nmod` → 58.2 `anima` | `nmod` → 59.4 `fama` | *"di cui la fama ... dura"*: `cui` is the genitive of `fama`, the noun standing next to it, not of the vocative two lines up. Layer 5's rule D accepts an oblique hanging off a derived argument, and this attachment put it out of reach of that rule for no reason. |
| inferno 2:71.5 `tornar` | `nsubj` → 71.6 | `xcomp` → 71.6 | *"ove tornar disio"*: with `disio` corrected to the 1sg verb (Layer 2, same session), the infinitive is its complement, not the subject of a noun. |
| inferno 2:102.1 `che` | `obl` → 102.3 | `nsubj` → 102.3 | *"che mi sedea con l'antica Rachele"*: the relative pronoun is the subject of `sedea`. Layer 2 had it tagged a conjunction, which is the mistag family that hid it. |
| inferno 3:13.1 `Ed` | `cc` → 14.3 | `cc` → 13.2 | The elided verb of speech, **still un-normalized**: *"Ed elli a me, come persona accorta: «Qui si convien …»"* attached its whole frame to the verb *inside* the quotation. The 2026-08-07 round converted 99 such frames and missed this one. Now identical in shape to 3:34 and 3:76. |
| inferno 3:13.2 `elli` | `nsubj` → 14.3 | `root` | |
| inferno 3:13.4 `me` | `obl` → 14.3 | `obl` → 13.2 | |
| inferno 3:13.6 `persona` | `obl` → 14.3 | `obl` → 13.2 | |
| inferno 3:14.3 `convien` | `root` | `ccomp` → 13.2 | |
| inferno 3:76.6 `cose` | `nmod` → 76.9 | `nsubj` → 76.8 | *"Le cose ti fier conte"*: `fier` is 3pl of `essere` (Layer 2 had read it as `fare`, 1sg), `cose` its subject and `conte` the f. pl. predicate adjective. The old parse made the subject a modifier of the complement and left the clause with a pro-drop subject it does not have. |
| inferno 3:76.9 `conte` | `obj` → 76.8 | `attr` → 76.8 | |
| inferno 3:126.5 `si` | `obl` → 126.6 | `expl` → 126.6 | *"la tema si volve in disio"*: the reflexive clitic, which the multiple-`obj` round wrote as `expl` corpus-wide. |

Layer 5's count rose by four across the last two of these — at 3:13 the promoted frame is a
predicate the LLM never proposed, and at 3:76 the corrected parse no longer matches the LLM's
(wrong) reading of the line. Both are `--fix` material, the same reading recorded in PLAN.md's
*A note on Layer 5's count*; neither is a reason to revert a correct parse.

## Nine retags from Layer 5's Inferno 7-10 read (2026-08-14)

Surfaced by the per-position read of all 37 Layer-5 soft violations standing in Inferno 7-10 (see
[`skel/CORRECTIONS.md`](../skel/CORRECTIONS.md)'s *Rules AH-AL*). `dep --check` stays 0 hard / 18
soft (the subject-agreement rule's verified standing residue); the accompanying Layer-2 retags are
in [`morph/CORRECTIONS.md`](../morph/CORRECTIONS.md).

| position | was | now | why |
|---|---|---|---|
| inferno 8:78.6 `ferro` | `nsubj` → 78.7 | `attr` → 78.7 | *"le mura mi parean che ferro fosse"*: `ferro` is what the walls *seemed to be*, the predicate nominal — the subject of `fosse` is the elided *le mura*. Read as the subject, the clause lost its predication and gained a subject the line does not have. |
| inferno 9:41.1 `serpentelli` | `nsubj` → 41.4 | `obj` → 41.4 | *"serpentelli e ceraste avien per crine"* — the Furies **have** snakes for hair. Line 39 two lines earlier already has the correct shape for the same verb (*"che membra feminine avieno"*: `che` nsubj, `membra` obj); 41 was inconsistent with it, and the inversion made the snakes the subject of *avere*. |
| inferno 9:41.2 `e` | `conj` → 41.3 | `cc` → 41.3 | Follows from the above — the coordination is between the two objects, exactly as `e`/`atto` are coordinated at 39. |
| inferno 9:41.3 `ceraste` | `nsubj` → 41.4 | `conj` → 41.1 | |
| inferno 9:72.5 `fiere` | `obj` → 72.3 | `nsubj` → 72.3 | *"e fa fuggir le fiere e li pastori"*: the causee of *fare* + infinitive is the infinitive's **subject** — a rule `skel/skel.py`'s own `SYSTEM_PROMPT` states, and which Layer 4 was contradicting here. |
| inferno 9:103.2 `quella` | `obl` → 102.6 | `nmod` → 102.5 | *"altra cura ... che quella di colui"*: `quella` is the standard of a comparison modifying `cura`, not an oblique argument of `stringa`. As an `obl` under a `case` child `che`, it made the derivation mint the preposition-shaped role `obl:che` out of a comparative conjunction. |
| inferno 10:85.6 `strazio` | `obj` → 87.4 | `nsubj` → 87.3 | *"Lo strazio e 'l grande scempio ... tal orazion fa far nel nostro tempio"* = "the slaughter … causes such prayer to be made in our temple". Subject and object of the causative pair were exchanged. |
| inferno 10:87.2 `orazion` | `nsubj` → 87.3 | `obj` → 87.4 | |
| inferno 10:23.2 `ten` | `advcl` → 23.3 | `expl` → 23.3 | Follows the Layer-2 retag of `ten` to the clitic cluster `te+ne`; tagged exactly like `sen` at 10:1 of the same canto. |

### Three `come`/`perché` structures, from the conjunction-in-argument-slot census

The same read enumerated every token Layer 4 fills an argument slot with while Layer 2 calls it a
`conjunction` (250 corpus-wide). 247 are the relative `che`/`ch'`/`onde` mistag family, which is a
**Layer-2** defect deliberately left standing — see
[`morph/CORRECTIONS.md`](../morph/CORRECTIONS.md) for why the retag is gated on a `case`-annex
build round. The remaining 3 were Layer-4 structure errors and are fixed here:

| position | was | now | why |
|---|---|---|---|
| inferno 30:59.5 `perché` | `ccomp` → 59.3 | `advmod` → 59.3 | *"e non so io perché"*: a bare interrogative adverb standing for an elided indirect question. It heads no clause, so `ccomp` asserted a clausal complement that is not written. |
| paradiso 3:36.2 `com'` | `obl` → 35.6, with `uom` as its `obj` | `case` → 36.3 | *"quasi com' uom cui troppa voglia smaga"*: the comparative marker was made the head of the phrase and given an object. `com'` is the marker; `uom` is the oblique. |
| paradiso 32:54.3 `come` | `obl` → 53.4, with `tristizia` as its `obj` | `case` → 54.4 | *"se non come tristizia o sete o fame"* — same shape, same fix. |

The `perché` correction **raised** Layer 5's count by two (an `extra_tuple` and an `extra_arg` at
inferno 30:59): the old `ccomp` was licensing an LLM reading that opened a predicate on an adverb,
which the corpus's own rule forbids. The two new violations are correct flags of a real LLM error
the mistag had been masking — the same trade this file records at inferno 3:13 and 3:76.

## The agreement rule's last 18 positions, closed (2026-08-14)

The subject/head agreement rule had stood at **18 soft violations** since it opened
(*The subject/head agreement rule*, above). Each was read against its terzina then and left alone
as "a property of the text, not of the parse" — but that verdict lived only as prose here, so the
count still carried a residue nothing in the code explained. All 18 were re-read; the result is
**0 hard, 0 soft** for `dep --check`, reached three different ways.

### One real mis-attachment (purgatorio 26:147)

*sovenha vos a temps de ma dolor!* — Arnaut's Occitan. `sovenir` is impersonal here: `vos` is the
experiencer and `de ma dolor` the complement, so the clause has no nominal subject at all. Two
rows changed: `vos` `nsubj` → `iobj`, and `dolor` `nmod` → `obl` on `sovenha` (it was hanging off
`temps`, making *a temps de ma dolor* one phrase, which it is not). This is the one position where
the parse, not the text, was wrong, and it closes on its own merits.

### Six exclusions, each measured corpus-wide before it was written (10 positions)

The discipline is the one the rule's first round set: an exclusion must be defensible corpus-wide,
not fitted to a position. Every candidate was run over all 6 000 `nsubj` edges first, and the
counts below are `disagree → undecidable` / `agree → undecidable`. **The second number is 0 for
all six**, which is what makes them safe for Layer 5: `skel._find_repairs` repairs only on
`"agree"`, so no repair anywhere in the corpus was taken away.

| exclusion | what it recognizes | positions | agree touched |
|---|---|---|---|
| distributive subject | `ciascuno`/`ognuno` under a plural head, resuming it one member at a time — *vanno a vicenda **ciascuna** al giudizio* | inferno 5:14, paradiso 1:113 | 0 |
| coordination inside the subject phrase | a `cc` child alongside an `nmod`/`conj`/`appos` child — *e l'uno e l'altro **coro*** is two choirs on one noun | paradiso 14:62 | 0 |
| comitative phrase on a plural head | a `con`-phrase on the head — *necesse con contingente … **fenno***. The 3rd-person case of the existing 1/2-plural exclusion | paradiso 13:98 | 0 |
| quantified measure subject | a plural subject with a `nummod` child or a `molto` determiner, under a singular head — *cento miglia … **sazia***, *non **è** molt' anni* | inferno 19:19, 21:114, purgatorio 14:18 | 0 |
| copula agreeing with its predicate nominal | an `attr` child agreeing with the head while the subject does not — *La prova … **son** l'opere seguite* | purgatorio 10:112, paradiso 24:100 | 0 |
| impersonal `si` with a postposed subject | an `expl:impers`, or an `expl` Layer 2 notes `impersonal`, with a plural subject after it — *non si **convenia** più dolci salmi* | inferno 31:69 | 0 |

Two candidates were **narrowed** by the measurement rather than accepted as first drafted: the
`attr` rule matched 5 agreeing pairs (`dir`, `discriver`, `esser`, `peccar` — infinitive subjects
with no `number` at all) until it was gated on both numbers being present, and the impersonal-`si`
rule matched **41** agreeing pairs until it was gated on the plural-subject/singular-head shape.
Without those gates each would have silently cost Layer 5 real repairs. This is the whole reason
the population is measured before the rule is written.

### Two `note` flags for what no rule can state (7 positions, 70 rows)

The rest are the two classes whose criterion is a lexicon or a language identifier, both of which
PLAN.md's *Neutrality audit* keeps out of the corpus. They take the `NO_NP`/`CONT_NEXT` treatment
instead — a machine-readable flag in the Layer-2 `note`, one hand-verified row at a time (see
[`../morph/CORRECTIONS.md`](../morph/CORRECTIONS.md)):

- **`AD_SENSUM`** (4 rows) — agreement is notional rather than grammatical, in either direction:
  the collective singulars *il mal seme d'Adamo **gittansi*** (inferno 3:115), *La gente … **si
  parton*** (purgatorio 26:76), *quella gente allor **cantaro*** (purgatorio 32:62), and the
  converse aggregate *diverse colpe … **grava*** (inferno 6:86).
- **`FOREIGN`** (66 rows) — the token is not Italian, so no Italian agreement rule applies:
  Arnaut's Occitan (purgatorio 26:140-147, all 58 tokens), the Latin incipit *‘Sperent in te’*
  (paradiso 25:98.1-3) and Nimrod's *Raphèl maì amècche zabì almi* (inferno 31:67). The flag marks
  every token of the passage, not only the two a violation named: foreignness is a property of the
  token, and half-flagging a line would be the arbitrary thing to explain later.

Three of the four positions the original round listed as "non-Italian text" close this way; the
fourth was purgatorio 26:147, corrected above.

The two positions the round's own list called irreducible — the anacoluthon *quel ch'io veggio …
non mi **sembian** persone* (purgatorio 10:112) and the copular attraction at paradiso 24:100 —
turned out to be the same construction and needed no flag: both are the `attr` exclusion.

**Layer 5's soft count rose 1091 → 1094 (+3)**, and every one is accounted for:

- `inferno 6:87 missing_arg subj (86,2)` — rule AG (`skel`, gated on this rule's `"disagree"`) no
  longer drops the `conj`-inherited `colpe` subject there, because `colpe`/`grava` is now
  `AD_SENSUM`-exempt and therefore *undecidable*. The honest reading: AG was leaning on a
  disagreement the text licenses.
- `purgatorio 26:147 missing_arg obl:a` and `obl:di` — the two obliques the re-attachment above
  gives `sovenha`, which the LLM's own reading of the Occitan does not list.

`dep --check` **0 hard, 0 soft**; `morph --check` 0/0, `np --check` 0/0, `case --check` 0 hard,
`skel --check` 0 hard / 1094 soft, `pytest` **265** passed (eight new tests, one per exclusion
plus a flagged/unflagged pair proving `AD_SENSUM` is a per-row exemption and not a rule about the
word `gente`).

## The multiword-preposition normalization, 161 clusters rewritten (2026-08-14)

Layer 4 wrote stacked prepositions two ways: **flat** (both members `case` children of the
nominal — *"trovar dentro al tuo seno"*) and **chained** (outer member a `case` child of the
inner — *"Vòlt' era in su la favola"*: `in` → `su` → `favola`). The shape decided which
preposition a downstream derivation named, so the same phrase produced different labels by
accident of tree shape. This round picks one shape — UD's multiword-expression convention, the
opening word the head:

> In a stacked preposition only the opening word takes `case` on the nominal; each later word
> takes `fixed` on the opening word (*"in su la cima"* → `in` `case`→ `cima`, `su` `fixed`→
> `in`).

**161 clusters, 196 rows, 74 files**, rewritten by a gated script (idempotent; a second run
plans 0 edits). The gates keep the rewrite a pure shape change — Layer 4 already asserted every
member is a preposition of the nominal — and exclude:

- **Adverb-preps Layer 2 tags `adverb`** (`dentro a`, `dinanzi a`, `dietro a`, `intorno a`,
  `fuor di`, `infino al`, `sotto al`, `dintorno al`, `innanzi a` — 40 clusters): a Layer-2/4
  tension this round does not decide. They stay flat, and derivation + rule O keep accepting
  either member, exactly as before.
- **Genuine coordinations and ranges** (`dal quarto al quinto`, `a maggiore e … a minor passo`,
  *"in su le vecchie e 'n su le nuove cuoia"*, `di…di`, `a…a`, `dal…dal`, `de…de`, cross-line
  *"fioretti"*): non-contiguous case children of one nominal, never a stack.
- **One mis-attachment read** (purgatorio 5:53 *"qual d'una pianta"*: `qual` tagged `case` under
  a pronoun POS) — a reading question, left standing.

The rewrite preserves which preposition each derivation names everywhere except the 34 chained
clusters, where the named lemma deliberately flips inner → opening to match the flat majority
(see [`skel/CORRECTIONS.md`](../skel/CORRECTIONS.md) for the measured Layer-5 effect: net zero).
`derive_unit`'s `case`-child rule and rules O/`prep_stack` now read the normalized shape via a
`fixed`-under-`case` lemma aggregation in `dante_corpus/skel.py` (three new tests). The build
prompt (`dep/dep.py`) and this README now state the convention for future regenerations.

`dep --check` after the round: **0 hard, 0 soft**.

## Sixteen rows from the Layer-5 Inferno 11–15 read (2026-08-15)

Found position by position while auditing Layer 5's soft violations in Inferno 11–15 (see
[`../skel/CORRECTIONS.md`](../skel/CORRECTIONS.md)). Each was decided from the line itself, applied
by a gated script that checks the word at every index before rewriting it, and re-validated:
`dep --check` **0 hard / 0 soft**, `morph`/`np`/`case` unchanged at 0.

| position | before | after | why |
|---|---|---|---|
| inferno 12:2.2 `alpestro`, 12:3.1 `tal` | `amod`→ 1.3 `loco` | `attr`→ 1.1 `Era` | *«Era lo loco … alpestro e … tal ch'ogne vista ne sarebbe schiva»* — both are predicative complements of `Era`, not attributes of `loco`. |
| inferno 12:22.1 `Qual`, 12:22.4 `toro` | `nsubj` / `attr` | `attr` / `nsubj` | *«Qual è quel toro»* — `quel toro` is the subject and `Qual` the predicate nominal, which is exactly how 12:4 (*«Qual è quella ruina»*) is already tagged. The two rows were inconsistent with each other. |
| inferno 12:90.5 `io`, 12:90.6 `anima`, 12:90.7 `fuia` | `nsubj`→90.7, `appos`→90.5, `conj`→90.2 | `nsubj`→90.6, `conj`→90.3, `amod`→90.6 | *«non è ladron, né io anima fuia»* — with `fuia` retagged an adjective in Layer 2, `anima fuia` is a predicate nominal coordinated with `ladron`, and `io` its subject. |
| inferno 13:141.9 `disgiunte` | `amod`→ 141.5 | `xcomp`→ 141.2 | *«c'ha le mie fronde sì da me disgiunte»* — an object complement of `ha`, the resultative reading the `sì …` degree adverb requires. |
| inferno 14:44.4 `fuor`, 44.5 `che`, 44.6 `demon` | `obl`→43.6, `case`→44.6, `obj`→44.4 | `case`→44.6, `fixed`→44.4, `obl`→43.6 | *«fuor che ' demon duri»* — a multiword preposition in the shape the 2026-08-14 normalization froze. It was excluded from that round because Layer 2 tags `fuor` an adverb; the excluded set stands, but this cluster had `demon` as the *object of an adverb*, which no reading supports. |
| inferno 14:103.1 `Dentro`, 103.2 `dal` | `advmod`→103.4, `case`→103.3 | `case`→103.3, `fixed`→103.1 | *«Dentro dal monte»* — same shape, and the source of one of the three obl-vs-obl residues that round recorded as "genuine disagreements". It was a stack shape after all. |
| inferno 14:116.2 `Acheronte` | `nsubj`→116.1 | `obj`→116.1 | *«Lor corso in questa valle si diroccia; fanno Acheronte, Stige e Flegetonta»* — the rivers are what the waters *make*. 14:119 (*«fanno Cocito»*) already had `obj`; the two coordinated clauses disagreed. |
| inferno 11:70.3 `quei` | `nsubj`→74.3 | `dislocated`→74.3 | *«quei de la palude pingue … perché … sono ei puniti?»* — a left-dislocated topic resumed by `ei`, which is the clause's own subject. The row made `puniti` carry two subjects. |
| inferno 19:106.3 `pastor` | `appos`→106.7 `Vangelista` | `appos`→106.2 `voi` | *«Di voi pastor s'accorse il Vangelista»* — Layer 3's own NP span `[voi pastor]` says which noun it is appositive to. Surfaced by Layer 5's new rule AP, which collapses an apposition onto its host and so made the mis-attachment visible as a `missing_arg`. |

Layer 5 measured the whole set at **895 → 888 (−7)**. Two positions trade rather than clear: at
14:116 the corrected `obj` turns an `extra_arg` into a `role_mismatch` because the reading has the
river as subject, and at 14:43 the normalized cluster leaves the reading citing the preposition
itself. Both are now disagreements with a correct tree rather than with a wrong one.

## Twenty-five rows from the Layer-5 Inferno 16–20 read (2026-08-15)

Found position by position while auditing Layer 5's soft violations in Inferno 16–20 (see
[`../skel/CORRECTIONS.md`](../skel/CORRECTIONS.md)). Applied by a gated script that asserts the
word, the deprel and the head at every index before rewriting the row, then re-validated:
`dep --check` **0 hard / 0 soft**, `morph`/`np`/`case` unchanged at 0.

| position | before | after | why |
|---|---|---|---|
| the reflexive clitic in 15 places — inferno 17:102.6, purgatorio 9:36.6, 11:128.3, 21:59.7, 24:84.7, 28:75.8, 28:102.8, 28:138.5, 33:97.6, paradiso 11:14.7, 13:122.7, 14:77.2, 15:17.9, 24:123.7, 31:106.7 | `nsubj` | `expl` | *«si sentì a gioco»*, *«dove si fosse»*, *«non si scolpa»* — `si`/`s'` is never the clause's subject. The 2026-08-03 round normalized the reflexive clitic onto UD's `expl` corpus-wide; these 15 rows were left behind, and each one filled a subject slot the sentence leaves pro-drop, several of them propagating on across `conj`. |
| inferno 17:103.7 `coda` | `nsubj`→103.8 | `obj`→103.8 | *«là 'v' era 'l petto, la coda rivolse»* — the tail is what Geryon turns, not what turns; the subject is the elided beast. The mis-tagged subject was inherited by three further conjuncts (104.6, 105.9). |
| inferno 17:48.3 `vapori`, 48.1 / 48.5 `quando` | `advcl`→47.5, `mark` | `obl`→47.5, `advmod` | *«quando a' vapori, e quando al caldo suolo»* — a noun carrying its own `case` child is an oblique of the gapped `soccorrien`, not a clause head. The `advcl` made `derive_unit` mint two predicates out of two prepositional phrases. |
| inferno 18:122.6 `Lucca` | `obl`→122.2 `se'` | `nmod`→122.3 `Alessio` | *«e se' Alessio Interminei da Lucca»* — the toponym is part of the name, which is what Layer 3's own NP span `[Alessio Interminei da Lucca]` already says; as an oblique of the copula it became an argument of the predication. |
| inferno 17:85.1 `Qual` | `advmod`→85.2 | `attr`→85.2 | *«Qual è colui che … tal divenn' io»* — the correlative is the copula's predicative complement. Inferno 12:22 was corrected the same way in the previous batch. |
| inferno 16:95.1 `prima`, 95.3 `Monte`, 95.6 `levante`, 96.4 `costa` | →100.1 `rimbomba` | →94.5 `ha` | *«Come quel fiume c'ha proprio cammino / prima dal Monte Viso 'nver' levante, / da la sinistra costa d'Apennino, … rimbomba là sovra San Benedetto»* — the adverb and the three obliques say where the Montone's *course* runs, inside the relative clause five lines earlier. Hung on `rimbomba` they assert the resounding happens at Monviso. |

Layer 5 measured the whole set at **−14** (853 → 839, on top of that session's checker rules). The
16:95–96 reattachment is deliberately **count-neutral** — the three `missing_arg`s move from
`rimbomba` to `ha` — and was kept because the tree is now right; the same trade rule AM recorded.

## Twelve rows from the Layer-5 Purgatorio 26–30 read (2026-08-17)

Found position by position while auditing Layer 5's soft violations in Purgatorio 26–30 (see
[`../skel/CORRECTIONS.md`](../skel/CORRECTIONS.md)). Applied by a gated script that asserts the
word, the deprel and the head at every index before rewriting the row, then re-validated:
`dep --check` **0 hard / 0 soft**, `morph`/`np`/`case` unchanged at 0.

| position | before | after | why |
|---|---|---|---|
| purgatorio 28:110.7 `aura` | `nsubj`→110.8 | `obj`→110.8 | *«che de la sua virtute l'aura impregna / e quella poi, girando, intorno scuote»* — the air is what the struck plant impregnates. The next line resumes it as `quella`, a *new* subject, which only parses if the air was the object here; `impregna`'s own subject is the pro-drop `la percossa pianta`. |
| purgatorio 27:80.4 `che`, 80.8 `verga`, 81.1 `poggiato`, 81.2 `s'`, 81.3 `è`, 81.8 `serve` | clause head `è`, participle `amod`→80.4 | clause head `poggiato`, `è` `aux`→81.1 | *«il pastor, che 'n su la verga / poggiato s'è»* — a compound perfect of `poggiarsi` read as an adjective plus a copula. The participle is the lexical verb, so the `acl:relcl` edge, the subject, the oblique and the coordinate `serve` all belong on it. |
| purgatorio 30:60.8 `far`, 60.9 `l'`, 60.10 `incora` | `conj`→59.7, `det`→60.10, `obj`→60.8 | `advcl`→60.10, `obj`→60.10, `conj`→59.1 | *«viene a veder la gente che ministra / per li altri legni, e a ben far l'incora»* — `incora` is a finite verb (3sg of `incorare`) that had been attached as the *object* of an infinitive, with the accusative clitic `l'` as its `det`. It is the coordinate of `viene`: the admiral comes to see the crew and encourages them to do well. A pronoun in a `det` deprel under a **verb** head is censused at 3 rows corpus-wide; the other two are demonstratives before a nominalized infinitive. |
| purgatorio 28:38.2 `cosa`, 40.2 `donna` | `nsubj`→37.4, `appos`→38.2 | `nsubj`→37.8, `nsubj`→37.4 | *«e là m'apparve, sì com' elli appare / subitamente cosa che disvia … / una donna soletta»* — the simile's subject is `cosa` (with `elli` the expletive Dante's `com'elli appare` always carries) and the main clause's is `donna`. Layer 4 had given `cosa` to the main verb and left `donna` as an apposition of it. |

Layer 5 measured the whole set at **−7 / +2**, net −5. The two new positions are at 30:59–60 and
are the honest cost: with `incora` correctly a predicate, the LLM's own misreading — it made the
infinitive `far` the coordinate — is no longer hidden by the wrong tree. The same trade the
Purgatorio 21–25 batch recorded at 25:67 and 22:90.
