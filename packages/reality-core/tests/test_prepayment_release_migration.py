"""Spec 347: the release table comes and goes, and a rollback keeps what is recorded."""

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import Session

from reality.services import core

TABLE = "prepayment_release"


def test_the_table_comes_and_goes_and_recorded_rows_block_a_rollback(
    postgres_database, monkeypatch
):
    monkeypatch.setenv("REALITY_DATABASE_URL", postgres_database)
    config = Config("alembic.ini")
    command.upgrade(config, "0136_prepayment_releases")
    engine = create_engine(postgres_database)
    try:
        assert TABLE in inspect(engine).get_table_names()
        # Positive control: an empty table rolls back and comes again.
        command.downgrade(config, "0133_external_stock")
        assert TABLE not in inspect(engine).get_table_names()
        command.upgrade(config, "0136_prepayment_releases")

        with Session(engine) as session:
            tenant = core.create_tenant(session, "Migration GmbH")
            party = core.create_party(session, tenant.id, "Kunde", "customer")
            order = core.create_document(
                session, tenant.id, "sales_order", "SO-MIG", party.id, "100.00"
            )
            session.execute(
                text(
                    f"INSERT INTO {TABLE} (id, tenant_id, document_id, covered_amount,"
                    " currency, reason, created_at) VALUES ('ppr_1', :tenant,"
                    " :order, 100, 'EUR', 'Trusted customer', now())"
                ),
                {"tenant": tenant.id, "order": order.id},
            )
            session.commit()
        with pytest.raises(RuntimeError, match="cannot be removed"):
            command.downgrade(config, "0133_external_stock")
        assert TABLE in inspect(engine).get_table_names()
    finally:
        engine.dispose()
