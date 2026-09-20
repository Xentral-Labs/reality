"""Bounded discovery of retained joint inventory confirmations, not their values."""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from reality.db.core import ChangeProposal, Party
from reality.db.inventory_costing import CostInventoryReview, CostPolicyRevision
from reality.services import core


def inventory_review_options(
    session: Session, tenant_id: str, *, limit: int = 20, cursor: str | None = None
) -> dict:
    """Describe confirmations; graph execution must still admit the complete basis."""
    if type(limit) is not int or not 1 <= limit <= 50:
        raise core.InvalidOperation(
            "Inventory selection limit must be between 1 and 50."
        )
    if cursor is not None and (
        type(cursor) is not str or not cursor.strip() or len(cursor) > 128
    ):
        raise core.InvalidOperation("Invalid inventory selection cursor.")
    review, policy, action, owner = (
        CostInventoryReview,
        CostPolicyRevision,
        ChangeProposal,
        Party,
    )
    options = (
        select(
            review.action_id.label("action_id"),
            func.min(review.effective_at).label("effective_at"),
            func.min(review.knowledge_at).label("knowledge_at"),
            func.min(policy.owner_party_id).label("owner_party_id"),
            func.min(owner.name).label("owner_name"),
            func.min(policy.currency).label("currency"),
            func.count().label("item_count"),
            func.max(review.target_event_sequence).label("sequence"),
        )
        .join(policy, (policy.tenant_id == tenant_id) & (policy.id == review.policy_id))
        .join(action, (action.tenant_id == tenant_id) & (action.id == review.action_id))
        .join(
            owner, (owner.tenant_id == tenant_id) & (owner.id == policy.owner_party_id)
        )
        .where(
            review.tenant_id == tenant_id,
            action.type == "tool:cost.change",
            action.status == "executed",
        )
        .group_by(review.action_id)
        .having(
            func.count().between(2, 10),
            func.count(func.distinct(policy.item_id)) == func.count(),
            func.count(func.distinct(review.effective_at)) == 1,
            func.count(func.distinct(review.knowledge_at)) == 1,
            func.count(func.distinct(review.target_event_sequence)) == 1,
            func.count(func.distinct(policy.owner_party_id)) == 1,
            func.count(func.distinct(policy.currency)) == 1,
        )
        .subquery()
    )
    with session.no_autoflush:
        core.get_tenant(session, tenant_id)
        query = select(options)
        if cursor is not None:
            sequence = session.scalar(
                select(options.c.sequence).where(options.c.action_id == cursor)
            )
            if sequence is None:
                raise core.NotFound("Inventory selection not found.")
            query = query.where(options.c.sequence < sequence)
        rows = (
            session.execute(query.order_by(options.c.sequence.desc()).limit(limit + 1))
            .mappings()
            .all()
        )
        return {
            "items": [
                {
                    key: value.isoformat()
                    if key in {"effective_at", "knowledge_at"}
                    else value
                    for key, value in row.items()
                    if key != "sequence"
                }
                for row in rows[:limit]
            ],
            "next_cursor": rows[limit - 1]["action_id"] if len(rows) > limit else None,
        }
