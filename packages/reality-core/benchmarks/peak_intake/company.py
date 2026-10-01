"""The disposable company and the shop orders a peak-intake run feeds it.

Plain service calls, the same as a company that connected a shop: items with
opening stock, one customer standing in for the shop's buyers, and Shopify
order payloads that sell somewhat more than is stocked, so the reservation
pass and the oversold finding have something real to decide.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

from sqlalchemy.orm import Session

from reality.services import core

#: Demand is planned at this share above stock, so some items run out.
OVERSELL = Decimal("1.25")


@dataclass(frozen=True)
class Company:
    tenant_id: str
    company_party_id: str
    customer_party_id: str
    location_id: str
    skus: tuple[str, ...]


def _plan(orders: int, items: int, seed: int) -> list[list[tuple[int, int]]]:
    """Per order, its lines as (item index, quantity); deterministic for a seed."""
    rng = random.Random(seed)
    return [
        [(rng.randrange(items), rng.randint(1, 3)) for _ in range(rng.randint(1, 2))]
        for _ in range(orders)
    ]


def build(session: Session, *, orders: int, items: int, seed: int) -> Company:
    tenant = core.create_tenant(session, "Peak Intake GmbH")
    company = core.create_party(session, tenant.id, "Peak Intake GmbH", "company")
    customer = core.create_party(session, tenant.id, "Shop customers", "customer")
    location = core.create_location(session, tenant.id, "Peak warehouse")
    demand = [0] * items
    for lines in _plan(orders, items, seed):
        for index, quantity in lines:
            demand[index] += quantity
    skus = []
    for index in range(items):
        sku = f"PEAK-{index:04d}"
        item = core.create_item(session, tenant.id, sku, f"Peak article {index}")
        stock = int(Decimal(demand[index]) / OVERSELL)
        if stock:
            core.record_movement(
                session,
                tenant.id,
                "opening_stock",
                item.id,
                str(stock),
                to_location_id=location.id,
            )
        skus.append(sku)
    session.commit()
    return Company(tenant.id, company.id, customer.id, location.id, tuple(skus))


def payloads(
    company: Company, *, orders: int, seed: int, start: datetime | None = None
) -> list[dict[str, Any]]:
    """Shopify order payloads as the webhook delivers them, one per order."""
    start = start or datetime(2026, 11, 27, 18, tzinfo=UTC)
    result = []
    for number, lines in enumerate(_plan(orders, len(company.skus), seed), 1):
        at = (start + timedelta(seconds=number * 0.72)).isoformat()
        line_items = [
            {
                "id": position,
                "sku": company.skus[index],
                "quantity": quantity,
                "price": "19.90",
            }
            for position, (index, quantity) in enumerate(lines, 1)
        ]
        total = sum(Decimal("19.90") * row["quantity"] for row in line_items)
        result.append(
            {
                "id": 9_000_000 + number,
                "name": f"#BF{number:05d}",
                "currency": "EUR",
                "total_price": str(total),
                "created_at": at,
                "updated_at": at,
                "line_items": line_items,
            }
        )
    return result
