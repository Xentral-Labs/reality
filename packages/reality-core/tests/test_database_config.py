import pytest

from reality.db.core import (
    build_engine,
    resolve_database_pool_settings,
    resolve_database_url,
)


def test_database_url_requires_shared_postgresql_url():
    shared = "postgresql+psycopg://reality:secret@db/reality"
    assert resolve_database_url({"REALITY_DATABASE_URL": shared}) == shared
    with pytest.raises(RuntimeError, match="must be configured"):
        resolve_database_url({})
    with pytest.raises(ValueError, match="must use PostgreSQL"):
        resolve_database_url({"REALITY_DATABASE_URL": "mysql://user:secret@db/reality"})


def test_postgresql_engine_can_be_configured_without_connecting():
    database_engine = build_engine(
        "postgresql+psycopg://reality:secret@localhost/reality",
        pool_settings=resolve_database_pool_settings(
            {
                "REALITY_DB_POOL_SIZE": "3",
                "REALITY_DB_MAX_OVERFLOW": "2",
                "REALITY_DB_POOL_TIMEOUT": "7",
            }
        ),
    )
    try:
        assert database_engine.dialect.name == "postgresql"
        assert database_engine.pool.size() == 3
        assert database_engine.pool._max_overflow == 2
        assert database_engine.pool._timeout == 7
    finally:
        database_engine.dispose()


def test_non_postgresql_engine_is_rejected():
    with pytest.raises(ValueError, match="requires PostgreSQL"):
        build_engine("mysql://user:secret@localhost/reality")


@pytest.mark.parametrize(
    ("name", "value"),
    [
        ("REALITY_DB_POOL_SIZE", "0"),
        ("REALITY_DB_POOL_SIZE", "101"),
        ("REALITY_DB_MAX_OVERFLOW", "-1"),
        ("REALITY_DB_MAX_OVERFLOW", "101"),
        ("REALITY_DB_POOL_TIMEOUT", "0"),
        ("REALITY_DB_POOL_TIMEOUT", "301"),
        ("REALITY_DB_POOL_SIZE", "many"),
    ],
)
def test_database_pool_settings_are_bounded(name: str, value: str):
    with pytest.raises(ValueError, match=name):
        resolve_database_pool_settings({name: value})
