# skel — Layer 5: predicate-argument skeleton

Predicate ↔ argument tuples binding Layers 2-4 into bare propositions, citing **token
positions**, not raw text or lemmas — the next layer of the grammatical stack
([`../PLAN.md`](../PLAN.md)) after dependency parsing. This is the *raw* skeleton only: **no
semantic frame, no coreference, no vocabulary normalization.** Role labels are **UD-derived**
(`subj`/`obj`/`iobj`/`attr`/`xcomp`/`ccomp`/`obl:<preposition lemma>`), not semantic, so the
LLM's roles and the derivation's roles are directly comparable and the corpus stays
canon-neutral.

**Status: built for all 100 cantos, checker refined through Phase 5f, one Phase 5e `--fix` round
run.** `make -C skel check`: **0 hard, 4327 soft** violations (down from 17438 at the first
full-corpus measurement, 7776 at the Phase 4a checkpoint, 5919 after the Phase 4b `--fix` round,
5105 after Phase 5a, 4846 after Phase 5b, 4615 after the Phase 5e `--fix` round). See [skel/CORRECTIONS.md](CORRECTIONS.md) for the
full correction history. `--fix` regeneration improves **8.7%** of the units it attempts (178 of
2037 in the Phase 5e round, ~0.11 violations per LLM call) and that rate did not improve once
the deterministic phases had cleared the unfixable units out of the flagged set — so the
remaining gap is closed by measuring classes and normalizing, not by more model calls (see
[PLAN.md](PLAN.md) and *Next steps*).

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
  be a Layer-3 NP head, a Layer-1 pronoun token, or an in-unit predicate (clausal argument); and,
  the central check, every divergence from `derive_unit`:
  `missing_tuple`/`extra_tuple`/`missing_arg`/`extra_arg`/`role_mismatch`.

Four refinements make that divergence check meaningful rather than noisy — landed as four
successive phases, each measured before/after (`--stats` aggregates violations by kind, by
`(kind, role, ∅-or-real)`, and by `role_mismatch` pair):

1. **Normalization layer** (`_canonicalize_role`/`_normalize_prep_lemma`, applied to both sides
   before comparison): preposition-lemma orthographic variants (`sanza`/`sovra`/`de`/... →
   `senza`/`sopra`/`di`/...), the `attr`≡`xcomp` and `iobj`≡`obl:a` labeling splits, and
   clausal-complement double-listing (a `ccomp`/`xcomp` the LLM lists as its own tuple instead of
   also citing as its matrix predicate's argument) — all label-level equivalences, not
   disagreements about the parse.
2. **Authority model** (`_apply_subj_authority`): makes the `subj` slot LLM-authoritative
   (validated against a candidate set, not exact-matched) in exactly three mechanically
   underdetermined cases — pro-drop antecedents (`derive_unit` says ∅, any concrete subject the
   LLM cites is accepted), non-finite ∅ (LLM marks ∅ on an infinitive/gerund `derive_unit`'s
   pro-drop rule doesn't cover), and xcomp/ccomp control subjects (an LLM-proposed subject is
   accepted iff it equals the matrix predicate's derived `subj` or `obj` — replaces a
   verb-specific control lexicon with a structural check). Every other role, and `subj` where
   `derive_unit` resolves a real subject, stay exact-match.
3. **`--repair`** (`Repair`/`_find_repairs`/`_safe_role_repair`): for the subset of divergences
   the dep tree fully determines, mechanically rewrites the committed TSV — no model call — two
   conservative rules, both sourced from the checker's own violation list (so the authority model
   above automatically gates what's eligible):
   - **null_subject**: a `missing_arg subj` (derived a real subject from an explicit `nsubj`
     edge) paired with an `extra_arg subj (0,0)` (the LLM wrote pro-drop ∅) for the same
     predicate — the ∅ citation is replaced with the derived one.
   - **role_label**: a `role_mismatch` where the given role is bare `obl` and the derived role is
     `obl:<lemma>` (the dep tree's `case`-child detection) — the role cell is rewritten.
   - Genuine disagreements (`subj`/`obj` reversals, `iobj`/`obj` reversals, cross-lemma `obl`
     pairs) are deliberately excluded from both rules and left for hand/LLM triage.
4. **Phase 4a — double-listing + elided-copula whitelist** (`_classify_divergence`, gating the
   `extra_tuple` set): a predicate nominal/adjective double-listed as both another predicate's
   `attr`/`xcomp` argument *and* its own redundant predicate tuple is suppressed (extends Phase
   1's `ccomp`/`xcomp` double-listing suppression to `attr` and to `extra_tuple`); separately, a
   predicate nominal with **no verb token at all**, coordinate or apposed to a real clause (dep
   deprel `conj`/`appos`/`attr` — e.g. "mantoani per patrïa ambedui") is exempted as a genuine
   elided-copula reading `derive_unit` structurally can't produce. Deliberately narrower than a
   blanket "non-verb POS" rule: the majority of non-verb `extra_tuple` predicates (dep deprel
   `amod`/`advmod`/`obj`/`nsubj`/`nmod`) are NP-internal modifiers the LLM wrongly promoted to
   predicate status — genuine errors, left flagged for `--fix`, not swallowed by the whitelist.
5. **Phase 5a — coordination + `nmod`-oblique normalization** (`_collapse_coordination` /
   `_drop_nmod_obliques`, applied to the argument maps after the authority model, before the
   diff): every argument citation is collapsed onto its coordination head by walking `conj`
   edges up, on **both** sides ("si ciberà di terra e di sapïenza" — the LLM lists both
   conjuncts, `derive_unit` reads only a predicate's direct dep children and sees the first
   alone); and an `obl`/`obl:<prep>` whose argument is an `nmod` dependent of one of the same
   predicate's own derived arguments is accepted ("ha *bisogno* **di te**"). Both are
   notation-convention equivalences like Phase 1's, not new derived rows — emitting a derived
   row per conjunct instead was measured at net −2 (`extra_arg` −554 against `missing_arg` +529),
   because the LLM's own enumeration of coordinations is inconsistent. Roles are preserved, so a
   genuine role disagreement on a conjunct still surfaces.
6. **Phase 5b — three classes the re-triage isolated**: (a) `derive_unit` no longer promotes a
   **coordinating conjunction** to predicate status via its `conj` rule — Layer 4 routinely
   attaches a line-initial `E`/`Ma` to the previous clause head, and a function word is never a
   predicate (gated on Layer-2 POS, so gapped predicates of other POS stay derived); (b) a given
   predicate that is an `aux`/`cop` whose head `derive_unit` derived as the predicate is
   suppressed (`_aux_head`) — "Molti *son* li animali", the copula/modal double-listing, same
   shape as the Phase 4a `attr`/`xcomp` rule; (c) an `obl`/`obl:*` citing an adverb attached
   `advmod` to the same predicate (`quivi`, `là`, `dinanzi`) is accepted (`_adverbial_oblique`)
   — the membership check already accepts exactly these tokens as `obl` arguments.

**Measured over the full 100-canto corpus** (`--check`, 2026-07-20 Phase 4a checkpoint): **0
hard, 7776 soft** — by kind, `extra_arg` 3719, `missing_arg` 1780, `role_mismatch` 1466,
`extra_tuple` 600, `missing_tuple` 117, `membership` 94. See [CORRECTIONS.md](CORRECTIONS.md)
for the measured before/after at every phase (14329 → 12825 → 9672 → 8090 → 7776) and the tests
backing each rule.

After a round of Phase 4b `--fix` regeneration (2026-07-25, run 3-way parallel): **0 hard, 5919
soft** — by kind, `extra_arg` 2848, `missing_arg` 1353, `role_mismatch` 1245, `extra_tuple` 275,
`missing_tuple` 100, `membership` 96, `unknown_role` 2. Every kind dropped, but the pace slowed
noticeably compared to the mechanical phases above — and the measurement in [PLAN.md](PLAN.md)
showed why: most flagged units are checker-side notation mismatches, not LLM errors.

After Phase 5a (2026-07-26, checker-only, no model call): **0 hard, 5105 soft** — by kind,
`extra_arg` 2065, `missing_arg` 1317, `role_mismatch` 1250, the rest unchanged. Δ814 in minutes,
roughly 1.8× what a full 2235-call `--fix` pass was extrapolated to remove. `subj` remains the
largest role bucket (`extra_arg subj` 936, `missing_arg subj` 323), and that residue is genuine
subject disagreement (enjambment, pro-drop resolution) — widening the control-subject authority
model was measured at −22 and rejected.

After Phase 5b (2026-07-26, checker-only): **0 hard, 4846 soft** — `extra_arg` 1991,
`missing_arg` 1305, `role_mismatch` 1250, `extra_tuple` 176, `membership` 96, `missing_tuple`
26, `unknown_role` 2. Phase 5d's hypothesis that the `expl` cases are Layer-4 mistags was
**disproved** by enumeration (99 of 107 cite the clitic of an inherently pronominal verb, which
Layer 4 tags correctly) — no `dep/CORRECTIONS.md` entry was opened.

After the Phase 5e `--fix` round (2026-07-28, all three canticles, 2037 units attempted): **0
hard, 4615 soft** — `extra_arg` 1887, `missing_arg` 1239, `role_mismatch` 1214, `extra_tuple`
155, `membership` 94, `missing_tuple` 24, `unknown_role` 2. 178 units accepted (8.7%), none
regressed, 231 violations removed. No class moved more than 11.9% and the three large ones moved
2.9-5.2%, which is the signal that what remains is checker-side rather than LLM error.

After Phase 5f (2026-07-28, checker-only, rule L): **0 hard, 4327 soft** — `role_mismatch` falls
1214 → **926** (−288, −23.7%), every other class unchanged. A given `obl:<lemma>` against a
derived bare `obl` is not a disagreement: `derive_unit` emits the bare form only when no `case`
child names the preposition, which holds in all 288 instances (the preposition is fused into the
token — a clitic dative or a preposition+article contraction), so the LLM's label is strictly
more informative. One deterministic rule removed more than the whole Phase 5e `--fix` pass.

## Next steps

What remains past the mechanical phases above should be genuine LLM misreadings (subject
mix-ups across enjambment, `subj`/`obj`/`iobj` reversals) plus a residual `extra_tuple` tail
(non-finite verbs used as nominalized oblique complements and other one-off structural cases)
and `membership` (a scattered long tail of individual boundary cases, not one mechanical
pattern — Phase 0 already caught the two big mechanical membership fixes). Only these should
need `--fix` (LLM regeneration), restricted to the specific flagged lines, re-checked per class
— the goal is **0 soft violations**, treating every remaining class as something to fix or
formally exempt, not a baseline to tolerate.

`--fix` (`skel/skel.py`) regenerates a flagged parse unit and keeps the result only if its soft
violation count strictly drops **and** no violation class appears that wasn't already there
(`_is_improvement`, Phase 5c — the plain count test let the Phase 4b round trade a net drop for
`unknown_role` 0 → 2, a role outside the frozen vocabulary). As of Phase 4b's `_fix_hint`, a regeneration attempt gets a
per-predicate pointer built from the unit's prior soft violations — which predicate looks
unwarranted or missing, which role slot looks missing/extra/mislabeled — appended to the prompt
`build`'s initial parse never receives. The hint deliberately withholds `derive_unit`'s actual
argument citations and its correct role label (a `role_mismatch` hint names the LLM's *own*
prior label, not the derived one), so the retry still reads the sentence independently rather
than parroting back a guess; without it, a systematic misreading (e.g. resolving an `xcomp`
control subject from the wrong constituent) tends to reproduce itself verbatim across attempts.

## `--fix` hint (Phase 4b)

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

## Model

Build-time only, set in [`../model.mk`](../model.mk), overridable with `make skel MODEL=...`.
The model is a build tool whose output is frozen and checked; consumers see a stable asset.

## Usage

```bash
make -C skel                          # build all three canticles (model from model.mk)
make -C skel MODEL=ollama:gpt-oss     # override the model
make -C skel check                    # validate artifacts, no model call
make -C skel stats                    # validate artifacts, no model call; soft counts by class
make -C skel repair                   # rewrite derive-authoritative errors, no model call
make -C skel fix                      # regenerate parse units carrying soft violations

uv run skel/skel.py inferno [-c 1] [-m MODEL] [--chunk 12] [--force] [--check] [--stats]
uv run skel/skel.py inferno purgatorio paradiso --repair   # no model call
uv run skel/skel.py inferno -m ollama:gpt-oss --fix        # regenerate flagged units
```

Consumers read it deterministically via `Canto.skel()` (frozen, grouped, identified
`SkelTuple`s) or the CLI `dante-corpus text skel inferno 1:1-3` (`--format json` for tuple
dicts). `skel.antecedent` resolves a relative-pronoun subject's antecedent NP at serve time
(never stored); `skel.pro_drop_features` similarly derives person/number for a `∅` subject from
the predicate's own morphology.
