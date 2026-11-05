---
id: INFO-005
type: info
title: Parser
summary: What model/parser.py turns a file into, what it normalizes, and what it refuses to guess.
date: 2026-11-05
status: current
---

# Parser

`model/parser.py` is the only module that touches `sysmlpy`. It parses one file
into declarations; `model/variation.py` walks the same raw tree for the
variation facts sysmlpy does not model.

**Per file.** One file yields one package with its part, port, attribute,
requirement, and constraint definitions; each definition keeps its members,
specialization list, doc text, and `source_file`. Port direction comes from the
grammar prefix, not the public port object. Connection and binding endpoints
come from the feature chains, so a dotted end keeps both names and a bare end
stays a boundary endpoint with no part. Multiplicity comes from the grammar's
multiplicity range, including `0..*`.

**Value normalization.** `get_value()` is not trusted as written: a leading
unary minus is re-attached, `true`/`false` become real booleans, tuple literals
stay tuples, a pint `Quantity` collapses to its magnitude, and string escapes
are decoded. A value-less attribute yields `None`.

**Constraints.** `constraint def` bodies and `assert`/`assert not` usages are
captured as expressions and tokenized here; evaluation belongs to
`parameters/constraints.py`.

**Boundary.** The parser resolves no names, imports no package, and swallows no
error: a syntax error surfaces as `sysmlpy`'s `SysMLSyntaxError` with its
positions, and the loader propagates it. Unresolved references stay as written
and fail later at the consumer that needs them.
