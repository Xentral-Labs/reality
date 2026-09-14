"""Reviewed customer-wide shipment holds using canonical party hold services."""

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
    Movement,
    PartyHold,
)
from reality.services.core import (
    HOLD_REASONS,
    InvalidOperation,
    NotFound,
    _tenant_record,
    party_hold_snapshot,
)
from reality.services.reference_workspace import reference_detail

CUSTOMER_HOLD_TOOLS = {"party_delivery_hold", "party_delivery_hold_release"}


def _json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, default=str, separators=(",", ":"))


def customer_hold_context(
    session: Session, tenant_id: str, party_id: str
) -> dict[str, Any]:
    session.expire_all()
    party = reference_detail(session, tenant_id, "customer", party_id)
    holds = session.scalars(
        select(PartyHold)
        .where(
            PartyHold.tenant_id == tenant_id,
            PartyHold.party_id == party_id,
            PartyHold.hold_type == "delivery",
            PartyHold.released_at.is_(None),
        )
        .order_by(PartyHold.id)
    )
    return {
        "party": {
            key: party[key] for key in ("id", "name", "type", "roles", "is_active")
        },
        "holds": [party_hold_snapshot(hold) for hold in holds],
        "reasons": sorted(HOLD_REASONS),
    }


def review_customer_hold(
    session: Session, tenant_id: str, tool: str, arguments: dict[str, Any]
) -> dict[str, Any]:
    placing = tool == "party_delivery_hold"
    allowed = {"party_id", "reason_code", "note"} if placing else {"party_id"}
    if tool not in CUSTOMER_HOLD_TOOLS or set(arguments) - allowed:
        raise InvalidOperation("Check the customer hold fields.")
    if not isinstance(arguments.get("party_id"), str) or not arguments["party_id"]:
        raise InvalidOperation("Choose a customer.")
    intent = {"party_id": arguments["party_id"]}
    if placing:
        reason = arguments.get("reason_code")
        if not isinstance(reason, str) or reason not in HOLD_REASONS:
            raise InvalidOperation("Unsupported hold reason.")
        note = arguments.get("note", "")
        if not isinstance(note, str):
            raise InvalidOperation("A hold note must be text.")
        intent.update(reason_code=reason, note=note.strip())
    context = customer_hold_context(session, tenant_id, intent["party_id"])
    state = {"party": context["party"], "holds": context["holds"]}
    if placing and state["holds"]:
        raise InvalidOperation("This customer already has a delivery hold.")
    if not placing and not state["holds"]:
        raise InvalidOperation("This customer has no active delivery hold.")
    return {
        "version": 1,
        "tool": tool,
        "intent": intent,
        "state": state,
        "effect": {"holds_set": "1"}
        if placing
        else {"holds_released": str(len(state["holds"]))},
        "token": hashlib.sha256(
            _json([tenant_id, tool, intent, state]).encode()
        ).hexdigest(),
    }


def _parties(
    session: Session, tenant_id: str, tool: str, arguments: dict[str, Any]
) -> set[str]:
    if tool in CUSTOMER_HOLD_TOOLS:
        return {str(arguments.get("party_id", ""))}
    values = []
    if tool == "movement_create" and arguments.get("movement_type") == "shipment":
        values = [arguments]
    elif tool == "movement_correct":
        movement = _tenant_record(
            session, Movement, tenant_id, arguments.get("movement_id", "")
        )
        if movement.type == "shipment":
            values.append({"commitment_id": movement.commitment_id})
        replacement = arguments.get("replacement") or {}
        if replacement.get("type") == "shipment":
            values.append(replacement)
    parties = set()
    for value in values:
        if value.get("commitment_id"):
            commitment = _tenant_record(
                session, Commitment, tenant_id, value["commitment_id"]
            )
            if commitment.type == "customer_delivery":
                parties.add(commitment.to_party_id)
    return parties


def assert_customer_hold_overlap(
    session: Session,
    tenant_id: str,
    tool: str,
    arguments: dict[str, Any],
    exclude: str | None,
) -> None:
    relevant = {*CUSTOMER_HOLD_TOOLS, "movement_create", "movement_correct"}
    if tool not in relevant:
        return
    statement = select(ChangeProposal).where(
        ChangeProposal.tenant_id == tenant_id,
        ChangeProposal.status == "executing",
        ChangeProposal.type.in_([f"tool:{name}" for name in relevant]),
    )
    if tool not in CUSTOMER_HOLD_TOOLS:
        statement = statement.where(
            ChangeProposal.type.in_([f"tool:{name}" for name in CUSTOMER_HOLD_TOOLS])
        )
    current = None
    for proposal in session.scalars(statement):
        if proposal.id == exclude:
            continue
        if current is None:
            current = _parties(session, tenant_id, tool, arguments)
        if current & _parties(
            session,
            tenant_id,
            proposal.type.removeprefix("tool:"),
            json.loads(proposal.input),
        ):
            raise InvalidOperation(
                "An action affecting this customer’s shipment hold is unresolved. Check its outcome first."
            )


def customer_hold_detail(
    session: Session, tenant_id: str, proposal: ChangeProposal
) -> dict[str, Any]:
    saved = json.loads(proposal.input)
    review = saved.get("_delivery_review")
    intent = {key: value for key, value in saved.items() if key != "_delivery_review"}
    tool = proposal.type.removeprefix("tool:")
    result = {
        "id": proposal.id,
        "tool": tool,
        "status": proposal.status,
        "review": review,
        "intent": intent,
        "receipt": json.loads(proposal.output)
        if proposal.status == "executed"
        else None,
        "verification": "pending" if proposal.status == "proposed" else "unresolved",
        "links": [],
        "observation": None,
        "observation_error": None,
    }
    if proposal.status not in {"executing", "executed"} or not review:
        return result
    placing = tool == "party_delivery_hold"
    events = list(
        session.scalars(
            select(BusinessEvent)
            .where(
                BusinessEvent.tenant_id == tenant_id,
                BusinessEvent.action_id == proposal.id,
                BusinessEvent.event_type
                == (
                    "party.delivery_hold_placed"
                    if placing
                    else "party.delivery_hold_released"
                ),
            )
            .limit(2)
        )
    )
    if len(events) != 1:
        return result
    event = events[0]
    if (
        event.subject_type != "party"
        or event.subject_id != intent["party_id"]
        or event.correlation_id != proposal.id
        or event.source_record_id is not None
    ):
        return result
    payload = json.loads(event.payload)
    ids = [payload.get("hold_id")] if placing else payload.get("hold_ids", [])
    if (
        not isinstance(ids, list)
        or not ids
        or not all(isinstance(value, str) for value in ids)
        or len(set(ids)) != len(ids)
    ):
        return result
    holds = list(
        session.scalars(
            select(PartyHold)
            .where(
                PartyHold.tenant_id == tenant_id,
                PartyHold.party_id == intent["party_id"],
                PartyHold.hold_type == "delivery",
                PartyHold.id.in_(ids),
            )
            .order_by(PartyHold.id)
            .execution_options(populate_existing=True)
        )
    )
    if len(holds) != len(ids):
        return result
    snapshots = [party_hold_snapshot(hold) for hold in holds]
    if placing:
        if (
            len(holds) != 1
            or payload.get("hold") != snapshots[0]
            or holds[0].reason_code != intent["reason_code"]
            or payload.get("reason_code") != intent["reason_code"]
            or holds[0].note != intent.get("note", "")
            or holds[0].created_by != "human"
            or event.occurred_at != holds[0].created_at
        ):
            return result
    elif (
        snapshots != review["state"]["holds"]
        or payload.get("holds") != snapshots
        or any(
            hold.released_at is None
            or str(hold.released_at) != payload.get("released_at")
            or hold.released_at != event.occurred_at
            for hold in holds
        )
    ):
        return result
    receipt = {"records": [{"family": "party_hold", "id": hold.id} for hold in holds]}
    if proposal.status == "executed" and result["receipt"] != receipt:
        return result
    result.update(
        verification="verified"
        if proposal.status == "executed"
        else "recorded_unsettled",
        recorded_receipt=receipt,
        links=[
            {"kind": "party", "id": intent["party_id"]},
            {"kind": "business_event", "id": event.id},
        ],
    )
    try:
        result["observation"] = customer_hold_context(
            session, tenant_id, intent["party_id"]
        )
    except (NotFound, InvalidOperation):
        result["observation_error"] = "Current observation unavailable"
    return result
