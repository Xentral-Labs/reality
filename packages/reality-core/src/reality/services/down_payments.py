"""Down-payment invoices for a sales order (spec 299).

A down-payment invoice is for its order, not for any order line: it states what
the customer is asked to pay before delivery, is posted as a receivable against
received down payments, and is settled by ordinary customer payments. It bills
no quantity, so no billing reader counts it; prepayment readiness counts what
was paid on it.
"""

from __future__ import annotations

import json
from decimal import Decimal
from decimal import InvalidOperation as DecimalInvalid
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from reality.db.core import (
    Document,
    DocumentLine,
    DownPaymentOffset,
    LedgerEntry,
    LedgerReversal,
    SourceRecord,
    uid,
)
from reality.services import core
from reality.services.finance.accounts import lock_finance, resolve_account

ZERO = Decimal(0)
SOURCE_SYSTEM = "internal_down_payment"
AMOUNT_SCALE = Decimal("0.0001")


def _amount(value: Any, code: str) -> Decimal:
    try:
        amount = Decimal(str(value))
    except (DecimalInvalid, TypeError, ValueError) as error:
        raise core.InvalidOperation(code=code) from error
    if not amount.is_finite() or amount <= ZERO or amount.as_tuple().exponent < -4:
        raise core.InvalidOperation(code=code)
    return amount


def _sales_order(session: Session, tenant_id: str, order_id: str) -> Document:
    order = core._tenant_record(session, Document, tenant_id, order_id)
    if order.type != "sales_order" or not order.party_id:
        raise core.InvalidOperation(code="down_payment_order_required")
    return order


def _reversed(session: Session, tenant_id: str, document_id: str) -> bool:
    groups = set(
        session.scalars(
            select(LedgerEntry.posting_group_id).where(
                LedgerEntry.tenant_id == tenant_id,
                LedgerEntry.document_id == document_id,
            )
        )
    )
    if not groups:
        return False
    reversed_groups = set(
        session.scalars(
            select(LedgerReversal.original_posting_group_id).where(
                LedgerReversal.tenant_id == tenant_id,
                LedgerReversal.original_posting_group_id.in_(groups),
            )
        )
    )
    return groups <= reversed_groups


def down_payment_invoices(
    session: Session, tenant_id: str, order_id: str
) -> list[dict[str, Any]]:
    """The order's down-payment invoices with what was paid and already offset."""
    rows = []
    for document in session.scalars(
        select(Document)
        .where(
            Document.tenant_id == tenant_id,
            Document.type == "down_payment_invoice",
            Document.order_document_id == order_id,
        )
        .order_by(Document.document_date, Document.number, Document.id)
    ):
        reversed_ = _reversed(session, tenant_id, document.id)
        gross = Decimal(document.gross_amount)
        open_amount = (
            ZERO
            if reversed_
            else core.open_invoice_amount(session, tenant_id, document.id)
        )
        paid = ZERO if reversed_ else gross - open_amount
        offset = session.scalar(
            select(func.coalesce(func.sum(DownPaymentOffset.amount), 0)).where(
                DownPaymentOffset.tenant_id == tenant_id,
                DownPaymentOffset.down_payment_document_id == document.id,
            )
        )
        rows.append(
            {
                "document_id": document.id,
                "number": document.number,
                "currency": document.currency,
                "gross": gross,
                "open": open_amount,
                "paid": paid,
                "offset": Decimal(offset),
                "offsettable": max(paid - Decimal(offset), ZERO),
                "reversed": reversed_,
            }
        )
    return rows


def preview_down_payment_invoice(
    session: Session,
    tenant_id: str,
    *,
    order_id: str,
    number: str,
    gross_amount: Any,
    currency: str | None = None,
    effective_at: Any = None,
    net_amount: Any = None,
    tax_amount: Any = None,
) -> dict[str, Any]:
    """What recording this down-payment invoice would do, recording nothing."""
    order = _sales_order(session, tenant_id, order_id)
    if not str(number or "").strip():
        raise core.InvalidOperation(code="down_payment_number_missing")
    amount = _amount(gross_amount, "down_payment_amount_invalid")
    # The invoice is in its order's currency; a stated other one is refused.
    if currency and str(currency).strip().upper() != order.currency:
        raise core.InvalidOperation(code="down_payment_currency_mismatch")
    stated = {}
    for key, value in (("net", net_amount), ("tax", tax_amount)):
        if value is not None and str(value).strip() != "":
            try:
                stated[key] = str(Decimal(str(value)))
            except (DecimalInvalid, ValueError) as error:
                raise core.InvalidOperation(
                    code="down_payment_amount_invalid"
                ) from error
    moment = core.utc_datetime(effective_at) or core.now()
    earlier = down_payment_invoices(session, tenant_id, order.id)
    return {
        "order_id": order.id,
        "order_number": order.number,
        "party_id": order.party_id,
        "currency": order.currency,
        "order_gross": str(Decimal(order.gross_amount)),
        "number": str(number).strip(),
        "gross_amount": str(amount),
        "stated": stated,
        "effective_at": moment.isoformat(),
        "earlier_down_payments": [
            {
                "document_id": row["document_id"],
                "number": row["number"],
                "gross": str(row["gross"]),
                "paid": str(row["paid"]),
            }
            for row in earlier
            if not row["reversed"]
        ],
    }


def record_down_payment_invoice(
    session: Session,
    tenant_id: str,
    *,
    order_id: str,
    number: str,
    gross_amount: Any,
    currency: str | None = None,
    effective_at: Any = None,
    net_amount: Any = None,
    tax_amount: Any = None,
    action_id: str | None = None,
    _commit: bool = True,
) -> dict[str, Any]:
    """Record and post a down-payment invoice for its order."""
    core._require_business_mutation(session, tenant_id, "record_down_payment_invoice")
    lock_finance(session, tenant_id)
    preview = preview_down_payment_invoice(
        session,
        tenant_id,
        order_id=order_id,
        number=number,
        gross_amount=gross_amount,
        currency=currency,
        effective_at=effective_at,
        net_amount=net_amount,
        tax_amount=tax_amount,
    )
    external_id = action_id or uid("down_payment")
    existing = session.scalar(
        select(Document)
        .join(
            SourceRecord,
            (SourceRecord.tenant_id == Document.tenant_id)
            & (SourceRecord.id == Document.source_record_id),
        )
        .where(
            Document.tenant_id == tenant_id,
            Document.type == "down_payment_invoice",
            SourceRecord.source_system == SOURCE_SYSTEM,
            SourceRecord.external_id == external_id,
        )
    )
    if existing:
        return _result(existing)
    source, _, _ = core.store_source_record(
        session,
        tenant_id,
        SOURCE_SYSTEM,
        "down_payment_invoice",
        external_id,
        preview,
    )
    amount = Decimal(preview["gross_amount"])
    moment = core.utc_datetime(preview["effective_at"])
    document = core.create_document(
        session,
        tenant_id,
        "down_payment_invoice",
        preview["number"],
        preview["party_id"],
        amount,
        currency=preview["currency"],
        document_date=moment.date().isoformat(),
        source_record_id=source.id,
        action_id=action_id,
        _commit=False,
    )
    document.order_document_id = preview["order_id"]
    session.add(
        DocumentLine(
            id=uid("lin"),
            tenant_id=tenant_id,
            document_id=document.id,
            source_line_id="1",
            sku="",
            description=f"Down payment for {preview['order_number']}",
            quantity=Decimal(1),
            unit_price=amount,
            gross_amount=amount,
            unit="pcs",
            line_type="down_payment",
            # For the order, not for any of its lines: it bills no order line.
            billed_document_line_id=None,
            payload=json.dumps({"stated": preview["stated"]}, sort_keys=True),
        )
    )
    accounts = {
        "accounts_receivable": resolve_account(
            session, tenant_id, "accounts_receivable"
        ).id,
        "customer_down_payments": resolve_account(
            session, tenant_id, "customer_down_payments"
        ).id,
    }
    core.post_ledger(
        session,
        tenant_id,
        document.id,
        preview["party_id"],
        [
            ("accounts_receivable", "debit", amount),
            ("customer_down_payments", "credit", amount),
        ],
        account_ids=accounts,
        currency=preview["currency"],
        source_record_id=source.id,
        effective_at=moment,
        action_id=action_id,
        _commit=False,
    )
    session.flush()
    if _commit:
        session.commit()
    return _result(document)


def _result(document: Document) -> dict[str, Any]:
    return {
        "document_id": document.id,
        "number": document.number,
        "order_id": document.order_document_id,
        "gross_amount": str(Decimal(document.gross_amount).quantize(AMOUNT_SCALE)),
        "currency": document.currency,
    }


def order_down_payment_invoice_ids(
    session: Session, tenant_id: str, order_id: str
) -> set[str]:
    """For readiness: the order's down-payment invoices (spec 299 FR-002)."""
    return set(
        session.scalars(
            select(Document.id).where(
                Document.tenant_id == tenant_id,
                Document.type == "down_payment_invoice",
                Document.order_document_id == order_id,
            )
        )
    )
