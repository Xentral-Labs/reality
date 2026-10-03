"""Spec 349: the time-zone table comes and goes, and a rollback keeps a stated zone."""

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import Session

from reality.services import core
from reality.services.company_time_zone import set_company_time_zone

TABLE = "company_time_zone"


def test_the_table_comes_and_goes_and_a_stated_zone_blocks_a_rollback(
    postgres_database, monkeypatch
):
    """
    BUSINESS TEST:
    A rollback never silently moves a company's business days back to UTC.
    GIVEN:
    The time-zone migration applied, first empty and then with a stated zone.
    WHEN:
    The migration is rolled back.
    THEN:
    An empty table goes and comes again; a stated zone refuses the rollback.
    BUSINESS RULES:
    company_time_zone.set.event
    """
    monkeypatch.setenv("REALITY_DATABASE_URL", postgres_database)
    config = Config("alembic.ini")
    command.upgrade(config, "0138_company_time_zone")
    engine = create_engine(postgres_database)
    try:
        assert TABLE in inspect(engine).get_table_names()
        # Positive control: an empty table rolls back and comes again.
        command.downgrade(config, "0137_supplier_item_number")
        assert TABLE not in inspect(engine).get_table_names()
        command.upgrade(config, "0138_company_time_zone")

        with Session(engine) as session:
            tenant = core.create_tenant(session, "Migration GmbH")
            set_company_time_zone(session, tenant.id, "Europe/Berlin")
        with engine.connect() as connection:
            assert (
                connection.execute(text(f"SELECT count(*) FROM {TABLE}")).scalar() == 1
            )

        with pytest.raises(RuntimeError, match=TABLE):
            command.downgrade(config, "0137_supplier_item_number")
        assert TABLE in inspect(engine).get_table_names()
    finally:
        engine.dispose()
