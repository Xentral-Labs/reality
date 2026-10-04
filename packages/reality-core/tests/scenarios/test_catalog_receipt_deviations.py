"""Receipt and shipment deviations from the catalog (H04, H05, H06, H07, H17, G16, D05; spec 338)."""

import json
from decimal import Decimal

from reality.services import core
from reality.services.delivery_actions import prepare_delivery_action
from reality.services.exceptions import operational_exceptions
from reality.tools.application import (
    approve_and_execute_proposal,
    create_change_proposal,
    run_read_tool,
)


def _order(session, business, direction, number, quantity, item=None):
    item = item or business.item
    counterparty = business.supplier if direction == "purchase" else business.customer
    gross = str(Decimal(quantity) * 10)
    _, document, _, (promise,) = core.create_manual_order(
        session,
        business.tenant.id,
        direction,
        number,
        business.company.id,
        counterparty.id,
        business.location.id,
        [
            {
                "item_id": item.id,
                "quantity": quantity,
                "unit_price": "10",
                "gross_amount": gross,
            }
        ],
        gross,
    )
    return document, promise


def _act(session, business, tool, arguments, request_id):
    """A reviewed action: prepared, then confirmed by a person."""
    proposal = prepare_delivery_action(
        session, business.tenant.id, tool, arguments, request_id=request_id
    )
    executed = approve_and_execute_proposal(
        session,
        business.tenant.id,
        proposal.id,
        review_token=json.loads(proposal.input)["_delivery_review"]["token"],
        confirmed=True,
    )
    assert executed.status == "executed", executed.output
    return json.loads(executed.output)


def _receive(session, business, request_id, movements, **extra):
    return _act(
        session,
        business,
        "shipment_receive",
        {
            "purpose": "supplier_delivery",
            "counterparty_id": business.supplier.id,
            "movements": movements,
            **extra,
        },
        request_id,
    )


def _line(promise, item_id, quantity, **extra):
    return {
        "item_id": item_id,
        "to_location_id": promise.location_id,
        "quantity": quantity,
        **(
            {"commitment_id": promise.id}
            if "meant_for_commitment_id" not in extra
            else {}
        ),
        **extra,
    }


def _findings(session, business, class_id):
    return {
        row.record_id: row
        for row in operational_exceptions(session, business.tenant.id)
        if row.class_id == class_id
    }


def _match_line(session, business, document):
    return run_read_tool(
        session, business.tenant.id, "purchase_match", {"document_id": document.id}
    )["lines"][0]


def test_an_over_delivery_is_received_and_kept(session, business):
    """H04: 100 ordered, 105 arrive; the surplus is visible until it is kept."""
    document, promise = _order(session, business, "purchase", "PO-H04", "100")

    _receive(
        session,
        business,
        "h04-receive",
        [_line(promise, business.item.id, "105", beyond_order=True)],
    )

    surplus = _findings(session, business, "received_beyond_order")[promise.id]
    assert surplus.causal_values["surplus_quantity"] == 5
    assert "received_over" in _match_line(session, business, document)["differences"]

    _act(
        session,
        business,
        "commitment_revise",
        {"commitment_id": promise.id, "quantity": "105", "note": "We keep the five"},
        "h04-keep",
    )

    assert promise.id not in _findings(session, business, "received_beyond_order")
    assert _match_line(session, business, document)["received"] == "105"


def test_an_over_delivery_goes_back_to_the_supplier(session, business):
    """H05: 100 ordered, 110 arrive; the ten go back against the purchase line."""
    _, promise = _order(session, business, "purchase", "PO-H05", "100")
    _receive(
        session,
        business,
        "h05-receive",
        [_line(promise, business.item.id, "110", beyond_order=True)],
    )
    assert promise.id in _findings(session, business, "received_beyond_order")

    returned = _act(
        session,
        business,
        "shipment_dispatch",
        {
            "purpose": "supplier_return",
            "counterparty_id": business.supplier.id,
            "movements": [
                {
                    "commitment_id": promise.id,
                    "item_id": business.item.id,
                    "from_location_id": business.location.id,
                    "quantity": "10",
                }
            ],
        },
        "h05-return",
    )

    assert promise.id not in _findings(session, business, "received_beyond_order")
    assert (
        core.movement_quantity(
            session, business.tenant.id, promise.id, "supplier_return"
        )
        == 10
    )
    assert returned["movement_ids"]


def test_a_wrong_item_is_tied_to_its_purchase_and_sent_back(session, business):
    """H06: the supplier sent bells for an order of lights."""
    tenant = business.tenant.id
    bell = reviewed_create_item(session, tenant, "BIKE-BELL", "Bike bell")
    _, promise = _order(session, business, "purchase", "PO-H06", "20")

    received = _receive(
        session,
        business,
        "h06-receive",
        [
            _line(
                promise,
                bell.id,
                "20",
                meant_for_commitment_id=promise.id,
                reason="Bells in the light cartons",
            )
        ],
    )

    wrong = _findings(session, business, "misdelivery_outstanding")[promise.id]
    assert wrong.causal_values["wrong_items"] == {bell.id: 20}
    assert core.open_quantity(session, tenant, promise.id) == 20
    unexplained = _findings(session, business, "unexplained_movement")
    assert not set(received["movement_ids"]) & set(unexplained)

    _act(
        session,
        business,
        "shipment_dispatch",
        {
            "purpose": "supplier_return",
            "counterparty_id": business.supplier.id,
            "movements": [
                {
                    "meant_for_commitment_id": promise.id,
                    "item_id": bell.id,
                    "from_location_id": business.location.id,
                    "quantity": "20",
                }
            ],
        },
        "h06-return",
    )

    assert promise.id not in _findings(session, business, "misdelivery_outstanding")
    # Positive control: the lights are still expected.
    assert core.open_quantity(session, tenant, promise.id) == 20


def test_a_successor_item_is_accepted_against_the_purchase(session, business):
    """H07: the supplier delivers the successor model; the buyer accepts it."""
    tenant = business.tenant.id
    successor = reviewed_create_item(session, tenant, "BIKE-LIGHT-2", "Bike light v2")
    document, promise = _order(session, business, "purchase", "PO-H07", "12")
    proposal = create_change_proposal(
        session,
        tenant,
        "commitment_substitute_accept",
        {
            "commitment_id": promise.id,
            "item_id": successor.id,
            "reason": "Successor of the discontinued model",
        },
    )
    preview = json.loads(proposal.output)
    assert preview["substitute"]["substitute_item"]["sku"] == "BIKE-LIGHT-2"
    approve_and_execute_proposal(session, tenant, proposal.id, confirmed=True)

    _receive(session, business, "h07-receive", [_line(promise, successor.id, "12")])

    session.refresh(promise)
    assert promise.status == "fulfilled"
    line = _match_line(session, business, document)
    # Received in full; only the supplier's invoice is still to come.
    assert line["received"] == "12"
    assert line["differences"] == ["billed_short"]
    assert [row["item_id"] for row in line["substitutes"]] == [successor.id]


def test_advised_and_received_differ_by_four(session, business):
    """H17: the advice says 100, 96 arrive."""
    _, promise = _order(session, business, "purchase", "PO-H17", "100")
    notice = _act(
        session,
        business,
        "shipment_notice_record",
        {
            "direction": "inbound",
            "purpose": "supplier_delivery",
            "counterparty_id": business.supplier.id,
            "tracking_number": "ASN-H17",
            "advised": [{"commitment_id": promise.id, "quantity": "100"}],
        },
        "h17-notice",
    )

    _receive(
        session,
        business,
        "h17-receive",
        [_line(promise, business.item.id, "96")],
        shipment_id=notice["shipment_id"],
    )

    detail = run_read_tool(
        session,
        business.tenant.id,
        "shipment_explain",
        {"shipment_id": notice["shipment_id"]},
    )
    (advice,) = detail["advice"]
    assert (advice["advised"], advice["received"], advice["difference"]) == (
        "100",
        "96",
        "-4",
    )
    # The four are not in transit: the delivery arrived short.
    assert advice["in_transit"] == "0"
    assert core.open_quantity(session, business.tenant.id, promise.id) == 4


def test_one_container_shows_in_transit_per_purchase(session, business):
    """G16: eight weeks by sea, one container, three purchases."""
    orders = [
        _order(session, business, "purchase", f"PO-G16-{n}", quantity)
        for n, quantity in enumerate(("300", "500", "200"))
    ]
    notice = _act(
        session,
        business,
        "shipment_notice_record",
        {
            "direction": "inbound",
            "purpose": "supplier_delivery",
            "counterparty_id": business.supplier.id,
            "tracking_number": "MSCU7654321",
            "advised": [
                {"commitment_id": promise.id, "quantity": str(promise.quantity)}
                for _, promise in orders
            ],
        },
        "g16-notice",
    )
    assert [
        _match_line(session, business, document)["in_transit"] for document, _ in orders
    ] == ["300", "500", "200"]

    _receive(
        session,
        business,
        "g16-arrival",
        [
            _line(promise, business.item.id, str(promise.quantity))
            for _, promise in orders
        ],
        shipment_id=notice["shipment_id"],
    )

    assert [
        _match_line(session, business, document)["in_transit"] for document, _ in orders
    ] == ["0", "0", "0"]


def test_a_picking_error_found_by_the_customer(session, business):
    """D05: the customer received bells; the lights are still owed."""
    tenant = business.tenant.id
    bell = reviewed_create_item(session, tenant, "BIKE-BELL", "Bike bell")
    for item in (business.item, bell):
        core.record_movement(
            session,
            tenant,
            "receipt",
            item.id,
            "10",
            to_location_id=business.location.id,
        )
    _, promise = _order(session, business, "sales", "SO-D05", "3")
    core.reserve(session, tenant, promise.id)
    shipped = _act(
        session,
        business,
        "shipment_dispatch",
        {
            "purpose": "customer_delivery",
            "counterparty_id": business.customer.id,
            "movements": [
                {
                    "commitment_id": promise.id,
                    "item_id": business.item.id,
                    "from_location_id": business.location.id,
                    "quantity": "3",
                }
            ],
        },
        "d05-ship",
    )
    (movement_id,) = shipped["movement_ids"]

    _act(
        session,
        business,
        "movement_correct",
        {
            "movement_id": movement_id,
            "reason": "Customer received bells instead of lights",
            "replacement": {
                "type": "shipment",
                "item_id": bell.id,
                "quantity": "3",
                "from_location_id": business.location.id,
                "meant_for_commitment_id": promise.id,
            },
        },
        "d05-correct",
    )

    assert core.open_quantity(session, tenant, promise.id) == 3
    assert core.stock_at(session, tenant, business.item.id, business.location.id) == 10
    assert core.stock_at(session, tenant, bell.id, business.location.id) == 7
    wrong = _findings(session, business, "misdelivery_outstanding")[promise.id]
    assert wrong.causal_values["direction"] == "shipped"

    # The bells come back and the lights go out as promised.
    _act(
        session,
        business,
        "shipment_receive",
        {
            "purpose": "customer_return",
            "counterparty_id": business.customer.id,
            "movements": [
                {
                    "meant_for_commitment_id": promise.id,
                    "item_id": bell.id,
                    "to_location_id": business.location.id,
                    "quantity": "3",
                }
            ],
        },
        "d05-bells-back",
    )
    assert promise.id not in _findings(session, business, "misdelivery_outstanding")
    core.reserve(session, tenant, promise.id)
    _act(
        session,
        business,
        "shipment_dispatch",
        {
            "purpose": "customer_delivery",
            "counterparty_id": business.customer.id,
            "movements": [
                {
                    "commitment_id": promise.id,
                    "item_id": business.item.id,
                    "from_location_id": business.location.id,
                    "quantity": "3",
                }
            ],
        },
        "d05-reship",
    )
    session.refresh(promise)
    assert promise.status == "fulfilled"


from intake_review_support import reviewed_create_item
