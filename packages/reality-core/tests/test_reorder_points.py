"""Reorder points per item and location (spec 302 FR-001; spec 320 evidence)."""

import json
from decimal import Decimal

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from reality.db.core import BusinessEvent, ItemReorderPoint, SourceRecord, uid
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
    source, _, _ = core.store_source_record(
        session, tenant, "internal_reorder_point", "reorder_point", "schema", {}
    )

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
                    source_record_id=source.id,
                )
            )
            session.flush()

    # Positive control: a point of zero with a positive quantity is accepted.
    insert(point="0")
    with pytest.raises(IntegrityError, match="uq_item_reorder_point_item_location"):
        insert()
    other = reviewed_create_location(session, tenant, "Second store")
    with pytest.raises(IntegrityError, match="ck_item_reorder_point_values"):
        insert(quantity="0", location=other.id)
    with pytest.raises(IntegrityError, match="ck_item_reorder_point_values"):
        insert(point="-1", location=other.id)
    # Spec 320: a point without the statement it came from is refused.
    with (
        pytest.raises(IntegrityError, match="source_record_id"),
        session.begin_nested(),
    ):
        session.add(
            ItemReorderPoint(
                id=uid("rop"),
                tenant_id=tenant,
                item_id=business.item.id,
                location_id=other.id,
                reorder_point=Decimal(1),
                reorder_quantity=Decimal(1),
            )
        )
        session.flush()


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
                    "INSERT INTO source_record (id, tenant_id, source_system, "
                    "source_type, external_id, payload, payload_hash, version, "
                    "received_at) VALUES ('src_m302', 'ten_m302', "
                    "'internal_reorder_point', 'reorder_point', 'itm_m302@loc_m302', "
                    "'{}', 'x', 1, now())"
                )
            )
            connection.execute(
                text(
                    "INSERT INTO item_reorder_point (id, tenant_id, item_id, "
                    "location_id, reorder_point, reorder_quantity, created_at, "
                    "updated_at, source_record_id) VALUES ('rop_m302', 'ten_m302', "
                    "'itm_m302', 'loc_m302', 20, 48, now(), now(), 'src_m302')"
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
    service = reviewed_create_item(
        session, tenant, "SRV-302", "Assembly", item_type="service"
    )
    virtual = reviewed_create_location(session, tenant, "In transit")
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


# --- spec 320: every point names the statement it came from ----------------------------


def _statements(session, tenant, item_id, location_id):
    session.expire_all()
    return [
        (row.version, json.loads(row.payload), row.supersedes_source_record_id, row.id)
        for row in session.scalars(
            select(SourceRecord)
            .where(
                SourceRecord.tenant_id == tenant,
                SourceRecord.source_system == "internal_reorder_point",
                SourceRecord.external_id == f"{item_id}@{location_id}",
            )
            .order_by(SourceRecord.version)
        )
    ]


def test_each_statement_is_kept_and_the_point_names_the_one_in_force(session, business):
    tenant = business.tenant.id
    item, location = business.item.id, business.location.id

    first = set_reorder_point(session, tenant, item, location, "20", "48")
    set_reorder_point(session, tenant, item, location, "30", "60")
    (row,) = reorder_points(session, tenant)
    removed = remove_reorder_point(session, tenant, item, location)
    again = set_reorder_point(session, tenant, item, location, "20", "48")

    history = _statements(session, tenant, item, location)
    assert [
        (version, payload.get("reorder_point"), payload.get("removed", False))
        for version, payload, _, _ in history
    ] == [(1, "20", False), (2, "30", False), (3, None, True), (4, "20", False)]
    # Each statement supersedes the one before it, so the stream is the history.
    assert [supersedes for _, _, supersedes, _ in history] == [
        None,
        history[0][3],
        history[1][3],
        history[2][3],
    ]
    assert row["source_record_id"] == history[1][3]
    assert first.id != again.id
    assert again.source_record_id == history[3][3]
    assert removed["source_record_id"] == history[2][3]
    (gone,) = session.scalars(
        select(BusinessEvent).where(
            BusinessEvent.tenant_id == tenant,
            BusinessEvent.event_type == "reorder_point.removed",
        )
    )
    assert gone.source_record_id == history[2][3]


def test_a_replayed_confirmation_states_nothing_twice(session, business):
    from reality.tools.application import (
        approve_and_execute_proposal,
        create_change_proposal,
    )

    tenant = business.tenant.id
    item, location = business.item.id, business.location.id
    proposal = create_change_proposal(
        session,
        tenant,
        "reorder_point_set",
        {
            "item_id": item,
            "location_id": location,
            "reorder_point": "20",
            "reorder_quantity": "48",
        },
    )
    approve_and_execute_proposal(session, tenant, proposal.id, confirmed=True)
    point = reorder_points(session, tenant)[0]

    set_reorder_point(
        session, tenant, item, location, "20", "48", action_id=proposal.id
    )

    ((version, payload, _, source_id),) = _statements(session, tenant, item, location)
    assert (version, payload["statement_id"], point["source_record_id"]) == (
        1,
        proposal.id,
        source_id,
    )


def test_the_migration_gives_every_stated_point_its_evidence(
    postgres_database, monkeypatch
):
    """Spec 320 FR-003: a point stated before 0111 gets a source record marked as such."""
    from alembic import command
    from alembic.config import Config
    from sqlalchemy import create_engine, text

    monkeypatch.setenv("REALITY_DATABASE_URL", postgres_database)
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", postgres_database)
    command.upgrade(config, "0110_payment_return_links")
    engine = create_engine(postgres_database)
    try:
        with engine.begin() as connection:
            for statement in (
                (
                    "INSERT INTO tenant (id, name, purpose, created_at) "
                    "VALUES ('ten_m320', 'Migration 320', 'business', now())"
                ),
                (
                    "INSERT INTO item (id, tenant_id, sku, name, unit, is_active, "
                    "item_type, tracking_type, purchase_unit, conversion_factor) "
                    "VALUES ('itm_m320', 'ten_m320', 'M320', 'Screw', 'pcs', true, "
                    "'stocked', 'none', 'pcs', 1)"
                ),
                (
                    "INSERT INTO location (id, tenant_id, name, type, is_active, "
                    "allows_stock) VALUES ('loc_m320', 'ten_m320', 'Hamburg', "
                    "'warehouse', true, true)"
                ),
                (
                    "INSERT INTO item_reorder_point (id, tenant_id, item_id, location_id, "
                    "reorder_point, reorder_quantity, created_at, updated_at) VALUES "
                    "('rop_m320', 'ten_m320', 'itm_m320', 'loc_m320', 20, 48, now(), now())"
                ),
            ):
                connection.execute(text(statement))

        command.upgrade(config, "head")

        with engine.connect() as connection:
            source_id, payload, external_id, stream_current = connection.execute(
                text(
                    "SELECT s.id, s.payload, s.external_id, t.current_source_record_id "
                    "FROM item_reorder_point p JOIN source_record s "
                    "ON s.tenant_id = p.tenant_id AND s.id = p.source_record_id "
                    "JOIN source_stream t ON t.tenant_id = s.tenant_id "
                    "AND t.source_system = s.source_system "
                    "AND t.source_type = s.source_type "
                    "AND t.external_id = s.external_id WHERE p.id = 'rop_m320'"
                )
            ).one()
        stated = json.loads(payload)
        assert external_id == "itm_m320@loc_m320"
        assert stream_current == source_id
        assert (stated["reorder_point"], stated["reorder_quantity"]) == ("20", "48")
        assert stated["statement_id"] == "recorded before spec 320"

        command.downgrade(config, "0110_payment_return_links")
        command.upgrade(config, "head")
    finally:
        engine.dispose()


from intake_review_support import reviewed_create_item, reviewed_create_location
