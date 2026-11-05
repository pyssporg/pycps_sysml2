---
id: INFO-009
type: info
title: Roadmap
summary: What v0.2.0 is scoped to carry, and the choices that are still open behind it.
date: 2026-11-05
status: current
---

# Roadmap

**Shipped in v0.1.0.** Parsing, the IR, variation capture and resolution,
configuration-derived selection, analysis plans, constraint evaluation, and
every SSP and FMI marker and metadata accessor, behind explicit policies. No
artifact is emitted.

**Scoped to v0.2.0.**

1. **FMI authoring attributes.** Guid policy, modelName override, capabilities
   and flags, units, declared causality and variability, binary name, and source
   language. `pyfmi_sysml2` v0.1.0 derives defaults for all of them; the markers
   are added here first, with their recognizers, and only then consumed.
2. **A second policy.** An explicit FMI-only or test `DialectPolicy` that
   exercises the seam without a second dialect. The seam exists; only the SSP
   instance is exercised today.
3. **Array and list policy.** FMI 2.0 has no arrays, so list parameters expand
   to `<name>[<index>]` scalar entries. Whether the dialect carries a count
   field and what the C header exposes stays open; the current policy is the
   expansion.
4. **Grammar review.** Evaluate a newer `sysmlpy` against the private touchpoints
   (INFO-006) before any bump. A bump is a dialect decision, not a refresh.
5. **Synthesis boundary.** `parameters/synthesis/` reads `pyssp_standard`
   objects, so it stays in `pyssp_sysml2`. Moving it would break the
   no-`pyssp_standard` rule and needs a different seam than a policy object.
6. **`fmu_resource_path`.** `core/fmi_helpers.fmu_resource_path` still returns
   `resources/<class>.fmu`, an SSP-archive path kept in v0.1.0 for verbatim
   fidelity (INFO-010). Move it to the SSP implementer.
