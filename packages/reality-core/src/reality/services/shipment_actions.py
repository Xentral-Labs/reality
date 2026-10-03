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
    # Spec 312: a customer pickup and who collected.
    "delivery_mode",
    "collected_by",
    # Spec 334: the planned delivery this dispatch executes.
    "outbound_delivery_id",
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
    # Spec 301: a receipt may state the purchase unit.
    "unit",
    # Spec 304: a receipt may hold back part of what it brings in.
    "blocked_quantity",
    "block_reason",
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
        raise NotFound(code="record_not_found", values={"record": model.__name__})
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
        raise InvalidOperation(code="shipment_action_not_shipment")
    if any(key.startswith("_") for key in arguments):
        raise InvalidOperation(code="review_metadata_in_intent")
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
                code="shipment_purpose_unsupported",
                values={"values": ", ".join(sorted(PURPOSES))},
            )
        try:
            validate_shipment_direction(purpose, str(direction))
        except ValueError as error:
            raise InvalidOperation.from_refusal(error) from error
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
            raise InvalidOperation(code="shipment_counterparty_role_mismatch")
        state["counterparty"] = {"id": party.id, "roles": roles}
        state["direction"] = direction
        # Spec 312: the review refuses what the confirmation would refuse.
        from reality.services.shipments import (
            _check_moved_at,
            _check_stock_at_moved_time,
            _delivery_mode,
        )

        _delivery_mode(
            purpose,
            intent.get("carrier"),
            intent.get("tracking_number"),
            intent.get("delivery_mode"),
            intent.get("collected_by"),
        )
        _check_moved_at(intent.get("occurred_at"))
        if tool in {"shipment_dispatch", "shipment_receive"}:
            _check_stock_at_moved_time(
                session, tenant_id, intent.get("movements") or [], intent.get("occurred_at")
            )
        if tool in {"shipment_dispatch", "shipment_receive"}:
            unknown = set(arguments) - SHIPMENT_EXECUTION_FIELDS
            if unknown:
                raise InvalidOperation(
                    code="shipment_fields_unsupported",
                    values={"fields": ", ".join(sorted(unknown))},
                )
            movements = intent.get("movements")
            if not isinstance(movements, list) or not movements:
                raise InvalidOperation(code="shipment_execution_movement_missing")
            if intent.get("outbound_delivery_id"):
                from reality.services.outbound_deliveries import (
                    require_matches_delivery,
                )

                # Spec 334: the review refuses what the confirmation would refuse.
                if tool != "shipment_dispatch" or purpose != "customer_delivery":
                    raise InvalidOperation(code="outbound_delivery_dispatch_mismatch")
                planned = require_matches_delivery(
                    session,
                    tenant_id,
                    intent["outbound_delivery_id"],
                    party.id,
                    movements,
                )
                # A revision after the review changes what the dispatch would keep.
                state["outbound_delivery"] = {
                    "id": planned.id,
                    "source_record_id": planned.source_record_id,
                }
            expected = PURPOSES[purpose][1]
            if purpose == "customer_delivery":
                # Spec 306: one shipment carries a ship-complete order whole.
                from reality.services.delivery_rules import require_delivery_rule

                require_delivery_rule(
                    session,
                    tenant_id,
                    [
                        (raw.get("commitment_id"), raw.get("quantity") or 0)
                        for raw in movements
                        if isinstance(raw, dict)
                    ],
                )
            previews = []
            for raw in movements:
                if not isinstance(raw, dict):
                    raise InvalidOperation(code="shipment_movement_not_object")
                unknown = set(raw) - SHIPMENT_MOVEMENT_FIELDS
                if unknown:
                    raise InvalidOperation(
                        code="shipment_movement_fields_unsupported",
                        values={"fields": ", ".join(sorted(unknown))},
                    )
                movement = dict(raw)
                movement_type = movement.pop("movement_type", expected)
                if movement_type != expected:
                    raise InvalidOperation(
                        code="shipment_movement_type_mismatch_expected",
                        values={"expected": expected},
                    )
                movement.pop("shipment_package_id", None)
                movement.pop("source_record_id", None)
                blocked = movement.pop("blocked_quantity", None)
                block_reason = movement.pop("block_reason", None)
                preview = _append_movement(
                    session,
                    tenant_id,
                    movement_type=movement_type,
                    source_record_id=source_id,
                    validate_only=True,
                    **movement,
                )
                if blocked:
                    from reality.services.stock_blocks import validate_block

                    if movement_type != "receipt":
                        raise InvalidOperation(code="stock_block_receipt_only")
                    validate_block(
                        session,
                        tenant_id,
                        preview["item_id"],
                        preview["to_location_id"],
                        blocked,
                        block_reason or "",
                        handling_unit_id=movement.get("handling_unit_id"),
                        lot_id=preview.get("lot_id"),
                        serial_unit_id=movement.get("serial_unit_id"),
                        _incoming=Decimal(str(preview["quantity"])),
                        _receipt=Decimal(str(preview["quantity"])),
                    )
                readiness = None
                if purpose == "customer_delivery":
                    readiness = fulfillment_readiness(
                        session,
                        tenant_id,
                        preview["commitment_id"],
                        proposed_quantity=Decimal(preview["quantity"]),
                        from_location_id=preview.get("from_location_id"),
                        # The whole shipment answers to the order's rule.
                        _delivery_rule=False,
                    )
                    if not readiness.ship_ready:
                        raise InvalidOperation(
                            code="shipment_blocked_readiness",
                            values={
                                "blockers": ", ".join(readiness.blocker_codes),
                                "required_amount": readiness.required_amount,
                                "required_currency": readiness.currency,
                                "received_amount": readiness.received_amount,
                                "received_currency": readiness.currency,
                            },
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
            raise InvalidOperation(code="shipment_event_kind_or_reporter_unsupported")
        package_id = intent.get("shipment_package_id")
        if package_id:
            package = _owned(session, ShipmentPackage, tenant_id, package_id)
            if package.shipment_id != shipment.id:
                raise InvalidOperation(code="shipment_package_not_on_shipment")
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
            raise InvalidOperation(code="shipment_event_already_superseded")
        replacement_id = intent.get("replacement_event_id")
        if replacement_id:
            replacement = _owned(session, ShipmentEvent, tenant_id, replacement_id)
            if (
                replacement.shipment_id != event.shipment_id
                or replacement.id == event.id
            ):
                raise InvalidOperation(code="shipment_event_replacement_invalid")
        if not str(intent.get("reason", "")).strip():
            raise InvalidOperation(code="shipment_event_correction_reason_required")
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
