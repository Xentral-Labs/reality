"""Authorizations and captures of card and wallet payments (spec 336).

An authorization is what a provider stated it reserved for one sales order,
until when; a capture is what it then took against that authorization. Both
are recorded as stated. What is left of an authorization, and whether an
expired one leaves an order's remaining goods unsecured, is derived at read
time and never stored.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from decimal import InvalidOperation as DecimalInvalid
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from reality.db.core import (
    Commitment,
    Document,
    PaymentAuthorization,
    PaymentCapture,
    uid,
)
from reality.services import core
from reality.services.core import emit_business_event
from reality.services.finance.accounts import lock_finance

SOURCE_SYSTEM = "internal_payment_authorization"
AMOUNT_EXPONENT = -4


def _amount(value: Any) -> Decimal | None:
    """A positive amount with at most four decimals, or None."""
    try:
        amount = Decimal(str(value))
    except (TypeError, ValueError, DecimalInvalid):
        return None
    if (
        not amount.is_finite()
        or amount <= 0
        or amount.as_tuple().exponent < AMOUNT_EXPONENT
    ):
        return None
    return amount


def _instant(value: Any) -> datetime | None:
    """A stated date-time, or None."""
    try:
        return core.utc_datetime(value)
    except (TypeError, ValueError):
        return None


def _text(amount: Decimal) -> str:
    return format(Decimal(amount).normalize(), "f")


def _captured(
    session: Session,
    tenant_id: str,
    authorization_ids: set[str],
    as_of: datetime | None = None,
) -> dict[str, Decimal]:
    """What was captured per authorization, up to the instant when one is given."""
    if not authorization_ids:
        return {}
    return {
        authorization_id: Decimal(total)
        for authorization_id, total in session.execute(
            select(PaymentCapture.authorization_id, func.sum(PaymentCapture.amount))
            .where(
                PaymentCapture.tenant_id == tenant_id,
                PaymentCapture.authorization_id.in_(authorization_ids),
                *([PaymentCapture.captured_at <= as_of] if as_of else []),
            )
            .group_by(PaymentCapture.authorization_id)
        )
    }


def preview_authorization(
    session: Session, tenant_id: str, values: dict[str, Any]
) -> dict[str, Any]:
    """
    The stated authorization, checked against its order; records nothing.

    BUSINESS PURPOSE:
    The stated authorization, checked against its order; records nothing.

    BUSINESS RULE services.payment_authorizations.preview_authorization.refusal-7:
    IF the selected document is not a sales order:
        Refuse with payment_authorization_order_invalid.

    BUSINESS RULE services.payment_authorizations.preview_authorization.refusal-10:
    IF the authorization amount cannot be parsed as a valid amount:
        Refuse with payment_authorization_amount_invalid.

    BUSINESS RULE services.payment_authorizations.preview_authorization.refusal-12:
    IF the authorization currency differs from the sales order currency:
        Refuse with payment_authorization_currency_mismatch.

    BUSINESS RULE services.payment_authorizations.preview_authorization.refusal-16:
    IF the authorization or expiry timestamp is invalid:
        Refuse with payment_authorization_time_invalid.

    BUSINESS RULE services.payment_authorizations.preview_authorization.refusal-18:
    IF expiry is equal to or earlier than authorization time:
        Refuse with payment_authorization_expiry_invalid.

    BUSINESS RULE services.payment_authorizations.preview_authorization.refusal-21:
    IF the authorization reference is empty after trimming whitespace:
        Refuse with payment_authorization_reference_missing.

    BUSINESS RULE services.payment_authorizations.preview_authorization.refusal-23:
    IF this company already has an authorization with the same order and reference:
        Refuse with payment_authorization_duplicate.

    BUSINESS RULE services.payment_authorizations.preview_authorization.result:
    Return the current result with order_document_id, order_number, party_id, amount, currency, authorized_at, expires_at, reference.
    """
    order = core._tenant_record(
        session, Document, tenant_id, str(values.get("order_document_id") or "")
    )
    # reality-rule: services.payment_authorizations.preview_authorization.refusal-7
    if order.type != "sales_order":
        raise core.InvalidOperation(code="payment_authorization_order_invalid")
    amount = _amount(values.get("amount"))
    # reality-rule: services.payment_authorizations.preview_authorization.refusal-10
    if amount is None:
        raise core.InvalidOperation(code="payment_authorization_amount_invalid")
    # reality-rule: services.payment_authorizations.preview_authorization.refusal-12
    if values.get("currency") != order.currency:
        raise core.InvalidOperation(code="payment_authorization_currency_mismatch")
    authorized_at = _instant(values.get("authorized_at"))
    expires_at = _instant(values.get("valid_until"))
    # reality-rule: services.payment_authorizations.preview_authorization.refusal-16
    if authorized_at is None or expires_at is None:
        raise core.InvalidOperation(code="payment_authorization_time_invalid")
    # reality-rule: services.payment_authorizations.preview_authorization.refusal-18
    if expires_at <= authorized_at:
        raise core.InvalidOperation(code="payment_authorization_expiry_invalid")
    reference = str(values.get("reference") or "").strip()
    # reality-rule: services.payment_authorizations.preview_authorization.refusal-21
    if not reference:
        raise core.InvalidOperation(code="payment_authorization_reference_missing")
    # reality-rule: services.payment_authorizations.preview_authorization.refusal-23
    if session.scalar(
        select(PaymentAuthorization.id).where(
            PaymentAuthorization.tenant_id == tenant_id,
            PaymentAuthorization.order_document_id == order.id,
            PaymentAuthorization.reference == reference,
        )
    ):
        raise core.InvalidOperation(code="payment_authorization_duplicate")
    # reality-rule: services.payment_authorizations.preview_authorization.result
    return {
        "order_document_id": order.id,
        "order_number": order.number,
        "party_id": order.party_id,
        "amount": _text(amount),
        "currency": order.currency,
        "authorized_at": authorized_at.isoformat(),
        "expires_at": expires_at.isoformat(),
        "reference": reference,
    }


def record_authorization(
    session: Session,
    tenant_id: str,
    *,
    action_id: str,
    actor_id: str | None,
    **values: Any,
) -> dict[str, Any]:
    """
    Record the stated authorization; callers own the transaction.

    BUSINESS PURPOSE:
    Record the stated authorization; callers own the transaction.

    BUSINESS RULE services.payment_authorizations.record_authorization.step-9:
    Require the business permission for 'record_payment_authorization' before changing company records.

    BUSINESS RULE services.payment_authorizations.record_authorization.step-11:
    Run the shared preview authorization check and use its normalized inputs and current review evidence. Inspect that called function for its detailed eligibility rules.

    BUSINESS RULE services.payment_authorizations.record_authorization.step-12:
    Pass the stated inputs to the shared store source record service. Its own source describes validation and record changes.

    BUSINESS RULE services.payment_authorizations.record_authorization.step-33:
    Record the payment.authorized audit or business-event evidence with the supplied record and confirmation identity.

    BUSINESS RULE services.payment_authorizations.record_authorization.result:
    Return the result from authorization detail; inspect that called function for its calculation and eligibility rules.
    """
    # reality-rule: services.payment_authorizations.record_authorization.step-9
    core._require_business_mutation(session, tenant_id, "record_payment_authorization")
    lock_finance(session, tenant_id)
    # reality-rule: services.payment_authorizations.record_authorization.step-11
    preview = preview_authorization(session, tenant_id, values)
    # reality-rule: services.payment_authorizations.record_authorization.step-12
    source, _, _ = core.store_source_record(
        session,
        tenant_id,
        SOURCE_SYSTEM,
        "payment_authorization",
        action_id,
        {**preview, "actor_id": actor_id, "confirmation_id": action_id},
    )
    row = PaymentAuthorization(
        id=uid("pau"),
        tenant_id=tenant_id,
        order_document_id=preview["order_document_id"],
        amount=Decimal(preview["amount"]),
        currency=preview["currency"],
        authorized_at=datetime.fromisoformat(preview["authorized_at"]),
        expires_at=datetime.fromisoformat(preview["expires_at"]),
        reference=preview["reference"],
        source_record_id=source.id,
    )
    session.add(row)
    session.flush()
    # reality-rule: services.payment_authorizations.record_authorization.step-33
    emit_business_event(
        session,
        tenant_id,
        "payment.authorized",
        "payment_authorization",
        row.id,
        {
            key: preview[key]
            for key in (
                "order_document_id",
                "amount",
                "currency",
                "authorized_at",
                "expires_at",
                "reference",
            )
        },
        source_record_id=source.id,
        action_id=action_id,
    )
    # reality-rule: services.payment_authorizations.record_authorization.result
    return authorization_detail(session, tenant_id, row.id)


def preview_capture(
    session: Session, tenant_id: str, values: dict[str, Any]
) -> dict[str, Any]:
    """
    The stated capture, within what is left and before the expiry; records nothing.

    BUSINESS PURPOSE:
    The stated capture, within what is left and before the expiry; records nothing.

    BUSINESS RULE services.payment_authorizations.preview_capture.refusal-11:
    IF the capture amount cannot be parsed as a valid amount:
        Refuse with payment_capture_amount_invalid.

    BUSINESS RULE services.payment_authorizations.preview_capture.refusal-14:
    IF the capture timestamp is invalid:
        Refuse with payment_capture_time_invalid.

    BUSINESS RULE services.payment_authorizations.preview_capture.refusal-16:
    IF capture time is earlier than authorization time:
        Refuse with payment_capture_before_authorization.

    BUSINESS RULE services.payment_authorizations.preview_capture.refusal-18:
    IF capture time is later than authorization expiry:
        Refuse with payment_capture_after_expiry.

    BUSINESS RULE services.payment_authorizations.preview_capture.refusal-24:
    IF the capture amount exceeds the authorization amount still available:
        Refuse with payment_capture_exceeds_authorization.

    BUSINESS RULE services.payment_authorizations.preview_capture.result:
    Return the current result with authorization_id, order_document_id, amount, currency, captured_at, reference, remaining_after.
    """
    authorization = core._tenant_record(
        session,
        PaymentAuthorization,
        tenant_id,
        str(values.get("authorization_id") or ""),
    )
    amount = _amount(values.get("amount"))
    # reality-rule: services.payment_authorizations.preview_capture.refusal-11
    if amount is None:
        raise core.InvalidOperation(code="payment_capture_amount_invalid")
    captured_at = _instant(values.get("captured_at"))
    # reality-rule: services.payment_authorizations.preview_capture.refusal-14
    if captured_at is None:
        raise core.InvalidOperation(code="payment_capture_time_invalid")
    # reality-rule: services.payment_authorizations.preview_capture.refusal-16
    if captured_at < core.utc_datetime(authorization.authorized_at):
        raise core.InvalidOperation(code="payment_capture_before_authorization")
    # reality-rule: services.payment_authorizations.preview_capture.refusal-18
    if captured_at > core.utc_datetime(authorization.expires_at):
        raise core.InvalidOperation(code="payment_capture_after_expiry")
    captured = _captured(session, tenant_id, {authorization.id}).get(
        authorization.id, Decimal(0)
    )
    remaining = Decimal(authorization.amount) - captured
    # reality-rule: services.payment_authorizations.preview_capture.refusal-24
    if amount > remaining:
        raise core.InvalidOperation(
            code="payment_capture_exceeds_authorization",
            values={"remaining": _text(remaining)},
        )
    # reality-rule: services.payment_authorizations.preview_capture.result
    return {
        "authorization_id": authorization.id,
        "order_document_id": authorization.order_document_id,
        "amount": _text(amount),
        "currency": authorization.currency,
        "captured_at": captured_at.isoformat(),
        "reference": str(values.get("reference") or "").strip(),
        "remaining_after": _text(remaining - amount),
    }


def record_capture(
    session: Session,
    tenant_id: str,
    *,
    action_id: str,
    actor_id: str | None,
    **values: Any,
) -> dict[str, Any]:
    """
    Record the stated capture; callers own the transaction.

    BUSINESS PURPOSE:
    Record the stated capture; callers own the transaction.

    BUSINESS RULE services.payment_authorizations.record_capture.step-9:
    Require the business permission for 'record_payment_capture' before changing company records.

    BUSINESS RULE services.payment_authorizations.record_capture.step-11:
    Run the shared preview capture check and use its normalized inputs and current review evidence. Inspect that called function for its detailed eligibility rules.

    BUSINESS RULE services.payment_authorizations.record_capture.step-12:
    Pass the stated inputs to the shared store source record service. Its own source describes validation and record changes.

    BUSINESS RULE services.payment_authorizations.record_capture.step-31:
    Record the payment.captured audit or business-event evidence with the supplied record and confirmation identity.

    BUSINESS RULE services.payment_authorizations.record_capture.result:
    Return the result from authorization detail; inspect that called function for its calculation and eligibility rules.
    """
    # reality-rule: services.payment_authorizations.record_capture.step-9
    core._require_business_mutation(session, tenant_id, "record_payment_capture")
    lock_finance(session, tenant_id)
    # reality-rule: services.payment_authorizations.record_capture.step-11
    preview = preview_capture(session, tenant_id, values)
    # reality-rule: services.payment_authorizations.record_capture.step-12
    source, _, _ = core.store_source_record(
        session,
        tenant_id,
        SOURCE_SYSTEM,
        "payment_capture",
        action_id,
        {**preview, "actor_id": actor_id, "confirmation_id": action_id},
    )
    row = PaymentCapture(
        id=uid("pcp"),
        tenant_id=tenant_id,
        authorization_id=preview["authorization_id"],
        amount=Decimal(preview["amount"]),
        captured_at=datetime.fromisoformat(preview["captured_at"]),
        reference=preview["reference"],
        source_record_id=source.id,
    )
    session.add(row)
    session.flush()
    # reality-rule: services.payment_authorizations.record_capture.step-31
    emit_business_event(
        session,
        tenant_id,
        "payment.captured",
        "payment_capture",
        row.id,
        {
            key: preview[key]
            for key in (
                "authorization_id",
                "order_document_id",
                "amount",
                "currency",
                "captured_at",
                "reference",
            )
        },
        source_record_id=source.id,
        action_id=action_id,
    )
    # reality-rule: services.payment_authorizations.record_capture.result
    return authorization_detail(session, tenant_id, preview["authorization_id"])


def _row(
    authorization: PaymentAuthorization, captured: Decimal, as_of: datetime
) -> dict[str, Any]:
    remaining = Decimal(authorization.amount) - captured
    expires_at = core.utc_datetime(authorization.expires_at)
    return {
        "id": authorization.id,
        "order_document_id": authorization.order_document_id,
        "amount": _text(authorization.amount),
        "currency": authorization.currency,
        "authorized_at": core.utc_datetime(authorization.authorized_at).isoformat(),
        "expires_at": expires_at.isoformat(),
        "reference": authorization.reference,
        "captured": _text(captured),
        "remaining": _text(remaining),
        "state": "captured"
        if remaining <= 0
        else "expired"
        if expires_at <= as_of
        else "live",
        "source_record_id": authorization.source_record_id,
    }


def authorization_detail(
    session: Session, tenant_id: str, authorization_id: str
) -> dict[str, Any]:
    authorization = core._tenant_record(
        session, PaymentAuthorization, tenant_id, authorization_id
    )
    captured = _captured(session, tenant_id, {authorization.id})
    row = _row(authorization, captured.get(authorization.id, Decimal(0)), core.now())
    row["captures"] = [
        {
            "id": capture.id,
            "amount": _text(capture.amount),
            "captured_at": core.utc_datetime(capture.captured_at).isoformat(),
            "reference": capture.reference,
        }
        for capture in session.scalars(
            select(PaymentCapture)
            .where(
                PaymentCapture.tenant_id == tenant_id,
                PaymentCapture.authorization_id == authorization.id,
            )
            .order_by(PaymentCapture.captured_at, PaymentCapture.id)
        )
    ]
    return row


def authorizations(
    session: Session,
    tenant_id: str,
    *,
    order_document_id: str | None = None,
    as_of: datetime | None = None,
) -> list[dict[str, Any]]:
    """
    Authorizations with what was captured and what is left, at the instant.

    BUSINESS PURPOSE:
    Authorizations with what was captured and what is left, at the instant.

    BUSINESS RULE services.payment_authorizations.authorizations.result:
    Return the selected records in the displayed response structure; preserve the source identifiers and stated values used by this comprehension.
    """
    core.get_tenant(session, tenant_id)
    as_of = core.utc_datetime(as_of) or core.now()
    rows = list(
        session.scalars(
            select(PaymentAuthorization)
            .where(
                PaymentAuthorization.tenant_id == tenant_id,
                PaymentAuthorization.authorized_at <= as_of,
                *(
                    [PaymentAuthorization.order_document_id == order_document_id]
                    if order_document_id
                    else []
                ),
            )
            .order_by(PaymentAuthorization.authorized_at, PaymentAuthorization.id)
        )
    )
    captured = _captured(session, tenant_id, {row.id for row in rows}, as_of)
    # reality-rule: services.payment_authorizations.authorizations.result
    return [_row(row, captured.get(row.id, Decimal(0)), as_of) for row in rows]


def uncovered_orders(
    session: Session, tenant_id: str, *, as_of: datetime | None = None
) -> list[dict[str, Any]]:
    """Orders with goods still to ship whose expired authorizations nothing covers."""
    as_of = core.utc_datetime(as_of) or core.now()
    by_order: dict[str, list[dict[str, Any]]] = {}
    for row in authorizations(session, tenant_id, as_of=as_of):
        by_order.setdefault(row["order_document_id"], []).append(row)
    candidates = {
        order_id: rows
        for order_id, rows in by_order.items()
        if any(row["state"] == "expired" for row in rows)
    }
    if not candidates:
        return []
    open_orders = set(
        session.scalars(
            select(Commitment.document_id).where(
                Commitment.tenant_id == tenant_id,
                Commitment.document_id.in_(candidates),
                Commitment.type == "customer_delivery",
                Commitment.status == "open",
            )
        )
    )
    findings = []
    for order_id, rows in candidates.items():
        if order_id not in open_orders:
            continue
        expired = [row for row in rows if row["state"] == "expired"]
        lapsed = sum((Decimal(row["remaining"]) for row in expired), Decimal(0))
        live = sum(
            (Decimal(row["remaining"]) for row in rows if row["state"] == "live"),
            Decimal(0),
        )
        uncovered = lapsed - live
        if uncovered <= 0:
            continue
        findings.append(
            {
                "order_document_id": order_id,
                "authorized": _text(
                    sum((Decimal(row["amount"]) for row in rows), Decimal(0))
                ),
                "captured": _text(
                    sum((Decimal(row["captured"]) for row in rows), Decimal(0))
                ),
                "uncovered": _text(uncovered),
                "currency": rows[0]["currency"],
                "expired_at": max(
                    datetime.fromisoformat(row["expires_at"]) for row in expired
                ),
                "authorization_ids": [row["id"] for row in expired],
            }
        )
    return findings
