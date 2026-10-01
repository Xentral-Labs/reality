"""The reviewed tools that record down-payment and pro-forma invoices (spec 299)."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from reality.db.core import ChangeProposal, Document, SourceRecord
from reality.services import core

DOWN_PAYMENT_FIELDS = {"order_id", "number", "gross_amount"}
DOWN_PAYMENT_OPTIONAL = {"currency", "effective_at", "net_amount", "tax_amount"}
BILLING_DOCUMENT_TOOLS = {"down_payment_invoice_record"}


def _json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, default=str, separators=(",", ":"))


def _intent(arguments: dict[str, Any]) -> dict[str, Any]:
    if not DOWN_PAYMENT_FIELDS <= set(arguments) or set(arguments) - (
        DOWN_PAYMENT_FIELDS | DOWN_PAYMENT_OPTIONAL
    ):
        raise core.InvalidOperation(code="down_payment_fields_invalid")
    return {
        key: (str(value) if value is not None else None)
        for key, value in sorted(arguments.items())
    }


def review_billing_document(
    session: Session, tenant_id: str, tool: str, arguments: dict[str, Any]
) -> dict[str, Any]:
    from reality.services.down_payments import preview_down_payment_invoice

    intent = _intent(arguments)
    state = json.loads(
        _json(preview_down_payment_invoice(session, tenant_id, **intent))
    )
    pinned = {key: state[key] for key in ("order_id", "gross_amount", "currency")}
    return {
        "version": 1,
        "tool": tool,
        "intent": intent,
        "state": state,
        "effect": {
            "order_id": state["order_id"],
            "gross_amount": state["gross_amount"],
            "bills_quantity": False,
            "money_moves": False,
            "creates": ["document", "ledger_entry"],
        },
        "token": hashlib.sha256(
            _json([tenant_id, tool, intent, pinned]).encode()
        ).hexdigest(),
    }


def assert_no_unresolved_billing_document(
    session: Session,
    tenant_id: str,
    tool: str,
    arguments: dict[str, Any],
    exclude: str | None,
) -> None:
    for proposal in session.scalars(
        select(ChangeProposal).where(
            ChangeProposal.tenant_id == tenant_id,
            ChangeProposal.type == f"tool:{tool}",
            ChangeProposal.status == "executing",
        )
    ):
        saved = json.loads(proposal.input)
        if proposal.id != exclude and (saved.get("order_id"), saved.get("number")) == (
            arguments.get("order_id"),
            arguments.get("number"),
        ):
            raise core.InvalidOperation(code="down_payment_record_unresolved")


def billing_document_detail(
    session: Session, tenant_id: str, proposal: ChangeProposal
) -> dict[str, Any]:
    from reality.services.down_payments import SOURCE_SYSTEM

    tool = proposal.type.removeprefix("tool:")
    review = json.loads(proposal.input).get("_delivery_review")
    result: dict[str, Any] = {
        "id": proposal.id,
        "tool": tool,
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
    document = session.scalar(
        select(Document)
        .join(
            SourceRecord,
            (SourceRecord.tenant_id == Document.tenant_id)
            & (SourceRecord.id == Document.source_record_id),
        )
        .where(
            Document.tenant_id == tenant_id,
            SourceRecord.source_system == SOURCE_SYSTEM,
            SourceRecord.external_id == proposal.id,
        )
    )
    intent = review["intent"] if review else {}
    if document is not None and document.order_document_id == intent.get("order_id"):
        from reality.services.down_payments import _result

        receipt = _result(document)
        if proposal.status != "executed" or result["receipt"] == receipt:
            result.update(
                verification="verified"
                if proposal.status == "executed"
                else "recorded_unsettled",
                recorded_receipt=receipt,
                links=[
                    {"kind": "document", "id": document.id},
                    {"kind": "document", "id": document.order_document_id},
                ],
                observation=receipt,
            )
    result["lifecycle"] = proposal.status
    result["recorded_effect"] = result.get("recorded_receipt")
    result["current_observation"] = result["observation"]
    if proposal.status == "proposed":
        result["remaining_work"] = ["Confirm the unchanged reviewed recording."]
        result["safe_next_action"] = "confirm"
    elif result["verification"] == "recorded_unsettled":
        result["remaining_work"] = [
            "Settle the proposal receipt from the exact recorded effect."
        ]
        result["safe_next_action"] = "reconcile"
    elif result["verification"] == "verified":
        result["remaining_work"] = []
        result["safe_next_action"] = "none"
    else:
        result["remaining_work"] = [
            "Reconcile the proposal against the order's documents; do not retry blindly."
        ]
        result["safe_next_action"] = "reconcile"
    return result
