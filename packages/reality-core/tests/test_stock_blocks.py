"""Blocked stock: block, release and scrap (spec 304 FR-001, FR-003)."""

import json
from decimal import Decimal

import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from reality.db.core import BusinessEvent, Movement, StockBlock, uid
from reality.services import core
from reality.services.stock_blocks import (
    block_stock,
    release_stock_block,
    scrap_stock_block,
    stock_blocks,
)


def _stock(session, business, quantity, item=None, location=None, **identity):
    core.record_movement(
        session,
        business.tenant.id,
        "opening_stock",
        (item or business.item).id,
        quantity,
        to_location_id=(location or business.location).id,
        **identity,
    )


def _movements(session, business):
    return session.scalar(
        select(func.count())
        .select_from(Movement)
        .where(Movement.tenant_id == business.tenant.id)
    )


def _events(session, business, event_type):
    return [
        json.loads(event.payload)
        for event in session.scalars(
            select(BusinessEvent)
            .where(
                BusinessEvent.tenant_id == business.tenant.id,
                BusinessEvent.event_type == event_type,
            )
            .order_by(BusinessEvent.sequence)
        )
    ]


def _active(session, business):
    session.expire_all()
    return [
        (row["quantity"], row["reason_code"])
        for row in stock_blocks(session, business.tenant.id)
    ]


# --- schema ---------------------------------------------------------------------------


def test_the_table_refuses_nonsense(session, business):
    def insert(**overrides):
        values = {
            "id": uid("blk"),
            "tenant_id": business.tenant.id,
            "item_id": business.item.id,
            "location_id": business.location.id,
            "quantity": Decimal(1),
            "reason_code": "quality",
            "status": "active",
            **overrides,
        }
        with session.begin_nested():
            session.add(StockBlock(**values))
            session.flush()

    insert()  # positive control
    with pytest.raises(IntegrityError, match="ck_stock_block_quantity"):
        insert(quantity=Decimal(0))
    with pytest.raises(IntegrityError, match="ck_stock_block_reason"):
        insert(reason_code="feeling")
    with pytest.raises(IntegrityError, match="ck_stock_block_status"):
        insert(status="pending")


def test_the_migration_refuses_to_drop_stated_blocks(postgres_database, monkeypatch):
    from alembic import command
    from alembic.config import Config
    from sqlalchemy import create_engine, inspect, text

    monkeypatch.setenv("REALITY_DATABASE_URL", postgres_database)
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", postgres_database)
    command.upgrade(config, "head")
    engine = create_engine(postgres_database)

    def present():
        return "stock_block" in inspect(engine).get_table_names()

    try:
        assert present()
        command.downgrade(config, "0107_item_reorder_point")
        assert not present()
        command.upgrade(config, "head")
        with engine.begin() as connection:
            connection.execute(
                text(
                    "INSERT INTO tenant (id, name, purpose, created_at) "
                    "VALUES ('ten_m304', 'Migration 304', 'business', now())"
                )
            )
            connection.execute(
                text(
                    "INSERT INTO item (id, tenant_id, sku, name, unit, is_active, "
                    "item_type, tracking_type, purchase_unit, conversion_factor) "
                    "VALUES ('itm_m304', 'ten_m304', 'M304', 'Lamp', 'pcs', true, "
                    "'stocked', 'none', 'pcs', 1)"
                )
            )
            connection.execute(
                text(
                    "INSERT INTO location (id, tenant_id, name, type, is_active, "
                    "allows_stock) VALUES ('loc_m304', 'ten_m304', 'Hamburg', "
                    "'warehouse', true, true)"
                )
            )
            connection.execute(
                text(
                    "INSERT INTO stock_block (id, tenant_id, item_id, location_id, "
                    "quantity, reason_code, note, status, created_at, created_by) "
                    "VALUES ('blk_m304', 'ten_m304', 'itm_m304', 'loc_m304', 5, "
                    "'quality', '', 'active', now(), 'human')"
                )
            )
        with pytest.raises(RuntimeError, match="stock blocks exist"):
            command.downgrade(config, "0107_item_reorder_point")
        assert present()
    finally:
        engine.dispose()


# --- blocking -------------------------------------------------------------------------


def test_a_block_holds_back_stock_without_moving_it(session, business):
    tenant = business.tenant.id
    _stock(session, business, "20")
    before = _movements(session, business)

    block = block_stock(
        session,
        tenant,
        business.item.id,
        business.location.id,
        "5",
        "quality",
        "scratches on the housing",
    )

    assert _movements(session, business) == before
    assert core.stock_at(session, tenant, business.item.id, business.location.id) == 20
    assert core.blocked_quantity(session, tenant, business.item.id) == 5
    assert (block.status, block.note) == ("active", "scratches on the housing")
    (event,) = _events(session, business, "stock_block.created")
    assert (event["quantity"], event["reason_code"]) == ("5", "quality")


def test_only_free_stock_can_be_blocked(session, business):
    tenant = business.tenant.id
    _stock(session, business, "20")
    promise = core.create_commitment(
        session,
        tenant,
        "customer_delivery",
        business.company.id,
        business.customer.id,
        business.item.id,
        business.location.id,
        "12",
        "2026-10-10",
    )
    core.reserve(session, tenant, promise.id)
    block_stock(session, tenant, business.item.id, business.location.id, "5", "quality")

    # 20 there, 12 reserved for an order, 5 already blocked: 3 are free.
    with pytest.raises(core.InvalidOperation) as refused:
        block_stock(
            session, tenant, business.item.id, business.location.id, "4", "damage"
        )
    assert refused.value.code == "stock_block_exceeds_available"
    block_stock(session, tenant, business.item.id, business.location.id, "3", "damage")
    assert core.blocked_quantity(session, tenant, business.item.id) == 8


def test_a_block_is_refused_with_its_reason(session, business):
    tenant = business.tenant.id
    _stock(session, business, "20")
    service = core.create_item(
        session, tenant, "SRV-304", "Repair", item_type="service"
    )

    def refused(item_id, quantity="1", reason="quality"):
        with pytest.raises(core.InvalidOperation) as error:
            block_stock(
                session, tenant, item_id, business.location.id, quantity, reason
            )
        return error.value.code

    assert refused(business.item.id, reason="mood") == "stock_block_reason_unsupported"
    assert refused(business.item.id, quantity="0") == "stock_block_quantity_invalid"
    assert refused(business.item.id, quantity="1.23456") == (
        "stock_block_quantity_invalid"
    )
    assert refused(service.id) == "stock_block_item_not_stocked"
    other = core.create_tenant(session, "Other GmbH")
    with pytest.raises(core.NotFound):
        block_stock(
            session, other.id, business.item.id, business.location.id, "1", "quality"
        )
    assert _active(session, business) == []


def test_a_lot_is_blocked_exactly(session, business):
    tenant = business.tenant.id
    item = core.create_item(session, tenant, "LOT-304", "Lot item", tracking_type="lot")
    good = core.create_lot(session, tenant, item.id, "L-GOOD")
    bad = core.create_lot(session, tenant, item.id, "L-BAD")
    _stock(session, business, "10", item=item, lot_id=good.id)
    _stock(session, business, "4", item=item, lot_id=bad.id)

    # A lot-tracked item is blocked by its lot.
    with pytest.raises(core.InvalidOperation) as refused:
        block_stock(session, tenant, item.id, business.location.id, "4", "expiry")
    assert refused.value.code == "inventory_lot_required"
    with pytest.raises(core.InvalidOperation) as refused:
        block_stock(
            session, tenant, item.id, business.location.id, "5", "expiry", lot_id=bad.id
        )
    assert refused.value.code == "stock_block_exceeds_available"
    block_stock(
        session, tenant, item.id, business.location.id, "4", "expiry", lot_id=bad.id
    )
    assert core.blocked_quantity(session, tenant, item.id, lot_id=bad.id) == 4
    assert core.blocked_quantity(session, tenant, item.id, lot_id=good.id) == 0


# --- release and scrap -----------------------------------------------------------------


def test_a_block_is_released_partly_then_wholly(session, business):
    tenant = business.tenant.id
    _stock(session, business, "20")
    block = block_stock(
        session, tenant, business.item.id, business.location.id, "5", "inspection"
    )
    before = _movements(session, business)

    first = release_stock_block(session, tenant, block.id, "3", reason="passed QC")
    assert _active(session, business) == [("2", "inspection")]
    assert core.blocked_quantity(session, tenant, business.item.id) == 2
    session.expire_all()
    released = session.get(StockBlock, (tenant, block.id))
    assert (released.status, released.quantity, released.resolution_reason) == (
        "released",
        Decimal("3.0000"),
        "passed QC",
    )
    rest = session.get(StockBlock, (tenant, first["remainder_block_id"]))
    assert (rest.previous_block_id, rest.quantity) == (block.id, Decimal("2.0000"))

    release_stock_block(session, tenant, rest.id, reason="passed QC")
    assert _active(session, business) == []
    assert _movements(session, business) == before
    assert [
        e["quantity"] for e in _events(session, business, "stock_block.released")
    ] == [
        "3",
        "2",
    ]


def test_scrapping_writes_the_part_off_with_one_adjustment(session, business):
    tenant = business.tenant.id
    _stock(session, business, "20")
    block = block_stock(
        session, tenant, business.item.id, business.location.id, "5", "damage"
    )

    result = scrap_stock_block(session, tenant, block.id, "4", reason="crushed")

    assert core.stock_at(session, tenant, business.item.id, business.location.id) == 16
    assert core.blocked_quantity(session, tenant, business.item.id) == 1
    movement = session.get(Movement, (tenant, result["movement_id"]))
    assert (movement.type, movement.from_location_id, movement.quantity) == (
        "adjustment",
        business.location.id,
        Decimal("4.0000"),
    )
    session.expire_all()
    assert session.get(StockBlock, (tenant, block.id)).movement_id == movement.id
    (event,) = _events(session, business, "stock_block.scrapped")
    assert (event["quantity"], event["movement_id"]) == ("4", movement.id)


def test_a_resolution_is_refused_with_its_reason(session, business):
    tenant = business.tenant.id
    _stock(session, business, "20")
    block = block_stock(
        session, tenant, business.item.id, business.location.id, "5", "quality"
    )

    with pytest.raises(core.InvalidOperation) as refused:
        release_stock_block(session, tenant, block.id, "6", reason="ok")
    assert refused.value.code == "stock_block_quantity_exceeds_block"
    with pytest.raises(core.InvalidOperation) as refused:
        release_stock_block(session, tenant, block.id, reason=" ")
    assert refused.value.code == "stock_block_reason_required"
    release_stock_block(session, tenant, block.id, reason="ok")
    with pytest.raises(core.InvalidOperation) as refused:
        scrap_stock_block(session, tenant, block.id, reason="late")
    assert refused.value.code == "stock_block_not_active"
    other = core.create_tenant(session, "Other GmbH")
    with pytest.raises(core.NotFound):
        release_stock_block(session, other.id, block.id, reason="ok")
