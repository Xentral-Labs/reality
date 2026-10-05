"""Additive schema round trip and retained responsibility-history rollback guard."""

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import Session

from reality.db.core import AppUser, TenantMembership, now, uid
from reality.services import core
from reality.services import operational_cases as cases
from reality.services.memberships import Principal


def test_schema_roundtrip_and_populated_downgrade_guard(postgres_database, monkeypatch):
    monkeypatch.setenv("REALITY_DATABASE_URL", postgres_database)
    config = Config("alembic.ini")
    command.upgrade(config, "0144_operational_cases")
    engine = create_engine(postgres_database)
    try:
        assert "case_proposal_link" in inspect(engine).get_table_names()
        command.downgrade(config, "0143_intake_review_mandates")
        assert "operational_case" not in inspect(engine).get_table_names()
        command.upgrade(config, "0144_operational_cases")
        with Session(engine) as session:
            tenant = core.create_tenant(session, "Adoption migration")
            owner = AppUser(
                id=uid("usr"),
                email=f"{uid('mail')}@example.test",
                password_hash="unused",
                status="active",
                email_verified_at=now(),
            )
            session.add(owner)
            session.flush()
            session.add(
                TenantMembership(
                    id=uid("tmb"),
                    tenant_id=tenant.id,
                    user_id=owner.id,
                    role="owner",
                    status="active",
                )
            )
            session.commit()
            cases.adopt(
                session,
                tenant.id,
                Principal(owner.id),
                confirmed=True,
                request_key="adopt-migration",
            )
        with pytest.raises(RuntimeError, match="control history"):
            command.downgrade(config, "0143_intake_review_mandates")
        with engine.connect() as connection:
            assert connection.scalar(text("SELECT count(*) FROM case_adoption")) == 1
            assert (
                connection.scalar(text("SELECT version_num FROM alembic_version"))
                == "0144_operational_cases"
            )
    finally:
        engine.dispose()
