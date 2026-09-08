# layers — reviewing the description itself

The other layer directories each own an artifact: `morph/`, `case/`, `np/`,
`dep/` and `skel/` hold a frozen annotation, the `--check` that validates it, and
a `CORRECTIONS.md` recording every revision. This directory's subject is instead
**the description those layers are written in** — what each layer can and cannot
express, and what it ought to say.

It owned no artifact until 2026-09-09, when the review turned into a rebuilt
generation and that generation started producing one. The split is by kind:
**[`gen2/`](gen2/) is code**, and nothing is written into it; the artifacts it
builds sit beside it (`l2/<canticle>/NN.tsv`), in the same
`<layer>/<canticle>/NN.tsv` shape the older layer directories use.

It opened on 2026-09-07, when `harness/` closed. The harness reached its goal — a
reproducible, automated reconstruction pipeline — but that goal presupposed the
layer stack was an immutable reference, and the same work showed it is not: the
description is undecided at exactly the positions the last open question was
about. Reproducing it further would mean fitting an agent to choices that have no
criterion behind them. So the target changed from *reproduce the current
description* to *review it*, and the scope from Layer 5 to the whole stack.

`dante_corpus.harness` is now a library rather than a development subject. Work
here drives it; it is not worked on here. See
[`../harness/README.md`](../harness/README.md).

## Read this first

**[`PLAN.md`](PLAN.md)** — what established the change, the premises the work
runs on, what the change costs, and what is open. It is the source of truth for
this directory and the document that gets updated; everything else here is
evidence it cites.

## What is here

- **[`PLAN.md`](PLAN.md)** — the plan. Start here.
- **[`REDESIGN.md`](REDESIGN.md)** — a proposal, not a decision: decomposed
  terminals and an enumeration of phrases, deliberately stopping short of a tree
  rooted at the sentence, with the measurements that support it and the questions
  it leaves open. It is what `PLAN.md` §4-2 would be replaced *by* if the read's
  grammatical-word hypothesis survives; §4 stands as written until then.
- **`reads/`** — all-layer reads. One short passage displayed at every layer at
  once, read for what the stack can and cannot say, with each observation
  measured corpus-wide before it is written down. Findings stay in the read that
  produced them until they survive more than one passage; only then does `PLAN.md`
  adopt them.
  - [`reads/inf-1-1-9.md`](reads/inf-1-1-9.md) — *Inferno* 1:1-9, the first.

## How the work is constrained

Three premises, set before any decision (`PLAN.md` §2), and one engineering
constraint that is not a premise:

1. **Gold has no authority.** A rule change that puts gold in violation is
   information, not a problem.
2. **The other layers are not necessarily right either.** Do not force
   consistency inside the layer under work.
3. **Rules are decided by linguistic validity**, argued from the primary text,
   and the argument is recorded. There is no a priori principle to derive them
   from.

The constraint: a rule the agent cannot reach from the frozen layers is a rule
the agent cannot satisfy. Linguistic validity decides *what* the description
says; it does not decide *which layer it is written in*. Those two are kept
apart.

Premise 1 has a consequence worth stating plainly: `skel/` is a **subject** here,
not an oracle. Reading it is expected. Deriving a rule by matching it is not —
that prohibition, inherited from `harness/`, survives the change intact.

## Method

The per-layer `CORRECTIONS.md` files are the precedent, and their methodology is
the one to keep: classify by cause before touching anything, verify each row
against an existing precedent row, re-run the layer's `--check` afterwards.

What is new is that every layer's own `--check` is layer-local, so the
inconsistencies this directory is about are invisible to all of them. The
measurements live between layers.
