"""Shared live explanation reads for the Web, documentation, Chat and MCP."""

from __future__ import annotations

import ast
import builtins
import importlib
import inspect
import json
import os
import re
import time
import types
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from reality.domain.business_blueprints import Blueprint, CompareInput
from reality.services.business_blueprint_analysis import analyze_function, source_tree
from reality.services.business_blueprint_annotations import describe
from reality.services.business_blueprint_presentation import unavailable
from reality.services.business_blueprint_source import (
    PACKAGE_ROOT,
    SourceUnavailable,
    approved_callable,
    capture_source,
    digest_bytes,
    release_identity,
)
from reality.services.business_blueprint_tests import (
    APPROVED_TESTS,
    extract_scenarios,
    test_run,
)

ENTRY_KINDS = {"command", "tool", "action", "view", "projection", "exception"}
MAX_FUNCTIONS = 128
MAX_SCENARIOS = 200
MAX_TOTAL_SOURCE_BYTES = 1024 * 1024
MAX_ANALYSIS_SECONDS = 10.0
# Server-owned readers already used by the catalog-code endpoint.
VIEW_READERS = {
    "commitments": "tenant_commitment_control",
    "documents": "tenant_evidence_documents",
    "items": "list_items",
    "parties": "list_parties",
    "locations": "list_locations",
    "reservations": "list_reservations",
    "movements": "list_movements",
    "payments": "tenant_payments",
    "journal": "tenant_journal",
    "activity": "tenant_timeline",
    "sources_imports": "tenant_integrations",
    "commercial_terms": (
        "list_payment_terms",
        "list_price_lists",
        "list_pricing_groups",
    ),
}
# Generic framework/storage mechanics do not contain an alternate business decision.
MECHANICS = {
    "now",
    "uid",
    "get_tenant",
    "_tenant_record",
    "_require_business_mutation",
    "_commit_or_flush",
    "emit_business_event",
    "decimal",
    "utc_datetime",
    "day_text",
    "date_text",
    "_json_value",
}


def _inventory() -> dict[tuple[str, str], dict[str, Any]]:
    from reality.catalogs import runtime_application_catalog
    from reality.mcp.catalog import MCP_TOOL_CATALOG

    catalog = runtime_application_catalog()
    rows: dict[tuple[str, str], dict[str, Any]] = {}
    for kind, entries, key_name in (
        ("command", catalog["commands"], "service"),
        ("projection", catalog["projections"], "materialized_as"),
    ):
        for entry in entries:
            rows[kind, entry[key_name]] = {
                **entry,
                "key": entry[key_name],
                "kind": kind,
            }
    for workspace in catalog["workspaces"]:
        for kind, name in (("view", "views"), ("action", "actions")):
            for entry in workspace[name]:
                rows[kind, entry["key"]] = {**entry, "kind": kind}
    from reality.catalogs import load_operational_exception_catalog

    for entry in load_operational_exception_catalog().classes:
        rows["exception", entry["id"]] = {
            **entry,
            "key": entry["id"],
            "kind": "exception",
        }
    for tool in MCP_TOOL_CATALOG:
        rows["tool", tool.name] = {
            **tool.public_metadata(),
            "kind": "tool",
            "key": tool.name,
        }
    return rows


def _canonical_handler(function: Any) -> Any:
    while hasattr(function, "__wrapped__"):
        function = function.__wrapped__
    return function


def _bound_projection_keys(functions: list[Any], inventory: dict) -> set[str]:
    """Read fixed arguments to the actual shared adapter without executing it."""
    from reality.tools.application import _projection_read

    result: set[str] = set()
    for function in functions:
        try:
            tree = source_tree(capture_source(function))
            bindings = {
                **function.__globals__,
                **inspect.getclosurevars(function).nonlocals,
            }
        except (SourceUnavailable, TypeError, ValueError):
            continue
        local_names = set(function.__code__.co_varnames) | set(
            function.__code__.co_cellvars
        )
        for call in ast.walk(tree):
            if not isinstance(call, ast.Call) or not isinstance(call.func, ast.Name):
                continue
            if (
                call.func.id in local_names
                or bindings.get(call.func.id) is not _projection_read
            ):
                continue
            argument = (
                call.args[2]
                if len(call.args) > 2
                else next(
                    (
                        keyword.value
                        for keyword in call.keywords
                        if keyword.arg == "name"
                    ),
                    None,
                )
            )
            value = (
                argument.value
                if isinstance(argument, ast.Constant)
                else bindings.get(argument.id)
                if isinstance(argument, ast.Name) and argument.id not in local_names
                else None
            )
            if isinstance(value, str) and ("projection", value) in inventory:
                result.add(value)
    return result


def _roots(entry: dict[str, Any], inventory: dict) -> list[Any]:
    from reality.catalogs import _service
    from reality.mcp.catalog import MCP_TOOL_CATALOG
    from reality.tools.application import TOOLS

    kind = entry["kind"]
    if kind == "exception":
        from reality.services.exceptions import operational_exception_rows

        return [operational_exception_rows]
    if kind == "action":
        target = inventory.get(("command", entry.get("command", "")))
        return _roots(target, inventory) if target else []
    if kind == "view":
        target = inventory.get(("projection", entry.get("projection", "")))
        if target:
            return _roots(target, inventory)
        name = VIEW_READERS.get(entry["key"])
        if name:
            from reality.web import api

            return [
                getattr(api, item)
                for item in (name if isinstance(name, tuple) else (name,))
            ]
        return []
    if kind == "projection":
        from reality.services.projections import (
            NARROWED_BUILDERS,
            derive_projection_rows,
            projection_rows,
        )

        builder = NARROWED_BUILDERS.get(entry["key"])
        return [
            _canonical_handler(projection_rows),
            *([builder] if builder else []),
            derive_projection_rows,
            *[
                function
                for name in entry.get("related_services", [])
                if callable(function := _service(name))
            ],
        ]
    if kind == "tool":
        definition = next(t for t in MCP_TOOL_CATALOG if t.name == entry["key"])
        handler = definition.handler
        variables = (
            inspect.getclosurevars(handler).nonlocals
            if inspect.isfunction(handler)
            else {}
        )
        application_name = variables.get(
            "application_name", getattr(handler, "application_name", None)
        )
        if application_name in TOOLS:
            roots = [_canonical_handler(TOOLS[application_name].handler)]
            if approved_callable(handler):
                roots.insert(0, handler)
            for projection_key in sorted(_bound_projection_keys(roots, inventory)):
                roots.extend(_roots(inventory["projection", projection_key], inventory))
            return roots
        return [_canonical_handler(handler)] if approved_callable(handler) else []
    return [
        function
        for name in [entry.get("service"), *entry.get("related_services", [])]
        if name and callable(function := _service(name))
    ]


def discover(
    *, query: str = "", kind: str | None = None, cursor: int = 0, limit: int = 25
) -> dict:
    if kind and kind not in ENTRY_KINDS:
        raise ValueError("Unknown business entry kind")
    if cursor < 0 or not 1 <= limit <= 100 or len(query) > 200:
        raise ValueError("Invalid discovery bounds")
    inventory = _inventory()
    entries = []
    alternatives = []
    for identity, entry in sorted(inventory.items()):
        label = entry.get("label") or entry.get("name") or entry["key"]
        text = " ".join(
            str(entry.get(k, ""))
            for k in ("name", "label", "key", "description", "effect", "group")
        )
        if query.casefold() not in text.casefold():
            continue
        if kind and identity[0] != kind:
            alternatives.append(
                {"kind": identity[0], "key": identity[1], "label": label}
            )
            continue
        roots = _roots(entry, inventory)
        entries.append(
            {
                "kind": identity[0],
                "key": identity[1],
                "label": label,
                "status": "partial" if roots else "missing",
                "analysis": "not_analyzed",
                "roots": [
                    f"{f.__module__}.{f.__qualname__}"
                    for f in roots
                    if inspect.isfunction(f)
                ],
            }
        )
    end = cursor + limit
    return {
        "entries": entries[cursor:end],
        "total": len(entries),
        "next_cursor": end if end < len(entries) else None,
        "release": release_identity(),
        "alternative_entries": alternatives[:10] if not entries else [],
        "alternative_total": len(alternatives) if not entries else 0,
        "recovery_hint": (
            "No entry matched the requested kind. Matching entries exist in other kinds; explain one of the alternative identities or search without kind. An empty filtered search does not establish that rules or tests are absent."
            if not entries and alternatives
            else "An empty search does not prove that tests are absent; resolve the registered identity and retrieve its explanation before making an evidence claim."
            if not entries
            else ""
        ),
    }


def _resolve_calls(function: Any, tree: ast.AST) -> tuple[list[Any], list[str]]:
    """Resolve only names supplied by approved implementation, never by callers."""
    namespace = dict(function.__globals__)
    namespace.update(inspect.getclosurevars(function).nonlocals)
    for statement in ast.walk(tree):
        if (
            isinstance(statement, ast.ImportFrom)
            and statement.module
            and statement.module.startswith("reality.")
        ):
            module = importlib.import_module(statement.module)
            for alias in statement.names:
                namespace[alias.asname or alias.name] = getattr(
                    module, alias.name, None
                )
        elif isinstance(statement, ast.Import):
            for alias in statement.names:
                if alias.name.startswith("reality."):
                    namespace[alias.asname or alias.name] = importlib.import_module(
                        alias.name
                    )
    resolved: dict[str, Any] = {}
    missing: list[str] = []
    for call in ast.walk(tree):
        if not isinstance(call, ast.Call):
            continue
        fn = call.func
        value: Any = namespace.get(fn.id) if isinstance(fn, ast.Name) else None
        if isinstance(fn, ast.Attribute):
            parent = namespace.get(ast.unparse(fn.value))
            if isinstance(parent, types.ModuleType) and parent.__name__.startswith(
                "reality."
            ):
                value = getattr(parent, fn.attr, None)
        if inspect.isclass(value) and value.__module__.startswith(
            ("reality.services.", "reality.domain.")
        ):
            for member in vars(value).values():
                candidate = member.fget if isinstance(member, property) else member
                if (
                    approved_callable(candidate)
                    and getattr(candidate, "__code__", None)
                    and candidate.__code__.co_filename.endswith(".py")
                ):
                    resolved[candidate.__module__ + "." + candidate.__qualname__] = (
                        candidate
                    )
        if inspect.isfunction(value):
            value = _canonical_handler(value)
            if value.__name__ in MECHANICS:
                continue
            if approved_callable(value):
                resolved[value.__module__ + "." + value.__qualname__] = value
            elif value.__module__.startswith("reality."):
                missing.append(
                    "Dependency outside approved business source: "
                    + value.__module__
                    + "."
                    + value.__qualname__
                )
        elif (
            isinstance(fn, ast.Name)
            and fn.id not in namespace
            and fn.id not in vars(builtins)
        ):
            # A nested helper is included by its own AST; dynamic local callable use is explicit.
            local_functions = {
                n.name
                for n in ast.walk(tree)
                if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
            }
            if fn.id in local_functions:
                continue
            missing.append(
                "Unresolved dynamic local callable: "
                + function.__module__
                + "."
                + function.__qualname__
                + ":"
                + fn.id
            )
    return list(resolved.values()), missing


def _test_root() -> tuple[Path | None, dict]:
    configured = os.environ.get("REALITY_BLUEPRINT_EVIDENCE")
    if configured:
        root = Path(configured)
        try:
            manifest = json.loads((root / "manifest.json").read_text())
            if manifest.get("commit") != os.environ.get("REALITY_COMMIT", ""):
                return None, {}
            tests = root / "tests"
            for filename in APPROVED_TESTS:
                path = tests / filename
                if (
                    path.is_symlink()
                    or not path.resolve().is_relative_to(tests.resolve())
                    or manifest.get("tests", {}).get(filename)
                    != digest_bytes(path.read_bytes())
                ):
                    return None, {}
            return tests, manifest
        except (OSError, ValueError):
            return None, {}
    checkout = PACKAGE_ROOT.parents[1] / "tests"
    return (checkout, {}) if checkout.is_dir() else (None, {})


def explain(
    kind: str,
    key: str,
    *,
    language: str = "en",
    interpret: bool = True,
    brief: bool = False,
) -> Blueprint:
    inventory = _inventory()
    started = time.monotonic()
    entry = inventory.get((kind, key))
    if entry is None:
        raise ValueError("Unknown business entry")
    roots = _roots(entry, inventory)
    queue = [(fn, 0) for fn in roots]
    seen: set[str] = set()
    sources = []
    nodes = []
    edges = []
    limitations: list[str] = []
    runtime_values: dict[str, Any] = {}
    captured_functions = []
    source_callers: dict[str, set[str]] = {}
    total_source_bytes = 0
    status = "complete"
    if kind == "exception":
        limitations.append(
            "Source includes the shared exception evaluator, not a class-isolated implementation."
        )
        status = "partial"
    projection_keys = (
        {key}
        if kind == "projection"
        else {entry["projection"]}
        if entry.get("projection")
        else _bound_projection_keys(roots, inventory)
    )
    projection_key = next(iter(sorted(projection_keys)), None)
    if projection_key:
        limitations.append(
            "Source includes shared projection readers and derivation branches; "
            "the registered change builder can fall back to full derivation. "
            "Fixed projection bindings: " + ", ".join(sorted(projection_keys)) + "."
        )
        status = "partial"
    while queue:
        function, depth = queue.pop(0)
        identity = function.__module__ + "." + function.__qualname__
        if identity in seen:
            continue
        if (
            len(seen) >= MAX_FUNCTIONS
            or depth > 8
            or time.monotonic() - started > MAX_ANALYSIS_SECONDS
        ):
            limitations.append(
                "Analysis boundary reached; omitted dependency: " + identity
            )
            continue
        seen.add(identity)
        try:
            if function.__module__ == "reality.web.api" and function.__name__ in {
                name
                for value in VIEW_READERS.values()
                for name in (value if isinstance(value, tuple) else (value,))
            }:
                source = capture_source(function, approved_root=PACKAGE_ROOT)
            else:
                source = capture_source(function)
            if total_source_bytes + len(source.code.encode()) > MAX_TOTAL_SOURCE_BYTES:
                limitations.append(
                    "Source response boundary reached; omitted dependency: " + identity
                )
                continue
            if projection_key:
                from reality.services import projections

                role = "dependency"
                if function is _canonical_handler(projections.projection_rows):
                    role = "reader"
                elif any(
                    function is projections.NARROWED_BUILDERS.get(bound_key)
                    for bound_key in projection_keys
                ):
                    role = "builder"
                elif function is projections.derive_projection_rows:
                    role = "shared"
                source = source.model_copy(update={"role": role})
            total_source_bytes += len(source.code.encode())
            captured_functions.append(function)
            sources.append(source)
            limitations.extend(source.limitations)
            n, e, limits = analyze_function(source)
            nodes.extend(n)
            edges.extend(e)
            limitations.extend(limits)
            helpers, missing = _resolve_calls(function, source_tree(source))
            limitations.extend(missing)
            for helper in helpers:
                helper_identity = helper.__module__ + "." + helper.__qualname__
                source_callers.setdefault(helper_identity, set()).add(identity)
            queue.extend((helper, depth + 1) for helper in helpers)
            effective_values = {
                **function.__globals__,
                **inspect.getclosurevars(function).nonlocals,
            }
            for name in {*function.__code__.co_names, *function.__code__.co_freevars}:
                value = effective_values.get(name)
                if re.search(
                    r"secret|password|credential|token|private_key|api_key",
                    name,
                    re.IGNORECASE,
                ):
                    if isinstance(value, (str, int, bool)):
                        limitations.append(
                            "A sensitive runtime configuration binding is omitted."
                        )
                    continue
                if name in function.__code__.co_freevars and name != "application_name":
                    continue
                if (
                    isinstance(value, (str, int, bool))
                    or isinstance(value, (set, frozenset))
                    and all(isinstance(v, str) for v in value)
                ):
                    runtime_values[identity + ":" + name] = (
                        sorted(value) if isinstance(value, (set, frozenset)) else value
                    )
        except SourceUnavailable as error:
            limitations.append(str(error) + " (" + identity + ")")
            if "differ" in str(error):
                status = "outdated"
    sources = [
        source.model_copy(
            update={"called_by": tuple(sorted(source_callers.get(source.function, ())))}
        )
        for source in sources
    ]
    if len({n.id for n in nodes}) != len(nodes):
        raise ValueError("Duplicate shared rule identity")
    if not roots:
        limitations.append(
            "No approved running source root is registered for this entry."
        )
    test_root, manifest = _test_root()
    scenarios = []
    if test_root:
        names = {name.rsplit(".", 1)[-1] for name in seen}
        for filename in APPROVED_TESTS:
            if filename == "conftest.py":
                continue
            path = test_root / filename
            if not path.exists():
                continue
            try:
                expected = manifest.get("tests", {}).get(filename)
                if manifest and expected != digest_bytes(path.read_bytes()):
                    limitations.append(
                        "Test source differs from release evidence: " + filename
                    )
                    continue
                scenarios.extend(
                    extract_scenarios(
                        path, names, tuple(nodes), approved_root=test_root
                    )
                )
            except (OSError, ValueError, SyntaxError):
                limitations.append("Test evidence is unavailable: " + filename)
            if len(scenarios) > MAX_SCENARIOS:
                limitations.append(
                    "Scenario boundary reached; remaining test cases are not shown."
                )
                scenarios = scenarios[:MAX_SCENARIOS]
                break
    else:
        limitations.append(
            "Actual test source is unavailable for this running release."
        )
    if not scenarios:
        limitations.append(
            "No approved executable test definitions are linked to this entry; other test files were not inspected."
        )
    if language not in {"en", "de"}:
        limitations.append(
            "Business explanation language falls back to English; identifiers and source remain exact."
        )
    # Check source again after traversal; concurrent edits must not mix evidence versions.
    for function, source in zip(captured_functions, sources, strict=True):
        try:
            checked = capture_source(
                function,
                approved_root=PACKAGE_ROOT
                if function.__module__ == "reality.web.api"
                else None,
            )
            if checked.digest != source.digest:
                raise SourceUnavailable("Source changed during analysis.")
        except SourceUnavailable as error:
            status = "outdated"
            limitations.append(str(error))
    for scenario in scenarios:
        for relative, expected in [
            (scenario.path, scenario.digest),
            *[(h.path, h.digest) for h in scenario.helpers],
        ]:
            if test_root:
                path = test_root / relative.removeprefix("packages/reality-core/tests/")
                if (
                    not path.exists()
                    or path.is_symlink()
                    or digest_bytes(path.read_bytes()) != expected
                ):
                    status = "outdated"
                    limitations.append(
                        "Test evidence changed during analysis: " + relative
                    )
    provenance = release_identity()
    revision_digest = digest_bytes(
        json.dumps(
            {
                "sources": [(s.function, s.digest) for s in sources],
                "values": runtime_values,
            },
            sort_keys=True,
        ).encode()
    )
    gaps = tuple(n.id for n in nodes if n.kind == "decision") + tuple(
        f"{n.id}:predicate-{index}"
        for n in nodes
        for index, _ in enumerate(n.predicates, start=1)
    )
    # No execution/branch coverage is inferred from static associations.
    runs = manifest.get("runs", {})
    scenarios = [
        s.model_copy(
            update={
                "run": test_run(
                    runs.get(s.id, {}),
                    provenance["commit"],
                    test_digest=s.digest,
                    source_digest=revision_digest,
                )
            }
        )
        for s in scenarios
    ]
    consumers = tuple(
        f"{k}:{v}"
        for (k, v), row in inventory.items()
        if row.get("service") == entry.get("service")
        and row.get("service")
        or kind == "command"
        and row.get("command") == key
    )
    purpose = (
        entry.get("purpose")
        or entry.get("effect")
        or entry.get("description")
        or entry.get("calculation")
        or "Inspect the registered application logic."
    )
    requirements = tuple(
        sorted(
            set(
                re.findall(
                    r"(?:spec\s+\d+\s+)?(?:FR|DR)-\d{3}",
                    "\n".join(s.code for s in sources),
                )
            )
        )
    )
    presentation_language = "de" if language == "de" else "en"
    business = None
    if interpret:
        business = (
            unavailable(presentation_language, reason="source", outdated=True)
            if status == "outdated"
            else describe(tuple(nodes), tuple(sources), tuple(scenarios))
        )
        # Authored text must not outlive the verified source/test evidence.
        for function, source in zip(captured_functions, sources, strict=True):
            try:
                current = capture_source(
                    function,
                    approved_root=PACKAGE_ROOT
                    if function.__module__ == "reality.web.api"
                    else None,
                )
                if current.digest != source.digest:
                    raise SourceUnavailable("Source changed during interpretation.")
            except SourceUnavailable:
                status = "outdated"
                limitations.append(
                    "Source changed during interpretation; read live logic again."
                )
        for scenario in scenarios:
            for relative, expected in [
                (scenario.path, scenario.digest),
                *[(h.path, h.digest) for h in scenario.helpers],
            ]:
                if test_root:
                    path = test_root / relative.removeprefix(
                        "packages/reality-core/tests/"
                    )
                    if (
                        not path.exists()
                        or path.is_symlink()
                        or digest_bytes(path.read_bytes()) != expected
                    ):
                        status = "outdated"
                        limitations.append(
                            "Test evidence changed during interpretation; read live logic again."
                        )
        if status == "outdated":
            business = unavailable(
                presentation_language, reason="source", outdated=True
            )
    return Blueprint(
        kind=kind,
        key=key,
        label=entry.get("label") or entry.get("name") or key,
        purpose=purpose,
        release={**provenance, "source_digest": revision_digest},
        status=status
        if status == "outdated"
        else "missing"
        if not nodes
        else "partial"
        if limitations
        else "complete",
        limitations=tuple(dict.fromkeys(limitations)),
        nodes=tuple(nodes),
        edges=tuple(edges),
        sources=tuple(sources),
        scenarios=tuple(scenarios),
        test_gaps=gaps,
        requirements=requirements,
        consumers=consumers,
        inputs=tuple(
            str(p)
            for fn in roots
            for p in inspect.signature(fn).parameters
            if p not in {"session", "tenant_id"}
        ),
        outputs=tuple(entry.get("outputs", [])),
        prerequisites=tuple(entry.get("prerequisites", [])),
        runtime_values=runtime_values,
        presentation_language=presentation_language,
        business=business,
        evidence_digest=digest_bytes(
            json.dumps(
                {
                    "source": revision_digest,
                    "tests": [
                        (s.id, s.digest, [(h.id, h.digest) for h in s.helpers])
                        for s in scenarios
                    ],
                },
                sort_keys=True,
            ).encode()
        ),
    )


def source_for(kind: str, key: str, evidence_id: str) -> dict:
    if not re.fullmatch(r"[a-f0-9]{32}", evidence_id):
        raise ValueError("Unknown source evidence")
    blueprint = explain(kind, key, interpret=False)
    if blueprint.status == "outdated":
        raise SourceUnavailable("Current source cannot be established.")
    for source in blueprint.sources:
        if source.id == evidence_id:
            return source.model_dump(mode="json")
    for scenario in blueprint.scenarios:
        for helper in scenario.helpers:
            if helper.id == evidence_id:
                return helper.model_dump(mode="json")
    raise ValueError("Unknown source evidence")


def compare(session: Session, tenant_id: str, arguments: dict[str, Any]) -> dict:
    from reality.db.core import BusinessEvent, Commitment, Document, Party
    from reality.services import core
    from reality.services.credit_exposure import credit_exposure
    from reality.services.fulfillment_readiness import fulfillment_readiness

    request = CompareInput.model_validate(arguments)
    if request.record is not None and request.facts:
        raise ValueError("Supply either facts or one authorized record, not both")
    core.get_tenant(session, tenant_id)
    blueprint = explain(
        request.kind, request.key, language=request.language, interpret=False
    )
    if blueprint.status == "outdated":
        raise SourceUnavailable(
            "Running source is outdated; refresh/reload before comparing"
        )
    if request.evidence_digest and request.evidence_digest != blueprint.evidence_digest:
        raise ValueError(
            "Evidence changed; refresh the live explanation before comparing"
        )
    if len({f.name for f in request.facts}) != len(request.facts):
        raise ValueError("Case facts require unique names")
    supplied = {f.name: f.model_dump() for f in request.facts}
    links = []
    historical = []
    if request.record:
        ref = request.record
        model = {"party": Party, "order": Document, "commitment": Commitment}[ref.kind]
        record = core._tenant_record(session, model, tenant_id, ref.id)
        links.append({"kind": ref.kind, "id": record.id})
        if ref.kind == "order" and record.type != "sales_order":
            raise core.NotFound("Sales order not found")
        party_id = (
            record.id
            if ref.kind == "party"
            else record.party_id
            if ref.kind == "order"
            else record.to_party_id
        )
        if party_id:
            exposure = credit_exposure(session, tenant_id, party_id)
            supplied.update(
                {
                    name: {
                        "name": name,
                        "value": str(exposure[name]),
                        "currency": exposure["currency"],
                        "unit": None,
                    }
                    for name in ("credit_limit", "exposure", "over_limit")
                }
            )
            supplied["limit"] = {**supplied["credit_limit"], "name": "limit"}
            supplied["currency"] = {
                "name": "currency",
                "value": exposure["currency"],
                "currency": None,
                "unit": None,
            }
        commitments = (
            [record]
            if ref.kind == "commitment"
            else list(
                session.scalars(
                    select(Commitment).where(
                        Commitment.tenant_id == tenant_id,
                        Commitment.document_id == record.id,
                    )
                )
            )
            if ref.kind == "order"
            else []
        )
        ids = {c.id for c in commitments}
        for commitment in commitments:
            if commitment.type == "customer_delivery":
                readiness = fulfillment_readiness(
                    session, tenant_id, commitment.id
                ).as_dict()
                supplied.update(
                    {
                        k: {
                            "name": k,
                            "value": str(v),
                            "currency": readiness["currency"]
                            if "amount" in k
                            else None,
                            "unit": None,
                        }
                        for k, v in readiness.items()
                        if isinstance(v, (str, bool))
                        and k not in {"order_id", "document_id", "commitment_id"}
                    }
                )
        if ids:
            for event in session.scalars(
                select(BusinessEvent)
                .where(
                    BusinessEvent.tenant_id == tenant_id,
                    BusinessEvent.event_type == "commitment.held",
                    BusinessEvent.subject_id.in_(ids),
                )
                .order_by(BusinessEvent.occurred_at.desc())
                .limit(20)
            ):
                payload = json.loads(event.payload)
                if payload.get("reason_code") == "credit_check":
                    historical.append(
                        {
                            "event_id": event.id,
                            "recorded_at": str(event.occurred_at),
                            "facts": payload.get("credit"),
                            "rule_version": "unknown",
                        }
                    )
        if hasattr(record, "document_id") and record.document_id:
            links.append({"kind": "document", "id": record.document_id})
        if hasattr(record, "source_record_id") and record.source_record_id:
            links.append({"kind": "source_record", "id": record.source_record_id})
    scenarios = {s.id: s for s in blueprint.scenarios}
    selected = request.scenario_ids or list(scenarios)[:20]
    if any(identity not in scenarios for identity in selected):
        raise ValueError("Unknown executable test scenario")
    results = []
    for identity in selected:
        scenario = scenarios[identity]
        facts = []
        # Conflicting facts cannot be silently reduced to the last value.
        grouped: dict[str, list] = {}
        for fact in scenario.facts:
            grouped.setdefault(fact.name, []).append(fact)
        for name, values in grouped.items():
            given = supplied.get(name)
            expected = {str(f.value) for f in values}
            dimensions = {(f.currency, f.unit) for f in values}
            state = "unknown"
            if (
                given
                and given["value"] is not None
                and len(expected) == 1
                and len(dimensions) == 1
            ):
                currency, unit = next(iter(dimensions))
                missing_dimension = bool(currency) != bool(given["currency"]) or bool(
                    unit
                ) != bool(given["unit"])
                wrong_dimension = (
                    currency and given["currency"] and currency != given["currency"]
                ) or (unit and given["unit"] and unit != given["unit"])
                if wrong_dimension:
                    state = "different"
                elif not missing_dimension:
                    left, right = str(given["value"]), next(iter(expected))
                    try:
                        equal = (
                            Decimal(left).is_finite()
                            and Decimal(right).is_finite()
                            and Decimal(left) == Decimal(right)
                        )
                    except InvalidOperation:
                        equal = (
                            left.casefold() == right.casefold()
                            if right in {"True", "False"}
                            else left == right
                        )
                    state = "matching" if equal else "different"
            facts.append(
                {
                    "name": name,
                    "test_values": sorted(expected),
                    "case_value": given,
                    "status": state,
                }
            )
        results.append(
            {
                "scenario_id": identity,
                "rules": list(scenario.rules),
                "test_digest": scenario.digest,
                "conditions": facts,
                "unknown_assumptions": list(scenario.assumptions),
                "untested_aspects": [
                    "A matching example does not prove this case's result or execution path."
                ],
            }
        )
    return {
        "release": blueprint.release,
        "evidence_digest": blueprint.evidence_digest,
        "status": blueprint.status,
        "context": "current_state" if request.record else "caller_supplied",
        "evaluated_at": core.now().isoformat(),
        "case_facts": list(supplied.values()),
        "comparisons": results,
        "links": links,
        "recorded_decisions": historical,
        "historical_rule_version": "unknown",
        "limitations": list(blueprint.limitations)
        + [
            "No matching test"
            if not results
            else "Fixture assumptions remain explicit; no operation was executed."
        ],
    }
