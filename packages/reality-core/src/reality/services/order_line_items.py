"""Order lines whose stated SKU matches no item, and assigning one (spec 296).

An order from a shop can name an article the company has not set up. Its known
lines are interpreted as usual; the unknown line is kept as a document line
without an item and without a delivery promise. Assigning an item is the missing
interpretation of what the shop stated, so a person decides it through a
reviewed tool, and only then does the line become a promise.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

from sqlalchemy import and_, exists, select
from sqlalchemy.orm import Session

from reality.db.core import (
    BusinessEvent,
    ChangeProposal,
    Commitment,
    Document,
    DocumentLine,
    ImportJob,
    Item,
    SourceRecord,
    SourceStream,
)
from reality.services import core
from reality.services.core import emit_business_event

ORDER_LINE_ITEM_TOOLS = {"order_line_item_assign"}
FIELDS = {"document_line_id", "item_id"}
# Spec 308: also remember the line's customer number for the order's customer.
OPTIONAL_FIELDS = {"remember_for_customer"}


def _order_closed(session: Session, tenant_id: str, document_id: str) -> bool:
    """An order nothing more will ship from: its source cancelled it, or every promise.

    An order of unknown articles alone has no promise to cancel, so the shop's
    cancellation is read from the version its stream stands on.
    """
    order = core._tenant_record(session, Document, tenant_id, document_id)
    if order.source_record_id:
        source = session.get(SourceRecord, (tenant_id, order.source_record_id))
        current = source and session.scalar(
            select(SourceRecord)
            .join(
                SourceStream,
                and_(
                    SourceStream.tenant_id == tenant_id,
                    SourceStream.current_source_record_id == SourceRecord.id,
                ),
            )
            .where(
                SourceStream.source_system == source.source_system,
                SourceStream.source_type == source.source_type,
                SourceStream.external_id == source.external_id,
            )
        )
        if current and json.loads(current.payload or "{}").get("cancelled_at"):
            return True
    statuses = set(
        session.scalars(
            select(Commitment.status)
            .join(
                DocumentLine,
                and_(
                    DocumentLine.tenant_id == tenant_id,
                    DocumentLine.id == Commitment.document_line_id,
                ),
            )
            .where(
                Commitment.tenant_id == tenant_id,
                DocumentLine.document_id == document_id,
            )
        )
    )
    return statuses == {"cancelled"}


def unknown_item_lines(session: Session, tenant_id: str) -> list[dict[str, Any]]:
    """Sales-order item lines with a stated SKU, no item and no promise."""
    promised = exists().where(
        Commitment.tenant_id == tenant_id,
        Commitment.document_line_id == DocumentLine.id,
    )
    rows = session.execute(
        select(DocumentLine, Document)
        .join(
            Document,
            and_(
                Document.tenant_id == tenant_id,
                Document.id == DocumentLine.document_id,
            ),
        )
        .where(
            DocumentLine.tenant_id == tenant_id,
            Document.type == "sales_order",
            DocumentLine.line_type == "item",
            DocumentLine.item_id.is_(None),
            ~promised,
        )
        .order_by(Document.number, DocumentLine.id)
    ).all()
    return [
        {"line": line, "order": order}
        for line, order in rows
        if not _order_closed(session, tenant_id, order.id)
    ]


def _interpretation_context(
    session: Session, tenant_id: str, order: Document
) -> dict[str, Any]:
    """The parties and location the order's source was interpreted with."""
    job = session.scalar(
        select(ImportJob).where(
            ImportJob.tenant_id == tenant_id,
            ImportJob.source_record_id == order.source_record_id,
        )
    )
    if job and job.input:
        return json.loads(job.input)
    return _file_order_context(session, tenant_id, order)


def _file_order_context(
    session: Session, tenant_id: str, order: Document
) -> dict[str, Any]:
    """A file-imported order's own rows name its location (spec 308).

    The order's source keeps the rows it was read from; the company is the
    single company the import promised from. Nothing is assumed beyond that.
    """
    from reality.db.core import SourceRecord
    from reality.services.file_interpreters import (
        _location,
        _single_company,
        _value,
    )

    source = (
        session.get(SourceRecord, (tenant_id, order.source_record_id))
        if order.source_record_id
        else None
    )
    try:
        rows = json.loads(source.payload).get("rows") if source else None
    except ValueError:
        rows = None
    if not rows:
        return {}
    try:
        location = _location(
            session, tenant_id, str(_value(rows[0], "location")).strip()
        )
        company = _single_company(session, tenant_id)
    except core.InvalidOperation:
        return {}
    return {"company_party_id": company.id, "location_id": location.id}


def preview_item_assignment(
    session: Session, tenant_id: str, *, document_line_id: str, item_id: str
) -> dict[str, Any]:
    """What assigning this item would create, recording nothing."""
    line = core._tenant_record(session, DocumentLine, tenant_id, document_line_id)
    order = core._tenant_record(session, Document, tenant_id, line.document_id)
    if order.type != "sales_order":
        raise core.InvalidOperation(code="order_line_item_assign_not_sales_order")
    if line.line_type != "item":
        raise core.InvalidOperation(code="order_line_item_not_item_line")
    promised = session.scalar(
        select(Commitment.id).where(
            Commitment.tenant_id == tenant_id,
            Commitment.document_line_id == line.id,
        )
    )
    if line.item_id is not None or promised:
        raise core.InvalidOperation(code="order_line_item_already_assigned")
    if _order_closed(session, tenant_id, order.id):
        raise core.InvalidOperation(code="order_line_item_order_closed")
    item = core._tenant_record(session, Item, tenant_id, item_id)
    if not item.is_active:
        raise core.InvalidOperation(code="order_line_item_item_inactive")
    sibling = session.scalar(
        select(Commitment)
        .join(
            DocumentLine,
            and_(
                DocumentLine.tenant_id == tenant_id,
                DocumentLine.id == Commitment.document_line_id,
            ),
        )
        .where(
            Commitment.tenant_id == tenant_id,
            DocumentLine.document_id == order.id,
            Commitment.type == "customer_delivery",
        )
        .order_by(Commitment.id)
    )
    context = _interpretation_context(session, tenant_id, order)
    from_party_id = (
        sibling.from_party_id if sibling else context.get("company_party_id")
    )
    location_id = sibling.location_id if sibling else context.get("location_id")
    if not from_party_id or not location_id:
        raise core.InvalidOperation(code="order_line_item_location_unknown")
    due_at = line.requested_at or (sibling.due_at if sibling else None)
    from reality.services.customer_item_numbers import stated_number

    return {
        "customer_item_number": stated_number(line),
        "document_line_id": line.id,
        "order_id": order.id,
        "order_number": order.number,
        "stated_sku": line.sku,
        "item_id": item.id,
        "item_sku": item.sku,
        "quantity": str(line.quantity),
        "unit_price": str(line.unit_price) if line.unit_price is not None else None,
        "currency": order.currency,
        "from_party_id": from_party_id,
        "to_party_id": order.party_id,
        "location_id": location_id,
        "due_at": due_at.isoformat() if due_at else None,
    }


def _hold_like_its_order(session, tenant_id, order_id, commitment) -> None:
    """An assigned line of an order held for credit is held too (spec 298).

    Otherwise assigning the item would release part of the order past a
    decision nobody has taken yet.
    """
    from reality.services.credit_exposure import (
        active_credit_holds,
        credit_exposure,
        place_credit_holds,
    )

    siblings = list(
        session.scalars(
            select(Commitment.id).where(
                Commitment.tenant_id == tenant_id,
                Commitment.document_id == order_id,
                Commitment.id != commitment.id,
            )
        )
    )
    if not active_credit_holds(session, tenant_id, siblings):
        return
    session.flush()
    exposure = credit_exposure(session, tenant_id, commitment.to_party_id)
    place_credit_holds(session, tenant_id, [commitment], exposure, core.ZERO)


def assign_line_item(
    session: Session,
    tenant_id: str,
    *,
    document_line_id: str,
    item_id: str,
    remember_for_customer: bool = False,
    action_id: str | None = None,
    _commit: bool = True,
) -> dict[str, Any]:
    """Give an unknown order line its item and create its delivery promise.

    With `remember_for_customer`, the customer number the line was ordered by
    is stated for the order's customer in the same confirmation (spec 308).
    """
    core._require_business_mutation(session, tenant_id, "assign_order_line_item")
    with session.begin_nested():
        session.scalar(
            select(DocumentLine)
            .where(
                DocumentLine.tenant_id == tenant_id,
                DocumentLine.id == document_line_id,
            )
            .with_for_update()
        )
        preview = preview_item_assignment(
            session, tenant_id, document_line_id=document_line_id, item_id=item_id
        )
        line = core._tenant_record(session, DocumentLine, tenant_id, document_line_id)
        line.item_id = preview["item_id"]
        line.unit = core._tenant_record(
            session, Item, tenant_id, preview["item_id"]
        ).unit
        quantity = core.decimal(preview["quantity"])
        commitment = core.create_commitment(
            session,
            tenant_id,
            "customer_delivery",
            preview["from_party_id"],
            preview["to_party_id"],
            preview["item_id"],
            preview["location_id"],
            quantity,
            preview["due_at"],
            action_id=action_id,
            # A line without a stated price promises nothing billable (spec 314).
            amount=quantity * core.decimal(preview["unit_price"])
            if preview["unit_price"] is not None
            else core.ZERO,
            currency=preview["currency"],
            document_id=preview["order_id"],
            document_line_id=line.id,
            _commit=False,
        )
        _hold_like_its_order(session, tenant_id, preview["order_id"], commitment)
        if remember_for_customer:
            if not preview["customer_item_number"]:
                raise core.InvalidOperation(code="order_line_item_no_customer_number")
            from reality.services.customer_item_numbers import (
                set_customer_item_number,
            )

            set_customer_item_number(
                session,
                tenant_id,
                preview["to_party_id"],
                preview["item_id"],
                preview["customer_item_number"],
                line.description if line.description != line.sku else "",
                action_id=action_id,
                _commit=False,
            )
        emit_business_event(
            session,
            tenant_id,
            "document_line.item_assigned",
            "document_line",
            line.id,
            {
                "item_id": preview["item_id"],
                "stated_sku": preview["stated_sku"],
                "commitment_id": commitment.id,
                "document_id": preview["order_id"],
            },
            action_id=action_id,
        )
    result = {**preview, "commitment_id": commitment.id}
    if _commit:
        session.commit()
    else:
        session.flush()
    return result


# --- The reviewed tool ------------------------------------------------------------


def _json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, default=str, separators=(",", ":"))


def review_item_assignment(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> dict[str, Any]:
    if not FIELDS <= set(arguments) <= FIELDS | OPTIONAL_FIELDS:
        raise core.InvalidOperation(code="order_line_item_assign_fields_invalid")
    intent = {key: str(arguments[key]) for key in sorted(FIELDS)}
    state = json.loads(_json(preview_item_assignment(session, tenant_id, **intent)))
    if arguments.get("remember_for_customer"):
        if not state["customer_item_number"]:
            raise core.InvalidOperation(code="order_line_item_no_customer_number")
        intent["remember_for_customer"] = True
        from reality.services.customer_item_numbers import (
            mapping_values,
            resolve_customer_item,
        )

        # What the number names now is part of the review: a confirmation
        # after it changed is stale, and a remap is shown, never silent.
        current = mapping_values(
            resolve_customer_item(
                session, tenant_id, state["to_party_id"], state["customer_item_number"]
            )
        )
        if current:
            named = session.get(Item, (tenant_id, current["item_id"]))
            current["item_sku"] = named.sku if named else current["item_id"]
        state["customer_mapping"] = current
    remembers = (
        {
            "customer_item_number": state["customer_item_number"],
            "item_id": state["item_id"],
            "replaces": state["customer_mapping"],
        }
        if intent.get("remember_for_customer")
        else None
    )
    return {
        "version": 1,
        "tool": "order_line_item_assign",
        "intent": intent,
        "state": state,
        "effect": {
            "document_line_id": state["document_line_id"],
            "item_id": state["item_id"],
            "quantity": state["quantity"],
            "location_id": state["location_id"],
            "money_moves": False,
            "creates": ["commitment"],
            **({"remembers": remembers} if remembers else {}),
        },
        "token": hashlib.sha256(
            _json([tenant_id, "order_line_item_assign", intent, state]).encode()
        ).hexdigest(),
    }


def assert_no_unresolved_item_assignment(
    session: Session, tenant_id: str, arguments: dict[str, Any], exclude: str | None
) -> None:
    for proposal in session.scalars(
        select(ChangeProposal).where(
            ChangeProposal.tenant_id == tenant_id,
            ChangeProposal.type == "tool:order_line_item_assign",
            ChangeProposal.status == "executing",
        )
    ):
        saved = json.loads(proposal.input)
        if proposal.id != exclude and saved.get("document_line_id") == arguments.get(
            "document_line_id"
        ):
            raise core.InvalidOperation(code="order_line_item_assign_unresolved")


def item_assignment_detail(
    session: Session, tenant_id: str, proposal: ChangeProposal
) -> dict[str, Any]:
    review = json.loads(proposal.input).get("_delivery_review")
    result = {
        "id": proposal.id,
        "tool": "order_line_item_assign",
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
    event = session.scalar(
        select(BusinessEvent).where(
            BusinessEvent.tenant_id == tenant_id,
            BusinessEvent.event_type == "document_line.item_assigned",
            BusinessEvent.action_id == proposal.id,
        )
    )
    intent = review["intent"] if review else {}
    if event and event.subject_id == intent.get("document_line_id"):
        payload = json.loads(event.payload)
        receipt = {
            "document_line_id": event.subject_id,
            "item_id": payload["item_id"],
            "commitment_id": payload["commitment_id"],
        }
        if proposal.status != "executed" or result["receipt"] == receipt:
            result.update(
                verification="verified"
                if proposal.status == "executed"
                else "recorded_unsettled",
                recorded_receipt=receipt,
                links=[
                    {"kind": "document_line", "id": event.subject_id},
                    {"kind": "commitment", "id": payload["commitment_id"]},
                    {"kind": "document", "id": payload["document_id"]},
                ],
                observation=receipt,
            )
    result["lifecycle"] = proposal.status
    result["recorded_effect"] = result.get("recorded_receipt")
    result["current_observation"] = result["observation"]
    if proposal.status == "proposed":
        result["remaining_work"] = ["Confirm the unchanged reviewed action."]
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
            "Reconcile the proposal against the order line; do not retry blindly."
        ]
        result["safe_next_action"] = "reconcile"
    return result
