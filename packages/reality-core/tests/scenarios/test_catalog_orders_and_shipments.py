"""Catalog scenarios for order lines, order changes, combined shipments and split dispatch."""

import json
from datetime import UTC, datetime
from decimal import Decimal

from conftest import record_by_id
from sqlalchemy import select

from reality.db.core import (
    Commitment,
    Document,
    DocumentLine,
    Item,
    Movement,
    Reservation,
    Shipment,
)
from reality.services import core
from reality.services.core import (
    account_balance,
    active_reserved,
    announce_customer_return,
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
from reality.services.fulfillment_readiness import fulfillment_readiness
from reality.services.movement_explanations import movement_explanation
from reality.services.reference_workspace import prepare_reference, reference_detail
from reality.services.shipments import shipment_explain
from reality.services.supply_assignments import supply_coverage
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


# --- Spec 294: sales and master data (D16, L06, O01) ---------------------------


def _replacement_shipment(session, business, commitment_id):
    return session.scalars(
        select(Movement).where(
            Movement.tenant_id == business.tenant.id,
            Movement.commitment_id == commitment_id,
            Movement.type == "shipment",
        )
    ).one()


def test_a_free_replacement_ships_without_an_order_and_explains_itself(
    session, business
):
    """D16: a replacement for a faulty unit leaves on its own promise, not a new order."""
    tenant = business.tenant.id
    _receive(session, business, business.item.id, "10", business.location.id)
    receipt = _order(session, business, "SO-D16", [_line(business.item.id, "2")])
    delivered_id = receipt["commitment_ids"][0]
    reserve(session, tenant, delivered_id)
    _ship(session, business, "OUT-D16-1", delivered_id, "2")
    announcement = announce_customer_return(
        session, tenant, delivered_id, 1, reference="RMA-D16", reason="Faulty unit"
    )

    exchanged = json.loads(
        _act(
            session,
            business,
            "customer_exchange_record",
            {
                "return_announcement_id": announcement.id,
                "quantity": "1",
                "replacement_item_id": business.item.id,
                "replacement_quantity": "1",
                "reason": "Faulty unit replaced free of charge",
            },
            "exchange-d16",
        ).output
    )
    replacement_id = exchanged["replacement_commitment_id"]
    replacement = record_by_id(session, Commitment, replacement_id)
    assert (replacement.document_id, replacement.amount) == (None, Decimal(0))
    reserve(session, tenant, replacement_id)
    _ship(session, business, "OUT-D16-2", replacement_id, "1")

    assert record_by_id(session, Commitment, replacement_id).status == "fulfilled"
    explained = movement_explanation(
        session, tenant, _replacement_shipment(session, business, replacement_id).id
    )
    assert explained["kind"] == "commitment"
    assert {("commitment", replacement_id), ("commitment", delivered_id)} <= {
        (link["kind"], link["id"]) for link in explained["links"]
    }
    # Positive control: the original order, shipped and not billed, is reported;
    # the free replacement has no order line to bill and is not.
    assert _unbilled_lines(session, tenant) == {receipt["document_line_ids"][0]}


def test_a_pre_order_shows_its_shortage_and_the_supply_that_protects_it(
    session, business
):
    """L06: nothing in stock yet, but the incoming purchase is assigned to the order."""
    tenant = business.tenant.id
    receipt = _order(
        session,
        business,
        "SO-L06",
        [_line(business.item.id, "5", promised_at="2027-01-20T08:00:00Z")],
    )
    customer_id = receipt["commitment_ids"][0]
    _, _, _, purchases = core.create_manual_order(
        session,
        tenant,
        "purchase",
        "PO-L06",
        business.company.id,
        business.supplier.id,
        business.location.id,
        [
            {
                "item_id": business.item.id,
                "quantity": "20",
                "unit_price": "4.00",
                "gross_amount": "80.00",
            }
        ],
        "80.00",
        requested_delivery_at="2027-01-10T08:00:00Z",
    )
    before = supply_coverage(session, tenant, customer_commitment_id=customer_id)
    assert Decimal(before["customer"]["protecting_supply"]) == 0

    _act(
        session,
        business,
        "supply_assign",
        {
            "supplier_commitment_id": purchases[0].id,
            "purpose": "customer_demand",
            "customer_commitment_id": customer_id,
            "quantity": "5",
        },
        "assign-l06",
    )

    readiness = fulfillment_readiness(session, tenant, customer_id)
    assert "insufficient_stock" in readiness.blocker_codes
    coverage = supply_coverage(session, tenant, customer_commitment_id=customer_id)
    assert Decimal(coverage["customer"]["protecting_supply"]) == Decimal(5)
    commitment = record_by_id(session, Commitment, customer_id)
    assert commitment.due_at == datetime(2027, 1, 20, 8, tzinfo=UTC)


def test_a_renamed_item_number_keeps_every_record_on_the_same_item(session, business):
    """O01: numbers are not identity; history stays with the item, lines keep theirs."""
    tenant = business.tenant.id
    item = business.item
    old_sku = item.sku
    _receive(session, business, item.id, "10", business.location.id)
    receipt = _order(session, business, "SO-O01", [_line(item.id, "4")])
    commitment_id = receipt["commitment_ids"][0]
    order_line_id = receipt["document_line_ids"][0]
    reserve(session, tenant, commitment_id)
    _ship(session, business, "OUT-O01", commitment_id, "2")
    invoiced = core.record_sales_invoice(
        session, tenant, order_line_id, "2", "20.00", "RE-O01"
    )
    invoice_line_id = next(
        row["id"] for row in invoiced["records"] if row["family"] == "document_line"
    )
    stock_before = stock_at(session, tenant, item.id, business.location.id)

    detail = reference_detail(session, tenant, "item", item.id)
    proposal = prepare_reference(
        session,
        tenant,
        "item",
        "update",
        {
            "id": item.id,
            "expected_revision": detail["expected_revision"],
            "sku": "BIKE-LIGHT-2027",
            "name": item.name,
            "unit": item.unit,
        },
        request_id="rename-o01",
    )
    approve_and_execute_proposal(session, tenant, proposal.id)

    session.refresh(item)
    assert item.sku == "BIKE-LIGHT-2027"
    moved = session.scalars(
        select(Movement).where(
            Movement.tenant_id == tenant, Movement.commitment_id == commitment_id
        )
    ).all()
    assert moved and {movement.item_id for movement in moved} == {item.id}
    assert record_by_id(session, Commitment, commitment_id).item_id == item.id
    assert {
        reservation.item_id
        for reservation in session.scalars(
            select(Reservation).where(
                Reservation.tenant_id == tenant,
                Reservation.commitment_id == commitment_id,
            )
        )
    } == {item.id}
    assert stock_at(session, tenant, item.id, business.location.id) == stock_before
    # The documents keep the number they stated.
    assert record_by_id(session, DocumentLine, order_line_id).sku == old_sku
    assert record_by_id(session, DocumentLine, invoice_line_id).sku == old_sku
    # And the rest ships under the new number, against the same promise.
    _ship(session, business, "OUT-O01-2", commitment_id, "2")
    assert open_quantity(session, tenant, commitment_id) == Decimal(0)


# --- B14, L02, L07 (spec 300) ---------------------------------------------------


def _shop_order(session, business, number, quantity):
    """A Shopify order as the webhook delivers it, worked through its import job."""
    _, job = core.enqueue_shopify_order(
        session,
        business.tenant.id,
        {
            "id": number,
            "name": f"#{number}",
            "currency": "EUR",
            "total_price": str(Decimal(quantity) * 10),
            "created_at": "2026-11-27T18:00:00Z",
            "updated_at": "2026-11-27T18:00:00Z",
            "line_items": [
                {"id": 1, "sku": business.item.sku, "quantity": quantity, "price": "10"}
            ],
        },
        business.company.id,
        business.customer.id,
        business.location.id,
    )
    _, order, _, commitments = core.process_import_job(
        session, business.tenant.id, job.id
    )
    return order, commitments[0]


def _marketplace_order(session, business, tmp_path, number, quantity, due_at):
    """A marketplace order from its order report, through the reviewed file import."""
    import csv

    from reality.services.artifacts import stage_artifact
    from reality.services.file_interpreters import suggested_mapping

    tenant = business.tenant.id
    report = tmp_path / f"{number}.csv"
    columns = [
        "order_id",
        "order_number",
        "line_id",
        "party_name",
        "sku",
        "quantity",
        "unit_price",
        "currency",
        "location",
        "requested_delivery_at",
    ]
    with report.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(columns)
        writer.writerow(
            [
                number,
                number,
                "1",
                business.customer.name,
                business.item.sku,
                quantity,
                "10.00",
                "EUR",
                business.location.name,
                due_at.isoformat(),
            ]
        )
    with report.open("rb") as handle:
        artifact, _ = stage_artifact(
            session, tenant, handle, filename=report.name, content_type="text/csv"
        )
    proposal = propose_tool(
        session,
        tenant,
        "source_ingest",
        {
            "artifact_id": artifact.id,
            "source_system": "amazon_marketplace",
            "source_type": "order",
            "expected_target": "sales_order",
            "column_mapping": suggested_mapping(columns, "sales_order"),
        },
    )
    job_id = json.loads(confirm_tool(session, tenant, proposal.id).output)[
        "import_job_id"
    ]
    core.process_import_job(session, tenant, job_id)
    order = session.scalars(
        select(Document).where(Document.tenant_id == tenant, Document.number == number)
    ).one()
    commitment = session.scalars(
        select(Commitment).where(
            Commitment.tenant_id == tenant, Commitment.document_id == order.id
        )
    ).one()
    return order, commitment


def _findings(session, business, class_id, *, as_of=None):
    return {
        row.record_id: row
        for row in operational_exceptions(session, business.tenant.id, as_of=as_of)
        if row.class_id == class_id
    }


def test_an_item_oversold_in_the_shop_and_on_a_marketplace_names_both(
    session, business, tmp_path, monkeypatch
):
    """B14: shop and marketplace together sell more than stock and supply."""
    monkeypatch.setenv("REALITY_ARTIFACT_DIR", str(tmp_path / "artifacts"))
    tenant = business.tenant.id
    record_movement(
        session,
        tenant,
        "opening_stock",
        business.item.id,
        "4",
        to_location_id=business.location.id,
    )
    shop, _ = _shop_order(session, business, 3001, "3")
    # Positive control: the shop alone is within stock.
    assert business.item.id not in _findings(session, business, "item_oversold")

    market, _ = _marketplace_order(
        session, business, tmp_path, "AMZ-3001", "3", core.now()
    )
    row = _findings(session, business, "item_oversold")[business.item.id]
    assert row.causal_values["shortfall_quantity"] == 2
    assert {
        channel: values["orders"] for channel, values in row.trace["channels"].items()
    } == {"amazon_marketplace": [market.id], "shopify": [shop.id]}

    # A purchase order for the two missing units is supply on its way: covered.
    core.create_manual_order(
        session,
        tenant,
        "purchase",
        "PO-B14",
        business.company.id,
        business.supplier.id,
        business.location.id,
        [
            {
                "item_id": business.item.id,
                "quantity": "2",
                "unit_price": "5.00",
                "gross_amount": "10.00",
            }
        ],
        "10.00",
    )
    assert business.item.id not in _findings(session, business, "item_oversold")


def test_a_marketplace_order_due_tomorrow_is_at_risk_until_it_ships(
    session, business, tmp_path, monkeypatch
):
    """L02: a fully reserved marketplace order a day before its deadline."""
    from datetime import timedelta

    monkeypatch.setenv("REALITY_ARTIFACT_DIR", str(tmp_path / "artifacts"))
    tenant = business.tenant.id
    now = core.now()
    record_movement(
        session,
        tenant,
        "opening_stock",
        business.item.id,
        "10",
        to_location_id=business.location.id,
    )
    _, urgent = _marketplace_order(
        session, business, tmp_path, "AMZ-L02-1", "2", now + timedelta(hours=20)
    )
    _, relaxed = _marketplace_order(
        session, business, tmp_path, "AMZ-L02-2", "2", now + timedelta(days=3)
    )
    _, late = _marketplace_order(
        session, business, tmp_path, "AMZ-L02-3", "2", now + timedelta(hours=2)
    )
    for promise in (urgent, relaxed, late):
        core.reserve(session, tenant, promise.id)

    due_soon = _findings(session, business, "outgoing_commitment_due_soon", as_of=now)
    assert set(due_soon) == {urgent.id, late.id}
    # Fully reserved, so nothing else would have spoken.
    assert due_soon[urgent.id].cause_ids == ()
    assert relaxed.id not in due_soon

    _ship(session, business, "L02-DHL", urgent.id, "2")
    assert urgent.id not in _findings(
        session, business, "outgoing_commitment_due_soon", as_of=now
    )
    # Once its date passes, the unshipped one is overdue, and only that.
    later = now + timedelta(hours=3)
    assert late.id in _findings(
        session, business, "overdue_outgoing_customer_commitment", as_of=later
    )
    assert late.id not in _findings(
        session, business, "outgoing_commitment_due_soon", as_of=later
    )


def test_a_black_friday_burst_is_interpreted_once_and_never_over_reserved(
    session, business
):
    """L07: a burst of shop orders, then reservations; the measured run is in
    specs/300-multichannel-oversell/results.md (10,000 orders in 404 s)."""
    from benchmarks.peak_intake.company import Company, payloads

    tenant = business.tenant.id
    record_movement(
        session,
        tenant,
        "opening_stock",
        business.item.id,
        "60",
        to_location_id=business.location.id,
    )
    company = Company(
        tenant,
        business.company.id,
        business.customer.id,
        business.location.id,
        (business.item.sku,),
    )
    for payload in payloads(company, orders=40, seed=7):
        core.enqueue_shopify_order(
            session,
            tenant,
            payload,
            business.company.id,
            business.customer.id,
            business.location.id,
        )
    while sum(core.process_pending_import_jobs(session, tenant, limit=25)):
        pass

    orders = session.scalars(
        select(Document).where(
            Document.tenant_id == tenant, Document.type == "sales_order"
        )
    ).all()
    assert len(orders) == 40
    assert len({order.source_record_id for order in orders}) == 40
    promises = session.scalars(
        select(Commitment).where(
            Commitment.tenant_id == tenant, Commitment.type == "customer_delivery"
        )
    ).all()
    for promise in promises:
        core.reserve(session, tenant, promise.id)
    reserved = core.active_reserved(session, tenant, business.item.id)
    stock = core.stock_at(session, tenant, business.item.id)
    assert reserved == stock == 60
    demand = sum(core.open_quantity(session, tenant, row.id) for row in promises)
    assert demand > stock
    assert (
        _findings(session, business, "item_oversold")[business.item.id].causal_values[
            "shortfall_quantity"
        ]
        == demand - stock
    )


# --- spec 303: orders served from several warehouses -----------------------------------


def _warehouse_findings(session, tenant_id):
    return {
        row.record_id: row
        for row in operational_exceptions(session, tenant_id)
        if row.class_id == "stock_in_another_location"
    }


def _from(business, commitment_id, location, quantity, item_id=None):
    return {
        "commitment_id": commitment_id,
        "item_id": item_id or business.item.id,
        "from_location_id": location.id,
        "quantity": quantity,
    }


def test_two_warehouses_ship_one_order_line_as_two_parcels(session, business):
    """D02: movements per location, one commitment?"""
    tenant = business.tenant.id
    munich = core.create_location(session, tenant, "Munich Warehouse")
    _receive(session, business, business.item.id, "6", business.location.id)
    _receive(session, business, business.item.id, "40", munich.id)
    (promise_id,) = _order(
        session, business, "SO-D02", [_line(business.item.id, "10")]
    )["commitment_ids"]

    # Home reserves its six; the finding points at Munich for the other four.
    _act(session, business, "reserve", {"commitment_id": promise_id}, "d02-home")
    where = _warehouse_findings(session, tenant)[promise_id].trace["locations"][0]
    assert (where["location_id"], where["proposed"]) == (munich.id, "4")
    _act(
        session,
        business,
        "reserve",
        {
            "commitment_id": promise_id,
            "location_id": where["location_id"],
            "quantity": where["proposed"],
        },
        "d02-munich",
    )
    assert promise_id not in _warehouse_findings(session, tenant)
    assert fulfillment_readiness(session, tenant, promise_id).ship_ready

    # Each warehouse ships its part as its own parcel against the one promise.
    home = _dispatch(
        session,
        business,
        "D02-1",
        [_from(business, promise_id, business.location, "6")],
    )
    away = _dispatch(
        session, business, "D02-2", [_from(business, promise_id, munich, "4")]
    )
    parcels = [home["package_id"], away["package_id"]]
    assert len(set(parcels)) == 2
    assert [
        [
            (m.from_location_id, m.quantity)
            for m in _package_movements(session, business, p)
        ]
        for p in parcels
    ] == [[(business.location.id, Decimal("6.0000"))], [(munich.id, Decimal("4.0000"))]]
    assert core.open_quantity(session, tenant, promise_id) == 0
    assert _active_reservations(session, business, promise_id) == 0


def test_stock_in_the_wrong_warehouse_is_transferred_and_then_reserved(
    session, business
):
    """B06: is a transfer needed, and is availability per location?"""
    tenant = business.tenant.id
    munich = core.create_location(session, tenant, "Munich Warehouse")
    _receive(session, business, business.item.id, "40", munich.id)
    (promise_id,) = _order(session, business, "SO-B06", [_line(business.item.id, "5")])[
        "commitment_ids"
    ]

    # Home reserves nothing; the stock is in Munich, and the finding says so.
    _act(session, business, "reserve", {"commitment_id": promise_id}, "b06-home")
    assert _active_reservations(session, business, promise_id) == 0
    finding = _warehouse_findings(session, tenant)[promise_id]
    assert finding.causal_values["elsewhere"] == "Munich Warehouse 40"
    where = finding.trace["locations"][0]

    # The warehouse lead moves the five home through the reviewed transfer.
    _act(
        session,
        business,
        "movement_create",
        {
            "movement_type": "transfer",
            "item_id": business.item.id,
            "quantity": where["proposed"],
            "from_location_id": where["location_id"],
            "to_location_id": finding.trace["location_id"],
        },
        "b06-transfer",
    )
    assert promise_id not in _warehouse_findings(session, tenant)
    assert core.stock_at(session, tenant, business.item.id, business.location.id) == 5

    # Then the order reserves and ships at home, as usual.
    _act(session, business, "reserve", {"commitment_id": promise_id}, "b06-reserve")
    _ship(session, business, "B06-1", promise_id, "5")
    assert core.open_quantity(session, tenant, promise_id) == 0


def test_an_order_with_many_lines_is_served_from_two_warehouses(session, business):
    """A02: what is open per line and per location?"""
    tenant = business.tenant.id
    munich = core.create_location(session, tenant, "Munich Warehouse")
    items = [business.item] + [
        core.create_item(session, tenant, f"A02-{index}", f"Part {index}")
        for index in range(1, 12)
    ]
    # Even items are stocked at home, odd ones in Munich.
    for index, item in enumerate(items):
        place = business.location if index % 2 == 0 else munich
        _receive(session, business, item.id, "3", place.id)
    promise_ids = _order(
        session, business, "SO-A02", [_line(item.id, "3") for item in items]
    )["commitment_ids"]
    assert len(promise_ids) == 12

    for promise_id in promise_ids:
        _act(session, business, "reserve", {"commitment_id": promise_id}, promise_id)
    # Every line whose stock is in Munich is named; no line stocked at home is.
    named = _warehouse_findings(session, tenant)
    assert set(named) == set(promise_ids[1::2])
    for promise_id in promise_ids[1::2]:
        where = named[promise_id].trace["locations"][0]
        _act(
            session,
            business,
            "reserve",
            {"commitment_id": promise_id, "location_id": where["location_id"]},
            f"{promise_id}-m",
        )
    assert _warehouse_findings(session, tenant) == {}
    assert all(
        fulfillment_readiness(session, tenant, promise_id).ship_ready
        for promise_id in promise_ids
    )

    # Each warehouse ships its own lines in one parcel.
    for tracking, place, ids in (
        ("A02-H", business.location, promise_ids[0::2]),
        ("A02-M", munich, promise_ids[1::2]),
    ):
        _dispatch(
            session,
            business,
            tracking,
            [
                _from(business, promise_id, place, "3", item_id=item.id)
                for promise_id, item in zip(
                    ids, items[0::2] if place is business.location else items[1::2]
                )
            ],
        )
    assert all(core.open_quantity(session, tenant, pid) == 0 for pid in promise_ids)


# --- Spec 306: ship complete (B10) and no backorders (M06) ---------------------------


def _state_rule(session, business, rule, reason, **subject):
    proposal = create_change_proposal(
        session,
        business.tenant.id,
        "delivery_rule_set",
        {**subject, "rule": rule, "reason": reason},
    )
    executed = approve_and_execute_proposal(
        session, business.tenant.id, proposal.id, confirmed=True
    )
    assert executed.status == "executed"


def _rule_findings(session, business, class_id):
    return {
        row.record_id: row
        for row in operational_exceptions(session, business.tenant.id)
        if row.class_id == class_id
    }


def test_a_customer_who_refuses_partial_delivery_gets_the_whole_order_at_once(
    session, business
):
    """B10: reserved goods wait, the reason is named, and the whole order ships together."""
    tenant = business.tenant.id
    lamp = core.create_item(session, tenant, "LAMP-B10", "Lamp B10")
    _receive(session, business, business.item.id, "5", business.location.id)
    _receive(session, business, lamp.id, "1", business.location.id)
    order = _order(
        session,
        business,
        "SO-B10",
        [_line(business.item.id, "5"), _line(lamp.id, "3")],
    )
    bikes, lamps = order["commitment_ids"]
    for commitment_id in (bikes, lamps):
        reserve(session, tenant, commitment_id)
    # Positive control: without a rule the bikes alone ship.
    assert fulfillment_readiness(session, tenant, bikes).ship_ready

    _state_rule(
        session,
        business,
        "ship_complete",
        "Customer accepts complete deliveries only",
        party_id=business.customer.id,
    )

    readiness = fulfillment_readiness(session, tenant, bikes)
    assert "ship_complete_incomplete" in readiness.blocker_codes
    waiting = _rule_findings(session, business, "order_waiting_for_completeness")
    assert waiting[order["document_id"]].trace["waiting_commitment_ids"] == [lamps]
    try:
        _ship(session, business, "TRK-B10-1", bikes, "5")
    except core.InvalidOperation as error:
        assert error.code == "shipment_ship_complete_partial"
    else:
        raise AssertionError("a partial shipment left for a ship-complete customer")

    _receive(session, business, lamp.id, "2", business.location.id)
    reserve(session, tenant, lamps)
    _dispatch(
        session,
        business,
        "TRK-B10-2",
        [
            {
                "commitment_id": bikes,
                "item_id": business.item.id,
                "from_location_id": business.location.id,
                "quantity": "5",
            },
            {
                "commitment_id": lamps,
                "item_id": lamp.id,
                "from_location_id": business.location.id,
                "quantity": "3",
            },
        ],
    )
    assert open_quantity(session, tenant, bikes) == 0
    assert open_quantity(session, tenant, lamps) == 0
    assert order["document_id"] not in _rule_findings(
        session, business, "order_waiting_for_completeness"
    )


def test_a_customer_who_wants_no_backorders_has_the_rest_cancelled(session, business):
    """M06: after a partial shipment the rest is reported and cancelled with the rule."""
    tenant = business.tenant.id
    _state_rule(
        session,
        business,
        "no_backorders",
        "Customer reorders instead of waiting",
        party_id=business.customer.id,
    )
    _receive(session, business, business.item.id, "6", business.location.id)
    order = _order(session, business, "SO-M06", [_line(business.item.id, "10")])
    (bikes,) = order["commitment_ids"]
    reserve(session, tenant, bikes)
    # Positive control: nothing shipped, nothing is a backorder yet.
    assert bikes not in _rule_findings(session, business, "backorder_against_rule")

    _ship(session, business, "TRK-M06", bikes, "6")

    finding = _rule_findings(session, business, "backorder_against_rule")[bikes]
    assert finding.causal_values["open_quantity"] == 4
    assert finding.trace["reason"] == "Customer reorders instead of waiting"
    _act(
        session,
        business,
        "commitment_cancel",
        {
            "commitment_id": bikes,
            "reason": "No backorders by the customer's rule",
        },
        "m06-cancel",
    )
    assert record_by_id(session, Commitment, bikes).status == "cancelled"
    assert bikes not in _rule_findings(session, business, "backorder_against_rule")


def _customer_number(session, business, number, item_id, name):
    proposal = create_change_proposal(
        session,
        business.tenant.id,
        "customer_item_number_set",
        {
            "party_id": business.customer.id,
            "customer_item_number": number,
            "item_id": item_id,
            "customer_item_name": name,
        },
    )
    executed = approve_and_execute_proposal(
        session, business.tenant.id, proposal.id, confirmed=True
    )
    assert executed.status == "executed"


def _order_file(session, business, tmp_path, order_id, rows):
    import csv

    from reality.services.artifacts import stage_artifact
    from reality.services.file_interpreters import suggested_mapping

    columns = ["order_id", "line_id", "party_name", "customer_item_number"]
    columns += ["name", "quantity", "unit_price", "currency", "location"]
    path = tmp_path / f"{order_id}.csv"
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(columns)
        for index, (number, quantity) in enumerate(rows, start=1):
            writer.writerow(
                [order_id, index, business.customer.name, number, number]
                + [quantity, "10", "EUR", business.location.name]
            )
    with path.open("rb") as handle:
        artifact, _ = stage_artifact(
            session,
            business.tenant.id,
            handle,
            filename=path.name,
            content_type="text/csv",
        )
    proposal = propose_tool(
        session,
        business.tenant.id,
        "source_ingest",
        {
            "artifact_id": artifact.id,
            "source_system": "edi_customer",
            "source_type": "order",
            "expected_target": "sales_order",
            "column_mapping": suggested_mapping(columns, "sales_order"),
        },
    )
    output = json.loads(confirm_tool(session, business.tenant.id, proposal.id).output)
    core.process_import_job(session, business.tenant.id, output["import_job_id"])


def _unknown_lines(session, business):
    return {
        row.trace.get("customer_item_number"): row.record_id
        for row in operational_exceptions(session, business.tenant.id, as_of=AS_OF)
        if row.class_id == "order_line_item_unknown"
    }


def test_a_customer_orders_by_its_own_item_numbers(
    session, business, tmp_path, monkeypatch
):
    """M02: the customer's numbers name our items, by hand, by file and once assigned."""
    monkeypatch.setenv("REALITY_ARTIFACT_DIR", str(tmp_path / "artifacts"))
    tenant = business.tenant.id
    lamp = core.create_item(session, tenant, "LAMP-M02", "Lamp M02")
    _customer_number(session, business, "K-4711", business.item.id, "Laufrad 28 Zoll")

    # By hand: the clerk types the customer's number and gets our item.
    order = _order(
        session,
        business,
        "SO-M02",
        [
            {
                **_line(business.item.id, "2"),
                "item_id": "",
                "customer_item_number": "k-4711",
            }
        ],
    )
    (wheels,) = order["commitment_ids"]
    assert record_by_id(session, Commitment, wheels).item_id == business.item.id

    # By file: the known number is promised, the unknown one waits for a person.
    _order_file(
        session, business, tmp_path, "EDI-M02", [("K-4711", "3"), ("K-55", "1")]
    )
    pending = _unknown_lines(session, business)
    assert list(pending) == ["K-55"]
    _act(
        session,
        business,
        "order_line_item_assign",
        {
            "document_line_id": pending["K-55"],
            "item_id": lamp.id,
            "remember_for_customer": True,
        },
        "m02-assign",
    )
    assert _unknown_lines(session, business) == {}

    # The next order by the same number needs nobody.
    _order_file(session, business, tmp_path, "EDI-M02B", [("K-55", "4")])
    assert _unknown_lines(session, business) == {}
    later = session.scalar(
        select(Commitment)
        .join(Document, Document.id == Commitment.document_id)
        .where(Commitment.tenant_id == tenant, Document.number == "EDI-M02B")
    )
    assert later.item_id == lamp.id


def test_a_customer_lowers_a_line_below_what_already_shipped(session, business):
    """A05: the revision stands, the excess is reported until it is settled."""
    tenant = business.tenant.id
    _receive(session, business, business.item.id, "10", business.location.id)
    order = _order(session, business, "SO-A05", [_line(business.item.id, "10")])
    (promise,) = order["commitment_ids"]
    reserve(session, tenant, promise)
    _ship(session, business, "TRK-A05", promise, "6")

    _act(
        session,
        business,
        "commitment_revise",
        {"commitment_id": promise, "quantity": "4", "note": "Customer needs only 4"},
        "a05-lower",
    )

    finding = {
        row.record_id: row
        for row in operational_exceptions(session, tenant, as_of=AS_OF)
        if row.class_id == "shipped_beyond_order"
    }[promise]
    assert finding.causal_values["excess_quantity"] == 2
    assert record_by_id(session, Commitment, promise).status == "fulfilled"

    # The customer keeps the two after all: the line is raised to what shipped.
    _act(
        session,
        business,
        "commitment_revise",
        {"commitment_id": promise, "quantity": "6", "note": "Customer keeps 6"},
        "a05-keep",
    )
    assert promise not in {
        row.record_id
        for row in operational_exceptions(session, tenant, as_of=AS_OF)
        if row.class_id == "shipped_beyond_order"
    }


def _dispatch_as(session, business, promise, quantity, **extra):
    proposal = create_change_proposal(
        session,
        business.tenant.id,
        "shipment_dispatch",
        {
            "purpose": "customer_delivery",
            "counterparty_id": business.customer.id,
            "movements": [
                {
                    "commitment_id": promise,
                    "item_id": business.item.id,
                    "from_location_id": business.location.id,
                    "quantity": quantity,
                }
            ],
            **extra,
        },
    )
    return json.loads(_confirm(session, business.tenant.id, proposal).output)


def test_a_customer_collects_the_order_at_the_counter(session, business):
    """D15: a pickup is a delivery of its own kind, with who collected."""
    from reality.services.shipments import shipment_explain

    tenant = business.tenant.id
    _receive(session, business, business.item.id, "3", business.location.id)
    order = _order(session, business, "SO-D15", [_line(business.item.id, "3")])
    (promise,) = order["commitment_ids"]
    reserve(session, tenant, promise)

    shipped = _dispatch_as(
        session,
        business,
        promise,
        "3",
        delivery_mode="pickup",
        collected_by="Frau Weber",
    )

    detail = shipment_explain(session, tenant, shipped["shipment_id"])
    assert (detail["delivery_mode"], detail["collected_by"]) == ("pickup", "Frau Weber")
    assert record_by_id(session, Commitment, promise).status == "fulfilled"


def test_a_3pl_confirms_on_thursday_what_left_on_monday(session, business):
    """D12: the movements carry Monday, the shipment shows when Reality was told."""
    from datetime import timedelta

    from reality.services.shipments import shipment_explain

    tenant = business.tenant.id
    monday = core.now() - timedelta(days=3)
    # The goods were in the warehouse before Monday.
    record_movement(
        session,
        tenant,
        "receipt",
        business.item.id,
        "5",
        to_location_id=business.location.id,
        occurred_at=monday - timedelta(days=7),
    )
    order = _order(
        session,
        business,
        "SO-D12",
        [
            _line(
                business.item.id,
                "5",
                promised_at=(monday + timedelta(hours=1)).isoformat(),
            )
        ],
    )
    (promise,) = order["commitment_ids"]
    reserve(session, tenant, promise)
    overdue = {
        row.record_id
        for row in operational_exceptions(session, tenant, as_of=core.now())
        if row.class_id == "overdue_outgoing_customer_commitment"
    }
    assert promise in overdue

    shipped = _dispatch_as(
        session,
        business,
        promise,
        "5",
        carrier="3PL Nord",
        tracking_number="3PL-D12",
        occurred_at=monday.isoformat(),
    )

    movement = record_by_id(session, Movement, shipped["movement_ids"][0])
    assert core.utc_datetime(movement.occurred_at) == monday
    detail = shipment_explain(session, tenant, shipped["shipment_id"])
    assert detail["moved_at"] == monday
    assert detail["confirmation_lag_seconds"] >= 3 * 24 * 3600 - 60
    assert promise not in {
        row.record_id
        for row in operational_exceptions(session, tenant, as_of=core.now())
        if row.class_id == "overdue_outgoing_customer_commitment"
    }
