"""Blocked stock in every reader (spec 304 FR-002)."""

from datetime import date
from decimal import Decimal

import pytest

from reality.services import core
from reality.services.exceptions import operational_exceptions
from reality.services.fulfillment_readiness import fulfillment_readiness
from reality.services.inventory_positions import inventory_detail_rows
from reality.services.stock_blocks import block_stock, release_stock_block


def _stock(session, business, quantity, location=None, item=None, **identity):
    core.record_movement(
        session,
        business.tenant.id,
        "opening_stock",
        (item or business.item).id,
        quantity,
        to_location_id=(location or business.location).id,
        **identity,
    )


def _promise(session, business, quantity, location=None):
    return core.create_commitment(
        session,
        business.tenant.id,
        "customer_delivery",
        business.company.id,
        business.customer.id,
        business.item.id,
        (location or business.location).id,
        quantity,
        "2026-10-10",
    )


def _block(session, business, quantity, location=None, **identity):
    return block_stock(
        session,
        business.tenant.id,
        (identity.pop("item", None) or business.item).id,
        (location or business.location).id,
        quantity,
        identity.pop("reason", "quality"),
        **identity,
    )


def _inventory(session, business):
    (row,) = [
        row
        for row in core.inventory_rows(session, business.tenant.id)
        if row["item"].id == business.item.id
    ]
    return row


def _classes(session, business, class_id):
    return {
        row.record_id: row
        for row in operational_exceptions(session, business.tenant.id)
        if row.class_id == class_id
    }


def test_reserving_takes_only_unblocked_stock(session, business):
    tenant = business.tenant.id
    _stock(session, business, "20")
    _block(session, business, "5")
    promise = _promise(session, business, "20")

    result = core.reserve(session, tenant, promise.id)

    assert (result.reserved, result.shortage) == (Decimal(15), Decimal(5))


def test_releasing_a_block_makes_it_reservable_again(session, business):
    tenant = business.tenant.id
    _stock(session, business, "20")
    block = _block(session, business, "5")
    promise = _promise(session, business, "20")
    core.reserve(session, tenant, promise.id)

    release_stock_block(session, tenant, block.id, reason="passed QC")

    assert core.reserve(session, tenant, promise.id).reserved == 5


def test_blocked_stock_does_not_move(session, business):
    tenant = business.tenant.id
    munich = core.create_location(session, tenant, "Munich")
    _stock(session, business, "10")
    _block(session, business, "8")

    for kind, extra in (
        ("transfer", {"to_location_id": munich.id}),
        ("adjustment", {"reason": "count"}),
        ("shipment", {}),
    ):
        with pytest.raises(core.InvalidOperation) as refused:
            core.record_movement(
                session,
                tenant,
                kind,
                business.item.id,
                "3",
                from_location_id=business.location.id,
                **extra,
            )
        assert refused.value.code == "movement_takes_blocked_stock", kind
    # Positive control: the two unblocked pieces move.
    core.record_movement(
        session,
        tenant,
        "transfer",
        business.item.id,
        "2",
        from_location_id=business.location.id,
        to_location_id=munich.id,
    )
    assert core.stock_at(session, tenant, business.item.id, munich.id) == 2


def test_a_blocked_lot_does_not_move_while_another_does(session, business):
    tenant = business.tenant.id
    item = core.create_item(
        session, tenant, "LOT-304R", "Lot item", tracking_type="lot"
    )
    good = core.create_lot(session, tenant, item.id, "R-GOOD")
    bad = core.create_lot(session, tenant, item.id, "R-BAD")
    _stock(session, business, "10", item=item, lot_id=good.id)
    _stock(session, business, "4", item=item, lot_id=bad.id)
    _block(session, business, "4", item=item, lot_id=bad.id, reason="expiry")

    with pytest.raises(core.InvalidOperation) as refused:
        core.record_movement(
            session,
            tenant,
            "adjustment",
            item.id,
            "1",
            from_location_id=business.location.id,
            lot_id=bad.id,
            reason="count",
        )
    assert refused.value.code == "movement_takes_blocked_stock"
    core.record_movement(
        session,
        tenant,
        "adjustment",
        item.id,
        "1",
        from_location_id=business.location.id,
        lot_id=good.id,
        reason="count",
    )


def test_inventory_rows_show_what_is_blocked(session, business):
    _stock(session, business, "20")
    assert _inventory(session, business)["blocked"] == 0  # control
    _block(session, business, "5")

    row = _inventory(session, business)
    assert (row["physical"], row["blocked"], row["available"]) == (
        Decimal(20),
        Decimal(5),
        Decimal(15),
    )
    (position,) = [
        row
        for row in inventory_detail_rows(session, business.tenant.id)
        if row["item_id"] == business.item.id and row["location_id"]
    ]
    assert (position["blocked"], position["available"]) == (Decimal(5), Decimal(15))


def test_readiness_and_the_queue_do_not_count_blocked_stock(session, business):
    from reality.services import projections

    tenant = business.tenant.id
    _stock(session, business, "10")
    _block(session, business, "6")
    promise = _promise(session, business, "10")

    readiness = fulfillment_readiness(session, tenant, promise.id)
    assert readiness.physical_quantity == 4
    assert set(readiness.blocker_codes) == {
        "insufficient_reservation",
        "insufficient_stock",
    }
    projections.refresh_operational_projections(session, tenant, force=True)
    (line,) = [
        line
        for row in projections.projection_rows(
            session, tenant, projections.FULFILLMENT_QUEUE
        )
        for line in row["lines"]
        if line["commitment_id"] == promise.id
    ]
    assert Decimal(line["physical_quantity"]) == 4
    assert "insufficient_stock" in line["blocking_reasons"]


def test_without_blocks_readers_are_unchanged(session, business):
    tenant = business.tenant.id
    _stock(session, business, "10")
    promise = _promise(session, business, "10")
    core.reserve(session, tenant, promise.id)

    assert fulfillment_readiness(session, tenant, promise.id).ship_ready
    row = _inventory(session, business)
    assert (row["blocked"], row["available"]) == (0, 0)


def test_an_oversold_item_counts_blocked_stock_as_missing(session, business):
    _stock(session, business, "10")
    _promise(session, business, "8")
    assert business.item.id not in _classes(session, business, "item_oversold")

    _block(session, business, "5")
    row = _classes(session, business, "item_oversold")[business.item.id]
    assert row.causal_values["on_hand_quantity"] == 5


def test_a_reorder_point_counts_blocked_stock_as_gone(session, business):
    from reality.services.reorder_points import set_reorder_point

    tenant = business.tenant.id
    _stock(session, business, "30")
    set_reorder_point(
        session, tenant, business.item.id, business.location.id, "20", "48"
    )
    assert not _classes(session, business, "reorder_point_reached")

    _block(session, business, "15")
    (row,) = _classes(session, business, "reorder_point_reached").values()
    assert row.causal_values["available_quantity"] == 15


def test_blocked_stock_elsewhere_is_not_offered(session, business):
    tenant = business.tenant.id
    munich = core.create_location(session, tenant, "Munich")
    _stock(session, business, "4", location=munich)
    promise = _promise(session, business, "4")
    assert promise.id in _classes(session, business, "stock_in_another_location")

    _block(session, business, "4", location=munich)
    assert promise.id not in _classes(session, business, "stock_in_another_location")


def test_expired_stock_that_is_blocked_is_no_longer_reported(session, business):
    tenant = business.tenant.id
    item = core.create_item(session, tenant, "LOT-304E", "Milk", tracking_type="lot")
    lot = core.create_lot(session, tenant, item.id, "E-1", expires_at=date(2020, 1, 1))
    _stock(session, business, "6", item=item, lot_id=lot.id)

    row = _classes(session, business, "stock_expired")[lot.id]
    assert row.trace["locations"] == [
        {"location_id": business.location.id, "quantity": "6"}
    ]

    _block(session, business, "4", item=item, lot_id=lot.id, reason="expiry")
    row = _classes(session, business, "stock_expired")[lot.id]
    assert row.causal_values["held_quantity"] == 2
    _block(session, business, "2", item=item, lot_id=lot.id, reason="expiry")
    assert lot.id not in _classes(session, business, "stock_expired")
