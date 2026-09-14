"""Owner-scoped report definitions with explicit revision and retry semantics."""

import base64
import json

from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from reality.db.analytics import AnalyticsReport
from reality.db.core import AppUser, TenantMembership, now, uid
from reality.domain.analytics import ReportChange
from reality.services.analytics.execution import (
    AnalyticsError,
    checked_definition,
    fingerprint,
)
from reality.services.core import NotFound


def require_author(session, tenant_id, principal):
    if principal is None:
        raise AnalyticsError(
            "An authenticated user is required for private reports.",
            "user_context_required",
        )
    active = session.scalar(
        select(TenantMembership.id)
        .join(AppUser, AppUser.id == TenantMembership.user_id)
        .where(
            TenantMembership.tenant_id == tenant_id,
            TenantMembership.user_id == principal.user_id,
            TenantMembership.status == "active",
            AppUser.status == "active",
        )
    )
    if not active:
        raise NotFound("Report not found.")
    return principal.user_id


def render(row):
    return {
        "id": row.id,
        "name": row.name,
        "definition": row.definition,
        "revision": row.revision,
        "created_at": row.created_at.isoformat(),
        "updated_at": row.updated_at.isoformat(),
        "deleted": row.deleted_at is not None,
    }


def owned(session, tenant_id, principal, report_id, *, lock=False, deleted=False):
    owner = require_author(session, tenant_id, principal)
    statement = select(AnalyticsReport).where(
        AnalyticsReport.tenant_id == tenant_id,
        AnalyticsReport.owner_user_id == owner,
        AnalyticsReport.id == report_id,
    )
    if not deleted:
        statement = statement.where(AnalyticsReport.deleted_at.is_(None))
    if lock:
        statement = statement.with_for_update()
    row = session.scalar(statement)
    if row is None:
        raise NotFound("Report not found.")
    return row


def get_report(session, tenant_id, principal, report_id):
    return render(owned(session, tenant_id, principal, report_id))


def list_reports(session, tenant_id, principal, *, query="", limit=50, cursor=None):
    owner = require_author(session, tenant_id, principal)
    if not 1 <= limit <= 200 or len(query) > 200:
        raise AnalyticsError("Choose a valid report list limit or search.")
    statement = select(AnalyticsReport).where(
        AnalyticsReport.tenant_id == tenant_id,
        AnalyticsReport.owner_user_id == owner,
        AnalyticsReport.deleted_at.is_(None),
    )
    if query:
        statement = statement.where(
            AnalyticsReport.name.icontains(query, autoescape=True)
        )
    scope = fingerprint([tenant_id, owner, query])
    if cursor:
        try:
            token = json.loads(base64.urlsafe_b64decode(cursor))
            if token["scope"] != scope or not isinstance(token["after"], str):
                raise ValueError()
            statement = statement.where(AnalyticsReport.id > token["after"])
        except (ValueError, TypeError, KeyError, UnicodeError) as error:
            raise AnalyticsError(
                "Invalid private report cursor.", "invalid_cursor"
            ) from error
    rows = list(
        session.scalars(statement.order_by(AnalyticsReport.id).limit(limit + 1))
    )
    return {
        "records": [render(row) for row in rows[:limit]],
        "has_more": len(rows) > limit,
        "next_cursor": base64.urlsafe_b64encode(
            json.dumps({"scope": scope, "after": rows[limit - 1].id}).encode()
        ).decode()
        if len(rows) > limit
        else None,
    }


def change_report(session, tenant_id, principal, arguments):
    owner = require_author(session, tenant_id, principal)
    try:
        request = ReportChange.model_validate(arguments)
    except ValidationError as error:
        raise AnalyticsError(str(error)) from error
    if request.definition:
        checked_definition({"definition": request.definition.model_dump(mode="json")})
    digest = fingerprint(request.model_dump(mode="json"))
    request_id = str(request.request_id)
    if request.operation in {"create", "duplicate"}:
        existing = session.scalar(
            select(AnalyticsReport).where(
                AnalyticsReport.tenant_id == tenant_id,
                AnalyticsReport.owner_user_id == owner,
                AnalyticsReport.create_request_id == request_id,
            )
        )
        if existing:
            if existing.create_payload_hash != digest:
                raise AnalyticsError(
                    "This retry key belongs to a different change.",
                    "idempotency_conflict",
                )
            return {**render(existing), "replayed": True}
        if request.operation == "duplicate":
            source = owned(session, tenant_id, principal, request.report_id, lock=True)
            if source.revision != request.expected_revision:
                raise AnalyticsError(
                    "The report changed. Reload it before duplicating.",
                    "revision_conflict",
                )
            definition = source.definition
        else:
            definition = request.definition.model_dump(mode="json")
        row = AnalyticsReport(
            id=uid("anr"),
            tenant_id=tenant_id,
            owner_user_id=owner,
            name=request.name,
            definition=definition,
            create_request_id=request_id,
            create_payload_hash=digest,
            last_request_id=request_id,
            last_payload_hash=digest,
        )
        try:
            with session.begin_nested():
                session.add(row)
                session.flush()
        except IntegrityError as error:
            if (
                getattr(getattr(error.orig, "diag", None), "constraint_name", None)
                != "uq_analytics_report_create"
            ):
                raise
            existing = session.scalar(
                select(AnalyticsReport).where(
                    AnalyticsReport.tenant_id == tenant_id,
                    AnalyticsReport.owner_user_id == owner,
                    AnalyticsReport.create_request_id == request_id,
                )
            )
            if existing is None or existing.create_payload_hash != digest:
                raise AnalyticsError(
                    "This retry key belongs to a different change.",
                    "idempotency_conflict",
                ) from error
            return {**render(existing), "replayed": True}
        return render(row)
    row = owned(
        session, tenant_id, principal, request.report_id, lock=True, deleted=True
    )
    if row.last_request_id == request_id:
        if row.last_payload_hash != digest:
            raise AnalyticsError(
                "This retry key belongs to a different change.", "idempotency_conflict"
            )
        return {**render(row), "replayed": True}
    if row.deleted_at:
        raise NotFound("Report not found.")
    if row.revision != request.expected_revision:
        raise AnalyticsError(
            "The report changed. Reload it before saving.", "revision_conflict"
        )
    if request.name:
        row.name = request.name
    if request.definition:
        row.definition = request.definition.model_dump(mode="json")
    if request.operation == "delete":
        row.deleted_at = now()
    row.revision += 1
    row.updated_at = now()
    row.last_request_id, row.last_payload_hash = request_id, digest
    session.flush()
    return render(row)
