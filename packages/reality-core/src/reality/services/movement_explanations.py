from __future__ import annotations

import json
from typing import Any

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from reality.db.core import (
    ChangeProposal,
    Commitment,
    Document,
    Movement,
    MovementCorrection,
    ReturnAnnouncement,
    ShipmentPackage,
    SourceRecord,
)
from reality.services.core import NotFound


def _link(kind: str, record_id: str | None, label: str) -> dict[str, str] | None:
    return {"kind": kind, "id": record_id, "label": label} if record_id else None


def movement_explanation(
    session: Session, tenant_id: str, movement_id: str
) -> dict[str, Any]:
    """Explain a movement from authoritative links, without storing a derivation."""
    movement = session.scalar(
        select(Movement).where(
            Movement.tenant_id == tenant_id, Movement.id == movement_id
        )
    )
    if movement is None:
        raise NotFound("Movement not found.")

    correction = session.scalar(
        select(MovementCorrection).where(
            MovementCorrection.tenant_id == tenant_id,
            or_(
                MovementCorrection.original_movement_id == movement_id,
                MovementCorrection.compensating_movement_id == movement_id,
                MovementCorrection.replacement_movement_id == movement_id,
            ),
        )
    )
    links: list[dict[str, str]] = []
    kind = "unexplained"
    summary = "No business reason or source is linked to this movement."
    reason = None
    state_change = None

    if correction:
        role = (
            "original"
            if correction.original_movement_id == movement_id
            else "compensation"
            if correction.compensating_movement_id == movement_id
            else "replacement"
        )
        kind = "correction"
        summary = f"This is the {role} movement in an inventory correction."
        reason = correction.reason
        links.append(
            {"kind": "movement_correction", "id": correction.id, "label": "Correction"}
        )
        peer_id = (
            correction.original_movement_id
            if role != "original"
            else correction.replacement_movement_id
            or correction.compensating_movement_id
        )
        if peer_id:
            links.append(
                {"kind": "movement", "id": peer_id, "label": "Related movement"}
            )
    elif movement.resolves_movement_id:
        kind = "return_disposition"
        summary = (
            "This movement records what happened to goods after they were returned."
        )
        links.append(
            {
                "kind": "movement",
                "id": movement.resolves_movement_id,
                "label": "Returned goods",
            }
        )
        from reality.services.return_dispositions import return_disposition_summary

        returned = session.scalar(
            select(Movement).where(
                Movement.tenant_id == tenant_id,
                Movement.id == movement.resolves_movement_id,
            )
        )
        disposition = return_disposition_summary(
            session, tenant_id, movement.resolves_movement_id
        )
        state_change = {
            "before": {
                "movement_id": returned.id if returned else None,
                "location_id": returned.to_location_id if returned else None,
                "quantity": returned.quantity if returned else None,
                "handling_unit_id": returned.handling_unit_id if returned else None,
                "lot_id": returned.lot_id if returned else None,
                "serial_unit_id": returned.serial_unit_id if returned else None,
            },
            "effect": {
                "movement_id": movement.id,
                "from_location_id": movement.from_location_id,
                "to_location_id": movement.to_location_id,
                "quantity": movement.quantity,
                "handling_unit_id": movement.handling_unit_id,
                "lot_id": movement.lot_id,
                "serial_unit_id": movement.serial_unit_id,
            },
            "after": {
                "resolved": disposition["resolved"],
                "unresolved": disposition["unresolved"],
            },
        }
    elif movement.return_announcement_id:
        announcement = session.scalar(
            select(ReturnAnnouncement).where(
                ReturnAnnouncement.tenant_id == tenant_id,
                ReturnAnnouncement.id == movement.return_announcement_id,
            )
        )
        kind = "return_announcement"
        summary = (
            "This movement records goods received for an announced customer return."
        )
        reason = announcement.reason if announcement else None
        links.append(
            {
                "kind": "return_announcement",
                "id": movement.return_announcement_id,
                "label": "Return announcement",
            }
        )
    elif movement.commitment_id:
        commitment = session.scalar(
            select(Commitment).where(
                Commitment.tenant_id == tenant_id,
                Commitment.id == movement.commitment_id,
            )
        )
        kind = "commitment"
        summary = "This movement fulfils a customer or supplier delivery commitment."
        links.append(
            {
                "kind": "commitment",
                "id": movement.commitment_id,
                "label": "Delivery commitment",
            }
        )
        if commitment and commitment.document_id:
            document = session.scalar(
                select(Document).where(
                    Document.tenant_id == tenant_id,
                    Document.id == commitment.document_id,
                )
            )
            links.append(
                {
                    "kind": "document",
                    "id": commitment.document_id,
                    "label": document.number if document else "Document",
                }
            )
    elif movement.shipment_package_id:
        package = session.scalar(
            select(ShipmentPackage).where(
                ShipmentPackage.tenant_id == tenant_id,
                ShipmentPackage.id == movement.shipment_package_id,
            )
        )
        kind = "shipment"
        summary = "This movement belongs to a recorded shipment package."
        links.append(
            {
                "kind": "shipment_package",
                "id": movement.shipment_package_id,
                "label": package.tracking_number or "Shipment package"
                if package
                else "Shipment package",
            }
        )
    elif movement.source_record_id:
        source = session.scalar(
            select(SourceRecord).where(
                SourceRecord.tenant_id == tenant_id,
                SourceRecord.id == movement.source_record_id,
            )
        )
        kind = "source"
        summary = "This movement was stated by an imported source record."
        links.append(
            {
                "kind": "source_record",
                "id": movement.source_record_id,
                "label": source.external_id if source else "Source record",
            }
        )
    elif movement.type == "adjustment":
        proposals = session.scalars(
            select(ChangeProposal).where(
                ChangeProposal.tenant_id == tenant_id,
                ChangeProposal.type == "inventory_adjusted",
            )
        ).all()
        proposal = next(
            (
                row
                for row in proposals
                if json.loads(row.output or "{}").get("movement_id") == movement_id
            ),
            None,
        )
        if proposal:
            kind = "explicit_reason"
            summary = "This movement is a manually stated inventory adjustment."
            reason = json.loads(proposal.input or "{}").get("reason")

    return {
        "movement_id": movement.id,
        "kind": kind,
        "explained": kind != "unexplained",
        "summary": summary,
        "reason": reason,
        "links": links,
        "source_record_id": movement.source_record_id,
        "state_change": state_change,
    }
