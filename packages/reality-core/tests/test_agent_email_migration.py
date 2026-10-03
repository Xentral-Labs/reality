"""Spec 351: exact dispatch authorization survives migrations and rollback guards."""

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import Session

from reality.services.core import create_tenant
from reality.tools.application import (
    approve_and_execute_proposal,
    create_change_proposal,
)


def test_dispatch_migration_round_trip_and_populated_guard(
    postgres_database, monkeypatch
):
    monkeypatch.setenv("REALITY_DATABASE_URL", postgres_database)
    config = Config("alembic.ini")
    command.upgrade(config, "0134_agent_email_handoffs")
    engine = create_engine(postgres_database)
    try:
        assert "email_dispatch" in inspect(engine).get_table_names()
        command.downgrade(config, "0133_external_stock")
        assert "email_dispatch" not in inspect(engine).get_table_names()
        command.upgrade(config, "0134_agent_email_handoffs")
        with Session(engine) as db:
            tenant = create_tenant(db, "Email migration")
            p = create_change_proposal(
                db,
                tenant.id,
                "email_dispatch_authorize",
                {
                    "message": {
                        "account": "support@example.test",
                        "sender": "support@example.test",
                        "to": ["customer@example.test"],
                        "subject": "Reply",
                        "text": "Hello",
                    },
                    "rationale": "Answer",
                    "supporting_source_ids": [],
                },
            )
            approve_and_execute_proposal(db, tenant.id, p.id, confirmed=True)
        with pytest.raises(RuntimeError, match="dispatch"):
            command.downgrade(config, "0133_external_stock")
        assert "email_dispatch" in inspect(engine).get_table_names()
    finally:
        engine.dispose()
