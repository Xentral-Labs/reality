"""Deterministic retained-history meanings for the SMB question contract."""

from test_analytics_execution import orders

from reality.services.analytics.execution import query


def test_first_observed_purchase_and_product_existence(session, business):
    orders(session, business)
    definition = {
        "dataset": "customer_purchases",
        "dimensions": ["customer_id", "first_order_at"],
        "measures": ["customer_count"],
        "where": {
            "all": [
                {
                    "relationship": "purchases",
                    "op": "exists",
                    "where": {
                        "field": "product_id",
                        "op": "eq",
                        "value": business.item.id,
                    },
                },
                {
                    "relationship": "purchases",
                    "op": "not_exists",
                    "where": {
                        "field": "product_id",
                        "op": "eq",
                        "value": "unobserved_product",
                    },
                },
            ]
        },
    }
    result = query(session, business.tenant.id, {"definition": definition})
    assert result["rows"][0]["customer_count"] == 1
    assert result["rows"][0]["first_order_at"].startswith("2026-02-10")


def test_product_pairs_never_pair_an_item_with_itself(session, business):
    orders(session, business)
    result = query(
        session,
        business.tenant.id,
        {
            "definition": {
                "dataset": "order_product_pairs",
                "dimensions": ["product_id", "product_b_id"],
                "measures": ["order_count"],
            }
        },
    )
    assert result["rows"] == []


def test_due_week_groups_are_discoverable():
    from reality.services.analytics.catalog import catalog

    fields = {f["key"] for f in catalog("open_items")["datasets"][0]["dimensions"]}
    assert {"due_week", "currency", "side"} <= fields


def test_billing_and_open_items_use_canonical_partial_invoice(session, business):
    from decimal import Decimal

    from test_multi_position_invoices import order
    from test_partial_invoicing_rebilling import invoice

    lines = order(session, business, "sales")
    invoice(session, business, lines[0])
    billing = query(
        session,
        business.tenant.id,
        {
            "definition": {
                "dataset": "order_billing",
                "dimensions": ["record_id"],
                "measures": ["billed_quantity"],
            }
        },
    )
    assert (
        Decimal(
            next(r for r in billing["rows"] if r["record_id"] == lines[0].id)[
                "billed_quantity"
            ]
        )
        == 1
    )
    open_items = query(
        session,
        business.tenant.id,
        {
            "definition": {
                "dataset": "open_items",
                "dimensions": ["side", "due_week"],
                "measures": ["open_amount"],
            }
        },
    )
    assert sum(Decimal(r["open_amount"]) for r in open_items["rows"]) == Decimal(
        "101.1234"
    )


def test_unallocated_payment_filter_preserves_recorded_values(session, business):
    from decimal import Decimal

    from reality.services.core import record_customer_payment

    record_customer_payment(session, business.tenant.id, business.customer.id, "125")
    result = query(
        session,
        business.tenant.id,
        {
            "definition": {
                "dataset": "payments",
                "dimensions": ["party_id"],
                "measures": ["allocated", "unallocated"],
                "where": {"field": "unallocated", "op": "gt", "value": "0"},
            }
        },
    )
    assert Decimal(result["rows"][0]["unallocated"]) == 125
    assert Decimal(result["rows"][0]["allocated"]) == 0


def test_idle_stock_and_company_demand_have_separate_grains(session, business):
    from decimal import Decimal

    orders(session, business)
    demand = query(
        session,
        business.tenant.id,
        {
            "definition": {
                "dataset": "inventory_demand",
                "dimensions": ["product_id"],
                "measures": ["open_demand", "stock_shortfall"],
            }
        },
    )
    assert Decimal(demand["rows"][0]["open_demand"]) == 3
    assert Decimal(demand["rows"][0]["stock_shortfall"]) == 3
    idle = query(
        session,
        business.tenant.id,
        {
            "definition": {
                "dataset": "inventory",
                "dimensions": ["product_id"],
                "measures": ["physical"],
                "where": {
                    "relationship": "outbound",
                    "op": "not_exists",
                    "time": {
                        "field": "occurred_at",
                        "timezone": "UTC",
                        "window": {"kind": "last_days", "count": 90},
                    },
                },
            }
        },
    )
    assert idle["rows"][0]["product_id"] == business.item.id


def test_exactly_one_observed_supplier_is_not_market_dependence(session, business):
    from test_multi_position_invoices import order

    order(session, business, "purchase")
    result = query(
        session,
        business.tenant.id,
        {
            "definition": {
                "dataset": "product_suppliers",
                "dimensions": ["product_id", "supplier_id"],
                "measures": ["row_count"],
                "where": {"field": "observed_supplier_count", "op": "eq", "value": "1"},
            }
        },
    )
    assert all(row["supplier_id"] == business.supplier.id for row in result["rows"])
    assert result["rows"]


def test_replay_and_pending_shopify_version_keep_interpreted_order(session, business):
    from test_shopify_update_guard import changed_payload, enqueue, payload

    from reality.services.core import ingest_shopify_order

    ingest_shopify_order(
        session,
        business.tenant.id,
        payload(),
        business.company.id,
        business.customer.id,
        business.location.id,
    )
    ingest_shopify_order(
        session,
        business.tenant.id,
        payload(),
        business.company.id,
        business.customer.id,
        business.location.id,
    )
    enqueue(session, business, changed_payload())
    result = query(
        session,
        business.tenant.id,
        {
            "definition": {
                "dataset": "sales_orders",
                "dimensions": [],
                "measures": ["order_count"],
            }
        },
    )
    assert result["rows"][0]["order_count"] == 1
    assert (
        result["metadata"]["source_coverage"]["retained_orders_with_newer_sources"] == 1
    )
    lines = query(
        session,
        business.tenant.id,
        {
            "definition": {
                "dataset": "sales_order_lines",
                "dimensions": [],
                "measures": ["stated_line_amount"],
            }
        },
    )
    assert lines["rows"][0]["stated_line_amount"] is None


def test_restricted_questions_have_explicit_narrower_meanings():
    from reality.services.analytics.catalog import catalog

    meanings = catalog()["restricted_meanings"]
    assert set(meanings) == {"Q13", "Q14", "Q15", "Q20", "Q21", "Q24", "Q27"}
    for value in meanings.values():
        assert value["limitation"] and value["alternative"]


def test_customer_product_week_and_price_questions(session, business):
    from decimal import Decimal

    orders(session, business)
    week = {
        "field": "ordered_at",
        "timezone": "Europe/Berlin",
        "window": {"kind": "iso_week", "year": 2026, "week": 7},
    }
    common = {
        "dataset": "sales_order_lines",
        "time": week,
        "where": {"field": "product_id", "op": "eq", "value": business.item.id},
    }
    cases = [
        ("Q01", ["customer_id"], ["order_count"], "order_count", Decimal(1)),
        ("Q06", ["product_id"], ["ordered_quantity"], "ordered_quantity", Decimal(3)),
        (
            "Q07",
            ["ordered_week", "product_id"],
            ["stated_line_amount"],
            "stated_line_amount",
            Decimal(12),
        ),
        ("Q09", ["customer_id"], ["min_price", "max_price"], "min_price", Decimal(3)),
    ]
    for question, dimensions, measures, key, expected in cases:
        result = query(
            session,
            business.tenant.id,
            {"definition": {**common, "dimensions": dimensions, "measures": measures}},
        )
        assert Decimal(result["rows"][0][key]) == expected, question


def test_previous_buyers_and_first_observed_customer_windows(session, business):
    orders(session, business)
    inactive = query(
        session,
        business.tenant.id,
        {
            "definition": {
                "dataset": "customer_purchases",
                "dimensions": ["customer_id"],
                "measures": ["customer_count"],
                "where": {
                    "relationship": "purchases",
                    "op": "not_exists",
                    "time": {
                        "field": "ordered_at",
                        "timezone": "UTC",
                        "window": {
                            "kind": "absolute",
                            "start": "2026-03-01",
                            "end": "2026-06-01",
                        },
                    },
                },
            }
        },
    )
    assert inactive["rows"][0]["customer_count"] == 1  # Q02: retained history only.
    first = query(
        session,
        business.tenant.id,
        {
            "definition": {
                "dataset": "customer_purchases",
                "dimensions": ["customer_id"],
                "measures": ["customer_count"],
                "time": {
                    "field": "first_order_at",
                    "timezone": "UTC",
                    "window": {
                        "kind": "absolute",
                        "start": "2026-02-01",
                        "end": "2026-03-01",
                    },
                },
            }
        },
    )
    assert (
        first["rows"][0]["customer_count"] == 1
    )  # Q03: first observed, not first-ever.


def test_current_customer_promises_and_stock_are_canonical(session, business):
    from decimal import Decimal

    orders(session, business)
    promises = query(
        session,
        business.tenant.id,
        {
            "definition": {
                "dataset": "delivery_commitments",
                "dimensions": ["party_id", "order_id"],
                "measures": ["open_quantity", "reservation_gap"],
                "where": {"field": "type", "op": "eq", "value": "customer_delivery"},
            }
        },
    )
    assert Decimal(promises["rows"][0]["open_quantity"]) == 3  # Q11, Q14.
    assert Decimal(promises["rows"][0]["reservation_gap"]) == 3
    stock = query(
        session,
        business.tenant.id,
        {
            "definition": {
                "dataset": "inventory",
                "dimensions": ["product_id", "location_id"],
                "measures": ["physical", "reserved", "available"],
            }
        },
    )
    assert all(Decimal(row["physical"]) == 0 for row in stock["rows"])  # Q16.


def test_cancelled_promises_and_corrected_returns_remain_distinct(session, business):
    from decimal import Decimal

    from reality.services.core import (
        cancel_commitment,
        correct_movement,
        record_movement,
    )

    _source, _document, _lines, promises = orders(session, business)
    for promise in promises:
        cancel_commitment(session, business.tenant.id, promise.id)
    cancelled = query(
        session,
        business.tenant.id,
        {
            "definition": {
                "dataset": "delivery_commitments",
                "dimensions": ["product_id"],
                "measures": ["row_count"],
                "where": {"field": "status", "op": "eq", "value": "cancelled"},
            }
        },
    )
    assert cancelled["rows"][0]["row_count"] == 2  # Q10 operational cancellation count.
    returned = record_movement(
        session,
        business.tenant.id,
        "return",
        business.item.id,
        "2",
        to_location_id=business.location.id,
    )
    definition = {
        "dataset": "returns",
        "dimensions": ["product_id"],
        "measures": ["returned_quantity"],
    }
    assert (
        Decimal(
            query(session, business.tenant.id, {"definition": definition})["rows"][0][
                "returned_quantity"
            ]
        )
        == 2
    )
    correct_movement(
        session, business.tenant.id, returned.id, reason="Duplicate return observation"
    )
    assert query(session, business.tenant.id, {"definition": definition})["rows"] == []


def test_purchase_prices_supplier_history_and_due_promises(session, business):
    from decimal import Decimal

    from reality.services.core import create_manual_order

    create_manual_order(
        session,
        business.tenant.id,
        "purchase",
        "PUR-QUESTION",
        business.company.id,
        business.supplier.id,
        business.location.id,
        [
            {
                "item_id": business.item.id,
                "quantity": "4",
                "unit_price": "2.5",
                "gross_amount": "11",
                "unit": "pcs",
            }
        ],
        "11",
        ordered_at="2026-02-10T10:00:00Z",
        requested_delivery_at="2026-02-17T10:00:00Z",
    )
    for dimensions in (["ordered_week", "product_id"], ["supplier_id", "product_id"]):
        result = query(
            session,
            business.tenant.id,
            {
                "definition": {
                    "dataset": "purchase_order_lines",
                    "dimensions": dimensions,
                    "measures": ["ordered_quantity", "min_price", "max_price"],
                }
            },
        )
        assert Decimal(result["rows"][0]["ordered_quantity"]) == 4  # Q22, Q23.
        assert Decimal(result["rows"][0]["min_price"]) == Decimal("2.5")
    result = query(
        session,
        business.tenant.id,
        {
            "definition": {
                "dataset": "delivery_commitments",
                "dimensions": ["party_id"],
                "measures": ["open_quantity"],
                "where": {"field": "type", "op": "eq", "value": "supplier_delivery"},
                "time": {
                    "field": "due_at",
                    "timezone": "UTC",
                    "window": {"kind": "iso_week", "year": 2026, "week": 8},
                },
            }
        },
    )
    assert (
        Decimal(result["rows"][0]["open_quantity"]) == 4
    )  # Q19: promise, not forecast.
