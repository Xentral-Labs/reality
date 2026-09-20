"""Invoice-linked credits through canonical evidence, postings and settlement."""

from __future__ import annotations

import hashlib
import json
from decimal import Decimal
from decimal import InvalidOperation as DecimalInvalidOperation
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from reality.db.core import (
    BusinessEvent,
    ChangeProposal,
    Document,
    DocumentLine,
    LedgerEntry,
    LedgerReversal,
    SettlementAllocation,
    SourceRecord,
)
from reality.services import core
from reality.services.core import emit_business_event
from reality.services.order_actions import _canonical, _json


def _released(
    session: Session, tenant: str, document: str
) -> tuple[bool, list[str], list[str]]:
    groups = sorted(
        set(
            session.scalars(
                select(LedgerEntry.posting_group_id).where(
                    LedgerEntry.tenant_id == tenant, LedgerEntry.document_id == document
                )
            )
        )
    )
    reversals = list(
        session.scalars(
            select(LedgerReversal)
            .where(
                LedgerReversal.tenant_id == tenant,
                LedgerReversal.original_posting_group_id.in_(groups),
            )
            .order_by(LedgerReversal.id)
        )
    )
    return (
        bool(groups)
        and set(groups) <= {r.original_posting_group_id for r in reversals},
        groups,
        [r.id for r in reversals],
    )


def _credit_context(session: Session, tenant: str, invoice_id: str) -> dict[str, Any]:
    invoice = core._tenant_record(session, Document, tenant, invoice_id)
    if invoice.type != "sales_invoice":
        raise core.InvalidOperation("Select a customer invoice.")
    _, groups, reversals = _released(session, tenant, invoice.id)
    if not groups or reversals:
        raise core.InvalidOperation(
            "Credit requires a posted invoice without reversed posting groups."
        )
    invoice_lines = list(
        session.scalars(
            select(DocumentLine)
            .where(
                DocumentLine.tenant_id == tenant, DocumentLine.document_id == invoice.id
            )
            .order_by(DocumentLine.source_line_id, DocumentLine.id)
        )
    )
    ids = [line.id for line in invoice_lines]
    credit_rows = list(
        session.execute(
            select(DocumentLine, Document)
            .join(
                Document,
                (Document.id == DocumentLine.document_id)
                & (Document.tenant_id == tenant),
            )
            .where(
                DocumentLine.tenant_id == tenant,
                DocumentLine.billed_document_line_id.in_(ids),
                Document.type == "credit_note",
            )
            .order_by(Document.id, DocumentLine.id)
        )
    )
    credit_documents = {doc.id: doc for _, doc in credit_rows}
    state = {id_: _released(session, tenant, id_) for id_ in credit_documents}
    # A header spanning several invoices has no attributable invoice-level amount.
    for id_ in credit_documents:
        targets = set(
            session.scalars(
                select(DocumentLine.billed_document_line_id).where(
                    DocumentLine.tenant_id == tenant, DocumentLine.document_id == id_
                )
            )
        )
        if not targets <= set(ids):
            raise core.InvalidOperation(
                "An existing credit spans other evidence. Inspect its attribution first."
            )
    credited_amount = sum(
        (
            doc.gross_amount
            for id_, doc in credit_documents.items()
            if not state[id_][0]
        ),
        Decimal(0),
    )
    positions = []
    for line in invoice_lines:
        evidence = [
            {
                "id": credit.id,
                "number": credit.number,
                "line_id": row.id,
                "quantity": row.quantity,
                "released": state[credit.id][0],
                "groups": state[credit.id][1],
                "reversals": state[credit.id][2],
            }
            for row, credit in credit_rows
            if row.billed_document_line_id == line.id
        ]
        credited = sum(
            (row["quantity"] for row in evidence if not row["released"]), Decimal(0)
        )
        legacy = []
        if line.billed_document_line_id:
            legacy = list(
                session.scalars(
                    select(Document.id)
                    .join(
                        DocumentLine,
                        (DocumentLine.document_id == Document.id)
                        & (DocumentLine.tenant_id == tenant),
                    )
                    .where(
                        Document.tenant_id == tenant,
                        Document.type == "credit_note",
                        DocumentLine.billed_document_line_id
                        == line.billed_document_line_id,
                    )
                    .order_by(Document.id)
                )
            )
        positions.append(
            {
                "id": line.id,
                "label": line.description or line.sku or line.id,
                "quantity": line.quantity,
                "unit": line.unit,
                "unit_price": line.unit_price,
                "item_id": line.item_id,
                "credited": credited,
                "remaining": max(line.quantity - credited, Decimal(0)),
                "legacy_credit_ids": sorted(set(legacy)),
                "evidence": evidence,
            }
        )
    return {
        "invoice": {
            "id": invoice.id,
            "number": invoice.number,
            "currency": invoice.currency,
            "gross_amount": invoice.gross_amount,
            "party_id": invoice.party_id,
        },
        "party": {
            "name": core._tenant_record(
                session, core.Party, tenant, invoice.party_id
            ).name
        },
        "groups": groups,
        "reversals": reversals,
        "open_amount": core.open_invoice_amount(session, tenant, invoice.id),
        "credited_amount": credited_amount,
        "remaining_amount": max(invoice.gross_amount - credited_amount, Decimal(0)),
        "positions": positions,
    }


def _exact(value: Any, label: str, *, zero: bool = False) -> Decimal:
    try:
        amount = core.decimal(value)
    except (DecimalInvalidOperation, ValueError, TypeError) as error:
        raise core.InvalidOperation(f"{label} must be a decimal value.") from error
    if (
        amount < 0
        or (not zero and amount == 0)
        or amount >= Decimal(100000000000000)
        or amount != amount.quantize(Decimal("0.0001"))
    ):
        raise core.InvalidOperation(
            f"{label} must be positive and fit four decimal places without rounding."
        )
    return amount


def _preview_credit(
    session: Session, tenant: str, arguments: dict[str, Any]
) -> tuple[dict, dict]:
    fields = {
        "invoice_id",
        "lines",
        "gross_amount",
        "number",
        "reason",
        "allocation_amount",
    }
    if not fields <= arguments.keys() or arguments.keys() - fields - {"effective_at"}:
        raise core.InvalidOperation("Credit fields are incomplete or unsupported.")
    reason = arguments["reason"].strip() if isinstance(arguments["reason"], str) else ""
    if not reason:
        raise core.InvalidOperation("A credit reason is required.")
    context = _credit_context(session, tenant, arguments["invoice_id"])
    if any(row["legacy_credit_ids"] for row in context["positions"]):
        raise core.InvalidOperation(
            "An older order-linked credit has no invoice attribution. Inspect it before crediting this invoice."
        )
    rows = arguments["lines"]
    if not isinstance(rows, list) or not rows:
        raise core.InvalidOperation("Select at least one credit position.")
    selected = []
    seen = set()
    for row in rows:
        if not isinstance(row, dict) or set(row) != {
            "invoice_line_id",
            "quantity",
            "gross_amount",
        }:
            raise core.InvalidOperation(
                "Credit position fields are incomplete or unsupported."
            )
        id_ = row["invoice_line_id"]
        if not isinstance(id_, str) or id_ in seen:
            raise core.InvalidOperation("Credit positions must be distinct.")
        seen.add(id_)
        line = next((p for p in context["positions"] if p["id"] == id_), None)
        if not line:
            raise core.NotFound("Invoice position not found.")
        if line["legacy_credit_ids"]:
            raise core.InvalidOperation(
                "An older order-linked credit has no invoice attribution. Inspect it before crediting this position."
            )
        quantity = _exact(row["quantity"], "quantity")
        amount = _exact(row["gross_amount"], "line amount")
        if quantity > line["remaining"]:
            raise core.InvalidOperation(
                "Credit quantity exceeds the remaining invoice quantity."
            )
        selected.append(
            {"invoice_line_id": id_, "quantity": quantity, "gross_amount": amount}
        )
    amount = _exact(arguments["gross_amount"], "credit amount")
    allocation = _exact(arguments["allocation_amount"], "allocation amount", zero=True)
    if amount > context["remaining_amount"]:
        raise core.InvalidOperation(
            "Credit amount exceeds the remaining invoice amount."
        )
    if allocation > min(amount, context["open_amount"]):
        raise core.InvalidOperation(
            "Allocation exceeds the credit or open invoice amount."
        )
    effective = core.utc_datetime(arguments.get("effective_at"))
    document, lines = core._preview_manual_document_input(
        session,
        tenant,
        "credit_note",
        arguments["number"],
        context["invoice"]["party_id"],
        [
            {
                "item_id": next(
                    p for p in context["positions"] if p["id"] == row["invoice_line_id"]
                )["item_id"],
                "quantity": row["quantity"],
                "unit": next(
                    p for p in context["positions"] if p["id"] == row["invoice_line_id"]
                )["unit"],
                "unit_price": next(
                    p for p in context["positions"] if p["id"] == row["invoice_line_id"]
                )["unit_price"],
                "gross_amount": row["gross_amount"],
                "billed_document_line_id": row["invoice_line_id"],
            }
            for row in selected
        ],
        amount,
        currency=context["invoice"]["currency"],
        document_date=effective.date().isoformat() if effective else "",
    )
    creation = {
        "invoice_id": arguments["invoice_id"],
        "selections": selected,
        "gross_amount": amount,
        "number": document["number"],
        "reason": reason,
        "allocation_amount": allocation,
        "effective_at": effective,
        "document": document,
        "lines": lines,
    }
    return creation, context


def _review_credit(session: Session, tenant: str, arguments: dict[str, Any]) -> dict:
    session.expire_all()
    creation, context = _preview_credit(session, tenant, arguments)
    state = json.loads(
        _json(
            {
                "creation": creation,
                "context": context,
                "invoice_after": context["open_amount"] - creation["allocation_amount"],
                "credit_open": creation["gross_amount"] - creation["allocation_amount"],
            }
        )
    )
    intent = json.loads(_json(arguments))
    return {
        "version": 1,
        "tool": "sales_credit_record",
        "intent": intent,
        "state": state,
        "token": hashlib.sha256(_json([tenant, intent, state]).encode()).hexdigest(),
    }


def _snapshot(record):
    return {
        column.name: getattr(record, column.name) for column in record.__table__.columns
    }


def _record_invoice_credit(
    session: Session, tenant: str, arguments: dict, action_id: str | None
) -> dict:
    from reality.services.tenant_policy import require_decision_finance

    require_decision_finance(
        session, tenant, "sales_credit_record", arguments, action_id
    )
    session.expire_all()
    with session.begin_nested():
        creation, context = _preview_credit(session, tenant, arguments)
        effective = creation["effective_at"] or core.now()
        source = core.create_master_source_record(
            session,
            tenant,
            "credit_note",
            "manual",
            action_id or core.uid("credit"),
            {**arguments, "effective_at": effective.isoformat()},
            action_id=action_id,
            _commit=False,
        )
        note, lines = core.create_manual_document_with_lines(
            session,
            tenant,
            "credit_note",
            creation["number"],
            context["invoice"]["party_id"],
            creation["lines"],
            creation["gross_amount"],
            currency=context["invoice"]["currency"],
            document_date=effective.date().isoformat(),
            source_record_id=source.id,
            action_id=action_id,
            _commit=False,
        )
        entries = core.post_sales_credit_note(
            session,
            tenant,
            note.id,
            effective_at=effective,
            action_id=action_id,
            _commit=False,
        )
        allocation = None
        if creation["allocation_amount"]:
            allocation = core.allocate_settlement(
                session,
                tenant,
                core._control_entry(entries, "accounts_receivable").id,
                core._settlement_control_entry(
                    session, tenant, creation["invoice_id"]
                ).id,
                creation["allocation_amount"],
                action_id=action_id,
                _commit=False,
            )
        objects = [
            ("source_record", source),
            ("document", note),
            *[("document_line", row) for row in lines],
            *[("ledger_entry", row) for row in entries],
            *([("settlement_allocation", allocation)] if allocation else []),
        ]
        receipt = {
            "records": [
                {"family": family, "id": record.id} for family, record in objects
            ]
        }
        emit_business_event(
            session,
            tenant,
            "credit.recorded",
            "document",
            note.id,
            {
                "creation": creation,
                "receipt": receipt,
                "snapshots": [
                    {"family": family, "record": _snapshot(record)}
                    for family, record in objects
                ],
            },
            source_record_id=source.id,
            action_id=action_id,
            correlation_id=action_id,
        )
    session.commit()
    return receipt


def _assert_credit_overlap(
    session: Session, tenant: str, arguments: dict, exclude: str | None
) -> None:
    for p in session.scalars(
        select(ChangeProposal).where(
            ChangeProposal.tenant_id == tenant,
            ChangeProposal.type == "tool:sales_credit_record",
            ChangeProposal.status == "executing",
        )
    ):
        if p.id != exclude and json.loads(p.input).get("invoice_id") == arguments.get(
            "invoice_id"
        ):
            raise core.InvalidOperation(
                "An invoice credit execution is unresolved. Check its outcome first."
            )


def _credit_evidence(
    session: Session, tenant: str, proposal: ChangeProposal, review: dict
):
    events = list(
        session.scalars(
            select(BusinessEvent).where(
                BusinessEvent.tenant_id == tenant,
                BusinessEvent.action_id == proposal.id,
            )
        )
    )
    recorded = [e for e in events if e.event_type == "credit.recorded"]
    if len(recorded) != 1:
        return None
    event = recorded[0]
    payload = json.loads(event.payload)
    creation = review["state"]["creation"]
    if _canonical(payload["creation"]) != _canonical(creation):
        return None
    families = {
        "source_record": SourceRecord,
        "document": Document,
        "document_line": DocumentLine,
        "ledger_entry": LedgerEntry,
        "settlement_allocation": SettlementAllocation,
    }
    expected = (
        ["source_record", "document"]
        + ["document_line"] * len(creation["selections"])
        + ["ledger_entry"] * 2
        + (["settlement_allocation"] if Decimal(creation["allocation_amount"]) else [])
    )
    records = payload["receipt"]["records"]
    snapshots = payload["snapshots"]
    if (
        [r["family"] for r in records] != expected
        or len(snapshots) != len(records)
        or len({r["id"] for r in records}) != len(records)
    ):
        return None
    objects = []
    for reference, snapshot in zip(records, snapshots, strict=True):
        if (
            snapshot["family"] != reference["family"]
            or snapshot["record"]["id"] != reference["id"]
        ):
            return None
        record = core._tenant_record(
            session, families[reference["family"]], tenant, reference["id"]
        )
        if _canonical(json.loads(_json(_snapshot(record)))) != _canonical(
            snapshot["record"]
        ):
            return None
        objects.append(record)
    source, note = objects[:2]
    effective = core.utc_datetime(json.loads(source.payload).get("effective_at"))
    if not effective or (
        creation.get("effective_at")
        and effective != core.utc_datetime(creation["effective_at"])
    ):
        return None
    line_count = len(creation["selections"])
    lines = objects[2 : 2 + line_count]
    entries = objects[2 + line_count : 4 + line_count]
    if (
        note.number != creation["number"]
        or note.document_date != effective.date()
        or note.type != "credit_note"
        or note.source_record_id != source.id
        or note.party_id != review["state"]["context"]["invoice"]["party_id"]
        or note.currency != review["state"]["context"]["invoice"]["currency"]
        or note.gross_amount != Decimal(creation["gross_amount"])
    ):
        return None
    stated = json.loads(source.payload)
    if any(
        _canonical(stated.get(key)) != _canonical(value)
        for key, value in review["intent"].items()
        if key != "effective_at"
    ):
        return None
    if (
        event.subject_id != note.id
        or event.subject_type != "document"
        or event.source_record_id != source.id
    ):
        return None
    for line, selected in zip(lines, creation["selections"], strict=True):
        if (
            line.document_id != note.id
            or line.billed_document_line_id != selected["invoice_line_id"]
            or line.quantity != Decimal(selected["quantity"])
            or line.gross_amount != Decimal(selected["gross_amount"])
        ):
            return None
    if {(e.account, e.debit_credit) for e in entries} != {
        ("sales_revenue", "debit"),
        ("accounts_receivable", "credit"),
    } or len({e.posting_group_id for e in entries}) != 1:
        return None
    if any(
        e.effective_at != effective
        or e.document_id != note.id
        or e.source_record_id != source.id
        or e.amount != note.gross_amount
        or e.party_id != note.party_id
        or e.currency != note.currency
        for e in entries
    ):
        return None
    docs = [e for e in events if e.event_type == "document.recorded"]
    posts = [e for e in events if e.event_type == "ledger.posted"]
    if (
        len(docs) != 1
        or json.loads(docs[0].payload).get("document_line_ids") != [r.id for r in lines]
        or len(posts) != 1
        or posts[0].subject_id != entries[0].posting_group_id
    ):
        return None
    for line, expected in zip(lines, creation["lines"], strict=True):
        line_payload = json.loads(line.payload or "{}")
        actual = {
            key: (
                line_payload.get("reality_finance_v1")
                if key == "reality_finance_v1"
                else getattr(line, key)
            )
            for key in expected
            if key != "id"
        }
        wanted = {key: value for key, value in expected.items() if key != "id"}
        if _canonical(json.loads(_json(actual))) != _canonical(wanted):
            return None
    if Decimal(creation["allocation_amount"]):
        allocation = objects[-1]
        if (
            allocation.currency != note.currency
            or allocation.amount != Decimal(creation["allocation_amount"])
            or allocation.payment_ledger_entry_id
            != core._control_entry(entries, "accounts_receivable").id
        ):
            return None
        target = core._tenant_record(
            session, LedgerEntry, tenant, allocation.invoice_ledger_entry_id
        )
        if target.document_id != creation["invoice_id"]:
            return None
    return payload["receipt"], [
        {"kind": r["family"], "id": r["id"]} for r in records
    ] + [{"kind": "business_event", "id": event.id}]


def _credit_detail(session: Session, tenant: str, proposal: ChangeProposal) -> dict:
    review = json.loads(proposal.input).get("_delivery_review")
    result = {
        "id": proposal.id,
        "tool": "sales_credit_record",
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
    if review and proposal.status in {"executing", "executed"}:
        try:
            proof = _credit_evidence(session, tenant, proposal, review)
        except (KeyError, ValueError, TypeError, AttributeError, core.NotFound):
            proof = None
        if proof and (proposal.status != "executed" or result["receipt"] == proof[0]):
            result.update(
                verification="verified"
                if proposal.status == "executed"
                else "recorded_unsettled",
                links=proof[1],
                recorded_receipt=proof[0],
            )
    return result
