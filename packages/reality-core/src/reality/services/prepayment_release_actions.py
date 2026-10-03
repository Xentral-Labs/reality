"""Shipping a prepayment order before it is paid: an owner's decision (spec 347).

A prepayment order stays unshippable until its stated gross amount is paid (spec
275). A company owner may decide to ship it anyway, for one order and with a
stated reason, as the credit hold release of spec 298 does for credit. The
release covers the order's amount as it stood when the owner decided; raising the
order past it asks again. The unpaid remainder stays an ordinary open receivable.
An invoice that also bills other orders is not released this way, because it
leaves open what was paid for this one.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from reality.db.core import (
    BusinessEvent,
    ChangeProposal,
    Commitment,
    Document,
    PrepaymentRelease,
)
from reality.services import core

PREPAYMENT_RELEASE_TOOLS = {"prepayment_release"}
FIELDS = {"document_id", "reason"}


def _json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, default=str, separators=(",", ":"))


def _order_payment(session: Session, tenant_id: str, document_id: str) -> Any:
    from reality.services.fulfillment_readiness import fulfillment_readiness

    order = core._tenant_record(session, Document, tenant_id, document_id)
    # reality-rule: prepayment_release_actions._order_payment.order
    if order.type != "sales_order":
        raise core.InvalidOperation(code="prepayment_release_order_not_found")
    promise = session.scalar(
        select(Commitment)
        .where(
            Commitment.tenant_id == tenant_id,
            Commitment.document_id == order.id,
            Commitment.type == "customer_delivery",
            Commitment.status == "open",
        )
        .order_by(Commitment.id)
        .limit(1)
    )
    # reality-rule: prepayment_release_actions._order_payment.open
    if promise is None:
        raise core.InvalidOperation(code="prepayment_release_nothing_open")
    return order, fulfillment_readiness(
        session, tenant_id, promise.id, _delivery_rule=False
    )


def preview_prepayment_release(
    session: Session, tenant_id: str, *, document_id: str, reason: str
) -> dict[str, Any]:
    """
    What releasing this order's prepayment would do, recording nothing.

    BUSINESS PURPOSE:
    Show what a company owner's decision to ship a prepayment order before it is paid would release.

    BUSINESS RULE services.prepayment_release_actions.preview.refusals:
    IF the document is not a sales order, refuse with prepayment_release_order_not_found. IF the order has no open delivery promise, refuse with prepayment_release_nothing_open. IF its payment terms require no prepayment, refuse with prepayment_release_not_required. IF an invoice also bills other orders or is attributed ambiguously, refuse with prepayment_release_attribution_unclear. IF the order is paid or already released for its amount, refuse with prepayment_release_nothing_to_release. IF the reason is empty after trimming, refuse with prepayment_release_reason_missing.

    BUSINESS RULE services.prepayment_release_actions.preview.result:
    Return the order, the reason, the payment basis (required, received and remaining in the order's currency) and the blockers the release lifts.
    """
    from reality.services.fulfillment_readiness import RELEASABLE_BLOCKERS

    order, readiness = _order_payment(session, tenant_id, document_id)
    # reality-rule: services.prepayment_release_actions.preview.refusals
    if not readiness.requires_prepayment:
        raise core.InvalidOperation(code="prepayment_release_not_required")
    if {
        "prepayment_attribution_ambiguous",
        "prepayment_consolidated_invoice_open",
    } & set(readiness.blocker_codes):
        raise core.InvalidOperation(code="prepayment_release_attribution_unclear")
    lifted = sorted(set(readiness.blocker_codes) & RELEASABLE_BLOCKERS)
    if not lifted:
        raise core.InvalidOperation(code="prepayment_release_nothing_to_release")
    stated = str(reason or "").strip()
    if not stated:
        raise core.InvalidOperation(code="prepayment_release_reason_missing")
    # reality-rule: services.prepayment_release_actions.preview.result
    return {
        "document_id": order.id,
        "number": order.number,
        "party_id": order.party_id,
        "reason": stated,
        "lifts": lifted,
        "payment": {
            "currency": readiness.currency,
            "required": str(readiness.required_amount),
            "received": str(readiness.received_amount),
            "remaining": str(readiness.remaining_amount),
        },
    }


def release_prepayment(
    session: Session,
    tenant_id: str,
    *,
    document_id: str,
    reason: str,
    action_id: str | None = None,
    _commit: bool = True,
) -> dict[str, Any]:
    """
    Record an owner's release of one order's prepayment; callers check the owner.

    BUSINESS PURPOSE:
    Let a company owner ship one prepayment order before it is paid, with a stated reason.

    BUSINESS RULE services.prepayment_release_actions.release.permission:
    Require the business permission for 'release_prepayment' before changing company records.

    BUSINESS RULE services.prepayment_release_actions.release.check:
    Run the shared preview check and use its normalized inputs.

    BUSINESS RULE services.prepayment_release_actions.release.effect:
    Append a prepayment release covering the order's stated gross amount in its currency, with the reason and the confirming action, and record order.prepayment_released for the order.

    BUSINESS RULE services.prepayment_release_actions.release.result:
    Return the order, the release, the reason and the covered amount.
    """
    # reality-rule: services.prepayment_release_actions.release.permission
    core._require_business_mutation(session, tenant_id, "release_prepayment")
    # reality-rule: services.prepayment_release_actions.release.check
    preview = preview_prepayment_release(
        session, tenant_id, document_id=document_id, reason=reason
    )
    # reality-rule: services.prepayment_release_actions.release.effect
    release = PrepaymentRelease(
        id=core.uid("ppr"),
        tenant_id=tenant_id,
        document_id=document_id,
        covered_amount=preview["payment"]["required"],
        currency=preview["payment"]["currency"],
        reason=preview["reason"],
        action_id=action_id,
    )
    session.add(release)
    session.flush()
    from reality.services.core import emit_business_event

    emit_business_event(
        session,
        tenant_id,
        "order.prepayment_released",
        "document",
        document_id,
        {
            "release_id": release.id,
            "document_id": document_id,
            "reason": preview["reason"],
            "covered_amount": preview["payment"]["required"],
            "received_amount": preview["payment"]["received"],
            "currency": preview["payment"]["currency"],
            "lifts": preview["lifts"],
        },
        action_id=action_id,
        correlation_id=action_id,
    )
    if _commit:
        session.commit()
    else:
        session.flush()
    # reality-rule: services.prepayment_release_actions.release.result
    return {
        "document_id": document_id,
        "release_id": release.id,
        "reason": preview["reason"],
        "covered_amount": preview["payment"]["required"],
        "currency": preview["payment"]["currency"],
    }


def review_prepayment_release(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> dict[str, Any]:
    if set(arguments) != FIELDS:
        raise core.InvalidOperation(code="prepayment_release_fields_invalid")
    intent = {key: str(arguments[key]) for key in sorted(FIELDS)}
    state = json.loads(
        _json(preview_prepayment_release(session, tenant_id, **intent))
    )
    # What arrives meanwhile is shown, not pinned: a payment must not make the
    # owner review again. The amount the release covers is pinned: an order
    # raised after the review is a different decision.
    pinned = {
        "document_id": state["document_id"],
        "required": state["payment"]["required"],
        "currency": state["payment"]["currency"],
    }
    return {
        "version": 1,
        "tool": "prepayment_release",
        "intent": intent,
        "state": state,
        "effect": {
            "document_id": state["document_id"],
            "covered_amount": state["payment"]["required"],
            "currency": state["payment"]["currency"],
            "money_moves": False,
            "owner_required": True,
        },
        "token": hashlib.sha256(
            _json([tenant_id, "prepayment_release", intent, pinned]).encode()
        ).hexdigest(),
    }


def assert_no_unresolved_prepayment_release(
    session: Session, tenant_id: str, arguments: dict[str, Any], exclude: str | None
) -> None:
    for proposal in session.scalars(
        select(ChangeProposal).where(
            ChangeProposal.tenant_id == tenant_id,
            ChangeProposal.type == "tool:prepayment_release",
            ChangeProposal.status == "executing",
        )
    ):
        saved = json.loads(proposal.input)
        if proposal.id != exclude and saved.get("document_id") == arguments.get(
            "document_id"
        ):
            raise core.InvalidOperation(code="prepayment_release_unresolved")


def prepayment_release_detail(
    session: Session, tenant_id: str, proposal: ChangeProposal
) -> dict[str, Any]:
    review = json.loads(proposal.input).get("_delivery_review")
    result: dict[str, Any] = {
        "id": proposal.id,
        "tool": "prepayment_release",
        "status": proposal.status,
        "review": review,
        "receipt": json.loads(proposal.output)
        if proposal.status == "executed"
        else None,
        "verification": "pending" if proposal.status == "proposed" else "unresolved",
        "links": [],
        "observation": None,
        "observation_error": None,
    }
    intent = review["intent"] if review else {}
    event = session.scalar(
        select(BusinessEvent)
        .where(
            BusinessEvent.tenant_id == tenant_id,
            BusinessEvent.event_type == "order.prepayment_released",
            BusinessEvent.action_id == proposal.id,
        )
        .order_by(BusinessEvent.id)
        .limit(1)
    )
    payload = json.loads(event.payload) if event is not None else None
    if payload and payload.get("document_id") == intent.get("document_id"):
        receipt = {
            "document_id": payload["document_id"],
            "release_id": payload["release_id"],
            "reason": payload["reason"],
            "covered_amount": payload["covered_amount"],
            "currency": payload["currency"],
        }
        if proposal.status != "executed" or result["receipt"] == receipt:
            result.update(
                verification="verified"
                if proposal.status == "executed"
                else "recorded_unsettled",
                recorded_receipt=receipt,
                links=[
                    {"kind": "document", "id": receipt["document_id"]},
                    {"kind": "prepayment_release", "id": receipt["release_id"]},
                ],
                observation=receipt,
            )
    result["lifecycle"] = proposal.status
    result["recorded_effect"] = result.get("recorded_receipt")
    result["current_observation"] = result["observation"]
    if proposal.status == "proposed":
        result["remaining_work"] = ["An owner confirms the unchanged reviewed release."]
        result["safe_next_action"] = "confirm"
    elif result["verification"] == "recorded_unsettled":
        result["remaining_work"] = [
            "Settle the proposal receipt from the exact recorded effect."
        ]
        result["safe_next_action"] = "reconcile"
    elif result["verification"] == "verified":
        result["remaining_work"] = []
        result["safe_next_action"] = "none"
    else:
        result["remaining_work"] = [
            "Reconcile the proposal against the order's releases; do not retry blindly."
        ]
        result["safe_next_action"] = "reconcile"
    return result



def _prepayment_view(
    session: Session, tenant_id: str, commitment: Commitment
) -> dict[str, Any] | None:
    """The payment gate of a customer promise's order, for the delivery case.

    Read only for an open promise whose order requires prepayment, so other cases
    pay nothing for it.
    """
    from reality.db.core import PaymentTerm
    from reality.services.fulfillment_readiness import (
        PAYMENT_BLOCKERS,
        RELEASABLE_BLOCKERS,
        fulfillment_readiness,
    )

    if (
        commitment.type != "customer_delivery"
        or commitment.status != "open"
        or not commitment.document_id
    ):
        return None
    requires = session.scalar(
        select(PaymentTerm.requires_prepayment)
        .join(
            Document,
            (Document.tenant_id == PaymentTerm.tenant_id)
            & (Document.payment_term_id == PaymentTerm.id),
        )
        .where(
            Document.tenant_id == tenant_id,
            Document.id == commitment.document_id,
            Document.type == "sales_order",
        )
    )
    if not requires:
        return None
    readiness = fulfillment_readiness(
        session, tenant_id, commitment.id, _delivery_rule=False
    )
    blockers = [code for code in readiness.blocker_codes if code in PAYMENT_BLOCKERS]
    return {
        "currency": readiness.currency,
        "required": str(readiness.required_amount),
        "received": str(readiness.received_amount),
        "remaining": str(readiness.remaining_amount),
        "blockers": blockers,
        # An owner may release it only when the order is simply not (fully) paid.
        "owner_release": bool(blockers) and set(blockers) <= RELEASABLE_BLOCKERS,
        "release_id": readiness.prepayment_release_id,
    }
