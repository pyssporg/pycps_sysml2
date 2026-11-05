---
id: INFO-001
type: info
title: Intent
summary: Why pycps_sysml2 exists — one home for our SysML dialect — and what it refuses to become.
date: 2026-11-05
status: current
---

# Intent

**Purpose.** `pycps_sysml2` is the single home of our SysML dialect: it parses
SysML v2, builds the IR, and owns variation, selection, constraints, and every
marker and metadata accessor for the SSP and FMI dialects alike (`SspModel`,
`Analysis`, `Experiment`, `SspMetadata`, `FmuMetadata`, `ParameterInterface`,
`ParameterSet`, the `pyssp_*` control attributes).

**Roles and commitments.** `pyssp_sysml2` and `pyfmi_sysml2` implement this
dialect: each imports the package for every SysML read and keeps no parser,
marker set, or IR, and implementers build on released wheels. One owner per
marker, name, or rule, selected through the policy objects (INFO-003); one
parser behind one module with a pinned grammar (INFO-006); a repo-owned IR,
never sysmlpy objects; nothing below `metadata/` imports a marker.

**Non-goals.** No artifact emission: no SSD, SSV, SSM, SSP, modelDescription, C
header, or FMU packaging. No `pyssp_standard` dependency, direct or transitive.
Not a SysML v2 conformance suite or a general SysML toolchain. No FMI authoring
attributes in v0.1.0 (guid, modelName override, capabilities, units, declared
causality), nor artifact-to-SysML synthesis, which needs `pyssp_standard`.
