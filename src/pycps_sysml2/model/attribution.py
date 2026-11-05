"""Per-file scanning and definition attribution for the merged load.

``sysmlpy`` merges files that declare the same package, so the merged parse
carries no origin. This module owns the second, cheap per-file pass that ties
each definition back to the file that declared it: it scans a file once for its
packages and per-file facts, names the primary root's package, and builds the
attribution map the merge walks.

The pass is per-file and sysmlpy-free: :mod:`pycps_sysml2.model.parser` parses
each file, and the facts stay per file — variation points and constraint bodies
are never folded into the merged parse.
"""

from __future__ import annotations

from pathlib import Path
from typing import NamedTuple

from pycps_sysml2.model.names import unquote_name
from pycps_sysml2.model.parser import import_declarations, parse_packages
from pycps_sysml2.model.source import constraint_definitions_from_source
from pycps_sysml2.model.variation import VariationFacts, variation_facts

__all__ = [
    "MergeState",
    "ParsedFile",
    "attribution",
    "collect_imports",
    "primary_package_name",
    "scan_files",
]

# sysmlpy package collections, in the order definitions are added.
_SYSTEM_COLLECTIONS = (
    ("part", "parts"),
    ("port", "ports"),
    ("attribute", "attributes"),
    ("requirement", "requirements"),
    ("constraint", "constraints"),
)


class ParsedFile(NamedTuple):
    """One scanned file: its package(s) plus the per-file facts the IR needs."""

    file: Path
    include: Path | None
    packages: list
    variation: VariationFacts
    constraint_bodies: dict[str, str]
    imports: list[tuple[str, str | None]]


class MergeState:
    """Per-load attribution cursor and duplicate-conflict origins."""

    def __init__(
        self, attribution: dict[tuple[str, str, str], list[ParsedFile]]
    ) -> None:
        self.attribution = attribution
        self.cursors: dict[tuple[str, str, str], int] = {}
        self.model_origins: dict[str, Path] = {}
        self.included_origins: dict[str, Path] = {}

    def take(self, package: str, kind: str, name: str) -> ParsedFile:
        """The next declaring file of one definition, in merged-walk order."""
        key = (package, kind, name)
        index = self.cursors.get(key, 0)
        self.cursors[key] = index + 1
        occurrences = self.attribution.get(key, [])
        if index >= len(occurrences):
            raise RuntimeError(
                f"No source attribution for {kind} definition '{name}' "
                f"in package {package}"
            )
        return occurrences[index]


def scan_files(entries: list[tuple[Path, Path | None]]) -> list[ParsedFile]:
    """Parse each file once for attribution and its per-file facts.

    The merged model carries no origin, so this pass is what ties each
    definition back to its file. Variation facts and constraint bodies read
    the source text; they stay per file and are never folded into the merged
    parse.
    """
    scanned: list[ParsedFile] = []
    for file, include in entries:
        source = file.read_text(encoding="utf-8")
        packages = parse_packages(file)
        scanned.append(
            ParsedFile(
                file=file,
                include=include,
                packages=packages,
                variation=variation_facts(source),
                constraint_bodies=constraint_definitions_from_source(source),
                imports=[
                    declaration
                    for package in packages
                    for declaration in import_declarations(package)
                ],
            )
        )
    return scanned


def collect_imports(
    scanned: list[ParsedFile],
) -> dict[str, frozenset[str] | None]:
    """Merge every file's import declarations into one visibility map.

    Read from the per-file scan, not the merged parse: sysmlpy keeps only the
    first file's imports when it merges same-named packages. The result is
    keyed by imported package name; ``None`` means a ``::*`` wildcard and a
    member import accumulates a union. Wildcards absorb member imports, so
    duplicate declarations never raise. Package names are sorted for a stable
    order regardless of load order.
    """
    collected: dict[str, set[str] | None] = {}
    for parsed in scanned:
        for package, member in parsed.imports:
            if collected.get(package, set()) is None:
                continue
            if member is None:
                collected[package] = None
            elif package in collected:
                collected[package].add(member)
            else:
                collected[package] = {member}
    return {
        package: None if collected[package] is None else frozenset(collected[package])
        for package in sorted(collected)
    }


def primary_package_name(primary: list[ParsedFile]) -> str:
    """The primary root's single package name, or a mismatch error."""
    name = primary[0].packages[0].name
    for parsed in primary[1:]:
        current = parsed.packages[0].name
        if current != name:
            raise ValueError(
                f"Mismatched package names: {name} vs {current} in {parsed.file}"
            )
    return name


def attribution(
    model, scanned: list[ParsedFile]
) -> dict[tuple[str, str, str], list[ParsedFile]]:
    """Map each definition to its declaring files, in merged-walk order.

    The key is ``(package, kind, name)`` so two packages declaring the same
    bare name cannot steal each other's ``source_file``. The walk mirrors the
    merge: merged package order, then the definition kinds, then the files in
    load order. A duplicate therefore resolves to the same later file the old
    per-file merge reported.
    """
    attribution: dict[tuple[str, str, str], list[ParsedFile]] = {}
    for package in model.packages:
        for kind, collection in _SYSTEM_COLLECTIONS:
            for parsed in scanned:
                for own in parsed.packages:
                    if own.name != package.name:
                        continue
                    for element in getattr(own, collection):
                        if element.is_definition:
                            key = (package.name, kind, unquote_name(element.name))
                            attribution.setdefault(key, []).append(parsed)
    return attribution
