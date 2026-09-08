# Grammar Agent Harness

Autonomous Grammar Agent Harness for Local LLMs (e.g., **Gemma 4 31B**), designed to systematically infer and reconstruct Layer 5 predicate-argument skeletons from multi-layer grammatical contexts (Layer 1 tokens, quotes hierarchy, Layer 2 morphology, pronoun case annex, Layer 3 noun phrases, and Layer 4 UD syntax trees).

> **Status: CLOSED (2026-09-08).** Stages 1–10 ran and closed; Stage 10 was the
> last, and development of `harness/` ends there. The generic apparatus was split
> out into `dante_corpus/harness/`, both halves were verified deterministically
> (739 tests) and live (`run` and `fix` on the real model), and the tests were
> then parted so that only the apparatus's stay in the maintained suite. What is
> left is a **library that [`../layers/PLAN.md`](../layers/PLAN.md) drives**
> rather than a development subject of its own. Read that plan before anything
> here; read [`PLAN.md`](PLAN.md) §2 for the four pieces of closing work.

### Design Philosophy: Autonomy Over Rigid Templates
The harness favors letting the model decide for itself — what a unit's frame contains, and when its work on that unit is actually done — over forcing it through a fixed, scripted procedure. Since Stage 9 the mechanism is a **bounded fixed-context step**: each iteration hands the model the same prompt plus the unit's own evidence and the previous iteration's rows, and it answers with one `<rows>` block. The loop stops when the model's answer stops changing — its own completion signal — with the iteration cap (`FIXED_ITERATIONS`, 4 by default) only a safety net; a request's size is therefore a function of the unit, not of how many times the model has revised. A model boxed into a rigid template is expected to underperform one given room to judge for itself when its work is done.

*(Through Stage 8 the same philosophy ran as a per-unit tool-calling session that submitted through `validate_candidate` and ended when the model replied in plain text. That session was measured against the fixed-context step in Stage 9, lost, and was deleted on 2026-09-07; [`TOOLCALL.md`](TOOLCALL.md) is its record. `validate_candidate` itself survives as the gate.)*

### Motivation: Generalizable Layer 5 Reconstruction
While Layer 5 (`skel/`) reached **0 hard / 0 soft violations across all 100 cantos** in Phase 8, its historical construction had a small local LLM (`gemma4:31b-it-qat`) generate and repair the TSVs, while its residual errors required an ad hoc, semi-manual triage process (interactive audits with frontier LLMs — Claude Opus 5, switching to Gemini 3.7 Flash at the end of Phase 8 — plus hand-crafted rules and manual corrections) that was bespoke to Dante's Italian and difficult to generalize to new texts or languages.

`harness/` is the **systematic and fully automated reconstruction of Layer 5**. It held `skel/` fixed as a **0-soft Gold Standard** for the duration of the work — a benchmark read afterwards, never a target, and since 2026-09-07 not opened at all — and was built as a **two-stage bottom-up architecture** to show that a local LLM can autonomously reconstruct Layer 5 and generalize across grammatical domains:

1. **Stage 1: Autonomous Inference & Benchmark** ([`runner/`](runner/README.md)) — Evaluated local models using dedicated tool calling and multi-layer CoT reasoning without free-form bash execution, logging rich inference traces.
2. **Stage 2: Bottom-Up Extraction & Hybrid Engine** ([`extractor/`](extractor/README.md)) — Mined those traces into deterministic fast-path rules and verb valency lexicons, behind a gated production pipeline.

**Both stages' inference machinery is gone as of 2026-09-07**, and the two bullets are the record of what was built, not of what runs. Stage 2 measured the mined fast path at **7% of the corpus**, so it never became the primary path and was deleted with the benchmark that fed it; the surviving pipeline is L1–L4 → the fixed-context step → the three gates, with **every unit reaching the model**. What each stage settled is [`PLAN.md`](PLAN.md) §2's table.

---

## Documentation & Roadmap

- **Master Plan**: [`PLAN.md`](PLAN.md) — Comprehensive architectural specification and staged bottom-up strategy (Stages 1–2 induction core, Stage 3 context optimization, Stage 4 corpus scale-out, Stages 5–6 corpus durability and divergence reduction, Stage 7 refactoring, Stage 8 soft level 2, Stage 9 fixed-context execution, Stage 10 soft level 3 — the last stage). Keeps the closing readouts (Current Status), the standing disciplines (§4), and — in §2's *After the last stage* — the four pieces of closing work that followed Stage 10: the cut, the apparatus split, the live verification, and the parting of the tests.
- **What happens next**: [`../layers/PLAN.md`](../layers/PLAN.md) — `harness/` is closed as a development subject and becomes a library; the layer stack's own description is the open question. Read it before anything here.
- **Stage 1 Record**: [`stages/01.md`](stages/01.md) — Archived milestones, ledger, and carry-over resolutions for the completed Stage 1 (split from PLAN.md).
- **Stage 2 Record**: [`stages/02.md`](stages/02.md) — Archived milestones, ledger, and carry-overs for the completed Stage 2, incl. the inferno-1 pilot/recheck readouts (split from PLAN.md).
- **Stage 3 Design & Ledger**: [`stages/03.md`](stages/03.md) — Stage-3 home: the payload/pacing design (S3.2), gate re-check, implementation map, confirmation protocol, and the record of why transcript compaction was removed (S3.7). CLOSED on S3.11.
- **Stage 4 Record**: [`stages/04.md`](stages/04.md) — The 99-canto full-corpus scale-out: commands, watch items, readout criteria, and the ledger S4.1–S4.3. CLOSED on S4.3.
- **Stage 5 Record**: [`stages/05.md`](stages/05.md) — Corpus durability (the run's logs turned into 100 committed gold-format TSVs) and the hard-divergence reduction that followed, incl. what the violation count is and what gold is not (§5). CLOSED on S5.8 at **0 hard**.
- **Stage 6 Design & Ledger**: [`stages/06.md`](stages/06.md) — Reducing the 5,014 soft findings, the standing method that record S6.1 forced on it, and class eligibility. CLOSED on S6.11 with soft level 1 at 0 findings.
- **Stage 7 Record**: [`stages/07.md`](stages/07.md) — Refactoring: the agent's knowledge moved into `runner/skills/` files (S7.1) and `extractor/reconstruct.py` split into seven modules (S7.2), both argued behaviour-neutral. CLOSED on S7.2's live confirmation; §4 lists what carries forward.
- **Stage 8 Record**: [`stages/08.md`](stages/08.md) — Soft `--fix` level 2 (`omitted_l4_argument`), argued from `derive.py` with gold unopened: 1,128 → 0 findings. CLOSED.
- **Stage 9 Record**: [`stages/09.md`](stages/09.md) — The per-unit tool-calling session replaced by a bounded fixed-context step whose request size does not grow with the iteration count, and made the default. CLOSED.
- **Stage 10 Record**: [`stages/10.md`](stages/10.md) — Soft `--fix` level 3 (`unregistered_predicate`), the first concurrent corpus run, and S10.2's finding that `membership` cannot be decided inside Layer 5. CLOSED — **the last stage**.
- **Classification audits**: [`HARD.md`](HARD.md) (S5.4) and [`SOFT.md`](SOFT.md) (S6.1) — evidence records asking whether the checker's own hard/soft classification is sound, each filed before the design pass it would otherwise drive. Cross-linked to each other.
- **Beyond Layer 5**: [`FUTURE.md`](FUTURE.md) — Unscheduled design notes on layer swaps, whole-stack vertical slices, and grammar reconstruction without a grammar book.
- **Stage 1 (Inference & Benchmark)**: [`runner/README.md`](runner/README.md) | [`runner/PLAN.md`](runner/PLAN.md)
- **Stage 2 (Extraction & Hybrid Engine)**: [`extractor/README.md`](extractor/README.md) | [`extractor/PLAN.md`](extractor/PLAN.md)

Both subpackage plans specify Layer 5's side and name which of their modules
moved to `dante_corpus/harness/`, but each also describes code deleted on
2026-09-07 (the agent session and benchmark in `runner/PLAN.md`, the miners and
hybrid engine in `extractor/PLAN.md`). The apparatus's own contract is
`dante_corpus/harness/__init__.py`'s docstring plus the four seams in
[`PLAN.md`](PLAN.md) §3; the directory map below is current.

---

## Directory Structure

The single directory map for the harness — [`PLAN.md`](PLAN.md) and the stage
plans reference this section instead of repeating it. Implementation status is
tracked in [`PLAN.md`](PLAN.md) (Current Status / Milestone Ledger), not here.

```
dante-corpus/
├── skel/                          # [Protected] Layer 5 gold TSV & Phase 8 deterministic engine
│   ├── RULES.md                   # 130 deterministic rule handbook (masked from agents)
│   └── ...                        # Active 0-soft regression gate target
│
├── dante_corpus/harness/          # The apparatus, with no layer of its own
│   ├── rows.py                    # The seam: RowCodec + the row/violation protocols
│   ├── pipeline.py                # The canto loop + Subject (gates 1-2 applied)
│   ├── fixedcontext.py            # The bounded per-unit step + Observer
│   ├── fixrun.py                  # --fix: plan, verdict, salvage, revert + Criteria
│   ├── outcome.py                 # UnitOutcome / CantoReconstruction + unit resume
│   ├── artifact.py                # render_tsv + TsvArtifact (through the codec)
│   ├── report.py                  # ReconstructReport + load_log
│   ├── llm.py                     # llm7shi adapter + the llm_request/llm_response wire log
│   ├── skills.py                  # File-based skill loader (SKILL.md + resources)
│   └── statusline.py              # Rich live status bar for long operator-run sessions
│
├── harness/                       # [Isolated] Grammar Agent Harness & Extraction Lab
│   ├── README.md                  # Overview, navigation, and this directory map
│   ├── PLAN.md                    # Master architectural plan (status, milestones, disciplines)
│   ├── stages/                    # One file per stage: design, running detail, ledger
│   │   ├── 01.md                  # Archived Stage-1 record (milestones 1.1–1.4, carry-overs)
│   │   ├── 02.md                  # Archived Stage-2 record (milestones 2.1–2.5, pilot/recheck readouts)
│   │   ├── 03.md                  # Stage-3 design + ledger (payload/pacing, launch hardening)
│   │   ├── 04.md                  # Stage-4 record (99-canto corpus run, readout, ledger)
│   │   ├── 05.md                  # Stage-5 record (corpus durability + hard reduction to 0)
│   │   ├── 06.md                  # Stage-6 design + ledger (soft divergence reduction)
│   │   ├── 07.md                  # Stage-7 record (refactoring: skills as files + module split)
│   │   ├── 08.md                  # Stage-8 record (soft fix level 2)
│   │   ├── 09.md                  # Stage-9 record (fixed-context execution, made the default)
│   │   └── 10.md                  # Stage-10 record (soft fix level 3 — the last stage)
│   ├── HARD.md                    # Audit: is the hard classification sound? (S5.4)
│   ├── SOFT.md                    # Audit: is the soft classification sound? (S6.1)
│   ├── TOOLCALL.md                # [Historical] Tool call protocol sub-project — the code it
│   │                              #   documents (toolcall/) was removed on 2026-09-07
│   ├── FUTURE.md                  # Beyond Layer 5 (unscheduled design notes)
│   │
│   ├── runner/                    # The model-facing half: the evidence, the gate, the wording
│   │   ├── README.md              # Stage 1 overview
│   │   ├── PLAN.md                # Stage 1 specification (toolset, agent, benchmark)
│   │   ├── tools.py               # Dedicated Grammar Tool API (Layer 5 masked structurally)
│   │   ├── prompts.py             # Prompt assembly (the grammatical wording lives in skills/)
│   │   └── skills/grammar-fixed/  # [Stage 9] The model's domain knowledge as reviewable files
│   │       ├── SKILL.md           # Role framing + skeleton row conventions
│   │       ├── protocol.md        # The reasoning protocol
│   │       └── answer.md          # The answer contract (<rows> …)
│   │
│   ├── extractor/                 # Layer 5's side of the pipeline: the gates' content
│   │   ├── README.md              # Stage 2 overview
│   │   ├── PLAN.md                # Stage 2 specification (miner, lexicon, hybrid engine)
│   │   ├── layers.py              # Frozen L1-L4 bundle + gates 1-2; SKEL_CODEC / SKEL_SUBJECT
│   │   ├── observe.py             # [Stage 9] The frozen-layer verdict; SkelObserver
│   │   ├── fixlevel.py            # [Stage 6] Soft-finding levels — the apparatus's Criteria
│   │   ├── artifact.py            # \
│   │   ├── fixrun.py              #  |- one-line bindings of the apparatus modules above
│   │   ├── fixedcontext.py        # /
│   │   └── reconstruct.py         # Gate 3 (commit), the CLI, and the subject wiring
│   │
│   ├── recon/                     # [Stage 4–6] Full-corpus run drivers & durable artifacts
│   │   ├── Makefile               # 100-canto launch, resumable; goal & resume state = NN.tsv
│   │   ├── readout.py             # [Stage 4] Corpus-wide log aggregation & closing readout
│   │   ├── check.py               # [Stage 5] Hard/soft violation check, stats & fix-level readout
│   │   └── <canticle>/            # NN.tsv (skel-compatible, committed); NN.log = gitignored by-product
│   │
│   └── tests/                     # Layer 5's own tests — closed; not in the default pytest run
│       ├── test_harness_tools.py      # Toolset unit tests (masking, validation)
│       ├── test_harness_skills.py     # [Stage 7/9] The grammar-fixed skill files + the prompt
│       ├── test_harness_fixedcontext.py   # Stage 9 tests (the bounded step, the verdict, $P$)
│       ├── test_harness_fixlevel.py       # Stage 6/8/10 tests (levels, selection, --fix end to end)
│       ├── test_harness_reconstruct.py    # Gate tests (assertions, 0-soft, hash commit, CLI)
│       ├── test_harness_recon_readout.py  # Stage 4 readout tests (aggregation math)
│       └── test_harness_recon_check.py    # Stage 5 check tests (hard/soft split, base_dir)
│
└── tests/                         # The maintained suite: the corpus + the apparatus
    ├── test_harness_apparatus.py  # The apparatus with no subject (loader, Σ, report, row delta)
    ├── test_harness_pacing.py     # Stage 3 tests (Client sync, interval, token bucket)
    └── test_harness_boundary.py   # The split's rule: no dante_corpus import either way
```

**Where the tests live** (2026-09-08, operator). The close leaves two bodies of
code with opposite futures — `harness/` finished, `dante_corpus/harness/` still
to be driven by [`../layers/PLAN.md`](../layers/PLAN.md) — so the one suite that
covered both was split by a mechanical criterion: **does the test import from
top-level `harness/`?**

- `harness/tests/` — **163** tests in seven files, everything that reaches the
  apparatus *through* Layer 5's bindings. Kept as the record of what the closed
  work verified, not as a suite this repository keeps green.
- `tests/` — **24** harness tests in three files, the apparatus with no subject:
  `test_harness_apparatus.py` (skill loader, the bounded step's row parsing and
  rendering, the report's aggregation, the fix machinery's row delta),
  `test_harness_pacing.py` (model adapter), `test_harness_boundary.py` (the
  import rule). These stay in the maintained suite, because `layers/` reaches
  exactly this code.

`pyproject.toml`'s `testpaths = ["tests"]` keeps the closed half out of a bare
`uv run pytest` (**576**); naming the directory still runs it
(`uv run pytest harness/tests` → 163), and both together are the same **739** as
before — nothing was dropped or weakened. What the arrangement costs is in
[`PLAN.md`](PLAN.md) §2, item 4: the apparatus's behavioural coverage lives
mostly on the closed side, so a bare `pytest` would not catch a regression in
the canto loop or the `--fix` verdicts.

**What moved on 2026-09-07**, when the generic apparatus was split out of
`harness/` into `dante_corpus/harness/`: the canto loop, the bounded per-unit
step, the `--fix` machinery, the artifact and resume machinery, the outcome
records, the run report, the model adapter, the status bar and the skill loader.
They were coupled to Layer 5 by a *type* they carried (`skel.models.SkelRow`)
rather than by anything they did, and that type is now a `RowCodec` the subject
supplies. Four seams carry the rest — `RowCodec`, `Subject`, `Criteria`,
`Observer` — and Layer 5's implementations of all four stay here, in
`extractor/layers.py`, `fixlevel.py` and `observe.py`. `tests/test_harness_boundary.py`
holds the rule that makes the split real: nothing under `dante_corpus/harness/`
imports anything else from `dante_corpus`. The apparatus therefore ships with the
distribution; `harness/` deliberately does not.

**What was removed on 2026-09-07**, when the harness was cut down to the run and
fix paths it is actually driven by: the Stage-1 per-unit tool-calling session
and the protocol library under it (`toolcall/`, `runner/agent.py`, the
`--tool-calling` flag and `TOOLCALL=1`), the Stage-1 benchmark and its fixtures
(`runner/benchmark.py`, `fixtures/`), the Stage-2 mined fast path
(`syntax_miner.py`, `lexicon_builder.py`, `hybrid_engine.py` — every unit now
reaches the model), and every gold-referenced readout (`goldeval.py`,
`--verify-gold`, `recon/agree.py`), together with `recon/convert.py` and
`recon/repair.py`. Gold is no longer opened anywhere in `harness/`. The stage
documents that describe those pieces are kept as the record of what was done.

**Both changes were verified live on 2026-09-07/08**, once each, because neither
could be proven by tests: assistant sessions call no model, and the two changes
rewired the only path that reaches one. Each verification regenerated
`inferno/01` from scratch and ran `make fix` over all 100 cantos. The post-split
run held the prompt digest byte-identical (`ee6f1a46…` on all 101
`canto_complete` records), showed the injected observer live (162 observations
over 346 iterations), routed every unit as specified, and finished at **0 hard,
0 token-assertion errors, no canto worse than it started**. Closing readouts:
**0 hard / 2,954 soft**, `make fix-level` **0 / 0 / 206**, **739 tests** (576 +
163 since the parting above). The
numbers and the four checks behind them are in [`PLAN.md`](PLAN.md) §2, *After
the last stage*.
