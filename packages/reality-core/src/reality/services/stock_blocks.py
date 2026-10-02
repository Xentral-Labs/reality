"""Blocked stock: goods held back where they lie, with their reason (spec 304).

A block names an item at a location, optionally its exact lot, handling unit
or serial unit, a quantity and a reason. Nothing moves: the goods stay where
they are, and every reader that reserves, ships, transfers or reports
availability subtracts what blocks still hold back (`core.blocked_quantity`).
A block is released, wholly or partly, when quality clears the goods, or
scrapped, which writes the part off with one reasoned adjustment.

The block stays as it was stated, under one id (spec 316). Each release or
scrap is appended as its own resolution, and the open quantity, the stated
quantity less the resolutions, is read at read time and never stored.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from reality.db.core import (
    Item,
    Location,
    StockBlock,
    StockBlockResolution,
    uid,
)
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


def _resolutions(
    session: Session, tenant_id: str, block_ids: list[str]
) -> dict[str, list[StockBlockResolution]]:
    """Each block's releases and scraps, oldest first."""
    found: dict[str, list[StockBlockResolution]] = {key: [] for key in block_ids}
    if block_ids:
        for resolution in session.scalars(
            select(StockBlockResolution)
            .where(
                StockBlockResolution.tenant_id == tenant_id,
                StockBlockResolution.block_id.in_(block_ids),
            )
            .order_by(StockBlockResolution.resolved_at, StockBlockResolution.id)
        ):
            found[resolution.block_id].append(resolution)
    return found


def _open_quantity(
    block: StockBlock, resolutions: list[StockBlockResolution]
) -> Decimal:
    """The stated quantity less every release and scrap of it (spec 316)."""
    return Decimal(block.quantity) - sum(
        (Decimal(row.quantity) for row in resolutions), ZERO
    )


def _row(
    block: StockBlock,
    resolutions: list[StockBlockResolution],
    item: Item | None = None,
    location: Location | None = None,
):
    remaining = _open_quantity(block, resolutions)
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
        "open_quantity": _plain(remaining),
        "status": "active" if remaining > ZERO else "resolved",
        "reason_code": block.reason_code,
        "note": block.note,
        "created_at": block.created_at,
        "created_by": block.created_by,
        "receipt_movement_id": block.receipt_movement_id,
        "resolutions": [
            {
                "id": row.id,
                "kind": row.kind,
                "quantity": _plain(row.quantity),
                "reason": row.reason,
                "resolved_at": row.resolved_at,
                "resolved_by": row.resolved_by,
                "movement_id": row.movement_id,
            }
            for row in resolutions
        ],
    }


def stock_blocks(
    session: Session,
    tenant_id: str,
    *,
    item_id: str | None = None,
    location_id: str | None = None,
    status: str = "active",
) -> list[dict[str, Any]]:
    """The company's stock blocks, open ones by default, newest first.

    `active` holds something back still, `resolved` holds nothing back any
    more; both are read from the resolutions, never stored (spec 316).
    """
    get_tenant(session, tenant_id)
    if status not in {"active", "resolved", "all"}:
        raise InvalidOperation(code="stock_block_status_unsupported")
    resolved = (
        select(
            StockBlockResolution.block_id,
            func.sum(StockBlockResolution.quantity).label("quantity"),
        )
        .where(StockBlockResolution.tenant_id == tenant_id)
        .group_by(StockBlockResolution.block_id)
        .subquery()
    )
    remaining = StockBlock.quantity - func.coalesce(resolved.c.quantity, 0)
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
        .outerjoin(resolved, resolved.c.block_id == StockBlock.id)
        .where(StockBlock.tenant_id == tenant_id)
        .order_by(StockBlock.created_at.desc(), StockBlock.id)
    )
    if status == "active":
        query = query.where(remaining > 0)
    elif status == "resolved":
        query = query.where(remaining <= 0)
    if item_id:
        query = query.where(StockBlock.item_id == item_id)
    if location_id:
        query = query.where(StockBlock.location_id == location_id)
    rows = session.execute(query).all()
    resolutions = _resolutions(session, tenant_id, [block.id for block, _, _ in rows])
    return [
        _row(block, resolutions[block.id], item, location)
        for block, item, location in rows
    ]


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
    _receipt: Decimal | None = None,
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
    # A receipt blocks part of what it brings, never stock already there.
    if _receipt is not None and amount > _receipt:
        raise InvalidOperation(code="stock_block_exceeds_receipt")
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
    _receipt: Decimal | None = None,
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
        _receipt=_receipt,
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
        created_by=created_by,
        receipt_movement_id=_movement_id,
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
) -> tuple[StockBlock, Decimal, str, Decimal]:
    """The block, the part to resolve, the stated reason and what is open."""
    block = _tenant_record(session, StockBlock, tenant_id, block_id)
    remaining = _open_quantity(
        block, _resolutions(session, tenant_id, [block.id])[block.id]
    )
    if remaining <= ZERO:
        raise InvalidOperation(code="stock_block_not_active")
    stated = (reason or "").strip()
    if not stated:
        raise InvalidOperation(code="stock_block_reason_required")
    if quantity in (None, ""):
        amount = remaining
    else:
        try:
            amount = decimal(quantity)
        except (ArithmeticError, ValueError, InvalidOperation) as error:
            raise InvalidOperation(code="stock_block_quantity_invalid") from error
    if amount <= ZERO or amount.normalize().as_tuple().exponent < -4:
        raise InvalidOperation(code="stock_block_quantity_invalid")
    if amount > remaining:
        raise InvalidOperation(code="stock_block_quantity_exceeds_block")
    return block, amount, stated, remaining


def _resolve(
    session: Session,
    tenant_id: str,
    block: StockBlock,
    kind: str,
    amount: Decimal,
    reason: str,
    resolved_by: str,
    movement_id: str | None = None,
) -> StockBlockResolution:
    """Append one release or scrap; the block itself is never changed."""
    resolution = StockBlockResolution(
        id=uid("sbr"),
        tenant_id=tenant_id,
        block_id=block.id,
        kind=kind,
        quantity=amount,
        reason=reason,
        resolved_by=resolved_by,
        movement_id=movement_id,
    )
    session.add(resolution)
    session.flush()
    return resolution


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
    block, amount, stated, remaining = validate_resolution(
        session, tenant_id, block_id, quantity, reason
    )
    resolution = _resolve(
        session, tenant_id, block, "release", amount, stated, resolved_by
    )
    left = _plain(remaining - amount)
    emit_business_event(
        session,
        tenant_id,
        "stock_block.released",
        "stock_block",
        block.id,
        {
            "item_id": block.item_id,
            "location_id": block.location_id,
            "resolution_id": resolution.id,
            "quantity": _plain(amount),
            "reason": stated,
            "open_quantity": left,
        },
        action_id=action_id,
        correlation_id=action_id,
    )
    if _commit:
        session.commit()
    return {"block_id": block.id, "released": _plain(amount), "open_quantity": left}


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
    block, amount, stated, remaining = validate_resolution(
        session, tenant_id, block_id, quantity, reason
    )
    # The scrap is resolved first, so the adjustment takes stock its own block
    # no longer holds back; the resolution names the adjustment it is about to
    # write, whose key is checked when the transaction commits.
    movement_id = uid("mov")
    resolution = _resolve(
        session, tenant_id, block, "scrap", amount, stated, resolved_by, movement_id
    )
    movement = record_movement(
        session,
        tenant_id,
        "adjustment",
        block.item_id,
        amount,
        from_location_id=block.location_id,
        handling_unit_id=block.handling_unit_id,
        lot_id=block.lot_id,
        serial_unit_id=block.serial_unit_id,
        reason=f"scrap: {stated}",
        action_id=action_id,
        _commit=False,
        _movement_id=movement_id,
    )
    left = _plain(remaining - amount)
    emit_business_event(
        session,
        tenant_id,
        "stock_block.scrapped",
        "stock_block",
        block.id,
        {
            "item_id": block.item_id,
            "location_id": block.location_id,
            "resolution_id": resolution.id,
            "quantity": _plain(amount),
            "reason": stated,
            "movement_id": movement.id,
            "open_quantity": left,
        },
        action_id=action_id,
        correlation_id=action_id,
    )
    if _commit:
        session.commit()
    return {
        "block_id": block.id,
        "scrapped": _plain(amount),
        "movement_id": movement.id,
        "open_quantity": left,
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
        _resolutions(session, tenant_id, [block.id])[block.id],
        session.get(Item, (tenant_id, block.item_id)),
        session.get(Location, (tenant_id, block.location_id)),
    )


STOCK_BLOCK_TOOLS = {"stock_block", "stock_block_release", "stock_block_scrap"}


def review_stock_block(
    session: Session, tenant_id: str, tool_name: str, arguments: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any]]:
    """The arguments a confirmation executes and what the person is shown.

    A block's review shows the stock at its identity: physical, reserved,
    already blocked and what this block leaves available. A release or scrap
    review shows the block and carries the quantity it saw, so a confirmation
    after the block changed is refused.
    """
    if tool_name == "stock_block":
        identity = {
            key: arguments.get(key) or None
            for key in ("handling_unit_id", "lot_id", "serial_unit_id")
        }
        item, location, amount, lot_id = validate_block(
            session,
            tenant_id,
            str(arguments.get("item_id") or ""),
            str(arguments.get("location_id") or ""),
            arguments.get("quantity", ""),
            str(arguments.get("reason_code") or ""),
            **identity,
        )
        identity["lot_id"] = lot_id
        free = free_to_block(session, tenant_id, item.id, location.id, **identity)
        normalized = {
            "item_id": item.id,
            "location_id": location.id,
            "quantity": _plain(amount),
            "reason_code": arguments["reason_code"],
            "note": str(arguments.get("note") or "").strip(),
            **{key: value for key, value in identity.items() if value},
        }
        preview = {
            "item": item.name,
            "unit": item.unit,
            "location": location.name,
            "physical": _plain(stock_at(session, tenant_id, item.id, location.id)),
            "reserved": _plain(
                active_reserved(session, tenant_id, item.id, location.id)
            ),
            "blocked": _plain(
                blocked_quantity(session, tenant_id, item.id, location.id)
            ),
            "free_before": _plain(free),
            "free_after": _plain(free - amount),
            "quantity": _plain(amount),
            "reason_code": arguments["reason_code"],
        }
        return normalized, preview
    if tool_name not in STOCK_BLOCK_TOOLS:
        raise InvalidOperation(code="proposal_tool_not_found")
    block, amount, stated, remaining = validate_resolution(
        session,
        tenant_id,
        str(arguments.get("block_id") or ""),
        arguments.get("quantity"),
        str(arguments.get("reason") or ""),
    )
    normalized = {
        "block_id": block.id,
        "quantity": _plain(amount),
        "reason": stated,
        "reviewed": _plain(remaining),
    }
    detail = stock_block_detail(session, tenant_id, block.id)
    preview = {**detail, "resolving": _plain(amount), "reason": stated}
    return normalized, preview


def check_reviewed_block(
    session: Session, tenant_id: str, block_id: str, reviewed: str | None
) -> None:
    """Refuse a release or scrap of a block that changed after its review."""
    if reviewed is None:
        return
    block = _tenant_record(session, StockBlock, tenant_id, block_id)
    remaining = _open_quantity(
        block, _resolutions(session, tenant_id, [block.id])[block.id]
    )
    if _plain(remaining) != reviewed:
        raise InvalidOperation(code="stock_block_changed_since_review")
