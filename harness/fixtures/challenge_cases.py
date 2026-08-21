"""Curated challenge fixtures for the Stage 1 benchmark (`runner/PLAN.md` §5.1).

One entry per parse unit: coordinates plus a phenomenon category. The table is
**frozen curated data**, not a query — it was authored by deterministically mining
the corpus (2026-08-22) so every unit is a verified exemplar of its category, and
is committed verbatim so fixture sets stay comparable across evaluation runs.

Categories (`CATEGORIES`, one per case):
- `historical`: units hosting positions documented in `skel/CORRECTIONS.md`
  (censuses §P15 final residue closure, §P13 spurious clausal complements, §P5
  verbless speech frames). These are the primary benchmark: the harness must
  self-resolve them from linguistic first principles, without the corrections.
- `control`: control verbs / infinitival complement propagation (`xcomp`).
- `coordination`: predicates sharing arguments across conjuncts (same-role
  argument pairs on one predicate).
- `relative_chain`: units carrying at least two `acl:relcl` dependencies.
- `quotes`: units inside direct-speech spans (speech frames, vocatives).
- `hyperbaton`: long-distance discontinuous dependencies (an argument cited >= 45
  linear token positions away from its predicate).

This module serves **operators only**: nothing under `harness/runner/` reads it,
and no gold Layer 5 data is stored here. Masking discipline is unaffected.
"""

from __future__ import annotations

from dataclasses import dataclass

__all__ = [
    "CATEGORIES",
    "CATEGORY_NOTES",
    "CHALLENGE_CASES",
    "ChallengeCase",
    "case_by_id",
    "cases_for",
]

# Closed category vocabulary; `historical` doubles as the §5.1 "Historical Case
# Units" dataset, the rest partition the core challenge fixtures.
CATEGORIES = (
    "historical",
    "control",
    "coordination",
    "relative_chain",
    "quotes",
    "hyperbaton",
)

CATEGORY_NOTES = {
    "control": "Control verb / infinitival complement (xcomp) propagation.",
    "coordination": "Shared arguments across coordinated predicates.",
    "relative_chain": "Two or more relative clauses in one parse unit.",
    "quotes": "Direct-speech span: speech frames vs vocatives vs complementation.",
    "hyperbaton": "Long-distance discontinuous dependency (>= 45 linear tokens).",
}


@dataclass(frozen=True)
class ChallengeCase:
    """One benchmark unit: parse-unit coordinates plus phenomenon metadata."""

    case_id: str
    canticle: str
    canto: int
    line_start: int
    line_end: int
    category: str
    note: str = ""

    @property
    def unit(self) -> dict:
        """Coordinates in `UnitResult.unit` shape."""
        return {
            "canticle": self.canticle,
            "canto": self.canto,
            "line_start": self.line_start,
            "line_end": self.line_end,
        }


# Historical notes cite the CORRECTIONS.md census section; see that file for the
# full per-position record (which this file deliberately does not reproduce).
_HISTORICAL_NOTES = {
    "hist-inf02-082": ("P15: 2sg verb with relative pronoun (subj/obl retag)"),
    "hist-inf10-091": ("P15: copular predicate with cross-line locative"),
    "hist-inf14-124": ("P15: directional obl:a on gerund participle"),
    "hist-inf22-097": ("P15: predicative relative on copula son"),
    "hist-inf28-076": ("P15: dative iobj vs obl:a normalization"),
    "hist-pur01-100": ("P15: locative adverb as oblique"),
    "hist-pur02-124": ("P15: comparative clause head as oblique"),
    "hist-pur04-067": ("P15: second directional oblique"),
    "hist-pur09-013": ("P15: temporal heads as obliques"),
    "hist-pur09-064": ("P15: directional obl:per on mosse"),
    "hist-pur13-133": ("P15: temporal modifier on past participle"),
    "hist-pur14-028": ("P15: ablative relative onde"),
    "hist-pur19-064": ("P15: comparative standard quale"),
    "hist-pur20-091": ("P15: Layer-4 xcomp retag feeding subj propagation"),
    "hist-pur25-046": ("P15: coordinate subject across lines"),
    "hist-pur26-031": ("P15: reciprocal obl / pronominal ne"),
    "hist-pur26-061": ("P15: pronominal se ne va oblique"),
    "hist-pur27-094": ("P15: temporal head as oblique (parea)"),
    "hist-pur28-070": ("P15: locative adverb la as oblique"),
    "hist-par01-076": ("P15: parvemi partitive obl:di vs subj"),
    "hist-par08-001": ("P15: directional obl:da"),
    "hist-par11-088": ("P15: coordinate subject across lines"),
    "hist-par12-010": ("P15: comparative oblique cross-line"),
    "hist-par12-121": ("P15: topical chi subject across lines"),
    "hist-par13-037": ("P15: second locative oblique on participle"),
    "hist-par14-052": ("P15: comparative standard / speech obj role fix"),
    "hist-par14-091": ("P15: accusative+infinitive xcomp role fix"),
    "hist-par15-031": ("P15: discourse oblique across lines"),
    "hist-par16-058": ("P15: split coordinate predicates normalized"),
    "hist-par20-031": ("P15: dative clitic mi as oblique"),
    "hist-par23-001": ("P15: temporal oblique across lines"),
    "hist-par25-058": ("P15: clitic li iobj vs subj retag"),
    "hist-par26-025": ("P15: clausal subj / correlative obl:in"),
    "hist-par29-031": ("P15: inverted obl subject / topical subj"),
    "hist-par29-136": ("P15: topical subject across lines"),
    "hist-par30-010": ("P15: adverbial quantifier as obl:a"),
    "hist-inf07-049": ("P5: verbless speech frame (io root + ccomp)"),
    "hist-inf08-052": ("P5: verbless speech frame (io root + ccomp)"),
    "hist-inf08-070": ("P5: verbless speech frame (io root + ccomp)"),
    "hist-inf10-019": ("P5: verbless speech frame (io root + ccomp)"),
    "hist-inf11-067": ("P5: verbless speech frame (io root + ccomp)"),
    "hist-inf24-070": ("P5: verbless speech frame (io root + ccomp)"),
    "hist-inf31-019": ("P5: verbless speech frame (io root + ccomp)"),
    "hist-pur06-049": ("P5: verbless speech frame (io root + ccomp)"),
    "hist-inf08-079": ("P13: spurious clausal complement dropped"),
    "hist-inf22-081": ("P13: spurious clausal complement dropped"),
    "hist-pur05-046": ("P13: spurious clausal complement dropped"),
    "hist-pur09-070": ("P13: spurious clausal complement dropped"),
}

# Frozen table: (case_id, canticle, canto, line_start, line_end, category),
# grouped by category in `CATEGORIES` order.
_CASE_ROWS = (
    (
        ("hist-inf02-082", "inferno", 2, 82, 84, "historical"),
        ("hist-inf10-091", "inferno", 10, 91, 93, "historical"),
        ("hist-inf14-124", "inferno", 14, 124, 129, "historical"),
        ("hist-inf22-097", "inferno", 22, 97, 105, "historical"),
        ("hist-inf28-076", "inferno", 28, 76, 81, "historical"),
        ("hist-pur01-100", "purgatorio", 1, 100, 105, "historical"),
        ("hist-pur02-124", "purgatorio", 2, 124, 133, "historical"),
        ("hist-pur04-067", "purgatorio", 4, 67, 75, "historical"),
        ("hist-pur09-013", "purgatorio", 9, 13, 24, "historical"),
        ("hist-pur09-064", "purgatorio", 9, 64, 69, "historical"),
        ("hist-pur13-133", "purgatorio", 13, 133, 135, "historical"),
        ("hist-pur14-028", "purgatorio", 14, 28, 39, "historical"),
        ("hist-pur19-064", "purgatorio", 19, 64, 69, "historical"),
        ("hist-pur20-091", "purgatorio", 20, 91, 93, "historical"),
        ("hist-pur25-046", "purgatorio", 25, 46, 51, "historical"),
        ("hist-pur26-031", "purgatorio", 26, 31, 36, "historical"),
        ("hist-pur26-061", "purgatorio", 26, 61, 66, "historical"),
        ("hist-pur27-094", "purgatorio", 27, 94, 102, "historical"),
        ("hist-pur28-070", "purgatorio", 28, 70, 75, "historical"),
        ("hist-par01-076", "paradiso", 1, 76, 81, "historical"),
        ("hist-par08-001", "paradiso", 8, 1, 12, "historical"),
        ("hist-par11-088", "paradiso", 11, 88, 93, "historical"),
        ("hist-par12-010", "paradiso", 12, 10, 21, "historical"),
        ("hist-par12-121", "paradiso", 12, 121, 126, "historical"),
        ("hist-par13-037", "paradiso", 13, 37, 48, "historical"),
        ("hist-par14-052", "paradiso", 14, 52, 60, "historical"),
        ("hist-par14-091", "paradiso", 14, 91, 96, "historical"),
        ("hist-par15-031", "paradiso", 15, 31, 36, "historical"),
        ("hist-par16-058", "paradiso", 16, 58, 66, "historical"),
        ("hist-par20-031", "paradiso", 20, 31, 36, "historical"),
        ("hist-par23-001", "paradiso", 23, 1, 12, "historical"),
        ("hist-par25-058", "paradiso", 25, 58, 63, "historical"),
        ("hist-par26-025", "paradiso", 26, 25, 30, "historical"),
        ("hist-par29-031", "paradiso", 29, 31, 36, "historical"),
        ("hist-par29-136", "paradiso", 29, 136, 138, "historical"),
        ("hist-par30-010", "paradiso", 30, 10, 15, "historical"),
        ("hist-inf07-049", "inferno", 7, 49, 51, "historical"),
        ("hist-inf08-052", "inferno", 8, 52, 54, "historical"),
        ("hist-inf08-070", "inferno", 8, 70, 75, "historical"),
        ("hist-inf10-019", "inferno", 10, 19, 21, "historical"),
        ("hist-inf11-067", "inferno", 11, 67, 69, "historical"),
        ("hist-inf24-070", "inferno", 24, 70, 75, "historical"),
        ("hist-inf31-019", "inferno", 31, 19, 21, "historical"),
        ("hist-pur06-049", "purgatorio", 6, 49, 51, "historical"),
        ("hist-inf08-079", "inferno", 8, 79, 81, "historical"),
        ("hist-inf22-081", "inferno", 22, 81, 84, "historical"),
        ("hist-pur05-046", "purgatorio", 5, 46, 48, "historical"),
        ("hist-pur09-070", "purgatorio", 9, 70, 72, "historical"),
    ),
    (
        ("ctl-inf01-010", "inferno", 1, 10, 12, "control"),
        ("ctl-pur01-001", "purgatorio", 1, 1, 6, "control"),
        ("ctl-par01-004", "paradiso", 1, 4, 9, "control"),
        ("ctl-inf01-022", "inferno", 1, 22, 27, "control"),
        ("ctl-pur01-019", "purgatorio", 1, 19, 21, "control"),
        ("ctl-par01-010", "paradiso", 1, 10, 12, "control"),
        ("ctl-inf01-037", "inferno", 1, 37, 45, "control"),
        ("ctl-pur01-025", "purgatorio", 1, 25, 27, "control"),
    ),
    (
        ("crd-inf01-046", "inferno", 1, 46, 48, "coordination"),
        ("crd-pur01-049", "purgatorio", 1, 49, 51, "coordination"),
        ("crd-par01-022", "paradiso", 1, 22, 27, "coordination"),
        ("crd-inf01-103", "inferno", 1, 103, 105, "coordination"),
        ("crd-pur01-067", "purgatorio", 1, 67, 69, "coordination"),
        ("crd-par01-028", "paradiso", 1, 28, 33, "coordination"),
        ("crd-inf01-127", "inferno", 1, 127, 129, "coordination"),
        ("crd-pur02-019", "purgatorio", 2, 19, 21, "coordination"),
    ),
    (
        ("rel-inf01-007", "inferno", 1, 7, 9, "relative_chain"),
        ("rel-pur01-013", "purgatorio", 1, 13, 18, "relative_chain"),
        ("rel-par01-058", "paradiso", 1, 58, 63, "relative_chain"),
        ("rel-inf01-013", "inferno", 1, 13, 18, "relative_chain"),
        ("rel-pur01-028", "purgatorio", 1, 28, 33, "relative_chain"),
        ("rel-par01-073", "paradiso", 1, 73, 75, "relative_chain"),
        ("rel-inf01-019", "inferno", 1, 19, 21, "relative_chain"),
        ("rel-pur01-073", "purgatorio", 1, 73, 75, "relative_chain"),
    ),
    (
        ("quo-inf01-064", "inferno", 1, 64, 66, "quotes"),
        ("quo-pur01-040", "purgatorio", 1, 40, 42, "quotes"),
        ("quo-par01-085", "paradiso", 1, 85, 90, "quotes"),
        ("quo-inf01-067", "inferno", 1, 67, 69, "quotes"),
        ("quo-pur01-043", "purgatorio", 1, 43, 45, "quotes"),
        ("quo-par01-091", "paradiso", 1, 91, 93, "quotes"),
        ("quo-inf01-070", "inferno", 1, 70, 72, "quotes"),
        ("quo-pur01-046", "purgatorio", 1, 46, 46, "quotes"),
    ),
    (
        ("hyp-par13-010", "paradiso", 13, 10, 21, "hyperbaton"),
        ("hyp-inf16-094", "inferno", 16, 94, 105, "hyperbaton"),
        ("hyp-inf23-037", "inferno", 23, 37, 45, "hyperbaton"),
        ("hyp-par30-082", "paradiso", 30, 82, 90, "hyperbaton"),
        ("hyp-inf24-001", "inferno", 24, 1, 11, "hyperbaton"),
        ("hyp-par31-001", "paradiso", 31, 1, 12, "hyperbaton"),
        ("hyp-pur12-127", "purgatorio", 12, 127, 136, "hyperbaton"),
    ),
)


def _build() -> tuple[ChallengeCase, ...]:
    cases: list[ChallengeCase] = []
    for block in _CASE_ROWS:
        for case_id, canticle, canto, start, end, category in block:
            cases.append(
                ChallengeCase(
                    case_id=case_id,
                    canticle=canticle,
                    canto=canto,
                    line_start=start,
                    line_end=end,
                    category=category,
                    note=_HISTORICAL_NOTES.get(case_id, CATEGORY_NOTES.get(category, "")),
                )
            )
    return tuple(cases)


CHALLENGE_CASES: tuple[ChallengeCase, ...] = _build()

_INDEX = {case.case_id: case for case in CHALLENGE_CASES}


def case_by_id(case_id: str) -> ChallengeCase | None:
    return _INDEX.get(case_id)


def cases_for(categories=None) -> list[ChallengeCase]:
    """Cases in canonical order, optionally filtered to a category subset."""
    wanted = None if categories is None else set(categories)
    return [case for case in CHALLENGE_CASES if wanted is None or case.category in wanted]
