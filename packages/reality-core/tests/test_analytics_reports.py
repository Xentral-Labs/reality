"""Private report configuration is neither business authority nor tenant-wide data."""

from uuid import uuid4

import pytest

from reality.services.analytics.execution import AnalyticsError
from reality.services.analytics.reports import change_report, get_report, list_reports
from reality.services.core import NotFound
from reality.services.memberships import Principal


def create_args():
    return {
        "operation": "create",
        "request_id": str(uuid4()),
        "name": "Weekly sales",
        "definition": {
            "dataset": "sales_orders",
            "dimensions": ["customer_id"],
            "measures": ["order_count"],
        },
    }


def test_private_lifecycle_replay_revision_and_tombstone(
    session, business, scheduled_owner
):
    principal = Principal(scheduled_owner.id)
    arguments = create_args()
    result = change_report(session, business.tenant.id, principal, arguments)
    assert (
        change_report(session, business.tenant.id, principal, arguments)["id"]
        == result["id"]
    )
    renamed = change_report(
        session,
        business.tenant.id,
        principal,
        {
            "operation": "rename",
            "request_id": str(uuid4()),
            "report_id": result["id"],
            "expected_revision": 1,
            "name": "Customer orders",
        },
    )
    assert renamed["revision"] == 2
    with pytest.raises(AnalyticsError):
        change_report(
            session,
            business.tenant.id,
            principal,
            {
                "operation": "rename",
                "request_id": str(uuid4()),
                "report_id": result["id"],
                "expected_revision": 1,
                "name": "Stale",
            },
        )
    change_report(
        session,
        business.tenant.id,
        principal,
        {
            "operation": "delete",
            "request_id": str(uuid4()),
            "report_id": result["id"],
            "expected_revision": 2,
        },
    )
    assert list_reports(session, business.tenant.id, principal)["records"] == []
    replay = change_report(session, business.tenant.id, principal, arguments)
    assert replay["deleted"]
    assert list_reports(session, business.tenant.id, principal)["records"] == []


def test_report_identity_cannot_be_supplied_by_model(
    session, business, scheduled_owner
):
    with pytest.raises(AnalyticsError, match="authenticated"):
        list_reports(session, business.tenant.id, None)
    principal = Principal(scheduled_owner.id)
    with pytest.raises(AnalyticsError):
        change_report(
            session,
            business.tenant.id,
            principal,
            {**create_args(), "owner_user_id": "other"},
        )
    with pytest.raises(NotFound):
        get_report(session, "foreign", principal, "anything")


def test_report_migration_roundtrip(postgres_database, monkeypatch):
    from alembic import command
    from alembic.config import Config
    from sqlalchemy import create_engine, inspect

    monkeypatch.setenv("REALITY_DATABASE_URL", postgres_database)
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", postgres_database)
    command.upgrade(config, "head")
    engine = create_engine(postgres_database)
    try:
        inspector = inspect(engine)
        assert "analytics_report" in inspector.get_table_names()
        constraints = {
            row["name"] for row in inspector.get_unique_constraints("analytics_report")
        }
        assert {
            "uq_analytics_report_create",
            "uq_analytics_report_tenant",
        } <= constraints
        command.downgrade(config, "0058_storyline")
        assert "analytics_report" not in inspect(engine).get_table_names()
        command.upgrade(config, "head")
    finally:
        engine.dispose()


def test_report_migration_refuses_to_drop_saved_definitions(
    postgres_database, monkeypatch
):
    from alembic import command
    from alembic.config import Config
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    from reality.db.core import AppUser, TenantMembership, now, uid
    from reality.services.core import create_tenant

    monkeypatch.setenv("REALITY_DATABASE_URL", postgres_database)
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", postgres_database)
    command.upgrade(config, "head")
    engine = create_engine(postgres_database)
    factory = sessionmaker(engine, expire_on_commit=False)
    try:
        with factory() as db:
            tenant = create_tenant(db, "Saved analytics migration")
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
                    role="owner",
                    status="active",
                )
            )
            db.flush()
            change_report(db, tenant.id, Principal(owner.id), create_args())
            db.commit()
        with pytest.raises(RuntimeError, match="Retain saved reports"):
            command.downgrade(config, "0058_storyline")
    finally:
        engine.dispose()


def test_same_company_member_cannot_read_or_modify_anothers_report(
    session, business, scheduled_owner
):
    from reality.db.core import AppUser, TenantMembership, now, uid

    other = AppUser(
        id=uid("usr"),
        email=f"{uid('mail')}@example.test",
        password_hash="unused",
        status="active",
        email_verified_at=now(),
    )
    session.add(other)
    session.flush()
    session.add(
        TenantMembership(
            id=uid("tmb"),
            tenant_id=business.tenant.id,
            user_id=other.id,
            role="member",
            status="active",
        )
    )
    session.flush()
    owner = Principal(scheduled_owner.id)
    report = change_report(session, business.tenant.id, owner, create_args())
    stranger = Principal(other.id)
    assert list_reports(session, business.tenant.id, stranger)["records"] == []
    for operation in ("get", "rename", "delete", "duplicate"):
        with pytest.raises(NotFound):
            if operation == "get":
                get_report(session, business.tenant.id, stranger, report["id"])
            else:
                change_report(
                    session,
                    business.tenant.id,
                    stranger,
                    {
                        "operation": operation,
                        "report_id": report["id"],
                        "expected_revision": 1,
                        "request_id": str(uuid4()),
                        **({"name": "Stolen"} if operation != "delete" else {}),
                    },
                )


def test_report_cursor_is_bound_to_search_and_owner(session, business, scheduled_owner):
    owner = Principal(scheduled_owner.id)
    for _ in range(3):
        change_report(session, business.tenant.id, owner, create_args())
    first = list_reports(session, business.tenant.id, owner, limit=1)
    second = list_reports(
        session, business.tenant.id, owner, limit=1, cursor=first["next_cursor"]
    )
    assert first["records"][0]["id"] != second["records"][0]["id"]
    with pytest.raises(AnalyticsError, match="cursor"):
        list_reports(
            session,
            business.tenant.id,
            owner,
            query="Weekly",
            cursor=first["next_cursor"],
        )


def test_concurrent_report_creation_replays_one_row(scheduled_database):
    from concurrent.futures import ThreadPoolExecutor

    _engine, factory, tenant_id, actor_id = scheduled_database
    arguments = create_args()

    def create():
        with factory() as db:
            result = change_report(db, tenant_id, Principal(actor_id), arguments)
            db.commit()
            return result["id"]

    with ThreadPoolExecutor(max_workers=2) as pool:
        ids = list(pool.map(lambda _: create(), range(2)))
    assert ids[0] == ids[1]
    with factory() as db:
        assert len(list_reports(db, tenant_id, Principal(actor_id))["records"]) == 1
