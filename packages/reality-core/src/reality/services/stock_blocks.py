"""Blocked stock: goods held back where they lie, with their reason (spec 304).

A block names an item at a location, optionally its exact lot, handling unit
or serial unit, a quantity and a reason. Nothing moves: the goods stay where
they are, and every reader that reserves, ships, transfers or reports
availability subtracts the active blocks (`core.blocked_quantity`). A block
is released, wholly or partly, when quality clears the goods, or scrapped,
which writes the part off with one reasoned adjustment. A partial release or
scrap closes the row for that part and continues the rest as a new active
row, so each row's history stays what happened to it.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from reality.db.core import Item, Location, StockBlock, now, uid
from reality.services.business_locks import lock_delivery_state
from reality.services.core import (
    InvalidOperation,
    NotFound,
    _require_business_mutation,
    _tenant_record,
    _validate_inventory_identity,
    active_reserved,
    blocked_quantity,
    decimal,
    emit_business_event,
    get_tenant,
    reserved_by_identity,
    stock_at,
    stock_by_identity,
)

ZERO = Decimal(0)
REASONS = ("quality", "damage", "expiry", "inspection")


def _plain(value: Decimal) -> str:
    return f"{Decimal(value).normalize():f}"


def free_to_block(
    session: Session,
    tenant_id: str,
    item_id: str,
    location_id: str,
    *,
    handling_unit_id: str | None = None,
    lot_id: str | None = None,
    serial_unit_id: str | None = None,
) -> Decimal:
    """What is physically there and neither reserved nor already blocked."""
    identity = {
        "handling_unit_id": handling_unit_id,
        "lot_id": lot_id,
        "serial_unit_id": serial_unit_id,
    }
    at_location = (
        stock_at(session, tenant_id, item_id, location_id)
        - active_reserved(session, tenant_id, item_id, location_id)
        - blocked_quantity(session, tenant_id, item_id, location_id)
    )
    if not any(identity.values()):
        return max(ZERO, at_location)
    at_identity = (
        stock_by_identity(session, tenant_id, item_id, location_id, **identity)
        - reserved_by_identity(session, tenant_id, item_id, location_id, **identity)
        - blocked_quantity(session, tenant_id, item_id, location_id, **identity)
    )
    return max(ZERO, min(at_location, at_identity))


def _row(block: StockBlock, item: Item | None = None, location: Location | None = None):
    return {
        "id": block.id,
        "item_id": block.item_id,
        "item": item.name if item else None,
        "unit": item.unit if item else None,
        "location_id": block.location_id,
        "location": location.name if location else None,
        "handling_unit_id": block.handling_unit_id,
        "lot_id": block.lot_id,
        "serial_unit_id": block.serial_unit_id,
        "quantity": _plain(block.quantity),
        "reason_code": block.reason_code,
        "note": block.note,
        "status": block.status,
        "created_at": block.created_at,
        "created_by": block.created_by,
        "resolved_at": block.resolved_at,
        "resolved_by": block.resolved_by,
        "resolution_reason": block.resolution_reason,
        "previous_block_id": block.previous_block_id,
        "movement_id": block.movement_id,
    }


def stock_blocks(
    session: Session,
    tenant_id: str,
    *,
    item_id: str | None = None,
    location_id: str | None = None,
    status: str = "active",
) -> list[dict[str, Any]]:
    """The company's stock blocks, active by default, newest first."""
    get_tenant(session, tenant_id)
    if status not in {"active", "released", "scrapped", "all"}:
        raise InvalidOperation(code="stock_block_status_unsupported")
    query = (
        select(StockBlock, Item, Location)
        .join(
            Item,
            (Item.tenant_id == StockBlock.tenant_id) & (Item.id == StockBlock.item_id),
        )
        .join(
            Location,
            (Location.tenant_id == StockBlock.tenant_id)
            & (Location.id == StockBlock.location_id),
        )
        .where(StockBlock.tenant_id == tenant_id)
        .order_by(StockBlock.created_at.desc(), StockBlock.id)
    )
    if status != "all":
        query = query.where(StockBlock.status == status)
    if item_id:
        query = query.where(StockBlock.item_id == item_id)
    if location_id:
        query = query.where(StockBlock.location_id == location_id)
    return [_row(*row) for row in session.execute(query)]


def validate_block(
    session: Session,
    tenant_id: str,
    item_id: str,
    location_id: str,
    quantity: Decimal | float | str,
    reason_code: str,
    *,
    handling_unit_id: str | None = None,
    lot_id: str | None = None,
    serial_unit_id: str | None = None,
    _incoming: Decimal = ZERO,
) -> tuple[Item, Location, Decimal, str | None]:
    """The checks a block makes, also run by its review so both refuse alike.

    `_incoming` is stock a receipt is about to record, so a receipt can block
    part of what it brings in the same confirmation.
    """
    item = _tenant_record(session, Item, tenant_id, item_id)
    location = _tenant_record(session, Location, tenant_id, location_id)
    if item.item_type != "stocked":
        raise InvalidOperation(code="stock_block_item_not_stocked")
    if not location.allows_stock:
        raise InvalidOperation(code="stock_block_location_not_stock")
    if reason_code not in REASONS:
        raise InvalidOperation(code="stock_block_reason_unsupported")
    try:
        amount = decimal(quantity)
    except (ArithmeticError, ValueError, InvalidOperation) as error:
        raise InvalidOperation(code="stock_block_quantity_invalid") from error
    if amount <= ZERO or amount.normalize().as_tuple().exponent < -4:
        raise InvalidOperation(code="stock_block_quantity_invalid")
    _, _, serial = _validate_inventory_identity(
        session,
        tenant_id,
        item,
        handling_unit_id=handling_unit_id,
        lot_id=lot_id,
        serial_unit_id=serial_unit_id,
        require_tracked_identity=True,
    )
    if serial and serial.lot_id:
        lot_id = serial.lot_id
    free = _incoming + free_to_block(
        session,
        tenant_id,
        item.id,
        location.id,
        handling_unit_id=handling_unit_id,
        lot_id=lot_id,
        serial_unit_id=serial_unit_id,
    )
    if amount > free:
        raise InvalidOperation(
            code="stock_block_exceeds_available",
            values={"requested": _plain(amount), "available": _plain(free)},
        )
    return item, location, amount, lot_id


def block_stock(
    session: Session,
    tenant_id: str,
    item_id: str,
    location_id: str,
    quantity: Decimal | float | str,
    reason_code: str,
    note: str = "",
    *,
    handling_unit_id: str | None = None,
    lot_id: str | None = None,
    serial_unit_id: str | None = None,
    created_by: str = "human",
    action_id: str | None = None,
    _movement_id: str | None = None,
    _commit: bool = True,
) -> StockBlock:
    """Hold back a quantity where it lies; nothing moves."""
    _require_business_mutation(session, tenant_id, "block_stock")
    lock_delivery_state(session, tenant_id)
    item, location, amount, lot_id = validate_block(
        session,
        tenant_id,
        item_id,
        location_id,
        quantity,
        reason_code,
        handling_unit_id=handling_unit_id,
        lot_id=lot_id,
        serial_unit_id=serial_unit_id,
    )
    block = StockBlock(
        id=uid("blk"),
        tenant_id=tenant_id,
        item_id=item.id,
        location_id=location.id,
        handling_unit_id=handling_unit_id,
        lot_id=lot_id,
        serial_unit_id=serial_unit_id,
        quantity=amount,
        reason_code=reason_code,
        note=(note or "").strip(),
        status="active",
        created_by=created_by,
        movement_id=_movement_id,
    )
    session.add(block)
    session.flush()
    emit_business_event(
        session,
        tenant_id,
        "stock_block.created",
        "stock_block",
        block.id,
        {
            "item_id": item.id,
            "location_id": location.id,
            "handling_unit_id": handling_unit_id,
            "lot_id": lot_id,
            "serial_unit_id": serial_unit_id,
            "quantity": _plain(amount),
            "reason_code": reason_code,
            **({"movement_id": _movement_id} if _movement_id else {}),
        },
        action_id=action_id,
        correlation_id=action_id,
    )
    if _commit:
        session.commit()
    return block


def validate_resolution(
    session: Session,
    tenant_id: str,
    block_id: str,
    quantity: Decimal | float | str | None,
    reason: str,
) -> tuple[StockBlock, Decimal, str]:
    block = _tenant_record(session, StockBlock, tenant_id, block_id)
    if block.status != "active":
        raise InvalidOperation(code="stock_block_not_active")
    stated = (reason or "").strip()
    if not stated:
        raise InvalidOperation(code="stock_block_reason_required")
    if quantity in (None, ""):
        amount = Decimal(block.quantity)
    else:
        try:
            amount = decimal(quantity)
        except (ArithmeticError, ValueError, InvalidOperation) as error:
            raise InvalidOperation(code="stock_block_quantity_invalid") from error
    if amount <= ZERO or amount.normalize().as_tuple().exponent < -4:
        raise InvalidOperation(code="stock_block_quantity_invalid")
    if amount > Decimal(block.quantity):
        raise InvalidOperation(code="stock_block_quantity_exceeds_block")
    return block, amount, stated


def _resolve(
    session: Session,
    tenant_id: str,
    block: StockBlock,
    amount: Decimal,
    status: str,
    reason: str,
    resolved_by: str,
) -> tuple[StockBlock, StockBlock | None]:
    """Close the resolved part; continue the rest as a new active block."""
    rest = Decimal(block.quantity) - amount
    remainder = None
    if rest > ZERO:
        remainder = StockBlock(
            id=uid("blk"),
            tenant_id=tenant_id,
            item_id=block.item_id,
            location_id=block.location_id,
            handling_unit_id=block.handling_unit_id,
            lot_id=block.lot_id,
            serial_unit_id=block.serial_unit_id,
            quantity=rest,
            reason_code=block.reason_code,
            note=block.note,
            status="active",
            created_by=block.created_by,
            previous_block_id=block.id,
        )
        session.add(remainder)
    block.quantity = amount
    block.status = status
    block.resolved_at = now()
    block.resolved_by = resolved_by
    block.resolution_reason = reason
    session.flush()
    return block, remainder


def release_stock_block(
    session: Session,
    tenant_id: str,
    block_id: str,
    quantity: Decimal | float | str | None = None,
    *,
    reason: str,
    resolved_by: str = "human",
    action_id: str | None = None,
    _commit: bool = True,
) -> dict[str, Any]:
    """Make blocked goods available again, wholly or partly; nothing moves."""
    _require_business_mutation(session, tenant_id, "release_stock_block")
    lock_delivery_state(session, tenant_id)
    block, amount, stated = validate_resolution(
        session, tenant_id, block_id, quantity, reason
    )
    released, remainder = _resolve(
        session, tenant_id, block, amount, "released", stated, resolved_by
    )
    emit_business_event(
        session,
        tenant_id,
        "stock_block.released",
        "stock_block",
        released.id,
        {
            "item_id": released.item_id,
            "location_id": released.location_id,
            "quantity": _plain(amount),
            "reason": stated,
            **({"remainder_block_id": remainder.id} if remainder else {}),
        },
        action_id=action_id,
        correlation_id=action_id,
    )
    if _commit:
        session.commit()
    return {
        "block_id": released.id,
        "released": _plain(amount),
        "remainder_block_id": remainder.id if remainder else None,
    }


def scrap_stock_block(
    session: Session,
    tenant_id: str,
    block_id: str,
    quantity: Decimal | float | str | None = None,
    *,
    reason: str,
    resolved_by: str = "human",
    action_id: str | None = None,
    _commit: bool = True,
) -> dict[str, Any]:
    """Write blocked goods off: one reasoned adjustment out of their location."""
    from reality.services.core import record_movement

    _require_business_mutation(session, tenant_id, "scrap_stock_block")
    lock_delivery_state(session, tenant_id)
    block, amount, stated = validate_resolution(
        session, tenant_id, block_id, quantity, reason
    )
    # The part is no longer blocked once it is written off, so the adjustment
    # takes stock that is no longer held back by its own block.
    scrapped, remainder = _resolve(
        session, tenant_id, block, amount, "scrapped", stated, resolved_by
    )
    movement = record_movement(
        session,
        tenant_id,
        "adjustment",
        scrapped.item_id,
        amount,
        from_location_id=scrapped.location_id,
        handling_unit_id=scrapped.handling_unit_id,
        lot_id=scrapped.lot_id,
        serial_unit_id=scrapped.serial_unit_id,
        reason=f"scrap: {stated}",
        action_id=action_id,
        _commit=False,
    )
    scrapped.movement_id = movement.id
    session.flush()
    emit_business_event(
        session,
        tenant_id,
        "stock_block.scrapped",
        "stock_block",
        scrapped.id,
        {
            "item_id": scrapped.item_id,
            "location_id": scrapped.location_id,
            "quantity": _plain(amount),
            "reason": stated,
            "movement_id": movement.id,
            **({"remainder_block_id": remainder.id} if remainder else {}),
        },
        action_id=action_id,
        correlation_id=action_id,
    )
    if _commit:
        session.commit()
    return {
        "block_id": scrapped.id,
        "scrapped": _plain(amount),
        "movement_id": movement.id,
        "remainder_block_id": remainder.id if remainder else None,
    }


def stock_block_detail(
    session: Session, tenant_id: str, block_id: str
) -> dict[str, Any]:
    block = session.scalar(
        select(StockBlock).where(
            StockBlock.tenant_id == tenant_id, StockBlock.id == block_id
        )
    )
    if block is None:
        raise NotFound(code="stock_block_not_found")
    return _row(
        block,
        session.get(Item, (tenant_id, block.item_id)),
        session.get(Location, (tenant_id, block.location_id)),
    )
