"""Read-only response contracts shared by application tools and MCP."""

from __future__ import annotations

import base64
import binascii
import hashlib
import json
from decimal import Decimal
from typing import Any

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from reality.db.core import BusinessEvent, Commitment, Item, LedgerEntry, Location, now
from reality.services.core import (
    InvalidOperation,
    NotFound,
    active_reserved,
    business_discovery_record,
    business_discovery_statement,
    get_tenant,
    open_quantity,
    stock_at,
)


def read_metadata(
    session: Session,
    tenant_id: str,
    filters: dict[str, Any],
    *,
    projection_version: int | None = None,
    paged: bool = False,
) -> dict[str, Any]:
    get_tenant(session, tenant_id)
    sequence = session.scalar(
        select(func.max(BusinessEvent.sequence)).where(
            BusinessEvent.tenant_id == tenant_id
        )
    )
    return {
        "contract_version": 2,
        "tenant_id": tenant_id,
        "filters": filters,
        "observed_at": now().isoformat(),
        "projection_version": projection_version,
        "event_sequence": int(sequence) if sequence is not None else None,
        "upstream_freshness": "unknown",
        "consistency": "live_keyset" if paged else "live_read",
        "completeness": "matching_retained_records_only",
        "persistence": {
            "business_writes": False,
            "projection_writes": False,
            "authentication_telemetry": "possible",
        },
    }


def page_options(
    tenant_id: str, read: str, filters: dict[str, Any], arguments: dict[str, Any]
) -> tuple[int, str, str | None]:
    limit = arguments.get("limit", 25)
    if type(limit) is not int or not 1 <= limit <= 100:
        raise InvalidOperation("Page limit must be between 1 and 100.")
    scope = hashlib.sha256(
        json.dumps([tenant_id, read, filters, "key_ascending"], sort_keys=True).encode()
    ).hexdigest()
    cursor = arguments.get("cursor")
    after = None
    if cursor is not None:
        try:
            if not isinstance(cursor, str) or not 1 <= len(cursor) <= 2048:
                raise ValueError()
            payload = json.loads(
                base64.b64decode(cursor, altchars=b"-_", validate=True)
            )
            if (
                not isinstance(payload, dict)
                or set(payload) != {"v", "scope", "after"}
                or type(payload["v"]) is not int
                or payload["v"] != 1
                or payload["scope"] != scope
                or not isinstance(payload["after"], str)
                or not 1 <= len(payload["after"]) <= 512
            ):
                raise ValueError()
            after = payload["after"]
        except (ValueError, TypeError, binascii.Error, UnicodeError):
            raise InvalidOperation("Invalid cursor for this read scope.") from None
    return limit, scope, after


def page_result(
    records: list[dict[str, Any]],
    keys: list[str],
    limit: int,
    scope: str,
    metadata: dict[str, Any],
) -> dict[str, Any]:
    more = len(records) > limit
    cursor = None
    if more:
        cursor = base64.urlsafe_b64encode(
            json.dumps(
                {"v": 1, "scope": scope, "after": keys[limit - 1]},
                separators=(",", ":"),
            ).encode()
        ).decode()
    return {
        "records": records[:limit],
        "next_cursor": cursor,
        "has_more": more,
        "metadata": metadata,
    }


def discovery_page(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> dict[str, Any]:
    filters = {
        "family": arguments["family"].strip().lower(),
        "query": (arguments.get("query") or "").strip(),
        "record_id": arguments.get("record_id"),
    }
    limit, scope, after = page_options(
        tenant_id, "business_discover", filters, arguments
    )
    with session.no_autoflush:
        statement, model, fields = business_discovery_statement(
            session, tenant_id, **filters
        )
        if after:
            statement = statement.where(model.id > after)
        rows = list(session.scalars(statement.limit(limit + 1)))
        if filters["record_id"] and not rows and after is None:
            raise NotFound("Business record not found.")
        return page_result(
            [business_discovery_record(row, fields, session) for row in rows],
            [row.id for row in rows],
            limit,
            scope,
            read_metadata(session, tenant_id, filters, paged=True),
        )


def finance_balances(session: Session, tenant_id: str) -> dict[str, Any]:
    with session.no_autoflush:
        get_tenant(session, tenant_id)
        signed = case(
            (LedgerEntry.debit_credit == "debit", LedgerEntry.amount),
            else_=-LedgerEntry.amount,
        )
        rows = session.execute(
            select(
                LedgerEntry.currency,
                func.sum(
                    case(
                        (LedgerEntry.account == "accounts_receivable", signed), else_=0
                    )
                ),
                func.sum(
                    case((LedgerEntry.account == "accounts_payable", -signed), else_=0)
                ),
            )
            .where(
                LedgerEntry.tenant_id == tenant_id,
                LedgerEntry.account.in_(["accounts_receivable", "accounts_payable"]),
            )
            .group_by(LedgerEntry.currency)
            .order_by(LedgerEntry.currency)
        )
        balances = [
            {
                "currency": currency,
                "receivables": str(receivable),
                "payables": str(payable),
            }
            for currency, receivable, payable in rows
        ]
        return {
            "balances": balances,
            "metadata": read_metadata(
                session,
                tenant_id,
                {
                    "accounts": ["accounts_receivable", "accounts_payable"],
                    "currency": "all_separate",
                },
            ),
        }


def location_inventory_rows(
    session: Session, tenant_id: str, *, item_id: str | None, location_id: str | None
) -> dict[str, dict[str, Any]]:
    item_query = select(Item).where(Item.tenant_id == tenant_id)
    location_query = select(Location).where(Location.tenant_id == tenant_id)
    if item_id:
        item_query = item_query.where(Item.id == item_id)
    if location_id:
        location_query = location_query.where(Location.id == location_id)
    else:
        location_query = location_query.where(Location.allows_stock.is_(True))
    items = list(session.scalars(item_query.order_by(Item.id)))
    locations = list(session.scalars(location_query.order_by(Location.id)))
    if (item_id and not items) or (location_id and not locations):
        raise NotFound("Inventory reference not found.")
    result = {}
    for item in items:
        for location in locations:
            physical = stock_at(session, tenant_id, item.id, location.id)
            reserved = active_reserved(session, tenant_id, item.id, location.id)
            incoming = sum(
                (
                    open_quantity(session, tenant_id, c.id)
                    for c in session.scalars(
                        select(Commitment).where(
                            Commitment.tenant_id == tenant_id,
                            Commitment.item_id == item.id,
                            Commitment.location_id == location.id,
                            Commitment.type == "supplier_delivery",
                            Commitment.status == "open",
                        )
                    )
                ),
                Decimal(0),
            )
            result[f"{item.id}:{location.id}"] = {
                "item_id": item.id,
                "item": item.name,
                "sku": item.sku,
                "location_id": location.id,
                "location": location.name,
                "aggregation": "item_location",
                "unit": item.unit or None,
                "unit_status": "known" if item.unit else "unknown",
                "quantity_basis": "item_unit",
                "physical": str(physical),
                "reserved": str(reserved),
                "available": str(physical - reserved),
                "incoming": str(incoming),
                "projected": str(physical - reserved + incoming),
            }
    return result


def location_stock_row(
    session: Session, tenant_id: str, pair_key: str
) -> dict[str, Any]:
    """Read one item's position at one place, keyed as the shared rows key it."""
    item_id, separator, location_id = pair_key.partition(":")
    if not (item_id and separator and location_id):
        raise NotFound("Inventory reference not found.")
    rows = location_inventory_rows(
        session, tenant_id, item_id=item_id, location_id=location_id
    )
    return rows[pair_key]


def operational_page(
    session: Session, tenant_id: str, name: str, arguments: dict[str, Any]
) -> dict[str, Any]:
    from reality.services.projections import (
        INVENTORY,
        PROJECTION_VERSION,
        derive_projection_rows,
    )

    filters: dict[str, Any] = {}
    if name == INVENTORY:
        view = arguments.get("view", "aggregate")
        if view not in {"aggregate", "location"}:
            raise InvalidOperation("Inventory view must be aggregate or location.")
        filters = {
            "view": "location" if arguments.get("location_id") else view,
            "item_id": arguments.get("item_id"),
            "location_id": arguments.get("location_id"),
        }
    limit, scope, after = page_options(tenant_id, name, filters, arguments)
    with session.no_autoflush:
        get_tenant(session, tenant_id)
        if name == INVENTORY and filters["view"] == "location":
            rows = location_inventory_rows(
                session,
                tenant_id,
                item_id=filters["item_id"],
                location_id=filters["location_id"],
            )
        else:
            rows = derive_projection_rows(session, tenant_id, name)
            if name == INVENTORY and filters["item_id"]:
                rows = {
                    key: row
                    for key, row in rows.items()
                    if row["item_id"] == filters["item_id"]
                }
                if not rows:
                    raise NotFound("Inventory reference not found.")
        keys = [key for key in sorted(rows) if after is None or key > after][
            : limit + 1
        ]
        return page_result(
            [rows[key] for key in keys],
            keys,
            limit,
            scope,
            read_metadata(
                session,
                tenant_id,
                filters,
                projection_version=PROJECTION_VERSION,
                paged=True,
            ),
        )
