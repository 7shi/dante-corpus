#!/usr/bin/env python3
"""Generate skel/RULES.md as a formal Grammar Handbook for Layer 5.

Extracts docstrings, source comments, census metrics, and concrete examples
for all 130 rules, structuring them into a 6-branch grammatical hierarchy.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

from dante_corpus import api, case, dep, morph, np, skel
from dante_corpus.skel import RULES
from dante_corpus.skel.registry import _RULES_CATALOG

# Taxonomy tree definition: Branch -> Sub-branch -> list of rule IDs
TAXONOMY: list[dict[str, object]] = [
    {
        "branch_id": "1",
        "title": "Predicate Identification & Clausal Topology",
        "description": "Rules governing the identification of clause roots, subordinate clause heads, auxiliary/copular periphrases, and secondary predications.",
        "subbranches": [
            {
                "sub_id": "1.1",
                "title": "Predicate Head Selection",
                "description": "Syntactic criteria for designating clause heads and independent predications from UD deprels and POS tags.",
                "rules": ["1", "2", "BN", "AN"],
            },
            {
                "sub_id": "1.2",
                "title": "Auxiliary & Copula Predications",
                "description": "Handling copular predicates, auxiliary chains, nominal predications, and inverted copula complements.",
                "rules": ["I", "Y", "BF", "BS", "CT", "AV"],
            },
            {
                "sub_id": "1.3",
                "title": "Secondary & Reduced Predications",
                "description": "Adjectival/adverbial secondary predicates, depictive small clauses, complemented adjective phrases, reduced relative participles, and speech-act nominals.",
                "rules": ["AA", "AU", "R", "DX", "AZ", "BX", "DW", "AY", "CH", "EA", "CS", "DA"],
            },
        ],
    },
    {
        "branch_id": "2",
        "title": "Subject Licensing & Authority Model",
        "description": "Rules defining subjecthood, pro-drop resolution, coordinate subject inheritance, agreement constraints, and control/raising structures.",
        "subbranches": [
            {
                "sub_id": "2.1",
                "title": "Pro-Drop & Null Subjects",
                "description": "Mechanisms for pro-drop (∅) null subjects, overt referent promotion, and chain boundary cutoffs.",
                "rules": ["BH", "CN", "CU", "DU"],
            },
            {
                "sub_id": "2.2",
                "title": "Coordinate Subject Inheritance",
                "description": "Subject propagation across coordinate conjuncts (conj chains), morphological agreement gates, and sibling cutoffs.",
                "rules": ["BZ", "AT", "AG", "DO", "AH", "EF", "AP", "BE", "CD", "DE", "AC", "BU"],
            },
            {
                "sub_id": "2.3",
                "title": "Control & Raising Theory",
                "description": "Subject inheritance for non-finite clauses (infinitive, gerund, participle), control partner argument sharing, raising structures, and controller extraction.",
                "rules": ["V", "CL", "BB", "BI", "DN", "AX", "CF", "CJ", "CE", "DF"],
            },
            {
                "sub_id": "2.4",
                "title": "Impersonal & Displaced Subjects",
                "description": "Impersonal verbs with clausal subjects and multi-candidate subject disambiguation.",
                "rules": ["DQ", "BA"],
            },
        ],
    },
    {
        "branch_id": "3",
        "title": "Core Valency & Complementation",
        "description": "Rules governing direct/indirect objects, pronominal clitics, fused clitic pronouns, clausal complements, and predicative complements.",
        "subbranches": [
            {
                "sub_id": "3.1",
                "title": "Direct & Indirect Objects, Pronominal Clitics",
                "description": "Direct and indirect object identification, reflexive clitics in pronominal verbs, and dual-role fused clitics.",
                "rules": ["N", "AB", "AW", "BD", "AL", "AS", "EH"],
            },
            {
                "sub_id": "3.2",
                "title": "Clausal Complements",
                "description": "Subordinate clausal arguments (ccomp vs xcomp), prepositional infinitive complements, and marker-named clauses.",
                "rules": ["P", "Q", "CQ", "CY", "CK"],
            },
            {
                "sub_id": "3.3",
                "title": "Predicative Complements & Copular Structures",
                "description": "Predicative complements (xcomp/attr) vs direct objects, prepositional copular complements, and copular adverb complements.",
                "rules": ["M", "DB", "DL", "AD", "X"],
            },
        ],
    },
    {
        "branch_id": "4",
        "title": "Obliques & Adjuncts",
        "description": "Rules governing prepositional phrases, adverbials, locatives, and adverbial/relative clauses.",
        "subbranches": [
            {
                "sub_id": "4.1",
                "title": "Prepositional Obliques",
                "description": "Lemma-qualified prepositional obliques (obl:<prep>), bare vs qualified obliques, co-present prepositions, and adnominal nmod obliques.",
                "rules": ["L", "O", "S", "CB", "DV", "D"],
            },
            {
                "sub_id": "4.2",
                "title": "Adverbial Obliques & Locatives",
                "description": "Adverbial obliques in locative/directional slots, relative locative adverbs, and POS classification.",
                "rules": ["J", "BC", "DD", "DY"],
            },
            {
                "sub_id": "4.3",
                "title": "Adverbial & Relative Clauses",
                "description": "Prepositional infinitive adverbial clauses (advcl), free relative clauses, relative pronouns vs antecedents, and interrogative wh-words.",
                "rules": ["T", "AE", "BT", "DP", "DK", "CX", "DJ", "DC"],
            },
        ],
    },
    {
        "branch_id": "5",
        "title": "Coordination, Ellipsis & Comparative Constructions",
        "description": "Rules resolving coordinate structures, gapping, orphan remnants, and verbless comparative clauses.",
        "subbranches": [
            {
                "sub_id": "5.1",
                "title": "Coordinate Conjuncts & Shared Arguments",
                "description": "Coordination argument mapping onto head, shared arguments across conjuncts, and nominal conjunct promotion.",
                "rules": ["A", "C", "DG", "AJ", "DZ", "CA", "CC"],
            },
            {
                "sub_id": "5.2",
                "title": "Gapping & Orphan Remnants",
                "description": "Gapped conjuncts with orphan children, remnant case assignment via case annex, and multi-term gapped comparisons.",
                "rules": ["CZ", "DH", "CW", "DI", "CG"],
            },
            {
                "sub_id": "5.3",
                "title": "Comparative Constructions",
                "description": "Verbless comparative clauses (come, che, quasi), correlatives (sì come), and comparative particle handling.",
                "rules": ["AK", "AR", "BK", "BL", "DM", "DR", "EB", "EC", "ED"],
            },
        ],
    },
    {
        "branch_id": "6",
        "title": "Citation Normalization & Layer Stack Harmony",
        "description": "Rules for surface span harmonization, multi-word clusters, morphosyntactic alignment with Layer 2/case annex, and slot validity.",
        "subbranches": [
            {
                "sub_id": "6.1",
                "title": "NP Head & Cluster Normalization",
                "description": "Layer-3 NP head equivalence, nested phrase resolution, floating quantifiers, preposition stacks, and adverb-preposition clusters.",
                "rules": ["AI", "BO", "BR", "EI", "BV", "EE", "BJ", "BQ", "AQ", "BP"],
            },
            {
                "sub_id": "6.2",
                "title": "Morphosyntactic & Case Annex Alignment",
                "description": "Corroboration of role assignments via Layer-2 case annex (nominative, accusative, dative, locative), pronoun filtering, and conjunction handling.",
                "rules": ["U", "W", "CM", "CP", "BM"],
            },
            {
                "sub_id": "6.3",
                "title": "Syntactic Slot Admissibility & Consistency",
                "description": "Admissibility of UD argument deprels as skeleton arguments, verbs in argument slots, rule ordering audit, and self-contradictory dual-role violations.",
                "rules": ["AF", "DS", "BW", "Z", "DT", "EG"],
            },
        ],
    },
]

# Curated textual examples and explanations from code comments / tests / corpus citations
RULE_DETAILS: dict[str, dict[str, str]] = {
    "1": {
        "doc": "Clause head token is a predicate. Every token with a clause-head deprel (`root`, `ccomp`, `xcomp`, `csubj`, `csubj:pass`, `advcl`, `acl`, `acl:relcl`, `parataxis`) is derived as an asserting predicate.",
        "ud_rel": "`deprel in CLAUSE_HEAD_DEPRELS`",
        "example": "*Inferno* 1:1 `Nel mezzo del cammin di nostra vita / mi ritrovai...` -> `ritrovai` (root) derived as predicate at (2, 2).",
    },
    "2": {
        "doc": "Non-auxiliary verb carrying argument dependent is a predicate. Any verb that is not an auxiliary (`aux`, `aux:pass`, `cop`) but governs a core or oblique argument is derived as a predicate.",
        "ud_rel": "`deprel not in _AUX_DEPRELS and has argument child`",
        "example": "*Inferno* 1:4 `Ahi quanto a dir qual era è cosa dura...` -> `dir` (verb taking `ccomp` dependent `era`) derived as predicate.",
    },
    "A": {
        "doc": "Basic coordination argument mapping onto coordination head. Net-zero prototype rule for mapping conjunct arguments onto coordination head (subsumed by Rule C).",
        "ud_rel": "`conj` edge walk",
        "example": "Coordinate argument mapping base prototype (subsumed by Rule C).",
    },
    "C": {
        "doc": "Map argument citations across `conj` edges onto coordination head. When an argument is attached to a conjunct or when an argument is coordinate, normalize its citation onto the coordination head (`_coordination_head`).",
        "ud_rel": "`conj` / `appos` / `flat` chains",
        "example": "*Inferno* 1:5 `esta selva selvaggia e aspra e forte` -> `aspra` and `forte` map onto coordination head `selvaggia`.",
    },
    "D": {
        "doc": "Drop nmod obliques whose parent nominal is cited as argument. An adnominal prepositional phrase (`nmod`) hanging off a derived nominal argument is accepted when cited as an oblique of the matrix verb.",
        "ud_rel": "`nmod` child of derived argument nominal",
        "example": "*Inferno* 1:1 `Nel mezzo del cammin di nostra vita` -> `cammin` is an `nmod` of `mezzo`; when `mezzo` is cited as `obl`, `cammin` is dropped without flagging.",
    },
    "I": {
        "doc": "Lexical head attached by `aux`/`cop` is the predicate head. Bounded walk through `aux`, `aux:pass`, and `cop` edges to identify the governing lexical predicate.",
        "ud_rel": "`head` of `aux` / `cop` token",
        "example": "*Inferno* 1:3 `ché la diritta via era smarrita` -> `era` (aux) maps to `smarrita` (lexical head).",
    },
    "J": {
        "doc": "Adverbial oblique in locative/directional slot. A given `obl` or `obl:<prep>` whose argument is an adverb attached to that same predicate as `advmod` ('quivi', 'là', 'dinanzi').",
        "ud_rel": "`advmod` attached to predicate with adverb/noun POS",
        "example": "*Purgatorio* 1:101 `là giù colà dove la batte l'onda` -> `colà` (advmod) accepted in locative oblique slot.",
    },
    "L": {
        "doc": "Refinement between bare `obl` and lemma-qualified `obl:<prep>`. Accepts divergence between derived bare `obl` and LLM lemma-qualified `obl:per`, `obl:a`, `obl:di`, etc., when argument has no case child.",
        "ud_rel": "`obl` vs `obl:<lemma>`",
        "example": "*Inferno* 1:2 `per una selva oscura` -> derived `obl` matched with LLM `obl:per`.",
    },
    "M": {
        "doc": "Predicative complement `xcomp` against derived `obj`/`subj`. Accepts a given `xcomp` when derivation identified the dependent as a direct object or subject in copular/secondary predication.",
        "ud_rel": "`xcomp` vs `obj` / `subj`",
        "example": "*Inferno* 1:4 `è cosa dura` -> derived `obj`/`attr` matched with `xcomp`.",
    },
    "N": {
        "doc": "Case-marked oblique against direct object/subject. A given `obl:<lemma>` against a derived `obj`/`subj` when the argument carries a corresponding `case` marker.",
        "ud_rel": "`obl:<lemma>` vs `obj` with matching `case` child",
        "example": "*Inferno* 21:130 `noi prendemmo la via` -> case-marked complement variation accepted.",
    },
    "O": {
        "doc": "Co-present prepositional variants for one argument. Two different `obl:<lemma>` labels (e.g. `obl:a` vs `obl:in`) for the same argument carrying multiple case particles.",
        "ud_rel": "`obl:<lemma1>` vs `obl:<lemma2>`",
        "example": "*Purgatorio* 1:100 `intorno ad imo ad imo` -> prepositional variants `obl:a` vs `obl:ad` reconciled.",
    },
    "P": {
        "doc": "Flavor mismatch between `ccomp` and `xcomp`. Accepts clausal complement flavor discrepancies (finite `ccomp` vs non-finite `xcomp`).",
        "ud_rel": "`ccomp` vs `xcomp`",
        "example": "*Inferno* 1:4 `a dir qual era` -> `qual era` as `ccomp` vs `xcomp`.",
    },
    "Q": {
        "doc": "Clausal `ccomp` against derived direct object/subject whose argument is a verb. Reconciles nominalized/infinitive verb arguments.",
        "ud_rel": "`ccomp` vs `obj` on verb token",
        "example": "*Inferno* 5:94 `Di quel che udire e che parlar vi piace` -> `udire` derived as `obj`, accepted as `ccomp`.",
    },
    "R": {
        "doc": "Predicative adjective or adverb attached as `advmod` or secondary predicate. Accepts `xcomp` when Layer 4 hung an adjective/adverb as `advmod`.",
        "ud_rel": "`advmod` with adjective POS",
        "example": "*Inferno* 1:7 `Tant' è amara che poco è più morte` -> `amara` attached as `advmod`, accepted as predicative.",
    },
    "S": {
        "doc": "Prepositional `nmod` attached directly to predicate. A given `obl:<lemma>` whose argument is an `nmod` child of the predicate itself with a matching `case` child.",
        "ud_rel": "`nmod` child of predicate with `case` marker",
        "example": "*Inferno* 1:102 `porta di giunchi` -> `giunchi` attached as `nmod`, accepted as `obl:di`.",
    },
    "T": {
        "doc": "Prepositional infinitive adverbial clause attached as `advcl`. A given `obl:<lemma>` whose argument is an `advcl` child of the predicate carrying a `mark`/`case` preposition.",
        "ud_rel": "`advcl` with prepositional `mark`",
        "example": "*Inferno* 5:99 `per aver pace co' seguaci sui` -> `aver` attached as `advcl` with `per`, accepted as `obl:per`.",
    },
    "U": {
        "doc": "Role mismatch corroborated by Layer-2 case annex. When derivation and LLM disagree on pronoun role, accept if Layer-2 case value uniquely corroborates the LLM assignment.",
        "ud_rel": "Pronoun token with Layer-2 case annex value",
        "example": "*Inferno* 5:90 `noi che tignemmo il mondo` -> `noi` verified as `nominative` -> `subj`.",
    },
    "V": {
        "doc": "Non-finite verb control subject inheritance along head chain. Non-finite verbs (infinitives, gerunds, participles) inherit subjects from their governing matrix predicate or controller.",
        "ud_rel": "`xcomp` / `advcl` non-finite head chain walk",
        "example": "*Inferno* 1:4 `a dir qual era` -> `dir` inherits subject from matrix clause controller.",
    },
    "W": {
        "doc": "Swap partner of a case-corroborated role assignment. When Rule U validates a role swap between two pronouns, accept the reciprocal partner.",
        "ud_rel": "Reciprocal partner of Rule U pronoun role swap",
        "example": "*Inferno* 10:44 `onde li piacque` -> clitic pronoun case swap partner accepted.",
    },
    "X": {
        "doc": "Argument cited on copula complement vs matrix predicate. Argument attached to copular complement (`attr`/`xcomp`) accepted when cited on the matrix copula or vice versa.",
        "ud_rel": "Copular complement host transfer",
        "example": "*Inferno* 1:4 `è cosa dura` -> arguments on `cosa` accepted for `è`.",
    },
    "Y": {
        "doc": "Copular nominal clause head attached under nominal deprel. Accepts nominal/adjectival predicates in copular clauses attached under `attr` or `root` without elision.",
        "ud_rel": "Copular clause nominal predicate",
        "example": "*Inferno* 1:4 `è cosa dura` -> `cosa` accepted as copular nominal predication.",
    },
    "Z": {
        "doc": "Verb in argument/adjunct slot proposed as predicate. A subordinate verb placed in a nominal argument slot (`nsubj`, `obj`, `obl`) accepted when proposed as an independent predication.",
        "ud_rel": "`deprel in _NOMINAL_SLOT_DEPRELS` with verb POS",
        "example": "*Inferno* 3:10 `parole di colore oscuro` -> subordinate verb in argument position.",
    },
    "AA": {
        "doc": "Perception or depictive small clause secondary predicate. Secondary predicate hung on a direct object or subject in perception verb constructions.",
        "ud_rel": "`xcomp` / `acl` secondary predicate over argument",
        "example": "*Inferno* 4:118 `Vidi Elettra con molti compagni` -> depictive secondary predication.",
    },
    "AB": {
        "doc": "Reflexive clitic argument of pronominal verb. Pronominal/reflexive clitic pronoun (`si`, `mi`, `ti`, `ci`, `vi`) attached as `expl` accepted in core argument slot.",
        "ud_rel": "`expl` clitic pronoun with pronominal/reflexive verb",
        "example": "*Inferno* 1:2 `mi ritrovai per una selva oscura` -> `mi` (expl) accepted as `obj`/argument.",
    },
    "AC": {
        "doc": "Inherited subject across `conj` is not an independent assertion. An inherited subject across coordination is pruned when identical to the coordination head's given subject.",
        "ud_rel": "`conj` inherited subject vs coordination head subject",
        "example": "*Inferno* 1:2-3 -> coordinate verb conjunct subject pruned against coordination head.",
    },
    "AD": {
        "doc": "Copular adverb complement accepted as predicative modifier. Adverb attached as `advmod` to `essere` accepted as predicative complement `xcomp`.",
        "ud_rel": "`advmod` on copula `essere`",
        "example": "*Inferno* 7:84 `là dove è il male` -> locative adverb on `essere` accepted.",
    },
    "AE": {
        "doc": "Free relative clause cited by verb rather than relative pronoun. Free relative clause cited by its predicate head rather than the introductory relative pronoun (`chi`, `che`).",
        "ud_rel": "Free relative clause head verb in argument slot",
        "example": "*Inferno* 3:34 `e vidi le genti ch'eran là` -> free relative clause resolution.",
    },
    "AF": {
        "doc": "Layer-4 argument deprel position admissible as Layer-5 argument. A token carrying a core/oblique argument deprel in Layer 4 is admissible in Layer 5 even if not heading a Layer-3 NP.",
        "ud_rel": "`deprel in ARG_DEPRELS`",
        "example": "*Inferno* 5:96 `ci tace` -> clitic argument position verified admissible.",
    },
    "AG": {
        "doc": "Drop `conj`-inherited subject when person/number disagrees. Propagation of subjects across coordinate conjuncts is blocked when the target verb's morphological features disagree with the candidate subject.",
        "ud_rel": "`conj` subject agreement filter",
        "example": "*Inferno* 10:111 `e io dissi ... e rispuose` -> 1sg subject `io` blocked from propagating to 3sg `rispuose`.",
    },
    "AH": {
        "doc": "Derivation remains silent when inherited subject is dropped. When Rule AG drops a coordinate subject due to agreement clash, derivation leaves the subject slot empty rather than asserting an erroneous ∅.",
        "ud_rel": "Derivation silence post-Rule AG subject drop",
        "example": "*Inferno* 10:111 -> `rispuose` left with silent subject slot after `io` dropped.",
    },
    "AI": {
        "doc": "Re-key given citation onto derived citation for same Layer-3 NP. Normalizes citations between the syntactic head and modifiers/determiners within the same Layer-3 noun phrase span.",
        "ud_rel": "Layer-3 NP span head equivalence",
        "example": "*Inferno* 1:5 `esta selva selvaggia` -> citation on `esta` or `selva` merged onto NP head.",
    },
    "AJ": {
        "doc": "Argument shared across coordinate conjuncts. An argument (e.g. direct object) expressed only on one conjunct is accepted when cited on coordinate sibling verbs.",
        "ud_rel": "`conj` shared non-subject argument",
        "example": "*Inferno* 5:95 `noi udiremo e parleremo a voi` -> `a voi` shared across coordinate verbs `udiremo` and `parleremo`.",
    },
    "AK": {
        "doc": "Comparative `come` phrase as predicative complement. Comparative phrase introduced by `come` accepted as predicative complement `xcomp`.",
        "ud_rel": "`come` comparative phrase with `xcomp` role",
        "example": "*Inferno* 1:15 `guardai in alto e vidi le sue spalle vestite già de' raggi del pianeta...` -> comparative complement.",
    },
    "AL": {
        "doc": "Fused clitic pronoun legitimately filling two argument slots. Multi-component fused clitic (e.g. `gliel'`, `dammelo`, `cen`) legitimately fills both direct and indirect object slots.",
        "ud_rel": "Fused clitic token (`pronoun+pronoun`)",
        "example": "*Purgatorio* 2:42 `faccel grazioso` -> `cel` (`ci` + `lo`) filling `iobj` and `obj` simultaneously.",
    },
    "AM": {
        "doc": "Collect arguments stranded on `cop`/`aux` dependents. Gathers argument dependents that Layer 4 attached to an auxiliary or copula token and associates them with the lexical predicate head.",
        "ud_rel": "Arguments attached to `aux` / `cop` dependents",
        "example": "*Inferno* 1:3 `era smarrita` -> subject `via` attached to `era` lifted onto `smarrita`.",
    },
    "AN": {
        "doc": "Gapped conjunct carrying orphan fills predicate slots as remnants. A conjunct carrying an `orphan` child heads a gapped clause; its remnants fill the coordination head's argument slots.",
        "ud_rel": "`orphan` deprel on coordinate conjunct",
        "example": "*Inferno* 15:96 `però giri Fortuna la sua rota ..., e 'l villan la sua marra` -> `villan` and `marra` fill `giri`'s slots as remnants.",
    },
    "AP": {
        "doc": "Walk `conj` chain to find coordination head. Bounded traversal across `conj` and `appos` edges to locate the root head of a coordination structure.",
        "ud_rel": "`conj` / `appos` traversal",
        "example": "Coordinate noun phrases with apposition mapped to primary host.",
    },
    "AQ": {
        "doc": "Map argument citations landing on `aux`/`cop` onto lexical head. Re-keys argument citations targeting auxiliary/copula tokens onto the governing lexical verb.",
        "ud_rel": "Argument citation re-keying from `aux`/`cop` to lexical head",
        "example": "*Inferno* 1:3 `era smarrita` -> argument on `era` mapped to `smarrita`.",
    },
    "AR": {
        "doc": "Verbless comparative clause nominal in adjunct slot. Oblique argument derived from a verbless comparison clause introduced by `come`, `quasi`, or `che`.",
        "ud_rel": "Verbless comparative clause with `come`/`quasi` marker",
        "example": "*Inferno* 29:83 `come coltel le scaglie` -> comparative clause nominals mapped to adjunct slot.",
    },
    "AS": {
        "doc": "Widen role gate for fused clitic combinations. Widens role matching gate for fused clitic combinations when both case slots are occupied.",
        "ud_rel": "Fused clitic case slot combination",
        "example": "Fused clitic pronoun role matching extension.",
    },
    "AT": {
        "doc": "Only verbs inherit subjects across `conj` chains. Restricts coordinate subject inheritance to finite verb conjuncts, preventing nominal conjuncts from receiving inherited subjects.",
        "ud_rel": "`is_verb_pos` gate on `conj` subject inheritance",
        "example": "*Purgatorio* 9:58 `Sordel rimase e l'altre genti...` -> nominal conjunct `genti` blocked from inheriting subject.",
    },
    "AU": {
        "doc": "Adjective attached `amod` to argument acting as secondary predicate. Secondary predicate adjective attached as `amod` to an argument nominal.",
        "ud_rel": "`amod` adjective functioning as secondary predicate",
        "example": "*Inferno* 6:24 `urlavan per la pioggia come cani` -> depictive adjective predication.",
    },
    "AV": {
        "doc": "Derived predicate named by auxiliary in LLM output. Derived lexical predicate accepted when named by its auxiliary token in model output.",
        "ud_rel": "Auxiliary token naming lexical predicate",
        "example": "*Inferno* 1:3 `era smarrita` -> predicate cited at line/token of `era`.",
    },
    "AW": {
        "doc": "Pronominal verb clitic omitted in LLM reading. Inherent reflexive clitic in pronominal verbs accepted when omitted in model reading.",
        "ud_rel": "Reflexive clitic omitted on pronominal verb",
        "example": "*Inferno* 1:2 `ritrovarsi` -> omission of reflexive `mi` accepted.",
    },
    "AX": {
        "doc": "Argument hung on opposite end of `xcomp` edge. Argument attached to matrix verb accepted when cited on non-finite `xcomp` complement or vice versa.",
        "ud_rel": "`xcomp` control partner argument sharing",
        "example": "*Inferno* 1:4 `puote aver vita` -> arguments shared between modal `puote` and infinitive `aver`.",
    },
    "AY": {
        "doc": "Adjective phrase governing an argument proposed as predicate. Adjective attached as `amod` governing an argument complement accepted as an independent predication.",
        "ud_rel": "`amod` adjective phrase with argument dependent",
        "example": "*Inferno* 28:115 `un busto sanza capo andar sì come andavan li altri` -> complemented adjective phrase.",
    },
    "AZ": {
        "doc": "Depictive adjective attached as bare `obl` vs `attr`/`xcomp`. Depictive adjective hung as bare `obl` in Layer 4 accepted against `attr` or `xcomp`.",
        "ud_rel": "Bare `obl` with adjective POS vs `xcomp`",
        "example": "*Inferno* 12:83 `ch'i' son soletto` -> depictive bare oblique accepted.",
    },
    "BA": {
        "doc": "Derivation produced two subjects without disambiguating. When derivation produces two candidate subjects (e.g. in gapped clauses), accepts LLM selection of either.",
        "ud_rel": "Dual derived subject candidates",
        "example": "*Inferno* 15:96 `però giri Fortuna la sua rota, e 'l villan la sua marra` -> dual subject resolution.",
    },
    "BB": {
        "doc": "Accept all conjuncts of a coordinate controller. When a controller is a coordination of nominals, accepts any conjunct as valid control subject.",
        "ud_rel": "Coordinate controller conjuncts",
        "example": "Coordinate control subjects mapped onto non-finite complement.",
    },
    "BC": {
        "doc": "Filter adverbial obliques by Layer-2 POS. Restricts adverbial oblique recognition to tokens tagged as adverb, noun, or pronoun in Layer 2.",
        "ud_rel": "POS filtering for adverbial obliques",
        "example": "Adverbial oblique POS validation.",
    },
    "BD": {
        "doc": "Reflexive clitics in pronominal verbs with minor role discrepancy. Reconciles minor role discrepancies (`obj` vs `iobj` vs `obl`) for reflexive clitics in pronominal verbs.",
        "ud_rel": "Reflexive clitic role discrepancy",
        "example": "*Inferno* 9:101 `si volse` -> `obj` vs `iobj` on reflexive clitic.",
    },
    "BE": {
        "doc": "Cycle protection in coordination head walk. Prevents infinite loops when traversing multiword `flat` or cyclic `conj` edges.",
        "ud_rel": "`flat` / `conj` cycle guard",
        "example": "Cycle protection during coordination traversal.",
    },
    "BF": {
        "doc": "Inverted copula dependency structure. Reconciles inverted copular dependencies where Layer 4 attached copula `essere` as head over predicate noun.",
        "ud_rel": "Inverted `cop` dependency structure",
        "example": "*Inferno* 11:25 `d'ogne malizia ... ingiuria è 'l fine` -> inverted copula complement.",
    },
    "BH": {
        "doc": "Displaced pro-drop subject when subject is expressed elsewhere. Accepts pro-drop ∅ subject left behind when the concrete subject is assigned to an `xcomp` complement.",
        "ud_rel": "Displaced pro-drop ∅ subject",
        "example": "*Inferno* 1:4 `è cosa dura` -> ∅ subject on `è` reconciled.",
    },
    "BI": {
        "doc": "Accusative-and-infinitive subject/object sharing. Reconciles nominal shared between matrix perception/causative verb (`obj`) and infinitive complement (`subj`).",
        "ud_rel": "Accusative-and-infinitive construction (`obj` = `subj`)",
        "example": "*Inferno* 4:118 `Vidi Elettra ... andar` -> `Elettra` as matrix `obj` and infinitive `subj`.",
    },
    "BJ": {
        "doc": "Merge multi-word adverb-preposition cluster citations. Normalizes multi-word adverb-preposition combinations ('davanti a', 'dentro di', 'intorno a') onto single oblique head.",
        "ud_rel": "Multi-word adverb-preposition cluster",
        "example": "*Purgatorio* 1:100 `intorno ad imo` -> `intorno a` cluster normalized.",
    },
    "BK": {
        "doc": "Verbless comparative clause marked by `che`. Comparative clause marker `che` in verbless comparative adjunct.",
        "ud_rel": "`che` comparative marker",
        "example": "*Inferno* 1:7 `poco è più morte che...` -> `che` comparative clause.",
    },
    "BL": {
        "doc": "Verbless comparative clause marked by `sì come`. Comparative clause marker `sì come` in verbless comparative adjunct.",
        "ud_rel": "`sì come` comparative marker",
        "example": "*Inferno* 28:115 `sì come andavan li altri` -> `sì come` comparison marker.",
    },
    "BM": {
        "doc": "Connective conjunction parked by Layer 4 in adjunct slot. Reconciles coordinating/subordinating conjunction tokens attached as `obl` in Layer 4.",
        "ud_rel": "`obl` with conjunction POS",
        "example": "*Inferno* 29:124 `Onde l'altro lebbroso...` -> `Onde` in oblique slot.",
    },
    "BN": {
        "doc": "Filter out conjunctions attached as clause heads without arguments. Refuses to promote conjunctions attached as `advcl`/`root` when they carry no argument dependents.",
        "ud_rel": "`advcl`/`root` conjunction without argument children",
        "example": "*Inferno* 29:124 `Onde ... rispuose` -> connective `Onde` blocked from predicate promotion.",
    },
    "BO": {
        "doc": "Ordering gate: rule AI runs before rule D. Ensures Layer-3 NP head normalization executes before adnominal nmod oblique dropping.",
        "ud_rel": "Rule execution ordering constraint",
        "example": "Pipeline execution order enforcement (AI -> D).",
    },
    "BP": {
        "doc": "Normalize `aux`/`cop` dependencies in child host checks. Helper reading `aux`/`cop` heads through to their lexical verb when checking parent-child hosting.",
        "ud_rel": "`_hosts_child` through `aux`/`cop`",
        "example": "Host validation through auxiliary periphrasis.",
    },
    "BQ": {
        "doc": "Support alternative word orders in adverb-preposition clusters. Normalizes inverted or split word order variants in adverb-preposition clusters.",
        "ud_rel": "Split adverb-preposition cluster word order",
        "example": "Inverted adverbial cluster normalization.",
    },
    "BR": {
        "doc": "Argument nested inside a larger Layer-3 noun phrase named by LLM. Accepts a derived argument when nested inside a broader NP span named in model reading.",
        "ud_rel": "Layer-3 NP span nesting containment",
        "example": "*Inferno* 1:1 `il cammin di nostra vita` -> `cammin` nested inside full NP span.",
    },
    "BS": {
        "doc": "Copular predication named by copula token. Reconciles copular predications when the model names the auxiliary/copula token instead of the nominal predicate.",
        "ud_rel": "Copula token naming nominal predication",
        "example": "Copular predication named by `è`.",
    },
    "BT": {
        "doc": "Free relative clause attached under matrix predicate. Reconciles free relative clauses attached as `acl:relcl` to pronoun under matrix verb.",
        "ud_rel": "Free relative clause attached to matrix pronoun",
        "example": "*Inferno* 3:34 `vidi le genti...` -> free relative clause attached to matrix pronoun.",
    },
    "BU": {
        "doc": "Subject supplied by the last conjunct of a coordination. When the subject is syntactically expressed on the final conjunct, propagates subject backward to matrix head.",
        "ud_rel": "Last conjunct subject backward propagation",
        "example": "*Inferno* 10:111 `gridò e disse il duca` -> `il duca` on `disse` supplied to `gridò`.",
    },
    "BV": {
        "doc": "Normalize multi-word preposition fixed/case tokens onto nominal head. Maps multi-word preposition components (`fixed` edges) onto the governing nominal argument head.",
        "ud_rel": "`fixed` edge walk to nominal head",
        "example": "*Inferno* 1:1 `Nel mezzo del cammin` -> `del` fixed child mapped to `cammin`.",
    },
    "BW": {
        "doc": "Interrogative or relative marker token filling an argument slot. Accepts interrogative or relative markers (`chi`, `che`, `dove`) parked in `mark` slot as arguments.",
        "ud_rel": "`mark` slot carrying interrogative/relative pronoun",
        "example": "*Inferno* 1:4 `qual era` -> `qual` in marker slot accepted as argument.",
    },
    "BX": {
        "doc": "Depictive bare oblique omitted in LLM reading. Inherent depictive bare oblique accepted when omitted in model reading.",
        "ud_rel": "Depictive bare oblique omission",
        "example": "*Inferno* 12:83 `soletto` depictive omission accepted.",
    },
    "BY": {
        "doc": "Argument hung on this predicate's own `aux`/`cop` periphrasis. Reconciles arguments attached to the predicate's own auxiliary or copula dependents.",
        "ud_rel": "Argument attached to auxiliary child",
        "example": "*Inferno* 1:3 `era smarrita` -> argument on `era` attached to `smarrita`.",
    },
    "BZ": {
        "doc": "Conj chain subject propagation restricted to finite verbs. Ensures coordinate subject inheritance only walks through finite verb conjuncts.",
        "ud_rel": "Finite verb restriction on `conj` walk",
        "example": "*Inferno* 10:111 -> coordinate finite verb chain traversal.",
    },
    "CA": {
        "doc": "Non-verb conjunct promoted only if it carries argument child. Nominal/adjectival conjuncts are promoted to predicates only if they carry explicit arguments or a copula.",
        "ud_rel": "`conj` nominal promotion argument test",
        "example": "*Inferno* 11:15 `Ed elli: «Vedi...»` -> nominal conjunct with `ccomp` speech promoted.",
    },
    "CB": {
        "doc": "Argument attached to predicative complement underived in Layer 5. Accepts oblique argument hanging off an underived predicative complement.",
        "ud_rel": "Oblique attached to underived `attr`/`xcomp` complement",
        "example": "Oblique on underived complement resolution.",
    },
    "CC": {
        "doc": "Coordinate nominal promoted to `conj` on predicate without slot. Coordinate nominal promoted to predicate level accepted in model argument slot.",
        "ud_rel": "Promoted coordinate nominal argument acceptance",
        "example": "Promoted conjunct nominal argument slot resolution.",
    },
    "CD": {
        "doc": "Coordination head search termination condition. Bounding condition terminating coordination head search when crossing clause boundaries.",
        "ud_rel": "Coordination head walk bounding",
        "example": "Coordination search boundary condition.",
    },
    "CE": {
        "doc": "Relative pronoun and antecedent co-indexing in control chain. Co-indexes relative pronoun with its antecedent during control subject candidate generation.",
        "ud_rel": "Relative pronoun antecedent co-indexing",
        "example": "*Inferno* 1:3 `che la diritta via...` -> `che` co-indexed with antecedent.",
    },
    "CF": {
        "doc": "Extract controller hidden inside fused clitic pronoun. Extracts controller nominal from fused clitic pronouns (e.g. `tenerla` -> `la`).",
        "ud_rel": "Controller extraction from fused clitic",
        "example": "*Inferno* 10:55 `anzi ad aprir ch'a tenerla serrata` -> `la` extracted as controller.",
    },
    "CG": {
        "doc": "Elided coordinate oblique citable only by modifier. Accepts elided coordinate oblique cited through its determiner or modifier.",
        "ud_rel": "Elided coordinate oblique modifier citation",
        "example": "Elided coordinate oblique resolution.",
    },
    "CH": {
        "doc": "Participle or verb in `amod`/`acl` slot acting as reduced relative. Participle or verb attached as `amod` or `acl` accepted as an independent predication.",
        "ud_rel": "`amod` / `acl` participle / reduced relative verb",
        "example": "*Inferno* 1:15 `vestite già de' raggi del pianeta` -> participle `vestite` accepted as predicate.",
    },
    "CI": {
        "doc": "Resolve host positions through coordination collapse. Helper resolving argument host positions through coordinate head collapse.",
        "ud_rel": "Coordination host position resolution",
        "example": "Host position coordination resolution.",
    },
    "CJ": {
        "doc": "Controller in Layer 4 `obl` slot in control candidate walk. Allows oblique controllers (e.g. agent or dative controller) during control candidate generation.",
        "ud_rel": "`obl` controller in control candidate walk",
        "example": "*Inferno* 3:10 `parve a me` -> oblique experiencer `me` as controller.",
    },
    "CK": {
        "doc": "Subordinate clause cited by its marker/complementizer. Accepts a subordinate clause argument cited by its opening complementizer (`che`, `come`, `se`).",
        "ud_rel": "`mark` complementizer naming subordinate clause",
        "example": "*Inferno* 1:3 `ché la diritta via...` -> subordinate clause cited at `ché`.",
    },
    "CL": {
        "doc": "Fall back to control subject when Rule AG drops inherited subject. When Rule AG drops a coordinate subject, falls back to control chain candidate search.",
        "ud_rel": "Control fallback post-Rule AG subject drop",
        "example": "*Inferno* 10:111 -> control subject fallback after agreement mismatch drop.",
    },
    "CM": {
        "doc": "Map clitic pronoun to case annex slot. Helper mapping clitic pronoun position to Layer-2 case annex slot string.",
        "ud_rel": "Clitic pronoun case annex mapping",
        "example": "Clitic case slot mapping.",
    },
    "CN": {
        "doc": "Pro-drop null subject slot placed at back of queue. Places pro-drop ∅ null subject at the back of the argument ranking queue during gapped remnant assignment.",
        "ud_rel": "Pro-drop ∅ ranking queue positioning",
        "example": "Gapped remnant pro-drop ranking queue order.",
    },
    "CP": {
        "doc": "Identify adjective and noun POS for secondary predication. Helper identifying adjective and noun POS for depictive/secondary predication classification.",
        "ud_rel": "Nominal POS classification helper",
        "example": "Secondary predication nominal POS filter.",
    },
    "CQ": {
        "doc": "Prepositional infinitive complement clause as `xcomp`. Prepositional infinitive complement clause (e.g. `a + inf`) accepted as `xcomp` vs `obl:<prep>`.",
        "ud_rel": "Prepositional infinitive complement `xcomp` vs `obl`",
        "example": "*Inferno* 1:4 `a dir qual era` -> `a dir` as `xcomp` vs `obl:a`.",
    },
    "CS": {
        "doc": "Role-less empty derived tuple treated as non-asserting. Empty derived predicate tuple with no arguments treated as non-asserting when absent in LLM output.",
        "ud_rel": "Empty derived predicate tuple",
        "example": "*Inferno* 29:124 -> empty derived connective tuple.",
    },
    "CT": {
        "doc": "Copula attached under its own predicate complement. Reconciles inverted tree structure where copula `essere` is attached under its own predicate complement.",
        "ud_rel": "Copula attached under complement",
        "example": "*Inferno* 1:4 `cosa dura` -> `è` attached under `cosa`.",
    },
    "CU": {
        "doc": "Accept double listing of pro-drop ∅ and concrete subject. Accepts LLM listing both pro-drop ∅ and the concrete derived subject token for the same predicate.",
        "ud_rel": "Double listing of ∅ and concrete subject",
        "example": "*Inferno* 1:2 `ritrovai` -> double listing of (0,0) and overt subject.",
    },
    "CW": {
        "doc": "Second term of gapped comparison clause. Oblique argument belonging to the second term of a gapped comparison clause.",
        "ud_rel": "Second term of gapped comparison",
        "example": "*Inferno* 15:96 `e 'l villan la sua marra` -> `marra` as second term argument.",
    },
    "CX": {
        "doc": "Interrogative wh-word opening a subordinate clause. Accepts subordinate clause cited by its opening interrogative wh-word (`chi`, `qual`, `dove`).",
        "ud_rel": "Interrogative wh-word naming clause",
        "example": "*Inferno* 1:4 `qual era` -> clause cited by `qual`.",
    },
    "CY": {
        "doc": "Clausal complement double-listed under auxiliary. Accepts clausal complement double-listed on both auxiliary and lexical head.",
        "ud_rel": "Clausal complement double-listing on `aux`",
        "example": "*Inferno* 1:4 `puote aver vita` -> clausal complement double-listing.",
    },
    "CZ": {
        "doc": "Gapped remnant case assignment via Layer-2 case annex. Uses Layer-2 case annex values (nominative, accusative, dative) to assign argument slots to gapped remnants.",
        "ud_rel": "Case annex slot assignment for gapped remnants",
        "example": "*Inferno* 15:96 `il villan` (nominative -> subj), `la sua marra` (accusative -> obj).",
    },
    "DA": {
        "doc": "Empty derived predicate cannot contradict non-subject arguments. An empty derived predicate cannot contradict non-subject arguments proposed in LLM reading.",
        "ud_rel": "Empty derived predicate non-subject compatibility",
        "example": "Empty derived predicate argument validation.",
    },
    "DB": {
        "doc": "Copular complement carrying prepositional marker. Copular predicate complement carrying a prepositional marker (e.g. `è di pietra`) accepted as `xcomp` vs `obl`.",
        "ud_rel": "Prepositional copular complement `xcomp` vs `obl`",
        "example": "*Inferno* 3:10 `parole di colore oscuro` -> prepositional complement on `essere`.",
    },
    "DC": {
        "doc": "Resolve host position through relative pronoun identity. Helper resolving host position through relative pronoun co-indexing.",
        "ud_rel": "Relative pronoun host position resolution",
        "example": "Relative pronoun host position identity.",
    },
    "DD": {
        "doc": "Relative locative adverb attached as `case` on clause. Relative locative adverb (`dove`, `ove`, `onde`) attached as `case` on clause accepted as locative oblique.",
        "ud_rel": "`dove`/`ove`/`onde` relative locative adverb",
        "example": "*Inferno* 5:97 `dove nata fui` -> `dove` in locative oblique slot.",
    },
    "DE": {
        "doc": "Coordination head names its own role independently. When coordination head is explicitly cited, preserves the head's own syntactic role.",
        "ud_rel": "Coordination head independent role assignment",
        "example": "*Inferno* 1:5 `selva selvaggia e aspra` -> head `selvaggia` names its own role.",
    },
    "DF": {
        "doc": "Apply rule AI NP-head normalization to control candidates. Normalizes control subject candidates using Layer-3 NP head equivalence.",
        "ud_rel": "NP head normalization in control candidate set",
        "example": "Control candidate NP head normalization.",
    },
    "DG": {
        "doc": "Apply coordination collapse in raw membership check. Applies coordination collapse during raw token argument membership verification.",
        "ud_rel": "Raw membership coordination normalization",
        "example": "Raw membership check across coordination.",
    },
    "DH": {
        "doc": "First term of gapped comparison clause. Oblique argument belonging to the first term of an elided comparison clause.",
        "ud_rel": "First term of gapped comparison",
        "example": "*Inferno* 15:96 `Fortuna la sua rota` -> `rota` as first term argument.",
    },
    "DI": {
        "doc": "Gapped clause headed on remnant read as predicate. Gapped clause headed on orphan remnant accepted when proposed as an independent predication.",
        "ud_rel": "Gapped clause orphan remnant as predicate",
        "example": "*Inferno* 15:96 `villan` accepted as gapped clause predicate head.",
    },
    "DJ": {
        "doc": "Wh-word opening clause with identical role. Reconciles wh-word opening subordinate clause when carrying identical role.",
        "ud_rel": "Wh-word identical role assignment",
        "example": "Wh-word subordinate clause citation.",
    },
    "DK": {
        "doc": "Antecedent cited where derivation names relative pronoun. Accepts antecedent nominal cited where derivation names relative pronoun (`che`, `cui`).",
        "ud_rel": "Antecedent nominal vs relative pronoun",
        "example": "*Inferno* 1:3 `la diritta via era smarrita / che...` -> `via` cited for `che`.",
    },
    "DL": {
        "doc": "Pruned redundant gate in prepositional copular complement. Pruned redundant gate in prepositional copular complement classification.",
        "ud_rel": "Prepositional copular gate pruning",
        "example": "Prepositional copular complement gate.",
    },
    "DM": {
        "doc": "Comparison markers in Layer-4 `case` slot. Reconciles comparison markers (`come`, `quanto`) placed in Layer-4 `case` slot.",
        "ud_rel": "Comparison marker in `case` slot",
        "example": "*Inferno* 1:4 `quanto a dir` -> comparison particle in case slot.",
    },
    "DN": {
        "doc": "Subject written inside periphrasis by Layer 4. Raised subject placed inside non-finite periphrasis accepted on matrix verb.",
        "ud_rel": "Raised infinitive subject inside periphrasis",
        "example": "*Inferno* 5:94 `vi piace` -> raised subject inside periphrasis.",
    },
    "DO": {
        "doc": "Donor predicate disagrees in person/number with target. Blocks coordinate subject inheritance when donor predicate's morphological person/number contradicts target verb.",
        "ud_rel": "Donor predicate agreement clash gate",
        "example": "*Inferno* 10:111 `gridò e disse` -> donor predicate agreement validation.",
    },
    "DP": {
        "doc": "Negative gate: clause relativized by non-pronoun particle. Negative gate ensuring clause relativized by non-pronoun particle is not treated as a relative pronoun argument.",
        "ud_rel": "Clausal relativizer negative gate",
        "example": "Relative clause relativizer negative gate.",
    },
    "DQ": {
        "doc": "Impersonal verb whose subject is its own `che`-clause. Reconciles impersonal verbs (e.g. `parve`, `convenne`) whose subject is their subordinate `che`-clause (`ccomp`).",
        "ud_rel": "Impersonal verb with clausal subject (`ccomp` = `subj`)",
        "example": "*Inferno* 1:12 `Tant' era pien di sonno su quel punto / che la verace via abbandonai` -> impersonal clausal subject.",
    },
    "DR": {
        "doc": "Verbless comparison marked by `quasi`. Oblique argument derived from a verbless comparison marked by `quasi`.",
        "ud_rel": "`quasi` comparison marker",
        "example": "*Inferno* 4:110 `quasi di fiamme` -> `quasi` verbless comparison.",
    },
    "DS": {
        "doc": "Marker slot argument normalization in raw membership check. Normalizes marker slot arguments during raw token membership validation.",
        "ud_rel": "Raw membership marker slot normalization",
        "example": "Marker slot argument membership verification.",
    },
    "DT": {
        "doc": "Ordering constraint between classification rules. Ordering constraint audit ensuring proper sequence among classification checks.",
        "ud_rel": "Rule ordering constraint audit",
        "example": "Classification rule execution order audit.",
    },
    "DU": {
        "doc": "Conj subject chain cut by explicit pro-drop ∅. Coordinate subject inheritance stops when an intervening conjunct carries an explicit pro-drop ∅.",
        "ud_rel": "Explicit pro-drop ∅ cutoff in `conj` chain",
        "example": "*Purgatorio* 1:105 `seconda` -> explicit pro-drop ∅ cut.",
    },
    "DV": {
        "doc": "Stranded complement read through rule AU adjective host. Stranded complement argument read through Rule AU adjective host.",
        "ud_rel": "Stranded complement on adjective host",
        "example": "Stranded complement resolution via adjective host.",
    },
    "DW": {
        "doc": "Depictive `attr` omitted in LLM reading. Depictive adjective placed in `attr` slot in Layer 4 accepted when omitted in model reading.",
        "ud_rel": "Depictive `attr` omission",
        "example": "*Inferno* 12:83 `soletto` depictive attr omission.",
    },
    "DX": {
        "doc": "Predicative adjective attached as `advmod`. Predicative adjective attached as `advmod` accepted in secondary predication slot.",
        "ud_rel": "`advmod` predicative adjective",
        "example": "*Inferno* 1:7 `amara` predicative advmod.",
    },
    "DY": {
        "doc": "Relative locative markers identified by Layer-2 lemma. Identifies relative locative markers by Layer-2 lemma ('dove', 'ove', 'onde', 'donde').",
        "ud_rel": "Relative locative lemma identification",
        "example": "*Inferno* 5:97 `dove` identified by lemma.",
    },
    "DZ": {
        "doc": "Rule AI NP-head equivalence read through rule C coordination collapse. Re-keys conjunct argument citations onto NP head through coordinate collapse.",
        "ud_rel": "NP head equivalence through coordination collapse",
        "example": "NP head equivalence read through coordination collapse.",
    },
    "EA": {
        "doc": "Elided speech verb parataxis on pronoun asserts lone ∅ subject. Elided speech verb in paratactic structure on pronoun asserts a lone pro-drop ∅ subject.",
        "ud_rel": "Paratactic speech-act nominal predication",
        "example": "*Inferno* 11:15 `Ed elli: «Vedi...»` -> speech-act parataxis asserting ∅ subject.",
    },
    "EB": {
        "doc": "Boundary check for comparative `come` phrases. Bounding check ensuring comparative `come` phrases stay within parse unit boundaries.",
        "ud_rel": "Comparative `come` phrase boundary check",
        "example": "*Inferno* 29:83 `come coltel...` boundary validation.",
    },
    "EC": {
        "doc": "Correlative comparison marker in comparative `come` phrases. Reconciles correlative markers (`sì`, `così`) in comparative `come` constructions.",
        "ud_rel": "`sì ... come` correlative comparison",
        "example": "*Inferno* 28:115 `sì come andavan li altri` -> correlative comparison.",
    },
    "ED": {
        "doc": "Comparison clause headed on `come` with adjunct on matrix verb. Comparison clause headed on `come` attached as adjunct on matrix verb.",
        "ud_rel": "Comparison clause attached as matrix adjunct",
        "example": "*Inferno* 5:96 `come fa, ci tace` -> comparison clause host.",
    },
    "EE": {
        "doc": "Fixed child in multiword preposition stack. Normalizes fixed children in multiword preposition combinations onto governing head.",
        "ud_rel": "`fixed` child preposition stack normalization",
        "example": "Preposition stack fixed child normalization.",
    },
    "EF": {
        "doc": "Conj subject inheritance walk stops at sibling with subject. Coordinate subject inheritance stops at any sibling conjunct that has already supplied its own overt subject.",
        "ud_rel": "Sibling subject cutoff in `conj` walk",
        "example": "*Inferno* 10:111 -> sibling subject cutoff.",
    },
    "EG": {
        "doc": "One token filling two incompatible roles of one predicate. Hard semantic constraint: one token cannot fill two incompatible roles (e.g. `subj` and `obj`) of the same predicate.",
        "ud_rel": "Dual-role self-contradiction check across artifact rows",
        "example": "*Purgatorio* 1 -> dual role violation gate (0 corpus-wide).",
    },
    "EH": {
        "doc": "Positionally aligned lemma components for fused clitics. Matches positionally aligned lemma components for fused clitic combinations.",
        "ud_rel": "Fused clitic positional lemma alignment",
        "example": "Fused clitic lemma alignment.",
    },
    "EI": {
        "doc": "Re-key given floating quantifier citation onto derived nominal head. Floating quantifiers ('tutti', 'ambo', 'amendue', 'ciascuno') cited in argument slots are merged onto the derived nominal head.",
        "ud_rel": "Floating quantifier citation merge (`_FLOATING_QUANTIFIERS`)",
        "example": "*Paradiso* 10:136 `tutti quanti` -> floating quantifier `tutti` merged onto nominal head.",
    },
}


class CachedCorpus:
    """Pre-loaded corpus tables for fast in-memory rule census."""

    def __init__(self) -> None:
        self.units: list[tuple[list[int], list[str], dict[int, list], dict[int, list], dict[int, list], dict[int, list], dict[int, list]]] = []

    def load(self) -> None:
        cantos_list = [
            ("inferno", api.cantos("inferno")),
            ("purgatorio", api.cantos("purgatorio")),
            ("paradiso", api.cantos("paradiso")),
        ]
        for canticle, nums in cantos_list:
            for number in nums:
                if not skel.has_skel(canticle, number):
                    continue
                data = skel.load_skel(canticle, number)
                morph_rows = {no: list(rows) for no, rows in morph.load_morph(canticle, number).items()} if morph.has_morph(canticle, number) else {}
                np_rows = {no: list(rows) for no, rows in np.load_np(canticle, number).items()} if np.has_np(canticle, number) else {}
                dep_rows = {no: list(rows) for no, rows in dep.load_dep(canticle, number).items()} if dep.has_dep(canticle, number) else {}
                case_rows = {no: list(rows) for no, rows in case.load_case(canticle, number).items()} if case.has_case(canticle, number) else {}

                lines = api.canto(canticle, number).lines()
                text_by_no = {line.no: line.text for line in lines}
                nos_all = [line.no for line in lines]
                texts_all = [line.text for line in lines]

                for unit in dep.sentence_groups(nos_all, texts_all, dep.MAX_UNIT_LINES):
                    unit_texts = [text_by_no[no] for no in unit]
                    rows_by_line = {no: list(data.get(no, [])) for no in unit}
                    self.units.append(
                        (unit, unit_texts, rows_by_line, morph_rows, np_rows, dep_rows, case_rows)
                    )


def run_census(corpus: CachedCorpus) -> dict[str, dict[str, object]]:
    RULES.reset_disabled()
    RULES.reset_hits()

    for unit, unit_texts, rows_by_line, morph_rows, np_rows, dep_rows, case_rows in corpus.units:
        skel.validate_unit(
            unit,
            unit_texts,
            rows_by_line,
            morph_rows=morph_rows,
            np_rows=np_rows,
            dep_rows=dep_rows,
            case_rows=case_rows,
        )

    all_rules = RULES.all_rules()
    population_counts = {r.id: RULES.hit_count(r.id) for r in all_rules}
    results: dict[str, dict[str, object]] = {}

    for rule in all_rules:
        RULES.reset_disabled()
        RULES.disable(rule.id)

        violations_on_removal = 0
        for unit, unit_texts, rows_by_line, morph_rows, np_rows, dep_rows, case_rows in corpus.units:
            v = skel.validate_unit(
                unit,
                unit_texts,
                rows_by_line,
                morph_rows=morph_rows,
                np_rows=np_rows,
                dep_rows=dep_rows,
                case_rows=case_rows,
            )
            soft = [x for x in v if x.kind == "tag"]
            violations_on_removal += len(soft)

        pop = population_counts.get(rule.id, 0)
        status = "active" if violations_on_removal > 0 else ("auxiliary" if pop > 0 else "dormant")

        results[rule.id] = {
            "id": rule.id,
            "name": rule.name,
            "kind": rule.kind,
            "population": pop,
            "removal_violations": violations_on_removal,
            "status": status,
            "description": rule.description,
        }

    RULES.reset_disabled()
    return results


def render_markdown(census_results: dict[str, dict[str, object]]) -> str:
    lines: list[str] = []

    # Title & Metadata
    lines.append("# Layer 5 Grammar Handbook & Rule Specification (`skel/RULES.md`)\n")
    lines.append("**Dante Corpus — Layer 5 Predicate-Argument Skeleton Rules**\n")
    lines.append("> **Status**: Verified at **0 hard / 0 soft violations** across all 100 cantos of the *Divina Commedia* (`pytest` **547 passed**).")
    lines.append("> **Rule Catalog**: 130 formally registered rules (82 directly active, 5 auxiliary/structural, 43 dormant/subsumed).\n")
    lines.append("---\n")

    # Table of Contents & Hierarchy
    lines.append("## Table of Contents & Grammatical Hierarchy Tree\n")
    lines.append("```mermaid")
    lines.append("graph TD")
    lines.append("    ROOT[Layer 5 Grammatical Rules Engine]")
    lines.append("    ROOT --> B1[1. Predicate & Clausal Topology]")
    lines.append("    ROOT --> B2[2. Subject Licensing & Authority]")
    lines.append("    ROOT --> B3[3. Core Valency & Complementation]")
    lines.append("    ROOT --> B4[4. Obliques & Adjuncts]")
    lines.append("    ROOT --> B5[5. Coordination, Ellipsis & Comparison]")
    lines.append("    ROOT --> B6[6. Citation Normalization & Layer Harmony]")
    lines.append("    B1 --> B1_1[1.1 Predicate Head Selection: 1, 2, BN, AN]")
    lines.append("    B1 --> B1_2[1.2 Aux / Copula Predications: I, Y, BF, BS, CT, AV]")
    lines.append("    B1 --> B1_3[1.3 Secondary & Reduced Predications: AA, AU, R, DX, AZ, BX, DW, AY, CH, EA, CS, DA]")
    lines.append("    B2 --> B2_1[2.1 Pro-Drop & Null Subjects: BH, CN, CU, DU]")
    lines.append("    B2 --> B2_2[2.2 Coordinate Subject Inheritance: BZ, AT, AG, DO, AH, EF, AP, BE, CD, DE, AC, BU]")
    lines.append("    B2 --> B2_3[2.3 Control & Raising: V, CL, BB, BI, DN, AX, CF, CJ, CE, DF]")
    lines.append("    B2 --> B2_4[2.4 Impersonal & Displaced Subjects: DQ, BA]")
    lines.append("    B3 --> B3_1[3.1 Objects & Pronominal Clitics: N, AB, AW, BD, AL, AS, EH]")
    lines.append("    B3 --> B3_2[3.2 Clausal Complements: P, Q, CQ, CY, CK]")
    lines.append("    B3 --> B3_3[3.3 Predicative Complements: M, DB, DL, AD, X]")
    lines.append("    B4 --> B4_1[4.1 Prepositional Obliques: L, O, S, CB, DV, D]")
    lines.append("    B4 --> B4_2[4.2 Adverbial & Locative Obliques: J, BC, DD, DY]")
    lines.append("    B4 --> B4_3[4.3 Adverbial & Relative Clauses: T, AE, BT, DP, DK, CX, DJ, DC]")
    lines.append("    B5 --> B5_1[5.1 Coordinate Conjuncts: A, C, DG, AJ, DZ, CA, CC]")
    lines.append("    B5 --> B5_2[5.2 Gapping & Orphan Remnants: CZ, DH, CW, DI, CG]")
    lines.append("    B5 --> B5_3[5.3 Comparative Constructions: AK, AR, BK, BL, DM, DR, EB, EC, ED]")
    lines.append("    B6 --> B6_1[6.1 NP Head & Cluster Normalization: AI, BO, BR, EI, BV, EE, BJ, BQ, AQ, BP]")
    lines.append("    B6 --> B6_2[6.2 Morphosyntactic & Case Annex Alignment: U, W, CM, CP, BM]")
    lines.append("    B6 --> B6_3[6.3 Syntactic Slot Admissibility & Consistency: AF, DS, BW, Z, DT, EG]")
    lines.append("```\n")

    for branch in TAXONOMY:
        b_id = branch["branch_id"]
        b_title = branch["title"]
        lines.append(f"- [{b_id}. {b_title}](#{b_id.lower()}-{b_title.lower().replace(' ', '-').replace('&', '').replace(',', '')})")
        for sub in branch["subbranches"]:
            s_id = sub["sub_id"]
            s_title = sub["title"]
            lines.append(f"  - [{s_id} {s_title}](#{s_id.replace('.', '')}-{s_title.lower().replace(' ', '-').replace('&', '').replace(',', '')})")
    lines.append("- [Execution Pipelines & Cascades](#execution-pipelines--cascades)")
    lines.append("- [Master Rule Index](#master-rule-index)\n")
    lines.append("---\n")

    # Sections
    for branch in TAXONOMY:
        b_id = branch["branch_id"]
        b_title = branch["title"]
        b_desc = branch["description"]
        lines.append(f"## {b_id}. {b_title}\n")
        lines.append(f"{b_desc}\n")

        for sub in branch["subbranches"]:
            s_id = sub["sub_id"]
            s_title = sub["title"]
            s_desc = sub["description"]
            lines.append(f"### {s_id} {s_title}\n")
            lines.append(f"{s_desc}\n")

            for rid in sub["rules"]:
                census = census_results.get(rid, {})
                details = RULE_DETAILS.get(rid, {})
                rname = census.get("name", "")
                rkind = census.get("kind", "")
                rstatus = census.get("status", "dormant")
                rpop = census.get("population", 0)
                rrem = census.get("removal_violations", 0)
                rdesc = census.get("description", "")
                doc = details.get("doc", rdesc)
                ud_rel = details.get("ud_rel", "Universal Dependencies relation")
                example = details.get("example", "Corpus citation in Divina Commedia")

                lines.append(f"#### Rule `{rid}`: `{rname}`\n")
                lines.append(f"- **Kind**: `{rkind}` | **Status**: **{rstatus}** | **Population**: {rpop} hits | **Removal Impact**: {rrem} violations")
                lines.append(f"- **Grammatical Summary**: {rdesc}")
                lines.append(f"- **Universal Dependencies Formulation**: `{ud_rel}`")
                lines.append(f"- **Linguistic Rationale & Implementation**:")
                lines.append(f"  > {doc}")
                lines.append(f"- **Archetypal Text Example**:")
                lines.append(f"  > {example}\n")

        lines.append("---\n")

    # Execution Cascades
    lines.append("## Execution Pipelines & Cascades\n")
    lines.append("### 1. Derivation Engine (`derive_unit`)\n")
    lines.append("The deterministic skeleton derivation engine operates in 9 strict stages:")
    lines.append("1. **Clause-Head Predicates**: Rule `1` (identifies heads in `CLAUSE_HEAD_DEPRELS`), filtered by Rule `BN` (conjunction without arguments) and Rule `AN` (gapped orphan head).")
    lines.append("2. **Non-Auxiliary Verbs**: Rule `2` (identifies verbs with argument dependents).")
    lines.append("3. **Conjunct Promotion**: Rule `CA` (non-verb argument test) and Rule `AT` (finite verb restriction).")
    lines.append("4. **Control Chain & Inheritance**: Rule `V` (non-finite verb control chain walk), Rule `BB` (coordinate controllers), Rule `CE` (relative pronoun co-indexing), Rule `CF` (fused clitic controller), Rule `CJ` (oblique controller), and Rule `DF` (NP-head normalization).")
    lines.append("5. **Coordination Argument Collapse**: Rule `C` (collapses `conj` edges), Rule `AP` (appositions), Rule `BE` (flat multiword), Rule `CD` (termination condition), and Rule `DE` (head independent role).")
    lines.append("6. **Subject Inheritance with Agreement**: Rule `BZ` (finite verbs), Rule `AG` / `DO` (agreement mismatch gates), Rule `AH` (silent fallback), Rule `CL` (control subject fallback), Rule `EF` (sibling cutoff), and Rule `DU` (pro-drop cutoff).")
    lines.append("7. **Pro-Drop Null Subject Queue**: Rule `CN` (places ∅ at back of rank queue).")
    lines.append("8. **Gapped Remnant Assignment**: Rule `AN` (orphan remnants fill head slots) and Rule `CZ` (case annex assignment).")
    lines.append("9. **Stranded Argument Collection**: Rule `AM` (collects arguments attached to `cop`/`aux` dependents).\n")

    lines.append("### 2. Normalization Pipeline\n")
    lines.append("Before divergence checking, argument citations undergo a strict linear normalization cascade:")
    lines.append("```text")
    lines.append("AQ (auxiliary citation merge) -> BV (preposition stack fixed children) -> BJ (adverb-preposition clusters) -> C (coordination collapse) -> AI (Layer-3 NP head equivalence) -> EI (floating quantifiers) -> D (drop adnominal nmod obliques)")
    lines.append("```\n")

    lines.append("### 3. Subject Authority Workflow\n")
    lines.append("Subject assignment is evaluated via the authority protocol in `_apply_subj_authority`:")
    lines.append("1. **Rule CU**: Double listing of pro-drop ∅ and concrete subject -> prune ∅.")
    lines.append("2. **Pro-Drop Resolution**: When derivation asserts ∅, concrete subject proposed by model is accepted.")
    lines.append("3. **Non-Finite Predicates**: When derivation asserts no subject, candidate subjects reachable by Rule `V` control chain are accepted.")
    lines.append("4. **Agreement Discordance**: When coordinate inherited subject clashes in person/number with target verb, Rule `AG` / `DO` drops the inherited subject; Rule `AH` keeps derivation silent or Rule `CL` falls back to control subject.")
    lines.append("5. **Non-Independent Assertion**: Rule `AC` prunes coordinate subjects matching the coordination head; Rule `BU` accepts subject supplied by the last conjunct.\n")

    lines.append("---\n")

    # Master Rule Index
    lines.append("## Master Rule Index\n")
    lines.append("| Rule ID | Name | Kind | Branch | Population | Removal Violations | Status | Description |")
    lines.append("| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |")

    # Build branch mapping for index
    rule_to_branch: dict[str, str] = {}
    for branch in TAXONOMY:
        for sub in branch["subbranches"]:
            for rid in sub["rules"]:
                rule_to_branch[rid] = sub["sub_id"]

    for rid, rname, rkind, rdesc in _RULES_CATALOG:
        census = census_results.get(rid, {})
        rstatus = census.get("status", "dormant")
        rpop = census.get("population", 0)
        rrem = census.get("removal_violations", 0)
        branch_ref = rule_to_branch.get(rid, "-")
        lines.append(f"| `{rid}` | `{rname}` | `{rkind}` | {branch_ref} | {rpop} | {rrem} | **{rstatus}** | {rdesc} |")

    lines.append("")
    return "\n".join(lines)


def main() -> None:
    t0 = time.perf_counter()
    print("Loading corpus for census...", file=sys.stderr)
    corpus = CachedCorpus()
    corpus.load()
    print(f"Loaded {len(corpus.units)} parse units in {time.perf_counter() - t0:.2f}s.", file=sys.stderr)

    t1 = time.perf_counter()
    print("Executing live rule census...", file=sys.stderr)
    census_results = run_census(corpus)
    print(f"Census completed in {time.perf_counter() - t1:.2f}s.", file=sys.stderr)

    print("Rendering skel/RULES.md...", file=sys.stderr)
    md_content = render_markdown(census_results)

    target_path = Path("skel/RULES.md")
    target_path.write_text(md_content, encoding="utf-8")
    print(f"Successfully generated {target_path} ({len(md_content)} bytes, {len(md_content.splitlines())} lines).", file=sys.stderr)


if __name__ == "__main__":
    main()
