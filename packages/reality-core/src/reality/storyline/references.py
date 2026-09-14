"""Symbolic references inside a storyline package and their resolution at run time.

A package never carries an opaque id or a human-readable number as identity
(Constitution II). It names seed records symbolically and points at what earlier
steps produced. Dates are relative to the run start, so the same file plays on any
day. This module owns the grammar of those references; the package validator uses
it to refuse what it cannot resolve, and the storyline service uses it to turn a
chapter's declared input into the arguments of a real proposal.

Reference kinds:

- ``$ref.<group>.<name>``            a seed party, item, location or term
- ``$company.party``                 the practice company's own party
- ``$seed.<as>.output.<path>``       a field of a named seed history result
- ``$chapter.<key>.output.<path>``   a field of an earlier chapter's output
- ``$context.<name>[.<path>]``       a value the chapter's ``context`` block read
- ``$exception.<class>.<reference>`` a finding id composed from a class and a record
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

REF_PREFIX = "$ref."
COMPANY_PREFIX = "$company."
SEED_PREFIX = "$seed."
CHAPTER_PREFIX = "$chapter."
CONTEXT_PREFIX = "$context."
EXCEPTION_PREFIX = "$exception."
REFERENCE_PREFIXES = (
    REF_PREFIX,
    COMPANY_PREFIX,
    SEED_PREFIX,
    CHAPTER_PREFIX,
    CONTEXT_PREFIX,
    EXCEPTION_PREFIX,
)

SEED_GROUPS = ("parties", "items", "locations", "terms")
COMPANY_FIELDS = ("party",)

RAW_ID_PATTERN = re.compile(r"^[a-z]{3}_[0-9a-f]{10}$")
RELATIVE_DATE_PATTERN = re.compile(r"^(?P<sign>[+-]?)(?P<days>\d{1,4})d$")
NAME_PATTERN = re.compile(r"^[a-z][a-z0-9_]{0,39}$")
CLASS_PATTERN = re.compile(r"^[a-z][a-z0-9_]{0,79}$")

# The only input fields a relative date may stand in. Everywhere else a string
# shaped like "-42d" is a mistake the validator names.
DATE_FIELDS = frozenset(
    {
        "at",
        "effective_at",
        "occurred_at",
        "observed_at",
        "requested_delivery_at",
        "document_date",
        "ordered_at",
        "promised_at",
        "due_before",
        "source_version_at",
        "value_date",
        "value",
    }
)
# Fields whose value is a calendar day rather than an instant.
DAY_FIELDS = frozenset({"document_date", "value"})


class ReferenceError(ValueError):
    """A reference the package or the run cannot resolve."""


def is_reference(value: Any) -> bool:
    return isinstance(value, str) and value.startswith(REFERENCE_PREFIXES)


def is_raw_identity(value: Any) -> bool:
    return isinstance(value, str) and bool(RAW_ID_PATTERN.match(value))


def is_relative_date(value: Any) -> bool:
    return isinstance(value, str) and bool(RELATIVE_DATE_PATTERN.match(value))


def parse_relative_date(text: str, start: datetime) -> datetime:
    match = RELATIVE_DATE_PATTERN.match(text)
    if not match:
        raise ReferenceError(f"'{text}' is not a relative date such as -42d or +3d.")
    days = int(match.group("days"))
    if match.group("sign") == "-":
        days = -days
    return start + timedelta(days=days)


@dataclass(frozen=True)
class ParsedReference:
    kind: str  # ref | company | seed | chapter | context | exception
    target: str  # group.name | field | as | chapter key | context name | class id
    path: tuple[str, ...]  # output path; for exception the inner reference


def parse_reference(value: str) -> ParsedReference:
    """Split a reference into its kind, target and path; refuse malformed ones."""
    if value.startswith(REF_PREFIX):
        rest = value[len(REF_PREFIX) :]
        parts = rest.split(".")
        if (
            len(parts) != 2
            or parts[0] not in SEED_GROUPS
            or not NAME_PATTERN.match(parts[1])
        ):
            raise ReferenceError(
                f"'{value}' must be $ref.<group>.<name> with a group of "
                f"{', '.join(SEED_GROUPS)}."
            )
        return ParsedReference("ref", rest, ())
    if value.startswith(COMPANY_PREFIX):
        rest = value[len(COMPANY_PREFIX) :]
        if rest not in COMPANY_FIELDS:
            raise ReferenceError(f"'{value}' must be $company.party.")
        return ParsedReference("company", rest, ())
    if value.startswith((SEED_PREFIX, CHAPTER_PREFIX)):
        kind = "seed" if value.startswith(SEED_PREFIX) else "chapter"
        prefix = SEED_PREFIX if kind == "seed" else CHAPTER_PREFIX
        parts = value[len(prefix) :].split(".")
        if len(parts) < 3 or parts[1] != "output" or not parts[0]:
            raise ReferenceError(f"'{value}' must be ${kind}.<key>.output.<field>.")
        return ParsedReference(kind, parts[0], tuple(parts[2:]))
    if value.startswith(CONTEXT_PREFIX):
        parts = value[len(CONTEXT_PREFIX) :].split(".")
        if not parts[0] or not NAME_PATTERN.match(parts[0]):
            raise ReferenceError(f"'{value}' must be $context.<name>[.<field>].")
        return ParsedReference("context", parts[0], tuple(parts[1:]))
    if value.startswith(EXCEPTION_PREFIX):
        rest = value[len(EXCEPTION_PREFIX) :]
        class_id, _, inner = rest.partition(".")
        if not CLASS_PATTERN.match(class_id) or not is_reference(inner):
            raise ReferenceError(
                f"'{value}' must be $exception.<class>.<reference to the record>."
            )
        return ParsedReference("exception", class_id, (inner,))
    raise ReferenceError(f"'{value}' is not a reference.")


def walk_strings(value: Any, path: str = "") -> list[tuple[str, str, str | None]]:
    """Every string leaf as (path, value, nearest key). Lists keep their parent's key."""
    found: list[tuple[str, str, str | None]] = []

    def visit(node: Any, where: str, key: str | None) -> None:
        if isinstance(node, str):
            found.append((where, node, key))
        elif isinstance(node, dict):
            for name, child in node.items():
                visit(child, f"{where}.{name}" if where else str(name), str(name))
        elif isinstance(node, list):
            for index, child in enumerate(node):
                visit(child, f"{where}[{index}]", key)

    visit(value, path, None)
    return found


def dig(payload: Any, path: tuple[str, ...]) -> Any:
    """Follow output paths such as ``commitment_ids[0]`` or ``records[document].id``.

    A numeric index selects a list element; a word selects the first element whose
    ``family`` (or ``kind``) is that word, which is how outputs shaped as
    ``records: [{family, id}]`` are addressed without counting.
    """
    current = payload
    for raw in path:
        segment = raw
        selectors: list[str] = []
        while segment.endswith("]"):
            head, _, tail = segment.rpartition("[")
            selectors.insert(0, tail[:-1])
            segment = head
        if segment:
            if isinstance(current, dict) and segment in current:
                current = current[segment]
            elif isinstance(current, list) and segment.isdigit():
                current = current[int(segment)]
            else:
                raise ReferenceError(f"Output has no field '{segment}'.")
        for selector in selectors:
            if not isinstance(current, list):
                raise ReferenceError(f"Output field is not a list before [{selector}].")
            if selector.isdigit():
                index = int(selector)
                if index >= len(current):
                    raise ReferenceError(f"Output has no element {index}.")
                current = current[index]
                continue
            match = next(
                (
                    element
                    for element in current
                    if isinstance(element, dict)
                    and (
                        element.get("family") == selector
                        or element.get("kind") == selector
                    )
                ),
                None,
            )
            if match is None:
                raise ReferenceError(f"Output has no element of family '{selector}'.")
            current = match
    return current


@dataclass
class ResolutionContext:
    """What a run knows when it resolves a chapter's declared input.

    ``refs`` maps seed groups to name -> opaque id, except ``terms`` which maps to the
    payment term *code*, because commands take terms by code. ``context_values`` holds
    the results of the chapter's ``context`` reads, keyed by their name.
    """

    start: datetime
    refs: dict[str, dict[str, str]] = field(default_factory=dict)
    company_party_id: str | None = None
    seed_outputs: dict[str, Any] = field(default_factory=dict)
    chapter_outputs: dict[str, Any] = field(default_factory=dict)
    context_values: dict[str, Any] = field(default_factory=dict)


def resolve_value(
    value: Any, context: ResolutionContext, *, key: str | None = None
) -> Any:
    """Replace every reference and relative date inside ``value``; refuse raw ids."""
    if isinstance(value, dict):
        return {
            name: resolve_value(child, context, key=str(name))
            for name, child in value.items()
        }
    if isinstance(value, list):
        return [resolve_value(child, context, key=key) for child in value]
    if not isinstance(value, str):
        return value
    if is_reference(value):
        return resolve_reference(value, context)
    if is_relative_date(value) and key in DATE_FIELDS:
        instant = parse_relative_date(value, context.start)
        return instant.date().isoformat() if key in DAY_FIELDS else instant.isoformat()
    if is_raw_identity(value):
        raise ReferenceError(f"Raw identity '{value}' is not allowed in a storyline.")
    return value


def resolve_reference(value: str, context: ResolutionContext) -> Any:
    parsed = parse_reference(value)
    if parsed.kind == "ref":
        group, name = parsed.target.split(".")
        try:
            return context.refs[group][name]
        except KeyError as exc:
            singular = {
                "parties": "party",
                "items": "item",
                "locations": "location",
                "terms": "term",
            }
            raise ReferenceError(
                f"Seed has no {singular.get(group, group)} named '{name}'."
            ) from exc
    if parsed.kind == "company":
        if not context.company_party_id:
            raise ReferenceError("The run has no company party yet.")
        return context.company_party_id
    if parsed.kind == "seed":
        if parsed.target not in context.seed_outputs:
            raise ReferenceError(f"Seed history has no result named '{parsed.target}'.")
        return dig(context.seed_outputs[parsed.target], parsed.path)
    if parsed.kind == "chapter":
        if parsed.target not in context.chapter_outputs:
            raise ReferenceError(
                f"Chapter '{parsed.target}' has not produced an output yet."
            )
        return dig(context.chapter_outputs[parsed.target], parsed.path)
    if parsed.kind == "context":
        if parsed.target not in context.context_values:
            raise ReferenceError(f"Context '{parsed.target}' was not read.")
        return dig(context.context_values[parsed.target], parsed.path)
    record_id = resolve_reference(parsed.path[0], context)
    if not isinstance(record_id, str) or not record_id:
        raise ReferenceError(f"'{value}' does not resolve to a record id.")
    return f"exc__{parsed.target}__{record_id}"
