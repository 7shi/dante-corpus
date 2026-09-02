# Stage 7 — Refactoring (OPENED 2026-09-02 by operator, on Stage 6's close)

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
   one module. (**S7.2.**)

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

---

## 4. Remaining stage scope

- **S7.2 (planned) — split `extractor/reconstruct.py`.** The responsibility
  boundaries are already visible in the module (`FixPlan` / `fix_*` / `salvage_*`,
  `TsvArtifact`, `GoldReport` / `GoldFace`, `ReconstructReport`, the CLI). Same
  neutrality bar: the pipeline's behaviour must not move.

That is the whole of the stage. The item below is **not** in it.

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
