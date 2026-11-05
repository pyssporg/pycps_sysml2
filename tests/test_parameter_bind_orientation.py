"""A parameter bind is resolved by role: the port is left, the set is right.

The originating suite also scanned the repository's shipped examples for the
canonical orientation. Those example trees do not exist in this library, so that
half is not ported; the resolver assertions are.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from pycps_sysml2.model import Architecture, load
from pycps_sysml2.parameters.dialect.composition import parameter_bind
from tests.fixture_files import render_fixture
from tests.testhelpers import COMPOSITION_NAME, write_model


def _model(bind_line: str, *, parts: str = "part comp : Comp;") -> str:
    return render_fixture(
        "parameter-bind-orientation/template.sysml",
        parts=parts,
        bind_line=bind_line,
        COMPOSITION_NAME=COMPOSITION_NAME,
    )


def _load(
    tmp_path: Path, bind_line: str, *, parts: str = "part comp : Comp;"
) -> tuple[Architecture, object]:
    path = tmp_path / "model.sysml"
    write_model(path, _model(bind_line, parts=parts))
    architecture = load(path)
    return architecture, architecture.get_part_def(COMPOSITION_NAME)


def test_canonical_member_bind_resolves_by_role(tmp_path: Path) -> None:
    """The port is on the left; the set usage is on the right."""
    _, system = _load(tmp_path, "bind comp.parameters.count = nominal.n;")

    bind = parameter_bind(system.bindings[0])

    assert bind is not None
    assert bind.port_path == ("comp",)
    assert bind.port_member == "count"
    assert bind.set_usage == "nominal"
    assert bind.set_member == "n"


def test_canonical_identity_bind_resolves_by_role(tmp_path: Path) -> None:
    """A whole-object bind is still port-first."""
    _, system = _load(tmp_path, "bind comp.parameters = nominal;")

    bind = parameter_bind(system.bindings[0])

    assert bind is not None
    assert bind.identity
    assert bind.port_reference() == "comp.parameters"
    assert bind.set_path == ("nominal",)


def test_reversed_bind_is_rejected_with_rewrite(tmp_path: Path) -> None:
    """Only the canonical orientation is accepted."""
    _, system = _load(tmp_path, "bind nominal.n = comp.parameters.count;")

    with pytest.raises(ValueError, match="parameter port on the left") as error:
        parameter_bind(system.bindings[0])

    assert "bind comp.parameters.count = nominal.n;" in str(error.value)


def test_port_to_port_bind_is_rejected(tmp_path: Path) -> None:
    """Two parameter ports are a connection, not a parameter application."""
    _, system = _load(
        tmp_path,
        "bind left.parameters = right.parameters;",
        parts="part left : Comp;\n        part right : Comp;",
    )

    with pytest.raises(ValueError, match="connects two parameter ports"):
        parameter_bind(system.bindings[0])


def test_non_parameter_bind_is_ignored(tmp_path: Path) -> None:
    """Binds without a parameter port are ordinary SysML bindings."""
    _, system = _load(tmp_path, "bind comp.count = nominal.n;")

    assert parameter_bind(system.bindings[0]) is None
