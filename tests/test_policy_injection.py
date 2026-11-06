"""The dialect policy is the only place domain vocabulary is allowed.

Each test injects a policy that differs from :data:`SSP_POLICY` in exactly one
dimension and shows the behaviour change at a public entry point. The last test
is a source gate: the parameter package must not reach for the role vocabulary
on its own.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from pycps_sysml2.core.control import ControlAttributes
from pycps_sysml2.metadata.roles import RolePolicy
from pycps_sysml2.model import Architecture, load
from pycps_sysml2.parameters.dialect.composition import (
    applied_sets,
    validate_parameter_dialect,
)
from pycps_sysml2.parameters.policy import SSP_POLICY, DialectPolicy
from tests.fixture_files import fixture_text
from tests.testhelpers import write_model


PROJECT = Path(__file__).resolve().parents[1]
SRC = PROJECT / "src" / "pycps_sysml2"
PARAMETERS = SRC / "parameters"

CONTROL_MODEL = """package Controls {
  part def Comp {
    attribute acme_default_start_time = 0.0;
  }
  part def System {
    part comp : Comp;
  }
}"""

NESTED_BIND_MODEL = """package Binds {
  port def ParameterInterface;
  attribute def ParameterSet;
  port def Params :> ParameterInterface { attribute k : Real; }
  attribute def Nom :> ParameterSet { attribute n = 1.0; }
  part def Leaf {
    in port parameters : Params;
    attribute nominal : Nom;
    bind parameters.k = nominal.n;
  }
  part def System {
    part leaf : Leaf;
  }
}"""

ANALYSIS_MODEL = """package An {
  attribute def SspMetadata { attribute source : String; }
  attribute def LegacySsp :> SspMetadata { attribute source = "legacy"; }
  part def Analysis;
  part def SspModel;
  part def Plain :> SspModel {
    attribute ssp_meta : LegacySsp;
  }
  part def NotAnAnalysis {
    attribute ssp_meta : LegacySsp;
    part sut : Plain;
  }
}"""

LEGACY_MODEL = """package Legacy {
  part def Comp {
    attribute pyssp_implementation = "CoSimulation";
    attribute gain = 2.0;
  }
  part def System {
    part comp : Comp;
  }
}"""

FMU_COMPONENT_MODEL = fixture_text("fmu-model/component.sysml")


def _load(tmp_path: Path, text: str) -> Architecture:
    write_model(tmp_path / "model.sysml", text)
    return load(tmp_path)


def _stub_analysis(_architecture: Architecture, _definition) -> bool:
    return True


def test_a_custom_control_prefix_is_honoured_end_to_end(tmp_path: Path) -> None:
    """``acme_*`` attributes are control metadata only under an acme policy."""
    architecture = _load(tmp_path, CONTROL_MODEL)
    system = architecture.get_part_def("System")

    with pytest.raises(ValueError, match="flat parameter attribute"):
        validate_parameter_dialect(architecture, system, policy=SSP_POLICY)

    acme = ControlAttributes(prefix="acme_")
    validate_parameter_dialect(
        architecture, system, policy=DialectPolicy(control=acme)
    )


def test_a_custom_role_policy_changes_which_nested_bindings_are_rejected(
    tmp_path: Path,
) -> None:
    """A model-owned part may carry its own binds; the role decides which part."""
    architecture = _load(tmp_path, NESTED_BIND_MODEL)
    system = architecture.get_part_def("System")

    with pytest.raises(ValueError, match="nested part definition"):
        applied_sets(architecture, system, policy=SSP_POLICY)

    def is_model(_architecture: Architecture, definition) -> bool:
        return definition is not None and definition.name == "Leaf"

    roles = RolePolicy(model_marker=None, is_model=is_model)
    assert applied_sets(
        architecture, system, policy=DialectPolicy(roles=roles)
    ) == []


def test_a_custom_role_policy_changes_the_analysis_metadata_rule(
    tmp_path: Path,
) -> None:
    """SSP metadata on an analysis is rejected; the predicate says what an analysis is."""
    architecture = _load(tmp_path, ANALYSIS_MODEL)
    system = architecture.get_part_def("NotAnAnalysis")

    validate_parameter_dialect(architecture, system, policy=SSP_POLICY)

    roles = RolePolicy(model_marker=None, is_analysis=_stub_analysis)
    with pytest.raises(ValueError, match="SSP metadata"):
        validate_parameter_dialect(
            architecture, system, policy=DialectPolicy(roles=roles)
        )


def test_the_migration_flags_let_an_older_architecture_through(
    tmp_path: Path,
) -> None:
    architecture = _load(tmp_path, LEGACY_MODEL)
    system = architecture.get_part_def("System")

    with pytest.raises(ValueError, match="no longer supported"):
        validate_parameter_dialect(architecture, system, policy=SSP_POLICY)

    permissive = DialectPolicy(
        reject_retired_attributes=False, reject_flat_connectors=False
    )
    validate_parameter_dialect(architecture, system, policy=permissive)


def test_fmu_metadata_is_accepted_only_on_an_fmu_model_composition(
    tmp_path: Path,
) -> None:
    """The marker makes the composition the export unit; subparts still reject."""
    architecture = _load(tmp_path, FMU_COMPONENT_MODEL)

    validate_parameter_dialect(
        architecture, architecture.get_part_def("Comp"), policy=SSP_POLICY
    )

    with pytest.raises(ValueError, match="not an FMU component"):
        validate_parameter_dialect(
            architecture, architecture.get_part_def("Unmarked"), policy=SSP_POLICY
        )

    with pytest.raises(ValueError, match="subparts"):
        validate_parameter_dialect(
            architecture, architecture.get_part_def("Nested"), policy=SSP_POLICY
        )


def _imported_names(tree: ast.AST) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                names.add(node.module)
            names.update(alias.name for alias in node.names)
    return names


def _called_names(tree: ast.AST) -> set[str]:
    """Bare-name calls only: ``policy.roles.is_model(...)`` is the allowed form."""
    return {
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }


def test_the_parameter_package_does_not_reach_for_role_vocabulary() -> None:
    """Only ``policy.py`` may bind the role markers; everything else injects it."""
    role_markers = {
        "SSP_MODEL_MARKER",
        "ANALYSIS_MARKER",
        "FMU_MODEL_MARKER",
        "EXPERIMENT_MARKER",
    }
    role_calls = {"is_ssp_model", "is_analysis", "is_fmu_model"}
    offenders: list[str] = []

    for path in sorted(PARAMETERS.rglob("*.py")):
        if path.name == "policy.py":
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        imported = _imported_names(tree)
        for name in sorted(imported & (role_markers | {"pycps_sysml2.metadata.roles"})):
            offenders.append(f"{path.relative_to(PROJECT)} imports {name}")
        for name in sorted(_called_names(tree) & role_calls):
            offenders.append(f"{path.relative_to(PROJECT)} calls {name}")

    assert not offenders, "role vocabulary leaked into parameters/:\n" + "\n".join(
        offenders
    )


def test_the_package_constructs_no_ssp_artifact_paths() -> None:
    """Artifact naming belongs to the writer; the dialect layer stays text-free."""
    offenders: list[str] = []
    for path in sorted(SRC.rglob("*.py")):
        for lineno, line in enumerate(
            path.read_text(encoding="utf-8").splitlines(), start=1
        ):
            if ".ssv" in line or "parameter_set_resource" in line:
                offenders.append(
                    f"{path.relative_to(PROJECT)}:{lineno}: {line.strip()}"
                )
    assert not offenders, "SSP artifact naming in src/:\n" + "\n".join(offenders)
