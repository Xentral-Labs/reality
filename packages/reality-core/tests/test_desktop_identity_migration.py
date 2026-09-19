"""Existing email identities remain email; local identities prohibit unsafe downgrade."""

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text


def test_desktop_identity_upgrade_and_downgrade_guard(postgres_database, monkeypatch):
    monkeypatch.setenv("REALITY_DATABASE_URL", postgres_database)
    config = Config("alembic.ini")
    command.upgrade(config, "0066_global_search_support")
    engine = create_engine(postgres_database)
    try:
        with engine.begin() as connection:
            connection.execute(
                text(
                    "INSERT INTO app_user (id,email,password_hash,display_name,status,language,locale,timezone,is_platform_admin,created_at,updated_at) VALUES ('existing','existing@example.test','x','','active','en','en-GB','UTC',false,now(),now())"
                )
            )
        command.upgrade(config, "0067_desktop_identity")
        with engine.begin() as connection:
            assert (
                connection.scalar(
                    text(
                        "SELECT authentication_method FROM app_user WHERE id='existing'"
                    )
                )
                == "email"
            )
            connection.execute(
                text(
                    "UPDATE app_user SET authentication_method='local_os' WHERE id='existing'"
                )
            )
        with pytest.raises(RuntimeError, match="Cannot downgrade"):
            command.downgrade(config, "0066_global_search_support")
        with engine.begin() as connection:
            connection.execute(
                text(
                    "UPDATE app_user SET authentication_method='email' WHERE id='existing'"
                )
            )
        command.downgrade(config, "0066_global_search_support")
        command.upgrade(config, "0067_desktop_identity")
    finally:
        engine.dispose()
