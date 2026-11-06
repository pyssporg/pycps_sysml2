<!-- GENERATED FILE — do not edit. Regenerate with pb-registers. -->

# Decision Stream

Flat, dated history of every committed design choice. Current state lives
in the layer leaves named by each record's `state:` field.

Records live in the cold-storage archive; extract one with `pb archive read <ID>`.

## By Layer

### Intent

- **DEC-001** — pycps_sysml2 owns the SysML dialect · accepted · 2026-11-05 · `DEC-001`
  Parsing, the IR, and every marker and metadata accessor move into one library that pyssp_sysml2 and pyfmi_sysml2 implement.

### Architecture

- **DEC-002** — Domain selection is an explicit policy · accepted · 2026-11-05 · `DEC-002`
  RolePolicy, DialectPolicy, and ControlAttributes replace hard-coded markers, are keyword-only, and have no generic default.
- **DEC-004** — Imports gate cross-package visibility · accepted · 2026-11-05 · `DEC-004`
  A qualified definition is visible only if its package is imported; unknown targets stay a loader-untouched concern for analyze.

### Implementation

- **DEC-003** — sysmlpy is pinned exactly · accepted · 2026-11-05 · `DEC-003`
  The parser depends on grammar internals, so sysmlpy is pinned to 0.96.4 and a bump is a dialect decision with a test.
