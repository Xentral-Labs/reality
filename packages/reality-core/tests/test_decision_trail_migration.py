"""Spec 263 DR-002: token attribution is additive, reversible and needs no backfill."""

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text


def _columns(engine, table: str) -> set[str]:
    return {column["name"] for column in inspect(engine).get_columns(table)}


def test_decision_trail_migration_upgrades_and_downgrades(
    postgres_database: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("REALITY_DATABASE_URL", postgres_database)
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", postgres_database)
    command.upgrade(config, "0092_party_email_addresses")
    engine = create_engine(postgres_database)
    try:
        with engine.begin() as connection:
            connection.execute(
                text(
                    "INSERT INTO tenant (id, name, purpose, created_at) "
                    "VALUES ('ten_a', 'A', 'business', now())"
                )
            )
            connection.execute(
                text(
                    "INSERT INTO mcp_access_token "
                    "(id, tenant_id, name, token_prefix, token_hash, allowed_tools, "
                    "created_at) VALUES ('mcp_legacy', 'ten_a', 'Legacy', 'rmcp_legacy', "
                    "'hash-legacy', '[\"*\"]', now())"
                )
            )
            connection.execute(
                text(
                    "INSERT INTO action (id, tenant_id, type, actor_type, status, "
                    "input, output, created_at) VALUES ('act_old', 'ten_a', "
                    "'tool:item_create', 'agent', 'executed', '{}', '{}', now())"
                )
            )

        command.upgrade(config, "0093_decision_trail")

        assert "created_by_user_id" in _columns(engine, "mcp_access_token")
        assert "decided_via_token_id" in _columns(engine, "action")
        inspector = inspect(engine)
        assert any(
            key["referred_table"] == "mcp_access_token"
            and key["constrained_columns"] == ["tenant_id", "decided_via_token_id"]
            and key["referred_columns"] == ["tenant_id", "id"]
            for key in inspector.get_foreign_keys("action")
        )
        assert any(
            key["referred_table"] == "app_user"
            and key["constrained_columns"] == ["created_by_user_id"]
            for key in inspector.get_foreign_keys("mcp_access_token")
        )
        assert ["tenant_id", "decided_via_token_id"] in [
            index["column_names"] for index in inspector.get_indexes("action")
        ]
        assert ["created_by_user_id"] in [
            index["column_names"] for index in inspector.get_indexes("mcp_access_token")
        ]
        with engine.begin() as connection:
            # Nothing is backfilled: existing rows keep an honest blank.
            assert (
                connection.scalar(
                    text(
                        "SELECT created_by_user_id FROM mcp_access_token "
                        "WHERE id = 'mcp_legacy'"
                    )
                )
                is None
            )
            assert (
                connection.scalar(
                    text("SELECT decided_via_token_id FROM action WHERE id = 'act_old'")
                )
                is None
            )
            connection.execute(
                text(
                    "UPDATE action SET decided_via_token_id = 'mcp_legacy' "
                    "WHERE id = 'act_old'"
                )
            )

        command.downgrade(config, "0092_party_email_addresses")

        assert "created_by_user_id" not in _columns(engine, "mcp_access_token")
        assert "decided_via_token_id" not in _columns(engine, "action")
        with engine.begin() as connection:
            assert connection.scalar(text("SELECT count(*) FROM action")) == 1, (
                "downgrade must not lose business rows"
            )
    finally:
        engine.dispose()
