## Handoff (2026-08-18) — resume here

> **Phase 7 is open, all structural outliers are closed, and divergence residue is 87.** Layer 5 stands
> at **0 hard / 87 soft** (all 87 standard argument divergence positions; 0 `dual_role`, 0 `extra_tuple`,
> 0 `missing_tuple`, 0 `argument heads no NP`), `pytest` **544**, every other layer 0/0. Phase 6's whole record —
> seven `--fix` rounds (2,084 → 160 with the reads), the nineteen-batch per-position read of all 100 cantos,
> rules AG–EH, the routes it closed and its ten transferable findings — is in [`skel/PHASE6.md`](skel/PHASE6.md).
> The current plan is [`skel/PLAN.md`](skel/PLAN.md); the eighth round is **§P1**, rule EI is **§P2**, the ninth round
> is **§P3**, the refusal census audit is **§P4**, the two systematic failure shapes is **§P5**, the final
> `dual_role` resolutions is **§P6**, the seven outlier positions is **§P7**, the tenth round is **§P8**,
> Round 10 log audits & driver fix is **§P9**, the first read census is **§P10**, the second read census is **§P11**,
> the third read census is **§P12**, and the fourth read census is **§P13**.
>
> **Phase 7 is: drive soft to 0, and when a fix fails, find out why.** The fourth read census resolved
> 4 positions across clause arguments (**91 → 87**), the third read census resolved 4 positions in Paradiso
> (**96 → 91**), the second read census resolved 7 positions (**104 → 96**), the first read census resolved
> one Layer-4 retag and dropped 6 spurious argument positions (**112 → 104**), Round 10 log audits resolved
> one Layer-4 retag and dropped 3 spurious rows with driver fix (**116 → 112**), the tenth round went
> **119 → 116** on **106 calls** (45.3% refusals), the ninth round went **150 → 140** on **135 calls**, the
> refusal census audit resolved two upstream Layer-4 attachment errors (**140 → 137**), the systematic failure
> shapes resolved the 8 `missing_tuple_nominal` positions and added a subject splice guard (**137 → 129**),
> the final 3 `dual_role` positions were cleared (**129 → 126**), and the seven structural outlier positions
> were resolved (**126 → 119**, inferno 26, purgatorio 28, paradiso 33).
>
> **What the rounds & failure analyses settled, question by question**:
>
> - **All structural outliers and internal contradictions are 0**: `dual_role` (0), `extra_tuple` (0), `missing_tuple` (0), `argument heads no NP` (0).
> - **The refusal census is fully audited.** 38 positions read across `extra_arg`, `extra_arg_subject`, `missing_arg`.
>   2 upstream Layer-4 errors were corrected (−3 soft), 1 single-instance shape dropped, and 35 reading disagreements confirmed.
> - **Two systematic failure shapes are settled**: `missing_tuple_nominal` prompt defect resolved across all 8 positions
>   (−8 soft: inferno 7:49, 8:52, 8:70, 10:19, 11:67, 24:72, 31:21; purgatorio 6:49), and `missing_arg_subject`
>   splice guard landed in `_apply_missing_arg` (544 tests passing).
>
> ---
>
> ### What the next session does
>
> 1. **The standing open routes** in [`skel/PLAN.md`](skel/PLAN.md) (copula/predicative nominals, coordination/coreference).
> 2. **Artifact-internal checks**: look for more checks of rule EG's shape.
> 3. **The standing populations**: `missing_arg_adverb` (7 in log, 21 censused), `extra_arg_adjective` (3 in log, 19 censused).
>
> **Not queued, deliberately**: prompt changes, widening field notes, or restructuring `dante_corpus/skel.py`.
>
> **Layer 5 is operating under Phase 7 with 0 hard / 87 soft violations** (all 87 standard argument
> divergence positions; all structural outliers and artifact-internal contradictions 0). Per canticle:
> inferno 26, purgatorio 28, paradiso 33. Checks: `dep --check` **0 hard / 0 soft**, `case --check` 0 hard,
> `skel --check` 0 hard / **87** soft, `np --check` 0/0, `morph --check` 0/0, `pytest` **544 passed**. The
> upstream layers were corrected batch by batch throughout the Phase 6 read series (~200 Layer-4 rows,
> ~40 Layer-2 rows, a dozen Layer-3 spans and a dozen case-annex rows, each re-validated in the same
> session) — see each layer's `CORRECTIONS.md` and [`skel/PHASE6.md`](skel/PHASE6.md) for the per-batch
> record. The `--fix` rounds touched `skel/*.tsv` only, so no other layer moved with them.

**Layer 4's stacked prepositions are normalized (2026-08-14).** 161 multiword-preposition
clusters (196 rows, 74 files) rewritten to the UD convention — opening word `case`→ nominal,
later members `fixed`→ opening word — closing the flat/chained shape lottery. Layer 5 measured
**1094 → 1094, net zero** (0 units cleared / newly flagged; one derived lemma flip at
purgatorio 31:26 by design); rules O/`prep_stack` read the normalized shape via a
`fixed`-under-`case` lemma aggregation in `dante_corpus/skel.py`. See
[`dep/CORRECTIONS.md`](dep/CORRECTIONS.md) and [`skel/CORRECTIONS.md`](skel/CORRECTIONS.md).

**Layer 4's agreement residue is closed (2026-08-14).** All 18 were re-read: one was a real
mis-attachment (purgatorio 26:147, Occitan `sovenha vos`), ten were taken by six new exclusions in
`dep.subject_agreement` — each measured corpus-wide first, and none of them touching a pair the
rule calls `"agree"` — and seven by hand-verified `AD_SENSUM`/`FOREIGN` flags in the Layer-2 `note`
column, the `NO_NP`/`CONT_NEXT` mechanism. Layer 5 rose **1091 → 1094 (+3)**, all three individually
attributable — the same honest trade the later rounds record. The rule was refined three more times
in 2026-08-16 (rules CR, CV and the per-conjunct person test) and `dep --check` has stayed 0/0. See
[`dep/CORRECTIONS.md`](dep/CORRECTIONS.md).

### Current State & Architecture Summary

- **Layer 5 (Phase 7)**: `--fix` runs in three stages: Stage 1 (deterministic auto-repairs, −73), Stage 2 (fourteen class-specific micro-prompts, keyed by POS, by role, by class alone, or — for `arg_slot` and `dual_role` — on a *pair* of rows), and Stage 3 (fallback whole-unit regeneration, **measured at 128 calls for 6 violations in round 7, switched off in round 8 with no shape lost, and now permanently off**). Ten user-run rounds so far: **2011 → 1452 (−559)**, **1409 → 1247 (−162)**, **1094 → 963 (−131)**, **650 → 541 (−109)**, **351 → 298 (−53)**, **213 → 174 (−39)**, **224 → 161 (−63)**, **160 → 154 (−6)**, **150 → 140 (−10)** and **119 → 116 (−3)**.
  - **Current plan**: Phase 7's operating principles, work queue, open routes and measurement procedures are in [`skel/PLAN.md`](skel/PLAN.md).
  - **Closed record**: Phase 6 — the seven rounds, the nineteen-batch read of all 100 cantos, rules AG–EH, the routes it closed and its transferable findings — is in [`skel/PHASE6.md`](skel/PHASE6.md). Phase 5 is in [`skel/PHASE5.md`](skel/PHASE5.md).
- **Latest Improvements** (the full chronology is in [`skel/PHASE6.md`](skel/PHASE6.md) §3):
  - **Fourth assistant-side read census (2026-08-18)**: **91 → 87 (−4, −4.4%)**; `pytest` **544**;
    4 positions resolved across clause arguments (`inferno 8:81`, `inferno 22:84`, `purgatorio 9:72`, `purgatorio 5:48`). See [`skel/PLAN.md`](skel/PLAN.md) §P13.
  - **Third assistant-side read census (2026-08-18)**: **96 → 91 (−5, −5.2%)**; `pytest` **544**;
    4 positions resolved in Paradiso (`paradiso 12:93`, `paradiso 28:20`, `paradiso 11:21`, `paradiso 21:5`). See [`skel/PLAN.md`](skel/PLAN.md) §P12.
  - **Second assistant-side read census (2026-08-18)**: **104 → 96 (−8, −7.7%)**; `pytest` **544**;
    7 positions resolved across `extra_arg` and `missing_arg` (`inferno 8:93`, `inferno 32:7`, `inferno 16:94`,
    `purgatorio 27:10`, `purgatorio 24:107`, `purgatorio 10:30`, `purgatorio 15:32`). See [`skel/PLAN.md`](skel/PLAN.md) §P11.
  - **First assistant-side read census on `extra_arg` (2026-08-18)**: **112 → 104 (−8, −7.1%)**; `pytest` **544**;
    one Layer-4 retag (`paradiso 7:25 virtù` `obl<-25.3 soffrire`), 6 spurious argument positions resolved (`purgatorio 30:59`,
    `purgatorio 10:60`, `paradiso 7:25`, `paradiso 14:136`, `paradiso 17:116`, `paradiso 3:59`). See [`skel/PLAN.md`](skel/PLAN.md) §P10.
  - **Round 10 log audits & driver fix (2026-08-18)**: **116 → 112 (−4, −3.4%)**; `pytest` 543 → **544**;
    one Layer-4 retag (`paradiso 11:127 pecore` `nsubj<-129.2 tornano`), 3 spurious argument rows dropped (`inferno 16:21`,
    `inferno 29:63`, `purgatorio 32:69`) where the model answered `drop` in the log, and driver `_find_arg_row` updated
    with single-role fallback. See [`skel/PLAN.md`](skel/PLAN.md) §P9.
  - **Tenth `--fix` round (2026-08-18)**: **119 → 116 (−3, −2.5%)**; 106 calls, 3 removed (0.028/call),
    **48 refusals (45.3%)**, **0 newly flagged, 0 regressed**; `pytest` **543**; `skel/*.tsv` only (2 files).
    `paradiso 1:81` cleared via `arg_slot` (−2: `fece subj`), `purgatorio 21:36` cleared via `missing_arg` (−1: `parve obl:a`).
    The refusal rate reproduced rounds 8 & 9's rates closely (45.3% vs 43.7% / 41.5%). Subject splice guard
    verified in production across all 8 `missing_arg_subject` calls. See [`skel/PLAN.md`](skel/PLAN.md) §P8.
  - **Ninth `--fix` round (2026-08-18)**: **150 → 140 (−10, −6.7%)**; 135 calls, 10 removed (0.074/call),
    **56 refusals (41.5%)**, **0 newly flagged, 0 regressed**; `pytest` **542**; `skel/*.tsv` only (8 files).
    The planted positive control at **purgatorio 9:97** cleared cleanly (both `extra_tuple` and `missing_tuple`
    removed). `arg_slot` calls dropped to 4 (all 4 refused 100% `keep`). `dual_role` cleared 3 more positions
    (6 → 3). The refusal census reproduced round 8's rates closely across all classes, confirming it as a
    settled reading list. See [`skel/PLAN.md`](skel/PLAN.md) §P3.
  - **Rule EI and the first refusal-census read (2026-08-18)**: **154 → 150 (−4/+0)**, `pytest`
    534 → **542**. `arg_slot`'s 8 predicates — the only class the model refused at **100% in two
    consecutive rounds** — read one by one with `read.py`. Two were checker silence, one was a
    Layer-4 mis-parse, one shape was censused at 2 and dropped, four are genuine reading
    disagreement: **three findings out of eight positions at zero model cost.** **Rule EI** takes
    the *floating quantifier* ("e **tutta quanta** … **faceva** dir", purgatorio 10:58; "e **son**
    … **tutti quanti**", inferno 31:32): Layer 4 hangs it on the noun as an adnominal, Layer 3
    enumerates it as an NP of its own, `SYSTEM_PROMPT` says cite a phrase's head — so the reading
    cites the quantifier and the derivation the noun. **Rule AI accepts this convention already**
    and declines only because its test is "both inside one NP span". Gated on the Layer-4 adnominal
    edge read through rule C's coordination collapse, a closed quantifier lemma list, and Layer 2
    calling the token an adjective/numeral/pronoun; censused at **53**. The same batch retagged
    **purgatorio 9:97** in Layer 4 («Era il secondo tinto più che perso» — the comparative standard
    had been made the root), on inferno 7:103's precedent, at **Layer-5 net zero** and recorded as
    such. See [`skel/CORRECTIONS.md`](skel/CORRECTIONS.md), [`dep/CORRECTIONS.md`](dep/CORRECTIONS.md)
    and [`skel/PLAN.md`](skel/PLAN.md) §P2.
  - **Eighth `--fix` round (2026-08-18)**: **160 → 154 (−6, −3.8%)**, the first round of Phase 7 and
    the first run `--no-whole`. 130 units flagged, 6 cleared, **0 regressed, 0 newly flagged**;
    `pytest` **534**; `skel/*.tsv` only. **Its result is the measurement, not the six positions**:
    142 calls at **0.042** each — below the pre-written floor of 12–20 — and **62 of them (43.7%)
    refusals**, so the standing 148 divergence positions would cost ~3,500 calls. **A ninth round is
    not queued.** The refusal census reproduced round 7's per class almost exactly (`arg_slot`
    **7 calls / 7 refused / 100% `keep`**, `missing_arg` 10 `none`, `extra_arg` 15, `extra_arg_subject`
    13), which makes it a settled reading list. `dual_role` held its lead at **8.3×** (0.250 vs 0.030)
    against round 7's 10.3× — the *ratio* survived while both terms fell, so §30 finding 1 is about
    evidence rather than novelty. `--no-whole` confirmed permanent (332 → 142 calls, no shape lost);
    `_CONV_DATIVE` held (`obl:a` 6 → 5); field notes 2 over 142 calls, closing §29. Two systematic
    failure shapes named: `missing_tuple_nominal` fails identically 9-for-9, and
    `missing_arg_subject` splices `extra_arg subj` rows in half its calls. Full tables in
    [`skel/PLAN.md`](skel/PLAN.md) §P1.
  - **The refusal split (2026-08-18)**: `no actionable answer` was two outcomes wearing one label.
    `_is_refusal` separates the model **standing by its reading** — every answer it gave is its
    class's own word for *leave this as it is* (`keep`/`none`/`both`/`yes`, or for `role_mismatch`
    the role the artifact already carries) — from a response the driver could not use. Counted as
    `refused:<class>` / `unusable:<class>` and printed as a **`refused` column** in the fix summary,
    which is written to `--log`. It adds no call, changes no prompt and moves no position; what it
    produces is the census that was being discarded — 57 of round 7's 332 calls — and a class that is
    all refusals is checker-side work rather than a prompt population. `pytest` **534** (11 new,
    mutation-checked at three sites). See [`skel/PHASE6.md`](skel/PHASE6.md) §31.
  - **Rule EH (2026-08-18)**: **161 → 160**, the seventh round's one concrete checker finding, found
    by the model refusing. Purgatorio 2:40's `sen` = `si`+`ne` written as `obl:si` **and** `obl:ne`
    of `venne` is rule AL/CM's licensed fused clitic; `_case_supports_role` sends every
    `obl:<marker>` role to the `ablative` slot whatever the marker says, so both obliques collided
    on one slot and rule CM's "the two supporting slot sets must differ" rejected them. Layer 2's
    fused lemma and the annex's slots share a separator and an order (`si+ne` /
    `reflexive+ablative`), so component *i* is slot *i*. Censused at **1 of 7**, kept on the rule-CY
    precedent, **−1/+0**, `pytest` **527**. See [`skel/CORRECTIONS.md`](skel/CORRECTIONS.md).
  - **Seventh `--fix` round (2026-08-18)**: **224 → 161 (−63, −28.1%)**; 182 → 131 flagged parse
    units (51 cleared, 9 improved, **0 regressed, 0 newly flagged**); per-unit yield **0.346**, the
    highest of the seven; `pytest` **521**; `skel/*.tsv` only. **The first round run with `--log`,
    hence the first with per-class call counts — and that table is the result.** The records belong to
    one class: `dual_role` **50 → 9 (−82.0%)** carried 40 of the 63, while the divergence residue
    alone went **174 → 152 (−12.6%)**, weaker than rounds 4–6. Per *call*, `dual_role` is **0.833**
    and everything else **0.081**. **30% of the round's calls ended in `no actionable answer`, and 57
    of those were the model explicitly refusing.** `arg_slot` decided at **0 of 7 calls, all `keep`**.
    `_CONV_DATIVE` rewritten is **positive** (`obl:a` 11 → 6, −45.5%). `_whole` cost **128 calls
    (38.6%) for 6**. Field notes **did not pay**: 5 over 332 calls, one of them real. Full tables in
    [`skel/PHASE6.md`](skel/PHASE6.md) §30.
  - **Rule EG (2026-08-18)**: the first check in this layer that reads the artifact *against itself* —
    one token filling two roles of one predicate, censused at 56 with 7 licensed by rule AL's fused
    clitic and **52 of the 56 on lines `--check` said nothing about**. It **raises** the count,
    **174 → 224 (+50)**, the honest trade rule AM records, and it is the question the model answers
    ten times better than any other. Landed with a splice guard in `_apply_missing_arg`, the
    `arg_slot` merge, and `_CONV_DATIVE` rewritten. See [`skel/PHASE6.md`](skel/PHASE6.md) §28.
  - **The read series, CLOSED (2026-08-17)**: all 100 cantos read position by position in nineteen
    batches, producing rules AG–EF at **zero model cost** — AG −43; AH–AL −156; AM–AT −75; AU–AY −54;
    AZ–BI −143; BJ–BN −41; BO–BV −35; BW–BZ −25; CA–CJ −33; CK–CO −21; CP–CT −18; CU–CY −21;
    CZ–DD −30; DE–DF −7; DG–DJ −10; DK–DR −27; DS–DW −16; DX–EA −11; EB–EF −21 — plus the upstream
    corrections each batch applied in the same session. Per-batch write-ups, the rules' evidence
    lines and the candidates censused and dropped are in [`skel/PHASE6.md`](skel/PHASE6.md) §3–§4 and
    the layers' `CORRECTIONS.md` files.
  - **Rounds one through six (2026-08-13 … 2026-08-18)**: −559, −162, −131, −109, −53, −39, all with
    **0 units regressed and 0 newly flagged**. What each round tested and decided — including the
    three prompt changes that worked and the four that did not — is in
    [`skel/PHASE6.md`](skel/PHASE6.md) §1.3 and §3.
- **Phase 5 Retrospective**: Complete and closed (5,919 → 2,084). Established the flat yield ceiling of monolithic regeneration and the provenance law of yield. For full details, measurement tables, and lessons learned, see [`skel/PHASE5.md`](skel/PHASE5.md).

### Standing Disciplines

- **A refusal is an answer, not a parse failure** (2026-08-18, §30 finding 3; **split in the driver
  the same day**, §31): `keep`, `none`, `both` and `yes` are first-class answers in the class
  prompts' own vocabularies, and each means *the checker is wrong here*. When every answer in a call
  is one of them the splice changes nothing, `apply` returns False, and the driver used to file the
  whole response under `no actionable answer` — discarding 30% of a round. It is now counted as
  `refused:<class>` and printed in the fix summary. **The census is a position-by-position reading
  list**, and a class that is all refusals is checker-side work rather than a prompt population. Two
  corollaries: a "frozen" class is ambiguous until you look (`arg_slot` at 0 removed over 7 calls is
  not a model that could not answer, it is a model that answered `keep` seven times); and a *failed
  change* is not a refusal — `drop` the splice could not carry out is a splice failure, and counting
  it as a verdict would poison the census.
- **"Checker silent" and "a rule already ran and said no" are different diagnoses** (2026-08-18,
  §P2, rule EI): rule AI accepts the exact citation convention both rule-EI positions use, and
  declined them only because its gate is *"both citations inside one NP span"* — which a floating
  quantifier, given its own Layer-3 span, can never satisfy. Nineteen read batches and eight `--fix`
  rounds walked past two positions `--check` was naming out loud, because a reader who sees a
  familiar convention assumes the rule for it has been applied. **Of every standing pair, ask which
  existing rule ought to have taken it, and then ask which single gate stopped it.** The companion
  question is the older one: *which normalization has already run on this citation?*
- **Read the refusals; they pay at a rate model calls do not** (2026-08-18, §P2): the first batch
  chosen by the refusal census — `arg_slot`'s 8 predicates, refused 7-for-7 in two consecutive
  rounds — produced three checker- or upstream-side findings and −4 violations **at zero model
  cost**, against 0.042 violations per model call in the same round. A class at a 100% refusal rate
  is not a model that could not answer; in both rule-EI positions **the model was citing exactly
  what `SYSTEM_PROMPT` told it to cite**, and `keep` was the right answer seven times.
- **A question's yield is a property of its evidence, not of the residue's difficulty** (2026-08-18,
  §30 finding 1): `dual_role` runs at 0.833 violations per call and every other class at 0.081,
  because rule EG's is the only question whose evidence sits entirely inside the artifact — it shows
  the model both of its own rows and asks which is right. Every other class asks it to adjudicate
  against `derive_unit`'s reading, which the Independence Rule withholds. **When a class will not
  move, ask first whether the model has been given enough to decide it.**
- **Measure calls, not only violations** (2026-08-18): a round's violation diff says which positions
  moved and never how many questions were asked to move them. Run `--fix` with `--log`; the per-class
  `calls / removed / per call` table is appended to it under `=== fix summary ===`. Round 7's whole
  reading came from that table, and `_whole` — 38.6% of the call budget for 6 violations — is
  invisible without it.
- **A silent `--check` pass, closed (2026-08-07)**: Found while re-measuring from a `git worktree` (where `src/` is unbuilt because per-canticle source directories are generated, not tracked). `api.cantos()` now raises `FileNotFoundError` if the directory is missing, preventing checks from silently returning `0 hard, 0 soft`. `tests/test_api.py` pins this behaviour.
- **How `CORRECTIONS.md` is used**: `*/CORRECTIONS.md` records **hand-applied corrections**, not a place to log "found a problem, leaving it." If a review turns up a clear, decidable error, **fix it in the same session** and record what was fixed and why. The only legitimate "left alone" write-ups are ones with a genuine structural reason the text itself doesn't decide (e.g., free relatives, accusative-and-infinitive, Latin quotations, etc.).
  - **A `--fix` round is not a correction and is never written there** (2026-08-16). It is LLM regeneration of the artifact, decided by the acceptance gate rather than by a person reading a line. Round measurements belong in [`skel/PLAN.md`](skel/PLAN.md)'s *Phase 7 Record* — Phase 6's are in [`skel/PHASE6.md`](skel/PHASE6.md) — and in this file's *Latest Improvements*. What does go in `CORRECTIONS.md` is what a human decided: upstream retags, gated-script rewrites, checker and derivation rules, and the shapes deliberately left standing.
- **CRLF hygiene**: Writing TSVs with Python's `csv` module and `newline=''` defaults to `\r\n`. Ensure `\n`-only line endings (`sed -i 's/\r$//'` or `Path.write_text` splitting/joining on `\n`) before diffing or committing.
- **Measure a checker rule by violation diff, never by the total** (2026-08-15): keep the sorted `--check` output before and after and diff it, so what a rule *newly flags* is visible next to what it removes. Two rules this session looked neutral or positive on the total and were only decidable from the diff — rule AM (−15/+22, kept: the derivation is now right) and its subject leg (dropped). A rule may be kept when it raises the count, if it makes the parse provably more correct; record that trade explicitly.
- **Census a shape before writing a rule for it** (2026-08-15): count the structural pattern over all 100 cantos first. One evidence line is not a population, and several candidate rules have been dropped at census — with a population of 0, and once (gapped-clause remnants, Inferno 16–20 batch) with a population of 12 that the census itself showed was reading error rather than checker silence.
- **When you write a checker rule, check its mirror leg** (2026-08-15): a labeling convention has two directions, and a rule that accepts "the LLM names X where the derivation names Y" leaves the reverse reported. Three of the Inferno 16–20 batch's five rules were mirror legs of rules already in the checker (AV, AW, AY), worth 18 positions between them.
- **Ask what the artifact asserts that no comparison tests** (2026-08-18, rule EG): every soft check from rule V to EF compared the LLM's reading with `derive_unit`, so a contradiction *inside* the reading was invisible whenever one of its two rows happened to match the derivation — one token in two roles of one predicate, 56 positions, 52 of them on lines `--check` said nothing about. A read can only ever examine a position the checker has named, which is why 21 read batches walked past this one. **A checker built entirely out of comparisons has a blind spot the shape of its own inputs.**
- **A check that only reports lets the next round write more** (2026-08-18): rule EG's evidence line was written *by* the fifth-to-sixth round series, because `_apply_missing_arg` appends a row without looking at the rows already there and the per-unit acceptance gate absorbed the contradiction. A new soft class over LLM-authored artifacts is owed a matching **splice guard** in the applier that can create it.
- **Before blaming a frozen class on the model, ask whether any answer to the question asked could have moved it** (2026-08-18, the `arg_slot` merge): 8 predicates carrying a `missing_arg` and an `extra_arg` on the same role survived three `--fix` rounds because the two halves were asked as two independent questions, and neither answer alone could clear the pair.
- **Mutation-check a new rule's test**: break the rule in the source and confirm the test fails. A test that still passes with the rule removed pins nothing. **Include the call site**: the `arg_slot` merge's own function was pinned while the line calling it from `_fix_canto` was not, and only the mutation run showed it.
- **Editing frozen TSVs**: never by hand. Use a gated script that asserts the expected word at each `(line, token)` before rewriting the row, then re-run every layer's `--check` and `pytest`.

### Next Steps & Open Routes

- **Phase 7's plan (opened 2026-08-18, base 160; now at 154 after §P1)**: **drive soft to 0, and when
  a fix fails, find out why.** The read series is complete, eight rounds have run, and the residue is
  a hard core: **the eighth round measured 0.042 per call over 142 calls with 43.7% refusals**, and
  the census those refusals produce is what pays instead (§P2, −4 at zero model cost), so
  **the residue is not going to 0 by running rounds** and a ninth is not queued. What closes it is
  checker-side work off the refusal census. Full statement, work queue and measurement procedure in
  [`skel/PLAN.md`](skel/PLAN.md).
- **The assistant-side reading list is confirmed by two rounds, and its first batch is read**:
  `arg_slot`'s 8 predicates are **done** (§P2 — rule EI, one Layer-4 retag, one shape censused and
  dropped, four reading disagreements). Still standing: `extra_arg`'s 15 `keep`s,
  `extra_arg_subject`'s 13, `missing_arg`'s 10 `none`s, `missing_arg_adverb`'s 3. Read each with
  `read.py` and give it one of the five verdicts in *How to Read a Batch*; a refusal chooses the
  position and has no standing on what is wrong there.
- **Two systematic failure shapes from round 8's log** (§P1), which the violation diff does not show:
  `missing_tuple_nominal` fails identically nine times out of nine (`missing_tuple: predicate NN.2
  not proposed` → `extra_arg: NN.2 obl:a`), and `missing_arg_subject` splices a fresh `extra_arg subj`
  in half its calls — check its applier against rule EG's splice guard.
- **Look for more artifact-internal checks** — rule EG's shape, the only question shape the model
  answers well (0.833 per call against 0.081). It found 56 positions, **52 of them on lines `--check`
  was silent about**, which is why nineteen read batches walked past them.
- **The prompt queue is empty, deliberately.** Seven rounds of verdicts say only three shapes have
  ever moved a class — withdraw a licence (`_CONV_ADVERB`, −66.3%), narrow one (`_CONV_ADJUNCT`,
  −52.6%), make an instruction executable (`_CONV_DATIVE`, −45.5%) — and every added convention
  paragraph about a shape the model reads wrong has measured at the round average. No candidate of the
  three working shapes is outstanding.
- **The read series is CLOSED (2026-08-17)**: all 100 cantos read position by position in nineteen
  batches. Nothing is re-read — the standing residue is reading error, and it is the most direct
  sample there is of what a `--fix` round leaves behind. The eight-step procedure stays written down
  in [`skel/PLAN.md`](skel/PLAN.md)'s *How to Read a Batch*; the per-batch record is in
  [`skel/PHASE6.md`](skel/PHASE6.md). Tool: `skel/read.py`.
- **The subject slot may simply stay reported**: `extra_arg subj` **24 → 24 (±0)** in round 7,
  `missing_arg subj` 19 → 16, plus the `role_mismatch` rows with `subj` on one side — 40 of the 152.
  Round 4 measured `_CONV_SUBJECT` at the round average, the read series read it and left it standing,
  and `arg_slot` (its one mechanical part) came back **0 of 7 calls, all `keep`**. This is the corpus's
  genuine disagreement over Dante's inversion.
- **The other standing populations and the named-but-uncensused shapes** — `missing_arg_adverb` (21),
  `missing_tuple_nominal` (16), `extra_arg_adjective` (19), the `parataxis`→`ccomp` rule for quoted
  speech, the relative pronoun's antecedent subject, the Layer-2 `onde`/relative-`che` vocabulary
  routes — are listed with their populations and their blocking reasons in
  [`skel/PLAN.md`](skel/PLAN.md)'s *Active & Open Routes*, together with the standing heuristics that
  produced rules in more than one batch (which check runs first, which edge a gate reads, which
  normalization has already run, check the mirror leg, measure by diff then read what the diff
  removed). Routes Phase 6 closed are in [`skel/PHASE6.md`](skel/PHASE6.md) §5.

## Status

**All five layers are implemented, built for all 100 cantos, and merged to `main`.** Layer 5's
checker was refined through Phases 0-5r, rules V through EH, Phase 6's restructuring plus seven `--fix` rounds, and Phase 7's eighth, ninth, and tenth rounds, rule EI, census reads/retags, systematic failure shape fixes, dual_role resolution, outlier position fixes, Round 10 log audits, and four assistant-side read census rounds, bringing its divergence residue to **87** and its total soft count to **87** (all structural outliers and internal contradictions are 0)
(down from 17438 at the first full-corpus measurement). Work continues as **Phase 7** — drive soft to 0, and diagnose why a fix fails. See [`skel/PLAN.md`](skel/PLAN.md) for the current plan and the open positions, [`skel/PHASE6.md`](skel/PHASE6.md) and [`skel/PHASE5.md`](skel/PHASE5.md) for the closed phase records, and *The layers* below and [`skel/README.md`](skel/README.md) for the design and current status.

**The pronoun case annex is complete and closed (2026-08-02).** It is a permanent Layer-2 sibling
extension, `case/`, on the same footing as `np/`, `dep/` and `skel/` relative to `morph/` — not a
new `morph/*.tsv` column, decided at the annex's close after two budgeted blind-regeneration
rounds were measured and rejected against a verdict rule fixed in advance. See
[`case/README.md`](case/README.md) for the design and current status and
[`case/CORRECTIONS.md`](case/CORRECTIONS.md) for the full measurement history, including *Step 5 —
the merge decision*.

**The open route is checker-side, off the refusal census** — this is Phase 7, opened 2026-08-18 at base **160** and now at **87**. The read series is complete (all 100 cantos read position by position) and ten rounds have run. The seventh added the instrument: run with `--log`, it showed that 30% of its calls end in the model refusing, naming position by position where it thinks `--check` is wrong. **The eighth (§P1), ninth (§P3), and tenth (§P8) rounds confirmed that rounds are no longer the productive instrument** (~42-45% refusals) and reproduced the census per class across four rounds, confirming it as a settled reading list. The census audit (§P4) audited all 38 refusals, resolving two upstream Layer-4 attachment errors. The systematic failure shapes (§P5) resolved the 8 `missing_tuple_nominal` positions and added a subject splice guard, §P6 resolved the remaining 3 `dual_role` positions, §P7 resolved the 7 structural outlier positions, §P8 resolved 3 divergence positions, §P9 resolved 4 divergence positions with a driver fix, and §P10–§P13 resolved 25 divergence positions via the read census rounds. All five layers plus the case extension are implemented, built for all 100
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
  further shapes where the derivation was silent rather than disagreeing, and the AG-EF series
  from the Inferno 4-6, 7-10, 11-15, 16-20, 21-25, 26-30 and 31-34, the Purgatorio 1-5, 6-10,
  11-15, 16-20, 21-25, 26-30 and 31-33 and the Paradiso 1-5, 6-10, 11-20, 21-25 and 26-33
  per-position reads — all 100 cantos; see
  [`skel/README.md`](skel/README.md). `dante_corpus/skel.py` (dataclasses, role
  vocabulary, deterministic derivation, table parsing, validation, TSV I/O, serve-time joins),
  `dante_corpus/hashes.py` (content-hash versioning, all layers), `Canto.skel()`/`Canto.hashes()`
  in `api.py`, `dante-corpus text skel`/`dante-corpus hash` in `cli.py`, `skel/skel.py` (LLM
  build driver, mirrors `dep/dep.py`, plus `--stats`/`--repair` modes), `skel/read.py` (the audit
  series' read tool: all five layers plus both Layer-5 readings for one parse unit). `--check` across all
  three canticles reports **0 hard, 87 soft** (down from 17438 at the first full-corpus
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
   CP-CT series, the CU-CY series, the CZ-DD series, the DE-DF series, the DG-DJ series, the DK-DR series, the DS-DW series, the DX-EA series and the EB-EF series, with
   `--fix` restructured in Phase 6 and eight rounds run, plus rules EG/EH and Phase 7's rule EI (`--check`: 0 hard / 150 soft). Phase 5 closed with every route measured; see
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
