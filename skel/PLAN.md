# skel — Layer 5 soft-violation elimination plan

Status as of 2026-07-20: `make -C skel check` reports **0 hard, 14329 soft** violations across
all 100 cantos (down from 17438 after three days of per-canto fix rounds). The project goal is
**0 soft violations** — soft divergences are rule mismatches to eliminate, not a baseline to
tolerate (see the corpus-wide premise recorded after the first full check).

## Why the current process is inefficient

Two structural problems, not a lack of effort:

1. **Fixes are applied per canto, but violations cluster by class.** The distribution below
   shows a handful of divergence classes account for the large majority of all 14329 instances.
   One deterministic change to the checker or a mechanical rewrite rule kills thousands of
   instances at once; re-reading cantos one at a time kills dozens.
2. **LLM regeneration (`--fix`) is a stochastic tool applied to deterministic problems.** Each
   re-roll can fix some lines and break others; there is no convergence guarantee, so rounds
   repeat. Every divergence whose "correct" answer is already known mechanically (from the
   Layer 4 dep tree, or from a normalization rule) should be fixed by a script, not by
   re-asking the model.

## Measured violation distribution (2026-07-20, 14329 total)

By kind:

| kind          | count | notes                                                          |
|---------------|-------|----------------------------------------------------------------|
| extra_arg     |  7035 | subj 4666 (of which ∅ `(0,0)`: 2227), obj 593, obl:di 358, …   |
| missing_arg   |  3782 | subj 1718 (of which ∅ `(0,0)`: 591), ccomp 567, obl 368, …     |
| role_mismatch |  2392 | see below                                                      |
| extra_tuple   |   914 | LLM-only predicates (elided copula etc.)                       |
| missing_tuple |   117 | derived predicates the LLM never proposed                      |
| membership    |    89 | "argument … heads no NP/pronoun/predicate"                     |

Top role_mismatch pairs (given = LLM, derived = `derive_unit`):

| given vs derived        | count | diagnosis                                        |
|-------------------------|-------|--------------------------------------------------|
| 'attr' vs 'xcomp'       |   482 | same copular-complement reading, two labels      |
| 'subj' vs 'obj' (+rev.) |   279 | genuine disagreements, inspect                   |
| 'iobj' vs 'obl:a'/'obl' |   157 | dative alternation labeling                      |
| 'iobj' vs 'obj' (+rev.) |   145 | genuine disagreements, inspect                   |
| 'obl:sanza' vs 'obl:senza' |  73 | orthographic variant of the same preposition   |
| 'obl:di' vs 'obl'/'obj' |   145 | prep-lemma detection asymmetry                   |
| 'obl:sovra' vs 'obl:sopra' |  52 | orthographic variant                           |
| 'obl:de' vs 'obl:di'    |    47 | orthographic variant                             |

Subject-related divergence alone (extra_arg subj + missing_arg subj = 6384) is 45% of the
total, and most of it traces to two known structural gaps already documented in
`CORRECTIONS.md`: xcomp/ccomp control subjects and pro-drop ∅ vs. discourse antecedents.

## Plan

### Phase 0 — add `--stats` to the checker (measurement first)

`skel/skel.py --check` currently prints one line per violation and a total; per-class impact of
a fix round is invisible without ad-hoc grep/awk. Add a `--stats` flag that aggregates
violations by (kind, role, ∅-or-real) and by role_mismatch pair, exactly like the tables above.
Every subsequent phase is then measured as "class X: N → M" instead of a bare total.

Touches: `skel/skel.py` (CLI + report), no artifact changes.

### Phase 1 — normalization layer before the diff

Insert a canonicalization step in `dante_corpus/skel.py` applied to **both** the given and the
derived side before `_classify_divergence` compares them. All of these are label-level
equivalences, not disagreements about the parse:

1. **Preposition lemma normalization** for `obl:<prep>` roles: `sanza → senza`,
   `sovra → sopra`, `de → di`, plus any further variants `--stats` surfaces. (~200 instances)
2. **Role equivalences**, canonicalized to one form:
   - `attr` ≡ `xcomp` when the argument is the same token (the copular-complement labeling
     split; canonical: follow the derived side's label). (~480 instances)
   - `iobj` ≡ `obl:a` (dative alternation; pick one canonical label). (~160 instances)
3. **Clausal-complement double-listing**: `derive_unit` lists a `ccomp`/`xcomp` clause both as
   an argument of the matrix predicate and as its own tuple; the LLM usually lists only the
   tuple. Accept a missing `ccomp`/`xcomp` arg when the same (line, token) is proposed by the
   LLM as its own predicate. (~700 instances: missing_arg ccomp 567 + xcomp 128)

Touches: `dante_corpus/skel.py` (`_classify_divergence` or a `_canonicalize` helper),
`tests/test_skel.py`. No artifact changes — pure checker fix.

### Phase 2 — authority model: exact match only where the parse determines the answer

The root design tension: the checker demands exact equality on slots the Layer 4 tree does not
determine. Make the authority explicit per slot:

- **Derive-authoritative** (dep tree has an explicit edge): exact match required, as now.
- **LLM-authoritative** (mechanically underdetermined): validate against a *candidate set*
  instead of demanding equality.
  - *Pro-drop antecedents*: where `derive_unit` produces ∅ `(0,0)`, accept any concrete
    subject the LLM cites, subject to the existing NP-membership check. ∅ is the weakest
    claim; a resolved antecedent is strictly more informative, not wrong.
    (missing_arg subj ∅ 591 + their paired extra_args)
  - *xcomp/ccomp control subjects*: `derive_unit` derives no subject for a controlled
    complement. Accept an LLM-proposed subject iff it equals the matrix predicate's subj or
    obj (covers both subject-control `sembiare`/`parere` and object-control `fare` without a
    verb-specific control lexicon — the candidate set replaces the lexicon).
    (large share of extra_arg subj 4666)
  - *Non-finite ∅*: the LLM marks ∅ subjects on infinitives/gerunds where `derive_unit`'s
    pro-drop rule requires finiteness. Accept ∅ on any verbal predicate.
    (large share of extra_arg subj ∅ 2227)

Touches: `dante_corpus/skel.py` (`_classify_divergence` needs access to the derived matrix
tuples; thread them through), `tests/test_skel.py`.

### Phase 3 — `--repair`: mechanical TSV rewriting for derive-authoritative errors

For divergences where the derived answer is trusted and the LLM's is wrong, do **not**
regenerate with the LLM. Add a `--repair` mode that rewrites the committed TSVs
deterministically, one pass, guaranteed convergence:

- LLM wrote ∅ where `derive_unit` derived a real subject from an explicit `nsubj` edge
  (e.g. an enjambment subject on the next line): replace `(0,0)` with the derived citation.
- Role-label corrections that survive Phase 1 normalization but where the dep tree is explicit
  (e.g. `obl` vs `obl:di` when the `case` child exists): rewrite to the derived role.

Each repair rule must be conservative: apply only when the dep tree fully determines the
answer, and log every rewrite (same discipline as `dep/CORRECTIONS.md`). Run corpus-wide,
commit the diff as one reviewable change.

Touches: `skel/skel.py` (new mode), `dante_corpus/skel.py` (expose repair candidates from the
diff), artifacts under `skel/*/`.

### Phase 4 — targeted LLM regeneration, last resort only

After Phases 1-3, re-run `--stats`. What remains should be genuine LLM misreadings
(e.g. inferno 1:4's subject mix-up across the enjambment, subj/obj reversals) plus the small
structural classes (elided-copula extra_tuples 914, membership 89). Only then use `--fix`,
restricted to the specific flagged lines, and re-check per class. Elided-copula predicate
nominals may end as a narrow, explicitly whitelisted acceptance rule in `validate_unit`
(predicate nominal with no verb token in the unit) rather than as standing violations —
consistent with the goal that even "exemptions" must not remain as nonzero counts.

### Expected impact

Rough attribution of the 14329 (some instances pair up — one disagreement produces both a
missing_arg and an extra_arg — so classes overlap and these do not sum linearly):

- Phase 1: ~1500 instances (normalizations + double-listing)
- Phase 2: ~6000-7000 instances (the subj-related 45% is mostly this)
- Phase 3: ~1000-2000 instances (∅→real-subject repairs and residual role rewrites)
- Phase 4: the remainder, expected in the low thousands at most, handled per class.

Phases 0-2 are pure checker changes (no artifact edits) and should land first; they are safe,
testable, and shrink the problem before any TSV is touched.

## Documentation to update on completion

- `skel/CORRECTIONS.md`: record each phase's class → count reduction (measure-then-freeze).
- `dante_corpus/README.md` / root `PLAN.md`: checker semantics changes (normalization,
  authority model, `--repair`, `--stats`).
