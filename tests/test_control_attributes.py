"""The control-attribute vocabulary is injectable, not a module global.

A consumer may carry a different prefix and a different retired map. The module
constants stay as the documented defaults; these tests pin both paths so a
consumer cannot silently fall back to ``CONTROL_PREFIX``.
"""

from __future__ import annotations

import pytest

from pycps_sysml2.core.control import (
    CONTROL,
    CONTROL_PREFIX,
    DEFAULT_START_ATTR,
    DEFAULT_STOP_ATTR,
    FLAT_CONNECTOR_ATTR,
    RETIRED_CONTROL_ATTRS,
    ControlAttributes,
    is_control_attribute,
    is_retired_control_attribute,
    validate_retired_control_attributes,
)
from pycps_sysml2.model import Architecture, Attribute, PartDefinition


def _architecture(*attribute_names: str) -> Architecture:
    """One part def carrying the named attributes, for validation tests."""
    part_def = PartDefinition(
        name="Component",
        attributes={
            name: Attribute(name=name, type_name="String")
            for name in attribute_names
        },
    )
    return Architecture(
        package_name="Pkg",
        part_definitions={"Component": part_def},
    )


def test_the_default_prefix_recognises_control_attributes() -> None:
    assert is_control_attribute("pyssp_x")
    assert is_control_attribute(DEFAULT_START_ATTR)
    assert not is_control_attribute("x")


def test_the_module_constants_are_the_default_vocabulary() -> None:
    assert CONTROL.prefix == CONTROL_PREFIX == "pyssp_"
    assert DEFAULT_START_ATTR == "pyssp_default_start_time"
    assert DEFAULT_STOP_ATTR == "pyssp_default_stop_time"
    assert FLAT_CONNECTOR_ATTR == "pyssp_flat_connector"
    assert CONTROL.default_start == DEFAULT_START_ATTR
    assert CONTROL.default_stop == DEFAULT_STOP_ATTR
    assert CONTROL.flat_connector == FLAT_CONNECTOR_ATTR


def test_a_custom_prefix_recognises_only_its_own_attributes() -> None:
    attributes = ControlAttributes(prefix="acme_")

    assert attributes.is_control("acme_x")
    assert not attributes.is_control("pyssp_x")
    assert is_control_attribute("acme_x", attributes=attributes)
    assert not is_control_attribute("pyssp_x", attributes=attributes)


def test_a_custom_prefix_derives_its_own_names() -> None:
    attributes = ControlAttributes(prefix="acme_")

    assert attributes.default_start == "acme_default_start_time"
    assert attributes.default_stop == "acme_default_stop_time"
    assert attributes.flat_connector == "acme_flat_connector"


def test_retired_attributes_are_recognised_by_default() -> None:
    assert set(RETIRED_CONTROL_ATTRS) == {
        "pyssp_implementation",
        "pyssp_parameter_set",
    }
    assert is_retired_control_attribute("pyssp_implementation")
    assert not is_retired_control_attribute("pyssp_something_else")
    assert not is_retired_control_attribute("acme_implementation")


def test_validate_rejects_a_retired_attribute() -> None:
    architecture = _architecture("pyssp_implementation")

    with pytest.raises(ValueError) as excinfo:
        validate_retired_control_attributes(architecture)

    assert str(excinfo.value).startswith(
        "Component.pyssp_implementation is no longer supported; "
    )


def test_validate_accepts_the_injected_retired_map() -> None:
    architecture = _architecture("acme_legacy")
    attributes = ControlAttributes(
        prefix="acme_",
        retired={"acme_legacy": "use 'attribute fmu_meta'"},
    )

    with pytest.raises(ValueError) as excinfo:
        validate_retired_control_attributes(architecture, attributes=attributes)

    assert str(excinfo.value) == (
        "Component.acme_legacy is no longer supported; use 'attribute fmu_meta'"
    )


def test_the_injected_map_replaces_the_default_one() -> None:
    """A custom map must not also reject the default retired names."""
    architecture = _architecture("pyssp_implementation")
    attributes = ControlAttributes(retired={"acme_legacy": "use something else"})

    validate_retired_control_attributes(architecture, attributes=attributes)
