"""The parameter port contract: direction, marker kind, and declarations.

Only the reader-level half of the originating suite is here. Rules that a
generator enforces (flat FMI variables, flat SSD connectors, refusal to
``connect`` two parameter ports) belong to the generator that owns them.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from pycps_sysml2.model import Architecture, load
from pycps_sysml2.parameters.dialect.declarations import (
    parameter_declarations,
    parameter_interface,
)
from pycps_sysml2.parameters.dialect.markers import validate_marker_definitions
from tests.fixture_files import render_fixture
from tests.testhelpers import COMPOSITION_NAME, write_model


def _model(
    *,
    port: str = "in port parameters : Params;",
    markers: str = (
        "port def ParameterInterface;\n"
        "  attribute def ParameterSet;"
    ),
    interface_decl: str = "port def Params :> ParameterInterface",
    interface_members: str = (
        "attribute gain : Real = 2.0;\n"
        "    attribute count : Integer;\n"
        "    attribute xs : Real[2];"
    ),
) -> str:
    return render_fixture(
        "parameter-ports/template.sysml",
        port=port,
        markers=markers,
        interface_decl=interface_decl,
        interface_members=interface_members,
        COMPOSITION_NAME=COMPOSITION_NAME,
    )


def _load(tmp_path: Path, text: str) -> Architecture:
    architecture_dir = tmp_path / "arch"
    write_model(architecture_dir / "model.sysml", text)
    return load(architecture_dir)


@pytest.mark.parametrize(
    "port",
    ["in port parameters : Params;", "port parameters : Params;"],
)
def test_parameter_interface_is_a_port(tmp_path: Path, port: str) -> None:
    """The parameter port is an input (or undirected) port typed by a marked port def."""
    architecture = _load(tmp_path, _model(port=port))
    part_def = architecture.get_part_def("Comp")

    interface = parameter_interface(architecture, part_def)

    assert interface is not None
    assert interface.specializes == ("ParameterInterface",)
    assert list(interface.attributes) == ["gain", "count", "xs"]
    assert part_def.ports["parameters"].direction in (None, "in")
    assert part_def.attributes == {}
    assert [
        attribute.name
        for attribute in parameter_declarations(architecture, part_def)
    ] == ["gain", "count", "xs"]


def test_out_direction_is_rejected(tmp_path: Path) -> None:
    """A parameter port is not an output signal."""
    architecture = _load(
        tmp_path, _model(port="out port parameters : Params;")
    )

    with pytest.raises(ValueError, match="undirected or 'in'"):
        parameter_interface(architecture, architecture.get_part_def("Comp"))


def test_attribute_bag_is_rejected(tmp_path: Path) -> None:
    """The retired attribute carrier fails with a migration hint."""
    architecture = _load(
        tmp_path, _model(port="attribute parameters : Params;")
    )

    with pytest.raises(ValueError, match="attribute bag"):
        parameter_interface(architecture, architecture.get_part_def("Comp"))


def test_attribute_marker_is_rejected(tmp_path: Path) -> None:
    """ParameterInterface must be a port def, not an attribute def."""
    architecture = _load(
        tmp_path,
        _model(
            markers=(
                "attribute def ParameterInterface;\n"
                "  attribute def ParameterSet;"
            ),
        ),
    )

    with pytest.raises(ValueError, match="defined as an attribute def"):
        validate_marker_definitions(architecture)


def test_flat_connector_marker_is_rejected(tmp_path: Path) -> None:
    """A parameter interface cannot flatten to the port name."""
    architecture = _load(
        tmp_path,
        _model(
            interface_members=(
                "attribute pyssp_flat_connector : Boolean = true;\n"
                "    attribute gain : Real;"
            ),
        ),
    )

    with pytest.raises(ValueError, match="cannot declare"):
        parameter_interface(architecture, architecture.get_part_def("Comp"))


def test_connected_parameter_ports_still_resolve_as_interfaces(
    tmp_path: Path,
) -> None:
    """The reader resolves both sides; refusing the wiring is a writer's rule."""
    architecture = _load(
        tmp_path,
        render_fixture(
            "parameter-ports/connected-ports.sysml",
            COMPOSITION_NAME=COMPOSITION_NAME,
        ),
    )
    system = architecture.get_part_def(COMPOSITION_NAME)

    assert len(system.connections) == 1
    interfaces = [
        parameter_interface(
            architecture, architecture.resolve_part(system.parts[name])
        )
        for name in ("left", "right")
    ]
    assert [interface.name for interface in interfaces if interface] == [
        "Params",
        "Params",
    ]
