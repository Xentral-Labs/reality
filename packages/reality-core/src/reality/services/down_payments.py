"""Down-payment and pro-forma invoices for a sales order (spec 299).

A down-payment invoice is for its order, not for any order line: it states what
the customer is asked to pay before delivery, is posted as a receivable against
received down payments, and is settled by ordinary customer payments. It bills
no quantity, so no billing reader counts it; prepayment readiness counts what
was paid on it.
"""

from __future__ import annotations

import json
from datetime import date
from decimal import Decimal
from decimal import InvalidOperation as DecimalInvalid
from typing import Any

from sqlalchemy import select
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
PROFORMA_SOURCE_SYSTEM = "internal_proforma"
PROFORMA_FIELDS = {"order_id", "number", "gross_amount"}
PROFORMA_OPTIONAL = {"currency", "document_date", "lines"}
PROFORMA_LINE_FIELDS = {"description", "quantity", "gross_amount"}
PROFORMA_LINE_OPTIONAL = {"net_amount", "tax_amount"}
AMOUNT_SCALE = Decimal("0.0001")


def _positive(value: Any) -> Decimal | None:
    """A positive amount with at most four decimals, or None."""
    try:
        amount = Decimal(str(value))
    except (DecimalInvalid, TypeError, ValueError):
        return None
    if not amount.is_finite() or amount <= ZERO or amount.as_tuple().exponent < -4:
        return None
    return amount


def _amount(value: Any, code: str) -> Decimal:
    amount = _positive(value)
    if amount is None:
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


def _cash_received(session: Session, tenant_id: str, document_id: str) -> Decimal:
    """What active payments, not credits or write-offs, allocated to the invoice."""
    controls = set(
        session.scalars(
            select(LedgerEntry.id).where(
                LedgerEntry.tenant_id == tenant_id,
                LedgerEntry.document_id == document_id,
                LedgerEntry.account == "accounts_receivable",
                LedgerEntry.debit_credit == "debit",
            )
        )
    )
    if not controls:
        return ZERO
    allocations = [
        row
        for row in core.active_settlement_allocations(
            session, tenant_id, entry_ids=controls
        )
        if row.invoice_ledger_entry_id in controls
    ]
    if not allocations:
        return ZERO
    payment_groups = dict(
        session.execute(
            select(LedgerEntry.id, LedgerEntry.posting_group_id).where(
                LedgerEntry.tenant_id == tenant_id,
                LedgerEntry.id.in_(
                    {row.payment_ledger_entry_id for row in allocations}
                ),
            )
        ).all()
    )
    cash_groups = set(
        session.scalars(
            select(LedgerEntry.posting_group_id).where(
                LedgerEntry.tenant_id == tenant_id,
                LedgerEntry.account == "cash",
                LedgerEntry.posting_group_id.in_(set(payment_groups.values())),
            )
        )
    )
    return sum(
        (
            Decimal(row.amount)
            for row in allocations
            if payment_groups.get(row.payment_ledger_entry_id) in cash_groups
        ),
        ZERO,
    )


def _offset_groups(
    session: Session, tenant_id: str, final_ids: set[str]
) -> dict[str, set[str]]:
    """Each final invoice's offset posting groups that are not reversed."""
    if not final_ids:
        return {}
    groups: dict[str, set[str]] = {}
    for document_id, group in session.execute(
        select(LedgerEntry.document_id, LedgerEntry.posting_group_id).where(
            LedgerEntry.tenant_id == tenant_id,
            LedgerEntry.document_id.in_(final_ids),
            LedgerEntry.account == "customer_down_payments",
            LedgerEntry.debit_credit == "debit",
        )
    ):
        groups.setdefault(document_id, set()).add(group)
    reversed_groups = set(
        session.scalars(
            select(LedgerReversal.original_posting_group_id).where(
                LedgerReversal.tenant_id == tenant_id,
                LedgerReversal.original_posting_group_id.in_(
                    {group for values in groups.values() for group in values}
                ),
            )
        )
    )
    return {
        document_id: live
        for document_id, values in groups.items()
        if (live := values - reversed_groups)
    }


def live_offsets(
    session: Session,
    tenant_id: str,
    *,
    down_payment_ids: set[str] | None = None,
    final_invoice_ids: set[str] | None = None,
) -> list[DownPaymentOffset]:
    """Offsets whose posting on the final invoice still stands.

    Reversing that posting releases the offset: the down payment can be offset
    again, and the final invoice is open for the full amount once more.
    """
    query = select(DownPaymentOffset).where(DownPaymentOffset.tenant_id == tenant_id)
    if down_payment_ids is not None:
        query = query.where(
            DownPaymentOffset.down_payment_document_id.in_(down_payment_ids)
        )
    if final_invoice_ids is not None:
        query = query.where(
            DownPaymentOffset.final_invoice_document_id.in_(final_invoice_ids)
        )
    rows = list(session.scalars(query.order_by(DownPaymentOffset.id)))
    live = _offset_groups(
        session, tenant_id, {row.final_invoice_document_id for row in rows}
    )
    return [row for row in rows if row.final_invoice_document_id in live]


def assert_reversal_keeps_offsets(
    session: Session, tenant_id: str, entries: list[LedgerEntry]
) -> None:
    """Refuse a reversal that would leave a standing offset without its basis.

    The final invoice is reversed only after its offset; a down-payment invoice,
    or a payment of it, only once no standing offset deducts it (spec 299).
    """
    if not session.scalar(
        select(DownPaymentOffset.id)
        .where(DownPaymentOffset.tenant_id == tenant_id)
        .limit(1)
    ):
        return
    documents = {entry.document_id for entry in entries if entry.document_id}
    accounts = {entry.account for entry in entries}
    if (
        documents
        and "customer_down_payments" not in accounts
        and live_offsets(session, tenant_id, final_invoice_ids=documents)
    ):
        raise core.InvalidOperation(code="down_payment_offset_reverse_first")
    down_payments = set(documents)
    allocations = core.active_settlement_allocations(
        session, tenant_id, entry_ids={entry.id for entry in entries}
    )
    paid = {
        row.invoice_ledger_entry_id
        for row in allocations
        if row.payment_ledger_entry_id in {entry.id for entry in entries}
    }
    if paid:
        down_payments |= set(
            session.scalars(
                select(LedgerEntry.document_id).where(
                    LedgerEntry.tenant_id == tenant_id, LedgerEntry.id.in_(paid)
                )
            )
        )
    is_offset_group = "customer_down_payments" in accounts and any(
        entry.account == "customer_down_payments" and entry.debit_credit == "debit"
        for entry in entries
    )
    if (
        not is_offset_group
        and down_payments
        and live_offsets(session, tenant_id, down_payment_ids=down_payments)
    ):
        raise core.InvalidOperation(code="down_payment_offset_active")


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
        # Paid means money received: a credit or write-off that settles the
        # invoice is no down payment anyone can deduct later.
        paid = ZERO if reversed_ else _cash_received(session, tenant_id, document.id)
        offset = sum(
            (
                Decimal(row.amount)
                for row in live_offsets(
                    session, tenant_id, down_payment_ids={document.id}
                )
            ),
            ZERO,
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
    """
    What recording this down-payment invoice would do, recording nothing.

    BUSINESS PURPOSE:
    What recording this down-payment invoice would do, recording nothing.

    BUSINESS RULE services.down_payments.preview_down_payment_invoice.refusal-14:
    IF the down-payment invoice number is empty after trimming whitespace:
        Refuse with down_payment_number_missing.

    BUSINESS RULE services.down_payments.preview_down_payment_invoice.refusal-18:
    IF a currency was supplied and its normalized value differs from the sales order currency:
        Refuse with down_payment_currency_mismatch.

    BUSINESS RULE services.down_payments.preview_down_payment_invoice.result:
    Return the current result with order_id, order_number, party_id, currency, order_gross, number, gross_amount, stated, effective_at, earlier_down_payments.
    """
    order = _sales_order(session, tenant_id, order_id)
    # reality-rule: services.down_payments.preview_down_payment_invoice.refusal-14
    if not str(number or "").strip():
        raise core.InvalidOperation(code="down_payment_number_missing")
    amount = _amount(gross_amount, "down_payment_amount_invalid")
    # The invoice is in its order's currency; a stated other one is refused.
    # reality-rule: services.down_payments.preview_down_payment_invoice.refusal-18
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
    # reality-rule: services.down_payments.preview_down_payment_invoice.result
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
    """
    Record and post a down-payment invoice for its order.

    BUSINESS PURPOSE:
    Record and post a down-payment invoice for its order.

    BUSINESS RULE services.down_payments.record_down_payment_invoice.step-15:
    Require the business permission for 'record_down_payment_invoice' before changing company records.

    BUSINESS RULE services.down_payments.record_down_payment_invoice.step-17:
    Run the shared preview down payment invoice check and use its normalized inputs and current review evidence. Inspect that called function for its detailed eligibility rules.

    BUSINESS RULE services.down_payments.record_down_payment_invoice.step-45:
    Pass the stated inputs to the shared store source record service. Its own source describes validation and record changes.

    BUSINESS RULE services.down_payments.record_down_payment_invoice.step-55:
    Pass the stated inputs to the shared create document service. Its own source describes validation and record changes.

    BUSINESS RULE services.down_payments.record_down_payment_invoice.result:
    Return the recorded down-payment invoice and its posting receipt using the common invoice result reader.
    """
    # reality-rule: services.down_payments.record_down_payment_invoice.step-15
    core._require_business_mutation(session, tenant_id, "record_down_payment_invoice")
    lock_finance(session, tenant_id)
    # reality-rule: services.down_payments.record_down_payment_invoice.step-17
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
    # reality-rule: services.down_payments.record_down_payment_invoice.step-45
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
    # reality-rule: services.down_payments.record_down_payment_invoice.step-55
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
    # reality-rule: services.down_payments.record_down_payment_invoice.result
    return _result(document)


def _result(document: Document) -> dict[str, Any]:
    return {
        "document_id": document.id,
        "number": document.number,
        "order_id": document.order_document_id,
        "gross_amount": str(Decimal(document.gross_amount).quantize(AMOUNT_SCALE)),
        "currency": document.currency,
    }


def down_payment_offers(
    session: Session, tenant_id: str, order_ids: list[str]
) -> list[dict[str, Any]]:
    """What a final invoice for these orders may offset (spec 299 FR-003)."""
    return [
        {
            key: str(row[key].quantize(AMOUNT_SCALE))
            if isinstance(row[key], Decimal)
            else row[key]
            for key in (
                "document_id",
                "number",
                "currency",
                "gross",
                "paid",
                "offset",
                "offsettable",
            )
        }
        for order_id in dict.fromkeys(order_ids)
        for row in down_payment_invoices(session, tenant_id, order_id)
        if not row["reversed"]
    ]


def preview_offsets(
    session: Session,
    tenant_id: str,
    *,
    order_ids: list[str],
    offsets: Any,
    invoice_gross: Decimal,
    currency: str,
) -> list[dict[str, str]]:
    """Check the stated offsets of a final invoice; returns them as stated."""
    if (
        not isinstance(offsets, list)
        or not offsets
        or any(
            not isinstance(row, dict)
            or set(row) != {"down_payment_document_id", "amount"}
            or not isinstance(row["down_payment_document_id"], str)
            for row in offsets
        )
    ):
        raise core.InvalidOperation(code="down_payment_offset_fields_invalid")
    if len({row["down_payment_document_id"] for row in offsets}) != len(offsets):
        raise core.InvalidOperation(code="down_payment_offset_fields_invalid")
    stated = [
        (
            row["down_payment_document_id"],
            _amount(row["amount"], "down_payment_offset_fields_invalid"),
        )
        for row in offsets
    ]
    by_id = {
        row["document_id"]: row
        for order_id in dict.fromkeys(order_ids)
        for row in down_payment_invoices(session, tenant_id, order_id)
    }
    for document_id, amount in stated:
        row = by_id.get(document_id)
        if row is None or row["currency"] != currency:
            raise core.InvalidOperation(code="down_payment_offset_other_order")
        if row["reversed"]:
            raise core.InvalidOperation(code="down_payment_offset_reversed")
        if amount > row["offsettable"]:
            raise core.InvalidOperation(code="down_payment_offset_exceeds_paid")
    if sum((amount for _, amount in stated), ZERO) > invoice_gross:
        raise core.InvalidOperation(code="down_payment_offset_exceeds_invoice")
    return [
        {"down_payment_document_id": document_id, "amount": str(amount)}
        for document_id, amount in stated
    ]


def post_offsets(
    session: Session,
    tenant_id: str,
    *,
    invoice: Document,
    offsets: list[dict[str, str]],
    effective_at: Any,
    source_record_id: str,
    action_id: str | None,
) -> tuple[list[LedgerEntry], list[DownPaymentOffset]]:
    """Post a final invoice's stated offsets and record one row for each."""
    total = sum((Decimal(row["amount"]) for row in offsets), ZERO)
    accounts = {
        role: resolve_account(session, tenant_id, role).id
        for role in ("customer_down_payments", "accounts_receivable")
    }
    entries = core.post_ledger(
        session,
        tenant_id,
        invoice.id,
        invoice.party_id,
        [
            ("customer_down_payments", "debit", total),
            ("accounts_receivable", "credit", total),
        ],
        account_ids=accounts,
        currency=invoice.currency,
        source_record_id=source_record_id,
        effective_at=effective_at,
        action_id=action_id,
        _commit=False,
    )
    rows = [
        DownPaymentOffset(
            id=uid("dpo"),
            tenant_id=tenant_id,
            final_invoice_document_id=invoice.id,
            down_payment_document_id=row["down_payment_document_id"],
            amount=Decimal(row["amount"]),
            source_record_id=source_record_id,
        )
        for row in offsets
    ]
    session.add_all(rows)
    session.flush()
    return list(entries), rows


def held_down_payments(
    session: Session, tenant_id: str, party_ids: set[str]
) -> list[dict[str, Any]]:
    """Down payments received from these customers and not yet offset.

    Money the company holds against an order not yet invoiced in full, so the
    credit exposure counts it like an available credit (spec 299).
    """
    if not party_ids:
        return []
    orders = {
        order_id: party_id
        for order_id, party_id in session.execute(
            select(Document.order_document_id, Document.party_id)
            .where(
                Document.tenant_id == tenant_id,
                Document.type == "down_payment_invoice",
                Document.party_id.in_(party_ids),
            )
            .distinct()
        )
    }
    rows = []
    for order_id, party_id in sorted(orders.items()):
        for row in down_payment_invoices(session, tenant_id, order_id):
            if not row["reversed"] and row["offsettable"] > ZERO:
                rows.append({**row, "party_id": party_id})
    return rows


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


# --- Pro-forma (FR-004) ---------------------------------------------------------------


def preview_proforma_invoice(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> dict[str, Any]:
    """
    What recording this pro-forma would record; it posts nothing.

    BUSINESS PURPOSE:
    What recording this pro-forma would record; it posts nothing.

    BUSINESS RULE services.down_payments.preview_proforma_invoice.refusal-4:
    IF required proforma fields are missing or unsupported fields were supplied:
        Refuse with proforma_fields_invalid.

    BUSINESS RULE services.down_payments.preview_proforma_invoice.refusal-9:
    IF the selected document is not a sales order with a customer:
        Refuse with proforma_order_required.

    BUSINESS RULE services.down_payments.preview_proforma_invoice.refusal-12:
    IF a currency was supplied and its normalized value differs from the sales order currency:
        Refuse with proforma_currency_mismatch.

    BUSINESS RULE services.down_payments.preview_proforma_invoice.refusal-15:
    IF the proforma number is empty after trimming whitespace:
        Refuse with proforma_number_missing.

    BUSINESS RULE services.down_payments.preview_proforma_invoice.refusal-18:
    IF the proforma amount cannot be parsed as a valid amount:
        Refuse with proforma_amount_invalid.

    BUSINESS RULE services.down_payments.preview_proforma_invoice.refusal-38:
    IF the proforma lines are missing, not a nonempty list, or contain invalid fields or an empty description:
        Refuse with proforma_line_fields_invalid.

    BUSINESS RULE services.down_payments.preview_proforma_invoice.refusal-41:
    IF the proforma lines are missing, not a nonempty list, or contain invalid fields or an empty description:
        Refuse with proforma_line_fields_invalid.

    BUSINESS RULE services.down_payments.preview_proforma_invoice.result:
    Return the current result with order_id, order_number, party_id, currency, number, gross_amount, document_date, lines.
    """
    # reality-rule: services.down_payments.preview_proforma_invoice.refusal-4
    if not PROFORMA_FIELDS <= set(arguments) or set(arguments) - (
        PROFORMA_FIELDS | PROFORMA_OPTIONAL
    ):
        raise core.InvalidOperation(code="proforma_fields_invalid")
    order = core._tenant_record(session, Document, tenant_id, arguments["order_id"])
    # reality-rule: services.down_payments.preview_proforma_invoice.refusal-9
    if order.type != "sales_order" or not order.party_id:
        raise core.InvalidOperation(code="proforma_order_required")
    currency = arguments.get("currency")
    # reality-rule: services.down_payments.preview_proforma_invoice.refusal-12
    if currency and str(currency).strip().upper() != order.currency:
        raise core.InvalidOperation(code="proforma_currency_mismatch")
    number = str(arguments["number"] or "").strip()
    # reality-rule: services.down_payments.preview_proforma_invoice.refusal-15
    if not number:
        raise core.InvalidOperation(code="proforma_number_missing")
    amount = _positive(arguments["gross_amount"])
    # reality-rule: services.down_payments.preview_proforma_invoice.refusal-18
    if amount is None:
        raise core.InvalidOperation(code="proforma_amount_invalid")
    document_date = arguments.get("document_date")
    if document_date:
        try:
            document_date = date.fromisoformat(str(document_date)).isoformat()
        except ValueError as error:
            raise core.InvalidOperation(code="proforma_date_invalid") from error
    else:
        document_date = core.now().date().isoformat()
    lines = arguments.get("lines")
    if lines is None:
        lines = [
            {
                "description": f"Pro-forma for {order.number}",
                "quantity": "1",
                "gross_amount": str(amount),
            }
        ]
    stated_lines = []
    # reality-rule: services.down_payments.preview_proforma_invoice.refusal-38
    if not isinstance(lines, list) or not lines:
        raise core.InvalidOperation(code="proforma_line_fields_invalid")
    for line in lines:
        # reality-rule: services.down_payments.preview_proforma_invoice.refusal-41
        if (
            not isinstance(line, dict)
            or not PROFORMA_LINE_FIELDS <= set(line)
            or set(line) - (PROFORMA_LINE_FIELDS | PROFORMA_LINE_OPTIONAL)
            or not str(line["description"] or "").strip()
        ):
            raise core.InvalidOperation(code="proforma_line_fields_invalid")
        stated = {
            "description": str(line["description"]).strip(),
            "quantity": str(_amount(line["quantity"], "proforma_line_fields_invalid")),
            "gross_amount": str(
                _amount(line["gross_amount"], "proforma_line_fields_invalid")
            ),
        }
        for key in sorted(PROFORMA_LINE_OPTIONAL & set(line)):
            try:
                stated[key] = str(Decimal(str(line[key])))
            except (DecimalInvalid, ValueError) as error:
                raise core.InvalidOperation(
                    code="proforma_line_fields_invalid"
                ) from error
        stated_lines.append(stated)
    # reality-rule: services.down_payments.preview_proforma_invoice.result
    return {
        "order_id": order.id,
        "order_number": order.number,
        "party_id": order.party_id,
        "currency": order.currency,
        "number": number,
        "gross_amount": str(amount),
        "document_date": document_date,
        "lines": stated_lines,
    }


def record_proforma_invoice(
    session: Session,
    tenant_id: str,
    *,
    order_id: str,
    number: str,
    gross_amount: Any,
    currency: str | None = None,
    document_date: str | None = None,
    lines: list[dict[str, Any]] | None = None,
    action_id: str | None = None,
    _commit: bool = True,
) -> dict[str, Any]:
    """
    Record a pro-forma for its order as evidence only: nothing is posted.

    BUSINESS PURPOSE:
    Record a pro-forma for its order as evidence only: nothing is posted.

    BUSINESS RULE services.down_payments.record_proforma_invoice.step-14:
    Require the business permission for 'record_proforma_invoice' before changing company records.

    BUSINESS RULE services.down_payments.record_proforma_invoice.step-23:
    Run the shared preview proforma invoice check and use its normalized inputs and current review evidence. Inspect that called function for its detailed eligibility rules.

    BUSINESS RULE services.down_payments.record_proforma_invoice.step-41:
    Pass the stated inputs to the shared store source record service. Its own source describes validation and record changes.

    BUSINESS RULE services.down_payments.record_proforma_invoice.step-49:
    Pass the stated inputs to the shared create document service. Its own source describes validation and record changes.

    BUSINESS RULE services.down_payments.record_proforma_invoice.result:
    Return the recorded proforma document and its evidence through the common invoice result reader. Its effect remains that of a proforma, not a financial posting.
    """
    # reality-rule: services.down_payments.record_proforma_invoice.step-14
    core._require_business_mutation(session, tenant_id, "record_proforma_invoice")
    arguments = {
        "order_id": order_id,
        "number": number,
        "gross_amount": gross_amount,
        **({"currency": currency} if currency is not None else {}),
        **({"document_date": document_date} if document_date is not None else {}),
        **({"lines": lines} if lines is not None else {}),
    }
    # reality-rule: services.down_payments.record_proforma_invoice.step-23
    preview = preview_proforma_invoice(session, tenant_id, arguments)
    external_id = action_id or uid("proforma")
    existing = session.scalar(
        select(Document)
        .join(
            SourceRecord,
            (SourceRecord.tenant_id == Document.tenant_id)
            & (SourceRecord.id == Document.source_record_id),
        )
        .where(
            Document.tenant_id == tenant_id,
            Document.type == "proforma_invoice",
            SourceRecord.source_system == PROFORMA_SOURCE_SYSTEM,
            SourceRecord.external_id == external_id,
        )
    )
    if existing:
        return _result(existing)
    # reality-rule: services.down_payments.record_proforma_invoice.step-41
    source, _, _ = core.store_source_record(
        session,
        tenant_id,
        PROFORMA_SOURCE_SYSTEM,
        "proforma_invoice",
        external_id,
        preview,
    )
    # reality-rule: services.down_payments.record_proforma_invoice.step-49
    document = core.create_document(
        session,
        tenant_id,
        "proforma_invoice",
        preview["number"],
        preview["party_id"],
        Decimal(preview["gross_amount"]),
        currency=preview["currency"],
        document_date=preview["document_date"],
        source_record_id=source.id,
        action_id=action_id,
        _commit=False,
    )
    document.order_document_id = preview["order_id"]
    for index, line in enumerate(preview["lines"], 1):
        quantity = Decimal(line["quantity"])
        session.add(
            DocumentLine(
                id=uid("lin"),
                tenant_id=tenant_id,
                document_id=document.id,
                source_line_id=str(index),
                sku="",
                description=line["description"],
                quantity=quantity,
                # A pro-forma states no unit price; none is derived from its amount.
                unit_price=None,
                gross_amount=Decimal(line["gross_amount"]),
                unit="pcs",
                line_type="proforma",
                payload=json.dumps(line, sort_keys=True),
            )
        )
    session.flush()
    if _commit:
        session.commit()
    # reality-rule: services.down_payments.record_proforma_invoice.result
    return _result(document)


# --- Inspector ------------------------------------------------------------------------


def order_billing_rows(
    session: Session, tenant_id: str, document: Document
) -> dict[str, list[dict[str, Any]]]:
    """Inspector sections: an order's down-payment and pro-forma invoices with
    what was paid and offset, a final invoice's offsets, and the order a
    down-payment or pro-forma invoice is for."""
    sections: dict[str, list[dict[str, Any]]] = {}
    if document.type == "sales_order":
        rows = []
        for record in session.scalars(
            select(Document)
            .where(
                Document.tenant_id == tenant_id,
                Document.order_document_id == document.id,
            )
            .order_by(Document.document_date, Document.number, Document.id)
        ):
            label = (
                "Pro-forma invoice"
                if record.type == "proforma_invoice"
                else "Down-payment invoice"
            )
            rows.append(
                {
                    "label": f"{label} {record.number}",
                    "value": f"{Decimal(record.gross_amount):.2f} {record.currency}",
                    "kind": "document",
                    "record_id": record.id,
                    "meta": "Posts nothing"
                    if record.type == "proforma_invoice"
                    else None,
                }
            )
        by_id = {
            row["document_id"]: row
            for row in down_payment_invoices(session, tenant_id, document.id)
        }
        for row in rows:
            figures = by_id.get(row["record_id"])
            if figures is not None:
                row["meta"] = (
                    "Reversed"
                    if figures["reversed"]
                    else f"Paid {figures['paid']:.2f} · offset {figures['offset']:.2f}"
                )
        if rows:
            sections["Down-payment and pro-forma invoices"] = rows
    if document.type in {"down_payment_invoice", "proforma_invoice"}:
        order_id = session.scalar(
            select(Document.order_document_id).where(
                Document.tenant_id == tenant_id, Document.id == document.id
            )
        )
        order = session.get(Document, (tenant_id, order_id)) if order_id else None
        if order is not None:
            sections["For order"] = [
                {
                    "label": order.number,
                    "value": f"{Decimal(order.gross_amount):.2f} {order.currency}",
                    "kind": "document",
                    "record_id": order.id,
                    "meta": None,
                }
            ]
    offsets = list(
        session.execute(
            select(DownPaymentOffset, Document)
            .join(
                Document,
                (Document.tenant_id == DownPaymentOffset.tenant_id)
                & (
                    Document.id
                    == (
                        DownPaymentOffset.down_payment_document_id
                        if document.type == "sales_invoice"
                        else DownPaymentOffset.final_invoice_document_id
                    )
                ),
            )
            .where(
                DownPaymentOffset.tenant_id == tenant_id,
                (
                    DownPaymentOffset.final_invoice_document_id
                    if document.type == "sales_invoice"
                    else DownPaymentOffset.down_payment_document_id
                )
                == document.id,
            )
            .order_by(Document.number, DownPaymentOffset.id)
        )
    )
    if offsets:
        sections["Down-payment offsets"] = [
            {
                "label": other.number,
                "value": f"{Decimal(offset.amount):.2f} {other.currency}",
                "kind": "document",
                "record_id": other.id,
                "meta": None,
            }
            for offset, other in offsets
        ]
    return sections
