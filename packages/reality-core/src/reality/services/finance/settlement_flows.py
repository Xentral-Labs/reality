"""Reviewed actual payments, explicit differences and existing-credit consumption."""

import hashlib
import json
from datetime import datetime
from decimal import Decimal
from decimal import InvalidOperation as InvalidDecimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from reality.db.core import Document, LedgerEntry, Party, SourceRecord
from reality.domain.finance import OPENING_CREDITS, OPENING_DEBTS
from reality.services import core
from reality.services.business_locks import lock_delivery_state
from reality.services.finance.accounts import (
    list_accounts,
    lock_finance,
    resolve_account,
)
from reality.services.finance.settlement import (
    accept_adjustment,
    adjustment_context,
    preview_adjustment,
)

SOURCE_SYSTEM = "internal_settlement_cash"
INVOICES = {
    "sales_invoice": "customer",
    "supplier_invoice": "supplier",
    **OPENING_DEBTS,
}
CREDITS = {
    **OPENING_CREDITS,
    "customer_payment": "customer",
    "credit_note": "customer",
    "supplier_payment": "supplier",
    "supplier_credit_note": "supplier",
}


def _amount(value: str, *, zero: bool = False) -> Decimal:
    try:
        result = Decimal(value)
    except (InvalidDecimal, ValueError, TypeError) as error:
        raise core.InvalidOperation("Enter a valid stated decimal amount.") from error
    if not result.is_finite() or result < 0 or (result == 0 and not zero):
        raise core.InvalidOperation("Enter a positive stated amount.")
    if result >= Decimal(100000000000000):
        raise core.InvalidOperation("Amount exceeds the supported monetary range.")
    if result.as_tuple().exponent < -4:
        raise core.InvalidOperation("Amount supports at most four decimal places.")
    return result


def _credit(
    session: Session, tenant_id: str, document: Document
) -> tuple[LedgerEntry, Decimal]:
    side = CREDITS.get(document.type)
    if not side:
        raise core.InvalidOperation("Select an original payment or credit note.")
    role = "accounts_receivable" if side == "customer" else "accounts_payable"
    entries = list(
        session.scalars(
            select(LedgerEntry).where(
                LedgerEntry.tenant_id == tenant_id,
                LedgerEntry.document_id == document.id,
                LedgerEntry.account == role,
                LedgerEntry.debit_credit
                == ("credit" if side == "customer" else "debit"),
            )
        )
    )
    if len(entries) != 1:
        raise core.InvalidOperation("Credit must have one original control entry.")
    entry = entries[0]
    if core._ledger_reversal_for_group(session, tenant_id, entry.posting_group_id)[0]:
        raise core.InvalidOperation("Credit has been reversed.")
    used = sum(
        (
            a.amount
            for a in core.active_settlement_allocations(session, tenant_id)
            if entry.id in (a.payment_ledger_entry_id, a.invoice_ledger_entry_id)
        ),
        Decimal(0),
    )
    return entry, entry.amount - used


def settlement_context(
    session: Session, tenant_id: str, document_id: str, query: str = ""
) -> dict[str, Any]:
    """Read an invoice or original credit and bounded matching invoice choices."""
    document = core._tenant_record(session, Document, tenant_id, document_id)
    accounts = list_accounts(session, tenant_id)
    if document.type in INVOICES:
        context = adjustment_context(session, tenant_id, document.id)
        context["party"] = core._tenant_record(
            session, Party, tenant_id, context["party_id"]
        ).name
        return {
            **context,
            "document_id": document.id,
            "kind": "invoice",
            "cash_account": next(
                (
                    a
                    for a in accounts["accounts"]
                    if a["id"] == accounts["defaults"].get("cash")
                ),
                None,
            ),
        }
    control, available = _credit(session, tenant_id, document)
    side = CREDITS[document.type]
    party = core._tenant_record(session, Party, tenant_id, control.party_id)
    statement = select(Document).where(
        Document.tenant_id == tenant_id,
        Document.party_id == control.party_id,
        Document.currency == control.currency,
        Document.type.in_([kind for kind, value in INVOICES.items() if value == side]),
    )
    if query.strip():
        statement = statement.where(Document.number.ilike(f"%{query.strip()}%"))
    # Feature 168: an unallocated customer payment carries read-time candidates
    # with the reason each invoice fits; they are observations, never stored.
    reasons: dict[str, tuple[str, ...]] = {}
    if document.type == "customer_payment":
        from reality.services.payment_intake import payment_candidates

        reasons = {
            candidate.invoice_id: candidate.reasons
            for candidate in payment_candidates(session, tenant_id, document.id)
        }
    choices = []
    for invoice in session.scalars(statement.order_by(Document.id)):
        try:
            entry = core._settlement_control_entry(session, tenant_id, invoice.id)
            opened = core.open_invoice_amount(session, tenant_id, invoice.id)
        except core.InvalidOperation:
            continue
        if opened > 0 and entry.account_id == control.account_id:
            choices.append(
                {
                    "id": invoice.id,
                    "number": invoice.number,
                    "open": str(opened),
                    "currency": invoice.currency,
                    "reasons": list(reasons.get(invoice.id, ())),
                }
            )
        if len(choices) == 51:
            break
    choices.sort(key=lambda choice: (not choice["reasons"], choice["number"]))
    return {
        "document_id": document.id,
        "number": document.number,
        "kind": "credit",
        "side": side,
        "party_id": control.party_id,
        "party": party.name,
        "currency": control.currency,
        "available": str(available),
        "control_entry_id": control.id,
        "control_account_id": control.account_id,
        "control_account_code": control.account_record.code,
        "source_record_id": control.source_record_id or document.source_record_id,
        "revision": accounts["revision"],
        "invoices": choices[:50],
        "more_invoices": len(choices) > 50,
        "candidates": [choice for choice in choices[:50] if choice["reasons"]],
    }


def _cash_evidence(session: Session, tenant_id: str, values: dict) -> str | None:
    source_id, effect_id = (
        values.get("source_record_id"),
        values.get("source_effect_id"),
    )
    if bool(source_id) != bool(effect_id):
        raise core.InvalidOperation(
            "External evidence requires both source and effect identity."
        )
    if not source_id:
        return None
    original = core._tenant_record(session, SourceRecord, tenant_id, source_id)
    if original.source_system == SOURCE_SYSTEM:
        raise core.Conflict("This cash evidence has already been recorded.")
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
        raise core.Conflict("This cash effect has already been recorded.")
    if session.scalar(
        select(Document.id)
        .join(SourceRecord, Document.source_record_id == SourceRecord.id)
        .where(
            Document.tenant_id == tenant_id,
            SourceRecord.tenant_id == tenant_id,
            SourceRecord.source_system == original.source_system,
            SourceRecord.source_type == original.source_type,
            SourceRecord.external_id == original.external_id,
            Document.type.in_(
                (
                    "customer_payment",
                    "supplier_payment",
                    "customer_refund",
                    "supplier_refund",
                )
            ),
        )
    ):
        raise core.Conflict(
            "Reuse the existing cash document instead of recording it again."
        )
    return identity


def preview_settlement(session: Session, tenant_id: str, values: dict) -> dict:
    context = settlement_context(session, tenant_id, values["document_id"])
    if context["revision"] != values["expected_revision"]:
        raise core.Conflict("Finance preview is stale; reload and confirm again.")
    mode, side = values["mode"], context["side"]
    role = "accounts_receivable" if side == "customer" else "accounts_payable"
    resolve_account(session, tenant_id, role, context["control_account_id"])
    amount = _amount(values["amount"])
    allocated, reduction, remaining, available = Decimal(0), None, None, Decimal(0)
    invoice_id, target_entry_id, invoice_number = None, None, None
    if mode == "payment":
        if context["kind"] != "invoice":
            raise core.InvalidOperation("Select an invoice for payment.")
        allocated = _amount(values["allocation_amount"], zero=True)
        if allocated > amount or allocated > Decimal(context["open"]):
            raise core.InvalidOperation(
                "Allocation exceeds payment or open invoice amount."
            )
        remaining = Decimal(context["open"]) - allocated
        if values.get("reduction"):
            reduction = preview_adjustment(
                session,
                tenant_id,
                {
                    **values["reduction"],
                    "invoice_id": context["document_id"],
                    "expected_revision": values["expected_revision"],
                },
            )
            remaining -= Decimal(reduction["amount"])
            if remaining < 0:
                raise core.InvalidOperation(
                    "Payment allocation and reduction exceed the open invoice amount."
                )
        available = amount - allocated
        invoice_number = context["number"]
        invoice_id, target_entry_id = (
            context["document_id"],
            context["control_entry_id"],
        )
    else:
        if context["kind"] != "credit":
            raise core.InvalidOperation("Select existing available credit.")
        if amount > Decimal(context["available"]):
            raise core.InvalidOperation("Amount exceeds available credit.")
        available = Decimal(context["available"]) - amount
        allocated = amount
        if mode == "allocate_credit":
            target = adjustment_context(session, tenant_id, values["invoice_id"])
            if any(
                context[k] != target[k]
                for k in ("party_id", "currency", "control_account_id", "side")
            ):
                raise core.InvalidOperation(
                    "Credit and invoice must have the same party, currency and account."
                )
            if amount > Decimal(target["open"]):
                raise core.InvalidOperation(
                    "Allocation exceeds the open invoice amount."
                )
            remaining = Decimal(target["open"]) - amount
            invoice_number = target["number"]
            invoice_id, target_entry_id = (
                target["invoice_id"],
                target["control_entry_id"],
            )
        elif mode != "refund_credit":
            raise core.InvalidOperation("Unsupported settlement mode.")
    cash = mode != "allocate_credit"
    identity, cash_account = None, None
    if cash:
        if not values["reference"].strip():
            raise core.InvalidOperation("Document the actual payment reference.")
        try:
            stated_time = datetime.fromisoformat(values["effective_at"])
            if stated_time.tzinfo is None:
                raise core.InvalidOperation(
                    "Payment timestamp must include its timezone."
                )
            effective = core.utc_datetime(stated_time)
        except (ValueError, TypeError, AttributeError) as error:
            raise core.InvalidOperation("Enter a valid payment timestamp.") from error
        if effective is None:
            raise core.InvalidOperation("Actual payment time is required.")
        cash_account = resolve_account(session, tenant_id, "cash")
        identity = _cash_evidence(session, tenant_id, values)
    return {
        "mode": mode,
        "document_id": context["document_id"],
        "number": context["number"],
        "party": context["party"],
        "invoice_number": invoice_number,
        "side": side,
        "party_id": context["party_id"],
        "currency": context["currency"],
        "control_entry_id": context["control_entry_id"],
        "control_account_id": context["control_account_id"],
        "control_account_code": context["control_account_code"],
        "cash_account_code": cash_account.code if cash_account else None,
        "cash_amount": str(amount if cash else Decimal(0)),
        "cash_direction": (
            "incoming" if (side == "customer") == (mode == "payment") else "outgoing"
        )
        if cash
        else "none",
        "allocation_amount": str(allocated),
        "reduction_amount": reduction["amount"] if reduction else "0",
        "remaining_claim": str(remaining) if remaining is not None else None,
        "remaining_credit": str(available),
        "invoice_id": invoice_id,
        "target_entry_id": target_entry_id,
        "reduction": reduction,
        "effect_identity": identity,
        "reference": values.get("reference"),
        "effective_at": values.get("effective_at"),
        "source_record_id": values.get("source_record_id"),
    }


def apply_settlement(
    session: Session, tenant_id: str, *, action_id: str, actor_id: str | None, **values
) -> dict:
    """Compose existing primitives inside the confirmed finance transaction."""
    lock_delivery_state(session, tenant_id)
    lock_finance(session, tenant_id)
    preview = preview_settlement(session, tenant_id, values)
    mode, side = preview["mode"], preview["side"]
    role = "accounts_receivable" if side == "customer" else "accounts_payable"
    result = {
        **preview,
        "payment": None,
        "refund": None,
        "reduction": None,
        "allocation_id": None,
    }
    with session.begin_nested():
        source_entry_id, target_entry_id = (
            preview["control_entry_id"],
            preview["target_entry_id"],
        )
        if mode != "allocate_credit":
            source, _, _ = core.store_source_record(
                session,
                tenant_id,
                SOURCE_SYSTEM,
                "actual_cash",
                preview["effect_identity"] or action_id,
                {
                    **values,
                    "currency": preview["currency"],
                    "actor_id": actor_id,
                    "confirmation_id": action_id,
                    "confirmed_at": core.now().isoformat(),
                },
            )
            refund = mode == "refund_credit"
            record = getattr(core, f"record_{side}_{'refund' if refund else 'payment'}")
            entries = record(
                session,
                tenant_id,
                preview["party_id"],
                values["amount"],
                currency=preview["currency"],
                source_record_id=source.id,
                effective_at=core.utc_datetime(values["effective_at"]),
                action_id=action_id,
                _control_account_id=preview["control_account_id"],
                _commit=False,
                **{
                    ("refund_number" if refund else "payment_number"): values[
                        "reference"
                    ]
                },
            )
            control = next(e for e in entries if e.account == role)
            result["refund" if refund else "payment"] = {
                "document_id": control.document_id,
                "source_record_id": source.id,
                "posting_group_id": control.posting_group_id,
                "ledger_entry_ids": [e.id for e in entries],
            }
            if refund:
                target_entry_id = control.id
            else:
                source_entry_id = control.id
        if Decimal(preview["allocation_amount"]) > 0:
            allocation = core.allocate_settlement(
                session,
                tenant_id,
                source_entry_id,
                target_entry_id,
                preview["allocation_amount"],
                action_id=action_id,
                _commit=False,
            )
            result["allocation_id"] = allocation.id
        if values.get("reduction"):
            result["reduction"] = accept_adjustment(
                session,
                tenant_id,
                action_id=action_id,
                actor_id=actor_id,
                invoice_id=preview["invoice_id"],
                expected_revision=list_accounts(session, tenant_id)["revision"],
                **values["reduction"],
            )
    return result
