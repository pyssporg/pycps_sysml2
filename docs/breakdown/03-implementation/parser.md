---
id: INFO-005
type: info
title: Parser
summary: What model/parser.py turns a file into, what it normalizes, and what it refuses to guess.
date: 2026-11-05
status: current
---

# Parser

`model/parser.py` is the only module that touches `sysmlpy`. It loads one merged
set of files into declarations; `model/variation.py` walks each file's raw tree
for the variation facts sysmlpy does not model.

**Merged parse.** `parse_files(paths)` hands every file of every root to one
`sysmlpy.load_files` call, so sysmlpy merges files that declare the same
package and the loader no longer does. `parse_packages(path)` stays the
one-file entry point and is the per-file attribution pass: the merged model
exposes no `source_file`, so each definition's origin comes from a second
parse of every file. Text concatenation is not equivalent; `loads` keeps
duplicate packages apart and reports `DUPLICATE_NAME`. The primary root must
still resolve to one package name; include roots may use any name. sysmlpy
keeps only the first file's imports when it merges a repeated package, so
imports are collected in the per-file pass, not from the merged model.

**Declarations.** Each package yields part, port, attribute, requirement, and
constraint definitions; each definition keeps its members, specialization
list, doc text, and `source_file`. The same pass reads the package's `import`
declarations as `(package, member)` pairs (`None` for `::*`), preferring the
structured grammar objects and falling back to `dump()` text. Port direction
comes from the grammar prefix, not the public port object. Connection and
binding endpoints come from the feature chains, so a dotted end keeps both
names and a bare end stays a boundary endpoint with no part. Multiplicity comes
from the grammar's multiplicity range, including `0..*`.

**Value normalization.** `get_value()` is not trusted as written: a leading
unary minus is re-attached, `true`/`false` become real booleans, tuple literals
stay tuples, a pint `Quantity` collapses to its magnitude, and string escapes
are decoded. A value-less attribute yields `None`.

**Constraints.** `constraint def` bodies and `assert`/`assert not` usages are
captured as expressions; body scanning and tokenization live in
`model/source.py`, and evaluation belongs to `parameters/constraints.py`.

**Boundary.** The parser resolves no names and rejects no import target: a
syntax error surfaces as `sysmlpy`'s `SysMLSyntaxError` with its positions, and
the loader propagates it. Unresolved references stay as written and fail later
at the consumer that needs them.
