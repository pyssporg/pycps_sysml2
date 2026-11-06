"""Authored source-text scanning: imports, connection ends, constraint bodies.

This module works on plain ``str`` text and owns no ``sysmlpy`` import. The
parser hands it the authored source (and the grammar dump of a constraint
usage) because the grammar layer garbles a constraint *definition* body and
because a connection end is a plain dotted name once the grammar has been
walked. Import declarations are read from the grammar objects when they are
well formed and from their textual dump otherwise.
"""

from __future__ import annotations

import re
from pathlib import Path

from pycps_sysml2.model.model import ConstraintParameter
from pycps_sysml2.model.names import unquote_name


# -- connection endpoints ---------------------------------------------------


def connection_endpoint(
    names: list[str], file: Path | None = None
) -> tuple[str | None, str]:
    """Split one connection end into ``(part, port)``; a bare name is a boundary port."""
    if not names:
        where = f" in {file}" if file is not None else " in a variant body"
        raise ValueError(
            "Connection ends must be 'part.port' or a boundary 'port', "
            f"got an empty end{where}"
        )
    if len(names) == 1:
        return None, names[0]
    return names[0], names[-1]


# -- import declarations ----------------------------------------------------


_IMPORT = re.compile(
    r"^(?:(?:private|protected|public)\s+)?import\s+(?:all\s+)?"
    r"(?P<target>.+?)\s*;?$"
)


def _unquote_path(path: str) -> str:
    """Unquote each ``::``-separated segment of a qualified name."""
    return "::".join(unquote_name(part.strip()) for part in path.split("::"))


def parse_import_declaration(text: str) -> tuple[str, str | None] | None:
    """``(package, member)`` for one import statement, or ``None``.

    ``member`` is ``None`` for a ``::*`` wildcard and the imported name
    otherwise. The parser boundary prefers structured sysmlpy objects and
    falls back here only when that shape is unusable, so this also accepts the
    ``dump()`` form (``private import Pkg::*;``). Anything that is not an
    import — an ``alias``, malformed text — returns ``None`` and is skipped.
    """
    match = _IMPORT.match(text.strip())
    if match is None:
        return None
    target = match.group("target").strip()
    if target.endswith("::*"):
        package = target[:-3].strip()
        return (_unquote_path(package), None) if package else None
    if "::" not in target:
        return None
    package, member = target.rsplit("::", 1)
    package = _unquote_path(package)
    member = unquote_name(member.strip())
    if not package or not member or "*" in member:
        return None
    return package, member


# -- constraint bodies ------------------------------------------------------
#
# ``grammar.dump()`` is reliable for constraint *usages* but garbles the
# expression of a constraint *definition*. Definitions are therefore read from
# the authored source text, once per file, by scanning the matching braces.

_CONSTRAINT_DEF = re.compile(r"\bconstraint\s+def\s+([A-Za-z_]\w*)\s*\{")
_IN_PARAMETER = re.compile(r"^in\s+([A-Za-z_]\w*)\s*:\s*([\w:]+)$")
_IN_BINDING = re.compile(r"^in\s+([A-Za-z_]\w*)\s*=\s*(.+)$")
_DOC_STRING = re.compile(r'\bdoc\s*"(?:\\.|[^"\\])*"')


def _mask_ignored(text: str) -> str:
    """Blank comments and string literals, preserving offsets and newlines."""
    chars = list(text)
    index = 0
    length = len(text)
    while index < length:
        if text.startswith("//", index):
            end = text.find("\n", index)
            end = length if end == -1 else end
            for position in range(index, end):
                chars[position] = " "
            index = end
        elif text.startswith("/*", index):
            end = text.find("*/", index + 2)
            end = length if end == -1 else end + 2
            for position in range(index, end):
                if chars[position] != "\n":
                    chars[position] = " "
            index = end
        elif text[index] == '"':
            end = index + 1
            escaped = False
            while end < length:
                if escaped:
                    escaped = False
                elif text[end] == "\\":
                    escaped = True
                elif text[end] == '"':
                    end += 1
                    break
                end += 1
            for position in range(index, end):
                if chars[position] != "\n":
                    chars[position] = " "
            index = end
        else:
            index += 1
    return "".join(chars)


def _matching_brace(text: str, opening: int) -> int:
    """Index of the ``}`` matching the ``{`` at *opening* in masked text."""
    depth = 0
    for index in range(opening, len(text)):
        char = text[index]
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return index
    raise ValueError("Unbalanced '{' in constraint body")


def constraint_definitions_from_source(source: str) -> dict[str, str]:
    """Authored body text of every ``constraint def Name { ... }``, keyed by name."""
    masked = _mask_ignored(source)
    bodies: dict[str, str] = {}
    for match in _CONSTRAINT_DEF.finditer(masked):
        opening = match.end() - 1
        closing = _matching_brace(masked, opening)
        bodies[match.group(1)] = source[opening + 1 : closing]
    return bodies


def constraint_definition_body(source: str, name: str) -> str | None:
    """Authored body of the named constraint definition, or ``None``."""
    return constraint_definitions_from_source(source).get(name)


def _remove_comments(text: str) -> str:
    """Drop ``//`` and ``/* ... */`` comments, keeping everything else."""
    chars = list(text)
    index = 0
    length = len(text)
    while index < length:
        if text.startswith("//", index):
            end = text.find("\n", index)
            end = length if end == -1 else end
            for position in range(index, end):
                chars[position] = " "
            index = end
        elif text.startswith("/*", index):
            end = text.find("*/", index + 2)
            end = length if end == -1 else end + 2
            for position in range(index, end):
                if chars[position] != "\n":
                    chars[position] = " "
            index = end
        elif text[index] == '"':
            end = index + 1
            escaped = False
            while end < length:
                if escaped:
                    escaped = False
                elif text[end] == "\\":
                    escaped = True
                elif text[end] == '"':
                    end += 1
                    break
                end += 1
            index = end
        else:
            index += 1
    return "".join(chars)


def _split_statements(text: str) -> list[str]:
    """Split a body on top-level ``;``, respecting parentheses and strings."""
    statements: list[str] = []
    current: list[str] = []
    depth = 0
    quoted = False
    escaped = False
    for char in text:
        if escaped:
            current.append(char)
            escaped = False
            continue
        if quoted and char == "\\":
            current.append(char)
            escaped = True
            continue
        if char == '"':
            quoted = not quoted
            current.append(char)
            continue
        if not quoted:
            if char in "([{":
                depth += 1
            elif char in ")]}":
                depth = max(depth - 1, 0)
            elif char == ";" and depth == 0:
                statements.append("".join(current).strip())
                current = []
                continue
        current.append(char)
    tail = "".join(current).strip()
    if tail:
        statements.append(tail)
    return [statement for statement in statements if statement]


def parse_constraint_body(
    text: str,
) -> tuple[dict[str, ConstraintParameter], str | None]:
    """Turn authored constraint body text into parameters plus expression.

    ``in name : Type`` becomes a typed definition parameter; ``in name = ref``
    becomes a usage binding stored in ``ConstraintParameter.value``. Any other
    statement is the boolean expression.
    """
    cleaned = _DOC_STRING.sub("", _remove_comments(text))
    cleaned = re.sub(r"\bdoc\b", "", cleaned)
    parameters: dict[str, ConstraintParameter] = {}
    expressions: list[str] = []
    for statement in _split_statements(cleaned):
        parameter_match = _IN_PARAMETER.match(statement)
        if parameter_match:
            name, type_name = parameter_match.groups()
            parameters[name] = ConstraintParameter(name=name, type_name=type_name)
            continue
        binding_match = _IN_BINDING.match(statement)
        if binding_match:
            name, reference = binding_match.groups()
            parameters[name] = ConstraintParameter(
                name=name, value=reference.strip()
            )
            continue
        expressions.append(statement)
    expression = " ".join(expressions).strip() or None
    return parameters, expression


def _body_text(dump: str) -> str:
    """Body between the first ``{`` and its matching ``}`` of a grammar dump."""
    masked = _mask_ignored(dump)
    opening = masked.find("{")
    if opening == -1:
        return ""
    closing = _matching_brace(masked, opening)
    return dump[opening + 1 : closing]
