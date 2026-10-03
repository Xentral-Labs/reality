"""Spec 345: the mapping table comes and goes, and a rollback keeps stated numbers."""

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import Session

from reality.services import core
from reality.services.supplier_item_numbers import set_supplier_item_number

TABLE = "supplier_item_number"


def test_the_table_comes_and_goes_and_stated_numbers_block_a_rollback(
    postgres_database, monkeypatch
):
    monkeypatch.setenv("REALITY_DATABASE_URL", postgres_database)
    config = Config("alembic.ini")
    command.upgrade(config, "0134_supplier_item_number")
    engine = create_engine(postgres_database)
    try:
        assert TABLE in inspect(engine).get_table_names()
        # Positive control: an empty table rolls back and comes again.
        command.downgrade(config, "0133_external_stock")
        assert TABLE not in inspect(engine).get_table_names()
        command.upgrade(config, "0134_supplier_item_number")

        with Session(engine) as session:
            tenant = core.create_tenant(session, "Migration GmbH")
            supplier = core.create_party(session, tenant.id, "Lindner", "supplier")
            item = core.create_item(session, tenant.id, "SKU", "Item")
            set_supplier_item_number(
                session, tenant.id, supplier.id, item.id, "LF-1", "Rad"
            )
        with engine.connect() as connection:
            assert (
                connection.execute(text(f"SELECT count(*) FROM {TABLE}")).scalar() == 1
            )

        with pytest.raises(RuntimeError, match="supplier item numbers"):
            command.downgrade(config, "0133_external_stock")
        assert TABLE in inspect(engine).get_table_names()
    finally:
        engine.dispose()
