"""Spec 353 FR-008a: unknown source totals survive without synthetic replacements."""

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import Session

from reality.services import core


def test_nullable_total_upgrade_preserves_values_and_refuses_lossy_downgrade(
    postgres_database, monkeypatch
):
    monkeypatch.setenv("REALITY_DATABASE_URL", postgres_database)
    config = Config("alembic.ini")
    command.upgrade(config, "0139_unstated_source_amounts")
    engine = create_engine(postgres_database)
    try:
        with Session(engine) as session:
            tenant = core.create_tenant(session, "Received values migration")
            party = core.create_party(
                session, tenant.id, "Received customer", "customer"
            )
            document = core.create_document(
                session, tenant.id, "sales_order", "RECEIVED", party.id, "99.1234"
            )
            document_id = document.id
        command.upgrade(config, "0140_unstated_document_totals")
        with engine.connect() as connection:
            assert connection.execute(
                text("SELECT gross_amount FROM document WHERE id = :id"),
                {"id": document_id},
            ).scalar() == core.decimal("99.1234")
        assert next(
            c
            for c in inspect(engine).get_columns("document")
            if c["name"] == "gross_amount"
        )["nullable"]
        command.downgrade(config, "0139_unstated_source_amounts")
        command.upgrade(config, "0140_unstated_document_totals")
        with engine.begin() as connection:
            connection.execute(
                text("UPDATE document SET gross_amount = NULL WHERE id = :id"),
                {"id": document_id},
            )
        with pytest.raises(RuntimeError, match="never invent"):
            command.downgrade(config, "0139_unstated_source_amounts")
        with engine.connect() as connection:
            assert (
                connection.execute(
                    text("SELECT gross_amount FROM document WHERE id = :id"),
                    {"id": document_id},
                ).scalar()
                is None
            )
    finally:
        engine.dispose()
