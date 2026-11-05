---
id: INFO-012
type: info
title: Core definitions
summary: The dialect markers and metadata schemas ship once as package data; a model loads that file as one include root and never redeclares one.
date: 2026-11-05
status: current
---

# Core definitions

`src/pycps_sysml2/definitions/core.sysml` is the single copy of the shared
vocabulary (`package PysspCore`): `SspModel`, `Analysis`, `FmuModel`,
`ParameterInterface`, `ParameterSet`, `FmuMetadata`, `SspMetadata`, and
`Experiment`.

- **Package data:** `pyproject.toml` lists `definitions/*.sysml`, so the wheel
  carries the file; `core_definitions()` returns it as a real `Path` and
  refuses a zipped install.
- **Multi-root load:** `load(path, *includes)` takes one primary model root and
  any number of included definition roots. `path` is one root or a sequence
  whose first element is the primary; further elements and `*includes` are
  included roots. With no includes, `load(primary)` behaves exactly as before.
- **Primary vs included:** every primary file must declare the same package;
  an included root may declare any package, because it supplies definitions
  rather than composition.
- **Duplicate rule:** a definition the model also declares raises `ValueError`
  naming the definition, its kind, both sources, and the local declaration to
  remove; never an override. One name supplied by two included roots is also
  an error and names both roots.
- **Export exclusion:** every included name lands in
  `Architecture.included_definitions`, and `export_declared()` skips those
  names.
- **Implementers:** `pyssp_sysml2` exposes the same merge as keyword-only
  `includes` (a sequence of roots), off by default; its `--core-definitions`
  flag is sugar for one `core_definitions()` include.
