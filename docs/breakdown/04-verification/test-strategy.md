---
id: TEST-001
type: test
title: Test strategy
summary: Six levels, one marker per test, and the default CI gate that runs everything but slow.
date: 2026-11-05
status: current
---

# Test strategy

Every test carries exactly one level marker. The level states what the test is
evidence for, not how long it runs.

| marker | the test proves |
|---|---|
| `static` | a property of the source or the tree: layout, layering, fixture policy, one version source |
| `unit` | one object's behaviour: parser values, loader merge, configuration capture, resolution, constraints |
| `component` | a produced document is the unit: the exported SysML text is compared as a whole |
| `contract` | two directions agree: export then reload, constraint capture then evaluation |
| `system` | the public API is driven as a consumer would, from the installed package |
| `slow` | not part of the default CI subset: whole-tree sweeps and build checks |

**Level map.** `tests/conftest.py` holds `FILE_LEVELS`, a file-to-markers map.
`pytest_collection_modifyitems` applies those markers and stashes the per-node
map in `COLLECTED_LEVELS`. `tests/test_layering.py` fails when a collected test
carries no level or a level the map does not declare, so a new test file cannot
arrive undeclared. `slow` never appears in the map: it is a time marker applied
to individual tests.

**Gate.** CI runs `ruff check src tests`, then `python -m pytest -m "not slow"`
on Python 3.11 and 3.12, and fails if the run leaves the checkout dirty. A bare
`python -m pytest` runs the whole set, `slow` included.

**House style.** A document of 15 or more lines is a fixture file, never a
literal; a case stays in the test. Assertions read as behaviour, and a whole
document is compared only when the document is the contract.
