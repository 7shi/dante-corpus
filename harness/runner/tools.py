"""Dedicated Grammar Tool API for Stage 1 autonomous inference.

Implements the closed toolset of `harness/runner/PLAN.md` §3. Free-form bash execution is
disabled by design: the agent interacts with the corpus exclusively through the three tools
below, each of which serves multi-layer grammatical context (L1 tokens/texts, quotes
hierarchy, L2 morphology, pronoun case annex, L3 noun phrases, L4 UD trees) while
**strictly masking** Layer 5 gold data (`skel/*.tsv`), the 130-rule registry, and the
correction records.

Masking discipline (enforced structurally, not by convention): this module never imports
`dante_corpus.skel.io`, `dante_corpus.skel.registry`, or `dante_corpus.skel.rules`, and no
code path here opens a file under `skel/`. The only Layer-5 artifact it touches is the
frozen role vocabulary in `dante_corpus.skel.models` (public knowledge the agent needs to
speak the skeleton language at all).

Anti-Leakage Guard: `search_corpus` never returns a hit from the canto of the active parse
unit (the unit most recently served by `read_unit` or validated by `validate_candidate`),
so the agent cannot fish for gold-adjacent annotations of its own target.
"""

from __future__ import annotations

import copy
import json
from dataclasses import dataclass, field

from dante_corpus import api
from dante_corpus.case import CaseRow
from dante_corpus.dep import MAX_UNIT_LINES, DepRow, sentence_groups
from dante_corpus.morph import MorphRow, strip_word_punct
from dante_corpus.np import NPSpan
from dante_corpus.skel.models import GrammarContext, OBL_RE, ROLES

__all__ = [
    "GrammarToolkit",
    "MAX_UNIT_LINES",
    "PAYLOAD_LEGEND",
    "PAYLOAD_TIERS",
    "TOOL_SPECS",
    "VALID_ROLES",
    "tool_specs",
]

# The role vocabulary a candidate may speak: the frozen core roles, the empty marker for a
# zero-argument predicate's single row, and `obl:<prep>` for preposition-governed obliques.
# (`ROLES` already carries the bare `obl` marker gold uses for adverbial obliques.)
VALID_ROLES = frozenset(ROLES)

# Roles whose fillers are nominal: their arguments must cite a Layer 3 NP head or a
# pronoun (`runner/PLAN.md` §3.3 item 2 — "Nominal argument tokens..."). Clausal /
# predicative roles (`attr`, `ccomp`, `xcomp`) naturally anchor on predicate tokens, and
# bare `obl` is gold's adverbial-oblique marker, so none of them is held to the nominal
# citation rule (existence and word-anchor checks still apply everywhere).
NOMINAL_ANCHOR_ROLES = frozenset({"subj", "obj", "iobj"})


def requires_nominal_anchor(role: str) -> bool:
    """True when `role` demands an NP-head/pronoun citation for its arguments."""
    return role in NOMINAL_ANCHOR_ROLES or (
        role.startswith("obl:") and OBL_RE.fullmatch(role) is not None
    )

# Fields `search_corpus` accepts; everything else is rejected rather than ignored, so a
# typo'd query fails loudly instead of silently matching everything.
_QUERY_FIELDS = frozenset({"word", "lemma", "pos", "deprel", "case"})

_ROW_FIELDS = ("line", "token", "word", "role", "arg_line", "arg_token")

# Fields a candidate row cannot do without; `word` is an optional verification anchor
# (coordinates alone identify the token, so wire payloads may omit it).
_REQUIRED_ROW_FIELDS = ("line", "token", "role", "arg_line", "arg_token")

# --- read_unit payload tiers (STAGE3.md §2.B) -------------------------------------------
#
# The wire size of a `read_unit` result is the session's size tail (corpus wire
# p50 7.1 / max 30.0 kB per unit), so the payload ships compact. Tier "R1"
# (primary) serves positional one-line rows — a CoNLL-like columnar shape made
# self-describing by the inline `PAYLOAD_LEGEND` inside every result. Tier "S1"
# (fallback, near-zero comprehension risk) keeps today's named-dict schema,
# dropping empty-valued keys and empty sections only. The confirmation run
# (STAGE3.md §5) picks the tier; content coverage is identical by test.

PAYLOAD_TIERS = ("R1", "S1")

# MorphRow fields in compact positional order; `note` rides as an optional 9th
# element when non-empty (26% of corpus rows carry one — 'reflexive', 'clitic',
# 'apocope'... — and dropping live Layer-2 annotation to save ~1% of payload
# bytes would change what the model can reason about, not just how it is packed).
_MORPH_COMPACT_FIELDS = ("word", "lemma", "pos", "gender", "number", "person", "tense", "mood")

PAYLOAD_LEGEND = (
    "Compact shapes: morphology [word,lemma,pos,gender,number,person,tense,"
    "mood], empty trailing fields omitted, 9th element = note when present; "
    "dependencies [token,head_token,deprel] with 4th = head_line only when "
    "it differs from line (head 0.0 = sentence root); noun_phrases "
    "[line,start,end,head], 1-based token indexes into the lines token "
    "lists. Empty sections are omitted."
)


def _sparse_dict(data: dict) -> dict:
    """Drop empty-valued keys (tier S1's sparseness convention)."""
    return {
        key: value
        for key, value in data.items()
        if value not in ("", None, (), [], {})
    }


def _morph_row_compact(row: MorphRow) -> list:
    fields = [getattr(row, name) for name in _MORPH_COMPACT_FIELDS]
    if row.note:
        # Keep interior empties as "" so positions stay unambiguous.
        return fields + [row.note]
    while fields and fields[-1] == "":
        fields.pop()
    return fields


def _dep_row_compact(row: DepRow) -> list:
    out = [row.token, row.head_token, row.deprel]
    if row.head_line != row.line:
        out.append(row.head_line)
    return out


def _np_row_compact(span: NPSpan) -> list:
    return [span.line, span.start, span.end, span.head]


def _render_payload(
    data: "_CantoData",
    unit_nos: list[int],
    quotes: list[dict],
    tier: str,
) -> dict[str, object]:
    """Render the `read_unit` result body in the requested payload tier."""
    if tier == "R1":
        payload: dict[str, object] = {
            "legend": PAYLOAD_LEGEND,
            "morphology": {
                no: [_morph_row_compact(row) for row in data.morph.get(no, ())]
                for no in unit_nos
                if data.morph.get(no)
            },
            "noun_phrases": [
                _np_row_compact(span)
                for span in _flatten_np(data.np_forest)
                if unit_nos[0] <= span.line <= unit_nos[-1]
            ],
            "dependencies": {
                no: [_dep_row_compact(row) for row in data.dep.get(no, ())]
                for no in unit_nos
                if data.dep.get(no)
            },
        }
        if quotes:
            payload["quotes"] = quotes
        case_rows = {
            no: [_sparse_dict(row.to_dict()) for row in data.case.get(no, ())]
            for no in unit_nos
            if data.case.get(no)
        }
        if case_rows:
            payload["case"] = case_rows
        return payload
    if tier == "S1":
        payload = {
            "morphology": {
                no: [_sparse_dict(row.to_dict()) for row in data.morph.get(no, ())]
                for no in unit_nos
                if data.morph.get(no)
            },
            "noun_phrases": [
                _sparse_dict(span.to_dict())
                for span in _flatten_np(data.np_forest)
                if unit_nos[0] <= span.line <= unit_nos[-1]
            ],
            "dependencies": {
                no: [_sparse_dict(row.to_dict()) for row in data.dep.get(no, ())]
                for no in unit_nos
                if data.dep.get(no)
            },
        }
        if quotes:
            payload["quotes"] = [
                _sparse_dict(quote) for quote in quotes
            ]
        case_rows = {
            no: [_sparse_dict(row.to_dict()) for row in data.case.get(no, ())]
            for no in unit_nos
            if data.case.get(no)
        }
        if case_rows:
            payload["case"] = case_rows
        return payload
    raise ValueError(f"unknown payload tier: {tier!r} (valid: {list(PAYLOAD_TIERS)})")


# --- Tool-call specifications ---------------------------------------------------------
#
# `llm7shi.Client` speaks structured output (`schema=`), not native function calling, so the
# agent loop embeds these specs in its prompt and parses the model's JSON tool call itself
# (see `GrammarToolkit.dispatch`). The specs are plain JSON Schema in OpenAI function form,
# which doubles as documentation of the closed tool surface.

_CANTICLE_SCHEMA = {
    "type": "string",
    "enum": list(api.VALID_CANTICLES),
    "description": "Canticle: inferno, purgatorio, or paradiso.",
}

_LINE_SCHEMA = {"type": "integer", "minimum": 1, "description": "1-based line number."}

_CANDIDATE_ROW_SCHEMA = {
    "type": "object",
    "description": (
        "One (predicate, argument) row, `SkelRow.to_dict()` shape. Cite (0, 0) for a "
        "pro-drop argument; role '' marks a zero-argument predicate's single row."
    ),
    "properties": {
        "line": {"type": "integer", "description": "Predicate line."},
        "token": {"type": "integer", "description": "Predicate token index (1-based)."},
        "word": {
            "type": "string",
            "description": "Predicate word (optional verification anchor).",
        },
        "role": {
            "type": "string",
            "description": (
                "subj | obj | iobj | attr | xcomp | ccomp | obl | obl:<prep>, or '' "
                "for a zero-argument predicate."
            ),
        },
        "arg_line": {"type": "integer", "description": "Argument line (0 for pro-drop)."},
        "arg_token": {"type": "integer", "description": "Argument token index (0 for pro-drop)."},
        "arg_word": {"type": "string", "description": "Argument word anchor ('' for pro-drop)."},
    },
    "required": list(_REQUIRED_ROW_FIELDS),
    "additionalProperties": False,
}

TOOL_SPECS: tuple[dict, ...] = (
    {
        "type": "function",
        "function": {
            "name": "read_unit",
            "description": (
                "Read the complete multi-layer grammatical context of one parse unit "
                "(a sentence group of at most 12 lines): Layer 1 tokens/texts, quotes "
                "hierarchy, Layer 2 morphology, pronoun case annex, Layer 3 noun phrases, "
                "and Layer 4 UD trees. A range crossing a sentence boundary is rejected "
                "with the actual unit bounds. Layer 5 gold data is never served."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "canticle": _CANTICLE_SCHEMA,
                    "canto": {"type": "integer", "minimum": 1, "description": "Canto number."},
                    "line_start": _LINE_SCHEMA,
                    "line_end": {
                        **_LINE_SCHEMA,
                        "description": (
                            "Last line of the requested range; omit to read the whole "
                            "parse unit containing line_start."
                        ),
                    },
                },
                "required": ["canticle", "canto", "line_start"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_corpus",
            "description": (
                "Search other cantos for analogous grammatical constructions. The query "
                "conjoins any of: word (loose token match), lemma, pos (substring, e.g. "
                "'verb'), deprel (exact), case (one slot of the pronoun case annex). The "
                "canto of your active parse unit is excluded by an anti-leakage guard."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "object",
                        "description": "Conjunctive match fields; at least one required.",
                        "properties": {
                            "word": {"type": "string"},
                            "lemma": {"type": "string"},
                            "pos": {"type": "string"},
                            "deprel": {"type": "string"},
                            "case": {"type": "string"},
                        },
                        "minProperties": 1,
                        "additionalProperties": False,
                    },
                    "limit": {
                        "type": "integer",
                        "minimum": 1,
                        "default": 10,
                        "description": "Maximum number of hits to return.",
                    },
                },
                "required": ["query"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "validate_candidate",
            "description": (
                "Validate intrinsic syntactic well-formedness of your candidate skeleton "
                "rows: predicate tokens exist in Layer 1, nominal arguments (subj, obj, "
                "iobj, obl:<prep>) cite Layer 3 NP heads or pronouns — clausal roles "
                "(attr, xcomp, ccomp) and bare obl may anchor on any token — slots are "
                "unique per predicate (dual roles need clitic licensing), and roles use "
                "the frozen vocabulary. Also records upstream_feedback about "
                "irreconcilable L2/L4 defects you identified."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "canticle": _CANTICLE_SCHEMA,
                    "canto": {"type": "integer", "minimum": 1, "description": "Canto number."},
                    "line_start": {
                        **_LINE_SCHEMA,
                        "description": "First line of the parse unit being solved.",
                    },
                    "candidate_rows": {
                        "type": "array",
                        "items": _CANDIDATE_ROW_SCHEMA,
                        "description": "Your proposed skeleton rows for the unit.",
                    },
                    "upstream_feedback": {
                        "type": "array",
                        "items": {"type": "object"},
                        "description": (
                            "Optional records of upstream defects, each naming 'layer' "
                            "('L2' or 'L4') and a 'description'."
                        ),
                    },
                },
                "required": ["canticle", "canto", "line_start", "candidate_rows"],
                "additionalProperties": False,
            },
        },
    },
)


def tool_specs() -> list[dict]:
    """A fresh copy of the tool-call specifications, safe to mutate per prompt."""
    return copy.deepcopy(list(TOOL_SPECS))


def _check_canticle(canticle: str) -> str:
    if canticle not in api.VALID_CANTICLES:
        raise ValueError(f"unknown canticle: {canticle}")
    return canticle


def _flatten_np(spans: tuple[NPSpan, ...]):
    """Yield every span of the nested NP forest, parents before children."""
    for span in spans:
        yield span
        yield from _flatten_np(span.children)


def _words_match(word: str, token: str) -> bool:
    """Loose anchor equality, mirroring Layer 5's own build-time check."""
    return word == token or strip_word_punct(word, token) is not None


@dataclass
class _CantoData:
    """Everything the tools need about one canto, loaded once and cached per toolkit."""

    canticle: str
    number: int
    nos: list[int]
    texts: list[str]
    tokens: dict[int, tuple[str, ...]]
    groups: list[list[int]]
    morph: dict[int, tuple[MorphRow, ...]]
    dep: dict[int, tuple[DepRow, ...]]
    case: dict[int, tuple[CaseRow, ...]]
    case_by_pos: dict[tuple[int, int], CaseRow]
    np_forest: tuple[NPSpan, ...]
    np_heads: dict[tuple[int, int], NPSpan]
    quotes: tuple[api.QuoteSpan, ...]
    ctx: GrammarContext = field(repr=False)

    def group_of(self, line: int) -> list[int] | None:
        for group in self.groups:
            if group[0] <= line <= group[-1]:
                return group
        return None


@dataclass(frozen=True)
class _CandidateRow:
    """One normalized candidate row (`SkelRow.to_dict()` shape)."""

    index: int
    line: int
    token: int
    word: str
    role: str
    arg_line: int
    arg_token: int
    arg_word: str

    @property
    def pred(self) -> tuple[int, int]:
        return (self.line, self.token)

    @property
    def arg(self) -> tuple[int, int]:
        return (self.arg_line, self.arg_token)


def _load_canto(canticle: str, number: int) -> _CantoData:
    canto = api.canto(canticle, number)
    lines = canto.lines()
    nos = [line.no for line in lines]
    texts = [line.text for line in lines]
    morph = canto.morph()
    dep = canto.dep()
    case = canto.case()

    forest = canto.np()
    np_heads: dict[tuple[int, int], NPSpan] = {}
    for span in _flatten_np(forest):
        np_heads.setdefault((span.line, span.head), span)

    case_by_pos = {
        (row.line, row.token): row for rows in case.values() for row in rows
    }

    ctx = GrammarContext(
        nos=nos,
        texts=texts,
        morph_rows={no: list(rows) for no, rows in morph.items()},
        np_rows={no: [s for s in _flatten_np(forest) if s.line == no] for no in nos},
        dep_rows={no: list(rows) for no, rows in dep.items()},
        case_rows={no: list(rows) for no, rows in case.items()},
    )
    return _CantoData(
        canticle=canticle,
        number=number,
        nos=nos,
        texts=texts,
        tokens={line.no: line.tokens for line in lines},
        groups=sentence_groups(nos, texts),
        morph=morph,
        dep=dep,
        case=case,
        case_by_pos=case_by_pos,
        np_forest=forest,
        np_heads=np_heads,
        quotes=canto.quotes(),
        ctx=ctx,
    )


class GrammarToolkit:
    """The closed toolset bound to one agent session.

    One instance per benchmark run / agent conversation. It tracks the *active unit* —
    the parse unit currently being solved — so `search_corpus` can enforce the anti-leakage
    guard without the agent having to pass exclusion arguments it could forget or forge.
    """

    def __init__(self, payload_tier: str = "R1") -> None:
        if payload_tier not in PAYLOAD_TIERS:
            raise ValueError(
                f"unknown payload tier: {payload_tier!r} (valid: {list(PAYLOAD_TIERS)})"
            )
        self.payload_tier = payload_tier
        self._cache: dict[tuple[str, int], _CantoData] = {}
        self._active_unit: tuple[str, int, int, int] | None = None
        self.upstream_log: list[dict[str, object]] = []

    # --- internals -----------------------------------------------------------------

    def _canto(self, canticle: str, number: int) -> _CantoData:
        _check_canticle(canticle)
        if not isinstance(number, int) or isinstance(number, bool) or number < 1:
            raise ValueError(f"invalid canto number: {number!r}")
        key = (canticle, number)
        if key not in self._cache:
            try:
                self._cache[key] = _load_canto(canticle, number)
            except FileNotFoundError as exc:
                raise ValueError(f"canto not found: {canticle} {number}") from exc
        return self._cache[key]

    def _unit_bounds(self, data: _CantoData, line_start: int, line_end: int | None) -> tuple[int, int]:
        """Resolve the requested range to one parse unit (a `dep.sentence_groups` slice)."""
        if not isinstance(line_start, int) or isinstance(line_start, bool):
            raise ValueError(f"invalid line_start: {line_start!r}")
        if line_end is not None and (
            not isinstance(line_end, int) or isinstance(line_end, bool)
        ):
            raise ValueError(f"invalid line_end: {line_end!r}")
        group = data.group_of(line_start)
        if group is None:
            raise ValueError(
                f"line {line_start} is outside {data.canticle} {data.number} "
                f"(lines {data.nos[0]}-{data.nos[-1]})"
            )
        if line_end is None:
            return group[0], group[-1]
        if line_end < line_start:
            raise ValueError(f"line range runs backwards: {line_start}-{line_end}")
        if line_end > group[-1]:
            raise ValueError(
                f"requested range {line_start}-{line_end} crosses the parse-unit "
                f"boundary: this unit is lines {group[0]}-{group[-1]}"
            )
        return line_start, line_end

    def _iter_search_cantos(self):
        """Yield cached-or-loaded cantos in canonical order, skipping the active one."""
        for canticle in api.VALID_CANTICLES:
            try:
                numbers = api.cantos(canticle)
            except FileNotFoundError:
                continue  # unbuilt source tree: nothing to search in this canticle
            for number in numbers:
                if self._active_unit is not None and (
                    canticle, number
                ) == self._active_unit[:2]:
                    continue  # Anti-Leakage Guard: never serve the target's own canto
                yield self._canto(canticle, number)

    # --- tool 1: read_unit -----------------------------------------------------------

    def read_unit(
        self, canticle: str, canto: int, line_start: int, line_end: int | None = None
    ) -> dict[str, object]:
        """Serve the complete multi-layer grammatical context of one parse unit.

        The unit is bounded by `dep.sentence_groups` (at most `MAX_UNIT_LINES` lines): a
        request that would cross a sentence boundary is rejected with the actual bounds so
        the agent can re-align. Layers 1-4, the quotes hierarchy, and the pronoun case
        annex are provided in full; Layer 5 skeleton rows and rule annotations are strictly
        masked (they are never read, let alone served).

        The heavy per-line sections render in the toolkit's compact `payload_tier`
        (STAGE3.md §2.B): "R1" serves positional rows plus an inline legend; "S1" serves
        sparse named dicts. Content coverage is identical across tiers.

        Returns a JSON-ready dict with keys: `unit`, `lines`, and — when non-empty —
        `quotes`, `morphology`, `case`, `noun_phrases`, `dependencies` (plus `legend`
        under R1).
        """
        data = self._canto(canticle, canto)
        start, end = self._unit_bounds(data, line_start, line_end)
        self._active_unit = (data.canticle, data.number, start, end)

        unit_nos = [no for no in data.nos if start <= no <= end]
        text_by_no = dict(zip(data.nos, data.texts))
        quotes = [
            q.to_dict()
            for q in data.quotes
            if q.start_line <= end and q.end_line >= start
        ]
        return {
            "unit": {
                "canticle": data.canticle,
                "canto": data.number,
                "line_start": start,
                "line_end": end,
            },
            "lines": [
                {
                    "no": no,
                    "text": text_by_no[no],
                    "tokens": list(data.tokens[no]),
                }
                for no in unit_nos
            ],
            **_render_payload(data, unit_nos, quotes, self.payload_tier),
        }

    # --- tool 2: search_corpus ---------------------------------------------------------

    def search_corpus(self, query: dict, limit: int = 10) -> list[dict]:
        """Scoped search for analogous grammatical constructions outside the active canto.

        `query` conjoins any of: `word` (loose token match), `lemma`, `pos` (substring,
        e.g. `"verb"`), `deprel` (exact), `case` (one slot of the pronoun case annex).
        Hits carry their location plus every layer field that resolved, and never any
        Layer 5 information. The Anti-Leakage Guard excludes the active canto entirely —
        the current canto and target unit are unsearchable by construction.
        """
        if not isinstance(query, dict) or not query:
            raise ValueError("query must be a non-empty dict")
        unknown = set(query) - _QUERY_FIELDS
        if unknown:
            raise ValueError(
                f"unknown query fields: {sorted(unknown)} (valid: {sorted(_QUERY_FIELDS)})"
            )
        if not isinstance(limit, int) or isinstance(limit, bool) or limit < 1:
            raise ValueError(f"limit must be a positive integer: {limit!r}")

        wanted_word = query.get("word")
        wanted_lemma = str(query.get("lemma", "")).lower()
        wanted_pos = str(query.get("pos", "")).lower()
        wanted_deprel = query.get("deprel")
        wanted_case = str(query.get("case", "")).lower()

        hits: list[dict] = []
        for data in self._iter_search_cantos():
            for no in data.nos:
                morph_rows = data.morph.get(no, ())
                dep_rows = data.dep.get(no, ())
                for i, token in enumerate(data.tokens[no]):
                    pos_index = (no, i + 1)
                    mrow = morph_rows[i] if i < len(morph_rows) else None
                    drow = dep_rows[i] if i < len(dep_rows) else None
                    crow = data.case_by_pos.get(pos_index)

                    if wanted_word is not None and not _words_match(
                        str(wanted_word), token
                    ):
                        continue
                    if wanted_lemma and (
                        mrow is None or (mrow.lemma or "").lower() != wanted_lemma
                    ):
                        continue
                    if wanted_pos and (
                        mrow is None or wanted_pos not in mrow.pos.lower()
                    ):
                        continue
                    if wanted_deprel is not None and (
                        drow is None or drow.deprel != str(wanted_deprel)
                    ):
                        continue
                    if query.get("case") and (
                        crow is None
                        or wanted_case not in [c.lower() for c in crow.cases()]
                    ):
                        continue

                    hit: dict[str, object] = {
                        "canticle": data.canticle,
                        "canto": data.number,
                        "line": no,
                        "token": i + 1,
                        "word": token,
                    }
                    if mrow is not None:
                        hit["lemma"] = mrow.lemma
                        hit["pos"] = mrow.pos
                    if drow is not None:
                        hit["deprel"] = drow.deprel
                        hit["head_line"] = drow.head_line
                        hit["head_token"] = drow.head_token
                    if crow is not None:
                        hit["case"] = crow.case
                    hits.append(hit)
                    if len(hits) >= limit:
                        return hits
        return hits

    # --- tool 3: validate_candidate ------------------------------------------------------

    def validate_candidate(
        self,
        canticle: str,
        canto: int,
        line_start: int,
        candidate_rows: list[dict],
        upstream_feedback: list[dict] | None = None,
    ) -> dict[str, object]:
        """Validate intrinsic syntactic well-formedness of candidate skeleton rows.

        Checks (see `harness/runner/PLAN.md` §3.3):
        1. every predicate token exists in Layer 1 and matches its word anchor when one
           is given;
        2. every nominal argument (subj, obj, iobj, obl:<prep>) cites a valid Layer 3 NP
           head or a Layer 1 pronoun (or `(0, 0)` for pro-drop). Clausal / predicative
           roles (`attr`, `ccomp`, `xcomp`) and bare `obl` — gold's adverbial-oblique
           marker — may anchor on any existing token: complements cite their clause's
           predicate head by nature, so holding them to the nominal rule would reject
           correct analyses;
        3. slots are unique per predicate — duplicate citations are rejected, and one
           argument filling two roles requires clitic licensing (a multi-slot case annex
           row such as fused `gliel'`);
        4. every role belongs to the frozen vocabulary (`subj`, `obj`, `iobj`, `attr`,
           `xcomp`, `ccomp`, `obl`, `obl:<prep>`, or the zero-argument `""` marker).

        `upstream_feedback` records (irreconcilable L2/L4 defects spotted by the model)
        are accepted, logged verbatim for human triage, and reported back; malformed
        records downgrade to warnings and never affect validity.

        Returns `{"valid": bool, "errors": [...], "warnings": [...], "diagnostics": str}`.
        """
        data = self._canto(canticle, canto)
        start, end = self._unit_bounds(data, line_start, None)
        self._active_unit = (data.canticle, data.number, start, end)

        errors: list[str] = []
        warnings: list[str] = []
        parsed: list[_CandidateRow] = []

        for index, raw in enumerate(candidate_rows):
            where = f"row[{index}]"
            if not isinstance(raw, dict):
                errors.append(f"{where}: not a dict")
                continue
            missing = [key for key in _REQUIRED_ROW_FIELDS if key not in raw]
            if missing:
                errors.append(f"{where}: missing field(s) {missing}")
                continue
            ints: dict[str, int] = {}
            bad_type = False
            for key in ("line", "token", "arg_line", "arg_token"):
                value = raw[key]
                if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                    errors.append(f"{where}: {key} must be a non-negative int, got {value!r}")
                    bad_type = True
                else:
                    ints[key] = value
            if bad_type:
                continue
            parsed.append(
                _CandidateRow(
                    index=index,
                    line=ints["line"],
                    token=ints["token"],
                    word=str(raw.get("word", "")),
                    role=str(raw["role"]),
                    arg_line=ints["arg_line"],
                    arg_token=ints["arg_token"],
                    arg_word=str(raw.get("arg_word", "")),
                )
            )

        seen_slots: dict[tuple[int, int], list[tuple[str, int, int]]] = {}
        args_by_pair: dict[tuple[tuple[int, int], tuple[int, int]], set[str]] = {}

        for row in parsed:
            where = f"row[{row.index}]"
            role = row.role

            # 4. role vocabulary.
            if role != "" and role not in VALID_ROLES and not OBL_RE.fullmatch(role):
                errors.append(
                    f"{where}: invalid role {role!r} "
                    f"(valid: {sorted(VALID_ROLES)}, obl:<prep>, or '' for zero-argument)"
                )

            # Zero-argument marker consistency: "" pairs only with (0, 0).
            if role == "" and row.arg != (0, 0):
                errors.append(
                    f"{where}: zero-argument marker '' must cite arg (0, 0), "
                    f"got ({row.arg_line}, {row.arg_token})"
                )

            # 1. predicate existence + word anchor.
            tokens = data.tokens.get(row.line)
            if tokens is None:
                errors.append(
                    f"{where}: predicate line {row.line} does not exist in Layer 1"
                )
            elif not 1 <= row.token <= len(tokens):
                errors.append(
                    f"{where}: predicate token {row.line}.{row.token} out of range "
                    f"(line has {len(tokens)} tokens)"
                )
            else:
                if row.word and not _words_match(row.word, tokens[row.token - 1]):
                    errors.append(
                        f"{where}: predicate word {row.word!r} does not match Layer 1 "
                        f"token {row.line}.{row.token} {tokens[row.token - 1]!r}"
                    )
                if not start <= row.line <= end:
                    errors.append(
                        f"{where}: predicate {row.line}.{row.token} lies outside the "
                        f"parse unit (lines {start}-{end})"
                    )

            # 2. argument citation.
            if row.arg != (0, 0):
                arg_tokens = data.tokens.get(row.arg_line)
                if arg_tokens is None or not 1 <= row.arg_token <= len(arg_tokens):
                    errors.append(
                        f"{where}: argument ({row.arg_line}, {row.arg_token}) does not "
                        f"exist in Layer 1"
                    )
                else:
                    if row.arg_word and not _words_match(
                        row.arg_word, arg_tokens[row.arg_token - 1]
                    ):
                        errors.append(
                            f"{where}: argument word {row.arg_word!r} does not match "
                            f"Layer 1 token {row.arg_line}.{row.arg_token} "
                            f"{arg_tokens[row.arg_token - 1]!r}"
                        )
                    if (
                        requires_nominal_anchor(row.role)
                        and row.arg not in data.np_heads
                        and not data.ctx.is_pronoun(row.arg)
                    ):
                        errors.append(
                            f"{where}: argument {row.arg_line}.{row.arg_token} cites "
                            f"neither a Layer 3 NP head nor a pronoun "
                            f"(nominal role {row.role!r} requires one; clausal and "
                            f"adverbial roles may anchor on any token)"
                        )
                    if not start <= row.arg_line <= end:
                        warnings.append(
                            f"{where}: argument {row.arg_line}.{row.arg_token} lies "
                            f"outside the parse unit (lines {start}-{end})"
                        )

            # 3. slot uniqueness per predicate.
            if tokens is not None and 1 <= row.token <= len(tokens):
                slots = seen_slots.setdefault(row.pred, [])
                slot = (role, row.arg_line, row.arg_token)
                if slot in slots:
                    errors.append(
                        f"{where}: duplicate slot on predicate {row.line}.{row.token}: "
                        f"{role} <- ({row.arg_line}, {row.arg_token})"
                    )
                else:
                    slots.append(slot)
                if row.arg != (0, 0):
                    args_by_pair.setdefault((row.pred, row.arg), set()).add(role)

        # The zero-argument marker is a predicate's single row: it cannot coexist with
        # argument slots on the same predicate.
        for pred, slots in sorted(seen_slots.items()):
            if len(slots) > 1 and any(role == "" for role, _l, _t in slots):
                errors.append(
                    f"predicate {pred[0]}.{pred[1]}: zero-argument marker '' cannot "
                    f"coexist with argument slots"
                )

        # One argument filling two roles of one predicate needs clitic licensing: a fused
        # form whose case annex row carries multiple slots (e.g. `gliel'` = dat + acc).
        for (pred, arg), roles in sorted(args_by_pair.items()):
            if len(roles) < 2:
                continue
            crow = data.case_by_pos.get(arg)
            licensed = crow is not None and len(crow.cases()) > 1
            if not licensed:
                listed = ", ".join(sorted(roles))
                errors.append(
                    f"predicate {pred[0]}.{pred[1]}: argument {arg[0]}.{arg[1]} fills "
                    f"multiple roles ({listed}) without clitic licensing"
                )

        # Same role, several distinct arguments: legal in coordination-heavy readings but
        # worth flagging as a diagnostic.
        roles_by_pred: dict[tuple[int, int], dict[str, int]] = {}
        for row in parsed:
            if row.role == "":
                continue
            counts = roles_by_pred.setdefault(row.pred, {})
            counts[row.role] = counts.get(row.role, 0) + 1
        for pred, counts in sorted(roles_by_pred.items()):
            for role, count in counts.items():
                if count > 1:
                    warnings.append(
                        f"predicate {pred[0]}.{pred[1]} lists {count} distinct {role} "
                        f"arguments"
                    )

        # Upstream discrepancy channel: log verbatim, report malformed records softly.
        feedback_echo: list[dict] = []
        for record in upstream_feedback or []:
            if not isinstance(record, dict):
                warnings.append(f"upstream_feedback record must be a dict: {record!r}")
                continue
            stamped = {
                "canticle": data.canticle,
                "canto": data.number,
                "line_start": start,
                "line_end": end,
                **record,
            }
            self.upstream_log.append(stamped)
            feedback_echo.append(record)
            if not record.get("layer") or not (
                record.get("description") or record.get("issue")
            ):
                warnings.append(
                    f"upstream_feedback record should name 'layer' and a 'description': "
                    f"{record!r}"
                )

        parts: list[str] = []
        if errors:
            parts.append(f"{len(errors)} error(s): {'; '.join(errors)}")
        if warnings:
            parts.append(f"{len(warnings)} warning(s): {'; '.join(warnings)}")
        diagnostics = "; ".join(parts) if parts else "candidate is well-formed"

        return {
            "valid": not errors,
            "errors": errors,
            "warnings": warnings,
            "diagnostics": diagnostics,
            "upstream_feedback": feedback_echo,
        }

    # --- tool-call dispatch ---------------------------------------------------------

    _TOOLS = ("read_unit", "search_corpus", "validate_candidate")

    # Arguments the model may emit as numeric strings; coerced before dispatch so one
    # sloppy JSON type does not burn a whole agent turn.
    _INT_ARGUMENTS = frozenset({"canto", "line_start", "line_end", "limit"})

    def dispatch(self, name: str, arguments: dict | str) -> dict[str, object]:
        """Execute one model-emitted tool call; never raises into the agent loop.

        `arguments` may be a dict or a JSON string (models emit both). Returns
        `{"ok": True, "tool": ..., "result": ...}` on success, or
        `{"ok": False, "tool": ..., "error": "..."}` for an unknown tool, unparsable or
        mistyped arguments, or a rejected request — the error text is written to be fed
        back to the model verbatim so it can self-correct on the next turn.
        """
        if isinstance(arguments, str):
            try:
                arguments = json.loads(arguments)
            except json.JSONDecodeError as exc:
                return self._dispatch_error(name, f"arguments are not valid JSON: {exc}")
        if not isinstance(arguments, dict):
            return self._dispatch_error(
                name, f"arguments must be a JSON object, got {type(arguments).__name__}"
            )
        if name not in self._TOOLS:
            return self._dispatch_error(
                name, f"unknown tool {name!r} (available: {list(self._TOOLS)})"
            )

        coerced = dict(arguments)
        for key in self._INT_ARGUMENTS & coerced.keys():
            value = coerced[key]
            if isinstance(value, str) and value.strip().lstrip("+").isdigit():
                coerced[key] = int(value)

        try:
            result = getattr(self, name)(**coerced)
        except TypeError as exc:
            return self._dispatch_error(name, f"bad arguments for {name}: {exc}")
        except ValueError as exc:
            return self._dispatch_error(name, str(exc))
        except Exception as exc:  # pragma: no cover - defensive: keep the loop alive
            return self._dispatch_error(name, f"{type(exc).__name__}: {exc}")
        return {"ok": True, "tool": name, "result": result}

    @staticmethod
    def _dispatch_error(name: str, message: str) -> dict[str, object]:
        return {"ok": False, "tool": name, "error": message}
