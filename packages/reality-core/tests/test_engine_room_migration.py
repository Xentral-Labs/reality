"""Spec 266: the interaction table arrives and leaves with its own revision."""

from __future__ import annotations

import pytest
from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from sqlalchemy import create_engine, inspect

from reality.db.core import Base

EXPECTED_INDEXES = {
    "ix_interaction_tenant_id",
    "ix_interaction_actor_user_id",
    "ix_interaction_cursor",
    "ix_interaction_recorded",
    "ix_interaction_correlation",
    "ix_interaction_events",
    "ix_interaction_mcp_token_id",
    "ix_interaction_proposal_id",
}


def _about_interaction(diff) -> bool:
    for part in diff if isinstance(diff, tuple) else ():
        name = getattr(part, "name", None)
        table = getattr(part, "table", None)
        if name == "interaction" or getattr(table, "name", None) == "interaction":
            return True
        if part == "interaction":
            return True
    return False


def test_interaction_table_matches_the_model_and_downgrades(
    postgres_database: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("REALITY_DATABASE_URL", postgres_database)
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", postgres_database)
    command.upgrade(config, "head")
    engine = create_engine(postgres_database)
    try:
        inspector = inspect(engine)
        assert "interaction" in inspector.get_table_names()
        indexes = {index["name"] for index in inspector.get_indexes("interaction")}
        # PostgreSQL reports the unique constraint's backing index as well.
        assert indexes - {"uq_interaction_cursor"} == EXPECTED_INDEXES
        checks = {
            check["name"] for check in inspector.get_check_constraints("interaction")
        }
        assert {
            "ck_interaction_channel",
            "ck_interaction_kind",
            "ck_interaction_outcome",
            "ck_interaction_summary",
        } <= checks
        foreign_keys = {fk["name"] for fk in inspector.get_foreign_keys("interaction")}
        assert {"fk_interaction_mcp_token", "fk_interaction_proposal"} <= foreign_keys
        with engine.connect() as connection:
            diffs = compare_metadata(
                MigrationContext.configure(connection), Base.metadata
            )
        flat = [
            d for diff in diffs for d in (diff if isinstance(diff, list) else [diff])
        ]
        # Positive control: the comparison sees the table at all.
        assert "interaction" in Base.metadata.tables
        assert [diff for diff in flat if _about_interaction(diff)] == []

        command.downgrade(config, "0093_decision_trail")
        assert "interaction" not in set(inspect(engine).get_table_names())
    finally:
        engine.dispose()
