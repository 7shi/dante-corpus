# skel — Layer 5 Plan: Phase 7, Closing the Residue

## Status

- **Current State**: `make -C skel check` reports **0 hard, 150 soft** violations across all 100
  cantos — **144 divergence positions + 6 `dual_role`** (rule EG's artifact-internal contradiction).
  Per canticle: inferno 42, purgatorio 54, paradiso 54. Base as of 2026-08-18, after rule EI
  (154 → 150, §P2) and the eighth `--fix` round before it (160 → 154, §P1).
- **Other Layers**: `dep --check` **0 hard / 0 soft**, `case --check` 0 hard, `np --check` 0/0,
  `morph --check` 0/0, `pytest` **542 passed**.
- **Phase 5**: Complete and closed — 5,919 → 2,084 soft. Full record in [`PHASE5.md`](PHASE5.md).
- **Phase 6**: Complete and closed — 2,084 → 160 soft, with seven user-run `--fix` rounds (−1,157)
  and a per-position read of all 100 cantos in nineteen batches (rules AG–EH, −793, at zero model
  cost). Full record, per-round tables, the read series and the routes it closed are in
  [`PHASE6.md`](PHASE6.md).
- **Phase 7 (current)**: **drive soft to 0, and when a fix fails, find out why.** See below. One
  round run (§P1, 160 → 154) and one refusal-census read landed (§P2, 154 → 150, rule EI); the work
  is checker-side from here, off that census.
- **Section references**: a bare **§N** points to [`PHASE6.md`](PHASE6.md)'s chronological record
  (§1–§31, the seven rounds and nineteen read batches). Phase 7's own write-ups are numbered **§P1,
  §P2, …** in *Phase 7 Record* below.

---

## Phase 7 — What It Is

**The target is 0 soft violations.** Soft checks are rules to fix, not exemptions to tolerate: a
standing position is either checker silence, a wrong derivation, an upstream mistag, a prompt defect,
or a reading disagreement worth reporting — and each of those has a different owner.

**The premise Phase 6 measured, and Phase 7 starts from: the residue does not go to 0 by running
rounds.** Outside `dual_role`, a model call is worth **0.081** violations (§30 in
[`PHASE6.md`](PHASE6.md)), and 51 of the standing 152 divergence positions have survived three rounds
each. A round over the standing residue is expected to take 12–20 positions and to introduce nothing
new to read. **The eighth round confirmed this below its own floor** (§P1): 142 calls, **6**
positions, **0.030** per call outside `dual_role`, and 43.7% of the calls refusals. At that rate the
standing 144 divergence positions would cost on the order of 3,500 calls. Rounds are not the
instrument any more. **And the instrument that replaces them paid on its first batch** (§P2): the 8
`arg_slot` refusals read out to 3 checker- or upstream-side findings and **−4 at zero model cost**.

**So the work shifts from repairing positions to diagnosing failures.** Phase 6 spent itself finding
positions to read (nineteen batches over 100 cantos) and repairing them (seven rounds). Phase 7 asks
the other question: **when the driver asks and nothing improves, what happened?** Three instruments
exist for it, all landed 2026-08-18 and none of them costing a model call:

1. **The refusal split** (§31). `no actionable answer` was two outcomes wearing one label. A
   **refusal** — every answer in the call is that class's own word for *leave this as it is*
   (`keep`/`none`/`both`/`yes`, or for `role_mismatch` the role the artifact already carries) — is the
   model asserting **the checker is wrong**, and it is now counted per class (`refused:<class>`)
   and printed as a `refused` column in the fix summary. 57 of round 7's 332 calls were refusals, and
   they had all been discarded. **A class that is all refusals is checker-side work, not a prompt
   population.**
2. **The per-class `calls / removed / per call / refused` table**, written into `--log`. A call count
   is not recoverable from the artifact afterwards, so it has to be written down while the round runs.
3. **The field-note slot** (§29) — measured, kept because it costs nothing, and **not to be
   widened**: 5 notes over 332 calls, one of them real.

**What a failure diagnosis is worth: rule EH is the worked example.** The model refused one
`dual_role` question (`both` at purgatorio 2:40). The refusal was read; `_case_supports_role` was
sending *every* `obl:<marker>` role to the `ablative` slot whatever the marker said, so rule CM's
"the two supporting slot sets must differ" rejected a fused clitic it licenses everywhere else. The
model was right and the checker was wrong: 161 → 160.

**And the shape of question that pays is now known.** `dual_role` runs at **0.833 removed per call**
against 0.081 for everything else — because it is the only question in this project whose evidence
sits **entirely inside the artifact**: it shows the model both of its own rows and asks which is
right. Every other class asks it to adjudicate against `derive_unit`'s reading, which the
Independence Rule withholds. **Looking for more questions of that shape is a first-class Phase 7
route** (see *Open Assistant-Side Routes*).

### The Phase 7 Work Queue

1. ~~**The eighth `--fix` round, `--no-whole`**~~ — **run 2026-08-18, §P1**: 160 → 154. Its finding is
   that the queue's other items are the work; a ninth round is not queued.
2. **The refusal reading list — confirmed twice, and its first batch paid** (§P2: `arg_slot`'s 8
   refusals read, 3 of them checker- or upstream-side, **−4 at zero model cost**, rule EI). **Next in
   the list, in order**: `extra_arg`'s 15 `keep`s, `extra_arg_subject`'s 13, `missing_arg`'s 10
   `none`, `missing_arg_adverb`'s 3. Read each with `read.py` and give it one of the five verdicts in
   *How to Read a Batch*. **A refusal chooses a position and has no standing on what is wrong there**
   — it is a hypothesis about the checker with exactly the standing a field note has about the corpus.
   §P2's finding to carry in: ask of every standing pair whether an **existing** rule is one gate
   away from taking it, because rule AI had already run on both rule-EI positions and declined.
3. **Two systematic *failure* shapes round 8's log names** (§P1), neither of them a refusal:
   `missing_tuple_nominal` fails identically nine times out of nine (`missing_tuple: predicate NN.2
   not proposed` → `extra_arg: NN.2 obl:a`), and `missing_arg_subject` splices a fresh `extra_arg
   subj` in half its calls — check its applier against rule EG's splice guard.
4. **Look for more artifact-internal checks** — rule EG's shape: a contradiction the artifact
   contains without reference to `derive_unit`. Rule EG found 56 such positions, **52 of them on lines
   `--check` was silent about**, which is why 21 read batches walked past them. Any check of this kind
   both raises the count honestly and produces questions the model can actually answer.
5. **The standing open routes** below, which the reads named but did not settle.

**Not queued, deliberately:**

- **Any prompt change.** Seven rounds of verdicts say only three shapes have ever moved a class —
  withdraw a licence, narrow a licence, make an instruction executable (§1.3 in
  [`PHASE6.md`](PHASE6.md)) — and there is no candidate of any of those shapes outstanding. Adding
  convention prose about a shape the model reads wrong measures at the round average, four times out
  of four.
- **Any widening of the field-note slot** (§29, measured and not paying).
- **Any restructuring of `dante_corpus/skel.py`.** That waits for 0, which is what makes it safe.
  See [`PORTABILITY.md`](PORTABILITY.md).

---

## Operating Principles & Architecture

*Inherited from Phase 6 unchanged; the three-stage driver, the Independence Rule and the division of
labor are what produced 2,084 → 160.*

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
- Exhaustive position-by-position reads uncover genuine checker silence, upstream layer errors,
  defects in `derive_unit` itself, and defects in the corpus's own *prompt* — the four verdicts an
  aggregate statistic cannot separate. The procedure is *How to Read a Batch* below; `skel/read.py`
  is the tool (`--check` names a position, `read.py` shows all five layers for its parse unit).
- **The canto-batch series is complete**: all 100 cantos were read in Phase 6, in nineteen batches
  (see [`PHASE6.md`](PHASE6.md) §4). **Nothing is re-read.** In Phase 7 the same eight-step procedure
  runs on positions chosen by the refusal census instead of by canto order — the model names the
  position, the read decides what is wrong there.

### 5. Immediate Cross-Layer Remediation
- Upstream defects in Layer 2 (`morph/`), Layer 4 (`dep/`), or the pronoun case annex (`case/`) discovered during audits must be corrected in the same session, re-validated, and documented in `*/CORRECTIONS.md`.
- **`*/CORRECTIONS.md` records hand-applied corrections only** — upstream retags, gated-script
  rewrites, checker/derivation rules, and the shapes deliberately left alone with the reason. A
  `--fix` round is LLM regeneration of the artifact, not a correction to it: rounds are written up
  in [`PHASE6.md`](PHASE6.md) and summarized in the root [`../PLAN.md`](../PLAN.md),
  and never in `CORRECTIONS.md`.

### 6. Strict Division of Labor
- **Assistant**: Conduct per-position audits, implement deterministic checker/derivation rules, develop Stage 2 micro-prompts/hints, and maintain upstream layer data.
- **User**: Execute parallel `--fix` regeneration passes (`make -C skel fix`) and commit updated TSVs.
- A read batch is therefore entirely the assistant's, start to finish: the eight steps in *How to Read a Batch* need no model call and no user action, and a batch is not finished until its write-ups and count updates are in.

---

## The Eighth Round — scale, command, and the checklist to read it with

> **RUN, 2026-08-18 — result and the six answers are in §P1** (160 → 154, 142 calls, 62 refusals).
> Everything below this line was written *before* the round and is left unedited, which is the whole
> point of it: it is what the round was read against. `--no-whole` is confirmed permanent; the
> command block below is the standing round command.

**Base: 0 hard, 160 soft** (152 divergence + 8 `dual_role`), `pytest` 534, all other layers 0/0. The
seventh round settled all four of its candidates — `dual_role` **−82.0%**, `_CONV_DATIVE` **−45.5%**,
`arg_slot` **0 of 7 calls**, and the splice-guard caveat did not materialize (`missing_arg` −14.5%,
above the divergence average).

**Run it with `--no-whole`.** §30 finding 6: `_whole` took 128 calls — 38.6% of the round's budget,
and the most expensive call in the driver — for 6 violations. No file changes for this; the flag
exists:

```
uv run skel.py <canticle> --fix -m $(MODEL) --no-whole --log skel-<canticle>.log
```

three ways in parallel, **one log file per process** (`fix` truncates its log at start). `--log` is
not optional any more in practice: the per-class `calls / removed / per call / refused` table only
exists if it is passed, and §30's central finding is invisible without it. The summary is appended to
the log itself under `=== fix summary ===`. `make -C skel fix` still passes neither flag, and that
standing decision is untouched — a round is measured by **violation diff**, not by driver telemetry.

**What is on the scale:**

1. **The refusal split** (§31), the first round with a refusal census taken by the driver rather than
   by hand. Nothing about the model changes; what changes is that 30% of a round stops being
   discarded.
2. **Nothing else.** No prompt candidate is queued, and rule EH closed the only checker candidate
   round 7 produced.

**What the round will *not* do, and it is worth writing down before it runs.** At 0.081 per call
outside `dual_role`, a round over the standing 152 divergence positions is expected to take on the
order of 12–20 of them. **The residue is not going to 0 by running rounds** — what closes it is the
checker-side work in the Phase 7 queue above.

**After the round — the checklist.** Re-measure per *How to Measure a `--fix` Round* below, then
answer these six. They were written before the round, so it cannot be read backwards into whatever it
happens to show.

1. **Does `dual_role` still run several times the rate of every other class?** It was 0.833 against
   0.081 (round 7) with a population that had never been asked. Rule EH took one of its 9 survivors,
   so the remaining 8 are positions the model failed on *with the contradiction pointed out to it*.
   If the rate collapses toward the others, the "artifact-internal questions are the answerable ones"
   reading is about novelty rather than about evidence, and §30 finding 1 needs weakening — as does
   Phase 7 queue item 3.
2. **What did `--no-whole` cost?** Compare `TOTAL` calls and `per call` against round 7's 332 /
   0.190. If removed falls by ~6 while calls fall by ~128, the switch is confirmed and permanent.
   If it falls by much more, `_whole` was doing something the class prompts cannot and the flag
   should come back for a subset.
3. **Does the refusal census reproduce, and is it stable per class?** Round 7 by hand: `arg_slot` 8
   `keep` over 7 calls, `extra_arg_subject` 15, `extra_arg` 16, `missing_arg` 10 `none`. A class whose
   refusal rate is *stable across two rounds on the same positions* is settled — that is the
   checker-side reading list, and it is the round's real product.
4. **Is anything refused that was not refused last time?** A position the model repaired in round 7
   and refuses in round 8 would mean the two rounds disagree with each other, which nothing in the
   series has yet shown.
5. **Did `_CONV_DATIVE`'s gain hold?** `missing_arg obl:a` was 11 → 6. A rebound would mean the
   round-7 result was the population's easy half rather than the clause working.
6. **Field notes**: count them (`grep -c '^NOTE'`). If a third round is again in single digits, §29 is
   closed as measured-and-not-paying, and the note slot can be left in place unmentioned.

Then take the reading list the refusal census produces — starting with `arg_slot`'s 8 predicates.

---

## Phase 7 Record

*Opened 2026-08-18 at base **0 hard / 160 soft**, `pytest` 534, all other layers 0/0. Every batch,
round and rule gets a numbered subsection here (**§P1, §P2, …**), written in the same session, per
step 8 of *How to Read a Batch*.*

### §P1 — Eighth `--fix` round, 160 → 154 (−6, −3.8%), and the refusal census reproduces

Run by the user 2026-08-18, three ways in parallel with `--no-whole --log`, per *The Eighth Round*
above. **160 → 154 soft, 0 hard**; per canticle inferno 44 (±0), purgatorio 56 (−2), paradiso 54
(−4). Divergence residue **148**, `dual_role` **8 → 6**. Violation diff against a base worktree:
**exactly the 6 lines removed, 0 newly flagged, 0 regressed** — the eighth consecutive round with a
clean diff. 130 units flagged, 6 cleared outright, per-unit yield **0.046**. `pytest` **534**,
`skel/*.tsv` only (6 files).

The six lines removed: paradiso 5:37 `role_mismatch`, 23:134 `dual_role`, 26:79 `extra_arg`,
31:19 `extra_arg`; purgatorio 4:7 `dual_role`, 29:35 `missing_arg obl:a`.

**Per-class table, the three logs summed** (142 calls against round 7's 332):

| class | calls | removed | per call | refused |
| --- | --- | --- | --- | --- |
| `dual_role` | 8 | 2 | **0.250** | 0 |
| `extra_arg` | 23 | 1 | 0.043 | 15 |
| `role_mismatch` | 21 | 1 | 0.048 | 13 |
| `extra_arg_subject` | 17 | 1 | 0.059 | 13 |
| `missing_arg` | 34 | 1 | 0.029 | 10 |
| `arg_slot` | 7 | 0 | 0.000 | **7** |
| `missing_tuple_nominal` | 9 | 0 | 0.000 | 0 |
| `missing_arg_subject` | 8 | 0 | 0.000 | 0 |
| `missing_arg_adverb` | 7 | 0 | 0.000 | 3 |
| `extra_tuple` / `missing_tuple` / `extra_arg_adjective` | 8 | 0 | 0.000 | 1 |
| **TOTAL** | **142** | **6** | **0.042** | **62 (43.7%)** |

**The six checklist questions, answered in the order they were written:**

1. **`dual_role` still outruns everything else, and the ratio is what held.** 0.250 per call against
   **0.030** for the other 134 calls — **8.3×**, against round 7's 10.3× (0.833 / 0.081). Both terms
   fell by about a third; the *ratio* did not. So the gap is not novelty wearing off — it is what §30
   finding 1 said it was, a property of where the evidence sits. **Phase 7 queue item 3 (look for more
   artifact-internal checks) is confirmed rather than weakened.** Caveat kept explicitly: 8 calls is a
   small base, and one more round at this rate will not settle it further.
2. **`--no-whole` cost nothing identifiable and saved 57% of the budget.** Calls 332 → 142; removed
   63 → 6. Round 7's `_whole` was 128 calls for 6 violations, and removed fell by close to that same
   6 with the whole of `dual_role`'s fresh population also gone from the numerator. Nothing in the log
   shows a shape the class prompts could not reach. **The switch is confirmed and permanent**; the
   flag stays available but the round default is `--no-whole`.
3. **The refusal census reproduces, and per class it is essentially identical.** `arg_slot` **7 calls,
   7 refused, 100%, every answer `keep`** — round 7 was 7 calls / 0 removed. `missing_arg`'s `none`
   **10** (round 7: 10), `missing_arg_adverb` **3** (3), `extra_arg` **15** (16), `extra_arg_subject`
   **13** (15). A refusal rate stable across two rounds on the same positions is the definition of
   settled: **this table is the round's real product**, and it is the checker-side reading list.
4. **Nothing repaired in round 7 came back refused in round 8.** 0 newly flagged and 0 regressed, so
   the two rounds do not disagree anywhere. The overall refusal rate rose 30% → 43.7%, fully explained
   by `_whole` (which never produces a refusal) leaving the denominator and by the easy population
   being gone.
5. **`_CONV_DATIVE` held.** `missing_arg obl:a` 6 → 5, no rebound. The round-7 result was the clause
   working, not the population's easy half.
6. **Field notes: 2 over 142 calls** (inferno 10:91, purgatorio 16:34 — the second is a correct
   reading of the position). Third round in single digits. **§29 is closed as measured-and-not-paying**;
   the slot stays in place and is not mentioned again.

**Two failure shapes the log names that the violation diff does not.** Both are Phase 7 read-work,
and both are *systematic*, which is what distinguishes them from the residue:

- **`missing_tuple_nominal` fails the same way nine times out of nine.** Every call is
  `not accepted`, and eight of them with an identical before/after pair — `missing_tuple: predicate
  NN.2 not proposed` → `extra_arg: NN.2 obl:a` (inferno 7:49, 8:52, 8:70, 10:19, 11:67, 24:72,
  31:21; purgatorio 6:49). Two of them also raise a hard violation (`ccomp argument … is not a
  predicate in this unit`). The class is written up in *Active & Open Routes* as "read it, do not
  write for it" after three prompt surfaces failed on it — and this is the reading: **one shape, a
  nominal predicate taking `obl:a`, missed the same way every time.** It is a better first read than
  its 0.000 per-call rate suggests.
- **`missing_arg_subject` makes its own `extra_arg` in half its calls.** 8 calls, 0 removed, and
  four of them turn one violation into two by adding `extra_arg: … subj`, three times with the null
  citation `(0, 0)` (paradiso 11:92, 12:124, 26:27, 29:137; purgatorio 20:93, 25:49). That is the
  splice writing a subject row the unit already disputes — the shape rule EG's splice guard was
  written for, in a different applier. **Check `_apply_missing_arg`'s subject leg against the guard
  in `_apply_missing_arg`'s `dual_role` path before reading the positions themselves.**

One malformed response is worth noting for the same reason: purgatorio 31:13 `missing_tuple_nominal`
returned its table with a *word* in the `Arg Line` column (`| 15.5 | … | obl:a | 15.2 | quale |
quale |`), which is the only format break in 142 calls.

**What this round settles about the plan.** The pre-round prediction was 12–20 positions; the round
took **6**, below its own floor. At 0.042 per call the remaining 148 divergence positions would cost
roughly 3,500 calls, and the refusal census says why: **62 of 142 calls are the model telling the
checker it is wrong.** Rounds are no longer the instrument. The Phase 7 queue is unchanged and its
item 2 is now a list of positions confirmed twice — start with `arg_slot`'s 8 predicates (inferno
5:88, 24:1 ×2, 31:28; paradiso 1:76; purgatorio 9:97, 10:28, 10:58).

### §P2 — `arg_slot`'s eight refusals read; rule EI, 154 → 150 (−4), and one Layer-4 retag

The first batch chosen by the **refusal census** instead of by canto order, and the first test of
whether a refusal is worth reading. `arg_slot` is the class the model refused at **100% in two
consecutive rounds** (7 calls, 7 refusals, every answer `keep`, §P1 answer 3). Its 8 predicates are
the pairs `_split_slot_conflicts` merges — a `missing_arg` and an `extra_arg` naming the same slot.

**Result: 0 hard / 150 soft** (144 divergence + 6 `dual_role`); inferno 42, purgatorio 54,
paradiso 54. `pytest` 534 → **542**; all other layers 0/0. Rule EI measured **−4/+0** by full-corpus
diff; the Layer-4 retag measured **±0** and is kept anyway.

**The eight, one verdict each** (`read.py`, per *How to Read a Batch*):

| position | derivation cites | the reading cites | verdict |
| --- | --- | --- | --- |
| inferno 31:32 `son` subj | `torri` (31.5) | `tutti` (33.6) | **checker silent** → rule EI |
| purgatorio 10:60 `faceva` subj | `gente` (58.3) | `quanta` (58.6) | **checker silent** → rule EI |
| purgatorio 9:97 `perso` subj | `tinto` (97.4) | `secondo` (97.3) | **upstream wrong** → Layer-4 retag |
| inferno 5:92 `pregheremmo` subj | `noi` (90.1 `nsubj`) | `noi` (92.1 `expl`) | censused at 2, **dropped** |
| inferno 24:10 `ritorna` subj | `villanello` (7.2) | `ei` (9.4) | reading disagreement |
| inferno 24:10 `lagna` subj | `villanello` (7.2) | `ei` (9.4) | reading disagreement |
| paradiso 1:81 `fece` subj | `pioggia` (80.7) | `alcun` (81.4) | reading disagreement |
| purgatorio 10:30 `aveva` obj | `dritto` (30.2) | `manco` (30.6) | reading disagreement |

**Rule EI — the floating quantifier.** "e **tutta quanta** … **faceva** dir" (purgatorio 10:58),
"e **son** … **tutti quanti**" (inferno 31:32). Layer 4 hangs the quantifier on the noun as an
adnominal; Layer 3, over-inclusive by design, enumerates `[tutta quanta]` as a noun phrase of its
**own**; `SYSTEM_PROMPT` tells the model to cite a phrase's head. So the reading cites the quantifier
and `derive_unit` cites the noun — one participant, two names, two violations. Gated on the Layer-4
adnominal edge read **through rule C's coordination collapse** (inferno 31:32's `tutti` hangs on
`giganti`, the `conj` of `torri`), on a closed quantifier lemma list, and on Layer 2 calling the
token an adjective/numeral/pronoun rather than a noun. Censused at **53**. Full write-up in
[`CORRECTIONS.md`](CORRECTIONS.md).

**The Layer-4 retag, kept at net zero.** purgatorio 9:97 «Era il secondo tinto più che perso»: Layer
4 made the comparative standard `perso` the **root** and the predicate adjective `tinto` its `nsubj`,
burying the real subject `il secondo` as an `amod`. Inferno 7:103 «L'acqua era buia assai più che
persa» is the identical construction already tagged the other way, so the retag is onto the corpus's
own precedent. Layer 5 **±0** — the two `subj` violations became an `extra_tuple`/`missing_tuple` pair
because the reading still names `perso` as the predicate — and the trade is recorded rather than
hidden, on the rule-AM precedent. See [`../dep/CORRECTIONS.md`](../dep/CORRECTIONS.md).

**Four findings worth carrying forward.**

1. **A refusal is worth reading, and this measures how much.** Eight positions, three of them
   checker- or upstream-side, at **zero model cost**. That is a 37.5% hit rate on a class eight
   `--fix` rounds could not move — against 0.042 violations per model call in round 8. **The refusal
   census is the productive instrument, and Phase 7's premise is confirmed on its first batch.**
2. **The model was refusing because it was right about its own convention.** In both rule EI
   positions the model cited exactly what `SYSTEM_PROMPT` told it to cite — a noun phrase's head —
   and `keep` was the correct answer. A class at a 100% refusal rate is not a model that cannot
   answer; it is a checker being told the same thing seven times.
3. **The blind spot had a shape, and it was rule AI's own gate.** Rule AI accepts this citation
   convention and declines here only because its test is *"both inside one NP span"*. The standing
   heuristic that found it is **"which normalization has already run on the citation?"** — the answer
   was "rule AI's, and it ran and said no", which is a different thing from checker silence and is
   why nineteen read batches walked past it. Ask of any standing pair whether an existing rule is one
   gate away.
4. **Seven of the eight refusals are on `subj`**, and the two the checker was wrong about are not
   about the subject at all — they are about *which token names a noun phrase*. The subject-slot
   route (below) is unchanged by this batch: the four reading disagreements it leaves are Dante's
   inversion and a resumptive pronoun, which is coreference and out of scope by design.

**Censused and dropped: the repeated subject pronoun** (inferno 5:90/92, `noi` … `noi`, Layer 4
attaching both to the same predicate as `nsubj` and `expl`). Censused at 4, but two are `tu`/`ti`
pairs where the `expl` is a reflexive clitic and only Layer 2's lemmatization makes them look alike —
a gate loose enough to take them would confuse a clitic with a subject. The genuine shape is **2**,
only **1** of them flagged. Dropped; recorded so a later batch recognises it.

---

## How to Read a Batch

The procedure below is what produced rules AG through EH, and it is unchanged in Phase 7 — only the
way a batch is *chosen* changed: the canto series is complete, so a Phase-7 batch is a set of
positions named by the refusal census (or by a class the routes below single out) rather than a canto
range. Steps 4–7 are the part that must not be skipped: a rule that is not censused, measured, tested
and written up is not a rule.

1. **List the batch.** For a canto, `uv run skel.py <canticle> --check -c <n>` from `skel/`; for a
   refusal batch, the class's `refused` positions from the round's `--log`. Record the counts and the
   class/role breakdown (`--stats`) before touching anything — this is the batch's baseline.
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
   numbered subsection in this file's *Phase 7 Record* (above), the rule catalogue in
   [`README.md`](README.md), and the counts in both PLAN files. `CORRECTIONS.md` records
   corrections that were *applied* — see the root PLAN's *Standing Disciplines*.

---

## Active & Open Routes

Populations are quoted at the base they were last measured against — mostly **base 541** (after the
fourth `--fix` round) or **base 174/213** — and the base is now **150**, so a route's number is a
starting point for a re-measure, not a current count. These are shapes the reads named but did not
settle; work that runs into one of them should fold it in rather than open a new route. Routes Phase 6
**closed** are in [`PHASE6.md`](PHASE6.md) §5 — read the entry before re-opening one.

### Standing populations

- **The refusal census is route zero, two rounds agree on it, and its first batch is read** —
  `arg_slot`'s 8 predicates are **done** (§P2: rule EI, one Layer-4 retag, one shape censused and
  dropped, four reading disagreements). Still standing: `extra_arg`'s 15–16 `keep`s,
  `extra_arg_subject`'s 13–15, `missing_arg`'s 10 `none`s, `missing_arg_adverb`'s 3. See *Phase 7
  Work Queue* above; every other route below is a shape, while this one is a list of positions the
  model itself chose.
- **The subject slot, and it may simply stay reported.** `extra_arg subj` (96 at base 541, of which
  `∅ (0,0)` 22) and `missing_arg subj` (54) plus the `role_mismatch` rows with `subj` on one side were
  **62 of 174** after round 6. Round 4 measured `_CONV_SUBJECT` at the round average and converted the
  bucket to read-work; the read series read it and left it standing; round 7 moved `extra_arg subj`
  24 → 24 (±0) and round 8 24 → 23, with `missing_arg_subject` spending 8 calls to remove 0 and to
  *add* four `extra_arg subj` rows the acceptance gate then rejected (§P1). It is neither prompt-work
  nor unread — it is genuine disagreement over Dante's
  inversion. Start with the `∅ (0,0)` half, where the derivation found a genuine overt subject, often
  long-distance (e.g. inferno 9:20, `alcun` at 21.4 the subject of `incontra`).
  - **`role_mismatch` is the only large class with no branch of its own, and the only argument-level
    class whose prompt omits `_CONV_SUBJECT`** — while 37 of its 73 positions involve `subj` on one
    side (28 of them the symmetric `obj` ↔ `subj` pair). **Do not close that gap by adding the prose:**
    round 4 measured the same prose at the round average on the buckets it was written for. **Read the
    28 symmetric positions first**; their symmetry argues for one cause, as likely a checker or
    `derive_unit` rule as a prompt branch.
- **The 44 positions Inferno still holds** are the read batches' own residue *after* the rounds have
  been over them, which makes them the most direct sample there is of what a round leaves behind. All
  100 cantos are read, so these are reading disagreement rather than unread material.
- **`missing_tuple_nominal` (16) — read it, do not write for it, and §P1 says what to read.** Round 3
  gave it convention prose and a hint (−7.7%), round 4 a rewritten *question* (−11.1%), round 7 nine
  calls for **0**, round 8 nine calls for **0** — and its positions have been substantially the same
  set throughout. Every prompt surface has been tried. What round 8 added is that the *failure* is one
  shape, not nine: eight of the nine calls turn `missing_tuple: predicate NN.2 not proposed` into
  `extra_arg: NN.2 obl:a` (inferno 7:49, 8:52, 8:70, 10:19, 11:67, 24:72, 31:21; purgatorio 6:49),
  two of them raising a hard `ccomp argument … is not a predicate in this unit` on the way. **A
  nominal predicate taking `obl:a`** is the read.
- **`missing_arg_adverb` residue (21)**: the survivors of the `_CONV_ADVERB` repair and of
  `_CONV_REPEATED`. Two prompt repairs have had their turn, so this is a per-position read — establish
  first whether these are locative adverbs the model still omits or a different shape the branch
  over-collects.
- **`extra_arg_adjective` residue (19; `extra_arg xcomp` 35)**: three rounds took a couple of
  positions each (−20.0%, −3.9%, −5.0%), which is itself evidence of genuine reading disagreement
  rather than prompt weakness. Per-position read to settle it.
- **`role_mismatch` `xcomp` vs `obl` (7)**: the second dominant mismatch shape, unbranched.
- **Rule AN's two unresolved gapping clusters** (purgatorio 25:3, 27:108): 2-slot ambiguities that
  only word order settles, and Italian inverts word order freely. Left standing deliberately.

### Named shapes, not yet censused

- **Subject vs. predicate nominal under a copula** (inferno 19:85 *«Nuovo Iasón sarà»*, 20:77
  *«ma Mencio si chiama»*): Layer 4 calls the single nominal `nsubj`, the LLM calls it the complement
  of an elided pro-drop subject, and the line does not decide. Feeds the `extra_arg subj ∅ (0,0)`
  bucket; census it there rather than as a route of its own.
- **A relative pronoun's subject named by its antecedent** (inferno 16:94 *«quel fiume c'ha proprio
  cammino»*): the derivation cites the relative `c'`, the LLM cites `fiume`. An acceptance rule keyed
  on `skel.antecedent` is plausible — **census it before writing it**.
- **An argument named by its Layer-3 NP head against a clause the derivation cites by its clause
  head** (inferno 13:52, *«Ma dilli chi tu fosti»*): rule AI merges these only when the *role*
  matches, and here the LLM's `obj` on `chi` faces the derivation's `ccomp` on `fosti`. Measure how
  many `extra_arg` positions are NP-head-equivalent to a derived argument in a different role before
  extending AI — one instance is not a population. (The dropped `iobj` ↔ `obl:a` equivalence at
  inferno 28:76 is a second instance; see [`PHASE6.md`](PHASE6.md) §5.)
- **An `advcl` the LLM reads as a complement** (inferno 27:101 "fa **sì come** … getti", 29:63
  "**secondo che** i poeti hanno per fermo", 30:59 "non so io **perché**"): three shapes in which the
  LLM promotes an adverbial clause, a parenthetical, or a bare interrogative to the matrix verb's
  `ccomp`. Layer 4's `advcl` is right in all three; recorded so a later read can decide whether they
  are one population.
- **Quoted speech attached as `parataxis`** (inferno 8:81, `«qui è l'intrata», gridò`): Layer 4 hangs
  the quotation as `parataxis`, a clause-head deprel but not an argument deprel, so the derivation
  never makes it the verb's `ccomp` while the LLM (rightly) does. A `parataxis`→`ccomp` acceptance
  rule for verbs of speech is plausibly large; **measure the population before writing it.** Its
  neighbour, the *result* clause read as `ccomp` (`sì … che`, inferno 22:84), was censused at **2** and
  dropped.

### Upstream routes, blocked on a build round rather than an edit

- **Relative `che`/`ch'`/`onde` tagged `conjunction` (247 tokens)**: unblocked only by an independent
  model read of the `case` annex over the 243 positions the retag would add. See
  [`../morph/CORRECTIONS.md`](../morph/CORRECTIONS.md).
- **`onde` is tagged five ways in Layer 2** (conjunction 56, pronoun 43, adverb 23, noun 11, relative
  pronoun 7). The noun rows are right; the 129 relative ones split three ways by nothing visible. Its
  Layer-5 cost is paid by rules BM and DY, so this is a Layer-2 quality route rather than a violation
  route — a measured vocabulary pass, not a per-line edit.
- **`dep.subject_agreement`'s *coordinated subject* exclusion (12 positions)**: restricting it to the
  number test — a coordination of nominals is third person however many members it has — was
  implemented and measured, and takes `dep --check` from 0 to 12 soft. Each is a real Layer-4 question
  (inferno 2:33, 8:28, 21:121, 25:36; purgatorio 4:102, 5:82, 10:62, 23:113, 29:37; paradiso 14:125,
  19:12, 31:96); reverted rather than landed against the 0-soft invariant. It is what keeps rule AG
  from dropping the wrong inherited subject at inferno 24:125.

### Standing heuristics — the questions that produced rules in more than one batch

Each of these earned its place by taking positions in a batch that had not thought to ask it. Ask all
of them of every new rule.

- **Which checks run *before* this rule?** (rules AQ′, DG, DS, DT, BZ). An acceptance rule can be
  correct and complete inside `_classify_divergence` and simply absent from the membership check that
  runs first on the un-normalized row.
- **Which *edge* does the gate read?** (rule BP, nine rules at once, plus rule CY). Every rule that
  reads a deprel edge — head, child, or marker — may be comparing Layer 4's raw head while
  `derive_unit` normalizes through `aux`/`cop`.
- **Which *normalization* has already run on the citation?** (rules CD, CI, DZ — the last needing rule
  AI's NP-head equivalence and rule C's coordination collapse composed).
- **What *else* does this rule's evidence cover?** (rule CW from rule BA's). When a rule accepts an
  argument *because* of some structural fact, ask which other arguments that fact reaches.
- **Does the rule's docstring ask for everything the code tests?** (rules DL, DM each dropped a POS
  condition its own stated reason never asked for).
- **Is the gate a claim about a *column*?** (rules DY, EB). A gate naming a part of speech or a deprel
  is only as good as that column's consistency — `come` is written 812 times under eight deprels and
  four tags.
- **What does it do when the shape supplies *several* citations?** (rule BB — rule V popped one `subj`
  out of a map a coordinate subject fills three times).
- **Does a comment delegate to a branch that never runs?** (rule CV). When a gate excludes a pair, ask
  **which feature** it is excluding and what it stops.
- **Check the mirror leg — but a mirror is not owed acceptance.** Three of the Inferno 16–20 batch's
  five rules were mirrors, worth 37 positions in the next batch; rule BR's mirror measured −6/+0 and
  was **dropped**, because its only evidence is a Layer-3 span and Layer 3 is over-inclusive by
  design. Measure the mirror every time; land it only when its evidence is as strong as the leg it
  mirrors.
- **Measure by violation diff, then read what the diff removed** (rule DQ's widening scored −3/+0 and
  was still wrong).

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
