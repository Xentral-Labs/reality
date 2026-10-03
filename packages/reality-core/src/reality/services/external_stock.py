"""External stock statements: stock someone outside states, compared not taken over (spec 344).

A 3PL's stock report or a shop's stock level names, per item and location, how
much is there at a stated time. It is kept as stated and never moves stock.
The latest statement per item and location is compared, when read, with what
Reality's movements hold there at that same time; a corrected movement and its
compensation are left out, as for a stock count (spec 307). A difference is the
finding `external_stock_differs`; a person resolves it, by a stock count dated
at the statement's time or by recording the movement that is missing, and a
newer statement that matches ends it too.
"""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime, timedelta
from decimal import Decimal
from decimal import InvalidOperation as DecimalError
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from reality.db.core import (
    ExternalStockStatement,
    Item,
    Location,
    Movement,
    MovementCorrection,
    Party,
    SourceRecord,
    now,
    uid,
)
from reality.services.core import InvalidOperation, NotFound, utc_datetime

ZERO = Decimal(0)
SOURCE_SYSTEM = "internal_external_stock"
SOURCE_TYPE = "external_stock_statement"
LIMIT = Decimal(10) ** 14
# A stated time may lie this far ahead of the server clock (clock skew).
FUTURE_TOLERANCE = timedelta(minutes=5)
FIELDS = {"lines", "reporter_party_id", "note"}
LINE_FIELDS = {"item_id", "location_id", "quantity", "stated_at"}


def _plain(value: Decimal) -> str:
    return f"{Decimal(value).normalize():f}"


def _quantity(value: Any) -> Decimal:
    try:
        quantity = Decimal(str(value).strip())
    except (DecimalError, ValueError) as error:
        raise InvalidOperation(code="external_stock_quantity_invalid") from error
    if not quantity.is_finite() or quantity < ZERO or quantity >= LIMIT:
        raise InvalidOperation(code="external_stock_quantity_invalid")
    if quantity.as_tuple().exponent < -4:
        raise InvalidOperation(code="external_stock_quantity_invalid")
    return quantity


def _stated_at(value: Any, default: datetime) -> datetime:
    if value in (None, ""):
        return default
    try:
        stated = utc_datetime(value)
    except InvalidOperation as error:
        raise InvalidOperation(code="external_stock_time_invalid") from error
    if stated is None:
        return default
    if stated > now() + FUTURE_TOLERANCE:
        raise InvalidOperation(code="external_stock_time_future")
    return stated


def _item(session: Session, tenant_id: str, item_id: Any) -> Item:
    item = session.scalar(
        select(Item).where(Item.tenant_id == tenant_id, Item.id == str(item_id or ""))
    )
    if item is None:
        raise NotFound(code="item_not_found")
    if item.item_type != "stocked":
        raise InvalidOperation(code="external_stock_item_not_stocked")
    return item


def _location(session: Session, tenant_id: str, location_id: Any) -> Location:
    location = session.scalar(
        select(Location).where(
            Location.tenant_id == tenant_id, Location.id == str(location_id or "")
        )
    )
    if location is None or not location.is_active or not location.allows_stock:
        raise InvalidOperation(code="external_stock_location_not_stock")
    return location


def _reporter(session: Session, tenant_id: str, party_id: Any) -> Party | None:
    if party_id in (None, ""):
        return None
    party = session.scalar(
        select(Party).where(Party.tenant_id == tenant_id, Party.id == str(party_id))
    )
    if party is None:
        raise NotFound(code="external_stock_reporter_not_found")
    return party


def _checked_lines(
    session: Session, tenant_id: str, lines: Any, default: datetime
) -> list[dict[str, Any]]:
    if not isinstance(lines, list) or not lines:
        raise InvalidOperation(code="external_stock_lines_required")
    checked = []
    seen = set()
    for line in lines:
        if not isinstance(line, dict) or set(line) - LINE_FIELDS:
            raise InvalidOperation(code="external_stock_fields_invalid")
        item = _item(session, tenant_id, line.get("item_id"))
        location = _location(session, tenant_id, line.get("location_id"))
        stated_at = _stated_at(line.get("stated_at"), default)
        key = (item.id, location.id, stated_at)
        if key in seen:
            raise InvalidOperation(code="external_stock_line_repeated")
        seen.add(key)
        checked.append(
            {
                "item": item,
                "location": location,
                "quantity": _quantity(line.get("quantity")),
                "stated_at": stated_at,
            }
        )
    return checked


def _book_quantities(
    session: Session,
    tenant_id: str,
    statements: Iterable[ExternalStockStatement],
) -> dict[str, Decimal]:
    """What Reality's movements hold, per statement, at its location and time.

    Two grouped queries for every statement at once: movements into and out of
    the statement's location up to its stated time, corrected movements and
    their compensations left out, as `stock_counts.book_as_of` reads them.
    """
    ids = [statement.id for statement in statements]
    if not ids:
        return {}
    corrected = select(MovementCorrection.original_movement_id).where(
        MovementCorrection.tenant_id == tenant_id
    )
    compensating = select(MovementCorrection.compensating_movement_id).where(
        MovementCorrection.tenant_id == tenant_id
    )
    held = {statement_id: ZERO for statement_id in ids}
    for column, sign in (
        (Movement.to_location_id, Decimal(1)),
        (Movement.from_location_id, Decimal(-1)),
    ):
        rows = session.execute(
            select(ExternalStockStatement.id, func.sum(Movement.quantity))
            .join(
                Movement,
                (Movement.tenant_id == ExternalStockStatement.tenant_id)
                & (Movement.item_id == ExternalStockStatement.item_id)
                & (column == ExternalStockStatement.location_id)
                & (Movement.occurred_at <= ExternalStockStatement.stated_at),
            )
            .where(
                ExternalStockStatement.tenant_id == tenant_id,
                ExternalStockStatement.id.in_(ids),
                Movement.id.not_in(corrected),
                Movement.id.not_in(compensating),
            )
            .group_by(ExternalStockStatement.id)
        )
        for statement_id, quantity in rows:
            held[statement_id] += sign * Decimal(quantity or 0)
    return held


def _latest_statements(
    session: Session,
    tenant_id: str,
    *,
    item_id: str | None = None,
    location_id: str | None = None,
) -> list[ExternalStockStatement]:
    """The latest statement per item and location; earlier ones are history."""
    ranked = select(
        ExternalStockStatement.id,
        func.row_number()
        .over(
            partition_by=(
                ExternalStockStatement.item_id,
                ExternalStockStatement.location_id,
            ),
            order_by=(
                ExternalStockStatement.stated_at.desc(),
                ExternalStockStatement.created_at.desc(),
                ExternalStockStatement.id.desc(),
            ),
        )
        .label("rank"),
    ).where(ExternalStockStatement.tenant_id == tenant_id)
    if item_id:
        ranked = ranked.where(ExternalStockStatement.item_id == item_id)
    if location_id:
        ranked = ranked.where(ExternalStockStatement.location_id == location_id)
    ranked = ranked.subquery()
    return list(
        session.scalars(
            select(ExternalStockStatement)
            .join(ranked, ranked.c.id == ExternalStockStatement.id)
            .where(
                ExternalStockStatement.tenant_id == tenant_id,
                ranked.c.rank == 1,
            )
            .order_by(ExternalStockStatement.stated_at, ExternalStockStatement.id)
        )
    )


def _compared(
    session: Session, tenant_id: str, statements: list[ExternalStockStatement]
) -> list[dict[str, Any]]:
    held = _book_quantities(session, tenant_id, statements)
    item_ids = {statement.item_id for statement in statements}
    location_ids = {statement.location_id for statement in statements}
    party_ids = {s.reporter_party_id for s in statements if s.reporter_party_id}
    source_ids = {statement.source_record_id for statement in statements}
    items = {
        item.id: item
        for item in session.scalars(
            select(Item).where(Item.tenant_id == tenant_id, Item.id.in_(item_ids))
        )
    }
    locations = {
        location.id: location
        for location in session.scalars(
            select(Location).where(
                Location.tenant_id == tenant_id, Location.id.in_(location_ids)
            )
        )
    }
    parties = (
        {
            party.id: party
            for party in session.scalars(
                select(Party).where(
                    Party.tenant_id == tenant_id, Party.id.in_(party_ids)
                )
            )
        }
        if party_ids
        else {}
    )
    systems = dict(
        session.execute(
            select(SourceRecord.id, SourceRecord.source_system).where(
                SourceRecord.tenant_id == tenant_id, SourceRecord.id.in_(source_ids)
            )
        ).all()
    )
    rows = []
    for statement in statements:
        stated = Decimal(statement.quantity)
        book = held[statement.id]
        item = items[statement.item_id]
        location = locations[statement.location_id]
        reporter = parties.get(statement.reporter_party_id or "")
        rows.append(
            {
                "statement_id": statement.id,
                "item_id": item.id,
                "sku": item.sku,
                "item": item.name,
                "unit": item.unit,
                "location_id": location.id,
                "location": location.name,
                "stated_quantity": stated,
                "reality_quantity": book,
                "difference": stated - book,
                "stated_at": statement.stated_at,
                "reporter_party_id": statement.reporter_party_id,
                "reporter": reporter.name if reporter else None,
                "source_record_id": statement.source_record_id,
                "source_system": systems.get(statement.source_record_id),
            }
        )
    return rows


def external_stock_differences(
    session: Session, tenant_id: str
) -> list[dict[str, Any]]:
    """The latest statements whose stated stock differs from Reality's at that time."""
    return [
        row
        for row in _compared(session, tenant_id, _latest_statements(session, tenant_id))
        if row["difference"] != ZERO
    ]


def external_stock(
    session: Session,
    tenant_id: str,
    *,
    item_id: str | None = None,
    location_id: str | None = None,
    differing_only: bool = False,
) -> list[dict[str, Any]]:
    """The latest statement per item and location, with Reality's stock then."""
    if item_id:
        _item(session, tenant_id, item_id)
    if location_id:
        location = session.scalar(
            select(Location).where(
                Location.tenant_id == tenant_id, Location.id == location_id
            )
        )
        if location is None:
            raise InvalidOperation(code="external_stock_location_not_stock")
    rows = _compared(
        session,
        tenant_id,
        _latest_statements(
            session, tenant_id, item_id=item_id, location_id=location_id
        ),
    )
    if differing_only:
        rows = [row for row in rows if row["difference"] != ZERO]
    return [
        {
            **row,
            "stated_quantity": _plain(row["stated_quantity"]),
            "reality_quantity": _plain(row["reality_quantity"]),
            "difference": _plain(row["difference"]),
            "stated_at": row["stated_at"].isoformat(),
        }
        for row in rows
    ]


def _line_view(line: dict[str, Any], book: Decimal) -> dict[str, Any]:
    return {
        "item_id": line["item"].id,
        "sku": line["item"].sku,
        "item": line["item"].name,
        "location_id": line["location"].id,
        "location": line["location"].name,
        "stated_quantity": _plain(line["quantity"]),
        "stated_at": line["stated_at"].isoformat(),
        "reality_quantity": _plain(book),
        "difference": _plain(line["quantity"] - book),
    }


def _held_at(session: Session, tenant_id: str, line: dict[str, Any]) -> Decimal:
    from reality.services.stock_counts import book_as_of

    return book_as_of(
        session,
        tenant_id,
        line["item"].id,
        line["location"].id,
        None,
        line["stated_at"],
    )


def review_external_stock(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any]]:
    """The arguments a confirmation executes and what the person is shown.

    A line without a stated time is fixed now, so the confirmation records the
    same statement the person saw.
    """
    if not isinstance(arguments, dict) or set(arguments) - FIELDS:
        raise InvalidOperation(code="external_stock_fields_invalid")
    reporter = _reporter(session, tenant_id, arguments.get("reporter_party_id"))
    lines = _checked_lines(session, tenant_id, arguments.get("lines"), now())
    note = str(arguments.get("note") or "").strip()
    normalized = {
        "lines": [
            {
                "item_id": line["item"].id,
                "location_id": line["location"].id,
                "quantity": _plain(line["quantity"]),
                "stated_at": line["stated_at"].isoformat(),
            }
            for line in lines
        ],
        "reporter_party_id": reporter.id if reporter else None,
        "note": note,
    }
    preview = {
        "reporter_party_id": reporter.id if reporter else None,
        "reporter": reporter.name if reporter else None,
        "note": note,
        "lines": [
            _line_view(line, _held_at(session, tenant_id, line)) for line in lines
        ],
    }
    return normalized, preview


def _store(
    session: Session,
    tenant_id: str,
    lines: list[dict[str, Any]],
    reporter_party_id: str | None,
    source_record_id: str,
    *,
    action_id: str | None = None,
) -> list[ExternalStockStatement]:
    from reality.services.core import emit_business_event

    rows = []
    for line in lines:
        row = ExternalStockStatement(
            id=uid("ess"),
            tenant_id=tenant_id,
            item_id=line["item"].id,
            location_id=line["location"].id,
            quantity=line["quantity"],
            stated_at=line["stated_at"],
            reporter_party_id=reporter_party_id,
            source_record_id=source_record_id,
        )
        session.add(row)
        rows.append(row)
    session.flush()
    for row in rows:
        emit_business_event(
            session,
            tenant_id,
            "external_stock.stated",
            "external_stock_statement",
            row.id,
            {
                "item_id": row.item_id,
                "location_id": row.location_id,
                "quantity": _plain(Decimal(row.quantity)),
                "stated_at": row.stated_at.isoformat(),
                "reporter_party_id": row.reporter_party_id,
            },
            source_record_id=source_record_id,
            action_id=action_id,
            correlation_id=action_id,
        )
    return rows


def record_external_stock(
    session: Session,
    tenant_id: str,
    lines: list[dict[str, Any]],
    reporter_party_id: str | None = None,
    note: str = "",
    *,
    action_id: str | None = None,
    _commit: bool = True,
) -> list[ExternalStockStatement]:
    """Record what someone outside states is in stock, without moving stock."""
    from reality.services.core import _require_business_mutation, store_source_record

    _require_business_mutation(session, tenant_id, "record_external_stock")
    reporter = _reporter(session, tenant_id, reporter_party_id)
    checked = _checked_lines(session, tenant_id, lines, now())
    statement = {
        "lines": [
            {
                "item_id": line["item"].id,
                "location_id": line["location"].id,
                "quantity": _plain(line["quantity"]),
                "stated_at": line["stated_at"].isoformat(),
            }
            for line in checked
        ],
        "reporter_party_id": reporter.id if reporter else None,
        "note": str(note or "").strip(),
        "statement_id": action_id or uid("stm"),
    }
    source, inserted, _ = store_source_record(
        session,
        tenant_id,
        SOURCE_SYSTEM,
        SOURCE_TYPE,
        statement["statement_id"],
        statement,
    )
    if not inserted:
        # The same confirmation again: it is already recorded.
        existing = list(
            session.scalars(
                select(ExternalStockStatement).where(
                    ExternalStockStatement.tenant_id == tenant_id,
                    ExternalStockStatement.source_record_id == source.id,
                )
            )
        )
        if existing:
            return existing
    rows = _store(
        session,
        tenant_id,
        checked,
        reporter.id if reporter else None,
        source.id,
        action_id=action_id,
    )
    if _commit:
        session.commit()
    return rows


def _record_file_rows(
    session: Session,
    tenant_id: str,
    source: SourceRecord,
    rows: list[dict[str, Any]],
) -> list[ExternalStockStatement]:
    """A file of external stock: each row a statement, the file its source.

    Rows name the item by SKU and the location by name, as the stock snapshot
    file does; a row without a time is stated as of the file's arrival.
    """
    from reality.services.file_interpreters import _item as item_by_sku
    from reality.services.file_interpreters import _location as location_by_name
    from reality.services.file_interpreters import _party, _value

    arrived = source.received_at or now()
    checked = []
    reporters: set[str | None] = set()
    for row in rows:
        item = item_by_sku(session, tenant_id, str(_value(row, "sku")).strip())
        location = location_by_name(
            session, tenant_id, str(_value(row, "location")).strip()
        )
        line = _checked_lines(
            session,
            tenant_id,
            [
                {
                    "item_id": item.id,
                    "location_id": location.id,
                    "quantity": _value(row, "quantity"),
                    "stated_at": _value(row, "stated_at", None) or None,
                }
            ],
            arrived,
        )[0]
        reporter = (
            _party(session, tenant_id, row).id
            if row.get("party_accounting_code") or row.get("party_name")
            else None
        )
        reporters.add(reporter)
        checked.append((line, reporter))
    stored = []
    for reporter in reporters:
        stored += _store(
            session,
            tenant_id,
            [line for line, by in checked if by == reporter],
            reporter,
            source.id,
        )
    return stored
