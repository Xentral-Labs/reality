from copy import deepcopy

from reality.catalogs import load_application_catalog
from reality.mcp.catalog import tool_definitions
from reality.tool_catalog import build_tool_catalog


def test_catalog_covers_every_existing_definition_without_changing_mcp():
    source = load_application_catalog()
    original = deepcopy(source)
    before = [tool.public_metadata() for tool in tool_definitions()]
    result = build_tool_catalog(source)
    entries = result["entries"]
    assert len({row["id"] for row in entries}) == len(entries)
    for field, expected in {
        "commands": {c["service"] for c in source["commands"]},
        "actions": {a["key"] for w in source["workspaces"] for a in w["actions"]},
        "views": {v["key"] for w in source["workspaces"] for v in w["views"]},
        "projections": {p["materialized_as"] for p in source["projections"]},
        "mcp": {t.name for t in tool_definitions()},
        "discovery": {e["key"] for e in source["discovery"]["entries"]},
    }.items():
        assert {key for row in entries for key in row[field]} == expected, field
    assert source == original
    assert before == [tool.public_metadata() for tool in tool_definitions()]


def test_inventory_aliases_merge_but_movement_intents_stay_separate():
    entries = build_tool_catalog(load_application_catalog())["entries"]
    inventory = [e for e in entries if "inventory_read" in e["mcp"]]
    assert len(inventory) == 1
    assert inventory[0]["views"] == ["inventory"]
    assert inventory[0]["projections"] == ["inventory"]
    forms = {d: e for e in entries for d in e["discovery"]}
    assert forms["receipt"]["id"] != forms["movement_create"]["id"]
    assert forms["receipt"]["commands"] == forms["movement_create"]["commands"]
    assert forms["shipment_dispatch"]["mcp"] == ["shipment_dispatch_propose"]
    assert forms["shipment_receive"]["mcp"] == ["shipment_receive_propose"]
    assert all(e["topic"] for e in entries)
    assert all(
        e["purpose"] in {"read", "understand", "change", "navigate"} for e in entries
    )


def test_catalog_metadata_cannot_mutate_mcp_schema():
    before = deepcopy([tool.public_metadata() for tool in tool_definitions()])
    result = build_tool_catalog(load_application_catalog())
    result["mcp_tools"][0]["input_schema"].clear()
    assert before == [tool.public_metadata() for tool in tool_definitions()]


def test_contribution_capabilities_share_one_business_topic():
    result = build_tool_catalog(load_application_catalog())
    topics = {row["key"]: row["label"] for row in result["topics"]}
    assert topics["contribution"] == "Contribution margin"
    entries = result["entries"]
    expected = {
        "command:cost_evidence",
        "command:receipt_cost",
        "command:inventory_cost",
        "command:commercial_match",
        "command:contribution_preview",
        "command:cost_query",
        "command:cost_record",
        "command:reviewed_contribution",
        "command:execute_cost_change",
        "mcp:graph_contribution_reviews_list",
    }
    assert {row["id"] for row in entries if row["topic"] == "contribution"} == expected
