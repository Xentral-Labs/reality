"""Spec 196: extensions preserve consumption and account audit boundaries."""

import json
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select
from test_free_playground import sandbox

from reality.db.core import AppUser, SecurityAuditEvent, now, uid
from reality.services import ai_usage, free_playground
from reality.services.core import InvalidOperation, NotFound


def exhaust(db, tenant, actor):
    while free_playground.allowance(db, tenant, actor)["remaining"]:
        free_playground.reserve_managed_question(db, tenant, actor)


def grant(db, tenant, actor, key, **kwargs):
    return ai_usage.grant(db, tenant, actor, request_key=key, confirmed=True, **kwargs)


def test_lifetime_replay_reset_and_audit(session, scheduled_owner, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "fake-no-network")
    instant = datetime(2026, 9, 14, 12, tzinfo=UTC)
    monkeypatch.setattr(free_playground, "now", lambda: instant)
    monkeypatch.setattr(ai_usage, "now", lambda: instant)
    actor = scheduled_owner.id
    tenant = sandbox(session, scheduled_owner)
    other = sandbox(session, scheduled_owner)
    exhaust(session, tenant, actor)
    for index in range(3):
        result = grant(session, other, actor, str(index))
        assert result["allowance"]["remaining"] == 20
        assert result["allowance"]["used"] == 20
        assert result["self_extensions_remaining"] == 2 - index
        assert grant(session, tenant, actor, str(index))["allowance"]["remaining"] == 20
        assert result["history"][0]["actor_user_id"] == actor
        assert result["history"][0]["recipient_user_id"] == actor
        assert result["history"][0]["reason"] == "Continued testing"
        instant += timedelta(days=1)
        current = free_playground.allowance(session, tenant, actor)
        assert current["used"] == 0 and current["remaining"] == 20
        assert current["bonus_questions"] == 0
        exhaust(session, tenant, actor)
    with pytest.raises(InvalidOperation, match="extensions"):
        grant(session, tenant, actor, "fourth")
    rows = session.scalars(
        select(SecurityAuditEvent).where(
            SecurityAuditEvent.event_type == ai_usage.GRANT_EVENT,
            SecurityAuditEvent.user_id == actor,
        )
    ).all()
    assert len(rows) == 3
    assert all(json.loads(row.detail)["questions"] == 20 for row in rows)


def test_confirmation_privileges_and_admin(session, scheduled_owner, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "fake-no-network")
    tenant = sandbox(session, scheduled_owner)
    actor = scheduled_owner.id
    with pytest.raises(InvalidOperation):
        ai_usage.grant(session, tenant, actor, request_key="x")
    with pytest.raises(InvalidOperation):
        grant(session, tenant, actor, "x")
    with pytest.raises(InvalidOperation):
        grant(session, tenant, actor, "x", mode="admin", questions=100, reason="Test")
    with pytest.raises(NotFound):
        ai_usage.status(session, "missing", actor)
    with pytest.raises(InvalidOperation):
        ai_usage.status(session, tenant, actor, recipient_email="someone@example.com")
    admin = AppUser(
        id=uid("usr"),
        email="privilege-admin@example.test",
        password_hash="unused",
        status="active",
        email_verified_at=now(),
        is_platform_admin=True,
    )
    session.add(admin)
    session.commit()
    result = grant(
        session,
        tenant,
        admin.id,
        "admin",
        recipient_email=scheduled_owner.email,
        mode="admin",
        questions=100,
        reason="Acceptance testing",
    )
    assert result["allowance"]["remaining"] == 120
    assert result["allowance"]["used"] == 0
    assert result["self_extensions_remaining"] == 3
    assert result["history"][0]["mode"] == "admin"
    with pytest.raises(InvalidOperation):
        grant(
            session,
            tenant,
            admin.id,
            "admin",
            recipient_email=scheduled_owner.email,
            mode="admin",
            questions=20,
            reason="Acceptance testing",
        )
    with pytest.raises(InvalidOperation):
        grant(
            session,
            tenant,
            admin.id,
            "bad",
            recipient_email=scheduled_owner.email,
            mode="admin",
            questions=100,
            reason=" ",
        )
    for _ in range(21):
        free_playground.reserve_managed_question(session, tenant, actor)
    current = free_playground.allowance(session, tenant, actor)
    assert current["used"] == 21 and current["remaining"] == 99
    assert current["bonus_remaining"] == 99


def test_concurrent_self_extension_is_atomic(scheduled_database, monkeypatch):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier
    from types import SimpleNamespace

    _, factory, _, actor = scheduled_database
    monkeypatch.setenv("ANTHROPIC_API_KEY", "fake-no-network")
    with factory() as db:
        tenant = sandbox(db, SimpleNamespace(id=actor))
        for i in range(2):
            exhaust(db, tenant, actor)
            grant(db, tenant, actor, str(i))
        exhaust(db, tenant, actor)
    barrier = Barrier(2)

    def attempt(i):
        with factory() as db:
            barrier.wait(timeout=10)
            try:
                grant(db, tenant, actor, f"last-{i}")
                return "granted"
            except InvalidOperation:
                return "denied"

    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(attempt, range(2))) == ["denied", "granted"]
    with factory() as db:
        assert ai_usage.status(db, tenant, actor)["self_extensions_remaining"] == 0
        assert free_playground.allowance(db, tenant, actor)["remaining"] == 20


from test_playground_api import playground_http as _playground_http

playground_http = _playground_http


def test_usage_api_real_auth_confirmation_and_history(
    session, playground_http, monkeypatch
):
    client, tenant, user, _run, login = playground_http
    monkeypatch.setenv("ANTHROPIC_API_KEY", "fake-no-network")
    path = "/api/company-setup/ai-usage"
    assert client.get(path, params={"tenant_id": tenant.id}).status_code == 401
    login(user)
    exhaust(session, tenant.id, user.id)
    status = client.get(path, params={"tenant_id": tenant.id})
    assert status.status_code == 200, status.text
    assert status.json()["self_extensions_remaining"] == 3
    body = {"tenant_id": tenant.id, "request_key": "http-grant"}
    assert client.post(path, json=body).status_code == 422
    result = client.post(path, json={**body, "confirmed": True})
    assert result.status_code == 200, result.text
    assert result.json()["allowance"]["remaining"] == 20
    assert result.json()["history"][0]["actor_user_id"] == user.id
    assert (
        client.post(path, json={**body, "confirmed": True}).json()[
            "self_extensions_remaining"
        ]
        == 2
    )
    assert (
        client.post(
            path, json={**body, "confirmed": True, "questions": True}
        ).status_code
        == 422
    )
    assert client.get(path, params={"tenant_id": "foreign"}).status_code == 404


def test_admin_target_audit_and_cross_account_isolation(
    session, scheduled_owner, monkeypatch
):
    from reality.db.core import TenantMembership

    monkeypatch.setenv("ANTHROPIC_API_KEY", "fake-no-network")
    tenant = sandbox(session, scheduled_owner)
    target = scheduled_owner
    admin = AppUser(
        id=uid("usr"),
        email="grant-admin@example.test",
        password_hash="unused",
        status="active",
        email_verified_at=now(),
        is_platform_admin=True,
    )
    session.add(admin)
    session.commit()
    result = grant(
        session,
        tenant,
        admin.id,
        "other",
        recipient_email=target.email,
        mode="admin",
        questions=20,
        reason="Support testing",
    )
    assert result["recipient"]["id"] == target.id
    assert result["history"][0]["actor_user_id"] == admin.id
    assert result["history"][0]["recipient_user_id"] == target.id
    assert ai_usage.status(session, tenant, admin.id)["history"] == []
    member = session.scalar(
        select(TenantMembership).where(
            TenantMembership.tenant_id == tenant, TenantMembership.user_id == target.id
        )
    )
    member.status = "removed"
    session.commit()
    with pytest.raises(NotFound):
        ai_usage.status(session, tenant, target.id)
    with pytest.raises(NotFound):
        grant(
            session,
            tenant,
            admin.id,
            "denied",
            recipient_email=target.email,
            mode="admin",
            questions=20,
            reason="Support testing",
        )


def test_ineligible_and_arbitrary_grants_rejected(
    session, scheduled_owner, monkeypatch
):
    tenant = sandbox(session, scheduled_owner)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    assert ai_usage.status(session, tenant, scheduled_owner.id)["allowance"] is None
    with pytest.raises(InvalidOperation):
        grant(session, tenant, scheduled_owner.id, "no-provider")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "fake-no-network")
    for count in (100, 21, True):
        with pytest.raises(InvalidOperation):
            grant(session, tenant, scheduled_owner.id, "arbitrary", questions=count)
