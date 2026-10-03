"""Spec 336: marketplace and payment-provider payouts settle many orders at once."""

import json
from decimal import Decimal

import pytest
from sqlalchemy import func, select

from reality.db.core import Document, DocumentLine, LedgerEntry, PaymentReturn
from reality.services import core
from reality.services.exceptions import operational_exceptions
from reality.services.finance.accounts import (
    create_account,
    initialize_accounts,
    list_accounts,
    set_default_account,
)
from reality.services.payouts import payout_detail, payouts
from reality.tools.application import (
    approve_and_execute_proposal,
    create_change_proposal,
)

PAID_ON = "2026-09-30"


def _accounts(session, tenant):
    """The provider's cash account, beside the bank, and a fee expense default."""
    initialize_accounts(session, tenant)
    state = list_accounts(session, tenant)
    if "payment_fee_expense" not in state["defaults"]:
        fee = create_account(
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
            account_id=fee["id"],
            expected_revision=list_accounts(session, tenant)["revision"],
        )
    clearing = create_account(
        session,
        tenant,
        code=core.uid("1361")[:12],
        name="Amazon Payments",
        role="cash",
        expected_revision=list_accounts(session, tenant)["revision"],
    )
    return clearing["id"], list_accounts(session, tenant)["defaults"]["cash"]


def _invoiced_order(session, business, number, amount, customer=None, invoice=True):
    tenant = business.tenant.id
    customer = customer or business.customer
    order, (order_line,) = core.create_manual_document_with_lines(
        session,
        tenant,
        "sales_order",
        number,
        customer.id,
        [
            {
                "item_id": business.item.id,
                "quantity": "1",
                "unit_price": amount,
                "gross_amount": amount,
                "unit": "pcs",
                "source_line_id": "1",
            }
        ],
        amount,
        _commit=False,
    )
    if not invoice:
        return order, None
    document, (invoice_line,) = core.create_manual_document_with_lines(
        session,
        tenant,
        "sales_invoice",
        f"RE-{number}",
        customer.id,
        [
            {
                "item_id": business.item.id,
                "quantity": "1",
                "unit_price": amount,
                "gross_amount": amount,
                "unit": "pcs",
                "source_line_id": "1",
                "billed_document_line_id": order_line.id,
            }
        ],
        amount,
        document_date="2026-09-20",
        _commit=False,
    )
    core.post_sales_invoice(session, tenant, document.id, _commit=False)
    session.flush()
    return order, document


def _credit_note(session, business, invoice, amount):
    tenant = business.tenant.id
    (invoice_line,) = session.scalars(
        select(DocumentLine).where(
            DocumentLine.tenant_id == tenant,
            DocumentLine.document_id == invoice.id,
        )
    ).all()
    note, _ = core.create_manual_document_with_lines(
        session,
        tenant,
        "credit_note",
        f"GS-{invoice.number}",
        invoice.party_id,
        [
            {
                "item_id": business.item.id,
                "quantity": "1",
                "unit_price": amount,
                "gross_amount": amount,
                "unit": "pcs",
                "source_line_id": "1",
                "billed_document_line_id": invoice_line.id,
            }
        ],
        amount,
        document_date="2026-09-25",
        _commit=False,
    )
    core.post_sales_credit_note(session, tenant, note.id, _commit=False)
    session.flush()
    return note


def _line(line_id, kind, amount, order=None, **extra):
    references = (
        [{"type": "shop_order_number", "value": order}] if order is not None else []
    )
    return {
        "line_id": line_id,
        "kind": kind,
        "amount": amount,
        "references": extra.pop("references", references),
        **extra,
    }


def _statement(business, clearing, lines, amount, reference="PO-2026-09-30"):
    return {
        "provider_party_id": business.supplier.id,
        "payout_reference": reference,
        "paid_on": PAID_ON,
        "currency": "EUR",
        "amount": amount,
        "clearing_account_id": clearing,
        "lines": lines,
    }


def _settle(session, tenant, values):
    proposal = create_change_proposal(
        session, tenant, "finance.payout.settle", values, actor_type="human"
    )
    review = json.loads(proposal.output)["payout"]
    receipt = json.loads(
        approve_and_execute_proposal(session, tenant, proposal.id).output
    )
    return review, receipt


def _account_balance(session, tenant, account_id):
    total = Decimal(0)
    for entry in session.scalars(
        select(LedgerEntry).where(
            LedgerEntry.tenant_id == tenant, LedgerEntry.account_id == account_id
        )
    ):
        total += entry.amount if entry.debit_credit == "debit" else -entry.amount
    return total


def _refused(code, call):
    with pytest.raises((core.InvalidOperation, core.NotFound)) as refused:
        call()
    assert refused.value.code == code, refused.value.code
    return refused.value


def _unmatched(session, tenant):
    return {
        row.record_id: row
        for row in operational_exceptions(session, tenant)
        if row.class_id == "payout_line_unmatched"
    }


def test_a_payout_pays_each_order_and_books_its_fee_and_the_deposit(
    session, business
):
    tenant = business.tenant.id
    clearing, bank = _accounts(session, tenant)
    other = core.create_party(session, tenant, "Weber KG", "customer")
    _, first = _invoiced_order(session, business, "AMZ-1", "100")
    _, second = _invoiced_order(session, business, "AMZ-2", "50", customer=other)
    bank_before = _account_balance(session, tenant, bank)

    review, receipt = _settle(
        session,
        tenant,
        _statement(
            business,
            clearing,
            [
                _line("1", "charge", "100", "AMZ-1"),
                _line("2", "charge", "50", "AMZ-2"),
                _line("3", "fee", "7.50"),
            ],
            "142.50",
        ),
    )

    assert [line["outcome"] for line in review["lines"]] == [
        "allocate",
        "allocate",
        "expense",
    ]
    assert core.open_invoice_amount(session, tenant, first.id) == 0
    assert core.open_invoice_amount(session, tenant, second.id) == 0
    assert _account_balance(session, tenant, bank) - bank_before == Decimal("142.50")
    # What the provider kept is the fee; nothing else stays on its account.
    assert _account_balance(session, tenant, clearing) == 0
    assert core.account_balance(session, tenant, "payment_fee_expense") == Decimal(
        "7.50"
    )
    assert receipt["unmatched_line_ids"] == []
    assert {line["line_id"]: line["allocated_to"] for line in receipt["lines"]}[
        "1"
    ] == [first.id]
    assert payouts(session, tenant)[0]["unmatched_lines"] == 0
    # Positive control: nothing unmatched is reported.
    assert receipt["id"] not in _unmatched(session, tenant)


def test_a_refund_settles_the_credit_note_of_its_order(session, business):
    tenant = business.tenant.id
    clearing, _ = _accounts(session, tenant)
    _, invoice = _invoiced_order(session, business, "AMZ-10", "100")
    note = _credit_note(session, business, invoice, "20")

    review, _ = _settle(
        session,
        tenant,
        _statement(
            business,
            clearing,
            [_line("1", "charge", "100", "AMZ-10"), _line("2", "refund", "20", "AMZ-10")],
            "80",
        ),
    )

    refund = next(line for line in review["lines"] if line["kind"] == "refund")
    assert (refund["outcome"], refund["credit_note_id"]) == ("allocate", note.id)
    assert core.open_invoice_amount(session, tenant, note.id) == 0
    assert core.open_invoice_amount(session, tenant, invoice.id) == 0


def test_a_chargeback_returns_the_payment_held_on_the_provider_account(
    session, business
):
    tenant = business.tenant.id
    clearing, _ = _accounts(session, tenant)
    _, paid = _invoiced_order(session, business, "AMZ-20", "100")
    _, later = _invoiced_order(session, business, "AMZ-21", "150")
    _, same = _invoiced_order(session, business, "AMZ-22", "60")
    _settle(
        session,
        tenant,
        _statement(business, clearing, [_line("1", "charge", "100", "AMZ-20")], "100"),
    )
    assert core.open_invoice_amount(session, tenant, paid.id) == 0

    review, _ = _settle(
        session,
        tenant,
        _statement(
            business,
            clearing,
            [
                _line("1", "charge", "150", "AMZ-21"),
                _line("2", "charge", "60", "AMZ-22"),
                _line("3", "chargeback", "100", "AMZ-20", reason="Item not received"),
                # A chargeback of a charge in this very statement.
                _line("4", "chargeback", "60", "AMZ-22"),
            ],
            "50",
            reference="PO-2026-10-01",
        ),
    )

    assert {line["line_id"]: line["outcome"] for line in review["lines"]} == {
        "1": "allocate",
        "2": "allocate",
        "3": "return",
        "4": "return",
    }
    assert core.open_invoice_amount(session, tenant, paid.id) == 100
    assert core.open_invoice_amount(session, tenant, same.id) == 60
    assert core.open_invoice_amount(session, tenant, later.id) == 0
    returns = session.scalars(
        select(PaymentReturn).where(PaymentReturn.tenant_id == tenant)
    ).all()
    assert {row.kind for row in returns} == {"chargeback"}
    assert "Item not received" in {row.reason for row in returns}
    assert _account_balance(session, tenant, clearing) == 0


def test_a_statement_that_does_not_add_up_is_refused(session, business):
    tenant = business.tenant.id
    clearing, _ = _accounts(session, tenant)
    _invoiced_order(session, business, "AMZ-30", "100")

    refused = _refused(
        "payout_total_mismatch",
        lambda: _settle(
            session,
            tenant,
            _statement(
                business,
                clearing,
                [_line("1", "charge", "100", "AMZ-30"), _line("2", "fee", "3")],
                "98",
            ),
        ),
    )
    assert refused.values == {"stated": "98", "lines": "97"}
    # Positive control: the statement that adds up is accepted.
    _settle(
        session,
        tenant,
        _statement(
            business,
            clearing,
            [_line("1", "charge", "100", "AMZ-30"), _line("2", "fee", "3")],
            "97",
        ),
    )


def test_an_unmatched_line_waits_and_settling_again_books_only_it(
    session, business
):
    tenant = business.tenant.id
    clearing, _ = _accounts(session, tenant)
    _, held = _invoiced_order(session, business, "AMZ-40", "100")
    values = _statement(
        business,
        clearing,
        [_line("1", "charge", "100", "AMZ-40"), _line("2", "charge", "35", "AMZ-41")],
        "135",
    )

    review, receipt = _settle(session, tenant, values)

    assert {line["line_id"]: line["outcome"] for line in review["lines"]} == {
        "1": "allocate",
        "2": "unmatched",
    }
    assert receipt["unmatched_line_ids"] == ["2"]
    finding = _unmatched(session, tenant)[receipt["id"]]
    assert finding.causal_values["unmatched_lines"] == 1
    assert finding.causal_values["unmatched_amount"] == 35
    # The 35 the provider paid for an order Reality does not hold stay on its account.
    assert _account_balance(session, tenant, clearing) == Decimal("-35")

    _, missing = _invoiced_order(session, business, "AMZ-41", "35")
    review, receipt = _settle(session, tenant, values)

    assert {line["line_id"]: line["outcome"] for line in review["lines"]} == {
        "1": "booked",
        "2": "allocate",
    }
    assert receipt["unmatched_line_ids"] == []
    assert core.open_invoice_amount(session, tenant, missing.id) == 0
    assert core.open_invoice_amount(session, tenant, held.id) == 0
    assert receipt["id"] not in _unmatched(session, tenant)
    assert _account_balance(session, tenant, clearing) == 0
    # The deposit and the first line were booked once.
    assert (
        session.scalar(
            select(func.count())
            .select_from(Document)
            .where(Document.tenant_id == tenant, Document.type == "payout")
        )
        == 1
    )
    assert (
        session.scalar(
            select(func.count())
            .select_from(Document)
            .where(Document.tenant_id == tenant, Document.type == "customer_payment")
        )
        == 2
    )


def test_a_changed_statement_is_refused_and_a_replay_books_nothing(
    session, business
):
    tenant = business.tenant.id
    clearing, _ = _accounts(session, tenant)
    _invoiced_order(session, business, "AMZ-50", "100")
    values = _statement(
        business, clearing, [_line("1", "charge", "100", "AMZ-50")], "100"
    )
    _settle(session, tenant, values)

    _, receipt = _settle(session, tenant, values)
    assert (
        session.scalar(
            select(func.count())
            .select_from(Document)
            .where(Document.tenant_id == tenant, Document.type == "customer_payment")
        )
        == 1
    )
    assert receipt["unmatched_line_ids"] == []
    _refused(
        "payout_statement_changed",
        lambda: _settle(
            session,
            tenant,
            _statement(
                business,
                clearing,
                [_line("1", "charge", "90", "AMZ-50")],
                "90",
            ),
        ),
    )


def test_the_provider_account_is_a_cash_account_apart_from_the_bank(
    session, business
):
    tenant = business.tenant.id
    clearing, bank = _accounts(session, tenant)
    _invoiced_order(session, business, "AMZ-60", "100")
    lines = [_line("1", "charge", "100", "AMZ-60")]
    _refused(
        "payout_clearing_is_bank",
        lambda: _settle(session, tenant, _statement(business, bank, lines, "100")),
    )
    fees = list_accounts(session, tenant)["defaults"]["payment_fee_expense"]
    _refused(
        "payout_clearing_account_invalid",
        lambda: _settle(session, tenant, _statement(business, fees, lines, "100")),
    )
    # Positive control: the provider's own cash account is accepted.
    _settle(session, tenant, _statement(business, clearing, lines, "100"))


def test_a_charge_for_an_order_not_invoiced_yet_is_recorded_for_its_customer(
    session, business
):
    tenant = business.tenant.id
    clearing, _ = _accounts(session, tenant)
    _invoiced_order(session, business, "AMZ-70", "80", invoice=False)

    review, receipt = _settle(
        session,
        tenant,
        _statement(business, clearing, [_line("1", "charge", "80", "AMZ-70")], "80"),
    )

    (line,) = review["lines"]
    assert line["outcome"] == "record"
    assert "order AMZ-70 is not invoiced yet" in line["reasons"]
    (booked,) = receipt["lines"]
    assert booked["state"] == "booked"
    assert booked["document_type"] == "customer_payment"
    assert booked["allocated_to"] == []
    payment = core._tenant_record(session, Document, tenant, booked["document_id"])
    assert payment.party_id == business.customer.id


def test_another_company_sees_no_payout_and_resolves_nothing(session, business):
    tenant = business.tenant.id
    clearing, _ = _accounts(session, tenant)
    _invoiced_order(session, business, "AMZ-80", "100")
    _, receipt = _settle(
        session,
        tenant,
        _statement(business, clearing, [_line("1", "charge", "100", "AMZ-80")], "100"),
    )
    other = core.create_tenant(session, "Other GmbH")

    with pytest.raises(core.NotFound):
        payout_detail(session, other.id, receipt["id"])
    assert payouts(session, other.id) == []
    assert not [
        row
        for row in operational_exceptions(session, other.id)
        if row.class_id == "payout_line_unmatched"
    ]
