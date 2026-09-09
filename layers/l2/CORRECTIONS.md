# Manual generation-2 Layer-2 corrections

> [!NOTE]
> **This file records manual corrections only** — edits made by hand, directly in a
> committed `layers/l2/<canticle>/NN.tsv`, with no model call. It is a history of
> human judgments applied to the artifact, one entry per position.
>
> **It is not a changelog for the layer.** A correction that comes from changing the
> *mechanism* — a prompt fix, a gate rule, a new tag, a re-run under a different
> contract — does not belong here, however many positions it moves. Those changes are
> argued in [`../L2.md`](../L2.md) and recorded in [`../PLAN.md`](../PLAN.md)'s
> handoffs, and their effect reaches the artifact by regeneration, not by editing.
> If an entry below is later overturned by such a change, the entry stays as the
> record of what was decided and when; it is not rewritten.

Generation-2 Layer 2 (`layers/l2/`) is build-time output — one model call per chunk of
lines, gated at the runtime, written to `layers/l2/<canticle>/NN.tsv` (`line`,
`l1_index`, `l2_index`, `text`, `pos`). The gate enforces the *shape* of an answer: one
row per token in the order given, a single word that is the token or the token with its
dropped letters put back (`is_restoration`), and one closed-set tag per word. It cannot
catch a row that is structurally clean and linguistically wrong.

Hand-editing the artifact is adopted deliberately (operator, 2026-09-09, argued in
[`../L2.md`](../L2.md)): steering a one-shot prompt toward a known answer and correcting
that answer afterwards put the same human judgment into the corpus by two different
routes, and only the second one leaves a record. This file is that record.

**Methodology, inherited from the four per-layer files that precede it**
([`../../morph/CORRECTIONS.md`](../../morph/CORRECTIONS.md),
[`../../dep/CORRECTIONS.md`](../../dep/CORRECTIONS.md),
[`../../case/CORRECTIONS.md`](../../case/CORRECTIONS.md),
[`../../np/CORRECTIONS.md`](../../np/CORRECTIONS.md)): classify by cause before touching
anything, verify each row against precedent elsewhere in the corpus before applying it,
and re-run the layer's `--check` afterwards. Old Layer 2 (`morph/`) is cited here as
**precedent, never as authority** (premise 1) — where this artifact departs from it on
purpose, the entry says so.


## 8 rows from the first two runs of *Inferno* 1 (2026-09-10)

*Inferno* 1 was generated twice under the merged split-and-POS pass
(`google:gemma-4-31b-it`), the second time after the `Index` column was added. Positions
that moved between the two runs cannot carry an argument on their own — repeated runs
detect disagreement, they do not verify correctness — so each entry below is argued from
the line and from corpus-wide precedent, and names which run it was found in.

Applied to `layers/l2/inferno/01.tsv` (the run 2 artifact, committed at `30aee49` as the
model produced it). `--check` before and after the batch:

| | splits | tags | restorations |
|---|---|---|---|
| before | 507 agrees, 4 differs, 0/0 | 953 of 989 (96.4%) | 143 positions, 74 distinct |
| after | **507 agrees, 4 differs, 0/0** | **956 of 989 (96.7%)** | **145 positions, 76 distinct** |

No split moved — every correction here is in the `pos` column or is a restoration of a
token that was already one grammatical word. The net gain of three tag agreements is
five mistags removed against **two participles deliberately put *into* disagreement**
with old Layer 2, so the headline figure understates the first group and should not be
read as the batch's whole effect.

### Tags contradicted by the word's own corpus-wide record

**inferno 1:7 `poco`** — `pronoun` → `adverb`. "*Tant' è amara che **poco** è più
morte*": so bitter that death is little more. `poco` is **never** a pronoun anywhere in
the corpus — old Layer 2 reads it `adverb` 75×, `noun` 43×, `adjective` 26×, and
`pronoun` **0×** — which is the shape `morph/CORRECTIONS.md` already treats as a mistag
("*giuso* … the only one of 33 occurrences in the corpus tagged noun"). Run 1 read this
position `adverb` and agreed with old Layer 2; run 2 alone introduced the error, and it
is also what makes `poco` read three ways in run 2's `[two readings]` (`pronoun` ×4,
`noun` ×3, `adverb` ×1).

**inferno 1:49 `brame`** — `verb` → `noun`. "*Ed una lupa, che di tutte **brame** /
sembiava carca ne la sua magrezza*": a she-wolf that seemed laden with every craving.
`brame` is the plural of the noun *brama*, which old Layer 2 reads `noun` at **7 of 7**
occurrences corpus-wide and never as a verb. Present in both runs.

**inferno 1:49 `tutte`** — `pronoun` → `adjective`. Same line: `tutte` is attributive on
`brame` — *di tutte brame* — not a pronoun standing for a noun, which is the boundary
the prompt itself draws ("*a possessive or demonstrative modifier is `adjective`;
standing on its own for a noun, it is `pronoun`*"). Old Layer 2 reads it `adjective`
f. pl. Present in both runs.

**inferno 1:100 `Molti`** — `pronoun` → `adjective`. "***Molti** son li animali a cui
s'ammoglia*": the adjective is predicative, agreeing with `li animali`, and predicative
use does not make an adjective a pronoun. Old Layer 2 reads `molto`/`molti` `adjective`
62×, `adverb` 29×, `noun` 4×, `pronoun` 3× corpus-wide, and `adjective` at every
occurrence of the plural `molti` in this predicative shape (*Inf* 4:61, 4:121, 29:105,
*Par* 2:64, 7:29, 13:108, 13:125, 16:142, 17:117, 19:20, 19:106). Run 2 only.

### Restorations the gate refused and the model then declined to make

Both of these are apocope — old Layer 2 marks both `apocope` in its `note` column — so a
restoration is owed. In each case the model first offered a **respelling**, the gate
correctly refused it (`is_restoration` requires the token's own letters to read straight
through the answer), and the retry then left the token whole rather than restoring it
correctly. The gate was right both times; what is missing is the right answer, which is
supplied here.

**inferno 1:112 `me'`** — `me'` / `pronoun` → `meglio` / `noun`. "*Ond' io per lo tuo
**me'** penso e discerno*": for your good. The model answered `me`, which the gate
refused as a truncation rather than a restoration; `meglio` passes `is_restoration` (the
apostrophe opens the end, and `me` reads straight through `meglio`). Old Layer 2 records
lemma `meglio`, `noun` m. sg., note `apocope` — the nominalised comparative, not the
pronoun *me*. Present in both runs.

**inferno 1:124 `imperador`** — `imperador` → `imperadore`; tag `noun` unchanged. "*ché
quello **imperador** che là sù regna*". The model answered `imperatore`, and the gate
refused it correctly: *imperatore* is the modern form and its `t` breaks the token's own
letters, so it is a lexical substitution, not a restoration. The Tuscan form
`imperadore` is what the dropped syllable restores (`is_restoration` passes), and it is
the form Dante writes in full elsewhere. Old Layer 2 records `apocope` here, confirming
letters are missing; its `lemma` column holds `imperatore`, but a lemma is not a
restoration and this pass writes no lemmas. Run 2 only.

### Internal inconsistency against this pass's own stated convention

**inferno 1:115 `disperate`** — `adjective` → `verb`, and
**inferno 1:116 `dolenti`** — `adjective` → `verb`. "*ove udirai le **disperate**
strida*" / "*vedrai li antichi spiriti **dolenti***". The prompt states the convention
flatly — *a participle is `verb`, always … whether it stands in a compound tense,
predicatively, or in front of a noun like an adjective; do not retag a participle
`adjective` because it reads like one here* — and the same artifact applies it at
`smarrita` (1:3), `giunto` (1:13), `compunto` (1:15), `vestite` (1:17), `affannata`
(1:22), `vòlto` (1:36), `carca` (1:50), `combusto` (1:75) and `ribellante` (1:125).
These two are the same shape treated differently in the same file, so they are corrected
to the convention.

**This is the one entry here that departs from precedent on purpose.** Old Layer 2 reads
`disperato`/`dolente` `adjective` at **26 of 26** occurrences corpus-wide, so the
correction puts this artifact against a unanimous precedent — deliberately, under
premise 1, because the convention is this pass's own and its point is to keep a
participle from being decided by how adjectival it happens to read.

**These two positions are also the evidence in the open eleventh-tag question**
(`../L2.md`, *The regeneration under `Index`*): run 1 read both `verb` and run 2 read
both `adjective`, which is the model declining the convention at exactly the lexicalised
boundary that produced old Layer 2's 573-row `adjective` bucket (`../REDESIGN.md` §6). If
a `participle` tag is adopted, these positions are revisited **by regeneration**, and
this entry stays as the record of what the convention was when the artifact was written.
