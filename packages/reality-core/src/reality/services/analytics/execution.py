"""Allowlisted, decimal-safe analytical execution; output pages never define totals."""

from __future__ import annotations

import base64
import hashlib
import json
import time
from datetime import UTC, datetime
from decimal import Decimal
from decimal import InvalidOperation as DecimalError

from pydantic import ValidationError
from sqlalchemy import and_, exists, func, or_, select
from sqlalchemy.exc import DBAPIError

from reality.domain.analytics import AnalyticsQuery, resolve_window
from reality.services.analytics.catalog import CATALOG, FIELDS, MEASURES, catalog
from reality.services.analytics.orders import order_relation, source_coverage
from reality.services.core import InvalidOperation, get_tenant


class AnalyticsError(InvalidOperation):
    def __init__(self, message: str, code: str = "invalid_definition"):
        super().__init__(message)
        self.code = code


def encode(value):
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    raise TypeError(type(value).__name__)


def canonical(value):
    return json.dumps(value, default=encode, sort_keys=True, separators=(",", ":"))


def fingerprint(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def checked_definition(arguments):
    try:
        request = AnalyticsQuery.model_validate(arguments)
    except ValidationError as error:
        raise AnalyticsError(str(error)) from error
    d = request.definition
    if d.dataset not in CATALOG:
        raise AnalyticsError(
            "This analytical perspective is not supported.", "unsupported_combination"
        )
    info = CATALOG[d.dataset]
    if any(key not in info["fields"] for key in d.dimensions) or any(
        key not in info["measures"] for key in d.measures
    ):
        raise AnalyticsError(
            "Choose dimensions and measures from this dataset's catalog.",
            "unsupported_combination",
        )
    if d.time and (
        d.time.field not in info["fields"] or FIELDS[d.time.field][1] != "datetime"
    ):
        raise AnalyticsError("Choose a supported date field.")
    if (
        isinstance(d.compare, type(d.time))
        and d.compare is not None
        and d.compare.field != d.time.field
    ):
        raise AnalyticsError("Comparison periods must use the same date field.")
    if d.presentation.kind == "pivot":
        p = d.presentation
        if (
            not p.rows
            or not p.column
            or p.column in p.rows
            or set(d.dimensions) != {*p.rows, p.column}
            or any(m not in d.measures for m in p.measures)
        ):
            raise AnalyticsError(
                "Choose distinct selected row and column dimensions for the pivot."
            )
    return request


def value_for(field, value):
    kind = FIELDS[field][1]
    try:
        if kind == "decimal":
            result = Decimal(str(value))
            if not result.is_finite():
                raise ValueError()
            return result
        if kind == "datetime":
            result = datetime.fromisoformat(str(value))
            if result.tzinfo is None:
                raise ValueError()
            return result
        if not isinstance(value, str):
            raise TypeError()
        return value
    except (ValueError, TypeError, DecimalError) as error:
        raise AnalyticsError(f"Invalid value for {FIELDS[field][0]}.") from error


def predicate(node, relation, info):
    if node.relationship:
        permitted = (
            node.relationship == "purchases"
            and info["key"] == "customer_purchases"
            or node.relationship == "order_lines"
            and info["key"] in {"sales_orders", "purchase_orders"}
            or node.relationship == "outbound"
            and info["key"] == "inventory"
        )
        if not permitted:
            raise AnalyticsError(
                "This relationship is not available in the selected perspective."
            )
        from reality.domain.analytics import AnalyticsDefinition

        dataset = (
            "purchase_order_lines"
            if info["key"] == "purchase_orders"
            else "sales_order_lines"
        )
        related = order_relation(
            info["tenant_id"],
            AnalyticsDefinition(
                dataset=dataset, measures=["row_count"], time=node.time
            ),
        )
        if node.relationship == "outbound":
            from reality.services.analytics.finance import return_relation

            dataset = "outbound_movements"
            related = return_relation(info["tenant_id"], outbound=True)
        key = (
            "product_id"
            if node.relationship == "outbound"
            else "customer_id"
            if node.relationship == "purchases"
            else "order_id"
        )
        conditions = [related.c[key] == relation.c[key]]
        if node.relationship == "outbound":
            conditions.append(related.c.location_id == relation.c.location_id)
        if node.where:
            conditions.append(
                predicate(
                    node.where,
                    related,
                    {
                        **CATALOG[dataset],
                        "key": dataset,
                        "tenant_id": info["tenant_id"],
                    },
                )
            )
        if node.time:
            start, end = resolve_window(node.time, datetime.now(UTC))
            conditions.extend(
                [related.c[node.time.field] >= start, related.c[node.time.field] < end]
            )
        expression = exists(
            select(related.c[key]).where(*conditions).correlate(relation)
        )
        return ~expression if node.op == "not_exists" else expression
    if node.all is not None:
        return and_(*(predicate(child, relation, info) for child in node.all))
    if node.any is not None:
        return or_(*(predicate(child, relation, info) for child in node.any))
    field = node.field
    if field not in info["fields"] + info.get("filter_fields", []):
        raise AnalyticsError("Filter field is not available in this dataset.")
    descriptor = next(
        f
        for f in catalog(info["key"])["datasets"][0]["dimensions"]
        if f["key"] == field
    )
    if node.op not in descriptor["operators"]:
        raise AnalyticsError("This operator does not apply to the selected field.")
    column = relation.c[field]
    if node.op == "is_missing":
        return column.is_(None)
    if node.op == "is_present":
        return column.is_not(None)
    if node.op in {"in", "not_in"}:
        result = column.in_([value_for(field, v) for v in node.values])
        return ~result if node.op == "not_in" else result
    value = value_for(field, node.value)
    if node.op == "contains":
        return column.icontains(value, autoescape=True)
    return {
        "eq": lambda: column == value,
        "ne": lambda: column != value,
        "gte": lambda: column >= value,
        "gt": lambda: column > value,
        "lte": lambda: column <= value,
        "lt": lambda: column < value,
    }[node.op]()


def partitions(definition):
    result = []
    for measure in definition.measures:
        part = MEASURES[measure][2]
        if part in {"currency", "currency_unit"} and "currency" not in result:
            result.append("currency")
        if part in {"unit", "currency_unit"} and "unit" not in result:
            result.append("unit")
    return result


def measure_expression(name, relation):
    if name == "row_count":
        return func.count()
    if name in {"order_count", "customer_count"}:
        return func.count(
            func.distinct(
                relation.c["order_id" if name == "order_count" else "customer_id"]
            )
        )
    if name in {"min_price", "max_price"}:
        return (func.min if name == "min_price" else func.max)(relation.c.unit_price)
    return func.sum(relation.c[name])


LABEL_FIELDS = {
    "customer_id": "customer",
    "supplier_id": "supplier",
    "party_id": "party",
    "product_id": "product",
    "location_id": "location",
    "order_id": "order",
}


def aggregate(relation, dimensions, measures):
    fields = [relation.c[f] for f in dimensions]
    labels = [
        func.min(relation.c[LABEL_FIELDS[f]]).label(LABEL_FIELDS[f])
        for f in dimensions
        if f in LABEL_FIELDS and LABEL_FIELDS[f] in relation.c
    ]
    return (
        select(
            *fields,
            *labels,
            *(measure_expression(m, relation).label(m) for m in measures),
        )
        .select_from(relation)
        .group_by(*fields)
    )


def mappings(session, statement):
    return [
        json.loads(canonical(dict(row)))
        for row in session.execute(statement).mappings()
    ]


def _relation(session, tenant_id, d):
    if d.dataset == "product_suppliers":
        from reality.services.analytics.orders import supplier_history_relation

        return supplier_history_relation(tenant_id, d)
    if d.dataset in {"returns", "outbound_movements"}:
        from reality.services.analytics.finance import return_relation

        return return_relation(tenant_id, outbound=d.dataset == "outbound_movements")
    if d.dataset == "customer_purchases":
        from reality.services.analytics.orders import customer_relation

        return customer_relation(tenant_id, d)
    if d.dataset == "order_product_pairs":
        from reality.services.analytics.orders import pair_relation

        return pair_relation(session, tenant_id, d)
    if d.dataset.startswith(("sales_", "purchase_")):
        return order_relation(tenant_id, d)
    from reality.services.analytics.operations import operational_relation

    return operational_relation(session, tenant_id, d)


def query(
    session,
    tenant_id: str,
    arguments: dict,
    *,
    observed_at=None,
    deadline=None,
    all_rows=False,
):
    started = time.monotonic()
    deadline = deadline or started + 30
    observed = observed_at or datetime.now(UTC)
    request = checked_definition(arguments)
    d = request.definition
    get_tenant(session, tenant_id)
    info = {**CATALOG[d.dataset], "key": d.dataset, "tenant_id": tenant_id}
    source = _relation(session, tenant_id, d)
    conditions = [predicate(d.where, source, info)] if d.where else []
    window = None
    if d.time:
        start, end = resolve_window(d.time, observed)
        window = {
            "start": start.isoformat(),
            "end": end.isoformat(),
            "timezone": d.time.timezone,
            "field": d.time.field,
        }
        conditions += [source.c[d.time.field] >= start, source.c[d.time.field] < end]
    relation = select(source).where(*conditions).subquery()
    required = partitions(d)
    dimensions = list(dict.fromkeys([*d.dimensions, *required]))
    statement = aggregate(relation, dimensions, d.measures)
    grouped = statement.subquery()
    total_groups = session.scalar(select(func.count()).select_from(grouped))
    if total_groups > 10000:
        raise AnalyticsError(
            "More than 10,000 groups. Narrow the period or add a filter.",
            "query_too_broad",
        )
    normalized = d.model_dump(mode="json")
    identity = fingerprint([tenant_id, normalized])
    offset = 0
    if request.cursor:
        try:
            cursor = json.loads(base64.urlsafe_b64decode(request.cursor))
            if (
                cursor["scope"] != identity
                or type(cursor["offset"]) is not int
                or not 0 <= cursor["offset"] <= 10000
            ):
                raise ValueError()
            offset = cursor["offset"]
        except (ValueError, TypeError, KeyError, UnicodeError) as error:
            raise AnalyticsError(
                "Invalid cursor for this report.", "invalid_cursor"
            ) from error
    period_changes = bool(d.compare) and not any(
        key.startswith("ordered_") or key == "due_week" for key in dimensions
    )
    change_fields = (
        [prefix + m for m in d.measures for prefix in ("change:", "percent_change:")]
        if period_changes
        else []
    )
    order = []
    for sort in d.sort:
        if sort.field in change_fields:
            continue
        if sort.field not in dimensions + d.measures:
            raise AnalyticsError("Sort by a selected dimension or measure.")
        order.append(
            (
                grouped.c[sort.field].desc()
                if sort.direction == "desc"
                else grouped.c[sort.field].asc()
            ).nulls_last()
        )
    order += [grouped.c[f].asc().nulls_last() for f in dimensions]
    rows = mappings(
        session,
        select(grouped)
        .order_by(*order)
        .offset(0 if period_changes else offset)
        .limit(10000 if all_rows or period_changes else request.page_size),
    )
    totals = mappings(session, aggregate(relation, required, d.measures))
    missing = {}
    for name in d.measures:
        column = "unit_price" if name in {"min_price", "max_price"} else name
        if column in relation.c:
            missing[name] = session.scalar(
                select(func.count())
                .select_from(relation)
                .where(relation.c[column].is_(None))
            )
    undated = (
        session.scalar(
            select(func.count())
            .select_from(source)
            .where(
                *(conditions[:1] if d.where else []), source.c[d.time.field].is_(None)
            )
        )
        if d.time
        else 0
    )
    pivot = None
    if d.presentation.kind == "pivot":
        p = d.presentation
        pivot_measures = p.measures or d.measures[:2]
        row_dimensions = list(dict.fromkeys([*p.rows, *required]))
        cell_dimensions = list(dict.fromkeys([*row_dimensions, p.column]))
        cells = mappings(session, aggregate(relation, cell_dimensions, pivot_measures))
        if (
            len(cells) * len(pivot_measures) > 5000
            or len({canonical(row[p.column]) for row in cells}) > 50
        ):
            raise AnalyticsError(
                "Pivot exceeds 50 columns or 5,000 cells. Narrow the analysis.",
                "query_too_broad",
            )
        pivot = {
            "row_dimensions": row_dimensions,
            "column_dimension": p.column,
            "measures": pivot_measures,
            "cells": cells,
            "row_totals": mappings(
                session, aggregate(relation, row_dimensions, pivot_measures)
            ),
            "column_totals": mappings(
                session,
                aggregate(
                    relation, list(dict.fromkeys([p.column, *required])), pivot_measures
                ),
            ),
            "totals": totals,
        }
    comparison = None
    if d.compare:
        if d.compare == "previous_period":
            local_start = start.astimezone(
                __import__("zoneinfo").ZoneInfo(d.time.timezone)
            ).date()
            local_end = end.astimezone(
                __import__("zoneinfo").ZoneInfo(d.time.timezone)
            ).date()
            prior = d.time.model_copy(
                update={
                    "window": d.time.window.model_validate(
                        {
                            "kind": "absolute",
                            "start": local_start - (local_end - local_start),
                            "end": local_start,
                        }
                    )
                }
            )
        else:
            prior = d.compare
        prior_request = d.model_copy(
            update={
                "time": prior,
                "compare": None,
                "sort": [sort for sort in d.sort if sort.field not in change_fields],
            }
        ).model_dump(mode="json")
        comparison = query(
            session,
            tenant_id,
            {"definition": prior_request, "page_size": request.page_size},
            observed_at=observed,
            deadline=deadline,
            all_rows=period_changes,
        )
        if period_changes:
            from reality.services.analytics.comparison import changes, order_changes

            combined = changes(rows, comparison["rows"], dimensions, d.measures)
            if len(combined) > 10000:
                raise AnalyticsError(
                    "Comparison exceeds 10,000 groups. Narrow the analysis.",
                    "query_too_broad",
                )
            total_groups = len(combined)
            rows = order_changes(combined, d.sort, dimensions)[
                offset : offset + (10000 if all_rows else request.page_size)
            ]
    if time.monotonic() > deadline:
        raise AnalyticsError(
            "The analysis exceeded its execution limit.", "query_timeout"
        )
    more = offset + len(rows) < total_groups
    cursor = (
        base64.urlsafe_b64encode(
            canonical({"scope": identity, "offset": offset + len(rows)}).encode()
        ).decode()
        if more
        else None
    )
    columns = [
        {
            "key": key,
            "label": (FIELDS[key][0] if key in FIELDS else MEASURES[key][0]),
            "type": FIELDS[key][1]
            if key in FIELDS
            else "integer"
            if MEASURES[key][1] in {"count", "distinct"}
            else "decimal",
        }
        for key in [*dimensions, *d.measures]
    ]
    if period_changes:
        for measure in d.measures:
            columns.extend(
                [
                    {
                        "key": "change:" + measure,
                        "label": "Change · " + MEASURES[measure][0],
                        "type": "decimal",
                    },
                    {
                        "key": "percent_change:" + measure,
                        "label": "Change (%) · " + MEASURES[measure][0],
                        "type": "decimal",
                    },
                ]
            )
    handoff = {"version": 1, "tenant_id": tenant_id, "definition": normalized}
    from urllib.parse import quote

    handoff_url = (
        "/app/analytics?tenant="
        + quote(tenant_id, safe="")
        + "&analytics_view=explore#analytics="
        + base64.urlsafe_b64encode(canonical(handoff).encode()).decode().rstrip("=")
    )
    return {
        "open_in_reports": {**handoff, "url": handoff_url},
        "version": 1,
        "executed_definition": normalized,
        "definition_fingerprint": identity,
        "columns": columns,
        "rows": rows,
        "population_totals": totals,
        "comparison": comparison,
        "pivot": pivot,
        "page": {"has_more": more, "next_cursor": cursor, "total": total_groups},
        "metadata": {
            "observed_at": observed.isoformat(),
            "tenant_id": tenant_id,
            "resolved_window": window,
            "history_scope": "matching_interpreted_retained_records",
            "source_coverage": source_coverage(session, tenant_id),
            "upstream_freshness": "unknown",
            "missing_values": missing,
            "undated_excluded": undated,
            "continuation": "fresh_observation",
            "duration_ms": round((time.monotonic() - started) * 1000),
            "persistence": {
                "business_writes": False,
                "projection_writes": False,
                "transport_telemetry": "possible",
            },
        },
    }


def execute(
    tenant_id,
    arguments,
    *,
    session_factory=None,
    operation="query",
    cancellation=None,
    timeout_seconds=30,
):
    """Own the analytical transaction, deadline and cancellation; never caller writes."""
    from threading import Event, Thread, Timer

    from sqlalchemy import event, text

    from reality.db.core import Session
    from reality.services.analytics.budget import CANCELLED, DEADLINE, check_budget
    from reality.services.analytics.contributors import contributors
    from reality.services.analytics.exports import export_csv

    factory = session_factory or Session
    deadline_token = DEADLINE.set(time.monotonic() + timeout_seconds)
    cancel_token = CANCELLED.set(cancellation)
    try:
        with factory() as session:
            connection = session.connection(
                execution_options={
                    "isolation_level": "REPEATABLE READ",
                    "postgresql_readonly": True,
                }
            )
            driver = connection.connection.driver_connection
            timer = Timer(timeout_seconds, driver.cancel)
            timer.daemon = True

            def before_sql(*args):
                check_budget()

            event.listen(connection, "before_cursor_execute", before_sql)
            stopped = Event()

            def watch_cancellation():
                while not stopped.wait(0.05):
                    if cancellation is not None and cancellation.is_set():
                        driver.cancel()
                        return

            watcher = (
                Thread(target=watch_cancellation, daemon=True)
                if cancellation is not None
                else None
            )
            timer.start()
            if watcher:
                watcher.start()
            try:
                session.execute(
                    text("SELECT set_config('statement_timeout', :timeout, true)"),
                    {"timeout": str(max(1, int(timeout_seconds * 1000)))},
                )
                with session.no_autoflush:
                    handler = {
                        "query": query,
                        "contributors": contributors,
                        "export": export_csv,
                    }[operation]
                    result = handler(session, tenant_id, arguments)
                check_budget()
                result["metadata"]["consistency"] = "repeatable_read_request"
                return result
            except DBAPIError as error:
                if getattr(error.orig, "sqlstate", None) == "57014":
                    check_budget()
                    raise AnalyticsError(
                        "The analysis was cancelled or exceeded its execution limit.",
                        "query_timeout",
                    ) from error
                raise
            finally:
                stopped.set()
                timer.cancel()
                timer.join()
                if watcher:
                    watcher.join()
                event.remove(connection, "before_cursor_execute", before_sql)
                session.rollback()
    finally:
        DEADLINE.reset(deadline_token)
        CANCELLED.reset(cancel_token)
