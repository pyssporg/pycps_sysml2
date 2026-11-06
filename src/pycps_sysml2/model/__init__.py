"""SysML v2 model adapter for pycps_sysml2.

Anti-corruption layer over the external `sysmlpy` parser:

- ``model.py``    — the repo-owned dataclasses every generator works against.
- ``parser.py``   — the ONLY module that imports ``sysmlpy``; parses one
  file's packages and exposes the grammar-layer walks.
- ``variation.py``— captures variation points from the raw parse tree, which
  ``sysmlpy`` drops from its wrapper objects.
- ``loader.py``   — walks a file or directory, merges the packages, and
  builds the repo-owned model.
- ``attribution.py`` — the per-file scan that ties each merged definition
  back to the file that declared it.
- ``exporter.py`` — emits conformant SysML v2 text from the repo-owned model
  (no parser involvement, so the output format is a repo contract).

If sysmlpy's API changes, only ``parser.py`` needs fixes.
"""

from collections.abc import Sequence
from pathlib import Path

from pycps_sysml2.model.model import (
    Architecture,
    Attribute,
    AttributeDefinition,
    Binding,
    Connection,
    ConstraintDefinition,
    ConstraintParameter,
    ConstraintUsage,
    Definition,
    PartDefinition,
    PartUsage,
    PortDefinition,
    PortUsage,
    RequirementDefinition,
    VariantBody,
    VariantMember,
    endpoint_text,
)

__all__ = [
    "Architecture",
    "Attribute",
    "AttributeDefinition",
    "Binding",
    "Connection",
    "ConstraintDefinition",
    "ConstraintParameter",
    "ConstraintUsage",
    "Definition",
    "PartDefinition",
    "PartUsage",
    "PortDefinition",
    "PortUsage",
    "RequirementDefinition",
    "VariantBody",
    "VariantMember",
    "endpoint_text",
    "load",
]


def load(
    path: Path | str | Sequence[Path | str],
    *includes: Path | str,
) -> Architecture:
    """Load a primary architecture root plus any number of included roots.

    ``path`` is one root or a sequence whose first element is the primary model
    root; further elements and ``*includes`` are included roots. See
    :func:`pycps_sysml2.model.loader.load`. Implemented in
    :mod:`pycps_sysml2.model.loader`.
    """
    from pycps_sysml2.model.loader import load as _load

    return _load(path, *includes)
