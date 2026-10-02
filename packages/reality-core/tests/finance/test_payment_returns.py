"""Spec 297: returned direct debits, chargebacks and payment fees; spec 321 links."""

import json
from datetime import date
from decimal import Decimal

import pytest
from conftest import record_by_id
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from reality.db.core import (
    BusinessEvent,
    LedgerEntry,
    LedgerReversal,
    PaymentReturn,
    SourceRecord,
)
from reality.domain.finance import ACCOUNT_ROLES
from reality.services import core
from reality.services.exceptions import operational_exceptions
from reality.services.finance.accounts import (
    create_account,
    initialize_accounts,
    list_accounts,
)
from reality.tools.application import (
    approve_and_execute_proposal,
    create_change_proposal,
)

# --- T005: the record and the role ---------------------------------------------------


def _paid_invoice(session, business, number="RE-297", amount="100.00", paid=None):
    tenant = business.tenant.id
    invoice = core.create_document(
        session,
        tenant,
        "sales_invoice",
        number,
        business.customer.id,
        amount,
        document_date="2026-09-01",
    )
    core.post_sales_invoice(session, tenant, invoice.id)
    entries = core.post_customer_payment(
        session, tenant, invoice.id, paid or amount, payment_number=f"PAY-{number}"
    )
    return invoice, entries[0]


def _row(session, business, payment_document_id, **columns):
    tenant = business.tenant.id
    values = {
        "id": core.uid("prt"),
        "tenant_id": tenant,
        "payment_document_id": payment_document_id,
        "kind": "direct_debit_return",
        "reason": "MD06",
        "reference": "",
        "returned_on": date(2026, 10, 2),
        "fee_amount": Decimal(0),
        "fee_bearer": "none",
        "source_record_id": core.create_master_source_record(
            session, tenant, "payment_return", "manual", core.uid("t005"), {}
        ).id,
        **columns,
    }
    return PaymentReturn(**values)


def _insert(session, record):
    with session.begin_nested():
        session.add(record)
        session.flush()


def test_a_return_names_its_kind_and_who_bears_the_fee(session, business):
    _, entry = _paid_invoice(session, business)
    # Positive control: a well-formed return is accepted.
    _insert(session, _row(session, business, entry.document_id))

    _, other = _paid_invoice(session, business, "RE-297-B")
    for columns, constraint in (
        ({"kind": "refund"}, "ck_payment_return_kind"),
        ({"fee_bearer": "partner"}, "ck_payment_return_fee_bearer"),
        ({"fee_amount": Decimal(-1)}, "ck_payment_return_fee"),
        (
            {"fee_amount": Decimal(3), "fee_bearer": "none"},
            "ck_payment_return_fee_bearer",
        ),
        (
            {"fee_amount": Decimal(0), "fee_bearer": "customer"},
            "ck_payment_return_fee_bearer",
        ),
        ({"reason": "  "}, "ck_payment_return_reason"),
    ):
        with pytest.raises(IntegrityError, match=constraint):
            _insert(
                session,
                _row(session, business, other.document_id, **columns),
            )


def test_a_payment_is_returned_once(session, business):
    _, entry = _paid_invoice(session, business)
    _insert(session, _row(session, business, entry.document_id))

    with pytest.raises(IntegrityError, match="uq_payment_return_payment"):
        _insert(session, _row(session, business, entry.document_id))


def test_a_return_does_not_store_what_it_caused(session, business):
    """Spec 321 FR-001: the reversal and fee documents point back, not forward."""
    columns = set(PaymentReturn.__table__.columns.keys())
    assert not columns & {
        "ledger_reversal_id",
        "fee_document_id",
        "fee_charge_document_id",
    }
    assert {"payment_document_id", "source_record_id", "fee_amount"} <= columns


def test_the_payment_fee_role_exists_and_can_hold_an_account(session, business):
    tenant = business.tenant.id
    assert "payment_fee_expense" in ACCOUNT_ROLES

    account = create_account(
        session,
        tenant,
        code="6855",
        name="Payment fees",
        role="payment_fee_expense",
        expected_revision=list_accounts(session, tenant)["revision"],
    )

    assert account["role"] == "payment_fee_expense"


# --- T007: recording a returned payment ------------------------------------------------


def _fee_account(session, tenant):
    from reality.services.finance.accounts import set_default_account

    state = list_accounts(session, tenant)
    if "payment_fee_expense" in state["defaults"]:
        return
    initialize_accounts(session, tenant)
    state = list_accounts(session, tenant)
    if "payment_fee_expense" in state["defaults"]:
        return
    account = create_account(
        session,
        tenant,
        code="6855",
        name="Payment fees",
        role="payment_fee_expense",
        expected_revision=state["revision"],
    )
    set_default_account(
        session,
        tenant,
        role="payment_fee_expense",
        account_id=account["id"],
        expected_revision=list_accounts(session, tenant)["revision"],
    )


def _return(session, tenant, payment_id, **arguments):
    values = {
        "payment_document_id": payment_id,
        "kind": "direct_debit_return",
        "returned_on": "2026-10-02",
        "reason": "MD06 refund on customer request",
        "reference": "RTN-4711",
        **arguments,
    }
    proposal = create_change_proposal(
        session, tenant, "finance.payment.return", values, actor_type="human"
    )
    review = json.loads(proposal.output)["payment_return"]
    receipt = json.loads(
        approve_and_execute_proposal(session, tenant, proposal.id).output
    )
    return review, receipt


def _balance(session, tenant, role):
    return core.account_balance(session, tenant, role)


def test_a_returned_direct_debit_reverses_the_payment_and_reopens_the_invoice(
    session, business
):
    tenant = business.tenant.id
    invoice, entry = _paid_invoice(session, business)
    assert core.open_invoice_amount(session, tenant, invoice.id) == 0

    review, receipt = _return(session, tenant, entry.document_id)

    assert [row["invoice_id"] for row in review["reopened"]] == [invoice.id]
    assert Decimal(review["reopened"][0]["open_after"]) == 100
    assert core.open_invoice_amount(session, tenant, invoice.id) == 100
    row = record_by_id(session, PaymentReturn, receipt["id"])
    assert (row.kind, row.reason, row.reference) == (
        "direct_debit_return",
        "MD06 refund on customer request",
        "RTN-4711",
    )
    reversal = record_by_id(session, LedgerReversal, receipt["ledger_reversal_id"])
    assert reversal.original_posting_group_id == entry.posting_group_id
    event = session.scalars(
        select(BusinessEvent).where(
            BusinessEvent.event_type == "payment.returned",
            BusinessEvent.subject_id == row.id,
        )
    ).one()
    assert json.loads(event.payload)["reopened_invoice_ids"] == [invoice.id]


def test_a_fee_charged_on_is_the_customers_own_charge_and_recovers_the_cost(
    session, business
):
    tenant = business.tenant.id
    _fee_account(session, tenant)
    invoice, entry = _paid_invoice(session, business)

    _, receipt = _return(
        session, tenant, entry.document_id, fee_amount="3.50", fee_bearer="customer"
    )

    assert core.open_invoice_amount(session, tenant, invoice.id) == 100
    assert core.open_invoice_amount(
        session, tenant, receipt["fee_charge_document_id"]
    ) == Decimal("3.50")
    # The bank took the fee from the account; the customer now owes it, so the
    # company's own cost nets to zero.
    assert _balance(session, tenant, "payment_fee_expense") == 0


def test_a_chargeback_fee_kept_by_the_company_is_an_expense(session, business):
    tenant = business.tenant.id
    _fee_account(session, tenant)
    _, entry = _paid_invoice(session, business)

    _, receipt = _return(
        session,
        tenant,
        entry.document_id,
        kind="chargeback",
        reason="Fraudulent, card not present",
        reference="dp_1PzX",
        fee_amount="15",
        fee_bearer="company",
    )

    assert receipt["kind"] == "chargeback" and receipt["reference"] == "dp_1PzX"
    assert receipt["fee_charge_document_id"] is None
    assert _balance(session, tenant, "payment_fee_expense") == Decimal(15)


def test_a_zero_fee_posts_nothing(session, business):
    tenant = business.tenant.id
    _, entry = _paid_invoice(session, business)

    _, receipt = _return(session, tenant, entry.document_id)

    assert receipt["fee_document_id"] is None and receipt["fee_bearer"] == "none"


def test_a_payment_of_two_invoices_reopens_both(session, business):
    tenant = business.tenant.id
    first = core.create_document(
        session,
        tenant,
        "sales_invoice",
        "RE-297-1",
        business.customer.id,
        "60",
        document_date="2026-09-01",
    )
    second = core.create_document(
        session,
        tenant,
        "sales_invoice",
        "RE-297-2",
        business.customer.id,
        "40",
        document_date="2026-09-01",
    )
    for invoice in (first, second):
        core.post_sales_invoice(session, tenant, invoice.id)
    payment = core.record_customer_payment(
        session, tenant, business.customer.id, "100", payment_number="PAY-297-2"
    )
    cash_entry = next(e for e in payment if e.account == "accounts_receivable")
    for invoice, amount in ((first, "60"), (second, "40")):
        control = core._settlement_control_entry(session, tenant, invoice.id)
        core.allocate_settlement(session, tenant, cash_entry.id, control.id, amount)

    review, _ = _return(session, tenant, cash_entry.document_id)

    assert {row["number"] for row in review["reopened"]} == {"RE-297-1", "RE-297-2"}
    assert core.open_invoice_amount(session, tenant, first.id) == 60
    assert core.open_invoice_amount(session, tenant, second.id) == 40


@pytest.mark.parametrize(
    ("case", "arguments", "code"),
    [
        ("returned", {}, "payment_return_already_returned"),
        ("reversed", {}, "payment_return_already_reversed"),
        ("invoice", {}, "payment_return_not_customer_payment"),
        ("ok", {"reason": " "}, "payment_return_reason_missing"),
        ("ok", {"fee_amount": "-1"}, "payment_return_fee_invalid"),
        (
            "ok",
            {"fee_amount": "1.00001", "fee_bearer": "company"},
            "payment_return_fee_invalid",
        ),
        (
            "ok",
            {"fee_amount": "3", "fee_bearer": "none"},
            "payment_return_fee_bearer_invalid",
        ),
        (
            "ok",
            {"fee_amount": "0", "fee_bearer": "customer"},
            "payment_return_fee_bearer_invalid",
        ),
    ],
)
def test_a_return_names_why_it_is_refused(session, business, case, arguments, code):
    from reality.services.payment_returns import preview_return

    tenant = business.tenant.id
    invoice, entry = _paid_invoice(session, business)
    target = entry.document_id
    if case == "returned":
        _return(session, tenant, target)
    elif case == "reversed":
        core.reverse_ledger_posting_group(
            session, tenant, entry.posting_group_id, reason="Entered twice"
        )
    elif case == "invoice":
        target = invoice.id

    with pytest.raises(core.InvalidOperation) as refused:
        preview_return(
            session,
            tenant,
            {
                "payment_document_id": target,
                "kind": "direct_debit_return",
                "returned_on": "2026-10-02",
                "reason": "MD06",
                **arguments,
            },
        )
    assert refused.value.code == code


def test_a_fee_needs_the_payment_fee_account(session, business):
    tenant = business.tenant.id
    _, entry = _paid_invoice(session, business)
    with pytest.raises(core.InvalidOperation) as refused:
        _return(
            session, tenant, entry.document_id, fee_amount="3", fee_bearer="company"
        )
    assert refused.value.code == "finance_account_default_missing"


def test_replaying_a_confirmed_return_records_it_once(session, business):
    from reality.services.payment_returns import record_return

    tenant = business.tenant.id
    _, entry = _paid_invoice(session, business)
    _, receipt = _return(session, tenant, entry.document_id)
    source = record_by_id(session, SourceRecord, receipt["source_record_id"])

    again = record_return(
        session,
        tenant,
        payment_document_id=entry.document_id,
        kind="direct_debit_return",
        returned_on="2026-10-02",
        reason="MD06 refund on customer request",
        action_id=source.external_id,
        actor_id=None,
    )

    assert again["id"] == receipt["id"]


def test_a_return_stays_in_its_company(session, business):
    from reality.services.payment_returns import return_detail

    tenant = business.tenant.id
    _, entry = _paid_invoice(session, business)
    _, receipt = _return(session, tenant, entry.document_id)
    other = core.create_tenant(session, "Other GmbH")

    with pytest.raises(core.NotFound):
        return_detail(session, other.id, receipt["id"])


# --- T009: following up the reopened invoice ---------------------------------------------


def _findings(session, tenant):
    return [
        row
        for row in operational_exceptions(session, tenant)
        if row.class_id == "payment_returned"
    ]


def test_a_reopened_invoice_is_reported_until_it_is_paid_again(session, business):
    tenant = business.tenant.id
    invoice, entry = _paid_invoice(session, business)
    # Positive control for the absence: a paid invoice with no return reports nothing.
    assert _findings(session, tenant) == []

    _return(session, tenant, entry.document_id)
    (finding,) = _findings(session, tenant)
    assert finding.record_id == invoice.id
    assert finding.causal_values["kind"] == "direct_debit_return"
    assert finding.causal_values["reference"] == "RTN-4711"

    core.post_customer_payment(
        session, tenant, invoice.id, "100", payment_number="PAY-AGAIN"
    )

    assert _findings(session, tenant) == []


def test_a_returned_payment_leaves_no_unallocated_money_behind(session, business):
    tenant = business.tenant.id
    _, entry = _paid_invoice(session, business)
    # Positive control: money not allocated to an invoice is reported.
    over = create_change_proposal(
        session,
        tenant,
        "finance.settlement.apply",
        {
            "mode": "payment",
            "document_id": _posted_invoice(session, business, "RE-297-OV").id,
            "amount": "101",
            "allocation_amount": "100",
            "expected_revision": list_accounts(session, tenant)["revision"],
            "reference": "Overpaid transfer",
            "effective_at": "2026-09-10T08:00:00Z",
        },
        actor_type="human",
    )
    approve_and_execute_proposal(session, tenant, over.id)

    def unmatched():
        return {
            row.record_id
            for row in operational_exceptions(session, tenant)
            if row.class_id == "unmatched_financial_event"
        }

    before = unmatched()
    assert before

    _return(session, tenant, entry.document_id)

    # The reversal's own receivable entry is no new unallocated money.
    assert unmatched() == before


def test_the_invoice_inspector_names_the_return(session, business):
    from reality.web.api import document_inspector

    tenant = business.tenant.id
    invoice, entry = _paid_invoice(session, business)
    _, receipt = _return(session, tenant, entry.document_id)

    rows = next(
        section["rows"]
        for section in document_inspector(session, tenant, invoice.id)["sections"]
        if section["title"] == "Returned payments"
    )

    assert rows[0]["label"] == "Returned direct debit"
    assert rows[0]["link"]["id"] == receipt["source_record_id"]


# --- T011: a fee the provider deducted from a payment --------------------------------------


def _settle_with_fee(
    session, business, invoice, cash, fee, side="customer", category="payment_fee"
):
    tenant = business.tenant.id
    arguments = {
        "mode": "payment",
        "document_id": invoice.id,
        "amount": cash,
        "allocation_amount": cash,
        "expected_revision": list_accounts(session, tenant)["revision"],
        "reference": "Stripe payout po_1",
        "effective_at": "2026-09-10T08:00:00Z",
    }
    if fee:
        arguments["reduction"] = {
            "amount": fee,
            "reason_category": category,
            "reason": "Stated by the provider",
        }
    proposal = create_change_proposal(
        session, tenant, "finance.settlement.apply", arguments, actor_type="human"
    )
    return json.loads(approve_and_execute_proposal(session, tenant, proposal.id).output)


def _posted_invoice(session, business, number, amount="100"):
    invoice = core.create_document(
        session,
        business.tenant.id,
        "sales_invoice",
        number,
        business.customer.id,
        amount,
        document_date="2026-09-01",
    )
    core.post_sales_invoice(session, business.tenant.id, invoice.id)
    return invoice


def _preview(session, tenant, payment_id, **values):
    from reality.services.payment_returns import preview_return

    return preview_return(
        session,
        tenant,
        {
            "payment_document_id": payment_id,
            "kind": "chargeback",
            "returned_on": "2026-10-02",
            "reason": "Disputed",
            **values,
        },
    )


def test_a_deducted_payment_fee_settles_the_invoice_and_is_an_expense(
    session, business
):
    tenant = business.tenant.id
    _fee_account(session, tenant)
    invoice = core.create_document(
        session,
        tenant,
        "sales_invoice",
        "RE-297-PSP",
        business.customer.id,
        "100",
        document_date="2026-09-01",
    )
    core.post_sales_invoice(session, tenant, invoice.id)

    _settle_with_fee(session, business, invoice, "97", "3")

    assert core.open_invoice_amount(session, tenant, invoice.id) == 0
    assert _balance(session, tenant, "payment_fee_expense") == Decimal(3)
    assert _balance(session, tenant, "customer_reduction") == 0


@pytest.mark.parametrize("category", ["payment_fee", "early_payment_discount"])
def test_a_payment_settled_with_a_reduction_is_returned_only_after_it_is_reversed(
    session, business, category
):
    from reality.db.core import Document as DocumentRow

    tenant = business.tenant.id
    _fee_account(session, tenant)
    # Positive control: a settlement payment without a reduction, recorded under a
    # confirmation the same way, can be returned.
    plain = _settle_with_fee(
        session, business, _posted_invoice(session, business, "RE-297-P0"), "100", None
    )
    assert _preview(session, tenant, plain["payment"]["document_id"])["reopened"]

    invoice = _posted_invoice(session, business, f"RE-297-{category}")
    receipt = _settle_with_fee(session, business, invoice, "97", "3", category=category)
    payment_id = receipt["payment"]["document_id"]

    with pytest.raises(core.InvalidOperation) as refused:
        _preview(session, tenant, payment_id)
    assert refused.value.code == "payment_return_reduction_active"

    adjustment = session.scalar(
        select(DocumentRow).where(
            DocumentRow.tenant_id == tenant,
            DocumentRow.type == "customer_settlement_adjustment",
        )
    )
    group = session.scalar(
        select(LedgerEntry.posting_group_id).where(
            LedgerEntry.tenant_id == tenant, LedgerEntry.document_id == adjustment.id
        )
    )
    core.reverse_ledger_posting_group(session, tenant, group, reason="Fee disputed")

    (reopened,) = _preview(session, tenant, payment_id)["reopened"]
    assert (reopened["number"], reopened["open_after"]) == (
        f"RE-297-{category}",
        "100.0000",
    )


def test_a_refund_of_the_payment_is_open_again_but_not_reported_as_an_invoice(
    session, business
):
    from reality.services.payment_returns import return_detail

    tenant = business.tenant.id
    invoice = _posted_invoice(session, business, "RE-297-RF")
    proposal = create_change_proposal(
        session,
        tenant,
        "finance.settlement.apply",
        {
            "mode": "payment",
            "document_id": invoice.id,
            "amount": "120",
            "allocation_amount": "100",
            "expected_revision": list_accounts(session, tenant)["revision"],
            "reference": "Overpaid transfer",
            "effective_at": "2026-09-10T08:00:00Z",
        },
        actor_type="human",
    )
    paid = json.loads(approve_and_execute_proposal(session, tenant, proposal.id).output)
    payment_id = paid["payment"]["document_id"]
    refund = create_change_proposal(
        session,
        tenant,
        "finance.settlement.apply",
        {
            "mode": "refund_credit",
            "document_id": payment_id,
            "amount": "20",
            "expected_revision": list_accounts(session, tenant)["revision"],
            "reference": "Refund of the overpayment",
            "effective_at": "2026-09-11T08:00:00Z",
        },
        actor_type="human",
    )
    approve_and_execute_proposal(session, tenant, refund.id)

    _, receipt = _return(session, tenant, payment_id)

    # The refund is owed back too, and the preview says so with its type ...
    assert sorted(
        row["type"] for row in return_detail(session, tenant, receipt["id"])["reopened"]
    ) == [
        "customer_refund",
        "sales_invoice",
    ]
    # ... but only the invoice is reported as an invoice open again.
    (finding,) = _findings(session, tenant)
    assert finding.record_id == invoice.id


def test_an_invoice_whose_payments_came_back_twice_is_reported_once(session, business):
    tenant = business.tenant.id
    invoice, entry = _paid_invoice(session, business)
    _return(session, tenant, entry.document_id)
    again = core.post_customer_payment(
        session, tenant, invoice.id, "100", payment_number="PAY-AGAIN"
    )
    _return(session, tenant, again[0].document_id, reason="AM04 insufficient funds")

    (finding,) = _findings(session, tenant)
    assert finding.causal_values["reason"] == "AM04 insufficient funds"


def test_the_fee_leaves_the_cash_account_the_payment_was_booked_on(session, business):
    from reality.services.finance.accounts import set_default_account

    tenant = business.tenant.id
    _fee_account(session, tenant)
    _, entry = _paid_invoice(session, business)
    booked = session.scalar(
        select(LedgerEntry.account_id).where(
            LedgerEntry.tenant_id == tenant,
            LedgerEntry.posting_group_id == entry.posting_group_id,
            LedgerEntry.account == "cash",
        )
    )
    second = create_account(
        session,
        tenant,
        code="1210",
        name="Second bank",
        role="cash",
        expected_revision=list_accounts(session, tenant)["revision"],
    )
    set_default_account(
        session,
        tenant,
        role="cash",
        account_id=second["id"],
        expected_revision=list_accounts(session, tenant)["revision"],
    )

    _, receipt = _return(
        session, tenant, entry.document_id, fee_amount="2.50", fee_bearer="company"
    )

    fee_cash = session.scalar(
        select(LedgerEntry.account_id).where(
            LedgerEntry.tenant_id == tenant,
            LedgerEntry.document_id == receipt["fee_document_id"],
            LedgerEntry.account == "cash",
        )
    )
    assert (fee_cash, fee_cash != second["id"]) == (booked, True)


@pytest.mark.parametrize("returned_on", ["", "02.10.2026", "2026-13-01"])
def test_a_return_date_that_is_no_date_is_refused_as_such(
    session, business, returned_on
):
    tenant = business.tenant.id
    _, entry = _paid_invoice(session, business)
    # Positive control: a calendar date is accepted.
    assert _preview(session, tenant, entry.document_id, returned_on="2026-10-02")

    with pytest.raises(core.InvalidOperation) as refused:
        _preview(session, tenant, entry.document_id, returned_on=returned_on)
    assert refused.value.code == "payment_return_date_invalid"


def test_each_return_names_its_own_reversal_and_fee_documents(session, business):
    """Spec 321 FR-002: the links are read from the records that hold them."""
    from reality.db.core import Document
    from reality.services.payment_returns import return_detail

    tenant = business.tenant.id
    _fee_account(session, tenant)
    _, first = _paid_invoice(session, business)
    _, second = _paid_invoice(session, business, "RE-318-B")

    _, one = _return(
        session, tenant, first.document_id, fee_amount="3.50", fee_bearer="customer"
    )
    _, two = _return(
        session,
        tenant,
        second.document_id,
        kind="chargeback",
        reference="dp_318",
        fee_amount="15",
        fee_bearer="company",
    )

    for receipt, entry, charged in ((one, first, True), (two, second, False)):
        session.expire_all()
        detail = return_detail(session, tenant, receipt["id"])
        assert detail == receipt
        reversal = record_by_id(session, LedgerReversal, detail["ledger_reversal_id"])
        assert reversal.original_posting_group_id == entry.posting_group_id
        fee = record_by_id(session, Document, detail["fee_document_id"])
        assert (fee.type, fee.source_record_id) == (
            "payment_return_fee",
            detail["source_record_id"],
        )
        if charged:
            charge = record_by_id(session, Document, detail["fee_charge_document_id"])
            assert (charge.type, charge.source_record_id) == (
                "payment_return_fee_charge",
                detail["source_record_id"],
            )
        else:
            assert detail["fee_charge_document_id"] is None
    assert one["ledger_reversal_id"] != two["ledger_reversal_id"]
    assert one["fee_document_id"] != two["fee_document_id"]


def test_a_return_without_a_fee_names_no_fee_documents(session, business):
    tenant = business.tenant.id
    _, entry = _paid_invoice(session, business)

    _, receipt = _return(session, tenant, entry.document_id)

    assert (receipt["fee_document_id"], receipt["fee_charge_document_id"]) == (
        None,
        None,
    )
    assert receipt["ledger_reversal_id"]


def test_the_migration_drops_the_links_only_when_they_can_be_read_back(
    postgres_database, monkeypatch
):
    """Spec 321 FR-003: 0110 checks every stored link, and its downgrade restores them."""
    from types import SimpleNamespace

    from alembic import command
    from alembic.config import Config
    from sqlalchemy import create_engine, inspect, text
    from sqlalchemy.orm import Session

    monkeypatch.setenv("REALITY_DATABASE_URL", postgres_database)
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", postgres_database)
    command.upgrade(config, "0109_stock_block_resolution")
    engine = create_engine(postgres_database)
    links = ("ledger_reversal_id", "fee_document_id", "fee_charge_document_id")

    def columns():
        return {c["name"] for c in inspect(engine).get_columns("payment_return")}

    try:
        with Session(engine) as session:
            tenant = core.create_tenant(session, "Migration 321")
            business = SimpleNamespace(
                tenant=tenant,
                customer=core.create_party(session, tenant.id, "Kunde", "customer"),
            )
            _fee_account(session, tenant.id)
            _, entry = _paid_invoice(session, business)
            _, receipt = _return(
                session,
                tenant.id,
                entry.document_id,
                fee_amount="3.50",
                fee_bearer="customer",
            )
            session.commit()
        stated = {key: receipt[key] for key in links}
        assert all(stated.values())

        def store(values):
            with engine.begin() as connection:
                connection.execute(
                    text(
                        "UPDATE payment_return SET ledger_reversal_id = :ledger_reversal_id, "
                        "fee_document_id = :fee_document_id, "
                        "fee_charge_document_id = :fee_charge_document_id WHERE id = :id"
                    ),
                    {**values, "id": receipt["id"]},
                )

        # A link that is not what the records say is refused, not dropped.
        store({**stated, "fee_document_id": stated["fee_charge_document_id"]})
        with pytest.raises(Exception, match="payment returns name links"):
            command.upgrade(config, "head")
        assert set(links) <= columns()

        store(stated)
        command.upgrade(config, "head")
        assert not set(links) & columns()

        command.downgrade(config, "0109_stock_block_resolution")
        with engine.connect() as connection:
            restored = connection.execute(
                text(
                    "SELECT ledger_reversal_id, fee_document_id, fee_charge_document_id "
                    "FROM payment_return WHERE id = :id"
                ),
                {"id": receipt["id"]},
            ).one()
        assert dict(zip(links, restored)) == stated
    finally:
        engine.dispose()
