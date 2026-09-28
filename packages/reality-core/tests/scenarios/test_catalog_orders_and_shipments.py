"""Catalog scenarios for order lines, order changes, combined shipments and split dispatch."""

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
    account_balance,
    active_reserved,
    commitment_quantity,
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
from reality.services.exceptions import operational_exceptions
from reality.services.shipments import shipment_explain
from reality.tools.application import (
    approve_and_execute_proposal,
    confirm_tool,
    create_change_proposal,
    propose_tool,
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


# --- Order changes: A04, A06, A07, A19 (spec 292) ------------------------------

AS_OF = datetime(2026, 12, 31, 12, tzinfo=UTC)


def _act(session, business, tool, arguments, request_id):
    proposal = prepare_delivery_action(
        session, business.tenant.id, tool, arguments, request_id=request_id
    )
    executed = _confirm(session, business.tenant.id, proposal)
    assert executed.status == "executed"
    return executed


def _ship(session, business, tracking_number, commitment_id, quantity, item_id=None):
    return _dispatch(
        session,
        business,
        tracking_number,
        [
            {
                "commitment_id": commitment_id,
                "item_id": item_id or business.item.id,
                "from_location_id": business.location.id,
                "quantity": quantity,
            }
        ],
    )


def _active_reservations(session, business, commitment_id):
    return sum(
        (
            reservation.quantity
            for reservation in session.scalars(
                select(Reservation).where(
                    Reservation.tenant_id == business.tenant.id,
                    Reservation.commitment_id == commitment_id,
                    Reservation.status == "active",
                )
            )
        ),
        Decimal(0),
    )


def _unbilled_lines(session, tenant_id):
    return {
        row.record_id
        for row in operational_exceptions(session, tenant_id, as_of=AS_OF)
        if row.class_id == "shipped_not_billed"
    }


def test_raising_the_quantity_after_a_partial_delivery_opens_only_the_rest(
    session, business
):
    """A04: after 4 of 10 went out and the customer raises to 12, 8 are open."""
    tenant_id = business.tenant.id
    _receive(session, business, business.item.id, "20", business.location.id)
    receipt = _order(session, business, "SO-A04", [_line(business.item.id, "10")])
    commitment_id = receipt["commitment_ids"][0]
    reserve(session, tenant_id, commitment_id)
    _ship(session, business, "OUT-A04-1", commitment_id, "4")

    _act(
        session,
        business,
        "commitment_revise",
        {"commitment_id": commitment_id, "quantity": "12", "note": "Customer adds 2"},
        "revise-a04",
    )

    assert commitment_quantity(session, tenant_id, commitment_id) == Decimal(12)
    assert fulfilled_quantity(session, tenant_id, commitment_id) == Decimal(4)
    assert open_quantity(session, tenant_id, commitment_id) == Decimal(8)
    # The order line keeps what the customer first stated; the revision is Reality.
    assert record_by_id(session, Commitment, commitment_id).quantity == Decimal(10)

    # The rest can be reserved and go out in full, and nothing more.
    reserve(session, tenant_id, commitment_id)
    assert _active_reservations(session, business, commitment_id) == Decimal(8)
    _ship(session, business, "OUT-A04-2", commitment_id, "8")
    assert open_quantity(session, tenant_id, commitment_id) == Decimal(0)
    assert record_by_id(session, Commitment, commitment_id).status == "fulfilled"
    assert stock_at(
        session, tenant_id, business.item.id, business.location.id
    ) == Decimal(8)


def test_cancelling_one_line_leaves_the_other_lines_open_and_reserved(
    session, business
):
    """A06: only the cancelled line closes and gives its reservation back."""
    tenant_id = business.tenant.id
    _receive(session, business, business.item.id, "20", business.location.id)
    receipt = _order(
        session,
        business,
        "SO-A06",
        [
            _line(business.item.id, "2"),
            _line(business.item.id, "3"),
            _line(business.item.id, "4"),
        ],
    )
    first, cancelled, third = receipt["commitment_ids"]
    for commitment_id in receipt["commitment_ids"]:
        reserve(session, tenant_id, commitment_id)

    _act(
        session,
        business,
        "commitment_cancel",
        {"commitment_id": cancelled, "reason": "Customer no longer needs it"},
        "cancel-a06",
    )

    statuses = {
        commitment_id: record_by_id(session, Commitment, commitment_id).status
        for commitment_id in receipt["commitment_ids"]
    }
    assert statuses == {first: "open", cancelled: "cancelled", third: "open"}
    assert _active_reservations(session, business, cancelled) == Decimal(0)
    assert _active_reservations(session, business, first) == Decimal(2)
    assert _active_reservations(session, business, third) == Decimal(4)
    assert open_quantity(session, tenant_id, first) == Decimal(2)
    assert open_quantity(session, tenant_id, third) == Decimal(4)
    assert active_reserved(session, tenant_id, business.item.id) == Decimal(6)
    assert stock_at(
        session, tenant_id, business.item.id, business.location.id
    ) == Decimal(20)


def test_cancelling_every_line_of_a_reserved_order_releases_all_its_stock(
    session, business
):
    """A07: a whole order cancelled line by line leaves no reservation behind."""
    tenant_id = business.tenant.id
    pump = create_item(session, tenant_id, "PUMP-A07", "Mini Pump")
    _receive(session, business, business.item.id, "10", business.location.id)
    _receive(session, business, pump.id, "10", business.location.id)
    receipt = _order(
        session,
        business,
        "SO-A07",
        [_line(business.item.id, "3"), _line(pump.id, "5")],
    )
    for commitment_id in receipt["commitment_ids"]:
        reserve(session, tenant_id, commitment_id)
    assert active_reserved(session, tenant_id, business.item.id) == Decimal(3)
    assert active_reserved(session, tenant_id, pump.id) == Decimal(5)

    # There is no order-level cancellation: the whole order is every line.
    for index, commitment_id in enumerate(receipt["commitment_ids"]):
        _act(
            session,
            business,
            "commitment_cancel",
            {"commitment_id": commitment_id, "reason": "Customer cancelled order"},
            f"cancel-a07-{index}",
        )

    assert {
        record_by_id(session, Commitment, commitment_id).status
        for commitment_id in receipt["commitment_ids"]
    } == {"cancelled"}
    assert active_reserved(session, tenant_id, business.item.id) == Decimal(0)
    assert active_reserved(session, tenant_id, pump.id) == Decimal(0)
    # Cancelling moves no goods: the stock was never gone, now it is free again.
    assert stock_at(
        session, tenant_id, business.item.id, business.location.id
    ) == Decimal(10)
    assert stock_at(session, tenant_id, pump.id, business.location.id) == Decimal(10)


def test_a_zero_price_line_ships_and_is_invoiced_without_revenue(session, business):
    """A19: a free line is committed, shipped and invoiced at zero next to a priced one."""
    tenant_id = business.tenant.id
    gift = create_item(session, tenant_id, "GIFT-A19", "Gift Bell")
    _receive(session, business, business.item.id, "10", business.location.id)
    _receive(session, business, gift.id, "10", business.location.id)
    free = {
        "item_id": gift.id,
        "quantity": "1",
        "unit_price": "0.00",
        "gross_amount": "0.00",
    }
    receipt = _order(session, business, "SO-A19", [_line(business.item.id, "2"), free])
    priced_id, free_id = receipt["commitment_ids"]
    priced_line_id, free_line_id = receipt["document_line_ids"]
    for commitment_id in receipt["commitment_ids"]:
        reserve(session, tenant_id, commitment_id)
    _ship(session, business, "OUT-A19-1", priced_id, "2")
    _ship(session, business, "OUT-A19-2", free_id, "1", item_id=gift.id)
    assert record_by_id(session, Commitment, free_id).status == "fulfilled"
    # Positive control: shipped and not yet invoiced, both lines are reported.
    assert {priced_line_id, free_line_id} <= _unbilled_lines(session, tenant_id)

    # Recorded and booked through the same tools the agent and the web use.
    recording = propose_tool(
        session,
        tenant_id,
        "document_create",
        {
            "document_type": "sales_invoice",
            "number": "RE-A19",
            "party_id": business.customer.id,
            "gross_amount": "20.00",
            "document_date": "2026-12-01",
            "lines": [
                {
                    "item_id": business.item.id,
                    "quantity": "2",
                    "unit": "pcs",
                    "unit_price": "10.00",
                    "gross_amount": "20.00",
                    "billed_document_line_id": priced_line_id,
                },
                {
                    "item_id": gift.id,
                    "quantity": "1",
                    "unit": "pcs",
                    "unit_price": "0.00",
                    "gross_amount": "0.00",
                    "billed_document_line_id": free_line_id,
                },
            ],
        },
    )
    invoice_id = json.loads(confirm_tool(session, tenant_id, recording.id).output)[
        "document_id"
    ]
    booking = propose_tool(
        session, tenant_id, "sales_invoice_post", {"document_id": invoice_id}
    )
    confirm_tool(session, tenant_id, booking.id)

    assert account_balance(session, tenant_id, "sales_revenue") == Decimal("-20.00")
    assert account_balance(session, tenant_id, "accounts_receivable") == Decimal(
        "20.00"
    )
    unbilled = _unbilled_lines(session, tenant_id)
    assert free_line_id not in unbilled
    assert priced_line_id not in unbilled
