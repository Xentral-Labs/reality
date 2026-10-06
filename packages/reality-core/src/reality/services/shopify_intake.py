"""Pure Shopify interpretation; accepted effects use the shared admission executor."""

import json

from sqlalchemy import select
from sqlalchemy.orm import Session

from reality.db.core import Document, ImportJob, Item, Party, SourceRecord
from reality.domain.intake import (
    Effect,
    ObservationState,
    PreparedIntake,
    content_digest,
)
from reality.services import core


def prepare_order(
    session: Session, tenant_id: str, source: SourceRecord, job: ImportJob
) -> PreparedIntake:
    if session.scalar(
        select(Document.id).where(
            Document.tenant_id == tenant_id, Document.source_record_id == source.id
        )
    ):
        raise core.InvalidOperation(code="intake_source_already_accepted")
    from reality.services.shop_order_changes import order_for_source

    existing = order_for_source(session, tenant_id, source)
    if existing is not None:
        return prepare_change(session, tenant_id, source, job, existing)
    from reality.services.intake import _reference

    payload = json.loads(source.payload)
    currency = core._required_source_field(payload.get("currency"), "currency")
    if not 1 <= len(payload.get("line_items", [])) <= 500:
        raise core.InvalidOperation(code="intake_package_too_large")
    mapping = json.loads(job.input)
    company_id = mapping["company_party_id"]
    customer_id = core._surviving_party_id(
        session, tenant_id, mapping["customer_party_id"]
    )
    location_id = mapping["location_id"]
    customer = core._tenant_record_read(session, Party, tenant_id, customer_id)

    references = [
        _reference(session, tenant_id, "party", company_id),
        _reference(session, tenant_id, "party", customer_id),
        _reference(session, tenant_id, "location", location_id),
    ]
    promised_at = next(
        (
            str(row.get("value") or "")
            for row in payload.get("note_attributes", [])
            if row.get("name") == "requested_delivery"
        ),
        "",
    )
    lines = []
    promises = []
    issues = []
    for index, raw in enumerate(payload.get("line_items", [])):
        sku = str(raw.get("sku") or "")
        item = (
            session.scalar(
                select(Item).where(Item.tenant_id == tenant_id, Item.sku == sku)
            )
            if sku
            else None
        )
        received_quantity = raw.get("quantity")
        if received_quantity is None or str(received_quantity).strip() == "":
            raise core.InvalidOperation(
                code="source_line_quantity_missing",
                values={"line": str(raw.get("id") or index + 1)},
            )
        quantity = str(core.positive(received_quantity))
        price = raw.get("price")
        if price is None or str(price).strip() == "":
            price = None
            issues.append(f"line:{index}:price_unstated")
        else:
            price = str(core.decimal(price))
        # Never compute the source's line total from quantity and price.
        stated_amount = raw.get("total_price", raw.get("gross_amount"))
        if stated_amount in (None, ""):
            amount = None
            issues.append(f"line:{index}:amount_unstated")
        else:
            amount = str(core.decimal(stated_amount))
        ships = raw.get("requires_shipping", True) is not False
        if item:
            references.append(_reference(session, tenant_id, "item", item.id))
        else:
            issues.append(f"line:{index}:item_unknown")
        lines.append(
            {
                "source_line_id": str(raw.get("id") or index + 1),
                "item_id": item.id if item else None,
                "sku": sku,
                "description": str(
                    raw.get("name") or raw.get("title") or (item.name if item else sku)
                ),
                "quantity": quantity,
                "unit_price": price,
                "gross_amount": amount,
                "promised_at": promised_at,
                "unit": item.unit if item else "pcs",
                "line_type": "item" if ships else "service",
            }
        )
        if item and ships:
            promises.append(
                Effect(
                    operation="commitment",
                    arguments={
                        "commitment_type": "customer_delivery",
                        "from_party_id": company_id,
                        "to_party_id": customer_id,
                        "item_id": item.id,
                        "location_id": location_id,
                        "quantity": quantity,
                        "due_at": promised_at or None,
                        "amount": amount,
                        "currency": currency,
                        "line_index": index,
                    },
                )
            )
    document = {
        "document_type": "sales_order",
        "number": str(payload.get("name") or source.external_id),
        "party_id": customer_id,
        "lines": lines,
        "gross_amount": str(core.decimal(payload["total_price"])),
        "currency": currency,
        "document_date": core._source_document_day(
            session, tenant_id, payload.get("created_at")
        ),
        "ordered_at": payload.get("created_at"),
        "requested_delivery_at": promised_at or None,
        "sales_channel": "shopify",
        "source_record_id": source.id,
    }
    core._preview_manual_document_input(
        session,
        tenant_id,
        **document,
        _carry_unstated_price=True,
        _carry_unstated_amount=True,
    )
    from reality.domain.intake_completeness import order_issues

    issues.extend(order_issues(document, lines))
    document["_source_line_payloads"] = payload["line_items"]
    observations = []
    holds = []
    if customer.credit_limit > 0 and promises:
        from reality.services.credit_exposure import credit_exposure

        as_of = core.now().isoformat()
        arguments = {"party_id": customer.id, "as_of": as_of}
        current = credit_exposure(
            session, tenant_id, customer.id, as_of=core.utc_datetime(as_of)
        )
        observations.append(
            ObservationState(
                kind="credit_exposure",
                arguments=arguments,
                digest=content_digest(current),
            )
        )
        amount_unknown = any(
            line["gross_amount"] is None or line["unit_price"] is None for line in lines
        )
        stated_value = sum(
            (
                core.decimal(line["gross_amount"])
                for line in lines
                if line["gross_amount"] is not None
            ),
            core.ZERO,
        )
        over_limit = current["exposure"] + stated_value > customer.credit_limit
        if (
            amount_unknown
            or current["open_orders"]["unpriced"]
            or over_limit
            or document["currency"] != customer.default_currency
        ):
            issues.append("credit_check_required")
            holds.append(
                Effect(
                    operation="credit_hold",
                    arguments={
                        "commitment_indices": list(range(len(promises))),
                        "note": "Reviewed order requires a credit decision: exposure is incomplete, above the limit or in another currency.",
                        "facts": {
                            "reviewed_exposure": current,
                            "source_stated_order_amount": document["gross_amount"],
                            "order_currency": document["currency"],
                        },
                    },
                )
            )
    return PreparedIntake(
        tenant_id=tenant_id,
        source_record_id=source.id,
        source_hash=source.payload_hash,
        source_version=source.version,
        import_job_id=job.id,
        profile="shopify.order",
        mapping=mapping,
        references=tuple(
            {(row.record_type, row.record_id): row for row in references}.values()
        ),
        effects=(Effect(operation="document", arguments=document), *promises, *holds),
        observations=tuple(observations),
        issues=tuple(issues),
        row_count=len(lines),
    )


def order_state(session: Session, tenant_id: str, order_id: str) -> dict:
    """Snapshot membership as well as state, including newly recorded fulfilment."""
    from reality.db.core import (
        Commitment,
        CommitmentHold,
        CommitmentRevision,
        DocumentLine,
        Movement,
        MovementCorrection,
        Reservation,
        ReturnAnnouncement,
    )
    from reality.services.intake import _state

    order = core._tenant_record_read(session, Document, tenant_id, order_id)
    commitments = list(
        session.scalars(
            select(Commitment)
            .where(
                Commitment.tenant_id == tenant_id, Commitment.document_id == order_id
            )
            .order_by(Commitment.id)
            .execution_options(populate_existing=True)
        )
    )
    ids = [row.id for row in commitments]
    result = {
        "document": _state(order),
        "commitment": [(row.id, _state(row)) for row in commitments],
    }
    for model, predicate in (
        (DocumentLine, DocumentLine.document_id == order_id),
        (CommitmentHold, CommitmentHold.commitment_id.in_(ids)),
        (CommitmentRevision, CommitmentRevision.commitment_id.in_(ids)),
        (Reservation, Reservation.commitment_id.in_(ids)),
        (Movement, Movement.commitment_id.in_(ids)),
        (ReturnAnnouncement, ReturnAnnouncement.commitment_id.in_(ids)),
    ):
        rows = list(
            session.scalars(
                select(model)
                .where(model.tenant_id == tenant_id, predicate)
                .order_by(model.id)
                .execution_options(populate_existing=True)
            )
        )
        result[model.__tablename__] = [(row.id, _state(row)) for row in rows]
    movement_ids = [row[0] for row in result["movement"]]
    result["movement_correction"] = [
        (row.id, _state(row))
        for row in session.scalars(
            select(MovementCorrection)
            .where(
                MovementCorrection.tenant_id == tenant_id,
                MovementCorrection.original_movement_id.in_(movement_ids),
            )
            .order_by(MovementCorrection.id)
        )
    ]
    from reality.services.shop_refunds import refunds_for_order

    refunds = sorted(
        refunds_for_order(session, tenant_id, order), key=lambda row: row.id
    )
    result["refund_documents"] = [(row.id, _state(row)) for row in refunds]
    result["refund_lines"] = [
        (row.id, _state(row))
        for row in session.scalars(
            select(DocumentLine)
            .where(
                DocumentLine.tenant_id == tenant_id,
                DocumentLine.document_id.in_([row.id for row in refunds]),
            )
            .order_by(DocumentLine.id)
        )
    ]
    return result


def prepare_change(
    session: Session,
    tenant_id: str,
    source: SourceRecord,
    job: ImportJob,
    order: Document,
) -> PreparedIntake:
    from reality.services.intake import _reference
    from reality.services.shop_order_changes import (
        _previous_payload,
        classify_order_version,
    )

    payload = json.loads(source.payload)
    plan = classify_order_version(
        session,
        tenant_id,
        order,
        payload,
        _previous_payload(session, tenant_id, source),
    )
    if plan.held:
        raise core.ShopifyUpdateNeedsReview(
            codes=[code for code, _ in plan.held],
            reason_code=plan.reason_code,
            summary=plan.summary,
        )
    effects = [
        Effect(
            operation="commitment_revision",
            arguments={
                "commitment_id": commitment.id,
                "quantity": str(quantity),
                "note": "Quantity lowered in Shopify",
                "source_record_id": source.id,
            },
        )
        for commitment, quantity in plan.revisions
    ]
    effects.extend(
        Effect(
            operation="commitment_cancellation",
            arguments={
                "commitment_id": commitment.id,
                "reason": plan.cancel_reason,
                "source_record_id": source.id,
            },
        )
        for commitment in plan.cancellations
    )
    return PreparedIntake(
        tenant_id=tenant_id,
        source_record_id=source.id,
        source_hash=source.payload_hash,
        source_version=source.version,
        import_job_id=job.id,
        profile="shopify.order_change",
        mapping=json.loads(job.input),
        references=(_reference(session, tenant_id, "document", order.id),),
        observations=(
            ObservationState(
                kind="shop_order_state",
                arguments={"order_id": order.id},
                digest=content_digest(order_state(session, tenant_id, order.id)),
            ),
        ),
        effects=tuple(effects),
        row_count=max(1, len(payload.get("line_items", []))),
    )
