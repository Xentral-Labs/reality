from sqlalchemy import func, select

from reality.db.core import Shipment
from reality.mcp.catalog import MCP_TOOL_REGISTRY, dispatch_tool
from reality.services.shipments import record_shipment_notice


def test_shipment_mcp_reads_match_shared_service_and_need_no_confirmation(
    session, business
):
    shipment, package, _ = record_shipment_notice(
        session,
        business.tenant.id,
        direction="inbound",
        purpose="supplier_delivery",
        counterparty_id=business.supplier.id,
        tracking_number="MCP-TRACK-173",
    )

    listing = dispatch_tool(
        session,
        business.tenant.id,
        "shipments_list",
        {"tracking": "TRACK-173", "observation": "announced"},
    )
    detail = dispatch_tool(
        session,
        business.tenant.id,
        "shipment_explain",
        {"shipment_id": package.id},
    )

    assert listing["items"][0]["id"] == shipment.id
    assert detail["id"] == shipment.id
    assert MCP_TOOL_REGISTRY["shipments_list"].access == "read"
    assert MCP_TOOL_REGISTRY["shipment_explain"].access == "read"


def test_shipment_mcp_mutations_are_proposal_only_and_notice_has_no_effect(
    session, business
):
    proposal_names = {
        "shipment_notice_record_propose",
        "shipment_dispatch_propose",
        "shipment_receive_propose",
        "shipment_event_record_propose",
        "shipment_event_supersede_propose",
    }
    assert all(MCP_TOOL_REGISTRY[name].access == "propose" for name in proposal_names)
    before = session.scalar(select(func.count()).select_from(Shipment))
    result = dispatch_tool(
        session,
        business.tenant.id,
        "shipment_notice_record_propose",
        {
            "direction": "outbound",
            "purpose": "customer_delivery",
            "counterparty_id": business.customer.id,
        },
    )

    assert result["status"] == "proposed"
    assert result["proposal_id"]
    assert result["requires_confirmation"] is True
    assert session.scalar(select(func.count()).select_from(Shipment)) == before
