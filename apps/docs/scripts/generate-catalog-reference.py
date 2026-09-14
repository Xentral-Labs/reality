"""Render the executable Reality catalogs as the public Tool Usage reference.

One model is built from the YAML catalogs and the MCP registry, with the links between
commands, agent tools, views, projections, actions, exceptions and events resolved once.
It is written twice: as JSON for the interactive explorer and as man-page-style Markdown
for search, permalinks and printing, in every documentation language.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[3]
CONFIG = ROOT / "packages/reality-core/config"
CONTENT = ROOT / "apps/docs/content"
DATA = ROOT / "apps/docs/.vitepress/data"
SECTION = "tool-usage"


def load(name: str) -> dict[str, Any]:
    return yaml.safe_load((CONFIG / name).read_text())


# --- business areas -----------------------------------------------------------------------
# The catalogs carry no business area of their own; the reference groups every entry by the
# vocabulary in its key so an ERP consultant finds finance next to finance. First match wins.

AREAS: list[tuple[str, str, str, str]] = [
    ("missing_information", "Missing information", "Fehlende Informationen", r"reality_gap"),
    ("agent_governance", "Agent governance", "Agentensteuerung", r"proposal|capability_describe|business_records_discover"),
    ("company", "Company & access", "Unternehmen & Zugang", r"invitation|remove_member|member_invite|member_remove|tenant"),
    ("master_data", "Master data & pricing", "Stammdaten & Preise", r"payment_term|price|party_group|group_price|master_data|^(?:create|update)_(?:party|item|location)|^(?:party|item|location)_(?:create|update)|^parties$|^items$|^locations$|commercial|assign_party"),
    ("finance", "Finance", "Finanzen", r"financ|payment|invoice|credit|refund|ledger|account|settlement|adjustment|opening|component|reference|mapping|target|matrix|balance|journal|open_items|billed|receivable|payable|discount"),
    ("orders", "Orders & fulfilment", "Aufträge & Erfüllung", r"commitment|reserv|fulfillment|order|return|stale|promise|hold|shipped|delivery"),
    ("warehouse", "Warehouse & logistics", "Lager & Logistik", r"movement|inventory|lot|serial|handling_unit|stock|supply_demand|expired|shipment|package|received|warehouse"),
    ("sources", "Documents, sources & facts", "Belege, Quellen & Facts", r"source|connector|interpretation|document|fact|ingest|import|integration"),
]
AREA_OVERRIDES = {
    "hold_party_delivery": "orders",
    "party_delivery_hold_propose": "orders",
    "party_delivery_hold_release_propose": "orders",
    "hold_document_commitments": "orders",
    "document_hold_propose": "orders",
    "document_hold_release_propose": "orders",
    "set_master_data_active": "master_data",
    "sold_below_purchase_price": "finance",
    "invoice_price_differs": "finance",
    "exceptions": "cross_functional",
    "timeline": "cross_functional",
    "activity": "cross_functional",
    "documents": "sources",
}
DEFAULT_AREA = ("cross_functional", "Cross-functional", "Bereichsübergreifend")


def area_for(key: str) -> str:
    if key in AREA_OVERRIDES:
        return AREA_OVERRIDES[key]
    for area, _, _, pattern in AREAS:
        if re.search(pattern, key):
            return area
    return DEFAULT_AREA[0]


def area_label(area: str, de: bool) -> str:
    for key, en, german, _ in [*AREAS, DEFAULT_AREA + ("",)]:
        if key == area:
            return german if de else en
    return area


# --- model ------------------------------------------------------------------------------------


def inline_refs(schema: Any, defs: dict[str, Any], depth: int = 0) -> Any:
    """Replace `$ref` pointers into `$defs` with the definition itself, so nested rows can
    be read off the schema directly. Pydantic-generated schemas use them for row models."""
    if depth > 32:
        return {}
    if isinstance(schema, dict):
        ref = schema.get("$ref")
        if isinstance(ref, str) and ref.startswith("#/$defs/"):
            return inline_refs(defs.get(ref.split("/")[-1], {}), defs, depth + 1)
        return {k: inline_refs(v, defs, depth + 1) for k, v in schema.items() if k != "$defs"}
    if isinstance(schema, list):
        return [inline_refs(item, defs, depth + 1) for item in schema]
    return schema


def concrete(spec: dict[str, Any]) -> dict[str, Any]:
    """Collapse `anyOf`/`oneOf` unions with `null` to their one concrete branch."""
    branches = spec.get("anyOf") or spec.get("oneOf")
    if not branches:
        return spec
    real = [b for b in branches if isinstance(b, dict) and b.get("type") != "null"]
    if len(real) == 1:
        merged = {k: v for k, v in spec.items() if k not in {"anyOf", "oneOf"}}
        merged.update(real[0])
        return merged
    return spec


def schema_type(schema: dict[str, Any]) -> str:
    schema = concrete(schema)
    raw = schema.get("type")
    if raw is None and (schema.get("anyOf") or schema.get("oneOf")):
        kinds = [b.get("type") for b in (schema.get("anyOf") or schema.get("oneOf")) if isinstance(b, dict)]
        return " | ".join(str(k) for k in kinds if k and k != "null") or "any"
    if raw is None:
        return "any"
    if isinstance(raw, list):
        return " | ".join(str(x) for x in raw if x != "null") or "null"
    return str(raw)


def parameters(
    schema: dict[str, Any], glossary: dict[str, str], prefix: str = "", depth: int = 0
) -> list[dict[str, Any]]:
    """Flatten an input schema into rows; nested objects and arrays of objects become
    `parent.field` and `parent[].field` rows so a reader sees every field a tool takes."""
    if depth == 0 and schema.get("$defs"):
        schema = inline_refs(schema, schema.get("$defs", {}))
    required = set(schema.get("required", []))
    rows = []
    for name, raw_spec in schema.get("properties", {}).items():
        spec = concrete(raw_spec)
        row: dict[str, Any] = {
            "name": prefix + name,
            "type": schema_type(spec),
            "required": name in required,
            "description": str(spec.get("description") or glossary.get(name) or ""),
            "depth": depth,
        }
        if "default" in spec:
            row["default"] = spec["default"]
        if spec.get("enum"):
            row["enum"] = [v for v in spec["enum"] if v is not None]
        items = spec.get("items") if row["type"] == "array" else None
        if isinstance(items, dict) and items.get("enum"):
            row["enum"] = [v for v in items["enum"] if v is not None]
        rows.append(row)
        if isinstance(items, dict) and items.get("properties"):
            rows.extend(parameters(items, glossary, prefix + name + "[].", depth + 1))
        elif row["type"] == "object" and spec.get("properties"):
            rows.extend(parameters(spec, glossary, prefix + name + ".", depth + 1))
    return rows


def synopsis(name: str, params: list[dict[str, Any]]) -> str:
    top = [p for p in params if p.get("depth", 0) == 0]
    parts = [p["name"] if p["required"] else f"[{p['name']}]" for p in top]
    return " ".join([name, *parts])


# Documentation of concrete adapter paths, not an alternate business-rule registry.
READ_MODE_DEFINITIONS = {
    "stored": {
        "label": {"en": "Stored — updated in background", "de": "Vorberechnet — im Hintergrund aktualisiert"},
        "description": {
            "en": "Reads the last completed projection. Opening or refreshing the page does not calculate or enqueue it; the shared scheduler and worker update it after relevant committed business events.",
            "de": "Liest die zuletzt fertig berechnete Projektion. Öffnen oder Aktualisieren der Seite berechnet sie nicht neu und stellt keinen Job ein; Scheduler und Worker aktualisieren sie nach relevanten abgeschlossenen Business Events.",
        },
    },
    "live": {
        "label": {"en": "Live — read at request time", "de": "Live — beim Aufruf gelesen"},
        "description": {
            "en": "Reads or derives results from the records currently held by Reality for this request. This does not mean that external systems were just synchronized.",
            "de": "Liest oder berechnet das Ergebnis beim Aufruf aus den aktuell in Reality vorhandenen Datensätzen. Das bedeutet nicht, dass externe Systeme gerade synchronisiert wurden.",
        },
    },
    "parameterized": {
        "label": {"en": "Live — calculated for your inputs", "de": "Live — für deine Eingaben berechnet"},
        "description": {
            "en": "Calculates the answer when requested for the supplied customer, item, quantity, currency, unit and date. Price resolution uses current canonical rules and does not read a stored price projection.",
            "de": "Berechnet die Antwort beim Aufruf für den angegebenen Geschäftspartner, Artikel, die Menge, Währung, Einheit und den Zeitpunkt. Die Preisermittlung verwendet die aktuellen Preisregeln und keine gespeicherte Preisprojektion.",
        },
    },
}

# These are the five _projection_read adapters in tools/application.py. MCP selects
# page by default; direct application callers retain the legacy default.
MCP_PROJECTION_READS = {
    "inventory_read": "inventory",
    "commitments_list": "commitment_register",
    "fulfillment_queue": "fulfillment_queue",
    "fulfillment_blockers": "fulfillment_blockers",
    "item_supply_demand": "item_supply_demand",
}
LIVE_VIEW_PATHS = {
    "commitments": ["/commitment-control"],
    "documents": ["/evidence-documents"],
    "reservations": ["/reservations"],
    "movements": ["/movements"],
    "items": ["/items"],
    "locations": ["/locations"],
    "parties": ["/parties"],
    "payments": ["/finance/payments"],
    "journal": ["/finance/journal"],
    "activity": ["/timeline"],
    "sources_imports": ["/integrations"],
    "commercial_terms": ["/payment-terms", "/price-lists", "/pricing-groups"],
}


def http_read(path: str, mode: str) -> dict[str, Any]:
    return {"query": "GET /api/tenants/{tenant}" + path, "mode": mode}


def tool_read_modes(tool: Any) -> list[dict[str, Any]]:
    if tool.access != "read":
        return []
    if tool.name in MCP_PROJECTION_READS:
        formats = tool.input_schema["properties"]["response_format"]
        if formats["default"] != "page" or set(formats["enum"]) != {"page", "legacy"}:
            raise ValueError(f"Review documented MCP read modes: {tool.name}")
        return [
            {"query": f"MCP {tool.name}(response_format=page)", "mode": "live", "default": True},
            {"query": f"MCP {tool.name}(response_format=legacy)", "mode": "stored"},
        ]
    return [{"query": f"MCP {tool.name}", "mode": "live", "default": True}]


def view_read_modes(view: dict[str, Any]) -> list[dict[str, Any]]:
    projection = view.get("projection")
    modes = (
        [http_read("/projection-snapshots/" + projection, "stored")]
        if projection else [http_read(path, "live") for path in LIVE_VIEW_PATHS[view["key"]]]
    )
    if projection in {"fulfillment_queue", "fulfillment_blockers", "item_supply_demand"}:
        modes.append(http_read("/projection-views/" + projection, "stored"))
    if view["key"] == "inventory":
        modes.append(http_read("/warehouse/stock", "live"))
    if view["key"] == "open_items":
        modes.extend(http_read("/finance/open-items?flow=" + flow, "stored") for flow in ("receivable", "payable"))
        modes.extend(http_read("/finance/open-items?flow=" + flow, "live") for flow in (
            "customer-credit", "customer-balance", "supplier-balance", "customer-balances", "supplier-balances"
        ))
    return modes


GUIDANCE_KEYS = (
    "purpose",
    "use_when",
    "do_not_use_when",
    "preconditions",
    "refusals",
    "verification_reads",
    "limitations",
    "empty_result",
    "freshness",
    "idempotency",
)


def guidance_of(raw: dict[str, Any] | None) -> dict[str, Any]:
    if not raw:
        return {}
    return {key: raw[key] for key in GUIDANCE_KEYS if raw.get(key)}


def build_model() -> dict[str, Any]:
    os.environ.setdefault(
        "REALITY_DATABASE_URL", "postgresql+psycopg://unused:unused@localhost/unused"
    )
    from reality.mcp.catalog import tool_definitions
    from reality.services.projections import MATERIALIZED_PROJECTIONS, TIME_SENSITIVE_PROJECTIONS

    command_catalog = load("command_catalog.yaml")
    glossary: dict[str, str] = command_catalog["parameter_descriptions"]
    commands = command_catalog["commands"]
    coverage: dict[str, dict[str, Any]] = command_catalog["agent_command_coverage"]
    guidance: dict[str, dict[str, Any]] = command_catalog["capability_guidance"]
    events = load("business_event_catalog.yaml")["events"]
    projections = load("projection_catalog.yaml")["projections"]
    exceptions = load("operational_exception_catalog.yaml")["classes"]
    workspace = load("workspace_catalog.yaml")
    tools = list(tool_definitions())

    projection_keys = {p["materialized_as"] for p in projections}
    tool_by_name = {t.name: t for t in tools}
    command_of_tool: dict[str, str] = {}
    for service, entry in coverage.items():
        for tool in entry.get("tools", []):
            command_of_tool.setdefault(tool, service)

    entries: list[dict[str, Any]] = []

    def link(kind: str, key: str) -> str:
        return f"{kind}:{key}"

    # Agent tools ---------------------------------------------------------------------------
    for tool in tools:
        raw_guidance = guidance.get(tool.name)
        params = parameters(tool.input_schema, glossary)
        related_projections = sorted(
            {
                *(x for x in (raw_guidance or {}).get("data_basis", []) if x in projection_keys),
                *(
                    x["name"]
                    for x in (raw_guidance or {}).get("verification_reads", [])
                    if x.get("name") in projection_keys
                ),
            }
        )
        command = command_of_tool.get(tool.name)
        entries.append(
            {
                "id": link("tool", tool.name),
                "kind": "tool",
                "key": tool.name,
                "label": tool.label,
                "area": area_for(tool.name),
                "summary": tool.description,
                "access": tool.access,
                "group": tool.group[:1].upper() + tool.group[1:],
                "synopsis": synopsis(tool.name, params),
                "parameters": params,
                "guidance": guidance_of(raw_guidance),
                "read_modes": tool_read_modes(tool),
                "command": command,
                "projections": related_projections,
                "links": [
                    *([link("command", command)] if command else []),
                    *(link("projection", p) for p in related_projections),
                ],
            }
        )

    # Business commands ---------------------------------------------------------------------
    actions_of_command: dict[str, list[str]] = {}
    for action in workspace["actions"]:
        actions_of_command.setdefault(action["command"], []).append(action["key"])
    events_of_command: dict[str, list[str]] = {}
    for event in events:
        events_of_command.setdefault(event["producer"], []).append(event["type"])

    for command in commands:
        service = command["service"]
        tool_names = coverage.get(service, {}).get("tools", [])
        merged_guidance: dict[str, Any] = {}
        for name in tool_names:
            merged_guidance = guidance_of(guidance.get(name))
            if merged_guidance:
                break
        entries.append(
            {
                "id": link("command", service),
                "kind": "command",
                "key": service,
                "label": command["name"],
                "area": area_for(service),
                "summary": command["effect"],
                "mode": command["mode"],
                "adapters": command.get("adapters", []),
                "reads": command.get("reads", []),
                "writes": command.get("writes", []),
                "confirmation": command.get("confirmation"),
                "related_services": command.get("related_services", []),
                "tools": tool_names,
                "synopses": [
                    synopsis(name, parameters(tool_by_name[name].input_schema, glossary))
                    for name in tool_names
                    if name in tool_by_name
                ],
                "events": events_of_command.get(service, []),
                "actions": actions_of_command.get(service, []),
                "guidance": merged_guidance,
                "links": [
                    *(link("tool", n) for n in tool_names),
                    *(link("action", a) for a in actions_of_command.get(service, [])),
                    *(link("event", e) for e in events_of_command.get(service, [])),
                    *(link("command", r) for r in command.get("related_services", [])),
                ],
            }
        )

    # Workspaces, views, actions ---------------------------------------------------------------
    workspaces_of_view: dict[str, list[str]] = {}
    workspaces_of_action: dict[str, list[str]] = {}
    for space in workspace["workspaces"]:
        for view in space.get("views", []):
            workspaces_of_view.setdefault(view, []).append(space["key"])
        for action in space.get("actions", []):
            workspaces_of_action.setdefault(action, []).append(space["key"])
        entries.append(
            {
                "id": link("workspace", space["key"]),
                "kind": "workspace",
                "key": space["key"],
                "label": space["label"],
                "area": DEFAULT_AREA[0],
                "summary": "",
                "views": space.get("views", []),
                "actions": space.get("actions", []),
                "complete_navigation": bool(space.get("complete_navigation")),
                "links": [
                    *(link("view", v) for v in space.get("views", [])),
                    *(link("action", a) for a in space.get("actions", [])),
                ],
            }
        )

    views_of_projection: dict[str, list[str]] = {}
    view_by_route: dict[str, str] = {}
    for view in workspace["views"]:
        view_by_route[view["route"]] = view["key"]
        if view.get("projection"):
            views_of_projection.setdefault(view["projection"], []).append(view["key"])
        entries.append(
            {
                "id": link("view", view["key"]),
                "kind": "view",
                "key": view["key"],
                "label": view["label"],
                "area": area_for(view["key"]),
                "summary": view["description"],
                "route": view["route"],
                "view_kind": view["kind"],
                "read_modes": view_read_modes(view),
                "projection": view.get("projection"),
                "workspaces": workspaces_of_view.get(view["key"], []),
                "links": [
                    *([link("projection", view["projection"])] if view.get("projection") else []),
                    *(link("workspace", w) for w in workspaces_of_view.get(view["key"], [])),
                ],
            }
        )

    for action in workspace["actions"]:
        target_view = view_by_route.get(action["target_route"])
        entries.append(
            {
                "id": link("action", action["key"]),
                "kind": "action",
                "key": action["key"],
                "label": action["label"],
                "area": area_for(action["command"]),
                "summary": "",
                "command": action["command"],
                "target_route": action["target_route"],
                "confirmation": action["confirmation"],
                "prerequisites": action.get("prerequisites", []),
                "result_kind": action.get("result_kind"),
                "workspaces": workspaces_of_action.get(action["key"], []),
                "links": [
                    link("command", action["command"]),
                    *([link("view", target_view)] if target_view else []),
                    *(link("workspace", w) for w in workspaces_of_action.get(action["key"], [])),
                ],
            }
        )

    # Projections -----------------------------------------------------------------------------
    tools_of_projection: dict[str, list[str]] = {}
    for entry in entries:
        if entry["kind"] == "tool":
            for p in entry["projections"]:
                tools_of_projection.setdefault(p, []).append(entry["key"])
    exception_ids = [x["id"] for x in exceptions]
    for projection in projections:
        key = projection["materialized_as"]
        if key not in MATERIALIZED_PROJECTIONS and key != "price_resolution":
            raise ValueError(f"Review documented projection mode: {key}")
        entries.append(
            {
                "id": link("projection", key),
                "kind": "projection",
                "key": key,
                "label": projection["name"],
                "area": area_for(key),
                "summary": projection["calculation"],
                "read_modes": [http_read("/projection-snapshots/" + key, "stored"), http_read("/projections/" + key, "stored")]
                if key in MATERIALIZED_PROJECTIONS else [http_read("/prices/resolve", "parameterized")],
                "refresh_events": [event["type"] for event in events if projection["name"] in event["invalidates"]],
                "clock_refresh_seconds": 60 if key in TIME_SENSITIVE_PROJECTIONS else None,
                "service": projection["service"],
                "related_services": projection.get("related_services", []),
                "consumers": projection.get("consumers", []),
                "reads": projection.get("reads", []),
                "outputs": projection.get("outputs", []),
                "views": views_of_projection.get(key, []),
                "tools": tools_of_projection.get(key, []),
                "links": [
                    *(link("view", v) for v in views_of_projection.get(key, [])),
                    *(link("tool", t) for t in tools_of_projection.get(key, [])),
                    *(link("exception", x) for x in (exception_ids if key == "exceptions" else [])),
                ],
            }
        )

    # Operational exceptions -----------------------------------------------------------------
    view_keys = {v["key"] for v in workspace["views"]}
    for exception in exceptions:
        record_view = next(
            (v for v in (exception["record_type"] + "s", exception["record_type"]) if v in view_keys),
            None,
        )
        entries.append(
            {
                "id": link("exception", exception["id"]),
                "kind": "exception",
                "key": exception["id"],
                "label": exception["label"],
                "area": area_for(exception["id"]),
                "summary": exception["description"],
                "owner": exception["owner"],
                "clears_through": exception["clears_through"],
                "severity": exception["severity"],
                "record_type": exception["record_type"],
                "authority": exception["authority"],
                "evidence": exception.get("evidence", []),
                "causes": [
                    {"id": c["id"], "label": c["label"], "authority": c["authority"]}
                    for c in exception.get("causes", [])
                ],
                "links": [
                    link("projection", "exceptions"),
                    link("tool", "exceptions_list"),
                    link("tool", "exception_explain"),
                    *([link("view", record_view)] if record_view else []),
                ],
            }
        )

    # Business events -------------------------------------------------------------------------
    for event in events:
        entries.append(
            {
                "id": link("event", event["type"]),
                "kind": "event",
                "key": event["type"],
                "label": event["type"],
                "area": area_for(event["producer"]),
                "summary": "",
                "producer": event["producer"],
                "subject": event["subject"],
                "invalidates": event.get("invalidates", []),
                "links": [link("command", event["producer"])],
            }
        )

    known = {e["id"] for e in entries}
    for entry in entries:
        entry["links"] = [x for x in dict.fromkeys(entry["links"]) if x in known and x != entry["id"]]

    resource_catalog = load("resource_catalog.yaml")
    resources, processes = attach_resources(entries, resource_catalog)

    return {
        "read_mode_definitions": READ_MODE_DEFINITIONS,
        "sources": [
            "command_catalog.yaml",
            "business_event_catalog.yaml",
            "projection_catalog.yaml",
            "operational_exception_catalog.yaml",
            "workspace_catalog.yaml",
            "reality/mcp/catalog.py",
        ],
        "areas": [
            {"key": key, "label": {"en": en, "de": de}}
            for key, en, de, _ in [*AREAS, DEFAULT_AREA + ("",)]
        ],
        "resources": resources,
        "processes": processes,
        "entries": entries,
    }


LABEL_SECTIONS = {
    "command": "commands",
    "view": "views",
    "projection": "projections",
    "exception": "exceptions",
    "workspace": "workspaces",
}


def attach_resources(
    entries: list[dict[str, Any]], catalog: dict[str, Any]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Group the executable vocabulary by business resource and validate every reference."""
    by_id = {e["id"]: e for e in entries}
    german = catalog.get("labels", {}).get("de", {})
    for entry in entries:
        section = LABEL_SECTIONS.get(entry["kind"])
        entry["label_de"] = german.get(section, {}).get(entry["key"], entry["label"]) if section else entry["label"]

    generic = set(catalog.get("generic_tables", []))
    definitions = catalog["resources"]
    problems: list[str] = []

    def require(entry_id: str, where: str) -> None:
        if entry_id not in by_id:
            problems.append(f"{where}: unknown {entry_id}")

    def matches(definition: dict[str, Any], key: str) -> bool:
        return bool(definition.get("match")) and re.search(definition["match"], key) is not None

    def by_tables(definition: dict[str, Any], tables: list[str]) -> bool:
        return bool(set(definition.get("tables", [])) & (set(tables) - generic))

    explicit: dict[str, set[str]] = {}
    for definition in definitions:
        for kind, field in (("view", "views"), ("projection", "projections"), ("exception", "exceptions")):
            for key in definition.get(field, []):
                require(f"{kind}:{key}", f"resource {definition['key']}.{field}")
                explicit.setdefault(f"{kind}:{key}", set()).add(definition["key"])

    for entry in entries:
        found: set[str] = set(explicit.get(entry["id"], set()))
        kind = entry["kind"]
        if kind == "command":
            found |= {d["key"] for d in definitions if matches(d, entry["key"])}
            if not found:
                found |= {d["key"] for d in definitions if by_tables(d, entry["writes"])}
            if not found:
                found |= {d["key"] for d in definitions if by_tables(d, entry["reads"])}
        elif kind in {"view", "projection", "exception"}:
            if not found:
                found |= {d["key"] for d in definitions if matches(d, entry["key"])}
        entry["resources"] = sorted(found)

    for entry in entries:
        kind = entry["kind"]
        if kind == "tool":
            source = by_id.get(f"command:{entry['command']}") if entry.get("command") else None
            found = set(source["resources"]) if source else set()
            if not found:
                found = {d["key"] for d in definitions if matches(d, entry["key"])}
            if not found:
                for projection in entry.get("projections", []):
                    found |= set(by_id.get(f"projection:{projection}", {}).get("resources", []))
            entry["resources"] = sorted(found)
        elif kind == "action":
            entry["resources"] = list(by_id.get(f"command:{entry['command']}", {}).get("resources", []))
        elif kind == "event":
            source = by_id.get(f"command:{entry['producer']}")
            found = set(source["resources"]) if source else set()
            if not found:
                found = {d["key"] for d in definitions if entry["subject"] in d.get("tables", [])}
            if not found:
                found = {d["key"] for d in definitions if matches(d, entry["key"])}
            entry["resources"] = sorted(found)
        elif kind == "workspace":
            entry["resources"] = []

    resources: list[dict[str, Any]] = []
    for definition in definitions:
        members = [e for e in entries if definition["key"] in e["resources"]]
        ids = lambda kind, predicate=lambda e: True: [e["id"] for e in members if e["kind"] == kind and predicate(e)]
        lists = ids("view") + ids("projection")
        resources.append(
            {
                "key": definition["key"],
                "label": definition["label"],
                "subtitle": definition.get("subtitle", {}),
                "description": definition.get("description", {}),
                "synonyms": definition.get("synonyms", []),
                "tables": definition.get("tables", []),
                "lists": lists,
                "actions": ids("command", lambda e: e["mode"] == "mutation"),
                "reads": ids("command", lambda e: e["mode"] != "mutation"),
                "exceptions": ids("exception"),
                "tools": ids("tool", lambda e: not e.get("command")),
                "events": ids("event"),
                "workspace_actions": ids("action"),
            }
        )

    resource_keys = {d["key"] for d in definitions}
    processes: list[dict[str, Any]] = []
    for process in catalog.get("processes", []):
        steps = []
        for index, step in enumerate(process.get("steps", []), start=1):
            where = f"process {process['key']} step {index}"
            if step.get("resource") not in resource_keys:
                problems.append(f"{where}: unknown resource {step.get('resource')}")
            resolved = {
                "title": step["title"],
                "resource": step.get("resource"),
                "actions": [f"command:{k}" for k in step.get("actions", [])],
                "tools": [f"tool:{k}" for k in step.get("tools", [])],
                "lists": [
                    f"view:{k}" if f"view:{k}" in by_id else f"projection:{k}" for k in step.get("lists", [])
                ],
                "exceptions": [f"exception:{k}" for k in step.get("exceptions", [])],
            }
            for field in ("actions", "tools", "lists", "exceptions"):
                for entry_id in resolved[field]:
                    require(entry_id, f"{where}.{field}")
            steps.append(resolved)
        processes.append(
            {
                "key": process["key"],
                "label": process["label"],
                "summary": process.get("summary", {}),
                "playbook": process.get("playbook"),
                "steps": steps,
            }
        )

    for section, kind in ((v, k) for k, v in LABEL_SECTIONS.items()):
        for key in german.get(section, {}):
            require(f"{kind}:{key}", f"labels.de.{section}")

    unassigned = [e["id"] for e in entries if e["kind"] not in {"workspace"} and not e["resources"]]
    if unassigned:
        problems.append("entries without a business resource: " + ", ".join(unassigned))
    if problems:
        raise SystemExit("resource_catalog.yaml is inconsistent:\n  " + "\n  ".join(problems))
    return resources, processes


# --- markdown -----------------------------------------------------------------------------------

PAGE_OF_KIND = {
    "resource": "resources",
    "process": "processes",
    "command": "commands",
    "tool": "commands",
    "workspace": "views",
    "view": "views",
    "action": "views",
    "projection": "views",
    "exception": "exceptions",
    "event": "events",
}

COPY = {
    "en": {
        "generated": "Automatically generated from `{source}`. Do not edit this page by hand.",
        "resources_title": "Business resources",
        "resources_intro": "The business objects an ERP professional works with, each with the lists that show it, the actions that change it, the exceptions it can raise, and the technology underneath. Names follow ERP usage; the technical key stands beside each one.",
        "processes_title": "Business processes",
        "processes_intro": "The processes a consultant walks through, step by step: which object, which action, which list to check afterwards, and which exceptions a step can leave behind. The agent playbooks carry the narrative; these pages index the executable vocabulary.",
        "also_called": "Also called",
        "lists": "Lists",
        "actions_of": "Actions",
        "lookups": "Look up",
        "exceptions_of": "Exceptions to clear",
        "in_processes": "Appears in processes",
        "technical": "Underneath",
        "tables": "Tables",
        "events_of": "Events",
        "agent_tools_of": "Agent tools without a command",
        "read_playbook": "Read the playbook",
        "play_storyline": "Play it as a storyline",
        "storylines_title": "Storylines",
        "storylines_intro": "Storylines are the playground for getting to know Reality. Pick one, press Start, and play a real business flow step by step in a sandbox of your own, an order from creation to the month-end review, or a purchase from the order to the discounted payment. Nothing you do here touches a real company, so try things: confirm, discard, take the other branch, leave the story and poke around in the sandbox, come back. Every step is an ordinary command or an ordinary read. You see the situation, prepare the step, read the preview, confirm, and then read what Reality recorded: which events, records and Facts were added and which findings a rule raised or cleared, and why. That is the point of a storyline, watching the rules work on evidence instead of reading about them.\n\nOpen **Storyline** in the navigation of the app. The library shows the storylines and where you are in each; a card starts or continues one. While playing, the step card on the left tells the story, the middle shows the view the step names in the app itself, and the protocol on the right lists every call with its input, result and catalog entry, and below it what the step added. Click any call, record or finding and you land on its ordinary page. Free play lets you leave the story and work in the sandbox; the protocol keeps recording. Autoplay runs the steps on a timer for a presentation and stops at any click.\n\nBuild your own and pass them around. The files below are the packages Reality ships, plain YAML with symbolic references: download one, change the texts, amounts or steps, and import it into your library. A run you played by hand can be exported as a draft storyline, so the fastest way to a new one is to play it once and fill in the texts. Send a package to a colleague, a customer or us; it is checked against the catalogs on import and runs under exactly the rules a built-in one runs under. The schema lets an editor complete the format.",
        "storylines_files": "Files",
        "storyline_schema": "Package schema (JSON Schema)",
        "storyline_download": "Download the package",
        "storyline_chapters": "Steps",
        "storyline_default_path": "Default path",
        "storyline_alternative": "Alternative reached by a branch",
        "chapter": "Step",
        "chapter_kind": "Kind",
        "chapter_command": "Command or reads",
        "chapter_view": "View",
        "chapter_expect": "Findings expected",
        "raised": "raised",
        "cleared": "cleared",
        "kind_read": "read",
        "kind_command_chapter": "command",
        "step": "Step",
        "object": "Object",
        "check": "Check afterwards",
        "can_leave": "Can leave behind",
        "kind_command": "command",
        "kind_tool": "agent tool",
        "kind_view": "view",
        "kind_projection": "projection",
        "kind_action": "action",
        "kind_exception": "exception",
        "kind_event": "event",
        "kind_workspace": "workspace",
        "synopsis": "Synopsis",
        "reach": "Reach via",
        "confirmation": "Confirmation",
        "use_when": "Use when",
        "do_not_use_when": "Do not use when",
        "preconditions": "Preconditions",
        "refusals": "Refused when",
        "parameters": "Parameters",
        "no_parameters": "No parameters.",
        "effect": "Effect",
        "reads": "Reads",
        "writes": "Writes",
        "emits": "Emits",
        "verify": "Verify with",
        "see_also": "See also",
        "name": "Name",
        "type": "Type",
        "required": "Required",
        "description": "Description",
        "default": "Default",
        "yes": "yes",
        "no": "no",
        "key": "Key",
        "label": "Label",
        "area": "Area",
        "access": "Access",
        "tools": "Agent tools",
        "answers": "Answers",
        "agent_only_intro": "These agent tools do not stand for one business command. Read tools answer a view or projection; governance tools carry proposals, discovery and missing information.",
        "commands_title": "Business commands",
        "commands_intro": "Every shared state-changing or reading operation, written like a manual page: what it does, how an agent calls it, which parameters it takes, and what to read afterwards. CLI, Web, API, Chat and MCP all reach the same operation.",
        "agent_only_title": "Agent tools without a business command",
        "read_modes": "How this query runs",
        "query": "Concrete query",
        "refresh_events": "Background refresh after",
        "clock_refresh": "Also eligible for background refresh every 60 seconds, without a new business event.",
        "refresh_note": "Events make stored results eligible for background work; they do not synchronously rebuild every view. Unknown event types conservatively invalidate stored projections. During delays or worker outages, the last completed result remains visible. Time-sensitive exceptions, commitment risk and tenant activity also become eligible every minute. A new company or builder version is initialized in the background. Command validation still uses authoritative records.",
        "states_note": "Snapshot metadata reports `uninitialized` (awaiting first calculation), `ready` (caught up to known relevant events), `pending` (an update is due) or `failed` (calculation failed). `completed_at` is the completed calculation time; processed and target event sequences describe local progress. Missing data before the first calculation is not an empty business result. Upstream freshness remains unknown.",
        "adapter_note": "The mode belongs to a concrete query, not to a business name. The Inspector can read stored inventory while the Warehouse page and the default MCP inventory page read live records. MCP page is the default for the five operational page tools; explicit response_format=legacy reads stored results. Direct application-tool callers retain the legacy default. The catalog's Art/Kind column describes its view definition, not every Web screen with a similar name. All HTTP paths below are tenant-scoped GET requests.",
        "views_title": "Views, projections and actions",
        "views_intro": "Where an operator looks and what they can trigger there. A view is either an authoritative register or a materialized projection; an action starts a business command.",
        "workspaces": "Workspaces",
        "views": "Views",
        "projections": "Projections",
        "actions": "Actions",
        "route": "Route",
        "kind": "Kind",
        "projection": "Projection",
        "command": "Command",
        "prerequisites": "Prerequisites",
        "consumers": "Consumers",
        "outputs": "Outputs",
        "workspace_of": "Workspaces",
        "exceptions_title": "Operational exceptions",
        "exceptions_intro": "Deterministically derived conditions that need attention. Each one names who owns it, what clears it, and which agent tools list and explain it.",
        "owner": "Owner",
        "clears_through": "Clears through",
        "severity": "Severity",
        "record_type": "Record type",
        "authority": "Authority",
        "evidence": "Evidence",
        "causes": "Causes",
        "events_title": "Business events",
        "events_intro": "Events connect a business command to the timeline and to the views it invalidates.",
        "event": "Event",
        "producer": "Producer",
        "subject": "Subject",
        "invalidates": "Invalidates",
    },
    "de": {
        "generated": "Automatisch aus `{source}` erzeugt. Diese Seite nicht von Hand bearbeiten.",
        "resources_title": "Ressourcen",
        "resources_intro": "Die Fachobjekte, mit denen ein ERP-Berater arbeitet, jeweils mit den Listen, die es zeigen, den Aktionen, die es verändern, den Klärfällen, die es auslösen kann, und der Technik darunter. Die Namen folgen dem ERP-Sprachgebrauch; der technische Schlüssel steht daneben.",
        "processes_title": "Geschäftsprozesse",
        "processes_intro": "Die Prozesse, die ein Berater Schritt für Schritt durchgeht: welches Objekt, welche Aktion, welche Liste danach zu prüfen ist und welche Klärfälle ein Schritt hinterlassen kann. Die Agenten-Playbooks erzählen den Ablauf; diese Seiten sind der Index in das ausführbare Vokabular.",
        "also_called": "Auch genannt",
        "lists": "Listen",
        "actions_of": "Aktionen",
        "lookups": "Nachschlagen",
        "exceptions_of": "Klärfälle",
        "in_processes": "Kommt vor in",
        "technical": "Darunter",
        "tables": "Tabellen",
        "events_of": "Events",
        "agent_tools_of": "Agenten-Tools ohne Geschäftsaktion",
        "read_playbook": "Playbook lesen",
        "play_storyline": "Als Storyline spielen",
        "storylines_title": "Storylines",
        "storylines_intro": "Storylines sind der Spielplatz, um Reality kennenzulernen. Wähle eine, drücke Starten und spiele einen echten Geschäftsablauf Schritt für Schritt in einer eigenen Sandbox, einen Auftrag von der Anlage bis zum Monatsrückblick oder einen Einkauf von der Bestellung bis zur Zahlung mit Skonto. Nichts, was du hier tust, berührt ein echtes Unternehmen, also probiere aus: bestätige, verwirf, nimm den anderen Abzweig, verlasse die Storyline und stöbere in der Sandbox, komm zurück. Jeder Schritt ist ein gewöhnlicher Befehl oder eine gewöhnliche Lesung. Du siehst die Situation, bereitest den Schritt vor, liest die Vorschau, bestätigst und liest dann, was Reality aufgezeichnet hat: welche Ereignisse, Datensätze und Fakten dazukamen und welche Abweichungen eine Regel gehoben oder geschlossen hat, und warum. Genau darum geht es: den Regeln bei der Arbeit auf Evidenz zuzusehen, statt darüber zu lesen.\n\nÖffne **Storyline** in der Navigation der App. Die Bibliothek zeigt die Storylines und wo du in jeder stehst; eine Karte startet oder setzt fort. Beim Spielen erzählt die Schrittkarte links die Geschichte, die Mitte zeigt die Ansicht, die der Schritt nennt, in der App selbst, und das Protokoll rechts listet jeden Aufruf mit Eingabe, Ergebnis und Katalogeintrag, darunter, was der Schritt hinzugefügt hat. Klicke auf einen Aufruf, einen Datensatz oder eine Abweichung, und du landest auf der gewohnten Seite dazu. Im freien Spiel verlässt du die Storyline und arbeitest in der Sandbox; das Protokoll zeichnet weiter auf. Die Automatik spielt die Schritte für eine Vorführung nach Zeit und hält bei jedem Klick an.\n\nBaue eigene und gib sie weiter. Die Dateien unten sind die Pakete, die Reality mitliefert, einfaches YAML mit symbolischen Verweisen: Lade eines herunter, ändere Texte, Beträge oder Schritte und importiere es in deine Bibliothek. Ein von Hand gespielter Durchlauf lässt sich als Storyline-Entwurf exportieren; der schnellste Weg zu einer neuen ist also, sie einmal zu spielen und die Texte zu ergänzen. Schick ein Paket einer Kollegin, einem Kunden oder uns; beim Import wird es gegen die Kataloge geprüft und läuft unter genau den Regeln wie eine eingebaute. Das Schema lässt einen Editor das Format vervollständigen.",
        "storylines_files": "Dateien",
        "storyline_schema": "Paketschema (JSON Schema)",
        "storyline_download": "Paket herunterladen",
        "storyline_chapters": "Schritte",
        "storyline_default_path": "Standardpfad",
        "storyline_alternative": "Alternative über eine Abzweigung",
        "chapter": "Schritt",
        "chapter_kind": "Art",
        "chapter_command": "Befehl oder Lesungen",
        "chapter_view": "Ansicht",
        "chapter_expect": "Erwartete Abweichungen",
        "raised": "gehoben",
        "cleared": "geschlossen",
        "kind_read": "Lesung",
        "kind_command_chapter": "Befehl",
        "step": "Schritt",
        "object": "Objekt",
        "check": "Danach prüfen",
        "can_leave": "Kann hinterlassen",
        "kind_command": "Geschäftsaktion",
        "kind_tool": "Agenten-Tool",
        "kind_view": "Sicht",
        "kind_projection": "Projection",
        "kind_action": "Aktion",
        "kind_exception": "Ausnahme",
        "kind_event": "Event",
        "kind_workspace": "Arbeitsbereich",
        "synopsis": "Aufruf",
        "reach": "Erreichbar über",
        "confirmation": "Bestätigung",
        "use_when": "Verwenden, wenn",
        "do_not_use_when": "Nicht verwenden, wenn",
        "preconditions": "Voraussetzungen",
        "refusals": "Abgelehnt, wenn",
        "parameters": "Parameter",
        "no_parameters": "Keine Parameter.",
        "effect": "Wirkung",
        "reads": "Liest",
        "writes": "Schreibt",
        "emits": "Erzeugt",
        "verify": "Prüfen mit",
        "see_also": "Siehe auch",
        "name": "Name",
        "type": "Typ",
        "required": "Pflicht",
        "description": "Beschreibung",
        "default": "Standard",
        "yes": "ja",
        "no": "nein",
        "key": "Schlüssel",
        "label": "Bezeichnung",
        "area": "Bereich",
        "access": "Zugriff",
        "tools": "Agenten-Tools",
        "answers": "Beantwortet",
        "agent_only_intro": "Diese Agenten-Tools stehen für keine einzelne Geschäftsaktion. Lese-Tools beantworten eine Sicht oder Projection; Steuerungs-Tools tragen Vorschläge, Erkundung und fehlende Informationen.",
        "commands_title": "Geschäftsaktionen",
        "commands_intro": "Jede gemeinsam implementierte ändernde oder lesende Operation, geschrieben wie eine Handbuchseite: was sie tut, wie ein Agent sie aufruft, welche Parameter sie nimmt und was danach zu lesen ist. CLI, Web, API, Chat und MCP erreichen dieselbe Operation.",
        "agent_only_title": "Agenten-Tools ohne Geschäftsaktion",
        "read_modes": "So wird diese Abfrage ausgeführt",
        "query": "Konkrete Abfrage",
        "refresh_events": "Hintergrundaktualisierung nach",
        "clock_refresh": "Zusätzlich alle 60 Sekunden für eine Hintergrundaktualisierung vorgesehen, auch ohne neues Business Event.",
        "refresh_note": "Events melden Aktualisierungsbedarf; sie berechnen nicht synchron jede Sicht neu. Unbekannte Event-Typen machen gespeicherte Projektionen vorsorglich aktualisierungsbedürftig. Bei Verzögerungen oder einem ausgefallenen Worker bleibt das letzte fertige Ergebnis sichtbar. Zeitabhängige Abweichungen, Verpflichtungsrisiken und Firmenaktivität werden zusätzlich jede Minute berücksichtigt. Neue Firmen und neue Berechnungsversionen werden im Hintergrund initialisiert. Aktionen prüfen weiterhin die maßgeblichen Datensätze.",
        "states_note": "Die Metadaten melden `uninitialized` (erste Berechnung ausstehend), `ready` (bekannte relevante Events verarbeitet), `pending` (Aktualisierung ausstehend) oder `failed` (Berechnung fehlgeschlagen). `completed_at` nennt den Zeitpunkt der fertigen Berechnung; verarbeitete und angestrebte Event-Sequenz zeigen den lokalen Fortschritt. Fehlende Daten vor der ersten Berechnung bedeuten nicht, dass es keine Geschäftsdaten gibt. Die Aktualität externer Quellen bleibt unbekannt.",
        "adapter_note": "Der Modus gehört zur konkreten Abfrage, nicht zum Geschäftsbegriff. Der Inspector kann den vorberechneten Bestand lesen, während die Lagerseite und die normale MCP-Bestandsabfrage live lesen. Bei den fünf operativen MCP-Seitenabfragen ist page der Standard; response_format=legacy liest gespeicherte Ergebnisse. Direkte Aufrufe der Anwendungstools behalten legacy als Standard. Die Spalte Art beschreibt die Katalogsicht und nicht jeden ähnlich benannten Web-Bildschirm. Alle HTTP-Pfade unten sind firmenbezogene GET-Abfragen.",
        "views_title": "Sichten, Projections und Aktionen",
        "views_intro": "Wo jemand hinschaut und was er dort auslösen kann. Eine Sicht ist entweder ein autoritatives Register oder eine materialisierte Projection; eine Aktion startet eine Geschäftsaktion.",
        "workspaces": "Arbeitsbereiche",
        "views": "Sichten",
        "projections": "Projections",
        "actions": "Aktionen",
        "route": "Route",
        "kind": "Art",
        "projection": "Projection",
        "command": "Geschäftsaktion",
        "prerequisites": "Voraussetzungen",
        "consumers": "Verbraucher",
        "outputs": "Ausgaben",
        "workspace_of": "Arbeitsbereiche",
        "exceptions_title": "Operative Ausnahmen",
        "exceptions_intro": "Deterministisch abgeleitete Zustände, die Aufmerksamkeit brauchen. Jede nennt, wer sie verantwortet, was sie auflöst und welche Agenten-Tools sie auflisten und erklären.",
        "owner": "Verantwortlich",
        "clears_through": "Aufgelöst durch",
        "severity": "Schwere",
        "record_type": "Datensatztyp",
        "authority": "Spezifikation",
        "evidence": "Nachweis",
        "causes": "Ursachen",
        "events_title": "Business Events",
        "events_intro": "Events verbinden eine Geschäftsaktion mit der Timeline und den Sichten, die sie ungültig machen.",
        "event": "Event",
        "producer": "Erzeuger",
        "subject": "Subjekt",
        "invalidates": "Invalidiert",
    },
}


def esc(text: str) -> str:
    return str(text).replace("|", "\\|").replace("\n", " ")


def table(headers: list[str], rows: list[list[str]]) -> str:
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    lines.extend("| " + " | ".join(esc(cell) for cell in row) + " |" for row in rows)
    return "\n".join(lines)


def codes(values: list[str]) -> str:
    return ", ".join(f"`{v}`" for v in values) if values else "—"


class Renderer:
    def __init__(self, model: dict[str, Any], locale: str) -> None:
        self.model = model
        self.locale = locale
        self.de = locale == "de"
        self.t = COPY["de" if self.de else "en"]
        self.by_id = {e["id"]: e for e in model["entries"]}

    def area(self, key: str) -> str:
        return area_label(key, self.de)

    def name(self, entry: dict[str, Any]) -> str:
        return entry.get("label_de", entry["label"]) if self.de else entry["label"]

    def text(self, value: dict[str, str] | str) -> str:
        if isinstance(value, dict):
            return value.get("de" if self.de else "en") or value.get("en", "")
        return value

    def named_ref(self, entry_id: str) -> str:
        entry = self.by_id.get(entry_id)
        if entry is None:
            return f"`{entry_id.split(':', 1)[1]}`"
        page = PAGE_OF_KIND[entry["kind"]]
        return f"[{self.name(entry)}](./{page}#{self.anchor(entry)}) (`{entry['key']}`)"

    def resources_page(self) -> str:
        t = self.t
        lines = self.front(t["resources_title"], t["resources_intro"], ["resource_catalog.yaml"])
        lines += [
            table(
                [t["object"], t["lists"], t["actions_of"], t["exceptions_of"]],
                [
                    [f"[{self.text(r['label'])}](#resource-{r['key']})", str(len(r["lists"])), str(len(r["actions"])), str(len(r["exceptions"]))]
                    for r in self.model["resources"]
                ],
            ),
            "",
        ]
        for r in self.model["resources"]:
            lines += [f"## {self.text(r['label'])} {{#resource-{r['key']}}}", "", f"*{self.text(r['subtitle'])}*", "", self.text(r["description"]), ""]
            if r["synonyms"]:
                lines += [f"**{t['also_called']}:** " + ", ".join(r["synonyms"]), ""]
            for field, label in (("lists", "lists"), ("actions", "actions_of"), ("reads", "lookups"), ("exceptions", "exceptions_of")):
                if r[field]:
                    lines += [f"**{t[label]}**", ""] + [f"- {self.named_ref(x)}" for x in r[field]] + [""]
            in_processes = [
                f"[{self.text(p['label'])}](./processes#process-{p['key']})"
                for p in self.model["processes"]
                if any(step["resource"] == r["key"] for step in p["steps"])
            ]
            if in_processes:
                lines += [f"**{t['in_processes']}:** " + ", ".join(in_processes), ""]
            technical = []
            if r["tables"]:
                technical.append(f"{t['tables']}: {codes(r['tables'])}")
            if r["events"]:
                technical.append(f"{t['events_of']}: " + ", ".join(self.ref(x) for x in r["events"]))
            if r["tools"]:
                technical.append(f"{t['agent_tools_of']}: " + ", ".join(self.ref(x) for x in r["tools"]))
            if technical:
                lines += [f"**{t['technical']}:** " + " · ".join(technical), ""]
        return "\n".join(lines)

    def processes_page(self) -> str:
        t = self.t
        lines = self.front(t["processes_title"], t["processes_intro"], ["resource_catalog.yaml"])
        resource_by_key = {r["key"]: r for r in self.model["resources"]}
        for p in self.model["processes"]:
            lines += [f"## {self.text(p['label'])} {{#process-{p['key']}}}", "", self.text(p["summary"]), ""]
            if p.get("playbook"):
                lines += [f"[{t['read_playbook']}](../agent-playbooks/{p['playbook']})", ""]
            for story in self.model.get("storylines", []):
                if story.get("process") == p["key"]:
                    lines += [f"[{t['play_storyline']}: {self.text(story['title'])}](../storylines/#storyline-{story['key']})", ""]
            for index, step in enumerate(p["steps"], start=1):
                resource = resource_by_key.get(step["resource"])
                lines += [f"### {index}. {self.text(step['title'])}", ""]
                if resource:
                    lines += [f"**{t['object']}:** [{self.text(resource['label'])}](./resources#resource-{resource['key']})", ""]
                if step["actions"] or step["tools"]:
                    lines += [f"**{t['actions_of']}**", ""] + [f"- {self.named_ref(x)}" for x in step["actions"] + step["tools"]] + [""]
                if step["lists"]:
                    lines += [f"**{t['check']}:** " + ", ".join(self.named_ref(x) for x in step["lists"]), ""]
                if step["exceptions"]:
                    lines += [f"**{t['can_leave']}:** " + ", ".join(self.named_ref(x) for x in step["exceptions"]), ""]
        return "\n".join(lines)

    def anchor(self, entry: dict[str, Any]) -> str:
        return f"{entry['kind']}-{entry['key'].replace('.', '-')}"

    def ref(self, entry_id: str, *, with_kind: bool = False) -> str:
        entry = self.by_id.get(entry_id)
        if entry is None:
            return f"`{entry_id.split(':', 1)[1]}`"
        text = f"[`{entry['key']}`](./{PAGE_OF_KIND[entry['kind']]}#{self.anchor(entry)})"
        return f"{self.t['kind_' + entry['kind']]} {text}" if with_kind else text

    def see_also(self, entry: dict[str, Any]) -> list[str]:
        if not entry["links"]:
            return []
        refs = ", ".join(self.ref(x, with_kind=True) for x in entry["links"])
        return [f"**{self.t['see_also']}:** {refs}", ""]

    def heading(self, level: int, entry: dict[str, Any]) -> str:
        title = f"`{entry['key']}`" + (f" — {entry['label']}" if entry["label"] != entry["key"] else "")
        return f"{'#' * level} {title} {{#{self.anchor(entry)}}}"

    def front(self, title: str, intro: str, sources: list[str]) -> list[str]:
        return [
            f"# {title}",
            "",
            intro,
            "",
            "> " + self.t["generated"].format(source="`, `".join(sources)),
            "",
        ]

    def parameter_table(self, params: list[dict[str, Any]]) -> list[str]:
        t = self.t
        if not params:
            return [t["no_parameters"], ""]
        rows = []
        for p in params:
            description = p["description"] or "—"
            if p.get("enum"):
                description = (description + " " if description != "—" else "") + codes(p["enum"])
            rows.append(
                [
                    f"`{p['name']}`",
                    f"`{p['type']}`",
                    t["yes"] if p["required"] else t["no"],
                    description,
                    f"`{p['default']}`" if "default" in p and p["default"] != "" else "—",
                ]
            )
        return [table([t["name"], t["type"], t["required"], t["description"], t["default"]], rows), ""]

    def read_mode_lines(self, entry: dict[str, Any]) -> list[str]:
        modes = entry.get("read_modes", [])
        if not modes:
            return []
        locale = "de" if self.de else "en"
        rows = [[f"`{read['query']}`", READ_MODE_DEFINITIONS[read["mode"]]["label"][locale], self.t["yes"] if read.get("default") else "—"] for read in modes]
        return [f"**{self.t['read_modes']}**", "", table([self.t["query"], self.t["kind"], self.t["default"]], rows), "", f"[{self.t['read_modes']}](./views#read-execution)", ""]

    def guidance_lines(self, guidance: dict[str, Any]) -> list[str]:
        t = self.t
        lines: list[str] = []
        for key in ("use_when", "do_not_use_when", "preconditions"):
            if guidance.get(key):
                lines += [f"**{t[key]}**", ""] + [f"- {x}" for x in guidance[key]] + [""]
        if guidance.get("refusals"):
            lines += [f"**{t['refusals']}**", ""]
            lines += [f"- `{r['code']}` — {r['description']}" for r in guidance["refusals"]]
            lines.append("")
        return lines

    def verify_lines(self, guidance: dict[str, Any]) -> list[str]:
        reads = guidance.get("verification_reads") or []
        if not reads:
            return []
        return [
            f"**{self.t['verify']}:** "
            + "; ".join(f"`{r['name']}` — {r['proves']}" for r in reads if r.get("name")),
            "",
        ]

    # pages -----------------------------------------------------------------------------------

    def command_block(self, entry: dict[str, Any], level: int) -> list[str]:
        t = self.t
        lines = [self.heading(level, entry), "", entry["summary"], ""]
        if entry["synopses"]:
            lines += [f"**{t['synopsis']}**", "", "```text", *entry["synopses"], "```", ""]
        reach = f"**{t['reach']}:** " + " · ".join(entry["adapters"]) if entry["adapters"] else ""
        if entry.get("confirmation"):
            reach += f" · **{t['confirmation']}:** `{entry['confirmation']}`"
        if reach:
            lines += [reach, ""]
        effect = [f"{t['reads']}: {codes(entry['reads'])}", f"{t['writes']}: {codes(entry['writes'])}"]
        if entry["events"]:
            effect.append(f"{t['emits']}: {codes(entry['events'])}")
        lines += [f"**{t['effect']}:** " + " · ".join(effect), ""]
        lines += self.see_also(entry)
        tools = [self.by_id[f"tool:{name}"] for name in entry["tools"] if f"tool:{name}" in self.by_id]
        if not tools:
            lines += [f"**{t['parameters']}**", "", t["no_parameters"], ""]
        for tool in tools:
            lines += self.tool_block(tool, level + 1)
        return lines

    def tool_block(self, entry: dict[str, Any], level: int) -> list[str]:
        t = self.t
        lines = [self.heading(level, entry), "", entry["summary"], ""]
        lines += [f"**{t['synopsis']}**", "", "```text", entry["synopsis"], "```", ""]
        lines += [f"**{t['access']}:** `{entry['access']}`", ""]
        lines += self.read_mode_lines(entry)
        if entry["guidance"].get("purpose"):
            lines += [entry["guidance"]["purpose"], ""]
        lines += self.guidance_lines(entry["guidance"])
        lines += [f"**{t['parameters']}**", ""] + self.parameter_table(entry["parameters"])
        lines += self.verify_lines(entry["guidance"])
        lines += self.see_also(entry)
        return lines

    def commands_page(self) -> str:
        t = self.t
        entries = [e for e in self.model["entries"] if e["kind"] == "command"]
        lines = self.front(t["commands_title"], t["commands_intro"], ["command_catalog.yaml", "reality/mcp/catalog.py"])
        lines += [
            table(
                [t["key"], t["label"], t["area"], t["tools"], t["reach"]],
                [
                    [
                        f"[`{e['key']}`](#{self.anchor(e)})",
                        e["label"],
                        self.area(e["area"]),
                        codes(e["tools"]),
                        " · ".join(e["adapters"]),
                    ]
                    for e in sorted(entries, key=lambda e: (e["area"], e["label"]))
                ],
            ),
            "",
        ]
        for area_key, *_ in [*AREAS, DEFAULT_AREA + ("",)]:
            group = sorted((e for e in entries if e["area"] == area_key), key=lambda e: e["label"])
            if not group:
                continue
            lines += [f"## {self.area(area_key)}", ""]
            for entry in group:
                lines += self.command_block(entry, 3)
        agent_only = [e for e in self.model["entries"] if e["kind"] == "tool" and not e["command"]]
        lines += [f"## {t['agent_only_title']}", "", t["agent_only_intro"], ""]
        lines += [
            table(
                [t["key"], t["label"], t["access"], t["answers"]],
                [
                    [f"[`{e['key']}`](#{self.anchor(e)})", e["label"], f"`{e['access']}`", codes(e["projections"])]
                    for e in agent_only
                ],
            ),
            "",
        ]
        for entry in agent_only:
            lines += self.tool_block(entry, 3)
        return "\n".join(lines)

    def views_page(self) -> str:
        t = self.t
        entries = self.model["entries"]
        lines = self.front(t["views_title"], t["views_intro"], ["workspace_catalog.yaml", "projection_catalog.yaml"])
        lines += [f"## {t['read_modes']} {{#read-execution}}", ""]
        locale = "de" if self.de else "en"
        for definition in READ_MODE_DEFINITIONS.values():
            lines += [f"**{definition['label'][locale]}**", "", definition["description"][locale], ""]
        lines += [t["adapter_note"], "", t["refresh_note"], "", t["states_note"], ""]
        spaces = [e for e in entries if e["kind"] == "workspace"]
        lines += [f"## {t['workspaces']}", ""]
        for space in spaces:
            lines += [self.heading(3, space), ""]
            lines += [f"**{t['views']}:** " + ", ".join(self.ref(f'view:{v}') for v in space["views"]), ""]
            if space["actions"]:
                lines += [f"**{t['actions']}:** " + ", ".join(self.ref(f'action:{a}') for a in space["actions"]), ""]
        views = [e for e in entries if e["kind"] == "view"]
        lines += [f"## {t['views']}", ""]
        lines += [
            table(
                [t["key"], t["label"], t["route"], t["kind"], t["projection"]],
                [
                    [f"[`{v['key']}`](#{self.anchor(v)})", v["label"], f"`{v['route']}`", f"`{v['view_kind']}`", f"`{v['projection']}`" if v["projection"] else "—"]
                    for v in views
                ],
            ),
            "",
        ]
        for view in views:
            lines += [self.heading(3, view), "", view["summary"], ""]
            lines += [f"**{t['route']}:** `{view['route']}` · **{t['kind']}:** `{view['view_kind']}`", ""]
            lines += self.read_mode_lines(view)
            lines += self.see_also(view)
        projections = [e for e in entries if e["kind"] == "projection"]
        lines += [f"## {t['projections']}", ""]
        for projection in projections:
            lines += [self.heading(3, projection), "", projection["summary"], ""]
            lines += [
                f"**{t['consumers']}:** {', '.join(projection['consumers']) or '—'} · **{t['reads']}:** {codes(projection['reads'])}",
                "",
                f"**{t['outputs']}:** {codes(projection['outputs'])}",
                "",
            ]
            lines += self.read_mode_lines(projection)
            if projection["read_modes"][0]["mode"] == "stored":
                lines += [f"**{t['refresh_events']}:** {codes(projection['refresh_events'])}", ""]
                if projection["clock_refresh_seconds"]:
                    lines += [t["clock_refresh"], ""]
            lines += self.see_also(projection)
        actions = [e for e in entries if e["kind"] == "action"]
        lines += [f"## {t['actions']}", ""]
        lines += [
            table(
                [t["key"], t["label"], t["command"], t["confirmation"], t["prerequisites"]],
                [
                    [f"[`{a['key']}`](#{self.anchor(a)})", a["label"], self.ref(f"command:{a['command']}"), f"`{a['confirmation']}`", codes(a["prerequisites"])]
                    for a in actions
                ],
            ),
            "",
        ]
        for action in actions:
            command_ref = self.ref(f"command:{action['command']}")
            lines += [self.heading(3, action), ""]
            lines += [f"**{t['command']}:** {command_ref} · **{t['confirmation']}:** `{action['confirmation']}` · **{t['prerequisites']}:** {codes(action['prerequisites'])}", ""]
            lines += self.see_also(action)
        return "\n".join(lines)

    def exceptions_page(self) -> str:
        t = self.t
        entries = [e for e in self.model["entries"] if e["kind"] == "exception"]
        lines = self.front(t["exceptions_title"], t["exceptions_intro"], ["operational_exception_catalog.yaml"])
        lines += [
            table(
                [t["key"], t["label"], t["area"], t["severity"], t["owner"]],
                [
                    [f"[`{e['key']}`](#{self.anchor(e)})", e["label"], self.area(e["area"]), f"`{e['severity']}`", e["owner"]]
                    for e in entries
                ],
            ),
            "",
        ]
        for entry in entries:
            lines += [self.heading(2, entry), "", entry["summary"], ""]
            lines += [
                f"- **{t['owner']}:** {entry['owner']}",
                f"- **{t['clears_through']}:** {entry['clears_through']}",
                f"- **{t['severity']}:** `{entry['severity']}`",
                f"- **{t['record_type']}:** `{entry['record_type']}`",
                f"- **{t['authority']}:** `{entry['authority']}`",
                f"- **{t['evidence']}:** {codes(entry['evidence'])}",
                "",
            ]
            if entry["causes"]:
                lines += [f"**{t['causes']}**", "", table(["ID", t["label"], t["authority"]], [[f"`{c['id']}`", c["label"], f"`{c['authority']}`"] for c in entry["causes"]]), ""]
            lines += self.see_also(entry)
        return "\n".join(lines)

    def events_page(self) -> str:
        t = self.t
        entries = [e for e in self.model["entries"] if e["kind"] == "event"]
        lines = self.front(t["events_title"], t["events_intro"], ["business_event_catalog.yaml"])
        lines += [
            table(
                [t["event"], t["producer"], t["subject"], t["invalidates"]],
                [
                    [f"`{e['key']}`", self.ref(f"command:{e['producer']}"), f"`{e['subject']}`", codes(e["invalidates"])]
                    for e in entries
                ],
            ),
            "",
        ]
        return "\n".join(lines)

    def storylines_page(self) -> str:
        t = self.t
        lines = [
            "---",
            "aside: false",
            "---",
            "",
            f"# {t['storylines_title']}",
            "",
            t["storylines_intro"],
            "",
            t["generated"].format(source="packages/reality-core/storylines/*.storyline.yaml"),
            "",
            f"- [{t['storyline_schema']}](/storylines/storyline.schema.json)",
            "",
        ]
        for story in self.model.get("storylines", []):
            lines += [
                f"## {self.text(story['title'])} {{#storyline-{story['key']}}}",
                "",
                self.text(story["summary"]),
                "",
                f"- [{t['storyline_download']}](/storylines/{story['key']}.storyline.yaml) (`{story['key']}` v{story['version']})",
                "",
                f"### {t['storyline_chapters']}",
                "",
                table(
                    [t["chapter"], t["chapter_kind"], t["chapter_command"], t["chapter_view"], t["chapter_expect"]],
                    [
                        [
                            f"{index}. {self.text(c['title'])}" + ("" if c["default_path"] else f" ({t['storyline_alternative']})"),
                            t["kind_read"] if c["kind"] == "read" else t["kind_command_chapter"],
                            ", ".join(f"`{x}`" for x in c["tools"]),
                            f"`{c['view']}`" if c["view"] else "",
                            ", ".join(
                                [f"▲ `{x}`" for x in c["expect"]["raised"]]
                                + [f"✓ `{x}`" for x in c["expect"]["cleared"]]
                            ),
                        ]
                        for index, c in enumerate(story["chapters"], start=1)
                    ],
                ),
                "",
            ]
        return "\n".join(lines)

    def write(self) -> None:
        target = CONTENT / (f"{self.locale}/" if self.locale else "") / SECTION
        target.mkdir(parents=True, exist_ok=True)
        stories = CONTENT / (f"{self.locale}/" if self.locale else "") / "storylines"
        stories.mkdir(parents=True, exist_ok=True)
        (stories / "index.md").write_text(self.storylines_page() + "\n")
        (target / "resources.md").write_text(self.resources_page() + "\n")
        (target / "processes.md").write_text(self.processes_page() + "\n")
        (target / "commands.md").write_text(self.commands_page() + "\n")
        (target / "views.md").write_text(self.views_page() + "\n")
        (target / "exceptions.md").write_text(self.exceptions_page() + "\n")
        (target / "events.md").write_text(self.events_page() + "\n")


def storyline_models() -> list[dict[str, Any]]:
    """The built-in storyline packages, reduced to what the docs page shows."""
    from reality.storyline.package import builtin_packages

    stories = []
    for result in builtin_packages():
        if not result.ok:
            raise SystemExit(f"built-in storyline does not validate: {result.errors}")
        package = result.package
        default_path: list[str] = []
        key = package.chapters[0].key
        while key and key not in default_path:
            default_path.append(key)
            key = package.default_next(key)
        stories.append(
            {
                "key": package.key,
                "version": package.version,
                "process": package.process,
                "title": package.title.model_dump(exclude_none=True),
                "summary": package.summary.model_dump(exclude_none=True),
                "chapters": [
                    {
                        "key": chapter.key,
                        "title": chapter.title.model_dump(exclude_none=True),
                        "kind": chapter.kind,
                        "tools": [chapter.command] if chapter.command else [read.tool for read in chapter.reads],
                        "view": chapter.view,
                        "expect": {"raised": chapter.expect.raised, "cleared": chapter.expect.cleared},
                        "default_path": chapter.key in default_path,
                    }
                    for chapter in package.chapters
                ],
            }
        )
    return stories


def write_storyline_files() -> None:
    """Copies of the built-in packages and the schema, served from the docs' public dir."""
    from reality.storyline.package import FILE_SUFFIX, builtin_directory, json_schema

    public = CONTENT / "public/storylines"
    public.mkdir(parents=True, exist_ok=True)
    for path in sorted(builtin_directory().glob(f"*{FILE_SUFFIX}")):
        (public / path.name).write_bytes(path.read_bytes())
    (public / "storyline.schema.json").write_text(json.dumps(json_schema(), indent=2, ensure_ascii=False) + "\n")


def main() -> None:
    model = build_model()
    from data_model_reference import build_data_models

    model["dataModels"] = build_data_models(model["entries"])
    model["storylines"] = storyline_models()
    write_storyline_files()
    DATA.mkdir(parents=True, exist_ok=True)
    (DATA / "tool-usage.json").write_text(json.dumps(model, indent=2, ensure_ascii=False) + "\n")
    for locale in ("", "de"):
        Renderer(model, locale).write()

    prettier = ROOT / "apps/docs/node_modules/.bin/prettier"
    if prettier.exists():
        subprocess.run(
            [str(prettier), "--write", f"content/{SECTION}", f"content/de/{SECTION}", "content/storylines", "content/de/storylines", "content/public/storylines", ".vitepress/data"],
            cwd=ROOT / "apps/docs",
            check=True,
        )


if __name__ == "__main__":
    main()
