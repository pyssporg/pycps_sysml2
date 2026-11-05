"""The shared core definitions: package data and multi-root loading.

An included root is opt-in, so a fixture that declares its own markers keeps
loading unchanged, and a fixture that omits them can merge the packaged core
definitions instead of redeclaring them.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from pycps_sysml2 import core_definitions, load
from pycps_sysml2.definitions import CORE_FILE
from pycps_sysml2.metadata import fmu_metadata, validate_role_markers
from pycps_sysml2.parameters import validate_marker_definitions
from tests.fixture_files import fixture_text
from tests.testhelpers import write_model

CORE_NAMES = {
    "SspModel",
    "Analysis",
    "ParameterInterface",
    "ParameterSet",
    "FmuMetadata",
    "SspMetadata",
    "Experiment",
}

COMMON_DEFINITIONS = """
package CommonVocab {
  part def SspModel;
  port def ParameterInterface;

  attribute def FmuMetadata {
    attribute source : String;
    attribute implementation : String;
  }
}
"""


def _marker_user(tmp_path: Path) -> Path:
    """A model that uses the core markers without declaring them."""
    model_file = tmp_path / "model.sysml"
    write_model(
        model_file,
        fixture_text("core-definitions/marker-user.sysml"),
    )
    return model_file


def _model_dir(tmp_path: Path) -> Path:
    """The marker user as a directory root, for the two-argument-form test."""
    model_dir = tmp_path / "model"
    write_model(
        model_dir / "model.sysml",
        fixture_text("core-definitions/marker-user.sysml"),
    )
    return model_dir


def _common_dir(tmp_path: Path) -> Path:
    """An included root whose package name differs from the model's."""
    common_dir = tmp_path / "common"
    write_model(common_dir / "common.sysml", COMMON_DEFINITIONS)
    return common_dir


def test_core_definitions_is_an_existing_real_file() -> None:
    path = core_definitions()

    assert isinstance(path, Path)
    assert path.is_file()
    assert path.name == CORE_FILE.rsplit("/", 1)[-1] == "core.sysml"
    assert path.parent.name == "definitions"


def test_core_definitions_parses_as_the_core_package() -> None:
    architecture = load(core_definitions())

    assert architecture.package_name == "PysspCore"
    assert list(architecture.part_definitions) == ["SspModel", "Analysis"]
    assert list(architecture.port_definitions) == ["ParameterInterface"]
    assert list(architecture.attribute_definitions) == [
        "ParameterSet",
        "FmuMetadata",
        "SspMetadata",
        "Experiment",
    ]
    assert architecture.included_definitions == set()


def test_load_without_includes_leaves_markers_unresolved(tmp_path) -> None:
    architecture = load(_marker_user(tmp_path))

    system = architecture.get_part_def("System")
    assert system.specializes == ("SspModel",)
    assert "SspModel" not in architecture.part_definitions
    assert architecture.resolve_attribute_def("FmuMetadata") is None
    assert architecture.included_definitions == set()

    with pytest.raises(ValueError, match="Role marker 'SspModel'"):
        validate_role_markers(architecture)
    with pytest.raises(ValueError, match="missing marker definition"):
        validate_marker_definitions(architecture)


def test_load_with_include_resolves_core_markers(tmp_path) -> None:
    architecture = load(_marker_user(tmp_path), core_definitions())

    validate_role_markers(architecture)
    validate_marker_definitions(architecture)

    metadata = fmu_metadata(architecture, architecture.get_part_def("System"))
    assert metadata is not None
    assert metadata.source == "models/fmu/Ball/fmu"
    assert metadata.implementation == "CoSimulation"
    assert architecture.included_definitions == CORE_NAMES


def test_load_with_include_accepts_a_directory(tmp_path) -> None:
    architecture = load(_marker_user(tmp_path), core_definitions().parent)

    assert "SspModel" in architecture.part_definitions
    assert architecture.included_definitions == CORE_NAMES


def test_load_accepts_a_sequence_or_star_includes(tmp_path) -> None:
    model_dir = _model_dir(tmp_path)
    common_dir = _common_dir(tmp_path)

    from_sequence = load([model_dir, common_dir])
    from_includes = load(model_dir, common_dir)

    assert from_sequence.package_name == from_includes.package_name == "MarkerUser"
    assert from_sequence.part_definitions.keys() == from_includes.part_definitions.keys()
    assert from_sequence.port_definitions.keys() == from_includes.port_definitions.keys()
    assert (
        from_sequence.attribute_definitions.keys()
        == from_includes.attribute_definitions.keys()
    )
    assert from_sequence.included_definitions == from_includes.included_definitions


def test_included_root_package_name_need_not_match(tmp_path) -> None:
    model_dir = _model_dir(tmp_path)
    common_dir = _common_dir(tmp_path)

    architecture = load(model_dir, common_dir)

    assert architecture.package_name == "MarkerUser"
    assert architecture.included_definitions == {
        "SspModel",
        "ParameterInterface",
        "FmuMetadata",
    }
    validate_role_markers(architecture)
    assert architecture.get_part_def("System").specializes == ("SspModel",)


def test_locally_declared_marker_is_a_duplicate_error(tmp_path) -> None:
    model_file = tmp_path / "model.sysml"
    write_model(
        model_file,
        """
        package LocalMarkers {
          part def SspModel;

          part def System :> SspModel;
        }
        """,
    )

    with pytest.raises(ValueError) as excinfo:
        load(model_file, core_definitions())

    message = str(excinfo.value)
    assert "'SspModel'" in message
    assert "part def" in message
    assert str(model_file) in message
    assert str(core_definitions()) in message
    assert "remove the local declaration" in message


def test_duplicate_between_included_roots_names_both(tmp_path) -> None:
    model_dir = _model_dir(tmp_path)
    first = tmp_path / "first"
    second = tmp_path / "second"
    write_model(first / "one.sysml", "package First { part def SspModel; }")
    write_model(second / "two.sysml", "package Second { part def SspModel; }")

    with pytest.raises(ValueError) as excinfo:
        load(model_dir, first, second)

    message = str(excinfo.value)
    assert "'SspModel'" in message
    assert str(first) in message
    assert str(second) in message
    assert "only one included root" in message


def test_export_declared_omits_included_definitions(tmp_path) -> None:
    model_file = _marker_user(tmp_path)
    architecture = load(model_file, core_definitions())

    text = architecture.export_declared()["model.sysml"]

    assert "part def SspModel;" not in text
    assert "part def Analysis;" not in text
    assert "port def ParameterInterface;" not in text
    assert "attribute def ParameterSet;" not in text
    assert "attribute def FmuMetadata {" not in text
    assert "attribute def SspMetadata {" not in text
    assert "part def System :> SspModel" in text
    assert text == load(model_file).export_declared()["model.sysml"]
