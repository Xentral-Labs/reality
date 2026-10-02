"""Exact default mapping and finance authority survive consolidation and rollback."""

from hashlib import sha256

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text

from reality.db.core import SourceRecord


@pytest.fixture
def legacy_defaults(postgres_database, monkeypatch):
    monkeypatch.setenv("REALITY_DATABASE_URL", postgres_database)
    config = Config("alembic.ini")
    command.upgrade(config, "0117_cost_projections")
    engine = create_engine(postgres_database)
    try:
        with engine.begin() as connection:
            for tenant in ("a", "b"):
                connection.execute(
                    text(
                        "INSERT INTO tenant (id,name,purpose,created_at) VALUES (:t,:t,'business',now())"
                    ),
                    {"t": tenant},
                )
                connection.execute(
                    text(
                        "INSERT INTO subledger_account (tenant_id,id,code,name,role,state,revision) VALUES (:t,'account','cash','Cash','cash','blocked',7),(:t,'sales','sales','Sales','sales_revenue','active',2)"
                    ),
                    {"t": tenant},
                )
                connection.execute(
                    text(
                        "INSERT INTO finance_role_destination (tenant_id,id,role,account_id) VALUES (:t,'same-destination','cash','account')"
                    ),
                    {"t": tenant},
                )
                connection.execute(
                    text(
                        "INSERT INTO finance_state (tenant_id,id,revision) VALUES (:t,'finance',8)"
                    ),
                    {"t": tenant},
                )
                connection.execute(
                    SourceRecord.__table__.insert().values(
                        id="source",
                        tenant_id=tenant,
                        source_system="test",
                        source_type="statement",
                        external_id="1",
                        payload='{"amount":"10.2500"}',
                        payload_hash=sha256(b'{"amount":"10.2500"}').hexdigest(),
                        version=1,
                    )
                )
                connection.execute(
                    text(
                        "INSERT INTO ledger_entry (tenant_id,id,posting_group_id,account_id,amount,currency,debit_credit,effective_at,source_record_id) VALUES (:t,'debit','group','account',10.2500,'EUR','debit',now(),'source'),(:t,'credit','group','account',10.2500,'EUR','credit',now(),'source')"
                    ),
                    {"t": tenant},
                )
        yield engine, config
    finally:
        engine.dispose()


def _records(connection, columns):
    return {
        name: list(
            connection.execute(
                text(f"SELECT {','.join(fields)} FROM {name} ORDER BY tenant_id,id")
            ).tuples()
        )
        for name, fields in columns.items()
    }


def test_populated_defaults_roundtrip_exact_ids_accounts_authority_and_schema(
    legacy_defaults,
):
    from test_cost_projection_migration import _schema_snapshot

    engine, config = legacy_defaults
    with engine.connect() as connection:
        inspector = inspect(connection)
        physical = set(inspector.get_table_names())
        columns = {
            name: tuple(c["name"] for c in inspector.get_columns(name))
            for name in (
                "subledger_account",
                "finance_role_destination",
                "finance_state",
                "source_record",
                "ledger_entry",
                "business_event",
            )
        }
        before = _records(connection, columns)
        schema = _schema_snapshot(
            connection, ("subledger_account", "finance_role_destination")
        )
    command.upgrade(config, "0118_account_defaults")
    with engine.connect() as connection:
        assert _records(connection, columns) == before
        assert set(inspect(connection).get_table_names()) == physical - {
            "finance_role_destination"
        }
        assert "finance_role_destination" in inspect(connection).get_view_names()
    # Rollback must also preserve legitimate new choices made after upgrade.
    from sqlalchemy.orm import Session

    from reality.services.finance import accounts

    with Session(engine) as session:
        new = accounts.create_account(
            session, "a", code="cash-new", name="New cash", role="cash"
        )
        accounts.set_default_account(session, "a", role="cash", account_id=new["id"])
    with engine.connect() as connection:
        after_change = _records(connection, columns)
        for name in ("source_record", "ledger_entry"):
            assert after_change[name] == before[name]
        assert (
            connection.scalar(
                text(
                    "SELECT default_destination_id FROM subledger_account WHERE tenant_id='a' AND id=:id"
                ),
                {"id": new["id"]},
            )
            == "same-destination"
        )
    command.downgrade(config, "0117_cost_projections")
    with engine.connect() as connection:
        assert _records(connection, columns) == after_change
        assert (
            _schema_snapshot(
                connection, ("subledger_account", "finance_role_destination")
            )
            == schema
        )
        assert set(inspect(connection).get_table_names()) == physical
    command.upgrade(config, "0118_account_defaults")
    with engine.connect() as connection:
        assert _records(connection, columns) == after_change


def test_incompatible_legacy_role_aborts_without_schema_or_data_loss(legacy_defaults):
    engine, config = legacy_defaults
    with engine.begin() as connection:
        connection.execute(
            text(
                "UPDATE finance_role_destination SET role='sales_revenue' WHERE tenant_id='a'"
            )
        )
    with pytest.raises(RuntimeError, match="role"):
        command.upgrade(config, "0118_account_defaults")
    with engine.connect() as connection:
        assert "finance_role_destination" in inspect(connection).get_table_names()
        assert "default_destination_id" not in {
            c["name"] for c in inspect(connection).get_columns("subledger_account")
        }
        assert (
            connection.scalar(
                text("SELECT role FROM finance_role_destination WHERE tenant_id='a'")
            )
            == "sales_revenue"
        )
        assert connection.scalar(text("SELECT count(*) FROM ledger_entry")) == 4
        assert (
            connection.scalar(text("SELECT version_num FROM alembic_version"))
            == "0117_cost_projections"
        )
