# Product Breakdown — pycps_sysml2

Current-state record: why the dialect layer exists, what it promises, how it is
organized, and how it is verified and released.

## Layers

- `00-intent/` — why the project exists.
- `01-product/` — the promise to implementers.
- `02-architecture/` — dialect inventory and policy seam.
- `03-implementation/` — module map, parser, grammar pin.
- `04-verification/` — test levels and fixture policy.
- `05-operation/` — setup, commands, release.
- `06-evolution/` — next-minor scope.
- `../archive/archive.zip` — dated decisions, via `pb archive`.

## Boundary Rule

Read top-down. Current state lives in the leaves, in the present tense; history
lives in the archive; navigation is generated. Cite nodes by ID, never by path.
Evolution holds candidates only. Fixtures, build output, and generated archives
stay out: `tests/fixtures/`, `build/`.
