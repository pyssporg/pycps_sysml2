"""File orchestration: builds the repo-owned model from ``.sysml`` files.

This module walks a load target, asks :mod:`pycps_sysml2.model.parser` for one
merged parse of every file, merges the resulting packages into one
:class:`~pycps_sysml2.model.model.Architecture`, and builds the repo-owned
dataclasses from the parsed elements.

sysmlpy itself merges files that declare the same package, so the primary
root's files and every included root go through a single
:func:`~pycps_sysml2.model.parser.parse_files` call. The merged model carries
no origin, so a second, cheap per-file pass recovers the file behind each
definition; that pass lives in :mod:`pycps_sysml2.model.attribution` and is
the price of the merged parse. The primary root must resolve to one package
name because ``Architecture.package_name`` stores it; include roots may use
any package name.

Package names are first-class in the resulting
:class:`~pycps_sysml2.model.model.Architecture`: a definition of the primary
package is stored under its bare name, and one from any other package under
``"<package>::<name>"``. Definition ``.name`` stays bare, so no package
qualifier reaches an artifact surface.

The parser boundary is exactly one module: only
:mod:`pycps_sysml2.model.parser` imports ``sysmlpy`` and reads raw ANTLR trees,
and only :mod:`pycps_sysml2.model.variation` walks the tree for variation
points; every other module works against the repo-owned model, never against
sysmlpy objects. Loading stays non-validating, so unresolved references simply
surface as ``resolve_part``/``resolve_port`` returning ``None`` in consumers.
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from pycps_sysml2.model.attribution import (
    MergeState,
    attribution,
    primary_package_name,
    scan_files,
)
from pycps_sysml2.model.model import (
    Architecture,
    Attribute,
    AttributeDefinition,
    Binding,
    Connection,
    ConstraintDefinition,
    PartDefinition,
    PartUsage,
    PortDefinition,
    PortUsage,
    RequirementDefinition,
    endpoint_text,
)
from pycps_sysml2.model.names import unquote_name
from pycps_sysml2.model.parser import (
    UUID_PATTERN,
    assert_constraint,
    binding_endpoints,
    connection_endpoints,
    constraint_usage,
    is_definition_variation,
    multiplicity,
    normalize_value,
    parse_files,
    port_direction,
    specializes,
)
from pycps_sysml2.model.source import connection_endpoint, parse_constraint_body
from pycps_sysml2.model.variation import VariationFacts

__all__ = ["load"]


_DEFINITION_ATTRIBUTES = (
    ("part", "part_definitions"),
    ("port", "port_definitions"),
    ("attribute", "attribute_definitions"),
    ("requirement", "requirement_definitions"),
    ("constraint", "constraint_definitions"),
)


def load(
    path: Path | str | Sequence[Path | str],
    *includes: Path | str,
) -> Architecture:
    """Load one primary architecture root plus any number of included roots.

    ``path`` is either one root or a sequence whose first element is the
    primary model root; any further sequence elements and ``*includes`` are
    included roots. A root is a ``.sysml`` file or a directory of them. A file
    loads exactly that file; a directory loads its ``*.sysml`` files
    non-recursively in sorted name order. The primary model's files must
    declare the same package name.

    Every file is parsed in one ``sysmlpy.load_files`` call, so files that
    declare the same package are merged by sysmlpy. A second per-file pass
    recovers each definition's ``source_file`` and lets cross-file duplicates
    name the declaring files precisely.

    Included roots are opt-in: with none, ``load(primary)`` loads exactly the
    primary's definitions and leaves the behaviour unchanged. An included root
    merges shared definitions and need not use the model's package name,
    because it supplies definitions rather than composition; the exemption is
    the package name only. A definition whose stored key the model already
    declares is an error, never an override, and so is one key supplied by two
    included roots; the same bare name in a different package is a distinct
    definition and coexists. Every key from an included root is recorded on
    :attr:`Architecture.included_definitions`.
    """
    entries = [path] if isinstance(path, (str, Path)) else list(path)
    if not entries:
        raise ValueError("load() requires a primary model root")
    include_entries = [Path(entry) for entry in entries[1:]]
    include_entries.extend(Path(entry) for entry in includes)

    files = _resolve_files(Path(entries[0]))
    primary = scan_files([(file, None) for file in files])
    package_name = primary_package_name(primary)

    included_files = [
        (file, root)
        for root in include_entries
        for file in _resolve_files(root)
    ]
    scanned = primary + scan_files(included_files)

    model = parse_files([parsed.file for parsed in scanned])
    architecture = Architecture(package_name=package_name)
    _merge_model(architecture, model, attribution(model, scanned))
    return architecture


# -- file resolution (legacy parity) --------------------------------------


def _resolve_files(path: Path) -> list[Path]:
    """Resolve a load target to the files to parse, matching legacy semantics.

    File → ``[path]``; directory → non-recursive ``sorted(glob("*.sysml"))``;
    a missing path or an empty directory raise ``FileNotFoundError`` (the
    missing-path message is what a caller catches to bootstrap a new document).
    """
    if path.is_file():
        return [path]
    if path.is_dir():
        files = sorted(path.glob("*.sysml"))
        if not files:
            raise FileNotFoundError(f"No .sysml files found under {path}")
        return files
    raise FileNotFoundError(f"No .sysml file found under {path}")


# -- merged loading --------------------------------------------------------


def _merge_model(architecture: Architecture, model, attribution) -> None:
    """Add every definition of the merged model, parts first, then the rest."""
    state = MergeState(attribution)
    for package in model.packages:
        package_name = package.name
        for element in package.parts:
            if not element.is_definition:
                continue
            parsed = state.take(package_name, "part", unquote_name(element.name))
            _add_definition(
                architecture,
                architecture.add_part_def,
                _part_definition(element, parsed.file, parsed.variation),
                parsed,
                state,
                package_name,
            )
        for element in package.ports:
            if not element.is_definition:
                continue
            parsed = state.take(package_name, "port", unquote_name(element.name))
            _add_definition(
                architecture,
                architecture.add_port_def,
                _port_definition(element, parsed.file),
                parsed,
                state,
                package_name,
            )
        for element in package.attributes:
            if not element.is_definition:
                continue
            parsed = state.take(
                package_name, "attribute", unquote_name(element.name)
            )
            _add_definition(
                architecture,
                architecture.add_attribute_def,
                _attribute_definition(element, parsed.file, parsed.variation),
                parsed,
                state,
                package_name,
            )
        for element in package.requirements:
            if not element.is_definition:
                continue
            parsed = state.take(
                package_name, "requirement", unquote_name(element.name)
            )
            _add_definition(
                architecture,
                architecture.add_requirement_def,
                _requirement_definition(element, parsed.file),
                parsed,
                state,
                package_name,
            )
        for element in package.constraints:
            if not element.is_definition:
                continue
            parsed = state.take(
                package_name, "constraint", unquote_name(element.name)
            )
            _add_definition(
                architecture,
                architecture.add_constraint_def,
                _constraint_definition(
                    element, parsed.file, parsed.constraint_bodies
                ),
                parsed,
                state,
                package_name,
            )


def _add_definition(architecture, add, definition, parsed, state, package) -> None:
    """Add a definition, re-raising duplicates with file context (legacy parity)."""
    definition.package = package
    include = parsed.include
    if include is not None:
        _reject_included_duplicate(
            architecture,
            definition,
            include,
            state.model_origins,
            state.included_origins,
        )
    try:
        add(definition)
    except ValueError:
        kind = type(definition).__name__.removesuffix("Definition").lower()
        raise ValueError(
            f"Duplicate {kind} definition for {definition.name} in {parsed.file}"
        ) from None
    key = architecture.stored_key(definition)
    if include is not None:
        architecture.included_definitions.add(key)
        state.included_origins[key] = include
    else:
        state.model_origins[key] = parsed.file


def _reject_included_duplicate(
    architecture: Architecture,
    definition,
    include: Path,
    model_origins: dict[str, Path],
    origins: dict[str, Path],
) -> None:
    """Reject an included definition the model or another root supplies.

    Only a repeated stored key conflicts: the same bare name in a different
    package is a distinct definition and coexists.
    """
    key = architecture.stored_key(definition)
    for kind, attribute in _DEFINITION_ATTRIBUTES:
        existing = getattr(architecture, attribute).get(key)
        if existing is None:
            continue
        definition_kind = type(definition).__name__.removesuffix("Definition").lower()
        if key in model_origins:
            existing_path = model_origins[key]
            raise ValueError(
                f"Included {definition_kind} def '{definition.name}' from {include} "
                f"conflicts with the {kind} def declared in {existing_path}; "
                f"remove the local declaration of '{definition.name}' from "
                f"{existing_path} to use the included definition."
            )
        existing_include = origins.get(
            key, Path(existing.source_file or "<unknown>")
        )
        raise ValueError(
            f"Included {definition_kind} def '{definition.name}' from {include} "
            f"conflicts with the {kind} def already supplied by {existing_include}; "
            "a name may come from only one included root."
        )


# -- definition builders ----------------------------------------------------


def _part_definition(element, file: Path, variation: VariationFacts) -> PartDefinition:
    """Repo PartDefinition from a sysmlpy part definition.

    Member docs are not captured: sysmlpy attaches a ``doc /* ... */``
    written above a member to the owning definition, so per-member docs are
    not recoverable from a parsed model (sysmlpy_api.md §3).

    The variation flag comes from the grammar prefix; the variant members and
    usage-level flags come from the raw-tree walk, keyed by this definition's
    name.
    """
    definition_name = unquote_name(element.name)
    part_def = PartDefinition(
        name=definition_name,
        doc=element.doc,
        source_file=file.name,
        specializes=specializes(element),
        is_variation=is_definition_variation(element),
        variants=list(variation.variants.get(definition_name, ())),
    )
    variation_usages = variation.usage_points.get(definition_name, ())
    for attribute in element.attributes:
        # A redefining attribute (``attribute :>> scenario = ...;``) gets a UUID
        # as its parsed name; ``display_name`` keeps the inherited name.
        name = unquote_name(getattr(attribute, "display_name", None) or attribute.name)
        extras = variation.usage_extras.get((definition_name, name))
        part_def.attributes[name] = _attribute(
            attribute, extras.redefines if extras is not None else ()
        )
    for port in element.ports:
        # A redefining port (``out port :>> y : T;``) gets a UUID as its parsed
        # name; ``display_name`` keeps the name the composition connects to.
        name = unquote_name(getattr(port, "display_name", None) or port.name)
        part_def.ports[name] = PortUsage(
            name=name,
            direction=port_direction(port),
            type_name=port.typed_by_name,
            multiplicity=multiplicity(port),
        )
    for part in element.parts:
        # A redefining part usage (``part :>> source = ...;``) gets a UUID as
        # its parsed name; ``display_name`` keeps the inherited name.
        name = unquote_name(getattr(part, "display_name", None) or part.name)
        extras = variation.usage_extras.get((definition_name, name))
        part_def.parts[name] = PartUsage(
            name=name,
            type_name=part.typed_by_name,
            is_variation=name in variation_usages,
            variants=list(variation.usage_variants.get((element.name, name), ())),
            redefines=extras.redefines if extras is not None else (),
            subsets=extras.subsets if extras is not None else (),
            value=extras.value if extras is not None else None,
            body=extras.body if extras is not None else None,
        )
    for connect in element.connections:
        connection = _connection(connect, file)
        # Keyed by endpoint pair: a later connect with identical endpoints
        # overwrites the earlier one (legacy parity).
        part_def.connections[connection.key] = connection
    for child in element.children:
        if type(child).__name__ == "Binding":
            part_def.bindings.append(_binding(child, file))
    _attach_constraints(part_def, element, file)
    return part_def


def _attach_constraints(
    part_def: PartDefinition, element, file: Path
) -> None:
    """Append constraint usages and apply their ``assert`` statements.

    A constraint definition nested in a part def is not a usage and is skipped;
    ``assert`` statements are resolved to the usage they name after every usage
    has been collected.
    """
    asserts: list[tuple[str, bool]] = []
    for child in element.constraints:
        if getattr(child, "is_definition", False):
            continue
        if type(child.grammar).__name__ == "AssertConstraintUsage":
            asserts.append(assert_constraint(child))
            continue
        usage = constraint_usage(child)
        usage.source_file = file.name
        part_def.constraints.append(usage)
    for name, negated in asserts:
        for usage in part_def.constraints:
            if usage.name == name:
                usage.asserted = True
                usage.negated = negated
                break
        else:
            raise ValueError(
                f"assert names unknown constraint usage '{name}' in "
                f"'{part_def.name}' ({file})"
            )


def _port_definition(element, file: Path) -> PortDefinition:
    """Repo PortDefinition from a sysmlpy port definition."""
    port_def = PortDefinition(
        name=unquote_name(element.name),
        doc=element.doc,
        source_file=file.name,
        specializes=specializes(element),
    )
    for attribute in element.attributes:
        name = unquote_name(attribute.name)
        port_def.attributes[name] = _attribute(attribute)
    return port_def


def _attribute_definition(
    element, file: Path, variation: VariationFacts
) -> AttributeDefinition:
    """Repo AttributeDefinition from a sysmlpy attribute definition."""
    definition_name = unquote_name(element.name)
    attribute_def = AttributeDefinition(
        name=definition_name,
        doc=element.doc,
        source_file=file.name,
        specializes=specializes(element),
        is_variation=definition_name in variation.attribute_points,
        variants=list(variation.attribute_variants.get(definition_name, ())),
    )
    for attribute in element.attributes:
        attribute_def.attributes[unquote_name(attribute.name)] = _attribute(attribute)
    return attribute_def


def _requirement_definition(element, file: Path) -> RequirementDefinition:
    """Repo RequirementDefinition; the doc comment is the requirement text."""
    return RequirementDefinition(
        name=unquote_name(element.name), text=element.doc, source_file=file.name
    )


def _constraint_definition(
    element, file: Path, bodies: dict[str, str]
) -> ConstraintDefinition:
    """Repo ConstraintDefinition from the source-scanned authored body.

    ``sysmlpy`` garbles the expression of a constraint definition in its
    grammar dump, so the body is read from the authored source text instead.
    """
    parameters, expression = parse_constraint_body(bodies.get(element.name, ""))
    return ConstraintDefinition(
        name=unquote_name(element.name),
        doc=element.doc,
        source_file=file.name,
        parameters=parameters,
        expression=expression,
    )


def _connection(connect, file: Path) -> Connection:
    """Repo Connection from a sysmlpy connect statement.

    Only binary connects are supported. An end is either part-qualified
    (``connect a.p to b.q;``) or a bare port name that refers to a port of the
    enclosing part def, i.e. the system boundary (``connect gain.y to y;``).
    A parsed name of ``None`` or a UUID means sysmlpy generated it for an
    unnamed connect, so the legacy endpoint-derived name is rebuilt instead.
    """
    ends = connection_endpoints(connect)
    if len(ends) != 2:
        raise ValueError(
            f"Only binary connections are supported ('connect a.p to b.q;'), "
            f"got {len(ends)} ends in {file}"
        )
    source, destination = ends
    source_part, source_port = connection_endpoint(source, file)
    destination_part, destination_port = connection_endpoint(destination, file)
    name = connect.name
    if name is None or UUID_PATTERN.match(name):
        name = (
            f"{endpoint_text(source_part, source_port)}"
            f"_to_{endpoint_text(destination_part, destination_port)}"
        )
    else:
        name = unquote_name(name)
    return Connection(
        name=name,
        source_part=source_part,
        source_port=source_port,
        destination_part=destination_part,
        destination_port=destination_port,
    )


def _binding(bind, file: Path) -> Binding:
    """Repo Binding from a sysmlpy ``bind a.x = b.y;`` statement.

    Both endpoints keep their full feature chain. Unnamed bindings receive a
    UUID name from sysmlpy; those are normalized back to ``None``.
    """
    ends = binding_endpoints(bind)
    if len(ends) != 2:
        raise ValueError(
            f"Only binary bindings are supported ('bind a.x = b.y;'), "
            f"got {len(ends)} ends in {file}"
        )
    source, target = ends
    if not source or not target:
        raise ValueError(
            f"Binding ends must be feature references, got {source} = {target} in {file}"
        )
    name = bind.name
    if name is None or UUID_PATTERN.match(name):
        name = None
    else:
        name = unquote_name(name)
    return Binding(source=tuple(source), target=tuple(target), name=name)


# -- attribute usages -------------------------------------------------------


def _attribute(element, redefines: tuple[str, ...] = ()) -> Attribute:
    """Repo Attribute from a sysmlpy attribute usage."""
    return Attribute(
        name=unquote_name(getattr(element, "display_name", None) or element.name),
        type_name=element.typed_by_name,
        value=normalize_value(element),
        multiplicity=multiplicity(element),
        redefines=redefines,
    )
