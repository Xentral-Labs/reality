import json
from decimal import Decimal

import pytest
from conftest import record_by_id
from sqlalchemy import func, select

from reality.db.core import ChangeProposal, Document, Movement, Reservation, Shipment
from reality.mcp.catalog import dispatch_tool
from reality.services import core
from reality.services.fulfillment_readiness import fulfillment_readiness
from reality.services.shipments import record_packaged_execution
from reality.tools.application import (
    approve_and_execute_proposal,
    create_change_proposal,
    reject_proposal,
    run_read_tool,
)


def _order(
    session,
    business,
    number,
    term,
    due_at=None,
    *,
    customer=None,
    item=None,
    reserve_quantity=None,
):
    tenant_id = business.tenant.id
    customer = customer or business.customer
    item = item or business.item
    document, lines = core.create_manual_document_with_lines(
        session,
        tenant_id,
        "sales_order",
        number,
        customer.id,
        [
            {
                "sku": item.sku,
                "item_id": item.id,
                "quantity": "10",
                "unit_price": "10",
                "gross_amount": "100",
            }
        ],
        "100",
        payment_term_code=term,
    )
    commitment = core.create_commitment(
        session,
        tenant_id,
        "customer_delivery",
        business.company.id,
        customer.id,
        item.id,
        business.location.id,
        "10",
        due_at,
        amount="100",
        document_id=document.id,
        document_line_id=lines[0].id,
    )
    core.reserve(session, tenant_id, commitment.id, reserve_quantity)
    return document, lines[0], commitment


def _invoice(session, tenant_id, line, number):
    receipt = core.record_sales_invoice(
        session, tenant_id, line.id, "10", "100", number
    )
    return record_by_id(
        session,
        Document,
        next(row["id"] for row in receipt["records"] if row["family"] == "document"),
    )


def _dispatch(session, business, commitment):
    proposal = create_change_proposal(
        session,
        business.tenant.id,
        "shipment_dispatch",
        {
            "purpose": "customer_delivery",
            "counterparty_id": business.customer.id,
            "movements": [
                {
                    "commitment_id": commitment.id,
                    "item_id": business.item.id,
                    "from_location_id": business.location.id,
                    "quantity": "10",
                }
            ],
        },
    )
    token = json.loads(proposal.input)["_delivery_review"]["token"]
    return approve_and_execute_proposal(
        session,
        business.tenant.id,
        proposal.id,
        review_token=token,
        confirmed=True,
    )


def test_two_order_story_keeps_unpaid_prepayment_stock_inside(session, business):
    tenant_id = business.tenant.id
    core.create_payment_term(session, tenant_id, "NET14", "Net 14", 14)
    core.create_payment_term(
        session,
        tenant_id,
        "PREPAY",
        "Pay before dispatch",
        0,
        requires_prepayment=True,
    )
    core.record_movement(
        session,
        tenant_id,
        "opening_stock",
        business.item.id,
        "30",
        to_location_id=business.location.id,
    )
    net_order, net_line, net_commitment = _order(
        session, business, "SO-NET", "NET14"
    )
    prepay_order, prepay_line, prepay_commitment = _order(
        session, business, "SO-PREPAY", "PREPAY"
    )

    net_invoice = _invoice(session, tenant_id, net_line, "INV-NET")
    assert core.open_invoice_amount(session, tenant_id, net_invoice.id) == Decimal(100)
    _dispatch(session, business, net_commitment)
    core.post_customer_payment(session, tenant_id, net_invoice.id, "100")

    prepay_invoice = _invoice(session, tenant_id, prepay_line, "INV-PREPAY")
    before = fulfillment_readiness(session, tenant_id, prepay_commitment.id)
    assert before.blocker_codes == ("prepayment_required",)
    assert before.required_amount == Decimal(100)
    assert before.received_amount == 0
    assert before.remaining_amount == Decimal(100)
    explained_before_payment = run_read_tool(
        session,
        tenant_id,
        "order_explain",
        {"order_reference": prepay_order.id},
    )
    assert explained_before_payment["fulfillment"]["ship_ready"] is False
    assert "prepayment_required" in explained_before_payment["fulfillment"][
        "blocking_reasons"
    ]
    assert run_read_tool(
        session,
        tenant_id,
        "fulfillment_readiness",
        {"commitment_id": prepay_commitment.id},
    ) == dispatch_tool(
        session,
        tenant_id,
        "fulfillment_readiness",
        {"commitment_id": prepay_commitment.id},
    )

    shipment_count = session.scalar(select(func.count()).select_from(Shipment))
    movement_count = session.scalar(select(func.count()).select_from(Movement))
    with pytest.raises(core.InvalidOperation, match="prepayment_required"):
        _dispatch(session, business, prepay_commitment)
    assert session.scalar(select(func.count()).select_from(Shipment)) == shipment_count
    assert session.scalar(select(func.count()).select_from(Movement)) == movement_count
    with pytest.raises(core.InvalidOperation, match="prepayment_required"):
        record_packaged_execution(
            session,
            tenant_id,
            direction="outbound",
            purpose="customer_delivery",
            counterparty_id=business.customer.id,
            movements=[
                {
                    "commitment_id": prepay_commitment.id,
                    "item_id": business.item.id,
                    "from_location_id": business.location.id,
                    "quantity": "10",
                }
            ],
        )
    assert session.scalar(select(func.count()).select_from(Shipment)) == shipment_count
    assert session.scalar(select(func.count()).select_from(Movement)) == movement_count
    with pytest.raises(core.InvalidOperation, match="valid movement quantity"):
        record_packaged_execution(
            session,
            tenant_id,
            direction="outbound",
            purpose="customer_delivery",
            counterparty_id=business.customer.id,
            movements=[{"commitment_id": prepay_commitment.id}],
        )

    core.post_customer_payment(session, tenant_id, prepay_invoice.id, "40")
    partial = fulfillment_readiness(session, tenant_id, prepay_commitment.id)
    assert partial.received_amount == Decimal(40)
    assert partial.remaining_amount == Decimal(60)
    assert partial.ship_ready is False
    core.post_customer_payment(session, tenant_id, prepay_invoice.id, "60")
    reviewed = create_change_proposal(
        session,
        tenant_id,
        "shipment_dispatch",
        {
            "purpose": "customer_delivery",
            "counterparty_id": business.customer.id,
            "movements": [
                {
                    "commitment_id": prepay_commitment.id,
                    "item_id": business.item.id,
                    "from_location_id": business.location.id,
                    "quantity": "10",
                }
            ],
        },
    )
    reviewed_token = json.loads(reviewed.input)["_delivery_review"]["token"]
    core.hold_commitment(
        session, tenant_id, prepay_commitment.id, "manual_review", "Final check"
    )
    with pytest.raises(core.InvalidOperation, match="hold"):
        approve_and_execute_proposal(
            session,
            tenant_id,
            reviewed.id,
            review_token=reviewed_token,
            confirmed=True,
        )
    session.refresh(reviewed)
    assert reviewed.status == "proposed"
    reject_proposal(session, tenant_id, reviewed.id)
    core.release_commitment_hold(session, tenant_id, prepay_commitment.id)
    executed_dispatch = _dispatch(session, business, prepay_commitment)
    execution_status = run_read_tool(
        session,
        tenant_id,
        "proposal_execution_status",
        {"proposal_id": executed_dispatch.id},
    )
    assert execution_status["status"] == "executed"
    assert "observation" in execution_status
    completed = fulfillment_readiness(session, tenant_id, prepay_commitment.id)
    assert completed.open_quantity == 0
    assert completed.ship_ready is False
    explained_after_dispatch = run_read_tool(
        session,
        tenant_id,
        "order_explain",
        {"order_reference": prepay_order.id},
    )
    assert explained_after_dispatch["fulfillment"]["readiness"] == "closed"
    assert explained_after_dispatch["fulfillment"]["ship_ready"] is False
    assert explained_after_dispatch["fulfillment"]["lines"][0]["readiness"][
        "ship_ready"
    ] is False

    assert core.stock_at(session, tenant_id, business.item.id, business.location.id) == 10
    assert core.open_invoice_amount(session, tenant_id, net_invoice.id) == 0
    assert core.open_invoice_amount(session, tenant_id, prepay_invoice.id) == 0
    assert (
        session.scalar(
            select(func.coalesce(func.sum(Reservation.quantity), 0)).where(
                Reservation.tenant_id == tenant_id,
                Reservation.status == "active",
            )
        )
        == 0
    )
    assert net_order.id != prepay_order.id


def test_exact_stocked_and_reserved_partial_quantity_can_ship(session, business):
    tenant_id = business.tenant.id
    core.create_payment_term(session, tenant_id, "NET30", "Net 30", 30)
    core.record_movement(
        session,
        tenant_id,
        "opening_stock",
        business.item.id,
        "4",
        to_location_id=business.location.id,
    )
    _order_document, _line, commitment = _order(
        session, business, "SO-PARTIAL", "NET30"
    )
    before = fulfillment_readiness(session, tenant_id, commitment.id)
    assert before.open_quantity == 10
    assert before.reserved_quantity == 4
    assert before.ship_ready is False

    proposal = create_change_proposal(
        session,
        tenant_id,
        "shipment_dispatch",
        {
            "purpose": "customer_delivery",
            "counterparty_id": business.customer.id,
            "movements": [
                {
                    "commitment_id": commitment.id,
                    "item_id": business.item.id,
                    "from_location_id": business.location.id,
                    "quantity": "4",
                }
            ],
        },
    )
    review = json.loads(proposal.input)["_delivery_review"]
    assert review["state"]["movement_previews"][0]["fulfillment_readiness"][
        "ship_ready"
    ] is True
    approve_and_execute_proposal(
        session,
        tenant_id,
        proposal.id,
        review_token=review["token"],
        confirmed=True,
    )

    after = fulfillment_readiness(session, tenant_id, commitment.id)
    assert after.open_quantity == 6
    assert after.reserved_quantity == 0
    assert core.stock_at(session, tenant_id, business.item.id, business.location.id) == 0


def test_agent_proposes_future_prepayment_and_partial_shipment_without_self_execution(
    session, business
):
    tenant_id = business.tenant.id
    core.create_payment_term(
        session,
        tenant_id,
        "AGENT-PREPAY",
        "Pay before dispatch",
        0,
        requires_prepayment=True,
    )
    core.record_movement(
        session,
        tenant_id,
        "opening_stock",
        business.item.id,
        "4",
        to_location_id=business.location.id,
    )
    order, line, commitment = _order(
        session,
        business,
        "SO-AGENT-FUTURE",
        "AGENT-PREPAY",
        "2026-12-15T00:00:00+00:00",
    )
    invoice_count = session.scalar(
        select(func.count()).select_from(Document).where(Document.type == "sales_invoice")
    )
    invoice_proposal = dispatch_tool(
        session,
        tenant_id,
        "sales_invoice_record_propose",
        {
            "number": "INV-AGENT-PREPAY",
            "gross_amount": "100",
            "lines": [
                {
                    "order_line_id": line.id,
                    "quantity": "10",
                    "gross_amount": "100",
                }
            ],
        },
    )
    assert invoice_proposal["status"] == "proposed"
    assert invoice_proposal["requires_confirmation"] is True
    assert (
        session.scalar(
            select(func.count()).select_from(Document).where(
                Document.type == "sales_invoice"
            )
        )
        == invoice_count
    )
    invoice_candidate = record_by_id(
        session, ChangeProposal, invoice_proposal["proposal_id"]
    )
    invoice_token = json.loads(invoice_candidate.input)["_delivery_review"]["token"]
    approve_and_execute_proposal(
        session,
        tenant_id,
        invoice_candidate.id,
        review_token=invoice_token,
        confirmed=True,
    )
    invoice = session.scalar(
        select(Document).where(
            Document.tenant_id == tenant_id,
            Document.type == "sales_invoice",
            Document.number == "INV-AGENT-PREPAY",
        )
    )
    assert invoice is not None
    core.post_customer_payment(session, tenant_id, invoice.id, "100")
    movement_count = session.scalar(select(func.count()).select_from(Movement))
    shipment_proposal = dispatch_tool(
        session,
        tenant_id,
        "shipment_dispatch_propose",
        {
            "purpose": "customer_delivery",
            "counterparty_id": business.customer.id,
            "movements": [
                {
                    "commitment_id": commitment.id,
                    "item_id": business.item.id,
                    "from_location_id": business.location.id,
                    "quantity": "4",
                }
            ],
        },
    )
    assert shipment_proposal["status"] == "proposed"
    assert shipment_proposal["requires_confirmation"] is True
    assert session.scalar(select(func.count()).select_from(Movement)) == movement_count
    shipment_candidate = record_by_id(
        session, ChangeProposal, shipment_proposal["proposal_id"]
    )
    shipment_token = json.loads(shipment_candidate.input)["_delivery_review"]["token"]
    approve_and_execute_proposal(
        session,
        tenant_id,
        shipment_candidate.id,
        review_token=shipment_token,
        confirmed=True,
    )
    final = fulfillment_readiness(session, tenant_id, commitment.id)
    assert order.id == final.order_id
    assert final.open_quantity == 6
    assert final.received_amount == 100

    replenishment = core.create_commitment(
        session,
        tenant_id,
        "supplier_delivery",
        business.supplier.id,
        business.company.id,
        business.item.id,
        business.location.id,
        "6",
        "2026-12-10T00:00:00+00:00",
    )
    core.record_movement(
        session,
        tenant_id,
        "receipt",
        business.item.id,
        "6",
        to_location_id=business.location.id,
        commitment_id=replenishment.id,
    )
    core.reserve(session, tenant_id, commitment.id, "6")
    rest_movement_count = session.scalar(select(func.count()).select_from(Movement))
    rest_proposal = dispatch_tool(
        session,
        tenant_id,
        "shipment_dispatch_propose",
        {
            "purpose": "customer_delivery",
            "counterparty_id": business.customer.id,
            "movements": [
                {
                    "commitment_id": commitment.id,
                    "item_id": business.item.id,
                    "from_location_id": business.location.id,
                    "quantity": "6",
                }
            ],
        },
    )
    assert session.scalar(select(func.count()).select_from(Movement)) == rest_movement_count
    rest_candidate = record_by_id(session, ChangeProposal, rest_proposal["proposal_id"])
    rest_token = json.loads(rest_candidate.input)["_delivery_review"]["token"]
    approve_and_execute_proposal(
        session,
        tenant_id,
        rest_candidate.id,
        review_token=rest_token,
        confirmed=True,
    )
    completed = fulfillment_readiness(session, tenant_id, commitment.id)
    assert completed.open_quantity == 0
    assert completed.ship_ready is False
    assert core.stock_at(session, tenant_id, business.item.id, business.location.id) == 0


def test_agent_readiness_matrix_distinguishes_multiple_customers(session, business):
    tenant_id = business.tenant.id
    customer_paid = core.create_party(
        session, tenant_id, "Ready Industries", "customer"
    )
    customer_unpaid = core.create_party(
        session, tenant_id, "Prepay Wholesale", "customer"
    )
    customer_partial = core.create_party(
        session, tenant_id, "Partial Components", "customer"
    )
    core.create_payment_term(session, tenant_id, "MATRIX-NET", "Net", 14)
    core.create_payment_term(
        session,
        tenant_id,
        "MATRIX-PREPAY",
        "Prepayment",
        0,
        requires_prepayment=True,
    )
    core.record_movement(
        session,
        tenant_id,
        "opening_stock",
        business.item.id,
        "20",
        to_location_id=business.location.id,
    )
    partial_item = core.create_item(
        session, tenant_id, "MATRIX-PART", "Partially stocked assembly"
    )
    core.record_movement(
        session,
        tenant_id,
        "opening_stock",
        partial_item.id,
        "4",
        to_location_id=business.location.id,
    )
    ready_order, _, ready = _order(
        session,
        business,
        "SO-MATRIX-READY",
        "MATRIX-NET",
        "2026-11-01T00:00:00+00:00",
        customer=customer_paid,
    )
    unpaid_order, unpaid_line, unpaid = _order(
        session,
        business,
        "SO-MATRIX-UNPAID",
        "MATRIX-PREPAY",
        "2026-11-15T00:00:00+00:00",
        customer=customer_unpaid,
    )
    partial_order, _, partial = _order(
        session,
        business,
        "SO-MATRIX-PARTIAL",
        "MATRIX-NET",
        "2026-12-01T00:00:00+00:00",
        customer=customer_partial,
        item=partial_item,
        reserve_quantity="4",
    )
    _invoice(session, tenant_id, unpaid_line, "INV-MATRIX-UNPAID")

    matrix = {
        "ready": fulfillment_readiness(session, tenant_id, ready.id),
        "unpaid": fulfillment_readiness(session, tenant_id, unpaid.id),
        "partial": fulfillment_readiness(session, tenant_id, partial.id),
    }
    assert matrix["ready"].ship_ready is True
    assert matrix["ready"].blocker_codes == ()
    assert matrix["unpaid"].blocker_codes == ("prepayment_required",)
    assert matrix["unpaid"].remaining_amount == 100
    assert matrix["partial"].ship_ready is False
    assert matrix["partial"].blocker_codes == (
        "insufficient_reservation",
        "insufficient_stock",
    )
    assert matrix["partial"].reserved_quantity == 4
    assert matrix["partial"].physical_quantity == 4
    assert {
        ready_order.party_id,
        unpaid_order.party_id,
        partial_order.party_id,
    } == {customer_paid.id, customer_unpaid.id, customer_partial.id}
    for commitment in (ready, unpaid, partial):
        agent_read = dispatch_tool(
            session,
            tenant_id,
            "fulfillment_readiness",
            {"commitment_id": commitment.id},
        )
        assert agent_read["commitment_id"] == commitment.id
        assert agent_read["order_id"] == commitment.document_id
