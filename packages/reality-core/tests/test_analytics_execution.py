"""Evidence aggregates must preserve identity, grain, money and tenant boundaries."""

from decimal import Decimal

import pytest

from reality.services.analytics.execution import AnalyticsError, query
from reality.services.core import create_manual_order


def orders(session, business):
    return create_manual_order(
        session,
        business.tenant.id,
        "sales",
        "AN-001",
        business.company.id,
        business.customer.id,
        business.location.id,
        [
            {
                "item_id": business.item.id,
                "sku": business.item.sku,
                "quantity": "2",
                "unit_price": "3",
                "gross_amount": "7",
                "unit": "pcs",
            },
            {
                "item_id": business.item.id,
                "sku": business.item.sku,
                "quantity": "1",
                "unit_price": "4",
                "gross_amount": "5",
                "unit": "pcs",
            },
        ],
        "12",
        ordered_at="2026-02-10T10:00:00Z",
        document_date="2026-02-10",
    )


def request(**changes):
    return {
        "definition": {
            "dataset": "sales_order_lines",
            "dimensions": ["customer_id"],
            "measures": ["ordered_quantity", "stated_line_amount", "order_count"],
            **changes,
        }
    }


def test_exact_stated_values_distinct_orders_and_population_totals(session, business):
    orders(session, business)
    result = query(session, business.tenant.id, request())
    assert len(result["rows"]) == 1
    row = result["rows"][0]
    assert Decimal(row["ordered_quantity"]) == 3
    assert Decimal(row["stated_line_amount"]) == 12  # not price * quantity = 10
    assert row["order_count"] == 1
    assert row["customer_id"] == business.customer.id
    assert (
        result["metadata"]["history_scope"] == "matching_interpreted_retained_records"
    )


def test_empty_filtered_population_and_untrusted_fields(session, business):
    orders(session, business)
    result = query(
        session,
        business.tenant.id,
        request(where={"field": "customer_id", "op": "eq", "value": "foreign"}),
    )
    assert result["rows"] == []
    for change in [
        {"dimensions": ["tenant_id"]},
        {"measures": ["profit"]},
        {"where": {"field": "unit_price", "op": "contains", "value": "1"}},
    ]:
        with pytest.raises(AnalyticsError):
            query(session, business.tenant.id, request(**change))


def test_page_never_changes_population_total(session, business):
    orders(session, business)
    req = request(dimensions=["record_id"])
    req["page_size"] = 1
    result = query(session, business.tenant.id, req)
    assert len(result["rows"]) == 1 and result["page"]["has_more"]
    assert Decimal(result["population_totals"][0]["ordered_quantity"]) == 3
    req["cursor"] = result["page"]["next_cursor"]
    other = query(session, business.tenant.id, req)
    assert other["rows"][0]["record_id"] != result["rows"][0]["record_id"]


def test_pivot_totals_reaggregate_distinct_orders(session, business):
    orders(session, business)
    definition = {
        "dataset": "sales_order_lines",
        "dimensions": ["customer_id", "record_id"],
        "measures": ["order_count"],
        "presentation": {
            "kind": "pivot",
            "rows": ["customer_id"],
            "column": "record_id",
            "measures": ["order_count"],
        },
    }
    result = query(session, business.tenant.id, {"definition": definition})
    assert len(result["pivot"]["cells"]) == 2
    assert result["pivot"]["row_totals"][0]["order_count"] == 1
    assert result["pivot"]["totals"][0]["order_count"] == 1


def test_production_boundary_is_repeatable_read_and_read_only():
    from unittest.mock import patch

    from sqlalchemy import text

    from reality.services.analytics.execution import execute

    tenant_id = "no_business_records_needed"

    def observe(session, tenant_id, arguments):
        assert session.scalar(text("SHOW transaction_read_only")) == "on"
        assert session.scalar(text("SHOW transaction_isolation")) == "repeatable read"
        return {"metadata": {}}

    with patch("reality.services.analytics.execution.query", observe):
        assert (
            execute(tenant_id, {})["metadata"]["consistency"]
            == "repeatable_read_request"
        )


def test_cancelled_query_returns_no_partial_result():
    from threading import Event

    from reality.services.analytics.execution import execute

    cancelled = Event()
    cancelled.set()
    with pytest.raises(AnalyticsError) as error:
        execute("not_reached", request(), cancellation=cancelled)
    assert error.value.code == "query_cancelled"


def test_period_difference_keeps_zero_baseline_unknown(session, business):
    orders(session, business)
    result = query(
        session,
        business.tenant.id,
        {
            "definition": {
                "dataset": "sales_orders",
                "dimensions": ["customer_id"],
                "measures": ["stated_order_amount"],
                "time": {
                    "field": "ordered_at",
                    "timezone": "UTC",
                    "window": {"kind": "iso_week", "year": 2026, "week": 7},
                },
                "compare": "previous_period",
                "sort": [{"field": "change:stated_order_amount", "direction": "desc"}],
            }
        },
    )
    row = result["rows"][0]
    assert Decimal(row["change:stated_order_amount"]) == 12
    assert row["percent_change:stated_order_amount"] is None


def test_currency_and_unit_partitions_preserve_zero_and_exact_totals(session, business):
    for index, (currency, unit, amount) in enumerate(
        [("EUR", "pcs", "0"), ("USD", "kg", "1.1234")]
    ):
        create_manual_order(
            session,
            business.tenant.id,
            "sales",
            f"PART-{index}",
            business.company.id,
            business.customer.id,
            business.location.id,
            [
                {
                    "item_id": business.item.id,
                    "quantity": "1",
                    "unit_price": "0",
                    "gross_amount": amount,
                    "unit": unit,
                }
            ],
            amount,
            currency=currency,
        )
    result = query(
        session,
        business.tenant.id,
        request(
            measures=["stated_line_amount", "ordered_quantity"],
            dimensions=["customer_id"],
        ),
    )
    assert {(row["currency"], row["unit"]) for row in result["rows"]} == {
        ("EUR", "pcs"),
        ("USD", "kg"),
    }
    assert {Decimal(row["stated_line_amount"]) for row in result["rows"]} == {
        Decimal(0),
        Decimal("1.1234"),
    }
    assert result["metadata"]["missing_values"]["stated_line_amount"] == 0


def test_real_observation_executes_no_writes(scheduled_database):
    from sqlalchemy import event

    from reality.services.analytics.execution import execute

    engine, factory, tenant_id, _actor_id = scheduled_database
    statements = []

    def record(connection, cursor, statement, parameters, context, executemany):
        statements.append(statement.lstrip().split()[0].upper())

    event.listen(engine, "before_cursor_execute", record)
    try:
        result = execute(tenant_id, request(), session_factory=factory)
        assert result["rows"] == []
        assert not {"INSERT", "UPDATE", "DELETE", "CREATE", "ALTER"} & set(statements)
    finally:
        event.remove(engine, "before_cursor_execute", record)
