"""Variation-point capture and resolution on the repo-owned model.

Only the model-level half of the originating suite is ported: the loader's
variation facts and the resolver, with no artifact in the loop. Every entry
point receives the SSP role vocabulary explicitly.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from pycps_sysml2.metadata import SSP_ROLES
from pycps_sysml2.model import load
from pycps_sysml2.parameters.selection import parse_selection
from pycps_sysml2.parameters.variation import (
    has_variation,
    resolve,
    resolve_selected,
)
from tests.fixture_files import fixture_text
from tests.testhelpers import write_model


CONNECTION_VARIATION = fixture_text("variation/connection.sysml")


PARAMETER_BINDING_VARIATION = fixture_text("variation/parameter-binding.sysml")


NESTED_BODY_VARIATION = fixture_text("variation/nested-body.sysml")


DEFINITION_VARIATION = fixture_text("variation/definition.sysml")


DEFINITION_VARIATION_FMU = fixture_text("variation/definition-fmu.sysml")


USAGE_VARIATION = fixture_text("variation/usage.sysml")


BODY_VARIATION = fixture_text("variation/body.sysml")


NESTED_VARIATION = fixture_text("variation/nested.sysml")


AMBIGUOUS_NAMES = fixture_text("variation/ambiguous-names.sysml")


NO_VARIATION = fixture_text("variation/no-variation.sysml")


UNDECLARED_BODY_PORT = fixture_text("variation/undeclared-body-port.sysml")


THREE_LEVELS = fixture_text("variation/three-levels.sysml")


VALUED_BODY_ATTRIBUTE = fixture_text("variation/valued-body-attribute.sysml")


ATTRIBUTE_VARIATION = fixture_text("variation/attribute-variation.sysml")


ATTRIBUTE_SET_VARIATION = fixture_text("variation/attribute-set-variation.sysml")


UNTYPED_ATTRIBUTE_VARIANT = fixture_text("variation/untyped-attribute-variant.sysml")


AMBIGUOUS_NESTED = fixture_text("variation/ambiguous-nested.sysml")


RESOLUTION_ORDER = fixture_text("variation/resolution-order.sysml")


NESTED_UNDER_REPLACED = fixture_text("variation/nested-under-replaced.sysml")


NESTED_UNKNOWN = fixture_text("variation/nested-unknown.sysml")


BODY_CHECKS = fixture_text("variation/body-checks.sysml")


MEMBER_RULES = fixture_text("variation/member-rules.sysml")


CONFIG_BODY_UNNAMED_PART = fixture_text("variation/config-body-unnamed-part.sysml")


CONFIG_BODY_UNNAMED_ATTRIBUTE = fixture_text(
    "variation/config-body-unnamed-attribute.sysml"
)


CONFIG_BODY_UNSUPPORTED = fixture_text(
    "variation/config-body-unsupported-member.sysml"
)


VARIANT_BODY_UNNAMED_PART = fixture_text(
    "variation/variant-body-unnamed-part.sysml"
)


VARIANT_BODY_UNNAMED_ATTRIBUTE = fixture_text(
    "variation/variant-body-unnamed-attribute.sysml"
)


VARIANT_BODY_UNSUPPORTED = fixture_text(
    "variation/variant-body-unsupported-member.sysml"
)


def _load_architecture(tmp_path: Path, content: str):
    path = tmp_path / "architecture.sysml"
    write_model(path, content)
    return path, load(path)


def test_definition_variation_captures_variants(tmp_path: Path) -> None:
    """A variation definition keeps its flag and its variant members, not parts."""
    _, architecture = _load_architecture(tmp_path, DEFINITION_VARIATION)

    source_choice = architecture.part_definitions["SourceChoice"]
    assert source_choice.is_variation is True
    assert [
        (variant.name, variant.kind, variant.type_name)
        for variant in source_choice.variants
    ] == [
        ("stepImplementation", "part", "Step"),
        ("sineImplementation", "part", "Sine"),
    ]
    assert source_choice.parts == {}


def test_usage_level_variation_captures_variants(tmp_path: Path) -> None:
    """A ``variation part`` usage keeps its flag and its own variants."""
    _, architecture = _load_architecture(tmp_path, USAGE_VARIATION)

    system = architecture.part_definitions["System"]
    assert system.is_variation is False
    source = system.parts["source"]
    assert source.is_variation is True
    assert [(variant.name, variant.type_name) for variant in source.variants] == [
        ("stepSource", "Step"),
        ("sineSource", "Sine"),
    ]
    assert system.variants == []


def test_model_without_variation_stays_clean(tmp_path: Path) -> None:
    """An architecture with no variation construct reports no variation."""
    _, architecture = _load_architecture(tmp_path, NO_VARIATION)

    for definition in architecture.part_definitions.values():
        assert definition.is_variation is False
        assert definition.variants == []
        assert not any(usage.is_variation for usage in definition.parts.values())


def test_variant_member_with_a_body_loads(tmp_path: Path) -> None:
    """A variant with a body keeps its nested parts and connections."""
    _, architecture = _load_architecture(tmp_path, BODY_VARIATION)

    path_choice = architecture.part_definitions["PathChoice"]
    assert path_choice.is_variation is True
    assert [(variant.name, variant.type_name) for variant in path_choice.variants] == [
        ("directPath", None)
    ]
    body = path_choice.variants[0].body
    assert body is not None
    assert [(name, usage.type_name) for name, usage in body.parts.items()] == [
        ("gain", "Gain")
    ]
    assert [
        (
            conn.source_part,
            conn.source_port,
            conn.destination_part,
            conn.destination_port,
        )
        for conn in body.connections.values()
    ] == [(None, "u", "gain", "u"), ("gain", "y", None, "y")]
    assert path_choice.parts == {}


def test_resolve_substitutes_the_selected_variant(tmp_path: Path) -> None:
    """Resolution rewrites the usage type on a copy and keeps the usage name."""
    _, architecture = _load_architecture(tmp_path, DEFINITION_VARIATION_FMU)

    resolved = resolve(architecture, "System", {"source": "stepImplementation"}, roles=SSP_ROLES)

    assert resolved.part_definitions["System"].parts["source"].type_name == "Step"
    assert architecture.part_definitions["System"].parts["source"].type_name == (
        "SourceChoice"
    )
    assert list(resolved.part_definitions["System"].parts) == ["source", "gain"]


def test_resolve_rejects_an_unknown_key(tmp_path: Path) -> None:
    _, architecture = _load_architecture(tmp_path, DEFINITION_VARIATION_FMU)

    with pytest.raises(ValueError, match="Unknown selection key 'missing'"):
        resolve(architecture, "System", {"missing": "stepImplementation"}, roles=SSP_ROLES)


def test_resolve_accepts_a_dotted_path_for_nesting(tmp_path: Path) -> None:
    """A nested variation point is selected by its dotted usage path."""
    _, architecture = _load_architecture(tmp_path, NESTED_VARIATION)

    resolved = resolve(architecture, "System", {"inner.source": "a"}, roles=SSP_ROLES)

    assert resolved.part_definitions["Inner"].parts["source"].type_name == "A"


def test_resolve_rejects_an_ambiguous_bare_key(tmp_path: Path) -> None:
    _, architecture = _load_architecture(tmp_path, AMBIGUOUS_NAMES)

    with pytest.raises(
        ValueError,
        match="Selection key 'x' is ambiguous.*'x', 'inner.x'",
    ):
        resolve(architecture, "System", {"x": "anything"}, roles=SSP_ROLES)


def test_resolve_rejects_a_non_variation_usage(tmp_path: Path) -> None:
    _, architecture = _load_architecture(tmp_path, DEFINITION_VARIATION_FMU)

    with pytest.raises(
        ValueError,
        match="'gain', which is not a variation point",
    ):
        resolve(architecture, "System", {"gain": "stepImplementation"}, roles=SSP_ROLES)


def test_resolve_rejects_an_unknown_variant(tmp_path: Path) -> None:
    _, architecture = _load_architecture(tmp_path, DEFINITION_VARIATION_FMU)

    with pytest.raises(
        ValueError,
        match="Unknown variant 'nope' for variation point 'SourceChoice'",
    ):
        resolve(architecture, "System", {"source": "nope"}, roles=SSP_ROLES)


def test_resolve_rejects_an_unselected_variation_point(tmp_path: Path) -> None:
    _, architecture = _load_architecture(tmp_path, DEFINITION_VARIATION_FMU)

    with pytest.raises(
        ValueError,
        match="Variation point 'SourceChoice' at 'source'.*is not selected",
    ):
        resolve(architecture, "System", {}, roles=SSP_ROLES)


def test_resolve_substitutes_a_usage_level_variant(tmp_path: Path) -> None:
    """A usage-level point is selected by its usage path and keeps the name."""
    _, architecture = _load_architecture(tmp_path, USAGE_VARIATION)

    resolved = resolve(architecture, "System", {"source": "stepSource"}, roles=SSP_ROLES)

    source = resolved.part_definitions["System"].parts["source"]
    assert source.type_name == "Step"
    assert source.name == "source"
    assert source.is_variation is False


def test_resolve_synthesises_a_body_variant(tmp_path: Path) -> None:
    """A body variant becomes a definition carrying the point's ports."""
    _, architecture = _load_architecture(tmp_path, BODY_VARIATION)

    resolved = resolve(architecture, "System", {"path": "directPath"}, roles=SSP_ROLES)

    usage = resolved.part_definitions["System"].parts["path"]
    assert usage.type_name == "PathChoice__directPath"
    definition = resolved.part_definitions[usage.type_name]
    assert list(definition.ports) == ["u", "y"]
    assert list(definition.parts) == ["gain"]
    assert [conn.key for conn in definition.connections.values()] == [
        "u->gain.u",
        "gain.y->y",
    ]
    assert architecture.part_definitions["System"].parts["path"].type_name == (
        "PathChoice"
    )


def test_example_08_rejects_an_unselected_body_point(tmp_path: Path) -> None:
    _, architecture = _load_architecture(tmp_path, CONNECTION_VARIATION)

    with pytest.raises(
        ValueError,
        match="Variation point 'PathChoice' at 'path'.*is not selected",
    ):
        resolve(architecture, "System", {}, roles=SSP_ROLES)


def test_resolve_rejects_a_body_port_the_point_does_not_declare(
    tmp_path: Path,
) -> None:
    _, architecture = _load_architecture(tmp_path, UNDECLARED_BODY_PORT)

    with pytest.raises(
        ValueError,
        match="Variant 'directPath' of variation point 'PathChoice' connects to "
        "port 'missing', which the point does not declare",
    ):
        resolve(architecture, "System", {"path": "directPath"}, roles=SSP_ROLES)


def test_example_09_captures_body_attributes_and_bindings(tmp_path: Path) -> None:
    """Example 09: a statement body carries a set usage and its binds."""
    _, architecture = _load_architecture(tmp_path, PARAMETER_BINDING_VARIATION)

    usage = architecture.part_definitions["test_selected"].parts["parameters"]
    body = usage.variants[1].body
    assert body is not None
    assert list(body.attributes) == ["values"]
    assert body.attributes["values"].type_name == "LateStepValues"
    assert [binding.key for binding in body.bindings] == [
        "sut.step.parameters.height=values.height",
        "sut.step.parameters.offset=values.offset",
        "sut.step.parameters.startTime=values.startTime",
        "sut.gain.parameters.k=values.k",
    ]


def test_example_09_selected_body_merges_into_the_analysis(
    tmp_path: Path,
) -> None:
    """Selection adds the set usage and binds to the analysis, not a component."""
    _, architecture = _load_architecture(tmp_path, PARAMETER_BINDING_VARIATION)

    resolved = resolve(
        architecture, "test_selected", {"parameters": "lateStepBinding"}, roles=SSP_ROLES
    )
    analysis = resolved.part_definitions["test_selected"]
    assert "parameters" not in analysis.parts
    assert analysis.attributes["values"].type_name == "LateStepValues"
    assert [binding.key for binding in analysis.bindings] == [
        "sut.step.parameters.height=values.height",
        "sut.step.parameters.offset=values.offset",
        "sut.step.parameters.startTime=values.startTime",
        "sut.gain.parameters.k=values.k",
    ]
    assert architecture.part_definitions["test_selected"].bindings == []
    assert architecture.part_definitions["test_selected"].parts[
        "parameters"
    ].is_variation


def test_example_10_captures_the_inner_variation_usage(tmp_path: Path) -> None:
    """Example 10: a body's variation usage keeps its flag and its variants."""
    _, architecture = _load_architecture(tmp_path, NESTED_BODY_VARIATION)

    body = architecture.part_definitions["PathChoice"].variants[1].body
    assert body is not None
    stage = body.parts["stage"]
    assert stage.is_variation is True
    assert stage.type_name == "StageChoice"
    assert [(variant.name, variant.type_name) for variant in stage.variants] == [
        ("gainStage", "Gain"),
        ("attenuateStage", "Attenuate"),
    ]


def test_example_10_dotted_selection_resolves_both_points(
    tmp_path: Path,
) -> None:
    """The inner key extends the outer usage path with a dot."""
    path, architecture = _load_architecture(tmp_path, NESTED_BODY_VARIATION)

    resolved = resolve(
        architecture,
        "System",
        {"path": "nestedPath", "path.stage": "attenuateStage"}, roles=SSP_ROLES,
    )
    part = resolved.part_definitions["System"].parts["path"]
    assert part.type_name == "PathChoice__nestedPath"
    definition = resolved.part_definitions[part.type_name]
    assert list(definition.parts) == ["stage", "gain"]
    assert definition.parts["stage"].type_name == "Attenuate"


def test_example_10_unselected_inner_point_names_the_full_path(
    tmp_path: Path,
) -> None:
    """An inner point left unselected fails with its dotted path."""
    _, architecture = _load_architecture(tmp_path, NESTED_BODY_VARIATION)

    with pytest.raises(
        ValueError,
        match="Variation point 'StageChoice' at 'path.stage'.*is not selected",
    ):
        resolve(architecture, "System", {"path": "nestedPath"}, roles=SSP_ROLES)


def test_example_10_inner_key_needs_the_outer_body_first(
    tmp_path: Path,
) -> None:
    """Without the outer selection the inner usage does not exist yet."""
    _, architecture = _load_architecture(tmp_path, NESTED_BODY_VARIATION)

    with pytest.raises(ValueError, match="Unknown selection key 'path.stage'"):
        resolve(architecture, "System", {"path.stage": "attenuateStage"}, roles=SSP_ROLES)


def test_three_level_variation_is_rejected_not_flattened(tmp_path: Path) -> None:
    _, architecture = _load_architecture(tmp_path, THREE_LEVELS)

    with pytest.raises(
        ValueError,
        match="variation nested deeper than two levels is not supported",
    ):
        resolve(
            architecture,
            "System",
            {"path": "nestedPath", "path.stage": "deepStage"}, roles=SSP_ROLES,
        )


def test_variant_body_rejects_an_attribute_value_it_cannot_carry(
    tmp_path: Path,
) -> None:
    with pytest.raises(
        ValueError, match="body attributes carry a type only"
    ):
        _load_architecture(tmp_path, VALUED_BODY_ATTRIBUTE)


def test_parse_selections_rejects_a_malformed_value() -> None:
    with pytest.raises(ValueError, match="expected 'key=variant'"):
        parse_selection("source")


def test_has_variation_covers_definitions_usages_and_attributes(
    tmp_path: Path,
) -> None:
    _, definition = _load_architecture(tmp_path / "definition", DEFINITION_VARIATION)
    _, usage = _load_architecture(tmp_path / "usage", USAGE_VARIATION)
    _, attribute = _load_architecture(tmp_path / "attribute", ATTRIBUTE_VARIATION)
    _, clean = _load_architecture(tmp_path / "clean", NO_VARIATION)

    assert has_variation(definition) is True
    assert has_variation(usage) is True
    assert has_variation(attribute) is True
    assert has_variation(clean) is False


def test_attribute_variation_captures_variants(tmp_path: Path) -> None:
    """A variation attribute def keeps variant attribute members, not attributes."""
    _, architecture = _load_architecture(tmp_path, ATTRIBUTE_SET_VARIATION)

    choice = architecture.attribute_definitions["ScenarioChoice"]
    assert choice.is_variation is True
    assert [
        (variant.name, variant.kind, variant.type_name)
        for variant in choice.variants
    ] == [
        ("baseline", "attribute", "BaselineScenario"),
        ("lateStep", "attribute", "LateStepScenario"),
        ("highGain", "attribute", "HighGainScenario"),
    ]
    assert choice.attributes == {}


def test_resolve_substitutes_the_attribute_usage_type(tmp_path: Path) -> None:
    """Resolution rewrites the attribute usage type on a copy."""
    _, architecture = _load_architecture(tmp_path, ATTRIBUTE_SET_VARIATION)

    resolved = resolve(architecture, "test_selected_scenario", {"scenario": "baseline"}, roles=SSP_ROLES)

    assert (
        resolved.part_definitions["test_selected_scenario"]
        .attributes["scenario"]
        .type_name
    ) == "BaselineScenario"
    assert (
        architecture.part_definitions["test_selected_scenario"]
        .attributes["scenario"]
        .type_name
    ) == "ScenarioChoice"


def test_resolve_finds_an_analysis_attribute_from_the_model(tmp_path: Path) -> None:
    """A composing analysis's attribute usage is selectable when its model is resolved."""
    _, architecture = _load_architecture(tmp_path, ATTRIBUTE_SET_VARIATION)

    resolved = resolve(architecture, "System", {"scenario": "lateStep"}, roles=SSP_ROLES)

    assert (
        resolved.part_definitions["test_selected_scenario"]
        .attributes["scenario"]
        .type_name
    ) == "LateStepScenario"


@pytest.mark.parametrize(
    ("variant", "expected"),
    [
        ("baseline", "BaselineScenario"),
        ("lateStep", "LateStepScenario"),
        ("highGain", "HighGainScenario"),
    ],
)
def test_every_attribute_variant_resolves(
    tmp_path: Path, variant: str, expected: str
) -> None:
    _, architecture = _load_architecture(tmp_path, ATTRIBUTE_SET_VARIATION)

    resolved = resolve(architecture, "test_selected_scenario", {"scenario": variant}, roles=SSP_ROLES)

    assert (
        resolved.part_definitions["test_selected_scenario"]
        .attributes["scenario"]
        .type_name
    ) == expected


def test_resolve_rejects_an_unknown_attribute_key(tmp_path: Path) -> None:
    _, architecture = _load_architecture(tmp_path, ATTRIBUTE_SET_VARIATION)

    with pytest.raises(ValueError, match="Unknown selection key 'missing'"):
        resolve(architecture, "test_selected_scenario", {"missing": "baseline"}, roles=SSP_ROLES)


def test_resolve_rejects_a_non_variation_attribute_usage(tmp_path: Path) -> None:
    _, architecture = _load_architecture(tmp_path, ATTRIBUTE_SET_VARIATION)

    with pytest.raises(
        ValueError,
        match="names attribute usage 'experiment_baseline', which is not a "
        "variation point",
    ):
        resolve(
            architecture,
            "test_selected_scenario",
            {"experiment_baseline": "baseline"}, roles=SSP_ROLES,
        )


def test_resolve_rejects_an_unknown_attribute_variant(tmp_path: Path) -> None:
    _, architecture = _load_architecture(tmp_path, ATTRIBUTE_SET_VARIATION)

    with pytest.raises(
        ValueError,
        match="Unknown variant 'nope' for variation point 'ScenarioChoice'",
    ):
        resolve(architecture, "test_selected_scenario", {"scenario": "nope"}, roles=SSP_ROLES)


def test_resolve_rejects_an_unselected_attribute_point(tmp_path: Path) -> None:
    _, architecture = _load_architecture(tmp_path, ATTRIBUTE_SET_VARIATION)

    with pytest.raises(
        ValueError,
        match="Attribute variation point 'ScenarioChoice' at 'scenario'.*"
        "is not selected",
    ):
        resolve(architecture, "test_selected_scenario", {}, roles=SSP_ROLES)


def test_resolve_rejects_an_attribute_variant_without_a_type(tmp_path: Path) -> None:
    _, architecture = _load_architecture(tmp_path, UNTYPED_ATTRIBUTE_VARIANT)

    with pytest.raises(
        ValueError,
        match="'empty' of variation point 'Choice' has no resolvable type",
    ):
        resolve(architecture, "System", {"value": "empty"}, roles=SSP_ROLES)


def test_parse_selections_rejects_a_duplicate_key() -> None:
    with pytest.raises(ValueError, match="names variation point 'scenario' twice"):
        parse_selection("scenario=baseline;scenario=lateStep")


def test_resolve_rejects_a_nested_suffix_matching_two_paths(
    tmp_path: Path,
) -> None:
    """A suffix that ends both 'a.inner.x' and 'b.inner.x' is ambiguous."""
    _, architecture = _load_architecture(tmp_path, AMBIGUOUS_NESTED)

    with pytest.raises(
        ValueError,
        match=re.escape(
            "Selection key 'inner.x' is ambiguous in composition 'System'; "
            "it names 'a.inner.x', 'b.inner.x'. Write the full dotted path."
        ),
    ):
        resolve(architecture, "System", {"inner.x": "anything"}, roles=SSP_ROLES)


def test_resolve_accepts_one_full_nested_path(tmp_path: Path) -> None:
    """The full dotted path disambiguates the two nested usages."""
    _, architecture = _load_architecture(tmp_path, AMBIGUOUS_NESTED)

    with pytest.raises(
        ValueError,
        match=re.escape(
            "Selection key 'a.inner.x' names part usage 'a.inner.x', which is "
            "not a variation point; select a variation point instead."
        ),
    ):
        resolve(architecture, "System", {"a.inner.x": "x"}, roles=SSP_ROLES)


def test_resolution_is_independent_of_input_order(tmp_path: Path) -> None:
    """Keys apply shallowest-first, so the map order does not matter."""
    _, architecture = _load_architecture(tmp_path, RESOLUTION_ORDER)

    first, first_map = resolve_selected(
        architecture, "System", {"x": "a", "inner.y": "b"}, roles=SSP_ROLES
    )
    second, second_map = resolve_selected(
        architecture, "System", {"inner.y": "b", "x": "a"}, roles=SSP_ROLES
    )

    assert first_map == second_map == {"x": "a", "inner.y": "b"}
    assert first.part_definitions["System"].parts["x"].type_name == "A"
    assert first.part_definitions["Inner"].parts["y"].type_name == "B"
    assert second.part_definitions["Inner"].parts["y"].type_name == "B"


def test_canonical_map_records_the_resolved_path_not_the_user_key(
    tmp_path: Path,
) -> None:
    """A suffix key is canonicalised to the path it resolved to."""
    _, architecture = _load_architecture(tmp_path, NESTED_BODY_VARIATION)

    _, canonical = resolve_selected(
        architecture,
        "System",
        {"path": "nestedPath", "stage": "attenuateStage"}, roles=SSP_ROLES,
    )

    assert canonical == {"path": "nestedPath", "path.stage": "attenuateStage"}


def test_canonical_map_keeps_both_paths_for_a_bare_and_an_inner_key(
    tmp_path: Path,
) -> None:
    """A top-level and a nested key are both recorded under their own path."""
    _, architecture = _load_architecture(tmp_path, RESOLUTION_ORDER)

    _, canonical = resolve_selected(
        architecture, "System", {"x": "a", "y": "b"}, roles=SSP_ROLES
    )

    assert canonical == {"x": "a", "inner.y": "b"}


def test_resolve_rejects_a_key_removed_by_another_selection(
    tmp_path: Path,
) -> None:
    """'zpath' is replaced by a body without 'astage', so that key is gone."""
    _, architecture = _load_architecture(tmp_path, NESTED_UNDER_REPLACED)

    with pytest.raises(
        ValueError,
        match=re.escape(
            "Selection key 'zpath.astage' is nested under another selected "
            "variation point and no longer exists after resolution; select "
            "one variation point per path."
        ),
    ):
        resolve(architecture, "System", {"astage": "a", "zpath": "plain"}, roles=SSP_ROLES)


def test_nested_point_reports_an_unknown_variant(tmp_path: Path) -> None:
    """An unknown variant under a resolved outer point names the inner point."""
    _, architecture = _load_architecture(tmp_path, NESTED_UNKNOWN)

    with pytest.raises(
        ValueError,
        match=re.escape(
            "Unknown variant 'nope' for variation point 'InnerChoice'; "
            "expected one of a, b."
        ),
    ):
        resolve(architecture, "System", {"outer": "chosen", "outer.inner": "nope"}, roles=SSP_ROLES)


def test_resolve_rejects_a_body_part_the_body_does_not_declare(
    tmp_path: Path,
) -> None:
    """A connection end naming a part the body does not declare is refused."""
    _, architecture = _load_architecture(tmp_path, BODY_CHECKS)

    with pytest.raises(
        ValueError,
        match=re.escape(
            "Variant 'directPath' of variation point 'GhostChoice' connects to "
            "part 'ghost', which its body does not declare."
        ),
    ):
        resolve(architecture, "GhostSystem", {"path": "directPath"}, roles=SSP_ROLES)


def test_resolve_rejects_a_synthesized_definition_name_collision(
    tmp_path: Path,
) -> None:
    """The deterministic name '<Point>__<variant>' must not already exist."""
    _, architecture = _load_architecture(tmp_path, BODY_CHECKS)

    with pytest.raises(
        ValueError,
        match=re.escape(
            "Synthesized variant definition 'Collision__directPath' for "
            "variation point 'Collision' collides with an existing part "
            "definition; rename the variant."
        ),
    ):
        resolve(architecture, "CollisionSystem", {"path": "directPath"}, roles=SSP_ROLES)


def test_resolve_rejects_a_body_attribute_the_owner_already_declares(
    tmp_path: Path,
) -> None:
    """Merging a body attribute must not shadow the owning definition's own."""
    _, architecture = _load_architecture(tmp_path, BODY_CHECKS)

    with pytest.raises(
        ValueError,
        match=re.escape(
            "Variant 'withValues' of variation point 'AttributeChoice' "
            "declares attribute 'pyssp_default_start_time', which definition "
            "'AttributeSystem' already declares; rename it."
        ),
    ):
        resolve(architecture, "AttributeSystem", {"path": "withValues"}, roles=SSP_ROLES)


def test_resolve_rejects_a_variant_with_a_type_and_a_body(
    tmp_path: Path,
) -> None:
    _, architecture = _load_architecture(tmp_path, MEMBER_RULES)

    with pytest.raises(
        ValueError,
        match=re.escape(
            "Selected variant 'both' of variation point 'BothChoice' declares "
            "both type 'Gain' and a body; use one."
        ),
    ):
        resolve(architecture, "BothSystem", {"point": "both"}, roles=SSP_ROLES)


def test_resolve_rejects_a_variant_with_neither_type_nor_body(
    tmp_path: Path,
) -> None:
    _, architecture = _load_architecture(tmp_path, MEMBER_RULES)

    with pytest.raises(
        ValueError,
        match=re.escape(
            "Selected variant 'empty' of variation point 'EmptyChoice' has no "
            "resolvable type and no body; write 'variant part empty : "
            "<PartDef>;' or give it a body."
        ),
    ):
        resolve(architecture, "EmptySystem", {"point": "empty"}, roles=SSP_ROLES)


def test_resolve_rejects_a_variant_typed_by_a_non_part_definition(
    tmp_path: Path,
) -> None:
    _, architecture = _load_architecture(tmp_path, MEMBER_RULES)

    with pytest.raises(
        ValueError,
        match=re.escape(
            "Selected variant 'wrong' of variation point 'WrongTypeChoice' has "
            "type 'Weight', which is not a part definition; only part "
            "variants are supported."
        ),
    ):
        resolve(architecture, "WrongTypeSystem", {"point": "wrong"}, roles=SSP_ROLES)


def test_resolve_rejects_a_point_with_no_captured_part_variants(
    tmp_path: Path,
) -> None:
    _, architecture = _load_architecture(tmp_path, MEMBER_RULES)

    with pytest.raises(
        ValueError,
        match=re.escape(
            "Variation point 'point' has no captured part variants; only "
            "'variant part <name> : <PartDef>;' members are supported."
        ),
    ):
        resolve(architecture, "NoVariantsSystem", {"point": "anything"}, roles=SSP_ROLES)


def test_resolve_rejects_a_point_with_no_captured_attribute_variants(
    tmp_path: Path,
) -> None:
    _, architecture = _load_architecture(tmp_path, MEMBER_RULES)

    with pytest.raises(
        ValueError,
        match=re.escape(
            "Attribute variation point 'EmptyScale' has no captured attribute "
            "variants; only 'variant attribute <name> : <AttributeDef>;' "
            "members are supported."
        ),
    ):
        resolve(architecture, "AttributeSystem", {"gain": "anything"}, roles=SSP_ROLES)


def test_configuration_body_rejects_an_unnamed_part(tmp_path: Path) -> None:
    with pytest.raises(
        ValueError,
        match=re.escape(
            "A part usage in a configuration body must be named or redefine "
            "exactly one feature"
        ),
    ):
        _load_architecture(tmp_path, CONFIG_BODY_UNNAMED_PART)


def test_configuration_body_rejects_an_unnamed_attribute(tmp_path: Path) -> None:
    with pytest.raises(
        ValueError,
        match=re.escape(
            "An attribute usage in a configuration body must be named or "
            "redefine exactly one feature"
        ),
    ):
        _load_architecture(tmp_path, CONFIG_BODY_UNNAMED_ATTRIBUTE)


def test_configuration_body_rejects_a_member_it_cannot_carry(
    tmp_path: Path,
) -> None:
    with pytest.raises(
        ValueError,
        match=re.escape("Unsupported member in a configuration body: 'portp:RealSignal;'."),
    ):
        _load_architecture(tmp_path, CONFIG_BODY_UNSUPPORTED)


def test_variant_body_rejects_an_unnamed_part(tmp_path: Path) -> None:
    with pytest.raises(
        ValueError,
        match=re.escape("A part usage in a variant body must be named"),
    ):
        _load_architecture(tmp_path, VARIANT_BODY_UNNAMED_PART)


def test_variant_body_rejects_an_unnamed_attribute(tmp_path: Path) -> None:
    with pytest.raises(
        ValueError,
        match=re.escape("An attribute usage in a variant body must be named"),
    ):
        _load_architecture(tmp_path, VARIANT_BODY_UNNAMED_ATTRIBUTE)


def test_variant_body_rejects_a_member_it_cannot_carry(tmp_path: Path) -> None:
    with pytest.raises(
        ValueError,
        match=re.escape("Unsupported member in a variant body: 'portp:RealSignal;'."),
    ):
        _load_architecture(tmp_path, VARIANT_BODY_UNSUPPORTED)


def test_a_resolved_usage_is_no_longer_a_variation_point(tmp_path: Path) -> None:
    """Resolving twice must not report the already substituted usage."""
    _, architecture = _load_architecture(tmp_path, USAGE_VARIATION)

    resolved = resolve(architecture, "System", {"source": "stepSource"}, roles=SSP_ROLES)
    source = resolved.part_definitions["System"].parts["source"]
    assert source.is_variation is False

    again = resolve(resolved, "System", {}, roles=SSP_ROLES)
    assert again.part_definitions["System"].parts["source"].type_name == "Step"


