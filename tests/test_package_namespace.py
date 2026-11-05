"""Package-first IR: storage keys, resolution, export, and configuration values.

A definition of the primary package keeps its bare storage key; a definition of
any other (included) package is keyed ``Pkg::Name``. ``Definition.name`` stays
bare everywhere, so no package qualifier reaches an artifact surface.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from pycps_sysml2 import load
from pycps_sysml2.metadata import SSP_ROLES
from pycps_sysml2.metadata.roles import is_ssp_model
from pycps_sysml2.model import Architecture, PartDefinition, PartUsage
from pycps_sysml2.parameters import component_definitions, component_refs
from pycps_sysml2.parameters.configuration import derived_selection, qualified_type
from tests.fixture_files import fixture_path


def _primary() -> Path:
    return fixture_path("packages/primary")


def _alpha() -> Path:
    return fixture_path("packages/alpha")


def _beta() -> Path:
    return fixture_path("packages/beta")


def _configuration() -> Path:
    return fixture_path("packages/configuration")


def test_same_name_in_two_packages_coexists() -> None:
    architecture = load(_primary(), _alpha())

    assert set(architecture.part_definitions) == {
        "Same",
        "System",
        "Extra",
        "Alpha::Same",
        "Alpha::SourceChoice",
    }
    assert architecture.part_definitions["Same"].package == "Fixed"
    assert architecture.part_definitions["Alpha::Same"].package == "Alpha"
    assert architecture.included_definitions == {
        "Alpha::Same",
        "Alpha::SourceChoice",
    }


def test_attribution_stays_with_the_declaring_package() -> None:
    architecture = load(_primary(), _alpha())

    assert architecture.part_definitions["Same"].source_file == "model.sysml"
    assert architecture.part_definitions["Alpha::Same"].source_file == (
        "definitions.sysml"
    )


def test_bare_resolution_prefers_the_primary_package() -> None:
    architecture = load(_primary(), _alpha())

    assert architecture.resolve_part("Same") is architecture.part_definitions["Same"]
    assert (
        architecture.resolve_part("Alpha::Same")
        is architecture.part_definitions["Alpha::Same"]
    )
    assert architecture.resolve_part("Beta::Same") is None


def test_ambiguous_bare_name_names_every_candidate() -> None:
    architecture = load(_configuration(), _alpha(), _beta())

    with pytest.raises(ValueError) as excinfo:
        architecture.resolve_part("Same")

    message = str(excinfo.value)
    assert "Ambiguous definition name 'Same'" in message
    assert "Alpha::Same" in message
    assert "Beta::Same" in message


def test_export_emits_the_primary_package_only() -> None:
    architecture = load(_primary(), _alpha())

    files = architecture.export_declared()

    assert set(files) == {"model.sysml", "extra.sysml"}
    assert files["model.sysml"].count("package Fixed {") == 1
    assert files["extra.sysml"].count("package Fixed {") == 1
    assert "package Alpha" not in "".join(files.values())
    assert "part def Same {" in files["model.sysml"]


def test_qualified_configuration_value_resolves_the_type() -> None:
    architecture = load(_configuration(), _alpha())

    selection = derived_selection(
        architecture, architecture.get_part_def("Config"), roles=SSP_ROLES
    )

    assert selection == {"source": "step"}


def test_qualified_value_without_a_resolving_type_names_the_value() -> None:
    architecture = load(_configuration(), _alpha())

    with pytest.raises(ValueError, match="Unknown::Missing::step"):
        qualified_type(
            architecture,
            architecture.part_definitions,
            "Unknown::Missing::step",
        )


def test_single_package_keys_stay_bare() -> None:
    architecture = load(_configuration())

    assert isinstance(architecture, Architecture)
    assert set(architecture.part_definitions) == {
        "SspModel",
        "Step",
        "System",
        "StepSystem",
        "Config",
    }


def test_deep_marker_walk_is_keyed_by_stored_key_not_bare_name() -> None:
    """A same-named definition of another package must not prune the chain.

    ``Fixed`` and ``Alpha`` each define ``Base``; ``System`` reaches the plain
    one first, so a visited set holding bare names would prune ``Alpha::Base``
    and miss the ``SspModel`` marker behind it.
    """
    architecture = Architecture(
        package_name="Fixed",
        imports={"Alpha": None},
        part_definitions={
            "SspModel": PartDefinition(name="SspModel", package="Fixed"),
            "Base": PartDefinition(name="Base", package="Fixed"),
            "Alpha::Base": PartDefinition(
                name="Base", package="Alpha", specializes=("SspModel",)
            ),
            "System": PartDefinition(
                name="System",
                package="Fixed",
                specializes=("Base", "Alpha::Base"),
            ),
        },
    )

    assert is_ssp_model(architecture, architecture.get_part_def("System"))


def test_component_definitions_keeps_same_named_definitions_of_two_packages() -> None:
    """Dedupe is by stored key: ``Same`` and ``Alpha::Same`` both stay."""
    architecture = Architecture(
        package_name="Fixed",
        imports={"Alpha": None},
        part_definitions={
            "Same": PartDefinition(name="Same", package="Fixed"),
            "Alpha::Same": PartDefinition(name="Same", package="Alpha"),
            "System": PartDefinition(
                name="System",
                package="Fixed",
                parts={
                    "primary": PartUsage(name="primary", type_name="Same"),
                    "included": PartUsage(name="included", type_name="Alpha::Same"),
                },
            ),
        },
    )

    definitions = component_definitions(
        architecture, architecture.get_part_def("System")
    )

    assert definitions == [
        architecture.part_definitions["Same"],
        architecture.part_definitions["Alpha::Same"],
    ]
    assert [architecture.stored_key(item) for item in definitions] == [
        "Same",
        "Alpha::Same",
    ]


def test_component_refs_cycle_guard_is_keyed_by_stored_key() -> None:
    """A same-named definition of another package is not a cycle."""
    architecture = Architecture(
        package_name="Fixed",
        imports={"Alpha": None},
        part_definitions={
            "Same": PartDefinition(
                name="Same",
                package="Fixed",
                parts={"other": PartUsage(name="other", type_name="Alpha::Same")},
            ),
            "Alpha::Same": PartDefinition(
                name="Same",
                package="Alpha",
                parts={"leaf": PartUsage(name="leaf", type_name="Leaf")},
            ),
            "Leaf": PartDefinition(name="Leaf", package="Fixed"),
            "System": PartDefinition(
                name="System",
                package="Fixed",
                parts={"root": PartUsage(name="root", type_name="Same")},
            ),
        },
    )

    refs = component_refs(architecture, architecture.get_part_def("System"))

    assert [ref.path for ref in refs] == [
        ("root",),
        ("root", "other"),
        ("root", "other", "leaf"),
    ]
