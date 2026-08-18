# skel — Layer 5: predicate-argument skeleton

Predicate ↔ argument tuples binding Layers 2-4 into bare propositions, citing **token
positions**, not raw text or lemmas — the next layer of the grammatical stack
([`../PLAN.md`](../PLAN.md)) after dependency parsing. This is the *raw* skeleton only: **no
semantic frame, no coreference, no vocabulary normalization.** Role labels are **UD-derived**
(`subj`/`obj`/`iobj`/`attr`/`xcomp`/`ccomp`/`obl:<preposition lemma>`), not semantic, so the
canon-neutral.

**Status: built for all 100 cantos and verified at 0 hard / 0 soft violations corpus-wide. Checker refined through Phase 5 (5,919 → 2,084 soft), Phase 6 (2,084 → 160 soft), and Phase 7 (160 → 0 soft).**

`make -C skel check`: **0 hard, 0 soft** violations across all 100 cantos (100% clean corpus-wide; 0 `dual_role`, 0 `extra_tuple`, 0 `missing_tuple`, 0 `argument heads no NP`, 0 divergence residue).

## Documents & Layer 5 Roadmap

- **Active Plans & Future Architecture**:
  - [`PLAN.md`](PLAN.md): Current post-zero development plan (Phase 8 refactoring & Phase 9 autonomous grammar harness).
  - [`PORTABILITY.md`](PORTABILITY.md): Architectural roadmap toward a portable, modular Layer-5 checker (Rule Registry, language pack isolation, fixture tests).
  - [`HARNESS.md`](HARNESS.md): Specification for the autonomous grammatical parsing harness for local LLMs (Gemma 4).
- **Rule Reference & Correction History**:
  - [`RULES.md`](RULES.md) / [`RULES-ja.md`](RULES-ja.md): Formal Grammar Handbook & Rule Specification (all 130 rules systematized into a 6-branch hierarchical tree taxonomy with live census metrics and textual examples; Japanese edition with translated citations).
  - [`CORRECTIONS.md`](CORRECTIONS.md): Permanent record of hand corrections, checker rules (Rules A through EI), and verified structural exceptions.
- **Phase Retrospectives (Closed Records)**:
  - [`PHASE7.md`](PHASE7.md): Phase 7 Retrospective — driving soft violations from 160 to 0 (refusal census, outlier resolution, §P1–§P15).
  - [`PHASE6.md`](PHASE6.md): Phase 6 Retrospective — 2,084 → 160 soft violations (7 `--fix` rounds, 19-batch full-corpus read series, Rules AG–EH).
  - [`PHASE5.md`](PHASE5.md): Phase 5 Retrospective — 5,919 → 2,084 soft violations (deterministic elimination vs monolithic LLM regeneration).

## What it does

Unlike Layers 2-4, this layer's artifact is LLM-authored but **checked by a deterministic
derivation**: one LLM pass per parse unit (the same sentence-grouped units as Layer 4, see
`dep.sentence_groups`) proposes, independently, a Markdown table listing every predicate token
and its arguments — the model is deliberately **not shown the Layer-4 parse**, so its reading is
its own. `derive_unit` (`dante_corpus/skel.py`) computes the same predicate-argument structure
*mechanically* from the frozen Layer 2-4 artifacts, and `validate_unit`'s soft checks report
every place the LLM's tuple set diverges from that derivation. A purely deterministic Layer 5
would just be `f(dep)` and could never disagree with Layer 4; giving the LLM an independent read
means a divergence can surface a genuine Layer-4 mis-parse, not just an LLM slip — Layer 5
doubles as an audit of Layer 4, triaged with the same measure-then-freeze discipline as
[`dep/CORRECTIONS.md`](../dep/CORRECTIONS.md).

Worked example, Inferno I.1-9 (verified by hand against the frozen `dep`/`np`/`morph` artifacts;
reproduced exactly by `derive_unit`, see `tests/test_skel.py::test_derive_unit_inferno_1_1_9`):

- `ritrovai` (2.2): `subj = ∅` (pro-drop), `obl:in = [mezzo del cammin di nostra vita]` (1.1),
  `obl:per = [una selva oscura]` (2.1)
- `smarrita` (3.6): `subj = [la diritta via]` (3.1)
- `rinova` (6.4): `subj = che` (the relative pronoun token itself — its antecedent, `[esta selva
  selvaggia e aspra e forte]`, is *derived*, not stored, via `skel.antecedent`), `obj = [la
  paura]` (6.2), `obl:in = pensier` (6.1)

Each tuple is addressable by a stable id (`<line>.<ordinal>` in line order, mirroring Layer 3's
NP ids, derived at serve time via `skel.tuples_canto`), so a consumer artifact can **cite** a
skeleton tuple rather than paraphrase it.

## Output

`skel/<canticle>/NN.tsv` — one tab-separated row per (predicate, argument) pair: `line  token
word  role  arg_line  arg_token`. `arg_line=0, arg_token=0` marks pro-drop ∅ or a zero-argument
predicate. A `token=0` sentinel row (empty `word`/`role`, `0 0`) marks a whole line with no
predicates. Example (`skel/inferno/04.tsv`):

```
line	token	word	role	arg_line	arg_token
1	1	Ruppemi	subj	2	3
1	1	Ruppemi	obj	1	4
1	1	Ruppemi	obl:in	1	7
4	6	mossi	subj	0	0
```

## Check

`--check` validates every committed artifact with **no model call** (`validate_unit`):

- **Hard** (the structural bar): the predicate token exists in Layer 1 and every argument
  position is a valid in-unit token position or the `(0,0)` sentinel. `0 hard` is required
  before an artifact is trusted.
- **Soft** (reported, not enforced; measure-then-freeze): an argument citing a nominal role must
  be a Layer-3 NP head, a Layer-1 pronoun token, or an in-unit predicate (clausal argument); one
  token may not fill **two roles of one predicate** unless it is a fused clitic (`dual_role`,
  **rule EG**, 2026-08-18 — the only soft check that compares the artifact with *itself* rather than
  with `derive_unit`, which is why its 56 positions went unseen through 21 read batches); and,
  the central check, every divergence from `derive_unit`:
  `missing_tuple`/`extra_tuple`/`missing_arg`/`extra_arg`/`role_mismatch`.

### Checker Architecture & Core Principles

The Layer-5 checker (`validate_unit` in `dante_corpus/skel.py`) evaluates candidate tuples against `derive_unit` using five structural pillars:

1. **Normalization Layer (`_canonicalize_role`/`_normalize_prep_lemma`)**: Canonicalizes orthographic variants (`sanza` → `senza`), labeling conventions (`attr` ≡ `xcomp`, `iobj` ≡ `obl:a`), and multiword preposition clusters.
2. **Authority Model (`_apply_subj_authority`)**: Delegates mechanically underdetermined subject slots to the LLM within candidate sets (pro-drop antecedents, non-finite null subjects, and control/participial propagation via Rule V).
3. **Deterministic Auto-Repairs (`--repair` / Stage 1 of `--fix`)**:
   - **Tier A (No Reading Asserted)**: Mechanics-only repairs like `role_label` and `prep_stack`.
   - **Tier B (Corroborated Reading)**: Repairs requiring independent corroboration from Layer 2 morphology (e.g. `null_subject` gated on `dep.subject_agreement`).
4. **Third-Opinion Case Annex Integration (`_case_corroborated_role`)**: Adjudicates disputed clitic roles by reading the frozen `case/` annex as a third arbiter (Phase 5r, Rule U).
5. **Artifact-Internal Contradiction Checks (`dual_role`, Rule EG)**: Validates that one token does not fill two conflicting roles on the same predicate unless licensed as a fused clitic (Rule AL/CM).

### Rule Catalogue & Chronological Evolution

Over the course of Phases 4–7, **84 rule letters (A through EI)** were incrementally censused, measured by violation diff, tested, and landed.

For the complete evidence, rationale, and per-rule documentation:
- **Grammar Handbook & Tree Taxonomy**: See [`RULES.md`](RULES.md) (or [`RULES-ja.md`](RULES-ja.md) for the Japanese edition) for the complete 6-branch hierarchical specification of all 130 rules with UD formulations and corpus examples.
- **Full Rule Catalogue & History**: See [`CORRECTIONS.md`](CORRECTIONS.md).
- **Phase 5 Evolution (5,919 → 2,084 soft)**: Rules C–AF and the adoption of deterministic checker rules — see [`PHASE5.md`](PHASE5.md).
- **Phase 6 Evolution (2,084 → 160 soft)**: Rules AG–EH and the 19-batch full-corpus read series — see [`PHASE6.md`](PHASE6.md).
- **Phase 7 Evolution (160 → 0 soft)**: Rule EI, refusal census reads, outlier resolution, and complete residue closure — see [`PHASE7.md`](PHASE7.md).

### Measured Progression Across Phases

| Phase | Milestone / Key Interventions | Soft Violations |
|---|---|---|
| **Phase 4a** | Normalization, double-listing suppression, elided-copula whitelist | 17,438 → 7,776 |
| **Phase 4b** | Monolithic `--fix` baseline pass | 7,776 → 5,919 |
| **Phase 5** | Deterministic rules (Rules C–AF), Case Annex (Rule U), Control subjects (Rule V) | 5,919 → 2,084 |
| **Phase 6** | Three-stage `--fix` (Rounds 1–7: −1,157), Full-corpus read series (Rules AG–EH: −793), Refusal split | 2,084 → 160 |
| **Phase 7** | Refusal census reads, Rule EI, outlier elimination, upstream retags, 6 read censuses | 160 → **0** |

## `--fix`'s three stages (Phase 6)

Phase 5w measured the old design's cost: 1290 LLM calls removed 123 violations, because a flagged
unit was regenerated *whole* from one monolithic prompt and accepted only if the *whole* unit
improved. `--fix` now works cheapest-first, and a unit drops out as soon as it is clean.

1. **Deterministic** — `_apply_unit_repairs`, the `--repair` rules above, no model call. Measured
   at **2084 → 2011, −73** over the corpus. A unit this clears never reaches the model.
2. **Class-targeted** — the remaining violations are grouped by `_violation_subclass` and each
   group gets **its own system prompt, its own narrow question, and its own small answer**,
   spliced in at row level and accepted independently (`_CLASS_PROMPTS`, `_ask_class`). Tuple-level
   classes are asked before argument-level ones (`_CLASS_ORDER`), because adding or withdrawing a
   predicate changes which arguments there are to dispute.
3. **Whole-unit regeneration** — the original instrument, now a fallback for units the first two
   stages left untouched; `--no-whole` disables it so a round can be measured with and without it.

The summary is printed **per class, with calls beside violations removed**. That is what Phase
5w's finding demands: a pass average conceals which instrument worked.

### Why per-class prompts

Phase 5w's result was that a prose rule buried in a long prompt does not change the reading,
while an instruction that reaches the model *at the flagged position* does. Splitting the prompt
by class makes that structural rather than a matter of prompt-writing discipline: each class
prompt carries only the conventions bearing on it — the adverb rule for an adverb `extra_tuple`,
the attributive-adjective rule for an adjective one, the elided-speech-frame rule for a nominal
`missing_tuple` — all lifted verbatim from `SYSTEM_PROMPT`, which is unchanged and still used by
`build`. Each is under half its length. The other gain is partial credit: settling one class is
committed even when the others fail.

`membership` and `unknown_role` have no prompt on purpose — `_fix_hint` never produced one for
them (they carry no predicate), rule AF closed the membership question at 8, and `unknown_role`
stands at 0.

### The independence rule, in stage 2

A question may name the predicate, the argument **the LLM itself cited**, and the role slot in
dispute — exactly what `_fix_hint` already disclosed. It may **never** cite `derive_unit`'s own
argument position, which would reduce the model to confirming Layer 4 instead of reading the
line; `tests/test_skel_fix.py` pins this for both the position and, for `role_mismatch`, the
derived role.

## `--fix` hint (Phase 4b; now stage 3 only)

`skel/skel.py`:

- **`_fix_hint(nos, texts, violations)`**: summarizes a unit's `soft_before` violations into a
  short list, one line per `(predicate, role)` pair, phrased per violation kind
  (`missing_tuple`/`extra_tuple`/`missing_arg`/`extra_arg`/`role_mismatch`) — see
  `_HINT_PHRASING`. Only violations carrying a `.predicate` (i.e. `_classify_divergence`'s
  output) are included; `membership`/`unknown_role` violations (no predicate attached) are
  skipped.
- **`_prompt`/`_try_parse`** gained an optional `hint` parameter, appended as a final prompt
  section when present. `_fix_canto` is the only caller that supplies one, computed from each
  unit's `soft_before` right before regenerating; `build`'s call sites pass none.

## Field notes (`--log`)

Every instrument here asks for an answer of a fixed shape, and every one of them is answerable in
that shape whether or not the sentence supports it: asked *which token is this predicate's `subj`*,
a model with no way to say "none of them, and here is why" names a token. So each prompt carries
one **conditional** extra slot — a note line for a question the sentence offers nothing of the
shape asked for, one where two answers are equally defensible, or one whose convention does not fit
what the sentence does. The Q-numbered classes number their notes to the question (`N1: …`); the
table classes and `SYSTEM_PROMPT` cite a token instead (`N<line>.<token>: …`).

It is **not** an escape hatch — the prompts require the answer anyway — and it is **inert**:
`_split_field_notes` strips the notes before the response reaches `prompt.apply` or
`skel.resolve_chunk`, so splices, the acceptance gate and every per-class number are exactly what
they were without it (`tests/test_skel_fix.py::test_a_field_note_changes_nothing_about_the_splice`).
A note is a hypothesis about the *question*, never evidence about the corpus; what it buys is a
position worth handing to `read.py`, chosen by something other than reading all 100 cantos.

Notes are written only when `--log FILE` is given, one tab-separated line each, for accepted and
rejected candidates alike:

```
NOTE	purgatorio 1	100-102	missing_arg_adverb	102.1 'vidi' obl	no locative here answers 'where'.
#     canticle canto   unit lines  violation class   position + slot   what the model reported
```

```bash
uv run skel/skel.py inferno --fix -m ... --log skel-inferno.log   # one file per process
grep '^NOTE' skel-*.log | cut -f4 | sort | uniq -c                # by violation class
grep '^NOTE' skel-*.log | cut -f2,3,5                             # positions to hand to read.py
```

`--fix` truncates its log at start, so three parallel processes must not share one file. See
[`PHASE6.md`](PHASE6.md) §29 for how to read a round's notes.

## Model

Build-time only, set in [`../model.mk`](../model.mk), overridable with `make skel MODEL=...`.
The model is a build tool whose output is frozen and checked; consumers see a stable asset.

## Usage

```bash
make -C skel                          # build all three canticles (model from model.mk)
make -C skel MODEL=ollama:gpt-oss     # override the model
make -C skel check                    # validate artifacts, no model call
make -C skel stats                    # validate artifacts, no model call; soft counts by class
make -C skel repair                   # --fix's deterministic stage on its own, no model call
make -C skel fix                      # reduce soft violations (three stages)

uv run skel/skel.py inferno [-c SPEC] [-m MODEL] [--chunk 12] [--force] [--check] [--stats]
uv run skel/skel.py inferno purgatorio paradiso --repair    # no model call
uv run skel/skel.py inferno -m ollama:gpt-oss --fix         # all three stages
uv run skel/skel.py inferno -m ... --fix --no-whole         # without the regeneration fallback
uv run skel/skel.py inferno -m ... --fix --log skel-inferno.log   # ... collecting field notes

uv run skel/read.py inferno 16 43                           # read one position, all five layers
uv run skel/read.py inferno 16 43 48                        # ... over a line range
```

`-c`/`--canto` selects which cantos to process: `1`, `11-20`, `12-` (from 12 on), `-20` (up to
20), or a comma-separated mix such as `1,3-5,11-`. It is the same selection syntax in every build
driver, and a spec matching no canto is a command-line error rather than a silent no-op.

`read.py` is the audit series' tool (see [`PHASE6.md`](PHASE6.md) §4 and [`PHASE7.md`](PHASE7.md)): `--check`
names a position, `read.py` prints its whole parse unit with Layer-2 morphology and the `case`
annex, Layer-4 deprels, Layer-3 NP spans, and **both** Layer-5 readings — the frozen artifact rows
and `derive_unit`'s derived rows, which is exactly the pair the soft checks diff.

Consumers read it deterministically via `Canto.skel()` (frozen, grouped, identified
`SkelTuple`s) or the CLI `dante-corpus text skel inferno 1:1-3` (`--format json` for tuple
dicts). `skel.antecedent` resolves a relative-pronoun subject's antecedent NP at serve time
(never stored); `skel.pro_drop_features` similarly derives person/number for a `∅` subject from
the predicate's own morphology.
