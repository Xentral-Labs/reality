"""Validate shared capability-discovery metadata without executing commands."""

from __future__ import annotations

from typing import Any


def validate_action_discovery(
    payload: dict[str, Any], *, commands: list[dict[str, Any]]
) -> dict[str, Any]:
    """Reject incomplete classification and invalid executable presentation entries."""
    categories = payload.get("categories", [])
    category_keys = [c["key"] for c in categories]
    groups = [g["key"] for c in categories for g in c["groups"]]
    if (
        not categories
        or len(set(category_keys)) != len(category_keys)
        or len(set(groups)) != len(groups)
        or len(set(category_keys + groups)) != len(category_keys + groups)
        or any(not c.get("label") or not c.get("groups") for c in categories)
        or any(not g.get("label") for c in categories for g in c["groups"])
    ):
        raise ValueError("Discovery categories and groups must be nonempty and unique")
    primary = {c["service"]: c for c in commands}
    services = {
        s: c for c in commands for s in [c["service"], *c.get("related_services", [])]
    }
    assignments = payload.get("command_groups", {})
    if set(assignments) != set(primary) or not set(assignments.values()) <= set(groups):
        raise ValueError("Discovery command classification is incomplete or invalid")
    seen: set[str] = set()
    forms: set[str] = set()
    for entry in payload.get("entries", []):
        key = entry["key"]
        if key in seen or not entry.get("label") or not entry.get("placements"):
            raise ValueError(
                "Discovery entries require unique identities, labels and placements"
            )
        if entry.get("access") not in {None, "owner", "demo"}:
            raise ValueError("Unknown discovery access condition")
        placements = entry["placements"]
        if not isinstance(placements, list):
            raise TypeError("Discovery placements must be a list")
        if any(not isinstance(p, str) or not p.strip() for p in placements) or len(
            set(placements)
        ) != len(placements):
            raise ValueError("Discovery placements must be unique nonempty strings")
        if not set(entry.get("commands", [])) <= set(primary):
            raise ValueError("Discovery destination references unknown commands")
        seen.add(key)
        if ("form" in entry) == ("destination" in entry):
            raise ValueError("Discovery entry requires exactly one form or destination")
        if "form" in entry:
            command = services.get(entry.get("command"))
            if (
                not command
                or command["mode"] != "mutation"
                or "Web" not in command["adapters"]
            ):
                raise ValueError("Discovery form must reference a Web mutation command")
            if entry["form"] in forms:
                raise ValueError("Duplicate discovery form")
            forms.add(entry["form"])
        elif set(entry["destination"]) - {
            "route",
            "analyticsView",
            "family",
            "dataView",
            "settingsView",
            "financeView",
            "financeSettings",
            "flow",
        }:
            raise ValueError(
                "Discovery destinations cannot override company or record context"
            )
        elif entry.get("group") not in groups or entry["destination"].get(
            "route"
        ) not in {
            "analytics",
            "master-data",
            "data-sources",
            "settings",
            "demo-data",
            "finance",
        }:
            raise ValueError(
                "Discovery destination must be an existing management page"
            )
    return payload
