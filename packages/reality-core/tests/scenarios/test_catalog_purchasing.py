"""Purchasing scenarios from the catalog (G14, H10, H11, H12, I05)."""

import json
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from conftest import record_by_id
from sqlalchemy import select

from reality.db.core import Movement
from reality.services import core
from reality.services.exceptions import operational_exceptions
from reality.services.shipments import shipment_explain
from reality.services.supply_assignments import assign_supply, supply_coverage
from reality.tools.application import (
    approve_and_execute_proposal,
    confirm_tool,
    create_change_proposal,
    propose_tool,
)

AS_OF = datetime(2026, 9, 25, 12, tzinfo=UTC)


def _order(session, business, direction, number, counterparty_id, quantity, price):
    gross = str(Decimal(quantity) * Decimal(price))
    _, document, lines, commitments = core.create_manual_order(
        session,
        business.tenant.id,
        direction,
        number,
        business.company.id,
        counterparty_id,
        business.location.id,
        [
            {
                "item_id": business.item.id,
                "quantity": quantity,
                "unit_price": price,
                "gross_amount": gross,
            }
        ],
        gross,
        document_date="2026-09-01",
    )
    return document, lines[0], commitments[0]


def _execute_delivery(session, tenant_id, tool, arguments):
    proposal = create_change_proposal(session, tenant_id, tool, arguments)
    token = json.loads(proposal.input)["_delivery_review"]["token"]
    return approve_and_execute_proposal(
        session, tenant_id, proposal.id, review_token=token, confirmed=True
    )


def _records_of(session, tenant_id, class_id):
    return {
        row.record_id
        for row in operational_exceptions(session, tenant_id, as_of=AS_OF)
        if row.class_id == class_id
    }


def test_two_suppliers_purchases_together_protect_one_customer_promise(
    session, business
):
    """G14: two suppliers' purchases together protect one customer promise."""
    second_supplier = core.create_party(
        session, business.tenant.id, "Light Works AG", "supplier"
    )
    _, _, customer = _order(
        session, business, "sales", "SO-G14", business.customer.id, "10", "20"
    )
    _, _, first = _order(
        session, business, "purchase", "PO-G14-A", business.supplier.id, "6", "10"
    )
    _, _, second = _order(
        session, business, "purchase", "PO-G14-B", second_supplier.id, "8", "11"
    )
    assign_supply(
        session,
        business.tenant.id,
        first.id,
        "6",
        purpose="customer_demand",
        customer_commitment_id=customer.id,
        request_id="g14-first",
    )
    assign_supply(
        session,
        business.tenant.id,
        second.id,
        "4",
        purpose="customer_demand",
        customer_commitment_id=customer.id,
        request_id="g14-second",
    )

    coverage = supply_coverage(
        session, business.tenant.id, customer_commitment_id=customer.id
    )
    assert coverage["customer"]["quantity"] == Decimal(10)
    assert coverage["customer"]["protecting_supply"] == Decimal(10)
    assert sorted(
        (item["supplier_commitment_id"], item["quantity"]) for item in coverage["items"]
    ) == sorted([(first.id, Decimal(6)), (second.id, Decimal(4))])
    assert {first.from_party_id, second.from_party_id} == {
        business.supplier.id,
        second_supplier.id,
    }
    second_view = supply_coverage(
        session, business.tenant.id, supplier_commitment_id=second.id
    )["supplier"]
    assert second_view["customer_assigned"] == Decimal(4)
    assert second_view["unassigned"] == Decimal(4)


def test_one_inbound_package_is_split_across_several_purchase_orders(session, business):
    """H10: one received package fulfils several purchase orders by their own lines."""
    _, _, first = _order(
        session, business, "purchase", "PO-H10-A", business.supplier.id, "5", "10"
    )
    _, _, second = _order(
        session, business, "purchase", "PO-H10-B", business.supplier.id, "7", "10"
    )
    before = core.stock_at(
        session, business.tenant.id, business.item.id, business.location.id
    )
    proposal = _execute_delivery(
        session,
        business.tenant.id,
        "shipment_receive",
        {
            "purpose": "supplier_delivery",
            "counterparty_id": business.supplier.id,
            "tracking_number": "IN-H10",
            "movements": [
                {
                    "commitment_id": first.id,
                    "item_id": business.item.id,
                    "to_location_id": business.location.id,
                    "quantity": "5",
                },
                {
                    "commitment_id": second.id,
                    "item_id": business.item.id,
                    "to_location_id": business.location.id,
                    "quantity": "4",
                },
            ],
        },
    )
    receipt = json.loads(proposal.output)
    movements = list(
        session.scalars(
            select(Movement).where(
                Movement.tenant_id == business.tenant.id,
                Movement.shipment_package_id == receipt["package_id"],
            )
        )
    )

    assert {movement.id for movement in movements} == set(receipt["movement_ids"])
    assert sorted((m.commitment_id, m.quantity) for m in movements) == sorted(
        [(first.id, Decimal(5)), (second.id, Decimal(4))]
    )
    assert core.fulfilled_quantity(session, business.tenant.id, first.id) == Decimal(5)
    assert core.fulfilled_quantity(session, business.tenant.id, second.id) == Decimal(4)
    terms = core.commitment_terms(session, business.tenant.id, [first.id, second.id])
    assert terms[first.id].open == Decimal(0)
    assert terms[second.id].open == Decimal(3)
    assert core.stock_at(
        session, business.tenant.id, business.item.id, business.location.id
    ) == before + Decimal(9)
    detail = shipment_explain(session, business.tenant.id, receipt["shipment_id"])
    assert Decimal(detail["quantities"]["received"]) == Decimal(9)


def test_early_receipt_fulfils_the_purchase_and_keeps_its_due_date(session, business):
    """H11: a delivery before the confirmed date is recorded and readable as early."""
    due = datetime(2026, 9, 20, tzinfo=UTC)
    received_at = datetime(2026, 9, 12, 9, tzinfo=UTC)
    early = core.create_commitment(
        session,
        business.tenant.id,
        "supplier_delivery",
        business.supplier.id,
        business.company.id,
        business.item.id,
        business.location.id,
        "8",
        due,
    )
    waiting = core.create_commitment(
        session,
        business.tenant.id,
        "supplier_delivery",
        business.supplier.id,
        business.company.id,
        business.item.id,
        business.location.id,
        "3",
        due,
    )
    movement = core.record_movement(
        session,
        business.tenant.id,
        "receipt",
        business.item.id,
        "8",
        to_location_id=business.location.id,
        commitment_id=early.id,
        occurred_at=received_at,
    )

    terms = core.commitment_terms(session, business.tenant.id, [early.id])[early.id]
    assert terms.fulfilled == Decimal(8)
    assert terms.open == Decimal(0)
    assert terms.due_at == due
    stored = record_by_id(session, Movement, movement.id)
    assert stored.occurred_at == received_at
    # No read labels a receipt "early"; it is derivable from the two held values.
    assert terms.due_at - stored.occurred_at == timedelta(days=7, hours=15)
    overdue = _records_of(
        session, business.tenant.id, "overdue_incoming_supplier_commitment"
    )
    assert waiting.id in overdue
    assert early.id not in overdue


def test_receipt_before_purchase_order_is_linked_later_by_replacement(
    session, business
):
    """H12: a receipt booked before its purchase order exists is linked to it later."""
    received_at = datetime(2026, 9, 10, 8, tzinfo=UTC)
    receipt = core.record_movement(
        session,
        business.tenant.id,
        "receipt",
        business.item.id,
        "10",
        to_location_id=business.location.id,
        occurred_at=received_at,
    )
    assert receipt.id in _records_of(
        session, business.tenant.id, "unexplained_movement"
    )
    assert core.stock_at(
        session, business.tenant.id, business.item.id, business.location.id
    ) == Decimal(10)

    _, _, purchase = _order(
        session, business, "purchase", "PO-H12", business.supplier.id, "10", "10"
    )
    assert core.fulfilled_quantity(session, business.tenant.id, purchase.id) == Decimal(
        0
    )
    result = core.correct_movement(
        session,
        business.tenant.id,
        receipt.id,
        reason="Receipt belongs to PO-H12, entered later",
        replacement={
            "type": "receipt",
            "item_id": business.item.id,
            "quantity": "10",
            "to_location_id": business.location.id,
            "commitment_id": purchase.id,
            "occurred_at": received_at,
        },
    )

    replacement = record_by_id(session, Movement, result.replacement_movement_id)
    assert replacement.commitment_id == purchase.id
    assert replacement.occurred_at == received_at
    assert core.stock_at(
        session, business.tenant.id, business.item.id, business.location.id
    ) == Decimal(10)
    assert core.fulfilled_quantity(session, business.tenant.id, purchase.id) == Decimal(
        10
    )
    unexplained = _records_of(session, business.tenant.id, "unexplained_movement")
    assert receipt.id not in unexplained
    assert replacement.id not in unexplained


def test_one_supplier_invoice_bills_lines_of_two_purchase_orders(session, business):
    """I05: one supplier invoice over two purchase orders is allocated per purchase."""
    _, first_line, _ = _order(
        session, business, "purchase", "PO-I05-A", business.supplier.id, "5", "10"
    )
    _, second_line, _ = _order(
        session, business, "purchase", "PO-I05-B", business.supplier.id, "3", "20"
    )
    # The order-line invoice command keeps one invoice to one order.
    with pytest.raises(core.InvalidOperation, match="same order"):
        core.record_supplier_invoice(
            session,
            business.tenant.id,
            lines=[
                {
                    "order_line_id": first_line.id,
                    "quantity": "5",
                    "gross_amount": "50",
                },
                {
                    "order_line_id": second_line.id,
                    "quantity": "2",
                    "gross_amount": "40",
                },
            ],
            gross_amount="90",
            number="SINV-I05-REFUSED",
        )

    proposal = propose_tool(
        session,
        business.tenant.id,
        "supplier_invoice_free_record",
        {
            "supplier_id": business.supplier.id,
            "number": "SINV-I05",
            "currency": "EUR",
            "gross_amount": "90",
            "document_date": "2026-09-15",
            "lines": [
                {
                    "item_id": business.item.id,
                    "description": "PO-I05-A goods",
                    "quantity": "5",
                    "unit_price": "10",
                    "gross_amount": "50",
                    "billed_document_line_id": first_line.id,
                },
                {
                    "item_id": business.item.id,
                    "description": "PO-I05-B goods",
                    "quantity": "2",
                    "unit_price": "20",
                    "gross_amount": "40",
                    "billed_document_line_id": second_line.id,
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

    first_billing = core._order_line_billing(session, business.tenant.id, first_line.id)
    second_billing = core._order_line_billing(
        session, business.tenant.id, second_line.id
    )
    assert (first_billing["invoiced"], first_billing["remaining"]) == (
        Decimal(5),
        Decimal(0),
    )
    assert (second_billing["invoiced"], second_billing["remaining"]) == (
        Decimal(2),
        Decimal(1),
    )
    assert [row["invoice_id"] for row in first_billing["evidence"]] == [invoice_id]
    assert [row["invoice_id"] for row in second_billing["evidence"]] == [invoice_id]
    assert core.open_invoice_amount(session, business.tenant.id, invoice_id) == Decimal(
        90
    )

    # The allocation is binding: PO-A is fully billed, PO-B has exactly one left.
    with pytest.raises(core.InvalidOperation, match="remaining"):
        core.record_supplier_invoice(
            session, business.tenant.id, first_line.id, "1", "10", "SINV-I05-OVER"
        )
    core.record_supplier_invoice(
        session, business.tenant.id, second_line.id, "1", "20", "SINV-I05-REST"
    )
    assert core._order_line_billing(session, business.tenant.id, second_line.id)[
        "remaining"
    ] == Decimal(0)
