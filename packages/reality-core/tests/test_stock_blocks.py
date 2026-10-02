"""Blocked stock: block, release and scrap (spec 304 FR-001, FR-003; spec 316)."""

import json
from decimal import Decimal

import pytest
from sqlalchemy import func, select, text
from sqlalchemy.exc import IntegrityError

from reality.db.core import (
    BusinessEvent,
    Movement,
    StockBlock,
    StockBlockResolution,
    uid,
)
from reality.services import core
from reality.services.stock_blocks import (
    block_stock,
    release_stock_block,
    scrap_stock_block,
    stock_block_detail,
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
    # Spec 316 DR-002: nothing about a block's later fate is stored on it.
    columns = set(StockBlock.__table__.columns.keys())
    assert not columns & {
        "status",
        "resolved_at",
        "resolved_by",
        "resolution_reason",
        "previous_block_id",
        "movement_id",
    }
    assert "receipt_movement_id" in columns


def test_a_resolution_refuses_nonsense(session, business):
    tenant = business.tenant.id
    _stock(session, business, "20")
    block = block_stock(
        session, tenant, business.item.id, business.location.id, "5", "quality"
    )
    scrap = Movement(
        id=uid("mov"),
        tenant_id=tenant,
        type="adjustment",
        item_id=business.item.id,
        from_location_id=business.location.id,
        quantity=Decimal(1),
    )
    session.add(scrap)
    session.flush()

    def insert(**overrides):
        values = {
            "id": uid("sbr"),
            "tenant_id": tenant,
            "block_id": block.id,
            "kind": "release",
            "quantity": Decimal(1),
            "reason": "passed QC",
            **overrides,
        }
        with session.begin_nested():
            session.add(StockBlockResolution(**values))
            session.flush()
            session.execute(text("SET CONSTRAINTS ALL IMMEDIATE"))

    insert()  # positive control
    insert(kind="scrap", movement_id=scrap.id)  # positive control
    with pytest.raises(IntegrityError, match="ck_stock_block_resolution_quantity"):
        insert(quantity=Decimal(0))
    with pytest.raises(IntegrityError, match="ck_stock_block_resolution_kind"):
        insert(kind="forgotten")
    with pytest.raises(IntegrityError, match="ck_stock_block_resolution_reason"):
        insert(reason=" ")
    with pytest.raises(IntegrityError, match="ck_stock_block_resolution_movement"):
        insert(kind="scrap")
    with pytest.raises(IntegrityError, match="ck_stock_block_resolution_movement"):
        insert(movement_id=scrap.id)
    with pytest.raises(IntegrityError):
        insert(kind="scrap", movement_id="mov_nowhere")


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
                    "quantity, reason_code, note, created_at, created_by) "
                    "VALUES ('blk_m304', 'ten_m304', 'itm_m304', 'loc_m304', 5, "
                    "'quality', '', now(), 'human')"
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
    assert block.note == "scratches on the housing"
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


def _block(session, tenant, block_id):
    session.expire_all()
    return stock_block_detail(session, tenant, block_id)


def test_a_block_keeps_what_was_stated_through_its_resolutions(session, business):
    """Spec 316 US1: block 20, release 5, scrap 3, release the rest."""
    tenant = business.tenant.id
    _stock(session, business, "20")
    block = block_stock(
        session, tenant, business.item.id, business.location.id, "20", "quality"
    )
    before = _movements(session, business)

    first = release_stock_block(session, tenant, block.id, "5", reason="passed QC")
    assert first == {"block_id": block.id, "released": "5", "open_quantity": "15"}
    assert _movements(session, business) == before
    assert core.blocked_quantity(session, tenant, business.item.id) == 15
    assert _active(session, business) == [("20", "quality")]

    scrapped = scrap_stock_block(session, tenant, block.id, "3", reason="cracked")
    assert (scrapped["block_id"], scrapped["open_quantity"]) == (block.id, "12")
    assert core.blocked_quantity(session, tenant, business.item.id) == 12
    assert core.stock_at(session, tenant, business.item.id) == 17

    row = _block(session, tenant, block.id)
    assert (row["quantity"], row["open_quantity"], row["status"]) == (
        "20",
        "12",
        "active",
    )
    assert [
        (r["kind"], r["quantity"], r["reason"], r["movement_id"])
        for r in row["resolutions"]
    ] == [
        ("release", "5", "passed QC", None),
        ("scrap", "3", "cracked", scrapped["movement_id"]),
    ]

    last = release_stock_block(session, tenant, block.id, reason="passed QC")
    assert last == {"block_id": block.id, "released": "12", "open_quantity": "0"}
    assert core.blocked_quantity(session, tenant, business.item.id) == 0
    assert _active(session, business) == []
    resolved = stock_blocks(session, tenant, status="resolved")
    assert [(r["id"], r["quantity"], r["open_quantity"]) for r in resolved] == [
        (block.id, "20", "0")
    ]
    assert (
        session.scalar(
            select(func.count())
            .select_from(StockBlock)
            .where(StockBlock.tenant_id == tenant)
        )
        == 1
    )
    session.expire_all()
    assert session.get(StockBlock, (tenant, block.id)).quantity == Decimal("20.0000")
    released = _events(session, business, "stock_block.released")
    assert [(e["quantity"], e["open_quantity"]) for e in released] == [
        ("5", "15"),
        ("12", "0"),
    ]
    assert all("remainder_block_id" not in e for e in released)


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
    (resolution,) = session.scalars(
        select(StockBlockResolution).where(StockBlockResolution.block_id == block.id)
    )
    assert (resolution.kind, resolution.movement_id) == ("scrap", movement.id)
    assert session.get(StockBlock, (tenant, block.id)).receipt_movement_id is None
    (event,) = _events(session, business, "stock_block.scrapped")
    assert (event["quantity"], event["movement_id"], event["open_quantity"]) == (
        "4",
        movement.id,
        "1",
    )


def test_a_receipt_block_keeps_its_receipt_when_wholly_scrapped(session, business):
    """Spec 316 FR-005: the receipt and the scrap are two different movements."""
    tenant = business.tenant.id
    receipt = core.record_movement(
        session,
        tenant,
        "receipt",
        business.item.id,
        "5",
        to_location_id=business.location.id,
    )
    block = block_stock(
        session,
        tenant,
        business.item.id,
        business.location.id,
        "5",
        "damage",
        _movement_id=receipt.id,
        _receipt=Decimal(5),
    )

    result = scrap_stock_block(session, tenant, block.id, reason="crushed")

    row = _block(session, tenant, block.id)
    assert row["receipt_movement_id"] == receipt.id
    assert row["resolutions"][0]["movement_id"] == result["movement_id"]
    assert result["movement_id"] != receipt.id


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
    release_stock_block(session, tenant, block.id, "3", reason="ok")
    # The open quantity bounds the next resolution, not the stated one.
    with pytest.raises(core.InvalidOperation) as refused:
        scrap_stock_block(session, tenant, block.id, "3", reason="cracked")
    assert refused.value.code == "stock_block_quantity_exceeds_block"
    release_stock_block(session, tenant, block.id, reason="ok")
    with pytest.raises(core.InvalidOperation) as refused:
        scrap_stock_block(session, tenant, block.id, reason="late")
    assert refused.value.code == "stock_block_not_active"
    other = core.create_tenant(session, "Other GmbH")
    with pytest.raises(core.NotFound):
        release_stock_block(session, other.id, block.id, reason="ok")


def test_the_migration_folds_split_blocks_into_what_was_stated(
    postgres_database, monkeypatch
):
    """Spec 316 FR-008: a spec 304 chain becomes one block with its resolutions."""
    from alembic import command
    from alembic.config import Config
    from sqlalchemy import create_engine

    monkeypatch.setenv("REALITY_DATABASE_URL", postgres_database)
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", postgres_database)
    command.upgrade(config, "0108_stock_block")
    engine = create_engine(postgres_database)
    statements = [
        (
            "INSERT INTO tenant (id, name, purpose, created_at) "
            "VALUES ('ten_m316', 'Migration 316', 'business', now())"
        ),
        (
            "INSERT INTO item (id, tenant_id, sku, name, unit, is_active, item_type, "
            "tracking_type, purchase_unit, conversion_factor) VALUES ('itm_m316', "
            "'ten_m316', 'M316', 'Lamp', 'pcs', true, 'stocked', 'none', 'pcs', 1)"
        ),
        (
            "INSERT INTO location (id, tenant_id, name, type, is_active, allows_stock) "
            "VALUES ('loc_m316', 'ten_m316', 'Hamburg', 'warehouse', true, true)"
        ),
        # The receipt that stated the second block, and the scrap adjustments.
        (
            "INSERT INTO movement (id, tenant_id, type, item_id, to_location_id, "
            "quantity, occurred_at) VALUES ('mov_rcv', 'ten_m316', "
            "'receipt', 'itm_m316', 'loc_m316', 40, now())"
        ),
        (
            "INSERT INTO movement (id, tenant_id, type, item_id, from_location_id, "
            "quantity, occurred_at) VALUES ('mov_scrap1', 'ten_m316', "
            "'adjustment', 'itm_m316', 'loc_m316', 3, now())"
        ),
        (
            "INSERT INTO movement (id, tenant_id, type, item_id, from_location_id, "
            "quantity, occurred_at) VALUES ('mov_scrap2', 'ten_m316', "
            "'adjustment', 'itm_m316', 'loc_m316', 4, now())"
        ),
    ]
    columns = (
        "id, tenant_id, item_id, location_id, quantity, reason_code, note, status, "
        "created_at, created_by, resolved_at, resolved_by, resolution_reason, "
        "previous_block_id, movement_id"
    )
    rows = [
        # Block 20: release 5, then scrap 3, 12 still open.
        (
            "('blk_a', 'ten_m316', 'itm_m316', 'loc_m316', 5, 'quality', 'dented', "
            "'released', now() - interval '3 days', 'clerk', now() - interval '2 days', "
            "'qa', 'passed QC', NULL, NULL)"
        ),
        (
            "('blk_a2', 'ten_m316', 'itm_m316', 'loc_m316', 3, 'quality', 'dented', "
            "'scrapped', now() - interval '3 days', 'clerk', now() - interval '1 day', "
            "'qa', 'cracked', 'blk_a', 'mov_scrap1')"
        ),
        (
            "('blk_a3', 'ten_m316', 'itm_m316', 'loc_m316', 12, 'quality', 'dented', "
            "'active', now() - interval '3 days', 'clerk', NULL, NULL, NULL, 'blk_a2', "
            "NULL)"
        ),
        # A receipt block of 4, wholly scrapped: the scrap overwrote its receipt.
        (
            "('blk_b', 'ten_m316', 'itm_m316', 'loc_m316', 4, 'damage', '', "
            "'scrapped', now() - interval '3 days', 'clerk', now(), 'qa', 'crushed', "
            "NULL, 'mov_scrap2')"
        ),
    ]
    statements.append(f"INSERT INTO stock_block ({columns}) VALUES " + ", ".join(rows))
    statements.append(
        "INSERT INTO business_event (id, tenant_id, sequence, event_type, "
        "schema_version, subject_type, subject_id, occurred_at, recorded_at, "
        "payload) VALUES ('evt_b', 'ten_m316', 1, 'stock_block.created', 1, "
        "'stock_block', 'blk_b', now(), now(), "
        '\'{"quantity": "4", "movement_id": "mov_rcv"}\')'
    )
    try:
        with engine.begin() as connection:
            for statement in statements:
                connection.execute(text(statement))

        command.upgrade(config, "head")

        with engine.connect() as connection:
            blocks = connection.execute(
                text(
                    "SELECT id, quantity, note, created_by, receipt_movement_id "
                    "FROM stock_block ORDER BY id"
                )
            ).all()
            resolutions = connection.execute(
                text(
                    "SELECT block_id, kind, quantity, reason, resolved_by, movement_id "
                    "FROM stock_block_resolution ORDER BY block_id, resolved_at"
                )
            ).all()
        assert [(b[0], b[1], b[2], b[3], b[4]) for b in blocks] == [
            ("blk_a", Decimal("20.0000"), "dented", "clerk", None),
            ("blk_b", Decimal("4.0000"), "", "clerk", "mov_rcv"),
        ]
        assert [tuple(r) for r in resolutions] == [
            ("blk_a", "release", Decimal("5.0000"), "passed QC", "qa", None),
            ("blk_a", "scrap", Decimal("3.0000"), "cracked", "qa", "mov_scrap1"),
            ("blk_b", "scrap", Decimal("4.0000"), "crushed", "qa", "mov_scrap2"),
        ]

        # History is not discarded to make a downgrade possible.
        with pytest.raises(RuntimeError, match="stock block resolutions exist"):
            command.downgrade(config, "0108_stock_block")
    finally:
        engine.dispose()
