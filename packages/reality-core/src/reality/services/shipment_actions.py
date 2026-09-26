"""State-bound reviews for physical shipment mutations."""

from __future__ import annotations

import hashlib
import json
from decimal import Decimal
from typing import Any

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from reality.db.core import (
    BusinessEvent,
    ChangeProposal,
    Movement,
    Party,
    PartyRole,
    Reservation,
    Shipment,
    ShipmentEvent,
    ShipmentEventSupersession,
    ShipmentPackage,
    SourceRecord,
)
from reality.domain.shipments import (
    EVENT_TYPES,
    PURPOSES,
    REPORTER_TYPES,
    required_party_role,
    validate_shipment_direction,
)
from reality.services.core import (
    InvalidOperation,
    NotFound,
    _append_movement,
    active_party_delivery_hold,
)
from reality.services.fulfillment_readiness import fulfillment_readiness

SHIPMENT_TOOLS = {
    "shipment_notice_record",
    "shipment_dispatch",
    "shipment_receive",
    "shipment_event_record",
    "shipment_event_supersede",
}

SHIPMENT_EXECUTION_FIELDS = {
    "purpose",
    "counterparty_id",
    "movements",
    "carrier",
    "tracking_number",
    "source_record_id",
    "occurred_at",
}
SHIPMENT_MOVEMENT_FIELDS = {
    "movement_type",
    "item_id",
    "quantity",
    "from_location_id",
    "to_location_id",
    "commitment_id",
    "handling_unit_id",
    "lot_id",
    "serial_unit_id",
    "reason",
}


def is_shipment_action(tool: str) -> bool:
    return tool in SHIPMENT_TOOLS


def _json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, default=str, separators=(",", ":"))


def _owned(session: Session, model, tenant_id: str, record_id: str):
    record = session.scalar(
        select(model).where(model.tenant_id == tenant_id, model.id == record_id)
    )
    if record is None:
        raise NotFound(f"{model.__name__} not found.")
    return record


def _source_state(session: Session, tenant_id: str, source_id: str | None):
    if not source_id:
        return None
    source = _owned(session, SourceRecord, tenant_id, source_id)
    return {
        "id": source.id,
        "version": source.version,
        "payload_hash": source.payload_hash,
    }


def review_shipment_action(
    session: Session, tenant_id: str, tool: str, arguments: dict[str, Any]
) -> dict[str, Any]:
    if tool not in SHIPMENT_TOOLS:
        raise InvalidOperation("This is not a shipment action.")
    if any(key.startswith("_") for key in arguments):
        raise InvalidOperation("Internal review metadata cannot be supplied as intent.")
    intent = json.loads(_json(arguments))
    state: dict[str, Any] = {}
    source_id = intent.get("source_record_id")
    state["source"] = _source_state(session, tenant_id, source_id)

    if tool in {"shipment_notice_record", "shipment_dispatch", "shipment_receive"}:
        direction = intent.get("direction")
        if tool == "shipment_dispatch":
            direction = "outbound"
            intent.pop("direction", None)
        elif tool == "shipment_receive":
            direction = "inbound"
            intent.pop("direction", None)
        purpose = str(intent.get("purpose", ""))
        if purpose not in PURPOSES:
            raise InvalidOperation(
                "Unsupported shipment purpose; permitted values: "
                + ", ".join(sorted(PURPOSES))
                + "."
            )
        try:
            validate_shipment_direction(purpose, str(direction))
        except ValueError as error:
            raise InvalidOperation(str(error)) from error
        party = _owned(
            session, Party, tenant_id, str(intent.get("counterparty_id", ""))
        )
        role = required_party_role(purpose)
        roles = tuple(
            session.scalars(
                select(PartyRole.role)
                .where(PartyRole.tenant_id == tenant_id, PartyRole.party_id == party.id)
                .order_by(PartyRole.role)
            )
        )
        if role not in roles:
            raise InvalidOperation("Counterparty role does not match shipment purpose.")
        state["counterparty"] = {"id": party.id, "roles": roles}
        state["direction"] = direction
        if tool in {"shipment_dispatch", "shipment_receive"}:
            unknown = set(arguments) - SHIPMENT_EXECUTION_FIELDS
            if unknown:
                raise InvalidOperation(
                    "Unsupported shipment field(s): " + ", ".join(sorted(unknown))
                )
            movements = intent.get("movements")
            if not isinstance(movements, list) or not movements:
                raise InvalidOperation(
                    "Packaged execution requires at least one movement."
                )
            expected = PURPOSES[purpose][1]
            previews = []
            for raw in movements:
                if not isinstance(raw, dict):
                    raise InvalidOperation("Each shipment movement must be an object.")
                unknown = set(raw) - SHIPMENT_MOVEMENT_FIELDS
                if unknown:
                    raise InvalidOperation(
                        "Unsupported shipment movement field(s): "
                        + ", ".join(sorted(unknown))
                    )
                movement = dict(raw)
                movement_type = movement.pop("movement_type", expected)
                if movement_type != expected:
                    raise InvalidOperation(
                        "Movement type does not match the shipment purpose; "
                        f"permitted value: {expected}."
                    )
                movement.pop("shipment_package_id", None)
                movement.pop("source_record_id", None)
                preview = _append_movement(
                    session,
                    tenant_id,
                    movement_type=movement_type,
                    source_record_id=source_id,
                    validate_only=True,
                    **movement,
                )
                readiness = None
                if purpose == "customer_delivery":
                    readiness = fulfillment_readiness(
                        session,
                        tenant_id,
                        preview["commitment_id"],
                        proposed_quantity=Decimal(preview["quantity"]),
                    )
                    if not readiness.ship_ready:
                        raise InvalidOperation(
                            "Shipment blocked: "
                            + ", ".join(readiness.blocker_codes)
                            + f" (required {readiness.required_amount} "
                            + f"{readiness.currency}, received "
                            + f"{readiness.received_amount} {readiness.currency})."
                        )
                locations = {
                    value
                    for value in (
                        preview["from_location_id"],
                        preview["to_location_id"],
                    )
                    if value
                }
                relevant_movements = list(
                    session.execute(
                        select(Movement.id, Movement.type, Movement.quantity)
                        .where(
                            Movement.tenant_id == tenant_id,
                            Movement.item_id == preview["item_id"],
                            or_(
                                Movement.commitment_id == preview["commitment_id"],
                                Movement.from_location_id.in_(locations),
                                Movement.to_location_id.in_(locations),
                            ),
                        )
                        .order_by(Movement.id)
                    )
                )
                reservations = list(
                    session.execute(
                        select(
                            Reservation.id,
                            Reservation.quantity,
                            Reservation.status,
                        )
                        .where(
                            Reservation.tenant_id == tenant_id,
                            Reservation.item_id == preview["item_id"],
                            Reservation.location_id.in_(locations),
                        )
                        .order_by(Reservation.id)
                    )
                )
                previews.append(
                    {
                        "type": movement_type,
                        "quantity": str(preview["quantity"]),
                        "relevant_movements": [
                            [row.id, row.type, str(row.quantity)]
                            for row in relevant_movements
                        ],
                        "reservations": [
                            [row.id, str(row.quantity), row.status]
                            for row in reservations
                        ],
                        "delivery_hold": (
                            active_party_delivery_hold(session, tenant_id, party.id)
                            if purpose == "customer_delivery"
                            else False
                        ),
                        "fulfillment_readiness": (
                            readiness.as_dict() if readiness is not None else None
                        ),
                    }
                )
            state["movement_previews"] = previews
    elif tool == "shipment_event_record":
        shipment = _owned(
            session, Shipment, tenant_id, str(intent.get("shipment_id", ""))
        )
        if (
            intent.get("event_type") not in EVENT_TYPES
            or intent.get("reporter_type") not in REPORTER_TYPES
        ):
            raise InvalidOperation("Unsupported shipment event kind or reporter.")
        package_id = intent.get("shipment_package_id")
        if package_id:
            package = _owned(session, ShipmentPackage, tenant_id, package_id)
            if package.shipment_id != shipment.id:
                raise InvalidOperation("Package does not belong to the shipment.")
        state["shipment"] = {
            "id": shipment.id,
            "direction": shipment.direction,
            "purpose": shipment.purpose,
        }
    else:
        event = _owned(
            session, ShipmentEvent, tenant_id, str(intent.get("event_id", ""))
        )
        existing = session.scalar(
            select(ShipmentEventSupersession).where(
                ShipmentEventSupersession.tenant_id == tenant_id,
                ShipmentEventSupersession.superseded_event_id == event.id,
            )
        )
        if existing:
            raise InvalidOperation("Shipment event is already superseded.")
        replacement_id = intent.get("replacement_event_id")
        if replacement_id:
            replacement = _owned(session, ShipmentEvent, tenant_id, replacement_id)
            if (
                replacement.shipment_id != event.shipment_id
                or replacement.id == event.id
            ):
                raise InvalidOperation(
                    "Replacement must be another event on the shipment."
                )
        if not str(intent.get("reason", "")).strip():
            raise InvalidOperation("Shipment event correction reason is required.")
        state["event"] = {
            "id": event.id,
            "shipment_id": event.shipment_id,
            "event_type": event.event_type,
            "reporter_type": event.reporter_type,
        }

    token = hashlib.sha256(
        _json(
            {"tenant": tenant_id, "tool": tool, "intent": intent, "state": state}
        ).encode()
    ).hexdigest()
    return {
        "version": 1,
        "tool": tool,
        "intent": intent,
        "effect": {"shipment_action": tool},
        "state": state,
        "token": token,
    }


def shipment_proposal_detail(
    session: Session, tenant_id: str, proposal: ChangeProposal
) -> dict[str, Any]:
    tool = proposal.type.removeprefix("tool:")
    arguments = json.loads(proposal.input)
    review = arguments.get("_delivery_review")
    result = {
        "id": proposal.id,
        "tool": tool,
        "status": proposal.status,
        "review": review,
        "receipt": json.loads(proposal.output)
        if proposal.status in {"executed", "failed"}
        else None,
        "recorded_receipt": None,
        "verification": (
            "pending"
            if proposal.status == "proposed"
            else "verified_no_effect"
            if proposal.status == "failed"
            else "unresolved"
        ),
        "links": [],
    }
    if proposal.status not in {"executing", "executed"}:
        return result
    event_types = {
        "shipment_notice_record": "shipment.notice_recorded",
        "shipment_dispatch": "shipment.notice_recorded",
        "shipment_receive": "shipment.notice_recorded",
        "shipment_event_record": "shipment.event_recorded",
        "shipment_event_supersede": "shipment.event_superseded",
    }
    events = list(
        session.scalars(
            select(BusinessEvent).where(
                BusinessEvent.tenant_id == tenant_id,
                BusinessEvent.action_id == proposal.id,
                BusinessEvent.event_type == event_types[tool],
            )
        )
    )
    if len(events) != 1:
        return result
    business_event = events[0]
    payload = json.loads(business_event.payload)
    if tool in {"shipment_notice_record", "shipment_dispatch", "shipment_receive"}:
        shipment = _owned(session, Shipment, tenant_id, business_event.subject_id)
        package = _owned(session, ShipmentPackage, tenant_id, payload["package_id"])
        notice = session.scalar(
            select(ShipmentEvent).where(
                ShipmentEvent.tenant_id == tenant_id,
                ShipmentEvent.shipment_id == shipment.id,
                ShipmentEvent.shipment_package_id == package.id,
                ShipmentEvent.event_type == "announced",
            )
        )
        if notice is None:
            return result
        receipt = {
            "shipment_id": shipment.id,
            "package_id": package.id,
            "event_id": notice.id,
        }
        if tool in {"shipment_dispatch", "shipment_receive"}:
            movements = list(
                session.scalars(
                    select(Movement)
                    .where(
                        Movement.tenant_id == tenant_id,
                        Movement.shipment_package_id == package.id,
                    )
                    .order_by(Movement.id)
                )
            )
            if len(movements) != len(arguments.get("movements", [])):
                return result
            receipt = {
                "shipment_id": shipment.id,
                "package_id": package.id,
                "notice_event_id": notice.id,
                "movement_ids": [movement.id for movement in movements],
            }
        result["links"] = [
            {"kind": "shipment", "id": shipment.id},
            {"kind": "shipment_package", "id": package.id},
            {"kind": "business_event", "id": business_event.id},
        ]
    elif tool == "shipment_event_record":
        event = _owned(session, ShipmentEvent, tenant_id, business_event.subject_id)
        receipt = {"shipment_id": event.shipment_id, "event_id": event.id}
        result["links"] = [{"kind": "shipment_event", "id": event.id}]
    else:
        correction = session.scalar(
            select(ShipmentEventSupersession).where(
                ShipmentEventSupersession.tenant_id == tenant_id,
                ShipmentEventSupersession.superseded_event_id
                == business_event.subject_id,
            )
        )
        if correction is None:
            return result
        receipt = {
            "event_id": correction.superseded_event_id,
            "supersession_id": correction.id,
        }
        result["links"] = [{"kind": "shipment_event_supersession", "id": correction.id}]
    result["recorded_receipt"] = receipt
    if proposal.status == "executing":
        result["verification"] = "recorded_unsettled"
    elif result["receipt"] == receipt:
        result["verification"] = "verified"
    return result
