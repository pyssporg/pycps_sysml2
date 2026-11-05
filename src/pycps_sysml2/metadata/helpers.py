"""Marker and member resolution shared by every metadata dialect.

Two marker questions exist and they are not the same question:

- the parameter dialect asks whether a definition *directly* writes a marker in
  its ``:>`` list, and deliberately does not treat the marker definition itself
  as an instance of the marker (:func:`specializes_marker`);
- the role and typed-metadata dialects ask whether a definition *is* the marker
  or reaches it through any chain of supertypes, including the marker
  definition itself (:func:`specializes_marker_deep`).

Keeping both here means one implementation and one place to reason about the
namespace: a ``PartDefinition`` resolves supertypes through
``architecture.part_definitions``, everything else through
``architecture.attribute_definitions``.
"""

from __future__ import annotations

from pycps_sysml2.model import (
    Architecture,
    Attribute,
    AttributeDefinition,
    Definition,
    PartDefinition,
)


def short_name(name: str) -> str:
    """Last segment of a possibly qualified SysML name."""
    return name.split("::")[-1]


def specializes_marker(definition: Definition | None, marker: str) -> bool:
    """True when ``definition`` writes ``marker`` in its own ``:>`` list.

    Direct only, and the definition's own name is never inspected, so the
    marker definition is not an instance of itself:
    ``is_parameter_set(ParameterSet_marker_definition)`` stays ``False``.
    """
    if definition is None:
        return False
    return any(short_name(name) == marker for name in definition.specializes)


def specializes_marker_deep(
    architecture: Architecture,
    definition: PartDefinition | AttributeDefinition | None,
    marker: str,
    *,
    seen: set[str] | None = None,
) -> bool:
    """True when ``definition`` is ``marker`` or specializes it transitively.

    Unlike :func:`specializes_marker` this matches the definition's own short
    name, so ``is_ssp_model(SspModel_marker_definition)`` stays ``True``.
    """
    if definition is None:
        return False
    if short_name(definition.name) == marker:
        return True
    seen = set() if seen is None else seen
    if definition.name in seen:
        return False
    seen.add(definition.name)
    for supertype in definition.specializes:
        if short_name(supertype) == marker:
            return True
        if isinstance(definition, PartDefinition):
            base = architecture.part_definitions.get(short_name(supertype))
        else:
            base = architecture.attribute_definitions.get(short_name(supertype))
        if specializes_marker_deep(architecture, base, marker, seen=seen):
            return True
    return False


def effective_members(
    architecture: Architecture,
    definition: AttributeDefinition,
    *,
    seen: set[str] | None = None,
) -> dict[str, Attribute]:
    """Direct members plus inherited members; inherited values win by name.

    A derived member with no value of its own keeps the inherited value instead
    of shadowing it with ``None``.
    """
    seen = set() if seen is None else seen
    if definition.name in seen:
        return {}
    seen.add(definition.name)

    members: dict[str, Attribute] = {}
    for supertype in definition.specializes:
        base = architecture.attribute_definitions.get(short_name(supertype))
        if base is not None:
            members.update(effective_members(architecture, base, seen=seen))
    for name, attribute in definition.attributes.items():
        inherited = members.get(name)
        if (
            attribute.value is None
            and inherited is not None
            and inherited.value is not None
        ):
            members[name] = inherited
        else:
            members[name] = attribute
    return members
