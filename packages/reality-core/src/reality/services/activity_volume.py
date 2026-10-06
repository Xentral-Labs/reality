"""Read-only recorded-entity activity; never operational quantities or throughput claims."""

from datetime import UTC, datetime, timedelta
from math import ceil, floor

from sqlalchemy import and_, case, func, or_, select
from sqlalchemy.orm import Session

from reality.db.core import BusinessEvent, Document
from reality.services.core import InvalidOperation, get_tenant

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


def rolling(
    session: Session,
    tenant_id: str,
    *,
    minutes: int = 15,
    as_of: datetime | None = None,
) -> dict:
    """
    BUSINESS PURPOSE:
    Observe bounded recent recorded business entities without claiming throughput.

    BUSINESS RULE activity_volume.rolling.classification:
    Reuse Home's first-recorded-entity classification and recording-time window.
    Full totals precede the latest fifty event identities; retries never reappear.

    BUSINESS RULE activity_volume.rolling.coverage:
    Return UTC-aligned minute buckets with partial boundary/company-creation
    coverage. A quiet fully observed bucket is known zero, not a fabricated action.
    """
    # reality-rule: activity_volume.rolling.classification
    if type(minutes) is not int or minutes not in (5, 15, 60):
        raise InvalidOperation(code="shipping_observation_filter_invalid")
    tenant = get_tenant(session, tenant_id)
    end = (
        as_of
        or session.info.get("operations_snapshot_observed_at")
        or datetime.now(UTC)
    )
    if end.tzinfo is None:
        raise InvalidOperation(code="shipping_observation_filter_invalid")
    end = end.astimezone(UTC)
    start = end - timedelta(minutes=minutes)
    coverage = max(start, tenant.created_at)
    entities = _entities(tenant_id, start, end)
    bucket = func.floor(func.extract("epoch", entities.c.recorded_at) / 60) * 60
    rows = session.execute(
        select(bucket, entities.c.category, func.count()).group_by(
            bucket, entities.c.category
        )
    ).all()
    counts = {(int(at), category): count for at, category, count in rows}
    # reality-rule: activity_volume.rolling.coverage
    buckets = [
        {
            "start": datetime.fromtimestamp(at, UTC).isoformat(),
            "end": datetime.fromtimestamp(
                min(at + 60, end.timestamp()), UTC
            ).isoformat(),
            "partial": at < coverage.timestamp() or at + 60 > end.timestamp(),
            "counts": {key: counts.get((at, key), 0) for key in CATEGORIES},
        }
        for at in range(
            floor(start.timestamp() / 60) * 60, ceil(end.timestamp() / 60) * 60, 60
        )
    ]
    latest = details(session, tenant_id, start=start, end=end)
    for row in buckets:
        row["total"] = sum(row["counts"].values())
    totals = {key: sum(row["counts"][key] for row in buckets) for key in CATEGORIES}
    return {
        "observed_at": end.isoformat(),
        "start": start.isoformat(),
        "coverage_start": coverage.isoformat(),
        "bucket_seconds": 60,
        "minutes": minutes,
        "counts": totals,
        "total": latest["total"],
        "buckets": buckets,
        "events": latest["events"],
        "has_more": latest["has_more"],
    }
