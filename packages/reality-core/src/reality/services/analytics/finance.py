"""Correction-aware return evidence and canonical order-line billing observations."""

from decimal import Decimal

from sqlalchemy import and_, case, exists, func, literal, select

from reality.db.core import (
    Commitment,
    Document,
    DocumentLine,
    Item,
    Movement,
    MovementCorrection,
)
from reality.services.analytics.budget import check_budget
from reality.services.analytics.execution import AnalyticsError
from reality.services.core import _order_line_billing, movement_quantity
from reality.services.exceptions import _invoice_lines, _quantity_in_agreed_unit


def return_relation(tenant_id, outbound=False):
    voided = exists(
        select(MovementCorrection.id).where(
            MovementCorrection.tenant_id == tenant_id,
            (MovementCorrection.original_movement_id == Movement.id)
            | (MovementCorrection.compensating_movement_id == Movement.id),
        )
    )
    return (
        select(
            Movement.id.label("record_id"),
            literal("movement").label("record_kind"),
            Movement.source_record_id,
            Movement.item_id.label("product_id"),
            Item.name.label("product"),
            Item.unit.label("unit"),
            Movement.type.label("type"),
            Movement.occurred_at,
            Movement.quantity.label("returned_quantity"),
            Movement.quantity.label("moved_quantity"),
            Movement.from_location_id.label("location_id"),
            case(
                (Movement.type == "supplier_return", Commitment.from_party_id),
                else_=Commitment.to_party_id,
            ).label("party_id"),
        )
        .select_from(Movement)
        .join(Item, and_(Item.id == Movement.item_id, Item.tenant_id == tenant_id))
        .outerjoin(
            Commitment,
            and_(
                Commitment.id == Movement.commitment_id,
                Commitment.tenant_id == tenant_id,
            ),
        )
        .where(
            Movement.tenant_id == tenant_id,
            Movement.from_location_id.is_not(None)
            if outbound
            else Movement.type.in_(["return", "supplier_return"]),
            ~voided,
        )
        .subquery()
    )


def billing_rows(session, tenant_id):
    count = session.scalar(
        select(func.count())
        .select_from(DocumentLine)
        .where(DocumentLine.tenant_id == tenant_id)
    )
    if count > 20000:
        raise AnalyticsError(
            "Billing analysis exceeds 20,000 source lines.", "query_too_broad"
        )
    rows = []
    for line, document in session.execute(
        select(DocumentLine, Document)
        .join(
            Document,
            and_(
                Document.id == DocumentLine.document_id, Document.tenant_id == tenant_id
            ),
        )
        .where(
            DocumentLine.tenant_id == tenant_id,
            Document.type.in_(["sales_order", "purchase_order"]),
        )
    ):
        check_budget()
        state = _order_line_billing(session, tenant_id, line.id)
        # Canonical reversal release and canonical quantity compatibility are separate
        # observations. Neither a reversed invoice nor an incompatible unit is hidden.
        released = {r["invoice_line_id"] for r in state["evidence"] if r["released"]}
        evidence = [
            r
            for r in _invoice_lines(session, tenant_id, line.id)
            if r.id not in released
        ]
        billed = _quantity_in_agreed_unit(session, tenant_id, line, evidence)
        movement_type = "shipment" if document.type == "sales_order" else "receipt"
        return_type = "return" if document.type == "sales_order" else "supplier_return"
        promises = list(
            session.scalars(
                select(Commitment).where(
                    Commitment.tenant_id == tenant_id,
                    Commitment.document_line_id == line.id,
                )
            )
        )
        fulfilled = sum(
            (
                movement_quantity(session, tenant_id, c.id, movement_type)
                for c in promises
            ),
            Decimal(0),
        )
        returned = sum(
            (
                movement_quantity(session, tenant_id, c.id, return_type)
                for c in promises
            ),
            Decimal(0),
        )
        item = session.scalar(
            select(Item).where(Item.tenant_id == tenant_id, Item.id == line.item_id)
        )
        compatible = item is not None and item.unit == line.unit
        rows.append(
            {
                "record_id": line.id,
                "record_kind": "document_line",
                "source_record_id": document.source_record_id,
                "order_id": document.id,
                "party_id": document.party_id,
                "product_id": line.item_id,
                "product": state["label"],
                "unit": line.unit,
                "type": document.type,
                "ordered_at": document.ordered_at,
                "ordered_quantity": line.quantity,
                "fulfilled": fulfilled if compatible else None,
                "returned_quantity": returned if compatible else None,
                "billed_quantity": billed,
                "unbilled_quantity": max(fulfilled - returned - billed, Decimal(0))
                if billed is not None and compatible
                else None,
            }
        )
    return rows
