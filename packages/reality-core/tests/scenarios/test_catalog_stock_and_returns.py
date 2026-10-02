"""Catalog scenarios B04, F01, F03, F05, F07, J08 and L01: stock that moves between
promises and places, and goods that come back.

Each test drives the same services the CLI and tools call and answers one
catalog question with exact quantities.
"""

import json
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from conftest import record_by_id

from reality.db.core import Commitment
from reality.services.core import (
    InvalidOperation,
    account_balance,
    active_reserved,
    announce_customer_return,
    announcement_outstanding,
    arrived_against_announcement,
    business_events,
    create_commitment,
    create_item,
    create_location,
    create_lot,
    create_party,
    fulfilled_quantity,
    location_detail,
    open_invoice_amount,
    open_quantity,
    record_movement,
    release_reservation,
    reservation_register,
    reserve,
    return_announcements,
    stock_at,
)
from reality.services.delivery_actions import prepare_delivery_action
from reality.services.exceptions import operational_exceptions
from reality.services.movement_explanations import movement_explanation
from reality.services.read_contracts import location_inventory_rows
from reality.tools.application import (
    approve_and_execute_proposal,
    confirm_tool,
    propose_tool,
    run_read_tool,
)

AS_OF = datetime(2026, 8, 31, 12, tzinfo=UTC)


def customer_commitment(session, business, customer, location, quantity):
    return create_commitment(
        session,
        business.tenant.id,
        "customer_delivery",
        business.company.id,
        customer.id,
        business.item.id,
        location.id,
        quantity,
        "2026-09-03",
    )


def opening_stock(session, business, quantity, location=None, item=None):
    record_movement(
        session,
        business.tenant.id,
        "opening_stock",
        (item or business.item).id,
        quantity,
        to_location_id=(location or business.location).id,
    )


def reserved_for(session, business, commitment):
    return sum(
        (
            Decimal(row["reservation"].quantity)
            for row in reservation_register(session, business.tenant.id)
            if row["reservation"].commitment_id == commitment.id
            and row["reservation"].status == "active"
        ),
        Decimal(0),
    )


def position(session, business, location, item=None):
    row = location_inventory_rows(
        session,
        business.tenant.id,
        item_id=(item or business.item).id,
        location_id=location.id,
    )[f"{(item or business.item).id}:{location.id}"]
    return {key: Decimal(row[key]) for key in ("physical", "reserved", "available")}


def events_about(session, business, event_type, subject_id):
    return [
        event
        for event in business_events(session, business.tenant.id)
        if event.event_type == event_type and event.subject_id == subject_id
    ]


def test_stock_reserved_for_one_customer_can_be_moved_to_a_more_important_one(
    session, business
):
    """B04: releasing A's reservation and reserving for B moves the stock, traceably.

    There is no single "move reservation" operation; the move is a release
    followed by a new reservation, and the two are recorded as separate events.
    """
    tenant = business.tenant.id
    important = create_party(session, tenant, "Key Account AG", "customer")
    opening_stock(session, business, 10)
    for_a = customer_commitment(
        session, business, business.customer, business.location, 10
    )
    for_b = customer_commitment(session, business, important, business.location, 8)

    held_by_a = reserve(session, tenant, for_a.id)
    assert held_by_a.reserved == Decimal("10.0000")
    # Positive control for the shortage: while A holds everything, B gets nothing.
    assert reserve(session, tenant, for_b.id).reserved == Decimal(0)
    assert reserved_for(session, business, for_b) == Decimal(0)

    release_reservation(session, tenant, held_by_a.reservation.id)
    held_by_b = reserve(session, tenant, for_b.id)

    assert held_by_b.requested == Decimal("8.0000")
    assert held_by_b.reserved == Decimal("8.0000")
    assert held_by_b.shortage == Decimal(0)
    assert stock_at(session, tenant, business.item.id) == Decimal("10.0000")
    assert active_reserved(session, tenant, business.item.id) == Decimal("8.0000")
    assert reserved_for(session, business, for_a) == Decimal(0)
    assert reserved_for(session, business, for_b) == Decimal("8.0000")
    # Reservations promise nothing new: both deliveries are still fully open.
    assert open_quantity(session, tenant, for_a.id) == Decimal("10.0000")
    assert open_quantity(session, tenant, for_b.id) == Decimal("8.0000")
    assert position(session, business, business.location) == {
        "physical": Decimal("10.0000"),
        "reserved": Decimal("8.0000"),
        "available": Decimal("2.0000"),
    }
    # What is left over can go back to A, and no more than that.
    assert reserve(session, tenant, for_a.id).reserved == Decimal("2.0000")
    assert reserved_for(session, business, for_a) == Decimal("2.0000")

    # Both steps are traceable: the released reservation keeps its record and
    # its event names A's commitment; the new one names B's.
    assert held_by_a.reservation.status == "released"
    assert held_by_a.reservation.commitment_id == for_a.id
    assert held_by_b.reservation.commitment_id == for_b.id
    (released,) = events_about(
        session, business, "reservation.released", held_by_a.reservation.id
    )
    assert json.loads(released.payload) == {"commitment_id": for_a.id}
    (created,) = events_about(
        session, business, "reservation.created", held_by_b.reservation.id
    )
    created_payload = json.loads(created.payload)
    assert created_payload["commitment_id"] == for_b.id
    assert Decimal(str(created_payload["quantity"])) == Decimal(8)
    assert released.sequence < created.sequence


def test_a_different_item_returned_does_not_fulfil_the_announcement(session, business):
    """F03: a return of another item leaves the announcement open and stands unexplained."""
    tenant = business.tenant.id
    other = create_item(session, tenant, "BIKE-BELL", "Bike Bell")
    opening_stock(session, business, 10)
    delivery = customer_commitment(
        session, business, business.customer, business.location, 5
    )
    record_movement(
        session,
        tenant,
        "shipment",
        business.item.id,
        5,
        from_location_id=business.location.id,
        commitment_id=delivery.id,
        occurred_at=AS_OF - timedelta(days=25),
    )
    announcement = announce_customer_return(
        session,
        tenant,
        delivery.id,
        2,
        reference="RMA-4711",
        expected_by=AS_OF - timedelta(days=4),
        announced_at=AS_OF - timedelta(days=20),
    )

    # The other item cannot be booked against the announced delivery.
    with pytest.raises(InvalidOperation, match="does not match the commitment"):
        record_movement(
            session,
            tenant,
            "return",
            other.id,
            2,
            to_location_id=business.location.id,
            commitment_id=delivery.id,
            return_announcement_id=announcement.id,
        )

    # So it arrives as what it is: goods back with no delivery or announcement.
    foreign = record_movement(
        session,
        tenant,
        "return",
        other.id,
        2,
        to_location_id=business.location.id,
        occurred_at=AS_OF - timedelta(days=1),
    )
    assert stock_at(session, tenant, other.id, business.location.id) == Decimal(
        "2.0000"
    )
    explained = movement_explanation(session, tenant, foreign.id)
    assert explained["kind"] == "unexplained"
    assert explained["explained"] is False
    assert explained["links"] == []

    assert arrived_against_announcement(session, tenant, announcement.id) == Decimal(0)
    assert announcement_outstanding(session, tenant, announcement) == Decimal(2)
    row = {
        entry.class_id: entry
        for entry in operational_exceptions(session, tenant, as_of=AS_OF)
    }["announced_return_not_arrived"]
    assert row.record_id == announcement.id
    assert row.causal_values["outstanding_quantity"] == Decimal(2)

    # Positive control: the announced item coming back does clear it.
    arrived = record_movement(
        session,
        tenant,
        "return",
        business.item.id,
        2,
        to_location_id=business.location.id,
        commitment_id=delivery.id,
        return_announcement_id=announcement.id,
        occurred_at=AS_OF - timedelta(hours=2),
    )
    assert movement_explanation(session, tenant, arrived.id)["kind"] == (
        "return_announcement"
    )
    assert announcement_outstanding(session, tenant, announcement) == Decimal(0)
    assert "announced_return_not_arrived" not in {
        entry.class_id for entry in operational_exceptions(session, tenant, as_of=AS_OF)
    }
    assert {
        entry.id: entry.status
        for entry in return_announcements(session, tenant, commitment_id=delivery.id)
    } == {announcement.id: "fulfilled"}
    # The foreign return is still there and still unexplained.
    assert movement_explanation(session, tenant, foreign.id)["kind"] == "unexplained"


def test_consignment_stock_at_a_customer_site_stays_counted_as_ours(session, business):
    """J08: stock moved to a customer's site stays in the company total and is held there."""
    tenant = business.tenant.id
    site = create_location(session, tenant, "Müller GmbH consignment", "consignment")
    opening_stock(session, business, 20)

    record_movement(
        session,
        tenant,
        "transfer",
        business.item.id,
        6,
        from_location_id=business.location.id,
        to_location_id=site.id,
    )

    assert site.type == "consignment"
    assert stock_at(session, tenant, business.item.id) == Decimal("20.0000")
    assert stock_at(session, tenant, business.item.id, site.id) == Decimal("6.0000")
    assert stock_at(session, tenant, business.item.id, business.location.id) == (
        Decimal("14.0000")
    )
    assert [
        (entry["item"].id, entry["physical"])
        for entry in location_detail(session, tenant, site.id)["stock"]
    ] == [(business.item.id, Decimal("6.0000"))]

    # Availability is per place: a warehouse order cannot reserve what sits at
    # the customer, while one served from the site can.
    from_warehouse = customer_commitment(
        session, business, business.customer, business.location, 16
    )
    warehouse_hold = reserve(session, tenant, from_warehouse.id)
    assert warehouse_hold.reserved == Decimal("14.0000")
    assert warehouse_hold.shortage == Decimal("2.0000")
    from_site = customer_commitment(session, business, business.customer, site, 4)
    assert reserve(session, tenant, from_site.id).reserved == Decimal("4.0000")

    assert position(session, business, business.location) == {
        "physical": Decimal("14.0000"),
        "reserved": Decimal("14.0000"),
        "available": Decimal(0),
    }
    assert position(session, business, site) == {
        "physical": Decimal("6.0000"),
        "reserved": Decimal("4.0000"),
        "available": Decimal("2.0000"),
    }
    assert active_reserved(session, tenant, business.item.id) == Decimal("18.0000")


def test_stock_at_an_external_fulfilment_location_is_sold_from_there(session, business):
    """L01: stock sent to an FBA-style location is counted there and ships the order."""
    tenant = business.tenant.id
    fba = create_location(session, tenant, "Amazon FBA DE", "external_fulfillment")
    opening_stock(session, business, 30)
    record_movement(
        session,
        tenant,
        "transfer",
        business.item.id,
        12,
        from_location_id=business.location.id,
        to_location_id=fba.id,
    )
    assert fba.type == "external_fulfillment"
    assert stock_at(session, tenant, business.item.id) == Decimal("30.0000")
    assert position(session, business, fba) == {
        "physical": Decimal("12.0000"),
        "reserved": Decimal(0),
        "available": Decimal("12.0000"),
    }

    marketplace_buyer = create_party(session, tenant, "Amazon customer", "customer")
    order = customer_commitment(session, business, marketplace_buyer, fba, 5)
    assert reserve(session, tenant, order.id).reserved == Decimal("5.0000")
    assert position(session, business, fba)["available"] == Decimal("7.0000")
    # The warehouse is untouched by a reservation at FBA.
    assert position(session, business, business.location) == {
        "physical": Decimal("18.0000"),
        "reserved": Decimal(0),
        "available": Decimal("18.0000"),
    }

    record_movement(
        session,
        tenant,
        "shipment",
        business.item.id,
        5,
        from_location_id=fba.id,
        commitment_id=order.id,
    )

    assert fulfilled_quantity(session, tenant, order.id) == Decimal("5.0000")
    assert open_quantity(session, tenant, order.id) == Decimal(0)
    assert order.status == "fulfilled"
    assert position(session, business, fba) == {
        "physical": Decimal("7.0000"),
        "reserved": Decimal(0),
        "available": Decimal("7.0000"),
    }
    assert stock_at(session, tenant, business.item.id) == Decimal("25.0000")
    assert stock_at(session, tenant, business.item.id, business.location.id) == (
        Decimal("18.0000")
    )


# --- Returns and refunds: F01, F05, F07 (spec 292) -----------------------------

WATCHED = {
    "returned_not_credited",
    "credited_not_returned",
    "shipped_not_billed",
    "unexplained_movement",
}


def _tool(session, business, tool, arguments):
    proposal = propose_tool(session, business.tenant.id, tool, arguments)
    return json.loads(confirm_tool(session, business.tenant.id, proposal.id).output)


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


def _sales_order(session, business, number, quantity, unit_price):
    gross = str(Decimal(quantity) * Decimal(unit_price))
    receipt = _reviewed(
        session,
        business,
        "order_create",
        {
            "direction": "sales",
            "number": number,
            "company_party_id": business.company.id,
            "counterparty_id": business.customer.id,
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
        },
        number,
    )
    commitment = record_by_id(session, Commitment, receipt["commitment_ids"][0])
    return commitment, receipt["document_line_ids"][0]


def _deliver(session, business, commitment, quantity, days_ago):
    reserve(session, business.tenant.id, commitment.id)
    return record_movement(
        session,
        business.tenant.id,
        "shipment",
        business.item.id,
        quantity,
        from_location_id=business.location.id,
        commitment_id=commitment.id,
        occurred_at=AS_OF - timedelta(days=days_ago),
    )


def _invoice(session, business, number, order_line_id, quantity, unit_price):
    gross = str(Decimal(quantity) * Decimal(unit_price))
    recorded = _tool(
        session,
        business,
        "document_create",
        {
            "document_type": "sales_invoice",
            "number": number,
            "party_id": business.customer.id,
            "gross_amount": gross,
            "document_date": "2026-08-05",
            "lines": [
                {
                    "item_id": business.item.id,
                    "quantity": quantity,
                    "unit": "pcs",
                    "unit_price": unit_price,
                    "gross_amount": gross,
                    "billed_document_line_id": order_line_id,
                }
            ],
        },
    )
    _tool(
        session,
        business,
        "sales_invoice_post",
        {"document_id": recorded["document_id"]},
    )
    return recorded["document_id"], recorded["document_line_ids"][0]


def _signals(session, business, record_ids):
    return {
        (row.class_id, row.record_id)
        for row in operational_exceptions(session, business.tenant.id, as_of=AS_OF)
        if row.class_id in WATCHED and row.record_id in record_ids
    }


def test_a_b2c_withdrawal_brings_the_goods_back_and_refunds_in_full(session, business):
    """F01: stock back, full credit and the refund paid, with nothing left open."""
    tenant = business.tenant.id
    opening_stock(session, business, 10)
    commitment, order_line_id = _sales_order(session, business, "SO-F01", "2", "49.95")
    shipment = _deliver(session, business, commitment, 2, days_ago=20)
    invoice_id, invoice_line_id = _invoice(
        session, business, "RE-F01", order_line_id, "2", "49.95"
    )
    _reviewed(
        session,
        business,
        "customer_payment_post",
        {"invoice_id": invoice_id, "amount": "99.90"},
        "pay-f01",
    )
    assert open_invoice_amount(session, tenant, invoice_id) == Decimal(0)

    # Within 14 days the customer withdraws and sends both units back.
    goods_back = record_movement(
        session,
        tenant,
        "return",
        business.item.id,
        2,
        to_location_id=business.location.id,
        commitment_id=commitment.id,
        occurred_at=AS_OF - timedelta(days=10),
    )
    # Positive control: back but not yet credited is reported.
    assert ("returned_not_credited", order_line_id) in _signals(
        session, business, {order_line_id}
    )

    credited = _reviewed(
        session,
        business,
        "sales_credit_record",
        {
            "invoice_id": invoice_id,
            "lines": [
                {
                    "invoice_line_id": invoice_line_id,
                    "quantity": "2",
                    "gross_amount": "99.90",
                }
            ],
            "gross_amount": "99.90",
            "number": "GS-F01",
            "reason": "Withdrawal within 14 days",
            # The invoice is already paid, so the credit settles nothing yet.
            "allocation_amount": "0",
        },
        "credit-f01",
    )
    credit_note_id = next(
        row["id"] for row in credited["records"] if row["family"] == "document"
    )
    assert open_invoice_amount(session, tenant, credit_note_id) == Decimal("99.90")
    _reviewed(
        session,
        business,
        "customer_refund_post",
        {"credit_note_id": credit_note_id, "amount": "99.90"},
        "refund-f01",
    )

    assert stock_at(session, tenant, business.item.id, business.location.id) == (
        Decimal(10)
    )
    assert open_invoice_amount(session, tenant, invoice_id) == Decimal(0)
    assert open_invoice_amount(session, tenant, credit_note_id) == Decimal(0)
    assert account_balance(session, tenant, "accounts_receivable") == Decimal(0)
    assert account_balance(session, tenant, "cash") == Decimal(0)
    # The promise was kept when the goods went out; the return does not undo it.
    assert fulfilled_quantity(session, tenant, commitment.id) == Decimal(2)
    assert (
        _signals(session, business, {order_line_id, shipment.id, goods_back.id})
        == set()
    )


def test_a_damaged_return_is_disposed_and_credited_independently(session, business):
    """F05: what happens to the goods and what the customer gets back are separate."""
    tenant = business.tenant.id
    opening_stock(session, business, 10)
    returns_area = create_location(session, tenant, "Returns Area")
    commitment, order_line_id = _sales_order(session, business, "SO-F05", "5", "20.00")
    _deliver(session, business, commitment, 5, days_ago=20)
    invoice_id, invoice_line_id = _invoice(
        session, business, "RE-F05", order_line_id, "5", "20.00"
    )
    _reviewed(
        session,
        business,
        "customer_payment_post",
        {"invoice_id": invoice_id, "amount": "100.00"},
        "pay-f05",
    )

    # Two come back; one of them is damaged beyond repair.
    goods_back = record_movement(
        session,
        tenant,
        "return",
        business.item.id,
        2,
        to_location_id=returns_area.id,
        commitment_id=commitment.id,
        occurred_at=AS_OF - timedelta(days=10),
    )
    _reviewed(
        session,
        business,
        "return_disposition",
        {
            "return_movement_id": goods_back.id,
            "disposition": "restock",
            "quantity": "1",
            "destination_location_id": business.location.id,
        },
        "dispose-f05-restock",
    )
    _reviewed(
        session,
        business,
        "return_disposition",
        {
            "return_movement_id": goods_back.id,
            "disposition": "scrap_loss",
            "quantity": "1",
            "reason": "Housing cracked",
        },
        "dispose-f05-scrap",
    )

    # Positive control: the goods' fate does not settle what the customer is owed.
    assert ("returned_not_credited", order_line_id) in _signals(
        session, business, {order_line_id}
    )

    # The customer is credited for both units and charged for the damage.
    recorded = _tool(
        session,
        business,
        "document_create",
        {
            "document_type": "credit_note",
            "number": "GS-F05",
            "party_id": business.customer.id,
            "gross_amount": "25.00",
            "document_date": "2026-08-25",
            "lines": [
                {
                    "item_id": business.item.id,
                    "quantity": "2",
                    "unit": "pcs",
                    "unit_price": "20.00",
                    "gross_amount": "40.00",
                    "billed_document_line_id": invoice_line_id,
                },
                {
                    "description": "Damage deduction",
                    "quantity": "1",
                    "unit": "pcs",
                    "unit_price": "-15.00",
                    "gross_amount": "-15.00",
                    "line_type": "charge",
                },
            ],
        },
    )
    credit_note_id = recorded["document_id"]
    _tool(session, business, "credit_note_post", {"credit_note_id": credit_note_id})
    _reviewed(
        session,
        business,
        "customer_refund_post",
        {"credit_note_id": credit_note_id, "amount": "25.00"},
        "refund-f05",
    )

    summary = run_read_tool(
        session,
        tenant,
        "return_disposition_summary",
        {"return_movement_id": goods_back.id},
    )
    assert Decimal(summary["arrived"]) == Decimal(2)
    assert Decimal(summary["unresolved"]) == Decimal(0)
    assert {key: Decimal(value) for key, value in summary["totals"].items()} == {
        "restock": Decimal(1),
        "scrap_loss": Decimal(1),
        "quarantine_repair": Decimal(0),
        "return_to_supplier": Decimal(0),
    }
    # 10 - 5 shipped + 1 restocked; the scrapped unit left the returns area.
    assert stock_at(session, tenant, business.item.id, business.location.id) == (
        Decimal(6)
    )
    assert stock_at(session, tenant, business.item.id, returns_area.id) == Decimal(0)
    assert open_invoice_amount(session, tenant, invoice_id) == Decimal(0)
    assert open_invoice_amount(session, tenant, credit_note_id) == Decimal(0)
    assert account_balance(session, tenant, "cash") == Decimal("75.00")
    assert _signals(session, business, {order_line_id, goods_back.id}) == set()


def test_an_exchange_returns_one_unit_and_sends_another_without_money(
    session, business
):
    """F07: a return plus a replacement delivery moves no money and leaves no work.

    The exchange is recorded through the same reviewed tool the web and the agent
    use (spec 293); before it, the returned unit is owed a credit.
    """
    tenant = business.tenant.id
    opening_stock(session, business, 10)
    larger = create_item(session, tenant, "BIKE-LIGHT-XL", "Bike Light XL")
    opening_stock(session, business, 5, item=larger)
    commitment, order_line_id = _sales_order(session, business, "SO-F07", "1", "20.00")
    _deliver(session, business, commitment, 1, days_ago=20)
    invoice_id, _ = _invoice(session, business, "RE-F07", order_line_id, "1", "20.00")
    _reviewed(
        session,
        business,
        "customer_payment_post",
        {"invoice_id": invoice_id, "amount": "20.00"},
        "pay-f07",
    )
    cash_before = account_balance(session, tenant, "cash")
    goods_back = record_movement(
        session,
        tenant,
        "return",
        business.item.id,
        1,
        to_location_id=business.location.id,
        commitment_id=commitment.id,
        occurred_at=AS_OF - timedelta(days=10),
    )
    # Positive control: back and neither credited nor exchanged is reported.
    assert ("returned_not_credited", order_line_id) in _signals(
        session, business, {order_line_id}
    )

    receipt = _reviewed(
        session,
        business,
        "customer_exchange_record",
        {
            "return_movement_id": goods_back.id,
            "quantity": "1",
            "replacement_item_id": larger.id,
            "replacement_quantity": "1",
            "reason": "Customer needs the larger size",
        },
        "exchange-f07",
    )
    replacement = record_by_id(
        session, Commitment, receipt["replacement_commitment_id"]
    )
    reserve(session, tenant, replacement.id)
    sent = record_movement(
        session,
        tenant,
        "shipment",
        larger.id,
        1,
        from_location_id=business.location.id,
        commitment_id=replacement.id,
        occurred_at=AS_OF - timedelta(days=9),
    )

    assert replacement.status == "fulfilled"
    assert (replacement.to_party_id, replacement.amount) == (
        business.customer.id,
        Decimal(0),
    )
    assert stock_at(session, tenant, business.item.id, business.location.id) == (
        Decimal(10)
    )
    assert stock_at(session, tenant, larger.id, business.location.id) == Decimal(4)
    # No money moved: the invoice stays paid, nothing was credited or refunded.
    assert open_invoice_amount(session, tenant, invoice_id) == Decimal(0)
    assert account_balance(session, tenant, "cash") == cash_before
    assert account_balance(session, tenant, "accounts_receivable") == Decimal(0)
    assert {
        (row.class_id, row.record_id)
        for row in operational_exceptions(session, tenant, as_of=AS_OF)
        if row.class_id in WATCHED | {"exchange_without_return"}
    } == set()
    # Neither movement overwrote the other (spec 246 US7), and each explains the other.
    assert fulfilled_quantity(session, tenant, commitment.id) == Decimal(1)
    assert ("customer_exchange", receipt["exchange_id"]) in {
        (link["kind"], link["id"])
        for link in movement_explanation(session, tenant, sent.id)["links"]
    }


# --- Spec 314: an unannounced return and a refund ahead of the goods (F04, F08) ----


def _findings_at(session, business, as_of, record_ids):
    return {
        (row.class_id, row.record_id)
        for row in operational_exceptions(session, business.tenant.id, as_of=as_of)
        if row.record_id in record_ids
    }


def _returns_of(session, business):
    from sqlalchemy import select

    from reality.db.core import Movement

    return set(
        session.scalars(
            select(Movement.id).where(
                Movement.tenant_id == business.tenant.id, Movement.type == "return"
            )
        )
    )


def test_an_unannounced_return_is_linked_to_its_delivery_later(session, business):
    """F04: a parcel without paperwork is taken in, reported, and linked by a person."""
    tenant = business.tenant.id
    opening_stock(session, business, 10)
    commitment, order_line_id = _sales_order(session, business, "SO-F04", "2", "49.95")
    _deliver(session, business, commitment, 2, days_ago=20)
    invoice_id, invoice_line_id = _invoice(
        session, business, "RE-F04", order_line_id, "2", "49.95"
    )

    # A parcel arrives with no announcement and no order number on it.
    arrived_at = AS_OF - timedelta(days=5)
    parcel = record_movement(
        session,
        tenant,
        "return",
        business.item.id,
        2,
        to_location_id=business.location.id,
        occurred_at=arrived_at,
    )
    assert stock_at(session, tenant, business.item.id, business.location.id) == 10
    assert movement_explanation(session, tenant, parcel.id)["kind"] == "unexplained"
    watched = {order_line_id, parcel.id}
    assert _signals(session, business, watched) == {("unexplained_movement", parcel.id)}

    # The warehouse finds the packing slip: the parcel is the delivery of SO-F04.
    before = _returns_of(session, business)
    _reviewed(
        session,
        business,
        "movement_correct",
        {
            "movement_id": parcel.id,
            "reason": "Packing slip names SO-F04",
            "replacement": {
                "type": "return",
                "item_id": business.item.id,
                "quantity": "2",
                "to_location_id": business.location.id,
                "commitment_id": commitment.id,
                "occurred_at": arrived_at.isoformat(),
            },
        },
        "link-f04",
    )
    (linked,) = _returns_of(session, business) - before
    watched |= {linked}

    # Linked, what is owed back is visible: two back without a credit.
    assert stock_at(session, tenant, business.item.id, business.location.id) == 10
    assert _signals(session, business, watched) == {
        ("returned_not_credited", order_line_id)
    }

    _reviewed(
        session,
        business,
        "sales_credit_record",
        {
            "invoice_id": invoice_id,
            "lines": [
                {
                    "invoice_line_id": invoice_line_id,
                    "quantity": "2",
                    "gross_amount": "99.90",
                }
            ],
            "gross_amount": "99.90",
            "number": "GS-F04",
            "reason": "Return of SO-F04",
            # The invoice is still open, so the credit settles it.
            "allocation_amount": "99.90",
        },
        "credit-f04",
    )
    assert _signals(session, business, watched) == set()
    assert open_invoice_amount(session, tenant, invoice_id) == 0


def test_a_goodwill_refund_is_paid_while_the_return_is_still_expected(
    session, business
):
    """F08: credit and refund go out first; the announced return stays expected."""
    tenant = business.tenant.id
    opening_stock(session, business, 10)
    commitment, order_line_id = _sales_order(session, business, "SO-F08", "2", "49.95")
    _deliver(session, business, commitment, 2, days_ago=20)
    invoice_id, _ = _invoice(session, business, "RE-F08", order_line_id, "2", "49.95")
    _reviewed(
        session,
        business,
        "customer_payment_post",
        {"invoice_id": invoice_id, "amount": "99.90"},
        "pay-f08",
    )
    announcement = announce_customer_return(
        session,
        tenant,
        commitment.id,
        "2",
        reference="RMA-F08",
        reason="Goodwill: wrong colour",
        announced_at=AS_OF - timedelta(days=1),
        expected_by=AS_OF + timedelta(days=5),
    )

    # Goodwill: the customer is credited and refunded before anything is back.
    credit = _tool(
        session,
        business,
        "document_create",
        {
            "document_type": "credit_note",
            "number": "GS-F08",
            "party_id": business.customer.id,
            "gross_amount": "99.90",
            "document_date": "2026-08-31",
            "lines": [
                {
                    "item_id": business.item.id,
                    "quantity": "2",
                    "unit": "pcs",
                    "unit_price": "49.95",
                    "gross_amount": "99.90",
                    "billed_document_line_id": order_line_id,
                }
            ],
        },
    )["document_id"]
    _tool(session, business, "credit_note_post", {"credit_note_id": credit})
    # Positive control for the refund: the posted credit is owed to the customer.
    assert open_invoice_amount(session, tenant, credit) == Decimal("99.90")
    _reviewed(
        session,
        business,
        "customer_refund_post",
        {"credit_note_id": credit, "amount": "99.90"},
        "refund-f08",
    )
    assert open_invoice_amount(session, tenant, credit) == 0

    watched = {order_line_id, announcement.id}
    # Paid out, still expected, and not yet late: nothing to do.
    assert announcement_outstanding(session, tenant, announcement) == 2
    assert _findings_at(session, business, AS_OF, watched) == set()
    # Past its date the expected return is reported.
    late = AS_OF + timedelta(days=10)
    assert _findings_at(session, business, late, watched) == {
        ("announced_return_not_arrived", announcement.id)
    }

    def arrive(quantity, days):
        record_movement(
            session,
            tenant,
            "return",
            business.item.id,
            quantity,
            to_location_id=business.location.id,
            commitment_id=commitment.id,
            return_announcement_id=announcement.id,
            occurred_at=AS_OF + timedelta(days=days),
        )

    # One unit arrives: the credit now exceeds what came back.
    arrive(1, 11)
    assert (
        "credited_not_returned",
        order_line_id,
    ) in _findings_at(session, business, AS_OF + timedelta(days=12), watched)

    # The second unit fulfils the announcement and nothing is left.
    arrive(1, 12)
    assert announcement_outstanding(session, tenant, announcement) == 0
    assert _findings_at(session, business, AS_OF + timedelta(days=13), watched) == set()


# --- spec 304: blocked stock -----------------------------------------------------------


def _confirmed(session, business, tool, arguments):
    from reality.tools.application import create_change_proposal

    proposal = create_change_proposal(session, business.tenant.id, tool, arguments)
    executed = approve_and_execute_proposal(
        session, business.tenant.id, proposal.id, confirmed=True
    )
    assert executed.status == "executed"
    return json.loads(executed.output)


def _active_blocks(session, business):
    from reality.services.stock_blocks import stock_blocks

    return stock_blocks(session, business.tenant.id)


def test_blocked_stock_is_not_available_until_quality_releases_it(session, business):
    """B05: is blocked stock excluded from availability?"""
    opening_stock(session, business, "20")
    _confirmed(
        session,
        business,
        "stock_block",
        {
            "item_id": business.item.id,
            "location_id": business.location.id,
            "quantity": "5",
            "reason_code": "quality",
            "note": "scratched housings",
        },
    )
    assert position(session, business, business.location)["available"] == 15

    # An order for 20 gets the 15 that are free; the 5 stay blocked.
    commitment = customer_commitment(
        session, business, business.customer, business.location, "20"
    )
    _reviewed(session, business, "reserve", {"commitment_id": commitment.id}, "b05-1")
    assert reserved_for(session, business, commitment) == 15

    # Quality releases them, saying why; they are reserved for the order.
    (block,) = _active_blocks(session, business)
    assert (block["quantity"], block["reason_code"]) == ("5", "quality")
    _confirmed(
        session,
        business,
        "stock_block_release",
        {"block_id": block["id"], "reason": "rework passed QC"},
    )
    assert _active_blocks(session, business) == []
    _reviewed(session, business, "reserve", {"commitment_id": commitment.id}, "b05-2")
    assert reserved_for(session, business, commitment) == 20
    (released,) = events_about(session, business, "stock_block.released", block["id"])
    assert json.loads(released.payload)["reason"] == "rework passed QC"


def test_damaged_goods_are_received_blocked_and_scrapped(session, business):
    """H08: damaged goods, part to quarantine."""
    _reviewed(
        session,
        business,
        "movement_create",
        {
            "movement_type": "receipt",
            "item_id": business.item.id,
            "quantity": "20",
            "to_location_id": business.location.id,
            "blocked_quantity": "5",
            "block_reason": "damage",
        },
        "h08-receipt",
    )
    assert position(session, business, business.location) == {
        "physical": Decimal(20),
        "reserved": Decimal(0),
        "available": Decimal(15),
    }

    (block,) = _active_blocks(session, business)
    _confirmed(
        session,
        business,
        "stock_block_scrap",
        {"block_id": block["id"], "reason": "crushed in transit"},
    )
    assert position(session, business, business.location)["physical"] == 15
    assert _active_blocks(session, business) == []


def test_a_receipt_awaiting_inspection_is_released_days_later(session, business):
    """H15: received but not released?"""
    _reviewed(
        session,
        business,
        "shipment_receive",
        {
            "purpose": "supplier_delivery",
            "counterparty_id": business.supplier.id,
            "tracking_number": "H15-1",
            "movements": [
                {
                    "item_id": business.item.id,
                    "to_location_id": business.location.id,
                    "quantity": "12",
                    "blocked_quantity": "12",
                    "block_reason": "inspection",
                }
            ],
        },
        "h15-receipt",
    )
    commitment = customer_commitment(
        session, business, business.customer, business.location, "12"
    )
    # Received, but nothing can be reserved while inspection holds it.
    _reviewed(session, business, "reserve", {"commitment_id": commitment.id}, "h15-1")
    assert reserved_for(session, business, commitment) == 0
    assert position(session, business, business.location)["available"] == 0

    # Days later quality releases ten and rejects two.
    (block,) = _active_blocks(session, business)
    _confirmed(
        session,
        business,
        "stock_block_release",
        {"block_id": block["id"], "quantity": "10", "reason": "inspection passed"},
    )
    # The same block still states 12 received for inspection; 2 stay open.
    (rest,) = _active_blocks(session, business)
    assert (rest["id"], rest["quantity"], rest["open_quantity"]) == (
        block["id"],
        "12",
        "2",
    )
    _reviewed(session, business, "reserve", {"commitment_id": commitment.id}, "h15-2")
    assert reserved_for(session, business, commitment) == 10


def test_an_expired_lot_is_blocked_from_its_finding_and_scrapped(session, business):
    """J05: excluded from availability, then scrapped?"""
    from datetime import date

    tenant = business.tenant.id
    item = create_item(session, tenant, "MILK-J05", "Milk", tracking_type="lot")
    lot = create_lot(session, tenant, item.id, "J05-1", expires_at=date(2020, 1, 1))
    record_movement(
        session,
        tenant,
        "opening_stock",
        item.id,
        "6",
        to_location_id=business.location.id,
        lot_id=lot.id,
    )

    def expired():
        return {
            row.record_id: row
            for row in operational_exceptions(session, tenant)
            if row.class_id == "stock_expired"
        }

    finding = expired()[lot.id]
    (where,) = finding.trace["locations"]
    _confirmed(
        session,
        business,
        "stock_block",
        {
            "item_id": item.id,
            "location_id": where["location_id"],
            "lot_id": lot.id,
            "quantity": where["quantity"],
            "reason_code": "expiry",
        },
    )
    # Blocked, the lot is no longer reported, and nothing of it is available.
    assert lot.id not in expired()
    assert position(session, business, business.location, item=item)["available"] == 0

    (block,) = _active_blocks(session, business)
    _confirmed(
        session,
        business,
        "stock_block_scrap",
        {"block_id": block["id"], "reason": "expired"},
    )
    assert position(session, business, business.location, item=item)["physical"] == 0


# --- spec 307: stock counts (J02, J03, R07) --------------------------------------------


def _count(session, business, lines, note="Count"):
    """Review a count of the business location and confirm it as a person."""
    from reality.tools.application import create_change_proposal

    proposal = create_change_proposal(
        session,
        business.tenant.id,
        "stock_count",
        {"location_id": business.location.id, "note": note, "lines": lines},
    )
    review = json.loads(proposal.output)["stock_count"]
    executed = approve_and_execute_proposal(
        session, business.tenant.id, proposal.id, confirmed=True
    )
    assert executed.status == "executed"
    return review, json.loads(executed.output)


def test_a_count_posts_its_gain_and_its_loss(session, business):
    """J02: a count finds 3 missing of one item and 1 more of another."""
    from reality.services.core import create_item, record_movement, stock_at
    from reality.services.stock_counts import stock_count_detail

    tenant = business.tenant.id
    lamp = create_item(session, tenant, "LAMP-J02", "Lamp J02")
    for item, quantity in ((business.item, "20"), (lamp, "8")):
        record_movement(
            session,
            tenant,
            "opening_stock",
            item.id,
            quantity,
            to_location_id=business.location.id,
        )

    review, output = _count(
        session,
        business,
        [
            {"item_id": business.item.id, "counted_quantity": "17"},
            {"item_id": lamp.id, "counted_quantity": "9"},
        ],
        note="Month end J02",
    )

    assert [(line["book"], line["difference"]) for line in review["lines"]] == [
        ("20", "-3"),
        ("8", "1"),
    ]
    assert (
        stock_at(session, tenant, business.item.id),
        stock_at(session, tenant, lamp.id),
    ) == (17, 9)
    detail = stock_count_detail(session, tenant, output["records"][0]["id"])
    assert all(line["movement_id"] for line in detail["lines"])


def test_a_cycle_count_during_operation_keeps_the_picks_after_it(session, business):
    """J03: a bin is counted at 10:00; a pick at 10:30 stays; the count posts at 11:00."""
    from reality.services.core import record_movement, stock_at

    tenant = business.tenant.id
    counted_at = datetime.now(UTC) - timedelta(hours=1)
    record_movement(
        session,
        tenant,
        "opening_stock",
        business.item.id,
        "10",
        to_location_id=business.location.id,
        occurred_at=counted_at - timedelta(days=1),
    )
    record_movement(
        session,
        tenant,
        "adjustment",
        business.item.id,
        "2",
        from_location_id=business.location.id,
        reason="picked during the count",
        occurred_at=counted_at + timedelta(minutes=30),
    )

    review, _ = _count(
        session,
        business,
        [
            {
                "item_id": business.item.id,
                "counted_quantity": "9",
                "counted_at": counted_at.isoformat(),
            }
        ],
        note="Cycle count bin A",
    )

    assert (review["lines"][0]["book"], review["lines"][0]["difference"]) == (
        "10",
        "-1",
    )
    # The pick of 2 after the count stays; only the difference at 10:00 is posted.
    assert stock_at(session, tenant, business.item.id) == 7


def test_a_month_end_loss_uncovers_three_reservations_and_releases_none(
    session, business
):
    """R07: three reservations of 4 against 12; a count finds 9."""
    from sqlalchemy import select

    from reality.db.core import Reservation
    from reality.services.core import (
        create_commitment,
        record_movement,
        reserve,
    )
    from reality.services.exceptions import operational_exceptions

    tenant = business.tenant.id
    record_movement(
        session,
        tenant,
        "opening_stock",
        business.item.id,
        "12",
        to_location_id=business.location.id,
    )
    promises = [
        create_commitment(
            session,
            tenant,
            "customer_delivery",
            business.company.id,
            business.customer.id,
            business.item.id,
            business.location.id,
            "4",
            "2026-10-20",
        )
        for _ in range(3)
    ]
    for promise in promises:
        reserve(session, tenant, promise.id)

    def flagged():
        return {
            row.record_id
            for row in operational_exceptions(session, tenant)
            if row.class_id == "reservation_exceeds_stock"
        }

    # Positive control: before the count nothing exceeds stock.
    assert not flagged()

    review, _ = _count(
        session, business, [{"item_id": business.item.id, "counted_quantity": "9"}]
    )

    (uncovered,) = review["uncovered"]
    assert {row["commitment_id"] for row in uncovered["reservations"]} == {
        promise.id for promise in promises
    }
    assert flagged()
    # No reservation is released by the count: who waits stays a person's decision.
    assert all(
        core_reserved == 4
        for core_reserved in (
            sum(
                row.quantity
                for row in session.scalars(
                    select(Reservation).where(
                        Reservation.tenant_id == tenant,
                        Reservation.commitment_id == promise.id,
                        Reservation.status == "active",
                    )
                )
            )
            for promise in promises
        )
    )
