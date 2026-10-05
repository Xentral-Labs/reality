from copy import deepcopy
from decimal import Decimal

import pytest
from sqlalchemy import event
from test_business_decision_discovery import discover, executed_reservation
from test_mcp_read_contract import order, read

from reality.mcp.catalog import MCP_TOOL_REGISTRY, dispatch_tool
from reality.services.core import (
    NotFound,
    create_document,
    create_tenant,
    record_movement,
)
from reality.services.read_contracts import discovery_summary
from reality.tools.application import run_read_tool


@pytest.mark.parametrize("scoped", [True, False])
@pytest.mark.parametrize(
    "count,earlier,later",
    [
        (0, False, False),
        (1, False, False),
        (1, False, True),
        (1, True, True),
        (1, True, False),
    ],
)
def test_decision_count_is_immediately_qualified(scoped, count, earlier, later):
    scope = "retained_execution_events" if scoped else "retained_executed_decisions"
    coverage = {"scope": scope, "historical_completeness": "unknown"}
    page = {
        "records": [{}] * count,
        "has_more": later,
        "metadata": {"decision_coverage": coverage},
    }
    before = deepcopy(page)
    summary = discovery_summary(
        page, family="executed_decision", omitted_before=earlier
    )
    assert page == before
    assert summary["selection_scope"] == coverage["scope"]
    assert summary["historical_completeness"] == coverage["historical_completeness"]
    assert summary["scope"] == "shown_records"
    assert summary["shown_record_count"] == count
    assert summary["selection_record_count"] == (None if earlier or later else count)
    first = summary["observation"].split(".")[0]
    assert scope in first
    assert "Historical completeness is unknown" in summary["observation"]
    if count == 0:
        assert "does not establish absence" in summary["observation"]


def test_actual_decision_page_and_legacy_share_unchanged_records(session, business):
    document, _, proposal = executed_reservation(session, business)
    writes = []

    def before_execute(conn, cursor, statement, parameters, context, many):
        if statement.lstrip().split()[0].upper() in {"INSERT", "UPDATE", "DELETE"}:
            writes.append(statement)

    event.listen(session.bind, "before_cursor_execute", before_execute)
    try:
        page = discover(session, business, document)
        assert (
            page["summary"]["selection_scope"]
            == page["metadata"]["decision_coverage"]["scope"]
        )
        assert page["records"][0]["id"] == proposal.id
        assert (
            discover(session, business, document, response_format="legacy")
            == page["records"]
        )
        assert (
            run_read_tool(
                session,
                business.tenant.id,
                "business_discover",
                {"family": "executed_decision", "document_id": document.id},
            )
            == page["records"]
        )
    finally:
        event.remove(session.bind, "before_cursor_execute", before_execute)
    assert not writes
    ordinary = read(session, business, "business_records_discover", family="item")
    assert "selection_scope" not in ordinary["summary"]


def test_order_stock_does_not_establish_uninspected_history(session, business):
    _, document, _, commitments = order(session, business)
    commitment = next(c for c in commitments if c.type == "customer_delivery")
    unrelated = record_movement(
        session,
        business.tenant.id,
        "receipt",
        business.item.id,
        "10",
        to_location_id=business.location.id,
    )
    shipped = record_movement(
        session,
        business.tenant.id,
        "shipment",
        business.item.id,
        "2",
        from_location_id=business.location.id,
        commitment_id=commitment.id,
    )
    session.flush()
    writes = []

    def before_execute(conn, cursor, statement, parameters, context, many):
        if statement.lstrip().split()[0].upper() in {"INSERT", "UPDATE", "DELETE"}:
            writes.append(statement)

    event.listen(session.bind, "before_cursor_execute", before_execute)
    try:
        value = read(session, business, "order_explain", order_reference=document.id)
        assert value == run_read_tool(
            session,
            business.tenant.id,
            "order_explain",
            {"order_reference": document.id},
        ) | {"metadata": value["metadata"]}
        scope = value["interpretation_scope"]
        assert scope["kind"] == "current_inventory_and_order_linked_movements"
        assert scope["inventory_history"] == "not_established_by_this_read"
        assert "not checked" in scope["notice"]
        assert "movement_explanation" in scope["notice"]
        assert "not complete inventory history" in scope["notice"]
        assert [m["id"] for m in value["movements"]] == [shipped.id]
        assert unrelated.id not in str(value["movements"])
        assert Decimal(
            value["fulfillment"]["lines"][0]["inventory"]["physical"]
        ) == Decimal(8)
        assert Decimal(
            value["fulfillment"]["lines"][0]["fulfilled_quantity"]
        ) == Decimal(2)
        exact = read(session, business, "movement_explanation", movement_id=shipped.id)
        assert exact["movement_id"] == shipped.id
    finally:
        event.remove(session.bind, "before_cursor_execute", before_execute)
    assert not writes
    foreign = create_tenant(session, "Foreign inventory boundary")
    with pytest.raises(NotFound):
        dispatch_tool(
            session, foreign.id, "order_explain", {"order_reference": document.id}
        )


def test_existing_tool_descriptions_name_evidence_limits():
    discovery = MCP_TOOL_REGISTRY["business_records_discover"].description
    assert "qualify the count immediately" in discovery
    for name in ["order_explain", "inventory_read"]:
        description = MCP_TOOL_REGISTRY[name].description
        assert "not checked" in description
        assert "receipt timing" in description
        assert "movement_explanation" in description


def test_empty_order_still_bounds_inventory_history(session, business):
    document = create_document(
        session,
        business.tenant.id,
        "sales_order",
        "EMPTY-HISTORY",
        business.customer.id,
        "0",
    )
    value = read(session, business, "order_explain", order_reference=document.id)
    assert value["fulfillment"]["lines"] == []
    assert value["movements"] == []
    assert (
        value["interpretation_scope"]["inventory_history"]
        == "not_established_by_this_read"
    )
