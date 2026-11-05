# AGENTS

## Vision first (required)

Before you read code, edit files, or plan a change, read the project vision:

**`docs/breakdown/00-intent/intent.md`**

It states why this repository exists, what it commits to, and what it refuses to
become. It is the first document to read, not a reference of last resort.

- Read it in full before making any change to code, tests, docs, or artifacts.
- Judge every proposed change against it. If a change conflicts with the vision,
  its commitments, goals, or non-goals, stop and surface the conflict; do not
  implement it silently.
- If the work shows the long-term direction is wrong, change the vision
  deliberately first, then the code. Never let the repository drift away from
  its stated intent.

## Rules

1. **Don't assume. Surface tradeoffs.** If a contract is ambiguous, stop and say
   so rather than picking a behaviour silently.
2. **Minimum code that solves the problem.** Nothing speculative.
3. **Touch only what you must.** Clean up only your own mess.
4. **Define success criteria and verify.**

## Repository Focus

`pycps_sysml2` is the single home of our SysML dialect: parsing, the IR,
variation, selection, constraints, and every marker and metadata accessor for
the SSP and the FMI dialects. `pyssp_sysml2` and `pyfmi_sysml2` implement the
dialect; they consume this library and emit artifacts. This repository emits
none.

- Current state, the dialect inventory, and the layering rule live in
  `docs/breakdown/`; the code is the source of truth when the two disagree.
- Dated decisions live in `docs/archive/archive.zip`, read with `pb archive`.

## Hard constraints

- **One dialect owner.** A marker, attribute name, or resolution rule exists
  here once. An implementer selects a domain with `RolePolicy`,
  `DialectPolicy`, or `ControlAttributes`; it never re-declares a marker.
- **No `pyssp_standard`, direct or transitive.** It carries artifact objects,
  which this library does not know about. `pyssp_sysml2` and `pyfmi_sysml2` are
  never imported either.
- **The layering rule.** `model` ← `core` ← `metadata` ← `parameters`;
  `parameters/dialect` above `metadata`. Nothing below `parameters` imports
  `parameters`, and no module below `metadata` imports a marker constant or
  calls `is_ssp_model`/`is_analysis`.
- **The parser boundary.** Only `model/parser.py` imports `sysmlpy`; only
  `model/variation.py` walks the raw ANTLR tree. The IR is repo-owned.
- **The pin is hard.** `sysmlpy==0.96.4`, exact. A bump is a dialect decision
  that lands with a record and a test.
- **No artifact path in `src/`.** `.ssd`, `.ssv`, `.ssm`, `.ssp`, `.fmu`, and
  `resources/` belong to the implementers.
- **Fixtures are evidence.** Every fixture directory has a `case.md` listing its
  files; a document of 15 or more lines is a file, never a test literal.

## Code guidelines

- Keep changes direct and explicit. Minimize duplication, but do not hide the
  dialect behind abstractions.
- Public entry points take their policy keyword-only and required; private
  helpers take it positionally and forward it. No default domain.
- Keep error messages naming the member, its owner, and the path involved.
- Treat interfaces as pre-1.0: clarity outranks compatibility shims.

## Conventions

- `README.md` is the landing page; `docs/breakdown/` holds current state.
- `docs/breakdown/` follows the product-breakdown skill. Set
  `PB=<skills-dir>/product-breakdown/scripts/pb` and pass
  `--root docs/breakdown` to every command:
  - current state lives in layer leaves, in the present tense;
  - dated decisions live in `docs/archive/archive.zip` (`pb archive list`,
    `pb archive read <ID>`, `pb archive add <FILE>`);
  - never add per-layer `decisions/` folders or hand-maintain decision logs;
  - regenerate `docs/archive/README.md`, `design-choice-log.md`, and
    `traceability-map.md` with `python3 $PB registers --root docs/breakdown`;
    never edit them by hand;
  - run `python3 $PB check --strict --root docs/breakdown` and
    `python3 $PB node-size --strict --root docs/breakdown` after edits.
- Version lives in `src/pycps_sysml2/__init__.py` only; `pyproject.toml` is
  dynamic and has no `[project].version`.

## Environment

- Python >= 3.10; CI runs 3.11 and 3.12.
- `python3 -m venv venv`, `source venv/bin/activate`,
  `pip install -e ".[dev]"`.
- Tests: `python3 -m pytest -m "not slow"` (the CI gate); a bare
  `python3 -m pytest` includes the slow set.
- Lint: `ruff check src tests`.
- Build: `python -m build --wheel --sdist`.
