"""Confirmed, stated noncash reductions of individual operational claims."""

import hashlib
import json
from decimal import Decimal
from decimal import InvalidOperation as InvalidDecimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from reality.db.core import Document, SourceRecord
from reality.services import core
from reality.services.finance.accounts import (
    list_accounts,
    lock_finance,
    resolve_account,
)

REASONS = {
    "early_payment_discount",
    "agreed_deduction",
    "accepted_small_remainder",
    "bad_debt",
}
SOURCE_SYSTEM = "internal_settlement_adjustment"


def adjustment_context(
    session: Session, tenant_id: str, invoice_id: str
) -> dict[str, Any]:
    invoice = core._tenant_record(session, Document, tenant_id, invoice_id)
    if invoice.type not in {
        "sales_invoice",
        "supplier_invoice",
        "opening_customer_debt",
        "opening_supplier_debt",
    }:
        raise core.InvalidOperation("Select a customer or supplier invoice.")
    control = core._settlement_control_entry(session, tenant_id, invoice.id)
    side = (
        "customer"
        if invoice.type in {"sales_invoice", "opening_customer_debt"}
        else "supplier"
    )
    accounts = list_accounts(session, tenant_id)
    role = f"{side}_reduction"
    counterpart = next(
        (a for a in accounts["accounts"] if a["id"] == accounts["defaults"].get(role)),
        None,
    )
    return {
        "invoice_id": invoice.id,
        "number": invoice.number,
        "side": side,
        "party_id": control.party_id,
        "currency": control.currency,
        "open": str(core.open_invoice_amount(session, tenant_id, invoice.id)),
        "revision": accounts["revision"],
        "control_entry_id": control.id,
        "control_account_id": control.account_id,
        "control_account_code": control.account_record.code,
        "counterpart": counterpart,
    }


def preview_adjustment(session: Session, tenant_id: str, values: dict) -> dict:
    context = adjustment_context(session, tenant_id, values["invoice_id"])
    if context["revision"] != values["expected_revision"]:
        raise core.Conflict("Finance preview is stale; reload and confirm again.")
    try:
        amount = core.positive(values["amount"], "amount")
    except (InvalidDecimal, ValueError, TypeError) as error:
        raise core.InvalidOperation("Enter a valid stated decimal amount.") from error
    if amount.as_tuple().exponent < -4:
        raise core.InvalidOperation("Amount supports at most four decimal places.")
    if amount > Decimal(context["open"]):
        raise core.InvalidOperation("Reduction exceeds the remaining invoice amount.")
    if values["reason_category"] not in REASONS or not values["reason"].strip():
        raise core.InvalidOperation("A supported reason and explanation are required.")
    if values["reason_category"] == "bad_debt" and context["side"] != "customer":
        raise core.InvalidOperation("Bad debt is supported for customer receivables only.")
    if context["side"] == "supplier" and not values.get("agreement", "").strip():
        raise core.InvalidOperation("Document the supplier entitlement or agreement.")
    resolve_account(
        session,
        tenant_id,
        "accounts_receivable" if context["side"] == "customer" else "accounts_payable",
        context["control_account_id"],
    )
    counterpart_role = (
        "bad_debt_expense"
        if values["reason_category"] == "bad_debt"
        else f"{context['side']}_reduction"
    )
    counterpart = resolve_account(session, tenant_id, counterpart_role)
    source_id, effect_id = (
        values.get("source_record_id"),
        values.get("source_effect_id"),
    )
    if bool(source_id) != bool(effect_id):
        raise core.InvalidOperation(
            "External evidence requires both source and effect identity."
        )
    identity = None
    if source_id:
        original = core._tenant_record(session, SourceRecord, tenant_id, source_id)
        if original.source_system == SOURCE_SYSTEM:
            raise core.Conflict("This source adjustment has already been accepted.")
        if session.scalar(
            select(Document.id)
            .join(SourceRecord, Document.source_record_id == SourceRecord.id)
            .where(
                Document.tenant_id == tenant_id,
                SourceRecord.tenant_id == tenant_id,
                SourceRecord.source_system == original.source_system,
                SourceRecord.source_type == original.source_type,
                SourceRecord.external_id == original.external_id,
                Document.type.in_(("credit_note", "supplier_credit_note")),
            )
        ):
            raise core.InvalidOperation("Allocate the existing credit note instead.")
        identity = (
            "effect:"
            + hashlib.sha256(
                json.dumps(
                    [
                        original.source_system,
                        original.source_type,
                        original.external_id,
                        effect_id,
                    ],
                    ensure_ascii=False,
                    separators=(",", ":"),
                ).encode()
            ).hexdigest()
        )
        if session.scalar(
            select(SourceRecord.id).where(
                SourceRecord.tenant_id == tenant_id,
                SourceRecord.source_system == SOURCE_SYSTEM,
                SourceRecord.external_id == identity,
            )
        ):
            raise core.Conflict("This source adjustment has already been accepted.")
    return {
        **context,
        "amount": str(amount),
        "remaining": str(Decimal(context["open"]) - amount),
        "cash_change": "0",
        "counterpart_account_id": counterpart.id,
        "counterpart_account_code": counterpart.code,
        "counterpart_role": counterpart_role,
        "reason_category": values["reason_category"],
        "reason": values["reason"],
        "agreement": values.get("agreement", ""),
        "source_record_id": source_id,
        "source_effect_id": effect_id,
        "effect_identity": identity,
    }


def accept_adjustment(
    session: Session,
    tenant_id: str,
    *,
    action_id: str,
    actor_id: str | None,
    invoice_id: str,
    amount: str,
    expected_revision: int,
    reason_category: str,
    reason: str,
    agreement: str = "",
    source_record_id: str | None = None,
    source_effect_id: str | None = None,
) -> dict:
    """Called only inside the confirmed tool transaction; never commits independently."""
    from reality.services.business_locks import lock_delivery_state

    values = {
        "invoice_id": invoice_id,
        "amount": amount,
        "expected_revision": expected_revision,
        "reason_category": reason_category,
        "reason": reason,
        "agreement": agreement,
        "source_record_id": source_record_id,
        "source_effect_id": source_effect_id,
    }
    lock_delivery_state(session, tenant_id)
    lock_finance(session, tenant_id)
    preview = preview_adjustment(session, tenant_id, values)
    side = preview["side"]
    amount = Decimal(preview["amount"])
    with session.begin_nested():
        source, _, _ = core.store_source_record(
            session,
            tenant_id,
            SOURCE_SYSTEM,
            "accepted_reduction",
            preview["effect_identity"] or action_id,
            {
                **values,
                "currency": preview["currency"],
                "amount": str(amount),
                "actor_id": actor_id,
                "confirmation_id": action_id,
                "accepted_at": core.now().isoformat(),
            },
        )
        document = core.create_document(
            session,
            tenant_id,
            f"{side}_settlement_adjustment",
            action_id,
            preview["party_id"],
            amount,
            currency=preview["currency"],
            document_date=core.now().date().isoformat(),
            source_record_id=source.id,
            action_id=action_id,
            _commit=False,
        )
        control_role = (
            "accounts_receivable" if side == "customer" else "accounts_payable"
        )
        reduction_role = preview["counterpart_role"]
        entries = core.post_ledger(
            session,
            tenant_id,
            document.id,
            preview["party_id"],
            [
                (control_role, "credit" if side == "customer" else "debit", amount),
                (reduction_role, "debit" if side == "customer" else "credit", amount),
            ],
            account_ids={
                control_role: preview["control_account_id"],
                reduction_role: preview["counterpart_account_id"],
            },
            currency=preview["currency"],
            source_record_id=source.id,
            action_id=action_id,
            _commit=False,
        )
        control = next(e for e in entries if e.account == control_role)
        allocation = core.allocate_settlement(
            session,
            tenant_id,
            control.id,
            preview["control_entry_id"],
            amount,
            action_id=action_id,
            _commit=False,
        )
        return {
            "document_id": document.id,
            "source_record_id": source.id,
            "posting_group_id": control.posting_group_id,
            "ledger_entry_ids": [e.id for e in entries],
            "allocation_id": allocation.id,
            "amount": str(amount),
            "currency": preview["currency"],
            "remaining": preview["remaining"],
            "cash_change": "0",
        }
