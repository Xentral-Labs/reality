"""Spec 344: the statement table comes and goes, and a rollback keeps what is recorded."""

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import Session

from reality.services import core
from reality.services.external_stock import record_external_stock

TABLE = "external_stock_statement"


def test_the_table_comes_and_goes_and_recorded_rows_block_a_rollback(
    postgres_database, monkeypatch
):
    monkeypatch.setenv("REALITY_DATABASE_URL", postgres_database)
    config = Config("alembic.ini")
    command.upgrade(config, "0133_external_stock")
    engine = create_engine(postgres_database)
    try:
        assert TABLE in inspect(engine).get_table_names()
        # Positive control: an empty table rolls back and comes again.
        command.downgrade(config, "0132_receipt_deviations")
        assert TABLE not in inspect(engine).get_table_names()
        command.upgrade(config, "0133_external_stock")

        with Session(engine) as session:
            tenant = core.create_tenant(session, "Migration GmbH")
            item = reviewed_create_item(session, tenant.id, "SKU", "Item")
            location = reviewed_create_location(session, tenant.id, "3PL")
            record_external_stock(
                session,
                tenant.id,
                [{"item_id": item.id, "location_id": location.id, "quantity": "5"}],
            )
        with engine.connect() as connection:
            assert (
                connection.execute(text(f"SELECT count(*) FROM {TABLE}")).scalar() == 1
            )

        with pytest.raises(RuntimeError, match=TABLE):
            command.downgrade(config, "0132_receipt_deviations")
        assert TABLE in inspect(engine).get_table_names()
    finally:
        engine.dispose()


from intake_review_support import reviewed_create_item, reviewed_create_location
