---
id: CP-001
type: capability
title: Scope
summary: Loading, IR, export, variation, selection, constraints, and dialect accessors a caller can rely on.
date: 2026-11-05
status: current
---

# Scope

**Promise.** One package answers every SysML question an implementer asks, and
answers it the same way for the SSP and the FMI domain.

- **Load.** `load(path, *includes)` takes a `.sysml` file or a directory of
  them as the primary root, loads the sorted files in one sysmlpy parse into
  one same-package `Architecture`, and does not validate: unresolved
  references surface later as missing lookups. Further roots in `*includes` (or after the first element of
  a sequence) merge included definitions under any package name; a duplicate
  definition is an error and included names are excluded from export.
- **IR.** Part, port, attribute, requirement, and constraint definitions and
  usages, with multiplicity, typed values, doc text, `source_file`, connections
  keyed by endpoint pair, and bindings kept as feature chains.
- **Export.** `Architecture.export_declared()` emits one SysML text per source
  file that reloads to the same declarations; the writer refuses a configuration
  body it cannot carry rather than dropping it.
- **Variation.** Definition, usage, attribute, and body variation points are
  captured; `resolve` and `resolve_selected` substitute one selection and
  return the canonical path map.
- **Selection.** `derived_selection` reads the bindings of a configuration,
  and `analysis_selections`/`analysis_plans` classify each analysis as legal,
  violated, or invalid after constraint evaluation.
- **Constraints.** `evaluate` and `enforce_constraints` run `assert`
  expressions over a resolved architecture and return a report.
- **Dialect.** Marker names are exported defaults; `RolePolicy`,
  `DialectPolicy`, and `ControlAttributes` select the domain (INFO-003). SSP
  metadata, FMU metadata, experiments, parameter interfaces and sets, and the
  `pyssp_*` control attributes are all readable through this package.

**Contract.** Every domain-sensitive entry point takes its policy keyword-only
and required. No artifact is read or written. Failures raise `FileNotFoundError`
or `ValueError` naming the member, its owner, and the path involved.
