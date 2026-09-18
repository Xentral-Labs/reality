"""Exact stock identities derived from retained movement legs and active reservations."""

import json
from collections.abc import Iterator
from datetime import datetime
from decimal import Decimal
from hashlib import sha256
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from reality.db.core import (
    HandlingUnit,
    Item,
    Location,
    Lot,
    Movement,
    Reservation,
    SerialUnit,
)


def position_identity(*parts: str | None) -> str:
    """Opaque, stable row identity that never relies on human numbers."""
    return sha256(json.dumps(parts, separators=(",", ":")).encode()).hexdigest()


def movement_legs(movement: Movement) -> Iterator[tuple[str, Decimal]]:
    """Signed physical effects, including both legs of internal transfers."""
    if movement.from_location_id:
        yield movement.from_location_id, -movement.quantity
    if movement.to_location_id:
        yield movement.to_location_id, movement.quantity


def inventory_detail_rows(
    session: Session,
    tenant_id: str,
    *,
    effective_before: datetime | None = None,
) -> list[dict[str, Any]]:
    """Null tracking dimensions are exact unknown buckets, never wildcard matches.

    Historical reads expose physical quantities only: reservation status is mutable.
    Names and units are current master data, not reconstructed historical attributes.
    """

    def records(model):
        return {
            r.id: r
            for r in session.scalars(select(model).where(model.tenant_id == tenant_id))
        }

    items = records(Item)
    dimensions = [
        ("location_id", records(Location), "name"),
        ("lot_id", records(Lot), "lot_number"),
        ("serial_unit_id", records(SerialUnit), "serial_number"),
        ("handling_unit_id", records(HandlingUnit), "nve"),
    ]
    buckets: dict[tuple[str | None, ...], dict[str, Any]] = {}

    def bucket(
        item_id: str,
        location_id: str | None,
        lot_id: str | None,
        serial_unit_id: str | None,
        handling_unit_id: str | None,
    ) -> dict[str, Any]:
        key = (item_id, location_id, lot_id, serial_unit_id, handling_unit_id)
        if key not in buckets:
            row = dict(
                zip(
                    (
                        "item_id",
                        "location_id",
                        "lot_id",
                        "serial_unit_id",
                        "handling_unit_id",
                    ),
                    key,
                    strict=True,
                )
            )
            row.update(
                position_id=position_identity(tenant_id, *key), physical=Decimal(0)
            )
            for field, lookup, label in dimensions:
                row[field.removesuffix("_id") + "_name"] = getattr(
                    lookup.get(row[field]), label, None
                )
            if effective_before is None:
                row["reserved"] = Decimal(0)
            buckets[key] = row
        return buckets[key]

    movements = select(Movement).where(Movement.tenant_id == tenant_id)
    if effective_before:
        movements = movements.where(Movement.occurred_at < effective_before)
    for movement in session.scalars(movements):
        for location, amount in movement_legs(movement):
            bucket(
                movement.item_id,
                location,
                movement.lot_id,
                movement.serial_unit_id,
                movement.handling_unit_id,
            )["physical"] += amount
    if effective_before is None:
        for reservation in session.scalars(
            select(Reservation).where(
                Reservation.tenant_id == tenant_id, Reservation.status == "active"
            )
        ):
            bucket(
                reservation.item_id,
                reservation.location_id,
                reservation.lot_id,
                reservation.serial_unit_id,
                reservation.handling_unit_id,
            )["reserved"] += reservation.quantity
    present = {key[0] for key in buckets}
    for item_id in items.keys() - present:
        bucket(item_id, None, None, None, None)
    for row in buckets.values():
        if effective_before is None:
            row["available"] = row["physical"] - row["reserved"]
    return list(buckets.values())
