from datetime import UTC, datetime
from decimal import Decimal

import pytest

from reality.services.core import (
    InvalidOperation,
    NotFound,
    account_balance,
    allocate_settlement,
    allocate_supplier_credit_note,
    create_document,
    create_manual_document_with_lines,
    create_party,
    create_payment_term,
    create_tenant,
    open_invoice_amount,
    post_customer_payment,
    post_customer_refund,
    post_sales_credit_note,
    post_sales_invoice,
    post_supplier_credit_note,
    post_supplier_invoice,
    post_supplier_payment,
    post_supplier_refund,
)
from reality.services.exceptions import operational_exceptions


def invoice(session, business, number, amount, *, post=True):
    document = create_document(
        session,
        business.tenant.id,
        "sales_invoice",
        number,
        business.customer.id,
        amount,
        document_date="2026-08-01",
    )
    if post:
        post_sales_invoice(session, business.tenant.id, document.id)
    return document


def credit_note(session, business, number, total, *, line_total=None):
    document, _ = create_manual_document_with_lines(
        session,
        business.tenant.id,
        "credit_note",
        number,
        business.customer.id,
        [
            {
                "item_id": business.item.id,
                "quantity": "1",
                "unit": "pcs",
                "unit_price": line_total or total,
                "gross_amount": line_total or total,
            }
        ],
        total,
        document_date="2026-08-10",
    )
    return document


def test_a_credit_note_posts_the_reverse_of_an_invoice(session, business):
    tenant = business.tenant.id
    invoice(session, business, "RE-CN-1", "100.00")
    note = credit_note(session, business, "GS-1", "30.00")

    post_sales_credit_note(session, tenant, note.id)

    # Exactly what a sales invoice posts, in the other direction.
    assert account_balance(session, tenant, "sales_revenue", note.id) == Decimal(
        "30.0000"
    )
    assert account_balance(
        session, tenant, "accounts_receivable", note.id
    ) == Decimal("-30.0000")


def test_a_paid_invoice_can_still_be_credited(session, business):
    tenant = business.tenant.id
    paid = invoice(session, business, "RE-CN-PAID", "100.00")
    post_customer_payment(session, tenant, paid.id, "100.00")
    assert open_invoice_amount(session, tenant, paid.id) == Decimal(0)

    note = credit_note(session, business, "GS-PAID", "30.00")
    post_sales_credit_note(session, tenant, note.id)

    # The ordinary consumer return: paid at checkout, sent back later. The
    # company owes the customer, and the books say so.
    assert open_invoice_amount(session, tenant, note.id) == Decimal("30.0000")


def test_the_stated_total_is_what_posts(session, business):
    tenant = business.tenant.id
    invoice(session, business, "RE-CN-2", "100.00")
    # The paper says 25 and the line says 30. The paper is what somebody stated.
    note = credit_note(session, business, "GS-2", "25.00", line_total="30.00")

    post_sales_credit_note(session, tenant, note.id)

    assert account_balance(session, tenant, "sales_revenue", note.id) == Decimal(
        "25.0000"
    )


def test_posting_is_refused_where_it_would_be_wrong(session, business):
    tenant = business.tenant.id
    sales = invoice(session, business, "RE-CN-3", "100.00")
    note = credit_note(session, business, "GS-3", "30.00")

    # A sales invoice is not a credit note.
    with pytest.raises(InvalidOperation, match="credit note"):
        post_sales_credit_note(session, tenant, sales.id)

    # Posting once is accepted; twice is not.
    post_sales_credit_note(session, tenant, note.id)
    with pytest.raises(InvalidOperation, match="already posted"):
        post_sales_credit_note(session, tenant, note.id)

    # Nothing moves for nothing.
    empty = credit_note(session, business, "GS-ZERO", "0")
    with pytest.raises(InvalidOperation):
        post_sales_credit_note(session, tenant, empty.id)


def test_a_credit_may_be_netted_against_an_open_invoice(session, business):
    from reality.services.core import _settlement_control_entry

    tenant = business.tenant.id
    open_invoice = invoice(session, business, "RE-CN-4", "100.00")
    note = credit_note(session, business, "GS-4", "30.00")
    post_sales_credit_note(session, tenant, note.id)

    allocate_settlement(
        session,
        tenant,
        _settlement_control_entry(session, tenant, note.id).id,
        _settlement_control_entry(session, tenant, open_invoice.id).id,
        "30.00",
    )

    # The invoice falls exactly as a payment would make it fall.
    assert open_invoice_amount(session, tenant, open_invoice.id) == Decimal("70.0000")
    assert open_invoice_amount(session, tenant, note.id) == Decimal(0)


def test_a_credit_may_be_refunded(session, business):
    tenant = business.tenant.id
    paid = invoice(session, business, "RE-CN-5", "100.00")
    post_customer_payment(session, tenant, paid.id, "100.00")
    note = credit_note(session, business, "GS-5", "30.00")
    post_sales_credit_note(session, tenant, note.id)
    cash_before = account_balance(session, tenant, "cash")

    post_customer_refund(session, tenant, note.id, "30.00")

    # Money leaves and the obligation is settled.
    assert account_balance(session, tenant, "cash") == cash_before - Decimal("30.0000")
    assert open_invoice_amount(session, tenant, note.id) == Decimal(0)


def test_settling_is_refused_beyond_what_is_owed(session, business):
    tenant = business.tenant.id
    invoice(session, business, "RE-CN-6", "100.00")
    note = credit_note(session, business, "GS-6", "30.00")
    post_sales_credit_note(session, tenant, note.id)

    # Everything owed may be refunded.
    post_customer_refund(session, tenant, note.id, "30.00")

    # Nothing beyond it, which is what makes the acceptance above a rule.
    with pytest.raises(InvalidOperation):
        post_customer_refund(session, tenant, note.id, "0.01")


# --- The credit that comes the other way (spec 089) ------------------------


def supplier_invoice(session, business, number, amount, *, post=True, date="2026-08-01"):
    document = create_document(
        session,
        business.tenant.id,
        "supplier_invoice",
        number,
        business.supplier.id,
        amount,
        document_date=date,
    )
    if post:
        post_supplier_invoice(session, business.tenant.id, document.id)
    return document


def supplier_credit(session, business, number, amount, *, post=True, date="2026-08-05"):
    document = create_document(
        session,
        business.tenant.id,
        "supplier_credit_note",
        number,
        business.supplier.id,
        amount,
        document_date=date,
    )
    if post:
        post_supplier_credit_note(session, business.tenant.id, document.id)
    return document


def test_a_supplier_credit_note_posts_the_reverse(session, business):
    tenant_id = business.tenant.id
    supplier_invoice(session, business, "ER-089", "1000.00")
    note = supplier_credit(session, business, "SG-089", "150.00")

    # The exact opposite of the supplier invoice posting, with the credit note's
    # own gross amount and nothing derived, apportioned or rounded.
    assert account_balance(session, tenant_id, "accounts_payable", note.id) == Decimal(150)
    assert account_balance(session, tenant_id, "inventory", note.id) == Decimal(-150)

    # And it is settleable: what it claims from the supplier is its own amount.
    assert open_invoice_amount(session, tenant_id, note.id) == Decimal(150)


def test_a_supplier_credit_note_posts_once_and_for_something(session, business):
    tenant_id = business.tenant.id
    note = supplier_credit(session, business, "SG-089-TWICE", "150.00")

    with pytest.raises(InvalidOperation, match="already posted"):
        post_supplier_credit_note(session, tenant_id, note.id)

    nothing = create_document(
        session,
        tenant_id,
        "supplier_credit_note",
        "SG-089-ZERO",
        business.supplier.id,
        "0.00",
        document_date="2026-08-05",
    )
    with pytest.raises(InvalidOperation):
        post_supplier_credit_note(session, tenant_id, nothing.id)

    # A document that is not a supplier credit note is refused, and the positive
    # control is that a real one posts on the very next line.
    invoice_document = supplier_invoice(session, business, "ER-089-NOT", "10.00")
    with pytest.raises(InvalidOperation, match="not a supplier credit note"):
        post_supplier_credit_note(session, tenant_id, invoice_document.id)
    assert supplier_credit(session, business, "SG-089-OK", "10.00") is not None


def test_a_supplier_credit_settles_only_its_own_supplier(session, business):
    tenant_id = business.tenant.id
    other = create_party(session, tenant_id, "Other Supplier GmbH", "supplier")
    theirs = create_document(
        session, tenant_id, "supplier_invoice", "ER-089-OTHER", other.id,
        "500.00", document_date="2026-08-01",
    )
    post_supplier_invoice(session, tenant_id, theirs.id)
    ours = supplier_invoice(session, business, "ER-089-OURS", "500.00")
    note = supplier_credit(session, business, "SG-089-PARTY", "100.00")

    with pytest.raises(InvalidOperation, match="own supplier"):
        allocate_supplier_credit_note(session, tenant_id, note.id, theirs.id, "100.00")

    # An unposted credit has no control entry to settle with.
    unposted = supplier_credit(
        session, business, "SG-089-UNPOSTED", "100.00", post=False
    )
    with pytest.raises(InvalidOperation):
        allocate_supplier_credit_note(session, tenant_id, unposted.id, ours.id, "100.00")

    # The positive control: the same credit against its own supplier's invoice.
    allocate_supplier_credit_note(session, tenant_id, note.id, ours.id, "100.00")
    assert open_invoice_amount(session, tenant_id, ours.id) == Decimal(400)


def test_netting_leaves_the_remainder_open(session, business):
    tenant_id = business.tenant.id
    small = supplier_invoice(session, business, "ER-089-SMALL", "100.00")
    note = supplier_credit(session, business, "SG-089-BIG", "250.00")

    allocate_supplier_credit_note(session, tenant_id, note.id, small.id, "100.00")

    # The invoice is settled and the excess is still claimable from the supplier.
    assert open_invoice_amount(session, tenant_id, small.id) == Decimal(0)
    assert open_invoice_amount(session, tenant_id, note.id) == Decimal(150)

    # And what is left cannot be netted beyond what either document holds.
    another = supplier_invoice(session, business, "ER-089-REST", "500.00")
    with pytest.raises(InvalidOperation):
        allocate_supplier_credit_note(session, tenant_id, note.id, another.id, "200.00")
    allocate_supplier_credit_note(session, tenant_id, note.id, another.id, "150.00")
    assert open_invoice_amount(session, tenant_id, note.id) == Decimal(0)
    assert open_invoice_amount(session, tenant_id, another.id) == Decimal(350)


def test_a_supplier_refund_settles_the_credit(session, business):
    tenant_id = business.tenant.id
    paid = supplier_invoice(session, business, "ER-089-PAID", "400.00")
    post_supplier_payment(session, tenant_id, paid.id, "400.00")
    assert open_invoice_amount(session, tenant_id, paid.id) == Decimal(0)

    # The credit arrives after the invoice was paid: nothing is open to net it
    # against, and the company's money is with the supplier.
    note = supplier_credit(session, business, "SG-089-REFUND", "60.00")
    with pytest.raises(InvalidOperation, match="still claims"):
        post_supplier_refund(session, tenant_id, note.id, "61.00")

    entries = post_supplier_refund(session, tenant_id, note.id, "60.00")

    assert open_invoice_amount(session, tenant_id, note.id) == Decimal(0)
    refund = next(entry for entry in entries if entry.account == "cash")
    assert refund.debit_credit == "debit"
    assert Decimal(refund.amount) == Decimal(60)


def test_a_credit_takes_a_payable_off_the_overdue_queue(session, business):
    tenant_id = business.tenant.id
    create_payment_term(session, tenant_id, "NET30", "Net 30 days", 30)
    overdue = create_document(
        session, tenant_id, "supplier_invoice", "ER-089-OVERDUE",
        business.supplier.id, "300.00",
        document_date="2026-07-01", payment_term_code="NET30",
    )
    post_supplier_invoice(session, tenant_id, overdue.id)
    as_of = datetime(2026, 8, 31, 12, tzinfo=UTC)
    reported = {
        row.record_id
        for row in operational_exceptions(session, tenant_id, as_of=as_of)
        if row.class_id == "overdue_payable"
    }
    assert overdue.id in reported

    # A credit settles the last of it, and nothing downstream needed telling
    # that a credit was involved rather than a payment.
    note = supplier_credit(session, business, "SG-089-OVERDUE", "300.00")
    allocate_supplier_credit_note(session, tenant_id, note.id, overdue.id, "300.00")

    reported = {
        row.record_id
        for row in operational_exceptions(session, tenant_id, as_of=as_of)
        if row.class_id == "overdue_payable"
    }
    assert overdue.id not in reported


def test_one_allocation_service_settles_both_sides(session, business):
    """DR-003: no second way of reducing a payable may appear."""
    import inspect

    from reality.services import core

    for name in ("allocate_credit_note", "allocate_supplier_credit_note"):
        source = inspect.getsource(getattr(core, name))
        assert "allocate_settlement(" in source
        # Neither writes an allocation of its own.
        assert "SettlementAllocation(" not in source


def test_supplier_credit_operations_are_tenant_scoped(session, business):
    tenant_id = business.tenant.id
    note = supplier_credit(session, business, "SG-089-TENANT", "50.00")
    foreign = create_tenant(session, "Foreign supplier credit tenant")

    with pytest.raises(NotFound):
        post_supplier_refund(session, foreign.id, note.id, "50.00")
    with pytest.raises(NotFound):
        open_invoice_amount(session, foreign.id, note.id)

    # The positive control: its own tenant can still do both.
    assert open_invoice_amount(session, tenant_id, note.id) == Decimal(50)
