# skel — Layer 5 correction history

## Rule EG and the sixth round's prompt repairs — 174 → 224, +50 by design (2026-08-18)

The sixth `--fix` round (see [`PLAN.md`](PLAN.md) §27) left 174 soft violations and produced one
finding that no read batch could have produced: **the checker has never looked at the artifact's
internal consistency.** Rule EG closes that, and **raises the count by 50** — the honest trade rule
AM records, and the first rule in the series whose whole value is that it *reports* something.

| rule | shape | census | net |
|---|---|---:|---:|
| **EG** (`_dual_role_violations`) | one token filling **two roles of one predicate** in the artifact, other than rule AL's fused clitic | 56 / 7 licensed | **+50** |

Plus two prompt-side repairs the round's measurements pointed at (they move nothing until a round
runs): the **`arg_slot` merge** and **`_CONV_DATIVE`'s rewritten citation instruction**.
`pytest` **511 passed** (17 new), 0 hard, all other layers 0/0.

### Rule EG — the first check that reads the artifact against itself

Every rule from V to EF compares the LLM's reading with `derive_unit`. That comparison is blind to
a contradiction *inside* the reading: when a token is written into two roles of one predicate and
**one** of those rows matches the derivation, the other row is constrained by nothing at all, and
the position is silent.

The evidence line is the sixth round's own output. At paradiso 1:81, *«… che pioggia o fiume / lago
non fece alcun tanto disteso»*, the round added `81.3 fece: obj=(81,4)` beside the `subj=(81,4)`
already there — `alcun` as both the subject and the object of `fece`, when Layer 4 reads it as the
determiner of `lago` and the subject as `pioggia` (80.7). It was accepted because `_is_improvement`
grades the **unit**, and the same call had cleared two `missing_arg`s on 79.1.

Censused over all 100 cantos: **56** such positions. **Seven** are the shape rule AL exists to
license — a fused clitic is two pronouns in one Layer-1 token and genuinely fills two slots (*«non
**gliel** celai»* inferno 10:44, `gli` + `lo`; *«**sen** venne a riva»* purgatorio 2:40, `si` +
`ne`) — and the gate that grants them is `_fused_clitic_dual_role` itself, applied to each pair of
roles the token was given, so the new check and rule AL agree by construction rather than by a
copied condition. **52 of the 56 sit on a line the checker reports nothing about**, which is why 21
read batches walked past them: a read compares the two readings of a position `--check` has named.

The 49 that are errors fall into three sub-shapes:

- **A nominal as both `subj` and `obj` of one verb (27).** *«Le braccia aperse»* (inferno 24:22) —
  `braccia` is the object and the subject is pro-drop; *«per li miei prieghi ti chiudon le mani»*
  (paradiso 33:39) — `mani` is the subject; *«serpentelli e ceraste avien per crine»* (inferno 9:41).
- **An oblique or predicative role against the subject (14)**: `subj` + `obl:di` (3, paradiso 1:79,
  21:87), `obl:per` (2, inferno 9:119, on two predicates of one line), `obl:in` (2), `obl:a` (2),
  bare `obl` (2), `attr` (2, inferno 31:31, purgatorio 9:74), `obl:da` (1).
- **One relation written twice at two levels of specificity (4)**: `obl` beside `obl:a`
  (inferno 25:138 `dietro`, paradiso 15:59 `te`), `obl` beside `obl:in` (purgatorio 33:77
  `dentro`), `obl:da` beside `obl:di` (paradiso 14:74). One relation, two rows.
- **Four further pairs of two incompatible non-subject roles**: `obj` + `obl:verso`
  (paradiso 17:106), `obj` + `obl:presso` (purgatorio 17:67), `obj` + `attr` (paradiso 31:41),
  `attr` + `obl:quale` (purgatorio 19:67).

**One position is a fused clitic rule AL's gate does not license, and it is left flagged**:
purgatorio 2:40's `sen` is written `obl:si` **and** `obl:ne`, and rule CM's licence reads the annex
through `_case_supports_role`, which maps no slot to a role named after a clitic rather than a
preposition. Widening rule AL to `obl:si` is a change to *that* rule's gate and needs its own
census, which this session did not take. Flagged, and recorded here as the census item.

**Kept soft, not hard**, for two reasons: the population predates the check, and `--fix`'s
acceptance gate refuses any candidate with a hard violation — which would make the 49 unrepairable
by the instrument that should repair them. What stops a *new* one from being written is the splice
guard below.

### The splice guard — the round wrote one, so the applier must refuse one

`_apply_missing_arg` answers "which token fills this slot?" by **appending** a row, and never looked
at the rows already there. So the class that is supposed to add a missing argument could write the
contradiction rule EG now reports, and paradiso 1:81 is that happening. The guard refuses the splice
when the predicate already holds that token in another role, licensing the same exception through
rule AL's own gate. Mutation-checked: removing the guard fails
`test_apply_missing_arg_refuses_to_put_one_token_in_two_roles`.

### The `arg_slot` merge — one slot, one question

Eight predicates in the standing 174 carry a `missing_arg` **and** an `extra_arg` on the *same*
role — inferno 5:92, 24:10 (two predicates), 31:32, purgatorio 9:97, 10:30, 10:60, paradiso 1:81 —
which is **one** disagreement (*which token fills this slot*) counted as two positions, 16 of the
174. `_CLASS_ORDER` asked it as two questions in two separate calls, and neither call was told the
other side existed: the `extra_arg` question offers `keep` and the `missing_arg` question invites the
token the reading already wrote, so **neither single-class splice can improve the pair**, and the
pair had survived three rounds untouched.

`_split_slot_conflicts` now routes each such pair to one new class, `arg_slot`, keeping the
`extra_arg` half because it carries the filler the reading itself supplied — the half a question is
allowed to quote. The merged question names the predicate, the slot, and that filler, and offers
`keep` / a token position / `0.0` / `none`. **The independence rule is unchanged**: the derivation's
own filler is never named, and `test_arg_slot_question_names_the_reading_own_filler_and_not_the_
derived_one` pins it.

### `_CONV_DATIVE` — the clause told the model to write a role its class cannot set

The round measured `_CONV_DATIVE` at −8.3% (`missing_arg obl:a` 12 → 11), under half the round
average, and the wording is a sufficient explanation. It ended *"Cite it as `iobj` at its own token
position"* — but the clause hangs on the generic `missing_arg` class alone, whose question asks
*which token* fills a slot the question itself names, and whose applier splices the role from the
violation rather than from the answer. The slot named at every one of these positions is `obl:a`,
because that is what the derivation emits for a bare dative clitic (rule AB). So the instruction was
unfollowable, and the name the checker uses for the slot went unmentioned. Rewritten to name the
slot the way the question does (`iobj` or `obl:a`) and to say nothing about setting a role.

This is a fourth form of the prompt lesson six rounds have now measured: the two clauses that ever
moved a class (`_CONV_ADVERB_ARG`, `_CONV_ADJUNCT`) each **withdrew or narrowed a licence the prompt
itself had granted**, while every clause that added prose about a shape the model reads wrong
measured at the round average — and this one could not even be obeyed.

### Tests

17 new (`pytest` 494 → **511**): six on rule EG itself (the flag, one-role-per-token, the ∅
sentinel, rule AL's licence, a single pronoun still flagged), two on the splice guard, five on the
`arg_slot` merge and its question, four on the `dual_role` repair question and its applier. Each
mutation-checked — including the merge's *call site* in `_fix_canto`, which a first pass left
unpinned (`test_fix_canto_asks_a_same_slot_pair_as_one_question`, on inferno 5, whose only flagged
unit is a same-slot pair). Two existing tests were updated rather than weakened: purgatorio 1 now
carries three soft violations, not one, because rule EG flags 96.6 and 133.7.


## Rules EB-EF, from reading Paradiso 26-33 — 234 → 213, −21 (2026-08-17)

Per-position read of all **32** soft violations in Paradiso 26-33 — the **last two batches of the
read series**, taken in one session — following the eight-step procedure in
[`PLAN.md`](PLAN.md)'s *How to Read a Batch*. Zero model calls. Paradiso 26-33 itself went
**32 → 14** (26: 4 → 3, 27: 1 → 1, 28: 6 → 4, 29: 7 → 2, 30: 5 → 1, 31: 2 → 1, 32: 3 → 1,
33: 4 → 1); the corpus went **234 → 213 (−21, −9.0%)**. Five deterministic rules, 16 Layer-4 rows,
6 Layer-2 rows, 4 Layer-3 spans and 2 case-annex rows. `pytest` **494 passed**, 0 hard, all other
layers 0/0. **The read series now covers all 100 cantos.**

| rule | shape | census | net |
|---|---|---:|---:|
| **EB** (`_comparative_come_adjunct`) | rule AR's marker gate names the **word** `come`, not the deprel it was written with or the tag Layer 2 gave it | 812 rows / 8 deprels / 4 tags | **−3** |
| **EC** (`_comparative_come_adjunct`) | rule AR's no-correlative branch, opened by rule BA's evidence: two derived subjects mean a collapsed clause, and the marker is the gap boundary rule CW's positional test cannot see | 13 / 598 | **−1** |
| **ED** (`_comparison_clause_hosts`) | rule AR's `extra_arg` leg from the matrix side: the comparison Layer 4 headed on `come` itself, whose adjunct the LLM lists on the matrix predicate | 14 | **−1** |
| **EE** (`_prep_stack_nominal`) | rule BV's opening-word leg: the `case` row a multiword preposition's `fixed` members hang on is one of the preposition's own words, so the citation is the nominal it opens | 167 | **−2** |
| **EF** (`derive_unit`) | the `conj` shared-subject propagation stops at a **sibling** conjunct that has already supplied one | 23 / 3658 | **−3/+1** |

Plus the upstream rows, **−14/+2** between them (counted below).

### The batch's first finding — a POS gate, a deprel gate, and the word underneath both

Rule DY (the Paradiso 21-25 batch) found that rule DD's "adverb" gate was really a claim about the
word `onde`, because `onde` carries four Layer-2 tags under one deprel. Rule EB is the same
finding with the *edge* column added to it, and with the largest tag census the series has taken.
`come`/`com` is written **812** times in the corpus, under **eight** deprels — 543 `mark`, 145
`case`, 103 `advmod`, 10 `advcl`, 4 `ccomp`, 4 `obj`, 2 `obl`, 1 `cc` — and **four** Layer-2 tags.
Rule AR's gate admitted exactly one cell of that table, `mark` + conjunction, which is 441 rows.

Nothing in the reading turns on either column:

- *«ché, **come** sole in viso che più trema, **così** lo rimembrar del dolce riso … la mente mia
  … scema»* (paradiso 30:25) is rule AR's own correlative shape, with the marker written `advmod`
  and tagged an adverb;
- *«**Come** l'augello, intra l'amate fronde … **così** la donna mia stava eretta»* (23:1) is the
  same, and the Paradiso 21-25 batch had assigned this position to the **prompt**, as an instance
  of `_CONV_ADJUNCT`;
- *«com' a terra quïete in foco vivo»* (1:141) is the compared nominal's own marker, one deprel
  over from the `mark` branch rule BK widened.

Dropping both columns takes 3 positions and newly flags none. The transferable form: **a gate
that names a part of speech or a deprel is a claim about a column; check what the column actually
holds for the word before trusting it.** And its corollary, which this batch supplies for the
first time: **a position an earlier batch assigned to the prompt can be checker silence.** 23:10
was written up as prompt work three batches ago and cost nothing to recover, because a prompt
verdict is the one of the five that leaves no rule behind to be measured.

### The batch's second finding — a refusal beats a re-assignment, again

Rule EF is the shape of paradiso 29:31-35: *«Concreato fu **ordine** e costrutto a le sustanze …
**pura potenza** tenne la parte ima; / nel mezzo **strinse** potenza con atto»*. Five conjuncts
hang off `Concreato`; the fourth brings its own subject; the fifth was still being handed the
first one's, because `derive_unit`'s walk goes straight up the `conj` edge and never looks at what
the coordination has done in between. Rule AT decides *who* may inherit and rule DU where a
subordinator cuts the chain; this is the third question about the same walk — whether the chain
head is still the **nearest** antecedent.

The obvious repair is to hand the conjunct the nearer sibling's subject instead, and it is wrong:
measured at **+8/−2**. It is right at 29:35 and wrong at six other places, where the nearer subject
belongs to a clause the coordination does not continue. What is right is simply to **stop** — the
slot then falls to step 4's pro-drop ∅ and the authority model decides it, which is rule DA's
boundary read from the other side (*an empty subject slot is a decision procedure having
declined*, and declining is a decision). Measured at **−3/+1**, censused at 23 subject-less `conj`
predicates out of 3658, and correct at both positions it removes: inferno 33:61 (*«ed **ei** … di
sùbito levorsi / e **disser**»* — the sons say it, and the derivation was reaching past them to
`io`) and paradiso 29:35, where the two violations become one on a parse that no longer claims
`ordine` bound potency with act.

The **+1** is honest and is the trade rule AM recorded: with the false subject gone, the LLM's own
reading of `potenza` (35, 4) — which the tree calls a bare `obl` — is now reported as the one
disagreement it is, instead of being spread across a `missing_arg` and a `role_mismatch`.

### The batch's third finding — the last cell of a normalization

Rule EE is a single line of gate and it closes the 2026-08-14 multiword-preposition
normalization's last open cell. That normalization writes a cluster as *opening word* `case` →
nominal, *later members* `fixed` → opening word. Rule BV (Inferno 31-34) merges a cited `fixed`
member onto the nominal, on the reading that **a preposition's own words are not arguments**, and
explicitly declined to enter from a `case` row, because a plain `case` preposition is cited for
other reasons and rules L/N/O already read it. But the cluster's *opening* word is not a plain
preposition standing on its own — it is a preposition for the same reason its `fixed` members are,
and the exclusion never meant to cover it. *«Poscia che **'ncontro a** la vita presente … aperse
'l vero»* (paradiso 28:1): the LLM names `'ncontro`, Layer 4 opens the cluster on it, and the
nominal is `vita`. Censused at **167** `case` rows heading a multiword preposition, 1 of which the
LLM cites — a census of one for the divergence against a structural population of 167, kept for
the same reason rule CY was: **the two directions of one gate should not disagree.** Worth 2
positions, because the shape reports twice (a `missing_arg` on the nominal and an `extra_arg` on
the preposition).

### Rules EC and ED — the two halves rule AR had left

Both are legs of a rule that has now been extended in four batches, and both come from the same
observation: a verbless comparison has to hang **somewhere**, and Layer 4 has two choices.

**Rule EC** is the case where it hangs on the matrix predicate. *«ma or convien che mio seguir
**desista** / più dietro a sua bellezza, poetando, / **come a l'ultimo suo ciascuno artista**»*
(paradiso 30:31): the comparison is verbless, so Layer 4 puts both of its remnants — the oblique
`a l'ultimo suo` and the subject `ciascuno artista` — on `desista`. Two derived subjects is rule
BA's evidence that two clauses have been collapsed onto one head, and rule CW then drops the
elided clause's remnants **by position**: everything standing after the second subject. Here
Dante puts the second term's subject *last* and its oblique before it, so rule CW's test looks
straight past the remnant — the inversion the Purgatorio 26-30 batch already found in rule AN's
sort key. Rule EC reads the boundary off the one thing the tree does state about the gap: the
marker `come` opens the second term, so every argument after it belongs to it. Censused at 13
predicates carrying a correlative-less `come` marker and two or more subject children, against
598 with the marker alone.

**Rule ED** is the case where Layer 4 hangs the comparison on the `come` itself. *«E dal settimo
grado in giù, **sì come** infino ad esso, succedono Ebree»* (paradiso 32:16): `come` is an `advcl`
of `succedono` and carries `ad esso` as its own oblique, so `derive_unit` mints it as a predicate
and puts the adjunct there, while the LLM — reading the comparison as an adjunct of the matrix
verb, which is rule AR's own reading — lists it on `succedono`. One adjunct of comparison, named
once in each reading at the level that reading gives it. Routed through rule X's mechanism, so it
inherits the role-must-match gate, and restricted to a host whose own word is the marker: that is
what makes it a marker standing in for a clause rather than a clause of its own. Structural census
14 (`come` in a clause-head deprel).

### Candidates censused and dropped

- **The participial adjunct's subject, named by the Layer-3 span that contains it** (paradiso
  28:20, *«parrebbe **luna, locata con esso**»* — Layer 3 makes `luna, locata con esso` one phrase
  headed by `luna`, so `locata` is a reduced relative on `luna` and `luna` is its subject, which is
  rule AY's reading with Layer 3 supplying the modification edge Layer 4 wrote as `advcl`).
  Censused at **8** `advcl` rows lying inside an NP span whose head is an argument of their own
  governor, of which 1 diverges — and dropped on the Inferno 31-34 batch's precedent, which
  declined rule BR's mirror leg at −6/+0 because **its only evidence was a Layer-3 span and Layer
  3 is over-inclusive by design**. That is exactly the evidence here.
- **The causee of a causative `fare` + infinitive, `obj` against `iobj`** (paradiso 33:96, *«che
  fé **Nettuno** ammirar l'ombra d'Argo»*). Censused at **16** predicates with an `xcomp`
  infinitive and an `iobj` of their own; 15 of the 16 are clitics and only this one is a full
  nominal. Dropped on the grammar rather than the count: Italian codes the causee of a *transitive*
  infinitive as a dative (*far ammirare qualcosa **a** qualcuno*), which is what Layer 4 wrote, so
  the LLM's `obj` is a second claim about the role — the DX-EA batch's finding, applied to a
  construction the corpus already has a rule for on the other side (rule BI).
- **Handing a `conj` the nearer sibling's subject** instead of stopping — rule EF's own
  re-assignment variant, measured at **+8/−2** and rejected. See the second finding above.

### Standing shapes the batch recorded but did not settle

- **The elided-verb `csubj` the LLM omits** (26:27, *«cotale amor **convien** che in me si
  'mprenti»*): Layer 4 writes the `che`-clause as `convien`'s `csubj` and the derivation says so;
  the LLM gives `convien` its two obliques and no subject at all. Rule DQ's family — but rule DQ
  accepts an *inherited* subject against a lone `ccomp`, and here the subject is the tree's own
  and the omission is the LLM's.
- **The prepositional adjunct, omitted** (26:29 *«in quanto ben»*, 28:73 *«non a la parvenza»*,
  30:13 *«a poco a poco»*). Three more instances of `_CONV_ADJUNCT`/`_CONV_REPEATED`, both already
  written into `skel/skel.py` and both waiting on the sixth round. Two of the three are a *second*
  filler of a slot the LLM did name once, which is `_CONV_REPEATED`'s target.
- **The relative temporal `che` read as an object** (27:79, *«Da l'ora **ch'**ïo avea guardato
  prima»*): Layer 4 gives the relative link an `obl`, the LLM calls it the participle's `obj`. Rule
  BM's shape with the roles swapped — a second claim about the slot, not checker silence.
- **The comparative `che` the LLM reads as an argument** (26:79, *«onde mei **che** dinanzi vidi
  poi»*). The Layer-2 rows that made the misreading available are corrected below; the citation
  itself is reading error and stays flagged.
- **`missing_arg subj` residue** (29:137 *«per tanti modi in essa **si recepe**»*, the LLM reading
  the reflexive passive as impersonal; 32:150 *«**lo cor** non parti»*, the LLM reading the object
  as a subject).
- **The subjective genitive of a nominalized infinitive** (31:19, *«né l'**interporsi** … **di
  tanta moltitudine volante**»*): with the genitive re-attached to the infinitive below, the LLM's
  reading of it as that infinitive's subject is still not something the derivation produces. Rule
  V's neighbourhood; not censused.

## Rules DX-EA, from reading Paradiso 21-25 — 245 → 234, −11 (2026-08-17)

Per-position read of all **21** soft violations in Paradiso 21-25, following the eight-step
procedure in [`PLAN.md`](PLAN.md)'s *How to Read a Batch*. Zero model calls. Paradiso 21-25 itself
went **21 → 11** (21: 8 → 6, 22: 2 → 2, 23: 5 → 2, 24: 4 → 0, 25: 2 → 1); the corpus went
**245 → 234 (−11, −4.5%)**. Four deterministic Layer-5 rules, 10 Layer-4 rows, 1 Layer-2 row and
1 Layer-3 span. `pytest` **483 passed**, 0 hard, all other layers 0/0.

| rule | shape | census | net |
|---|---|---:|---:|
| **DX** (`_predicative_advmod`) | rule R's **noun** leg: the depictive nominal Layer 4 hangs `advmod` on the predicate, which rule CP already reads off a bare `obl` | 52 | −1 |
| **DY** (`_relative_adverb_oblique`) | rule DD's POS gate read as the reason it states: the relative locative is `onde` whatever of its four tags Layer 2 gave the row | 32 | −2 |
| **DZ** (`_conjunct_named_by_phrase_head`) | rule AI's NP-head equivalence read **through** rule C's coordination collapse | 85 | −2 |
| **EA** (`speech_act_nominal`) | the elided speech verb Layer 4 records as a `parataxis` on a bare pronoun, whose whole derived tuple is a lone ∅ subject | 4 | −1 |

Plus the upstream rows, **−6/+1** between them (counted below).

### The batch's finding — the same construction, twice, decides a widening against itself

The candidate that did **not** land is the one worth writing down, for the second batch running.
Paradiso 21:5 (*«tu ti faresti **quale** / fu Semelè»*) is rule CX's shape: the derivation cites
the comparative clause by its verb (`fu`), the LLM cites the `quale` that opens it, and the only
thing stopping rule CX is its role gate — the derivation calls the clause an `obl` and the LLM
calls the word an `attr`. Widening `_COMPLEMENT_ROLES` to admit `obl` is the obvious next step,
and it takes the position.

It is wrong, and what shows it is the corpus's own second instance of the construction. Paradiso
23:14 — *«fecimi **qual** è quei che disïando altro vorria»* — is the identical line: a reflexive
`fare` with a `quale` comparative complement, and Layer 4 wrote it the same way (`qual` `xcomp` on
`è`, `è` `obl` on `fecimi`). That position is **already accepted**, by rule DJ, because there the
LLM also said `obl` and the two sides agreed about the slot. So Layer 4's `obl` is a convention it
applies consistently to this construction, and the divergence at 21:5 is the LLM claiming a
complement where the tree asserts an adjunct — a second claim about the role, which is exactly
what rule CX's gate exists to keep out. **A candidate that a rule's role gate blocks should be
priced against the corpus's other instances of the same construction, not against the line that
prompted it**: here the other instance is not new evidence for the widening, it is the evidence
against it. 21:5 stays flagged.

### The four rules

- **Rule DX — rule R's noun leg** (`_predicative_advmod`). *«ov' io **dormi' agnello**»* (paradiso
  25:5): a depictive predicated of the subject, which Layer 4 hangs `advmod` on the verb. Rule R
  has taken exactly this shape since Phase 5, for an *adjective*, and its docstring justifies the
  POS gate against **adverbs** — "which leaves the reading genuinely undecided" — and never
  considers a nominal. Its two siblings already do: rule BC accepts a noun in this very deprel
  when the given role is `obl`, and rules AZ/CP accept adjective *and* noun when the deprel is a
  caseless `obl`. Censused at **52** noun `advmod` rows, of which one is a depictive and the rest
  are the adverbial quantifiers and accusatives (`poco` 25, `fin` 7, `pena` 5, `tutto` 4, `volta`,
  `passo`, `giorno`). That is the shape of census rule CP landed on and for the same reason: the
  acceptance is not the census, because it fires only where the LLM independently read the token
  as this predicate's complement, which *«un poco avante»* does not attract. The pronoun leg stays
  declined, as it is in rule AZ.
- **Rule DY — a POS gate read for the reason its docstring states** (`_relative_adverb_oblique`).
  *«lo cibo **onde** li pasca»* (paradiso 23:5): the relative locative Layer 4 writes as a `case`
  on its own clause's verb, which rule DD settled for `dove`/`ove` at census 21. The gate DD
  carries is "Layer 2 must call the word an adverb", and its stated purpose is to separate a
  relative locative from a real preposition. `onde` is a relative locative by any grammar and
  Layer 2 tags it **four** ways across the corpus — 111 conjunction, 79 pronoun, 49 adverb, 17
  relative pronoun — with the same `obl` deprel under each; which tag a row got is the lottery
  rule DT refused to let a normalization depend on. So the gate now also admits the three locative
  **lemmas** themselves. Lemma, not word, is what separates `onde` "whence" from `onda` "wave"
  (11 rows share the surface form). Of the **32** `case`-on-a-verb rows those lemmas hold, 28 were
  already adverbs; the rule adds paradiso 23:5 and 33:135 (*«quel principio **ond'** elli
  indige»*). The `che`/`fin`/`secondo` rows in the same structural position stay out — those are
  complementizers and nouns, rule BW/CK's question, not this one.
- **Rule DZ — rule AI through rule C** (`_conjunct_named_by_phrase_head`). *«Or voglion quinci e
  quindi **chi rincalzi** / li moderni pastori e **chi li meni**, / … e **chi di rietro li alzi**»*
  (paradiso 21:130): three free relatives in one object slot. Layer 4 heads each on its own
  subjunctive and coordinates the second and third onto the first, so rule C collapses the
  derivation's three citations onto the coordination head; the LLM names each clause by the `chi`
  that opens it, which Layer 3 confirms is that clause's phrase head. **The first of the three was
  already accepted** — by rule AI, because `chi` and `rincalzi` share a line and the NP-head merge
  is a same-line test. The other two are the same citation convention one `conj` edge further out,
  and nothing reached them, because by the time rule AI fires the collapse has already run. This
  is the *«which normalization has already run on the citation»* question (rules CD, CI, DT) in
  its composed form: two normalizations that are each the corpus's own, and the shape that needs
  both. The structural pattern — a Layer-3 span holding a `conj` whose head lies outside it — is
  censused at **85**. Gated on rule AI's own test, that the cited token is the span's *head*, and
  on the role matching.
- **Rule EA — the elided speech verb, on the derivation's side** (`speech_act_nominal`). *«Ed
  **ella**: «O luce etterna del gran viro … tenta costui»»* (paradiso 24:34): the speech verb is
  gapped and Layer 4 hangs the speaker on the quotation with `parataxis`, a clause-head deprel, so
  `derive_unit` promotes the pronoun to a predicate. Nothing then attaches to it — the whole tuple
  is the `subj=(0, 0)` rule M's pro-drop relabelling leaves behind, which asserts a dropped
  subject and nothing whatever about any other slot. The LLM reads the ellipsis for what it is and
  gives the elided verb the quotation as its `ccomp`, and the derivation does not contradict that,
  because it made no claim there. This is **rule DA's boundary read one step in**: DA silences a
  role-less derived row outside the subject slot, and a tuple whose only row is a ∅ subject names
  no argument either. It is deliberately **not** widened to that shape in general — **720** tuples
  corpus-wide are a lone ∅ subject, and rule CS's own +180 measurement is what they are, copular
  and controlled predicates whose subject comes from rule V and whose complements the LLM proposes
  correctly. What is gated is Layer 4's own record of the ellipsis, a `parataxis` on a **non-verb**,
  censused at exactly **4** rows corpus-wide (purgatorio 4:127 *«Ed elli»*, 18:10 *«E io»*,
  paradiso 24:34 *«Ed ella»*, 24:91 *«E io»*) — the same speech-act pronoun each time.
  Kept as an acceptance rather than as a refusal to mint the predicate: rules AN/BN/CA's move
  would turn the LLM's *correct* reading into an `extra_tuple`, which is the trade rule BN records
  running the other way, where the LLM was wrong.

### Upstream rows — Layer 4 ×10, Layer 2 ×1, Layer 3 ×1 (−6/+1)

Applied with a gated script that asserts the word at each `(line, token)` before rewriting; all
four upstream checks stay 0 and `pytest` passes. See [`../dep/CORRECTIONS.md`](../dep/CORRECTIONS.md),
[`../morph/CORRECTIONS.md`](../morph/CORRECTIONS.md), [`../np/CORRECTIONS.md`](../np/CORRECTIONS.md).

- **paradiso 21:28** *«di color d'oro **in che** raggio traluce»* — `che` is the relative pronoun
  `in` governs, antecedent `color d'oro` ("gold colour in which a ray shines through"). Layer 4
  read it as a determiner of `raggio` ("in which ray"). Retagged `det`→`obl` on the clause's verb,
  and the Layer-3 span `[che raggio]` dropped, Layer 3's own scope rule keeping bare relative
  pronouns out of noun phrases (`[raggio]` was already there). **This correction costs +1**: the
  two violations it removes are replaced by three, because with the tree right the LLM's own
  misreading — `raggio` as the oblique and a ∅ subject — is now fully reported. The honest trade
  the series has recorded since rule AM; the count is not the measure.
- **paradiso 21:105** *«a dimandarla umilmente **chi** fue»* — the indirect question is
  `dimandare`'s second object, not a predicative complement. `attr` on a non-copular verb is
  censused at **1** row corpus-wide, this one; the other 447 sit on `essere` (351), `fare` (32),
  `parere`, `chiamare`, `tenere`, `rendere` and the rest of the predicative verbs. `attr`→`obj`.
- **paradiso 23:17** *«Ma poco fu tra uno e altro quando, / **del mio attender**, dico, e del
  vedere / lo ciel venir più e più rischiarando»* — the parenthetical gloss says what the two
  moments were, so it belongs to the interval `fu` states, not to the brightening; `dico`, which
  marks the gloss, is already `parataxis` on `fu`. `attender` re-attached from `rischiarando` to
  `fu`. Two violations, one at each end of the pair.
- **paradiso 24:19** *«**Di quella** ch'io notai **di più carezza** / vid' ïo uscire un foco»* —
  two prepositional phrases, one inside the other's relative clause. Layer 4 made `quella` a
  determiner of `carezza` *across* the relative clause and split "di più carezza" in half. Line 21
  has the parallel phrase (*«nullo vi lasciò **di più chiarezza**»*) parsed right, which is what
  decides it. Six rows.
- **paradiso 24:147** *«quest' è la favilla / che si dilata in fiamma poi vivace, / e come stella
  in cielo in me **scintilla**»* — the second verb of the relative clause, coordinate with `dilata`
  and sharing its subject `che`, not a conjunct of the noun `favilla`. Re-headed onto `dilata`;
  the derivation then propagates `che` and both violations go.
- **paradiso 22:21** (Layer 2) *«se com' io dico l'aspetto **redui**»* — `redui` is the 2sg present
  of *reddure* ("riduci, rivolgi"), not an adjective. Layer 4 already heads a clause on it and
  gives it `l'aspetto` as an object. Retagged, which does not move the count: the artifact is
  frozen and the LLM's omission of the predicate stays reported until a `--fix` round re-reads it.

### Candidates censused and dropped

- **Rule CX's role gate widened to `obl`** — the batch's finding, above. Refuted by paradiso 23:14,
  the corpus's other instance of the same construction.
- **A derived tuple that is a lone ∅ subject, in general** — measured as a population rather than
  as a rule: **720** corpus-wide, 133 of them on non-verbs, and rule CS's own +180 measurement
  says what they are. Rule EA takes the 4 that are Layer 4's record of an ellipsis and nothing
  else.

### Standing shapes the batch recorded but did not settle

- **The prepositional adjunct and the dative clitic** — the two clauses already written for the
  sixth round, with two more instances each. 23:7 (*«previene il tempo»*, `la notte` omitted) and
  23:10 (the *«Come l'augello …»* simile's own nominal, omitted) are `_CONV_ADJUNCT`'s target;
  25:61 (*«ché non **li** saran forti»*, the dative of the person concerned read as the subject) is
  `_CONV_DATIVE`'s, and is its second instance after the three the 11-20 batch found. **No new
  prompt candidate came out of this batch**, which is now true of four of the five Paradiso
  batches.
- **The comparison's second term in a role other than `obl`** (22:79, *«grave usura tanto non si
  tolle … **quanto quel frutto**»*, given `obj`). The same standing shape the 11-20 batch recorded
  at 15:102 and 16:59; rule AR's role gate is still the obvious widening and still uncensused.
- **The right referent named by the wrong token** (21:23, *«quanto m'era a grato / ubidire»*: the
  infinitive's controller is the dative `m'`, and the LLM cites the `io` two lines up that means
  the same person). Accepting it would need coreference, which *Out of scope* rejects; supplying
  the controller in rule V would leave the position flagged anyway.
- **Genuine LLM misreadings, left flagged**: 21:54 (the determiner of the nominalized infinitive
  `'l chieder` cited as its object), 21:28 (above), 22:79 (above).

## Rules DS-DW, from reading Paradiso 11-20 — 261 → 245, −16 (2026-08-17)

Per-position read of all **43** soft violations in Paradiso 11-20 — **two** batches of the
Paradiso series in one session — following the eight-step procedure in [`PLAN.md`](PLAN.md)'s
*How to Read a Batch*. Zero model calls. Paradiso 11-20 itself went **43 → 30** (11: 5 → 7,
12: 6 → 5, 13: 4 → 2, 14: 6 → 4, 15: 7 → 5, 16: 6 → 1, 17: 4 → 3, 18: 1 → 1, 19: 3 → 1,
20: 1 → 1); the corpus went **261 → 245 (−16, −6.1%)**. Five deterministic Layer-5 rules,
9 Layer-4 rows, 1 Layer-2 row, and the sixth round's queued prompt clause finally written.
`pytest` **475 passed**, 0 hard, all other layers 0/0.

| rule | shape | census | net |
|---|---|---:|---:|
| **DU** (`derive_unit` step 3) | the shared-subject propagation across `conj` **stops at a conjunct Layer 4 marks with its own subordinator** — a marked clause is subordinate, not coordinate | 49 | **−8/+1** |
| **DW** (`_depictive_attr_omitted`) | rule BX's `attr` leg: the depictive Layer 4 wrote in the complement slot rather than loose as an `obl` | 100 | −2 |
| **DS** (membership check) | rule BW, applied where the citation is still raw: the interrogative `mark` that opens a clause and fills one of its slots | 325 | −1 |
| **DT** (`_coordination_head`) | `compound` collapses onto its head like `flat` (rule BE) — the same nominal spread over two tokens | 2 | −1 |
| **DV** (`_stranded_on_underived_complement`) | rule CB read through rule AU's host: the oblique stranded on an `amod` adjective over one of the predicate's own arguments | 119 | −1 |

Plus the upstream rows, **−9/+5** between them (counted below).

### The batch's finding — a rule can measure −3/+0 and still be wrong

The candidate that did **not** land is the one worth writing down. Rule DQ (Paradiso 6-10) accepts
an impersonal verb's inherited subject when the only other thing the derivation gives that
predicate is a `ccomp`; paradiso 14:49 (*«onde la visïon crescer convene»*) is the identical
reading with an `xcomp` instead, so widening DQ's gate to `{"ccomp"} | {"xcomp"}` is the obvious
next step. It measures **−3/+0** — net negative, nothing newly flagged, exactly the profile every
kept rule in this series has.

It is wrong. Reading the three positions it removes: purgatorio 20:151 (*«così m'andava timido e
pensoso»*, a `conj` of `potea` whose 1sg subject genuinely is the inherited one) and purgatorio
25:49 (*«e, giunto lui, comincia ad operare»*) are **control** verbs, not impersonal ones, and
their inherited subject is correct — the rule buys its −2 by suppressing two true reports. That is
precisely the boundary the Paradiso 1-5 batch censused and refused on the corpus's own scope rule:
telling `convien` from `puote` in the `xcomp` frame needs a verb-valency lexicon. A `ccomp` gate is
structural because a `che`-clause under a subjectless verb *is* that verb's subject; an `xcomp`
gate is lexical wearing a structural costume.

So: **measure by violation diff, and then read what the diff removed.** Nine rule batches have
banked "net negative, nothing newly flagged" as the acceptance test; this is the first position
where that test passes on a rule that makes the parse worse. The count is not the measure.

What did take paradiso 14:49 — and inferno 20:57, and four of the five 16:55 positions — is rule
DU, which asks a structural question about the same shape: *is this conjunct subordinate?* The
`onde` in *«onde la visïon crescer convene»*, the `che` in *«che averle dentro»*, the `onde` in
*«onde un poco mi piace»* are all `mark` children Layer 4 wrote on a `conj`, and a clause with its
own subordinator is not the second half of a coordination. UD's shared-subject convention is about
coordination; nothing licenses reading it across a subordinator. Censused at 49 `conj` verbs with
no subject of their own that carry a `mark`.

### Rule DU's one new position is a correctness trade

Purgatorio 21:80 (*«e perché tanti secoli giaciuto qui se'»*) rises by 1. The derivation used to
hand `giaciuto` the subject of *«Ora chi fosti»* — `chi` — and the LLM listed **both** `chi` and ∅
in the slot, so one of the two matched and rule CU absorbed the other. With the propagation stopped
the derivation says ∅, which is right (`se'` is 2sg, the addressee), the LLM's ∅ matches it, and
the LLM's `chi` is now reported. The wrong tree had been matching an LLM misreading; the count
records that honestly.

### Rules DS and DT are both "which check runs first"

Rule BW's own docstring cites paradiso 19:74 (*«sappiendo … quanto costa»*) as one of its three
evidence lines — and that position was still flagged, because the **membership** check runs before
`_classify_divergence` and rejected `quanto` as heading no NP, pronoun or predicate. The rule
written for the line never saw the line. This is the third time the same finding has landed (rule
AQ′ for the `aux` merge, rule DG for rule C's collapse), and the membership check now consults rule
BW with rule BW's own gates unchanged.

Rule DT is the same question about a normalization rather than a rule: `_coordination_head` walks
`conj`, `appos` and `flat`, and Layer 4 writes *«un Lapo Salterello»* with `compound`. Its census
is **2** rows corpus-wide — below the bar this series has dropped candidates at — and it is kept
anyway, on rule BZ's ground: it is rule BE's reasoning verbatim (a multiword name is one nominal,
and citing any of its tokens cites it), it measured −1/+0, and leaving it out means the collapse
depends on which of two interchangeable deprels Layer 4 happened to pick.

### The sixth `--fix` round's queued clause is now written

`_CONV_ADJUNCT` in [`skel.py`](skel.py) — the prepositional adjunct of time, place, source or
manner, proposed by the Purgatorio 16-20 read and unwritten through two rounds. Its target,
`missing_arg obl*`, is **56 of 245** after this batch (bare `obl` 17) and is still the residue's
largest single bucket; four of this batch's own positions are instances (12:10 *«a guisa del parlar
di quella vaga»*, 13:44 the second of two coordinate `in quel che` obliques, 15:20 *«dal corno che
'n destro si stende»*, 18:51 *«tra i cantor del cielo»*).

A second clause, `_CONV_DATIVE`, is this batch's own prompt finding: three positions (17:102
*«ch'io **le** porsi ordita»*, 17:110 *«se loco **m'**è tolto»*, 20:35 *«l'occhio in testa **mi**
scintilla»*) are a non-core dative clitic — the dative of the person concerned — that Layer 4
records and the reading drops as a particle. Both hang on the generic `missing_arg` class, and they
are separable in a round's subclass table because the dative surfaces as `missing_arg obl:a`.
Neither moves anything until a round runs.

### Candidates censused and dropped

- **Rule DQ widened to `xcomp`** — measured **−3/+0** and dropped. See *The batch's finding* above.
- **Binding Principle B on the `conj` subject propagation** (paradiso 16:55, *«che averle
  dentro»*, where the fused accusative clitic `le` cannot be coreferent with the subject it would
  inherit). Censused at **46** subjectless `conj` verbs carrying a fused non-reflexive accusative
  clitic, of which **3** agree with the candidate subject in gender and number — and two of those
  three (purgatorio 7:15 *«abbracciòl»*, 32:158 *«trassel»*) are *«he embraced him»*, where subject
  and object simply share m.sg. Agreement is not coreference; the rule would have broken two
  correct derivations to fix one. Rule DU takes 16:55 by a structural question instead.
- **The relative pronoun Layer 4 writes as a `case` on the nominal it relativizes** (11:21,
  *«li tuoi pensieri **onde** cagioni apprendo»*, where the derivation cites `pensieri` with role
  `obl:onde` and the LLM cites `onde` with role `obl:di`). Censused at **7** pronoun-POS `case`
  rows corpus-wide, of which only this one is a relative pronoun — the rest are prepositions Layer
  2 mistagged (`lunghesso`, `ne`). Not a population.

### Standing shapes the batch recorded but did not settle

- **The prepositional adjunct, and the dative clitic** — now prompt candidates, above. Also 14:56
  (*«sì come carbon che fiamma rende»*, the comparandum), 15:32 (*«Così quel lume»*, the nominal of
  an elided verb of speech parked as a bare `obl` on the following root).
- **The LLM listing one argument on two predicates** (12:27 `chiudere` given `li occhi` as both
  `subj` and `obj`; 13:1 the object of the embedded `intender` also given to the matrix `Imagini`;
  15:55 *«da quel ch'è primo»* given to both `mei` and `raia`). Four positions across the batch,
  and no gate yet that says which of the two listings the derivation should be compared against.
- **The quoted exclamation named by its own relative verb** (14:96, *«ch'io dissi: “O Elïòs che sì
  li addobbi!”»*: Layer 4 makes the vocative `Elïòs` the object of `dissi`, the LLM names
  `addobbi`, the verb inside it). Rule BR's shape with the containment reversed; the
  `parataxis`→`ccomp` route the Inferno 8:81 note has queued since the 26-30 batch.
- **`obj` against a derived `xcomp` on an infinitive complement** (14:92, *«ch'io conobbi esso
  litare stato accetto»*): Layer 3 draws an NP round `esso litare`, which is what makes `obj` the
  LLM's natural label. Not censused.
- **The comparison's second term in a role other than `obl`** (15:102, *«più che la persona»*;
  16:59, *«ma come madre a suo figlio benigna»*). Rule AR's role gate is the obvious widening and
  neither line reaches it — 15:102's `che` is already `case`, and 16:59's `madre` is an `attr`.
- **Genuine LLM misreadings, left flagged**: 11:129 (`tornano`'s subject is `le sue pecore`, not
  the coordination head's `pecuglio`), 12:124 (`fia`'s subject is `carta`, and the LLM names none),
  17:116 (the relative `che` given to the `advcl` inside its own clause), 19:63 (*«ma cela lui
  l'esser profondo»* read with subject and object swapped).

## Rules DK-DR, from reading Paradiso 6-10 — 288 → 261, −27 (2026-08-17)

Per-position read of all **18** soft violations in Paradiso 6-10, the second batch of the Paradiso
series, following the eight-step procedure in [`PLAN.md`](PLAN.md)'s *How to Read a Batch*. Zero
model calls. Paradiso 6-10 itself went **18 → 6** (6: 0 → 0, 7: 7 → 4, 8: 5 → 1, 9: 5 → 1,
10: 1 → 0); the corpus went **288 → 261 (−27, −9.4%)**. Eight deterministic Layer-5 rules, 10
Layer-4 rows, 2 Layer-2 rows and 2 case-annex rows. `pytest` **465 passed**, 0 hard, all other
layers 0/0.

| rule | shape | census | net |
|---|---|---:|---:|
| **DO** | rule AG's agreement test asked of the two **predicates**: two finite verbs sharing a subject must agree with each other | 30 / 1151 | −5 |
| **DQ** | the impersonal verb whose subject is its own `che`-clause, reached without a valency lexicon | 217 | −5 |
| **DL** | rule DB's part-of-speech gate dropped: a copula's *sole* complement is its predicate complement whatever it is made of | 414 / 492 | −5 |
| **DP** | the relative clause with **no relativizer at all**, whose head noun the derivation therefore never cites | 474 / 3261 | −3 |
| **DK** | the antecedent, where the derivation names that clause's own relative pronoun | 2574 / 3261 | −2 |
| **DR** | `quasi` is the third marker of rule AR's verbless comparison, written `advmod` | 9 / 52 | −2 |
| **DM** | rule AK's gate read as the negative its own docstring states: *no layer calls the particle a preposition* | 33 / 150 | −1 |
| **DN** | the subject Layer 4 writes inside a periphrasis, on the `xcomp` infinitive rather than the modal | 106 / 1130 | −1 |

Plus the upstream rows (**−3** between them, counted below).

### The batch's finding — a rule's docstring can be more correct than its code

Two of the eight rules are one defect, and it is the sharpest thing the batch has to say. Rule DB
accepts a copula's prepositional complement as its predicate complement, and its docstring names
the deciding gate outright: *"the copula must have no other complement … `essere` with none is
predicating **this** phrase or nothing."* The code carried that test **and** a second one — the
complement must be an `advmod`-turned-`obl` **adverb** — inherited unexamined from rule AD, where
it is load-bearing, and from the single line that motivated rule DB. Nothing in the reasoning needs
it. Dropping it (rule DL) takes five positions across four cantos and three canticles: "tal ch'**è
da sermone**" (8:147), "elli **era d'alte lode**" (14:124), "**sarebbe a maraviglia**" (19:84),
"l'uso d'i mortali **è come fronda** in ramo" (26:137), "quando **saranno più presso** a noi"
(inferno 5:76).

Rule AK is the identical story one rule over. Its docstring explains that Layer 4's `case` edge
mints `obl:come` *"out of a token no layer calls a preposition"* — and then gates on Layer 2
calling it a **conjunction**, which is only what the evidence line happened to carry. The census
says 150 comparative particles sit in a `case` slot and just 117 are tagged that way: `come`/`com'`
is an **adverb** 24 times, and `qual` — the other particle of the same construction — is an
adjective or a pronoun 5 times ("mi si fece in vista **qual fin balasso**", 9:68). Rule DM makes the
gate the negative one the docstring already describes.

**So: when a rule fires, read its stated reason and ask which of its conditions that reason
actually requires.** The Purgatorio 26-30 batch found this defect with the polarity reversed —
rule AN's comment described an ordering its sort key did not implement — and the pair is worth
holding together. A prose reason and a code gate that disagree is a finding either way; the
question is only which of the two is right, and it is decided by census, not by which came first.

### Three more

**1. A scope refusal is about the instrument, not the shape.** The Paradiso 1-5 batch censused the
impersonal-verb reading at 29 and dropped it on the corpus's own scope boundary: telling `convien`
from `puote` needs a list of impersonal verbs, which is [`../PLAN.md`](../PLAN.md)'s *Out of
scope* by another name. Rule DQ takes five positions of that same family without any list, because
it stops trying to classify the verb. Its two gates are both structural: the derivation's subject
must be **inherited** across `conj` (so nothing in the predicate's own clause was ever a
candidate), and the only other thing derived for it must be a `ccomp`. A verb with a clausal
complement and no subject anywhere in its own clause has that clause as its subject on every
reading of "**convien** che caggia" (7:78), "**par** ch'abbia" / "**par** che pregi" (inferno
14:69, 14:70), "**avvegna** che si rauni" (16:131), "**convien** ch'io desista" (30:31). The
earlier refusal was correct about the instrument it was offered and says nothing about the shape.

**2. Check a rule's test against *both* ends of the relation it is about.** Rule AG drops a
`conj`-inherited subject whose Layer-2 person/number contradicts the predicate it lands on — the
nominal against the recipient. It never compares the **donor** predicate with the recipient, and
that comparison is decidable in cases where the first is not: a third-person noun agrees with every
third-person verb. "Cunizza fui chiamata … a me medesma **indulgo** la cagion di mia sorte, e non
mi **noia**" (9:35) walks a chain of 1sg verbs onto a 3sg one; whoever vexes is not whoever
forgives. Censused: of 1151 inheritance candidates, rule AG says *disagree* for 232 and rule DO
adds **30** — 25 where rule AG is undecidable and 5 where it actively says *agree*, which are
exactly the cases where the inherited nominal has no person of its own to contradict with. Five
positions, and every one of the five reads correctly (inferno 6:87, paradiso 3:61, 9:35 ×2).

**3. The same reading is right as an acceptance and wrong as an assertion — again.** Rule DN began
in `derive_unit`: if a predicate has no subject of its own and its `xcomp` infinitive carries an
overt `nsubj`, mint that as the predicate's subject (raising). Measured **−4 / +40**. An overt
subject under an `xcomp` is far more often the accusative-and-infinitive's own than a raised one,
and asserting it overrode 24 pro-drop ∅ subjects the LLM reads correctly. Moved to
`_classify_divergence` as an acceptance the same evidence is decisive without deciding anything —
−1 / +0. This is the Purgatorio 16-20 batch's rule-CS finding (its `derive_unit` variant measured
+180) in a second instance, and it is now a standing question: **before writing a rule into the
derivation, price it as an acceptance.**

### The upstream rows

Ten Layer-4 rows, 2 Layer-2 rows and 2 case-annex rows, applied by a gated script that asserts the word — and the old cell value — at every
`(line, token)` before rewriting; see
[`../dep/CORRECTIONS.md`](../dep/CORRECTIONS.md), [`../morph/CORRECTIONS.md`](../morph/CORRECTIONS.md)
and [`../case/CORRECTIONS.md`](../case/CORRECTIONS.md). Net **−3**, and the gross is the more
honest number: two of the four corrections are net zero because they expose an LLM misreading the
wrong tree had been matching.

- **7:75, −2.** "ché l'ardor santo … **ne la più somigliante** è più vivace": Layer 4 hung the
  preposition `ne` on `ardor`, three tokens to its left and across a line break, making the
  adjective inside the prepositional phrase the subject. `ardor` is the subject and `la più
  somigliante` the oblique, which is what the LLM read.
- **7:142, ±0.** "ma vostra vita … **spira** / la somma beninanza": the supreme beneficence
  breathes forth your life, not the reverse. Two `role_mismatch` positions go and two new ones
  appear one line down, where the LLM gives `innamora` the subject it had wrongly agreed with the
  tree about.
- **9:135, ±0.** "sì che pare **a' lor vivagni**": one prepositional phrase, which is how Layer 3
  already read it (`NP [6-8] head=8`). Layer 4 had `a'` governing `lor` alone, `lor` a dative
  oblique and `vivagni` an `xcomp` of `pare`. `lor` is the possessive adjective (Layer 2 retagged,
  and its `dative` case-annex row dropped — 114 of the corpus's `lor` rows are already
  `det:poss`), `vivagni` the oblique. The `role_mismatch` is replaced by an `extra_tuple`: the
  LLM's own row for `vivagni` as a predicate, which only the wrong tree supported.
- **9:87, −1.** "là dove l'orizzonte pria **far suole**": `suole` is the modal and `far` the
  lexical verb, so `far` is its `xcomp`, not its `aux`. Layer 4 writes `solere` as a clause head
  with a complement 23 times and as an `aux` 18; `fare` is an `aux` only in the causative ("il fé
  far", purgatorio 5:77), which this is not.
- **10:147, ±0 on its own, and it is what rule DK had to be written through.** "e in **dolcezza**
  **ch'** esser non pò nota": `ch'` is the relative pronoun (Layer 2 called it a conjunction; a
  `nominative` case-annex row added), and the clause modifies `dolcezza`, the conjunct it follows,
  not the coordination head `tempra`. Correcting the attachment moved the antecedent *off* the
  position rule C's collapse rewrites the LLM's citation to — so rule DK reads the antecedent
  through `_coordination_head` as well, which the uncorrected tree would never have shown.

### Candidates measured and dropped

- **Rule DN in `derive_unit`** — **−4 / +40**, see finding 3.
- **Rule DP without the relativizer gate.** The first form asked only whether the clause had a
  *relative pronoun* (rules CE/DC/DK's four words). It accepted "che di tutte altre cose **qual**
  mi torse" (purgatorio 31:86) wrongly: `qual` relativizes the clause, and the partitive the LLM
  adds to it is genuinely the main clause's. The fix is a **wider** word list used **negatively** —
  every word this corpus relativizes with, refusing the rule rather than licensing it. Found by
  the violation diff, not by census: the census counts the population, the diff names the boundary.
- **Rule DP without the complement-role gate.** The second form broke two existing near-miss
  tests (rule BT's), which were right: an `acl:relcl` head standing as its clause's *predicate
  complement* is the free-relative shape rules AE and BT adjudicate on their own evidence, and a
  correlative antecedent ("**colui** che …") is emphatically not one. Restricted to the non-
  complement roles, all 465 tests pass. Second batch running in which a broken near-miss test
  located a gate rather than condemning a rule.

### What the batch left standing (6)

- **7:25 ×2** — "Per non soffrire a la virtù che vole / freno a suo prode": Layer 4 hangs `a la
  virtù` on the noun `freno` and gives `vole` no object; the LLM raises the dative to `soffrire`
  and makes `freno` the object of `vole`. Both are readings of a genuinely tangled line and the
  text does not decide between them.
- **7:143 ×2** — created by the 7:142 correction above: the LLM's subject for `innamora`, which
  the wrong tree had been agreeing with.
- **8:12** — "che 'l sol vagheggia or **da coppa** or **da ciglio**", the LLM omitting the
  oblique entirely. The residue's largest bucket (`missing_arg obl*`, now **57 of 261**) and the
  sixth `--fix` round's one queued prompt candidate, still unwritten.
- **9:135** — the `extra_tuple` the 9:135 correction exposed, above.

## Rules DG-DJ, from reading Paradiso 1-5 — 298 → 288, −10 (2026-08-17)

Per-position read of all **26** soft violations in Paradiso 1-5, the first batch of the Paradiso
series, following the eight-step procedure in [`PLAN.md`](PLAN.md)'s *How to Read a Batch*. Zero
model calls. Paradiso 1-5 itself went **26 → 18** (1: 11 → 10, 2: 2 → 0, 3: 5 → 4, 4: 4 → 2,
5: 4 → 2); the corpus went **298 → 288 (−10, −3.4%)**. Four deterministic Layer-5 rules, 6
Layer-4 rows, 1 Layer-2 row, 1 Layer-3 span and 2 case-annex rows. `pytest` **449 passed**, 0
hard, all other layers 0/0.

| rule | shape | census | net |
|---|---|---:|---:|
| **DJ** | rule CX's complement-role gate dropped where the two sides name the **same** role | 28 | −3 |
| **DI** | rule AN's acceptance leg: the gapped clause the LLM heads on its own remnant | 13 / 2 | −2 |
| **DG** | the *membership* check read through rule C's coordination collapse | — | −1 |
| **DH** | rule CW's mirror leg: the elided clause is the **first** one | 64 / 2 | −1 |

Plus the upstream rows (**−4 / +1**, counted below).

### The batch's finding — a gate can be right about the disagreement and wrong about the agreement

Rule CX exists to license one *difference* of role notation: the complement of a verb of
remembering is `obj` to one reading and `ccomp` to the other, which is notation rather than two
claims. To say that, it required both roles to be complement roles — and that requirement, written
for the case where the roles differ, silently threw out every case where they are **identical**.
"Veramente **quant'** io del regno santo / ne la mia mente potei **far** tesoro, / sarà ora
materia del mio canto" (1:12): both readings put the free relative in `materia`'s subject slot and
disagree about nothing except which of its tokens names it. That is the *weakest* disagreement the
rule can be shown, and it was the one case the gate excluded.

The lesson generalizes past this rule. **A gate written to admit a specific disagreement should be
asked what it does with no disagreement at all** — the agreeing case is strictly inside the one the
rule already accepts, so excluding it is never the conservative choice it looks like. Rule DJ is
one condition rewritten (`drole == grole or both are complement roles`) and it reached two shapes
nobody had proposed a rule for: "fecimi **qual** è quei che disïando altro vorria" (23:14, a
comparative) and "se c'è **più** d'un varco" (purgatorio 11:41, a quantified nominal whose Layer-3
span is headed on the same `più`). All three acceptances were read individually before the rule
was kept.

### Three smaller ones

- **Ordering, in the same form the last five batches found it — and this time it is the sixth.**
  Rule DG is rule AQ′ exactly: a normalization complete inside `_classify_divergence` and absent
  from the membership check that runs before it. "cui più si convenia dicer 'Mal feci' / **che,
  servando, far peggio**" (5:67): the two compared infinitives are one subject between them,
  `_collapse_coordination` merges the second onto the first before the divergence check ever runs,
  and the membership check — reading the raw row — reported `far` as heading no NP, pronoun or
  derived predicate. Two lines. **Ask of every check that runs early which of the late
  normalizations it is missing**, now the most productive question this checker has.
- **A mirror leg found by asking which of two readings the LLM took.** Rule CW drops the remnants
  standing *after* the second of two derived subjects, because the LLM reads one clause per
  predicate and it read the first. Nothing makes the first its only choice: at "**Beatrice in
  suso**, e io in lei guardava" (2:22) the verb's own morphology settles it the other way
  (`guardava` is 1sg), so the gapped term is the one before the LLM's subject and rule CW's
  positional test looks straight past it. The gate that keeps the two legs disjoint is which
  subject the LLM named, so neither guesses.
- **A refusal in `derive_unit` needs an acceptance leg, and rule AN never got one.** Rule AN reads
  Layer 4's `orphan` as "this is a gapped clause, not a predicate" and hands the remnants to the
  coordination head's slots. The LLM reads the same gap the other way, heading it on the remnant
  itself: "de la voglia assoluta **intende**, e **io** de l'**altra**" (4:113) gets a tuple at
  `io` with the ∅ subject and the oblique the remnant supplies. Both readings say the line has two
  clauses and put the same two words in the second; which token carries its tuple is the citation
  convention rules CA/CC established. Rule DI is that leg, gated on the `orphan` itself.

### One candidate censused and dropped, on the corpus's own scope boundary

**A given `subj` against a derived `xcomp` on the same infinitive**, censused at **29** — a
coherent and largely lexical class: `convien(e|ti|mi|si)`, `piacque`/`piaccia`, `parve`/`parea`,
`conven`, `est`. For an impersonal verb the infinitive genuinely *is* the logical subject ("e di
sùbito parve giorno a giorno / **essere aggiunto**", 1:61; "**convienti** ancor **sedere** un poco
a mensa", 5:37), and rule M already accepts the reverse direction. But only **3** of the 29 are
reported at all, and the 29 are not one shape: `puote cader`, `lascia veder` and `fé pianger` are
modals and causatives, where the infinitive is not a subject on any reading. Separating them needs
a list of impersonal verbs — **an imported verb-valency lexicon by another name**, which the root
[`../PLAN.md`](../PLAN.md)'s *Out of scope* rejects on the ground that it is an external authority
rather than something the Italian line determines. Left flagged as genuine reading disagreement:
paradiso 1:61, 5:37 and purgatorio 2:120.

### What the batch left standing (18)

Canto 1 keeps 10 of them, and four are one line. **1:81** ("che pioggia o fiume / lago non fece
alcun tanto disteso") went 3 → 4 because the Layer-4 correction there is the honest trade rule AM
recorded: the old tree read `lago` as a third conjunct of the subject and `alcun` as a determiner
of `pioggia`, which is not Italian, and the LLM's own misreading (`alcun` as the subject, `pioggia`
omitted) had been matching it closely enough to be half-hidden. With `subj=pioggia, obj=lago`
correct, all four divergences are the LLM's and are now visible.

The rest: two plain omissions of an adjunct the tree records (1:79, 5:136 — the latter a
comparative `obl:come` rule AR does not reach because Layer 4 writes its `come` as an `advmod` on
the compared nominal rather than as a `case`); `non so che divino` (3:59), where the idiom's own
`che` is the governor Layer 4 hangs `so` under; the `sì … che` result clause read as a `ccomp`
(4:107), censused at 2 by the Inferno 21-25 batch and unchanged in kind; the accusative-and-
infinitive whose shared nominal Layer 4 parks in a `mark` slot (3:76, rule BW's shape reached
through rule V's candidate set — a route, not a rule, until it is censused); a depictive adjective
Layer 4 hangs on its predicate as an `advcl` (1:97, the fourth attachment point of the
construction rules R/AA/AU/AZ take from the other three); a subject the derivation propagates
across `conj` onto a 1sg verb because Layer 2 marks no person on the relative pronoun it comes
from (3:61, two positions); and three flat LLM omissions or duplications (1:72, 4:30).

## Rules DE-DF, from reading Purgatorio 31-33 — 358 → 351, −7 (2026-08-17)

Per-position read of all **14** soft violations in Purgatorio 31-33, the batch that finishes
Purgatorio, following the eight-step procedure in [`PLAN.md`](PLAN.md)'s *How to Read a Batch*.
Zero model calls. Purgatorio 31-33 itself went **14 → 11** (31: 3 → 2, 32: 7 → 4, 33: 4 → 5); the
corpus went **358 → 351 (−7, −2.0%)**. Two deterministic Layer-5 rules, 4 Layer-4 rows, 1 Layer-2
row, 2 Layer-3 spans and 2 case-annex rows. `pytest` **441 passed**, all other layers 0/0.

| rule | shape | census | net |
|---|---|---:|---:|
| **DF** | rule V's candidate set read through rule AI's Layer-3 NP-head equivalence | — | −4 |
| **DE** | rule C's collapse: a conjunct's role never displaces the coordination head's own | 98 | −2 |

Plus the upstream rows (**−6 / +5** together, counted below).

This is the smallest batch of the series, and its finding is proportionate: **the two rules are
both one existing normalization applied at a gate that had not read it**, which is the ordering
question the Purgatorio 1-5, 6-10, 21-25 and 26-30 batches each asked in a different form. Nothing
here is a new reading of Italian; both are places where the checker already knew the answer and
the gate was comparing raw positions.

One candidate was censused and dropped, at **2**.

### Rule DF — rule V's candidates, through rule AI

"ne li atti, l'altre tre si fero avanti, / **danzando** al loro angelico caribo" (purgatorio
31:132). `danzando` is a gerund with no subject of its own, so `derive_unit` is silent and rule V
supplies the candidate set by walking the head chain: `fero`'s derived subject, which Layer 4
attaches to `altre`. Layer 3 heads the span `[l'altre tre]` on `tre`, the LLM is told to cite a
noun phrase by its Layer-3 head, and so the citation and the candidate are two names for one
phrase — exactly the pair **rule AI** was written for.

Rule AI could not reach it. It runs downstream of `_apply_subj_authority`, and it only pairs a
`missing_arg` with an `extra_arg` of the *same role* — but for an inherited subject the derivation
has no `subj` row at all, so there is no derived half to pair with. The fix is one clause in
`_accept_control_subjects`: a citation that `_np_head_equivalent` says names the same noun phrase
as a candidate **is** that candidate. The function already tested each citation through rule C's
collapse for the same reason, and this is the second normalization it was missing.

**Measured −4 / +0** (purgatorio 30:25 and 31:132, paradiso 4:81 and 5:21), with one position at
inferno 18:30 changing class rather than count — see the Layer-3 correction below, which is why it
changed back.

### Rule DE — whose preposition survives the collapse

"la flagellò **dal capo** infin **le piante**" (purgatorio 32:156). Rule C maps every argument
citation onto its coordination head, so the LLM's `obl:a` on `piante` lands on `capo`, where the
LLM has also written `obl:da` — and the tie-break between two roles on one key is role rank, which
picked the conjunct's. The position the derivation reports with the head's own preposition came
back a `role_mismatch`.

Coordination in this corpus is not always of like with like. A conjunct carries its own `case`
marker as readily as it shares the head's, and **98** `conj` nominals corpus-wide have one whose
word differs — "dal capo infin le piante", "from head to sole", is two prepositional phrases, not
one named twice. When that is so, the head's own citation is the one that names the head and a
conjunct's role is only riding along on it, so a collapsed role never displaces an uncollapsed one.
Rank still decides between two collapsed conjuncts, which is the case rule C was written for.

The gate is the conjunct's own distinct `case` marker, and it is load-bearing. Without it the rule
also fires on apposition — "che **l'uno** a l'altro raggio non ingombra" (purgatorio 3:30), where
Layer 4 hangs `uno` on the emptier `che` as `appos`, the LLM's role for the `appos` is the right
one, and rank is the better answer. Unrestricted the rule measured **−2 / +1**; gated, **−2 / +0**
(purgatorio 32:156 and paradiso 32:57).

### Censused and dropped — the adjunct scoping over a relative clause

"che **di tutte altre cose** qual mi torse / più nel suo amor, più mi si fé nemica" (purgatorio
31:86). The partitive belongs with `qual` inside the relative clause and with `fé` outside it; the
LLM lists it on both, and Layer 4 hangs it on `fé` only. A rule accepting an oblique the LLM
scopes over both a predicate and the relative clause modifying that very oblique was censused
against the artifact: the structural shape (a relative clause on a derived oblique) occurs
**1026** times, and the LLM names the antecedent as the clause's own oblique in **2** of them.
Dropped, and the position is left flagged as genuine reading disagreement.

### What the batch left standing (11 positions)

- **purgatorio 31:15** `missing_tuple` — the Layer-2 correction below makes `mestier` a copular
  predicate the LLM never proposed, because its own reading of `fuor` was the mistagged one. The
  count is unchanged and the parse is right.
- **purgatorio 31:86** — the dropped candidate above.
- **purgatorio 32:69 ×2** — "ma qual vuol sia che l'assonnar ben finga": the LLM makes `vuol`
  govern `sia` where Layer 4 has it the other way round, and reads `l'assonnar` as `finga`'s
  subject where Layer 4 makes it the object. Genuine disagreement on a genuinely tangled line.
- **purgatorio 32:139 ×2** — "Quel che rimase … da la piuma … si ricoperse": plain omissions of
  the two obliques the tree records. `missing_arg obl*`, the residue's largest bucket, and the
  fifth `--fix` round's one prompt candidate.
- **purgatorio 33:25 ×2** — the LLM cites `parlando` for an oblique; with the Layer-3 span
  corrected below that citation now heads no nominal at all, which is the honest report.
- **purgatorio 33:106 ×3** — the Layer-4 correction below moves `le sette donne` to the predicate
  they belong to and exposes the LLM's own misreading of the same clause; see there.

## Rules CU-CY, from reading Purgatorio 21-25 — 409 → 388, −21 (2026-08-16)

Per-position read of all **33** soft violations in Purgatorio 21-25, following the eight-step
procedure in [`PLAN.md`](PLAN.md)'s *How to Read a Batch*. Zero model calls. Purgatorio 21-25
itself went **33 → 24** (21: 9 → 5, 22: 6 → 6, 23: 2 → 1, 24: 7 → 1, 25: 9 → 11); the corpus went
**409 → 388 (−21, −5.1%)**. Four deterministic Layer-5 rules, one `dep.subject_agreement`
refinement (rule CV), 27 Layer-4 rows and 1 Layer-2 row. `pytest` **427 collected**, all other
layers 0/0.

| rule | shape | census | net |
|---|---|---:|---:|
| **CW** | rule BA's oblique leg: the rest of the elided clause the second derived subject opens | 85 / 13 | −7 |
| **CX** | rule CK widened from the complementizer to the **interrogative word** that opens the clause | 6 | −6 |
| **CU** | a ∅ subject the LLM lists **beside** the derived one is the slot not decided, not a second claim | 6 / 4 | −3 |
| **CV** | `dep.subject_agreement`: the number-only exclusions ran *before* the person test and took it with them | — | −3 |
| **CY** | the clausal-complement double-listing test, read through the `aux` edge | 1 | −1 |

Plus the upstream rows (**−8 / +7** together, counted below).

Two of the batch's own shapes carried it. The first is **the second subject as a marker of
collapse**: rule BA already reads two derived subjects as one predicate holding two clauses, and
rule CW simply follows that reading past the subject slot to the rest of the elided clause — seven
positions in one line of gating. The second is that **an upstream correction can raise the count
and still be right**: four of this batch's six new positions are the LLM's own misreadings, which
the Layer-4 errors had been hiding.

### Rule CU — a ∅ beside the derived subject

"e perché tanti secoli **giaciuto** / qui se'" (purgatorio 21:80), "tanto **ovra** poi" (25:55),
"li ordini … li spiriti **muovono**" (paradiso 1:112). The LLM filled the subject slot twice, once
with pro-drop ∅ and once with the very token the derivation supplies. Two subjects for one
predicate is not two claims about the slot; it is the reading not deciding, which is **rule BA's
principle read from the LLM's end** — there the *derivation* offered two and was made to require
neither.

Censused at **6** predicates corpus-wide that list a ∅ beside another subject, **4** of them beside
the derived one; the rule takes the 3 that were flagged. Only the ∅ half is dropped, and only when
the other half is exactly the derived subject: a concrete subject the derivation contradicts is a
claim and stays flagged, which is what keeps 21:123 ("ma più d'ammirazion vo' **che ti pigli**",
where the LLM's ∅ stands against the derivation's `ammirazion`) reported.

**A variant was censused and dropped.** At 21:6 the LLM gives `condoleami` two *concrete* subjects,
the coordination head's and the nearest conjunct's own — rule BU's evidence for the alternative,
listed alongside the derived one. The census found **1** such predicate in the corpus. One instance
is not a population.

### Rule CV — the number exclusions swallowed the person test

Rule CR, one batch earlier, found that the 1/2-plural exclusion in `dep.subject_agreement` was
right about *number* and wrong about *person*, and narrowed it to the number half. It delegated the
coordinate case to "the conjunct branch below", which tests person member by member — but
**returning is what stops that branch from running**. "Né 'l dir l'andar, né l'andar lui più lento
/ facea, ma ragionando **andavam** forte" (purgatorio 24:2) left through the exclusion with its
3-vs-1 person clash never asked, and `derive_unit`'s step 3 inherited two third-person nouns onto a
first-plural verb.

The same defect turned out to be in **five more** exclusions, all of them number licences —
*coordination inside the subject phrase*, *comitative phrase on a plural head*, *quantified subject
read as one measure*, *copula agreeing with its predicate nominal*, *impersonal `si`* — each of
which returned "undecidable" for both features. They now record that the *number* half is
undecidable and let the person test run first; a pair that clears the person test and holds one of
these licences comes out undecidable from exactly the reason it did before. Two further halves of
the same rule:

- **a coordination is a chain, not a fan.** Layer 4 writes "La bella donna … e Stazio e io"
  (purgatorio 32:28) as `donna` ← `Stazio` ← `io`, so the members are only reached by walking
  `conj` transitively; the direct-children walk lost the `io` that carries the person.
- **`tutto` joins `_DISTRIBUTIVE_LEMMAS`.** "là 've già **tutti e cinque sedavamo**" (9:12), "e
  **tutti eravamo** già vòlti" (27:85): "tutti e cinque" names the whole of the "we" the verb
  carries, exactly as `ambedue` does.

`dep --check` stays **0 hard / 0 soft** — the refinement surfaced one new position, inferno 23:103,
which is a real Layer-4 mis-parse and was corrected (below). Layer 5: **−3** (purgatorio 24:2 twice,
paradiso 32:111).

### Rule CW — rule BA's oblique leg

"e come abete in alto si **digrada** / di ramo in ramo, così **quello in giuso**" (purgatorio
22:134), "che li occhi miei si **fero** a lui seguaci, / come **la mente a le parole sue**"
(24:102), "si mosse, e **io di rietro inver' l'altura**" (9:69), "La sua chiarezza séguita
l'ardore; / **l'ardor la visïone**" (paradiso 14:41), "ed **essi teco le cittadi e ' regni**"
(18:84), "**ed ella primavera**" (purgatorio 28:51), "e **là da Tagliacozzo**" (inferno 28:17),
"come **nota con suo metro**" (paradiso 28:9).

Two subjects on one predicate is rule BA's own evidence that Layer 4 has collapsed **two clauses**
onto one head — a gapped coordination, or the second term of a comparison, whose verb the line does
not repeat and which the tree therefore has nowhere else to put. Rule BA drew the conclusion for
the subject slot only, and left the rest of the elided clause — its obliques, its object, its
predicate complement — asserted as arguments of a predicate that never had them. The remnant is
identified positionally, the one thing the tree does say about it: an argument standing **after**
the second subject is on the second term's side of the gap.

**Censused at 85** arguments standing after a second derived subject, **13** of which the LLM does
not cite; every one of the 13 is a gapped conjunct or comparison term, and the rule takes the **7**
that were flagged. The eighth, purgatorio 9:69, it does not: rule AG had already dropped one of the
two subjects there as disagreeing, so by the time this gate reads `d` the collapse is no longer
visible in it. Reading the *normalized* `d` is deliberate — it is what rule BA reads, and the two
legs of one reading must not diverge — but it is also this batch's third ordering finding, and it
costs one position.

### Rule CX — rule CK widened to the interrogative word

"Se tu riduci a mente **qual** fosti meco" (purgatorio 23:115), "Ma dilli **chi** tu fosti"
(inferno 13:52), "a dirne **chi** tu se'" (16:32), "e perché fosse **qual** era in costrutto"
(paradiso 12:67), "tentando a render te **qual** tu paresti" (purgatorio 31:143), "di non celar
**qual** hai vista la pianta" (33:56).

The complement is an indirect question, which `derive_unit` cites by its verb and the LLM cites by
the word that opens it. Rule CK is the same convention for a clause opened by a `che`, and neither
of its gates reaches here: an interrogative word is a constituent *inside* its clause (Layer 4
makes `qual` the `advmod`, `attr` or `obj` of its own verb — rule BW's tension), and the complement
of a verb of remembering is `obj` to one reading and `ccomp` to the other, a difference of notation
about one slot rather than two claims.

Three gates keep it to the shape: rule BW's POS test (a pronoun, adjective or adverb, never a
conjunction — a subordinator is rule CK's), both roles complement roles, and the word must be the
**leftmost token of the whole clause subtree**. A fourth is explicit: the clause's own `nsubj` is
refused, because a subject named on the matrix is rule BI's accusative-and-infinitive, a claim
about a different slot and not a way of naming the clause. The rule takes all **6** positions the
census found.

### Rule CY — the double-listing test read through the `aux`

"«Come!», diss' elli … chi v'**ha** per la sua scala tanto **scorte**?" (purgatorio 21:21). The
clausal-complement double-listing skip accepts the LLM listing a clause as its own tuple instead of
citing it as an argument, and it compares raw positions: Layer 4 heads this quoted question on
`scorte` with `ha` as its `aux`, and the LLM's tuple is headed by `ha`, so the clause *is*
double-listed — one edge away. `_aux_of_derived_predicate` already reads this very convention from
the other direction, and rules AQ and BP already normalize `aux`/`cop` to the lexical word for the
citation gates; this test was the one left comparing raw positions. The Inferno 31-34 batch's
finding — *ask which edge a gate reads* — in a fourth place.

**Censused at 1** position corpus-wide: the double-listing skip already takes **655** of the 656
uncited clausal complements. Kept for consistency between the two directions of one gate rather
than for its count.

### Upstream corrections in the same read

**Layer 4 — 27 rows** (see [`../dep/CORRECTIONS.md`](../dep/CORRECTIONS.md)): eleven predicate
nominals of `essere` recorded as `obj` or `nsubj` (a census the rule-CV finding opened, including
inferno 23:103, the one position rule CV newly reported), six reflexive clitics recorded as the
clause's `nsubj`, the `a riso` cluster at purgatorio 22:26 (5 rows), the two causative
`lasciare` + infinitive nominals at 24:71/73, the `che`/`petto` swap at 25:67, and the
case-marked `persona` at 22:17. **Layer 2 — 1 row**: `riso` in "un poco **a riso** pria" (22:26) is
the noun *riso*, not a past participle of *ridere*.

Two of these raise the count and were kept anyway — the trade rule AM recorded, and the reason the
batch's own residue went from 33 to 24 rather than to 18:

- **purgatorio 25:67** (+2). "Apri a la verità che viene **il petto**": Layer 4 had `il petto` as
  the subject of `viene` and the relative `che` as its object, and the LLM read the line the same
  way. With the parse corrected, three of the LLM's own citations diverge from it. The derivation
  is now right; the reading is now visibly wrong, which is what a soft violation is for.
- **purgatorio 22:90** (+4 / −2). "chiuso cristian **fu'mi**": the reflexive `mi` was recorded as
  the clause's `nsubj`, which hid the LLM reading it as the subject of a first-person verb. Once it
  is `expl` the derivation inherits the real `io` from the coordination head and the LLM's reading
  is reported on all three predicates it touches.

## Rules CP-CT, from reading Purgatorio 16-20 — 427 → 409, −18 (2026-08-16)

Per-position read of all **26** soft violations in Purgatorio 16-20, following the eight-step
procedure in [`PLAN.md`](PLAN.md)'s *How to Read a Batch*. Zero model calls. Purgatorio 16-20
itself went **26 → 14** (16: 11 → 6, 17: 1 → 0, 18: 3 → 1, 19: 6 → 4, 20: 5 → 3); the corpus went
**427 → 409 (−18, −4.2%)**. Four deterministic Layer-5 rules, one `dep.subject_agreement`
refinement (rule CR), 17 Layer-4 rows, 2 Layer-2 rows, 1 Layer-3 span and 2 case-annex rows.
`pytest` **414 collected** (396 test functions, +12 from this batch; earlier entries in this file
counted functions), all other layers 0/0.

| rule | shape | census | net |
|---|---|---:|---:|
| **CP** | rule AZ's noun leg: a bare caseless `obl` **nominal** is the predicate's secondary predicate | 245 / 44 | −5 |
| **CS** | a derived predicate whose tuple is **empty** asserts nothing, so its absence is not a divergence | — | −2 |
| **CQ** | rule T's `xcomp` leg: the prepositional infinitive Layer 4 marked with `case` and attached as a complement | 4 | −2 |
| **CT** | a copula Layer 4 hung **under** its own predicate complement | 25 / 294 | −2 |
| **CR** | `dep.subject_agreement`: the 1/2-plural exclusion covers the *number* test, not the person one | 3 | −2 |

Plus the upstream rows (**−7 / +2** together, counted below).

The batch's own shape: **eleven of the 26 were upstream**, nine of them in canto 16 alone — the
second batch running where one canto carried the tree's errors. Four more are the LLM omitting an
oblique or a dative the tree records, which is now the residue's largest single bucket
(`missing_arg obl`, **81** of the 409) and the batch's one prompt-side lead.

### Rule CP — rule AZ's noun leg

"che **piuma** sembran tutte l'altre some" (purgatorio 19:105), "come fatto fui **roman pastore**"
(19:107), "non uscir … **Gentili**, ma **Cristiani**" (paradiso 20:103), "e, quasi **amici**,
dipartirsi pigri" (33:114). Rule AZ accepts a bare caseless `obl` as the predicate's secondary
predicate when it is an **adjective**; Italian writes the same predication with a bare nominal as
readily, and 33:114 has one of each in one line — `pigri` taken by rule AZ, `amici` flagged.

**Censused at 245** bare nominal obliques corpus-wide against rule AZ's 44 adjectival ones. The
larger population is the caseless `obl`'s other job, the adverbial accusative ("la **notte**
ch'i' passai", inferno 1:21) — but the census is not the acceptance: the rule fires only where the
LLM independently read the token as the predicate's complement, which a temporal accusative does
not attract, and it takes **5**, exactly the five read positions. The **adverb** leg stays
declined, as when rule AZ was written ("è **fuor** di strada", paradiso 8:148); the **pronoun**
leg is refused explicitly, since 509 of the 1118 bare obliques are the corpus's own clitics, where
the question is rules AB/AW's, not this one. `"pronoun"` contains `"noun"`, so that exclusion is a
helper (`_is_nominal_pos`) rather than the module's usual substring test.

### Rule CQ — rule T's `xcomp` leg

"mi fé desideroso **di sapere**" (purgatorio 20:146), "Qual pare **a riguardar** la Carisenda"
(inferno 31:136). Layer 4 hangs the infinitive on its governor as `xcomp` — a *complement* — while
writing the preposition that introduces it as a `case` child — the deprel of a *nominal*. The tree
is of two minds about one edge, and the readings split along that seam: `derive_unit` reads the
deprel, the LLM reads the preposition sitting on the token. Rule T settles the identical
convention one deprel over, for `advcl`.

The gate is rule T's, unchanged: the LLM's lemma must be one the tree itself carries on that very
token. That is what keeps paradiso 9:135 flagged — "pare a' lor **vivagni**", where the `a'` marks
the dative beside the complement and nothing on `vivagni` corroborates the oblique reading. Of the
four `obl:<lemma>`-against-`xcomp` positions in the corpus the rule takes **2**; purgatorio 17:111
is a third, taken after the upstream retag below put the `da` on the infinitive it governs.

### Rule CS — an empty derived tuple

`derive_unit` writes a role-less `=(0, 0)` row for a position it promoted to predicate and then
found no argument for. Such a tuple asserts nothing, so the LLM's not proposing it cannot be a
divergence — the same reading rules AN, BN and CA already give ("a tuple with no arguments in it,
which no reading of the line can supply"), applied at the reporting end rather than at the census.

It takes the elliptical answer "**Nullo**, però che 'l pastor … rugumar può" (purgatorio 16:98),
whose verb is gapped from the question it answers in the previous parse unit, and "**per che**,
come fa l'uom …" (25:4), a connective Layer 4 wrote as a pronoun in `advcl` — rule BN's shape with
a POS rule BN does not test.

**The variant that refuses to mint the predicate at all was measured at +180 and rejected.**
Extending rule BN's argument test from a conjunction to any non-verb clause head looks like the
same rule one step earlier, and is not: a non-verb clause head with no argument child is
overwhelmingly a copular or controlled predicate whose only subject comes from rule V, and the LLM
proposes those correctly. Reading the derived *tuple* rather than the deprel separates the two
exactly. The Purgatorio 11-15 batch's finding again — the measured variant is the argument.

### Rule CT — the copula under its own complement

"quant' **esser può** di nuvol **tenebrata**" (purgatorio 16:3): the degree clause of the
adjective the copula predicates, which Layer 4 hangs *under* that adjective. The corpus's own
convention makes the complement the head of a copular clause and the copula its `cop` child; where
the copula carries a clause deprel instead, `derive_unit` reads the edge downwards and gives it
nothing but a pro-drop subject, while the LLM reads the predication and names the adjective as its
`attr`. This is rule BT's shape (the argument is the predicate's own governor) with the copular
convention in place of the free relative, and rule Y's evidence from the other side.

**Censused at 21** `essere` clauses under an adjective head and 4 under a noun, against **294**
`advcl` verbs under a nominal head in all: the copular lemma is the whole gate, and without it the
rule would accept every adverbial clause modifying a noun. It takes 16:3 and paradiso 26:109
("Tu vuogli udir **quant' è** che Dio mi puose"), both correctly.

### Rule CR — the person half of the 1/2-plural exclusion

`dep.subject_agreement` treated a 1st/2nd person **plural** head as admitting any singular
subject, because the tree may hold only one member of the "io e tu" it agrees with. That is a
statement about *number*; it was swallowing the *person* test with it. A lone third-person subject
cannot be a member of a "we" at all — "Ciò ch'io dicea … contrario suon **prendemo**"
(purgatorio 20:102), where `Ciò` is the subject of the *first* conjunct and the second is the
pilgrims' own. The exclusion now applies only to a subject that could be such a member: a 1st or
2nd person word, or a coordination, whose person the conjunct branch tests member by member.

Narrowing it surfaced **3** new `dep --check` soft violations, all one shape — `ambedui`,
`amendue` and the distributive `uno` ("uno innanzi altro, ce n'andavamo") standing in for the whole
of a "we" the verb already carries. All three are the notional reading `_DISTRIBUTIVE_LEMMAS`
already names for `ciascuno`, so the three lemmas join that set and `dep --check` returns to
**0 hard / 0 soft**. Layer 5: **−2**, both at 20:102.

### Upstream: 17 Layer-4 rows, 2 Layer-2 rows, 1 Layer-3 span, 2 case-annex rows

Applied with a gated script that asserts the word and the current cell value at every
`(line, token)` before rewriting it. Together **−7 / +2**.

- **16:43** "non mi celar chi fosti **anzi la morte**" — `anzi` was an `advmod` on `celar` and
  `morte` a `vocative`. It is a prepositional phrase on `fosti` (−1).
- **16:64-65** "**Alto sospir** … mise fuor prima" — the sigh was the `nsubj` of `mise`; it is
  what he put forth. With `mise` pro-drop, the LLM's concrete subject on the following `cominciò`
  is accepted by the pro-drop branch (−2).
- **16:98-99** "Nullo, **però che** 'l pastor … rugumar può, ma non ha l'unghie fesse" — `che` was
  the `obj` of `rugumar`; it is the second word of the causal conjunction. `Nullo` is the
  elliptical answer and heads its clause, `può` the because-clause under it, `ha` `può`'s
  coordinate sharing `'l pastor` (−2, +1: the LLM's own hedge, two subjects on `ha`, stays).
- **16:129** "e **sé brutta** e la soma" — Layer 2 read `brutta` as the adjective *brutto*; it is
  the verb *bruttare*, with `sé` (now accusative in the annex) and `la soma` as its two objects.
  The same shape as purgatorio 14:69's `parte` in the previous batch. Net 0 on the count, and the
  parse is right (−1 / +1).
- **17:111** "**da quello odiare** ogne effetto è deciso" — the `da` was on `quello`; it governs
  the infinitive ("from hating that"), whose own object `quello` is (accusative in the annex).
  With rule CQ above, −1.
- **18:50** "ed **è** con lei **unita**" — `unita` was an `amod` hung on the verb; it is the
  participial predicate and `è` its copula, the convention the rest of the corpus uses (−1).
- **18:117** "se **villania nostra giustizia** tieni" — the possessive belonged to `villania`; it
  belongs to `giustizia`, the object, and the Layer-3 span moves with it. The position stays
  flagged: the LLM swapped the object and the predicative complement, which is its own reading
  (±0).
- **18:140** "tanto divise … **che** veder più non potiersi" — the consecutive `che` of "tanto …
  che" was the `obj` of `veder`; it is the clause's marker (−1).
- **20:151** "così **m'andava** timido e pensoso" — Layer 2 read `andava` as 3sg; it is Dante's
  own going, 1sg, as lines 149-150 are. **This one costs a violation (+1)** and is kept: rule AG
  had been dropping the inherited 1sg subject on the strength of the wrong person, and the LLM's
  omission of that subject was hidden behind the drop. The honest trade earlier rounds recorded —
  the count is not the measure, the correctness of the parse is.

### Censused and dropped

- **The LLM naming a marked clause by a nominal inside it** — "or può … passarsi **per qualunque
  lasciasse**" (16:118), where the `per` sits on the free relative's verb and the LLM cites the
  `qualunque` inside it. Censused at **243** verbs carrying both a `case` child and a nominal
  argument: far too broad a licence for the one position it would take. Rule T's gate (the LLM
  must cite the clause itself) is what keeps that rule narrow, and this would remove it.
- **A non-finite conjunct with no arguments** — "di ragionar coi buoni o **d'appressarsi**"
  (16:120), an `extra_tuple`. Rule BZ decided this shape deliberately when it restricted the
  second `conj` walk to finite verbs, on the ground that the minted tuple would be empty; rule CS
  now says the same thing at the other end. Left as decided.

## Rules CK-CO, from reading Purgatorio 11-15 — 448 → 427, −21 (2026-08-16)

Per-position read of all **30** soft violations in Purgatorio 11-15, following the eight-step
procedure in [`PLAN.md`](PLAN.md)'s *How to Read a Batch*. Zero model calls. Purgatorio 11-15
itself went **30 → 15** (11: 5 → 4, 12: 3 → 2, 13: 1 → 1, 14: 15 → 3, 15: 6 → 5); the corpus went
**448 → 427 (−21, −4.7%)**. Five deterministic rules, the `dep.subject_agreement` refinement the
Inferno 21-25 batch measured and deferred, 11 Layer-4 rows, 8 Layer-2 rows, 1 Layer-3 span and 1
case-annex row. `pytest` **384**, all other layers 0/0.

The batch's own shape: **canto 14 held half the batch (15 of 30) and gave up 12 of them to
upstream reading**, which is the highest upstream share of the series. Three of its five checker
rules came out of positions where the tree was right and the checker silent; the other two came
out of `derive_unit` and rule AG.

| rule | shape | census | net |
|---|---|---:|---:|
| **CK** | the LLM names a subordinate clause by the complementizer that opens it | 18 / 3 | −5 |
| **CM** | rule AL read through the `case` annex: a fused clitic whose two slots back the two roles separately | 13 / 7 | −2 |
| **CL** | rule AG's third leg: once the inherited subject is dropped, the slot is rule V's to decide | — | −2 |
| **CN** | rule AN's slot assignment: a ∅ slot goes to the back of the queue | — | −1 |
| **CO** | rule AU's `advmod` leg: a second predicative adjective on the predicate's own complement | 101 / 77 | −1 |

Plus the coordinated-subject refinement and the upstream rows (**−10 / +2** together).

### Rule CK — the clause named by its complementizer

"degno / ben è **che** 'l nome di tal valle **pèra**" (purgatorio 14:30). The clause fills the
copula's subject slot; `derive_unit`, reading the tree, cites its head `pèra`, and the LLM cites
the `che` that introduces it. Both name one constituent in one slot. Rule AE already accepts a
free relative cited from its two ends; this is the same convention for an ordinary subordinate
clause, and it is written as **one gate read from both sides** — the shape rules CA/CC
established — because without the acceptance leg the marker is an `extra_arg` and without the
mirror the clause is a `missing_arg`, for one disagreement. Two gates: the marker must hang on
that very clause and the clause on this very predicate (rule BW covers the different shape, a
`mark` that hangs on the *predicate* and fills a slot of its own), and the roles must match.

**Censused at 18** given citations of a `mark` whose head is a clause on the same predicate.
**Only 3 have matching roles** — 14:30, purgatorio 18:34, paradiso 14:18, worth 5 violations
between them. The other **15 pair the LLM's `subj` against a derived `ccomp`**: that is the
impersonal subject-clause question, a second claim about the slot rather than a citation
convention, and where it is accepted at all it is accepted by other rules already (only 3 of the
15 are flagged, all for unrelated reasons). Restricting to the matching role is what keeps the
rule a convention.

### Rule CL — rule AG's third leg

Rule AG drops a `conj`-inherited subject whose Layer-2 person contradicts the predicate's own;
rule AH then drops the LLM's ∅ with it, on the ground that the derivation is now *silent* about
the slot. But the same argument covers a **concrete** subject: silence is branch 2's state, and
branch 2 does not accept a citation outright either — it validates it against rule V's
control/raising candidate set. Leaving concrete citations flagged was reporting the LLM's own
reading against a slot the derivation had just disclaimed.

"Io veggio tuo nepote che diventa / cacciator di quei lupi … **e tutti li sgomenta**" (purgatorio
14:60) is the evidence line, and it is *not* one of the two the rule takes: `che` is the subject
of a relative clause the control walk does not reach, so it stays flagged, which is the gate
working. What the rule takes is inferno 14:117 ("fanno Acheronte, Stige e Flegetonta; / poi **sen
van** giù") and paradiso 21:3 ("e l'animo con essi, / e da ogne altro intento **s'era tolto**"),
where the citation is an argument of the coordination head and the LLM's reading is the right one.
`_accept_control_subjects` is branch 2's body factored out, so the two legs cannot drift apart.

### Rule CM — rule AL through the `case` annex

Rule AL accepts a fused clitic filling two roles at once when the roles are exactly
`{obj, obl:a}` — the pair `gliel'` encodes. "e ora a pena in Siena **sen** pispiglia"
(purgatorio 11:111) and "**sen** va" (paradiso 2:20) are the same shape with a different cluster:
`si` + `ne`, whose annex value is `reflexive+ablative`. The derivation takes the reflexive half as
the verb's object — rule AB's own gate already lets a bare clitic carry `obj`/`iobj`/`obl:a` — and
the LLM takes the ablative half as the oblique `ne` marks. Each side is corroborated by a
*different* slot, which is what makes this a non-dispute rather than a role disagreement.

**Censused at 13** fused positions carrying a role_mismatch; **7 split this way** (3 of them
already taken by rule AL's fixed pair), and 2 were flagged. Requiring the two supporting slot sets
to *differ* is the gate: a fused position whose annex backs only one side, or the same slot on
both, stays flagged — which is what leaves inferno 29:34, purgatorio 2:40, 12:48, 19:24 and 27:5
alone.

### Rule CN — a ∅ slot goes to the back of the queue

Rule AN hands a gapped conjunct's remnants to the coordination head's slots, pairing them off in
the order the head's own arguments stand in the line. But ∅ = (0, 0) sorts before every real
position, so a pro-drop subject slot was taking the **first** remnant of every gapped clause under
a pro-drop predicate. "molti di vita e **sé** di pregio priva" (purgatorio 14:63): `pregio` claims
`obl:di` by its own preposition, and `sé` — the second object, which the `case` annex calls
accusative — was then derived as the *subject* of `priva`.

Two variants were measured. Dropping ∅ slots from the queue outright took **2** (14:63 and
paradiso 4:113) and was **wrong**: "tu … intende de la voglia assoluta, e **io** de l'altra"
(4:113) is a genuine contrastive subject remnant under a pro-drop head, and the rule was silencing
it. Moving ∅ slots to the back instead takes 14:63 and leaves 4:113 derived correctly (and still
flagged, because there the LLM mints a predicate at `io`). A ∅ slot is still offered — only once
the overt slots are spoken for.

### Rule CO — rule AU's `advmod` leg

Rule AU accepts an adjective Layer 4 attaches `amod` to one of the predicate's own derived
arguments as the predication's secondary predicate. "Io non son … esser contento **più digiuno**"
(purgatorio 15:58) is the same construction with `advmod`: `digiuno` hangs on `contento`, which is
`esser`'s own derived complement, and the LLM reads it as `esser`'s second predicative. The other
three gates are unchanged — adjective POS, `xcomp` role, host is a derived argument of this same
predicate — and they are what keep it narrow: **101** adjectives corpus-wide stand `advmod` on a
nominal or adjective, **77** of them on a derived argument of some predicate, and the rule moves
**1**.

### The coordinated-subject refinement — a route the batch closed

`dep.subject_agreement` bailed out with "undecidable" as soon as the subject carried a `conj`
child. The Inferno 21-25 batch measured restricting that exclusion to the **number** test and
found 12 new `dep --check` soft violations, and reverted it rather than land a non-zero check
([`../dep/CORRECTIONS.md`](../dep/CORRECTIONS.md)); clearing those 12 has been a standing route
since.

Two positions in this batch ran into it — "e dimanda ne **fei**" (purgatorio 14:75, a 1sg conjunct
inheriting the coordinate nominal subject `Lo dir … la vista`) and inferno 24:125 — so the route
was folded in. Reading all 12 showed the deferred refinement was **half right**: a coordination
does have a person, but Italian lets a finite verb agree with **one member** of it, in either
direction ("Tosto che 'l duca e io nel legno **fui**", inferno 8:28, 1sg on the second conjunct;
"né io né altri 'l **crede**", 2:33, 3sg on the second). Testing the head's person against *every*
conjunct rather than against the first leaves **6**, and all 6 are real upstream errors, listed in
[`../dep/CORRECTIONS.md`](../dep/CORRECTIONS.md) and
[`../morph/CORRECTIONS.md`](../morph/CORRECTIONS.md). With those corrected, `dep --check` is back
to 0 and Layer 5 moves **−3 / +1**.

### Upstream corrections

Twelve of the batch's 30 positions were the tree or the morphology, not the checker. Canto 14 held
all but two of them. Full rows in [`../dep/CORRECTIONS.md`](../dep/CORRECTIONS.md),
[`../morph/CORRECTIONS.md`](../morph/CORRECTIONS.md), [`../np/CORRECTIONS.md`](../np/CORRECTIONS.md)
and [`../case/CORRECTIONS.md`](../case/CORRECTIONS.md). The largest is **purgatorio 14:69**, "da
qual che parte il periglio l'assanni", where Layer 2 read `parte` as the verb `partire`: that made
"from whatever side" a clause, gave `il periglio` to it as a subject, and left `assanni` to inherit
one across `conj` — three violations from one mistag, all cleared (and one new `extra_tuple`, the
LLM having minted the same phantom predicate, now reported where it belongs).

**Three retags are net zero and were applied anyway**, the honest trade rule AM records:
purgatorio 11:19 (`Nostra virtù` is what the Paternoster asks not to be tested, so `obj`, not
`vocative` — the addressee is God, unnamed), 12:136 (`a che guardando`: the gerund governs the
oblique Layer 4 hung on the matrix `sorrise` — the LLM lists it under both, so the violation moves
rather than clears) and purgatorio 29:37 (`fami … per voi soffersi` is "if I ever suffered hunger
for you", so `obj`).

### Censused and dropped

**The Layer-3 NP-head duplicate citation.** "se c'è **più d'un varco**" (purgatorio 11:41): the LLM
lists the subject twice, once by the Layer-3 span's head `più` and once by Layer 4's `varco`, and
the second matches the derivation exactly. A rule accepting a given-only citation that is the head
of a span containing an already-accepted argument of the same predicate and role censuses at
**5** and would clear **2**. Dropped: one of the two is paradiso 10:142 ("che l'una parte e
l'altra tira e urge"), where the real question is whether the coordinate nominal is the subject or
the object of the two verbs, and the rule would silence it for the wrong reason — the same ground
the Inferno 31-34 batch declined rule BR's mirror on. **Layer 3 is over-inclusive by design**, and
a span is not evidence about a slot.

### The 15 that stand

Four are the LLM omitting an adjunct the tree records (13:133 `ma picciol tempo`, 14:37 `dal
principio suo`, 15:10 `a lo splendore`, 15:121 `con le gambe avvolte`) and one a dative it drops
(15:12). Three are the two net-zero retags above plus 12:136's moved oblique. Two are the LLM
minting a predicate the line does not carry (11:110, at the adverb of a `dinanzi a` cluster;
14:69, at the `parte` its own reading turned into a verb). One is rule CL's gate holding (14:60).
One is `quanto` read as a subject where Layer 2 calls it an adverb (12:24). One is the copular
subject/complement exchange the Purgatorio 1-5 batch censused at 1 and dropped (15:32) — now at 2.
One is a Latin quotation as the subject of a passive Layer 4 calls an object (15:39), the
structural class [`PLAN.md`](PLAN.md) leaves standing by design. And one is rule CK's own boundary
(11:41, above).

## Rules CA-CJ, from reading Purgatorio 6-10 — 481 → 448, −33 (2026-08-16)

Per-position read of all **35** soft violations in Purgatorio 6-10, following the eight-step
procedure in [`PLAN.md`](PLAN.md)'s *How to Read a Batch*. Zero model calls. Purgatorio 6-10 itself
went **35 → 19** (6: 3 → 2, 7: 3 → 1, 8: 6 → 2, 9: 13 → 7, 10: 10 → 7); the corpus went **481 →
448 (−33, −6.9%)**. Ten deterministic rules plus 1 Layer-4 row. `pytest` **372**, all other layers
0/0.

The batch's own shape: **eight of the ten rules are about coordination or about a predicate the
derivation declines to mint**, and the two halves turned out to be the same question asked from
opposite ends — *when UD promotes a conjunct to the clause head, is that an elided clause or a
coordinate argument?* Rule CA answers it on the derivation side and rule CC on the acceptance
side, from one test.

| rule | shape | census | net |
|---|---|---:|---:|
| **CA** | rule BN's argument test applied to the `conj` branch: an argumentless nominal conjunct is not an elided clause | 209 | −10 |
| **CB** | an oblique the tree hangs on a predicative complement the derivation never promotes | 566 / 551 | −2 |
| **CC** | rule CA's argument leg: the promoted coordinate nominal, in the slot the LLM gives it | (CA's) | −5 |
| **CD** | the coordination-head walk stops where argument coordination ends and clause coordination begins | — | −1 |
| **CE** | the antecedent and the relative pronoun of its own relative clause are one referent | 2061 | −1 |
| **CF** | the controller a fused clitic hides (`tenerla serrata`) | 66 | −3 |
| **CG** | the coordinate oblique whose noun is elided, citable only by its adjective | 56 | −2 |
| **CH** | rule Z's adnominal leg: a verb in `amod`/`acl` is a reduced relative clause | 5019 | −3 |
| **CI** | rule AA's host test read through rule C's collapse | — | −1 |
| **CJ** | rule V's oblique leg: the controller Layer 4 labelled `obl` | — | −4 |

Plus 1 Layer-4 row (**−1**).

### The batch's finding: an empty tuple is not a reading

Rule BN (the 26-30 batch) refused to mint a predicate at a *conjunction* Layer 4 had put in a
clause-head deprel with no arguments, on the ground that **no reading of the line can fill the
tuple**. This batch found the same defect one branch over, in `promote_conjuncts`: "Sordel rimase
e **l'altre genti** forme" (9:58) and "sen venne suso; e **io** per le sue orme" (9:60) promote a
noun and a pronoun whose remnants Layer 4 left on the coordination head, so the minted tuple is
empty — or, worse, a lone pro-drop `subj` ∅, which asserts that the conjunct has a subject other
than itself. The same test that stops rule BN's conjunctions stops these (**−10**, and 7:19's
phantom `grazia` predicate with them).

The reach of that argument was then **measured and bounded**. Generalizing it once more — dropping
*every* non-verb clause head with no argument children, which would have covered a comparative's
second term as well — was measured at **+168** and rejected outright: those positions are
overwhelmingly copular predicates whose subject is pro-drop, which the LLM proposes and the
corpus's own convention expects. The same measurement is why rule CA carries an explicit `cop`/`aux`
exemption ("Tant' **è amara**", inferno 1:7): a copula child is the tree's own assertion that the
conjunct heads a predication, and dropping it made `pytest` fail while the violation count did not
move — the count is not the measure.

### The ten rules

- **Rule CA — `promote_conjuncts`.** A non-verb `conj` conjunct with no argument child of its own
  and no `cop`/`aux` is a coordinate nominal, not a gapped clause. Rules AN and BN already refuse
  the same promotion for `orphan`-carrying conjuncts and for conjunctions; this is the general
  test. A conjunct that *does* carry arguments ("Ed **elli**: «Vedi …»", inferno 11:15, whose
  `ccomp` is the elided speech) stays promoted, which is what keeps the corpus's elided-speech
  convention intact. Censused at 209 promoted non-verb conjuncts.
- **Rule CC — `_promoted_conjunct_argument`.** The acceptance side of the same decision: having
  denied that the conjunct is a clause, the checker owes it a slot, and the derivation gives it
  none — Layer 4 attached it to the verb, not to the argument it coordinates with, so there is
  nothing to disagree about. Accepted in whatever role the LLM assigns, as in rule AJ, gated on
  rule CA's own test ("qual merito o **qual grazia** mi ti mostra?", 7:19).
- **Rule CD — `_coordination_head`.** Rule C maps an argument citation onto its coordination head,
  walking `conj` upwards without asking what it is walking onto. For `io` at 9:60 the chain runs
  `io` → `venne` → `tolse` → `rimase` and rewrites a subject citation into a citation of a
  predicate three lines up, which no reading asserts — and hides the conjunct from rule CC. The
  walk now stops at a `conj` step from a nominal onto a **verb in a clause slot**; a verb that is
  itself an argument is a real coordinate member ("addimandò … di **dispensare** … ma **licenza**",
  paradiso 12:95, measured: the first variant, without that exemption, was **−3/+2** and re-flagged
  exactly this position). Final: **−1**, plus two `role_mismatch` citations at purgatorio 14:63 and
  27:108 that now name the nominal itself instead of a verb three lines away.
- **Rule CB — `_stranded_on_underived_complement`.** "li occhi e 'l naso / e **al sì e al no**
  discordi **fensi**" (10:63): Layer 4 hangs the obliques on `discordi`, the adjective it marks
  `attr` on `fensi`, and the derivation promotes neither adjectival complements nor their
  arguments — so an argument the tree plainly records is dropped and the LLM, hanging it on the
  only verb there is, is reported for naming it. Rule AM makes the same collection from a
  predicate's `cop`/`aux`; rule X accepts the *reverse* relocation, where the complement is a
  derived predicate and the two readings disagree about which carries the argument. Gated like
  rules S and T: the given `obl:<lemma>` must name a preposition the tree carries on that edge.
  Censused at 566 obliques under `attr`/`xcomp` complements (551 with a `case` child).
- **Rule CE — `_control_subject_candidates`.** The antecedent and the relative pronoun of its own
  relative clause are one referent, so either names an adnominal predicate's subject ("O superbi
  cristian … **che**, de la vista de la mente **infermi**, fidanza avete", 10:122). This is the
  argument-identity route the 16-20 and 21-25 batches named and left unopened; censused at 2061
  antecedents carrying both an adnominal predicate and a relative-pronoun subject, and kept to the
  relative pronoun forms so that an ordinary nominal subject of the relative clause — a different
  referent — stays flagged.
- **Rule CF — `_control_subject_candidates`.** Object control whose object is a clitic fused into
  the host verb ("a **tenerla serrata**", 9:128). Layer 1 gives the clitic no position, so the only
  citation for it is the host token, which is exactly what rules AL and AS already read as two
  roles on one position. Censused at 66 `xcomp` edges under a fused verb+pronoun host.
- **Rule CJ — `_control_subject_candidates`.** The same function's third leg: the candidate set
  was `subj`/`obj`/`iobj`, but this corpus's Layer 4 writes many controllers as obliques —
  "s'avacci **lor** divenir **sante**" (6:27), the possessor of a nominalized infinitive;
  "**detto n'**avea **beati**" (22:5), object control on a `ne` clitic marked `obl`. The set is an
  acceptance, never an assertion, so widening it accepts a reading the tree leaves open. An `amod`
  branch was measured alongside it and moved **nothing** (32:11 is already taken by this leg), so
  it was not added.
- **Rule CG — `_gapped_coordinate_oblique`.** "or dal sinistro e or dal destro fianco" (10:27) is
  two obliques with one surviving noun, and Layer 4 records the ellipsis by hanging *both*
  prepositions on it — so the elided phrase is citable only by its adjective. The second `case`
  child is the tree's own evidence, and is the gate. Censused at 56 doubly-marked obliques.
- **Rule CH — `_verb_in_adnominal_slot`.** Rule Z's adnominal leg. A verb Layer 4 attached `amod`
  or `acl` over a nominal is a reduced relative clause, and the derivation reads it as a predicate
  whenever pass 2 can find it — that is, whenever it has an argument child ("che da verdi penne /
  **percosse** traean dietro", 8:30). A participle with nothing but its subject ("come fogliette
  pur mo **nate**", 8:28) is the identical reading with nothing for pass 2 to catch it by, so the
  derivation is silent about the tuple rather than opposed to it. Rule V's `acl` branch already
  accepts the subject such a tuple carries; this closes the tuple side of a predication the checker
  was half-accepting. Conjuncts of one are the same clause coordinated ("e **ventilate**", 8:30).
- **Rule CI — rule AA's host gate.** "ma vidi bene e l'uno e **l'altro mosso**" (8:105): the small
  clause's participle hangs on the *second conjunct* of the object, and rule AA tested the host
  against `derived_args`, which holds only the coordination head. The host is now read through
  rule C's collapse — the 31-34 batch's finding (a gate must read the same edge the derivation
  normalized) applied to a third rule.

### Upstream correction in the same read

**Layer 4 — 1 row** (see [`../dep/CORRECTIONS.md`](../dep/CORRECTIONS.md)): `poste` at 9:5 is
f. pl. and the `fronte` Layer 4 gave it is f. sg., so the participle cannot agree with its own
head; `gemme` is the only nominal in the unit it can modify, and Layer 3's spans agree (**−1**).

### Standing shapes the batch recorded but did not settle

- **The elided verb of speech, unproposed** (6:49 *«E io: "Segnore, andiamo…"»*, 8:91 *«Ond' elli a
  me: "Le quattro chiare stelle…"»*). The census of 152 non-verb clause heads with a `ccomp` child
  found the corpus's artifact **naming the pronoun as the predicate** in the ordinary case
  (inferno 3:13 has four tuples on `elli`), so the derivation is following the convention and these
  two are the LLM omitting it. A candidate rule was killed by that census before it was written;
  round 3 had already measured the prompt-side fix at zero.
- **`Era il secondo tinto più che perso`** (9:97), where Layer 4 makes the comparison's second
  term the root and the predicate participle its subject, while Layer 3 and the LLM both read
  `il secondo` as the nominal. Re-parsing it was worked out in full and **not applied**: every
  arrangement trades the two current violations for two or three others, because the disagreement
  is over which of `tinto` and `perso` heads the predication and the line does not decide. Left
  flagged, in the "structural reason the text does not settle" category.
- **A clause coordinated with `conj` read as a `ccomp`** (7:53, 8:50, 9:72 — three in this batch
  alone). The `sì … che` half of it was censused at 2 and dropped by the 26-30 batch; the
  `advcl`-as-complement half is the same lexical argument-structure judgment rule T deliberately
  leaves flagged.
- **An argument named by a modifier of the derived argument** (10:60, where the LLM's subject is
  `quanta` of "tutta quanta" and the derivation's is `gente`). Rule AI covers the Layer-3 NP-head
  version of this; the raw `amod`/`det` population is 16882, far too broad for the rule to be
  written from one instance.
- **Rule AN's remnant slots** (9:69, 10:60): the derivation assigns a gapped conjunct's remnants
  the coordination head's *role labels*, which is rule AN's measured convention, and the LLM names
  neither. Recorded, not reopened.

## Rules BW-BZ, from reading Purgatorio 1-5 — 506 → 481, −25 (2026-08-16)

Per-position read of all **14** soft violations in Purgatorio 1-5, following the eight-step
procedure in [`PLAN.md`](PLAN.md)'s *How to Read a Batch*. Zero model calls. Purgatorio 1-5 itself
went **14 → 10** (1: 1 → 1, 2: 4 → 3, 3: 1 → 0, 4: 2 → 3, 5: 6 → 3); the corpus went **506 → 481
(−25, −4.9%)**. Four deterministic rules plus 2 Layer-4 rows and 1 case-annex row. `pytest`
**351**, all other layers 0/0.

The smallest batch of the series by base count, and the first outside Inferno. Three of its four
rules are mirror or ordering legs of rules already in the checker, which is the series' standing
pattern; the fourth is a defect in `derive_unit`'s own predicate census.

| rule | shape | census | net |
|---|---|---:|---:|
| **BW** | rule BM's mirror leg: an argument Layer 4 parked in the predicate's `mark` slot | 63 / 19 | −9 |
| **BX** | rule AZ's `missing_arg` leg: the bare adjectival oblique the LLM omits entirely | 44 / 11 | −11 |
| **BY** | the LLM splits one periphrasis's arguments across the lexical verb and its `aux` | 5 | −3 |
| **BZ** | the `conj` chain is walked **before** the pass that would resolve it | 372 | ±0 |

Plus 2 Layer-4 rows and 1 case-annex row (**−2** together).

### The batch's two findings

**1. Rule ordering, for the third time, and now inside the derivation.** The 21-25 batch found two
acceptance rules in the wrong order, the 26-30 batch a rule present in one check and absent from
another, the 31-34 batch a rule's own gate reading the wrong edge. Rule BZ is the same defect in
`derive_unit`'s predicate census: that census has three passes — clause-head deprels, `conj`
chains that resolve to one of those, then argument-bearing verbs — and the `conj` walk asks
"does the chain I hang on end in a predicate?" *before* the third pass has added any. So a verb
Layer 4 attached with an argument deprel of its own ("com' io **rimango** sol, se non **restai**",
purgatorio 4:45, where `rimango` is the `obj` of `rimira`) got its own tuple but its conjunct did
not. **A pass that reads a set another pass writes has to run after it, or again.**

**2. A census of 1 is a census.** Two of the batch's positions produced candidate rules that a
one-line script killed before either was written: the verbless comparison whose head Layer 4 makes
the *marker* itself ("com' om che va", purgatorio 2:130, where `com'` is the `obl` and `om` its
`nmod` — rule AR expects the marker as a `mark` child of the compared nominal) occurs **once**
corpus-wide, and the copular subject/complement exchange ("**Che** è **ciò**?", 2:120, where the
tree and the LLM disagree about which of two nominals is the subject of `è`) is likewise the only
pure `subj`↔`attr` swap in the residue. Both are real reading questions and both stay flagged. The
same script found the `obj`↔`subj` swap at 8 positions across 4 predicates, which is the known
open route — measured here, not opened again.

### The four rules

- **Rule BW — `_marker_slot_argument`.** An interrogative or relative word opens its clause *and*
  fills one of its argument slots, which is a thing one token does and a UD tree cannot say twice.
  Layer 4 records the connective function with `mark`, `mark` is outside `ARG_DEPRELS`, so
  `derive_unit` cannot assert the argument function at all and the LLM's citation is reported as
  an `extra_arg` ("un non sapeva **che** bianco", purgatorio 2:23; "**qual** io fossi", paradiso
  1:68; "sappiendo **quanto** costa", 19:74). Rule BM is the same tension from the other side — an
  *oblique* slot filled with a token Layer 2 calls a conjunction, where the connective reading
  wins — and the Layer-2 POS is what separates the two: a `mark` Layer 2 calls a conjunction is a
  subordinator and stays flagged, a `mark` it calls a pronoun, adjective or adverb is a relative
  or interrogative word. Censused at 63 pronoun-tagged `mark` tokens; 19 standing `extra_arg`
  positions cite a `mark`, 14 of them non-conjunction. Gated on the marker hanging on this very
  predicate, through rule BP's `_hosts_child`.
- **Rule BX — `_depictive_bare_oblique_omitted`.** Rule AZ accepts a depictive adjective Layer 4
  hung on the predicate as a bare `obl` when the LLM names it as the secondary predicate it is;
  this is the leg where the LLM lists it not at all ("mi cominciò **tutto rivolto**", purgatorio
  3:23; "**pien** di sonno", inferno 17:6; "**disïante**", paradiso 5:86). A depictive is an
  adjunct of the predication, not one of its arguments, so the omission is as faithful to the line
  as the naming — the acceptance rule AR already makes for a comparison the tree could only hang
  on the main predicate. Rule AZ's three gates unchanged: no `case` child, adjective POS, the
  predicate's own child. Censused at 44 bare adjectival obliques, 11 of them standing
  `missing_arg` positions, all 11 taken.
- **Rule BY — `_auxiliary_hosts`.** "quel da Esti **il fé far**" (purgatorio 5:77): Layer 4 heads
  the causative on `far` and makes the finite `fé` its `aux`; the LLM writes *two* tuples and puts
  the subject on the finite word, the object on the infinitive. Rule AQ merges an argument
  *citation* landing on an auxiliary onto its lexical head, rules AV/BS accept the *predicate*
  citation when the LLM names only the auxiliary — this is the third combination, the LLM naming
  both and splitting the arguments. Routed through rule X's `_complement_hosted_argument`, so it
  inherits that rule's **role-must-match** gate: relocating an argument onto the finite word of
  one periphrasis is a convention, relabelling it is a second claim. That gate is why purgatorio
  2:66 ("ne parrà gioco", `obl:di` against a derived bare `obl`) is not taken. Population 5, 3
  fired.
- **Rule BZ — the second `conj` walk.** See finding 1. Restricted to **finite** verbs, and the
  restriction is rule BN's own test — would the promoted position carry a tuple at all? A nominal
  conjoined to something the third pass promoted is an ordinary coordinate argument of it
  ("addimandò **licenza** di combatter", paradiso 12:95), and a non-finite conjunct with no
  argument child yields an empty tuple no reading can fill ("del comperare e **vender** dentro al
  templo", paradiso 18:122); ungated, the walk minted predicates at both. A finite conjunct always
  has a subject, overt or pro-drop. Measured **−2 / +2**: it clears the `extra_tuple` at
  purgatorio 21:119 and 4:45, and at 4:45 the tuple it now derives inherits `io` across the `conj`
  while the LLM read a pro-drop ∅, so one reported divergence becomes two. Kept at net zero for
  the same reason as rules BN and AN′ — the derivation is now right about what a predicate is, and
  the disagreement is reported where it belongs. (`restai` is 1sg by Layer 2 and 2sg by sense;
  the form itself does not decide, so Layer 2 was left alone.)

### Two upstream rows, and one annex row

- **purgatorio 5:77, `Esti`** — "**quel da Esti** il fé far": `da Esti` is the epithet's own
  modifier, not an oblique of `far`. `obl<-77.6` → `nmod<-77.1`. −1.
- **purgatorio 5:135, `colui`** — "**salsi colui** che 'nnanellata pria / disposando m'avea":
  `sa`+`si` with a postposed subject, "lo sa colui" — `colui` is the subject, not the object.
  `obj<-135.1` → `nsubj<-135.1`, and the `case` annex row accusative → nominative. −1.

### The ten positions left standing

Genuine reading disagreements, recorded so a later batch can recognise a population:

- **purgatorio 1:102, 2:130, 4:73** — adjuncts the LLM omits: the adverb-preposition cluster
  `intorno ad imo`, the comparison `com' om che va`, and the *second* `obl:da` of an elliptical
  pair ("da l'un, quando a colui **da l'altro fianco**") — the repeated-slot shape `_CONV_REPEATED`
  addresses from the prompt side.
- **purgatorio 2:66** — `ne parrà gioco`: the clitic `ne` read as `obl:di` on the copula against a
  bare `obl` on the nominal predicate. Rule BY relocates, rule L specializes, and neither does
  both.
- **purgatorio 2:120** — "Che è ciò?", the copular swap censused at 1 above.
- **purgatorio 4:45** ×2 — the subject of `restai`, see rule BZ.
- **purgatorio 5:14** ×2 — "che non crolla già mai **la cima**": `crollare` is transitive here and
  Layer 4 is right; the LLM read `la cima` as the subject of an intransitive.
- **purgatorio 5:48** — "venian **gridando**": a gerund of manner Layer 4 calls `advcl` and the
  LLM calls `xcomp`. Censused at 3 with its two siblings (paradiso 1:97, purgatorio 25:122) and
  dropped as too small; it belongs to the standing *`advcl` the LLM reads as a complement* route.

### One test fixture changed

`_comparative_adjunct_fixture` in `tests/test_skel.py` gave its compared nominal an *adjective*
POS, which rule BX now accepts on its own — the near-miss half of rule AR's test stopped failing.
The fixture's nominal is a noun now, so the test pins rule AR's marker gate and nothing else. The
overlap is real in the corpus too and harmless there: both rules accept the same shape, and rule
BX was measured at +0.

## Rules BO-BV, from re-reading Inferno 31-34 — 541 → 506, −35 (2026-08-16)

Per-position read of all **37** soft violations in Inferno 31-34, following the eight-step
procedure in [`PLAN.md`](PLAN.md)'s *How to Read a Batch*. Zero model calls. Inferno 31-34 itself
went **37 → 16** (31: 20 → 8, 32: 8 → 5, 33: 4 → 2, 34: 5 → 1); the corpus went **541 → 506
(−35, −6.5%)**. Eight deterministic rules plus 15 Layer-4 rows, 2 Layer-2 rows, 1 Layer-3 span and
1 case-annex row. `pytest` **342**, all other layers 0/0.

The first batch measured against a base a `--fix` round has moved (§12 of [`PLAN.md`](PLAN.md)),
so these numbers are not comparable with the AG-BN series' — the easy positions of every class the
round's prompts cover are gone from underneath them.

| rule | shape | census | net |
|---|---|---:|---:|
| **BO** | rule AI runs **before** rule D: the weaker rule was silencing the stronger one's other half | — | −2 |
| **BP** | "is this the predicate's own child" reads an `aux`/`cop` head through to its lexical word | 53 | −1 |
| **BQ** | rule BJ's other two orders: the adverb cluster's nominal hangs **bare**, or the preposition is on the adverb | 11 | −6 |
| **BR** | a derived argument buried in a Layer-3 noun phrase the LLM named by its head | 404 / 8 | −8 |
| **BS** | rule Y read from the other end: the LLM names the copula of a nominal predication | — | −4 |
| **BT** | rule AE's embedded side: the clause's own governor is the slot it fills | 765 → 92 | −3 |
| **BU** | the subject a coordination supplies from its **last** conjunct | 74 | −2 |
| **BV** | a `fixed` word of a multiword preposition names the nominal it opens | 196 rows | (below) |

Plus 15 Layer-4 rows, 2 Layer-2 rows, 1 Layer-3 span and 1 case-annex row (**−7** for the retags,
and **−2** for the `con esso` normalization together with rule BV and the inferno 31:143 re-parse).

### The batch's three findings

**1. "Which checks run before a rule" has a third form: a rule's own gate.** The Inferno 26-30
batch found rule AQ correct inside `_classify_divergence` and absent from the membership check
that runs first. This batch found the same normalization missing *inside* a rule. Nine acceptance
rules asked "is this argument the predicate's own dependent" by comparing Layer 4's raw
`head_line`/`head_token` to the predicate's position — but **53 arguments corpus-wide hang on an
auxiliary or a copula** rather than on the lexical verb that carries the tuple ("tre Frison
**s'**averien dato mal vanto", inferno 31:64, where the reflexive clitic is `expl` on `averien`
while the predicate is `dato`). `derive_unit` has reached through that edge since rule AM, and
rule AQ re-keys citations that land on one; the gates were the last place still reading the
un-normalized edge. `_hosts_child` (rule BP) fixes all nine at once. Rule BS is the same
normalization applied to a *tuple*-side gate, and rule BV to the multiword-preposition edge.

**2. Rule ordering cuts the other way too.** The Inferno 21-25 batch found rule V's citation being
rewritten by a collapse that ran *after* it. Here the loss is upstream of that: rule D
(`_drop_nmod_obliques`) and rule AI (`_merge_np_head_citations`) both fire on a given citation the
derivation does not carry, and rule D ran first. Rule D is the weaker answer — it drops the
citation as an accepted `nmod` adjunct and leaves the derivation's own position reported as a
`missing_arg`, so one decision still costs one violation. Rule AI re-keys the citation onto the
derived position and both halves go quiet ("torreggiavan **di mezza la persona**", inferno 31:43,
where Layer 4 heads the oblique on `mezza` and Layer 3 heads the span on `persona`). Rule BO is
the two lines swapped. **When two rules can fire on one citation, the order is a decision, and
only the diff shows which one is making it.**

**3. The mirror leg was measured and dropped — the first time in the series.** "Check the mirror
leg of every rule you write" has been standing advice since the Inferno 16-20 batch and has never
before been declined. Rule BR's mirror (the *LLM* naming a word buried in a phrase both readings
already carry) measured **−6 / +0** and was still dropped: on the derived side both positions are
arguments Layer 4 itself asserts, so "one phrase named twice" is Layer 4's own claim, while on the
given side the only evidence is a Layer-3 span — and Layer 3 is **deliberately over-inclusive**
(see the root [`../PLAN.md`](../PLAN.md), Layer 3: "over-inclusion is correct behaviour"). Two of
the six it removed were LLM errors it silenced for the wrong reason (inferno 16:21, where `sé`
inside `[una rota di sé tutti e trei]` was accepted as the verb's subject; paradiso 13:45, where a
relative clause inside the span swallowed the second conjunct of an object). **A mirror leg is
worth testing every time and is not owed acceptance.**

### The eight rules

- **Rule BO — rule AI before rule D.** Two lines swapped in `_classify_divergence`. Evidence:
  inferno 31:43 and inferno 20:10.
- **Rule BP — `_hosts_child`.** Every child-of-the-predicate gate resolves an `aux`/`cop` head to
  its lexical word. Censused at 53 arguments hanging on an auxiliary; only inferno 31:64 was
  producing a violation at one of the nine gates, which is the cheap half of the finding — the
  other 52 are positions where the gate would have been wrong had anything else diverged.
- **Rule BQ — the adverb cluster's other two orders.** Rule BJ requires the nominal to carry a
  preposition of its own ("fuor **del** dritto amore"). Italian also writes the cluster with no
  preposition at all ("dinanzi **l'altro** e dietro **il braccio destro**", inferno 31:87) and
  with the preposition on the *adverb* ("'n su **lo scoperto**", 31:89), and then the nominal
  hangs bare and rule BJ's gate never sees it. Censused at 11 bare against rule BJ's 150. The
  `mark` exclusion keeps the second term of a comparison out ("vie più là **che 'l punir**",
  paradiso 17:99), which rules BK/BL own.
- **Rule BR — a phrase named once, by its head.** Rule AI merges two citations of one noun phrase
  when the *role* matches; this is the case where it does not. "**Gualandi con Sismondi e con
  Lanfranchi** s'avea messi dinanzi" (inferno 33:33): Layer 3 reads the comitative chain as one
  subject phrase, Layer 4 hangs `Sismondi` off the participle as a second `obl:con`. Gated on the
  outer position being a **derived** argument too *and* one the LLM cited. The structural pattern
  is censused at 404; 8 are positions where the LLM named exactly the head.
- **Rule BS — rule Y from the other end.** Rule Y accepts a nominal with a `cop` child as a
  predication whatever deprel it carries; the LLM sometimes names that predication by the copula
  instead ("e cortesia fu lui **esser villano**", inferno 33:150). Testing the citation through
  `_aux_head` first.
- **Rule BT — the free relative's embedded side.** Rule AE accepts a free relative cited from the
  matrix side; this is the clause's own side. In an embedded question Layer 4 hangs the clause
  **under** the interrogative pronoun ("se vuoi saper **chi son cotesti due**", inferno 32:55), so
  the word filling the embedded predicate's complement slot is, in the tree, its governor. 765
  predicates are `acl:relcl` under a pronoun, but nearly all are ordinary correlatives where the
  antecedent is emphatically *not* an argument of the clause; the discriminator is the second
  pronoun, and requiring the clause to hold none leaves **92**.
- **Rule BU — the subject the last conjunct supplies.** "per fuggir lui **lasciò** qui loco vòto /
  **quella ch'appar di qua**, e sù ricorse" (inferno 34:125): `lasciò` has no subject of its own,
  so `derive_unit`'s step 3 walks the conj chain *up* and inherits one from three predicates away,
  while the only overt `nsubj` Layer 4 records is on the conjunct *below* it. Rule AT's direction
  reversed, for the one case where the derivation has no subject of its own to defend. Censused at
  74 coordination heads whose conjunct carries the only overt subject.
- **Rule BV — a multiword preposition's own words are not arguments.** `_prep_stack_nominal`
  re-keys a citation landing on a `fixed` member onto the nominal the cluster opens, the same
  merge rules AQ and BJ make. Entered only from a `fixed` member, so a plain `case` preposition is
  untouched — a first, broader version that also walked from `case` re-keyed five citations onto
  the predicate itself and was narrowed.

### Two candidates measured and dropped

- **The `da` + infinitive gerundive** ("ché non è impresa **da pigliare** a gabbo", inferno 32:7,
  where `impresa` is the infinitive's notional object). Censused at **8** corpus-wide, and the
  role the host fills is not constant across them — object at inferno 32:7 and paradiso 27:92,
  but an oblique at purgatorio 15:144 ("loco da cansarsi") and 17:56 ("via da ir"). A rule
  accepting any role on a population of 8 is not a rule; left flagged.
- **Rule BR's mirror leg**, −6 / +0, dropped on the reasoning in finding 3 above.

### Standing shapes the batch recorded but did not settle

- **A subject inherited across an adversative coordination** (inferno 31:32, "non son torri, ma
  giganti, / e son nel pozzo"): the second `son`'s subject is `giganti`, the *predicate nominal*
  of the negated first clause, and neither reading finds it — the derivation propagates `torri`
  and the LLM names the quantifier `tutti quanti` that follows two lines later.
- **A prepositional phrase as a copula's complement** (inferno 34:43, "la destra parea **tra
  bianca e gialla**"): Layer 4's `obl:tra` has a real preposition in it, and `parere` has no other
  slot for it. Both readings are defensible and the line does not decide.
- **`qual che fosse`** (inferno 31:85): Layer 4 tags `qual` as a second `mark` alongside `che`,
  which leaves `fosse` with no complement; the LLM reads `qual` as the complement. A one-instance
  Layer-4 question, not censused.
- **The elided speech verb at a pronoun** (inferno 31:21, "ond' io: «Maestro, dì, …»"): the
  derivation mints the predicate at `io`, which the Inferno 21-25 batch censused at 164 and
  settled as reading error when the LLM omits it. This is one of the omissions.
- **Rule BR's own trade** (inferno 6:20, "de l'un de' lati fanno **a l'altro schermo**"): Layer 3
  reads `[l'altro schermo]` as one span, so rule BR accepts the LLM's silence about the dative.
  The span is Layer 3 being over-inclusive as designed; recorded rather than split, because
  splitting it is a Layer-3 judgment this batch did not census.

### Upstream corrections in the same read

**Layer 4 — 15 rows** (see [`../dep/CORRECTIONS.md`](../dep/CORRECTIONS.md)): a prepositional
phrase attached to the wrong clause (inferno 31:89, 2 rows), an embedded question attached to the
outer verb of speech rather than the inner one (32:44), a subject read as a modifier inside the
object phrase (34:105, 2 rows), an object read as the following clause's subject (31:143, 2 rows),
and the **`con esso` normalization** (9 rows across 4 cantos in 3 canticles). **Layer 2 — 2 rows**:
the correlative `Qual` at 31:136, a pronoun where the 19 other `quale` tokens in the same `advmod`
slot are adjectives, and `udi'` at 32:19, a 1sg remote past that had been read as a 2sg imperative.
**Layer 3 — 1 span**: `[il sol tragitto]` at 34:105 split into `[il sol]` and `[tragitto]`.
**Case annex — 1 row**: 31:136.1 `Qual` dropped, since the token is no longer a pronoun.

The inferno 31:143 re-parse is the batch's honest trade: making `Lucifero con Giuda` the object of
`divora` rather than the subject of `sposò` removes one violation and adds one, because the LLM
had read `con Giuda` as `sposò`'s oblique. The count does not move; the parse is right.

## Rules BJ-BN, from re-reading Inferno 26-30 — 691 → 650, −41 (2026-08-15)

Per-position read of all **23** soft violations in Inferno 26-30, following the eight-step
procedure in [`PLAN.md`](PLAN.md)'s *How to Read a Batch*. Zero model calls. Inferno 26-30 itself
went **23 → 11**; the corpus went **691 → 650 (−41, −5.9%)**. Five deterministic rules, two legs
added to rules already in the checker, one applied where a rule had not been reaching, plus 4
Layer-4 rows and 1 Layer-2 row. `pytest` **326**, all other layers 0/0.

| rule | shape | census | net |
|---|---|---:|---:|
| **BJ** | the adverb-preposition cluster ("fuor **del** dritto amore") names one oblique, from either word | 147 | −21 |
| **BK** | rule AR's other marker: `che` opens the second term of a comparison, and it is an adjunct | 51 | −4 |
| **BL** | rule AR's other order: `sì come` is one word, so the comparison is what the marker opens | 107 | −1 |
| **BM** | an oblique whose filler Layer 2 calls a **conjunction** is the clause's connective | 37 | −11 |
| **BN** | a conjunction in a clause-head deprel with no arguments is a connective, not an elided predicate | 14 | ±0 |
| **BI**′ | rule BI's third host deprel: the perception verb's infinitive written as a plain `obj` | 7 | −1 |
| **AN**′ | rule AN's clause-head leg: a gapped comparison promoted to `advcl` heads no predicate | — | ±0 |
| **AQ**′ | rule AQ applied to the *membership* check, which runs before the merge | 2 | −2 |

Plus 4 Layer-4 rows and 1 Layer-2 row (**−3 / +2** together).

### The batch's three findings

**1. A rule can be right and simply never reach the check that reports the position.** Rule AQ
maps an argument citation landing on a `cop`/`aux` onto its lexical head, and has done since the
Inferno 11-15 batch — but only inside `_classify_divergence`. The *membership* check ("argument
(87, 4) for role obj heads no NP/pronoun/predicate") runs earlier, on the raw row, and was
reporting the un-normalized position at inferno 28:87 and paradiso 1:61. This is the Inferno
21-25 batch's ordering finding in a new form: there it was two rules in the wrong order inside
one pass, here it is one rule present in one pass and absent from another. **Ask of every rule
not only what it does with a plural or a normalized citation, but which checks run before it.**

**2. The largest mover was a shape a previous route had deliberately deferred.** The Layer-4
prep-stack normalization of 2026-08-14 rewrote 161 multiword-preposition clusters to one UD shape
and explicitly excluded the ~40 whose opening word Layer 2 calls an *adverb* (`dentro a`,
`dinanzi a`, `fuor di`, `di là da`), recording it as "a Layer-2/4 tension to decide separately if
it ever matters". It mattered: censused at 147 clusters, they were producing violations in both
directions — the derivation naming the adverb where the LLM names the nominal (inferno 30:38),
and the derivation naming nothing at all where the adverb sits in an `advmod` slot (28:68). Rule
BJ settles it at Layer 5 without touching Layer 4, by merging the citation onto the cluster head
exactly as rule AQ merges an auxiliary citation, and by feeding the cluster's inner preposition
into rule O's lemma set so `di là **da**` reads as the one complex preposition it is. **A
deliberately deferred upstream tension is a Layer-5 population; census it rather than waiting for
the upstream decision.**

**3. Two of the five rules make the derivation more correct at no gain in the count, and one
upstream fix costs a position.** Rule BN stops `derive_unit` minting a predicate at a bare
connective (`Onde` as `advcl`, inferno 29:124) — −2 `missing_tuple`, +2 `extra_tuple`, because at
purgatorio 33:91 and paradiso 25:19 the LLM had proposed exactly the tuple the derivation was
inventing. Rule AN's clause-head leg does the same for a gapped comparison promoted to `advcl`.
And correcting `scardova` (inferno 29:83, below) removed one violation and added one, because the
LLM's rows for that unit were written against the mistagged verb. All three are the honest trade
rule AM recorded: **the count is not the measure, the correctness of the parse is.**

### Rule BJ — the adverb-preposition cluster

`_merge_adverb_cluster_citations` + `_adverb_cluster_head` in `dante_corpus/skel.py`. Italian
builds complex prepositions out of an adverb plus a simple preposition. Layer 4 hangs the adverb
on the predicate and the phrase's nominal under the adverb, so the two words are two citations of
one adjunct:

- "che divenne / al padre, **fuor del dritto amore**, amica" (inferno 30:38-39) — derived
  `obl=(39,3)` on `fuor`, given `obl:di=(39,6)` on `amore`;
- "**innanzi a li altri** aprì la canna" (28:68) — the adverb is `advmod`, so the derivation
  produced nothing and the LLM's `obl:a` on `altri` was an extra argument;
- "da **qui innanzi**" (29:22-23) — both members are adverbs, and the two readings picked
  different ones, producing a `missing_arg` and an `extra_arg` at the same position.

The merge is onto the cluster head with the role carried across unchanged, so a genuine role
disagreement still surfaces; rule J then accepts the `advmod` half, and rule L or rule O settles
the label. `case_children` is taken *before* the cluster lemmas are aggregated, so rule L's gate
("the derivation could not have emitted a lemma here") still means what it says — measured: with
the aggregation before that line the rule scored −21/**+6**, after it −21/**0**.

### Rules BK and BL — rule AR's other marker and other order

Rule AR reads an oblique off a *verbless* comparative clause as the adjunct it is. Two of its
legs were missing:

- **BK**: the marker can be `che`. "vedesse altro **che la fiamma sola**" (inferno 26:38),
  "guizzando più **che li altri suoi consorti**" (19:32), "ogn' uom v'è barattier, fuor **che
  Bonturo**" (21:41). Censused at 51 corpus-wide — every one a comparative or exceptive second
  term. Only the *argument* leg takes `che`: a `che`-marked clause on the predicate is an
  ordinary complement clause, so the correlative branch stays `come`-only.
- **BL**: the correlative can stand *before* the marker. Rule AR's `come … sì` branch places the
  compared nominal between the two, which is the order at inferno 13:43; `sì come` (censused at
  107) is one word, and the comparison is simply what the marker opens. Gated to the marker's
  next token but for its determiners, so the predicate's other obliques stay its own ("sì come
  nuvoletta, **in sù** salire", 26:39). Worth −1 today: the shape is common, the divergence is
  not.

### Rule BM — a connective in the oblique slot

`_conjunction_oblique`. "Nel tempo **che** Iunone era crucciata" (inferno 30:1), "**onde**
Cleopatràs lussurïosa" (14:54), "**per che** no i volle Gedeon compagni" (purgatorio 24:125): the
relative adverb is the clause's link, and Layer 2 tags it a conjunction for that reason, but
Layer 4 parks it in an `obl` slot. Restricted to the oblique — the same census finds 147 `nsubj`
and 61 `obj` conjunction-tagged tokens, and those are relative pronouns doing real argument work
that both readings name. This is the tail of the known Layer-2 route (relative `che`/`onde`
tagged `conjunction`, 247 tokens), which needs a model read of the `case` annex to settle
properly; until then an adjunct slot filled by a conjunction is not something the derivation can
assert. −11.

### Rule BN and rule AN's clause-head leg — what is not a predicate

Both in `derive_unit`'s step 1. A token Layer 2 calls a **conjunction**, in a clause-head deprel,
with no arguments of its own is a connective ("**Onde** l'altro lebbroso … rispuose", inferno
29:124): the derivation minted a predicate there and then reported the LLM for not proposing a
tuple with nothing in it. The `conj` branch already refused to promote a coordinating conjunction
for exactly this reason. Rule AN's leg is the same refusal for a *gapped* clause whose head is
not a conjunct: "come coltel [fa] le scaglie di scardova" (29:83) is `advcl` with an `orphan`
remnant, and unlike the `conj` case there is no coordination head whose slots the remnants could
fill a second time.

### Rule BI's `obj` branch

"Io vidi **due** sedere a sé poggiati" (inferno 29:73). Rule BI takes the accusative-and-
infinitive's shared nominal when Layer 4 writes the infinitive as an `xcomp`/`ccomp`; Layer 4
also writes it as a plain `obj`. Gated on Layer 2 calling the host an **infinitive**: the census
finds 35 `nsubj` tokens under an `obj`-attached verb, of which 28 are finite clauses whose
subject is the embedded clause's own and nobody's matrix object. −1, after the Layer-4 retag
below made the position reachable at all.

### Rules censused and dropped, and shapes left standing

- **An `iobj` ↔ `obl:a` equivalence** (inferno 28:76, "fa saper **a' due miglior** da Fano" —
  the LLM cites the NP head `miglior`, the derivation the Layer-4 head `due`, and the roles
  differ too). Both halves would be needed: extending rule AI to pair citations in *different*
  roles, and extending rule N to a derived `iobj`. The role pair `iobj`/`obl:a` occurs **0** times
  as a role_mismatch corpus-wide, so the second half has no population and the first is the open
  NP-head route, which asks for a census before AI is widened. Left standing.
- **The elided speech verb** (inferno 26:70, "Ed elli a me: «…»") — censused at 164 in the
  Inferno 21-25 batch and dropped there; the four omissions are reading error. Still true here.
- **Quoted-clause and parenthetical `ccomp`** (inferno 27:101 "fa **sì come** … getti",
  29:63 "**secondo che** i poeti hanno per fermo", 30:59 "non so io **perché**"): three different
  shapes in which the LLM promotes an `advcl`, a parenthetical, or a bare interrogative to a
  complement of the matrix verb. Genuine reading disagreements; Layer 4's `advcl` is right.
- **The `là` obliques** (inferno 27:46, 28:15): locative adverbs the LLM omits — the
  `missing_arg_adverb` residue, prompt-side, and unmeasured until the fourth round.

## Rules AZ-BI, from re-reading Inferno 21-25 — 834 → 691, −143 (2026-08-15)

Per-position read of all **44** soft violations in Inferno 21-25, following the eight-step
procedure in [`PLAN.md`](PLAN.md)'s *How to Read a Batch*. Zero model calls. Inferno 21-25 itself
went **44 → 16**; the corpus went **834 → 691 (−143, −17.1%)**, the largest batch on record.
Nine deterministic rules, 20 Layer-4 rows and 5 Layer-2 rows; `pytest` 311, all other layers 0/0.

| rule | shape | census | net |
|---|---|---:|---:|
| **AZ** | rule R's mirror leg: a depictive adjective Layer 4 hung on the predicate as a **bare `obl`** | 43 | −13 |
| **BA** | `derive_unit` gave one predicate **two** subjects and the LLM named one of them | 99 | −41 |
| **BB** | rule V's coordination leg: every conjunct of a controlled infinitive's subject, read through rule C | — | −26 |
| **BC** | an `advmod` whose filler Layer 2 calls a **noun or pronoun** is an oblique | 117 | −14 |
| **BD** | rule AW's third deprel: a reflexive clitic Layer 4 left as `obl` | 35 | −10 |
| **BE** | `flat` collapses onto its head like `conj`/`appos` — a multiword name is one nominal | 31 | (in BB) |
| **BF** | a `cop` edge Layer 4 pointed the wrong way: the non-verb in the `cop` slot is the `attr` | 11 | −8 |
| **BH** | rule M's mirror leg: the pro-drop ∅ subject rule M's relabelling leaves behind | — | −14 |
| **BI** | the accusative-and-infinitive's shared nominal, named from the matrix side | 10 | −10 |

Rules BB and BE were measured together: BE alone scored −7/+2, the +2 being two subjects rule V
should have accepted but did not, because `_apply_subj_authority` runs *before*
`_collapse_coordination` and the collapse then rewrote an unaccepted citation onto the very
position rule V does accept ("Bellincion **Berti** vid' io andar", paradiso 15:112). Testing rule
V's candidate set through `_coordination_head` as well closed both directions: −23, 0 newly
flagged.

### The batch's three findings

- **Two more mirror legs, and a third kind of half-written rule.** AZ is rule R looking at the
  other deprel Layer 4 uses for the same construction, BD is rule AW's third deprel, BH is rule M's
  own leftover — 37 positions between them. But BB is new in kind: rule V was not *missing* a
  direction, it was **applied once where the shape supplies several citations**
  (`_subj_arg` returns the first `subj` it finds, and a coordinate subject has three). The
  Inferno 16-20 batch's "check the mirror leg" now has a companion: **check the plural** — when a
  rule pops one citation out of a map, ask what happens when the shape produces two.

- **Rule ordering is itself a defect surface.** The BE/BB interaction was invisible from the
  count (−7 looked like a clean win) and only the violation *diff* named it. Normalization
  (`_collapse_coordination`, `_merge_np_head_citations`) runs after `_apply_subj_authority`, so
  any rule that tests a raw citation for membership must test the normalized one too.

- **Two censused rules were dropped.** A `missing_tuple` acceptance for the elided verb of speech
  ("per ch'io: «Maestro, fa che …»", inferno 24:72, where `derive_unit` mints a predicate out of
  the bare pronoun): the census found 164 pronoun clause heads with a `ccomp`, and the LLM
  proposes a tuple for nearly all of them, so the corpus's own convention is to propose them and
  the four omissions are reading error. And a `parataxis`/result-clause `ccomp` acceptance
  ("e fé sì lor, **che** ciascun se ne loda", 22:84): population **2**.

### The upstream retags, and the honest trades

20 Layer-4 rows and 5 Layer-2 rows were corrected in the same session (see
[`../dep/CORRECTIONS.md`](../dep/CORRECTIONS.md) and
[`../morph/CORRECTIONS.md`](../morph/CORRECTIONS.md)). Measured together: **−11 / +4**. Three of
the four new positions are the retags doing their job — a more correct parse that the artifact
now visibly disagrees with, which is the trade rule AM already put on the record:

- inferno 22:32 `'ncontra` was Layer-2 tagged a *preposition*; it is the impersonal verb
  `incontra`. Correcting it makes `derive_unit` propose a predicate the LLM (reading a
  preposition) never proposed — a `missing_tuple` that is now correctly attributed.
- inferno 24:22 `aperse` was tagged an *adjective*; "Le braccia aperse" is "he opened his arms",
  so `braccia` is its object, and the LLM's participial reading is now the divergence.
- inferno 25:68 `ti` in "come ti muti" stood as `nsubj`; a reflexive clitic is not a subject, and
  with it corrected the LLM's `attr` on the clitic is the divergence rather than the derivation's.
- inferno 24:125: retagging the gapped `non umana` onto `Vita` moved a violation from `piacque`
  to `son` without changing the count. `son` (1sg) inherits `Vita` across `conj` and rule AG does
  not drop it, because `dep.subject_agreement` calls a **coordinated subject** undecidable — see
  the deferred route below.

### A measured `dep.subject_agreement` refinement, deferred

The "coordinated subject" exclusion suspends the whole agreement test, but a coordination of
nominals admits a plural *number* over a singular first conjunct — it says nothing about
**person**. Restricting the exclusion to number only was implemented and measured: `dep --check`
0 → **12** soft violations, every one a real Layer-4 question (inferno 2:33, 8:28, 21:121, 25:36;
purgatorio 4:102, 5:82, 10:62, 23:113, 29:37; paradiso 14:125, 19:12, 31:96). Reverted: the
standing invariant is `dep --check` 0, and clearing those 12 is a read of its own. Recorded here
so the next session does not re-derive the measurement.

## The second Phase 6 `--fix` round — 1409 → 1247, −162 (2026-08-14, user-run)

`make -C skel fix` over the 841 units flagged at 1409 — the first pass carrying the
`extra_arg_adjective` micro-prompt. Measured exactly as the previous round: from a `git worktree`
at the pre-`--fix` commit (`src/` symlinked in, since the per-canticle source directories are
generated, not tracked), diffed against the working tree at the parse-unit level
(`dep.sentence_groups`).

| metric | measured |
|---|---|
| units flagged before | 841 |
| units flagged after | 765 (**−76 cleared outright**) |
| units improved | 62 |
| units unchanged | 703 |
| units that got *worse* | **0** |
| units newly flagged | **0** |
| soft violations removed | **162** (1409 → **1247**, −11.5%) |
| files touched | 76 (161 insertions / 158 deletions) |

Per `_violation_subclass`, which is what `_CLASS_PROMPTS` is actually keyed by:

| subclass | before | after | Δ |
|---|---|---|---|
| `extra_arg` | 597 | 535 | −62 (−10.4%) |
| `missing_arg` | 522 | 465 | −57 (−10.9%) |
| `role_mismatch` | 132 | 115 | −17 (−12.9%) |
| `extra_arg_adjective` | 65 | 52 | −13 (−20.0%) |
| `missing_tuple_nominal` | 40 | 39 | −1 (−2.5%) |
| `extra_tuple_adjective` | 17 | 13 | −4 (−23.5%) |
| `extra_tuple` | 14 | 12 | −2 (−14.3%) |
| `membership` | 8 | 7 | −1 (−12.5%) |
| `extra_tuple_adverb` | 7 | 4 | −3 (−42.9%) |
| `missing_tuple` | 7 | 5 | −2 (−28.6%) |

Two readings of this table:

1. **Per-unit yield halved** — 0.193 violations removed per unit flagged before, against the first
   round's 0.505. This is the provenance law of yield restated: the first round consumed the easy
   population of every class it had just been given a prompt for, and this round faced its residue.
   A third round run now would repeat the same pattern at a lower rate again, so none is queued;
   the next pass should follow new checker rules or a sharpened prompt rather than precede them.
2. **`extra_arg_adjective`'s −20.0% is not a verdict on the prompt.** Its sibling
   `extra_tuple_adjective` scored −54.1% on *its* debut, but against an untouched population; this
   class's 65 instances were already the residue of a class the first round had worked over.
   Whether the remaining 52 are prompt weakness or genuine reading disagreements is a question for
   a per-position read, not for another pass.

Two representative repairs from the diff, one of each shape the round produced: Inferno 3:13
replaced an empty placeholder row (`13 0 …`) with a four-tuple predicate on `elli`, closing a
`missing_tuple`; Inferno 6:70 dropped a spurious `attr` on `terrà` (`extra_arg`) while 6:72
specialized a bare `obl` to `obl:di` (`role_mismatch`).

Checks after the round: `skel --check` 0 hard / **1247** soft, `dep --check` 0 hard / 18 soft,
`case --check` 0 hard, `np --check` 0/0, `morph --check` 0/0, `pytest` 243 passed. No CRLF in any
rewritten TSV.

## Rule AG, from re-reading Inferno 4-6 — 1452 → 1409, −43 (2026-08-13)

The fourth per-position read of this kind (after rule V's twelve, rules W/X's five, rules
Y-AF's twenty-six), over **all 19 remaining soft violations in Inferno 4-6** (two of the
original 21 — 6:54, 6:87 — turned out to be the same bug, see below, and are not part of the
19). One checker rule, one cross-layer correction; no model call.

| kind | before | after | Δ |
|---|---|---|---|
| `extra_arg` | 661 | 662 | +1 |
| `missing_arg` | 566 | 522 | **−44** |
| `role_mismatch` | 132 | 132 | 0 |
| `missing_tuple` | 47 | 47 | 0 |
| `extra_tuple` | 38 | 38 | 0 |
| **total** | **1452** | **1409** | **−43** |

`dep`/`np`/`morph`/`case --check` all unchanged (`dep` still 0 hard/18 soft, the standing
subject-agreement residue). `pytest` 243 passed (one fixture's expected flagged-unit count moved
by this rule and was repointed, mechanics unchanged).

### Rule AG (`_apply_subj_authority`'s new branch, −43): gate conj-subject-propagation on Layer-2 agreement

`derive_unit`'s step 3 (conj shared-subject propagation) walks a `conj` chain up to the nearest
ancestor with a subject of its own and inherits it — unconditionally, with no check that the
inherited subject's person/number actually fits the predicate it's being assigned to. "come tu
vedi, a la pioggia mi fiacco" (inferno 6:54, *after* the cross-layer fix below): `fiacco` (1sg) is
attached `conj` to `chiamaste` (2pl, three lines up, a different speaker's address entirely) with
no subject of its own, and step 3 blindly inherited "Voi" — asserting a `missing_arg subj (52,1)`
no reading supports.

Measured over the whole corpus with `dante_corpus.dep.subject_agreement` — the same person/number
test Phase 6's `null_subject` gate uses, extended here with a new `_finite_head_of` helper so a
periphrastic predicate (`potrai vedere`) is checked against the token that actually carries person
(the `aux`, not the non-finite `vedere` itself — inferno 6:87 needed this: `vedere`'s own morph row
has no person, so the naive check called it "undecidable" and rule AG didn't fire until the aux was
consulted): of **1370** conj-inherited-subject candidates, **682 agree**, **461 are undecidable**
(no verdict either way — same as Tier B's discipline, left untouched) and **227 actively
disagree**. An inherited subject in the last group is not a candidate to require, so
`_apply_subj_authority` now drops it from the derived side — but only when doing so doesn't erase
an existing match (`_subj_arg(g) != d_subj` is checked first; an initial ungated version that
skipped this guard *raised* the count from 1452 to 1586 by turning cases where the LLM
independently agreed with the inherited subject into fresh `extra_arg` reports, and was rejected
before landing).

### One cross-layer correction: `fiacco` at inferno 6:54 was tagged an adjective

Layer 2 had `fiacco` (inferno 6:54, "a la pioggia mi fiacco") as the adjective *fiacco* ("weak"),
which cannot explain the reflexive clitic `mi` sitting right next to it — adjectives don't take
clitics. It's 1sg present indicative of *fiaccarsi* ("to wear oneself down"): "in the rain I wear
myself down". Retagged `verb`/`fiaccare`/1sg/present/indicative in `morph/inferno/06.tsv`. This is
what let rule AG's agreement check see `fiacco` as a finite verb at all (an adjective has no
person to disagree with anything) — without the retag the position would have stayed
"undecidable" and unflagged for the wrong reason.

### The other 19: read individually, staying flagged for stated reasons

Every other position in Inferno 4-6 was read against its terzina and is a genuine reading
disagreement or an outright LLM omission, not checker silence — consistent with the Y-AF finding
that `role_mismatch` (both layers speaking) doesn't move, extended here: most of `extra_arg`/
`missing_arg` residue in this sample is the same shape.

- **4:27** (`role_mismatch` ×2): "che l'aura etterna facevan tremare" — `facevan` is plural,
  agreeing with `sospiri` (the antecedent of `che`), not the singular `l'aura etterna`; the LLM
  read the causative construction backwards (subject/object swapped). Real LLM error.
- **6:9, 6:20**: compound subjects/obliques ("regola e qualità", "de l'un... a l'altro") where the
  LLM cited only one of two coordinated arguments. Real omissions.
- **4:37, 6:37**: an adverb-headed oblique ("dinanzi al cristianesmo", "fuor d'una...") where Layer
  4 attaches the adverb itself as the predicate's `obl` and nests a further `nmod` on it; the LLM
  cites only the nested noun, never the adverb. Same shape both times — a plausible future rule,
  but only two instances in this sample; not generalized without a larger read.
- **4:112**: "Genti v'eran" — `v'` (locative "there") is tagged `advmod`, not `obl`, so
  `derive_unit` is silent; the LLM's `obl:in` citation is defensible but uncorroborated by the
  tree. Same shape as rule AB's clitic acceptance, but for a locative adverb-pronoun rather than a
  reflexive; one instance here, not generalized.
- **5:92**: "noi... noi pregheremmo" — a left-dislocated subject echoed by a resumptive `noi`
  Layer 4 tags `expl`; `derive_unit` correctly cites the first `noi`, the LLM cites the second.
  Rule AG doesn't reach this (the predicate's deprel is `root`, not `conj` — this isn't
  conj-propagation, it's a direct `nsubj` at a distance). Same *family* as rule AG but a different
  mechanism; one instance here.
- **6:70**: "Alte terrà... le fronti" — `Alte` is Layer-4 `amod` inside the object NP, the LLM
  reads it as a depictive secondary predicate (`xcomp`) of `terrà`. No `cop`/small-clause marker
  either way — the same attributive-vs-predicative shape as the open `extra_tuple_adjective` route,
  manifesting here as `extra_arg` instead of a whole tuple.
- **4:39, 4:71, 4:135, 4:149, 5:13, 5:48, 5:76, 5:95**: each read individually; all either a real
  role disagreement (both layers assert something, and disagree) or an LLM omission of a second
  argument on a multi-argument predicate. None is checker silence.

**The finding, again**: a per-position read keeps finding one real rule per pass, never the
population the coarse-class count would predict, and the majority of any small sample is genuine
disagreement or omission — `--fix` material, not checker material.

### A third POS-keyed `--fix` class: `extra_arg_adjective`, from the 6:70 shape

6:70's shape — an attributive adjective Layer 4 hangs `amod` inside an argument's own NP, which
the LLM reads as a depictive secondary predicate (`xcomp`/`attr`) of the verb that argument
belongs to — is the same misreading `extra_tuple_adjective` (rules Y-AF) already has a dedicated
`--fix` question and prompt for, one level down: the adjective isn't promoted to its own `Pred`
row here, just wrongly attached as an *argument* of one. Checked against the corpus before
generalizing from one instance: **65 of the 107 `extra_arg xcomp`/`attr` violations cite an
adjective as the argument** — a population the size of `extra_tuple_adjective`'s original 37, so
this is worth the same treatment Phase 6 gave that class.

`skel/skel.py` gained a third POS-keyed `--violation_subclass`/`_CLASS_PROMPTS` entry,
`extra_arg_adjective`, keyed on the **argument's** POS rather than the predicate's (the other two
POS splits key on the predicate itself): `extra_arg`/`role in (xcomp, attr)`/argument tagged
adjective. Its system prompt is `extra_arg`'s own (`_CONV_ROLES`/`_CONV_PRODROP`/`_CONV_RELPRON`)
with `_CONV_ADJECTIVE` fronted, reusing `_ask_extra_arg`/`_apply_extra_arg` unchanged — same
mechanics (`keep`/`<role>`/`drop`), only the system prompt's convention selection differs. The
`_fix_hint` fallback phrasing got the matching third entry. `_CLASS_ORDER` places it before the
generic `extra_arg` so the more specific question is asked where it applies.

**Unmeasured until a `--fix` round runs** — same status Y-AF's two hints shipped with. `pytest`
243 passed (`test_every_ordered_class_has_a_prompt_and_vice_versa` pins `_CLASS_ORDER`/
`_CLASS_PROMPTS` staying in sync); `skel --check` unaffected (0 hard, 1409 soft) since this only
changes which `--fix` question a violation is asked, not the derivation.

## Phase 6 — `--fix` restructured: deterministic first, then one question per class (2026-08-12)

`--fix` was rebuilt because it was the most expensive instrument in the project and the least
efficient. Phase 5w's pass is the reference point: **1290 LLM calls removed 123 violations**, so
roughly 93% of the calls produced nothing. Two properties of the old design account for that, and
both are now gone.

- **It regenerated a whole parse unit and accepted the result only if the whole unit improved.**
  A unit with five violations where the model settled one was discarded entirely.
- **It used one monolithic `SYSTEM_PROMPT` for every violation class.** Phase 5w had already
  measured what that costs — the one class whose instruction was rewritten with a worked example
  and a per-violation hint fell 28.6%, while three prose-only rules in the same prompt moved
  nothing above the pass average. Its finding, *a pass moves a class only when something about
  that class changed*, is an argument against ever asking one prompt to fix everything at once.

`--fix` now runs three stages per flagged unit, cheapest first, each with the same acceptance
gate (zero hard violations and `_is_improvement`), so the no-worse-off guarantee holds stage by
stage rather than only for the pass.

### Stage 1 — deterministic, measured: 2084 → **2011**, −73, **0 LLM calls**

`_find_repairs` grew from two rules to four, and — this is the part that needed deciding —
they are now explicitly split into two tiers.

**Tier A asserts no reading**: it rewrites a label the two sides spell differently while meaning
the same thing. Safe wherever it fires.

| rule | rewrites | fired |
|---|---|---|
| `role_label` (existing) | bare `obl` → `obl:<lemma>` when a `case` child names the preposition | **7** |
| `prep_stack` (new) | one preposition of a stack named instead of another | **4** |

**Tier B asserts a reading**, and may do so only where a signal *independent of Layer 4*
corroborates it. This is the constraint PLAN.md had already stated as a warning — "`--repair`'s
`null_subject` rule would rewrite those rows to the derived position; do **not** run it blind,
since it asserts Layer 4 is right at exactly the positions this round found Layer 4 could be
wrong." The rule is now gated rather than avoided.

| rule | corroborating signal | fired |
|---|---|---|
| `null_subject` (narrowed) | Layer 2's person/number on the derived subject agrees with the predicate (`dep.subject_agreement`) | **31** |

The gate is what makes the rule usable, and the numbers show it is not cosmetic. Of the **67**
∅-subject pairs in the corpus, Layer 2 corroborates only **37**; of the rest, **20 actively
disagree** (a plural subject under a singular verb, a 3rd-person nominal under a 2nd-person
verb), 8 have a non-finite head and 2 a relative-pronoun subject whose person comes from its
antecedent. Running the rule ungated would have rewritten 30 rows on the derivation's say-so at
precisely the positions where the two frozen layers contradict each other.

`dep.subject_agreement` is the *same* test `dep --check`'s subject-agreement rule runs, extracted
from it so the two cannot drift: the checker asks the negative question and this rule the
positive one, and both get "undecidable" as a distinct third answer. **Undecidable is not a weak
yes** — the rule repairs only on "agree".

Stage 1 also verifies itself. `_apply_unit_repairs` applies one rewrite at a time and
re-validates, rolling back anything that does not clear violations cleanly; 6 of the 37
corroborated `null_subject` candidates were rejected that way. The pass is idempotent — a second
run proposes nothing — and `dep`/`np`/`morph`/`case --check` are all unmoved.

`--repair` is now exactly this stage run on its own, sharing one implementation with `--fix`.

### Stage 2 — one narrow question per violation class

The remaining violations in a unit are grouped by class (`_violation_subclass`, the same key
`_HINT_PHRASING` uses, POS refinements included) and each group gets **its own system prompt, its
own question, and its own small answer**, spliced back in at row level and accepted on its own.

| class | asked | answer |
|---|---|---|
| `role_mismatch` | predicate P, argument A — which role does A fill? | one role, or `none` |
| `extra_arg` | is A really P's argument in that role? | `keep` / `<role>` / `drop` |
| `missing_arg` | which token fills P's *R* slot? | `Line.Token`, `0.0`, or `none` |
| `extra_tuple` ×3 | does W head a clause of its own? | `yes` / `no <host> <role>` / `no -` |
| `missing_tuple` ×2 | give the rows for the clause W heads | a small table |

`membership` (8) and `unknown_role` (0) have no prompt on purpose: `_fix_hint` never produced one
for them either, rule AF closed the membership question, and there is nothing left for a prompt
to move.

Three things follow from the shape rather than from any one prompt's wording:

- **An instruction reaches the model at the flagged position by construction.** Each class prompt
  carries only the conventions bearing on it — the adverb rule for an adverb `extra_tuple`, the
  attributive-adjective rule for an adjective one, the elided-speech-frame rule for a nominal
  `missing_tuple`. They are lifted verbatim from `SYSTEM_PROMPT`, which stays unchanged for
  `build`; each is under half its length.
- **Partial credit exists.** Settling one class is committed even when the others fail.
- **The tuple-level classes are asked first** (`_CLASS_ORDER`), because adding or withdrawing a
  predicate changes which arguments there are to dispute.

The independence rule still binds and is now pinned by a test. A question may name the predicate,
the argument the LLM itself cited, and the role slot in dispute — exactly what `_fix_hint`
already disclosed — but **never the derivation's own argument position**, which would reduce the
model to confirming Layer 4 rather than reading the line.

### Stage 3 — whole-unit regeneration, unchanged, as a fallback

The original instrument still runs, but only for units stages 1 and 2 left untouched, and
`--no-whole` disables it so a round can be measured with and without it.

### What is reported

`--fix` now prints **calls and violations-removed per class**, with the ratio. That is the
measurement Phase 5w's finding demands: a pass average conceals which instrument worked, and the
per-class ratio is the only number that says whether a given prompt is earning its call.

### Two things deliberately not done, both measured first

- **`case_corroborated_relabel`** — rewriting the **106** `role_mismatch` rows where the `case`
  annex corroborates the derived role and contradicts the given one (rule U's gate, applied as a
  rewrite instead of an acceptance). It would remove **zero** violations, because rule U already
  suppresses every one of them; what it would fix is artifact hygiene — a wrong label sitting in
  the TSV behind an acceptance. That is a real task, but it is not a `--fix` efficiency task, and
  106 rewrites for no measured effect is not something to slip into a pass. Recorded here so the
  count is not re-derived.
- **`role_alias`** — canonicalizing a role outside the frozen vocabulary. Population is **0**
  (`unknown_role` has stood at 0 since Phase 4b), so the rule would be dead code.

### The `obl:X` vs `obl:Y` class, classified

The 24 remaining preposition-lemma mismatches were classified before `prep_stack` was written,
which is why the rule is gated the way it is:

- **4 are a genuine stack** — Layer 4 chains `in` → `su` → nominal, so the derivation names the
  preposition adjacent to the nominal and the LLM the one opening the phrase. Both are in the
  same `case`-child chain; this is what `prep_stack` rewrites.
- **18 name a preposition the tree does not carry at all** (`obl:in` where only `su` is attached).
  Layer 4 is inconsistent about writing `in su` flat vs chained, so the tree and the reading
  differ about *what is attached* — the `dep/` normalization round PLAN.md reserves, not a
  relabeling. Left flagged.
- 2 are neither.

A first version of the rule accepted the flat-sibling case as well as the chain, on the theory
that both spellings name one PP. It is kept (both prepositions being `case` children of the
nominal is still one stack), but the "LLM names an absent preposition" case is refused — the
distinction is whether the tree contains both lemmas anywhere in the argument's `case` chain, not
whether the two readings *sound* like the same phrase.

### Prediction for the first stage-2 round

Unmeasured until the user runs one. Two things to check against Phase 5w's 1290 calls / 123
removed / 0.095 per call, and neither is "fewer calls" — grouping by (unit × class) will produce
a similar or slightly higher call count:

1. **Per-call yield should rise**, from partial credit and from the truncation retries
   (`_continue_if_missing`) largely disappearing when the answer is three lines rather than a
   whole table.
2. **The per-class table is the result, not the pass average.** A class whose prompt is wrong
   will show it directly instead of being diluted, which is what the last four rounds could not
   see.

### The round, measured: 2011 → **1452**, −559 (2026-08-13, user-run)

`make -C skel fix` 3-way parallel over the 1106 units flagged at 2011 — the first pass against
the restructured stage 2/3 driver. Measured the same way as every prior round, from a `git
worktree` at the pre-`--fix` commit (`src/` symlinked in, since the per-canticle source
directories are generated, not tracked), diffed against the working tree at the parse-unit level
(`dep.sentence_groups`).

| metric | measured |
|---|---|
| units flagged before | 1106 |
| units flagged after | 847 (**−259 cleared outright**) |
| units improved | 197 |
| units unchanged | 650 |
| units that got *worse* | **0** |
| units newly flagged | **0** |
| soft violations removed | **559** (2011 → **1452**, −27.8%) |
| cantos touched | 98 |

Per class, at the coarse `--check` granularity:

| kind | before | after | Δ |
|---|---|---|---|
| `missing_arg` | 796 | 566 | −230 (−28.9%) |
| `extra_arg` | 817 | 661 | −156 (−19.1%) |
| `role_mismatch` | 223 | 132 | −91 (−40.8%) |
| `extra_tuple` | 91 | 38 | **−53 (−58.2%)** |
| `missing_tuple` | 76 | 47 | −29 (−38.2%) |
| `membership` (`argument`) | 8 | 8 | 0 — no prompt, as designed |

But `--fix`'s own unit of work is the finer `_violation_subclass` split `_CLASS_PROMPTS` is keyed
by — the POS-keyed refinement Phase 6 introduced — and that is where the two predictions actually
resolve:

| subclass | before | after | Δ |
|---|---|---|---|
| `missing_arg` | 796 | 566 | −230 (−28.9%) |
| `extra_arg` | 817 | 661 | −156 (−19.1%) |
| `role_mismatch` | 223 | 132 | −91 (−40.8%) |
| `missing_tuple_nominal` | 67 | 40 | −27 (−40.3%) |
| `extra_tuple_adjective` | 37 | 17 | −20 (−54.1%) |
| `extra_tuple_adverb` | 33 | 7 | **−26 (−78.8%)** |
| `extra_tuple` (no prompt) | 21 | 14 | −7 (−33.3%) |
| `missing_tuple` (no prompt) | 9 | 7 | −2 (−22.2%) |
| `membership` (no prompt) | 8 | 8 | 0 — as designed |

**Both predictions held, and by a wide margin.** `skel/skel.log` was again left empty by the
parallel invocation, so the exact call count is not recoverable and the flagged-unit count (1106)
remains only a lower bound on calls — stage 2 asks one question *per class per unit*, so the true
call count is higher, same as every prior round's caveat. Even against that lower bound, **0.505
violations removed per unit flagged** is five times Phase 5w's 0.095 and two and a half times
5s's 0.199 ceiling, the previous high. The true per-call figure is lower than 0.505 (more calls
went into the denominator than 1106), but the gap is too large to be call-count inflation alone —
partial credit is doing real work: a unit with five violations across three classes now keeps
whatever subset of classes the model got right, instead of the whole unit being discarded because
one class failed.

**`extra_tuple_adverb` moved furthest — −78.8%, the largest single-class move of any `--fix`
round on record** — the class Phase 5v/5w had already flagged as prompt-side and Phase 6 finally
gave its own narrow prompt, carrying only the adverb rule and nothing competing for the model's
attention. `extra_tuple_adjective` moved −54.1%, also well clear of the pass average, though less
than half its sibling's rate — the adjective reading is a genuine disagreement (no `cop` edge
asserts a predication either way), so the ceiling on how much a prompt alone can settle is lower
than a rule the tree itself contradicts. The three classes with **no** stage-2 prompt
(`extra_tuple`, `missing_tuple`, `membership`) moved at or near zero, which is the control: the
restructuring's gain is coming from the targeted prompts, not from stage 3's regeneration alone.
`role_mismatch` (−40.8%, mostly the stacked-preposition `prep_stack` gate and `case`-corroborated
swaps reaching further under partial credit) and `missing_tuple_nominal` (−40.3%) also moved well
above the pass average; the two large classes `missing_arg` (−28.9%) and `extra_arg` (−19.1%)
moved at roughly their usual regeneration-resistant rate, though even `missing_arg`'s rate beats
any prior round's pass average. `membership` held at 8, exactly as designed — it has no stage-2
prompt because rule AF already closed it to a checker question, not a data error.

Checks after the round: `skel --check` 0 hard / **1452** soft, `dep --check` 0 hard / 18 soft,
`case --check` 0 hard, `np`/`morph --check` 0/0. **Three `tests/test_skel_fix.py` fixtures needed
updating**, not the driver: they pinned Inferno 1 as "the smallest real case" (one `extra_tuple`
violation), and this round cleared it outright. No canto now has a single flagged unit whose only
violation class is `extra_tuple_adverb`; the smallest surviving single-unit case is Purgatorio 1
(one `missing_arg`), so the three tests were repointed there with matching answer strings —
mechanics unchanged, only the fixture canto and reply text. `pytest` 243 passed after the update.

## Rules Y-AF, from re-reading Inferno 1-3 — 2330 → 2084, −246 (2026-08-12)

The third per-position read of this kind — rule V came out of Inferno 1's twelve, rules W and X
out of its remaining five, and this one out of **all 26 violations standing in Inferno 1-3**. It
produced eight checker rules, seven Layer-2/Layer-4 corrections, and two `--fix` hints. Every rule
is an *acceptance*: no artifact row was rewritten by a rule and no model was called.

| kind | before | after | Δ |
|---|---|---|---|
| `extra_arg` | 954 | 848 | **−106 (−11.1%)** |
| `missing_arg` | 883 | 827 | −56 (−6.3%) |
| `role_mismatch` | 234 | 234 | **0** |
| `extra_tuple` | 137 | 91 | **−46 (−33.6%)** |
| `missing_tuple` | 75 | 76 | +1 |
| `membership` | 47 | 8 | **−39 (−83.0%)** |
| **total** | **2330** | **2084** | **−246 (−10.6%)** |

89 cantos touched. Inferno 1-3 itself 26 → **11**. `pytest` 196 passed (15 new); `dep --check`
0 hard/18 soft, `morph`/`np --check` 0/0, `case --check` 0 hard — all unchanged from before,
though four of those artifacts *were* corrected (see below). Four violations appear in the
after-run that were absent from the before-run, all four at the two positions where a Layer-4
correction made the parse right and left the LLM's reading wrong; they are `--fix` material.

### The finding: `role_mismatch` did not move at all

Every one of the eight rules landed on `extra_arg`, `missing_arg`, `extra_tuple` or `membership`,
and the whole `role_mismatch` class is untouched. That is not an accident of gating. A
`role_mismatch` is the one class where **both layers speak** — Layer 4 attached the argument and
the LLM labelled it — so a divergence there is a real disagreement about the parse, and only a
third read (rule U's `case` annex) has ever settled one. Everything the checker still had to
give was in the classes where **one side is silent**: the derivation says nothing because of
where a token sits in the tree, and silence was being reported as denial.

That also predicts where the remaining residue is, and it is the reverse of the historical
pattern: the two big classes are now `extra_arg` 848 / `missing_arg` 827 with only 234
`role_mismatch`, so the next instrument has to be something other than another silence rule.

### The eight rules, each with its measured move

Measured one at a time, cumulatively, over all 100 cantos:

| rule | function | shape | Δ |
|---|---|---|---|
| **Y** | `_copular_predication` | copular clause head under a nominal deprel | −8 |
| **Z** (tuple leg) | `_verb_in_argument_slot` | a verb form Layer 4 put in an argument slot | −38 |
| **Z** (host leg) | same, at `missing_arg` | the host's citation of that same infinitive | −39 |
| **AA** | `_secondary_predicate_over_argument` | perception/depictive `acl` small clause | −3 |
| **AB** | `_reflexive_clitic_argument` | the reflexive clitic Layer 4 writes `expl` | −63 |
| **AC** | `_inherited_subject` echo | a conj-inherited subject restating the head's | −26 |
| **AD** | `_copular_adverb_complement` | rule R's shape with an adverb, under `essere` | −14 |
| **AE** | `_free_relative_head` | a free relative cited from its two ends | −12 |
| **AF** | dep-corroborated membership | the `membership` residue, closed as a question | −39 |

- **Rule Y** — *"Caccianli i ciel per non esser men **belli**"* (inferno 3:40). The tree gives
  `belli` a `cop` child and then attaches the whole predication as `obl`, which is not in
  `CLAUSE_HEAD_DEPRELS`, so `derive_unit` never proposes it although Layer 4's own `cop` edge
  asserts it. `_elided_copula_nominal` was already the same acceptance for the case with **no**
  copula token; this is the case where there is one, and the copula edge is the whole gate. This
  is the *If a next task is wanted* route the plan ranked first, and it turned out to be worth 8,
  not the 43 the class count suggested — most of that population had already been absorbed by
  rules X and `double_listed`.
- **Rule Z** — *"ch'i' fui **per ritornar** più volte vòlto"* (inferno 1:36), the plan's
  `per`-infinitive route, generalized past the preposition. Layer 2 says the token is a verb and
  Layer 4 put it in an argument slot (`obl`/`nmod`/`nsubj`/`obj`/`advmod`); no reading disputes
  that a verb form heads a predication, so the derivation's silence is about *where the token
  sits*, not about the predicate. Both legs matter: the host leg accepts the derivation's citation
  of the same infinitive as its oblique or subject, which is the identical double-listing the
  `ccomp`/`xcomp` skip has always accepted. Together they are the largest single move here (−77).
- **Rule AB** — *"tal **mi** fec' ïo"* (inferno 2:40). The multiple-`obj` round normalized every
  reflexive clitic onto UD's `expl`, which is outside `ARG_DEPRELS`, so the derivation says
  nothing about a token the LLM reads as the verb's object or dative. Gated to the roles a bare
  clitic can carry (`obj`/`iobj`/`obl:a` — the annex's own accusative/dative pair) and to a
  Layer-2 pronoun: the loose variant, accepting any oblique label, was measured at −67 and
  **rejected**, because the extra 4 name a preposition the tree does not carry.
- **Rule AC** — *"Questa chiese Lucia ... e disse"* (inferno 2:97-98). `derive_unit`'s step 3
  copies the coordination head's subject onto a conjunct with none of its own, and the LLM copies
  its own reading the same way, so a disagreement is the head's disagreement restated once per
  conjunct — here, the subj/obj inversion rules U and W had *already* accepted at `chiese`. This
  is the same "one decision reported twice" shape as rule W, one relation further out.
- **Rule AD** — *"che l'ubidir, se già fosse, **m'è tardi**"* (inferno 2:80). Rule R's own
  docstring cites this line as the case it deliberately leaves undecided, because Layer 2 calls
  `tardi` an adverb. That caution is right under a lexical verb and wrong under `essere`, which
  needs a complement to predicate anything at all. The copula lemma is the whole gate.
- **Rule AE** — *"Galeotto fu 'l libro e **chi lo scrisse**"* (inferno 5:137). Layer 4 puts the
  free relative's *verb* in the matrix role; the LLM cites the *pronoun* heading it, which is what
  the prompt's own relative-pronoun rule tells it to do. Same constituent, same role, two
  citation conventions.
- **Rule AF** — the `membership` class, 47 → **8**. The plan called it "a question about the
  check, not a data error", and the answer was already in the corpus: a token Layer 4 fills an
  argument slot with (`nsubj`/`obj`/`iobj`/`obl`) is admissible as a Layer-5 argument whatever
  its POS, so the check no longer needs Layer 3 to have drawn an NP around it. *"ch'io v'ebbi
  **alcun** riconosciuto"* (inferno 3:58) — a substantivized adjective — is the type. The 8 that
  remain are citations **nothing** corroborates. Five consecutive `--fix` rounds left this class
  at exactly 47, which is what a checker question looks like from the outside.

### Seven cross-layer corrections the same read turned up

Fixed in the same session, per the standing rule; recorded in full in
[`morph/CORRECTIONS.md`](../morph/CORRECTIONS.md), [`dep/CORRECTIONS.md`](../dep/CORRECTIONS.md)
and [`case/CORRECTIONS.md`](../case/CORRECTIONS.md).

- **Layer 2** (4 rows): `tosta` (inferno 2:42) read as an adverb where it agrees with `'mpresa`
  as a predicate adjective; `disio` (2:71) read as the noun `desiderio` where *"ove tornar
  disio"* is the 1sg verb; `che` (2:102) tagged a conjunction where it is the relative subject of
  `sedea` — the family `morph/CORRECTIONS.md` already records; `fier`/`conte` (3:76) read as
  `fare` 1sg + a masculine noun where *"Le cose ti fier conte"* is 3pl of `essere` with a f. pl.
  predicate adjective.
- **Layer 4** (11 rows): `di cui` (2:59) attached to `anima` instead of to `fama`, the noun it is
  the genitive of; `tornar` (2:71) as `nsubj` of a noun, now the `xcomp` of the verb; `che`
  (2:102) as `obl`, now `nsubj`; **the elided speech frame at 3:13** — *"Ed elli a me, come
  persona accorta: «…»"* — still in the un-normalized shape the 2026-08-07 round converted 99
  frames out of, now matching 3:34 and 3:76 exactly; `cose`/`conte` (3:76) rebuilt around the
  corrected Layer 2; `si` (3:126) as `obl`, now the `expl` the corpus writes everywhere else.
- **`case`** (1 row): 2:102's `che`, in scope for the annex for the first time now that Layer 2
  calls it a pronoun, entered as `nominative`.

**Two of these corrections raise Layer 5's count, and that is the honest reading again.** The
speech-frame normalization at 3:13 replaced four violations with one `missing_tuple` (the LLM
never proposed the promoted frame), and the corrected 3:76 turned one violation into three,
because the LLM's reading of that line is simply wrong and the derivation had been wrong in a way
that partly matched it. Both are `--fix` material. See PLAN.md's *A note on Layer 5's count*.

### Two `--fix` hints, and why prose was not enough

Phase 5w measured that a prompt rule moves its class only when an instruction also reaches the
model *at the flagged position*. The `extra_tuple` residue is the case in point: 33 of its 91
violations cite an **adverb**, and the prompt has said "An ADVERB is never a predicate — not a
comparative (più, meno, sì)" throughout. *"più di me degna"* (inferno 1:122) survived it anyway.
So both new instructions ship as POS-keyed `_fix_hint` phrasings with matching prompt prose:

- `extra_tuple_adverb` for the 33, and `extra_tuple_adjective` for the 37 adjectives (31 of them
  attached `amod` inside a noun phrase — *"non fur mai persone **ratte**"*, inferno 2:109), paired
  with a new attributive-adjective rule in `SYSTEM_PROMPT`.
- `missing_tuple_nominal` widened past the elided verb of speech to any **verbless clause**: 32
  of the 76 surviving `missing_tuple` cite a pronoun at the *root* of a verbless sentence, and
  *"e te cortese ch'ubidisti tosto"* (inferno 2:134) is not a speech frame at all. The prompt
  gains the general rule next to the speech-frame one.

Neither hint has been measured yet — that needs a `--fix` round, which is user-run work.

## Rules W and X, from re-reading Inferno 1 — 2408 → 2330, −78 (2026-08-12)

Rule V came out of a per-position read of Inferno 1's twelve soft violations. This is the same
exercise repeated on the **five** that read left standing, and it produced the same result twice
over: two of the five were not what that read called them. No artifact was regenerated, no model
was called, and no artifact row changed — both rules are checker *acceptances*.

| kind | before | after | Δ |
|---|---|---|---|
| `extra_arg` | 995 | 954 | **−41 (−4.1%)** |
| `missing_arg` | 896 | 883 | −13 (−1.5%) |
| `role_mismatch` | 258 | 234 | **−24 (−9.3%)** |
| `extra_tuple` | 137 | 137 | 0 |
| `missing_tuple` | 75 | 75 | 0 |
| `membership` | 47 | 47 | 0 (fifth round unmoved) |
| **total** | **2408** | **2330** | **−78 (−3.2%)** |

44 cantos touched — inferno 24, purgatorio 30, paradiso 24. Inferno 1 itself 5 → **3**. `pytest`
181 passed (8 new); `dep --check` 0 hard/18 soft, `case --check` 0 hard, `np`/`morph --check` 0/0,
all unchanged. **No violation appears in the after-run that was absent from the before-run.**

### What the previous read got wrong

Rule V's write-up classified Inferno 1's survivors as *"two LLM slips that only regeneration
settles, one attachment-level disagreement, and two halves of one Layer-4 question."* Re-read
against the checker rather than against the text, the first two of those three are **checker
silence, not disagreement** — the same shape rule V itself exploited. The lesson is procedural: a
per-position read has to ask *which rule declined to fire*, not only *what does the line mean*.
Reading the line settles what is true; it does not reveal that the checker already knew.

### Rule W (`_case_corroborated_swap`): the swap partner of a rule-U accept

> `lo passo / che non lasciò già mai persona viva` (inferno 1:27)

Layer 4 reads `che` as the subject and `persona viva` as the object — the pass that never let
anyone through alive. The LLM inverted **both**. The `case` annex holds a value for this very
clause: `che` is `nominative`, which corroborates the derived role and contradicts the LLM's, so
rule U accepted that leg and it was never reported. But rule U is scoped to the pronoun position
the annex has a value for, and `persona` is a noun — out of the annex's scope — so the other half
stayed flagged, although it is the *same decision reported twice*: if `che` is the subject, the
argument the LLM also called subject cannot be one.

This is the general case, not a quirk of one line. A `subj`/`obj` disagreement is rarely about one
argument; the LLM inverts both legs of a transitive clause at once, and typically only one leg is a
pronoun. Rule W accepts the second leg when the first was accepted by rule U.

**Gated on the exchange, not on co-presence.** The partner's given and derived roles must be
exactly this argument's, swapped — an annex-contradicted argument that merely happens to sit under
the same predicate adjudicates nothing about the subject question, and an earlier draft that
accepted on co-presence alone would have taken one `dative` position it had no business taking.
One-directional like rule U: the annex siding with the LLM accepts nothing on either leg.

**−24** of the 82 `subj`↔`obj` `role_mismatch`es: 15 `'subj' vs 'obj'`, 9 `'obj' vs 'subj'`.

### Rule X (`_complement_hosted_argument`): the argument side of the copula convention

> `color che **son** contenti / **nel foco**` (inferno 1:118)
> `a costor si vuole **esser** cortese` (inferno 16:15)

The corpus's frozen copular style makes the **copula** the clause head and the predicate
nominal/adjective its `attr`/`xcomp`, so Layer 4 hangs the clause's obliques on the copula. The LLM
follows UD and hangs them on the complement.

The checker already accepted exactly this split **on the tuple side**, twice: `double_listed` (the
complement listed both as the copula's `attr` and as its own tuple) and `_aux_of_derived_predicate`
(the LLM naming the copula where derive_unit names the lexical head). Nothing did the same on the
argument side — and where `derive_unit` promotes the complement too, one convention was costing
**two** violations, a `missing_arg` on the copula plus an `extra_arg` on the complement:

```
inferno 16:15  «a costor si vuole esser cortese»
  missing_arg: 15.6 obl:a (15, 3)   ← dep: costor = obl of the copula esser
  extra_arg:   15.7 obl:a (15, 3)   ← LLM: obl:a on cortese, esser's xcomp
```

Rule X closes both legs. **Gated on both readings agreeing that the pair forms one predication**:
the LLM must list the complement as the host's `attr`/`xcomp` *and* Layer 4 must attach it to the
host with an `attr`/`xcomp` deprel. That is what keeps the rule from accepting an arbitrary
relocation of an argument between two predicates. The role must match as well — relocating the
argument is the convention, relabelling it is a second claim, so `obl:su` against `obl:in`, or
`subj` against `obl`, stays flagged.

**−54**: `extra_arg` −41 (34 oblique, 5 `subj`, 2 `obj`), `missing_arg` −13 (11 oblique, 1 `subj`,
1 `obj`). The `extra_arg` leg is much the larger because a `missing_arg` is only reported for a
predicate both readings propose: where the LLM never proposed the copula as a predicate at all,
only the complement-side leg fires.

**A first gate that was wrong, and why it is worth recording.** Rule X was first written to require
that the complement *not* be a derived predicate, reasoning that if `derive_unit` promotes it too
then the argument had a derived home of its own. That gate rejected 12 of the 17 candidates and
took the count to only 2380. It was backwards: when both are derived, the convention costs *two*
violations rather than one, so those are the cases most worth accepting. The relation between the
two predicates — not the derivation's opinion about one of them — is what makes the split a
notational variant.

### What is left in Inferno 1, and what it costs corpus-wide

Three, and they are the two routes already named:

- **`1:36`, two violations** — `ch'i' fui **per** *ritornar* più volte vòlto`. `per` is a `case`
  child of an `obl` infinitive where UD would have `mark` + `advcl`, so `derive_unit` refuses the
  infinitive predicate status. **Now measured, and the route is small.** The raw case-vs-mark split
  before a non-finite verb is large and genuinely inconsistent (`per` 130 case / 72 mark, `a`
  144/150, `di` 101/74), but nearly all of it lands on an `advcl`/`xcomp` head, which is a clause
  head either way — the derivation is indifferent. Only where the head deprel is
  `obl`/`nmod`/`conj`/`nsubj` does it bite: **98 positions**, of which 22 the LLM also proposes as
  a predicate, for a **total cost of 27 violations** (19 `extra_tuple`, 4 `missing_arg`, 4
  `role_mismatch`) — about 1% of the residue, not the volume route the framing suggested.
- **`1:122`** — `anima fia a ciò più di me degna`. The LLM promoted the comparative adverb `più` to
  a predicate carrying `obl:di [me]`, instead of attaching the standard to `degna`, which it
  otherwise parsed correctly. A plain LLM error in the adverb `extra_tuple` class (33 corpus-wide,
  12 in this `advmod` shape) — the class Phase 5v gave a prose-only prompt rule and 5w measured at
  −5.7%, i.e. no better than the pass average. `--fix` material with a hint attached, per 5w.

### What this predicts about the next `--fix` round

Both rules are acceptances that create **no** LLM-authored rows, so by Phase 5u's rule they remove
precisely the positions regeneration had a chance at and leave a *more* resistant flagged set. The
next `--fix` pass should return a yield at or below 5u's 0.068 floor, not above it. Read that as
confirmation, not as failure.

## Phase 5w: the `--fix` round on the rewritten prompt — 2531 → 2408, −123 (2026-08-12)

Baseline: **0 hard, 2531 soft**, **1290 flagged parse units** — the state left by Phase 5v, which
changed the *instrument* rather than the data: four conventions added to `SYSTEM_PROMPT`, a second
worked example, and a corrected `--fix` hint for a non-verb `missing_tuple`. One full `--fix` pass
over all three canticles, run by the user as `make -C skel fix` 3-way parallel. This is the first
round whose reason to beat the flat rate was not "a previous round created LLM-authored rows".

Measured the same way as Phases 5t/5u: a `git worktree` at the pre-`--fix` commit with the
generated `src/` canticle directories symlinked in, diffed against the working tree at the
**parse-unit** level (`dep.sentence_groups`, which is what `--fix` regenerates).

| metric | measured |
|---|---|
| units flagged before | 1290 |
| units flagged after | 1239 (**−51 cleared outright**) |
| units improved | 90 |
| soft violations removed | **123** (2531 → **2408**, −4.9%) |
| violations removed per LLM call | **≈0.095** |
| units that got *worse* | **0** (Phase 5c's criterion held) |
| units newly flagged | **0** |
| cantos touched | 57 — inferno 22, purgatorio 18, paradiso 17 |
| artifact rows | +348 / −253 |

Per class:

| kind | before | after | Δ |
|---|---|---|---|
| `extra_arg` | 1031 | 995 | −36 (−3.5%) |
| `missing_arg` | 933 | 896 | −37 (−4.0%) |
| `role_mismatch` | 280 | 258 | −22 (−7.9%) |
| `extra_tuple` | 146 | 137 | −9 (−6.2%) |
| `missing_tuple` | 94 | 75 | **−19 (−20.2%)** |
| `membership` | 47 | 47 | **0** (fourth round unmoved) |

### The four prompt rules, scored one by one

This is the measurement Phase 5v set up, and it does not come out uniform. Each rule addressed a
population identified by the Layer-2 POS of the token its violations cite; the same instrument
re-run after the pass gives the verdict:

| 5v rule | population | before | after | Δ |
|---|---|---|---|---|
| the elided verb of speech, promoted to its subject | `missing_tuple` on a **pronoun** | 63 | 45 | **−18 (−28.6%)** |
| — same rule, nominal subject | `missing_tuple` on a **noun** | 16 | 15 | −1 (−6.2%) |
| a non-finite predicate takes its controller's subject | `extra_arg subj (0,0)` | 126 | 123 | −3 (−2.4%) |
| an adverb is never a predicate | `extra_tuple` on an **adverb** | 35 | 33 | −2 (−5.7%) |
| `attr` is not its own predicate | — | \* | \* | not measurable |

\* `attr` never appears in `--check` output at all: it is neither a derived role the checker names
nor a role any surviving `extra_arg`/`role_mismatch` cites. The gloss was worth adding — the label
sat in the vocabulary list unexplained — but this round cannot score it, and no future round can
either without a check that reports it. Recorded so it is not re-measured.

**One rule of the four took, and it took hard.** The promoted speech frame moved 28.6%, six times
the pass average, and its 18 violations are **15% of the entire pass's −123** from a class that is
2.5% of the residue. The other three moved at or below the pass average, i.e. at the rate the
residue moves anyway.

**What separates them is not the subject matter but the form of the instruction.** The speech-frame
rule was the one 5v gave *three* instruments: the prose rule, a **worked example as a table**
(inferno 3:34-35), and a **rewritten `--fix` hint** — `_fix_hint` now recognizes that the
un-proposed predicate is not a verb and stops asking whether a pronoun "heads its own clause". The
other three rules were prose only, added to a system prompt that already ran to several screens.
The finding to carry forward: **a prose rule in a long prompt does not change the reading; a worked
example plus a corrected per-violation hint does.** The hint is the likelier of the two to be doing
the work, since it is the only part of the instrument that reaches the model *at the position that
is wrong*, and it is far cheaper to write than a worked example.

### What this says about the stop rule

**Yield 0.095 per call** — back inside the flat 0.085-0.11 band (5e 0.11, 5q 0.086, 5t 0.085), well
above 5u's 0.068 floor and nowhere near 5s's 0.199. So at the *pass* level the prompt rewrite
returned an ordinary round. At the *population* level it produced the second-largest single-class
move any `--fix` round has recorded (−28.6%, behind only 5t's −22.1% on the same class by a
different route — that class has now moved sharply twice).

This is the same population-not-pass reading 5s/5t/5u converged on, arrived at from a third
direction. The rule that survives all four rounds:

> A `--fix` pass moves a violation class when *something about that class changed* since the last
> pass — new LLM-authored rows in it (5s, 5t), or a new instruction aimed at it that reaches the
> model where the violation is (5w). The pass-level yield is that move diluted by everything that
> did not change, and lands near 0.09 no matter what. Never read the pass number as the verdict on
> the intervention.

And the corollary Phase 5v asked for explicitly: the residue is **not** reading disagreement all
the way down — one prompt silence, correctly closed, was worth 18 violations. But it is also not
prompt-side in bulk: 2408 remain and three of four rules bought nothing. Further prompt rules are
worth writing only with a `--fix` hint attached, and the assistant-side routes (`PLAN.md`'s
copular clause heads under a nominal deprel, `per` + infinitive, the `membership` remainder,
stacked prepositions) are still where the volume is.

Other layers unchanged by this round: `dep --check` 0 hard / 18 soft, `case --check` 0 hard,
`np` and `morph --check` 0/0, `pytest` 173 passed.

## Phase 5v: aligning the build prompt with the conventions the corrections fixed (2026-08-10)

**The point Phase 5u's finding leaves standing**: `--fix` re-runs the *same* prompt over the same
sentences, so a violation class that exists because the prompt never states a convention cannot be
regenerated away — the model re-derives the same reading, correctly, from instructions that do not
mention the rule. Yield stays flat no matter how many rounds are run. Five rounds of Layer-4 and
checker corrections (the `adverb` bug fix, the multiple-`obj` round's `attr`, the subject-agreement
round's ellipsis promotion, rule V's control chain) changed what the corpus *means* by a predicate
and a subject; `SYSTEM_PROMPT` still says what it said before any of them.

Classifying the surviving 2531 by the Layer-2 POS of the token each violation cites — the same
instrument the membership audit used — shows how much of the residue that accounts for:

| class | population | prompt was silent about |
|---|---|---|
| `missing_tuple` | **79 of 94** — 63 pronoun (`io` 30, `elli` 22), 16 noun | the elided verb of speech: the frame is promoted to its **subject** token, which the prompt never mentions, so the model reports no predicate at all |
| `extra_arg subj (0,0)` | **126 of 321** `extra_arg subj` | the ∅ row is described only for a *finite* verb; nothing tells the model that a non-finite predicate takes its controller's subject, which is exactly what rule V now accepts |
| `extra_tuple` (adverb) | **35 of 146** | that an adverb is never a predicate — the rule `is_verb_pos` enforces on the derivation side since the `adverb` bug fix |
| `attr` | small, but the role is in the vocabulary list with **no gloss** | the multiple-`obj` round chose `attr` over `xcomp` for a secondary predicate over an object; the prompt lists the label and never says what it is for |

**~240 violations, ~9.5% of the residue, are positions where the model is being asked the wrong
question.** For comparison, the whole of Phase 5u moved 92.

### What changed in `skel/skel.py`

Four rules added to `SYSTEM_PROMPT`, each stating a convention the corpus had already fixed
elsewhere, plus a **second worked example** (inferno 3:34-35, *«Ed elli a me: "Questo misero
modo…"»*) showing the promoted frame as a table, since it is the one shape no amount of prose
makes obvious:

- non-finite predicates cite their controller's subject; ∅ only when nothing supplies one;
- an adverb is never a predicate (comparative `più`/`sì`, locative `dentro`/`dinanzi`/`fuor`);
- `attr` is the secondary predicate over an argument, and is *not* its own predicate;
- the elided verb of speech is reported with the subject token as the predicate (`subj` ∅,
  quotation as `ccomp`, addressee as `obl:a`).

And one fix to the `--fix` hints: `_HINT_PHRASING["missing_tuple"]` said *"check whether it heads
its own clause"*, which is the **wrong question** for a promoted frame — the token is a pronoun and
does not head a clause in the ordinary sense. `_fix_hint` now takes `morph_rows` and switches to a
`missing_tuple_nominal` phrasing when the un-proposed predicate is not a verb, i.e. for 79 of the
94. Verified on inferno 3:76 (*«Ed elli a me: "Le cose ti fier conte"»*), where the hint now reads
*"'elli' (76.2) may be the subject of an ELIDED verb of speech…"*.

No artifact changed and no count moved: `skel --check` is still 0 hard / **2531** soft, `pytest`
173 passed. **The measurement is the next `--fix` pass** (user-run), and it is the first one with a
reason to beat the flat rate that is not "a previous round created LLM-authored rows": this time
the instrument itself changed. If the yield does not move, the honest conclusion is that the
residue is reading disagreement all the way down and the prompt was never the binding constraint.

### Two classes that turned out **not** to be prompt-side

Both found by the same pass, both recorded here so the next session does not re-derive them:

- **47 `extra_tuple` on adjectives** — *"Di che ciascun di colpa fu compunto"*, *"ch'a la Fortuna
  … son presto"*, *"'l suo nato è co' vivi ancor congiunto"*. The LLM is right and the prompt is
  right: these are copular predicates. Layer 4 attaches the clause head with a **nominal** deprel
  (`obl`, `obj`, `nsubj`) to its matrix, and those are not in `CLAUSE_HEAD_DEPRELS`, so
  `derive_unit` never promotes a token that carries `cop`/`aux` and `nsubj` children of its own.
  This is rule V's shape exactly — checker silence, not disagreement — and it is either a
  derivation rule (a token with a `cop` child is a clause head whatever its own deprel) or a
  Layer-4 correction round (a clause attached as `obj`/`nsubj` should be `ccomp`/`csubj`). It is
  the strongest remaining assistant-side route.
- **14 stacked-preposition `role_mismatch`es** (`obl:in` vs `obl:su` 7, `obl:in` vs `obl:dentro`
  7). Layer 4 is not internally consistent here: in *"Vòlt' era in su la favola"* the two
  prepositions are **chained** (`in` → `su` → `favola`, so the derivation names `su`), while in
  *"trovar dentro al tuo seno"* they are **flat** (`dentro` and `al` both → `seno`, so it names
  `dentro`). No prompt rule can be stated until Layer 4 picks one shape; a normalization round
  there settles the class.

## Phase 5u: the `--fix` round after rule V — 2623 → 2531, −92 (2026-08-10)

Baseline: **0 hard, 2623 soft**, **1347 flagged parse units** — the state left by rule V and the
membership audit (2026-08-09, below). One full `--fix` pass over all three canticles, run by the
user as `make -C skel fix` 3-way parallel. It was run on the condition `PLAN.md` carried forward
from Phase 5t: a cross-layer round had just moved 513 violations and rewritten 81 rows across four
layers. **That condition turned out to be the wrong predictor, and this round is what corrects it**
— see *What this says about the stop rule* below.

Measured the same way as Phase 5t: a `git worktree` at the pre-`--fix` commit with the generated
`src/` canticle directories symlinked in, diffed against the working tree at the **parse-unit**
level (`dep.sentence_groups`, which is what `--fix` regenerates).

| metric | measured |
|---|---|
| units flagged before | 1347 |
| units flagged after | 1290 (**−57 cleared outright**) |
| units improved | 79 |
| soft violations removed | **92** (2623 → **2531**, −3.5%) |
| violations removed per LLM call | **≈0.068** |
| units that got *worse* | **0** (Phase 5c's criterion held) |
| units newly flagged | **0** |
| cantos touched | 54 — inferno 19, purgatorio 23, paradiso 12 |

Per class:

| kind | before | after | Δ |
|---|---|---|---|
| `extra_arg` | 1065 | 1031 | −34 (−3.2%) |
| `missing_arg` | 957 | 933 | −24 (−2.5%) |
| `role_mismatch` | 288 | 280 | −8 (−2.8%) |
| `extra_tuple` | 157 | 146 | −11 (−7.0%) |
| `missing_tuple` | 109 | 94 | **−15 (−13.8%)** |
| `membership` | 47 | 47 | **0** |

### What this says about the stop rule

**The yield, 0.068 per call, is the lowest any `--fix` round has returned** — below 5t's 0.085,
5q's 0.086 and 5e's 0.11, and a third of 5s's 0.199. The prediction `PLAN.md` carried (a
cross-layer round on the order of several hundred violations makes regeneration pay) did not hold,
and the reason is visible in what the 513 were made of:

- 5s and 5t were preceded by rounds that **created LLM-authored error** — the `adverb` bug's
  surfaced `extra_tuple`s, the subject-agreement round's 99 promoted speech frames. Those are rows
  the model itself can settle, and each time the class carrying them moved several times the pass
  average.
- **Rule V created nothing.** It is a checker *acceptance*: it removed 479 `extra_arg` reports
  without touching a single artifact row. The 34 cross-layer corrections behind it are real but
  tiny against 1347 units. So the flagged set that went into this pass was not a mix of fresh error
  and old residue — it was the old residue with a large, model-settleable slice of it deleted, i.e.
  **more** selected for regeneration-resistance than the set 5t faced, not less.

**The corrected rule**: what makes a `--fix` pass pay is a preceding round that *added* LLM-authored
rows to the flagged set, not the size of the violation move. A checker rule that removes violations
by accepting them lowers the next pass's yield, because it removes exactly the positions
regeneration had a chance at. Phase 5q's stop rule stands, in the form 5t left it, with this
addition: measure the *provenance* of a cross-layer round's delta, not its magnitude, before
predicting the next pass.

`missing_tuple` was again the fastest-moving class (−13.8%), the residual tail of the promoted
speech frames 5t settled a third of; `membership` did not move at all, which is the expected result
and confirms the read below that its 47 are a question about the check, not artifact error.

Concretely, the round is the usual mix of arguments the LLM had omitted and predicates it had
over-proposed: inferno 5:23 *«Vuolsi così colà dove si puote»* gained `obl 23.3` (*colà*) on
`vuolsi`, a locative the derivation had and the LLM had not.

As in 5q, 5s and 5t, the per-unit acceptance count is not recoverable — `skel/skel.log` was again
left empty by the parallel invocation — so the table reports the flagged-unit delta (−57) as a
lower bound on accepted units.

Checks after the round: `skel --check` 0 hard / **2531** soft, `dep --check` 0 hard / 18 soft,
`case --check` 0 hard, `np` and `morph --check` 0/0, `pytest` 173 passed. No code changed; the
round is 54 `skel/*.tsv` files, 208 insertions / 174 deletions, line endings unchanged.

## Rule V, the control/participial subject chain — 3136 → 2623, −513 (2026-08-09)

This started as a per-position read of **Inferno 1's twelve** soft violations, asked for as a check
on what the residue actually consists of. Four of the twelve were one thing: `derive_unit` has no
rule for the subject of a **non-finite** predicate. Classifying all 805 `extra_arg subj` violations
corpus-wide — the largest single class, 26% of the residue — showed the same four shapes account
for most of it, and that they are the checker's silence rather than a reading disagreement.

### What derive_unit was doing

`derive_unit` reads a predicate's own dep children. A predicate with no `nsubj` child and no finite
morphology therefore gets **no `subj` row at all** — not "∅", which rule 4 reserves for finite
pro-drop, but nothing. `_apply_subj_authority` already accepted an LLM subject at such a position,
but only from a candidate set built from the **immediate** head, and only when the predicate's own
deprel was `xcomp`/`ccomp`, and only from that head's `subj`/`obj`. Everything else the LLM
resolved was reported as `extra_arg subj`. The classification (all 805, by whether the derivation
also proposed a competing subject):

| shape | n | why the candidate set missed it |
|---|---|---|
| control subject reachable up the chain | 289 | the walk stopped at the immediate head |
| `acl` participle, subject = modified noun | 155 | `acl` was not a control deprel at all |
| LLM says ∅ where derivation has a subject | 127 | genuine disagreement, left flagged |
| head-to-head (derivation has a *different* subject) | 189 | genuine disagreement, left flagged |
| causative: the matrix `iobj` is the causee | 13 | `iobj` was not a candidate role |
| other | 32 | left flagged |

### Rule V

`_control_subject_candidates` walks the predicate's dep head chain (limit 8) and collects, at each
link, the `subj`/`obj`/`iobj` of that ancestor's **derived** rows, plus the modified nominal itself
when the link is `acl`/`acl:relcl`. It stops at the first ancestor that has a subject of its own —
that clause supplies the controller, and a subject taken from beyond it stays flagged. Two readings
of Italian are what the walk encodes:

- **Control / raising through a chain of subjectless non-finite links.** "e molte genti **fé** già
  *viver* *grame*": `grame` is an xcomp of `viver`, itself an xcomp of `fé`, and the controller
  `genti` is `fé`'s object, two links up. Which argument controls is lexical — subject control
  (*vuole partire*), object control (*fé … viver*), the causative's **dative** causee ("ella **mi**
  fa *tremar* le vene") — so all three roles are candidates.
- **The adnominal participle.** "le sue spalle *vestite* de' raggi", "io, *vinto* dal sonno",
  "prieghi *fatti* a Dio": an `acl` participle's subject is the nominal it modifies. 155 positions,
  and the shape is unambiguous — 154 of them `acl`, 1 `acl:relcl`.

A second pass added the case Inferno 1:63 exposed: when the walk reaches a matrix whose own subject
`derive_unit` could only give as pro-drop **∅** ("chi per lungo silenzio *parea* fioco"), the
controller is a referent the derivation never resolved, so it cannot adjudicate the LLM's
resolution of it either. That is exactly what `_apply_subj_authority`'s pro-drop branch already
concludes one level down, and the walk now returns it as an `unresolved` flag (−50 further).

Membership in the candidate set is an **acceptance, never an assertion**: the derivation still says
nothing at these positions, and a subject from outside the set is still reported. Five new tests in
`tests/test_skel.py` pin the participle, the two-link chain, the causative dative, the pro-drop
matrix, and the walk's stop condition (a subject taken past a subject-bearing ancestor still
flags).

### The cross-layer corrections the same audit produced

Classifying the 82 `membership` violations by the Layer-2 POS of the cited token found five shapes
where Layer 2 was wrong about the word, not Layer 5 about the argument: `onde` as a conjunction
where it is a relative pro-form (16), `quantunque` (2), proclitic pronouns tagged as articles (8),
`e'` read as a form of `essere` (2), fused clitic clusters and adverbs tagged as prepositions (7),
plus 2 tags corrected in the other direction. All 37 are in
[`../morph/CORRECTIONS.md`](../morph/CORRECTIONS.md), with the 32 case rows and 4 Layer-3 clitic
mentions they pulled in ([`../case/CORRECTIONS.md`](../case/CORRECTIONS.md),
[`../np/CORRECTIONS.md`](../np/CORRECTIONS.md)) and eight Layer-4 retags
([`../dep/CORRECTIONS.md`](../dep/CORRECTIONS.md)).

### Measured

| kind | before | after | Δ |
|---|---|---|---|
| `extra_arg` | 1544 | 1065 | **−479** (−31%) |
| `membership` | 82 | 47 | **−35** (−43%) |
| `role_mismatch` | 292 | 288 | −4 |
| `missing_arg` | 953 | 957 | +4 |
| `extra_tuple` | 156 | 157 | +1 |
| `missing_tuple` | 109 | 109 | 0 |
| **total** | **3136** | **2623** | **−513 (−16.4%)** |

By step: rule V in its first form −427, the cross-layer corrections −34, the pro-drop extension
−50, inferno 1:112's Layer-4 rows −2. `extra_arg subj` itself went **805 → 327**, of which 127 are
the LLM asserting ∅ against a derived subject. Inferno 1 went **12 → 5**.

`skel --check` 0 hard / **2623** soft; `dep --check` 0 hard / 18 soft; `case --check` 0 hard;
`np --check` 0/0; `morph --check` 0/0; `pytest` 173 passed.

### What Inferno 1's five survivors say about the rest

Two are LLM slips that only regeneration settles (27.3 reads *persona viva* as the subject of "lo
passo che non lasciò già mai persona viva"; 122.5 promotes the comparative adverb *più* to a
predicate). One is an attachment-level disagreement (`nel foco` cited on the predicate adjective
*contenti* rather than on its copula). **Two are one open question**: "fui **per** *ritornar* più
volte vòlto" has Layer 4 treating `per` + infinitive as `obl` + `case`, where UD would have
`advcl` + `mark`, so the LLM's predicate reading of the infinitive is reported as both an
`extra_tuple` and a `missing_arg obl:per`. `missing_arg obl:per` stands at 44 corpus-wide; whether
that convention should change is a Layer-4 question, not a checker one, and it is the next named
route — see [`../PLAN.md`](../PLAN.md).

The `membership` remainder (47) is deliberately untouched: substantivized adjectives (23 before the
round), quoted mention words as the object of a verb of saying ("faceva dir l'un ‘No’"), and
adverbs cited as objects ("non sa **como**"). None of those is a data error — they are all
questions about what the check should admit as an argument, and they need a decision on the check
rather than an edit to an artifact.

## Phase 5t: the `--fix` round after the subject-agreement corrections — 3270 → 3136, −134 (2026-08-09)

Baseline: **0 hard, 3270 soft**, **1575 flagged parse units** — the state left by Layer 4's
subject-agreement round (2026-08-07, below). One full `--fix` pass over all three canticles, run by
the user as `make -C skel fix` 3-way parallel. It was run on Phase 5s's recommendation: a
cross-layer correction round had just moved 424 Layer-4 and 77 Layer-2 rows under the flagged set,
which is the condition 5s measured as the one that makes regeneration pay.

Measured from a `git worktree` at the pre-`--fix` commit (with the generated `src/` canticle
directories symlinked in), diffed against the working tree at the **parse-unit** level
(`dep.sentence_groups`, which is what `--fix` regenerates):

| metric | measured |
|---|---|
| units flagged before | 1575 |
| units flagged after | 1527 (**−48 cleared outright**) |
| units improved | 96 |
| soft violations removed | **134** (3270 → **3136**, −4.1%) |
| violations removed per LLM call | **≈0.085** |
| units that got *worse* | **0** (Phase 5c's criterion held) |
| units newly flagged | **0** |
| cantos touched | 61 — inferno 22, purgatorio 19, paradiso 20 |

Per class:

| kind | before | after | Δ |
|---|---|---|---|
| `extra_arg` | 1580 | 1544 | −36 (−2.3%) |
| `missing_arg` | 985 | 953 | −32 (−3.2%) |
| `role_mismatch` | 305 | 292 | −13 (−4.3%) |
| `extra_tuple` | 175 | 156 | −19 (−10.9%) |
| `missing_tuple` | 140 | 109 | **−31 (−22.1%)** |
| `membership` | 85 | 82 | −3 (−3.5%) |

**Phase 5s's prediction held only for the population that round created, not for the pass as a
whole.** The overall yield came in at **0.085 per call** — indistinguishable from 5q's 0.086 and
5e's 0.11, the flat rate on a *static* residue, and less than half of 5s's 0.199. But the class
breakdown is not flat: `missing_tuple` fell **22.1%**, five times the pass average and the largest
single-class move of any `--fix` round on record, while the two big classes moved 2-3%, i.e. at
their usual regeneration-resistant rate. `missing_tuple` is exactly where the subject-agreement
round's +105 had landed (the 99 promoted speech frames), so the same pattern as 5s — where
`extra_tuple`, the `adverb` bug's population, moved furthest — repeated in miniature.

**The corrected reading of 5s's rule**, which supersedes the version `PLAN.md`'s *Where Phase 5
ended* carried: a cross-layer correction round does **not** raise the yield of the next `--fix`
pass as such. It creates a *sub-population* that regeneration settles at a high rate, and the
pass-level yield is that rate diluted by however much of the flagged set the new population
occupies. In 5s the two 2026-08-03 populations were large against 1659 units, so the pass looked
like a break from the stop rule; here +105 against 1575 units was too small, and the pass reverted
to the flat rate. **Phase 5q's stop rule stands** — with the qualification that it is about the
*old* residue, and says nothing about freshly created LLM-authored error, which is worth
regenerating whatever its size.

What changed, concretely: **33 of the 99 promoted speech frames were taken up by the LLM** and 2
newly appeared (inferno 30:37-38), a net −31. E.g. inferno 3:34 *«Ed elli a me: "Questo misero
modo…"»* went from an empty row to `34.2 elli` carrying `subj (0,0)`, `ccomp 35.1` and
`obl:a 34.4` — the UD ellipsis promotion the subject-agreement round normalized corpus-wide, now
proposed independently by the LLM. The same canto shows the other kind of move: `obl:senza` →
`obl:sanza` at 36:2, the preposition lemma taken from the form the line actually uses.

**Zero units got worse and zero were newly flagged** — the third consecutive round to hold both
(5q, 5s, 5t). As in 5q and 5s, the per-unit acceptance count is not recoverable: `skel/skel.log`
was again left empty by the parallel invocation, so the table reports the flagged-unit delta (−48),
a lower bound on accepted units.

Checks after the round: `skel --check` 0 hard / **3136** soft, `dep --check` 0 hard / 18 soft,
`case --check` 0 hard, `np` and `morph --check` 0/0, `pytest` 168 passed. No code changed; the
round is 61 `skel/*.tsv` files, 303 insertions / 242 deletions.

## Layer 4's subject-agreement round — 3215 → 3270, +55 (2026-08-07)

No Layer-5 change: a new `dep` soft check (an `nsubj` whose person or number contradicts its finite
head's) flagged 173 positions, 155 of which were corrected in Layers 2/4 — see
[`../dep/CORRECTIONS.md`](../dep/CORRECTIONS.md) and
[`../morph/CORRECTIONS.md`](../morph/CORRECTIONS.md). `derive_unit` reads those layers, so the
count moved underneath Layer 5, and, as in the multiple-`obj` round, **it moved up**:

| kind | before | after | Δ |
|---|---|---|---|
| `extra_arg` | 1558 | 1580 | +22 |
| `missing_arg` | 1053 | 985 | −68 |
| `role_mismatch` | 309 | 305 | −4 |
| `extra_tuple` | 174 | 175 | +1 |
| `missing_tuple` | 35 | 140 | +105 |
| `membership` | 86 | 85 | −1 |
| **total** | **3215** | **3270** | **+55** |

`missing_arg` fell by 68 — the derivation now supplies arguments it had been attaching elsewhere —
and the whole of the rise is `missing_tuple`: the 99 **promoted speech frames** ("Ed elli a me:
«…»", where the elided verb of speech makes the subject the clause head) each give `derive_unit` a
predicate the LLM never proposed, exactly as the gapping promotions of the multiple-`obj` round
did. The audit reading of PLAN.md's *A note on Layer 5's count* applies unchanged: this is
`--fix` material — LLM-authored rows against a now-corrected Layer 4 — and `--fix` is user-run
work. Do not "fix" it by reverting the Layer-4 corrections.

The round also started here: it was `skel`'s own 133 `extra_arg subj (0,0)` violations that
exposed the agreement problem. 43 of those had a derived subject that could not agree with its
predicate, which is what made the generalized test worth running over all ~6 000 `nsubj` edges.

## Phase 5s: the `--fix` round the 2026-08-03 work opened up — 3545 → 3215, −330 (2026-08-07)

Baseline: **0 hard, 3545 soft**, **1659 flagged parse units** — the state left by the multiple-`obj`
round and the `adverb` bug fix (both 2026-08-03, below). One full `--fix` pass over all three
canticles, run by the user as `make -C skel fix` 3-way parallel. This is the route PLAN.md's *If a
next task is wanted* had reserved for the user, and the reason to run a third pass after Phase 5q's
stop rule was specific: the 2026-08-03 round had **added two populations that are `--fix` material
by construction** (LLM-authored artifact rows against a now-corrected Layer 4, and the 72
adverb-as-predicate `extra_tuple`s the bug had been absorbing), not the regeneration-resistant
residue 5q measured.

| metric | measured |
|---|---|
| units flagged before | 1659 |
| units flagged after | 1549 (**−110 cleared outright**) |
| soft violations removed | **330** (3545 → **3215**, −9.3%) |
| violations removed per LLM call | **≈0.199** |
| units that got *worse* | **0** (Phase 5c's criterion held) |
| units newly flagged | **0** |
| cantos touched | 91 — inferno 30, purgatorio 30, paradiso 31 |

Per class:

| kind | before | after | Δ |
|---|---|---|---|
| extra_arg | 1687 | 1558 | −129 (−7.6%) |
| missing_arg | 1151 | 1053 | −98 (−8.5%) |
| role_mismatch | 360 | 309 | −51 (−14.2%) |
| extra_tuple | 217 | 174 | −43 (−19.8%) |
| argument | 92 | 86 | −6 (−6.5%) |
| missing_tuple | 38 | 35 | −3 (−7.9%) |

**The prediction held, and this does not reopen Phase 5q's stop rule.** The yield came in at
**0.199 violations per call against 5q's 0.086 and 5e's 0.11** — the first pass to beat that flat
rate, by better than double. The stop rule 5q wrote said *what is left does not respond to
regeneration*; it was measured on a residue that had not yet had a wrong Layer 4 corrected under it.
Every class moved further than in 5q (7.6%/8.5%/14.2% against 4.4%/3.6%/3.4%), and `extra_tuple`
moved most of all (−19.8%) — which is where the adverb bug's +72 had landed. Three of the five
adverb-predicate positions the bug write-up names by hand are now cleared (inferno 11:93 *non men
che saver*, 13:112 *similemente a colui*, 14:44 *fuor che ' demon duri*); 1:122 *più di me degna*
and 21:49 *altrimenti che nel Serchio* still stand. The correct reading is that a regeneration pass
is worth running **after a cross-layer correction round moves the ground under the flagged set**,
not on a static residue.

**Zero units got worse and zero were newly flagged** — the cleanest round on record on both counts
(5q also held the no-worse criterion, but is not recorded against newly-flagged). Line-level counts
do show 49 lines rising, entirely from violations relocating to a neighbouring line inside the same
parse unit; measured at the parse-unit level, which is the unit `--fix` actually regenerates, the
delta is one-directional: **238 units improved, 0 degraded.**

Sample of what changed (inferno 1–2): 1:56 `perder` `subj` → `obj` with `face`'s duplicate `obj`
dropped — the LLM converging on the Layer-4 tree the multiple-`obj` round had just corrected;
1:59–60 the `obl` under fused `venendomi` re-attached as `ripigneva`'s `obl:a`; 2:110/113 the
missing implicit-subject rows (`subj 0 0`) supplied on infinitives and a gerund.

As in 5q, the per-unit acceptance count is not recoverable — `skel/skel.log` was again left empty by
the parallel invocation — so the table reports the flagged-unit delta (−110), a lower bound on
accepted units.

**Current state**: `skel --check` **0 hard, 3215 soft** (down from 17438 at the first full-corpus
measurement, overall Δ14223, 81.6%). `dep --check` 0 hard / 0 soft, `case --check` 0 hard,
`np --check` 0 hard / 0 soft, `pytest` 154 passed.

## The `"verb" in pos` bug: `adverb` matched too — 3509 → 3545, +36 (2026-08-03)

Found while wiring Layer 4's new *at most one `obj` per predicate* rule
([`../dep/CORRECTIONS.md`](../dep/CORRECTIONS.md), same date). Layer 2's `pos` is a `+`-joined
list of components (`verb`, `verb+pronoun`, `adverb`, `conjunction+pronoun+verb`), and three
places in `skel.py` tested it with a plain substring — **`"verb" in "adverb"` is `True`**, so every
adverb in the corpus was being read as a verb:

- `derive_unit`'s **rule 2** ("a non-auxiliary *verb* that itself takes an argument-bearing
  dependent") was promoting adverbs to predicates. The comment above `CLAUSE_HEAD_DEPRELS` says
  *verb*; the code did not.
- `_ccomp_over_a_verbal_argument` (rule for a given `ccomp` against a derived `obj`/`subj`) was
  accepting an adverbial argument as verbal.
- The elided-copula whitelist's "predicate is not a verb" gate was excluding adverbs from a
  whitelist meant to cover exactly the non-verbal predicates.

Fixed by a shared `is_verb_pos(pos)` that splits on non-letters and tests for a `verb`
**component**; two tests pin it (`adverb` and `preposition+adverb` are not verbs, `adverb+verb` and
`conjunction+pronoun+verb` are).

**The count goes up, and every component of the move is an improvement.** By kind: `extra_arg`
1709 → **1687** (−22), `missing_arg` 1156 → **1151** (−5), `role_mismatch` 362 → **360** (−2),
`missing_tuple` 45 → **38** (−7), `argument` **92** unchanged — and `extra_tuple` 145 → **217**
(+72). The +72 are positions where the LLM proposes a comparative or exceptive **adverb** as a
predicate and the derivation, no longer buggy, does not: *non men che saver* (inferno 11:93),
*similemente a colui* (13:112), *fuor che ' demon duri* (14:44), *più di me degna* (1:122), *qui si
nuota altrimenti che nel Serchio* (21:49). Each is an adverb carrying its own comparative standard
as an `obl` child. An adverb is not a predicate in a UD-derived role vocabulary, so all 72 are real
LLM divergences the bug had been silently absorbing by inventing a matching derived tuple. They are
`--fix` material (LLM-authored artifact), not rule material.

Left alone deliberately: the corpus is **not** re-checked for whether those `obl` standards should
attach to the adverb or to the clause head. Both are attested; the rule does not care; and moving
them would be a separate round.

`skel --check`: 0 hard, **3545** soft. `dep --check` 0/0, `case --check` 0 hard, `np --check` 0/0,
`pytest` 154 passed.

## Phase 5r: rule U — the `case` annex as a third read — 3633 → 3465, −168 (2026-08-03)

Phase 5's closing position parked its largest remaining reading-disagreement population with an
explicit reason: deciding it "needs a Layer-2 case feature or a clitic lexicon", and the project
had twice declined to open one. **That feature exists now** — `case/` was built after that verdict
was written and hand-audited against `dep` through the annex's Steps 6-9 — but until this phase
`dante_corpus/skel.py` never imported it. This phase wires it into the checker.

### The measurement (on the post-Step-9 tree, 3633 soft)

Of the **516** `role_mismatch` violations, **210** sit on an argument position the annex holds a
value for. Classifying each by whether that value corroborates the derived (`dep`-side) or the
given (LLM-side) role, under the obvious mapping between the two frozen vocabularies —
`nominative`↔`subj`, `accusative`↔`obj`, `dative`↔`iobj`/`obl:a`, `ablative`/`locative`↔`obl*`,
with `obl:a` deliberately compatible with *both* `dative` and the locative values because Italian
`a` marks both:

| | count |
|---|---|
| `case` corroborates the **derived** side → rule-U candidate | **161** |
| `case` corroborates the **given** side → `dep`-correction candidate | **17** |
| value has no role mapping (`reflexive`/`vocative`/`genitive`/fused `a+b`) | 23 |
| decides neither (both or neither side match) | 9 |

The four biggest buckets are all in the first row: given `obj` / derived `obl:a` with `dative`
(55), given `obj` / derived `subj` with `nominative` (43), given `subj` / derived `obj` with
`accusative` (21), given `obl:a` / derived `obj` with `accusative` (20).

### Rule U (`_case_corroborated_role`), −160

A one-directional acceptance in `_classify_divergence`'s `elif grole != drole:` branch, in the
same shape as rules L/M/N/O: accept the divergence when the annex's value for that argument
position corroborates the **derived** role and *not* the given one. Corroborating both or neither
accepts nothing, and the mirror direction is never an automatic accept — it is the hand round
below. This is the same asymmetry Phase 5j enforced when it rejected rule O's two-directional
variant. `case` data is threaded into the checker the way `dep_index_by_pos`/
`morph_pos_by_position` already are (`validate_unit(..., case_rows=...)`, fed by `skel.py`'s new
`_case_rows`).

**One scope gate, `_bare_pronoun_position`, costs the rule exactly 1 of its 161:** the annex is in
scope for every token whose Layer-2 `pos` *names* a pronoun, fused ones included (601 of the 13113
in-scope positions are `verb+pronoun` and friends), and there `venendomi`'s value is the
enclitic's case while a Layer-5 argument citing that position cites the **verb**. The one instance
this removed is a given `xcomp` / derived `obl` with `ablative` — an infinitive+`ne`, exactly the
scope mismatch the annex's own Steps 8 and 9 left alone by hand. Yield: **3633 → 3473, −160**.

Tests: `tests/test_skel.py`'s `test_case_supports_role_mapping` plus six
`test_classify_divergence_case_*` cases covering the accept, the mirror direction, both-sides,
neither-side, the fused-token gate, and an absent position.

### The 17 `dep`-correction candidates, hand-verified — a further −8

Every position where the annex sides with the LLM against `dep`, read against its terzina. **Ten
`dep` retags** (recorded in [`../dep/CORRECTIONS.md`](../dep/CORRECTIONS.md)) and **four `case`
corrections** (in [`../case/CORRECTIONS.md`](../case/CORRECTIONS.md)) came out of it; the other
**8** are left alone for stated structural reasons, in four families:

- **A copular predicate nominal is nominative too** (5): inferno 7:69.1 *che è*, 24:112.2 *qual è
  quel che cade*, purgatorio 2:120.4 *Che è ciò*, 10:90.3 *L'altrui bene a te che fia*, 23:13.6
  *che è quel ch'i' odo*. `dep` tags the pronoun `attr` (canonicalized to `xcomp`), the LLM calls
  it `subj`, and the annex says `nominative` — but Italian predicate nominals **are** nominative,
  so the value corroborates both readings and adjudicates neither. The mapping cannot separate a
  subject from a copular predicative, and the measurement's "corroborates given" column overstates
  itself by exactly this family. Rule U is unaffected: it is one-directional and never fires here.
- **The tree's preposition is explicit** (1): inferno 12:16.5 *Lo savio mio inver' lui gridò*.
  `lui` carries an `inver'` `case` child, so derived `obl:in` (`_PREP_LEMMA_NORM` folds `inver'`
  into `in`) is what the tree says; the annex reading `lui` as the `dative` addressee of *gridò*
  is a semantic-role read, not a contradiction of the parse. No `dep` error.
- **Fused infinitive+clitic scope mismatch** (1): inferno 21:79.5 *Credi tu... vedermi esser
  venuto*. The annex's `accusative` is `mi`'s; the disputed role is the whole infinitive's. The
  same exception rule U's own gate encodes, and the one Steps 8/9 already established.
- **Comparative standard** (1): paradiso 13:131.5 *sì come quei che stima*. `dep`'s convention
  makes *come* the `advcl` head and *quei* its `obj`; the annex's `nominative` reflects the form,
  not the attachment. Already on record as a left-alone shape in `../case/CORRECTIONS.md`.

**State check.** `skel --check`: **0 hard, 3465 soft** (3633 → 3473 by rule U → 3465 by the
corrections). By kind: `role_mismatch` 516 → **347**, `missing_tuple` 25 → **26** (one retag made
the derivation propose a predicate the artifact does not), `extra_arg` 1649, `missing_arg` 1206,
`extra_tuple` 145 and `membership` 92 all unchanged. `dep --check`: 0 hard, 0 soft. `case --check`: 0 hard. `np --check`: 0/0. `pytest`:
149 passed.

## Layer 3's clitic reconciliation — 3633 → 3635, both at one position (2026-08-02)

Closing Layer 3's stale clitic mentions (see [`../np/CORRECTIONS.md`](../np/CORRECTIONS.md)) moved
this count by **+2**, and both of them are the same position: **purgatorio 20:83**, *poscia c'ha'
il mio sangue a te sì tratto*.

The 94 backfilled `+lemma` mentions and the 6 dropped ones moved nothing — a clitic mention is not
an argument citation, so Layer 5's derivation never reads one. What moved the count was the
**non-clitic** half of the same round: the 2026-08-02 Layer-2 correction had retagged `c'` from
the pronoun `ci` to the conjunction *che* of *poscia che*, and once Layer 3 dropped its `c'` span
and Layer 4 took `c'` `obj` → `mark` (`poscia` `mark` → `advmod`, matching the **27** other
*poscia che* pairs in `dep/`, against the one that reads `mark` + `mark`), the frozen `skel/` row asserting `83.10 tratto obj (83, 2)`
had nothing left to cite:

- `argument (83, 2) for role obj heads no NP/pronoun/predicate` — the membership check.
- `extra_arg: 83.10 obj (83, 2)` — the derivation now yields one `obj` (`sangue`), the artifact two.

**Both flags are correct and neither was closed.** Layer 5's read of this line — `subj` = *sangue*,
`obj` = `c'` — *is* the pre-correction pronoun reading: the subject is the pro-drop *tu* of `ha'`
and `il mio sangue` is the object. Editing the `skel/` row to agree would manufacture the
agreement this layer exists to measure; it is `--fix` work, which is the user's to run. This is the
count moving up because the corpus got better, the same shape as the case annex's first and third
Layer-4 rounds below.

## The `case` annex's Layer-2 round — 3634 → 3633, and Layer 5 confirming two readings (2026-08-02)

The case annex's step 5 finally spent the `morph/` corrections its three earlier steps had
surfaced and parked — 10 hand-verified singletons plus the 58-token comitative family, recorded
in full in [`../morph/CORRECTIONS.md`](../morph/CORRECTIONS.md). **No `skel/` artifact and no
`dep/` row was touched**; the whole delta is Layer 5's deterministic derivation reading a changed
Layer 2.

The net is −1, but the interesting part is that it is **−2 +1**, and both of the closures are
Layer 5's LLM having been right about a position where Layer 2 was wrong:

| | position | violation | why it moved |
|---|---|---|---|
| **closed** | *Purg* 11:137 | `argument (137, 2) for role subj heads no NP/pronoun/predicate` | the LLM read `e'` as the subject of `sostenea`. Layer 2 had it as a form of `essere`, so the argument headed no pronoun. Retagged `egli`/`pronoun`, the violation dissolves |
| **closed** | *Purg* 16:141 | `argument (141, 9) for role obl heads no NP/pronoun/predicate` | the same shape for `vosco`, which Layer 2 had as an `adjective`. Retagged `voi+con`/`pronoun+preposition` |
| **opened** | *Inf* 23:87 | `extra_arg: 87.7 obl (87, 8)` | `seco` is now a pronoun, so `derive_unit` produces an `obl` argument the LLM's skeleton does not carry |

**This is the audit running in the direction it was designed to run.** Layer 5's whole rationale
is that the LLM's skeleton is an independent read, so a divergence can indict a lower layer rather
than the model — Phases 5i, 5n and 5p spent that against Layer 4, and here it lands on Layer 2
instead. Neither `e'` nor `vosco` was found *by* Layer 5; both came off the `case` annex's parked
list. But Layer 5 had already flagged both, which is exactly the corroboration a third read is
for, and it is worth more than the −1.

The single opened violation is the behaviour recorded at length in the three step-4 entries below:
**the soft count measures divergence between two independent reads, not correctness**, so a
correct round can move it either way. 3633 is not a better number than 3634 by one; it is a
different corpus, marginally more correct, whose two reads happen to line up once more often.

**Other layers**: `morph --check` and `dep --check` stay 0/0, `pytest` stays at 138 passed.
`case --check` goes 0 → **25 hard** and `np --check` 3/64 → **5/96**, both of them the mechanical
consequence of a moved Layer 2 and both described in
[`../morph/CORRECTIONS.md`](../morph/CORRECTIONS.md).

## The `case` annex's third Layer-4 round — 3469 → 3634, upward by 165 (2026-08-01)

**The count rose, the round was correct, and the rise was predicted before it was run.** Slice 3
is the population `case.py --stats` lists and `skel --check` does *not* flag: 325 positions where
`dep` and Layer 5 already **agree** and only the `case` column dissents. Correcting `dep` there
necessarily breaks an agreement, so every correct fix creates a divergence rather than closing
one. The previous two entries said so; this one is the measurement.

**124 positions, 167 rows, +165 soft.** `dep --check` stayed 0/0 throughout. Rows and readings in
[`../dep/CORRECTIONS.md`](../dep/CORRECTIONS.md); the partition and the per-position verdicts in
[`../case/CORRECTIONS.md`](../case/CORRECTIONS.md).

### The three slices, side by side

| slice | population | candidates | edited | yield | Layer 5 |
|---|---|---|---|---|---|
| 1 | `obl` × `nominative` impossible pairings | 49 | 10 | 20% | 3550 → **3555**, +5 |
| 2 | contradictions where `skel` sides with `case` | 102 | 81 | 79% | 3555 → **3469**, −86 |
| 3 | contradictions `skel` does not flag | 325 | 124 | 38% | 3469 → **3634**, +165 |

The selector holds on both axes it was built to predict. **Direction**: it is the only thing that
decided the sign, and it decided it three times out of three. **Yield**: 79% inside the
intersection, 38% and 20% outside — a contradiction that breaks a 2-1 tie really is a better
predictor of a Layer-4 defect than one that is merely a disagreement, and this is now measured
over 476 candidates rather than argued.

### Where the 165 went

| kind | added | note |
|---|---|---|
| `role_mismatch` | 133 | the direct consequence: `dep`'s role moved away from the one the LLM asserted |
| `missing_arg` | 16 | mostly the `obj` → `attr` and `obj` → `mark` rows, which remove an argument the derivation used to produce |
| `extra_arg` | 15 | the swaps, where the newly-`nsubj` relative is an argument the LLM did not list |
| `missing_tuple` | 2 | two predicates the derivation no longer reaches |
| `extra_arg` | −1 | one closed |

Almost exactly one new divergence per edited row (165 / 167). That ratio is the mirror image of
slice 2's (86 closed / 92 rows) and it is what the configuration guarantees: in slice 2 the
correction and the LLM's dissent were the same judgment, so the report stopped existing; here the
correction and the LLM's *agreement* were opposed, so a report starts.

### Why this is not a regression, and how to tell the difference

Layer 5's soft count measures divergence between two independent reads. It falls when `dep` moves
toward the LLM and rises when it moves away, and **neither movement is evidence about
correctness** — that comes from the terzina. The guard this round offers is its own control: of
the 325 candidates, **171 were `case`-side errors and were left alone**. Had the round been
optimizing the number in either direction, that is the population it would have touched.

The practical reading for anyone interpreting this number later: **3634 is a worse number and a
better corpus than 3469**, and after slice 3 the divergence that remains at these 124 positions is
a documented disagreement between a corrected Layer 4 and an uncorrected Layer-5 reading — the
same category as the 2832 `extra_arg`/`missing_arg` residue Phase 5 closed its books on, not a
new defect. A future `--fix` pass over the affected units is the only instrument that would move
it, and Phase 5q's measured verdict on `--fix` yield (~0.09-0.11 violations per call) applies
unchanged.

## The `case` annex's second Layer-4 round — 3555 → 3469, −86 (2026-07-31)

**The corrected selector paid out.** Slice 1 spent 49 candidates and the count rose by 5; slice 2
spent 102 and it fell by **86**. The difference is not effort or care — both rounds were
hand-verified against the terzine to the same standard — it is entirely *which two of the three
reads already agreed*, which is what the previous entry predicted and this one measures.

### How the population was selected

Of `case.py --stats`'s 462 contradictions, **138** fall on a position Layer 5 already flags, and
**102** of those are positions where the role the Layer-5 LLM *asserted* sides with `case`
against `dep`. That last set is tier A — the 2-1 configuration, and the only population the
annex's **≈90–100** estimate ever described. It is worth stating how close the estimate landed:
predicted ≈90–100, spent 102 candidates, measured **−86**.

The remaining 36 of the 138 are positions where `skel` flags something else at that token
(`missing_arg` only, or a role pointing away from `case`), and the other 324 contradictions are
positions `skel` does not flag at all. **Those 324 are the slice-1 configuration**: correcting
`dep` there is still correct, and it will not lower this count.

### The delta, by group

| group | candidates | edited | Layer 5 |
|---|---|---|---|
| `dep`=`obj`, `case`=`dative`, `skel`=`obl:a` | 46 | 39 (40 rows) | 3555 → 3518, **−37** |
| `dep`=`obj`, `case`=`nominative`, `skel`=`subj` | 18 | 12 (19 rows) | 3518 → 3499, **−19** |
| `dep`=`nsubj`, `case`=`accusative`, `skel`=`obj` | 25 | 19 (22 rows) | 3499 → 3479, **−20** |
| `dep`=`iobj`/`nsubj` mirror direction | 13 | 11 (11 rows) | 3479 → 3469, **−10** |
| **total** | **102** | **81 positions / 92 rows** | **−86** |

The yield rate is the other measured difference from slice 1: **79%** of tier-A candidates were
Layer-4 errors, against slice 1's 20%. A contradiction where the third read breaks a tie is a
much better predictor of a defect than a contradiction that is merely structurally impossible.

Roughly one violation closes per edited position (86 / 81). That is the expected ratio when the
LLM's dissent and the correction are the same judgment: the divergence that was being reported
simply stops existing. It is not one-to-one because a few edits close two violations (a swap
fixes both halves) and a few convert one violation into another instead of closing it — most
visibly the two edits that side with neither `case` nor `skel` (purgatorio 10:90.3 `obj` → `attr`,
paradiso 10:22.2 `nsubj` → `expl`), which are correct Layer-4 fixes that leave a divergence
standing.

### What this does not license

The count fell because `dep` got more correct at positions where an independent read already said
so — the Phase 5i mechanism, not a new one. **It remains a diagnostic, not the objective.** The
21 tier-A candidates left alone are the guard: in eleven of them `case` is the read that is wrong
(*m'avea 'mmonito* is the annex's own worked example of an accusative, read `dative` by the
column), and editing `dep` toward `case` there would have lowered this number by making Layer 4
worse. The rows are in [`../dep/CORRECTIONS.md`](../dep/CORRECTIONS.md); the point is that a
selector good enough to be worth 86 is still not good enough to apply without opening the terzina.

## The `case` annex's first Layer-4 round — 3550 → 3555, upward (2026-07-31)

**The soft count went up by 5, and the round was still correct.** Recorded here because Layer 5's
count is the thing that moved, and because the reason invalidates the ordering
[`../case/CORRECTIONS.md`](../case/CORRECTIONS.md) gave step 4.

The round is in [`../dep/CORRECTIONS.md`](../dep/CORRECTIONS.md): 11 rows over 10 positions,
drawn from the 49 `obl` × `nominative` impossible pairings, each verified against its terzina and
each justified by a parallel the corpus itself already contains. `dep --check` stayed 0/0.

Per position, from a before/after diff of the violation list:

| position | delta | what happened |
|---|---|---|
| inferno 1:80, purgatorio 25:8 | **−2** | the Layer-5 LLM had already read these the way the edit does |
| inferno 14:80, 16:94, 27:54, purgatorio 5:14 | **+5** | the LLM shares Layer 4's **original** reading |
| purgatorio 4:38 | **+2** | derivation artifact: `elli`:`nsubj` propagates a subject to the `conj` predicate on the next line |
| the three `Ed elli a me:` positions | **0** | the violation changed shape (`missing_arg obl` → `missing_arg subj`); the LLM proposes the pronoun as an argument under neither reading |

### Why a correct round can raise the count

The soft count measures **divergence between two independent reads**, not correctness. It falls
when a Layer-4 fix moves `dep` toward what the Layer-5 LLM already said, and rises when it moves
`dep` away from a reading the LLM happened to share. Both are possible, and which one happens is
a property of **the population the candidates were drawn from**, not of whether the edits were
right.

The impossible pairings are, by construction, positions where `dep` and `skel` **agree** and only
`case` dissents — `case` is the third read precisely because it was authored blind. Correcting
`dep` there breaks an existing agreement, so the count goes up whenever `case` is right and the
other two shared an error. That is the annex doing exactly what
[`../case/README.md`](../case/README.md)'s *Independence* section built it to do.

### What this changes about the remaining slices

[`../case/CORRECTIONS.md`](../case/CORRECTIONS.md) ordered step 4 by "the combination neither layer can be right
about together", predicting the 49 would be the **highest-yield** slice. **That criterion was
wrong**, and this is its measurement: 49 candidates produced 10 edits and *cost* 5 soft
violations.

The **≈90–100** figure in that plan was never derived from impossible pairings. It came from the
Phase 5h/5i population — positions where the Layer-5 LLM **already dissents from** Layer 4, so a
third read that sides with the LLM breaks a 2-1 tie and closes the violation. The correct
selector for slices 2 and 3 is therefore not "do `case` and `dep` contradict" but **"does `skel`
already diverge from `dep` here"**, with `case` used to adjudicate. Measure that intersection
before working the `obj` column's 317.

None of this is an argument for reverting the 11 rows. Layer 4 is more correct than it was, which
is the thing the round is for; the count is a diagnostic, and treating it as the objective is how
a round starts editing artifacts to move a number.

## Layer-2 `nol` mistag closes one soft violation (2026-07-31)

**3551 → 3550.** Not a Layer-5 change: a Layer-2 correction round driven by the
[`case/`](../case/README.md) annex happened to close one of Layer 5's soft residue, and the
delta is recorded here because Layer 5's count is the thing that moved.

*Paradiso* 17:92, "e nol dirai" ("and you will not say it"). Layer 2 read `nol` as
`non+il` / `adverb+article`, treating the clitic `lo` as an article. Layer 5's membership check
consequently reported `argument (92, 4) for role obj heads no NP/pronoun/predicate` — the `obj`
was correct, but the token it cited was tagged as neither a noun phrase nor a pronoun. Correcting
`nol` to `non+lo` / `adverb+pronoun`, which is how the corpus reads the other 37 occurrences of
the form, resolves it with no change to `skel/`.

The mistag was found by [`case/`](../case/README.md)'s scope audit rather than by Layer 5's own
triage, which is the annex behaving as PLAN.md's *Layer 5 doubles as an audit of Layer 4* claim
predicted, one layer further down: a column that reads `pos` as a **count** exercises Layer 2 in
a way no previous consumer did. See [`../morph/CORRECTIONS.md`](../morph/CORRECTIONS.md)'s
*Fused-token component counts, round 2*.

`skel --check` is now **0 hard, 3550 soft**; `morph --check` and `dep --check` stay 0/0. Figures
quoted as 3551 elsewhere in this repo describe the Phase-5 end state and are left as they were.

## Phase 5q: the final `--fix` regeneration pass, and the `ioj` typo (2026-07-29)

Baseline: **0 hard, 3702 soft** (the Phase 5p state), **1702 flagged parse units**. One full
`--fix` pass over all three canticles, run by the user as `make -C skel fix` 3-way parallel,
**≈28 hours wall time**. This is the work item PLAN.md had reserved for the user once the
deterministic route was exhausted, and it is the second (and last) full regeneration round.

| metric | measured |
|---|---|
| units flagged before | 1702 |
| units flagged after | 1644 (**−58 cleared outright**) |
| soft violations removed | **147** (3702 → **3555**, −4.0%) |
| violations removed per LLM call | **≈0.086** |
| units that got *worse* | **0** (Phase 5c's criterion held) |
| cantos touched | 66 — inferno 25, purgatorio 21, paradiso 20 |

Per class:

| kind | before | after | Δ |
|---|---|---|---|
| extra_arg | 1714 | 1639 | −75 (−4.4%) |
| missing_arg | 1238 | 1193 | −45 (−3.6%) |
| role_mismatch | 475 | 459 | −16 (−3.4%) |
| extra_tuple | 155 | 145 | −10 (−6.5%) |
| missing_tuple | 24 | 23 | −1 |
| membership | 94 | 94 | 0 |
| unknown_role | 2 | 2 | 0 |

**The Phase 5e result reproduced, on a residue two Layer-4 correction rounds and nine checker
rules further along.** The yield came in at 0.086 violations per call against 5e's 0.11 — the
same flat rate, on a flagged set composed very differently. Every class moved less than it did in
5e (the three large ones 4.4%/3.6%/3.4% against 5.2%/5.1%/2.9%), so **PLAN.md's stop rule applies
again and no third pass is warranted**: what is left does not respond to regeneration.

The per-unit acceptance count is not recoverable for this round — `skel/skel.log` was left empty
by the parallel invocation — so the table reports the flagged-unit delta (−58) instead, which is
a lower bound on accepted units (a unit can be improved without being cleared).

**The `ioj` typo (−4).** `--stats` had reported `unknown_role 2` since the Phase 4b round; the
two rows were `purgatorio 13:103 dome` and `13:104 rispondesti`, both carrying the role `ioj` —
a plain misspelling of `iobj`, not a reading. Layer 4 tags both arguments (`ti dome`, `mi
rispondesti`) `iobj`, so the correction is mechanical and agrees with the tree. Fixing it removed
the 2 `unknown_role` violations and the 2 `role_mismatch` rows they carried (`'ioj' vs 'obl:a'`):
3555 → **3551**, and **`unknown_role` is now 0 for the first time**.

**Current state**: `make -C skel check` — **0 hard, 3551 soft** (down from 17438 at the first
full-corpus measurement, overall Δ13887, 79.7%; Δ2368 across Phase 5). `make -C dep check` stays
0 hard / 0 soft; `uv run pytest -q` 125 passed.

## Phase 5p: two Layer-4 correction rounds — clausal complements and the `mark` deferrals (2026-07-28)

Baseline: **0 hard, 3702 soft** (from 3712, the Phase 5o state) — −10, no checker code and no
skel artifact touched, zero model calls. Both rounds are Layer-4 edits, the third and fourth the
audit role has produced; the full reading is in [`../dep/CORRECTIONS.md`](../dep/CORRECTIONS.md),
and this section records only what it means for Layer 5.

- **Round A (−7)** — the `ccomp`/`xcomp`-over-`advcl` population Phase 5o left with a verdict but
  no rule. All 35 were re-read with their sub-trees; **6 were retagged** (5 `advcl` → `ccomp`, 1
  → `csubj`, plus one supporting `obj` → `mark` and one `nsubj` → `attr`), and **29 were left**
  because Layer 4 is right. Phase 5o predicted 5-8 plausible cases and named four of them; three
  of those four were retagged and the fourth (`supplica … tanto che possa levarsi`) was left with
  the consecutives, `tanto … che` being the shape Phase 5o had already assigned to Layer 4.
  The 29 residuals are now classified by shape in `dep/CORRECTIONS.md`, so the class does not
  need re-triaging: purposive `per`/`a` + infinitive (10), consecutive `sì`/`tanto … che` (8),
  conditional/temporal adverbials, gerunds after perception or inceptive verbs, and depictive
  adjectives — the last confirmed conventional by a corpus sweep (350 `advcl` heads carry an
  adjective POS).
- **Round B (−3)** — the two multi-edge deferrals of the Phase 5n `mark` round (purgatorio 8:114,
  purgatorio 22:15), closed with the full restructuring (2 and 4 rows) rather than the single-row
  retag 5n was scoped to.

Both rounds kept `dep --check` at **0 hard, 0 soft**. One flagged violation survived by design:
purgatorio 8:114 `quant'` still reports `argument (114, 1) for role subj heads no
NP/pronoun/predicate`, which reads Layer 2's POS (it calls the word a conjunction), not Layer 4's
tree.

By kind, `extra_arg` 1722 → **1714**, `missing_arg` 1239 → **1238** and `role_mismatch` 476 →
**475**. With this the audit route
Phases 5i/5n/5p worked has no measured population left either: every structural bucket the plan
enumerated is closed, and the residual is the reading disagreement the user-run `--fix` pass is
for.

## Checker Phase 5o: rule T — marked adverbial clauses, and the `advcl` verdict (2026-07-28)

Baseline: **0 hard, 3725 soft** (the Phase 5n state). 3725 → **3712** (−13), all `extra_arg`
(1735 → **1722**); every other kind unchanged. Checker-side, zero model calls, zero artifacts
touched. This closes the **last open row** of the `extra_arg` direct-child bucket.

The 51 `advcl` instances were measured before proposing, as the plan required, and they split
into two populations that need opposite treatment:

- **16 give an oblique role** (`obl:per` 8, `obl:a` 4, bare `obl` 3, `obl:senza` 1). These are
  **prepositional infinitive clauses** — "un angel che s'appresta **per venir** verso noi", "**A
  descriver** lor forme più non spargo rime", "Ciascun si fida del beneficio tuo **sanza
  giurarlo**", "discesi tanto sol **per farti** festa". Layer 4 attaches them as `advcl`, outside
  `ARG_DEPRELS`, so `derive_unit` cannot produce them at all; the LLM reads the same edge as an
  oblique and names the preposition literally sitting on it as a `mark`.
- **35 give a complement role** (`ccomp` 18, `xcomp` 14, `subj` 2, `obj` 1) — the
  complement-vs-adjunct distinction, treated separately below.

**Rule T (−13)** (`_marked_adverbial_clause`): a given `obl:<lemma>` whose argument is an `advcl`
child **of the predicate itself** and carries a `mark`/`case` child naming that same preposition.
This is rule S's shape with `advcl` in place of `nmod`, and it inherits rule N's gate — the lemma
must be one the tree itself carries. `_classify_divergence`'s `case_lemmas` map gained a sibling
`marker_lemmas` that also indexes `mark` children, because the preposition of an infinitive
clause is a `mark`, not a `case`; `case_lemmas` is unchanged, so rules L/N/O/S keep their exact
populations (measured: their counts do not move).

**The loose variant was measured at a further −2 and rejected.** Accepting a bare given `obl`
whenever the clause carries any marker admits markers that are not prepositions at all — "infin
ch'el si raggiunge **ove** la tirannia convien che gema" (marker `ove`) and "**quando** a' vapori"
— where nothing in the tree confirms an oblique reading. This is the same narrowing rules N, O
and S apply, and the third time in Phase 5 that measuring the loose variant changed the shipped
rule.

**The `ccomp`/`xcomp` half stays flagged — verdict, not rule.** Read against their terzine, the
35 are mixed in exactly the way the `mark` and clitic populations were, and the split is a
*lexical argument-structure* judgment:

- **Layer 4 is right in the purposive and consecutive cases**, where the LLM over-promotes an
  adjunct to a complement: "i' vegno **per menarvi** a l'altra riva", "non sì **ch'io non
  discernessi** in parte", "e fé sì lor, **che ciascun se ne loda**", "la percossa pianta tanto
  puote, **che de la sua virtute l'aura impregna**".
- **Layer 4 looks wrong in the indirect questions and true complements**: "nota … **come natura
  lo suo corso prende**", "Ch'avete tu e 'l tuo padre sofferto … **che 'l giardin de lo 'mperio
  sia diserto**", "supplica a te … **che possa … levarsi**", "mostrommi l'alma … **qual era tra i
  cantor del cielo artista**".

  The boundary between the two is genuinely fine, which is the argument against ruling on it: in
  "dimmi, **se tu sai**, perché tai crolli diè" the `se` clause is a parenthetical conditional and
  Layer 4's `advcl` is right, while in the superficially identical "Ricorditi, lettor, **se** mai
  … ti colse nebbia" it heads the recalled content. Only a per-case reading separates them.

Separating the two requires knowing which matrix verbs take clausal complements, i.e. the verb
lexicon Phase 5k refused for the predicative-PP half of the clausal cluster. The matrix-lemma
distribution confirms no cheaper gate exists: after splitting off the copular/aspectual verbs
(8 instances), the remaining 43 are spread over **37 distinct lemmas**, 33 of them appearing
exactly once — not a coherent population. The honest residual route is Phase 5i/5n's, a
hand-verified `dep/` correction round over the handful of plausible complement cases (**5-8** of
the 35 on this reading, each needing the sub-tree check 5n established); it is recorded as an
option, not opened here, and is worth at most −8. **It ran as Phase 5p** — 6 retagged, −7 with
its supporting rows.

Four tests in `tests/test_skel.py` (accepted; non-preposition marker still flagged; a given
`xcomp` over an `advcl` still flagged; an `advcl` of another verb still flagged), 125 passing.

**State at this phase**: `make -C skel check` — **0 hard, 3712 soft** (down from 17438 at the
first full-corpus measurement, overall Δ13726, 78.7%; Δ2207 across Phase 5). By kind: `extra_arg`
1722, `missing_arg` 1239, `role_mismatch` 476, `extra_tuple` 155, `membership` 94,
`missing_tuple` 24, `unknown_role` 2.

## Phase 5n: the `mark` bucket, resolved as a Layer-4 correction (2026-07-28)

Baseline: **0 hard, 3746 soft** (the Phase 5m state). 3746 → **3725** (−21). Zero model calls,
zero checker code changed, zero skel artifacts touched — the whole round is 22 retagged rows in
`dep/`, and the full reading of all 35 instances lives in
[`../dep/CORRECTIONS.md`](../dep/CORRECTIONS.md).

This is the second correction Layer 5's audit role produced (Phase 5i was the first), and it
closes the last **open** row of the `extra_arg` direct-child triage table apart from `advcl`.
The population: Layer 4 tags a relative or interrogative word `mark` on a predicate, and the
LLM — which never sees that parse — cites the same token as an argument of it.

**Why a correction and not a rule.** All 35 were read against their terzine, and the population
is mixed the way the clitic-case one was: 22 are Layer-4 mistags (the word fills a real argument
slot — `poi mi farai, **quantunque** vorrai, fretta`; `per la ragion **che** di'`; `**qual**
diverrebbe Iove`), 11 are cases where Layer 4 is right and the LLM misreads (complex
subordinators `secondo che`, comparative and consecutive `che`, the idiomatic concessives `qual
che si sia` / `che che li appaia`), and 2 need a multi-edge restructuring this round is not
scoped to. **No gate separates them.** Layer 2's POS is not usable either — it calls most of
these words "conjunction", including the ones that are plainly relative pronouns. A blanket
`mark` exemption would have swallowed the 11 correct Layer-4 tags along with the mistags, which
is exactly what PLAN.md's *What is deliberately not proposed* warned against.

**Measured.** `dep --check` stays **0 hard, 0 soft**; `pytest` 121 passed. All 22 retags closed
their `extra_arg` violation; the net is −21 rather than −22 because paradiso 27:79 (`Da l'ora
**ch'**ïo avea guardato prima`) **converts** instead of closing — `ch'` is a temporal oblique,
which is what the retag says, but the LLM had cited it as an `obj`, so the divergence is now
reported as a `role_mismatch` against a reading that is still wrong. That is the checker
classifying more precisely rather than the correction failing, the same sign rule C gave in
Phase 5a.

**Current state**: `make -C skel check` — **0 hard, 3725 soft** (down from 17438 at the first
full-corpus measurement, overall Δ13713, 78.6%; Δ2194 across Phase 5). By kind: `extra_arg`
1735, `missing_arg` 1239, `role_mismatch` 476, `extra_tuple` 155, `membership` 94,
`missing_tuple` 24, `unknown_role` 2.

## Checker Phase 5m: rule S — `nmod` complements of the predicate (2026-07-28)

Baseline: **0 hard, 3808 soft** (the Phase 5l state). 3808 → **3746** (−62), all `extra_arg`
(1819 → **1757**); every other kind unchanged. Checker-side, zero model calls, zero artifacts
touched. This is the second cut into the `extra_arg` **direct-child** bucket Phase 5l identified
as the most promising remaining structural population.

Re-triage of that bucket (324 after rule R), by the deprel `derive_unit`'s map omits:

| deprel | count | | deprel | count |
|---|---|---|---|---|
| `expl` | 87 | | `mark` | 35 |
| `nmod` | 62 | | `cop` | 9 |
| `advcl` | 51 | | `conj` | 8 |
| `advmod` | 50 | | `vocative` | 7 |
| | | | tail (`case`, `aux`, …) | 15 |

**Rule S (−62)** (`_nmod_complement_of_predicate`): a given `obl:<lemma>` whose argument is an
`nmod` child **of the predicate itself** and carries a `case` child naming that same preposition.
Rule D already accepts this shape one edge further out (an `nmod` of one of the predicate's
*derived arguments*, "ha bisogno **di te**"); this is the direct-child case, which `derive_unit`
cannot produce because `nmod` is outside `ARG_DEPRELS`.

The population is completely uniform on the gate — **all 62** `nmod` direct-child `extra_arg`
instances are `obl:<lemma>` with a same-lemma `case` child, so the strict and loose variants
return the identical set, the same evidence rule L's two variants gave. By the predicate's POS it
splits into two constructions, both of which leave the tree uncontradicted:

- **58 nominal or adjectival predicates** (noun 32, adjective 26): "intese cose che furon
  *cagione* **di sua vittoria**", "di quanto *mal* fu matre", "*Oppresso* **di stupore**", "di
  sospetto *pieno* e d'ira crudo". UD correctly attaches the PP complement of a predicate nominal
  as `nmod`, and it is an argument of the predication all the same.
- **4 verbal predicates** where Layer 4 wrote `nmod` for a plain oblique: "nel *fermar* **tra Dio
  e l'omo** il patto", "*mischiato* **di lagrime**".

**Shipped ungated on the predicate's POS**, for the reason measured for rule M's proposed gate:
the two shapes are both correct readings, so a gate there would separate the wrong thing rather
than sound from unsound. The lemma match is the structural gate — the LLM names the preposition
literally present on that edge, and naming a different one stays flagged.

Three tests in `tests/test_skel.py` (accepted; different `case` lemma still flagged; `nmod` of a
non-predicate head still flagged), 121 passing.

**State at this phase**: `make -C skel check` — **0 hard, 3746 soft** (down from 17438 at the first
full-corpus measurement, overall Δ13692, 78.5%; Δ2173 across Phase 5). By kind: `extra_arg`
1757, `missing_arg` 1239, `role_mismatch` 475, `extra_tuple` 155, `membership` 94,
`missing_tuple` 24, `unknown_role` 2.

## Checker Phase 5l: rule R — predicative adjectives attached as `advmod` (2026-07-28)

Baseline: **0 hard, 3876 soft** (the Phase 5k state). 3876 → **3808** (−68), all `extra_arg`
(1887 → **1819**); every other kind unchanged. Checker-side, zero model calls, zero artifacts
touched. **This is the first cut into `extra_arg`/`missing_arg` since Phase 5b.**

The re-triage of the two big classes started as this plan prescribed — classifying every
instance by how the cited argument reaches the predicate in the dep tree:

| `extra_arg` (1887) | count | | `missing_arg` (1239) | count |
|---|---|---|---|---|
| unrelated | 659 | | direct child | 1116 |
| descendant, depth 2 | 398 | | unrelated | 123 |
| direct child | 392 | | | |
| predicate is a descendant of the argument | 268 | | | |
| pro-drop ∅ | 131 | | | |
| descendant, depth ≥ 3 | 39 | | | |

`missing_arg` is now **90% direct-child** — the LLM omitting an argument the tree carries on the
very edge `derive_unit` reads. That is LLM incompleteness, not a checker artifact, and no
structural rule can absorb it. (The pairing hypothesis was tested and is small: only **70**
`extra_arg`/`missing_arg` pairs on the same predicate cite two tokens of the same NP span or two
adjacent tokens — "Pape/Satàn", "Anastasio/papa", "Caron/dimonio" — so citation-token drift is
not what these classes are made of.)

**Rule R (−68)** (`_predicative_advmod`): a given `xcomp` whose argument is an **adjective**
attached to that same predicate as `advmod` — "e io etterno **duro**", "dinanzi polveroso va
**superbo**", "il primo cerchio è **tutto**", "tal mi **fec'** io". These are the predicative
complements rule M already covers, which Layer 4 attached adverbially instead; `derive_unit`
only reads `ARG_DEPRELS`, so it can produce no argument for them at all. The whole direct-child
`advmod` population is 118, and the rule takes the 68 that are adjectives.

**The adjective gate was measured against its alternatives and is what keeps this from being a
blanket `advmod` exemption**: the same shape with an **adverb** argument (17 — "che fu nel
cominciar cotanto **tosta**", "m'è **tardi**", "lungi **fia** dal becco l'erba") is Layer 2
calling the word an adverb, which leaves the predicative reading genuinely undecided, so it
stays flagged; so does everything with a non-`xcomp` role (33, mostly `obl`/`obj` over a
quantifier adverb — "guardommi **un poco**", "ebbi **assai**"). This is the split Phase 5b
predicted but did not have the POS breakdown to make: it left the "`xcomp`-over-`advmod` half"
whole, and it divides cleanly.

Three tests in `tests/test_skel.py` (accepted; adverb POS still flagged; non-`xcomp` role still
flagged), 118 passing.

**Current state**: `make -C skel check` — **0 hard, 3808 soft** (down from 17438 at the first
full-corpus measurement, overall Δ13630, 78.2%; Δ2111 across Phase 5). By kind: `extra_arg`
1819, `missing_arg` 1239, `role_mismatch` 475, `extra_tuple` 155, `membership` 94,
`missing_tuple` 24, `unknown_role` 2.

## Checker Phase 5k: rules P and Q — the clausal-complement cluster (2026-07-28)

Baseline: **0 hard, 3924 soft** (the Phase 5j state). 3924 → **3876** (−48), all
`role_mismatch` (523 → **475**); every other kind unchanged. Checker-side, zero model calls,
zero artifacts touched.

The `xcomp`/`ccomp`/`obj` cluster this plan queued was enumerated by (given role, derived role,
the argument's dep deprel, its Layer-2 POS), 173 instances. Two sub-classes are mechanical; the
rest are not, and are left alone.

**Rule P — `ccomp` against `xcomp`, either direction (−22)** (`_clausal_complement_flavor`).
Both labels say *clausal complement of this predicate*; they differ only on whether the
complement has its own subject or takes one by control. Layer 4 makes that judgment
inconsistently on the same construction — "Fa che tu **m'abbracce**" is tagged `xcomp` with an
overt "tu" — so neither side is more informative. This is therefore a **label equivalence**, the
move `_ROLE_CANON` already makes for `attr`/`xcomp`, and it is the one rule in Phase 5 that is
deliberately two-directional: the asymmetry argument L/M/N/O/Q rest on ("one side names
something the tree makes explicit") does not apply when both labels name the same tree edge.
Kept local to the divergence check, so `ccomp` and `xcomp` remain distinct in the artifact and
in the role vocabulary. Distribution: 21 given `ccomp` / derived `xcomp`, 1 the other way.

**Rule Q — given `ccomp` against derived `obj`/`subj` with a verb argument (−25)**
(`_clausal_object`). Layer 4 attaches the complement clause's head verb straight to the matrix
predicate as `obj`/`nsubj` — "or mi concedi ch'io **sappia**", "dimmi se tu **sai**", "avvien
che poi nel maginare **abborri**" — and `derive_unit` reads the deprel alone, so a whole clause
is reported as a direct argument. Same shape as rule N: the LLM's label is strictly more
informative, and one-directional (a given `obj`/`subj` against a derived `ccomp` means the tree
*did* carry the explicit deprel and the LLM flattened it — 4 instances, still flagged).

**The ungated variant was measured: dropping the verb-POS gate would admit exactly one more
instance, and it is an error** — inferno 18:117 "che non parëa s'era **laico** o cherco", where
the cited argument is a noun. Small, but it is the difference between a structural claim and a
blanket exemption, so the gate stays.

**Deliberately not proposed: the predicative-PP half of the cluster (≈55).** Given `xcomp`
against a derived `obl`/`obl:<lemma>` whose argument is an `obl` dependent — "sta **come torre**
ferma", "fu **di grado** maggior", "son io medesmo **di questi cotai**". The LLM reads the PP as
the copula's predicative complement, which is a real reading, but so is the tree's: both sides
make a claim about the same edge, and separating the copular cases would need a verb lexicon
(`essere`/`stare`/`parere`/`sembrare`), which this project has consistently refused in favour of
structural checks. Left flagged.

Four tests in `tests/test_skel.py` (rule P both directions, rule Q accepted, the verb-POS gate,
the flattened-`ccomp` mirror), 115 passing.

**Current state**: `make -C skel check` — **0 hard, 3876 soft** (down from 17438 at the first
full-corpus measurement, overall Δ13562, 77.8%; Δ2043 across Phase 5). By kind: `extra_arg`
1887, `missing_arg` 1239, `role_mismatch` 475, `extra_tuple` 155, `membership` 94,
`missing_tuple` 24, `unknown_role` 2.

## Checker Phase 5j: preposition-lemma normalization + rule O (2026-07-28)

Baseline: **0 hard, 4042 soft** (the Phase 5i state). 4042 → **3924** (−118), all
`role_mismatch` (641 → **523**); every other kind unchanged. Checker-side, zero model calls,
zero artifacts touched.

The 140 remaining `obl:<lemma>` vs `obl:<other>` mismatches were enumerated with each argument's
`case`-child words beside them, which split them into two mechanical classes and a small
residue.

**1. Same preposition, different spelling (−57).** `_PREP_LEMMA_NORM` — Phase 1's normalization
table, until now eight entries hand-picked from the pair list — was rebuilt from what the corpus
actually contains: every `case`-child word form in `dep/`, cross-checked against the pair table.
Three kinds of key, all spellings of their value, never a different preposition:

- **preposition+article contractions** (`nel`/`ne`/`ne'` → `in`, `al`/`ai`/`a'` → `a`, `dal` →
  `da`, `del`/`de'` → `di`, `sul` → `su`, `pel` → `per`) — the LLM names the contraction it sees
  ("scendemmo **ne la** quarta lacca" → `obl:ne`), while Layer 2 lemmatizes it as `in+il` and
  `_prep_lemma` keeps the first part, so `derive_unit` says `obl:in`. `col`/`coi` were already
  in the table for exactly this reason; this generalizes them.
- **archaic/apocopated spellings** (`sovr'`/`sovresso` → `sopra`, `ver'` → `verso`, `'nnanzi` →
  `innanzi`, `fin`/`infin`/`insin` → `fino`, `contr'` → `contro`, `tr'`/`fra`/`intra` → `tra`,
  `incontr'` → `incontra`, `lunghesso` → `lungo`, `apo` → `appresso`).
- **the `in+verso` univerbation family** (`inver`, `inver'`, `'nver'`, `inverso`, `invero` →
  `in`) — Layer 2 analyses `inver'` as the compound `in+verso` (21 of the 30 occurrences), so
  `_prep_lemma`'s split reports `in`. Normalizing onto `in` rather than onto `verso` follows
  this table's stated convention (canonicalize to the derived side), and it collapses the pair
  in both directions at once: `obl:inver` vs `obl:in` (5), `obl:inver'` vs `obl:in` (4),
  `obl:in` vs `obl:invero` (2), `obl:inverso` vs `obl:in` (2).

**2. Rule O — co-present prepositions (−61)** (`_co_present_preposition`): two different
`obl:<lemma>` labels for the same argument where the **given** lemma is one of that argument's
own `case` children. Italian stacks prepositions and the dep tree attaches both markers to the
nominal — "**in su** le porte", "dietro **a** noi", "dentro **a** lo specchio", "infino **al**
giro quinto" — while `derive_unit` reports whichever it reaches first. The LLM naming the other
one is a choice between two markers that are both in the tree, not a contradiction of it. Same
shape and the same one-directional gate as rules L/M/N.

**The negative (two-directional) variant was measured and rejected: it would remove 30 more, on
much weaker evidence.** In the mirror direction — the *derived* lemma is the argument's `case`
child, the given one is not — the given preposition is a `case` marker attached **elsewhere** in
the unit in 17 instances ("in su la ripa", where Layer 4 attached only `su` to `ripa`), an
`advmod`/`obl` token in 7, and **absent from the unit entirely** in 5. The first group is a
Layer-4 inconsistency (multiword prepositions sometimes get both `case` children, sometimes
one), the last is plainly the LLM inventing a preposition, and a single gate cannot tell them
apart — so the mirror stays flagged, as it does for L, M and N. What is left after rule O is 3
instances where neither side's preposition is anywhere near the argument.

Five tests in `tests/test_skel.py` (`test_normalize_prep_lemma_contractions_and_variants`,
`test_classify_divergence_contraction_lemma_is_not_a_divergence`, rule O accepted / mirror
flagged / both-sides-oblique gate), 111 passing.

**Current state**: `make -C skel check` — **0 hard, 3924 soft** (down from 17438 at the first
full-corpus measurement, overall Δ13514, 77.5%; Δ1995 across Phase 5). By kind: `extra_arg`
1887, `missing_arg` 1239, `role_mismatch` 523, `extra_tuple` 155, `membership` 94,
`missing_tuple` 24, `unknown_role` 2.

## Phase 5i: the clitic-case question, resolved as a Layer-4 correction (2026-07-28)

Baseline: **0 hard, 4042 soft** (from the Phase 5h state of 4068, −26, all `role_mismatch`:
667 → **641**). **No checker code changed and no skel artifact was touched** — the 26 came from
correcting Layer 4, which is what Phase 5h filed this class as.

Phase 5h left 97 instances where the LLM labels a clitic `obl:a`/`obl:di` against Layer 4's
`obj`, and argued they could not be a checker rule because both sides make a case claim about
the same token. Reading them confirmed that, and sharpened it: the population is genuinely
**mixed**. Most are datives Layer 4 mistagged (`mi pesa`, `ti noccia`, `li convien fuggire`,
`ha tolto loro`), but some are plain accusatives the LLM got wrong (`m'avea 'mmonito`,
`ti priego`) — so no blanket routing was possible either.

**What decides a subset is structural, and needs no case feature.** In 30 of the 97 the
predicate carries a *second* `obj` child in the dep tree. UD allows at most one `obj` per
predicate, so the tree contradicts itself independently of the LLM, and the non-clitic object is
the direct one. Those 30 were hand-read against their terzine, 4 rejected, and the remaining 26
retagged in `dep/` (22 → `iobj`, 4 → `obl` for partitive `ne`); see
[`../dep/CORRECTIONS.md`](../dep/CORRECTIONS.md) for the full list and the rejections. `dep
--check` stays **0 hard, 0 soft**; every retagged row closed its Layer-5 divergence, because
Phase 1 canonicalizes `iobj` → `obl:a` and rule L reconciles bare derived `obl` with a given
`obl:<lemma>`.

**This is the first Layer-4 correction Layer 5 produced**, which is the audit role the layer was
built for (see the README's *What it does*): a divergence between two independent readings
located a real mis-parse in the frozen dependency artifact, not just an LLM slip.

**Still open** (unchanged in count, now with a measured reason): the other **67** — no second
`obj`, so nothing structural decides them — and the **30** mirror-direction instances (`iobj`
given by Layer 4, `obj` by the LLM: `mi bagna`, `mi tormenta`, `ti conforta`, `lui non aita`).
Several of the mirror cases look like Layer-4 datives over real accusatives, i.e. errors running
the other way. Deciding either group needs a Layer-2 case feature or a clitic lexicon.

**A wider Layer-4 finding**, recorded in `dep/CORRECTIONS.md` and not acted on: **231**
predicates corpus-wide carry two or more `obj` children (84 with a clitic, 147 without —
flattened coordinations and object complements).

**Current state**: `make -C skel check` — **0 hard, 4042 soft** (down from 17438 at the first
full-corpus measurement, overall Δ13396, 76.8%; Δ1877 across Phase 5).

## Checker Phase 5h: rule N — case-marked objects, and the clitic-case finding (2026-07-28)

Baseline: **0 hard, 4097 soft** (the Phase 5g state). 4097 → **4068** (−29), all `role_mismatch`
(696 → **667**). The small number is the point: the class it came from is 148 instances, and the
measurement split it into two populations that are *not* the same phenomenon.

The `obl:<lemma>` vs `obj`/`subj` pairs (148 given-side, 45 in the mirror direction), classified
by what the dep tree says about the argument:

| bucket | count | reading |
|---|---|---|
| argument has a `case` child naming **the same** preposition | **29** | notation split — **accepted (rule N)** |
| argument has **no** `case` child, and is a **pronoun** | **97** | clitic case — see below |
| argument has a `case` child naming a **different** preposition | 12 | real disagreement — stays flagged |
| argument has no `case` child and is a noun/adjective/article | 10 | stays flagged |

**Rule N (−29)**: the argument carries an explicit `case` child, but Layer 4 attached it as
`obj`/`nsubj`, and `derive_unit` takes the role from the deprel alone — so the preposition
sitting in the tree is dropped ("curan **di te**", "contastare **a Ruberto**", "gridavano «**A
Filippo** Argenti!»", "pigliando più **de la** dolente ripa"). The LLM reads the preposition that
is there; nothing is contradicted. Same one-directional shape as rules L and M (given
`obj`/`subj` vs derived `obl:<lemma>` means the LLM *dropped* an explicit preposition — flagged),
and requiring the *same* lemma is what keeps it narrow: the 12 different-lemma instances stay
flagged. Implemented as `_case_marked_object`; `case_children` from rule L became `case_lemmas`
(position → normalized `case`-child lemmas) to serve both.

**The 97 pronominal cases are deliberately not accepted, and they are a Layer-4 finding.** They
are clitics — 84 of them `obl:a` — where the LLM names a case the token carries morphologically
and the tree cannot express: "**mi** pesa", "non **ti** noccia", "**li** convien fuggire", "fa
che **gliel'** accocchi", "**n'**accorgo", "**ne** portò un lacerto". Layer 4 tags them `obj`.
Unlike rules L/M/N, **both sides here make a case claim about the same token**, so the
"strictly more informative" argument does not apply — and the mirror direction confirms it is a
real disagreement rather than a convention split: in 30 further instances Layer 4 tags the clitic
`iobj` (which Phase 1 canonicalizes to `obl:a`) and the *LLM* says `obj`. The two sides disagree
about clitic case in **both** directions, on the same syncretic pronoun set (`mi`/`ti`/`ci`/`vi`/
`li`/`ne`, accusative and dative alike in Italian).

That makes it a Layer-2/Layer-4 question, not a checker rule: if "mi pesa" is a dative, Layer 4's
`obj` is a mistag, and the correction belongs in [`dep/CORRECTIONS.md`](../dep/CORRECTIONS.md)
under the same measure-then-freeze discipline Phase 5d used to *reject* the `expl` hypothesis. No
correction is opened here — Layer 2 records no case feature (`MorphRow` has gender/number/person,
not case), so deciding it needs either that feature or a clitic lexicon, and both are larger
moves than this round. **Filed as the open question for the next round.**

**Current state**: `make -C skel check` — **0 hard, 4068 soft** (down from 17438 at the first
full-corpus measurement, overall Δ13370, 76.7%; Δ1851 across Phase 5).

## Checker Phase 5g: rule M — given `xcomp` vs derived `obj`/`subj` (2026-07-28)

Baseline: **0 hard, 4327 soft** (the Phase 5f state). One rule, no LLM call, no artifact touched:
4327 → **4097** (−230, −5.3%), all of it `role_mismatch` (926 → **696**, −24.8%).

**The gate this plan proposed was measured and abandoned, in both variants.** PLAN.md's candidate
was to accept the pair only in the object-complement configuration — the predicate carrying
*another* `obj`/`subj` argument. Measured full-corpus: the **given-side** gate admits **227 of
230** (98.7%), so it is the ungated rule under another name and discriminates nothing; the
**derived-side** gate admits **163** (71%). The derived-side variant looked principled — of the
73 adjective arguments 63 pass it, against 60 of 100 nouns — until the excluded 67 were read:

```
  gated:    "tal mi fece la bestia"   "li chiama orbi"      "hanno Italia morta"
            "mi chiamaste Ciacco"     "si fa vino"          "chi tu se'"
  excluded: "non son torri"           "mi parve una lontra"  "fummo Frati godenti"
            "è tempo da scostarsi"    "sarà maraviglia"      "ben son Beatrice"
```

The excluded set is not a different phenomenon; it is the **copular** half of the same one. The
gate separates object complements from predicate nominals, which is not the distinction the rule
turns on, and leaving the second group flagged would keep 67 known-correct readings in the
violation count. So the rule ships ungated.

**Why the pair is a notation split**: UD has no relation for secondary predication. An object
complement is attached as a plain `obj`, and a copular predicate nominal as `nsubj`, so
`derive_unit` can only ever report the *attachment* — the LLM names the same token's *predicative
function*. This is exactly the split Phase 1 already canonicalizes `attr` → `xcomp` for, one step
further. Both descriptions are true of the same token and nothing in the dep tree contradicts the
LLM, the same "strictly more informative" argument as Rule L.

**One-directional, deliberately.** The mirror pairs (given `obj`/`subj` vs derived `xcomp` — 15
and 22) stay flagged: there the dep tree *did* carry an explicit `xcomp`/`ccomp` deprel and the
LLM contradicted it. Same asymmetry as `_safe_role_repair` and Rule L.

Evidence and its limits: roughly 110 of the 230 were read by hand across every POS bucket
(adjective 73, noun 100, pronoun 31, verb 11). No case was found where the LLM's `xcomp` labels a
plain direct object — the residual doubt is a handful (~3%) of arguable readings such as
"n'andavam l'un dinanzi" and "Femmina è nata", where the token is defensibly the subject. The
`verb`-argument cases are causative/modal infinitives ("perder lo face", "pianger non lascia"),
where `xcomp` is if anything the better UD label.

Implemented as `_predicative_complement` (`dante_corpus/skel.py`), consulted from the same
`elif grole != drole:` branch as Rule L. Three tests: object complement accepted, copular
predicate nominal accepted, mirror direction still flagged.

**Current state**: `make -C skel check` — **0 hard, 4097 soft** (down from 17438 at the first
full-corpus measurement, overall Δ13341, 76.5%; Δ1822 across Phase 5).

## Checker Phase 5f: rule L — `obl:<lemma>` given vs bare `obl` derived (2026-07-28)

Baseline: **0 hard, 4615 soft** (the Phase 5e state). One rule, measured corpus-wide before
implementing, **no LLM call and no artifact touched**: 4615 → **4327** (−288, −6.2%), all of it
`role_mismatch` (1214 → **926**, −23.7%).

`derive_unit` emits a bare `obl` in exactly one situation: the argument has no `case` child
naming the preposition (the `obl`/`obl:agent` branch of its argument loop builds the
lemma-qualified form from that lookup). In **all 288** instances of this pair that condition
holds — the strict variant of the rule (gated on the absence of a `case` child) and the loose one
(ungated) return the identical set, which is itself the evidence that the two sides are not
disagreeing. The preposition is fused into the token: a clitic dative (`che nel lago del cor
**m'**era durata` — derived `obl`, given `obl:a`) or a preposition+article contraction. The LLM's
label is therefore **strictly more informative, not a divergence** — the same argument the Phase 2
authority model makes for pro-drop subjects, and the mirror of `--repair`'s `role_label` rule
(`_safe_role_repair`), which rewrites the *opposite* direction, given bare `obl` → derived
`obl:<lemma>`, precisely because *there* the dep tree is explicit.

Implemented checker-side as `_oblique_lemma_refinement` (`dante_corpus/skel.py`), consulted in
the `elif grole != drole:` branch of `_classify_divergence`. Deliberately **not** a `--repair`
rule: the derivation is the less informative side here, so there is nothing to rewrite the
artifact towards. Three tests, per the file's per-rule convention: the accepted case, a
cross-lemma pair (`obl:a` vs `obl:di`, still flagged — that disagreement is real), and the
defensive negative where the argument *does* carry a `case` child (still flagged: that
combination means the derivation had the preposition and dropped it).

This single deterministic rule removed **more than the entire Phase 5e `--fix` pass** (288 vs
231) at zero model calls — the third time in Phase 5 that measuring a class beat regenerating it.

**Current state**: `make -C skel check` — **0 hard, 4327 soft** (down from 17438 at the first
full-corpus measurement, overall Δ13111, 75.2%; Δ1592 across Phase 5).

## Phase 5e: full-corpus `--fix` regeneration round (2026-07-28)

Baseline: **0 hard, 4846 soft** (the Phase 5b state), 2037 flagged parse units. One full pass,
all three canticles, under the Phase 5c acceptance criterion. This is the first `--fix` round
run on a residue the deterministic phases had already cleared of structurally unfixable units.

| metric | measured |
|---|---|
| units attempted | 2037 |
| units accepted (rewritten) | **178 (8.7%)** |
| units that got *worse* | **0** |
| soft violations removed | **231** (4846 → **4615**, −4.8%) |
| violations removed per accepted unit | 1.3 |
| cantos touched | 85 |
| accepted per canticle | inferno 56, purgatorio 58, paradiso 64 |

Per class:

| kind | before | after | Δ |
|---|---|---|---|
| extra_arg | 1991 | 1887 | −104 (−5.2%) |
| missing_arg | 1305 | 1239 | −66 (−5.1%) |
| role_mismatch | 1250 | 1214 | −36 (−2.9%) |
| extra_tuple | 176 | 155 | −21 (−11.9%) |
| missing_tuple | 26 | 24 | −2 |
| membership | 96 | 94 | −2 |
| unknown_role | 2 | 2 | 0 |

**The expected rise in success rate did not materialize.** PLAN.md predicted the rate would come
in above the pre-Phase-5 10.5%, since 5a/5b had removed from the denominator precisely the units
regeneration could never fix. It came in at **8.7%** instead — statistically indistinguishable
from the earlier figure (which was itself 2 of 19 units on a local model), so the honest reading
is that the method's yield is **flat at roughly 0.11 violations per LLM call**, independent of
how the flagged set is composed. Regeneration is not the lever that closes the remaining gap.

Phase 5c's tightened acceptance held: **no unit regressed**, and `unknown_role` stayed at 2 —
the failure mode that motivated the rule did not recur.

**PLAN.md's stop rule therefore applies: no second pass.** No class moved more than 11.9%, and
the three large ones moved 5.2%/5.1%/2.9% — a class that barely moves after a full pass is
evidence of a checker-side rule mismatch, not of an LLM error awaiting another attempt.
`role_mismatch` moved least while sitting 99.9% on edges *both* sides see, and its top pairs are
strikingly systematic:

```
'xcomp' vs 'obj'   170    'obl:a' vs 'obl'  94    'obl:a' vs 'obj'  92
'obl:di' vs 'obl'   84    'obj'  vs 'subj'  81    'subj'  vs 'obj'  67
'xcomp' vs 'subj'   60
```

The `xcomp`/`obj` and `obl:<lemma>`/bare-`obl` pairs in particular look like the same kind of
labeling-convention split Phase 1 and Phase 5a/5b already normalized elsewhere (a nominalized
infinitive read as a clausal complement; a preposition the dep tree attaches without a `case`
child) — they should be measured before any further model calls. That is the next round.

**Current state**: `make -C skel check` — **0 hard, 4615 soft** (down from 17438 at the first
full-corpus measurement, overall Δ12823, 73.5%; Δ1304 across Phase 5). The artifacts changed
this round are the 85 cantos listed above — the first `skel/*/` change since the Phase 4b round.

## Checker Phase 5b/5d: re-triage of the reduced set (2026-07-26)

Baseline: **0 hard, 5105 soft** (the Phase 5a state). Every surviving violation was re-classified
by its dep-tree context — for `extra_arg`/`missing_arg`/`role_mismatch`, how the cited argument
attaches under the predicate (direct child + deprel, descendant depth, unrelated, ∅); for
`extra_tuple`/`missing_tuple`, the predicate's own deprel and Layer-2 POS. Three mechanical
classes fell out, all measured corpus-wide before implementing, and all landing additively
(5105 → 5012 → 5006 → 4945 → **4846**, exactly the sum of the three measured sizes):

1. **Coordinating conjunctions promoted to predicates** (`derive_unit` rule 1, −93):
   `missing_tuple` was **74% a single pattern** — a line-initial `E`/`Ed`/`Ma` that Layer 4
   attaches to the previous clause head with deprel `conj` ("E 'l mio buon duca, che già li er'
   al petto"), which `derive_unit`'s conj-promotion then made a predicate. A coordinating
   conjunction is a function word and can never be a predicate: this is a **derivation
   over-generation**, not an LLM omission — the LLM was right to not propose it. Gated on the
   Layer-2 POS being `conjunction`, so gapped predicates of other POS (the `conj`/`noun` and
   `conj`/`pronoun` cases, real ellipsis) stay derived. `missing_tuple` **100 → 26**.
2. **Copula/auxiliary listed as the predicate** (`_classify_divergence`, `_aux_head`, −99):
   "Molti *son* li animali", "se tu *vorrai* salire" — the LLM names the copula or modal as the
   predicate where `derive_unit`, following UD, names the lexical head it attaches to. In
   essentially every instance the LLM lists the head **as well**, so this is the same
   double-listing the Phase 4a `attr`/`xcomp` whitelist already suppresses, and it is gated the
   same way: only when the `aux`/`aux:pass`/`cop` token's head is itself a derived predicate.
   `extra_tuple` **275 → 176**, with `extra_arg`/`missing_arg` untouched (an `extra_tuple`
   predicate's argument rows were never compared, so nothing stops being checked).
3. **Adverbial obliques** (`_adverbial_oblique`, −67): `obl`/`obl:<prep>` citing an adverb that
   hangs off the same predicate as `advmod` (`quivi`, `là`, `dinanzi`) — 67% of all remaining
   bare-`obl` `extra_arg`. `derive_unit` builds obliques only from `obl` deprel children, so it
   structurally can't emit one; the membership soft check **already** accepts exactly these
   tokens as `obl` arguments for exactly this reason (Pilot-build item 3), so this closes an
   inconsistency between the two checks rather than adding an exemption.

Rejected by the same measurement — recorded because each disproves a plausible rule:

| candidate | measured |
|---|---|
| remap every given `aux`/`cop` predicate onto its head (instead of suppressing) | **−6** ❌ — merging the two argument sets adds `extra_arg` +19 as fast as it removes tuples |
| remap only when the head is derived but *not* also listed by the LLM | −2 ❌ — the pattern is double-listing, so this variant almost never fires |

**Phase 5d (route Layer-4 errors back to Layer 4): the hypothesis is disproved.** PLAN.md
expected the `extra_arg` cases citing an `expl` child (107, counting `expl:pass`) to be `dep`
mistags. Enumerating them: **99 of 107** cite a clitic — `si` 30, `mi` 27, `s'` 20, `ti` 7, `m'`
7, `ci` 3, `se`/`sen`/`v'` 5 — i.e. Layer 4 correctly marks the clitic of an inherently
pronominal verb (`andarsene`, `muoversi`, `rimanersi`, `raccostarsi`) as `expl`, and the LLM
promotes it to `obj` (78) or an oblique (18). The 8 non-clitic stragglers (`noi`, `io`, `te`...)
are too few to constitute a class.
That is an **LLM reading against the frozen UD convention**, not a Layer-4 error — `--fix`
material for Phase 5e, and nothing to file in `dep/CORRECTIONS.md`. No Layer-4 correction was
opened this round.

- Tests (`tests/test_skel.py`): `test_derive_unit_does_not_promote_coordinating_conjunction` +
  `..._still_promotes_gapped_non_conjunction_conj`,
  `test_classify_divergence_copula_predicate_double_listing_suppressed` +
  `..._copula_of_underived_head_still_flagged`, `..._adverbial_oblique_accepted` +
  `..._adverbial_argument_of_nominal_role_still_flagged` — again one negative case per rule.
- No artifact under `skel/*/` was touched; checker-only, no model call.

**Current state**: `make -C skel check` — **0 hard, 4846 soft** (5105 → 4846, Δ259; Δ1073 across
Phase 5 so far, 18.1%). Remaining: `extra_arg` 1991, `missing_arg` 1305, `role_mismatch` 1250,
`extra_tuple` 176, `membership` 96, `missing_tuple` 26, `unknown_role` 2. What is left in the
three big classes is now dominated by patterns triage says are genuine reading disagreements:
`extra_arg subj` 936 (73% citing a token *unrelated* to the predicate in the dep tree —
enjambment and pro-drop resolution), `missing_arg` 716 obliques and 265 objects `derive_unit`
reads off explicit dep edges the LLM simply didn't list, and `role_mismatch` 99.9% on edges both
sides see. Those are Phase 5e (`--fix`) material.

## Checker Phase 5a/5c: coordination + `nmod`-oblique normalization; `--fix` acceptance (2026-07-26)

Baseline before this round (`make -C skel check`): **0 hard, 5919 soft** — the state after one
Phase 4b `--fix` regeneration pass. That pass is what motivated the round: measured on inferno 1
it improved **2 of 19** flagged units (10.5%) in 3 hours, because a large share of flagged units
cannot be fixed by regeneration at all — the LLM's reading is already correct and the divergence
is on the checker's side. `PLAN.md` records the full measurement, including the four candidate
rules that were implemented, measured corpus-wide, and **rejected**.

Two rules landed in `dante_corpus/skel.py`'s `_classify_divergence`, both applied to the
`by_arg` maps after `_apply_subj_authority` and before the diff — normalizations of the same
shape as Phase 1's preposition-lemma and `attr`≡`xcomp` equivalences, not new derived rows:

1. **Rule C — coordination normalization** (`_coordination_head` / `_collapse_coordination`):
   every argument citation is mapped onto its coordination head by walking `conj` edges up
   (bounded to 8, never collapsing onto the predicate's own position), on **both** sides, with
   de-duplication. "si ciberà di terra e di sapïenza" — both conjuncts are objects and the LLM
   lists both, while `derive_unit` reads only a predicate's *direct* dep children and so sees
   the first alone. Coordination was the dominant `extra_arg` bucket (38.5% of them attached at
   dep depth 2, overwhelmingly `conj`). Roles are preserved, so a genuine role disagreement on a
   conjunct still surfaces. Emitting a derived row per conjunct instead (PLAN.md's Rule A) was
   measured at net **−2** — `extra_arg` −554 against `missing_arg` +529 — proving the divergence
   is a notation-convention mismatch, not a parse disagreement, and that normalization is the
   right instrument.
2. **Rule D — `nmod` oblique of a derived argument** (`_drop_nmod_obliques`): a given
   `obl`/`obl:<prep>` row is accepted when its argument is an `nmod` dependent of a token
   `derive_unit` already derived as an argument of the same predicate ("ha *bisogno* **di te**"
   — the dep tree hangs "te" off the noun, the LLM reads it as the predicate's oblique).

- Measured (all 100 cantos): **5919 → 5105 soft, Δ814 (13.8%), 0 hard throughout, 0 LLM calls.**
  By kind: `extra_arg` 2848 → 2065, `missing_arg` 1353 → 1317, `role_mismatch` 1245 → 1250;
  `extra_tuple` (275), `missing_tuple` (100), `membership` (96), `unknown_role` (2) unchanged.
  The slight `role_mismatch` **rise** is the expected sign of a normalization that is not merely
  suppressing: collapsing a coordination exposes role disagreements previously split across an
  `extra_arg`/`missing_arg` pair. (PLAN.md's monkeypatched pre-measurement predicted 5099; the
  landed version differs by 6 because it applies the authority model before collapsing, keeping
  Phase 2 behaviour exactly intact.)
- No artifact under `skel/*/` was touched — checker-only, like Phases 0-2 and 4a.
- Tests (`tests/test_skel.py`): `test_classify_divergence_coordinated_argument_collapsed`,
  `..._coordination_collapse_preserves_role_disagreement`,
  `..._uncoordinated_extra_argument_still_flagged`,
  `..._nmod_oblique_of_derived_argument_accepted`,
  `..._nmod_oblique_of_unrelated_token_still_flagged` — each rule paired with a negative case
  proving it doesn't swallow genuine errors.

**Phase 5c** (`skel/skel.py`, new `_is_improvement`): `--fix` accepted a regeneration on
`len(soft_after) < len(soft_before)` alone, a total-count test that admits regressions in *kind*
— the Phase 4b round traded a net count drop for `unknown_role` 0 → 2, a role outside the frozen
vocabulary. Acceptance now additionally requires that every surviving violation's class was
already present before the regeneration.

**Current state**: `make -C skel check` — **0 hard, 5105 soft** (down from 5919, Δ814; down from
17438 at the first full-corpus measurement, overall Δ12333, 70.7%). Remaining, in order:
`extra_arg` 2065 (of which `subj` 936), `missing_arg` 1317, `role_mismatch` 1250. Next is
PLAN.md's Phase 5b re-triage on this reduced set — no further `--fix` calls until it says which
classes are genuine LLM misreadings, since 5d expects part of the residue (the `expl` cases) to
be Layer-4 errors belonging in `dep/CORRECTIONS.md`.

## Checker Phase 4a: attr/xcomp double-listing + elided-copula whitelist (2026-07-20)

Corpus-wide baseline before this round (`make -C skel check`): **0 hard, 8090 soft** — Phase 3's
ending state. Phase 4 opens with a measure-first pass over the two candidate checker
refinements this file's *Next steps* named, rather than assuming their rough estimates: a
read-only analysis (calling `derive_unit`/`validate_unit` directly over the frozen corpus, no
artifact touched) sized each pattern before writing any rule.

1. **Attr/xcomp double-listing** (`dante_corpus/skel.py`'s `_classify_divergence`, new
   `double_listed` set gating the `extra_tuple` loop): a predicate nominal/adjective the LLM
   lists both as another predicate's `attr`/`xcomp` row *and* as its own redundant predicate
   tuple with the same subj — pure restatement, not new information (e.g. `inferno 1:100`, "Molti
   son li animali...": `son`'s `attr Molti` already captures the reading; the LLM's extra `Molti
   subj=animali` tuple adds nothing). Structurally identical to Phase 1's already-landed
   `ccomp`/`xcomp` double-listing suppression for `missing_arg`, just never extended to the
   `extra_tuple` side or to `attr`. Measured: **264** of 914 `extra_tuple` violations.
2. **Elided-copula predicate nominal whitelist** (same function, new `_elided_copula_nominal`
   helper, gated on both the predicate's dep deprel — `conj`/`appos`/`attr` — and a non-verb
   Layer-2 POS, via a new `morph_pos_by_position` parameter threaded from `validate_unit`'s
   `morph_rows`): a predicate nominal coordinate or apposed to a real clause with no copula token
   anywhere (`mantoani per patrïa ambedui`, `Non omo, omo già fui`) — `derive_unit` structurally
   cannot produce this (no verb, no clause-head deprel), but it's a genuine reading, not an error.
   **Narrower than this file's own earlier description** ("no verb token in the unit at all"):
   measuring the full 289 non-verb-POS `extra_tuple` predicates by dep deprel showed only
   `conj`/`appos`/`attr` (**~50**) look like genuine elided copulas. The dominant sub-pattern,
   **150** with deprel `amod` (plus `advmod` 22, `obj` 13, `nsubj` 13, `nmod` 4), are NP-internal
   participial/adjectival modifiers (`unta`, `atra`, `spiacenti`, `cinta`...) the LLM wrongly
   promoted to independent predicate status — genuine LLM errors, deliberately left flagged for
   `--fix`, not swallowed by a blanket "non-verb POS" rule.
   - Effect: `extra_tuple` dropped **914 → 600** (Δ314, exactly 264 + 50 — the two rules'
     measured sizes, confirming no unintended overlap or side effect on other kinds).
   - Tests (`tests/test_skel.py`): `test_classify_divergence_attr_double_listing_suppressed`,
     `test_classify_divergence_elided_copula_conj_whitelisted`,
     `test_classify_divergence_amod_extra_tuple_not_whitelisted` (negative case proving the
     whitelist doesn't swallow genuine errors).

**Current state**: `make -C skel check` — **0 hard, 7776 soft** (down from 8090, Δ314, 3.9%; down
from 14329 at the start of Phases 0-2, overall Δ6553, 45.7%). No artifact under `skel/*/` was
touched — checker-only, like Phases 0-2. `extra_tuple` (600), `missing_tuple` (117), `role_mismatch`
(1466), and the remaining `extra_arg`/`missing_arg`/`membership` are left for `--fix` (LLM
regeneration) or hand triage — see `skel/README.md`'s *Next steps*.

## Checker Phase 3: `--repair` mechanical TSV rewriting (2026-07-20)

Corpus-wide baseline before this round (`make -C skel check`, all 100 cantos): **0 hard, 9672
soft** — Phase 2's ending state, reproduced exactly. Phase 3 is the first pass that touches the
artifact itself (every `skel/<canticle>/<NN>.tsv` with an eligible
divergence), using a new `--repair` mode (`skel/skel.py`) that rewrites committed rows
deterministically — no model call — via two conservative rules in `dante_corpus/skel.py`'s new
`Repair`/`_find_repairs`/`_safe_role_repair`, sourced entirely from `_classify_divergence`'s own
violation list (already passed through Phase 2's `_apply_subj_authority`), never recomputing the
diff independently:

1. **null_subject** — a `missing_arg subj` (`derive_unit` resolved a real subject from an
   explicit `nsubj` edge, e.g. an enjambment subject on a preceding line) paired with an
   `extra_arg subj (0,0)` (the LLM wrote pro-drop ∅) for the *same* predicate: the ∅ row's
   citation is replaced with the derived one. Requires *both* violations present for the same
   predicate — a lone one of either means Phase 2's authority model already accepted it, or the
   two sides cite different real subjects (genuine disagreement), and no repair fires. Effect:
   `extra_arg subj` dropped **2133 → 1350** (of which ∅ `(0,0)`: **878 → 95**); `missing_arg subj`
   dropped **1127 → 344**. **783** rewrites across 100 cantos.
2. **role_label** — a `role_mismatch` where the given role is bare `obl` and the derived role is
   `obl:<lemma>` (`derive_unit`'s `case`-child detection — the only role_mismatch shape that is
   dep-tree-explicit post-Phase-1-normalization): the role cell is rewritten to the derived label.
   Explicitly does **not** fire for `subj`/`obj` or `iobj`/`obj` reversals (either direction) or
   for `obl:<lemma1>` vs `obl:<lemma2>` (cross-lemma) pairs — all genuine disagreements per this
   file's Phase 0 "Top role_mismatch pairs" table, left for Phase 4. Effect: `role_mismatch`
   dropped **1487 → 1466** (Δ21, exactly the **21** rewrites this rule made).
3. **Side effect, not fixed by this phase**: `membership` rose **89 → 94** (Δ+5). In these five
   cases (e.g. paradiso 6:142's `subj` citation to `(136,3)`, the archaic accusative clitic `il`
   in "E poi il mosser le parole biece") `derive_unit`'s `nsubj`-edge resolution points at a token
   Layer 3's NP-span/pronoun data doesn't recognize as heading an argument — a genuine Layer
   3/4 boundary case that repair's null_subject rule surfaces rather than causes. Left as-is and
   folded into Phase 4's existing `membership` backlog (deliberately not special-cased in
   `_find_repairs`, to keep the rule's precondition — "both a missing_arg and a paired ∅ extra_arg
   for the same predicate" — the sole gate, rather than adding a second, NP-membership-shaped
   gate that duplicates the checker's own membership logic).

Tests (`tests/test_skel.py`): `test_find_repairs_null_subject_pairs_missing_and_extra`,
`test_find_repairs_null_subject_then_reclassify_is_clean`,
`test_find_repairs_null_subject_not_produced_when_pro_drop_authoritative`,
`test_find_repairs_null_subject_not_produced_for_xcomp_control_accept`,
`test_find_repairs_null_subject_not_produced_for_genuine_disagreement`,
`test_find_repairs_role_label_bare_obl_to_lemma`,
`test_find_repairs_role_label_then_reclassify_is_clean`,
`test_find_repairs_role_label_rejects_subj_obj_reversal`,
`test_find_repairs_role_label_rejects_different_obl_lemma`,
`test_find_repairs_role_label_rejects_iobj_obj_reversal`.

Corpus-wide run: `make -C skel repair` — **804** total rewrites (783 null-subject + 21
role-label) across 100 cantos, touching 100 `skel/<canticle>/<NN>.tsv` files (804 rows changed,
804 removed — a clean 1:1 replace per row, verified by diff; re-running `--repair` afterward is a
no-op, confirming convergence). By kind, before → after: `extra_arg` 4502 → 3719, `missing_arg`
2563 → 1780, `role_mismatch` 1487 → 1466, `extra_tuple` 914 → 914 (untouched, Phase 4), `missing_
tuple` 117 → 117 (untouched, Phase 4), `membership` 89 → 94 (see item 3 above).

**Current state**: `make -C skel check` — **0 hard, 8090 soft** (down from 9672 at Phase 2's end,
Δ1582, 16.4%; down from 14329 at the start of Phases 0-2, overall Δ6239, 43.5%). Every touched
`skel/<canticle>/<NN>.tsv` was committed alongside this entry. Phase 4 (targeted `--fix`/hand
corrections for the remainder — genuine subj/obj/iobj reversals, elided-copula extra_tuples,
membership) is still open; see `skel/README.md`'s *Next steps*.

## Checker Phases 0-2: normalization + authority model (2026-07-20)

Corpus-wide baseline before this round (`make -C skel check`, all 100 cantos): **0 hard, 14329
soft**. Phases 0-2 are pure checker changes — no artifact
edited — that shrink the soft-violation count deterministically before any TSV is touched
(Phase 3) or the LLM is re-invoked (Phase 4). All three phases (`dante_corpus/skel.py`,
`skel/skel.py`) landed together in this pass; measured **corpus-wide `--stats` after each
phase**, not just the final number, so each phase's own contribution is on record.

1. **Phase 0 — `--stats`** (`skel/skel.py`): added a `--stats` flag/`stats()` function that
   aggregates `validate_unit`'s soft `Violation`s by kind, by `(kind, role, ∅-or-real)`, and by
   `role_mismatch` pair, instead of the one-line-per-violation dump `--check` prints. Required
   extending the shared `Violation` dataclass (`dante_corpus/morph.py`) with optional
   `role`/`given_role`/`arg`/`predicate` fields, populated only by `skel._classify_divergence` —
   additive, no other layer's `Violation` construction changed. Baseline reproduced exactly:
   7035 extra_arg / 3782 missing_arg / 2392 role_mismatch / 914 extra_tuple / 117 missing_tuple /
   89 membership = 14329, matching the original plan's published table verbatim (measurement only, no
   count changed).
2. **Phase 1 — normalization layer** (`dante_corpus/skel.py`, `_canonicalize_role`/
   `_normalize_prep_lemma`, applied inside `_classify_divergence`'s `by_arg` comparison and
   inside `derive_unit`'s own `obl:<lemma>` construction): canonicalized both sides of the diff
   toward the derived side's convention before comparing.
   - Preposition-lemma orthographic variants: `sanza`/`sanz`/`sans` → `senza`,
     `sovra`/`sovr'`/`sor` → `sopra`, `de` → `di`, `contra`/`contr` → `contro`, `ver` → `verso`,
     `ad` → `a`, `col`/`coi` → `con` (the last four extend the original plan's three named pairs, found
     via `--stats`'s role_mismatch-pairs table as it recommends).
   - Role-label splits for one reading: `attr` ≡ `xcomp` (copular-complement labeling),
     `iobj` ≡ `obl:a` (dative alternation) — both canonicalize to the derived side's label.
   - Clausal-complement double-listing: a `missing_arg` for a `ccomp`/`xcomp` derived role is
     suppressed when the argument token is itself proposed as its own predicate tuple by the LLM.
   - Effect: **14329 → 12825** (Δ1504, close to the original ~1500 estimate). `role_mismatch`
     dropped 2392 → 1584; the `attr`/`xcomp`, `iobj`/`obl:a`, and all seven orthographic prep
     pairs no longer appear in the pairs table. Tests: `test_validate_unit_divergence_
     normalizes_attr_xcomp_and_prep_variants`, `test_validate_unit_divergence_ccomp_double_
     listing_suppressed` (`tests/test_skel.py`).
3. **Phase 2 — authority model for `subj`** (`dante_corpus/skel.py`, `_apply_subj_authority`,
   threaded into `_classify_divergence` via a new `dep_index_by_pos` parameter built from
   `dep_rows` at `validate_unit`'s call site): made the `subj` slot LLM-authoritative (validated
   against a candidate set, not exact-matched) in exactly the three cases the original plan named, no
   further:
   - **Pro-drop antecedent** — `derive_unit` produced `subj (0,0)`: any concrete subject the LLM
     resolves is accepted (strictly more informative than ∅, not wrong).
   - **Non-finite ∅** — `derive_unit` produced no `subj` row at all for the predicate: an
     LLM-proposed `(0,0)` is accepted.
   - **xcomp/ccomp control subject** — `derive_unit` produced no `subj` row and the predicate's
     own deprel (via `dep_index_by_pos`) is `xcomp`/`ccomp`: an LLM-proposed subject is accepted
     iff it equals the matrix predicate's derived `subj` or `obj` — replaces the verb-specific
     control lexicon the pilot-build note above (Item 1, 2026-07-13) explicitly deferred, with a
     structural candidate-set check instead (no lexicon, still UD-deprel-only).
   - Every other role, and `subj` where `derive_unit` derives a real (non-∅) subject, stay
     exact-match — this is deliberately narrower than "any subject disagreement is fine": a
     control-subject candidate outside the matrix subj/obj pair, or a `subj` disagreement on a
     predicate `derive_unit` already resolves, still flags (`test_classify_divergence_xcomp_
     control_subject_rejects_unrelated_arg` asserts this negative case explicitly).
   - Effect: **12825 → 9672** (Δ3153; the original ~6000-7000 estimate for this phase was
     explicitly rough/non-additive — the actual figure is lower because a meaningful share of
     `extra_arg subj`/`missing_arg subj` are genuine LLM/derivation disagreements on predicates
     `derive_unit` *does* resolve a real subject for, which correctly remain exact-match and
     unaffected). `extra_arg subj` dropped 4666 → 2133 (of which ∅ 2227 → 878); `missing_arg
     subj` dropped 1718 → 1127. Tests: `test_classify_divergence_non_finite_predicate_accepts_
     null_subject`, `test_classify_divergence_xcomp_control_subject_accepts_matrix_arg`,
     `test_classify_divergence_xcomp_control_subject_rejects_unrelated_arg`.

**Current state**: `make -C skel check` — **0 hard, 9672 soft** (down from 14329; Δ4657, 32.5%).
No artifact under `skel/*/` was touched — this is checker-only, per the plan's gate before
Phase 3 (`--repair`, mechanical TSV rewriting) and Phase 4 (targeted `--fix`/hand corrections),
both still open. `dante_corpus/README.md`'s Layer-5 section (still to be written — see root
`PLAN.md`'s Handoff) and root `PLAN.md`'s Layer-5 "Check" paragraph should describe the
derive-authoritative/LLM-authoritative distinction once Phase 3/4 land alongside it.

## Pilot build, Inferno 1 (2026-07-13)

First build (`uv run skel/skel.py inferno -c 1 -m ollama:gemma4:31b-it-qat`) hit 3/3 retry
failures on lines 55-60, all identical: the model cited `59.2 venendomi` (gerund `venire` fused
with the enclitic dative pronoun `mi` — Layer 2 lemma `venire+mi`, no separate token exists for
`mi`) as its own argument, tripping the hard self-citation check. Fixed in `SYSTEM_PROMPT`
(`skel/skel.py`) with an explicit rule: a verb token with a fused enclitic pronoun encodes that
pronoun internally; do not cite it, or the predicate's own position, as a separate argument. No
`derive_unit` change — this is a token-citation constraint the prompt needs to state, not a
divergence the deterministic derivation gets wrong.

After that fix, the canto built clean: **0 hard** violations, all 136 lines committed.

### Soft-divergence triage (`--check`: 0 hard, 136 soft before the fixes below)

Every soft violation was inspected by comparing the LLM's rows against `derive_unit`'s output
for the same parse unit (not just the violation's one-line detail). Four distinct root causes
emerged, none of them the mixed-copular-style pattern the *Handoff* section predicted as the
likely largest class — that pattern (`è root`/`cosa attr` vs `amara`/`è cop`) barely appears in
canto 1; the actual largest class is different and still open (see below).

1. **`xcomp`-complement subject/object control (largest class, ~50+ of 136 soft violations)** —
   copular-raising verbs (`sembiava carca`, `parea fioco`) and causative `fare` (`fé... viver
   grame`, `fai... mesti`) both take an `xcomp` complement whose own implicit subject
   `derive_unit` currently leaves unfilled (only `conj`-chain subject sharing is implemented, not
   `xcomp`/`ccomp` control). The LLM consistently filled it in, but with an important wrinkle:
   `sembiare`/`parere` are **subject-control** (the xcomp's implicit subject = the matrix
   predicate's own subject) while `fare` is **object-control** (the xcomp's implicit subject =
   the matrix predicate's direct object) — a lexically-governed distinction, not one derivable
   from UD deprels alone. **Deferred, not fixed**: extending `derive_unit` would mean encoding a
   verb-specific control lexicon, which sits uneasily with this layer's "no semantic frame, UD
   deprels only" design (see `dante_corpus/skel.py`'s module docstring and PLAN.md's *Out of
   scope*). Revisit once more cantos are built and the pattern's shape (how many verbs, how
   reliably subject- vs object-control splits along closed verb classes) is actually measured,
   per the *measure-then-freeze* discipline — a single canto is too small a sample to freeze a
   control lexicon against.
2. **Elliptical predicate nominals with no verb token at all** (`mantoani per patrïa ambedui` —
   "[we were] Mantuans by homeland", copula elided; `Non omo, omo già fui` — "[I was] not a man,
   [but] a man I once was", first `omo` has no copula at all) — `derive_unit`'s two predicate
   rules both require either a clause-head deprel or a verb token; an elided-copula predicate
   nominal satisfies neither structurally. Genuinely unexpressable by the current derivation, not
   a bug. **Exemption, not fixed** — same shape as `dep/CORRECTIONS.md`'s substantivization
   cases: a real reading the mechanism can't cite, checked by hand against its terzina, not a
   parse error.
3. **NP-membership soft-check false positives, fixed deterministically** (`dante_corpus/skel.py`
   `validate_unit`) — two sub-patterns, both mechanical widenings of the membership check, not
   changes to `derive_unit` or any artifact:
   - Relative pronoun `che`/`ch'` cited as a `subj`/`obj`/`obl` argument is correctly Layer-5
     usage, but Layer 2 tags `che`/`ch'` inconsistently between `pronoun` and `conjunction` even
     in its relative use (`morph/CORRECTIONS.md`'s `che`/`ch'` mistag section), so the
     POS-based pronoun check missed it. Fixed by also accepting the word form itself
     (`che`/`ch'`/`cui`/`qual`/`quale`/`chi`) regardless of the frozen POS tag.
   - An adverbial oblique (`quivi`, `là`, `sù`, `dietro`) is a legitimate `obl`/`obl:*` argument
     with no NP to cite — adverbs were simply never in the membership check's acceptance set.
     Fixed by accepting an adverb-POS token specifically for `obl`/`obl:*` roles (not for
     `subj`/`obj`/`iobj`, where an adverb would still be a genuine miscitation).
   - Tests: `tests/test_skel.py`'s four new `test_validate_unit_membership_*` cases.
   - Effect on canto 1: 13 -> 2 membership violations (11 resolved: 6 relative-pronoun instances,
     5 adverb instances). `--check`: **136 -> 125 soft** (0 hard throughout).
4. **Two single-instance boundary cases, left as-is** — inferno 1:59 `'ncontro` (the model, having
   been told not to cite the fused-enclitic argument of `venendomi` directly per item 1's build
   fix, cited the adjacent preposition instead — a defensible fallback, not wrong, but not a
   nominal citation either); inferno 1:110 `l'` (elided direct-object clitic `lo`, graphically
   identical to an elided article, so Layer 2 tags it `article` — genuinely ambiguous without
   deeper morph-layer work, out of scope for this pass). Both remain flagged by the membership
   check; revisit only if the pattern recurs at scale.

**Current state**: `skel/inferno/01.tsv` — **0 hard, 125 soft** (`uv run skel/skel.py inferno -c
1 --check`). Item 1 (xcomp control) is the dominant remaining class and is an open design
question, not a bug to silently fix; items 2 and 4 are structural/POS-ambiguity limits expected
to recur at low, tolerable rates across the corpus. No canto-2+ build has been run yet.

## Rules AH-AL and the Inferno 7-10 read (2026-08-14)

Per-position read of all **37** soft violations standing in Inferno 7-10, on Phase 6's principle
that aggregate statistics misdiagnose checker silence as LLM error. Each position was read against
its terzina with `morph`/`np`/`dep` open; the read produced five deterministic checker rules, five
upstream mistags, eight Layer-4 retags, three prompt defects, and two candidate rules measured and
dropped. **1247 → 1091 soft (−156, −12.5%)**, 0 hard throughout, with **zero model calls**.

Inferno 7-10 itself went **37 → 17**.

### The five rules

Every population below was measured over all 100 cantos before the rule was written.

| rule | shape | population | moved |
|---|---|---:|---:|
| **AH** | `extra_arg subj ∅` left standing after rule AG dropped the inherited subject | 69 | −14 |
| **AI** | Layer-3 NP head vs Layer-4 attachment naming one argument twice | 92 slots / 184 | −71 |
| **AJ** | an object or dative gapped from the coordination head onto a conjunct | — | −59 |
| **AK** | comparative `come` minted into `obl:come` from a Layer-2 conjunction | 7 | −6 |
| **AL** | a fused clitic cluster (`gliel` = `gli`+`lo`) genuinely filling two roles | 4 | −4 |

**Rule AH — AG's second leg.** *"e ora attendi qui"* (10:129) is a 2sg imperative attached `conj`
to `conservi`, whose 3sg subject *La mente tua* step 3 propagates onto it. Rule AG correctly
detects the person disagreement and drops the derived subject — and then the LLM's `∅` was
reported as an `extra_arg`, an argument the derivation had just disclaimed any opinion about. AG
was fixing one leg of a divergence and manufacturing the other. The fix is the authority model's
own logic: branch 2 already accepts `∅` wherever the derivation is silent, and after AG fires it
*is* silent. Only `∅` is dropped — a conjunct where the LLM resolved a concrete subject is making
its own claim and stays flagged. **14 of the 69** ∅-subject positions turned out to be AG-dropped;
the other 55 (e.g. 9:20, where `alcun` at 21.4 is a genuine long-distance overt subject the LLM
missed) are unaffected, which is the point of measuring the split rather than assuming it.

**Rule AI — NP head vs dep attachment.** *"Qui con più di mille giaccio"* (10:118): Layer 3 gives
the NP `[più di mille]` `head=più`, Layer 4 hangs `mille`. `SYSTEM_PROMPT` tells the model to
"prefer a noun phrase's head token", so the LLM cites Layer 3's head and the derivation cites
Layer 4's — one argument, two violations, neither side having read the line differently. 7:39
(`[questi chercuti]` `head=chercuti`, dep `nsubj=questi`) is the same shape. The rule pairs an
unmatched `missing_arg` and `extra_arg` **in the same role** when both positions lie in one NP span
and one of them is that span's head; each is consumed once, so it can never silence a role
disagreement or absorb a second argument. Chosen over editing `np/`'s heads so no Layer-3 artifact
hash moves. **35 of the 92 candidate slots** matched the gate.

**Rule AJ — coordination gapping.** The densest single pattern of the read, six positions in four
cantos: 7:59 `posti`, 8:98 `tratto`, 8:107 `ciba`, 9:70 `abbatte`/`porta`, 9:102 `morda`. Step 3
propagates a shared **subject** across a coordination and nothing else, but Italian gaps objects
and datives just as freely — *"li rami schianta, abbatte e porta fori"*. Accepted whatever role the
conjunct assigns, because gapping genuinely changes it (7:59: `loro` is the head's `iobj` and the
conjunct's `obj`); the gate is on the *slot* being empty on the conjunct side, not on the role
matching. One implementation note worth keeping: the walk must visit **every** conjunct up the
chain, not `_coordination_head`'s topmost one — `porta` chains to `abbatte` to `schianta`, and the
gapped object belongs to `schianta` while the coordination head is `fier`, two lines up. Walking to
the head alone fired on 3 of the 6 positions; walking the chain fires on all 6.

**Rule AK — comparative `come`.** *"che qui staranno come porci in brago"* (8:50). Layer 2 tags
`come` a conjunction — which is what it is, a comparative marker — while Layer 4 attaches it as a
`case` child, so the oblique refinement mints `obl:come` out of a token no layer calls a
preposition. Gated on Layer 2's own POS, so a `come` genuinely tagged a preposition keeps its
oblique reading. 6 of 7; the seventh has Layer 2 calling it a preposition.

**Rule AL — dual-role fused clitic.** *"non gliel celai"* (10:44) is `gli` + `lo` in one Layer-1
token, the dative and the accusative of one verb. The Phase-4 `double_listed` whitelist already
accepted the `extra_arg` leg of this; AL is the same acceptance for the `role_mismatch` leg, gated
on Layer 2 having tagged the token as two fused pronouns and on the roles being exactly the pair
such a cluster encodes.

### Two candidates measured and dropped

- **A Stage-1 repair retargeting a conjunction-anchored predicate.** At 8:52 the LLM opened the
  elided-speech frame on `E` rather than on `io`. A deterministic repair moving the Pred to the
  `conj` head asserts no new reading and looked worth having — but the corpus carries **exactly one**
  `extra_tuple` whose predicate POS is `conjunction`, and it is a different shape (`perché`, inferno
  30:59). Population effectively 0. The frame is addressed on the prompt side instead (below).
- **Retagging relative `che`/`ch'`/`onde` from `conjunction` to `pronoun`** (247 tokens). Implemented,
  measured, reverted: it demands 243 new `case`-annex rows, and filling those from Layer 4 would make
  rule U's adjudication circular. See [`../morph/CORRECTIONS.md`](../morph/CORRECTIONS.md).

### Three prompt defects (no count movement until the next `--fix` round)

1. **`_CONV_ADVERB`'s "or it is left out"** — the single largest finding. The shared conventions
   text and `SYSTEM_PROMPT` both gave the model blanket licence to omit an adverb argument. The
   derivation has no such licence: wherever Layer 4 attaches an adverb with deprel `obl`, an
   oblique is emitted. Measured cost: **82 `missing_arg` positions whose argument is an adverb** —
   the largest unbranched bucket in the residue — and the sample is strikingly homogeneous
   (`fuor` 8, `là` 6, `dentro` 6, `dove`/`ove`/`u'`/`v'` 7, `dinanzi` 4, `dietro` 3, plus `qua`,
   `qui`, `suso`, `giù`, `intorno`, `oltre`, `innanzi`). Resolved prompt-side, since Layer 4's
   `obl`-vs-`advmod` split is a real judgment Layer 5 must respect: the licence now covers only
   manner/degree/negation adverbs, and a new `_CONV_ADVERB_ARG` block states that a locative or
   directional adverb answering *where/whither* is an argument. New Stage-2 class
   **`missing_arg_adverb`** carries it, keyed on the *argument's* POS like `extra_arg_adjective`.
   Note the class cannot name the adverb in its question — that is the derivation's own argument
   position, which the independence rule forbids disclosing — so the convention block, not the
   question, is what points the model at it.
2. **The elided verb of speech without an addressee.** 7:49, 8:52, 8:70 and 10:19 are all `E io:
   «…»` with no a-phrase; 10:85 `Ond' io a lui: «…»` — the same frame *with* an addressee — the LLM
   gets right. Every example in `SYSTEM_PROMPT`, `_CONV_VERBLESS` and the `missing_tuple_nominal`
   hint carried an addressee and prescribed `obl:a`, so the model was treating it as criterial.
   All three now state that the addressee is optional, and that the Pred token is never the
   conjunction in front of the speaker's pronoun (the 8:52 error).
3. **Appositive adjective phrases.** 9:111 *"grande campagna, piena di duolo e di tormento rio"* —
   `_CONV_ADJECTIVE` ruled out only the *attributive* case. The appositive one is now named too.

`missing_arg_adverb` stands at 82 unchanged, as it must: the route is prompt-side and moves only
when a `--fix` round is run. That round is the user's, and it is now worth running.

## Layer 4's agreement residue closes; Layer 5 rises 1091 → 1094 (2026-08-14)

`dep --check` went **18 soft → 0** (see [`../dep/CORRECTIONS.md`](../dep/CORRECTIONS.md)): one real
Layer-4 re-attachment, six measured exclusions added to `dep.subject_agreement`, and two
hand-verified Layer-2 `note` flags. Layer 5 was measured before and after, and the three new
violations are individually attributable — no unit regressed anywhere else:

| position | class | why |
|---|---|---|
| inferno 6:87 | `missing_arg subj (86,2)` | **Rule AG** drops a `conj`-inherited subject only on `subject_agreement(...) == "disagree"`. *diverse colpe … grava* is now `AD_SENSUM`-exempt, so the verdict there is *undecidable* and AG no longer fires. AG had been leaning on a disagreement the text itself licenses. |
| purgatorio 26:147 ×2 | `missing_arg obl:a`, `missing_arg obl:di` | The Occitan `sovenha vos a temps de ma dolor` was re-parsed: `vos` is the experiencer (`iobj`), and `de ma dolor` is an oblique of `sovenha` rather than a modifier of `temps`. The derivation now reads two obliques the LLM's own reading of the Occitan does not list. |

This is the same trade `dep/CORRECTIONS.md` records for the multiple-`obj` and agreement rounds:
`derive_unit` reads Layer 4, so making Layer 4 more correct can turn a spurious agreement with the
LLM into a real disagreement. The direction of the count is not the measure; the correctness of
the parse is.

None of the six new exclusions touches a pair the rule calls `"agree"` — that was the gate they
were measured against — so `_find_repairs`' Tier-B null-subject repair keeps every position it had.

## Layer 4's multiword-preposition normalization lands with zero Layer-5 movement (2026-08-14)

Layer 4's stacked-preposition shapes were normalized in the same session
([`dep/CORRECTIONS.md`](../dep/CORRECTIONS.md)'s round: 161 clusters, 196 rows, flat and chained
alike rewritten to the opening word `case`→ nominal, later members `fixed`→ opening word). What
moved on this side:

- **`_classify_divergence`'s lemma collection and `_case_child_lemmas`** now aggregate a `fixed`
  child of a `case` row as a co-present preposition of the same nominal, so rules O/L/N and the
  `prep_stack` repair read the normalized tree exactly as they read the flat one (three new
  tests: fixed member accepted, absent preposition still flagged, stack walk reaches the fixed
  member).
- **Derived labels flip at the 34 chained clusters only** (inner → opening preposition), matching
  what the flat majority already named. Measured per the standing recipe (violation dump before /
  after, parse-unit keyed): **1094 → 1094 soft, net zero** — 696 units flagged before and after,
  **0 cleared, 0 newly flagged, 0 regressed**. The single violation-level change is
  purgatorio 31:26 (*"Per entro i mie' disiri"*): a `missing_arg obl:entro` that becomes
  `missing_arg obl:per` because the derivation now names the opening preposition — the argument
  was already missing on both sides and stays missing.
- The *In Flight* note's "14 stacked-preposition `role_mismatch`es / 18 unattached" was a
  Phase-5j-era count: rules O and `prep_stack` had since absorbed every one of the 14, and the
  standing obl-vs-obl residue is 3 genuine preposition disagreements (*inferno 14:103
  `obl:dentro` vs `obl:di`*, *purgatorio 32:156* and *paradiso 32:57 `obl:a` vs `obl:da`*) that
  no stack shape explains. The normalization's Layer-5 yield is zero **by design** — it removes
  the shape lottery so future rounds stop paying it, it does not chase the count.

`skel --check` stays **0 hard / 1094 soft**; `dep --check` 0/0, `np --check` 0/0, `case --check`
0 hard, `morph --check` 0/0, `pytest` **268** passed.

## Rules AM–AT and the Inferno 11–15 read (2026-08-15)

Per-position read of all **37** soft violations in Inferno 11–15 (11:8, 12:5, 13:4, 14:13, 15:7),
the fifth batch in the audit series. **963 → 888 (−75, −7.8%)**, zero model calls; Inferno 11–15
itself went **37 → 17**. Eight deterministic rules, sixteen Layer-4 rows and two Layer-2 rows.
`pytest` **281** passed (20 new tests, each mutation-checked against the rule it pins).

Four of the eight rules are in `derive_unit` itself rather than the divergence check — the read
found the derivation *wrong*, not merely silent, which no earlier batch had produced at this
rate:

| rule | shape | evidence line | moved |
|---|---|---|---:|
| **AM** | arguments Layer 4 stranded on a `cop`/`aux` never reach the lexical predicate | 15:82 *«'n la mente m'è fitta»* | +7 |
| **AN** | a conjunct with an `orphan` child is a *gapped clause*, not a predicate | 15:95–96 *«…e 'l villan la sua marra»* | −9 |
| **AJ′** | rule AJ's other two directions: an argument gapped from a *sibling* conjunct or from a conjunct up onto its head | 11:44 *«biscazza e fonde la sua facultade»*, 11:47 *«col cor negando e bestemmiando quella»* | −8 |
| **AP** | an apposition is the same argument named twice, and collapses like a conjunct | 11:38 *«guastatori e predon, tutti tormenta»* | −15 |
| **AQ** | an argument citation landing on an `aux`/`cop` names its lexical head | 13:110 *«ch'altro ne volesse dire»* | −11 |
| **AR** | an oblique read off a *verbless* comparative clause is an adjunct (rule AK's `missing_arg` leg) | 11:17 *«come que' che lassi»*, 13:43 *«Come d'un stizzo verde … sì»* | −8 |
| **AS** | a fused clitic's second `case` slot licenses the oblique role Layer 4's single `expl` cannot record | 14:117 *«poi sen van giù»* | −2 |
| **AT** | only a **verb** inherits a subject across `conj`; a nominal promoted to predicate is an elided clause of its own | 11:15 *«Ed elli: «Vedi …»»* | −22 |

**Rule AM is an honest trade, recorded as such.** Lifting the 39 stranded arguments onto their
lexical predicate cleared 15 spurious `extra_arg`s and raised 22 `missing_arg`s the derivation had
simply never asked about — e.g. purgatorio 11:45 (*«al montar sù, contra sua voglia, è parco»*),
where all three of `parco`'s obliques hang on the copula. The derivation is now right and the
reading is wrong, which is a better state than both being silent; the count is not the measure.
The subject leg was measured separately and **dropped** — lifting `nsubj` off a `cop`/`aux` (87
positions) fought the authority model and scored +11 on its own.

**Rule AT is the largest single mover and the read did not predict it.** The evidence line is one
elided verb of speech whose speaker was handed Dante's subject instead of being left pro-drop; the
same defect turned out to run through every nominal `conj` in the corpus (purgatorio 10:86–91,
paradiso 25:55, …). One position cost: paradiso 1:45 (*«e l'altra parte nera»*), where the elided
copula's subject is a `conj` sibling the derivation still cannot see.

**Rule AN's slot assignment was measured across four variants** (rank order 957, text order 961,
case-matched 961/962). The one kept assigns a case-marked remnant to the matching oblique slot
first, then the rest in canonical role order, and drops `subj` from the slots when the promoted
conjunct is itself case-marked (paradiso 27:118 — a preposition on the conjunct means the subject
is *shared*, not gapped). Two clusters stay wrong under every variant (purgatorio 25:3, 27:108):
they are 2-slot ambiguities that only word order settles, and Italian inverts word order freely.

### Upstream corrections in the same read

**Layer 4 — 16 rows** (see [`../dep/CORRECTIONS.md`](../dep/CORRECTIONS.md)): predicative
adjectives tagged `amod` (12:1–3, 13:141), a `Qual è quel toro` subject/predicate swap inconsistent
with 12:4's own tagging, two multiword-preposition clusters the 2026-08-14 normalization had
excluded (`fuor che` 14:44, `Dentro dal` 14:103), a left-dislocated topic (11:70), an object tagged
`nsubj` (14:116), an apposition attached to the wrong host (19:106, found *by* rule AP), and the
`né io anima fuia` clause. **Layer 2 — 2 rows**: `fuia` (12:90) is the adjective, not `fuggire`;
`ascolta` (15:99) is third-person indicative with `chi la nota` as its subject, not an imperative.

### Prompt side, unmeasured until the next `--fix` round

The residue the rules leave in Inferno 11–15 is 17 positions, and it is almost all reading error,
so the fix side got the four changes the read's diagnoses name:

- **Two new Stage-2 classes, `missing_arg_subject` and `extra_arg_subject`**, on the *role* rather
  than a POS. These are the two largest buckets in the whole residue — **153 `extra_arg subj`** (45
  of them asserting pro-drop over a subject the sentence writes) and **103 `missing_arg subj`**,
  29% of the corpus total — and nothing in the prompt had ever addressed the subject slot beyond
  `_CONV_PRODROP`. The new `_CONV_SUBJECT` states the three causes the read found: postverbal
  subjects (11:12 *«no i fia riguardo»*, 15:99 *«Bene ascolta chi la nota»*), the proclitic that
  cannot be a subject (14:70 *«poco par che 'l pregi»*), and the coordination whose subject is
  written once at its first conjunct (14:69).
- **`missing_tuple_nominal` gets its own question.** The class had the right convention
  (`_CONV_VERBLESS`) and the right hint since round 3 and moved 39 → 36 anyway, position-identical
  — because the *question* asked whether the token "heads a clause of its own", which a bare
  `io`/`elli` visibly does not. `_ask_missing_tuple_nominal` states the frame instead of asking
  about it. This is Phase 5w's law applied to a question rather than a convention.
- **`_CONV_REPEATED`** for the `missing_arg` classes: one predicate may fill the same slot twice
  (14:126, *«pur a sinistra, giù calando al fondo»* — two `obl:a`).
- **A `_fix_hint` bug fixed**: it never branched to `missing_arg_adverb`, so Stage 3's hint used the
  generic phrasing for a class that has had its own since round 3. `_violation_subclass` and
  `_fix_hint` now agree.

Nothing on the prompt side moves anything until a `--fix` round is run, and that round is now
worth running.

## Rules AU–AY and the Inferno 16–20 read (2026-08-15)

Per-position read of all **47** soft violations in Inferno 16–20 (16:15, 17:15, 18:6, 19:5, 20:6),
following the eight-step procedure in [`PLAN.md`](PLAN.md)'s *How to Read a Batch*. **888 → 834
(−54, −6.1%)**, zero model calls, 0 hard; Inferno 16–20 itself **47 → 31**. `pytest` 293 passed.

Five deterministic rules, each censused corpus-wide before it was written, measured on its own by
full-corpus violation **diff**, and pinned by a mutation-checked test. **No rule newly flagged a
single position.**

| rule | shape | census | moved |
|---|---|---:|---:|
| **AU** (`_secondary_predicate_over_argument`, `amod` leg) | an adjective Layer 4 hangs `amod` on one of *this* predicate's own derived arguments is the predication's secondary predicate | 19 | **−17** |
| **AV** (`_named_by_its_auxiliary`) | the LLM names only the `aux`/`cop`; Layer 4's lexical head is then reported "not proposed" | 4 | **−4** |
| **AW** (`_pronominal_verb_clitic`) | rule AB's mirror: a reflexive clitic Layer 4 left as `obj`/`iobj` rather than `expl` | 9 | **−9** |
| **AX** (`_control_partners`) | an argument shared across an `xcomp` control edge, same role, either direction | 11 | **−5** |
| **AY** (`_complemented_adjective_phrase`) | an `amod` adjective that governs an argument of its own is a reduced relative, and predicates | 5 | **−5** |

### What the batch found, and what it declined to write

- **Rule AU is the batch's largest mover and the third leg of a construction the checker already
  knew.** Rule R accepts a predicative complement Layer 4 hung on the *predicate* as `advmod`;
  rule AA accepts a participle hung on one of its *arguments* as `acl`. The `amod` leg — "che
  innanzi a buon segnor fa **servo forte**" (inferno 17:90), "ch'i' ho **le cose conte**" (21:62),
  "e fia **la tua imagine leggera**" (purgatorio 17:7), "**innata** v'è la virtù" (18:62) — was
  still being reported, and it is 37 of the residue's `extra_arg` positions by deprel, the third
  largest bucket after `obl` and `nsubj`. The three gates (adjective POS, `xcomp` role, host is a
  derived argument of *this* predicate) are what keep an ordinary attributive out; the 19 the
  census found are all object or subject complements.
- **Rules AV and AW are both mirror legs of accepted rules, and both were found by reading a
  single position.** `_aux_of_derived_predicate` already accepted the LLM naming an `aux`/`cop` as
  the predicate *when it also names the lexical head*; when it names only the auxiliary ("che
  spezzate **averien** ritorte e strambe", 19:27) the very same convention was reported as a
  `missing_tuple`. Likewise rule AB accepts the LLM naming a reflexive clitic the derivation is
  silent about (`expl`), while the 371 reflexive clitics Layer 4 still calls `obj` produced the
  opposite complaint ("si partiro" 16:4, "s'atterga" 20:46, "si puose" 20:56) — the split between
  the two deprels follows nothing visible, so both directions now get the same treatment.
- **A censused rule was dropped: gapped-clause remnants.** "se non ch'**elli uno**, e voi ne orate
  cento" (19:114) reports two `missing_arg`s because rule AN hands a gapped conjunct's remnants to
  the coordination head's slots and the LLM lists only its own. The census found 12 such positions
  — but rule AN's assignment is *right*: `elli`/`uno` are the second clause's subject and object,
  and the head's slots are where they belong. The divergence is the LLM omitting them, which is
  reading error, not checker silence. Left flagged.
- **A one-instance shape was fixed upstream instead of by rule**: at 18:122 the derived argument
  lay inside the Layer-3 NP headed by the predicate itself (`[Alessio Interminei da Lucca]`). The
  census over the whole residue found exactly **one** such position, so this is a Layer-4 row, not
  a rule.

### Standing shapes the batch recorded but did not settle

- **Subject vs. predicate nominal under a copula** (19:85 *«Nuovo Iasón sarà»*, 20:77 *«ma Mencio
  si chiama»*): Layer 4 calls the single nominal `nsubj`, the LLM calls it the complement of an
  elided pro-drop subject, and the line does not decide. Part of the `extra_arg subj ∅ (0,0)`
  bucket.
- **A relative pronoun's subject named by its antecedent** (16:94 *«quel fiume c'ha proprio
  cammino»*): the derivation cites `c'`, the LLM cites `fiume`. An acceptance rule keyed on
  `skel.antecedent` is plausible; not censused this batch.
- **Accusative-and-infinitive** (16:104 *«trovammo risonar quell' acqua tinta»*): the LLM reads
  `acqua` as the matrix object, the derivation as the infinitive's subject. Rule AX deliberately
  does not cover it — that would be relabelling, not relocating.
- **`vicino a` as a multiword preposition** (17:5): Layer 2 tags `vicino` an adjective, so the
  2026-08-14 prep-stack normalization did not reach it, the same tension the 40 adverb-tagged
  clusters were left in.

### Upstream corrections in the same read

**Layer 4 — 25 rows** (see [`../dep/CORRECTIONS.md`](../dep/CORRECTIONS.md)): the reflexive clitic
tagged `nsubj` in 15 places, an object tagged `nsubj` (17:103), a case-marked noun tagged `advcl`
(17:48, 3 rows), a toponym inside a name tagged as the copula's oblique (18:122), a correlative
`Qual` tagged `advmod` (17:85), and four rows at 16:95–96 that hung the river's course on a verb
twelve lines away. **Layer 2 — 1 row**: `c'` in *«quel fiume c'ha proprio cammino»* (16:94) is
elided `che`, not `ci` — the identical `c'ha` at 17:86 already reads it that way.

The 16:95–96 reattachment is **count-neutral by construction** (three `missing_arg`s move from
`rimbomba` to `ha`) and was kept anyway: the count is not the measure, the correctness of the
parse is — the same trade rule AM recorded.

## Rules CZ–DD and the Purgatorio 26–30 read (2026-08-17)

Per-position read of all **33** soft violations in Purgatorio 26–30 (26:6, 27:6, 28:9, 29:4,
30:8), following the eight-step procedure in [`PLAN.md`](PLAN.md)'s *How to Read a Batch*.
**388 → 358 (−30, −7.7%)**, zero model calls, 0 hard; Purgatorio 26–30 itself **33 → 22**.
`pytest` **437 passed**.

Five deterministic rules, each censused corpus-wide before it was written, measured on its own by
full-corpus violation **diff**, and pinned by a mutation-checked test.

| rule | shape | census | moved |
|---|---|---:|---:|
| **DA** (`empty_derived`, argument leg) | rule CS's mirror: a derived tuple that is **empty** asserts nothing, so it contradicts no argument the LLM puts on the predicate — *except* in the subject slot | 17 | **−17** |
| **DD** (`_relative_adverb_oblique`) | the relative locative adverb (`dove`/`ove`/`u'`) Layer 4 writes as a `case` on its own clause's verb is that clause's locative adjunct | 21 | **−3** |
| **CZ** (`derive_unit`, rule AN's slot claim) | a gapped-clause remnant the `case` annex assigns a case to claims the slot that case names, before the role-rank queue hands out what is left | — | **−2** |
| **DB** (`_prepositional_copular_complement`) | rule AD's mismatch leg: a copula's only complement, an adverb Layer 4 wrote as `obl` because it carries a preposition | 2 | **−2** |
| **DC** (`_secondary_predicate_over_argument`, host gate) | rule AA/AU's host test read through rule CE's relative-pronoun identity: inside a relative clause the derived argument is `che` and the adjective hangs on the antecedent | 489 | **−1** |

Plus **12 Layer-4 rows** (see [`../dep/CORRECTIONS.md`](../dep/CORRECTIONS.md)), worth −7/+2.

### The batch's findings

**1. A rule's evidence line can be the line the rule gets wrong.** Rule AN's paragraph says its
remnants "take the remaining slots in the order the predicate's own arguments stand in the line",
and names purgatorio 27:108 — *«lei lo vedere, e me l'ovrare appaga»* — as the case where the
object precedes the subject in both halves. The code did not do that: its sort key is
`(predicate token, role rank, argument position)`, and the predicate token is identical for every
row in the queue, so the queue was ordered by **role rank** and `lei` took the subject slot. The
comment had been describing an intention for four batches.

Sorting the queue by argument position instead is the obvious repair and it is **wrong**: it fixes
27:108 and breaks inferno 19:114 and paradiso 29:78 (−2/+3 on the full corpus), because Dante
inverts the two halves chiastically as readily as he parallels them — *«onde fa l'arco il Sole e
Delia il cinto»* has the head clause object-first and the remnants subject-first. No order is the
convention. What decides 27:108 is the `case` annex reading `lei` as `accusative`, which is rule
U's third opinion moved to the one place in `derive_unit` that is openly guessing. It runs in both
directions, unlike rule U, because here the annex overrules no Layer-4 label — Layer 4 assigns a
gapped remnant no role at all. `derive_unit` gained an optional `case_rows_by_line` parameter for
it, read at exactly this one site.

**2. The near-miss tests are what found rule DA's boundary.** Rule DA started as the plain mirror
of rule CS — an empty derived tuple asserts nothing, in either direction — and measured **−23/+0**,
the batch's largest single move. It also broke five existing tests, all of them the "and a
near-miss still gets flagged" half of the rule-V family (BB, CF, CI, CJ). They were right and the
rule was wrong: for the **subject** slot an empty tuple is not silence but a decision. Rule V is a
procedure that walks the control chain for exactly that slot and rules BB/CF/CJ each widened what
it may collect; when it comes back empty it has *declined*, and accepting whatever subject the LLM
offers would quietly undo four rules' worth of adjudication. No comparable procedure runs for the
other roles, where an empty tuple means only that Layer 4 gave the predicate no argument child.
Restricted to non-subject roles the rule takes 17 of the 23 and all 437 tests pass. **A rule that
breaks an existing near-miss test has been told where its gate belongs, not that it is unusable.**

**3. Census the *shape*, not the violation diff — they answer different questions.** Rule DC's
violation diff is −1, which by the batch series' own habit ("one instance is not a population")
reads as a drop. Its structural census is **489**: adjectives and participles hanging on the
antecedent of a relative clause whose derived argument is the pronoun. The two numbers are not in
conflict — 488 of those positions are already accepted by some other route or never diverge — and
the one that does is not a coincidence but the gate failing on a distinction the corpus settled
elsewhere (rule CE). Kept, on the same ground as rule CI. Contrast rule DC's rejected sibling
below, whose *shape* census was 1.

### Candidates censused and dropped

- **The antecedent double-listed with its relative pronoun** (28:97, *«'l turbar che sotto da sé
  fanno / l'essalazion…»*, the LLM giving `fanno` both `che` and the antecedent in the subject
  slot). Written, measured at **−1/+0**, and dropped: the structural census is also 1. This is the
  shape the Inferno 16–20 batch recorded as "an acceptance rule keyed on `skel.antecedent` is
  plausible" and it is still not a population.
- **Two adjacent bare `obl` adverbs as one locative cluster** (28:71, *«là 've passò Serse»*).
  Rule BJ's shape with *sibling* attachment instead of nested, so the cluster-head walk never sees
  it. Censused at **4** corpus-wide (`là 've` three times, `giù dentro` once), of which one is
  flagged. Dropped as too thin, and recorded below.
- **`dove` as a Layer-4 error.** Investigated as an upstream retag — a `case` deprel whose head is
  a finite verb is structurally odd — and dropped: all **21** `dove`/`ove`/`u'` rows carrying
  `case` attach to a verb, so it is a convention applied consistently, and the fix belongs in the
  checker. That is rule DD.

### Standing shapes the batch recorded but did not settle

- **The prepositional adjunct of time or place, omitted** (27:97 *«Ne l'ora … mi parea»*, 28:79
  *«in questo luogo eletto … tienvi alcun sospetto»*, 29:146 *«col primaio stuolo erano
  abitüati»*). Three more instances of the residue's largest bucket and of the fifth `--fix`
  round's one queued prompt candidate. Reading error, not checker silence.
- **The simile's nominal, omitted** (26:46 *«come grue»*, 30:64 *«Quasi ammiraglio»*): the
  derivation gives the matrix verb the comparison's noun as an oblique and the LLM names nothing
  at all. Rules AK/AR/BK accept the *relabelling* of a comparison; this is plain omission.
- **The quantifier and its partitive noun** (30:120 *«quant' elli ha più di buon vigor
  terrestro»*): Layer 4 makes the adverb `più` the object with `vigor` its `nmod`, and the LLM
  names the noun that carries the meaning. Rule BR's shape one relation over; not censused.
- **The causative `fare` + infinitive** (28:108 *«e fa sonar la selva»*): Layer 4 attaches
  `la selva` as `obj` of the intransitive infinitive, the LLM reads it as the infinitive's
  subject, which is what an intransitive requires. Rule BI's neighbourhood.
- **An adjunct scoping over a predicate and its gerund** (26:100 *«pensoso andai / lunga fïata
  rimirando lui»*): the LLM lists `lunga fïata` on both `andai` and `rimirando`; Layer 4 attaches
  it only to the gerund.
- **Two adjacent bare `obl` adverbs** (28:71) — see above, censused at 4.
- **Genuine LLM misreadings, left flagged**: 27:10 (`anime sante` is Dante's vocative, not
  `morde`'s object), 29:38 (*«se fami, freddi o vigilie … soffersi»* — the 1sg verb's subject is
  pro-drop and the three nouns are its objects), 29:35 (the locative clitic `ci`, omitted).
