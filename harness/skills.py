"""File-based skills: the agent's domain knowledge as plain, reviewable files.

A *skill* is a directory holding a `SKILL.md` — YAML-ish frontmatter naming the
skill plus a body that is prompt text verbatim — and any number of sibling
`.md` resource files the frontmatter declares. `Skill.load()` reads the
directory; `skill.body` and `skill.resource(name)` return prompt text ready to
paste into a system prompt, and `skill.digest()` fingerprints the whole
directory so a run's log can record which wording it ran under (Standing
Invariant §6, session semantics stability: semantics may change between runs but
never mid-run, and the digest is how that is checked afterwards).

Why files rather than Python string constants: prompt wording is domain
knowledge, not code. As files it diffs on its own, reviews on its own, and can
be extended without touching the assembly logic — and the body is stored exactly
as the model receives it, so what a reviewer reads is what the model reads.

The frontmatter parser is deliberately tiny — scalars and one level of nested
mapping, which is all a skill header needs — so this module adds no dependency
to a project that has one.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from pathlib import Path

__all__ = ["Skill", "SkillError"]

_FENCE = "---"


class SkillError(Exception):
    """A skill directory is missing, malformed, or missing a declared resource."""


def _split_frontmatter(text: str, where: Path) -> tuple[list[str], str]:
    """Return (frontmatter lines, body) for a `---`-fenced document."""
    lines = text.split("\n")
    if not lines or lines[0].strip() != _FENCE:
        raise SkillError(f"{where}: expected a '{_FENCE}' frontmatter fence on line 1")
    for i in range(1, len(lines)):
        if lines[i].strip() == _FENCE:
            return lines[1:i], "\n".join(lines[i + 1 :]).strip("\n")
    raise SkillError(f"{where}: unterminated '{_FENCE}' frontmatter")


def _parse_frontmatter(lines: list[str], where: Path) -> dict[str, object]:
    """Parse `key: value` scalars plus one level of indented nested mappings."""
    meta: dict[str, object] = {}
    current: dict[str, str] | None = None
    for lineno, raw in enumerate(lines, start=2):
        if not raw.strip():
            continue
        indented = raw[:1].isspace()
        key, sep, value = raw.strip().partition(":")
        if not sep:
            raise SkillError(f"{where}:{lineno}: expected 'key: value', got {raw!r}")
        key, value = key.strip(), value.strip()
        if indented:
            if current is None:
                raise SkillError(f"{where}:{lineno}: indented entry outside a mapping")
            current[key] = value
            continue
        if value:
            meta[key], current = value, None
        else:
            current = {}
            meta[key] = current
    return meta


@dataclass(frozen=True)
class Skill:
    """One skill directory: its metadata, its body, and its resource files."""

    path: Path
    name: str
    description: str
    body: str
    resources: dict[str, str] = field(default_factory=dict)

    @classmethod
    def load(cls, path: str | Path) -> "Skill":
        directory = Path(path)
        entry = directory / "SKILL.md"
        if not entry.is_file():
            raise SkillError(f"{directory}: no SKILL.md")
        front, body = _split_frontmatter(entry.read_text(encoding="utf-8"), entry)
        meta = _parse_frontmatter(front, entry)
        for required in ("name", "description"):
            if not isinstance(meta.get(required), str):
                raise SkillError(f"{entry}: frontmatter needs a '{required}:' scalar")
        resources = meta.get("resources", {})
        if not isinstance(resources, dict):
            raise SkillError(f"{entry}: 'resources:' must be a nested mapping")
        for filename in resources:
            if not (directory / filename).is_file():
                raise SkillError(f"{entry}: declares missing resource {filename!r}")
        return cls(
            path=directory,
            name=meta["name"],  # type: ignore[arg-type]
            description=meta["description"],  # type: ignore[arg-type]
            body=body,
            resources=dict(resources),
        )

    def resource(self, filename: str) -> str:
        """Prompt text of one declared resource file, trailing newlines stripped.

        Only declared resources load: the frontmatter is the skill's manifest, so
        an undeclared file is a mistake rather than a silent extension point.
        """
        if filename not in self.resources:
            raise SkillError(f"{self.path}: resource {filename!r} is not declared")
        return (self.path / filename).read_text(encoding="utf-8").strip("\n")

    def files(self) -> list[Path]:
        """Every file the skill is made of, in stable order."""
        return [self.path / "SKILL.md"] + [
            self.path / name for name in sorted(self.resources)
        ]

    def digest(self) -> str:
        """A stable fingerprint of the skill's wording, for the run log."""
        h = hashlib.sha256()
        for file in self.files():
            h.update(file.name.encode("utf-8"))
            h.update(b"\0")
            h.update(file.read_bytes())
            h.update(b"\0")
        return h.hexdigest()
