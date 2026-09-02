# Stage 7 — Refactoring (OPENED 2026-09-02 by operator, on Stage 6's close)

Opening this document is what closes Stage 6 on S6.11. The operator's decision
of 2026-09-02 re-scoped Stage 7: it is **a refactoring stage**, not level 2 of
the soft-divergence reduction. Level 2 keeps its candidates and eligibility list
in [`STAGE6.md`](STAGE6.md) §3 and waits for a stage of its own; nothing about
that analysis is invalidated by the delay.

---

## 1. Scope & why now

Six stages of live-run work left the harness working but top-heavy. Three
specific weights, in the order they were agreed:

1. **The agent's domain knowledge is hidden inside Python string literals.**
   `runner/prompts.py` held the role framing, the skeleton row conventions and
   the whole 5-step reasoning protocol as module constants. Prompt wording is
   the most consequential thing in the project and it was the least reviewable:
   a change to it looked like a code change, and no run recorded which wording
   it ran under.
2. **The transcription drift between `harness/` and `dante_corpus/` is a class,
   not a point.** S6.10 found `runner/tools.py`'s gate narrower than the
   `validate.py` contract it transcribes, after five corpus-wide runs had been
   spent on the symptom. One test now covers the anchor rule; the drift it
   belongs to is not otherwise covered.
3. **`extractor/reconstruct.py` is 1,928 lines** carrying the canto loop, fix
   planning, salvage, the TSV artifact, the gold face, reporting and the CLI in
   one module.

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

- **S7.2 (planned) — generalize the transcription-drift check.** S6.10's
  `test_anchor_gate_is_never_stricter_than_validate` covers one rule. Every
  constraint `runner/tools.py`'s gate enforces should be checked against the
  `validate.py` clause it transcribes, so a gate that refuses what the corpus
  permits fails a test instead of costing corpus-wide runs. This is also the
  reusable observer the Warp pattern's improver would need, minus the loop.
  [`PLAN.md`](PLAN.md)'s Handoff names this as the check to write before level 2
  spends a live run.
- **S7.3 (planned) — split `extractor/reconstruct.py`.** The responsibility
  boundaries are already visible in the module (`FixPlan` / `fix_*` / `salvage_*`,
  `TsvArtifact`, `GoldReport` / `GoldFace`, `ReconstructReport`, the CLI). Same
  neutrality bar: the pipeline's behaviour must not move.
