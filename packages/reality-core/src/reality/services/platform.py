"""Platform operations overview for the environment-configured administrator.

This module answers questions about the deployment itself: who has an account,
which companies exist, whether the runtime is configured, and whether anything is
stuck. It deliberately returns only platform metadata — counts, states, timestamps
and error classes. Tenant business content stays behind the tenant-scoped services,
so the platform administrator does not become an unbounded reader of every company's
reality.
"""

from __future__ import annotations

import ast
import os
from datetime import datetime
from pathlib import Path

from sqlalchemy import func, select, text
from sqlalchemy.orm import Session as OrmSession

from reality.db.core import (
    AccessAdmissionCounter,
    AccessApplication,
    AppUser,
    BusinessEvent,
    CompanyInvitation,
    ImportJob,
    InvitationDelivery,
    MCPAccessToken,
    ProjectionCheckpoint,
    SecurityAuditEvent,
    Tenant,
    TenantMembership,
    UserSession,
    now,
)
from reality.services.access_admission import automatic_access_limit

USER_LIMIT = 100
COMPANY_LIMIT = 100
AUDIT_LIMIT = 25
MIGRATION_DIRECTORIES = (
    Path(__file__).resolve().parents[1] / "migrations" / "versions",
    Path(__file__).resolve().parents[3] / "migrations" / "versions",
)


def _stamp(value: datetime | None) -> str | None:
    return value.isoformat() if value else None


def _configured(name: str) -> bool:
    """Report that a secret is present without ever revealing its value."""
    return bool(os.environ.get(name, "").strip())


def _migration_head(directory: Path) -> str | None:
    """Return one unambiguous head from a directory of revision scripts."""
    if not directory.is_dir():
        return None
    revisions: set[str] = set()
    predecessors: set[str] = set()
    for script in directory.glob("*.py"):
        content = script.read_text(encoding="utf-8")
        try:
            for statement in ast.parse(content).body:
                if not isinstance(statement, ast.Assign):
                    continue
                for target in statement.targets:
                    if not isinstance(target, ast.Name) or target.id not in {
                        "revision",
                        "down_revision",
                    }:
                        continue
                    value = ast.literal_eval(statement.value)
                    if target.id == "revision" and isinstance(value, str):
                        revisions.add(value)
                    elif target.id == "down_revision":
                        if isinstance(value, str):
                            predecessors.add(value)
                        elif isinstance(value, (tuple, list)) and all(
                            isinstance(item, str) for item in value
                        ):
                            predecessors.update(value)
                        elif value is not None:
                            return None
        except (SyntaxError, ValueError, TypeError):
            return None
    heads = revisions - predecessors
    return heads.pop() if len(heads) == 1 else None


def _expected_revision() -> str | None:
    """Derive one head consistently from source or packaged migration assets."""
    existing = [path for path in MIGRATION_DIRECTORIES if path.is_dir()]
    if not existing:
        return None
    heads = [_migration_head(path) for path in existing]
    if any(head is None for head in heads):
        return None
    unique_heads = set(heads)
    return unique_heads.pop() if len(unique_heads) == 1 else None


def _database_revision(session: OrmSession) -> str | None:
    """Read the applied revision without aborting the caller's transaction.

    A schema built directly from the ORM metadata, as the test suite does, has no
    Alembic bookkeeping table. Probing with `to_regclass` keeps that case a plain
    absent value instead of a failed statement.
    """
    if not session.scalar(text("SELECT to_regclass('alembic_version')")):
        return None
    return session.scalar(text("SELECT version_num FROM alembic_version"))


def _counts(session: OrmSession, column, *conditions) -> dict[str, int]:
    query = select(column, func.count()).group_by(column)
    for condition in conditions:
        query = query.where(condition)
    return {key: count for key, count in session.execute(query) if key is not None}


def running_version() -> str:
    """Release version baked into the image; "dev" for a source checkout."""
    return os.environ.get("REALITY_VERSION", "").strip() or "dev"


def running_commit() -> str:
    """Commit baked into the image; empty for a source checkout."""
    return os.environ.get("REALITY_COMMIT", "").strip()


def deployment_posture(session: OrmSession) -> dict:
    """Describe how this instance is configured, using presence bits for secrets."""
    database_revision = _database_revision(session)
    expected_revision = _expected_revision()
    counter = session.get(AccessAdmissionCounter, "automatic")
    return {
        "version": running_version(),
        "commit": running_commit(),
        "auth_mode": os.environ.get("REALITY_AUTH_MODE", "enabled"),
        "cookie_secure": os.environ.get("REALITY_COOKIE_SECURE", "false"),
        "auth_expose_codes": os.environ.get("REALITY_AUTH_EXPOSE_CODES", "false"),
        "artifact_storage": os.environ.get("REALITY_ARTIFACT_STORAGE", "database"),
        "email_provider": os.environ.get("REALITY_EMAIL_PROVIDER", "log"),
        "email_sender_configured": _configured("REALITY_EMAIL_FROM"),
        "email_credential_configured": _configured("RESEND_API_KEY")
        or _configured("REALITY_SMTP_HOST"),
        "master_key_configured": _configured("REALITY_MASTER_KEY"),
        "database_revision": database_revision,
        "expected_revision": expected_revision,
        "migrations_current": bool(database_revision)
        and database_revision == expected_revision,
        "automatic_access_used": counter.used_slots if counter else 0,
        "automatic_access_limit": automatic_access_limit(),
    }


def people_overview(session: OrmSession) -> dict:
    """List accounts with the membership and session facts an operator acts on."""
    users = list(
        session.scalars(
            select(AppUser).order_by(AppUser.created_at.desc()).limit(USER_LIMIT)
        )
    )
    identifiers = [user.id for user in users]
    memberships: dict[str, list[dict]] = {}
    if identifiers:
        rows = session.execute(
            select(TenantMembership, Tenant)
            .join(Tenant, Tenant.id == TenantMembership.tenant_id)
            .where(
                TenantMembership.user_id.in_(identifiers),
                TenantMembership.status == "active",
            )
        ).all()
        for membership, tenant in rows:
            memberships.setdefault(membership.user_id, []).append(
                {"id": tenant.id, "name": tenant.name, "role": membership.role}
            )
    sessions = dict(
        session.execute(
            select(UserSession.user_id, func.count())
            .where(
                UserSession.revoked_at.is_(None),
                UserSession.expires_at > now(),
            )
            .group_by(UserSession.user_id)
        ).all()
    )
    oldest_pending = session.scalar(
        select(func.min(AccessApplication.requested_at)).where(
            AccessApplication.status == "pending"
        )
    )
    return {
        "total": session.scalar(select(func.count(AppUser.id))) or 0,
        "by_status": _counts(session, AppUser.status),
        "pending_applications": session.scalar(
            select(func.count(AccessApplication.id)).where(
                AccessApplication.status == "pending"
            )
        )
        or 0,
        "oldest_pending_at": _stamp(oldest_pending),
        "users": [
            {
                "id": user.id,
                "email": user.email,
                "display_name": user.display_name,
                "status": user.status,
                "is_platform_admin": user.is_platform_admin,
                "email_verified_at": _stamp(user.email_verified_at),
                "last_login_at": _stamp(user.last_login_at),
                "created_at": _stamp(user.created_at),
                "active_sessions": sessions.get(user.id, 0),
                "companies": memberships.get(user.id, []),
            }
            for user in users
        ],
    }


def companies_overview(session: OrmSession) -> dict:
    """Describe tenants by shape and liveness, never by business content."""
    tenants = list(
        session.scalars(
            select(Tenant)
            .where(Tenant.purpose == "business")
            .order_by(Tenant.created_at.desc())
            .limit(COMPANY_LIMIT)
        )
    )
    roles: dict[str, dict[str, int]] = {}
    for tenant_id, role, count in session.execute(
        select(TenantMembership.tenant_id, TenantMembership.role, func.count())
        .where(TenantMembership.status == "active")
        .group_by(TenantMembership.tenant_id, TenantMembership.role)
    ):
        roles.setdefault(tenant_id, {})[role] = count
    invitations = dict(
        session.execute(
            select(CompanyInvitation.tenant_id, func.count())
            .where(CompanyInvitation.status == "pending")
            .group_by(CompanyInvitation.tenant_id)
        ).all()
    )
    activity = {
        tenant_id: (count, last)
        for tenant_id, count, last in session.execute(
            select(
                BusinessEvent.tenant_id,
                func.count(),
                func.max(BusinessEvent.recorded_at),
            ).group_by(BusinessEvent.tenant_id)
        )
    }
    return {
        "total": session.scalar(
            select(func.count(Tenant.id)).where(Tenant.purpose == "business")
        )
        or 0,
        "archived": session.scalar(
            select(func.count(Tenant.id)).where(
                Tenant.purpose == "business", Tenant.archived_at.is_not(None)
            )
        )
        or 0,
        "rows": [
            {
                "id": tenant.id,
                "name": tenant.name,
                "created_at": _stamp(tenant.created_at),
                "archived_at": _stamp(tenant.archived_at),
                "owners": roles.get(tenant.id, {}).get("owner", 0),
                "members": roles.get(tenant.id, {}).get("member", 0),
                "open_invitations": invitations.get(tenant.id, 0),
                "business_events": activity.get(tenant.id, (0, None))[0],
                "last_event_at": _stamp(activity.get(tenant.id, (0, None))[1]),
            }
            for tenant in tenants
        ],
    }


def operations_health(session: OrmSession) -> dict:
    """Surface the work that silently stops: intake, projections and delivery."""
    return {
        "import_jobs": _counts(session, ImportJob.status),
        "projections_failed": session.scalar(
            select(func.count(ProjectionCheckpoint.id)).where(
                ProjectionCheckpoint.status != "ready"
            )
        )
        or 0,
        "invitation_deliveries": _counts(session, InvitationDelivery.status),
        "active_agent_tokens": session.scalar(
            select(func.count(MCPAccessToken.id)).where(
                MCPAccessToken.revoked_at.is_(None)
            )
        )
        or 0,
    }


def security_trail(session: OrmSession) -> list[dict]:
    """Return the most recent privileged events with actor and subject identity."""
    events = list(
        session.scalars(
            select(SecurityAuditEvent)
            .order_by(SecurityAuditEvent.occurred_at.desc())
            .limit(AUDIT_LIMIT)
        )
    )
    identifiers = {
        identifier
        for event in events
        for identifier in (event.user_id, event.actor_user_id)
        if identifier
    }
    emails = (
        dict(
            session.execute(
                select(AppUser.id, AppUser.email).where(AppUser.id.in_(identifiers))
            ).all()
        )
        if identifiers
        else {}
    )
    return [
        {
            "id": event.id,
            "event_type": event.event_type,
            "outcome": event.outcome,
            "occurred_at": _stamp(event.occurred_at),
            "tenant_id": event.tenant_id,
            "subject": emails.get(event.user_id or ""),
            "actor": emails.get(event.actor_user_id or ""),
        }
        for event in events
    ]


def platform_overview(session: OrmSession) -> dict:
    """Compose the complete platform administration overview."""
    return {
        "generated_at": _stamp(now()),
        "deployment": deployment_posture(session),
        "people": people_overview(session),
        "companies": companies_overview(session),
        "operations": operations_health(session),
        "security": security_trail(session),
    }
