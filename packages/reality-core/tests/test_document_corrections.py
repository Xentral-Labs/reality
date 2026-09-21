import json

import pytest
from conftest import record_by_id
from sqlalchemy import select

from reality.db.core import BusinessEvent, DocumentLine, SourceRecord
from reality.services.core import (
    InvalidOperation,
    NotFound,
    correct_manual_document,
    correct_manual_document_lines,
    create_commitment,
    create_document,
    create_item,
    create_manual_document_with_lines,
    create_payment_term,
    create_tenant,
    enqueue_source,
    manual_document_line_snapshot,
    post_sales_invoice,
    record_corrected_document_source,
)


def test_manual_document_correction_records_typed_fields_and_event(session, business):
    term = create_payment_term(session, business.tenant.id, "NET14", "Net 14", 14)
    document = create_document(
        session,
        business.tenant.id,
        "sales_order",
        "SO-OLD",
        business.customer.id,
        "100.00",
    )

    corrected = correct_manual_document(
        session,
        business.tenant.id,
        document.id,
        document_type="sales_order",
        number="SO-NEW",
        party_id=business.customer.id,
        amount="125.00",
        currency="eur",
        document_date="2026-08-29",
        ordered_at="2026-08-29T10:00",
        requested_delivery_at="2026-09-02T08:00",
        customer_reference="PO-42",
        sales_channel="direct",
        payment_term_code=term.code,
        ship_to_party_id=business.customer.id,
    )

    assert corrected.number == "SO-NEW"
    assert corrected.currency == "EUR"
    assert corrected.payment_term_id == term.id
    assert corrected.customer_reference == "PO-42"
    event = session.scalar(
        select(BusinessEvent)
        .where(BusinessEvent.subject_id == document.id)
        .order_by(BusinessEvent.sequence.desc())
    )
    assert event.event_type == "document.corrected"
    assert "customer_reference" in json.loads(event.payload)["changed_fields"]


def test_manual_document_economic_fields_lock_after_reality_is_derived(
    session, business
):
    document = create_document(
        session,
        business.tenant.id,
        "sales_order",
        "SO-LOCKED",
        business.customer.id,
        "100.00",
    )
    create_commitment(
        session,
        business.tenant.id,
        "customer_delivery",
        business.company.id,
        business.customer.id,
        business.item.id,
        business.location.id,
        1,
        "2026-09-03",
        document_id=document.id,
    )

    with pytest.raises(InvalidOperation, match="after Reality records"):
        correct_manual_document(
            session,
            business.tenant.id,
            document.id,
            document_type=document.type,
            number=document.number,
            party_id=document.party_id,
            amount="101",
            currency=document.currency,
        )


def test_external_document_correction_appends_immutable_source_version(
    session, business
):
    first, _ = enqueue_source(
        session,
        business.tenant.id,
        "shopify",
        "order",
        "1001",
        {"id": 1001, "total": "100.00"},
        context={"channel": "web"},
    )
    document = create_document(
        session,
        business.tenant.id,
        "sales_order",
        "1001",
        business.customer.id,
        "100.00",
        source_record_id=first.id,
    )

    second, job = record_corrected_document_source(
        session,
        business.tenant.id,
        document.id,
        {"id": 1001, "total": "125.00"},
    )

    assert second.id != first.id
    assert second.version == first.version + 1
    assert second.supersedes_source_record_id == first.id
    assert (
        json.loads(record_by_id(session, SourceRecord, first.id).payload)["total"]
        == "100.00"
    )
    assert json.loads(job.input)["channel"] == "web"
    with pytest.raises(InvalidOperation, match="cannot be overwritten"):
        correct_manual_document(
            session,
            business.tenant.id,
            document.id,
            document_type=document.type,
            number=document.number,
            party_id=document.party_id,
            amount=document.gross_amount,
        )


def manual_document(session, business):
    return create_manual_document_with_lines(
        session,
        business.tenant.id,
        "sales_order",
        "SO-LINES",
        business.customer.id,
        [
            {
                "item_id": business.item.id,
                "source_line_id": "1",
                "quantity": "2",
                "unit_price": "10",
                "gross_amount": "20",
            },
            {
                "item_id": business.item.id,
                "source_line_id": "2",
                "quantity": "1",
                "unit_price": "5",
                "gross_amount": "5",
            },
        ],
        "25",
    )


def test_manual_line_snapshot_correction_is_atomic_and_audited(session, business):
    document, original = manual_document(session, business)
    snapshot = manual_document_line_snapshot(session, business.tenant.id, document.id)
    retained_id = snapshot["lines"][0]["id"]
    removed_id = next(line.id for line in original if line.id != retained_id)

    result = correct_manual_document_lines(
        session,
        business.tenant.id,
        document.id,
        expected_revision=snapshot["revision"],
        lines=[
            {**snapshot["lines"][0], "description": "Corrected", "quantity": "3"},
            {
                "item_id": business.item.id,
                "source_line_id": "3",
                "quantity": "1",
                "unit_price": "7",
                "gross_amount": "7",
            },
        ],
        actor_context={"actor_type": "human", "actor_id": "usr_test"},
    )

    assert result["changed"] is True
    assert (result["added"], result["updated"], result["removed"]) == (1, 1, 1)
    assert retained_id in {line["id"] for line in result["lines"]}
    assert record_by_id(session, DocumentLine, removed_id) is None
    event = session.scalar(
        select(BusinessEvent)
        .where(BusinessEvent.subject_id == document.id)
        .order_by(BusinessEvent.sequence.desc())
    )
    payload = json.loads(event.payload)
    assert payload["changed_fields"] == ["lines"]
    assert payload["actor_context"]["actor_id"] == "usr_test"
    assert {entry["id"] for entry in payload["line_changes"]["removed"]} == {removed_id}


def test_manual_line_correction_rejects_stale_and_retries_current_state_as_noop(
    session, business
):
    document, _ = manual_document(session, business)
    snapshot = manual_document_line_snapshot(session, business.tenant.id, document.id)
    intended = [{**line, "description": "Current"} for line in snapshot["lines"]]
    first = correct_manual_document_lines(
        session,
        business.tenant.id,
        document.id,
        expected_revision=snapshot["revision"],
        lines=intended,
    )
    retry = correct_manual_document_lines(
        session,
        business.tenant.id,
        document.id,
        expected_revision=snapshot["revision"],
        lines=first["lines"],
    )
    assert retry["changed"] is False
    with pytest.raises(InvalidOperation, match="stale"):
        correct_manual_document_lines(
            session,
            business.tenant.id,
            document.id,
            expected_revision=snapshot["revision"],
            lines=[{**line, "description": "Divergent"} for line in first["lines"]],
        )


def test_manual_line_economic_changes_lock_after_reality_but_description_remains_correctable(
    session, business
):
    document, lines = manual_document(session, business)
    create_commitment(
        session,
        business.tenant.id,
        "customer_delivery",
        business.company.id,
        business.customer.id,
        business.item.id,
        business.location.id,
        2,
        "2026-09-03",
        document_line_id=lines[0].id,
    )
    snapshot = manual_document_line_snapshot(session, business.tenant.id, document.id)
    with pytest.raises(InvalidOperation, match="Reality correction workflow"):
        correct_manual_document_lines(
            session,
            business.tenant.id,
            document.id,
            expected_revision=snapshot["revision"],
            lines=[{**line, "quantity": "4"} for line in snapshot["lines"]],
        )
    result = correct_manual_document_lines(
        session,
        business.tenant.id,
        document.id,
        expected_revision=snapshot["revision"],
        lines=[
            {**line, "description": "Reference correction"}
            for line in snapshot["lines"]
        ],
    )
    assert result["changed"] is True


def test_manual_line_economic_changes_detect_document_commitment_and_ledger(
    session, business
):
    document, _ = manual_document(session, business)
    create_commitment(
        session,
        business.tenant.id,
        "customer_delivery",
        business.company.id,
        business.customer.id,
        business.item.id,
        business.location.id,
        1,
        "2026-09-03",
        document_id=document.id,
    )
    snapshot = manual_document_line_snapshot(session, business.tenant.id, document.id)
    with pytest.raises(InvalidOperation, match="Reality correction workflow"):
        correct_manual_document_lines(
            session,
            business.tenant.id,
            document.id,
            expected_revision=snapshot["revision"],
            lines=[{**line, "unit_price": "11"} for line in snapshot["lines"]],
        )

    invoice, _ = create_manual_document_with_lines(
        session,
        business.tenant.id,
        "sales_invoice",
        "INV-LINES",
        business.customer.id,
        [
            {
                "item_id": business.item.id,
                "source_line_id": "1",
                "quantity": "1",
                "unit_price": "25",
                "gross_amount": "25",
            }
        ],
        "25",
    )
    post_sales_invoice(session, business.tenant.id, invoice.id)
    invoice_snapshot = manual_document_line_snapshot(
        session, business.tenant.id, invoice.id
    )
    with pytest.raises(InvalidOperation, match="Reality correction workflow"):
        correct_manual_document_lines(
            session,
            business.tenant.id,
            invoice.id,
            expected_revision=invoice_snapshot["revision"],
            lines=[{**line, "quantity": "2"} for line in invoice_snapshot["lines"]],
        )


def test_external_line_snapshot_is_not_correctable(session, business):
    source, _ = enqueue_source(
        session,
        business.tenant.id,
        "shopify",
        "order",
        "line-source",
        {"id": "line-source"},
    )
    document = create_document(
        session,
        business.tenant.id,
        "sales_order",
        "EXT-LINES",
        business.customer.id,
        "10",
        source_record_id=source.id,
    )
    snapshot = manual_document_line_snapshot(session, business.tenant.id, document.id)
    assert snapshot["correctable"] is False
    assert snapshot["lines"] == []
    with pytest.raises(InvalidOperation, match="source version"):
        correct_manual_document_lines(
            session,
            business.tenant.id,
            document.id,
            expected_revision="",
            lines=[],
        )


def test_manual_line_event_failure_rolls_back_all_changes(
    session, business, monkeypatch
):
    document, lines = manual_document(session, business)
    snapshot = manual_document_line_snapshot(session, business.tenant.id, document.id)

    def fail_event(*args, **kwargs):
        raise RuntimeError("event unavailable")

    monkeypatch.setattr("reality.services.core.emit_business_event", fail_event)
    with pytest.raises(RuntimeError, match="event unavailable"):
        correct_manual_document_lines(
            session,
            business.tenant.id,
            document.id,
            expected_revision=snapshot["revision"],
            lines=[
                {**line, "description": "Must roll back"} for line in snapshot["lines"]
            ],
        )
    assert (
        record_by_id(session, DocumentLine, lines[0].id).description != "Must roll back"
    )


def test_manual_line_correction_rejects_foreign_item_with_overlapping_sku(
    session, business
):
    document, _ = manual_document(session, business)
    other = create_tenant(session, "Foreign line item tenant")
    foreign_item = create_item(session, other.id, business.item.sku, "Foreign item")
    snapshot = manual_document_line_snapshot(session, business.tenant.id, document.id)

    with pytest.raises(NotFound, match="not found"):
        correct_manual_document_lines(
            session,
            business.tenant.id,
            document.id,
            expected_revision=snapshot["revision"],
            lines=[{**snapshot["lines"][0], "item_id": foreign_item.id}],
        )
