# Phase 6 Retrospective: Targeted Micro-Fixes, the Read Series, and What a Round Cannot Do

Phase 6 ran from 2026-08-12 to 2026-08-18 and took `skel --check` from **2,084 soft violations to
160** (152 divergence positions plus the 8 artifact-internal contradictions rule EG still reports),
at 0 hard throughout. It did so with two instruments in alternation: a rebuilt three-stage `--fix`
driver (seven user-run rounds, **−1,157** between them) and a per-position read of **all 100
cantos** in nineteen batches (rules AG–EH, **−793**, at zero model cost).

This file is the closed record: the operating principles that produced it, the chronological
write-up of every round and every read batch, the read series' schedule and results, and the routes
Phase 6 closed. Current work is Phase 7 — see [`PLAN.md`](PLAN.md). Phase 5 is in
[`PHASE5.md`](PHASE5.md).

---

## 1. Key Findings & Core Lessons Learned

### 1.1 Reads and rounds take largely disjoint residue

Nineteen read batches (−793) and seven `--fix` rounds (−1,157) never competed for the same
positions. The fifth round is the measurement: run with **no prompt change and no model change**,
against a base fifteen rule batches lower than round 4's, it still took **−15.1%**, flat at −7…−17%
across every bucket with n ≥ 9 (§21). A round's recovery is therefore real and collectable at any
time; what a round buys that a rule cannot is nothing, and what a rule buys that a round cannot is a
*reason*.

The ordering constraint that follows governed the whole phase: **land the checker work first, then
run the round**, so the round's per-class numbers measure the prompt rather than a moving base. The
sixth round was the one round run under that discipline in full (§27).

### 1.2 The residue became a hard core, and rounds stopped closing it

Re-checked under one gate, the artifact goes 265 → 213 → 174 across rounds 5 and 6 as **pure
subtraction**, and **173 of the standing 174 predated round 5** (§27). A round still paid ~18%, but
every position it took was one it had already failed twice, and it introduced nothing new to read.

Round 7 put a number on the ceiling: outside one class, a model call is worth **0.081 violations**,
and 51 of the 152 standing divergence positions had by then survived three rounds each. **The
residue does not go to 0 by running rounds** — which is the finding Phase 7 starts from.

### 1.3 Only three shapes of prompt change have ever moved a class

Across seven rounds, six prompt changes were measured against the population their own prose names:

| shape of change | instance | result |
|---|---|---|
| **withdraw a licence the prompt granted** | `_CONV_ADVERB`'s "or it is left out" | `missing_arg_adverb` −66.3% |
| **narrow a licence** | `_CONV_ADJUNCT` | `obl:{in,da,di,con,tra,per}` −52.6% |
| **make an instruction the class can carry out** | `_CONV_DATIVE` rewritten | `missing_arg obl:a` −45.5% |
| add prose about a shape the model reads wrong | `_CONV_SUBJECT`, the elided-speech frame, the appositive-adjective clause, `_CONV_DATIVE` v1 | round average or ±0, four times |

The negative half is the more useful half: **a convention paragraph aimed at a misreading measures at
the round average**, every time it has been tried. Phase 5w's law survived a question rewrite as well
as a convention rewrite (`missing_tuple_nominal`, round 4).

### 1.4 The only question the model answers well is one answerable from the artifact alone

Round 7 was the first run with `--log`, hence the first with per-class *call* counts, and the table
is the phase's largest single finding. `dual_role` — rule EG's class — ran at **0.833 removed per
call**; every other class ran at **0.081**, a **10× gap** over 284 calls (§30).

The cause is not difficulty. `dual_role` shows the model both of its own rows and asks which is
right; every other class asks it to adjudicate against `derive_unit`'s reading, which the
**Independence Rule** deliberately withholds. Rule EG's real result is not its +50 — it is that
**it is the only question in this project whose evidence sits entirely inside the artifact, and it is
the only one that pays.**

### 1.5 The driver was discarding the model's verdicts, and they were the reading list

**101 of round 7's 332 calls (30%) ended in `no actionable answer`** — one label doing two jobs.
**57 of them were the model answering with its class's own word for *leave this as it is***
(`keep` 39, `none` 14, `drop` 3, `both` 1). `keep` is a first-class answer meaning *the checker is
wrong*; when every answer in a call was `keep`, `apply` returned False and the whole response was
filed as unusable (§30 finding 3).

Splitting the label cost no call, no prompt change and moved no position (§31), and what it produces
is a **census**: a position-by-position list of where the model thinks `--check` is wrong. Rule EH is
the worked example of the whole route — the model refused, the refusal was read, and **the checker
was wrong**. `arg_slot` was decided the same way: 7 calls, 0 removed, 8 answers, all `keep`.

### 1.6 The field-note instrument was measured and did not pay

Every prompt was given a conditional `N…` note slot beside its answer (§29), inert by construction,
to let the model name a position no check looks at. Round 7 produced **5 notes over 332 calls**: one
real (paradiso 14:93, a Layer-2/Layer-3 contradiction no check compares), one a rewording of its own
answer, two outright wrong in a way that contradicted rows the same response wrote. It is kept
because it costs nothing, and **no further prompt work should go into widening it** — the answer slot
already carried the refusal (§1.5).

### 1.7 A per-position read tests the derivation and the upstream layers, not just the checker

The read series' five verdicts (*checker silent*, *derivation wrong*, *upstream wrong*, *prompt
defect*, *genuine reading disagreement*) each earned their place empirically. The Inferno 11–15 batch
was the first to find the derivation **wrong** rather than silent (four rules inside `derive_unit`);
across the series the reads also corrected some 200 Layer-4 rows, ~40 Layer-2 rows, a dozen Layer-3
spans and a dozen case-annex rows, always in the same session.

Recurring shapes worth carrying forward, each found more than once:

- **Which check runs *first*?** An acceptance rule can be correct and simply never reached (rules
  AQ′, DG, DS, DT, BZ).
- **Which *edge* does a gate read?** Nine rules compared Layer 4's raw head while `derive_unit` had
  been normalizing through `aux`/`cop` since rule AM (rule BP).
- **Which *normalization* has already run on the citation?** (rules CD, CI, DZ — the last needing two
  composed.)
- **Check the mirror leg** — but a mirror is not owed acceptance (rule BR's measured −6/+0 and
  declined).
- **A rule's docstring can be more correct than its code** (rules DL, DM each dropped a POS
  condition its own stated reason never asked for).
- **A gate that names a part of speech or a deprel is a claim about a column** (rules DY, EB —
  `come` is written 812 times under eight deprels and four tags).
- **Measure by violation diff, then read what the diff removed** (rule DQ's widening scored −3/+0 and
  was still wrong).
- **A prompt verdict is the only one of the five that leaves no rule behind to be measured, so reach
  for it last** (paradiso 23:10, written up as prompt work three batches before rule EB took it for
  nothing).

### 1.8 An honest count sometimes goes up

Rule AM's trade (−15 spurious / +22 real) set the precedent, rule EG took it to +50 by design, and
across the reads a dozen upstream corrections deliberately raised the Layer-5 count by exposing LLM
readings a wrong tree had been absorbing. **The count is not the measure; the correctness of the
parse is.**

### 1.9 A census of one is still a census — and a rejected variant is a result

Roughly twenty candidate rules were censused and dropped during Phase 6, several at population 0 or
1, two on precedent rather than on count, one on the corpus's own scope boundary (a verb-valency
lexicon, which *Out of scope* rejects). Two variants measured **+168** and **+180** — the same
reading applied at the wrong end of the pipeline (rules CA, CS). Recording the number that killed a
candidate is what stopped later batches from re-proposing it.

---

## 2. The Phase in Numbers

**Seven user-run `--fix` rounds:**

| round | date | base → after | delta | per-unit yield |
|---|---|---|---:|---:|
| 1 | 2026-08-13 | 2011 → 1452 | −559 (−27.8%) | 0.66 |
| 2 | 2026-08-14 | 1409 → 1247 | −162 (−11.5%) | 0.193 |
| 3 | 2026-08-15 | 1094 → 963 | −131 (−12.0%) | 0.188 |
| 4 | 2026-08-16 | 650 → 541 | −109 (−16.8%) | 0.246 |
| 5 | 2026-08-17 | 351 → 298 | −53 (−15.1%) | 0.201 |
| 6 | 2026-08-18 | 213 → 174 | −39 (−18.3%) | 0.232 |
| 7 | 2026-08-18 | 224 → 161 | −63 (−28.1%) | 0.346 |

**Zero units regressed and zero were newly flagged in any of the seven rounds.**

**Nineteen read batches, zero model calls:** AG −43; AH–AL −156; AM–AT −75; AU–AY −54; AZ–BI −143;
BJ–BN −41; BO–BV −35; BW–BZ −25; CA–CJ −33; CK–CO −21; CP–CT −18; CU–CY −21; CZ–DD −30; DE–DF −7;
DG–DJ −10; DK–DR −27; DS–DW −16; DX–EA −11; EB–EF −21. Plus rules EG (+50 by design) and EH (−1)
from round 7's own output.

---

## 3. Chronological Record — Rounds and Read Batches

### 1. The Restructuring (2026-08-12)
- Rebuilt `skel/skel.py` driver to replace monolithic prompt regeneration with Stage 1 auto-repairs and Stage 2 micro-prompts.
- Stage 1 deterministic pass measured at **2084 → 2011 (−73)** with zero LLM calls.
- Two candidate rules measured and deliberately dropped: a case-annex relabel (106 rewrites for 0 violations eliminated) and a `role_alias` rule (population 0).

### 2. First User-Run `--fix` Round (2026-08-13)
- **2011 → 1452 soft, −559 (−27.8%)**, 98 cantos touched, 259 units cleared outright, 197 improved. 0 units regressed, 0 newly flagged.
- **Subclass Results**:
  - `extra_tuple_adverb`: **37 → 7 (−78.8%)** (largest single-class drop on record).
  - `extra_tuple_adjective`: **37 → 17 (−54.1%)**.
  - `role_mismatch`: −40.8%.
  - `missing_tuple_nominal`: −40.3%.
  - Classes without dedicated stage-2 prompts (`extra_tuple`, `missing_tuple`, `membership`): ~0% (confirming gains stemmed from targeted prompts).

### 3. Rule AG & Inferno 4–6 Read (2026-08-13)
- Position-by-position audit of all 19 remaining soft violations in Inferno 4–6.
- **Rule AG (−43, 1452 → 1409)**: Gated `conj` shared-subject propagation on Layer-2 person/number agreement (`dep.subject_agreement` + `_finite_head_of` for periphrastic verbs). Out of 1370 candidates, 682 agreed, 461 were undecidable (untouched), and **227 actively disagreed** and were dropped.
- **Cross-Layer Correction**: Retagged `fiacco` (Inferno 6:54) from adjective to 1sg verb in `morph/inferno/06.tsv`.
- Remaining 17 positions verified as real LLM omissions or genuine reading disagreements.

### 4. Third POS-Keyed Class: `extra_arg_adjective`
- From Inferno 6:70 ("Alte terrà... le fronti"), identified that 65 of 107 `extra_arg xcomp`/`attr` violations cite an adjective argument.
- Implemented `extra_arg_adjective` class in `skel/skel.py` (`_violation_subclass`, `_CLASS_PROMPTS` with `_CONV_ADJECTIVE` fronted, `_fix_hint`).

### 5. Second User-Run `--fix` Round (2026-08-14)
- **1409 → 1247 soft, −162 (−11.5%)**, 76 files touched (161 insertions / 158 deletions).
- Unit-level: **841 → 765 flagged**; 76 cleared outright, 62 improved, 703 unchanged, **0 regressed, 0 newly flagged**.
- Per-unit yield **0.193 violations removed per unit flagged before** — less than half the first round's rate, as expected: the first round consumed the easy population of the classes that had just been given prompts, and what remains is progressively harder residue.
- **Subclass results** (before → after):

  | subclass | before | after | delta |
  | --- | ---: | ---: | ---: |
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

- **Reading of `extra_arg_adjective` (−20.0%)**: the new prompt works but is far from the −54% its sibling `extra_tuple_adjective` scored on its debut round. Its population was already the *residue* of a class the first round had worked over, so −20% on a pre-filtered population is not evidence the prompt is weak. Deciding between "prompt needs sharpening" and "the remaining 52 are genuine reading disagreements" requires a per-position read, not another pass.
- Two structurally identical repairs seen in the diff, illustrating both halves of the round: Inferno 3:13 replaced an empty placeholder row with a four-tuple predicate on `elli` (`missing_tuple`), and Inferno 6:70 dropped a spurious `attr` on `terrà` while 6:72 specialized a bare `obl` to `obl:di`.

### 6. Rules AH–AL and the Inferno 7–10 Read (2026-08-14)

Per-position read of all **37** soft violations in Inferno 7–10. **1247 → 1091 (−156, −12.5%)**,
zero model calls; Inferno 7–10 itself went 37 → 17. Full grammar specification in
[`RULES.md`](RULES.md); upstream retags in [`CORRECTIONS.md`](CORRECTIONS.md).

| rule | shape | population | moved |
|---|---|---:|---:|
| **AH** | `extra_arg subj ∅` left standing after rule AG dropped the inherited subject | 69 | −14 |
| **AI** | Layer-3 NP head vs Layer-4 attachment naming one argument twice | 92 slots / 184 | −71 |
| **AJ** | an object or dative gapped from the coordination head onto a conjunct | — | −59 |
| **AK** | comparative `come` minted into `obl:come` from a Layer-2 conjunction | 7 | −6 |
| **AL** | a fused clitic cluster (`gliel` = `gli`+`lo`) genuinely filling two roles | 4 | −4 |

Upstream: 5 Layer-2 mistags (Inferno 7:38–39 `fuor`/`cherci`/`chercuti`, 8:71 `entro`, 10:23 `ten`)
and 9 Layer-4 rows (Inferno 8:78, 9:41 ×3, 9:72, 9:103, 10:23, 10:85, 10:87), plus 3 further
`come`/`perché` structures (8 rows: Inferno 30:59, Paradiso 3:36, 32:54) found by the
conjunction-in-argument-slot census. Two candidate rules were measured and **dropped**: a Stage-1
conjunction-anchored-predicate repair (population 0) and a 247-token relative-`che` retag (blocked
by the `case` annex — filling those rows from Layer 4 would make rule U circular).

Prompt side, unmeasured until the third round: the `_CONV_ADVERB` omission licence (82 positions),
the addressee-less elided-speech frame (4 of the 37 read), and appositive adjectives. Round 3
settled all three — the licence was the real defect, the other two moved nothing (see below).

---

### 7. Third User-Run `--fix` Round (2026-08-15)

- **1094 → 963 soft, −131 (−12.0%)**, 72 files touched (181 insertions / 76 deletions), 0 hard,
  `pytest` 268 passed.
- Unit-level: **696 → 618 flagged**; 78 cleared outright, 42 improved, 576 unchanged,
  **0 regressed, 0 newly flagged**.
- Per-unit yield **0.188**, against 0.66 (round 1) and 0.193 (round 2) — flat rather than
  declining, even though the base was already stripped of the 156 positions rules AH–AL had taken.
- Per canticle: inferno 303 → 264, purgatorio 410 → 360, paradiso 381 → 339.
- **Subclass results** (before → after):

  | subclass | before | after | delta |
  | --- | ---: | ---: | ---: |
  | `extra_arg` | 424 | 406 | −18 (−4.2%) |
  | `missing_arg` | 349 | 306 | −43 (−12.3%) |
  | `role_mismatch` | 105 | 100 | −5 (−4.8%) |
  | `missing_arg_adverb` | 83 | 28 | **−55 (−66.3%)** |
  | `extra_arg_adjective` | 51 | 49 | −2 (−3.9%) |
  | `missing_tuple_nominal` | 39 | 36 | −3 (−7.7%) |
  | `extra_tuple` | 14 | 12 | −2 (−14.3%) |
  | `extra_tuple_adjective` | 13 | 13 | ±0 |
  | `membership` | 7 | 7 | ±0 |
  | `missing_tuple` | 5 | 3 | −2 (−40.0%) |
  | `extra_tuple_adverb` | 4 | 3 | −1 (−25.0%) |

**What the round was a test of, and what it decided:**

- **`missing_arg_adverb` (−66.3%) — the prompt-defect diagnosis is confirmed.** This was the first
  class whose population was traced to a defect in the corpus's own prompt (`_CONV_ADVERB`'s "or it
  is left out" licence) rather than to the model, and removing the licence took 56 of its 83
  positions in one round — the second-largest single-class drop on record after
  `extra_tuple_adverb`'s debut. It is also the first confirmation that **an aggregate class can be
  caused by our own instructions**, which makes a prompt read a standing move alongside per-position
  checker reads. The 27 that survived are the same positions as before plus one new one; they are
  now a residue to read, not a licence to withdraw.
- **Per-unit yield held at 0.188 vs 0.193**, on a base the AH–AL rules had already stripped of its
  easy positions. Two rounds of decline (0.66 → 0.193) did not continue, which is the first evidence
  that the fall is a function of *what precedes a round* rather than of residue depth alone. One
  caveat against over-reading it: 55 of the 131 removed (42%) came from one class, so this is
  evidence for prompt repair specifically, not for pre-round work in general.
- **The elided-speech frame moved almost nothing** (`missing_tuple_nominal` −3, and all 36
  survivors are the same positions as before). **The appositive-adjective clause moved exactly
  nothing** (`extra_tuple_adjective` 13 → 13, position-identical). Both were prose added to a
  convention block with no instruction reaching the model *at* the flagged position — precisely the
  shape Phase 5w said does not move a class. Before touching either convention text again, they
  need `_HINT_PHRASING`/class-question work or a per-position read; a fourth round will not move
  them as they stand.

---

### 8. Rules AM–AT and the Inferno 11–15 Read (2026-08-15)

Per-position read of all **37** soft violations in Inferno 11–15. **963 → 888 (−75, −7.8%)**, zero
model calls; Inferno 11–15 itself 37 → 17. Full grammar specification in [`RULES.md`](RULES.md);
upstream retags in [`CORRECTIONS.md`](CORRECTIONS.md).

| rule | shape | moved |
|---|---|---:|
| **AM** | arguments Layer 4 stranded on a `cop`/`aux` never reach the lexical predicate | +7 |
| **AN** | a conjunct with an `orphan` child heads a *gapped clause*, not a predicate | −9 |
| **AJ′** | rule AJ's other two directions — gapping from a sibling conjunct, and up onto the head | −8 |
| **AP** | an apposition is the same argument named twice, and collapses like a conjunct | −15 |
| **AQ** | an argument citation landing on an `aux`/`cop` names its lexical head | −11 |
| **AR** | an oblique read off a *verbless* comparative clause is an adjunct (rule AK's `missing_arg` leg) | −8 |
| **AS** | a fused clitic's second `case` slot licenses the oblique Layer 4's single `expl` cannot record | −2 |
| **AT** | only a **verb** inherits a subject across `conj` | −22 |

Two findings worth carrying forward:

- **Four of the eight rules are in `derive_unit`, not the divergence check.** Every earlier batch
  produced acceptance rules — places the checker was *silent*. This one found the derivation
  **wrong**: it lost arguments Layer 4 records (AM), invented predicates out of gapping remnants
  (AN), and propagated subjects onto nominals (AT, the largest single mover in the batch and one no
  aggregate statistic pointed at). A per-position read is now known to test the derivation as well
  as the checker.
- **Rule AM raises the count on purpose** (−15 spurious `extra_arg`, +22 real `missing_arg`) — the
  same honest trade the Layer-4 rounds record. Its subject leg was measured separately and dropped
  (+11 on its own): the authority model already owns that slot.

Prompt side, unmeasured until the next round: two new subject classes (`missing_arg_subject`,
`extra_arg_subject`) covering 29% of the residue, `missing_tuple_nominal`'s own question, a
repeated-slot convention, and a `_fix_hint` branch that had been missing since round 3.

---

### 9. Rules AU–AY and the Inferno 16–20 Read (2026-08-15)

Per-position read of all **47** soft violations in Inferno 16–20. **888 → 834 (−54, −6.1%)**, zero
model calls, **zero newly-flagged positions**; Inferno 16–20 itself 47 → 31. Full grammar specification
in [`RULES.md`](RULES.md); upstream retags in [`CORRECTIONS.md`](CORRECTIONS.md).

| rule | shape | census | moved |
|---|---|---:|---:|
| **AU** | an adjective Layer 4 hangs `amod` on one of this predicate's own derived arguments is its secondary predicate | 19 | −17 |
| **AV** | the LLM names only the `aux`/`cop`; the lexical head is then "not proposed" | 4 | −4 |
| **AW** | rule AB's mirror: a reflexive clitic Layer 4 left as `obj`/`iobj` rather than `expl` | 9 | −9 |
| **AX** | an argument shared across an `xcomp` control edge, same role, either direction | 11 | −5 |
| **AY** | an `amod` adjective governing an argument of its own is a reduced relative, and predicates | 5 | −5 |

Three findings worth carrying forward:

- **Three of the five rules are *mirror legs* of rules the checker already had.** AV is
  `_aux_of_derived_predicate` looking the other way, AW is rule AB looking the other way, AY is
  `_elided_copula_nominal`'s adjective-phrase case. A labeling convention has two directions, and
  a rule written for one of them leaves the other reported — so **when a rule is written, check
  its mirror**. This is cheap to test and was worth 18 of the batch's 54.
- **Rule AU is the third leg of the secondary-predicate construction** (R takes it off the
  predicate as `advmod`, AA off an argument as `acl`, AU off an argument as `amod`) and is the
  batch's largest mover. `extra_arg` positions whose argument Layer 4 calls `amod` were the third
  largest bucket in the residue by deprel, after `obl` and `nsubj`.
- **A censused rule was dropped at population 12**: rule AN hands a gapped conjunct's remnants to
  the coordination head's slots, and the LLM sometimes lists none of them (inferno 19:114). Rule
  AN's assignment is right; the divergence is reading error, so it stays flagged. The census
  decided this, not the count.

Prompt side, unmeasured until the next round: nothing new — this batch's diagnoses were all
checker-side or upstream.

---

### 10. Rules AZ–BI and the Inferno 21–25 Read (2026-08-15)

Per-position read of all **44** soft violations in Inferno 21–25. **834 → 691 (−143, −17.1%)**,
zero model calls; Inferno 21–25 itself 44 → 16. The largest batch of the series. Full grammar
specification in [`RULES.md`](RULES.md); upstream retags in [`CORRECTIONS.md`](CORRECTIONS.md).

| rule | shape | census | net |
|---|---|---:|---:|
| **AZ** | rule R's mirror leg: a depictive adjective on the predicate as a **bare `obl`** | 43 | −13 |
| **BA** | a predicate with **two** derived `subj` rows — the derivation has not decided | 99 | −41 |
| **BB** | rule V's coordination leg: *every* conjunct of a controlled infinitive's subject | — | −26 |
| **BC** | an `advmod` whose filler Layer 2 calls a **noun or pronoun** is an oblique | 117 | −14 |
| **BD** | rule AW's third deprel: a reflexive clitic Layer 4 left as `obl` | 35 | −10 |
| **BE** | `flat` collapses onto its head like `conj`/`appos` | 31 | (in BB) |
| **BF** | a `cop` edge pointed the wrong way: the non-verb in the `cop` slot is the `attr` | 11 | −8 |
| **BH** | rule M's mirror leg: the pro-drop ∅ subject rule M's relabelling leaves behind | — | −14 |
| **BI** | the accusative-and-infinitive's shared nominal, named from the matrix side | 10 | −10 |

Plus 20 Layer-4 rows and 5 Layer-2 rows (**−11 / +4** together), and `pytest` 311.

Three findings worth carrying forward:

- **When you write a rule, check the *plural* as well as the mirror.** Rules AZ, BD and BH are
  more mirror legs (37 positions), which the previous batch already taught. Rule BB is new in
  kind: rule V was correct in direction and simply **applied once to a shape that supplies
  several citations** — `_subj_arg` returns the first `subj` in the map, and a coordinate subject
  has three. Any rule that pops a single entry out of `g`/`d` should be asked what it does when
  the shape produces two.
- **Rule ordering is a defect surface, and only the diff shows it.** Rule BE alone measured
  −7/**+2**: `_apply_subj_authority` runs *before* `_collapse_coordination`, so the collapse
  rewrote citations rule V had refused onto the very position it accepts (paradiso 15:112).
  Testing rule V's candidate set through `_coordination_head` too took the pair to −23/0. A rule
  that tests a **raw** citation for membership must test the normalized one as well.
- **Two rules were censused and dropped, and one upstream refinement was measured and deferred.**
  The elided speech verb's `missing_tuple` (inferno 24:72) has a census of 164 and the LLM
  proposes nearly all of them, so the four omissions are reading error, not checker silence; the
  result-clause `ccomp` (22:84) has a census of 2. Restricting `dep.subject_agreement`'s
  *coordinated subject* exclusion to the number test — a coordination of nominals is third person
  however many members it has — was implemented and measured at **12 new `dep --check` soft
  violations**, all real Layer-4 questions, and reverted rather than landed against the standing
  0-soft invariant.

Prompt side, unmeasured until the next round: nothing new — every diagnosis was checker-side or
upstream.

---

### 11. Rules BJ–BN and the Inferno 26–30 Read (2026-08-15)

Per-position read of all **23** soft violations in Inferno 26–30. **691 → 650 (−41, −5.9%)**,
zero model calls; Inferno 26–30 itself 23 → 11. Full grammar specification in [`RULES.md`](RULES.md);
upstream retags in [`CORRECTIONS.md`](CORRECTIONS.md).

| rule | shape | census | net |
|---|---|---:|---:|
| **BJ** | the adverb-preposition cluster ("fuor **del** dritto amore") names one oblique, from either word | 147 | −21 |
| **BK** | rule AR's other marker: `che` opens the second term of a comparison | 51 | −4 |
| **BL** | rule AR's other order: `sì come` is one word, so the comparison is what the marker opens | 107 | −1 |
| **BM** | an oblique whose filler Layer 2 calls a **conjunction** is the clause's connective | 37 | −11 |
| **BN** | a conjunction in a clause-head deprel with no arguments is not an elided predicate | 14 | ±0 |
| **BI**′ | rule BI's third host deprel: the perception verb's infinitive written as a plain `obj` | 7 | −1 |
| **AN**′ | rule AN's clause-head leg: a gapped comparison promoted to `advcl` heads no predicate | — | ±0 |
| **AQ**′ | rule AQ applied to the *membership* check, which runs before the merge | 2 | −2 |

Plus 10 Layer-4 rows and 1 Layer-2 row, and `pytest` 326.

Three findings worth carrying forward:

- **A rule can be right and simply never reach the check that reports the position.** Rule AQ has
  merged an argument citation landing on a `cop`/`aux` onto its lexical head since the Inferno
  11–15 batch — but only inside `_classify_divergence`. The *membership* check ("argument (87, 4)
  for role obj heads no NP/pronoun/predicate") runs earlier, on the raw row, and was reporting the
  un-normalized position. This is the 21–25 batch's ordering finding in a new form: there, two
  rules in the wrong order inside one pass; here, one rule present in one pass and absent from
  another. **Ask which checks run before a rule, not only what runs after it.**
- **A deliberately deferred upstream tension is a Layer-5 population.** The prep-stack
  normalization of 2026-08-14 excluded the ~40 adverb-preposition clusters (`dentro a`, `fuor
  di`, `di là da`) and recorded them as "a Layer-2/4 tension to decide separately if it ever
  matters". Censused at 147, they were producing violations in *both* directions, and rule BJ
  settles them at Layer 5 — merging the citation onto the cluster head as rule AQ does for an
  auxiliary, and feeding the cluster's inner preposition into rule O's lemma set. Largest mover
  of the batch. **Census a deferred route rather than waiting for the upstream decision.**
- **Three changes make the derivation more correct at no gain in the count.** Rule BN (−2/+2) and
  rule AN's clause-head leg (−1/+1) stop `derive_unit` minting predicates at connectives and
  gapped-clause remnants; at purgatorio 33:91, paradiso 25:19 and 28:75 the LLM had proposed
  exactly the tuples the derivation was inventing, so the `missing_tuple` becomes an `extra_tuple`
  and the reading error is now reported where it belongs. Correcting `scardova` (inferno 29:83,
  a fish Layer 2 called a verb) trades the same way. The honest trade rule AM recorded.

Prompt side, unmeasured until the next round: nothing new — every diagnosis was checker-side or
upstream. Two of the eleven survivors (inferno 27:46, 28:15) are `missing_arg_adverb` residue.

---

### 12. Fourth User-Run `--fix` Round (2026-08-16)

Run by the user **ahead of the read series**, which *The Read Series* below had deferred it behind.
It therefore measures the queued prompt work against a checker that is finished for Inferno 1–30
and untouched for the remaining 70 cantos — see *What running it early costs* at the end of this
section.

- **650 → 541 soft, −109 (−16.8%)**, 62 files touched (172 insertions / 101 deletions), 0 hard,
  `pytest` 326 passed, no CRLF.
- Unit-level: **443 → 388 flagged**; 55 cleared outright, 38 improved, 350 unchanged,
  **0 regressed, 0 newly flagged**.
- Per-unit yield **0.246**, against 0.66 (round 1), 0.193 (round 2) and 0.188 (round 3) — the
  first *rise* of the series, on the base six read batches had already stripped of 444 positions.
- Eight positions are present after but not before, all inside units that net improved (the
  acceptance gate is per-unit): inferno 16:100 ×2, 16:105, 32:101; purgatorio 22:25;
  paradiso 26:72, 27:141, 33:96.
- Per canticle: inferno 137 → 109, purgatorio 258 → 212, paradiso 255 → 220.
- **Subclass results** (before → after):

  | subclass | before | after | delta |
  | --- | ---: | ---: | ---: |
  | `missing_arg` | 173 | 124 | −49 (−28.3%) |
  | `extra_arg` | 129 | 117 | −12 (−9.3%) |
  | `extra_arg_subject` | 110 | 96 | −14 (−12.7%) |
  | `role_mismatch` | 82 | 73 | −9 (−11.0%) |
  | `missing_arg_subject` | 60 | 54 | −6 (−10.0%) |
  | `missing_arg_adverb` | 24 | 21 | −3 (−12.5%) |
  | `extra_arg_adjective` | 20 | 19 | −1 (−5.0%) |
  | `missing_tuple_nominal` | 18 | 16 | −2 (−11.1%) |
  | `extra_tuple` | 16 | 12 | −4 (−25.0%) |
  | `extra_tuple_adjective` | 7 | 0 | **−7 (−100%)** |
  | `membership` | 5 | 5 | ±0 |
  | `extra_tuple_adverb` | 3 | 2 | −1 (−33.3%) |
  | `missing_tuple` | 3 | 2 | −1 (−33.3%) |

**What the round was a test of, and what it decided.** The three items *A Fourth `--fix` Round*
put on the scale, in order:

1. **The subject branches — negative.** `extra_arg_subject` −12.7% and `missing_arg_subject`
   −10.0% are the round average, not the "largest single-round drop since `extra_tuple_adverb`'s
   debut" that `_CONV_SUBJECT`'s three diagnoses (postverbal subjects, proclitics read as
   subjects, coordination-shared subjects) would have produced if they were the real causes. By
   the test's own stated branch, **the two largest buckets in the residue become read-work**: 96
   `extra_arg subj` (22 of them ∅ (0,0)) and 54 `missing_arg subj` at base 541.
2. **`missing_tuple_nominal`'s rewritten question — negative.** 18 → 16. The class has now been
   given a correct convention, a correct hint *and* a rewritten question across two rounds and
   has moved by single digits each time. **Phase 5w's law is not about convention prose
   specifically**: a class whose positions are genuine reading disagreements does not move for any
   prompt surface. Read the 16.
3. **`_CONV_REPEATED` against the `missing_arg obl` family — the round's one clear win, but not
   cleanly attributable.** `missing_arg` fell 28.3% (−49 of the round's −109) while its branched
   adverb sibling fell only 12.5%, which points at the repeated-slot convention rather than the
   adverb branch. `missing_arg obl` stands at 40 (from 68 at base 691).

Two results nobody had queued:

- **`extra_tuple_adjective` 7 → 0.** This class was position-identical across rounds 2 and 3 and
  was explicitly listed as a route to *read* rather than write more prose for. Rules AU/AY/AZ
  (secondary predicates and depictives) took it from 13 to 7, and the round took the rest. The
  route closes without the read it was waiting for.
- **Per-unit yield rose for the first time.** Round 3 had already shown the fall (0.66 → 0.193) is
  a function of what precedes a round rather than of residue depth; a round preceded by six read
  batches yielding *more* per flagged unit than one preceded by one batch is the stronger form of
  that evidence.

**What running it early costs.** *The Read Series* deferred this round because a round rewrites
the artifact: a rule written afterwards is measured against a base the round already moved, so the
rule's effect and the round's can no longer be separated. That confound is now real for the
fifteen batches still to read (inferno 31–34 through paradiso 33, 469 positions at base 541), and
it is not recoverable — the base they will be measured against is this one. What was bought for it
is that the two prompt questions above are answered now rather than after the series, and both
answers convert prompt work into read work, which is the series' own currency. The series itself is
unaffected in method: it needs the positions, not a frozen base.

**Not recorded in [`CORRECTIONS.md`](CORRECTIONS.md).** A `--fix` round is LLM regeneration of the
artifact, not a hand-applied correction to it. `*/CORRECTIONS.md` is the record of manual,
per-position corrections — upstream retags, gated-script rewrites, checker rules and the shapes
deliberately left alone. Round measurements live here, in *Chronological Record*, and
in the root [`../PLAN.md`](../PLAN.md).

### 13. Rules BO-BV and the Inferno 31-34 Read (2026-08-16)

Per-position read of all **37** soft violations in Inferno 31-34. **541 → 506 (−35, −6.5%)**,
zero model calls; Inferno 31-34 itself 37 → 16 (31: 20 → 8, 32: 8 → 5, 33: 4 → 2, 34: 5 → 1).
The first batch measured against a base a `--fix` round has moved, which is the cost §12 recorded:
these numbers are not comparable with the AG-BN series', because the easy positions of every class
round 4's prompts cover are already gone. Full grammar specification in [`RULES.md`](RULES.md);
upstream retags in [`CORRECTIONS.md`](CORRECTIONS.md).

| rule | shape | census | net |
|---|---|---:|---:|
| **BO** | rule AI runs **before** rule D: the weaker rule was silencing the stronger one's other half | — | −2 |
| **BP** | "is this the predicate's own child" reads an `aux`/`cop` head through to its lexical word | 53 | −1 |
| **BQ** | rule BJ's other two orders: the adverb cluster's nominal hangs **bare**, or the preposition is on the adverb | 11 | −6 |
| **BR** | a derived argument buried in a Layer-3 noun phrase the LLM named by its head | 404 / 8 | −8 |
| **BS** | rule Y from the other end: the LLM names the copula of a nominal predication | — | −4 |
| **BT** | rule AE's embedded side: the clause's own governor is the slot it fills | 765 → 92 | −3 |
| **BU** | the subject a coordination supplies from its **last** conjunct | 74 | −2 |
| **BV** | a `fixed` word of a multiword preposition names the nominal it opens | 196 rows | (with the retags) |

Plus 15 Layer-4 rows, 2 Layer-2 rows, 1 Layer-3 span and 1 case-annex row (**−7** for the retags,
**−2** for the `con esso` normalization together with rule BV and the inferno 31:143 re-parse), and
`pytest` **342**.

Three findings worth carrying forward:

- **"Which checks run before a rule" has a third form: a rule's own gate.** The 26-30 batch found
  rule AQ complete inside `_classify_divergence` and absent from the membership check that runs
  first. Here the same normalization was missing *inside* nine rules: each asked "is this argument
  the predicate's own dependent" against Layer 4's raw head, and **53 arguments corpus-wide hang on
  an auxiliary or a copula** instead of on the lexical verb carrying the tuple (inferno 31:64).
  `derive_unit` has read through that edge since rule AM. One helper (`_hosts_child`, rule BP)
  fixes all nine; rules BS and BV are the same normalization on a tuple-side and a
  preposition-side gate. **Ask of every gate which edge it is reading, not only which rule reads
  it.**
- **Rule ordering cuts the other way too.** The 21-25 batch found a rule's citation being rewritten
  by a collapse that ran *after* it. Rule BO is the loss upstream of that: rule D and rule AI both
  fire on a given citation the derivation does not carry, and rule D — the weaker answer, which
  drops the citation and leaves the derived position reported — ran first. Two lines swapped.
- **The mirror leg was measured and dropped, the first time in the series.** Rule BR's mirror
  measured −6/+0 and was still declined: on the derived side both positions are arguments Layer 4
  itself asserts, but on the given side the only evidence is a Layer-3 span, and **Layer 3 is
  deliberately over-inclusive**. Two of the six it removed were LLM errors silenced for the wrong
  reason (inferno 16:21, paradiso 13:45). "Check the mirror leg" stays standing advice; it is not
  an entitlement to land one.

Two candidates were censused and **dropped**: the `da` + infinitive gerundive (inferno 32:7,
"impresa **da pigliare** a gabbo") at a population of 8 whose host role is not constant across
them, and rule BR's mirror leg above. Prompt side: nothing new — every diagnosis was checker-side
or upstream.

### 14. Rules BW-BZ and the Purgatorio 1-5 Read (2026-08-16)

Per-position read of all **14** soft violations in Purgatorio 1-5. **506 → 481 (−25, −4.9%)**,
zero model calls; Purgatorio 1-5 itself 14 → 10 (1: 1 → 1, 2: 4 → 3, 3: 1 → 0, 4: 2 → 3,
5: 6 → 3). The first batch outside Inferno, and the smallest of the series by base count. Full
grammar specification in [`RULES.md`](RULES.md); upstream retags in [`CORRECTIONS.md`](CORRECTIONS.md).

| rule | shape | census | net |
|---|---|---:|---:|
| **BW** | rule BM's mirror leg: an argument Layer 4 parked in the predicate's `mark` slot | 63 / 19 | −9 |
| **BX** | rule AZ's `missing_arg` leg: the bare adjectival oblique the LLM omits entirely | 44 / 11 | −11 |
| **BY** | the LLM splits one periphrasis's arguments across the lexical verb and its `aux` | 5 | −3 |
| **BZ** | the `conj` chain is walked **before** the pass that would resolve it | 372 | ±0 |

Plus 2 Layer-4 rows and 1 case-annex row (**−2**), and `pytest` **351**.

Two findings worth carrying forward:

- **Rule ordering, for the third batch running — and now inside the derivation.** The 21-25 batch
  found two acceptance rules in the wrong order; the 26-30 batch a rule present in one check and
  absent from the one that runs first; the 31-34 batch a rule's own gate reading the un-normalized
  edge. Rule BZ is the same defect in `derive_unit`'s **predicate census**, which has three passes
  — clause-head deprels, `conj` chains resolving to one of those, then argument-bearing verbs —
  and asks "does my chain end in a predicate?" before the third pass has added any. "com' io
  **rimango** sol, se non **restai**" (purgatorio 4:45): `rimango` is the `obj` of `rimira` and
  becomes a predicate only in pass 3, so its conjunct was dropped. **A pass that reads a set
  another pass writes must run after it, or again.** The second walk is restricted to *finite*
  verbs by rule BN's own test — would the promoted position carry a tuple at all — because a
  nominal or a bare infinitive conjunct yields an empty one.
- **A census of 1 is a census.** Two positions produced candidate rules that a one-line script
  killed before either was written: the verbless comparison Layer 4 heads on the *marker* itself
  ("com' om che va", 2:130) occurs once corpus-wide, and the copular subject/complement exchange
  ("Che è ciò?", 2:120) is the only pure `subj`↔`attr` swap in the residue. The same script
  measured the known `obj`↔`subj` swap at 8 positions across 4 predicates — the open route, sized
  rather than reopened.

Rule BY is worth noting for what it does **not** take: routed through rule X's
`_complement_hosted_argument`, it inherits that rule's role-must-match gate, so purgatorio 2:66
("ne parrà gioco", a given `obl:di` on the copula against a derived bare `obl` on the nominal
predicate) stays flagged — relocating an argument is a convention, relabelling it is a second
claim, and no single rule in the checker does both.

Prompt side: nothing new — every diagnosis was checker-side or upstream. Of the ten survivors,
three are adjunct omissions (one of them the repeated-slot shape `_CONV_REPEATED` addresses) and
one is `advcl`-read-as-complement residue.

### 15. Rules CA-CJ and the Purgatorio 6-10 Read (2026-08-16)

Per-position read of all **35** soft violations in Purgatorio 6-10. **481 → 448 (−33, −6.9%)**,
zero model calls; Purgatorio 6-10 itself 35 → 19 (6: 3 → 2, 7: 3 → 1, 8: 6 → 2, 9: 13 → 7,
10: 10 → 7). Ten rules, the largest count of any batch. Full grammar specification in
[`RULES.md`](RULES.md); upstream retags in [`CORRECTIONS.md`](CORRECTIONS.md).

| rule | shape | census | net |
|---|---|---:|---:|
| **CA** | rule BN's argument test on the `conj` branch: an argumentless nominal conjunct is not an elided clause | 209 | −10 |
| **CC** | rule CA's argument leg: the promoted coordinate nominal, in the slot the LLM gives it | (CA's) | −5 |
| **CJ** | rule V's oblique leg: the controller Layer 4 labelled `obl` | — | −4 |
| **CF** | the controller a fused clitic hides (`tenerla serrata`) | 66 | −3 |
| **CH** | rule Z's adnominal leg: a verb in `amod`/`acl` is a reduced relative clause | 5019 | −3 |
| **CB** | an oblique the tree hangs on a predicative complement the derivation never promotes | 566 / 551 | −2 |
| **CG** | the coordinate oblique whose noun is elided, citable only by its adjective | 56 | −2 |
| **CD** | the coordination-head walk stops where argument coordination ends | — | −1 |
| **CE** | the antecedent and the relative pronoun of its own relative clause are one referent | 2061 | −1 |
| **CI** | rule AA's host test read through rule C's collapse | — | −1 |

Plus 1 Layer-4 row (**−1**), and `pytest` **372**.

Three findings worth carrying forward:

- **An empty tuple is not a reading — and the argument has a measured boundary.** Rule BN refused
  to mint a predicate at a conjunction in a clause-head deprel with no arguments, because no
  reading can fill the tuple. Rule CA is that test on the `conj` branch ("Sordel rimase e
  **l'altre genti** forme", 9:58; "sen venne suso; e **io** per le sue orme", 9:60). Pushing it one
  step further — dropping *every* non-verb clause head with no argument children — was measured at
  **+168** and rejected: those positions are copular predicates with pro-drop subjects, which the
  corpus's own convention has the LLM propose. The same measurement is why rule CA exempts a
  conjunct with a `cop`/`aux` child; that exemption costs **nothing** in the count and was found by
  `pytest` failing on inferno 1:7 while the count stood still. **Generalize a refusal only as far
  as the diff says.**
- **A rule and its acceptance leg can come from one test.** Rules CA and CC are the same question
  — is a promoted conjunct an elided clause or a coordinate argument? — answered on the derivation
  side and the acceptance side from the identical gate. Writing only the first leaves the nominal
  with no slot in either reading; writing only the second leaves the phantom predicate standing.
  Worth asking of every `derive_unit` refusal: *what fills the slot now?*
- **Rule C's collapse is itself a rule, and it can be wrong.** Two of the ten (CD, CI) are about
  the coordination-head walk rather than about any acceptance: CD stops it where it would leave the
  arguments' coordination for the predicates', and CI makes rule AA's host gate read it. The
  31-34 batch's "which *edge* does a gate read" now has a companion: **which normalization has
  already run on the citation this gate compares?**

Prompt side: nothing new — every diagnosis was checker-side or upstream. Of the 19 survivors, four
are the LLM reading a `conj`/`advcl` clause as a `ccomp` (7:53, 8:50 residue, 9:72), two are the
elided speech verb it declines to name at all (6:49, 8:91), and one (9:97) is a Layer-4 parse the
read worked out in full and deliberately did **not** rewrite, because every arrangement of it
trades two violations for two or three and the line does not decide between them.

---

### 16. Rules CK-CO and the Purgatorio 11-15 Read (2026-08-16)

Per-position read of all **30** soft violations in Purgatorio 11-15. **448 → 427 (−21, −4.7%)**,
zero model calls; Purgatorio 11-15 itself 30 → 15 (11: 5 → 4, 12: 3 → 2, 13: 1 → 1, 14: 15 → 3,
15: 6 → 5). Full grammar specification in [`RULES.md`](RULES.md); upstream retags in [`CORRECTIONS.md`](CORRECTIONS.md).

| rule | shape | census | net |
|---|---|---:|---:|
| **CK** | the LLM names a subordinate clause by the complementizer that opens it | 18 / 3 | −5 |
| **CM** | rule AL read through the `case` annex: a fused clitic whose two slots back the two roles separately | 13 / 7 | −2 |
| **CL** | rule AG's third leg: once the inherited subject is dropped, the slot is rule V's to decide | — | −2 |
| **CN** | rule AN's slot assignment: a ∅ slot goes to the **back** of the queue | — | −1 |
| **CO** | rule AU's `advmod` leg: a second predicative adjective on the predicate's own complement | 101 / 77 | −1 |

Plus the `dep.subject_agreement` coordinated-subject refinement, 11 Layer-4 rows, 8 Layer-2 rows,
1 Layer-3 span and 1 case-annex row (**−10 / +2** together), and `pytest` **384**.

Three findings worth carrying forward:

- **A deferred route is worth re-deriving, not just re-running.** The Inferno 21-25 batch measured
  `dep.subject_agreement`'s *coordinated subject* exclusion restricted to the number test at **12
  new `dep --check` soft violations** and reverted it; "clear the 12" has been a standing route
  since. This batch ran into it at purgatorio 14:75 and, reading all 12, found the deferred
  refinement **half right**: a coordination has a person, but Italian lets the finite verb agree
  with *one member* of it, in either direction ("'l duca e io … **fui**", "né io né altri 'l
  **crede**"). Testing against **every** conjunct leaves 6, and all 6 are upstream errors the
  session corrected. The route closes at −3/+1 in Layer 5 with `dep --check` back at 0. **A route
  parked on a count may be parked on the wrong rule.**
- **A canto can be an upstream canto.** Purgatorio 14 held 15 of the batch's 30 positions and gave
  **12 of them to the tree or the morphology** — the highest upstream share of the series, against
  a corpus where `dep --check` and `morph --check` both stand at 0. One Layer-2 mistag (`parte`
  read as the verb `partire`, 14:69) cost three Layer-5 violations on its own, by turning an
  adverbial into a clause and forcing a `conj` subject inheritance. **The upstream checks being
  clean is not evidence that a canto is.**
- **The measured variant is the argument.** Rule CN's first form — dropping ∅ slots from the
  gapped-remnant queue outright — took 2 and was *wrong*: paradiso 4:113 ("tu … intende de la
  voglia assoluta, e **io** de l'altra") is a genuine contrastive subject remnant under a pro-drop
  head. Moving ∅ to the **back** of the queue instead takes 1 and derives 4:113 correctly. The
  count was better for the wrong rule, which is what the diff-plus-read discipline is for.

Two candidates were censused and **dropped**: the Layer-3 NP-head duplicate citation (census 5,
would clear 2 — declined because one of the two, paradiso 10:142, is a real subject/object
question the rule would silence on the strength of an over-inclusive Layer-3 span, the same ground
the Inferno 31-34 batch declined rule BR's mirror on), and — in effect — the 15 of rule CK's 18
censused positions that pair the LLM's `subj` against a derived `ccomp`, which is the impersonal
subject-clause question rather than a citation convention. Prompt side: nothing new — every
diagnosis was checker-side or upstream.

Of the 15 survivors, five are the LLM omitting an adjunct or dative the tree records, three are
net-zero upstream retags applied for correctness, two are predicates the LLM mints where the line
carries none, and one each are rule CL's gate holding (14:60), `quanto` read as a subject (12:24),
the copular subject/complement exchange (15:32, now censused at 2 after the Purgatorio 1-5 batch
found 1), a Latin quotation as a passive subject (15:39), and rule CK's own role boundary (11:41).

### 17. Rules CP-CT and the Purgatorio 16-20 Read (2026-08-16)

Per-position read of all **26** soft violations in Purgatorio 16-20. **427 → 409 (−18, −4.2%)**,
zero model calls; Purgatorio 16-20 itself 26 → 14 (16: 11 → 6, 17: 1 → 0, 18: 3 → 1, 19: 6 → 4,
20: 5 → 3). Full grammar specification in [`RULES.md`](RULES.md); upstream retags in [`CORRECTIONS.md`](CORRECTIONS.md).

| rule | shape | census | net |
|---|---|---:|---:|
| **CP** | rule AZ's noun leg: a bare caseless `obl` **nominal** is the predicate's secondary predicate | 245 / 44 | −5 |
| **CS** | a derived predicate whose tuple is **empty** asserts nothing, so its absence is not a divergence | — | −2 |
| **CQ** | rule T's `xcomp` leg: the prepositional infinitive Layer 4 marked with `case` and attached as a complement | 4 | −2 |
| **CT** | a copula Layer 4 hung **under** its own predicate complement | 25 / 294 | −2 |
| **CR** | `dep.subject_agreement`: the 1/2-plural exclusion covers the *number* test, not the person one | 3 | −2 |

Plus 17 Layer-4 rows, 2 Layer-2 rows, 1 Layer-3 span and 2 case-annex rows (**−7 / +2** together),
and `pytest` **414 collected** (396 functions).

Three findings worth carrying forward:

- **An exclusion can be right about one feature and wrong about the other.**
  `subject_agreement` called a subject undecidable whenever the head was 1st/2nd person **plural**,
  because the tree may hold only one member of the "io e tu" it agrees with. That is a statement
  about *number*; it was taking the *person* test with it, and a lone third person cannot be a
  member of a "we" at all ("contrario suon **prendemo**", 20:102). Narrowing it surfaced exactly
  3 positions, all one shape (`ambedui`/`amendue`/distributive `uno` resuming a plural), which
  joined the set that already names that reading. The rule to carry: when a gate is written for
  one feature, check what *else* it is silencing.
- **The same reading can be right at one end of the pipeline and wrong at the other.** Rule CS's
  refusal — "a tuple with no arguments in it is not a reading" — is rules AN/BN/CA's own. Applied
  at the **census** end, by POS, it measured **+180**, because a non-verb clause head with no
  argument child is usually a copular or controlled predicate whose subject comes from rule V.
  Applied at the **reporting** end, to the empty tuple `derive_unit` actually produced, it takes
  2 and nothing else. Where a rule is placed decides what it means.
- **A canto can be an upstream canto — again.** Eleven of the 26 were Layer-2/Layer-4 errors, ten
  of them in canto 16, which is the Purgatorio 11-15 batch's canto-14 finding repeating one batch
  later. One Layer-2 POS error (`brutta` read as the adjective *brutto* rather than the verb
  *bruttare*, 16:129) was again the whole of a divergence, as `parte` was at 14:69.

Two candidates were censused and **dropped**: the LLM naming a marked clause by a nominal *inside*
it (16:118, "per qualunque lasciasse" — censused at **243** verbs carrying both a `case` child and
a nominal argument, far too broad a licence for one position), and the non-finite argumentless
conjunct (16:120), which rule BZ decided deliberately and rule CS now says the same thing about
from the other end.

**Prompt side, the first lead since round 4 emptied the queue**: four of the batch's 26 are the LLM
omitting an oblique or a dative the tree records (19:7 "**Ne l'ora** … mi venne in sogno", 19:67
the simile's own correlative `falcon`, 19:86 the dative clitic `m'`, 19:113 "**Fino a quel
punto**"). `missing_arg obl` is now the residue's largest single bucket at **81 of 409** (20%), and
59 of the 81 cite an argument on a different line from the predicate. Nothing in the conventions
tells the model that a prepositional adjunct of time or place attached to the predicate is an
argument to cite — `_CONV_ADVERB_ARG` says it only for bare adverbs. This is a *candidate*, not a
measured defect: it is worth a convention clause and a round to test, on the same terms as
`_CONV_ADVERB`'s omission licence, which is the only prompt change that has ever collapsed a class.

---

### 18. Rules CU-CY and the Purgatorio 21-25 Read (2026-08-16)

Per-position read of all **33** soft violations in Purgatorio 21-25. **409 → 388 (−21, −5.1%)**,
zero model calls; Purgatorio 21-25 itself 33 → 24 (21: 9 → 5, 22: 6 → 6, 23: 2 → 1, 24: 7 → 1,
25: 9 → 11). Full grammar specification in [`RULES.md`](RULES.md); upstream retags in [`CORRECTIONS.md`](CORRECTIONS.md).

| rule | shape | census | net |
|---|---|---:|---:|
| **CW** | rule BA's oblique leg: the rest of the elided clause the second derived subject opens | 85 / 13 | −7 |
| **CX** | rule CK widened from the complementizer to the **interrogative word** that opens the clause | 6 | −6 |
| **CU** | a ∅ subject the LLM lists **beside** the derived one is the slot not decided | 6 / 4 | −3 |
| **CV** | `dep.subject_agreement`: the number-only exclusions ran *before* the person test | — | −3 |
| **CY** | the clausal-complement double-listing test, read through the `aux` edge | 1 | −1 |

Plus 27 Layer-4 rows and 1 Layer-2 row (**−8 / +7** together), and `pytest` **427 collected**.

Three findings worth carrying forward:

- **A rule's own evidence names more than the slot it was written for.** Rule BA reads two derived
  subjects on one predicate as the tree collapsing *two clauses* onto one head, and concludes only
  that the subject slot is undecided. But if the evidence is a collapse, then everything else the
  second clause left behind — its obliques, its object, its complement — is equally not this
  predicate's, and identifying it needs nothing but token order: it stands *after* the second
  subject. That is rule CW, seven positions for one line of gating, and the question to carry is:
  **when a rule accepts an argument on some evidence, what else does that evidence cover?**
- **The exclusion defect was in six places, and it was an ordering defect.** Rule CR narrowed the
  1/2-plural exclusion to its number half one batch ago, and delegated the coordinate case to "the
  conjunct branch below" — but returning is what stops that branch from running, so the delegation
  never happened. Reading around it showed the same confusion in **five more** exclusions, every
  one of them a number licence returning "undecidable" for person as well. Running the person test
  first and keeping the number licence as a flag is the whole of rule CV. Ordering has now been a
  finding in six consecutive batches, and this is its most literal form: *a comment that names a
  later branch as the judge is a claim the code has to keep.*
- **An upstream correction can raise the count and still be right.** Purgatorio 25:67 (+2) and
  22:90 (+4 / −2) are Layer-4 mis-parses whose correction *exposed* the LLM's own misreadings,
  which the wrong tree had been matching. The batch's residue therefore went 33 → 24 rather than
  to 18, and every one of the six new positions is a genuine reading disagreement now visible in
  the right place. The count is not the measure; the correctness of the parse is.

Two candidates were censused and **dropped**: rule CU's concrete variant — the LLM listing the
coordination head's subject *and* a conjunct's own, rule BU's evidence for the alternative — at
population **1** (21:6), and the perception verb's gerund complement (25:122 "udi' **cantando**",
where Layer 4 says `advcl` and the LLM `xcomp`) at population **2**. The reflexive-clitic-as-`nsubj`
shape was decided **upstream** rather than by rule: rules AB/AW/BD leave 371 reflexive clitics in
`obj`/`iobj`/`obl` as notation, but `nsubj` asserts that the clitic is the clause's subject, which
competes with the pro-drop reading the verb's own person carries, and the six positions were
retagged `expl`.

Of the 24 survivors, four are the LLM omitting an adjunct the tree records (21:36, 22:133 — taken
by rule CW — 25:10, 25:33), four are the Stage-1 `null_subject` repair's own shape at 25:49/50
(the checker has already decided them; they wait on a `--fix` round, not on a rule), six are the
two upstream corrections above, and the rest are single positions where the LLM read the line
differently — the comparative `che` cited as an object (23:4), the "non so che" idiom (24:107), the
gapped coordination's subject read as an object (25:3).

**Prompt side**: no new lead. `missing_arg obl` is still the residue's largest single bucket at
**77 of 388**, and the Purgatorio 16-20 batch's convention clause for the prepositional adjunct of
time or place remains the fifth round's one candidate.

### 19. Rules CZ-DD and the Purgatorio 26-30 Read (2026-08-17)

Per-position read of all **33** soft violations in Purgatorio 26-30. **388 → 358 (−30, −7.7%)**,
zero model calls; Purgatorio 26-30 itself 33 → 22 (26: 6 → 5, 27: 6 → 2, 28: 9 → 5, 29: 4 → 3,
30: 8 → 7). Full grammar specification in [`RULES.md`](RULES.md); upstream retags in [`CORRECTIONS.md`](CORRECTIONS.md).

| rule | shape | census | net |
|---|---|---:|---:|
| **DA** | rule CS's argument leg: an **empty** derived tuple contradicts no argument put on it — except in the subject slot | 17 | −17 |
| **DD** | the relative locative adverb Layer 4 writes as a `case` on its own clause's verb | 21 | −3 |
| **CZ** | `derive_unit`: a gapped remnant the `case` annex assigns a case to claims that slot first | — | −2 |
| **DB** | rule AD's mismatch leg: the copula's only complement, an adverb `obl` because it carries a preposition | 2 | −2 |
| **DC** | rule AA/AU's host gate read through rule CE's relative-pronoun/antecedent identity | 489 | −1 |

Plus 12 Layer-4 rows (**−7 / +2** together), and `pytest` **437 passed**.

Three findings worth carrying forward:

1. **A rule's evidence line can be the line the rule gets wrong.** Rule AN's comment promised
   slots "in the order the predicate's own arguments stand in the line" and named purgatorio
   27:108 as the case; its sort key ordered them by **role rank** instead, and had done so for
   four batches. Read the code the comment describes, not the comment.
2. **The obvious repair was wrong, and the corpus already owned the right one.** Ordering the
   queue by argument position measured −2/+3: Dante inverts a gapped clause's two halves
   chiastically (paradiso 29:78) as readily as he parallels them, so no order is the convention.
   The `case` annex decides all four evidence lines, which is rule U's third opinion applied at
   the one place in `derive_unit` that is openly guessing.
3. **A rule that breaks an existing near-miss test has been told where its gate belongs.** Rule
   DA's unrestricted form measured −23 and broke five tests of the rule-V family. They were
   right: in the *subject* slot an empty derived tuple is rule V having declined, not the
   derivation being silent. Restricted to the roles no procedure adjudicates it takes 17 of the
   23 and everything passes.

Also: **census the shape, not only the violation diff.** Rule DC moves 1 position and its
structural census is 489; its dropped sibling (the antecedent double-listed with its relative
pronoun, 28:97) moves 1 and its structural census is 1. Only the second number separates them.

**Prompt side**: no new lead, and three more instances of the standing one. `missing_arg obl` is
still the residue's largest single bucket at **76 of 351** (moved by 1 by the DE-DF batch), and the Purgatorio 16-20 batch's
convention clause for the prepositional adjunct of time or place remains the fifth round's one
candidate.

## 4. The Read Series — read the whole corpus (decided 2026-08-15, COMPLETE 2026-08-17)

**Per-position reads cover all 100 cantos in 5-canto batches, and the series is COMPLETE
(2026-08-17).** Inferno (batches 1, 1–3, 4–6, 7–10, 11–15, 16–20, 21–25, 26–30, 31–34), all of
Purgatorio (1–5, 6–10, 11–15, 16–20, 21–25, 26–30, 31–33) and all of Paradiso (1–5, 6–10,
11–15 + 16–20 read together in one session, 21–25, 26–33) have been read position by position.

**What remains is the sixth `--fix` round** — the one this series was written to enable, run
against a checker that is finished, so that its per-class numbers measure the prompt alone. See
*The Sixth `--fix` Round* below.

The series was originally declared to run *before* any further `--fix` round. That clause has now
lapsed **twice**: the fourth round ran on 2026-08-16 (§12) and the fifth on 2026-08-17 (§21), both
ahead of it, so the last seven batches were measured against a base two rounds had moved and that
cost is paid rather than pending. The reasoning below is kept because it still governs the
*sixth* round, and because it names what was traded away.

**Why read first.** Every batch so far has produced deterministic rules that remove violations at
**zero model cost** (AG: −43; AH–AL: −156; AM–AT: −75; AU–AY: −54; AZ–BI: −143; BJ–BN: −41; BO–BV: −35;
BW–BZ: −25; CA–CJ: −33; CK–CO: −21; CP–CT: −18; CU–CY: −21; CZ–DD: −30; DE–DF: −7; DG–DJ: −10; DK–DR: −27; DS–DW: −16; DX–EA: −11; EB–EF: −21), the 11–15 batch
showed the reads also find `derive_unit` itself to be wrong rather than merely silent, the 16–20
batch showed they find existing rules to be **half-written** — three of its five rules are the
mirror leg of a rule already in the checker — and the 21–25 batch found a rule that was neither
silent nor half-written but *singular where the shape is plural*, plus an ordering defect between
two rules that were each correct alone, and the 26–30 batch found a rule that was correct and
simply absent from one of the two checks that report its shape, and the Purgatorio 21–25 batch
found a rule whose own evidence licensed more than the slot it was written for, and the
Purgatorio 26–30 batch found a rule that had been *describing an intention its own sort key did
not implement*. A `--fix` round run before those rules
exist pays a model for positions a later rule would have taken for free, and worse: a round rewrites
the artifact, so a rule written afterwards is measured against a base the round already moved, and
the two effects can no longer be told apart. Reading the whole corpus first means the round runs
**once**, against a checker that is finished, with every prompt defect the reads found already in
place — and its per-class numbers then measure the prompt alone.

The cost the deferral was meant to avoid is now incurred twice, and only the first purchase bought
anything: §12 measured the queued prompt work (the subject branches, `missing_tuple_nominal`'s
question, `_CONV_REPEATED`) and two of the three answers turned prompt routes into read routes,
while §21 ran with **no prompt change at all** and so answered no question — it recovered 53
positions and moved the base for the seven batches still to read. The standing form of the rule is
therefore weaker than "read everything first" and still worth keeping: **do not run a round while
checker rules are being written against the base it would move, and do not run one with nothing on
the scale.** Both conditions are now met for the first time: the series is finished, so no rule is
being written against the base, and two prompt clauses are on the scale.

### 20. Rules DE-DF and the Purgatorio 31-33 Read (2026-08-17)

Per-position read of all **14** soft violations in Purgatorio 31-33, the batch that finishes
Purgatorio. **358 → 351 (−7, −2.0%)**, zero model calls; Purgatorio 31-33 itself went 14 → 11
(31: 3 → 2, 32: 7 → 4, 33: 4 → 5). `pytest` **441 passed**, 0 hard, all other layers 0/0. Full
grammar specification in [`RULES.md`](RULES.md); upstream retags in [`CORRECTIONS.md`](CORRECTIONS.md).

| rule | shape | census | moved |
|---|---|---:|---:|
| **DF** | rule V's control candidates read through rule AI's Layer-3 NP-head equivalence | — | −4 |
| **DE** | rule C's collapse: a conjunct's role never displaces the coordination head's own | 98 | −2 |

Upstream: 4 Layer-4 rows (purgatorio 31:15 — six cells of one line, 32:67, 33:18, 33:109 ×2),
1 Layer-2 row (31:15 `fuor`), 2 Layer-3 spans (inferno 18:30, purgatorio 33:26) and 2 case-annex
rows, **−6 / +5** between them. One candidate was censused and dropped, at **2** against a
structural population of 1026.

**The batch's finding — the two rules are the same finding twice.** Neither is a new reading of
Italian. Rule DF is rule AI applied where rule AI cannot run, and rule DE is rule C's own
tie-break told which of two citations is authoritative; both are gates comparing raw positions
while the checker already held the answer one function away. That is the ordering question in a
**fifth consecutive form** — after the Purgatorio 1-5 batch (a pass reading a set another pass
writes), 6-10 (which normalization has already run on the citation a gate compares), 21-25 (one
rule preempting another), 26-30 (a comment describing an intention its sort key did not
implement) and the Inferno 31-34 batch (which *edge* a gate reads). It is now the single most
productive question to ask of this checker.

**Two smaller ones.**

- **A rule's gate can be found by the position it wrongly takes, not by census.** Rule DE
  unrestricted measured −2/+1, and the +1 (purgatorio 3:30, an apposition) named the gate exactly:
  the conjunct must carry a `case` marker of its own. The census (98) confirmed the population
  afterwards; it could not have found the boundary.
- **A Layer-3 span that is not a phrase is not over-inclusion.** Layer 3 is over-inclusive by
  design and its wide spans are normally left alone — but rules AI and DF read a span's `head` as
  an argument's *alternative name*, so a span covering two different nominals makes them
  equivalent. Rule DF's one wrong acceptance (inferno 18:30, `[la gente modo colto]`) was a span
  of that kind, and the fix was upstream.

**What the batch left standing (11).** Two genuine disagreements on one tangled line (32:69), two
plain `missing_arg obl` omissions (32:139), and seven positions where a correction exposed the
LLM's own misreading rather than the tree's — see [`CORRECTIONS.md`](CORRECTIONS.md).

### 21. Fifth User-Run `--fix` Round (2026-08-17)

Run by the user after the Purgatorio 31–33 read closed Purgatorio, and **again ahead of the
schedule** *A Fifth `--fix` Round* below had set for it (which was: after the series finishes, and
only with new prompt-side diagnoses on the scale). Neither condition held.

- **351 → 298 soft, −53 (−15.1%)**, 33 files touched (75 insertions / 51 deletions), 0 hard,
  `pytest` 441 passed, no CRLF. All four other layers stay 0 — the round touched `skel/*.tsv` only.
- Unit-level: **264 → 233 flagged**; 31 cleared outright, 10 improved, 223 unchanged,
  **0 regressed, 0 newly flagged**.
- Per-unit yield **0.201**, against 0.66 / 0.193 / 0.188 / 0.246 for rounds 1–4.
- Exactly **one** position is present after but not before (paradiso 13:82 `extra_arg obl:di`),
  inside a unit that net improved — the acceptance gate is per-unit. Round 4 had eight.
- Per canticle: inferno 72 → 60, purgatorio 114 → 87, paradiso 165 → 151.
- **Subclass results** (before → after):

  | subclass | before | after | delta |
  | --- | ---: | ---: | ---: |
  | `missing_arg` | 84 | 70 | −14 (−16.7%) |
  | `extra_arg_subject` | 60 | 50 | −10 (−16.7%) |
  | `extra_arg` | 58 | 51 | −7 (−12.1%) |
  | `role_mismatch` | 54 | 50 | −4 (−7.4%) |
  | `missing_arg_subject` | 44 | 39 | −5 (−11.4%) |
  | `missing_arg_adverb` | 15 | 11 | −4 (−26.7%) |
  | `missing_tuple_nominal` | 12 | 10 | −2 (−16.7%) |
  | `extra_arg_adjective` | 9 | 6 | −3 (−33.3%) |
  | `membership` | 6 | 5 | −1 (−16.7%) |
  | `extra_tuple` | 4 | 4 | ±0 |
  | `missing_tuple` | 3 | 1 | −2 (−66.7%) |
  | `extra_tuple_adverb` | 2 | 1 | −1 (−50.0%) |

**The round tested no hypothesis, and that was checked rather than assumed.** `skel/skel.py` was
audited before the write-up:

- `git log -S'_CONV_' -- skel/skel.py` returns four commits, the newest **1eb2a86 (2026-08-15,
  Inferno 11–15 read)**, which added `_CONV_SUBJECT` and the rewritten `missing_tuple_nominal`
  question. Round 4 was the round that decided both, and **both came back negative**.
- The whole `1eb2a86 → HEAD` diff of `skel/skel.py` is 26/27 lines and contains no prompt text: the
  `-c` canto-range refactor (`only` → `spec`, 5e08c5d) and rule CZ's `case_rows` plumbing (b92d5e7).
- The one queued candidate — a convention clause for the **prepositional adjunct of time or
  place** — is **not in the file**: `adjunct`, `time or place`, `temporal`, `of time` all miss.
  This is not an implementation slip; *A Fifth `--fix` Round* below states it in the imperative
  ("**write it**, then let a round decide it"), so code and plan agree that it is an untouched TODO.
- `model.mk` still pins `ollama:gemma4:31b-it-qat`, unchanged since 2026-06-24.

**A round with an unchanged prompt is still not a repeat, and the −53 says why.** What moved
between rounds 4 and 5 is the *checker*: `dante_corpus/skel.py` is **+1158 / −55** since 0697024
(rules BO through DF, fifteen read batches). `--fix` consults `_classify_violations` at three
points — Stage 1's deterministic repairs run against the derivation, Stage 2's questions are keyed
by `_violation_subclass` of the *current* soft set, and every candidate is admitted only by
`_is_improvement`. So the same prompt was asked different questions about different units and
graded by a stricter gate.

What that measures is the thing no round had isolated before: **the rules and the LLM address
largely disjoint residue.** A base already stripped of 190 positions by fifteen rule batches still
gave up 15.1% to the same prompt, and the yield per flagged unit (0.201) sits in the middle of the
series rather than at its floor. Rules do not pre-empt regeneration, and regeneration does not
pre-empt rules.

**The flatness is the second reading.** Every bucket with n ≥ 9 fell between 7% and 17%; nothing
collapsed. Round 3's signature of a real prompt defect was the opposite shape — `missing_arg_adverb`
−66.3% against a flat background — so the absence of that signal here is consistent with what the
audit found in the source: there is no untested defect currently in the prompt.

**What running it early costs, measured.** Two things, both quantified rather than asserted:

1. The seven remaining Paradiso batches are now measured against a base **two** rounds have moved
   (§12 recorded the first). Paradiso 1–5 went 27 → **26** by the round alone.
2. The queued candidate's target shrank while it waited: **`missing_arg obl*` 76 → 62** (bare
   `obl` 25 → 20). When the clause is finally written, it is tested against a population 18%
   smaller than the one that motivated it.

**Not recorded in [`CORRECTIONS.md`](CORRECTIONS.md)**, for the reason §12 gives.

### 22. Rules DG-DJ and the Paradiso 1-5 Read (2026-08-17)

Per-position read of all **26** soft violations in Paradiso 1-5, the first batch of the Paradiso
series. **298 → 288 (−10, −3.4%)**, zero model calls; Paradiso 1-5 itself 26 → 18 (1: 11 → 10,
2: 2 → 0, 3: 5 → 4, 4: 4 → 2, 5: 4 → 2). `pytest` **449 passed**, 0 hard, all other layers 0/0.
Full grammar specification in [`RULES.md`](RULES.md); upstream retags in [`CORRECTIONS.md`](CORRECTIONS.md).

| rule | shape | census | net |
|---|---|---:|---:|
| **DJ** | rule CX's complement-role gate dropped where the two sides name the **same** role | 28 | −3 |
| **DI** | rule AN's acceptance leg: the gapped clause the LLM heads on its own remnant | 13 / 2 | −2 |
| **DG** | the *membership* check read through rule C's coordination collapse | — | −1 |
| **DH** | rule CW's mirror leg: the elided clause is the **first** one | 64 / 2 | −1 |

Plus 6 Layer-4 rows, 1 Layer-2 row, 1 Layer-3 span and 2 case-annex rows (**−4 / +1** together).

**The batch's finding — ask a gate what it does when the two sides agree.** Rule CX requires both
roles to be complement roles, and that requirement is *about a disagreement*: it licenses `obj` ↔
`ccomp` as notation rather than two claims. Written for the case where the roles differ, it
silently excluded the case where they are identical — which is strictly the weaker claim, since
the two readings then disagree about nothing except which token names the filler. "Veramente
**quant'** io del regno santo / ne la mia mente potei **far** tesoro, / sarà ora materia del mio
canto" (1:12) is that case in the subject slot, and rule CK's own censused core (the free relative
opened by `chi`) is the same shape. One condition rewritten, three positions, and two shapes
nobody had proposed a rule for. **A gate that admits a specific disagreement should always be
asked what it does with none.**

**Three smaller ones.**

- **Ordering, for the sixth consecutive batch, and in a form already named.** Rule DG is rule AQ′
  exactly — a normalization complete inside `_classify_divergence` and absent from the membership
  check that runs before it (5:67, two compared infinitives Layer 4 writes as a `conj`). The
  question "which checks run *before* this rule" has now produced a rule in six batches running.
- **A mirror leg found by asking which of two readings the LLM took**, not by asking which
  direction the rule was written for. Rule CW assumes the LLM read the *first* of two collapsed
  clauses; at 2:22 the verb's own 1sg morphology says it read the second, and the gate that keeps
  the legs disjoint is simply which subject the LLM named.
- **A refusal in `derive_unit` still needs its acceptance leg.** The Purgatorio 6-10 batch's
  standing question ("what fills the slot now?") applied to rule AN, which has refused to mint a
  predicate at an `orphan`-marked gap since the Inferno 11-15 batch and never said what happens
  when the LLM mints one there instead (rule DI).

**One candidate censused at 29 and dropped on the corpus's scope boundary.** A given `subj`
against a derived `xcomp` on the same infinitive is the impersonal-verb reading (`convien`,
`piacque`, `parve`, `est`), and rule M already accepts the reverse direction — but only 3 of the
29 are reported, and the 29 are not one shape: modals and causatives (`puote cader`, `lascia
veder`, `fé pianger`) sit in the same census and are not subject clauses on any reading.
Separating them needs a list of impersonal verbs, which is **an imported verb-valency lexicon by
another name** — the one instrument the root [`../PLAN.md`](../PLAN.md)'s *Out of scope* names and
rejects. Left flagged: paradiso 1:61, 5:37, purgatorio 2:120.

**One Layer-4 correction deliberately raises the count by +1.** At 1:81 the old tree read `lago`
as a third conjunct of the subject and `alcun` as a determiner of `pioggia`, which is not Italian;
the LLM's own misreading had been matching it closely enough to be half-hidden, and with the tree
correct all four of its divergences surface. The fourth batch in the series to record that trade.

### 23. Rules DK-DR and the Paradiso 6-10 Read (2026-08-17)

Per-position read of all **18** soft violations in Paradiso 6-10, the second batch of the Paradiso
series. **288 → 261 (−27, −9.4%)**, zero model calls; Paradiso 6-10 itself 18 → 6 (6: 0 → 0,
7: 7 → 4, 8: 5 → 1, 9: 5 → 1, 10: 1 → 0). `pytest` **465 passed**, 0 hard, all other layers 0/0.
Full grammar specification in [`RULES.md`](RULES.md); upstream retags in [`CORRECTIONS.md`](CORRECTIONS.md). Eight rules is the second-largest count of
the series, after the Purgatorio 6-10 batch's ten.

| rule | shape | census | net |
|---|---|---:|---:|
| **DO** | rule AG's agreement test asked of the two **predicates** | 30 / 1151 | −5 |
| **DQ** | the impersonal verb whose subject is its own `che`-clause | 217 | −5 |
| **DL** | rule DB's part-of-speech gate dropped | 414 / 492 | −5 |
| **DP** | the relative clause with **no relativizer at all** | 474 / 3261 | −3 |
| **DK** | the antecedent, where the derivation names its clause's relative pronoun | 2574 / 3261 | −2 |
| **DR** | `quasi`, rule AR's third comparison marker | 9 / 52 | −2 |
| **DM** | rule AK's gate read as the negative its docstring states | 33 / 150 | −1 |
| **DN** | the subject Layer 4 writes on the `xcomp` infinitive | 106 / 1130 | −1 |

Plus 10 Layer-4 rows, 2 Layer-2 rows and 2 case-annex rows (**−3** between them).

**The batch's finding — read a rule's stated reason, then ask which of its conditions that reason
requires.** Rules DL and DM are one defect twice. Rule DB's docstring names its deciding gate
outright ("the copula must have no other complement … `essere` with none is predicating *this*
phrase or nothing") and the code carried a second condition beside it: the complement must be an
adverb, inherited from rule AD, where it is load-bearing, and from the single line that motivated
rule DB. Rule AK's docstring says its `come` mints an oblique "out of a token no layer calls a
preposition" and the code gated on Layer 2 calling it a *conjunction* — one of the three tags the
census finds on the same particle. Neither extra condition appears in either rule's reasoning;
between them they were hiding six positions across five cantos and all three canticles.

This is the Purgatorio 26-30 batch's finding with the polarity reversed. There, rule AN's comment
described an ordering its sort key did not implement, and the code was wrong about what the
comment claimed. Here the comment is right and the code is *narrower* than its own claim. **Prose
and gate disagreeing is a finding either way**; which of the two to keep is decided by census.

**Three more.**

- **A scope refusal is about the instrument, not the shape.** §22 censused the impersonal-verb
  reading at 29 and dropped it, correctly, because separating `convien` from `puote` needs a list
  of impersonal verbs — [`../PLAN.md`](../PLAN.md)'s *Out of scope*. Rule DQ takes five of that
  family with no list at all, because it stops classifying the verb: the derivation's subject must
  be **inherited** across `conj` (nothing in the predicate's own clause was ever a candidate) and
  a `ccomp` must be the only other thing derived for it. Both gates are structural. A refusal
  answers the instrument it was offered and says nothing about the shape.
- **Check a rule's test against both ends of the relation.** Rule AG compares the inherited
  nominal with the predicate it lands on. It never compares the **donor** predicate with the
  recipient — and that comparison is decidable exactly where the first is not, since a
  third-person noun agrees with every third-person verb. Census: of 1151 inheritance candidates
  rule AG calls 232 *disagree*; rule DO adds 30, of which 5 are cases rule AG calls *agree*.
- **Price a derivation rule as an acceptance first.** Rule DN in `derive_unit` — mint the `xcomp`
  infinitive's overt subject as the matrix predicate's — measured **−4 / +40**, because an overt
  subject under an `xcomp` is usually the accusative-and-infinitive's own and asserting it
  overrode 24 pro-drop ∅ subjects. The same evidence read as an acceptance is −1 / +0. Rule CS's
  variant (+180, §17) was the first instance; this is the second, and it is now worth doing by
  default.

**Two gates found by things other than census.** Rule DP's first form accepted purgatorio 31:86
wrongly and the **violation diff** named the boundary — the clause's relativizer `qual` is outside
the four-word relative-pronoun set rules CE/DC/DK read, so the gate had to become a *wider* list
used *negatively*. Its second form broke two of rule BT's near-miss **tests**, which were right: a
relative clause's head standing as that clause's predicate complement is the free-relative shape
rules AE and BT already adjudicate. Census counts a population; the diff and the near-miss tests
find boundaries.

**One correction deliberately leaves the count where it was, twice.** paradiso 7:142 and 9:135
each remove a violation and expose a different one, because the LLM's own misreading had been
matching the wrong tree closely enough to stay hidden. The fifth and sixth batches in the series
to record that trade.

### 24. Rules DS-DW and the Paradiso 11-20 Read (2026-08-17)

Per-position read of all **43** soft violations in Paradiso 11-20 — the third *and fourth* batches
of the Paradiso series, read in one session — following *How to Read a Batch* ([`PLAN.md`](PLAN.md)). **261 → 245
(−16, −6.1%)**, zero model calls, 0 hard; Paradiso 11-20 itself **43 → 30** (11: 5 → 7, 12: 6 → 5,
13: 4 → 2, 14: 6 → 4, 15: 7 → 5, 16: 6 → 1, 17: 4 → 3, 18: 1 → 1, 19: 3 → 1, 20: 1 → 1).
`pytest` **475 passed**.

Five deterministic rules, each censused corpus-wide before it was written, measured on its own by
full-corpus violation **diff**, and pinned by a mutation-checked test.

| rule | shape | census | moved |
|---|---|---:|---:|
| **DU** (`derive_unit`, step 3) | the shared-subject propagation across `conj` **stops at a conjunct Layer 4 marks with its own subordinator** | 49 | **−8/+1** |
| **DW** (`_depictive_attr_omitted`) | rule BX's `attr` leg: the depictive Layer 4 wrote in the complement slot rather than loose as an `obl` | 100 | **−2** |
| **DS** (membership check) | rule BW, applied where the citation is still raw: the interrogative `mark` that opens a clause and fills one of its slots | 325 | **−1** |
| **DT** (`_coordination_head`) | `compound` collapses onto its head like `flat` (rule BE) | 2 | **−1** |
| **DV** (`_stranded_on_underived_complement`) | rule CB read through rule AU's host: the oblique stranded on an `amod` over one of the predicate's own arguments | 119 | **−1** |

Plus **9 Layer-4 rows** and **1 Layer-2 row** (see [`../dep/CORRECTIONS.md`](../dep/CORRECTIONS.md),
[`../morph/CORRECTIONS.md`](../morph/CORRECTIONS.md)), worth −9/+5 between them.

### The batch's findings

**1. A rule can measure −3/+0 and still be wrong — read the positions the diff removes.** Rule DQ
(§23) accepts an impersonal verb's inherited subject when a `ccomp` is the only other thing the
derivation gives it. paradiso 14:49 (*«onde la visïon crescer convene»*) is the same reading with
an `xcomp`, so widening the gate is the obvious next step, and it measures −3/+0 — the exact
profile every kept rule in nine batches has had. Reading the three positions kills it: purgatorio
20:151 and 25:49 are **control** verbs whose inherited subject is correct, so two of the three are
true reports being suppressed. This is the scope boundary the Paradiso 1–5 batch censused and
refused: a `ccomp` gate is structural (a subjectless verb with a `che`-clause *has* that clause as
its subject), an `xcomp` gate is lexical wearing a structural costume. **The acceptance test the
series runs — net negative, nothing newly flagged — is necessary and not sufficient.**

**2. What takes the same family is a question about the tree, not the verb.** Rule DU asks whether
the conjunct is *subordinate*: `onde`, `che`, `perché`, `se` written as a `mark` on a `conj` means
Layer 4 recorded a subordinate clause with a coordination deprel, and UD's shared-subject
convention is about coordination only. It takes paradiso 14:49, inferno 20:57, paradiso 3:76,
27:94 and four of the five paradiso 16:55 positions. Its one new position (purgatorio 21:80) is
the familiar trade: the derivation is now right (∅, the 2sg addressee), and the LLM's second,
wrong subject citation stops being absorbed by rule CU.

**3. "Which check runs first" landed twice more.** Rule BW's docstring names paradiso 19:74 as one
of its three evidence lines and that position was still flagged, because the **membership** check
runs before `_classify_divergence`; rule DS gives the membership check rule BW with rule BW's own
gates. Rule DT is the same question about a normalization: `_coordination_head` walks `conj`,
`appos` and `flat`, and Layer 4 wrote *«un Lapo Salterello»* with `compound`. Census 2 — below the
bar this series has dropped candidates at — kept on rule BZ's ground, because it is rule BE's
reasoning verbatim and leaving it out makes the collapse depend on which of two interchangeable
deprels Layer 4 picked.

**4. The sixth round's queued clause is written.** `_CONV_ADJUNCT` (the prepositional adjunct of
time, place, source or manner) and `_CONV_DATIVE` (the non-core dative clitic, this batch's own
prompt finding, 3 positions), both on the generic `missing_arg` class and separable in a round's
subclass table because the dative surfaces as `missing_arg obl:a`. `missing_arg obl*` is **56 of
245** after this batch, bare `obl` 17.

**Two candidates were censused and dropped**, plus rule DQ's widening above: a Binding-Principle-B
block on the `conj` propagation (census 46, of which 3 agree with the candidate subject and 2 of
those 3 are *«he embraced him»* — agreement is not coreference), and the relative pronoun Layer 4
writes as a `case` on the nominal it relativizes (census 7, of which 1 is a relative pronoun).

### 25. Rules DX-EA and the Paradiso 21-25 Read (2026-08-17)

Per-position read of all **21** soft violations in Paradiso 21-25, following *How to Read a Batch* ([`PLAN.md`](PLAN.md))
below. **245 → 234 (−11, −4.5%)**, zero model calls, 0 hard; Paradiso 21-25 itself **21 → 11**
(21: 8 → 6, 22: 2 → 2, 23: 5 → 2, 24: 4 → 0, 25: 2 → 1). `pytest` **483 passed**.

Four deterministic rules, each censused corpus-wide before it was written, measured on its own by
full-corpus violation **diff**, and pinned by a mutation-checked test.

| rule | shape | census | moved |
|---|---|---:|---:|
| **DZ** (`_conjunct_named_by_phrase_head`) | rule AI's NP-head equivalence read **through** rule C's coordination collapse | 85 | **−2** |
| **DY** (`_relative_adverb_oblique`) | rule DD's POS gate read as the reason it states: `onde` is a relative locative whatever of its four tags Layer 2 gave the row | 32 | **−2** |
| **DX** (`_predicative_advmod`) | rule R's **noun** leg: the depictive nominal Layer 4 hangs `advmod` on the predicate, which rule CP already reads off a bare `obl` | 52 | **−1** |
| **EA** (`speech_act_nominal`) | the elided speech verb Layer 4 records as a `parataxis` on a bare pronoun, whose whole derived tuple is a lone ∅ subject | 4 | **−1** |

Plus **10 Layer-4 rows**, **1 Layer-2 row** and **1 Layer-3 span**
(see [`../dep/CORRECTIONS.md`](../dep/CORRECTIONS.md),
[`../morph/CORRECTIONS.md`](../morph/CORRECTIONS.md), [`../np/CORRECTIONS.md`](../np/CORRECTIONS.md)),
worth **−6/+1** between them.

#### The batch's findings

**1. Price a blocked candidate against the corpus's other instances of the same construction.**
The 11-20 batch found that a candidate can measure −3/+0 and still be wrong, and that reading the
positions it removes is what shows it. This batch has the cheaper version of the same test.
Paradiso 21:5 (*«tu ti faresti **quale** / fu Semelè»*) is rule CX's shape — the derivation cites
the comparative clause by its verb, the LLM cites the `quale` that opens it — and the only thing
blocking rule CX is its role gate, because the derivation calls the clause an `obl` and the LLM
calls the word an `attr`. Widening `_COMPLEMENT_ROLES` to `obl` takes it. What kills it is
paradiso **23:14**, *«fecimi **qual** è quei che disïando altro vorria»*: the identical
construction, written by Layer 4 the identical way, and **already accepted** — by rule DJ, because
there the LLM also said `obl`. So the `obl` is a convention Layer 4 applies consistently, and 21:5
is the LLM claiming a complement where the tree asserts an adjunct, which is a second claim about
the role and exactly what rule CX's gate is for. *Before widening a role gate, find the corpus's
other instances of the construction and ask which side they land on.*

**2. Two normalizations, and the shape that needs both.** Rules CD, CI and DT each asked which
normalization has already run on a citation a gate compares. Rule DZ is the first that needs the
**composition** of two. Paradiso 21:130 puts three free relatives in one object slot; rule C
collapses the derivation's three citations onto the coordination head, and rule AI would pair each
`chi` with its own clause's verb except that rule AI is a same-line test and the collapse has
already moved the target off the line. The first of the three was accepted and the other two were
not, for no reason either rule states. Reading the *accepted* position is what found it.

**3. A POS gate is only as good as the tag's consistency.** Rule DY is rule DM's finding
(a rule's docstring can be more correct than its code) with a measurement attached: `onde` carries
four different Layer-2 tags across the corpus — 111 conjunction, 79 pronoun, 49 adverb, 17
relative pronoun — under one and the same `obl` deprel. Rule DD's gate says "adverb" and means
"not a preposition"; where the tag itself is a lottery, rule DT's reasoning applies and the gate
has to name the word.

**4. No new prompt candidate, for the fourth Paradiso batch of five.** The three positions this
batch assigned to the prompt are all instances of clauses already written: 23:7 and 23:10 for
`_CONV_ADJUNCT`, 25:61 for `_CONV_DATIVE` (its second, after the three in 11-20). `missing_arg
obl*` stands at **56 of 234** (bare `obl` 17) — unchanged in absolute terms, because this batch
removed none of it. (23:10 was **wrong**: the next batch's rule EB takes it as checker silence.
See §26.)

**One correction deliberately raised the count by +1.** Paradiso 21:28 (*«di color d'oro **in
che** raggio traluce»*): with `che` retagged from a determiner of `raggio` to the relative pronoun
`in` governs, the position goes 2 → 3, because the LLM's own misreading is now fully reported
instead of half-matching a wrong tree. The trade rule AM recorded, for the fourth batch running.

**Two candidates were censused and dropped**: rule CX's role gate above, and the general form of
rule EA — a derived tuple that is a lone ∅ subject, **720** corpus-wide and 133 of them on
non-verbs, which is precisely the population rule CS measured at +180.

### 26. Rules EB-EF and the Paradiso 26-33 Read (2026-08-17)

Per-position read of all **32** soft violations in Paradiso 26-33 — the **last two batches of the
read series**, taken in one session — following *How to Read a Batch* ([`PLAN.md`](PLAN.md)). **234 → 213 (−21,
−9.0%)**, zero model calls, 0 hard; Paradiso 26-33 itself **32 → 14** (26: 4 → 3, 27: 1 → 1,
28: 6 → 4, 29: 7 → 2, 30: 5 → 1, 31: 2 → 1, 32: 3 → 1, 33: 4 → 1). `pytest` **494 passed**.

**With this batch the read series covers all 100 cantos.** Per canticle the residue now stands at
inferno 54, purgatorio 85, paradiso 74.

Five rules, each censused corpus-wide before it was written, measured on its own by full-corpus
violation **diff**, and pinned by a mutation-checked test.

| rule | shape | census | moved |
|---|---|---:|---:|
| **EB** (`_comparative_come_adjunct`) | rule AR's marker gate names the **word** `come`, not the deprel it was written with or the tag Layer 2 gave it | 812 rows / 8 deprels / 4 tags | **−3** |
| **EF** (`derive_unit`) | the `conj` shared-subject propagation stops at a **sibling** conjunct that has already supplied one | 23 / 3658 | **−3/+1** |
| **EE** (`_prep_stack_nominal`) | rule BV's opening-word leg: the `case` row a multiword preposition's `fixed` members hang on is one of the preposition's own words | 167 | **−2** |
| **EC** (`_comparative_come_adjunct`) | rule AR's no-correlative branch, opened by rule BA's two derived subjects: the marker is the gap boundary rule CW's positional test cannot see | 13 / 598 | **−1** |
| **ED** (`_comparison_clause_hosts`) | rule AR's `extra_arg` leg from the matrix side: the comparison Layer 4 headed on `come` itself | 14 | **−1** |

Plus **16 Layer-4 rows**, **6 Layer-2 rows**, **4 Layer-3 spans** and **2 case-annex rows**
(see [`../dep/CORRECTIONS.md`](../dep/CORRECTIONS.md),
[`../morph/CORRECTIONS.md`](../morph/CORRECTIONS.md), [`../np/CORRECTIONS.md`](../np/CORRECTIONS.md),
[`../case/CORRECTIONS.md`](../case/CORRECTIONS.md)), worth **−14/+2** between them.

#### The batch's findings

**1. A gate names a column; check what the column holds.** Rule DY (the 21-25 batch) found rule
DD's "adverb" gate was really a claim about the word `onde`, which carries four Layer-2 tags under
one deprel. Rule EB is the same finding with the *edge* column added and the series' largest tag
census attached: `come`/`com` is written **812** times under **eight** deprels — 543 `mark`, 145
`case`, 103 `advmod`, 10 `advcl`, 4 `ccomp`, 4 `obj`, 2 `obl`, 1 `cc` — and four Layer-2 tags, and
rule AR admitted exactly one cell of that table (`mark` + conjunction, 441 rows). Nothing in the
reading turns on either column: "**come** sole in viso che più trema, **così** … scema" (paradiso
30:25) is rule AR's own correlative shape written `advmod` + adverb. Dropping both columns takes 3
positions and flags none.

**2. A prompt verdict can be wrong, and it is the expensive kind of wrong.** One of rule EB's three
positions is paradiso **23:10**, which the Paradiso 21-25 batch wrote up as an instance of
`_CONV_ADJUNCT` — prompt work, queued for the sixth round. It is checker silence, and rule EB takes
it for nothing. Of the five verdicts *How to Read a Batch* ([`PLAN.md`](PLAN.md)) offers, **prompt defect is the only one
that leaves no rule behind to be measured**: an acceptance, a derivation fix and an upstream retag
all get a violation diff on the spot, while a prompt diagnosis is unfalsifiable until a round runs.
So the standing form of the rule is: **before assigning a position to the prompt, ask whether any
existing rule's gate is one column away from taking it.**

**3. A refusal beats a re-assignment — rule DA's boundary from a new side.** Rule EF's evidence is
paradiso 29:31-35, five conjuncts of `Concreato` where the fourth brings its own subject and the
fifth was still being handed the first one's. `derive_unit`'s walk goes straight up the `conj` edge
and never looks at what the coordination has done in between: rule AT decides *who* may inherit,
rule DU where a subordinator cuts the chain, and this is the third question about the same walk —
whether the chain head is still the **nearest** antecedent. Handing the conjunct the nearer
sibling's subject instead measured **+8/−2** and was rejected; simply *stopping* measured −3/+1,
because the slot then falls to step 4's pro-drop ∅ and the authority model decides it. That is rule
DA's boundary read from the other side — *an empty subject slot is a decision procedure having
declined*, and declining is a decision.

**4. Two candidates censused and dropped, both on precedent rather than on the count.** The
participial adjunct's subject named by the Layer-3 span containing it (paradiso 28:20) censuses at
8 and is refused on the Inferno 31-34 batch's rule-BR precedent: **its only evidence is a Layer-3
span, and Layer 3 is over-inclusive by design.** The causative causee's `obj` against Layer 4's
`iobj` (paradiso 33:96) censuses at 16 and is refused on the grammar: Italian codes the causee of a
*transitive* infinitive as a dative, so the LLM's `obj` is a second claim about the role — the
DX-EA batch's finding applied to a construction the corpus already has a rule for from the other
side (rule BI).

**Two corrections deliberately raised the count by +2.** Paradiso 28:106 (*«e **dei saper** che
tutti hanno diletto»*): with `dei` retagged from the contraction `di+i` to `dovere` 2sg and `saper`
from a noun to its infinitive, the LLM's having proposed neither predicate is reported as two
`missing_tuple`s instead of being absorbed by a wrong tree. The trade rule AM recorded, for the
fifth batch running.

### 27. Sixth User-Run `--fix` Round (2026-08-18)

The round the whole read series was written to enable: the checker is finished, all 100 cantos have
been read, nothing was written against the base the round would move, and **two prompt clauses were
on the scale with nothing else on it** — so the per-class numbers measure the prompt alone, which no
previous round could.

- **213 → 174 soft, −39 (−18.3%)**, 26 files touched (59 insertions / 31 deletions), 0 hard,
  `pytest` 494 passed, no CRLF. All four other layers stay 0 — the round touched `skel/*.tsv` only.
- Unit-level: **168 → 141 flagged**; 27 cleared outright, 5 improved, 136 unchanged,
  **0 regressed, 0 newly flagged**.
- Per-unit yield **0.232**, against 0.66 / 0.193 / 0.188 / 0.246 / 0.201 for rounds 1–5.
- Exactly **one** position is present after but not before — paradiso 1:81 `extra_arg obj` — inside
  a unit that net improved. It is not an ordinary miss; see finding 3.
- Per canticle: inferno 54 → 49, purgatorio 85 → 67, paradiso 74 → 58.
- **Subclass results** (before → after):

  | subclass | before | after | delta |
  | --- | ---: | ---: | ---: |
  | `missing_arg` | 54 | 42 | −12 (−22.2%) |
  | `extra_arg_subject` | 37 | 24 | −13 (−35.1%) |
  | `extra_arg` | 33 | 32 | −1 (−3.0%) |
  | `role_mismatch` | 31 | 28 | −3 (−9.7%) |
  | `missing_arg_subject` | 24 | 19 | −5 (−20.8%) |
  | `missing_tuple_nominal` | 9 | 9 | ±0 |
  | `missing_arg_adverb` | 9 | 8 | −1 (−11.1%) |
  | `extra_tuple` | 5 | 4 | −1 (−20.0%) |
  | `missing_tuple` | 4 | 2 | −2 (−50.0%) |
  | `extra_arg_adjective` | 4 | 3 | −1 (−25.0%) |
  | `membership` | 2 | 2 | ±0 |
  | `extra_tuple_adverb` | 1 | 1 | ±0 |

**1. `_CONV_ADJUNCT` is positive, and the class table hid it.** The clause names the *prepositional*
adjunct of time, place, source or manner, and `missing_arg obl*` — the aggregate it was queued
against — fell only 24.0%, a little over the round average. Decomposed by the role's own case
marker, the result is the second-largest class effect on record after `_CONV_ADVERB`'s −66.3%:

  | target | before | after | delta |
  | --- | ---: | ---: | ---: |
  | `obl:{in,da,di,con,tra,per}` — the clause's actual target | 19 | 9 | **−52.6%** |
  | `obl` — bare, no case marker | 15 | 14 | −6.7% |
  | `obl:a` — `_CONV_DATIVE`'s target | 12 | 11 | −8.3% |
  | `obl:{come,onde,quale}` — a marker, not a preposition | 4 | 4 | ±0 |
  | `missing_arg obl*` total | 50 | 38 | −24.0% |

The two halves that did not move are the two the clause never addressed. The bare `obl` is not a
prepositional phrase at all: rules AZ/CP settled it as the predicate's **secondary predicate**
(a depictive nominal or adjective Layer 4 hangs caseless). And `obl:come`/`onde`/`quale` are
comparison and relative *markers* the corpus writes in case position (rules AR, DD/DY). So the
subclass table's `missing_arg obl*` was never one population, and **a clause must be measured
against the shape its own prose names**, not against the aggregate the residue is bucketed by.

**2. `_CONV_DATIVE` is negative.** `missing_arg obl:a` 12 → 11 (−8.3%), under half the round
average. The non-core dative clitic was this batch-series' own prompt finding and it moved nothing
— the fourth negative prompt verdict in a row (round 4's two subject branches and
`missing_tuple_nominal`'s rewritten question, now this), against `_CONV_ADVERB` and `_CONV_ADJUNCT`
as the only two positives. What separates the positives from the negatives is now visible: both
positives **withdrew or narrowed a licence the prompt itself had granted** (`_CONV_ADVERB` deleted
"or it is left out"; `_CONV_ADJUNCT` named a slot the conventions had left unnamed), while every
negative *added prose about a shape the model already reads wrong*. Phase 5w's law, sharpened:
**prose that competes with the model's reading does not move a class; removing an instruction that
licensed the omission does.**

**3. The residue is now a hard core, and this was measured, not assumed.** The pre-round-5 artifact
was re-checked with today's checker to put all three snapshots on one gate:

| artifact | soft under HEAD checker | new positions vs previous |
|---|---:|---:|
| before round 5 (894b050) | 265 | — |
| before round 6 (base 213) | 213 | **0** |
| after round 6 | 174 | **1** (paradiso 1:81) |

**173 of the standing 174 were already there before round 5.** Two consecutive rounds have been
pure subtraction from one fixed set, at a flat −19.6% then −18.3%. That is re-sampling, not
progress on new material: a round still pays ~18%, but every position it takes is one it had
already failed twice, and it introduces nothing to read. Extrapolated, three or four more rounds
reach ~90 without a single new diagnosis. **The recovery is real and can be collected at any time;
what a further round cannot buy is information.**

**4. The one new position is a class of LLM error the checker cannot see** — the round's most
valuable output, and the reason it was worth reading a single position. At paradiso 1:81 (*«lago non
fece alcun tanto disteso»*) the round wrote `81.3 fece: obj=(81,4)` beside the `subj=(81,4)` already
there: **one token filling two roles of one predicate**, which rule AL exists precisely to license
as the *exception* (the fused clitic `gliel'` = `gli` + `lo`). Censused over all 100 cantos: **56
positions, 7 of them the fused-clitic shape rule AL licenses, 49 unlicensed** (27 of those
`subj`+`obj`), and **52 of the 56 sit on a line with no soft violation at all**. The checker reports
only divergence from `derive_unit`, so when one of the two roles matches the derivation the other is
unconstrained. Twenty-one read batches could not find this because a read compares the artifact with
the derivation, and this is a contradiction **inside the artifact**. See *After the Sixth Round*
below for what it is owed.

**Not recorded in [`CORRECTIONS.md`](CORRECTIONS.md)**, for the reason §12 gives.

### 28. Rule EG and the Sixth Round's Prompt Repairs (2026-08-18)

The sixth round's own findings, landed the same day. One checker rule that **raises** the count by
50, and two prompt repairs its measurements pointed at. `pytest` **511 passed** (17 new), 0 hard,
all other layers 0/0, `skel/*.tsv` untouched. Full grammar specification in [`RULES.md`](RULES.md).

| change | shape | census | net |
|---|---|---:|---:|
| **EG** (`_dual_role_violations`) | one token filling **two roles of one predicate**, other than rule AL's fused clitic | 56 / 7 licensed | **+50** |
| splice guard (`_apply_missing_arg`) | the class that appends a missing argument may not append a contradiction | — | prevents new ones |
| `arg_slot` (`_split_slot_conflicts`) | a `missing_arg` and an `extra_arg` on the *same* role are **one** question | 8 predicates / 16 positions | 0 until a round |
| `_CONV_DATIVE` | rewritten: the old wording told the model to write a role its class cannot set | `obl:a` 11 | 0 until a round |

**1. The first check that reads the artifact against itself.** Rules V through EF all compare the
reading with `derive_unit`, and that comparison cannot see a contradiction *inside* the reading:
when one token carries two roles of one predicate and one of those rows matches the derivation, the
other is constrained by nothing. 52 of the 56 positions are on lines `--check` says nothing about,
which is exactly why 21 read batches walked past them — **a read only ever sees a position the
checker has named.** The generalization worth carrying: *ask what an artifact asserts that no
comparison tests.* The count going **up** is the point of the rule, not a cost of it (rule AM's
trade), and it stays *soft* because `--fix` refuses any candidate carrying a hard violation, which
would leave the 49 unrepairable by the instrument meant to repair them.

**2. A rule and a splice guard are two halves of one finding.** The evidence line for rule EG was
written *by a round*: `_apply_missing_arg` appends a row and never looks at the rows already there,
so the class that adds a missing argument produced the contradiction (paradiso 1:81), and the
per-unit gate absorbed it because the same call had cleared two other positions. A check that only
reports would let the next round write more. Both halves license rule AL's fused clitic by calling
**that rule's own gate**, not by copying its condition.

**3. Two questions about one slot are a construction defect, not a model failure.** The 8 same-slot
pairs had survived three rounds, and the reason is mechanical: the `extra_arg` question offers
`keep`, the `missing_arg` question invites the token the reading already wrote, and neither answer
alone can clear the pair — so *no* single-class splice could ever be an improvement. The merge is
the fix, and it stays inside the independence rule because the half it quotes is the reading's own
filler. **Before blaming a frozen class on the model, ask whether any answer to the question asked
could have moved it.**

**4. `_CONV_DATIVE` could not be obeyed.** It said *"Cite it as `iobj`"*, hangs on a class whose
question names the slot and whose applier splices the role from the violation, and the slot at every
one of its positions is `obl:a`. Six rounds of prompt verdicts now say the same thing from four
angles: **the only changes that ever moved a class withdrew or narrowed a licence the prompt itself
granted** (`_CONV_ADVERB_ARG` −66.3%, `_CONV_ADJUNCT` −52.6%); prose added about a shape the model
reads wrong measures at the round average, and prose the class cannot act on measures below it.

### 29. Field Notes — the model's own report, into `--log` (2026-08-18)

**Discovery has cost eighteen full passes over the corpus, and every one of them read positions the
checker had already named.** Rule EG measured the ceiling of that: 52 of its 56 positions sit on
lines `--check` is silent about, so 21 read batches walked past them. The read series is closed and
the residue is reading disagreement — which leaves no instrument that can point at a position
*nobody has thought to look at*.

The change is one conditional slot added to every prompt in `skel.py`, and a line format in the log.
Asked *which token is this predicate's `subj`*, a model with no way to say "none of them, and here
is why" names one; the answer and an honest failure are then indistinguishable downstream, because
both look like a violation that did not move. So each prompt now asks for a note — **in addition to**
the answer, never instead of it — when the sentence offers nothing of the shape asked for, when two
answers are equally defensible, or when the convention given does not fit. `_ASK_HEADER`'s classes
number their notes to the question (`N1: …`); the table classes and `SYSTEM_PROMPT` cite a token
(`N<line>.<token>: …`), because they number no questions.

`pytest` **518 passed** (7 new), 0 hard, 224 soft, `skel/*.tsv` untouched.

**1. It is inert, and that is a requirement, not a nicety.** `_split_field_notes` strips the notes
before the response reaches `prompt.apply` or `skel.resolve_chunk`, so splices, `_is_improvement`
and every per-class number are bit-for-bit what they were. `test_a_field_note_changes_nothing_
about_the_splice` pins it by running one canto twice, with and without a note on the same answer,
and comparing the stats Counters. A seventh round therefore stays comparable with the six before it
even though every prompt changed.

**2. It is not an escape hatch.** The prompts state that the model answers every question anyway and
that a note changes nothing — the two properties that stop it buying its way out of the work, which
is what an optional *"report if you cannot"* invites. A note costs the model nothing to write, so
its *rate* carries no information; only the population does.

**3. A note is a hypothesis about the question, never evidence about the corpus.** It earns exactly
one thing: a position to hand to `read.py`, chosen by something other than reading 100 cantos to
find it. The verdict procedure in *How to Read a Batch* ([`PLAN.md`](PLAN.md)) is unchanged and still applies to every
position a note names — and the five verdicts are what the notes should be censused against, since
a note that repeats across dozens of positions is a prompt defect and a note that appears once is
noise.

**4. Collection is opt-in and per process.** `make -C skel fix` still does not pass `--log`, and
that standing decision is untouched (see §6): pass `--log skel-<canticle>.log`
explicitly, **one file per process**, because a round is run three ways in parallel and `fix`
truncates its log at start.

**How to read the notes after a round.** This has not been done yet — the instrument landed with no
round behind it, so the first pass is as much a test of the notes as of the corpus.

1. **Count before reading.** `grep '^NOTE' skel-*.log | cut -f4 | sort | uniq -c` (by class),
   `cut -f5 | sort | uniq -c` (by position — a position noted by several classes is the strongest
   signal there is). The *rate* means nothing: a note costs the model nothing to write, so it is
   governed by the prompt's wording, not by the corpus. Only the population is evidence.
2. **Group by what the note claims,** not by its wording — the same complaint arrives in many
   phrasings. A group of dozens is a candidate prompt or checker defect; a singleton is noise and is
   dropped without reading it.
3. **Read the group's positions with `read.py` and give each the usual five verdicts** (*How to Read
   a Batch*, step 3). Nothing about a note shortens this step: it chose the position, and it has no
   standing on what is wrong there. In particular a note claiming the convention does not fit is
   **not** a prompt verdict — that verdict is the one to reach for last, and the note is written by
   the same reading the verdict is about.
4. **From there the batch procedure is unchanged**: census the shape corpus-wide, measure the rule
   on its own by violation diff, pin it with a mutation-checked test, write it up.
5. **Judge the instrument too.** If the note groups name only positions the checker already flags,
   it has bought nothing over `--check` and should be said so plainly here. Its whole claim is
   reaching positions `--check` is silent about — the 52-of-56 gap rule EG exposed.

**Judged, after the seventh round (§30 finding 4): it did not pay.** 5 notes over 332 calls — too
few to group, let alone census. One is a real finding (paradiso 14:93, a Layer-2 mistag no check
looks for), two are wrong in a way that contradicts the noting model's own rows, one is a rewording
of the answer it accompanies. The reason is in §30: the answer vocabulary already carried a
recorded refusal (`keep`/`none`/`drop`/`both`), and the prompts told the model a note changes
nothing, so there was never a reason to use the second channel. **The instrument is kept — it costs
nothing and it did find one thing — but it is not the route to positions `--check` is silent about,
and no further prompt work should be spent widening it.**

---

### 30. Seventh User-Run `--fix` Round (2026-08-18)

- **224 → 161 soft, −63 (−28.1%)**, 0 hard, `pytest` 521. `skel/*.tsv` only, so no other layer
  moved.
- Unit-level: **182 → 131 flagged**; 51 cleared outright, 9 improved, 122 unchanged,
  **0 regressed, 0 newly flagged** — the seventh round running.
- Per-unit yield **0.346**, the highest of the seven rounds (0.66, 0.193, 0.188, 0.246, 0.201,
  0.232, **0.346**).
- Per canticle: inferno 60 → 44, purgatorio 84 → 59, paradiso 80 → 58.
- **The first round run with `--log`** (§29), so it is also the first with per-class *call* counts.
- **Class results** (before → after):

  | class | before | after | delta |
  | --- | ---: | ---: | ---: |
  | `dual_role` | 50 | 9 | **−41 (−82.0%)** |
  | `missing_arg` | 69 | 59 | −10 (−14.5%) |
  | `extra_arg` | 59 | 53 | −6 (−10.2%) |
  | `role_mismatch` | 28 | 24 | −4 (−14.3%) |
  | `extra_tuple` | 5 | 3 | −2 (−40.0%) |
  | `missing_tuple` | 11 | 11 | ±0 |
  | `membership` | 2 | 2 | ±0 |

- **Calls and yield per class** (3 canticles summed by hand from the three `--log` summaries):

  | class | calls | removed | per call |
  | --- | ---: | ---: | ---: |
  | `dual_role` | 48 | 40 | **0.833** |
  | `extra_arg` | 28 | 5 | 0.179 |
  | `missing_arg_subject` | 12 | 2 | 0.167 |
  | `missing_arg` | 39 | 6 | 0.154 |
  | `missing_arg_adverb` | 8 | 1 | 0.125 |
  | `role_mismatch` | 25 | 2 | 0.080 |
  | `extra_arg_subject` | 18 | 1 | 0.056 |
  | `_whole` | 128 | 6 | 0.047 |
  | `arg_slot` | 7 | 0 | **0.000** |
  | `missing_tuple_nominal` | 9 | 0 | 0.000 |
  | `extra_tuple` / `extra_tuple_adverb` / `extra_arg_adjective` / `missing_tuple` | 10 | 0 | 0.000 |
  | **TOTAL** | **332** | **63** | **0.190** |

**The records are one class being harvested for the first time, not the prompt improving.** −28.1%
is the largest percentage since round 1 and 0.346 the highest yield ever measured, and `dual_role`
carries **40 of the 63 (63%)**. On the divergence residue alone the round is **174 → 152 (−22,
−12.6%)** — weaker than rounds 4, 5 and 6 (−16.8%, −15.1%, −18.3%). Read the round as two results:
a new class cleared at 82%, and the standing residue moved less than the last three rounds moved it.

**1. The only question the model answers well is the one answerable from the artifact alone.**
`dual_role` runs at **0.833 per call**; everything else runs at **0.081** (284 calls, 23 removed) —
a **10× gap**, and the largest per-class separation the project has measured. The difference is not
difficulty, it is *what the question needs*: `dual_role` shows the model both of its own rows and
asks which is right, and every other class asks it to adjudicate against a reading it cannot see —
`derive_unit`'s, which the Independence Rule deliberately withholds. Rule EG was written up in §28
as a checker gain (+50 by design); its larger result is that **it is the first question in this
project whose evidence is entirely inside the artifact**, and it is the only one that pays.

**2. `arg_slot` is decided, and the verdict is checker-side.** 7 calls, **0 removed**, and all 8
answers in the log are `keep`. §28's finding 3 was that no single-class answer could have cleared
these 16 positions, and merging the pair into one question was the right repair *of the question* —
but the answer is still outside the artifact, so the merge changed nothing. What the log adds is
**why**: the model is not failing to answer, it is **refusing** — it asserts that both rows are
right and the checker's complaint is unfounded. That converts the 8 predicates from a prompt
population into a **checker-side reading list**.

**3. The driver has been discarding the model's verdicts, and this round measured how many.**
**101 of 332 calls (30%) ended in `no actionable answer`** — a label that reads like a parse
failure and is doing two different jobs. The answers under it:

  | answer | count | where |
  | --- | ---: | --- |
  | `keep` | 39 | `extra_arg` 16, `extra_arg_subject` 15, `arg_slot` 8 |
  | `none` | 14 | `missing_arg` 10, `missing_arg_adverb` 3, `role_mismatch` 1 |
  | `drop` | 3 | |
  | `both` | 1 | `dual_role` |
  | a role or token already in the artifact | 48 | `missing_arg` 22, `role_mismatch` 17, … |

`keep` is a **first-class answer** in `_ask_extra_arg`'s own vocabulary, meaning *the token really is
that predicate's argument in that role* — that is, the checker is wrong. When every answer in a
call is `keep`, `apply` returns False and the driver files the whole response under "no actionable
answer" and moves on. **The signal the field-note instrument was built to create already existed,
in the answer slot, and was being thrown away.** Splitting the label — a refusal is not a parse
failure — and counting refusals per class in the summary table is the cheapest instrument this
project has been offered: no extra call, no prompt change, and the census is the reading list.

**4. The field-note instrument did not pay.** 5 notes over 332 calls (inferno 1, purgatorio 0,
paradiso 4). One is real: paradiso 14:93, where Layer 2 tags `esso` as `essere` (verb, infinitive,
apocope) while Layer 3 heads a noun phrase `[esso litare]` on it — `esso` is the demonstrative and
`esso litare` a nominalized infinitive, so the Layer-2 row is wrong, and **no check compares Layer 2
with Layer 3 that way**. The other three are a rewording of the answer they accompany, and two
outright errors, both of which contradict rows the same response wrote (inferno 10:93 calls a token
"not a predicate" and gives it a tuple; paradiso 21:55 calls `nascosta` missing from the token list
and cites it). See the verdict added to §29 above.

**5. `_CONV_DATIVE`, rewritten, is positive.** `missing_arg obl:a` **11 → 6 (−45.5%)**, against a
divergence-wide −12.6%. §28's finding 4 was that its old text told the model to "cite it as `iobj`",
which the class it hangs on cannot do; making the instruction executable moved the class. That is a
**third shape of positive prompt change**, next to the two the six earlier rounds found (withdraw a
licence, narrow a licence): **make an instruction the class can actually carry out.** All four
negatives remain what they were — added prose about a shape the model reads wrong.

**6. `_whole` is a loss and the next round should not run it.** **128 calls (38.6% of the round's
budget), 6 violations removed, 0.047 per call** — and a whole-unit regeneration is the most
expensive call in the driver. Inferno's `_whole` was 32 calls for **0**. The eighth round is to be
run with `--no-whole`; the flag exists and no file changes for it.

**7. One `dual_role` refusal is a checker gap, and it is the round's concrete rule candidate.**
purgatorio 2:40, `sen` = `si`+`ne`, Layer 2 `pronoun+pronoun`, annex `reflexive+ablative`, written
as both `obl:si` and `obl:ne` of `venne`. The model answered `both`, **and it is right** — this is
rule AL/CM's licensed fused clitic. `_fused_clitic_dual_role` refuses it because
`_case_supports_role` maps the `reflexive` slot onto `obj`/`iobj`/`obl:a` only, and never onto the
`obl:<clitic-lemma>` role `derive_unit` mints from the clitic's own `case` child. Census and write
the leg.

**8. The subject slot did not move.** `extra_arg subj` **24 → 24 (±0)**, `missing_arg subj` 19 → 16.
Four rounds have now left it standing and the read series read it; it is 40 of the 152 divergence
positions and it is genuine disagreement over Dante's inversion, not a prompt population.

### 31. The Refusal Split — `no actionable answer` was two outcomes (2026-08-18)

§30 finding 3 measured that **101 of the seventh round's 332 calls produced no splice, and 57 of
them were the model answering with its class's own word for *leave this as it is***: `keep` (39),
`none` (14), `drop` (3, which is a failed change rather than a verdict) and `both` (1). All of them
were written to the log under `no actionable answer` — a label that reads like a parse failure —
and none of them was counted anywhere.

`_is_refusal` splits the two. A **refusal** is a response that answered and whose *every* answer
asserts the artifact as written; anything else is **unusable**. The driver counts them separately
(`refused:<class>` / `unusable:<class>`), the log says which (`refused: the reading stands` versus
`no usable answer`), and `_fix_summary_lines` prints a **`refused` column** beside
`calls / removed / per call`. `pytest` **534** (11 new, mutation-checked at the predicate, the
`_ask_class` call site and the summary).

**1. The vocabulary is per class, and it is the prompts' own.** `_STAND_PAT` maps `extra_arg`,
`extra_arg_subject`, `extra_arg_adjective` and `arg_slot` to `keep`; `missing_arg`,
`missing_arg_adverb` and `missing_arg_subject` to `none`; `dual_role` to `both`; the three
`extra_tuple` classes to `yes`. `role_mismatch` has no such word — standing pat there is answering
the role the artifact already carries, so it is compared against `given_role`, canonicalized
(a violation reports `iobj` as `obl:a` while the row may hold either).

**2. Strict on purpose.** Every answer given must assert the artifact: a response that stands pat on
one question and tries to change another is not a verdict about the reading. And **a failed change
is not a refusal** — `drop` that the splice could not carry out is a splice failure, and counting it
as the model declining would poison the census the split exists to produce. Question numbers are
consulted only for `role_mismatch`, because `arg_slot` asks one question for a *pair* of violations
and its answer count does not match its violation count.

**3. What it buys, and what it does not.** It adds no call, changes no prompt, and moves no
position — `--check` is identical before and after. What it produces is a **census**: a class that
is all refusals is checker-side work rather than a prompt population, and the round's own log
becomes a position-by-position list of where the model thinks `--check` is wrong. It does **not**
make the model right. A refusal is a hypothesis about the checker with exactly the standing a field
note has about the corpus (§29): it chooses a position, and *How to Read a Batch*'s five verdicts ([`PLAN.md`](PLAN.md))
still decide what is wrong there.

**4. The first reading list is already known**, from round 7 counted by hand: `arg_slot` 8 `keep`
over 7 calls (every call), `extra_arg` 16, `extra_arg_subject` 15, `missing_arg` 10 `none`,
`missing_arg_adverb` 3, `dual_role` 1 `both` — that last one became rule EH the same day, which is
the shape of the whole route: the model refused, the refusal was read, and the checker was wrong.

### Schedule — the series is complete

**All 100 cantos have been read**: Inferno (batches 1, 1–3, 4–6, 7–10, 11–15, 16–20, 21–25, 26–30,
31–34), Purgatorio (1–5, 6–10, 11–15, 16–20, 21–25, 26–30, 31–33) and Paradiso (1–5, 6–10,
11–15 + 16–20 together, 21–25, 26–33). Nothing is re-read: the standing residue is reading error,
and it is the most direct sample there is of what a `--fix` round leaves behind.

| canticle | soft at base 213 | after the sixth round (174) |
|---|---:|---:|
| inferno | 54 | 49 |
| purgatorio | 85 | 67 |
| paradiso | 74 | 58 |

Eighteen batches produced rules at zero model cost — AG: −43; AH–AL: −156; AM–AT: −75; AU–AY: −54;
AZ–BI: −143; BJ–BN: −41; BO–BV: −35; BW–BZ: −25; CA–CJ: −33; CK–CO: −21; CP–CT: −18; CU–CY: −21;
CZ–DD: −30; DE–DF: −7; DG–DJ: −10; DK–DR: −27; DS–DW: −16; DX–EA: −11; EB–EF: −21 — against two
`--fix` rounds run inside the series (−109 and −53). **The sixth round then ran (2026-08-18, §27)**,
the one the series was written to enable: the checker was finished, so its per-class numbers measured
the prompt alone. See *After the Sixth Round* below (§6) for what it settled and what it left.

Per canto, get the current numbers with `uv run skel.py <canticle> --check -c <n>` from `skel/`.


---

## 5. Routes Closed in Phase 6

Populations are quoted at the base they were measured against. These are settled; a Phase-7 batch
that runs into one of them should read this entry rather than re-open the route.

- **Stacked prepositions in Layer 4 — CLOSED 2026-08-14.** 161 multiword-preposition clusters (196
  rows, 74 files) normalized to the UD shape (opening word `case`→ nominal, later members
  `fixed`→ opening word); Layer 5 measured **1094 → 1094, net zero by design**. Rules O/`prep_stack`
  read the normalized shape via a `fixed`-under-`case` lemma aggregation. The route's old "14
  role_mismatch / 18 unattached" count was Phase-5j-era and already absorbed. Standing residue: 3
  genuine obl-vs-obl disagreements (inferno 14:103, purgatorio 32:156, paradiso 32:57). See
  [`../dep/CORRECTIONS.md`](../dep/CORRECTIONS.md) and [`CORRECTIONS.md`](CORRECTIONS.md).
- **The adverb-preposition clusters — CLOSED by rule BJ (2026-08-15).** The 40 clusters the
  prep-stack normalization deliberately excluded as "a Layer-2/4 tension to decide separately if it
  ever matters" **did** matter: censused at 147 and settled at Layer 5 (−21) without a Layer-4
  rewrite.
- **Accusative-and-infinitive — CLOSED by rule BI (2026-08-15).** Censused at 10 and all 10 taken;
  the tree asserts both edges, so neither reading is wrong.
- **Depictive adjectives under bare `obl` — CLOSED by rule AZ (2026-08-15).** Censused at 43, worth
  −13 as a role-mismatch acceptance rather than a derivation change.
- **Attributive vs. predicative adjectives — CLOSED.** `extra_tuple_adjective` went 37 → 13 (rules
  AU/AY/AZ) → **0** (round 4), without the read it had been queued for. The remaining `extra_tuple`
  positions are a different, unbranched population.
- **Adverbs promoted to predicates — CLOSED.** `extra_tuple_adverb` 33 → 2, effectively by the
  Stage-2 micro-prompt alone.
- **`missing_arg obl` sample audit — folded into the read series.** The adverb bucket that dominated
  it was branched and repaired (`_CONV_ADVERB`, then `_CONV_REPEATED` in round 4); the series walked
  the rest in batch order, so it stopped being a route of its own.
- **`dep.subject_agreement`'s residue — CLOSED 2026-08-14, and refined four times since.** All 18
  positions were re-read; the *coordinated subject* exclusion became a per-conjunct **person** test
  (2026-08-16, from the Purgatorio 11–15 read), the 1/2-plural exclusion was narrowed to its number
  half (rule CR) and the number-only exclusions were stopped from preempting the person test (rule
  CV). `dep --check` has stayed **0 hard / 0 soft** throughout. See
  [`../dep/CORRECTIONS.md`](../dep/CORRECTIONS.md).
- **An `iobj` ↔ `obl:a` equivalence — censused and dropped** (inferno 28:76). Both rule AI and rule N
  would have to widen, and the role pair occurs **0** times as a `role_mismatch` corpus-wide.

---

## 6. After the Sixth Round — what it settled (closed; superseded by Phase 7)

**The sequence this section used to set is spent.** It read: *read Paradiso in 5-canto batches, then
run one `--fix` round, none in between.* The reading half closed 2026-08-17 (§26) and the round ran
2026-08-18 (§27). Both prompt candidates are decided — `_CONV_ADJUNCT` positive at −52.6% on the
shape its prose names, `_CONV_DATIVE` negative at −8.3%, and the second of those turned out to be a
wording defect rather than a verdict on the shape (§28 finding 4).

**The residue's shape had changed, and the three things that followed from it** — the first two were
landed the same day (§28, 2026-08-18), the third became a Phase-7 standing fact:

1. **DONE — rule EG, the dual-role check**, plus the `_apply_missing_arg` splice guard that stops a
   round writing another one. Census 56, 7 licensed by rule AL, base 174 → **224**.
2. **DONE — the `arg_slot` merge**, the same-slot pair asked once instead of twice (8 predicates,
   16 positions), and `_CONV_DATIVE` rewritten to name the slot its class actually asks about.
3. **The subject slot, 36% of everything the round left**: `extra_arg_subject` 24 +
   `missing_arg_subject` 19 + the 19 `role_mismatch` rows with `subj` on one side = **62 of 174**,
   and 13 of those mismatches are `subj` ↔ `obj` in both directions on one predicate. Round 4
   decided `_CONV_SUBJECT` negative and converted this to read-work; the read series then read it
   and left it standing. So it is neither prompt-work nor unread — it is the corpus's genuine
   reading disagreement over Dante's inversion. The `arg_slot` merge covers 14 of the 62. **The
   seventh round confirmed it: `extra_arg subj` moved 24 → 24 (±0), `missing_arg subj` 19 → 16.**

**A round is worth running even with an unchanged prompt — but know what it buys.** §21 measured
that: −15.1% at a base fifteen rule batches lower, 0 regressed / 0 newly flagged, which shows the
rules and the LLM take largely disjoint residue. What such a round does *not* buy is an answer to
any question, and it moves the base under every rule measured afterwards. So the recovery is real
and can be collected at any time; the ordering constraint is about *evidence*, not about yield.

**Why `--log` became mandatory in practice (2026-08-18).** After round 4 it was proposed and
declined that `make -C skel fix` pass `--log`, on the grounds that a round is measured by **violation
diff, not by driver telemetry**. The seventh round showed what the violation diff does *not*
reconstruct: Inferno's table read **TOTAL 84 calls / 16 removed / 0.190**, and split by class it was
`dual_role` **10 calls / 11 removed / 1.100** against **74 calls / 5 removed / 0.068** for everything
else, with `_whole` at **32 calls / 0 removed** — 38% of the round's call budget, and the most
expensive call in it, for nothing. **A call count is not recoverable from the artifact, so it has to
be written down while the round runs.** `_print_fix_summary`'s per-class table is therefore appended
to `--log` under `=== fix summary ===`; the `make` target still does not pass the flag.
