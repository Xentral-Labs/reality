"""The 0061 backfill applies only the association rules already in force (spec 211)."""

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text


def _columns(engine) -> set[str]:
    return {column["name"] for column in inspect(engine).get_columns("source_system")}


def test_addressing_columns_roundtrip(postgres_database, monkeypatch):
    monkeypatch.setenv("REALITY_DATABASE_URL", postgres_database)
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", postgres_database)
    command.upgrade(config, "head")
    engine = create_engine(postgres_database)
    try:
        assert {"base_url", "connector_code"} <= _columns(engine)
        command.downgrade(config, "0060_analytics_reports")
        assert not {"base_url", "connector_code"} & _columns(engine)
        command.upgrade(config, "head")
        assert {"base_url", "connector_code"} <= _columns(engine)
    finally:
        engine.dispose()


def test_backfill_resolves_only_unambiguous_connectors(postgres_database, monkeypatch):
    monkeypatch.setenv("REALITY_DATABASE_URL", postgres_database)
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", postgres_database)
    command.upgrade(config, "0060_analytics_reports")
    engine = create_engine(postgres_database)
    try:
        with engine.begin() as connection:
            connection.execute(
                text(
                    "INSERT INTO tenant (id, name, purpose, created_at) "
                    "VALUES ('ten_1', 'Acme', 'business', now())"
                )
            )
            for identity, code, description in (
                ("sys_exact", "shopify", "Shopify Commerce source definition"),
                (
                    "sys_payments",
                    "shopify_payments_de",
                    "Shopify Payments Payments source definition · no connection",
                ),
                (
                    "sys_named",
                    "shop_de",
                    "Shopify Commerce source definition · no connection",
                ),
                ("sys_hand", "legacy_ftp", "Nightly export from the old server"),
            ):
                connection.execute(
                    text(
                        "INSERT INTO source_system "
                        "(id, tenant_id, code, name, description, is_active, "
                        " created_at, updated_at) "
                        "VALUES (:id, 'ten_1', :code, :code, :description, true, "
                        " now(), now())"
                    ),
                    {"id": identity, "code": code, "description": description},
                )
        command.upgrade(config, "head")
        with engine.connect() as connection:
            resolved = dict(
                connection.execute(
                    text("SELECT id, connector_code FROM source_system")
                ).all()
            )
        assert resolved["sys_exact"] == "shopify"
        # The longest display name wins, so this is not claimed by "Shopify ".
        assert resolved["sys_payments"] == "shopify_payments"
        assert resolved["sys_named"] == "shopify"
        assert resolved["sys_hand"] is None
    finally:
        engine.dispose()
