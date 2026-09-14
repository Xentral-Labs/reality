"""Bounded reviewed opening movements; stock remains derived from immutable events."""

from __future__ import annotations

import hashlib
import json
from decimal import Decimal
from decimal import InvalidOperation as DecimalError
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from reality.db.core import BusinessEvent, ChangeProposal, Item, Location, Movement
from reality.services.core import (
    InvalidOperation,
    _append_movement,
    _tenant_record,
    active_reserved,
    positive,
    stock_at,
    utc_datetime,
)


def _json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, default=str, separators=(",", ":"))


def _quantity(value: Any) -> str:
    return format(Decimal(value).normalize(), "f")


def is_opening(tool: str, arguments: dict[str, Any]) -> bool:
    return (
        tool == "movement_create" and arguments.get("movement_type") == "opening_stock"
    )


def _intent(arguments: dict[str, Any]) -> dict[str, Any]:
    allowed = {"movement_type", "item_id", "to_location_id", "quantity", "occurred_at"}
    if set(arguments) - allowed or arguments.get("movement_type") != "opening_stock":
        raise InvalidOperation(
            "Opening stock accepts only item, destination, quantity and optional time."
        )
    for name in ("item_id", "to_location_id"):
        if not isinstance(arguments.get(name), str) or not arguments[name]:
            raise InvalidOperation("Choose an item and a destination location.")
    try:
        qty = positive(arguments.get("quantity", ""))
    except (DecimalError, TypeError, ValueError) as error:
        raise InvalidOperation("Enter a valid positive quantity.") from error
    if (
        qty >= Decimal(100000000000000)
        or qty * 10000 != (qty * 10000).to_integral_value()
    ):
        raise InvalidOperation(
            "Opening quantity supports at most 14 integer and 4 decimal places."
        )
    intent = {
        key: arguments[key] for key in ("movement_type", "item_id", "to_location_id")
    }
    intent["quantity"] = _quantity(qty)
    if arguments.get("occurred_at"):
        if not isinstance(arguments["occurred_at"], str):
            raise InvalidOperation("Enter a valid occurrence time.")
        intent["occurred_at"] = utc_datetime(arguments["occurred_at"]).isoformat()
    return intent


def review_opening(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> dict[str, Any]:
    intent = _intent(arguments)
    session.expire_all()
    item = _tenant_record(session, Item, tenant_id, intent["item_id"])
    location = _tenant_record(session, Location, tenant_id, intent["to_location_id"])
    if item.tracking_type != "none":
        raise InvalidOperation(
            "This opening stock form supports items without lot or serial tracking."
        )
    _append_movement(session, tenant_id, **intent, validate_only=True)
    physical = stock_at(session, tenant_id, item.id, location.id)
    reserved = active_reserved(session, tenant_id, item.id, location.id)
    state = {
        "item": {
            key: getattr(item, key)
            for key in (
                "id",
                "sku",
                "name",
                "unit",
                "is_active",
                "item_type",
                "tracking_type",
            )
        },
        "location": {
            key: getattr(location, key)
            for key in ("id", "name", "is_active", "allows_stock")
        },
        "physical": _quantity(physical),
        "reserved": _quantity(reserved),
    }
    return {
        "version": 1,
        "tool": "movement_create",
        "intent": intent,
        "state": state,
        "effect": {
            "added": intent["quantity"],
            "physical_after": _quantity(physical + Decimal(intent["quantity"])),
            "reserved_after": _quantity(reserved),
        },
        "token": hashlib.sha256(_json([tenant_id, intent, state]).encode()).hexdigest(),
    }


def assert_opening_overlap(
    session: Session,
    tenant_id: str,
    tool: str,
    arguments: dict[str, Any],
    exclude: str | None,
) -> None:
    from reality.services.movement_correction_actions import action_keys

    relevant = {
        "movement_create",
        "movement_correct",
        "reserve",
        "reservation_release",
        "commitment_hold",
        "commitment_hold_release",
    }
    if tool not in relevant:
        return
    opening = is_opening(tool, arguments)
    if opening:
        _intent(
            {
                key: value
                for key, value in arguments.items()
                if key != "_delivery_review"
            }
        )
    candidates = session.scalars(
        select(ChangeProposal).where(
            ChangeProposal.tenant_id == tenant_id,
            ChangeProposal.status == "executing",
            ChangeProposal.type.in_([f"tool:{name}" for name in relevant]),
        )
    )
    current = None
    for candidate in candidates:
        if candidate.id == exclude:
            continue
        other = json.loads(candidate.input)
        other_tool = candidate.type.removeprefix("tool:")
        if not opening and not is_opening(other_tool, other):
            continue
        if current is None:
            current = action_keys(session, tenant_id, tool, arguments)
        if current & action_keys(session, tenant_id, other_tool, other):
            raise InvalidOperation(
                "An overlapping stock action is unresolved. Check its outcome first."
            )


def opening_detail(
    session: Session, tenant_id: str, proposal: ChangeProposal
) -> dict[str, Any]:
    from reality.tools.application import _opening_movement_evidence

    saved = json.loads(proposal.input)
    review = saved.get("_delivery_review")
    intent = {key: value for key, value in saved.items() if key != "_delivery_review"}
    result = {
        "id": proposal.id,
        "tool": "movement_create",
        "movement_type": "opening_stock",
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
    if proposal.status not in {"executing", "executed"}:
        return result
    evidence = _opening_movement_evidence(session, tenant_id, proposal)
    if not evidence:
        return result
    movement = _tenant_record(session, Movement, tenant_id, evidence["movement_id"])
    event = _tenant_record(session, BusinessEvent, tenant_id, evidence["event_id"])
    payload = json.loads(event.payload)
    expected = {
        "type": "opening_stock",
        "item_id": movement.item_id,
        "to_location_id": movement.to_location_id,
        **{
            name: None
            for name in (
                "from_location_id",
                "commitment_id",
                "handling_unit_id",
                "lot_id",
                "serial_unit_id",
            )
        },
    }
    if (
        any(payload.get(key) != value for key, value in expected.items())
        or set(expected) - set(payload)
        or event.source_record_id is not None
        or event.occurred_at != movement.occurred_at
        or movement.resolves_movement_id is not None
        or movement.return_announcement_id is not None
    ):
        return result
    try:
        if Decimal(str(payload.get("quantity"))) != movement.quantity:
            return result
    except DecimalError:
        return result
    receipt = {"records": [{"family": "movement", "id": movement.id}]}
    if proposal.status == "executed" and result["receipt"] != receipt:
        return result
    result.update(
        verification="verified"
        if proposal.status == "executed"
        else "recorded_unsettled",
        recorded_receipt=receipt,
        links=[
            {"kind": "movement", "id": movement.id},
            {"kind": "business_event", "id": event.id},
        ],
        observation={
            "physical": _quantity(
                stock_at(session, tenant_id, movement.item_id, movement.to_location_id)
            ),
            "reserved": _quantity(
                active_reserved(
                    session, tenant_id, movement.item_id, movement.to_location_id
                )
            ),
        },
    )
    return result
