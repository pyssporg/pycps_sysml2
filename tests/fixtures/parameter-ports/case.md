# Case: `parameter-ports`

Inputs for `tests/test_parameter_ports.py`. The test is the oracle: it asserts
on the loaded model and the resolved interface, so this directory holds no
expected artifact.

## Artifacts

All paths are relative to this directory.

| Path | Kind |
| --- | --- |
| `template.sysml` | SysML v2 template, filled once per test |
| `connected-ports.sysml` | complete document: two parameter ports wired with `connect` |

`template.sysml` is filled per test by `render_fixture` with `$port`, `$markers`,
`$interface_decl`, `$interface_members`, and `$COMPOSITION_NAME`. It carries the
package scaffolding that would otherwise be repeated in every test body.

The short `port`, `markers`, `interface_decl`, and `interface_members`
fragments stay inline in the test on purpose: they are the case, not the
document.

## What this case proves

The set pins the parameter port contract: direction and marker validation, the
retired attribute carrier, the marker-kind rule, and the flat-connector marker
rejection. `connected-ports.sysml` records what a wired pair of parameter ports
looks like; whether a consumer may emit that wiring is the consumer's rule and
is not asserted here.

## Update history

| Date | Change | Reason |
| --- | --- | --- |
| 2026-10-28 | Template and document moved out of the test module | Test bodies carried escaped document text |
| 2026-11-05 | Copied into this library, artifact assertions removed | The dialect reader was extracted from the SSP toolchain |

## Provenance

Copied from `pyssporg/pyssp_sysml2`, commit `5856b41` (tag `v0.3.0`), path
`tests/fixtures/parameter-ports/`. Duplicated rather than referenced because
this library has no dependency on the SSP toolchain; the parameter dialect is
still shared, so the same SysML documents are evidence in both repositories. The
documents are copied text-only; only the reader-level assertions are ported.
