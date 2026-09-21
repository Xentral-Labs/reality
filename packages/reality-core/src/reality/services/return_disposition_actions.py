"""State-bound review and verification for customer-return disposition."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from reality.db.core import ChangeProposal, Movement, SourceRecord
from reality.services import core
from reality.services.return_dispositions import (
    preview_return_disposition,
    return_disposition_summary,
)

RETURN_DISPOSITION_TOOLS = {"return_disposition"}


def _json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, default=str, separators=(",", ":"))


def review_return_disposition(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> dict[str, Any]:
    allowed = {
        "return_movement_id",
        "disposition",
        "quantity",
        "destination_location_id",
        "reason",
    }
    if set(arguments) - allowed or not {
        "return_movement_id",
        "disposition",
        "quantity",
    } <= set(arguments):
        raise core.InvalidOperation(
            "Return disposition fields are incomplete or unsupported."
        )
    intent = {key: value for key, value in arguments.items() if value is not None}
    state = json.loads(_json(preview_return_disposition(session, tenant_id, **intent)))
    normalized = {
        "return_movement_id": state["before"]["return_movement_id"],
        "disposition": state["disposition"],
        "quantity": str(state["quantity"]),
        **(
            {"destination_location_id": intent["destination_location_id"]}
            if intent.get("destination_location_id")
            else {}
        ),
        **({"reason": intent["reason"]} if intent.get("reason") else {}),
    }
    return {
        "version": 1,
        "tool": "return_disposition",
        "intent": normalized,
        "state": state,
        "effect": {
            "disposition": state["disposition"],
            "resolved": str(state["quantity"]),
            "unresolved_after": str(state["after"]["unresolved"]),
        },
        "token": hashlib.sha256(
            _json([tenant_id, "return_disposition", normalized, state]).encode()
        ).hexdigest(),
    }


def assert_no_unresolved_return_disposition(
    session: Session,
    tenant_id: str,
    arguments: dict[str, Any],
    exclude: str | None,
) -> None:
    for proposal in session.scalars(
        select(ChangeProposal).where(
            ChangeProposal.tenant_id == tenant_id,
            ChangeProposal.type == "tool:return_disposition",
            ChangeProposal.status == "executing",
        )
    ):
        saved = json.loads(proposal.input)
        if proposal.id != exclude and saved.get("return_movement_id") == arguments.get(
            "return_movement_id"
        ):
            raise core.InvalidOperation(
                "An earlier return disposition is unresolved. Check its outcome first."
            )


def return_disposition_detail(
    session: Session, tenant_id: str, proposal: ChangeProposal
) -> dict[str, Any]:
    review = json.loads(proposal.input).get("_delivery_review")
    result = {
        "id": proposal.id,
        "tool": "return_disposition",
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
            SourceRecord.source_type == "return_disposition",
            SourceRecord.external_id == proposal.id,
        )
    )
    movement = (
        session.scalar(
            select(Movement).where(
                Movement.tenant_id == tenant_id,
                Movement.source_record_id == source.id,
            )
        )
        if source
        else None
    )
    if movement and review:
        receipt = {"movement_id": movement.id, "source_record_id": source.id}
        if proposal.status != "executed" or result["receipt"] == receipt:
            result.update(
                verification="verified"
                if proposal.status == "executed"
                else "recorded_unsettled",
                recorded_receipt=receipt,
                links=[
                    {"kind": "movement", "id": movement.id},
                    {"kind": "source_record", "id": source.id},
                ],
                observation=return_disposition_summary(
                    session, tenant_id, review["intent"]["return_movement_id"]
                ),
            )
    return result
