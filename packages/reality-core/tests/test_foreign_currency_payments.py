"""Spec 309 FR-001/FR-002: a USD supplier invoice posted at its rate and paid in EUR."""

import json
from decimal import Decimal

import pytest
from intake_review_support import reviewed_record_free_supplier_invoice
from sqlalchemy import select

from reality.db.core import LedgerEntry
from reality.services import core
from reality.services.delivery_actions import prepare_delivery_action
from reality.tools.application import approve_and_execute_proposal


def _refused(code, call):
    with pytest.raises((core.InvalidOperation, core.NotFound)) as refused:
        call()
    assert refused.value.code == code, refused.value.code


def _exchange_account(session, tenant):
    account = reviewed_create_account(
        session,
        tenant,
        code="7100",
        name="Kursdifferenzen",
        role="exchange_difference",
    )
    reviewed_set_default_account(
        session, tenant, role="exchange_difference", account_id=account["id"]
    )


def _invoice(
    session, business, number="USD-INV-1", gross="1000", rate="0.92", currency="USD"
):
    receipt = reviewed_record_free_supplier_invoice(
        session,
        business.tenant.id,
        supplier_id=business.supplier.id,
        number=number,
        currency=currency,
        gross_amount=gross,
        lines=[
            {
                "item_id": business.item.id,
                "quantity": "100",
                "unit_price": str(Decimal(gross) / 100),
                "gross_amount": gross,
            }
        ],
        **({"exchange_rate": rate} if rate is not None else {}),
    )
    return next(row["id"] for row in receipt["records"] if row["family"] == "document")


def _entries(session, tenant, document_id):
    return {
        (entry.account, entry.debit_credit): entry
        for entry in session.scalars(
            select(LedgerEntry).where(
                LedgerEntry.tenant_id == tenant, LedgerEntry.document_id == document_id
            )
        )
    }


def _pay(session, business, invoice, amount, paid, number):
    return core.post_supplier_payment(
        session,
        business.tenant.id,
        invoice,
        amount,
        payment_number=number,
        paid_amount=paid,
    )


def _company_open(session, tenant, invoice):
    """What is left of the invoice's company-currency value."""
    control = _entries(session, tenant, invoice)[("accounts_payable", "credit")]
    settled = Decimal(0)
    for row in core.active_settlement_allocations(
        session, tenant, entry_ids={control.id}
    ):
        payment = session.scalar(
            select(LedgerEntry).where(
                LedgerEntry.tenant_id == tenant,
                LedgerEntry.id == row.payment_ledger_entry_id,
            )
        )
        settled += payment.company_amount
    return control.company_amount - settled


def test_an_invoice_is_posted_at_its_stated_rate(session, business):
    tenant = business.tenant.id

    invoice = _invoice(session, business)

    entries = _entries(session, tenant, invoice)
    payable = entries[("accounts_payable", "credit")]
    assert (payable.amount, payable.currency) == (Decimal(1000), "USD")
    assert (payable.company_amount, payable.exchange_rate) == (
        Decimal("920.00"),
        Decimal("0.92"),
    )
    assert entries[("inventory", "debit")].company_amount == Decimal("920.00")


def test_an_invoice_in_another_currency_needs_its_rate(session, business):
    _refused("exchange_rate_required", lambda: _invoice(session, business, rate=None))
    _refused(
        "exchange_rate_invalid",
        lambda: _invoice(session, business, number="X", rate="-1"),
    )
    _refused(
        "exchange_rate_not_applicable",
        lambda: _invoice(session, business, number="EUR-1", currency="EUR"),
    )
    # Positive control: in the company currency no rate is needed.
    _invoice(session, business, number="EUR-2", currency="EUR", rate=None)


def test_a_payment_at_a_better_rate_realises_a_gain(session, business):
    tenant = business.tenant.id
    _exchange_account(session, tenant)
    invoice = _invoice(session, business)

    entries = _pay(session, business, invoice, "1000", "912.40", "PAY-1")

    by_account = {entry.account: entry for entry in entries}
    assert (
        by_account["accounts_payable"].amount,
        by_account["accounts_payable"].company_amount,
    ) == (
        Decimal(1000),
        Decimal("920.00"),
    )
    assert by_account["cash"].company_amount == Decimal("912.40")
    gain = by_account["exchange_difference"]
    assert (gain.debit_credit, gain.amount, gain.company_amount) == (
        "credit",
        Decimal(0),
        Decimal("7.60"),
    )
    assert core.open_invoice_amount(session, tenant, invoice) == 0
    assert _company_open(session, tenant, invoice) == 0


def test_a_payment_at_a_worse_rate_realises_a_loss(session, business):
    tenant = business.tenant.id
    _exchange_account(session, tenant)
    invoice = _invoice(session, business)

    entries = _pay(session, business, invoice, "1000", "931.00", "PAY-2")

    loss = next(entry for entry in entries if entry.account == "exchange_difference")
    assert (loss.debit_credit, loss.company_amount) == ("debit", Decimal("11.00"))


def test_two_partial_payments_leave_nothing_in_either_currency(session, business):
    tenant = business.tenant.id
    _exchange_account(session, tenant)
    invoice = _invoice(session, business, gross="1000", rate="0.91234")

    first = _pay(session, business, invoice, "333.33", "310.00", "PAY-3A")
    second = _pay(session, business, invoice, "666.67", "600.00", "PAY-3B")

    first_payable = next(e for e in first if e.account == "accounts_payable")
    # 333.33 × 0.91234 = 304.11; the last payment takes the rest of 912.34.
    assert first_payable.company_amount == Decimal("304.11")
    second_payable = next(e for e in second if e.account == "accounts_payable")
    assert second_payable.company_amount == Decimal("608.23")
    assert core.open_invoice_amount(session, tenant, invoice) == 0
    assert _company_open(session, tenant, invoice) == 0
    differences = {
        e.debit_credit: e.company_amount
        for e in [*first, *second]
        if e.account == "exchange_difference"
    }
    assert differences == {"debit": Decimal("5.89"), "credit": Decimal("8.23")}


def test_a_foreign_payment_states_what_was_paid(session, business):
    tenant = business.tenant.id
    _exchange_account(session, tenant)
    invoice = _invoice(session, business)
    euro = _invoice(session, business, number="EUR-3", currency="EUR", rate=None)

    _refused(
        "paid_amount_invalid", lambda: _pay(session, business, invoice, "10", "0", "P2")
    )
    _refused(
        "paid_amount_invalid",
        lambda: _pay(session, business, invoice, "10", "9.123", "P3"),
    )
    _refused(
        "paid_amount_not_applicable",
        lambda: _pay(session, business, euro, "10", "10", "P4"),
    )
    _refused(
        "payment_exceeds_open_invoice",
        lambda: _pay(session, business, invoice, "1000.01", "920", "P5"),
    )
    # Positive control: a stated payment of the EUR invoice in EUR passes.
    _pay(session, business, euro, "10", None, "P6")


def test_an_unconverted_invoice_cannot_be_paid_across_currencies(session, business):
    tenant = business.tenant.id
    document = core.create_document(
        session,
        tenant,
        "supplier_invoice",
        "OLD-USD",
        business.supplier.id,
        "50",
        currency="USD",
    )
    # A foreign posting from before spec 309 carries no company amount.
    core.post_ledger(
        session,
        tenant,
        document.id,
        business.supplier.id,
        [("inventory", "debit", "50"), ("accounts_payable", "credit", "50")],
        currency="USD",
    )

    _refused(
        "invoice_not_converted",
        lambda: _pay(session, business, document.id, "50", "46", "P7"),
    )


def test_a_reviewed_payment_shows_the_difference_and_turns_stale(session, business):
    tenant = business.tenant.id
    _exchange_account(session, tenant)
    invoice = _invoice(session, business)
    arguments = {"invoice_id": invoice, "amount": "400", "paid_amount": "372.00"}

    proposal = prepare_delivery_action(
        session, tenant, "supplier_payment_post", arguments, request_id="fx-1"
    )
    review = json.loads(proposal.input)["_delivery_review"]
    exchange = review["state"]["exchange"]
    assert (
        Decimal(exchange["invoice_value"]),
        Decimal(exchange["payment_rate"]),
        exchange["kind"],
        Decimal(exchange["difference"]),
    ) == (Decimal(368), Decimal("0.93"), "loss", Decimal(4))
    # Another payment changes what is open: the review is stale.
    _pay(session, business, invoice, "100", "92.00", "PAY-4")
    with pytest.raises(core.InvalidOperation):
        approve_and_execute_proposal(
            session, tenant, proposal.id, review_token=review["token"], confirmed=True
        )
    session.rollback()
    fresh = prepare_delivery_action(
        session, tenant, "supplier_payment_post", arguments, request_id="fx-2"
    )
    executed = approve_and_execute_proposal(
        session,
        tenant,
        fresh.id,
        review_token=json.loads(fresh.input)["_delivery_review"]["token"],
        confirmed=True,
    )
    assert executed.status == "executed"
    from reality.services.delivery_actions import delivery_proposal_detail

    assert (
        delivery_proposal_detail(session, tenant, fresh.id)["verification"]
        == "verified"
    )


def test_reversing_a_payment_takes_its_difference_back(session, business):
    tenant = business.tenant.id
    _exchange_account(session, tenant)
    invoice = _invoice(session, business)
    entries = _pay(session, business, invoice, "1000", "912.40", "PAY-5")

    core.reverse_ledger_posting_group(
        session, tenant, entries[0].posting_group_id, reason="Wrong bank line"
    )

    gains = [
        (entry.debit_credit, entry.company_amount)
        for entry in session.scalars(
            select(LedgerEntry).where(LedgerEntry.tenant_id == tenant)
        )
        if entry.account == "exchange_difference"
    ]
    assert sorted(gains) == [("credit", Decimal("7.60")), ("debit", Decimal("7.60"))]
    assert core.open_invoice_amount(session, tenant, invoice) == Decimal(1000)


def test_a_payment_in_the_invoice_currency_realises_nothing(session, business):
    """Paid from an account in the invoice currency: valued at the invoice rate."""
    tenant = business.tenant.id
    invoice = _invoice(session, business)

    entries = _pay(session, business, invoice, "250", None, "PAY-6")

    assert sorted((e.account, e.company_amount) for e in entries) == [
        ("accounts_payable", Decimal("230.00")),
        ("cash", Decimal("230.00")),
    ]
    assert core.open_invoice_amount(session, tenant, invoice) == Decimal(750)


def test_a_reduction_then_the_last_payment_close_both_currencies(session, business):
    """A reduction of a converted invoice is valued at its rate; the payment of the
    rest takes what is left of the invoice's value."""
    from reality.services.finance.accounts import list_accounts
    from reality.services.finance.settlement import adjustment_context
    from reality.tools.application import create_change_proposal

    tenant = business.tenant.id
    _exchange_account(session, tenant)
    if "supplier_reduction" not in list_accounts(session, tenant)["defaults"]:
        account = reviewed_create_account(
            session, tenant, code="red", name="Reductions", role="supplier_reduction"
        )
        reviewed_set_default_account(
            session, tenant, role="supplier_reduction", account_id=account["id"]
        )
    invoice = _invoice(session, business)
    _pay(session, business, invoice, "333.33", "305.00", "PAY-7A")
    proposal = create_change_proposal(
        session,
        tenant,
        "finance.adjustment.accept",
        {
            "invoice_id": invoice,
            "amount": "20",
            "expected_revision": adjustment_context(session, tenant, invoice)[
                "revision"
            ],
            "reason_category": "early_payment_discount",
            "reason": "Agreed discount",
            "agreement": "Terms grant USD 20",
        },
        actor_type="human",
    )
    receipt = json.loads(
        approve_and_execute_proposal(
            session, tenant, proposal.id, confirmed=True
        ).output
    )
    reduction = session.scalars(
        select(LedgerEntry).where(
            LedgerEntry.tenant_id == tenant,
            LedgerEntry.posting_group_id == receipt["posting_group_id"],
        )
    ).all()
    assert {entry.company_amount for entry in reduction} == {Decimal("18.40")}

    last = _pay(session, business, invoice, "646.67", "590.00", "PAY-7B")

    payable = next(e for e in last if e.account == "accounts_payable")
    # 920.00 − 306.66 (333.33 at 0.92) − 18.40 = 594.94.
    assert payable.company_amount == Decimal("594.94")
    assert core.open_invoice_amount(session, tenant, invoice) == 0


def test_a_review_needs_an_exchange_difference_account(session, business):
    tenant = business.tenant.id
    invoice = _invoice(session, business)

    _refused(
        "finance_account_default_missing",
        lambda: prepare_delivery_action(
            session,
            tenant,
            "supplier_payment_post",
            {"invoice_id": invoice, "amount": "100", "paid_amount": "90.00"},
            request_id="fx-no-account",
        ),
    )
    # Positive control: a payment that realises nothing needs no such account.
    prepare_delivery_action(
        session,
        tenant,
        "supplier_payment_post",
        {"invoice_id": invoice, "amount": "100", "paid_amount": "92.00"},
        request_id="fx-no-difference",
    )


def test_a_part_without_a_company_value_is_refused(session, business):
    invoice = _invoice(session, business, rate="0.4")
    _refused(
        "exchange_value_too_small",
        lambda: _pay(session, business, invoice, "0.01", None, "PAY-8"),
    )
    _refused(
        "exchange_rate_invalid",
        lambda: _invoice(session, business, number="BIG", rate="1e12"),
    )


def test_a_company_that_posted_only_in_usd_may_state_usd(session, business):
    from reality.services.finance.company_currency import set_company_currency

    tenant = business.tenant.id
    document = core.create_document(
        session,
        tenant,
        "supplier_invoice",
        "OLD-USD-2",
        business.supplier.id,
        "50",
        currency="USD",
    )
    (entry, _) = core.post_ledger(
        session,
        tenant,
        document.id,
        business.supplier.id,
        [("inventory", "debit", "50"), ("accounts_payable", "credit", "50")],
        currency="USD",
    )

    set_company_currency(session, tenant, "USD")

    session.refresh(entry)
    assert (entry.company_amount, entry.exchange_rate) == (Decimal(50), Decimal(1))
    _refused(
        "company_currency_has_postings",
        lambda: set_company_currency(session, tenant, "EUR"),
    )


from intake_review_support import reviewed_create_account, reviewed_set_default_account
