"""Shopify refunds as their own source records and evidence on the order (spec 296).

A refund is split from the order version that carries it, so it is recorded
even when that version's order changes are held for review, and so the same
refund in a later version is recognised as a duplicate. It becomes a
`sales_refund` document: evidence of money returned, never a posting. Where the
shop states that shipped goods come back, the return is announced, which keeps
it visible until the goods arrive or a person withdraws it.
"""

import json
from decimal import Decimal
from typing import Any

from sqlalchemy import cast, select
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Session

from reality.db.core import (
    Commitment,
    Document,
    DocumentLine,
    SourceRecord,
    uid,
)
from reality.services import core

SOURCE = ("shopify", "refund")
DOCUMENT_TYPE = "sales_refund"


class ShopRefundNeedsReview(core.InterpretationNeedsReview):
    """A refund naming something the order does not have."""

    def __init__(self, reason_code: str, summary: str) -> None:
        super().__init__(summary)
        self.reason_code = reason_code
        self.summary = summary


def split_refunds(
    session: Session,
    tenant_id: str,
    order_payload: dict[str, Any],
    context: dict[str, Any] | None,
) -> list[SourceRecord]:
    """Store each refund an order version carries as its own source record."""
    stored = []
    for refund in order_payload.get("refunds") or []:
        if not isinstance(refund, dict) or refund.get("id") is None:
            continue
        source, _ = core.enqueue_source(
            session,
            tenant_id,
            *SOURCE,
            str(refund["id"]),
            {**refund, "order_id": refund.get("order_id", order_payload.get("id"))},
            context={
                key: value
                for key, value in (context or {}).items()
                if key != "disposition"
            },
            _commit=False,
        )
        stored.append(source)
    return stored


def _order_for_refund(session: Session, tenant_id: str, order_id: Any) -> Document:
    versions = select(SourceRecord.id).where(
        SourceRecord.tenant_id == tenant_id,
        SourceRecord.source_system == "shopify",
        SourceRecord.source_type == "order",
        SourceRecord.external_id == str(order_id),
    )
    order = session.scalar(
        select(Document).where(
            Document.tenant_id == tenant_id,
            Document.type == "sales_order",
            Document.source_record_id.in_(versions),
        )
    )
    if order is None:
        # The order has not been interpreted yet; the job fails and retries.
        raise core.InvalidOperation(code="shop_refund_order_missing")
    return order


def _refunded_amount(refund: dict[str, Any]) -> tuple[Decimal, str | None]:
    """The money the shop states it returned: its successful refund transactions."""
    total, currency = Decimal(0), None
    for transaction in refund.get("transactions") or []:
        if transaction.get("kind", "refund") != "refund":
            continue
        if transaction.get("status") not in {None, "success"}:
            continue
        total += core.decimal(transaction.get("amount") or 0)
        currency = currency or transaction.get("currency")
    return total, currency


def interpret_shop_refund(
    session: Session, tenant_id: str, source: SourceRecord, context: dict[str, Any]
) -> tuple[SourceRecord, Document, list[DocumentLine], list[Any]]:
    existing = session.scalar(
        select(Document).where(
            Document.tenant_id == tenant_id,
            Document.source_record_id == source.id,
            Document.type == DOCUMENT_TYPE,
        )
    )
    if existing:
        lines = list(
            session.scalars(
                select(DocumentLine).where(
                    DocumentLine.tenant_id == tenant_id,
                    DocumentLine.document_id == existing.id,
                )
            )
        )
        return source, existing, lines, []
    refund = json.loads(source.payload)
    order = _order_for_refund(session, tenant_id, refund.get("order_id"))
    order_lines = {
        line.source_line_id: line
        for line in session.scalars(
            select(DocumentLine).where(
                DocumentLine.tenant_id == tenant_id,
                DocumentLine.document_id == order.id,
            )
        )
    }
    stated = refund.get("refund_line_items") or []
    unknown = [
        str(entry.get("line_item_id"))
        for entry in stated
        if str(entry.get("line_item_id")) not in order_lines
    ]
    if unknown:
        raise ShopRefundNeedsReview(
            "shop_refund_line_unknown",
            f"Refund {source.external_id} names order lines {', '.join(unknown)} that "
            f"order {order.number} does not have; nothing was recorded.",
        )
    amount, currency = _refunded_amount(refund)
    document = Document(
        id=uid("doc"),
        tenant_id=tenant_id,
        source_record_id=source.id,
        type=DOCUMENT_TYPE,
        number=f"Refund {source.external_id}",
        party_id=order.party_id,
        currency=currency or order.currency,
        gross_amount=amount,
        status="recorded",
        document_date=core._document_day(refund.get("created_at")),
        sales_channel=order.sales_channel,
    )
    session.add(document)
    session.flush()
    lines = []
    for entry in stated:
        order_line = order_lines[str(entry.get("line_item_id"))]
        line = DocumentLine(
            id=uid("lin"),
            tenant_id=tenant_id,
            document_id=document.id,
            # The Shopify line it refunds; not `billed_document_line_id`, which
            # every billing and crediting reader counts.
            source_line_id=order_line.source_line_id,
            item_id=order_line.item_id,
            sku=order_line.sku,
            description=order_line.description,
            quantity=core.decimal(entry.get("quantity") or 0),
            unit_price=order_line.unit_price,
            gross_amount=core.decimal(entry.get("subtotal") or 0),
            unit=order_line.unit,
            line_type=order_line.line_type,
            payload=json.dumps(entry, ensure_ascii=False, separators=(",", ":")),
        )
        session.add(line)
        lines.append(line)
    session.flush()
    core.emit_business_event(
        session,
        tenant_id,
        "document.recorded",
        "document",
        document.id,
        {
            "type": document.type,
            "number": document.number,
            "party_id": document.party_id,
            "amount": document.gross_amount,
            "currency": document.currency,
            "order_id": order.id,
        },
        source_record_id=source.id,
    )
    announcements = _announce_returns(
        session, tenant_id, source, order, stated, order_lines
    )
    return source, document, lines, announcements


def _announce_returns(session, tenant_id, source, order, stated, order_lines) -> list:
    """Expect back the shipped goods the shop says the customer returns."""
    announced = []
    for entry in stated:
        if entry.get("restock_type") != "return":
            continue
        order_line = order_lines[str(entry.get("line_item_id"))]
        commitment = session.scalar(
            select(Commitment).where(
                Commitment.tenant_id == tenant_id,
                Commitment.document_line_id == order_line.id,
                Commitment.type == "customer_delivery",
            )
        )
        if commitment is None or commitment.status == "cancelled":
            continue
        quantity = min(
            core.decimal(entry.get("quantity") or 0),
            core.announceable_quantity(session, tenant_id, commitment.id),
        )
        if quantity <= 0:
            continue
        announced.append(
            core.announce_customer_return(
                session,
                tenant_id,
                commitment.id,
                quantity,
                reference=f"Refund {source.external_id}",
                reason="Refunded in Shopify",
                source_record_id=source.id,
                _commit=False,
            )
        )
    return announced


def refunds_for_order(
    session: Session, tenant_id: str, order: Document
) -> list[Document]:
    """The refunds recorded for one interpreted Shopify order."""
    order_source = core._tenant_record(
        session, SourceRecord, tenant_id, order.source_record_id
    )
    if (order_source.source_system, order_source.source_type) != ("shopify", "order"):
        return []
    refund_sources = select(SourceRecord.id).where(
        SourceRecord.tenant_id == tenant_id,
        SourceRecord.source_system == SOURCE[0],
        SourceRecord.source_type == SOURCE[1],
        cast(SourceRecord.payload, JSONB)["order_id"].astext
        == order_source.external_id,
    )
    return list(
        session.scalars(
            select(Document)
            .where(
                Document.tenant_id == tenant_id,
                Document.type == DOCUMENT_TYPE,
                Document.source_record_id.in_(refund_sources),
            )
            .order_by(Document.document_date, Document.number)
        )
    )
