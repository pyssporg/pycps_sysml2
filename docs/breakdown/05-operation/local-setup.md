---
id: INFO-008
type: info
title: Local setup
summary: The venv, the dev extra, the runtime pin, and the commands that must pass before a change lands.
date: 2026-11-05
status: current
---

# Local setup

Python 3.10 or newer; CI covers 3.11 and 3.12. Work in a repository-local venv.

```bash
python3 -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
python -c "import pycps_sysml2; print(pycps_sysml2.__version__)"
```

The `dev` extra is `pytest`, `ruff`, and `build`; the only runtime dependency is
the hard `sysmlpy==0.96.4` pin (INFO-006). The install provides no console
script: v0.1.0 ships the Python API only.

Before a change lands:

```bash
ruff check src tests
python -m pytest -m "not slow"
python -m build            # wheel + sdist, optional but cheap
```

Documentation checks use the product-breakdown tool with an explicit root:
`python3 <pb> check --strict --root docs/breakdown`,
`python3 <pb> node-size --strict --root docs/breakdown`, and
`python3 <pb> registers --root docs/breakdown` after any leaf edit.
