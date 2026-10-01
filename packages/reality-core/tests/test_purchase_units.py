"""Purchasing in a purchase unit (spec 301).

A purchase order line keeps the cartons it states; its promise, every receipt
and stock are in the item's stock unit, by the item's stated factor.
"""

from decimal import Decimal
from types import SimpleNamespace

import pytest
from sqlalchemy.exc import IntegrityError

from reality.domain.units import decline_reason, in_unit, promise_unit

CARTONS = SimpleNamespace(
    unit="pcs", purchase_unit="box", conversion_factor=Decimal(12)
)


# --- T004: the shared rule, now in the domain --------------------------------------


@pytest.mark.parametrize(
    ("quantity", "recorded", "target", "expected"),
    [
        ("5", "box", "pcs", Decimal(60)),
        ("60", "pcs", "box", Decimal(5)),
        ("7", "pcs", "pcs", Decimal(7)),
        ("61", "pcs", "box", None),
        ("1", "pallet", "pcs", None),
    ],
)
def test_the_shared_rule_converts_only_what_the_item_states(
    quantity, recorded, target, expected
):
    assert in_unit(CARTONS, Decimal(quantity), recorded, target) == expected


def test_a_refusal_says_which_statement_is_missing():
    assert decline_reason(CARTONS, "pallet", "pcs") == "no_stated_relation"
    assert decline_reason(CARTONS, "pcs", "box") == "conversion_leaves_a_remainder"
    without = SimpleNamespace(unit="pcs", purchase_unit="box", conversion_factor=0)
    assert decline_reason(without, "box", "pcs") == "no_stated_relation"


def test_a_promise_tells_whether_it_is_in_the_stock_unit():
    line = SimpleNamespace(unit="box", quantity=Decimal(5))
    # New: the promise was made in pieces from the line's cartons.
    assert promise_unit(Decimal(60), line, CARTONS) == "stock"
    # Recorded before spec 301: the promise took the line's cartons as stated.
    assert promise_unit(Decimal(5), line, CARTONS) == "line"
    # A line in the stock unit, or no line, is always the stock unit.
    stock_line = SimpleNamespace(unit="pcs", quantity=Decimal(5))
    assert promise_unit(Decimal(5), stock_line, CARTONS) == "stock"
    assert promise_unit(Decimal(5), None, CARTONS) == "stock"


# --- T004: schema ---------------------------------------------------------------------


def test_a_stated_receipt_keeps_both_values_or_neither(session, business):
    from reality.db.core import Movement, uid

    tenant = business.tenant.id

    def insert(**stated):
        with session.begin_nested():
            session.add(
                Movement(
                    id=uid("mov"),
                    tenant_id=tenant,
                    type="receipt",
                    item_id=business.item.id,
                    quantity=Decimal(60),
                    to_location_id=business.location.id,
                    **stated,
                )
            )
            session.flush()

    # Positive control: both stated values together are accepted.
    insert(stated_quantity=Decimal(5), stated_unit="box")
    with pytest.raises(IntegrityError, match="ck_movement_stated_unit"):
        insert(stated_quantity=Decimal(5))


def test_the_migration_upgrades_downgrades_and_keeps_stated_receipts(
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

    def columns():
        return {
            column["name"] for column in inspect(engine).get_columns("movement")
        } & {"stated_quantity", "stated_unit"}

    try:
        assert columns() == {"stated_quantity", "stated_unit"}
        # Positive control: with nothing stated the downgrade removes them.
        command.downgrade(config, "0105_down_payments")
        assert columns() == set()
        command.upgrade(config, "head")

        with engine.begin() as connection:
            connection.execute(
                text(
                    "INSERT INTO tenant (id, name, purpose, created_at) "
                    "VALUES ('ten_m301', 'Migration 301', 'business', now())"
                )
            )
            connection.execute(
                text(
                    "INSERT INTO item (id, tenant_id, sku, name, unit, is_active, "
                    "item_type, tracking_type, purchase_unit, conversion_factor) "
                    "VALUES ('itm_m301', 'ten_m301', 'M301', 'Box item', 'pcs', true, "
                    "'stocked', 'none', 'box', 12)"
                )
            )
            connection.execute(
                text(
                    "INSERT INTO movement (id, tenant_id, type, item_id, quantity, "
                    "occurred_at, stated_quantity, stated_unit) VALUES ('mov_m301', "
                    "'ten_m301', 'receipt', 'itm_m301', 60, now(), 5, 'box')"
                )
            )
        with pytest.raises(RuntimeError, match="stated in a purchase unit"):
            command.downgrade(config, "0105_down_payments")
        assert columns() == {"stated_quantity", "stated_unit"}
    finally:
        engine.dispose()
