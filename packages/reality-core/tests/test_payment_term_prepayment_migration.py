"""Spec 275: the explicit prepayment policy is additive and reversible."""

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text


def _columns(engine, table: str) -> set[str]:
    return {column["name"] for column in inspect(engine).get_columns(table)}


def test_prepayment_policy_migration_defaults_existing_terms_false_and_downgrades(
    postgres_database, monkeypatch
):
    monkeypatch.setenv("REALITY_DATABASE_URL", postgres_database)
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", postgres_database)
    command.upgrade(config, "0098_chat_agent_decisions")
    engine = create_engine(postgres_database)
    try:
        assert "requires_prepayment" not in _columns(engine, "payment_term")
        with engine.begin() as connection:
            connection.execute(
                text(
                    "INSERT INTO tenant (id, name, purpose, created_at) "
                    "VALUES ('ten_policy', 'Policy tenant', 'business', now())"
                )
            )
            connection.execute(
                text(
                    "INSERT INTO payment_term "
                    "(id, tenant_id, code, name, due_days, is_active) "
                    "VALUES ('ptm_legacy', 'ten_policy', 'NET0', 'Net zero', 0, true)"
                )
            )

        command.upgrade(config, "0099_payment_term_prepayment")

        assert "requires_prepayment" in _columns(engine, "payment_term")
        with engine.begin() as connection:
            assert connection.scalar(
                text(
                    "SELECT requires_prepayment FROM payment_term "
                    "WHERE id = 'ptm_legacy'"
                )
            ) is False
            connection.execute(
                text(
                    "UPDATE payment_term SET requires_prepayment = true "
                    "WHERE id = 'ptm_legacy'"
                )
            )

        command.downgrade(config, "0098_chat_agent_decisions")

        assert "requires_prepayment" not in _columns(engine, "payment_term")
        with engine.begin() as connection:
            assert connection.scalar(
                text("SELECT count(*) FROM payment_term WHERE id = 'ptm_legacy'")
            ) == 1
    finally:
        engine.dispose()
