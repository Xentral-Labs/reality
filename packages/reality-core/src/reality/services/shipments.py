from __future__ import annotations

import json
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import and_, exists, func, or_, select
from sqlalchemy.orm import Session

from reality.db.core import (
    Commitment,
    Movement,
    MovementCorrection,
    Party,
    PartyRole,
    Shipment,
    ShipmentEvent,
    ShipmentEventSupersession,
    ShipmentPackage,
    SourceRecord,
    now,
    uid,
)
from reality.domain.shipments import (
    EVENT_TYPES,
    REPORTER_TYPES,
    ShipmentCompatibilityError,
    current_observations,
    required_party_role,
    validate_shipment_direction,
)
from reality.services.core import (
    InvalidOperation,
    NotFound,
    emit_business_event,
    record_movement,
    utc_datetime,
)


def _record(session: Session, model, tenant_id: str, record_id: str):
    value = session.scalar(
        select(model).where(model.tenant_id == tenant_id, model.id == record_id)
    )
    if value is None:
        raise NotFound(f"{model.__name__} not found.")
    return value


def _validate_source(
    session: Session, tenant_id: str, source_record_id: str | None
) -> None:
    if source_record_id:
        _record(session, SourceRecord, tenant_id, source_record_id)


def record_shipment_notice(
    session: Session,
    tenant_id: str,
    *,
    direction: str,
    purpose: str,
    counterparty_id: str,
    carrier: str | None = None,
    tracking_number: str | None = None,
    source_record_id: str | None = None,
    occurred_at: datetime | None = None,
    reporter_type: str = "counterparty",
    action_id: str | None = None,
    commit: bool = True,
) -> tuple[Shipment, ShipmentPackage, ShipmentEvent]:
    try:
        validate_shipment_direction(purpose, direction)
    except ShipmentCompatibilityError as error:
        raise InvalidOperation(str(error)) from error
    _record(session, Party, tenant_id, counterparty_id)
    role = required_party_role(purpose)
    if not session.scalar(
        select(
            exists().where(
                PartyRole.tenant_id == tenant_id,
                PartyRole.party_id == counterparty_id,
                PartyRole.role == role,
            )
        )
    ):
        raise InvalidOperation("Counterparty role does not match shipment purpose.")
    _validate_source(session, tenant_id, source_record_id)
    if reporter_type not in REPORTER_TYPES:
        raise InvalidOperation("Unsupported shipment event reporter.")
    shipment = Shipment(
        id=uid("shp"),
        tenant_id=tenant_id,
        direction=direction,
        purpose=purpose,
        counterparty_id=counterparty_id,
        source_record_id=source_record_id,
    )
    session.add(shipment)
    session.flush()
    package = ShipmentPackage(
        id=uid("pkg"),
        tenant_id=tenant_id,
        shipment_id=shipment.id,
        carrier=carrier.strip() if carrier and carrier.strip() else None,
        tracking_number=(
            tracking_number.strip()
            if tracking_number and tracking_number.strip()
            else None
        ),
        source_record_id=source_record_id,
    )
    session.add(package)
    session.flush()
    event = ShipmentEvent(
        id=uid("sev"),
        tenant_id=tenant_id,
        shipment_id=shipment.id,
        shipment_package_id=package.id,
        event_type="announced",
        reporter_type=reporter_type,
        occurred_at=utc_datetime(occurred_at),
        source_record_id=source_record_id,
    )
    session.add(event)
    session.flush()
    emit_business_event(
        session,
        tenant_id,
        "shipment.notice_recorded",
        "shipment",
        shipment.id,
        {"package_id": package.id, "direction": direction, "purpose": purpose},
        source_record_id=source_record_id,
        action_id=action_id,
        correlation_id=action_id,
    )
    if commit:
        session.commit()
    return shipment, package, event


def record_shipment_event(
    session: Session,
    tenant_id: str,
    shipment_id: str,
    *,
    event_type: str,
    reporter_type: str,
    shipment_package_id: str | None = None,
    occurred_at: datetime | None = None,
    location_text: str | None = None,
    source_record_id: str | None = None,
    external_event_id: str | None = None,
    action_id: str | None = None,
    commit: bool = True,
) -> ShipmentEvent:
    _record(session, Shipment, tenant_id, shipment_id)
    if event_type not in EVENT_TYPES or reporter_type not in REPORTER_TYPES:
        raise InvalidOperation("Unsupported shipment event kind or reporter.")
    if shipment_package_id:
        package = _record(session, ShipmentPackage, tenant_id, shipment_package_id)
        if package.shipment_id != shipment_id:
            raise InvalidOperation("Package does not belong to the shipment.")
    _validate_source(session, tenant_id, source_record_id)
    if external_event_id:
        existing = session.scalar(
            select(ShipmentEvent).where(
                ShipmentEvent.tenant_id == tenant_id,
                ShipmentEvent.external_event_id == external_event_id,
                ShipmentEvent.source_record_id == source_record_id,
            )
        )
        if existing:
            return existing
    event = ShipmentEvent(
        id=uid("sev"),
        tenant_id=tenant_id,
        shipment_id=shipment_id,
        shipment_package_id=shipment_package_id,
        event_type=event_type,
        reporter_type=reporter_type,
        occurred_at=utc_datetime(occurred_at),
        location_text=location_text,
        source_record_id=source_record_id,
        external_event_id=external_event_id,
    )
    session.add(event)
    session.flush()
    emit_business_event(
        session,
        tenant_id,
        "shipment.event_recorded",
        "shipment_event",
        event.id,
        {
            "shipment_id": shipment_id,
            "package_id": shipment_package_id,
            "event_type": event_type,
        },
        source_record_id=source_record_id,
        occurred_at=utc_datetime(occurred_at),
        action_id=action_id,
        correlation_id=action_id,
    )
    if commit:
        session.commit()
    return event


def supersede_shipment_event(
    session: Session,
    tenant_id: str,
    event_id: str,
    *,
    reason: str,
    replacement_event_id: str | None = None,
    actor_context: dict[str, Any] | None = None,
    source_record_id: str | None = None,
    action_id: str | None = None,
    commit: bool = True,
) -> ShipmentEventSupersession:
    event = _record(session, ShipmentEvent, tenant_id, event_id)
    if not reason.strip():
        raise InvalidOperation("Shipment event correction reason is required.")
    replacement = None
    if replacement_event_id:
        replacement = _record(session, ShipmentEvent, tenant_id, replacement_event_id)
        if replacement.shipment_id != event.shipment_id or replacement.id == event.id:
            raise InvalidOperation("Replacement must be another event on the shipment.")
    _validate_source(session, tenant_id, source_record_id)
    existing = session.scalar(
        select(ShipmentEventSupersession).where(
            ShipmentEventSupersession.tenant_id == tenant_id,
            ShipmentEventSupersession.superseded_event_id == event_id,
        )
    )
    if existing:
        return existing
    result = ShipmentEventSupersession(
        id=uid("ses"),
        tenant_id=tenant_id,
        superseded_event_id=event_id,
        replacement_event_id=replacement.id if replacement else None,
        reason=reason.strip(),
        actor_context=json.dumps(actor_context or {}, sort_keys=True),
        source_record_id=source_record_id,
    )
    session.add(result)
    session.flush()
    emit_business_event(
        session,
        tenant_id,
        "shipment.event_superseded",
        "shipment_event",
        event_id,
        {"supersession_id": result.id, "replacement_event_id": replacement_event_id},
        source_record_id=source_record_id,
        action_id=action_id,
        correlation_id=action_id,
    )
    if commit:
        session.commit()
    return result


def record_packaged_execution(
    session: Session,
    tenant_id: str,
    *,
    direction: str,
    purpose: str,
    counterparty_id: str,
    movements: list[dict[str, Any]],
    carrier: str | None = None,
    tracking_number: str | None = None,
    source_record_id: str | None = None,
    occurred_at: datetime | None = None,
    action_id: str | None = None,
    commit: bool = True,
) -> dict[str, Any]:
    if purpose == "customer_delivery":
        from reality.services.fulfillment_readiness import fulfillment_readiness

        for movement_arguments in movements:
            commitment_id = movement_arguments.get("commitment_id")
            if not commitment_id:
                raise InvalidOperation(
                    "Customer dispatch requires a delivery commitment."
                )
            try:
                proposed_quantity = Decimal(str(movement_arguments["quantity"]))
            except (KeyError, ValueError, ArithmeticError):
                raise InvalidOperation(
                    "Customer dispatch requires a valid movement quantity."
                ) from None
            readiness = fulfillment_readiness(
                session,
                tenant_id,
                commitment_id,
                proposed_quantity=proposed_quantity,
            )
            if not readiness.ship_ready:
                raise InvalidOperation(
                    "Shipment blocked: "
                    + ", ".join(readiness.blocker_codes)
                    + f" (required {readiness.required_amount} "
                    + f"{readiness.currency}, received "
                    + f"{readiness.received_amount} {readiness.currency})."
                )
    shipment, package, notice = record_shipment_notice(
        session,
        tenant_id,
        direction=direction,
        purpose=purpose,
        counterparty_id=counterparty_id,
        carrier=carrier,
        tracking_number=tracking_number,
        source_record_id=source_record_id,
        occurred_at=occurred_at,
        reporter_type="company",
        action_id=action_id,
        commit=False,
    )
    expected_type = {
        "customer_delivery": "shipment",
        "supplier_delivery": "receipt",
        "customer_return": "return",
        "supplier_return": "supplier_return",
    }[purpose]
    created = []
    for movement_arguments in movements:
        supplied_type = movement_arguments.get("movement_type", expected_type)
        if supplied_type != expected_type:
            raise InvalidOperation("Movement type does not match the shipment purpose.")
        arguments = {**movement_arguments, "movement_type": supplied_type}
        arguments.pop("shipment_package_id", None)
        created.append(
            record_movement(
                session,
                tenant_id,
                shipment_package_id=package.id,
                source_record_id=arguments.pop("source_record_id", source_record_id),
                action_id=action_id,
                _commit=False,
                **arguments,
            )
        )
    if not created:
        raise InvalidOperation("Packaged execution requires at least one movement.")
    if commit:
        session.commit()
    return {
        "shipment_id": shipment.id,
        "package_id": package.id,
        "notice_event_id": notice.id,
        "movement_ids": [movement.id for movement in created],
    }


def _details(
    session: Session, tenant_id: str, shipments: list[Shipment]
) -> dict[str, dict[str, Any]]:
    shipment_ids = [shipment.id for shipment in shipments]
    if not shipment_ids:
        return {}
    packages = list(
        session.scalars(
            select(ShipmentPackage)
            .where(
                ShipmentPackage.tenant_id == tenant_id,
                ShipmentPackage.shipment_id.in_(shipment_ids),
            )
            .order_by(ShipmentPackage.created_at, ShipmentPackage.id)
        )
    )
    package_ids = [package.id for package in packages]
    movements = (
        list(
            session.scalars(
                select(Movement)
                .where(
                    Movement.tenant_id == tenant_id,
                    Movement.shipment_package_id.in_(package_ids),
                    ~exists().where(
                        MovementCorrection.tenant_id == tenant_id,
                        MovementCorrection.original_movement_id == Movement.id,
                    ),
                )
                .order_by(Movement.occurred_at, Movement.id)
            )
        )
        if package_ids
        else []
    )
    commitment_ids = sorted(
        {movement.commitment_id for movement in movements if movement.commitment_id}
    )
    commitments = (
        list(
            session.scalars(
                select(Commitment).where(
                    Commitment.tenant_id == tenant_id,
                    Commitment.id.in_(commitment_ids),
                )
            )
        )
        if commitment_ids
        else []
    )
    commitments_by_id = {commitment.id: commitment for commitment in commitments}
    event_rows = list(
        session.execute(
            select(ShipmentEvent, ShipmentEventSupersession)
            .outerjoin(
                ShipmentEventSupersession,
                and_(
                    ShipmentEventSupersession.tenant_id == tenant_id,
                    ShipmentEventSupersession.superseded_event_id == ShipmentEvent.id,
                ),
            )
            .where(
                ShipmentEvent.tenant_id == tenant_id,
                ShipmentEvent.shipment_id.in_(shipment_ids),
            )
            .order_by(
                ShipmentEvent.occurred_at.asc().nulls_last(),
                ShipmentEvent.recorded_at,
                ShipmentEvent.id,
            )
        )
    )
    events = [event for event, supersession in event_rows if supersession is None]
    event_history_by_shipment = {
        shipment_id: [
            (event, supersession)
            for event, supersession in event_rows
            if event.shipment_id == shipment_id
        ]
        for shipment_id in shipment_ids
    }
    packages_by_shipment = {
        shipment_id: [p for p in packages if p.shipment_id == shipment_id]
        for shipment_id in shipment_ids
    }
    shipment_by_package = {package.id: package.shipment_id for package in packages}
    movements_by_shipment = {
        shipment_id: [
            movement
            for movement in movements
            if shipment_by_package.get(movement.shipment_package_id) == shipment_id
        ]
        for shipment_id in shipment_ids
    }
    events_by_shipment = {
        shipment_id: [event for event in events if event.shipment_id == shipment_id]
        for shipment_id in shipment_ids
    }

    def render(shipment: Shipment) -> dict[str, Any]:
        shipment_packages = packages_by_shipment[shipment.id]
        shipment_movements = movements_by_shipment[shipment.id]
        shipment_events = events_by_shipment[shipment.id]
        shipment_event_history = event_history_by_shipment[shipment.id]
        observations = current_observations(
            direction=shipment.direction,
            package_ids=[package.id for package in shipment_packages],
            effective_movements=(
                {
                    "package_id": movement.shipment_package_id,
                    "occurred_at": movement.occurred_at,
                }
                for movement in shipment_movements
            ),
            current_events=(
                {
                    "package_id": event.shipment_package_id,
                    "event_type": event.event_type,
                    "occurred_at": event.occurred_at,
                }
                for event in shipment_events
            ),
        )
        promised = {
            movement.commitment_id: commitments_by_id[movement.commitment_id]
            for movement in shipment_movements
            if movement.commitment_id in commitments_by_id
        }
        moved_quantity = sum(
            (movement.quantity for movement in shipment_movements), Decimal()
        )
        externally_delivered_quantity = (
            moved_quantity if observations["externally_delivered"] else None
        )
        return {
            "id": shipment.id,
            "direction": shipment.direction,
            "purpose": shipment.purpose,
            "counterparty_id": shipment.counterparty_id,
            "created_at": shipment.created_at,
            "source_record_id": shipment.source_record_id,
            "packages": [
                {
                    "id": package.id,
                    "carrier": package.carrier,
                    "tracking_number": package.tracking_number,
                    "source_record_id": package.source_record_id,
                }
                for package in shipment_packages
            ],
            "movements": [
                {
                    "id": movement.id,
                    "package_id": movement.shipment_package_id,
                    "type": movement.type,
                    "item_id": movement.item_id,
                    "quantity": str(movement.quantity),
                    "occurred_at": movement.occurred_at,
                    "commitment_id": movement.commitment_id,
                }
                for movement in shipment_movements
            ],
            "events": [
                {
                    "id": event.id,
                    "package_id": event.shipment_package_id,
                    "event_type": event.event_type,
                    "reporter_type": event.reporter_type,
                    "occurred_at": event.occurred_at,
                    "location_text": event.location_text,
                    "source_record_id": event.source_record_id,
                }
                for event in shipment_events
            ],
            "event_history": [
                {
                    "id": event.id,
                    "package_id": event.shipment_package_id,
                    "event_type": event.event_type,
                    "reporter_type": event.reporter_type,
                    "occurred_at": event.occurred_at,
                    "recorded_at": event.recorded_at,
                    "location_text": event.location_text,
                    "source_record_id": event.source_record_id,
                    "superseded": supersession is not None,
                    "supersession_id": supersession.id if supersession else None,
                    "supersession_reason": supersession.reason
                    if supersession
                    else None,
                    "replacement_event_id": (
                        supersession.replacement_event_id if supersession else None
                    ),
                }
                for event, supersession in shipment_event_history
            ],
            "observations": observations,
            "quantities": {
                "promised": str(
                    sum(
                        (commitment.quantity for commitment in promised.values()),
                        Decimal(),
                    )
                )
                if promised
                else None,
                "announced": None,
                "dispatched": (
                    str(moved_quantity) if shipment.direction == "outbound" else None
                ),
                "externally_delivered": (
                    str(externally_delivered_quantity)
                    if externally_delivered_quantity is not None
                    else None
                ),
                "received": (
                    str(moved_quantity) if shipment.direction == "inbound" else None
                ),
            },
            "discrepancies": {
                "external_delivery_without_warehouse_receipt": (
                    shipment.direction == "inbound"
                    and observations["externally_delivered"]
                    and not observations["received"]
                ),
                "warehouse_receipt_without_external_delivery": (
                    shipment.direction == "inbound"
                    and observations["received"]
                    and not observations["externally_delivered"]
                ),
            },
            "observed_at": datetime.now(UTC),
        }

    return {shipment.id: render(shipment) for shipment in shipments}


def _detail(session: Session, tenant_id: str, shipment: Shipment) -> dict[str, Any]:
    return _details(session, tenant_id, [shipment])[shipment.id]


def shipment_explain(
    session: Session, tenant_id: str, shipment_id: str
) -> dict[str, Any]:
    shipment = session.scalar(
        select(Shipment).where(
            Shipment.tenant_id == tenant_id, Shipment.id == shipment_id
        )
    )
    if shipment is None:
        package = session.scalar(
            select(ShipmentPackage).where(
                ShipmentPackage.tenant_id == tenant_id,
                ShipmentPackage.id == shipment_id,
            )
        )
        if package is None:
            raise NotFound("Shipment not found.")
        shipment = _record(session, Shipment, tenant_id, package.shipment_id)
    return _detail(session, tenant_id, shipment)


def shipments_list(
    session: Session,
    tenant_id: str,
    *,
    page: int = 1,
    size: int = 50,
    query: str = "",
    direction: str = "",
    purpose: str = "",
    counterparty_id: str = "",
    carrier: str = "",
    tracking: str = "",
    created_from: datetime | None = None,
    created_to: datetime | None = None,
    observation: str = "",
) -> dict[str, Any]:
    if direction and direction not in {"inbound", "outbound"}:
        raise InvalidOperation("Unsupported shipment direction.")
    if purpose:
        try:
            required_party_role(purpose)
        except ShipmentCompatibilityError as error:
            raise InvalidOperation(str(error)) from error
    statement = select(Shipment).where(Shipment.tenant_id == tenant_id)
    if direction:
        statement = statement.where(Shipment.direction == direction)
    if purpose:
        statement = statement.where(Shipment.purpose == purpose)
    if counterparty_id:
        statement = statement.where(Shipment.counterparty_id == counterparty_id)
    if created_from:
        statement = statement.where(Shipment.created_at >= utc_datetime(created_from))
    if created_to:
        statement = statement.where(Shipment.created_at <= utc_datetime(created_to))
    if query.strip() or carrier.strip() or tracking.strip():
        package_filter = select(ShipmentPackage.shipment_id).where(
            ShipmentPackage.tenant_id == tenant_id
        )
        if query.strip():
            pattern = f"%{query.strip()}%"
            package_filter = package_filter.where(
                or_(
                    ShipmentPackage.tracking_number.ilike(pattern),
                    ShipmentPackage.carrier.ilike(pattern),
                )
            )
        if carrier.strip():
            package_filter = package_filter.where(
                ShipmentPackage.carrier.ilike(carrier.strip())
            )
        if tracking.strip():
            package_filter = package_filter.where(
                ShipmentPackage.tracking_number.ilike(f"%{tracking.strip()}%")
            )
        statement = statement.where(Shipment.id.in_(package_filter))
    if observation:
        supported = {
            "announced",
            "dispatched",
            "received",
            "externally_delivered",
            "has_exception",
        }
        if observation not in supported:
            raise InvalidOperation("Unsupported shipment observation.")
        effective_movement = exists().where(
            ShipmentPackage.tenant_id == tenant_id,
            ShipmentPackage.shipment_id == Shipment.id,
            Movement.tenant_id == tenant_id,
            Movement.shipment_package_id == ShipmentPackage.id,
            ~exists().where(
                MovementCorrection.tenant_id == tenant_id,
                MovementCorrection.original_movement_id == Movement.id,
            ),
        )

        def current_event(event_type: str, *, package_id=None):
            clauses = [
                ShipmentEvent.tenant_id == tenant_id,
                ShipmentEvent.shipment_id == Shipment.id,
                ShipmentEvent.event_type == event_type,
                ~exists().where(
                    ShipmentEventSupersession.tenant_id == tenant_id,
                    ShipmentEventSupersession.superseded_event_id == ShipmentEvent.id,
                ),
            ]
            if package_id is not None:
                clauses.append(ShipmentEvent.shipment_package_id == package_id)
            return exists().where(*clauses)

        filters = {
            "announced": current_event("announced"),
            "dispatched": and_(Shipment.direction == "outbound", effective_movement),
            "received": and_(Shipment.direction == "inbound", effective_movement),
            "has_exception": current_event("delivery_exception"),
            "externally_delivered": and_(
                exists().where(
                    ShipmentPackage.tenant_id == tenant_id,
                    ShipmentPackage.shipment_id == Shipment.id,
                ),
                ~exists().where(
                    ShipmentPackage.tenant_id == tenant_id,
                    ShipmentPackage.shipment_id == Shipment.id,
                    ~current_event("delivered", package_id=ShipmentPackage.id),
                ),
            ),
        }
        statement = statement.where(filters[observation])
    total = int(
        session.scalar(select(func.count()).select_from(statement.subquery())) or 0
    )
    size = max(1, min(size, 100))
    pages = max(1, (total + size - 1) // size)
    page = max(1, min(page, pages))
    rows = list(
        session.scalars(
            statement.order_by(Shipment.created_at.desc(), Shipment.id)
            .offset((page - 1) * size)
            .limit(size)
        )
    )
    return {
        "items": list(_details(session, tenant_id, rows).values()),
        "page": {
            "number": page,
            "size": size,
            "total": total,
            "pages": pages,
            "has_next": page < pages,
            "has_previous": page > 1,
        },
        "scope": {
            "tenant_id": tenant_id,
            "query": query,
            "direction": direction,
            "purpose": purpose,
            "counterparty_id": counterparty_id,
            "carrier": carrier,
            "tracking": tracking,
            "created_from": utc_datetime(created_from) if created_from else None,
            "created_to": utc_datetime(created_to) if created_to else None,
            "observation": observation,
        },
        "observed_at": now(),
    }
