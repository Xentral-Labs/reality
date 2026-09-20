"""Spec 234 inventory authority migration preserves tenant links and retained history."""

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text

TABLES = {
    "cost_policy_revision",
    "cost_movement_basis",
    "cost_ownership_revision",
    "cost_inventory_review",
    "cost_inventory_member",
}


def test_inventory_migration_foreign_keys_and_empty_rollback(
    postgres_database, monkeypatch
):
    monkeypatch.setenv("REALITY_DATABASE_URL", postgres_database)
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", postgres_database)
    command.upgrade(config, "0072_inventory_costing")
    engine = create_engine(postgres_database)
    try:
        from reality.db.core import Base

        inspector = inspect(engine)
        assert TABLES <= set(inspector.get_table_names())
        assert any(
            index["name"] == "ix_cost_movement_pool_cutoff"
            and index["column_names"] == ["tenant_id", "item_id", "occurred_at", "id"]
            for index in inspector.get_indexes("movement")
        )
        for name in TABLES:
            actual = {
                tuple(f["constrained_columns"])
                for f in inspector.get_foreign_keys(name)
            }
            expected = {
                tuple(f.column_keys)
                for f in Base.metadata.tables[name].foreign_key_constraints
            }
            assert actual == expected, name
        command.downgrade(config, "0071_receipt_costing")
        assert not TABLES & set(inspect(engine).get_table_names())
        assert "cost_receipt_basis" in inspect(engine).get_table_names()
    finally:
        engine.dispose()


def test_inventory_populated_downgrade_refuses(postgres_database, monkeypatch):
    monkeypatch.setenv("REALITY_DATABASE_URL", postgres_database)
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", postgres_database)
    command.upgrade(config, "0072_inventory_costing")
    engine = create_engine(postgres_database)
    try:
        # Use normal service fixtures elsewhere; here a sentinel verifies the guard
        # runs before dropping even the first authority table.
        with engine.begin() as connection:
            connection.execute(
                text("ALTER TABLE cost_inventory_review DISABLE TRIGGER ALL")
            )
            connection.execute(
                text(
                    "INSERT INTO cost_inventory_review(id,tenant_id,policy_id,effective_at,target_event_sequence,knowledge_at,introduced_event_id,action_id,reason,algorithm_version,input_schema_version,content_hash) VALUES ('r','t','p',now(),1,now(),'e','a','retained','inventory-v1',1,'hash')"
                )
            )
            connection.execute(
                text("ALTER TABLE cost_inventory_review ENABLE TRIGGER ALL")
            )
        with pytest.raises(RuntimeError, match="retained"):
            command.downgrade(config, "0071_receipt_costing")
        assert TABLES <= set(inspect(engine).get_table_names())
    finally:
        engine.dispose()


def test_specific_policy_constraint_and_populated_downgrade_guard(
    postgres_database, monkeypatch
):
    monkeypatch.setenv("REALITY_DATABASE_URL", postgres_database)
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", postgres_database)
    command.upgrade(config, "0081_inventory_specific_policy")
    engine = create_engine(postgres_database)
    try:
        constraint = next(
            row
            for row in inspect(engine).get_check_constraints("cost_policy_revision")
            if row["name"] == "ck_inventory_policy"
        )
        assert "specific" in constraint["sqltext"]
        with engine.begin() as connection:
            connection.execute(
                text("ALTER TABLE cost_policy_revision DISABLE TRIGGER ALL")
            )
            connection.execute(
                text(
                    "INSERT INTO cost_policy_revision(id,tenant_id,item_id,owner_party_id,revision,method,currency,base_unit,history_start,introduced_event_id,action_id,reason) VALUES ('p','t','i','o',1,'specific','EUR','pcs',now(),'e','a','retained specific policy')"
                )
            )
            connection.execute(
                text("ALTER TABLE cost_policy_revision ENABLE TRIGGER ALL")
            )
        with pytest.raises(RuntimeError, match="specific-identification"):
            command.downgrade(config, "0080_company_generations")
        assert (
            "specific"
            in next(
                row
                for row in inspect(engine).get_check_constraints("cost_policy_revision")
                if row["name"] == "ck_inventory_policy"
            )["sqltext"]
        )
    finally:
        engine.dispose()


def test_return_loss_constraints_are_widened(postgres_database, monkeypatch):
    monkeypatch.setenv("REALITY_DATABASE_URL", postgres_database)
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", postgres_database)
    command.upgrade(config, "0082_inventory_returns_losses")
    engine = create_engine(postgres_database)
    try:
        movement = next(
            row
            for row in inspect(engine).get_check_constraints("cost_movement_basis")
            if row["name"] == "ck_inventory_movement"
        )["sqltext"]
        member = next(
            row
            for row in inspect(engine).get_check_constraints("cost_inventory_member")
            if row["name"] == "ck_inventory_member"
        )["sqltext"]
        assert all(
            kind in movement for kind in ("return", "supplier_return", "adjustment")
        )
        assert all(
            kind in member for kind in ("customer_return", "supplier_return", "loss")
        )
        with engine.begin() as connection:
            connection.execute(
                text("ALTER TABLE cost_movement_basis DISABLE TRIGGER ALL")
            )
            connection.execute(
                text("ALTER TABLE cost_inventory_member DISABLE TRIGGER ALL")
            )
            connection.execute(
                text(
                    "INSERT INTO cost_movement_basis(id,tenant_id,movement_id,movement_event_id,introduced_event_id,movement_type,base_quantity,base_unit,occurred_at,input_schema_version) VALUES ('b','t','m','e','i','return',1,'pcs',now(),1)"
                )
            )
            connection.execute(
                text(
                    "INSERT INTO cost_inventory_member(id,tenant_id,review_id,movement_basis_id,kind) VALUES ('x','t','r','b','customer_return')"
                )
            )
            connection.execute(
                text("ALTER TABLE cost_inventory_member ENABLE TRIGGER ALL")
            )
            connection.execute(
                text("ALTER TABLE cost_movement_basis ENABLE TRIGGER ALL")
            )
        with pytest.raises(RuntimeError, match="return/loss"):
            command.downgrade(config, "0081_inventory_specific_policy")
    finally:
        engine.dispose()


def test_opening_basis_migration_matches_model_and_empty_rollback(
    postgres_database, monkeypatch
):
    monkeypatch.setenv("REALITY_DATABASE_URL", postgres_database)
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", postgres_database)
    command.upgrade(config, "0083_inventory_opening_basis")
    engine = create_engine(postgres_database)
    try:
        from reality.db.core import Base

        inspector = inspect(engine)
        assert "cost_opening_basis" in inspector.get_table_names()
        actual = {
            tuple(row["constrained_columns"])
            for row in inspector.get_foreign_keys("cost_opening_basis")
        }
        expected = {
            tuple(row.column_keys)
            for row in Base.metadata.tables[
                "cost_opening_basis"
            ].foreign_key_constraints
        }
        assert actual == expected
        assert (
            "opening_stock"
            in next(
                row
                for row in inspector.get_check_constraints("cost_movement_basis")
                if row["name"] == "ck_inventory_movement"
            )["sqltext"]
        )
        command.downgrade(config, "0082_inventory_returns_losses")
        assert "cost_opening_basis" not in inspect(engine).get_table_names()
    finally:
        engine.dispose()


def test_opening_basis_populated_downgrade_refuses(postgres_database, monkeypatch):
    monkeypatch.setenv("REALITY_DATABASE_URL", postgres_database)
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", postgres_database)
    command.upgrade(config, "0083_inventory_opening_basis")
    engine = create_engine(postgres_database)
    try:
        with engine.begin() as connection:
            connection.execute(
                text("ALTER TABLE cost_opening_basis DISABLE TRIGGER ALL")
            )
            connection.execute(
                text(
                    "INSERT INTO cost_opening_basis(id,tenant_id,movement_basis_id,owner_party_id,evidence_source_record_id,acquisition_cost,currency,input_schema_version,introduced_event_id,action_id,reason) VALUES ('o','t','m','p','s',0,'EUR',1,'e','a','retained opening')"
                )
            )
            connection.execute(
                text("ALTER TABLE cost_opening_basis ENABLE TRIGGER ALL")
            )
        with pytest.raises(RuntimeError, match="opening-basis"):
            command.downgrade(config, "0082_inventory_returns_losses")
        assert "cost_opening_basis" in inspect(engine).get_table_names()
    finally:
        engine.dispose()


def test_ownership_parts_migration_matches_model_and_empty_rollback(
    postgres_database, monkeypatch
):
    monkeypatch.setenv("REALITY_DATABASE_URL", postgres_database)
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", postgres_database)
    command.upgrade(config, "0084_inventory_ownership_parts")
    engine = create_engine(postgres_database)
    try:
        from reality.db.core import Base

        inspector = inspect(engine)
        name = "cost_inventory_ownership_part"
        assert name in inspector.get_table_names()
        actual = {
            tuple(row["constrained_columns"])
            for row in inspector.get_foreign_keys(name)
        }
        expected = {
            tuple(row.column_keys)
            for row in Base.metadata.tables[name].foreign_key_constraints
        }
        assert actual == expected
        command.downgrade(config, "0083_inventory_opening_basis")
        assert name not in inspect(engine).get_table_names()
    finally:
        engine.dispose()


def test_ownership_parts_populated_downgrade_refuses(postgres_database, monkeypatch):
    monkeypatch.setenv("REALITY_DATABASE_URL", postgres_database)
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", postgres_database)
    command.upgrade(config, "0084_inventory_ownership_parts")
    engine = create_engine(postgres_database)
    try:
        with engine.begin() as connection:
            connection.execute(
                text("ALTER TABLE cost_inventory_ownership_part DISABLE TRIGGER ALL")
            )
            connection.execute(
                text(
                    "INSERT INTO cost_inventory_ownership_part(id,tenant_id,review_id,movement_basis_id,owner_party_id,evidence_source_record_id,quantity,input_schema_version) VALUES ('p','t','r','m','o','s',1,1)"
                )
            )
            connection.execute(
                text("ALTER TABLE cost_inventory_ownership_part ENABLE TRIGGER ALL")
            )
        with pytest.raises(RuntimeError, match="ownership-part"):
            command.downgrade(config, "0083_inventory_opening_basis")
        assert "cost_inventory_ownership_part" in inspect(engine).get_table_names()
    finally:
        engine.dispose()
