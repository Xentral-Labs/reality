"""Party balances: where does one customer or supplier stand (feature 170).

One row per party and currency, summed at read time from the two derivations the
registers already show: the aging register for open items and their due dates,
and the credit rows for unused payments and credit notes. Nothing is stored and
nothing is recomputed; the amounts are the stated amounts, added up.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy.orm import Session

from reality.services import core
from reality.services.finance.credits import available_credit_rows

ZERO = Decimal(0)
SORT_KEYS = ("party", "open", "overdue", "credit", "balance", "oldest_due")


def party_balances(
    session: Session,
    tenant_id: str,
    *,
    side: str,
    credit_only: bool = False,
    query: str = "",
    page: int = 1,
    size: int = 50,
    sort: str = "balance",
    sort_direction: str = "desc",
    as_of: datetime | None = None,
) -> dict[str, Any]:
    """Open, overdue, credit and balance per party and currency for one side."""
    core.get_tenant(session, tenant_id)
    if side not in {"customer", "supplier"}:
        raise core.InvalidOperation("Balance side must be customer or supplier.")
    moment = as_of or datetime.now(UTC)
    account = "accounts_receivable" if side == "customer" else "accounts_payable"
    buckets: dict[tuple[str, str], dict[str, Any]] = {}

    def bucket(party_id: str, party: str, currency: str) -> dict[str, Any]:
        return buckets.setdefault(
            (party_id, currency),
            {
                "party_id": party_id,
                "party": party,
                "currency": currency,
                "open": ZERO,
                "overdue": ZERO,
                "credit": ZERO,
                "open_count": 0,
                "credit_count": 0,
                "oldest_due_date": None,
            },
        )

    # Open items with the one due-date rule, the rows the overdue classes judge.
    for row in core.aging_register(session, tenant_id, as_of=moment):
        if row["control"].account != account or row["status"] not in {
            "open",
            "partial",
        }:
            continue
        document = row["document"]
        outstanding = Decimal(row["open"])
        if outstanding <= ZERO:
            continue
        entry = bucket(document.party_id, row["party"], document.currency)
        entry["open"] += outstanding
        entry["open_count"] += 1
        due_date = row["due_date"]
        if due_date is not None:
            if due_date < moment.date():
                entry["overdue"] += outstanding
            if entry["oldest_due_date"] is None or due_date < entry["oldest_due_date"]:
                entry["oldest_due_date"] = due_date

    # Unused credit, the rows the credit register shows.
    credit_rows, _ = available_credit_rows(
        session, tenant_id, side=side, status="outstanding"
    )
    for row in credit_rows:
        available = Decimal(row["open"])
        if available <= ZERO:
            continue
        entry = bucket(row["party_id"], row["party"], row["currency"])
        entry["credit"] += available
        entry["credit_count"] += 1

    needle = query.strip().lower()
    items = []
    totals: dict[str, dict[str, Decimal | str]] = {}
    for entry in buckets.values():
        if entry["open"] == ZERO and entry["credit"] == ZERO:
            continue
        if credit_only and entry["credit"] <= ZERO:
            continue
        if needle and needle not in (entry["party"] or "").lower():
            continue
        entry["balance"] = entry["open"] - entry["credit"]
        items.append(entry)
        total = totals.setdefault(
            entry["currency"],
            {
                "currency": entry["currency"],
                "open": ZERO,
                "overdue": ZERO,
                "credit": ZERO,
                "balance": ZERO,
            },
        )
        for key in ("open", "overdue", "credit", "balance"):
            total[key] += entry[key]

    key = sort or "balance"
    if key not in SORT_KEYS:
        raise core.InvalidOperation("Unsupported balance sort.")

    def order(entry: dict[str, Any]):
        if key == "party":
            return (
                (entry["party"] or "").lower(),
                entry["currency"],
                entry["party_id"],
            )
        if key == "oldest_due":
            due = entry["oldest_due_date"]
            return (due is None, due or moment.date(), entry["party_id"])
        return (entry[key], entry["party_id"])

    items.sort(key=order, reverse=sort_direction == "desc")
    size = min(100, max(1, size))
    pages = max(1, (len(items) + size - 1) // size)
    page = min(pages, max(1, page))
    return {
        "side": side,
        "as_of": moment.isoformat(),
        "items": [
            {
                **entry,
                "open": str(entry["open"]),
                "overdue": str(entry["overdue"]),
                "credit": str(entry["credit"]),
                "balance": str(entry["balance"]),
                "oldest_due_date": entry["oldest_due_date"].isoformat()
                if entry["oldest_due_date"]
                else None,
            }
            for entry in items[(page - 1) * size : page * size]
        ],
        "totals": [
            {k: str(v) for k, v in row.items()}
            for row in sorted(totals.values(), key=lambda row: row["currency"])
        ],
        "page": {
            "number": page,
            "size": size,
            "total": len(items),
            "pages": pages,
            "has_previous": page > 1,
            "has_next": page < pages,
        },
    }
