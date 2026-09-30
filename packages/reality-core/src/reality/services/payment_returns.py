"""Returned direct debits and chargebacks of customer payments (spec 297).

A return reverses the payment's posting through the ordinary ledger reversal, so
the invoices it paid are open again, and keeps what the bank or provider stated:
the kind, reason, reference, date and fee. The fee is always the company's cost
first; charged on, the customer owes it as its own receivable, which recovers
that cost.
"""

import json
from datetime import date
from decimal import Decimal
from decimal import InvalidOperation as DecimalInvalid
from typing import Any

from sqlalchemy import cast, select
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Session

from reality.db.core import (
    Document,
    LedgerEntry,
    LedgerReversal,
    PaymentReturn,
    SettlementAllocation,
    SourceRecord,
    uid,
)
from reality.services import core
from reality.services.core import emit_business_event
from reality.services.finance.accounts import lock_finance, resolve_account

SOURCE_SYSTEM = "internal_payment_return"
KINDS = {"direct_debit_return": "Returned direct debit", "chargeback": "Chargeback"}
BEARERS = {"customer", "company"}
FEE_SCALE = Decimal("0.0001")


def _payment_entry(session: Session, tenant_id: str, payment: Document) -> LedgerEntry:
    """The payment's receivable entry: its allocations say which invoices it paid."""
    entry = session.scalar(
        select(LedgerEntry).where(
            LedgerEntry.tenant_id == tenant_id,
            LedgerEntry.document_id == payment.id,
            LedgerEntry.account == "accounts_receivable",
            LedgerEntry.debit_credit == "credit",
        )
    )
    if entry is None:
        raise core.InvalidOperation(code="payment_return_not_customer_payment")
    return entry


def _paid_invoices(
    session: Session, tenant_id: str, entry: LedgerEntry
) -> list[tuple[Document, Decimal]]:
    """Every invoice this payment was allocated to, with the allocated amount."""
    rows = session.execute(
        select(Document, SettlementAllocation.amount)
        .join(
            LedgerEntry,
            (LedgerEntry.tenant_id == tenant_id)
            & (LedgerEntry.id == SettlementAllocation.invoice_ledger_entry_id),
        )
        .join(
            Document,
            (Document.tenant_id == tenant_id)
            & (Document.id == LedgerEntry.document_id),
        )
        .where(
            SettlementAllocation.tenant_id == tenant_id,
            SettlementAllocation.payment_ledger_entry_id == entry.id,
        )
        .order_by(Document.number, Document.id)
    ).all()
    totals: dict[str, list] = {}
    for document, amount in rows:
        totals.setdefault(document.id, [document, Decimal(0)])[1] += amount
    return [(document, amount) for document, amount in totals.values()]


def _fee_adjusted(session: Session, tenant_id: str, payment: Document) -> bool:
    """Whether the same confirmed settlement also booked a payment fee on the invoice.

    The payment and its fee adjustment are recorded under one confirmation; their
    source records both name it.
    """
    if not payment.source_record_id:
        return False
    source = session.get(SourceRecord, (tenant_id, payment.source_record_id))
    confirmation = (
        json.loads(source.payload or "{}").get("confirmation_id") if source else None
    )
    if not confirmation:
        return False
    adjustments = select(SourceRecord.id).where(
        SourceRecord.tenant_id == tenant_id,
        SourceRecord.source_system == "internal_settlement_adjustment",
        cast(SourceRecord.payload, JSONB)["confirmation_id"].astext == confirmation,
    )
    return (
        session.scalar(
            select(LedgerEntry.id)
            .join(
                Document,
                (Document.tenant_id == tenant_id)
                & (Document.id == LedgerEntry.document_id),
            )
            .where(
                LedgerEntry.tenant_id == tenant_id,
                Document.type == "customer_settlement_adjustment",
                Document.source_record_id.in_(adjustments),
                LedgerEntry.account == "payment_fee_expense",
            )
        )
        is not None
    )


def preview_return(
    session: Session, tenant_id: str, values: dict[str, Any]
) -> dict[str, Any]:
    """What returning this payment would do, recording nothing."""
    payment = core._tenant_record(
        session, Document, tenant_id, str(values.get("payment_document_id") or "")
    )
    if payment.type != "customer_payment":
        raise core.InvalidOperation(code="payment_return_not_customer_payment")
    existing = session.scalar(
        select(PaymentReturn.id).where(
            PaymentReturn.tenant_id == tenant_id,
            PaymentReturn.payment_document_id == payment.id,
        )
    )
    if existing:
        raise core.InvalidOperation(code="payment_return_already_returned")
    entry = _payment_entry(session, tenant_id, payment)
    reversed_group = session.scalar(
        select(LedgerReversal.id).where(
            LedgerReversal.tenant_id == tenant_id,
            LedgerReversal.original_posting_group_id == entry.posting_group_id,
        )
    )
    if reversed_group:
        raise core.InvalidOperation(code="payment_return_already_reversed")
    if _fee_adjusted(session, tenant_id, payment):
        raise core.InvalidOperation(code="payment_return_fee_adjusted")
    kind = values.get("kind")
    if kind not in KINDS:
        raise core.InvalidOperation(code="payment_return_kind_invalid")
    reason = str(values.get("reason") or "").strip()
    if not reason:
        raise core.InvalidOperation(code="payment_return_reason_missing")
    try:
        returned_on = date.fromisoformat(str(values.get("returned_on")))
        fee = Decimal(str(values.get("fee_amount") or "0"))
    except (TypeError, ValueError, DecimalInvalid) as error:
        raise core.InvalidOperation(code="payment_return_fee_invalid") from error
    if not fee.is_finite() or fee < 0 or fee.as_tuple().exponent < -4:
        raise core.InvalidOperation(code="payment_return_fee_invalid")
    bearer = str(values.get("fee_bearer") or ("none" if not fee else "customer"))
    if (fee == 0) != (bearer == "none") or (fee and bearer not in BEARERS):
        raise core.InvalidOperation(code="payment_return_fee_bearer_invalid")
    accounts = {}
    if fee:
        accounts["payment_fee_expense"] = resolve_account(
            session, tenant_id, "payment_fee_expense"
        ).id
        accounts["cash"] = resolve_account(session, tenant_id, "cash").id
        accounts["accounts_receivable"] = entry.account_id
    reopened = [
        {
            "invoice_id": invoice.id,
            "number": invoice.number,
            "allocated": str(amount),
            "open_after": str(
                core.open_invoice_amount(session, tenant_id, invoice.id) + amount
            ),
        }
        for invoice, amount in _paid_invoices(session, tenant_id, entry)
    ]
    return {
        "payment_document_id": payment.id,
        "payment_number": payment.number,
        "party_id": payment.party_id,
        "currency": payment.currency,
        "amount": str(entry.amount),
        "posting_group_id": entry.posting_group_id,
        "kind": kind,
        "reason": reason,
        "reference": str(values.get("reference") or "").strip(),
        "returned_on": returned_on.isoformat(),
        "fee_amount": str(fee),
        "fee_bearer": bearer,
        "accounts": accounts,
        "reopened": reopened,
    }


def record_return(
    session: Session,
    tenant_id: str,
    *,
    payment_document_id: str,
    kind: str,
    returned_on: str,
    reason: str,
    reference: str = "",
    fee_amount: str = "0",
    fee_bearer: str | None = None,
    action_id: str,
    actor_id: str | None,
) -> dict[str, Any]:
    """Reverse a returned payment and keep what was stated; callers own the transaction.

    It re-checks everything under the finance lock instead of comparing a revision:
    every posting raises the revision, and an unrelated payment must not refuse this.
    """
    core._require_business_mutation(session, tenant_id, "record_payment_return")
    lock_finance(session, tenant_id)
    replay = session.scalar(
        select(PaymentReturn.id).where(
            PaymentReturn.tenant_id == tenant_id,
            PaymentReturn.source_record_id
            == select(SourceRecord.id)
            .where(
                SourceRecord.tenant_id == tenant_id,
                SourceRecord.source_system == SOURCE_SYSTEM,
                SourceRecord.external_id == action_id,
            )
            .scalar_subquery(),
        )
    )
    if replay:
        return return_detail(session, tenant_id, replay)
    preview = preview_return(
        session,
        tenant_id,
        {
            "payment_document_id": payment_document_id,
            "kind": kind,
            "returned_on": returned_on,
            "reason": reason,
            "reference": reference,
            "fee_amount": fee_amount,
            "fee_bearer": fee_bearer,
        },
    )
    source, _, _ = core.store_source_record(
        session,
        tenant_id,
        SOURCE_SYSTEM,
        "payment_return",
        action_id,
        {**preview, "actor_id": actor_id, "confirmation_id": action_id},
    )
    record_id = uid("prt")
    reversal = core.reverse_ledger_posting_group(
        session,
        tenant_id,
        preview["posting_group_id"],
        reason=f"{KINDS[preview['kind']]}: {preview['reason']}",
        actor_context={"payment_return_id": record_id, "actor_id": actor_id},
        action_id=action_id,
        _commit=False,
    )
    fee = Decimal(preview["fee_amount"])
    fee_document = fee_charge = None
    if fee:
        stated_on = preview["returned_on"]
        fee_document = core.create_document(
            session,
            tenant_id,
            "payment_return_fee",
            f"{preview['payment_number']}-FEE",
            preview["party_id"],
            fee,
            currency=preview["currency"],
            document_date=stated_on,
            source_record_id=source.id,
            action_id=action_id,
            _commit=False,
        )
        core.post_ledger(
            session,
            tenant_id,
            fee_document.id,
            preview["party_id"],
            [("payment_fee_expense", "debit", fee), ("cash", "credit", fee)],
            account_ids=preview["accounts"],
            currency=preview["currency"],
            source_record_id=source.id,
            action_id=action_id,
            _commit=False,
        )
        if preview["fee_bearer"] == "customer":
            fee_charge = core.create_document(
                session,
                tenant_id,
                "payment_return_fee_charge",
                f"{preview['payment_number']}-FEE-CHARGE",
                preview["party_id"],
                fee,
                currency=preview["currency"],
                document_date=stated_on,
                source_record_id=source.id,
                action_id=action_id,
                _commit=False,
            )
            core.post_ledger(
                session,
                tenant_id,
                fee_charge.id,
                preview["party_id"],
                [
                    ("accounts_receivable", "debit", fee),
                    ("payment_fee_expense", "credit", fee),
                ],
                account_ids=preview["accounts"],
                currency=preview["currency"],
                source_record_id=source.id,
                action_id=action_id,
                _commit=False,
            )
    row = PaymentReturn(
        id=record_id,
        tenant_id=tenant_id,
        payment_document_id=preview["payment_document_id"],
        kind=preview["kind"],
        reason=preview["reason"],
        reference=preview["reference"],
        returned_on=date.fromisoformat(preview["returned_on"]),
        fee_amount=fee,
        fee_bearer=preview["fee_bearer"],
        ledger_reversal_id=reversal.reversal_id,
        fee_document_id=fee_document.id if fee_document else None,
        fee_charge_document_id=fee_charge.id if fee_charge else None,
        source_record_id=source.id,
    )
    session.add(row)
    session.flush()
    emit_business_event(
        session,
        tenant_id,
        "payment.returned",
        "payment_return",
        row.id,
        {
            "kind": row.kind,
            "reason": row.reason,
            "reference": row.reference,
            "returned_on": preview["returned_on"],
            "fee_amount": preview["fee_amount"],
            "fee_bearer": row.fee_bearer,
            "reopened_invoice_ids": [
                item["invoice_id"] for item in preview["reopened"]
            ],
            "ledger_reversal_id": row.ledger_reversal_id,
        },
        source_record_id=source.id,
        action_id=action_id,
    )
    return return_detail(session, tenant_id, row.id)


def return_detail(session: Session, tenant_id: str, return_id: str) -> dict[str, Any]:
    row = core._tenant_record(session, PaymentReturn, tenant_id, return_id)
    payment = core._tenant_record(session, Document, tenant_id, row.payment_document_id)
    entry = _payment_entry(session, tenant_id, payment)
    return {
        "id": row.id,
        "payment_document_id": payment.id,
        "payment_number": payment.number,
        "party_id": payment.party_id,
        "kind": row.kind,
        "reason": row.reason,
        "reference": row.reference,
        "returned_on": row.returned_on.isoformat(),
        "fee_amount": str(Decimal(row.fee_amount).quantize(FEE_SCALE)),
        "fee_bearer": row.fee_bearer,
        "reopened": [
            {
                "invoice_id": invoice.id,
                "number": invoice.number,
                "allocated": str(amount),
                "open": str(core.open_invoice_amount(session, tenant_id, invoice.id)),
            }
            for invoice, amount in _paid_invoices(session, tenant_id, entry)
        ],
        "ledger_reversal_id": row.ledger_reversal_id,
        "fee_document_id": row.fee_document_id,
        "fee_charge_document_id": row.fee_charge_document_id,
        "source_record_id": row.source_record_id,
    }


def returns(session: Session, tenant_id: str) -> list[dict[str, Any]]:
    """Returned payments, newest first."""
    core.get_tenant(session, tenant_id)
    return [
        return_detail(session, tenant_id, return_id)
        for return_id in session.scalars(
            select(PaymentReturn.id)
            .where(PaymentReturn.tenant_id == tenant_id)
            .order_by(
                PaymentReturn.returned_on.desc(),
                PaymentReturn.created_at.desc(),
                PaymentReturn.id,
            )
        )
    ]


def returned_invoices(session: Session, tenant_id: str) -> list[dict[str, Any]]:
    """Invoices a returned payment had paid that are still open (the finding's reader)."""
    rows = []
    for row in session.scalars(
        select(PaymentReturn).where(PaymentReturn.tenant_id == tenant_id)
    ):
        payment = core._tenant_record(
            session, Document, tenant_id, row.payment_document_id
        )
        entry = _payment_entry(session, tenant_id, payment)
        for invoice, allocated in _paid_invoices(session, tenant_id, entry):
            open_amount = core.open_invoice_amount(session, tenant_id, invoice.id)
            if open_amount > 0:
                rows.append(
                    {
                        "return": row,
                        "payment": payment,
                        "invoice": invoice,
                        "allocated": allocated,
                        "open": open_amount,
                    }
                )
    return rows


def invoice_return_rows(
    session: Session, tenant_id: str, invoice: Document
) -> list[dict[str, Any]]:
    """What an invoice's explanation says about payments to it that came back."""
    if invoice.type != "sales_invoice":
        return []
    rows = []
    for row in session.scalars(
        select(PaymentReturn).where(PaymentReturn.tenant_id == tenant_id)
    ):
        payment = session.get(Document, (tenant_id, row.payment_document_id))
        entry = _payment_entry(session, tenant_id, payment)
        if any(
            paid.id == invoice.id
            for paid, _ in _paid_invoices(session, tenant_id, entry)
        ):
            rows.append(
                {
                    "label": KINDS[row.kind],
                    "value": f"{row.returned_on.isoformat()} · {row.reason}",
                    "kind": "source_record",
                    "record_id": row.source_record_id,
                    "meta": row.reference or payment.number,
                }
            )
    return rows
