"""The `grammar-fixed` skill files and the prompt they assemble.

Stage 7 moved the agent's grammatical knowledge out of Python string constants
into files under `runner/skills/`, and Stage 9 narrowed those to
`grammar-fixed/`. These tests hold the property that move earns its keep by:
the prompt the model receives is assembled from the files alone, so a wording
change is a file diff and nothing else.

The loader itself (`dante_corpus.harness.skills`) is the apparatus's, and its
tests live at the repository root in `tests/test_harness_apparatus.py` — this
file is Layer 5's half, and it closed with `harness/`.
"""

from __future__ import annotations

from harness.runner import prompts


# --- the fixed-context skill -------------------------------------------------------------


def test_the_fixed_skill_declares_every_section_the_prompt_assembles():
    skill = prompts.FIXED_SKILL
    assert skill.name == "grammar-fixed"
    assert set(skill.resources) == {"protocol.md", "answer.md"}


def test_the_fixed_system_prompt_is_assembled_from_the_skill_files_alone():
    # Nothing grammatical is left in prompts.py: every section of the assembled
    # prompt traces back to a file, which is what makes a wording change a diff.
    skill = prompts.FIXED_SKILL
    prompt = prompts.fixed_system_prompt()
    for section in (skill.body, skill.resource("protocol.md"), skill.resource("answer.md")):
        assert section in prompt
    # There is no tool-spec or wire-contract section: the mode has no tools, so
    # the digest below covers the prompt entire.
    assert len(prompt) == sum(
        len(s) for s in (skill.body, skill.resource("protocol.md"), skill.resource("answer.md"))
    ) + 4


def test_fixed_skill_digest_is_the_fixed_skills_digest():
    assert prompts.fixed_skill_digest() == prompts.FIXED_SKILL.digest()
