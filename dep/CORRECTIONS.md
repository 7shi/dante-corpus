# dep — Layer 4 correction history

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
