"""Parameter dialect, and the policy that gives it its vocabulary.

The dialect helpers live one module per layer under
``pycps_sysml2.parameters.dialect``: ``markers``, ``declarations``,
``composition``, and ``mapping``. Callers may import from the precise layer, or
from this package for the documented surface below. Variation resolution,
configuration derivation, analysis plans, and constraint evaluation are the
sibling modules re-exported here with the dialect API.

Every entry point that needs to know what a model or an analysis is takes a
:class:`~pycps_sysml2.parameters.policy.DialectPolicy`. ``SSP_POLICY`` is the
SSP answer; a different consumer constructs its own.
"""

from pycps_sysml2.parameters.configuration import (
    configuration_name,
    derived_selection,
    model_root,
    scope_analysis_to_root,
)
from pycps_sysml2.parameters.constraints import (
    ConstraintReport,
    ConstraintResult,
    ConstraintViolation,
    enforce_constraints,
    evaluate,
)
from pycps_sysml2.parameters.dialect.composition import (
    AppliedSet,
    ComponentRef,
    MappingSpec,
    ParameterBind,
    applied_sets,
    component_definitions,
    component_refs,
    has_parameter_dialect,
    parameter_bind,
    set_usages,
    validate_parameter_dialect,
)
from pycps_sysml2.parameters.dialect.declarations import (
    ParameterItem,
    coerce_parameter_value,
    fixed_count,
    parameter_declarations,
    parameter_interface,
    parameter_items,
    parameter_port,
)
from pycps_sysml2.parameters.dialect.mapping import (
    mapping_entries,
    mapping_specs,
    parameter_sets_for_generation,
    validate_applied_sets,
)
from pycps_sysml2.parameters.dialect.markers import (
    PARAMETER_INTERFACE_MARKER,
    PARAMETER_SET_MARKER,
    PARAMETERS_PORT_NAME,
    is_parameter_interface,
    is_parameter_set,
    validate_marker_definitions,
)
from pycps_sysml2.parameters.policy import SSP_POLICY, DialectPolicy
from pycps_sysml2.parameters.selection import (
    AnalysisPlan,
    analysis_plans,
    analysis_selection,
    analysis_selections,
    parse_selection,
)
from pycps_sysml2.parameters.variation import (
    has_variation,
    refuse_variation_erasure,
    require_resolved_attribute_variation,
    resolve,
    resolve_selected,
)

__all__ = [
    "AnalysisPlan",
    "AppliedSet",
    "ComponentRef",
    "ConstraintReport",
    "ConstraintResult",
    "ConstraintViolation",
    "DialectPolicy",
    "MappingSpec",
    "PARAMETER_INTERFACE_MARKER",
    "PARAMETER_SET_MARKER",
    "PARAMETERS_PORT_NAME",
    "ParameterBind",
    "ParameterItem",
    "SSP_POLICY",
    "analysis_plans",
    "analysis_selection",
    "analysis_selections",
    "applied_sets",
    "coerce_parameter_value",
    "component_definitions",
    "component_refs",
    "configuration_name",
    "derived_selection",
    "enforce_constraints",
    "evaluate",
    "fixed_count",
    "has_parameter_dialect",
    "has_variation",
    "is_parameter_interface",
    "is_parameter_set",
    "mapping_entries",
    "mapping_specs",
    "model_root",
    "parameter_bind",
    "parameter_declarations",
    "parameter_interface",
    "parameter_items",
    "parameter_port",
    "parameter_sets_for_generation",
    "parse_selection",
    "refuse_variation_erasure",
    "require_resolved_attribute_variation",
    "resolve",
    "resolve_selected",
    "scope_analysis_to_root",
    "set_usages",
    "validate_applied_sets",
    "validate_marker_definitions",
    "validate_parameter_dialect",
]
