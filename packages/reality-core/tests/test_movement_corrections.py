from decimal import Decimal

import pytest
from conftest import record_by_id
from sqlalchemy import select

from reality.db.core import Movement, MovementCorrection
from reality.services.core import (
    Conflict,
    InvalidOperation,
    NotFound,
    correct_movement,
    create_commitment,
    create_tenant,
    fulfilled_quantity,
    movement_correction_snapshot,
    preview_movement_correction,
    record_movement,
    stock_at,
)


def test_void_receipt_appends_exact_correction_and_preserves_original(
    session, business
):
    original = record_movement(
        session,
        business.tenant.id,
        "receipt",
        business.item.id,
        10,
        to_location_id=business.location.id,
    )

    result = correct_movement(
        session,
        business.tenant.id,
        original.id,
        reason="Receipt quantity was keyed incorrectly",
    )

    session.refresh(original)
    compensation = record_by_id(session, Movement, result.compensating_movement_id)
    relation = session.scalar(
        select(MovementCorrection).where(
            MovementCorrection.original_movement_id == original.id
        )
    )
    assert original.type == "receipt"
    assert original.quantity == Decimal("10.0000")
    assert original.to_location_id == business.location.id
    assert compensation.type == "correction"
    assert compensation.quantity == original.quantity
    assert compensation.from_location_id == business.location.id
    assert compensation.to_location_id is None
    assert compensation.commitment_id is None
    assert compensation.source_record_id is None
    assert relation.reason == "Receipt quantity was keyed incorrectly"
    assert stock_at(session, business.tenant.id, business.item.id) == 0


def test_replacement_is_atomic_and_becomes_the_only_net_effect(session, business):
    original = record_movement(
        session,
        business.tenant.id,
        "receipt",
        business.item.id,
        10,
        to_location_id=business.location.id,
    )
    preview = preview_movement_correction(
        session,
        business.tenant.id,
        original.id,
        reason="Actual receipt was seven",
        replacement={
            "type": "receipt",
            "item_id": business.item.id,
            "quantity": "7",
            "to_location_id": business.location.id,
        },
    )

    result = correct_movement(
        session,
        business.tenant.id,
        original.id,
        reason="Actual receipt was seven",
        replacement=preview["replacement"],
        expected_revision=preview["revision"],
        preview_fingerprint=preview["request_fingerprint"],
    )

    replacement = record_by_id(session, Movement, result.replacement_movement_id)
    assert replacement.type == "receipt"
    assert replacement.quantity == Decimal("7.0000")
    assert stock_at(session, business.tenant.id, business.item.id) == Decimal("7.0000")


def test_shipment_correction_restores_fulfilment_without_rewriting_original(
    session, business
):
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
        5,
        "2026-09-03",
    )
    shipment = record_movement(
        session,
        business.tenant.id,
        "shipment",
        business.item.id,
        5,
        from_location_id=business.location.id,
        commitment_id=commitment.id,
    )
    assert commitment.status == "fulfilled"

    correct_movement(
        session,
        business.tenant.id,
        shipment.id,
        reason="Shipment never left the warehouse",
    )

    assert fulfilled_quantity(session, business.tenant.id, commitment.id) == 0
    assert commitment.status == "open"
    assert stock_at(session, business.tenant.id, business.item.id) == Decimal("5.0000")


def test_identical_retry_ignores_actor_context_and_divergent_retry_conflicts(
    session, business
):
    original = record_movement(
        session,
        business.tenant.id,
        "receipt",
        business.item.id,
        1,
        to_location_id=business.location.id,
    )
    first = correct_movement(
        session,
        business.tenant.id,
        original.id,
        reason="Duplicate scan",
        actor_context={"surface": "web"},
    )
    replay = correct_movement(
        session,
        business.tenant.id,
        original.id,
        reason="Duplicate scan",
        actor_context={"surface": "cli"},
    )
    assert replay.correction_id == first.correction_id
    assert replay.replayed is True
    with pytest.raises(Conflict, match="already corrected"):
        correct_movement(
            session,
            business.tenant.id,
            original.id,
            reason="Different reason",
        )


def test_compensation_cannot_be_corrected_and_foreign_movement_is_not_found(
    session, business
):
    original = record_movement(
        session,
        business.tenant.id,
        "receipt",
        business.item.id,
        1,
        to_location_id=business.location.id,
    )
    result = correct_movement(
        session, business.tenant.id, original.id, reason="Duplicate"
    )
    with pytest.raises(InvalidOperation, match="cannot be corrected"):
        correct_movement(
            session,
            business.tenant.id,
            result.compensating_movement_id,
            reason="No",
        )
    foreign = create_tenant(session, "Foreign")
    with pytest.raises(NotFound, match="Movement not found"):
        movement_correction_snapshot(session, foreign.id, original.id)
