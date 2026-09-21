from decimal import Decimal

import pytest

from reality.db.core import PaymentTerm
from reality.services.core import (
    InvalidOperation,
    NotFound,
    aging_register,
    create_document,
    create_party,
    create_payment_term,
    payment_terms,
    post_supplier_invoice,
    set_master_data_active,
    update_payment_term,
)


def test_payment_terms_are_tenant_scoped_master_data(session, business):
    term = create_payment_term(
        session,
        business.tenant.id,
        "net_30",
        "Net 30 days",
        30,
        source_system="erp",
        external_id="ZB30",
    )
    party = create_party(
        session,
        business.tenant.id,
        "Terms Customer",
        "customer",
        payment_term_code="net_30",
    )

    assert term.code == "NET_30"
    assert party.payment_term_id == term.id
    assert payment_terms(session, business.tenant.id) == [term]

    set_master_data_active(session, business.tenant.id, PaymentTerm, term.id, False)
    with pytest.raises(NotFound, match="Active payment term"):
        create_party(
            session,
            business.tenant.id,
            "Blocked Assignment",
            "customer",
            payment_term_code="NET_30",
        )


def test_payment_term_validates_code_and_due_days(session, business):
    create_payment_term(session, business.tenant.id, "DUE", "Due now", 0)
    with pytest.raises(InvalidOperation, match="already exists"):
        create_payment_term(session, business.tenant.id, "due", "Duplicate", 1)
    with pytest.raises(InvalidOperation, match="cannot be negative"):
        create_payment_term(session, business.tenant.id, "BAD", "Bad", -1)


# --- The early-payment discount (spec 088) ---------------------------------


def test_a_payment_term_can_state_a_discount(session, business):
    term = create_payment_term(
        session,
        business.tenant.id,
        "SKONTO",
        "2% 10 days, net 30",
        30,
        discount_percent="2",
        discount_days=10,
    )

    assert term.due_days == 30
    assert term.discount_percent == Decimal("2.000")
    assert term.discount_days == 10

    # The positive control for the other direction: a term that states neither
    # figure carries neither, and nothing about it has changed.
    plain = create_payment_term(session, business.tenant.id, "NET14", "Net 14", 14)
    assert plain.discount_percent is None
    assert plain.discount_days is None

    updated = update_payment_term(
        session,
        business.tenant.id,
        plain.id,
        plain.code,
        plain.name,
        14,
        discount_percent="1.5",
        discount_days=7,
    )
    assert updated.discount_percent == Decimal("1.500")
    assert updated.discount_days == 7


def test_a_discount_rate_and_window_are_validated(session, business):
    tenant_id = business.tenant.id

    # A rate has to be a rate: nothing off is not a discount, and a hundred per
    # cent off is not a payment condition.
    for rate in ("0", "-1", "100", "150"):
        with pytest.raises(InvalidOperation, match="discount"):
            create_payment_term(
                session,
                tenant_id,
                f"BAD{rate}",
                "Bad",
                30,
                discount_percent=rate,
                discount_days=10,
            )
    with pytest.raises(InvalidOperation, match="discount"):
        create_payment_term(
            session,
            tenant_id,
            "BADDAYS",
            "Bad",
            30,
            discount_percent="2",
            discount_days=-1,
        )

    # Half a discount condition is not a condition. Either half alone leaves
    # every derivation guessing what the other one was meant to be.
    with pytest.raises(InvalidOperation, match="discount"):
        create_payment_term(
            session, tenant_id, "HALF1", "Rate only", 30, discount_percent="2"
        )
    with pytest.raises(InvalidOperation, match="discount"):
        create_payment_term(
            session, tenant_id, "HALF2", "Days only", 30, discount_days=10
        )

    # The positive control: the same figures together are accepted, and a term
    # stating neither is accepted as it always was.
    assert (
        create_payment_term(
            session,
            tenant_id,
            "GOOD",
            "Good",
            30,
            discount_percent="2",
            discount_days=10,
        ).discount_days
        == 10
    )
    assert create_payment_term(session, tenant_id, "PLAIN", "Plain", 30) is not None


def test_the_discount_deadline_is_one_shared_rule(session, business):
    from datetime import date

    from reality.services.core import (
        invoice_discount_date,
        invoice_due_date,
    )

    term = create_payment_term(
        session,
        business.tenant.id,
        "SK10",
        "2% 10",
        30,
        discount_percent="2",
        discount_days=10,
    )
    invoice = create_document(
        session,
        business.tenant.id,
        "supplier_invoice",
        "ER-088-RULE",
        business.supplier.id,
        "1000.00",
        document_date="2026-08-01",
        payment_term_code="SK10",
    )
    post_supplier_invoice(session, business.tenant.id, invoice.id)

    # The window is placed the way the due date is placed: the invoice's own
    # date advanced by a number of days the company stated.
    assert invoice_due_date(invoice, term) == date(2026, 8, 31)
    assert invoice_discount_date(invoice, term) == date(2026, 8, 11)

    # The register carries both, so no consumer derives either for itself.
    row = next(
        entry
        for entry in aging_register(session, business.tenant.id)
        if entry["document"].id == invoice.id
    )
    assert row["due_date"] == date(2026, 8, 31)
    assert row["discount_date"] == date(2026, 8, 11)
    assert row["payment_term"] is not None and row["payment_term"].id == term.id

    # The positive control for the silence: a term granting no discount places
    # no window, while still placing a due date.
    plain = create_payment_term(session, business.tenant.id, "NET7", "Net 7", 7)
    assert invoice_due_date(invoice, plain) == date(2026, 8, 8)
    assert invoice_discount_date(invoice, plain) is None
    assert invoice_discount_date(invoice, None) is None
