"""Spec 338: over-delivery, wrong items, substitutes and advised quantities."""

import json
from decimal import Decimal

import pytest

from reality.services import core
from reality.services.exceptions import operational_exceptions
from reality.services.movement_explanations import movement_explanation
from reality.services.purchase_match import purchase_match
from reality.services.receipt_deviations import accept_substitute
from reality.services.shipments import shipment_explain
from reality.tools.application import (
    approve_and_execute_proposal,
    create_change_proposal,
)


def _purchase(session, business, number, quantity="10", item=None):
    item = item or business.item
    _, document, _, (promise,) = core.create_manual_order(
        session,
        business.tenant.id,
        "purchase",
        number,
        business.company.id,
        business.supplier.id,
        business.location.id,
        [
            {
                "item_id": item.id,
                "quantity": quantity,
                "unit_price": "5",
                "gross_amount": str(Decimal(quantity) * 5),
            }
        ],
        str(Decimal(quantity) * 5),
    )
    return document, promise


def _sale(session, business, number, quantity="2"):
    _, document, _, (promise,) = core.create_manual_order(
        session,
        business.tenant.id,
        "sales",
        number,
        business.company.id,
        business.customer.id,
        business.location.id,
        [
            {
                "item_id": business.item.id,
                "quantity": quantity,
                "unit_price": "10",
                "gross_amount": str(Decimal(quantity) * 10),
            }
        ],
        str(Decimal(quantity) * 10),
    )
    return document, promise


def _findings(session, business, class_id):
    return {
        row.record_id: row
        for row in operational_exceptions(session, business.tenant.id)
        if row.class_id == class_id
    }


def _act(session, business, tool, arguments):
    proposal = create_change_proposal(session, business.tenant.id, tool, arguments)
    review = json.loads(proposal.input).get("_delivery_review")
    executed = approve_and_execute_proposal(
        session,
        business.tenant.id,
        proposal.id,
        review_token=review["token"] if review else None,
        confirmed=True,
    )
    assert executed.status == "executed", executed.output
    return json.loads(executed.output)


def _refused(code, call):
    with pytest.raises((core.InvalidOperation, core.NotFound)) as refused:
        call()
    assert refused.value.code == code, refused.value.code


def _receipt(session, business, promise, quantity, **extra):
    return core.record_movement(
        session,
        business.tenant.id,
        "receipt",
        extra.pop("item_id", business.item.id),
        quantity,
        to_location_id=business.location.id,
        commitment_id=promise.id if promise is not None else None,
        **extra,
    )


# --- Over-delivery (FR-001, FR-002) ---------------------------------------


def test_a_surplus_is_refused_unless_stated_and_then_reported(session, business):
    _, promise = _purchase(session, business, "PO-338-1", "100")
    _refused(
        "movement_exceeds_commitment_open_quantity",
        lambda: _receipt(session, business, promise, "105"),
    )
    # Positive control: what was ordered is not beyond it.
    _receipt(session, business, promise, "100")
    assert promise.id not in _findings(session, business, "received_beyond_order")

    _receipt(session, business, promise, "5", beyond_order=True)

    finding = _findings(session, business, "received_beyond_order")[promise.id]
    assert finding.causal_values["surplus_quantity"] == 5
    assert finding.causal_values["received_quantity"] == 105
    session.refresh(promise)
    assert promise.status == "fulfilled"
    line = purchase_match(session, business.tenant.id, promise.document_id)["lines"][0]
    assert "received_over" in line["differences"]


def test_keeping_the_surplus_raises_the_line_to_what_arrived(session, business):
    tenant = business.tenant.id
    _, promise = _purchase(session, business, "PO-338-2", "100")
    _receipt(session, business, promise, "105", beyond_order=True)

    _refused(
        "revision_beyond_received",
        lambda: core.revise_commitment(session, tenant, promise.id, quantity="106"),
    )
    core.revise_commitment(session, tenant, promise.id, quantity="105")

    assert promise.id not in _findings(session, business, "received_beyond_order")
    session.refresh(promise)
    assert promise.status == "fulfilled"


def test_sending_the_surplus_back_clears_it(session, business):
    tenant = business.tenant.id
    _, promise = _purchase(session, business, "PO-338-3", "100")
    _receipt(session, business, promise, "110", beyond_order=True)
    assert promise.id in _findings(session, business, "received_beyond_order")

    core.record_movement(
        session,
        tenant,
        "supplier_return",
        business.item.id,
        "10",
        from_location_id=business.location.id,
        commitment_id=promise.id,
    )

    assert promise.id not in _findings(session, business, "received_beyond_order")


def test_beyond_order_is_for_purchase_receipts_only(session, business):
    _, sale = _sale(session, business, "SO-338-1", "2")
    _receipt(session, business, None, "5")
    _refused(
        "movement_beyond_order_receipt_only",
        lambda: core.record_movement(
            session,
            business.tenant.id,
            "shipment",
            business.item.id,
            "3",
            from_location_id=business.location.id,
            commitment_id=sale.id,
            beyond_order=True,
        ),
    )


# --- Wrong items (FR-003, FR-004) -----------------------------------------


def test_a_wrong_item_names_its_line_and_fulfils_nothing(session, business):
    tenant = business.tenant.id
    wrong = core.create_item(session, tenant, "BIKE-BELL", "Bike bell")
    _, promise = _purchase(session, business, "PO-338-4", "10")

    movement = _receipt(
        session,
        business,
        None,
        "10",
        item_id=wrong.id,
        meant_for_commitment_id=promise.id,
        reason="Bells in the light carton",
    )

    session.refresh(promise)
    assert promise.status == "open"
    assert core.open_quantity(session, tenant, promise.id) == 10
    assert core.stock_at(session, tenant, wrong.id, business.location.id) == 10
    finding = _findings(session, business, "misdelivery_outstanding")[promise.id]
    assert finding.causal_values["wrong_quantity"] == 10
    assert finding.causal_values["direction"] == "received"
    assert movement.id not in _findings(session, business, "unexplained_movement")
    explained = movement_explanation(session, tenant, movement.id)
    assert explained["kind"] == "misdelivery"
    assert explained["reason"] == "Bells in the light carton"
    # Positive control: the same receipt without its line is unexplained.
    other = _receipt(session, business, None, "1", item_id=wrong.id)
    assert other.id in _findings(session, business, "unexplained_movement")


def test_wrong_goods_go_back_against_the_same_line(session, business):
    tenant = business.tenant.id
    wrong = core.create_item(session, tenant, "BIKE-BELL", "Bike bell")
    _, promise = _purchase(session, business, "PO-338-5", "10")
    _receipt(
        session,
        business,
        None,
        "10",
        item_id=wrong.id,
        meant_for_commitment_id=promise.id,
    )
    back = {
        "from_location_id": business.location.id,
        "meant_for_commitment_id": promise.id,
    }
    _refused(
        "misdelivery_back_exceeds_out",
        lambda: core.record_movement(
            session, tenant, "supplier_return", wrong.id, "11", **back
        ),
    )

    core.record_movement(session, tenant, "supplier_return", wrong.id, "10", **back)

    assert promise.id not in _findings(session, business, "misdelivery_outstanding")
    session.refresh(promise)
    assert promise.status == "open"


def test_a_wrong_item_must_be_another_item_on_the_right_kind(session, business):
    tenant = business.tenant.id
    wrong = core.create_item(session, tenant, "BIKE-BELL", "Bike bell")
    _, promise = _purchase(session, business, "PO-338-6", "10")
    _refused(
        "misdelivery_same_item",
        lambda: _receipt(
            session, business, None, "1", meant_for_commitment_id=promise.id
        ),
    )
    _refused(
        "misdelivery_commitment_both",
        lambda: _receipt(
            session, business, promise, "1", meant_for_commitment_id=promise.id
        ),
    )
    _receipt(session, business, None, "3", item_id=wrong.id)
    _refused(
        "misdelivery_movement_type",
        lambda: core.record_movement(
            session,
            tenant,
            "shipment",
            wrong.id,
            "1",
            from_location_id=business.location.id,
            meant_for_commitment_id=promise.id,
        ),
    )


def test_a_picking_error_is_corrected_into_a_wrong_item(session, business):
    """D05: the customer got another item than the shipment says."""
    tenant = business.tenant.id
    wrong = core.create_item(session, tenant, "BIKE-BELL", "Bike bell")
    for item in (business.item, wrong):
        _receipt(session, business, None, "5", item_id=item.id)
    _, promise = _sale(session, business, "SO-338-2", "2")
    shipped = core.record_movement(
        session,
        tenant,
        "shipment",
        business.item.id,
        "2",
        from_location_id=business.location.id,
        commitment_id=promise.id,
    )
    session.refresh(promise)
    assert promise.status == "fulfilled"

    core.correct_movement(
        session,
        tenant,
        shipped.id,
        reason="Customer received bells instead of lights",
        replacement={
            "type": "shipment",
            "item_id": wrong.id,
            "quantity": "2",
            "from_location_id": business.location.id,
            "meant_for_commitment_id": promise.id,
        },
    )

    session.refresh(promise)
    assert promise.status == "open"
    assert core.stock_at(session, tenant, business.item.id, business.location.id) == 5
    assert core.stock_at(session, tenant, wrong.id, business.location.id) == 3
    finding = _findings(session, business, "misdelivery_outstanding")[promise.id]
    assert finding.causal_values["direction"] == "shipped"

    core.record_movement(
        session,
        tenant,
        "return",
        wrong.id,
        "2",
        to_location_id=business.location.id,
        meant_for_commitment_id=promise.id,
    )
    assert promise.id not in _findings(session, business, "misdelivery_outstanding")


# --- Substitutes (FR-005) -------------------------------------------------


def test_an_accepted_substitute_fulfils_the_line(session, business):
    tenant = business.tenant.id
    successor = core.create_item(session, tenant, "BIKE-LIGHT-2", "Bike light v2")
    _, promise = _purchase(session, business, "PO-338-7", "10")
    # Positive control: before it is accepted the successor does not match.
    _refused(
        "movement_commitment_mismatch",
        lambda: _receipt(session, business, promise, "10", item_id=successor.id),
    )

    accept_substitute(session, tenant, promise.id, successor.id, "Successor model")
    _receipt(session, business, promise, "10", item_id=successor.id)

    session.refresh(promise)
    assert promise.status == "fulfilled"
    line = purchase_match(session, tenant, promise.document_id)["lines"][0]
    assert [row["item_id"] for row in line["substitutes"]] == [successor.id]
    assert line["received"] == "10"


def test_a_substitute_that_arrived_as_a_wrong_item_is_moved_onto_the_line(
    session, business
):
    tenant = business.tenant.id
    successor = core.create_item(session, tenant, "BIKE-LIGHT-2", "Bike light v2")
    _, promise = _purchase(session, business, "PO-338-8", "10")
    arrived = _receipt(
        session,
        business,
        None,
        "10",
        item_id=successor.id,
        meant_for_commitment_id=promise.id,
    )
    assert promise.id in _findings(session, business, "misdelivery_outstanding")

    accept_substitute(session, tenant, promise.id, successor.id, "We keep v2")
    core.correct_movement(
        session,
        tenant,
        arrived.id,
        reason="Accepted as substitute",
        replacement={
            "type": "receipt",
            "item_id": successor.id,
            "quantity": "10",
            "to_location_id": business.location.id,
            "commitment_id": promise.id,
        },
    )

    session.refresh(promise)
    assert promise.status == "fulfilled"
    assert promise.id not in _findings(session, business, "misdelivery_outstanding")


def test_a_substitute_is_refused_where_it_cannot_stand(session, business):
    tenant = business.tenant.id
    boxed = core.create_item(session, tenant, "LIGHT-BOX", "Light box", unit="box")
    service = core.create_item(session, tenant, "FIT", "Fitting", item_type="service")
    successor = core.create_item(session, tenant, "BIKE-LIGHT-2", "Bike light v2")
    _, promise = _purchase(session, business, "PO-338-9", "10")
    _, sale = _sale(session, business, "SO-338-3", "1")
    for code, args in (
        ("substitute_same_item", (promise.id, business.item.id, "x")),
        ("substitute_unit_differs", (promise.id, boxed.id, "x")),
        ("substitute_item_not_stocked", (promise.id, service.id, "x")),
        ("substitute_purchase_only", (sale.id, boxed.id, "x")),
        ("substitute_reason_required", (promise.id, successor.id, " ")),
    ):
        _refused(code, lambda args=args: accept_substitute(session, tenant, *args))
    # Positive control: the successor is accepted once, and only once.
    accept_substitute(session, tenant, promise.id, successor.id, "Successor")
    _refused(
        "substitute_already_accepted",
        lambda: accept_substitute(session, tenant, promise.id, successor.id, "Again"),
    )


# --- Advice (FR-006) ------------------------------------------------------


def test_advised_against_received_into_the_announced_shipment(session, business):
    """H17: the advice says 100, 96 arrive."""
    _, promise = _purchase(session, business, "PO-338-10", "100")
    notice = _act(
        session,
        business,
        "shipment_notice_record",
        {
            "direction": "inbound",
            "purpose": "supplier_delivery",
            "counterparty_id": business.supplier.id,
            "tracking_number": "ASN-100",
            "advised": [{"commitment_id": promise.id, "quantity": "100"}],
        },
    )
    before = shipment_explain(session, business.tenant.id, notice["shipment_id"])
    assert before["quantities"]["announced"] == "100"
    assert before["advice"][0]["in_transit"] == "100"

    _act(
        session,
        business,
        "shipment_receive",
        {
            "purpose": "supplier_delivery",
            "counterparty_id": business.supplier.id,
            "shipment_id": notice["shipment_id"],
            "movements": [
                {
                    "commitment_id": promise.id,
                    "item_id": business.item.id,
                    "to_location_id": business.location.id,
                    "quantity": "96",
                }
            ],
        },
    )

    after = shipment_explain(session, business.tenant.id, notice["shipment_id"])
    (row,) = after["advice"]
    assert (row["advised"], row["received"], row["difference"], row["in_transit"]) == (
        "100",
        "96",
        "-4",
        "0",
    )
    assert after["observations"]["received"] is True


def test_in_transit_per_purchase_until_the_container_arrives(session, business):
    """G16: one container, several purchases."""
    tenant = business.tenant.id
    orders = [
        _purchase(session, business, f"PO-338-C{n}", quantity)
        for n, quantity in enumerate(("40", "60", "20"))
    ]
    notice = _act(
        session,
        business,
        "shipment_notice_record",
        {
            "direction": "inbound",
            "purpose": "supplier_delivery",
            "counterparty_id": business.supplier.id,
            "tracking_number": "MSCU1234567",
            "advised": [
                {"commitment_id": promise.id, "quantity": str(promise.quantity)}
                for _, promise in orders
            ],
        },
    )
    for document, promise in orders:
        line = purchase_match(session, tenant, document.id)["lines"][0]
        assert line["in_transit"] == format(promise.quantity.normalize(), "f")

    _act(
        session,
        business,
        "shipment_receive",
        {
            "purpose": "supplier_delivery",
            "counterparty_id": business.supplier.id,
            "shipment_id": notice["shipment_id"],
            "movements": [
                {
                    "commitment_id": promise.id,
                    "item_id": business.item.id,
                    "to_location_id": business.location.id,
                    "quantity": str(promise.quantity),
                }
                for _, promise in orders
            ],
        },
    )
    for document, _ in orders:
        assert (
            purchase_match(session, tenant, document.id)["lines"][0]["in_transit"]
            == "0"
        )


def test_advice_and_receiving_into_a_shipment_are_bounded(session, business):
    tenant = business.tenant.id
    _, promise = _purchase(session, business, "PO-338-11", "10")
    _, sale = _sale(session, business, "SO-338-4", "1")
    other = core.create_party(session, tenant, "Other Parts GmbH", "supplier")
    notice = {
        "direction": "inbound",
        "purpose": "supplier_delivery",
        "counterparty_id": business.supplier.id,
    }
    for code, advised in (
        (
            "advice_line_not_this_supplier",
            [{"commitment_id": sale.id, "quantity": "1"}],
        ),
        ("advice_quantity_invalid", [{"commitment_id": promise.id, "quantity": "0"}]),
        (
            "advice_line_repeated",
            [{"commitment_id": promise.id, "quantity": "1"}] * 2,
        ),
    ):
        _refused(
            code,
            lambda advised=advised: create_change_proposal(
                session,
                tenant,
                "shipment_notice_record",
                {**notice, "advised": advised},
            ),
        )
    announced = _act(
        session,
        business,
        "shipment_notice_record",
        {**notice, "advised": [{"commitment_id": promise.id, "quantity": "10"}]},
    )
    _refused(
        "shipment_receive_into_mismatch",
        lambda: create_change_proposal(
            session,
            tenant,
            "shipment_receive",
            {
                "purpose": "supplier_delivery",
                "counterparty_id": other.id,
                "shipment_id": announced["shipment_id"],
                "movements": [
                    {
                        "item_id": business.item.id,
                        "to_location_id": business.location.id,
                        "quantity": "1",
                        "reason": "sample",
                    }
                ],
            },
        ),
    )
