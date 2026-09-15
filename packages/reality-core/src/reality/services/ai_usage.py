"""Auditable account-wide managed AI grants (spec 196)."""

import json
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from reality.db.core import (
    AppUser,
    SecurityAuditEvent,
    Tenant,
    TenantMembership,
    now,
    uid,
)
from reality.services.core import InvalidOperation, NotFound
from reality.services.tenant_policy import require_playground_account

GRANT_EVENT = "playground.ai_allowance_granted"
SELF_EXTENSIONS = 3
SELF_QUESTIONS = 20


def _grants(session: Session, account: str) -> list[SecurityAuditEvent]:
    return list(
        session.scalars(
            select(SecurityAuditEvent)
            .where(
                SecurityAuditEvent.user_id == account,
                SecurityAuditEvent.event_type == GRANT_EVENT,
            )
            .order_by(
                SecurityAuditEvent.occurred_at.desc(), SecurityAuditEvent.id.desc()
            )
        )
    )


def grant_totals(session: Session, account: str, instant: datetime) -> dict:
    rows = _grants(session, account)
    details = [json.loads(row.detail) for row in rows]
    return {
        "bonus_questions": sum(
            detail["questions"]
            for detail in details
            if datetime.fromisoformat(detail["expires_at"]) > instant
        ),
        "self_extensions_remaining": max(
            0, SELF_EXTENSIONS - sum(detail["mode"] == "self" for detail in details)
        ),
    }


def _target(
    session: Session, tenant_id: str, actor_id: str, recipient_email: str = ""
) -> tuple[AppUser, AppUser]:
    actor = require_playground_account(session, actor_id)
    tenant = session.get(Tenant, tenant_id)
    if tenant is None or tenant.archived_at is not None:
        raise NotFound("Company not found.")

    def member(user_id: str) -> bool:
        return (
            session.scalar(
                select(TenantMembership.id).where(
                    TenantMembership.tenant_id == tenant_id,
                    TenantMembership.user_id == user_id,
                    TenantMembership.status == "active",
                )
            )
            is not None
        )

    if not actor.is_platform_admin and not member(actor.id):
        raise NotFound("Company not found.")
    target = actor
    if recipient_email.strip():
        if not actor.is_platform_admin:
            raise InvalidOperation("Only platform admins may select another account.")
        target = session.scalar(
            select(AppUser).where(AppUser.email == recipient_email.strip().lower())
        )
        if target is None or not member(target.id):
            raise NotFound("Account not found in this company.")
        require_playground_account(session, target.id)
    return actor, target


def status(
    session: Session, tenant_id: str, actor_id: str, *, recipient_email: str = ""
) -> dict:
    from reality.services import free_playground

    actor, target = _target(session, tenant_id, actor_id, recipient_email)
    account = free_playground._account(session, tenant_id, target.id, companion=False)
    current = (
        free_playground._allowance(session, target.id) if account == target.id else None
    )
    rows = _grants(session, target.id)
    history = []
    for row in rows:
        detail = json.loads(row.detail)
        author = session.get(AppUser, row.actor_user_id) if row.actor_user_id else None
        history.append(
            {
                "id": row.id,
                "actor_user_id": row.actor_user_id,
                "actor_name": (author.display_name or author.email)
                if author
                else row.actor_user_id,
                "recipient_user_id": row.user_id,
                "occurred_at": row.occurred_at.isoformat(),
                **{
                    key: detail[key]
                    for key in ("questions", "mode", "reason", "expires_at")
                },
            }
        )
    return {
        "allowance": current,
        "recipient": {
            "id": target.id,
            "email": target.email,
            "name": target.display_name,
        },
        "can_admin_grant": actor.is_platform_admin,
        "self_extensions_remaining": grant_totals(session, target.id, now())[
            "self_extensions_remaining"
        ],
        "self_extension_questions": SELF_QUESTIONS,
        "history": history,
    }


def grant(
    session: Session,
    tenant_id: str,
    actor_id: str,
    *,
    request_key: str,
    confirmed: bool = False,
    mode: str = "self",
    questions: int = SELF_QUESTIONS,
    reason: str = "",
    recipient_email: str = "",
) -> dict:
    from reality.services import free_playground

    if confirmed is not True:
        raise InvalidOperation("Confirmation is required.")
    if not isinstance(request_key, str) or not 1 <= len(request_key.strip()) <= 128:
        raise InvalidOperation("A request key is required.")
    actor, target = _target(session, tenant_id, actor_id, recipient_email)
    if mode not in {"self", "admin"}:
        raise InvalidOperation("Unknown extension mode.")
    if mode == "admin" and not actor.is_platform_admin:
        raise InvalidOperation("Only platform admins may grant extra questions.")
    if mode == "self" and (target.id != actor.id or questions != SELF_QUESTIONS):
        raise InvalidOperation(
            "Self extensions grant 20 questions to your own account."
        )
    if type(questions) is not int or questions not in {20, 100}:
        raise InvalidOperation("Grant 20 or 100 questions.")
    reason = "Continued testing" if mode == "self" else reason.strip()
    if not reason or len(reason) > 500:
        raise InvalidOperation("A reason of 1 to 500 characters is required.")
    # Same account lock as dispatch reservations: no cross-company quota race.
    session.scalar(select(AppUser).where(AppUser.id == target.id).with_for_update())
    payload = {
        "mode": mode,
        "questions": questions,
        "reason": reason,
        "request_key": request_key,
    }
    for previous in _grants(session, target.id):
        detail = json.loads(previous.detail)
        if detail["request_key"] == request_key:
            if (
                any(detail[key] != value for key, value in payload.items())
                or previous.actor_user_id != actor.id
            ):
                raise InvalidOperation(
                    "Request key was already used for a different grant."
                )
            session.commit()
            return status(session, tenant_id, actor_id, recipient_email=recipient_email)
    if (
        free_playground._account(session, tenant_id, target.id, companion=False)
        != target.id
    ):
        raise InvalidOperation("No managed AI allowance is active for this account.")
    instant = now()
    current = free_playground._allowance(session, target.id, instant=instant)
    if mode == "self":
        if current["self_extensions_remaining"] == 0:
            raise InvalidOperation("All three self-service extensions have been used.")
        if current["remaining"] != 0:
            raise InvalidOperation("Use the available questions before extending.")
    session.add(
        SecurityAuditEvent(
            id=uid("aud"),
            user_id=target.id,
            actor_user_id=actor.id,
            tenant_id=tenant_id,
            subject_type="ai_allowance",
            subject_id=target.id,
            outcome="granted",
            event_type=GRANT_EVENT,
            occurred_at=instant,
            detail=json.dumps(
                {"version": 1, **payload, "expires_at": current["resets_at"]}
            ),
        )
    )
    session.commit()
    return status(session, tenant_id, actor_id, recipient_email=recipient_email)
