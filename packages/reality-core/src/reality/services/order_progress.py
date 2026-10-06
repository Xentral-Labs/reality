"""Read-only order progress through canonical terms and explicit record links."""

import json

from sqlalchemy import exists, select

from reality.db.core import (
    Commitment,
    Document,
    DocumentLine,
    Item,
    Movement,
    MovementCorrection,
    Shipment,
    ShipmentPackage,
    SourceRecord,
)
from reality.services import core


def overview(session, tenant_id, document_id):
    """BUSINESS PURPOSE:
    Explain an order's current reservations, dispatch and linked billing evidence without booking effects.

    BUSINESS RULE services.order_progress.overview.scope:
    Read canonical terms and explicit same-company record links only; never infer tracking or invoice associations.
    """
    document = core._tenant_record_read(session, Document, tenant_id, document_id)
    if document.type not in {"sales_order", "purchase_order"}:
        return None
    commitments = list(
        session.scalars(
            select(Commitment).where(
                Commitment.tenant_id == tenant_id, Commitment.document_id == document_id
            )
        )
    )
    terms = core.commitment_terms(session, tenant_id, [c.id for c in commitments])
    items = {
        i.id: i
        for i in session.scalars(
            select(Item).where(
                Item.tenant_id == tenant_id,
                Item.id.in_([c.item_id for c in commitments]),
            )
        )
    }
    packages = list(
        session.scalars(
            select(ShipmentPackage)
            .join(
                Movement,
                (Movement.tenant_id == ShipmentPackage.tenant_id)
                & (Movement.shipment_package_id == ShipmentPackage.id),
            )
            .where(
                ShipmentPackage.tenant_id == tenant_id,
                Movement.commitment_id.in_([c.id for c in commitments]),
                Movement.type
                == ("shipment" if document.type == "sales_order" else "receipt"),
                ~exists().where(
                    MovementCorrection.tenant_id == tenant_id,
                    MovementCorrection.original_movement_id == Movement.id,
                ),
            )
            .distinct()
        )
    )
    billed = list(
        session.scalars(
            select(Document)
            .join(
                DocumentLine,
                (DocumentLine.tenant_id == Document.tenant_id)
                & (DocumentLine.document_id == Document.id),
            )
            .where(
                Document.tenant_id == tenant_id,
                Document.type.in_(
                    [
                        "sales_invoice",
                        "supplier_invoice",
                        "down_payment_invoice",
                        "proforma_invoice",
                    ]
                ),
                (Document.order_document_id == document_id)
                | DocumentLine.billed_document_line_id.in_(
                    select(DocumentLine.id).where(
                        DocumentLine.tenant_id == tenant_id,
                        DocumentLine.document_id == document_id,
                    )
                ),
            )
            .distinct()
        )
    )
    notes = []
    for shipment in session.scalars(
        select(Shipment).where(
            Shipment.tenant_id == tenant_id,
            Shipment.id.in_([p.shipment_id for p in packages]),
        )
    ):
        source = session.scalar(
            select(SourceRecord).where(
                SourceRecord.tenant_id == tenant_id,
                SourceRecord.id == shipment.source_record_id,
            )
        )
        raw = json.loads(source.payload) if source else {}
        if not isinstance(raw, dict):
            raw = {}
        if (
            isinstance(raw.get("delivery_note_number"), (str, int))
            and not isinstance(raw.get("delivery_note_number"), bool)
            and raw.get("delivery_note_number")
        ):
            notes.append(
                {"number": str(raw["delivery_note_number"]), "source_id": source.id}
            )
    # reality-rule: services.order_progress.overview.scope
    return {
        "fulfillment_label": "Shipped"
        if document.type == "sales_order"
        else "Received",
        "shipment_title": "Dispatch" if document.type == "sales_order" else "Incoming",
        "lines": [
            {
                "commitment_id": c.id,
                "label": items[c.item_id].name if c.item_id in items else c.item_id,
                "unit": items[c.item_id].unit if c.item_id in items else "",
                "quantity": str(terms[c.id].quantity),
                "reserved": str(terms[c.id].reserved),
                "fulfilled": str(terms[c.id].fulfilled),
                "open": str(terms[c.id].open),
            }
            for c in commitments
        ],
        "packages": [
            {
                "id": p.id,
                "shipment_id": p.shipment_id,
                "carrier": p.carrier,
                "tracking_number": p.tracking_number,
            }
            for p in packages
        ],
        "invoices": [{"id": d.id, "number": d.number, "type": d.type} for d in billed],
        "delivery_notes": notes,
    }
