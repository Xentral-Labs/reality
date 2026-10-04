"""Browser-free company, review and navigation contracts (spec 363)."""

import json
from dataclasses import replace

import pytest

from reality.db.core import ChangeProposal, Document, DocumentLine, Party, uid
from reality.mcp.catalog import MCP_TOOL_REGISTRY, dispatch_mcp_tool, dispatch_tool
from reality.mcp.principal import MCPPrincipal
from reality.services.core import InvalidOperation, NotFound, create_tenant
from reality.tools.application import run_read_tool


def test_context_returns_stored_company_identity(session, business):
    result = dispatch_tool(session, business.tenant.id, "company_context", {})
    assert result["company"] == {
        "id": business.tenant.id,
        "name": business.tenant.name,
        "purpose": business.tenant.purpose,
    }
    assert result["rights_read"] == "capability_catalog"
    assert "credential_id" not in json.dumps(result)


def test_pending_pages_are_bounded_payload_free_and_scope_bound(session, business):
    for i in range(3):
        session.add(
            ChangeProposal(
                id=uid("act"),
                tenant_id=business.tenant.id,
                type="tool:party_create",
                status="proposed",
                input=json.dumps({"password": "never-publish", "large": "x" * 20000}),
            )
        )
    session.flush()
    page = dispatch_tool(
        session, business.tenant.id, "proposals_awaiting_approval", {"limit": 2}
    )
    assert len(page["records"]) == 2
    assert page["has_more"]
    assert "never-publish" not in json.dumps(page)
    assert all(
        "arguments" not in row and "preview" not in row for row in page["records"]
    )
    second = dispatch_tool(
        session,
        business.tenant.id,
        "proposals_awaiting_approval",
        {"limit": 2, "cursor": page["next_cursor"]},
    )
    assert len(second["records"]) == 1
    assert not second["has_more"]
    with pytest.raises(InvalidOperation, match="cursor"):
        dispatch_tool(
            session,
            business.tenant.id,
            "proposals_awaiting_approval",
            {"cursor": page["next_cursor"], "tool": "reserve"},
        )
    other = create_tenant(session, "Other company")
    with pytest.raises(InvalidOperation, match="cursor"):
        dispatch_tool(
            session,
            other.id,
            "proposals_awaiting_approval",
            {"cursor": page["next_cursor"]},
        )
    legacy = run_read_tool(
        session, business.tenant.id, "proposals_awaiting_approval", {}
    )
    assert isinstance(legacy, list) and len(legacy) == 3
    with pytest.raises(InvalidOperation, match="limit"):
        dispatch_tool(
            session, business.tenant.id, "proposals_awaiting_approval", {"limit": 0}
        )


def test_exact_review_separate_decision_receipt_and_replay(
    session, business, scheduled_owner
):
    principal = MCPPrincipal(
        "interactive",
        "credential_1",
        "grant_1",
        scheduled_owner.id,
        business.tenant.id,
        "client_1",
        frozenset({"reality:read", "reality:propose", "reality:confirm"}),
        frozenset(
            {
                "party_create_propose",
                "proposal_review",
                "proposal_approve_and_execute",
                "proposal_execution_status",
            }
        ),
    )
    before = session.query(Party).filter_by(tenant_id=business.tenant.id).count()
    proposed = dispatch_mcp_tool(
        session,
        principal,
        "party_create_propose",
        {"records": [{"name": "MCP reviewed customer", "roles": ["customer"]}]},
    )
    args = {"proposal_id": proposed["proposal_id"]}
    review = dispatch_mcp_tool(session, principal, "proposal_review", args)
    assert review["company"]["id"] == business.tenant.id
    assert review["status"] == "proposed"
    assert review["next_step"]["confirmation_tool"] == "proposal_approve_and_execute"
    assert review["next_step"]["decision_handoff"] == "proposal_approve_and_execute"
    assert (
        session.query(Party).filter_by(tenant_id=business.tenant.id).count() == before
    )
    read_only = replace(
        principal, scopes=frozenset({"reality:read", "reality:propose"})
    )
    with pytest.raises(PermissionError):
        dispatch_mcp_tool(
            session,
            read_only,
            "proposal_approve_and_execute",
            {**args, "approved": True},
        )
    confirmed = dispatch_mcp_tool(
        session, principal, "proposal_approve_and_execute", {**args, "approved": True}
    )
    assert confirmed["status"] == "executed"
    receipt = dispatch_mcp_tool(session, principal, "proposal_review", args)
    assert receipt["status"] == "executed" and receipt["receipt"]
    dispatch_mcp_tool(
        session, principal, "proposal_approve_and_execute", {**args, "approved": True}
    )
    assert (
        session.query(Party).filter_by(tenant_id=business.tenant.id).count()
        == before + 1
    )
    other = create_tenant(session, "Other review company")
    with pytest.raises(NotFound):
        dispatch_tool(session, other.id, "proposal_review", args)


def test_exact_review_redacts_credentials_but_exposes_only_delivery_fingerprint(
    session, business
):
    proposal = ChangeProposal(
        id=uid("act"),
        tenant_id=business.tenant.id,
        type="tool:reserve",
        status="proposed",
        input=json.dumps(
            {
                "password": "hidden-password",
                "token": "hidden-token",
                "_delivery_review": {"token": "retained-fingerprint"},
            }
        ),
        output=json.dumps({"api_key": "hidden-api-key"}),
    )
    session.add(proposal)
    session.flush()
    result = dispatch_tool(
        session, business.tenant.id, "proposal_review", {"proposal_id": proposal.id}
    )
    assert "hidden-" not in json.dumps(result)
    assert result["confirmation"]["review_token"] == "retained-fingerprint"
    assert proposal.status == "proposed"


def test_document_lines_use_exact_company_document_scope(session, business):
    document = Document(
        id=uid("doc"),
        tenant_id=business.tenant.id,
        type="supplier_invoice",
        number="TEST-INV",
        party_id=business.supplier.id,
    )
    session.add(document)
    session.flush()
    line = DocumentLine(
        id=uid("dln"),
        tenant_id=business.tenant.id,
        document_id=document.id,
        sku="FREIGHT",
        quantity="1",
        unit_price=None,
        gross_amount="5",
    )
    session.add(line)
    session.flush()
    page = dispatch_tool(
        session,
        business.tenant.id,
        "business_records_discover",
        {"family": "document_line", "document_id": document.id},
    )
    assert page["records"][0]["id"] == line.id
    assert page["records"][0]["unit_price"] is None
    assert page["records"][0]["document_id"] == document.id
    with pytest.raises(InvalidOperation) as refused:
        dispatch_tool(
            session,
            business.tenant.id,
            "business_records_discover",
            {"family": "document", "document_id": document.id},
        )
    assert refused.value.code == "discovery_document_scope_unsupported"
    other = create_tenant(session, "Other lines company")
    with pytest.raises(NotFound):
        dispatch_tool(
            session,
            other.id,
            "business_records_discover",
            {"family": "document_line", "document_id": document.id},
        )


def test_public_schemas_offer_closed_navigation_choices():
    schema = MCP_TOOL_REGISTRY["business_records_discover"].input_schema
    assert "document_line" in schema["properties"]["family"]["enum"]
    assert "document_id" in schema["properties"]
    assert MCP_TOOL_REGISTRY["inventory_read"].input_schema["properties"]["view"][
        "enum"
    ] == ["aggregate", "location"]


@pytest.mark.parametrize("purpose", ["business", "playground"])
def test_reservation_review_confirms_without_browser_and_checks_stale_state(
    session, business, scheduled_owner, purpose
):
    from reality.services.core import (
        active_reserved,
        create_commitment,
        record_movement,
    )

    if purpose == "playground":
        from reality.db.core import Tenant
        from reality.services import company_setup
        from reality.services.core import create_item, create_location, create_party

        created = company_setup.create_company(
            session,
            scheduled_owner.id,
            uid("req"),
            "Practice review",
            "sandbox",
            "empty",
            confirmed=True,
        )
        tenant = session.get(Tenant, created["tenant_id"])
        business = replace(
            business,
            tenant=tenant,
            company=create_party(session, tenant.id, "Practice review", "company"),
            customer=create_party(session, tenant.id, "Customer", "customer"),
            supplier=create_party(session, tenant.id, "Supplier", "supplier"),
            item=create_item(session, tenant.id, "MUG", "Mug"),
            location=create_location(session, tenant.id, "Warehouse"),
        )
    record_movement(
        session,
        business.tenant.id,
        "opening_stock",
        business.item.id,
        "5",
        to_location_id=business.location.id,
    )
    commitment = create_commitment(
        session,
        business.tenant.id,
        "customer_delivery",
        business.company.id,
        business.customer.id,
        business.item.id,
        business.location.id,
        "2",
        None,
    )
    principal = MCPPrincipal(
        "interactive",
        "credential_1",
        "grant_1",
        scheduled_owner.id,
        business.tenant.id,
        "client_1",
        frozenset({"reality:read", "reality:propose", "reality:confirm"}),
        frozenset(
            {
                "reservation_propose",
                "proposal_review",
                "proposal_approve_and_execute",
                "proposal_execution_status",
            }
        ),
    )
    proposed = dispatch_mcp_tool(
        session, principal, "reservation_propose", {"commitment_id": commitment.id}
    )
    args = {"proposal_id": proposed["proposal_id"]}
    review = dispatch_mcp_tool(session, principal, "proposal_review", args)
    assert review["review_kind"] == "delivery"
    assert "inventory_read" in review["next_step"]["verification_reads"]
    assert all(
        MCP_TOOL_REGISTRY[name].access == "read"
        for name in review["next_step"]["verification_reads"]
    )
    assert review["input"]["_delivery_review"]["state"]
    assert review["input"]["_delivery_review"]["effect"]
    assert active_reserved(session, business.tenant.id, business.item.id) == 0
    token = review["confirmation"]["review_token"]
    assert isinstance(token, str) and token
    assert not review["confirmation"]["review_preparation_required"]
    assert review["confirmation"]["arguments"] == {
        "proposal_id": proposed["proposal_id"],
        "approved": True,
        "review_token": token,
    }
    confirmed = dispatch_mcp_tool(
        session,
        principal,
        "proposal_approve_and_execute",
        {**args, "approved": True, "review_token": token},
    )
    assert confirmed["status"] == "executed"
    assert "inventory_read" in confirmed["next_step"]["verification_reads"]
    assert "inventory" in confirmed["receipt"]["verification_reads"]
    stored = session.get(
        ChangeProposal, (business.tenant.id, proposed["proposal_id"])
    ).output
    assert active_reserved(session, business.tenant.id, business.item.id) == 2
    receipt = dispatch_mcp_tool(session, principal, "proposal_execution_status", args)
    assert receipt["status"] == "executed"
    assert "inventory_read" in receipt["next_step"]["verification_reads"]
    assert (
        session.get(
            ChangeProposal, (business.tenant.id, proposed["proposal_id"])
        ).output
        == stored
    )
    dispatch_mcp_tool(
        session,
        principal,
        "proposal_approve_and_execute",
        {**args, "approved": True, "review_token": token},
    )
    assert active_reserved(session, business.tenant.id, business.item.id) == 2

    second = create_commitment(
        session,
        business.tenant.id,
        "customer_delivery",
        business.company.id,
        business.customer.id,
        business.item.id,
        business.location.id,
        "1",
        None,
    )
    proposed = dispatch_mcp_tool(
        session, principal, "reservation_propose", {"commitment_id": second.id}
    )
    args = {"proposal_id": proposed["proposal_id"]}
    review = dispatch_mcp_tool(session, principal, "proposal_review", args)
    record_movement(
        session,
        business.tenant.id,
        "opening_stock",
        business.item.id,
        "1",
        to_location_id=business.location.id,
    )
    with pytest.raises(InvalidOperation):
        dispatch_mcp_tool(
            session,
            principal,
            "proposal_approve_and_execute",
            {
                **args,
                "approved": True,
                "review_token": review["confirmation"]["review_token"],
            },
        )
    assert active_reserved(session, business.tenant.id, business.item.id) == 2


def test_shipping_movements_remain_visible_without_consignment(session, business):
    from reality.services.core import create_commitment, record_movement

    record_movement(
        session,
        business.tenant.id,
        "opening_stock",
        business.item.id,
        "5",
        to_location_id=business.location.id,
    )
    commitment = create_commitment(
        session,
        business.tenant.id,
        "customer_delivery",
        business.company.id,
        business.customer.id,
        business.item.id,
        business.location.id,
        "5",
        None,
    )
    movement = record_movement(
        session,
        business.tenant.id,
        "shipment",
        business.item.id,
        "3",
        from_location_id=business.location.id,
        commitment_id=commitment.id,
    )
    explained = dispatch_tool(
        session, business.tenant.id, "order_explain", {"order_reference": commitment.id}
    )
    assert explained["movements"][0]["id"] == movement.id
    assert explained["movements"][0]["type"] == "shipment"
    assert explained["fulfillment"]["lines"][0]["open_quantity"] == "2.0000"
    from reality.db.core import Shipment

    assert session.query(Shipment).filter_by(tenant_id=business.tenant.id).count() == 0


def test_legacy_delivery_handoff_requires_preparation_without_read_writes(
    session, business, scheduled_owner
):
    from reality.services.core import (
        active_reserved,
        create_commitment,
        record_movement,
    )

    record_movement(
        session,
        business.tenant.id,
        "opening_stock",
        business.item.id,
        "5",
        to_location_id=business.location.id,
    )
    commitment = create_commitment(
        session,
        business.tenant.id,
        "customer_delivery",
        business.company.id,
        business.customer.id,
        business.item.id,
        business.location.id,
        "2",
        None,
    )
    principal = MCPPrincipal(
        "interactive",
        "credential_legacy",
        "grant_legacy",
        scheduled_owner.id,
        business.tenant.id,
        "client_legacy",
        frozenset({"reality:read", "reality:confirm"}),
        frozenset({"proposal_review", "proposal_approve_and_execute"}),
    )
    proposal = ChangeProposal(
        id=uid("act"),
        tenant_id=business.tenant.id,
        type="tool:reserve",
        status="proposed",
        input=json.dumps({"commitment_id": commitment.id, "quantity": "2"}),
        output="{}",
    )
    session.add(proposal)
    session.flush()
    before = (proposal.input, proposal.output)
    review = dispatch_tool(
        session, business.tenant.id, "proposal_review", {"proposal_id": proposal.id}
    )
    confirmation = review["confirmation"]
    assert confirmation["review_preparation_required"]
    assert not confirmation["execution_expected"]
    assert confirmation["arguments"] == {"proposal_id": proposal.id, "approved": True}
    assert confirmation["after_preparation"]["tool"] == "proposal_review"
    assert confirmation["after_preparation"]["requires_new_explicit_approval"]
    assert (proposal.input, proposal.output) == before

    prepared = dispatch_mcp_tool(
        session, principal, "proposal_approve_and_execute", confirmation["arguments"]
    )
    assert prepared["status"] == "proposed"
    assert prepared["requires_new_explicit_approval"]
    assert active_reserved(session, business.tenant.id, business.item.id) == 0
    exact = dispatch_mcp_tool(
        session, principal, "proposal_review", {"proposal_id": proposal.id}
    )
    assert not exact["confirmation"]["review_preparation_required"]
    assert exact["confirmation"]["execution_expected"]
    assert exact["confirmation"]["arguments"]["review_token"]
    executed = dispatch_mcp_tool(
        session,
        principal,
        "proposal_approve_and_execute",
        exact["confirmation"]["arguments"],
    )
    assert executed["status"] == "executed"
    assert active_reserved(session, business.tenant.id, business.item.id) == 2


def test_read_only_mcp_connection_receives_filtered_shipping_page(
    session,
    business,
    padded_shipping,
):
    _, movements = padded_shipping
    principal = MCPPrincipal(
        "manual",
        "shipping_read",
        None,
        None,
        business.tenant.id,
        "shipping_read",
        frozenset({"reality:read", "reality:tool:business_records_discover"}),
        frozenset({"business_records_discover"}),
    )
    result = dispatch_mcp_tool(
        session,
        principal,
        "business_records_discover",
        {"family": "movement", "query": "shipment", "limit": 5},
    )
    assert [row["id"] for row in result["records"]] == [
        movement.id for movement in movements
    ]
    assert result["has_more"] is False
    assert {row["type"] for row in result["records"]} == {"shipment"}
