from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import func, select

from reality.db.core import PlaygroundRun, Tenant, now, uid
from reality.services import company_setup, free_playground
from reality.services.core import InvalidOperation


def consent(session, user):
    free_playground.request_entry(session, user.id)
    session.commit()


def sandbox(session, user):
    return company_setup.create_company(
        session, user.id, uid("test"), "Quota demo", "sandbox", "empty", confirmed=True
    )["tenant_id"]


def test_entry_requires_consent_verification_and_confirmation(session, scheduled_owner):
    user = scheduled_owner
    assert not free_playground.entry_status(session, user.id)["requested"]
    with pytest.raises(InvalidOperation):
        free_playground.enter(session, user.id, confirmed=True)
    consent(session, user)
    with pytest.raises(InvalidOperation):
        free_playground.enter(session, user.id)
    user.status = "pending_approval"
    session.commit()
    with pytest.raises(InvalidOperation):
        free_playground.enter(session, user.id, confirmed=True)


@pytest.mark.parametrize("retired_flag", [None, "false", "true", "", "invalid"])
def test_entry_read_only_replay_preserves_live_pause(
    session, scheduled_owner, monkeypatch, retired_flag
):
    from reality.services import demo_data

    if retired_flag is None:
        monkeypatch.delenv("REALITY_PLAYGROUND_ENABLED", raising=False)
    else:
        monkeypatch.setenv("REALITY_PLAYGROUND_ENABLED", retired_flag)
    assert free_playground.entry_status(session, scheduled_owner.id)["enabled"] is True
    consent(session, scheduled_owner)
    before = session.scalar(select(func.count()).select_from(Tenant))
    assert free_playground.entry_status(session, scheduled_owner.id)["requested"]
    assert session.scalar(select(func.count()).select_from(Tenant)) == before
    result = free_playground.enter(session, scheduled_owner.id, confirmed=True)
    assert result["status"] == "ready"
    assert (
        session.get(PlaygroundRun, result["run_id"]).owner_user_id == scheduled_owner.id
    )
    demo_data.control(
        session,
        result["tenant_id"],
        scheduled_owner.id,
        "pause",
        demo_data.status(session, result["tenant_id"], scheduled_owner.id)["revision"],
        "pause-trial",
        confirmed=True,
    )
    again = free_playground.enter(session, scheduled_owner.id, confirmed=True)
    assert again["tenant_id"] == result["tenant_id"]
    assert (
        demo_data.status(session, result["tenant_id"], scheduled_owner.id)["state"]
        == "paused"
    )
    session.get(Tenant, result["tenant_id"]).archived_at = now()
    session.commit()
    with pytest.raises(InvalidOperation):
        free_playground.enter(session, scheduled_owner.id, confirmed=True)


def test_allowance_shared_across_companies_and_utc_reset(
    session, scheduled_owner, monkeypatch
):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "fake-no-network")
    tenant = sandbox(session, scheduled_owner)
    other = sandbox(session, scheduled_owner)
    instant = datetime(2026, 9, 14, 23, 59, tzinfo=UTC)
    monkeypatch.setattr(free_playground, "now", lambda: instant)
    for _ in range(20):
        free_playground.reserve_managed_question(session, tenant, scheduled_owner.id)
    allowance = free_playground.allowance(session, other, scheduled_owner.id)
    assert allowance["remaining"] == 0
    assert allowance["resets_at"] == "2026-09-15T00:00:00+00:00"
    with pytest.raises(InvalidOperation, match="20"):
        free_playground.reserve_managed_question(session, other, scheduled_owner.id)
    instant += timedelta(minutes=2)
    assert (
        free_playground.allowance(session, tenant, scheduled_owner.id)["remaining"]
        == 20
    )
    free_playground.reserve_managed_question(session, tenant, scheduled_owner.id)
    assert (
        free_playground.allowance(session, tenant, scheduled_owner.id)["remaining"]
        == 19
    )


def test_no_managed_provider_or_business_has_no_allowance(
    session, scheduled_owner, business, monkeypatch
):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    tenant = sandbox(session, scheduled_owner)
    assert free_playground.allowance(session, tenant, scheduled_owner.id) is None
    monkeypatch.setenv("ANTHROPIC_API_KEY", "fake-no-network")
    assert (
        free_playground.allowance(session, business.tenant.id, scheduled_owner.id)
        is None
    )


def test_exhaustion_never_calls_provider_or_stores_question(
    session, scheduled_owner, monkeypatch
):
    from reality.agent import mcp_chat
    from reality.db.core import ChatMessage
    from reality.services.core import create_chat_session, send_chat_message

    monkeypatch.setenv("ANTHROPIC_API_KEY", "fake-no-network")
    tenant = sandbox(session, scheduled_owner)
    conversation = create_chat_session(session, tenant)
    for _ in range(20):
        free_playground.reserve_managed_question(session, tenant, scheduled_owner.id)

    def forbidden(**kwargs):
        pytest.fail("Exhausted request reached provider")

    monkeypatch.setattr(mcp_chat, "reply_via_anthropic_tools", forbidden)
    with pytest.raises(InvalidOperation):
        send_chat_message(
            session,
            tenant,
            conversation.id,
            "Show orders",
            actor_user_id=scheduled_owner.id,
        )
    assert not session.scalar(
        select(ChatMessage).where(ChatMessage.tenant_id == tenant)
    )


def test_concurrent_final_slot_is_account_atomic(scheduled_database, monkeypatch):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier
    from types import SimpleNamespace

    _, factory, _, actor = scheduled_database
    monkeypatch.setenv("ANTHROPIC_API_KEY", "fake-no-network")
    with factory() as db:
        tenant = sandbox(db, SimpleNamespace(id=actor))
        for _ in range(19):
            free_playground.reserve_managed_question(db, tenant, actor)
    barrier = Barrier(2)

    def reserve():
        with factory() as db:
            barrier.wait(timeout=10)
            try:
                free_playground.reserve_managed_question(db, tenant, actor)
                return "accepted"
            except InvalidOperation:
                return "limited"

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(lambda _: reserve(), range(2)))
    assert sorted(outcomes) == ["accepted", "limited"]
    with factory() as db:
        assert free_playground.allowance(db, tenant, actor)["used"] == 20


def test_own_provider_exempt_but_companion_still_uses_managed_allowance(
    session, scheduled_owner, monkeypatch
):
    from reality.db.core import AISettings

    monkeypatch.setenv("ANTHROPIC_API_KEY", "fake-no-network")
    tenant = sandbox(session, scheduled_owner)
    session.add(
        AISettings(
            tenant_id=tenant, provider="anthropic", encrypted_api_key="opaque-test-key"
        )
    )
    session.commit()
    assert free_playground.allowance(session, tenant, scheduled_owner.id) is None
    free_playground.reserve_managed_question(
        session, tenant, scheduled_owner.id, companion=True
    )
    assert free_playground._allowance(session, scheduled_owner.id)["used"] == 1


def test_failed_entry_retries_same_receipt(session, scheduled_owner, monkeypatch):
    from reality.services import demo_profile

    consent(session, scheduled_owner)
    original = demo_profile.seed_profile

    def fail(*args, **kwargs):
        raise RuntimeError("test initialization failure")

    monkeypatch.setattr(demo_profile, "seed_profile", fail)
    failed = free_playground.enter(session, scheduled_owner.id, confirmed=True)
    assert failed["status"] != "ready"
    monkeypatch.setattr(demo_profile, "seed_profile", original)
    ready = free_playground.enter(session, scheduled_owner.id, confirmed=True)
    assert ready["status"] == "ready"
    assert ready["tenant_id"] == failed["tenant_id"]
    assert ready["run_id"] == failed["run_id"]


def test_signup_records_only_explicit_trial_request(session, business, monkeypatch):
    from reality.db.core import AppUser
    from reality.web import auth

    monkeypatch.setenv("REALITY_PUBLIC_SIGNUP_ENABLED", "true")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "fake-no-network")
    monkeypatch.setattr(auth, "issue_code", lambda *_: "123456")
    for requested in [False, True]:
        email = f"{uid('signup')}@example.test"
        auth.signup(
            auth.SignupBody(
                email=email,
                password="long-test-password",
                accepted_terms=True,
                playground=requested,
            ),
            session,
        )
        user = session.scalar(select(AppUser).where(AppUser.email == email))
        assert free_playground.entry_status(session, user.id)["requested"] is requested
        assert not free_playground.entry_status(session, user.id)["eligible"]
        # Omitting demo consent cannot opt out of the free account allowance.
        assert (
            free_playground.allowance(session, business.tenant.id, user.id)["remaining"]
            == 20
        )


def test_dispatched_provider_failure_counts_once(session, scheduled_owner, monkeypatch):
    from reality.agent import mcp_chat
    from reality.services.core import create_chat_session, send_chat_message

    monkeypatch.setenv("ANTHROPIC_API_KEY", "fake-no-network")
    tenant = sandbox(session, scheduled_owner)
    conversation = create_chat_session(session, tenant)
    calls = []

    async def fail(**kwargs):
        calls.append(kwargs["tenant_id"])
        raise RuntimeError("test provider outage")

    monkeypatch.setattr(mcp_chat, "reply_via_anthropic_tools", fail)
    _, reply = send_chat_message(
        session, tenant, conversation.id, "Show stock", actor_user_id=scheduled_owner.id
    )
    assert "could not answer" in reply.content
    assert calls == [tenant]
    assert free_playground.allowance(session, tenant, scheduled_owner.id)["used"] == 1


def test_trial_account_cannot_bypass_allowance_in_ordinary_company(
    session, scheduled_owner, business, monkeypatch
):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "fake-no-network")
    consent(session, scheduled_owner)
    tenant = sandbox(session, scheduled_owner)
    for _ in range(20):
        free_playground.reserve_managed_question(session, tenant, scheduled_owner.id)
    assert (
        free_playground.allowance(session, business.tenant.id, scheduled_owner.id)[
            "remaining"
        ]
        == 0
    )
    with pytest.raises(InvalidOperation):
        free_playground.reserve_managed_question(
            session, business.tenant.id, scheduled_owner.id
        )
