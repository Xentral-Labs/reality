from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from reality.db.core import Base
from sqlalchemy import CheckConstraint, create_engine, inspect, text

TABLES = {
    "mcp_client_grant",
    "mcp_authorization_interaction",
    "mcp_user_credential",
}


def test_mcp_authorization_schema_is_additive_and_tenant_scoped():
    grant = Base.metadata.tables["mcp_client_grant"]
    interaction = Base.metadata.tables["mcp_authorization_interaction"]
    credential = Base.metadata.tables["mcp_user_credential"]

    assert [column.name for column in grant.primary_key.columns] == ["tenant_id", "id"]
    assert [column.name for column in credential.primary_key.columns] == [
        "tenant_id",
        "id",
    ]
    assert interaction.c.grant_id.nullable
    assert "mcp_access_token" in Base.metadata.tables
    assert not any(
        column.name in {"oauth_status", "fulfillment_status"}
        for table in Base.metadata.tables.values()
        for column in table.columns
    )


def _config(database_url: str) -> Config:
    root = Path(__file__).resolve().parents[1]
    config = Config(str(root / "alembic.ini"))
    config.set_main_option("script_location", str(root / "migrations"))
    config.set_main_option("sqlalchemy.url", database_url)
    return config


def test_mcp_authorization_migration_empty_up_down_up(postgres_database, monkeypatch):
    monkeypatch.setenv("REALITY_DATABASE_URL", postgres_database)
    config = _config(postgres_database)
    command.upgrade(config, "0093_mcp_user_authorization")
    engine = create_engine(postgres_database)
    try:
        inspector = inspect(engine)
        assert TABLES <= set(inspector.get_table_names())
        for name in TABLES:
            model = Base.metadata.tables[name]
            assert {row["name"] for row in inspector.get_check_constraints(name)} == {
                constraint.name
                for constraint in model.constraints
                if isinstance(constraint, CheckConstraint)
            }
        command.downgrade(config, "0092_party_email_addresses")
        assert not TABLES & set(inspect(engine).get_table_names())
        command.upgrade(config, "0093_mcp_user_authorization")
        assert TABLES <= set(inspect(engine).get_table_names())
    finally:
        engine.dispose()


def test_mcp_authorization_populated_downgrade_refuses(
    postgres_database, monkeypatch
):
    monkeypatch.setenv("REALITY_DATABASE_URL", postgres_database)
    config = _config(postgres_database)
    command.upgrade(config, "0093_mcp_user_authorization")
    engine = create_engine(postgres_database)
    try:
        with engine.begin() as connection:
            connection.execute(
                text(
                    """
                    INSERT INTO mcp_authorization_interaction (
                        id, client_id, client_metadata, redirect_uri, resource,
                        requested_scopes, code_challenge, code_challenge_method,
                        client_state, status, expires_at
                    ) VALUES (
                        'oai_retained', 'client', '{}', 'https://client.example/cb',
                        'https://mcp.example/', '[\"reality:read\"]',
                        'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa', 'S256', '',
                        'pending', now() + interval '10 minutes'
                    )
                    """
                )
            )
        with pytest.raises(RuntimeError, match="Refusing to remove populated"):
            command.downgrade(config, "0092_party_email_addresses")
        assert TABLES <= set(inspect(engine).get_table_names())
    finally:
        engine.dispose()
