"""Owner-scoped report definitions with explicit revision and retry semantics."""

import base64
import json
from contextlib import contextmanager
from contextvars import ContextVar

from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from reality.db.analytics import AnalyticsReport
from reality.db.core import AppUser, TenantMembership, now, uid
from reality.services.analytics.errors import AnalyticsError, fingerprint
from reality.services.core import NotFound
from reality.services.memberships import Principal

# Who is asking. A private report is owned, so every read and every change needs
# the principal, and it travels here rather than through every signature.
CALLER: ContextVar[Principal | None] = ContextVar("analytics_caller", default=None)


@contextmanager
def caller(principal):
    token = CALLER.set(principal)
    try:
        yield
    finally:
        CALLER.reset(token)



class ReportKind:
    """What makes one kind of saved report different from another.

    Retry, revision, ownership and soft deletion are the same for every report, so
    they are written once. Only three things differ: the change model, how its
    payload is checked, and the model version the row records — and the last is why
    this exists at all, because a graph report that cannot say which meaning
    produced it would silently change what it reports.
    """

    def __init__(self, key, change_model, payload_field, check, version=lambda: None):
        self.key = key
        self.change_model = change_model
        self.payload_field = payload_field
        self.check = check
        self.version = version


def _graph_kind():
    from reality.domain.graph_report import GraphReportChange
    from reality.services.analytics.graph_model import reporting_graph
    from reality.services.analytics.traversal import plan

    return ReportKind(
        "graph",
        GraphReportChange,
        "question",
        lambda question: plan(question),
        lambda: reporting_graph().model_version,
    )


def kind(key):
    """One kind ships today. The seam stays because the row records which one.

    A report saved before the graph carries no kind and no model version; it is
    not readable by any surface and is not migrated — the configured generation
    it belonged to was replaced rather than translated.
    """
    if key != "graph":
        raise AnalyticsError(f"unknown report kind {key!r}", "unknown_report_kind")
    return _graph_kind()


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
        "kind": row.kind or "definition",
        "model_version": row.model_version,
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


def get_report(session, tenant_id, principal, report_id, report_kind=None):
    row = owned(session, tenant_id, principal, report_id)
    if report_kind and (row.kind or "definition") != report_kind:
        # Opening it under the wrong contract would read the question with the wrong
        # meaning, which is worse than not finding it.
        raise NotFound("Report not found.")
    return render(row)


def list_reports(
    session, tenant_id, principal, query="", limit=50, cursor=None, report_kind=None
):
    owner = require_author(session, tenant_id, principal)
    if not 1 <= limit <= 200 or len(query) > 200:
        raise AnalyticsError("Choose a valid report list limit or search.")
    statement = select(AnalyticsReport).where(
        AnalyticsReport.tenant_id == tenant_id,
        AnalyticsReport.owner_user_id == owner,
        AnalyticsReport.deleted_at.is_(None),
    )
    if report_kind:
        statement = statement.where(AnalyticsReport.kind == report_kind)
    if query:
        statement = statement.where(
            AnalyticsReport.name.icontains(query, autoescape=True)
        )
    scope = fingerprint([tenant_id, owner, query, report_kind or ""])
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


def change_graph_report(session, tenant_id, principal, arguments):
    """The same journey for a graph question, sharing one retry implementation."""
    return _change(session, tenant_id, principal, arguments, kind("graph"))


def _change(session, tenant_id, principal, arguments, contract):
    owner = require_author(session, tenant_id, principal)
    try:
        request = contract.change_model.model_validate(arguments)
    except ValidationError as error:
        raise AnalyticsError(str(error)) from error
    payload = getattr(request, contract.payload_field)
    if payload:
        contract.check(payload)
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
            definition = payload.model_dump(mode="json", by_alias=True)
        row = AnalyticsReport(
            id=uid("anr"),
            tenant_id=tenant_id,
            owner_user_id=owner,
            name=request.name,
            definition=definition,
            kind=contract.key,
            model_version=contract.version(),
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
    # A row saved before the graph carries no kind at all. Treating that as
    # "any kind" would let a graph change overwrite a retired report in place.
    stored_kind = row.kind or "definition"
    if stored_kind != contract.key:
        raise AnalyticsError(
            f"This report holds a {stored_kind} question; it cannot be changed as a "
            f"{contract.key} one.",
            "kind_mismatch",
        )
    if request.name:
        row.name = request.name
    if payload:
        row.definition = payload.model_dump(mode="json", by_alias=True)
        row.model_version = contract.version()
    if request.operation == "delete":
        row.deleted_at = now()
    row.revision += 1
    row.updated_at = now()
    row.last_request_id, row.last_payload_hash = request_id, digest
    session.flush()
    return render(row)
