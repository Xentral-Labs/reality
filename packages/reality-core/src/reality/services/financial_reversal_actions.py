"""Reviewed financial reversal with current effects and historical proof."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from decimal import Decimal
from typing import Any

from sqlalchemy import case, exists, func, or_, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from reality.db.core import (
    BusinessEvent,
    ChangeProposal,
    Document,
    LedgerEntry,
    LedgerReversal,
    Party,
)
from reality.services import core
from reality.services.order_actions import _json


def _reversal_choices(
    session: Session, tenant_id: str, query: str = "", page: int = 1
) -> dict[str, Any]:
    core.get_tenant(session, tenant_id)
    active = ~exists(
        select(LedgerReversal.id).where(
            LedgerReversal.tenant_id == tenant_id,
            or_(
                LedgerReversal.original_posting_group_id
                == LedgerEntry.posting_group_id,
                LedgerReversal.reversing_posting_group_id
                == LedgerEntry.posting_group_id,
            ),
        )
    )
    statement = (
        select(
            LedgerEntry.posting_group_id.label("id"),
            func.min(Document.number).label("number"),
            func.min(Party.name).label("party"),
            func.min(LedgerEntry.currency).label("currency"),
            func.sum(
                case((LedgerEntry.debit_credit == "debit", LedgerEntry.amount), else_=0)
            ).label("amount"),
            func.max(LedgerEntry.effective_at).label("date"),
        )
        .outerjoin(
            Document,
            (Document.tenant_id == tenant_id)
            & (Document.id == LedgerEntry.document_id),
        )
        .outerjoin(
            Party, (Party.tenant_id == tenant_id) & (Party.id == LedgerEntry.party_id)
        )
        .where(LedgerEntry.tenant_id == tenant_id, active)
    )
    if query:
        match = f"%{query}%"
        matching = (
            select(LedgerEntry.posting_group_id)
            .outerjoin(
                Document,
                (Document.tenant_id == tenant_id)
                & (Document.id == LedgerEntry.document_id),
            )
            .outerjoin(
                Party,
                (Party.tenant_id == tenant_id) & (Party.id == LedgerEntry.party_id),
            )
            .where(
                LedgerEntry.tenant_id == tenant_id,
                or_(
                    Document.number.ilike(match),
                    Party.name.ilike(match),
                    LedgerEntry.posting_group_id.ilike(match),
                ),
            )
        )
        statement = statement.where(LedgerEntry.posting_group_id.in_(matching))
    statement = statement.group_by(LedgerEntry.posting_group_id)
    total = session.scalar(select(func.count()).select_from(statement.subquery())) or 0
    pages = max(1, (total + 49) // 50)
    page = min(max(1, page), pages)
    rows = session.execute(
        statement.order_by(
            func.max(LedgerEntry.effective_at).desc(), LedgerEntry.posting_group_id
        )
        .offset((page - 1) * 50)
        .limit(50)
    ).mappings()
    return {
        "items": [
            {
                **row,
                "amount": str(row["amount"]),
                "number": row["number"] or row["id"],
                "party": row["party"] or "",
            }
            for row in rows
        ],
        "page": {
            "number": page,
            "size": 50,
            "total": total,
            "pages": pages,
            "has_previous": page > 1,
            "has_next": page < pages,
        },
    }


def _financial_keys(
    session: Session, tenant_id: str, tool: str, intent: dict[str, Any]
) -> set[str]:
    if tool in {
        "customer_payment_post",
        "supplier_payment_post",
        "customer_refund_post",
    }:
        return {
            core._settlement_control_entry(
                session,
                tenant_id,
                intent.get(
                    "credit_note_id"
                    if tool == "customer_refund_post"
                    else "invoice_id",
                    "",
                ),
            ).posting_group_id
        }
    group = intent.get("posting_group_id", "")
    entries = core._ledger_group_entries(session, tenant_id, group)
    allocations = core._allocations_for_entries(
        session, tenant_id, {e.id for e in entries}
    )
    ids = {
        i
        for row in allocations
        for i in (row.payment_ledger_entry_id, row.invoice_ledger_entry_id)
    }
    return {
        group,
        *session.scalars(
            select(LedgerEntry.posting_group_id).where(
                LedgerEntry.tenant_id == tenant_id, LedgerEntry.id.in_(ids)
            )
        ),
    }


def _assert_financial_overlap(
    session: Session,
    tenant_id: str,
    tool: str,
    intent: dict[str, Any],
    exclude: str | None = None,
) -> None:
    candidates = session.scalars(
        select(ChangeProposal).where(
            ChangeProposal.tenant_id == tenant_id,
            ChangeProposal.status == "executing",
            ChangeProposal.type.in_(
                [
                    "tool:ledger_reverse",
                    "tool:customer_payment_post",
                    "tool:supplier_payment_post",
                    "tool:customer_refund_post",
                ]
            ),
        )
    )
    keys = None
    for p in candidates:
        other = p.type.removeprefix("tool:")
        if p.id == exclude or (tool != "ledger_reverse" and other != "ledger_reverse"):
            continue
        if keys is None:
            keys = _financial_keys(session, tenant_id, tool, intent)
        if keys & _financial_keys(session, tenant_id, other, json.loads(p.input)):
            raise core.InvalidOperation(
                "An overlapping financial action is unresolved. Check its outcome first."
            )


def _reversal_effects(session: Session, tenant_id: str, group: str) -> dict[str, Any]:
    entries = core._ledger_group_entries(session, tenant_id, group)
    allocations = core._allocations_for_entries(
        session, tenant_id, {e.id for e in entries}
    )
    active = list(core.active_settlement_allocations(session, tenant_id))
    active_ids = {a.id for a in active}
    newly = [a for a in allocations if a.id in active_ids]
    ids = {e.id for e in entries} | {
        i
        for a in allocations
        for i in (a.payment_ledger_entry_id, a.invoice_ledger_entry_id)
    }
    related = list(
        session.scalars(
            select(LedgerEntry).where(
                LedgerEntry.tenant_id == tenant_id, LedgerEntry.id.in_(ids)
            )
        )
    )
    documents = sorted({e.document_id for e in related if e.document_id})
    invoices, payments = [], []
    for id_ in documents:
        doc = core._tenant_record(session, Document, tenant_id, id_)
        if doc.type in core.SETTLEMENT_CONTROL:
            control = core._settlement_control_entry(session, tenant_id, id_)
            before = core.open_invoice_amount(session, tenant_id, id_)
            after = (
                Decimal(0)
                if control.posting_group_id == group
                else before
                + sum(
                    (
                        a.amount
                        for a in newly
                        if control.id
                        in (a.payment_ledger_entry_id, a.invoice_ledger_entry_id)
                    ),
                    Decimal(0),
                )
            )
            invoices.append(
                {
                    "id": id_,
                    "number": doc.number,
                    "currency": doc.currency,
                    "before": before,
                    "after": after,
                }
            )
        if doc.type in {"customer_payment", "supplier_payment"}:
            control = next(
                (
                    e
                    for e in related
                    if e.document_id == id_
                    and e.account in {"accounts_receivable", "accounts_payable"}
                ),
                None,
            )
            if not control:
                continue
            reversed_ = (
                core._ledger_reversal_for_group(
                    session, tenant_id, control.posting_group_id
                )[0]
                is not None
            )
            before = (
                Decimal(0)
                if reversed_
                else control.amount
                - sum(
                    (
                        a.amount
                        for a in active
                        if control.id
                        in (a.payment_ledger_entry_id, a.invoice_ledger_entry_id)
                    ),
                    Decimal(0),
                )
            )
            after = (
                Decimal(0)
                if reversed_ or control.posting_group_id == group
                else before
                + sum(
                    (
                        a.amount
                        for a in newly
                        if control.id
                        in (a.payment_ledger_entry_id, a.invoice_ledger_entry_id)
                    ),
                    Decimal(0),
                )
            )
            payments.append(
                {
                    "id": id_,
                    "number": doc.number,
                    "currency": doc.currency,
                    "before": before,
                    "after": after,
                }
            )
    billing = []
    invoice_ids = {e.document_id for e in entries if e.document_id}
    order_line_ids = session.scalars(
        select(core.DocumentLine.billed_document_line_id)
        .join(
            Document,
            (Document.id == core.DocumentLine.document_id)
            & (Document.tenant_id == tenant_id),
        )
        .where(
            core.DocumentLine.tenant_id == tenant_id,
            Document.id.in_(invoice_ids),
            Document.type.in_(["sales_invoice", "supplier_invoice"]),
            core.DocumentLine.billed_document_line_id.is_not(None),
        )
        .distinct()
    )
    for line_id in sorted(order_line_ids):
        before = core._order_line_billing(session, tenant_id, line_id)
        after = core._order_line_billing(
            session, tenant_id, line_id, projected_reversal_group=group
        )
        billing.append(
            {
                **before,
                "invoiced_before": before["invoiced"],
                "invoiced_after": after["invoiced"],
                "remaining_before": before["remaining"],
                "remaining_after": after["remaining"],
            }
        )
    return {
        "billing": billing,
        "invoices": invoices,
        "payments": payments,
        "newly_inactive": [
            core._allocation_values(a) for a in sorted(newly, key=lambda a: a.id)
        ],
        "already_inactive": [
            core._allocation_values(a)
            for a in sorted(allocations, key=lambda a: a.id)
            if a.id not in active_ids
        ],
    }


def _review_reversal(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> dict[str, Any]:
    allowed = {"posting_group_id", "reason", "expected_revision", "preview_fingerprint"}
    if (
        not {"posting_group_id", "reason"} <= arguments.keys()
        or arguments.keys() - allowed
        or not isinstance(arguments["reason"], str)
    ):
        raise core.InvalidOperation("Reversal fields are incomplete or unsupported.")
    session.expire_all()
    preview = core.preview_ledger_reversal(
        session, tenant_id, arguments["posting_group_id"], reason=arguments["reason"]
    )
    if (
        arguments.get("expected_revision")
        and arguments["expected_revision"] != preview["revision"]
    ):
        raise core.InvalidOperation(
            "The financial context changed. Prepare a fresh review."
        )
    if (
        arguments.get("preview_fingerprint")
        and arguments["preview_fingerprint"] != preview["request_fingerprint"]
    ):
        raise core.InvalidOperation("Reversal preview does not match this reason.")
    for row in preview["inverse_entries"]:
        row["effective_at"] = None
    state = {
        "preview": preview,
        "effects": _reversal_effects(session, tenant_id, arguments["posting_group_id"]),
    }
    first = preview["original_entries"][0]
    party = (
        core._tenant_record(session, Party, tenant_id, first["party_id"])
        if first["party_id"]
        else None
    )
    state["party"] = {"id": party.id, "name": party.name} if party else None
    state["documents"] = [
        {"id": d.id, "number": d.number, "type": d.type}
        for d in session.scalars(
            select(Document)
            .where(
                Document.tenant_id == tenant_id,
                Document.id.in_(
                    {
                        e["document_id"]
                        for e in preview["original_entries"]
                        if e["document_id"]
                    }
                ),
            )
            .order_by(Document.id)
        )
    ]
    state = json.loads(_json(state))
    intent = json.loads(_json(arguments))
    return {
        "version": 1,
        "tool": "ledger_reverse",
        "intent": intent,
        "state": state,
        "token": hashlib.sha256(_json([tenant_id, intent, state]).encode()).hexdigest(),
    }


def _reversal_evidence(
    session: Session, tenant_id: str, proposal: ChangeProposal, review: dict[str, Any]
):
    events = list(
        session.scalars(
            select(BusinessEvent).where(
                BusinessEvent.tenant_id == tenant_id,
                BusinessEvent.action_id == proposal.id,
                BusinessEvent.event_type == "ledger.reversed",
            )
        )
    )
    if len(events) != 1:
        return None
    event = events[0]
    payload = json.loads(event.payload)
    relation = session.scalar(
        select(LedgerReversal).where(
            LedgerReversal.tenant_id == tenant_id,
            LedgerReversal.id == payload.get("reversal_id"),
        )
    )
    preview = review["state"]["preview"]
    if (
        not relation
        or event.subject_type != "posting_group"
        or event.subject_id != relation.original_posting_group_id
        or relation.original_posting_group_id != preview["posting_group_id"]
    ):
        return None
    if (
        relation.reason != preview["reason"]
        or payload.get("reason") != relation.reason
        or relation.request_fingerprint != preview["request_fingerprint"]
        or payload.get("reversing_posting_group_id")
        != relation.reversing_posting_group_id
    ):
        return None
    original = core._ledger_group_entries(
        session, tenant_id, relation.original_posting_group_id
    )
    inverse = core._ledger_group_entries(
        session, tenant_id, relation.reversing_posting_group_id
    )
    if core.utc_datetime(event.occurred_at) != core.utc_datetime(relation.reversed_at):
        return None
    originals = [core._ledger_entry_values(e) for e in original]
    inverses = [core._ledger_entry_values(e) for e in inverse]
    if json.loads(_json(originals)) != json.loads(
        _json(preview["original_entries"])
    ) or json.loads(_json(payload.get("original_entries"))) != json.loads(
        _json(originals)
    ):
        return None
    if sorted(payload.get("affected_allocation_ids", [])) != sorted(
        a["id"] for a in preview["affected_allocations"]
    ):
        return None
    if json.loads(
        _json(sorted(payload.get("reversing_entries", []), key=lambda e: e["id"]))
    ) != json.loads(_json(inverses)):
        return None
    signature = lambda e: (e.account, e.party_id, e.currency, e.amount, e.debit_credit)
    expected = Counter(
        (
            e.account,
            e.party_id,
            e.currency,
            e.amount,
            "credit" if e.debit_credit == "debit" else "debit",
        )
        for e in original
    )
    if Counter(signature(e) for e in inverse) != expected or any(
        e.document_id
        or e.source_record_id
        or core.utc_datetime(e.effective_at) != core.utc_datetime(relation.reversed_at)
        for e in inverse
    ):
        return None
    receipt = {
        "reversal_id": relation.id,
        "original_posting_group_id": relation.original_posting_group_id,
        "reversing_posting_group_id": relation.reversing_posting_group_id,
        "replayed": False,
    }
    links = [{"kind": "ledger_entry", "id": e.id} for e in original + inverse] + [
        {"kind": "business_event", "id": event.id}
    ]
    return receipt, links


def _reversal_detail(
    session: Session, tenant_id: str, proposal: ChangeProposal
) -> dict[str, Any]:
    review = json.loads(proposal.input).get("_delivery_review")
    result = {
        "id": proposal.id,
        "tool": "ledger_reverse",
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
            evidence = _reversal_evidence(session, tenant_id, proposal, review)
        except (
            ValueError,
            KeyError,
            TypeError,
            AttributeError,
            core.InvalidOperation,
            core.NotFound,
        ):
            evidence = None
        if evidence and (
            proposal.status != "executed" or result["receipt"] == evidence[0]
        ):
            result.update(
                verification="verified"
                if proposal.status == "executed"
                else "recorded_unsettled",
                recorded_receipt=evidence[0],
                links=evidence[1],
            )
            try:
                result["observation"] = json.loads(
                    _json(
                        _reversal_effects(
                            session, tenant_id, review["intent"]["posting_group_id"]
                        )
                    )
                )
            except (core.InvalidOperation, core.NotFound) as error:
                result["observation_error"] = str(error)
            except SQLAlchemyError:
                session.rollback()
                result["observation_error"] = (
                    "Current observation unavailable. Refresh this view."
                )
    return result
