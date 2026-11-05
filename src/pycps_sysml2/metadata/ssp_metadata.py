"""Typed SSP-source metadata carried by an ``SspModel`` definition.

The dialect mirrors ``FmuMetadata``::

    attribute def SspMetadata {
      attribute source : String;
    }

    attribute def LegacySsp :> SspMetadata {
      attribute source = "models/ssp/dcmotor/ssp";
    }

    part def DcMotorModel :> SspModel {
      attribute ssp_meta : LegacySsp;
    }

Metadata is recognized by **type**, not by the usage name: the part attribute
must be typed by an ``attribute def`` that specializes ``SspMetadata``. At most
one such attribute is allowed per definition, and only on an ``SspModel``.

``source`` names a directory containing ``SystemStructure.ssd`` and optional
``resources/``. The build stage resolves it against the repository root. A
composition that carries this metadata is an analysis-only boundary: its body is
the checked-in SSP, not an export from SysML.
"""

from __future__ import annotations

from dataclasses import dataclass

from pycps_sysml2.metadata.helpers import (
    effective_members,
    short_name,
    specializes_marker_deep,
)
from pycps_sysml2.metadata.roles import is_ssp_model
from pycps_sysml2.model import (
    Architecture,
    Attribute,
    AttributeDefinition,
    PartDefinition,
)

SSP_METADATA_ATTR = "ssp_meta"
SSP_METADATA_MARKER = "SspMetadata"
SSP_METADATA_FIELDS = ("source",)


@dataclass(frozen=True)
class SspMetadata:
    """Effective metadata values for one SSP-backed composition."""

    source: str | None = None


def is_ssp_metadata_definition(
    architecture: Architecture, definition: AttributeDefinition | None
) -> bool:
    """True when ``definition`` is the marker or specializes it transitively."""
    return specializes_marker_deep(architecture, definition, SSP_METADATA_MARKER)


def _metadata_usage(
    architecture: Architecture, part_def: PartDefinition
) -> tuple[str, Attribute, AttributeDefinition] | None:
    found: list[tuple[str, Attribute, AttributeDefinition]] = []
    for name, attribute in part_def.attributes.items():
        definition = architecture.resolve_attribute_def(attribute)
        if is_ssp_metadata_definition(architecture, definition):
            assert definition is not None
            found.append((name, attribute, definition))

    if len(found) > 1:
        names = ", ".join(sorted(name for name, _, _ in found))
        raise ValueError(
            f"{part_def.name} declares multiple SSP metadata attributes "
            f"({names}); use one"
        )
    if found:
        name, attribute, definition = found[0]
        if short_name(definition.name) == SSP_METADATA_MARKER:
            raise ValueError(
                f"{part_def.name}.{name} is typed by the '{SSP_METADATA_MARKER}' "
                "schema directly; use a concrete 'attribute def <Part>SspMetadata "
                f":> {SSP_METADATA_MARKER} {{ ... }}' instead"
            )
        return name, attribute, definition

    if SSP_METADATA_ATTR in part_def.attributes:
        raise ValueError(
            f"{part_def.name}.{SSP_METADATA_ATTR} must be typed by an "
            f"attribute def marked ':> {SSP_METADATA_MARKER}'"
        )
    return None


def _string_member(name: str, attribute: Attribute | None) -> str | None:
    if attribute is None or attribute.value is None:
        return None
    value = attribute.value
    if not isinstance(value, str) or attribute.primitive_type_str() != "String":
        actual = attribute.primitive_type_str()
        raise ValueError(
            f"SSP metadata member '{name}' must be a String, got {actual}"
        )
    return value


def ssp_metadata(
    architecture: Architecture, part_def: PartDefinition
) -> SspMetadata | None:
    """Resolve effective SSP-source metadata for ``part_def``, or ``None``."""
    usage = _metadata_usage(architecture, part_def)
    if usage is None:
        return None

    name, _attribute, definition = usage
    if not is_ssp_model(architecture, part_def):
        raise ValueError(
            f"{part_def.name}.{name} is SSP metadata, but "
            f"'{part_def.name}' is not marked ':> SspModel'"
        )

    marker = architecture.attribute_definitions.get(SSP_METADATA_MARKER)
    if marker is None:
        raise ValueError(
            f"SSP metadata uses missing marker definition '{SSP_METADATA_MARKER}'. "
            f"Add 'attribute def {SSP_METADATA_MARKER} {{ attribute source : "
            "String; }}' to the package."
        )

    members = effective_members(architecture, definition)
    unknown = sorted(set(members) - set(SSP_METADATA_FIELDS))
    if unknown:
        raise ValueError(
            f"SSP metadata definition '{definition.name}' declares unsupported "
            f"member(s): {', '.join(unknown)}; allowed members are "
            f"{', '.join(SSP_METADATA_FIELDS)}"
        )

    return SspMetadata(source=_string_member("source", members.get("source")))
