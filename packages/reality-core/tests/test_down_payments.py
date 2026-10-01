"""Down-payment invoices for an order (spec 299 FR-002).

A down-payment invoice is for its order, is a receivable against received down
payments, bills no quantity, and paid it counts towards prepayment readiness.
"""

import json
from decimal import Decimal

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from reality.db.core import Document, DocumentLine, DownPaymentOffset
from reality.domain.finance import ACCOUNT_ROLES
from reality.services import core
from reality.services.delivery_actions import prepare_delivery_action
from reality.services.finance.accounts import initialize_accounts, list_accounts
from reality.services.fulfillment_readiness import fulfillment_readiness
from reality.tools.application import approve_and_execute_proposal


def _order(session, business, number="SO-299", total="1000.00", prepay=False):
    tenant = business.tenant.id
    if prepay and not session.scalar(
        select(core.PaymentTerm).where(
            core.PaymentTerm.tenant_id == tenant, core.PaymentTerm.code == "PREPAY"
        )
    ):
        core.create_payment_term(
            session, tenant, "PREPAY", "Prepayment", 0, requires_prepayment=True
        )
    _, order, lines, commitments = core.create_manual_order(
        session,
        tenant,
        "sales",
        number,
        business.company.id,
        business.customer.id,
        business.location.id,
        [
            {
                "item_id": business.item.id,
                "quantity": "10",
                "unit_price": str(Decimal(total) / 10),
                "gross_amount": total,
            }
        ],
        total,
        **({"payment_term_code": "PREPAY"} if prepay else {}),
    )
    return order, lines[0], commitments[0]


def _reviewed(session, business, tool, arguments, request_id):
    proposal = prepare_delivery_action(
        session, business.tenant.id, tool, arguments, request_id=request_id
    )
    token = json.loads(proposal.input)["_delivery_review"]["token"]
    executed = approve_and_execute_proposal(
        session, business.tenant.id, proposal.id, review_token=token, confirmed=True
    )
    assert executed.status == "executed"
    return json.loads(proposal.input)["_delivery_review"], json.loads(executed.output)


def _down_payment(session, business, order, amount="300.00", number="AR-299-1"):
    return _reviewed(
        session,
        business,
        "down_payment_invoice_record",
        {
            "order_id": order.id,
            "number": number,
            "gross_amount": amount,
            "effective_at": "2026-09-20T10:00:00Z",
        },
        f"dp-{number}",
    )


# --- T004: schema and role ------------------------------------------------------------


def test_the_down_payment_role_exists_and_gets_a_default(session, business):
    assert "customer_down_payments" in ACCOUNT_ROLES
    initialize_accounts(session, business.tenant.id)

    assert (
        "customer_down_payments"
        in list_accounts(session, business.tenant.id)["defaults"]
    )


def test_an_offset_must_state_a_positive_amount(session, business):
    tenant = business.tenant.id
    order, _, _ = _order(session, business)
    source = core.create_master_source_record(
        session, tenant, "down_payment_offset", "manual", core.uid("t004"), {}
    )

    def insert(amount):
        with session.begin_nested():
            session.add(
                DownPaymentOffset(
                    id=core.uid("dpo"),
                    tenant_id=tenant,
                    final_invoice_document_id=order.id,
                    down_payment_document_id=order.id,
                    amount=Decimal(amount),
                    source_record_id=source.id,
                )
            )
            session.flush()

    # Positive control: a positive amount is accepted.
    insert("1")
    with pytest.raises(IntegrityError, match="ck_down_payment_offset_amount"):
        insert("0")


def test_a_document_names_only_an_order_of_its_own_company(session, business):
    tenant = business.tenant.id
    other = core.create_tenant(session, "Other GmbH")
    order, _, _ = _order(session, business)
    document = core.create_document(
        session, tenant, "proforma_invoice", "PF-T004", business.customer.id, "10"
    )
    # Positive control: its own company's order is accepted.
    document.order_document_id = order.id
    session.flush()

    stranger = core.create_party(session, other.id, "Fremd GmbH", "customer")
    foreign = core.create_document(
        session, other.id, "proforma_invoice", "PF-T004-X", stranger.id, "10"
    )
    with (
        pytest.raises(IntegrityError, match="fk_document_order_document"),
        session.begin_nested(),
    ):
        foreign.order_document_id = order.id
        session.flush()


# --- T006: the down-payment invoice -------------------------------------------------


def test_a_down_payment_invoice_is_a_receivable_for_its_order(session, business):
    tenant = business.tenant.id
    initialize_accounts(session, tenant)
    order, line, _ = _order(session, business)

    review, receipt = _down_payment(session, business, order)

    assert review["state"]["order_number"] == "SO-299"
    document = session.get(Document, (tenant, receipt["document_id"]))
    assert (document.type, document.order_document_id) == (
        "down_payment_invoice",
        order.id,
    )
    assert core.open_invoice_amount(session, tenant, document.id) == Decimal("300.00")
    assert core.account_balance(session, tenant, "customer_down_payments") == Decimal(
        "-300.00"
    )
    # It bills no quantity of the order.
    assert core._order_line_billing(session, tenant, line.id)["invoiced"] == 0


def test_a_paid_down_payment_counts_towards_prepayment(session, business):
    tenant = business.tenant.id
    initialize_accounts(session, tenant)
    order, _, commitment = _order(session, business, prepay=True)
    # Positive control: without a down-payment invoice the basis is missing.
    assert (
        "prepayment_invoice_missing"
        in fulfillment_readiness(session, tenant, commitment.id).blocker_codes
    )

    _, receipt = _down_payment(session, business, order)
    core.post_customer_payment(
        session, tenant, receipt["document_id"], "300.00", payment_number="PAY-DP-1"
    )

    readiness = fulfillment_readiness(session, tenant, commitment.id)
    assert "prepayment_invoice_missing" not in readiness.blocker_codes
    assert (readiness.received_amount, readiness.remaining_amount) == (
        Decimal("300.00"),
        Decimal("700.0000"),
    )
    assert "prepayment_required" in readiness.blocker_codes


def test_a_reversed_down_payment_no_longer_counts(session, business):
    from reality.db.core import LedgerEntry

    tenant = business.tenant.id
    initialize_accounts(session, tenant)
    order, _, commitment = _order(session, business, prepay=True)
    _, receipt = _down_payment(session, business, order)
    payment = core.post_customer_payment(
        session, tenant, receipt["document_id"], "300.00", payment_number="PAY-DP-R"
    )
    assert fulfillment_readiness(session, tenant, commitment.id).received_amount == 300

    core.reverse_ledger_posting_group(
        session, tenant, payment[0].posting_group_id, reason="Bounced"
    )
    group = session.scalar(
        select(LedgerEntry.posting_group_id).where(
            LedgerEntry.tenant_id == tenant,
            LedgerEntry.document_id == receipt["document_id"],
        )
    )
    core.reverse_ledger_posting_group(session, tenant, group, reason="Cancelled")

    assert fulfillment_readiness(session, tenant, commitment.id).received_amount == 0


@pytest.mark.parametrize(
    ("change", "code"),
    [
        ({"gross_amount": "0"}, "down_payment_amount_invalid"),
        ({"gross_amount": "-5"}, "down_payment_amount_invalid"),
        ({"number": "  "}, "down_payment_number_missing"),
        ({"order_id": "purchase"}, "down_payment_order_required"),
        ({"currency": "USD"}, "down_payment_currency_mismatch"),
    ],
)
def test_a_down_payment_invoice_states_a_sales_order_and_an_amount(
    session, business, change, code
):
    initialize_accounts(session, business.tenant.id)
    order, _, _ = _order(session, business)
    arguments = {
        "order_id": order.id,
        "number": "AR-BAD",
        "gross_amount": "300.00",
        "effective_at": "2026-09-20T10:00:00Z",
        **change,
    }
    if arguments["order_id"] == "purchase":
        _, purchase, _, _ = core.create_manual_order(
            session,
            business.tenant.id,
            "purchase",
            "PO-299",
            business.company.id,
            business.supplier.id,
            business.location.id,
            [
                {
                    "item_id": business.item.id,
                    "quantity": "1",
                    "unit_price": "10",
                    "gross_amount": "10",
                }
            ],
            "10",
        )
        arguments["order_id"] = purchase.id

    with pytest.raises(core.InvalidOperation) as refused:
        prepare_delivery_action(
            session,
            business.tenant.id,
            "down_payment_invoice_record",
            arguments,
            request_id="dp-bad",
        )
    assert refused.value.code == code


def test_the_migration_upgrades_downgrades_and_keeps_recorded_down_payments(
    postgres_database, monkeypatch
):
    from alembic import command
    from alembic.config import Config
    from sqlalchemy import create_engine, inspect, text
    from sqlalchemy.orm import Session

    monkeypatch.setenv("REALITY_DATABASE_URL", postgres_database)
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", postgres_database)
    command.upgrade(config, "head")
    engine = create_engine(postgres_database)

    def schema():
        inspector = inspect(engine)
        return (
            "down_payment_offset" in inspector.get_table_names(),
            "order_document_id"
            in {column["name"] for column in inspector.get_columns("document")},
        )

    try:
        assert schema() == (True, True)
        # Positive control: with nothing recorded the downgrade removes the schema.
        command.downgrade(config, "0104_line_price_optional")
        assert schema() == (False, False)
        command.upgrade(config, "head")

        with Session(engine) as session:
            tenant = core.create_tenant(session, "Migration down payment")
            party = core.create_party(session, tenant.id, "Customer", "customer")
            core.create_document(
                session, tenant.id, "down_payment_invoice", "AR-M", party.id, "10"
            )
            session.commit()
            tenant_id = tenant.id
        with pytest.raises(RuntimeError, match="down-payment or pro-forma invoices"):
            command.downgrade(config, "0104_line_price_optional")
        assert schema() == (True, True)

        with engine.begin() as connection:
            connection.execute(
                text("DELETE FROM document WHERE type = 'down_payment_invoice'")
            )
        with Session(engine) as session:
            initialize_accounts(session, tenant_id)
        with pytest.raises(RuntimeError, match="received down-payment accounts"):
            command.downgrade(config, "0104_line_price_optional")
    finally:
        engine.dispose()


# --- T008: the final invoice offsets what was paid --------------------------------------


def _paid_down_payment(session, business, order, amount="300.00", number="AR-299-1"):
    _, receipt = _down_payment(session, business, order, amount, number)
    core.post_customer_payment(
        session,
        business.tenant.id,
        receipt["document_id"],
        amount,
        payment_number=f"PAY-{number}",
    )
    return receipt["document_id"]


def _final(line, quantity="10", amount="1000.00", number="RE-299", offsets=None):
    return {
        "order_line_id": line.id,
        "quantity": quantity,
        "gross_amount": amount,
        "number": number,
        "effective_at": "2026-09-25T10:00:00Z",
        **({"down_payment_offsets": offsets} if offsets is not None else {}),
    }


def _invoice_document(receipt):
    return next(r["id"] for r in receipt["records"] if r["family"] == "document")


def test_the_final_invoice_offers_the_paid_down_payment(session, business):
    initialize_accounts(session, business.tenant.id)
    order, line, _ = _order(session, business)
    down_payment = _paid_down_payment(session, business, order)

    review = prepare_delivery_action(
        session,
        business.tenant.id,
        "sales_invoice_record",
        _final(line),
        request_id="o",
    )
    offers = json.loads(review.input)["_delivery_review"]["state"][
        "down_payment_offers"
    ]

    assert offers == [
        {
            "document_id": down_payment,
            "number": "AR-299-1",
            "currency": "EUR",
            "gross": "300.0000",
            "paid": "300.0000",
            "offset": "0.0000",
            "offsettable": "300.0000",
        }
    ]


def test_an_order_without_down_payments_reviews_its_invoice_as_before(
    session, business
):
    initialize_accounts(session, business.tenant.id)
    _, line, _ = _order(session, business)

    review, receipt = _reviewed(
        session, business, "sales_invoice_record", _final(line), "plain"
    )

    # Control: no offers, no offsets, the invoice is open for its whole amount.
    assert "down_payment_offers" not in review["state"]
    assert "down_payment_offsets" not in review["state"]["creation"]
    assert core.open_invoice_amount(
        session, business.tenant.id, _invoice_document(receipt)
    ) == Decimal("1000.00")


def test_a_stated_offset_is_posted_and_recorded(session, business):
    tenant = business.tenant.id
    initialize_accounts(session, tenant)
    order, line, _ = _order(session, business)
    down_payment = _paid_down_payment(session, business, order)

    review, receipt = _reviewed(
        session,
        business,
        "sales_invoice_record",
        _final(
            line,
            offsets=[{"down_payment_document_id": down_payment, "amount": "300.00"}],
        ),
        "final",
    )

    invoice = _invoice_document(receipt)
    assert review["state"]["open_after_offsets"] == "700.00"
    assert core.open_invoice_amount(session, tenant, invoice) == Decimal("700.00")
    assert core.account_balance(session, tenant, "customer_down_payments") == 0
    offset = session.scalar(
        select(DownPaymentOffset).where(DownPaymentOffset.tenant_id == tenant)
    )
    assert (
        offset.final_invoice_document_id,
        offset.down_payment_document_id,
        offset.amount,
    ) == (invoice, down_payment, Decimal("300.0000"))
    # The down-payment invoice stays paid; its offset is used up.
    assert core.open_invoice_amount(session, tenant, down_payment) == 0
    proposal_id = next(
        p.id
        for p in session.scalars(
            select(core.ChangeProposal).where(
                core.ChangeProposal.tenant_id == tenant,
                core.ChangeProposal.type == "tool:sales_invoice_record",
            )
        )
    )
    from reality.services.delivery_actions import delivery_proposal_detail

    detail = delivery_proposal_detail(session, tenant, proposal_id)
    assert detail["verification"] == "verified"
    assert {"kind": "down_payment_offset", "id": offset.id} in detail["links"]


def test_a_second_final_invoice_offers_only_what_is_left(session, business):
    initialize_accounts(session, business.tenant.id)
    order, line, _ = _order(session, business)
    down_payment = _paid_down_payment(session, business, order)
    _reviewed(
        session,
        business,
        "sales_invoice_record",
        _final(
            line,
            "5",
            "500.00",
            "RE-299-A",
            [{"down_payment_document_id": down_payment, "amount": "200.00"}],
        ),
        "first",
    )

    review = prepare_delivery_action(
        session,
        business.tenant.id,
        "sales_invoice_record",
        _final(line, "5", "500.00", "RE-299-B"),
        request_id="second",
    )
    (offer,) = json.loads(review.input)["_delivery_review"]["state"][
        "down_payment_offers"
    ]

    assert (offer["offset"], offer["offsettable"]) == ("200.0000", "100.0000")


def test_a_consolidated_final_invoice_offsets_too(session, business):
    tenant = business.tenant.id
    initialize_accounts(session, tenant)
    order, line, _ = _order(session, business)
    down_payment = _paid_down_payment(session, business, order)

    _, receipt = _reviewed(
        session,
        business,
        "sales_invoice_record",
        {
            "lines": [
                {"order_line_id": line.id, "quantity": "10", "gross_amount": "1000.00"}
            ],
            "gross_amount": "1000.00",
            "number": "RE-299-L",
            "effective_at": "2026-09-25T10:00:00Z",
            "down_payment_offsets": [
                {"down_payment_document_id": down_payment, "amount": "300.00"}
            ],
        },
        "lines",
    )

    assert core.open_invoice_amount(
        session, tenant, _invoice_document(receipt)
    ) == Decimal("700.00")


def test_the_rest_paid_makes_the_prepayment_order_ready(session, business):
    tenant = business.tenant.id
    initialize_accounts(session, tenant)
    order, line, commitment = _order(session, business, prepay=True)
    down_payment = _paid_down_payment(session, business, order)
    _, receipt = _reviewed(
        session,
        business,
        "sales_invoice_record",
        _final(
            line,
            offsets=[{"down_payment_document_id": down_payment, "amount": "300.00"}],
        ),
        "final-prepay",
    )
    # Positive control: before the rest is paid, 700 is still required.
    assert fulfillment_readiness(session, tenant, commitment.id).remaining_amount == (
        Decimal("700.0000")
    )

    core.post_customer_payment(
        session, tenant, _invoice_document(receipt), "700.00", payment_number="PAY-R"
    )

    readiness = fulfillment_readiness(session, tenant, commitment.id)
    assert readiness.received_amount == Decimal("1000.00")
    assert not {"prepayment_required", "prepayment_invoice_missing"} & set(
        readiness.blocker_codes
    )


def _refused(session, business, arguments):
    with pytest.raises(core.InvalidOperation) as refused:
        prepare_delivery_action(
            session,
            business.tenant.id,
            "sales_invoice_record",
            arguments,
            request_id="refused",
        )
    return refused.value.code


def test_an_offset_beyond_what_was_paid_is_refused(session, business):
    initialize_accounts(session, business.tenant.id)
    order, line, _ = _order(session, business)
    down_payment = _paid_down_payment(session, business, order)
    _, unpaid = _down_payment(session, business, order, "100.00", "AR-299-U")

    def offset(document, amount):
        return _final(
            line, offsets=[{"down_payment_document_id": document, "amount": amount}]
        )

    assert _refused(session, business, offset(down_payment, "300.01")) == (
        "down_payment_offset_exceeds_paid"
    )
    assert _refused(session, business, offset(unpaid["document_id"], "1")) == (
        "down_payment_offset_exceeds_paid"
    )
    # Positive control: the paid amount itself is accepted.
    prepare_delivery_action(
        session,
        business.tenant.id,
        "sales_invoice_record",
        offset(down_payment, "300.00"),
        request_id="accepted",
    )


def test_an_offset_beyond_the_invoice_is_refused(session, business):
    initialize_accounts(session, business.tenant.id)
    order, line, _ = _order(session, business)
    down_payment = _paid_down_payment(session, business, order)

    assert (
        _refused(
            session,
            business,
            _final(
                line,
                "1",
                "100.00",
                offsets=[{"down_payment_document_id": down_payment, "amount": "200"}],
            ),
        )
        == "down_payment_offset_exceeds_invoice"
    )


def test_an_offset_of_another_orders_down_payment_is_refused(session, business):
    initialize_accounts(session, business.tenant.id)
    _, line, _ = _order(session, business)
    other, _, _ = _order(session, business, number="SO-299-B")
    foreign = _paid_down_payment(session, business, other, number="AR-299-B")

    assert (
        _refused(
            session,
            business,
            _final(
                line, offsets=[{"down_payment_document_id": foreign, "amount": "300"}]
            ),
        )
        == "down_payment_offset_other_order"
    )
    # A goods invoice is not a down payment either.
    _, plain = _reviewed(
        session,
        business,
        "sales_invoice_record",
        _final(line, "1", "100.00", "RE-PLAIN"),
        "plain-other",
    )
    assert (
        _refused(
            session,
            business,
            _final(
                line,
                "1",
                "100.00",
                "RE-X",
                [{"down_payment_document_id": _invoice_document(plain), "amount": "1"}],
            ),
        )
        == "down_payment_offset_other_order"
    )


def test_an_offset_of_a_reversed_down_payment_is_refused(session, business):
    from reality.db.core import LedgerEntry

    tenant = business.tenant.id
    initialize_accounts(session, tenant)
    order, line, _ = _order(session, business)
    _, receipt = _down_payment(session, business, order)
    down_payment = receipt["document_id"]
    payment = core.post_customer_payment(
        session, tenant, down_payment, "300.00", payment_number="PAY-REV"
    )
    core.reverse_ledger_posting_group(
        session, tenant, payment[0].posting_group_id, reason="Bounced"
    )
    group = session.scalar(
        select(LedgerEntry.posting_group_id).where(
            LedgerEntry.tenant_id == tenant,
            LedgerEntry.document_id == down_payment,
            LedgerEntry.account == "customer_down_payments",
        )
    )
    core.reverse_ledger_posting_group(session, tenant, group, reason="Cancelled")

    assert (
        _refused(
            session,
            business,
            _final(
                line,
                offsets=[{"down_payment_document_id": down_payment, "amount": "300"}],
            ),
        )
        == "down_payment_offset_reversed"
    )


@pytest.mark.parametrize(
    "offsets",
    [
        "300",
        [],
        [{"down_payment_document_id": "x"}],
        [{"down_payment_document_id": "x", "amount": "1", "extra": 1}],
        [{"down_payment_document_id": "x", "amount": "0"}],
    ],
)
def test_offsets_are_stated_as_a_list_of_documents_and_amounts(
    session, business, offsets
):
    initialize_accounts(session, business.tenant.id)
    _, line, _ = _order(session, business)

    assert _refused(session, business, _final(line, offsets=offsets)) == (
        "down_payment_offset_fields_invalid"
    )


# --- T021 review: offsets, reversals and what counts as paid ---------------------------


def _offset_final(
    session, business, line, down_payment, amount="300.00", number="RE-RV"
):
    _, receipt = _reviewed(
        session,
        business,
        "sales_invoice_record",
        _final(
            line,
            number=number,
            offsets=[{"down_payment_document_id": down_payment, "amount": amount}],
        ),
        number,
    )
    return _invoice_document(receipt)


def _group(session, tenant, document_id, account):
    from reality.db.core import LedgerEntry

    return session.scalar(
        select(LedgerEntry.posting_group_id).where(
            LedgerEntry.tenant_id == tenant,
            LedgerEntry.document_id == document_id,
            LedgerEntry.account == account,
        )
    )


def _offers(session, business, line):
    """What a final invoice for the line's order is offered (the review's read)."""
    from reality.services.down_payments import down_payment_offers

    order_id = session.get(DocumentLine, (business.tenant.id, line.id)).document_id
    return down_payment_offers(session, business.tenant.id, [order_id])


def test_a_final_invoice_is_reversed_after_its_offset_and_frees_the_down_payment(
    session, business
):
    tenant = business.tenant.id
    initialize_accounts(session, tenant)
    order, line, _ = _order(session, business)
    down_payment = _paid_down_payment(session, business, order)
    final = _offset_final(session, business, line, down_payment)
    invoice_group = _group(session, tenant, final, "sales_revenue")
    offset_group = _group(session, tenant, final, "customer_down_payments")

    # The invoice cannot go while its offset stands: received down payments
    # would stay debited for an invoice that no longer exists.
    with pytest.raises(core.InvalidOperation) as refused:
        core.reverse_ledger_posting_group(
            session, tenant, invoice_group, reason="Wrong"
        )
    assert refused.value.code == "down_payment_offset_reverse_first"

    core.reverse_ledger_posting_group(session, tenant, offset_group, reason="Undo")
    (offer,) = _offers(session, business, line)
    assert (offer["offset"], offer["offsettable"]) == ("0.0000", "300.0000")
    assert core.account_balance(session, tenant, "customer_down_payments") == Decimal(
        "-300.00"
    )
    # Positive control: with the offset reversed, the invoice can be reversed.
    core.reverse_ledger_posting_group(session, tenant, invoice_group, reason="Wrong")
    _offset_final(session, business, line, down_payment, number="RE-RV-2")


def test_an_offset_down_payment_and_its_payment_cannot_be_reversed(session, business):
    tenant = business.tenant.id
    initialize_accounts(session, tenant)
    order, line, _ = _order(session, business)
    _, receipt = _down_payment(session, business, order)
    down_payment = receipt["document_id"]
    payment = core.post_customer_payment(
        session, tenant, down_payment, "300.00", payment_number="PAY-OFF"
    )
    final = _offset_final(session, business, line, down_payment)

    for group in (
        payment[0].posting_group_id,
        _group(session, tenant, down_payment, "customer_down_payments"),
    ):
        with pytest.raises(core.InvalidOperation) as refused:
            core.reverse_ledger_posting_group(session, tenant, group, reason="Bounced")
        assert refused.value.code == "down_payment_offset_active"

    # Positive control: once the offset is reversed, the payment can come back.
    core.reverse_ledger_posting_group(
        session,
        tenant,
        _group(session, tenant, final, "customer_down_payments"),
        reason="Undo",
    )
    core.reverse_ledger_posting_group(
        session, tenant, payment[0].posting_group_id, reason="Bounced"
    )


def test_a_down_payment_settled_by_a_credit_is_not_paid(session, business):
    from reality.db.core import LedgerEntry

    tenant = business.tenant.id
    initialize_accounts(session, tenant)
    order, line, _ = _order(session, business)
    _, receipt = _down_payment(session, business, order)
    down_payment = receipt["document_id"]
    note = core.create_document(
        session, tenant, "credit_note", "GS-DP", business.customer.id, "300.00"
    )
    core.post_sales_credit_note(session, tenant, note.id)

    def control(document_id, side):
        return session.scalar(
            select(LedgerEntry.id).where(
                LedgerEntry.tenant_id == tenant,
                LedgerEntry.document_id == document_id,
                LedgerEntry.account == "accounts_receivable",
                LedgerEntry.debit_credit == side,
            )
        )

    core.allocate_settlement(
        session,
        tenant,
        control(note.id, "credit"),
        control(down_payment, "debit"),
        "300",
    )
    assert core.open_invoice_amount(session, tenant, down_payment) == 0

    (offer,) = _offers(session, business, line)
    # Settled, but not by money received: nothing may be deducted for it.
    assert (offer["paid"], offer["offsettable"]) == ("0.0000", "0.0000")


def test_a_consolidated_invoice_offsetting_the_down_payment_counts_it_once(
    session, business
):
    tenant = business.tenant.id
    initialize_accounts(session, tenant)
    order, line, commitment = _order(session, business, prepay=True)
    _, other_line, _ = _order(session, business, number="SO-299-C", total="500.00")
    down_payment = _paid_down_payment(session, business, order, "400.00", "AR-C")

    _, receipt = _reviewed(
        session,
        business,
        "sales_invoice_record",
        {
            "lines": [
                {"order_line_id": line.id, "quantity": "6", "gross_amount": "600.00"},
                {
                    "order_line_id": other_line.id,
                    "quantity": "10",
                    "gross_amount": "500.00",
                },
            ],
            "gross_amount": "1100.00",
            "number": "RE-C",
            "effective_at": "2026-09-25T10:00:00Z",
            "down_payment_offsets": [
                {"down_payment_document_id": down_payment, "amount": "400.00"}
            ],
        },
        "consolidated",
    )
    invoice = _invoice_document(receipt)
    core.post_customer_payment(
        session, tenant, invoice, "700.00", payment_number="PAY-C"
    )
    assert core.open_invoice_amount(session, tenant, invoice) == 0

    readiness = fulfillment_readiness(session, tenant, commitment.id)
    # 400 down payment plus this order's 600 on the settled consolidated invoice,
    # less the 400 that invoice deducted: 600 received, not 1,000.
    assert readiness.received_amount == Decimal("600.0000")
    assert readiness.remaining_amount == Decimal("400.0000")


def test_a_received_down_payment_lowers_the_credit_exposure(session, business):
    from reality.services.credit_exposure import credit_exposure

    tenant = business.tenant.id
    initialize_accounts(session, tenant)
    order, line, _ = _order(session, business)
    _, receipt = _down_payment(session, business, order, "400.00", "AR-EXP")
    # Positive control: an unpaid down-payment invoice holds no money.
    assert credit_exposure(session, tenant, business.customer.id)["exposure"] == (
        Decimal("1000.0000")
    )

    core.post_customer_payment(
        session, tenant, receipt["document_id"], "400.00", payment_number="PAY-EXP"
    )
    exposure = credit_exposure(session, tenant, business.customer.id)
    assert exposure["exposure"] == Decimal("600.0000")
    assert [row["origin"] for row in exposure["available_credits"]["rows"]] == [
        "down_payment"
    ]

    # Once offset, the final invoice's open 600 is the exposure; nothing twice.
    _offset_final(session, business, line, receipt["document_id"], "400.00", "RE-EXP")
    assert credit_exposure(session, tenant, business.customer.id)["exposure"] == (
        Decimal("600.00")
    )


# --- T020 manual check: the stored fulfillment queue follows payments ------------------


def _queued(session, tenant, order_id):
    from tests.test_incremental_derivation import _queue

    row = _queue(session, tenant).get(order_id)
    return row and sorted(
        {code for line in row["lines"] for code in line["blocking_reasons"]}
    )


@pytest.mark.parametrize("down_payment", [False, True])
def test_the_narrowed_queue_follows_an_invoice_and_its_payment(
    session, business, down_payment
):
    from reality.services import projections

    tenant = business.tenant.id
    initialize_accounts(session, tenant)
    order, line, _ = _order(session, business, prepay=True)
    projections.refresh_operational_projections(session, tenant)
    assert "prepayment_invoice_missing" in _queued(session, tenant, order.id)

    if down_payment:
        _, receipt = _down_payment(session, business, order)
        document, amount = receipt["document_id"], "300.00"
    else:
        invoice = core.record_sales_invoice(
            session, tenant, line.id, "10", "1000.00", "RE-Q"
        )
        document, amount = _invoice_document(invoice), "1000.00"
    payment = core.post_customer_payment(
        session, tenant, document, amount, payment_number="PAY-Q"
    )
    with projections.narrowing_report() as report:
        projections.refresh_operational_projections(session, tenant)
    assert report.get(projections.FULFILLMENT_QUEUE) is None
    narrowed = _queued(session, tenant, order.id)
    projections.refresh_operational_projections(session, tenant, force=True)
    # The narrowed refresh agrees with the company evaluated whole.
    assert narrowed == _queued(session, tenant, order.id)
    assert "prepayment_invoice_missing" not in narrowed

    core.reverse_ledger_posting_group(
        session, tenant, payment[0].posting_group_id, reason="Bounced"
    )
    projections.refresh_operational_projections(session, tenant)
    narrowed = _queued(session, tenant, order.id)
    projections.refresh_operational_projections(session, tenant, force=True)
    assert narrowed == _queued(session, tenant, order.id)
    assert "prepayment_required" in narrowed
