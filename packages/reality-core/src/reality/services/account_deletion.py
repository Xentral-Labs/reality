"""Platform administration: remove one account and everything only it holds.

This is not a business operation. `require_business_operation` governs what may
happen *inside* a tenant and refuses practice tenants by design, which is why a
free-playground company cannot be deleted through the company lifecycle at all.
Removing an account is platform administration: its authority is the platform-admin
role plus two exact confirmations, checked here and again at the boundary.
"""

from __future__ import annotations

import json
from typing import Any

from sqlalchemy import delete, func, select, update
from sqlalchemy.orm import Session as OrmSession

from reality.db.core import (
    AccessApplication,
    AppUser,
    Base,
    PlaygroundRun,
    SecurityAuditEvent,
    Tenant,
    TenantMembership,
    uid,
)
from reality.services.core import (
    InvalidOperation,
    NotFound,
    _purge_tenant_records,
)

CONFIRMATION_WORD = "DELETE"


def _normalize_email(value: str) -> str:
    return value.strip().lower()


def _user(session: OrmSession, user_id: str) -> AppUser:
    user = session.get(AppUser, user_id)
    if user is None:
        raise NotFound("Account not found.")
    return user


def _sole_owned_tenant_ids(session: OrmSession, user_id: str) -> list[str]:
    """Return tenants whose only remaining active owner is this account."""
    owned = session.scalars(
        select(TenantMembership.tenant_id).where(
            TenantMembership.user_id == user_id,
            TenantMembership.role == "owner",
            TenantMembership.status == "active",
        )
    ).all()
    if not owned:
        return []
    other_owners = set(
        session.scalars(
            select(TenantMembership.tenant_id).where(
                TenantMembership.tenant_id.in_(owned),
                TenantMembership.user_id != user_id,
                TenantMembership.role == "owner",
                TenantMembership.status == "active",
            )
        ).all()
    )
    return sorted(
        tenant_id for tenant_id in set(owned) if tenant_id not in other_owners
    )


def _tenant_record_count(session: OrmSession, tenant_id: str) -> int:
    total = 0
    for table in Base.metadata.sorted_tables:
        if table.name == Tenant.__tablename__ or "tenant_id" not in table.c:
            continue
        total += (
            session.scalar(
                select(func.count())
                .select_from(table)
                .where(table.c.tenant_id == tenant_id)
            )
            or 0
        )
    return total


def _user_reference_columns() -> list[Any]:
    """Every column that points at `app_user`, read from the schema, not a list.

    A hand-written table list rots silently as the schema grows; a missed column
    would either abort the deletion with a foreign key error or, worse, leave a
    dangling reference behind.
    """
    columns = []
    for table in Base.metadata.sorted_tables:
        if table.name == AppUser.__tablename__:
            continue
        for column in table.columns:
            if any(
                foreign_key.column.table.name == AppUser.__tablename__
                for foreign_key in column.foreign_keys
            ):
                columns.append(column)
    return columns


def account_deletion_preview(session: OrmSession, user_id: str) -> dict[str, Any]:
    """Describe what deleting this account would remove. Reads only."""
    user = _user(session, user_id)
    deleted_ids = _sole_owned_tenant_ids(session, user_id)
    member_ids = [
        tenant_id
        for tenant_id in session.scalars(
            select(TenantMembership.tenant_id).where(
                TenantMembership.user_id == user_id,
                TenantMembership.status == "active",
            )
        ).all()
        if tenant_id not in set(deleted_ids)
    ]
    tenants = {
        tenant.id: tenant
        for tenant in session.scalars(
            select(Tenant).where(Tenant.id.in_(deleted_ids + member_ids))
        ).all()
    }
    deleted_companies = [
        {
            "id": tenant_id,
            "name": tenants[tenant_id].name,
            "purpose": tenants[tenant_id].purpose,
            "record_count": _tenant_record_count(session, tenant_id),
        }
        for tenant_id in deleted_ids
        if tenant_id in tenants
    ]
    return {
        "user_id": user.id,
        "email": user.email,
        "is_platform_admin": user.is_platform_admin,
        "deleted_companies": deleted_companies,
        "kept_companies": [
            {"id": tenant_id, "name": tenants[tenant_id].name}
            for tenant_id in sorted(set(member_ids))
            if tenant_id in tenants
        ],
        "sandbox_count": session.scalar(
            select(func.count(PlaygroundRun.id)).where(
                PlaygroundRun.owner_user_id == user_id
            )
        )
        or 0,
        "record_count": sum(entry["record_count"] for entry in deleted_companies),
    }


def delete_account(
    session: OrmSession,
    user_id: str,
    *,
    confirmation_email: str,
    confirmation_word: str,
    actor_user_id: str,
) -> dict[str, Any]:
    """Remove the account, its sole-owned companies and every reference to it."""
    user = _user(session, user_id)
    if user.id == actor_user_id:
        raise InvalidOperation("An administrator cannot delete their own account.")
    if user.is_platform_admin:
        raise InvalidOperation(
            "A platform administrator account cannot be deleted here."
        )
    if _normalize_email(confirmation_email) != _normalize_email(user.email):
        raise InvalidOperation(
            "Account e-mail and DELETE confirmation must match exactly."
        )
    if confirmation_word != CONFIRMATION_WORD:
        raise InvalidOperation(
            "Account e-mail and DELETE confirmation must match exactly."
        )

    summary = account_deletion_preview(session, user_id)
    for tenant_id in [entry["id"] for entry in summary["deleted_companies"]]:
        _purge_tenant_records(session, tenant_id)
        session.execute(delete(Tenant).where(Tenant.id == tenant_id))

    # Whatever survives in other people's companies must stop pointing here:
    # clear the reference where the schema allows it, drop the row where it does not.
    # The one nullable exception is an audit event *about* this account: the row
    # carries no meaning once its subject is gone, so it goes with the account
    # while events the account merely acted on stay, anonymized.
    for column in _user_reference_columns():
        about_the_account = (
            column.table.name == SecurityAuditEvent.__tablename__
            and column.name == "user_id"
        )
        statement = (
            update(column.table).where(column == user_id).values({column: None})
            if column.nullable and not about_the_account
            else delete(column.table).where(column == user_id)
        )
        session.execute(statement)

    session.execute(delete(AppUser).where(AppUser.id == user_id))
    session.add(
        SecurityAuditEvent(
            id=uid("sec"),
            user_id=None,
            actor_user_id=actor_user_id,
            event_type="access.deleted",
            detail=json.dumps(
                {
                    "email": summary["email"],
                    "company_count": len(summary["deleted_companies"]),
                    "record_count": summary["record_count"],
                    "sandbox_count": summary["sandbox_count"],
                }
            ),
        )
    )
    session.commit()
    # The sweep deletes through Table objects, which the ORM identity map never
    # learns about. Without this a caller that reused the session would still be
    # handed the rows it just deleted.
    session.expire_all()
    return summary


def application_account_id(session: OrmSession, application_id: str) -> str:
    """Resolve the account behind one access application."""
    application = session.get(AccessApplication, application_id)
    if application is None:
        raise NotFound("Application not found.")
    return application.user_id
