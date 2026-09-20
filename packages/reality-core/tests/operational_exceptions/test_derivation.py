from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from types import SimpleNamespace

import pytest
from sqlalchemy import select

from reality.db.core import (
    Commitment,
    ImportJob,
    LedgerEntry,
    Reservation,
    SourceRecord,
    uid,
)
from reality.services import core
from reality.services.core import (
    allocate_credit_note,
    allocate_supplier_credit_note,
    create_commitment,
    create_document,
    create_item,
    create_location,
    create_manual_document_with_lines,
    create_manual_order,
    create_party,
    create_payment_term,
    create_price_list,
    create_price_list_entry,
    create_source_capability,
    create_source_system,
    create_tenant,
    enqueue_shopify_order,
    inventory_rows,
    open_invoice_amount,
    payment_terms,
    post_customer_payment,
    post_customer_refund,
    post_ledger,
    post_sales_credit_note,
    post_sales_invoice,
    post_supplier_credit_note,
    post_supplier_invoice,
    post_supplier_payment,
    post_supplier_refund,
    process_import_job,
    record_movement,
    release_reservation,
    reserve,
    retry_import_job,
    reverse_ledger_posting_group,
    revise_commitment,
    update_item,
    update_party,
)
from reality.services.exceptions import operational_exceptions

AS_OF = datetime(2026, 8, 31, 12, tzinfo=UTC)


def by_class(session, tenant_id, *, as_of=AS_OF):
    return {
        row.class_id: row
        for row in operational_exceptions(session, tenant_id, as_of=as_of)
    }


def test_outgoing_commitment_at_risk(session, business):
    commitment = create_commitment(
        session,
        business.tenant.id,
        "customer_delivery",
        business.company.id,
        business.customer.id,
        business.item.id,
        business.location.id,
        5,
        AS_OF + timedelta(days=1),
    )

    row = by_class(session, business.tenant.id)["outgoing_commitment_at_risk"]

    assert row.record_id == commitment.id
    assert row.cause_ids == ("insufficient_reservation",)
    assert row.causal_values["unreserved_quantity"] == Decimal("5.0000")


def test_overdue_incoming_supplier_commitment(session, business):
    commitment = create_commitment(
        session,
        business.tenant.id,
        "supplier_delivery",
        business.supplier.id,
        business.company.id,
        business.item.id,
        business.location.id,
        7,
        AS_OF - timedelta(seconds=1),
    )

    row = by_class(session, business.tenant.id)["overdue_incoming_supplier_commitment"]

    assert row.record_id == commitment.id
    assert row.causal_values["remaining_quantity"] == Decimal("7.0000")


def test_source_interpretation_failure(session, business):
    source = SourceRecord(
        id=uid("src"),
        tenant_id=business.tenant.id,
        source_system="test",
        source_type="order",
        external_id="shared-human-id",
        payload='{"complete": true}',
        payload_hash="a" * 64,
        version=1,
    )
    job = ImportJob(
        id=uid("job"),
        tenant_id=business.tenant.id,
        source_record_id=source.id,
        status="failed",
        error="Any parser error",
    )
    session.add(source)
    session.flush()
    session.add(job)
    session.flush()

    row = by_class(session, business.tenant.id)["source_interpretation_failure"]

    assert row.record_id == job.id
    assert row.trace["source_record_id"] == source.id
    assert row.causal_values["error"] == "Any parser error"


def test_source_interpretation_failure_disappears_after_successful_retry(
    session, business, monkeypatch
):
    source, job = enqueue_shopify_order(
        session,
        business.tenant.id,
        {
            "id": 4502,
            "name": "#4502",
            "created_at": "2026-09-03T10:00:00Z",
            "updated_at": "2026-09-03T10:00:00Z",
            "currency": "EUR",
            "total_price": "12.00",
            "line_items": [
                {
                    "id": 92,
                    "sku": business.item.sku,
                    "name": business.item.name,
                    "quantity": 1,
                    "price": "12.00",
                }
            ],
        },
        business.company.id,
        business.customer.id,
        business.location.id,
    )
    interpreter = core.SOURCE_INTERPRETERS[("shopify", "order")]

    def fail(*args, **kwargs):
        raise RuntimeError("transient parser failure")

    monkeypatch.setitem(core.SOURCE_INTERPRETERS, ("shopify", "order"), fail)
    with pytest.raises(RuntimeError, match="transient parser failure"):
        process_import_job(session, business.tenant.id, job.id)
    failed = by_class(session, business.tenant.id)["source_interpretation_failure"]
    assert failed.record_id == job.id
    assert failed.trace["source_record_id"] == source.id

    monkeypatch.setitem(core.SOURCE_INTERPRETERS, ("shopify", "order"), interpreter)
    retry_import_job(session, business.tenant.id, job.id)
    process_import_job(session, business.tenant.id, job.id)

    assert "source_interpretation_failure" not in by_class(session, business.tenant.id)


def test_unexplained_movement(session, business):
    record_movement(
        session,
        business.tenant.id,
        "opening_stock",
        business.item.id,
        3,
        to_location_id=business.location.id,
    )
    movement = record_movement(
        session,
        business.tenant.id,
        "shipment",
        business.item.id,
        1,
        from_location_id=business.location.id,
    )

    row = by_class(session, business.tenant.id)["unexplained_movement"]

    assert row.record_id == movement.id
    assert row.trace["commitment_absent"] is True
    assert row.trace["source_absent"] is True


def test_unmatched_financial_event(session, business):
    payment = create_document(
        session,
        business.tenant.id,
        "customer_payment",
        "PAY-1",
        business.customer.id,
        25,
    )
    entries = post_ledger(
        session,
        business.tenant.id,
        payment.id,
        business.customer.id,
        [
            ("cash", "debit", 25),
            ("accounts_receivable", "credit", 25),
        ],
    )
    control = next(row for row in entries if row.account == "accounts_receivable")

    row = by_class(session, business.tenant.id)["unmatched_financial_event"]

    assert row.record_id == control.id
    assert row.causal_values["unallocated_amount"] == Decimal("25.0000")


def records_of(session, tenant_id, class_id, *, as_of=AS_OF):
    return {
        row.record_id
        for row in operational_exceptions(session, tenant_id, as_of=as_of)
        if row.class_id == class_id
    }


def promise(
    session, tenant_id, company_id, customer_id, item_id, location_id, quantity, due_at
):
    return create_commitment(
        session,
        tenant_id,
        "customer_delivery",
        company_id,
        customer_id,
        item_id,
        location_id,
        quantity,
        due_at,
    )


def customer_commitment(session, business, quantity, due_at):
    return promise(
        session,
        business.tenant.id,
        business.company.id,
        business.customer.id,
        business.item.id,
        business.location.id,
        quantity,
        due_at,
    )


def test_overdue_outgoing_customer_commitment(session, business):
    commitment = customer_commitment(session, business, 4, AS_OF - timedelta(days=2))

    row = by_class(session, business.tenant.id)["overdue_outgoing_customer_commitment"]

    assert row.id == f"exc__overdue_outgoing_customer_commitment__{commitment.id}"
    assert row.record_type == "commitment"
    assert row.record_id == commitment.id
    assert row.severity == "high"
    assert row.causal_values["remaining_quantity"] == Decimal(4)
    assert row.causal_values["due_at"] < row.causal_values["as_of"]
    assert row.trace["commitment_id"] == commitment.id


def test_overdue_outgoing_boundaries(session, business):
    tenant_id = business.tenant.id
    absent = customer_commitment(session, business, 1, None)
    future = customer_commitment(session, business, 1, AS_OF + timedelta(days=1))
    exactly_due = customer_commitment(session, business, 1, AS_OF)
    overdue = customer_commitment(session, business, 1, AS_OF - timedelta(seconds=1))

    overdue_class = "overdue_outgoing_customer_commitment"
    assert records_of(session, tenant_id, overdue_class) == {overdue.id}
    assert {absent.id, future.id, exactly_due.id} <= records_of(
        session, tenant_id, "outgoing_commitment_at_risk"
    )

    record_movement(
        session,
        tenant_id,
        "opening_stock",
        business.item.id,
        1,
        to_location_id=business.location.id,
    )
    record_movement(
        session,
        tenant_id,
        "shipment",
        business.item.id,
        1,
        from_location_id=business.location.id,
        commitment_id=overdue.id,
    )

    assert records_of(session, tenant_id, overdue_class) == set()


def test_overdue_outgoing_supersedes_at_risk(session, business):
    tenant_id = business.tenant.id
    record_movement(
        session,
        tenant_id,
        "opening_stock",
        business.item.id,
        6,
        to_location_id=business.location.id,
    )
    commitment = customer_commitment(session, business, 10, AS_OF - timedelta(days=1))
    reserve(session, tenant_id, commitment.id)

    rows = [
        row
        for row in operational_exceptions(session, tenant_id, as_of=AS_OF)
        if row.record_id == commitment.id
    ]

    assert len(rows) == 1
    assert rows[0].class_id == "overdue_outgoing_customer_commitment"
    assert rows[0].cause_ids == ("insufficient_reservation",)
    assert rows[0].causal_values["remaining_quantity"] == Decimal(10)
    assert rows[0].causal_values["unreserved_quantity"] == Decimal(4)
    # A partial shortfall adds a number the condition does not carry, so the
    # clause stays in the queue row.
    assert "10" in rows[0].impact
    assert "4" in rows[0].impact
    assert "unreserved" in rows[0].impact

    # A promise with nothing reserved at all keeps the cause but not the
    # clause: it would repeat the overdue remainder. This is the common row
    # after importing an established order book.
    bare = customer_commitment(session, business, 7, AS_OF - timedelta(days=1))

    entry = next(
        row
        for row in operational_exceptions(session, tenant_id, as_of=AS_OF)
        if row.record_id == bare.id
    )

    assert entry.class_id == "overdue_outgoing_customer_commitment"
    assert entry.cause_ids == ("insufficient_reservation",)
    assert entry.causal_values["unreserved_quantity"] == Decimal(7)
    assert "unreserved" not in entry.impact
    assert entry.impact.count("7") == 1


def test_at_risk_unchanged_before_due_date(session, business):
    tenant_id = business.tenant.id
    commitment = customer_commitment(session, business, 5, AS_OF + timedelta(days=1))

    rows = by_class(session, tenant_id)
    at_risk = rows["outgoing_commitment_at_risk"]

    assert at_risk.record_id == commitment.id
    assert at_risk.cause_ids == ("insufficient_reservation",)
    assert at_risk.causal_values["unreserved_quantity"] == Decimal(5)
    assert "overdue_outgoing_customer_commitment" not in rows


def test_reservation_exceeds_stock(session, business):
    tenant_id = business.tenant.id
    item_id = business.item.id
    location_id = business.location.id
    record_movement(
        session, tenant_id, "opening_stock", item_id, 10, to_location_id=location_id
    )
    commitment = customer_commitment(session, business, 10, AS_OF + timedelta(days=5))

    allocation = reserve(session, tenant_id, commitment.id)

    # Reserving cannot over-allocate, so the condition never arises at write time.
    assert allocation.reserved == Decimal(10)
    assert allocation.shortage == Decimal(0)
    assert "reservation_exceeds_stock" not in by_class(session, tenant_id)

    record_movement(
        session,
        tenant_id,
        "adjustment",
        item_id,
        4,
        from_location_id=location_id,
        reason="stocktake loss",
    )

    row = by_class(session, tenant_id)["reservation_exceeds_stock"]
    assert row.id == f"exc__reservation_exceeds_stock__{item_id}"
    assert row.record_type == "item"
    assert row.record_id == item_id
    assert row.severity == "high"
    assert row.causal_values["observed_stock"] == Decimal(6)
    assert row.causal_values["reserved_quantity"] == Decimal(10)
    assert row.causal_values["shortfall"] == Decimal(4)
    # The promise still holds a reservation covering its remainder, so the
    # commitment-level class reports nothing. Only this class sees the loss.
    assert "outgoing_commitment_at_risk" not in by_class(session, tenant_id)

    record_movement(
        session, tenant_id, "receipt", item_id, 4, to_location_id=location_id
    )
    assert "reservation_exceeds_stock" not in by_class(session, tenant_id)

    record_movement(
        session, tenant_id, "receipt", item_id, 5, to_location_id=location_id
    )
    assert "reservation_exceeds_stock" not in by_class(session, tenant_id)

    elsewhere = create_location(session, tenant_id, "Munich Warehouse")
    record_movement(
        session,
        tenant_id,
        "transfer",
        item_id,
        15,
        from_location_id=location_id,
        to_location_id=elsewhere.id,
    )
    # Coverage is judged per item across the tenant, so stock held in another
    # location still counts as backing.
    assert "reservation_exceeds_stock" not in by_class(session, tenant_id)

    # An item reserved without any recorded movement has no backing at all. The
    # reservation is written directly because reserve() allocates nothing when
    # no stock exists.
    spare = create_item(session, tenant_id, "BIKE-BELL", "Bike Bell")
    spare_commitment = promise(
        session,
        tenant_id,
        business.company.id,
        business.customer.id,
        spare.id,
        location_id,
        3,
        AS_OF + timedelta(days=5),
    )
    session.add(
        Reservation(
            id=uid("res"),
            tenant_id=tenant_id,
            commitment_id=spare_commitment.id,
            item_id=spare.id,
            location_id=location_id,
            quantity=Decimal(3),
            status="active",
        )
    )
    session.flush()

    assert records_of(session, tenant_id, "reservation_exceeds_stock") == {spare.id}


def unbacked_reservations(session, business):
    """Two promises backed by stock that then partly disappears."""
    tenant_id = business.tenant.id
    record_movement(
        session,
        tenant_id,
        "opening_stock",
        business.item.id,
        10,
        to_location_id=business.location.id,
    )
    first = customer_commitment(session, business, 6, AS_OF + timedelta(days=5))
    second = customer_commitment(session, business, 4, AS_OF + timedelta(days=5))
    first_reservation = reserve(session, tenant_id, first.id).reservation
    second_reservation = reserve(session, tenant_id, second.id).reservation
    record_movement(
        session,
        tenant_id,
        "adjustment",
        business.item.id,
        5,
        from_location_id=business.location.id,
        reason="stocktake loss",
    )
    return (first, second), (first_reservation, second_reservation)


def test_reservation_exceeds_stock_impact(session, business):
    unbacked_reservations(session, business)

    row = by_class(session, business.tenant.id)["reservation_exceeds_stock"]

    assert row.causal_values["observed_stock"] == Decimal(5)
    assert row.causal_values["reserved_quantity"] == Decimal(10)
    assert row.causal_values["shortfall"] == Decimal(5)
    assert row.causal_values["competing_commitments"] == 2
    assert "5" in row.impact
    assert "2" in row.impact


def test_reservation_exceeds_stock_references_are_opaque(session, business):
    commitments, reservations = unbacked_reservations(session, business)

    row = by_class(session, business.tenant.id)["reservation_exceeds_stock"]

    assert row.trace["item_id"] == business.item.id
    assert set(row.trace["reservation_ids"]) == {
        reservation.id for reservation in reservations
    }
    assert set(row.trace["commitment_ids"]) == {
        commitment.id for commitment in commitments
    }
    # No promise is named as the one that will fail, and no business field is
    # restated from the records the trace points at.
    assert not {
        "failing_commitment_id",
        "item_name",
        "sku",
        "name",
        "quantity",
    } & set(row.trace)


def test_queue_and_inventory_agree_on_availability(session, business):
    unbacked_reservations(session, business)

    row = by_class(session, business.tenant.id)["reservation_exceeds_stock"]
    inventory = next(
        entry
        for entry in inventory_rows(session, business.tenant.id)
        if entry["item"].id == business.item.id
    )

    assert row.causal_values["observed_stock"] == inventory["physical"]
    assert row.causal_values["reserved_quantity"] == inventory["reserved"]
    assert row.causal_values["shortfall"] == -inventory["available"]


def both_new_classes(session, tenant_id, company_id, customer_id, item_id, location_id):
    """One overdue promise and one unbacked reservation, on separate items."""
    overdue = promise(
        session,
        tenant_id,
        company_id,
        customer_id,
        item_id,
        location_id,
        4,
        AS_OF - timedelta(days=2),
    )
    other = create_item(session, tenant_id, "BIKE-BELL", "Bike Bell")
    record_movement(
        session, tenant_id, "opening_stock", other.id, 8, to_location_id=location_id
    )
    backed = promise(
        session,
        tenant_id,
        company_id,
        customer_id,
        other.id,
        location_id,
        8,
        AS_OF + timedelta(days=5),
    )
    reservation = reserve(session, tenant_id, backed.id).reservation
    record_movement(
        session,
        tenant_id,
        "adjustment",
        other.id,
        3,
        from_location_id=location_id,
        reason="stocktake loss",
    )
    return overdue, other, reservation


def both_for(session, business):
    return both_new_classes(
        session,
        business.tenant.id,
        business.company.id,
        business.customer.id,
        business.item.id,
        business.location.id,
    )


def test_new_classes_expose_full_entry_shape(session, business):
    overdue, other, _ = both_for(session, business)

    rows = by_class(session, business.tenant.id)

    expected = {
        "overdue_outgoing_customer_commitment": ("commitment", overdue.id),
        "reservation_exceeds_stock": ("item", other.id),
    }
    for class_id, (record_type, record_id) in expected.items():
        row = rows[class_id]
        assert row.record_type == record_type
        assert row.record_id == record_id
        assert row.severity == "high"
        assert row.title
        assert row.impact
        assert row.causal_values
        assert row.trace
        payload = row.to_dict()
        assert {
            "id",
            "class_id",
            "cause_ids",
            "severity",
            "title",
            "impact",
            "record_type",
            "record_id",
            "causal_values",
            "trace",
            "sort_at",
        } <= set(payload)
        # The row carries the moment it is ordered by. It used to be dropped here,
        # and the stored projection kept each row's rank instead — which is what
        # stopped that projection deriving by change (spec 181 FR-002).
        assert payload["sort_at"] is None or payload["sort_at"].endswith("+00:00")


def test_new_classes_clear_through_reality(session, business):
    tenant_id = business.tenant.id
    overdue, _, reservation = both_for(session, business)
    present = by_class(session, tenant_id)
    assert "overdue_outgoing_customer_commitment" in present
    assert "reservation_exceeds_stock" in present

    record_movement(
        session,
        tenant_id,
        "opening_stock",
        business.item.id,
        4,
        to_location_id=business.location.id,
    )
    record_movement(
        session,
        tenant_id,
        "shipment",
        business.item.id,
        4,
        from_location_id=business.location.id,
        commitment_id=overdue.id,
    )
    release_reservation(session, tenant_id, reservation.id)

    cleared = by_class(session, tenant_id)
    assert "overdue_outgoing_customer_commitment" not in cleared
    assert "reservation_exceeds_stock" not in cleared


def test_new_classes_are_tenant_scoped(session, business):
    both_for(session, business)
    other_tenant = create_tenant(session, "Nordwind Handel GmbH")
    both_new_classes(
        session,
        other_tenant.id,
        create_party(session, other_tenant.id, "Nordwind Handel GmbH", "company").id,
        create_party(session, other_tenant.id, "Schmidt AG", "customer").id,
        create_item(session, other_tenant.id, "BIKE-LIGHT", "Bike Light").id,
        create_location(session, other_tenant.id, "Bremen Warehouse").id,
    )

    for class_id in (
        "overdue_outgoing_customer_commitment",
        "reservation_exceeds_stock",
    ):
        ours = records_of(session, business.tenant.id, class_id)
        theirs = records_of(session, other_tenant.id, class_id)
        assert ours
        assert theirs
        assert not ours & theirs


def test_queue_order_places_overdue_before_at_risk(session, business):
    tenant_id = business.tenant.id
    both_for(session, business)
    customer_commitment(session, business, 2, AS_OF + timedelta(days=3))

    first = operational_exceptions(session, tenant_id, as_of=AS_OF)
    classes = [row.class_id for row in first]

    assert classes.index("overdue_outgoing_customer_commitment") < classes.index(
        "outgoing_commitment_at_risk"
    )
    assert classes.index("outgoing_commitment_at_risk") < classes.index(
        "reservation_exceeds_stock"
    )
    second = operational_exceptions(session, tenant_id, as_of=AS_OF)
    assert [row.id for row in second] == [row.id for row in first]


def sales_invoice(
    session,
    business,
    number,
    document_date,
    amount="1000.00",
    *,
    term_code="",
    document_type="sales_invoice",
):
    return create_document(
        session,
        business.tenant.id,
        document_type,
        number,
        business.customer.id
        if document_type == "sales_invoice"
        else business.supplier.id,
        amount,
        document_date=document_date,
        payment_term_code=term_code,
    )


def overdue_invoice(session, business, number="RE-9001", amount="1000.00"):
    """A posted sales invoice due 2026-07-31, so overdue at AS_OF."""
    create_payment_term(session, business.tenant.id, "NET30", "Net 30 days", 30)
    invoice = sales_invoice(
        session, business, number, "2026-07-01", amount, term_code="NET30"
    )
    entries = post_sales_invoice(session, business.tenant.id, invoice.id)
    return invoice, entries


def test_overdue_receivable(session, business):
    invoice, _ = overdue_invoice(session, business)

    row = by_class(session, business.tenant.id)["overdue_receivable"]

    assert row.id == f"exc__overdue_receivable__{invoice.id}"
    assert row.record_type == "document"
    assert row.record_id == invoice.id
    assert row.severity == "high"
    assert row.causal_values["due_date"] == date(2026, 7, 31)
    assert row.causal_values["days_overdue"] == 31
    assert row.causal_values["outstanding_amount"] == Decimal(1000)
    assert row.causal_values["currency"] == "EUR"
    assert row.trace["document_id"] == invoice.id


def test_overdue_receivable_boundaries(session, business):
    tenant_id = business.tenant.id
    create_payment_term(session, tenant_id, "NET30", "Net 30 days", 30)
    overdue = sales_invoice(session, business, "RE-1", "2026-07-01", term_code="NET30")
    not_yet_due = sales_invoice(
        session, business, "RE-2", "2026-08-30", term_code="NET30"
    )
    exactly_due = sales_invoice(
        session, business, "RE-3", "2026-08-01", term_code="NET30"
    )
    no_date = sales_invoice(session, business, "RE-4", "", term_code="NET30")
    settled = sales_invoice(session, business, "RE-5", "2026-07-01", term_code="NET30")
    reversed_invoice = sales_invoice(
        session, business, "RE-6", "2026-07-01", term_code="NET30"
    )
    supplier = sales_invoice(
        session,
        business,
        "ER-1",
        "2026-07-01",
        "500.00",
        term_code="NET30",
        document_type="supplier_invoice",
    )
    for document in (
        overdue,
        not_yet_due,
        exactly_due,
        no_date,
        settled,
        reversed_invoice,
    ):
        post_sales_invoice(session, tenant_id, document.id)
    post_supplier_invoice(session, tenant_id, supplier.id)
    post_customer_payment(session, tenant_id, settled.id, "1000.00")
    group = session.scalar(
        select(LedgerEntry.posting_group_id).where(
            LedgerEntry.tenant_id == tenant_id,
            LedgerEntry.document_id == reversed_invoice.id,
        )
    )
    reverse_ledger_posting_group(
        session, tenant_id, group, reason="Issued to the wrong customer"
    )

    assert records_of(session, tenant_id, "overdue_receivable") == {overdue.id}


def test_overdue_receivable_reports_the_outstanding_amount(session, business):
    invoice, _ = overdue_invoice(session, business, amount="1470.00")
    post_customer_payment(session, business.tenant.id, invoice.id, "500.00")
    credit = create_document(
        session,
        business.tenant.id,
        "credit_note",
        "GS-OUTSTANDING",
        business.customer.id,
        "100.00",
        document_date="2026-08-20",
    )
    post_sales_credit_note(session, business.tenant.id, credit.id)
    allocate_credit_note(session, business.tenant.id, credit.id, invoice.id, "100.00")

    row = by_class(session, business.tenant.id)["overdue_receivable"]

    # 1470 gross, 500 paid, 100 credited: the queue reports what is still owed.
    assert row.causal_values["outstanding_amount"] == Decimal(870)
    assert row.causal_values["gross_amount"] == Decimal(1470)
    assert open_invoice_amount(session, business.tenant.id, invoice.id) == Decimal(870)
    assert "870" in row.impact


def test_overdue_receivable_entry_shape(session, business):
    invoice, entries = overdue_invoice(session, business)
    control = next(entry for entry in entries if entry.account == "accounts_receivable")

    row = by_class(session, business.tenant.id)["overdue_receivable"]

    assert row.cause_ids == ()
    assert row.title
    assert row.impact
    assert row.trace["document_id"] == invoice.id
    assert row.trace["ledger_entry_id"] == control.id
    assert row.trace["source_record_id"] is None
    # Opaque identities only; no business field is restated from the invoice.
    assert not {"number", "party", "gross_amount", "document_date"} & set(row.trace)
    payload = row.to_dict()
    assert {
        "id",
        "class_id",
        "cause_ids",
        "severity",
        "title",
        "impact",
        "record_type",
        "record_id",
        "causal_values",
        "trace",
    } <= set(payload)


def test_overdue_receivable_clears_through_settlement(session, business):
    tenant_id = business.tenant.id
    invoice, _ = overdue_invoice(session, business)
    assert "overdue_receivable" in by_class(session, tenant_id)

    post_customer_payment(session, tenant_id, invoice.id, "1000.00")

    assert "overdue_receivable" not in by_class(session, tenant_id)


def test_overdue_receivable_is_tenant_scoped(session, business):
    tenant_id = business.tenant.id
    mine, _ = overdue_invoice(session, business)
    other_tenant = create_tenant(session, "Nordwind Handel GmbH")
    other_customer = create_party(session, other_tenant.id, "Schmidt AG", "customer")
    create_payment_term(session, other_tenant.id, "NET30", "Net 30 days", 30)
    theirs = create_document(
        session,
        other_tenant.id,
        "sales_invoice",
        "RE-9001",
        other_customer.id,
        "1000.00",
        document_date="2026-07-01",
        payment_term_code="NET30",
    )
    post_sales_invoice(session, other_tenant.id, theirs.id)

    assert records_of(session, tenant_id, "overdue_receivable") == {mine.id}
    assert records_of(session, other_tenant.id, "overdue_receivable") == {theirs.id}


def test_overdue_receivable_orders_before_unmatched_payment(session, business):
    tenant_id = business.tenant.id
    older, _ = overdue_invoice(session, business, number="RE-8000")
    newer = sales_invoice(session, business, "RE-8001", "2026-07-15", term_code="NET30")
    post_sales_invoice(session, tenant_id, newer.id)
    standalone = create_document(
        session, tenant_id, "customer_payment", "PAY-1", business.customer.id, 25
    )
    post_ledger(
        session,
        tenant_id,
        standalone.id,
        business.customer.id,
        [("cash", "debit", 25), ("accounts_receivable", "credit", 25)],
    )

    first = operational_exceptions(session, tenant_id, as_of=AS_OF)
    classes = [row.class_id for row in first]

    assert classes.index("overdue_receivable") < classes.index(
        "unmatched_financial_event"
    )
    # Longest overdue first among receivables.
    receivables = [row for row in first if row.class_id == "overdue_receivable"]
    assert [row.record_id for row in receivables] == [older.id, newer.id]
    second = operational_exceptions(session, tenant_id, as_of=AS_OF)
    assert [row.id for row in second] == [row.id for row in first]


SILENT_AS_OF = datetime(2026, 9, 21, 12, tzinfo=UTC)


def declared_capability(session, tenant_id, *, code="shopify", source_type="order"):
    system = create_source_system(session, tenant_id, code, code.title())
    return system, create_source_capability(
        session, tenant_id, system.id, source_type, "document"
    )


def deliver(session, tenant_id, system, source_type, received_at, sequence):
    """Record one arrival at a controlled instant."""
    record = SourceRecord(
        id=uid("src"),
        tenant_id=tenant_id,
        source_system=system.code,
        source_type=source_type,
        external_id=f"{system.code}-{sequence}",
        payload='{"ok": true}',
        payload_hash=f"{sequence:064d}",
        version=1,
        received_at=received_at,
    )
    session.add(record)
    session.flush()
    return record


def daily_history(
    session, tenant_id, system, *, days=8, source_type="order", last=None
):
    """One arrival a day, so the longest pause is a day."""
    last = last or SILENT_AS_OF - timedelta(days=1)
    records = [
        deliver(
            session,
            tenant_id,
            system,
            source_type,
            last - timedelta(days=offset),
            offset,
        )
        for offset in range(days)
    ]
    return records[0]


def test_silent_source(session, business):
    tenant_id = business.tenant.id
    system, capability = declared_capability(session, tenant_id)
    latest = daily_history(
        session, tenant_id, system, last=SILENT_AS_OF - timedelta(days=4)
    )

    row = by_class(session, tenant_id, as_of=SILENT_AS_OF)["silent_source"]

    assert row.id == f"exc__silent_source__{capability.id}"
    assert row.record_type == "source_capability"
    assert row.record_id == capability.id
    assert row.severity == "high"
    # Silence runs from the last arrival to the evaluation instant.
    assert row.causal_values["last_received_at"] == latest.received_at
    assert row.causal_values["silent_hours"] == 96
    assert row.causal_values["expected_pause_hours"] == 24


def test_silent_source_learns_the_rhythm(session, business):
    tenant_id = business.tenant.id
    system, _ = declared_capability(session, tenant_id)
    # Weekdays only: the source pauses three days across every weekend, which is
    # its rhythm rather than a fault.
    friday = datetime(2026, 9, 18, 9, tzinfo=UTC)
    weekdays = []
    day = friday
    while len(weekdays) < 10:
        if day.weekday() < 5:
            weekdays.append(day)
        day -= timedelta(days=1)
    for sequence, moment in enumerate(weekdays):
        deliver(session, tenant_id, system, "order", moment, sequence)

    monday = datetime(2026, 9, 21, 9, tzinfo=UTC)

    # Read on Monday morning after a normal weekend: nothing to report.
    assert "silent_source" not in by_class(session, tenant_id, as_of=monday)

    # The same history read a week later, with nothing delivered since Friday.
    later = datetime(2026, 9, 28, 9, tzinfo=UTC)
    row = by_class(session, tenant_id, as_of=later)["silent_source"]
    assert row.causal_values["expected_pause_hours"] == 72
    assert row.causal_values["silent_hours"] == 240


def test_silent_source_floor_protects_fast_sources(session, business):
    tenant_id = business.tenant.id
    system, _ = declared_capability(session, tenant_id)
    # A minute-rhythm source: twice its longest pause is minutes, but the floor
    # keeps a brief interruption out of the queue.
    for sequence in range(10):
        deliver(
            session,
            tenant_id,
            system,
            "order",
            SILENT_AS_OF - timedelta(minutes=30 + sequence),
            sequence,
        )

    assert "silent_source" not in by_class(session, tenant_id, as_of=SILENT_AS_OF)

    later = SILENT_AS_OF + timedelta(hours=30)
    assert "silent_source" in by_class(session, tenant_id, as_of=later)

    # Every arrival in the same second: no pause was ever observed, so only the
    # floor decides.
    other = create_tenant(session, "Same Second GmbH")
    other_system, _ = declared_capability(session, other.id, code="samesecond")
    moment = SILENT_AS_OF - timedelta(hours=30)
    for sequence in range(10):
        deliver(session, other.id, other_system, "order", moment, sequence)

    row = by_class(session, other.id, as_of=SILENT_AS_OF)["silent_source"]
    assert row.causal_values["expected_pause_hours"] == 0


def test_silent_source_handles_receipts_after_the_evaluation_instant(session, business):
    tenant_id = business.tenant.id
    system, _ = declared_capability(session, tenant_id)
    daily_history(session, tenant_id, system, last=SILENT_AS_OF + timedelta(days=1))

    # A receipt ahead of the instant means no silence at all, not a negative one.
    assert "silent_source" not in by_class(session, tenant_id, as_of=SILENT_AS_OF)

    other = create_tenant(session, "Out Of Order GmbH")
    other_system, _ = declared_capability(session, other.id, code="unordered")
    moments = [
        SILENT_AS_OF - timedelta(days=offset) for offset in (7, 3, 5, 1, 6, 2, 4)
    ]
    for sequence, moment in enumerate(moments):
        deliver(session, other.id, other_system, "order", moment, sequence)

    # Written out of order, the rhythm is still a day.
    later = SILENT_AS_OF + timedelta(days=3)
    row = by_class(session, other.id, as_of=later)["silent_source"]
    assert row.causal_values["expected_pause_hours"] == 24


def test_silent_source_says_nothing_without_history(session, business):
    tenant_id = business.tenant.id
    empty_system, _ = declared_capability(session, tenant_id, code="never")
    sparse_system, _ = declared_capability(session, tenant_id, code="sparse")
    for sequence in range(3):
        deliver(
            session,
            tenant_id,
            sparse_system,
            "order",
            SILENT_AS_OF - timedelta(days=30 + sequence),
            sequence,
        )
    inactive_system, inactive = declared_capability(session, tenant_id, code="inactive")
    daily_history(
        session,
        tenant_id,
        inactive_system,
        last=SILENT_AS_OF - timedelta(days=10),
    )
    inactive.is_active = False
    session.flush()
    # A fourth capability with a real history and a real silence, so the
    # assertion below proves exclusion rather than an empty derivation.
    watched_system, watched = declared_capability(session, tenant_id, code="watched")
    daily_history(
        session,
        tenant_id,
        watched_system,
        last=SILENT_AS_OF - timedelta(days=4),
    )

    assert empty_system is not None
    assert records_of(session, tenant_id, "silent_source", as_of=SILENT_AS_OF) == {
        watched.id
    }


def test_silent_source_entry_shape(session, business):
    tenant_id = business.tenant.id
    system, capability = declared_capability(session, tenant_id)
    latest = daily_history(
        session, tenant_id, system, last=SILENT_AS_OF - timedelta(days=4)
    )

    row = by_class(session, tenant_id, as_of=SILENT_AS_OF)["silent_source"]

    assert row.cause_ids == ()
    assert row.title
    assert row.impact
    assert "96" in row.impact
    assert row.trace["source_capability_id"] == capability.id
    assert row.trace["source_system_id"] == system.id
    assert row.trace["source_record_id"] == latest.id
    # Opaque identities only; no business field is restated.
    assert not {"code", "name", "source_type", "payload"} & set(row.trace)
    payload = row.to_dict()
    assert {
        "id",
        "class_id",
        "cause_ids",
        "severity",
        "title",
        "impact",
        "record_type",
        "record_id",
        "causal_values",
        "trace",
    } <= set(payload)


def test_silent_source_clears_when_delivery_resumes(session, business):
    tenant_id = business.tenant.id
    system, _ = declared_capability(session, tenant_id)
    daily_history(session, tenant_id, system, last=SILENT_AS_OF - timedelta(days=4))
    assert "silent_source" in by_class(session, tenant_id, as_of=SILENT_AS_OF)

    deliver(session, tenant_id, system, "order", SILENT_AS_OF - timedelta(hours=1), 99)

    assert "silent_source" not in by_class(session, tenant_id, as_of=SILENT_AS_OF)


def test_silent_source_orders_longest_silence_first(session, business):
    tenant_id = business.tenant.id
    quiet_system, quiet = declared_capability(session, tenant_id, code="quiet")
    quieter_system, quieter = declared_capability(session, tenant_id, code="quieter")
    daily_history(
        session, tenant_id, quiet_system, last=SILENT_AS_OF - timedelta(days=4)
    )
    daily_history(
        session, tenant_id, quieter_system, last=SILENT_AS_OF - timedelta(days=9)
    )

    first = operational_exceptions(session, tenant_id, as_of=SILENT_AS_OF)
    silent = [row for row in first if row.class_id == "silent_source"]

    assert [row.record_id for row in silent] == [quieter.id, quiet.id]
    second = operational_exceptions(session, tenant_id, as_of=SILENT_AS_OF)
    assert [row.id for row in second] == [row.id for row in first]


def test_silent_source_is_tenant_scoped(session, business):
    tenant_id = business.tenant.id
    system, mine = declared_capability(session, tenant_id)
    daily_history(session, tenant_id, system, last=SILENT_AS_OF - timedelta(days=4))
    other = create_tenant(session, "Nordwind Handel GmbH")
    other_system, theirs = declared_capability(session, other.id)
    # The other tenant is still delivering; its records must not silence mine,
    # and mine must not keep theirs quiet.
    daily_history(
        session, other.id, other_system, last=SILENT_AS_OF - timedelta(hours=2)
    )

    assert records_of(session, tenant_id, "silent_source", as_of=SILENT_AS_OF) == {
        mine.id
    }
    assert records_of(session, other.id, "silent_source", as_of=SILENT_AS_OF) == set()
    assert theirs.id != mine.id


def test_silent_source_constants_are_product_wide(session, business):
    from reality.services import exceptions as exception_service

    # The judgement is made from four product constants and nothing a tenant can
    # set. They live together so that changing one is a deliberate act.
    assert exception_service.SILENT_SOURCE_HISTORY == 20
    assert exception_service.SILENT_SOURCE_MIN_HISTORY == 5
    assert exception_service.SILENT_SOURCE_MULTIPLE == 2
    assert exception_service.SILENT_SOURCE_FLOOR == timedelta(hours=24)


def other_business(session, name):
    """A second tenant shaped like the `business` fixture, without importing it."""
    tenant = create_tenant(session, name)
    return SimpleNamespace(
        tenant=tenant,
        company=create_party(session, tenant.id, name, "company"),
        customer=create_party(session, tenant.id, f"{name} Kunde", "customer"),
        supplier=create_party(session, tenant.id, f"{name} Lieferant", "supplier"),
        item=create_item(session, tenant.id, "BIKE-LIGHT", "Bike Light"),
        location=create_location(session, tenant.id, f"{name} Warehouse"),
    )


def supplier_invoice_with_term(
    session, business, number, document_date, amount="600.00", *, term_code="NET30"
):
    return create_document(
        session,
        business.tenant.id,
        "supplier_invoice",
        number,
        business.supplier.id,
        amount,
        document_date=document_date,
        payment_term_code=term_code,
    )


def overdue_supplier_invoice(session, business, number="ER-9001", amount="600.00"):
    """A posted supplier invoice due 2026-07-31, so overdue at AS_OF."""
    create_payment_term(session, business.tenant.id, "NET30", "Net 30 days", 30)
    invoice = supplier_invoice_with_term(
        session, business, number, "2026-07-01", amount
    )
    entries = post_supplier_invoice(session, business.tenant.id, invoice.id)
    return invoice, entries


def test_overdue_payable(session, business):
    invoice, _ = overdue_supplier_invoice(session, business)

    row = by_class(session, business.tenant.id)["overdue_payable"]

    assert row.id == f"exc__overdue_payable__{invoice.id}"
    assert row.record_type == "document"
    assert row.record_id == invoice.id
    assert row.severity == "high"
    assert row.causal_values["due_date"] == date(2026, 7, 31)
    assert row.causal_values["days_overdue"] == 31
    assert row.causal_values["outstanding_amount"] == Decimal(600)
    assert row.trace["document_id"] == invoice.id


def test_payable_and_receivable_share_one_rule(session, business):
    tenant_id = business.tenant.id
    create_payment_term(session, tenant_id, "NET30", "Net 30 days", 30)
    # Neither invoice carries a term of its own; both parties do. The cascade
    # has to work identically on both sides or the two disagree about "due".
    update_party(
        session,
        tenant_id,
        business.customer.id,
        business.customer.name,
        "customer",
        payment_term_code="NET30",
    )
    update_party(
        session,
        tenant_id,
        business.supplier.id,
        business.supplier.name,
        "supplier",
        payment_term_code="NET30",
    )
    receivable = create_document(
        session,
        tenant_id,
        "sales_invoice",
        "RE-5001",
        business.customer.id,
        "1000.00",
        document_date="2026-07-01",
    )
    payable = supplier_invoice_with_term(
        session, business, "ER-5001", "2026-07-01", term_code=""
    )
    post_sales_invoice(session, tenant_id, receivable.id)
    post_supplier_invoice(session, tenant_id, payable.id)

    rows = by_class(session, tenant_id)

    assert (
        rows["overdue_receivable"].causal_values["due_date"]
        == rows["overdue_payable"].causal_values["due_date"]
        == date(2026, 7, 31)
    )
    assert (
        rows["overdue_receivable"].causal_values["days_overdue"]
        == rows["overdue_payable"].causal_values["days_overdue"]
        == 31
    )


def test_overdue_payable_boundaries(session, business):
    tenant_id = business.tenant.id
    create_payment_term(session, tenant_id, "NET30", "Net 30 days", 30)
    overdue = supplier_invoice_with_term(session, business, "ER-1", "2026-07-01")
    not_yet_due = supplier_invoice_with_term(session, business, "ER-2", "2026-08-30")
    no_date = supplier_invoice_with_term(session, business, "ER-3", "")
    settled = supplier_invoice_with_term(session, business, "ER-4", "2026-07-01")
    reversed_invoice = supplier_invoice_with_term(
        session, business, "ER-5", "2026-07-01"
    )
    receivable = create_document(
        session,
        tenant_id,
        "sales_invoice",
        "RE-1",
        business.customer.id,
        "900.00",
        document_date="2026-07-01",
        payment_term_code="NET30",
    )
    for document in (overdue, not_yet_due, no_date, settled, reversed_invoice):
        post_supplier_invoice(session, tenant_id, document.id)
    post_sales_invoice(session, tenant_id, receivable.id)
    post_supplier_payment(session, tenant_id, settled.id, "600.00")
    group = session.scalar(
        select(LedgerEntry.posting_group_id).where(
            LedgerEntry.tenant_id == tenant_id,
            LedgerEntry.document_id == reversed_invoice.id,
        )
    )
    reverse_ledger_posting_group(
        session, tenant_id, group, reason="Booked against the wrong supplier"
    )

    assert records_of(session, tenant_id, "overdue_payable") == {overdue.id}
    # The sales invoice in the same state stays on its own side.
    assert records_of(session, tenant_id, "overdue_receivable") == {receivable.id}


def test_overdue_payable_orders_longest_first(session, business):
    tenant_id = business.tenant.id
    create_payment_term(session, tenant_id, "NET30", "Net 30 days", 30)
    older = supplier_invoice_with_term(session, business, "ER-8000", "2026-05-01")
    newer = supplier_invoice_with_term(session, business, "ER-8001", "2026-07-01")
    post_supplier_invoice(session, tenant_id, older.id)
    post_supplier_invoice(session, tenant_id, newer.id)

    first = operational_exceptions(session, tenant_id, as_of=AS_OF)
    payables = [row for row in first if row.class_id == "overdue_payable"]

    assert [row.record_id for row in payables] == [older.id, newer.id]
    second = operational_exceptions(session, tenant_id, as_of=AS_OF)
    assert [row.id for row in second] == [row.id for row in first]


def test_overdue_payable_entry_shape(session, business):
    invoice, entries = overdue_supplier_invoice(session, business)
    control = next(entry for entry in entries if entry.account == "accounts_payable")

    row = by_class(session, business.tenant.id)["overdue_payable"]

    assert row.record_type == "document"
    assert row.record_id == invoice.id
    assert row.severity == "high"
    assert row.cause_ids == ()
    assert row.title
    assert row.impact
    assert row.trace["document_id"] == invoice.id
    assert row.trace["ledger_entry_id"] == control.id
    assert not {"number", "party", "gross_amount", "document_date"} & set(row.trace)
    payload = row.to_dict()
    assert {
        "id",
        "class_id",
        "cause_ids",
        "severity",
        "title",
        "impact",
        "record_type",
        "record_id",
        "causal_values",
        "trace",
    } <= set(payload)


def test_overdue_payable_clears_through_payment(session, business):
    tenant_id = business.tenant.id
    invoice, _ = overdue_supplier_invoice(session, business)
    assert "overdue_payable" in by_class(session, tenant_id)

    post_supplier_payment(session, tenant_id, invoice.id, "600.00")

    assert "overdue_payable" not in by_class(session, tenant_id)


def test_overdue_payable_is_tenant_scoped(session, business):
    tenant_id = business.tenant.id
    mine, _ = overdue_supplier_invoice(session, business)
    other = other_business(session, "Nordwind Handel GmbH")
    theirs, _ = overdue_supplier_invoice(session, other, number="ER-7777")

    assert records_of(session, tenant_id, "overdue_payable") == {mine.id}
    assert records_of(session, other.tenant.id, "overdue_payable") == {theirs.id}


# --- Invoice lines and the order lines they bill (spec 076) -----------------


def stock(session, business, quantity=50):
    record_movement(
        session,
        business.tenant.id,
        "opening_stock",
        business.item.id,
        quantity,
        to_location_id=business.location.id,
    )


def order(
    session,
    business,
    *,
    direction="sales",
    number="SO-076",
    quantity="10",
    unit="pcs",
    unit_price="9.00",
):
    """One order line with the commitment that promises its delivery."""
    _, document, lines, commitments = create_manual_order(
        session,
        business.tenant.id,
        direction,
        number,
        business.company.id,
        business.customer.id if direction == "sales" else business.supplier.id,
        business.location.id,
        [
            {
                "item_id": business.item.id,
                "quantity": quantity,
                "unit": unit,
                "unit_price": unit_price,
                "gross_amount": "90.00",
            }
        ],
        "90.00",
        requested_delivery_at=AS_OF + timedelta(days=30),
    )
    return document, lines[0], commitments[0]


def bill(
    session,
    business,
    order_line,
    *,
    direction="sales",
    number="RE-076",
    quantity="4",
    unit="pcs",
    unit_price="9.00",
    document_date="2026-08-20",
):
    document_type = "sales_invoice" if direction == "sales" else "supplier_invoice"
    party = business.customer if direction == "sales" else business.supplier
    document, lines = create_manual_document_with_lines(
        session,
        business.tenant.id,
        document_type,
        number,
        party.id,
        [
            {
                "item_id": business.item.id,
                "quantity": quantity,
                "unit": unit,
                "unit_price": unit_price,
                "gross_amount": "36.00",
                "billed_document_line_id": order_line.id if order_line else None,
            }
        ],
        "36.00",
        document_date=document_date,
    )
    return document, lines[0]


def ship(session, business, commitment, quantity, *, movement_type="shipment"):
    return record_movement(
        session,
        business.tenant.id,
        movement_type,
        business.item.id,
        quantity,
        from_location_id=business.location.id if movement_type == "shipment" else None,
        to_location_id=business.location.id if movement_type != "shipment" else None,
        commitment_id=commitment.id,
        occurred_at=AS_OF - timedelta(days=3),
    )


def test_shipped_not_billed(session, business):
    stock(session, business)
    _, line, commitment = order(session, business)

    # Nothing delivered yet says nothing, whatever has or has not been billed.
    assert "shipped_not_billed" not in by_class(session, business.tenant.id)

    ship(session, business, commitment, 6)
    row = by_class(session, business.tenant.id)["shipped_not_billed"]

    assert row.record_type == "document_line"
    assert row.record_id == line.id
    assert row.causal_values["delivered_quantity"] == Decimal("6.0000")
    assert row.causal_values["billed_quantity"] == Decimal("0.0000")
    assert row.causal_values["unbilled_quantity"] == Decimal("6.0000")

    # Billed for less than was delivered reports the difference, not the whole.
    bill(session, business, line, quantity="4")
    row = by_class(session, business.tenant.id)["shipped_not_billed"]
    assert row.causal_values["billed_quantity"] == Decimal("4.0000")
    assert row.causal_values["unbilled_quantity"] == Decimal("2.0000")

    # Billing the remainder clears it with no manual step.
    bill(session, business, line, number="RE-076-2", quantity="2")
    assert "shipped_not_billed" not in by_class(session, business.tenant.id)


def test_billed_not_received(session, business):
    _, line, commitment = order(
        session, business, direction="purchase", number="PO-076"
    )

    bill(session, business, line, direction="purchase", number="ER-076", quantity="6")
    row = by_class(session, business.tenant.id)["billed_not_received"]

    assert row.record_type == "document_line"
    assert row.record_id == line.id
    assert row.causal_values["billed_quantity"] == Decimal("6.0000")
    assert row.causal_values["received_quantity"] == Decimal("0.0000")
    assert row.causal_values["unreceived_quantity"] == Decimal("6.0000")

    # The goods arrive and the entry goes.
    ship(session, business, commitment, 6, movement_type="receipt")
    assert "billed_not_received" not in by_class(session, business.tenant.id)


def test_received_but_not_yet_billed_is_not_reported(session, business):
    _, line, commitment = order(
        session, business, direction="purchase", number="PO-076b"
    )
    ship(session, business, commitment, 10, movement_type="receipt")

    # A supplier invoice still in the post is the usual sequence, not a finding.
    assert "billed_not_received" not in by_class(session, business.tenant.id)

    # And the silence is the rule speaking, not the class being absent: billing
    # beyond what arrived reports at once on the very same line.
    bill(
        session,
        business,
        line,
        direction="purchase",
        number="ER-076b",
        quantity="12",
    )
    assert "billed_not_received" in by_class(session, business.tenant.id)


def test_invoice_price_differs(session, business):
    stock(session, business)
    _, line, _ = order(session, business, unit_price="9.00")

    bill(session, business, line, unit_price="9.00")
    assert "invoice_price_differs" not in by_class(session, business.tenant.id)

    _, billed = bill(session, business, line, number="RE-076-HIGH", unit_price="11.00")
    row = by_class(session, business.tenant.id)["invoice_price_differs"]

    # The wrong figure is on the invoice, so the invoice line carries the entry.
    assert row.record_id == billed.id
    assert row.causal_values["agreed_unit_price"] == Decimal("9.0000")
    assert row.causal_values["billed_unit_price"] == Decimal("11.0000")
    assert row.causal_values["unit_price_difference"] == Decimal("2.0000")

    # A line that bills no order line has nothing to differ from.
    bill(session, business, None, number="RE-076-FREIGHT", unit_price="99.00")
    assert (
        by_class(session, business.tenant.id)["invoice_price_differs"].record_id
        == billed.id
    )


def test_billing_sums_across_invoices(session, business):
    stock(session, business)
    _, line, commitment = order(session, business)
    ship(session, business, commitment, 10)

    bill(session, business, line, number="RE-A", quantity="4")
    bill(session, business, line, number="RE-B", quantity="3")

    # A consolidated or partial invoice is ordinary: both lines count.
    row = by_class(session, business.tenant.id)["shipped_not_billed"]
    assert row.causal_values["billed_quantity"] == Decimal("7.0000")
    assert row.causal_values["unbilled_quantity"] == Decimal("3.0000")


def test_non_deliverable_lines_are_never_reported(session, business):
    # An order line recorded without a commitment promised no delivery. Freight,
    # a discount or a service is exactly that, and can never be received.
    _, lines = create_manual_document_with_lines(
        session,
        business.tenant.id,
        "purchase_order",
        "PO-FREIGHT",
        business.supplier.id,
        [
            {
                "description": "Freight",
                "quantity": "1",
                "unit": "pcs",
                "unit_price": "25.00",
                "gross_amount": "25.00",
            }
        ],
        "25.00",
    )
    _, billed = bill(
        session,
        business,
        lines[0],
        direction="purchase",
        number="ER-FREIGHT",
        quantity="1",
    )

    # The reference is really there and the order line really promised nothing,
    # so the silence comes from the rule rather than from a missing link.
    assert billed.billed_document_line_id == lines[0].id
    assert (
        session.scalar(
            select(Commitment).where(Commitment.document_line_id == lines[0].id)
        )
        is None
    )
    assert "billed_not_received" not in by_class(session, business.tenant.id)


def test_mismatched_units_are_not_compared(session, business):
    stock(session, business)
    _, line, commitment = order(session, business, unit="box")
    ship(session, business, commitment, 10)

    bill(session, business, line, quantity="4", unit="pcs", unit_price="11.00")

    # Four pieces against ten boxes is not a comparison. Converting would guess.
    current = by_class(session, business.tenant.id)
    assert "shipped_not_billed" not in current
    assert "invoice_price_differs" not in current

    # The same figures in the order line's own unit report immediately, which is
    # what makes the silence above the unit rule and not an empty catalog.
    _, matching_line, matching_commitment = order(
        session, business, number="SO-UNITS-MATCH", unit="box"
    )
    ship(session, business, matching_commitment, 10)
    bill(
        session,
        business,
        matching_line,
        number="RE-UNITS-MATCH",
        quantity="4",
        unit="box",
        unit_price="11.00",
    )
    matched = by_class(session, business.tenant.id)
    assert matched["shipped_not_billed"].record_id == matching_line.id
    assert matched["invoice_price_differs"].causal_values[
        "unit_price_difference"
    ] == Decimal("2.0000")


def test_line_classes_order_longest_first(session, business):
    stock(session, business, 200)
    _, first, first_commitment = order(session, business, number="SO-OLD")
    _, second, second_commitment = order(session, business, number="SO-NEW")
    record_movement(
        session,
        business.tenant.id,
        "shipment",
        business.item.id,
        5,
        from_location_id=business.location.id,
        commitment_id=first_commitment.id,
        occurred_at=AS_OF - timedelta(days=20),
    )
    record_movement(
        session,
        business.tenant.id,
        "shipment",
        business.item.id,
        5,
        from_location_id=business.location.id,
        commitment_id=second_commitment.id,
        occurred_at=AS_OF - timedelta(days=2),
    )

    rows = [
        row.record_id
        for row in operational_exceptions(session, business.tenant.id, as_of=AS_OF)
        if row.class_id == "shipped_not_billed"
    ]

    assert rows == [first.id, second.id]
    repeated = [
        row.record_id
        for row in operational_exceptions(session, business.tenant.id, as_of=AS_OF)
        if row.class_id == "shipped_not_billed"
    ]
    assert repeated == rows


def test_one_delivered_quantity_path(session, business, monkeypatch):
    stock(session, business)
    _, _, commitment = order(session, business)
    ship(session, business, commitment, 6)

    from reality.services import exceptions

    original = exceptions._fulfilled_quantity
    calls: list[str] = []

    def counted(session_, tenant_id, commitment_id, movement_type):
        calls.append(commitment_id)
        return original(session_, tenant_id, commitment_id, movement_type)

    monkeypatch.setattr(exceptions, "_fulfilled_quantity", counted)
    current = by_class(session, business.tenant.id)

    # The commitment classes and the line classes read the delivered quantity
    # through one helper, so a quantity is never counted two ways.
    assert commitment.id in calls
    assert current["shipped_not_billed"].causal_values["delivered_quantity"] == Decimal(
        "6.0000"
    )


def test_line_classes_expose_full_entry_shape(session, business):
    stock(session, business)
    document, line, commitment = order(session, business)
    ship(session, business, commitment, 6)
    purchase_document, purchase_line, _ = order(
        session, business, direction="purchase", number="PO-SHAPE"
    )
    bill(
        session,
        business,
        purchase_line,
        direction="purchase",
        number="ER-SHAPE",
        quantity="3",
    )
    invoice, billed = bill(
        session, business, line, number="RE-SHAPE", unit_price="12.00", quantity="1"
    )

    current = by_class(session, business.tenant.id)
    for class_id in (
        "shipped_not_billed",
        "billed_not_received",
        "invoice_price_differs",
    ):
        row = current[class_id]
        assert row.id == f"exc__{class_id}__{row.record_id}"
        assert row.severity == "high"
        assert row.title and row.impact
        assert row.record_type == "document_line"
        assert row.cause_ids == ()
        assert row.causal_values
        # Traces reach records by opaque identity and restate no business field.
        assert set(row.trace) <= {
            "document_line_id",
            "document_id",
            "billed_document_line_id",
            "billed_document_id",
            "commitment_id",
            "source_record_id",
        }
        assert row.trace["document_line_id"]
        assert row.trace["document_id"]

    assert current["shipped_not_billed"].trace["commitment_id"] == commitment.id
    assert current["invoice_price_differs"].trace["document_id"] == invoice.id
    assert current["invoice_price_differs"].trace["billed_document_line_id"] == line.id
    assert current["billed_not_received"].trace["document_id"] == purchase_document.id
    assert current["shipped_not_billed"].trace["document_id"] == document.id
    assert billed.id == current["invoice_price_differs"].record_id


def test_line_classes_clear_through_reality(session, business):
    stock(session, business)
    _, sales_line, sales_commitment = order(session, business)
    ship(session, business, sales_commitment, 5)
    _, purchase_line, purchase_commitment = order(
        session, business, direction="purchase", number="PO-CLEAR"
    )
    bill(
        session,
        business,
        purchase_line,
        direction="purchase",
        number="ER-CLEAR",
        quantity="5",
    )
    _, billed = bill(
        session,
        business,
        sales_line,
        number="RE-CLEAR",
        quantity="5",
        unit_price="10.00",
    )

    current = by_class(session, business.tenant.id)
    assert "shipped_not_billed" not in current  # billed in full by the same act
    assert "billed_not_received" in current
    assert "invoice_price_differs" in current

    ship(session, business, purchase_commitment, 5, movement_type="receipt")
    billed.unit_price = Decimal("9.0000")
    session.flush()

    cleared = by_class(session, business.tenant.id)
    assert "billed_not_received" not in cleared
    assert "invoice_price_differs" not in cleared


def test_line_classes_are_tenant_scoped(session, business):
    stock(session, business)
    _, _, commitment = order(session, business)
    ship(session, business, commitment, 6)

    foreign = create_tenant(session, "Foreign line tenant")

    assert "shipped_not_billed" in by_class(session, business.tenant.id)
    assert by_class(session, foreign.id) == {}


# --- Two answers the records already hold (spec 078) -----------------------


def customer(session, business, *, limit="1000", currency="EUR", name="Limited GmbH"):
    return create_party(
        session,
        business.tenant.id,
        name,
        "customer",
        credit_limit=limit,
        default_currency=currency,
    )


def invoice(
    session,
    business,
    party,
    number,
    amount,
    *,
    document_type="sales_invoice",
    currency="EUR",
    document_date="2026-08-01",
    post=True,
):
    document = create_document(
        session,
        business.tenant.id,
        document_type,
        number,
        party.id,
        amount,
        currency=currency,
        document_date=document_date,
    )
    if post:
        if document_type == "sales_invoice":
            post_sales_invoice(session, business.tenant.id, document.id)
        else:
            post_supplier_invoice(session, business.tenant.id, document.id)
    return document


def test_credit_limit_exceeded(session, business):
    party = customer(session, business, limit="1000")
    invoice(session, business, party, "RE-CL-1", "1200.00")

    row = by_class(session, business.tenant.id)["credit_limit_exceeded"]

    assert row.record_type == "party"
    assert row.record_id == party.id
    assert row.causal_values["credit_limit"] == Decimal("1000.0000")
    assert row.causal_values["outstanding_amount"] == Decimal("1200.0000")
    assert row.causal_values["excess_amount"] == Decimal("200.0000")


def test_an_amount_equal_to_the_limit_is_allowed(session, business):
    party = customer(session, business, limit="1000")
    invoice(session, business, party, "RE-CL-EQ", "1000.00")

    # The agreed number is what the company said it would carry.
    assert "credit_limit_exceeded" not in by_class(session, business.tenant.id)

    # One cent past it is not, which is what makes the silence above a rule.
    invoice(session, business, party, "RE-CL-EQ-2", "0.01")
    assert "credit_limit_exceeded" in by_class(session, business.tenant.id)


def test_a_party_without_a_limit_is_never_reported(session, business):
    party = customer(session, business, limit="0")
    invoice(session, business, party, "RE-CL-NONE", "9999.00")

    # Zero means no limit is recorded, not a limit of nothing.
    assert "credit_limit_exceeded" not in by_class(session, business.tenant.id)

    # Recording one reports the same party on the very next read.
    party.credit_limit = Decimal("100.0000")
    session.flush()
    assert "credit_limit_exceeded" in by_class(session, business.tenant.id)


def test_credit_exposure_uses_the_shared_open_items(session, business):
    from reality.services.core import aging_register

    party = customer(session, business, limit="500")
    invoice(session, business, party, "RE-CL-SHARED", "800.00")

    row = by_class(session, business.tenant.id)["credit_limit_exceeded"]
    register = [
        entry
        for entry in aging_register(session, business.tenant.id, as_of=AS_OF)
        if entry["document"].party_id == party.id
    ]

    # One number, one authority: what an operator reads here is what the aging
    # register shows, never a second sum over postings.
    assert row.causal_values["outstanding_amount"] == sum(
        entry["open"] for entry in register
    )


def test_only_the_partys_own_currency_counts(session, business):
    party = customer(session, business, limit="500", currency="EUR")
    invoice(session, business, party, "RE-CL-USD", "900.00", currency="USD")

    # Nine hundred dollars against a limit in euro is not a comparison.
    assert "credit_limit_exceeded" not in by_class(session, business.tenant.id)

    # The same amount in the party's own currency reports immediately.
    invoice(session, business, party, "RE-CL-EUR", "900.00", currency="EUR")
    row = by_class(session, business.tenant.id)["credit_limit_exceeded"]
    assert row.causal_values["outstanding_amount"] == Decimal("900.0000")
    assert row.causal_values["currency"] == "EUR"


def test_a_settled_invoice_clears_the_exposure(session, business):
    party = customer(session, business, limit="1000")
    document = invoice(session, business, party, "RE-CL-PAY", "1500.00")
    assert "credit_limit_exceeded" in by_class(session, business.tenant.id)

    post_customer_payment(session, business.tenant.id, document.id, "600.00")

    assert "credit_limit_exceeded" not in by_class(session, business.tenant.id)


def test_duplicate_supplier_invoice(session, business):
    first = invoice(
        session,
        business,
        business.supplier,
        "ER-4711",
        "300.00",
        document_type="supplier_invoice",
        document_date="2026-08-01",
    )
    assert "duplicate_supplier_invoice" not in by_class(session, business.tenant.id)

    second = invoice(
        session,
        business,
        business.supplier,
        "ER-4711",
        "300.00",
        document_type="supplier_invoice",
        document_date="2026-08-05",
    )
    row = by_class(session, business.tenant.id)["duplicate_supplier_invoice"]

    assert row.record_type == "document"
    assert row.record_id == second.id
    assert row.causal_values["number"] == "ER-4711"
    assert row.trace["original_document_id"] == first.id

    # A third names the first as well, so two entries stand.
    invoice(
        session,
        business,
        business.supplier,
        "ER-4711",
        "300.00",
        document_type="supplier_invoice",
        document_date="2026-08-09",
    )
    duplicates = [
        entry
        for entry in operational_exceptions(session, business.tenant.id, as_of=AS_OF)
        if entry.class_id == "duplicate_supplier_invoice"
    ]
    assert len(duplicates) == 2
    assert {entry.trace["original_document_id"] for entry in duplicates} == {first.id}


def test_the_same_number_from_two_suppliers_is_not_a_duplicate(session, business):
    other = create_party(session, business.tenant.id, "Second Parts GmbH", "supplier")
    invoice(
        session,
        business,
        business.supplier,
        "ER-9000",
        "100.00",
        document_type="supplier_invoice",
    )
    invoice(
        session,
        business,
        other,
        "ER-9000",
        "100.00",
        document_type="supplier_invoice",
        document_date="2026-08-04",
    )

    # A number is only unique inside the supplier that issued it.
    assert "duplicate_supplier_invoice" not in by_class(session, business.tenant.id)

    # The same supplier twice reports at once, which is what makes that a rule.
    invoice(
        session,
        business,
        other,
        "ER-9000",
        "100.00",
        document_type="supplier_invoice",
        document_date="2026-08-07",
    )
    assert "duplicate_supplier_invoice" in by_class(session, business.tenant.id)


def test_numbers_are_matched_without_case_or_padding(session, business):
    invoice(
        session,
        business,
        business.supplier,
        "ER-100",
        "50.00",
        document_type="supplier_invoice",
    )
    invoice(
        session,
        business,
        business.supplier,
        " er-100 ",
        "50.00",
        document_type="supplier_invoice",
        document_date="2026-08-06",
    )

    assert "duplicate_supplier_invoice" in by_class(session, business.tenant.id)


def test_unnumbered_invoices_are_neither_reported_nor_matched(session, business):
    for index, day in enumerate(("2026-08-02", "2026-08-03"), start=1):
        document = create_document(
            session,
            business.tenant.id,
            "supplier_invoice",
            f"ER-BLANK-{index}",
            business.supplier.id,
            "40.00",
            document_date=day,
        )
        document.number = "   "
        session.flush()
        post_supplier_invoice(session, business.tenant.id, document.id)

    # An empty string is not a number two documents can share.
    assert "duplicate_supplier_invoice" not in by_class(session, business.tenant.id)

    # Two that do share a number report, so the silence above is the rule.
    invoice(
        session,
        business,
        business.supplier,
        "ER-REAL",
        "40.00",
        document_type="supplier_invoice",
    )
    invoice(
        session,
        business,
        business.supplier,
        "ER-REAL",
        "40.00",
        document_type="supplier_invoice",
        document_date="2026-08-08",
    )
    assert "duplicate_supplier_invoice" in by_class(session, business.tenant.id)


def test_a_reversed_invoice_is_not_a_duplicate(session, business):
    first = invoice(
        session,
        business,
        business.supplier,
        "ER-REV",
        "200.00",
        document_type="supplier_invoice",
    )
    second = invoice(
        session,
        business,
        business.supplier,
        "ER-REV",
        "200.00",
        document_type="supplier_invoice",
        document_date="2026-08-06",
    )
    # While the first stands, the reissue is a duplicate.
    assert "duplicate_supplier_invoice" in by_class(session, business.tenant.id)

    control = core._settlement_control_entry(session, business.tenant.id, first.id)
    reverse_ledger_posting_group(
        session,
        business.tenant.id,
        control.posting_group_id,
        reason="recorded in error",
    )

    # Withdrawn, it cannot be paid twice, and a corrected reissue under the same
    # number is ordinary rather than a finding.
    assert "duplicate_supplier_invoice" not in by_class(session, business.tenant.id)
    assert second.id


def test_the_original_is_the_same_document_every_read(session, business):
    for index, day in enumerate(("2026-08-01", "2026-08-01", "2026-08-01"), start=1):
        invoice(
            session,
            business,
            business.supplier,
            "ER-SAMEDAY",
            "70.00",
            document_type="supplier_invoice",
            document_date=day,
            post=index == 1,
        )

    def read():
        return [
            (entry.record_id, entry.trace["original_document_id"])
            for entry in operational_exceptions(
                session, business.tenant.id, as_of=AS_OF
            )
            if entry.class_id == "duplicate_supplier_invoice"
        ]

    first_read = read()

    # Three documents dated the same day still have one unambiguous original.
    assert len(first_read) == 2
    assert len({original for _, original in first_read}) == 1
    assert read() == first_read


def test_both_record_classes_expose_full_entry_shape(session, business):
    party = customer(session, business, limit="100")
    invoice(session, business, party, "RE-SHAPE", "400.00")
    first = invoice(
        session,
        business,
        business.supplier,
        "ER-SHAPE",
        "80.00",
        document_type="supplier_invoice",
    )
    second = invoice(
        session,
        business,
        business.supplier,
        "ER-SHAPE",
        "80.00",
        document_type="supplier_invoice",
        document_date="2026-08-07",
    )

    current = by_class(session, business.tenant.id)
    for class_id, record_type, record_id in (
        ("credit_limit_exceeded", "party", party.id),
        ("duplicate_supplier_invoice", "document", second.id),
    ):
        row = current[class_id]
        assert row.id == f"exc__{class_id}__{record_id}"
        assert row.record_type == record_type
        assert row.record_id == record_id
        assert row.severity == "high"
        assert row.title and row.impact
        assert row.cause_ids == ()
        assert row.causal_values
        assert set(row.trace) <= {
            "party_id",
            "document_id",
            "document_ids",
            "original_document_id",
            "original_source_record_id",
            "source_record_id",
        }

    assert current["credit_limit_exceeded"].trace["party_id"] == party.id
    assert current["duplicate_supplier_invoice"].trace["document_id"] == second.id
    assert (
        current["duplicate_supplier_invoice"].trace["original_document_id"] == first.id
    )


def test_record_classes_are_tenant_scoped(session, business):
    party = customer(session, business, limit="10")
    invoice(session, business, party, "RE-TENANT", "500.00")
    invoice(
        session,
        business,
        business.supplier,
        "ER-TENANT",
        "60.00",
        document_type="supplier_invoice",
    )
    invoice(
        session,
        business,
        business.supplier,
        "ER-TENANT",
        "60.00",
        document_type="supplier_invoice",
        document_date="2026-08-06",
    )
    foreign = create_tenant(session, "Foreign record tenant")

    current = by_class(session, business.tenant.id)
    assert "credit_limit_exceeded" in current
    assert "duplicate_supplier_invoice" in current
    assert by_class(session, foreign.id) == {}


# --- Goods coming back (spec 079) ------------------------------------------


def send_back(session, business, commitment, quantity, *, at=None):
    return record_movement(
        session,
        business.tenant.id,
        "return",
        business.item.id,
        quantity,
        to_location_id=business.location.id,
        commitment_id=commitment.id,
        occurred_at=at or AS_OF - timedelta(days=1),
    )


def credit(
    session,
    business,
    order_line,
    *,
    number="GS-079",
    quantity="4",
    unit="pcs",
):
    document, lines = create_manual_document_with_lines(
        session,
        business.tenant.id,
        "credit_note",
        number,
        business.customer.id,
        [
            {
                "item_id": business.item.id,
                "quantity": quantity,
                "unit": unit,
                "unit_price": "9.00",
                "gross_amount": "36.00",
                "billed_document_line_id": order_line.id,
            }
        ],
        "36.00",
        document_date="2026-08-25",
    )
    return document, lines[0]


def test_returned_goods_are_not_reported_as_unbilled(session, business):
    stock(session, business)
    _, _, commitment = order(session, business, number="SO-RET-1")
    ship(session, business, commitment, 10)
    assert by_class(session, business.tenant.id)["shipped_not_billed"].causal_values[
        "unbilled_quantity"
    ] == Decimal("10.0000")

    # Part of it comes back: only what the customer kept is still unbilled.
    send_back(session, business, commitment, 4)
    assert by_class(session, business.tenant.id)["shipped_not_billed"].causal_values[
        "unbilled_quantity"
    ] == Decimal("6.0000")

    # All of it comes back: nobody should be invoiced for anything.
    send_back(session, business, commitment, 6)
    assert "shipped_not_billed" not in by_class(session, business.tenant.id)


def test_returned_not_credited(session, business):
    stock(session, business)
    _, line, commitment = order(session, business, number="SO-RET-2")
    ship(session, business, commitment, 10)
    bill(session, business, line, number="RE-RET-2", quantity="10")

    # Nothing back yet says nothing.
    assert "returned_not_credited" not in by_class(session, business.tenant.id)

    send_back(session, business, commitment, 6)
    row = by_class(session, business.tenant.id)["returned_not_credited"]

    assert row.record_type == "document_line"
    assert row.record_id == line.id
    assert row.causal_values["returned_quantity"] == Decimal("6.0000")
    assert row.causal_values["credited_quantity"] == Decimal("0.0000")
    assert row.causal_values["uncredited_quantity"] == Decimal("6.0000")

    credit(session, business, line, quantity="4")
    assert by_class(session, business.tenant.id)["returned_not_credited"].causal_values[
        "uncredited_quantity"
    ] == Decimal("2.0000")

    credit(session, business, line, number="GS-079-2", quantity="2")
    assert "returned_not_credited" not in by_class(session, business.tenant.id)


def test_goods_that_were_never_billed_need_no_credit(session, business):
    stock(session, business)
    _, line, commitment = order(session, business, number="SO-RET-3")
    ship(session, business, commitment, 10)
    send_back(session, business, commitment, 5)

    # Nobody was charged for these goods, so nothing is owed back.
    assert "returned_not_credited" not in by_class(session, business.tenant.id)

    # Bill them and the same return is owed a credit at once.
    bill(session, business, line, number="RE-RET-3", quantity="10")
    assert by_class(session, business.tenant.id)["returned_not_credited"].causal_values[
        "uncredited_quantity"
    ] == Decimal("5.0000")


def test_credited_not_returned(session, business):
    stock(session, business)
    _, line, commitment = order(session, business, number="SO-RET-4")
    ship(session, business, commitment, 10)
    bill(session, business, line, number="RE-RET-4", quantity="10")
    credit(session, business, line, quantity="6")

    # A credit with nothing coming back is a decision, not a discrepancy.
    assert "credited_not_returned" not in by_class(session, business.tenant.id)

    send_back(session, business, commitment, 2)
    row = by_class(session, business.tenant.id)["credited_not_returned"]

    assert row.record_id == line.id
    assert row.causal_values["credited_quantity"] == Decimal("6.0000")
    assert row.causal_values["returned_quantity"] == Decimal("2.0000")
    assert row.causal_values["unreturned_quantity"] == Decimal("4.0000")

    # The outstanding goods arrive and it clears.
    send_back(session, business, commitment, 4)
    assert "credited_not_returned" not in by_class(session, business.tenant.id)


def test_one_line_produces_at_most_one_return_entry(session, business):
    stock(session, business, 200)
    _, short_line, short_commitment = order(session, business, number="SO-RET-5")
    ship(session, business, short_commitment, 10)
    bill(session, business, short_line, number="RE-RET-5", quantity="10")
    send_back(session, business, short_commitment, 8)
    credit(session, business, short_line, number="GS-RET-5", quantity="3")

    _, long_line, long_commitment = order(session, business, number="SO-RET-6")
    ship(session, business, long_commitment, 10)
    bill(session, business, long_line, number="RE-RET-6", quantity="10")
    send_back(session, business, long_commitment, 2)
    credit(session, business, long_line, number="GS-RET-6", quantity="7")

    rows = [
        entry
        for entry in operational_exceptions(session, business.tenant.id, as_of=AS_OF)
        if entry.class_id in {"returned_not_credited", "credited_not_returned"}
    ]

    # Opposite directions of one difference: neither line can be in both.
    by_line: dict[str, list[str]] = {}
    for entry in rows:
        by_line.setdefault(entry.record_id, []).append(entry.class_id)
    assert by_line[short_line.id] == ["returned_not_credited"]
    assert by_line[long_line.id] == ["credited_not_returned"]


def test_a_voided_movement_stops_counting(session, business):
    from reality.services.core import correct_movement

    stock(session, business)
    _, _, commitment = order(session, business, number="SO-RET-7")
    shipment = ship(session, business, commitment, 10)
    assert "shipped_not_billed" in by_class(session, business.tenant.id)

    correct_movement(
        session,
        business.tenant.id,
        shipment.id,
        reason="Recorded against the wrong order",
    )

    # A shipment recorded in error never happened, so nothing is unbilled.
    assert "shipped_not_billed" not in by_class(session, business.tenant.id)


def test_crediting_sums_across_credit_notes(session, business):
    stock(session, business)
    _, line, commitment = order(session, business, number="SO-RET-8")
    ship(session, business, commitment, 10)
    bill(session, business, line, number="RE-RET-8", quantity="10")
    send_back(session, business, commitment, 9)

    credit(session, business, line, number="GS-A", quantity="4")
    credit(session, business, line, number="GS-B", quantity="3")

    assert by_class(session, business.tenant.id)["returned_not_credited"].causal_values[
        "credited_quantity"
    ] == Decimal("7.0000")


def test_return_classes_ignore_mismatched_units(session, business):
    stock(session, business)
    _, line, commitment = order(session, business, number="SO-RET-9", unit="box")
    ship(session, business, commitment, 10)
    bill(session, business, line, number="RE-RET-9", quantity="10", unit="box")
    send_back(session, business, commitment, 5)
    credit(session, business, line, number="GS-UNITS", quantity="2", unit="pcs")

    # Two pieces against five boxes is not a comparison.
    assert "returned_not_credited" not in by_class(session, business.tenant.id)

    # The same figures in the order line's own unit report immediately.
    _, matching_line, matching_commitment = order(
        session, business, number="SO-RET-10", unit="box"
    )
    ship(session, business, matching_commitment, 10)
    bill(
        session, business, matching_line, number="RE-RET-10", quantity="10", unit="box"
    )
    send_back(session, business, matching_commitment, 5)
    credit(
        session, business, matching_line, number="GS-MATCH", quantity="2", unit="box"
    )
    assert (
        by_class(session, business.tenant.id)["returned_not_credited"].record_id
        == matching_line.id
    )


def test_one_returned_quantity_path(session, business, monkeypatch):
    stock(session, business)
    _, line, commitment = order(session, business, number="SO-RET-11")
    ship(session, business, commitment, 10)
    bill(session, business, line, number="RE-RET-11", quantity="10")
    send_back(session, business, commitment, 5)

    from reality.services import exceptions

    original = exceptions._fulfilled_quantity
    seen: list[str] = []

    def counted(session_, tenant_id, commitment_id, movement_type):
        seen.append(movement_type)
        return original(session_, tenant_id, commitment_id, movement_type)

    monkeypatch.setattr(exceptions, "_fulfilled_quantity", counted)
    row = by_class(session, business.tenant.id)["returned_not_credited"]

    # Shipments and returns come from one helper, never a second count.
    assert "return" in seen
    assert "shipment" in seen
    assert row.causal_values["returned_quantity"] == Decimal("5.0000")


def test_return_classes_expose_full_entry_shape(session, business):
    stock(session, business)
    document, line, commitment = order(session, business, number="SO-RET-12")
    ship(session, business, commitment, 10)
    bill(session, business, line, number="RE-RET-12", quantity="10")
    send_back(session, business, commitment, 6)

    row = by_class(session, business.tenant.id)["returned_not_credited"]

    assert row.id == f"exc__returned_not_credited__{line.id}"
    assert row.severity == "high"
    assert row.title and row.impact
    assert row.record_type == "document_line"
    assert row.cause_ids == ()
    assert set(row.trace) <= {
        "document_line_id",
        "document_id",
        "commitment_id",
        "source_record_id",
    }
    assert row.trace["commitment_id"] == commitment.id
    assert row.trace["document_id"] == document.id


def test_return_classes_clear_through_reality(session, business):
    stock(session, business)
    _, line, commitment = order(session, business, number="SO-RET-13")
    ship(session, business, commitment, 10)
    bill(session, business, line, number="RE-RET-13", quantity="10")
    send_back(session, business, commitment, 5)
    assert "returned_not_credited" in by_class(session, business.tenant.id)

    credit(session, business, line, number="GS-CLEAR", quantity="5")

    assert "returned_not_credited" not in by_class(session, business.tenant.id)
    assert "credited_not_returned" not in by_class(session, business.tenant.id)


def test_return_classes_order_longest_first(session, business):
    stock(session, business, 200)
    _, first, first_commitment = order(session, business, number="SO-RET-OLD")
    _, second, second_commitment = order(session, business, number="SO-RET-NEW")
    for line, commitment, number in (
        (first, first_commitment, "RE-RET-OLD"),
        (second, second_commitment, "RE-RET-NEW"),
    ):
        ship(session, business, commitment, 10)
        bill(session, business, line, number=number, quantity="10")
    send_back(session, business, first_commitment, 5, at=AS_OF - timedelta(days=20))
    send_back(session, business, second_commitment, 5, at=AS_OF - timedelta(days=2))

    rows = [
        entry.record_id
        for entry in operational_exceptions(session, business.tenant.id, as_of=AS_OF)
        if entry.class_id == "returned_not_credited"
    ]

    assert rows == [first.id, second.id]
    assert rows == [
        entry.record_id
        for entry in operational_exceptions(session, business.tenant.id, as_of=AS_OF)
        if entry.class_id == "returned_not_credited"
    ]


def test_return_classes_are_tenant_scoped(session, business):
    stock(session, business)
    _, line, commitment = order(session, business, number="SO-RET-14")
    ship(session, business, commitment, 10)
    bill(session, business, line, number="RE-RET-14", quantity="10")
    send_back(session, business, commitment, 5)
    foreign = create_tenant(session, "Foreign returns tenant")

    assert "returned_not_credited" in by_class(session, business.tenant.id)
    assert by_class(session, foreign.id) == {}


# --- Long by this company's own standard (spec 080) ------------------------


def undated_promise(session, business, *, age_days, due_at=None, quantity=5):
    """One customer delivery promise created some days ago."""
    commitment = create_commitment(
        session,
        business.tenant.id,
        "customer_delivery",
        business.company.id,
        business.customer.id,
        business.item.id,
        business.location.id,
        quantity,
        due_at,
    )
    commitment.created_at = AS_OF - timedelta(days=age_days)
    session.flush()
    return commitment


def fulfil(session, business, commitment, *, after_days, quantity=5):
    """Ship the promise in full, that many days after it was created."""
    return record_movement(
        session,
        business.tenant.id,
        "shipment",
        business.item.id,
        quantity,
        from_location_id=business.location.id,
        commitment_id=commitment.id,
        occurred_at=commitment.created_at + timedelta(days=after_days),
    )


def history(session, business, *, lag_days=1, cases=6, quantity=5):
    """A tenant that normally ships in `lag_days`."""
    stock(session, business, cases * quantity + 100)
    for index in range(cases):
        commitment = undated_promise(
            session, business, age_days=90 - index, quantity=quantity
        )
        fulfil(session, business, commitment, after_days=lag_days, quantity=quantity)


def thresholds(session, business):
    from reality.services import exceptions

    return (
        exceptions._fulfilment_threshold(session, business.tenant.id),
        exceptions._billing_threshold(session, business.tenant.id),
    )


def test_the_fulfilment_norm_describes_this_tenant(session, business):
    history(session, business, lag_days=2, cases=6)

    fulfilment, _ = thresholds(session, business)

    # Three times a two-day median, which clears the seven-day floor.
    assert fulfilment == timedelta(days=6) or fulfilment == timedelta(days=7)
    assert fulfilment >= timedelta(days=6)


def test_a_young_tenant_is_never_judged(session, business):
    history(session, business, lag_days=1, cases=4)
    stalled = undated_promise(session, business, age_days=200)

    # Four cases is not a norm, so nothing is claimed and nothing reported.
    fulfilment, _ = thresholds(session, business)
    assert fulfilment is None
    assert "order_stalled" not in by_class(session, business.tenant.id)

    # The fifth completed case makes a norm, and the same promise reports.
    extra = undated_promise(session, business, age_days=80)
    fulfil(session, business, extra, after_days=1)
    assert thresholds(session, business)[0] is not None
    assert by_class(session, business.tenant.id)["order_stalled"].record_id == (
        stalled.id
    )


def test_one_slow_case_does_not_move_the_norm(session, business):
    history(session, business, lag_days=1, cases=6)
    before, _ = thresholds(session, business)

    # One order that took a year leaves the median where it was.
    outlier = undated_promise(session, business, age_days=400)
    fulfil(session, business, outlier, after_days=365)
    assert thresholds(session, business)[0] == before

    # Shifting the whole business does move it, which is the point.
    history(session, business, lag_days=30, cases=8)
    assert thresholds(session, business)[0] > before


def test_a_backdated_shipment_cannot_drag_the_norm(session, business):
    stock(session, business, 200)
    for index in range(6):
        commitment = undated_promise(session, business, age_days=50 - index)
        record_movement(
            session,
            business.tenant.id,
            "shipment",
            business.item.id,
            5,
            from_location_id=business.location.id,
            commitment_id=commitment.id,
            # Recorded as having happened before the promise existed.
            occurred_at=commitment.created_at - timedelta(days=3),
        )

    fulfilment, _ = thresholds(session, business)

    # A negative lag counts as none, so the floor is what is left.
    assert fulfilment == timedelta(days=7)


def test_norms_are_learned_per_tenant(session, business):
    history(session, business, lag_days=1, cases=6)
    fast, _ = thresholds(session, business)

    other = create_tenant(session, "Slow neighbour")
    slow_company = create_party(session, other.id, "Slow GmbH", "company")
    slow_customer = create_party(session, other.id, "Slow Customer GmbH", "customer")
    slow_item = create_item(session, other.id, "SLOW-1", "Slow Item")
    slow_location = create_location(session, other.id, "Slow Warehouse")
    record_movement(
        session,
        other.id,
        "opening_stock",
        slow_item.id,
        200,
        to_location_id=slow_location.id,
    )
    for index in range(6):
        commitment = create_commitment(
            session,
            other.id,
            "customer_delivery",
            slow_company.id,
            slow_customer.id,
            slow_item.id,
            slow_location.id,
            5,
            None,
        )
        commitment.created_at = AS_OF - timedelta(days=200 - index)
        session.flush()
        record_movement(
            session,
            other.id,
            "shipment",
            slow_item.id,
            5,
            from_location_id=slow_location.id,
            commitment_id=commitment.id,
            occurred_at=commitment.created_at + timedelta(days=60),
        )

    from reality.services import exceptions

    # A neighbour that takes two months never raises this tenant's bar.
    assert exceptions._fulfilment_threshold(session, business.tenant.id) == fast
    assert exceptions._fulfilment_threshold(session, other.id) > fast


def test_order_stalled(session, business):
    history(session, business, lag_days=1, cases=6)
    stalled = undated_promise(session, business, age_days=60)
    recent = undated_promise(session, business, age_days=1)

    current = by_class(session, business.tenant.id)
    row = current["order_stalled"]

    assert row.record_type == "commitment"
    assert row.record_id == stalled.id
    assert row.causal_values["standing_for_days"] == 60
    assert row.causal_values["threshold_days"] == 7
    assert recent.id != row.record_id

    # Shipping it clears the entry with no manual step.
    fulfil(session, business, stalled, after_days=60)
    assert "order_stalled" not in by_class(session, business.tenant.id)


def test_a_dated_promise_is_left_to_the_overdue_class(session, business):
    history(session, business, lag_days=1, cases=6)
    dated = undated_promise(
        session, business, age_days=60, due_at=AS_OF - timedelta(days=30)
    )

    current = by_class(session, business.tenant.id)

    # A promise with a date belongs to the overdue class, and to it alone.
    assert "order_stalled" not in current
    assert current["overdue_outgoing_customer_commitment"].record_id == dated.id

    # The same promise without a date is this class's business.
    undated = undated_promise(session, business, age_days=60)
    assert by_class(session, business.tenant.id)["order_stalled"].record_id == (
        undated.id
    )


def test_a_cancelled_promise_is_neither_reported_nor_learned_from(session, business):
    from reality.services.core import cancel_commitment

    history(session, business, lag_days=1, cases=6)
    before, _ = thresholds(session, business)
    abandoned = undated_promise(session, business, age_days=90)
    cancel_commitment(session, business.tenant.id, abandoned.id)

    # Nobody is waiting for it, and it teaches the norm nothing.
    assert "order_stalled" not in by_class(session, business.tenant.id)
    assert thresholds(session, business)[0] == before

    # The same promise standing rather than cancelled is reported.
    standing = undated_promise(session, business, age_days=90)
    assert by_class(session, business.tenant.id)["order_stalled"].record_id == (
        standing.id
    )


def test_a_fast_tenant_is_not_reported_at_once(session, business):
    stock(session, business, 200)
    for index in range(6):
        commitment = undated_promise(session, business, age_days=30 - index)
        record_movement(
            session,
            business.tenant.id,
            "shipment",
            business.item.id,
            5,
            from_location_id=business.location.id,
            commitment_id=commitment.id,
            occurred_at=commitment.created_at + timedelta(hours=1),
        )
    quick = undated_promise(session, business, age_days=3)

    # Three times an hour is not a threshold anybody would act on. The floor is.
    assert "order_stalled" not in by_class(session, business.tenant.id)

    # Past the floor it reports, which is what makes the silence a rule.
    quick.created_at = AS_OF - timedelta(days=8)
    session.flush()
    assert by_class(session, business.tenant.id)["order_stalled"].record_id == quick.id


def test_lag_classes_order_longest_first(session, business):
    history(session, business, lag_days=1, cases=6)
    older = undated_promise(session, business, age_days=90)
    newer = undated_promise(session, business, age_days=30)

    rows = [
        row.record_id
        for row in operational_exceptions(session, business.tenant.id, as_of=AS_OF)
        if row.class_id == "order_stalled"
    ]

    assert rows == [older.id, newer.id]
    assert rows == [
        row.record_id
        for row in operational_exceptions(session, business.tenant.id, as_of=AS_OF)
        if row.class_id == "order_stalled"
    ]


def test_lag_classes_expose_full_entry_shape(session, business):
    history(session, business, lag_days=1, cases=6)
    stalled = undated_promise(session, business, age_days=60)

    row = by_class(session, business.tenant.id)["order_stalled"]

    assert row.id == f"exc__order_stalled__{stalled.id}"
    assert row.severity == "high"
    assert row.title and row.impact
    assert row.cause_ids == ()
    assert row.causal_values["norm_days"] is not None
    assert set(row.trace) <= {
        "commitment_id",
        "document_line_id",
        "document_id",
        "document_number",
        "customer_reference",
        "source_record_id",
        "source_system",
        "source_external_id",
        # A presence flag the commitment classes already carry, not a business
        # field: it says whether a source exists, never what it said.
        "source_absent",
    }
    assert row.trace["commitment_id"] == stalled.id


def receive(session, business, commitment, quantity, *, days_ago, unit="pcs"):
    return record_movement(
        session,
        business.tenant.id,
        "receipt",
        business.item.id,
        quantity,
        to_location_id=business.location.id,
        commitment_id=commitment.id,
        occurred_at=AS_OF - timedelta(days=days_ago),
    )


def purchase(session, business, number, *, unit="pcs", quantity="10"):
    _, line, commitment = order(
        session,
        business,
        direction="purchase",
        number=number,
        unit=unit,
        quantity=quantity,
    )
    return line, commitment


def billing_history(session, business, *, lag_days=3, cases=6):
    """A tenant whose suppliers normally invoice `lag_days` after delivery."""
    for index in range(cases):
        received_days_ago = 200 - index * 5
        line, commitment = purchase(session, business, f"PO-NORM-{index}")
        receive(session, business, commitment, 10, days_ago=received_days_ago)
        invoiced = (AS_OF - timedelta(days=received_days_ago - lag_days)).date()
        bill(
            session,
            business,
            line,
            direction="purchase",
            number=f"ER-NORM-{index}",
            quantity="10",
            document_date=invoiced.isoformat(),
        )


def test_the_billing_norm_describes_this_tenant(session, business):
    billing_history(session, business, lag_days=3, cases=6)

    _, billing = thresholds(session, business)

    # Three times a three-day median is nine days, under the fortnight floor.
    assert billing == timedelta(days=14)


def test_receipt_unbilled(session, business):
    billing_history(session, business, lag_days=3, cases=6)
    line, commitment = purchase(session, business, "PO-UNBILLED")
    receive(session, business, commitment, 10, days_ago=60)

    row = by_class(session, business.tenant.id)["receipt_unbilled"]

    assert row.record_type == "document_line"
    assert row.record_id == line.id
    assert row.causal_values["received_quantity"] == Decimal("10.0000")
    assert row.causal_values["billed_quantity"] == Decimal("0.0000")
    assert row.causal_values["standing_for_days"] == 60
    assert row.causal_values["threshold_days"] == 14

    # A receipt inside the norm says nothing.
    recent_line, recent_commitment = purchase(session, business, "PO-RECENT")
    receive(session, business, recent_commitment, 10, days_ago=2)
    assert by_class(session, business.tenant.id)["receipt_unbilled"].record_id == (
        line.id
    )

    # Billing it clears the entry with no manual step.
    bill(
        session,
        business,
        line,
        direction="purchase",
        number="ER-UNBILLED",
        quantity="10",
    )
    assert "receipt_unbilled" not in by_class(session, business.tenant.id)
    assert recent_line.id


def test_lag_classes_ignore_mismatched_units(session, business):
    billing_history(session, business, lag_days=3, cases=6)
    line, commitment = purchase(session, business, "PO-UNITS", unit="box")
    receive(session, business, commitment, 10, days_ago=60)
    bill(
        session,
        business,
        line,
        direction="purchase",
        number="ER-UNITS",
        quantity="2",
        unit="pcs",
    )

    # Two pieces against ten boxes is not a comparison.
    assert "receipt_unbilled" not in by_class(session, business.tenant.id)

    # The same figures in the order line's own unit report immediately.
    matching, matching_commitment = purchase(
        session, business, "PO-UNITS-MATCH", unit="box"
    )
    receive(session, business, matching_commitment, 10, days_ago=60)
    bill(
        session,
        business,
        matching,
        direction="purchase",
        number="ER-UNITS-MATCH",
        quantity="2",
        unit="box",
    )
    assert by_class(session, business.tenant.id)["receipt_unbilled"].record_id == (
        matching.id
    )


def test_lag_classes_clear_through_reality(session, business):
    history(session, business, lag_days=1, cases=6)
    billing_history(session, business, lag_days=3, cases=6)
    stalled = undated_promise(session, business, age_days=60)
    line, commitment = purchase(session, business, "PO-CLEAR")
    receive(session, business, commitment, 10, days_ago=60)

    current = by_class(session, business.tenant.id)
    assert "order_stalled" in current
    assert "receipt_unbilled" in current

    fulfil(session, business, stalled, after_days=60)
    bill(
        session,
        business,
        line,
        direction="purchase",
        number="ER-CLEAR-LAG",
        quantity="10",
    )

    cleared = by_class(session, business.tenant.id)
    assert "order_stalled" not in cleared
    assert "receipt_unbilled" not in cleared


def test_lag_classes_use_the_shared_movement_quantity(session, business):
    from reality.services.core import correct_movement

    billing_history(session, business, lag_days=3, cases=6)
    line, commitment = purchase(session, business, "PO-VOID")
    receipt = receive(session, business, commitment, 10, days_ago=60)
    assert "receipt_unbilled" in by_class(session, business.tenant.id)

    correct_movement(
        session,
        business.tenant.id,
        receipt.id,
        reason="Booked against the wrong order",
    )

    # A voided receipt never arrived, so there is nothing to invoice.
    assert "receipt_unbilled" not in by_class(session, business.tenant.id)
    assert line.id


# --- What happened to the goods (spec 081) ---------------------------------


def area(session, business):
    return create_location(session, business.tenant.id, "Returns Area")


def goods_back(session, business, commitment, quantity, returns, *, days_ago):
    return record_movement(
        session,
        business.tenant.id,
        "return",
        business.item.id,
        quantity,
        to_location_id=returns.id,
        commitment_id=commitment.id,
        occurred_at=AS_OF - timedelta(days=days_ago),
    )


def settle(session, business, movement, quantity, returns, *, days_after=1):
    return record_movement(
        session,
        business.tenant.id,
        "transfer",
        business.item.id,
        quantity,
        from_location_id=returns.id,
        to_location_id=business.location.id,
        resolves_movement_id=movement.id,
        occurred_at=movement.occurred_at + timedelta(days=days_after),
    )


def resolution_history(session, business, returns, *, lag_days=2, cases=6, prefix="A"):
    """A tenant that normally deals with a return in `lag_days`."""
    stock(session, business, 400)
    for index in range(cases):
        _, _, commitment = order(session, business, number=f"SO-RES-{prefix}{index}")
        ship(session, business, commitment, 10)
        came = goods_back(
            session, business, commitment, 4, returns, days_ago=150 - index * 5
        )
        settle(session, business, came, 4, returns, days_after=lag_days)


def test_the_resolution_norm_describes_this_tenant(session, business):
    from reality.services import exceptions

    returns = area(session, business)
    resolution_history(session, business, returns, lag_days=2, cases=4)

    # Four settled returns is not a norm.
    assert exceptions._resolution_threshold(session, business.tenant.id) is None

    resolution_history(session, business, returns, lag_days=2, cases=2, prefix="B")

    # Six is, and three times two days sits under the fortnight floor.
    assert exceptions._resolution_threshold(session, business.tenant.id) == (
        timedelta(days=14)
    )


def test_the_resolution_norm_is_learned_per_tenant(session, business):
    from reality.services import exceptions

    returns = area(session, business)
    resolution_history(session, business, returns, cases=6)
    foreign = create_tenant(session, "Foreign returns tenant")

    assert exceptions._resolution_threshold(session, business.tenant.id) is not None
    assert exceptions._resolution_threshold(session, foreign.id) is None


def test_return_unresolved(session, business):
    returns = area(session, business)
    resolution_history(session, business, returns, cases=6)
    _, _, commitment = order(session, business, number="SO-SITTING")
    ship(session, business, commitment, 10)
    sitting = goods_back(session, business, commitment, 6, returns, days_ago=60)

    row = by_class(session, business.tenant.id)["return_unresolved"]

    assert row.record_type == "movement"
    assert row.record_id == sitting.id
    assert row.causal_values["returned_quantity"] == Decimal("6.0000")
    assert row.causal_values["resolved_quantity"] == Decimal("0.0000")
    assert row.causal_values["outstanding_quantity"] == Decimal("6.0000")
    assert row.causal_values["standing_for_days"] == 60
    assert row.causal_values["threshold_days"] == 14

    # Settling part of it reports only what is still sitting.
    settle(session, business, sitting, 4, returns, days_after=59)
    assert by_class(session, business.tenant.id)["return_unresolved"].causal_values[
        "outstanding_quantity"
    ] == Decimal("2.0000")

    # A recent return says nothing, whatever else is standing.
    _, _, fresh_commitment = order(session, business, number="SO-FRESH")
    ship(session, business, fresh_commitment, 10)
    goods_back(session, business, fresh_commitment, 3, returns, days_ago=2)
    assert by_class(session, business.tenant.id)["return_unresolved"].record_id == (
        sitting.id
    )


def test_return_unresolved_clears_through_reality(session, business):
    returns = area(session, business)
    resolution_history(session, business, returns, cases=6)
    _, _, commitment = order(session, business, number="SO-CLEARS")
    ship(session, business, commitment, 10)
    sitting = goods_back(session, business, commitment, 5, returns, days_ago=60)
    assert "return_unresolved" in by_class(session, business.tenant.id)

    settle(session, business, sitting, 5, returns, days_after=59)

    assert "return_unresolved" not in by_class(session, business.tenant.id)


def test_a_voided_resolution_stops_counting(session, business):
    from reality.services.core import correct_movement

    returns = area(session, business)
    resolution_history(session, business, returns, cases=6)
    _, _, commitment = order(session, business, number="SO-VOIDED")
    ship(session, business, commitment, 10)
    sitting = goods_back(session, business, commitment, 5, returns, days_ago=60)
    settlement = settle(session, business, sitting, 5, returns, days_after=59)
    assert "return_unresolved" not in by_class(session, business.tenant.id)

    correct_movement(
        session,
        business.tenant.id,
        settlement.id,
        reason="Booked against the wrong return",
    )

    # A settlement recorded in error settled nothing, so the goods are sitting.
    assert by_class(session, business.tenant.id)["return_unresolved"].record_id == (
        sitting.id
    )

    # And a voided return needs no resolution at all.
    correct_movement(
        session,
        business.tenant.id,
        sitting.id,
        reason="The goods never came back",
    )
    assert "return_unresolved" not in by_class(session, business.tenant.id)


def test_return_unresolved_exposes_full_entry_shape(session, business):
    returns = area(session, business)
    resolution_history(session, business, returns, cases=6)
    _, _, commitment = order(session, business, number="SO-SHAPE-RET")
    ship(session, business, commitment, 10)
    sitting = goods_back(session, business, commitment, 5, returns, days_ago=60)

    row = by_class(session, business.tenant.id)["return_unresolved"]

    assert row.id == f"exc__return_unresolved__{sitting.id}"
    assert row.severity == "normal"
    assert row.title and row.impact
    assert row.cause_ids == ()
    assert set(row.trace) <= {"movement_id", "commitment_id", "source_record_id"}
    assert row.trace["movement_id"] == sitting.id
    assert row.trace["commitment_id"] == commitment.id


def test_return_unresolved_orders_longest_first(session, business):
    returns = area(session, business)
    resolution_history(session, business, returns, cases=6)
    older_ids = []
    for number, days in (("SO-OLD-RET", 90), ("SO-NEW-RET", 30)):
        _, _, commitment = order(session, business, number=number)
        ship(session, business, commitment, 10)
        older_ids.append(
            goods_back(session, business, commitment, 3, returns, days_ago=days).id
        )

    rows = [
        row.record_id
        for row in operational_exceptions(session, business.tenant.id, as_of=AS_OF)
        if row.class_id == "return_unresolved"
    ]

    assert rows == older_ids
    assert rows == [
        row.record_id
        for row in operational_exceptions(session, business.tenant.id, as_of=AS_OF)
        if row.class_id == "return_unresolved"
    ]


# --- A credit note gives the money back (spec 084) -------------------------


def credited_invoice(session, business, number, amount, *, day="2026-08-01"):
    document = create_document(
        session,
        business.tenant.id,
        "sales_invoice",
        number,
        business.customer.id,
        amount,
        document_date=day,
    )
    post_sales_invoice(session, business.tenant.id, document.id)
    return document


def note(session, business, number, amount, *, day="2026-08-01"):
    return create_document(
        session,
        business.tenant.id,
        "credit_note",
        number,
        business.customer.id,
        amount,
        document_date=day,
    )


def posting_history(session, business, *, lag_days=2, cases=6, prefix="A"):
    """A tenant that normally posts a credit note `lag_days` after recording it."""
    for index in range(cases):
        recorded = AS_OF - timedelta(days=120 - index * 5)
        credit = note(
            session,
            business,
            f"GS-NORM-{prefix}{index}",
            "10.00",
            day=recorded.date().isoformat(),
        )
        post_sales_credit_note(
            session,
            business.tenant.id,
            credit.id,
            effective_at=recorded + timedelta(days=lag_days),
        )
        post_customer_refund(session, business.tenant.id, credit.id, "10.00")


def test_the_posting_norm_describes_this_tenant(session, business):
    from reality.services import exceptions

    posting_history(session, business, cases=4)

    # Four is not a norm, so nothing is claimed and nothing reported.
    assert exceptions._posting_threshold(session, business.tenant.id) is None

    posting_history(session, business, cases=2, prefix="B")

    assert exceptions._posting_threshold(session, business.tenant.id) == (
        timedelta(days=14)
    )


def test_credit_note_unposted(session, business):
    posting_history(session, business, cases=6)
    forgotten = note(session, business, "GS-FORGOTTEN", "40.00", day="2026-06-01")
    note(session, business, "GS-YESTERDAY", "5.00", day="2026-08-30")

    row = by_class(session, business.tenant.id)["credit_note_unposted"]

    assert row.record_type == "document"
    assert row.record_id == forgotten.id
    assert row.causal_values["gross_amount"] == Decimal("40.0000")
    assert row.causal_values["threshold_days"] == 14

    # Posting it clears the entry with no manual step.
    post_sales_credit_note(session, business.tenant.id, forgotten.id)
    assert "credit_note_unposted" not in by_class(session, business.tenant.id)


def test_credit_note_unsettled(session, business):
    invoice_document = credited_invoice(session, business, "RE-UNSETTLED", "500.00")
    owed = note(session, business, "GS-UNSETTLED", "60.00")
    post_sales_credit_note(session, business.tenant.id, owed.id)

    row = by_class(session, business.tenant.id)["credit_note_unsettled"]

    assert row.record_type == "document"
    assert row.record_id == owed.id
    assert row.causal_values["gross_amount"] == Decimal("60.0000")
    assert row.causal_values["outstanding_amount"] == Decimal("60.0000")

    # Netting part of it reports only the remainder.
    allocate_credit_note(
        session, business.tenant.id, owed.id, invoice_document.id, "20.00"
    )
    assert by_class(session, business.tenant.id)["credit_note_unsettled"].causal_values[
        "outstanding_amount"
    ] == Decimal("40.0000")

    # Refunding the rest clears it.
    post_customer_refund(session, business.tenant.id, owed.id, "40.00")
    assert "credit_note_unsettled" not in by_class(session, business.tenant.id)


def test_credit_note_classes_expose_full_entry_shape(session, business):
    posting_history(session, business, cases=6)
    forgotten = note(session, business, "GS-SHAPE-1", "40.00", day="2026-06-01")
    owed = note(session, business, "GS-SHAPE-2", "60.00")
    post_sales_credit_note(session, business.tenant.id, owed.id)

    current = by_class(session, business.tenant.id)
    for class_id, record_id in (
        ("credit_note_unposted", forgotten.id),
        ("credit_note_unsettled", owed.id),
    ):
        row = current[class_id]
        assert row.id == f"exc__{class_id}__{record_id}"
        assert row.record_type == "document"
        assert row.record_id == record_id
        assert row.severity == "high"
        assert row.title and row.impact
        assert row.cause_ids == ()
        assert set(row.trace) <= {
            "document_id",
            "ledger_entry_id",
            "source_record_id",
        }
        assert row.trace["document_id"] == record_id


def test_credit_note_classes_order_longest_first(session, business):
    posting_history(session, business, cases=6)
    older = note(session, business, "GS-OLD", "10.00", day="2026-05-01")
    newer = note(session, business, "GS-NEW", "10.00", day="2026-07-01")

    rows = [
        row.record_id
        for row in operational_exceptions(session, business.tenant.id, as_of=AS_OF)
        if row.class_id == "credit_note_unposted"
    ]

    assert rows == [older.id, newer.id]
    assert rows == [
        row.record_id
        for row in operational_exceptions(session, business.tenant.id, as_of=AS_OF)
        if row.class_id == "credit_note_unposted"
    ]


def test_credit_note_classes_are_tenant_scoped(session, business):
    posting_history(session, business, cases=6)
    note(session, business, "GS-TENANT", "40.00", day="2026-06-01")
    owed = note(session, business, "GS-TENANT-2", "60.00")
    post_sales_credit_note(session, business.tenant.id, owed.id)
    foreign = create_tenant(session, "Foreign credit tenant")

    current = by_class(session, business.tenant.id)
    assert "credit_note_unposted" in current
    assert "credit_note_unsettled" in current
    assert by_class(session, foreign.id) == {}


# --- Sold for less than it costs to buy (spec 086) -------------------------


def purchase_price(session, business, amount, *, unit="pcs", currency="EUR", item=None):
    """What the company says the item costs it, on its default purchase list."""
    price_list = create_price_list(
        session,
        business.tenant.id,
        f"BUY-{uid('l')[-6:]}",
        "Standing purchase prices",
        "purchase",
        currency,
        is_default=True,
    )
    create_price_list_entry(
        session,
        business.tenant.id,
        price_list.id,
        (item or business.item).id,
        1,
        amount,
        unit,
    )
    return price_list


def sold_at(session, business, number, price, *, quantity="1", unit="pcs", item=None):
    _, lines = create_manual_document_with_lines(
        session,
        business.tenant.id,
        "sales_order",
        number,
        business.customer.id,
        [
            {
                "item_id": (item or business.item).id
                if (item or business.item)
                else None,
                "quantity": quantity,
                "unit": unit,
                "unit_price": price,
                "gross_amount": "1.00",
            }
        ],
        "1.00",
        document_date="2026-08-20",
    )
    return lines[0]


def test_sold_below_purchase_price(session, business):
    purchase_price(session, business, "10.00")
    cheap = sold_at(session, business, "SO-CHEAP", "8.00")
    sold_at(session, business, "SO-AT-COST", "10.00")

    row = by_class(session, business.tenant.id)["sold_below_purchase_price"]

    assert row.record_type == "document_line"
    assert row.record_id == cheap.id
    # Both figures exactly as somebody stated them, and the plain difference.
    assert row.causal_values["agreed_unit_price"] == Decimal("8.0000")
    assert row.causal_values["purchase_unit_price"] == Decimal("10.0000")
    assert row.causal_values["shortfall"] == Decimal("2.0000")


def test_without_a_purchase_price_nothing_is_reported(session, business):
    line = sold_at(session, business, "SO-NO-COST", "1.00")

    # The company has not said what the item costs it, so nothing is invented.
    assert "sold_below_purchase_price" not in by_class(session, business.tenant.id)

    # Recording one reports the same line at once.
    purchase_price(session, business, "10.00")
    assert (
        by_class(session, business.tenant.id)["sold_below_purchase_price"].record_id
        == line.id
    )


def test_a_line_agreed_at_zero_is_a_decision(session, business):
    purchase_price(session, business, "10.00")
    sold_at(session, business, "SO-SAMPLE", "0")

    # A sample or a replacement is priced at nothing on purpose.
    assert "sold_below_purchase_price" not in by_class(session, business.tenant.id)

    # A penny is not, which is what makes the silence a rule.
    penny = sold_at(session, business, "SO-PENNY", "0.01")
    assert (
        by_class(session, business.tenant.id)["sold_below_purchase_price"].record_id
        == penny.id
    )


def test_only_sales_lines_are_judged(session, business):
    purchase_price(session, business, "10.00")
    _, purchase_lines = create_manual_document_with_lines(
        session,
        business.tenant.id,
        "purchase_order",
        "PO-CHEAP",
        business.supplier.id,
        [
            {
                "item_id": business.item.id,
                "quantity": "1",
                "unit": "pcs",
                "unit_price": "2.00",
                "gross_amount": "2.00",
            }
        ],
        "2.00",
    )
    _, freight_lines = create_manual_document_with_lines(
        session,
        business.tenant.id,
        "sales_order",
        "SO-FREIGHT",
        business.customer.id,
        [
            {
                "description": "Freight",
                "quantity": "1",
                "unit": "pcs",
                "unit_price": "1.00",
                "gross_amount": "1.00",
            }
        ],
        "1.00",
    )

    # Buying cheaply is the point of buying, and freight has no purchase price.
    assert "sold_below_purchase_price" not in by_class(session, business.tenant.id)
    assert purchase_lines[0].id and freight_lines[0].id

    # A sales line for the same item does report.
    cheap = sold_at(session, business, "SO-JUDGED", "3.00")
    assert (
        by_class(session, business.tenant.id)["sold_below_purchase_price"].record_id
        == cheap.id
    )


def test_a_different_currency_or_unit_is_not_compared(session, business):
    purchase_price(session, business, "10.00", unit="box")
    sold_at(session, business, "SO-UNITS", "2.00", unit="pcs")

    # Two euro a piece against ten a box is not a comparison.
    assert "sold_below_purchase_price" not in by_class(session, business.tenant.id)

    # The same figures in the price list's own unit report at once.
    matching = sold_at(session, business, "SO-UNITS-MATCH", "2.00", unit="box")
    assert (
        by_class(session, business.tenant.id)["sold_below_purchase_price"].record_id
        == matching.id
    )


def test_the_pricing_entry_exposes_full_shape(session, business):
    purchase_price(session, business, "10.00")
    line = sold_at(session, business, "SO-SHAPE", "7.00")

    row = by_class(session, business.tenant.id)["sold_below_purchase_price"]

    assert row.id == f"exc__sold_below_purchase_price__{line.id}"
    assert row.severity == "high"
    assert row.title and row.impact
    assert row.cause_ids == ()
    assert set(row.trace) <= {
        "document_line_id",
        "document_id",
        "price_list_entry_id",
        "source_record_id",
    }
    assert row.trace["document_line_id"] == line.id


def test_the_pricing_entry_clears_through_reality(session, business):
    purchase_price(session, business, "10.00")
    line = sold_at(session, business, "SO-CLEARS", "7.00")
    assert "sold_below_purchase_price" in by_class(session, business.tenant.id)

    line.unit_price = Decimal("11.0000")
    session.flush()

    assert "sold_below_purchase_price" not in by_class(session, business.tenant.id)


def test_the_pricing_entry_orders_longest_first(session, business):
    purchase_price(session, business, "10.00")
    older = sold_at(session, business, "SO-OLD-PRICE", "7.00")
    newer = sold_at(session, business, "SO-NEW-PRICE", "7.00")
    older_document = session.get(type(older), older.id)
    assert older_document is not None

    rows = [
        row.record_id
        for row in operational_exceptions(session, business.tenant.id, as_of=AS_OF)
        if row.class_id == "sold_below_purchase_price"
    ]

    assert set(rows) == {older.id, newer.id}
    assert rows == [
        row.record_id
        for row in operational_exceptions(session, business.tenant.id, as_of=AS_OF)
        if row.class_id == "sold_below_purchase_price"
    ]


def test_the_pricing_class_is_tenant_scoped(session, business):
    purchase_price(session, business, "10.00")
    sold_at(session, business, "SO-TENANT-PRICE", "7.00")
    foreign = create_tenant(session, "Foreign pricing tenant")

    assert "sold_below_purchase_price" in by_class(session, business.tenant.id)
    assert by_class(session, foreign.id) == {}


# --- Units that do not meet (spec 087) -------------------------------------


def states_a_conversion(session, business, *, purchase_unit="box", factor="12"):
    """The company says how many pieces are in one of what it buys."""
    return update_item(
        session,
        business.tenant.id,
        business.item.id,
        business.item.sku,
        business.item.name,
        business.item.unit,
        purchase_unit=purchase_unit,
        conversion_factor=factor,
    )


def ordered_in_boxes(session, business, *, number="SO-087", quantity="10"):
    """One order line in boxes, delivered in full."""
    stock(session, business, 200)
    _, line, commitment = order(
        session, business, number=number, quantity=quantity, unit="box"
    )
    ship(session, business, commitment, quantity)
    return line


def test_a_stated_conversion_lets_the_comparison_happen(session, business):
    line = ordered_in_boxes(session, business)
    bill(session, business, line, number="RE-087", quantity="108", unit="pcs")

    # Nothing yet relates a box to a piece, so the pair cannot be judged — and
    # the queue says so rather than staying silent about it.
    rows = by_class(session, business.tenant.id)
    assert "shipped_not_billed" not in rows
    assert rows["units_not_comparable"].record_id == business.item.id

    # The company states how it buys the item, and the same figures are enough.
    states_a_conversion(session, business)
    rows = by_class(session, business.tenant.id)

    assert "units_not_comparable" not in rows
    row = rows["shipped_not_billed"]
    assert row.causal_values["delivered_quantity"] == Decimal("10.0000")
    assert row.causal_values["billed_quantity"] == Decimal(9)
    assert row.causal_values["unbilled_quantity"] == Decimal("1.0000")
    # Reported in the unit that was agreed, because that is the unit the promise
    # and every movement against it were recorded in.
    assert row.causal_values["unit"] == "box"

    # Billing the last box in pieces clears it with no manual step.
    bill(session, business, line, number="RE-087b", quantity="12", unit="pcs")
    assert "shipped_not_billed" not in by_class(session, business.tenant.id)


def test_an_inexact_conversion_is_declined(session, business):
    states_a_conversion(session, business)
    line = ordered_in_boxes(session, business, number="SO-087-ODD")
    bill(session, business, line, number="RE-087-ODD", quantity="107", unit="pcs")

    # A hundred and seven pieces are not a number of boxes, and a remainder is
    # the rounding this product exists to avoid.
    rows = by_class(session, business.tenant.id)
    assert "shipped_not_billed" not in rows
    assert (
        rows["units_not_comparable"].causal_values["reason"]
        == "conversion_leaves_a_remainder"
    )

    # The positive control: it is the total billed against the agreement that is
    # converted, not each invoice on its own, so one more piece makes the whole
    # comparable and it happens at once.
    bill(session, business, line, number="RE-087-ODD-2", quantity="1", unit="pcs")
    rows = by_class(session, business.tenant.id)
    assert "units_not_comparable" not in rows
    assert rows["shipped_not_billed"].causal_values["billed_quantity"] == Decimal(9)


def test_a_useless_factor_is_no_relation(session, business):
    states_a_conversion(session, business)
    line = ordered_in_boxes(session, business, number="SO-087-ZERO")
    bill(session, business, line, number="RE-087-ZERO", quantity="108", unit="pcs")
    assert "shipped_not_billed" in by_class(session, business.tenant.id)

    # No service will record one, so this is defence against a figure that
    # arrived some other way. Zero is not a statement about anything.
    for factor in (Decimal(0), Decimal(-12)):
        business.item.conversion_factor = factor
        session.flush()
        rows = by_class(session, business.tenant.id)
        assert "shipped_not_billed" not in rows
        assert (
            rows["units_not_comparable"].causal_values["reason"] == "no_stated_relation"
        )

    business.item.conversion_factor = Decimal(12)
    session.flush()
    assert "shipped_not_billed" in by_class(session, business.tenant.id)


def test_a_third_unit_has_no_stated_relation(session, business):
    states_a_conversion(session, business)
    line = ordered_in_boxes(session, business, number="SO-087-KG")
    bill(session, business, line, number="RE-087-KG", quantity="108", unit="kg")

    # Reality knows what this company said about this item and nothing else. A
    # kilogram is not in that statement.
    rows = by_class(session, business.tenant.id)
    assert "shipped_not_billed" not in rows
    assert rows["units_not_comparable"].causal_values["reason"] == "no_stated_relation"
    assert rows["units_not_comparable"].causal_values["units"] == ["box", "kg"]

    # The positive control: on a second line, in the item's own purchase unit,
    # the very same comparison is made.
    second = ordered_in_boxes(session, business, number="SO-087-KG-2")
    bill(session, business, second, number="RE-087-KG-2", quantity="108", unit="pcs")
    assert "shipped_not_billed" in by_class(session, business.tenant.id)


def test_prices_are_never_converted(session, business):
    states_a_conversion(session, business)
    line = ordered_in_boxes(session, business, number="SO-087-PRICE")
    # A hundred and eight pieces convert to nine boxes exactly, so the quantity
    # side is perfectly comparable. The price is not: nine euros per box and
    # nine euros per piece are different figures, and dividing one by twelve
    # would produce money nobody agreed.
    bill(
        session,
        business,
        line,
        number="RE-087-PRICE",
        quantity="108",
        unit="pcs",
        unit_price="1.00",
    )

    rows = by_class(session, business.tenant.id)
    assert "shipped_not_billed" in rows
    assert "invoice_price_differs" not in rows
    # And the refusal is not reported either: no statement anybody could make
    # would let that comparison happen, so an entry offering one would be a lie.
    assert "units_not_comparable" not in rows

    # The positive control: a price difference in a matching unit still reports.
    second = ordered_in_boxes(session, business, number="SO-087-PRICE-2")
    bill(
        session,
        business,
        second,
        number="RE-087-PRICE-2",
        quantity="10",
        unit="box",
        unit_price="11.00",
    )
    assert "invoice_price_differs" in by_class(session, business.tenant.id)


def test_one_decision_answers_comparability():
    """DR-003: no class decides for itself whether two quantities can be compared."""
    import inspect
    import re

    from reality.services import exceptions

    comparing = {
        name
        for name, function in vars(exceptions).items()
        if inspect.isfunction(function)
        and function.__module__ == exceptions.__name__
        and re.search(r"\.unit\s*[!=]=", inspect.getsource(function))
    }

    # Three classes used to answer this for themselves, which is how two of them
    # would eventually have disagreed. The quantity rule now lives in one place
    # that compares no unit directly. `_prices_comparable` is the deliberately
    # narrower rule the prices get, and `_standing_purchase_price` compares a
    # unit only to look a price up by it — a lookup key, not a judgement about
    # whether two figures are the same kind of thing.
    assert comparing == {"_prices_comparable", "_standing_purchase_price"}


def sold_in_boxes(session, business, item, *, number, billed, unit="pcs"):
    """One order line in boxes for a given item, delivered and then invoiced."""
    record_movement(
        session,
        business.tenant.id,
        "opening_stock",
        item.id,
        200,
        to_location_id=business.location.id,
    )
    _, _document, lines, commitments = create_manual_order(
        session,
        business.tenant.id,
        "sales",
        number,
        business.company.id,
        business.customer.id,
        business.location.id,
        [
            {
                "item_id": item.id,
                "quantity": "10",
                "unit": "box",
                "unit_price": "9.00",
                "gross_amount": "90.00",
            }
        ],
        "90.00",
        requested_delivery_at=AS_OF + timedelta(days=30),
    )
    record_movement(
        session,
        business.tenant.id,
        "shipment",
        item.id,
        10,
        from_location_id=business.location.id,
        commitment_id=commitments[0].id,
        occurred_at=AS_OF - timedelta(days=3),
    )
    create_manual_document_with_lines(
        session,
        business.tenant.id,
        "sales_invoice",
        f"RE-{number}",
        business.customer.id,
        [
            {
                "item_id": item.id,
                "quantity": billed,
                "unit": unit,
                "unit_price": "1.00",
                "gross_amount": "90.00",
                "billed_document_line_id": lines[0].id,
            }
        ],
        "90.00",
        document_date="2026-08-20",
    )
    return lines[0]


def test_units_not_comparable(session, business):
    first = ordered_in_boxes(session, business, number="SO-087-A")
    second = ordered_in_boxes(session, business, number="SO-087-B")
    bill(session, business, first, number="RE-087-A", quantity="60", unit="pcs")
    bill(session, business, first, number="RE-087-A2", quantity="30", unit="pcs")
    bill(session, business, second, number="RE-087-B", quantity="45", unit="pcs")

    rows = [
        row
        for row in operational_exceptions(session, business.tenant.id, as_of=AS_OF)
        if row.class_id == "units_not_comparable"
    ]

    # Three invoice lines across two order lines, one statement missing, and one
    # entry: the relation belongs to the item and so does the fix.
    assert len(rows) == 1
    assert rows[0].record_type == "item"
    assert rows[0].record_id == business.item.id
    assert rows[0].causal_values["affected_lines"] == 3
    assert rows[0].causal_values["units"] == ["box", "pcs"]
    assert rows[0].causal_values["stock_unit"] == "pcs"
    assert "3 lines" in rows[0].impact

    # A pair whose units already match is not counted: the class is about what
    # could not be judged, not about every line.
    third = ordered_in_boxes(session, business, number="SO-087-C")
    bill(session, business, third, number="RE-087-C", quantity="10", unit="box")
    rows = [
        row
        for row in operational_exceptions(session, business.tenant.id, as_of=AS_OF)
        if row.class_id == "units_not_comparable"
    ]
    assert len(rows) == 1
    assert rows[0].causal_values["affected_lines"] == 3


def test_the_entry_says_which_of_the_two_went_wrong(session, business):
    line = ordered_in_boxes(session, business, number="SO-087-WHY")
    bill(session, business, line, number="RE-087-WHY", quantity="107", unit="pcs")

    # Nothing stated: the exit is to state it.
    row = by_class(session, business.tenant.id)["units_not_comparable"]
    assert row.causal_values["reason"] == "no_stated_relation"
    assert "states no conversion" in row.impact

    # Stated and still not comparable: a different problem with a different
    # exit, and telling this company to state the relation would be advice it
    # has already taken.
    states_a_conversion(session, business)
    row = by_class(session, business.tenant.id)["units_not_comparable"]
    assert row.causal_values["reason"] == "conversion_leaves_a_remainder"
    assert row.causal_values["conversion_factor"] == Decimal("12.000000")
    assert "does not divide evenly" in row.impact


def test_the_units_entry_exposes_full_shape(session, business):
    line = ordered_in_boxes(session, business, number="SO-087-SHAPE")
    _, invoice_line = bill(
        session, business, line, number="RE-087-SHAPE", quantity="108", unit="pcs"
    )

    row = by_class(session, business.tenant.id)["units_not_comparable"]

    assert row.id == f"exc__units_not_comparable__{business.item.id}"
    assert row.severity == "normal"
    assert row.title and row.impact
    assert row.cause_ids == ()
    assert row.record_type == "item"
    assert row.record_id == business.item.id
    assert set(row.causal_values) == {
        "units",
        "stock_unit",
        "purchase_unit",
        "conversion_factor",
        "reason",
        "affected_lines",
    }
    # The trace reaches its records by identity and restates no business field.
    # The units are in the causal values, because they are what the entry is
    # about.
    assert set(row.trace) == {"item_id", "document_line_ids"}
    assert row.trace["item_id"] == business.item.id
    assert row.trace["document_line_ids"] == [invoice_line.id]


def test_the_units_entry_clears_through_reality(session, business):
    line = ordered_in_boxes(session, business, number="SO-087-CLEARS")
    bill(session, business, line, number="RE-087-CLEARS", quantity="108", unit="pcs")
    assert "units_not_comparable" in by_class(session, business.tenant.id)

    # Stating the relation is the whole of it: no acknowledgement, no status,
    # and nothing was stored that would have to be undone.
    states_a_conversion(session, business)

    assert "units_not_comparable" not in by_class(session, business.tenant.id)


def test_the_units_entry_orders_deterministically(session, business):
    bell = create_item(session, business.tenant.id, "BIKE-BELL", "Bike Bell")
    chain = create_item(session, business.tenant.id, "BIKE-CHAIN", "Bike Chain")
    sold_in_boxes(session, business, chain, number="SO-087-CHAIN", billed="108")
    sold_in_boxes(session, business, bell, number="SO-087-BELL", billed="90")

    def reported():
        return [
            row.record_id
            for row in operational_exceptions(session, business.tenant.id, as_of=AS_OF)
            if row.class_id == "units_not_comparable"
        ]

    # One entry per item, and there is no moment at which a company failed to
    # state a relation — so the order comes from the items themselves and is the
    # same on every read.
    assert reported() == sorted([bell.id, chain.id])
    assert reported() == reported()


def test_the_units_class_is_tenant_scoped(session, business):
    line = ordered_in_boxes(session, business, number="SO-087-TENANT")
    bill(session, business, line, number="RE-087-TENANT", quantity="108", unit="pcs")
    foreign = create_tenant(session, "Foreign units tenant")

    assert "units_not_comparable" in by_class(session, business.tenant.id)
    assert by_class(session, foreign.id) == {}


# --- The early-payment discount (spec 088) ---------------------------------


def skonto_term(session, business, code="SK2_10", *, percent="2", days=10, due=30):
    existing = [
        term
        for term in payment_terms(session, business.tenant.id)
        if term.code == code.upper()
    ]
    if existing:
        return existing[0]
    return create_payment_term(
        session,
        business.tenant.id,
        code,
        f"{percent}% {days} days, net {due}",
        due,
        discount_percent=percent,
        discount_days=days,
    )


def supplier_invoice_under(
    session, business, number, document_date, term_code, amount="1000.00"
):
    """A posted supplier invoice governed by a stated term."""
    invoice = create_document(
        session,
        business.tenant.id,
        "supplier_invoice",
        number,
        business.supplier.id,
        amount,
        document_date=document_date,
        payment_term_code=term_code,
    )
    post_supplier_invoice(session, business.tenant.id, invoice.id)
    return invoice


def discounted_receivable(session, business, number="RE-088", amount="1000.00"):
    """A posted sales invoice due 2026-07-31 whose term grants 2% within ten days."""
    skonto_term(session, business)
    invoice = sales_invoice(
        session, business, number, "2026-07-01", amount, term_code="SK2_10"
    )
    post_sales_invoice(session, business.tenant.id, invoice.id)
    return invoice


def test_purchase_discount_available(session, business):
    skonto_term(session, business)
    # Dated six days before the queue is read, so four days of the window are
    # left when it is.
    invoice = supplier_invoice_under(
        session, business, "ER-088-A", "2026-08-25", "SK2_10"
    )

    row = by_class(session, business.tenant.id)["purchase_discount_available"]

    assert row.record_type == "document"
    assert row.record_id == invoice.id
    assert row.causal_values["discount_percent"] == Decimal("2.000")
    assert row.causal_values["discount_date"] == date(2026, 9, 4)
    assert row.causal_values["days_remaining"] == 4
    assert row.causal_values["outstanding_amount"] == Decimal(1000)

    # The positive control: the same invoice under a term granting no discount
    # says nothing, so the silence is the rule speaking rather than the class
    # being absent.
    create_payment_term(session, business.tenant.id, "NET30", "Net 30 days", 30)
    plain = supplier_invoice_under(
        session, business, "ER-088-PLAIN", "2026-08-25", "NET30"
    )
    reported = {
        entry.record_id
        for entry in operational_exceptions(session, business.tenant.id, as_of=AS_OF)
        if entry.class_id == "purchase_discount_available"
    }
    assert reported == {invoice.id}
    assert plain.id not in reported


def test_the_discount_entry_ends_both_ways(session, business):
    skonto_term(session, business)
    taken = supplier_invoice_under(
        session, business, "ER-088-TAKEN", "2026-08-25", "SK2_10"
    )
    assert "purchase_discount_available" in by_class(session, business.tenant.id)

    # Settling it ends the entry, with nothing persisted and no manual step.
    post_supplier_payment(
        session,
        business.tenant.id,
        taken.id,
        "1000.00",
        effective_at=datetime(2026, 8, 30, 12, tzinfo=UTC),
    )
    assert "purchase_discount_available" not in by_class(session, business.tenant.id)

    # And the deadline passing ends it too, which is the uncomfortable half:
    # the class goes quiet whether the discount was taken or lost, and only the
    # payment says which.
    lost = supplier_invoice_under(
        session, business, "ER-088-LOST", "2026-08-01", "SK2_10"
    )
    reported = {
        entry.record_id
        for entry in operational_exceptions(session, business.tenant.id, as_of=AS_OF)
        if entry.class_id == "purchase_discount_available"
    }
    assert reported == set()
    assert lost.id not in reported


def test_no_discount_amount_is_ever_reported(session, business):
    skonto_term(session, business)
    invoice = supplier_invoice_under(
        session, business, "ER-088-MONEY", "2026-08-25", "SK2_10", amount="1000.13"
    )

    row = by_class(session, business.tenant.id)["purchase_discount_available"]

    # Two per cent of 1000.13 is 20.0026, a figure nobody agreed and one that
    # has to be rounded to be said. It is never said. The only money in the
    # entry is what the ledger already holds open.
    assert row.causal_values["outstanding_amount"] == open_invoice_amount(
        session, business.tenant.id, invoice.id
    )
    money = {
        key: value
        for key, value in row.causal_values.items()
        if isinstance(value, Decimal)
    }
    assert set(money) == {"discount_percent", "outstanding_amount"}
    assert money["discount_percent"] == Decimal("2.000")
    assert "20.00" not in row.impact


def test_a_discount_taken_explains_the_remainder(session, business):
    tenant_id = business.tenant.id
    invoice = discounted_receivable(session, business)
    # Paid on the fourth day for exactly what the agreed rate allows.
    post_customer_payment(
        session,
        tenant_id,
        invoice.id,
        "980.00",
        effective_at=datetime(2026, 7, 5, 9, tzinfo=UTC),
    )

    row = by_class(session, tenant_id)["overdue_receivable"]

    assert row.cause_ids == ("early_payment_discount_taken",)
    # The entry is otherwise exactly what it was: twenty is genuinely open and
    # the queue still says so.
    assert row.causal_values["outstanding_amount"] == Decimal(20)
    assert row.causal_values["days_overdue"] == 31
    assert row.severity == "high"

    # Beyond what the rate allows is not a discount, whenever it arrived.
    short = discounted_receivable(session, business, number="RE-088-SHORT")
    post_customer_payment(
        session,
        tenant_id,
        short.id,
        "900.00",
        effective_at=datetime(2026, 7, 5, 9, tzinfo=UTC),
    )
    # Inside the rate but after the window had closed is not one either.
    late = discounted_receivable(session, business, number="RE-088-LATE")
    post_customer_payment(
        session,
        tenant_id,
        late.id,
        "980.00",
        effective_at=datetime(2026, 7, 20, 9, tzinfo=UTC),
    )
    # And an invoice nobody paid at all is simply overdue.
    unpaid = discounted_receivable(session, business, number="RE-088-UNPAID")

    causes = {
        entry.record_id: entry.cause_ids
        for entry in operational_exceptions(session, tenant_id, as_of=AS_OF)
        if entry.class_id == "overdue_receivable"
    }
    assert causes[invoice.id] == ("early_payment_discount_taken",)
    assert causes[short.id] == ()
    assert causes[late.id] == ()
    assert causes[unpaid.id] == ()


def test_the_discount_reason_works_on_both_sides(session, business):
    tenant_id = business.tenant.id
    skonto_term(session, business)
    # The company takes a discount from its own supplier: the same condition
    # with the words the other way round.
    payable = supplier_invoice_under(
        session, business, "ER-088-BOTH", "2026-07-01", "SK2_10"
    )
    post_supplier_payment(
        session,
        tenant_id,
        payable.id,
        "980.00",
        effective_at=datetime(2026, 7, 5, 9, tzinfo=UTC),
    )
    receivable = discounted_receivable(session, business, number="RE-088-BOTH")
    post_customer_payment(
        session,
        tenant_id,
        receivable.id,
        "980.00",
        effective_at=datetime(2026, 7, 5, 9, tzinfo=UTC),
    )

    rows = {
        entry.class_id: entry
        for entry in operational_exceptions(session, tenant_id, as_of=AS_OF)
        if entry.class_id in {"overdue_receivable", "overdue_payable"}
    }

    assert rows["overdue_payable"].cause_ids == ("early_payment_discount_taken",)
    assert rows["overdue_receivable"].cause_ids == ("early_payment_discount_taken",)


def test_the_discount_entry_exposes_full_shape(session, business):
    skonto_term(session, business)
    invoice = supplier_invoice_under(
        session, business, "ER-088-SHAPE", "2026-08-25", "SK2_10"
    )

    row = by_class(session, business.tenant.id)["purchase_discount_available"]

    assert row.id == f"exc__purchase_discount_available__{invoice.id}"
    assert row.severity == "normal"
    assert row.title and row.impact
    assert row.cause_ids == ()
    assert set(row.causal_values) == {
        "discount_percent",
        "discount_date",
        "days_remaining",
        "due_date",
        "outstanding_amount",
        "currency",
    }
    assert set(row.trace) <= {"document_id", "ledger_entry_id", "source_record_id"}
    assert row.trace["document_id"] == invoice.id


def test_the_discount_entry_orders_by_deadline(session, business):
    skonto_term(session, business)
    later = supplier_invoice_under(
        session, business, "ER-088-LATER", "2026-08-27", "SK2_10"
    )
    sooner = supplier_invoice_under(
        session, business, "ER-088-SOONER", "2026-08-23", "SK2_10"
    )

    def reported():
        return [
            entry.record_id
            for entry in operational_exceptions(
                session, business.tenant.id, as_of=AS_OF
            )
            if entry.class_id == "purchase_discount_available"
        ]

    # The one about to expire is the one worth acting on first, and the order is
    # the same on every read.
    assert reported() == [sooner.id, later.id]
    assert reported() == reported()


def test_the_discount_class_is_tenant_scoped(session, business):
    skonto_term(session, business)
    supplier_invoice_under(session, business, "ER-088-TEN", "2026-08-25", "SK2_10")
    foreign = create_tenant(session, "Foreign discount tenant")

    assert "purchase_discount_available" in by_class(session, business.tenant.id)
    assert by_class(session, foreign.id) == {}


def test_nothing_in_this_feature_divides():
    """DR-007: a division here would author money nobody agreed."""
    import ast
    import inspect
    import textwrap

    from reality.services import exceptions

    watched = (
        exceptions._purchase_discount_available_exceptions,
        exceptions._discount_explains_remainder,
        exceptions._open_item_exceptions,
    )
    divisions = [
        function.__name__
        for function in watched
        for node in ast.walk(ast.parse(textwrap.dedent(inspect.getsource(function))))
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div | ast.FloorDiv)
    ]

    # Both sides of the discount comparison are multiplied out precisely so that
    # nothing has to be rounded. A division added near this code is a defect
    # whatever it produces.
    assert divisions == []


# --- The credit that comes the other way (spec 089) ------------------------


def supplier_note(session, business, number, amount, *, day="2026-08-01"):
    return create_document(
        session,
        business.tenant.id,
        "supplier_credit_note",
        number,
        business.supplier.id,
        amount,
        document_date=day,
    )


def supplier_posting_history(session, business, *, lag_days=2, cases=6, prefix="A"):
    """A tenant that normally books a supplier credit `lag_days` after recording it."""
    for index in range(cases):
        recorded = AS_OF - timedelta(days=120 - index * 5)
        credit = supplier_note(
            session,
            business,
            f"SG-NORM-{prefix}{index}",
            "10.00",
            day=recorded.date().isoformat(),
        )
        post_supplier_credit_note(
            session,
            business.tenant.id,
            credit.id,
            effective_at=recorded + timedelta(days=lag_days),
        )
        post_supplier_refund(session, business.tenant.id, credit.id, "10.00")


def payable(session, business, number, amount, *, day="2026-08-01"):
    document = create_document(
        session,
        business.tenant.id,
        "supplier_invoice",
        number,
        business.supplier.id,
        amount,
        document_date=day,
    )
    post_supplier_invoice(session, business.tenant.id, document.id)
    return document


def test_supplier_credit_unposted(session, business):
    supplier_posting_history(session, business, cases=6)
    forgotten = supplier_note(
        session, business, "SG-FORGOTTEN", "40.00", day="2026-06-01"
    )
    supplier_note(session, business, "SG-YESTERDAY", "5.00", day="2026-08-30")

    row = by_class(session, business.tenant.id)["supplier_credit_unposted"]

    assert row.record_type == "document"
    assert row.record_id == forgotten.id
    assert row.causal_values["gross_amount"] == Decimal("40.0000")
    assert row.causal_values["threshold_days"] == 14

    # Booking it clears the entry with no manual step.
    post_supplier_credit_note(session, business.tenant.id, forgotten.id)
    assert "supplier_credit_unposted" not in by_class(session, business.tenant.id)


def test_supplier_credit_unclaimed(session, business):
    owed_to_us = payable(session, business, "ER-UNCLAIMED", "500.00")
    credit = supplier_note(session, business, "SG-UNCLAIMED", "60.00")
    post_supplier_credit_note(session, business.tenant.id, credit.id)

    row = by_class(session, business.tenant.id)["supplier_credit_unclaimed"]

    assert row.record_type == "document"
    assert row.record_id == credit.id
    assert row.causal_values["gross_amount"] == Decimal("60.0000")
    assert row.causal_values["outstanding_amount"] == Decimal("60.0000")

    # Netting part of it reports only the remainder.
    allocate_supplier_credit_note(
        session, business.tenant.id, credit.id, owed_to_us.id, "20.00"
    )
    assert by_class(session, business.tenant.id)[
        "supplier_credit_unclaimed"
    ].causal_values["outstanding_amount"] == Decimal("40.0000")

    # Having the supplier refund the rest clears it.
    post_supplier_refund(session, business.tenant.id, credit.id, "40.00")
    assert "supplier_credit_unclaimed" not in by_class(session, business.tenant.id)


def test_the_two_credit_sides_stay_apart(session, business):
    tenant_id = business.tenant.id
    # Both sides have a history, so both thresholds exist and neither class is
    # silent for want of one.
    posting_history(session, business, cases=6, prefix="SEP")
    supplier_posting_history(session, business, cases=6, prefix="SEP")

    ours = note(session, business, "GS-SEPARATE", "40.00", day="2026-06-01")
    theirs = supplier_note(session, business, "SG-SEPARATE", "40.00", day="2026-06-01")

    reported = {
        (row.class_id, row.record_id)
        for row in operational_exceptions(session, tenant_id, as_of=AS_OF)
        if row.class_id.endswith(("_unposted", "_unsettled", "_unclaimed"))
    }

    # Each pair of classes reports only its own document type. A credit the
    # company wrote is never reported as one a supplier sent, and neither class
    # can quietly start reading the other's documents.
    assert ("credit_note_unposted", ours.id) in reported
    assert ("supplier_credit_unposted", theirs.id) in reported
    assert ("credit_note_unposted", theirs.id) not in reported
    assert ("supplier_credit_unposted", ours.id) not in reported


def test_each_side_learns_its_own_rhythm(session, business):
    """FR-009a: the rule is shared and the history deliberately is not."""
    from reality.services import exceptions

    tenant_id = business.tenant.id
    posting_history(session, business, cases=6, prefix="RHY")
    supplier_note(session, business, "SG-SLOW", "40.00", day="2026-06-01")

    # A prompt history of the company's own credit notes says nothing about how
    # it handles a supplier's, so the supplier side claims no norm and reports
    # nothing — even though the selling side has one.
    assert exceptions._posting_threshold(session, tenant_id) is not None
    assert (
        exceptions._posting_threshold(
            session, tenant_id, "supplier_credit_note", "inventory"
        )
        is None
    )
    assert "supplier_credit_unposted" not in by_class(session, tenant_id)

    # The positive control: a history of supplier credits gives that side its
    # own norm, and the same forgotten credit reports at once.
    supplier_posting_history(session, business, cases=6, prefix="RHY")
    assert "supplier_credit_unposted" in by_class(session, tenant_id)


def test_the_supplier_credit_entries_expose_full_shape(session, business):
    tenant_id = business.tenant.id
    supplier_posting_history(session, business, cases=6, prefix="SHAPE")
    unbooked = supplier_note(session, business, "SG-SHAPE-1", "40.00", day="2026-06-01")
    unclaimed = supplier_note(session, business, "SG-SHAPE-2", "70.00")
    post_supplier_credit_note(session, tenant_id, unclaimed.id)

    rows = by_class(session, tenant_id)

    first = rows["supplier_credit_unposted"]
    assert first.id == f"exc__supplier_credit_unposted__{unbooked.id}"
    assert first.severity == "high"
    assert first.title and first.impact
    assert first.cause_ids == ()
    assert set(first.causal_values) == {
        "gross_amount",
        "currency",
        "standing_for_days",
        "threshold_days",
        "norm_days",
    }
    assert set(first.trace) <= {"document_id", "source_record_id"}
    assert first.trace["document_id"] == unbooked.id

    second = rows["supplier_credit_unclaimed"]
    assert second.id == f"exc__supplier_credit_unclaimed__{unclaimed.id}"
    assert set(second.causal_values) == {
        "gross_amount",
        "outstanding_amount",
        "currency",
    }
    assert second.trace["document_id"] == unclaimed.id


def test_the_supplier_credit_entries_clear_through_reality(session, business):
    tenant_id = business.tenant.id
    invoice_document = payable(session, business, "ER-CLEARS", "300.00")
    credit = supplier_note(session, business, "SG-CLEARS", "300.00")
    post_supplier_credit_note(session, tenant_id, credit.id)
    assert "supplier_credit_unclaimed" in by_class(session, tenant_id)

    allocate_supplier_credit_note(
        session, tenant_id, credit.id, invoice_document.id, "300.00"
    )

    assert "supplier_credit_unclaimed" not in by_class(session, tenant_id)


def test_the_supplier_credit_entries_order_deterministically(session, business):
    tenant_id = business.tenant.id
    older = supplier_note(session, business, "SG-ORDER-1", "10.00", day="2026-07-01")
    newer = supplier_note(session, business, "SG-ORDER-2", "20.00", day="2026-07-15")
    post_supplier_credit_note(session, tenant_id, older.id)
    post_supplier_credit_note(session, tenant_id, newer.id)

    def reported():
        return [
            row.record_id
            for row in operational_exceptions(session, tenant_id, as_of=AS_OF)
            if row.class_id == "supplier_credit_unclaimed"
        ]

    assert reported() == [older.id, newer.id]
    assert reported() == reported()


def test_the_supplier_credit_classes_are_tenant_scoped(session, business):
    tenant_id = business.tenant.id
    credit = supplier_note(session, business, "SG-TENANT", "10.00")
    post_supplier_credit_note(session, tenant_id, credit.id)
    foreign = create_tenant(session, "Foreign supplier credit derivation tenant")

    assert "supplier_credit_unclaimed" in by_class(session, tenant_id)
    assert by_class(session, foreign.id) == {}


# --- Goods going back the other way (spec 090) -----------------------------


def bought(session, business, *, number="PO-090", quantity="10", received=None):
    """A purchase order line whose goods have arrived."""
    _, line, commitment = order(
        session, business, direction="purchase", number=number, quantity=quantity
    )
    ship(
        session,
        business,
        commitment,
        quantity if received is None else received,
        movement_type="receipt",
    )
    return line, commitment


def return_to_supplier(session, business, commitment, quantity, **kwargs):
    return record_movement(
        session,
        business.tenant.id,
        "supplier_return",
        business.item.id,
        quantity,
        from_location_id=business.location.id,
        commitment_id=commitment.id,
        occurred_at=AS_OF - timedelta(days=2),
        **kwargs,
    )


def supplier_credit_line(
    session, business, order_line, *, number, quantity, unit="pcs"
):
    document, lines = create_manual_document_with_lines(
        session,
        business.tenant.id,
        "supplier_credit_note",
        number,
        business.supplier.id,
        [
            {
                "item_id": business.item.id,
                "quantity": quantity,
                "unit": unit,
                "unit_price": "9.00",
                "gross_amount": "36.00",
                "billed_document_line_id": order_line.id,
            }
        ],
        "36.00",
        document_date="2026-08-25",
    )
    assert document
    return lines[0]


def test_supplier_return_not_credited(session, business):
    tenant_id = business.tenant.id
    line, commitment = bought(session, business, number="PO-090-A")

    # Goods nobody has invoiced need no credit: the company was never charged.
    return_to_supplier(session, business, commitment, 4)
    assert "supplier_return_not_credited" not in by_class(session, tenant_id)

    # The supplier's invoice arrives, and now four went back that nobody has
    # credited.
    bill(
        session, business, line, direction="purchase", number="ER-090-A", quantity="10"
    )
    row = by_class(session, tenant_id)["supplier_return_not_credited"]

    assert row.record_type == "document_line"
    assert row.record_id == line.id
    assert row.causal_values["returned_quantity"] == Decimal("4.0000")
    assert row.causal_values["billed_quantity"] == Decimal("10.0000")
    assert row.causal_values["uncredited_quantity"] == Decimal("4.0000")

    # A credit for part of it reports only the remainder.
    supplier_credit_line(session, business, line, number="SG-090-A", quantity="3")
    assert by_class(session, tenant_id)["supplier_return_not_credited"].causal_values[
        "uncredited_quantity"
    ] == Decimal("1.0000")

    # And one order line never produces both entries.
    rows = by_class(session, tenant_id)
    assert "supplier_credit_not_returned" not in rows


def test_supplier_credit_not_returned(session, business):
    tenant_id = business.tenant.id
    line, commitment = bought(session, business, number="PO-090-B")
    bill(
        session, business, line, direction="purchase", number="ER-090-B", quantity="10"
    )

    # A rebate, an allowance or a price correction has no goods behind it, and
    # this class must never report one.
    supplier_credit_line(session, business, line, number="SG-090-B", quantity="6")
    assert "supplier_credit_not_returned" not in by_class(session, tenant_id)

    # Once goods have started going back, a credit larger than what went is a
    # real difference.
    return_to_supplier(session, business, commitment, 4)
    row = by_class(session, tenant_id)["supplier_credit_not_returned"]

    assert row.record_id == line.id
    assert row.causal_values["credited_quantity"] == Decimal("6.0000")
    assert row.causal_values["returned_quantity"] == Decimal("4.0000")
    assert row.causal_values["unreturned_quantity"] == Decimal("2.0000")


def test_receipt_unbilled_counts_what_is_still_here(session, business):
    tenant_id = business.tenant.id
    billing_history(session, business, lag_days=3, cases=6)
    line, commitment = purchase(session, business, "PO-090-KEPT")
    receive(session, business, commitment, 10, days_ago=60)
    assert line.id

    row = by_class(session, tenant_id)["receipt_unbilled"]
    assert row.causal_values["received_quantity"] == Decimal("10.0000")

    # Four go back, so the company is accruing an invoice for six, not ten.
    return_to_supplier(session, business, commitment, 4)
    row = by_class(session, tenant_id)["receipt_unbilled"]
    assert row.causal_values["received_quantity"] == Decimal("6.0000")
    assert row.causal_values["unbilled_quantity"] == Decimal("6.0000")

    # All of it goes back and there is nothing left to accrue.
    return_to_supplier(session, business, commitment, 6)
    assert "receipt_unbilled" not in by_class(session, tenant_id)


def test_a_return_does_not_unmake_a_receipt(session, business):
    tenant_id = business.tenant.id
    line, commitment = bought(session, business, number="PO-090-RAW", quantity="10")
    bill(
        session,
        business,
        line,
        direction="purchase",
        number="ER-090-RAW",
        quantity="10",
    )

    # Billed ten, received ten: nothing is unreceived.
    assert "billed_not_received" not in by_class(session, tenant_id)

    # Four go back. The supplier still delivered ten, so it is not accused of
    # failing to deliver — what it owes for them is the credit classes' business.
    return_to_supplier(session, business, commitment, 4)
    rows = by_class(session, tenant_id)
    assert "billed_not_received" not in rows
    assert "supplier_return_not_credited" in rows

    # The positive control: billing beyond what arrived still reports at once.
    bill(
        session,
        business,
        line,
        direction="purchase",
        number="ER-090-RAW-2",
        quantity="3",
    )
    assert by_class(session, tenant_id)["billed_not_received"].causal_values[
        "unreceived_quantity"
    ] == Decimal("3.0000")


def test_the_supplier_return_entries_expose_full_shape(session, business):
    tenant_id = business.tenant.id
    line, commitment = bought(session, business, number="PO-090-SHAPE")
    bill(
        session,
        business,
        line,
        direction="purchase",
        number="ER-090-SHAPE",
        quantity="10",
    )
    return_to_supplier(session, business, commitment, 4)

    row = by_class(session, tenant_id)["supplier_return_not_credited"]

    assert row.id == f"exc__supplier_return_not_credited__{line.id}"
    assert row.severity == "high"
    assert row.title == "Returned to supplier and not credited"
    assert row.impact
    assert row.cause_ids == ()
    assert set(row.causal_values) == {
        "returned_quantity",
        "billed_quantity",
        "credited_quantity",
        "uncredited_quantity",
        "unit",
    }
    assert set(row.trace) <= {
        "commitment_id",
        "document_line_id",
        "document_id",
        "source_record_id",
    }
    assert row.trace["document_line_id"] == line.id


def test_the_supplier_return_entries_clear_through_reality(session, business):
    tenant_id = business.tenant.id
    line, commitment = bought(session, business, number="PO-090-CLEARS")
    bill(
        session,
        business,
        line,
        direction="purchase",
        number="ER-090-CLEARS",
        quantity="10",
    )
    return_to_supplier(session, business, commitment, 4)
    assert "supplier_return_not_credited" in by_class(session, tenant_id)

    supplier_credit_line(session, business, line, number="SG-090-CLEARS", quantity="4")

    assert "supplier_return_not_credited" not in by_class(session, tenant_id)


def test_an_unreconcilable_supplier_credit_is_reported_not_judged(session, business):
    tenant_id = business.tenant.id
    line, commitment = bought(session, business, number="PO-090-UNITS")
    bill(
        session,
        business,
        line,
        direction="purchase",
        number="ER-090-UNITS",
        quantity="10",
    )
    return_to_supplier(session, business, commitment, 4)
    assert "supplier_return_not_credited" in by_class(session, tenant_id)

    # A credit in a unit the item cannot reconcile stops the comparison, and the
    # decline is said out loud rather than being silently skipped.
    supplier_credit_line(
        session, business, line, number="SG-090-UNITS", quantity="4", unit="box"
    )
    rows = by_class(session, tenant_id)
    assert "supplier_return_not_credited" not in rows
    assert rows["units_not_comparable"].record_id == business.item.id


def test_both_return_directions_share_one_body(session, business):
    """DR-003: neither side may drift in what "returned" and "credited" mean."""
    import inspect

    from reality.services import exceptions

    for name in (
        "_returned_not_credited_exceptions",
        "_credited_not_returned_exceptions",
        "_supplier_return_not_credited_exceptions",
        "_supplier_credit_not_returned_exceptions",
    ):
        source = inspect.getsource(getattr(exceptions, name))
        assert "_return_exceptions(" in source
        # None of the four computes a difference of its own.
        assert "min(" not in source


def test_the_supplier_return_entries_order_deterministically(session, business):
    tenant_id = business.tenant.id
    first, first_commitment = bought(session, business, number="PO-090-ORDER-1")
    second, second_commitment = bought(session, business, number="PO-090-ORDER-2")
    for line, commitment, number in (
        (first, first_commitment, "ER-090-ORDER-1"),
        (second, second_commitment, "ER-090-ORDER-2"),
    ):
        bill(
            session, business, line, direction="purchase", number=number, quantity="10"
        )
        return_to_supplier(session, business, commitment, 4)

    def reported():
        return [
            row.record_id
            for row in operational_exceptions(session, tenant_id, as_of=AS_OF)
            if row.class_id == "supplier_return_not_credited"
        ]

    assert set(reported()) == {first.id, second.id}
    assert reported() == reported()


def test_the_supplier_return_classes_are_tenant_scoped(session, business):
    tenant_id = business.tenant.id
    line, commitment = bought(session, business, number="PO-090-TENANT")
    bill(
        session,
        business,
        line,
        direction="purchase",
        number="ER-090-TENANT",
        quantity="10",
    )
    return_to_supplier(session, business, commitment, 4)
    foreign = create_tenant(session, "Foreign supplier return tenant")

    assert "supplier_return_not_credited" in by_class(session, tenant_id)
    assert by_class(session, foreign.id) == {}


# --- The invoice nobody booked (spec 092) ----------------------------------


def unbooked(session, business, number, amount="100.00", *, kind="sales_invoice", day):
    party = business.customer if kind == "sales_invoice" else business.supplier
    return create_document(
        session,
        business.tenant.id,
        kind,
        number,
        party.id,
        amount,
        document_date=day,
    )


def booking_history(
    session, business, *, kind="sales_invoice", lag_days=2, cases=6, prefix="A"
):
    """A tenant that normally books this kind of document `lag_days` after recording it."""
    post = post_sales_invoice if kind == "sales_invoice" else post_supplier_invoice
    for index in range(cases):
        recorded = AS_OF - timedelta(days=120 - index * 5)
        document = unbooked(
            session,
            business,
            f"{'RE' if kind == 'sales_invoice' else 'ER'}-NORM-{prefix}{index}",
            "10.00",
            kind=kind,
            day=recorded.date().isoformat(),
        )
        post(
            session,
            business.tenant.id,
            document.id,
            effective_at=recorded + timedelta(days=lag_days),
        )


def test_sales_invoice_unposted(session, business):
    tenant_id = business.tenant.id
    forgotten = unbooked(
        session, business, "RE-092-FORGOTTEN", "400.00", day="2026-06-01"
    )

    # Fewer than five booked invoices is no rhythm, so nothing is claimed.
    booking_history(session, business, cases=4)
    assert "sales_invoice_unposted" not in by_class(session, tenant_id)

    booking_history(session, business, cases=2, prefix="B")
    row = by_class(session, tenant_id)["sales_invoice_unposted"]

    assert row.record_type == "document"
    assert row.record_id == forgotten.id
    assert row.causal_values["gross_amount"] == Decimal("400.0000")
    assert row.causal_values["threshold_days"] == 14

    # One recorded yesterday is inside the norm and says nothing.
    unbooked(session, business, "RE-092-YESTERDAY", "5.00", day="2026-08-30")
    assert (
        by_class(session, tenant_id)["sales_invoice_unposted"].record_id == forgotten.id
    )

    # Booking it clears the entry with no manual step.
    post_sales_invoice(session, tenant_id, forgotten.id)
    assert "sales_invoice_unposted" not in by_class(session, tenant_id)


def test_supplier_invoice_unposted(session, business):
    tenant_id = business.tenant.id
    booking_history(session, business, kind="supplier_invoice", cases=6)
    forgotten = unbooked(
        session,
        business,
        "ER-092-FORGOTTEN",
        "700.00",
        kind="supplier_invoice",
        day="2026-06-01",
    )

    row = by_class(session, tenant_id)["supplier_invoice_unposted"]

    assert row.record_id == forgotten.id
    assert row.causal_values["gross_amount"] == Decimal("700.0000")

    post_supplier_invoice(session, tenant_id, forgotten.id)
    assert "supplier_invoice_unposted" not in by_class(session, tenant_id)


def test_each_document_type_learns_its_own_rhythm(session, business):
    """FR-003: one side's rhythm never judges another's."""
    from reality.services import exceptions

    tenant_id = business.tenant.id
    booking_history(session, business, kind="sales_invoice", cases=6, prefix="RHY")
    unbooked(
        session,
        business,
        "ER-092-SLOW",
        "300.00",
        kind="supplier_invoice",
        day="2026-06-01",
    )

    # A prompt sales-invoice rhythm says nothing about supplier invoices, so the
    # supplier side claims no norm and reports nothing.
    assert (
        exceptions._posting_threshold(
            session, tenant_id, "sales_invoice", "sales_revenue"
        )
        is not None
    )
    assert (
        exceptions._posting_threshold(
            session, tenant_id, "supplier_invoice", "accounts_payable"
        )
        is None
    )
    assert "supplier_invoice_unposted" not in by_class(session, tenant_id)

    # The positive control: its own history gives that side a norm at once.
    booking_history(session, business, kind="supplier_invoice", cases=6, prefix="RHY")
    assert "supplier_invoice_unposted" in by_class(session, tenant_id)


def test_a_reversed_posting_is_not_an_unbooked_one(session, business):
    tenant_id = business.tenant.id
    booking_history(session, business, cases=6, prefix="REV")
    booked = unbooked(session, business, "RE-092-REVERSED", "200.00", day="2026-06-01")
    post_sales_invoice(session, tenant_id, booked.id)
    group = session.scalar(
        select(LedgerEntry.posting_group_id).where(
            LedgerEntry.tenant_id == tenant_id,
            LedgerEntry.document_id == booked.id,
        )
    )
    reverse_ledger_posting_group(
        session, tenant_id, group, reason="Issued to the wrong customer"
    )

    # Somebody booked it and then deliberately unbooked it. That is not the same
    # as nobody having got round to it, and the reversing entries carry no
    # document reference, so it still reads as booked.
    reported = {
        row.record_id
        for row in operational_exceptions(session, tenant_id, as_of=AS_OF)
        if row.class_id == "sales_invoice_unposted"
    }
    assert booked.id not in reported

    # The positive control: a genuinely unbooked invoice on the same tenant does
    # report, so the silence above is the rule speaking.
    never = unbooked(session, business, "RE-092-NEVER", "50.00", day="2026-06-01")
    assert never.id in {
        row.record_id
        for row in operational_exceptions(session, tenant_id, as_of=AS_OF)
        if row.class_id == "sales_invoice_unposted"
    }


def test_a_document_with_no_date_says_nothing(session, business):
    """A document stating no date is not judged; one stating a bad date is refused.

    The two used to be the same case, because any text at all could be stored and
    every reader had to decide again whether it was a date (spec 234).
    """
    tenant_id = business.tenant.id
    booking_history(session, business, cases=6, prefix="DATE")
    undated = unbooked(session, business, "RE-092-UNDATED", "90.00", day="")

    reported = {
        row.record_id
        for row in operational_exceptions(session, tenant_id, as_of=AS_OF)
        if row.class_id == "sales_invoice_unposted"
    }
    assert undated.id not in reported

    # The positive control: the same amount with a readable date reports.
    dated = unbooked(session, business, "RE-092-DATED", "90.00", day="2026-06-01")
    assert dated.id in {
        row.record_id
        for row in operational_exceptions(session, tenant_id, as_of=AS_OF)
        if row.class_id == "sales_invoice_unposted"
    }

    # A day the calendar does not have never reaches the column.
    with pytest.raises(core.InvalidOperation, match="YYYY-MM-DD"):
        unbooked(session, business, "RE-092-BAD", "90.00", day="whenever")
    session.rollback()


def test_the_four_unposted_sides_stay_apart(session, business):
    tenant_id = business.tenant.id
    booking_history(session, business, kind="sales_invoice", cases=6, prefix="SEP")
    booking_history(session, business, kind="supplier_invoice", cases=6, prefix="SEP")
    posting_history(session, business, cases=6, prefix="SEP")
    supplier_posting_history(session, business, cases=6, prefix="SEP")

    documents = {
        "sales_invoice_unposted": unbooked(
            session, business, "RE-092-SEP", day="2026-06-01"
        ).id,
        "supplier_invoice_unposted": unbooked(
            session, business, "ER-092-SEP", kind="supplier_invoice", day="2026-06-01"
        ).id,
        "credit_note_unposted": note(
            session, business, "GS-092-SEP", "40.00", day="2026-06-01"
        ).id,
        "supplier_credit_unposted": supplier_note(
            session, business, "SG-092-SEP", "40.00", day="2026-06-01"
        ).id,
    }

    reported: dict[str, set[str]] = {}
    for row in operational_exceptions(session, tenant_id, as_of=AS_OF):
        if row.class_id in documents:
            reported.setdefault(row.class_id, set()).add(row.record_id)

    # Each document is reported by exactly one class, and by its own.
    for class_id, document_id in documents.items():
        assert document_id in reported[class_id]
        for other, ids in reported.items():
            if other != class_id:
                assert document_id not in ids


def test_the_unposted_invoice_entries_expose_full_shape(session, business):
    tenant_id = business.tenant.id
    booking_history(session, business, cases=6, prefix="SHAPE")
    forgotten = unbooked(session, business, "RE-092-SHAPE", "400.00", day="2026-06-01")

    row = by_class(session, tenant_id)["sales_invoice_unposted"]

    assert row.id == f"exc__sales_invoice_unposted__{forgotten.id}"
    assert row.severity == "high"
    assert row.title and row.impact
    assert row.cause_ids == ()
    assert set(row.causal_values) == {
        "gross_amount",
        "currency",
        "standing_for_days",
        "threshold_days",
        "norm_days",
    }
    assert set(row.trace) <= {"document_id", "source_record_id"}
    assert row.trace["document_id"] == forgotten.id


def test_the_unposted_invoice_entries_order_deterministically(session, business):
    tenant_id = business.tenant.id
    booking_history(session, business, cases=6, prefix="ORDER")
    older = unbooked(session, business, "RE-092-OLDER", "10.00", day="2026-05-01")
    newer = unbooked(session, business, "RE-092-NEWER", "20.00", day="2026-06-01")

    def reported():
        return [
            row.record_id
            for row in operational_exceptions(session, tenant_id, as_of=AS_OF)
            if row.class_id == "sales_invoice_unposted"
        ]

    assert reported() == [older.id, newer.id]
    assert reported() == reported()


def test_the_unposted_invoice_classes_are_tenant_scoped(session, business):
    tenant_id = business.tenant.id
    booking_history(session, business, cases=6, prefix="TENANT")
    unbooked(session, business, "RE-092-TENANT", "10.00", day="2026-06-01")
    foreign = create_tenant(session, "Foreign unposted tenant")

    assert "sales_invoice_unposted" in by_class(session, tenant_id)
    assert by_class(session, foreign.id) == {}


def test_all_four_unposted_classes_share_one_body():
    """DR-003: none of the four may drift in what "booked" means."""
    import inspect

    from reality.services import exceptions

    for name in (
        "_credit_note_unposted_exceptions",
        "_supplier_credit_unposted_exceptions",
        "_sales_invoice_unposted_exceptions",
        "_supplier_invoice_unposted_exceptions",
    ):
        source = inspect.getsource(getattr(exceptions, name))
        assert "_unposted_document_exceptions(" in source
        # None of the four asks the ledger anything for itself.
        assert "account_balance" not in source


def test_a_class_and_its_operation_agree_on_booked():
    """FR-015: the class asks the account its own posting operation guards on."""
    import inspect

    from reality.services import core, exceptions

    for constant, poster in (
        (exceptions.SALES_INVOICE, core.post_sales_invoice),
        (exceptions.SUPPLIER_INVOICE, core.post_supplier_invoice),
        (exceptions.SALES_CREDIT, core.post_sales_credit_note),
        (exceptions.SUPPLIER_CREDIT, core.post_supplier_credit_note),
    ):
        _document_type, account = constant
        guard = next(
            line
            for line in inspect.getsource(poster).splitlines()
            if "account_balance(" in line
        )
        assert f'"{account}"' in guard


# --- When the other side says a new date (spec 093) ------------------------


def late_promise(session, business, *, kind="supplier_delivery", quantity=10):
    """A promise due before the queue is read, so it is already overdue."""
    return create_commitment(
        session,
        business.tenant.id,
        kind,
        business.supplier.id if kind == "supplier_delivery" else business.company.id,
        business.company.id if kind == "supplier_delivery" else business.customer.id,
        business.item.id,
        business.location.id,
        quantity,
        AS_OF - timedelta(days=20),
    )


def test_a_revised_promise_is_judged_by_its_new_date(session, business):
    tenant_id = business.tenant.id
    commitment = late_promise(session, business)
    assert "overdue_incoming_supplier_commitment" in by_class(session, tenant_id)

    # The supplier acknowledges a later day. It is not late until that day.
    revise_commitment(session, tenant_id, commitment.id, AS_OF + timedelta(days=5))
    assert "overdue_incoming_supplier_commitment" not in by_class(session, tenant_id)

    # The positive control: once the revised date passes it is overdue again,
    # so the revision moved the judgement rather than removing it.
    later = by_class(session, tenant_id, as_of=AS_OF + timedelta(days=10))
    assert "overdue_incoming_supplier_commitment" in later


def test_a_revision_cannot_buy_silence(session, business):
    tenant_id = business.tenant.id
    commitment = late_promise(session, business)
    original = commitment.due_at
    before = by_class(session, tenant_id)["overdue_incoming_supplier_commitment"]
    assert before.cause_ids == ()

    revise_commitment(session, tenant_id, commitment.id, AS_OF - timedelta(days=5))
    row = by_class(session, tenant_id)["overdue_incoming_supplier_commitment"]

    # Late against a date the supplier itself chose, having already moved it.
    assert row.cause_ids == ("promise_was_revised",)
    assert row.causal_values["due_at"] == AS_OF - timedelta(days=5)
    assert row.causal_values["originally_due_at"] == original
    assert row.causal_values["times_revised"] == 1

    # The entry is not suppressed and nothing else about it moved.
    assert row.severity == before.severity
    assert row.record_id == before.record_id
    assert (
        row.causal_values["remaining_quantity"]
        == before.causal_values["remaining_quantity"]
    )
    assert set(row.trace) == set(before.trace)


def test_both_directions_can_be_revised(session, business):
    tenant_id = business.tenant.id
    stock(session, business, 100)
    outgoing = late_promise(session, business, kind="customer_delivery")
    assert "overdue_outgoing_customer_commitment" in by_class(session, tenant_id)

    revise_commitment(session, tenant_id, outgoing.id, AS_OF + timedelta(days=5))
    assert "overdue_outgoing_customer_commitment" not in by_class(session, tenant_id)

    # And it says so when the agreed date passes too.
    later = by_class(session, tenant_id, as_of=AS_OF + timedelta(days=10))
    assert later["overdue_outgoing_customer_commitment"].cause_ids == (
        "insufficient_reservation",
        "promise_was_revised",
    )


def test_a_dated_promise_is_no_longer_a_stalled_order(session, business):
    tenant_id = business.tenant.id
    history(session, business, lag_days=1, cases=6)
    undated = undated_promise(session, business, age_days=60)
    assert by_class(session, tenant_id)["order_stalled"].record_id == undated.id

    # Somebody states a date, so it is a dated order from now on.
    revise_commitment(session, tenant_id, undated.id, AS_OF + timedelta(days=30))

    rows = by_class(session, tenant_id)
    assert "order_stalled" not in rows
    assert "overdue_outgoing_customer_commitment" not in rows


def test_revised_promises_order_deterministically(session, business):
    tenant_id = business.tenant.id
    first = late_promise(session, business)
    second = late_promise(session, business)
    revise_commitment(session, tenant_id, second.id, AS_OF - timedelta(days=1))

    def reported():
        return [
            row.record_id
            for row in operational_exceptions(session, tenant_id, as_of=AS_OF)
            if row.class_id == "overdue_incoming_supplier_commitment"
        ]

    # Sorted by the date in force, so the revised one comes last.
    assert reported() == [first.id, second.id]
    assert reported() == reported()


def test_one_rule_answers_the_date_in_force():
    """DR-003: no class works out the date in force for itself."""
    import inspect

    from reality.services import exceptions

    asking = {
        name
        for name, function in vars(exceptions).items()
        if inspect.isfunction(function)
        and function.__module__ == exceptions.__name__
        and "commitment_due_at(" in inspect.getsource(function)
    }

    # Exactly one function asks, and it is the helper that delegates to the one
    # service-layer rule. Every class reads the date through it.
    assert asking == {"_promise_due_at"}


# --- A fee is a charge, not a smaller credit (spec 095) --------------------


def test_a_restocking_fee_is_a_charge_not_a_smaller_credit(session, business):
    """Both recordings, in one test so neither can change unread.

    The second assertion is the one that matters. A credit for fewer units than
    came back reports the difference, that behaviour is correct, and it looks
    exactly like the bug somebody would file as "false entry on restocking
    fees". Removing it would be the wrong fix, and this is what stops that.
    """
    tenant_id = business.tenant.id
    stock(session, business, 200)

    # Recorded the way the product wants it: credit the goods that came back,
    # charge for what is being kept. The charge names no order line, because it
    # is not credit for goods.
    _, kept, commitment = order(session, business, number="SO-095-FEE")
    ship(session, business, commitment, 10)
    bill(session, business, kept, number="RE-095-FEE", quantity="10")
    send_back(session, business, commitment, 10)
    document, lines = create_manual_document_with_lines(
        session,
        tenant_id,
        "credit_note",
        "GS-095-FEE",
        business.customer.id,
        [
            {
                "item_id": business.item.id,
                "quantity": "10",
                "unit": "pcs",
                "unit_price": "9.00",
                "gross_amount": "90.00",
                "billed_document_line_id": kept.id,
            },
            {
                "description": "Restocking fee",
                "quantity": "1",
                "unit": "pcs",
                "unit_price": "-18.00",
                "gross_amount": "-18.00",
                "line_type": "charge",
            },
        ],
        "72.00",
        document_date="2026-08-25",
    )

    reported = {
        row.record_id
        for row in operational_exceptions(session, tenant_id, as_of=AS_OF)
        if row.class_id == "returned_not_credited"
    }
    assert kept.id not in reported
    # And the customer receives the reduced amount, stated rather than derived.
    assert Decimal(document.gross_amount) == Decimal("72.0000")
    assert len(lines) == 2

    # Recorded the other way, on its own order line: a credit note for eight
    # says eight were credited, and two are uncredited. That is a true statement
    # about the document, and nothing will ever clear it — which is why the
    # guidance tells an operator to record the fee as a charge instead.
    _, short, other = order(session, business, number="SO-095-SHORT")
    ship(session, business, other, 10)
    bill(session, business, short, number="RE-095-SHORT", quantity="10")
    send_back(session, business, other, 10)
    credit(session, business, short, number="GS-095-SHORT", quantity="8")

    row = next(
        entry
        for entry in operational_exceptions(session, tenant_id, as_of=AS_OF)
        if entry.class_id == "returned_not_credited" and entry.record_id == short.id
    )
    assert row.causal_values["uncredited_quantity"] == Decimal("2.0000")


# --- Eighty of the hundred (spec 097) --------------------------------------


def test_a_shrunk_promise_is_judged_by_what_is_in_force(session, business):
    tenant_id = business.tenant.id
    commitment = late_promise(session, business, quantity=100)
    ship(session, business, commitment, 80, movement_type="receipt")

    # Twenty still missing against the hundred that was ordered.
    row = by_class(session, tenant_id)["overdue_incoming_supplier_commitment"]
    assert row.causal_values["committed_quantity"] == Decimal(100)
    assert row.causal_values["remaining_quantity"] == Decimal(20)

    # The supplier says eighty is all there is. Nothing is missing any more, and
    # the entry goes — not because time passed, but because the promise did.
    revise_commitment(session, tenant_id, commitment.id, quantity=80)

    assert "overdue_incoming_supplier_commitment" not in by_class(session, tenant_id)

    # The positive control: a promise revised to ninety still owes ten, and the
    # entry measures against ninety rather than the hundred it was made with.
    other = late_promise(session, business, quantity=100)
    ship(session, business, other, 80, movement_type="receipt")
    revise_commitment(session, tenant_id, other.id, quantity=90)
    row = by_class(session, tenant_id)["overdue_incoming_supplier_commitment"]
    assert row.record_id == other.id
    assert row.causal_values["committed_quantity"] == Decimal(90)
    assert row.causal_values["remaining_quantity"] == Decimal(10)


def test_one_rule_answers_the_quantity_in_force():
    """DR-003: no class works out what a promise is for."""
    import inspect

    from reality.services import exceptions

    asking = {
        name
        for name, function in vars(exceptions).items()
        if inspect.isfunction(function)
        and function.__module__ == exceptions.__name__
        and "commitment_quantity(" in inspect.getsource(function)
    }

    assert asking == {"_promise_quantity"}


# ---------------------------------------------------------------------------
# Spec 099: the half of a return's life before the goods arrive.


def announce(
    session, business, commitment, quantity, *, expected_by=None, at=None, reference=""
):
    return core.announce_customer_return(
        session,
        business.tenant.id,
        commitment.id,
        quantity,
        reference=reference,
        reason="Wrong colour",
        expected_by=expected_by,
        announced_at=at or AS_OF - timedelta(days=20),
    )


def arrive(session, business, commitment, announcement, quantity, *, at=None):
    return record_movement(
        session,
        business.tenant.id,
        "return",
        business.item.id,
        quantity,
        to_location_id=business.location.id,
        commitment_id=commitment.id,
        return_announcement_id=announcement.id,
        occurred_at=at or AS_OF - timedelta(days=1),
    )


def arrived_announcements(session, business, count, *, quantity=1):
    """`count` announcements that arrived a day after they were announced.

    The learned rule needs finished cases to learn from, and only finished ones
    count: one still waiting is what the class exists to judge.
    """
    stock(session, business)
    # Numbered from what already exists, so a test may build history in two
    # steps without colliding with its own earlier orders.
    start = len(core.return_announcements(session, business.tenant.id))
    for index in range(start, start + count):
        _, _, commitment = order(session, business, number=f"SO-099-H{index}")
        ship(session, business, commitment, quantity)
        announced = announce(
            session,
            business,
            commitment,
            quantity,
            at=AS_OF - timedelta(days=60 + index),
        )
        arrive(
            session,
            business,
            commitment,
            announced,
            quantity,
            at=AS_OF - timedelta(days=59 + index),
        )


def test_announced_return_not_arrived(session, business):
    """Two ways in, and the entry says which one spoke."""
    stock(session, business)
    _, _, commitment = order(session, business, number="SO-099-A")
    ship(session, business, commitment, 5)

    # A day the customer stated, still in the future: nothing to report.
    announced = announce(
        session,
        business,
        commitment,
        2,
        expected_by=AS_OF + timedelta(days=3),
        reference="RMA-4711",
    )
    assert "announced_return_not_arrived" not in by_class(session, business.tenant.id)

    # The same announcement with the day behind it: reported, judged by the
    # customer's own word, with no learned norm claimed.
    core.withdraw_return_announcement(session, business.tenant.id, announced.id)
    late = announce(
        session,
        business,
        commitment,
        2,
        expected_by=AS_OF - timedelta(days=4),
        reference="RMA-4712",
    )
    row = by_class(session, business.tenant.id)["announced_return_not_arrived"]
    assert row.record_type == "return_announcement"
    assert row.record_id == late.id
    assert row.causal_values["outstanding_quantity"] == Decimal(2)
    assert row.causal_values["judged_by"] == "the day the customer stated"
    assert row.causal_values["reference"] == "RMA-4712"
    assert row.causal_values["threshold_days"] is None
    assert row.causal_values["norm_days"] is None

    # The goods arriving ends it, with nothing stored and no manual step.
    arrive(session, business, commitment, late, 2)
    assert "announced_return_not_arrived" not in by_class(session, business.tenant.id)
    settled = {
        row.id: row.status
        for row in core.return_announcements(
            session, business.tenant.id, commitment_id=commitment.id
        )
    }
    assert settled == {announced.id: "withdrawn", late.id: "fulfilled"}


def test_an_announcement_with_no_stated_day_is_judged_by_the_learned_rhythm(
    session, business
):
    arrived_announcements(session, business, 5)
    _, _, commitment = order(session, business, number="SO-099-B")
    ship(session, business, commitment, 5)

    # Announced today: well inside any rhythm.
    fresh = announce(session, business, commitment, 2, at=AS_OF - timedelta(hours=2))
    assert "announced_return_not_arrived" not in by_class(session, business.tenant.id)
    core.withdraw_return_announcement(session, business.tenant.id, fresh.id)

    # Announced two months ago, with five one-day arrivals behind it: the norm
    # is a day, three times over is three days, and the floor is a fortnight.
    stale = announce(session, business, commitment, 2, at=AS_OF - timedelta(days=30))
    row = by_class(session, business.tenant.id)["announced_return_not_arrived"]
    assert row.record_id == stale.id
    assert row.causal_values["judged_by"] == "this company's own rhythm"
    # Three times a one-day median is three days, so the fortnight floor is what
    # actually decides. `norm_days` divides the threshold back out, the same way
    # Return not dealt with reports it, so it names the floor rather than the
    # median whenever the floor is what spoke.
    assert row.causal_values["threshold_days"] == 14
    assert row.causal_values["norm_days"] == 4
    assert row.causal_values["waiting_for_days"] == 30


def test_an_announcement_without_a_date_or_a_history_is_not_judged(session, business):
    """Four arrivals is not a lenient threshold, it is a rule that cannot speak."""
    arrived_announcements(session, business, 4)
    _, _, commitment = order(session, business, number="SO-099-C")
    ship(session, business, commitment, 5)
    announce(session, business, commitment, 2, at=AS_OF - timedelta(days=200))

    assert "announced_return_not_arrived" not in by_class(session, business.tenant.id)

    # The positive control: one more finished case and the same announcement is
    # judged, so the silence above was the minimum speaking and not the class
    # being absent.
    arrived_announcements(session, business, 1)
    assert "announced_return_not_arrived" in by_class(session, business.tenant.id)


def test_the_announcement_threshold_is_the_learned_rule(session, business):
    """Same rule as every other learned expectation, and never a shared history."""
    from reality.services.exceptions import (
        LEARNED_MINIMUM,
        LEARNED_MULTIPLE,
        UNARRIVED_ANNOUNCEMENT_FLOOR,
        UNRESOLVED_RETURN_FLOOR,
        _announcement_arrival_threshold,
    )

    assert UNARRIVED_ANNOUNCEMENT_FLOOR == UNRESOLVED_RETURN_FLOOR

    assert _announcement_arrival_threshold(session, business.tenant.id) is None
    arrived_announcements(session, business, LEARNED_MINIMUM - 1)
    assert _announcement_arrival_threshold(session, business.tenant.id) is None
    arrived_announcements(session, business, 1)
    learned = _announcement_arrival_threshold(session, business.tenant.id)
    assert learned == max(
        timedelta(days=1) * LEARNED_MULTIPLE, UNARRIVED_ANNOUNCEMENT_FLOOR
    )

    # A second tenant's history is its own: the rule is shared, never the cases.
    other = create_tenant(session, "Other GmbH")
    assert _announcement_arrival_threshold(session, other.id) is None


def test_a_withdrawn_announcement_is_not_reported(session, business):
    arrived_announcements(session, business, 5)
    _, _, commitment = order(session, business, number="SO-099-D")
    ship(session, business, commitment, 5)
    announcement = announce(
        session, business, commitment, 2, at=AS_OF - timedelta(days=60)
    )
    assert "announced_return_not_arrived" in by_class(session, business.tenant.id)

    core.withdraw_return_announcement(
        session, business.tenant.id, announcement.id, note="Customer keeps them"
    )

    assert "announced_return_not_arrived" not in by_class(session, business.tenant.id)


# ---------------------------------------------------------------------------
# Spec 100: what a missing reference actually does. Two directions, recorded.


def test_a_missing_billing_reference_makes_the_queue_cry_wolf(session, business):
    """A class that concludes from absence reports work that was actually done."""
    stock(session, business)
    _, line, commitment = order(session, business, number="SO-100-A")
    ship(session, business, commitment, 10)
    _, billed = bill(session, business, line, number="RE-100-A", quantity="10")

    # Everything shipped and everything billed: the queue is quiet.
    assert "shipped_not_billed" not in by_class(session, business.tenant.id)

    # The same invoice line, with the reference removed and nothing else changed.
    billed.billed_document_line_id = None
    session.commit()

    row = by_class(session, business.tenant.id)["shipped_not_billed"]
    # It now reports ten pieces shipped and unbilled. They were billed. This is
    # the cheaper of the two directions — a queue that cries wolf stops being
    # believed — and it is why the gate exists.
    assert row.record_id == line.id
    assert row.causal_values["unbilled_quantity"] == Decimal(10)


def test_a_missing_billing_reference_makes_the_queue_go_blind(session, business):
    """A class that starts from the reference never looks at the record."""
    stock(session, business)
    _, line, _ = order(session, business, direction="purchase", number="PO-100-B")
    _, billed = bill(
        session,
        business,
        line,
        direction="purchase",
        number="ER-100-B",
        quantity="10",
    )

    # Ten billed and nothing received: the supplier has invoiced goods that
    # never arrived, and the queue says so.
    row = by_class(session, business.tenant.id)["billed_not_received"]
    assert row.record_id == line.id
    assert row.causal_values["unreceived_quantity"] == Decimal(10)

    # The same invoice line, with the reference removed and nothing else changed.
    billed.billed_document_line_id = None
    session.commit()

    # Silence. The company is being billed for goods that never arrived and
    # nothing reports it. This is the direction worth losing sleep over: the
    # class did not get it wrong, it never looked.
    assert "billed_not_received" not in by_class(session, business.tenant.id)


# ---------------------------------------------------------------------------
# Spec 107: a hold nobody lifted.


def lifted_holds(session, business, count, *, party=False, days=1):
    """`count` holds raised and lifted `days` apart, so the rule has a rhythm.

    Only lifted holds teach it: one still standing is what the class exists to
    judge, so counting it would let a backlog raise its own bar.
    """
    for index in range(count):
        raised = AS_OF - timedelta(days=200 + index * 3)
        if party:
            target = create_party(
                session, business.tenant.id, f"Lifted Party {index}", "customer"
            )
            hold = core.hold_party_delivery(
                session, business.tenant.id, target.id, "credit_check"
            )
        else:
            commitment = customer_commitment(
                session, business, 1, AS_OF + timedelta(days=30)
            )
            hold = core.hold_commitment(
                session, business.tenant.id, commitment.id, "credit_check"
            )
        hold.created_at = raised
        hold.released_at = raised + timedelta(days=days)
        session.commit()


def test_commitment_hold_unreleased(session, business):
    """A credit check somebody finished, and a hold nobody lifted."""
    lifted_holds(session, business, 5)
    stock(session, business)
    _, line, commitment = order(session, business, number="SO-107-A")
    reported_before = set(by_class(session, business.tenant.id))
    hold = core.hold_commitment(
        session,
        business.tenant.id,
        commitment.id,
        "credit_check",
        note="Waiting on the credit report",
    )
    hold.created_at = AS_OF - timedelta(days=60)
    session.commit()

    row = by_class(session, business.tenant.id)["commitment_hold_unreleased"]

    assert row.record_type == "commitment_hold"
    assert row.record_id == hold.id
    assert row.severity == "normal"
    # Exactly what somebody recorded, and nothing invented.
    assert row.causal_values["reason_code"] == "credit_check"
    assert row.causal_values["note"] == "Waiting on the credit report"
    assert row.causal_values["raised_by"] == "human"
    assert row.causal_values["standing_for_days"] == 60
    # What the hold is holding back: a formality somebody forgot looks nothing
    # like a block on a real backlog.
    assert row.causal_values["held_quantity"] == Decimal(10)
    assert row.causal_values["unit"] == "pcs"
    assert row.trace["commitment_id"] == commitment.id
    assert line.id  # the promise came from an order line, which gives the unit

    # A hold suppresses nothing: whatever the queue said about this promise
    # before it was held, it still says, because a hold means somebody is
    # dealing with it and not that it is fine.
    assert reported_before <= set(by_class(session, business.tenant.id))
    assert reported_before

    # Lifting it ends the entry, with nothing stored and no manual step.
    core.release_commitment_hold(session, business.tenant.id, commitment.id)
    assert "commitment_hold_unreleased" not in by_class(session, business.tenant.id)

    # A hold on a promise nobody is waiting for holds nothing back, so nobody
    # could clear it by doing anything useful. Since spec 108 cancelling a
    # promise releases its holds, so the ordinary path no longer produces one.
    closed = customer_commitment(session, business, 3, AS_OF - timedelta(days=2))
    dangling = core.hold_commitment(
        session, business.tenant.id, closed.id, "manual_review"
    )
    dangling.created_at = AS_OF - timedelta(days=90)
    session.commit()
    core.cancel_commitment(session, business.tenant.id, closed.id)
    assert dangling.released_at is not None
    assert "commitment_hold_unreleased" not in by_class(session, business.tenant.id)

    # The skip still has a job: a tenant that was running before spec 108 can
    # hold a row in exactly this state, and nothing tidies it. Reconstructed
    # here rather than left untested, so the skip cannot be removed by accident.
    dangling.released_at = None
    session.commit()
    assert closed.status == "cancelled"
    assert core.active_commitment_hold(session, business.tenant.id, closed.id)
    assert "commitment_hold_unreleased" not in by_class(session, business.tenant.id)


def test_party_hold_unreleased(session, business):
    """A customer nobody can ship to, quietly, for as long as it stands."""
    lifted_holds(session, business, 5, party=True)
    stock(session, business)
    _, _, first = order(session, business, number="SO-107-B")
    order(session, business, number="SO-107-C")
    hold = core.hold_party_delivery(
        session,
        business.tenant.id,
        business.customer.id,
        "compliance",
        note="Sanctions screening",
    )
    hold.created_at = AS_OF - timedelta(days=45)
    session.commit()

    row = by_class(session, business.tenant.id)["party_hold_unreleased"]

    assert row.record_type == "party_hold"
    assert row.record_id == hold.id
    # More serious than a promise hold: it refuses every shipment to this
    # customer, including orders taken after it was raised.
    assert row.severity == "high"
    assert row.causal_values["hold_type"] == "delivery"
    assert row.causal_values["reason_code"] == "compliance"
    assert row.causal_values["note"] == "Sanctions screening"
    assert row.causal_values["standing_for_days"] == 45
    # A count, never a sum: quantities across different items do not add up.
    assert row.causal_values["blocked_commitments"] == 2
    assert "held_quantity" not in row.causal_values
    assert row.trace["party_id"] == business.customer.id

    # It really does refuse a shipment, which is what the count is about.
    with pytest.raises(core.InvalidOperation, match="delivery hold"):
        ship(session, business, first, 1)

    # A hold blocking nothing is still reported, because it will refuse the
    # next order too.
    quiet = create_party(session, business.tenant.id, "Quiet GmbH", "customer")
    idle = core.hold_party_delivery(
        session, business.tenant.id, quiet.id, "manual_review"
    )
    idle.created_at = AS_OF - timedelta(days=45)
    session.commit()
    reported = {
        entry.record_id: entry.causal_values["blocked_commitments"]
        for entry in operational_exceptions(session, business.tenant.id, as_of=AS_OF)
        if entry.class_id == "party_hold_unreleased"
    }
    assert reported == {hold.id: 2, idle.id: 0}

    # Lifting it ends the entry.
    core.release_party_delivery_hold(session, business.tenant.id, quiet.id)
    assert idle.id not in {
        entry.record_id
        for entry in operational_exceptions(session, business.tenant.id, as_of=AS_OF)
        if entry.class_id == "party_hold_unreleased"
    }


def test_a_hold_is_judged_by_this_company_s_own_rhythm(session, business):
    """The floor, the rhythm, and the silence below the minimum."""
    from reality.services.exceptions import UNLIFTED_HOLD_FLOOR

    assert UNLIFTED_HOLD_FLOOR == timedelta(days=7)

    # Four lifted holds is not a lenient threshold, it is a rule that cannot
    # speak. Nothing is reported however long the fifth has stood.
    lifted_holds(session, business, 4)
    ancient = customer_commitment(session, business, 2, AS_OF + timedelta(days=30))
    hold = core.hold_commitment(session, business.tenant.id, ancient.id, "compliance")
    hold.created_at = AS_OF - timedelta(days=300)
    session.commit()
    assert "commitment_hold_unreleased" not in by_class(session, business.tenant.id)

    # The positive control: one more lifted hold and the same one is judged, so
    # the silence above was the minimum speaking rather than the class being
    # absent.
    lifted_holds(session, business, 1)
    row = by_class(session, business.tenant.id)["commitment_hold_unreleased"]
    assert row.record_id == hold.id
    # Three times a one-day median is three days, so the week floor is what
    # actually decides, and norm_days divides the threshold back out.
    assert row.causal_values["threshold_days"] == 7

    # A hold inside the floor says nothing.
    fresh = customer_commitment(session, business, 2, AS_OF + timedelta(days=30))
    recent = core.hold_commitment(
        session, business.tenant.id, fresh.id, "address_clarification"
    )
    recent.created_at = AS_OF - timedelta(days=3)
    session.commit()
    assert recent.id not in {
        entry.record_id
        for entry in operational_exceptions(session, business.tenant.id, as_of=AS_OF)
        if entry.class_id == "commitment_hold_unreleased"
    }


def test_each_hold_kind_learns_its_own_rhythm(session, business):
    """A rule is shared; a history never is, between kinds or between tenants."""
    from reality.db.core import CommitmentHold, PartyHold
    from reality.services.exceptions import _lifted_hold_threshold

    tenant_id = business.tenant.id
    assert _lifted_hold_threshold(session, tenant_id, CommitmentHold) is None
    assert _lifted_hold_threshold(session, tenant_id, PartyHold) is None

    # Five lifted promise holds teach the promise rule and say nothing about
    # the party rule, which is a different process with different people.
    lifted_holds(session, business, 5)
    assert _lifted_hold_threshold(session, tenant_id, CommitmentHold) is not None
    assert _lifted_hold_threshold(session, tenant_id, PartyHold) is None

    lifted_holds(session, business, 5, party=True)
    assert _lifted_hold_threshold(session, tenant_id, PartyHold) is not None

    # And another company's history is its own.
    other = create_tenant(session, "Other GmbH")
    assert _lifted_hold_threshold(session, other.id, CommitmentHold) is None
    assert _lifted_hold_threshold(session, other.id, PartyHold) is None


def test_a_hold_suppresses_nothing(session, business):
    """Holding something changes what the queue says about it not at all."""
    lifted_holds(session, business, 5)
    stock(session, business)
    _, _, commitment = order(session, business, number="SO-107-D")
    ship(session, business, commitment, 6)
    before = set(by_class(session, business.tenant.id))

    hold = core.hold_commitment(
        session, business.tenant.id, commitment.id, "manual_review"
    )
    hold.created_at = AS_OF - timedelta(days=30)
    session.commit()

    after = set(by_class(session, business.tenant.id))
    assert after == before | {"commitment_hold_unreleased"}


def test_holds_are_tenant_scoped(session, business):
    lifted_holds(session, business, 5)
    commitment = customer_commitment(session, business, 4, AS_OF + timedelta(days=30))
    hold = core.hold_commitment(
        session, business.tenant.id, commitment.id, "compliance"
    )
    hold.created_at = AS_OF - timedelta(days=40)
    session.commit()

    other = create_tenant(session, "Foreign GmbH")

    assert hold.id in {
        entry.record_id
        for entry in operational_exceptions(session, business.tenant.id, as_of=AS_OF)
    }
    assert operational_exceptions(session, other.id, as_of=AS_OF) == []


# ---------------------------------------------------------------------------
# Spec 109: stock held past its stated best-before.


def perishable(session, business, sku="PERISH"):
    return core.create_item(
        session, business.tenant.id, sku, "Perishable", tracking_type="lot"
    )


def batch(session, business, item, number, expires_at, quantity=6, location=None):
    """A lot with a stated best-before and stock on hand."""
    lot = core.create_lot(
        session, business.tenant.id, item.id, number, expires_at=expires_at
    )
    if quantity:
        record_movement(
            session,
            business.tenant.id,
            "opening_stock",
            item.id,
            quantity,
            to_location_id=(location or business.location).id,
            lot_id=lot.id,
            occurred_at=AS_OF - timedelta(days=30),
        )
    return lot


def test_stock_expired(session, business):
    """A stated date and the day of the read. No third measurement."""
    item = perishable(session, business)
    gone_off = batch(session, business, item, "LOT-OLD", "2026-08-20")

    row = by_class(session, business.tenant.id)["stock_expired"]

    assert row.record_type == "lot"
    assert row.record_id == gone_off.id
    assert row.severity == "high"
    assert row.cause_ids == ()
    assert row.causal_values["expires_at"] == date(2026, 8, 20)
    assert row.causal_values["expired_days"] == 11
    assert row.causal_values["held_quantity"] == Decimal(6)
    assert row.causal_values["reserved_quantity"] == Decimal(0)
    assert row.causal_values["lot_number"] == "LOT-OLD"
    assert row.trace["lot_id"] == gone_off.id

    # A lot still ahead of its date says nothing.
    ahead = batch(session, business, item, "LOT-AHEAD", "2026-12-31")
    assert ahead.id not in {
        entry.record_id
        for entry in operational_exceptions(session, business.tenant.id, as_of=AS_OF)
        if entry.class_id == "stock_expired"
    }

    # Neither does an expired lot with nothing left on hand: nothing is held, so
    # there is nothing for anybody to do.
    empty = core.create_lot(
        session, business.tenant.id, item.id, "LOT-EMPTY", expires_at="2026-01-01"
    )
    assert empty.id in {
        row.id for row in core.expired_lots(session, business.tenant.id)
    }
    assert empty.id not in {
        entry.record_id
        for entry in operational_exceptions(session, business.tenant.id, as_of=AS_OF)
        if entry.class_id == "stock_expired"
    }

    # Writing the stock off ends the entry, with nothing stored and no manual
    # step. Nothing was blocked on the way in either.
    record_movement(
        session,
        business.tenant.id,
        "adjustment",
        item.id,
        6,
        from_location_id=business.location.id,
        lot_id=gone_off.id,
        reason="Written off past its best-before",
        occurred_at=AS_OF - timedelta(hours=1),
    )
    assert gone_off.id not in {
        entry.record_id
        for entry in operational_exceptions(session, business.tenant.id, as_of=AS_OF)
        if entry.class_id == "stock_expired"
    }


def test_expired_stock_reserved_for_a_customer(session, business):
    """Same record, same owner, different urgency — which is what a cause is for."""
    item = perishable(session, business)
    lot = batch(session, business, item, "LOT-PROMISED", "2026-08-25")
    commitment = customer_commitment(session, business, 4, AS_OF + timedelta(days=3))
    commitment.item_id = item.id
    session.commit()
    reserved = core.reserve(session, business.tenant.id, commitment.id, lot_id=lot.id)

    row = by_class(session, business.tenant.id)["stock_expired"]
    assert row.cause_ids == ("reserved_for_delivery",)
    assert row.causal_values["reserved_quantity"] == Decimal(4)
    assert "reserved for a customer" in row.impact

    # Releasing the reservation removes the reason and leaves the entry, because
    # the stock is still expired.
    core.release_reservation(session, business.tenant.id, reserved.reservation.id)
    after = by_class(session, business.tenant.id)["stock_expired"]
    assert after.cause_ids == ()
    assert after.causal_values["reserved_quantity"] == Decimal(0)


def test_expired_lots_are_ordered_by_the_day_they_expired(session, business):
    item = perishable(session, business)
    later = batch(session, business, item, "LOT-B", "2026-08-25")
    earlier = batch(session, business, item, "LOT-A", "2026-07-01")

    reported = [
        entry.record_id
        for entry in operational_exceptions(session, business.tenant.id, as_of=AS_OF)
        if entry.class_id == "stock_expired"
    ]

    # Oldest expiry first, whatever order the lots were recorded in.
    assert reported == [earlier.id, later.id]


def test_the_quantity_held_is_the_one_stock_rule(session, business):
    """One count, so this can never disagree with the inventory register."""
    item = perishable(session, business)
    elsewhere = core.create_location(session, business.tenant.id, "Cold Store")
    lot = batch(session, business, item, "LOT-SPLIT", "2026-08-01", quantity=2)
    record_movement(
        session,
        business.tenant.id,
        "opening_stock",
        item.id,
        3,
        to_location_id=elsewhere.id,
        lot_id=lot.id,
        occurred_at=AS_OF - timedelta(days=20),
    )

    row = by_class(session, business.tenant.id)["stock_expired"]

    # Stock of one lot spread across two locations is one quantity held, and it
    # is the figure the tracked-identity stock rule gives per location.
    assert row.causal_values["held_quantity"] == Decimal(5)
    assert core.stock_by_identity(
        session, business.tenant.id, item.id, business.location.id, lot_id=lot.id
    ) == Decimal(2)
    assert core.stock_by_identity(
        session, business.tenant.id, item.id, elsewhere.id, lot_id=lot.id
    ) == Decimal(3)


# ---------------------------------------------------------------------------
# Spec 110: the queue follows a corrected best-before.


def test_the_queue_follows_a_corrected_best_before(session, business):
    """Derived per read, so a correction moves the entry with nothing stored."""
    item = perishable(session, business, sku="PERISH-CORRECTED")
    wrong_early = batch(session, business, item, "LOT-TOO-EARLY", "2026-08-20")
    wrong_late = batch(session, business, item, "LOT-TOO-LATE", "2026-12-31")

    reported = lambda: {
        entry.record_id
        for entry in operational_exceptions(session, business.tenant.id, as_of=AS_OF)
        if entry.class_id == "stock_expired"
    }
    assert reported() == {wrong_early.id}

    # A date read a day early reported good stock as expired. Corrected forward,
    # the entry goes.
    core.correct_lot_expiry(
        session,
        business.tenant.id,
        wrong_early.id,
        "2026-12-01",
        expected_expires_at="2026-08-20",
        reason="Read the label of the pallet behind it",
    )

    # A date read late hid expired stock. Corrected back, it is reported.
    core.correct_lot_expiry(
        session,
        business.tenant.id,
        wrong_late.id,
        "2026-08-01",
        expected_expires_at="2026-12-31",
        reason="Transposed the month",
    )

    assert reported() == {wrong_late.id}
    row = by_class(session, business.tenant.id)["stock_expired"]
    assert row.record_id == wrong_late.id
    assert row.causal_values["expires_at"] == date(2026, 8, 1)
    assert row.causal_values["expired_days"] == 30
