import logging
from datetime import timedelta

from sqlalchemy import select

from reality.db.core import (
    AppUser,
    CompanyInvitation,
    InvitationDelivery,
    SecurityAuditEvent,
    TenantMembership,
    now,
    uid,
)
from reality.services.core import create_tenant
from reality.services.memberships import (
    Principal,
    create_invitation,
    inspect_invitation,
    revoke_invitation,
)
from reality.services.notifications import (
    claim_due_delivery,
    cleanup_terminal_invitations,
    deliver_next_invitation,
)
from reality.web import email as email_module


def test_company_invitation_email_escapes_dynamic_content_and_uses_fragment(
    monkeypatch,
):
    sent: list[dict[str, str]] = []
    monkeypatch.setattr(
        email_module, "send_email", lambda **message: sent.append(message)
    )
    monkeypatch.setenv("APP_URL", "https://app.example.test")

    email_module.send_company_invitation_email(
        "recipient@example.com",
        '<script>alert("company")</script>\r\nBcc: attacker@example.com',
        "clear-secret-token",
        locale="unknown",
    )

    assert len(sent) == 1
    message = sent[0]
    assert "<script>" not in message["html_body"]
    assert "&lt;script&gt;" in message["html_body"]
    assert "\r" not in message["subject"] and "\n" not in message["subject"]
    assert "/invitation#token=clear-secret-token" in message["text"]
    assert "/invitation?token=" not in message["text"]
    assert "support@xentral.com" in message["text"]
    assert "mailto:support@xentral.com" in message["html_body"]
    assert message["subject"].startswith("Join ")


def test_disabled_email_provider_never_logs_invitation_content_or_token(
    monkeypatch, caplog
):
    monkeypatch.setenv("REALITY_EMAIL_PROVIDER", "log")
    caplog.set_level(logging.INFO, logger=email_module.__name__)

    email_module.send_company_invitation_email(
        "log-recipient@example.com",
        "Secret Company",
        "clear-secret-token",
        locale="de",
    )

    assert "clear-secret-token" not in caplog.text
    assert "#token=" not in caplog.text
    assert "Secret Company" not in caplog.text


def _queued_invitation(session, suffix: str = ""):
    tenant = create_tenant(session, f"Delivery Company {suffix}".strip())
    owner = AppUser(
        id=uid("usr"),
        email=f"delivery-owner{suffix}@example.com",
        password_hash="unused",
        status="active",
        email_verified_at=now(),
    )
    session.add(owner)
    session.flush()
    session.add(
        TenantMembership(
            id=uid("tmb"),
            tenant_id=tenant.id,
            user_id=owner.id,
            role="owner",
            status="active",
        )
    )
    session.flush()
    invitation = create_invitation(
        session, tenant.id, Principal(owner.id), f"recipient{suffix}@example.com"
    )
    delivery = session.scalar(
        select(InvitationDelivery).where(
            InvitationDelivery.invitation_id == invitation.id
        )
    )
    return tenant, owner, invitation, delivery


def test_delivery_retry_rotates_clear_token_and_records_sanitized_outcome(session):
    tenant, _, invitation, delivery = _queued_invitation(session)
    clear_tokens: list[str] = []

    def failing_sender(_email, _company, token, **_kwargs):
        clear_tokens.append(token)
        raise RuntimeError("secret provider diagnostic")

    assert deliver_next_invitation(session, failing_sender)
    assert delivery.status == "retry"
    assert delivery.last_error_code == "RuntimeError"
    assert "secret provider diagnostic" not in delivery.last_error_code
    first_hash = invitation.token_hash
    delivery.next_attempt_at = now() - timedelta(seconds=1)
    assert deliver_next_invitation(session, failing_sender)
    assert invitation.token_hash != first_hash
    assert len(clear_tokens) == 2
    audit = session.scalar(
        select(SecurityAuditEvent)
        .where(
            SecurityAuditEvent.tenant_id == tenant.id,
            SecurityAuditEvent.subject_id == delivery.id,
        )
        .order_by(SecurityAuditEvent.occurred_at.desc())
    )
    assert audit.outcome == "retry"
    assert all(token not in audit.detail for token in clear_tokens)


def test_provider_timeout_may_duplicate_mail_but_only_latest_link_remains_valid(
    session,
):
    _, _, invitation, delivery = _queued_invitation(session)
    sent_tokens: list[str] = []

    def ambiguous_sender(_email, _company, token, **_kwargs):
        sent_tokens.append(token)
        if len(sent_tokens) == 1:
            raise TimeoutError("provider accepted before timeout")

    assert deliver_next_invitation(session, ambiguous_sender)
    assert delivery.status == "retry"
    delivery.next_attempt_at = now() - timedelta(seconds=1)
    assert deliver_next_invitation(session, ambiguous_sender)

    assert delivery.status == "delivered"
    assert len(sent_tokens) == 2
    assert sent_tokens[0] != sent_tokens[1]
    assert inspect_invitation(session, sent_tokens[0]) == {"status": "unavailable"}
    assert inspect_invitation(session, sent_tokens[1])["status"] == "pending"
    assert invitation.token_hash is not None


def test_delivery_intent_rolls_back_atomically_with_invitation(session):
    tenant, owner = _queued_invitation(session)[:2]
    invitation_count = session.query(CompanyInvitation).count()
    delivery_count = session.query(InvitationDelivery).count()

    transaction = session.begin_nested()
    create_invitation(
        session,
        tenant.id,
        Principal(owner.id),
        "rollback-recipient@example.com",
    )
    transaction.rollback()

    assert session.query(CompanyInvitation).count() == invitation_count
    assert session.query(InvitationDelivery).count() == delivery_count


def test_worker_outage_preserves_pending_intent_and_failure_becomes_terminal_after_day(
    session,
):
    _, _, _, delivery = _queued_invitation(session)
    delivery_id = delivery.id
    session.commit()
    session.expire_all()
    durable = session.get(InvitationDelivery, delivery_id)
    assert durable is not None and durable.status == "pending"

    durable.created_at = now() - timedelta(hours=25)
    assert deliver_next_invitation(
        session,
        lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("raw detail")),
    )
    assert durable.status == "failed"
    assert durable.last_error_code == "RuntimeError"


def test_expired_worker_lease_is_reclaimable_and_old_terminal_rows_are_cleaned(session):
    tenant, owner, invitation, delivery = _queued_invitation(session)
    delivery.status = "processing"
    delivery.claimed_at = now() - timedelta(minutes=6)
    assert claim_due_delivery(session).id == delivery.id

    revoke_invitation(session, tenant.id, Principal(owner.id), invitation.id)
    invitation.terminal_at = now() - timedelta(days=91)
    audit_id = session.scalar(
        select(SecurityAuditEvent.id).where(
            SecurityAuditEvent.tenant_id == tenant.id,
            SecurityAuditEvent.subject_id == invitation.id,
        )
    )
    assert cleanup_terminal_invitations(session, tenant_id=tenant.id) == 1
    assert session.get(type(invitation), invitation.id) is None
    assert session.get(InvitationDelivery, delivery.id) is None
    assert session.get(SecurityAuditEvent, audit_id) is not None

    _, _, recent_terminal, _ = _queued_invitation(session, "-recent")
    recent_terminal.status = "revoked"
    recent_terminal.terminal_at = now() - timedelta(days=89)
    _, _, old_pending, _ = _queued_invitation(session, "-pending")
    old_pending.created_at = now() - timedelta(days=100)
    assert cleanup_terminal_invitations(session, tenant_id=tenant.id) == 0
    assert session.get(CompanyInvitation, recent_terminal.id) is not None
    assert session.get(CompanyInvitation, old_pending.id) is not None
