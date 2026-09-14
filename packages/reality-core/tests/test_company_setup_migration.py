from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect


def test_company_setup_schema_roundtrip(postgres_database, monkeypatch):
    from reality.db.company_setup import OrdinaryCompanyCreation
    from reality.db.demo_data import DemoDataConnection

    assert OrdinaryCompanyCreation.__tablename__ == "ordinary_company_creation"
    assert DemoDataConnection.__tablename__ == "demo_data_connection"
    monkeypatch.setenv("REALITY_DATABASE_URL", postgres_database)
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", postgres_database)
    command.upgrade(config, "head")
    engine = create_engine(postgres_database)
    try:
        assert {"ordinary_company_creation", "demo_data_connection"} <= set(
            inspect(engine).get_table_names()
        )
        command.downgrade(config, "0045_scheduled_jobs")
        assert "demo_data_connection" not in inspect(engine).get_table_names()
        command.upgrade(config, "head")
    finally:
        engine.dispose()


def test_receipt_uniqueness_and_demo_source_scope(session, business, scheduled_owner):
    import pytest
    from sqlalchemy.exc import IntegrityError

    from reality.db.company_setup import OrdinaryCompanyCreation
    from reality.db.core import uid
    from reality.db.demo_data import DemoDataConnection
    from reality.services import core

    other = core.create_tenant(session, "Other company")
    source = core.create_source_system(
        session, business.tenant.id, "test-demo", "Test Demo"
    )
    session.add(
        OrdinaryCompanyCreation(
            id=uid("receipt"),
            tenant_id=business.tenant.id,
            actor_id=scheduled_owner.id,
            request_key="unique",
            request_fingerprint="a" * 64,
        )
    )
    session.flush()
    with pytest.raises(IntegrityError), session.begin_nested():
        session.add(
            OrdinaryCompanyCreation(
                id=uid("receipt"),
                tenant_id=other.id,
                actor_id=scheduled_owner.id,
                request_key="unique",
                request_fingerprint="b" * 64,
            )
        )
        session.flush()
    with pytest.raises(IntegrityError), session.begin_nested():
        session.add(
            DemoDataConnection(
                id=uid("demo"),
                tenant_id=other.id,
                source_system_id=source.id,
                state="stopped",
            )
        )
        session.flush()
    session.add(
        DemoDataConnection(
            id=uid("demo"),
            tenant_id=business.tenant.id,
            source_system_id=source.id,
            state="stopped",
        )
    )
    session.flush()


def test_demo_connection_refuses_foreign_schedule(session, business, scheduled_owner):
    import pytest
    from sqlalchemy.exc import IntegrityError

    from reality.db.core import uid
    from reality.db.demo_data import DemoDataConnection
    from reality.services import core, scheduled_jobs

    other = core.create_tenant(session, "Foreign schedule company")
    source = core.create_source_system(session, other.id, "demo_data", "Demo Data")
    schedule = scheduled_jobs.create_schedule(
        session,
        business.tenant.id,
        scheduled_owner.id,
        "invitations.cleanup",
        {},
        request_id="foreign-schedule-fk",
        interval_seconds=60,
    )
    with pytest.raises(IntegrityError), session.begin_nested():
        session.add(
            DemoDataConnection(
                id=uid("demo"),
                tenant_id=other.id,
                source_system_id=source.id,
                current_schedule_id=schedule.id,
                state="stopped",
            )
        )
        session.flush()
