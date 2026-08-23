# Beyond Layer 5: Future Directions (design notes, not scheduled work)

Companion to [`PLAN.md`](PLAN.md). Everything here concerns what becomes
possible **after** the `skel/` (Layer 5) reconstruction that `PLAN.md` plans and
tracks; nothing in this file is scheduled, and nothing in it asks for a
refactor of current code. `PLAN.md` stays the single source of truth for status,
milestones, and standing disciplines. Bare `§N` references below point into
`PLAN.md`.

The three notes build on one another: a **layer swap** (same machinery, a
different target layer) → a **vertical slice** (the harness builds every layer
itself over a narrow range) → the **horizon** (a language with no grammatical
description available at all).

---

## Layer-direction generalization (design note, 2026-08-23 — not scheduled work)

`harness/` targets Layer 5, but the same machinery can in principle reconstruct
a *lower* layer (L4 UD, L3 NPs) by re-scoping which layers the toolkit serves.
Recorded here because a successful layer swap would be independent evidence for
the §1 generalization claim ("layer-agnostic", alongside "language-agnostic").
Prototype only **after Stage 2**; nothing below asks for a refactor now.

**Already layer-independent (reusable unchanged):** the whole `toolcall/`
library (parser, prompts, transports, loop); the §4-item-5 observability frame
(`runner/statusline.py`, streaming JSONL contract, session separators,
`turn_seconds` roll-ups); the benchmark skeleton; the `upstream_feedback`
channel pattern (target layer reporting defects in the layers below it). Parse
units survive a layer swap too: `dep.sentence_groups(nos, texts)` keys on line
numbers and sentence-final punctuation only — it never reads L4 — so unit
bounds stay valid even when L4 itself is the masked target.

**What a layer swap actually costs (three items; none is a tool allow-list):**

1. **Masking is structural, so the *loader* must fork, not the tool schema.**
   `_load_canto` eagerly reads `canto.morph()/dep()/case()/np()` into
   `_CantoData`; L5 is masked because `tools.py` never imports `skel.io` at all
   (proved by poisoning tests). Dropping a key from `read_unit`'s return value
   would be a strictly weaker guarantee. An L4-target toolkit must never call
   `canto.dep()`.
2. **`search_corpus` changes character — the open design question.** The
   Anti-Leakage Guard only excludes the active canto. With L5 as target that
   suffices (gold is never loaded anywhere), but with L4 as target every hit
   carries other cantos' gold dep rows: the task drifts from inference toward
   retrieval. Masking the target layer out of hits instead guts the tool, since
   its query keys (`lemma` / `pos` / `deprel` / `case`) are themselves
   upper-layer features. Decide the stance first — deliberate
   retrieval-augmented annotation vs. measured autonomous inference vs. the
   own-precedent store below — before any implementation.
3. **`validate_candidate` is wholly layer-specific and is the real work.**
   `ROLES`, `OBL_RE`, the nominal NP-head citation rule, slot uniqueness with
   clitic licensing — that is the L5 schema. Another layer needs a peer
   intrinsic validator written from scratch (the bulk of milestone 1.1's
   effort). The swap adds a validator; it does not subtract tools.

**Own-precedent store — the harness's settled output is fair game (and the way
out of item 2's dilemma).** What must stay masked is *gold*, not everything in
the target layer's shape. Once the harness itself has settled a unit, that
result is the harness's own product and may be served back as searchable
precedent: later units then align with already-settled analogous cases instead
of re-deciding each pattern from scratch. This directly serves the §2 Stage-2
objective of cross-corpus consistency, and it rescues `search_corpus` under a
layer swap — hits carry the harness's own accumulated analyses rather than
other cantos' gold. It applies to the current L5 target too, not only to layer
swaps. Constraints to design against, not around:

- **"Settled" must be an intrinsic criterion**, never gold agreement.
  Gold-matched-therefore-confirmed would smuggle the evaluation oracle into the
  agent's context and quietly void every §5.2 metric. Candidate criteria:
  clean `validate_candidate` + convergence within budget, optionally plus human
  triage — all of them operator-side judgments computable without `skel/`.
- **The Anti-Leakage Guard still applies unchanged**: the active canto is
  excluded from precedent hits exactly as it is from corpus hits.
- **Path dependence becomes real.** Results start depending on processing
  order, and a benchmark whose context grows mid-run is not reproducible.
  Freeze the precedent store per run (build it in a prior pass, read-only
  during the scored pass) rather than letting it accumulate live.
- **Relation to Stage 2**: a queryable store of settled frames is a retrieval
  form of the valency lexicon. Build it after milestones 2.1–2.2 so the two
  share one representation instead of diverging.

**Layer feasibility gradient.** The harness thins out downward: an L2 target
leaves only L1 as input and reduces `search_corpus` to bare word matching
(every other query key is the target layer), degenerating to plain prompting.
L3/L4 keep L1+L2(+L3) and stay viable. L5 is the richest target by
construction — four layers of context beneath it, plus enough features for both
search keys and an intrinsic validator.

**Current abstraction boundary is already the right seam** — layer-specific:
`runner/tools.py`'s three tools; layer-independent: `toolcall/` + observability.
No pre-emptive refactor needed; a future L4 toolkit would sit beside
`runner/tools.py`, not inside it.

## Vertical slice — whole-stack reconstruction (design note, 2026-08-23 — not scheduled work)

The orthogonal axis to the layer swap above. **Horizontal**: one target layer,
gold everywhere else, wide coverage (what Stage 1 does today). **Vertical**:
pick a *narrow* range — a handful of parse units, at most a canto — and have
the harness build every layer itself, L2 → case → L3 → L4 → L5, each layer's
own settled output serving as the next layer's context. Depth traded for
breadth.

**Why it is the decisive test of §1's mission.** Stage 1 currently assumes gold
L1–L4 exist for the unit under analysis — precisely the assumption a new text
or language cannot satisfy. A vertical slice is the only configuration that
demonstrates the end-to-end claim: from bare text, the harness produces a
Layer-5 skeleton with no gold input at any level.

**L1 stays deterministic and given.** `dante_corpus/tokenizer.py` is the anchor
every layer cites (see the `morph/`, `np/`, `dep/` READMEs), and all row keys
are `(line, token)`. An LLM re-tokenization would shift every key and make
layer-by-layer diffing meaningless, so vertical mode's honest bottom is **L2**.
The quotes hierarchy rides with L1 as a given for the same reason: `quotes.py`
derives it mechanically from guillemet spans in `src/`.

**The measurement only this corpus can make.** Gold exists at *every* layer
here, so a vertical slice can be scored layer by layer **and** decomposed:
L5-given-gold-L4 (the current benchmark: micro F1 0.711) vs L5-given-own-L4.
The delta is the error-propagation tax of a fully autonomous stack — a number
that requires a completely gold-annotated multi-layer corpus to obtain at all.
That, rather than the L5 numbers themselves, is what would justify the cost.

**It makes `upstream_feedback` actionable for the first time.** Today L2/L4 are
gold and immutable, so the channel's records (19 from the M1.4 unit run) can
only park in human triage. In a vertical slice the harness *owns* those layers,
so a defect report can trigger an actual revision of the layer below —
back-propagation across the stack. Guard: needs an explicit commit/termination
discipline per layer, or adjacent layers will oscillate.

**Costs and preconditions.** Sessions multiply by the number of layers over the
range, and each layer needs its own intrinsic validator (item 3 above, ×4) — so
vertical *presupposes* the horizontal work rather than shortcutting it, and the
own-precedent store above is a prerequisite, not an option (every layer's
context is the harness's own settled output). Sequencing: after Stage 2, and
after at least one horizontal non-L5 toolkit has proven a second validator is
tractable. Choose the range from the existing 87 challenge fixtures so the
vertical L5 numbers stay directly comparable to the M1.4 baselines.

## Horizon — grammar reconstruction where no grammar book exists (memo, 2026-08-23)

Not a plan and not scheduled: the destination that gives the two notes above
their direction. Extrapolate the vertical slice to a language with **no
available grammatical description** — the harness reads a corpus of raw text
and induces the description itself, bottom-up, the way a field linguist works
from a closed body of material rather than from an existing reference grammar.

**Stage 2's deliverable already is that artifact, generalized.** Mined syntax
fast-path rules plus an empirical valency lexicon are a descriptive grammar
sketch; on Dante they are validated against a known answer, but the same
pipeline pointed at an undescribed language produces a grammar *as its primary
output*, with annotations as the by-product. That reframing is the point of the
memo.

**What must be separated first: assumed universals vs. induced theory.** The
vertical slice removes gold *input*, but the current stack still imports a
great deal from a described language — the UD relation vocabulary, the POS
inventory, `ROLES` / `OBL_RE`, `ItalianLanguagePack`, and above all the model's
pretrained knowledge of Italian. Legitimately assumable as cross-lingual
scaffolding: the token anchor, predicate-argument structure as an organizing
notion, UD's relation inventory (it is designed for exactly this). Necessarily
induced: the lexicon, POS inventory and morphological paradigms, the
argument-marking strategy (word order vs. case vs. adpositions), and the
preposition set that populates `obl:<prep>`. Drawing that line explicitly is
the first real work item whenever this is picked up.

**Honest limit of the Dante corpus for this claim.** Dante validates the
machinery and the metrics; it cannot validate the "unknown language" part,
because the model's pretrained Italian cannot be ablated. The credible ladder
is: (1) Dante — calibrate; (2) a low-resource language with a small existing UD
treebank — the model's prior is weak but a gold answer exists; (3) a
synthetic/permuted language — the prior is genuinely absent, the gold is
constructed; (4) the real target, where by definition there is no gold at all.

**Which makes one Dante-side measurement the actual bridge**: the correlation
between *settled by intrinsic criteria* (clean validation + convergence, the
own-precedent store's admission test) and *agreeing with gold*. Where no gold
exists, internal consistency plus expert audit is all that remains as an
acceptance signal — so how far intrinsic settlement predicts correctness is the
one quantity worth carrying forward. It is measurable here today and nowhere
later. Worth capturing opportunistically from Stage 2 runs even though the
horizon itself stays unscheduled.
