from decimal import Decimal

import pytest

from reality.services.core import (
    InvalidOperation,
    active_reserved,
    cancel_commitment,
    create_commitment,
    create_location,
    fulfilled_quantity,
    inventory_rows,
    open_quantity,
    record_movement,
    release_reservation,
    reserve,
    stock_at,
)


def customer_commitment(session, business, quantity=30):
    return create_commitment(
        session,
        business.tenant.id,
        "customer_delivery",
        business.company.id,
        business.customer.id,
        business.item.id,
        business.location.id,
        quantity,
        "2026-09-03",
        amount=1470,
    )


def test_shortage_reservation_and_release(session, business):
    record_movement(
        session,
        business.tenant.id,
        "opening_stock",
        business.item.id,
        20,
        to_location_id=business.location.id,
    )
    commitment = customer_commitment(session, business)

    result = reserve(session, business.tenant.id, commitment.id)

    assert result.requested == Decimal("30.0000")
    assert result.reserved == Decimal("20.0000")
    assert result.shortage == Decimal("10.0000")
    assert stock_at(session, business.tenant.id, business.item.id) == Decimal("20.0000")
    assert active_reserved(session, business.tenant.id, business.item.id) == Decimal(
        "20.0000"
    )
    release_reservation(session, business.tenant.id, result.reservation.id)
    assert active_reserved(session, business.tenant.id, business.item.id) == 0


def test_partial_shipments_derive_fulfillment_and_consume_reservations(
    session, business
):
    record_movement(
        session,
        business.tenant.id,
        "opening_stock",
        business.item.id,
        30,
        to_location_id=business.location.id,
    )
    commitment = customer_commitment(session, business)
    reserve(session, business.tenant.id, commitment.id)

    record_movement(
        session,
        business.tenant.id,
        "shipment",
        business.item.id,
        10,
        from_location_id=business.location.id,
        commitment_id=commitment.id,
    )
    assert fulfilled_quantity(session, business.tenant.id, commitment.id) == Decimal(
        "10.0000"
    )
    assert open_quantity(session, business.tenant.id, commitment.id) == Decimal(
        "20.0000"
    )
    assert commitment.status == "open"
    assert active_reserved(session, business.tenant.id, business.item.id) == Decimal(
        "20.0000"
    )

    record_movement(
        session,
        business.tenant.id,
        "shipment",
        business.item.id,
        20,
        from_location_id=business.location.id,
        commitment_id=commitment.id,
    )
    assert fulfilled_quantity(session, business.tenant.id, commitment.id) == Decimal(
        "30.0000"
    )
    assert open_quantity(session, business.tenant.id, commitment.id) == 0
    assert commitment.status == "fulfilled"
    assert active_reserved(session, business.tenant.id, business.item.id) == 0


def test_supplier_receipts_drive_stock_and_incoming_open_quantity(session, business):
    incoming = create_commitment(
        session,
        business.tenant.id,
        "supplier_delivery",
        business.supplier.id,
        business.company.id,
        business.item.id,
        business.location.id,
        20,
        "2026-09-05",
        amount=600,
    )
    record_movement(
        session,
        business.tenant.id,
        "receipt",
        business.item.id,
        8,
        to_location_id=business.location.id,
        commitment_id=incoming.id,
    )

    row = inventory_rows(session, business.tenant.id)[0]
    assert row["physical"] == Decimal("8.0000")
    assert row["incoming"] == Decimal("12.0000")
    assert row["projected"] == Decimal("20.0000")


def test_cancel_preserves_commitment_and_releases_allocation(session, business):
    record_movement(
        session,
        business.tenant.id,
        "opening_stock",
        business.item.id,
        5,
        to_location_id=business.location.id,
    )
    commitment = customer_commitment(session, business, 5)
    reserve(session, business.tenant.id, commitment.id)

    cancel_commitment(session, business.tenant.id, commitment.id, reason="Test cancellation")

    assert commitment.status == "cancelled"
    assert active_reserved(session, business.tenant.id, business.item.id) == 0
    assert stock_at(session, business.tenant.id, business.item.id) == Decimal("5.0000")


def test_cannot_ship_more_than_stock(session, business):
    commitment = customer_commitment(session, business, 2)
    with pytest.raises(InvalidOperation, match="physical stock"):
        record_movement(
            session,
            business.tenant.id,
            "shipment",
            business.item.id,
            2,
            from_location_id=business.location.id,
            commitment_id=commitment.id,
        )


def test_transfer_return_and_reasoned_adjustment_reconcile_by_location(
    session, business
):
    returns = create_location(session, business.tenant.id, "Returns Area")
    record_movement(
        session,
        business.tenant.id,
        "opening_stock",
        business.item.id,
        20,
        to_location_id=business.location.id,
    )
    record_movement(
        session,
        business.tenant.id,
        "transfer",
        business.item.id,
        3,
        from_location_id=business.location.id,
        to_location_id=returns.id,
    )
    record_movement(
        session,
        business.tenant.id,
        "return",
        business.item.id,
        2,
        to_location_id=returns.id,
    )
    record_movement(
        session,
        business.tenant.id,
        "adjustment",
        business.item.id,
        1,
        from_location_id=returns.id,
        reason="Damaged item written off",
    )

    assert stock_at(
        session, business.tenant.id, business.item.id, business.location.id
    ) == Decimal("17.0000")
    assert stock_at(
        session, business.tenant.id, business.item.id, returns.id
    ) == Decimal("4.0000")
    assert stock_at(session, business.tenant.id, business.item.id) == Decimal("21.0000")


def test_adjustment_requires_reason(session, business):
    with pytest.raises(InvalidOperation, match="reason"):
        record_movement(
            session,
            business.tenant.id,
            "adjustment",
            business.item.id,
            1,
            to_location_id=business.location.id,
        )
