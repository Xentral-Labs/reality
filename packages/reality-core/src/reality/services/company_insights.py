"""Current delivery position and retained activity, with matching contributors."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from reality.db.core import Commitment, Item, Movement, MovementCorrection, Party
from reality.services.delivery_reads import effective_value, fulfillment_expressions


def _window(days: int, observed_at: datetime | None):
    if days not in {7, 30, 90}:
        raise ValueError("Period must be 7, 30 or 90 days.")
    observed = (observed_at or datetime.now(UTC)).astimezone(UTC)
    start = observed.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(
        days=days - 1
    )
    return observed, start


def _records(
    tenant_id: str,
    metric: str,
    observed: datetime,
    start: datetime,
    day: str | None = None,
):
    if metric not in {
        "open",
        "fully_reserved",
        "needs_reservation",
        "overdue",
        "unknown_due",
        "created",
        "shipped",
    }:
        raise ValueError("Unknown analytics metric.")
    activity = metric in {"created", "shipped"}
    end = observed
    if day is not None:
        if not activity:
            raise ValueError("Day selection applies only to activity.")
        selected = datetime.strptime(day, "%Y-%m-%d").replace(tzinfo=UTC)
        if selected < start or selected.date() > observed.date():
            raise ValueError("Selected day is outside the period.")
        start, end = selected, min(selected + timedelta(days=1), observed)
    if metric == "shipped":
        corrected = (
            select(MovementCorrection.id)
            .where(
                MovementCorrection.tenant_id == tenant_id,
                or_(
                    MovementCorrection.original_movement_id == Movement.id,
                    MovementCorrection.compensating_movement_id == Movement.id,
                ),
            )
            .exists()
        )
        return select(Movement.id, Movement.occurred_at.label("at")).where(
            Movement.tenant_id == tenant_id,
            Movement.type == "shipment",
            Movement.quantity > 0,
            ~corrected,
            Movement.occurred_at >= start,
            Movement.occurred_at < end,
        ), "movement"
    statement = select(Commitment.id, Commitment.created_at.label("at")).where(
        Commitment.tenant_id == tenant_id,
        Commitment.type == "customer_delivery",
    )
    if activity:
        return statement.where(
            Commitment.created_at >= start, Commitment.created_at < end
        ), "commitment"
    reserved, _, remaining = fulfillment_expressions()
    statement = statement.where(Commitment.status == "open", remaining > 0)
    filters = {
        "fully_reserved": reserved >= remaining,
        "needs_reservation": reserved < remaining,
        "overdue": effective_value("due_at") < observed,
        "unknown_due": effective_value("due_at").is_(None),
    }
    if metric in filters:
        statement = statement.where(filters[metric])
    return statement, "commitment"


def company_insights(
    session: Session,
    tenant_id: str,
    *,
    days: int = 30,
    observed_at: datetime | None = None,
) -> dict[str, Any]:
    from reality.services.core import get_tenant

    get_tenant(session, tenant_id)
    observed, start = _window(days, observed_at)
    position = {}
    for metric in (
        "open",
        "fully_reserved",
        "needs_reservation",
        "overdue",
        "unknown_due",
    ):
        query, _ = _records(tenant_id, metric, observed, start)
        position[metric] = int(
            session.scalar(select(func.count()).select_from(query.subquery())) or 0
        )
    position["coverage_percent"] = (
        str(
            (Decimal(position["fully_reserved"]) * 100 / position["open"]).quantize(
                Decimal("0.1")
            )
        )
        if position["open"]
        else None
    )
    series = {
        (start + timedelta(days=index)).date().isoformat(): {"created": 0, "shipped": 0}
        for index in range(days)
    }
    for metric in ("created", "shipped"):
        query, _ = _records(tenant_id, metric, observed, start)
        records = query.subquery()
        date = func.date(func.timezone("UTC", records.c.at))
        for day, count in session.execute(
            select(date, func.count()).group_by(date).select_from(records)
        ):
            series[day.isoformat()][metric] = count
    return {
        "position": position,
        "series": [{"date": day, **values} for day, values in series.items()],
        "window": {"days": days, "start": start, "end": observed, "timezone": "UTC"},
        "observed_at": observed,
        "definitions": {
            "created": "Customer delivery commitments by creation time",
            "shipped": "Positive shipment movements by occurrence time, excluding corrected originals and compensations",
            "coverage_percent": "Fully reserved open delivery commitments / open delivery commitments",
        },
        "coverage": "Retained records only; external history may be incomplete. The two series count different record families, not order conversion. Current position is independent of the chart period.",
    }


def insight_contributors(
    session: Session,
    tenant_id: str,
    *,
    metric: str,
    days: int = 30,
    day: str | None = None,
    page: int = 1,
    size: int = 50,
    observed_at: datetime | None = None,
) -> dict[str, Any]:
    from reality.services.core import get_tenant

    get_tenant(session, tenant_id)
    observed, start = _window(days, observed_at)
    query, kind = _records(tenant_id, metric, observed, start, day)
    total = int(session.scalar(select(func.count()).select_from(query.subquery())) or 0)
    size = max(1, min(size, 100))
    pages = max(1, (total + size - 1) // size)
    page = max(1, min(page, pages))
    rows = list(
        session.execute(
            query.order_by("at", "id").offset((page - 1) * size).limit(size)
        )
    )
    identities = [identity for identity, _ in rows]
    model = Commitment if kind == "commitment" else Movement
    labels_query = (
        select(model.id, Item.name)
        .outerjoin(Item, (Item.tenant_id == tenant_id) & (Item.id == model.item_id))
        .where(model.tenant_id == tenant_id, model.id.in_(identities))
    )
    if kind == "commitment":
        labels_query = labels_query.add_columns(Party.name).outerjoin(
            Party, (Party.tenant_id == tenant_id) & (Party.id == Commitment.to_party_id)
        )
    names = {
        row[0]: " · ".join(str(value) for value in row[1:] if value)
        for row in session.execute(labels_query)
    }
    return {
        "items": [
            {
                "id": identity,
                "kind": kind,
                "at": at,
                "label": names.get(identity) or identity,
            }
            for identity, at in rows
        ],
        "page": {
            "number": page,
            "size": size,
            "total": total,
            "pages": pages,
            "has_next": page < pages,
            "has_previous": page > 1,
        },
        "scope": {"tenant_id": tenant_id, "metric": metric, "days": days, "day": day},
        "observed_at": observed,
    }
