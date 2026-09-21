"""Explicit customer and supplier deposits over the shared settlement ledger."""

from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from reality.db.core import Document, LedgerEntry, Party, PartyRole, SourceRecord
from reality.services import core
from reality.services.finance.accounts import lock_finance, resolve_account

SOURCE_SYSTEM = "internal_deposit"


def record_deposit(
    session: Session,
    tenant_id: str,
    *,
    action_id: str,
    actor_id: str | None,
    side: str,
    party_id: str,
    amount: str,
    currency: str,
    reference: str,
    effective_at: datetime | str,
    expected_revision: int,
) -> dict[str, Any]:
    core._require_business_mutation(session, tenant_id, "record_deposit")
    if side not in {"customer", "supplier"}:
        raise core.InvalidOperation("Deposit side must be customer or supplier.")
    value = core.positive(amount, "amount")
    moment = core.utc_datetime(effective_at)
    if moment is None or not reference.strip():
        raise core.InvalidOperation("Deposit reference and effective time are required.")
    party = core._tenant_record(session, Party, tenant_id, party_id)
    roles = set(
        session.scalars(
            select(PartyRole.role).where(
                PartyRole.tenant_id == tenant_id, PartyRole.party_id == party.id
            )
        )
    )
    if side not in roles:
        raise core.InvalidOperation(f"Party is not a {side}.")
    state = lock_finance(session, tenant_id)
    if state.revision != expected_revision:
        raise core.Conflict("Finance preview is stale; reload and confirm again.")
    source = session.scalar(
        select(SourceRecord).where(
            SourceRecord.tenant_id == tenant_id,
            SourceRecord.source_system == SOURCE_SYSTEM,
            SourceRecord.external_id == action_id,
        )
    )
    if source:
        document = session.scalar(
            select(Document).where(
                Document.tenant_id == tenant_id,
                Document.source_record_id == source.id,
                Document.type == f"{side}_deposit",
            )
        )
        control = core._settlement_control_entry(session, tenant_id, document.id)
        return _deposit_result(document, control, source.id)
    with session.begin_nested():
        source, _, _ = core.store_source_record(
            session,
            tenant_id,
            SOURCE_SYSTEM,
            f"{side}_deposit",
            action_id,
            {
                "side": side,
                "party_id": party.id,
                "amount": str(value),
                "currency": currency,
                "reference": reference.strip(),
                "effective_at": moment.isoformat(),
                "actor_id": actor_id,
            },
        )
        document = core.create_document(
            session,
            tenant_id,
            f"{side}_deposit",
            reference.strip(),
            party.id,
            value,
            currency=currency,
            document_date=moment.date().isoformat(),
            source_record_id=source.id,
            action_id=action_id,
            _commit=False,
        )
        control_role = "accounts_receivable" if side == "customer" else "accounts_payable"
        control = resolve_account(session, tenant_id, control_role)
        rows = (
            [("cash", "debit", value), (control_role, "credit", value)]
            if side == "customer"
            else [(control_role, "debit", value), ("cash", "credit", value)]
        )
        entries = core.post_ledger(
            session,
            tenant_id,
            document.id,
            party.id,
            rows,
            account_ids={control_role: control.id},
            currency=currency,
            source_record_id=source.id,
            effective_at=moment,
            action_id=action_id,
            _commit=False,
        )
        control_entry = next(row for row in entries if row.account == control_role)
        return _deposit_result(document, control_entry, source.id)


def preview_clearing(
    session: Session,
    tenant_id: str,
    *,
    deposit_document_id: str,
    invoice_id: str,
    amount: str,
    expected_revision: int,
) -> dict[str, Any]:
    if lock_finance(session, tenant_id).revision != expected_revision:
        raise core.Conflict("Finance preview is stale; reload and confirm again.")
    deposit = core._tenant_record(session, Document, tenant_id, deposit_document_id)
    side = {"customer_deposit": "customer", "supplier_deposit": "supplier"}.get(
        deposit.type
    )
    if side is None:
        raise core.InvalidOperation("Select a customer or supplier deposit.")
    invoice = core._tenant_record(session, Document, tenant_id, invoice_id)
    expected = "sales_invoice" if side == "customer" else "supplier_invoice"
    if invoice.type != expected:
        raise core.InvalidOperation(f"Deposit clearing requires a {expected}.")
    if deposit.party_id != invoice.party_id or deposit.currency != invoice.currency:
        raise core.InvalidOperation("Deposit and invoice must share party and currency.")
    value = core.positive(amount, "amount")
    deposit_entry = core._settlement_control_entry(session, tenant_id, deposit.id)
    invoice_entry = core._settlement_control_entry(session, tenant_id, invoice.id)
    used = sum(
        allocation.amount
        for allocation in core.active_settlement_allocations(session, tenant_id)
        if allocation.payment_ledger_entry_id == deposit_entry.id
    )
    available = deposit_entry.amount - used
    invoice_open = core.open_invoice_amount(session, tenant_id, invoice.id)
    if value > available or value > invoice_open:
        raise core.InvalidOperation("Clearing exceeds deposit availability or invoice open amount.")
    return {
        "side": side,
        "deposit_document_id": deposit.id,
        "invoice_id": invoice.id,
        "deposit_entry_id": deposit_entry.id,
        "invoice_entry_id": invoice_entry.id,
        "amount": str(value),
        "currency": deposit.currency,
        "available_before": str(available),
        "available_after": str(available - value),
        "invoice_open_before": str(invoice_open),
        "invoice_open_after": str(invoice_open - value),
    }


def clear_deposit(
    session: Session,
    tenant_id: str,
    *,
    action_id: str,
    deposit_document_id: str,
    invoice_id: str,
    amount: str,
    expected_revision: int,
) -> dict[str, Any]:
    core._require_business_mutation(session, tenant_id, "clear_deposit")
    state = lock_finance(session, tenant_id)
    if state.revision != expected_revision:
        raise core.Conflict("Finance preview is stale; reload and confirm again.")
    preview = preview_clearing(
        session,
        tenant_id,
        deposit_document_id=deposit_document_id,
        invoice_id=invoice_id,
        amount=amount,
        expected_revision=expected_revision,
    )
    allocation = core.allocate_settlement(
        session,
        tenant_id,
        preview["deposit_entry_id"],
        preview["invoice_entry_id"],
        Decimal(preview["amount"]),
        action_id=action_id,
        _commit=False,
    )
    # Read models in the same confirmed transaction must observe the allocation;
    # this also keeps consecutive profile seeds deterministic with autoflush-disabled sessions.
    session.flush()
    return {**preview, "allocation_id": allocation.id}


def _deposit_result(
    document: Document, control: LedgerEntry, source_record_id: str
) -> dict[str, Any]:
    return {
        "document_id": document.id,
        "number": document.number,
        "source_record_id": source_record_id,
        "control_entry_id": control.id,
        "posting_group_id": control.posting_group_id,
        "amount": str(control.amount),
        "currency": control.currency,
    }
