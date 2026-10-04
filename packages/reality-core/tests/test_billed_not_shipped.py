"""Invoiced but not shipped, and the month-end billing lists (spec 299 FR-001).

The sales mirror of Billed and not received: an invoice line that bills more of
a customer order line than has shipped is reported until the goods ship.
"""

import json
from decimal import Decimal

from intake_review_support import (
    reviewed_cancel_commitment,
    reviewed_post_sales_invoice,
)
from sqlalchemy import select

from reality.db.core import LedgerEntry
from reality.services import core
from reality.services.delivery_actions import prepare_delivery_action
from reality.services.month_end_billing import month_end_billing
from reality.tools.application import approve_and_execute_proposal
from tests.operational_exceptions.test_derivation import (
    AS_OF,
    bill,
    by_class,
    order,
    ship,
    stock,
)


def test_an_invoice_ahead_of_the_goods_is_reported_until_they_ship(session, business):
    stock(session, business)
    _, line, commitment = order(session, business)
    # Positive control: an order nobody has invoiced reports nothing.
    assert "billed_not_shipped" not in by_class(session, business.tenant.id)

    bill(session, business, line, quantity="5")
    row = by_class(session, business.tenant.id)["billed_not_shipped"]

    assert (row.record_type, row.record_id, row.severity) == (
        "document_line",
        line.id,
        "normal",
    )
    assert (
        row.causal_values["billed_quantity"],
        row.causal_values["shipped_quantity"],
        row.causal_values["unshipped_quantity"],
    ) == (Decimal("5.0000"), Decimal(0), Decimal("5.0000"))
    assert row.trace["document_id"] == commitment.document_id

    ship(session, business, commitment, 3)
    assert by_class(session, business.tenant.id)["billed_not_shipped"].causal_values[
        "unshipped_quantity"
    ] == Decimal("2.0000")

    ship(session, business, commitment, 2)
    assert "billed_not_shipped" not in by_class(session, business.tenant.id)


def test_shipping_ahead_of_the_invoice_is_not_this_class(session, business):
    stock(session, business)
    _, _, commitment = order(session, business)
    ship(session, business, commitment, 5)

    classes = by_class(session, business.tenant.id)
    assert "billed_not_shipped" not in classes
    # Control: the opposite direction is reported by its own class.
    assert "shipped_not_billed" in classes


def test_a_down_payment_invoice_reports_nothing(session, business):
    tenant = business.tenant.id
    reviewed_initialize_accounts(session, tenant)
    document, line, _ = order(session, business)
    proposal = prepare_delivery_action(
        session,
        tenant,
        "down_payment_invoice_record",
        {"order_id": document.id, "number": "AR-BNS", "gross_amount": "30.00"},
        request_id="dp-bns",
    )
    approve_and_execute_proposal(
        session,
        tenant,
        proposal.id,
        review_token=json.loads(proposal.input)["_delivery_review"]["token"],
        confirmed=True,
    )

    assert "billed_not_shipped" not in by_class(session, tenant)
    # Control: a goods invoice for the same line is reported.
    bill(session, business, line, quantity="1")
    assert "billed_not_shipped" in by_class(session, tenant)


def test_a_cancelled_line_stays_reported_until_its_invoice_is_reversed(
    session, business
):
    tenant = business.tenant.id
    _, line, commitment = order(session, business)
    invoice, _ = bill(session, business, line, quantity="5")
    reviewed_post_sales_invoice(session, tenant, invoice.id)

    reviewed_cancel_commitment(session, tenant, commitment.id, reason="Customer withdrew")
    # The customer was asked to pay for goods that will now never ship.
    assert "billed_not_shipped" in by_class(session, tenant)

    group = session.scalar(
        select(LedgerEntry.posting_group_id).where(
            LedgerEntry.tenant_id == tenant, LedgerEntry.document_id == invoice.id
        )
    )
    core.reverse_ledger_posting_group(session, tenant, group, reason="Cancelled")
    assert "billed_not_shipped" not in by_class(session, tenant)


def test_the_month_end_lists_are_the_findings(session, business):
    tenant = business.tenant.id
    stock(session, business)
    _, shipped_line, shipped = order(session, business, number="SO-ME-1")
    ship(session, business, shipped, 4)
    _, billed_line, _ = order(session, business, number="SO-ME-2")
    bill(session, business, billed_line, number="RE-ME", quantity="5")

    lists = month_end_billing(session, tenant, as_of=AS_OF)
    findings = by_class(session, tenant)

    assert lists["as_of"] == AS_OF.isoformat()
    (unbilled,) = lists["shipped_not_billed"]
    (unshipped,) = lists["billed_not_shipped"]
    assert (unbilled["order_line_id"], unbilled["exception_id"]) == (
        shipped_line.id,
        findings["shipped_not_billed"].id,
    )
    assert (unbilled["order_number"], unbilled["quantity"]) == ("SO-ME-1", "4.0000")
    assert (unshipped["order_line_id"], unshipped["exception_id"]) == (
        billed_line.id,
        findings["billed_not_shipped"].id,
    )
    assert (unshipped["order_number"], unshipped["quantity"]) == ("SO-ME-2", "5.0000")
    assert unshipped["item_id"] == business.item.id


from intake_review_support import reviewed_initialize_accounts
