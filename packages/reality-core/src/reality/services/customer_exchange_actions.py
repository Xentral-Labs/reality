"""State-bound review and verification for a customer exchange (spec 293)."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from reality.db.core import ChangeProposal, CustomerExchange, SourceRecord
from reality.services import core
from reality.services.customer_exchanges import (
    customer_exchange_detail,
    preview_customer_exchange,
)

CUSTOMER_EXCHANGE_TOOLS = {"customer_exchange_record"}
FIELDS = {
    "return_movement_id",
    "return_announcement_id",
    "quantity",
    "replacement_item_id",
    "replacement_quantity",
    "location_id",
    "due_at",
    "reason",
}
REQUIRED = {"quantity", "replacement_item_id", "replacement_quantity", "reason"}


def _json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, default=str, separators=(",", ":"))


def review_customer_exchange(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> dict[str, Any]:
    if set(arguments) - FIELDS or not REQUIRED <= set(arguments):
        raise core.InvalidOperation(code="customer_exchange_fields_invalid")
    intent = {key: value for key, value in arguments.items() if value is not None}
    state = json.loads(_json(preview_customer_exchange(session, tenant_id, **intent)))
    normalized = {
        **intent,
        "quantity": state["exchanged_quantity"],
        "replacement_quantity": state["replacement"]["quantity"],
        "location_id": state["replacement"]["location_id"],
        "reason": state["reason"],
    }
    return {
        "version": 1,
        "tool": "customer_exchange_record",
        "intent": normalized,
        "state": state,
        "effect": {
            "returned_delivery_id": state["returned_delivery_id"],
            "return": state["return"],
            "exchanged_quantity": state["exchanged_quantity"],
            "replacement": {
                "item_id": state["replacement"]["item_id"],
                "quantity": state["replacement"]["quantity"],
                "location_id": state["replacement"]["location_id"],
            },
            "money_moves": False,
            "creates": ["customer_exchange", "commitment"],
        },
        "token": hashlib.sha256(
            _json([tenant_id, "customer_exchange_record", normalized, state]).encode()
        ).hexdigest(),
    }


def assert_no_unresolved_customer_exchange(
    session: Session,
    tenant_id: str,
    arguments: dict[str, Any],
    exclude: str | None,
) -> None:
    returned = (
        arguments.get("return_movement_id"),
        arguments.get("return_announcement_id"),
    )
    for proposal in session.scalars(
        select(ChangeProposal).where(
            ChangeProposal.tenant_id == tenant_id,
            ChangeProposal.type == "tool:customer_exchange_record",
            ChangeProposal.status == "executing",
        )
    ):
        saved = json.loads(proposal.input)
        if (
            proposal.id != exclude
            and (
                saved.get("return_movement_id"),
                saved.get("return_announcement_id"),
            )
            == returned
        ):
            raise core.InvalidOperation(code="customer_exchange_unresolved")


def customer_exchange_proposal_detail(
    session: Session, tenant_id: str, proposal: ChangeProposal
) -> dict[str, Any]:
    review = json.loads(proposal.input).get("_delivery_review")
    result = {
        "id": proposal.id,
        "tool": "customer_exchange_record",
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
            SourceRecord.source_type == "customer_exchange",
            SourceRecord.external_id == proposal.id,
        )
    )
    exchange = (
        session.scalar(
            select(CustomerExchange).where(
                CustomerExchange.tenant_id == tenant_id,
                CustomerExchange.source_record_id == source.id,
            )
        )
        if source
        else None
    )
    intent = review["intent"] if review else {}
    identity_matches = bool(
        exchange
        and review
        and exchange.return_movement_id == intent.get("return_movement_id")
        and exchange.return_announcement_id == intent.get("return_announcement_id")
        and core.decimal(exchange.quantity) == core.decimal(intent["quantity"])
    )
    if exchange and identity_matches:
        receipt = {
            "exchange_id": exchange.id,
            "replacement_commitment_id": exchange.replacement_commitment_id,
            "source_record_id": source.id,
        }
        if proposal.status != "executed" or result["receipt"] == receipt:
            observation = customer_exchange_detail(
                session, tenant_id, exchange_id=exchange.id
            )
            result.update(
                verification="verified"
                if proposal.status == "executed"
                else "recorded_unsettled",
                recorded_receipt=receipt,
                links=[
                    {"kind": "customer_exchange", "id": exchange.id},
                    {"kind": "commitment", "id": exchange.replacement_commitment_id},
                    {"kind": "commitment", "id": observation["returned_delivery_id"]},
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
            "Reconcile exact tenant, proposal, and return identity evidence; do not retry blindly."
        ]
        result["safe_next_action"] = "reconcile"
    return result
