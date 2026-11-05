# Case: `variation`

Input documents for `tests/test_variation_model.py`. Every file is a complete
SysML v2 package that a test writes with `write_model` and loads; nothing is
generated from them, so the tree holds inputs only.

- **Conversion:** SysML v2 text → `Architecture` through
  `pycps_sysml2.model.load`, then variation resolution
  (`pycps_sysml2.parameters.variation.resolve`).
- **Requirement / fault:** a variation point must be captured, resolved by its
  usage path, or refused by name — never flattened silently. The set pins
  definition-level, usage-level, body-level, nested, and attribute variation,
  plus the errors for an unselected point, an unknown variant, an ambiguous
  bare key, a body port the point does not declare, three levels of nesting,
  and a body attribute carrying a value it cannot keep.
- **Level:** unit. Every test reads the parsed or resolved model; no artifact is
  generated from these documents.
- **Input:** the files listed below. `definition.sysml`,
  `definition-fmu.sysml`, `usage.sysml`, `body.sysml`, `nested.sysml`,
  `ambiguous-names.sysml`, `no-variation.sysml`,
  `undeclared-body-port.sysml`, `three-levels.sysml`,
  `valued-body-attribute.sysml`, `attribute-variation.sysml`,
  `attribute-set-variation.sysml`, `untyped-attribute-variant.sysml`,
  `ambiguous-nested.sysml`, `resolution-order.sysml`, `nested-unknown.sysml`,
  `nested-under-replaced.sysml`, `body-checks.sysml`, `member-rules.sysml`,
  `config-body-unnamed-part.sysml`, `config-body-unnamed-attribute.sysml`,
  `config-body-unsupported-member.sysml`, `variant-body-unnamed-part.sysml`,
  `variant-body-unnamed-attribute.sysml`, and
  `variant-body-unsupported-member.sysml` were authored here for these tests.
  `usage-level.sysml`, `connection.sysml`,
  `parameter-binding.sysml`, and `nested-body.sysml` are the variation-point
  examples from the product repository
  (`docs/breakdown/06-evolution/selected/examples/variation-points/`), moved
  verbatim with their descriptive header comment omitted.
- **Expected:** none. There is no expected artifact for these inputs; each test
  is its own oracle and asserts parsed structure or generated artifact content
  inline.
- **Independent oracle:** the tests. The parsed-structure assertions in
  `tests/test_variation_model.py` are the only authority on what each document
  must produce.
- **Comparison:** exact values in test assertions and `pytest.raises` message
  matches for the refusal cases.
- **Normalization:** none. Each file is stored exactly as `write_model` writes
  it: stripped, with one trailing newline.
- **Volatile fields:** none.
- **Update policy:** edit a document only together with the test that reads it;
  the tests fail on any byte change that alters the parsed model.
- **Notes:** two different documents are both named "nested variation" in the
  test module: `nested.sysml` is the local dotted-key case and
  `nested-body.sysml` is the two-level body example. They are separate files on
  purpose.

## Artifacts

Inputs, relative to this directory. None is generated.

| Path | Behaviour |
| --- | --- |
| `definition.sysml` | variation part def with two variants |
| `definition-fmu.sysml` | the same shape with FMU metadata, so a selection changes the usage type |
| `usage.sysml` | `variation part` usage with its own variants |
| `body.sysml` | variant with a statement body: nested parts and boundary connections |
| `nested.sysml` | variation point reached by a dotted usage path |
| `ambiguous-names.sysml` | bare selection key that matches two usages |
| `no-variation.sysml` | architecture without any variation construct |
| `undeclared-body-port.sysml` | body connects to a port the point does not declare |
| `three-levels.sysml` | variation nested three levels deep, refused |
| `valued-body-attribute.sysml` | variant body attribute with a value, refused |
| `attribute-variation.sysml` | `variation attribute def` marker |
| `attribute-set-variation.sysml` | attribute variation over parameter sets, resolved through an analysis |
| `untyped-attribute-variant.sysml` | attribute variant without a resolvable type |
| `ambiguous-nested.sysml` | nested suffix key that matches two dotted paths |
| `resolution-order.sysml` | shallow and nested variation points selected together |
| `nested-unknown.sysml` | unknown variant under an already resolved outer point |
| `nested-under-replaced.sysml` | inner key removed by the outer body selection |
| `body-checks.sysml` | body connection to an undeclared part, name collision, attribute clash |
| `member-rules.sysml` | variant member shapes and points without captured variants |
| `config-body-unnamed-part.sysml` | configuration body part with no name and no single redefinition |
| `config-body-unnamed-attribute.sysml` | configuration body attribute with no name and no single redefinition |
| `config-body-unsupported-member.sysml` | configuration body member the walk cannot carry |
| `variant-body-unnamed-part.sysml` | variant body part with no name |
| `variant-body-unnamed-attribute.sysml` | variant body attribute with no name |
| `variant-body-unsupported-member.sysml` | variant body member the walk cannot carry |
| `usage-level.sysml` | example 03: usage-level point, retained with the example set |
| `connection.sysml` | example 08: two path variants with different decompositions |
| `parameter-binding.sysml` | example 09: variation over parameter bindings inside an analysis |
| `nested-body.sysml` | example 10: variation point nested in a variant body |

## What this case proves

If these documents were dropped, the loader and resolver tests would have to
inline SysML again, and a reviewer could not read the input as SysML. Keeping
one file per behaviour also keeps the refusal cases distinguishable: the same
bytes cannot serve both the accepted and the rejected shape.

## Update history

| Date | Change | Reason |
| --- | --- | --- |
| 2026-10-28 | Case record added; documents moved out of the test modules | Test inputs were Python string literals, not reviewable SysML files |
| 2026-10-30 | Added nested ambiguity, resolution-order, replaced-point, body-check, member-rule, and body-capture documents | The resolver's error paths and ordering were only half covered |
| 2026-11-05 | Copied into this library, artifact cases dropped | The variation resolver was extracted; SSD, SSP, and analysis generation stayed behind |

## Provenance

Copied from `pyssporg/pyssp_sysml2`, commit `5856b41` (tag `v0.3.0`),
path `tests/fixtures/variation/`. Duplicated rather than referenced because
this library has no dependency on the SSP toolchain; the model-level
behaviour is still shared, so the same SysML documents are evidence in both
repositories. The authored `SspModel` / `pyssp_*` identifiers are this
library's dialect vocabulary, not upstream leakage.
