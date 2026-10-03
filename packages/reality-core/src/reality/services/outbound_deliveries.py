"""Planned outbound deliveries and picking (spec 334).

A planned delivery groups open promises of one customer before dispatch, with
the quantity planned for each, an optional recipient (a store of a retail
chain, say; without one, the customer), a stated address, an optional booked
slot and an optional staging location. Each statement of it — the plan and
every revision — is kept as a version of one internal source stream, and the
delivery points at its current statement, which holds the address and slot.

Picking is a transfer from where a promise is reserved to the staging location,
and the reservation moves with the goods, so availability stays true at both
places. A put-back is the reverse transfer. Nothing about a delivery is stored
as a status: planned, picked, waiting to be put back and shipped are read from
its lines, its pick movements and the shipment that executed it.
"""

from __future__ import annotations

import hashlib
import json
from decimal import Decimal
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from reality.db.core import (
    Commitment,
    Document,
    Item,
    Location,
    Movement,
    OutboundDelivery,
    OutboundDeliveryLine,
    OutboundDeliveryPick,
    Party,
    Reservation,
    SourceRecord,
    now,
    uid,
)
from reality.services.business_locks import lock_delivery_state
from reality.services.core import (
    InvalidOperation,
    NotFound,
    _require_business_mutation,
    _tenant_record,
    decimal,
    emit_business_event,
    open_quantity,
    record_movement,
    store_source_record,
    utc_datetime,
)

ZERO = Decimal(0)
SOURCE_SYSTEM = "internal_outbound_delivery"
SOURCE_TYPE = "outbound_delivery"
ADDRESS_FIELDS = ("name", "street", "postal_code", "city", "country", "note")
DELIVERY_TOOLS = (
    "outbound_delivery_plan",
    "outbound_delivery_revise",
    "outbound_delivery_pick",
    "outbound_delivery_put_back",
)
UNSTATED: Any = object()
REVISABLE = (
    "recipient_party_id",
    "address",
    "slot",
    "staging_location_id",
    "lines",
    "note",
)


def _plain(value: Decimal) -> str:
    text = format(value.normalize(), "f")
    return "0" if text in {"-0", ""} else text


def _quantity(value: Any) -> Decimal:
    try:
        result = decimal(value)
    except (ArithmeticError, ValueError, TypeError, InvalidOperation):
        raise InvalidOperation(
            code="master_data_field_not_positive", values={"field": "Quantity"}
        ) from None
    if result <= ZERO:
        raise InvalidOperation(
            code="master_data_field_not_positive", values={"field": "Quantity"}
        )
    return result


def _delivery(
    session: Session, tenant_id: str, delivery_id: str, *, lock: bool = False
) -> OutboundDelivery:
    query = select(OutboundDelivery).where(
        OutboundDelivery.tenant_id == tenant_id,
        OutboundDelivery.id == str(delivery_id or ""),
    )
    if lock:
        query = query.with_for_update()
    delivery = session.scalar(query)
    if delivery is None:
        raise NotFound(code="outbound_delivery_not_found")
    return delivery


def _statement(session: Session, delivery: OutboundDelivery) -> dict[str, Any]:
    source = _tenant_record(
        session, SourceRecord, delivery.tenant_id, delivery.source_record_id
    )
    return json.loads(source.payload)


def _address(raw: Any) -> dict[str, str]:
    if raw in (None, ""):
        return {}
    if not isinstance(raw, dict) or set(raw) - set(ADDRESS_FIELDS):
        raise InvalidOperation(code="outbound_delivery_address_invalid")
    address = {}
    for field in ADDRESS_FIELDS:
        value = raw.get(field)
        if value is None:
            continue
        if not isinstance(value, str):
            raise InvalidOperation(code="outbound_delivery_address_invalid")
        if value.strip():
            address[field] = value.strip()
    return address


def _slot(raw: Any) -> dict[str, str] | None:
    """A booked slot, as stated: when it opens and when it closes."""
    if raw in (None, ""):
        return None
    if not isinstance(raw, dict) or set(raw) - {"from", "until"}:
        raise InvalidOperation(code="outbound_delivery_slot_invalid")
    try:
        opens = utc_datetime(raw.get("from"))
        closes = utc_datetime(raw.get("until"))
    except (InvalidOperation, ValueError, TypeError):
        raise InvalidOperation(code="outbound_delivery_slot_invalid") from None
    if opens is None or closes is None or closes <= opens:
        raise InvalidOperation(code="outbound_delivery_slot_invalid")
    return {"from": opens.isoformat(), "until": closes.isoformat()}


def _party(session: Session, tenant_id: str, party_id: Any) -> Party | None:
    if party_id in (None, ""):
        return None
    return _tenant_record(session, Party, tenant_id, str(party_id))


def _staging(session: Session, tenant_id: str, location_id: Any) -> Location | None:
    if location_id in (None, ""):
        return None
    location = _tenant_record(session, Location, tenant_id, str(location_id))
    if not location.is_active or not location.allows_stock:
        raise InvalidOperation(code="outbound_delivery_staging_invalid")
    return location


def _planned_elsewhere(
    session: Session,
    tenant_id: str,
    commitment_ids: list[str],
    exclude_delivery_id: str | None,
) -> dict[str, Decimal]:
    """What other deliveries not yet shipped already plan for each promise."""
    query = (
        select(
            OutboundDeliveryLine.commitment_id, func.sum(OutboundDeliveryLine.quantity)
        )
        .join(
            OutboundDelivery,
            (OutboundDelivery.tenant_id == OutboundDeliveryLine.tenant_id)
            & (OutboundDelivery.id == OutboundDeliveryLine.outbound_delivery_id),
        )
        .where(
            OutboundDeliveryLine.tenant_id == tenant_id,
            OutboundDeliveryLine.commitment_id.in_(commitment_ids),
            OutboundDelivery.shipment_id.is_(None),
        )
        .group_by(OutboundDeliveryLine.commitment_id)
    )
    if exclude_delivery_id:
        query = query.where(OutboundDelivery.id != exclude_delivery_id)
    return {row[0]: Decimal(row[1]) for row in session.execute(query)}


def _lines(
    session: Session,
    tenant_id: str,
    customer_id: str,
    raw: Any,
    delivery_id: str | None,
) -> list[tuple[Commitment, Decimal, Decimal]]:
    """Each stated line with its promise, its quantity and what it may plan."""
    if not isinstance(raw, list) or not raw:
        raise InvalidOperation(code="outbound_delivery_lines_required")
    seen: set[str] = set()
    stated: list[tuple[Commitment, Decimal]] = []
    for row in raw:
        if not isinstance(row, dict) or set(row) - {"commitment_id", "quantity"}:
            raise InvalidOperation(code="outbound_delivery_lines_required")
        commitment = _tenant_record(
            session, Commitment, tenant_id, str(row.get("commitment_id") or "")
        )
        if commitment.type != "customer_delivery":
            raise InvalidOperation(code="outbound_delivery_promise_not_customer")
        if commitment.to_party_id != customer_id:
            raise InvalidOperation(code="outbound_delivery_promise_other_customer")
        if commitment.status != "open":
            raise InvalidOperation(code="outbound_delivery_promise_not_open")
        if commitment.id in seen:
            raise InvalidOperation(code="outbound_delivery_promise_twice")
        seen.add(commitment.id)
        stated.append((commitment, _quantity(row.get("quantity"))))
    elsewhere = _planned_elsewhere(
        session, tenant_id, [commitment.id for commitment, _ in stated], delivery_id
    )
    checked = []
    for commitment, quantity in stated:
        room = open_quantity(session, tenant_id, commitment.id) - elsewhere.get(
            commitment.id, ZERO
        )
        if quantity > room:
            raise InvalidOperation(
                code="outbound_delivery_quantity_beyond_open",
                values={"open": _plain(max(room, ZERO))},
            )
        checked.append((commitment, quantity, room))
    return checked


def _picks(
    session: Session, tenant_id: str, line_ids: list[str]
) -> dict[str, list[tuple[OutboundDeliveryPick, Movement]]]:
    """The pick and put-back movements of each line, oldest first."""
    result: dict[str, list[tuple[OutboundDeliveryPick, Movement]]] = {
        line_id: [] for line_id in line_ids
    }
    if not line_ids:
        return result
    for pick, movement in session.execute(
        select(OutboundDeliveryPick, Movement)
        .join(
            Movement,
            (Movement.tenant_id == OutboundDeliveryPick.tenant_id)
            & (Movement.id == OutboundDeliveryPick.movement_id),
        )
        .where(
            OutboundDeliveryPick.tenant_id == tenant_id,
            OutboundDeliveryPick.outbound_delivery_line_id.in_(line_ids),
        )
        .order_by(Movement.occurred_at, Movement.id)
    ):
        result[pick.outbound_delivery_line_id].append((pick, movement))
    return result


def _identity(
    movement: Movement | Reservation,
) -> tuple[str | None, str | None, str | None]:
    return (movement.handling_unit_id, movement.lot_id, movement.serial_unit_id)


def _picked_by_identity(
    picks: list[tuple[OutboundDeliveryPick, Movement]],
) -> dict[tuple[str | None, str | None, str | None], Decimal]:
    held: dict[tuple[str | None, str | None, str | None], Decimal] = {}
    for pick, movement in picks:
        sign = 1 if pick.kind == "pick" else -1
        key = _identity(movement)
        held[key] = held.get(key, ZERO) + sign * Decimal(movement.quantity)
    return {key: value for key, value in held.items() if value > ZERO}


def _picked(picks: list[tuple[OutboundDeliveryPick, Movement]]) -> Decimal:
    return sum(_picked_by_identity(picks).values(), ZERO)


def _delivery_lines(
    session: Session, tenant_id: str, delivery_ids: list[str]
) -> dict[str, list[OutboundDeliveryLine]]:
    result: dict[str, list[OutboundDeliveryLine]] = {
        delivery_id: [] for delivery_id in delivery_ids
    }
    if not delivery_ids:
        return result
    for line in session.scalars(
        select(OutboundDeliveryLine)
        .where(
            OutboundDeliveryLine.tenant_id == tenant_id,
            OutboundDeliveryLine.outbound_delivery_id.in_(delivery_ids),
        )
        .order_by(OutboundDeliveryLine.id)
    ):
        result[line.outbound_delivery_id].append(line)
    return result


def _record_statement(
    session: Session,
    tenant_id: str,
    delivery_id: str,
    statement: dict[str, Any],
) -> tuple[SourceRecord, bool]:
    source, inserted, _ = store_source_record(
        session, tenant_id, SOURCE_SYSTEM, SOURCE_TYPE, delivery_id, statement
    )
    return source, inserted


def _plan_arguments(
    session: Session, tenant_id: str, arguments: dict[str, Any], delivery_id: str | None
) -> tuple[dict[str, Any], list[tuple[Commitment, Decimal, Decimal]]]:
    """The checked statement of a plan or of a revision's result."""
    customer = _tenant_record(
        session, Party, tenant_id, str(arguments.get("customer_id") or "")
    )
    recipient = _party(session, tenant_id, arguments.get("recipient_party_id"))
    staging = _staging(session, tenant_id, arguments.get("staging_location_id"))
    address = _address(arguments.get("address"))
    slot = _slot(arguments.get("slot"))
    lines = _lines(session, tenant_id, customer.id, arguments.get("lines"), delivery_id)
    statement = {
        "customer_id": customer.id,
        "recipient_party_id": recipient.id if recipient else None,
        "address": address,
        "slot": slot,
        "staging_location_id": staging.id if staging else None,
        "lines": [
            {"commitment_id": commitment.id, "quantity": _plain(quantity)}
            for commitment, quantity, _ in lines
        ],
        "note": str(arguments.get("note") or "").strip(),
    }
    return statement, lines


def _review_rows(lines: list[tuple[Commitment, Decimal, Decimal]]) -> list[list[str]]:
    # What the person saw: how much each promise could still be planned.
    return [[commitment.id, _plain(room)] for commitment, _, room in lines]


def _revised_arguments(
    session: Session,
    tenant_id: str,
    delivery: OutboundDelivery,
    changes: dict[str, Any],
) -> dict[str, Any]:
    unknown = set(changes) - set(REVISABLE)
    if unknown:
        raise InvalidOperation(
            code="outbound_delivery_fields_unsupported",
            values={"fields": ", ".join(sorted(unknown))},
        )
    current = _statement(session, delivery)
    merged = {key: current.get(key) for key in ("customer_id", *REVISABLE)}
    merged.update(changes)
    return merged


def _check_revision(
    session: Session,
    tenant_id: str,
    delivery: OutboundDelivery,
    statement: dict[str, Any],
) -> None:
    """A revision may not strand what is already picked."""
    lines = _delivery_lines(session, tenant_id, [delivery.id])[delivery.id]
    picks = _picks(session, tenant_id, [line.id for line in lines])
    planned = {
        row["commitment_id"]: Decimal(row["quantity"]) for row in statement["lines"]
    }
    waiting = ZERO
    for line in lines:
        held = _picked(picks[line.id])
        waiting += held
        if picks[line.id] and line.commitment_id not in planned:
            raise InvalidOperation(code="outbound_delivery_line_picked")
        if line.commitment_id in planned and planned[line.commitment_id] < held:
            raise InvalidOperation(code="outbound_delivery_line_picked")
    if (
        waiting > ZERO
        and statement["staging_location_id"] != delivery.staging_location_id
    ):
        raise InvalidOperation(code="outbound_delivery_staging_occupied")


def _delivery_id_for(tenant_id: str, action_id: str | None) -> str:
    if not action_id:
        return uid("odv")
    digest = hashlib.sha256(f"{tenant_id}:{action_id}".encode()).hexdigest()[:24]
    return f"odv_{digest}"


def _from_location(
    session: Session,
    tenant_id: str,
    commitment: Commitment,
    stated: Any,
    staging_id: str,
) -> str:
    if stated not in (None, ""):
        return _tenant_record(session, Location, tenant_id, str(stated)).id
    places = sorted(
        set(
            session.scalars(
                select(Reservation.location_id).where(
                    Reservation.tenant_id == tenant_id,
                    Reservation.commitment_id == commitment.id,
                    Reservation.status == "active",
                    Reservation.location_id != staging_id,
                )
            )
        )
    )
    if not places:
        raise InvalidOperation(code="outbound_delivery_pick_not_reserved")
    if len(places) > 1:
        raise InvalidOperation(code="outbound_delivery_pick_location_ambiguous")
    return places[0]


def _reservations_at(
    session: Session, tenant_id: str, commitment_id: str, location_id: str
) -> list[Reservation]:
    return list(
        session.scalars(
            select(Reservation)
            .where(
                Reservation.tenant_id == tenant_id,
                Reservation.commitment_id == commitment_id,
                Reservation.status == "active",
                Reservation.location_id == location_id,
            )
            .order_by(Reservation.reserved_at, Reservation.id)
        )
    )


def _pick_plan(
    session: Session,
    tenant_id: str,
    delivery: OutboundDelivery,
    raw: Any,
) -> list[dict[str, Any]]:
    """Each stated pick, checked: its line, promise, source location and quantity."""
    if delivery.shipment_id:
        raise InvalidOperation(code="outbound_delivery_shipped")
    if not delivery.staging_location_id:
        raise InvalidOperation(code="outbound_delivery_staging_missing")
    if not isinstance(raw, list) or not raw:
        raise InvalidOperation(code="outbound_delivery_lines_required")
    lines = {
        line.commitment_id: line
        for line in _delivery_lines(session, tenant_id, [delivery.id])[delivery.id]
    }
    picks = _picks(session, tenant_id, [line.id for line in lines.values()])
    planned = []
    for row in raw:
        if not isinstance(row, dict) or set(row) - {
            "commitment_id",
            "quantity",
            "from_location_id",
        }:
            raise InvalidOperation(code="outbound_delivery_lines_required")
        line = lines.get(str(row.get("commitment_id") or ""))
        if line is None:
            raise InvalidOperation(code="outbound_delivery_pick_not_on_delivery")
        commitment = _tenant_record(session, Commitment, tenant_id, line.commitment_id)
        if commitment.status != "open":
            raise InvalidOperation(code="outbound_delivery_promise_not_open")
        quantity = _quantity(row.get("quantity"))
        picked = _picked(picks[line.id])
        if picked + quantity > Decimal(line.quantity):
            raise InvalidOperation(
                code="outbound_delivery_pick_beyond_planned",
                values={"open": _plain(Decimal(line.quantity) - picked)},
            )
        source = _from_location(
            session,
            tenant_id,
            commitment,
            row.get("from_location_id"),
            delivery.staging_location_id,
        )
        if source == delivery.staging_location_id:
            raise InvalidOperation(code="outbound_delivery_staging_invalid")
        reservations = _reservations_at(session, tenant_id, commitment.id, source)
        reserved = sum((Decimal(row.quantity) for row in reservations), ZERO)
        if reserved < quantity:
            raise InvalidOperation(code="outbound_delivery_pick_not_reserved")
        planned.append(
            {
                "line": line,
                "commitment": commitment,
                "quantity": quantity,
                "from_location_id": source,
                "picked": picked,
                "reservations": reservations,
            }
        )
    return planned


def _put_back_plan(
    session: Session,
    tenant_id: str,
    delivery: OutboundDelivery,
    raw: Any,
) -> list[dict[str, Any]]:
    if delivery.shipment_id:
        raise InvalidOperation(code="outbound_delivery_shipped")
    if not isinstance(raw, list) or not raw:
        raise InvalidOperation(code="outbound_delivery_lines_required")
    lines = {
        line.commitment_id: line
        for line in _delivery_lines(session, tenant_id, [delivery.id])[delivery.id]
    }
    picks = _picks(session, tenant_id, [line.id for line in lines.values()])
    planned = []
    for row in raw:
        if not isinstance(row, dict) or set(row) - {
            "commitment_id",
            "quantity",
            "to_location_id",
        }:
            raise InvalidOperation(code="outbound_delivery_lines_required")
        line = lines.get(str(row.get("commitment_id") or ""))
        if line is None:
            raise InvalidOperation(code="outbound_delivery_pick_not_on_delivery")
        quantity = _quantity(row.get("quantity"))
        held = _picked_by_identity(picks[line.id])
        picked = sum(held.values(), ZERO)
        if quantity > picked:
            raise InvalidOperation(
                code="outbound_delivery_put_back_beyond_picked",
                values={"picked": _plain(picked)},
            )
        target = _staging(session, tenant_id, row.get("to_location_id"))
        if target is None or target.id == delivery.staging_location_id:
            raise InvalidOperation(code="outbound_delivery_staging_invalid")
        planned.append(
            {
                "line": line,
                "commitment": _tenant_record(
                    session, Commitment, tenant_id, line.commitment_id
                ),
                "quantity": quantity,
                "to_location_id": target.id,
                "picked": picked,
                "held": held,
            }
        )
    return planned


def _pick_rows(planned: list[dict[str, Any]], key: str) -> list[dict[str, str]]:
    return [
        {
            "commitment_id": row["commitment"].id,
            "quantity": _plain(row["quantity"]),
            key: row[key],
        }
        for row in planned
    ]


def _pick_reviewed(planned: list[dict[str, Any]]) -> list[list[str]]:
    return [[row["commitment"].id, _plain(row["picked"])] for row in planned]


def review_outbound_delivery(
    session: Session, tenant_id: str, tool: str, arguments: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any]]:
    """The arguments a confirmation executes and what the person is shown."""
    if tool == "outbound_delivery_plan":
        statement, lines = _plan_arguments(session, tenant_id, arguments, None)
        normalized = {**statement, "reviewed": _review_rows(lines)}
        return normalized, _preview(session, tenant_id, statement, lines)
    delivery = _delivery(
        session, tenant_id, str(arguments.get("outbound_delivery_id") or "")
    )
    if tool == "outbound_delivery_revise":
        if delivery.shipment_id:
            raise InvalidOperation(code="outbound_delivery_shipped")
        changes = {
            key: value
            for key, value in arguments.items()
            if key not in {"outbound_delivery_id", "reviewed"}
        }
        merged = _revised_arguments(session, tenant_id, delivery, changes)
        statement, lines = _plan_arguments(session, tenant_id, merged, delivery.id)
        _check_revision(session, tenant_id, delivery, statement)
        normalized = {
            "outbound_delivery_id": delivery.id,
            **changes,
            "reviewed": _review_rows(lines),
        }
        preview = _preview(session, tenant_id, statement, lines)
        preview["outbound_delivery_id"] = delivery.id
        preview["previous"] = _statement(session, delivery)
        return normalized, preview
    if tool == "outbound_delivery_pick":
        planned = _pick_plan(session, tenant_id, delivery, arguments.get("lines"))
        normalized = {
            "outbound_delivery_id": delivery.id,
            "lines": _pick_rows(planned, "from_location_id"),
            "reviewed": _pick_reviewed(planned),
        }
    elif tool == "outbound_delivery_put_back":
        planned = _put_back_plan(session, tenant_id, delivery, arguments.get("lines"))
        normalized = {
            "outbound_delivery_id": delivery.id,
            "lines": _pick_rows(planned, "to_location_id"),
            "reviewed": _pick_reviewed(planned),
        }
    else:
        raise InvalidOperation(code="proposal_tool_not_found")
    return normalized, {
        "outbound_delivery_id": delivery.id,
        "staging_location_id": delivery.staging_location_id,
        "lines": [
            {
                **row,
                "picked_before": reviewed[1],
            }
            for row, reviewed in zip(
                normalized["lines"], normalized["reviewed"], strict=True
            )
        ],
    }


def _preview(
    session: Session,
    tenant_id: str,
    statement: dict[str, Any],
    lines: list[tuple[Commitment, Decimal, Decimal]],
) -> dict[str, Any]:
    items = {
        item.id: item
        for item in session.scalars(
            select(Item).where(
                Item.tenant_id == tenant_id,
                Item.id.in_({commitment.item_id for commitment, _, _ in lines}),
            )
        )
    }
    return {
        **statement,
        "lines": [
            {
                "commitment_id": commitment.id,
                "item_id": commitment.item_id,
                "item": items[commitment.item_id].name
                if commitment.item_id in items
                else None,
                "quantity": _plain(quantity),
                "may_plan": _plain(room),
            }
            for commitment, quantity, room in lines
        ],
    }


def _require_reviewed(reviewed: Any, rows: list[list[str]]) -> None:
    if reviewed is not None and [list(row) for row in reviewed] != rows:
        raise InvalidOperation(code="outbound_delivery_changed_since_review")


def _write_lines(
    session: Session,
    tenant_id: str,
    delivery: OutboundDelivery,
    lines: list[tuple[Commitment, Decimal, Decimal]],
) -> None:
    existing = {
        line.commitment_id: line
        for line in _delivery_lines(session, tenant_id, [delivery.id])[delivery.id]
    }
    wanted = {commitment.id: quantity for commitment, quantity, _ in lines}
    for commitment_id, line in existing.items():
        if commitment_id not in wanted:
            session.delete(line)
    session.flush()
    for commitment, quantity, _ in lines:
        line = existing.get(commitment.id)
        if line is None:
            session.add(
                OutboundDeliveryLine(
                    id=uid("odl"),
                    tenant_id=tenant_id,
                    outbound_delivery_id=delivery.id,
                    commitment_id=commitment.id,
                    quantity=quantity,
                )
            )
        elif Decimal(line.quantity) != quantity:
            line.quantity = quantity
    session.flush()


def plan_outbound_delivery(
    session: Session,
    tenant_id: str,
    *,
    customer_id: str,
    lines: list[dict[str, Any]],
    recipient_party_id: str | None = None,
    address: dict[str, Any] | None = None,
    slot: dict[str, Any] | None = None,
    staging_location_id: str | None = None,
    note: str = "",
    reviewed: list[list[str]] | None = None,
    action_id: str | None = None,
    _commit: bool = True,
) -> OutboundDelivery:
    """
    Plan one delivery of a customer's open promises.

    BUSINESS PURPOSE:
    Plan one delivery of a customer's open promises.

    BUSINESS RULE services.outbound_deliveries.plan_outbound_delivery.step-16:
    Require the business permission for 'plan_outbound_delivery' before changing company records.

    BUSINESS RULE services.outbound_deliveries.plan_outbound_delivery.step-59:
    Record the outbound_delivery.planned audit or business-event evidence with the supplied record and confirmation identity.

    BUSINESS RULE services.outbound_deliveries.plan_outbound_delivery.result:
    Return delivery, as prepared by the preceding checks and service calls.
    """
    # reality-rule: services.outbound_deliveries.plan_outbound_delivery.step-16
    _require_business_mutation(session, tenant_id, "plan_outbound_delivery")
    lock_delivery_state(session, tenant_id)
    delivery_id = _delivery_id_for(tenant_id, action_id)
    existing = session.scalar(
        select(OutboundDelivery).where(
            OutboundDelivery.tenant_id == tenant_id, OutboundDelivery.id == delivery_id
        )
    )
    if existing is not None:
        # The same confirmation again: it is already planned.
        return existing
    statement, checked = _plan_arguments(
        session,
        tenant_id,
        {
            "customer_id": customer_id,
            "recipient_party_id": recipient_party_id,
            "address": address,
            "slot": slot,
            "staging_location_id": staging_location_id,
            "lines": lines,
            "note": note,
        },
        None,
    )
    _require_reviewed(reviewed, _review_rows(checked))
    source, _ = _record_statement(
        session,
        tenant_id,
        delivery_id,
        {**statement, "statement_id": action_id or delivery_id},
    )
    delivery = OutboundDelivery(
        id=delivery_id,
        tenant_id=tenant_id,
        customer_id=statement["customer_id"],
        recipient_party_id=statement["recipient_party_id"],
        staging_location_id=statement["staging_location_id"],
        source_record_id=source.id,
    )
    session.add(delivery)
    session.flush()
    _write_lines(session, tenant_id, delivery, checked)
    # reality-rule: services.outbound_deliveries.plan_outbound_delivery.step-59
    emit_business_event(
        session,
        tenant_id,
        "outbound_delivery.planned",
        "outbound_delivery",
        delivery.id,
        statement,
        source_record_id=source.id,
        action_id=action_id,
        correlation_id=action_id,
    )
    if _commit:
        session.commit()
    # reality-rule: services.outbound_deliveries.plan_outbound_delivery.result
    return delivery


def revise_outbound_delivery(
    session: Session,
    tenant_id: str,
    outbound_delivery_id: str,
    *,
    recipient_party_id: Any = UNSTATED,
    address: Any = UNSTATED,
    slot: Any = UNSTATED,
    staging_location_id: Any = UNSTATED,
    lines: Any = UNSTATED,
    note: Any = UNSTATED,
    reviewed: list[list[str]] | None = None,
    action_id: str | None = None,
    _commit: bool = True,
) -> OutboundDelivery:
    """
    State a delivery anew before it ships; the earlier statement is kept.

    A field left unstated stays as the current statement says; a field stated
    as empty clears it.

    BUSINESS PURPOSE:
    State a delivery anew before it ships; the earlier statement is kept.

    BUSINESS RULE services.outbound_deliveries.revise_outbound_delivery.step-32:
    Require the business permission for 'revise_outbound_delivery' before changing company records.

    BUSINESS RULE services.outbound_deliveries.revise_outbound_delivery.refusal-35:
    IF the outbound delivery already has a shipment:
        Refuse with outbound_delivery_shipped.

    BUSINESS RULE services.outbound_deliveries.revise_outbound_delivery.step-54:
    Record the outbound_delivery.revised audit or business-event evidence with the supplied record and confirmation identity.

    BUSINESS RULE services.outbound_deliveries.revise_outbound_delivery.result:
    Return delivery, as prepared by the preceding checks and service calls.
    """
    changes = {
        key: value
        for key, value in (
            ("recipient_party_id", recipient_party_id),
            ("address", address),
            ("slot", slot),
            ("staging_location_id", staging_location_id),
            ("lines", lines),
            ("note", note),
        )
        if value is not UNSTATED
    }
    # reality-rule: services.outbound_deliveries.revise_outbound_delivery.step-32
    _require_business_mutation(session, tenant_id, "revise_outbound_delivery")
    lock_delivery_state(session, tenant_id)
    delivery = _delivery(session, tenant_id, outbound_delivery_id, lock=True)
    # reality-rule: services.outbound_deliveries.revise_outbound_delivery.refusal-35
    if delivery.shipment_id:
        raise InvalidOperation(code="outbound_delivery_shipped")
    previous = _statement(session, delivery)
    merged = _revised_arguments(session, tenant_id, delivery, changes)
    statement, checked = _plan_arguments(session, tenant_id, merged, delivery.id)
    _check_revision(session, tenant_id, delivery, statement)
    _require_reviewed(reviewed, _review_rows(checked))
    source, inserted = _record_statement(
        session,
        tenant_id,
        delivery.id,
        {**statement, "statement_id": action_id or uid("stm")},
    )
    if not inserted:
        return delivery
    delivery.recipient_party_id = statement["recipient_party_id"]
    delivery.staging_location_id = statement["staging_location_id"]
    delivery.source_record_id = source.id
    _write_lines(session, tenant_id, delivery, checked)
    # reality-rule: services.outbound_deliveries.revise_outbound_delivery.step-54
    emit_business_event(
        session,
        tenant_id,
        "outbound_delivery.revised",
        "outbound_delivery",
        delivery.id,
        {
            "changed": sorted(
                key for key in REVISABLE if previous.get(key) != statement.get(key)
            ),
            "previous_source_record_id": _previous_source(
                session, tenant_id, delivery.id, source.id
            ),
            **statement,
        },
        source_record_id=source.id,
        action_id=action_id,
        correlation_id=action_id,
    )
    if _commit:
        session.commit()
    # reality-rule: services.outbound_deliveries.revise_outbound_delivery.result
    return delivery


def _previous_source(
    session: Session, tenant_id: str, delivery_id: str, current_id: str
) -> str | None:
    return session.scalar(
        select(SourceRecord.id)
        .where(
            SourceRecord.tenant_id == tenant_id,
            SourceRecord.source_system == SOURCE_SYSTEM,
            SourceRecord.source_type == SOURCE_TYPE,
            SourceRecord.external_id == delivery_id,
            SourceRecord.id != current_id,
        )
        .order_by(SourceRecord.version.desc())
        .limit(1)
    )


def _already_done(
    session: Session, tenant_id: str, event_type: str, action_id: str | None
) -> bool:
    if not action_id:
        return False
    from reality.db.core import BusinessEvent

    return bool(
        session.scalar(
            select(func.count()).where(
                BusinessEvent.tenant_id == tenant_id,
                BusinessEvent.event_type == event_type,
                BusinessEvent.action_id == action_id,
            )
        )
    )


def _move_reservation(
    session: Session,
    tenant_id: str,
    reservation: Reservation,
    quantity: Decimal,
    to_location_id: str,
    *,
    cause: str,
    movement_id: str,
    action_id: str | None,
) -> None:
    """Move part of a reservation with the goods it holds."""
    held = Decimal(reservation.quantity)
    reservation.status = "released"
    emit_business_event(
        session,
        tenant_id,
        "reservation.released",
        "reservation",
        reservation.id,
        {
            "commitment_id": reservation.commitment_id,
            "location_id": reservation.location_id,
            "quantity": held,
            "cause": cause,
            "movement_id": movement_id,
        },
        action_id=action_id,
        correlation_id=action_id,
    )
    for location_id, part, why in (
        (to_location_id, quantity, cause),
        (reservation.location_id, held - quantity, f"{cause}_remainder"),
    ):
        if part <= ZERO:
            continue
        moved = Reservation(
            id=uid("res"),
            tenant_id=tenant_id,
            commitment_id=reservation.commitment_id,
            item_id=reservation.item_id,
            location_id=location_id,
            quantity=part,
            status="active",
            handling_unit_id=reservation.handling_unit_id,
            lot_id=reservation.lot_id,
            serial_unit_id=reservation.serial_unit_id,
        )
        session.add(moved)
        emit_business_event(
            session,
            tenant_id,
            "reservation.created",
            "reservation",
            moved.id,
            {
                "commitment_id": moved.commitment_id,
                "item_id": moved.item_id,
                "location_id": location_id,
                "quantity": part,
                "handling_unit_id": moved.handling_unit_id,
                "lot_id": moved.lot_id,
                "serial_unit_id": moved.serial_unit_id,
                "previous_reservation_id": reservation.id,
                "cause": why,
                "movement_id": movement_id,
            },
            action_id=action_id,
            correlation_id=action_id,
        )
    session.flush()


def _transfer(
    session: Session,
    tenant_id: str,
    item_id: str,
    quantity: Decimal,
    from_location_id: str,
    to_location_id: str,
    identity: tuple[str | None, str | None, str | None],
    action_id: str | None,
) -> Movement:
    handling_unit_id, lot_id, serial_unit_id = identity
    return record_movement(
        session,
        tenant_id,
        "transfer",
        item_id,
        quantity,
        from_location_id=from_location_id,
        to_location_id=to_location_id,
        handling_unit_id=handling_unit_id,
        lot_id=lot_id,
        serial_unit_id=serial_unit_id,
        action_id=action_id,
        _commit=False,
    )


def pick_outbound_delivery(
    session: Session,
    tenant_id: str,
    outbound_delivery_id: str,
    lines: list[dict[str, Any]],
    *,
    reviewed: list[list[str]] | None = None,
    action_id: str | None = None,
    _commit: bool = True,
) -> OutboundDelivery:
    """
    Pick goods into staging; each promise's reservation moves with them.

    BUSINESS PURPOSE:
    Pick goods into staging; each promise's reservation moves with them.

    BUSINESS RULE services.outbound_deliveries.pick_outbound_delivery.step-11:
    Require the business permission for 'pick_outbound_delivery' before changing company records.

    BUSINESS RULE services.outbound_deliveries.pick_outbound_delivery.step-66:
    Record the outbound_delivery.picked audit or business-event evidence with the supplied record and confirmation identity.

    BUSINESS RULE services.outbound_deliveries.pick_outbound_delivery.result:
    Return delivery, as prepared by the preceding checks and service calls.
    """
    # reality-rule: services.outbound_deliveries.pick_outbound_delivery.step-11
    _require_business_mutation(session, tenant_id, "pick_outbound_delivery")
    lock_delivery_state(session, tenant_id)
    delivery = _delivery(session, tenant_id, outbound_delivery_id, lock=True)
    if _already_done(session, tenant_id, "outbound_delivery.picked", action_id):
        return delivery
    planned = _pick_plan(session, tenant_id, delivery, lines)
    _require_reviewed(reviewed, _pick_reviewed(planned))
    recorded = []
    for row in planned:
        remaining = row["quantity"]
        movement_ids = []
        for reservation in row["reservations"]:
            if remaining <= ZERO:
                break
            take = min(remaining, Decimal(reservation.quantity))
            movement = _transfer(
                session,
                tenant_id,
                row["commitment"].item_id,
                take,
                row["from_location_id"],
                delivery.staging_location_id,
                _identity(reservation),
                action_id,
            )
            _move_reservation(
                session,
                tenant_id,
                reservation,
                take,
                delivery.staging_location_id,
                cause="picked",
                movement_id=movement.id,
                action_id=action_id,
            )
            session.add(
                OutboundDeliveryPick(
                    id=uid("odp"),
                    tenant_id=tenant_id,
                    outbound_delivery_line_id=row["line"].id,
                    movement_id=movement.id,
                    kind="pick",
                )
            )
            movement_ids.append(movement.id)
            remaining -= take
        recorded.append(
            {
                "commitment_id": row["commitment"].id,
                "quantity": _plain(row["quantity"]),
                "from_location_id": row["from_location_id"],
                "movement_ids": movement_ids,
            }
        )
    session.flush()
    # reality-rule: services.outbound_deliveries.pick_outbound_delivery.step-66
    emit_business_event(
        session,
        tenant_id,
        "outbound_delivery.picked",
        "outbound_delivery",
        delivery.id,
        {"staging_location_id": delivery.staging_location_id, "lines": recorded},
        action_id=action_id,
        correlation_id=action_id,
    )
    if _commit:
        session.commit()
    # reality-rule: services.outbound_deliveries.pick_outbound_delivery.result
    return delivery


def put_back_outbound_delivery(
    session: Session,
    tenant_id: str,
    outbound_delivery_id: str,
    lines: list[dict[str, Any]],
    *,
    reviewed: list[list[str]] | None = None,
    action_id: str | None = None,
    _commit: bool = True,
) -> OutboundDelivery:
    """
    Move picked goods out of staging again, and an open promise's reservation.

    BUSINESS PURPOSE:
    Move picked goods out of staging again, and an open promise's reservation.

    BUSINESS RULE services.outbound_deliveries.put_back_outbound_delivery.step-11:
    Require the business permission for 'put_back_outbound_delivery' before changing company records.

    BUSINESS RULE services.outbound_deliveries.put_back_outbound_delivery.step-78:
    Record the outbound_delivery.put_back audit or business-event evidence with the supplied record and confirmation identity.

    BUSINESS RULE services.outbound_deliveries.put_back_outbound_delivery.result:
    Return delivery, as prepared by the preceding checks and service calls.
    """
    # reality-rule: services.outbound_deliveries.put_back_outbound_delivery.step-11
    _require_business_mutation(session, tenant_id, "put_back_outbound_delivery")
    lock_delivery_state(session, tenant_id)
    delivery = _delivery(session, tenant_id, outbound_delivery_id, lock=True)
    if _already_done(session, tenant_id, "outbound_delivery.put_back", action_id):
        return delivery
    planned = _put_back_plan(session, tenant_id, delivery, lines)
    _require_reviewed(reviewed, _pick_reviewed(planned))
    recorded = []
    for row in planned:
        remaining = row["quantity"]
        movement_ids = []
        # The last identity picked goes back first.
        for identity, held in reversed(list(row["held"].items())):
            if remaining <= ZERO:
                break
            take = min(remaining, held)
            movement = _transfer(
                session,
                tenant_id,
                row["commitment"].item_id,
                take,
                delivery.staging_location_id,
                row["to_location_id"],
                identity,
                action_id,
            )
            if row["commitment"].status == "open":
                left = take
                for reservation in _reservations_at(
                    session,
                    tenant_id,
                    row["commitment"].id,
                    delivery.staging_location_id,
                ):
                    if left <= ZERO:
                        break
                    if _identity(reservation) != identity:
                        continue
                    part = min(left, Decimal(reservation.quantity))
                    _move_reservation(
                        session,
                        tenant_id,
                        reservation,
                        part,
                        row["to_location_id"],
                        cause="put_back",
                        movement_id=movement.id,
                        action_id=action_id,
                    )
                    left -= part
            session.add(
                OutboundDeliveryPick(
                    id=uid("odp"),
                    tenant_id=tenant_id,
                    outbound_delivery_line_id=row["line"].id,
                    movement_id=movement.id,
                    kind="put_back",
                )
            )
            movement_ids.append(movement.id)
            remaining -= take
        recorded.append(
            {
                "commitment_id": row["commitment"].id,
                "quantity": _plain(row["quantity"]),
                "to_location_id": row["to_location_id"],
                "movement_ids": movement_ids,
            }
        )
    session.flush()
    # reality-rule: services.outbound_deliveries.put_back_outbound_delivery.step-78
    emit_business_event(
        session,
        tenant_id,
        "outbound_delivery.put_back",
        "outbound_delivery",
        delivery.id,
        {"staging_location_id": delivery.staging_location_id, "lines": recorded},
        action_id=action_id,
        correlation_id=action_id,
    )
    if _commit:
        session.commit()
    # reality-rule: services.outbound_deliveries.put_back_outbound_delivery.result
    return delivery


def _dispatch_movements(
    session: Session,
    tenant_id: str,
    delivery: OutboundDelivery,
    lines: list[OutboundDeliveryLine],
    picks: dict[str, list[tuple[OutboundDeliveryPick, Movement]]],
    commitments: dict[str, Commitment],
) -> list[dict[str, Any]]:
    """The movements a dispatch of this delivery carries."""
    uses_picking = any(picks[line.id] for line in lines)
    movements = []
    for line in lines:
        commitment = commitments[line.commitment_id]
        if commitment.status != "open":
            continue
        if uses_picking:
            for (handling_unit_id, lot_id, serial_unit_id), held in _picked_by_identity(
                picks[line.id]
            ).items():
                movements.append(
                    {
                        "commitment_id": commitment.id,
                        "item_id": commitment.item_id,
                        "from_location_id": delivery.staging_location_id,
                        "quantity": _plain(held),
                        **(
                            {"handling_unit_id": handling_unit_id}
                            if handling_unit_id
                            else {}
                        ),
                        **({"lot_id": lot_id} if lot_id else {}),
                        **(
                            {"serial_unit_id": serial_unit_id} if serial_unit_id else {}
                        ),
                    }
                )
            continue
        places = sorted(
            set(
                session.scalars(
                    select(Reservation.location_id).where(
                        Reservation.tenant_id == tenant_id,
                        Reservation.commitment_id == commitment.id,
                        Reservation.status == "active",
                    )
                )
            )
        )
        movements.append(
            {
                "commitment_id": commitment.id,
                "item_id": commitment.item_id,
                "from_location_id": places[0]
                if len(places) == 1
                else commitment.location_id,
                "quantity": _plain(Decimal(line.quantity)),
            }
        )
    return movements


def require_matches_delivery(
    session: Session,
    tenant_id: str,
    outbound_delivery_id: str,
    counterparty_id: Any,
    movements: Any,
    *,
    lock: bool = False,
) -> OutboundDelivery:
    """A dispatch naming a planned delivery ships exactly what it carries."""
    delivery = _delivery(session, tenant_id, outbound_delivery_id, lock=lock)
    if delivery.shipment_id:
        raise InvalidOperation(code="outbound_delivery_shipped")
    if counterparty_id != delivery.customer_id:
        raise InvalidOperation(code="outbound_delivery_dispatch_mismatch")
    lines = _delivery_lines(session, tenant_id, [delivery.id])[delivery.id]
    picks = _picks(session, tenant_id, [line.id for line in lines])
    commitments = {
        commitment.id: commitment
        for commitment in session.scalars(
            select(Commitment).where(
                Commitment.tenant_id == tenant_id,
                Commitment.id.in_([line.commitment_id for line in lines]),
            )
        )
    }
    uses_picking = any(picks[line.id] for line in lines)
    expected: dict[str, Decimal] = {}
    for line in lines:
        commitment = commitments[line.commitment_id]
        held = _picked(picks[line.id])
        if commitment.status != "open":
            if held > ZERO:
                raise InvalidOperation(code="outbound_delivery_waiting_put_back")
            continue
        if uses_picking and held != Decimal(line.quantity):
            raise InvalidOperation(code="outbound_delivery_dispatch_not_picked")
        expected[commitment.id] = Decimal(line.quantity)
    if not expected:
        raise InvalidOperation(code="outbound_delivery_dispatch_mismatch")
    stated: dict[str, Decimal] = {}
    for raw in movements if isinstance(movements, list) else []:
        if not isinstance(raw, dict):
            raise InvalidOperation(code="outbound_delivery_dispatch_mismatch")
        commitment_id = str(raw.get("commitment_id") or "")
        if uses_picking and raw.get("from_location_id") != delivery.staging_location_id:
            raise InvalidOperation(code="outbound_delivery_dispatch_mismatch")
        try:
            quantity = decimal(raw.get("quantity"))
        except (ArithmeticError, ValueError, TypeError, InvalidOperation):
            raise InvalidOperation(code="outbound_delivery_dispatch_mismatch") from None
        stated[commitment_id] = stated.get(commitment_id, ZERO) + quantity
    if stated != expected:
        raise InvalidOperation(code="outbound_delivery_dispatch_mismatch")
    return delivery


def dispatch_details(session: Session, delivery: OutboundDelivery) -> dict[str, Any]:
    """What a shipment keeps from the delivery it executed: as stated."""
    statement = _statement(session, delivery)
    return {
        "outbound_delivery_id": delivery.id,
        "recipient_party_id": statement.get("recipient_party_id"),
        "address": statement.get("address") or {},
        "slot": statement.get("slot"),
    }


def _state(
    delivery: OutboundDelivery, lines: list[dict[str, Any]], uses_picking: bool
) -> str:
    if delivery.shipment_id:
        return "shipped"
    open_lines = [line for line in lines if line["promise_status"] == "open"]
    if not uses_picking:
        return "planned"
    if open_lines and all(
        Decimal(line["picked"]) == Decimal(line["planned"]) for line in open_lines
    ):
        return "picked"
    return "picking"


def _views(
    session: Session,
    tenant_id: str,
    deliveries: list[OutboundDelivery],
    *,
    detail: bool,
) -> list[dict[str, Any]]:
    ids = [delivery.id for delivery in deliveries]
    lines_of = _delivery_lines(session, tenant_id, ids)
    all_lines = [line for lines in lines_of.values() for line in lines]
    picks = _picks(session, tenant_id, [line.id for line in all_lines])
    commitments = {
        commitment.id: commitment
        for commitment in session.scalars(
            select(Commitment).where(
                Commitment.tenant_id == tenant_id,
                Commitment.id.in_({line.commitment_id for line in all_lines}),
            )
        )
    }
    items = {
        item.id: item
        for item in session.scalars(
            select(Item).where(
                Item.tenant_id == tenant_id,
                Item.id.in_(
                    {commitment.item_id for commitment in commitments.values()}
                ),
            )
        )
    }
    documents = {
        document_id: number
        for document_id, number in session.execute(
            select(Document.id, Document.number).where(
                Document.tenant_id == tenant_id,
                Document.id.in_(
                    {
                        commitment.document_id
                        for commitment in commitments.values()
                        if commitment.document_id
                    }
                ),
            )
        )
    }
    party_ids = {delivery.customer_id for delivery in deliveries} | {
        delivery.recipient_party_id
        for delivery in deliveries
        if delivery.recipient_party_id
    }
    parties = {
        party_id: name
        for party_id, name in session.execute(
            select(Party.id, Party.name).where(
                Party.tenant_id == tenant_id, Party.id.in_(party_ids)
            )
        )
    }
    locations = {
        location_id: name
        for location_id, name in session.execute(
            select(Location.id, Location.name).where(
                Location.tenant_id == tenant_id,
                Location.id.in_(
                    {
                        delivery.staging_location_id
                        for delivery in deliveries
                        if delivery.staging_location_id
                    }
                ),
            )
        )
    }
    sources = {
        source.id: source
        for source in session.scalars(
            select(SourceRecord).where(
                SourceRecord.tenant_id == tenant_id,
                SourceRecord.id.in_(
                    {delivery.source_record_id for delivery in deliveries}
                ),
            )
        )
    }
    shipped: dict[tuple[str, str], Decimal] = {}
    shipment_ids = [
        delivery.shipment_id for delivery in deliveries if delivery.shipment_id
    ]
    if shipment_ids:
        from reality.db.core import ShipmentPackage

        for shipment_id, commitment_id, quantity in session.execute(
            select(
                ShipmentPackage.shipment_id,
                Movement.commitment_id,
                func.sum(Movement.quantity),
            )
            .join(
                Movement,
                (Movement.tenant_id == ShipmentPackage.tenant_id)
                & (Movement.shipment_package_id == ShipmentPackage.id),
            )
            .where(
                ShipmentPackage.tenant_id == tenant_id,
                ShipmentPackage.shipment_id.in_(shipment_ids),
                Movement.type == "shipment",
            )
            .group_by(ShipmentPackage.shipment_id, Movement.commitment_id)
        ):
            shipped[(shipment_id, commitment_id)] = Decimal(quantity)
    moment = now()
    views = []
    for delivery in deliveries:
        statement = json.loads(sources[delivery.source_record_id].payload)
        lines = []
        for line in lines_of[delivery.id]:
            commitment = commitments[line.commitment_id]
            held = _picked(picks[line.id])
            row = {
                "line_id": line.id,
                "commitment_id": commitment.id,
                "item_id": commitment.item_id,
                "item": items[commitment.item_id].name
                if commitment.item_id in items
                else None,
                "unit": items[commitment.item_id].unit
                if commitment.item_id in items
                else None,
                "document_id": commitment.document_id,
                "document_number": documents.get(commitment.document_id),
                "promise_status": commitment.status,
                "planned": _plain(Decimal(line.quantity)),
                "picked": _plain(held),
                # Picked goods whose promise is off wait in staging to be put back.
                "to_put_back": _plain(held if commitment.status != "open" else ZERO),
                "shipped": _plain(
                    shipped.get((delivery.shipment_id, commitment.id), ZERO)
                    if delivery.shipment_id
                    else ZERO
                ),
            }
            if detail:
                row["movements"] = [
                    {
                        "kind": pick.kind,
                        "movement_id": movement.id,
                        "quantity": _plain(Decimal(movement.quantity)),
                        "from_location_id": movement.from_location_id,
                        "to_location_id": movement.to_location_id,
                        "lot_id": movement.lot_id,
                        "occurred_at": movement.occurred_at,
                    }
                    for pick, movement in picks[line.id]
                ]
            lines.append(row)
        uses_picking = any(picks[line.id] for line in lines_of[delivery.id])
        view = {
            "id": delivery.id,
            "customer_id": delivery.customer_id,
            "customer": parties.get(delivery.customer_id),
            "recipient_party_id": delivery.recipient_party_id,
            "recipient": parties.get(
                delivery.recipient_party_id or delivery.customer_id
            ),
            "address": statement.get("address") or {},
            "slot": statement.get("slot"),
            "note": statement.get("note") or "",
            "staging_location_id": delivery.staging_location_id,
            "staging_location": locations.get(delivery.staging_location_id),
            "shipment_id": delivery.shipment_id,
            "source_record_id": delivery.source_record_id,
            "created_at": delivery.created_at,
            "state": _state(delivery, lines, uses_picking),
            # A booked slot that closed before the delivery shipped; read, never stored.
            "slot_passed": bool(
                statement.get("slot")
                and not delivery.shipment_id
                and utc_datetime(statement["slot"]["until"]) < moment
            ),
            "lines": lines,
        }
        views.append(view)
    if detail:
        for view, delivery in zip(views, deliveries, strict=True):
            view["statements"] = _statements(session, tenant_id, delivery.id)
            view["dispatch"] = (
                None
                if delivery.shipment_id
                else {
                    "purpose": "customer_delivery",
                    "counterparty_id": delivery.customer_id,
                    "outbound_delivery_id": delivery.id,
                    "movements": _dispatch_movements(
                        session,
                        tenant_id,
                        delivery,
                        lines_of[delivery.id],
                        picks,
                        commitments,
                    ),
                }
            )
    return views


def _statements(
    session: Session, tenant_id: str, delivery_id: str
) -> list[dict[str, Any]]:
    """Every statement of the delivery, oldest first, as stated."""
    rows = []
    for source in session.scalars(
        select(SourceRecord)
        .where(
            SourceRecord.tenant_id == tenant_id,
            SourceRecord.source_system == SOURCE_SYSTEM,
            SourceRecord.source_type == SOURCE_TYPE,
            SourceRecord.external_id == delivery_id,
        )
        .order_by(SourceRecord.version)
    ):
        payload = json.loads(source.payload)
        rows.append(
            {
                "source_record_id": source.id,
                "version": source.version,
                "received_at": source.received_at,
                "recipient_party_id": payload.get("recipient_party_id"),
                "address": payload.get("address") or {},
                "slot": payload.get("slot"),
                "staging_location_id": payload.get("staging_location_id"),
                "lines": payload.get("lines") or [],
                "note": payload.get("note") or "",
            }
        )
    return rows


def outbound_deliveries(
    session: Session,
    tenant_id: str,
    *,
    customer_id: str | None = None,
    open_only: bool = False,
) -> list[dict[str, Any]]:
    """
    The company's planned deliveries, newest first.

    BUSINESS PURPOSE:
    The company's planned deliveries, newest first.

    BUSINESS RULE services.outbound_deliveries.outbound_deliveries.result:
    Return the selected outbound deliveries in the shared delivery-view format, preserving the requested status filter and result bound.
    """
    query = select(OutboundDelivery).where(OutboundDelivery.tenant_id == tenant_id)
    if customer_id:
        query = query.where(OutboundDelivery.customer_id == customer_id)
    if open_only:
        query = query.where(OutboundDelivery.shipment_id.is_(None))
    deliveries = list(
        session.scalars(
            query.order_by(OutboundDelivery.created_at.desc(), OutboundDelivery.id)
        )
    )
    # reality-rule: services.outbound_deliveries.outbound_deliveries.result
    return _views(session, tenant_id, deliveries, detail=False)


def outbound_delivery_detail(
    session: Session, tenant_id: str, outbound_delivery_id: str
) -> dict[str, Any]:
    """
    One planned delivery: its lines, picks, statements, shipment and dispatch.

    BUSINESS PURPOSE:
    One planned delivery: its lines, picks, statements, shipment and dispatch.

    BUSINESS RULE services.outbound_deliveries.outbound_delivery_detail.result:
    Return _views(session, tenant_id, [delivery], detail=True) [0], as prepared by the preceding checks and service calls.
    """
    delivery = _delivery(session, tenant_id, outbound_delivery_id)
    # reality-rule: services.outbound_deliveries.outbound_delivery_detail.result
    return _views(session, tenant_id, [delivery], detail=True)[0]
