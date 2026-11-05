"""Control-attribute names shared by the SysML adapters.

Metadata that has no first-class SysML v2 equivalent is carried as ordinary
``pyssp_*`` attributes. Every generator skips them as model data. The names and
the recognition rule live in one tiny module so the model adapter, the parameter
layer, and the artifact synthesis layer do not need to import each other.

The module constants are the documented defaults. A consumer that owns a
different vocabulary constructs a :class:`ControlAttributes` with its own
prefix and retired map and passes it in; nothing reads the module globals on
that path.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Mapping

if TYPE_CHECKING:
    from pycps_sysml2.model import Architecture

CONTROL_PREFIX = "pyssp_"

# Removed control attributes. They still match the prefix, so generators would
# otherwise skip them silently; validation turns them into migration errors
# instead.
RETIRED_CONTROL_ATTRS: dict[str, str] = {
    f"{CONTROL_PREFIX}implementation": (
        "use 'attribute fmu_meta : <Part>FmuMetadata { attribute "
        "implementation = \"...\"; }'"
    ),
    f"{CONTROL_PREFIX}parameter_set": (
        "define an 'attribute def <Set> :> ParameterSet' and bind it to the "
        "component with 'bind'"
    ),
}


@dataclass(frozen=True)
class ControlAttributes:
    """The control-attribute vocabulary one consumer recognises."""

    prefix: str = CONTROL_PREFIX
    retired: Mapping[str, str] = field(
        default_factory=lambda: dict(RETIRED_CONTROL_ATTRS)
    )

    @property
    def default_start(self) -> str:
        return f"{self.prefix}default_start_time"

    @property
    def default_stop(self) -> str:
        return f"{self.prefix}default_stop_time"

    @property
    def flat_connector(self) -> str:
        return f"{self.prefix}flat_connector"

    def is_control(self, name: str) -> bool:
        return name.startswith(self.prefix)

    def is_retired(self, name: str) -> bool:
        return name in self.retired

    def validate(self, architecture: Architecture) -> None:
        """Reject attributes removed by the typed-metadata migration."""
        definitions = list(architecture.part_definitions.values()) + list(
            architecture.port_definitions.values()
        )
        for definition in definitions:
            for name in definition.attributes:
                message = self.retired.get(name)
                if message is not None:
                    raise ValueError(
                        f"{definition.name}.{name} is no longer supported; {message}"
                    )


#: The default vocabulary; every module constant below is derived from it.
CONTROL = ControlAttributes()
DEFAULT_START_ATTR = CONTROL.default_start
DEFAULT_STOP_ATTR = CONTROL.default_stop
FLAT_CONNECTOR_ATTR = CONTROL.flat_connector


def is_control_attribute(
    name: str, *, attributes: ControlAttributes = CONTROL
) -> bool:
    return attributes.is_control(name)


def is_retired_control_attribute(
    name: str, *, attributes: ControlAttributes = CONTROL
) -> bool:
    return attributes.is_retired(name)


def validate_retired_control_attributes(
    architecture: Architecture, *, attributes: ControlAttributes = CONTROL
) -> None:
    """Reject retired control attributes, using ``attributes``' retired map."""
    attributes.validate(architecture)
