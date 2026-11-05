# Case: `fmu-metadata` (accessor subset)

The SysML template for typed FMU metadata: a schema definition, a concrete
definition, and the part that uses it. Only the loader-level accessor cases are
kept here; the SSP/FMI artifact cases from the originating suite stay there.

## Artifacts

All paths are relative to this directory.

| Path | Kind |
| --- | --- |
| `template.sysml` | Input, template with `$marker`, `$concrete`, `$part_body`, `$COMPOSITION_NAME` |

The marker definition, the concrete definition, and the part body stay inline in
`tests/test_metadata_dialects.py` on purpose: they are short fragments whose
point is the difference between two tests, not a document a reviewer reads on
its own.

## What this case proves

Filling the template proves default resolution and value-less redeclaration
through the effective-member merge, rejection of a non-string metadata value, of
duplicate metadata attributes, of the schema used directly, and of a metadata
usage whose definition is missing the marker. The document is what a reviewer
reads as SysML; the accessor is the oracle.

## Update history

| Date | Change | Reason |
| --- | --- | --- |
| 2026-11-05 | Accessor-level subset copied into this library | The typed-metadata accessor was extracted from the SSP toolchain |

## Provenance

Copied from `pyssporg/pyssp_sysml2`, commit `5856b41` (tag `v0.3.0`), path
`tests/fixtures/fmu-metadata/template.sysml`. Duplicated rather than referenced
because this library must stand alone: it has no dependency on the SSP
toolchain, and its accessor tests need the same document as evidence. Only the
template is copied — the artifact-bound cases and documents
(`parameter-connector.sysml`, `retired-implementation.sysml`) stay upstream.
