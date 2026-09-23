"""Compose existing register observations for the unified warehouse adapter."""

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from reality.db.core import Commitment, Item, Location
from reality.services.core import (
    NotFound,
    _movement_correction_relation_for_member,
    get_tenant,
)
from reality.web.read_models import inventory_page, movement_page, reservation_page

STATES = {
    "stock": {"", "available", "fully_allocated", "shortage"},
    "reservations": {"", "active", "released", "consumed"},
    "movements": {
        "",
        "receipt",
        "shipment",
        "transfer",
        "correction",
        "return",
        "supplier_return",
        "adjustment",
    },
}


def warehouse_register(
    session: Session,
    tenant_id: str,
    view: str,
    *,
    query: str = "",
    state: str = "",
    item_id: str | None = None,
    location_id: str | None = None,
    page: int = 1,
    size: int = 50,
    sort: str = "",
    sort_direction: str = "asc",
) -> dict[str, Any]:
    get_tenant(session, tenant_id)
    if view not in STATES or state not in STATES[view]:
        raise ValueError("Unsupported warehouse view or state.")
    selected_item = None
    if item_id:
        selected_item = session.scalar(
            select(Item).where(Item.tenant_id == tenant_id, Item.id == item_id)
        )
        if selected_item is None:
            raise NotFound("Item not found.")
    selected_location = None
    if location_id:
        selected_location = session.scalar(
            select(Location).where(
                Location.tenant_id == tenant_id, Location.id == location_id
            )
        )
        if selected_location is None:
            raise NotFound("Location not found.")
    options = {
        "query": query,
        "item_id": item_id,
        "location_id": location_id,
        "page": page,
        "size": size,
        "sort": sort,
        "sort_direction": sort_direction,
    }
    if view == "stock":
        rows, pager = inventory_page(session, tenant_id, stock_state=state, **options)
        items = [
            {
                "id": row["item"].id,
                "name": row["item"].name,
                "sku": row["item"].sku,
                "unit": row["item"].unit,
                **{key: str(row[key]) for key in ("physical", "reserved", "available")},
            }
            for row in rows
        ]
    else:
        rows, pager = (
            reservation_page(session, tenant_id, status=state, **options)
            if view == "reservations"
            else movement_page(session, tenant_id, movement_type=state, **options)
        )
        key = "reservation" if view == "reservations" else "movement"
        ids = {row[key].commitment_id for row in rows if row[key].commitment_id}
        deliveries = set(
            session.scalars(
                select(Commitment.id).where(
                    Commitment.tenant_id == tenant_id,
                    Commitment.id.in_(ids),
                    Commitment.type == "customer_delivery",
                )
            )
        )
        items = []
        for row in rows:
            record = row[key]
            item = row["item"]
            result = {
                "id": record.id,
                "item_id": record.item_id,
                "item": item.name if item else record.item_id,
                "sku": item.sku if item else "",
                "unit": item.unit if item else "",
                "quantity": str(record.quantity),
                "commitment_id": record.commitment_id,
                "delivery_id": record.commitment_id
                if record.commitment_id in deliveries
                else None,
            }
            if view == "reservations":
                result.update(
                    status=record.status,
                    at=record.reserved_at,
                    location_id=record.location_id,
                    location=row["location"].name
                    if row["location"]
                    else record.location_id,
                )
            else:
                _, role = _movement_correction_relation_for_member(
                    session, tenant_id, record.id
                )
                result.update(
                    type=record.type,
                    at=record.occurred_at,
                    from_location_id=record.from_location_id,
                    to_location_id=record.to_location_id,
                    from_location=row["from_location"].name
                    if row["from_location"]
                    else None,
                    to_location=row["to_location"].name if row["to_location"] else None,
                    correction_role=role,
                )
            items.append(result)
    return {
        "items": items,
        "page": {
            "number": pager.number,
            "size": pager.size,
            "total": pager.total,
            "pages": pager.pages,
            "has_previous": pager.has_previous,
            "has_next": pager.has_next,
        },
        "scope": {
            "tenant_id": tenant_id,
            "view": view,
            "query": query,
            "state": state,
            "item_id": item_id,
            "item": selected_item.name if selected_item else None,
            "location_id": location_id,
            "location": selected_location.name if selected_location else None,
        },
        "observed_at": datetime.now(UTC),
    }
