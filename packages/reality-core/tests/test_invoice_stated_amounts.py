"""Invoices carry the net and tax they state, compared and never derived (spec 284)."""

import json

import pytest
from conftest import record_by_id
from sqlalchemy import func, select

from reality.db.core import (
    ChangeProposal,
    Document,
    DocumentLine,
    LedgerEntry,
    SourceRecord,
)
from reality.mcp.catalog import MCP_TOOL_REGISTRY
from reality.services.core import InvalidOperation, create_manual_order
from reality.services.delivery_actions import (
    delivery_proposal_detail,
    prepare_delivery_action,
)
from reality.services.finance import components
from reality.tools.application import approve_and_execute_proposal

STATED = {"net": "50.00", "tax": "9.50"}


def order_line(session, business, direction="sales", number="ORDER-284"):
    order = create_manual_order(
        session,
        business.tenant.id,
        direction,
        number,
        business.company.id,
        business.customer.id if direction == "sales" else business.supplier.id,
        business.location.id,
        [
            {
                "item_id": business.item.id,
                "quantity": "4",
                "unit_price": "29.75",
                "gross_amount": "119.00",
            },
            {
                "item_id": business.item.id,
                "quantity": "4",
                "unit_price": "29.75",
                "gross_amount": "119.00",
            },
        ],
        gross_amount="238.00",
    )
    return [line.id for line in order[2]]


def tool(direction):
    return "sales_invoice_record" if direction == "sales" else "supplier_invoice_record"


def single(session, business, line, direction="sales", request="single", **extra):
    return prepare_delivery_action(
        session,
        business.tenant.id,
        tool(direction),
        {
            "order_line_id": line,
            "quantity": "2",
            "gross_amount": "59.50",
            "number": f"INV-{request}",
            "effective_at": "2026-09-26T10:00:00Z",
            **extra,
        },
        request_id=request,
    )


def confirm(session, business, proposal):
    return approve_and_execute_proposal(
        session,
        business.tenant.id,
        proposal.id,
        review_token=json.loads(proposal.input)["_delivery_review"]["token"],
        confirmed=True,
    )


def invoice_lines(session, proposal):
    ids = [
        row["id"]
        for row in json.loads(proposal.output)["records"]
        if row["family"] == "document_line"
    ]
    return [record_by_id(session, DocumentLine, identity) for identity in ids]


def detail(line):
    return json.loads(line.payload or "{}").get("reality_finance_v1")


# The stated amounts check ---------------------------------------------------------


def test_net_plus_tax_contradiction_is_refused_and_records_nothing(session, business):
    line = order_line(session, business)[0]
    before = session.scalar(select(func.count()).select_from(DocumentLine))
    with pytest.raises(InvalidOperation, match="Net plus tax differs"):
        single(
            session, business, line, reality_finance_v1={"net": "50.00", "tax": "10.00"}
        )
    assert session.scalar(select(func.count()).select_from(DocumentLine)) == before
    # Positive control: the consistent statement is accepted by the same path.
    assert single(session, business, line, request="ok", reality_finance_v1=STATED)


@pytest.mark.parametrize(
    "stated",
    [
        {"net": "50.00", "rate": "19"},
        {"net": "-1"},
        {"net": "50.00001"},
        {"net": "fifty"},
        {"gross": "60.00"},
        {"net": "50.00", "currency": "USD"},
        "50.00",
    ],
)
def test_malformed_statements_are_refused(session, business, stated):
    line = order_line(session, business)[0]
    with pytest.raises(InvalidOperation):
        single(session, business, line, request="bad", reality_finance_v1=stated)


# US1 single position ----------------------------------------------------------------


@pytest.mark.parametrize("direction", ["sales", "purchase"])
def test_single_position_records_stated_net_and_tax(session, business, direction):
    line = order_line(session, business, direction)[0]
    proposal = single(session, business, line, direction, reality_finance_v1=STATED)
    review = json.loads(proposal.input)["_delivery_review"]
    # The person confirms the stated amounts: they are part of the reviewed creation.
    assert review["state"]["creation"]["lines"][0]["reality_finance_v1"] == STATED
    confirm(session, business, proposal)
    (invoice_line,) = invoice_lines(session, proposal)
    # Recorded exactly as stated: no normalizing, no added keys.
    assert detail(invoice_line) == STATED
    invoice = record_by_id(session, Document, invoice_line.document_id)
    source = record_by_id(session, SourceRecord, invoice.source_record_id)
    assert json.loads(source.payload)["reality_finance_v1"] == STATED
    amounts = components.component_context(
        session, business.tenant.id, invoice_line.document_id
    )["items"][0]["amounts"]
    assert amounts["net"] == "50" and amounts["tax"] == "9.5"


def test_stated_net_makes_the_contribution_a_candidate(session, business):
    lines = order_line(session, business)
    plain = single(session, business, lines[0], request="plain")
    stated = single(
        session, business, lines[1], request="stated", reality_finance_v1=STATED
    )
    confirm(session, business, plain)
    confirm(session, business, stated)

    def received_net(proposal):
        (line,) = invoice_lines(session, proposal)
        invoice = record_by_id(session, Document, line.document_id)
        # The contribution preview reads exactly this and gaps on None.
        return components._received(session, business.tenant.id, invoice, line)[
            "amounts"
        ]["net"]

    assert received_net(plain) is None
    assert received_net(stated) == "50"


def test_mcp_single_position_proposal_carries_the_statement(session, business):
    line = order_line(session, business)[0]
    proposed = MCP_TOOL_REGISTRY["sales_invoice_record_propose"].handler(
        session,
        business.tenant.id,
        {
            "order_line_id": line,
            "quantity": "2",
            "gross_amount": "59.50",
            "number": "INV-MCP-284",
            "reality_finance_v1": STATED,
        },
    )
    proposal = record_by_id(session, ChangeProposal, proposed["proposal_id"])
    assert json.loads(proposal.input)["reality_finance_v1"] == STATED
    confirm(session, business, proposal)
    (invoice_line,) = invoice_lines(session, proposal)
    assert detail(invoice_line) == STATED


def test_gross_only_is_unchanged_and_posts_the_same_ledger(session, business):
    lines = order_line(session, business)
    plain = single(session, business, lines[0], request="plain")
    stated = single(
        session, business, lines[1], request="stated", reality_finance_v1=STATED
    )
    assert "reality_finance_v1" not in json.loads(plain.input)
    confirm(session, business, plain)
    confirm(session, business, stated)
    (plain_line,) = invoice_lines(session, plain)
    (stated_line,) = invoice_lines(session, stated)
    assert detail(plain_line) is None

    def postings(line):
        return sorted(
            (row.account, str(row.amount), row.debit_credit)
            for row in session.scalars(
                select(LedgerEntry).where(LedgerEntry.document_id == line.document_id)
            )
        )

    # DR-004: the stated net and tax change no ledger entry.
    assert postings(plain_line) == postings(stated_line)


# US2 multi position -----------------------------------------------------------------


def multi(session, business, positions, request="multi"):
    return prepare_delivery_action(
        session,
        business.tenant.id,
        "sales_invoice_record",
        {
            "lines": positions,
            "gross_amount": "119.00",
            "number": f"INV-{request}",
            "effective_at": "2026-09-26T10:00:00Z",
        },
        request_id=request,
    )


def test_multi_position_keeps_each_positions_amounts(session, business):
    first, second = order_line(session, business)
    proposal = multi(
        session,
        business,
        [
            {
                "order_line_id": first,
                "quantity": "2",
                "gross_amount": "59.50",
                "reality_finance_v1": STATED,
            },
            {"order_line_id": second, "quantity": "2", "gross_amount": "59.50"},
        ],
    )
    confirm(session, business, proposal)
    by_order_line = {
        row.billed_document_line_id: detail(row)
        for row in invoice_lines(session, proposal)
    }
    assert by_order_line == {first: STATED, second: None}
    # The post-execution check binds the stated amounts and still verifies.
    verification = delivery_proposal_detail(session, business.tenant.id, proposal.id)
    assert verification["verification"] == "verified"


def test_the_review_binds_each_positions_statement(session, business):
    first, second = order_line(session, business)

    def token(stated, request):
        proposal = multi(
            session,
            business,
            [
                {
                    "order_line_id": first,
                    "quantity": "2",
                    "gross_amount": "59.50",
                    "reality_finance_v1": stated,
                },
                {"order_line_id": second, "quantity": "2", "gross_amount": "59.50"},
            ],
            request=request,
        )
        return json.loads(proposal.input)["_delivery_review"]["token"]

    # Different stated amounts are a different decision, so a different review.
    assert token(STATED, "a") != token({"net": "49.00", "tax": "10.50"}, "b")


def test_positions_without_statement_keep_their_selection_shape(session, business):
    first, second = order_line(session, business)
    proposal = multi(
        session,
        business,
        [
            {"order_line_id": first, "quantity": "2", "gross_amount": "59.50"},
            {"order_line_id": second, "quantity": "2", "gross_amount": "59.50"},
        ],
    )
    selections = json.loads(proposal.input)["_delivery_review"]["state"]["creation"][
        "selections"
    ]
    # Invoices without statements keep exactly their former review shape (token stable).
    assert all(
        set(row) == {"order_line_id", "quantity", "gross_amount"} for row in selections
    )


def test_multi_position_contradiction_is_refused(session, business):
    first, second = order_line(session, business)
    with pytest.raises(InvalidOperation, match="Net plus tax differs"):
        multi(
            session,
            business,
            [
                {
                    "order_line_id": first,
                    "quantity": "2",
                    "gross_amount": "59.50",
                    "reality_finance_v1": {"net": "50.00", "tax": "9.00"},
                },
                {"order_line_id": second, "quantity": "2", "gross_amount": "59.50"},
            ],
        )


# US3 supplier invoices ----------------------------------------------------------------


def test_supplier_invoice_net_basis_is_available_to_cost_evidence(session, business):
    from reality.services.costing import cost_evidence

    lines = order_line(session, business, "purchase", "PO-284")
    plain = single(session, business, lines[0], "purchase", request="plain")
    stated = single(
        session, business, lines[1], "purchase", "stated", reality_finance_v1=STATED
    )
    confirm(session, business, plain)
    confirm(session, business, stated)

    def amounts(proposal):
        (line,) = invoice_lines(session, proposal)
        return cost_evidence(session, business.tenant.id, line.document_id, line.id)[
            "amounts"
        ]

    # Receipt costing reads the stated net instead of a gross of unknown tax treatment.
    assert amounts(stated)["net"] == "50" and amounts(stated)["tax"] == "9.5"
    assert amounts(plain)["net"] is None
