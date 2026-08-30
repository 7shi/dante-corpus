"""Prompt-side material for Stage 1 autonomous inference (`harness/runner/PLAN.md` §4).

`system_prompt(specs)` assembles the per-unit system prompt from three sections:

1. the role framing and the 5-step grammatical reasoning protocol (this module),
2. the tool-call wire contract (`toolcall.prompts.xml_contract_section`),
3. the closed tool surface (`toolcall.prompts.tool_specs_section(TOOL_SPECS)`).

`unit_task(unit)` renders the one user message that opens a session: solve exactly
one parse unit and finish with validated candidate rows.

The few-shot demonstration is deliberately **non-colliding**: its search content is
an empty-result lookup for a lemma far from any fixture unit, so an echo of it in a
final answer is both harmless and instantly diagnosable (the live probe's 'cammin'
demo leaked into every final answer — see `harness/TOOLCALL.md` T4).
"""

from __future__ import annotations

from typing import Sequence

from harness.toolcall import tool_specs_section, xml_contract_section

__all__ = [
    "ROLE_INTRO",
    "REASONING_PROTOCOL",
    "few_shot_messages",
    "system_prompt",
    "unit_task",
]

ROLE_INTRO = """\
You are a grammar analysis agent reconstructing Layer 5 predicate-argument \
skeletons for the Divina Commedia. You receive multi-layer grammatical context \
(Layer 1 tokens and verse text, quotes hierarchy, Layer 2 morphology, the pronoun \
case annex, Layer 3 noun phrases, Layer 4 Universal Dependencies trees) through a \
closed toolset, and you produce skeleton rows: one row per (predicate, argument) \
pair.

Skeleton row conventions:

- Each row names a predicate by (line, token) plus optionally its word, and one \
argument by role plus (arg_line, arg_token); word / arg_word are optional \
verification anchors — coordinates alone identify the token, so omit them to \
keep calls compact.
- Roles come from the frozen vocabulary: subj, obj, iobj, attr, xcomp, ccomp, \
obl (an adverbial oblique), obl:<prep> (e.g. obl:di), or "" (a zero-argument \
predicate's single row).
- A pro-drop argument (unexpressed subject, omitted clitic complement) cites \
(0, 0).
- Nominal arguments (subj, obj, iobj, obl:<prep>) must cite the head token of \
their Layer 3 noun phrase; pronouns and clitics cite their own token and take \
their case from the annex. Clausal roles anchor elsewhere by nature: xcomp / \
ccomp / attr cite the complement's own predicate-head token, and bare obl cites \
its adverb — no NP-head requirement applies there."""

STEPS_1_TO_4 = """\
## 5-step reasoning protocol

Work through these steps in order for every parse unit. Think step by step in \
plain prose between tool calls; never state a fact about the text that a tool did \
not just show you.

### Step 1 - Discourse & quote boundaries

Call `read_unit` for the target unit. Read the quotes hierarchy first: direct \
speech spans and speaker boundaries decide whether a name is a vocative inside a \
quote or a subject of narration, and embedded quotes shift attribution. Note the \
unit bounds; every citation you make later must fall inside them.

### Step 2 - Predicates, agreement & voice

From Layer 2 morphology, enumerate every verbal token in the unit (finite verbs, \
participles, infinitives, gerunds). For each finite verb check person/number \
agreement against candidate nominative arguments: agreement with nothing visible \
means a pro-drop subject `(0, 0)`. Identify passive constructions and reflexive \
`si` before assigning roles.

### Step 3 - Case & core argument discrimination

Resolve pronouns and clitics through the pronoun case annex: case (nom / acc / \
dat / ...) decides `subj` vs `obj` vs `iobj`, not word order. Project Layer 4 UD \
relations onto roles (`nsubj` to `subj`, `obj` to `obj`, `iobj` to `iobj`, \
preposition-governed obliques to `obl:<prep>`). Use `search_corpus` when you need \
analogous constructions from other cantos to disambiguate. If Layer 2 or Layer 4 \
is defective beyond repair, say so explicitly and pass an `upstream_feedback` \
record with your validation call instead of forcing a reading.

### Step 4 - NP heads, clausal complements & control

Cite nominal arguments at their exact Layer 3 phrase-head tokens. Attach \
infinitival complements as `xcomp` when the complement subject is controlled by \
the matrix predicate, as `ccomp` otherwise; trace control chains across the whole \
unit so no predicate loses its arguments."""


STEP5_UNIT = """\
### Step 5 - Intrinsic validation & self-correction

Submit all rows of the unit in one `validate_candidate` call. Read ok="false" \
payloads and error diagnostics literally: repair exactly what they name and call \
again. Iterate until the result reports `"valid": true`, then stop working and \
give your final answer: a short summary of the predicates, their roles, and any \
upstream feedback you filed. Never answer in prose alone without having validated \
a candidate."""

STEP5_PREDICATE = """\
### Step 5 - Per-predicate validation & self-correction

Work through the predicates you enumerated in Step 2, one at a time, in text \
order. For each predicate: state its frame briefly (a sentence or two — which \
arguments, which case), then call `validate_candidate` with only that \
predicate's rows. Never batch several predicates into one call. Read ok="false" \
payloads and error diagnostics literally and repair exactly what they name; if a \
frame cannot be made well-formed at all, say so and file an `upstream_feedback` \
record with that predicate's validation call instead of dropping rows silently. \
After the last predicate, stop working and give your final answer: a short list \
of the validated predicates (predicate token -> roles) plus any upstream \
feedback you filed. Never answer in prose alone without having validated every \
predicate."""

REASONING_PROTOCOL = STEPS_1_TO_4 + "\n\n" + STEP5_UNIT
PREDICATE_PROTOCOL = STEPS_1_TO_4 + "\n\n" + STEP5_PREDICATE

WORKFLOWS = ("unit", "predicate")

_PROTOCOLS = {"unit": REASONING_PROTOCOL, "predicate": PREDICATE_PROTOCOL}


def system_prompt(specs: Sequence[dict], workflow: str = "unit") -> str:
    """Assemble the per-unit system prompt: protocol + wire contract + tool specs.

    `workflow` selects the validation granularity taught by Step 5: "unit" submits
    every row of the unit in one call; "predicate" validates one predicate's rows
    per call, interleaving reasoning and feedback.
    """
    return "\n\n".join(
        [
            ROLE_INTRO,
            _PROTOCOLS[workflow],
            xml_contract_section(),
            tool_specs_section(specs),
        ]
    )


def unit_task(
    canticle: str,
    canto: int,
    line_start: int,
    line_end: int | None = None,
    revision: str | None = None,
) -> str:
    """The opening user message assigning one parse unit.

    `revision`, when given (a Stage-6 `--fix` run, `extractor/fixlevel.py`),
    appends the unit's already-recorded rows plus one notice per position whose
    invariant they break. The notices name the invariant and the frozen-layer
    evidence only: the derivation's own answer never enters the session
    (`../STAGE5.md` record S5.5, and the departure recorded in `../STAGE6.md`).
    """
    span = f"lines {line_start}-{line_end}" if line_end else f"line {line_start}"
    task = (
        "<task>\n"
        f"Solve the parse unit containing {canticle} {canto}, {span}.\n"
        "Follow the 5-step reasoning protocol: read the unit, work out the "
        "predicate-argument frames layer by layer, then validate your candidate "
        "rows and iterate until they are well-formed.\n"
        "</task>"
    )
    return task if revision is None else f"{task}\n\n{revision}"


def few_shot_messages() -> list[dict]:
    """A minimal demonstration exchange with deliberately non-colliding content.

    The demo searches a rare lemma of a word foreign to the fixture units and shows
    an *empty* hit list, so there is no plausible content to echo into a final
    answer (the live probe's 'cammin' demo was echoed verbatim despite contract
    rule 7). Kept parse-consistent with `toolcall.parser.parse_tool_calls`.
    """
    return [
        {
            "role": "user",
            "content": (
                "<task>\n"
                "(Demonstration only.) Find occurrences of the German lemma "
                "'Waldeinsamkeit' outside this canto.\n"
                "</task>"
            ),
        },
        {
            "role": "assistant",
            "content": (
                "This is a format illustration, so I will simply run the requested "
                "search outside the current canto.\n"
                "<tool_call>\n"
                '{"name": "search_corpus", '
                '"arguments": {"query": {"lemma": "Waldeinsamkeit"}, "limit": 5}}\n'
                "</tool_call>"
            ),
        },
        {
            "role": "user",
            "content": (
                '<tool_result tool="search_corpus" ok="true">\n'
                "[]\n"
                "</tool_result>\n"
                "(End of demonstration. It shows only the wire format: think in "
                "prose, emit one JSON object per <tool_call> block, read "
                "<tool_result> blocks. Never reuse demonstration content."
            ),
        },
    ]
