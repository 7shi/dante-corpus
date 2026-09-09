# Manual generation-2 Layer-2 corrections

> [!NOTE]
> **This file records manual corrections only** — edits made by hand, directly in a
> committed `layers/l2/<canticle>/NN.tsv`, with no model call. It is a history of
> human judgments applied to the artifact, one entry per position.
>
> **It is not a changelog for the layer.** A correction that comes from changing the
> *mechanism* — a prompt fix, a gate rule, a new tag, a re-run under a different
> contract — does not belong here, however many positions it moves. Those changes are
> argued in [`../L2.md`](../L2.md) and recorded in [`../PLAN.md`](../PLAN.md)'s
> handoffs, and their effect reaches the artifact by regeneration, not by editing.
>
> **This file describes the artifact that is on disk, so a regeneration rewrites it**
> (operator, 2026-09-10). A re-run does not reliably reproduce the same mistakes at the
> same positions, so an entry naming a position the new artifact gets right is describing
> nothing and is dropped; an entry whose problem survives is carried forward, re-verified
> against the new file. What was deleted is not kept here as history — the argument for
> each decision lives in `../L2.md`, which is where it survives a rewrite. Git holds the
> previous versions of this file for anyone who needs them.

Generation-2 Layer 2 (`layers/l2/`) is build-time output — one model call per chunk of
lines, gated at the runtime, written to `layers/l2/<canticle>/NN.tsv` (`line`,
`l1_index`, `l2_index`, `text`, `pos`). The gate enforces the *shape* of an answer: one
row per token in the order given, a single word that is the token or the token with its
dropped letters put back (`is_restoration`), and one closed-set tag per word. It cannot
catch a row that is structurally clean and linguistically wrong.

Hand-editing the artifact is adopted deliberately (operator, 2026-09-09, argued in
[`../L2.md`](../L2.md)): steering a one-shot prompt toward a known answer and correcting
that answer afterwards put the same human judgment into the corpus by two different
routes, and only the second one leaves a record. This file is that record.

**Methodology, inherited from the four per-layer files that precede it**
([`../../morph/CORRECTIONS.md`](../../morph/CORRECTIONS.md),
[`../../dep/CORRECTIONS.md`](../../dep/CORRECTIONS.md),
[`../../case/CORRECTIONS.md`](../../case/CORRECTIONS.md),
[`../../np/CORRECTIONS.md`](../../np/CORRECTIONS.md)): classify by cause before touching
anything, verify each row against precedent elsewhere in the corpus before applying it,
and re-run the layer's `--check` afterwards. Old Layer 2 (`morph/`) is cited here as
**precedent, never as authority** (premise 1) — where this artifact departs from it on
purpose, the entry says so.


## 3 rows, *Inferno* 1's third run under the participle-reason prompt (2026-09-10)

*Inferno* 1 was regenerated a third time (`--force`, `google:gemma-4-31b-it`), this time
under the prompt that states the participle convention's *reason* rather than a bare
prohibition (`../L2.md`, *The eleventh tag, declined*). Every prior entry in this file
was checked against the new artifact first: **`poco` 1:7, `brame` 1:49, `tutte` 1:49,
`Molti` 1:100, `imperador` 1:124, `disperate` 1:115 and `dolenti` 1:116 are all correct
unaided this run** and are dropped, per this file's own rewrite rule — describing a
position the artifact now gets right describes nothing. `me'` 1:112 survives, re-verified
against the same argument as before. Two new entries, `pel` 1:33 and `dipartilla` 1:111,
are added — not because the mechanism regressed, but because it is now clear it never
fully closed (`../L2.md`, *A third run: the participle reason holds, `pel` and
`dipartilla` wobble*): both positions had read correctly in each of the two prior runs,
and both flipped to the wrong answer in this one, under a prompt that names neither word.
Repeated runs detect disagreement, they do not verify correctness — the same lesson the
tag column already carried is now confirmed at the two positions that most needed it.

Applied to `layers/l2/inferno/01.tsv` (the third run's artifact, as the model produced
it). `--check` before and after the batch:

| | splits | tags | restorations |
|---|---|---|---|
| before | 505 agrees, 6 differs, 0/0 | 947 of 987 (95.98%) | 142 positions, 73 distinct |
| after | **507 agrees, 4 differs, 0/0** | **950 of 989 (96.06%)** | **144 positions, 75 distinct** |

### A restoration the gate refused and the model then declined to make

**inferno 1:112 `me'`** — `me'` / `pronoun` → `meglio` / `noun`. "*Ond' io per lo tuo
**me'** penso e discerno*": for your good. The model answered a truncation the gate
correctly refused as not a restoration, and the retry left the token whole rather than
restoring it correctly. `meglio` passes `is_restoration` (the apostrophe opens the end,
and `me` reads straight through `meglio`). Old Layer 2 records lemma `meglio`, `noun`
m. sg., note `apocope` — the nominalised comparative, not the pronoun *me*. Present in
all three runs so far.

### Systematic, not random: two positions the mechanism was supposed to close

**inferno 1:33 `pel`** — `per`+`il` → `pelo` (unsplit), `noun`. "*che di **pel** macolato
era coverta*": covered with spotted fur. `pel` is the noun *pelo* (fur) in all 7
corpus-wide occurrences and never a contraction — the split-only pass agreed with itself
three times on `per`+`il` (`../L2.md`, *Is a `differs` random or systematic?*), and the
merged pass's contentful POS column was built specifically to make that split unwritable
(a preposition immediately followed by another preposition and an article, with
`macolato` left with no noun). It did so **twice** and then produced the old wrong answer
a third time, so the guard is real but not reliable — the failure is the model's sampling,
not the mechanism's design. `macolato` itself is untouched by this entry: it reads `verb`
in this run, which is the participle convention working correctly (old Layer 2's
`adjective` is the encoding this pass departs from on purpose), not a side effect of the
`pel` fix.

**inferno 1:111 `dipartilla`** — unsplit `verb` → `dipartì`+`la` (`verb`+`pronoun`). "*là
onde 'nvidia prima **dipartilla***": whence envy first drove him away. Old Layer 2 records
this lemma as **remote past** (`dipartì`), not present subjunctive (`diparta`) — confirmed
twice over, by the three-run check's 2:1 majority under the split-only pass and
independently by `01-4.tsv`'s restoration run (`../L2.md`, *Is a `differs` random or
systematic?*, *`01-4.tsv`*). The merged pass had reproduced this correct split-and-lemma
reading in both prior runs; this run left the token whole instead, the same
"differs"-shaped regression as `pel` and, by the argument above, evidence of the same
cause — sampling variance at a position the mechanism has already gotten right more than
once, not a new defect to design against.
