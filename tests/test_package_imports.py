"""Import-gated visibility: a qualified definition needs its package imported.

A definition of an included package is invisible by bare name until the model
imports that package. A wildcard exposes every member, a member import exposes
one, and an explicit reference to a non-imported package raises with the
``private import`` hint. Own-package definitions never need an import.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from pycps_sysml2 import load
from tests.testhelpers import write_model


def _included(tmp_path: Path) -> Path:
    included = tmp_path / "included"
    write_model(
        included / "definitions.sysml",
        """
        package Alpha {
          part def Thing;
          part def Other;
        }
        """,
    )
    return included


def _beta(tmp_path: Path) -> Path:
    included = tmp_path / "beta"
    write_model(included / "definitions.sysml", "package Beta { part def Thing; }")
    return included


def _model(tmp_path: Path, *imports: str) -> Path:
    model = tmp_path / "model"
    lines = "".join(f"  private import {declaration};\n" for declaration in imports)
    write_model(
        model / "model.sysml",
        f"""
        package Main {{
        {lines}  part def Local;
        }}
        """,
    )
    return model


def test_included_definition_is_invisible_without_an_import(tmp_path) -> None:
    architecture = load(_model(tmp_path), _included(tmp_path))

    assert architecture.imports == {}
    assert architecture.resolve_part("Thing") is None
    assert architecture.resolve_part("Other") is None


def test_wildcard_import_makes_every_member_visible(tmp_path) -> None:
    architecture = load(_model(tmp_path, "Alpha::*"), _included(tmp_path))

    assert architecture.imports == {"Alpha": None}
    assert architecture.resolve_part("Thing") is architecture.get_part_def(
        "Alpha::Thing"
    )
    assert architecture.resolve_part("Other") is architecture.get_part_def(
        "Alpha::Other"
    )


def test_member_import_exposes_only_that_member(tmp_path) -> None:
    architecture = load(_model(tmp_path, "Alpha::Thing"), _included(tmp_path))

    assert architecture.imports == {"Alpha": frozenset({"Thing"})}
    assert architecture.resolve_part("Thing") is architecture.get_part_def(
        "Alpha::Thing"
    )
    assert architecture.resolve_part("Other") is None


def test_own_package_names_need_no_import(tmp_path) -> None:
    architecture = load(_model(tmp_path), _included(tmp_path))

    assert architecture.resolve_part("Local") is architecture.get_part_def("Local")


def test_qualified_reference_to_a_non_imported_package_raises(tmp_path) -> None:
    architecture = load(_model(tmp_path), _included(tmp_path))

    with pytest.raises(ValueError, match=r"private import Alpha::\*;"):
        architecture.resolve_part("Alpha::Thing")


def test_wildcard_and_member_imports_coexist(tmp_path) -> None:
    model = _model(tmp_path, "Alpha::*", "Beta::Thing")
    architecture = load(model, _included(tmp_path), _beta(tmp_path))

    assert architecture.imports == {
        "Alpha": None,
        "Beta": frozenset({"Thing"}),
    }
    assert architecture.resolve_part("Other") is architecture.get_part_def(
        "Alpha::Other"
    )
    assert architecture.resolve_part("Beta::Thing") is not None


def test_duplicate_imports_across_files_do_not_raise(tmp_path) -> None:
    model = _model(tmp_path, "Alpha::*", "Alpha::Thing")
    write_model(
        model / "extra.sysml",
        "package Main {\n  private import Alpha::Other;\n}",
    )

    architecture = load(model, _included(tmp_path))

    assert architecture.imports == {"Alpha": None}
