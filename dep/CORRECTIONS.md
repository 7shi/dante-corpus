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
