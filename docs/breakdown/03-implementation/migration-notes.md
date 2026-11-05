---
id: INFO-010
type: info
title: Extraction record
summary: What v0.1.0 took from pyssp_sysml2 v0.3.0, and what it left behind.
date: 2026-11-05
status: current
---

# Extraction record

Provenance: `pyssp_sysml2` v0.3.0 at commit `5856b41`; this is a subset plus a policy seam, not a fork.

**Moved.** `model/*.py` verbatim (only the package name changed);
`core/control.py` rewritten onto `ControlAttributes` (INFO-003);
`core/fmi_helpers.py` verbatim; `metadata/{roles,ssp_metadata,fmu_metadata}.py`
onto one `metadata/helpers.py` with `RolePolicy` added; `parameters/dialect/`
with SSP and FMI decisions turned into `DialectPolicy` lookups;
`parameters/{configuration,variation,selection,constraints}.py` with the role
predicates injected as `roles=RolePolicy`. Six private helper copies are gone
(`_specializes_marker` at `roles.py:57`, `ssp_metadata.py:70`,
`fmu_metadata.py:79`, `dialect/markers.py:24`; `_effective_members` at
`roles.py:200`, `ssp_metadata.py:93`, `fmu_metadata.py:102`), keeping the
direct-marker and transitive-marker forms distinct so `is_parameter_set` stays
`False` for the marker definition itself while `is_ssp_model` stays `True`.

**Not moved.** `parameters/synthesis/` imports `pyssp_standard`
(`inputs.py:15`, `interfaces.py:10`), so it stays in `pyssp_sysml2` v0.4.0 and
consumes the public dialect surface plus `core.control`. `parameter_set_resource`
(`parameters/dialect/markers.py:44-47`) returns `f"{prefix}/{set_name}.ssv"`,
an artifact path, so `pyssp_sysml2` re-adds it for `artifacts/ssp.py:347` and
`artifacts/ssd.py:158`. `core/paths.py`, `artifacts/`, `sysml/`, `cli.py` and
the old root `__init__.py` stay behind; `artifacts/fmi.py` belongs to
`pyfmi_sysml2`.

**Behaviour changes.** Policy arguments are required keyword-only with no
implicit default; a domain-neutral diagnostic that named `SspModel` now says
"model composition"; `validate_parameter_dialect` consults the injected policy
instead of module constants. Parsing, IR, resolution, selection, constraints and
list expansion (`<name>[<index>]`) are unchanged. Dropped tests: INFO-011.
