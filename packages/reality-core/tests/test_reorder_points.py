"""Reorder points per item and location (spec 302 FR-001)."""

import json
from decimal import Decimal

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from reality.db.core import BusinessEvent, ItemReorderPoint, uid
from reality.services import core
from reality.services.reorder_points import (
    remove_reorder_point,
    reorder_points,
    set_reorder_point,
)


def _events(session, tenant_id, event_type):
    return [
        json.loads(event.payload)
        for event in session.scalars(
            select(BusinessEvent)
            .where(
                BusinessEvent.tenant_id == tenant_id,
                BusinessEvent.event_type == event_type,
            )
            .order_by(BusinessEvent.sequence)
        )
    ]


# --- schema ---------------------------------------------------------------------------


def test_one_point_per_item_and_location_with_values_in_range(session, business):
    tenant = business.tenant.id

    def insert(point="20", quantity="48", location=None):
        with session.begin_nested():
            session.add(
                ItemReorderPoint(
                    id=uid("rop"),
                    tenant_id=tenant,
                    item_id=business.item.id,
                    location_id=location or business.location.id,
                    reorder_point=Decimal(point),
                    reorder_quantity=Decimal(quantity),
                )
            )
            session.flush()

    # Positive control: a point of zero with a positive quantity is accepted.
    insert(point="0")
    with pytest.raises(IntegrityError, match="uq_item_reorder_point_item_location"):
        insert()
    other = core.create_location(session, tenant, "Second store")
    with pytest.raises(IntegrityError, match="ck_item_reorder_point_values"):
        insert(quantity="0", location=other.id)
    with pytest.raises(IntegrityError, match="ck_item_reorder_point_values"):
        insert(point="-1", location=other.id)


def test_the_migration_upgrades_downgrades_and_keeps_stated_points(
    postgres_database, monkeypatch
):
    from alembic import command
    from alembic.config import Config
    from sqlalchemy import create_engine, inspect, text

    monkeypatch.setenv("REALITY_DATABASE_URL", postgres_database)
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", postgres_database)
    command.upgrade(config, "head")
    engine = create_engine(postgres_database)

    def present():
        return "item_reorder_point" in inspect(engine).get_table_names()

    try:
        assert present()
        # Positive control: with nothing stated the downgrade removes the table.
        command.downgrade(config, "0106_movement_stated_unit")
        assert not present()
        command.upgrade(config, "head")

        with engine.begin() as connection:
            connection.execute(
                text(
                    "INSERT INTO tenant (id, name, purpose, created_at) "
                    "VALUES ('ten_m302', 'Migration 302', 'business', now())"
                )
            )
            connection.execute(
                text(
                    "INSERT INTO item (id, tenant_id, sku, name, unit, is_active, "
                    "item_type, tracking_type, purchase_unit, conversion_factor) "
                    "VALUES ('itm_m302', 'ten_m302', 'M302', 'Screw', 'pcs', true, "
                    "'stocked', 'none', 'pcs', 1)"
                )
            )
            connection.execute(
                text(
                    "INSERT INTO location (id, tenant_id, name, type, is_active, "
                    "allows_stock) VALUES ('loc_m302', 'ten_m302', 'Hamburg', "
                    "'warehouse', true, true)"
                )
            )
            connection.execute(
                text(
                    "INSERT INTO item_reorder_point (id, tenant_id, item_id, "
                    "location_id, reorder_point, reorder_quantity, created_at, "
                    "updated_at) VALUES ('rop_m302', 'ten_m302', 'itm_m302', "
                    "'loc_m302', 20, 48, now(), now())"
                )
            )
        with pytest.raises(RuntimeError, match="reorder points are stated"):
            command.downgrade(config, "0106_movement_stated_unit")
        assert present()
    finally:
        engine.dispose()


# --- services -------------------------------------------------------------------------


def test_a_point_is_set_changed_and_removed_with_its_history(session, business):
    tenant = business.tenant.id

    point = set_reorder_point(
        session, tenant, business.item.id, business.location.id, "20", "48"
    )
    assert (point.reorder_point, point.reorder_quantity) == (
        Decimal("20.0000"),
        Decimal("48.0000"),
    )
    changed = set_reorder_point(
        session, tenant, business.item.id, business.location.id, "30", "60"
    )
    # Restating changes the one point, it does not add a second.
    assert changed.id == point.id
    (row,) = reorder_points(session, tenant, item_id=business.item.id)
    assert (row["reorder_point"], row["reorder_quantity"], row["location_id"]) == (
        "30",
        "60",
        business.location.id,
    )

    removed = remove_reorder_point(
        session, tenant, business.item.id, business.location.id
    )
    assert removed["reorder_point"] == "30"
    assert reorder_points(session, tenant) == []

    set_events = _events(session, tenant, "reorder_point.set")
    assert [event["reorder_point"] for event in set_events] == ["20", "30"]
    assert "previous" not in set_events[0]
    assert set_events[1]["previous"] == {
        "reorder_point": "20",
        "reorder_quantity": "48",
    }
    (gone,) = _events(session, tenant, "reorder_point.removed")
    assert (gone["item_id"], gone["reorder_point"], gone["reorder_quantity"]) == (
        business.item.id,
        "30",
        "60",
    )


def test_only_a_stocked_active_item_at_a_stock_location_takes_a_point(
    session, business
):
    tenant = business.tenant.id
    service = core.create_item(
        session, tenant, "SRV-302", "Assembly", item_type="service"
    )
    virtual = core.create_location(session, tenant, "In transit")
    virtual.allows_stock = False
    session.commit()

    def refused(item_id, location_id, point="20", quantity="48"):
        with pytest.raises(core.InvalidOperation) as error:
            set_reorder_point(session, tenant, item_id, location_id, point, quantity)
        return error.value.code

    assert refused(service.id, business.location.id) == "reorder_point_item_not_stocked"
    assert refused(business.item.id, virtual.id) == "reorder_point_location_not_stock"
    assert refused(business.item.id, business.location.id, quantity="0") == (
        "reorder_point_values_invalid"
    )
    assert refused(business.item.id, business.location.id, point="-1") == (
        "reorder_point_values_invalid"
    )
    assert refused(business.item.id, business.location.id, point="many") == (
        "reorder_point_values_invalid"
    )
    business.item.is_active = False
    session.commit()
    assert refused(business.item.id, business.location.id) == (
        "reorder_point_item_not_stocked"
    )
    assert reorder_points(session, tenant) == []


def test_a_change_since_the_review_is_refused(session, business):
    tenant = business.tenant.id
    item, location = business.item.id, business.location.id

    # The review saw no point; another person set one meanwhile.
    set_reorder_point(session, tenant, item, location, "20", "48")
    with pytest.raises(core.InvalidOperation) as error:
        set_reorder_point(session, tenant, item, location, "25", "48", _expected=None)
    assert error.value.code == "reorder_point_changed_since_review"

    # Positive control: the values the review saw are accepted.
    seen = {"reorder_point": "20", "reorder_quantity": "48"}
    set_reorder_point(session, tenant, item, location, "25", "48", _expected=seen)
    with pytest.raises(core.InvalidOperation) as error:
        remove_reorder_point(session, tenant, item, location, _expected=seen)
    assert error.value.code == "reorder_point_changed_since_review"
    remove_reorder_point(
        session,
        tenant,
        item,
        location,
        _expected={"reorder_point": "25", "reorder_quantity": "48"},
    )

    with pytest.raises(core.NotFound) as error:
        remove_reorder_point(session, tenant, item, location)
    assert error.value.code == "reorder_point_not_found"


def test_another_company_sees_and_changes_nothing(session, business):
    tenant = business.tenant.id
    set_reorder_point(
        session, tenant, business.item.id, business.location.id, "20", "48"
    )
    other = core.create_tenant(session, "Other GmbH")

    assert reorder_points(session, other.id) == []
    with pytest.raises(core.NotFound):
        set_reorder_point(
            session, other.id, business.item.id, business.location.id, "1", "1"
        )
    with pytest.raises(core.NotFound):
        remove_reorder_point(session, other.id, business.item.id, business.location.id)
    assert len(reorder_points(session, tenant)) == 1


def test_a_value_the_column_would_round_or_cannot_hold_is_refused(session, business):
    tenant = business.tenant.id
    for point, quantity in (("1.23456", "48"), ("20", "0.00001"), ("1e15", "48")):
        with pytest.raises(core.InvalidOperation) as error:
            set_reorder_point(
                session, tenant, business.item.id, business.location.id, point, quantity
            )
        assert error.value.code == "reorder_point_values_invalid"
    # Positive control: four places are kept exactly as stated.
    point = set_reorder_point(
        session, tenant, business.item.id, business.location.id, "1.2345", "48"
    )
    assert point.reorder_point == Decimal("1.2345")
