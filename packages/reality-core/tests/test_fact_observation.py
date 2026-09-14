from __future__ import annotations

import pytest
from sqlalchemy import func, select

from reality.db.core import BusinessEvent, Fact
from reality.services.core import (
    InvalidOperation,
    NotFound,
    create_commitment,
    create_tenant,
    observe_fact,
    store_source_record,
)


def _commitment(session, business):
    return create_commitment(
        session,
        business.tenant.id,
        "customer_delivery",
        business.company.id,
        business.customer.id,
        business.item.id,
        business.location.id,
        "1",
        "2026-09-15T10:00:00Z",
    )


def _source(session, tenant_id, external_id="ORDER-42"):
    source, _, _ = store_source_record(
        session,
        tenant_id,
        "shopify",
        "order",
        external_id,
        {"id": external_id, "shipping_priority": "express"},
    )
    session.commit()
    return source


def test_observe_fact_requires_source_and_cataloged_existing_subject(session, business):
    commitment = _commitment(session, business)
    source = _source(session, business.tenant.id)

    fact = observe_fact(
        session,
        business.tenant.id,
        source_record_id=source.id,
        subject_type="commitment",
        subject_id=commitment.id,
        predicate="order.shipping_priority",
        value="express",
        observed_at="2026-09-02T14:06:00Z",
        idempotency_key="shopify-order-42-priority-v1",
    )

    assert fact.source_record_id == source.id
    assert fact.subject_id == commitment.id
    assert fact.value == "express"
    events = list(
        session.scalars(
            select(BusinessEvent).where(
                BusinessEvent.tenant_id == business.tenant.id,
                BusinessEvent.event_type == "fact.observed",
                BusinessEvent.subject_id == fact.id,
            )
        )
    )
    assert len(events) == 1


def test_observe_fact_is_idempotent_and_rejects_conflicting_reuse(session, business):
    commitment = _commitment(session, business)
    source = _source(session, business.tenant.id)
    arguments = {
        "source_record_id": source.id,
        "subject_type": "commitment",
        "subject_id": commitment.id,
        "predicate": "order.shipping_priority",
        "value": "express",
        "observed_at": "2026-09-02T14:06:00Z",
        "idempotency_key": "same-request",
    }
    first = observe_fact(session, business.tenant.id, **arguments)
    second = observe_fact(session, business.tenant.id, **arguments)
    assert second.id == first.id
    assert session.scalar(select(func.count(Fact.id))) == 1

    try:
        observe_fact(session, business.tenant.id, **{**arguments, "value": "standard"})
    except InvalidOperation as error:
        assert "Idempotency key" in str(error)
    else:
        raise AssertionError("Conflicting idempotency reuse must fail.")
    assert session.scalar(select(func.count(Fact.id))) == 1


def test_observe_fact_rejects_invalid_or_cross_tenant_inputs(session, business):
    commitment = _commitment(session, business)
    source = _source(session, business.tenant.id)
    other = create_tenant(session, "Other")
    foreign_source = _source(session, other.id, "FOREIGN")
    base = {
        "source_record_id": source.id,
        "subject_type": "commitment",
        "subject_id": commitment.id,
        "predicate": "order.shipping_priority",
        "value": "express",
        "observed_at": "2026-09-02T14:06:00Z",
        "idempotency_key": "invalid-request",
    }
    invalid = [
        ({**base, "source_record_id": foreign_source.id}, NotFound),
        ({**base, "predicate": "unknown.predicate"}, InvalidOperation),
        ({**base, "subject_type": "party"}, InvalidOperation),
        ({**base, "value": "overnight"}, InvalidOperation),
    ]
    for arguments, error_type in invalid:
        try:
            observe_fact(session, business.tenant.id, **arguments)
        except error_type:
            session.rollback()
        else:
            raise AssertionError(f"Expected {error_type.__name__}")
    assert session.scalar(select(func.count(Fact.id))) == 0


def _fact(session, business, source, subject_type, subject_id, predicate, value, key):
    return observe_fact(
        session,
        business.tenant.id,
        source_record_id=source.id,
        subject_type=subject_type,
        subject_id=subject_id,
        predicate=predicate,
        value=value,
        observed_at="2026-09-12T09:00:00Z",
        idempotency_key=key,
    )


def test_everyday_predicates_describe_documents_lines_lots_and_movements(
    session, business
):
    from reality.services.core import (
        create_item,
        create_lot,
        create_manual_document_with_lines,
        record_movement,
    )

    source = _source(session, business.tenant.id, "PHONE-2026-09-12")
    commitment = _commitment(session, business)
    invoice, lines = create_manual_document_with_lines(
        session,
        business.tenant.id,
        "supplier_invoice",
        "ER-1042",
        business.supplier.id,
        [{"quantity": "1", "unit": "pcs", "unit_price": "10", "gross_amount": "10"}],
        gross_amount="10",
    )
    line = lines[0]
    tracked = create_item(
        session, business.tenant.id, "BATCH-TEA", "Batch Tea", tracking_type="lot"
    )
    lot = create_lot(session, business.tenant.id, tracked.id, "4711")
    movement = record_movement(
        session,
        business.tenant.id,
        "receipt",
        business.item.id,
        "5",
        to_location_id=business.location.id,
    )
    session.commit()

    facts = [
        _fact(
            session,
            business,
            source,
            "commitment",
            commitment.id,
            "order.delivery_instruction",
            "mornings only, side entrance",
            "k1",
        ),
        _fact(
            session,
            business,
            source,
            "document",
            invoice.id,
            "order.customer_reference",
            "PO-88231",
            "k2",
        ),
        _fact(
            session,
            business,
            source,
            "document",
            invoice.id,
            "invoice.payment_promise_date",
            "2026-09-30",
            "k3",
        ),
        _fact(
            session,
            business,
            source,
            "document_line",
            line.id,
            "invoice_line.dispute_reason",
            "price differs from the quotation",
            "k4",
        ),
        _fact(
            session,
            business,
            source,
            "lot",
            lot.id,
            "lot.quality_release",
            "released",
            "k5",
        ),
        _fact(
            session,
            business,
            source,
            "movement",
            movement.id,
            "movement.damage_report",
            "two cartons crushed",
            "k6",
        ),
    ]
    assert [fact.predicate for fact in facts] == [
        "order.delivery_instruction",
        "order.customer_reference",
        "invoice.payment_promise_date",
        "invoice_line.dispute_reason",
        "lot.quality_release",
        "movement.damage_report",
    ]
    assert facts[2].value == "2026-09-30"
    assert facts[4].subject_type == "lot" and facts[4].subject_id == lot.id
    assert all(fact.source_record_id == source.id for fact in facts)


def test_everyday_predicates_keep_their_value_and_subject_contracts(session, business):
    from reality.services.core import (
        create_item,
        create_lot,
        create_manual_document_with_lines,
    )

    source = _source(session, business.tenant.id, "PHONE-2026-09-13")
    commitment = _commitment(session, business)
    invoice, _ = create_manual_document_with_lines(
        session,
        business.tenant.id,
        "supplier_invoice",
        "ER-1043",
        business.supplier.id,
        [{"quantity": "1", "unit": "pcs", "unit_price": "10", "gross_amount": "10"}],
        gross_amount="10",
    )
    tracked = create_item(
        session, business.tenant.id, "BATCH-COFFEE", "Batch Coffee", tracking_type="lot"
    )
    lot = create_lot(session, business.tenant.id, tracked.id, "4712")
    session.commit()

    # A payment promise belongs to an invoice, not to a delivery promise.
    with pytest.raises(InvalidOperation, match="subject type"):
        _fact(
            session,
            business,
            source,
            "commitment",
            commitment.id,
            "invoice.payment_promise_date",
            "2026-09-30",
            "k7",
        )
    # A quality decision is one of the reviewed values, not free text.
    with pytest.raises(InvalidOperation, match="does not satisfy lot.quality_release"):
        _fact(
            session,
            business,
            source,
            "lot",
            lot.id,
            "lot.quality_release",
            "looks fine",
            "k8",
        )
    # A promise date is a calendar day.
    with pytest.raises(
        InvalidOperation, match="does not satisfy invoice.payment_promise_date"
    ):
        _fact(
            session,
            business,
            source,
            "document",
            invoice.id,
            "invoice.payment_promise_date",
            "end of month",
            "k9",
        )
