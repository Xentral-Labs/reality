from __future__ import annotations

import os
import uuid
from dataclasses import dataclass

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker

os.environ.setdefault("REALITY_AUTH_MODE", "disabled")

POSTGRES_ADMIN_URL = os.getenv(
    "TEST_POSTGRES_ADMIN_URL",
    "postgresql+psycopg://reality:local-only@localhost:54329/postgres",
)
TEST_DATABASE_NAME = f"reality_pytest_{uuid.uuid4().hex[:10]}"
admin_url = make_url(POSTGRES_ADMIN_URL)
test_url = admin_url.set(database=TEST_DATABASE_NAME)
admin_engine = create_engine(admin_url, isolation_level="AUTOCOMMIT")
with admin_engine.connect() as connection:
    connection.execute(text(f'CREATE DATABASE "{TEST_DATABASE_NAME}"'))
os.environ["REALITY_DATABASE_URL"] = test_url.render_as_string(hide_password=False)

from reality.db.core import Base, build_engine
from reality.services.core import (
    create_item,
    create_location,
    create_party,
    create_tenant,
)

test_engine = build_engine(os.environ["REALITY_DATABASE_URL"])
# Build the schema once per worker; each test rolls back its outer transaction.
Base.metadata.create_all(test_engine)


def _drop_database(database_name: str) -> None:
    with admin_engine.connect() as connection:
        connection.execute(
            text(
                "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
                "WHERE datname = :database_name AND pid <> pg_backend_pid()"
            ),
            {"database_name": database_name},
        )
        connection.execute(text(f'DROP DATABASE IF EXISTS "{database_name}"'))


def pytest_sessionfinish(session, exitstatus):
    test_engine.dispose()
    _drop_database(TEST_DATABASE_NAME)
    admin_engine.dispose()


@pytest.fixture(autouse=True)
def no_leaked_dependency_overrides():
    """Fail the test that leaves a FastAPI dependency override installed.

    `app.dependency_overrides` is process-global, and the usual override binds a
    session factory to *this* test's connection. Left behind, it hands a closed
    connection to whichever later test uses the app without installing an
    override of its own — which fails in a different file, minutes later, with
    a `ResourceClosedError` that says nothing about the cause.

    Forty tests remembered to clear it in a `finally` and one did not, so the
    convention was not the protection anybody thought it was. This names the
    test that leaked rather than the test that tripped over it, and clears the
    override so the damage stops there.
    """
    from reality.web.app import app

    yield
    leaked = sorted(
        getattr(key, "__name__", str(key)) for key in app.dependency_overrides
    )
    app.dependency_overrides.clear()
    assert not leaked, (
        "This test left FastAPI dependency overrides installed: "
        f"{leaked}. Clear them in a finally block; a later test will otherwise "
        "be handed this test's closed database connection."
    )


@pytest.fixture
def postgres_database():
    database_name = f"reality_migration_{uuid.uuid4().hex[:10]}"
    with admin_engine.connect() as connection:
        connection.execute(text(f'CREATE DATABASE "{database_name}"'))
    url = admin_url.set(database=database_name).render_as_string(hide_password=False)
    try:
        yield url
    finally:
        _drop_database(database_name)


@pytest.fixture
def session():
    with test_engine.connect() as connection:
        transaction = connection.begin()
        factory = sessionmaker(
            bind=connection,
            expire_on_commit=False,
            join_transaction_mode="create_savepoint",
        )
        try:
            with factory() as db_session:
                yield db_session
        finally:
            transaction.rollback()


@dataclass
class Business:
    tenant: object
    company: object
    customer: object
    supplier: object
    item: object
    location: object


@pytest.fixture
def business(session):
    tenant = create_tenant(session, "Acme Bikes GmbH")
    return Business(
        tenant=tenant,
        company=create_party(session, tenant.id, "Acme Bikes GmbH", "company"),
        customer=create_party(session, tenant.id, "Müller GmbH", "customer"),
        supplier=create_party(session, tenant.id, "Bike Parts GmbH", "supplier"),
        item=create_item(session, tenant.id, "BIKE-LIGHT", "Bike Light"),
        location=create_location(session, tenant.id, "Augsburg Warehouse"),
    )


@pytest.fixture
def scheduled_owner(session, business):
    from reality.db.core import AppUser, TenantMembership, now, uid

    user = AppUser(
        id=uid("usr"),
        email=f"{uid('mail')}@example.test",
        password_hash="unused",
        status="active",
        email_verified_at=now(),
    )
    session.add(user)
    session.flush()
    session.add(
        TenantMembership(
            id=uid("tmb"),
            tenant_id=business.tenant.id,
            user_id=user.id,
            role="owner",
            status="active",
        )
    )
    session.flush()
    return user


@pytest.fixture
def scheduled_database(postgres_database, monkeypatch):
    """Committed isolated fixture for real subprocess and concurrent connection proofs."""
    from reality.db.core import AppUser, TenantMembership, now, uid

    monkeypatch.setenv("REALITY_DATABASE_URL", postgres_database)
    engine = create_engine(postgres_database)
    Base.metadata.create_all(engine)
    factory = sessionmaker(engine, expire_on_commit=False)
    with factory() as db:
        tenant = create_tenant(db, "Scheduled Work Example")
        owner = AppUser(
            id=uid("usr"),
            email=f"{uid('mail')}@example.test",
            password_hash="unused",
            status="active",
            email_verified_at=now(),
        )
        db.add(owner)
        db.flush()
        db.add(
            TenantMembership(
                id=uid("tmb"),
                tenant_id=tenant.id,
                user_id=owner.id,
                status="active",
                role="owner",
            )
        )
        db.commit()
        tenant_id, actor_id = tenant.id, owner.id
    try:
        yield engine, factory, tenant_id, actor_id
    finally:
        engine.dispose()


@pytest.fixture
def company_setup_login(session):
    """Real verified account cookie for account-scoped company creation tests."""
    from datetime import timedelta

    from reality.db.core import AppUser, UserSession, now, uid
    from reality.web.auth import COOKIE_NAME, digest

    actor = AppUser(
        id=uid("usr"),
        email=f"{uid('mail')}@example.test",
        password_hash="unused",
        status="active",
        email_verified_at=now(),
    )
    session.add(actor)
    session.commit()

    def login(client):
        token = uid("login")
        session.add(
            UserSession(
                id=uid("ses"),
                user_id=actor.id,
                token_hash=digest(token),
                expires_at=now() + timedelta(days=1),
            )
        )
        session.commit()
        client.cookies.set(COOKIE_NAME, token)
        return actor

    return login
