"""Read-only recorded-entity activity; never operational quantities or throughput claims."""

from datetime import UTC, datetime, timedelta
from math import ceil, floor

from sqlalchemy import and_, case, func, or_, select
from sqlalchemy.orm import Session

from reality.db.core import BusinessEvent, Document
from reality.services.core import get_tenant

CATEGORIES = ("orders", "reservations", "movements", "documents")


def _entities(tenant_id: str, start: datetime, end: datetime):
    category = case(
        (BusinessEvent.event_type == "reservation.created", "reservations"),
        (BusinessEvent.event_type == "movement.recorded", "movements"),
        (Document.type.in_(("sales_order", "purchase_order")), "orders"),
        else_="documents",
    )
    ranked = (
        select(
            BusinessEvent.id,
            BusinessEvent.recorded_at,
            category.label("category"),
            func.row_number()
            .over(
                partition_by=(category, BusinessEvent.subject_id),
                order_by=(BusinessEvent.recorded_at, BusinessEvent.sequence),
            )
            .label("rank"),
        )
        .outerjoin(
            Document,
            and_(
                Document.tenant_id == tenant_id,
                Document.id == BusinessEvent.subject_id,
                BusinessEvent.subject_type == "document",
            ),
        )
        .where(
            BusinessEvent.tenant_id == tenant_id,
            or_(
                and_(
                    BusinessEvent.event_type == "document.recorded",
                    Document.id.is_not(None),
                ),
                and_(
                    BusinessEvent.event_type == "reservation.created",
                    BusinessEvent.subject_type == "reservation",
                ),
                and_(
                    BusinessEvent.event_type == "movement.recorded",
                    BusinessEvent.subject_type == "movement",
                ),
            ),
        )
        .subquery()
    )
    return (
        select(ranked.c.id, ranked.c.recorded_at, ranked.c.category)
        .where(
            ranked.c.rank == 1,
            ranked.c.recorded_at >= start,
            ranked.c.recorded_at < end,
        )
        .subquery()
    )


def volume(
    session: Session, tenant_id: str, *, days: int = 30, as_of: datetime | None = None
) -> dict:
    tenant = get_tenant(session, tenant_id)
    if days not in (1, 7, 30):
        raise ValueError("Choose 1, 7 or 30 days.")
    end = as_of or datetime.now(UTC)
    start = end - timedelta(days=days)
    entities = _entities(tenant_id, start, end)
    bucket = func.floor(func.extract("epoch", entities.c.recorded_at) / 1800) * 1800
    rows = session.execute(
        select(bucket.label("bucket"), entities.c.category, func.count()).group_by(
            bucket, entities.c.category
        )
    ).all()
    counts = {(int(at), category): count for at, category, count in rows}
    buckets = [
        {
            "start": datetime.fromtimestamp(at, UTC).isoformat(),
            "end": datetime.fromtimestamp(
                min(at + 1800, end.timestamp()), UTC
            ).isoformat(),
            "counts": {key: counts.get((at, key), 0) for key in CATEGORIES},
        }
        for at in range(
            floor(start.timestamp() / 1800) * 1800,
            ceil(end.timestamp() / 1800) * 1800,
            1800,
        )
    ]
    return {
        "start": start.isoformat(),
        "observed_at": end.isoformat(),
        "coverage_start": max(start, tenant.created_at).isoformat(),
        "bucket_seconds": 1800,
        "total": sum(sum(row["counts"].values()) for row in buckets),
        "buckets": buckets,
    }


def details(
    session: Session, tenant_id: str, *, start: datetime, end: datetime
) -> dict:
    get_tenant(session, tenant_id)
    if (
        start.tzinfo is None
        or end.tzinfo is None
        or not timedelta(0) < end - start <= timedelta(days=1)
    ):
        raise ValueError("Choose an interval of up to one day with explicit timezone.")
    entities = _entities(tenant_id, start, end)
    total = session.scalar(select(func.count()).select_from(entities))
    rows = session.scalars(
        select(BusinessEvent)
        .join(entities, BusinessEvent.id == entities.c.id)
        .where(BusinessEvent.tenant_id == tenant_id)
        .order_by(BusinessEvent.recorded_at.desc(), BusinessEvent.sequence.desc())
        .limit(50)
    ).all()
    return {
        "total": total,
        "has_more": total > len(rows),
        "events": [
            {
                "id": row.id,
                "sequence": row.sequence,
                "type": row.event_type,
                "subject_type": row.subject_type,
                "subject_id": row.subject_id,
                "recorded_at": row.recorded_at.isoformat(),
                "occurred_at": row.occurred_at.isoformat(),
                "business_context": {},
                "source_record_id": row.source_record_id,
            }
            for row in rows
        ],
    }
