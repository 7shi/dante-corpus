"""Prompt-side material for the fixed-context loop (`extractor/fixedcontext.py`).

The grammatical knowledge itself is not written here: it lives as plain files in
`skills/grammar-fixed/` and loads through `harness.skills.Skill` (Stage 7). This
module is the assembly layer.

`fixed_system_prompt()` is the whole of the mode's $P$ — role, protocol, answer
contract — and it comes entirely from the skill directory, so
`fixed_skill_digest()` covers every byte of it (`../stages/09.md` §3). There is
no tool-spec or wire-contract section: that mode has no tools.

The Stage-1 tool-calling assembly that used to sit beside this one — the role
intro, the two 5-step protocols, the wire contract, the tool specs, and the
few-shot demonstration — went with the session it served (2026-09-07).
"""

from __future__ import annotations

from pathlib import Path

from harness.skills import Skill

__all__ = [
    "FIXED_SKILL",
    "fixed_skill_digest",
    "fixed_system_prompt",
]

_SKILLS = Path(__file__).resolve().parent / "skills"

# Stage 9's $P$ (`../stages/09.md` §3): the domain knowledge with the tool step
# removed and the answer contract in its place.
FIXED_SKILL = Skill.load(_SKILLS / "grammar-fixed")


def fixed_skill_digest() -> str:
    """Fingerprint of the fixed-context skill's wording (Standing Invariant §6).

    Standing Invariant §6 fixes a run's session semantics for its whole duration;
    logging this digest is what lets that be checked after the fact, and what
    tells two runs' records apart when the wording did change between them. The
    skill *is* $P$ here, so the digest covers the prompt entire.
    """
    return FIXED_SKILL.digest()


def fixed_system_prompt() -> str:
    """Assemble $P$: role + protocol + answer contract.

    No tool specs and no wire contract — there are no tools — so every byte of
    this string comes from the skill directory and rides its digest.
    """
    return "\n\n".join(
        [
            FIXED_SKILL.body,
            FIXED_SKILL.resource("protocol.md"),
            FIXED_SKILL.resource("answer.md"),
        ]
    )
