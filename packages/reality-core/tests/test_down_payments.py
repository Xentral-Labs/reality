"""Down-payment invoices for an order (spec 299 FR-002).

A down-payment invoice is for its order, is a receivable against received down
payments, bills no quantity, and paid it counts towards prepayment readiness.
"""

import json
from decimal import Decimal

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from reality.db.core import Document, DownPaymentOffset
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
