"""Manual, evidenced customer reminders and their optional stated fee."""

from datetime import UTC, date, datetime, time
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from reality.db.core import (
    BusinessEvent,
    Document,
    DunningNotice,
    DunningNoticeInvoice,
    LedgerEntry,
    SourceRecord,
    uid,
)
from reality.services import core
from reality.services.core import emit_business_event
from reality.services.finance.accounts import lock_finance, resolve_account
from reality.services.finance.worklists import overdue_document_ids

SOURCE_SYSTEM = "internal_dunning"


def preview_notice(session: Session, tenant_id: str, values: dict) -> dict[str, Any]:
    invoice_ids = list(dict.fromkeys(values.get("invoice_ids") or []))
    if not invoice_ids:
        raise core.InvalidOperation("Select at least one overdue customer invoice.")
    try:
        level = int(values["level"])
        fee = core.decimal(values.get("fee_amount") or "0")
        notice_date = date.fromisoformat(values["notice_date"])
    except (KeyError, TypeError, ValueError) as error:
        raise core.InvalidOperation("Enter a valid notice date, level and fee.") from error
    if level not in {1, 2, 3}:
        raise core.InvalidOperation("Dunning level must be 1, 2 or 3.")
    if fee < 0 or fee.as_tuple().exponent < -4:
        raise core.InvalidOperation("Dunning fee must be non-negative with at most four decimals.")
    invoices = [
        core._tenant_record(session, Document, tenant_id, invoice_id)
        for invoice_id in invoice_ids
    ]
    if any(
        invoice.type not in {"sales_invoice", "opening_customer_debt"}
        for invoice in invoices
    ):
        raise core.InvalidOperation("Dunning requires customer invoices.")
    party_id, currency = invoices[0].party_id, invoices[0].currency
    if any(
        invoice.party_id != party_id or invoice.currency != currency
        for invoice in invoices
    ):
        raise core.InvalidOperation("One notice cannot mix customers or currencies.")
    as_of = datetime.combine(notice_date, time.max, tzinfo=UTC)
    overdue = overdue_document_ids(session, tenant_id, as_of=as_of)
    if any(invoice.id not in overdue for invoice in invoices):
        raise core.InvalidOperation("Every reminded invoice must be open and overdue.")
    accounts = None
    if fee:
        receivable = core._settlement_control_entry(session, tenant_id, invoices[0].id)
        revenue = resolve_account(session, tenant_id, "dunning_fee_revenue")
        accounts = {
            "accounts_receivable": receivable.account_id,
            "dunning_fee_revenue": revenue.id,
        }
    return {
        "invoice_ids": invoice_ids,
        "party_id": party_id,
        "currency": currency,
        "notice_date": notice_date.isoformat(),
        "level": level,
        "fee_amount": str(fee),
        "reason": str(values.get("reason") or "").strip(),
        "number": str(values.get("number") or "").strip(),
        "accounts": accounts,
        "invoice_open": {
            invoice.id: str(core.open_invoice_amount(session, tenant_id, invoice.id))
            for invoice in invoices
        },
    }


def dunning_context(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> dict[str, Any]:
    """Return the current finance revision and a validated reminder preview."""
    from reality.services.finance.accounts import list_accounts

    return {
        "revision": list_accounts(session, tenant_id)["revision"],
        "preview": preview_notice(session, tenant_id, arguments),
    }


def record_notice(
    session: Session,
    tenant_id: str,
    *,
    action_id: str,
    actor_id: str | None,
    invoice_ids: list[str],
    level: int,
    notice_date: str,
    fee_amount: str = "0",
    reason: str = "",
    number: str = "",
    expected_revision: int,
) -> dict[str, Any]:
    """Record one confirmed notice atomically; callers own the outer transaction."""
    core._require_business_mutation(session, tenant_id, "record_dunning_notice")
    state = lock_finance(session, tenant_id)
    if state.revision != expected_revision:
        raise core.Conflict("Finance preview is stale; reload and confirm again.")
    values = preview_notice(
        session,
        tenant_id,
        {
            "invoice_ids": invoice_ids,
            "level": level,
            "notice_date": notice_date,
            "fee_amount": fee_amount,
            "reason": reason,
            "number": number,
        },
    )
    existing = session.scalar(
        select(DunningNotice).where(
            DunningNotice.tenant_id == tenant_id,
            DunningNotice.source_record_id
            == select(SourceRecord.id)
            .where(
                SourceRecord.tenant_id == tenant_id,
                SourceRecord.source_system == SOURCE_SYSTEM,
                SourceRecord.external_id == action_id,
            )
            .scalar_subquery(),
        )
    )
    if existing:
        return notice_detail(session, tenant_id, existing.id)
    with session.begin_nested():
        source, _, _ = core.store_source_record(
            session,
            tenant_id,
            SOURCE_SYSTEM,
            "dunning_notice",
            action_id,
            {**values, "actor_id": actor_id, "confirmation_id": action_id},
        )
        reference = values["number"] or f"DN-{action_id[-8:].upper()}"
        document = core.create_document(
            session,
            tenant_id,
            "dunning_notice",
            reference,
            values["party_id"],
            "0",
            currency=values["currency"],
            document_date=values["notice_date"],
            source_record_id=source.id,
            action_id=action_id,
            _commit=False,
        )
        notice = DunningNotice(
            id=uid("dun"),
            tenant_id=tenant_id,
            document_id=document.id,
            source_record_id=source.id,
            party_id=values["party_id"],
            currency=values["currency"],
            notice_date=date.fromisoformat(values["notice_date"]),
            level=values["level"],
            fee_amount=Decimal(values["fee_amount"]),
        )
        session.add(notice)
        memberships = [
            DunningNoticeInvoice(
                id=uid("dni"),
                tenant_id=tenant_id,
                notice_id=notice.id,
                invoice_id=invoice_id,
            )
            for invoice_id in values["invoice_ids"]
        ]
        session.add_all(memberships)
        fee_result = None
        if notice.fee_amount:
            fee_document = core.create_document(
                session,
                tenant_id,
                "dunning_fee_charge",
                f"{reference}-FEE",
                notice.party_id,
                notice.fee_amount,
                currency=notice.currency,
                document_date=values["notice_date"],
                source_record_id=source.id,
                action_id=action_id,
                _commit=False,
            )
            entries = core.post_ledger(
                session,
                tenant_id,
                fee_document.id,
                notice.party_id,
                [
                    ("accounts_receivable", "debit", notice.fee_amount),
                    ("dunning_fee_revenue", "credit", notice.fee_amount),
                ],
                account_ids=values["accounts"],
                currency=notice.currency,
                source_record_id=source.id,
                action_id=action_id,
                _commit=False,
            )
            fee_result = {
                "document_id": fee_document.id,
                "posting_group_id": entries[0].posting_group_id,
                "ledger_entry_ids": [entry.id for entry in entries],
            }
        emit_business_event(
            session,
            tenant_id,
            "dunning.notice_recorded",
            "dunning_notice",
            notice.id,
            {
                "level": notice.level,
                "invoice_ids": values["invoice_ids"],
                "fee_amount": notice.fee_amount,
                "reason": values["reason"],
            },
            source_record_id=source.id,
            action_id=action_id,
        )
        session.flush()
        return {
            **notice_detail(session, tenant_id, notice.id),
            "fee": fee_result,
        }


def notice_detail(session: Session, tenant_id: str, notice_id: str) -> dict[str, Any]:
    notice = core._tenant_record(session, DunningNotice, tenant_id, notice_id)
    document = core._tenant_record(session, Document, tenant_id, notice.document_id)
    invoice_ids = list(
        session.scalars(
            select(DunningNoticeInvoice.invoice_id)
            .where(
                DunningNoticeInvoice.tenant_id == tenant_id,
                DunningNoticeInvoice.notice_id == notice.id,
            )
            .order_by(DunningNoticeInvoice.invoice_id)
        )
    )
    fee_document = session.scalar(
        select(Document).where(
            Document.tenant_id == tenant_id,
            Document.source_record_id == notice.source_record_id,
            Document.type == "dunning_fee_charge",
        )
    )
    fee_entries = (
        list(
            session.scalars(
                select(LedgerEntry).where(
                    LedgerEntry.tenant_id == tenant_id,
                    LedgerEntry.document_id == fee_document.id,
                )
            )
        )
        if fee_document
        else []
    )
    reversal = session.scalar(
        select(BusinessEvent)
        .where(
            BusinessEvent.tenant_id == tenant_id,
            BusinessEvent.event_type == "dunning.notice_reversed",
            BusinessEvent.subject_type == "dunning_notice",
            BusinessEvent.subject_id == notice.id,
        )
        .order_by(BusinessEvent.sequence.desc())
    )
    return {
        "id": notice.id,
        "document_id": notice.document_id,
        "number": document.number,
        "source_record_id": notice.source_record_id,
        "party_id": notice.party_id,
        "currency": notice.currency,
        "notice_date": notice.notice_date.isoformat(),
        "level": notice.level,
        "fee_amount": str(notice.fee_amount),
        "invoice_ids": invoice_ids,
        "fee_document_id": fee_document.id if fee_document else None,
        "fee_posting_group_id": fee_entries[0].posting_group_id if fee_entries else None,
        "reversed": reversal is not None,
        "reversal_event_id": reversal.id if reversal else None,
    }


def notices(session: Session, tenant_id: str) -> list[dict[str, Any]]:
    """List notices newest first with their invoice and fee trace."""
    core.get_tenant(session, tenant_id)
    return [
        notice_detail(session, tenant_id, notice_id)
        for notice_id in session.scalars(
            select(DunningNotice.id)
            .where(DunningNotice.tenant_id == tenant_id)
            .order_by(
                DunningNotice.notice_date.desc(),
                DunningNotice.created_at.desc(),
                DunningNotice.id,
            )
        )
    ]


def reverse_notice(
    session: Session,
    tenant_id: str,
    *,
    action_id: str,
    actor_id: str | None,
    notice_id: str,
    reason: str,
    expected_revision: int,
) -> dict[str, Any]:
    """Reverse a notice's financial fee and retain the original reminder evidence."""
    core._require_business_mutation(session, tenant_id, "reverse_dunning_notice")
    if lock_finance(session, tenant_id).revision != expected_revision:
        raise core.Conflict("Finance preview is stale; reload and confirm again.")
    detail = notice_detail(session, tenant_id, notice_id)
    if detail["reversed"]:
        raise core.InvalidOperation("Dunning notice is already reversed.")
    reversal_id = None
    if detail["fee_posting_group_id"]:
        reversal = core.reverse_ledger_posting_group(
            session,
            tenant_id,
            detail["fee_posting_group_id"],
            reason=reason,
            actor_context={"actor_id": actor_id, "dunning_notice_id": notice_id},
            action_id=action_id,
            _commit=False,
        )
        reversal_id = reversal.reversal_id
    emit_business_event(
        session,
        tenant_id,
        "dunning.notice_reversed",
        "dunning_notice",
        notice_id,
        {"reason": reason.strip(), "fee_reversal_id": reversal_id},
        source_record_id=detail["source_record_id"],
        action_id=action_id,
    )
    return {**detail, "reversal_id": reversal_id, "reversed": True}
