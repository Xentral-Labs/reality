import json
from decimal import Decimal

import pytest
from conftest import record_by_id
from sqlalchemy import func, select

from reality.db.core import Document, Movement, Reservation, Shipment
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


def _order(session, business, number, term):
    tenant_id = business.tenant.id
    document, lines = core.create_manual_document_with_lines(
        session,
        tenant_id,
        "sales_order",
        number,
        business.customer.id,
        [
            {
                "sku": business.item.sku,
                "item_id": business.item.id,
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
        business.customer.id,
        business.item.id,
        business.location.id,
        "10",
        None,
        amount="100",
        document_id=document.id,
        document_line_id=lines[0].id,
    )
    core.reserve(session, tenant_id, commitment.id)
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
