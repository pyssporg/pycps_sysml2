---
id: INFO-006
type: info
title: sysmlpy pin
summary: The hard grammar pin, the private structures the parser depends on, and the rule for moving it.
date: 2026-11-05
status: current
---

# sysmlpy pin

The runtime dependency is `sysmlpy==0.96.4`, exact. Not a range, not a git ref:
the parser depends on grammar internals that the package does not promise.

**Private touchpoints.** A bump is read as a change to these, in this order:

- `sysmlpy.antlr_parser.parse(...)` returns the raw ANTLR tree. Nothing in the
  public model carries variation points, so `model/variation.py` walks that
  tree's grammar context classes directly for `variation`, `variant`, and
  configuration bodies.
- Port direction lives under `port.grammar.prefix...direction` with
  `FeatureDirection`; the public `Port` has none.
- Connection and binding endpoints live under
  `ConnectionUsage`/`BindingConnector` children, through
  `OwnedReferenceSubsetting` and `OwnedFeatureChaining`.
- Multiplicity lives in `FeatureSpecializationPart.multiplicity`, and supertypes
  in `DefinitionDeclaration.subclassificationpart`.
- `get_value()` drops a leading unary minus, returns `'true'`, `'false'`, and
  `'(1.0,2.0)'` as raw strings, returns a pint `Quantity` for unit literals, and
  raises `AttributeError` for a value-less attribute. `model/parser.py`
  normalizes all of it.
- The first load emits a benign DFA-cache `UserWarning`, suppressed at
  `model/parser.py` import time.

**The rule.** A pin bump is a dialect decision, not a dependency refresh: it
lands with a decision record, a full fixture run, and a test for every
behaviour that moved — parse shape, normalized value, or captured variation
fact. If the new grammar accepts or rejects a different document, the dialect
leaf (INFO-002) changes in the same commit.
