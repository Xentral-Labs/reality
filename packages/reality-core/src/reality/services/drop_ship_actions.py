"""State-bound review and verification for a drop shipment (spec 337)."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from reality.db.core import ChangeProposal, Movement, SourceRecord
from reality.services import core
from reality.services.drop_shipping import (
    SOURCE_TYPE,
    drop_shipments,
    preview_drop_shipment,
)

DROP_SHIP_TOOLS = {"drop_shipment_record"}
FIELDS = {
    "supplier_commitment_id",
    "customer_commitment_id",
    "quantity",
    "occurred_at",
    "carrier",
    "tracking_number",
}
REQUIRED = {"supplier_commitment_id", "quantity"}


def _json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, default=str, separators=(",", ":"))


def review_drop_shipment(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> dict[str, Any]:
    if set(arguments) - FIELDS or not REQUIRED <= set(arguments):
        raise core.InvalidOperation(code="drop_ship_fields_invalid")
    intent = {key: value for key, value in arguments.items() if value not in (None, "")}
    state = json.loads(_json(preview_drop_shipment(session, tenant_id, **intent)))
    # The reviewed time is the one recorded: a drop shipment stated without a
    # time happened when it was reviewed, not when it is confirmed.
    normalized = {
        "supplier_commitment_id": state["supplier_commitment_id"],
        "customer_commitment_id": state["customer_commitment_id"],
        "quantity": state["quantity"],
        "occurred_at": state["occurred_at"],
        **({"carrier": state["carrier"]} if state["carrier"] else {}),
        **(
            {"tracking_number": state["tracking_number"]}
            if state["tracking_number"]
            else {}
        ),
    }
    return {
        "version": 1,
        "tool": "drop_shipment_record",
        "intent": normalized,
        "state": state,
        "effect": {
            "keeps": [state["supplier_commitment_id"], state["customer_commitment_id"]],
            "quantity": state["quantity"],
            "stock_moves": False,
            "money_moves": False,
            "creates": ["shipment", "movement", "source_record"],
        },
        "token": hashlib.sha256(
            _json([tenant_id, "drop_shipment_record", normalized, state]).encode()
        ).hexdigest(),
    }


def assert_no_unresolved_drop_shipment(
    session: Session,
    tenant_id: str,
    arguments: dict[str, Any],
    exclude: str | None,
) -> None:
    for proposal in session.scalars(
        select(ChangeProposal).where(
            ChangeProposal.tenant_id == tenant_id,
            ChangeProposal.type == "tool:drop_shipment_record",
            ChangeProposal.status == "executing",
        )
    ):
        saved = json.loads(proposal.input)
        if proposal.id != exclude and saved.get(
            "supplier_commitment_id"
        ) == arguments.get("supplier_commitment_id"):
            raise core.InvalidOperation(code="drop_ship_unresolved")


def drop_shipment_proposal_detail(
    session: Session, tenant_id: str, proposal: ChangeProposal
) -> dict[str, Any]:
    review = json.loads(proposal.input).get("_delivery_review")
    result = {
        "id": proposal.id,
        "tool": "drop_shipment_record",
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
    intent = review["intent"] if review else {}
    movements = (
        {
            row.type: row
            for row in session.scalars(
                select(Movement).where(
                    Movement.tenant_id == tenant_id,
                    Movement.source_record_id == source.id,
                )
            )
        }
        if source
        else {}
    )
    received, shipped = movements.get("receipt"), movements.get("shipment")
    if (
        received
        and shipped
        and received.commitment_id == intent.get("supplier_commitment_id")
        and shipped.commitment_id == intent.get("customer_commitment_id")
    ):
        observation = drop_shipments(
            session, tenant_id, commitment_id=shipped.commitment_id
        )
        shipment_id = next(
            (
                row["shipment_id"]
                for row in observation["drop_shipments"]
                if row["source_record_id"] == source.id
            ),
            None,
        )
        receipt = {
            "shipment_id": shipment_id,
            "receipt_movement_id": received.id,
            "shipment_movement_id": shipped.id,
            "source_record_id": source.id,
        }
        if proposal.status != "executed" or result["receipt"] == receipt:
            result.update(
                verification="verified"
                if proposal.status == "executed"
                else "recorded_unsettled",
                recorded_receipt=receipt,
                links=[
                    *([{"kind": "shipment", "id": shipment_id}] if shipment_id else []),
                    {"kind": "commitment", "id": received.commitment_id},
                    {"kind": "commitment", "id": shipped.commitment_id},
                    {"kind": "movement", "id": received.id},
                    {"kind": "movement", "id": shipped.id},
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
            "Reconcile exact tenant, proposal, and promise identity evidence; do not retry blindly."
        ]
        result["safe_next_action"] = "reconcile"
    return result
