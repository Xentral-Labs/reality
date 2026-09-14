import pytest

from reality.services.core import (
    InvalidOperation,
    active_party_delivery_hold,
    create_commitment,
    hold_party_delivery,
    record_movement,
    release_party_delivery_hold,
    reserve,
)


def test_customer_delivery_hold_blocks_only_shipment(session, business):
    record_movement(
        session,
        business.tenant.id,
        "opening_stock",
        business.item.id,
        5,
        to_location_id=business.location.id,
    )
    commitment = create_commitment(
        session,
        business.tenant.id,
        "customer_delivery",
        business.company.id,
        business.customer.id,
        business.item.id,
        business.location.id,
        2,
        "2026-09-05",
    )
    hold = hold_party_delivery(
        session,
        business.tenant.id,
        business.customer.id,
        "credit_check",
        "Customer credit review",
    )

    assert reserve(session, business.tenant.id, commitment.id).reserved == 2
    with pytest.raises(InvalidOperation, match="delivery hold"):
        record_movement(
            session,
            business.tenant.id,
            "shipment",
            business.item.id,
            2,
            from_location_id=business.location.id,
            commitment_id=commitment.id,
        )
    assert (
        active_party_delivery_hold(session, business.tenant.id, business.customer.id)
        == hold
    )

    released = release_party_delivery_hold(
        session, business.tenant.id, business.customer.id
    )
    assert released == [hold]
    movement = record_movement(
        session,
        business.tenant.id,
        "shipment",
        business.item.id,
        2,
        from_location_id=business.location.id,
        commitment_id=commitment.id,
    )
    assert movement.quantity == 2


def test_delivery_hold_does_not_block_unrelated_customer(session, business):
    hold_party_delivery(
        session,
        business.tenant.id,
        business.customer.id,
        "manual_review",
    )
    assert (
        active_party_delivery_hold(session, business.tenant.id, business.supplier.id)
        is None
    )
