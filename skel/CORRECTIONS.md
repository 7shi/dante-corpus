# skel — Layer 5 correction history

## Checker Phase 3: `--repair` mechanical TSV rewriting (2026-07-20)

Corpus-wide baseline before this round (`make -C skel check`, all 100 cantos): **0 hard, 9672
soft** — Phase 2's ending state, reproduced exactly. Phase 3 is the first pass that touches the
artifact itself (every `skel/<canticle>/<NN>.tsv` with an eligible
divergence), using a new `--repair` mode (`skel/skel.py`) that rewrites committed rows
deterministically — no model call — via two conservative rules in `dante_corpus/skel.py`'s new
`Repair`/`_find_repairs`/`_safe_role_repair`, sourced entirely from `_classify_divergence`'s own
violation list (already passed through Phase 2's `_apply_subj_authority`), never recomputing the
diff independently:

1. **null_subject** — a `missing_arg subj` (`derive_unit` resolved a real subject from an
   explicit `nsubj` edge, e.g. an enjambment subject on a preceding line) paired with an
   `extra_arg subj (0,0)` (the LLM wrote pro-drop ∅) for the *same* predicate: the ∅ row's
   citation is replaced with the derived one. Requires *both* violations present for the same
   predicate — a lone one of either means Phase 2's authority model already accepted it, or the
   two sides cite different real subjects (genuine disagreement), and no repair fires. Effect:
   `extra_arg subj` dropped **2133 → 1350** (of which ∅ `(0,0)`: **878 → 95**); `missing_arg subj`
   dropped **1127 → 344**. **783** rewrites across 100 cantos.
2. **role_label** — a `role_mismatch` where the given role is bare `obl` and the derived role is
   `obl:<lemma>` (`derive_unit`'s `case`-child detection — the only role_mismatch shape that is
   dep-tree-explicit post-Phase-1-normalization): the role cell is rewritten to the derived label.
   Explicitly does **not** fire for `subj`/`obj` or `iobj`/`obj` reversals (either direction) or
   for `obl:<lemma1>` vs `obl:<lemma2>` (cross-lemma) pairs — all genuine disagreements per this
   file's Phase 0 "Top role_mismatch pairs" table, left for Phase 4. Effect: `role_mismatch`
   dropped **1487 → 1466** (Δ21, exactly the **21** rewrites this rule made).
3. **Side effect, not fixed by this phase**: `membership` rose **89 → 94** (Δ+5). In these five
   cases (e.g. paradiso 6:142's `subj` citation to `(136,3)`, the archaic accusative clitic `il`
   in "E poi il mosser le parole biece") `derive_unit`'s `nsubj`-edge resolution points at a token
   Layer 3's NP-span/pronoun data doesn't recognize as heading an argument — a genuine Layer
   3/4 boundary case that repair's null_subject rule surfaces rather than causes. Left as-is and
   folded into Phase 4's existing `membership` backlog (deliberately not special-cased in
   `_find_repairs`, to keep the rule's precondition — "both a missing_arg and a paired ∅ extra_arg
   for the same predicate" — the sole gate, rather than adding a second, NP-membership-shaped
   gate that duplicates the checker's own membership logic).

Tests (`tests/test_skel.py`): `test_find_repairs_null_subject_pairs_missing_and_extra`,
`test_find_repairs_null_subject_then_reclassify_is_clean`,
`test_find_repairs_null_subject_not_produced_when_pro_drop_authoritative`,
`test_find_repairs_null_subject_not_produced_for_xcomp_control_accept`,
`test_find_repairs_null_subject_not_produced_for_genuine_disagreement`,
`test_find_repairs_role_label_bare_obl_to_lemma`,
`test_find_repairs_role_label_then_reclassify_is_clean`,
`test_find_repairs_role_label_rejects_subj_obj_reversal`,
`test_find_repairs_role_label_rejects_different_obl_lemma`,
`test_find_repairs_role_label_rejects_iobj_obj_reversal`.

Corpus-wide run: `make -C skel repair` — **804** total rewrites (783 null-subject + 21
role-label) across 100 cantos, touching 100 `skel/<canticle>/<NN>.tsv` files (804 rows changed,
804 removed — a clean 1:1 replace per row, verified by diff; re-running `--repair` afterward is a
no-op, confirming convergence). By kind, before → after: `extra_arg` 4502 → 3719, `missing_arg`
2563 → 1780, `role_mismatch` 1487 → 1466, `extra_tuple` 914 → 914 (untouched, Phase 4), `missing_
tuple` 117 → 117 (untouched, Phase 4), `membership` 89 → 94 (see item 3 above).

**Current state**: `make -C skel check` — **0 hard, 8090 soft** (down from 9672 at Phase 2's end,
Δ1582, 16.4%; down from 14329 at the start of Phases 0-2, overall Δ6239, 43.5%). Every touched
`skel/<canticle>/<NN>.tsv` was committed alongside this entry. Phase 4 (targeted `--fix`/hand
corrections for the remainder — genuine subj/obj/iobj reversals, elided-copula extra_tuples,
membership) is still open; see `skel/README.md`'s *Next steps*.

## Checker Phases 0-2: normalization + authority model (2026-07-20)

Corpus-wide baseline before this round (`make -C skel check`, all 100 cantos): **0 hard, 14329
soft**. Phases 0-2 are pure checker changes — no artifact
edited — that shrink the soft-violation count deterministically before any TSV is touched
(Phase 3) or the LLM is re-invoked (Phase 4). All three phases (`dante_corpus/skel.py`,
`skel/skel.py`) landed together in this pass; measured **corpus-wide `--stats` after each
phase**, not just the final number, so each phase's own contribution is on record.

1. **Phase 0 — `--stats`** (`skel/skel.py`): added a `--stats` flag/`stats()` function that
   aggregates `validate_unit`'s soft `Violation`s by kind, by `(kind, role, ∅-or-real)`, and by
   `role_mismatch` pair, instead of the one-line-per-violation dump `--check` prints. Required
   extending the shared `Violation` dataclass (`dante_corpus/morph.py`) with optional
   `role`/`given_role`/`arg`/`predicate` fields, populated only by `skel._classify_divergence` —
   additive, no other layer's `Violation` construction changed. Baseline reproduced exactly:
   7035 extra_arg / 3782 missing_arg / 2392 role_mismatch / 914 extra_tuple / 117 missing_tuple /
   89 membership = 14329, matching the original plan's published table verbatim (measurement only, no
   count changed).
2. **Phase 1 — normalization layer** (`dante_corpus/skel.py`, `_canonicalize_role`/
   `_normalize_prep_lemma`, applied inside `_classify_divergence`'s `by_arg` comparison and
   inside `derive_unit`'s own `obl:<lemma>` construction): canonicalized both sides of the diff
   toward the derived side's convention before comparing.
   - Preposition-lemma orthographic variants: `sanza`/`sanz`/`sans` → `senza`,
     `sovra`/`sovr'`/`sor` → `sopra`, `de` → `di`, `contra`/`contr` → `contro`, `ver` → `verso`,
     `ad` → `a`, `col`/`coi` → `con` (the last four extend the original plan's three named pairs, found
     via `--stats`'s role_mismatch-pairs table as it recommends).
   - Role-label splits for one reading: `attr` ≡ `xcomp` (copular-complement labeling),
     `iobj` ≡ `obl:a` (dative alternation) — both canonicalize to the derived side's label.
   - Clausal-complement double-listing: a `missing_arg` for a `ccomp`/`xcomp` derived role is
     suppressed when the argument token is itself proposed as its own predicate tuple by the LLM.
   - Effect: **14329 → 12825** (Δ1504, close to the original ~1500 estimate). `role_mismatch`
     dropped 2392 → 1584; the `attr`/`xcomp`, `iobj`/`obl:a`, and all seven orthographic prep
     pairs no longer appear in the pairs table. Tests: `test_validate_unit_divergence_
     normalizes_attr_xcomp_and_prep_variants`, `test_validate_unit_divergence_ccomp_double_
     listing_suppressed` (`tests/test_skel.py`).
3. **Phase 2 — authority model for `subj`** (`dante_corpus/skel.py`, `_apply_subj_authority`,
   threaded into `_classify_divergence` via a new `dep_index_by_pos` parameter built from
   `dep_rows` at `validate_unit`'s call site): made the `subj` slot LLM-authoritative (validated
   against a candidate set, not exact-matched) in exactly the three cases the original plan named, no
   further:
   - **Pro-drop antecedent** — `derive_unit` produced `subj (0,0)`: any concrete subject the LLM
     resolves is accepted (strictly more informative than ∅, not wrong).
   - **Non-finite ∅** — `derive_unit` produced no `subj` row at all for the predicate: an
     LLM-proposed `(0,0)` is accepted.
   - **xcomp/ccomp control subject** — `derive_unit` produced no `subj` row and the predicate's
     own deprel (via `dep_index_by_pos`) is `xcomp`/`ccomp`: an LLM-proposed subject is accepted
     iff it equals the matrix predicate's derived `subj` or `obj` — replaces the verb-specific
     control lexicon the pilot-build note above (Item 1, 2026-07-13) explicitly deferred, with a
     structural candidate-set check instead (no lexicon, still UD-deprel-only).
   - Every other role, and `subj` where `derive_unit` derives a real (non-∅) subject, stay
     exact-match — this is deliberately narrower than "any subject disagreement is fine": a
     control-subject candidate outside the matrix subj/obj pair, or a `subj` disagreement on a
     predicate `derive_unit` already resolves, still flags (`test_classify_divergence_xcomp_
     control_subject_rejects_unrelated_arg` asserts this negative case explicitly).
   - Effect: **12825 → 9672** (Δ3153; the original ~6000-7000 estimate for this phase was
     explicitly rough/non-additive — the actual figure is lower because a meaningful share of
     `extra_arg subj`/`missing_arg subj` are genuine LLM/derivation disagreements on predicates
     `derive_unit` *does* resolve a real subject for, which correctly remain exact-match and
     unaffected). `extra_arg subj` dropped 4666 → 2133 (of which ∅ 2227 → 878); `missing_arg
     subj` dropped 1718 → 1127. Tests: `test_classify_divergence_non_finite_predicate_accepts_
     null_subject`, `test_classify_divergence_xcomp_control_subject_accepts_matrix_arg`,
     `test_classify_divergence_xcomp_control_subject_rejects_unrelated_arg`.

**Current state**: `make -C skel check` — **0 hard, 9672 soft** (down from 14329; Δ4657, 32.5%).
No artifact under `skel/*/` was touched — this is checker-only, per the plan's gate before
Phase 3 (`--repair`, mechanical TSV rewriting) and Phase 4 (targeted `--fix`/hand corrections),
both still open. `dante_corpus/README.md`'s Layer-5 section (still to be written — see root
`PLAN.md`'s Handoff) and root `PLAN.md`'s Layer-5 "Check" paragraph should describe the
derive-authoritative/LLM-authoritative distinction once Phase 3/4 land alongside it.

## Pilot build, Inferno 1 (2026-07-13)

First build (`uv run skel/skel.py inferno -c 1 -m ollama:gemma4:31b-it-qat`) hit 3/3 retry
failures on lines 55-60, all identical: the model cited `59.2 venendomi` (gerund `venire` fused
with the enclitic dative pronoun `mi` — Layer 2 lemma `venire+mi`, no separate token exists for
`mi`) as its own argument, tripping the hard self-citation check. Fixed in `SYSTEM_PROMPT`
(`skel/skel.py`) with an explicit rule: a verb token with a fused enclitic pronoun encodes that
pronoun internally; do not cite it, or the predicate's own position, as a separate argument. No
`derive_unit` change — this is a token-citation constraint the prompt needs to state, not a
divergence the deterministic derivation gets wrong.

After that fix, the canto built clean: **0 hard** violations, all 136 lines committed.

### Soft-divergence triage (`--check`: 0 hard, 136 soft before the fixes below)

Every soft violation was inspected by comparing the LLM's rows against `derive_unit`'s output
for the same parse unit (not just the violation's one-line detail). Four distinct root causes
emerged, none of them the mixed-copular-style pattern the *Handoff* section predicted as the
likely largest class — that pattern (`è root`/`cosa attr` vs `amara`/`è cop`) barely appears in
canto 1; the actual largest class is different and still open (see below).

1. **`xcomp`-complement subject/object control (largest class, ~50+ of 136 soft violations)** —
   copular-raising verbs (`sembiava carca`, `parea fioco`) and causative `fare` (`fé... viver
   grame`, `fai... mesti`) both take an `xcomp` complement whose own implicit subject
   `derive_unit` currently leaves unfilled (only `conj`-chain subject sharing is implemented, not
   `xcomp`/`ccomp` control). The LLM consistently filled it in, but with an important wrinkle:
   `sembiare`/`parere` are **subject-control** (the xcomp's implicit subject = the matrix
   predicate's own subject) while `fare` is **object-control** (the xcomp's implicit subject =
   the matrix predicate's direct object) — a lexically-governed distinction, not one derivable
   from UD deprels alone. **Deferred, not fixed**: extending `derive_unit` would mean encoding a
   verb-specific control lexicon, which sits uneasily with this layer's "no semantic frame, UD
   deprels only" design (see `dante_corpus/skel.py`'s module docstring and PLAN.md's *Out of
   scope*). Revisit once more cantos are built and the pattern's shape (how many verbs, how
   reliably subject- vs object-control splits along closed verb classes) is actually measured,
   per the *measure-then-freeze* discipline — a single canto is too small a sample to freeze a
   control lexicon against.
2. **Elliptical predicate nominals with no verb token at all** (`mantoani per patrïa ambedui` —
   "[we were] Mantuans by homeland", copula elided; `Non omo, omo già fui` — "[I was] not a man,
   [but] a man I once was", first `omo` has no copula at all) — `derive_unit`'s two predicate
   rules both require either a clause-head deprel or a verb token; an elided-copula predicate
   nominal satisfies neither structurally. Genuinely unexpressable by the current derivation, not
   a bug. **Exemption, not fixed** — same shape as `dep/CORRECTIONS.md`'s substantivization
   cases: a real reading the mechanism can't cite, checked by hand against its terzina, not a
   parse error.
3. **NP-membership soft-check false positives, fixed deterministically** (`dante_corpus/skel.py`
   `validate_unit`) — two sub-patterns, both mechanical widenings of the membership check, not
   changes to `derive_unit` or any artifact:
   - Relative pronoun `che`/`ch'` cited as a `subj`/`obj`/`obl` argument is correctly Layer-5
     usage, but Layer 2 tags `che`/`ch'` inconsistently between `pronoun` and `conjunction` even
     in its relative use (`morph/CORRECTIONS.md`'s `che`/`ch'` mistag section), so the
     POS-based pronoun check missed it. Fixed by also accepting the word form itself
     (`che`/`ch'`/`cui`/`qual`/`quale`/`chi`) regardless of the frozen POS tag.
   - An adverbial oblique (`quivi`, `là`, `sù`, `dietro`) is a legitimate `obl`/`obl:*` argument
     with no NP to cite — adverbs were simply never in the membership check's acceptance set.
     Fixed by accepting an adverb-POS token specifically for `obl`/`obl:*` roles (not for
     `subj`/`obj`/`iobj`, where an adverb would still be a genuine miscitation).
   - Tests: `tests/test_skel.py`'s four new `test_validate_unit_membership_*` cases.
   - Effect on canto 1: 13 -> 2 membership violations (11 resolved: 6 relative-pronoun instances,
     5 adverb instances). `--check`: **136 -> 125 soft** (0 hard throughout).
4. **Two single-instance boundary cases, left as-is** — inferno 1:59 `'ncontro` (the model, having
   been told not to cite the fused-enclitic argument of `venendomi` directly per item 1's build
   fix, cited the adjacent preposition instead — a defensible fallback, not wrong, but not a
   nominal citation either); inferno 1:110 `l'` (elided direct-object clitic `lo`, graphically
   identical to an elided article, so Layer 2 tags it `article` — genuinely ambiguous without
   deeper morph-layer work, out of scope for this pass). Both remain flagged by the membership
   check; revisit only if the pattern recurs at scale.

**Current state**: `skel/inferno/01.tsv` — **0 hard, 125 soft** (`uv run skel/skel.py inferno -c
1 --check`). Item 1 (xcomp control) is the dominant remaining class and is an open design
question, not a bug to silently fix; items 2 and 4 are structural/POS-ambiguity limits expected
to recur at low, tolerable rates across the corpus. No canto-2+ build has been run yet.
