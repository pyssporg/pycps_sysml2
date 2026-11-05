"""Metadata dialects read from the model: FMU, SSP, and role markers.

Two kinds of thing live here. The role vocabulary answers *what a definition is
for* (an exportable model, an analysis, an experiment). The typed-metadata
dialects answer *what a definition says about an artifact* (an FMU source and
its implementation, an SSP-backed body). Both are read by type, never by usage
name, and neither writes an artifact.
"""

from pycps_sysml2.metadata.fmu_metadata import (
    FMU_METADATA_ATTR,
    FMU_METADATA_FIELDS,
    FMU_METADATA_MARKER,
    FmuMetadata,
    add_fmu_metadata,
    component_implementation,
    component_source,
    ensure_fmu_metadata_definition,
    fmu_metadata,
    is_fmu_metadata_definition,
    update_fmu_metadata_from_component,
    validate_retired_control_attributes,
)
from pycps_sysml2.metadata.roles import (
    ANALYSIS_MARKER,
    EXPERIMENT_FIELDS,
    EXPERIMENT_MARKER,
    SSP_MODEL_MARKER,
    SSP_ROLES,
    Experiment,
    RolePolicy,
    analysis_part_definitions,
    experiment_attribute,
    exportable_part_definitions,
    is_analysis,
    is_experiment_definition,
    is_ssp_model,
    model_usage,
    read_experiment,
    require_resolved_variation,
    validate_role_markers,
)
from pycps_sysml2.metadata.ssp_metadata import (
    SSP_METADATA_ATTR,
    SSP_METADATA_FIELDS,
    SSP_METADATA_MARKER,
    SspMetadata,
    is_ssp_metadata_definition,
    ssp_metadata,
)

__all__ = [
    "ANALYSIS_MARKER",
    "EXPERIMENT_FIELDS",
    "EXPERIMENT_MARKER",
    "FMU_METADATA_ATTR",
    "FMU_METADATA_FIELDS",
    "FMU_METADATA_MARKER",
    "FmuMetadata",
    "RolePolicy",
    "SSP_METADATA_ATTR",
    "SSP_METADATA_FIELDS",
    "SSP_METADATA_MARKER",
    "SSP_MODEL_MARKER",
    "SSP_ROLES",
    "SspMetadata",
    "Experiment",
    "add_fmu_metadata",
    "analysis_part_definitions",
    "component_implementation",
    "component_source",
    "ensure_fmu_metadata_definition",
    "experiment_attribute",
    "exportable_part_definitions",
    "fmu_metadata",
    "is_analysis",
    "is_experiment_definition",
    "is_fmu_metadata_definition",
    "is_ssp_metadata_definition",
    "is_ssp_model",
    "model_usage",
    "read_experiment",
    "require_resolved_variation",
    "ssp_metadata",
    "update_fmu_metadata_from_component",
    "validate_retired_control_attributes",
    "validate_role_markers",
]
