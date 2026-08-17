## Handoff (2026-08-17) — resume here

> **The Paradiso read series is five batches in.** All of Inferno, all of Purgatorio and now
> **Paradiso 1–25** have been read per-position: rules DX–EA took **245 → 234 (−11, −4.5%)** with
> zero model calls, 0 hard, `pytest` **483 passed**, plus 10 Layer-4 rows, 1 Layer-2 row and
> 1 Layer-3 span. Per canticle: inferno 55, purgatorio 85, paradiso 94.
>
> **The plan for the rest of the work is unchanged:**
>
> > **Read Paradiso in 5-canto batches — 26–30, then 31–33 — and when the series is finished,
> > run one `--fix` round.** No round in between.
>
> **The next session's task: the per-position read of Paradiso 26–30 — 23 soft violations at base
> 234.** Start a fresh session, list them with `uv run skel.py paradiso --check -c <n>` from
> `skel/`, and read each one with `uv run read.py paradiso <canto> <line>`. Two batches,
> 32 positions, schedule **re-measured at base 234** in [`skel/PLAN.md`](skel/PLAN.md)'s *The Read
> Series*. **Re-measure the batch first**; every landed rule shrinks the batches after it, though
> rules DX–EA moved Paradiso only and left Inferno's 55 and Purgatorio's 85 exactly where they
> were.
>
> **What the Paradiso 21–25 batch found.** Its transferable lesson is a second, cheaper way to
> kill a candidate the acceptance test would pass. Paradiso 21:5 wants rule CX's role gate widened
> to `obl`, and the widening takes the position — but paradiso **23:14** is the *identical*
> construction (*«fecimi qual è quei …»* against *«ti faresti quale fu Semelè»*), Layer 4 wrote it
> the identical way, and it is **already accepted**, because there the LLM said `obl` too. So the
> `obl` is a convention Layer 4 applies consistently, and 21:5 is the LLM claiming a complement
> where the tree asserts an adjunct — the second claim about the role that rule CX's gate exists
> to keep out. **Before widening a role gate, find the corpus's other instances of the
> construction and ask which side they land on.**
>
> Second, **the composition of two normalizations**: rule DZ is the first shape that needs rule
> AI's NP-head equivalence *and* rule C's coordination collapse, and what found it was reading
> the one position of three the checker already accepted — paradiso 21:130's three free relatives
> in one object slot, of which only the same-line one was taken. Third, **a POS gate is only as
> good as the tag's consistency**: `onde` carries four different Layer-2 tags under one and the
> same deprel, so rule DD's "adverb" gate had to name the word instead (rule DY).
>
> **No new prompt candidate came out of this batch** — the fourth of five Paradiso batches for
> which that is true. Its three prompt positions are further instances of `_CONV_ADJUNCT` (23:7,
> 23:10) and `_CONV_DATIVE` (25:61), both already written into `skel/skel.py` and both waiting on
> the sixth round. **Do not run a round while checker rules are being written against the base it
> would move.**
>
> **The per-batch procedure is written down** — eight steps, in [`skel/PLAN.md`](skel/PLAN.md)'s
> *How to Read a Batch*. Follow it rather than improvising: every position gets one of five
> verdicts (checker silent / derivation wrong / upstream wrong / prompt defect / genuine
> disagreement), each of which sends the fix somewhere different; no rule is written before its
> shape is censused corpus-wide; each rule is measured alone by full-corpus violation **diff**
> (not by the total), pinned by a mutation-checked test, and written up in the same session.

**Layer 5 is operating under Phase 6 with 0 hard / 234 soft violations.**
Checks: `dep --check` **0 hard / 0 soft** (the subject-agreement rule's 18-position residue closed
2026-08-14; its *coordinated subject* exclusion refined to a per-conjunct person test 2026-08-16;
its 1/2-plural exclusion narrowed to the number test 2026-08-16 by rule CR and the
number-only exclusions stopped from preempting the person test the same day by rule CV;
16 + 25 + 20 + 10 further rows corrected 2026-08-15, 15 + 2 + 1 + 11 + 17 + 27 more 2026-08-16,
12 more 2026-08-17 by the Purgatorio 26–30 read, 4 more the same day by the Purgatorio 31–33
read, 6 more the same day by the Paradiso 1–5 read, 10 more by the Paradiso 6–10 read, 9 more by the Paradiso 11–20 read, 10 more by the Paradiso 21–25 read),
`case --check` 0 hard (1 stale row dropped, 1 row re-read, 1 more dropped and 2 re-read
2026-08-16, 1 re-read and 1 added 2026-08-17 by the Paradiso 1–5 read, 1 dropped and 1 added the same day
by the Paradiso 6–10 read), `skel --check` 0 hard/**234** soft (inferno 55, purgatorio 85,
paradiso 94),
`np --check` 0/0 (1 span split, 1 widened, 1 added, 1 moved 2026-08-16, 1 clitic span added and
1 span dropped 2026-08-17), `morph --check` 0/0
(3 + 5 + 1 + 2 + 8 + 2 + 1 + 1 + 1 + 2 + 1 + 1 rows corrected), `pytest` **483 passed** (the Purgatorio
26–30 read added 10, the Purgatorio 31–33 read 4 more, the Paradiso 1–5 read 8 more, the Paradiso
6–10 read 16 more, the Paradiso 11–20 read 10 more, the Paradiso 21–25 read 8 more). The fifth `--fix` round (2026-08-17) touched
`skel/*.tsv` only, so no other layer moved.

**Layer 4's stacked prepositions are normalized (2026-08-14).** 161 multiword-preposition
clusters (196 rows, 74 files) rewritten to the UD convention — opening word `case`→ nominal,
later members `fixed`→ opening word — closing the flat/chained shape lottery. Layer 5 measured
**1094 → 1094, net zero** (0 units cleared / newly flagged; one derived lemma flip at
purgatorio 31:26 by design); rules O/`prep_stack` read the normalized shape via a
`fixed`-under-`case` lemma aggregation in `dante_corpus/skel.py`. The old "14 role_mismatch /
18 unattached" note was a Phase-5j-era count already absorbed by those rules. See
[`dep/CORRECTIONS.md`](dep/CORRECTIONS.md) and [`skel/CORRECTIONS.md`](skel/CORRECTIONS.md).

**Layer 4's agreement residue is closed (2026-08-14).** All 18 were re-read: one was a real
mis-attachment (purgatorio 26:147, Occitan `sovenha vos`), ten were taken by six new exclusions in
`dep.subject_agreement` — each measured corpus-wide first, and none of them touching a pair the
rule calls `"agree"`, so Layer 5's Tier-B repairs are untouched — and seven by hand-verified
`AD_SENSUM`/`FOREIGN` flags in the Layer-2 `note` column, the `NO_NP`/`CONT_NEXT` mechanism. Layer
5 rose **1091 → 1094 (+3)**, all three individually attributable (rule AG at inferno 6:87, and the
two obliques the purgatorio 26:147 re-parse gives `sovenha`) — the same honest trade earlier
Layer-4 rounds recorded. See [`dep/CORRECTIONS.md`](dep/CORRECTIONS.md).

### Current State & Architecture Summary

- **Layer 5 (Phase 6)**: `--fix` runs in three stages: Stage 1 (deterministic auto-repairs, −73), Stage 2 (twelve class-specific micro-prompts, keyed by POS, by role, or by class alone), and Stage 3 (fallback whole-unit regeneration). Five user-run rounds so far: **2011 → 1452 (−559)**, **1409 → 1247 (−162)**, **1094 → 963 (−131)**, **650 → 541 (−109)** and **351 → 298 (−53)**.
  - **Detailed Phase 6 Plan**: For Phase 6 operating principles, architectural details, active routes, and measurement procedures, see [`skel/PLAN.md`](skel/PLAN.md).
- **Latest Improvements**:
  - **Rules DX–EA (Paradiso 21–25 read, 2026-08-17)**: Per-position read of all 21 soft violations
    in Paradiso 21–25 produced four deterministic rules — DZ (rule AI's NP-head equivalence read
    *through* rule C's coordination collapse, 85, −2), DY (rule DD's POS gate read as the reason
    its docstring states: the relative locative is `onde` whatever of its four Layer-2 tags the row
    got, 32, −2), DX (rule R's noun leg — the depictive nominal Layer 4 hangs `advmod` on the
    predicate, which rule CP already reads off a bare `obl`, 52, −1), EA (the elided speech verb
    Layer 4 records as a `parataxis` on a bare pronoun, whose whole derived tuple is a lone ∅
    subject, 4, −1) — plus 10 Layer-4 rows, 1 Layer-2 row and 1 Layer-3 span. **245 → 234 (−11,
    −4.5%)** with zero model calls; Paradiso 21–25 itself 21 → 11, `pytest` **483**. Its finding is
    a cheaper form of the 11–20 batch's: **price a blocked candidate against the corpus's other
    instances of the same construction**. Widening rule CX's role gate to `obl` takes paradiso
    21:5 — and paradiso 23:14 is the identical construction, written by Layer 4 the identical way,
    and already accepted because there the LLM said `obl` too, which makes the `obl` a consistent
    convention and 21:5 a second claim about the role. Also: **rule DZ is the first shape that
    needs two normalizations composed**, found by reading the one position of three that the
    checker already accepted; and **a POS gate is only as good as the tag's consistency**. Two
    candidates were censused and dropped (rule CX's widening, and rule EA's general form at 720).
    One Layer-4 correction deliberately raised the count by +1, exposing an LLM misreading the
    wrong tree had matched. See [`skel/CORRECTIONS.md`](skel/CORRECTIONS.md),
    [`dep/CORRECTIONS.md`](dep/CORRECTIONS.md), [`morph/CORRECTIONS.md`](morph/CORRECTIONS.md),
    [`np/CORRECTIONS.md`](np/CORRECTIONS.md).
  - **Rules DS–DW (Paradiso 11–20 read, 2026-08-17)**: Per-position read of all 43 soft violations
    in Paradiso 11–20 — **two** batches of the Paradiso series in one session — produced five
    deterministic rules — DU (the shared-subject propagation across `conj` stops at a conjunct
    Layer 4 marks with its own subordinator, 49, −8/+1), DW (rule BX's `attr` leg: the depictive
    Layer 4 wrote in the complement slot, 100, −2), DS (rule BW applied in the membership check
    that runs before it, 325, −1), DT (`compound` collapses like `flat`, 2, −1), DV (rule CB read
    through rule AU's host: the oblique stranded on an `amod` over one of the predicate's own
    arguments, 119, −1) — plus 9 Layer-4 rows and 1 Layer-2 row. **261 → 245 (−16, −6.1%)** with
    zero model calls; Paradiso 11–20 itself 43 → 30, `pytest` **475**. Its finding: **a rule can
    measure −3/+0 and still be wrong** — rule DQ's gate widened from `ccomp` to `xcomp` scored the
    exact profile every kept rule in nine batches has had, and two of the three positions it
    removed were control verbs whose inherited subject was correct. *Measure by violation diff,
    then read what the diff removed.* Also: **"which check runs first" landed twice more** (rules
    DS, DT), and **the sixth round's queued prompt clause is finally written** — `_CONV_ADJUNCT`
    for the prepositional adjunct of time or place, plus `_CONV_DATIVE`, this batch's own prompt
    finding. Two further candidates were censused and dropped (a Binding-Principle-B block at
    census 46/3, and a relative-pronoun `case` shape at census 7). One Layer-4 correction
    deliberately raised the count by +1, exposing an LLM misreading the wrong tree had matched.
    See [`skel/CORRECTIONS.md`](skel/CORRECTIONS.md), [`dep/CORRECTIONS.md`](dep/CORRECTIONS.md),
    [`morph/CORRECTIONS.md`](morph/CORRECTIONS.md).
  - **Rules DK–DR (Paradiso 6–10 read, 2026-08-17)**: Per-position read of all 18 soft violations
    in Paradiso 6–10, the **second batch of the Paradiso series**, produced **eight**
    deterministic rules — DO (rule AG's agreement test asked of the two *predicates*: two finite
    verbs sharing a subject must agree with each other, 30 / 1151, −5), DQ (the impersonal verb
    whose subject is its own `che`-clause, reached with no valency lexicon, 217, −5), DL (rule
    DB's part-of-speech gate dropped, 414 / 492, −5), DP (the relative clause with *no relativizer
    at all*, 474 / 3261, −3), DK (the antecedent where the derivation names its clause's relative
    pronoun, 2574 / 3261, −2), DR (`quasi`, rule AR's third comparison marker, 9 / 52, −2), DM
    (rule AK's gate read as the negative its docstring states, 33 / 150, −1), DN (the subject
    Layer 4 writes on the `xcomp` infinitive, 106 / 1130, −1) — plus 10 Layer-4 rows, 2 Layer-2
    rows and 2 case-annex rows. **288 → 261 (−27, −9.4%)** with zero model calls; Paradiso 6–10
    itself 18 → 6, `pytest` **465**. Its finding: **a rule's docstring can be more correct than
    its code** — rules DL and DM each drop a part-of-speech condition that the rule's own stated
    reason never asked for. Also: **a scope refusal is about the instrument, not the shape** (rule
    DQ takes the family the Paradiso 1–5 batch dropped at census 29), and **price a derivation
    rule as an acceptance first** (rule DN measured −4/**+40** in `derive_unit`, −1/+0 as an
    acceptance). Two Layer-4 corrections deliberately left the count where it was, exposing LLM
    misreadings the wrong tree had matched. See [`skel/CORRECTIONS.md`](skel/CORRECTIONS.md),
    [`dep/CORRECTIONS.md`](dep/CORRECTIONS.md), [`morph/CORRECTIONS.md`](morph/CORRECTIONS.md),
    [`case/CORRECTIONS.md`](case/CORRECTIONS.md).
  - **Rules DG–DJ (Paradiso 1–5 read, 2026-08-17)**: Per-position read of all 26 soft violations
    in Paradiso 1–5, the **first batch of the Paradiso series**, produced four deterministic
    rules — DJ (rule CX's complement-role gate dropped where the two sides name the *same* role,
    censused at 28, −3), DI (rule AN's acceptance leg: the gapped clause the LLM heads on its own
    `orphan` remnant, 13 / 2, −2), DG (the membership check read through rule C's coordination
    collapse, −1), DH (rule CW's mirror leg — the elided clause is the *first* one, 64 / 2, −1) —
    plus 6 Layer-4 rows, 1 Layer-2 row, 1 Layer-3 span and 2 case-annex rows. **298 → 288 (−10,
    −3.4%)** with zero model calls; Paradiso 1–5 itself 26 → 18, `pytest` **449**. Its finding:
    **a gate written to admit a specific disagreement can exclude the case where the two sides
    agree outright**, which is strictly the weaker claim. One candidate was censused at **29** and
    dropped on the corpus's own scope boundary — separating impersonal verbs from modals in the
    `subj`-versus-`xcomp` class needs a verb-valency lexicon, which *Out of scope* rejects. One
    Layer-4 correction deliberately *raised* the count by +1 (1:81), exposing an LLM misreading
    the wrong tree had matched. See [`skel/CORRECTIONS.md`](skel/CORRECTIONS.md),
    [`dep/CORRECTIONS.md`](dep/CORRECTIONS.md), [`morph/CORRECTIONS.md`](morph/CORRECTIONS.md),
    [`np/CORRECTIONS.md`](np/CORRECTIONS.md), [`case/CORRECTIONS.md`](case/CORRECTIONS.md).
  - **Fifth `--fix` round (2026-08-17)**: **351 → 298 (−53, −15.1%)**; 264 → 233 flagged parse
    units (31 cleared, 10 improved, **0 regressed, 0 newly flagged**, exactly one position present
    after but not before); per-unit yield **0.201**; `pytest` 441; `skel/*.tsv` only, so no other
    layer moved. Run by the user after the Purgatorio 31–33 read closed Purgatorio, and again
    ahead of the schedule [`skel/PLAN.md`](skel/PLAN.md) had set. **It tested no prompt
    hypothesis, and that was verified in the source rather than assumed**: the last prompt-content
    commit is 1eb2a86 (2026-08-15), round 4 already decided its two additions, the queued
    time-or-place clause is still unwritten, and the model is unchanged since June. What had moved
    is the checker (`dante_corpus/skel.py` +1158/−55 since round 4), which is why the same prompt
    was asked different questions and graded by a stricter gate. **Finding: rules and LLM repair
    take largely disjoint residue** — a base fifteen rule batches lower still gave up 15.1%, at a
    flat −7…−17% across every bucket with n ≥ 9, with none of the single-class collapse that
    marked round 3's genuine prompt defect. Cost, measured: the seven Paradiso batches now sit on
    a base two rounds have moved, and the sixth round's one candidate lost 18% of its target
    (`missing_arg obl*` 76 → 62). Full subclass table in [`skel/PLAN.md`](skel/PLAN.md) §21.
  - **Rules DE–DF (Purgatorio 31–33 read, 2026-08-17)**: Per-position read of all 14 soft
    violations in Purgatorio 31–33, the batch that finishes **Purgatorio**, produced two
    deterministic rules — DF (rule V's control-subject candidates read through rule AI's Layer-3
    NP-head equivalence, −4) and DE (rule C's collapse: a conjunct carrying its own distinct
    `case` marker is a separate oblique, so its role never displaces the coordination head's own
    citation, censused at 98, −2) — plus 4 Layer-4 rows, 1 Layer-2 row, 2 Layer-3 spans and
    2 case-annex rows. **358 → 351 (−7, −2.0%)** with zero model calls; Purgatorio 31–33 itself
    14 → 11, `pytest` 441. Both rules are an existing normalization applied at a gate that had not
    read it — the ordering question in a fifth consecutive form. One candidate was censused at 2
    (against a structural population of 1026) and dropped; one Layer-4 correction deliberately
    *raised* the count by +1, exposing an LLM misreading the wrong tree had matched. See
    [`skel/CORRECTIONS.md`](skel/CORRECTIONS.md), [`dep/CORRECTIONS.md`](dep/CORRECTIONS.md),
    [`morph/CORRECTIONS.md`](morph/CORRECTIONS.md), [`np/CORRECTIONS.md`](np/CORRECTIONS.md),
    [`case/CORRECTIONS.md`](case/CORRECTIONS.md).
  - **Rules CZ–DD (Purgatorio 26–30 read, 2026-08-17)**: Per-position read of all 33 soft
    violations in Purgatorio 26–30 produced five deterministic rules — DA (rule CS's argument
    leg: an *empty* derived tuple contradicts no argument put on the predicate, **except** in the
    subject slot, where an empty tuple is rule V having declined, 17, −17), DD (the relative
    locative adverb Layer 4 writes as a `case` on its own clause's verb, censused at 21, −3), CZ
    (a `derive_unit` fix: a gapped-clause remnant the `case` annex assigns a case to claims that
    slot before the role-rank queue, −2), DB (rule AD's mismatch leg — the copula's only
    complement, an adverb `obl` because it carries a preposition, 2, −2), DC (rule AA/AU's host
    gate read through rule CE's relative-pronoun identity, structural census 489, −1) — plus 12
    Layer-4 rows. **388 → 358 (−30, −7.7%)** with zero model calls; Purgatorio 26–30 itself
    33 → 22, `pytest` 437. Three candidates were censused and dropped (at 1, 4 and — for a
    proposed upstream retag — 21, where the census showed a consistent Layer-4 convention rather
    than an error, which became rule DD instead). One Layer-4 correction deliberately *raised*
    the count by +2, exposing an LLM misreading the wrong tree had matched. See
    [`skel/CORRECTIONS.md`](skel/CORRECTIONS.md), [`dep/CORRECTIONS.md`](dep/CORRECTIONS.md).
  - **Rules CU–CY (Purgatorio 21–25 read, 2026-08-16)**: Per-position read of all 33 soft
    violations in Purgatorio 21–25 produced four deterministic Layer-5 rules — CW (rule BA's
    oblique leg: two derived subjects mean two collapsed clauses, so the arguments after the
    second subject are the elided clause's, censused at 85 / 13, −7), CX (rule CK widened from
    the complementizer to the interrogative word that opens a complement clause, 6, −6), CU (a ∅
    subject the LLM lists *beside* the derived one is the slot not decided, 6 / 4, −3), CY (the
    clausal-complement double-listing test read through the `aux` edge, 1, −1) — plus **rule CV**,
    the `dep.subject_agreement` ordering refinement that stops six *number*-only exclusions from
    preempting the person test (−3, `dep --check` still 0/0), 27 Layer-4 rows and 1 Layer-2 row.
    **409 → 388 (−21, −5.1%)** with zero model calls; Purgatorio 21–25 itself 33 → 24, `pytest`
    427. Two candidates were censused at 1 and 2 and dropped. Two upstream corrections deliberately
    *raised* the count (+6 between them) by exposing LLM misreadings the wrong tree had matched.
    See [`skel/CORRECTIONS.md`](skel/CORRECTIONS.md), [`dep/CORRECTIONS.md`](dep/CORRECTIONS.md),
    [`morph/CORRECTIONS.md`](morph/CORRECTIONS.md).
  - **Rules CP–CT (Purgatorio 16–20 read, 2026-08-16)**: Per-position read of all 26 soft
    violations in Purgatorio 16–20 produced four deterministic Layer-5 rules — CP (rule AZ's noun
    leg: a bare caseless `obl` nominal is the predicate's secondary predicate, censused at
    245 / 44, −5), CS (a derived predicate whose tuple is *empty* asserts nothing, so its absence
    is no divergence, −2), CQ (rule T's `xcomp` leg: the prepositional infinitive Layer 4 marks
    with `case` and attaches as a complement, −2), CT (a copula Layer 4 hung *under* its own
    predicate complement, 25 / 294, −2) — plus **rule CR**, the `dep.subject_agreement`
    refinement that narrows the 1/2-plural exclusion to the *number* test (−2, `dep --check`
    still 0/0), 17 Layer-4 rows, 2 Layer-2 rows, 1 Layer-3 span and 2 case-annex rows.
    **427 → 409 (−18, −4.2%)** with zero model calls; Purgatorio 16–20 itself 26 → 14, `pytest`
    414. Rule CS's own variant, refusing to *mint* the predicate rather than to report it, was
    measured at **+180** and rejected — the same reading is right at one end of the pipeline and
    wrong at the other. Two candidates were censused and dropped. See
    [`skel/CORRECTIONS.md`](skel/CORRECTIONS.md), [`dep/CORRECTIONS.md`](dep/CORRECTIONS.md),
    [`morph/CORRECTIONS.md`](morph/CORRECTIONS.md), [`np/CORRECTIONS.md`](np/CORRECTIONS.md),
    [`case/CORRECTIONS.md`](case/CORRECTIONS.md).
  - **Rules CK–CO (Purgatorio 11–15 read, 2026-08-16)**: Per-position read of all 30 soft
    violations in Purgatorio 11–15 produced five deterministic rules — CK (the LLM names a
    subordinate clause by the complementizer that opens it, censused at 18 / 3, −5), CM (rule AL
    read through the `case` annex: a fused clitic whose two slots back the two disputed roles
    separately, 13 / 7, −2), CL (rule AG's third leg — once the inherited subject is dropped the
    slot is rule V's to decide, −2), CN (rule AN's slot assignment: a ∅ slot goes to the back of
    the queue, −1), CO (rule AU's `advmod` leg, 101 / 77, −1) — plus the `dep.subject_agreement`
    coordinated-subject refinement the Inferno 21–25 batch had deferred, 11 Layer-4 rows, 8 Layer-2
    rows, 1 Layer-3 span and 1 case-annex row. **448 → 427 (−21, −4.7%)** with zero model calls;
    Purgatorio 11–15 itself 30 → 15, `pytest` 384. Two candidates were censused and dropped. See
    [`skel/CORRECTIONS.md`](skel/CORRECTIONS.md), [`dep/CORRECTIONS.md`](dep/CORRECTIONS.md),
    [`morph/CORRECTIONS.md`](morph/CORRECTIONS.md), [`np/CORRECTIONS.md`](np/CORRECTIONS.md),
    [`case/CORRECTIONS.md`](case/CORRECTIONS.md).
  - **Rules CA–CJ (Purgatorio 6–10 read, 2026-08-16)**: Per-position read of all 35 soft violations
    in Purgatorio 6–10 produced **ten** deterministic rules, the largest count of the series: CA
    (rule BN's argument test on the `conj` branch — an argumentless nominal conjunct is not an
    elided clause, censused at 209, −10), CC (its acceptance leg, the promoted coordinate nominal
    in the slot the LLM gives it, −5), CJ (rule V's oblique leg, −4), CF (the controller a fused
    clitic hides, 66, −3), CH (rule Z's adnominal leg — a verb in `amod`/`acl` is a reduced
    relative clause, 5019, −3), CB (an oblique stranded on a predicative complement the derivation
    never promotes, 566, −2), CG (the coordinate oblique whose noun is elided, 56, −2), CD (the
    coordination-head walk stopping where argument coordination ends, −1), CE (the antecedent and
    its relative clause's pronoun are one referent, 2061, −1), CI (rule AA's host test read through
    rule C's collapse, −1) — plus 1 Layer-4 row. **481 → 448 (−33, −6.9%)** with zero model calls;
    Purgatorio 6–10 itself 35 → 19, `pytest` 372. One variant was measured at **+168** and
    rejected, and one Layer-4 re-parse was worked out and deliberately left unapplied. See
    [`skel/CORRECTIONS.md`](skel/CORRECTIONS.md), [`dep/CORRECTIONS.md`](dep/CORRECTIONS.md).
  - **Rules BW–BZ (Purgatorio 1–5 read, 2026-08-16)**: Per-position read of all 14 soft violations
    in Purgatorio 1–5 — the first batch outside Inferno — produced four deterministic rules: BW
    (rule BM's mirror leg, an argument Layer 4 parked in the predicate's `mark` slot, censused at
    63 / 19, −9), BX (rule AZ's `missing_arg` leg, the bare adjectival oblique the LLM omits
    entirely, 44 / 11, −11), BY (the LLM splitting one periphrasis's arguments across the lexical
    verb and its `aux`, 5, −3), BZ (`derive_unit`'s `conj` walk running before the pass that
    resolves it, ±0 and kept for correctness) — plus 2 Layer-4 rows and 1 case-annex row.
    **506 → 481 (−25, −4.9%)** with zero model calls; Purgatorio 1–5 itself 14 → 10, `pytest` 351.
    Two candidates were censused at **1** each and dropped. See
    [`skel/CORRECTIONS.md`](skel/CORRECTIONS.md), [`dep/CORRECTIONS.md`](dep/CORRECTIONS.md),
    [`case/CORRECTIONS.md`](case/CORRECTIONS.md).
  - **Rules BO–BV (Inferno 31–34 read, 2026-08-16)**: Per-position read of all 37 soft violations
    in Inferno 31–34 — the batch that finishes Inferno — produced eight deterministic rules: BO
    (rule AI runs before rule D, −2), BP (nine child-of-predicate gates read an `aux`/`cop` head
    through to its lexical word, censused at 53, −1), BQ (rule BJ's other two orders for the
    adverb-preposition cluster, −6), BR (a derived argument buried in a Layer-3 phrase the LLM
    named by its head, −8), BS (rule Y named by its copula, −4), BT (rule AE's embedded side, the
    free relative's own governor, −3), BU (the subject a coordination supplies from its last
    conjunct, −2), BV (a `fixed` word of a multiword preposition names its nominal) — plus 15
    Layer-4 rows, 2 Layer-2 rows, 1 Layer-3 span and 1 case-annex row. **541 → 506 (−35, −6.5%)**
    with zero model calls; Inferno 31–34 itself 37 → 16. Two candidates were censused and dropped,
    one of them **rule BR's own mirror leg** (−6/+0), the first mirror the series has declined.
    See [`skel/CORRECTIONS.md`](skel/CORRECTIONS.md), [`dep/CORRECTIONS.md`](dep/CORRECTIONS.md),
    [`morph/CORRECTIONS.md`](morph/CORRECTIONS.md), [`np/CORRECTIONS.md`](np/CORRECTIONS.md),
    [`case/CORRECTIONS.md`](case/CORRECTIONS.md).
  - **Fourth `--fix` round (2026-08-16)**: **650 → 541 (−109, −16.8%)**; 443 → 388 flagged parse
    units (55 cleared, 38 improved, **0 regressed, 0 newly flagged**); per-unit yield **0.246**,
    the first rise of the series. Run by the user ahead of the read series it had been deferred
    behind. It decided all three queued prompt questions: the subject branches (−12.7% / −10.0%)
    and `missing_tuple_nominal`'s rewritten question (18 → 16) both **negative**, which turns the
    residue's two largest buckets into read-work, and `_CONV_REPEATED` **positive**
    (`missing_arg` −28.3%, −49 of the round). `extra_tuple_adjective` reached **0**. The cost of
    running early: the fifteen unread batches' rules are now measured against a base a round has
    moved. Full subclass table in [`skel/PLAN.md`](skel/PLAN.md) §12.
  - **Rules BJ–BN (Inferno 26–30 read, 2026-08-15)**: Per-position read of all 23 soft violations in
    Inferno 26–30 produced five deterministic rules — BJ (the adverb-preposition cluster names one
    oblique from either of its two words, −21), BK (rule AR's other marker: `che` opens the second
    term of a comparison, −4), BL (rule AR's other order: `sì come` is one word, −1), BM (an
    oblique whose filler Layer 2 calls a conjunction is the clause's connective, −11), BN (a
    conjunction in a clause-head deprel with no arguments is not an elided predicate, ±0) — plus
    three legs added to rules already in the checker (BI′ the `obj`-attached infinitive, AN′ the
    gapped comparison under `advcl`, AQ′ the `cop` merge applied to the membership check), 10
    Layer-4 rows and 1 Layer-2 row. **691 → 650 (−41, −5.9%)** with zero model calls; Inferno
    26–30 itself 23 → 11. One rule was censused and dropped (an `iobj` ↔ `obl:a` equivalence,
    population 0). See [`skel/CORRECTIONS.md`](skel/CORRECTIONS.md),
    [`dep/CORRECTIONS.md`](dep/CORRECTIONS.md), [`morph/CORRECTIONS.md`](morph/CORRECTIONS.md).
  - **Rules AZ–BI (Inferno 21–25 read, 2026-08-15)**: Per-position read of all 44 soft violations in
    Inferno 21–25 produced nine deterministic rules — AZ (rule R's mirror: a depictive adjective
    Layer 4 hung on the predicate as a bare `obl`, −13), BA (a predicate with two derived subjects
    has not decided between them, −41), BB (rule V's coordination leg, with rule BE, −26), BC (an
    `advmod` whose filler Layer 2 calls a noun or pronoun is an oblique, −14), BD (rule AW's third
    deprel, −10), BE (`flat` collapses like `conj`), BF (an inverted `cop` edge, −8), BH (rule M's
    mirror: the pro-drop ∅ subject its relabelling leaves behind, −14), BI (the
    accusative-and-infinitive's shared nominal, −10) — plus 20 Layer-4 rows and 5 Layer-2 rows.
    **834 → 691 (−143, −17.1%)** with zero model calls; Inferno 21–25 itself 44 → 16, the largest
    batch of the series. Two rules were censused and dropped and one `dep.subject_agreement`
    refinement was measured (12 new Layer-4 soft violations) and deferred. See
    [`skel/CORRECTIONS.md`](skel/CORRECTIONS.md), [`dep/CORRECTIONS.md`](dep/CORRECTIONS.md),
    [`morph/CORRECTIONS.md`](morph/CORRECTIONS.md).
  - **Rules AU–AY (Inferno 16–20 read, 2026-08-15)**: Per-position read of all 47 soft violations in
    Inferno 16–20 produced five deterministic rules — AU (an `amod` adjective over one of the
    predicate's own arguments is its secondary predicate, −17), AV (the LLM naming only an
    `aux`/`cop` as the predicate), AW (rule AB's mirror: a reflexive clitic Layer 4 left as `obj`),
    AX (an argument shared across an `xcomp` control edge), AY (an `amod` adjective governing an
    argument of its own predicates) — plus 25 Layer-4 rows and 1 Layer-2 row retagged.
    **888 → 834 (−54, −6.1%)** with zero model calls and **zero newly-flagged positions**; Inferno
    16–20 itself 47 → 31. Three of the five are mirror legs of rules already in the checker, which
    is the batch's transferable finding; one censused rule was measured and dropped at population
    12. See [`skel/CORRECTIONS.md`](skel/CORRECTIONS.md), [`dep/CORRECTIONS.md`](dep/CORRECTIONS.md),
    [`morph/CORRECTIONS.md`](morph/CORRECTIONS.md).
  - **Rules AM–AT (Inferno 11–15 read, 2026-08-15)**: Per-position read of all 37 soft violations in
    Inferno 11–15 produced eight deterministic rules — AM (arguments stranded on a `cop`/`aux`),
    AN (`orphan`-marked gapped coordination), AJ′ (rule AJ's sibling and downward directions),
    AP (apposition collapsed like coordination), AQ (a citation on an auxiliary names its lexical
    head), AR (verbless comparative clauses), AS (a fused clitic's second `case` slot), AT (only a
    verb inherits a subject across `conj`) — plus 16 Layer-4 rows and 2 Layer-2 rows retagged.
    **963 → 888 (−75, −7.8%)** with zero model calls; Inferno 11–15 itself 37 → 17. Four of the
    eight are in `derive_unit` itself, the first batch to find the derivation wrong rather than
    silent. Prompt side, unmeasured: the first subject-slot Stage-2 classes and a rewritten
    `missing_tuple_nominal` question. See [`skel/CORRECTIONS.md`](skel/CORRECTIONS.md),
    [`dep/CORRECTIONS.md`](dep/CORRECTIONS.md), [`morph/CORRECTIONS.md`](morph/CORRECTIONS.md).
  - **Third `--fix` round (2026-08-15)**: **1094 → 963 (−131, −12.0%)**; 696 → 618 flagged parse
    units (78 cleared, 42 improved, **0 regressed, 0 newly flagged**); per-unit yield 0.188, flat
    against round 2's 0.193. `missing_arg_adverb` **83 → 28 (−66.3%)** carried 42% of the round on
    its own and confirmed that the class was caused by the corpus's own prompt; the two other
    prompt clauses tested moved nothing. Full subclass table in [`skel/PLAN.md`](skel/PLAN.md).
  - **Layer-4 stacked-preposition normalization (2026-08-14)**: 161 multiword-preposition clusters rewritten to one UD shape (opening word `case`, later members `fixed`), closing the flat/chained lottery. Layer 5: **1094 → 1094, net zero** by design; `skel.py`'s lemma aggregation reads the new shape (rules O/`prep_stack` unchanged in behaviour). See [`dep/CORRECTIONS.md`](dep/CORRECTIONS.md), [`skel/CORRECTIONS.md`](skel/CORRECTIONS.md).
  - **Rules AH–AL (Inferno 7–10 read, 2026-08-14)**: Per-position read of all 37 soft violations in Inferno 7–10 produced five deterministic checker rules — AH (rule AG's second leg), AI (Layer-3 NP head vs Layer-4 attachment), AJ (coordination gapping of objects and datives), AK (comparative `come`), AL (dual-role fused clitics) — plus 5 Layer-2 mistags and 17 Layer-4 rows retagged. **1247 → 1091 (−156, −12.5%)** with zero model calls; Inferno 7–10 itself 37 → 17. Two candidates were measured and dropped, including a 247-token relative-`che` retag the `case` annex blocks. See [`skel/CORRECTIONS.md`](skel/CORRECTIONS.md).
  - **Prompt work in the same read**: `_CONV_ADVERB`'s "or it is left out" clause was found responsible for **82 `missing_arg` positions whose argument is a locative adverb** — the largest unbranched bucket in the residue. Fixed prompt-side, with a new Stage-2 class `missing_arg_adverb`; also the addressee-less elided-speech frame (`E io: «…»`, 4 of the 37) and appositive adjectives. **Round 3 measured all three: the adverb licence was the real defect (−66.3%), the other two moved nothing.**
  - **Rule AG (Inferno 4–6 read)**: Gated `conj` subject propagation on Layer-2 person/number agreement (`dep.subject_agreement` + `_finite_head_of`), reducing soft violations **1452 → 1409 (−43)** with zero model calls.
  - **Second `--fix` round (2026-08-14)**: First live pass of the `extra_arg_adjective` micro-prompt. **1409 → 1247 (−162, −11.5%)**; 841 → 765 flagged parse units (76 cleared, 62 improved, **0 regressed, 0 newly flagged**); per-unit yield 0.193, under half the first round's rate. Full subclass table in [`skel/PLAN.md`](skel/PLAN.md).
- **Phase 5 Retrospective**: Complete and closed (5,919 → 2,084). Established the flat yield ceiling of monolithic regeneration and the provenance law of yield. For full details, measurement tables, and lessons learned, see [`skel/PHASE5.md`](skel/PHASE5.md).

### Standing Disciplines

- **A silent `--check` pass, closed (2026-08-07)**: Found while re-measuring from a `git worktree` (where `src/` is unbuilt because per-canticle source directories are generated, not tracked). `api.cantos()` now raises `FileNotFoundError` if the directory is missing, preventing checks from silently returning `0 hard, 0 soft`. `tests/test_api.py` pins this behaviour.
- **How `CORRECTIONS.md` is used**: `*/CORRECTIONS.md` records **hand-applied corrections**, not a place to log "found a problem, leaving it." If a review turns up a clear, decidable error, **fix it in the same session** and record what was fixed and why. The only legitimate "left alone" write-ups are ones with a genuine structural reason the text itself doesn't decide (e.g., free relatives, accusative-and-infinitive, Latin quotations, etc.).
  - **A `--fix` round is not a correction and is never written there** (2026-08-16). It is LLM regeneration of the artifact, decided by the acceptance gate rather than by a person reading a line. Round measurements belong in [`skel/PLAN.md`](skel/PLAN.md)'s *Phase 6 Implementation & Results* and in this file's *Latest Improvements*. What does go in `CORRECTIONS.md` is what a human decided: upstream retags, gated-script rewrites, checker and derivation rules, and the shapes deliberately left standing.
- **CRLF hygiene**: Writing TSVs with Python's `csv` module and `newline=''` defaults to `\r\n`. Ensure `\n`-only line endings (`sed -i 's/\r$//'` or `Path.write_text` splitting/joining on `\n`) before diffing or committing.
- **Measure a checker rule by violation diff, never by the total** (2026-08-15): keep the sorted `--check` output before and after and diff it, so what a rule *newly flags* is visible next to what it removes. Two rules this session looked neutral or positive on the total and were only decidable from the diff — rule AM (−15/+22, kept: the derivation is now right) and its subject leg (dropped). A rule may be kept when it raises the count, if it makes the parse provably more correct; record that trade explicitly.
- **Census a shape before writing a rule for it** (2026-08-15): count the structural pattern over all 100 cantos first. One evidence line is not a population, and several candidate rules have been dropped at census — with a population of 0, and once (gapped-clause remnants, Inferno 16–20 batch) with a population of 12 that the census itself showed was reading error rather than checker silence.
- **When you write a checker rule, check its mirror leg** (2026-08-15): a labeling convention has two directions, and a rule that accepts "the LLM names X where the derivation names Y" leaves the reverse reported. Three of the Inferno 16–20 batch's five rules were mirror legs of rules already in the checker (AV, AW, AY), worth 18 positions between them.
- **Mutation-check a new rule's test**: break the rule in the source and confirm the test fails. A test that still passes with the rule removed pins nothing.
- **Editing frozen TSVs**: never by hand. Use a gated script that asserts the expected word at each `(line, token)` before rewriting the row, then re-run every layer's `--check` and `pytest`.

### Next Steps & Open Routes

- **The plan for the rest of the work (decided 2026-08-17)**: **read Paradiso in 5-canto batches — 26–30, then 31–33 — and run one `--fix` round when the series is finished.** No round in between. Paradiso 1–5 (rules DG–DJ), 6–10 (rules DK–DR), 11–20 (rules DS–DW, two batches in one session) and 21–25 (rules DX–EA) are read.
- **The read series is the standing task**: per-position reads of all 100 cantos in 5-canto batches. **Inferno, Purgatorio and Paradiso 1–25 are complete**; **Paradiso 26–30 is next** (23 soft at base 234), running to Paradiso 33. Two batches, 32 positions, both of them Paradiso; schedule (re-measured at base 234), reasoning and the eight-step per-batch procedure in [`skel/PLAN.md`](skel/PLAN.md)'s *The Read Series* / *How to Read a Batch*. Tool: `skel/read.py`.
- **The sixth `--fix` round has two candidates queued, and both are now written** (`make -C skel fix`, run 3-way parallel — the user's to run). The fourth round emptied the prompt queue on 2026-08-16 and the fifth (2026-08-17) ran with nothing on it. The Purgatorio 16–20 read's contribution — `_CONV_ADJUNCT`, a convention clause for the **prepositional adjunct of time, place, source or manner**, against `missing_arg obl*` now at **56 of 234**, still the residue's largest single bucket — was written into `skel/skel.py` by the Paradiso 11–20 read (2026-08-17), together with `_CONV_DATIVE` for the **non-core dative clitic** (3 positions in that batch, plus a fourth the Paradiso 21–25 read found). Both hang on the generic `missing_arg` class and are separable in a round's subclass table, because the dative surfaces as `missing_arg obl:a`. Neither moves anything until the round runs. See [`skel/PLAN.md`](skel/PLAN.md)'s *The Sixth `--fix` Round*.
- **Inferno's 55, Purgatorio's 85 and Paradiso 1–25's 62 standing positions** are the read batches' residue with two `--fix` rounds now over them — the most direct sample of what a round leaves behind. Not urgent: the two unread batches come first.
- **Other Assistant-Side Tasks** (populations at base 541 unless noted, so a re-measure at 234 comes first; folded into the batch that covers them):
  - **Check the mirror leg of every new rule** — the Inferno 16–20 batch's finding, worth 18 positions there, 37 more in the 21–25 batch and 20 more in the Purgatorio 1–5 batch (rules BW, BX). **A mirror is not owed acceptance**: the 31–34 batch measured rule BR's at −6/+0 and dropped it, because its only evidence was a Layer-3 span and Layer 3 is over-inclusive by design.
  - **Ask what fills the slot after a refusal, and how far the refusal generalizes** — the Purgatorio 6–10 batch's finding: rules CA and CC are one gate read from the derivation side and the acceptance side, and the same gate widened one step further measured **+168** and was rejected. Also **which normalization has already run on the citation a gate compares** (rules CD, CI, about rule C's coordination collapse).
  - **Ask whether a pass reads a set another pass writes** — the Purgatorio 1–5 batch's finding: `derive_unit`'s predicate census walked `conj` chains against a set its third pass had not yet filled (rule BZ). Ordering has now been the finding of four consecutive batches, in four different forms.
  - **Ask which *edge* a gate reads**, not only which rule reads it — the Inferno 31–34 batch's finding: nine acceptance rules compared Layer 4's raw head to the predicate while `derive_unit` had normalized through `aux`/`cop` since rule AM (rule BP, censused at 53).
  - **Check the *plural*, and the rule's place in the pipeline** — the Inferno 21–25 batch's finding: rule V was written to pop one citation where a coordinate subject supplies three, and the collapse that runs after it put the survivors back on the accepted position.
  - Per-position read of the `missing_arg_adverb` residue (**21**) — what the `_CONV_ADVERB` and `_CONV_REPEATED` repairs left standing.
  - Read `missing_tuple_nominal` (**16**; `missing_tuple` **18** total): a convention, a hint and a rewritten question have each moved it by single digits, so it is genuine reading disagreement until a read says otherwise. Its old sibling `extra_tuple_adjective` is **closed at 0**.
  - Measure the population of a `parataxis`→`ccomp` acceptance rule for quoted speech under verbs of speech (Inferno 8:81) before writing it. Its neighbour, the `sì … che` result clause read as `ccomp`, was censused at **2** and dropped.
    - Ask which checks run *before* every acceptance rule — the Inferno 26–30 batch's finding: rule AQ was complete inside `_classify_divergence` and absent from the membership check that runs first.
  - **Read `extra_arg subj` (**80**, of which ∅ (0,0) **23**) and `missing_arg subj` (**50**)** — the residue's two largest buckets. Round 4 measured `_CONV_SUBJECT`'s three diagnoses at the round average, which by the test's own branch makes these read-work rather than prompt-work. Start with the ∅ (0,0) half.
  - Audit remaining `extra_arg_adjective` positions (**19**; `extra_arg xcomp` is **35**) — three rounds have each taken only a couple, which is itself evidence of genuine disagreement.
  - **Read `missing_arg obl*` (re-measured at **56** of 234, bare `obl` 17; still the residue's largest single bucket).** The Purgatorio 16–20 read found four of them to be plain omissions of an adjunct or a dative the tree records; the Paradiso 11–20 read wrote both prompt clauses (`_CONV_ADJUNCT`, `_CONV_DATIVE`), which the sixth round now decides.
  - **CLOSED (2026-08-16, Purgatorio 11–15 read)**: the `dep.subject_agreement` *coordinated subject* refinement. The deferred form (number test only) was the wrong rule; the person test run against **every conjunct** leaves 6 positions, all upstream errors, now corrected. `dep --check` stays 0/0 and Layer 5 moved −3/+1 — see [`dep/CORRECTIONS.md`](dep/CORRECTIONS.md).
- See [`skel/PLAN.md`](skel/PLAN.md) for full descriptions of each route and testing workflows.

## Status

**All five layers are implemented, built for all 100 cantos, and merged to `main`.** Layer 5's
checker was refined through Phases 0-5r, rules V through EA, and Phase 6's restructuring plus five `--fix` rounds, bringing its soft residue to **234**
(down from 17438 at the first full-corpus measurement). See [`skel/PHASE5.md`](skel/PHASE5.md) for the full Phase 5
history, [`skel/PLAN.md`](skel/PLAN.md) for the closing positions, and *The layers* below and [`skel/README.md`](skel/README.md) for the design and current status.

**The pronoun case annex is complete and closed (2026-08-02).** It is a permanent Layer-2 sibling
extension, `case/`, on the same footing as `np/`, `dep/` and `skel/` relative to `morph/` — not a
new `morph/*.tsv` column, decided at the annex's close after two budgeted blind-regeneration
rounds were measured and rejected against a verdict rule fixed in advance. See
[`case/README.md`](case/README.md) for the design and current status and
[`case/CORRECTIONS.md`](case/CORRECTIONS.md) for the full measurement history, including *Step 5 —
the merge decision*.

**The open route is the read series, then one final `--fix` round**: per-position reads of all 100 cantos in 5-canto batches. Inferno, Purgatorio and Paradiso 1–25 are complete; Paradiso 26–30 is next, running to Paradiso 33, and the sixth round follows the last batch (see *Next Steps & Open Routes* above and [`skel/PLAN.md`](skel/PLAN.md)). All five layers plus the case extension are implemented, built for all 100
cantos and merged to `main`. Detailed open routes and measurement instructions live in [`skel/PLAN.md`](skel/PLAN.md).

- **Layer 1 — Tokens**: implemented (`dante_corpus/tokenizer.py`, served via `Line.tokens`).
- **Layer 2 — Morphology + lemma**: implemented; see [`morph/README.md`](morph/README.md).
  Artifacts are built for all 100 cantos. Its pronoun-case feature is served separately, as the
  permanent Layer-2 sibling extension `case/` — see [`case/README.md`](case/README.md).
- **Layer 3 — Noun phrases**: implemented; see [`np/README.md`](np/README.md). Build
  driver `np/np.py`, served via `Canto.np()` and `dante-corpus text np`. Artifacts generated for
  all 100 cantos. `--check` reports **0 hard / 0 soft** — see
  [`np/README.md`](np/README.md)'s *Check* section and [`np/CORRECTIONS.md`](np/CORRECTIONS.md).
- **Layer 4 — Dependency / grammatical role**: implemented and complete; see
  [`dep/README.md`](dep/README.md). Build driver `dep/dep.py`, served via `Canto.dep()` and
  `dante-corpus text dep` (with `text np` gaining a derived `role=` per noun phrase). Artifacts
  built for all 100 cantos; `--check` reports **0 hard / 0 soft** violations — every class at 0,
  including the subject-agreement rule, whose 18-position residue was closed 2026-08-14 — see
  [`dep/README.md`](dep/README.md)'s *Check* section and
  [`dep/CORRECTIONS.md`](dep/CORRECTIONS.md) for the full correction history.
- **Layer 5 — skeleton**: implemented, all 100 cantos built, checker refined through Phases 0-5r
  — the four mechanical phases (normalization, authority model, `--repair`,
  double-listing/elided-copula whitelist) plus Phase 5's rule series, 5r's rule U, which reads the
  `case` annex as a third opinion on a disputed argument role, rule V, which supplies the
  control/participial subject of a non-finite predicate, the Y-AF series, which closes eight
  further shapes where the derivation was silent rather than disagreeing, and the AG-EA series
  from the Inferno 4-6, 7-10, 11-15, 16-20, 21-25, 26-30 and 31-34, the Purgatorio 1-5, 6-10,
  11-15, 16-20, 21-25, 26-30 and 31-33 and the Paradiso 1-5, 6-10, 11-20 and 21-25 per-position reads; see
  [`skel/README.md`](skel/README.md). `dante_corpus/skel.py` (dataclasses, role
  vocabulary, deterministic derivation, table parsing, validation, TSV I/O, serve-time joins),
  `dante_corpus/hashes.py` (content-hash versioning, all layers), `Canto.skel()`/`Canto.hashes()`
  in `api.py`, `dante-corpus text skel`/`dante-corpus hash` in `cli.py`, `skel/skel.py` (LLM
  build driver, mirrors `dep/dep.py`, plus `--stats`/`--repair` modes), `skel/read.py` (the audit
  series' read tool: all five layers plus both Layer-5 readings for one parse unit). `--check` across all
  three canticles reports **0 hard, 234 soft** (down from 17438 at the first full-corpus
  measurement) — see [`skel/README.md`](skel/README.md)'s *Check* section and
  [`skel/CORRECTIONS.md`](skel/CORRECTIONS.md) for the full correction history, including the
  case annex's contribution to that count. Phase 5 (see [`skel/PHASE5.md`](skel/PHASE5.md)) is
  **complete**: its measured finding was that monolithic `--fix` yields a flat ~0.09-0.11 violations per
  LLM call on static residue, leading to the adoption of deterministic checker rules and upstream corrections.
  **Phase 6 (2026-08-12) restructured `--fix` itself** into deterministic repairs (Stage 1), class-specific
  POS-keyed micro-prompts (Stage 2), and fallback whole-unit regeneration (Stage 3). `--fix` rounds are
  **LLM-regeneration work the user runs themselves** (`make -C skel fix`, run 3-way parallel); checker-side
  and audit work is the assistant's.

`grammar-stack-plan` was merged into `main` (fast-forward) and pushed; Layers 1–4 and their
artifacts now live on `main`.

## Why this lives in the corpus

`dante-corpus` is the queryable, **canon-neutral source of truth** for the *Commedia*: it serves
the normalized Italian text, the token stream, and the nested quote-span tree, all derived from
the poem itself with no external ontology. Today it stops at tokens and quotes.

Downstream projects each need to *read the source grammatically* before they can do their own
work — the formalization layer (`dante-analyze`) to extract entities and relations, the
translation layer (`dante-dravidian`) to align tokens to a reference. Both currently re-derive
the same morphosyntax from scratch, in their own prompts, every time. That re-derivation is not
project-specific: **the grammar of an Italian line is the same regardless of what you do with
it.** So it belongs here, computed once, and served like any other corpus asset.

The line that keeps this in the corpus — rather than letting it drift into an interpretation
engine — is a strict **asymmetry**:

> The corpus **enumerates and annotates** what the text's own grammar determines.
> Consumers **decide, normalize, and bind to external references** on top of that.

Everything in this plan is recoverable from the Italian source alone. Nothing here looks at a
reference translation, a knowledge-graph goal, or any external canon. The contested judgments —
*is this noun phrase an entity? which closed relation is this verb? is this a simile? what is the
English equivalent?* — are deliberately **not** computed here; they are the consumers' jobs (see
*Out of scope* below). This keeps the corpus reproducible and neutral while still removing the
duplicated reading.

## The layers

Five layers, each a function of the source text. All five are implemented and built for all 100
cantos. Examples use *Inferno* I.1–6.

```
1  Nel mezzo del cammin di nostra vita
2  mi ritrovai per una selva oscura,
3  ché la diritta via era smarrita.
4  Ahi quanto a dir qual era è cosa dura
5  esta selva selvaggia e aspra e forte
6  che nel pensier rinova la paura!
```

### Layer 1 — Tokens *(implemented — no new work)*

The token stream already produced by `dante_corpus/tokenizer.py` and served via `Line.tokens`.
This is the deterministic foundation every higher layer cites and checks against; it needs no
further design. Its unit already matches what the morphology layer expects: it splits
apostrophe-linked elisions (`ch'` `i'`), keeps prepositional contractions whole (`Nel`, `del`),
and excludes punctuation (`has_alpha`).

- `mi` `ritrovai` `per` `una` `selva` `oscura` …
- **Generation**: deterministic (`tokenizer.py` over the normalized `src/`).
- **Check**: each token is a verbatim, in-order substring of its source line.

### Layer 2 — Morphology + lemma *(implemented — see [`morph/README.md`](morph/README.md))*

Per-token lemma, part of speech, and morphological features (gender, number, person, tense, mood),
plus a note for contraction / apocope / elision — generated from the Italian alone at build time,
aligned 1:1 to the Layer-1 tokens, and frozen as TSV. This is the first layer that removes
duplicated reading: the translation layer (`dante-dravidian` Step 1) currently regenerates the same
morphology inline; this is what it would consume instead. A prior local-LLM experiment produced
exactly this table from the source with no reference, evidence the layer is intrinsically
recoverable.

The mechanics — columns, generation rules, the token-alignment algorithm, validation tiers, and
usage — live in [`morph/README.md`](morph/README.md). It is served via `Canto.morph()` and
`dante-corpus text morph`.

**Pronoun case** is served as a Layer-2 morphological feature — the one this layer's own columns
omit — but held in its own permanent sibling directory rather than a `morph/*.tsv` column, so no
existing artifact hash moves. See [`case/README.md`](case/README.md) for the design, scope, and
vocabulary, and [`case/CORRECTIONS.md`](case/CORRECTIONS.md) for why a sibling directory over a
merged column.

### Layer 3 — Noun-phrase enumeration *(implemented — see [`np/README.md`](np/README.md))*

Every noun phrase in the line, with its head, source span, and modifiers — enumerated
**exhaustively and over-inclusively**. The corpus does **not** decide whether an NP is an entity;
it lists every candidate so consumers can decide. Each NP is frozen as a contiguous Layer-1 token
range (`start`/`end`) with a `head` token index and verbatim `text`; nesting is derived by span
containment at serve time. Served via `Canto.np()` and `dante-corpus text np`.

- `[nostra vita]` · `[una selva oscura]` · `[la diritta via]` · `[esta selva selvaggia e aspra e
  forte]` · `[la paura]`
- **Generation**: LLM shallow parse at build time, frozen. Nesting (e.g. `mezzo del cammin di
  nostra vita`) is represented explicitly; over-inclusion is correct behaviour, not noise.
- **Check**: each NP span reproduces a verbatim source substring; the head token lies within the
  span.
- **Scope**: NP spans are **single-line** by design (each is a verbatim substring of one source
  line), so an enjambed phrase appears as its per-line pieces and is rejoined by layer-4
  attachment. Bare clitic and relative pronouns are **not** NPs — they are layer-1/2 tokens that
  receive their clause function in layer 4.

### Layer 4 — Dependency / grammatical role *(implemented — see [`dep/README.md`](dep/README.md))*

Each token tagged with its function in the clause (a Universal Dependencies relation) and the head
it attaches to — `[la diritta via]` = subject of `era smarrita`; `che` (l.6) = relative pronoun,
subject of `rinova`, antecedent `[esta selva …]`. Attachment may cross line boundaries, which is
what rejoins layer-3's single-line enjambed NP pieces; bare pronoun tokens (deliberately not
layer-3 NPs) each carry a role and a head here, making every pronoun mention enumerable. The
mechanics — parse units, index-citing generation, validation tiers, and usage — live in
[`dep/README.md`](dep/README.md). It is served via `Canto.dep()` and `dante-corpus text dep`.

### Layer 5 — Predicate-argument skeleton *(implemented — see [`skel/README.md`](skel/README.md))*

Predicate ↔ argument tuples binding layers 2–4 into bare propositions, citing **token
positions**, not raw text or lemmas — `[la diritta via]` = subject of `smarrita`; `che` (l.6) =
relative pronoun, subject of `rinova`, antecedent `[esta selva …]` (derived at serve time via
`skel.antecedent`, not stored). This is the *raw* skeleton only: **no semantic frame, no
coreference, no vocabulary normalization.** Role labels are **UD-derived**
(`subj`/`obj`/`iobj`/`attr`/`xcomp`/`ccomp`/`obl:<preposition lemma>`), not semantic, so they
stay directly comparable with the deterministic derivation below and the vocabulary stays
canon-neutral.

Unlike Layers 2–4, **the LLM authors the artifact but a deterministic derivation is the
checker**: `derive_unit` in `dante_corpus/skel.py` computes the same predicate-argument
structure mechanically from the frozen Layers 2–4, and the LLM proposes its own, independent
reading of the same parse unit (it is **not shown** the Layer-4 parse). Soft checks report every
divergence between the two. A purely deterministic Layer 5 would just be `f(dep)` and could
never disagree with Layer 4; giving the LLM an independent read means a divergence can surface
a genuine Layer-4 mis-parse, not just an LLM slip — Layer 5 doubles as an audit of Layer 4,
triaged with the same measure-then-freeze discipline as `dep/CORRECTIONS.md`. The mechanics —
parse units, table format, the derivation, the divergence-normalization/authority-model/
`--repair` checker phases, and usage — live in [`skel/README.md`](skel/README.md). It is served
via `Canto.skel()` and `dante-corpus text skel`.

## Out of scope — consumer responsibilities

These are intentionally absent from the corpus because they are not determined by the text's own
grammar; they are contested judgments, normalizations, or bindings to something external. Listing
them fixes the boundary:

- **Entity-hood and entity typing** — which layer-3 noun phrases are entities, and of what kind.
  (A formalization-layer judgment, frozen against that project's own evidence-derived vocabulary.)
- **Coreference / referent identity** — linking pronouns, pro-drop subjects, and epithets to a
  single referent. (Reading-bound interpretation; belongs to the consumer.)
- **Closed relation vocabulary** — mapping a layer-5 predicate onto a frozen relation set.
- **Frame** — literal / simile / prophecy / reported. (Interpretive.)
- **Reference equivalents and truth-conditions** — any alignment to an English (or other) reference
  translation. (Translation-layer concern; brings external canon and must not enter the corpus.)
- **An imported verb-valency lexicon** — the instrument that would settle Layer 5's remaining
  complement-vs-adjunct disagreements (`essere`/`stare`/`parere` as copulas, and the ~37 lemmas
  behind the residual `advcl` cases). Rejected on the same grounds: it is an external authority,
  not something the Italian line determines. Note the contrast with the case extension
  ([`case/README.md`](case/README.md)), which asks a model to *read* the source rather than
  importing a dictionary, and so satisfies the *Neutrality audit* invariant below.

## Build & serve model

Mirror the existing `quotes/` pipeline exactly: a build step generates each layer, the result is
**committed**, and the package then **serves it deterministically** through the `dante_corpus`
API. The LLM is a build-time tool whose output is frozen and round-trip-checked — consumers see a
stable, reproducible asset, never a live model call. This follows the *measure-then-freeze*
discipline already used for normalization and quotes.

- **Artifact**: one structured file per canto per layer, under its own directory. Rectangular
  layers freeze as TSV (Layer 2 → `morph/<canticle>/NN.tsv`, one line-numbered row per token);
  layers with nesting may use another structured form. Layers join by token order; whether later
  layers share a file or stay in sibling directories is decided per layer.
- **Versioning**: every canto×layer artifact is **content-addressed** — the serve API exposes a
  content hash alongside the data, so a consumer can record exactly which parse a derived artifact
  annotated and recompute only what a regeneration actually changed (granular invalidation, per
  `dante-analyze`'s REARCHITECTURE.md). Regenerating one canto changes only that canto's hash;
  nothing else downstream is invalidated.
- **Build driver**: each LLM-built layer's generator lives in its own step directory (Layer 2 →
  `morph/morph.py`, the reference implementation) and is **resumable from its own output** — every
  chunk's rows are written back to the artifact as soon as they validate, so an interrupted run
  skips already-committed lines and re-requests only the remainder. Progress is shown live through
  `llm7shi.statusline` (Rich) — a per-canto bar (`canticle canto/total |
  line/total …`) with the model's streamed output routed through the same console.
- **Output routing convention** (shared across all LLM build drivers): the `StatusLine` object
  (`ui`) is the single output channel throughout the build flow. `ui.log()` is used for status
  messages (skip, resume, wrote); `ui.stream` is passed as `file` to the `llm7shi.Client` so
  streamed LLM tokens flow through the same console; `ui.stream.error()` is used for error
  messages (attempt failures, giving up) so they appear in red and are visually distinct from
  normal progress output. All future layer drivers follow this same convention.
- **Multi-turn recovery** (shared pattern): the `llm7shi.Client` maintains a conversation session,
  enabling two-stage recovery when a local model fails to produce a complete response in one turn.
  First, split output is repaired before alignment (e.g. `_merge_tables()` in Layer 2 merges
  consecutive pipe-tables into one). Second, if the aligned result still has lines with fewer
  elements than expected, a follow-up turn on the same session asks the model to supply the missing
  content, and the result is concatenated before retrying. These two stages — structural repair
  then continuation — are the standard recovery pattern for all LLM-built layers.
- **API**: extend the corpus query surface (alongside `text tokens`, `quote show`) with each
  grammatical layer, addressable by canticle / canto / line range (Layer 2: `Canto.morph()` /
  `dante-corpus text morph`).
- **Strongest reader for the hard layers**: morphology (L2) is robust; NP/dependency/skeleton
  (L3–L5) are reading-bound and should use the strongest available model at build time, measured
  before freezing.

## Validation

- **Per-layer checks** (above) run over all 100 cantos; zero round-trip failures is the structural
  bar, exactly as for `quotes/`.
- **Closed tag/role sets**: features (L2) and roles (L4) validate against frozen vocabularies, so a
  drift in the build model is caught rather than silently absorbed.
- **Neutrality audit**: the build prompt for every layer takes only the Italian source as input —
  no reference translation, no entity list, no canon. This is the invariant that lets two very
  different consumers share one parse.

## Sequencing

1. **Layer 2 (morphology + lemma)** — *implemented* (`dante_corpus/morph.py` + `morph/morph.py`). Lowest risk,
   already shown feasible intrinsically, and immediately useful as a lemma-queryable index.
2. **Layer 3 (noun phrases)** — *implemented* (`dante_corpus/np.py` + `np/np.py`). The census/entity
   substrate consumers most want.
3. **Layer 4 (dependency)** — *implemented* (`dante_corpus/dep.py` + `dep/dep.py`). The syntactic
   spine that rejoins enjambed NPs and makes pronoun mentions enumerable.
4. **Layer 5 (skeleton)** — *implemented* (`dante_corpus/skel.py` + `dante_corpus/hashes.py` +
   `skel/skel.py`), all 100 cantos built, checker refined through Phases 0-5r plus rules V, W,
   X, the Y-AF series, AG, the AH-AL series, the AM-AT series, the AU-AY series, the AZ-BI
   series, the BJ-BN series, the BO-BV series, the BW-BZ series, the CA-CJ series, the CK-CO series, the
   CP-CT series, the CU-CY series, the CZ-DD series, the DE-DF series, the DG-DJ series, the DK-DR series and the DS-DW series, with
   `--fix` restructured in Phase 6 and five rounds run (`--check`: 0 hard / 234 soft). Phase 5 closed with every route measured; see
   [`skel/PLAN.md`](skel/PLAN.md) and [`skel/README.md`](skel/README.md).
5. **Pronoun case extension** — *complete and closed, 2026-08-02*
   (`dante_corpus/case.py` + `case/case.py`; [`case/README.md`](case/README.md),
   [`case/CORRECTIONS.md`](case/CORRECTIONS.md)). Not a sixth layer: a
   Layer-2 morphological feature held in its own **permanent** directory, useful to consumers on
   its own terms independently of Layer 5's violation count. See [`case/README.md`](case/README.md)
   for the full status.

Build alongside the existing assets, gate each layer on its checks, then expose through the API.
Layers 1–5 are implemented, built for all 100 cantos, and merged to `main`; the grammatical
stack this plan describes is complete. **The pronoun case extension is also complete and closed**,
merged to `main`.
