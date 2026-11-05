"""Applied parameter sets and the specs derived from them, without artifacts.

Only the dialect half of the originating suite is ported: the declarations a
typed parameter port exposes, the identity mapping of a whole-object bind, and
the detection used by a generator before it emits anything.
"""

from __future__ import annotations

from pathlib import Path

from pycps_sysml2.model import Architecture, load
from pycps_sysml2.parameters.dialect.composition import has_parameter_dialect
from pycps_sysml2.parameters.dialect.declarations import (
    parameter_declarations,
    parameter_interface,
)
from pycps_sysml2.parameters.dialect.mapping import mapping_specs
from pycps_sysml2.parameters.policy import SSP_POLICY
from tests.fixture_files import render_fixture
from tests.testhelpers import COMPOSITION_NAME, write_model


def _model(
    *,
    interface_marker: str = ":> ParameterInterface",
    interface_members: str = (
        "attribute waypointCount : Integer;\n"
        "    attribute waypointX_km : Real[3];"
    ),
    sets: str = "",
    composition: str = "",
) -> str:
    if not sets:
        sets = """
        attribute def NominalSet :> ParameterSet {
          attribute n_waypoints = 10;
          attribute waypoints_x_km = (0.0, 10.0, 20.0);
        }
        """
    if not composition:
        composition = """
        attribute nominal : NominalSet;
        bind autopilot.parameters.waypointCount = nominal.n_waypoints;
        bind autopilot.parameters.waypointX_km = nominal.waypoints_x_km;
        """
    return render_fixture(
        "parameter-sets/template.sysml",
        interface_marker=interface_marker,
        interface_members=interface_members,
        sets=sets,
        composition=composition,
        COMPOSITION_NAME=COMPOSITION_NAME,
    )


def _load(tmp_path: Path, text: str) -> Architecture:
    architecture_dir = tmp_path / "arch"
    write_model(architecture_dir / "model.sysml", text)
    return load(architecture_dir)


def test_parameter_interface_members_are_declarations(tmp_path: Path) -> None:
    """A typed parameter port exposes the interface members as declarations."""
    architecture = _load(tmp_path, _model())
    system = architecture.get_part_def(COMPOSITION_NAME)
    part_def = architecture.resolve_part(system.parts["autopilot"])

    assert part_def is not None
    interface = parameter_interface(architecture, part_def)
    assert interface is not None
    assert interface.name == "AutopilotParameters"
    assert [
        attribute.name
        for attribute in parameter_declarations(architecture, part_def)
    ] == ["waypointCount", "waypointX_km"]


def test_has_parameter_dialect_sees_an_applied_set(tmp_path: Path) -> None:
    architecture = _load(tmp_path, _model())
    system = architecture.get_part_def(COMPOSITION_NAME)

    assert has_parameter_dialect(architecture, system, policy=SSP_POLICY)


def test_whole_object_bind_is_identity(tmp_path: Path) -> None:
    """A whole-object bind uses matching names and maps member for member."""
    model = _model(
        sets="""
        attribute def NominalSet :> ParameterSet {
          attribute waypointCount = 10;
          attribute waypointX_km = (0.0, 10.0, 20.0);
        }
        """,
        composition="""
        attribute nominal : NominalSet;
        bind autopilot.parameters = nominal;
        """,
    )
    architecture = _load(tmp_path, model)
    system = architecture.get_part_def(COMPOSITION_NAME)

    specs = mapping_specs(architecture, system, policy=SSP_POLICY)

    assert len(specs) == 1
    assert specs[0].identity is True
    assert specs[0].entries == (
        ("waypointCount", "autopilot.waypointCount"),
        ("waypointX_km[0]", "autopilot.waypointX_km[0]"),
        ("waypointX_km[1]", "autopilot.waypointX_km[1]"),
        ("waypointX_km[2]", "autopilot.waypointX_km[2]"),
    )
