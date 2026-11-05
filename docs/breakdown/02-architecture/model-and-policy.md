---
id: INFO-003
type: info
title: Model and policy
summary: The IR, the layering rule, and the three policy objects a domain is selected with.
date: 2026-11-05
status: current
---

# Model and policy

**Layering.** `model` ← `core` ← `metadata` ← `parameters`, where an arrow means
"may import": `model` has no internal dependency, `core` may use `model`,
`metadata` may use `core` and `model`, and `parameters` may use all three.
`parameters/dialect` sits above `metadata`. Nothing below `parameters` imports
`parameters`, and no module below `metadata` imports a marker constant or calls
`is_ssp_model`/`is_analysis`/`is_fmu_model`; a static layering test enforces both
rules.

**The IR.** `Architecture` is a merged, insertion-ordered dataclass tree
(definitions, usages, attributes, ports, connections, bindings, constraints,
variation facts). It is repo-owned: no sysmlpy object crosses the parser
boundary, and loading is non-validating.

**Package namespace.** Packages are first-class in storage only: a definition of
the architecture's own package (or a synthesized one) is keyed by its bare
`name`, one from any other package by `Pkg::Name`, and `Definition.name` stays
bare so no qualifier reaches an artifact surface. One resolver
(`Architecture.resolve`) serves every lookup: an exact stored key wins, a bare
name falls back to qualified keys (one match resolves, several raise naming each
candidate), a qualified miss returns `None`.

**Three policy objects.** `RolePolicy` (`metadata/roles.py`) binds the model,
analysis, FmuModel, and experiment markers to their predicates and default
implementations. `DialectPolicy` (`parameters/policy.py`) composes a
`RolePolicy` with a `ControlAttributes`, the SSP and FMI metadata recognizers,
and the retired-attribute and flat-connector rejections. `ControlAttributes`
(`core/control.py`) carries the attribute prefix and the retired map, so
`ControlAttributes(prefix="acme_")` works end to end.

**Defaults.** Marker names stay exported (`SSP_MODEL_MARKER`,
`ANALYSIS_MARKER`, `FMU_MODEL_MARKER`, `PARAMETER_INTERFACE_MARKER`,
`PARAMETER_SET_MARKER`), and
`SSP_ROLES` / `SSP_POLICY` are the default instances. There is no
`GENERIC_POLICY`: a non-SSP domain constructs its policy explicitly, because
implicit domain-neutral behaviour hides which dialect is being read.

**Injection.** Public entry points in `parameters/` and `parameters/dialect/`
take the policy keyword-only and required; private helpers take it positionally
and forward it, so every call site states its domain.
