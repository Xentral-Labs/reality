"""Tenant-scoped inventory observations shared by services and adapters."""

from collections.abc import Sequence
from decimal import Decimal
from typing import Any

from sqlalchemy import Select, func, or_, select
from sqlalchemy.orm import Session

from reality.db.core import Commitment, Item, Movement, Reservation
from reality.db.pagination import DEFAULT_PAGE_SIZE, Page, page_for
from reality.db.query_order import query_order
from reality.domain.stock_scope import movement_at, reservation_at

QUANTITIES = ("physical", "reserved", "blocked", "available", "incoming", "projected")


def inventory_position_query(
    tenant_id: str, *, location_id: str | None = None
) -> Select:
    """Derive positions in SQL, using the existing effective fulfillment rule."""
    # A place scope narrows each side of the position to that exact location; without
    # one, every movement that names a location on its side is counted, as before.
    incoming = (
        select(
            Movement.item_id.label("item_id"), func.sum(Movement.quantity).label("qty")
        )
        .where(
            Movement.tenant_id == tenant_id,
            Movement.to_location_id == location_id
            if location_id
            else Movement.to_location_id.is_not(None),
        )
        .group_by(Movement.item_id)
        .subquery()
    )
    outgoing = (
        select(
            Movement.item_id.label("item_id"), func.sum(Movement.quantity).label("qty")
        )
        .where(
            Movement.tenant_id == tenant_id,
            Movement.from_location_id == location_id
            if location_id
            else Movement.from_location_id.is_not(None),
        )
        .group_by(Movement.item_id)
        .subquery()
    )
    reserved = (
        select(
            Reservation.item_id.label("item_id"),
            func.sum(Reservation.quantity).label("qty"),
        )
        .where(
            Reservation.tenant_id == tenant_id,
            Reservation.status == "active",
            *([Reservation.location_id == location_id] if location_id else []),
        )
        .group_by(Reservation.item_id)
        .subquery()
    )
    from reality.services.core import _open_stock_blocks

    # Spec 304: what is held back is neither available nor projected.
    blocks = _open_stock_blocks(tenant_id)
    blocked = (
        select(
            blocks.c.item_id.label("item_id"),
            func.sum(blocks.c.quantity).label("qty"),
        )
        .where(*([blocks.c.location_id == location_id] if location_id else []))
        .group_by(blocks.c.item_id)
        .subquery()
    )
    from reality.services.delivery_reads import fulfillment_expressions
    from reality.services.drop_shipping import ships_to_customer

    _, _, remaining = fulfillment_expressions()
    supplier_open = (
        select(
            Commitment.item_id.label("item_id"),
            func.sum(remaining).label("qty"),
        )
        .where(
            Commitment.tenant_id == tenant_id,
            Commitment.type == "supplier_delivery",
            Commitment.status != "cancelled",
            # Spec 337: a supplier shipping straight to a customer brings nothing here.
            ~ships_to_customer(),
            *([Commitment.location_id == location_id] if location_id else []),
        )
        .group_by(Commitment.item_id)
        .subquery()
    )
    physical = func.coalesce(incoming.c.qty, 0) - func.coalesce(outgoing.c.qty, 0)
    reserved_qty = func.coalesce(reserved.c.qty, 0)
    blocked_qty = func.coalesce(blocked.c.qty, 0)
    supplier_qty = func.coalesce(supplier_open.c.qty, 0)
    available = physical - reserved_qty - blocked_qty
    projected = available + supplier_qty
    return (
        select(
            Item,
            physical.label("physical"),
            reserved_qty.label("reserved"),
            blocked_qty.label("blocked"),
            available.label("available"),
            supplier_qty.label("incoming"),
            projected.label("projected"),
        )
        .outerjoin(incoming, incoming.c.item_id == Item.id)
        .outerjoin(outgoing, outgoing.c.item_id == Item.id)
        .outerjoin(reserved, reserved.c.item_id == Item.id)
        .outerjoin(blocked, blocked.c.item_id == Item.id)
        .outerjoin(supplier_open, supplier_open.c.item_id == Item.id)
        .where(Item.tenant_id == tenant_id)
    )


def position_row(item: Item, values: Sequence[Any]) -> dict[str, Any]:
    """Serialize a shared observation without deriving an adapter-specific value."""
    return {
        "item": item,
        **dict(zip(QUANTITIES, (Decimal(value or 0) for value in values), strict=True)),
        "receipts": [],
        "issues": [],
    }


def inventory_page(
    session: Session,
    tenant_id: str,
    *,
    page: int = 1,
    size: int = DEFAULT_PAGE_SIZE,
    query: str = "",
    item_id: str | None = None,
    location_id: str | None = None,
    stock_state: str = "",
    available_min: Decimal | None = None,
    available_max: Decimal | None = None,
    projected_min: Decimal | None = None,
    projected_max: Decimal | None = None,
    sort: str = "",
    sort_direction: str = "asc",
) -> tuple[list[dict[str, Any]], Page]:
    positions = inventory_position_query(tenant_id, location_id=location_id).subquery()
    physical, reserved_qty, _blocked_qty, available, _supplier_qty, projected = (
        positions.c[key] for key in QUANTITIES
    )
    criteria = [Item.tenant_id == tenant_id]
    if item_id:
        criteria.append(Item.id == item_id)
    if location_id:
        # Under a place scope the register answers for what is recorded there, not for
        # the whole catalogue: one set-based membership test, never a pass per item.
        criteria.append(
            Item.id.in_(
                select(Movement.item_id)
                .where(Movement.tenant_id == tenant_id, movement_at(location_id))
                .union(
                    select(Reservation.item_id).where(
                        Reservation.tenant_id == tenant_id,
                        reservation_at(location_id),
                        Reservation.status == "active",
                    )
                )
            )
        )
    if query:
        pattern = f"%{query.strip().lower()}%"
        criteria.append(
            or_(func.lower(Item.name).like(pattern), func.lower(Item.sku).like(pattern))
        )
    if stock_state == "shortage":
        criteria.append(available < 0)
    elif stock_state == "fully_allocated":
        criteria.append(available == 0)
    elif stock_state == "available":
        criteria.append(available > 0)
    for expression, minimum, maximum in (
        (available, available_min, available_max),
        (projected, projected_min, projected_max),
    ):
        if minimum is not None:
            criteria.append(expression >= minimum)
        if maximum is not None:
            criteria.append(expression <= maximum)
    base = (
        select(Item, *(positions.c[key] for key in QUANTITIES))
        .join(positions, positions.c.id == Item.id)
        .where(*criteria)
    )
    total = int(session.scalar(select(func.count()).select_from(base.subquery())) or 0)
    pager = page_for(total, page, size)
    records = session.execute(
        base.order_by(
            *query_order(
                sort,
                sort_direction,
                {
                    "id": Item.id,
                    "name": Item.name,
                    "physical": physical,
                    "reserved": reserved_qty,
                    "available": available,
                },
                Item.id,
                (
                    Item.name,
                    Item.id,
                ),
            )
        )
        .limit(pager.size)
        .offset(pager.offset)
    )
    return [position_row(row[0], row[1:]) for row in records], pager
