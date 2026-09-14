"""State-bound invoice reviews and exact historical financial evidence."""

from __future__ import annotations

import hashlib
import json
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from reality.db.core import (
    BusinessEvent,
    ChangeProposal,
    Document,
    DocumentLine,
    Item,
    LedgerEntry,
    Party,
    SourceRecord,
)
from reality.services.core import (
    InvalidOperation,
    _order_line_billing,
    _preview_order_invoice,
    _tenant_record,
)
from reality.services.order_actions import _json

INVOICE_TOOLS = {"sales_invoice_record", "supplier_invoice_record"}


def _review_invoice(
    session: Session, tenant_id: str, tool: str, arguments: dict[str, Any]
) -> dict[str, Any]:
    session.expire_all()
    direction = "sales" if tool == "sales_invoice_record" else "purchase"
    creation = _preview_order_invoice(session, tenant_id, direction, arguments)
    line = _tenant_record(session, DocumentLine, tenant_id, creation["order_line_id"])
    order = _tenant_record(session, Document, tenant_id, line.document_id)
    party = _tenant_record(session, Party, tenant_id, order.party_id)
    item = _tenant_record(session, Item, tenant_id, line.item_id)
    state = json.loads(
        _json(
            {
                "creation": creation,
                "order": {
                    column.name: getattr(order, column.name)
                    for column in Document.__table__.columns
                },
                "line": {
                    column.name: getattr(line, column.name)
                    for column in DocumentLine.__table__.columns
                },
                "party": {"id": party.id, "name": party.name},
                "item": {"id": item.id, "name": item.name},
            }
        )
    )
    if "selections" in creation:
        state["positions"] = []
        for selected in creation["selections"]:
            selected_line = _tenant_record(
                session, DocumentLine, tenant_id, selected["order_line_id"]
            )
            selected_item = _tenant_record(
                session, Item, tenant_id, selected_line.item_id
            )
            state["positions"].append(
                json.loads(
                    _json(
                        {
                            "line": {
                                column.name: getattr(selected_line, column.name)
                                for column in DocumentLine.__table__.columns
                            },
                            "item": {
                                "id": selected_item.id,
                                "name": selected_item.name,
                            },
                            **selected,
                        }
                    )
                )
            )
    state["billing"] = []
    for selected in creation.get("selections", [creation]):
        billing = _order_line_billing(session, tenant_id, selected["order_line_id"])
        state["billing"].append(
            json.loads(
                _json(
                    {
                        **billing,
                        "requested": selected["quantity"],
                        "remaining_after": billing["remaining"] - selected["quantity"],
                    }
                )
            )
        )
    intent = json.loads(_json(arguments))
    return {
        "version": 1,
        "tool": tool,
        "intent": intent,
        "state": state,
        "effect": {
            "debit": "accounts_receivable" if direction == "sales" else "inventory",
            "credit": "sales_revenue" if direction == "sales" else "accounts_payable",
        },
        "token": hashlib.sha256(
            _json([tenant_id, tool, intent, state]).encode()
        ).hexdigest(),
    }


def _assert_no_unresolved_invoice(
    session: Session, tenant_id: str, arguments: dict[str, Any], exclude: str | None
) -> None:
    for proposal in session.scalars(
        select(ChangeProposal).where(
            ChangeProposal.tenant_id == tenant_id,
            ChangeProposal.status == "executing",
            ChangeProposal.type.in_([f"tool:{tool}" for tool in INVOICE_TOOLS]),
        )
    ):

        def selected_ids(value):
            return (
                {row.get("order_line_id") for row in value.get("lines", [])}
                if "lines" in value
                else {value.get("order_line_id")}
            )

        if proposal.id != exclude and selected_ids(
            json.loads(proposal.input)
        ) & selected_ids(arguments):
            raise InvalidOperation(
                "An invoice execution for this order line is unresolved. Check its outcome first."
            )


def _invoice_evidence(
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
    recorded = [e for e in events if e.event_type == "invoice.recorded"]
    if len(recorded) != 1:
        return None
    event = recorded[0]
    payload = json.loads(event.payload)
    # Normalize database decimal scale and UTC spellings through shared serialization.
    from reality.services.core import utc_datetime
    from reality.services.order_actions import _canonical as order_canonical

    def _canonical(value):
        if isinstance(value, dict):
            return {
                k: format(Decimal(str(v)).normalize(), "f")
                if k == "amount"
                else _canonical(v)
                for k, v in value.items()
            }
        if isinstance(value, list):
            return [_canonical(v) for v in value]
        return value

    def canonical(value):
        return _canonical(order_canonical(value))

    creation = payload.get("creation", {})
    expected = review["state"]["creation"]
    if canonical(creation) != canonical(expected):
        return None
    selections = creation.get("selections", [creation])
    count = len(selections)
    records = payload.get("receipt", {}).get("records", [])
    if (
        not isinstance(records, list)
        or len(records) != count + 4
        or any(not isinstance(r, dict) for r in records)
    ):
        return None
    ids = {
        family: [r.get("id") for r in records if r.get("family") == family]
        for family in ("source_record", "document", "document_line", "ledger_entry")
    }
    if [len(ids[k]) for k in ids] != [1, 1, count, 2] or len(
        {r.get("id") for r in records}
    ) != count + 4:
        return None
    source = session.scalar(
        select(SourceRecord).where(
            SourceRecord.tenant_id == tenant_id,
            SourceRecord.id == ids["source_record"][0],
        )
    )
    doc = session.scalar(
        select(Document).where(
            Document.tenant_id == tenant_id, Document.id == ids["document"][0]
        )
    )
    if not source or not doc or doc.source_record_id != source.id:
        return None
    for line_id, selected in zip(ids["document_line"], selections, strict=True):
        line = session.scalar(
            select(DocumentLine).where(
                DocumentLine.tenant_id == tenant_id, DocumentLine.id == line_id
            )
        )
        if (
            not line
            or line.document_id != doc.id
            or line.billed_document_line_id != selected["order_line_id"]
        ):
            return None
        if "selections" in creation and (
            line.quantity != Decimal(str(selected["quantity"]))
            or line.gross_amount != Decimal(str(selected["gross_amount"]))
        ):
            return None
    if (
        event.subject_type != "document"
        or event.subject_id != doc.id
        or event.source_record_id != source.id
    ):
        return None
    stated = json.loads(source.payload)
    if "selections" in creation and canonical(stated.get("lines")) != canonical(
        creation["selections"]
    ):
        return None
    for key in (
        ("gross_amount", "currency")
        if "selections" in creation
        else ("order_line_id", "quantity", "gross_amount", "currency")
    ):
        if canonical({key: stated.get(key)}) != canonical({key: creation[key]}):
            return None
    if stated.get("number") != review["intent"]["number"] or utc_datetime(
        stated.get("effective_at")
    ) != utc_datetime(payload.get("effective_at")):
        return None
    if creation.get("effective_at") and utc_datetime(
        creation["effective_at"]
    ) != utc_datetime(payload.get("effective_at")):
        return None
    docs = [e for e in events if e.event_type == "document.recorded"]
    posted = [e for e in events if e.event_type == "ledger.posted"]
    if (
        len(docs) != 1
        or docs[0].subject_id != doc.id
        or json.loads(docs[0].payload).get("document_line_ids") != ids["document_line"]
        or len(posted) != 1
    ):
        return None
    entries = list(
        session.scalars(
            select(LedgerEntry).where(
                LedgerEntry.tenant_id == tenant_id,
                LedgerEntry.id.in_(ids["ledger_entry"]),
            )
        )
    )
    if len(entries) != 2 or len({e.posting_group_id for e in entries}) != 1:
        return None
    snapshots = payload.get("entries", [])
    if len(snapshots) != 2 or {e.get("id") for e in snapshots} != set(
        ids["ledger_entry"]
    ):
        return None
    for entry in entries:
        snapshot = next(e for e in snapshots if e["id"] == entry.id)
        actual = json.loads(_json({key: getattr(entry, key) for key in snapshot}))
        if canonical(snapshot) != canonical(actual):
            return None
        if (
            entry.document_id != doc.id
            or entry.source_record_id != source.id
            or entry.party_id != creation["party_id"]
            or entry.currency != creation["currency"]
            or str(entry.amount.normalize())
            != str(Decimal(creation["gross_amount"]).normalize())
        ):
            return None
        if utc_datetime(entry.effective_at) != utc_datetime(
            payload.get("effective_at")
        ):
            return None
    effects = review["effect"]
    if {(e.account, e.debit_credit) for e in entries} != {
        (effects["debit"], "debit"),
        (effects["credit"], "credit"),
    } or posted[0].subject_id != entries[0].posting_group_id:
        return None
    post = json.loads(posted[0].payload)
    if (
        post.get("document_id") != doc.id
        or post.get("party_id") != creation["party_id"]
        or post.get("currency") != creation["currency"]
    ):
        return None
    if canonical(sorted(post.get("entries", []), key=lambda e: e["id"])) != canonical(
        sorted(
            [
                {
                    "id": e.id,
                    "account": e.account,
                    "account_id": e.account_id,
                    "side": e.debit_credit,
                    "amount": str(e.amount),
                }
                for e in entries
            ],
            key=lambda e: e["id"],
        )
    ):
        return None
    return payload["receipt"], [
        {"kind": r["family"], "id": r["id"]} for r in records
    ] + [{"kind": "business_event", "id": event.id}]


def _invoice_detail(
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
    if review and proposal.status in {"executing", "executed"}:
        try:
            evidence = _invoice_evidence(session, tenant_id, proposal, review)
        except (KeyError, ValueError, TypeError, AttributeError):
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
            )
    return result
