# Case: `core-definitions`

Input for `tests/test_core_definitions.py`: a model that uses the shared dialect
markers without declaring them, so the test can compare the default load with a
load that merges the bundled core definitions.

## Artifacts

| Path | Behaviour |
| --- | --- |
| `marker-user.sysml` | imports `ScalarValues` and `PysspCore`, then uses `SspModel`, `ParameterInterface`, and `FmuMetadata` without declaring them |

## What this case proves

The fixture has no local marker declarations, so the default load leaves every
marker unresolved and the validation gates fail. Loading it with
`load(model, core_definitions())` must resolve the markers, keep the included
definitions out of `export_declared()`, and succeed for role, parameter, and FMU
metadata lookups.

## Update history

| Date | Change | Reason |
| --- | --- | --- |
| 2026-11-05 | Case record and `marker-user.sysml` added | The core-definition library test needs a marker-free model as reviewable SysML, not a Python literal |
