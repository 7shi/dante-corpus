# skel — Layer 5 correction history

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
