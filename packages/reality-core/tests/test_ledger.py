from datetime import UTC, date, datetime
from decimal import Decimal

import pytest
from conftest import record_by_id

from reality.db.core import Document, SettlementAllocation
from reality.services.core import (
    InvalidOperation,
    NotFound,
    account_statement,
    allocate_credit_note,
    allocate_settlement,
    create_document,
    create_payment_term,
    create_tenant,
    financial_open_items,
    journal_rows,
    ledger_posting_groups,
    ledger_t_accounts,
    open_invoice_amount,
    open_item_control_accounts,
    payment_rows,
    post_customer_payment,
    post_ledger,
    post_sales_credit_note,
    post_sales_invoice,
    post_supplier_invoice,
    post_supplier_payment,
    record_customer_payment,
    update_party,
)


def test_sales_invoice_partial_payment_and_credit_are_balanced(session, business):
    invoice = create_document(
        session,
        business.tenant.id,
        "sales_invoice",
        "RE-10473",
        business.customer.id,
        "1470.00",
        document_date="2026-09-22",
    )
    invoice_entries = post_sales_invoice(session, business.tenant.id, invoice.id)
    payment_entries = post_customer_payment(
        session, business.tenant.id, invoice.id, "500.00"
    )
    credit = create_document(
        session,
        business.tenant.id,
        "credit_note",
        "GS-10473",
        business.customer.id,
        "100.00",
        document_date="2026-09-27",
    )
    credit_entries = post_sales_credit_note(session, business.tenant.id, credit.id)
    allocate_credit_note(session, business.tenant.id, credit.id, invoice.id, "100.00")

    for group in (invoice_entries, payment_entries, credit_entries):
        debits = sum(
            (entry.amount for entry in group if entry.debit_credit == "debit"),
            Decimal(),
        )
        credits = sum(
            (entry.amount for entry in group if entry.debit_credit == "credit"),
            Decimal(),
        )
        assert debits == credits
        assert len({entry.posting_group_id for entry in group}) == 1
        rendered = ledger_posting_groups(group)[0]
        assert rendered["balanced"] is True
        assert rendered["debit_total"] == rendered["credit_total"]
    assert open_invoice_amount(session, business.tenant.id, invoice.id) == Decimal(
        "870.0000"
    )
    payment_document = record_by_id(session, Document, payment_entries[0].document_id)
    assert payment_document.type == "customer_payment"
    assert payment_document.id != invoice.id

    # Two allocations, because a credit note settles the invoice the same way a
    # payment does. Before this it posted and settled nothing.
    invoice_control = next(
        entry.id for entry in invoice_entries if entry.account == "accounts_receivable"
    )
    allocations = session.query(SettlementAllocation).all()
    assert len(allocations) == 2
    assert {row.invoice_ledger_entry_id for row in allocations} == {invoice_control}
    assert {row.payment_ledger_entry_id for row in allocations} == {
        next(
            entry.id
            for entry in payment_entries
            if entry.account == "accounts_receivable"
        ),
        next(
            entry.id
            for entry in credit_entries
            if entry.account == "accounts_receivable"
        ),
    }


def test_supplier_invoice_and_partial_payment_leave_open_payable(session, business):
    invoice = create_document(
        session,
        business.tenant.id,
        "supplier_invoice",
        "ER-2201",
        business.supplier.id,
        "600.00",
        document_date="2026-09-22",
    )
    post_supplier_invoice(session, business.tenant.id, invoice.id)
    post_supplier_payment(session, business.tenant.id, invoice.id, "250.00")

    assert open_invoice_amount(session, business.tenant.id, invoice.id) == Decimal(
        "350.0000"
    )


def test_unbalanced_manual_posting_is_rejected(session, business):
    invoice = create_document(
        session,
        business.tenant.id,
        "sales_invoice",
        "RE-1",
        business.customer.id,
        10,
    )
    with pytest.raises(InvalidOperation, match="balance"):
        post_ledger(
            session,
            business.tenant.id,
            invoice.id,
            business.customer.id,
            [("accounts_receivable", "debit", 10), ("sales_revenue", "credit", 9)],
        )


def test_duplicate_invoice_posting_and_overpayment_are_rejected(session, business):
    invoice = create_document(
        session,
        business.tenant.id,
        "sales_invoice",
        "RE-2",
        business.customer.id,
        10,
    )
    post_sales_invoice(session, business.tenant.id, invoice.id)

    with pytest.raises(InvalidOperation, match="already posted"):
        post_sales_invoice(session, business.tenant.id, invoice.id)
    with pytest.raises(InvalidOperation, match="exceeds"):
        post_customer_payment(session, business.tenant.id, invoice.id, 11)


def test_one_payment_can_settle_multiple_invoices_tenant_safely(session, business):
    invoices = [
        create_document(
            session,
            business.tenant.id,
            "sales_invoice",
            number,
            business.customer.id,
            amount,
        )
        for number, amount in [("RE-10", 60), ("RE-11", 40)]
    ]
    invoice_entries = [
        post_sales_invoice(session, business.tenant.id, invoice.id)
        for invoice in invoices
    ]
    payment_entries = record_customer_payment(
        session,
        business.tenant.id,
        business.customer.id,
        100,
        payment_number="BANK-42",
    )
    payment_control = next(
        entry for entry in payment_entries if entry.account == "accounts_receivable"
    )
    for entries, amount in zip(invoice_entries, (60, 40), strict=True):
        invoice_control = next(
            entry for entry in entries if entry.account == "accounts_receivable"
        )
        allocate_settlement(
            session, business.tenant.id, payment_control.id, invoice_control.id, amount
        )

    assert [
        open_invoice_amount(session, business.tenant.id, invoice.id)
        for invoice in invoices
    ] == [Decimal("0.0000"), Decimal("0.0000")]
    with pytest.raises(InvalidOperation, match="unallocated payment"):
        allocate_settlement(
            session,
            business.tenant.id,
            payment_control.id,
            invoice_entries[0][0].id,
            1,
        )

    other_tenant = create_tenant(session, "Other GmbH")
    with pytest.raises(NotFound, match="LedgerEntry"):
        allocate_settlement(
            session, other_tenant.id, payment_control.id, invoice_entries[0][0].id, 1
        )


def test_finance_registers_share_ledger_and_allocation_truth(session, business):
    invoice = create_document(
        session,
        business.tenant.id,
        "sales_invoice",
        "RE-FIN",
        business.customer.id,
        100,
    )
    post_sales_invoice(session, business.tenant.id, invoice.id)
    post_customer_payment(
        session,
        business.tenant.id,
        invoice.id,
        40,
        payment_number="BANK-FIN",
    )

    item = financial_open_items(session, business.tenant.id)[0]
    payment = payment_rows(session, business.tenant.id)[0]
    journal = journal_rows(session, business.tenant.id)

    assert item["open"] == Decimal("60.0000")
    assert item["status"] == "partial"
    assert payment["allocated"] == Decimal("40.0000")
    assert payment["unallocated"] == Decimal("0.0000")
    assert len(journal) == 4
    statement = account_statement(
        session, business.tenant.id, "accounts_receivable", "EUR"
    )
    assert statement["balance"] == Decimal("60.0000")
    assert statement["entries"][-1]["balance"] == Decimal("60.0000")
    accounts = {row["account"]: row for row in ledger_t_accounts(journal)}
    assert accounts["accounts_receivable"]["balance"] == Decimal("60.0000")
    controls = open_item_control_accounts([item])
    assert controls[0]["receivables"][0]["open"] == Decimal("60.0000")
    assert controls[0]["payables"] == []


AGING_AS_OF = datetime(2026, 8, 31, 12, tzinfo=UTC)


def invoice_with_term(session, business, number, document_date, *, term_code=""):
    return create_document(
        session,
        business.tenant.id,
        "sales_invoice",
        number,
        business.customer.id,
        "1000.00",
        document_date=document_date,
        payment_term_code=term_code,
    )


def test_invoice_term_cascades_from_the_document_to_the_party(session, business):
    from reality.services.core import (
        aging_register,
        effective_payment_term,
        invoice_due_date,
    )

    tenant_id = business.tenant.id
    net30 = create_payment_term(session, tenant_id, "NET30", "Net 30 days", 30)
    net7 = create_payment_term(session, tenant_id, "NET7", "Net 7 days", 7)
    terms = {net30.id: net30, net7.id: net7}
    update_party(
        session,
        tenant_id,
        business.customer.id,
        business.customer.name,
        "customer",
        payment_term_code="NET30",
    )
    own_term = invoice_with_term(
        session, business, "RE-101", "2026-07-01", term_code="NET7"
    )
    from_party = invoice_with_term(session, business, "RE-102", "2026-07-01")

    # The invoice's own term wins; the party's term stands in when it has none.
    assert effective_payment_term(own_term, net30.id, terms) is net7
    assert effective_payment_term(from_party, net30.id, terms) is net30
    assert effective_payment_term(from_party, None, terms) is None
    assert invoice_due_date(from_party, net30) == date(2026, 7, 31)

    post_sales_invoice(session, tenant_id, own_term.id)
    post_sales_invoice(session, tenant_id, from_party.id)
    register = {
        row["document"].id: row
        for row in aging_register(session, tenant_id, as_of=AGING_AS_OF)
    }

    # The register resolves the same cascade, so an invoice with no term of its
    # own is not treated as due on issue while its customer has terms.
    assert register[own_term.id]["due_date"] == date(2026, 7, 8)
    assert register[from_party.id]["due_date"] == date(2026, 7, 31)


def test_invoice_due_date_rule(session, business):
    from reality.services.core import invoice_days_overdue, invoice_due_date

    tenant_id = business.tenant.id
    net30 = create_payment_term(session, tenant_id, "NET30", "Net 30 days", 30)
    immediate = create_payment_term(session, tenant_id, "NET0", "Due on receipt", 0)

    with_term = invoice_with_term(
        session, business, "RE-1", "2026-07-01", term_code="NET30"
    )
    zero_term = invoice_with_term(
        session, business, "RE-2", "2026-07-01", term_code="NET0"
    )
    no_term = invoice_with_term(session, business, "RE-3", "2026-07-01")
    empty_date = invoice_with_term(session, business, "RE-4", "")

    # The term advances the invoice date; without one the invoice date stands.
    assert invoice_due_date(with_term, net30) == date(2026, 7, 31)
    assert invoice_due_date(zero_term, immediate) == date(2026, 7, 1)
    assert invoice_due_date(no_term, None) == date(2026, 7, 1)
    # A document stating no date asserts nothing rather than defaulting (spec 234).
    assert invoice_due_date(empty_date, None) is None
    # A date the calendar does not have is refused where it is written, so no
    # reader has to judge it again. The source payload keeps whatever was sent.
    with pytest.raises(InvalidOperation, match="YYYY-MM-DD"):
        invoice_with_term(session, business, "RE-5", "not-a-date")
    session.rollback()

    assert invoice_days_overdue(date(2026, 7, 31), AGING_AS_OF) == 31
    # The day the term elapses is not yet late.
    assert invoice_days_overdue(date(2026, 8, 31), AGING_AS_OF) == 0
    assert invoice_days_overdue(date(2026, 9, 30), AGING_AS_OF) == 0
    assert invoice_days_overdue(None, AGING_AS_OF) is None


def test_one_aging_rule_serves_every_consumer(session, business):
    import inspect

    from reality.services.core import aging_register
    from reality.web.read_models import aging_page

    tenant_id = business.tenant.id
    create_payment_term(session, tenant_id, "NET30", "Net 30 days", 30)
    invoice = invoice_with_term(
        session, business, "RE-2001", "2026-07-01", term_code="NET30"
    )
    post_sales_invoice(session, tenant_id, invoice.id)

    register = {
        row["document"].id: row
        for row in aging_register(session, tenant_id, as_of=AGING_AS_OF)
    }
    paged, _ = aging_page(session, tenant_id, as_of=AGING_AS_OF)
    page = {row["document"].id: row for row in paged}

    assert register[invoice.id]["due_date"] == date(2026, 7, 31)
    assert register[invoice.id]["days_overdue"] == 31
    # One rule, two consumers: they cannot disagree about the same invoice.
    assert page[invoice.id]["due_date"] == register[invoice.id]["due_date"]
    assert page[invoice.id]["days_overdue"] == register[invoice.id]["days_overdue"]

    # The read model presents; it does not compute when money is due.
    source = inspect.getsource(aging_page)
    assert "timedelta" not in source
    assert "fromisoformat" not in source
