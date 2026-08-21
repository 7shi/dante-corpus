# skel — Layer 5 Manual Corrections & Upstream Retag History

This document is the authoritative record of all **manual corrections**, **hand-applied TSV edits**, **structural outlier resolutions**, and **upstream cross-layer retags** for Layer 5 (predicate-argument skeleton).

> **Context for Grammar Agent Harness (`harness/`)**:
> The entries documented in this file represent grammatical positions and phenomena that lay **outside the static deterministic rule system** (and required manual/agentic correction in Phase 7).
> In the autonomous grammar harness (`harness/`), **this file is strictly excluded from LLM context and reference tools** (`read_unit`, `search_corpus`).
> Instead, these challenging positions serve as a primary benchmark to test whether an autonomous agent with multi-layer reasoning (Gemma 4 31B) can **self-resolve** them from linguistic first principles without cheat-sheets.
> For chronological phase retrospectives and rule development logs, see [`PHASE5.md`](PHASE5.md), [`PHASE6.md`](PHASE6.md), and [`PHASE7.md`](PHASE7.md).

---

## Table of Contents

- [1. Phase 7: Residue Closure & Manual Read Censuses (160 → 0)](#1-phase-7-residue-closure--manual-read-censuses-160--0)
  - [1.1 §P15: Sixth Read Census & Final Residue Closure (38 positions → 0)](#11-p15-sixth-read-census--final-residue-closure-38-positions--0)
  - [1.2 §P14: Fifth Read Census (`role_mismatch` and `extra_arg`, 31 units / 49 soft)](#12-p14-fifth-read-census-role_mismatch-and-extra_arg-31-units--49-soft)
  - [1.3 §P13: Fourth Read Census (Clausal Arguments, 4 positions)](#13-p13-fourth-read-census-clausal-arguments-4-positions)
  - [1.4 §P12: Third Read Census (Paradiso Positions, 4 positions)](#14-p12-third-read-census-paradiso-positions-4-positions)
  - [1.5 §P11: Second Read Census (Spurious Arguments, 7 positions)](#15-p11-second-read-census-spurious-arguments-7-positions)
  - [1.6 §P10: First Read Census (Spurious Arguments & Layer-4 Retag, 7 positions)](#16-p10-first-read-census-spurious-arguments--layer-4-retag-7-positions)
  - [1.7 §P9: Round 10 Log Audits & Driver Fallback (3 drops + 1 Layer-4 retag)](#17-p9-round-10-log-audits--driver-fallback-3-drops--1-layer-4-retag)
  - [1.8 §P7: Structural Outlier Resolutions (7 positions)](#18-p7-structural-outlier-resolutions-7-positions)
  - [1.9 §P6: Final `dual_role` Contradictions (3 positions)](#19-p6-final-dual_role-contradictions-3-positions)
  - [1.10 §P5: Verbless Speech Introductions (`missing_tuple_nominal`, 8 positions)](#110-p5-verbless-speech-introductions-missing_tuple_nominal-8-positions)
  - [1.11 §P4: Refusal Census Upstream Retags (2 positions)](#111-p4-refusal-census-upstream-retags-2-positions)
  - [1.12 §P2: Comparative Standard Root Upstream Retag (1 position)](#112-p2-comparative-standard-root-upstream-retag-1-position)
- [2. Phase 6: Upstream Cross-Layer Retags (2,084 → 160)](#2-phase-6-upstream-cross-layer-retags-2084--160)
  - [2.1 Paradiso Read Series Retags (Cantos 1–33)](#21-paradiso-read-series-retags-cantos-133)
  - [2.2 Purgatorio Read Series Retags (Cantos 1–33)](#22-purgatorio-read-series-retags-cantos-133)
  - [2.3 Inferno Read Series Retags (Cantos 1–34)](#23-inferno-read-series-retags-cantos-134)
- [3. Phase 5: Foundational Cross-Layer Retags & Structural Sweeps (5,919 → 2,084)](#3-phase-5-foundational-cross-layer-retags--structural-sweeps-5919--2084)
  - [3.1 Phase 5 Upstream Retags (Phases 5r, 5p, 5n, 5i)](#31-phase-5-upstream-retags-phases-5r-5p-5n-5i)
  - [3.2 Corpus-Wide Structural Sweeps (Multiple `obj`, Subject Agreement, Speech Frames)](#32-corpus-wide-structural-sweeps-multiple-obj-subject-agreement-speech-frames)
  - [3.3 Pilot Build & Initial Layer-5 Grounding (Inferno 1)](#33-pilot-build--initial-layer-5-grounding-inferno-1)

---

## 1. Phase 7: Residue Closure & Manual Read Censuses (160 → 0)

Phase 7 systematically resolved the final 160 soft violations across the corpus through targeted manual read censuses, outlier audits, and upstream retags (see [`PHASE7.md`](PHASE7.md)).

### 1.1 §P15: Sixth Read Census & Final Residue Closure (38 positions → 0)

Investigated 2026-08-18 as the final Phase 7 census closing all remaining 38 soft violations across the corpus:

#### 1. Inferno (5 positions, −5 soft)
- [`skel/inferno/02.tsv`](inferno/02.tsv): `82.8 guardi` had `82.5 che` tagged as `subj` on 2sg verb. Corrected to `subj=(0,0), obl=(82,5)` (cleared `missing_arg: 82.8 obl (82, 5)`).
- [`skel/inferno/10.tsv`](inferno/10.tsv): `93.1 colui` copular root predicate omitted locative modifier `91.5 là`. Added `obl=(91,5)` (cleared `missing_arg: 93.1 obl (91, 5)`).
- [`skel/inferno/14.tsv`](inferno/14.tsv): `126.5 calando` omitted directional oblique `126.3 sinistra`. Added `obl:a=(126,3)` (cleared `missing_arg: 126.5 obl:a (126, 3)`).
- [`skel/inferno/22.tsv`](inferno/22.tsv): `103.5 son` in *per un ch'io son* omitted predicative relative `103.3 ch'`. Added `attr=(103,3)` (cleared `missing_arg: 103.5 xcomp (103, 3)`).
- [`skel/inferno/28.tsv`](inferno/28.tsv): `76.3 saper` cited NP head `76.6 miglior` as `obl:a` instead of dative pronoun `76.5 due`. Normalized to `iobj=(76,5)` (cleared `extra_arg: 76.3 obl:a (76, 6)`).

#### 2. Purgatorio (15 positions, −15 soft, including 1 Layer-4 retag)
- [`skel/purgatorio/01.tsv`](purgatorio/01.tsv): `102.1 porta` omitted locative adverb `100.3 intorno`. Added `obl=(100,3)` (cleared `missing_arg: 102.1 obl (100, 3)`). Standalone test fixture updated in `tests/fixtures/skel_fixtures.py`.
- [`skel/purgatorio/02.tsv`](purgatorio/02.tsv): `130.2 vid'` omitted comparative clause head `132.1 com'`. Added `obl=(132,1)` (cleared `missing_arg: 130.2 obl (132, 1)`).
- [`skel/purgatorio/04.tsv`](purgatorio/04.tsv): `73.7 vada` omitted second directional oblique `74.10 fianco`. Added `obl:da=(74,10)` (cleared `missing_arg: 73.7 obl:da (74, 10)`).
- [`skel/purgatorio/09.tsv`](purgatorio/09.tsv): `19.4 parea` omitted temporal head `13.3 ora`. Added `obl:in=(13,3)` (cleared `missing_arg: 19.4 obl:in (13, 3)`).
- [`skel/purgatorio/09.tsv`](purgatorio/09.tsv): `69.2 mosse` omitted directional modifier `69.6 rietro`. Added `obl:per=(69,6)` (cleared `missing_arg: 69.2 obl:per (69, 6)`).
- [`skel/purgatorio/13.tsv`](purgatorio/13.tsv): `133.9 tolti` omitted temporal modifier `134.3 tempo`. Added `obl=(134,3)` (cleared `missing_arg: 133.9 obl (134, 3)`).
- [`skel/purgatorio/14.tsv`](purgatorio/14.tsv): `37.6 fuga` omitted ablative relative `31.3 onde`. Added `obl:da=(31,3)` (cleared `missing_arg: 37.6 obl:da (31, 3)`).
- [`skel/purgatorio/19.tsv`](purgatorio/19.tsv): `67.3 fec'` omitted comparative standard `64.3 falcon`. Added `obl:quale=(64,3)` (cleared `missing_arg: 67.3 obl:quale (64, 3)`).
- **One Layer-4 Upstream Retag at purgatorio 20:93**: In *Veggio il novo Pilato sì crudele, che ciò nol sazia, ma sanza decreto portar nel Tempio le cupide vele*, `93.1 portar` was misattached `conj<-92.4 sazia` (causing `derive_unit` to inherit `92.2 ciò` as subject). Retagged `93.1 portar` as `xcomp<-91.1 Veggio` in [`dep/purgatorio/20.tsv`](../dep/purgatorio/20.tsv) (cleared `missing_arg: 93.1 subj (92, 2)`). See [`../dep/CORRECTIONS.md`](../dep/CORRECTIONS.md).
- [`skel/purgatorio/25.tsv`](purgatorio/25.tsv): `49.4 comincia` and `50.5 avviva` omitted coordinate subject `46.5 uno`. Added `subj=(46,5)` to both (cleared `missing_arg: 49.4 subj (46, 5)` and `missing_arg: 50.5 subj (46, 5)`).
- [`skel/purgatorio/26.tsv`](purgatorio/26.tsv): `32.4 basciarsi` in reciprocal *una con una* cited dependent token `32.7` with role `obl:con` instead of head `32.5 una` with `obl`. Normalized to `obl=(32,5)` (cleared `missing_arg: 32.4 obl (32, 5)`).
- [`skel/purgatorio/26.tsv`](purgatorio/26.tsv): `66.4 va` in pronominal verb *se ne va* omitted `66.3 ne`. Added `obl=(66,3)` and dropped duplicate `obl:a` (cleared `missing_arg: 66.4 obl (66, 3)`).
- [`skel/purgatorio/27.tsv`](purgatorio/27.tsv): `97.7 parea` omitted temporal head `94.3 ora`. Added `obl:in=(94,3)` (cleared `missing_arg: 97.7 obl:in (94, 3)`).
- [`skel/purgatorio/28.tsv`](purgatorio/28.tsv): `71.5 passò` omitted locative adverb `71.3 là`. Added `obl=(71,3)` (cleared `missing_arg: 71.5 obl (71, 3)`).

#### 3. Paradiso (18 positions, −18 soft)
- [`skel/paradiso/01.tsv`](paradiso/01.tsv): `79.1 parvemi` had partitive/prepositional complement `79.5 cielo` tagged as `subj`. Corrected to `subj=(0,0), obl:di=(79,5)` (cleared `missing_arg: 79.1 obl:di (79, 5)`).
- [`skel/paradiso/08.tsv`](paradiso/08.tsv): `12.4 vagheggia` omitted directional oblique `12.7 coppa`. Added `obl:da=(12,7)` (cleared `missing_arg: 12.4 obl:da (12, 7)`).
- [`skel/paradiso/11.tsv`](paradiso/11.tsv): `92.7 ebbe` omitted coordinate subject `88.4 viltà`. Added `subj=(88,4)` (cleared `missing_arg: 92.7 subj (88, 4)`).
- [`skel/paradiso/12.tsv`](paradiso/12.tsv): `10.3 volgon` omitted comparative oblique `14.2 guisa`. Added `obl:a=(14,2)` (cleared `missing_arg: 12.10 obl:a (14, 2)`).
- [`skel/paradiso/12.tsv`](paradiso/12.tsv): `124.3 fia` omitted coordinate subject `121.3 chi`. Added `subj=(121,3)` (cleared `missing_arg: 124.3 subj (121, 3)`).
- [`skel/paradiso/13.tsv`](paradiso/13.tsv): `44.6 infuso` omitted second locative oblique `40.3 quel`. Added `obl:in=(40,3)` (cleared `missing_arg: 13.44 obl:in (40, 3)`).
- [`skel/paradiso/14.tsv`](paradiso/14.tsv): `56.2 vinto` omitted comparative standard `52.4 carbon`. Added `obl=(52,4)` (cleared `missing_arg: 14.56 obl (52, 4)`).
- [`skel/paradiso/14.tsv`](paradiso/14.tsv): `96.3 dissi` cited speech object `96.5 Elïòs` as `ccomp` clause. Corrected to `obj=(96,5)` (cleared `missing_arg: 14.96 obj (96, 5)`).
- [`skel/paradiso/15.tsv`](paradiso/15.tsv): `32.2 rivolsi` omitted discourse oblique `31.3 lume`. Added `obl=(31,3)` (cleared `missing_arg: 15.32 obl (31, 3)`).
- [`skel/paradiso/16.tsv`](paradiso/16.tsv): `59.3 stata` had coordinate predicate `60.7 benigna` split as separate unit. Normalized `59.3` to include `attr=(60,3), attr=(60,7)` (cleared `missing_arg: 16.59 xcomp (60, 3)`).
- [`skel/paradiso/20.tsv`](paradiso/20.tsv): `35.8 scintilla` omitted dative clitic `35.7 mi`. Added `obl=(35,7)` (cleared `missing_arg: 20.35 obl (35, 7)`).
- [`skel/paradiso/23.tsv`](paradiso/23.tsv): `7.1 previene` omitted temporal oblique `3.2 notte`. Added `obl=(3,2)` (cleared `missing_arg: 23.7 obl (3, 2)`).
- [`skel/paradiso/25.tsv`](paradiso/25.tsv): `61.9 forti` had dative clitic `61.7 li` tagged as `subj`. Corrected to `subj=(0,0), iobj=(61,7)` (cleared `missing_arg: 25.61 obl:a (61, 7)`).
- [`skel/paradiso/26.tsv`](paradiso/26.tsv): `27.3 convien` omitted clausal subject `27.8 'mprenti`. Added `subj=(27,8)` (cleared `missing_arg: 26.27 subj (27, 8)`).
- [`skel/paradiso/26.tsv`](paradiso/26.tsv): `29.2 accende` omitted correlative oblique `28.5 quanto`. Added `obl:in=(28,5)` (cleared `missing_arg: 26.29 obl:in (28, 5)`).
- [`skel/paradiso/29.tsv`](paradiso/29.tsv): `35.3 strinse` had direct object `35.4 potenza` tagged as `subj`. Corrected to `subj=(0,0), obl=(35,4)` (cleared `missing_arg: 29.35 obl (35, 4)`).
- [`skel/paradiso/29.tsv`](paradiso/29.tsv): `137.7 recepe` omitted topical subject `136.3 luce`. Added `subj=(136,3)` (cleared `missing_arg: 29.137 subj (136, 3)`).
- [`skel/paradiso/30.tsv`](paradiso/30.tsv): `13.9 stinse` omitted adverbial modifier `13.2 poco`. Added `obl:a=(13,2)` (cleared `missing_arg: 30.13 obl:a (13, 2)`).

---

### 1.2 §P14: Fifth Read Census (`role_mismatch` and `extra_arg`, 31 units / 49 soft)

Investigated 2026-08-18 across 31 parse units covering all 22 `role_mismatch` positions and 14 `extra_arg` positions corpus-wide:

#### 1. Inferno (11 positions, −17 soft)
- [`skel/inferno/03.tsv`](inferno/03.tsv): `76.3 fier` copula with `subj=(76,6)` erroneously proposed as `subj=(0,0), obj=(76,6)`. Corrected to `subj=(76,6)`.
- [`skel/inferno/04.tsv`](inferno/04.tsv): `27.4 facevan` causative with 3pl `che` inverted with singular `l'aura` as `subj=(27,3), obj=(27,1)`. Corrected to `subj=(27,1), obj=(27,3)`.
- [`skel/inferno/05.tsv`](inferno/05.tsv): `92.2 pregheremmo` cited repeated pronoun `92.1 noi` instead of topic subject `90.1 noi`. Corrected subject citation.
- [`skel/inferno/09.tsv`](inferno/09.tsv): `20.5 incontra` cited `subj=(0,0), obj=(21,4)` instead of inverted subject `21.4 alcun`. Corrected to `subj=(21,4)`.
- [`skel/inferno/15.tsv`](inferno/15.tsv): `99.2 ascolta` cited `subj=(0,0), obj=(99,5)` instead of relative clause subject `99.5 chi`. Corrected to `subj=(99,5)`.
- [`skel/inferno/16.tsv`](inferno/16.tsv): `80.3 rispuoser` omitted speech object `81.1 felice`. Added `obj=(81,1)`.
- [`skel/inferno/17.tsv`](inferno/17.tsv): `11.1 avea` cited `11.7 pelle` as `subj` and omitted coordinate subject `10.2 faccia`. Corrected subject to `10.2` and added `obj=(11,7)`.
- [`skel/inferno/17.tsv`](inferno/17.tsv): `89.3 fé` inverted singular subject `89.2 vergogna` and plural object `89.7 minacce`. Corrected subject to `89.2` and object to `89.7`.
- [`skel/inferno/23.tsv`](inferno/23.tsv): `109.1 cominciai` omitted speech object `109.7 mali`. Added `obj=(109,7)`.
- [`skel/inferno/24.tsv`](inferno/24.tsv): `10.3 ritorna` and `10.6 lagna` cited pronoun `9.4 ei` instead of coordinated subject `7.2 villanello`. Corrected subject citations.
- [`skel/inferno/33.tsv`](inferno/33.tsv): `102.3 cessato` had `del mio viso stallo` marked as `obl:di=(102,6)` instead of `obj=(102,6)`. Fixed role to `obj`.
- [`skel/inferno/34.tsv`](inferno/34.tsv): `43.3 parea` had `tra bianca e gialla` marked as `attr=(43,6)` instead of `obl:tra=(43,6)`. Fixed role to `obl:tra`.

#### 2. Purgatorio (11 positions, −12 soft)
- [`skel/purgatorio/02.tsv`](purgatorio/02.tsv): `120.3 è` in copular question *Che è ciò* had inverted `subj=(120,4), attr=(120,2)`. Fixed to `subj=(120,2), attr=(120,4)`.
- [`skel/purgatorio/05.tsv`](purgatorio/05.tsv): `14.8 crolla` had `15.4 cima` as subject instead of `subj=(14,5) che, obj=(15,4) cima`. Corrected subject/object alignment.
- [`skel/purgatorio/08.tsv`](purgatorio/08.tsv): `80.2 accampa` had direct object `80.4 Melanesi` tagged as bare `obl`. Fixed role to `obj`.
- [`skel/purgatorio/11.tsv`](purgatorio/11.tsv): `139.1 parlo` had adverbial modifier `139.5 scuro` tagged as `attr=(139,5)`. Dropped spurious `attr` row.
- [`skel/purgatorio/15.tsv`](purgatorio/15.tsv): `39.4 cantato` cited `38.3 misericordes` as `subj` instead of `38.2 Beati` as `obj`. Corrected citation and role.
- [`skel/purgatorio/16.tsv`](purgatorio/16.tsv): `71.6 fora` had prepositional phrase `per ben letizia` tagged as `subj=(72,3)`. Corrected to `subj=(0,0), obl:per=(72,3)`.
- [`skel/purgatorio/21.tsv`](purgatorio/21.tsv): `123.6 pigli` had partitive subject `123.4 ammirazion` tagged as `obl:di=(123,4)`. Corrected to `subj=(123,4)`.
- [`skel/purgatorio/25.tsv`](purgatorio/25.tsv): `3.2 lasciato` in gapped coordination had `3.6 notte` tagged as `obj` instead of `subj`. Corrected role to `subj`.
- [`skel/purgatorio/25.tsv`](purgatorio/25.tsv): `122.3 udi'` had gerund `122.6 cantando` (`advcl`) tagged as `xcomp`. Dropped spurious `xcomp` row.
- [`skel/purgatorio/26.tsv`](purgatorio/26.tsv): `100.3 andai` had spurious duplicate `obl=(101,2)` attached to matrix verb instead of gerund `rimirando`. Dropped duplicate `obl` row.
- [`skel/purgatorio/28.tsv`](purgatorio/28.tsv): `108.6 sonar` had causee object `108.5 selva` tagged as `subj`. Fixed role to `obj`.
- [`skel/purgatorio/30.tsv`](purgatorio/30.tsv): `120.2 ha` had partitive quantifier `120.4 più` omitted and modifier `120.7 vigor` tagged as `obl:di`. Corrected to `obj=(120,4)`.

#### 3. Paradiso (9 positions, −20 soft)
- [`skel/paradiso/01.tsv`](paradiso/01.tsv): `61.2 parve` had auxiliary `62.1 essere` as `subj` instead of `subj=(58,1), xcomp=(62,2)`. Corrected to `subj=(58,1), attr=(62,2)`.
- [`skel/paradiso/01.tsv`](paradiso/01.tsv): `81.3 fece` omitted `obj=(81,1) lago` and had spurious subject on `81.6 disteso`. Corrected to `obj=(81,1), attr=(81,6)`.
- [`skel/paradiso/01.tsv`](paradiso/01.tsv): `97.2 requïevi` had adverbial adjective `97.4 contento` tagged as `attr=(97,4)`. Dropped spurious `attr` row.
- [`skel/paradiso/04.tsv`](paradiso/04.tsv): `30.2 dico` omitted speech object `30.7 Maria`. Added `obj=(30,7)`.
- [`skel/paradiso/04.tsv`](paradiso/04.tsv): `107.4 fanno` had consecutive adverbial clause `108.6 posson` (`sì che...`) tagged as `ccomp`. Dropped spurious `ccomp` row.
- [`skel/paradiso/12.tsv`](paradiso/12.tsv): `27.4 chiudere` had subject `26.4 occhi` tagged as `obj`. Fixed role to `subj`.
- [`skel/paradiso/12.tsv`](paradiso/12.tsv): `30.3 parer` had object `29.6 ago` tagged as `subj`. Fixed role to `obj`.
- [`skel/paradiso/14.tsv`](paradiso/14.tsv): `92.7 conobbi` had accusative+infinitive complement tagged as `obj=(93,2)` instead of `xcomp=(93,1)`. Fixed role to `xcomp`.
- [`skel/paradiso/15.tsv`](paradiso/15.tsv): `102.3 veder` had comparative standard `102.8 persona` tagged as `obj` instead of `obl:che`. Fixed role to `obl:che`.
- [`skel/paradiso/19.tsv`](paradiso/19.tsv): `63.4 cela` had nominalized infinitive subject `63.6 esser` tagged as `obj`. Fixed role to `subj`.
- [`skel/paradiso/21.tsv`](paradiso/21.tsv): `28.3 traluce` had `28.7 raggio` as `obl:in` and pro-drop `subj=(0,0)` instead of `subj=(28,7), obl:in=(28,6)`. Corrected subject and oblique.
- [`skel/paradiso/32.tsv`](paradiso/32.tsv): `150.3 parti` had object `150.7 cor` tagged as `subj`. Fixed role to `obj`.
- [`skel/paradiso/33.tsv`](paradiso/33.tsv): `96.1 fé` had dative causee `96.3 Nettuno` tagged as `obj` instead of `iobj`. Fixed role to `iobj`.

---

### 1.3 §P13: Fourth Read Census (Clausal Arguments, 4 positions)

Investigated 2026-08-18 across standing `extra_arg` positions in Inferno and Purgatorio. Dropped spurious clause arguments (adverbial / paratactic clauses misregistered as complement clauses):

1. [`skel/inferno/08.tsv`](inferno/08.tsv): `81.2 gridò` in *«Usciteci», gridò: «qui è l'intrata»* had paratactic second direct speech clause *qui è l'intrata* registered as a second `ccomp`. Dropped `81 2 gridò ccomp 81 4` and spurious `è obl` row (cleared `extra_arg: 81.2 ccomp (81, 4)`).
2. [`skel/inferno/22.tsv`](inferno/22.tsv): `84.2 fé` in consecutive construction *e fé sì lor, che ciascun se ne loda* had consecutive adverbial clause `84.9 loda` registered as `ccomp`. Dropped `84 2 fé ccomp 84 9` and normalized `loda` arguments (cleared `extra_arg: 84.2 ccomp (84, 9)`).
3. [`skel/purgatorio/09.tsv`](purgatorio/09.tsv): `72.3 maravigliar` in conditional construction *non ti maravigliar s'io la rincalzo* had conditional clause `72.7 rincalzo` registered as `ccomp`. Dropped `72 3 maravigliar ccomp 72 7` (cleared `extra_arg: 72.3 ccomp (72, 7)`).
4. [`skel/purgatorio/05.tsv`](purgatorio/05.tsv): `48.1 venian` in *venian gridando* had circumstantial gerund `48.2 gridando` (`advcl`) registered as `xcomp`. Dropped `48 1 venian xcomp 48 2` and spurious adverb row (cleared `extra_arg: 48.1 xcomp (48, 2)`).

---

### 1.4 §P12: Third Read Census (Paradiso Positions, 4 positions)

Investigated 2026-08-18 across standing `extra_arg` and `missing_arg` positions in Paradiso. Dropped spurious rows, supplied missing arguments, and normalized predications across 4 positions:

1. [`skel/paradiso/12.tsv`](paradiso/12.tsv): `93.4 sunt` in Latin genitive of possession *non decimas, quae sunt pauperum Dei* had spurious `obl:di=(93,5)` (`pauperum`). Dropped `93 4 sunt obl:di 93 5` (cleared `extra_arg: 93.4 obl:di (93, 5)`).
2. [`skel/paradiso/28.tsv`](paradiso/28.tsv): `20.3 locata` in *parrebbe luna, locata con esso* had complement noun `luna` cited as its subject and as a non-derived predicate. Dropped `20 2 luna` predicate and `20 3 locata subj 20 2` (cleared `extra_arg: 20.3 subj (20, 2)`).
3. [`skel/paradiso/11.tsv`](paradiso/11.tsv): `21.6 apprendo` in *li tuoi pensieri onde cagioni apprendo* cited case marker `21.4 onde` as `obl:di` token instead of head noun `21.3 pensieri` with role `obl:onde`. Fixed to `obl:onde=(21,3)` (cleared `missing_arg: 21.6 obl:onde (21, 3)` and `extra_arg: 21.6 obl:di (21, 4)`, −2 soft).
4. [`skel/paradiso/21.tsv`](paradiso/21.tsv): `5.5 faresti` in correlative comparison *tu ti faresti quale fu Semelè…* had `5.6 quale` cited as `attr` and as a separate predicate. Dropped `5 5 faresti attr 5 6` and `5 6 quale` predicate (cleared `extra_arg: 5.5 xcomp (5, 6)`).

---

### 1.5 §P11: Second Read Census (Spurious Arguments, 7 positions)

Investigated 2026-08-18 across standing `extra_arg` and `missing_arg` positions:

1. [`skel/inferno/08.tsv`](inferno/08.tsv): `93.4 iscorta` in *che li ha' iscorta sì buia contrada* had direct object mistagged as `iobj` and missed the actual object `obj=(93,7)` (`contrada`). Added `obj=(93,7)` and changed `obj=(93,2)` to `iobj` (cleared `missing_arg: 93.4 obj (93, 7)`).
2. [`skel/inferno/32.tsv`](inferno/32.tsv): `7.6 pigliare` in *da pigliare a gabbo* (modifying noun *impresa*) had spurious object `obj=(7,4)` (`impresa`). Dropped `7 6 pigliare obj 7 4` (cleared `extra_arg: 7.6 obj (7, 4)`).
3. [`skel/inferno/16.tsv`](inferno/16.tsv): `94.5 ha` in *fiume c'ha proprio cammino* cited antecedent `fiume` as subject instead of relative pronoun `94.4 c'`. Fixed subject to `94.4` and dropped spurious `obl` row (cleared `extra_arg: 94.5 subj (94, 3)`).
4. [`skel/purgatorio/27.tsv`](purgatorio/27.tsv): `10.9 morde` in *se pria non morde, anime sante, il foco* had vocative addressee `anime sante` cited as direct object. Dropped `10 9 morde obj 11 1` (cleared `extra_arg: 10.9 obj (11, 1)`).
5. [`skel/purgatorio/24.tsv`](purgatorio/24.tsv): `107.4 so` in idiom *non so che* had spurious object `obj=(107,5)` (`che`). Dropped `107 4 so obj 107 5` (cleared `extra_arg: 107.4 obj (107, 5)`).
6. [`skel/purgatorio/10.tsv`](purgatorio/10.tsv): `30.5 aveva` in *che dritto di salita aveva manco* had adverbial modifier `manco` cited as object instead of `30.2 dritto`. Fixed `obj=(30,2)` (cleared `missing_arg: 30.5 obj (30, 2)` and `extra_arg: 30.5 obj (30, 6)`, −2 soft).
7. [`skel/purgatorio/15.tsv`](purgatorio/15.tsv): `32.6 fieti` in *ma fieti diletto quanto natura…* had adverbial `quanto` cited as subject and `diletto` as `attr` and predicate. Normalized `fieti` to `subj=(32,7)` (`diletto`) and dropped non-predicate `32.7 diletto` rows (cleared `extra_arg: 32.6 subj (33, 1)`).

---

### 1.6 §P10: First Read Census (Spurious Arguments & Layer-4 Retag, 7 positions)

Investigated 2026-08-18 across standing `extra_arg` positions:

1. **One Layer-4 Retag at paradiso 7:25**: Retagged `25.6 virtù` as `obl<-25.3 soffrire` in [`dep/paradiso/07.tsv`](../dep/paradiso/07.tsv) (cleared `extra_arg: 25.3 obl:a (25, 6)`).
2. [`skel/purgatorio/30.tsv`](purgatorio/30.tsv): `59.1 viene` in *viene a veder … e a ben far l'incora* had spurious duplicate `xcomp=(60,8)` (`far`). Dropped `59 1 viene xcomp 60 8` (cleared `extra_arg: 59.1 xcomp (60, 8)`).
3. [`skel/purgatorio/10.tsv`](purgatorio/10.tsv): `60.2 dir` in *faceva dir l'un 'No', l'altro 'Sì, canta'* had pseudo-predicative `attr` rows for 'Sì' and 'canta'. Dropped `attr 60 8`, `attr 60 9`, and orphan `60.9 canta` predicate, normalizing `dir` to `obj 60 5` ('No') (cleared `extra_arg: 60.2 xcomp (60, 8)` and `extra_arg: 60.2 xcomp (60, 9)`).
4. [`skel/paradiso/07.tsv`](paradiso/07.tsv): `25.8 vole` in *virtù che vole* had spurious direct object `obj=(26,1)` (`freno`, which belongs to `soffrire`). Dropped `25 8 vole obj 26 1` (cleared `extra_arg: 25.8 obj (26, 1)`).
5. [`skel/paradiso/14.tsv`](paradiso/14.tsv): `136.8 accuso` in *di quel ch'io m'accuso* had duplicate object `obj=(136,5)` (`che`) alongside reflexive `obj=(136,7)` (`m'`). Dropped `136 8 accuso obj 136 5` (cleared `extra_arg: 136.8 obj (136, 5)`).
6. [`skel/paradiso/17.tsv`](paradiso/17.tsv): `116.8 ridico` in *quel che s'io ridico, a molti fia sapor* had spurious object `obj=(116,5)` (`che`, which is subject of `fia`). Dropped `116 8 ridico obj 116 5` (cleared `extra_arg: 116.8 obj (116, 5)`).
7. [`skel/paradiso/03.tsv`](paradiso/03.tsv): `59.4 so` in idiom *non so che divino* had spurious object `obj=(59,6)` (`divino`). Dropped `59 4 so obj 59 6` (cleared `extra_arg: 59.4 obj (59, 6)`).

---

### 1.7 §P9: Round 10 Log Audits & Driver Fallback (3 drops + 1 Layer-4 retag)

Investigated 2026-08-18 from Round 10's `--log` outputs:

1. **One Layer-4 Upstream Retag at paradiso 11:127**: Retagged `127.5 pecore` as `nsubj<-129.2 tornano` in [`dep/paradiso/11.tsv`](../dep/paradiso/11.tsv).
2. [`skel/inferno/16.tsv`](inferno/16.tsv): `21.1 fenno: subj=(19,5), subj=(21,8), obj=(21,3)`. Dropped duplicate subject row `21 1 fenno subj 21 8` (cleared `extra_arg: 21.1 subj (21, 5)`).
3. [`skel/inferno/29.tsv`](inferno/29.tsv): `63.5 hanno` in parenthetical *secondo che i poeti hanno per fermo* had spurious `ccomp=(64,2)`. Dropped `63 5 hanno ccomp 64 2` (cleared `extra_arg: 63.5 ccomp (62, 1)`).
4. [`skel/purgatorio/32.tsv`](purgatorio/32.tsv): `69.3 vuol` in *qual vuol sia che l'assonnar ben finga* had spurious `ccomp=(69,4)`. Dropped `69 3 vuol ccomp 69 4` (cleared `extra_arg: 69.3 ccomp (68, 1)`).

---

### 1.8 §P7: Structural Outlier Resolutions (7 positions)

Investigated 2026-08-18 as Phase 7 outlier census. All 7 positions resolved cleanly:

1. **`extra_tuple` (3 positions)**:
   - [`skel/inferno/30.tsv`](inferno/30.tsv): `59.5 perché: subj=(0,0)` was proposed on an interrogative adverb. Dropped spurious predicate.
   - [`skel/purgatorio/09.tsv`](purgatorio/09.tsv): `58.7 forme: subj=(58,6)` was proposed on an attributive adjective (`amod`). Dropped spurious predicate.
   - [`skel/purgatorio/16.tsv`](purgatorio/16.tsv): `120.7 appressarsi: subj=(0,0)` was proposed on a coordinate nominalized infinitive without dependents. Dropped spurious predicate.
2. **`missing_tuple` (2 positions)**:
   - [`skel/purgatorio/31.tsv`](purgatorio/31.tsv): Copular nominal predicate `15.5 mestier: subj=(15,7)` was omitted in artifact, and `intender` role was mistagged. Added `mestier` and fixed `intender: obj=(15,2)`.
   - [`skel/paradiso/22.tsv`](paradiso/22.tsv): Conditional verb `21.7 redui: subj=(0,0), obj=(21,6)` was omitted in artifact. Added `redui`.
3. **`argument ... heads no NP/pronoun/predicate` (2 positions)**:
   - [`skel/purgatorio/12.tsv`](purgatorio/12.tsv): Adverb `24.1 quanto` was cited as subject of `avanza`. Replaced with pro-drop `subj=(0,0)`.
   - [`skel/paradiso/21.tsv`](paradiso/21.tsv): Article `54.5 'l` was cited as object of nominalized infinitive `chieder`. Dropped spurious `chieder` predicate.

---

### 1.9 §P6: Final `dual_role` Contradictions (3 positions)

Investigated per Phase 7 Work Queue. The 3 standing artifact-internal contradictions reported by rule EG were resolved by dropping the duplicate contradictory rows:

- [`skel/paradiso/23.tsv`](paradiso/23.tsv): `107.7 dia` had both `subj` and `obj` on `(108, 3) spera`. Dropped duplicate `subj` row.
- [`skel/paradiso/29.tsv`](paradiso/29.tsv): `105.4 gridan` had both `subj` and `obj` on `(104, 4) favole` (passive `si` construction). Dropped duplicate `subj` row.
- [`skel/paradiso/31.tsv`](paradiso/31.tsv): `124.6 aspetta` had both `subj` and `obj` on `(124, 8) temo` (passive `si` construction). Dropped duplicate `subj` row.

---

### 1.10 §P5: Verbless Speech Introductions (`missing_tuple_nominal`, 8 positions)

Verbless speech introductions (`«E io: "Maestro, …"»`, `«per ch'io: "…"»`, `«ond' io: "…"»`) where Layer 4 has `io` as root of an elided speech clause were standardized to `io: subj=(0,0), ccomp=(...)`:

- [`skel/inferno/07.tsv`](inferno/07.tsv) (`49.2 io: subj=(0,0), ccomp=(50,4)`)
- [`skel/inferno/08.tsv`](inferno/08.tsv) (`52.2 io: subj=(0,0), ccomp=(52,6)`)
- [`skel/inferno/08.tsv`](inferno/08.tsv) (`70.2 io: subj=(0,0), ccomp=(71,7)`)
- [`skel/inferno/10.tsv`](inferno/10.tsv) (`19.2 io: subj=(0,0), ccomp=(19,6)`)
- [`skel/inferno/11.tsv`](inferno/11.tsv) (`67.2 io: subj=(0,0), ccomp=(67,6)`)
- [`skel/inferno/24.tsv`](inferno/24.tsv) (`72.3 io: subj=(0,0), ccomp=(72,5)`)
- [`skel/inferno/31.tsv`](inferno/31.tsv) (`21.2 io: subj=(0,0), ccomp=(21,4)`)
- [`skel/purgatorio/06.tsv`](purgatorio/06.tsv) (`49.2 io: subj=(0,0), ccomp=(49,4)`)

---

### 1.11 §P4: Refusal Census Upstream Retags (2 positions)

Audited 38 refused positions across `extra_arg`, `extra_arg_subject`, and `missing_arg` with `skel/read.py`:

- **[`dep/inferno/02.tsv`](../dep/inferno/02.tsv) (2:60)**: `durerà quanto 'l mondo lontana`. Retagged `60.5 mondo` from `nsubj` to adverbial nominal `obl` (−2 soft: `extra_arg: 60.2 subj` and `role_mismatch: 60.2 arg`).
- **[`dep/purgatorio/14.tsv`](../dep/purgatorio/14.tsv) (14:60)**: `sgomenta`. Corrected attachment from `veggio` (1sg) to `diventa` (3sg) (−1 soft).

---

### 1.12 §P2: Comparative Standard Root Upstream Retag (1 position)

- **[`dep/purgatorio/09.tsv`](../dep/purgatorio/09.tsv) (9:97)**: *«Era il secondo tinto più che perso»*. Layer 4 made `perso` the root with `tinto` as its `nsubj`. Retagged `97.4 tinto` as `root` and `97.7 perso` as `advmod<-97.5 più` to align with copular precedent (*Inferno* 7:103).

---

## 2. Phase 6: Upstream Cross-Layer Retags (2,084 → 160)

During the 19 per-position read batches across all 100 cantos, over 200 upstream defects in Layer 4 (`dep/`), Layer 2 (`morph/`), Layer 3 (`np/`), and `case/` were identified and corrected.

### 2.1 Paradiso Read Series Retags (Cantos 1–33)

- **Paradiso 26–33 (2026-08-17)**:
  - `dep/`: 16 rows corrected across 11 places (26:56 `cor` `nsubj`, 31:116 `regina` `nsubj`, 28:13 `furon tocchi` passive periphrasis, 28:106 `dei saper` modal, 29:112 `quel` `nsubj`, 29:138/30:127 `quanti`/`qual` `xcomp`, 30:35 `che`/`quel` comparative standard, 31:20 `moltitudine` `nmod`, 32:128 `sposa` `nmod`, 33:63 `dolce` `nsubj`).
  - `morph/`: 6 rows corrected (26:79 `mei` adverb, 28:13 `tocchi` verb, 28:106 `dei` verb, etc.).
  - `np/`: 4 spans adjusted (28:13 `[tocchi]` dropped, 28:106 `[saper...]` dropped, 29:112 `[quel tanto]` -> `[quel]`, 33:21 `[quantunque...]` expanded).
  - `case/`: 2 rows dropped (26:79 `mei`, 26:79 `che`).
- **Paradiso 21–25 (2026-08-17)**:
  - `dep/`: 10 rows corrected across 5 places (21:28 `che` `obl`, 21:105 `chi` `obj`, 23:17 `attender` `obl`, 24:19 `quella`/`carezza` nested PPs, 24:147 `scintilla` `conj`).
  - `morph/`: 1 row (21:28 `che` relative pronoun).
  - `np/`: 1 span dropped (21:28 `[che raggio]`).
- **Paradiso 11–20 (2026-08-17)**:
  - `dep/`: 9 rows corrected across 9 places (11:92 `intenzione` `obj`, 12:38 `caro` `advmod`, 13:131 `quei` `nsubj`, 14:134 `suso` `advmod`, 15:12 `amor` `obj`, 15:51 `bianco` `nsubj`, 15:56 `quel` `obl`, 16:72 `spade` `nsubj`, 19:95 `imagine` `nsubj`).
  - `morph/`: 1 row (14:93 `esso` demonstrative).
- **Paradiso 6–10 (2026-08-17)**:
  - `dep/`: 10 rows corrected across 5 places (7:74-75 `ne`/`somigliante`/`ardor`, 7:142-143 `vita`/`beninanza`, 9:87 `far suole` modal, 9:135 `a' lor vivagni`, 10:147 `pò` `acl:relcl`).
  - `morph/`: 2 rows (9:135 `lor` `det:poss`, 10:147 `ch'` pronoun).
  - `case/`: 2 rows (9:135 `lor` dropped, 10:147 `ch'` added `nominative`).
- **Paradiso 1–5 (2026-08-17)**:
  - `dep/`: 6 rows corrected across 5 places (1:81 `lago` `obj`, 1:90 `che` `obj`, 2:45 `guisa` `obl`, 3:95 `qual` `xcomp`, 5:120 `noi` `obl`).
  - `morph/`: 1 row (5:37 `convienti` `verb+pronoun`).
  - `np/`: 1 clitic mention added (5:37 `+ti`).
  - `case/`: 2 rows (1:90 `che` `accusative`, 5:37 `convienti` `dative`).

### 2.2 Purgatorio Read Series Retags (Cantos 1–33)

- **Purgatorio 31–33 (2026-08-17)**:
  - `dep/`: 4 rows corrected (31:15 `fuor mestier` copula, 32:67 `come pintor` simile attachment, 33:18 `mi` dative of possession, 33:109 `donne`/`fin` subject/locative).
  - `morph/`: 1 row (31:15 `fuor` = *furono* verb).
  - `np/`: 2 spans adjusted (inferno 18:30 outer span dropped, purgatorio 33:26 `[suo maggior]` head fixed).
  - `case/`: 2 rows (31:15 `quale` `accusative`, 33:18 `mi` `dative`).
- **Purgatorio 21–25 (2026-08-16)**:
  - `dep/`: 27 rows corrected (11 copular predicate nominals of `essere` normalized to `attr`; 6 pronominal clitics retagged from `nsubj` to `expl`; 9 rows from read including 22:17 `persona`, 22:26 `a riso`, 24:71 `compagni`, 25:67 `petto`).
  - `morph/`: 2 rows (22:26 `riso` noun, etc.).
- **Purgatorio 16–20 (2026-08-16)**:
  - `dep/`: 17 rows corrected (16:43 `anzi la morte` PP, 16:64 `sospir` `obj`, 16:98-99 `però che`, 16:129 `brutta` transitive objects, 17:111 `da quello odiare`, 18:50 `unita` participial predicate, 18:117 `nostra`, 18:140 `che` `mark`).
  - `morph/`: 2 rows (16:129 `brutta` verb *bruttare*, etc.).
  - `np/`: 1 span adjusted (18:117 `[nostra giustizia]`).
  - `case/`: 2 rows (16:129 `sé` `accusative`, 17:111 `quello` `accusative`).
- **Purgatorio 11–15 (2026-08-16)**:
  - `dep/`: 11 rows corrected (including 14:75 coordinate subject agreement, 14:69).
  - `morph/`: 8 rows corrected (14:69 `che` conjunction, 14:69 `parte` noun, 14:90 `reda` noun, etc.).
  - `np/`: 2 spans adjusted (14:69 `[qual che parte]`, 14:90 `[reda]`).
  - `case/`: 1 row dropped (14:69 `che`).
- **Purgatorio 6–10 (2026-08-16)**:
  - `dep/`: 1 row corrected (9:58 `forme`).
  - `morph/`: 1 row corrected.
- **Purgatorio 1–5 (2026-08-16)**:
  - `dep/`: 2 rows corrected (5:135 `colui` postposed subject).
  - `case/`: 1 row (5:135 `colui` `nominative`).

### 2.3 Inferno Read Series Retags (Cantos 1–34)

- **Inferno 31–34 (2026-08-16)**:
  - `dep/`: 15 rows corrected (31:143 `con esso` multiword preposition normalization, 34:105 `il sol tragitto`).
  - `morph/`: 2 rows corrected.
  - `np/`: 1 span split (34:105 `[il sol]` and `[tragitto]`).
  - `case/`: 1 row.
- **Inferno 26–30 (2026-08-15)**:
  - `dep/`: 10 rows corrected.
  - `morph/`: 1 row (29:83 `scardova` noun).
- **Inferno 21–25 (2026-08-15)**:
  - `dep/`: 20 rows corrected (coordinate subject attachments, perception verb objects).
  - `morph/`: 5 rows corrected.
- **Inferno 16–20 (2026-08-15)**:
  - `dep/`: 25 rows corrected (reflexive clitics tagged `nsubj` retagged in 15 places, 17:103 `obj`, 17:48 `advcl`, 18:122 `obl`, 16:95-96 river course).
  - `morph/`: 1 row (16:94 `c'` relative pronoun *che*).
- **Inferno 11–15 (2026-08-15)**:
  - `dep/`: 16 rows corrected (12:1-3/13:141 predicative adjectives `amod` -> `attr`, 14:44/14:103 multiword prepositions `fuor che`/`Dentro dal`, 11:70 left-dislocated topic, 14:116 `obj`, 19:106 apposition).
  - `morph/`: 2 rows (12:90 `fuia` adjective, 15:99 `ascolta` 3sg indicative).
- **Inferno 7–10 (2026-08-14)**:
  - `dep/`: 9 rows corrected (8:78, 9:41 ×3, 9:72, 9:103, 10:23, 10:85, 10:87).
  - `morph/`: 5 rows (7:38-39 `fuor`/`cherci`/`chercuti`, 8:71 `entro`, 10:23 `ten` clitic cluster `te+ne`).
  - `np/`: 1 clitic cluster enumerated (10:23 `[+te]` and `[+ne]`).
- **Inferno 4–6 (2026-08-13)**:
  - `morph/`: 1 row (6:54 `fiacco` 1sg verb).
- **Inferno 1–3 (2026-08-12)**:
  - `dep/`: 11 rows corrected (including 3:13 elided speech frame).
  - `morph/`: 4 rows.
  - `case/`: 1 row.

---

## 3. Phase 5: Foundational Cross-Layer Retags & Structural Sweeps (5,919 → 2,084)

### 3.1 Phase 5 Upstream Retags (Phases 5r, 5p, 5n, 5i)

- **Phase 5r (Case Annex Reconciliation, 2026-08-03)**:
  - Audited 17 mirror candidates between `case/` and `dep/`: 10 `dep/` retags (clitics, causative *fare*), 4 `case/` corrections, 8 verified structural exceptions.
- **Phase 5p (Clausal Complements, 2026-07-28)**:
  - Retagged 6 clausal complements in `dep/` attached as `advcl` where the subordinate clause was a true complement.
- **Phase 5n (`mark` Bucket Audit, 2026-07-28)**:
  - Retagged 22 relative/interrogative pronouns filling core argument slots off `mark` in `dep/` (e.g., `quantunque`, `che`, `qual`).
- **Phase 5i (Double-`obj` Clitics, 2026-07-28)**:
  - Audited 30 predicates with multiple `obj` tokens in `dep/`; retagged 26 double-`obj` clitics to `iobj` (22) or `obl` (4 partitive `ne`).

---

### 3.2 Corpus-Wide Structural Sweeps (Multiple `obj`, Subject Agreement, Speech Frames)

- **Multiple `obj` Normalization (2026-08-03, +80 net)**:
  - Flagged 203 predicates in `dep/` carrying >1 direct object.
  - Corrected all 203 across 316 row edits in `dep/`: 88 `conj` coordinations, 63 secondary predicates relabeled `attr`, 22 reflexive `expl`, 27 partitive/locative `obl`, 9 clitic `iobj`, 14 gapping `orphan`.
- **Subject-Agreement Sweep (2026-08-07, +55 net)**:
  - Applied Layer 4 finite verb person/number agreement checks.
  - Corrected 155 upstream rows: 77 Layer-2 `morph/` rows and 424 Layer-4 `dep/` rows across 66 cantos.
- **Speech Frame Promotion (2026-08-07, +105 net)**:
  - Normalized 99 elided speech frames (*"Ed elli a me: «…»"*) across all three canticles to Universal Dependencies ellipsis promotion conventions.

---

### 3.3 Pilot Build & Initial Layer-5 Grounding (Inferno 1)

- **Fused Enclitic Self-Citation Guard (2026-07-13)**:
  - Fixed hard retry failure at Inferno 1:59 (`venendomi`) by prohibiting self-citation of enclitic verb tokens.
- **Elliptical Predicate Nominals**:
  - Identified and verified verbless predicate nominals (*"mantoani per patrïa ambedui"*, *"Non omo, omo già fui"*).
- **NP Membership Hardening**:
  - Extended membership check to accept relative pronoun forms (`che`/`ch'`/`cui`/`qual`/`chi`) regardless of POS tagging drift, and adverbial obliques (`quivi`, `là`, `sù`, `dietro`).
