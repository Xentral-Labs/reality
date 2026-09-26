"""Catalog scenarios B04, F03, J08 and L01: stock that moves between promises and places.

Each test drives the same services the CLI and tools call and answers one
catalog question with exact quantities.
"""

import json
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from reality.services.core import (
    InvalidOperation,
    active_reserved,
    announce_customer_return,
    announcement_outstanding,
    arrived_against_announcement,
    business_events,
    create_commitment,
    create_item,
    create_location,
    create_party,
    fulfilled_quantity,
    location_detail,
    open_quantity,
    record_movement,
    release_reservation,
    reservation_register,
    reserve,
    return_announcements,
    stock_at,
)
from reality.services.exceptions import operational_exceptions
from reality.services.movement_explanations import movement_explanation
from reality.services.read_contracts import location_inventory_rows

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
