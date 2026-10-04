"""The disposable company and the shop orders a peak-intake run feeds it.

Confirmed catalog proposals by the disposable company's named Owner create items
with opening stock and one customer standing in for the shop's buyers. Shopify
order payloads that sell somewhat more than is stocked, so the reservation
pass and the oversold finding have something real to decide.
"""

from __future__ import annotations

import json
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
    reviewer_user_id: str
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
    from reality.db.core import AppUser, Item, Location, Party, TenantMembership
    from reality.services.memberships import Principal
    from reality.tools.application import (
        approve_and_execute_proposal,
        create_change_proposal,
    )

    tenant = core.create_tenant(session, "Peak Intake GmbH")
    reviewer = AppUser(
        id=core.uid("usr"),
        email=f"{core.uid('benchmark')}@example.test",
        password_hash="unused",
        status="active",
        email_verified_at=core.now(),
    )
    session.add(reviewer)
    session.flush()
    session.add(
        TenantMembership(
            id=core.uid("tmb"),
            tenant_id=tenant.id,
            user_id=reviewer.id,
            role="owner",
            status="active",
        )
    )
    session.commit()

    def confirmed(tool, arguments):
        proposal = create_change_proposal(session, tenant.id, tool, arguments)
        receipt = approve_and_execute_proposal(
            session,
            tenant.id,
            proposal.id,
            confirmed=True,
            confirming_principal=Principal(reviewer.id),
        )
        return json.loads(receipt.output)

    parties = confirmed(
        "party_create",
        {
            "records": [
                {"name": "Peak Intake GmbH", "type": "company", "roles": ["company"]},
                {"name": "Shop customers", "type": "customer", "roles": ["customer"]},
            ]
        },
    )["records"]
    company, customer = [session.get(Party, (tenant.id, row["id"])) for row in parties]
    location_id = confirmed(
        "location_create", {"records": [{"name": "Peak warehouse"}]}
    )["records"][0]["id"]
    location = session.get(Location, (tenant.id, location_id))
    demand = [0] * items
    for lines in _plan(orders, items, seed):
        for index, quantity in lines:
            demand[index] += quantity
    skus = []
    for index in range(items):
        sku = f"PEAK-{index:04d}"
        item_id = confirmed(
            "item_create", {"records": [{"sku": sku, "name": f"Peak article {index}"}]}
        )["records"][0]["id"]
        item = session.get(Item, (tenant.id, item_id))
        stock = int(Decimal(demand[index]) / OVERSELL)
        if stock:
            confirmed(
                "movement_create",
                {
                    "movement_type": "opening_stock",
                    "item_id": item.id,
                    "quantity": str(stock),
                    "to_location_id": location.id,
                },
            )
        skus.append(sku)
    session.commit()
    return Company(
        tenant.id, reviewer.id, company.id, customer.id, location.id, tuple(skus)
    )


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
