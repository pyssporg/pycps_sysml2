---
id: INFO-011
type: info
title: Test port record
summary: Which pyssp_sysml2 tests were dropped or split when the suite moved.
date: 2026-11-05
status: current
---

# Test port record

**Dropped with their subject.** `test_golden_artifacts.py` and `tests/golden/`,
`test_generate_*`, `test_sync`, `test_roundtrip`, `test_cli`,
`test_constraints_cli` — each judges an emitted artifact, never the unit here.

**Re-authored.** The role half of `test_roles_analysis.py` became
`test_metadata_roles.py`; the accessor halves of `test_ssp_metadata.py` and
`test_fmu_metadata.py` became `test_metadata_dialects.py`.

**Split.** `test_variation.py` (80) → `test_variation_model.py` (57); the 23
artifact tests and the `_ssd_tree` / `_component_sources` / `_ssv_values`
helpers stayed behind. `test_selection.py` (34) → `test_selection_model.py`
(29). `test_parameter_sets.py` (27) kept one generic and one split test;
25 dropped. `test_parameter_ports.py` and `test_parameter_bind_orientation.py`
kept their generic halves. `test_fixture_policy.py` kept the fixture half,
extended so every `fixtures/*/case.md` carries the mandatory headings.
`test_layering.py` kept two generic gates and gained the AST gate on
`pyssp_standard` / `pyssp_sysml2` imports.

**Fixtures.** Generic inputs only: `sysml-model`, `quoted-names`, `arrays`,
`configuration`, `constraints`, `variation`, `selection`, the three
`parameter-*` sets, and the accessor subset of `fmu-metadata`. Each `case.md`
carries the mandatory headings plus `## Provenance`. The duplication is
intentional: these inputs are the dialect's own vocabulary, so an implementing
library must change its output without editing them.

**Level map.** `tests/conftest.py` assigns every file a level (`static`, `unit`,
`component`, `contract`, `system`, `slow`); unlisted files default to `unit`.
The CI gate is `pytest -m "not slow"`.
