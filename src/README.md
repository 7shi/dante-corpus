# Italian Source Texts and Scene Breakdowns

This directory holds the Italian source text of Dante's *Divina Commedia*,
split canto by canto under `inferno/`, `purgatorio/`, and `paradiso/`, together
with tooling that produces a scene-by-scene breakdown of each canticle.

## What a scene breakdown is

A breakdown summarizes a canticle as a sequence of scenes. For every canto it
emits a `## Canto N` heading followed by a Markdown table with the columns
`Lines`, `Scene` (a short, concrete label for the dominant event), and
`Summary` (a one-sentence description of what happens in that line range).
Scenes are divided at natural shifts in the text (place, speaker, action, or
topic) rather than at a fixed interval.

## Generating breakdowns: `scene.py`

`scene.py` generates breakdowns with a **local LLM** (via `llm7shi`; default a
local Ollama model, override with `-m`). To keep a small model stable it uses a
two-turn flow per canto:

1. **Planning** — the model reasons in plain prose (chain-of-thought enabled)
   about where the scene boundaries fall, biased toward fine-grained splits
   (merging scenes afterward is easy; re-splitting would need the source).
2. **Structuring** — the same conversation is asked to emit the result as a
   structured `CantoBreakdown` (Pydantic schema). The scene ranges are then
   checked for gaps, overlaps, reversed ranges, and coverage against the source
   line count; if the check fails, only this step is retried (with the specific
   problems fed back to the model), and the run aborts after three consecutive
   failures so no invalid canto is written.

Output is in **English** by default (`-l` to change), which avoids the
translation overhead that made the local model degenerate when forced to write
Japanese directly.

### Output and resuming

Each canticle produces one `.md` (e.g. `inferno.md`) plus a per-canto JSON
checkpoint written next to each source line file — `inferno/01.json` beside
`inferno/01.txt`, and so on. Each canto's breakdown is written as soon as it is
generated, so an interrupted run resumes by re-running the same command
(cantos that already have a JSON are skipped). Once every canto is present the
per-canto JSON files are rendered into the final Markdown.

### Usage

```sh
# All three canticles into this directory (inferno.md + inferno/NN.json, etc.)
make scenes
make scenes MODEL=google:gemini-3-pro-preview   # override the model

# A single canticle
uv run python scene.py inferno -o inferno.md

# Test one canto (no JSON checkpoint unless --save is given)
uv run python scene.py inferno -o /tmp/test.md -c 1
```

Key options: `-o` (single canticle → explicit file) vs `--outdir` (one or more
canticles → `<canticle>.md` each); `-m`/`--model`; `-l`/`--language`;
`-c`/`--canto` (test a single canto); `--save` (in test mode, also write the
per-canto JSON checkpoint).

## Manual corrections to `inferno.md`

The following factual/proper-noun errors in the generated `inferno.md` were
hand-corrected after checking the source in `inferno/`. These edits live **only
in `inferno.md`** — the per-canto `inferno/NN.json` checkpoints keep the raw
model output, so regenerating the Markdown with `scene.py` would overwrite them.

| Canto (lines) | Correction | Basis in the source |
|---|---|---|
| 5 (97–107) | Dido → **Francesca** speaking | "Siede la terra dove nata fui…" (Ravenna); "Caina attende" |
| 9 (title, 73–84, 88–99, 100–105) | Charon → **the heaven-sent messenger** | "un ch'al passo passava Stige con le piante asciutte"; "da ciel messo"; opens the gate with a *verghetta* |
| 12 (103–139) | Chiron → **Nessus** (the guiding centaur) | l.98 "disse a Nesso: «Torna, e sì li guida»" |
| 12 (133–138) | "the Rinvieri" → **Rinier da Corneto / Rinier Pazzo** (with Pyrrhus, Sextus) | ll.134–137 |
| 19 (title, 52–57, 64–78) | Boniface → **Pope Nicholas III** (who mistakes Dante for Boniface VIII) | "Se' tu già costì ritto, Bonifazio?"; "figliuol de l'orsa" (Orsini) |
| 25 (25–33) | the dragon → **the centaur** identified as Cacus | "io vidi un centauro… Questi è Caco" (the dragon rides on his back) |
| 34 (16–21) | the City of Dis → **Dis (Lucifer)** himself | l.20 "«Ecco Dite»" |
| 34 (61–67) | Cassio → **Cassius** (anglicized, matching Judas/Brutus) | l.67 "Cassio" |

## Manual corrections to `purgatorio.md`

Hand-corrected against the source in `purgatorio/` (same caveat as above — these
edits live only in `purgatorio.md`, not in the per-canto `purgatorio/NN.json`).

| Canto (lines) | Correction | Basis in the source |
|---|---|---|
| 2 (91–105) | "crossing the Acheronte" → souls gathered at the **mouth of the Tiber** | "dove l'acqua di Tevero s'insala"; Acheron is only where they do *not* go |
| 7 (title) | "the Limbo Valley" → **the Valley of the Princes** | the negligent rulers' valley in Ante-Purgatory |
| 8 (64–81) | Giovanna his "wife" → his **daughter** (the widow/mother is separate) | "dì a Giovanna mia… a li 'nnocenti si risponde"; "la sua madre… trasmutò le bianche bende" |
| 9 (title, 13–24, 25–33) | the "needle" → the **eagle** (Ganymede dream) | "un'aguglia nel ciel con penne d'oro" |
| 10 (1–6) | "gate of the lustful" → **gate of Purgatory** (perverse love) | "soglio de la porta che 'l mal amor de l'anime disusa" |
| 16 (16–21) | "the Neutrals" → **the Wrathful** | "Agnus Dei"; "d'iracundia van solvendo il nodo" |
| 17 (title) | "the Ninth Circle" → **the Ascent** (Purgatory has terraces, not circles) | — |
| 23 (title, 76–84, 85–96) | "Limbo" → **Purgatory / this terrace** (the gluttons) | "de la costa ove s'aspetta… liberato m'ha de li altri giri" |
| 24 (70–75) | "Forese Giunchi" → **Forese** (spurious surname) | l.74 "Forese" |
| 26 (1–9) | "Sunset in the Inferno" → **Sunset on the Mountain** | the terrace of the lustful, in Purgatory |
| 29 (title) | "of the Empyrean" → **in the Earthly Paradise** | the pageant atop Mount Purgatory |
| 29 (1–15, 55–63) | Beatrice → **Matelda** (Beatrice only appears in Canto 30) | the lady still singing "Beati quorum…"; "La donna mi sgridò" |
| 31 (title, 1–6, 22–30, 37–48, 49–63, 64–69) | "the Sphinx" → **Beatrice** (the speaker; no Sphinx here) | "O tu che se' di là dal fiume sacro" |
| 32 (124–129) | the "needle" → the **eagle** feathering the chariot | "l'aguglia vidi scender giù ne l'arca del carro e lasciar lei di sé pennuta" |

## Manual corrections to `paradiso.md`

Hand-corrected against the source in `paradiso/` (same caveat as above — these
edits live only in `paradiso.md`, not in the per-canto `paradiso/NN.json`).

| Canto (lines) | Correction | Basis in the source |
|---|---|---|
| 6 (title, 10–27) | Farinata → **Justinian** (the speaker) | l.10 "Cesare fui e son Iustinïano"; Pope Agapetus corrects his belief on Christ's nature (ll.13–18) |
| 6 (124–135) | "the Troubadours / Provençal poetic tradition" → the **harmony of the differing ranks of the blessed**, then **Romeo di Villanova** | ll.124–126 "Diverse voci fanno dolci note…"; l.128 "luce la luce di Romeo" |
| 9 (109–126) | "the spirit identifies itself as Raab" → **Folco points to the neighboring light as Rahab** | ll.115–117 "Or sappi che là entro si tranquilla Raab"; Folco is the speaker |
| 15 (25–31) | "the shade of Anchimates" → the spirit **Cacciaguida**, likened to the **shade of Anchises** greeting Aeneas | l.25 "Sì pïa l'ombra d'Anchise si porse… quando in Eliso del figlio s'accorse" (a simile) |
| 18 (100–108) | "the shape of a needle" → the **head and neck of an eagle** | l.107 "la testa e 'l collo d'un'aguglia vidi" (*aguglia* = eagle) |
| 25 (13–18) | "the figure of Hope" → **St. James** (who examines hope) | ll.17–18 "ecco il barone per cui là giù si vicita Galizia" (Santiago de Compostela) |
| 25 (64–78) | "the light of St. John" → **David** ("the supreme singer") and **St. James's epistle** | ll.72–77 "sommo cantor del sommo duce"; "Tu mi stillasti… ne la pistola" |
| 25 (109–114) | "the figure who died on the cross" → **St. John** | ll.112–114 "che giacque sopra 'l petto del nostro pellicano… di su la croce al grande officio eletto" (entrusted with Mary, not crucified) |
| 26 (118–123) | "the history of Virgil" → **Adam's** 4,302-year wait in Limbo and 930-year life | ll.118–123 "Quindi onde mosse tua donna Virgilio, quattromilia trecento e due volumi…" (Virgil names only the place) |

## `ref/` — reference examples

`ref/inferno-ja.md`, `ref/purgatorio-ja.md`, and `ref/paradiso-ja.md` are
**Japanese** reference breakdowns generated by GitHub Copilot (GPT-5.4),
following the policy in [`ref/AGENTS.md`](ref/AGENTS.md). They predate `scene.py`
and are kept as worked examples of the intended structure and granularity; their
table headers (`行` / `場面名` / `内容`) and summaries are in Japanese.

[`ref/inferno-01.toml`](ref/inferno-01.toml) is a hand-written **context-lock**
sample for Inferno Canto 1 — a per-scene skeleton that fixes identity only (who
speaks, where, who "this light" is) as translation pre-processing, with a `basis`
quote per entry for verification against the source. It is kept here to compare
against a model-generated version later. See `PLAN.md` for the design and the
error patterns it guards against.
