"""Account-scoped trial entry and bounded managed AI dispatches."""

import os
from datetime import datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from reality.db.core import (
    AISettings,
    AppUser,
    PlaygroundRun,
    SecurityAuditEvent,
    Tenant,
    now,
    uid,
)
from reality.services import company_setup
from reality.services.core import InvalidOperation, NotFound

REQUEST_KEY = "free-playground:v1"
DAILY_LIMIT = 20
USAGE_EVENT = "playground.ai_dispatched"

# Feature 198: the two starts a first entry may choose between, with the company name
# each one carries. The demo start also runs the live simulation.
STARTS = {"international_demo": "My demo company", "empty": "My company"}


def request_entry(session: Session, user_id: str) -> None:
    """Record the explicit signup request; the caller owns the auth transaction."""
    session.add(
        SecurityAuditEvent(
            id=uid("aud"),
            user_id=user_id,
            event_type="playground.requested",
            detail='{"version":1}',
        )
    )


def entry_status(session: Session, user_id: str) -> dict:
    user = session.get(AppUser, user_id)
    if not user:
        raise NotFound("Account not found.")
    requested = (
        session.scalar(
            select(SecurityAuditEvent.id)
            .where(
                SecurityAuditEvent.user_id == user_id,
                SecurityAuditEvent.event_type == "playground.requested",
            )
            .limit(1)
        )
        is not None
    )
    run = session.scalar(
        select(PlaygroundRun).where(
            PlaygroundRun.owner_user_id == user_id,
            PlaygroundRun.client_request_key == REQUEST_KEY,
        )
    )
    receipt = company_setup.read_request(session, user_id, REQUEST_KEY) if run else None
    tenant = session.get(Tenant, run.tenant_id) if run else None
    return {
        "archived": bool(
            run
            and (
                run.status == "archived"
                or tenant is None
                or tenant.archived_at is not None
            )
        ),
        "requested": requested,
        "enabled": True,
        "eligible": user.status == "active" and user.email_verified_at is not None,
        "receipt": receipt,
    }


def enter(
    session: Session,
    user_id: str,
    *,
    confirmed: bool = False,
    content: str = "international_demo",
) -> dict:
    state = entry_status(session, user_id)
    if not confirmed or not state["requested"]:
        raise InvalidOperation("Confirm creation of your demo company first.")
    if content not in STARTS:
        raise InvalidOperation("Choose a demo company or an empty company.")
    if not state["eligible"]:
        raise InvalidOperation("A verified, active account is required.")
    receipt = state["receipt"]
    if receipt:
        tenant = session.get(Tenant, receipt["tenant_id"])
        if (
            tenant is None
            or tenant.archived_at is not None
            or receipt["status"] == "archived"
        ):
            raise InvalidOperation("This demo company is archived.")
    return company_setup.create_company(
        session,
        user_id,
        REQUEST_KEY,
        STARTS[content],
        "sandbox",
        content,
        confirmed=True,
        live_simulation=content == "international_demo",
    )


def _account(
    session: Session, tenant_id: str, actor_user_id: str | None, *, companion: bool
) -> str | None:
    run = session.scalar(
        select(PlaygroundRun).where(PlaygroundRun.tenant_id == tenant_id)
    )
    if not os.environ.get("ANTHROPIC_API_KEY", "").strip():
        return None
    if not companion:
        from reality.agent.settings import has_configured_api_key

        settings = session.get(AISettings, tenant_id)
        if (
            settings
            and settings.provider in {"anthropic", "openai_compatible"}
            and has_configured_api_key(settings)
        ):
            return None
    if actor_user_id and session.scalar(
        select(SecurityAuditEvent.id)
        .where(
            SecurityAuditEvent.user_id == actor_user_id,
            SecurityAuditEvent.event_type.in_(
                {"account.trial_started", "playground.requested"}
            ),
        )
        .limit(1)
    ):
        return actor_user_id
    return (actor_user_id or run.owner_user_id) if run else None


def _allowance(
    session: Session, account_id: str, *, instant: datetime | None = None
) -> dict:
    from reality.services.ai_usage import grant_totals

    instant = instant or now()
    start = instant.replace(hour=0, minute=0, second=0, microsecond=0)
    reset = start + timedelta(days=1)
    used = (
        session.scalar(
            select(func.count())
            .select_from(SecurityAuditEvent)
            .where(
                SecurityAuditEvent.user_id == account_id,
                SecurityAuditEvent.event_type == USAGE_EVENT,
                SecurityAuditEvent.occurred_at >= start,
                SecurityAuditEvent.occurred_at < reset,
            )
        )
        or 0
    )
    grants = grant_totals(session, account_id, instant)
    return {
        **grants,
        "base_remaining": max(0, DAILY_LIMIT - used),
        "bonus_remaining": max(
            0, grants["bonus_questions"] - max(0, used - DAILY_LIMIT)
        ),
        "limit": DAILY_LIMIT,
        "used": used,
        "remaining": max(0, DAILY_LIMIT + grants["bonus_questions"] - used),
        "resets_at": reset.isoformat(),
    }


def allowance(
    session: Session, tenant_id: str, actor_user_id: str | None = None
) -> dict | None:
    account = _account(session, tenant_id, actor_user_id, companion=False)
    return _allowance(session, account) if account else None


def reserve_managed_question(
    session: Session,
    tenant_id: str,
    actor_user_id: str | None = None,
    *,
    companion: bool = False,
) -> None:
    """Commit one dispatch before network work; provider failures still incur usage."""
    account = _account(session, tenant_id, actor_user_id, companion=companion)
    if account is None:
        return
    user = session.scalar(
        select(AppUser).where(AppUser.id == account).with_for_update()
    )
    if user is None:
        raise NotFound("Account not found.")
    instant = now()
    current = _allowance(session, account, instant=instant)
    if current["remaining"] == 0:
        session.rollback()
        raise InvalidOperation(
            f"Your {DAILY_LIMIT + current['bonus_questions']} available AI questions are used. Resets at {current['resets_at']}. You can keep exploring your company."
        )
    session.add(
        SecurityAuditEvent(
            id=uid("aud"),
            user_id=account,
            tenant_id=tenant_id,
            event_type=USAGE_EVENT,
            occurred_at=instant,
            detail='{"version":1}',
        )
    )
    session.commit()
