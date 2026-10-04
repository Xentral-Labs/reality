"""Spec 305: serving backorders when goods arrive, and available-to-promise.

Nothing here is stored. The serving order, what is still waiting and what can be
promised are read from commitments, movements, reservations, blocks and supply
assignments when they are asked. What a person decides becomes ordinary
reservations under one confirmed proposal.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from decimal import InvalidOperation as DecimalError
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from reality.db.core import Commitment, DocumentLine, Item, Location, Party
from reality.domain.units import promise_held_unit
from reality.services.core import (
    InvalidOperation,
    _tenant_record,
    active_commitment_hold,
    active_party_delivery_hold,
    active_reserved,
    blocked_quantity,
    commitment_terms,
    reserve,
    stock_at,
)

ZERO = Decimal(0)


def _plain(value: Decimal) -> str:
    return format(value.normalize(), "f") if value else "0"


def _quantity(value: Any) -> Decimal:
    try:
        amount = Decimal(str(value).strip())
    except (DecimalError, ValueError):
        raise InvalidOperation(code="backorder_serving_line_quantity_invalid") from None
    if not amount.is_finite() or amount < 0:
        raise InvalidOperation(code="backorder_serving_line_quantity_invalid")
    return amount


def _day(value: datetime | None) -> str | None:
    return value.date().isoformat() if value else None


def _place(
    session: Session, tenant_id: str, item_id: str, location_id: str
) -> tuple[Item, Location]:
    item = session.scalar(
        select(Item).where(Item.tenant_id == tenant_id, Item.id == item_id)
    )
    if item is None:
        raise InvalidOperation(code="backorder_serving_item_not_found")
    if item.tracking_type != "none":
        # A lot or serial reservation names an identity; choosing it is an
        # allocation policy Reality does not have (spec 304 non-goal).
        raise InvalidOperation(code="backorder_serving_tracked_item")
    location = session.scalar(
        select(Location).where(
            Location.tenant_id == tenant_id, Location.id == location_id
        )
    )
    if location is None or not location.is_active or not location.allows_stock:
        raise InvalidOperation(code="backorder_serving_location_not_stock")
    return item, location


def free_at(
    session: Session, tenant_id: str, item_id: str, location_id: str
) -> Decimal:
    """What lies at the location and is neither reserved nor blocked."""
    return max(
        ZERO,
        stock_at(session, tenant_id, item_id, location_id)
        - active_reserved(session, tenant_id, item_id, location_id)
        - blocked_quantity(session, tenant_id, item_id, location_id),
    )


def _held_elsewhere(
    session: Session, tenant_id: str, rows: list[Commitment], item: Item
) -> set[str]:
    """Promises held in their line's unit (recorded before spec 301), not in stock units."""
    line_ids = {row.document_line_id for row in rows if row.document_line_id}
    lines = (
        {
            line.id: line
            for line in session.scalars(
                select(DocumentLine).where(
                    DocumentLine.tenant_id == tenant_id, DocumentLine.id.in_(line_ids)
                )
            )
        }
        if line_ids
        else {}
    )
    return {
        row.id
        for row in rows
        if promise_held_unit(row.unit, lines.get(row.document_line_id or ""), item.unit)
        != item.unit
    }


def waiting_promises(
    session: Session,
    tenant_id: str,
    item_id: str,
    location_id: str,
    supplier_commitment_id: str | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """
    The promises waiting for the item here, in serving order, and those on hold.

    A promise waits when it is an open customer delivery of the item with an
    open quantity it has not reserved. Those the named purchase is assigned to
    come first, in the order they were assigned, wherever they are held; then
    the others held at the location, by due date, then by when they were made.

    BUSINESS PURPOSE:
    The promises waiting for the item here, in serving order, and those on hold.

    BUSINESS RULE services.backorders.waiting_promises.refusal-21:
    IF a supplier promise was selected but is not a supplier delivery for this item:
        Refuse with backorder_serving_purchase_not_for_item.

    BUSINESS RULE services.backorders.waiting_promises.result:
    Return waiting, held, as prepared by the preceding checks and service calls.
    """
    from reality.services.supply_assignments import _effective_rows

    assigned_order: dict[str, int] = {}
    if supplier_commitment_id:
        supplier = _tenant_record(
            session, Commitment, tenant_id, supplier_commitment_id
        )
        # reality-rule: services.backorders.waiting_promises.refusal-21
        if supplier.type != "supplier_delivery" or supplier.item_id != item_id:
            raise InvalidOperation(code="backorder_serving_purchase_not_for_item")
        for row in _effective_rows(
            session, tenant_id, supplier_id=supplier_commitment_id
        ):
            if row.customer_commitment_id:
                assigned_order.setdefault(
                    row.customer_commitment_id, len(assigned_order)
                )
    query = select(Commitment).where(
        Commitment.tenant_id == tenant_id,
        Commitment.type == "customer_delivery",
        Commitment.status == "open",
        Commitment.item_id == item_id,
    )
    candidates = [
        row
        for row in session.scalars(query)
        if row.location_id == location_id or row.id in assigned_order
    ]
    terms = commitment_terms(session, tenant_id, [row.id for row in candidates])
    item = _tenant_record(session, Item, tenant_id, item_id)
    other_unit = _held_elsewhere(session, tenant_id, candidates, item)
    parties = {
        party.id: party.name
        for party in session.scalars(
            select(Party).where(
                Party.tenant_id == tenant_id,
                Party.id.in_(
                    {row.to_party_id for row in candidates if row.to_party_id}
                ),
            )
        )
    }
    far = datetime.max.replace(tzinfo=UTC)
    waiting, held = [], []
    for row in sorted(
        candidates,
        key=lambda row: (
            0 if row.id in assigned_order else 1,
            assigned_order.get(row.id, 0),
            # The stated date, revisions included.
            terms[row.id].due_at or far,
            row.created_at,
            row.id,
        ),
    ):
        need = terms[row.id].open - terms[row.id].reserved
        if need <= 0:
            continue
        entry = {
            "commitment_id": row.id,
            "customer": parties.get(row.to_party_id or "", ""),
            "due_at": _day(terms[row.id].due_at),
            "need": need,
            "why": "assigned" if row.id in assigned_order else "due",
        }
        hold = active_commitment_hold(session, tenant_id, row.id)
        if hold:
            held.append({**entry, "hold_reason": hold.reason_code})
        elif row.to_party_id and active_party_delivery_hold(
            session, tenant_id, row.to_party_id
        ):
            # Reserving is allowed but shipping is not; it is not served ahead.
            held.append({**entry, "hold_reason": "party_delivery_hold"})
        elif row.id in other_unit:
            held.append({**entry, "hold_reason": "held_in_line_unit"})
        else:
            waiting.append(entry)
    # reality-rule: services.backorders.waiting_promises.result
    return waiting, held


def _fingerprint(
    available: Decimal, waiting: list[dict[str, Any]], held: list[dict[str, Any]]
) -> dict[str, Any]:
    """What the person saw: a confirmation after any of it changed is refused."""
    return {
        "available": _plain(available),
        "waiting": [[row["commitment_id"], _plain(row["need"])] for row in waiting],
        "held": [row["commitment_id"] for row in held],
    }


def review_backorder_serving(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any]]:
    """
    The lines a confirmation reserves and what the person is shown.

    Without stated lines the available quantity is given out in serving order.
    Stated lines are checked instead: only waiting promises, none beyond its
    need, all together not beyond what is available.

    BUSINESS PURPOSE:
    The lines a confirmation reserves and what the person is shown.

    BUSINESS RULE services.backorders.review_backorder_serving.refusal-41:
    IF the plan reserves no positive quantity:
        Refuse with backorder_serving_nothing_to_serve.

    BUSINESS RULE services.backorders.review_backorder_serving.refusal-26:
    IF the supplied reservation quantities are not a list:
        Refuse with backorder_serving_line_quantity_invalid.

    BUSINESS RULE services.backorders.review_backorder_serving.refusal-38:
    IF the sum of planned reservations exceeds available stock:
        Refuse with backorder_serving_exceeds_available.

    BUSINESS RULE services.backorders.review_backorder_serving.refusal-32:
    IF a selected promise is not waiting for stock or is selected more than once:
        Refuse with backorder_serving_line_not_waiting.

    BUSINESS RULE services.backorders.review_backorder_serving.refusal-35:
    IF a selected reservation quantity exceeds that promise's uncovered need:
        Refuse with backorder_serving_line_exceeds_need.

    BUSINESS RULE services.backorders.review_backorder_serving.result:
    Return normalized, preview, as prepared by the preceding checks and service calls.
    """
    item, location = _place(
        session,
        tenant_id,
        str(arguments.get("item_id") or ""),
        str(arguments.get("location_id") or ""),
    )
    purchase = str(arguments.get("supplier_commitment_id") or "") or None
    waiting, held = waiting_promises(session, tenant_id, item.id, location.id, purchase)
    available = free_at(session, tenant_id, item.id, location.id)
    stated = arguments.get("lines")
    if stated is None:
        left = available
        quantities = {}
        for entry in waiting:
            quantities[entry["commitment_id"]] = min(entry["need"], left)
            left -= quantities[entry["commitment_id"]]
    else:
        # reality-rule: services.backorders.review_backorder_serving.refusal-26
        if not isinstance(stated, list):
            raise InvalidOperation(code="backorder_serving_line_quantity_invalid")
        needs = {entry["commitment_id"]: entry["need"] for entry in waiting}
        quantities = {}
        for line in stated:
            identity = str((line or {}).get("commitment_id") or "")
            # reality-rule: services.backorders.review_backorder_serving.refusal-32
            if identity not in needs or identity in quantities:
                raise InvalidOperation(code="backorder_serving_line_not_waiting")
            amount = _quantity(line.get("quantity", ""))
            # reality-rule: services.backorders.review_backorder_serving.refusal-35
            if amount > needs[identity]:
                raise InvalidOperation(code="backorder_serving_line_exceeds_need")
            quantities[identity] = amount
        # reality-rule: services.backorders.review_backorder_serving.refusal-38
        if sum(quantities.values(), ZERO) > available:
            raise InvalidOperation(code="backorder_serving_exceeds_available")
    reserving = sum(quantities.values(), ZERO)
    # reality-rule: services.backorders.review_backorder_serving.refusal-41
    if reserving <= 0:
        raise InvalidOperation(code="backorder_serving_nothing_to_serve")
    lines = [
        {
            **entry,
            "need": _plain(entry["need"]),
            "quantity": _plain(quantities.get(entry["commitment_id"], ZERO)),
        }
        for entry in waiting
    ]
    normalized = {
        "item_id": item.id,
        "location_id": location.id,
        **({"supplier_commitment_id": purchase} if purchase else {}),
        "lines": [
            {"commitment_id": identity, "quantity": _plain(amount)}
            for identity, amount in quantities.items()
            if amount > 0
        ],
        "reviewed": _fingerprint(available, waiting, held),
    }
    preview = {
        "item": item.name,
        "unit": item.unit,
        "location": location.name,
        "available": _plain(available),
        "reserving": _plain(reserving),
        "free_after": _plain(available - reserving),
        "lines": lines,
        "held": [{**entry, "need": _plain(entry["need"])} for entry in held],
    }
    # reality-rule: services.backorders.review_backorder_serving.result
    return normalized, preview


def serve_backorders(
    session: Session,
    tenant_id: str,
    item_id: str,
    location_id: str,
    lines: list[dict[str, Any]],
    *,
    supplier_commitment_id: str | None = None,
    reviewed: dict[str, Any] | None = None,
    action_id: str | None = None,
    _commit: bool = True,
) -> dict[str, Any]:
    """
    Reserve the confirmed lines; refuse all of them if anything changed.

    Under the delivery lock, the stock, the waiting promises and the holds are
    read again and compared with what the review showed.

    BUSINESS PURPOSE:
    Reserve the confirmed lines; refuse all of them if anything changed.

    BUSINESS RULE services.backorders.serve_backorders.refusal-27:
    IF a prior reviewed plan was supplied and the current plan differs:
        Refuse with backorder_serving_changed_since_review.

    BUSINESS RULE services.backorders.serve_backorders.refusal-62:
    IF the recorded reservation quantity differs from the reviewed line quantity or no reservation was produced:
        Refuse with backorder_serving_changed_since_review.

    BUSINESS RULE services.backorders.serve_backorders.refusal-41:
    IF execution finds that a selected line is no longer waiting, exceeds current need, exceeds available stock or has no quantity to serve:
        Refuse with backorder_serving_changed_since_review.

    BUSINESS RULE services.backorders.serve_backorders.result:
    Return the current result with item_id, location_id, reservations, records.

    BUSINESS RULE services.backorders.serve_backorders.effect-50:
    Run the shared review backorder serving check and use its normalized inputs and current review evidence. Inspect that called function for its detailed eligibility rules.
    """
    from reality.services.business_locks import lock_delivery_state
    from reality.services.core import _require_business_mutation
    from reality.services.intake import _invoke, require_scoped_intent

    _require_business_mutation(session, tenant_id, "serve_backorders")
    require_scoped_intent("serve_backorders", locals())
    lock_delivery_state(session, tenant_id)
    if reviewed is not None:
        item, location = _place(session, tenant_id, item_id, location_id)
        waiting, held = waiting_promises(
            session, tenant_id, item.id, location.id, supplier_commitment_id
        )
        current = _fingerprint(
            free_at(session, tenant_id, item.id, location.id), waiting, held
        )
        # reality-rule: services.backorders.serve_backorders.refusal-27
        if current != reviewed:
            raise InvalidOperation(code="backorder_serving_changed_since_review")
    try:
        # reality-rule: services.backorders.serve_backorders.effect-50
        normalized, _ = review_backorder_serving(
            session,
            tenant_id,
            {
                "item_id": item_id,
                "location_id": location_id,
                "supplier_commitment_id": supplier_commitment_id,
                "lines": lines,
            },
        )
    except InvalidOperation as error:
        # reality-rule: services.backorders.serve_backorders.refusal-41
        if error.code in {
            "backorder_serving_line_not_waiting",
            "backorder_serving_line_exceeds_need",
            "backorder_serving_exceeds_available",
            "backorder_serving_nothing_to_serve",
        }:
            raise InvalidOperation(
                code="backorder_serving_changed_since_review"
            ) from None
        raise
    reservations = []
    for line in normalized["lines"]:
        result = _invoke(
            "reserve", reserve,
            session,
            tenant_id,
            commitment_id=line["commitment_id"],
            quantity=line["quantity"],
            location_id=location_id,
            action_id=action_id,
            _commit=False,
        )
        # reality-rule: services.backorders.serve_backorders.refusal-62
        if result.reserved != Decimal(line["quantity"]) or result.reservation is None:
            session.rollback()
            raise InvalidOperation(code="backorder_serving_changed_since_review")
        reservations.append(
            {
                "reservation_id": result.reservation.id,
                "commitment_id": line["commitment_id"],
                "quantity": line["quantity"],
            }
        )
    if _commit:
        session.commit()
    # reality-rule: services.backorders.serve_backorders.result
    return {
        "item_id": item_id,
        "location_id": location_id,
        "reservations": reservations,
        "records": [
            {"family": "reservation", "id": row["reservation_id"]}
            for row in reservations
        ],
    }


def available_to_promise(
    session: Session, tenant_id: str, item_id: str
) -> dict[str, Any]:
    """
    From when, and how much, the item can be promised, purchase by purchase.

    Free now is what lies in stock less reservations and blocks, less the
    waiting need that neither a reservation nor supply still to come covers.
    Each open purchase then adds, on its stated date, what its customer
    assignments do not still expect. Read when asked; never stored.

    BUSINESS PURPOSE:
    From when, and how much, the item can be promised, purchase by purchase.

    BUSINESS RULE services.backorders.available_to_promise.result:
    Return the current result with item_id, item, unit, now, purchases, not_in_stock_unit.
    """
    from reality.services.supply_assignments import _effective_rows, assignment_split

    item = _tenant_record(session, Item, tenant_id, item_id)
    promises = list(
        session.scalars(
            select(Commitment).where(
                Commitment.tenant_id == tenant_id,
                Commitment.item_id == item.id,
                Commitment.status == "open",
                Commitment.type.in_(("customer_delivery", "supplier_delivery")),
            )
        )
    )
    # A promise still held in its line's unit cannot be added to stock units.
    other_unit = _held_elsewhere(session, tenant_id, promises, item)
    promises = [row for row in promises if row.id not in other_unit]
    terms = commitment_terms(session, tenant_id, [row.id for row in promises])
    need = {
        row.id: max(ZERO, terms[row.id].open - terms[row.id].reserved)
        for row in promises
        if row.type == "customer_delivery"
    }
    purchases = sorted(
        (
            row
            for row in promises
            if row.type == "supplier_delivery" and terms[row.id].open > 0
        ),
        key=lambda row: (
            terms[row.id].due_at or datetime.max.replace(tzinfo=UTC),
            row.created_at,
            row.id,
        ),
    )
    split = assignment_split(session, tenant_id, {row.id for row in purchases})
    open_purchases = {row.id for row in purchases}
    to_come_for: dict[str, Decimal] = {}
    to_come_of: dict[str, Decimal] = {}
    for row in _effective_rows(session, tenant_id):
        if (
            row.supplier_commitment_id not in open_purchases
            or row.customer_commitment_id not in need
        ):
            continue
        # Supply still to come counts for a promise only up to what it still
        # needs: once it is reserved or delivered, the rest is free again.
        still = min(
            split.get(row.id, (ZERO, ZERO))[1],
            need[row.customer_commitment_id]
            - to_come_for.get(row.customer_commitment_id, ZERO),
        )
        to_come_for[row.customer_commitment_id] = (
            to_come_for.get(row.customer_commitment_id, ZERO) + still
        )
        to_come_of[row.supplier_commitment_id] = (
            to_come_of.get(row.supplier_commitment_id, ZERO) + still
        )
    uncovered = sum(
        (max(ZERO, value - to_come_for.get(key, ZERO)) for key, value in need.items()),
        ZERO,
    )
    physical = stock_at(session, tenant_id, item.id)
    reserved = active_reserved(session, tenant_id, item.id)
    blocked = blocked_quantity(session, tenant_id, item.id)
    free = physical - reserved - blocked - uncovered
    parties = {
        party.id: party.name
        for party in session.scalars(
            select(Party).where(
                Party.tenant_id == tenant_id,
                Party.id.in_(
                    {row.from_party_id for row in purchases if row.from_party_id}
                ),
            )
        )
    }
    today = datetime.now(UTC)
    total = free
    rows = []
    for row in purchases:
        open_quantity = terms[row.id].open
        due_at = terms[row.id].due_at
        assigned = min(open_quantity, to_come_of.get(row.id, ZERO))
        adds = open_quantity - assigned
        total += adds
        rows.append(
            {
                "commitment_id": row.id,
                "supplier": parties.get(row.from_party_id or "", ""),
                "due_at": _day(due_at),
                "overdue": bool(due_at and due_at < today),
                "open": _plain(open_quantity),
                "assigned_to_come": _plain(assigned),
                "adds": _plain(adds),
                "total": _plain(total),
            }
        )
    # reality-rule: services.backorders.available_to_promise.result
    return {
        "item_id": item.id,
        "item": item.name,
        "unit": item.unit,
        "now": {
            "physical": _plain(physical),
            "reserved": _plain(reserved),
            "blocked": _plain(blocked),
            "waiting_uncovered": _plain(uncovered),
            "free": _plain(free),
        },
        "purchases": rows,
        "not_in_stock_unit": sorted(other_unit),
    }
