"""Discoverable analytical grains; keys are authority, labels are presentation."""

from __future__ import annotations

from copy import deepcopy

FIELDS = {
    "due_week": ("Due week", "text"),
    "direction": ("Direction", "text"),
    "reversal_role": ("Reversal status", "text"),
    "record_id": ("Record", "id"),
    "order_id": ("Order", "id"),
    "customer_id": ("Customer", "id"),
    "supplier_id": ("Supplier", "id"),
    "party_id": ("Business partner", "id"),
    "product_id": ("Product", "id"),
    "product_b_id": ("Other product", "id"),
    "location_id": ("Location", "id"),
    "currency": ("Currency", "text"),
    "unit": ("Unit", "text"),
    "ordered_at": ("Order date", "datetime"),
    "ordered_day": ("Day", "text"),
    "ordered_week": ("Week", "text"),
    "ordered_month": ("Month", "text"),
    "ordered_quarter": ("Quarter", "text"),
    "ordered_year": ("Year", "text"),
    "sales_channel": ("Sales channel", "text"),
    "unit_price": ("Agreed unit price", "decimal"),
    "status": ("Status", "text"),
    "type": ("Type", "text"),
    "due_at": ("Due date", "datetime"),
    "occurred_at": ("Occurrence date", "datetime"),
    "effective_at": ("Effective date", "datetime"),
    "side": ("Side", "text"),
    "first_order_at": ("First observed order", "datetime"),
    "last_order_at": ("Last observed order", "datetime"),
}
MEASURES = {
    "billed_quantity": ("Billed quantity", "sum", "unit"),
    "unbilled_quantity": ("Unbilled quantity", "sum", "unit"),
    "reservation_gap": ("Reservation gap", "sum", "unit"),
    "row_count": ("Record count", "count", None),
    "order_count": ("Order count", "distinct", None),
    "customer_count": ("Customer count", "distinct", None),
    "ordered_quantity": ("Ordered quantity", "sum", "unit"),
    "stated_line_amount": ("Stated line amount", "sum", "currency"),
    "stated_order_amount": ("Stated order amount", "sum", "currency"),
    "min_price": ("Minimum agreed price", "min", "currency_unit"),
    "max_price": ("Maximum agreed price", "max", "currency_unit"),
    "physical": ("Physical stock", "sum", "unit"),
    "reserved": ("Reserved quantity", "sum", "unit"),
    "available": ("Available quantity", "sum", "unit"),
    "incoming": ("Incoming quantity", "sum", "unit"),
    "open_quantity": ("Open quantity", "sum", "unit"),
    "fulfilled": ("Fulfilled quantity", "sum", "unit"),
    "open_amount": ("Open amount", "sum", "currency"),
    "allocated": ("Allocated amount", "sum", "currency"),
    "unallocated": ("Unallocated amount", "sum", "currency"),
    "amount": ("Recorded amount", "sum", "currency"),
    "returned_quantity": ("Returned quantity", "sum", "unit"),
}
ORDER_FIELDS = [
    "record_id",
    "order_id",
    "product_id",
    "currency",
    "unit",
    "ordered_at",
    "ordered_day",
    "ordered_week",
    "ordered_month",
    "ordered_quarter",
    "ordered_year",
    "sales_channel",
    "unit_price",
]
CATALOG = {}
for direction, party in (("sales", "customer_id"), ("purchase", "supplier_id")):
    CATALOG[f"{direction}_order_lines"] = {
        "label": "Sales order lines"
        if direction == "sales"
        else "Purchase order lines",
        "grain": "document_line",
        "fields": [party, *ORDER_FIELDS],
        "measures": [
            "row_count",
            "order_count",
            "ordered_quantity",
            "stated_line_amount",
            "min_price",
            "max_price",
        ]
        + (["customer_count"] if direction == "sales" else []),
    }
    CATALOG[f"{direction}_orders"] = {
        "label": "Sales orders" if direction == "sales" else "Purchase orders",
        "grain": "document",
        "fields": [
            party,
            *[f for f in ORDER_FIELDS if f not in {"product_id", "unit", "unit_price"}],
        ],
        "measures": ["row_count", "order_count", "stated_order_amount"]
        + (["customer_count"] if direction == "sales" else []),
    }
CATALOG.update(
    {
        "returns": {
            "label": "Physical returns",
            "grain": "movement",
            "fields": [
                "record_id",
                "product_id",
                "party_id",
                "unit",
                "type",
                "occurred_at",
            ],
            "measures": ["row_count", "returned_quantity"],
        },
        "order_billing": {
            "label": "Order line billing",
            "grain": "document_line",
            "fields": [
                "record_id",
                "order_id",
                "party_id",
                "product_id",
                "unit",
                "type",
                "ordered_at",
            ],
            "measures": [
                "row_count",
                "ordered_quantity",
                "fulfilled",
                "returned_quantity",
                "billed_quantity",
                "unbilled_quantity",
            ],
        },
        "customer_purchases": {
            "label": "Customer purchase history",
            "grain": "customer",
            "fields": ["customer_id", "first_order_at", "last_order_at"],
            "measures": ["customer_count", "row_count"],
            "relationships": ["purchases"],
        },
        "order_product_pairs": {
            "label": "Products ordered together",
            "grain": "order_product_pair",
            "fields": [
                "order_id",
                "customer_id",
                "product_id",
                "product_b_id",
                "ordered_at",
            ],
            "measures": ["order_count", "customer_count", "row_count"],
        },
        "payments": {
            "label": "Recorded payments",
            "grain": "payment",
            "fields": [
                "record_id",
                "party_id",
                "currency",
                "direction",
                "effective_at",
                "reversal_role",
            ],
            "measures": ["row_count", "amount", "allocated", "unallocated"],
        },
        "delivery_commitments": {
            "label": "Delivery commitments",
            "grain": "commitment",
            "fields": [
                "record_id",
                "order_id",
                "party_id",
                "product_id",
                "location_id",
                "unit",
                "type",
                "status",
                "due_at",
            ],
            "measures": [
                "row_count",
                "open_quantity",
                "reserved",
                "fulfilled",
                "reservation_gap",
            ],
        },
        "inventory": {
            "label": "Inventory by location",
            "grain": "item_location",
            "fields": ["product_id", "location_id", "unit"],
            "measures": ["row_count", "physical", "reserved", "available", "incoming"],
        },
        "open_items": {
            "label": "Open invoices",
            "grain": "invoice",
            "fields": [
                "record_id",
                "party_id",
                "currency",
                "side",
                "due_at",
                "due_week",
                "status",
            ],
            "measures": ["row_count", "open_amount", "amount"],
        },
    }
)

FIELDS["observed_supplier_count"] = ("Observed supplier count", "decimal")
MEASURES.update(
    {
        "moved_quantity": ("Moved quantity", "sum", "unit"),
        "open_demand": ("Open customer demand", "sum", "unit"),
        "stock_shortfall": ("Stock shortfall", "sum", "unit"),
    }
)
CATALOG.update(
    {
        "outbound_movements": {
            "label": "Outbound movements",
            "grain": "movement",
            "fields": [
                "record_id",
                "product_id",
                "party_id",
                "location_id",
                "unit",
                "type",
                "occurred_at",
            ],
            "measures": ["row_count", "moved_quantity"],
        },
        "inventory_demand": {
            "label": "Stock and promised demand",
            "grain": "item",
            "fields": ["product_id", "unit"],
            "measures": ["row_count", "physical", "open_demand", "stock_shortfall"],
        },
        "product_suppliers": {
            "label": "Observed suppliers by product",
            "grain": "product",
            "fields": [
                "product_id",
                "supplier_id",
                "observed_supplier_count",
                "ordered_at",
            ],
            "measures": ["row_count"],
        },
    }
)
CATALOG["inventory"]["relationships"] = ["outbound"]

# Numeric observations are filterable at their declared source grain. Counts remain
# aggregate-only, so filtering a count cannot accidentally mean filtering a line.
for _key, _info in CATALOG.items():
    _info["filter_fields"] = [m for m in _info["measures"] if MEASURES[m][1] == "sum"]
    for _measure in _info["filter_fields"]:
        FIELDS[_measure] = (MEASURES[_measure][0], "decimal")
    if _key in {"sales_orders", "purchase_orders"}:
        _info["relationships"] = ["order_lines"]


def catalog(dataset: str | None = None) -> dict:
    selected = (
        CATALOG
        if dataset is None
        else {dataset: CATALOG[dataset]}
        if dataset in CATALOG
        else {}
    )
    operators = {
        "text": ["eq", "ne", "in", "not_in", "contains", "is_missing", "is_present"],
        "id": ["eq", "ne", "in", "not_in", "is_missing", "is_present"],
        "datetime": ["eq", "gte", "gt", "lte", "lt", "is_missing", "is_present"],
        "decimal": ["eq", "ne", "gte", "gt", "lte", "lt", "is_missing", "is_present"],
    }
    datasets = []
    for key, item in selected.items():
        datasets.append(
            {
                "key": key,
                "label": item["label"],
                "grain": item["grain"],
                "relationships": item.get("relationships", []),
                "dimensions": [
                    {
                        "key": f,
                        "label": FIELDS[f][0],
                        "type": FIELDS[f][1],
                        "operators": operators[FIELDS[f][1]],
                        "groupable": f in item["fields"],
                    }
                    for f in dict.fromkeys([*item["fields"], *item["filter_fields"]])
                ],
                "measures": [
                    {
                        "key": m,
                        "label": MEASURES[m][0],
                        "aggregation": MEASURES[m][1],
                        "partition": MEASURES[m][2],
                    }
                    for m in item["measures"]
                ],
            }
        )
    return {
        "version": 1,
        "datasets": datasets,
        "limits": {"page_size": 200, "groups": 10000, "deadline_seconds": 30},
        "starters": deepcopy(STARTERS),
        "restricted_meanings": deepcopy(RESTRICTED_MEANINGS),
    }


STARTERS = [
    {
        "name": "Weekly product orders",
        "definition": {
            "dataset": "sales_order_lines",
            "dimensions": ["ordered_week", "product_id"],
            "measures": ["ordered_quantity"],
            "time": {
                "field": "ordered_at",
                "timezone": "UTC",
                "window": {"kind": "last_complete_weeks", "count": 12},
            },
        },
    },
    {
        "name": "Orders by customer",
        "definition": {
            "dataset": "sales_orders",
            "dimensions": ["customer_id"],
            "measures": ["order_count", "stated_order_amount"],
        },
    },
    {
        "name": "Current inventory",
        "definition": {
            "dataset": "inventory",
            "dimensions": ["product_id", "location_id"],
            "measures": ["physical", "reserved", "available"],
        },
    },
    {
        "name": "Open deliveries",
        "definition": {
            "dataset": "delivery_commitments",
            "dimensions": ["party_id", "product_id"],
            "measures": ["open_quantity"],
            "where": {"field": "status", "op": "eq", "value": "open"},
        },
    },
    {
        "name": "Open invoices",
        "definition": {
            "dataset": "open_items",
            "dimensions": ["party_id", "currency"],
            "measures": ["open_amount"],
        },
    },
]


RESTRICTED_MEANINGS = {
    "Q13": {
        "limitation": "Current reservations do not prove simultaneous stock feasibility.",
        "alternative": "delivery_commitments.reservation_gap",
    },
    "Q14": {
        "limitation": "Missing products can mean a reservation gap or a company-wide physical shortfall; these are separate observations.",
        "alternative": "inventory_demand.stock_shortfall",
    },
    "Q15": {
        "limitation": "Dispatch, receipt and revision baselines do not define one universal order-to-delivery duration.",
        "alternative": "outbound_movements.occurred_at",
    },
    "Q20": {
        "limitation": "Shared products identify candidate affected demand, not causal supplier-to-customer allocation.",
        "alternative": "delivery_commitments.product_id",
    },
    "Q21": {
        "limitation": "Current overdue promises do not define historical supplier reliability.",
        "alternative": "delivery_commitments.due_at",
    },
    "Q24": {
        "limitation": "Exactly one observed supplier does not mean that no alternatives exist.",
        "alternative": "product_suppliers.observed_supplier_count",
    },
    "Q27": {
        "limitation": "Payment and allocation timestamps do not define weighted historical payment lateness.",
        "alternative": "payments",
    },
}
