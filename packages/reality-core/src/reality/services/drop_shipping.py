"""Goods a supplier ships straight to the customer (spec 337).

A drop shipment needs no link of its own. The supplier's promise is already
assigned to the customer promise it serves (a supply assignment for customer
demand), which is the shortest true relationship between the purchase and the
sale. What this adds is the supplier's statement that it shipped: one reviewed
record that keeps both promises at once.

The goods pass none of the company's locations. The supplier's promise is kept
by a receipt and the customer's by a shipment, both without a location and
under the one statement, so received, shipped, billing, crediting and supplier
invoice matching read them like any other, while stock and availability never
see them. A later customer return comes back into stock like any other return.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal
from decimal import InvalidOperation as DecimalInvalid
from typing import Any

from sqlalchemy import and_, exists, select
from sqlalchemy.orm import Session, aliased

from reality.db.core import (
    Commitment,
    Document,
    Movement,
    MovementCorrection,
    Party,
    PartyRole,
    ShipmentPackage,
    SourceRecord,
    uid,
)
from reality.services import core
from reality.services.core import emit_business_event

SOURCE_TYPE = "drop_shipment"
#: A stated time a little ahead of the clock is a clock difference, not a claim
#: about the future; the same allowance the shipment notice takes (spec 312).
CLOCK_ALLOWANCE = timedelta(minutes=5)


def ships_to_customer() -> Any:
    """Whether a supplier promise's purchase order ships to a customer.

    The purchase order states where the goods go; naming a customer there is the
    statement that the supplier ships to that customer, not to the company. Such
    supply never arrives in stock, so readers of incoming stock leave it out.
    Correlates with ``Commitment`` in the enclosing query.
    """
    return exists().where(
        Document.tenant_id == Commitment.tenant_id,
        Document.id == Commitment.document_id,
        Document.ship_to_party_id.is_not(None),
        exists().where(
            PartyRole.tenant_id == Document.tenant_id,
            PartyRole.party_id == Document.ship_to_party_id,
            PartyRole.role == "customer",
        ),
    )


def drop_ship_cover(session: Session, tenant_id: str) -> dict[str, Decimal]:
    """What drop-ship supply still to come covers, per customer promise.

    A promise served this way is never reserved, because its goods never lie in
    stock; the part a supplier still ships straight to the customer is not a
    shortage. One query when the company has no drop-ship purchase open.
    """
    from reality.services.supply_assignments import _effective_rows, assignment_split

    supplier_ids = set(
        session.scalars(
            select(Commitment.id).where(
                Commitment.tenant_id == tenant_id,
                Commitment.type == "supplier_delivery",
                Commitment.status == "open",
                ships_to_customer(),
            )
        )
    )
    if not supplier_ids:
        return {}
    rows = [
        row
        for row in _effective_rows(session, tenant_id, supplier_ids=supplier_ids)
        if row.purpose == "customer_demand" and row.customer_commitment_id
    ]
    split = assignment_split(session, tenant_id, supplier_ids)
    cover: dict[str, Decimal] = {}
    for row in rows:
        _arrived, still_to_come = split.get(row.id, (Decimal(0), Decimal(0)))
        if still_to_come > 0:
            cover[row.customer_commitment_id] = (
                cover.get(row.customer_commitment_id, Decimal(0)) + still_to_come
            )
    return cover


def _standing(movement: Any) -> Any:
    """Movements no correction has voided."""
    return ~exists().where(
        MovementCorrection.tenant_id == movement.tenant_id,
        MovementCorrection.original_movement_id == movement.id,
    )


def _pairs(
    session: Session,
    tenant_id: str,
    supplier_ids: set[str] | None = None,
    customer_ids: set[str] | None = None,
) -> list[tuple[Movement, Movement]]:
    """Standing drop shipments: the receipt and the shipment one statement wrote."""
    receipt = aliased(Movement)
    shipment = aliased(Movement)
    query = (
        select(receipt, shipment)
        .join(
            shipment,
            and_(
                shipment.tenant_id == receipt.tenant_id,
                shipment.source_record_id == receipt.source_record_id,
                shipment.type == "shipment",
                shipment.from_location_id.is_(None),
            ),
        )
        .where(
            receipt.tenant_id == tenant_id,
            receipt.type == "receipt",
            receipt.to_location_id.is_(None),
            receipt.source_record_id.is_not(None),
            _standing(receipt),
            _standing(shipment),
        )
    )
    if supplier_ids is not None:
        query = query.where(receipt.commitment_id.in_(supplier_ids))
    if customer_ids is not None:
        query = query.where(shipment.commitment_id.in_(customer_ids))
    return list(
        session.execute(query.order_by(receipt.occurred_at, receipt.id)).tuples()
    )


def _assigned(session: Session, tenant_id: str, supplier_id: str) -> dict[str, Decimal]:
    """What of the supplier's promise is assigned to each customer promise."""
    from reality.services.supply_assignments import supply_coverage

    assigned: dict[str, Decimal] = {}
    for row in supply_coverage(session, tenant_id, supplier_commitment_id=supplier_id)[
        "items"
    ]:
        if row["purpose"] == "customer_demand" and row["quantity"] > 0:
            assigned[row["customer_commitment_id"]] = (
                assigned.get(row["customer_commitment_id"], Decimal(0))
                + row["quantity"]
            )
    return assigned


def _quantity(value: Any) -> Decimal:
    try:
        stated = Decimal(str(value))
    except (TypeError, ValueError, DecimalInvalid) as error:
        raise core.InvalidOperation(code="drop_ship_quantity_invalid") from error
    if not stated.is_finite() or stated <= 0 or stated.as_tuple().exponent < -4:
        raise core.InvalidOperation(code="drop_ship_quantity_invalid")
    return stated


def _occurred_at(value: Any) -> datetime:
    if value in (None, ""):
        return core.now()
    try:
        moment = core.utc_datetime(value)
    except (TypeError, ValueError) as error:
        raise core.InvalidOperation(code="drop_ship_time_invalid") from error
    if moment is None:
        raise core.InvalidOperation(code="drop_ship_time_invalid")
    if moment > core.now() + CLOCK_ALLOWANCE:
        raise core.InvalidOperation(code="drop_ship_time_future")
    return moment


def _plain(value: Decimal) -> str:
    """A quantity as a person writes it: 2, not 2.0000."""
    return format(core.decimal(value).normalize(), "f")


def _text(value: Any) -> str | None:
    stated = str(value or "").strip()
    return stated or None


def preview_drop_shipment(
    session: Session,
    tenant_id: str,
    *,
    supplier_commitment_id: str,
    quantity: Any,
    customer_commitment_id: str | None = None,
    occurred_at: Any = None,
    carrier: str | None = None,
    tracking_number: str | None = None,
) -> dict[str, Any]:
    """What recording this drop shipment would do, recording nothing."""
    supplier = core._tenant_record(
        session, Commitment, tenant_id, str(supplier_commitment_id)
    )
    if supplier.type != "supplier_delivery" or supplier.status != "open":
        raise core.InvalidOperation(code="drop_ship_supplier_promise_not_open")
    assigned = _assigned(session, tenant_id, supplier.id)
    if not assigned:
        raise core.InvalidOperation(code="drop_ship_not_assigned")
    if customer_commitment_id in (None, ""):
        if len(assigned) != 1:
            raise core.InvalidOperation(code="drop_ship_customer_promise_required")
        customer_commitment_id = next(iter(assigned))
    customer = core._tenant_record(
        session, Commitment, tenant_id, str(customer_commitment_id)
    )
    if customer.type != "customer_delivery" or customer.status != "open":
        raise core.InvalidOperation(code="drop_ship_customer_promise_not_open")
    if customer.id not in assigned:
        raise core.InvalidOperation(code="drop_ship_not_assigned")
    purchase = (
        session.get(Document, (tenant_id, supplier.document_id))
        if supplier.document_id
        else None
    )
    sale = (
        session.get(Document, (tenant_id, customer.document_id))
        if customer.document_id
        else None
    )
    receivers = {customer.to_party_id} | (
        {sale.party_id, sale.ship_to_party_id} if sale else set()
    )
    if purchase is None or purchase.ship_to_party_id not in receivers - {None}:
        # The purchase order states where the goods go; only one naming this
        # customer is an order for the supplier to ship there.
        raise core.InvalidOperation(code="drop_ship_purchase_not_to_customer")
    stated = _quantity(quantity)
    already = sum(
        (
            core.decimal(receipt.quantity)
            for receipt, shipment in _pairs(
                session, tenant_id, {supplier.id}, {customer.id}
            )
        ),
        Decimal(0),
    )
    if stated > assigned[customer.id] - already:
        raise core.InvalidOperation(
            code="drop_ship_exceeds_assigned",
            values={"remaining": assigned[customer.id] - already},
        )
    supplier_open = core.open_quantity(session, tenant_id, supplier.id)
    customer_open = core.open_quantity(session, tenant_id, customer.id)
    if stated > supplier_open or stated > customer_open:
        raise core.InvalidOperation(code="drop_ship_exceeds_open")
    core.require_not_held(session, tenant_id, customer.id)
    moment = _occurred_at(occurred_at)
    return {
        "supplier_commitment_id": supplier.id,
        "customer_commitment_id": customer.id,
        "supplier_party_id": supplier.from_party_id,
        "customer_party_id": customer.to_party_id,
        "item_id": supplier.item_id,
        "quantity": _plain(stated),
        "assigned": _plain(assigned[customer.id]),
        "drop_shipped_before": _plain(already),
        "occurred_at": moment.isoformat(),
        "carrier": _text(carrier),
        "tracking_number": _text(tracking_number),
        "supplier_open_after": _plain(supplier_open - stated),
        "customer_open_after": _plain(customer_open - stated),
    }


def record_drop_shipment(
    session: Session,
    tenant_id: str,
    *,
    supplier_commitment_id: str,
    quantity: Any,
    customer_commitment_id: str | None = None,
    occurred_at: Any = None,
    carrier: str | None = None,
    tracking_number: str | None = None,
    action_id: str | None = None,
    _commit: bool = True,
) -> dict[str, Any]:
    """Record that the supplier shipped straight to the customer."""
    core._require_business_mutation(session, tenant_id, "record_drop_shipment")
    from reality.services.business_locks import lock_delivery_state
    from reality.services.shipments import record_shipment_notice

    with session.begin_nested():
        lock_delivery_state(session, tenant_id)
        reviewed = preview_drop_shipment(
            session,
            tenant_id,
            supplier_commitment_id=supplier_commitment_id,
            customer_commitment_id=customer_commitment_id,
            quantity=quantity,
            occurred_at=occurred_at,
            carrier=carrier,
            tracking_number=tracking_number,
        )
        source = core.create_master_source_record(
            session,
            tenant_id,
            SOURCE_TYPE,
            "manual",
            action_id or uid("drop-shipment"),
            {
                key: reviewed[key]
                for key in (
                    "supplier_commitment_id",
                    "customer_commitment_id",
                    "quantity",
                    "occurred_at",
                    "carrier",
                    "tracking_number",
                )
            },
            action_id=action_id,
            _commit=False,
        )
        moment = core.utc_datetime(reviewed["occurred_at"])
        shipment, package, _notice = record_shipment_notice(
            session,
            tenant_id,
            direction="outbound",
            purpose="customer_delivery",
            counterparty_id=reviewed["customer_party_id"],
            carrier=reviewed["carrier"],
            tracking_number=reviewed["tracking_number"],
            source_record_id=source.id,
            occurred_at=moment,
            reporter_type="company",
            action_id=action_id,
            commit=False,
        )
        received = core._append_movement(
            session,
            tenant_id,
            "receipt",
            reviewed["item_id"],
            reviewed["quantity"],
            commitment_id=reviewed["supplier_commitment_id"],
            source_record_id=source.id,
            occurred_at=moment,
            action_id=action_id,
            _drop_ship=True,
        )
        shipped = core._append_movement(
            session,
            tenant_id,
            "shipment",
            reviewed["item_id"],
            reviewed["quantity"],
            commitment_id=reviewed["customer_commitment_id"],
            source_record_id=source.id,
            shipment_package_id=package.id,
            occurred_at=moment,
            consume_reservations=False,
            action_id=action_id,
            _drop_ship=True,
        )
        emit_business_event(
            session,
            tenant_id,
            "drop_shipment.recorded",
            "shipment",
            shipment.id,
            {
                "supplier_commitment_id": reviewed["supplier_commitment_id"],
                "customer_commitment_id": reviewed["customer_commitment_id"],
                "item_id": reviewed["item_id"],
                "quantity": reviewed["quantity"],
                "receipt_movement_id": received.id,
                "shipment_movement_id": shipped.id,
            },
            source_record_id=source.id,
            occurred_at=moment,
            action_id=action_id,
            correlation_id=action_id,
        )
    if _commit:
        session.commit()
    return {
        "shipment_id": shipment.id,
        "receipt_movement_id": received.id,
        "shipment_movement_id": shipped.id,
        "source_record_id": source.id,
    }


def drop_shipments(
    session: Session, tenant_id: str, *, commitment_id: str
) -> dict[str, Any]:
    """A promise's drop shipping: what is assigned, what the supplier shipped."""
    commitment = core._tenant_record(session, Commitment, tenant_id, commitment_id)
    if commitment.type == "supplier_delivery":
        assigned = _assigned(session, tenant_id, commitment.id)
        pairs = _pairs(session, tenant_id, supplier_ids={commitment.id})
        links = [
            {
                "supplier_commitment_id": commitment.id,
                "customer_commitment_id": key,
                "assigned": value,
            }
            for key, value in sorted(assigned.items())
        ]
    elif commitment.type == "customer_delivery":
        from reality.services.supply_assignments import supply_coverage

        rows = supply_coverage(
            session, tenant_id, customer_commitment_id=commitment.id
        )["items"]
        links = [
            {
                "supplier_commitment_id": row["supplier_commitment_id"],
                "customer_commitment_id": commitment.id,
                "assigned": row["quantity"],
            }
            for row in rows
            if row["purpose"] == "customer_demand" and row["quantity"] > 0
        ]
        pairs = _pairs(session, tenant_id, customer_ids={commitment.id})
    else:
        raise core.InvalidOperation(code="drop_ship_promise_required")
    packages = {
        package.id: package
        for package in session.scalars(
            select(ShipmentPackage).where(
                ShipmentPackage.tenant_id == tenant_id,
                ShipmentPackage.id.in_(
                    {shipment.shipment_package_id for _, shipment in pairs}
                ),
            )
        )
    }
    shipped = [
        {
            "source_record_id": receipt.source_record_id,
            "supplier_commitment_id": receipt.commitment_id,
            "customer_commitment_id": shipment.commitment_id,
            "quantity": core.decimal(receipt.quantity),
            "occurred_at": core.utc_datetime(receipt.occurred_at),
            "receipt_movement_id": receipt.id,
            "shipment_movement_id": shipment.id,
            "shipment_id": packages[shipment.shipment_package_id].shipment_id
            if shipment.shipment_package_id in packages
            else None,
            "carrier": packages[shipment.shipment_package_id].carrier
            if shipment.shipment_package_id in packages
            else None,
            "tracking_number": packages[shipment.shipment_package_id].tracking_number
            if shipment.shipment_package_id in packages
            else None,
        }
        for receipt, shipment in pairs
    ]
    for link in links:
        link["drop_shipped"] = sum(
            (
                row["quantity"]
                for row in shipped
                if row["supplier_commitment_id"] == link["supplier_commitment_id"]
                and row["customer_commitment_id"] == link["customer_commitment_id"]
            ),
            Decimal(0),
        )
    supplier_ids = {link["supplier_commitment_id"] for link in links}
    suppliers = {
        row.id: row.from_party_id
        for row in session.scalars(
            select(Commitment).where(
                Commitment.tenant_id == tenant_id, Commitment.id.in_(supplier_ids)
            )
        )
    }
    names = {
        party.id: party.name
        for party in session.scalars(
            select(Party).where(
                Party.tenant_id == tenant_id,
                Party.id.in_(set(suppliers.values()) - {None}),
            )
        )
    }
    for link in links:
        party_id = suppliers.get(link["supplier_commitment_id"])
        link["supplier_party_id"] = party_id
        link["supplier"] = names.get(party_id)
    return {
        "commitment_id": commitment.id,
        "type": commitment.type,
        "links": links,
        "drop_shipments": shipped,
    }


def drop_shipment_sources(
    session: Session, tenant_id: str, source_record_ids: set[str]
) -> set[str]:
    """Which of these statements are drop shipments, in one query."""
    if not source_record_ids:
        return set()
    return set(
        session.scalars(
            select(SourceRecord.id).where(
                SourceRecord.tenant_id == tenant_id,
                SourceRecord.id.in_(source_record_ids),
                SourceRecord.source_type == SOURCE_TYPE,
            )
        )
    )


__all__ = [
    "drop_shipment_sources",
    "drop_shipments",
    "preview_drop_shipment",
    "record_drop_shipment",
]
