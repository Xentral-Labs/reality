"""Catalog scenarios for order lines, combined shipments and split dispatch."""

import json
from datetime import UTC, datetime
from decimal import Decimal

from conftest import record_by_id
from sqlalchemy import select

from reality.db.core import (
    Commitment,
    DocumentLine,
    Item,
    Movement,
    Reservation,
    Shipment,
)
from reality.services.core import (
    create_commitment,
    create_item,
    fulfilled_quantity,
    ingest_shopify_order,
    open_quantity,
    record_movement,
    reserve,
    set_master_data_active,
    stock_at,
)
from reality.services.delivery_actions import prepare_delivery_action
from reality.services.shipments import shipment_explain
from reality.tools.application import (
    approve_and_execute_proposal,
    create_change_proposal,
)


def _confirm(session, tenant_id, proposal):
    token = json.loads(proposal.input)["_delivery_review"]["token"]
    return approve_and_execute_proposal(
        session, tenant_id, proposal.id, review_token=token, confirmed=True
    )


def _order(session, business, number, lines, **extra):
    proposal = prepare_delivery_action(
        session,
        business.tenant.id,
        "order_create",
        {
            "direction": "sales",
            "number": number,
            "company_party_id": business.company.id,
            "counterparty_id": business.customer.id,
            "location_id": business.location.id,
            "currency": "EUR",
            "gross_amount": str(
                sum((Decimal(line["gross_amount"]) for line in lines), Decimal())
            ),
            "lines": lines,
            **extra,
        },
        request_id=number,
    )
    _confirm(session, business.tenant.id, proposal)
    return json.loads(proposal.output)


def _line(item_id, quantity, *, promised_at=None):
    line = {
        "item_id": item_id,
        "quantity": quantity,
        "unit_price": "10.00",
        "gross_amount": str(Decimal(quantity) * Decimal("10.00")),
    }
    if promised_at:
        line["promised_at"] = promised_at
    return line


def _dispatch(session, business, tracking_number, movements):
    proposal = create_change_proposal(
        session,
        business.tenant.id,
        "shipment_dispatch",
        {
            "purpose": "customer_delivery",
            "counterparty_id": business.customer.id,
            "carrier": "DHL",
            "tracking_number": tracking_number,
            "movements": movements,
        },
    )
    return json.loads(_confirm(session, business.tenant.id, proposal).output)


def _receive(session, business, item_id, quantity, location_id):
    record_movement(
        session,
        business.tenant.id,
        "receipt",
        item_id,
        quantity,
        to_location_id=location_id,
    )


def _package_movements(session, business, package_id):
    return list(
        session.scalars(
            select(Movement).where(
                Movement.tenant_id == business.tenant.id,
                Movement.shipment_package_id == package_id,
            )
        )
    )


def test_each_order_line_keeps_its_own_promised_date(session, business):
    """A13: is each line's promise of one order dated separately?"""
    receipt = _order(
        session,
        business,
        "SO-A13",
        [
            _line(business.item.id, "2", promised_at="2026-10-05T08:00:00Z"),
            _line(business.item.id, "3", promised_at="2026-10-20T08:00:00Z"),
            _line(business.item.id, "4"),
        ],
        requested_delivery_at="2026-10-12T08:00:00Z",
    )

    commitments = [
        record_by_id(session, Commitment, cid) for cid in receipt["commitment_ids"]
    ]
    assert [commitment.document_id for commitment in commitments] == [
        receipt["document_id"]
    ] * 3
    assert [commitment.quantity for commitment in commitments] == [
        Decimal(2),
        Decimal(3),
        Decimal(4),
    ]
    assert [commitment.due_at for commitment in commitments] == [
        datetime(2026, 10, 5, 8, tzinfo=UTC),
        datetime(2026, 10, 20, 8, tzinfo=UTC),
        # A line without its own date falls back to the order's requested date.
        datetime(2026, 10, 12, 8, tzinfo=UTC),
    ]
    lines = [
        record_by_id(session, DocumentLine, line_id)
        for line_id in receipt["document_line_ids"]
    ]
    assert [line.id for line in lines] == [
        commitment.document_line_id for commitment in commitments
    ]


def test_one_shipment_fulfils_two_orders_of_the_same_customer(session, business):
    """A20: can one shipment fulfil the commitments of two orders of one customer?"""
    _receive(session, business, business.item.id, "20", business.location.id)
    first = _order(session, business, "SO-A20-1", [_line(business.item.id, "3")])
    second = _order(session, business, "SO-A20-2", [_line(business.item.id, "5")])
    assert first["document_id"] != second["document_id"]
    first_id = first["commitment_ids"][0]
    second_id = second["commitment_ids"][0]
    reserve(session, business.tenant.id, first_id)
    reserve(session, business.tenant.id, second_id)

    receipt = _dispatch(
        session,
        business,
        "OUT-A20",
        [
            {
                "commitment_id": first_id,
                "item_id": business.item.id,
                "from_location_id": business.location.id,
                "quantity": "3",
            },
            {
                "commitment_id": second_id,
                "item_id": business.item.id,
                "from_location_id": business.location.id,
                "quantity": "5",
            },
        ],
    )

    movements = _package_movements(session, business, receipt["package_id"])
    assert {movement.commitment_id: movement.quantity for movement in movements} == {
        first_id: Decimal(3),
        second_id: Decimal(5),
    }
    assert fulfilled_quantity(session, business.tenant.id, first_id) == Decimal(3)
    assert fulfilled_quantity(session, business.tenant.id, second_id) == Decimal(5)
    assert open_quantity(session, business.tenant.id, first_id) == Decimal(0)
    assert open_quantity(session, business.tenant.id, second_id) == Decimal(0)
    detail = shipment_explain(session, business.tenant.id, receipt["shipment_id"])
    assert len(detail["packages"]) == 1
    assert Decimal(detail["quantities"]["promised"]) == Decimal(8)
    assert Decimal(detail["quantities"]["dispatched"]) == Decimal(8)
    assert (
        len(
            list(
                session.scalars(
                    select(Shipment.id).where(Shipment.tenant_id == business.tenant.id)
                )
            )
        )
        == 1
    )
    assert stock_at(
        session, business.tenant.id, business.item.id, business.location.id
    ) == Decimal(12)


def test_one_package_carries_several_commitments_of_one_customer(session, business):
    """D03: does one package fulfil several commitments, each by its own quantity?"""
    tenant_id = business.tenant.id
    pump = create_item(session, tenant_id, "BIKE-PUMP", "Bike Pump")
    _receive(session, business, business.item.id, "10", business.location.id)
    _receive(session, business, pump.id, "10", business.location.id)
    commitments = [
        create_commitment(
            session,
            tenant_id,
            "customer_delivery",
            business.company.id,
            business.customer.id,
            item_id,
            business.location.id,
            quantity,
            None,
        )
        for item_id, quantity in (
            (business.item.id, "2"),
            (pump.id, "3"),
            (business.item.id, "4"),
        )
    ]
    for commitment in commitments:
        reserve(session, tenant_id, commitment.id)

    receipt = _dispatch(
        session,
        business,
        "OUT-D03",
        [
            {
                "commitment_id": commitments[0].id,
                "item_id": business.item.id,
                "from_location_id": business.location.id,
                "quantity": "2",
            },
            {
                "commitment_id": commitments[1].id,
                "item_id": pump.id,
                "from_location_id": business.location.id,
                "quantity": "3",
            },
            {
                "commitment_id": commitments[2].id,
                "item_id": business.item.id,
                "from_location_id": business.location.id,
                # Partial: one unit of the third promise stays open.
                "quantity": "3",
            },
        ],
    )

    movements = _package_movements(session, business, receipt["package_id"])
    assert {movement.commitment_id for movement in movements} == {
        commitment.id for commitment in commitments
    }
    assert [
        fulfilled_quantity(session, tenant_id, commitment.id)
        for commitment in commitments
    ] == [Decimal(2), Decimal(3), Decimal(3)]
    assert [
        open_quantity(session, tenant_id, commitment.id) for commitment in commitments
    ] == [Decimal(0), Decimal(0), Decimal(1)]
    detail = shipment_explain(session, tenant_id, receipt["shipment_id"])
    assert len(detail["packages"]) == 1
    assert Decimal(detail["quantities"]["promised"]) == Decimal(9)
    assert Decimal(detail["quantities"]["dispatched"]) == Decimal(8)
    assert stock_at(
        session, tenant_id, business.item.id, business.location.id
    ) == Decimal(5)
    assert stock_at(session, tenant_id, pump.id, business.location.id) == Decimal(7)


def test_shopify_free_promotion_item_is_its_own_zero_price_line_and_commitment(
    session, business
):
    """L09: is a free promotion item kept as its own zero-price line and promise?"""
    tenant_id = business.tenant.id
    gift = create_item(session, tenant_id, "GIFT-BELL", "Gift Bell")
    payload = {
        "id": 5837291099,
        "order_number": 10499,
        "name": "#10499",
        "created_at": "2026-09-02T09:15:00Z",
        "currency": "EUR",
        "total_price": "98.00",
        "line_items": [
            {"id": 900001, "sku": "BIKE-LIGHT", "quantity": 2, "price": "49.00"},
            {
                "id": 900002,
                "sku": "GIFT-BELL",
                "quantity": 1,
                "price": "0.00",
                "discount_allocations": [{"title": "Free bell above EUR 50"}],
            },
        ],
    }

    source, document, lines, commitments = ingest_shopify_order(
        session,
        tenant_id,
        payload,
        business.company.id,
        business.customer.id,
        business.location.id,
    )

    assert document.gross_amount == Decimal("98.00")
    assert [(line.item_id, line.source_line_id) for line in lines] == [
        (business.item.id, "900001"),
        (gift.id, "900002"),
    ]
    assert [(line.quantity, line.unit_price, line.gross_amount) for line in lines] == [
        (Decimal(2), Decimal("49.00"), Decimal("98.00")),
        (Decimal(1), Decimal("0.00"), Decimal("0.00")),
    ]
    assert [c.document_line_id for c in commitments] == [line.id for line in lines]
    assert [(c.item_id, c.quantity, c.amount) for c in commitments] == [
        (business.item.id, Decimal(2), Decimal("98.00")),
        (gift.id, Decimal(1), Decimal("0.00")),
    ]
    assert json.loads(lines[1].payload)["discount_allocations"] == [
        {"title": "Free bell above EUR 50"}
    ]
    assert json.loads(source.payload) == payload


def test_delisted_item_still_serves_its_open_commitment(session, business):
    """O04: can an open commitment still be reserved and shipped after its item is
    set inactive?"""
    tenant_id = business.tenant.id
    _receive(session, business, business.item.id, "10", business.location.id)
    commitment = create_commitment(
        session,
        tenant_id,
        "customer_delivery",
        business.company.id,
        business.customer.id,
        business.item.id,
        business.location.id,
        "4",
        None,
    )
    set_master_data_active(session, tenant_id, Item, business.item.id, False)
    assert record_by_id(session, Item, business.item.id).is_active is False

    reserved = reserve(session, tenant_id, commitment.id)
    assert reserved.reserved == Decimal(4)
    receipt = _dispatch(
        session,
        business,
        "OUT-O04",
        [
            {
                "commitment_id": commitment.id,
                "item_id": business.item.id,
                "from_location_id": business.location.id,
                "quantity": "4",
            }
        ],
    )

    movements = _package_movements(session, business, receipt["package_id"])
    assert [(m.commitment_id, m.quantity) for m in movements] == [
        (commitment.id, Decimal(4))
    ]
    assert fulfilled_quantity(session, tenant_id, commitment.id) == Decimal(4)
    assert open_quantity(session, tenant_id, commitment.id) == Decimal(0)
    assert stock_at(
        session, tenant_id, business.item.id, business.location.id
    ) == Decimal(6)
    reservation = record_by_id(session, Reservation, reserved.reservation.id)
    assert reservation.status == "consumed"
