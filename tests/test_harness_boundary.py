"""`dante_corpus/harness/` imports nothing else from `dante_corpus`.

That rule is the whole point of the split: the apparatus was coupled to Layer 5
by a *type* it carried (`skel.models.SkelRow`) rather than by anything it did,
and the split replaced the type with a `RowCodec` the subject supplies. A single
convenience import would put the coupling back, and nothing else would notice —
the tests would pass, the corpus would build, and the apparatus would quietly be
Layer 5's again.

The check reads source, not `sys.modules`, for two reasons. The escapes that
matter are function-local (`fixed_fallback`'s lazy `from .llm import ...`,
`commit`'s lazy `dante_corpus.hashes`), so an import-time check would miss them;
and importing `dante_corpus.harness` at all executes `dante_corpus/__init__.py`,
which pulls the source-text API in, so what actually gets imported can never
show the property this test is about.

The reverse rule is here too: nothing in `dante_corpus/` outside `harness/` may
import `dante_corpus.harness`, which is what keeps `llm7shi` off the corpus
package's own import path.
"""

from __future__ import annotations

import ast
from pathlib import Path

PACKAGE = Path(__file__).resolve().parents[1] / "dante_corpus"
APPARATUS = PACKAGE / "harness"


def _modules(root: Path) -> list[Path]:
    return sorted(p for p in root.rglob("*.py") if "__pycache__" not in p.parts)


def _imported_names(path: Path) -> list[tuple[str, int]]:
    """Every absolute module name the file imports, at any depth, with its line."""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    names: list[tuple[str, int]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names += [(alias.name, node.lineno) for alias in node.names]
        elif isinstance(node, ast.ImportFrom) and not node.level:
            names.append((node.module or "", node.lineno))
    return names


def test_the_apparatus_imports_nothing_else_from_the_corpus():
    offenders = []
    for path in _modules(APPARATUS):
        for name, lineno in _imported_names(path):
            if name == "dante_corpus" or (
                name.startswith("dante_corpus.")
                and not name.startswith("dante_corpus.harness")
            ):
                offenders.append(f"{path.name}:{lineno} imports {name}")
    assert not offenders, "\n".join(offenders)


def test_the_apparatus_does_not_import_the_layer_5_driver():
    """Nor the top-level `harness/` package, which is Layer 5's side."""
    offenders = []
    for path in _modules(APPARATUS):
        for name, lineno in _imported_names(path):
            if name == "harness" or name.startswith("harness."):
                offenders.append(f"{path.name}:{lineno} imports {name}")
    assert not offenders, "\n".join(offenders)


def test_relative_imports_stay_inside_the_package():
    for path in _modules(APPARATUS):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.level:
                assert node.level == 1, (
                    f"{path.name}:{node.lineno} reaches out of the package"
                )


def test_the_corpus_package_does_not_import_the_apparatus():
    """So `llm7shi` stays off `dante_corpus`'s own import path."""
    offenders = []
    for path in _modules(PACKAGE):
        if APPARATUS in path.parents or path.parent == APPARATUS:
            continue
        for name, lineno in _imported_names(path):
            if name.startswith("dante_corpus.harness"):
                offenders.append(f"{path.name}:{lineno} imports {name}")
    assert not offenders, "\n".join(offenders)


def test_the_apparatus_is_importable_on_its_own():
    """It has a public surface, and every name in it resolves."""
    import dante_corpus.harness as apparatus

    missing = [n for n in apparatus.__all__ if not hasattr(apparatus, n)]
    assert not missing, missing
