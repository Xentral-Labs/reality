"""Spec 297: returned direct debits, chargebacks and payment fees."""

import json
from datetime import date
from decimal import Decimal

import pytest
from conftest import record_by_id
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from reality.db.core import BusinessEvent, LedgerReversal, PaymentReturn, SourceRecord
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
        "ledger_reversal_id": None,
        "source_record_id": core.create_master_source_record(
            session, tenant, "payment_return", "manual", core.uid("t005"), {}
        ).id,
        **columns,
    }
    return PaymentReturn(**values)


def _reversal(session, business, payment_entry):
    return core.reverse_ledger_posting_group(
        session, business.tenant.id, payment_entry.posting_group_id, reason="T005"
    ).reversal_id


def _insert(session, record):
    with session.begin_nested():
        session.add(record)
        session.flush()


def test_a_return_names_its_kind_and_who_bears_the_fee(session, business):
    _, entry = _paid_invoice(session, business)
    reversal = _reversal(session, business, entry)
    # Positive control: a well-formed return is accepted.
    _insert(
        session,
        _row(session, business, entry.document_id, ledger_reversal_id=reversal),
    )

    _, other = _paid_invoice(session, business, "RE-297-B")
    other_reversal = _reversal(session, business, other)
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
                _row(
                    session,
                    business,
                    other.document_id,
                    ledger_reversal_id=other_reversal,
                    **columns,
                ),
            )


def test_a_payment_is_returned_once(session, business):
    _, entry = _paid_invoice(session, business)
    reversal = _reversal(session, business, entry)
    _insert(
        session, _row(session, business, entry.document_id, ledger_reversal_id=reversal)
    )

    with pytest.raises(IntegrityError, match="uq_payment_return_payment"):
        _insert(
            session,
            _row(session, business, entry.document_id, ledger_reversal_id=reversal),
        )


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
    reversal = record_by_id(session, LedgerReversal, row.ledger_reversal_id)
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
