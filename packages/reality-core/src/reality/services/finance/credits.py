"""Read-time customer and supplier credit, without a second balance authority."""

from collections import defaultdict
from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session

from reality.db.core import Document, LedgerEntry, LedgerReversal, Party
from reality.domain.calendar import day_text
from reality.services import core


def available_credit_rows(
    session: Session,
    tenant_id: str,
    *,
    side: str,
    query: str = "",
    status: str = "outstanding",
    party_id: str | None = None,
    party_ids: set[str] | None = None,
    effective_before: datetime | None = None,
) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    """Every original credit of one side with its effective consumption, unpaged.

    The register pages this list; the party balances (feature 170) sum it. Both
    must see the same rows, which is why the derivation lives here once.
    """
    core.get_tenant(session, tenant_id)
    if side not in {"customer", "supplier"}:
        raise core.InvalidOperation("Credit side must be customer or supplier.")
    customer = side == "customer"
    role = "accounts_receivable" if customer else "accounts_payable"
    reversal_groups = select(LedgerReversal.original_posting_group_id).where(
        LedgerReversal.tenant_id == tenant_id,
        LedgerReversal.reversed_at < effective_before if effective_before else True,
    )
    statement = (
        select(LedgerEntry, Document, Party.name)
        .join(
            Document,
            and_(
                Document.tenant_id == tenant_id, Document.id == LedgerEntry.document_id
            ),
        )
        .join(
            Party, and_(Party.tenant_id == tenant_id, Party.id == LedgerEntry.party_id)
        )
        .where(
            LedgerEntry.tenant_id == tenant_id,
            LedgerEntry.effective_at < effective_before if effective_before else True,
            LedgerEntry.account == role,
            LedgerEntry.debit_credit == ("credit" if customer else "debit"),
            LedgerEntry.posting_group_id.not_in(reversal_groups),
            Document.type.in_(
                (
                    f"{side}_payment",
                    f"{side}_deposit",
                    f"opening_{side}_credit",
                    "credit_note" if customer else "supplier_credit_note",
                )
            ),
        )
    )
    if query.strip():
        match = f"%{query.strip()}%"
        statement = statement.where(
            or_(
                Document.number.ilike(match),
                Document.id.ilike(match),
                Party.name.ilike(match),
            )
        )
    if party_id:
        statement = statement.where(LedgerEntry.party_id == party_id)
    if party_ids is not None:
        statement = statement.where(LedgerEntry.party_id.in_(party_ids))
    allocations: dict[str, list] = defaultdict(list)
    for allocation in core.active_settlement_allocations(
        session, tenant_id, effective_before=effective_before
    ):
        allocations[allocation.payment_ledger_entry_id].append(allocation)
        allocations[allocation.invoice_ledger_entry_id].append(allocation)
    items = []
    totals: dict[str, dict] = {}
    records = list(session.execute(statement))
    opening_ids = [
        document.id
        for _, document, _ in records
        if document.type.startswith("opening_")
    ]
    from reality.db.opening import OpeningItem, OpeningScope

    opening_kinds = (
        dict(
            session.execute(
                select(OpeningItem.document_id, OpeningScope.coverage_kind)
                .join(
                    OpeningScope,
                    (OpeningScope.tenant_id == tenant_id)
                    & (OpeningScope.id == OpeningItem.scope_id),
                )
                .where(
                    OpeningItem.tenant_id == tenant_id,
                    OpeningItem.document_id.in_(opening_ids),
                )
            ).all()
        )
        if opening_ids
        else {}
    )
    for entry, document, party in records:
        used = sum((a.amount for a in allocations[entry.id]), Decimal(0))
        available = entry.amount - used
        state = "paid" if available == 0 else "partial" if used else "open"
        if status and (
            state not in {"open", "partial"}
            if status == "outstanding"
            else state != status
        ):
            continue
        row = {
            "document_id": document.id,
            "number": document.number,
            "document_type": document.type,
            "coverage_kind": opening_kinds.get(document.id),
            "origin": "opening"
            if document.type.startswith("opening_")
            else "deposit"
            if document.type.endswith("_deposit")
            else "payment"
            if document.type.endswith("_payment")
            else "credit_note",
            "document_date": day_text(document.document_date),
            "source_record_id": entry.source_record_id or document.source_record_id,
            "party_id": entry.party_id,
            "party": party,
            "control_entry_id": entry.id,
            "posting_group_id": entry.posting_group_id,
            "account_id": entry.account_id,
            "account_code": entry.account_record.code,
            "account_state": entry.account_record.state,
            "allocation_ids": [a.id for a in allocations[entry.id]],
            "gross": str(entry.amount),
            "settled": str(used),
            "open": str(available),
            "currency": entry.currency,
            "status": state,
        }
        items.append(row)
        total = totals.setdefault(
            entry.currency,
            {
                "currency": entry.currency,
                "gross": Decimal(0),
                "settled": Decimal(0),
                "open": Decimal(0),
            },
        )
        for key, value in (
            ("gross", entry.amount),
            ("settled", used),
            ("open", available),
        ):
            total[key] += value
    return items, totals


def available_credit_items(
    session: Session,
    tenant_id: str,
    *,
    side: str,
    query: str = "",
    status: str = "outstanding",
    page: int = 1,
    size: int = 50,
    sort: str = "",
    sort_direction: str = "asc",
    party_id: str | None = None,
) -> dict[str, Any]:
    """Expose each original credit and its effective consumption, including refunds."""
    items, totals = available_credit_rows(
        session, tenant_id, side=side, query=query, status=status, party_id=party_id
    )
    key = {"id": "document_id", "date": "document_date"}.get(sort, sort) or "number"
    if key not in {
        "document_id",
        "document_date",
        "number",
        "party",
        "gross",
        "settled",
        "open",
        "status",
    }:
        raise core.InvalidOperation("Unsupported credit sort.")

    def order(row):
        value = (
            Decimal(row[key]) if key in {"gross", "settled", "open"} else row[key] or ""
        )
        return value, row["control_entry_id"]

    items.sort(key=order, reverse=sort_direction == "desc")
    size = min(100, max(1, size))
    pages = max(1, (len(items) + size - 1) // size)
    page = min(pages, max(1, page))
    return {
        "items": items[(page - 1) * size : page * size],
        "totals": [
            {key: str(value) for key, value in row.items()}
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
