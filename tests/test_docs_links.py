"""Every relative Markdown link in the repository resolves to a file that exists.

The documents are the project's memory: plans, phase retrospectives, per-layer
CORRECTIONS records and the stage documents all cite each other, and a citation
that no longer resolves is how a record quietly stops being checkable. Commit
`ee47f34` repaired 23 such links at once — documents retired into successors,
sections dropped before their document was, and a directory moved to another
repository — and that only surfaced because the harness stage files were being
renamed at the time. This test is the sweep that ran then, kept so the next
rename or retirement fails here instead of years later.

Scope, deliberately narrow: link *targets* that name a path. Anchors (`#...`)
are stripped rather than verified, and external URLs are not fetched — neither
can be checked offline, and a test that needs the network is a test that gets
skipped.
"""

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

# `](target)` — the only link form the repository's documents use.
LINK_RE = re.compile(r"\]\(([^)\s]+)\)")

SKIP_PREFIXES = ("http://", "https://", "mailto:", "#")
SKIP_DIRS = {".git", ".venv", "node_modules", "__pycache__"}


def markdown_files(root: Path) -> list[Path]:
    """Every tracked-looking `.md` file under `root`, tooling directories excluded."""
    return sorted(
        path
        for path in root.rglob("*.md")
        if not any(part in SKIP_DIRS or part.startswith(".") for part in path.relative_to(root).parts)
    )


def broken_links(root: Path) -> list[str]:
    """`file -> target` for every relative link whose target is missing."""
    broken = []
    for md in markdown_files(root):
        for target in LINK_RE.findall(md.read_text(encoding="utf-8")):
            if target.startswith(SKIP_PREFIXES):
                continue
            path = (md.parent / target.split("#", 1)[0]).resolve()
            if not path.exists():
                broken.append(f"{md.relative_to(root)} -> {target}")
    return broken


def test_repository_markdown_links_resolve():
    broken = broken_links(REPO_ROOT)
    assert not broken, "broken Markdown links:\n  " + "\n  ".join(broken)


def test_every_layer_and_stage_document_is_swept():
    """The sweep must actually reach the documents that cite each other the most."""
    swept = {path.relative_to(REPO_ROOT).as_posix() for path in markdown_files(REPO_ROOT)}
    for expected in (
        "PLAN.md",
        "harness/PLAN.md",
        "harness/stages/01.md",
        "skel/PHASE6.md",
        "dep/CORRECTIONS.md",
        "case/CORRECTIONS.md",
        "src/README.md",
    ):
        assert expected in swept, f"{expected} was not swept"


def test_checker_reports_a_missing_target(tmp_path):
    """Pins the check itself: a dead relative link must be reported, a live one must not."""
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "present.md").write_text("ok\n", encoding="utf-8")
    (tmp_path / "doc.md").write_text(
        "[live](sub/present.md) [dead](sub/missing.md)\n", encoding="utf-8"
    )

    assert broken_links(tmp_path) == ["doc.md -> sub/missing.md"]


def test_checker_strips_anchors_and_skips_external_targets(tmp_path):
    """An anchor is not a path, and an external URL is not ours to resolve."""
    (tmp_path / "present.md").write_text("ok\n", encoding="utf-8")
    (tmp_path / "doc.md").write_text(
        "[anchored](present.md#a-heading) [web](https://example.invalid/x)\n"
        "[anchor only](#local) [dead anchor](gone.md#h)\n",
        encoding="utf-8",
    )

    assert broken_links(tmp_path) == ["doc.md -> gone.md#h"]
