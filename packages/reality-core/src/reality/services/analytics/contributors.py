"""Fresh observations of supporting records for one analytical value."""

import base64
import json
from datetime import UTC, datetime

from pydantic import ValidationError
from sqlalchemy import func, literal, select

from reality.domain.analytics import ContributorQuery, resolve_window
from reality.services.analytics.budget import check_budget
from reality.services.analytics.catalog import CATALOG
from reality.services.analytics.execution import (
    AnalyticsError,
    _relation,
    canonical,
    checked_definition,
    fingerprint,
    mappings,
    partitions,
    predicate,
    value_for,
)
from reality.services.core import get_tenant


def contributors(session, tenant_id, arguments):
    try:
        request = ContributorQuery.model_validate(arguments)
    except ValidationError as error:
        raise AnalyticsError(str(error)) from error
    d = request.definition
    checked_definition({"definition": d.model_dump(mode="json")})
    if request.measure not in d.measures:
        raise AnalyticsError("Select a measure from the executed analysis.")
    allowed = set(d.dimensions + partitions(d))
    if set(request.group) - allowed:
        raise AnalyticsError("Contributor group does not belong to this analysis.")
    check_budget()
    get_tenant(session, tenant_id)
    observed = datetime.now(UTC)
    source = _relation(session, tenant_id, d)
    conditions = []
    if d.where:
        conditions.append(
            predicate(
                d.where,
                source,
                {**CATALOG[d.dataset], "key": d.dataset, "tenant_id": tenant_id},
            )
        )
    if d.time:
        start, end = resolve_window(d.time, observed)
        conditions.extend(
            [source.c[d.time.field] >= start, source.c[d.time.field] < end]
        )
    for field, value in request.group.items():
        conditions.append(
            source.c[field].is_(None)
            if value is None
            else source.c[field] == value_for(field, value)
        )
    relation = select(source).where(*conditions).subquery()
    # Distinct counts explain the counted identity, not every joined evidence line.
    identity_column = {"order_count": "order_id", "customer_count": "customer_id"}.get(
        request.measure
    )
    if identity_column:
        identity_kind = "document" if identity_column == "order_id" else "party"
        statement = (
            select(
                relation.c[identity_column].label("record_id"),
                literal(identity_kind).label("record_kind"),
            )
            .where(relation.c[identity_column].is_not(None))
            .distinct()
        )
    else:
        statement = select(relation)
        value_column = (
            "unit_price"
            if request.measure in {"min_price", "max_price"}
            else request.measure
        )
        if value_column in relation.c:
            statement = statement.where(relation.c[value_column].is_not(None))
    records = statement.subquery()
    count = session.scalar(select(func.count()).select_from(records))
    scope = fingerprint(
        [tenant_id, d.model_dump(mode="json"), request.group, request.measure]
    )
    offset = 0
    if request.cursor:
        try:
            cursor = json.loads(base64.urlsafe_b64decode(request.cursor))
            if (
                cursor["scope"] != scope
                or type(cursor["offset"]) is not int
                or not 0 <= cursor["offset"] <= 10000000
            ):
                raise ValueError()
            offset = cursor["offset"]
        except (ValueError, TypeError, KeyError, UnicodeError) as error:
            raise AnalyticsError(
                "Invalid contributor cursor.", "invalid_cursor"
            ) from error
    keys = [
        key for key in ("record_id", "product_id", "location_id") if key in records.c
    ]
    rows = mappings(
        session,
        select(records)
        .order_by(*(records.c[key] for key in keys))
        .offset(offset)
        .limit(request.page_size),
    )
    more = offset + len(rows) < count
    cursor = (
        base64.urlsafe_b64encode(
            canonical({"scope": scope, "offset": offset + len(rows)}).encode()
        ).decode()
        if more
        else None
    )
    return {
        "records": rows,
        "total": count,
        "has_more": more,
        "next_cursor": cursor,
        "metadata": {
            "observed_at": observed.isoformat(),
            "consistency": "fresh_observation",
            "tenant_id": tenant_id,
        },
        "definition": d.model_dump(mode="json"),
        "measure": request.measure,
    }
