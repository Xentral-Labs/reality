from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session as OrmSession

from reality.db.core import (
    AccessApplication,
    AppUser,
    CompanyInvitation,
    InvitationDelivery,
    SecurityAuditEvent,
    Tenant,
    TenantMembership,
    now,
    uid,
)
from reality.services.core import Conflict, InvalidOperation, NotFound
from reality.services.notifications import enqueue_invitation_delivery, token_digest
from reality.services.tenant_policy import require_business_operation

INVITATION_LIFETIME = timedelta(days=7)
INVITE_WINDOW = timedelta(hours=24)
RESEND_COOLDOWN = timedelta(seconds=60)


@dataclass(frozen=True)
class Principal:
    user_id: str
    is_platform_admin: bool = False


def normalize_email(value: str) -> str:
    normalized = value.strip().casefold()
    if (
        len(normalized) > 320
        or "@" not in normalized
        or normalized.startswith("@")
        or normalized.endswith("@")
        or "." not in normalized.rsplit("@", 1)[1]
    ):
        raise InvalidOperation("Enter a valid email address.")
    return normalized


def _tenant(session: OrmSession, tenant_id: str, *, lock: bool = False) -> Tenant:
    statement = select(Tenant).where(Tenant.id == tenant_id)
    if lock:
        statement = statement.with_for_update()
    tenant = session.scalar(statement)
    if tenant is None:
        raise NotFound("Company not found.")
    return tenant


def _active_membership(
    session: OrmSession, tenant_id: str, user_id: str
) -> TenantMembership | None:
    return session.scalar(
        select(TenantMembership).where(
            TenantMembership.tenant_id == tenant_id,
            TenantMembership.user_id == user_id,
            TenantMembership.status == "active",
        )
    )


def require_owner(
    session: OrmSession, tenant_id: str, principal: Principal
) -> TenantMembership:
    _tenant(session, tenant_id)
    membership = _active_membership(session, tenant_id, principal.user_id)
    if membership is None:
        raise NotFound("Company not found.")
    if membership.role != "owner":
        raise InvalidOperation("Active company owner access required.")
    return membership


def _audit(
    session: OrmSession,
    tenant_id: str,
    event_type: str,
    subject_type: str,
    subject_id: str,
    outcome: str,
    *,
    actor_user_id: str | None,
    user_id: str | None = None,
    detail: dict[str, str | int] | None = None,
) -> SecurityAuditEvent:
    event = SecurityAuditEvent(
        id=uid("sec"),
        tenant_id=tenant_id,
        user_id=user_id,
        actor_user_id=actor_user_id,
        event_type=event_type,
        subject_type=subject_type,
        subject_id=subject_id,
        outcome=outcome,
        detail=json.dumps(detail or {}, sort_keys=True, separators=(",", ":")),
    )
    session.add(event)
    return event


def _expire_elapsed(session: OrmSession, tenant_id: str) -> None:
    timestamp = now()
    for invitation in session.scalars(
        select(CompanyInvitation).where(
            CompanyInvitation.tenant_id == tenant_id,
            CompanyInvitation.status == "pending",
            CompanyInvitation.expires_at <= timestamp,
        )
    ):
        invitation.status = "expired"
        invitation.token_hash = None
        invitation.terminal_at = timestamp
        invitation.updated_at = timestamp
        _audit(
            session,
            tenant_id,
            "invitation.expired",
            "company_invitation",
            invitation.id,
            "expired",
            actor_user_id=None,
        )


def create_invitation(
    session: OrmSession,
    tenant_id: str,
    principal: Principal,
    email: str,
    *,
    locale: str = "en",
) -> CompanyInvitation | None:
    require_business_operation(session, tenant_id, "invitation_create")
    tenant = _tenant(session, tenant_id, lock=True)
    require_owner(session, tenant_id, principal)
    if tenant.archived_at is not None:
        raise Conflict("Archived companies cannot change membership.")
    normalized = normalize_email(email)
    _expire_elapsed(session, tenant_id)
    existing = session.scalar(
        select(CompanyInvitation).where(
            CompanyInvitation.tenant_id == tenant_id,
            CompanyInvitation.normalized_email == normalized,
            CompanyInvitation.status == "pending",
        )
    )
    account = session.scalar(select(AppUser).where(AppUser.email == normalized))
    if existing is not None or (
        account is not None
        and _active_membership(session, tenant_id, account.id) is not None
    ):
        return existing
    count = session.scalar(
        select(func.count(CompanyInvitation.id)).where(
            CompanyInvitation.tenant_id == tenant_id,
            CompanyInvitation.created_at > now() - INVITE_WINDOW,
        )
    )
    if (count or 0) >= 20:
        raise Conflict("Invitation creation rate limit reached.")
    timestamp = now()
    invitation = CompanyInvitation(
        id=uid("inv"),
        tenant_id=tenant_id,
        normalized_email=normalized,
        invited_by_user_id=principal.user_id,
        expires_at=timestamp + INVITATION_LIFETIME,
        created_at=timestamp,
        updated_at=timestamp,
    )
    session.add(invitation)
    session.flush()
    enqueue_invitation_delivery(session, invitation, locale=locale)
    _audit(
        session,
        tenant_id,
        "invitation.created",
        "company_invitation",
        invitation.id,
        "pending",
        actor_user_id=principal.user_id,
    )
    return invitation


def inspect_invitation(session: OrmSession, token: str) -> dict[str, object]:
    invitation = session.scalar(
        select(CompanyInvitation).where(
            CompanyInvitation.token_hash == token_digest(token)
        )
    )
    if invitation is None:
        return {"status": "unavailable"}
    tenant = session.get(Tenant, invitation.tenant_id)
    if (
        tenant is None
        or tenant.archived_at is not None
        or invitation.status != "pending"
        or invitation.expires_at <= now()
    ):
        return {"status": "unavailable"}
    return {
        "status": "pending",
        "company_name": tenant.name,
        "email": invitation.normalized_email,
        "expires_at": invitation.expires_at,
    }


def validate_invitation_recipient(
    session: OrmSession, token: str, email: str
) -> CompanyInvitation:
    invitation = session.scalar(
        select(CompanyInvitation).where(
            CompanyInvitation.token_hash == token_digest(token)
        )
    )
    if invitation is None:
        raise NotFound("Invitation not found.")
    tenant = session.get(Tenant, invitation.tenant_id)
    if (
        tenant is None
        or tenant.archived_at is not None
        or invitation.status != "pending"
        or invitation.expires_at <= now()
        or invitation.normalized_email != normalize_email(email)
    ):
        raise NotFound("Invitation not found.")
    return invitation


def accept_invitation(
    session: OrmSession, token: str, user_id: str
) -> TenantMembership:
    token_hash = token_digest(token)
    invitation_identity = session.execute(
        select(CompanyInvitation.id, CompanyInvitation.tenant_id).where(
            CompanyInvitation.token_hash == token_hash
        )
    ).one_or_none()
    if invitation_identity is None:
        raise NotFound("Invitation not found.")
    invitation_id, tenant_id = invitation_identity
    require_business_operation(session, tenant_id, "invitation_accept")
    tenant = _tenant(session, tenant_id, lock=True)
    invitation = session.scalar(
        select(CompanyInvitation)
        .where(
            CompanyInvitation.id == invitation_id,
            CompanyInvitation.tenant_id == tenant_id,
        )
        .with_for_update()
    )
    if invitation is None or invitation.token_hash != token_hash:
        raise NotFound("Invitation not found.")
    user = session.get(AppUser, user_id)
    if user is None:
        raise NotFound("Invitation not found.")
    if invitation.status == "accepted" and invitation.accepted_by_user_id == user.id:
        existing_membership = session.scalar(
            select(TenantMembership).where(
                TenantMembership.tenant_id == tenant.id,
                TenantMembership.user_id == user.id,
                TenantMembership.status == "active",
            )
        )
        if existing_membership is not None:
            return existing_membership
    if (
        tenant.archived_at is not None
        or invitation.status != "pending"
        or invitation.expires_at <= now()
    ):
        raise Conflict("Invitation is no longer available.")
    if (
        user.email_verified_at is None
        or normalize_email(user.email) != invitation.normalized_email
    ):
        raise InvalidOperation("Invitation requires the matching verified email.")
    if user.status in {"suspended", "rejected"}:
        raise InvalidOperation("This account cannot accept invitations.")
    membership = session.scalar(
        select(TenantMembership)
        .where(
            TenantMembership.tenant_id == tenant.id,
            TenantMembership.user_id == user.id,
        )
        .with_for_update()
    )
    outcome = "reactivated"
    if membership is None:
        membership = TenantMembership(
            id=uid("tmb"),
            tenant_id=tenant.id,
            user_id=user.id,
            role="member",
            status="active",
        )
        session.add(membership)
        outcome = "accepted"
    else:
        membership.status = "active"
    timestamp = now()
    invitation.status = "accepted"
    invitation.accepted_by_user_id = user.id
    invitation.accepted_at = timestamp
    invitation.terminal_at = timestamp
    invitation.updated_at = timestamp
    user.status = "active"
    application = session.scalar(
        select(AccessApplication).where(AccessApplication.user_id == user.id)
    )
    if application is not None and application.status == "pending":
        application.status = "approved"
        application.review_note = "admitted through company invitation"
        application.reviewed_at = timestamp
    _audit(
        session,
        tenant.id,
        "invitation.accepted",
        "company_invitation",
        invitation.id,
        outcome,
        actor_user_id=user.id,
        user_id=user.id,
    )
    return membership


def access_summary(
    session: OrmSession, tenant_id: str, principal: Principal
) -> dict[str, list[dict[str, object]]]:
    require_owner(session, tenant_id, principal)
    _expire_elapsed(session, tenant_id)
    memberships = session.execute(
        select(TenantMembership, AppUser)
        .join(AppUser, AppUser.id == TenantMembership.user_id)
        .where(
            TenantMembership.tenant_id == tenant_id,
            TenantMembership.status == "active",
        )
        .order_by(AppUser.email)
        .limit(500)
    ).all()
    invitations = list(
        session.scalars(
            select(CompanyInvitation)
            .where(
                CompanyInvitation.tenant_id == tenant_id,
                CompanyInvitation.status.in_(("pending", "expired")),
            )
            .order_by(CompanyInvitation.created_at.desc())
            .limit(500)
        )
    )
    invitation_ids = [invitation.id for invitation in invitations]
    deliveries = (
        list(
            session.scalars(
                select(InvitationDelivery).where(
                    InvitationDelivery.tenant_id == tenant_id,
                    InvitationDelivery.invitation_id.in_(invitation_ids),
                )
            )
        )
        if invitation_ids
        else []
    )
    latest_delivery = {
        delivery.invitation_id: delivery
        for delivery in sorted(deliveries, key=lambda row: row.generation)
    }
    return {
        "members": [
            {
                "id": membership.id,
                "email": user.email,
                "display_name": user.display_name,
                "role": membership.role,
            }
            for membership, user in memberships
        ],
        "invitations": [
            {
                "id": invitation.id,
                "email": invitation.normalized_email,
                "status": invitation.status,
                "delivery_status": latest_delivery.get(invitation.id).status
                if invitation.id in latest_delivery
                else "pending",
                "expires_at": invitation.expires_at,
            }
            for invitation in invitations
        ],
    }


def revoke_invitation(
    session: OrmSession, tenant_id: str, principal: Principal, invitation_id: str
) -> None:
    require_business_operation(session, tenant_id, "invitation_revoke")
    tenant = _tenant(session, tenant_id, lock=True)
    require_owner(session, tenant_id, principal)
    if tenant.archived_at is not None:
        raise Conflict("Archived companies cannot change membership.")
    invitation = session.scalar(
        select(CompanyInvitation)
        .where(
            CompanyInvitation.tenant_id == tenant_id,
            CompanyInvitation.id == invitation_id,
        )
        .with_for_update()
    )
    if invitation is None:
        raise NotFound("Invitation not found.")
    if invitation.status != "pending":
        raise Conflict("Invitation is no longer pending.")
    timestamp = now()
    invitation.status = "revoked"
    invitation.token_hash = None
    invitation.revoked_at = timestamp
    invitation.terminal_at = timestamp
    invitation.updated_at = timestamp
    _audit(
        session,
        tenant_id,
        "invitation.revoked",
        "company_invitation",
        invitation.id,
        "revoked",
        actor_user_id=principal.user_id,
    )


def resend_invitation(
    session: OrmSession,
    tenant_id: str,
    principal: Principal,
    invitation_id: str,
    *,
    locale: str = "en",
) -> CompanyInvitation:
    require_business_operation(session, tenant_id, "invitation_resend")
    tenant = _tenant(session, tenant_id, lock=True)
    require_owner(session, tenant_id, principal)
    if tenant.archived_at is not None:
        raise Conflict("Archived companies cannot change membership.")
    _expire_elapsed(session, tenant_id)
    invitation = session.scalar(
        select(CompanyInvitation)
        .where(
            CompanyInvitation.tenant_id == tenant_id,
            CompanyInvitation.id == invitation_id,
        )
        .with_for_update()
    )
    if invitation is None:
        raise NotFound("Invitation not found.")
    if invitation.status not in {"pending", "expired"}:
        raise Conflict("Invitation cannot be resent.")
    deliveries = list(
        session.scalars(
            select(InvitationDelivery)
            .where(
                InvitationDelivery.tenant_id == tenant_id,
                InvitationDelivery.invitation_id == invitation.id,
                InvitationDelivery.created_at > now() - INVITE_WINDOW,
            )
            .order_by(InvitationDelivery.created_at.desc())
        )
    )
    resend_count = sum(delivery.generation > 1 for delivery in deliveries)
    if resend_count >= 5:
        raise Conflict("Invitation resend rate limit reached.")
    if deliveries and deliveries[0].created_at > now() - RESEND_COOLDOWN:
        raise Conflict("Please wait before resending this invitation.")
    timestamp = now()
    invitation.status = "pending"
    invitation.token_generation += 1
    invitation.token_hash = None
    invitation.expires_at = timestamp + INVITATION_LIFETIME
    invitation.terminal_at = None
    invitation.accepted_at = None
    invitation.accepted_by_user_id = None
    invitation.revoked_at = None
    invitation.updated_at = timestamp
    enqueue_invitation_delivery(session, invitation, locale=locale)
    _audit(
        session,
        tenant_id,
        "invitation.resent",
        "company_invitation",
        invitation.id,
        "pending",
        actor_user_id=principal.user_id,
        detail={"generation": invitation.token_generation},
    )
    return invitation


def remove_member(
    session: OrmSession,
    tenant_id: str,
    principal: Principal,
    membership_id: str,
) -> None:
    require_business_operation(session, tenant_id, "membership_remove")
    tenant = _tenant(session, tenant_id, lock=True)
    if tenant.archived_at is not None:
        raise Conflict("Archived companies cannot change membership.")
    if not principal.is_platform_admin:
        require_owner(session, tenant_id, principal)
    membership = session.scalar(
        select(TenantMembership)
        .where(
            TenantMembership.tenant_id == tenant_id,
            TenantMembership.id == membership_id,
        )
        .with_for_update()
    )
    if membership is None:
        raise NotFound("Membership not found.")
    if membership.role == "owner":
        raise InvalidOperation("Owners cannot be removed by this operation.")
    if membership.status != "active":
        raise Conflict("Membership is not active.")
    membership.status = "removed"
    _audit(
        session,
        tenant_id,
        "membership.removed",
        "tenant_membership",
        membership.id,
        "removed",
        actor_user_id=principal.user_id,
        user_id=membership.user_id,
    )
