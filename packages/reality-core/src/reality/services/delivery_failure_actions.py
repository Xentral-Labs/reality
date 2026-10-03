"""State-bound review and verification for a failed delivery (spec 335)."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from reality.db.core import ChangeProposal, DeliveryFailure, SourceRecord
from reality.services import core
from reality.services.delivery_failures import (
    SOURCE_TYPE,
    delivery_failure_summary,
    preview_delivery_failure,
)

DELIVERY_FAILURE_TOOLS = {"shipment_delivery_failure"}
FIELDS = {
    "shipment_id",
    "kind",
    "reason",
    "occurred_at",
    "claim_party_id",
    "claim_amount",
}
REQUIRED = {"shipment_id", "kind", "reason"}


def _json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, default=str, separators=(",", ":"))


def review_delivery_failure(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> dict[str, Any]:
    if set(arguments) - FIELDS or not REQUIRED <= set(arguments):
        raise core.InvalidOperation(code="delivery_failure_fields_invalid")
    intent = {key: value for key, value in arguments.items() if value not in (None, "")}
    state = json.loads(_json(preview_delivery_failure(session, tenant_id, **intent)))
    # The reviewed time is the one recorded: a failure stated without a time
    # happened when it was reviewed, not when it is confirmed.
    normalized = {
        "shipment_id": state["shipment_id"],
        "kind": state["kind"],
        "reason": state["reason"],
        "occurred_at": state["occurred_at"],
        **(
            {
                "claim_party_id": state["claim"]["party_id"],
                "claim_amount": state["claim"]["amount"],
            }
            if state["claim"]
            else {}
        ),
    }
    return {
        "version": 1,
        "tool": "shipment_delivery_failure",
        "intent": normalized,
        "state": state,
        "effect": {
            "kind": state["kind"],
            "goods": state["goods"],
            "reversed_movements": [m["movement_id"] for m in state["movements"]],
            "reopened": state["promises"],
            "claim": state["claim"],
            "money_moves": bool(state["claim"]),
            "creates": ["delivery_failure", "movement_correction"]
            + (["document", "ledger_entry"] if state["claim"] else []),
        },
        "token": hashlib.sha256(
            _json([tenant_id, "shipment_delivery_failure", normalized, state]).encode()
        ).hexdigest(),
    }


def assert_no_unresolved_delivery_failure(
    session: Session,
    tenant_id: str,
    arguments: dict[str, Any],
    exclude: str | None,
) -> None:
    for proposal in session.scalars(
        select(ChangeProposal).where(
            ChangeProposal.tenant_id == tenant_id,
            ChangeProposal.type == "tool:shipment_delivery_failure",
            ChangeProposal.status == "executing",
        )
    ):
        saved = json.loads(proposal.input)
        if proposal.id != exclude and saved.get("shipment_id") == arguments.get(
            "shipment_id"
        ):
            raise core.InvalidOperation(code="delivery_failure_unresolved")


def delivery_failure_proposal_detail(
    session: Session, tenant_id: str, proposal: ChangeProposal
) -> dict[str, Any]:
    review = json.loads(proposal.input).get("_delivery_review")
    result = {
        "id": proposal.id,
        "tool": "shipment_delivery_failure",
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
    source = session.scalar(
        select(SourceRecord).where(
            SourceRecord.tenant_id == tenant_id,
            SourceRecord.source_system == "manual",
            SourceRecord.source_type == SOURCE_TYPE,
            SourceRecord.external_id == proposal.id,
        )
    )
    failure = (
        session.scalar(
            select(DeliveryFailure).where(
                DeliveryFailure.tenant_id == tenant_id,
                DeliveryFailure.source_record_id == source.id,
            )
        )
        if source
        else None
    )
    intent = review["intent"] if review else {}
    if (
        failure
        and failure.shipment_id == intent.get("shipment_id")
        and failure.kind == intent.get("kind")
    ):
        observation = delivery_failure_summary(
            session, tenant_id, delivery_failure_id=failure.id
        )
        receipt = {
            "delivery_failure_id": failure.id,
            "shipment_id": failure.shipment_id,
            "claim_document_id": observation["claim"]["document_id"]
            if observation["claim"]
            else None,
            "source_record_id": source.id,
        }
        if proposal.status != "executed" or result["receipt"] == receipt:
            result.update(
                verification="verified"
                if proposal.status == "executed"
                else "recorded_unsettled",
                recorded_receipt=receipt,
                links=[
                    {"kind": "delivery_failure", "id": failure.id},
                    {"kind": "shipment", "id": failure.shipment_id},
                    *(
                        [{"kind": "document", "id": receipt["claim_document_id"]}]
                        if receipt["claim_document_id"]
                        else []
                    ),
                    {"kind": "source_record", "id": source.id},
                ],
                observation=observation,
            )
    result["lifecycle"] = proposal.status
    result["recorded_effect"] = result.get("recorded_receipt")
    result["current_observation"] = result["observation"]
    if proposal.status == "proposed":
        result["remaining_work"] = ["Confirm the unchanged reviewed action."]
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
            "Reconcile exact tenant, proposal, and shipment identity evidence; do not retry blindly."
        ]
        result["safe_next_action"] = "reconcile"
    return result
