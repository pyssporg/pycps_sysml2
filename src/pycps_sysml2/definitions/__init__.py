"""Shared SysML core definitions shipped as package data.

The dialect markers are ordinary SysML definitions. Shipping them with the
package lets a model opt into the shared vocabulary instead of redeclaring
``SspModel``, ``FmuMetadata``, and the parameter markers in every fixture.
"""

from __future__ import annotations

from importlib import resources
from pathlib import Path

__all__ = ["CORE_FILE", "core_definitions"]

_PACKAGE = "pycps_sysml2"

#: Path of the core definitions inside the package.
CORE_FILE = "definitions/core.sysml"


def core_definitions() -> Path:
    """Return the bundled core definitions as a real file path.

    The file is package data. An unpacked install (editable checkout or wheel)
    yields a real ``Path``; a zipped install cannot expose one and is refused
    rather than handing a non-path to the loader.

    Returns:
        The ``definitions/core.sysml`` path.

    Raises:
        RuntimeError: The package is not installed as an unpacked directory.
        FileNotFoundError: The bundled core definitions file is absent.
    """
    path = resources.files(_PACKAGE).joinpath(CORE_FILE)
    if not isinstance(path, Path):
        raise RuntimeError(
            "pycps_sysml2 must be installed as an unpacked directory so the "
            "bundled core definitions have a real file path"
        )
    if not path.is_file():
        raise FileNotFoundError(
            f"no core definitions found at {path}; reinstall pycps_sysml2"
        )
    return path
