"""File-based skills (`harness/skills.py`) and the grammar skill they carry.

Stage 7 moved the agent's grammatical knowledge out of Python string constants
into `harness/runner/skills/grammar-agent/`. These tests hold the two properties
that move earns its keep by: the loader refuses a malformed or under-declared
skill rather than silently serving a partial prompt, and the prompt the model
receives is assembled from the files alone — so a wording change is a file diff
and nothing else.
"""

from __future__ import annotations

import pytest

from harness.runner import prompts
from harness.runner.tools import TOOL_SPECS
from harness.skills import Skill, SkillError


def write_skill(root, *, front: str, body: str = "Body.", **resources: str):
    directory = root / "demo"
    directory.mkdir()
    (directory / "SKILL.md").write_text(f"---\n{front}\n---\n\n{body}\n", encoding="utf-8")
    for name, text in resources.items():
        (directory / f"{name}.md").write_text(text + "\n", encoding="utf-8")
    return directory


# --- the loader --------------------------------------------------------------------------


def test_load_reads_frontmatter_body_and_declared_resources(tmp_path):
    directory = write_skill(
        tmp_path,
        front="name: demo\ndescription: A demo skill.\nresources:\n  extra.md: Extra material.",
        body="Line one.\n\nLine two.",
        extra="Extra body.",
    )
    skill = Skill.load(directory)
    assert (skill.name, skill.description) == ("demo", "A demo skill.")
    assert skill.body == "Line one.\n\nLine two."
    assert skill.resources == {"extra.md": "Extra material."}
    assert skill.resource("extra.md") == "Extra body."


def test_body_and_resources_drop_only_the_files_trailing_newline(tmp_path):
    # Prompt text is stored exactly as the model receives it, so the only thing
    # the loader may strip is the newline POSIX puts at the end of a file.
    directory = write_skill(
        tmp_path,
        front="name: demo\ndescription: d\nresources:\n  extra.md: e",
        body="  indented and  spaced  ",
        extra="  padded  ",
    )
    skill = Skill.load(directory)
    assert skill.body == "  indented and  spaced  "
    assert skill.resource("extra.md") == "  padded  "


@pytest.mark.parametrize(
    "front, message",
    [
        ("description: d", "'name:'"),
        ("name: demo", "'description:'"),
        ("name: demo\ndescription: d\nresources:\n  missing.md: m", "missing resource"),
    ],
)
def test_load_refuses_an_incomplete_skill(tmp_path, front, message):
    directory = write_skill(tmp_path, front=front)
    with pytest.raises(SkillError, match=message):
        Skill.load(directory)


def test_load_refuses_a_document_without_frontmatter(tmp_path):
    directory = tmp_path / "demo"
    directory.mkdir()
    (directory / "SKILL.md").write_text("No frontmatter here.\n", encoding="utf-8")
    with pytest.raises(SkillError, match="frontmatter fence"):
        Skill.load(directory)


def test_load_refuses_a_missing_directory(tmp_path):
    with pytest.raises(SkillError, match="no SKILL.md"):
        Skill.load(tmp_path / "absent")


def test_an_undeclared_resource_does_not_load(tmp_path):
    # The frontmatter is the manifest: a stray file beside SKILL.md is a mistake,
    # not an extension point that silently starts feeding the model.
    directory = write_skill(tmp_path, front="name: demo\ndescription: d")
    (directory / "stray.md").write_text("Stray.\n", encoding="utf-8")
    skill = Skill.load(directory)
    with pytest.raises(SkillError, match="not declared"):
        skill.resource("stray.md")


def test_digest_covers_every_file_and_changes_with_the_wording(tmp_path):
    directory = write_skill(
        tmp_path,
        front="name: demo\ndescription: d\nresources:\n  extra.md: e",
        extra="Extra body.",
    )
    before = Skill.load(directory).digest()
    assert Skill.load(directory).digest() == before  # stable across loads
    (directory / "extra.md").write_text("Extra body, revised.\n", encoding="utf-8")
    assert Skill.load(directory).digest() != before


# --- the grammar skill -------------------------------------------------------------------


def test_the_grammar_skill_declares_every_section_the_prompt_assembles():
    skill = prompts.GRAMMAR_SKILL
    assert skill.name == "grammar-agent"
    assert set(skill.resources) == {"protocol.md", "step5-unit.md", "step5-predicate.md"}


def test_the_system_prompt_is_assembled_from_the_skill_files_alone():
    # Nothing grammatical is left in prompts.py: every section of the assembled
    # prompt traces back to a file, which is what makes a wording change a diff.
    skill = prompts.GRAMMAR_SKILL
    for workflow, step5 in (("unit", "step5-unit.md"), ("predicate", "step5-predicate.md")):
        prompt = prompts.system_prompt(TOOL_SPECS, workflow)
        for section in (skill.body, skill.resource("protocol.md"), skill.resource(step5)):
            assert section in prompt
    # ...and the two workflows differ by exactly their Step 5.
    assert skill.resource("step5-predicate.md") not in prompts.system_prompt(TOOL_SPECS, "unit")


def test_skill_digest_is_the_grammar_skills_digest():
    assert prompts.skill_digest() == prompts.GRAMMAR_SKILL.digest()
