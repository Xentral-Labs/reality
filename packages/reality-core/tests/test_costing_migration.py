"""Receipt-cost authority has tenant-safe references and a non-destructive downgrade."""

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text


def test_receipt_costing_upgrade_and_empty_downgrade(postgres_database, monkeypatch):
    monkeypatch.setenv("REALITY_DATABASE_URL", postgres_database)
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", postgres_database)
    command.upgrade(config, "0071_receipt_costing")
    engine = create_engine(postgres_database)
    try:
        names = set(inspect(engine).get_table_names())
        assert {
            "cost_receipt_basis",
            "cost_attribution_revision",
            "cost_attribution_part",
            "cost_scope_review",
            "cost_input_manifest",
            "cost_manifest_attribution",
        } <= names
        constraints = inspect(engine).get_foreign_keys("cost_attribution_part")
        assert any(
            c["constrained_columns"] == ["tenant_id", "receipt_basis_id"]
            for c in constraints
        )
        from reality.db.core import Base

        for name in names:
            if not name.startswith("cost_"):
                continue
            expected = {
                tuple(c.column_keys)
                for c in Base.metadata.tables[name].foreign_key_constraints
                if all(element.column.table.name in names for element in c.elements)
            }
            actual = {
                tuple(c["constrained_columns"])
                for c in inspect(engine).get_foreign_keys(name)
            }
            assert expected == actual, name
        command.downgrade(config, "0070_projection_clock_due")
        assert "cost_receipt_basis" not in inspect(engine).get_table_names()
    finally:
        engine.dispose()


def test_populated_costing_downgrade_refuses_without_deleting(
    postgres_database, monkeypatch
):
    monkeypatch.setenv("REALITY_DATABASE_URL", postgres_database)
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", postgres_database)
    command.upgrade(config, "0071_receipt_costing")
    engine = create_engine(postgres_database)
    try:
        with engine.begin() as c:
            c.execute(
                text(
                    "INSERT INTO tenant(id,name,purpose,created_at) VALUES ('cost-tenant','Cost fixture','business',now())"
                )
            )
            c.execute(
                text(
                    "INSERT INTO cost_input_manifest(id,tenant_id,target_event_sequence,effective_at,knowledge_at,input_schema_version,algorithm_version,state,content_hash,sealed_at) VALUES ('manifest','cost-tenant',0,now(),now(),1,'receipt-v1','sealed','hash',now())"
                )
            )
        with pytest.raises(RuntimeError, match="retained"):
            command.downgrade(config, "0070_projection_clock_due")
        with engine.connect() as c:
            assert c.scalar(text("SELECT count(*) FROM cost_input_manifest")) == 1
    finally:
        engine.dispose()
