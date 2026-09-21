"""One linked operating case traverses every unified business action."""

import json
from decimal import Decimal

import pytest
from conftest import record_by_id
from sqlalchemy import func, select

from reality.db.core import (
    Document,
    DocumentLine,
    LedgerEntry,
    Movement,
    Reservation,
    SourceRecord,
)
from reality.services import core
from reality.services.delivery_actions import (
    delivery_proposal_detail,
    prepare_delivery_action,
)
from reality.services.delivery_reads import delivery_case
from reality.tools.application import approve_and_execute_proposal


def counts(session, tenant):
    return tuple(
        session.scalar(
            select(func.count()).select_from(model).where(model.tenant_id == tenant)
        )
        for model in (Document, Movement, Reservation, LedgerEntry)
    )


def execute(session, tenant, tool, args, key):
    before = counts(session, tenant)
    proposal = prepare_delivery_action(session, tenant, tool, args, request_id=key)
    assert counts(session, tenant) == before
    token = json.loads(proposal.input)["_delivery_review"]["token"]
    approve_and_execute_proposal(
        session, tenant, proposal.id, confirmed=True, review_token=token
    )
    result = delivery_proposal_detail(session, tenant, proposal.id)
    assert result["verification"] == "verified", result
    after = counts(session, tenant)
    approve_and_execute_proposal(
        session, tenant, proposal.id, confirmed=True, review_token=token
    )
    assert counts(session, tenant) == after
    return result


def record_id(result, family):
    return next(
        row["id"] for row in result["receipt"]["records"] if row["family"] == family
    )


@pytest.mark.parametrize("refund_amount", ["75", "200"])
def test_linked_partial_delivery_invoice_credit_refund_and_reversal(
    session, business, refund_amount
):
    b, tenant = business, business.tenant.id
    core.record_movement(
        session, tenant, "receipt", b.item.id, "20", to_location_id=b.location.id
    )
    order = execute(
        session,
        tenant,
        "order_create",
        {
            "direction": "sales",
            "number": "SO-127",
            "company_party_id": b.company.id,
            "counterparty_id": b.customer.id,
            "location_id": b.location.id,
            "currency": "EUR",
            "gross_amount": "1000",
            "lines": [
                {
                    "item_id": b.item.id,
                    "quantity": "10",
                    "unit_price": "100",
                    "gross_amount": "1000",
                }
            ],
        },
        "order",
    )
    cid = order["receipt"]["commitment_ids"][0]
    order_line = order["receipt"]["document_line_ids"][0]
    execute(
        session, tenant, "reserve", {"commitment_id": cid, "quantity": "10"}, "reserve"
    )
    execute(
        session,
        tenant,
        "movement_create",
        {
            "movement_type": "shipment",
            "commitment_id": cid,
            "item_id": b.item.id,
            "from_location_id": b.location.id,
            "quantity": "6",
        },
        "ship",
    )
    case = delivery_case(session, tenant, cid)
    assert Decimal(case["case"]["open"]) == 4
    assert Decimal(case["inventory"]["physical"]) == 14
    assert Decimal(case["case"]["reserved"]) == 4
    invoice = execute(
        session,
        tenant,
        "sales_invoice_record",
        {
            "number": "INV-127",
            "gross_amount": "400",
            "lines": [
                {"order_line_id": order_line, "quantity": "4", "gross_amount": "400"}
            ],
        },
        "invoice",
    )
    invoice_id = record_id(invoice, "document")
    invoice_line = record_id(invoice, "document_line")
    execute(
        session,
        tenant,
        "customer_payment_post",
        {"invoice_id": invoice_id, "amount": "400", "payment_number": "PAY-127"},
        "payment",
    )
    credit = execute(
        session,
        tenant,
        "sales_credit_record",
        {
            "invoice_id": invoice_id,
            "number": "CR-127",
            "gross_amount": "200",
            "reason": "Agreed partial credit",
            "allocation_amount": "0",
            "lines": [
                {
                    "invoice_line_id": invoice_line,
                    "quantity": "2",
                    "gross_amount": "200",
                }
            ],
        },
        "credit",
    )
    credit_id = record_id(credit, "document")
    refund = execute(
        session,
        tenant,
        "customer_refund_post",
        {
            "credit_note_id": credit_id,
            "amount": refund_amount,
            "refund_number": "REF-127",
        },
        "refund",
    )
    assert core.open_invoice_amount(session, tenant, invoice_id) == 0
    assert core.open_invoice_amount(session, tenant, credit_id) == Decimal(
        200
    ) - Decimal(refund_amount)
    entry = record_by_id(session, LedgerEntry, record_id(refund, "ledger_entry"))
    execute(
        session,
        tenant,
        "ledger_reverse",
        {
            "posting_group_id": entry.posting_group_id,
            "reason": "Refund recorded incorrectly",
        },
        "reverse",
    )
    assert core.open_invoice_amount(session, tenant, credit_id) == 200
    historical = delivery_proposal_detail(session, tenant, refund["id"])
    assert historical["verification"] == "verified"
    assert historical["observation"]["allocation_active"] is False
    assert delivery_case(session, tenant, cid)["case"]["open"] == case["case"]["open"]
    assert (
        delivery_case(session, tenant, cid)["inventory"]["physical"]
        == case["inventory"]["physical"]
    )
    assert (
        record_by_id(session, DocumentLine, invoice_line).billed_document_line_id
        == order_line
    )
    assert (
        record_by_id(
            session, DocumentLine, record_id(credit, "document_line")
        ).billed_document_line_id
        == invoice_line
    )
    assert core._order_line_billing(session, tenant, order_line)["remaining"] == 6
    for result, expected in [(invoice, "400"), (credit, "200")]:
        document = record_by_id(session, Document, record_id(result, "document"))
        source = record_by_id(session, SourceRecord, document.source_record_id)
        assert Decimal(json.loads(source.payload)["gross_amount"]) == Decimal(expected)
