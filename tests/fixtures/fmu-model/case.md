# Case: `fmu-model`

Input for the composition test in `tests/test_policy_injection.py`: three part
definitions that carry typed FMU metadata under the different role shapes, so the
test can show which one the marker accepts.

## Artifacts

| Path | Behaviour |
| --- | --- |
| `component.sysml` | `FmuModel` marker; a marked component, an unmarked part, and a marked part with subparts, all carrying `fmu_meta` |

## What this case proves

FMU metadata on a composition that specializes `FmuModel` belongs to the export
unit and passes validation. The same metadata on a part that does not specialize
the marker is still rejected as "not an FMU component", and a marked definition
that also has subparts is still rejected, because a nested system cannot also be
an FMU component.

## Update history

| Date | Change | Reason |
| --- | --- | --- |
| 2026-11-05 | Case record and `component.sysml` added | The direct `:> FmuModel` marker replaced the `Fmu` composition root; the three rejection shapes are reviewable SysML, not a Python literal |
