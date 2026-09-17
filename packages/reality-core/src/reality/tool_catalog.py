"""Presentation-only capabilities composed from existing executable contracts.

This module is consumed by application-reference, never by MCP dispatch. Explicit
relationships group representations; metadata cannot grant access or execute work.
"""

from __future__ import annotations

import json
from copy import deepcopy
from typing import Any

from reality.config import config_text


def build_tool_catalog(catalog: dict[str, Any]) -> dict[str, Any]:
    from reality.catalogs import load_catalog_labels
    from reality.mcp.catalog import tool_definitions

    config = json.loads(config_text("tool_catalog.json"))
    topics = {row["key"] for row in config["topics"]}
    tools = {tool.name: deepcopy(tool.public_metadata()) for tool in tool_definitions()}
    labels = load_catalog_labels()
    commands = {c["service"]: c for c in catalog["commands"]}
    aliases = {
        s: c["service"]
        for c in commands.values()
        for s in [c["service"], *c.get("related_services", [])]
    }
    actions = {a["key"]: a for w in catalog["workspaces"] for a in w["actions"]}
    views = {v["key"]: v for w in catalog["workspaces"] for v in w["views"]}
    projections = {p["materialized_as"]: p for p in catalog["projections"]}
    entries: list[dict[str, Any]] = []

    def entry(
        key: str, title: str, topic: str, purpose: str, description: str = ""
    ) -> dict[str, Any]:
        if topic not in topics:
            raise ValueError(f"Unknown capability topic: {topic}")
        result = {
            "id": key,
            "title": title,
            "topic": topic,
            "purpose": purpose,
            "description": description,
            "labels": {},
            "commands": [],
            "actions": [],
            "views": [],
            "projections": [],
            "mcp": [],
            "discovery": [],
            "related": [],
        }
        entries.append(result)
        return result

    def command_topic(service: str) -> str:
        group = catalog["discovery"]["command_groups"].get(service)
        topic = config["command_topics"].get(service) or config["groups"].get(group)
        if not topic:
            raise ValueError(f"Command needs a capability topic: {service}")
        return topic

    def command_tools(command: dict[str, Any]) -> list[str]:
        return list(
            dict.fromkeys(
                name
                for service in [
                    command["service"],
                    *command.get("related_services", []),
                ]
                for name in catalog["agent_command_coverage"]
                .get(service, {})
                .get("tools", [])
            )
        )

    def attach_command(row: dict[str, Any], command: dict[str, Any]) -> None:
        row["commands"] = [command["service"]]
        row["actions"] = [
            a["key"]
            for a in actions.values()
            if aliases.get(a["command"]) == command["service"]
        ]

    for form in catalog["discovery"]["entries"]:
        if not form.get("form"):
            continue
        command = commands[aliases[form["command"]]]
        row = entry(
            "form:" + form["key"],
            form["label"],
            config["form_topics"].get(form["key"]) or command_topic(command["service"]),
            "change",
            command.get("effect", ""),
        )
        attach_command(row, command)
        row["discovery"] = [form["key"]]
        row["mcp"] = config["form_tools"].get(form["key"], command_tools(command))

    represented = {s for e in entries for s in e["commands"]}
    for command in commands.values():
        if command["service"] in represented:
            continue
        names = command_tools(command)
        purpose = (
            "change"
            if command["mode"] == "mutation"
            else "understand"
            if any(n in config["understand_tools"] for n in names)
            else "read"
        )
        row = entry(
            "command:" + command["service"],
            command.get("name", command["service"]),
            command_topic(command["service"]),
            purpose,
            command.get("effect", ""),
        )
        attach_command(row, command)
        row["labels"] = labels["commands"].get(command["service"], {})
        row["mcp"] = names

    # Merge declared read aliases only; a shared database table is not equivalence.
    read_rows = {}
    view_targets = {
        v: target
        for target, item in config["reads"].items()
        for v in item.get("views", [])
    }
    for projection in projections.values():
        target = projection["materialized_as"]
        definition = config["reads"].get(target)
        if not definition:
            raise ValueError(f"Projection needs a capability topic: {target}")
        row = entry(
            "report:" + target,
            projection["name"],
            definition["topic"],
            definition.get("purpose", "read"),
            projection.get("calculation", ""),
        )
        row["projections"] = [target]
        row["mcp"] = definition.get("mcp", [])
        row["labels"] = labels["projections"].get(target, {})
        read_rows[target] = row
    for view in views.values():
        target = (
            view.get("projection")
            or view_targets.get(view["key"])
            or "view:" + view["key"]
        )
        if target not in read_rows:
            definition = config["reads"].get(target)
            if not definition:
                raise ValueError(f"View needs a capability topic: {target}")
            read_rows[target] = entry(
                "report:" + target,
                view["label"],
                definition["topic"],
                definition.get("purpose", "read"),
                view.get("description", ""),
            )
        read_rows[target]["views"].append(view["key"])

    represented_tools = {name for row in entries for name in row["mcp"]}
    for name, tool in tools.items():
        if name in represented_tools:
            continue
        topic = config["mcp_topics"].get(name)
        if not topic:
            raise ValueError(f"MCP tool needs an explicit capability topic: {name}")
        purpose = (
            "change"
            if tool["access"] != "read"
            else "understand"
            if name in config["understand_tools"]
            else "read"
        )
        row = entry("mcp:" + name, tool["label"], topic, purpose, tool["description"])
        row["mcp"] = [name]

    for link in catalog["discovery"]["entries"]:
        if link.get("form"):
            continue
        linked = {
            aliases.get(s)
            for s in [link.get("command"), *link.get("commands", [])]
            if s
        }
        matches = [row for row in entries if linked.intersection(row["commands"])]
        if matches:
            for row in matches:
                row["discovery"].append(link["key"])
        else:
            row = entry(
                "page:" + link["key"],
                link["label"],
                config["groups"][link["group"]],
                "navigate",
            )
            row["discovery"] = [link["key"]]

    ids = {row["id"] for row in entries}
    for row in entries:
        for name in row["mcp"]:
            if name not in tools:
                raise ValueError(f"Unknown capability MCP reference: {name}")
        row["related"] = config["related"].get(row["id"], [])
        if set(row["related"]) - ids:
            raise ValueError(f"Unknown related capability: {row['id']}")
    return {
        "version": 1,
        "topics": config["topics"],
        "entries": entries,
        "mcp_tools": list(tools.values()),
    }
