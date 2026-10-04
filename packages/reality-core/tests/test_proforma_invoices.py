"""Pro-forma invoices for an order (spec 299 FR-004).

A pro-forma is evidence only: it is for its order, posts nothing, is no open
item, bills no quantity and counts nothing towards prepayment.
"""

import json
from decimal import Decimal

import pytest
from intake_review_support import (
    reviewed_create_payment_term,
    reviewed_manual_order,
    reviewed_record_sales_invoice,
)
from sqlalchemy import func, select

from reality.db.core import Document, DocumentLine, LedgerEntry
from reality.services import core
from reality.services.delivery_actions import (
    delivery_proposal_detail,
    prepare_delivery_action,
)
from reality.services.fulfillment_readiness import fulfillment_readiness
from reality.tools.application import approve_and_execute_proposal
from reality.web.api import document_inspector


def _order(session, business, number="SO-PF", prepay=False):
    tenant = business.tenant.id
    if prepay:
        reviewed_create_payment_term(
            session, tenant, "PREPAY", "Prepayment", 0, requires_prepayment=True
        )
    _, order, lines, commitments = reviewed_manual_order(
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
                "unit_price": "100",
                "gross_amount": "1000.00",
            }
        ],
        "1000.00",
        **({"payment_term_code": "PREPAY"} if prepay else {}),
    )
    return order, lines[0], commitments[0]


def _reviewed(session, business, tool, arguments, request_id):
    proposal = prepare_delivery_action(
        session, business.tenant.id, tool, arguments, request_id=request_id
    )
    review = json.loads(proposal.input)["_delivery_review"]
    executed = approve_and_execute_proposal(
        session,
        business.tenant.id,
        proposal.id,
        review_token=review["token"],
        confirmed=True,
    )
    assert executed.status == "executed"
    return proposal, review, json.loads(executed.output)


def _proforma(session, business, order, **extra):
    return _reviewed(
        session,
        business,
        "proforma_invoice_record",
        {
            "order_id": order.id,
            "number": "PF-1",
            "gross_amount": "1000.00",
            "document_date": "2026-09-18",
            **extra,
        },
        f"pf-{extra.get('number', 'PF-1')}",
    )


def _ledger_count(session, tenant):
    return session.scalar(
        select(func.count())
        .select_from(LedgerEntry)
        .where(LedgerEntry.tenant_id == tenant)
    )


def test_a_proforma_is_for_its_order_and_posts_nothing(session, business):
    tenant = business.tenant.id
    reviewed_initialize_accounts(session, tenant)
    order, _, _ = _order(session, business)
    before = _ledger_count(session, tenant)

    proposal, review, receipt = _proforma(session, business, order)

    document = session.get(Document, (tenant, receipt["document_id"]))
    assert (document.type, document.order_document_id, document.gross_amount) == (
        "proforma_invoice",
        order.id,
        Decimal("1000.0000"),
    )
    assert review["effect"]["posts"] is False
    assert _ledger_count(session, tenant) == before
    assert document.id not in {
        row["document_id"] for row in core.financial_open_items(session, tenant)
    }
    detail = delivery_proposal_detail(session, tenant, proposal.id)
    assert detail["verification"] == "verified"


def test_a_proforma_states_its_lines(session, business):
    tenant = business.tenant.id
    order, _, _ = _order(session, business)

    _, _, receipt = _proforma(
        session,
        business,
        order,
        number="PF-L",
        lines=[
            {"description": "Widget", "quantity": "10", "gross_amount": "1000.00"},
        ],
    )

    (line,) = session.scalars(
        select(DocumentLine).where(
            DocumentLine.tenant_id == tenant,
            DocumentLine.document_id == receipt["document_id"],
        )
    )
    assert (line.description, line.quantity, line.billed_document_line_id) == (
        "Widget",
        Decimal("10.0000"),
        None,
    )


def test_a_proforma_bills_nothing_and_proves_no_prepayment(session, business):
    tenant = business.tenant.id
    reviewed_initialize_accounts(session, tenant)
    order, line, commitment = _order(session, business, prepay=True)

    _proforma(session, business, order)

    assert core._order_line_billing(session, tenant, line.id)["invoiced"] == 0
    assert "prepayment_invoice_missing" in (
        fulfillment_readiness(session, tenant, commitment.id).blocker_codes
    )
    # Control: a goods invoice for 5 bills them and is the payment basis.
    reviewed_record_sales_invoice(session, tenant, line.id, "5", "500.00", "RE-PF")
    assert core._order_line_billing(session, tenant, line.id)["invoiced"] == 5
    assert "prepayment_invoice_missing" not in (
        fulfillment_readiness(session, tenant, commitment.id).blocker_codes
    )


def test_the_order_inspector_lists_its_billing_documents(session, business):
    tenant = business.tenant.id
    reviewed_initialize_accounts(session, tenant)
    order, _, _ = _order(session, business)
    _proforma(session, business, order)
    _reviewed(
        session,
        business,
        "down_payment_invoice_record",
        {"order_id": order.id, "number": "AR-PF", "gross_amount": "300.00"},
        "dp-pf",
    )

    sections = {
        section["title"]: section["rows"]
        for section in document_inspector(session, tenant, order.id)["sections"]
    }

    rows = sections["Down-payment and pro-forma invoices"]
    assert [(row["label"], row["link"]["kind"], row.get("meta")) for row in rows] == [
        ("Pro-forma invoice PF-1", "document", "Posts nothing"),
        ("Down-payment invoice AR-PF", "document", "Paid 0.00 · offset 0.00"),
    ]
    # The pro-forma names its order.
    proforma = rows[0]["link"]["id"]
    (row,) = {
        section["title"]: section["rows"]
        for section in document_inspector(session, tenant, proforma)["sections"]
    }["For order"]
    assert (row["label"], row["link"]["id"]) == ("SO-PF", order.id)


def test_an_order_without_billing_documents_shows_no_section(session, business):
    order, _, _ = _order(session, business)

    titles = {
        section["title"]
        for section in document_inspector(session, business.tenant.id, order.id)[
            "sections"
        ]
    }

    assert "Down-payment and pro-forma invoices" not in titles
    assert "Lines" in titles


@pytest.mark.parametrize(
    ("change", "code"),
    [
        ({"currency": "USD"}, "proforma_currency_mismatch"),
        ({"gross_amount": "0"}, "proforma_amount_invalid"),
        ({"number": " "}, "proforma_number_missing"),
        ({"document_date": "soon"}, "proforma_date_invalid"),
        ({"lines": []}, "proforma_line_fields_invalid"),
        ({"lines": [{"description": "x"}]}, "proforma_line_fields_invalid"),
        (
            {"lines": [{"quantity": "1", "gross_amount": "1"}]},
            ("proforma_line_fields_invalid"),
        ),
        ({"unknown": 1}, "proforma_fields_invalid"),
        ({"order_id": "purchase"}, "proforma_order_required"),
    ],
)
def test_a_proforma_is_refused_with_its_code(session, business, change, code):
    order, _, _ = _order(session, business)
    arguments = {
        "order_id": order.id,
        "number": "PF-BAD",
        "gross_amount": "100.00",
        **change,
    }
    if arguments["order_id"] == "purchase":
        _, purchase, _, _ = reviewed_manual_order(
            session,
            business.tenant.id,
            "purchase",
            "PO-PF",
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
            "proforma_invoice_record",
            arguments,
            request_id="pf-bad",
        )
    assert refused.value.code == code


from intake_review_support import reviewed_initialize_accounts
