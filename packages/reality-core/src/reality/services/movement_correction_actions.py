"""Standalone movement correction reviews in the common proposal lifecycle."""

from __future__ import annotations

import hashlib
import json
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from reality.db.core import (
    BusinessEvent,
    ChangeProposal,
    Commitment,
    Item,
    Location,
    Movement,
    MovementCorrection,
    Reservation,
)
from reality.services.core import (
    InvalidOperation,
    NotFound,
    _movement_values,
    _tenant_record,
    active_reserved,
    preview_movement_correction,
    stock_at,
    stock_by_identity,
)
from reality.services.delivery_reads import delivery_case


def _json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, default=str, separators=(",", ":"))


def _quantity(value: Any) -> str:
    return format(Decimal(value).normalize(), "f")


def action_keys(
    session: Session, tenant_id: str, tool: str, intent: dict[str, Any]
) -> set[tuple[str, str]]:
    keys: set[tuple[str, str]] = set()
    values = []
    if tool == "movement_correct":
        original = _tenant_record(
            session, Movement, tenant_id, intent.get("movement_id", "")
        )
        values = [_movement_values(original), intent.get("replacement") or {}]
    elif tool == "movement_create":
        values = [intent]
    elif tool == "reservation_release":
        row = _tenant_record(
            session, Reservation, tenant_id, intent.get("reservation_id", "")
        )
        keys.add((row.item_id, row.location_id))
        values = [{"commitment_id": row.commitment_id}]
    else:
        values = [intent]
    for value in values:
        for name in ("from_location_id", "to_location_id"):
            if value.get("item_id") and value.get(name):
                keys.add((value["item_id"], value[name]))
        if value.get("commitment_id"):
            row = _tenant_record(session, Commitment, tenant_id, value["commitment_id"])
            keys.add(("commitment", row.id))
            keys.add((row.item_id, row.location_id))
    return keys


def assert_no_unresolved(
    session: Session,
    tenant_id: str,
    tool: str,
    intent: dict[str, Any],
    exclude: str | None = None,
) -> None:
    tools = {
        "movement_correct",
        "reserve",
        "movement_create",
        "reservation_release",
        "commitment_hold",
        "commitment_hold_release",
    }
    query = select(ChangeProposal).where(
        ChangeProposal.tenant_id == tenant_id,
        ChangeProposal.status == "executing",
        ChangeProposal.type.in_([f"tool:{name}" for name in tools]),
    )
    if exclude:
        query = query.where(ChangeProposal.id != exclude)
    if tool != "movement_correct":
        query = query.where(ChangeProposal.type == "tool:movement_correct")
    candidates = list(session.scalars(query))
    if not candidates:
        return
    current = action_keys(session, tenant_id, tool, intent)
    for candidate in candidates:
        if current & action_keys(
            session,
            tenant_id,
            candidate.type.removeprefix("tool:"),
            json.loads(candidate.input),
        ):
            raise InvalidOperation(
                "An earlier overlapping execution is unresolved. Check its outcome first."
            )


def correction_state(
    session: Session,
    tenant_id: str,
    original: dict[str, Any],
    replacement: dict[str, Any] | None,
    *,
    projected: bool = True,
) -> dict[str, Any]:
    values = [original, replacement or {}]
    pool_ids = {
        (value["item_id"], value[name])
        for value in values
        for name in ("from_location_id", "to_location_id")
        if value.get("item_id") and value.get(name)
    }
    pools = []
    for item_id, location_id in sorted(pool_ids):
        item = _tenant_record(session, Item, tenant_id, item_id)
        location = _tenant_record(session, Location, tenant_id, location_id)
        physical = stock_at(session, tenant_id, item_id, location_id)
        reserved = active_reserved(session, tenant_id, item_id, location_id)
        delta = Decimal(0)
        identities = []
        for index, value in enumerate(values):
            if value.get("item_id") != item_id:
                continue
            quantity = Decimal(str(value["quantity"]))
            effect = int(value.get("to_location_id") == location_id) - int(
                value.get("from_location_id") == location_id
            )
            delta += quantity * effect * (-1 if index == 0 else 1)
            tracking = {
                key: value.get(key)
                for key in ("handling_unit_id", "lot_id", "serial_unit_id")
            }
            if any(tracking.values()):
                identities.append(
                    {
                        **tracking,
                        "physical": _quantity(
                            stock_by_identity(
                                session, tenant_id, item_id, location_id, **tracking
                            )
                        ),
                    }
                )
        if not projected:
            delta = Decimal(0)
        pools.append(
            {
                "item_id": item_id,
                "item": item.name,
                "unit": item.unit,
                "location_id": location_id,
                "location": location.name,
                "physical": _quantity(physical),
                "reserved": _quantity(reserved),
                "delta": _quantity(delta),
                "after": _quantity(physical + delta),
                "available_after": _quantity(physical + delta - reserved),
                "identities": identities,
            }
        )
    commitments = []
    for cid in sorted(
        {value["commitment_id"] for value in values if value.get("commitment_id")}
    ):
        detail = delivery_case(session, tenant_id, cid)
        commitments.append(detail["case"])
    return {"pools": pools, "commitments": commitments}


def review_correction(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> dict[str, Any]:
    session.expire_all()  # Re-read references after the shared mutation lock.
    allowed = {
        "movement_id",
        "reason",
        "replacement",
        "expected_revision",
        "preview_fingerprint",
    }
    if set(arguments) - allowed:
        raise InvalidOperation("The correction contains unsupported fields.")
    preview = preview_movement_correction(
        session,
        tenant_id,
        arguments.get("movement_id", ""),
        reason=arguments.get("reason", ""),
        replacement=arguments.get("replacement"),
    )
    intent = {
        "movement_id": preview["movement_id"],
        "reason": preview["reason"],
        "expected_revision": preview["revision"],
        "preview_fingerprint": preview["request_fingerprint"],
    }
    if preview["replacement"] is not None:
        intent["replacement"] = preview["replacement"]
    state = correction_state(
        session, tenant_id, preview["original"], preview["replacement"]
    )
    state["correction"] = preview
    state = json.loads(_json(state))
    token = hashlib.sha256(_json([tenant_id, intent, state]).encode()).hexdigest()
    return {
        "version": 1,
        "tool": "movement_correct",
        "intent": intent,
        "effect": {},
        "state": state,
        "token": token,
    }


def _evidence(
    session: Session, tenant_id: str, proposal: ChangeProposal, review: dict[str, Any]
) -> tuple[dict[str, Any], list[dict[str, str]]] | None:
    preview = review["state"]["correction"]
    events = list(
        session.scalars(
            select(BusinessEvent)
            .where(
                BusinessEvent.tenant_id == tenant_id,
                BusinessEvent.action_id == proposal.id,
                BusinessEvent.event_type == "movement.corrected",
            )
            .limit(2)
        )
    )
    if len(events) != 1:
        return None
    event = events[0]
    payload = json.loads(event.payload)
    if event.subject_type != "movement" or event.subject_id != preview["movement_id"]:
        return None
    relation = session.scalar(
        select(MovementCorrection).where(
            MovementCorrection.tenant_id == tenant_id,
            MovementCorrection.id == payload.get("correction_id"),
        )
    )
    if (
        relation is None
        or relation.original_movement_id != preview["movement_id"]
        or relation.reason != preview["reason"]
        or relation.request_fingerprint != preview["request_fingerprint"]
    ):
        return None
    if (
        relation.compensating_movement_id != payload.get("compensating_movement_id")
        or relation.replacement_movement_id != payload.get("replacement_movement_id")
        or payload.get("reason") != preview["reason"]
    ):
        return None
    original = _tenant_record(
        session, Movement, tenant_id, relation.original_movement_id
    )
    compensation = _tenant_record(
        session, Movement, tenant_id, relation.compensating_movement_id
    )
    if _movement_values(original) != preview["original"]:
        return None
    expected = {
        **preview["original"],
        "type": "correction",
        "from_location_id": original.to_location_id,
        "to_location_id": original.from_location_id,
        "commitment_id": None,
        "source_record_id": None,
        "resolves_movement_id": None,
        "return_announcement_id": None,
    }
    actual = _movement_values(compensation)
    if any(
        actual[key] != value
        for key, value in expected.items()
        if key not in {"id", "occurred_at"}
    ):
        return None
    replacement = preview["replacement"]
    if bool(replacement) != bool(relation.replacement_movement_id):
        return None
    if replacement:
        recorded = _tenant_record(
            session, Movement, tenant_id, relation.replacement_movement_id
        )
        actual = _movement_values(recorded)
        for key, value in replacement.items():
            if key == "reason":
                continue  # Adjustment reason is event/intent context, not a Movement column.
            if key == "quantity":
                if Decimal(actual[key]) != Decimal(str(value)):
                    return None
            elif actual.get(key) != value:
                return None
        for key in (
            "commitment_id",
            "source_record_id",
            "from_location_id",
            "to_location_id",
            "handling_unit_id",
            "serial_unit_id",
        ):
            if actual[key] != replacement.get(key):
                return None
    receipt = {
        "correction_id": relation.id,
        "original_movement_id": original.id,
        "compensating_movement_id": compensation.id,
        "replacement_movement_id": relation.replacement_movement_id,
        "replayed": False,
    }
    links = [
        {"kind": "movement", "id": identity}
        for identity in (original.id, compensation.id, relation.replacement_movement_id)
        if identity
    ]
    links.append({"kind": "business_event", "id": event.id})
    return receipt, links


def correction_detail(
    session: Session, tenant_id: str, proposal: ChangeProposal
) -> dict[str, Any]:
    arguments = json.loads(proposal.input)
    review = arguments.get("_delivery_review")
    result = {
        "id": proposal.id,
        "tool": "movement_correct",
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
    if review and proposal.status in {"executing", "executed"}:
        evidence = _evidence(session, tenant_id, proposal, review)
        if evidence and (
            proposal.status != "executed" or result["receipt"] == evidence[0]
        ):
            result["verification"] = (
                "verified" if proposal.status == "executed" else "recorded_unsettled"
            )
            result["links"] = evidence[1]
            result["recorded_receipt"] = evidence[0]
    if review:
        try:
            preview = review["state"]["correction"]
            result["observation"] = correction_state(
                session,
                tenant_id,
                preview["original"],
                preview["replacement"],
                projected=False,
            )
        except (InvalidOperation, NotFound) as error:
            result["observation_error"] = str(error)
        except SQLAlchemyError:
            session.rollback()
            result["observation_error"] = (
                "Current observation unavailable. Refresh this view."
            )
    return result
