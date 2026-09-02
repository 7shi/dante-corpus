# Stage 7 — Refactoring (opened 2026-09-02, CLOSED 2026-09-03)

Opened by the operator on Stage 6's close and **closed on S7.2's live
confirmation** (2026-09-03, operator's decision): both of the stage's two items
shipped, and the live inferno-1 re-run that was the last outstanding check
passed. Unlike every earlier close, this one does **not** open the next stage's
document — Stage 8's scope is the operator's to decide, and §4 below is what it
inherits.

Opening this document is what closes Stage 6 on S6.11. The operator's decision
of 2026-09-02 re-scoped Stage 7: it is **a refactoring stage**, not level 2 of
the soft-divergence reduction. Level 2 keeps its candidates and eligibility list
in [`STAGE6.md`](STAGE6.md) §3 and waits for a stage of its own; nothing about
that analysis is invalidated by the delay.

---

## 1. Scope & why now

Six stages of live-run work left the harness working but top-heavy. Two weights,
and **only** these two — the stage is deliberately narrow (operator's decision,
2026-09-02, on seeing where the third was heading):

1. **The agent's domain knowledge is hidden inside Python string literals.**
   `runner/prompts.py` held the role framing, the skeleton row conventions and
   the whole 5-step reasoning protocol as module constants. Prompt wording is
   the most consequential thing in the project and it was the least reviewable:
   a change to it looked like a code change, and no run recorded which wording
   it ran under. (**S7.1, done.**)
2. **`extractor/reconstruct.py` is 1,928 lines** carrying the canto loop, fix
   planning, salvage, the TSV artifact, the gold face, reporting and the CLI in
   one module. (**S7.2, done.**)

A third candidate — generalizing the `harness/` ↔ `dante_corpus/` transcription
check S6.10 opened — **was investigated and then re-scoped out to Stage 8 or
later**, because it turned out to raise an authority question rather than a
tidying one. The measurement is recorded in §4 so it need not be redone.

Nothing here changes what a run produces. The stage's standing rule: **every
refactoring step must be argued to be behaviour-neutral, and where the output is
prompt text, proven byte-exact.** Standing Invariant §6 makes session semantics
a run-scoped constant; a refactor that quietly reworded a prompt would break
that invariant while looking like tidying.

## 2. The Warp self-improving-agent pattern: what applies, what does not

The stage opened from a review of [Warp's self-improving agent
pattern](https://claude.com/blog/how-warp-builds-self-improving-agents-on-claude)
(operator's reading note, 2026-09-01): an **inner/base skill** holding domain
knowledge as plain files, **human feedback** on the agent's output, and a
scheduled **outer/improver skill** that reads the accumulated feedback and
proposes a small edit to the base skill, merged by a human through the normal
review workflow.

The mapping onto this project is unusually clean in one direction and blocked in
another, and both halves are worth recording.

**What this project already has.** The article's own checklist asks "Is your
domain verifiable? Build the verification harness first, then let the agent tune
against it." That is what `harness/` is: `validate.py` / `derive.py` as the
contract, `recon/check.py` for hard and soft findings, `recon/agree.py` for the
gold readout, and a structured human-feedback channel that predates the article
(`upstream_feedback`, Standing Invariant §4.4 — 31 records still awaiting
triage). The heavy prerequisite is done.

**What blocks the loop itself.** Three constraints the Warp pattern does not
have to carry:

- **Gold cannot be the improver's signal** (Standing Invariant §1). The richest
  available "reaction" to an agent's output is its diff against gold, and tuning
  the prompt on that is teaching to the test — it voids Stage 1's micro F1,
  S4.3's verify-gold readout and `agree.py` at once. An improver here may read
  only `validate.py` / `derive.py`-derived signal: hard and soft findings,
  refusal reasons (S6.8), schema verdicts.
- **The autonomy premise** (§1 of [`PLAN.md`](PLAN.md)). A frontier model
  rewriting the local model's prompt is uncomfortably close to the Phase 5–8
  rails this project exists to replace. The distinction that can be defended:
  those rails were *deterministic corrections applied to the output*, whereas an
  improver edits *the wording the local model reasons from* and leaves the
  reasoning to it. Defensible, but only if the improver's edits are justified
  from the layer's published contract — the same authority bar discipline 3
  already sets for any deterministic rule.
- **Feedback volume.** Warp's loop runs across hundreds of contributors and
  thousands of reviews. Here there is one operator. The article's own
  "quality > volume" note covers this, and `upstream_feedback` is already the
  low-friction channel; no new collection mechanism is needed or wanted.

**Decision (2026-09-02):** the improver loop is **not** in Stage 7. What Stage 7
takes from the pattern is its two prerequisites — knowledge in plain files, and
a reusable observer that reads contract-derived signal. Whether an improver ever
runs is a later design question that must first answer, at S6.1's level of
rigour, what signal it is allowed to read.

The article's other transferable advice — *write principles, not rules*,
*explain the why*, *keep skills small with progressive disclosure* — is
absorbed as the stage's editorial standard for prompt and refusal text, not as
a separate deliverable. `runner/tools.py`'s refusal messages already largely
meet it (they name the clause and the reason); S6.8 moved refusal logging the
same way.

---

## 3. Milestone Ledger

### S7.1 — The agent's knowledge becomes files (2026-09-02)

**What shipped.** `harness/skills.py`, a task-agnostic loader for file-based
skills: a directory holding a `SKILL.md` (frontmatter naming the skill and
declaring its resources, then a body that is prompt text verbatim) plus the
sibling `.md` resources the frontmatter declares. `runner/prompts.py`'s four
knowledge constants moved out into `runner/skills/grammar-agent/`:

| File | Was |
|---|---|
| `SKILL.md` (body) | `ROLE_INTRO` — role framing + skeleton row conventions |
| `protocol.md` | `STEPS_1_TO_4` |
| `step5-unit.md` | `STEP5_UNIT` |
| `step5-predicate.md` | `STEP5_PREDICATE` |

`prompts.py` keeps every public name (the constants now load from the skill) and
is otherwise reduced to assembly: which sections a workflow gets and in what
order. No dependency was added — the project still has exactly one — because the
frontmatter parser handles only what a skill header needs: scalars and one level
of nested mapping.

**Why files.** Prompt wording is domain knowledge, not code. As files it diffs
on its own and reviews on its own, and the body is stored **exactly as the model
receives it**, so what a reviewer reads is what the model reads. This is the
prerequisite the Warp pattern rests on ("because skills are plain files, agents
are extremely good at updating them"), but it pays off with no loop attached:
prompt changes stop hiding inside code changes.

**Byte-exactness, proven.** All eight assembled outputs — the four sections, the
two protocol compositions, and `system_prompt()` for both workflows — were
captured before the move and compared after: identical, byte for byte
(`system_prompt` unit 9,259 B, predicate 9,639 B). The refactor is therefore
provably neutral with respect to Standing Invariant §6, rather than merely
believed to be.

**Runs now record their wording.** `prompts.skill_digest()` fingerprints the
skill directory, and every `canto_complete` record carries it as `skill_digest`.
§6 fixes a run's semantics for its whole duration; until now nothing in the log
let that be checked afterwards, or told two runs' records apart when the wording
genuinely had changed between them. Canto-scoped like every other record.

**Tests.** `tests/test_harness_skills.py`, 12 tests: the loader refuses an
incomplete skill (missing `name` / `description`, a declared resource that is not
on disk, a document with no frontmatter, a missing directory) and refuses to
serve an **undeclared** file sitting beside `SKILL.md` — the frontmatter is the
manifest, so a stray file is a mistake rather than a silent extension point. The
digest is stable across loads and moves when any file's wording moves. On the
grammar skill itself: every section of the assembled prompt traces back to a
file, and the two workflows differ by exactly their Step 5. Suite **987 passed**
(975 + 12).

**Falsification.** This record would be wrong if the move had changed what the
model sees — the eight-way byte comparison is what rules that out, and the
assembly tests are what keep a future edit from reintroducing grammatical text
into `prompts.py`. It would also be wrong if the digest were decorative: it is
written into every `canto_complete`, so the next corpus run's log carries it
whether or not anyone reads it.

**Not done here.** `toolcall/prompts.py` (the XML wire contract and the tool-spec
renderer) stays as Python. It is the protocol library's own text, and §3's
separation of concerns keeps `toolcall/` layer- and task-agnostic; folding it
into a grammar skill would blur that boundary. Moving it into a *protocol* skill
is a legitimate later step, not this one. Progressive disclosure — having the
agent look up a convention through a tool instead of carrying all 9 KB on every
call — is now possible and is deliberately **not** taken here: it changes what
the model sees, so it is a measured experiment (S3.7's territory), not a
refactor.

### S7.2 — `reconstruct.py` splits along its own seams (2026-09-03)

**What shipped.** The 1,934-line module became seven, each named for the one
responsibility it holds. Nothing was rewritten: every function and class moved
verbatim, and `reconstruct.py` keeps the whole public surface it exported before
(`__all__` unchanged, plus the re-exports `harness/recon/convert.py` and
`repair.py` import).

| Module | Lines | Holds |
|---|---|---|
| `layers.py` | 162 | `CantoLayers` + gates 1-2 (`build_rows`, `validate_rows`) |
| `outcome.py` | 199 | `UnitOutcome`, `CantoReconstruction`, unit-level resume |
| `artifact.py` | 180 | `render_tsv` + `TsvArtifact` — the durable artifact |
| `fixrun.py` | 381 | the Stage-6 `--fix` machinery (plan, verdict, salvage, revert) |
| `goldeval.py` | 133 | the evaluation face — **the only module that opens gold** |
| `report.py` | 185 | `ReconstructReport` + `load_log` |
| `reconstruct.py` | 907 | the canto loop, gate 3 (`commit`), the CLI |

The dependency order is strictly downward — `layers` → `outcome` → {`artifact`,
`fixrun`, `goldeval`} → `report` → `reconstruct` — so no module imports one that
imports it back, and each is importable on its own.

**Why this is more than tidying.** The row that matters is `goldeval.py`. The
execution and commit faces now import nothing from the module that reads gold,
so Standing Invariant §4 item 1's boundary is a **file boundary rather than a
comment**: it can be checked by reading an import list instead of by trusting a
docstring. That boundary was already adversarially tested; it is now also
structurally obvious.

Four private helpers became public where the split made them shared
(`_validate_rows` → `layers.validate_rows`, `_violation_record` →
`violation_record`, `_final_validation_errors`, `_replay_unit_outcome`,
`_refusal_note`, `_fix_summary_line`) — a name crossing a module boundary should
not be spelled private. `reconstruct._validate_rows` is kept as an alias so the
name the pipeline carried still resolves. Two dead imports (`os`, `tempfile`)
went with the move.

**Neutrality, as the stage requires it argued.** Three pieces of evidence, none
of them a code read:

- the suite passes **987, unchanged** — the same count, the same tests, not one
  of them edited (they drive the CLI, the fix run, resume, salvage and commit
  through `rc.<name>`, so the re-exports are exercised rather than assumed);
- `make check` exits 0 at **0 hard / 4,627 soft**, the corpus number unmoved;
- `--help` is **byte-identical** to the pre-split module's, which is the CLI
  surface the operator and `recon/Makefile` actually drive.

**Falsification.** This record would be wrong if any behaviour had moved with
the code. The three readouts above are what rule that out at the level the stage
asks for; the operator's live inferno-1 re-run (delete the canto's TSV, run it
through the real fallback) is the remaining check that the *live* path — the one
no test touches, because nothing in the suite reaches a model — still behaves.
It had not been run when this record was written; it has been run since, and the
readout is below.

**Live confirmation — the operator's inferno-1 re-run (2026-09-02 18:10 →
19:39 UTC, folded in 2026-09-03).** TSV and log were swept first, so the
telemetry covers exactly one run. The live path behaves:

- **It ran.** 34 units, contiguous over lines 1–136 with no span gap, routes
  `agent` 33 / `fast` 1, 105 `llm_request`/`llm_response` pairs, 34
  `--verify-gold` `gold` records, 89 minutes wall clock (`fallback_seconds_total`
  5,334.6, max 389.2), `api_retries` 3 / 117.0 s.
- **The canto came back equivalent, not identical.** `git diff --stat` is 50
  insertions / 48 deletions on `harness/recon/inferno/01.tsv`, which is the
  expected unit-level variation of a live model (inferno 1 was re-run before, at
  S5.6), and *not* a structural change: 34 units all present, rows in
  non-decreasing `(line, token)` order, 6 fields on every one of the 449 lines,
  the same 13 sentinel rows over the same 136 source lines, and the log's 435
  `row_keys` matching the TSV's 435 role-bearing rows exactly in both directions.
- **The log carries the whole contract.** Every `unit` record has `row_keys` and
  its gate verdicts; one `canto_complete` with `skill_digest`
  (`b16c0639…397ffa`), `elapsed_seconds` and `api_retries`; `summary` last.
- **`make check` still 0 hard**, and soft moved as a live run may: this canto
  46 → 43, corpus-wide 4,627 → **4,624**.

Gold agreement for the canto fell, 0.7780 → 0.7582 F1 (rows 432 → 435, tp
319 → 312) — read as a readout after the fact, per §4 item 1, not as a criterion:
the same run that lost 7 TPs cleared 3 soft findings, which is the Stage-5
finding that hard-clean and gold-close are different targets showing up again at
canto scale.

**Not done here.** No behaviour was added, removed or reordered, so nothing in
the log contract, the gates, or the fix verdicts changed. `hybrid_engine.py`
(the other large extractor module) was not touched: it is Stage 2's, not this
stage's scope, and no one asked for it.

---

## 4. Stage close & what carries forward

**Closed 2026-09-03.** Both items are done and committed: **S7.1** (the agent's
knowledge as files under `runner/skills/grammar-agent/`, byte-exact, with
`skill_digest` in every `canto_complete`) and **S7.2** (the `reconstruct.py`
split into seven modules, live-confirmed on the operator's inferno-1 re-run).
That is the whole of the stage; no S7.3 exists and nothing is in flight.

State at close — the baseline the next stage starts from:

- suite **987 passed** (975 + 12 from S7.1; S7.2 added none and edited none);
- corpus **0 hard / 4,624 soft**, `make check` exits 0 (4,627 before S7.2's live
  re-run moved inferno 1 from 46 to 43 soft);
- the live path is confirmed working after the split, on real fallback traffic.

Three items carry forward, none of them Stage 7's to answer:

1. **The transcription-drift check** — investigated here, re-scoped out; the
   measurement and the three options are below, so the next stage starts from
   numbers rather than a repeated sweep.
2. **Soft level 2** — still a design question before it is a run. Candidates and
   the eligibility list stay in [`STAGE6.md`](STAGE6.md) §3, unchanged and
   uninvalidated by the delay; any class must be argued to one of that stage's
   three outcomes from `validate.py` / `derive.py` with gold unopened.
3. **The standing authority question** — is `dante_corpus/skel/repairs.py` an
   admissible authority under discipline 3? It opens no gold file and its
   rewrites are re-derivable from `derive.py`, but it is the same `skel/`
   toolchain that built gold. [`STAGE6.md`](STAGE6.md) S6.3 prices both routes
   (deterministic through `repairs.py`, which transcribes `derive_unit`; or live,
   a session re-deriving the answer, which is what §1's autonomy premise actually
   measures). It is the operator's call, and item 1 below is a narrower instance
   of the same question.

### Carried out of Stage 7: the transcription-drift check (→ Stage 8 or later)

Investigated 2026-09-02 and deliberately left unimplemented — no test was
written and no code changed. Recorded here so the next stage starts from the
numbers rather than repeating the sweep.

**Why it left the stage.** It stopped being refactoring. Generalizing S6.10's
one-clause check turns out to require deciding *what the gate ought to be*, which
is a live authority question under Standing Invariant §1, not a neutrality-bound
tidy-up. Stage 7's rule is that every step is behaviour-neutral; this one cannot
be.

**What was measured.** Two sweeps, both over the committed corpus's frozen L1–L4
layers:

| Sweep | Scale | Result |
|---|---|---|
| Replay the 100 committed recon TSVs through `validate_candidate` | 3,477 units / 42,848 rows, 2.5 s | **0 refusals** |
| Generate every (predicate, argument, nominal role) triple per unit and compare `anchor_admits` against `validate.py` 150–179 rebuilt from its own helpers | 25,369,120 triples, 38 s | gate **looser**: 0; gate **stricter**: 317,305 |

The replay is cheap but **circular**: rows the gate refuses were never written
into the artifact, so a gate that is too strict stays consistent with its own
output. The generated sweep is the non-circular direction, and its verdict is
clean in both halves — the gate never admits what `validate.py` rejects, and
every position where it is stricter falls into exactly the three clauses
`runner/tools.py` (the `ARG_DEPRELS` note) already declares untranscribed:
**DG** coordination head 191,210, **AQ** aux head 125,342, **DS** marker slot
753. **No unknown drift exists**: the five transcribed clauses are faithful and
the gap is precisely the declared one.

**The question that made it a Stage-8 item.** `tools.py`'s note says these three
"are tree walks and no position in the corpus needs them here". The replay shows
that is true of the *committed* corpus; the generated sweep shows 317,305
positions outside it that do. Whether that matters is an authority question:
AQ, DG and DS are all `rule_active()` registry rules — the gold-fitted
tolerances S6.1 identified (88 of the 130 rules excusing 3,250 positions where
gold itself diverges from `derive_unit`). Transcribing them would widen the
*agent's* gate on the authority of a fit to gold. AF was transcribed on the same
footing in S6.10, so there is precedent, but precedent is not a principle. The
three options as they stand:

1. **Pin the gap.** Leave the three untranscribed and add the generated sweep as
   a test asserting the difference is *exactly* AQ/DG/DS and nothing else — new
   drift fails, no tolerance enters the gate. (The assistant's recommendation at
   the time; not acted on.)
2. **Transcribe the three.** The gate then matches `validate.py` exactly and the
   S6.9 deadlock becomes structurally impossible, at the cost of three more
   gold-fitted tolerances inside the agent's gate.
3. **Scope the property to what a `--fix` level can select.** S6.9's deadlock
   was about a level's bar naming a position the gate refuses; that, not the
   full cross-product, is the domain that actually matters.

Whichever is chosen, the replay sweep is worth keeping as a cheap regression
guard on its own (2.5 s, generalizing S6.10's thirteen cantos and one clause to
all hundred and every transcribed clause).
