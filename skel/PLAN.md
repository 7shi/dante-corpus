# skel — Layer 5 Plan: Deterministic Derivation & Targeted Micro-Fixes

## Status

- **Current State**: `make -C skel check` reports **0 hard, 224 soft** violations across all 100 cantos, after **rule EG** (174 → 224, **+50 by design** — the artifact-internal dual-role check, 2026-08-18, §28) and the **sixth `--fix` round** before it (213 → 174, −39, −18.3%, 2026-08-18, §27), which followed **rules EB–EF and the Paradiso 26–33 read** (234 → 213, −21, 2026-08-17), **the batch that finished the read series over all 100 cantos**, and before it rules DX–EA and the Paradiso 21–25 read (245 → 234, −11), and rules DS–DW and the Paradiso 11–20 read (261 → 245, −16), and rules DK–DR and the Paradiso 6–10 read (288 → 261, −27) and rules DG–DJ and the Paradiso 1–5 read (298 → 288, −10) and the **fifth `--fix` round** (351 → 298, −53, 2026-08-17) and rules DE–DF and the Purgatorio 31–33 read (358 → 351, −7), rules CZ–DD and the Purgatorio 26–30 read (388 → 358, −30), rules CU–CY and the Purgatorio 21–25 read (409 → 388, −21), rules CP–CT and the Purgatorio 16–20 read (427 → 409, −18), rules CK–CO and the Purgatorio 11–15 read (448 → 427, −21), rules CA–CJ and the Purgatorio 6–10 read (481 → 448, −33), rules BW–BZ and the Purgatorio 1–5 read (506 → 481, −25), rules BO–BV and the Inferno 31–34 read (541 → 506, −35), the fourth `--fix` round (650 → 541), rules BJ–BN (691 → 650), AZ–BI (834 → 691), AU–AY (888 → 834), AM–AT (963 → 888) and the third round (1094 → 963). Per canticle **at 174** (before rule EG): inferno 49, purgatorio 67, paradiso 58. **The next step is the seventh `--fix` round, which is the user's to run** — see *The Seventh `--fix` Round* below for what is on its scale, and *Sixth User-Run `--fix` Round* (§27) and *Rule EG and the Sixth Round's Prompt Repairs* (§28) for how the base got here.
- **Other Layers**: `dep --check` **0 hard / 0 soft** — the *coordinated subject* exclusion was
  refined to a per-conjunct **person** test on 2026-08-16 by the Purgatorio 11–15 read, which
  closed the 12-position route the Inferno 21–25 batch had deferred (16 rows corrected 2026-08-15 by the Inferno 11–15 read, 25 more by the Inferno 16–20 read, 20 more by the Inferno 21–25 read, 10 more by the Inferno 26–30 read the same day, 15 more 2026-08-16 by the Inferno 31–34 read, 9 of them the `con esso` normalization, 2 by the Purgatorio 1–5 read, 1 by the Purgatorio 6–10 read, 11 by the Purgatorio 11–15 read, 17 by the Purgatorio 16–20 read, 27 by the Purgatorio 21–25 read, 12 by the Purgatorio 26–30 read, 4 by the Purgatorio 31–33 read, 6 by the Paradiso 1–5 read, 10 by the Paradiso 6–10 read and 9 by the Paradiso 11–20 read, 10 by the Paradiso 21–25 read and 16 by the Paradiso 26–33 read; the 1/2-plural exclusion was narrowed to its number half by rule CR the same day, and the 3 positions that surfaced joined `_DISTRIBUTIVE_LEMMAS`; rule CV then took the *ordering* half of the same reading — the number-only exclusions had been returning before the person test — and its one new position, inferno 23:103, was corrected upstream). The subject-agreement rule's 18-position residue closed 2026-08-14 (Layer 5 1091 → 1094), and **Layer 4's stacked prepositions were normalized the same day** — 161 multiword-preposition clusters rewritten to one UD shape (opening word `case`, later members `fixed`), moving Layer 5 by zero (see [`CORRECTIONS.md`](CORRECTIONS.md) and [`../dep/CORRECTIONS.md`](../dep/CORRECTIONS.md)). `case --check` 0 hard (1 stale row dropped and 1 row re-read 2026-08-16, 1 more dropped by the Purgatorio 11–15 read, 2 re-read by the Purgatorio 16–20 read, 2 by the Purgatorio 31–33 read, 1 re-read and 1 added by the Paradiso 1–5 read, 1 dropped and 1 added by the Paradiso 6–10 read, 2 dropped by the Paradiso 26–33 read), `np --check` 0/0 (1 span split 2026-08-16, 1 widened and 1 added by the Purgatorio 11–15 read, 1 moved by the Purgatorio 16–20 read, 2 by the Purgatorio 31–33 read, 1 clitic span added by the Paradiso 1–5 read, 1 dropped by the Paradiso 21–25 read, 3 dropped and 2 rewritten by the Paradiso 26–33 read), `morph --check` 0/0 (3 rows corrected 2026-08-15 by the 11–15/16–20 reads, 5 more by the 21–25 read, 1 by the 26–30 read, 2 by the 31–34 read, 8 by the Purgatorio 11–15 read, 2 by the Purgatorio 16–20 read, 1 by the Purgatorio 21–25 read, 1 by the Purgatorio 31–33 read, 1 by the Paradiso 1–5 read, 2 by the Paradiso 6–10 read, 1 by the Paradiso 11–20 read, 1 by the Paradiso 21–25 read and 6 by the Paradiso 26–33 read), `pytest` **518 passed**
  (the Purgatorio 26–30 read added 10, the Purgatorio 31–33 read 4 more, the Paradiso 1–5 read 8 more, the Paradiso 6–10 read 16 more, the Paradiso 11–20 read 10 more, the Paradiso 21–25 read 8 more, the Paradiso 26–33 read 11 more, rule EG 17 more and the field-note instrument 7 more). The fourth, fifth and sixth
  `--fix` rounds (2026-08-16 / 2026-08-17 / 2026-08-18) touched `skel/*.tsv` only, so no other layer moved.
- **Phase 5**: Complete and closed (reduced soft violations from 5,919 to 2,084). Full historical record, per-phase measurement tables, cost comparisons, and lessons learned are documented in [`PHASE5.md`](PHASE5.md).
- **Phase 6**: Rebuilt `--fix` into a three-stage driver (Stage 1 deterministic, Stage 2 class-specific micro-prompts — now **fourteen**, keyed by POS, by role, by class, or on the two shapes that stand in for a pair of rows, Stage 3 fallback). Six user-run rounds so far: **2011 → 1452 (−27.8%)**, **1409 → 1247 (−11.5%)**, **1094 → 963 (−12.0%)**, **650 → 541 (−16.8%)**, **351 → 298 (−15.1%)**, **213 → 174 (−18.3%)**.
- **Latest Work**:
  - **Field notes — the model's own report, into `--log` (2026-08-18, §29)**: every prompt in
    `skel.py` now carries one **conditional** slot beside its answer — a `N…` line for a question the
    sentence does not support, one where two answers are equally defensible, or one whose convention
    does not fit. It is not an escape hatch (the model answers every question anyway) and it is
    **inert** (`_split_field_notes` strips the notes before the response reaches `prompt.apply` or
    `skel.resolve_chunk`, so splices, `_is_improvement` and every per-class number are unchanged, and
    a seventh round stays comparable with the six before it — pinned by
    `test_a_field_note_changes_nothing_about_the_splice`). What it buys is a **position to read**
    chosen by something other than reading 100 cantos to find it, which is the gap rule EG measured:
    52 of its 56 positions were on lines `--check` is silent about, so no read batch could reach
    them. Collection is opt-in — `--log`, **one file per parallel process** — and the notes are a
    hypothesis about the *question*, never evidence about the corpus. `pytest` **518 passed** (7 new),
    0 hard / 224 soft, `skel/*.tsv` untouched. See §29 for how to read a round's notes.
  - **Sixth `--fix` round (2026-08-18)**: **213 → 174 (−39, −18.3%)**, 0 hard, `pytest` **494**;
    units **168 → 141** (27 cleared, 5 improved, **0 regressed, 0 newly flagged**); per-unit yield
    **0.232**. The round the read series was written to enable — checker finished, all 100 cantos
    read, nothing written against the base it would move — so its per-class numbers measure the
    prompt alone. **`_CONV_ADJUNCT` is positive and the subclass table hid it**: `missing_arg obl*`
    fell only 24.0% in aggregate, but the roles the clause's prose actually names —
    `obl:{in,da,di,con,tra,per}` — fell **19 → 9 (−52.6%)**, while the bare `obl` (a secondary
    predicate, rules AZ/CP) went −6.7% and the marker pseudo-cases `obl:{come,onde,quale}` ±0.
    **`_CONV_DATIVE` is negative** (`obl:a` −8.3%). With that, the two positives in six rounds are
    the two that *withdrew or narrowed a licence the prompt granted*, and all four negatives added
    prose about a shape the model already reads wrong. Two structural findings: **the residue is a
    hard core** — re-checking the pre-round-5 artifact with today's checker gives 265 → 213 → 174,
    pure subtraction, and **173 of the 174 predate round 5**; and the round's one new position
    (paradiso 1:81) is **one token in two roles of one predicate**, a contradiction *inside the
    artifact* that no check looks for — censused at 56, 7 licensed by rule AL, **52 of 56 on lines
    with no violation at all**. See *Sixth User-Run `--fix` Round* and *After the Sixth Round* below.
  - **Rule EG + the sixth round's prompt repairs (2026-08-18)**: the round's own findings, landed the
    same day. **Rule EG** is the first check in this layer that reads the artifact *against itself* —
    one token filling two roles of one predicate, censused at 56 with 7 licensed by rule AL's fused
    clitic — and it **raises** the count, **174 → 224 (+50)**, the trade rule AM records; 52 of the 56
    were on lines `--check` said nothing about, which is why 21 read batches walked past them. With it:
    a **splice guard** in `_apply_missing_arg`, because the round itself wrote one of these (the class
    appends a row and never looked at the rows already there); the **`arg_slot` merge**, which asks a
    same-slot `missing_arg`/`extra_arg` pair as one question instead of two that could not see each
    other (8 predicates, 16 positions, frozen through three rounds because **no** single-class answer
    could clear them); and **`_CONV_DATIVE` rewritten**, its old "cite it as `iobj`" being an
    instruction the class it hangs on cannot carry out. `pytest` **511** (17 new, each
    mutation-checked). See *Rule EG and the Sixth Round's Prompt Repairs* (§28) below and
    [`CORRECTIONS.md`](CORRECTIONS.md).
  - **Rules EB–EF + Paradiso 26–33 read (2026-08-17)**: five deterministic rules — four
    acceptances and one in `derive_unit` — 16 Layer-4 rows, 6 Layer-2 rows, 4 Layer-3 spans and 2
    case-annex rows, scoring **234 → 213 (−21, −9.0%)** with zero model calls; Paradiso 26–33
    itself 32 → 14, and `pytest` **494**. **The last two batches, read in one session: the series
    now covers all 100 cantos.** Its first finding extends rule DY's by one column — a gate that
    names a part of speech *or a deprel* is a claim about a column, and `come`/`com` fills eight
    deprels and four Layer-2 tags with one reading, of which rule AR's gate admitted a single cell
    (rule EB, −3). Its corollary is new to the series: **a position an earlier batch assigned to
    the prompt can be checker silence** — paradiso 23:10 was written up as `_CONV_ADJUNCT` work
    three batches ago, and a prompt verdict is the only one of the five that leaves no rule behind
    to be measured. Its second finding is rule DA's boundary from a new side: rule EF stops the
    `conj` subject propagation at a sibling that has already supplied a subject, and **stopping is
    the rule — re-assigning to the nearer subject measured +8/−2 and was rejected**, because the
    empty slot is the authority model's to decide. Two candidates were censused and dropped (a
    Layer-3-only participial subject at 8, on the Inferno 31–34 batch's rule-BR precedent, and the
    causative causee's `obj`/`iobj` at 16, on the grammar). See *Rules EB-EF and the Paradiso 26-33
    Read* below and [`CORRECTIONS.md`](CORRECTIONS.md).
  - **Rules DX–EA + Paradiso 21–25 read (2026-08-17)**: four deterministic Layer-5 rules, 10
    Layer-4 rows, 1 Layer-2 row and 1 Layer-3 span, scoring **245 → 234 (−11, −4.5%)** with zero
    model calls; Paradiso 21–25 itself 21 → 11, and `pytest` **483**. Its finding is a cheaper
    form of the 11–20 batch's: **price a blocked candidate against the corpus's other instances
    of the same construction**. Paradiso 21:5 wants rule CX's role gate widened to `obl` and the
    widening takes it — but paradiso 23:14 is the identical construction, written by Layer 4 the
    identical way, and is *already accepted* because there the LLM said `obl` too. So the `obl` is
    a convention applied consistently and the divergence is a second claim about the role, which
    is what the gate exists to keep out. Second, **the composition of two normalizations**: rule
    DZ is the first shape that needs rule AI's NP-head equivalence *and* rule C's coordination
    collapse, and it was found by reading the one position of three that the checker already
    accepted. Third, **a POS gate is only as good as the tag's consistency** — `onde` carries four
    Layer-2 tags under one deprel, so rule DD's gate had to name the word (rule DY). One Layer-4
    correction deliberately raised the count by +1, exposing an LLM misreading the wrong tree had
    matched. See *Rules DX-EA and the Paradiso 21-25 Read* below and [`CORRECTIONS.md`](CORRECTIONS.md).
  - **Rules DS–DW + Paradiso 11–20 read (2026-08-17)**: five deterministic Layer-5 rules, 9
    Layer-4 rows and 1 Layer-2 row, scoring **261 → 245 (−16, −6.1%)** with zero model calls;
    Paradiso 11–20 itself 43 → 30, and `pytest` **475**. **Two batches read in one session.** Its
    finding is about the acceptance test the whole series runs on: a candidate measuring **−3/+0**
    — rule DQ's gate widened from `ccomp` to `xcomp` — was dropped only after *reading the three
    positions it removed*, two of which were control verbs whose inherited subject was correct.
    **Measure by violation diff, then read what the diff removed.** The same family is taken
    instead by rule DU, which asks a structural question about it: the shared-subject propagation
    across `conj` stops at a conjunct Layer 4 marks with its own subordinator (−8/+1, census 49).
    Rules DS and DT are both "which check runs first" — rule BW's own evidence line was still
    flagged because the membership check runs before it (the third instance, after rules AQ′ and
    DG). And the **sixth round's queued prompt clause is finally written**: `_CONV_ADJUNCT` for
    the prepositional adjunct of time or place, plus `_CONV_DATIVE`, this batch's own prompt
    finding. See *Rules DS-DW and the Paradiso 11-20 Read* below and [`CORRECTIONS.md`](CORRECTIONS.md).
  - **Rules DK–DR + Paradiso 6–10 read (2026-08-17)**: **eight** deterministic Layer-5 rules, 10
    Layer-4 rows, 2 Layer-2 rows and 2 case-annex rows, scoring **288 → 261 (−27, −9.4%)** with
    zero model calls; Paradiso 6–10 itself 18 → 6, and `pytest` **465**. Its finding is that **a
    rule's docstring can be more correct than its code**: rules DB and AK each state their
    deciding gate in prose (*the copula must have no other complement*; *a token no layer calls a
    preposition*) and each carried a second condition — the complement's part of speech, the
    particle's part of speech — inherited unexamined from the one line that motivated it. Dropping
    those (rules DL, DM) took 6 positions across five cantos and three canticles. Second, **a
    scope refusal is about the instrument, not the shape**: rule DQ reaches five positions of the
    impersonal-verb family the Paradiso 1–5 batch dropped at census 29 as needing a verb-valency
    lexicon, by asking a structural question instead of a lexical one. Third, **check a rule's
    test against both ends of the relation** — rule AG compares the inherited nominal with the
    recipient predicate and never the two *predicates* with each other (rule DO, 30 of 1151).
    Rule DN was measured in `derive_unit` at **−4/+40** and moved to the acceptance side, where
    it is −1/+0 — the rule-CS finding a second time. See *Rules DK-DR and the Paradiso 6-10 Read*
    below and [`CORRECTIONS.md`](CORRECTIONS.md).
  - **Rules DG–DJ + Paradiso 1–5 read (2026-08-17)**: four deterministic Layer-5 rules, 6 Layer-4
    rows, 1 Layer-2 row, 1 Layer-3 span and 2 case-annex rows, scoring **298 → 288 (−10, −3.4%)**
    with zero model calls; Paradiso 1–5 itself 26 → 18, and `pytest` **449**. Its finding is that
    **a gate written to admit a specific disagreement can exclude the case where the two sides
    agree outright** — rule CX required both roles to be complement roles in order to license
    `obj` ↔ `ccomp`, and identical roles, the strictly weaker claim, fell outside it (rule DJ).
    Second, ordering for the sixth consecutive batch, in the form the 26–30 batch named: rule DG
    is rule AQ′, the coordination collapse missing from the membership check that runs first.
    Third, a `derive_unit` refusal still owes an acceptance leg — rule AN has refused to mint a
    predicate at an `orphan`-marked gap since the Inferno 11–15 batch and never said what happens
    when the LLM mints one there (rule DI). One candidate was censused at 29 and **dropped on the
    corpus's own scope boundary**: separating impersonal verbs from modals in the `subj`-versus-
    `xcomp` class needs a verb-valency lexicon, which *Out of scope* rejects. See *Rules DG-DJ and
    the Paradiso 1-5 Read* below and [`CORRECTIONS.md`](CORRECTIONS.md).
  - **Fifth `--fix` round (2026-08-17)**: **351 → 298 (−53, −15.1%)**, 0 hard, `pytest` 441; units
    **264 → 233** (31 cleared, 10 improved, **0 regressed, 0 newly flagged**); per-unit yield
    **0.201**. Run with **no prompt change and no model change** — the last prompt-content commit
    is 1eb2a86 (2026-08-15), whose two additions round 4 already decided, and the one queued
    candidate (the prepositional adjunct of time or place) is still unwritten. So the round tested
    no hypothesis; what it measured instead is that **the read series' rules and the LLM's repairs
    address largely disjoint residue** — the same prompt, at a base fifteen rule batches lower,
    still took 15.1%, at a flat −7…−17% across every bucket with n ≥ 9. That flatness is itself
    the reading: round 3's signature of a real prompt defect was one class collapsing (−66.3%)
    against a flat background, and there is no such signal here. See *Fifth User-Run `--fix`
    Round* below.
  - **Rules CZ–DD + Purgatorio 26–30 read (2026-08-17)**: five deterministic rules — one of them
    in `derive_unit` — and 12 Layer-4 rows, scoring **388 → 358 (−30, −7.7%)** with zero model
    calls; Purgatorio 26–30 itself 33 → 22, and `pytest` **437**. Its finding is that **a rule's
    own evidence line can be the line the rule gets wrong**: rule AN's comment promised its
    gapped-clause remnants the slots "in the order the predicate's own arguments stand in the
    line" and named purgatorio 27:108 as the case, while its sort key ordered them by *role rank*
    — and had done so for four batches. The obvious repair is also wrong (−2/+3: Dante inverts a
    gapped clause's halves chiastically as readily as he parallels them, paradiso 29:78), and what
    decides every evidence line is the `case` annex — rule U's third opinion applied at the one
    place in `derive_unit` that is openly guessing (rule CZ). Third, **a rule that breaks an
    existing near-miss test has been told where its gate belongs**: rule DA's unrestricted form
    measured −23 and broke five tests of the rule-V family, because in the *subject* slot an empty
    derived tuple is rule V having declined, not the derivation being silent. See *Rules CZ–DD and
    the Purgatorio 26–30 Read* below and [`CORRECTIONS.md`](CORRECTIONS.md).
  - **Rules CU–CY + Purgatorio 21–25 read (2026-08-16)**: four deterministic Layer-5 rules, one
    `dep.subject_agreement` refinement (rule CV), 27 Layer-4 rows and 1 Layer-2 row, scoring
    **409 → 388 (−21, −5.1%)** with zero model calls; Purgatorio 21–25 itself 33 → 24, and
    `pytest` **427**. Its finding is that **a rule's own evidence names more than the slot it was
    written for**: rule BA reads two derived subjects as one predicate holding two collapsed
    clauses, and following that same evidence past the subject slot — everything after the second
    subject belongs to the elided clause — is rule CW, seven positions for one line of gating.
    Second, rule CR's defect was in **six** exclusions, not one, and as an *ordering* defect: every
    number-only licence in `subject_agreement` returned before the person test could run. Third,
    **an upstream correction can raise the count and still be right**: four of the batch's six new
    positions are the LLM's own misreadings that Layer-4 errors had been hiding. See *Rules CU–CY
    and the Purgatorio 21–25 Read* below and [`CORRECTIONS.md`](CORRECTIONS.md).
  - **Rules CP–CT + Purgatorio 16–20 read (2026-08-16)**: four deterministic Layer-5 rules, one
    `dep.subject_agreement` refinement (rule CR), 17 Layer-4 rows, 2 Layer-2 rows, 1 Layer-3 span
    and 2 case-annex rows, scoring **427 → 409 (−18, −4.2%)** with zero model calls; Purgatorio
    16–20 itself 26 → 14, and `pytest` **414**. Its finding is that **an exclusion can be right
    about one feature and wrong about the other**: `subject_agreement` treated a 1st/2nd person
    *plural* head as admitting any singular subject — true of number, false of person — and
    narrowing it to the number half closed purgatorio 20:102 at zero cost to `dep --check`.
    Second, rule CS's rejected variant: refusing to *mint* an argumentless non-verb clause head
    measured **+180**, while refusing to *report* the empty tuple it produces takes 2 — the same
    reading applied at the other end of the pipeline. Third, eleven of the 26 positions were
    upstream, ten of them in canto 16 — the second batch running where one canto carries the
    tree's errors. See *Rules CP–CT and the Purgatorio 16–20 Read* below and
    [`CORRECTIONS.md`](CORRECTIONS.md).
  - **Rules CK–CO + Purgatorio 11–15 read (2026-08-16)**: five deterministic rules, the
    `dep.subject_agreement` coordinated-subject refinement the Inferno 21–25 batch had deferred, 11
    Layer-4 rows, 8 Layer-2 rows, 1 Layer-3 span and 1 case-annex row, scoring **448 → 427 (−21,
    −4.7%)** with zero model calls; Purgatorio 11–15 itself 30 → 15, and `pytest` **384**. Its
    finding is that **a deferred route can be parked on the wrong rule**: the 21–25 batch measured
    the coordinated-subject exclusion restricted to the *number* test at 12 new `dep --check`
    violations and reverted it, and reading those 12 showed the right refinement is the *person*
    test against **every conjunct** — Italian agrees a finite verb with one member of a
    coordination, in either direction — which leaves 6, all of them upstream errors this session
    corrected. Second: Purgatorio 14 gave 12 of its 15 positions to the tree or the morphology,
    the highest upstream share of the series, against upstream checks standing at 0. Third: rule
    CN's *higher-scoring* first variant was the wrong rule, caught by reading the position it
    silenced. See *Rules CK–CO and the Purgatorio 11–15 Read* below and
    [`CORRECTIONS.md`](CORRECTIONS.md).
  - **Rules CA–CJ + Purgatorio 6–10 read (2026-08-16)**: ten deterministic rules and 1 Layer-4 row, scoring **481 → 448 (−33, −6.9%)** with zero model calls; Purgatorio 6–10 itself 35 → 19, and `pytest` **372**. The largest rule count of any batch, and eight of the ten are about coordination or about a predicate the derivation declines to mint. Its finding is that **an empty tuple is not a reading, and the refusal has a measured boundary**: rule CA extends rule BN's argument test to promoted `conj` conjuncts (−10), but pushing the same test to *all* non-verb clause heads measured **+168** and was rejected, and the `cop`/`aux` exemption rule CA carries was found by `pytest` failing while the count stood still. Two of the ten (CD, CI) are about rule C's coordination collapse rather than about any acceptance — the 31–34 batch's "which edge does a gate read" now has a companion: *which normalization has already run on the citation?* One Layer-4 re-parse (9:97) was worked out in full and deliberately not applied. See *Rules CA–CJ and the Purgatorio 6–10 Read* below and [`CORRECTIONS.md`](CORRECTIONS.md).
  - **Rules BW–BZ + Purgatorio 1–5 read (2026-08-16)**: four deterministic rules, 2 Layer-4 rows and 1 case-annex row, scoring **506 → 481 (−25, −4.9%)** with zero model calls; Purgatorio 1–5 itself 14 → 10, and `pytest` **351**. The first batch outside Inferno and the smallest of the series. Its finding is **rule ordering for the third batch running, and this time inside `derive_unit`**: the predicate census walks `conj` chains *before* the pass that adds argument-bearing verbs, so a conjunct of a verb reached only by that pass was never promoted (rule BZ, purgatorio 4:45). Two candidate rules were censused at **1** each and dropped — the comparison headed by its own marker, and the copular subject/complement exchange — which is the batch's second lesson: a census of one is still a census. See *Rules BW–BZ and the Purgatorio 1–5 Read* below and [`CORRECTIONS.md`](CORRECTIONS.md).
  - **Rules BO–BV + Inferno 31–34 read (2026-08-16)**: eight deterministic rules, 15 Layer-4 rows, 2 Layer-2 rows, 1 Layer-3 span and 1 case-annex row, scoring **541 → 506 (−35, −6.5%)** with zero model calls; Inferno 31–34 itself 37 → 16, and `pytest` 342. The batch's finding is that the *aux*-normalization the derivation has done since rule AM was missing from nine acceptance rules' own gates — 53 arguments corpus-wide hang on an auxiliary rather than on the verb carrying the tuple — plus a rule-ordering loss (rule D was silencing rule AI's other half) and the series' first **declined mirror leg**, measured at −6/+0 and dropped because its only evidence is a Layer-3 span and Layer 3 is over-inclusive by design. Two candidates censused and dropped. See *Rules BO–BV and the Inferno 31–34 Read* below and [`CORRECTIONS.md`](CORRECTIONS.md).
  - **Fourth `--fix` round (2026-08-16)**: run by the user **ahead of the read series**, which the series' plan had deferred it behind. **650 → 541 (−109, −16.8%)**, 0 hard, `pytest` 326; units **443 → 388** (55 cleared, 38 improved, **0 regressed, 0 newly flagged**); per-unit yield **0.246**, the first rise of the series. It decided the two prompt questions it was queued to test, and **decided both against the prompt**: the subject branches moved at the round average (`extra_arg_subject` −12.7%, `missing_arg_subject` −10.0%), not the large drop `_CONV_SUBJECT`'s three diagnoses predicted, and `missing_tuple_nominal`'s rewritten *question* moved 18 → 16 — Phase 5w's law survives a question rewrite, not just convention prose. Both buckets are now read-work. `missing_arg` (−28.3%) carried the round, `extra_tuple_adjective` went **7 → 0**. See *Fourth User-Run `--fix` Round* below.
  - **Rules BJ–BN + Inferno 26–30 read (2026-08-15)**: five deterministic rules, three legs added to rules already in the checker, 10 Layer-4 rows and 1 Layer-2 row, scoring **691 → 650 (−41, −5.9%)** with zero model calls; Inferno 26–30 itself 23 → 11. The batch's finding is that **a rule can be right and simply never reach the check that reports the position** — rule AQ has merged `cop`/`aux` citations since the 11–15 batch, but only inside `_classify_divergence`, while the membership check runs before it on the raw row. Its largest mover, rule BJ (−21), is the adverb-preposition cluster the Layer-4 prep-stack normalization deliberately deferred in 2026-08-14 as "a Layer-2/4 tension to decide separately if it ever matters": censused at 147 and settled at Layer 5 without touching Layer 4. Two rules are net zero on purpose (BN and rule AN's clause-head leg), and one Layer-2 correction costs a position. See *Rules BJ–BN and the Inferno 26–30 Read* below and [`CORRECTIONS.md`](CORRECTIONS.md).
  - **Rules AZ–BI + Inferno 21–25 read (2026-08-15)**: nine deterministic rules, 20 Layer-4 rows and 5 Layer-2 rows, scoring **834 → 691 (−143, −17.1%)** with zero model calls; Inferno 21–25 itself 44 → 16 — the largest batch of the series so far. Three of the nine are again mirror legs (AZ of rule R, BD of AW, BH of rule M), but the batch's new finding is **rule BB**: rule V was not missing a direction, it was written to pop *one* citation out of a map where a coordinate subject supplies three, and rule C then collapsed the survivors back onto the position it had just accepted. Two censused rules were dropped (the elided speech verb's `missing_tuple`, and result-clause `ccomp` at population 2), and a `dep.subject_agreement` refinement was measured at 12 new Layer-4 soft violations and deferred. See *Rules AZ–BI and the Inferno 21–25 Read* below and [`CORRECTIONS.md`](CORRECTIONS.md).
  - **Rules AU–AY + Inferno 16–20 read (2026-08-15)**: five deterministic rules, 25 Layer-4 rows and 1 Layer-2 row, scoring **888 → 834 (−54, −6.1%)** with zero model calls and **zero newly-flagged positions**; Inferno 16–20 itself 47 → 31. Three of the five are *mirror legs* of rules the checker already had (AV of `_aux_of_derived_predicate`, AW of AB, AY of `_elided_copula_nominal`), which is the batch's finding: a checker rule written for one direction of a labeling convention leaves the other direction reported. One censused rule was measured and **dropped** (gapped-clause remnants, population 12 — rule AN's assignment is right and the LLM's omission is reading error). See *Rules AU–AY and the Inferno 16–20 Read* below and [`CORRECTIONS.md`](CORRECTIONS.md).
  - **Rules AM–AT + Inferno 11–15 read (2026-08-15)**: eight deterministic rules, 16 Layer-4 rows and 2 Layer-2 rows, scoring **963 → 888 (−75, −7.8%)** with zero model calls; Inferno 11–15 itself 37 → 17. Four of the eight are in `derive_unit` itself — the first batch where the read found the derivation *wrong* rather than silent. Plus the fix side's first subject-slot branches (`missing_arg_subject`, `extra_arg_subject`, together 29% of the residue), a rewritten `missing_tuple_nominal` question, and a `_fix_hint` bug. See *Rules AM–AT and the Inferno 11–15 Read* below and [`CORRECTIONS.md`](CORRECTIONS.md).
  - **Third `--fix` round (2026-08-15)**: **1094 → 963 (−131)**, the first round preceded by new checker rules, a sharpened prompt and a new Stage-2 class. `missing_arg_adverb` **83 → 28 (−66.3%)** confirms the `_CONV_ADVERB` prompt-defect diagnosis; the elided-speech and appositive-adjective clauses moved ~nothing. See *Third User-Run `--fix` Round* below.
  - **Layer-4 prep-stack normalization (2026-08-14)**: closed the stacked-preposition route — 161 clusters, 196 rows, Layer 5 **1094 → 1094 net zero** by design; `dante_corpus/skel.py` gained a `fixed`-under-`case` lemma aggregation so rules O/`prep_stack` read the normalized shape (3 new tests). The route's old "14 role_mismatch / 18 unattached" count was Phase-5j-era and already absorbed.
  - **Rule AG (Inferno 4–6 Read)**: Gated `conj` subject propagation on Layer-2 person/number agreement (`dep.subject_agreement` + `_finite_head_of`), scoring **1452 → 1409 soft (−43)** with zero model calls.
  - **Second `--fix` round (2026-08-14)**: First live pass of the `extra_arg_adjective` micro-prompt; **1409 → 1247 (−162)**, 0 regressed / 0 newly flagged. See *Second User-Run `--fix` Round* below.
  - **Rules AH–AL + Inferno 7–10 read (2026-08-14)**: Five deterministic rules, five Layer-2 mistags and eight Layer-4 retags, scoring **1247 → 1091 (−156, −12.5%)** with zero model calls. Plus three prompt defects fixed and one new Stage-2 class (`missing_arg_adverb`), which move nothing until the next `--fix` round. See *Rules AH–AL and the Inferno 7–10 Read* below and [`CORRECTIONS.md`](CORRECTIONS.md).

---

## Phase 6 Operating Principles & Architecture

Building on Phase 5's hard-won lessons, Phase 6 eliminates brute-force whole-unit regeneration in favor of targeted, cost-effective interventions:

### 1. Three-Stage `--fix` Hierarchy
Every flagged parse unit passes through three stages, cheapest first, under the same acceptance gate (0 hard violations, `_is_improvement`):
- **Stage 1 (Deterministic Auto-Repair)**: Runs before any model call.
  - **Tier A (No Reading Asserted)**: Label canonicalizations (`role_label` 7, `prep_stack` 4).
  - **Tier B (Corroborated Reading)**: Independent signal required (e.g., `null_subject` 31 gated on `dep.subject_agreement`). Verified and idempotent.
  - `--repair` is this stage executed in isolation.
- **Stage 2 (Class-Specific POS-Keyed Micro-Prompts)**:
  - Bypasses monolithic `SYSTEM_PROMPT`.
  - Sends a concise 20–30 line prompt specific to the violation class — **fourteen** of them, keyed by POS (`extra_tuple_adverb`, `extra_tuple_adjective`, `extra_arg_adjective`, `missing_arg_adverb`), by role (`extra_arg_subject`, `missing_arg_subject`), by predicate POS (`missing_tuple_nominal`), or by class alone (`role_mismatch`, `extra_arg`, `missing_arg`, `extra_tuple`, `missing_tuple`) — plus two added 2026-08-18 (§28) that each stand in for a **pair** of rows rather than one: `arg_slot`, where a `missing_arg` and an `extra_arg` name the same slot and `_split_slot_conflicts` merges them into one question, and `dual_role`, rule EG's artifact-internal contradiction.
  - Solves one question at a time and splices answers row-by-row, eliminating the all-or-nothing unit rejection penalty.
- **Stage 3 (Fallback Whole-Unit Regeneration)**:
  - Opt-in fallback for complex multi-violation interactions. Can be disabled with `--no-whole` for benchmarking.

### 2. Independence Rule
A question may name the predicate, the argument the LLM itself cited, and the role slot in dispute (what `_fix_hint` already disclosed), but **never** `derive_unit`'s own derived argument position.

### 3. Evaluation at Subclass Granularity
- Never evaluate passes or rules by overall pass averages alone.
- Measure changes at `_violation_subclass` granularity against their specific target population.

### 4. Per-Position Manual Reads as Primary Discovery Engine
- Aggregate statistics frequently misdiagnose checker silence as LLM error.
- Exhaustive position-by-position reads of small canto batches (Inferno 1 through 30, five at a time) uncover genuine checker silence (e.g., Rules V, W, X, Y–AF, AG, AH–AL) and upstream layer errors. The Inferno 7–10 read also found the reverse case: a defect in the *prompt* (`_CONV_ADVERB`'s omission licence) responsible for the single largest bucket in the residue, which no aggregate statistic had attributed to anything. The Inferno 11–15 read found a third kind: four defects in `derive_unit` itself (rules AM, AN, AT and rule AJ's missing directions), where the derivation was not silent but **wrong**.
- **As of 2026-08-15 the reads are a planned series covering all 100 cantos.** They were also declared to run *before* the next `--fix` round; the fourth round was run ahead of them on 2026-08-16 (§12), so that clause has lapsed and the series continues against the base the round left. See *The Read Series* below for the reasoning, the schedule, and the eight-step per-batch procedure. `skel/read.py` is the tool; `--check` names a position, `read.py` shows all five layers for its parse unit.

### 5. Immediate Cross-Layer Remediation
- Upstream defects in Layer 2 (`morph/`), Layer 4 (`dep/`), or the pronoun case annex (`case/`) discovered during audits must be corrected in the same session, re-validated, and documented in `*/CORRECTIONS.md`.
- **`*/CORRECTIONS.md` records hand-applied corrections only** — upstream retags, gated-script
  rewrites, checker/derivation rules, and the shapes deliberately left alone with the reason. A
  `--fix` round is LLM regeneration of the artifact, not a correction to it: rounds are written up
  in *Phase 6 Implementation & Results* here and summarized in the root [`../PLAN.md`](../PLAN.md),
  and never in `CORRECTIONS.md`.

### 6. Strict Division of Labor
- **Assistant**: Conduct per-position audits, implement deterministic checker/derivation rules, develop Stage 2 micro-prompts/hints, and maintain upstream layer data.
- **User**: Execute parallel `--fix` regeneration passes (`make -C skel fix`) and commit updated TSVs.
- A read batch is therefore entirely the assistant's, start to finish: the eight steps in *How to Read a Batch* need no model call and no user action, and a batch is not finished until its write-ups and count updates are in.

---

## Phase 6 Implementation & Results

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
zero model calls; Inferno 7–10 itself went 37 → 17. Full write-up, with the evidence line for each
rule, in [`CORRECTIONS.md`](CORRECTIONS.md).

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
model calls; Inferno 11–15 itself 37 → 17. Full write-up, with the evidence line for each rule and
the variant measurements, in [`CORRECTIONS.md`](CORRECTIONS.md).

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
model calls, **zero newly-flagged positions**; Inferno 16–20 itself 47 → 31. Full write-up, with
the evidence line for each rule and the rule that was censused and dropped, in
[`CORRECTIONS.md`](CORRECTIONS.md).

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
zero model calls; Inferno 21–25 itself 44 → 16. The largest batch of the series. Full write-up,
with the evidence line for each rule, the two rules censused and dropped, and the honest trades
the upstream retags make, in [`CORRECTIONS.md`](CORRECTIONS.md).

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
zero model calls; Inferno 26–30 itself 23 → 11. Full write-up, with the evidence line for each
rule, the rules censused and dropped, and the two deliberate net-zero trades, in
[`CORRECTIONS.md`](CORRECTIONS.md).

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
deliberately left alone. Round measurements live here, in *Phase 6 Implementation & Results*, and
in the root [`../PLAN.md`](../PLAN.md).

### 13. Rules BO-BV and the Inferno 31-34 Read (2026-08-16)

Per-position read of all **37** soft violations in Inferno 31-34. **541 → 506 (−35, −6.5%)**,
zero model calls; Inferno 31-34 itself 37 → 16 (31: 20 → 8, 32: 8 → 5, 33: 4 → 2, 34: 5 → 1).
The first batch measured against a base a `--fix` round has moved, which is the cost §12 recorded:
these numbers are not comparable with the AG-BN series', because the easy positions of every class
round 4's prompts cover are already gone. Full write-up in [`CORRECTIONS.md`](CORRECTIONS.md).

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
write-up in [`CORRECTIONS.md`](CORRECTIONS.md).

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
10: 10 → 7). Ten rules, the largest count of any batch. Full write-up in
[`CORRECTIONS.md`](CORRECTIONS.md).

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
15: 6 → 5). Full write-up in [`CORRECTIONS.md`](CORRECTIONS.md).

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
20: 5 → 3). Full write-up in [`CORRECTIONS.md`](CORRECTIONS.md).

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
25: 9 → 11). Full write-up in [`CORRECTIONS.md`](CORRECTIONS.md).

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
30: 8 → 7). Full write-up in [`CORRECTIONS.md`](CORRECTIONS.md).

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

## The Read Series — read the whole corpus (decided 2026-08-15; two rounds ran inside it)

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
write-up in [`CORRECTIONS.md`](CORRECTIONS.md).

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
Full write-up in [`CORRECTIONS.md`](CORRECTIONS.md).

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
Full write-up in [`CORRECTIONS.md`](CORRECTIONS.md). Eight rules is the second-largest count of
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
of the Paradiso series, read in one session — following *How to Read a Batch* below. **261 → 245
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

Per-position read of all **21** soft violations in Paradiso 21-25, following *How to Read a Batch*
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
read series**, taken in one session — following *How to Read a Batch* below. **234 → 213 (−21,
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
it for nothing. Of the five verdicts *How to Read a Batch* offers, **prompt defect is the only one
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
all other layers 0/0, `skel/*.tsv` untouched. Full write-up in [`CORRECTIONS.md`](CORRECTIONS.md).

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
find it. The verdict procedure in *How to Read a Batch* is unchanged and still applies to every
position a note names — and the five verdicts are what the notes should be censused against, since
a note that repeats across dozens of positions is a prompt defect and a note that appears once is
noise.

**4. Collection is opt-in and per process.** `make -C skel fix` still does not pass `--log`, and
that standing decision is untouched (see *After the Sixth Round*): pass `--log skel-<canticle>.log`
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
the prompt alone. See *After the Sixth Round* below for what it settled and what it left.

Per canto, get the current numbers with `uv run skel.py <canticle> --check -c <n>` from `skel/`.

### How to Read a Batch

The procedure below is what produced rules AG through EA. Steps 4–7 are the part that must not be
skipped: a rule that is not censused, measured, tested and written up is not a rule.

1. **List the batch.** `uv run skel.py <canticle> --check -c <n>` for each canto, from `skel/`.
   Record the per-canto counts and the class/role breakdown (`--stats`) before touching anything —
   this is the batch's baseline.
2. **Read every position, in parse-unit order,** with `uv run read.py <canticle> <canto> <line>`
   (`skel/read.py`, added 2026-08-15). It prints the unit's source, Layer-2 morphology + the `case`
   annex, Layer-4 deprels, Layer-3 NP spans, and both Layer-5 readings — the artifact rows and
   `derive_unit`'s — which is exactly the pair `--check` diffs. Never diagnose a position from the
   violation line alone.
3. **Give every position one of five verdicts.** The verdict decides where the fix goes, and
   mixing them up is how earlier phases wasted rounds:
   - **checker silent** — Layer 4 records something the derivation cannot express, and the reading
     is right → an *acceptance* rule in `_classify_divergence`;
   - **derivation wrong** — the derivation contradicts the tree it reads, or invents structure →
     a fix in `derive_unit` (rules AM, AN, AT are of this kind);
   - **upstream wrong** — Layer 2 or Layer 4 mis-tagged the line → an upstream retag, applied in
     the same session (see *Operating Principle 5*);
   - **prompt defect** — the corpus's own instructions caused the reading (`_CONV_ADVERB`'s
     omission licence was worth 82 positions) → Stage-2/convention work, which moves nothing until
     a round runs. **This is the only verdict of the five that leaves no rule behind to be
     measured**, so it is the one to reach for last: the Paradiso 26–33 batch found that paradiso
     23:10, written up as `_CONV_ADJUNCT` work three batches earlier, was checker silence that rule
     EB took for nothing. Before assigning a position to the prompt, ask whether an existing rule's
     gate is one column away from taking it;
   - **genuine reading disagreement** — leave it flagged, and record the shape so a later batch can
     recognise a population.
4. **Census the shape corpus-wide before writing a rule.** A one-line script over
   `api.cantos()` counting the structural pattern (`orphan` deprels, argument children of a
   `cop`, `appos` on an argument, …). One instance is not a population; a rule whose census is
   0 is dropped, and several have been.
5. **Measure every rule on its own,** by full-corpus violation diff — not by the total alone:
   ```bash
   uv run skel.py inferno purgatorio paradiso --check | grep '\[tag\]' | sort > after.txt
   diff before.txt after.txt          # what it removed AND what it newly flagged
   ```
   Keep a rule when it is net negative, **or** when it makes the derivation provably more correct
   even at a cost (rule AM: −15/+22). Record such a trade explicitly in `CORRECTIONS.md`; the count
   is not the measure, the correctness of the parse is. Try variants and keep the numbers: rule
   AN's slot assignment was measured four ways.
6. **Pin every rule with a test, and mutation-check it.** Add to `tests/test_skel.py` a fixture
   built from the evidence line, one test that the rule fires and one that a near-miss still gets
   flagged. Then break the rule in the source and confirm the test fails — a test that passes with
   the rule removed pins nothing.
7. **Apply upstream retags with a gated script**, never by hand: assert the word at each
   `(line, token)` before rewriting the row, then re-run `morph`/`np`/`dep`/`case --check` (all must
   stay 0) and `pytest`. Watch CRLF hygiene (see the root PLAN's *Standing Disciplines*).
8. **Write it up in the same session**: the layer's `CORRECTIONS.md` for each layer touched, a
   numbered subsection in this file's *Phase 6 Implementation & Results*, the rule catalogue in
   [`README.md`](README.md), and the counts in both PLAN files. `CORRECTIONS.md` records
   corrections that were *applied* — see the root PLAN's *Standing Disciplines*.

### The Seventh `--fix` Round — what is on the scale (the user's to run)

**Base: 0 hard, 224 soft** (174 from the sixth round + rule EG's 50), `pytest` 511, all other layers
0/0. Run it the usual way — `make -C skel fix`, 3-way parallel — and measure per *How to Measure a
`--fix` Round* below. Everything queued here was written 2026-08-18 (§28) and **moves nothing until
the round runs**.

1. **`dual_role` — a brand-new class with its own prompt, 50 positions.** Rule EG's population, and
   the first class since `missing_arg_adverb` to arrive with a question written for it
   (`_ask_dual_role`: *this token was given two roles for this predicate — which one is right, or
   `both` if it is a fused clitic*). It is the round's cleanest test, because the class did not exist
   when the artifact was written: **it has never been asked**. It is separable in the subclass table
   under its own name. Expect the answers to be *decidable* — 27 of the 50 are a nominal written as
   both `subj` and `obj` — so a small drop here would say something about the model, not about the
   prompt.
2. **`arg_slot` — the same-slot merge, 8 predicates / 16 positions.** Three rounds could not move
   these because neither half's question could. Also separable in the table. A round that clears
   several of them confirms the diagnosis in §28's finding 3; one that clears none says the
   disagreement is real and the two rows are the honest report of it.
3. **`_CONV_DATIVE`, rewritten** (§28 finding 4) — against `missing_arg obl:a` at **11**. Small
   population, so read the per-position result rather than the percentage.
4. **The splice guard changes what a round can accept**, and this is a caveat for the measurement,
   not a candidate: `_apply_missing_arg` now refuses to append a row that would put one token in two
   roles. So `missing_arg`'s accepted-splice rate may fall slightly, and that is the guard working.
   **A round must not be read as having "regressed" the class if `dual_role` stays flat while
   `missing_arg` moves less than the round average.**

**What is *not* on the scale.** `_CONV_ADJUNCT` is settled positive and stays as written;
`_CONV_SUBJECT` and `missing_tuple_nominal`'s question are settled negative and are read-work; the
read series is closed. Do not add convention prose for a shape the model reads wrong — six rounds
have measured that at the round average every time (§28 finding 4).

**Collect the field notes while the round runs** (§29, landed 2026-08-18). They cost nothing extra —
no call, no acceptance change — but only if `--log` is passed, one file per parallel process:
`uv run skel.py <canticle> --fix -m $(MODEL) --log skel-<canticle>.log`. This is the round's second
product, and the first one that can name a position no read batch would have reached.

**After the round**: re-measure per the procedure below, then the residue to look at is the subject
slot (62 of the 174 before rule EG) and whatever the `dual_role` class leaves — the first sample
there will be of *reading* error the LLM cannot repair with the contradiction pointed out to it.

### After the Sixth Round — what the round settled, and what was landed the same day

**The sequence this section used to set is spent.** It read: *read Paradiso in 5-canto batches, then
run one `--fix` round, none in between.* The reading half closed 2026-08-17 (§26) and the round ran
2026-08-18 (§27). Both prompt candidates are decided — `_CONV_ADJUNCT` positive at −52.6% on the
shape its prose names, `_CONV_DATIVE` negative at −8.3%, and the second of those turned out to be a
wording defect rather than a verdict on the shape (§28 finding 4).

**The residue's shape had changed, and the three things that followed from it** — the first two are
**done** (§28, 2026-08-18), the third is the standing route:

1. **DONE — rule EG, the dual-role check**, plus the `_apply_missing_arg` splice guard that stops a
   round writing another one. Census 56, 7 licensed by rule AL, base 174 → **224**.
2. **DONE — the `arg_slot` merge**, the same-slot pair asked once instead of twice (8 predicates,
   16 positions), and `_CONV_DATIVE` rewritten to name the slot its class actually asks about.
3. **The subject slot, 36% of everything the round left**: `extra_arg_subject` 24 +
   `missing_arg_subject` 19 + the 19 `role_mismatch` rows with `subj` on one side = **62 of 174**,
   and 13 of those mismatches are `subj` ↔ `obj` in both directions on one predicate. Round 4
   decided `_CONV_SUBJECT` negative and converted this to read-work; the read series then read it
   and left it standing. So it is neither prompt-work nor unread — it is the corpus's genuine
   reading disagreement over Dante's inversion. The `arg_slot` merge covers 14 of the 62; the rest
   is honestly reported and may simply stay that way.

**The next step is the seventh round, and it is the user's** — see *The Seventh `--fix` Round* above
for what is on its scale. The ordering constraint that governed the whole read series still holds in
its general form: **land the checker work first, then run the round, so the round's per-class numbers
measure the prompt rather than a moving base.**

**A round is worth running even with an unchanged prompt — but know what it buys.** §21 measured
that: −15.1% at a base fifteen rule batches lower, 0 regressed / 0 newly flagged, which shows the
rules and the LLM take largely disjoint residue. What such a round does *not* buy is an answer to
any question, and it moves the base under every rule measured afterwards. So the recovery is real
and can be collected at any time; the ordering constraint is about *evidence*, not about yield.

**`make -C skel fix` still does not pass `--log`, and that omission is deliberate** (proposed after
round 4 and declined, 2026-08-16): a round's rejected candidates are not kept unless the round is
launched with `--log` by hand. A round is measured by **violation diff, not by driver telemetry** —
the worktree diff in *How to Measure a `--fix` Round* is what §12's table was built from.

**The other half of that 2026-08-16 decision is reversed (2026-08-18): `_print_fix_summary`'s
per-class `calls / removed / per call` table is now appended to `--log`**, under a
`=== fix summary ===` header, so a `--log` file is the round's whole record — what was asked, what
came back, and what the asking cost. The reason it was declined was that the violation diff
reconstructs a round's numbers afterwards; the seventh round showed what it does *not* reconstruct.
Inferno's table read **TOTAL 84 calls / 16 removed / 0.190**, and split by class it was
`dual_role` **10 calls / 11 removed / 1.100** against **74 calls / 5 removed / 0.068** for
everything else, with `_whole` at **32 calls / 0 removed** — 38% of the round's call budget, and
the most expensive call in it, for nothing. The violation diff sees the 16 positions and none of
that. **A call count is not recoverable from the artifact, so it has to be written down while the
round runs.** Still not summed across the three parallel processes: each writes its own file, and
the three tables are added up by hand.

---

## Active & Open Routes

Populations are quoted at **base 541** (after the fourth `--fix` round) where they have been
re-measured, and marked with their older base otherwise; the BO–BV through DE–DF rules and the
fifth `--fix` round, the DG–EF rules, the sixth `--fix` round and rule EG have since moved the base to **224** (174 of them divergence, 50 rule EG's new class), so a route's number is a starting point
for a re-measure, not a current count. These are shapes the reads have
already named but not settled; a batch that runs into one of them should fold it in rather than
open a new route.

### Open Assistant-Side Routes

*(populations at base 541 unless noted)*

- **The three routes the sixth round opened come first** — the artifact-internal dual-role check
  (census 56, 49 unlicensed), the same-slot question merge (8 predicates / 16 positions) and the
  subject slot at 62 of 174. All three are written up in *After the Sixth Round* above, in the order
  they should be taken.
- **The 49 positions Inferno still holds** (75 at base 541, 54 at base 213) are the read batches'
  own residue *after* three `--fix` rounds have been over them, which makes them the most direct
  sample there is of what a round leaves behind. All 100 cantos are read, so these are reading
  disagreement rather than unread material.
- **Ask what *else* a rule's evidence covers** (2026-08-16, from the Purgatorio 21–25 batch). Rule
  BA reads two derived subjects as two collapsed clauses and concludes only about the subject
  slot; rule CW follows the same evidence to the rest of the elided clause, for seven positions.
  When a rule accepts an argument *because* of some structural fact, ask which other arguments
  that fact reaches.
- **Ask which *edge* a gate reads** (2026-08-16, from the Inferno 31–34 batch; a fourth instance
  in the Purgatorio 21–25 batch, rule CY). Rule BP found nine
  acceptance rules comparing Layer 4's raw head to the predicate's position while `derive_unit`
  had been normalizing through `aux`/`cop` since rule AM. Every rule that reads a deprel edge —
  head, child, or marker — is a candidate for the same gap.
- **A comment that delegates to a later branch is a claim the code must keep** (2026-08-16, from
  the Purgatorio 21–25 batch, rule CV). `subject_agreement`'s 1/2-plural exclusion named "the
  conjunct branch below" as the judge of coordinations and then returned before it; five more
  exclusions in the same function returned "undecidable" for a feature they had nothing to say
  about. When a gate excludes a pair, ask **which feature** it is excluding and what it stops.
- **A mirror leg is not owed acceptance** (2026-08-16). Rule BR's mirror measured −6/+0 and was
  dropped: the derived side rests on Layer 4 asserting both positions, the given side only on a
  Layer-3 span, and Layer 3 is over-inclusive by design. Measure the mirror every time; land it
  only when its evidence is as strong as the leg it mirrors.
- **Ask which checks run *before* a rule** (2026-08-15, from the Inferno 26–30 batch). Rule AQ was
  correct and complete inside `_classify_divergence` and simply absent from the membership check,
  which runs first on the un-normalized row. Every acceptance rule keyed on a citation is a
  candidate for the same gap.
- **An `iobj` ↔ `obl:a` equivalence, censused and dropped** (inferno 28:76, "fa saper **a' due
  miglior** da Fano"). The LLM cites the Layer-3 NP head and the derivation the Layer-4 head, and
  the roles differ too, so both rule AI and rule N would have to be widened; the role pair occurs
  **0** times as a role_mismatch corpus-wide. Left standing — and it is a second instance of the
  NP-head-in-a-different-role route below.
- **The adverb-preposition clusters — CLOSED by rule BJ (2026-08-15)**: the 40 clusters the
  prep-stack normalization deliberately excluded because Layer 2 calls their opening word an
  adverb are censused at 147 and settled at Layer 5, without a Layer-4 rewrite (−21).
- **Check the mirror leg of every rule you write** (2026-08-15, from the Inferno 16–20 batch;
  three more legs in the 21–25 batch, worth 37 positions). When a rule accepts "the LLM names X
  where the derivation names Y", ask what happens when the derivation names X and the LLM names Y.
- **Check the *plural* too, and the rule's place in the pipeline** (2026-08-15, from the Inferno
  21–25 batch). Rule V popped one `subj` out of a map a coordinate subject fills three times, and
  the collapse that runs after it put the survivors back on the accepted position. Two questions
  for every rule: what does it do when the shape supplies **several** citations, and does it test
  a raw citation that a later normalization step will rewrite?
- **Subject vs. predicate nominal under a copula** (inferno 19:85 *«Nuovo Iasón sarà»*, 20:77
  *«ma Mencio si chiama»*): Layer 4 calls the single nominal `nsubj`, the LLM calls it the
  complement of an elided pro-drop subject, and the line does not decide. Feeds the
  `extra_arg subj ∅ (0,0)` bucket; census it there rather than as a route of its own.
- **A relative pronoun's subject named by its antecedent** (inferno 16:94 *«quel fiume c'ha
  proprio cammino»*): the derivation cites the relative `c'`, the LLM cites `fiume`. An acceptance
  rule keyed on `skel.antecedent` is plausible — **census it before writing it**.
- **Accusative-and-infinitive — CLOSED by rule BI (2026-08-15)**: censused at 10 (inferno 5:48,
  16:104, 22:31, 23:119, 26:78; purgatorio 18:24; paradiso 15:112, 19:39 …) and all 10 taken. The
  tree asserts both edges, so neither reading is wrong.
- **An argument named by its Layer-3 NP head against a clause the derivation cites by its clause
  head** (inferno 13:52, *«Ma dilli chi tu fosti»*): rule AI merges these only when the *role*
  matches, and here the LLM's `obj` on `chi` faces the derivation's `ccomp` on `fosti`. Measure how
  many `extra_arg` positions are NP-head-equivalent to a derived argument in a different role
  before extending AI — one instance is not a population.
- **`onde` is tagged five ways in Layer 2** (conjunction 56, pronoun 43, adverb 23, noun 11,
  relative pronoun 7). The noun rows are right; the 129 relative ones split three ways by nothing
  visible. Its Layer-5 cost is now paid by rule BM, which accepts a conjunction-tagged filler in
  an oblique slot (inferno 14:54 among them, −11), so this is a Layer-2 quality route rather than
  a violation route. A measured vocabulary pass, not a per-line edit — see
  [`../morph/CORRECTIONS.md`](../morph/CORRECTIONS.md).
- **Rule AN's two unresolved gapping clusters** (purgatorio 25:3, 27:108): 2-slot ambiguities that
  only word order settles, and Italian inverts word order freely. Left standing deliberately.

- **`missing_arg_adverb` residue (21)**: the survivors of the `_CONV_ADVERB` repair, now also of
  `_CONV_REPEATED` (24 → 21 in round 4). Two prompt repairs have had their turn, so this is a
  per-position read — the first thing to establish is whether these are locative adverbs the model
  still omits or a different shape the branch is over-collecting.
- **`missing_tuple_nominal` (16) — read it, do not write for it.** Round 3 gave it convention
  prose and a hint (−7.7%), round 4 a rewritten *question* (−11.1%), and its positions have been
  substantially the same set throughout. That is the strongest evidence in the series that a class
  can be genuine reading disagreement, and every prompt surface has now been tried on it.
  (Its old companion `extra_tuple_adjective` is **closed**: rules AU/AY/AZ took it 13 → 7 and
  round 4 took it 7 → **0**.)
- **`extra_arg subj` (96, of which `∅ (0,0)` 22) and `missing_arg subj` (54)**: still the two
  largest buckets, and now **read-work by decision** — `_CONV_SUBJECT`'s three diagnoses
  (postverbal subjects, proclitics read as subjects, coordination-shared subjects) were measured
  in round 4 at −12.7% / −10.0%, the round average, which is the branch *A Fourth `--fix` Round*
  named for "they are genuine reading disagreements". Start with the `∅ (0,0)` half, where the
  derivation found a genuine overt subject, often long-distance (e.g. Inferno 9:20, where `alcun`
  at 21.4 is the subject of `incontra`).
- **`role_mismatch` `xcomp` vs `obl` (7) and `obj` ↔ `subj` (28 across both directions)**: the two
  dominant mismatch shapes. The `obj`/`subj` swap is a symmetric pair, which suggests one
  systematic cause rather than scattered slips. Inferno 9:41 and 9:72, both fixed in `dep/` in the
  Inferno 7–10 session, were instances — worth checking whether the rest are too.
  - **`role_mismatch` is the only large class with no branch of its own, and the only
    argument-level class whose prompt omits `_CONV_SUBJECT`** (noted 2026-08-16 from round 4's
    shape). Its system block is `_ASK_HEADER` + `_CONV_ROLES` + `_CONV_RELPRON`, while **37 of its
    73 positions involve `subj` on one side or the other** (28 of them the symmetric
    `obj` ↔ `subj` pair) — and `_CONV_SUBJECT` states exactly the two rules that decide that pair
    (a postverbal subject is still the subject; an unstressed proclitic is never one). The gap is
    structural and cheap to close.
    **Do not close it yet.** Round 4 measured `_CONV_SUBJECT` on the buckets it was written for at
    the round average (−12.7% / −10.0%), so the same prose is unlikely to move a third class, and
    adding a prompt that the last round's evidence says will not work is the move that round
    argued against. **Read the 28 symmetric positions first**; their symmetry is the reason to
    expect a single cause, and if the read finds one, it is as likely to be a checker or `derive_unit`
    rule as a prompt branch.
- **An `advcl` the LLM reads as a complement** (inferno 27:101 "fa **sì come** … getti", 29:63
  "**secondo che** i poeti hanno per fermo", 30:59 "non so io **perché**"): three shapes in which
  the LLM promotes an adverbial clause, a parenthetical, or a bare interrogative to the matrix
  verb's `ccomp`. Layer 4's `advcl` is right in all three; recorded so a later batch can decide
  whether they are one population.
- **Quoted speech attached as `parataxis` (Inferno 8:81)**: `«qui è l'intrata», gridò` — Layer 4
  hangs the quotation as `parataxis`, which is a clause-head deprel but not an argument deprel, so
  the derivation never makes it the verb's `ccomp` while the LLM (rightly) does. A
  `parataxis`→`ccomp` acceptance rule for verbs of speech is plausibly large; **measure the
  population before writing it.** Its neighbour, the *result* clause read as `ccomp`
  (`sì … che`, inferno 22:84), was censused at **2** and dropped.
- **`dep.subject_agreement`'s *coordinated subject* exclusion (12 positions)**: restricting it to
  the number test — a coordination of nominals is third person however many members it has — was
  implemented and measured, and takes `dep --check` from 0 to 12 soft. Each is a real Layer-4
  question (inferno 2:33, 8:28, 21:121, 25:36; purgatorio 4:102, 5:82, 10:62, 23:113, 29:37;
  paradiso 14:125, 19:12, 31:96); reverted rather than landed against the 0-soft invariant. It is
  what keeps rule AG from dropping the wrong inherited subject at inferno 24:125.
- **Depictive adjectives under bare `obl` — CLOSED by rule AZ (2026-08-15)**: censused at 43 and
  worth −13 as a role-mismatch acceptance rather than a derivation change (inferno 10:72
  `supin ricadde`, 21:46, 23:17, 24:115).
- **Relative `che`/`ch'`/`onde` tagged `conjunction` (247 tokens)**: unblocked only by an
  independent model read of the `case` annex over the 243 positions the retag would add. That is a
  build round, not an edit — see [`../morph/CORRECTIONS.md`](../morph/CORRECTIONS.md).
- **Attributive vs. Predicative Adjectives — the adjective subclass is CLOSED** (`extra_tuple`
  stands at 14 overall; `extra_tuple_adjective` is **0** after round 4, down from 37):
  True reading disagreements with no `cop` edge (e.g., Inferno 2:109 *"non fur mai persone ratte /
  a far lor pro"*) were what round 3's appositive clause failed to move; rules AU/AY/AZ and round
  4 between them took the class to zero without the read it was queued for. The 14 remaining
  `extra_tuple` positions are a different, unbranched population.
- **`extra_arg_adjective` residue (19; `extra_arg xcomp` is 35)**: three rounds have now each taken
  a couple of positions (−20.0%, −3.9%, −5.0%), which is itself evidence that the residue is
  genuine reading disagreement rather than prompt weakness. Per-position read to settle it.
- **Adverbs Promoted to Predicates (2 `extra_tuple_adverb` remaining, down from 33)**:
  - Effectively closed by the Stage 2 micro-prompt. Read the final 2 positions to decide whether any residue warrants prompt tweaks or checker acceptance.
- **Stacked Prepositions in Layer 4 — CLOSED (2026-08-14)**: 161 multiword-preposition clusters
  normalized to the UD shape (opening word `case`→ nominal, later members `fixed`→ opening word),
  Layer 5 1094 → 1094 net zero; the old 14-role_mismatch count was Phase-5j-era and already
  absorbed by rules O/`prep_stack`. The standing obl-vs-obl residue is 3 genuine disagreements
  (inferno 14:103, purgatorio 32:156, paradiso 32:57). See
  [`../dep/CORRECTIONS.md`](../dep/CORRECTIONS.md) and [`CORRECTIONS.md`](CORRECTIONS.md).
  Its one deliberate leftover — the 40 adverb-prep clusters (`dentro a`, `dinanzi a`, `dietro a`,
  `intorno a`, `fuor di`, `infino al` …) Layer 2 tags `adverb`, excluded from the rewrite as "a
  Layer-2/4 tension to decide separately if it ever matters" — **did** matter, and was settled at
  Layer 5 by rule BJ (2026-08-15, censused at 147, −21) without a Layer-4 rewrite.
- **`missing_arg obl` Sample Audit (40 standing, down from 128)**: the adverb bucket that dominated
  it is branched and largely repaired, and `_CONV_REPEATED` addressed the duplicate-slot half of it
  in round 4 — `missing_arg` as a whole fell 28.3%, the round's largest contribution, while its
  branched adverb sibling fell only 12.5%, which is the attribution. The read series will walk
  these positions in batch order anyway, so this is no longer a separate route — fold what it finds
  into the batch that covers it.

---

## How to Measure a `--fix` Round

1. Create a clean worktree at base HEAD:
   ```bash
   git worktree add <scratch>/base HEAD
   # Symlink generated src/ directories into worktree if needed
   ```
2. Run validation across all cantos in both trees:
   ```bash
   uv run skel.py inferno purgatorio paradiso --check
   ```
3. Diff at the **parse-unit** level (`dep.sentence_groups`):
   - Units flagged before / after.
   - Units improved / cleared.
   - Units that regressed or were newly flagged (must remain **0**).
4. Compute per-unit yield (violations removed ÷ units flagged before).
5. Output results broken down by `_violation_subclass`.
