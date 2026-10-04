"""Spec 351: exact dispatch authorization survives migrations and rollback guards."""

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import Session

from reality.services.core import create_party, create_tenant
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
        command.downgrade(config, "0138_company_time_zone")
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
                    "business_references": [
                        {
                            "kind": "party",
                            "id": create_party(
                                db, tenant.id, "Supplier", "supplier"
                            ).id,
                        }
                    ],
                    "rationale": "Answer",
                    "supporting_source_ids": [],
                },
            )
            approve_and_execute_proposal(db, tenant.id, p.id, confirmed=True)
        with pytest.raises(RuntimeError, match="dispatch"):
            command.downgrade(config, "0138_company_time_zone")
        assert "email_dispatch" in inspect(engine).get_table_names()
    finally:
        engine.dispose()


def test_business_link_migration_preserves_legacy_and_refuses_populated_downgrade(
    postgres_database, monkeypatch
):
    from reality.services.core import enqueue_source
    from reality.services.emails import capture_email, email_history

    monkeypatch.setenv("REALITY_DATABASE_URL", postgres_database)
    config = Config("alembic.ini")
    command.upgrade(config, "0134_agent_email_handoffs")
    engine = create_engine(postgres_database)
    try:
        with Session(engine) as db:
            tenant = create_tenant(db, "Historical mail")
            party = create_party(db, tenant.id, "Supplier", "supplier")
            legacy, _ = enqueue_source(
                db,
                tenant.id,
                "agent",
                "email_message",
                "legacy",
                {"message": {"subject": "Legacy"}, "direction": "inbound"},
            )
            tenant_id, party_id, source_id = tenant.id, party.id, legacy.id
        command.upgrade(config, "0139_email_business_links")
        assert "email_business_link" in inspect(engine).get_table_names()
        with Session(engine) as db:
            assert (
                email_history(db, tenant_id, {"source_id": source_id})[
                    "context_missing"
                ]
                is True
            )
        command.downgrade(config, "0134_agent_email_handoffs")
        command.upgrade(config, "0139_email_business_links")
        with Session(engine) as db:
            capture_email(
                db,
                tenant_id,
                {
                    "origin": "agent",
                    "retry_key": "linked",
                    "direction": "inbound",
                    "business_references": [{"kind": "party", "id": party_id}],
                    "message": {
                        "account": "a@test",
                        "sender": "b@test",
                        "to": ["a@test"],
                        "subject": "Linked",
                    },
                },
            )
        with pytest.raises(RuntimeError, match="business links"):
            command.downgrade(config, "0134_agent_email_handoffs")
        assert "email_business_link" in inspect(engine).get_table_names()
    finally:
        engine.dispose()
