from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from reality.db.core import now
from reality.services import core
from reality.services.core import (
    NotFound,
    create_commitment,
    create_document,
    create_item,
    create_payment_term,
    create_tenant,
    post_customer_payment,
    post_sales_invoice,
    post_supplier_invoice,
    post_supplier_payment,
    record_movement,
    reserve,
    reverse_ledger_posting_group,
)
from reality.services.exceptions import (
    explain_operational_exception,
    operational_exception_rows,
    operational_exceptions,
)


def test_explanation_uses_stable_identity_and_rejects_malformed_or_foreign(
    session, business
):
    commitment = create_commitment(
        session,
        business.tenant.id,
        "customer_delivery",
        business.company.id,
        business.customer.id,
        business.item.id,
        business.location.id,
        2,
        "2026-09-03",
    )
    before_due = datetime(2026, 9, 1, 12, tzinfo=UTC)
    row = operational_exceptions(session, business.tenant.id, as_of=before_due)[0]

    explained = explain_operational_exception(
        session, business.tenant.id, row.id, as_of=before_due
    )

    assert explained["id"] == (f"exc__outgoing_commitment_at_risk__{commitment.id}")
    assert explained["record_id"] == commitment.id
    assert explained["trace"]["commitment_id"] == commitment.id
    with pytest.raises(NotFound, match="Current operational exception not found"):
        explain_operational_exception(
            session, business.tenant.id, commitment.id, as_of=before_due
        )
    with pytest.raises(NotFound, match="Current operational exception not found"):
        explain_operational_exception(session, "ten_foreign", row.id, as_of=before_due)


def test_new_class_explanation_and_not_found_parity(session, business):
    tenant_id = business.tenant.id
    due_at = datetime(2026, 9, 3, 12, tzinfo=UTC)
    before = due_at - timedelta(days=1)
    after = due_at + timedelta(days=1)
    commitment = create_commitment(
        session,
        tenant_id,
        "customer_delivery",
        business.company.id,
        business.customer.id,
        business.item.id,
        business.location.id,
        6,
        due_at,
    )
    record_movement(
        session,
        tenant_id,
        "opening_stock",
        business.item.id,
        6,
        to_location_id=business.location.id,
    )
    reserve(session, tenant_id, commitment.id)
    record_movement(
        session,
        tenant_id,
        "adjustment",
        business.item.id,
        2,
        from_location_id=business.location.id,
        reason="stocktake loss",
    )

    stock_id = f"exc__reservation_exceeds_stock__{business.item.id}"
    explained = explain_operational_exception(
        session, tenant_id, stock_id, as_of=before
    )

    assert explained["record_type"] == "item"
    assert explained["record_id"] == business.item.id
    assert explained["causal_values"]["shortfall"] == Decimal(2)
    # Only a failed source interpretation carries a raw payload.
    assert explained["raw_source"] is None

    # The promise above is fully reserved, so it is never at risk even though
    # its reservation has no goods behind it. The identity transition needs an
    # unreserved promise: at risk before its due date, overdue after it, and
    # the identity moves with the class it belongs to.
    unreserved = create_commitment(
        session,
        tenant_id,
        "customer_delivery",
        business.company.id,
        business.customer.id,
        create_item(session, tenant_id, "BIKE-CHAIN", "Bike Chain").id,
        business.location.id,
        3,
        due_at,
    )
    at_risk_id = f"exc__outgoing_commitment_at_risk__{unreserved.id}"
    overdue_id = f"exc__overdue_outgoing_customer_commitment__{unreserved.id}"
    assert (
        explain_operational_exception(session, tenant_id, at_risk_id, as_of=before)[
            "record_id"
        ]
        == unreserved.id
    )
    overdue = explain_operational_exception(session, tenant_id, overdue_id, as_of=after)
    assert overdue["record_id"] == unreserved.id
    assert overdue["trace"]["commitment_id"] == unreserved.id
    assert overdue["cause_ids"] == ["insufficient_reservation"]

    for exception_id, as_of in (
        (at_risk_id, after),
        (overdue_id, before),
        ("exc__overdue_outgoing_customer_commitment__com_missing", after),
        ("not-an-exception-identity", after),
    ):
        with pytest.raises(NotFound, match="Current operational exception not found"):
            explain_operational_exception(session, tenant_id, exception_id, as_of=as_of)
    with pytest.raises(NotFound, match="Current operational exception not found"):
        explain_operational_exception(session, "ten_foreign", stock_id, as_of=before)


def test_shared_consumer_parity_includes_new_classes(session, business):
    tenant_id = business.tenant.id
    create_commitment(
        session,
        tenant_id,
        "customer_delivery",
        business.company.id,
        business.customer.id,
        business.item.id,
        business.location.id,
        4,
        datetime(2026, 8, 1, 12, tzinfo=UTC),
    )
    other = create_item(session, tenant_id, "BIKE-BELL", "Bike Bell")
    record_movement(
        session,
        tenant_id,
        "opening_stock",
        other.id,
        5,
        to_location_id=business.location.id,
    )
    backed = create_commitment(
        session,
        tenant_id,
        "customer_delivery",
        business.company.id,
        business.customer.id,
        other.id,
        business.location.id,
        5,
        datetime(2026, 12, 1, 12, tzinfo=UTC),
    )
    reserve(session, tenant_id, backed.id)
    record_movement(
        session,
        tenant_id,
        "adjustment",
        other.id,
        2,
        from_location_id=business.location.id,
        reason="stocktake loss",
    )

    # A source that delivered daily and then stopped ten days ago. Anchored to
    # the wall clock, because this parity test reads the queue without an
    # evaluation instant.
    from reality.db.core import SourceRecord, now, uid
    from reality.services.core import create_source_capability, create_source_system

    system = create_source_system(session, tenant_id, "shopify", "Shopify")
    create_source_capability(session, tenant_id, system.id, "order", "document")
    stopped = now() - timedelta(days=10)
    for sequence in range(8):
        session.add(
            SourceRecord(
                id=uid("src"),
                tenant_id=tenant_id,
                source_system=system.code,
                source_type="order",
                external_id=f"parity-{sequence}",
                payload='{"ok": true}',
                payload_hash=f"{sequence:064d}",
                version=1,
                received_at=stopped - timedelta(days=sequence),
            )
        )
    session.flush()

    # One shipped-and-unbilled sales line, one over-billed purchase line, one
    # invoice line above the agreed price, one customer past its limit, one
    # supplier invoice recorded twice and one uncredited return, so every class
    # reaches the shared contract through the same read.
    billed_pair(session, business)
    exposed_and_duplicated(session, business)
    returned_pair(session, business)
    stalled_and_unbilled(session, business)
    sitting_return(session, business)
    promised_and_owed(session, business)
    sold_too_cheaply(session, business)
    units_that_do_not_meet(session, business)
    discount_still_available(session, business)
    supplier_credit_unclaimed(session, business)
    supplier_credit_unposted(session, business)
    sent_back_to_supplier(session, business)
    sales_invoice_unposted(session, business)
    supplier_invoice_unposted(session, business)

    create_payment_term(session, tenant_id, "NET30", "Net 30 days", 30)
    payable = create_document(
        session,
        tenant_id,
        "supplier_invoice",
        "ER-7001",
        business.supplier.id,
        "500.00",
        document_date="2026-01-01",
        payment_term_code="NET30",
    )
    post_supplier_invoice(session, tenant_id, payable.id)

    receivable = create_document(
        session,
        tenant_id,
        "sales_invoice",
        "RE-7001",
        business.customer.id,
        "900.00",
        document_date="2026-01-01",
        payment_term_code="NET30",
    )
    post_sales_invoice(session, tenant_id, receivable.id)

    rows = operational_exception_rows(session, tenant_id)
    entries = operational_exceptions(session, tenant_id)

    assert [row["id"] for row in rows] == [entry.id for entry in entries]
    by_class_id = {row["class_id"]: row for row in rows}
    for class_id in (
        "overdue_outgoing_customer_commitment",
        "reservation_exceeds_stock",
        "overdue_receivable",
        "overdue_payable",
        "purchase_discount_available",
        "silent_source",
        "shipped_not_billed",
        "billed_not_received",
        "invoice_price_differs",
        "credit_limit_exceeded",
        "duplicate_supplier_invoice",
        "returned_not_credited",
        "order_stalled",
        "receipt_unbilled",
        "units_not_comparable",
        "return_unresolved",
        "sales_invoice_unposted",
        "supplier_invoice_unposted",
        "credit_note_unposted",
        "credit_note_unsettled",
        "supplier_credit_unposted",
        "supplier_credit_unclaimed",
        "supplier_return_not_credited",
        "sold_below_purchase_price",
    ):
        row = by_class_id[class_id]
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
        } <= set(row)
        assert isinstance(row["cause_ids"], list)


def test_overdue_receivable_explanation_and_not_found_parity(session, business):
    tenant_id = business.tenant.id
    as_of = datetime(2026, 8, 31, 12, tzinfo=UTC)
    create_payment_term(session, tenant_id, "NET30", "Net 30 days", 30)
    invoice = create_document(
        session,
        tenant_id,
        "sales_invoice",
        "RE-6001",
        business.customer.id,
        "1000.00",
        document_date="2026-07-01",
        payment_term_code="NET30",
    )
    post_sales_invoice(session, tenant_id, invoice.id)
    exception_id = f"exc__overdue_receivable__{invoice.id}"

    explained = explain_operational_exception(
        session, tenant_id, exception_id, as_of=as_of
    )

    assert explained["record_type"] == "document"
    assert explained["record_id"] == invoice.id
    assert explained["causal_values"]["days_overdue"] == 31
    # Only a failed source interpretation carries a raw payload.
    assert explained["raw_source"] is None

    with pytest.raises(NotFound, match="Current operational exception not found"):
        explain_operational_exception(session, "ten_foreign", exception_id, as_of=as_of)
    with pytest.raises(NotFound, match="Current operational exception not found"):
        explain_operational_exception(
            session, tenant_id, "exc__overdue_receivable__doc_missing", as_of=as_of
        )

    post_customer_payment(session, tenant_id, invoice.id, "1000.00")

    with pytest.raises(NotFound, match="Current operational exception not found"):
        explain_operational_exception(session, tenant_id, exception_id, as_of=as_of)


def test_silent_source_explanation_and_not_found_parity(session, business):
    from reality.db.core import SourceRecord, uid
    from reality.services.core import create_source_capability, create_source_system

    tenant_id = business.tenant.id
    as_of = datetime(2026, 9, 21, 12, tzinfo=UTC)
    system = create_source_system(session, tenant_id, "shopify", "Shopify")
    capability = create_source_capability(
        session, tenant_id, system.id, "order", "document"
    )
    for sequence in range(8):
        session.add(
            SourceRecord(
                id=uid("src"),
                tenant_id=tenant_id,
                source_system=system.code,
                source_type="order",
                external_id=f"order-{sequence}",
                payload='{"ok": true}',
                payload_hash=f"{sequence:064d}",
                version=1,
                received_at=as_of - timedelta(days=4 + sequence),
            )
        )
    session.flush()
    exception_id = f"exc__silent_source__{capability.id}"

    explained = explain_operational_exception(
        session, tenant_id, exception_id, as_of=as_of
    )

    assert explained["record_type"] == "source_capability"
    assert explained["record_id"] == capability.id
    assert explained["causal_values"]["expected_pause_hours"] == 24
    # Only a failed source interpretation carries a raw payload, even though
    # this class is about sources too.
    assert explained["raw_source"] is None

    with pytest.raises(NotFound, match="Current operational exception not found"):
        explain_operational_exception(session, "ten_foreign", exception_id, as_of=as_of)
    with pytest.raises(NotFound, match="Current operational exception not found"):
        explain_operational_exception(
            session, tenant_id, "exc__silent_source__cap_missing", as_of=as_of
        )

    # The source resumes: the identity stops resolving.
    session.add(
        SourceRecord(
            id=uid("src"),
            tenant_id=tenant_id,
            source_system=system.code,
            source_type="order",
            external_id="order-resumed",
            payload='{"ok": true}',
            payload_hash="f" * 64,
            version=1,
            received_at=as_of - timedelta(hours=1),
        )
    )
    session.flush()

    with pytest.raises(NotFound, match="Current operational exception not found"):
        explain_operational_exception(session, tenant_id, exception_id, as_of=as_of)


# --- The three line classes explain themselves (spec 076) ------------------


def billed_pair(session, business):
    """One shipped-and-unbilled line and one invoice line billing it too dearly."""
    from tests.operational_exceptions.test_derivation import bill, order, ship, stock

    stock(session, business)
    _, line, commitment = order(session, business, number="SO-EXPLAIN")
    ship(session, business, commitment, 8)
    _, purchase_line, purchase_commitment = order(
        session, business, direction="purchase", number="PO-EXPLAIN"
    )
    bill(
        session,
        business,
        purchase_line,
        direction="purchase",
        number="ER-EXPLAIN",
        quantity="4",
    )
    _, billed = bill(
        session,
        business,
        line,
        number="RE-EXPLAIN",
        quantity="2",
        unit_price="12.00",
    )
    return line, purchase_line, purchase_commitment, billed


def test_line_classes_explanation_and_not_found_parity(session, business):
    tenant_id = business.tenant.id
    line, purchase_line, purchase_commitment, billed = billed_pair(session, business)

    current = {row.class_id: row for row in operational_exceptions(session, tenant_id)}
    for class_id, record_id in (
        ("shipped_not_billed", line.id),
        ("billed_not_received", purchase_line.id),
        ("invoice_price_differs", billed.id),
    ):
        row = current[class_id]
        explained = explain_operational_exception(session, tenant_id, row.id)

        assert explained["id"] == row.id
        assert explained["record_type"] == "document_line"
        assert explained["record_id"] == record_id
        assert explained["causal_values"] == row.causal_values
        # Only an interpretation failure carries the payload it failed on.
        assert explained["raw_source"] is None

    # A malformed identity and one from another tenant are the same answer.
    with pytest.raises(NotFound):
        explain_operational_exception(session, tenant_id, "not-an-exception")
    foreign = create_tenant(session, "Foreign explanation tenant")
    with pytest.raises(NotFound):
        explain_operational_exception(
            session, foreign.id, current["shipped_not_billed"].id
        )

    # A cleared condition is no longer explainable, with no manual step.
    cleared_id = current["billed_not_received"].id
    record_movement(
        session,
        tenant_id,
        "receipt",
        business.item.id,
        4,
        to_location_id=business.location.id,
        commitment_id=purchase_commitment.id,
    )
    with pytest.raises(NotFound):
        explain_operational_exception(session, tenant_id, cleared_id)


# --- Two answers the records already hold (spec 078) -----------------------


def exposed_and_duplicated(session, business):
    """A customer past its limit and a supplier invoice recorded twice."""
    from tests.operational_exceptions.test_derivation import customer, invoice

    party = customer(session, business, limit="100", name="Exposed GmbH")
    invoice(session, business, party, "RE-EXPL", "400.00")
    first = invoice(
        session,
        business,
        business.supplier,
        "ER-EXPL",
        "90.00",
        document_type="supplier_invoice",
    )
    second = invoice(
        session,
        business,
        business.supplier,
        "ER-EXPL",
        "90.00",
        document_type="supplier_invoice",
        document_date="2026-08-06",
    )
    return party, first, second


def test_record_classes_explanation_and_not_found_parity(session, business):
    tenant_id = business.tenant.id
    party, first, second = exposed_and_duplicated(session, business)

    current = {row.class_id: row for row in operational_exceptions(session, tenant_id)}
    for class_id, record_type, record_id in (
        ("credit_limit_exceeded", "party", party.id),
        ("duplicate_supplier_invoice", "document", second.id),
    ):
        row = current[class_id]
        explained = explain_operational_exception(session, tenant_id, row.id)

        assert explained["id"] == row.id
        assert explained["record_type"] == record_type
        assert explained["record_id"] == record_id
        assert explained["causal_values"] == row.causal_values
        assert explained["raw_source"] is None

    with pytest.raises(NotFound):
        explain_operational_exception(session, tenant_id, "not-an-exception")
    foreign = create_tenant(session, "Foreign record explanation tenant")
    with pytest.raises(NotFound):
        explain_operational_exception(
            session, foreign.id, current["credit_limit_exceeded"].id
        )

    # A cleared condition is no longer explainable, with no manual step.
    cleared_id = current["duplicate_supplier_invoice"].id
    control = core._settlement_control_entry(session, tenant_id, first.id)
    reverse_ledger_posting_group(
        session, tenant_id, control.posting_group_id, reason="recorded in error"
    )
    with pytest.raises(NotFound):
        explain_operational_exception(session, tenant_id, cleared_id)


# --- Goods coming back (spec 079) ------------------------------------------


def returned_pair(session, business):
    """One order line with goods back and nothing credited."""
    from tests.operational_exceptions.test_derivation import (
        bill,
        order,
        send_back,
        ship,
        stock,
    )

    stock(session, business)
    _, line, commitment = order(session, business, number="SO-RET-EXPL")
    ship(session, business, commitment, 10)
    bill(session, business, line, number="RE-RET-EXPL", quantity="10")
    send_back(session, business, commitment, 6)
    return line, commitment


def test_return_classes_explanation_and_not_found_parity(session, business):
    from tests.operational_exceptions.test_derivation import credit

    tenant_id = business.tenant.id
    line, _ = returned_pair(session, business)

    current = {row.class_id: row for row in operational_exceptions(session, tenant_id)}
    row = current["returned_not_credited"]
    explained = explain_operational_exception(session, tenant_id, row.id)

    assert explained["id"] == row.id
    assert explained["record_type"] == "document_line"
    assert explained["record_id"] == line.id
    assert explained["causal_values"] == row.causal_values
    assert explained["raw_source"] is None

    with pytest.raises(NotFound):
        explain_operational_exception(session, tenant_id, "not-an-exception")
    foreign = create_tenant(session, "Foreign returns explanation tenant")
    with pytest.raises(NotFound):
        explain_operational_exception(session, foreign.id, row.id)

    # Crediting the return clears it, and its identity stops explaining.
    credit(session, business, line, number="GS-EXPL", quantity="6")
    with pytest.raises(NotFound):
        explain_operational_exception(session, tenant_id, row.id)


# --- Long by this company's own standard (spec 080) ------------------------


def stalled_and_unbilled(session, business):
    """One order standing far too long and one receipt nobody invoiced."""
    from tests.operational_exceptions.test_derivation import (
        billing_history,
        history,
        purchase,
        receive,
        undated_promise,
    )

    history(session, business, lag_days=1, cases=6)
    billing_history(session, business, lag_days=3, cases=6)
    stalled = undated_promise(session, business, age_days=60)
    line, commitment = purchase(session, business, "PO-EXPL-LAG")
    receive(session, business, commitment, 10, days_ago=60)
    return stalled, line, commitment


def test_lag_classes_explanation_and_not_found_parity(session, business):
    from tests.operational_exceptions.test_derivation import AS_OF, bill

    tenant_id = business.tenant.id
    stalled, line, _ = stalled_and_unbilled(session, business)

    current = {
        row.class_id: row
        for row in operational_exceptions(session, tenant_id, as_of=AS_OF)
    }
    for class_id, record_type, record_id in (
        ("order_stalled", "commitment", stalled.id),
        ("receipt_unbilled", "document_line", line.id),
    ):
        row = current[class_id]
        explained = explain_operational_exception(
            session, tenant_id, row.id, as_of=AS_OF
        )

        assert explained["id"] == row.id
        assert explained["record_type"] == record_type
        assert explained["record_id"] == record_id
        assert explained["causal_values"] == row.causal_values
        assert explained["raw_source"] is None

    with pytest.raises(NotFound):
        explain_operational_exception(session, tenant_id, "not-an-exception")
    foreign = create_tenant(session, "Foreign lag explanation tenant")
    with pytest.raises(NotFound):
        explain_operational_exception(
            session, foreign.id, current["order_stalled"].id, as_of=AS_OF
        )

    # Billing the receipt clears it, and its identity stops explaining.
    cleared_id = current["receipt_unbilled"].id
    bill(
        session,
        business,
        line,
        direction="purchase",
        number="ER-EXPL-LAG",
        quantity="10",
    )
    with pytest.raises(NotFound):
        explain_operational_exception(session, tenant_id, cleared_id, as_of=AS_OF)


# --- What happened to the goods (spec 081) ---------------------------------


def sitting_return(session, business):
    """One return nobody has dealt with."""
    from tests.operational_exceptions.test_derivation import (
        area,
        goods_back,
        order,
        resolution_history,
        ship,
    )

    returns = area(session, business)
    resolution_history(session, business, returns, cases=6, prefix="X")
    _, _, commitment = order(session, business, number="SO-EXPL-RET")
    ship(session, business, commitment, 10)
    return goods_back(session, business, commitment, 5, returns, days_ago=60), returns


def test_return_unresolved_explanation_and_not_found_parity(session, business):
    from tests.operational_exceptions.test_derivation import AS_OF, settle

    tenant_id = business.tenant.id
    sitting, returns = sitting_return(session, business)

    row = next(
        entry
        for entry in operational_exceptions(session, tenant_id, as_of=AS_OF)
        if entry.class_id == "return_unresolved"
    )
    explained = explain_operational_exception(session, tenant_id, row.id, as_of=AS_OF)

    assert explained["record_type"] == "movement"
    assert explained["record_id"] == sitting.id
    assert explained["causal_values"] == row.causal_values
    assert explained["raw_source"] is None

    with pytest.raises(NotFound):
        explain_operational_exception(session, tenant_id, "not-an-exception")
    foreign = create_tenant(session, "Foreign return explanation tenant")
    with pytest.raises(NotFound):
        explain_operational_exception(session, foreign.id, row.id, as_of=AS_OF)

    # Dealing with the goods clears it, and its identity stops explaining.
    settle(session, business, sitting, 5, returns, days_after=59)
    with pytest.raises(NotFound):
        explain_operational_exception(session, tenant_id, row.id, as_of=AS_OF)


# --- A credit note gives the money back (spec 084) -------------------------


def promised_and_owed(session, business):
    """One credit note nobody booked and one booked that nobody gave back."""
    from tests.operational_exceptions.test_derivation import note, posting_history

    posting_history(session, business, cases=6, prefix="E")
    forgotten = note(session, business, "GS-EXPL-1", "40.00", day="2026-06-01")
    owed = note(session, business, "GS-EXPL-2", "60.00")
    from reality.services.core import post_sales_credit_note

    post_sales_credit_note(session, business.tenant.id, owed.id)
    return forgotten, owed


def test_credit_note_classes_explanation_and_not_found_parity(session, business):
    from reality.services.core import post_customer_refund
    from tests.operational_exceptions.test_derivation import AS_OF

    tenant_id = business.tenant.id
    forgotten, owed = promised_and_owed(session, business)

    current = {
        row.class_id: row
        for row in operational_exceptions(session, tenant_id, as_of=AS_OF)
    }
    for class_id, record_id in (
        ("credit_note_unposted", forgotten.id),
        ("credit_note_unsettled", owed.id),
    ):
        row = current[class_id]
        explained = explain_operational_exception(
            session, tenant_id, row.id, as_of=AS_OF
        )

        assert explained["id"] == row.id
        assert explained["record_type"] == "document"
        assert explained["record_id"] == record_id
        assert explained["causal_values"] == row.causal_values
        assert explained["raw_source"] is None

    with pytest.raises(NotFound):
        explain_operational_exception(session, tenant_id, "not-an-exception")
    foreign = create_tenant(session, "Foreign credit explanation tenant")
    with pytest.raises(NotFound):
        explain_operational_exception(
            session, foreign.id, current["credit_note_unposted"].id, as_of=AS_OF
        )

    # Giving the money back clears it, and its identity stops explaining.
    cleared_id = current["credit_note_unsettled"].id
    post_customer_refund(session, tenant_id, owed.id, "60.00")
    with pytest.raises(NotFound):
        explain_operational_exception(session, tenant_id, cleared_id, as_of=AS_OF)


# --- Sold for less than it costs to buy (spec 086) -------------------------


def sold_too_cheaply(session, business):
    """One sales line agreed below the standing purchase price."""
    from tests.operational_exceptions.test_derivation import purchase_price, sold_at

    purchase_price(session, business, "10.00")
    return sold_at(session, business, "SO-EXPL-PRICE", "6.00")


def test_pricing_class_explanation_and_not_found_parity(session, business):
    from decimal import Decimal

    from tests.operational_exceptions.test_derivation import AS_OF

    tenant_id = business.tenant.id
    line = sold_too_cheaply(session, business)

    row = next(
        entry
        for entry in operational_exceptions(session, tenant_id, as_of=AS_OF)
        if entry.class_id == "sold_below_purchase_price"
    )
    explained = explain_operational_exception(session, tenant_id, row.id, as_of=AS_OF)

    assert explained["record_type"] == "document_line"
    assert explained["record_id"] == line.id
    assert explained["causal_values"] == row.causal_values
    assert explained["raw_source"] is None

    with pytest.raises(NotFound):
        explain_operational_exception(session, tenant_id, "not-an-exception")
    foreign = create_tenant(session, "Foreign pricing explanation tenant")
    with pytest.raises(NotFound):
        explain_operational_exception(session, foreign.id, row.id, as_of=AS_OF)

    # Agreeing a sound price clears it, and its identity stops explaining.
    line.unit_price = Decimal("12.0000")
    session.flush()
    with pytest.raises(NotFound):
        explain_operational_exception(session, tenant_id, row.id, as_of=AS_OF)


# --- Units that do not meet (spec 087) -------------------------------------


def units_that_do_not_meet(session, business):
    """One order line in boxes, invoiced in pieces, on an item that says nothing."""
    from reality.services.core import (
        create_manual_document_with_lines,
        create_manual_order,
    )

    item = create_item(session, business.tenant.id, "BIKE-CRATE", "Bike Crate")
    _, _document, lines, _commitments = create_manual_order(
        session,
        business.tenant.id,
        "sales",
        "SO-EXPL-UNITS",
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
        requested_delivery_at=datetime(2026, 12, 1, 12, tzinfo=UTC),
    )
    create_manual_document_with_lines(
        session,
        business.tenant.id,
        "sales_invoice",
        "RE-EXPL-UNITS",
        business.customer.id,
        [
            {
                "item_id": item.id,
                "quantity": "108",
                "unit": "pcs",
                "unit_price": "1.00",
                "gross_amount": "108.00",
                "billed_document_line_id": lines[0].id,
            }
        ],
        "108.00",
        document_date="2026-08-20",
    )
    return item


def test_units_class_explanation_and_not_found_parity(session, business):
    from reality.services.core import update_item

    tenant_id = business.tenant.id
    item = units_that_do_not_meet(session, business)

    row = next(
        entry
        for entry in operational_exceptions(session, tenant_id)
        if entry.class_id == "units_not_comparable"
    )
    explained = explain_operational_exception(session, tenant_id, row.id)

    assert explained["record_type"] == "item"
    assert explained["record_id"] == item.id
    assert explained["causal_values"] == row.causal_values
    assert explained["raw_source"] is None

    with pytest.raises(NotFound):
        explain_operational_exception(session, tenant_id, "not-an-exception")
    foreign = create_tenant(session, "Foreign units explanation tenant")
    with pytest.raises(NotFound):
        explain_operational_exception(session, foreign.id, row.id)

    # Stating the relation clears it, and its identity stops explaining.
    update_item(
        session,
        tenant_id,
        item.id,
        item.sku,
        item.name,
        item.unit,
        purchase_unit="box",
        conversion_factor="12",
    )
    with pytest.raises(NotFound):
        explain_operational_exception(session, tenant_id, row.id)


# --- The early payment discount (spec 088) ---------------------------------


def discount_still_available(session, business):
    """An unpaid supplier invoice whose discount window is still open."""
    from reality.services.core import create_payment_term

    create_payment_term(
        session,
        business.tenant.id,
        "SK2_10_EXPL",
        "2% 10 days, net 30",
        30,
        discount_percent="2",
        discount_days=10,
    )
    invoice = create_document(
        session,
        business.tenant.id,
        "supplier_invoice",
        "ER-EXPL-SKONTO",
        business.supplier.id,
        "1000.00",
        document_date=(now() - timedelta(days=2)).date().isoformat(),
        payment_term_code="SK2_10_EXPL",
    )
    post_supplier_invoice(session, business.tenant.id, invoice.id)
    return invoice


def test_discount_class_explanation_and_not_found_parity(session, business):
    tenant_id = business.tenant.id
    invoice = discount_still_available(session, business)

    row = next(
        entry
        for entry in operational_exceptions(session, tenant_id)
        if entry.class_id == "purchase_discount_available"
    )
    explained = explain_operational_exception(session, tenant_id, row.id)

    assert explained["record_type"] == "document"
    assert explained["record_id"] == invoice.id
    assert explained["causal_values"] == row.causal_values

    with pytest.raises(NotFound):
        explain_operational_exception(session, tenant_id, "not-an-exception")
    foreign = create_tenant(session, "Foreign discount explanation tenant")
    with pytest.raises(NotFound):
        explain_operational_exception(session, foreign.id, row.id)

    # Paying it takes the discount and the identity stops explaining.
    post_supplier_payment(session, tenant_id, invoice.id, "1000.00")
    with pytest.raises(NotFound):
        explain_operational_exception(session, tenant_id, row.id)


# --- The credit that comes the other way (spec 089) ------------------------


def supplier_credit_unclaimed(session, business):
    """A booked supplier credit nobody has netted or asked for."""
    from reality.services.core import post_supplier_credit_note

    credit = create_document(
        session,
        business.tenant.id,
        "supplier_credit_note",
        "SG-EXPL",
        business.supplier.id,
        "80.00",
        document_date="2026-08-05",
    )
    post_supplier_credit_note(session, business.tenant.id, credit.id)
    return credit


def supplier_credit_unposted(session, business):
    """A supplier credit nobody booked, on a tenant with a rhythm of its own.

    The rhythm has to be this side's own: the unposted class deliberately learns
    nothing from the credit notes the company writes itself.
    """
    from reality.services.core import post_supplier_credit_note, post_supplier_refund

    tenant_id = business.tenant.id
    for index in range(6):
        recorded = now() - timedelta(days=120 - index * 5)
        booked = create_document(
            session,
            tenant_id,
            "supplier_credit_note",
            f"SG-EXPL-NORM-{index}",
            business.supplier.id,
            "10.00",
            document_date=recorded.date().isoformat(),
        )
        post_supplier_credit_note(
            session, tenant_id, booked.id, effective_at=recorded + timedelta(days=2)
        )
        post_supplier_refund(session, tenant_id, booked.id, "10.00")
    forgotten = create_document(
        session,
        tenant_id,
        "supplier_credit_note",
        "SG-EXPL-FORGOTTEN",
        business.supplier.id,
        "45.00",
        document_date=(now() - timedelta(days=90)).date().isoformat(),
    )
    return forgotten


def test_supplier_credit_explanation_and_not_found_parity(session, business):
    from reality.services.core import post_supplier_refund

    tenant_id = business.tenant.id
    credit = supplier_credit_unclaimed(session, business)

    row = next(
        entry
        for entry in operational_exceptions(session, tenant_id)
        if entry.class_id == "supplier_credit_unclaimed"
    )
    explained = explain_operational_exception(session, tenant_id, row.id)

    assert explained["record_type"] == "document"
    assert explained["record_id"] == credit.id
    assert explained["causal_values"] == row.causal_values

    with pytest.raises(NotFound):
        explain_operational_exception(session, tenant_id, "not-an-exception")
    foreign = create_tenant(session, "Foreign supplier credit explanation tenant")
    with pytest.raises(NotFound):
        explain_operational_exception(session, foreign.id, row.id)

    # Claiming it back settles the credit and its identity stops explaining.
    post_supplier_refund(session, tenant_id, credit.id, "80.00")
    with pytest.raises(NotFound):
        explain_operational_exception(session, tenant_id, row.id)


# --- Goods going back the other way (spec 090) -----------------------------


def sent_back_to_supplier(session, business):
    """A purchase order line billed by the supplier with part of it sent back."""
    from reality.services.core import (
        create_manual_document_with_lines,
        create_manual_order,
    )

    tenant_id = business.tenant.id
    _, _document, lines, commitments = create_manual_order(
        session,
        tenant_id,
        "purchase",
        "PO-EXPL-SRET",
        business.supplier.id,
        business.company.id,
        business.location.id,
        [
            {
                "item_id": business.item.id,
                "quantity": "10",
                "unit": "pcs",
                "unit_price": "9.00",
                "gross_amount": "90.00",
            }
        ],
        "90.00",
        requested_delivery_at=datetime(2026, 12, 1, 12, tzinfo=UTC),
    )
    record_movement(
        session,
        tenant_id,
        "receipt",
        business.item.id,
        10,
        to_location_id=business.location.id,
        commitment_id=commitments[0].id,
    )
    create_manual_document_with_lines(
        session,
        tenant_id,
        "supplier_invoice",
        "ER-EXPL-SRET",
        business.supplier.id,
        [
            {
                "item_id": business.item.id,
                "quantity": "10",
                "unit": "pcs",
                "unit_price": "9.00",
                "gross_amount": "90.00",
                "billed_document_line_id": lines[0].id,
            }
        ],
        "90.00",
        document_date="2026-08-20",
    )
    record_movement(
        session,
        tenant_id,
        "supplier_return",
        business.item.id,
        4,
        from_location_id=business.location.id,
        commitment_id=commitments[0].id,
    )
    return lines[0]


def test_supplier_return_explanation_and_not_found_parity(session, business):
    from reality.services.core import create_manual_document_with_lines

    tenant_id = business.tenant.id
    line = sent_back_to_supplier(session, business)

    row = next(
        entry
        for entry in operational_exceptions(session, tenant_id)
        if entry.class_id == "supplier_return_not_credited"
    )
    explained = explain_operational_exception(session, tenant_id, row.id)

    assert explained["record_type"] == "document_line"
    assert explained["record_id"] == line.id
    assert explained["causal_values"] == row.causal_values

    with pytest.raises(NotFound):
        explain_operational_exception(session, tenant_id, "not-an-exception")
    foreign = create_tenant(session, "Foreign supplier return explanation tenant")
    with pytest.raises(NotFound):
        explain_operational_exception(session, foreign.id, row.id)

    # The supplier credits it and the identity stops explaining.
    create_manual_document_with_lines(
        session,
        tenant_id,
        "supplier_credit_note",
        "SG-EXPL-SRET",
        business.supplier.id,
        [
            {
                "item_id": business.item.id,
                "quantity": "4",
                "unit": "pcs",
                "unit_price": "9.00",
                "gross_amount": "36.00",
                "billed_document_line_id": line.id,
            }
        ],
        "36.00",
        document_date="2026-08-25",
    )
    with pytest.raises(NotFound):
        explain_operational_exception(session, tenant_id, row.id)


# --- The invoice nobody booked (spec 092) ----------------------------------


def sales_invoice_unposted(session, business):
    """A tenant with a booking rhythm and one sales invoice left unbooked."""
    from reality.services.core import post_sales_invoice

    tenant_id = business.tenant.id
    for index in range(6):
        recorded = now() - timedelta(days=120 - index * 5)
        booked = create_document(
            session,
            tenant_id,
            "sales_invoice",
            f"RE-EXPL-NORM-{index}",
            business.customer.id,
            "10.00",
            document_date=recorded.date().isoformat(),
        )
        post_sales_invoice(
            session, tenant_id, booked.id, effective_at=recorded + timedelta(days=2)
        )
    return create_document(
        session,
        tenant_id,
        "sales_invoice",
        "RE-EXPL-FORGOTTEN",
        business.customer.id,
        "300.00",
        document_date=(now() - timedelta(days=90)).date().isoformat(),
    )


def supplier_invoice_unposted(session, business):
    """The same on the buying side, with its own rhythm rather than the sales one."""
    from reality.services.core import post_supplier_invoice

    tenant_id = business.tenant.id
    for index in range(6):
        recorded = now() - timedelta(days=120 - index * 5)
        booked = create_document(
            session,
            tenant_id,
            "supplier_invoice",
            f"ER-EXPL-NORM-{index}",
            business.supplier.id,
            "10.00",
            document_date=recorded.date().isoformat(),
        )
        post_supplier_invoice(
            session, tenant_id, booked.id, effective_at=recorded + timedelta(days=2)
        )
    return create_document(
        session,
        tenant_id,
        "supplier_invoice",
        "ER-EXPL-FORGOTTEN",
        business.supplier.id,
        "300.00",
        document_date=(now() - timedelta(days=90)).date().isoformat(),
    )


def test_unposted_invoice_explanation_and_not_found_parity(session, business):
    from reality.services.core import post_sales_invoice

    tenant_id = business.tenant.id
    forgotten = sales_invoice_unposted(session, business)

    row = next(
        entry
        for entry in operational_exceptions(session, tenant_id)
        if entry.class_id == "sales_invoice_unposted"
    )
    explained = explain_operational_exception(session, tenant_id, row.id)

    assert explained["record_type"] == "document"
    assert explained["record_id"] == forgotten.id
    assert explained["causal_values"] == row.causal_values

    with pytest.raises(NotFound):
        explain_operational_exception(session, tenant_id, "not-an-exception")
    foreign = create_tenant(session, "Foreign unposted explanation tenant")
    with pytest.raises(NotFound):
        explain_operational_exception(session, foreign.id, row.id)

    # Booking it clears the entry and its identity stops explaining.
    post_sales_invoice(session, tenant_id, forgotten.id)
    with pytest.raises(NotFound):
        explain_operational_exception(session, tenant_id, row.id)
