# Case: `packages`

Input documents for `tests/test_package_namespace.py`. Every file is a complete
SysML v2 package that a test loads through `pycps_sysml2.model.load`; nothing is
generated from them, so the tree holds inputs only.

- **Conversion:** SysML v2 text → `Architecture`. A directory root loads its
  `*.sysml` files (one package per file); a second root is an include.
- **Requirement / fault:** package names are first-class in the IR. A definition
  of the primary package keeps its bare key, a definition of another package is
  keyed `Pkg::Name`, and `Definition.name` stays bare. Two packages may declare
  the same bare name; a bare lookup then prefers the primary and an ambiguous
  bare lookup is refused. An included package is visible only through a
  `private import`, which the `Fixed` fixtures declare. Included packages never
  reach `export_declared`, and a qualified configuration value
  `Pkg::Type::variant` resolves its type.
- **Level:** unit. Every test reads the parsed model.
- **Input:** `primary/` (package `Fixed`, two files so export emits two
  `package` blocks), `alpha/` (package `Alpha`, declaring `Same` and the
  `SourceChoice` variation definition), `beta/` (package `Beta`, declaring
  `Same`), and `configuration/` (package `Fixed`, declaring the model,
  configuration, and analysis-local compositions).
- **Expected:** none. Each test asserts the parsed keys, resolution result, or
  exported text inline.
- **Independent oracle:** the tests.
- **Comparison:** exact dict keys, object identity, and `pytest.raises` message
  matches.
- **Normalization:** each file is stored exactly as authored, one trailing
  newline.
- **Volatile fields:** none.
- **Update policy:** edit a document only together with the test that reads it.

## Artifacts

Inputs, relative to this directory. None is generated.

| Path | Behaviour |
| --- | --- |
| `primary/model.sysml` | package `Fixed`: imports `Alpha` and declares `Same`, `System :> Same` |
| `primary/extra.sysml` | package `Fixed`: `Extra`, a second source file |
| `alpha/definitions.sysml` | package `Alpha`: its own `Same` and `SourceChoice` |
| `beta/definitions.sysml` | package `Beta`: its own `Same` |
| `configuration/model.sysml` | package `Fixed`: imports `Alpha`/`Beta`, variation point, configuration binding, composition |

## What this case proves

The IR can hold two definitions of the same bare name without collision, keeps
each definition's source file with its own package, resolves a bare name to the
primary package and a qualified name exactly, and refuses a genuinely ambiguous
bare lookup. It also proves that the exporter emits only the architecture's own
package, and that a `Pkg::Type::variant` configuration value resolves its type
through the package-aware namespace. Without these documents a reviewer could
not tell which package each key came from.

## Update history

| Date | Change | Reason |
| --- | --- | --- |
| 2026-11-05 | Case record added | Package-first IR needed same-name evidence in two packages |
