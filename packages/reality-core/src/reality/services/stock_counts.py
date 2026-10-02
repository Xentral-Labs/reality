"""Stock counts: what a person counted at a location, and the differences posted (spec 307).

A count names one location and, per line, an item, its lot where the item is
lot-tracked, the counted quantity and when it was counted. The book quantity a
line is compared with is what the movements up to its counting time hold; it
is read, never stored, and movements after that time carry on unchanged, so a
location is never frozen for a count.

One reviewed confirmation records the count and posts every difference: a
gain as an adjustment into the location, a loss as an adjustment out of free
stock, and whatever free stock cannot cover scrapped from the location's
blocks with the count as the reason. Reservations a loss leaves uncovered are
named in the review; nothing releases them by itself.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from decimal import Decimal
from decimal import InvalidOperation as DecimalError
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from reality.db.core import (
    Commitment,
    Item,
    Location,
    Lot,
    Movement,
    Party,
    Reservation,
    SourceRecord,
    StockBlock,
    StockCount,
    StockCountLine,
    now,
    uid,
)
from reality.services.business_locks import lock_delivery_state
from reality.services.core import (
    InvalidOperation,
    NotFound,
    _require_business_mutation,
    _tenant_record,
    active_reserved,
    blocked_quantity,
    emit_business_event,
    record_movement,
    stock_by_identity,
    store_source_record,
)

ZERO = Decimal(0)
SOURCE_SYSTEM = "internal_stock_count"
SOURCE_TYPE = "stock_count"
LIMIT = Decimal(10) ** 14


def _plain(value: Decimal) -> str:
    return format(Decimal(value).normalize(), "f") if value else "0"


def _quantity(value: Any) -> Decimal:
    try:
        amount = Decimal(str(value).strip())
    except (DecimalError, ValueError):
        raise InvalidOperation(code="stock_count_quantity_invalid") from None
    if not amount.is_finite() or amount < 0 or amount >= LIMIT:
        raise InvalidOperation(code="stock_count_quantity_invalid")
    if amount != amount.quantize(Decimal("0.0001")):
        raise InvalidOperation(code="stock_count_quantity_invalid")
    return amount


def _moment(value: Any, default: datetime) -> datetime:
    if value in (None, ""):
        return default
    if isinstance(value, datetime):
        moment = value
    else:
        try:
            moment = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        except ValueError:
            raise InvalidOperation(code="stock_count_time_invalid") from None
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=UTC)
    if moment > default:
        raise InvalidOperation(code="stock_count_time_in_future")
    return moment.astimezone(UTC)


def book_as_of(
    session: Session,
    tenant_id: str,
    item_id: str,
    location_id: str,
    lot_id: str | None,
    at: datetime,
) -> Decimal:
    """What the movements up to `at` hold of an item, and its lot, at a location."""
    totals = []
    for column in (Movement.to_location_id, Movement.from_location_id):
        query = select(func.coalesce(func.sum(Movement.quantity), 0)).where(
            Movement.tenant_id == tenant_id,
            Movement.item_id == item_id,
            column == location_id,
            Movement.occurred_at <= at,
        )
        if lot_id:
            query = query.where(Movement.lot_id == lot_id)
        totals.append(Decimal(session.scalar(query) or 0))
    return totals[0] - totals[1]


def _location(session: Session, tenant_id: str, location_id: str) -> Location:
    location = session.scalar(
        select(Location).where(
            Location.tenant_id == tenant_id, Location.id == location_id
        )
    )
    if location is None or not location.is_active or not location.allows_stock:
        raise InvalidOperation(code="stock_count_location_not_stock")
    return location


def _lines(
    session: Session, tenant_id: str, raw: Any, moment: datetime
) -> list[dict[str, Any]]:
    """The stated lines, checked: item, lot where tracked, quantity and time."""
    if not isinstance(raw, list) or not raw:
        raise InvalidOperation(code="stock_count_lines_required")
    lines, seen = [], set()
    for entry in raw:
        if not isinstance(entry, dict):
            raise InvalidOperation(code="stock_count_lines_required")
        item = session.scalar(
            select(Item).where(
                Item.tenant_id == tenant_id,
                Item.id == str(entry.get("item_id") or ""),
            )
        )
        if item is None:
            raise InvalidOperation(code="stock_count_item_not_found")
        if item.item_type != "stocked":
            raise InvalidOperation(code="stock_count_item_not_stocked")
        if item.tracking_type == "serial":
            raise InvalidOperation(code="stock_count_serial_item")
        lot_id = str(entry.get("lot_id") or "") or None
        if item.tracking_type == "lot" and not lot_id:
            raise InvalidOperation(code="stock_count_lot_required")
        if lot_id:
            lot = session.scalar(
                select(Lot).where(Lot.tenant_id == tenant_id, Lot.id == lot_id)
            )
            if lot is None or lot.item_id != item.id or item.tracking_type != "lot":
                raise InvalidOperation(code="stock_count_lot_not_for_item")
        if (item.id, lot_id) in seen:
            raise InvalidOperation(code="stock_count_line_twice")
        seen.add((item.id, lot_id))
        lines.append(
            {
                "item": item,
                "lot_id": lot_id,
                "counted": _quantity(entry.get("counted_quantity", "")),
                "counted_at": _moment(entry.get("counted_at"), moment),
            }
        )
    return lines


def _open_blocks(
    session: Session, tenant_id: str, item_id: str, location_id: str, lot_id: str | None
) -> list[tuple[StockBlock, Decimal]]:
    """The location's open blocks of an item and lot, oldest first, with what they hold."""
    from reality.services.stock_blocks import _open_quantity, _resolutions

    blocks = list(
        session.scalars(
            select(StockBlock)
            .where(
                StockBlock.tenant_id == tenant_id,
                StockBlock.item_id == item_id,
                StockBlock.location_id == location_id,
                StockBlock.lot_id.is_(None)
                if lot_id is None
                else StockBlock.lot_id == lot_id,
            )
            .order_by(StockBlock.created_at, StockBlock.id)
        )
    )
    resolutions = _resolutions(session, tenant_id, [block.id for block in blocks])
    return [
        (block, held)
        for block in blocks
        if (held := _open_quantity(block, resolutions[block.id])) > ZERO
    ]


def _assess(
    session: Session,
    tenant_id: str,
    location: Location,
    lines: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Each line's book, difference, and where a loss comes from, as of now."""
    assessed = []
    for line in lines:
        item = line["item"]
        book = book_as_of(
            session, tenant_id, item.id, location.id, line["lot_id"], line["counted_at"]
        )
        difference = line["counted"] - book
        from_free = from_blocks = ZERO
        if difference < 0:
            loss = -difference
            physical = stock_by_identity(
                session, tenant_id, item.id, location.id, lot_id=line["lot_id"]
            )
            blocked = blocked_quantity(
                session, tenant_id, item.id, location.id, lot_id=line["lot_id"]
            )
            if loss > physical:
                # Goods left after the count; the rest is not there to write off.
                raise InvalidOperation(code="stock_count_loss_exceeds_stock")
            from_free = min(loss, max(ZERO, physical - blocked))
            from_blocks = loss - from_free
        assessed.append(
            {
                **line,
                "book": book,
                "difference": difference,
                "from_free": from_free,
                "from_blocks": from_blocks,
            }
        )
    return assessed


def _uncovered(
    session: Session, tenant_id: str, location: Location, assessed: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Per item, the reservations here that the posted differences leave uncovered."""
    by_item: dict[str, dict[str, Any]] = {}
    for line in assessed:
        entry = by_item.setdefault(
            line["item"].id, {"item": line["item"], "difference": ZERO}
        )
        entry["difference"] += line["difference"]
    result = []
    for item_id, entry in by_item.items():
        if entry["difference"] >= 0:
            continue
        physical_after = (
            stock_by_identity(session, tenant_id, item_id, location.id)
            + entry["difference"]
        )
        reserved = active_reserved(session, tenant_id, item_id, location.id)
        if reserved <= physical_after:
            continue
        rows = session.execute(
            select(
                Reservation.id,
                Reservation.commitment_id,
                Reservation.quantity,
                Party.name,
            )
            .join(
                Commitment,
                (Commitment.tenant_id == Reservation.tenant_id)
                & (Commitment.id == Reservation.commitment_id),
            )
            .outerjoin(
                Party,
                (Party.tenant_id == Commitment.tenant_id)
                & (Party.id == Commitment.to_party_id),
            )
            .where(
                Reservation.tenant_id == tenant_id,
                Reservation.item_id == item_id,
                Reservation.location_id == location.id,
                Reservation.status == "active",
            )
            .order_by(Reservation.id)
        ).all()
        result.append(
            {
                "item_id": item_id,
                "item": entry["item"].name,
                "reserved": _plain(reserved),
                "physical_after": _plain(physical_after),
                "reservations": [
                    {
                        "reservation_id": row.id,
                        "commitment_id": row.commitment_id,
                        "quantity": _plain(row.quantity),
                        "customer": row.name or "",
                    }
                    for row in rows
                ],
            }
        )
    return result


def _line_view(line: dict[str, Any]) -> dict[str, Any]:
    return {
        "item_id": line["item"].id,
        "item": line["item"].name,
        "unit": line["item"].unit,
        "lot_id": line["lot_id"],
        "counted_at": line["counted_at"].isoformat(),
        "book": _plain(line["book"]),
        "counted": _plain(line["counted"]),
        "difference": _plain(line["difference"]),
        "from_free": _plain(line["from_free"]),
        "from_blocks": _plain(line["from_blocks"]),
    }


def review_stock_count(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any]]:
    """The arguments a confirmation executes and what the person is shown.

    The counting time of a line without one is fixed now, so the confirmation
    compares with the same book; the books the review saw travel along, and a
    confirmation after any of them changed is refused.
    """
    location = _location(session, tenant_id, str(arguments.get("location_id") or ""))
    lines = _lines(session, tenant_id, arguments.get("lines"), now())
    assessed = _assess(session, tenant_id, location, lines)
    note = str(arguments.get("note") or "").strip()
    normalized = {
        "location_id": location.id,
        "note": note,
        "lines": [
            {
                "item_id": line["item"].id,
                **({"lot_id": line["lot_id"]} if line["lot_id"] else {}),
                "counted_quantity": _plain(line["counted"]),
                "counted_at": line["counted_at"].isoformat(),
            }
            for line in assessed
        ],
        "reviewed": [_plain(line["book"]) for line in assessed],
    }
    preview = {
        "location_id": location.id,
        "location": location.name,
        "note": note,
        "lines": [_line_view(line) for line in assessed],
        "uncovered": _uncovered(session, tenant_id, location, assessed),
    }
    return normalized, preview


def record_stock_count(
    session: Session,
    tenant_id: str,
    location_id: str,
    lines: list[dict[str, Any]],
    note: str = "",
    *,
    reviewed: list[str] | None = None,
    action_id: str | None = None,
    _commit: bool = True,
) -> StockCount:
    """Record a count and post its differences in one transaction."""
    from reality.services.stock_blocks import scrap_stock_block

    _require_business_mutation(session, tenant_id, "record_stock_count")
    lock_delivery_state(session, tenant_id)
    location = _location(session, tenant_id, location_id)
    checked = _lines(session, tenant_id, lines, now())
    statement = {
        "location_id": location.id,
        "note": str(note or "").strip(),
        "lines": [
            {
                "item_id": line["item"].id,
                "lot_id": line["lot_id"],
                "counted_quantity": _plain(line["counted"]),
                "counted_at": line["counted_at"].isoformat(),
            }
            for line in checked
        ],
        "statement_id": action_id or uid("stm"),
    }
    count_id = uid("cnt")
    source, inserted, _ = store_source_record(
        session,
        tenant_id,
        SOURCE_SYSTEM,
        SOURCE_TYPE,
        action_id or count_id,
        statement,
    )
    if not inserted:
        # The same confirmation again: it is already recorded.
        existing = session.scalar(
            select(StockCount).where(
                StockCount.tenant_id == tenant_id,
                StockCount.source_record_id == source.id,
            )
        )
        if existing is not None:
            return existing
    assessed = _assess(session, tenant_id, location, checked)
    if reviewed is not None and [_plain(line["book"]) for line in assessed] != list(
        reviewed
    ):
        raise InvalidOperation(code="stock_count_changed_since_review")
    count = StockCount(
        id=count_id,
        tenant_id=tenant_id,
        location_id=location.id,
        note=statement["note"],
        source_record_id=source.id,
    )
    session.add(count)
    session.flush()
    reason = f"count {count.id}" + (
        f": {statement['note']}" if statement["note"] else ""
    )
    posted = []
    for line in assessed:
        item = line["item"]
        movement = None
        scrapped: list[str] = []
        if line["difference"] > 0:
            movement = record_movement(
                session,
                tenant_id,
                "adjustment",
                item.id,
                line["difference"],
                to_location_id=location.id,
                lot_id=line["lot_id"],
                reason=reason,
                action_id=action_id,
                _commit=False,
            )
        elif line["difference"] < 0:
            if line["from_free"] > 0:
                movement = record_movement(
                    session,
                    tenant_id,
                    "adjustment",
                    item.id,
                    line["from_free"],
                    from_location_id=location.id,
                    lot_id=line["lot_id"],
                    reason=reason,
                    action_id=action_id,
                    _commit=False,
                )
            rest = line["from_blocks"]
            for block, held in _open_blocks(
                session, tenant_id, item.id, location.id, line["lot_id"]
            ):
                if rest <= 0:
                    break
                taken = min(rest, held)
                result = scrap_stock_block(
                    session,
                    tenant_id,
                    block.id,
                    taken,
                    reason=reason,
                    action_id=action_id,
                    _commit=False,
                )
                scrapped.append(result["movement_id"])
                rest -= taken
            if rest > 0:
                raise InvalidOperation(code="stock_count_loss_exceeds_stock")
        row = StockCountLine(
            id=uid("cnl"),
            tenant_id=tenant_id,
            stock_count_id=count.id,
            item_id=item.id,
            lot_id=line["lot_id"],
            counted_quantity=line["counted"],
            counted_at=line["counted_at"],
            movement_id=movement.id if movement else None,
        )
        session.add(row)
        posted.append(
            {
                **_line_view(line),
                "line_id": row.id,
                "movement_id": row.movement_id,
                "scrap_movement_ids": scrapped,
            }
        )
    session.flush()
    emit_business_event(
        session,
        tenant_id,
        "stock_count.posted",
        "stock_count",
        count.id,
        {"location_id": location.id, "note": count.note, "lines": posted},
        source_record_id=source.id,
        action_id=action_id,
        correlation_id=action_id,
    )
    if _commit:
        session.commit()
    return count


def stock_counts(
    session: Session, tenant_id: str, *, location_id: str | None = None
) -> list[dict[str, Any]]:
    """The company's counts, of one location or all, newest first."""
    query = (
        select(StockCount, Location.name)
        .join(
            Location,
            (Location.tenant_id == StockCount.tenant_id)
            & (Location.id == StockCount.location_id),
        )
        .where(StockCount.tenant_id == tenant_id)
    )
    if location_id:
        query = query.where(StockCount.location_id == location_id)
    rows = session.execute(
        query.order_by(StockCount.created_at.desc(), StockCount.id)
    ).all()
    counts = {
        identity: total
        for identity, total in session.execute(
            select(StockCountLine.stock_count_id, func.count())
            .where(
                StockCountLine.tenant_id == tenant_id,
                StockCountLine.stock_count_id.in_([row[0].id for row in rows]),
            )
            .group_by(StockCountLine.stock_count_id)
        )
    }
    return [
        {
            "id": count.id,
            "location_id": count.location_id,
            "location": name,
            "note": count.note,
            "created_at": count.created_at,
            "lines": counts.get(count.id, 0),
            "source_record_id": count.source_record_id,
        }
        for count, name in rows
    ]


def stock_count_detail(
    session: Session, tenant_id: str, count_id: str
) -> dict[str, Any]:
    """One count: its lines as counted, and what posting them recorded."""
    count = session.scalar(
        select(StockCount).where(
            StockCount.tenant_id == tenant_id, StockCount.id == count_id
        )
    )
    if count is None:
        raise NotFound(code="stock_count_not_found")
    location = _tenant_record(session, Location, tenant_id, count.location_id)
    event = session.scalar(
        select(SourceRecord.payload).where(
            SourceRecord.tenant_id == tenant_id,
            SourceRecord.id == count.source_record_id,
        )
    )
    from reality.db.core import BusinessEvent

    posted = session.scalar(
        select(BusinessEvent.payload).where(
            BusinessEvent.tenant_id == tenant_id,
            BusinessEvent.event_type == "stock_count.posted",
            BusinessEvent.subject_id == count.id,
        )
    )
    lines = json.loads(posted)["lines"] if posted else []
    return {
        "id": count.id,
        "location_id": location.id,
        "location": location.name,
        "note": count.note,
        "created_at": count.created_at,
        "source_record_id": count.source_record_id,
        "statement": json.loads(event) if event else None,
        "lines": lines,
    }
