from __future__ import annotations

import json
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from reality.db.core import ChangeProposal, Party, uid
from reality.services.core import (
    InvalidOperation,
    active_reserved,
    allocate_credit_note,
    cancel_commitment,
    create_commitment,
    create_document,
    create_item,
    create_location,
    create_party,
    get_tenant,
    ingest_shopify_order,
    open_invoice_amount,
    post_customer_payment,
    post_sales_credit_note,
    post_sales_invoice,
    post_supplier_invoice,
    post_supplier_payment,
    record_movement,
    reserve,
    stock_at,
)

FIXTURE = Path(__file__).parents[3] / "fixtures" / "shopify" / "order_10473.json"
SCENARIO_ACTION = "scenario:normal_month:completed"


def at(day: int, hour: int = 9) -> datetime:
    return datetime(2026, 9, day, hour, 0, 0, tzinfo=UTC)


def _summary(
    session: Session, tenant_id: str, item_id: str, invoice_id: str
) -> dict[str, Any]:
    return {
        "item_id": item_id,
        "invoice_id": invoice_id,
        "physical": stock_at(session, tenant_id, item_id),
        "reserved": active_reserved(session, tenant_id, item_id),
        "receivable": open_invoice_amount(session, tenant_id, invoice_id),
    }


def run_normal_month(session: Session, tenant_id: str) -> dict[str, Any]:
    """Run the fixed September 2026 story once; reruns return the same derived result."""
    get_tenant(session, tenant_id)
    completed = session.scalar(
        select(ChangeProposal).where(
            ChangeProposal.tenant_id == tenant_id,
            ChangeProposal.type == SCENARIO_ACTION,
            ChangeProposal.status == "executed",
        )
    )
    if completed:
        output = json.loads(completed.output)
        return _summary(session, tenant_id, output["item_id"], output["invoice_id"])
    if session.scalar(select(Party.id).where(Party.tenant_id == tenant_id).limit(1)):
        raise InvalidOperation("Normal month requires an empty tenant.")

    company = create_party(session, tenant_id, "Acme Bikes GmbH", "company")
    customer = create_party(session, tenant_id, "Müller GmbH", "customer")
    create_party(session, tenant_id, "Huber Handel GmbH", "customer")
    create_party(session, tenant_id, "Velo Store GmbH", "customer")
    supplier = create_party(session, tenant_id, "Bike Parts GmbH", "supplier")
    create_party(session, tenant_id, "LightWorks AG", "supplier")
    warehouse = create_location(session, tenant_id, "Augsburg Warehouse")
    returns = create_location(session, tenant_id, "Returns Area")
    item = create_item(session, tenant_id, "BIKE-LIGHT", "Bike Light")
    for sku, name in [
        ("BIKE-BELL", "Bike Bell"),
        ("HELMET-M", "Helmet M"),
        ("HELMET-L", "Helmet L"),
        ("LOCK-01", "Bike Lock"),
    ]:
        create_item(session, tenant_id, sku, name)

    record_movement(
        session,
        tenant_id,
        "opening_stock",
        item.id,
        20,
        to_location_id=warehouse.id,
        occurred_at=at(1),
    )
    normal = {
        "id": 5837291002,
        "order_number": 10402,
        "name": "#10402",
        "created_at": "2026-09-02T09:15:00Z",
        "currency": "EUR",
        "total_price": "245.00",
        "line_items": [
            {
                "id": 8102,
                "sku": "BIKE-LIGHT",
                "name": "Bike Light",
                "quantity": 5,
                "price": "49.00",
            }
        ],
        "note_attributes": [{"name": "requested_delivery", "value": "2026-09-02"}],
    }
    _, _, _, normal_commitments = ingest_shopify_order(
        session, tenant_id, normal, company.id, customer.id, warehouse.id
    )
    reserve(session, tenant_id, normal_commitments[0].id)
    record_movement(
        session,
        tenant_id,
        "shipment",
        item.id,
        5,
        from_location_id=warehouse.id,
        commitment_id=normal_commitments[0].id,
        occurred_at=at(2, 14),
    )

    large = json.loads(FIXTURE.read_text())
    _, sales_order, _, customer_commitments = ingest_shopify_order(
        session, tenant_id, large, company.id, customer.id, warehouse.id
    )
    customer_commitment = customer_commitments[0]
    first_allocation = reserve(session, tenant_id, customer_commitment.id)
    assert first_allocation.shortage == Decimal("15.0000")
    purchase = create_commitment(
        session,
        tenant_id,
        "supplier_delivery",
        supplier.id,
        company.id,
        item.id,
        warehouse.id,
        20,
        "2026-09-10",
        amount=600,
    )
    record_movement(
        session,
        tenant_id,
        "receipt",
        item.id,
        8,
        to_location_id=warehouse.id,
        commitment_id=purchase.id,
        occurred_at=at(7),
    )
    record_movement(
        session,
        tenant_id,
        "receipt",
        item.id,
        12,
        to_location_id=warehouse.id,
        commitment_id=purchase.id,
        occurred_at=at(10),
    )
    reserve(session, tenant_id, customer_commitment.id)
    record_movement(
        session,
        tenant_id,
        "shipment",
        item.id,
        12,
        from_location_id=warehouse.id,
        commitment_id=customer_commitment.id,
        occurred_at=at(11),
    )
    record_movement(
        session,
        tenant_id,
        "shipment",
        item.id,
        18,
        from_location_id=warehouse.id,
        commitment_id=customer_commitment.id,
        occurred_at=at(13),
    )
    cancelled = create_commitment(
        session,
        tenant_id,
        "customer_delivery",
        company.id,
        customer.id,
        item.id,
        warehouse.id,
        4,
        "2026-09-18",
        amount=196,
    )
    reserve(session, tenant_id, cancelled.id)
    cancel_commitment(
        session,
        tenant_id,
        cancelled.id,
        reason="Customer cancelled before shipment",
    )
    record_movement(
        session,
        tenant_id,
        "return",
        item.id,
        2,
        to_location_id=returns.id,
        occurred_at=at(18),
    )
    record_movement(
        session,
        tenant_id,
        "adjustment",
        item.id,
        1,
        from_location_id=returns.id,
        occurred_at=at(20),
        reason="Damaged return",
    )

    invoice = create_document(
        session,
        tenant_id,
        "sales_invoice",
        "RE-10473",
        customer.id,
        sales_order.gross_amount,
        document_date="2026-09-22",
    )
    post_sales_invoice(session, tenant_id, invoice.id, effective_at=at(22))
    post_customer_payment(session, tenant_id, invoice.id, 500, effective_at=at(25))
    credit = create_document(
        session,
        tenant_id,
        "credit_note",
        "GS-10473",
        customer.id,
        100,
        document_date="2026-09-27",
    )
    post_sales_credit_note(session, tenant_id, credit.id, effective_at=at(27))
    allocate_credit_note(session, tenant_id, credit.id, invoice.id, 100)
    supplier_invoice = create_document(
        session,
        tenant_id,
        "supplier_invoice",
        "ER-2201",
        supplier.id,
        600,
        document_date="2026-09-22",
    )
    post_supplier_invoice(
        session, tenant_id, supplier_invoice.id, effective_at=at(22, 11)
    )
    post_supplier_payment(
        session, tenant_id, supplier_invoice.id, 250, effective_at=at(25, 11)
    )

    session.add(
        ChangeProposal(
            id=uid("act"),
            tenant_id=tenant_id,
            type=SCENARIO_ACTION,
            actor_type="scenario",
            status="executed",
            input="{}",
            output=json.dumps({"item_id": item.id, "invoice_id": invoice.id}),
            created_at=at(30),
        )
    )
    session.commit()
    return _summary(session, tenant_id, item.id, invoice.id)
