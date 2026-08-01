# Plan: a shared grammatical-analysis stack in the corpus

## Status

**All five layers are implemented, built for all 100 cantos, and merged to `main`.** Layer 5's
checker was refined through Phases 0-5q and its soft residue is at **3633** (3550 at the end of
Phase 5's own work; the case annex's step-4 slices then moved it 3555, 3469, 3634 — two of the
three raised it, correctly and by design — and its step-5 `morph/` round took it to 3633) — every route the
Phase 5 plan opened now has a measured verdict and none is open (see
[`skel/PLAN.md`](skel/PLAN.md)'s *Where Phase 5 ended*). See *The layers* below and
[`skel/README.md`](skel/README.md) for the design and current status. One follow-on is **on the
branch `case-pilot`**: the pronoun case annex, [`case/PLAN.md`](case/PLAN.md) —
its kill-gate pilot ran on 2026-07-30 and passed (81% self-agreement on the disputed clitics vs
95% on a control, zero three-way splits), step 2 froze the vocabulary and scope and wrote the
driver the same day, **step 3's corpus pass finished on 2026-07-31** — all 100 cantos at 0
hard, frozen and committed before the join to `dep` was looked at — and **step 4 closed on
2026-08-01**: all 510 adjudication candidates have a verdict, across three slices totalling
**215 positions / 270 rows** of hand-verified `dep/` corrections. **Step 5's owed `morph/`
correction round then landed on 2026-08-02** — 10 hand-verified singletons plus the 58-token
comitative family, 41 canto artifacts, `skel` 3634 → 3633 — and the chunk regeneration it owed
`case/` **has since been run, taking `case --check` back to 0 hard** over 13125 tokens / 13189
values. Step 5's `locative` question is settled (it is earned and stays), so the one open item is
**the `morph/` merge**. **A session picking this up should read *Handing off* below first** — it
carries the state check, what is closed, the two open items and what must not be done; then
[`case/PLAN.md`](case/PLAN.md).

- **Layer 1 — Tokens**: implemented (`dante_corpus/tokenizer.py`, served via `Line.tokens`).
- **Layer 2 — Morphology + lemma**: implemented; see [`morph/README.md`](morph/README.md).
  Artifacts are built for all 100 cantos.
- **Layer 3 — Noun phrases**: implemented; see [`np/README.md`](np/README.md). Build
  driver `np/np.py`, served via `Canto.np()` and `dante-corpus text np`. Artifacts generated for
  all 100 cantos. `--check` reported **0 hard / 0 soft** through Layer 3's own history — see
  [`np/README.md`](np/README.md)'s *Check* section and [`np/CORRECTIONS.md`](np/CORRECTIONS.md).
  **It now reports 5 hard / 96 soft**, not from anything Layer 3 did but as fallout from the case
  annex's `morph/` rounds; this is the stack's one open defect and it is described under
  *Open item* below.
- **Layer 4 — Dependency / grammatical role**: implemented and complete; see
  [`dep/README.md`](dep/README.md). Build driver `dep/dep.py`, served via `Canto.dep()` and
  `dante-corpus text dep` (with `text np` gaining a derived `role=` per noun phrase). Artifacts
  built for all 100 cantos; `--check` reports **0 hard / 0 soft** violations — see
  [`dep/README.md`](dep/README.md)'s *Check* section and
  [`dep/CORRECTIONS.md`](dep/CORRECTIONS.md) for the full correction history.
- **Layer 5 — skeleton**: implemented, all 100 cantos built, checker refined through Phases 0-5q
  — the four mechanical phases (normalization, authority model, `--repair`,
  double-listing/elided-copula whitelist) plus Phase 5's rule series; see
  [`skel/README.md`](skel/README.md). `dante_corpus/skel.py` (dataclasses, role
  vocabulary, deterministic derivation, table parsing, validation, TSV I/O, serve-time joins),
  `dante_corpus/hashes.py` (content-hash versioning, all layers), `Canto.skel()`/`Canto.hashes()`
  in `api.py`, `dante-corpus text skel`/`dante-corpus hash` in `cli.py`, `skel/skel.py` (LLM
  build driver, mirrors `dep/dep.py`, plus `--stats`/`--repair` modes). `--check` across all
  three canticles reports **0 hard, 3633 soft** (3550 at the end of Phase 5; the case annex's
  step-4 slices added 5, removed 86 and added 165, and its step-5 `morph/` round removed 1, for
  the reasons recorded in
  [`skel/CORRECTIONS.md`](skel/CORRECTIONS.md) — the count measures divergence between two
  independent reads, so a correct Layer-4 round can move it either way)
  (down from 17438 at the first full-corpus
  measurement, 7776 at the Phase 4a checkpoint, 5919 after the Phase 4b `--fix` round) — see
  [`skel/README.md`](skel/README.md)'s *Check* section and
  [`skel/CORRECTIONS.md`](skel/CORRECTIONS.md) for the full correction history. Phase 5 (see
  [`skel/PLAN.md`](skel/PLAN.md)) is **complete**: its measured finding is that `--fix` yields a
  flat ~0.09-0.11 violations per LLM call regardless of how the flagged set is composed, so the
  residual was closed by deterministic checker rules and cross-layer corrections instead. Phases
  5a-5q landed (rules C/D/L/M/N/O/P/Q/R/S/T, two re-triage rounds, **two** full `--fix` passes,
  and the four
  Layer-4 correction rounds Layer 5's audit role produced — the clitic datives of Phase 5i, the
  `mark` mistags of Phase 5n, and Phase 5p's clausal complements and multi-edge deferrals; see
  [`dep/CORRECTIONS.md`](dep/CORRECTIONS.md)). `--fix` rounds are **LLM-regeneration work the
  user runs themselves** (`make -C skel fix`, run 3-way parallel); checker-side and audit work
  is the assistant's.

`grammar-stack-plan` was merged into `main` (fast-forward) and pushed; Layers 1–4 and their
artifacts now live on `main`.

**Next work**

**Nothing is blocking any more**, and the two remaining items are independent of each other.

#### 0. ~~Blocking — regenerate the 25 `case/` chunks~~ *(user — done 2026-08-02)*

```bash
make -C case clean && make -C case      # then: make -C case check   -> 0 hard
```

The `morph/` round had moved the pronoun scope (13112 → **13125** tokens, 13176 → **13189**
values), so 20 lines needed a different number of case values and `case --check` read 25 hard.
Every one was a `[count]` mismatch and **none was the model getting the Italian wrong** — the same
situation, and the same fix, as step 3's rounds 2 and 3.

**Run, and `--check` is back to 0 hard.** `--stats` runs again and reads **258 contradictions / 40
impossible pairings** (260 / 40 at step 4's close); the census gain is almost all `ablative`
(1805 → **1819**), the newly in-scope comitatives, and `genitive`/`locative` did not move. All five
layers and the tests were re-measured and only `case` changed — deltas in
[`case/CORRECTIONS.md`](case/CORRECTIONS.md)'s *the chunk regeneration the `morph/` round owed*.

#### Then, in any order — two items left, neither blocking the other

| # | item | who | note |
|---|---|---|---|
| 1 | **Layer 3's stale clitic mentions** (5 hard / 96 soft) | assistant | the stack's one open defect, described immediately below. A deterministic regeneration of the derived `+X` spans is the obvious instrument, but it moves the `np` content hash of every canto it touches, so the choice is **deliberately left to whoever picks it up** |
| 2 | ~~**Settle `locative`**~~ | assistant | **done 2026-08-02 — it is earned and stays.** No artifact moved and the vocabulary does not change. By deprel it opens no slot, but that is the wrong test: Layer 2's `lemma` collapses `locative`/`accusative`/`dative`/`reflexive` onto one `ci`/`vi` form, so this column is the only record of which reading a given `vi` has. The round recommended folding it first and was wrong — see [`case/CORRECTIONS.md`](case/CORRECTIONS.md)'s *Step 5 — the `locative` question* |
| 3 | **The `morph/` merge itself** | mostly user | its first item is a **blind regeneration of `case` under a corrected prompt**, fixing the two weaknesses slice 3 counted (the postposed subject, 78; the dative of possession alongside an explicit object, 24). The assistant can write the prompt; the calls are the user's. See [`case/PLAN.md`](case/PLAN.md)'s *The next action* |

The case annex's steps 1–4 are all complete — the blind corpus pass finished 2026-07-31 and is
frozen, the Layer-4 adjudication round closed 2026-08-01 with a verdict on every candidate, and
the owed `morph/` correction round closed 2026-08-02.

### Open item — Layer 3's clitic mentions are stale after the annex's `morph/` rounds

**`make -C np check` reports 5 hard / 96 soft. It is not a regression from any `np/` work and it
is not caused by step 4's `dep/` edits** (`np.py` imports `api`, `morph` and `np` only; the
figure is unchanged with the `dep/` changes stashed). It is fallout from the case annex's Layer-2
correction rounds — `880fc2e` and `a97b80e` in step 3, which retagged fused clitic clusters so the
case pass could validate, and the 2026-08-02 round in step 5, which took it from 3 hard / 64 soft
to its present figure by giving the 58 comitatives the lemma parts `me`/`con`. At the time
`morph`, `dep` and `skel` were all re-measured; **`np` was not**, and nobody noticed until the
whole stack was checked at the end of slice 3.

`np`'s checker derives the *expected* clitic mentions from Layer 2's lemma parts
(`clitic_mentions()` in `dante_corpus/np.py`, compared against the frozen `+X` spans), so moving
a lemma moves what `np` is required to carry:

- **96 soft — `token N 'W' missing clitic mention '+X'`.** The rounds *added* components to fused
  tokens (`sen` → `si+ne`, `cen` → `ci+ne`, `Vattene` → three parts, `meco` → `me+con`), so the
  frozen `np` artifacts are now missing mentions they were never asked for when they were built.
  By token: `sen` 42, `seco` 14, `meco` 7, `men` 6, `ten` 4, `gliel` 4, `vosco` 3, `teco` 3,
  `nosco` 2, `gliene` 2, `cen` 2, `Vattene` 2, `salsi` 1, `percosselo` 1, `nol` 1.
- **5 hard — a frozen `+X` span with no lemma component to justify it.** The mirror case. `nol`
  was relemmatized to `non+lo`, so `'+ne' not in lemma parts ['non', 'lo']` at *Purgatorio*
  16:139, 16:140 and 31:99 — all three *nol*, all three the same correction that closed a Layer-5
  membership violation during the annex's step 3. The 2026-08-02 round added two more of the same
  shape, `'+se' not in lemma parts ['sé', 'con']` at *Inferno* 24:23 and *Paradiso* 5:84, where
  `seco`'s lemma moved from `con+se` to the corpus's dominant tonic `sé`.

**Nothing here was fixed, and the choice of instrument is deliberately left open** — the mentions
are derived rather than authored, so a deterministic regeneration of the `+X` spans is plausible,
but that is a Layer-3 decision with a hash consequence for every canto it touches and it belongs
to whoever picks this up. What a new session should *not* conclude is that Layer 3 was mis-built:
it was correct against the Layer 2 it was built on.

The case annex's remaining work, on the branch `case-pilot`:

| step | what | who | state |
|---|---|---|---|
| 1 | kill-gate pilot — self-consistency on the disputed clitics vs a control | user ran the calls | **done, passed** (2026-07-30) |
| 2 | freeze vocabulary (`accusative`/`dative`/`ablative`/`nominative`/`genitive`/`locative` from the pilot census, plus `vocative` and `reflexive`) and scope (**all pronoun-POS tokens**, 13112 over 8540 lines); write the driver, `README.md`, `Makefile`, `dante_corpus/case.py` | assistant | **done** (2026-07-30) |
| 3 | blind corpus pass over the pronoun-bearing parse units (1340 calls), validate, **commit**, *then* join to `dep` via `--stats` | user ran the calls | **done 2026-07-31**, four runs — `--check` went 1236 → 70 → 13 → **0 hard**, and **no residue was ever the model getting the Italian wrong**: a driver abort, then two rounds of Layer 2 disagreeing with itself on how many pronouns a fused token holds. 13112 tokens frozen at `0027494`, before `--stats` was run |
| 4 | hand-verified Layer-4 correction round over the contradictions, `make -C dep check` staying 0/0 | assistant | **done, all three slices** — 215 positions / 270 rows, `dep --check` 0/0 throughout. Slice 1 (49 impossible pairings): 10 positions, **3550 → 3555, up** — why it went up is its main finding. Slice 2 (the **102** contradictions `skel` already flags): 81 positions, **3555 → 3469, −86**, against a predicted ≈90–100. Slice 3 (the **325** `skel` does not flag, 2026-08-01): 124 positions, **3469 → 3634, +165**, the predicted direction |
| 5 | re-measure Layer 5 per slice (done); settle the oblique tail incl. `locative` (done 2026-08-02); the owed `morph/` correction round and its regeneration (done 2026-08-02); the `morph/` merge | assistant | **partly done** — the tail's verdict is **fold nothing** (`ablative` and `genitive` earned by their deprels; `locative` settled 2026-08-02 on different grounds — it opens no slot, but it is the only record of which reading a `ci`/`vi` token has). The `morph/` round spent all 10 parked mistags plus the 58-token comitative family, moving the pronoun scope to 13125/13189 and leaving `case --check` at 25 hard over 20 lines — **since regenerated back to 0 hard**, 258 contradictions / 40 impossible pairings. What remains is the merge into `morph/`, whose first item is a **blind regeneration of `case`** under a prompt fixed for the two weaknesses slice 3 counted |

The scope in step 2 went to the whole pronoun population rather than the clitic subset the
adjudication strictly needs: it is read off Layer 2's own `pos` column, so it draws no line of its
own, it covers the tonic forms (`cui`, `me`, `lui`, `altrui`, `lor`) the disputed *mirror* bucket
contains, and it makes the case of every pronominal mention queryable. That cost 1340 calls
instead of ~446 — still under Phase 5q's `--fix` pass (1702). See
[`case/CORRECTIONS.md`](case/CORRECTIONS.md)'s *Step 2*.

The order in step 3 is load-bearing: generating blind and freezing *before* looking at `dep` is
what keeps the column a third independent read rather than an artifact manufactured to close
violations. Expected return is ≈90–100 of the 3551, not zero — see the follow-on paragraph below.

**Step 4's slice 1 corrected how that return should be chased, slice 2 collected it, and slice 3
spent the rest knowing it would not.** Layer 5's soft count measures divergence between two
independent reads, not correctness, so it falls only where a Layer-4 fix moves `dep` toward what
the Layer-5 LLM already said. The impossible pairings are the opposite configuration — `dep` and
`skel` agree and only `case` dissents — so correcting `dep` there *raises* the count, as it did
(3550 → 3555). The ≈90–100 figure was always drawn from the Phase 5h/5i population, where `skel`
**already dissents from** `dep`. **Slice 2 built that intersection and spent it**: 102 candidates,
81 Layer-4 errors (79%), **−86** — the estimate was accurate. **Slice 3 then worked the 325
contradictions `skel` does not flag**, the slice-1 configuration: 124 Layer-4 errors (38%) and
**+165**, in the predicted direction. The selector decided the sign three times out of three and
predicts yield as well — 79% inside the intersection against 38% and 20% outside. **3634 is a
worse number and a better corpus than 3469.** See
[`case/CORRECTIONS.md`](case/CORRECTIONS.md)'s *Step 4, slice 3* and
[`skel/CORRECTIONS.md`](skel/CORRECTIONS.md).

## Handing off — the state at the close of 2026-08-02

**Everything below is on the branch `case-pilot`.** This section is the entry point for a session
with no memory of the annex; it says what is true now, what to do next, and what not to re-open.
The deeper history is in *Resuming cold* below and in
[`case/PLAN.md`](case/PLAN.md)'s *Resuming cold — after step 4*.

### Confirm the state first — every figure here is a current measurement

```bash
git status --short          # expect clean
uv run pytest -q            # expect 138 passed
make -C morph check         # expect 0 hard, 0 soft
make -C np check            # expect 5 hard, 96 soft  -- the open defect, NOT a new break
make -C dep check           # expect 0 hard, 0 soft
make -C skel check          # expect 0 hard, 3633 soft
make -C case check          # expect 0 hard
make -C case stats          # 13125 tokens / 13189 values; 258 contradictions / 40 impossible
```

If `case` reads 25 hard the regeneration is not in the tree; if `skel` reads 3634 the
2026-08-02 `morph/` round is not; if it reads 3469 slice 3 is not.

### What closed on 2026-08-02, and is not to be re-opened

1. **The `morph/` correction round** — 10 hand-verified singletons plus the 58-token comitative
   family, 41 canto artifacts. `skel` 3634 → 3633.
2. **The `case/` chunk regeneration it owed** — 25 hard → **0 hard**. Scope 13112 → 13125 tokens,
   13176 → 13189 values; the census gain is almost all `ablative` (1805 → **1819**), the newly
   in-scope comitatives, which the new column tagged in agreement with an alias table it never saw.
3. **The oblique tail: fold nothing.** `ablative` earned (prepositional oblique, `obl` 82%),
   `genitive` earned (`det:poss`, a slot `ablative` fills zero times), **`locative` earned** —
   *not* by the deprel test, which it fails, but because Layer 2's `lemma` collapses
   `locative`/`accusative`/`dative`/`reflexive` onto one `ci`/`vi` form. `vocative` is the one
   remaining frozen-but-unearned value. **No rows were rewritten and the vocabulary does not
   change**, so the merge has nothing to carry from this.

**Two verdicts in this annex were reached and then reversed, both recorded in full** in
[`case/CORRECTIONS.md`](case/CORRECTIONS.md) — *The subset argument was wrong* (fold `genitive`)
and *Step 5 — the `locative` question* (fold `locative`). Read the second before proposing any
vocabulary change: its guard is that **before folding a value V, print the cross-tab of V's word
forms against every value they carry**, not V against its proposed parent. A deprel containment
test only answers "does this value open a slot", which is the wrong question for a value whose
work is splitting one form into several readings.

### The two open items

| # | item | who | the first concrete action |
|---|---|---|---|
| 1 | **Layer 3's stale clitic mentions** — `np --check` 5 hard / 96 soft | assistant | decide the instrument. The mentions are *derived* from Layer 2's lemma parts, so a deterministic regeneration of the `+X` spans is the obvious move, but it moves the `np` content hash of every canto it touches. That trade is **deliberately left open**; see *Open item* below for the token counts and why Layer 3 was not mis-built |
| 2 | **The case annex's `morph/` merge** | mostly user | write the corrected build prompt, then the user runs a **blind regeneration of `case`**. Two measured weaknesses to fix, both word-order rather than case: the postposed subject (**78**) and the dative of possession alongside an explicit object (**24**). The merge must also settle the **fused-token mismatch** — `case` annotates a pronoun and `dep` a token, and five contradictions are nothing but that (inferno 2:81.7 *aprirmi*, 23:128.7 *dirci*; purgatorio 8:45.4 *vedervi*, 14:20.1 *dirvi*; paradiso 29:92.1 *seminarla*) |

Neither blocks the other. Item 2 is the annex's own next step and item 1 is a Layer-3 decision
that happens to have been caused by it.

### What must not be done

- **Do not edit `case/*.tsv` to close a contradiction.** The artifact stays frozen; it was held
  through 194 recorded `case`-side errors across step 4's three slices, and the corrected column
  comes from item 2's blind regeneration, never from a hand edit. The 258 remaining contradictions
  are measured residue with a verdict, not unfinished work.
- **Do not run another Layer-4 slice over them.** All 510 original candidates have a verdict, and
  the two slices that sampled this configuration found `case` was the wrong read 24% and 53% of
  the time. The next instrument is the regeneration.
- **Do not treat Layer 5's soft count as the objective.** It rose 5, fell 86 and rose 165 across
  three correct rounds. None of those numbers decided whether an edit was right.

### Resuming cold — the case annex, as of 2026-08-01

**For the next action specifically, read [`case/PLAN.md`](case/PLAN.md)'s *Resuming cold — after
step 4* first.** It is self-contained: the commits that matter, the state check with its expected
figures, what step 4 settled so none of it is re-litigated, the selector and its measured limits,
and the traps the three rounds hit. This section below carries the step-1-to-3 history.

**Step 2's code is committed (`637d417`) and step 3's artifact is committed separately
(`0027494`).** The branch is `case-pilot`. The split was deliberate and is the step-3 order made
literal: the artifact was held untracked until `--check` reached 0 hard, and committed **before**
`--stats` joined it to `dep`. Confirm the state before assuming it:

```bash
git status --short          # expect clean
uv run pytest -q            # expect 138 passed (125 before the annex)
make -C morph check         # expect 0 hard, 0 soft
make -C np check            # expect 5 hard, 96 soft  -- the open item above, NOT a new break
make -C dep check           # expect 0 hard, 0 soft
make -C skel check          # expect 0 hard, 3633 soft (3634 before the 2026-08-02 morph round)
make -C case check          # expect 0 hard  -- regenerated 2026-08-02
```

Committed in step 2 — new: `dante_corpus/case.py`, `case/case.py`, `case/README.md`,
`case/Makefile`, `tests/test_case.py`; modified: `dante_corpus/_paths.py` (`CASE_DIR`),
`hashes.py` (`"case"` **appended** to `LAYERS`), `api.py` (`Canto.case()`), `cli.py`
(`text case`), `tests/test_hashes.py` (isolate `CASE_DIR`), plus this file,
[`case/PLAN.md`](case/PLAN.md) and [`case/CORRECTIONS.md`](case/CORRECTIONS.md).

**What the user ran.** `make -C case` — the blind corpus pass, resumable from its own output,
three canticles runnable in three parallel shells. LLM-scale generation is the user's job by the
convention Phase 5 settled (cf. `make -C skel fix`), and it took **four runs**, all on
2026-07-31, taking `--check` from **1236 hard to 70 to 13 to 0**. **Not one residue was the model
getting the Italian wrong**:

1. A driver bug — an unrecoverable chunk aborted every remaining chunk of its canto, so ~23
   genuine failures cost 192 of the 1340. The driver now skips the chunk and carries on, and
   `--log` keeps the responses that failed.
2. **Layer 2's `pos` undercounting its own `lemma`** on 24 fused clitic clusters (`sen` = `si+ne`,
   tagged `pronoun` here and `pronoun+pronoun` 15 times elsewhere), rejecting a correct answer
   forever.
3. The same defect in shapes round 2 did not cover — the lemma undercounting too (`sen` with the
   lemma `si`), a three-part lemma under a two-part `pos` (`Vattene`), and `nol` = `non lo`
   demanding two cases for one pronoun. 14 more tokens, audited as a family rather than as
   symptoms.

Both correction rounds are in [`morph/CORRECTIONS.md`](morph/CORRECTIONS.md), with
`morph`/`dep`/`skel` re-measured at 0/0, 0/0 and **0/3550** — the last one moved because a `nol`
mistagged `adverb+article` was also the cause of a Layer-5 membership violation, so the annex had
audited Layer 2 before its `dep` join was looked at at all. Run 4 re-requested the last 12 chunks
and all validated; see [`case/CORRECTIONS.md`](case/CORRECTIONS.md)'s *Step 3 corpus pass*
entries.

**The finish sequence was executed in this order**, because the order is the annex's whole value:
`--check` at 0 hard → **commit the artifact** (`0027494`) → *then* `--stats`. Freezing precedes
the join to `dep`; doing it the other way round manufactures the column to close violations,
which is the failure mode [`case/PLAN.md`](case/PLAN.md)'s *Independence* section forbids.
**Step 4** — the hand-verified Layer-4 correction round over the contradictions, verified against
the terzine one at a time with `make -C dep check` staying 0/0 — then ran to completion over
2026-07-31 and 2026-08-01.

**The census, over 13112 tokens / 13176 values**: `nominative` 5620 (42.7%), `accusative` 2003,
`reflexive` 1961, `ablative` 1805, `dative` 1409, `genitive` 267, `locative` 81, `vocative` 30.
**The join to `dep`**: `obj`→`accusative` 84% (1631/317), `iobj`→`dative` 94% (669/46),
`nsubj`→`nominative` 98% (5076/98) — **461 contradictions and 49 impossible pairings**, step 4's
input. After all three slices those rates are **90% / 96% / 99%** and the list is **260 / 40**;
after the 2026-08-02 chunk regeneration they read **90% / 97% / 99%** and **258 / 40**.
The disagreement concentrates exactly on `obj`, the accusative-vs-dative class the annex
was built to adjudicate, which is the pilot's finding reproduced at corpus scale.

**The three parked questions are now answered**, with their measurements in
[`case/CORRECTIONS.md`](case/CORRECTIONS.md):

- **The oblique tail: fold nothing.** The deciding evidence is the `dep` deprel distribution,
  not the word forms. `ablative` (1805) is `obl` at 82%. **`genitive` (267) is earned** — 71% of
  it is adnominal (`nmod` 139, `det:poss` 50) and `det:poss` is a slot `ablative` fills zero
  times: `lor danno`, `il senso lor`, `le gambe loro` are possessive determiners, not obliques.
  **`locative` (81) is earned** — settled 2026-08-02, but **not** by the deprel test, which it
  fails: there is no relation `locative` fills that `ablative` does not. What earns it is that
  Layer 2's `lemma` collapses the readings of `ci`/`vi` (lemma `vi` spans `locative` 44 /
  `accusative` 21 / `dative` 15 / `reflexive` 4), so whether a given `vi` is *there* or *to you* is
  recorded nowhere else in the stack. A containment test can only answer "does this value open a
  slot"; for a value that splits one form into several readings, that is the wrong question, and
  the round recommended folding `locative` before seeing it. `vocative` (30) is frozen-but-unearned; `reflexive` (1961) is vindicated, and
  mistagging it was what the Inferno 1 smoke test caught. **An earlier reading of this tail
  recommended folding `genitive` and was wrong** — see [`case/CORRECTIONS.md`](case/CORRECTIONS.md)'s
  *The subset argument was wrong*. No rows were rewritten.
- **The third adjudication class is real** — relative pronouns that are the subject of their
  clause, read `nominative` by `case` and `obl` by Layer 4, **49 corpus-wide**. It is step 4's
  first and highest-yield slice, because the pairing is one neither layer can be right about
  together.
- **Layer-2 mistags this annex surfaced**, belonging to `morph/` and deliberately not acted on
  during the pass: the comitatives `meco`/`teco`/`seco`, tagged four different ways with `vosco`
  twice as `adjective` (once with the lemma `boscoso`), and `me'` (apocopated *meglio*) tagged
  `pronoun` at Inferno 1:112. **All of these were corrected on 2026-08-02**, together with the six
  more step 4 added — and sweeping each reported form corpus-wide found the reports had
  undercounted twice over: **both** corpus `me'` tokens are *meglio* and **both** `salsi` tokens
  are the same *sapere* idiom, and the comitatives are **58 tokens under 34 distinct taggings**,
  not 43 under four. See [`morph/CORRECTIONS.md`](morph/CORRECTIONS.md)'s *The mistags the case
  annex surfaced and parked*.

**Why Inferno 1 was built alone first.** It was the plumbing smoke test, and it earned its
keep: `--check` passed at 0 hard while the artifact was wrong in two ways the checker
structurally cannot see — the prompt's own worked example taught `accusative` for the reflexive
`mi ritrovai`, and the reflexive/impersonal clitic (1411 tokens, **10.8%** of the scope) had no
home in the seven-value vocabulary. Both were fixed (`reflexive` is now an eighth value) and the
canto rebuilt. The lesson generalizes: for this layer, **`--check` passing is not evidence the
artifact is right** — cross-tabulate against `dep` before trusting a batch.

Layer 5 Phase 5 closed at **0 hard, 3551 soft** (see
[`skel/PLAN.md`](skel/PLAN.md)'s *Where Phase 5 ended*): Phase 5o closed the last open row of the
`extra_arg` direct-child triage (`advcl`), Phase 5p ran the two hand-verified `dep/` correction
rounds its verdicts left over (−10), and Phase 5q spent the one remaining item — the user-run
`--fix` pass (−147, ≈28 h 3-way parallel) — plus a mechanical `ioj` → `iobj` typo fix (−4) that
took `unknown_role` to 0. What remains is documented reading disagreement between two independent
parses: `extra_arg` (1639) and `missing_arg` (1193) are 80% of it, and both regeneration and
deterministic rules now have a measured stop verdict against them.

**One follow-on is open, past its kill gate**: [`case/PLAN.md`](case/PLAN.md), a
**pronoun case annex to Layer 2** — the instrument Phase 5i/5h's parked verdicts named. It is the
sibling directory `case/`, not a new column in `morph/*.tsv`, so no existing artifact hash moves;
it is authored blind to the disputed positions so it stays a genuine **third independent read**;
and its contradictions with `dep` feed a hand-verified Layer-4 correction round rather than a
checker exemption. Its first step was a **kill-gate pilot** measuring whether the model agrees
with itself on the disputed clitics at all, and that pilot **ran on 2026-07-30 and passed**
(570 calls, `google:gemma-4-31b-it`, on the branch `case-pilot`): **81%** unanimity across three
presentation variants on the disputed positions with **zero** three-way splits, against **95%**
on a control group of undisputed clitics, and answers that split both ways against `dep` rather
than restating either existing read. Step 2 then froze the vocabulary at the census's own six
values plus `vocative` (which the clitic-only pilot population structurally could not produce)
and `reflexive`, and the scope at every pronoun-POS token, and wrote the driver, the shared
module (`dante_corpus/case.py`), `Canto.case()` / `dante-corpus text case`, and the tests;
step 3's corpus pass completed on 2026-07-31 at 0 hard and is frozen. Measurement in
[`case/CORRECTIONS.md`](case/CORRECTIONS.md), design in [`case/README.md`](case/README.md). Expected value is stated up front as
**≈90–100 of the 3551** — it does not reach zero, and the rest of the residual (subject
resolution across enjambment and pro-drop) is untouched by it. The paired proposal, a **verb lexicon** for the
complement-vs-adjunct distinction, stays **rejected**: it would import an external authority,
which the *Neutrality audit* invariant below forbids. (A case pass does not — that invariant
constrains the build prompt's *inputs*, and an LLM reading case from the Italian alone meets it
on the same terms `pos` and `deprel` already do.)

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

**Annex built (pilot passed, driver written, corpus pass complete and frozen)**: pronominal **case**,
the one morphological feature this layer omits and the instrument Layer 5's parked clitic
verdicts named. Built as the sibling directory `case/` rather than a new `morph/*.tsv` column, so no
existing artifact hash moves and the experiment stays revertible; merging into Layer 2 is the
natural end state if it proves out. Scope is every pronoun-POS token, decided from this layer's
own `pos` column; the vocabulary is the six values of the pilot's answer census plus `vocative`
and `reflexive`, the two that name a pronoun filling no argument slot. See
[`case/README.md`](case/README.md) and [`case/PLAN.md`](case/PLAN.md).

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
  not something the Italian line determines. Note the contrast with the proposed case annex
  ([`case/PLAN.md`](case/PLAN.md)), which asks a model to *read* the source rather than importing
  a dictionary, and so satisfies the *Neutrality audit* invariant below.

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
   `skel/skel.py`), all 100 cantos built, checker refined through Phases 0-5q
   (`--check`: 0 hard / 3633 soft — 3551 until the case annex's `morph/` rounds, then 3550,
   3555, 3469 and 3634 across step 4's three slices, then 3633 after step 5's `morph/` round).
   Phase 5 closed
   with every route measured; see
   [`skel/PLAN.md`](skel/PLAN.md) and [`skel/README.md`](skel/README.md).

5. **Pronoun case annex** — *pilot passed, driver written, corpus pass complete and frozen*
   (`dante_corpus/case.py` + `case/case.py`; [`case/README.md`](case/README.md),
   [`case/PLAN.md`](case/PLAN.md), branch `case-pilot`). Not a sixth layer: a Layer-2
   morphological feature held in its own directory, worth ≈90–100 of Layer 5's 3551 soft
   violations and useful to consumers on its own terms. The kill-gate pilot ran over the rebuilt
   population (67 + 28 disputed, 95 control) and passed; step 2 froze the vocabulary and scope
   and built the driver and serve surface; step 3's corpus pass built all 100 cantos at **0
   hard**, 13112 pronoun tokens, and froze them; step 4 spent all **510** candidates across three
   slices on **215 hand-verified positions / 270 rows** in `dep/`, taking Layer 5 to **3634**; step
   5's owed `morph/` correction round then landed on 2026-08-02, taking it to **3633** and leaving
   `case --check` at 25 hard, since regenerated back to **0 hard**; with `locative` settled, the
   one open item is step 5's `morph/` merge. The code and the artifact are committed **in that
   order, deliberately** — see *Resuming cold* above.

Build alongside the existing assets, gate each layer on its checks, then expose through the API.
Layers 1–5 are implemented, built for all 100 cantos, and merged to `main`; the grammatical
stack this plan describes is complete. What remains is all on the branch `case-pilot`: **nothing
is blocking**, and the two open items are Layer 3's stale clitic mentions (5 hard / 96 soft — see
*Open item* above, untouched) and the case annex's `morph/` merge. The annex's kill gate passed,
its corpus pass is complete and frozen, its Layer-4 adjudication round is complete, its owed
`morph/` correction round is closed and regenerated, and both of step 5's analysis sub-items —
the oblique tail and `locative` — are settled. See *Handing off* immediately below.
