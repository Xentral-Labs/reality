"""Read-only, bounded business flow and party workspace for the local spectator."""

import json
from datetime import datetime

from sqlalchemy import cast, func, select
from sqlalchemy.dialects.postgresql import JSONB

from reality.db.core import (
    BusinessEvent,
    Commitment,
    Document,
    LedgerEntry,
    Movement,
    Reservation,
    Shipment,
    ShipmentEvent,
    ShipmentPackage,
    SourceRecord,
)
from reality.services import business_performance, live_company_purchasing

EVENT_LABELS = {
    "order.recorded": "Order recorded",
    "invoice.recorded": "Invoice recorded",
    "credit.recorded": "Credit recorded",
    "commitment.fulfilled": "Goods booked against an order",
    "commitment.cancelled": "Order obligation cancelled",
    "commitment.revised": "Order obligation revised",
    "reservation.created": "Stock reserved",
    "shipment.notice_recorded": "Shipment recorded",
    "shipment.event_recorded": "Carrier event recorded",
    "movement.recorded": "Stock movement recorded",
    "payment.captured": "Payment capture recorded",
    "payment.authorized": "Payment authorization recorded",
    "payment.returned": "Payment return recorded",
    "ledger.posted": "Financial posting recorded",
}


def enrich(session, tenant, run_id, config, view, *, order_filter=""):
    system = f"company_simulator:{run_id}"
    start = datetime.fromisoformat(config["started_at"])
    docs = {
        d.id: d
        for d in session.scalars(select(Document).where(Document.tenant_id == tenant))
    }
    commitments = {
        c.id: c.document_id
        for c in session.scalars(
            select(Commitment).where(Commitment.tenant_id == tenant)
        )
    }
    recent_docs = list(
        session.execute(
            select(Document, SourceRecord.received_at)
            .join(
                SourceRecord,
                (SourceRecord.tenant_id == Document.tenant_id)
                & (SourceRecord.id == Document.source_record_id),
            )
            .where(Document.tenant_id == tenant, SourceRecord.received_at >= start)
            .order_by(SourceRecord.received_at.desc(), Document.id)
            .limit(100)
        )
    )
    documents = [
        {
            "id": d.id,
            "number": d.number,
            "party_id": d.party_id,
            "type": d.type,
            "amount": str(d.gross_amount),
            "currency": d.currency,
            "source_record_id": d.source_record_id,
            "recorded_at": at.isoformat(),
        }
        for d, at in recent_docs
    ]
    events = list(
        session.scalars(
            select(BusinessEvent)
            .where(
                BusinessEvent.tenant_id == tenant,
                BusinessEvent.recorded_at >= start,
                BusinessEvent.event_type.in_(EVENT_LABELS),
            )
            .order_by(BusinessEvent.sequence.desc())
            .limit(160)
        )
    )
    movements = {
        m.id: m
        for m in session.scalars(
            select(Movement).where(
                Movement.tenant_id == tenant,
                Movement.id.in_(
                    [e.subject_id for e in events if e.subject_type == "movement"]
                ),
            )
        )
    }
    reservations = {
        r.id: r.commitment_id
        for r in session.scalars(
            select(Reservation).where(
                Reservation.tenant_id == tenant,
                Reservation.id.in_(
                    [e.subject_id for e in events if e.subject_type == "reservation"]
                ),
            )
        )
    }
    posting_documents = {}
    for group_id, doc_id in session.execute(
        select(LedgerEntry.posting_group_id, LedgerEntry.document_id).where(
            LedgerEntry.tenant_id == tenant,
            LedgerEntry.posting_group_id.in_(
                [e.subject_id for e in events if e.subject_type == "posting_group"]
            ),
        )
    ):
        if doc_id:
            posting_documents.setdefault(group_id, set()).add(doc_id)
    shipments = {
        s.id: s.counterparty_id
        for s in session.scalars(select(Shipment).where(Shipment.tenant_id == tenant))
    }
    shipment_events = {
        e.id: e
        for e in session.scalars(
            select(ShipmentEvent).where(
                ShipmentEvent.tenant_id == tenant,
                ShipmentEvent.id.in_(
                    [e.subject_id for e in events if e.subject_type == "shipment_event"]
                ),
            )
        )
    }
    shipment_docs = {}
    for package_shipment, commitment_id in session.execute(
        select(ShipmentPackage.shipment_id, Movement.commitment_id)
        .join(
            Movement,
            (Movement.tenant_id == ShipmentPackage.tenant_id)
            & (Movement.shipment_package_id == ShipmentPackage.id),
        )
        .where(ShipmentPackage.tenant_id == tenant)
    ):
        if commitments.get(commitment_id):
            shipment_docs.setdefault(package_shipment, set()).add(
                commitments[commitment_id]
            )
    flow = [
        {
            **m,
            "id": m["source_record_id"],
            "category": m["direction"],
            "title": m["subject"],
        }
        for m in view["messages"]
    ]
    for event in events:
        payload = json.loads(event.payload)
        document_id = (
            event.subject_id
            if event.subject_type == "document"
            else payload.get("document_id")
        )
        shipment_id = None
        if event.subject_type == "commitment":
            document_id = commitments.get(event.subject_id)
        elif event.subject_type == "reservation":
            document_id = commitments.get(reservations.get(event.subject_id))
        elif (
            event.subject_type == "posting_group"
            and len(posting_documents.get(event.subject_id, [])) == 1
        ):
            document_id = next(iter(posting_documents[event.subject_id]))
        elif event.subject_type == "movement" and event.subject_id in movements:
            document_id = commitments.get(movements[event.subject_id].commitment_id)
        elif event.subject_type == "shipment":
            shipment_id = event.subject_id
        elif event.subject_id in shipment_events:
            shipment_id = shipment_events[event.subject_id].shipment_id
        if shipment_id and len(shipment_docs.get(shipment_id, [])) == 1:
            document_id = next(iter(shipment_docs[shipment_id]))
        doc = docs.get(document_id)
        title = EVENT_LABELS[event.event_type]
        if (
            event.event_type == "shipment.event_recorded"
            and event.subject_id in shipment_events
        ):
            title = "Carrier: " + shipment_events[event.subject_id].event_type.replace(
                "_", " "
            )
        flow.append(
            {
                "id": event.id,
                "category": "activity",
                "title": title,
                "recorded_at": event.recorded_at.isoformat(),
                "party_id": doc.party_id if doc else shipments.get(shipment_id),
                "document_id": doc.id if doc else None,
                "document_number": doc.number if doc else None,
                "source_record_id": event.source_record_id,
                "event_type": event.event_type,
                "subject_type": event.subject_type,
                "subject_id": event.subject_id,
                "payload": payload,
            }
        )
    flow.sort(key=lambda r: (r["recorded_at"], r["id"]), reverse=True)
    summaries = {
        p["id"]: {"incoming": 0, "outgoing": 0, "orders": 0, "documents": 0}
        for rows in config["references"].values()
        for p in rows
    }
    party_expression = cast(SourceRecord.payload, JSONB)["party_id"].astext
    for direction in ["incoming", "outgoing"]:
        for party_id, count in session.execute(
            select(party_expression, func.count())
            .where(
                SourceRecord.tenant_id == tenant,
                SourceRecord.source_system == system,
                SourceRecord.source_type == direction,
            )
            .group_by(party_expression)
        ):
            if party_id in summaries:
                summaries[party_id][direction] = count
    for party_id, kind, count in session.execute(
        select(Document.party_id, Document.type, func.count())
        .join(
            SourceRecord,
            (SourceRecord.tenant_id == Document.tenant_id)
            & (SourceRecord.id == Document.source_record_id),
        )
        .where(Document.tenant_id == tenant, SourceRecord.received_at >= start)
        .group_by(Document.party_id, Document.type)
    ):
        if party_id in summaries:
            summaries[party_id]["documents"] += count
            if kind in {"sales_order", "purchase_order"}:
                summaries[party_id]["orders"] += count
    receipts = dict(
        session.execute(
            select(
                cast(SourceRecord.payload, JSONB)["document_id"].astext,
                SourceRecord.received_at,
            ).where(
                SourceRecord.tenant_id == tenant,
                SourceRecord.source_system == system,
                SourceRecord.source_type == "incoming",
                cast(SourceRecord.payload, JSONB)["kind"].astext == "order",
            )
        ).all()
    )
    return {
        **view,
        "performance": business_performance.overview(
            session,
            tenant,
            document_ids=list(receipts),
            received_at_by_document=receipts,
            order_filter=order_filter,
        ),
        "purchasing": live_company_purchasing.catalogue(session, tenant, config),
        "documents": documents,
        "flow": flow[:200],
        "party_summaries": summaries,
        "view_limit": "Latest 200 flow entries, 100 documents, 100 order lines and 300 messages per direction. Party counts cover the full run; lists are bounded.",
    }
