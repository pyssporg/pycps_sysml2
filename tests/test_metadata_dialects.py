"""The typed-metadata accessors: FMU metadata and SSP metadata.

Both dialects are read the same way — by the *type* of a part attribute, never
by the usage name — so both get the same class of assertion here. Only
loader-level cases are ported; emitting an artifact is a different layer's test.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from pycps_sysml2.metadata.fmu_metadata import (
    FmuMetadata,
    component_implementation,
    component_source,
    fmu_metadata,
    is_fmu_metadata_definition,
)
from pycps_sysml2.metadata.ssp_metadata import (
    SSP_METADATA_MARKER,
    is_ssp_metadata_definition,
    ssp_metadata,
)
from pycps_sysml2.metadata.roles import is_ssp_model
from pycps_sysml2.model import Architecture, AttributeDefinition, PartDefinition, load
from pycps_sysml2.parameters.dialect.markers import is_parameter_set
from tests.fixture_files import render_fixture
from tests.testhelpers import COMPOSITION_NAME, write_model


def _metadata_model(
    *,
    marker: str = """
      attribute def FmuMetadata {
        attribute source : String;
        attribute implementation : String;
      }
    """,
    concrete: str = """
      attribute def CompFmu :> FmuMetadata {
        attribute source = "build/fmus/Comp.fmu";
        attribute implementation = "CoSimulation";
      }
    """,
    part_body: str = "attribute fmu_meta : CompFmu;",
) -> str:
    return render_fixture(
        "fmu-metadata/template.sysml",
        marker=marker,
        concrete=concrete,
        part_body=part_body,
        COMPOSITION_NAME=COMPOSITION_NAME,
    )


def _load(tmp_path: Path, text: str) -> Architecture:
    architecture_dir = tmp_path / "arch"
    write_model(architecture_dir / "model.sysml", text)
    return load(architecture_dir)


SSP_MODEL = """package Ssp {
  attribute def SspMetadata { attribute source : String; }
  attribute def LegacySsp :> SspMetadata {
    attribute source = "models/ssp/example";
  }
  part def SspModel;
  part def LegacyBody :> SspModel {
    attribute ssp_meta : LegacySsp;
  }
  part def PlainPart {
    attribute ssp_meta : LegacySsp;
  }
}"""


def test_fmu_metadata_resolves_concrete_and_base_values(tmp_path: Path) -> None:
    """Concrete values override the schema; unset fields fall back to it."""
    architecture = _load(
        tmp_path,
        _metadata_model(
            marker="""
            attribute def FmuMetadata {
              attribute source : String;
              attribute implementation : String = "CoSimulation";
            }
            """,
            concrete="""
            attribute def CompFmu :> FmuMetadata {
              attribute source = "build/fmus/Comp.fmu";
            }
            """,
        ),
    )

    metadata = fmu_metadata(architecture, architecture.get_part_def("Comp"))

    assert metadata is not None
    assert metadata.source == "build/fmus/Comp.fmu"
    assert metadata.implementation == "CoSimulation"


def test_value_less_redeclaration_inherits_the_base_value(tmp_path: Path) -> None:
    architecture = _load(
        tmp_path,
        _metadata_model(
            marker="""
            attribute def FmuMetadata {
              attribute implementation : String = "CoSimulation";
            }
            """,
            concrete="""
            attribute def CompFmu :> FmuMetadata {
              attribute implementation : String;
            }
            """,
        ),
    )

    metadata = fmu_metadata(architecture, architecture.get_part_def("Comp"))

    assert metadata is not None
    assert metadata.implementation == "CoSimulation"


def test_component_source_is_empty_without_a_source(tmp_path: Path) -> None:
    """A part with no authored FMU has no component source, whatever the metadata."""
    architecture = _load(
        tmp_path,
        _metadata_model(concrete="attribute def CompFmu :> FmuMetadata {}"),
    )
    part_def = architecture.get_part_def("Comp")

    metadata = FmuMetadata(implementation="CoSimulation")
    assert component_source(part_def, None) == ""
    assert component_source(part_def, metadata) == ""
    assert component_source(part_def, fmu_metadata(architecture, part_def)) == ""


def test_component_source_is_the_part_name_under_resources(tmp_path: Path) -> None:
    """Verbatim naming rule: the FMU resource is named after the part def."""
    architecture = _load(tmp_path, _metadata_model())
    part_def = architecture.get_part_def("Comp")

    assert component_source(part_def, fmu_metadata(architecture, part_def)) == (
        "resources/Comp.fmu"
    )
    assert component_implementation(
        fmu_metadata(architecture, part_def)
    ) == "CoSimulation"


def test_non_string_metadata_value_is_rejected(tmp_path: Path) -> None:
    architecture = _load(
        tmp_path,
        _metadata_model(
            concrete="""
            attribute def CompFmu :> FmuMetadata {
              attribute implementation = 1;
            }
            """,
        ),
    )

    with pytest.raises(ValueError, match="must be a String"):
        fmu_metadata(architecture, architecture.get_part_def("Comp"))


def test_duplicate_metadata_attributes_are_rejected(tmp_path: Path) -> None:
    architecture = _load(
        tmp_path,
        _metadata_model(
            concrete="""
            attribute def CompFmu :> FmuMetadata {
              attribute implementation = "CoSimulation";
            }
            attribute def OtherFmu :> FmuMetadata {
              attribute implementation = "ModelExchange";
            }
            """,
            part_body="""attribute fmu_meta : CompFmu;
            attribute other : OtherFmu;""",
        ),
    )

    with pytest.raises(ValueError, match="multiple FMU metadata"):
        fmu_metadata(architecture, architecture.get_part_def("Comp"))


def test_metadata_marker_cannot_be_used_directly(tmp_path: Path) -> None:
    architecture = _load(
        tmp_path,
        _metadata_model(part_body="attribute fmu_meta : FmuMetadata;"),
    )

    with pytest.raises(ValueError, match="schema directly"):
        fmu_metadata(architecture, architecture.get_part_def("Comp"))


def test_missing_metadata_marker_is_rejected(tmp_path: Path) -> None:
    architecture = _load(tmp_path, _metadata_model(marker=""))

    with pytest.raises(ValueError, match="missing marker definition"):
        fmu_metadata(architecture, architecture.get_part_def("Comp"))


def test_fmu_metadata_is_recognised_by_type_not_usage_name(tmp_path: Path) -> None:
    architecture = _load(
        tmp_path,
        _metadata_model(
            concrete="attribute def CompFmu :> FmuMetadata {}",
            part_body="attribute anything : CompFmu;",
        ),
    )

    definition = architecture.attribute_definitions["CompFmu"]
    assert is_fmu_metadata_definition(architecture, definition)
    assert is_fmu_metadata_definition(
        architecture, architecture.attribute_definitions["FmuMetadata"]
    )
    assert not is_fmu_metadata_definition(
        architecture, architecture.attribute_definitions.get("Missing")
    )


def test_ssp_metadata_resolves_its_source(tmp_path: Path) -> None:
    architecture = _load(tmp_path, SSP_MODEL)
    model = architecture.get_part_def("LegacyBody")

    metadata = ssp_metadata(architecture, model)

    assert metadata is not None
    assert metadata.source == "models/ssp/example"
    assert is_ssp_metadata_definition(
        architecture, architecture.attribute_definitions["LegacySsp"]
    )
    assert is_ssp_metadata_definition(
        architecture, architecture.attribute_definitions[SSP_METADATA_MARKER]
    )


def test_ssp_metadata_requires_an_ssp_model(tmp_path: Path) -> None:
    architecture = _load(tmp_path, SSP_MODEL)

    assert ssp_metadata(architecture, architecture.get_part_def("LegacyBody"))
    with pytest.raises(ValueError, match="not marked ':> SspModel'"):
        ssp_metadata(architecture, architecture.get_part_def("PlainPart"))


def test_a_marker_definition_is_not_its_own_instance() -> None:
    """The two marker predicates answer different questions on purpose."""
    architecture = Architecture(
        package_name="Markers",
        part_definitions={"SspModel": PartDefinition(name="SspModel")},
        attribute_definitions={
            "ParameterSet": AttributeDefinition(name="ParameterSet"),
            "Nominal": AttributeDefinition(
                name="Nominal", specializes=("ParameterSet",)
            ),
        },
    )

    assert is_ssp_model(architecture, architecture.part_definitions["SspModel"])
    assert not is_parameter_set(architecture.attribute_definitions["ParameterSet"])
    assert is_parameter_set(architecture.attribute_definitions["Nominal"])
