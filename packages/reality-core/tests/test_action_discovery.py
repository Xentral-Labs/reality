"""Presentation metadata must be complete without creating business authority."""

from copy import deepcopy

import pytest

from reality.action_discovery import validate_action_discovery
from reality.catalogs import load_application_catalog


def test_complete_discovery_and_action_inheritance():
    catalog = load_application_catalog()
    discovery = catalog["discovery"]
    assert set(discovery["command_groups"]) == {
        c["service"] for c in catalog["commands"]
    }
    assert len(discovery["command_groups"]) == len(catalog["commands"])
    actions = {a["key"]: a for w in catalog["workspaces"] for a in w["actions"]}
    assert len(actions) == 13
    assert all(a["command"] in discovery["command_groups"] for a in actions.values())
    assert len([e for e in discovery["entries"] if "form" in e]) == 23


@pytest.mark.parametrize(
    "damage",
    [
        "missing",
        "stale",
        "group",
        "duplicate",
        "service",
        "destination",
        "tenant_destination",
        "access",
        "empty_category",
    ],
)
def test_discovery_rejects_drift(damage):
    catalog = load_application_catalog()
    payload = deepcopy(catalog["discovery"])
    if damage == "missing":
        payload["command_groups"].pop("reserve")
    elif damage == "stale":
        payload["command_groups"]["not_a_command"] = "reservations"
    elif damage == "group":
        payload["command_groups"]["reserve"] = "not_a_group"
    elif damage == "duplicate":
        payload["entries"].append(payload["entries"][0])
    elif damage == "service":
        payload["entries"][0]["command"] = "missing_service"
    elif damage == "tenant_destination":
        next(e for e in payload["entries"] if "destination" in e)["destination"][
            "tenant"
        ] = "other-company"
    elif damage == "access":
        payload["entries"][0]["access"] = "unreviewed"
    elif damage == "empty_category":
        payload["categories"][0]["groups"] = []
    else:
        payload["entries"][0]["destination"] = {"route": "finance"}
    with pytest.raises(ValueError):
        validate_action_discovery(payload, commands=catalog["commands"])


def test_frontend_fixture_tracks_canonical_reference():
    import json
    from pathlib import Path

    import yaml

    root = Path(__file__).resolve().parents[3]
    fixture = json.loads(
        (root / "apps/web/scripts/fixtures/action-reference.json").read_text()
    )
    commands = yaml.safe_load(
        (root / "packages/reality-core/config/command_catalog.yaml").read_text()
    )["commands"]
    fields = {"name", "service", "mode", "adapters", "related_services", "effect"}
    assert fixture["commands"] == [
        {k: v for k, v in c.items() if k in fields} for c in commands
    ]
    workspaces = yaml.safe_load(
        (root / "packages/reality-core/config/workspace_catalog.yaml").read_text()
    )
    assert fixture["workspaces"][0]["actions"] == workspaces["actions"]
