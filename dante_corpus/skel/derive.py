"""Layer 5 predicate-argument derivation engine."""

from __future__ import annotations

import re

from ..case import SLOT_SEP, CaseRow
from ..dep import DepRow, subject_agreement
from ..morph import MorphRow
from ..np import NPSpan
from .models import (
    _RELATIVE_PRONOUNS,
    SkelRow,
    _normalize_prep_lemma,
    _role_rank,
    _row_sort_key,
)
from .registry import rule_active


def is_verb_pos(pos: str) -> bool:
    """True when a Layer-2 `pos` names `verb` as one of its components.

    A plain substring test would match **`adverb`**: Layer 2's `pos` is a `+`-joined list of
    components (`verb`, `adverb`, `verb+pronoun`, `conjunction+pronoun+verb`), so the test has to
    be on component boundaries."""
    return "verb" in re.split(r"[^a-z]+", pos.lower())


# A token is a predicate if it is a clause head (rule 1) or a non-auxiliary verb that itself
# takes an argument-bearing dependent (rule 2) — see the module docstring and PLAN.md. Both
# rules are UD-deprel-driven so they cover the corpus's two frozen copular styles alike: a
# copula-as-root clause (`è` root, `cosa` attr) and a UD-style adjectival/nominal predicate
# (`amara` head, `è` cop child).
CLAUSE_HEAD_DEPRELS = frozenset({
    "root", "ccomp", "xcomp", "csubj", "csubj:pass",
    "advcl", "acl", "acl:relcl", "parataxis",
})
_SUBJ_DEPRELS = frozenset({"nsubj", "nsubj:pass", "csubj", "csubj:pass"})
_DIRECT_ROLE_MAP = {
    "obj": "obj", "iobj": "iobj", "attr": "attr", "xcomp": "xcomp", "ccomp": "ccomp",
}
ARG_DEPRELS = frozenset(_SUBJ_DEPRELS | set(_DIRECT_ROLE_MAP) | {"obl", "obl:agent"})
_AUX_DEPRELS = frozenset({"aux", "aux:pass", "cop"})


def _prep_lemma(row: MorphRow) -> str:
    return row.lemma.split("+")[0].strip().lower()


def _case_supports_role(case_value: str, role: str) -> bool:
    """Whether the `case/` annex's value for an argument position is compatible with a Layer-5
    role label. The mapping between the two frozen vocabularies is the obvious one and nothing
    external enters it — both were authored by a model reading the Italian alone (see PLAN.md's
    *Neutrality check*).

    `obl:a` is deliberately compatible with `dative` **and** with the locative/ablative values:
    Italian `a` marks both the indirect object and a place ("a Roma"), so the annex cannot
    adjudicate between two oblique flavors there. A fused value (`a+b`, `SLOT_SEP`-joined for a
    fused token like `gliel'`) matches nothing, so a fused position decides nothing."""
    if role == "subj":
        return case_value == "nominative"
    if role == "obj":
        return case_value == "accusative"
    if role == "iobj":
        return case_value == "dative"
    if role == "obl:a":
        return case_value in ("dative", "ablative", "locative")
    if role == "obl" or role.startswith("obl:"):
        return case_value in ("ablative", "locative")
    return False


def derive_unit(
    nos: list[int],
    dep_rows_by_line: dict[int, "list[DepRow] | tuple[DepRow, ...]"],
    morph_rows_by_line: dict[int, "list[MorphRow] | tuple[MorphRow, ...]"],
    case_rows_by_line: "dict[int, list[CaseRow] | tuple[CaseRow, ...]] | None" = None,
) -> dict[int, list[SkelRow]]:
    """Mechanically derive the expected skeleton for one parse unit from Layers 2 and 4.

    This is the *checker*, not the artifact's author (see module docstring): its output is
    compared against the LLM's rows by `validate_unit`'s divergence check, never written to
    the artifact itself.

    `case_rows_by_line` is the Layer-2 `case` annex, optional and read at exactly one place —
    rule CZ's slot claim for a gapped-clause remnant. Everywhere else the derivation stays a
    function of Layers 2 and 4 alone, and the annex stays what rule U made it: a third opinion
    consulted only where the other two layers leave the role genuinely undetermined.
    """
    all_rows = [row for no in nos for row in dep_rows_by_line.get(no, ())]
    index = {(row.line, row.token): row for row in all_rows}
    children: dict[tuple[int, int], list[DepRow]] = {}
    for row in all_rows:
        if not (row.head_line == 0 and row.head_token == 0):
            children.setdefault((row.head_line, row.head_token), []).append(row)

    def morph_at(line: int, token: int) -> MorphRow | None:
        rows = morph_rows_by_line.get(line)
        if rows and 1 <= token <= len(rows):
            return rows[token - 1]
        return None

    case_by_pos: dict[tuple[int, int], str] = {
        (row.line, row.token): row.case
        for rows in (case_rows_by_line or {}).values() for row in rows
    }

    # 1. clause-head predicates, plus conj chains that resolve to one.
    #
    # Rule BN: a token Layer 2 calls a **conjunction** that Layer 4 put in a clause-head deprel
    # with no arguments of its own is a connective, not an elided predicate. "**Onde** l'altro
    # lebbroso … rispuose" (inferno 29:124) is `advcl` on `rispuose`, so the derivation minted a
    # predicate at the connective and reported the LLM for not proposing it — a tuple with no
    # arguments in it, which no reading of the line can supply. The `conj` branch below already
    # refuses to promote a coordinating conjunction for the same reason; this is that refusal
    # applied to the clause-head deprels, and the argument test keeps a genuinely gapped clause
    # (a `come` with the compared phrase hanging on it) promoted.
    #
    # Rule AN's clause-head leg: the same reasoning applies to a *non*-conjunct head. "come
    # coltel [fa] le scaglie di scardova" (inferno 29:83) is a gapped comparison hanging on the
    # main clause as `advcl`, with `coltel` promoted and `le scaglie` its `orphan` remnant; there
    # is no elided verb to mint a tuple for, and unlike the `conj` case there is no coordination
    # head whose slots the remnants could fill a second time.
    orphan_heads = {
        (row.head_line, row.head_token)
        for row in all_rows
        if row.deprel == "orphan" and (row.head_line, row.head_token) in index
    }
    predicate_positions: set[tuple[int, int]] = set()
    for row in all_rows:
        if row.deprel not in CLAUSE_HEAD_DEPRELS:
            continue
        pos = (row.line, row.token)
        morph = morph_at(row.line, row.token)
        if (morph is not None and "conjunction" in morph.pos.lower()
                and not any(c.deprel in ARG_DEPRELS for c in children.get(pos, ()))
                and rule_active("BN")):
            continue
        if pos in orphan_heads and (morph is None or not is_verb_pos(morph.pos)) and rule_active("AN"):
            continue
        predicate_positions.add(pos)

    def conj_resolves(row: DepRow, seen: set[tuple[int, int]]) -> bool:
        seen.add((row.line, row.token))
        head = index.get((row.head_line, row.head_token))
        if head is None:
            return False
        if (head.line, head.token) in predicate_positions or head.deprel in CLAUSE_HEAD_DEPRELS:
            return True
        if head.deprel == "conj" and (head.line, head.token) not in seen:
            return conj_resolves(head, seen)
        return False

    # Rule AN: a conjunct carrying an `orphan` child heads a *gapped* clause, not a predicate.
    # "però giri Fortuna la sua rota …, e 'l villan la sua marra" (inferno 15:96): UD promotes
    # `villan` to `conj` and hangs `marra` on it as `orphan`, precisely because the verb that
    # would govern them is elided. Promoting `villan` to a predicate invents one and then hands
    # it the coordination head's subject; the remnants are instead a second set of fillers for
    # the head's own slots, which is what the LLM lists.
    gapped_conjuncts = {
        (row.head_line, row.head_token)
        for row in all_rows
        if row.deprel == "orphan" and (row.head_line, row.head_token) in index
    }

    def promote_conjuncts(verbs_only: bool) -> None:
        for row in all_rows:
            pos = (row.line, row.token)
            if row.deprel != "conj" or pos in predicate_positions:
                continue
            if not conj_resolves(row, set()):
                continue
            # A coordinating conjunction is a function word, never a predicate: Layer 4 routinely
            # attaches a line-initial "E"/"Ed"/"Ma" to the previous clause head with deprel `conj`
            # ("E 'l mio buon duca, che già li er' al petto"), which this rule would otherwise
            # promote. Gapped/elided predicates of other POS stay promoted — those are real.
            conj_morph = morph_at(row.line, row.token)
            if conj_morph is not None and "conjunction" in conj_morph.pos.lower():
                continue
            if verbs_only and (conj_morph is None or not is_verb_pos(conj_morph.pos)
                               or not conj_morph.person):
                continue
            # Rule CA: rule BN's argument test, applied to the `conj` branch. A **non-verb**
            # conjunct with no argument child of its own is not an elided clause: "Sordel rimase
            # e **l'altre genti** forme" (purgatorio 9:58) and "sen venne suso; e **io** per le
            # sue orme" (9:60) promote a noun and a pronoun whose remnants Layer 4 left on the
            # coordination head, so the minted tuple is empty — or, worse, a lone pro-drop `subj`
            # ∅ asserting that the conjunct has a subject other than itself. The reading no
            # tuple can express is the one rules AN and BN already refuse elsewhere; a nominal
            # conjunct that *does* carry arguments ("Ed **elli**: «Vedi …»", inferno 11:15, whose
            # `ccomp` is the elided speech) is a real gapped clause and stays promoted.
            #
            # A `cop`/`aux` child is the tree's own assertion that the conjunct heads a
            # predication ("Tant' **è amara**", inferno 1:7, an adjective conjunct whose subject
            # is pro-drop), so the test is for arguments *or* a copula — the same both-readings
            # evidence rule Y reads on the acceptance side.
            if ((conj_morph is None or not is_verb_pos(conj_morph.pos))
                    and not any(c.deprel in ARG_DEPRELS or c.deprel in _AUX_DEPRELS
                                for c in children.get(pos, ()))
                    and rule_active("CA")):
                continue
            if pos in gapped_conjuncts:
                continue
            predicate_positions.add(pos)

    promote_conjuncts(verbs_only=False)

    # 2. argument-bearing non-auxiliary verbs.
    for row in all_rows:
        pos = (row.line, row.token)
        if pos in predicate_positions:
            continue
        morph = morph_at(row.line, row.token)
        if morph is None or not is_verb_pos(morph.pos) or row.deprel in _AUX_DEPRELS:
            continue
        if any(c.deprel in ARG_DEPRELS for c in children.get(pos, ())):
            predicate_positions.add(pos)

    # Rule BZ: the `conj` chain resolves against the predicate census, so it has to be walked
    # again once pass 2 has added to it. A conjunct is promoted when the chain it hangs on
    # resolves to a predicate, and a predicate reached only by pass 2 — a verb Layer 4 attached
    # with an argument deprel of its own, "com' io rimango sol, **se non restai**" (purgatorio
    # 4:45), where `rimango` is the `obj` of `rimira` and `restai` its `conj` — was not in
    # `predicate_positions` when the chain was first walked. The conjunct was therefore dropped,
    # and a finite verb whose only argument is a pro-drop subject (the one shape pass 2 cannot
    # rescue either, since it has no argument child to be found by) went underived while the LLM
    # proposed it. The 21-25 and 31-34 batches' ordering finding once more, between two passes of
    # the derivation's own predicate census rather than between two acceptance rules.
    #
    # This second walk is restricted to **finite verbs**, and the restriction is rule BN's own
    # test — would the promoted position carry a tuple at all? The first walk promotes a conjunct
    # of any POS, because a nominal conjoined to a clause head is a gapped clause of its own; but
    # a nominal conjoined to something pass 2 promoted is an ordinary coordinate *argument* of
    # that predicate ("addimandò **licenza** di combatter", paradiso 12:95, where `licenza` is the
    # object), and a non-finite conjunct with no argument child of its own ("del comperare e
    # **vender** dentro al templo", paradiso 18:122) yields an empty tuple no reading can fill —
    # the two shapes rules AN and BN stop elsewhere. A *finite* conjunct always has a subject,
    # overt or pro-drop, so its tuple is never empty.
    if rule_active("BZ"):
        promote_conjuncts(verbs_only=True)

    def argument_children(pos: tuple[int, int]) -> list[DepRow]:
        """Rule AM: a predicate's own argument children, plus any stranded on its `cop`/`aux`.

        UD attaches a clause's arguments to its lexical predicate, not to the copula or auxiliary
        that carries the tense — but Layer 4 does not do so consistently: "'n la mente m'è fitta"
        (inferno 15:82) hangs both `la mente` and the dative `m'` on the copula `è`, leaving the
        adjective `fitta` with a bare subject. Reading only the predicate's own children then
        loses arguments the tree does record, and the LLM (which reads the line, not the tree) is
        flagged for naming them. Rule I already walks the same edge in the other direction, from
        an auxiliary up to its lexical head; this is that walk applied to the argument slots.
        """
        own = list(children.get(pos, ()))
        taken = {c.deprel for c in own}
        if rule_active("AM"):
            for aux in children.get(pos, ()):
                if aux.deprel not in _AUX_DEPRELS:
                    continue
                for stranded in children.get((aux.line, aux.token), ()):
                    if (stranded.deprel in ARG_DEPRELS and stranded.deprel not in _SUBJ_DEPRELS
                            and stranded.deprel not in taken):
                        own.append(stranded)
        return own

    def _oblique_role_of(child: DepRow) -> str:
        """`obl:<preposition lemma>` for a token carrying a `case` child, else plain `obl`."""
        case_children = sorted(
            (c for c in children.get((child.line, child.token), ()) if c.deprel == "case"),
            key=lambda c: c.token,
        )
        if case_children:
            prep_morph = morph_at(case_children[0].line, case_children[0].token)
            lemma = _prep_lemma(prep_morph) if prep_morph else ""
            if lemma:
                return f"obl:{_normalize_prep_lemma(lemma)}"
        return "obl"

    result: dict[int, list[SkelRow]] = {no: [] for no in nos}
    for line, token in predicate_positions:
        pred_row = index[(line, token)]
        pred_args: list[SkelRow] = []
        has_subj = False
        for child in argument_children((line, token)):
            if child.deprel in _SUBJ_DEPRELS:
                pred_args.append(SkelRow(line, token, pred_row.word, "subj", child.line, child.token))
                has_subj = True
            elif child.deprel in _DIRECT_ROLE_MAP:
                role = _DIRECT_ROLE_MAP[child.deprel]
                pred_args.append(SkelRow(line, token, pred_row.word, role, child.line, child.token))
            elif child.deprel in ("obl", "obl:agent"):
                role = _oblique_role_of(child)
                pred_args.append(SkelRow(line, token, pred_row.word, role, child.line, child.token))

        # 3. conj shared-subject propagation: inherit the nearest conj-ancestor's subject.
        # Rule AT: only a verb inherits. A *nominal* promoted to predicate is an elided clause of
        # its own — "Così 'l maestro; e io «Alcun compenso», dissi lui … Ed **elli**: «Vedi …»"
        # (inferno 11:13–15), where `elli` is `conj` of `dissi` and is the speaker of the elided
        # second verb of speech, not a second subject of `dissi`'s own. Handing it the head's
        # subject asserts that Dante said what Virgil says; leaving it pro-drop is what the
        # root-position twin of the same frame ("E io: «Maestro, …»", 11:67) already derives.
        own_is_verb = is_verb_pos((morph_at(line, token) or MorphRow("")).pos)
        _subordinated = any(c.deprel == "mark" for c in children.get((line, token), ()))
        if not has_subj and pred_row.deprel == "conj" and (own_is_verb or not rule_active("AT")) and not _subordinated:
            seen = {(line, token)}
            cur = index.get((pred_row.head_line, pred_row.head_token))
            while cur is not None and (cur.line, cur.token) not in seen:
                seen.add((cur.line, cur.token))
                # Rule EF: the walk stops at a **sibling** that has already supplied a subject.
                # Rule AT decides who may inherit and rule DU where the chain is cut by a
                # subordinator; this is about the chain head no longer being the nearest
                # antecedent. "Concreato fu **ordine** … **pura potenza** tenne la parte ima; /
                # nel mezzo **strinse** potenza con atto" (paradiso 29:31-35): five conjuncts
                # hang off `Concreato`, the fourth brings its own subject, and the fifth was
                # still being handed the first one's. Italian shares a subject forward across a
                # coordination, and an intervening conjunct that states its own ends the sharing
                # — "ed **ei** … di sùbito levorsi / e **disser**" (inferno 33:59-61), where the
                # sons say it and the derivation was reaching past them to `io`.
                #
                # It is a **refusal, not a re-assignment**: step 4 then fills the slot with
                # pro-drop ∅ and the authority model decides it, which is rule DA's boundary
                # ("an empty subject slot is a decision procedure having declined"). Handing the
                # conjunct the nearer sibling's subject instead was measured and rejected at
                # **+8/−2** — it is right at paradiso 29:35 and wrong at six other places, where
                # the nearer subject belongs to a clause the coordination does not continue.
                # Censused at 23 subject-less `conj` predicates, of 3658.
                nearer = [c for c in children.get((cur.line, cur.token), ())
                          if c.deprel == "conj" and (c.line, c.token) < (line, token)
                          and any(x.deprel in _SUBJ_DEPRELS
                                  for x in children.get((c.line, c.token), ()))]
                if nearer and rule_active("EF"):
                    break
                inherited = next(
                    (c for c in children.get((cur.line, cur.token), ()) if c.deprel in _SUBJ_DEPRELS),
                    None,
                )
                if inherited is not None:
                    pred_args.append(
                        SkelRow(line, token, pred_row.word, "subj", inherited.line, inherited.token)
                    )
                    has_subj = True
                    break
                if cur.deprel != "conj" or (any(
                    c.deprel == "mark" for c in children.get((cur.line, cur.token), ())
                ) and rule_active("DU")):
                    break
                cur = index.get((cur.head_line, cur.head_token))

        # 4. pro-drop: a finite predicate with still no subject gets an explicit ∅ row.
        if not has_subj:
            own_morph = morph_at(line, token)
            finite = bool(own_morph and own_morph.person)
            if not finite:
                for c in children.get((line, token), ()):
                    if c.deprel in _AUX_DEPRELS:
                        cm = morph_at(c.line, c.token)
                        if cm and cm.person:
                            finite = True
                            break
            if finite:
                pred_args.append(SkelRow(line, token, pred_row.word, "subj", 0, 0))

        # 5. rule AN: the remnants of a gapped conjunct fill this predicate's slots a second
        # time. A remnant carrying its own preposition claims the matching oblique slot ("'l
        # sole avëa il cerchio … lasciato al Tauro e la notte *a lo Scorpio*", purgatorio 25:3);
        # the rest take the remaining slots in the order the predicate's own arguments stand in
        # the line ("lei lo vedere, e me l'ovrare appaga", purgatorio 27:108, where the object
        # precedes the subject in both halves). Run after the subject steps so a gapped clause
        # whose head takes its subject by propagation still has a `subj` slot to fill.
        for conjunct in sorted(
            (c for c in children.get((line, token), ())
             if c.deprel == "conj" and (c.line, c.token) in gapped_conjuncts),
            key=lambda c: (c.line, c.token),
        ):
            # Rule CN: a slot the head clause fills with ∅ goes to the **back** of the queue.
            # The remnants of a gapped clause pair off against the head clause's arguments by
            # the order they stand in the line, and a pro-drop subject stands nowhere — but
            # ∅ = (0, 0) sorts before every real position, so that empty slot was taking the
            # *first* remnant of every gapped clause under a pro-drop predicate. "molti di vita
            # e **sé** di pregio priva" (purgatorio 14:63) was derived with `sé` as the subject
            # of `priva`, against two overt objects in the line and the `case` annex's
            # accusative. A ∅ slot is still offered — "tu … intende de la voglia assoluta, e
            # **io** de l'altra" (paradiso 4:113) is a genuine contrastive subject remnant under
            # a pro-drop head — but only once the overt slots are spoken for.
            slots: list[str] = []
            null_slots: list[str] = []
            for row_ in sorted(pred_args, key=_row_sort_key):
                if not row_.role:
                    continue
                bucket = (null_slots if (row_.arg_line, row_.arg_token) == (0, 0) else slots)
                if row_.role not in slots and row_.role not in null_slots:
                    bucket.append(row_.role)
            if rule_active("CN"):
                slots += null_slots
            else:
                slots = null_slots + slots
            remnants = [conjunct] + sorted(
                (c for c in children.get((conjunct.line, conjunct.token), ())
                 if c.deprel == "orphan"),
                key=lambda c: (c.line, c.token),
            )
            # A promoted conjunct that carries its own preposition is an oblique, so the subject
            # is shared with the head clause rather than gapped: "come il tempo tegna in cotal
            # testo le sue radici e *ne li altri* le fronde" (paradiso 27:118).
            if any(c.deprel == "case" for c in children.get((conjunct.line, conjunct.token), ())):
                slots = [s for s in slots if s != "subj"]
            assigned: list[tuple[str, DepRow]] = []
            for remnant in list(remnants):
                if not any(c.deprel == "case"
                           for c in children.get((remnant.line, remnant.token), ())):
                    continue
                label = _oblique_role_of(remnant)
                if label in slots:
                    slots.remove(label)
                    remnants.remove(remnant)
                    assigned.append((label, remnant))
            # Rule CZ: a remnant the `case` annex assigns a case to claims the slot that case
            # names, before the queue below hands out what is left. What the queue does is pair
            # remnants against slots in **role-rank** order — subject, then object, then the
            # obliques — which reads Dante as always putting the gapped clause's remnants in the
            # canonical order. He does not. "lei lo vedere, e me l'ovrare appaga"
            # (purgatorio 27:108) puts the object first in both halves, and the rank queue gave
            # `lei` the subject slot: *she* satisfies the seeing, the reverse of the line. The
            # annex reads `lei` as `accusative`, which settles it, and settles it without
            # assuming an order — "onde fa l'arco il Sole e Delia il cinto" (paradiso 29:78)
            # inverts the two halves chiastically, so pairing the remnants by where they stand
            # would get *that* line wrong, and there the annex holds no value for either proper
            # noun and the rank queue is left to decide, correctly. This is rule U's third
            # opinion moved to the one place in `derive_unit` that is openly guessing; unlike
            # rule U it runs in both directions, because here the annex is not overruling a
            # Layer-4 label — Layer 4 assigns a gapped remnant no role at all.
            if rule_active("CZ"):
                for remnant in list(remnants):
                    value = case_by_pos.get((remnant.line, remnant.token))
                    if not value or SLOT_SEP in value:
                        continue
                    claimed = [s for s in slots if s in ("subj", "obj", "iobj")
                               and _case_supports_role(value, s)]
                    if len(claimed) == 1:
                        slots.remove(claimed[0])
                        remnants.remove(remnant)
                        assigned.append((claimed[0], remnant))
            assigned.extend(zip(slots, remnants))
            for role, remnant in assigned:
                pred_args.append(
                    SkelRow(line, token, pred_row.word, role, remnant.line, remnant.token)
                )

        if not pred_args:
            pred_args.append(SkelRow(line, token, pred_row.word, "", 0, 0))
        result.setdefault(line, []).extend(pred_args)

    for rows in result.values():
        rows.sort(key=_row_sort_key)
    return result


_CONTROL_CHAIN_LIMIT = 8


def _control_subject_candidates(
    pos: tuple[int, int], derived_by_pred: dict[tuple[int, int], list[SkelRow]],
    dep_index_by_pos: dict[tuple[int, int], DepRow],
    morph_rows: "dict[int, list[MorphRow]] | None" = None,
) -> tuple[set[tuple[int, int]], bool]:
    """Rule V: the subjects a **non-finite** predicate can inherit, walking its dep head chain.

    `derive_unit` only ever reads a predicate's own children, so a predicate with no `nsubj` of
    its own and no finite morphology gets no `subj` row at all — it is silent, not asserting
    that the predicate has no subject. Every such predicate does have one, and Italian fixes it
    structurally in exactly two ways this collects:

    - **Control / raising**: an `xcomp`/`ccomp`/`advcl`/`conj` chain of non-finite predicates
      takes its subject from an argument of the matrix predicate. Which argument is lexical
      (subject control "vuole partire", object control "fé molte genti viver grame", the
      causative's dative causee "ella mi fa tremar"), so all of `subj`/`obj`/`iobj` are
      candidates, at every link up to the first ancestor that has a subject of its own.
    - **Adnominal participle** (`acl`): the subject is the nominal the participle modifies —
      "le sue spalle *vestite* de' raggi", "io, *vinto* dal sonno", "prieghi *fatti* a Dio".

    Membership in this set is an acceptance, never an assertion: the derivation still says
    nothing, and a subject from outside the set stays flagged as a genuine disagreement.

    Returns `(candidates, unresolved)`. `unresolved` is true when the walk reaches a matrix
    predicate whose own subject derive_unit could only give as pro-drop ∅ ("chi ... *parea*
    fioco"): the controller is then a referent the derivation never resolved, so it cannot
    adjudicate the LLM's resolution of it either — exactly the case the pro-drop branch of
    `_apply_subj_authority` already treats as LLM-authoritative.
    """
    candidates: set[tuple[int, int]] = set()
    cur = dep_index_by_pos.get(pos)
    seen = {pos}
    for _ in range(_CONTROL_CHAIN_LIMIT):
        if cur is None:
            break
        head_pos = (cur.head_line, cur.head_token)
        if head_pos == (0, 0) or head_pos in seen:
            break
        seen.add(head_pos)
        if cur.deprel in ("acl", "acl:relcl"):
            candidates.add(head_pos)
            # Rule CE: the antecedent and the relative pronoun of its own relative clause are
            # one referent, so either of them names this participle's subject. "O superbi
            # cristian … **che**, de la vista de la mente **infermi**, fidanza avete"
            # (purgatorio 10:122): Layer 4 hangs both `infermi` and `avete` on `cristian` as
            # `acl:relcl`, and the LLM — reading a relative clause with a depictive inside it —
            # gives the depictive the clause's own subject, the relative `che`. Rule V's walk
            # reaches the antecedent and stops one edge short of the pronoun that stands for it.
            # This is the argument-identity route the Inferno 16-25 batches named and left
            # unopened; kept to the relative pronoun forms, so an ordinary nominal subject of
            # the relative clause (a different referent) stays flagged.
            candidates.update(
                (r.line, r.token)
                for r in dep_index_by_pos.values()
                if r.deprel in _SUBJ_DEPRELS
                and r.word.lower().rstrip("'") in _RELATIVE_PRONOUNS
                and (rel := dep_index_by_pos.get((r.head_line, r.head_token))) is not None
                and rel.deprel == "acl:relcl"
                and (rel.head_line, rel.head_token) == head_pos
            )
        # Rule CF: the controller a fused clitic hides. "anzi ad aprir ch'a **tenerla** serrata"
        # (purgatorio 9:128): the object controlling `serrata` is the `la` inside `tenerla`, and
        # Layer 1 gives it no position of its own — the only citation for it is the host token,
        # which is what the LLM writes and what rules AL and AS already read as two roles on one
        # position. Rule V collects the matrix predicate's derived `obj`, but a clitic fused into
        # the verb never becomes one, so object control across this edge had no candidate at all.
        # Censused at 66 `xcomp` edges under a fused verb+pronoun host.
        if morph_rows is not None:
            head_line_rows = morph_rows.get(head_pos[0])
            if (head_line_rows and 1 <= head_pos[1] <= len(head_line_rows)
                    and "+pronoun" in head_line_rows[head_pos[1] - 1].pos):
                candidates.add(head_pos)
        head_rows = derived_by_pred.get(head_pos, ())
        # Rule CJ: the controller Layer 4 labelled `obl`. The three core roles were the whole
        # candidate set, but Italian's controller is often a dative or a genitive that this
        # corpus's Layer 4 writes as an oblique: "s'avacci **lor** divenir **sante**"
        # (purgatorio 6:27), where the possessor of the nominalized infinitive is the subject of
        # its predicate adjective; "**detto n'**avea **beati**" (22:5), object control whose
        # object is the `ne` clitic Layer 4 marks `obl`; "dandole biasmo" (inferno 7:93). The
        # role name is Layer 4's notation for the edge, not a claim that an oblique cannot
        # control — and this set is an *acceptance*, never an assertion, so widening it accepts
        # a reading the tree leaves open rather than asserting one.
        candidates.update(
            (row.arg_line, row.arg_token)
            for row in head_rows
            if (row.role in ("subj", "obj", "iobj") or row.role.startswith("obl"))
            and (row.arg_line, row.arg_token) != (0, 0)
        )
        head_subj = [row for row in head_rows if row.role == "subj"]
        if any((row.arg_line, row.arg_token) == (0, 0) for row in head_subj):
            return candidates, True
        if head_subj:
            break
        cur = dep_index_by_pos.get(head_pos)
    return candidates, False


def _inherited_subject(
    pos: tuple[int, int], dep_index_by_pos: dict[tuple[int, int], DepRow]
) -> bool:
    """Whether `derive_unit` could only have given `pos` a subject by conj propagation (step 3):
    the predicate is a `conj` and has no subject child of its own."""
    row = dep_index_by_pos.get(pos)
    if row is None or row.deprel != "conj":
        return False
    return not any(
        r.deprel in _SUBJ_DEPRELS and (r.head_line, r.head_token) == pos
        for r in dep_index_by_pos.values()
    )


def _finite_head_of(
    pos: tuple[int, int], children_by_pos: "dict[tuple[int, int], list[DepRow]]",
    morph_rows: dict[int, list[MorphRow]],
) -> tuple[int, int]:
    """The token that actually carries `pos`'s person/number: itself, or — for a non-finite
    predicate like `vedere` in "là i **potrai** vedere" — its `aux`/`cop` child. Mirrors the
    finiteness test `derive_unit`'s step 4 (pro-drop) already runs, so subject-agreement checks
    on a periphrastic predicate look at the token Layer 2 actually marked person/tense on."""
    own_morph = None
    line_rows = morph_rows.get(pos[0])
    if line_rows and 1 <= pos[1] <= len(line_rows):
        own_morph = line_rows[pos[1] - 1]
    if own_morph and own_morph.person:
        return pos
    for child in children_by_pos.get(pos, ()):
        if child.deprel in _AUX_DEPRELS:
            child_line_rows = morph_rows.get(child.line)
            if child_line_rows and 1 <= child.token <= len(child_line_rows):
                child_morph = child_line_rows[child.token - 1]
                if child_morph and child_morph.person:
                    return (child.line, child.token)
    return pos


def _donor_predicate_disagrees(
    pos: tuple[int, int], d_subj: tuple[int, int],
    dep_index_by_pos: dict[tuple[int, int], DepRow],
    children_by_pos: "dict[tuple[int, int], list[DepRow]]",
    morph_rows: "dict[int, list[MorphRow]] | None",
) -> bool:
    """Rule DO: rule AG's test, asked of the two *predicates* instead of the subject nominal.

    Rule AG drops a `conj`-inherited subject whose Layer-2 person/number contradicts the
    predicate it lands on. That catches nothing when the inherited nominal has no person of its
    own to contradict with — a third-person noun agrees with every third-person verb, and 461 of
    the 1370 candidates are undecidable for exactly this reason. But two finite verbs sharing one
    subject must agree *with each other*, and that is decidable whenever both carry person and
    number, whatever the nominal is: "Cunizza **fui** chiamata … a me medesma **indulgo** la
    cagion di mia sorte, e non mi **noia**" (paradiso 9:35), where step 3 walks a chain of 1sg
    verbs onto a 3sg one and hands `noia` the subject of "I was called". Whoever vexes is not
    whoever forgives, and no reading of Layer 2 makes it so.

    The donor is the predicate the inherited nominal is actually a child of, read through
    `_finite_head_of` at both ends so a periphrasis is compared on the word Layer 2 marked. Both
    ends must carry person *and* number — an unmarked form concludes nothing, exactly as
    "undecidable" does in `subject_agreement`.
    """
    if morph_rows is None:
        return False
    donor_row = dep_index_by_pos.get(d_subj)
    if donor_row is None:
        return False
    donor = (donor_row.head_line, donor_row.head_token)
    if donor == pos or donor == (0, 0):
        return False

    def features(p: tuple[int, int]) -> tuple[str, str] | None:
        head = _finite_head_of(p, children_by_pos, morph_rows)
        rows = morph_rows.get(head[0])
        if not rows or not 1 <= head[1] <= len(rows):
            return None
        m = rows[head[1] - 1]
        if not (m.person and m.number and "verb" in m.pos):
            return None
        return (m.person, m.number)

    a, b = features(donor), features(pos)
    return a is not None and b is not None and a != b


def _accept_control_subjects(
    g: dict[tuple[int, int], str], pos: tuple[int, int],
    derived_by_pred: dict[tuple[int, int], list[SkelRow]],
    dep_index_by_pos: dict[tuple[int, int], DepRow],
    morph_rows: dict[int, list[MorphRow]] | None,
    np_spans_by_line: "dict[int, list[NPSpan]] | None" = None,
) -> None:
    if not rule_active("V"):
        return
    """Rule V's acceptance, applied to every `subj` citation `g` holds for `pos`.

    Used where the derivation asserts **no** subject for a predicate: either because it is
    non-finite (rule V's own case) or because rule AG has just dropped an inherited subject that
    contradicts it (rule CL). Each citation is validated against the control/raising candidate
    set rather than accepted outright, and rule BB's plural: a slot rule V accepts it accepts for
    every citation that fills it.
    """
    g_subjs = [a for a, role in g.items() if role == "subj"]
    if not g_subjs:
        return
    reachable, unresolved = _control_subject_candidates(pos, derived_by_pred,
                                                        dep_index_by_pos, morph_rows)
    candidates = None if unresolved else {(0, 0)} | reachable
    for g_subj in g_subjs:
        # …and the citation is tested through rule C's normalization too, since the collapse
        # runs after this and would otherwise rewrite an unaccepted conjunct/`flat` member
        # onto the very position rule V does accept ("Bellincion **Berti** vid' io andar",
        # paradiso 15:112, where the matrix object is cited by the name's second word).
        # Rule DF: …and through rule AI's normalization too, for the same reason. Rule V's
        # candidates are Layer 4's attachment points; the LLM is told to cite a noun phrase by
        # its Layer-3 head, and the two do not always land on the same token of one phrase —
        # "l'altre tre si fero avanti, **danzando**" (purgatorio 31:132), where Layer 4 makes
        # `altre` the subject of `fero` and Layer 3 heads `[l'altre tre]` on `tre`. Rule AI
        # already reads that pair as one argument named twice, but it runs downstream of this
        # and only pairs citations of a role the derivation *has* — which for a gerund's
        # inherited subject is exactly the role it does not. The ordering finding again, in the
        # form the Purgatorio 6-10 batch named: ask which normalization has already run on the
        # citation a gate compares.
        if (candidates is None or g_subj in candidates
                or _coordination_head(g_subj, dep_index_by_pos) in candidates
                or (np_spans_by_line is not None
                    and any(_np_head_equivalent(g_subj, c, np_spans_by_line)
                            for c in candidates))):
            g.pop(g_subj, None)


_ELIDED_COPULA_DEPRELS = frozenset({"conj", "appos", "attr"})

# Rule AY: the children that make an `amod` adjective an adjective *phrase* — one governing an
# argument of its own — rather than a bare attributive.
_ADJECTIVE_COMPLEMENT_DEPRELS = frozenset(
    {"obl", "obl:agent", "nmod", "obj", "iobj", "ccomp", "xcomp", "advcl", "nsubj"}
)

# Rule Z: the deprels that put a token in an argument or adjunct *slot* rather than at a clause
# head. A verb form sitting in one of these is a predicate no reading disputes — the derivation
# is silent about it only because `derive_unit`'s rule 1 keys on `CLAUSE_HEAD_DEPRELS` and its
# rule 2 needs the verb to carry an argument child of its own.
_NOMINAL_SLOT_DEPRELS = frozenset({"obl", "obl:agent", "nmod", "nsubj", "nsubj:pass", "obj",
                                   "iobj", "advmod"})

_CONJ_WALK_LIMIT = 8


def _coordination_head(
    pos: tuple[int, int], dep_index_by_pos: dict[tuple[int, int], DepRow],
    morph_pos_by_position: "dict[tuple[int, int], str] | None" = None,
) -> tuple[int, int]:
    """Rule C: the head of `pos`'s coordination, walking `conj` edges up (bounded).

    Rule AP walks `appos` with them. An apposition is the same argument named a second time —
    "onde omicide e ciascun che mal fiere, guastatori e predon, **tutti** tormenta lo giron
    primo" (inferno 11:38), where `tutti` sums up the coordination it is appositive to. Layer 4
    records the second naming as `appos` off the first, exactly as it records a conjunct as
    `conj`, and neither is a second argument of the verb; the LLM cites whichever of the two
    reads as the argument. Collapsing them together is the same notation normalization rule C
    already makes for coordination, and it preserves roles, so a genuine role disagreement on
    the merged position still surfaces.

    Rule BE walks `flat` with them, on the same reasoning one relation further in: a multiword
    name is one nominal spread over several tokens ("son Vanni Fucci", inferno 24:125, where the
    LLM gives the predicate an `attr` on each half and the tree only ever attaches the first).
    `flat` is UD's *headless* multiword relation, so its members are not modifiers of the opening
    word — they are the same nominal, and citing any of them cites it.

    **Rule CD** stops the walk where the coordination stops being one of arguments. UD promotes a
    conjunct to the *clause* head when it reads the coordination as clausal, so a `conj` step
    from a nominal onto a verb leaves the argument's own coordination and enters the predicates':
    "sen venne suso; e **io** per le sue orme" (purgatorio 9:60) walks `io` → `venne` → `tolse` →
    `rimase` and rewrites a subject citation into a citation of a predicate three lines up, which
    no reading of the line asserts. Rule CC accepts such a conjunct in the slot the LLM gives it,
    and can only see it if the collapse has left it alone.
    """
    seen = {pos}
    cur = pos
    for _ in range(_CONJ_WALK_LIMIT):
        row = dep_index_by_pos.get(cur)
        if row is None or row.deprel not in ("conj", "appos", "flat", "compound"):
            break
        head = (row.head_line, row.head_token)
        if head in seen or head not in dep_index_by_pos:
            break
        if row.deprel == "conj" and morph_pos_by_position is not None:
            head_row = dep_index_by_pos[head]
            cur_pos, head_pos = morph_pos_by_position.get(cur, ""), morph_pos_by_position.get(head, "")
            if (cur_pos and head_pos and not is_verb_pos(cur_pos) and is_verb_pos(head_pos)
                    and head_row.deprel not in ARG_DEPRELS):
                break
        seen.add(head)
        cur = head
    return cur


def _collapse_coordination(
    by_arg: dict[tuple[int, int], str], pos: tuple[int, int],
    dep_index_by_pos: dict[tuple[int, int], DepRow],
    morph_pos_by_position: "dict[tuple[int, int], str] | None" = None,
) -> dict[tuple[int, int], str]:
    """Rule C: map every argument citation onto its coordination head, de-duplicating.

    "si ciberà di terra e di sapïenza" — the LLM lists both conjuncts as `obj`, `derive_unit`
    reads only the predicate's direct children and so sees the first only. Enumerating conjuncts
    on the derived side instead was measured net-zero (PLAN.md Rule A): the LLM's own enumeration
    is inconsistent, so the divergence is a notation mismatch and normalization is the
    instrument. Roles are preserved, so a genuine role disagreement still surfaces.

    **Rule DE** decides *whose* role survives when the head is cited too. Coordination in this
    corpus is not always of like with like: a conjunct carries its own `case` marker as readily as
    it shares the head's, and 98 `conj` nominals corpus-wide have one whose lemma differs — "la
    flagellò **dal capo** infin **le piante**" (purgatorio 32:156), where Layer 4 hangs `piante`
    off `capo` as a `conj` with `infin` as its own `case`. The LLM names both, correctly, with
    two different prepositions; the collapse then had to pick one by role rank and picked the
    conjunct's, so the position the derivation reports with the *head's* preposition came back a
    `role_mismatch`. The head's own citation is the one that names the head, and a conjunct's role
    is only riding along on it — so a collapsed role never displaces an uncollapsed one. Rank
    still decides between two collapsed conjuncts, which is the case rule C was written for.

    The gate is the conjunct's **own** `case` marker, not the collapse alone: without it the rule
    also fires on an apposition whose head is the emptier of the two words ("che **l'uno** a
    l'altro raggio non ingombra", purgatorio 3:30, where the LLM's role for the `appos` is the
    right one), and rank is the better answer there.
    """
    out: dict[tuple[int, int], str] = {}
    from_head: dict[tuple[int, int], bool] = {}
    for arg, role in by_arg.items():
        key = arg
        if arg != (0, 0):
            head = _coordination_head(arg, dep_index_by_pos, morph_pos_by_position)
            if head != pos:  # never collapse an argument onto its own predicate
                key = head
        uncollapsed = key == arg
        if key not in out:
            out[key], from_head[key] = role, uncollapsed
            continue
        separately_marked = _distinctly_marked_conjunct(arg, key, dep_index_by_pos)
        if uncollapsed and not from_head[key] and separately_marked:
            out[key], from_head[key] = role, True  # rule DE: the head names its own role
        elif (uncollapsed == from_head[key] or not separately_marked) and (
                (_role_rank(role), role) < (_role_rank(out[key]), out[key])):
            out[key] = role  # rule C's rank tie-break, between citations of one provenance
    return out


def _distinctly_marked_conjunct(
    arg: tuple[int, int], head: tuple[int, int],
    dep_index_by_pos: dict[tuple[int, int], DepRow],
) -> bool:
    """Rule DE's gate: `arg` collapses onto `head` but carries a `case` marker of its own whose
    word differs from the head's, so the two are separately-marked obliques rather than one
    phrase named twice. Censused at 98 `conj` nominals corpus-wide."""
    if arg == head or arg == (0, 0):
        return False

    def marker(p: tuple[int, int]) -> str | None:
        for r in dep_index_by_pos.values():
            if r.deprel == "case" and (r.head_line, r.head_token) == p:
                return r.word.lower().rstrip("'")
        return None

    own = marker(arg)
    return own is not None and own != marker(head)


def _conj_shared_argument(
    pos: tuple[int, int], arg: tuple[int, int], grole: str,
    dep_index_by_pos: dict[tuple[int, int], DepRow],
    derived_by_pred: dict[tuple[int, int], list[SkelRow]],
    d: dict[tuple[int, int], str],
) -> bool:
    """Rule AJ: an argument gapped from the coordination head onto this conjunct.

    `derive_unit`'s step 3 propagates a shared **subject** across a coordination and nothing else,
    but Italian gaps objects and datives just as freely — "li rami *schianta*, *abbatte* e *porta*
    fori" (inferno 9:70), "m'hai sicurtà *renduta* e *tratto* d'alto periglio" (8:98), "lo spirito
    lasso *conforta* e *ciba*" (8:107). The LLM restates the shared argument under each conjunct,
    which is the correct reading; the derivation, reading only each predicate's own children,
    sees it once and reports the restatements as extra arguments.

    Accepted whatever role the conjunct assigns it: gapping genuinely changes the role, as in
    "ha *tolto* loro, e *posti* a questa zuffa" (7:59), where `loro` is the head's `iobj` and the
    conjunct's `obj`. The gate that keeps this from absorbing real disagreements is on the *slot*,
    not the role — the conjunct must have no derived filler of that role of its own. `subj` is
    excluded throughout: step 3 and the authority model (rules AC, AG, AH) already own it.
    """
    if grole == "subj" or arg == (0, 0) or grole in d.values():
        return False
    cluster: set[tuple[int, int]] = set()
    frontier = [pos]
    while frontier and len(cluster) < _CONJ_WALK_LIMIT * 2:
        cur = frontier.pop()
        if cur in cluster:
            continue
        cluster.add(cur)
        row = dep_index_by_pos.get(cur)
        if row is not None and row.deprel == "conj":
            head = (row.head_line, row.head_token)
            if head in dep_index_by_pos:
                frontier.append(head)
        for other in dep_index_by_pos.values():
            if other.deprel == "conj" and (other.head_line, other.head_token) == cur:
                frontier.append((other.line, other.token))
    cluster.discard(pos)
    return any(
        (r.arg_line, r.arg_token) == arg and r.role not in ("", "subj")
        for member in cluster
        for r in derived_by_pred.get(member, ())
    )


def _np_head_equivalent(
    a: tuple[int, int], b: tuple[int, int], np_spans_by_line: dict[int, list[NPSpan]]
) -> bool:
    """Rule AI: whether two argument citations are the same Layer-3 noun phrase named twice.

    Layer 3's `head` and Layer 4's attachment point are computed independently and do not always
    land on the same token of one NP. `SYSTEM_PROMPT` tells the model to "prefer a noun phrase's
    head token", so the LLM cites Layer 3's head and `derive_unit` cites whatever Layer 4 hung the
    argument edge on — "Qui con **più di mille** giaccio" (inferno 10:118), where the NP
    `[più di mille]` has `head=più` and Layer 4 attaches `mille`. One argument then costs two
    violations, a `missing_arg` and an `extra_arg`, without either side having read the line
    differently.

    True only when both positions lie inside a single NP span **and** one of them is that span's
    head: two tokens that merely share a line, or two nominals inside one span neither of which is
    its head, are not each other's alternative name.
    """
    if a == (0, 0) or b == (0, 0) or a == b or a[0] != b[0]:
        return False
    for span in np_spans_by_line.get(a[0], ()):
        if span.start <= a[1] <= span.end and span.start <= b[1] <= span.end:
            if span.head in (a[1], b[1]):
                return True
    return False


def _merge_auxiliary_citations(
    by_arg: dict[tuple[int, int], str], pos: tuple[int, int],
    dep_index_by_pos: dict[tuple[int, int], DepRow],
) -> dict[tuple[int, int], str]:
    """Rule AQ: map an argument citation landing on an `aux`/`cop` onto its lexical head.

    "credendo ch'altro ne **volesse** dire" (inferno 13:110): the complement clause is headed by
    `dire`, and `volesse` is its `aux`; the LLM cites the finite word it can see carrying the
    tense, the derivation cites the lexical verb Layer 4 made the head. The two name one clause.
    Rule I already treats the same edge as identity when the *predicate* of a tuple lands on an
    auxiliary; this is that identity applied to the argument slot, and roles are preserved so a
    genuine role disagreement on the merged position still surfaces.
    """
    out: dict[tuple[int, int], str] = {}
    for arg, role in by_arg.items():
        key = arg
        if arg != (0, 0):
            row = dep_index_by_pos.get(arg)
            if row is not None and row.deprel in _AUX_DEPRELS:
                head = _aux_head(arg, dep_index_by_pos)
                if head != pos and head != arg:
                    key = head
        prev = out.get(key)
        if prev is None or (_role_rank(role), role) < (_role_rank(prev), prev):
            out[key] = role
    return out


def _nested_in_named_phrase(
    arg: tuple[int, int], g: dict[tuple[int, int], str], d: dict[tuple[int, int], str],
    np_spans_by_line: "dict[int, list[NPSpan]] | None",
) -> bool:
    """Rule BR: a derived argument buried inside a Layer-3 noun phrase whose head is another
    derived argument of the same predicate, and the LLM named that head."""
    if np_spans_by_line is None or arg == (0, 0):
        return False
    for span in np_spans_by_line.get(arg[0], ()):
        if not (span.start <= arg[1] <= span.end) or span.head == arg[1]:
            continue
        outer = (arg[0], span.head)
        if outer in d and outer in g:
            return True
    return False


def _conjunct_named_by_phrase_head(
    arg: tuple[int, int], grole: str, d: dict[tuple[int, int], str],
    dep_index_by_pos: dict[tuple[int, int], DepRow] | None,
    morph_pos_by_position: dict[tuple[int, int], str] | None,
    np_spans_by_line: "dict[int, list[NPSpan]] | None",
) -> bool:
    """Rule DZ: rule AI's NP-head equivalence read **through** rule C's coordination collapse."""
    if np_spans_by_line is None or arg == (0, 0):
        return False
    for span in np_spans_by_line.get(arg[0], ()):
        if span.head != arg[1]:
            continue
        for tok in range(span.start, span.end + 1):
            member = (arg[0], tok)
            if member == arg:
                continue
            head = _coordination_head(member, dep_index_by_pos, morph_pos_by_position)
            if head != member and d.get(head) == grole:
                return True
    return False


def _merge_np_head_citations(
    g: dict[tuple[int, int], str], d: dict[tuple[int, int], str],
    np_spans_by_line: dict[int, list[NPSpan]],
) -> None:
    """Rule AI: re-key a given citation onto the derived one when `_np_head_equivalent` says the
    two name one NP in the same role. Mutates `g` in place."""
    roles = {role for arg, role in d.items() if arg not in g}
    for role in sorted(roles):
        unmatched_d = sorted(a for a, r in d.items() if r == role and a not in g)
        unmatched_g = sorted(a for a, r in g.items() if r == role and a not in d)
        for a_d in unmatched_d:
            match = next((a for a in unmatched_g if _np_head_equivalent(a, a_d, np_spans_by_line)),
                         None)
            if match is None:
                continue
            unmatched_g.remove(match)
            del g[match]
            g[a_d] = role


_FLOATING_QUANTIFIERS = frozenset({
    "tutto", "quanto", "ambedue", "amendue", "entrambi", "ciascuno", "ognuno",
})
_ADNOMINAL_DEPRELS = frozenset({"amod", "nmod", "det", "det:poss", "nummod"})
_QUANTIFIER_POS = frozenset({"adjective", "numeral", "pronoun"})


def _floating_quantifier_of(
    arg: tuple[int, int], target: tuple[int, int],
    dep_index_by_pos: dict[tuple[int, int], DepRow] | None,
    morph_lemma_by_position: dict[tuple[int, int], str] | None,
    morph_pos_by_position: dict[tuple[int, int], str] | None,
) -> bool:
    """Rule EI: whether `arg` is a **floating quantifier** of the nominal at `target`."""
    if (arg == (0, 0) or target == (0, 0) or arg == target
            or dep_index_by_pos is None or morph_lemma_by_position is None):
        return False
    if morph_lemma_by_position.get(arg, "").lower() not in _FLOATING_QUANTIFIERS:
        return False
    if morph_pos_by_position is None:
        return False
    if morph_pos_by_position.get(arg, "").strip().lower() not in _QUANTIFIER_POS:
        return False
    row = dep_index_by_pos.get(arg)
    if row is None or row.deprel not in _ADNOMINAL_DEPRELS:
        return False
    head = (row.head_line, row.head_token)
    if head == target:
        return True
    return _coordination_head(head, dep_index_by_pos, morph_pos_by_position) == target


def _merge_floating_quantifier_citations(
    g: dict[tuple[int, int], str], d: dict[tuple[int, int], str],
    dep_index_by_pos: dict[tuple[int, int], DepRow] | None,
    morph_lemma_by_position: dict[tuple[int, int], str] | None,
    morph_pos_by_position: dict[tuple[int, int], str] | None,
) -> None:
    """Rule EI: re-key a given citation onto the derived one when `_floating_quantifier_of` says
    the first is a floating quantifier of the second in the same role. Mutates `g` in place."""
    roles = {role for arg, role in d.items() if arg not in g}
    for role in sorted(roles):
        unmatched_d = sorted(a for a, r in d.items() if r == role and a not in g)
        unmatched_g = sorted(a for a, r in g.items() if r == role and a not in d)
        for a_d in unmatched_d:
            match = next(
                (a for a in unmatched_g
                 if _floating_quantifier_of(a, a_d, dep_index_by_pos, morph_lemma_by_position,
                                            morph_pos_by_position)),
                None)
            if match is None:
                continue
            unmatched_g.remove(match)
            del g[match]
            g[a_d] = role


def _adverb_cluster_head(
    arg: tuple[int, int],
    dep_index_by_pos: dict[tuple[int, int], DepRow] | None,
    children_by_pos: dict[tuple[int, int], list[DepRow]] | None,
    morph_pos_by_position: dict[tuple[int, int], str] | None,
) -> tuple[int, int] | None:
    """The head of the adverb-preposition cluster `arg` belongs to, or None — see rule BJ."""
    if dep_index_by_pos is None or children_by_pos is None or morph_pos_by_position is None:
        return None
    row = dep_index_by_pos.get(arg)
    if row is None:
        return None
    head = (row.head_line, row.head_token)
    host = dep_index_by_pos.get(head)
    if host is None:
        return None
    if host.deprel not in ("advmod", "obl") and not (host.deprel.startswith("obl:") and bool(re.fullmatch(r"obl:[a-zàèéìòù']+", host.deprel))):
        return None
    if "adverb" not in morph_pos_by_position.get(head, "").lower():
        return None
    if row.deprel in ("nmod", "obl") or (row.deprel.startswith("obl:") and bool(re.fullmatch(r"obl:[a-zàèéìòù']+", row.deprel))):
        kids = children_by_pos.get(arg, ())
        if any(k.deprel == "case" for k in kids):
            return head
        if not any(k.deprel == "mark" for k in kids):
            return head
    if row.deprel == "advmod" and "adverb" in morph_pos_by_position.get(arg, "").lower():
        return head
    return None


def _merge_adverb_cluster_citations(
    g: dict[tuple[int, int], str], pos: tuple[int, int],
    dep_index_by_pos: dict[tuple[int, int], DepRow],
    children_by_pos: dict[tuple[int, int], list[DepRow]] | None,
    morph_pos_by_position: dict[tuple[int, int], str] | None,
) -> dict[tuple[int, int], str]:
    """Rule BJ: the adverb-preposition cluster names one oblique, from either of its two words."""
    if children_by_pos is None or morph_pos_by_position is None:
        return g

    def cluster_head(arg: tuple[int, int]) -> tuple[int, int]:
        head = _adverb_cluster_head(arg, dep_index_by_pos, children_by_pos, morph_pos_by_position)
        if head is None or head == pos:
            return arg
        host = dep_index_by_pos[head]
        return head if (host.head_line, host.head_token) == pos else arg

    out: dict[tuple[int, int], str] = {}
    for arg, role in g.items():
        key = arg
        if arg != (0, 0) and (role == "obl" or role.startswith("obl:")):
            key = cluster_head(arg)
        prev = out.get(key)
        if prev is None or (_role_rank(role), role) < (_role_rank(prev), prev):
            out[key] = role
    return out


def _aux_head(
    pos: tuple[int, int], dep_index_by_pos: dict[tuple[int, int], DepRow]
) -> tuple[int, int]:
    """Rule I: the lexical head an `aux`/`aux:pass`/`cop` token attaches to (bounded walk)."""
    seen = {pos}
    cur = pos
    for _ in range(_CONJ_WALK_LIMIT):
        row = dep_index_by_pos.get(cur)
        if row is None or row.deprel not in _AUX_DEPRELS:
            break
        head = (row.head_line, row.head_token)
        if head in seen or head not in dep_index_by_pos:
            break
        seen.add(head)
        cur = head
    return cur


def _prep_stack_nominal(
    arg: tuple[int, int], dep_index_by_pos: dict[tuple[int, int], DepRow]
) -> tuple[int, int]:
    """Rule BV: the nominal a multiword preposition's own words belong to (bounded walk)."""
    row = dep_index_by_pos.get(arg) or DepRow(0, 0, "", "", 0, 0)
    if row.deprel == "case":
        if not any(r.deprel == "fixed" and (r.head_line, r.head_token) == arg
                   for r in dep_index_by_pos.values()):
            return arg
    elif row.deprel != "fixed":
        return arg
    seen = {arg}
    cur = arg
    for _ in range(_CONJ_WALK_LIMIT):
        row = dep_index_by_pos.get(cur)
        if row is None or row.deprel not in ("fixed", "case"):
            break
        head = (row.head_line, row.head_token)
        if head in seen or head not in dep_index_by_pos:
            break
        seen.add(head)
        cur = head
    return cur
