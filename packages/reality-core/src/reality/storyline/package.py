"""The storyline package contract (spec 182, contracts/storyline-package.md).

One declarative file per story. This module knows its shape, validates it in four
passes against the catalogs and against itself, loads the built-in packages that
ship with the wheel, and exports the JSON Schema the docs publish. It never touches
a database: what a package *does* is the storyline service's business.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Iterable
from dataclasses import asdict, dataclass, field
from functools import lru_cache
from importlib import resources
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ValidationError,
    field_validator,
    model_validator,
)

from reality.storyline.references import (
    DATE_FIELDS,
    NAME_PATTERN,
    SEED_GROUPS,
    ReferenceError,
    is_raw_identity,
    is_reference,
    is_relative_date,
    parse_reference,
    walk_strings,
)

FORMAT_VERSION = 1
PACKAGE_BYTE_BOUND = 200_000
MAX_CHAPTERS = 60
MAX_HISTORY = 40
MAX_BRANCHES = 4
MAX_READS = 8
LANGUAGES = ("en", "de", "nl", "es")
KEY_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]{1,78}$")
FILE_SUFFIX = ".storyline.yaml"
SCHEMA_ID = "https://docs.runreality.ai/storylines/storyline.schema.json"


# --------------------------------------------------------------------------- shape


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Text(_Strict):
    """A text in the UI languages. ``en`` is required unless the text is a draft gap."""

    en: str | None = Field(default=None, max_length=4000)
    de: str | None = Field(default=None, max_length=4000)
    nl: str | None = Field(default=None, max_length=4000)
    es: str | None = Field(default=None, max_length=4000)
    missing: bool = False

    @model_validator(mode="after")
    def _english_or_missing(self) -> Text:
        if not self.missing and not (self.en or "").strip():
            raise ValueError("en is required")
        return self

    def languages(self) -> set[str]:
        return {code for code in LANGUAGES if (getattr(self, code) or "").strip()}

    def pick(self, language: str) -> str:
        return (getattr(self, language, None) or self.en or "").strip()


class Author(_Strict):
    name: str = Field(min_length=1, max_length=200)
    contact: str | None = Field(default=None, max_length=200)


class SeedParty(_Strict):
    role: Literal["customer", "supplier"]
    name: str = Field(min_length=1, max_length=200)
    payment_term: str | None = None  # $ref.terms.<name>


class SeedItem(_Strict):
    sku: str = Field(min_length=1, max_length=80)
    name: str = Field(min_length=1, max_length=200)
    unit: str = Field(default="pcs", max_length=20)
    price: str | None = Field(default=None, max_length=32)
    currency: str = Field(default="EUR", min_length=3, max_length=3)


class SeedLocation(_Strict):
    name: str = Field(min_length=1, max_length=200)


class SeedTerm(_Strict):
    code: str = Field(min_length=1, max_length=40)
    name: str | None = Field(default=None, max_length=200)
    days: int = Field(ge=0, le=365)
    discount_percent: str | None = Field(default=None, max_length=16)
    discount_days: int | None = Field(default=None, ge=0, le=365)


class HistoryEntry(_Strict):
    command: str = Field(min_length=1, max_length=120)
    at: str | None = None
    input: dict[str, Any] = Field(default_factory=dict)
    as_: str | None = Field(default=None, alias="as", max_length=40)

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    @field_validator("at")
    @classmethod
    def _relative(cls, value: str | None) -> str | None:
        if value is not None and not is_relative_date(value):
            raise ValueError("at must be a relative date such as -42d")
        return value

    @field_validator("as_")
    @classmethod
    def _name(cls, value: str | None) -> str | None:
        if value is not None and not NAME_PATTERN.match(value):
            raise ValueError("as must be a short lowercase name")
        return value


class Seed(_Strict):
    parties: dict[str, SeedParty] = Field(min_length=1)
    items: dict[str, SeedItem] = Field(min_length=1)
    locations: dict[str, SeedLocation] = Field(min_length=1)
    terms: dict[str, SeedTerm] = Field(default_factory=dict)
    history: list[HistoryEntry] = Field(default_factory=list, max_length=MAX_HISTORY)

    @model_validator(mode="after")
    def _names(self) -> Seed:
        for group in SEED_GROUPS:
            for name in getattr(self, group):
                if not NAME_PATTERN.match(name):
                    raise ValueError(
                        f"{group}.{name}: names are short lowercase identifiers"
                    )
        return self


class Read(_Strict):
    tool: str = Field(min_length=1, max_length=120)
    input: dict[str, Any] = Field(default_factory=dict)


class ContextRead(Read):
    """A read the service performs at preparation; its result feeds the input."""

    field: str | None = Field(default=None, max_length=200)


class Requires(_Strict):
    """What must hold before a chapter runs, beyond its references resolving."""

    findings_present: list[str] = Field(default_factory=list)
    findings_absent: list[str] = Field(default_factory=list)


class Branch(_Strict):
    key: str = Field(pattern=KEY_PATTERN.pattern)
    label: Text
    next: str = Field(pattern=KEY_PATTERN.pattern)
    default: bool = False


class Primary(_Strict):
    record_type: str = Field(min_length=1, max_length=40)
    from_: str = Field(alias="from", min_length=1, max_length=200)

    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class Expect(_Strict):
    raised: list[str] = Field(default_factory=list)
    cleared: list[str] = Field(default_factory=list)
    facts: list[str] = Field(default_factory=list)


class Chapter(_Strict):
    key: str = Field(pattern=KEY_PATTERN.pattern)
    title: Text
    situation: Text
    explain: Text
    view: str | None = Field(default=None, max_length=80)
    kind: Literal["command", "read", "unsupported"] = "command"
    command: str | None = Field(default=None, max_length=120)
    input: dict[str, Any] = Field(default_factory=dict)
    context: dict[str, ContextRead] = Field(default_factory=dict)
    reads: list[Read] = Field(default_factory=list, max_length=MAX_READS)
    requires: Requires = Field(default_factory=Requires)
    primary: Primary | None = None
    expect: Expect = Field(default_factory=Expect)
    next: str | None = Field(default=None, pattern=KEY_PATTERN.pattern)
    branches: list[Branch] = Field(default_factory=list, max_length=MAX_BRANCHES)
    reason: str | None = Field(default=None, max_length=400)  # drafts: why unsupported

    @model_validator(mode="after")
    def _kind_shape(self) -> Chapter:
        if self.kind == "command" and not self.command:
            raise ValueError("a command chapter names a command")
        if self.kind == "read" and (self.command or not self.reads):
            raise ValueError("a read chapter lists reads and names no command")
        if self.next and self.branches:
            raise ValueError("a chapter has either next or branches")
        for name in self.context:
            if not NAME_PATTERN.match(name):
                raise ValueError(
                    f"context.{name}: names are short lowercase identifiers"
                )
        return self


class StorylinePackage(_Strict):
    storyline: Literal[1]
    key: str = Field(pattern=KEY_PATTERN.pattern)
    version: int = Field(ge=1)
    title: Text
    summary: Text
    author: Author | None = None
    # The Tool Usage process this story plays, for the docs link (optional).
    process: str | None = Field(default=None, pattern=r"^[a-z][a-z0-9_]{0,60}$")
    seed: Seed
    chapters: list[Chapter] = Field(min_length=1, max_length=MAX_CHAPTERS)
    draft: bool = False

    def chapter(self, key: str) -> Chapter | None:
        return next((chapter for chapter in self.chapters if chapter.key == key), None)

    def successors(self, key: str) -> list[str]:
        chapter = self.chapter(key)
        if chapter is None:
            return []
        if chapter.branches:
            return [branch.next for branch in chapter.branches]
        return [chapter.next] if chapter.next else []

    def default_next(self, key: str) -> str | None:
        chapter = self.chapter(key)
        if chapter is None:
            return None
        if chapter.branches:
            return next(
                (branch.next for branch in chapter.branches if branch.default), None
            )
        return chapter.next

    def texts(self) -> Iterable[tuple[str, Text]]:
        yield "title", self.title
        yield "summary", self.summary
        for index, chapter in enumerate(self.chapters):
            where = f"chapters[{index}]"
            yield f"{where}.title", chapter.title
            yield f"{where}.situation", chapter.situation
            yield f"{where}.explain", chapter.explain
            for b, branch in enumerate(chapter.branches):
                yield f"{where}.branches[{b}].label", branch.label


# ---------------------------------------------------------------------- validation


@dataclass(frozen=True)
class Issue:
    path: str
    code: str
    detail: str


@dataclass
class ValidationResult:
    package: StorylinePackage | None
    errors: list[Issue] = field(default_factory=list)
    warnings: list[Issue] = field(default_factory=list)
    checksum: str = ""

    @property
    def ok(self) -> bool:
        return self.package is not None and not self.errors

    def as_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "errors": [asdict(issue) for issue in self.errors],
            "warnings": [asdict(issue) for issue in self.warnings],
            "checksum": self.checksum,
        }


class PackageTooLarge(ValueError):
    pass


class PackageUnreadable(ValueError):
    pass


def parse_document(raw: bytes | str, *, filename: str = "") -> dict[str, Any]:
    """Bytes to a mapping. The size bound is checked before anything is parsed."""
    data = raw.encode("utf-8") if isinstance(raw, str) else raw
    if len(data) > PACKAGE_BYTE_BOUND:
        raise PackageTooLarge(
            f"A storyline package is at most {PACKAGE_BYTE_BOUND} bytes; "
            f"this file has {len(data)}."
        )
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise PackageUnreadable("The file is not UTF-8 text.") from exc
    try:
        document = (
            json.loads(text)
            if filename.lower().endswith(".json")
            else yaml.safe_load(text)
        )
    except (yaml.YAMLError, json.JSONDecodeError) as exc:
        raise PackageUnreadable(
            f"The file is not readable YAML or JSON: {exc}"
        ) from exc
    if not isinstance(document, dict):
        raise PackageUnreadable("A storyline package is a mapping at the top level.")
    return document


def checksum(document: dict[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(document, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


@dataclass(frozen=True)
class CatalogIndex:
    """What the validator needs to know from the catalogs, resolved once per process.

    ``command:`` names the proposal tool (the ``TOOLS`` key that becomes
    ``ChangeProposal.type = tool:<name>``); ``schemas`` carries the MCP input schema
    of that tool where the capability guidance maps one.
    """

    commands: frozenset[str]
    reads: frozenset[str]
    schemas: dict[str, dict[str, Any]]
    views: frozenset[str]
    exception_classes: frozenset[str]
    fact_predicates: frozenset[str]


@lru_cache(maxsize=1)
def catalog_index() -> CatalogIndex:
    from reality.catalogs import WORKSPACE_CATALOG_FILE, load_application_catalog
    from reality.config import config_text
    from reality.mcp.catalog import tool_definitions
    from reality.tools.application import TOOLS

    catalog = load_application_catalog()
    guidance = catalog.get("capability_guidance") or {}
    mcp = {definition.name: definition for definition in tool_definitions()}
    schemas: dict[str, dict[str, Any]] = {}
    for mcp_name, entry in guidance.items():
        application = (entry or {}).get("application_tool")
        definition = mcp.get(mcp_name)
        if application and definition is not None:
            schemas[application] = definition.input_schema
    for name, definition in mcp.items():
        if name.endswith("_propose"):
            schemas.setdefault(name[: -len("_propose")], definition.input_schema)
        else:
            schemas.setdefault(name, definition.input_schema)
    workspace = yaml.safe_load(config_text(WORKSPACE_CATALOG_FILE)) or {}
    return CatalogIndex(
        commands=frozenset(name for name, tool in TOOLS.items() if tool.mutating),
        reads=frozenset(name for name, tool in TOOLS.items() if not tool.mutating),
        schemas=schemas,
        views=frozenset(str(view["key"]) for view in workspace.get("views") or []),
        exception_classes=frozenset(catalog.get("operational_exception_classes") or []),
        fact_predicates=frozenset(
            str(entry["predicate"]) for entry in catalog.get("fact_predicates") or []
        ),
    )


def validate_package(
    document: dict[str, Any],
    *,
    builtin: bool = False,
    index: CatalogIndex | None = None,
) -> ValidationResult:
    """Four passes; every error is collected so the person fixes the file once."""
    result = ValidationResult(package=None, checksum=checksum(document))
    encoded = len(json.dumps(document, sort_keys=True).encode())
    if encoded > PACKAGE_BYTE_BOUND:
        result.errors.append(
            Issue(
                "",
                "too_large",
                f"{encoded} bytes exceed the bound of {PACKAGE_BYTE_BOUND}.",
            )
        )
        return result
    try:
        package = StorylinePackage.model_validate(document)
    except ValidationError as exc:
        for error in exc.errors():
            path = ".".join(str(part) for part in error["loc"])
            result.errors.append(Issue(path, "shape", error["msg"]))
        return result
    result.package = package
    index = index or catalog_index()
    _check_catalog(package, index, result)
    _check_references(package, index, result)
    _check_languages(package, builtin, result)
    if package.draft:
        result.errors.append(
            Issue("draft", "draft", "A draft must be edited before it is imported.")
        )
    return result


def _check_catalog(
    package: StorylinePackage, index: CatalogIndex, result: ValidationResult
) -> None:
    for position, entry in enumerate(package.seed.history):
        where = f"seed.history[{position}]"
        if entry.command not in index.commands:
            result.errors.append(
                Issue(f"{where}.command", "unknown_command", entry.command)
            )
        else:
            _check_input(
                index.schemas.get(entry.command), entry.input, f"{where}.input", result
            )
    for position, chapter in enumerate(package.chapters):
        where = f"chapters[{position}]"
        if chapter.kind == "unsupported":
            result.errors.append(
                Issue(
                    where,
                    "unsupported",
                    chapter.reason or "This chapter cannot be expressed.",
                )
            )
        if chapter.command:
            if chapter.command not in index.commands:
                code = (
                    "not_a_command"
                    if chapter.command in index.reads
                    else "unknown_command"
                )
                result.errors.append(Issue(f"{where}.command", code, chapter.command))
            else:
                _check_input(
                    index.schemas.get(chapter.command),
                    chapter.input,
                    f"{where}.input",
                    result,
                )
        for name, read in chapter.context.items():
            _check_read(read, f"{where}.context.{name}", index, result)
        for r, read in enumerate(chapter.reads):
            _check_read(read, f"{where}.reads[{r}]", index, result)
        if chapter.view is not None:
            key = chapter.view.removeprefix("view:")
            if not chapter.view.startswith("view:") or key not in index.views:
                result.errors.append(
                    Issue(f"{where}.view", "unknown_view", chapter.view)
                )
        for group in ("raised", "cleared"):
            for class_id in getattr(chapter.expect, group):
                if class_id not in index.exception_classes:
                    result.errors.append(
                        Issue(
                            f"{where}.expect.{group}",
                            "unknown_exception_class",
                            class_id,
                        )
                    )
        for group in ("findings_present", "findings_absent"):
            for class_id in getattr(chapter.requires, group):
                if class_id not in index.exception_classes:
                    result.errors.append(
                        Issue(
                            f"{where}.requires.{group}",
                            "unknown_exception_class",
                            class_id,
                        )
                    )
        for predicate in chapter.expect.facts:
            if predicate not in index.fact_predicates:
                result.errors.append(
                    Issue(f"{where}.expect.facts", "unknown_fact_predicate", predicate)
                )


def _check_read(
    read: Read, path: str, index: CatalogIndex, result: ValidationResult
) -> None:
    if read.tool not in index.reads:
        code = "not_a_read" if read.tool in index.commands else "unknown_read"
        result.errors.append(Issue(f"{path}.tool", code, read.tool))
    else:
        _check_input(index.schemas.get(read.tool), read.input, f"{path}.input", result)


_JSON_TYPES: dict[str, tuple[type, ...]] = {
    "string": (str,),
    "integer": (int,),
    "number": (int, float),
    "boolean": (bool,),
    "array": (list,),
    "object": (dict,),
    "null": (type(None),),
}


def _check_input(
    schema: dict[str, Any] | None,
    value: dict[str, Any],
    path: str,
    result: ValidationResult,
) -> None:
    """A light structural check against the tool's MCP input schema.

    Required keys, unknown keys where the schema forbids them, enum members and
    scalar types. References and relative dates are placeholders and pass. This is
    deliberately not a full JSON Schema engine: the proposal path validates the
    resolved arguments again at run time, and a new dependency was rejected.
    """
    if not schema:
        return
    properties = schema.get("properties") or {}
    for name in schema.get("required") or []:
        if name not in value:
            result.errors.append(
                Issue(f"{path}.{name}", "missing_input", "required by the command")
            )
    if schema.get("additionalProperties") is False:
        for name in value:
            if name not in properties:
                result.errors.append(
                    Issue(f"{path}.{name}", "unknown_input", "not a parameter")
                )
    for name, child in value.items():
        spec = properties.get(name)
        if spec is None:
            continue
        _check_value(spec, child, f"{path}.{name}", result)


def _check_value(
    spec: dict[str, Any], value: Any, path: str, result: ValidationResult
) -> None:
    if is_reference(value) or is_relative_date(value):
        return
    options = spec.get("anyOf") or spec.get("oneOf") or [spec]
    if isinstance(value, dict) and "properties" in spec:
        _check_input(spec, value, path, result)
        return
    if isinstance(value, list) and isinstance(spec.get("items"), dict):
        for index, element in enumerate(value):
            _check_value(spec["items"], element, f"{path}[{index}]", result)
        return
    accepted = False
    for option in options:
        declared = option.get("type")
        types = [declared] if isinstance(declared, str) else list(declared or [])
        if not types or any(
            isinstance(value, _JSON_TYPES.get(t, (object,)))
            and not (t in {"integer", "number"} and isinstance(value, bool))
            for t in types
        ):
            accepted = True
            break
    if not accepted:
        result.errors.append(
            Issue(path, "wrong_type", f"expected {spec.get('type') or 'another type'}")
        )
        return
    enum = spec.get("enum")
    if enum and value not in enum:
        result.errors.append(
            Issue(path, "not_in_enum", f"one of {', '.join(map(str, enum))}")
        )


@dataclass
class _Scope:
    """What a reference may point at from one place in the package."""

    refs: dict[str, set[str]]
    seed_names: set[str]
    dominators: set[str]  # chapters that ran on every path to here
    context_names: set[str]
    index: CatalogIndex


def _check_references(
    package: StorylinePackage, index: CatalogIndex, result: ValidationResult
) -> None:
    seed = package.seed
    refs = {group: set(getattr(seed, group)) for group in SEED_GROUPS}
    empty = _Scope(refs, set(), set(), set(), index)
    for name, party in seed.parties.items():
        if party.payment_term is not None:
            _check_one(
                party.payment_term, f"seed.parties.{name}.payment_term", empty, result
            )
    seed_names: set[str] = set()
    for position, entry in enumerate(seed.history):
        scope = _Scope(refs, set(seed_names), set(), set(), index)
        for path, text, key in walk_strings(
            entry.input, f"seed.history[{position}].input"
        ):
            _check_string(text, path, key, scope, result)
        if entry.as_:
            if entry.as_ in seed_names:
                result.errors.append(
                    Issue(f"seed.history[{position}].as", "duplicate_name", entry.as_)
                )
            seed_names.add(entry.as_)

    keys = [chapter.key for chapter in package.chapters]
    for key in sorted({key for key in keys if keys.count(key) > 1}):
        result.errors.append(Issue("chapters", "duplicate_chapter", key))
    known = set(keys)
    successors: dict[str, list[str]] = {}
    for position, chapter in enumerate(package.chapters):
        where = f"chapters[{position}]"
        defaults = [branch for branch in chapter.branches if branch.default]
        if chapter.branches and len(defaults) != 1:
            result.errors.append(
                Issue(f"{where}.branches", "default_branch", "exactly one default")
            )
        for b, branch in enumerate(chapter.branches):
            if branch.next not in known:
                result.errors.append(
                    Issue(f"{where}.branches[{b}].next", "unknown_chapter", branch.next)
                )
        if chapter.next and chapter.next not in known:
            result.errors.append(
                Issue(f"{where}.next", "unknown_chapter", chapter.next)
            )
        successors[chapter.key] = [
            target for target in package.successors(chapter.key) if target in known
        ]

    if not keys:
        return
    start = keys[0]
    reachable = _reachable(start, successors)
    for key in keys:
        if key not in reachable:
            result.errors.append(Issue("chapters", "unreachable_chapter", key))
    if _has_cycle(keys, successors):
        result.errors.append(Issue("chapters", "cycle", "a chapter reaches itself"))
    dominators = _dominators(start, keys, successors)

    for position, chapter in enumerate(package.chapters):
        where = f"chapters[{position}]"
        scope = _Scope(
            refs,
            seed_names,
            dominators.get(chapter.key, set()),
            set(chapter.context),
            index,
        )
        dependencies: dict[str, set[str]] = {}
        for name, read in chapter.context.items():
            others = set(chapter.context) - {name}
            inner = _Scope(refs, seed_names, scope.dominators, others, index)
            dependencies[name] = set()
            for path, text, key in walk_strings(
                read.input, f"{where}.context.{name}.input"
            ):
                _check_string(text, path, key, inner, result)
                if text.startswith("$context."):
                    dependencies[name].add(text.split(".")[1])
        if _has_cycle(
            list(dependencies), {k: sorted(v) for k, v in dependencies.items()}
        ):
            result.errors.append(
                Issue(f"{where}.context", "cycle", "context reads depend on each other")
            )

        for path, text, key in walk_strings(chapter.input, f"{where}.input"):
            _check_string(text, path, key, scope, result)
        for r, read in enumerate(chapter.reads):
            for path, text, key in walk_strings(
                read.input, f"{where}.reads[{r}].input"
            ):
                _check_string(text, path, key, scope, result)
        if chapter.primary and not chapter.primary.from_.startswith("output."):
            result.errors.append(
                Issue(
                    f"{where}.primary.from", "primary_path", "must start with output."
                )
            )


def _check_string(text, path, key, scope: _Scope, result: ValidationResult) -> None:
    if is_reference(text):
        _check_one(text, path, scope, result)
    elif is_raw_identity(text):
        result.errors.append(Issue(path, "raw_identity", "raw identity is not allowed"))
    elif is_relative_date(text) and key not in DATE_FIELDS:
        result.errors.append(Issue(path, "relative_date_not_allowed_here", text))


def _check_one(text: str, path: str, scope: _Scope, result: ValidationResult) -> None:
    try:
        parsed = parse_reference(text)
    except ReferenceError as exc:
        result.errors.append(Issue(path, "bad_reference", str(exc)))
        return
    if parsed.kind == "ref":
        group, name = parsed.target.split(".")
        if name not in scope.refs.get(group, set()):
            result.errors.append(Issue(path, "unknown_ref", text))
    elif parsed.kind == "seed":
        if parsed.target not in scope.seed_names:
            result.errors.append(Issue(path, "unknown_seed_result", text))
    elif parsed.kind == "chapter":
        if parsed.target not in scope.dominators:
            result.errors.append(Issue(path, "chapter_not_earlier", text))
    elif parsed.kind == "context":
        if parsed.target not in scope.context_names:
            result.errors.append(Issue(path, "unknown_context", text))
    elif parsed.kind == "exception":
        if parsed.target not in scope.index.exception_classes:
            result.errors.append(Issue(path, "unknown_exception_class", parsed.target))
        _check_one(parsed.path[0], path, scope, result)


def _reachable(start: str, successors: dict[str, list[str]]) -> set[str]:
    seen = {start}
    stack = [start]
    while stack:
        node = stack.pop()
        for target in successors.get(node, ()):
            if target not in seen:
                seen.add(target)
                stack.append(target)
    return seen


def _dominators(
    start: str, keys: list[str], successors: dict[str, list[str]]
) -> dict[str, set[str]]:
    """For each chapter, the chapters that lie on every path from the start to it.

    A ``$chapter`` reference must name such a chapter: any path that skipped it
    would reach this chapter without the output it needs.
    """
    result: dict[str, set[str]] = {}
    for key in keys:
        if key == start:
            result[key] = set()
            continue
        dominated: set[str] = set()
        for candidate in keys:
            if candidate == key:
                continue
            pruned = {
                node: [t for t in targets if t != candidate]
                for node, targets in successors.items()
                if node != candidate
            }
            if key not in _reachable(start, pruned):
                dominated.add(candidate)
        result[key] = dominated
    return result


def _has_cycle(keys: list[str], successors: dict[str, list[str]]) -> bool:
    state: dict[str, int] = {}

    def visit(node: str) -> bool:
        if state.get(node) == 1:
            return True
        if state.get(node) == 2:
            return False
        state[node] = 1
        if any(visit(target) for target in successors.get(node, ())):
            return True
        state[node] = 2
        return False

    return any(visit(key) for key in keys)


def _check_languages(
    package: StorylinePackage, builtin: bool, result: ValidationResult
) -> None:
    for path, text in package.texts():
        if text.missing:
            result.errors.append(
                Issue(path, "missing_text", "text is still to be written")
            )
            continue
        absent = [code for code in LANGUAGES if code not in text.languages()]
        if not absent:
            continue
        issue = Issue(path, "missing_language", ", ".join(absent))
        (result.errors if builtin else result.warnings).append(issue)


# ------------------------------------------------------------------------ built-ins


def builtin_directory() -> Path:
    source = Path(__file__).resolve().parents[3] / "storylines"
    if source.is_dir():
        return source
    return Path(str(resources.files("reality") / "storylines"))


def builtin_documents() -> dict[str, dict[str, Any]]:
    """Built-in packages keyed by file stem, parsed but not validated."""
    documents: dict[str, dict[str, Any]] = {}
    directory = builtin_directory()
    if not directory.is_dir():
        return documents
    for path in sorted(directory.glob(f"*{FILE_SUFFIX}")):
        documents[path.name[: -len(FILE_SUFFIX)]] = parse_document(
            path.read_bytes(), filename=path.name
        )
    return documents


@lru_cache(maxsize=1)
def builtin_packages() -> tuple[ValidationResult, ...]:
    """Every built-in validated as a built-in (all four languages required)."""
    return tuple(
        validate_package(document, builtin=True)
        for document in builtin_documents().values()
    )


def json_schema() -> dict[str, Any]:
    schema = StorylinePackage.model_json_schema()
    schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    schema["$id"] = SCHEMA_ID
    schema["title"] = "Reality storyline package"
    return schema
