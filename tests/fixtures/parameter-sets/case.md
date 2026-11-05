# Case: `parameter-sets`

Inputs for `tests/test_parameter_sets.py`. The test is the oracle: it asserts on
the resolved declarations and mapping specs, so this directory holds no expected
file.

## Artifacts

All paths are relative to this directory.

| Path | Kind |
| --- | --- |
| `template.sysml` | SysML v2 template, filled once per test |
| `two-sets-one-member.sysml` | complete document: two sets bound to one member |
| `two-disjoint-sets.sysml` | complete document: two sets bound to different members |
| `interface-only.sysml` | complete document: interface without an applied set |

`template.sysml` is filled per test by `render_fixture` with
`$interface_marker`, `$interface_members`, `$sets`, `$composition`, and
`$COMPOSITION_NAME`. It carries the package scaffolding that would otherwise be
repeated in every test body.

The short `sets`, `composition`, and `interface_members` fragments stay inline in
the test on purpose: they are the case, not the document.

## What this case proves

The set pins the documented parameter dialect: marker definitions, parameter
ports, applied and unapplied sets, per-member and whole-object binds, and the
mapping specs derived from them. The documents exist because a change to that
dialect has to be reviewable as SysML, not only as a diff in a test body.

## Update history

| Date | Change | Reason |
| --- | --- | --- |
| 2026-10-28 | Documents moved out of the test module | Every test body started with an escaped document |
| 2026-11-05 | Copied into this library, artifact assertions removed | The dialect reader was extracted from the SSP toolchain |

## Provenance

Copied from `pyssporg/pyssp_sysml2`, commit `5856b41` (tag `v0.3.0`), path
`tests/fixtures/parameter-sets/`. Duplicated rather than referenced because this
library has no dependency on the SSP toolchain; the parameter dialect is still
shared, so the same SysML documents are evidence in both repositories. The
documents are copied text-only; only the declaration and mapping assertions are
ported.
