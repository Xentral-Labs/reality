"""Spec 296: a Shopify refund is its own source and becomes evidence on the order."""

import json
from decimal import Decimal

from sqlalchemy import func, select

from reality.db.core import (
    Document,
    DocumentLine,
    ImportJob,
    InterpretationOutcome,
    LedgerEntry,
    ReturnAnnouncement,
    SourceRecord,
)
from reality.services import core

ORDER, LINE = 7101, 71


def _refund(refund_id=901, *, quantity=2, restock="return", line=LINE, amount="20.00"):
    return {
        "id": refund_id,
        "order_id": ORDER,
        "created_at": "2026-09-05T10:00:00Z",
        "note": "Customer changed their mind",
        "refund_line_items": [
            {
                "id": refund_id * 10,
                "line_item_id": line,
                "quantity": quantity,
                "restock_type": restock,
                "subtotal": amount,
            }
        ],
        "transactions": [
            {
                "id": refund_id * 100,
                "kind": "refund",
                "status": "success",
                "amount": amount,
                "currency": "EUR",
            }
        ],
    }


def _order(*, updated_at="2026-09-01T10:00:00Z", refunds=(), **changes):
    return {
        "id": ORDER,
        "name": f"#{ORDER}",
        "currency": "EUR",
        "total_price": "50.00",
        "created_at": "2026-09-01T10:00:00Z",
        "updated_at": updated_at,
        "line_items": [
            {"id": LINE, "sku": "BIKE-LIGHT", "quantity": 5, "price": "10.00"}
        ],
        "refunds": list(refunds),
        **changes,
    }


def _enqueue(session, business, payload):
    return core.enqueue_shopify_order(
        session,
        business.tenant.id,
        payload,
        business.company.id,
        business.customer.id,
        business.location.id,
    )


def _process_all(session, business):
    return core.process_pending_import_jobs(session, business.tenant.id)


def _interpreted_order(session, business, *, shipped="0"):
    core.record_movement(
        session,
        business.tenant.id,
        "opening_stock",
        business.item.id,
        "10",
        to_location_id=business.location.id,
    )
    _, job = _enqueue(session, business, _order())
    commitment = core.process_import_job(session, business.tenant.id, job.id)[3][0]
    if shipped != "0":
        core.reserve(session, business.tenant.id, commitment.id)
        core.record_movement(
            session,
            business.tenant.id,
            "shipment",
            business.item.id,
            shipped,
            from_location_id=business.location.id,
            commitment_id=commitment.id,
        )
    return commitment


def _refund_sources(session, business):
    return list(
        session.scalars(
            select(SourceRecord).where(
                SourceRecord.tenant_id == business.tenant.id,
                SourceRecord.source_system == "shopify",
                SourceRecord.source_type == "refund",
            )
        )
    )


def _refund_documents(session, business):
    return list(
        session.scalars(
            select(Document).where(
                Document.tenant_id == business.tenant.id,
                Document.type == "sales_refund",
            )
        )
    )


def _announcements(session, commitment):
    return list(
        session.scalars(
            select(ReturnAnnouncement).where(
                ReturnAnnouncement.commitment_id == commitment.id
            )
        )
    )


def _outcome(session, source):
    return session.scalars(
        select(InterpretationOutcome)
        .where(InterpretationOutcome.source_record_id == source.id)
        .order_by(InterpretationOutcome.attempt.desc())
    ).first()


def test_refunds_are_split_from_an_order_version_once_each(session, business):
    _interpreted_order(session, business)

    _enqueue(
        session,
        business,
        _order(updated_at="2026-09-05T10:00:00Z", refunds=[_refund()]),
    )
    _enqueue(
        session,
        business,
        _order(
            updated_at="2026-09-06T10:00:00Z",
            refunds=[_refund(), _refund(902, quantity=1, amount="10.00")],
        ),
    )

    sources = _refund_sources(session, business)
    assert sorted(source.external_id for source in sources) == ["901", "902"]
    assert json.loads(sources[0].payload)["order_id"] == ORDER


def test_a_refund_is_recorded_as_evidence_on_the_order_without_a_posting(
    session, business
):
    commitment = _interpreted_order(session, business)
    _enqueue(
        session,
        business,
        _order(updated_at="2026-09-05T10:00:00Z", refunds=[_refund()]),
    )

    _process_all(session, business)

    (refund,) = _refund_documents(session, business)
    assert (refund.gross_amount, refund.currency) == (Decimal("20.00"), "EUR")
    assert refund.party_id == business.customer.id
    (line,) = session.scalars(
        select(DocumentLine).where(DocumentLine.document_id == refund.id)
    ).all()
    assert (line.quantity, line.gross_amount) == (Decimal(2), Decimal("20.00"))
    assert line.source_line_id == str(LINE)
    assert line.item_id == commitment.item_id
    assert line.billed_document_line_id is None
    assert (
        session.scalar(
            select(func.count())
            .select_from(LedgerEntry)
            .where(LedgerEntry.document_id == refund.id)
        )
        == 0
    )
    assert _outcome(session, _refund_sources(session, business)[0]).classification == (
        "interpreted"
    )


def test_a_refund_of_shipped_goods_to_be_returned_announces_the_return(
    session, business
):
    commitment = _interpreted_order(session, business, shipped="5")
    _enqueue(
        session,
        business,
        _order(updated_at="2026-09-05T10:00:00Z", refunds=[_refund()]),
    )

    _process_all(session, business)

    (announcement,) = _announcements(session, commitment)
    assert announcement.quantity == 2
    assert announcement.reference == "Refund 901"
    assert announcement.source_record_id == _refund_sources(session, business)[0].id


def test_a_refund_without_restock_or_before_shipment_announces_nothing(
    session, business
):
    commitment = _interpreted_order(session, business, shipped="5")
    _enqueue(
        session,
        business,
        _order(
            updated_at="2026-09-05T10:00:00Z", refunds=[_refund(restock="no_restock")]
        ),
    )
    _process_all(session, business)
    assert _refund_documents(session, business)
    assert _announcements(session, commitment) == []


def test_a_refund_to_be_returned_of_unshipped_goods_announces_nothing(
    session, business
):
    commitment = _interpreted_order(session, business)
    _enqueue(
        session,
        business,
        _order(updated_at="2026-09-05T10:00:00Z", refunds=[_refund()]),
    )
    _process_all(session, business)
    assert _refund_documents(session, business)
    assert _announcements(session, commitment) == []


def test_a_refund_before_its_order_waits_and_is_recorded_on_retry(session, business):
    refund, job = core.enqueue_source(
        session,
        business.tenant.id,
        "shopify",
        "refund",
        "901",
        _refund(),
        context={},
    )
    try:
        core.process_import_job(session, business.tenant.id, job.id)
    except core.InvalidOperation as error:
        assert error.code == "shop_refund_order_missing"
    else:
        raise AssertionError("a refund before its order must not be interpreted")
    assert session.get(ImportJob, (business.tenant.id, job.id)).status == "failed"
    assert _refund_documents(session, business) == []

    _interpreted_order(session, business)
    core.retry_import_job(session, business.tenant.id, job.id)
    core.process_import_job(session, business.tenant.id, job.id)

    assert len(_refund_documents(session, business)) == 1
    assert _outcome(session, refund).classification == "interpreted"


def test_a_refund_naming_an_unknown_line_waits_with_its_code(session, business):
    _interpreted_order(session, business)
    _enqueue(
        session,
        business,
        _order(updated_at="2026-09-05T10:00:00Z", refunds=[_refund(line=99)]),
    )

    _process_all(session, business)

    outcome = _outcome(session, _refund_sources(session, business)[0])
    assert outcome.classification == "needs_review"
    assert outcome.reason_code == "shop_refund_line_unknown"
    assert _refund_documents(session, business) == []


def test_a_refund_is_recorded_even_when_its_order_version_is_held(session, business):
    _interpreted_order(session, business)
    order_version, _ = _enqueue(
        session,
        business,
        _order(
            updated_at="2026-09-05T10:00:00Z",
            refunds=[_refund()],
            shipping_address={"city": "Ulm"},
        ),
    )

    _process_all(session, business)

    assert _outcome(session, order_version).reason_code == "address_changed"
    assert len(_refund_documents(session, business)) == 1


def test_replaying_a_refund_records_it_once(session, business):
    commitment = _interpreted_order(session, business, shipped="5")
    _enqueue(
        session,
        business,
        _order(updated_at="2026-09-05T10:00:00Z", refunds=[_refund()]),
    )
    _process_all(session, business)
    job = session.scalars(
        select(ImportJob).where(
            ImportJob.source_record_id == _refund_sources(session, business)[0].id
        )
    ).one()

    core.process_import_job(session, business.tenant.id, job.id)

    assert len(_refund_documents(session, business)) == 1
    assert len(_announcements(session, commitment)) == 1


def test_the_order_inspector_lists_its_refunds(session, business):
    from reality.web.api import document_inspector

    commitment = _interpreted_order(session, business)
    order_id = commitment.document_id

    def refunds_section():
        return next(
            (
                section["rows"]
                for section in document_inspector(
                    session, business.tenant.id, order_id
                )["sections"]
                if section["title"] == "Refunds"
            ),
            None,
        )

    # Positive control for the absence: no refund, no section.
    assert refunds_section() is None
    _enqueue(
        session,
        business,
        _order(updated_at="2026-09-05T10:00:00Z", refunds=[_refund()]),
    )
    _process_all(session, business)

    (row,) = refunds_section()
    (refund,) = _refund_documents(session, business)
    assert row["label"] == "Refund 901"
    assert row["link"] == {"kind": "document", "id": refund.id}


def test_a_changed_payload_of_the_same_refund_is_not_a_second_refund(session, business):
    commitment = _interpreted_order(session, business, shipped="5")
    pending = {
        **_refund(),
        "transactions": [{**_refund()["transactions"][0], "status": "pending"}],
    }
    _enqueue(
        session, business, _order(updated_at="2026-09-05T10:00:00Z", refunds=[pending])
    )
    _process_all(session, business)
    assert _refund_documents(session, business) == []
    (pending_source,) = _refund_sources(session, business)
    assert _outcome(session, pending_source).reason_code == "shop_refund_pending"

    _enqueue(
        session,
        business,
        _order(updated_at="2026-09-06T10:00:00Z", refunds=[_refund()]),
    )
    _enqueue(
        session,
        business,
        _order(
            updated_at="2026-09-07T10:00:00Z",
            refunds=[{**_refund(), "note": "Edited note"}],
        ),
    )
    _process_all(session, business)

    (refund,) = _refund_documents(session, business)
    assert refund.gross_amount == Decimal("20.00")
    assert len(_announcements(session, commitment)) == 1


def test_a_cancelling_refund_lowers_the_promise_even_when_its_order_version_waits(
    session, business
):
    commitment = _interpreted_order(session, business)
    cancelling = _refund(quantity=2, restock="cancel")

    order_version, _ = _enqueue(
        session,
        business,
        _order(
            updated_at="2026-09-05T10:00:00Z",
            refunds=[cancelling],
            shipping_address={"city": "Ulm"},
            line_items=[
                {
                    "id": LINE,
                    "sku": "BIKE-LIGHT",
                    "quantity": 5,
                    "current_quantity": 3,
                    "price": "10.00",
                }
            ],
        ),
    )
    _process_all(session, business)

    assert _outcome(session, order_version).reason_code == "address_changed"
    assert core.commitment_quantity(session, business.tenant.id, commitment.id) == 3


def test_a_cancelling_refund_after_its_applied_order_version_lowers_nothing_more(
    session, business
):
    commitment = _interpreted_order(session, business)
    _enqueue(
        session,
        business,
        _order(
            updated_at="2026-09-05T10:00:00Z",
            refunds=[_refund(quantity=2, restock="cancel")],
            line_items=[
                {
                    "id": LINE,
                    "sku": "BIKE-LIGHT",
                    "quantity": 5,
                    "current_quantity": 3,
                    "price": "10.00",
                }
            ],
        ),
    )

    _process_all(session, business)

    assert core.commitment_quantity(session, business.tenant.id, commitment.id) == 3
