"""Static policy for the fixture tree: every case explains and lists its bytes.

A fixture directory is only evidence if a reader can tell what it is and which
files belong to it. Those facts live in ``case.md`` next to the data; this file
makes the record mandatory instead of customary. It also keeps documents out of
test modules: a SysML architecture belongs in a file, not in a 40-line literal.
It reads text and stat only, so it is ``static``.

Deliberate extension over the template this was ported from: the mandatory
section headings are enforced on *every* ``tests/fixtures/*/case.md``, not only
on golden case records. A fixture directory is reviewable evidence, so the
record has to be structured even when no generated artifact is committed.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

TESTS = Path(__file__).resolve().parent
FIXTURES = TESTS / "fixtures"

#: Files a case record must name, by suffix.
DATA_SUFFIXES = frozenset(
    {".sysml", ".ssd", ".ssv", ".ssm", ".xml", ".json", ".csv", ".txt"}
)

#: A literal with more newlines than this is a document, and documents live in
#: ``tests/fixtures/``. Fragments that a test interpolates stay inline.
INLINE_NEWLINE_LIMIT = 15

#: Exceptions, keyed ``<file>:<line>`` with the reason it stays inline.
INLINE_ALLOWLIST: dict[str, str] = {}

#: The case record is the manifest, not a generated artifact.
RECORD = "case.md"

#: Section headings every case record must carry; see ``tests/README.md``.
REQUIRED_HEADINGS = (
    "# Case:",
    "## Artifacts",
    "## What this case proves",
    "## Update history",
)

#: A backticked token in ``case.md`` is how a path is declared.
_BACKTICKED = re.compile(r"`([^`\n]+)`")


def _declared_in(record: Path) -> set[str]:
    """Relative paths the case record names anywhere in its text."""
    return {
        token.strip().removeprefix("./")
        for token in _BACKTICKED.findall(record.read_text(encoding="utf-8"))
    }


def _fixture_directories() -> list[Path]:
    """One case directory per subject: the direct children of ``fixtures/``."""
    return sorted(path for path in FIXTURES.iterdir() if path.is_dir())


def _fixture_files(case_dir: Path) -> set[str]:
    return {
        path.relative_to(case_dir).as_posix()
        for path in sorted(case_dir.rglob("*"))
        if path.is_file() and path.suffix in DATA_SUFFIXES
    }


def test_every_fixture_directory_has_a_case_record() -> None:
    missing = [
        directory.name
        for directory in _fixture_directories()
        if not (directory / RECORD).is_file()
    ]

    assert not missing, f"fixture directories without case.md: {missing}"


def test_every_fixture_case_record_carries_the_required_headings() -> None:
    """Extension: the headings are mandatory for fixtures, not only for goldens."""
    incomplete: dict[str, list[str]] = {}
    for directory in _fixture_directories():
        record = directory / RECORD
        if not record.is_file():
            continue
        text = record.read_text(encoding="utf-8")
        missing = [heading for heading in REQUIRED_HEADINGS if heading not in text]
        if missing:
            incomplete[directory.name] = missing

    assert not incomplete, (
        "fixture case records missing required headings:\n"
        + "\n".join(f"  {case}: {missing}" for case, missing in incomplete.items())
    )


def test_every_fixture_file_is_listed_in_its_case_record() -> None:
    unlisted: dict[str, list[str]] = {}
    for directory in _fixture_directories():
        declared = _declared_in(directory / RECORD)
        missing = sorted(_fixture_files(directory) - declared)
        if missing:
            unlisted[directory.name] = missing

    assert not unlisted, (
        "fixture files not named in their case.md:\n"
        + "\n".join(f"  {case}: {files}" for case, files in unlisted.items())
    )


def test_test_modules_do_not_embed_large_documents() -> None:
    """A document over the limit is a fixture that was never committed."""
    offenders: list[str] = []
    for path in sorted(TESTS.glob("*.py")):
        if path.name in {"test_fixture_policy.py", "fixture_files.py"}:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        docstrings = _docstring_nodes(tree)
        for node in ast.walk(tree):
            if not isinstance(node, ast.Constant) or not isinstance(node.value, str):
                continue
            if id(node) in docstrings:
                continue
            if node.value.count("\n") < INLINE_NEWLINE_LIMIT:
                continue
            key = f"{path.name}:{node.lineno}"
            if key in INLINE_ALLOWLIST:
                continue
            offenders.append(key)

    assert not offenders, (
        f"inline documents of {INLINE_NEWLINE_LIMIT}+ lines; move them to "
        "tests/fixtures/<subject>/ and load with fixture_text():\n"
        + "\n".join(f"  {key}" for key in offenders)
    )


def _docstring_nodes(tree: ast.AST) -> set[int]:
    """Ids of docstring constants, which are prose, not embedded documents."""
    found: set[int] = set()
    for node in ast.walk(tree):
        body = getattr(node, "body", None)
        if not isinstance(body, list) or not body:
            continue
        first = body[0]
        if (
            isinstance(first, ast.Expr)
            and isinstance(first.value, ast.Constant)
            and isinstance(first.value.value, str)
        ):
            found.add(id(first.value))
    return found


def test_fixture_paths_resolve_from_the_module() -> None:
    """A fixture read through the cwd breaks under a different rootdir."""
    offenders = [
        f"{path.name}:{index}"
        for path in sorted(TESTS.glob("*.py"))
        if path.name not in {"test_fixture_policy.py", "fixture_files.py"}
        for index, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1)
        if 'Path("tests/' in line or "Path('tests/" in line
    ]

    assert not offenders, f"cwd-relative fixture paths: {offenders}"
