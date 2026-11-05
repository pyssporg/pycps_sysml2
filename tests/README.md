# Tests

Two rules decide where a test belongs and what its green means.

- **Path = case.** A test file is named for the thing it is evidence about, and
  the fixture it needs lives beside it under `tests/fixtures/<subject>/`.
- **Marker = level.** The level says what a passing run proves, not how long the
  test takes. The level is declared once per file in `FILE_LEVELS`
  (`tests/conftest.py`) and applied at collection, so a new test file cannot
  arrive without one: `test_layering.py` fails until the file is listed.

## Levels

| Marker | A green run proves | Command |
| --- | --- | --- |
| `static` | source or files were inspected; the package was not executed | `python -m pytest -m static` |
| `unit` | one object behaves; no generated artifact involved | `python -m pytest -m unit` |
| `component` | a generated artifact (SysML text or a built document) is the unit under test | `python -m pytest -m component` |
| `contract` | two directions agree (round-trip, sync) | `python -m pytest -m contract` |
| `system` | an installed entry point was driven end to end | `python -m pytest -m system` |
| `slow` | excluded from the default CI subset, run on purpose | `python -m pytest -m slow` |

`python -m pytest` runs everything; CI runs `python -m pytest -m "not slow"`.
A file whose tests span two levels is listed with both markers and must appear
in `MIXED_FILES`; no other combination is accepted. A file that is not listed at
all falls back to `unit`, so a new test file still gets a level before it is
reviewed.

## Where the evidence lives

- `tests/fixtures/<subject>/` — SysML documents used as test data: one native
  file per case, plus a `case.md` naming every file and recording where it came
  from. Load with `tests/fixture_files.py` (`fixture_text`, `render_fixture`,
  `assert_matches_fixture`). Paths resolve from the module, never the cwd.
- `tests/fixture_files.py` — fixture path resolution and text comparison.
- `tests/fixture_guard.py` — session guard, see below.
- `tests/testhelpers.py` — `write_model` (strip and one trailing newline).
- `tests/test_sysml_model.py` — loader and exporter: one file per case, the
  directory merge rules, every captured field, and the export round trip.
- `tests/test_control_attributes.py` — the injectable control-attribute
  vocabulary: default prefix, custom prefix, retired names, injected map.
- `tests/test_layering.py` — no upstream package imports in `src/`, one version
  source, one level marker per test.
- `tests/test_module_layout.py` — package root and subpackage layout, `sysmlpy`
  confined to `model/parser.py`, large-module allow-list.
- `tests/test_fixture_policy.py` — static policy over the fixture tree: every
  directory has a `case.md`, every record carries the required headings and
  names every fixture file, no test module embeds a document of 15+ lines, and
  no fixture is read through the cwd.

## Adding a fixture case

1. Create `tests/fixtures/<subject>/` and add the `.sysml` document(s).
2. Add `case.md` with `# Case:`, `## Artifacts`, `## What this case proves`,
   `## Update history`, and a `## Provenance` line naming the source and commit
   when the document was copied from another repository.
3. Name every data file in the record, by relative path in backticks.
4. Read it with `fixture_text("<subject>/<file>.sysml")` and write it into
   `tmp_path` with `write_model`; tests never read or write the fixture itself.
5. `python -m pytest -m static` proves the record is complete.

## The fixture-write guard

`tests/fixture_guard.py` hashes every file under `tests/fixtures` at session
start and re-hashes it at session finish (`pytest_sessionstart` /
`pytest_sessionfinish` in `conftest.py`). A test that adds, removes, or rewrites
a committed fixture fails the session and the changed paths are printed, even
when every assertion passed. Bytecode caches (`__pycache__`, `*.pyc`) are
ignored.

A run that legitimately writes fixtures (`UPDATE_FIXTURES=1`) skips the guard.
If you find yourself wanting to disable it for anything else, the test is
probably asserting on evidence it just created; give it `tmp_path` instead.
