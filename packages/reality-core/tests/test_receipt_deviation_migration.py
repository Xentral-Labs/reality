"""Spec 338: the three deviation tables come and go, and a rollback keeps what is recorded."""

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import Session

from reality.services import core

TABLES = {"misdelivery", "commitment_substitute", "shipment_advice_line"}


def test_the_tables_come_and_go_and_recorded_rows_block_a_rollback(
    postgres_database, monkeypatch
):
    monkeypatch.setenv("REALITY_DATABASE_URL", postgres_database)
    config = Config("alembic.ini")
    command.upgrade(config, "0132_receipt_deviations")
    engine = create_engine(postgres_database)
    try:
        assert TABLES <= set(inspect(engine).get_table_names())
        # Positive control: empty tables roll back and come again.
        command.downgrade(config, "0131_party_merges")
        assert not TABLES & set(inspect(engine).get_table_names())
        # Current application services require the current readiness schema. The
        # populated rollback still traverses and checks the original migration.
        command.upgrade(config, "head")

        with Session(engine) as session:
            tenant = core.create_tenant(session, "Migration GmbH")
            supplier = core.create_party(session, tenant.id, "Supplier", "supplier")
            company = core.create_party(session, tenant.id, "Migration GmbH", "company")
            item = core.create_item(session, tenant.id, "SKU", "Item")
            location = core.create_location(session, tenant.id, "Warehouse")
            promise = core.create_commitment(
                session,
                tenant.id,
                "supplier_delivery",
                supplier.id,
                company.id,
                item.id,
                location.id,
                "10",
                None,
            )
            from reality.services.shipments import record_shipment_notice

            record_shipment_notice(
                session,
                tenant.id,
                direction="inbound",
                purpose="supplier_delivery",
                counterparty_id=supplier.id,
                advised=[{"commitment_id": promise.id, "quantity": "10"}],
            )
        with engine.connect() as connection:
            assert (
                connection.execute(
                    text("SELECT count(*) FROM shipment_advice_line")
                ).scalar()
                == 1
            )

        with pytest.raises(RuntimeError, match="shipment_advice_line"):
            command.downgrade(config, "0131_party_merges")
        assert TABLES <= set(inspect(engine).get_table_names())
    finally:
        engine.dispose()
