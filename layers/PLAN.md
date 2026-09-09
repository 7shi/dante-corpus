# Layer Structure Review: Plan

### Handoff (2026-09-09) — resume here

> **Where this stands.** The directory holds six documents and, as of this
> session, a first piece of code — [`README.md`](README.md) (stable
> orientation), this plan, **[`REDESIGN.md`](REDESIGN.md)** (the design
> proposal, now §1–§10), [`reads/inf-1-1-9.md`](reads/inf-1-1-9.md) (the pilot
> read, updated in place this session with this session's follow-ups),
> **[`L1.md`](L1.md)** (L1's design, measurement, and implementation gathered
> in one place, superseding the L1-specific detail that used to sit inline in
> this handoff and in `REDESIGN.md` §2.1), and **[`L2.md`](L2.md)** (new this
> session — L2's design gathered the same way, with its first of three passes
> now implemented,
> superseding the L2-specific detail that used to sit inline in this handoff
> and in `REDESIGN.md` §2.1) — plus **[`gen2/`](gen2/)** (see *L1 implemented*
> and *L2 step 1 implemented*, below), the code itself.
> §4's five items remain unstarted **as written**; the work took the shape
> described below instead, and §4 is deliberately not rewritten yet — the new
> direction is still provisional pending an implementation trial (see
> *Rollout*, below).
>
> **Premises (operator, 2026-09-07 and 2026-09-09), recorded at the head of
> `REDESIGN.md`:** (1) preserving frozen artifacts is not a constraint —
> regenerating a layer is accepted cost, terminal renumbering is on the table;
> (2) stop at phrases — no complete tree rooted at the sentence (`REDESIGN.md`
> §3 argues it, §4.1 prices it); (3) generation 2 must not depend on
> generation 1 at rebuild time — old Layers 1–5 are bootstrap-only, never a
> named input a generation-2 layer's *definition* reads.
>
> **Method: each layer examined on its own against concrete *Inferno* 1
> positions, every observation measured corpus-wide before being written
> down.** All five old layers plus `case/` have now been reviewed this way;
> each review is its own numbered section in `REDESIGN.md`, source-cited, and
> summarized below. None of the findings are corrected in the frozen
> artifacts — this is review, not repair.
>
> ---
>
> **Layer 1 (done, earlier this session).** Two corrections to this plan's
> own prior diagnosis: (1) nothing is discarded at Layer 1 — the defect is
> *address*, not loss (full finding: [`L1.md`](L1.md)). (2) the sentence unit
> already exists (`dante_corpus/dep.py:200` `sentence_groups`, Layer 4 is
> built inside it) but isn't stored or exposed. Also sharpened §1.3's
> diagnosis: Layer 4 *is* a tree; the defect is that its nodes are tokens,
> none stands for a constituent (`REDESIGN.md` §1).
>
> **Old Layer 2 review (`REDESIGN.md` §6).** Entry point *Inf* 1:3
> `smarrita`. Past participles are encoded three incompatible ways
> (`pos=verb`+`mood=participle` 724 / standalone `pos=participle` 25 /
> `pos=adjective` 573+, the last splitting its own lemma between the
> adjective form and the verb infinitive for 104 wordforms, `smarrito` itself
> 4/4). The `pos` column holds 39 values, not a closed set (subtype leakage —
> `relative pronoun`/`pronoun`, `proper noun`/`noun` — plus spacing
> duplicates and singletons). Checked `case/`'s sparseness against this and
> found it's **not** a `case/` coverage gap — `case/` is complete and closed
> (13,157 rows, exact match) — but a pass-through of Layer 2's `pos` column
> read verbatim (`case/case.py:11`): a `che` mistagged `conjunction` (finding
> B's 225 positions, `reads/inf-1-1-9.md`) never reaches `case/`'s build step
> at all. The working assumption that "later layers don't lean heavily on
> `pos`" does not hold for `case/` specifically — recorded as a correction to
> avoid deprioritizing a `pos`-vocabulary fix without checking the consumer.
>
> **Old Layer 3 review (`REDESIGN.md` §2.2, inline).** `np/`'s
> fused-enclitic-pronoun mechanism (`clitic_mentions()`, the `"+lemma"`
> sentinel span, e.g. *Inf* 1:59 `venendomi` → `np/inferno/01.tsv:59` `+mi`)
> compensates for old Layer 1 having no position for a bound pronoun. §2.1's
> L2 split table covers exactly this shape (`verb+pronoun`, 488/372
> wordforms), so under the rebuilt stack the pronoun becomes an ordinary L2
> entry and the whole synthetic-mention apparatus has nothing left to
> compensate for. Separately, corrected an overstatement made mid-session:
> rebuilt NP is not "narrower" than old Layer 3 — finding H's own example
> already folds a relative clause into one NP span (*Inf* 1:9) — the
> participle-object question is a second instance of finding H's real defect
> (no explicit hierarchy rule), folded into §4.2's bound rather than treated
> as a separate axis.
>
> **Old Layer 4 review (`REDESIGN.md` §7).** Entry point *Inf* 1:2
> `mi ritrovai` (`mi` tagged `expl`, discarded as a non-argument, 1,466
> occurrences corpus-wide) — this doubled as the falsification test
> `REDESIGN.md` had left open for its own grammatical-word hypothesis.
> **96 of 170 verb lemmas (56.5%) underlying `verb+pronoun`'s 488 fused
> tokens also occur as a separate `expl` construction with the same
> reflexive clitic** (`andare+si`, `fare+si`, `muovere+si`, …) — the
> fused/separate split is spelling, not grammar, so the hypothesis survives.
> But the two treatments are not equally good: composite POS at least records
> the pronoun, `expl` discards it outright. Once L2 splits every fused case,
> `vagliami` and `mi ritrovai` become structurally identical, so whatever
> generation 2's dependency layer turns out to be has no structural reason
> left to treat them differently — recorded as a constraint on that
> not-yet-designed layer, not a decision about it (only L1/L2 are concretely
> proposed; "L4" is a placeholder label, not a designed layer).
>
> **`case/` review (`REDESIGN.md` §8).** Entry point *Inf* 1:22 `quei`
> ("*E come **quei** che con lena affannata, … si volge*"): `case/`
> independently reads it `nominative`; `dep/` attaches it `obl` to `volse`
> two lines down — one of 25 corpus-wide "impossible pairings" (`--stats`),
> all the same shape: a nominative-form pronoun heads a relative clause and
> the whole pronoun-plus-clause unit fills an oblique/comparative slot up the
> tree (also *Par* 1:93 `tu`, plus a dozen `colui`/`quel`/`quella`/`questo`/
> `quello` instances). Neither layer is wrong — this is finding H's
> missing-hierarchy defect surfacing a third time, visible only because
> `case/` was generated blind and independently. `case/` needs no fix; where
> the rebuilt stack writes this fact is folded into §4.2.
>
> **Old Layer 5 / `skel/` gold review (`REDESIGN.md` §9, gold treated as
> benchmark per premise 1, never as authority).** Confirms the two findings
> above reach `derive_unit` **unrepaired, by design**: `mi` in
> *Inf* 1:2 produces no skeleton row at all — `derive.py` never references
> `"expl"` as a deprel. *Inf* 1:26's `obl:come=(22,3)` (citing `quei`) is
> derived purely from `dep`'s `case`+`obl` chain — `derive_unit`'s own
> docstring (`derive.py:86-89`) states `case_rows_by_line` is read "at
> exactly one place" (rule CZ), not this one. Neither is a Layer-5 defect (a
> checker inheriting Layers 2/4's decisions is its job); the consequence runs
> upward — whatever a rebuilt dependency layer decides about `expl` or the
> relative-clause case will pass through unrepaired unless caught at
> generation time or by a cross-layer check (§4.1).
>
> **`reads/inf-1-1-9.md` updated in place** with this session's follow-ups,
> noted at each finding rather than rewritten: B corrected (the `case/`
> mechanism above), C extended (the three-way participle split), F resolved
> (the hypothesis survives, plus the Layer-5 confirmation), H upgraded from
> "least confidence" to a three-times-confirmed load-bearing pattern (line 9's
> own relative clause, the participle-object question, the `case`/`dep`
> pairings). The Axes table gained a follow-up note: F was axis (iii)
> *resolved*, not open; H reads closer to axis (iii) than to axis (i) now.
> "What this read does not settle" updated accordingly — G's count and the
> *Inf* 4:5 read are still untouched.
>
> ---
>
> **L1/L2 design, decided; only L1 implemented (`REDESIGN.md` §2.1–§2.2,
> §5).** Premise 3 as above. **L1** = `tokenize()`'s full output, punctuation
> included, own numbering — design, measurement, and implementation:
> [`L1.md`](L1.md). **L2** = grammatical words as `(l1_index, text)` pairs,
> split → POS-classify → normalize, only splits and never merges (the `fixed`
> many:1 direction stays a relation one layer up, over L2 entries) — full
> design, cost figures, and rollout plan: [`L2.md`](L2.md), not repeated
> here. **Build order**: L4 (dependency) precedes L3 (phrases) — L3 must
> project from generation 2's own L4, never from old Layer 4.
>
> **L1 implemented (this session, operator instruction: "gen2/ にL1を実装して
> ください").** [`gen2/l1.py`](gen2/l1.py) implements §2.1's L1 in full and is
> verified against it; design, implementation, and verification detail all
> live in [`L1.md`](L1.md) now, not here. Tests:
> [`tests/test_gen2_l1.py`](tests/test_gen2_l1.py) (13 tests, `uv run pytest
> layers/tests`) — parallel to `harness/tests`, not part of the root suite
> (`pyproject.toml` `testpaths = ["tests"]`) until gen2 replaces the old
> stack, per operator instruction: "コードをdante_corpusと統合する際に、テス
> トもルートの tests/ と統合します."
>
> **This is a start, not yet a stack — L1, plus L2's first of three passes,
> tried over nine lines.** See *L2 step 1 implemented* and *The live pass ran*,
> below; steps 2 (POS) and 3 (normalize) are
> still exactly as designed and unstarted. Open review items remain (G's real count net of
> nested coordination, the *Inf* 4:5 all-layer read `PLAN.md` §4 item 4 asks
> for, the quotes hierarchy, §4.1's cross-layer checker design, §4.3's
> VP/Layer-5 relationship, or the external consumer survey `REDESIGN.md` §5
> flags as the one genuinely unknown cost figure).
>
> **Still deferred, unrevisited against premise 3: the bootstrap safe/
> contaminated split.** Which frozen layers are safe to show the model even
> as a one-time warm start (tentatively tokens, lemma decomposition, Layer-4
> bracketing, `sentence_groups`) and which are contaminated positions it must
> not anchor to (`cop`/`attr` 953:357, the locution `obl`:`advmod`:`nmod`:`conj`
> 217:68:30:13, Layer-3 granularity, participle POS, `che` POS, `expl`) —
> including whether Layer-4 bracketing can be "safe" when the `advmod`/`obl`
> choice moves the brackets themselves. Premise 3 settles the general shape;
> this specific split does not yet reflect the layer reviews above.
>
> **A caveat that still stands.** Every measurement in `reads/` and in
> `REDESIGN.md` came from ad hoc scripts run in a scratchpad and **not kept**.
> All are re-derivable from the frozen artifacts in minutes; none is
> reproducible by re-running a committed artifact. The cross-layer checker of
> §4.1 is where that gets fixed.
>
> **The `L2.md` extraction, committed (`2471807`).** Pulled L2's design —
> split table, the `fixed`/merge boundary, the split → POS → normalize
> pipeline, cost figures, execution mechanism, rollout plan — out of this
> handoff and `REDESIGN.md` §2.1 into [`L2.md`](L2.md), mirroring the
> earlier L1.md extraction; both documents above already reflect the dedupe.
> No new finding.
>
> **L2 step 1 implemented (operator instruction: 「まず単語の分解だけ実装して
> ください」).** [`gen2/l2.py`](gen2/l2.py) is the **split pass only** — no
> POS, no apocope/elision restoration; the three-step ordering `L2.md`
> designs is untouched and unprejudged. One bounded step per **chunk of
> lines** (`--chunk`, default 3 — old Layer 2's own granularity,
> `morph/morph.py --chunk 3`), **answers carrying only the tokens that split**,
> keyed by the word and never by an index, no transcript across a chunk or a
> retry, the gate in the runtime and refusal as the identity, and a
> **line-by-line fallback** when a group never passes (`morph.py`'s own
> degradation). Splits are recorded per occurrence, `(line, l1_index)`, so a
> wordform reading two ways in one passage keeps both. The prompt is a file
> ([`gen2/skills/l2-split/`](gen2/skills/l2-split/)) loaded through
> `dante_corpus.harness.skills`; the model is reached through
> `dante_corpus.harness.llm`. The CLI holds
> [`../ARCHITECTURE.md`](../ARCHITECTURE.md) §0's checklist — llm7shi adapter,
> a status bar walking the canto's Dante lines on a stream shared with
> llm7shi, streaming JSONL with summed (never spanned) timings, a report class
> with both faces — with **one stated override: §3's `<tool_call>` XML, since
> the fixed-context mode has no tools.** Full implementation and verification
> detail live in [`L2.md`](L2.md), not here.
> Tests: [`tests/test_gen2_l2.py`](tests/test_gen2_l2.py), 66 (79 with L1's,
> `uv run pytest layers/tests`).
>
> **Two design points in `L2.md` were settled against it on the way, both
> recorded there in place.** (1) It said both "old Layer 2's row is bootstrap
> precedent in $O$" and "build with no view of old Layer 2, then diff" — the
> second is adopted (operator, 2026-09-09), so old Layer 2 enters only through
> the offline `--check` and agreement with it is evidence rather than an echo.
> (2) Its *Execution mechanism* extended "no batching" from the three jobs to
> the wordforms, one request each; **that is corrected** (operator,
> 2026-09-09) — a wordform is too small a unit to spend a request on and the
> pass hits request-rate limits before it hits anything interesting (*Inf*
> 1:1-9 alone: 56 wordforms against 3 chunks; corpus-wide 442). The argument
> against batching does not reach this case: a chunk is still *one job* over
> more material, not three jobs merged, and there is no multi-key merge —
> which is the failure mode `harness/stages/09.md` §2 actually measures. Two
> things improved rather than degraded: keys resolve exactly against the L1
> tokens the request lists — old Layer 2 needed `morph.split_table`'s tolerant
> substring matching not for want of a token layer (`tokenizer.tokenize()`
> predates both, and `morph.validate_line` checks against it) but because its
> prompt asked the model to tokenize as well as analyse; and a wordform
> recurring across chunks is now a free consistency check, each occurrence
> keeping its own reading and a disagreement recorded as a conflict.
>
> **A third correction, from the first real model output (operator,
> 2026-09-09).** The contract had asked for one row per token; a real answer
> for *Inf* 1:7-9 came back as 27 rows of which one (`del:di+il`) said
> anything. **The answer now carries differences only** — tokens with no row
> are single words — and a key that names two places in the passage is refused
> until the model prefixes it with the preceding tokens. That also made splits
> per-occurrence rather than wordform-keyed, which is what lets `nel` read
> `in+il` in one line and `ne+lo` in another. **What it gives up is stated in
> `L2.md`:** one-row-per-token proved the model had judged every token, and an
> empty block no longer can; the after-the-fact detector is `--check`.
>
> **The live pass ran, and it is clean** (operator, 2026-09-09;
> `google:gemma-4-31b-it`). 3 requests, 0 refusals, 0 api retries, 47.3 s; the
> model listed **exactly four rows** across the three answers — `Nel`/`del`
> (1:1), `nel` (6:2), `del` (8:4) — and nothing else; 74 L1 tokens → 78 L2
> entries; `--check` **56 agrees, 0 differs**. Hand-inspected, the silences are
> as right as the rows: every elision (`ch'`, `i'`, `v'`, `Tant'`, `l'`) and
> every apocope (`cammin`, `ben`, `trattar`, `pensier`, `dir`, `qual`) passed
> through untouched, and `de` at 9:1 — the passage's nearest trap — was
> correctly left whole. Full figures and the inspection: [`L2.md`](L2.md),
> *The live pass over Inf 1:1-9*. So step 1 is implemented **and tried**, at
> the rollout plan's first rung.
>
> ---
>
> ### Resume here
>
> **Inferno 1 in full, run (2026-09-09, operator report, commit `b3828c7`).**
> 43 chunks asked (3 already held from 1:1-9), 0 refusals, 0 fallback, 1 api
> retry, ~14.8 min. The `--check` figures reported right after the run (491
> agrees, 8 differs, 12 ours-ambiguous, 0 precedent-ambiguous) **are now
> superseded by the checker rework below** — the wordform data didn't change,
> only how it's read.
>
> **The checker was reworked, three times over, same session (operator,
> 2026-09-09, commit `94796f1`).** Trigger: the 12 `ours-ambiguous` rows were
> uninterpretable — no way to tell *which* occurrence of `di`/`a`/`e`/… was
> supposedly ambiguous, and hand-inspection showed all 12 were a checker
> artifact (wordform-level pooling let `A`/`a` case variants count as two
> readings). Full history of the three corrections, in order, with what each
> one broke and fixed: [`L2.md`](L2.md), the `check_against_precedent` bullet
> and *The live pass over the rest of Inf 1*. The end state:
>
> - **`render_check_lines`** (new): a per-line view, plain `" ".join()`
>   reconstruction, printing only lines with a real per-position mismatch —
>   `word(parts)` for this artifact's own split, `[...]` for old Layer 2's
>   reading at that *exact same position* when it disagrees. No case-folding
>   (a case difference is a difference), no cross-occurrence aggregation, and
>   no special-casing of "the first occurrence" — every position is checked
>   the same way.
> - **`check_against_precedent`'s verdict** is now three independent checks in
>   order: **`l2-ambiguous`** (this artifact's own readings for a wordform are
>   genuinely distinct, case-folded, independent of old Layer 2 — checked
>   first so a wordform correctly read two different correct ways is never
>   swallowed into `agrees`), **`layer2-ambiguous`** (the symmetric case: old
>   Layer 2's own readings for the wordform disagree with themselves, within
>   the range this run actually compared), then **`differs`** (neither side
>   ambiguous, but `_positionally_mismatched_wordforms` finds a real
>   disagreement). `precedent-ambiguous` is gone — old Layer 2 disagreeing
>   with itself *outside* what this run compared is not this checker's
>   business.
> - **The report's three sections are never mixed** (operator: "differsと
>   ambiguousは別々に表示する"): `[differs]` is a `wordform`/`L2`/`old Layer 2`
>   table (one reading each side, by construction); `[L2 ambiguous]` and
>   `[Layer 2 ambiguous]` are `wordform: reading, reading, …` lists, each
>   header omitted when empty. Wordform-level aggregation now shows up only
>   where it's meaningful — the two ambiguous sections — never for `differs`.
> - The table column and verdict name **`ours`/`ours-ambiguous` are renamed
>   `L2`/`l2-ambiguous`** throughout, matching how this artifact is named
>   everywhere else in this document.
>
> **Re-run against the corrected checker, Inferno 1 reads: 503 agrees, 8
> differs, 0 l2-ambiguous, 0 layer2-ambiguous** — same 8 real `differs` as
> before, the 12 case-fold rows gone. Of those 8: 6 (`aiutami`, `dipartilla`,
> `Rispuosemi`, `trarrotti`, `vagliami`, `venendomi`) are the designed
> surface/lemma gap (step 3 not run yet, not a finding). The remaining 2 are
> genuine, decided by argument from corpus-wide precedent (never gold), full
> text in [`L2.md`](L2.md):
>
> - **`pel`** (*Inf* 1:33) — **L2 is wrong.** Oversplit `per+il`; corpus-wide
>   `pel` is the noun *pelo* (fur) in all 7 occurrences, never a contraction.
>   `layers/l2/inferno/01.tsv` is left as the model produced it — not
>   hand-repaired; whatever mechanism should catch this (a step-1 prompt fix,
>   a corpus-wide consistency pass, or accepted noise for step 3) is still
>   undesigned.
> - **`'ncontro`** (*Inf* 1:59) — **old Layer 2 is wrong.** L2 leaves it
>   whole; old Layer 2 splits it here but leaves the same lexical item unsplit
>   9 of 13 times corpus-wide. **The mechanical `layer2-ambiguous` check does
>   not catch this, correctly**: within *this canto*, `'ncontro` occurs once,
>   so there's nothing to pool against — the inconsistency is only visible
>   corpus-wide, across four spellings of one word, outside a per-canto,
>   exact-wordform checker's reach.
>
> `uv run pytest layers/tests` → 79 passed throughout all three corrections.
>
> **`layers/l2/Makefile` added (2026-09-09, commit `94796f1`).** `help`
> (default target), `all` (generate via `layers.gen2.l2`, `MODEL` from
> `../../model.mk`), `check` (`--check`), `clean` (deletes the run log, never
> the artifact) — `CANTICLE`/`CANTO` fixed to `inferno`/`1` for now (the only
> canto generated), overridable once more are.
>
> ```
> uv run python -m layers.gen2.l2 inferno -c 1 \
>     -m google:gemma-4-31b-it
> uv run python -m layers.gen2.l2 inferno -c 1 --check
> # or, equivalently, from layers/l2/:
> make all
> make check
> ```
>
> **The CLI takes the corpus's own driver shape** (operator, 2026-09-09,
> citing `skel/skel.py`): canticles positional, `-c` a canto *spec* (`1`,
> `12-`, `1,3-5,11-`) through `api.select_cantos`/`check_canto_spec`, `-m` for
> the model, `--lines` optional (whole canto by default, one-canto only). A
> multi-canto run writes one artifact per canto over one model connection,
> each with its own log at `NN.log` beside `NN.tsv` (`--no-log` turns it off).
> **The run resumes**: the committed artifact is read back and every chunk it
> already answers is skipped before any request, so widening a canto's range
> only costs the unanswered chunks; `--force` asks again from the first line.
> **The log is append-only**: nothing but an explicit delete shortens it,
> `--force` included, so a failed attempt's record survives its retry.
>
> **Session close (2026-09-09).** Working tree clean; two commits this
> session, `b3828c7` (the full Inferno 1 run) and `94796f1` (the checker
> rework + Makefile). Nothing was corrected in the *artifact* — only in how
> it's read back.
>
> **What to look for, widening past Inferno 1.** The checker rework means the
> per-line `[...]` view and the three-way split are now the tool for this,
> not the flat wordform table:
>
> 1. **`pel`'s failure mode is still uncaught.** Nothing yet stops another
>    over-split trap word (a `del`/`nel`-shaped token that isn't a
>    contraction) from reaching an artifact unflagged. Decide the mechanism
>    before or while widening.
> 2. **`layer2-ambiguous` needs a canto with real recurrence to prove itself
>    live** — *Inf* 1 never exercises it (0 rows), same as `l2-ambiguous`
>    (0 rows; `test_a_wordform_this_artifact_splits_two_ways_is_reported_not_hidden`
>    is the only place the design is currently exercised). A wider run is
>    where both either fire for real or stay unexercised in practice too.
> 3. **Clitic compounds (`verb+pronoun`) are confirmed working** at the
>    surface level — all 6 in this canto split correctly; the surface/lemma
>    gap is step 3's to close, not a splitting defect.
>
> A `differs` row is evidence for one of two outcomes (L2-is-wrong /
> layer2-is-wrong) — decide which by argument from the text and **record the
> argument in `L2.md`**, per premise 3. Record numbers, never log filenames
> (`ARCHITECTURE.md` §5).
>
> **If a chunk misbehaves.** Refused chunks fall back to line-by-line
> automatically and the summary counts them (`fallback_chunks`); a line no
> attempt ever answered lands on `unresolved_lines` and fails the gate. A
> systematically bad answer shape is a **prompt** fix in
> `gen2/skills/l2-split/`, not a parser fix — the gate's refusal messages are
> written to be handed back to the model, so read what it was told before
> changing code. `--chunk 1` isolates a bad line; `--max-iterations` raises the
> per-chunk cap.
>
> **Alternatives.** Steps 2 (POS) and 3 (normalize) of L2 are designed and
> unstarted; the open review items several paragraphs up (G's real count, the
> *Inf* 4:5 all-layer read, the quotes hierarchy, §4.1's cross-layer checker,
> §4.3's VP/Layer-5 relationship, the external consumer survey) are all still
> untouched.
>
> ---
>
> ### Handoff (2026-09-09, continued) — resume here
>
> **`gen2/l2.py` gained `-l`/`-o` short flags and per-chunk artifact writes**
> (commit `b990378`). `-l`/`-o` shorten `--lines`/`--out`. The TSV now flushes
> after every chunk settles or is skipped, not only once at the end of the
> canto — closing a real gap between the interruption-resilience claim
> (resuming reads the artifact back) and what had actually reached disk if a
> run died mid-canto.
>
> **A three-run check answered the open question about `pel`, and found two
> more positions (commit `f5bfbb7`, full text and argument in
> [`L2.md`](L2.md), *Is a `differs` random or systematic?*).** One run cannot
> distinguish a stochastic slip from a repeatable mistake, so *Inf* 1 was
> generated twice more with the same model and prompt (`01-2.tsv`, `01-3.tsv`,
> using the new `-o`), and the three files diffed against each other rather
> than against old Layer 2:
>
> - **`pel`** (1:33) — all three runs agree on the same wrong split
>   (`per+il`). Three-way agreement on a wrong answer is the signature of a
>   **systematic** error: nothing in one chunk of lines tells the model that
>   `pel` is `pelo` (fur) in all 7 corpus-wide occurrences. This closes the
>   question left open in the previous handoff — it is not a fluke, and no
>   amount of re-running would fix it by vote.
> - **`de'`** (1:17) — `01.tsv`/`01-2.tsv` split `di+i` (agreeing with old
>   Layer 2); `01-3.tsv` alone leaves it whole. Majority is right here.
> - **`dipartilla`** (1:111, verb half) — `01.tsv`/`01-3.tsv` both read
>   `diparta` (present subjunctive); `01-2.tsv` alone reads `dipartì`. Old
>   Layer 2 records **remote past** at this token
>   (`morph/inferno/01.tsv:808`), which is `dipartì` — **majority is wrong**
>   here, and the one-vote minority is correct.
>
> **The conclusion, load-bearing for how this proceeds: majority vote across
> repeated runs detects disagreement, it does not verify correctness.**
> Three-way agreement is not proof of correctness (`pel`), and a 2:1 split
> is not proof the majority is right (`dipartilla`) — every disagreement
> still has to be argued from precedent, same as any other `differs`.
>
> **A standing position was reversed this session: hand-editing the artifact
> is now adopted, not ruled out** (operator argument, recorded in `L2.md`
> right after the three-run section: steering a one-shot prompt toward the
> right answer and correcting the same answer by hand afterward put the
> identical human judgment into the corpus by two different routes, and the
> goal is a correct corpus, not one whose correctness was produced
> unassisted). **`l2/CORRECTIONS.md` is adopted**, matching the Cross-Layer
> Hygiene discipline `PLAN.md` §"Standing Disciplines" already states and the
> precedent on disk (`morph/`, `dep/`, `case/`, `np/` each have one).
>
> **Not yet done, and the concrete next step: `l2/CORRECTIONS.md` itself is
> still unwritten.** Its first three entries are already decided by the
> argument above and just need recording, in the same classify/verify/
> re-check form the other four files use:
>
> 1. **`pel`** (1:33) — systematic, not yet hand-corrected pending a decision
>    on which mechanism should have caught it (step-1 prompt fix, corpus-wide
>    consistency pass, or accepted noise for step 3) — record the finding
>    even before that decision is made.
> 2. **`de'`** (1:17) — hand-correct `layers/l2/inferno/01.tsv` to split
>    `di+i`, verified against `01-2.tsv` + old Layer 2's `preposition+article`.
> 3. **`dipartilla`** (1:111) — hand-correct `01.tsv`'s verb half from
>    `diparta` to `dipartì`, verified against `01-2.tsv`'s minority reading +
>    old Layer 2's `remote past` feature.
>
> After any hand correction to `01.tsv`, re-run `--check` per the standing
> methodology. `01-2.tsv`/`01-3.tsv` are diagnostic artifacts from this
> check, not a second and third canonical build — whether they stay on disk
> or are cleaned up once `l2/CORRECTIONS.md` is written is undecided, and
> should be settled explicitly rather than left to accumulate as more cantos
> get this treatment.
>
> ---
>
> ### Handoff (2026-09-09, step 0 tried) — resume here
>
> **A pass was added *before* the split and run over all of *Inf* 1; it did
> not do the job it was built for.** Full design, run, cost and conclusion:
> [`L2.md`](L2.md), *Step 0: restoring dropped letters before the split*. The
> short version:
>
> **Why it was built.** Old Layer 2 gets `pel` right because
> `morph/morph.py` never asks whether a token splits — it asks for a lemma
> *and* a POS in one row, so `di` + `preposition+article` is unwritable at
> that position and the wrong answer is blocked by a second, contentful
> column. Two ways to put that column back were identified: **step 2 revoking
> a step-1 split**, or asking the contentful question **first** — *what word
> is this?*, a choice of word form rather than a classification (operator: a
> model selects word forms statistically and is not reliably conscious of
> POS, so form-then-POS may be the more accurate order). The second was
> taken.
>
> **What it is.** [`gen2/restore.py`](gen2/restore.py) +
> [`gen2/skills/l2-restore/`](gen2/skills/l2-restore/), step 1's machinery
> throughout (chunk per request, keys not indexes, runtime gate, refusal as
> the identity, line-by-line fallback, resume, append-only log), artifact
> `layers/l2/<canticle>/NN-restore.tsv`. Scope is stated as an operation on
> letters and **never as "the standard form"** (operator: that phrasing
> invites lexical substitution, and `sanza`/`core`/`giuso` are this
> language's own words, not shortened ones). **The apostrophe is read as a
> marker of *where* the letters go**, not stripped (operator) — so the gate
> requires the token's letters to read straight through the answer *and* the
> answer to grow only at an end the token's own spelling opens.
> `l2.py -r` consumes it and **moves only the question**: positions are
> unchanged and an unsplit token still records its L1 surface, so an
> imperfect restoration cannot reach the split artifact. 42 tests (121 with
> the rest).
>
> **A discipline, recorded because it was broken first: a wordform under
> measurement must not appear in the prompt.** The first prompt used
> `pel` -> `pelo` as its worked apocope example and the pass duly "solved"
> `pel`; removing that one line, the same model left `pel` alone. Steering a
> one-shot to the answer and hand-correcting afterwards are the same act
> (operator), so an experiment whose prompt contains its own answer measures
> nothing. The prompt was then stripped of **every** example, scope-bounding
> ones included (operator: 「まず例は一切なしで実験です」). That is the version
> that ran.
>
> **The run (`google:gemma-4-31b-it`).** 49 chunks, gate PASS, 993 tokens,
> **136 restored**, 60 attempts / 12 refused. Working: every
> leading-apostrophe case correct (`'ncontro`→`incontro`, `'nvidia`→
> `invidia`, `'l`→`il`, …); the gate refused two real respellings
> (`avea`→`aveva`, `parea`→`pareva`); the per-occurrence design fired for the
> first time on real data (13 wordforms two ways, none an error — `l'` is
> `le` at 9:2, `la`/`lo` elsewhere); all six clitic compounds untouched, which
> is correct for this pass. **Not working: `pel` was not restored**, so step 1
> met the same token and split it `per+il` again.
>
> **`01-4.tsv` (the split over the restored tokens).** 46 chunks, gate PASS.
> `--check` is **identical to `01.tsv`'s** — 503 agrees, 8 differs, 0/0, the
> same eight wordforms — so **nothing broke**: the clitics all split, `de'`
> (restored to `dei`) still splits `di`+`i`, no new `differs`. Against the
> three earlier runs the whole canto differs in **one** place: 1:111
> `diparta` → `dipartì`, which is the correct reading (old Layer 2's *remote
> past*), making `01-4` the best of the four. **But `01-2` reached the
> identical output with no restoration at all**, so this run does not show the
> restoration caused it — the three-run lesson applies unchanged.
>
> **The cost, and it is not context.** 89 min against the split's 14.5 min,
> **6.2x** — and thought tokens are 177,071 against 28,581, the same 6.2x,
> while the restore request is the *shorter* prompt (1,662 input tokens per
> request against 2,033). Recognition of a closed pattern set is cheap;
> open generation over every token, with no example left to imitate, is not.
>
> **What it settles.** The pass **works as normalization, not as a guard for
> the split**: its output is real step-3 material, and moved to *after* the
> split it is the pass the `far`+`ne` shape needs anyway (a truncation hidden
> inside a fusion — `farsi` 8, `farne` 3, `farmi` 3, `dirne` 2, … — which no
> pre-split pass can see). **`pel` returns to the other candidate: step 2
> revoking a step-1 split** on a POS sequence that cannot be assigned in the
> line. That is the mechanism old Layer 2 actually had; a restoration pass is
> still one question about one token in isolation and does not carry the
> contradiction. Its cost is a backward edge step 2 → step 1, bounded if the
> revision runs once, step 1 is not re-run after it, and each revision is
> recorded as its own event.
>
> **Unchanged by this session, still the concrete next step:**
> `l2/CORRECTIONS.md` is **still unwritten**, and `01-4.tsv` adds a fourth
> diagnostic artifact to the `01-2`/`01-3` pile whose disposition is still
> undecided. Note `01-4` independently confirms `dipartì` at 1:111, so that
> entry's verification now rests on two runs plus old Layer 2 rather than
> one.
>
> **Provenance of `01-4.tsv`, checked rather than assumed** (operator asked;
> both checks pass). The run's `summary` record carries
> `restored_from = layers/l2/inferno/01-restore.tsv`, `restored_tokens = 136`
> (matching the restore artifact's own changed-row count) and
> `skipped_chunks = 0`, so all 46 chunks were asked with the restorations in
> hand and nothing was resumed from a pre-existing file. Independently, the
> model's answer keys are the **restored** spellings — 1:17 comes back as
> `dei -> di+i`, not `de'` — which is only possible if the restored token list
> is what the request carried, since keys must be copied verbatim from
> `<tokens>`. The artifact itself still records the L1 surface, as designed.
>
> **Which order — settled, and the reason is not the experiment.** Asked
> whether it matters which of the two passes runs first: for the split's
> *output*, measurably not — the whole canto differs in one position and that
> position was reached by `01-2` without any restoration. But the two
> positions are **not interchangeable in what they can reach**, and that is
> structural rather than measured:
>
> |  | a truncation masquerading as a fusion | a truncation hidden inside a fusion |
> |---|---|---|
> | **before** the split | reachable in principle (did not fire) | **invisible** — still one token |
> | **after** the split | **impossible** — the split is already wrong | reachable |
>
> Cost is the same in either position (the same question over roughly the same
> number of tokens), and the post-split question is the better-posed one — it
> is asked of grammatical words, so a fused token never has to be recognised
> and left alone at all. Since the pre-split position's *only* unique job is
> the `pel` shape and it did not do it, **the pass goes after the split**, and
> there is no case for paying for both. Moving it is not done.
>
> **A cheap measurement that should come before any new mechanism.** The whole
> `pel` argument rests on one word (7 corpus-wide occurrences). **How many
> `del`/`nel`-shaped tokens are there corpus-wide that are not contractions?**
> That is answerable offline from the frozen layers in minutes, and it decides
> the question the step-2 design is for: if the class has a handful of members,
> `l2/CORRECTIONS.md` is cheaper than a mechanism; if it is large, step 2's
> revocation earns its backward edge. Do this before widening past *Inf* 1.
>
> **Session close (2026-09-09, step 0).** One commit, `c9291d4` (the restore
> pass, `-r`, both artifacts, `L2.md`'s new section, this handoff); working
> tree clean afterwards. `uv run pytest layers/tests` → 121 passed. Nothing was
> hand-corrected in any artifact this session.

---

### Handoff (2026-09-09, split and POS merged) — resume here

**The pass was rebuilt: the split and a coarse POS are now one question**
(operator: 「Layer 2のように、文法解析まで一気にやってしまう方が良さそうです。
ただしlemmatizeは抜いた方が良いでしょう」). Full design, the argument, the
mechanical diff and the contamination note: [`L2.md`](L2.md), *Split and POS
become one pass*. The short version:

**Why.** Once `pel` is written down as `per`+`il` the route back is closed —
every later pass meets two grammatical words, not the trap — so no post-split
mechanism can be the guard, and step 0 measured that the pre-split position
does not do it either. What is left is the position old Layer 2 held: the
contentful column answered **at the same position, in the same answer**. At
*Inf* 1:33 `che di pel macolato era coverta` the wrong split is unwritable once
tags are required, because it puts two prepositions and an article in a row and
leaves `macolato` with no noun. **Lemmas stay out** (operator): the POS column
alone carries the contradiction, while the lemma column brings the dictionary
judgment that splits `smarrito`'s rows 4/4 (`REDESIGN.md` §6).

**Restorations stay in, and that folds step 3 into the same answer** (operator:
「ben→bene 禁止する必要はないのでは？restoreを包含しているので」). Refusing
`ben` -> `bene` was over-wide: a restoration is not a lemma, and the boundary
was already mechanical — `is_restoration`, moved from `restore.py` into
`l2.py`, requires the token's own letters to read straight through the answer,
growing only where its own spelling says letters were dropped. `ben` -> `bene`
and `ch'` -> `che` pass; `sanza` -> `senza`, `smarrita` -> `smarrito`, `era` ->
`essere` are refused, so gender, number, tense and mood cannot move. Because
each *part* is written whole, this reaches `farne` -> `fare`+`ne` — the
truncation hidden inside a fusion that the previous handoff's table showed no
separate pass could reach — and **`gen2/restore.py` is left with no job**. It
stays on disk (measured work; `l2.py` now owns its criterion and it imports it
back), unused, its deletion undecided.

**What it is.** [`gen2/l2.py`](gen2/l2.py) replaces the split-only module;
[`gen2/skills/l2-words/`](gen2/skills/l2-words/) replaces `l2-split/`. The
answer is a Markdown table in one `<table>` block, **one row per token, matched
by position** — `| Line | Index | Token | Words | Part of Speech |`, each word written
whole — so the sparse contract's
blind spot closes (a missing row is refused, not read as "single word") and
keys disappear along with `locate_key`, which moves to `restore.py`, its only
remaining user. Tags are a **closed set of ten**; subtypes and features stay a
later stage, and a participle is `verb` by stated convention. The artifact
gains a `pos` column (`line, l1_index, l2_index, text, pos`), and `--check` now
reads all three decisions on their own grains: splits compared through
`readings_agree` (putting letters back is not a split disagreement), a
`[restored]` section of its own, and a `[pos differs]` section that compares
tags only where both sides split the token the same way, folding old Layer 2's
39-value vocabulary through `COARSE_POS` first. Everything else is unchanged: chunk of lines per request,
runtime gate, refusal as the identity, line-by-line fallback, resume,
append-only log, `-o`/`-l`, per-chunk artifact writes. Tests rewritten;
`uv run pytest layers/tests` → **131 passed**.

**The question hands over that table with its first two columns filled in**
(operator: 表だけだと transformer が文章のイメージを構築できない可能性がある).
The verse was always shown; the weakness was the flat token list under it,
which stripped the line boundaries out of exactly the context `pel` needs. Now
each row carries its line number, the row set is a fill-in rather than
something to rebuild (and the gate checks the `Line` column, so a moved row is
caught), and the prompt asks for the passage to be read as verse first.

**`restore.py` is superseded, not deleted.** Its `-r` wiring into `l2.py` went
with the step-0 position, and the post-split job the previous handoff reserved
for it is now answered per part in the same row. The module and its artifact
stay on disk, unused.

**Every previous artifact was deleted with this commit, and the disposition
question closes with them** (operator: 「これまでの01-*.tsvは削除して、01.tsvと
して仕切り直します」). `layers/l2/inferno/` is empty: `01.tsv`, `01-2`, `01-3`,
`01-4` and `01-restore.tsv` are gone, and so are their logs. They were all
four-column split-only files (plus the restore pass's own), which this reader
treats as holding nothing anyway; keeping them would only have invited a resume
into a shape with no `pos`. **What they measured survives in prose** — the
three-run check, step 0's run, the eight `differs` — in `L2.md` and in the
handoffs above, which is where `ARCHITECTURE.md` §5 says the numbers belong.
The next run therefore starts at line 1 and writes one canonical `01.tsv`.

**Not run, and this is the session's whole open question.** No live model call
has been made with the merged pass. Three things to read off the first run:

1. **`pel` at *Inf* 1:33** — `che di pel macolato era coverta`. The whole
   redesign is aimed at this position. If `--check` reports no `differs` there,
   the mechanism worked; if it still splits `per`+`il`, the guard is not the
   tag column and the argument in `L2.md` needs revisiting rather than
   re-running.
2. **The six clitic compounds** (`aiutami`, `dipartilla`, `Rispuosemi`,
   `trarrotti`, `vagliami`, `venendomi`) — under the split-only pass these were
   six of the eight `differs`, the designed surface/lemma gap. With the parts
   now written whole they should agree, or the gap should at least shrink to
   something the `[restored]` section explains.
3. **Cost.** The answer is dense (68 rows for nine lines against four) and
   carries the restored spellings step 0 spent 89 minutes on by itself, though
   here they ride in a request that was being sent anyway, beside a tag column
   that is recognition over a closed set. The split-only baseline is **14.8 min
   for the canto**; step 0's was 89.

**How to run it.** From the repo root, or `make all` / `make check` from
`layers/l2/` (`MODEL` comes from `../../model.mk`):

```
uv run python -m layers.gen2.l2 inferno -c 1 -l 1-9 -m google:gemma-4-31b-it
uv run python -m layers.gen2.l2 inferno -c 1    -m google:gemma-4-31b-it
uv run python -m layers.gen2.l2 inferno -c 1 --check
```

The nine-line range first is the rollout plan's own first rung and costs three
requests; it does **not** reach `pel` (line 33), so the full canto is what
answers question 1. A run resumes, so the second command only asks the chunks
the first did not — no `--force` needed, and `--force` is what to use if the
prompt changes under an existing artifact. `--chunk 1` isolates a bad line and
`--max-iterations` raises the per-chunk cap.

**What to report back:** the summary block the run prints (chunks / tokens /
terminals / tags / requests / seconds), and `--check`'s output — the per-line
`[...]` view, `[differs]`, `[restored]`, `[pos differs]` and the counts.
A systematically bad answer *shape* is a prompt fix in
[`gen2/skills/l2-words/`](gen2/skills/l2-words/), never a parser fix: the gate's
refusal messages are written to be handed back to the model, so read what it
was told before changing code. A `differs` row is evidence for one of two
outcomes (L2-is-wrong / layer2-is-wrong) — decide which by argument from the
text and record the argument in `L2.md`, per premise 3.

**The question and the answer now share one block name** (operator, 2026-09-09:
「コンテキストが `<tokens>` なのに回答が `<words>` なのは混乱の元では？」). They
were `<tokens>` out and `<words>` back, which contradicts this pass's own stated
principle — *the shape of the answer needs no describing, because it is the
shape of the question* — since two names claim two different things are being
carried when it is one table travelling both ways, and `<words>` doubles as the
name of a *column*. **Both ends are `<table>`**: `ask_message` sends it,
`_TABLE_BLOCK` reads it back, and the prompt says the answer *is* the block it
was handed, filled in. The cost is one new failure mode — a model quoting the
question's table in its prose trips the "exactly one block" refusal — so that
refusal message now names the case, in the same hand-it-back-to-the-model style
as the rest of the gate. `uv run pytest layers/tests` → **131 passed**.
The rationale is recorded in [`L2.md`](L2.md), *Split and POS become one pass*.

**A run started under the old prompt was stopped** (operator), leaving
`layers/l2/inferno/01.tsv` and its log on disk from the `<tokens>`/`<words>`
wording. The prompt has changed under it, so the next run wants **`--force`**
rather than a resume; nothing has been deleted or hand-edited here.

---

### Handoff (2026-09-10, the merged pass ran) — resume here

**It ran over all of *Inf* 1, and `pel` is right.** Full figures, the
classification of every `[pos differs]` position and the argument:
[`L2.md`](L2.md), *The first run of the merged pass, over all of Inf 1*. The
three questions the previous handoff left open are all answered:

1. **`pel` (1:33): the mechanism worked.** Not only unsplit — restored to
   `pelo` and tagged `noun`. Three split-only runs had agreed on `per`+`il`;
   under the merged question it is gone, with no prompt example naming the word.
2. **The clitic compounds: 8 `differs` → 4.** `aiutami`, `dipartilla` and
   `vagliami` now agree; the three that remain (`Rispuosemi`, `trarrotti`,
   `venendomi`) differ only as surface against old Layer 2's lemma, which is out
   of scope by design. The fourth is `'ncontro`, where old Layer 2 is wrong.
3. **Cost: 59.5 min** against the split-only 14.8 and step 0's 89 — and this one
   answer carries the split, the tags and the restorations together.

`--check`: 507 agrees, 4 differs, 0/0; **948 of 989 tag positions agree
(95.9%)**; 142 restorations. All ten tags fire, so the closed set needs no
pruning and its tally is **not** going into the prompt (feeding the distribution
back would only bias the next run).

**`l2/CORRECTIONS.md` is still unwritten and its three planned entries are now
moot**: `pel` 1:33, `de'` 1:17 (`di`+`i`) and `dipartilla` 1:111 (`dipartì`, the
remote past) are **all three correct in the artifact, unaided**. What the file
should hold instead is the restoration class the gate refused and the model then
worked around — `'l` → `il`, `cor` → `core`, `me'` → `meglio` — plus the three
apparent tag errors (`brame` 1:49, `via` 1:29, `tutte` 1:49), hand-corrected and
recorded rather than fixed by adding prompt examples (operator: プロンプトに入れ
ても手動で直してもあまり違いはなく、手動で直してCORRECTIONSに記録した方が有意義).

**Two corrections landed this session** (full text in [`L2.md`](L2.md),
*`Index`, and the readout that had to be regrouped*):

- **The table gained an `Index` column**, filled in by the question and copied
  back. Five of the run's six refusals name a `row N` that existed only inside
  the program; `Index` hands the number over so a repair is addressable. It is
  the row's own 1-based number, **not** the artifact's `l1_index` (0-based, and
  it counts the punctuation the table omits). It does not prevent omissions —
  this run had none, over 993 tokens — and it does not reach a swap of two
  identical tokens inside one line, which nothing currently catches.
- **`TWO READINGS` is kept and regrouped**: capitalisation folded out of the
  comparison (22 of 76 conflicts were nothing else — the same case-fold artifact
  the `--check` rework removed once already) and one line per **wordform with
  counts** instead of one per occurrence. The same data reads as **17 lines**.
  It stays because it is the pass's only intrinsic check, which is what §3.1
  asks for and premise 3 requires; over this canto it independently surfaced
  `via`, `tutte`, `poco` and `alto`.

`uv run pytest layers/tests` → **135 passed**.

**The artifact was regenerated under the new prompt** (`--force`, operator,
2026-09-10; full figures in [`L2.md`](L2.md), *The regeneration under `Index`,
and what two runs of one canto show*). 46 chunks, gate PASS, 66.6 min; `--check`
**507 agrees, 4 differs, 0/0**, **953 of 989 tags agree (96.4%)**, 143
restorations. `pel`, `de'` and `dipartilla` all reproduce. Refusals 6 → 4, all
four `is_restoration` again, and **not one refusal in either run was a row out
of place** — which is `Index`'s honest measure: it prevents no omission, because
none occurs; it makes the `row N` those refusals name visible to the model.
`[two readings]` came back **16 wordforms, no capitalisation-only rows**.

**The tag column wobbles between runs, and this is now the load-bearing
finding.** Over an identical prompt and model the `[pos differs]` set moved
41 → 36, nine positions leaving and four arriving; 32 are stable. `via` 1:29 was
wrong in run 1 and right in run 2, `poco` 1:7 the reverse. The three-run lesson
holds in the new column: repeated runs detect disagreement, they do not verify
correctness — only the stable 32 can carry an argument.

**The participle convention is being declined at the lexicalised cases.**
`disperate` (1:115) and `dolenti` (1:116) came back `adjective` this run and
`verb` last, against a prompt that states the convention flatly. That is the
`participle` question ceasing to be hypothetical: the choice is already being
made at these positions, inconsistently, at exactly the boundary that produced
old Layer 2's 573-row `adjective` bucket.

**Still open, unchanged.** Whether to add `participle` as an eleventh tag: ten
of the 41 `[pos differs]` positions are the `verb`-by-convention choice, and
they bury the three real tag errors. The argument against it is weaker than it
first looked — `REDESIGN.md` §6 measures old Layer 2's *inconsistency*, not the
category — but the live risk is that `participle` vs `adjective` becomes a third
judgment for lexicalised cases (`disperate`, `dolenti`), which is how old Layer
2's 573-row `adjective` bucket happened. If it is added it must be mechanical
(*if the form is a participle, `participle`*), and `COARSE_POS` has to move with
it or every participle position becomes a `differs` on the next `--check`. And
the corpus-wide `del`/`nel`-shaped measurement is still undone, though `pel`
reading correctly drops its stakes further.

---

**Unchanged and still the standing next steps:** `l2/CORRECTIONS.md` is still
unwritten — but its three decided entries were all verified against artifacts
that no longer exist, so re-derive them from this run rather than from the
deleted files (`pel` 1:33; `de'` 1:17 splits `di`+`i`; `dipartilla` 1:111 reads
`dipartì`, not `diparta`, per old Layer 2's *remote past*). And the cheap
corpus-wide measurement the previous handoff asked for — **how many
`del`/`nel`-shaped tokens are not contractions** — is still the thing to do
before any further mechanism, though its stakes drop if this run reads `pel`
correctly.

---

### Handoff (2026-09-10, corrections recorded, participle decided) — resume here

**`l2/CORRECTIONS.md` exists and holds eight hand corrections to
`layers/l2/inferno/01.tsv`** (commit `7f74680`), each verified against corpus-wide
precedent, in three groups: four tags contradicted by the word's own record (`poco` 1:7
`pronoun` → `adverb`, never a pronoun in 144 corpus occurrences; `brame` 1:49 → `noun`;
`tutte` 1:49 → `adjective`; `Molti` 1:100 → `adjective`), two restorations the gate
refused and the model then declined to make (`me'` 1:112 → `meglio`/`noun`, `imperador`
1:124 → `imperadore` — in both the gate was right and only the answer was missing), and
two participles corrected to this pass's own convention (`disperate` 1:115, `dolenti`
1:116). `--check` after: splits unmoved at 507/4/0/0, tags 953 → 956 of 989,
restorations 143 → 145.

**The file's scope is fixed at its head in a `[!NOTE]`, and it is not append-only.** It
records hand edits only — mechanism changes belong in `L2.md` and these handoffs and
reach the artifact by regeneration. And **a regeneration rewrites it** (operator): a
re-run does not reliably repeat the same mistakes at the same positions, so an entry the
new artifact gets right is describing nothing and is dropped, while an entry whose
problem survives is carried forward and re-verified. Deleted entries are not kept there
as history — the argument lives in `L2.md`, and git holds the old versions. A gated
re-apply script was considered and **declined** for the same reason.

**The eleventh tag is decided: `participle` is NOT added** (operator, 2026-09-10; full
argument in [`L2.md`](L2.md), *The eleventh tag, declined*). Old Layer 2's own numbers
settle it — participle-hood is recorded as `pos=verb` plus the **`tense`** column at
**722** rows against **31** that put it in `pos`, so an eleventh tag would build the
23:1 minority encoding into generation 2. It also crosses this pass's stated boundary
(tense is explicitly a later pass's), the tag column's designed job does not need the
distinction, and adding it re-opens the lexicalised participle-versus-adjective judgment
that produced §6's 573-row `adjective` bucket.

**Instead the convention was given its reason in the prompt**
([`gen2/skills/l2-words/SKILL.md`](gen2/skills/l2-words/SKILL.md)): a later pass can add
*participle* to a `verb` but cannot recover a verb from an `adjective`, so `adjective` at
a participle destroys a coarse judgment rather than recording a finer one. The four
wordforms under measurement are deliberately **absent** from the new text, per the
discipline this repository recorded after the `pel` → `pelo` incident, so the next run
measures something.

---

### What the next session reports back

The prompt changed, so a regeneration is owed: `--force`, and it will overwrite the eight
hand corrections — which is expected, not a loss, since `CORRECTIONS.md` is rewritten
against the new artifact.

```
uv run python -m layers.gen2.l2 inferno -c 1 -m google:gemma-4-31b-it --force
uv run python -m layers.gen2.l2 inferno -c 1 --check
```

Read four things off it, in this order:

1. **1:115 `disperate` and 1:116 `dolenti`** — the whole point of this session's prompt
   change. `verb` means the reason reached the model and the convention needs no
   mechanism. `adjective` means prose is not enough, and the eleventh tag returns to the
   table on *different* grounds than the ones declined above (not "the category exists"
   but "the convention is unenforceable").
2. **`pel` 1:33 a third time**, plus `de'` 1:17 and `dipartilla` 1:111. Two runs have
   agreed; a third is what makes it a property of the pass rather than of two draws.
3. **Which of the eight corrections the new artifact needs again.** Run 1 and run 2
   overlapped at only some positions, so this is also the third data point on how much
   the tag column wobbles. Rewrite `l2/CORRECTIONS.md` against the new file: carry
   forward what survives, drop what does not, re-verify each against precedent.
4. **The `[two readings]` and `[pos differs]` counts** (16 and 36 last time, 33 after the
   hand corrections), and the refusal count and class — all four refusals were
   `is_restoration` in run 2, and that class is the one being left to hand correction
   rather than to prompt examples.

Then: the standing open items are unchanged — the corpus-wide `del`/`nel`-shaped
measurement, and widening past *Inferno* 1, where `layer2-ambiguous` and `l2-ambiguous`
have still never fired on real data.

---

## Why this directory exists

`layers/` opens because `harness/` finished the thing it was actually built for
and ran out of a subject worth pointing it at unchanged.

`harness/` is named for the apparatus, not for Layer 5. Its own mission
statement ([`../harness/PLAN.md`](../harness/PLAN.md) §1) says the goal is "a
reproducible, fully automated, and generalizable reconstruction pipeline";
Layer 5 was the first subject, chosen because it is the richest target in this
corpus. That mission is met. What is *not* met — and what this directory takes
up — is the assumption printed in the same paragraph: that `skel/` and the
layers beneath it are an **immutable** reference the pipeline reproduces.

The division of labour from here:

- **`dante_corpus.harness`** — the library. The canto loop, the fixed-context
  execution mode, the gates' shape, the `--fix` machinery, the artifact and
  resume machinery, the observability contract. It is a tool, and it is finished
  (see **§1**). Since 2026-09-07 it is literally a package: the apparatus was
  split out of `harness/` and imports nothing else from `dante_corpus`, so it
  ships with the distribution. What stays in top-level **`harness/`** is Layer
  5's own side — the gates' content, the fix levels, the toolset, the skill
  files, the CLI and the `recon/` artifacts — which is what a *subject* looks
  like to this library.
- **`layers/`** — this directory. Skills and loops that *use* that tool, aimed
  at the layer stack itself: what each layer can and cannot express, and what
  the description ought to say.

The mechanics of the split — what moves and what stays — were a separate
discussion, held after this document was written and settled on 2026-09-07;
[`../harness/PLAN.md`](../harness/PLAN.md) §2, *After the last stage*, is the
record. Nothing here specifies them.

---

## 1. What the last two sessions established

Two findings, and they point in opposite directions. Recording both is the
reason this document exists.

### 1.1 The apparatus is stable (2026-09-06, `harness/stages/10.md` §S10.4)

Level 3's first corpus-wide `--fix` run is the readout. It was not a trial of
the corpus; it was a trial of the machine, and the machine passed every check
put to it in advance:

| | |
|---|---|
| findings (the criterion) | **334 → 225** |
| corpus | 3,126 → **2,982 soft**, **0 hard** |
| levels 1 and 2 after the pass | **0 / 0**, unmoved |
| suite | **1,029 passed** |
| gold agreement (readout only) | 0.7610 → 0.7628 |
| units reopened | **293** across 94 cantos |
| verdicts | 62 accepted, 20 salvaged, 206 no improvement, 5 refused |
| `FixClass.exempts` (first live use) | fired at **exactly 3** units, each at a predicate the level's own findings named |
| the 5 `new_class:extra_arg` refusals | all at *other* predicates — correctly refused |
| units ending worse | **0** (hard 0 everywhere; no unit's own findings rose) |
| concurrency (first ever) | 3 streams, 16.82 h elapsed in **6.72 h wall = 2.50×**, **0 `api_retries`**, ≈ 8,800 tokens/min against the 16K TPM quota |

The mechanism does what it is told, and what it is told is auditable after the
fact. **The apparatus is no longer the open question.**

### 1.2 The object is not stable

The same session, asked to settle one narrow gate question (`harness/stages/10.md`
§S10.2), measured the layers instead and found the description undecided at the
positions the question was about. Every number below is from the frozen layers
and the recon artifact; gold was not opened.

**The 133 `membership` violations** (all of them bare `obl` — that is S10.2's
own finding), by the Layer-4 deprel of the argument:

```
advmod 108    mark 12    advcl 7    amod 2    case 2    conj 1    det 1
```

The 108 `advmod` ones, by the Layer-2 pos of the argument:

```
adjective 87    conjunction 9    preposition 8    verb 2    noun 1    preposition+noun 1
```

**Layer 2 contradicts itself at these positions.** Corpus-wide there are
**9,249** `advmod` tokens; Layer 2 calls 90.8% of them `adverb`, 5.1%
`adjective`. Splitting the 108 by how the *same word* is tagged at its other
`advmod` positions:

| | count | shape |
|---|---:|---|
| **A** | **15** | the word is usually `adverb` at `advmod`; this instance is not (`forte` ×3, `certo` ×3, `come` ×3, `entro` ×2, `presso` ×2, `tanto` ×1) |
| **B** | **41** | the word is tagged both ways and this is the majority (`tutto` ×10, `solo` ×7, `ratto` ×5, …) |
| **C** | **52** | the word is never tagged `adverb` at `advmod` anywhere (`fiso` ×3, `dritta` ×2, `lento` ×2, `veloci` ×2, …) |

Group A is the shape [`../morph/CORRECTIONS.md`](../morph/CORRECTIONS.md)
already treats as a mistag — "`giuso` … **the only one of 33 occurrences** in the
corpus tagged noun". `certo` at `advmod` is `adverb` 15 / `adjective` 9; `forte`
is 15 / 8. Same word, same function, two descriptions.

### 1.3 The root cause is a flat encoding, not a wrong rule

`per certo` is `preposition + adjective` at the token level — correctly so — and
an **adverb** as a whole. The stack is token-indexed, so it has nowhere to say
the second thing, and the annotation has to push the phrase's category onto one
of its tokens or onto the edge above it. Both were tried, inconsistently.

**The corpus already owns three devices for this, and only one direction is
built out:**

| device | expresses | usage |
|---|---|---|
| Layer 2 composite pos | **1 token = several categories** | `preposition+article` 1,984, `verb+pronoun` 488, `pronoun+preposition` 58, `adverb+pronoun` 42, `preposition+noun` 12, `preposition+adverb` 4, `adverb+adjective` 1 |
| Layer 4 `fixed` | **several tokens = 1 grammatical word** | **171 edges, 168 of them complex prepositions** (`in su` 51, `dietro a` 15, `presso a` 11, `per entro` 8 …), all with `head_deprel=case` |
| Layer 3 spans | **several tokens = 1 phrase, with a head** | noun phrases only (columns are `line, start, end, head, text` — the shape is general) |

The same word takes both treatments depending on which direction it grammaticalised
in:

```
Inf 23:148  dietro a le poste …   dietro pos=preposition deprel=case   FIXED child 'a'    hierarchy expressed
Inf  9:55   Volgiti 'n dietro …   dietro pos=adverb      deprel=obl    case  child "'n"   flattened
Inf 11:6    ci raccostammo, in dietro, ad un coperchio
                                  dietro pos=adverb      deprel=advmod case  child 'in'   flattened
```

**The cost is measurable.** Of 9,249 `advmod` tokens, **68 (0.7%) carry a `case`
child** and every one is an Italian adverbial locution — `di sùbito` 8,
`del tutto` 6, `di più` 5, `a pena` 5, `per certo` 3, `in dietro` 2, `di rado` 1,
… Widening to every position where such a locution head appears (32 distinct
locutions, **330 positions**), Layer 4 attaches the *same phrase* four different
ways:

```
obl 217    advmod 68    nmod 30    conj 13    xcomp 1    obj 1
```

```
di retro   obl=27  nmod=2  advmod=1        a pena     obl=10  advmod=5
di fuor    obl=17  nmod=5  advmod=1        del tutto  advmod=6  obl=2
di sotto   obl=15  nmod=6  advmod=2        di sùbito  advmod=8
in dietro  obl=14  advmod=2  conj=1        di più     advmod=5
```

A flat encoding gives the annotator two half-truths — *the phrase is adverbial*
(→ `advmod`) and *the head carries a `case` child, so it is a PP* (→ `obl`) — and
no way to hold both. 217 : 68 : 30 : 13 is the record of that choice being made
without a criterion.

### 1.4 The consequence reaches Layer 5, and it is arbitrary

`obl` is in `ARG_DEPRELS`, so `derive.py` derives it as an argument and an agent
row matching it is clean. `advmod` is not, so the *identical* row becomes
**`membership` + `extra_arg` — two violations**.

> The same phrase scores 0 or 2 violations depending on a Layer-4 choice that
> has no criterion behind it.

**Inferno 28:4** carries three `advmod` arguments and all three outcomes:

```
Ogne lingua per certo verria meno            per lo nostro sermone e per la mente
                                             c'hanno a tanto comprender poco seno.
```

| | what it is | agent wrote | checker says | correct? |
|---|---|---|---|---|
| `per certo` (4.4) | adverbial locution, sentence-modifying — **not an argument** | `obl` | membership + extra_arg (**2**) | right conclusion, by accident of `pos` |
| `meno` (4.6) | part of the verbal idiom *venir meno* — **not an argument** | `obl` | **0** (pos=`adverb` → exempt) | **wrong** |
| `tanto` (6.4) | what *comprender* comprehends — **is an argument** | `obl` | **0** | right |

And the agent is not over-generating: writing `obl` at `per certo` follows the
corpus's own majority treatment, **217 of 330**. It is penalised only where
Layer 4 happened to pick the minority label.

### 1.5 What `validate.py:158` actually is

The membership check exempts a bare `obl` whose argument's Layer-2 pos is
`adverb` (`dante_corpus/skel/validate.py:158`). Read against the above, that
condition is **a proxy for "is this phrase lexicalised?" expressed in the only
vocabulary a token layer has**. The proxy is needed because there is no place to
write the judgement itself. Registry rules J and R are two more proxies for the
same phenomenon with two more form conditions:

| | role | required pos |
|---|---|---|
| `validate.py:158` (contract, ungated) | `obl` / `obl:*` | `adverb` |
| rule J `_adverbial_oblique` | `obl` / `obl:*` | `adverb` / `noun` / `pronoun` |
| rule R `_predicative_advmod` | **`xcomp`** | `adjective` / `noun` |

Three conditions for one phenomenon is the signature of a judgement with no home.

**This is why S10.2 cannot be decided inside Layer 5**, and why the harness's
gate (`runner/tools.py`) cannot simply be aligned to the contract: the contract
is a proxy, and aligning to it would freeze the proxy.

---

## 2. The premises this work runs on

Set by the operator (2026-09-07), before any decision, and adopted here as
standing:

1. **Gold has no authority.** It is the product of ad hoc work. A rule change
   that puts gold in violation is information, not a problem.
2. **The other layers are not necessarily right either.** Do not force
   consistency inside the layer under work. The precedent is on disk: the
   Layer-5 read revised the layers beneath it, and each keeps its own record —
   [`../dep/CORRECTIONS.md`](../dep/CORRECTIONS.md) **42** correction sections,
   [`../case/CORRECTIONS.md`](../case/CORRECTIONS.md) **34**,
   [`../morph/CORRECTIONS.md`](../morph/CORRECTIONS.md) **30**,
   [`../np/CORRECTIONS.md`](../np/CORRECTIONS.md) **19** — with a methodology
   already stated there: classify by cause before touching anything, verify each
   row against an existing precedent row, re-run the layer's `--check`
   afterwards.
3. **Rules are decided by linguistic validity.** There is no a priori guiding
   principle to derive them from.

**One engineering constraint sits beside premise 3, and is not a fourth
premise:** a rule the agent cannot reach from the frozen layers is a rule the
agent cannot satisfy. Linguistic validity decides *what* the description says;
it does not decide *which layer it is written in*. Keeping those two apart is
what S10.2 failed to do.

---

## 3. The termination condition, and how it changes

**`harness/`'s termination condition was never written down.** It operated as
"Layer 5 conforms to the layer's own contract", implemented as "the soft
findings a fix level can reach are exhausted" — the stage structure, levels
1 → 2 → 3 → …

That condition presupposes §1.2's negation: that the contract and the layers
beneath it are fixed and correct. Where they are not, remaining findings are a
mixture of *the artifact is incomplete* and *the description is undecided*, and
a fix level cannot tell the two apart. Continuing would have the agent fit the
encoding's arbitrary choices — the ad hoc method of gold construction,
automated. That is the reason the condition changes rather than the reason a
level was hard.

**The new one, in scope and in kind:**

| | was | becomes |
|---|---|---|
| scope | Layer 5 | the whole layer stack |
| target | reproduce the current description | **review the description itself** |

[`../harness/FUTURE.md`](../harness/FUTURE.md)'s vertical-slice note already
planned the first half — the harness building every layer over a narrow range —
but assumed the second half away: it expected the current results to be
reproduced. That assumption is dropped, and the correction stands in that file
as a dated standing note at its head (2026-09-07), which also records what
survives it unchanged — the machinery inventory, the swap costs, the
feasibility gradient, and the own-precedent store.

### 3.1 What the change costs

Three things stop working, and each needs a successor.

1. **Standing Invariant §1 becomes provisional.** §1 keeps gold out of rule
   construction by naming `validate.py` / `derive.py` as the substitute
   authority. If the layers are under review, that substitute is under review
   too. §1 must not simply empty: the successor is premise 3 written as a rule —
   **rules are decided by linguistic argument from the primary text, and the
   argument is recorded**. The prohibition on fitting to gold survives intact;
   what changes is that the contract drops from *authority* to *current
   description*.
2. **The progress metric is gone.** Soft counts are not comparable across a
   moving contract, and `make agree` loses its baseline. The successor is
   already designed, in `FUTURE.md`'s horizon memo: the correlation between
   **settled by intrinsic criteria** (clean validation plus convergence, no gold
   consulted) and agreeing with gold. It was written for rungs (2)–(4) of that
   memo's ladder, where no gold exists. It is needed at rung (1) now.
3. **The stage structure retires with the condition it served.** "Pick a soft
   class, argue it from the contract, make it a level" works only while the
   contract is fixed. Stage 10's residue — **225 findings at level 3, 2,982 soft
   corpus-wide** — is a readout of where the current description and the current
   artifact disagree. **It is not a to-do list.**

---

## 4. What is open

Nothing below is started. The order is not fixed either, except that the last
one waits.

One all-layer read exists, as a pilot rather than as work on any item:
[`reads/inf-1-1-9.md`](reads/inf-1-1-9.md) — nine lines, eight findings, five
corpus-wide measurements. It proposes a classification axis for item 3 and a
hypothesis that would reshape item 2, and it is one passage, so neither is
adopted here.

1. **Which phenomena are hierarchical, and how many.** §1.3 measured one family
   (adverbial locutions, 330 positions). Others are visible and unmeasured:
   verbal idioms (*venir meno*), secondary predicates (`dritto levato` vs `fiso`
   in the same line, Inf 4:5 — depictive and manner both under `advmod`), the
   714 `advcl`-as-`obl` population Layer 5 declines on principle, the quotes
   hierarchy. A survey is the first work item.
2. **Where a hierarchical judgement gets written.** Three candidate homes, all
   already in the corpus (§1.3's table): Layer 4 `fixed` (UD's own device, in use
   for the mirror-image case), a Layer-3-style span layer generalised beyond NPs,
   or a Layer-2 composite pos (only for one-token cases). The decision is per
   phenomenon, not global.
3. **The classification readout.** Split today's 2,982 soft violations by a new
   axis — *disagreement about the language* vs *disagreement about the
   encoding*. Distinct from S6.1's three outcomes, which assumed a fixed
   contract. Stratified sampling by class is the practical form; the whole
   population is too heavy.
4. **The non-locution `advmod` residue.** Group C's 52 (§1.2) — bare adverbially
   used adjectives with no `case` child — are not multiword expressions and the
   flat encoding is adequate for them. What is undecided is whether Layer 5
   counts an `advmod` modifier as an argument at all. Inf 4:5 is the exemplar
   and needs its own all-layer read.
5. **`layers/` as a working directory.** Skills and loops that drive `harness/`
   as a library. Deferred until the harness split is settled.

---

## 5. Relationship to the existing documents

- [`../harness/PLAN.md`](../harness/PLAN.md) — the harness's own plan and stage
  history. Stays where it is; its closing discussion is the next conversation.
  Its §1 statement that `skel/` is an *immutable* Gold Standard is what §3 above
  supersedes.
- [`../harness/FUTURE.md`](../harness/FUTURE.md) — the layer swap, the vertical
  slice, and the horizon memo. §3 above promotes the horizon memo's intrinsic
  settlement criterion from future work to present need, and drops the vertical
  slice's reproduce-the-current-results assumption; both are recorded there in
  the standing correction at the file's head, so the notes below it are read
  through it.
- [`../harness/stages/10.md`](../harness/stages/10.md) — S10.1–S10.4 for level 3
  and its run; **S10.2** is the gate question this document answers by
  dissolving it, and that answer belongs in Stage 10's ledger as well as here.
- `*/CORRECTIONS.md` — the five per-layer correction records. They are the
  precedent for how a layer gets revised, and the methodology to keep:
  classify by cause before touching anything, verify against an existing
  precedent row, re-run each layer's `--check` afterwards.
- [`../ARCHITECTURE.md`](../ARCHITECTURE.md) — model access, wire protocol,
  observability. Unaffected; it describes the apparatus, which is what carries
  over.
