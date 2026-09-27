"""Spec 283 FR-008: the Inspector leads from an invoice to every order it bills."""

import json
from uuid import uuid4

from reality.services import core
from reality.tools.application import confirm_tool, propose_tool
from reality.web.api import document_inspector


def purchase(session, b, number):
    _, document, lines, _ = core.create_manual_order(
        session,
        b.tenant.id,
        "purchase",
        number,
        b.company.id,
        b.supplier.id,
        b.location.id,
        [
            {
                "item_id": b.item.id,
                "quantity": "3",
                "unit_price": "10",
                "gross_amount": "30",
            }
        ],
        gross_amount="30",
    )
    return document, lines[0]


def section(inspector, title):
    return next(s for s in inspector["sections"] if s["title"] == title)


def test_an_invoice_names_every_order_it_bills_and_each_order_names_it(
    session, business
):
    """Invoice → each order through the line links; each order → the invoice."""
    first_order, first = purchase(session, business, "PO-283-" + uuid4().hex[:4])
    second_order, second = purchase(session, business, "PO-283-" + uuid4().hex[:4])
    proposal = propose_tool(
        session,
        business.tenant.id,
        "supplier_invoice_free_record",
        {
            "supplier_id": business.supplier.id,
            "number": "SINV-283",
            "currency": "EUR",
            "gross_amount": "50",
            "document_date": "2026-09-20",
            "lines": [
                {
                    "item_id": business.item.id,
                    "description": "First",
                    "quantity": "3",
                    "unit_price": "10",
                    "gross_amount": "30",
                    "billed_document_line_id": first.id,
                },
                {
                    "item_id": business.item.id,
                    "description": "Second",
                    "quantity": "2",
                    "unit_price": "10",
                    "gross_amount": "20",
                    "billed_document_line_id": second.id,
                },
            ],
        },
    )
    executed = confirm_tool(session, business.tenant.id, proposal.id, confirmed=True)
    invoice_id = next(
        row["id"]
        for row in json.loads(executed.output)["records"]
        if row["family"] == "document"
    )

    billed = section(
        document_inspector(session, business.tenant.id, invoice_id), "Billed orders"
    )
    assert [(row["link"]["kind"], row["link"]["id"]) for row in billed["rows"]] == [
        ("document", first_order.id),
        ("document", second_order.id),
    ]
    assert [row["label"] for row in billed["rows"]] == [
        first_order.number,
        second_order.number,
    ]

    for order, line in ((first_order, first), (second_order, second)):
        evidence = next(
            row
            for row in document_inspector(session, business.tenant.id, order.id)[
                "evidence_lines"
            ]
            if row["id"] == line.id
        )
        assert [row["invoice_id"] for row in evidence["billing"]["evidence"]] == [
            invoice_id
        ]


def test_an_order_itself_has_no_billed_orders_section(session, business):
    """Positive scope: only a billing document lists the orders it bills."""
    order, _ = purchase(session, business, "PO-283-PLAIN")
    titles = [
        s["title"]
        for s in document_inspector(session, business.tenant.id, order.id)["sections"]
    ]
    assert "Billed orders" not in titles
