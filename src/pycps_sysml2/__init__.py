"""The SysML dialect layer for CPS artifacts.

The public surface is the repo-owned architecture model plus the loader:
parsing sits behind :mod:`pycps_sysml2.model`, so callers never see parser
objects. The domain subpackages are bound here so that ``import pycps_sysml2``
gives one object to reach the dialect from:

- :mod:`pycps_sysml2.core` — control attributes and FMI type helpers;
- :mod:`pycps_sysml2.metadata` — role and typed-metadata accessors;
- :mod:`pycps_sysml2.parameters` — variation, selection, constraints, dialect.
"""

from pycps_sysml2.model import (
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
    load,
)

__version__ = "0.1.0"

# Bound after the model so a subpackage that reads model types cannot re-enter
# a half-initialised root module.
from pycps_sysml2 import core, metadata, parameters  # noqa: E402

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
    "__version__",
    "core",
    "endpoint_text",
    "load",
    "metadata",
    "parameters",
]
