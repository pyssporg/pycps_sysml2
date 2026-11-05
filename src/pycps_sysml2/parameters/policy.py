"""The dialect policy a consumer injects into the parameter layer.

The parameter *syntax* is domain-neutral; the *meaning* of a few attributes is
not. A composition may carry control attributes, FMU metadata, SSP metadata, or
nothing at all, and only the consumer knows which vocabulary it uses. This
module names that vocabulary once and binds the SSP answer in :data:`SSP_POLICY`.

There is deliberately no generic default. A test or an FMI-only consumer builds
a :class:`DialectPolicy` explicitly, because implicit domain-neutral behaviour
would silently accept attributes the caller never agreed to.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from pycps_sysml2.core.control import CONTROL, ControlAttributes
from pycps_sysml2.metadata.fmu_metadata import (
    FMU_METADATA_ATTR,
    fmu_metadata,
    is_fmu_metadata_definition,
)
from pycps_sysml2.metadata.roles import SSP_ROLES, RolePolicy
from pycps_sysml2.metadata.ssp_metadata import (
    is_ssp_metadata_definition,
    ssp_metadata,
)
from pycps_sysml2.model import Architecture, AttributeDefinition, PartDefinition


@dataclass(frozen=True)
class DialectPolicy:
    """Everything the composition layer must not hard-code.

    ``roles`` supplies the model/analysis predicates, ``control`` the
    control-attribute vocabulary, and the metadata pairs say which attributes
    are typed metadata (and which resolver records them).

    ``reject_retired_attributes`` gates the retired-control-attribute rule;
    ``reject_flat_connectors`` gates the rule that rejects a parameter declared
    as a flat part attribute (the dialect that would be emitted as a flat
    connector). Both are migration rules, so a consumer that still carries the
    older shapes turns them off explicitly; :data:`SSP_POLICY` has both on.
    """

    roles: RolePolicy = SSP_ROLES
    control: ControlAttributes = CONTROL
    reject_retired_attributes: bool = True
    reject_flat_connectors: bool = True
    is_ssp_metadata: Callable[
        [Architecture, AttributeDefinition | None], bool
    ] = is_ssp_metadata_definition
    record_ssp_metadata: Callable[[Architecture, PartDefinition], None] = ssp_metadata
    is_fmu_metadata: Callable[
        [Architecture, AttributeDefinition | None], bool
    ] = is_fmu_metadata_definition
    record_fmu_metadata: Callable[[Architecture, PartDefinition], None] = fmu_metadata
    #: Usage name that must be typed by an FMU metadata definition when it
    #: appears; ``None`` when the dialect has no such reserved name.
    fmu_metadata_attr: str | None = FMU_METADATA_ATTR


#: The SSP vocabulary: ``SspModel``/``Analysis`` roles, ``pyssp_*`` controls,
#: FMU and SSP typed metadata, and both migration rules enforced.
SSP_POLICY = DialectPolicy()
