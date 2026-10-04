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
    # One refund is recorded once, whichever version of it arrives: a later
    # payload of the same refund id is not a second refund.
    """Retired writer: prepare and confirm the canonical intake proposal instead."""
    raise core.InvalidOperation(code="intake_approval_required")


def _reduce_cancelled(session, tenant_id, source, order, stated, order_lines) -> list:
    """Lower the promise for refunded goods the shop says will not ship.

    The target is the ordered quantity less every cancelling refund recorded for
    the line, so it does not matter whether the order version that lowered
    `current_quantity` or the refund arrives first: the second finds the promise
    already where it should be.
    """
    from reality.services.shop_order_changes import _needs_reservation_choice

    reduced = []
    cancelling = {
        str(entry.get("line_item_id"))
        for entry in stated
        if entry.get("restock_type") == "cancel"
    }
    for line_id in sorted(cancelling):
        order_line = order_lines[line_id]
        commitment = session.scalar(
            select(Commitment).where(
                Commitment.tenant_id == tenant_id,
                Commitment.document_line_id == order_line.id,
                Commitment.type == "customer_delivery",
            )
        )
        if commitment is None or commitment.status != "open":
            continue
        refunded = Decimal(0)
        for refund in refunds_for_order(session, tenant_id, order):
            for line in session.scalars(
                select(DocumentLine).where(
                    DocumentLine.tenant_id == tenant_id,
                    DocumentLine.document_id == refund.id,
                    DocumentLine.source_line_id == line_id,
                )
            ):
                if json.loads(line.payload or "{}").get("restock_type") == "cancel":
                    refunded += core.decimal(line.quantity)
        target = core.decimal(order_line.quantity) - refunded
        current = core.commitment_quantity(session, tenant_id, commitment.id)
        fulfilled = core.fulfilled_quantity(session, tenant_id, commitment.id)
        if target >= current or target < fulfilled:
            continue
        note = f"Refunded in Shopify before shipment (refund {source.external_id})"
        if target == 0:
            core.cancel_commitment(
                session,
                tenant_id,
                commitment.id,
                reason=note,
                source_record_id=source.id,
                _commit=False,
            )
        elif _needs_reservation_choice(
            session, tenant_id, commitment, target, fulfilled
        ):
            continue
        else:
            core.revise_commitment(
                session,
                tenant_id,
                commitment.id,
                quantity=target,
                note=note,
                source_record_id=source.id,
                _commit=False,
            )
        reduced.append(commitment)
    return reduced


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


def prepare_refund(session, tenant_id, source, job):
    """Freeze received refund evidence and supported operational effects without writing them."""
    from reality.domain.intake import (
        Effect,
        ObservationState,
        PreparedIntake,
        content_digest,
    )
    from reality.services.intake import _reference
    from reality.services.shop_order_changes import _needs_reservation_choice
    from reality.services.shopify_intake import order_state

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
            "The refund names lines the accepted order does not contain.",
        )
    transactions = [
        row
        for row in refund.get("transactions", [])
        if row.get("kind", "refund") == "refund"
        and row.get("status") in {None, "success"}
    ]
    if not transactions or any(row.get("amount") in (None, "") for row in transactions):
        raise ShopRefundNeedsReview(
            "shop_refund_pending",
            "No complete successful monetary refund statement is available.",
        )
    lines = []
    issues = []
    for entry in stated:
        original = order_lines[str(entry["line_item_id"])]
        subtotal = entry.get("subtotal")
        if subtotal in (None, ""):
            issues.append(f"line:{original.source_line_id}:amount_unstated")
        lines.append(
            {
                "source_line_id": original.source_line_id,
                "item_id": original.item_id,
                "sku": original.sku,
                "description": original.description,
                "quantity": str(core.positive(entry.get("quantity", 0))),
                "unit_price": None,
                "gross_amount": None
                if subtotal in (None, "")
                else str(core.decimal(subtotal)),
                "unit": original.unit,
                "line_type": original.line_type,
            }
        )
    effects = []
    for index, transaction in enumerate(transactions):
        amount = str(core.positive(transaction["amount"]))
        currency = transaction.get("currency") or order.currency
        number = (
            f"Refund {source.external_id}"
            if len(transactions) == 1
            else f"Refund {source.external_id} transaction {transaction.get('id', index)}"
        )
        arguments = {
            "document_type": DOCUMENT_TYPE,
            "number": number,
            "party_id": order.party_id,
            "gross_amount": amount,
            "currency": currency,
            "document_date": core._source_document_day(
                session, tenant_id, refund.get("created_at")
            ),
            "source_record_id": source.id,
        }
        if index == 0 and lines:
            arguments.update(lines=lines, sales_channel=order.sales_channel)
            core._preview_manual_document_input(
                session,
                tenant_id,
                **arguments,
                _carry_unstated_price=True,
                _carry_unstated_amount=True,
            )
            arguments["_source_line_payloads"] = stated
            effects.append(Effect(operation="document", arguments=arguments))
        else:
            arguments["amount"] = arguments.pop("gross_amount")
            effects.append(Effect(operation="source_document", arguments=arguments))
    previous = refunds_for_order(session, tenant_id, order)
    for line_id in sorted({str(entry["line_item_id"]) for entry in stated}):
        original = order_lines[line_id]
        commitment = session.scalar(
            select(Commitment).where(
                Commitment.tenant_id == tenant_id,
                Commitment.document_line_id == original.id,
                Commitment.type == "customer_delivery",
            )
        )
        if commitment is None or commitment.status == "cancelled":
            continue
        cancelling = sum(
            (
                core.decimal(entry["quantity"])
                for entry in stated
                if str(entry["line_item_id"]) == line_id
                and entry.get("restock_type") == "cancel"
            ),
            core.ZERO,
        )
        if cancelling and commitment.status == "open":
            for document in previous:
                for line in session.scalars(
                    select(DocumentLine).where(
                        DocumentLine.tenant_id == tenant_id,
                        DocumentLine.document_id == document.id,
                        DocumentLine.source_line_id == line_id,
                    )
                ):
                    if json.loads(line.payload or "{}").get("restock_type") == "cancel":
                        cancelling += line.quantity
            target = original.quantity - cancelling
            current = core.commitment_quantity(session, tenant_id, commitment.id)
            fulfilled = core.fulfilled_quantity(session, tenant_id, commitment.id)
            note = f"Refunded in Shopify before shipment (refund {source.external_id})"
            if target < fulfilled:
                raise ShopRefundNeedsReview(
                    "reduces_shipped_quantity",
                    "The refund would reduce already shipped goods.",
                )
            if target < current:
                if target == 0:
                    effects.append(
                        Effect(
                            operation="commitment_cancellation",
                            arguments={
                                "commitment_id": commitment.id,
                                "reason": note,
                                "source_record_id": source.id,
                            },
                        )
                    )
                elif _needs_reservation_choice(
                    session, tenant_id, commitment, target, fulfilled
                ):
                    raise ShopRefundNeedsReview(
                        "reservation_choice_required",
                        "A reviewer must select the retained reservation identities first.",
                    )
                else:
                    effects.append(
                        Effect(
                            operation="commitment_revision",
                            arguments={
                                "commitment_id": commitment.id,
                                "quantity": str(target),
                                "note": note,
                                "source_record_id": source.id,
                            },
                        )
                    )
        returning = sum(
            (
                core.decimal(entry["quantity"])
                for entry in stated
                if str(entry["line_item_id"]) == line_id
                and entry.get("restock_type") == "return"
            ),
            core.ZERO,
        )
        quantity = min(
            returning, core.announceable_quantity(session, tenant_id, commitment.id)
        )
        if quantity > 0:
            effects.append(
                Effect(
                    operation="return_announcement",
                    arguments={
                        "commitment_id": commitment.id,
                        "quantity": str(quantity),
                        "reference": f"Refund {source.external_id}",
                        "reason": "Refunded in Shopify",
                        "source_record_id": source.id,
                    },
                )
            )
    return PreparedIntake(
        tenant_id=tenant_id,
        source_record_id=source.id,
        source_hash=source.payload_hash,
        source_version=source.version,
        import_job_id=job.id,
        profile="shopify.refund",
        mapping=json.loads(job.input),
        references=(_reference(session, tenant_id, "document", order.id),),
        observations=(
            ObservationState(
                kind="shop_order_state",
                arguments={"order_id": order.id},
                digest=content_digest(order_state(session, tenant_id, order.id)),
            ),
        ),
        effects=tuple(effects),
        issues=tuple(issues),
        row_count=max(1, len(lines) + len(transactions)),
    )
