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

from sqlalchemy import cast, func, select
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Session, aliased

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
#: The documents a fee creates, each carrying the return's source record.
FEE_TYPES = ("payment_return_fee", "payment_return_fee_charge")
#: What a customer owes as an invoice; only these are reported as open again.
OWED_TYPES = {"sales_invoice", "opening_customer_debt"}


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


def _reduction_active(session: Session, tenant_id: str, payment: Document) -> bool:
    """Whether a reduction booked with this payment is still in force.

    The payment and its adjustment are recorded under one confirmation; their
    source records both name it. Returning the payment while a fee, discount or
    deduction stays in force would reopen the invoice short.
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
    reversed_groups = select(LedgerReversal.original_posting_group_id).where(
        LedgerReversal.tenant_id == tenant_id
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
                LedgerEntry.posting_group_id.not_in(reversed_groups),
            )
            .limit(1)
        )
        is not None
    )


def _payment_cash_account(
    session: Session, tenant_id: str, entry: LedgerEntry
) -> str | None:
    """The cash account the payment was booked on; the fee leaves the same account."""
    return session.scalar(
        select(LedgerEntry.account_id).where(
            LedgerEntry.tenant_id == tenant_id,
            LedgerEntry.posting_group_id == entry.posting_group_id,
            LedgerEntry.account == "cash",
        )
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
    if _reduction_active(session, tenant_id, payment):
        raise core.InvalidOperation(code="payment_return_reduction_active")
    kind = values.get("kind")
    if kind not in KINDS:
        raise core.InvalidOperation(code="payment_return_kind_invalid")
    reason = str(values.get("reason") or "").strip()
    if not reason:
        raise core.InvalidOperation(code="payment_return_reason_missing")
    try:
        returned_on = date.fromisoformat(str(values.get("returned_on")))
    except ValueError as error:
        raise core.InvalidOperation(code="payment_return_date_invalid") from error
    try:
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
        accounts["cash"] = (
            _payment_cash_account(session, tenant_id, entry)
            or resolve_account(session, tenant_id, "cash").id
        )
        accounts["accounts_receivable"] = entry.account_id
    reopened = [
        {
            "invoice_id": invoice.id,
            "number": invoice.number,
            "type": invoice.type,
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
    _source_record: SourceRecord | None = None,
) -> dict[str, Any]:
    """Reverse a returned payment and keep what was stated; callers own the transaction.

    It re-checks everything under the finance lock instead of comparing a revision:
    every posting raises the revision, and an unrelated payment must not refuse this.
    A payout's chargeback line (spec 336) passes its own source record: the line is
    what the provider stated, and the return carries it.
    """
    core._require_business_mutation(session, tenant_id, "record_payment_return")
    lock_finance(session, tenant_id)
    replay = session.scalar(
        select(PaymentReturn.id).where(
            PaymentReturn.tenant_id == tenant_id,
            PaymentReturn.source_record_id
            == (
                _source_record.id
                if _source_record is not None
                else select(SourceRecord.id)
                .where(
                    SourceRecord.tenant_id == tenant_id,
                    SourceRecord.source_system == SOURCE_SYSTEM,
                    SourceRecord.external_id == action_id,
                )
                .scalar_subquery()
            ),
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
    source = _source_record or (
        core.store_source_record(
            session,
            tenant_id,
            SOURCE_SYSTEM,
            "payment_return",
            action_id,
            {**preview, "actor_id": actor_id, "confirmation_id": action_id},
        )[0]
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
            "ledger_reversal_id": reversal.reversal_id,
        },
        source_record_id=source.id,
        action_id=action_id,
    )
    return return_detail(session, tenant_id, row.id)


def _caused(
    session: Session, tenant_id: str, row: PaymentReturn, entry: LedgerEntry
) -> dict[str, str | None]:
    """What the return caused, read from the records that point back to it (spec 322).

    The reversal is the one of the payment's posting group, which can be
    reversed once; the fee documents carry the return's own source record.
    """
    fees = dict(
        session.execute(
            select(Document.type, Document.id).where(
                Document.tenant_id == tenant_id,
                Document.source_record_id == row.source_record_id,
                Document.type.in_(FEE_TYPES),
            )
        ).all()
    )
    return {
        "ledger_reversal_id": session.scalar(
            select(LedgerReversal.id).where(
                LedgerReversal.tenant_id == tenant_id,
                LedgerReversal.original_posting_group_id == entry.posting_group_id,
            )
        ),
        "fee_document_id": fees.get("payment_return_fee"),
        "fee_charge_document_id": fees.get("payment_return_fee_charge"),
    }


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
                "type": invoice.type,
                "allocated": str(amount),
                "open": str(core.open_invoice_amount(session, tenant_id, invoice.id)),
            }
            for invoice, amount in _paid_invoices(session, tenant_id, entry)
        ],
        **_caused(session, tenant_id, row, entry),
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


def _returned_allocations(
    session: Session, tenant_id: str, invoice_id: str | None = None
) -> list[tuple[PaymentReturn, Document, Decimal]]:
    """Each return with every owed document its payment had paid, in one query."""
    payment_entry = aliased(LedgerEntry)
    invoice_entry = aliased(LedgerEntry)
    query = (
        select(PaymentReturn, Document, func.sum(SettlementAllocation.amount))
        .select_from(PaymentReturn)
        .join(
            payment_entry,
            (payment_entry.tenant_id == tenant_id)
            & (payment_entry.document_id == PaymentReturn.payment_document_id)
            & (payment_entry.account == "accounts_receivable")
            & (payment_entry.debit_credit == "credit"),
        )
        .join(
            SettlementAllocation,
            (SettlementAllocation.tenant_id == tenant_id)
            & (SettlementAllocation.payment_ledger_entry_id == payment_entry.id),
        )
        .join(
            invoice_entry,
            (invoice_entry.tenant_id == tenant_id)
            & (invoice_entry.id == SettlementAllocation.invoice_ledger_entry_id),
        )
        .join(
            Document,
            (Document.tenant_id == tenant_id)
            & (Document.id == invoice_entry.document_id),
        )
        .where(PaymentReturn.tenant_id == tenant_id, Document.type.in_(OWED_TYPES))
        .group_by(
            PaymentReturn.tenant_id, PaymentReturn.id, Document.tenant_id, Document.id
        )
        .order_by(
            PaymentReturn.returned_on.desc(),
            PaymentReturn.created_at.desc(),
            PaymentReturn.id,
        )
    )
    if invoice_id is not None:
        query = query.where(Document.id == invoice_id)
    return [tuple(row) for row in session.execute(query)]


def returned_invoices(session: Session, tenant_id: str) -> list[dict[str, Any]]:
    """Owed documents a returned payment had paid that are still open (the finding's reader).

    One row per document, from its newest return: a second return of the same
    invoice replaces the first rather than reporting it twice.
    """
    latest: dict[str, tuple[PaymentReturn, Document, Decimal]] = {}
    for row in _returned_allocations(session, tenant_id):
        latest.setdefault(row[1].id, row)
    open_amounts = core.open_invoice_amounts(
        session, tenant_id, [invoice for _, invoice, _ in latest.values()]
    )
    return [
        {
            "return": returned,
            "invoice": invoice,
            "allocated": allocated,
            "open": open_amounts[invoice.id],
        }
        for returned, invoice, allocated in latest.values()
        if open_amounts.get(invoice.id, Decimal(0)) > 0
    ]


def invoice_return_rows(
    session: Session, tenant_id: str, invoice: Document
) -> list[dict[str, Any]]:
    """What an invoice's explanation says about payments to it that came back."""
    if invoice.type != "sales_invoice":
        return []
    return [
        {
            "label": KINDS[row.kind],
            "value": f"{row.returned_on.isoformat()} · {row.reason}",
            "kind": "source_record",
            "record_id": row.source_record_id,
            "meta": row.reference
            or session.get(Document, (tenant_id, row.payment_document_id)).number,
        }
        for row, _, _ in _returned_allocations(session, tenant_id, invoice.id)
    ]
