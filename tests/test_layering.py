"""Layering rules for this package: no upstream package, one version source.

Three gates, all ``static``:

- ``src/`` never imports ``pyssp_standard`` or ``pyssp_sysml2``; the point of
  this repository is that the dialect layer stands on its own, and an import of
  either upstream package would silently reintroduce the coupling;
- ``pyproject.toml`` reads the version from the package, never from a copy;
- every collected test carries exactly one level marker.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

from conftest import COLLECTED_LEVELS, FILE_LEVELS, MIXED_FILES, MIXED_LEVELS

PROJECT = Path(__file__).resolve().parents[1]
SRC = PROJECT / "src"
PACKAGE = SRC / "pycps_sysml2"

#: Upstream packages this library must not depend on, at any depth.
FORBIDDEN_IMPORT_ROOTS = ("pyssp_standard", "pyssp_sysml2")


def _imported_modules(path: Path) -> list[tuple[str, int]]:
    """Every imported module name with the line it appears on."""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    sites: list[tuple[str, int]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            sites.extend((alias.name, node.lineno) for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                # A relative import can never name an upstream package.
                continue
            if node.module:
                sites.append((node.module, node.lineno))
            sites.extend((alias.name, node.lineno) for alias in node.names)
    return sites


def test_src_does_not_import_an_upstream_package() -> None:
    """An upstream import would make this package a wrapper, not a layer."""
    violations: list[str] = []
    for path in sorted(SRC.rglob("*.py")):
        for module, line in _imported_modules(path):
            root = module.lstrip(".").split(".", 1)[0]
            if root in FORBIDDEN_IMPORT_ROOTS:
                violations.append(
                    f"{path.relative_to(PROJECT)}:{line} imports {module}"
                )
    assert not violations, (
        "src/ must not import pyssp_standard or pyssp_sysml2:\n"
        + "\n".join(violations)
    )


def test_the_version_has_one_source_of_truth() -> None:
    """``pyproject.toml`` reads the version from the package, not a copy."""
    import pycps_sysml2

    tomllib = pytest.importorskip("tomllib", reason="tomllib is Python 3.11+")
    project = tomllib.loads((PROJECT / "pyproject.toml").read_text(encoding="utf-8"))

    assert "version" not in project["project"]
    assert project["project"]["dynamic"] == ["version"]
    assert project["tool"]["setuptools"]["dynamic"]["version"] == {
        "attr": "pycps_sysml2.__version__"
    }
    assert re.fullmatch(r"\d+\.\d+\.\d+", pycps_sysml2.__version__)

    # And the attribute is assigned in exactly one module.
    assignments: list[str] = []
    for path in sorted(SRC.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            targets: list[ast.expr] = []
            if isinstance(node, ast.Assign):
                targets = list(node.targets)
            elif isinstance(node, ast.AnnAssign):
                targets = [node.target]
            if any(
                isinstance(target, ast.Name) and target.id == "__version__"
                for target in targets
            ):
                assignments.append(str(path.relative_to(PROJECT)))
    expected = [str((PACKAGE / "__init__.py").relative_to(PROJECT))]
    assert assignments == expected, (
        "__version__ must be assigned once, in pycps_sysml2/__init__.py: "
        f"{assignments}"
    )


def test_every_collected_test_declares_exactly_one_level(
    request: pytest.FixtureRequest,
) -> None:
    """The level marker is how a reader knows what a green test is evidence for."""
    collected = request.config.stash[COLLECTED_LEVELS]
    assert collected, "collection recorded no tests"

    missing = [node for node, levels in collected.items() if not levels]
    assert not missing, (
        "test files without a level marker; add them to FILE_LEVELS in "
        "tests/conftest.py:\n" + "\n".join(sorted(missing))
    )

    wrong: list[str] = []
    for node, levels in sorted(collected.items()):
        if len(levels) == 1:
            continue
        file_name = node.split("::", 1)[0].rsplit("/", 1)[-1]
        if set(levels) == set(MIXED_LEVELS) and file_name in MIXED_FILES:
            continue
        wrong.append(f"{node}: {levels}")
    assert not wrong, (
        "a test must carry exactly one level marker, or both levels of a "
        "declared mixed file:\n" + "\n".join(wrong)
    )

    unused = [
        name
        for name in sorted(FILE_LEVELS)
        if not (Path(__file__).resolve().parent / name).is_file()
    ]
    assert not unused, f"FILE_LEVELS names files that do not exist: {unused}"
