---
id: TEST-002
type: test
title: Fixture policy
summary: Which fixture directories this repo owns, why part of the set duplicates an implementer, and what every case.md records.
date: 2026-11-05
status: current
---

# Fixture policy

**Owned fixtures.** The generic documents are this repo's: `sysml-model/`,
`quoted-names/`, `arrays/`, `variation/`, `selection/`, `configuration/`,
`constraints/`, and the parameter dialect's `parameter-ports/`,
`parameter-bind-orientation/`, `parameter-sets/`. An SSP-output fixture never
lives here; it lives with the library that emits the artifact.

**Recorded duplication.** `variation/`, `selection/`, `quoted-names/`, and some
`parameter-*` documents exist in a second, edited copy in `pyssp_sysml2`, which
needs its own variants to drive SSD output. The duplication is deliberate and
bounded: the two repositories release independently, a shared fixture package
would couple their release trains, and a test that reads across repositories
cannot run from an installed wheel. A copy is added only with this reason, is
kept small, and changes on its own release schedule.

**Mandatory record.** Every fixture directory carries `case.md` with the
headings `# Case:`, `## Artifacts`, `## What this case proves`, and
`## Update history`, and a bullet block with one line each for `Conversion`,
`Requirement / fault`, `Level`, `Input`, `Expected`, `Independent oracle`,
`Comparison`, `Normalization`, `Volatile fields`, `Update policy`, and `Notes`.
Every data file of the directory is named in backticks in that record.

**Enforcement.** `tests/test_fixture_policy.py` fails a directory without a
record, a record that omits a file, a test module holding a document of 15 or
more lines, and a cwd-relative fixture path. `tests/fixture_guard.py` hashes the
committed tree before collection and fails the run if a test rewrote it.
