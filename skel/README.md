# skel — Layer 5: predicate-argument skeleton

Predicate ↔ argument tuples binding Layers 2-4 into bare propositions, citing **token
positions**, not raw text or lemmas — the next layer of the grammatical stack
([`../PLAN.md`](../PLAN.md)) after dependency parsing. This is the *raw* skeleton only: **no
semantic frame, no coreference, no vocabulary normalization.** Role labels are **UD-derived**
(`subj`/`obj`/`iobj`/`attr`/`xcomp`/`ccomp`/`obl:<preposition lemma>`), not semantic, so the
canon-neutral.

**Status: built for all 100 cantos, checker refined through Phase 5 (5,919 → 2,084 soft) and Phase 6 (Rules AG–AL plus three `--fix` rounds: 963 soft). `--fix` operates as a three-stage driver (deterministic auto-repair, POS-keyed micro-prompts, and fallback regeneration).**

`make -C skel check`: **0 hard, 963 soft** violations across all 100 cantos (down from 17,438 at the first full-corpus measurement). Full historical measurement tables, per-phase progressions, and empirical findings on regeneration yields are documented in [`PHASE5.md`](PHASE5.md). For current Phase 6 operating principles, active routes, and driver architecture, see [`PLAN.md`](PLAN.md) and [`CORRECTIONS.md`](CORRECTIONS.md).

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

Thirteen refinements make that divergence check meaningful rather than noisy — landed as
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
   pro-drop rule doesn't cover), and the control/participial subject of a non-finite predicate
   (**rule V**, `_control_subject_candidates`, 2026-08-09). `derive_unit` reads a predicate's own
   dep children, so a non-finite predicate with no `nsubj` child gets no `subj` row at all — it is
   silent, not asserting the predicate has no subject. Rule V walks the dep head chain and accepts
   an LLM-proposed subject that is the `subj`/`obj`/`iobj` of any ancestor up to the first one that
   has a subject of its own (control and raising through a chain of subjectless links, including
   the causative's dative causee), or the nominal an `acl` participle modifies. If the walk reaches
   a matrix whose own subject is pro-drop ∅, the controller is unresolved and any resolution is
   accepted, as in the first case. Every other role, and `subj` where `derive_unit` resolves a real
   subject, stay exact-match.
3. **`--repair`** (`Repair`/`_find_repairs`/`_safe_role_repair`), which is also `--fix`'s
   stage 1: for the subset of divergences that need no *reading*, mechanically rewrites the
   committed TSV — no model call — from the checker's own violation list (so the authority model
   above automatically gates what's eligible). Each rewrite is applied singly and re-validated,
   and rolled back if it does not clear violations cleanly. The rules split into two tiers, and
   the split is the design:
   - **Tier A asserts no reading** — the two sides spell one thing two ways.
     **role_label**: given bare `obl` against a derived `obl:<lemma>` (the dep tree's
     `case`-child detection) — the role cell is rewritten.
     **prep_stack**: given `obl:X` against derived `obl:Y` where **both** lemmas sit in the same
     `case`-child chain off the argument ("in su la cima" is chained `in` → `su` → nominal, so
     the derivation names the inner preposition and the LLM the outer one). The corpus already
     normalizes this family onto the derived side (`_PREP_LEMMA_NORM`). When the LLM names a
     preposition the tree does not carry *at all*, the two sides differ about what is attached
     and nothing is rewritten.
   - **Tier B does assert a reading**, so it fires only where a signal **independent of Layer 4**
     corroborates it — a Layer-5 divergence is evidence that Layer 4 may be the wrong side, so
     "the derivation says so" is not by itself a reason to rewrite.
     **null_subject**: a `missing_arg subj` paired with an `extra_arg subj (0,0)` (the LLM wrote
     pro-drop ∅) for the same predicate, rewritten to the derived subject **only when Layer 2's
     person/number agrees with the predicate** (`dep.subject_agreement`, the same test
     `dep --check`'s subject-agreement rule runs, extracted so the two cannot drift). Its third
     answer, "undecidable", is not a weak yes: the rule repairs only on "agree". Of the corpus's
     67 candidate pairs Layer 2 corroborates 37 and *contradicts* 20.
   - Genuine disagreements (`subj`/`obj` reversals, `iobj`/`obj` reversals, cross-lemma `obl`
     pairs the tree does not stack) are excluded and left for `--fix`'s stage 2.
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
7. **Phases 5f/5g — two `role_mismatch` acceptances, both one-directional**
   (`_oblique_lemma_refinement` / `_predicative_complement`): a given `obl:<lemma>` against a
   derived bare `obl` is accepted, because `derive_unit` emits the bare form only when no `case`
   child names the preposition — it is fused into the token (`che nel lago del cor **m'**era
   durata`), so the LLM's label adds information rather than contradicting the tree; and a given
   `xcomp` against a derived `obj`/`subj` is accepted, because UD has no relation for secondary
   predication — an object complement is attached as plain `obj` ("mi chiamaste **Ciacco**") and
   a copular predicate nominal as `nsubj` ("non son **torri**"), so the derivation can only
   report the attachment while the LLM names the predicative function. Both **mirror** directions
   stay flagged (given bare `obl` vs derived `obl:<lemma>`; given `obj`/`subj` vs derived
   `xcomp`): there the dep tree is explicit and the LLM contradicts it — the same asymmetry
   `--repair`'s `role_label` rule already rewrites on.
8. **Phase 5h — case-marked objects** (`_case_marked_object`): a given `obl:<lemma>` against a
   derived `obj`/`subj` is accepted when the argument carries a `case` child naming that same
   preposition — `derive_unit` takes the role from the deprel alone, so a case-marked nominal
   Layer 4 attached as `obj` loses the preposition that is sitting in the tree. Naming a
   *different* preposition than the `case` child stays flagged, as does the mirror direction.
9. **Phase 5j — co-present prepositions** (`_co_present_preposition`) and a rebuilt
   preposition-lemma table: Italian stacks prepositions and the dep tree attaches both markers
   to the nominal ("**in su** le porte", "dietro **a** noi"), while `derive_unit` reports only
   one, so a given `obl:<lemma>` naming another `case` child of the same argument is accepted.
   Phase 1's `_PREP_LEMMA_NORM` was at the same time rebuilt from every `case`-child word form
   in `dep/`, so preposition+article contractions (`nel` → `in`, `dal` → `da`, `al` → `a`) and
   archaic spellings (`sovr'` → `sopra`, `'nnanzi` → `innanzi`) stop reading as disagreements.
   After Layer 4's 2026-08-14 multiword-preposition normalization the lemma collection also
   aggregates a `fixed` member under its `case` row (`su` `fixed`→ `in` `case`→ nominal), so the
   rule accepts either member of the stack unchanged.
10. **Phase 5k — the clausal-complement cluster** (`_clausal_complement_flavor`,
    `_clausal_object`): `ccomp` against `xcomp` is treated as one label in either direction —
    both say *clausal complement of this predicate*, and Layer 4 splits them inconsistently on
    the same construction; and a given `ccomp` against a derived `obj`/`subj` is accepted when
    the argument is a **verb**, since Layer 4 attaches a complement clause's head verb straight
    to the matrix predicate ("or mi concedi ch'io **sappia**"). The mirror of the second (a
    given `obj`/`subj` against an explicit derived `ccomp`) stays flagged.
11. **Phase 5l — predicative adjectives attached adverbially** (`_predicative_advmod`): a given
    `xcomp` whose argument is an **adjective** attached to that predicate as `advmod` ("e io
    etterno **duro**", "va **superbo**") is accepted — rule M's construction, which Layer 4
    attached adverbially, and which `derive_unit` cannot produce at all since `advmod` is not in
    `ARG_DEPRELS`. The adjective gate is load-bearing: the same shape with an adverb argument,
    and any non-`xcomp` role, stay flagged.

12. **Phase 5r — the `case` annex as a third read** (`_case_corroborated_role`): a
    `role_mismatch` is accepted when the Layer-2 [`case/`](../case/README.md) annex's frozen value
    for the argument corroborates the **derived** role and *not* the given one — `nominative`↔
    `subj`, `accusative`↔`obj`, `dative`↔`iobj`/`obl:a`, `ablative`/`locative`↔`obl*`. This is the
    2-of-3 adjudication the annex was built for: `case` and `dep` agreeing against the LLM's
    reading, on exactly the clitic positions where the tree shape cannot decide (*mi pesa* dative
    vs *m'avea 'mmonito* accusative). Corroborating **both** sides (`obl:a` under `dative`, since
    Italian *a* marks place as well as recipient) or neither accepts nothing, the mirror direction
    is a hand-verified `dep` round rather than an automatic accept, and *fused* argument positions
    (`venendomi` = `verb+pronoun`, where the annex's value is the enclitic's while the citation is
    the verb's) are excluded by `_bare_pronoun_position`.

13. **Phase 6 — rules AH-AL, from the Inferno 7-10 read** (2026-08-14). Five acceptances, each
    measured over all 100 cantos before being written; together **1247 → 1091 soft**, no model
    calls. Full evidence in [`CORRECTIONS.md`](CORRECTIONS.md).
    - **AH** (`_apply_subj_authority`, rule AG's branch): when rule AG drops a conj-inherited
      subject whose Layer-2 person/number contradicts the predicate, the LLM's `∅` is dropped with
      it. AG was disclaiming the derived subject and then reporting the LLM's ∅ as an `extra_arg`
      about a slot the derivation no longer filled. Only `∅` — a concrete subject stays flagged.
    - **AI** (`_np_head_equivalent` / `_merge_np_head_citations`): Layer 3's NP `head` and Layer
      4's attachment point are computed independently and do not always land on the same token
      (`[più di mille]` has `head=più`; Layer 4 attaches `mille`). Since `SYSTEM_PROMPT` tells the
      model to prefer the NP head, one argument became a `missing_arg` **and** an `extra_arg`.
      Paired and dropped when both positions lie in one NP span, one of them is its head, and the
      role is the same. Two tokens sharing only a line, or a role disagreement, stay flagged.
    - **AJ** (`_conj_shared_argument`): `derive_unit`'s step 3 propagates a shared **subject**
      across a coordination and nothing else, but Italian gaps objects and datives just as freely
      ("li rami *schianta*, *abbatte* e *porta* fori"). An `extra_arg` on a `conj` predicate is
      accepted when the cited argument is an argument of some conjunct **up its chain** and the
      conjunct has no derived filler of that role. The role may differ — gapping changes it — but
      the slot must be empty, and `subj` is excluded (rules AC/AG/AH own it).
    - **AK** (`_comparative_come_complement`): a given `xcomp` against a derived `obl:come`, when
      Layer 2 tags `come` a **conjunction** and only Layer 4's `case` edge makes it a preposition
      ("staranno *come porci* in brago").
    - **AL** (`_fused_clitic_dual_role`): a `role_mismatch` between `obj` and `obl:a`/`iobj` on an
      argument Layer 2 tags as two fused pronouns (`gliel` = `gli` + `lo`), which genuinely fills
      both slots. The Phase-4 `double_listed` whitelist already accepted the `extra_arg` leg.

**Measured Progression Across Phases**:
- **Phase 4a Checkpoint (2026-07-20)**: `0 hard, 7776 soft` (down from 17,438 initial).
- **Phase 4b `--fix` Pass (2026-07-25)**: `0 hard, 5919 soft` across all 100 cantos.
- **Phase 5 Deterministic Series & Upstream Audits (Phases 5a–5w, Rules C–AF)**: Reduced soft violations from **5,919 → 2,084**. For the complete chronological record, per-phase measurement tables, Layer-4 corrections, and empirical findings on regeneration yield, see [`PHASE5.md`](PHASE5.md).
- **Phase 6 Restructured `--fix`, Rules AG–AL**: Reduced soft violations from **2,084 → 1,091** (first user-run pass: 2011 → 1452; Rule AG: 1452 → 1409; second user-run pass: 1409 → 1247; Rules AH–AL and the Inferno 7–10 read: 1247 → 1091), then **1094** after the Layer-4 agreement close and prep-stack normalization (net zero by design), then **963** with the third user-run pass (1094 → 963, 2026-08-15). See [`PLAN.md`](PLAN.md) and [`CORRECTIONS.md`](CORRECTIONS.md).

## Next steps

For active Phase 6 open routes (a queued `--fix` round, plus assistant-side manual audits of the `extra_arg subj` null-position residue, quoted speech under `parataxis`, Inferno 11–13, attributive adjectives, and promoted adverbs — the stacked-preposition route closed 2026-08-14 with Layer 4's multiword-preposition normalization), see the active plan in [`PLAN.md`](PLAN.md).

`--fix` (`skel/skel.py`) keeps a change only if the unit's soft violation count strictly drops
**and** no violation class appears that wasn't already there (`_is_improvement`, Phase 5c — the
plain count test let the Phase 4b round trade a net drop for `unknown_role` 0 → 2, a role outside
the frozen vocabulary). That gate now applies **per stage**, so the no-worse-off guarantee holds
at each step rather than only across the pass.

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

uv run skel/skel.py inferno [-c 1] [-m MODEL] [--chunk 12] [--force] [--check] [--stats]
uv run skel/skel.py inferno purgatorio paradiso --repair    # no model call
uv run skel/skel.py inferno -m ollama:gpt-oss --fix         # all three stages
uv run skel/skel.py inferno -m ... --fix --no-whole         # without the regeneration fallback
```

Consumers read it deterministically via `Canto.skel()` (frozen, grouped, identified
`SkelTuple`s) or the CLI `dante-corpus text skel inferno 1:1-3` (`--format json` for tuple
dicts). `skel.antecedent` resolves a relative-pronoun subject's antecedent NP at serve time
(never stored); `skel.pro_drop_features` similarly derives person/number for a `∅` subject from
the predicate's own morphology.
