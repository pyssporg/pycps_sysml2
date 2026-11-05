"""Role markers: what a definition is for, read from its specializations.

Every assertion here reads the loaded model or the role accessors. Artifact
output belongs to the layer that writes it, not to this file.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from pycps_sysml2.metadata.roles import (
    ANALYSIS_MARKER,
    SSP_MODEL_MARKER,
    Experiment,
    analysis_part_definitions,
    experiment_attribute,
    exportable_part_definitions,
    is_analysis,
    is_experiment_definition,
    is_ssp_model,
    model_usage,
    read_experiment,
    require_resolved_variation,
    validate_role_markers,
)
from pycps_sysml2.model import Architecture, load, PartDefinition
from tests.testhelpers import write_model


ROLES = """package Roles {
  part def SspModel;
  part def Analysis;
  part def System :> SspModel;
  part def baseline :> Analysis {
    part sut : System;
  }
}"""

EXPERIMENT = """package Exp {
  attribute def Experiment {
    attribute startTime : Real = 0.0;
    attribute stopTime : Real = 1.0;
    attribute stepSize : Real = 0.001;
  }
  attribute def Baseline :> Experiment;
  part def Analysis;
  part def baseline :> Analysis {
    attribute experiment_baseline : Baseline;
  }
}"""

VARIATION = """package V {
  part def SspModel;
  part def S;
  part def System :> SspModel {
    variation part source : S;
  }
}"""


def _load(tmp_path: Path, text: str) -> Architecture:
    write_model(tmp_path / "model.sysml", text)
    return load(tmp_path)


def test_role_predicates_read_specialization_and_the_marker_itself(
    tmp_path: Path,
) -> None:
    architecture = _load(tmp_path, ROLES)

    assert is_ssp_model(architecture, architecture.get_part_def("System"))
    assert is_analysis(architecture, architecture.get_part_def("baseline"))
    assert is_ssp_model(
        architecture, architecture.get_part_def(SSP_MODEL_MARKER)
    )
    assert not is_analysis(architecture, architecture.get_part_def(SSP_MODEL_MARKER))


def test_role_definitions_are_listed_and_the_marker_is_not_an_analysis(
    tmp_path: Path,
) -> None:
    architecture = _load(tmp_path, ROLES)

    assert {
        definition.name
        for definition in exportable_part_definitions(architecture)
    } == {"SspModel", "System"}
    assert [
        definition.name for definition in analysis_part_definitions(architecture)
    ] == ["baseline"]


def test_validate_role_markers_requires_the_marker_definitions(
    tmp_path: Path,
) -> None:
    architecture = _load(tmp_path, ROLES)
    validate_role_markers(architecture)

    undeclared = _load(
        tmp_path / "undeclared",
        "package P {\n  part def System :> SspModel;\n}",
    )
    with pytest.raises(ValueError, match=f"Role marker '{SSP_MODEL_MARKER}'"):
        validate_role_markers(undeclared)


def test_model_usage_is_the_single_model_part_composed_by_an_analysis(
    tmp_path: Path,
) -> None:
    architecture = _load(tmp_path, ROLES)

    usage, definition = model_usage(
        architecture, architecture.get_part_def("baseline")
    )

    assert usage.name == "sut"
    assert definition.name == "System"


def test_an_analysis_without_exactly_one_model_part_is_rejected(
    tmp_path: Path,
) -> None:
    architecture = _load(
        tmp_path,
        """package P {
  part def SspModel;
  part def Analysis;
  part def Empty :> Analysis;
}""",
    )

    with pytest.raises(ValueError, match="exactly one SspModel part"):
        model_usage(architecture, architecture.get_part_def("Empty"))


def test_experiment_is_read_from_the_effective_members(tmp_path: Path) -> None:
    architecture = _load(tmp_path, EXPERIMENT)
    analysis = architecture.get_part_def("baseline")

    assert is_experiment_definition(
        architecture, architecture.attribute_definitions["Baseline"]
    )
    name, _attribute, definition = experiment_attribute(architecture, analysis)
    assert name == "experiment_baseline"
    assert definition.name == "Baseline"

    experiment = read_experiment(architecture, analysis)
    assert experiment == Experiment(
        name="experiment_baseline",
        start_time=0.0,
        stop_time=1.0,
        step_size=0.001,
    )


def test_an_analysis_must_declare_exactly_one_experiment_attribute(
    tmp_path: Path,
) -> None:
    architecture = _load(
        tmp_path,
        """package P {
  part def Analysis;
  part def baseline :> Analysis;
}""",
    )

    with pytest.raises(ValueError, match="exactly one Experiment"):
        experiment_attribute(architecture, architecture.get_part_def("baseline"))


def test_a_variation_point_blocks_generation_until_it_is_selected(
    tmp_path: Path,
) -> None:
    architecture = _load(tmp_path, VARIATION)

    with pytest.raises(ValueError, match="Variation point 'source'"):
        require_resolved_variation(
            architecture, architecture.get_part_def("System")
        )


def test_a_model_without_a_role_policy_is_still_a_part_definition() -> None:
    """The marker constants are the SSP vocabulary, not a required attribute."""
    architecture = Architecture(
        package_name="P",
        part_definitions={"Plain": PartDefinition(name="Plain")},
    )

    assert SSP_MODEL_MARKER == "SspModel"
    assert ANALYSIS_MARKER == "Analysis"
    assert not is_ssp_model(architecture, architecture.get_part_def("Plain"))
