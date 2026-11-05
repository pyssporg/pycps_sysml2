---
id: INFO-007
type: info
title: Release
summary: The exact tag, build, guard, and asset-URL sequence for a release, with one version source.
date: 2026-11-05
status: current
---

# Release

**One version source.** `src/pycps_sysml2/__init__.py` holds `__version__`.
`pyproject.toml` declares `dynamic = ["version"]` and maps
`version = { attr = "pycps_sysml2.__version__" }`; there is no
`[project].version`, so a release edits the package attribute only.

**Sequence.**

1. Set `__version__ = "0.1.0"` in `src/pycps_sysml2/__init__.py` and regenerate
   the registers if the version appears in prose.
2. Run the gate: `ruff check src tests`, `python -m pytest -m "not slow"`,
   `python -m build --wheel --sdist`.
3. Commit as `release: v0.1.0`, then `git tag v0.1.0` and
   `git push origin main --tags`.

**What the tag starts.** `.github/workflows/wheels.yml` builds
`python -m build --wheel --sdist` and guards, in order: exactly one wheel in
`dist/`; version not `0.0.0`; a fresh venv can install the wheel and import
`pycps_sysml2` and `sysmlpy`; and, on a tag, `${GITHUB_REF_NAME#v}` equals
`pycps_sysml2.__version__` read from `src`. A mismatched tag fails the job
before anything is attached. On success the workflow attaches every file in
`dist/` to the release.

**Asset URL.** The wheel lives at
`https://github.com/pyssporg/pycps_sysml2/releases/download/v<ver>/pycps_sysml2-<ver>-py3-none-any.whl`;
the tag carries the `v` and the version appears twice. Implementers pin that URL.

**Verification.** Install from the URL into a clean venv and print
`pycps_sysml2.__version__`; a failure means the tag and the package version
disagree or the wheel was never attached.
