"""The apparatus's own tests: what `dante_corpus/harness/` does with no subject.

`harness/` closed on 2026-09-08, and its tests went with it into
`harness/tests/` — but the apparatus did not close: it is the library
[`../layers/PLAN.md`](../layers/PLAN.md) drives, and a second subject will
reach exactly the code below. These are the tests that never needed Layer 5 to
say what they say, so they stay here, in the suite this repository maintains.

The criterion is mechanical, and `test_harness_boundary.py` holds its mirror
image for the source: **nothing here imports from top-level `harness/`.** Rows
appear as `SkelRow` where a row is needed, because that is the corpus's own row
type and the apparatus takes any row a codec can read — not because Layer 5 is
under test.

What is *not* here, deliberately: everything whose meaning comes from the
subject. The canto loop over frozen layers, the gates' content, the `--fix`
levels and their verdicts, the artifact's byte-exactness against `write_skel` —
those are exercised through Layer 5's bindings in `harness/tests/`, which a
bare `uv run pytest` no longer collects (`pyproject.toml`'s `testpaths`).
"""

from __future__ import annotations

import pytest

from dante_corpus.harness import fixedcontext as fx
from dante_corpus.harness.fixrun import row_delta
from dante_corpus.harness.report import ReconstructReport
from dante_corpus.harness.skills import Skill, SkillError
from dante_corpus.skel.models import SkelRow


# --- the skill loader: `skills.py` ---------------------------------------------------------

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


# --- the bounded step's wire: $\Sigma$ in and out (`fixedcontext.py`) --------------------

def test_parse_rows_reads_the_block_and_skips_the_furniture():
    text = (
        "reasoning\n<rows>\n"
        "line\ttoken\tword\trole\targ_line\targ_token\n"
        "2\t2\tritrovai\tsubj\t0\t0\n"
        "3\t0\t\t\t0\t0\n"  # the artifact's empty-line filler: not a row
        "garbage line without fields\n"
        "</rows>\ntrailing prose"
    )
    rows = fx.parse_rows(text)
    assert rows == [
        {
            "line": 2,
            "token": 2,
            "word": "ritrovai",
            "role": "subj",
            "arg_line": 0,
            "arg_token": 0,
        }
    ]


def test_parse_rows_accepts_space_separated_rows_and_refuses_no_block():
    assert fx.parse_rows("<rows>\n2 2 ritrovai subj 0 0\n</rows>")[0]["role"] == "subj"
    assert fx.parse_rows("I decline to answer") == []
    assert fx.parse_rows("") == []


def test_render_sigma_is_the_artifact_table():
    assert "no rows on record" in fx.render_sigma([])
    text = fx.render_sigma(
        [{"line": 2, "token": 2, "word": "x", "role": "obj", "arg_line": 2, "arg_token": 5}]
    )
    assert text.splitlines()[0].split("\t") == list(fx._TSV_HEADER)
    assert text.splitlines()[1] == "2\t2\tx\tobj\t2\t5"


# --- the run report: `report.py` -----------------------------------------------------------

def test_report_faces_aggregate_streamed_records():
    report = ReconstructReport()
    unit_record = {
        "record": "unit", "canticle": "inferno", "canto": 1,
        "line_start": 1, "line_end": 5, "route": "agent", "reason": "no_rows",
        "passed": False, "token_assertion_errors": 1, "hard_violations": 1,
        "soft_violations": 2, "violation_kinds": {"tag": 2}, "fallback_seconds": 3.5,
    }
    report.add_unit(unit_record)
    report.add_unit({
        **unit_record,
        "passed": True,
        "token_assertion_errors": 0,
        "hard_violations": 0,
        "soft_violations": 0,
        "violation_kinds": {},
        "fallback_seconds": None,
    })
    report.add_canto_complete(
        {"record": "canto_complete", "canticle": "inferno", "canto": 1,
         "units": 2, "passed": False}
    )
    report.add_canto_complete(
        {"record": "canto_complete", "canticle": "inferno", "canto": 2,
         "units": 1, "passed": True,
         "commit": {"wrote": True}}
    )
    metrics = report.metrics()
    assert metrics["units"] == 2 and metrics["passed_units"] == 1
    assert metrics["blocked_units"] == 1
    assert metrics["cantos_passed"] == 1
    assert metrics["written_cantos"] == 1
    assert metrics["token_assertion_errors"] == 1
    assert metrics["fallback_seconds_total"] == 3.5
    text = report.summary()
    assert "0 hard / 0 soft" in text
    assert "written 1" in text


# --- the fix machinery's row accounting: `fixrun.py` ---------------------------------------

def test_row_delta_names_the_mechanism():
    before = {1: [SkelRow(1, 2, "w", "obl", 1, 4), SkelRow(1, 2, "w", "subj", 0, 0)]}
    after = {1: [SkelRow(1, 2, "w", "obl:di", 1, 4), SkelRow(1, 2, "w", "obj", 1, 5)]}
    assert row_delta(before, after) == {
        "rows_before": 2, "rows_after": 2,
        "rows_added": 1, "rows_removed": 1, "rows_relabelled": 1,
    }
