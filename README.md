# pycps_sysml2

The SysML dialect layer for our CPS artifacts: it parses SysML v2 into a
repo-owned IR and owns variation, selection, constraints, and every marker and
metadata accessor for the SSP and the FMI dialects.

**Boundary.** This library reads and interprets SysML. It emits no artifact: no
SSD, SSV, SSM, SSP, modelDescription, C header, or FMU. `pyssp_sysml2` (SSP
artifacts) and `pyfmi_sysml2` (FMI artifacts) are implementers: both import
`pycps_sysml2` for every SysML read and keep no parser, marker set, or IR of
their own. A consumer that needs SysML knowledge installs this package; a
consumer that needs an artifact installs an implementer.

It is not a SysML v2 conformance suite, not a general SysML toolchain, and not a
`pyssp_standard` wrapper. v0.1.0 carries no FMI authoring attributes.

## Install

From the release wheel:

```bash
pip install "pycps-sysml2 @ https://github.com/pyssporg/pycps_sysml2/releases/download/v0.1.0/pycps_sysml2-0.1.0-py3-none-any.whl"
```

The one runtime dependency is pinned exactly: `sysmlpy==0.96.4`. From a
checkout:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
```

Requires Python 3.10 or newer; CI runs 3.11 and 3.12.

## No CLI

v0.1.0 ships no console script. There is no entry point, no
`python -m pycps_sysml2`, and nothing installed on `PATH`: the Python API is the
surface.

## Python API

Save this as `plant.sysml`:

```sysml
package Plant {
  part def SspModel;
  attribute def SspMetadata { attribute source : String; }
  attribute def PlantSource :> SspMetadata { attribute source = "plant.sysml"; }

  port def Signal { attribute value : Real; }
  part def Step { out port y : Signal; }
  part def Sine { out port y : Signal; }

  variation part def SourceChoice {
    variant part step : Step;
    variant part sine : Sine;
  }

  part def PlantComposition :> SspModel {
    attribute ssp_source : PlantSource;
    part source : SourceChoice;
  }
}
```

Then load it, select a variant, and read the dialect metadata:

```python
from pycps_sysml2 import load
from pycps_sysml2.metadata import ssp_metadata
from pycps_sysml2.parameters import SSP_POLICY, resolve

architecture = load("plant.sysml")          # a file or a directory of files

chosen = resolve(
    architecture,
    "PlantComposition",
    {"source": "step"},                     # usage name -> variant name
    roles=SSP_POLICY.roles,                 # required: the domain is a policy
)

composition = chosen.get_part_def("PlantComposition")
print(chosen.part_definitions["PlantComposition"].parts["source"].type_name)
print(ssp_metadata(chosen, composition).source)
print(SSP_POLICY.control.default_start)
```

```text
Step
plant.sysml
pyssp_default_start_time
```

`resolve` returns a deep copy; `architecture` is untouched. `roles=` is the
exact policy argument: every public entry point under `parameters/` requires it
and supplies no default. `SSP_POLICY.roles` is `SSP_ROLES`; another domain
constructs its own `RolePolicy` or `DialectPolicy`.

## Errors and limits

- `load()` raises `FileNotFoundError` for a missing path or an empty directory,
  `sysmlpy`'s `SysMLSyntaxError` for a syntax error, and `ValueError` for a
  package mismatch or a duplicate definition across files.
- Loading does not validate. An unresolved reference surfaces later as a missing
  lookup or a `ValueError` from the consumer that needed it.
- `resolve` and `resolve_selected` raise `ValueError` naming the key, its owner,
  and the paths that are reachable when a selection is unknown, ambiguous, or
  not a variation point.
- `ssp_metadata` and `fmu_metadata` raise `ValueError` for a missing marker
  definition, an unmarked owner, an unknown member, or a non-String value.
- One dialect ships: SSP. There is no `GENERIC_POLICY`; a non-SSP domain passes
  an explicit policy.
- Dialect limits: one `parameters` port per part, tuple-valued list attributes,
  and `metadata`/`comment` reserved as words.
- FMI authoring attributes (guid policy, modelName override, capabilities, units,
  declared causality) are out of scope for v0.1.0; `pyfmi_sysml2` derives them.

## Development

```bash
ruff check src tests
python -m pytest -m "not slow"      # the CI gate
python -m pytest                    # includes slow
python -m build                     # wheel and sdist
```

Intent, architecture, and the dialect inventory live in `docs/breakdown/`;
`AGENTS.md` states the rules a change must satisfy.
