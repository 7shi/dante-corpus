# The Hard Classification, Audited

The soft counterpart is [`SOFT.md`](SOFT.md) (record S6.1), which asks the
same four questions of the 5,014 soft findings and answers two of them
differently — and which corrects one claim made here (§4.3's "impossible by
construction"; see the note there).

An evidence record for one question, asked before the clausal repair design
pass was opened: **is the hard classification itself sound — not "is it
correctly implemented", but "does its justification hold"?** The violation
counter selects work ([`STAGE5.md`](STAGE5.md) §5 discipline 1), so before
letting 70 hard violations drive a design pass, the classification that
produces them was audited rather than taken a priori.

**Status**: audit record only, filed as [`STAGE5.md`](STAGE5.md) record
S5.4. No repair rule was designed here, no artifact was edited, and no
rule-choosing number below was read off gold. Run 2026-08-30 against the
tree at S5.3 (`6323d95`, working tree clean; suite 916 passed; `make check`
70 hard / 4,988 soft; `make repair-check` clean), and re-verified the same
day by an independent second pass that re-derived every figure and
corrected four of them (§7).

---

## 1. The question

`make check` reports each recon TSV against the frozen L1–L4 layers and
splits `skel.validate_unit`'s output by `kind`: `tag` → soft, everything
else → hard ([`recon/check.py`](recon/check.py) `_classify_violations`).
The 70 hard violations are all one class, `[clausal] xcomp/ccomp argument
is not a predicate in this unit` ([`dante_corpus/skel/validate.py`](../dante_corpus/skel/validate.py)
115–122). Before repairing them, the question: **what does "hard" rest on,
and does that rest hold?** An auditor's answer needs four things: what the
invariant asserts, where its authority comes from, whether the severity
(hard, not soft) is consistent with the contract's own taxonomy, and whether
any reading of the 70 rows shows the checker misfiring.

## 2. What the classification is

- **The invariant.** Every row whose role is `xcomp` or `ccomp` must cite,
  as its argument, a position that is itself a registered predicate (a row
  with `token > 0`) in the same parse unit (`validate.py` 115–122; the
  predicate set is `_predicate_positions_in`, which counts any `token > 0`
  row regardless of role). This is a closed-world, artifact-internal check:
  it reads the TSV against itself and no other layer.
- **The published contract, and a gap in it.**
  [`skel/README.md`](../skel/README.md) 79–80 publishes the hard bar as
  *the predicate token exists in Layer 1 and every argument position is a
  valid in-unit token position or the `(0,0)` sentinel* — the clausal
  invariant is **not named there**. (Line 83's "a Layer-3 NP head, a
  Layer-1 pronoun token, or an in-unit predicate (clausal argument)" is the
  **soft** bullet's *nominal*-role membership rule — the very check §4.2
  contrasts the clausal one against — so it cannot double as this
  invariant's authority.) The authority is therefore `validate.py` 115–122
  plus `derive.py`'s derivation (§4.1) — the contract
  [`STAGE5.md`](STAGE5.md) §5 designates — and README's hard bullet lags
  the checker: a documentation gap recorded here, not a defect in the check.
- **Parity with gold's checker.** `recon/check.py` wraps the same
  `validate_unit` (and the same tag→soft split) that `skel/skel.py --check`
  applies to gold; the hard classes and exit semantics are identical, only
  the artifact root differs.
- **Calibration.** Gold scores **0 hard / 0 soft** under this checker
  (re-verified live: `uv run python -m harness.recon.check --root skel
  --stats`). This is the sanctioned use of gold — calibration of the bar,
  not a target ([`STAGE5.md`](STAGE5.md) §5) — and it establishes the
  invariant is satisfiable with the full constructional coverage of the
  corpus.

## 3. The 70 positions, audited gold-closed

Method: each violation's row was recovered from the recon TSVs and joined,
position by position, against the frozen layers only — L1 token, L2 morph
(POS/lemma), L4 dep (deprel, head, children) — plus two corpus-wide
membership questions (is the cited position registered as a predicate
anywhere in the recon corpus; does its line carry any predicate rows at
all). No gold file was opened by the audit.

| Evidence at the cited argument position | Count (of 70) |
|---|---|
| L4 deprel `xcomp` | 51 |
| L4 deprel `ccomp` | 8 |
| L4 deprel `obj` | 5 |
| L4 deprel `conj` | 3 |
| L4 deprel `nsubj` | 3 |
| L2 POS adjective (participles incl.) | 43 |
| L2 POS verb / verb+pronoun | 16 / 3 |
| L2 POS adverb / interjection / pronoun / noun | 4 / 2 / 1 / 1 |
| cited position registered as a predicate **anywhere** in recon | **0** |
| cited position's line has zero predicate rows | 7 |
| cited position heads a clause in L4 (has dep children) | 40 |
| …of those, with an argument-bearing child (`ARG_DEPRELS`) | 13 |

Readings:

1. **Zero checker misfires.** In all 70 cases the cited position is genuinely
   unregistered — the checker never flags a citation that resolves. A
   unit-boundary false positive (predicate registered in a neighboring unit)
   was the obvious candidate and is ruled out corpus-wide: 0 of 70 resolve
   anywhere, not just in-unit.
2. **The dominant case is L4-faithful.** 59/70 cite a token L4 itself marks
   with a clause-head deprel (`xcomp` 51, `ccomp` 8), and in **56** of them
   L4 attaches that token to the citing predicate itself — the model copied
   the frozen tree's clausal attachment. The row is not wrong about the
   grammar; it is an **incomplete registration**: the artifact carries the
   citation without carrying the clause the citation names. The 3 remaining
   carry the clausal deprel under a *different* head — `inferno 19:73`
   `tratti xcomp → piatti (75,7)` (L4 head `(73,6)`), `paradiso 6:27`
   `dovessi xcomp → posarmi (27,7)` (L4 `ccomp` of `(27,3)`), `paradiso
   28:33` `sarebbe xcomp → contenerlo (33,3)` (L4 head `(33,5)`) — so the
   citation's *attachment* diverges from L4 even though its clause-hood
   claim does not; registration would still resolve them (§6).
3. **The POS split separates two sub-populations.** 43 cite an adjective
   (L2) — resultative/depictive small clauses ("fa morta", "tien stretti"):
   the derivation would *not* treat these as clause heads by POS, so the
   alternative is a different notation (below). 19 cite a verb or fused
   verb+pronoun — true clausal infinitives ("esser", "irmi", "posarmi"):
   the derivation *would* register these, so the citation is one missing
   registration away from resolving. The 8 remaining (adverb, interjection,
   pronoun, noun) cite tokens no reading promotes. Crossed with the deprel
   split, the 59 clausal-deprel rows are 40 adjective / 14 verb / 5 other,
   and the 11 non-clausal rows are 3 adjective / 5 verb / 3 other.
4. **Why the corpus committed them at all.** The agent-side gate
   `validate_candidate` ([`runner/tools.py`](runner/tools.py) 675, docstring
   685–698) *deliberately* does not enforce predicate membership for clausal
   roles — "complements cite their clause's predicate head by nature, so
   holding them to the nominal rule would reject correct analyses". The
   invariant is enforced only corpus-side, after commit. The tool's
   looseness and the checker's strictness are two registers of the same
   contract (§4.2); the 70 rows are what falls into the gap between them.

## 4. The basis, tested

### 4.1 The invariant is the derivation's own closure property

The decisive question: is "a clausal citation must resolve to a registered
predicate" an external demand, or something the layer's own derivation
already guarantees? It is the latter, and it can be watched happening.

- [`dante_corpus/skel/derive.py`](../dante_corpus/skel/derive.py) 131–142:
  every position L4 marks with a clause-head deprel (`root`, `ccomp`,
  `xcomp`, `csubj`, `csubj:pass`, `advcl`, `acl`, `acl:relcl`,
  `parataxis` — 35–38) is **promoted to a registered predicate before any
  citation is emitted** (exclusions: rule BN conjunctions, rule AN
  orphan-headed non-verbs).
- derive.py 288–290: only then does `_DIRECT_ROLE_MAP` emit the
  `xcomp`/`ccomp` citation, now guaranteed to resolve.

Empirically, `derive_unit` on the inferno 10 unit containing line 15
("che l' anima col corpo morta fanno", the L4 `xcomp` case behind the
audit's first row) derives **both** sides of the move: `fanno xcomp →
(15,6)` *and* a placeholder predicate row `morta '' → (0,0)` registering
(15,6); `validate_unit` over the fully derived artifact returns 0 hard,
0 clausal. The recon TSV carries the first half and not the second.

So the hard check is **the derivation's closure property restated as an
admission condition on the artifact**: an artifact may not assert a
citation whose referent the artifact itself does not contain. It is the
same family as `self_arg` and `dup` — an assertion the format cannot
interpret — and the plan's discipline 3 already names this authority
("the schema declares the current row impossible", [`PLAN.md`](PLAN.md)
§4; [`STAGE5.md`](STAGE5.md) §5).

### 4.2 The severity assignment is consistent with the contract's own taxonomy

The surface tension: the *nominal* membership check ("argument heads no
NP/pronoun/predicate", validate.py 150–179) is the same reference-integrity
principle and is classified **soft** (`tag`), while the clausal variant is
**hard**. The contract's own structure explains the split:

- **Hard = exception-free format impossibility** (`dup` — duplicate rows and
  the self-argument case alike — plus `position`, `word`, `sentinel`,
  `clausal`). A clausal argument has exactly one
  realization in this format — a registered predicate frame — so an
  unresolved clausal citation has no reading at all, and the contract
  publishes no tolerance for one.
- **Soft = divergence within a published tolerance.** The nominal check is
  soft *because* the contract publishes exceptions for it (rules AF/AQ/DG/DS,
  the adverbial-oblique allowance): a nominal argument has several sanctioned
  realizations, so "heads no NP/pronoun/predicate" is a defeasible finding,
  not an impossibility.
- **The Rule R/M/P non-conflict.** The soft taxonomy does tolerate
  xcomp-shaped divergences (rules M, P, Q, R in the registry). These are
  *scoring*-register tolerances — they classify the diff between a given
  frame and the derived frame at matched predicates — while the hard check
  is the *admission* register for the committed row. The 70 rows sit in
  both (some also carry a soft `role_mismatch`), and both reports are
  correct on their own registers. The registers must not be conflated: a
  scoring tolerance is never an admission permission.
- **The two notations.** `attr` and `xcomp` are canonically one role
  (`_ROLE_CANON`, [`dante_corpus/skel/models.py`](../dante_corpus/skel/models.py)
  204: `{"attr": "xcomp", ...}`; `_canonicalize_role` 211–215), and the
  contract publishes both as admissible ways to assert a predicative
  complement — `attr` makes no clause-hood claim and demands no
  registration (validate.py 151 exempts it from the membership check),
  `xcomp`/`ccomp` claim clause-hood and incur the registration duty. Gold
  notates adjective complements as `attr`; the derivation notates them as
  `xcomp` + registration; both pass 0/0. The 70 rows chose the strong
  notation while performing only the weak registration. The invariant is
  what makes the notation choice mean something: it is the enforcement of
  "if you assert a clause, the artifact must contain the clause".

### 4.3 Falsification attempts, all failed

- *Unit-boundary artifact*: predicate registered in a neighboring unit
  flagged as absent — ruled out, 0/70 resolve anywhere in the corpus (§3).
- *Derivation conflict*: a case where `derive_unit` itself emits an
  unresolved clausal citation — none; the promotion-then-cite ordering
  (§4.1) makes it impossible by construction, verified on a live unit.
  **Corrected 2026-08-30 by [`SOFT.md`](SOFT.md) §4.1**: sweeping the
  derivation's own output over all 100 cantos found exactly one —
  `paradiso 18:83 [clausal] xcomp argument (84, 3) is not a predicate`, a
  gapped-coordination `orphan` remnant cited but never promoted, because the
  gapping path bypasses the deprel-driven promotion §4.1 relies on. The
  closure property holds at 3,476 of the 3,477 units and nothing else in §4
  depends on it, but the unqualified "by construction" does not stand.
- *Coverage loss*: a construction the invariant forbids expressing — none;
  gold expresses every construction in the corpus (including the
  resultative small clauses, via `attr`) at 0/0 (§2 calibration).

### 4.4 What the evidence at the 70 positions adds

The invariant's *authority* does not rest on the 70 (it would hold of an
empty set); but the audit shows the class is homogeneous and real, not
checker noise: every row is L4-faithful or POS-explainable (§3), none is a
boundary artifact, and the two repair-relevant sub-populations (43
adjective / 19 verb / 8 other) are separable on frozen-layer evidence
alone, gold unopened.

## 5. The honest caveat

The hard/soft boundary is **contract-relative**. The tolerance registry is
a published design decision, not a fact of nature; a skeptic who rejects
the contract's authority reduces "hard" to "the contract says so". Within
the project's designated authority — `validate.py`'s schema invariants and
`derive.py`'s derivation ([`PLAN.md`](PLAN.md) §4 item 1, [`STAGE5.md`](STAGE5.md)
§5) — every leg tested here holds. The classification is not used a priori:
its basis was made explicit, then checked, and it held at every
independently testable point.

## 6. Consequences for the clausal design pass (not yet opened)

- **Deletion is the wrong repair for most of the class.** 59/70 have a
  derivable alternative: register the cited position as a predicate, exactly
  as the derivation does (§4.1) — after which the citation resolves and the
  row stands. The derivation's promotion is *deprel*-driven, not
  head-driven, so this covers the 3 rows whose L4 head is another predicate
  (§3 reading 2) as well. This is discipline 3's "where a derivable alternative exists,
  deletion is wrong" ([`STAGE5.md`](STAGE5.md) §5) applied with the
  contract, gold unopened.
- **The 43-adjective sub-population has a second admissible alternative**:
  re-notate as `attr`, the canonical equivalent (§4.2) that makes no
  registration demand. Which of the two alternatives (register the clause,
  or downgrade the notation) a rule should choose is the design pass's
  actual question, and the split is decidable from L2/L4 alone.
- **The 11 rows whose L4 deprel is not clausal** (`obj` 5, `conj` 3,
  `nsubj` 3) **need individual reading** — L4 itself asserts a different
  relation there, so no registration or re-notational alternative is
  derivable without deciding against the frozen tree (they are 3 adjective /
  5 verb / 3 other by L2 POS); and within the clausal-deprel 59, the **5**
  rows citing a non-verb, non-adjective token (the other 3 of §3's 8 sit in
  the 11 above) are where L2 refuses the clause L4 asserts, so their
  alternatives differ row by row.
- The pass must also settle how a registration-based repair interacts with
  the soft counts (registering a predicate adds the cited token's own frame
  to the diff surface) — measured in memory before any write, per the
  process note in [`PLAN.md`](PLAN.md)'s Handoff.

## 7. Method notes

- The audit was a scratch script (run from `/tmp`, not committed); every
  number in §3 is reproducible from `recon.check.check_canto` +
  `morph.load_morph` / `dep.load_dep` joins, position by position. The
  gold calibration in §2 is the standing `check.py` CLI pointed at
  `--root skel`.
- **Re-verified 2026-08-30, same tree, independent script.** Every §3
  figure was re-derived from scratch (recon TSVs + L1/L2/L4 only, gold
  unopened), the run numbers were re-measured (916 passed; 70 hard / 4,988
  soft; `repair-check` clean; gold `--root skel` 0/0), and §4.1's inferno 10
  demonstration was re-executed (unit `[13, 14, 15]`; derived rows include
  `fanno xcomp → (15,6)` and `morta '' → (0,0)`; 0 hard). Four figures did
  not survive and are corrected above: the dep-children count (38 → **40**),
  the "of that very predicate" claim in §3 reading 2 (59 → **56**, the 3
  exceptions now listed), §6's non-verb/non-adjective sub-count inside the
  clausal 59 (8 → **5**), and §2's contract citation, which pointed at the
  README's *soft* clause. Nothing in §4's argument depended on them.
- **Disclosure**: while diagnosing a key-collision bug in the scratch
  script ((canticle, line) keys without the canto number, so each canto
  overwrote the last), one debug print displayed gold's rows for inferno
  10:15 (`base_dir=None` loads gold). The audit itself — the §3 table and
  every statistic — was produced before and after that print with gold
  unopened, no rule was designed from it, and the same S5.3-style
  transparency ([`STAGE5.md`](STAGE5.md) §5's carry-over caveat) is applied
  here: the next session's design pass should still open gold-closed, and
  this record should not be read as having earned the convergence claim
  on its behalf.
