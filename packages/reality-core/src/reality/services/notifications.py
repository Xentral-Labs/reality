from __future__ import annotations

import hashlib
import json
import secrets
from datetime import timedelta

from sqlalchemy import delete, or_, select
from sqlalchemy.orm import Session as OrmSession

from reality.db.core import (
    CompanyInvitation,
    InvitationDelivery,
    SecurityAuditEvent,
    Tenant,
    now,
    uid,
)
from reality.services.core import Conflict, NotFound
from reality.services.tenant_policy import (
    PlaygroundOperationDenied,
    require_business_operation,
)


def token_digest(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def enqueue_invitation_delivery(
    session: OrmSession,
    invitation: CompanyInvitation,
    *,
    locale: str = "en",
) -> InvitationDelivery:
    require_business_operation(session, invitation.tenant_id, "invitation_enqueue")
    delivery = InvitationDelivery(
        id=uid("idl"),
        tenant_id=invitation.tenant_id,
        invitation_id=invitation.id,
        generation=invitation.token_generation,
        locale=locale if locale in {"en", "de", "nl", "es"} else "en",
        next_attempt_at=now(),
    )
    session.add(delivery)
    return delivery


def issue_delivery_token(
    session: OrmSession, tenant_id: str, delivery_id: str
) -> tuple[InvitationDelivery, CompanyInvitation, str]:
    require_business_operation(session, tenant_id, "invitation_delivery")
    delivery = session.scalar(
        select(InvitationDelivery)
        .where(
            InvitationDelivery.id == delivery_id,
            InvitationDelivery.tenant_id == tenant_id,
        )
        .with_for_update()
    )
    if delivery is None:
        raise NotFound("Invitation delivery not found.")
    invitation = session.scalar(
        select(CompanyInvitation)
        .where(
            CompanyInvitation.id == delivery.invitation_id,
            CompanyInvitation.tenant_id == tenant_id,
        )
        .with_for_update()
    )
    if invitation is None:
        raise NotFound("Invitation delivery not found.")
    if (
        delivery.generation != invitation.token_generation
        or invitation.status != "pending"
        or invitation.expires_at <= now()
    ):
        delivery.status = "failed"
        delivery.last_error_code = "stale_generation"
        raise Conflict("Invitation delivery is no longer current.")
    token = secrets.token_urlsafe(48)
    invitation.token_hash = token_digest(token)
    invitation.updated_at = now()
    delivery.status = "processing"
    delivery.claimed_at = now()
    delivery.attempt_count += 1
    delivery.attempted_at = now()
    return delivery, invitation, token


def record_delivery_result(
    delivery: InvitationDelivery,
    *,
    delivered: bool,
    provider_message_id: str | None = None,
    error_code: str | None = None,
) -> None:
    timestamp = now()
    delivery.claimed_at = None
    if delivered:
        delivery.status = "delivered"
        delivery.delivered_at = timestamp
        delivery.provider_message_id = (provider_message_id or "")[:255] or None
        delivery.last_error_code = None
        return
    if timestamp >= delivery.created_at + timedelta(hours=24):
        delivery.status = "failed"
        delivery.next_attempt_at = timestamp
    else:
        delivery.status = "retry"
        delay_minutes = min(360, 2 ** min(delivery.attempt_count, 8))
        delivery.next_attempt_at = timestamp + timedelta(minutes=delay_minutes)
    delivery.last_error_code = (error_code or "delivery_failed")[:255]


def claim_due_delivery(session: OrmSession) -> InvitationDelivery | None:
    lease_cutoff = now() - timedelta(minutes=5)
    return session.scalar(
        select(InvitationDelivery)
        .where(
            or_(
                (
                    InvitationDelivery.status.in_(("pending", "retry"))
                    & (InvitationDelivery.next_attempt_at <= now())
                ),
                (
                    (InvitationDelivery.status == "processing")
                    & (InvitationDelivery.claimed_at <= lease_cutoff)
                ),
            )
        )
        .order_by(InvitationDelivery.next_attempt_at, InvitationDelivery.created_at)
        .with_for_update(skip_locked=True)
        .limit(1)
    )


def deliver_next_invitation(
    session: OrmSession,
    sender,
) -> bool:
    delivery = claim_due_delivery(session)
    if delivery is None:
        return False
    try:
        delivery, invitation, token = issue_delivery_token(
            session, delivery.tenant_id, delivery.id
        )
        tenant = session.get(Tenant, delivery.tenant_id)
        sender(
            invitation.normalized_email,
            tenant.name,
            token,
            locale=delivery.locale,
        )
    except PlaygroundOperationDenied:
        # A forbidden delivery can never succeed on retry. Retain the evidence,
        # but do not issue a token, call a provider or starve later queue entries.
        delivery.status = "failed"
        delivery.claimed_at = None
        delivery.last_error_code = PlaygroundOperationDenied.code
    except Exception as error:  # noqa: BLE001 - provider adapters have heterogeneous errors
        record_delivery_result(
            delivery,
            delivered=False,
            error_code=type(error).__name__,
        )
    else:
        record_delivery_result(delivery, delivered=True)
    session.add(
        SecurityAuditEvent(
            id=uid("sec"),
            tenant_id=delivery.tenant_id,
            event_type="invitation.delivery",
            subject_type="invitation_delivery",
            subject_id=delivery.id,
            outcome=delivery.status,
            detail=json.dumps(
                {"attempt_count": delivery.attempt_count}, separators=(",", ":")
            ),
        )
    )
    session.commit()
    return True


def cleanup_terminal_invitations(
    session: OrmSession,
    *,
    tenant_id: str,
    limit: int = 100,
    retention: timedelta = timedelta(days=90),
) -> int:
    if not 1 <= limit <= 100:
        raise ValueError("Cleanup batch must be between 1 and 100.")
    invitation_ids = list(
        session.scalars(
            select(CompanyInvitation.id)
            .where(
                CompanyInvitation.tenant_id == tenant_id,
                CompanyInvitation.status.in_(("accepted", "revoked", "expired")),
                CompanyInvitation.terminal_at.is_not(None),
                CompanyInvitation.terminal_at <= now() - retention,
            )
            .order_by(CompanyInvitation.terminal_at, CompanyInvitation.id)
            .limit(limit)
            .with_for_update(skip_locked=True)
        )
    )
    if not invitation_ids:
        return 0
    session.execute(
        delete(InvitationDelivery).where(
            InvitationDelivery.tenant_id == tenant_id,
            InvitationDelivery.invitation_id.in_(invitation_ids),
        )
    )
    session.execute(
        delete(CompanyInvitation).where(
            CompanyInvitation.tenant_id == tenant_id,
            CompanyInvitation.id.in_(invitation_ids),
        )
    )
    return len(invitation_ids)
