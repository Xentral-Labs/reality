"""Closed contribution-only writer proof for captured scope resolution.

Never apply a blanket cost.reviewed exemption. Unknown or incomplete evidence stays
invalidating. This proves event relevance, not financial amounts or owner approval.
"""

import json

from pydantic import TypeAdapter, ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from reality.db.contribution import CostContributionReview, CostRevenueMatchBasis
from reality.db.core import BusinessEvent, ChangeProposal
from reality.db.inventory_costing import CostValuationAssessmentRevision
from reality.domain.costing import (
    ContributionBatchReview,
    ContributionReview,
    ValuationAssessment,
)
from reality.services import core

_REQUEST = TypeAdapter(
    ContributionReview | ContributionBatchReview | ValuationAssessment
)
MAX_REVIEW_EVENTS = 100


def _targets(session: Session, tenant: str, event: dict) -> set[str] | None:
    if (
        event["event_type"] != "cost.reviewed"
        or event["schema_version"] != 1
        or event["subject_type"] != "action"
        or not event["action_id"]
        or event["subject_id"] != event["action_id"]
    ):
        return None
    action_table = ChangeProposal.__table__
    action = (
        session.execute(
            select(action_table).where(
                action_table.c.tenant_id == tenant,
                action_table.c.id == event["action_id"],
            )
        )
        .mappings()
        .one_or_none()
    )
    if (
        action is None
        or action["type"] != "tool:cost.change"
        or action["status"] != "executed"
        or action["decided_at"] is None
        or action["decided_by_user_id"] is None
    ):
        return None
    try:
        request = _REQUEST.validate_python(json.loads(action["input"]))
        payload = json.loads(event["payload"])
    except (ValueError, TypeError, ValidationError):
        return None
    if (
        payload != {"operation": request.operation}
        or request.expected_event_sequence >= event["sequence"]
    ):
        return None
    if isinstance(request, ValuationAssessment):
        retained = session.scalar(
            select(CostValuationAssessmentRevision).where(
                CostValuationAssessmentRevision.tenant_id == tenant,
                CostValuationAssessmentRevision.introduced_event_id == event["id"],
                CostValuationAssessmentRevision.action_id == action["id"],
                CostValuationAssessmentRevision.inventory_review_id
                == request.inventory_review_id,
            )
        )
        if retained is None:
            return None
        return set()
    targets = (
        {request.document_line_id}
        if isinstance(request, ContributionReview)
        else {position.document_line_id for position in request.positions}
    )
    review, basis = CostContributionReview.__table__, CostRevenueMatchBasis.__table__
    rows = session.execute(
        select(review.c.action_id, review.c.event_sequence, basis.c.document_line_id)
        .outerjoin(
            basis,
            (basis.c.tenant_id == tenant) & (basis.c.id == review.c.revenue_basis_id),
        )
        .where(
            review.c.tenant_id == tenant, review.c.introduced_event_id == event["id"]
        )
        .limit(len(targets) + 1)
    ).all()
    if (
        len(rows) != len(targets)
        or {row.document_line_id for row in rows} != targets
        or any(
            row.action_id != action["id"] or row.event_sequence != event["sequence"]
            for row in rows
        )
    ):
        return None
    return targets


def _unchanged(
    session: Session,
    tenant: str,
    after: int,
    through: int,
    *,
    document_line_id: str | None = None,
) -> dict:
    """Prove a bounded complete interval contains only non-input review decisions.

    None selects inventory input relevance. A line identity selects contribution
    relevance and never exempts a new review of that same line. Caller supplies trusted
    selected-review/census cursors inside one snapshot; this is not an API assertion.
    """
    if (
        type(after) is not int
        or type(through) is not int
        or after < 0
        or through < after
    ):
        raise core.InvalidOperation("Invalid captured review event interval.")
    proof = {
        "unchanged": False,
        "from_event_sequence": after,
        "through_event_sequence": through,
        "checked_review_event_ids": [],
    }
    if through - after > MAX_REVIEW_EVENTS:
        return proof
    with session.no_autoflush:
        table = BusinessEvent.__table__
        events = (
            session.execute(
                select(table)
                .where(
                    table.c.tenant_id == tenant,
                    table.c.sequence > after,
                    table.c.sequence <= through,
                )
                .order_by(table.c.sequence)
                .limit(MAX_REVIEW_EVENTS + 1)
            )
            .mappings()
            .all()
        )
        # Tenant event allocation is serialized and contiguous. Missing history is not
        # evidence that nothing changed, even when the last event alone looks harmless.
        if len(events) != through - after:
            return proof
        for event in events:
            targets = _targets(session, tenant, dict(event))
            if targets is None or document_line_id in targets:
                return proof
            proof["checked_review_event_ids"].append(event["id"])
    return {**proof, "unchanged": True}
