# skel — Notes toward a portable Layer-5 checker

**Status: notes, not a plan in flight.** Nothing here is scheduled, and none of it should be
started before the condition in *Sequencing* below is met. `PLAN.md` remains the record of the
work and the place routes are opened; this file exists so that the portability question stops
being re-derived from scratch, and so a future cleanup does not tidy the wrong thing.

Written 2026-08-18, against `dante_corpus/skel.py` at 4484 lines.

---

## Why the file grew

`dante_corpus/skel.py` carries rules A through EG — 84 rule letters — added one read batch at a
time over 21 batches covering all 100 cantos. That growth was the method working, not the method
failing: each rule was censused corpus-wide before it was written, measured by violation diff on
its own, pinned by a mutation-checked test, and written up with its evidence line. Several
candidates were measured and rejected, and those are recorded too. The residue went from 17438 at
the first full-corpus measurement to 224.

What the method did *not* produce is any way to ask a question about the rule set **as a set**:
which rules are still load-bearing, which have been subsumed by later ones, what the ordering
between them actually is, and which of them are about Italian rather than about Universal
Dependencies. Those are the questions a port has to answer, and none of them can be answered from
the source as it stands.

## Sequencing — soft 0 is a precondition, not a milestone

**Do not restructure while the soft count is above 0.** The checker's own output is the
measurement instrument for every change made to it; the standing discipline is *measure a checker
rule by violation diff, never by the total* (`PLAN.md`, Standing Disciplines). A refactor landed
while the count is still moving cannot be shown to have moved nothing.

The inverse is the useful part: **once `--check` reports 0 hard / 0 soft over all 100 cantos, that
0 becomes a regression gate.** Any restructuring — merging rules, reordering them, extracting a
language pack, changing a signature — is then verifiable by re-running the same check and the same
`pytest` suite. That is a far stronger safety net than the project has had at any point so far,
and it is why the right move is to finish the residue first rather than to stop and tidy.

## What was measured (2026-08-18)

| | |
|---|---:|
| `dante_corpus/skel.py` total lines | 4484 |
| — code | 3171 |
| — comment | 865 |
| — blank | 448 |
| module-level functions | 135 |
| distinct rule letters referenced in comments | 84 |
| module-level constants | ~20 |
| **of those, language-specific** | **7** |

The seven:

```
_PREP_LEMMA_NORM            Italian preposition lemmas, article contractions, apocopes
_REL_PRONOUN_WORDS          relative-pronoun word forms, for the Layer-3 NP-head check
_RELATIVE_PRONOUNS          relative-pronoun word forms, for rules CE / DC / DK
_RELATIVIZERS               every word that relativizes a clause (rule DP's negative gate)
_COMPARATIVE_PARTICLES      comparison markers in a Layer-4 `case` slot (rules AK / DM)
_COMPARATIVE_LEMMAS         comparison markers by Layer-2 lemma (rule AR family)
_LOCATIVE_RELATIVE_LEMMAS   relative locatives by lemma (rule DY)
```

Everything else is UD deprel vocabulary (`_SUBJ_DEPRELS`, `_AUX_DEPRELS`, `_ELIDED_COPULA_DEPRELS`,
`_NOMINAL_SLOT_DEPRELS`, …) or this project's own frozen role vocabulary (`_ROLE_RANK`,
`_ROLE_CANON`, `_COMPLEMENT_ROLES`, `_DIRECT_ROLE_MAP`) — neither of which is about Italian.

**The three relative-pronoun sets are not duplicates, and merging them would be a bug.** They are
three different notions that happen to overlap in surface form: the word forms the NP-head check
accepts in an argument slot, the word forms rules CE/DC/DK match, and the deliberately *wider* set
rule DP uses as a **negative** gate (a clause carrying any of them has a relativizer of its own).
`_RELATIVIZERS` is documented in the source as intentionally wider than `_RELATIVE_PRONOUNS`. The
same holds for `_COMPARATIVE_PARTICLES` (by word form, in a `case` slot) versus
`_COMPARATIVE_LEMMAS` (by Layer-2 lemma). What is wrong with them is **naming, and the fact that
they are scattered** — not that there are too many.

So the headline for a port: **the Italian surface of a 4484-line checker is seven constants.** The
bulk of the file is about UD's conventions and about this corpus's five-layer stack, and both of
those travel.

## The three real couplings

### 1. Rule identity lives in comments

A rule is a named predicate function plus a `# rule XX:` comment at its call site in an
`if … continue` chain. Nothing in the program knows a rule's letter, its census, or its current
population. Consequences:

- **No rule can be re-measured without editing the source.** The censuses in `CORRECTIONS.md` are
  prose, taken at the base current when each rule was written — bases from 1452 down to 224.
- **Dead rules are invisible.** Over 84 letters and a base that fell by two orders of magnitude,
  some rules are certainly now subsumed by later ones. There is no way to find them.
- **A port cannot be prioritized.** "Which 20 rules carry 90% of the acceptances" is unanswerable.

### 2. Rule order is implicit and untested

Ordering has been the finding of several consecutive read batches (rules AQ′, DG, DS, DT, BO, BZ,
CZ) — "which check runs first" is a recurring source of real defects. Yet the order is nothing but
the line order of the `if … continue` chains in `_classify_divergence`, with no name, no test that
pins it, and no way to detect that a newly inserted rule shadowed an older one. This is the single
most fragile thing to carry to another corpus.

### 3. Rules read the layer stack directly

`validate_unit` already has a clean seam — it takes `morph_rows`, `np_rows`, `dep_rows`,
`case_rows` as optional layers, and degrades when one is absent. Below it, though, individual rule
functions take derived indices positionally (`dep_index_by_pos`, `morph_pos_by_position`,
`case_children`, `case_by_position`, `children_by_pos`, `marker_lemmas`, …) and read tag text and
annex slot vocabulary inline — e.g. `_fused_clitic_dual_role` tests `tag.count("pronoun") >= 2` on
Layer-2 tag text and splits the `case` annex's slot string. Those are cross-linguistic *categories*
wearing this project's *encoding*. A port needs the categories, not the encoding.

## Proposed sequence, after 0

1. **Rule registry + one-shot census of every rule.** Move rule letters from comments into data,
   and measure each rule by the standing method — disable it, re-run `--check` over 100 cantos,
   record what comes back. Deliverable: one reproducible table of `rule → population → what it
   newly flags when removed`, replacing prose censuses taken at nine different bases.
   **This pays for itself before any port**: it names the dead rules, it makes the implicit
   ordering measurable (does removing A change B's contribution?), and it gives a port its
   priority order.
2. **Collect the seven language constants into one language pack,** named by what they mean rather
   than by which rule reads them, with the three relative-pronoun sets kept distinct and their
   differences documented at the point of definition rather than at the point of use.
3. **Give the layer stack an interface.** Promote the derived indices into a single object the
   rules receive, so "what a rule needs from the corpus" is declared rather than inferred from an
   argument list. Category vocabularies (pronoun-ness, annex slots) become part of that interface.

Steps 2 and 3 are cheap and low-risk once step 1 exists; without step 1 they are unverifiable
beyond "the tests still pass."

## What is explicitly *not* the problem

- **The comment density.** 865 comment lines carry the evidence line, census and rejected variants
  for 84 rules. That is the project's memory, and it is what made the rules auditable. Do not
  compress it in the name of tidiness.
- **The number of rules.** Each was censused and measured. A rule set that grew to 84 over a
  corpus of 100 cantos is not prima facie ad hoc; the missing thing is the ability to interrogate
  the set, not a smaller set.
- **The if/continue chains as a form.** They are readable and each arm is an isolated pure
  predicate. The defect is that the chain's *order* is unnamed, not that the chain exists.

## Open questions

- **What is the porting target?** "Another language" and "another corpus in the same language" are
  different problems: the first needs the language pack, the second needs the layer stack (a UD
  parse, a morphology layer, NP spans, a pronoun-case annex) to exist at all. The five-layer stack
  is the deeper assumption, and nothing here loosens it.
- **Does the authority model port?** `derive_unit` encodes decisions (pro-drop subjects, control
  subject propagation across `conj`, gapped-clause remnants) that are correct for a pro-drop,
  heavily-inverting poetic language. Which of those are UD-general and which are Italian is not
  known and is not answerable from the constants alone — it is a question for the census in step 1.
- **Should the checker and the derivation separate?** They are one module today. The acceptance
  rules compare an artifact with `derive_unit`'s reading; rule EG is the first check that reads the
  artifact against itself and needs no derivation at all. If that class grows, the two may want to
  be separable.
