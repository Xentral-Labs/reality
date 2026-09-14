"""Order-specific evidence and review in the common proposal lifecycle."""

from __future__ import annotations

import hashlib
import json
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from reality.db.core import (
    BusinessEvent,
    ChangeProposal,
    Commitment,
    Document,
    DocumentLine,
    Item,
    Location,
    Party,
    PaymentTerm,
    PriceListEntry,
    SourceRecord,
)
from reality.services.core import (
    InvalidOperation,
    NotFound,
    _preview_manual_order,
    _tenant_record,
)
from reality.services.delivery_reads import delivery_case


def _json(value: Any) -> str:
    def encode(value):
        return (
            format(value.normalize(), "f") if isinstance(value, Decimal) else str(value)
        )

    return json.dumps(value, sort_keys=True, default=encode, separators=(",", ":"))


def review_order(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> dict[str, Any]:
    session.expire_all()
    creation = _preview_manual_order(session, tenant_id, arguments)
    references = {}
    for model, key in (
        (Party, "company_party_id"),
        (Party, "counterparty_id"),
        (Location, "location_id"),
        (Party, "ship_to_party_id"),
    ):
        if arguments.get(key):
            row = _tenant_record(session, model, tenant_id, arguments[key])
            references[key] = {
                "id": row.id,
                "name": row.name,
                "is_active": row.is_active,
            }
    items = {}
    for line in creation["lines"]:
        row = _tenant_record(session, Item, tenant_id, line["item_id"])
        items[row.id] = {
            "id": row.id,
            "name": row.name,
            "sku": row.sku,
            "unit": row.unit,
            "is_active": row.is_active,
            "tracking_type": row.tracking_type,
        }
    commercial = []
    selected = {(PaymentTerm, creation["document"].get("payment_term_id"))}
    selected |= {
        (PriceListEntry, line.get("price_list_entry_id")) for line in creation["lines"]
    }
    selected |= {
        (DocumentLine, line.get("billed_document_line_id"))
        for line in creation["lines"]
    }
    for model, identity in sorted(
        selected, key=lambda pair: (pair[0].__tablename__, str(pair[1]))
    ):
        if identity:
            row = _tenant_record(session, model, tenant_id, identity)
            commercial.append(
                {
                    "kind": model.__tablename__,
                    "values": {
                        column.name: getattr(row, column.name)
                        for column in model.__table__.columns
                    },
                }
            )
    state = json.loads(
        _json(
            {
                "creation": creation,
                "references": references,
                "items": items,
                "commercial": commercial,
            }
        )
    )
    intent = json.loads(_json(arguments))
    token = hashlib.sha256(_json([tenant_id, intent, state]).encode()).hexdigest()
    return {
        "version": 1,
        "tool": "order_create",
        "intent": intent,
        "state": state,
        "effect": {"lines": len(creation["lines"])},
        "token": token,
    }


def assert_no_unresolved_order(
    session: Session, tenant_id: str, arguments: dict[str, Any], exclude: str | None
) -> None:
    clean = {key: value for key, value in arguments.items() if not key.startswith("_")}
    creation = json.loads(
        _json(_preview_manual_order(session, tenant_id, clean, check_existing=False))
    )
    for candidate in session.scalars(
        select(ChangeProposal).where(
            ChangeProposal.tenant_id == tenant_id,
            ChangeProposal.type == "tool:order_create",
            ChangeProposal.status == "executing",
        )
    ):
        if candidate.id == exclude:
            continue
        saved = json.loads(candidate.input)
        review = saved.get("_delivery_review", {})
        if review.get("state", {}).get("creation") == creation and all(
            saved.get(key) == clean.get(key)
            for key in ("company_party_id", "counterparty_id", "location_id")
        ):
            raise InvalidOperation(
                "An identical order execution is unresolved. Check its outcome first."
            )


def _evidence(
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
    recorded = [event for event in events if event.event_type == "order.recorded"]
    if len(recorded) != 1:
        return None
    event = recorded[0]
    payload = json.loads(event.payload)
    # Decimal scale is presentation; event and review retain the same numeric values.
    if _canonical(payload.get("creation")) != _canonical(review["state"]["creation"]):
        return None
    receipt = payload.get("receipt", {})
    document = session.scalar(
        select(Document).where(
            Document.tenant_id == tenant_id, Document.id == receipt.get("document_id")
        )
    )
    source = session.scalar(
        select(SourceRecord).where(
            SourceRecord.tenant_id == tenant_id,
            SourceRecord.id == receipt.get("source_record_id"),
        )
    )
    if (
        not document
        or not source
        or document.source_record_id != source.id
        or event.subject_type != "document"
        or event.subject_id != document.id
        or event.source_record_id != source.id
    ):
        return None
    source_payload = json.loads(source.payload)
    if any(source_payload.get(key) != value for key, value in review["intent"].items()):
        return None
    line_ids, commitment_ids = (
        receipt.get("document_line_ids", []),
        receipt.get("commitment_ids", []),
    )
    count = len(review["state"]["creation"]["lines"])
    if (
        len(set(line_ids)) != count
        or len(set(commitment_ids)) != count
        or len(line_ids) != count
        or len(commitment_ids) != count
    ):
        return None
    docs = [item for item in events if item.event_type == "document.recorded"]
    commitments = [item for item in events if item.event_type == "commitment.created"]
    if (
        len(docs) != 1
        or docs[0].subject_id != document.id
        or json.loads(docs[0].payload).get("document_line_ids") != line_ids
    ):
        return None
    if len(commitments) != count or {item.subject_id for item in commitments} != set(
        commitment_ids
    ):
        return None
    for line_id, cid in zip(line_ids, commitment_ids, strict=True):
        line = session.scalar(
            select(DocumentLine).where(
                DocumentLine.tenant_id == tenant_id, DocumentLine.id == line_id
            )
        )
        commitment = session.scalar(
            select(Commitment).where(
                Commitment.tenant_id == tenant_id, Commitment.id == cid
            )
        )
        if (
            not line
            or not commitment
            or line.document_id != document.id
            or commitment.document_id != document.id
            or commitment.document_line_id != line.id
        ):
            return None
    snapshots = payload.get("commitments", [])
    if len(snapshots) != count:
        return None
    direction = review["state"]["creation"]["direction"]
    intent = review["intent"]
    for index, snapshot in enumerate(snapshots):
        line = review["state"]["creation"]["lines"][index]
        expected = {
            "id": commitment_ids[index],
            "document_id": document.id,
            "document_line_id": line_ids[index],
            "item_id": line["item_id"],
            "location_id": intent["location_id"],
            "from_party_id": intent["company_party_id"]
            if direction == "sales"
            else intent["counterparty_id"],
            "to_party_id": intent["counterparty_id"]
            if direction == "sales"
            else intent["company_party_id"],
            "type": "customer_delivery"
            if direction == "sales"
            else "supplier_delivery",
            "currency": intent.get("currency", "EUR"),
        }
        if any(snapshot.get(key) != value for key, value in expected.items()):
            return None
        if Decimal(str(snapshot.get("quantity", "-1"))) != Decimal(
            line["quantity"]
        ) or Decimal(str(snapshot.get("amount", "-1"))) != Decimal(
            line["gross_amount"]
        ):
            return None
        from reality.services.core import utc_datetime

        due = utc_datetime(
            line.get("promised_at") or intent.get("requested_delivery_at")
        )
        if utc_datetime(snapshot.get("due_at")) != due:
            return None
        created = next(
            item for item in commitments if item.subject_id == snapshot["id"]
        )
        stated = json.loads(created.payload)
        if (
            created.subject_type != "commitment"
            or any(
                stated.get(key) != expected[key]
                for key in ("document_id", "item_id", "type")
            )
            or Decimal(str(stated.get("quantity", "-1"))) != Decimal(line["quantity"])
        ):
            return None
    links = [
        {"kind": "document", "id": document.id},
        {"kind": "source_record", "id": source.id},
        {"kind": "business_event", "id": event.id},
    ]
    links += [{"kind": "commitment", "id": cid} for cid in commitment_ids]
    return receipt, links


def _canonical(value: Any) -> Any:
    """Compare the normalized numeric slots, retaining arbitrary source text verbatim."""
    if isinstance(value, dict):
        return {
            key: format(Decimal(str(item)).normalize(), "f")
            if key in {"quantity", "unit_price", "gross_amount"} and item is not None
            else _canonical(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [_canonical(item) for item in value]
    return value


def order_detail(
    session: Session, tenant_id: str, proposal: ChangeProposal
) -> dict[str, Any]:
    arguments = json.loads(proposal.input)
    review = arguments.get("_delivery_review")
    result = {
        "id": proposal.id,
        "tool": "order_create",
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
        evidence = _evidence(session, tenant_id, proposal, review)
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
            try:
                result["observation"] = {
                    "deliveries": [
                        delivery_case(session, tenant_id, cid)["case"]
                        for cid in evidence[0]["commitment_ids"]
                    ]
                }
            except (NotFound, InvalidOperation) as error:
                result["observation_error"] = str(error)
            except SQLAlchemyError:
                session.rollback()
                result["observation_error"] = (
                    "Current observation unavailable. Refresh this view."
                )
    return result
