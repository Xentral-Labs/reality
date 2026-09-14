"""Bounded adapters over canonical operational observations, never new rules."""

from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import DateTime, Numeric, String, column, func, select, values

from reality.db.core import (
    Commitment,
    Document,
    Item,
    LedgerEntry,
    Location,
    Movement,
    Reservation,
)
from reality.services.analytics.budget import check_budget
from reality.services.analytics.catalog import CATALOG, FIELDS
from reality.services.analytics.execution import AnalyticsError
from reality.services.core import (
    aging_register,
    inventory_rows,
    open_quantity,
    payment_rows,
)
from reality.services.delivery_reads import _query, _row
from reality.services.read_contracts import location_inventory_rows


def operational_relation(session, tenant_id, definition):
    models = (
        (Commitment, Movement, Reservation, Item, Location)
        if definition.dataset not in {"open_items", "payments"}
        else (Document, LedgerEntry)
    )
    population = sum(
        session.scalar(
            select(func.count()).select_from(model).where(model.tenant_id == tenant_id)
        )
        for model in models
    )
    if population > 20000:
        raise AnalyticsError(
            "This derived perspective exceeds 20,000 source records. Use a narrower operational workspace.",
            "query_too_broad",
        )
    check_budget()
    rows = []
    if definition.dataset == "order_billing":
        from reality.services.analytics.finance import billing_rows

        rows = billing_rows(session, tenant_id)
    elif definition.dataset == "delivery_commitments":
        for kind in ("customer_delivery", "supplier_delivery"):
            for result in session.execute(_query(tenant_id, kind)):
                row = _row(result)
                rows.append(
                    {
                        "record_id": row["id"],
                        "record_kind": "commitment",
                        "order_id": row["document_id"],
                        "party_id": row["party_id"],
                        "party": row["counterparty"],
                        "product_id": row["item_id"],
                        "product": row["item"],
                        "location_id": row["location_id"],
                        "location": row["location"],
                        "unit": row["unit"],
                        "type": kind,
                        "status": row["status"],
                        "due_at": row["due_at"],
                        "open_quantity": Decimal(row["open"])
                        if row["status"] == "open"
                        else Decimal(0),
                        "reserved": Decimal(row["reserved"]),
                        "fulfilled": Decimal(row["fulfilled"]),
                    }
                )
    elif definition.dataset == "inventory_demand":
        demand = {}
        for promise in session.scalars(
            select(Commitment).where(
                Commitment.tenant_id == tenant_id,
                Commitment.type == "customer_delivery",
                Commitment.status == "open",
            )
        ):
            check_budget()
            demand[promise.item_id] = demand.get(
                promise.item_id, Decimal(0)
            ) + open_quantity(session, tenant_id, promise.id)
        for observation in inventory_rows(session, tenant_id):
            check_budget()
            item = observation["item"]
            open_demand = demand.get(item.id, Decimal(0))
            rows.append(
                {
                    "product_id": item.id,
                    "product": item.name,
                    "unit": item.unit,
                    "physical": observation["physical"],
                    "open_demand": open_demand,
                    "stock_shortfall": max(
                        open_demand - observation["physical"], Decimal(0)
                    ),
                }
            )
    elif definition.dataset == "inventory":
        items = session.scalar(
            select(func.count()).select_from(Item).where(Item.tenant_id == tenant_id)
        )
        locations = session.scalar(
            select(func.count())
            .select_from(Location)
            .where(Location.tenant_id == tenant_id)
        )
        if items * locations > 3000:
            raise AnalyticsError(
                "Too many item/location combinations for this analysis.",
                "query_too_broad",
            )
        for row in location_inventory_rows(
            session, tenant_id, item_id=None, location_id=None
        ).values():
            rows.append(
                {
                    "product_id": row["item_id"],
                    "product": row["item"],
                    "location_id": row["location_id"],
                    "location": row["location"],
                    "unit": row["unit"],
                    **{
                        key: Decimal(row[key])
                        for key in ("physical", "reserved", "available", "incoming")
                    },
                }
            )
    elif definition.dataset == "open_items":
        for row in aging_register(session, tenant_id):
            if row["status"] not in {"open", "partial"} or row["open"] <= 0:
                continue
            doc = row["document"]
            rows.append(
                {
                    "record_id": doc.id,
                    "record_kind": "document",
                    "party_id": doc.party_id,
                    "party": row["party"],
                    "currency": doc.currency,
                    "side": "receivable"
                    if row["control"].account == "accounts_receivable"
                    else "payable",
                    "due_at": datetime.combine(
                        row["due_date"], datetime.min.time(), UTC
                    )
                    if row["due_date"]
                    else None,
                    "status": row["status"],
                    "amount": doc.gross_amount,
                    "open_amount": row["open"],
                }
            )
    elif definition.dataset == "payments":
        for row in payment_rows(session, tenant_id):
            cash = row["cash_entry"]
            rows.append(
                {
                    "record_id": cash.id,
                    "record_kind": "ledger_entry",
                    "party_id": cash.party_id,
                    "party": row["party"],
                    "currency": cash.currency,
                    "direction": row["direction"],
                    "effective_at": cash.effective_at,
                    "reversal_role": row["reversal_role"],
                    "amount": cash.amount,
                    "allocated": row["allocated"],
                    "unallocated": row["unallocated"],
                }
            )
    for row in rows:
        check_budget()
        if "open_quantity" in row:
            row["reservation_gap"] = max(
                row["open_quantity"] - row["reserved"], Decimal(0)
            )
        if "due_at" in row:
            due = row["due_at"]
            row["due_week"] = due.strftime("%G-W%V") if due else None
    info = CATALOG[definition.dataset]
    fields = list(
        dict.fromkeys(
            [
                *info["fields"],
                *[m for m in info["measures"] if m != "row_count"],
                "record_kind",
                "party",
                "product",
                "location",
            ]
        )
    )
    if len(rows) * len(fields) > 60000:
        raise AnalyticsError(
            "This derived result is too broad. Use the operational workspace.",
            "query_too_broad",
        )
    columns = [
        column(
            key,
            DateTime(timezone=True)
            if FIELDS.get(key, (None, None))[1] == "datetime"
            else Numeric(28, 8)
            if key in info["measures"] or FIELDS.get(key, (None, None))[1] == "decimal"
            else String(),
        )
        for key in fields
    ]
    relation = values(*columns, name="analytics_observations").data(
        [tuple(row.get(key) for key in fields) for row in rows]
        or [tuple(None for _ in fields)]
    )
    return select(relation).where(bool(rows)).subquery()
