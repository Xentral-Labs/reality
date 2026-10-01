"""Releasing an order held for credit: an owner's decision with a reason (spec 298).

A credit hold is released per order, only by a company owner and only with a
stated reason. Only the order's credit holds are lifted; any other hold on its
promises stays. The person comes from the decision that confirmed the release;
the reason travels with the release event.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from reality.db.core import BusinessEvent, ChangeProposal, Commitment, Document
from reality.services import core
from reality.services.credit_exposure import active_credit_holds, credit_exposure

CREDIT_HOLD_TOOLS = {"credit_hold_release"}
FIELDS = {"document_id", "reason"}


def _json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, default=str, separators=(",", ":"))


def _order_holds(
    session: Session, tenant_id: str, document_id: str
) -> tuple[Document, list[Any]]:
    order = core._tenant_record(session, Document, tenant_id, document_id)
    if order.type != "sales_order":
        raise core.InvalidOperation(code="credit_hold_not_found")
    commitment_ids = list(
        session.scalars(
            select(Commitment.id).where(
                Commitment.tenant_id == tenant_id, Commitment.document_id == order.id
            )
        )
    )
    return order, active_credit_holds(session, tenant_id, commitment_ids)


def preview_credit_release(
    session: Session, tenant_id: str, *, document_id: str, reason: str
) -> dict[str, Any]:
    """What releasing this order's credit holds would do, recording nothing."""
    order, holds = _order_holds(session, tenant_id, document_id)
    if not holds:
        raise core.InvalidOperation(code="credit_hold_not_found")
    stated = str(reason or "").strip()
    if not stated:
        raise core.InvalidOperation(code="credit_hold_release_reason_missing")
    exposure = credit_exposure(session, tenant_id, order.party_id)
    return {
        "document_id": order.id,
        "number": order.number,
        "party_id": order.party_id,
        "reason": stated,
        "holds": [
            {"id": hold.id, "commitment_id": hold.commitment_id, "note": hold.note}
            for hold in holds
        ],
        "exposure": {
            "currency": exposure["currency"],
            "credit_limit": str(exposure["credit_limit"]),
            "exposure": str(exposure["exposure"]),
            "excess": str(exposure["excess"]),
            "overdue": str(exposure["overdue_invoices"]["amount"]),
        },
    }


def release_credit_holds(
    session: Session,
    tenant_id: str,
    *,
    document_id: str,
    reason: str,
    action_id: str | None = None,
    _commit: bool = True,
) -> dict[str, Any]:
    """Lift the order's credit holds; callers check that an owner confirmed."""
    core._require_business_mutation(session, tenant_id, "release_credit_hold")
    preview = preview_credit_release(
        session, tenant_id, document_id=document_id, reason=reason
    )
    released_at = core.now()
    _, holds = _order_holds(session, tenant_id, document_id)
    by_commitment: dict[str, list[str]] = {}
    for hold in holds:
        hold.released_at = released_at
        by_commitment.setdefault(hold.commitment_id, []).append(hold.id)
    for commitment_id, hold_ids in by_commitment.items():
        core.emit_business_event(
            session,
            tenant_id,
            "commitment.hold_released",
            "commitment",
            commitment_id,
            {
                "hold_ids": hold_ids,
                "reason_code": "credit_check",
                "reason": preview["reason"],
                "document_id": document_id,
            },
            action_id=action_id,
            correlation_id=action_id,
        )
    if _commit:
        session.commit()
    else:
        session.flush()
    return {
        "document_id": document_id,
        "hold_ids": sorted(hold.id for hold in holds),
        "reason": preview["reason"],
    }


def review_credit_release(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> dict[str, Any]:
    if set(arguments) != FIELDS:
        raise core.InvalidOperation(code="credit_hold_release_fields_invalid")
    intent = {key: str(arguments[key]) for key in sorted(FIELDS)}
    state = json.loads(_json(preview_credit_release(session, tenant_id, **intent)))
    # The exposure is shown, not pinned: a payment arriving meanwhile must not
    # make the owner review again. The holds are pinned.
    pinned = {"holds": state["holds"], "document_id": state["document_id"]}
    return {
        "version": 1,
        "tool": "credit_hold_release",
        "intent": intent,
        "state": state,
        "effect": {
            "document_id": state["document_id"],
            "holds_released": str(len(state["holds"])),
            "money_moves": False,
            "owner_required": True,
        },
        "token": hashlib.sha256(
            _json([tenant_id, "credit_hold_release", intent, pinned]).encode()
        ).hexdigest(),
    }


def assert_no_unresolved_credit_release(
    session: Session, tenant_id: str, arguments: dict[str, Any], exclude: str | None
) -> None:
    for proposal in session.scalars(
        select(ChangeProposal).where(
            ChangeProposal.tenant_id == tenant_id,
            ChangeProposal.type == "tool:credit_hold_release",
            ChangeProposal.status == "executing",
        )
    ):
        saved = json.loads(proposal.input)
        if proposal.id != exclude and saved.get("document_id") == arguments.get(
            "document_id"
        ):
            raise core.InvalidOperation(code="credit_hold_release_unresolved")


def credit_release_detail(
    session: Session, tenant_id: str, proposal: ChangeProposal
) -> dict[str, Any]:
    review = json.loads(proposal.input).get("_delivery_review")
    result: dict[str, Any] = {
        "id": proposal.id,
        "tool": "credit_hold_release",
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
    events = list(
        session.scalars(
            select(BusinessEvent)
            .where(
                BusinessEvent.tenant_id == tenant_id,
                BusinessEvent.event_type == "commitment.hold_released",
                BusinessEvent.action_id == proposal.id,
            )
            .order_by(BusinessEvent.id)
        )
    )
    payloads = [json.loads(event.payload) for event in events]
    if payloads and all(
        payload.get("document_id") == intent.get("document_id")
        and payload.get("reason_code") == "credit_check"
        for payload in payloads
    ):
        receipt = {
            "document_id": intent["document_id"],
            "hold_ids": sorted(
                hold_id for payload in payloads for hold_id in payload["hold_ids"]
            ),
            "reason": payloads[0]["reason"],
        }
        if proposal.status != "executed" or result["receipt"] == receipt:
            result.update(
                verification="verified"
                if proposal.status == "executed"
                else "recorded_unsettled",
                recorded_receipt=receipt,
                links=[
                    {"kind": "document", "id": intent["document_id"]},
                    *[
                        {"kind": "commitment_hold", "id": hold_id}
                        for hold_id in receipt["hold_ids"]
                    ],
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
            "Reconcile the proposal against the order's holds; do not retry blindly."
        ]
        result["safe_next_action"] = "reconcile"
    return result
