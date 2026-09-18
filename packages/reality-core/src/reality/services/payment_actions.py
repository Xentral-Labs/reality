"""Selected-invoice payment review and historical allocation evidence."""

from __future__ import annotations

import hashlib
import json
from decimal import Decimal
from decimal import InvalidOperation as InvalidDecimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from reality.db.core import (
    BusinessEvent,
    ChangeProposal,
    Document,
    LedgerEntry,
    Party,
    SettlementAllocation,
    SourceRecord,
)
from reality.domain.calendar import day_text
from reality.services.core import (
    InvalidOperation,
    NotFound,
    _preview_customer_refund,
    _preview_invoice_payment,
    _tenant_record,
    active_settlement_allocations,
    open_invoice_amount,
    utc_datetime,
)
from reality.services.order_actions import _json

PAYMENT_TOOLS = {
    "customer_payment_post",
    "supplier_payment_post",
    "customer_refund_post",
}


def _values(row):
    return {column.name: getattr(row, column.name) for column in row.__table__.columns}


def _review_payment(
    session: Session, tenant_id: str, tool: str, arguments: dict[str, Any]
) -> dict[str, Any]:
    session.expire_all()
    state = (
        _preview_customer_refund(session, tenant_id, arguments)
        if tool == "customer_refund_post"
        else _preview_invoice_payment(
            session,
            tenant_id,
            "customer" if tool == "customer_payment_post" else "supplier",
            arguments,
        )
    )
    creation = state["creation"]
    invoice = _tenant_record(session, Document, tenant_id, creation["invoice_id"])
    control = _tenant_record(
        session, LedgerEntry, tenant_id, creation["invoice_entry_id"]
    )
    party = _tenant_record(session, Party, tenant_id, creation["party_id"])
    source = (
        _tenant_record(session, SourceRecord, tenant_id, creation["source_record_id"])
        if creation["source_record_id"]
        else None
    )
    state.update(
        invoice=_values(invoice),
        control=_values(control),
        party={"id": party.id, "name": party.name},
        source={
            "id": source.id,
            "payload_hash": source.payload_hash,
            "source_system": source.source_system,
            "external_id": source.external_id,
        }
        if source
        else None,
        allocations=sorted(
            [
                _values(row)
                for row in active_settlement_allocations(session, tenant_id)
                if control.id
                in (row.invoice_ledger_entry_id, row.payment_ledger_entry_id)
            ],
            key=lambda row: row["id"],
        ),
    )
    state = json.loads(_json(state))
    intent = json.loads(_json(arguments))
    return {
        "version": 1,
        "tool": tool,
        "intent": intent,
        "state": state,
        "token": hashlib.sha256(
            _json([tenant_id, tool, intent, state]).encode()
        ).hexdigest(),
    }


def _assert_no_unresolved_payment(
    session: Session,
    tenant_id: str,
    arguments: dict[str, Any],
    exclude: str | None,
    tool: str = "customer_payment_post",
) -> None:
    from reality.services.financial_reversal_actions import _assert_financial_overlap

    _assert_financial_overlap(session, tenant_id, tool, arguments, exclude)
    target_key = "credit_note_id" if tool == "customer_refund_post" else "invoice_id"
    for candidate in session.scalars(
        select(ChangeProposal).where(
            ChangeProposal.tenant_id == tenant_id,
            ChangeProposal.status == "executing",
            ChangeProposal.type.in_([f"tool:{tool}" for tool in PAYMENT_TOOLS]),
        )
    ):
        if candidate.id != exclude and json.loads(candidate.input).get(
            target_key
        ) == arguments.get(target_key):
            raise InvalidOperation(
                "A financial execution for this record is unresolved. Check its outcome first."
            )


def _payment_evidence(
    session: Session, tenant_id: str, proposal: ChangeProposal, review: dict[str, Any]
):
    events = list(
        session.scalars(
            select(BusinessEvent).where(
                BusinessEvent.tenant_id == tenant_id,
                BusinessEvent.action_id == proposal.id,
            )
        )
    )
    families = {
        kind: [e for e in events if e.event_type == kind]
        for kind in ("document.recorded", "ledger.posted", "settlement.allocated")
    }
    if any(len(values) != 1 for values in families.values()):
        return None
    document_event = families["document.recorded"][0]
    ledger_event = families["ledger.posted"][0]
    allocation_event = families["settlement.allocated"][0]
    created = review["state"]["creation"]
    amount = Decimal(created["amount"])
    refund = created["direction"] == "customer_refund"
    customer = created["direction"] in {"customer", "customer_refund"}
    account = "accounts_receivable" if customer else "accounts_payable"
    effect = (
        [("cash", "debit"), (account, "credit")]
        if customer and not refund
        else [(account, "debit"), ("cash", "credit")]
    )
    document = session.scalar(
        select(Document).where(
            Document.tenant_id == tenant_id, Document.id == document_event.subject_id
        )
    )
    stated = json.loads(document_event.payload)
    source_id = created["source_record_id"]
    if (
        not document
        or document_event.subject_type != "document"
        or document.source_record_id != source_id
        or document_event.source_record_id != source_id
    ):
        return None
    document_type = "customer_refund" if refund else f"{created['direction']}_payment"
    if (
        stated.get("type") != document_type
        or stated.get("party_id") != created["party_id"]
        or stated.get("currency") != created["currency"]
        or Decimal(str(stated.get("amount", "-1"))) != amount
    ):
        return None
    if created["payment_number"] and stated.get("number") != created["payment_number"]:
        return None
    if not stated.get("number"):
        return None
    if refund and (
        document.type != document_type
        or document.party_id != created["party_id"]
        or document.currency != created["currency"]
        or document.gross_amount != amount
        or document.number != stated.get("number")
    ):
        return None
    source = None
    if source_id:
        source = session.scalar(
            select(SourceRecord).where(
                SourceRecord.tenant_id == tenant_id, SourceRecord.id == source_id
            )
        )
        if (
            not source
            or source.payload_hash != review["state"]["source"]["payload_hash"]
        ):
            return None
    posted = json.loads(ledger_event.payload)
    snapshots = posted.get("entries", [])
    if (
        ledger_event.subject_type != "posting_group"
        or ledger_event.source_record_id != source_id
        or posted.get("document_id") != document.id
        or posted.get("party_id") != created["party_id"]
        or posted.get("currency") != created["currency"]
    ):
        return None
    if len(snapshots) != 2 or len({e["id"] for e in snapshots}) != 2:
        return None
    entries = []
    for snapshot, (expected_account, side) in zip(snapshots, effect, strict=True):
        entry = session.scalar(
            select(LedgerEntry).where(
                LedgerEntry.tenant_id == tenant_id, LedgerEntry.id == snapshot["id"]
            )
        )
        if (
            not entry
            or entry.document_id != document.id
            or entry.posting_group_id != ledger_event.subject_id
            or entry.source_record_id != source_id
            or entry.party_id != created["party_id"]
            or entry.currency != created["currency"]
        ):
            return None
        if (
            entry.account != expected_account
            or entry.debit_credit != side
            or entry.amount != amount
        ):
            return None
        if (
            snapshot.get("account") != expected_account
            or snapshot.get("side") != side
            or Decimal(str(snapshot.get("amount", "-1"))) != amount
        ):
            return None
        if created["effective_at"] and utc_datetime(entry.effective_at) != utc_datetime(
            created["effective_at"]
        ):
            return None
        entries.append(entry)
    if refund and (
        document.document_date != utc_datetime(entries[0].effective_at).date()
        or utc_datetime(entries[0].effective_at)
        != utc_datetime(entries[1].effective_at)
        or utc_datetime(entries[0].effective_at)
        != utc_datetime(ledger_event.occurred_at)
    ):
        return None
    allocation = session.scalar(
        select(SettlementAllocation).where(
            SettlementAllocation.tenant_id == tenant_id,
            SettlementAllocation.id == allocation_event.subject_id,
        )
    )
    allocated = json.loads(allocation_event.payload)
    payment_entry = next(e for e in entries if e.account == account)
    if not allocation or allocation_event.subject_type != "settlement_allocation":
        return None
    for key, value in {
        "payment_ledger_entry_id": payment_entry.id,
        "invoice_ledger_entry_id": created["invoice_entry_id"],
        "currency": created["currency"],
    }.items():
        if getattr(allocation, key) != value or allocated.get(key) != value:
            return None
    if (
        allocation.amount != amount
        or Decimal(str(allocated.get("amount", "-1"))) != amount
    ):
        return None
    invoice_entry = session.scalar(
        select(LedgerEntry).where(
            LedgerEntry.tenant_id == tenant_id,
            LedgerEntry.id == created["invoice_entry_id"],
        )
    )
    if (
        not invoice_entry
        or invoice_entry.document_id != created["invoice_id"]
        or invoice_entry.account != account
    ):
        return None
    if json.loads(_json(_values(invoice_entry))) != review["state"]["control"]:
        return None
    receipt = {"records": [{"family": "ledger_entry", "id": e.id} for e in entries]}
    links = [
        {"kind": "document", "id": document.id},
        {"kind": "document", "id": created["invoice_id"]},
        *({"kind": "ledger_entry", "id": e.id} for e in entries),
        {"kind": "business_event", "id": allocation_event.id},
    ]
    if source:
        links.append({"kind": "source_record", "id": source.id})
    return (
        receipt,
        links,
        allocation.id,
        document.id,
        next(e.id for e in entries if e.account == "cash"),
    )


def _payment_detail(
    session: Session, tenant_id: str, proposal: ChangeProposal
) -> dict[str, Any]:
    review = json.loads(proposal.input).get("_delivery_review")
    result = {
        "id": proposal.id,
        "tool": proposal.type.removeprefix("tool:"),
        "status": proposal.status,
        "review": review,
        "receipt": json.loads(proposal.output)
        if proposal.status == "executed"
        else None,
        "verification": "pending" if proposal.status == "proposed" else "unresolved",
        "links": [],
        "observation": None,
        "observation_error": None,
    }
    if review and proposal.status in {"executed", "executing"}:
        try:
            evidence = _payment_evidence(session, tenant_id, proposal, review)
        except (
            ValueError,
            KeyError,
            TypeError,
            AttributeError,
            InvalidOperation,
            InvalidDecimal,
        ):
            evidence = None
        if evidence and (
            proposal.status != "executed" or result["receipt"] == evidence[0]
        ):
            result.update(
                verification="verified"
                if proposal.status == "executed"
                else "recorded_unsettled",
                links=evidence[1],
                recorded_receipt=evidence[0],
                payment_document_id=evidence[3],
                payment_entry_id=evidence[4],
            )
            try:
                result["observation"] = {
                    "open": str(
                        open_invoice_amount(
                            session,
                            tenant_id,
                            review["state"]["creation"]["invoice_id"],
                        )
                    ),
                    "allocation_active": any(
                        a.id == evidence[2]
                        for a in active_settlement_allocations(session, tenant_id)
                    ),
                }
            except (InvalidOperation, NotFound) as error:
                result["observation_error"] = str(error)
            except SQLAlchemyError:
                session.rollback()
                result["observation_error"] = (
                    "Current observation unavailable. Refresh this view."
                )
    return result


def _customer_credit_items(
    session: Session,
    tenant_id: str,
    *,
    query: str = "",
    status: str = "",
    page: int = 1,
    size: int = 50,
    sort: str = "",
    sort_direction: str = "asc",
) -> dict[str, Any]:
    """Read the credit register without adding credits to invoice projections."""
    from reality.services import core

    core.get_tenant(session, tenant_id)
    statement = (
        select(Document, Party.name)
        .outerjoin(
            Party, (Party.tenant_id == tenant_id) & (Party.id == Document.party_id)
        )
        .where(Document.tenant_id == tenant_id, Document.type == "credit_note")
    )
    if query.strip():
        from sqlalchemy import or_

        match = f"%{query.strip()}%"
        statement = statement.where(
            or_(
                Document.number.ilike(match),
                Party.name.ilike(match),
                Document.id.ilike(match),
            )
        )
    items = []
    totals = {}
    for document, party in session.execute(statement):
        try:
            opened = core.open_invoice_amount(session, tenant_id, document.id)
            control = core._settlement_control_entry(session, tenant_id, document.id)
        except core.InvalidOperation:
            continue
        reversed_ = core._ledger_reversal_for_group(
            session, tenant_id, control.posting_group_id
        )[0]
        state = (
            "reversed"
            if reversed_
            else "paid"
            if opened == 0
            else "partial"
            if opened < document.gross_amount
            else "open"
        )
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
            "document_date": day_text(document.document_date),
            "party_id": document.party_id,
            "party": party or "—",
            "gross": document.gross_amount,
            "settled": document.gross_amount - opened,
            "open": opened,
            "currency": document.currency,
            "status": state,
        }
        items.append(row)
        total = totals.setdefault(
            document.currency,
            {
                "currency": document.currency,
                "gross": Decimal(0),
                "settled": Decimal(0),
                "open": Decimal(0),
            },
        )
        for key in ("gross", "settled", "open"):
            total[key] += row[key]
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
        raise InvalidOperation("Unsupported credit sort.")
    items.sort(
        key=lambda row: (row[key] if row[key] is not None else "", row["document_id"]),
        reverse=sort_direction == "desc",
    )
    size = min(100, max(1, size))
    pages = max(1, (len(items) + size - 1) // size)
    page = min(pages, max(1, page))
    return json.loads(
        _json(
            {
                "items": items[(page - 1) * size : page * size],
                "totals": list(totals.values()),
                "page": {
                    "number": page,
                    "size": size,
                    "total": len(items),
                    "pages": pages,
                    "has_previous": page > 1,
                    "has_next": page < pages,
                },
            }
        )
    )
