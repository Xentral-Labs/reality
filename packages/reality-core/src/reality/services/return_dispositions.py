"""Derived return disposition reads and confirmed resolving movements."""

from __future__ import annotations

import json
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from reality.db.core import Commitment, Movement, MovementCorrection, SourceRecord, uid
from reality.services import core

DISPOSITIONS = {"restock", "quarantine_repair", "scrap_loss", "return_to_supplier"}


def _return_movement(session: Session, tenant_id: str, movement_id: str) -> Movement:
    movement = core._tenant_record(session, Movement, tenant_id, movement_id)
    if movement.type != "return" or not movement.to_location_id:
        raise core.InvalidOperation(
            "Return disposition requires arrived customer-return goods."
        )
    return movement


def _label(movement: Movement, *, normal_location_id: str | None) -> str:
    if movement.type == "transfer":
        return (
            "restock"
            if normal_location_id and movement.to_location_id == normal_location_id
            else "quarantine_repair"
        )
    if movement.type == "adjustment":
        return "scrap_loss"
    if movement.type == "supplier_return":
        return "return_to_supplier"
    return "other"


def return_disposition_summary(
    session: Session, tenant_id: str, return_movement_id: str
) -> dict[str, Any]:
    arrived = _return_movement(session, tenant_id, return_movement_id)
    commitment = (
        core._tenant_record(session, Commitment, tenant_id, arrived.commitment_id)
        if arrived.commitment_id
        else None
    )
    corrections = {
        row.original_movement_id: row
        for row in session.scalars(
            select(MovementCorrection).where(
                MovementCorrection.tenant_id == tenant_id,
                MovementCorrection.original_movement_id.in_(
                    select(Movement.id).where(
                        Movement.tenant_id == tenant_id,
                        Movement.resolves_movement_id == arrived.id,
                    )
                ),
            )
        )
    }
    source_ids = select(Movement.source_record_id).where(
        Movement.tenant_id == tenant_id,
        Movement.resolves_movement_id == arrived.id,
        Movement.source_record_id.is_not(None),
    )
    sources = {
        row.id: row
        for row in session.scalars(
            select(SourceRecord).where(
                SourceRecord.tenant_id == tenant_id,
                SourceRecord.id.in_(source_ids),
            )
        )
    }
    history = []
    totals = {key: Decimal(0) for key in DISPOSITIONS}
    for row in session.scalars(
        select(Movement)
        .where(
            Movement.tenant_id == tenant_id,
            Movement.resolves_movement_id == arrived.id,
        )
        .order_by(Movement.occurred_at, Movement.id)
    ):
        disposition = _label(
            row, normal_location_id=commitment.location_id if commitment else None
        )
        corrected = row.id in corrections
        source = sources.get(row.source_record_id or "")
        payload = json.loads(source.payload) if source else {}
        if not corrected and disposition in totals:
            totals[disposition] += core.decimal(row.quantity)
        history.append(
            {
                "id": row.id,
                "disposition": disposition,
                "quantity": core.decimal(row.quantity),
                "from_location_id": row.from_location_id,
                "to_location_id": row.to_location_id,
                "handling_unit_id": row.handling_unit_id,
                "lot_id": row.lot_id,
                "serial_unit_id": row.serial_unit_id,
                "reason": payload.get("reason"),
                "occurred_at": row.occurred_at,
                "corrected": corrected,
                "correction_id": corrections[row.id].id if corrected else None,
            }
        )
    resolved = sum(totals.values(), Decimal(0))
    return {
        "return_movement_id": arrived.id,
        "commitment_id": arrived.commitment_id,
        "item_id": arrived.item_id,
        "arrival_location_id": arrived.to_location_id,
        "handling_unit_id": arrived.handling_unit_id,
        "lot_id": arrived.lot_id,
        "serial_unit_id": arrived.serial_unit_id,
        "arrived": core.decimal(arrived.quantity),
        "resolved": resolved,
        "unresolved": core.decimal(arrived.quantity) - resolved,
        "totals": totals,
        "history": history,
    }


def preview_return_disposition(
    session: Session,
    tenant_id: str,
    return_movement_id: str,
    disposition: str,
    quantity: Decimal | str,
    *,
    destination_location_id: str | None = None,
    reason: str | None = None,
) -> dict[str, Any]:
    if disposition not in DISPOSITIONS:
        raise core.InvalidOperation("Unsupported return disposition.")
    before = return_disposition_summary(session, tenant_id, return_movement_id)
    qty = core.positive(quantity)
    if qty > before["unresolved"]:
        raise core.InvalidOperation(
            "Return disposition exceeds unresolved arrived quantity."
        )
    if disposition in {"restock", "quarantine_repair"} and not destination_location_id:
        raise core.InvalidOperation(
            "This return disposition requires a destination location."
        )
    if disposition == "scrap_loss" and not (reason or "").strip():
        raise core.InvalidOperation("Scrap or loss requires a reason.")
    movement_type = {
        "restock": "transfer",
        "quarantine_repair": "transfer",
        "scrap_loss": "adjustment",
        "return_to_supplier": "supplier_return",
    }[disposition]
    arguments = {
        "movement_type": movement_type,
        "item_id": before["item_id"],
        "quantity": qty,
        "from_location_id": before["arrival_location_id"],
        "to_location_id": destination_location_id
        if disposition in {"restock", "quarantine_repair"}
        else None,
        "reason": (reason or "Returned to supplier").strip()
        if disposition in {"scrap_loss", "return_to_supplier"}
        else None,
        "resolves_movement_id": return_movement_id,
        "handling_unit_id": before["handling_unit_id"],
        "lot_id": before["lot_id"],
        "serial_unit_id": before["serial_unit_id"],
    }
    core._append_movement(session, tenant_id, **arguments, validate_only=True)
    return {
        "disposition": disposition,
        "quantity": qty,
        "before": before,
        "after": {
            "resolved": before["resolved"] + qty,
            "unresolved": before["unresolved"] - qty,
            "totals": {
                **before["totals"],
                disposition: before["totals"][disposition] + qty,
            },
        },
        "movement": arguments,
    }


def record_return_disposition(
    session: Session,
    tenant_id: str,
    return_movement_id: str,
    disposition: str,
    quantity: Decimal | str,
    *,
    destination_location_id: str | None = None,
    reason: str | None = None,
    action_id: str | None = None,
    _commit: bool = True,
) -> Movement:
    core._require_business_mutation(session, tenant_id, "record_return_disposition")
    with session.begin_nested():
        arrived = session.scalar(
            select(Movement)
            .where(
                Movement.tenant_id == tenant_id,
                Movement.id == return_movement_id,
            )
            .with_for_update()
        )
        if arrived is None:
            raise core.NotFound("Return movement was not found.")
        reviewed = preview_return_disposition(
            session,
            tenant_id,
            return_movement_id,
            disposition,
            quantity,
            destination_location_id=destination_location_id,
            reason=reason,
        )
        source = core.create_master_source_record(
            session,
            tenant_id,
            "return_disposition",
            "manual",
            action_id or uid("return-disposition"),
            {
                "return_movement_id": return_movement_id,
                "disposition": disposition,
                "quantity": str(reviewed["quantity"]),
                "destination_location_id": destination_location_id,
                "reason": reason,
            },
            _commit=False,
        )
        movement = core.record_movement(
            session,
            tenant_id,
            action_id=action_id,
            source_record_id=source.id,
            _commit=False,
            **reviewed["movement"],
        )
        session.flush()
    if _commit:
        session.commit()
    return movement
