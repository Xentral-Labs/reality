"""Bounded synthetic carrier observations, independent of simulated mailbox pressure."""

from datetime import datetime, timedelta

from sqlalchemy import cast, exists, select
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Session

from reality.db.core import (
    Commitment,
    Movement,
    MovementCorrection,
    Shipment,
    ShipmentEvent,
    ShipmentPackage,
    SourceRecord,
)
from reality.services import shipments


def observe_carrier(
    session: Session, tenant: str, run_id: str, start_at: datetime, at: datetime
) -> int:
    """Author current simulated handover evidence, then a later arrival; never backdate."""
    from reality.services.live_company import _namespace, _source, _store

    system = _namespace(run_id)
    run_order = exists().where(
        SourceRecord.tenant_id == tenant,
        SourceRecord.source_system == system,
        SourceRecord.source_type == "incoming",
        cast(SourceRecord.payload, JSONB)["document_id"].astext
        == Commitment.document_id,
    )
    physical_contents = (
        select(Movement.id)
        .join(
            Commitment,
            (Commitment.tenant_id == Movement.tenant_id)
            & (Commitment.id == Movement.commitment_id),
        )
        .where(
            Movement.tenant_id == tenant,
            Commitment.tenant_id == tenant,
            Movement.shipment_package_id == ShipmentPackage.id,
            Movement.type == "shipment",
            Movement.occurred_at <= at - timedelta(minutes=1),
            ~exists().where(
                MovementCorrection.tenant_id == tenant,
                MovementCorrection.original_movement_id == Movement.id,
            ),
            run_order,
        )
        .exists()
    )
    packages = session.execute(
        select(Shipment, ShipmentPackage)
        .join(
            ShipmentPackage,
            (ShipmentPackage.tenant_id == Shipment.tenant_id)
            & (ShipmentPackage.shipment_id == Shipment.id),
        )
        .where(
            Shipment.tenant_id == tenant,
            ShipmentPackage.tenant_id == tenant,
            Shipment.direction == "outbound",
            Shipment.purpose == "customer_delivery",
            Shipment.created_at >= start_at,
            Shipment.created_at <= at - timedelta(minutes=1),
            physical_contents,
            ~exists().where(
                ShipmentEvent.tenant_id == tenant,
                ShipmentEvent.shipment_id == Shipment.id,
                (ShipmentEvent.shipment_package_id == ShipmentPackage.id)
                | ShipmentEvent.shipment_package_id.is_(None),
                ShipmentEvent.event_type == "delivered",
            ),
        )
        .order_by(Shipment.created_at, ShipmentPackage.id)
        .limit(30)
    ).all()
    arrivals = 0
    for shipment, package in packages:
        handover = session.scalar(
            select(ShipmentEvent)
            .where(
                ShipmentEvent.tenant_id == tenant,
                ShipmentEvent.shipment_id == shipment.id,
                (ShipmentEvent.shipment_package_id == package.id)
                | ShipmentEvent.shipment_package_id.is_(None),
                ShipmentEvent.event_type == "handed_over",
            )
            .order_by(ShipmentEvent.occurred_at, ShipmentEvent.id)
            .limit(1)
        )
        if handover is None:
            event_type, key = "handed_over", "handover:" + package.id
        elif (
            handover.occurred_at is not None
            and handover.occurred_at <= at - timedelta(minutes=1)
        ):
            event_type, key = "delivered", "arrival:" + package.id
        else:
            continue
        if _source(session, tenant, system, "world_effect", key):
            continue
        source = _store(
            session,
            tenant,
            system,
            "carrier_evidence",
            key,
            {
                "shipment_id": shipment.id,
                "package_id": package.id,
                "event_type": event_type,
                "occurred_at": at.isoformat(),
                "origin": "simulated_carrier",
                "synthetic": True,
                "run_id": run_id,
            },
        )
        event = shipments.record_shipment_event(
            session,
            tenant,
            shipment.id,
            event_type=event_type,
            reporter_type="carrier",
            shipment_package_id=package.id,
            source_record_id=source.id,
            external_event_id=run_id + key,
            occurred_at=at,
            commit=False,
        )
        _store(
            session,
            tenant,
            system,
            "world_effect",
            key,
            {
                "kind": "carrier_handover"
                if event_type == "handed_over"
                else "customer_arrival",
                "shipment_id": shipment.id,
                "shipment_event_id": event.id,
            },
        )
        arrivals += event_type == "delivered"
    return arrivals
