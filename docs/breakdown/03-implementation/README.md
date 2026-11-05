---
title: Implementation
summary: Modules, the parser boundary, and the pinned grammar.
---

# Implementation

The module map, the parser, and the concrete dependency the parser is built on.

## Contents

<!-- pb:index:start -->
<!-- GENERATED FILE — do not edit. Regenerate with pb-registers. -->
- **INFO-004** [Module map](module-map.md) — Every module's responsibility and the imports the layering rule allows it.
- **INFO-005** [Parser](parser.md) — What model/parser.py turns a file into, what it normalizes, and what it refuses to guess.
- **INFO-006** [sysmlpy pin](sysmlpy-pin.md) — The hard grammar pin, the private structures the parser depends on, and the rule for moving it.
- **INFO-010** [Extraction record](migration-notes.md) — What v0.1.0 took from pyssp_sysml2 v0.3.0, and what it left behind.
- **INFO-012** [Core definitions](core-definitions.md) — The dialect markers and metadata schemas ship once as package data; a model loads that file as one include root and never redeclares one.
<!-- pb:index:end -->
