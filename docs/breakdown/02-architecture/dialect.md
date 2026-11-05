---
id: INFO-002
type: info
title: Dialect inventory
summary: Every marker, control attribute, and variation construct the library owns, and where each lives.
date: 2026-11-05
status: current
---

# Dialect inventory

The dialect is the set of SysML v2 constructs this library gives meaning to.
Anything not listed here is language the IR keeps but no marker interprets.

| marker or construct | attaches to | value | code ref |
|---|---|---|---|
| `part def SspModel` | part def, empty marker | marker | `metadata/roles.py` |
| `part def Analysis` | part def, empty marker | marker | `metadata/roles.py` |
| `attribute def Experiment` | attribute def | `startTime`, `stopTime`, `stepSize` Real | `metadata/roles.py` |
| `attribute def SspMetadata` | attribute def | `source` String | `metadata/ssp_metadata.py` |
| `attribute def FmuMetadata` | attribute def | `source`, `implementation` String | `metadata/fmu_metadata.py` |
| `port def ParameterInterface` | port def, empty marker | marker | `parameters/dialect/markers.py` |
| `attribute def ParameterSet` | attribute def, empty marker | marker | `parameters/dialect/markers.py` |
| `pyssp_default_start_time`, `pyssp_default_stop_time` | composition part def | Real | `core/control.py` |
| `pyssp_flat_connector` | port def attribute | Boolean, read as truthy | `core/control.py` |
| `pyssp_implementation`, `pyssp_parameter_set` | retired names | rejection | `core/control.py` |
| `variation part def`, `variation attribute def` | definition | `is_variation` | `model/variation.py` |
| `variant part n : T` or `variant { body }` | variation point | `variants` | `model/variation.py` |
| `:>> p = T::v` | configuration selection | binding | `parameters/configuration.py` |
| `constraint def`, `assert [not] <expr>` | constraint usage | Boolean expression | `model/parser.py`, `parameters/constraints.py` |

**Ownership boundary.** An implementing library selects a domain by passing
policy objects, not by re-declaring markers: `RolePolicy` binds the model,
analysis, and experiment markers and their predicates, `DialectPolicy` adds the
metadata recognizers plus the retired and flat-connector rejections, and
`ControlAttributes` carries the prefix and the retired map. Marker names stay
exported as defaults (`SSP_MODEL_MARKER`, `ANALYSIS_MARKER`, the `Parameter*`
names), so a caller that wants the default writes nothing; a caller that wants
another domain constructs the policy (INFO-003).

**Core vocabulary.** The seven markers and metadata schemas in the table ship in
one packaged file, `definitions/core.sysml`; a model loads it as one included
root with `load(model, core_definitions())` instead of declaring the names
itself (INFO-012).
