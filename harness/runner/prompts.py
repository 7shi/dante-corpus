"""Prompt-side material for Stage 1 autonomous inference (`harness/runner/PLAN.md` §4).

The grammatical knowledge itself is not written here: it lives as plain files in
`skills/grammar-agent/` and loads through `harness.skills.Skill` (Stage 7). This
module is the assembly layer — which sections a workflow gets, in what order,
and how the opening user message is worded.

`system_prompt(specs)` assembles the per-unit system prompt from three sections:

1. the role framing and the 5-step grammatical reasoning protocol (the skill),
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

from pathlib import Path
from typing import Sequence

from harness.skills import Skill
from harness.toolcall import tool_specs_section, xml_contract_section

__all__ = [
    "GRAMMAR_SKILL",
    "ROLE_INTRO",
    "REASONING_PROTOCOL",
    "few_shot_messages",
    "skill_digest",
    "system_prompt",
    "unit_task",
]

GRAMMAR_SKILL = Skill.load(Path(__file__).resolve().parent / "skills" / "grammar-agent")

ROLE_INTRO = GRAMMAR_SKILL.body
STEPS_1_TO_4 = GRAMMAR_SKILL.resource("protocol.md")
STEP5_UNIT = GRAMMAR_SKILL.resource("step5-unit.md")
STEP5_PREDICATE = GRAMMAR_SKILL.resource("step5-predicate.md")

REASONING_PROTOCOL = STEPS_1_TO_4 + "\n\n" + STEP5_UNIT
PREDICATE_PROTOCOL = STEPS_1_TO_4 + "\n\n" + STEP5_PREDICATE

WORKFLOWS = ("unit", "predicate")

_PROTOCOLS = {"unit": REASONING_PROTOCOL, "predicate": PREDICATE_PROTOCOL}


def skill_digest() -> str:
    """Fingerprint of the grammar skill's wording, recorded by live runs.

    Standing Invariant §6 fixes a run's session semantics for its whole duration;
    logging this digest is what lets that be checked after the fact, and what
    tells two runs' records apart when the wording did change between them.
    """
    return GRAMMAR_SKILL.digest()


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
    (`../stages/05.md` record S5.5, and the departure recorded in `../stages/06.md`).
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
