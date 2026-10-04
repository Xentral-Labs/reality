"""Catalog scenarios for drop shipping (spec 337): D10, D11, G15 and R03.

Every step goes through the reviewed tools a person or an agent uses: the order
and the drop-ship purchase order, the assignment of the purchase to the
customer's line, the supplier's dispatch, invoices, the return and the credits.
"""

import json
from decimal import Decimal

from conftest import record_by_id

from reality.db.core import Commitment
from reality.services.core import (
    account_balance,
    fulfilled_quantity,
    record_movement,
    reserve,
    stock_at,
)
from reality.services.delivery_actions import prepare_delivery_action
from reality.services.drop_shipping import drop_shipments
from reality.services.exceptions import operational_exceptions
from reality.services.shipments import shipment_explain
from reality.tools.application import (
    approve_and_execute_proposal,
    confirm_tool,
    create_change_proposal,
    propose_tool,
)


def _reviewed(session, business, tool, arguments, request_id):
    proposal = prepare_delivery_action(
        session, business.tenant.id, tool, arguments, request_id=request_id
    )
    token = json.loads(proposal.input)["_delivery_review"]["token"]
    executed = approve_and_execute_proposal(
        session, business.tenant.id, proposal.id, review_token=token, confirmed=True
    )
    assert executed.status == "executed"
    return json.loads(executed.output)


def _tool(session, business, tool, arguments):
    proposal = propose_tool(session, business.tenant.id, tool, arguments)
    return json.loads(confirm_tool(session, business.tenant.id, proposal.id, confirmed=True).output)


def _order(session, business, direction, number, quantity, unit_price, **extra):
    gross = str(Decimal(quantity) * Decimal(unit_price))
    receipt = _reviewed(
        session,
        business,
        "order_create",
        {
            "direction": direction,
            "number": number,
            "company_party_id": business.company.id,
            "counterparty_id": business.customer.id
            if direction == "sales"
            else business.supplier.id,
            "location_id": business.location.id,
            "currency": "EUR",
            "gross_amount": gross,
            "lines": [
                {
                    "item_id": business.item.id,
                    "quantity": quantity,
                    "unit_price": unit_price,
                    "gross_amount": gross,
                }
            ],
            **extra,
        },
        number,
    )
    (commitment_id,) = receipt["commitment_ids"]
    return record_by_id(session, Commitment, commitment_id)


def _drop_ship_order(session, business, number, sale, quantity):
    """G15: a purchase order the supplier ships to the customer, for the sale."""
    purchase = _order(
        session,
        business,
        "purchase",
        number,
        quantity,
        "12.00",
        ship_to_party_id=business.customer.id,
    )
    _reviewed(
        session,
        business,
        "supply_assign",
        {
            "supplier_commitment_id": purchase.id,
            "quantity": quantity,
            "purpose": "customer_demand",
            "customer_commitment_id": sale.id,
        },
        f"assign-{number}",
    )
    return purchase


def _drop_ship(session, business, purchase, quantity, tracking):
    return _reviewed(
        session,
        business,
        "drop_shipment_record",
        {
            "supplier_commitment_id": purchase.id,
            "quantity": quantity,
            "carrier": "DHL",
            "tracking_number": tracking,
        },
        f"drop-{tracking}",
    )


def _document(
    session, business, kind, number, party_id, order_line_id, quantity, price
):
    gross = str(Decimal(quantity) * Decimal(price))
    recorded = _tool(
        session,
        business,
        "document_create",
        {
            "document_type": kind,
            "number": number,
            "party_id": party_id,
            "gross_amount": gross,
            "document_date": "2026-10-03",
            "lines": [
                {
                    "item_id": business.item.id,
                    "quantity": quantity,
                    "unit": "pcs",
                    "unit_price": price,
                    "gross_amount": gross,
                    "billed_document_line_id": order_line_id,
                }
            ],
        },
    )
    post = {
        "sales_invoice": "sales_invoice_post",
        "supplier_invoice": "supplier_invoice_post",
        "credit_note": "credit_note_post",
        "supplier_credit_note": "supplier_credit_note_post",
    }[kind]
    key = "credit_note_id" if kind.endswith("credit_note") else "document_id"
    _tool(session, business, post, {key: recorded["document_id"]})
    return recorded["document_id"]


def _findings(session, business, record_ids):
    return {
        (row.class_id, row.record_id)
        for row in operational_exceptions(session, business.tenant.id)
        if row.record_id in record_ids
    }


def test_a_drop_ship_purchase_order_is_linked_to_the_customer_order(session, business):
    """G15: the purchase names the customer as where the goods go and serves its line."""
    tenant = business.tenant.id
    sale = _order(session, business, "sales", "SO-G15", "3", "20.00")
    # Positive control: an order nobody can serve from stock is at risk.
    assert ("outgoing_commitment_at_risk", sale.id) in _findings(
        session, business, {sale.id}
    )

    purchase = _drop_ship_order(session, business, "PO-G15", sale, "3")

    (link,) = drop_shipments(session, tenant, commitment_id=sale.id)["links"]
    assert (link["supplier_commitment_id"], link["assigned"]) == (
        purchase.id,
        Decimal(3),
    )
    assert link["supplier_party_id"] == business.supplier.id
    # The supplier ships it, so it is not a shortage of the company's stock, and
    # the purchase brings nothing to the warehouse.
    assert not _findings(session, business, {sale.id})
    assert stock_at(session, tenant, business.item.id, business.location.id) == 0


def test_the_supplier_ships_straight_to_the_customer(session, business):
    """D10: the customer is served without any movement of own stock."""
    tenant = business.tenant.id
    sale = _order(session, business, "sales", "SO-D10", "4", "20.00")
    purchase = _drop_ship_order(session, business, "PO-D10", sale, "4")

    shipped = _drop_ship(session, business, purchase, "4", "DS-D10")

    for promise in (sale, purchase):
        assert record_by_id(session, Commitment, promise.id).status == "fulfilled"
    assert stock_at(session, tenant, business.item.id) == 0
    shipment = shipment_explain(session, tenant, shipped["shipment_id"])
    assert shipment["counterparty_id"] == business.customer.id
    assert shipment["packages"][0]["tracking_number"] == "DS-D10"
    # Shipped and not yet billed, on both sides, until the invoices come.
    sale_line, purchase_line = sale.document_line_id, purchase.document_line_id
    assert ("shipped_not_billed", sale_line) in _findings(
        session, business, {sale_line}
    )
    _document(
        session,
        business,
        "sales_invoice",
        "RE-D10",
        business.customer.id,
        sale_line,
        "4",
        "20.00",
    )
    _document(
        session,
        business,
        "supplier_invoice",
        "ER-D10",
        business.supplier.id,
        purchase_line,
        "4",
        "12.00",
    )
    assert not _findings(session, business, {sale_line, purchase_line, sale.id})


def test_one_order_is_served_partly_from_stock_and_partly_by_the_supplier(
    session, business
):
    """D11: own stock and a drop shipment keep the same promise together."""
    tenant = business.tenant.id
    record_movement(
        session,
        tenant,
        "receipt",
        business.item.id,
        "6",
        to_location_id=business.location.id,
    )
    sale = _order(session, business, "sales", "SO-D11", "10", "20.00")
    reserve(session, tenant, sale.id)
    purchase = _drop_ship_order(session, business, "PO-D11", sale, "4")
    # The six in stock are reserved, the four the supplier ships are not a shortage.
    assert not _findings(session, business, {sale.id})

    proposal = create_change_proposal(
        session,
        tenant,
        "shipment_dispatch",
        {
            "purpose": "customer_delivery",
            "counterparty_id": business.customer.id,
            "carrier": "DHL",
            "tracking_number": "OWN-D11",
            "movements": [
                {
                    "commitment_id": sale.id,
                    "item_id": business.item.id,
                    "from_location_id": business.location.id,
                    "quantity": "6",
                }
            ],
        },
    )
    token = json.loads(proposal.input)["_delivery_review"]["token"]
    approve_and_execute_proposal(
        session, tenant, proposal.id, review_token=token, confirmed=True
    )
    assert record_by_id(session, Commitment, sale.id).status == "open"

    _drop_ship(session, business, purchase, "4", "DS-D11")

    assert fulfilled_quantity(session, tenant, sale.id) == Decimal(10)
    assert record_by_id(session, Commitment, sale.id).status == "fulfilled"
    assert stock_at(session, tenant, business.item.id, business.location.id) == 0
    read = drop_shipments(session, tenant, commitment_id=sale.id)
    assert [row["quantity"] for row in read["drop_shipments"]] == [Decimal(4)]


def test_a_drop_shipped_return_comes_to_us_and_both_sides_are_credited(
    session, business
):
    """R03: the customer returns to us, not to the supplier; credits on both sides."""
    tenant = business.tenant.id
    sale = _order(session, business, "sales", "SO-R03", "2", "20.00")
    purchase = _drop_ship_order(session, business, "PO-R03", sale, "2")
    _drop_ship(session, business, purchase, "2", "DS-R03")
    sale_line, purchase_line = sale.document_line_id, purchase.document_line_id
    _document(
        session,
        business,
        "sales_invoice",
        "RE-R03",
        business.customer.id,
        sale_line,
        "2",
        "20.00",
    )
    _document(
        session,
        business,
        "supplier_invoice",
        "ER-R03",
        business.supplier.id,
        purchase_line,
        "2",
        "12.00",
    )

    # The customer sends the goods back to the company's warehouse. They were
    # never in stock; now they are, and they belong to the company.
    record_movement(
        session,
        tenant,
        "return",
        business.item.id,
        "2",
        to_location_id=business.location.id,
        commitment_id=sale.id,
    )
    assert stock_at(session, tenant, business.item.id, business.location.id) == 2
    assert ("returned_not_credited", sale_line) in _findings(
        session, business, {sale_line}
    )
    _document(
        session,
        business,
        "credit_note",
        "GS-R03",
        business.customer.id,
        sale_line,
        "2",
        "20.00",
    )

    # The company sends them on to the supplier, against the drop-ship purchase.
    record_movement(
        session,
        tenant,
        "supplier_return",
        business.item.id,
        "2",
        from_location_id=business.location.id,
        commitment_id=purchase.id,
    )
    assert stock_at(session, tenant, business.item.id, business.location.id) == 0
    assert ("supplier_return_not_credited", purchase_line) in _findings(
        session, business, {purchase_line}
    )
    _document(
        session,
        business,
        "supplier_credit_note",
        "SG-R03",
        business.supplier.id,
        purchase_line,
        "2",
        "12.00",
    )

    assert not _findings(session, business, {sale_line, purchase_line})
    # What the customer owes and what the company owes the supplier both net out.
    assert account_balance(session, tenant, "accounts_receivable") == Decimal(0)
    assert account_balance(session, tenant, "accounts_payable") == Decimal(0)
