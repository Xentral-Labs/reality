from datetime import timedelta

import pytest
from sqlalchemy import func, select

from reality.db.core import (
    AccessAdmissionCounter,
    AccessApplication,
    AppUser,
    CompanyInvitation,
    InvitationDelivery,
    SecurityAuditEvent,
    TenantMembership,
    now,
    uid,
)
from reality.services.core import Conflict, InvalidOperation, create_tenant
from reality.services.memberships import (
    Principal,
    accept_invitation,
    access_summary,
    create_invitation,
    inspect_invitation,
    normalize_email,
    remove_member,
    resend_invitation,
    revoke_invitation,
)
from reality.services.notifications import issue_delivery_token


def _user(session, email: str, *, status: str = "active") -> AppUser:
    user = AppUser(
        id=uid("usr"),
        email=email,
        password_hash="test",
        status=status,
        email_verified_at=now(),
    )
    session.add(user)
    session.flush()
    return user


def _company_with_owner(session, suffix: str = ""):
    tenant = create_tenant(session, f"Invitation Test Company {suffix}".strip())
    owner = _user(session, f"owner{suffix}@example.com")
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
    return tenant, owner


def test_only_active_owner_can_create_invitation_without_pregranting_access(session):
    tenant, owner = _company_with_owner(session)
    member = _user(session, "member@example.com")
    session.add(
        TenantMembership(
            id=uid("tmb"),
            tenant_id=tenant.id,
            user_id=member.id,
            role="member",
            status="active",
        )
    )
    session.flush()

    with pytest.raises(InvalidOperation, match="owner"):
        create_invitation(
            session, tenant.id, Principal(member.id), "target@example.com"
        )

    invitation = create_invitation(
        session, tenant.id, Principal(owner.id), " Target@Example.COM "
    )
    assert invitation is not None
    assert invitation.normalized_email == "target@example.com"
    assert invitation.token_hash is None
    assert (
        session.scalar(
            select(func.count(TenantMembership.id)).where(
                TenantMembership.tenant_id == tenant.id,
                TenantMembership.user_id != owner.id,
            )
        )
        == 1
    )


def test_existing_and_unknown_account_create_the_same_pending_state(session):
    tenant, owner = _company_with_owner(session)
    existing = _user(session, "existing@example.com")

    first = create_invitation(session, tenant.id, Principal(owner.id), existing.email)
    second = create_invitation(
        session, tenant.id, Principal(owner.id), "unknown@example.com"
    )

    assert first is not None and second is not None
    assert first.status == second.status == "pending"
    assert first.accepted_by_user_id is second.accepted_by_user_id is None
    assert (
        session.scalar(
            select(func.count(InvitationDelivery.id)).where(
                InvitationDelivery.tenant_id == tenant.id
            )
        )
        == 2
    )


def test_matching_verified_account_must_explicitly_accept(session):
    tenant, owner = _company_with_owner(session)
    recipient = _user(session, "recipient@example.com", status="pending_approval")
    invitation = create_invitation(
        session, tenant.id, Principal(owner.id), recipient.email
    )
    assert invitation is not None
    delivery = session.scalar(
        select(InvitationDelivery).where(
            InvitationDelivery.invitation_id == invitation.id
        )
    )
    assert delivery is not None
    _, _, token = issue_delivery_token(session, tenant.id, delivery.id)

    membership = accept_invitation(session, token, recipient.id)

    assert membership.role == "member"
    assert membership.status == "active"
    assert recipient.status == "active"
    assert invitation.status == "accepted"
    assert invitation.terminal_at is not None
    assert (
        session.scalar(
            select(func.count(SecurityAuditEvent.id)).where(
                SecurityAuditEvent.tenant_id == tenant.id,
                SecurityAuditEvent.event_type == "invitation.accepted",
            )
        )
        == 1
    )
    assert accept_invitation(session, token, recipient.id).id == membership.id


def test_acceptance_approves_existing_application_without_claiming_admission_slot(
    session,
):
    tenant, owner = _company_with_owner(session)
    recipient = _user(session, "applicant@example.com", status="pending_approval")
    application = AccessApplication(
        id=uid("apl"), user_id=recipient.id, status="pending"
    )
    counter = AccessAdmissionCounter(id="automatic", used_slots=7)
    session.add_all([application, counter])
    invitation = create_invitation(
        session, tenant.id, Principal(owner.id), recipient.email
    )
    delivery = session.scalar(
        select(InvitationDelivery).where(
            InvitationDelivery.invitation_id == invitation.id
        )
    )
    _, _, token = issue_delivery_token(session, tenant.id, delivery.id)

    accept_invitation(session, token, recipient.id)

    assert application.status == "approved"
    assert application.review_note == "admitted through company invitation"
    assert counter.used_slots == 7
    assert (
        session.scalar(
            select(func.count(AccessApplication.id)).where(
                AccessApplication.user_id == recipient.id
            )
        )
        == 1
    )


def test_wrong_email_and_blocked_account_cannot_accept(session):
    tenant, owner = _company_with_owner(session)
    invitation = create_invitation(
        session, tenant.id, Principal(owner.id), "invited@example.com"
    )
    delivery = session.scalar(
        select(InvitationDelivery).where(
            InvitationDelivery.invitation_id == invitation.id
        )
    )
    _, _, token = issue_delivery_token(session, tenant.id, delivery.id)
    wrong = _user(session, "wrong@example.com")

    with pytest.raises(InvalidOperation, match="matching verified"):
        accept_invitation(session, token, wrong.id)

    blocked = _user(session, "invited@example.com", status="suspended")
    with pytest.raises(InvalidOperation, match="cannot accept"):
        accept_invitation(session, token, blocked.id)


def test_removed_member_is_reactivated_with_the_same_membership_identity(session):
    tenant, owner = _company_with_owner(session)
    recipient = _user(session, "returning@example.com")
    membership = TenantMembership(
        id=uid("tmb"),
        tenant_id=tenant.id,
        user_id=recipient.id,
        role="member",
        status="active",
    )
    session.add(membership)
    session.flush()
    original_id = membership.id
    remove_member(session, tenant.id, Principal(owner.id), membership.id)
    invitation = create_invitation(
        session, tenant.id, Principal(owner.id), recipient.email
    )
    delivery = session.scalar(
        select(InvitationDelivery).where(
            InvitationDelivery.invitation_id == invitation.id
        )
    )
    _, _, token = issue_delivery_token(session, tenant.id, delivery.id)

    reactivated = accept_invitation(session, token, recipient.id)

    assert reactivated.id == original_id
    assert reactivated.status == "active"
    events = list(
        session.scalars(
            select(SecurityAuditEvent)
            .where(
                SecurityAuditEvent.tenant_id == tenant.id,
                SecurityAuditEvent.event_type.in_(
                    ("membership.removed", "invitation.accepted")
                ),
            )
            .order_by(SecurityAuditEvent.occurred_at)
        )
    )
    removed, accepted = events
    assert removed.subject_type == "tenant_membership"
    assert removed.subject_id == original_id
    assert removed.actor_user_id == owner.id
    assert removed.user_id == recipient.id
    assert removed.outcome == "removed"
    assert accepted.subject_type == "company_invitation"
    assert accepted.subject_id == invitation.id
    assert accepted.actor_user_id == recipient.id
    assert accepted.user_id == recipient.id
    assert accepted.outcome == "reactivated"
    assert all(event.occurred_at.utcoffset() == timedelta(0) for event in events)
    assert all("token" not in event.detail.casefold() for event in events)
    assert all(recipient.email not in event.detail for event in events)


def test_removal_authorization_owner_protection_archive_and_inviter_loss(session):
    tenant, owner = _company_with_owner(session)
    member = _user(session, "authorization-member@example.com")
    membership = TenantMembership(
        id=uid("tmb"),
        tenant_id=tenant.id,
        user_id=member.id,
        role="member",
        status="active",
    )
    session.add(membership)
    session.flush()

    with pytest.raises(InvalidOperation, match="owner"):
        remove_member(session, tenant.id, Principal(member.id), membership.id)
    owner_membership = session.scalar(
        select(TenantMembership).where(
            TenantMembership.tenant_id == tenant.id,
            TenantMembership.user_id == owner.id,
        )
    )
    with pytest.raises(InvalidOperation, match="Owners cannot"):
        remove_member(session, tenant.id, Principal(owner.id), owner_membership.id)

    platform_admin = _user(session, "platform-admin@example.com")
    platform_admin.is_platform_admin = True
    remove_member(
        session,
        tenant.id,
        Principal(platform_admin.id, is_platform_admin=True),
        membership.id,
    )
    assert membership.status == "removed"

    invitation = create_invitation(
        session, tenant.id, Principal(owner.id), "inviter-loss@example.com"
    )
    delivery = session.scalar(
        select(InvitationDelivery).where(
            InvitationDelivery.invitation_id == invitation.id
        )
    )
    _, _, token = issue_delivery_token(session, tenant.id, delivery.id)
    recipient = _user(session, "inviter-loss@example.com")
    replacement_owner = _user(session, "replacement-owner@example.com")
    owner_membership.status = "removed"
    session.add(
        TenantMembership(
            id=uid("tmb"),
            tenant_id=tenant.id,
            user_id=replacement_owner.id,
            role="owner",
            status="active",
        )
    )
    assert accept_invitation(session, token, recipient.id).status == "active"

    archived, archived_owner = _company_with_owner(session, "-archived")
    archived_invitation = create_invitation(
        session,
        archived.id,
        Principal(archived_owner.id),
        "archived-recipient@example.com",
    )
    archived_delivery = session.scalar(
        select(InvitationDelivery).where(
            InvitationDelivery.invitation_id == archived_invitation.id
        )
    )
    _, _, archived_token = issue_delivery_token(
        session, archived.id, archived_delivery.id
    )
    archived_recipient = _user(session, "archived-recipient@example.com")
    archived_membership = TenantMembership(
        id=uid("tmb"),
        tenant_id=archived.id,
        user_id=archived_recipient.id,
        role="member",
        status="active",
    )
    session.add(archived_membership)
    session.flush()
    archived.archived_at = now()
    with pytest.raises(Conflict, match="Archived"):
        create_invitation(
            session, archived.id, Principal(archived_owner.id), "blocked@example.com"
        )
    with pytest.raises(Conflict, match="no longer available"):
        accept_invitation(session, archived_token, archived_recipient.id)
    with pytest.raises(Conflict, match="Archived"):
        resend_invitation(
            session,
            archived.id,
            Principal(archived_owner.id),
            archived_invitation.id,
        )
    with pytest.raises(Conflict, match="Archived"):
        revoke_invitation(
            session,
            archived.id,
            Principal(archived_owner.id),
            archived_invitation.id,
        )
    with pytest.raises(Conflict, match="Archived"):
        remove_member(
            session,
            archived.id,
            Principal(archived_owner.id),
            archived_membership.id,
        )


def test_normalization_does_not_infer_provider_aliases() -> None:
    assert normalize_email(" User.Name+tag@Example.COM ") == (
        "user.name+tag@example.com"
    )
    assert normalize_email("username@example.com") != normalize_email(
        "user.name+tag@example.com"
    )


def test_duplicate_invite_is_neutral_and_does_not_enqueue_again(session):
    tenant, owner = _company_with_owner(session)
    first = create_invitation(
        session, tenant.id, Principal(owner.id), "duplicate@example.com"
    )
    second = create_invitation(
        session, tenant.id, Principal(owner.id), " DUPLICATE@example.com "
    )

    assert second is first
    assert (
        session.scalar(
            select(func.count(InvitationDelivery.id)).where(
                InvitationDelivery.invitation_id == first.id
            )
        )
        == 1
    )


def test_inspect_names_the_company_and_the_invited_address_for_the_holder(session):
    tenant, owner = _company_with_owner(session, "inspect")
    invitation = create_invitation(
        session, tenant.id, Principal(owner.id), "Invited.Person@Example.com"
    )
    assert invitation is not None
    delivery = session.scalar(
        select(InvitationDelivery).where(
            InvitationDelivery.invitation_id == invitation.id
        )
    )
    _, _, token = issue_delivery_token(session, tenant.id, delivery.id)

    inspected = inspect_invitation(session, token)
    assert inspected["status"] == "pending"
    assert inspected["company_name"] == tenant.name
    assert inspected["email"] == normalize_email("Invited.Person@Example.com")

    revoke_invitation(session, tenant.id, Principal(owner.id), invitation.id)
    assert inspect_invitation(session, token) == {"status": "unavailable"}


def test_resend_enforces_cooldown_rotates_generation_and_revoke_is_terminal(session):
    tenant, owner = _company_with_owner(session)
    invitation = create_invitation(
        session, tenant.id, Principal(owner.id), "resend@example.com"
    )
    assert invitation is not None
    first_delivery = session.scalar(
        select(InvitationDelivery).where(
            InvitationDelivery.invitation_id == invitation.id
        )
    )
    _, _, old_token = issue_delivery_token(session, tenant.id, first_delivery.id)

    with pytest.raises(Conflict, match="wait"):
        resend_invitation(session, tenant.id, Principal(owner.id), invitation.id)

    first_delivery.created_at = now() - timedelta(seconds=61)
    resent = resend_invitation(session, tenant.id, Principal(owner.id), invitation.id)
    assert resent.token_generation == 2
    assert resent.token_hash is None
    assert inspect_invitation(session, old_token) == {"status": "unavailable"}

    revoke_invitation(session, tenant.id, Principal(owner.id), invitation.id)
    assert invitation.status == "revoked"
    assert invitation.terminal_at is not None


def test_expired_invitation_is_terminal_and_can_be_replaced(session):
    tenant, owner = _company_with_owner(session)
    original = create_invitation(
        session, tenant.id, Principal(owner.id), "expired@example.com"
    )
    original.expires_at = now() - timedelta(seconds=1)

    replacement = create_invitation(
        session, tenant.id, Principal(owner.id), "expired@example.com"
    )

    assert replacement is not None and replacement.id != original.id
    assert replacement.status == "pending"
    assert original.status == "expired"
    assert original.terminal_at is not None
    assert original.token_hash is None


def test_rolling_creation_and_resend_limits_recover_after_window(session):
    tenant, owner = _company_with_owner(session)
    principal = Principal(owner.id)
    invitations = [
        create_invitation(session, tenant.id, principal, f"limited-{index}@example.com")
        for index in range(20)
    ]
    with pytest.raises(Conflict, match="creation rate limit"):
        create_invitation(session, tenant.id, principal, "limited-next@example.com")

    invitations[0].created_at = now() - timedelta(hours=25)
    assert (
        create_invitation(session, tenant.id, principal, "limited-next@example.com")
        is not None
    )

    invitation = invitations[1]
    for _ in range(5):
        latest = session.scalar(
            select(InvitationDelivery)
            .where(InvitationDelivery.invitation_id == invitation.id)
            .order_by(InvitationDelivery.generation.desc())
        )
        latest.created_at = now() - timedelta(seconds=61)
        resend_invitation(session, tenant.id, principal, invitation.id)
    latest = session.scalar(
        select(InvitationDelivery)
        .where(InvitationDelivery.invitation_id == invitation.id)
        .order_by(InvitationDelivery.generation.desc())
    )
    latest.created_at = now() - timedelta(seconds=61)
    with pytest.raises(Conflict, match="resend rate limit"):
        resend_invitation(session, tenant.id, principal, invitation.id)

    for delivery in session.scalars(
        select(InvitationDelivery).where(
            InvitationDelivery.invitation_id == invitation.id,
            InvitationDelivery.generation > 1,
        )
    ):
        delivery.created_at = now() - timedelta(hours=25)
    assert resend_invitation(session, tenant.id, principal, invitation.id) is invitation


def test_access_summary_is_bounded_and_uses_latest_delivery_generation(session):
    tenant, owner = _company_with_owner(session)
    principal = Principal(owner.id)
    timestamp = now()
    invitations = [
        CompanyInvitation(
            id=uid("inv"),
            tenant_id=tenant.id,
            normalized_email=f"summary-{index:03d}@example.com",
            invited_by_user_id=owner.id,
            expires_at=timestamp + timedelta(days=7),
            created_at=timestamp + timedelta(seconds=index),
            updated_at=timestamp,
        )
        for index in range(501)
    ]
    session.add_all(invitations)
    session.flush()
    newest = invitations[-1]
    session.add_all(
        [
            InvitationDelivery(
                id=uid("dly"),
                tenant_id=tenant.id,
                invitation_id=newest.id,
                generation=1,
                status="failed",
            ),
            InvitationDelivery(
                id=uid("dly"),
                tenant_id=tenant.id,
                invitation_id=newest.id,
                generation=2,
                status="pending",
            ),
        ]
    )
    session.flush()

    summary = access_summary(session, tenant.id, principal)

    assert len(summary["invitations"]) == 500
    newest_row = next(row for row in summary["invitations"] if row["id"] == newest.id)
    assert newest_row["delivery_status"] == "pending"
