"""A question asked now and answered later (spec 236).

The decision of what may wait is not a new number. The derivations already carry
input caps, and today those caps produce a refusal: this company is too large to
derive inside one request. This module changes what that refusal *means*. The same
three codes now send the question to the worker instead of turning it away, and
every other refusal — a name that does not exist, an edge that fans out, a unit
that cannot be added — still arrives immediately, because those are judgements
about the question and no amount of waiting improves them.

The consequence is worth stating plainly: the set of questions that defer is
exactly the set that is refused today. Nothing that answers now becomes slower.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from reality.db.analytics import AnalysisRequest
from reality.db.core import TenantMembership
from reality.domain.traversal import Traversal
from reality.services.analytics.graph_model import reporting_graph
from reality.services.analytics.traversal import TraversalRefused, run_traversal
from reality.services.core import InvalidOperation, NotFound

#: The refusals that mean "too much of this company to hold in one request", and
#: only those. Every other code is a statement about the question itself.
SIZE_REFUSALS = frozenset({"finance_limit", "inventory_limit", "position_limit"})

JOB_TYPE = "analysis.run"
RETENTION = timedelta(days=7)


def _member(session: Session, tenant_id: str, user_id: str | None) -> str:
    """Whoever may ask a question interactively may ask it deferred, and no more."""
    if not user_id:
        raise InvalidOperation("A requested analysis needs a signed-in requester.")
    membership = session.scalar(
        select(TenantMembership).where(
            TenantMembership.tenant_id == tenant_id,
            TenantMembership.user_id == user_id,
            TenantMembership.status == "active",
        )
    )
    if membership is None:
        raise NotFound("Company not found.")
    return user_id


def ask(
    session: Session,
    tenant_id: str,
    *,
    question: Traversal,
    user_id: str | None,
    request_id: str,
) -> dict[str, Any]:
    """Answer the question, or accept it for the worker and say which.

    The answer comes back under `"answer"`. A deferral comes back under
    `"request"` with the reason it could not be answered here, so the asker is
    never left to guess why this particular question is being queued.
    """
    try:
        result = run_traversal(session, tenant_id, question)
    except TraversalRefused as refusal:
        if refusal.code not in SIZE_REFUSALS:
            raise
        return {
            "state": "accepted",
            "request": _accept(
                session,
                tenant_id,
                question=question,
                user_id=user_id,
                request_id=request_id,
                reason=refusal.code,
                message=str(refusal),
            ),
        }
    return {"state": "answered", "answer": result}


def _accept(
    session: Session,
    tenant_id: str,
    *,
    question: Traversal,
    user_id: str | None,
    request_id: str,
    reason: str,
    message: str,
) -> dict[str, Any]:
    from reality.services.scheduled_jobs import create_manual_run

    requester = _member(session, tenant_id, user_id)
    existing = session.scalar(
        select(AnalysisRequest).where(
            AnalysisRequest.tenant_id == tenant_id,
            AnalysisRequest.requested_by_user_id == requester,
            AnalysisRequest.request_id == request_id,
        )
    )
    if existing is not None:
        # A retried request finds its own run rather than starting a second one.
        return state_of(existing)

    row = AnalysisRequest(
        id=f"anq_{uuid4().hex}",
        tenant_id=tenant_id,
        requested_by_user_id=requester,
        question=question.model_dump(mode="json", by_alias=True, exclude_none=True),
        model_version=reporting_graph().model_version,
        deferred_reason=reason,
        state="accepted",
        request_id=request_id,
        expires_at=datetime.now(UTC) + RETENTION,
    )
    session.add(row)
    session.flush()
    run = create_manual_run(
        session,
        tenant_id,
        requester,
        JOB_TYPE,
        {"analysis_request_id": row.id},
        request_id=f"{request_id}:analysis",
    )
    row.run_id = run.id
    session.flush()
    return state_of(row) | {"message": message}


def state_of(row: AnalysisRequest) -> dict[str, Any]:
    """What a requested analysis is, without its rows."""
    return {
        "id": row.id,
        "state": row.state,
        "deferred_reason": row.deferred_reason,
        "model_version": row.model_version,
        "requested_at": row.created_at.isoformat() if row.created_at else None,
        "answered_at": row.answered_at.isoformat() if row.answered_at else None,
        "expires_at": row.expires_at.isoformat() if row.expires_at else None,
        "row_count": row.row_count,
        "failure_code": row.failure_code,
        "failure_message": row.failure_message,
    }


def _owned(
    session: Session, tenant_id: str, request_id: str, user_id: str | None
) -> AnalysisRequest:
    requester = _member(session, tenant_id, user_id)
    row = session.scalar(
        select(AnalysisRequest).where(
            AnalysisRequest.tenant_id == tenant_id,
            AnalysisRequest.id == request_id,
            AnalysisRequest.requested_by_user_id == requester,
        )
    )
    if row is None:
        raise NotFound("Requested analysis not found.")
    return row


def collect(
    session: Session, tenant_id: str, request_id: str, *, user_id: str | None
) -> dict[str, Any]:
    """The answer, with the question and the moment that make it mean something.

    A ready result is evidence of one answer at one moment. It is returned with
    its question and `answered_at` so that nothing downstream can mistake it for
    what is true now.
    """
    row = _owned(session, tenant_id, request_id, user_id)
    answer = state_of(row)
    answer["question"] = row.question
    if row.state == "ready":
        answer["rows"] = row.rows or []
        answer["statements"] = row.statements
    return answer


def listing(
    session: Session, tenant_id: str, *, user_id: str | None, limit: int = 50
) -> dict[str, Any]:
    requester = _member(session, tenant_id, user_id)
    rows = session.scalars(
        select(AnalysisRequest)
        .where(
            AnalysisRequest.tenant_id == tenant_id,
            AnalysisRequest.requested_by_user_id == requester,
        )
        .order_by(AnalysisRequest.created_at.desc())
        .limit(limit)
    ).all()
    return {"items": [state_of(row) for row in rows]}


def expire(session: Session, tenant_id: str, *, now: datetime | None = None) -> int:
    """Remove answers nobody collected, so none of them lingers as a current figure."""
    moment = now or datetime.now(UTC)
    rows = session.scalars(
        select(AnalysisRequest).where(
            AnalysisRequest.tenant_id == tenant_id,
            AnalysisRequest.expires_at < moment,
        )
    ).all()
    for row in rows:
        session.delete(row)
    return len(rows)
