---
id: INFO-004
type: info
title: Module map
summary: Every module's responsibility and the imports the layering rule allows it.
date: 2026-11-05
status: current
---

# Module map

`src/pycps_sysml2/` is split by concern; the root re-exports `load` and the
dataclasses.

| module | responsibility | may import |
|---|---|---|
| `model/model.py` | IR dataclasses: architecture, definitions, usages, attributes, connections, bindings, constraints | stdlib |
| `model/names.py`, `model/exporter.py` | name quoting and unquoting; SysML text emission | `model.model` |
| `model/parser.py` | one file to declarations: values, directions, multiplicity, supertypes, constraint usages | `sysmlpy`, `model.names`, `model.model`, `model.source` |
| `model/source.py` | authored source text: connection endpoints, comment/string masking, constraint bodies | `model.model` |
| `model/variation.py` | the raw ANTLR walk: variation points, variants, configuration bodies | `sysmlpy`, `model.model` |
| `model/loader.py` | primary-root file walk, one merged parse, IR construction, duplicate rejection | all of `model` |
| `model/attribution.py` | per-file scan: packages, variation facts, constraint bodies, definition-to-file attribution | `model.parser`, `model.source`, `model.variation`, `model.names` |
| `definitions/` | the packaged core vocabulary and `core_definitions()` | stdlib |
| `core/control.py`, `core/fmi_helpers.py` | control attributes with injectable prefix and retired map; FMI helpers | `model` |
| `metadata/helpers.py` | the single copy of `short_name`, `specializes_marker`, `effective_members` | `model` |
| `metadata/roles.py`, `metadata/ssp_metadata.py`, `metadata/fmu_metadata.py` | role policy, SSP metadata, FMI metadata | `model`, `core`, `metadata.helpers` |
| `parameters/policy.py` | `DialectPolicy` and `SSP_POLICY` | `metadata`, `core` |
| `parameters/configuration.py`, `variation.py`, `selection.py`, `constraints.py` | configuration capture, resolution, analysis plans, constraint evaluation | `metadata`, `core`, `model` |
| `parameters/dialect/` | markers, declarations, composition, mapping | `metadata`, `core`, `model` |

**Layering rule.** `model` ← `core` ← `metadata` ← `parameters`, with
`parameters/dialect` above `metadata`. Nothing below `parameters` imports
`parameters`; nothing below `metadata` imports a marker constant or calls
`is_ssp_model`/`is_analysis`/`is_fmu_model`. There is no `cli.py`,
`artifacts/`, or `sysml/`.
