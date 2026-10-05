"""Spec 334: planned outbound deliveries, picking and dispatch through them."""

import json
from decimal import Decimal

import pytest
from sqlalchemy import func, select

from reality.db.core import Movement
from reality.services import core
from reality.services.outbound_deliveries import (
    outbound_deliveries,
    outbound_delivery_detail,
    pick_outbound_delivery,
    plan_outbound_delivery,
    put_back_outbound_delivery,
    revise_outbound_delivery,
)
from reality.services.shipments import shipment_explain
from reality.tools.application import (
    approve_and_execute_proposal,
    create_change_proposal,
)

ADDRESS = {"name": "Müller GmbH", "street": "Hafenstr. 1", "city": "Hamburg"}


def _setup(session, business, quantity="10", stock="20"):
    tenant = business.tenant.id
    staging = core.create_location(session, tenant, "Packing zone")
    core.record_movement(
        session,
        tenant,
        "receipt",
        business.item.id,
        stock,
        to_location_id=business.location.id,
    )
    document = core.create_document(
        session, tenant, "sales_order", "OUTBOUND-ORDER", business.customer.id, "0"
    )
    promise = core.create_commitment(
        session,
        tenant,
        "customer_delivery",
        business.company.id,
        business.customer.id,
        business.item.id,
        business.location.id,
        quantity,
        None,
        document_id=document.id,
    )
    return staging, promise


def _stock(session, business, location_id):
    return core.stock_at(session, business.tenant.id, business.item.id, location_id)


def _reserved(session, business, location_id):
    return core.active_reserved(
        session, business.tenant.id, business.item.id, location_id
    )


def _refused(code, call):
    with pytest.raises((core.InvalidOperation, core.NotFound)) as refused:
        call()
    assert refused.value.code == code, refused.value.code


def _plan(session, business, promise, staging=None, quantity="10", **extra):
    return plan_outbound_delivery(
        session,
        business.tenant.id,
        customer_id=business.customer.id,
        lines=[{"commitment_id": promise.id, "quantity": quantity}],
        address=ADDRESS,
        staging_location_id=staging.id if staging else None,
        **extra,
    )


def _dispatch(session, business, detail, **extra):
    arguments = {**detail["dispatch"], **extra}
    proposal = create_change_proposal(
        session, business.tenant.id, "shipment_dispatch", arguments
    )
    token = json.loads(proposal.input)["_delivery_review"]["token"]
    executed = approve_and_execute_proposal(
        session, business.tenant.id, proposal.id, review_token=token, confirmed=True
    )
    return json.loads(executed.output)


def test_a_delivery_states_its_recipient_address_and_slot(session, business):
    tenant = business.tenant.id
    staging, promise = _setup(session, business)
    store = core.create_party(session, tenant, "Müller Store Bremen", "customer")
    slot = {"from": "2026-10-08T08:00:00+00:00", "until": "2026-10-08T10:00:00+00:00"}

    delivery = _plan(
        session, business, promise, staging, recipient_party_id=store.id, slot=slot
    )

    detail = outbound_delivery_detail(session, tenant, delivery.id)
    assert detail["recipient"] == "Müller Store Bremen"
    assert detail["address"] == ADDRESS
    assert detail["slot"] == slot
    assert detail["state"] == "planned"
    assert [(line["planned"], line["picked"]) for line in detail["lines"]] == [
        ("10", "0")
    ]
    assert [row["id"] for row in outbound_deliveries(session, tenant)] == [delivery.id]


def test_planned_quantities_stay_within_what_is_open(session, business):
    tenant = business.tenant.id
    _, promise = _setup(session, business)
    _plan(session, business, promise, quantity="6")
    # Positive control: the remaining four still fit on a second delivery.
    _plan(session, business, promise, quantity="4")
    _refused(
        "outbound_delivery_quantity_beyond_open",
        lambda: _plan(session, business, promise, quantity="1"),
    )
    other = core.create_party(session, tenant, "Other Customer", "customer")
    _refused(
        "outbound_delivery_promise_other_customer",
        lambda: plan_outbound_delivery(
            session,
            tenant,
            customer_id=other.id,
            lines=[{"commitment_id": promise.id, "quantity": "1"}],
        ),
    )
    _refused(
        "outbound_delivery_slot_invalid",
        lambda: plan_outbound_delivery(
            session,
            tenant,
            customer_id=business.customer.id,
            lines=[{"commitment_id": promise.id, "quantity": "1"}],
            slot={"from": "2026-10-08T10:00:00+00:00", "until": "2026-10-08T08:00:00+00:00"},
        ),
    )


def test_a_revision_keeps_every_statement(session, business):
    tenant = business.tenant.id
    _, promise = _setup(session, business)
    delivery = _plan(session, business, promise)
    moved = {"name": "Müller GmbH", "street": "Neuer Weg 7", "city": "Lübeck"}

    revise_outbound_delivery(session, tenant, delivery.id, address=moved)

    detail = outbound_delivery_detail(session, tenant, delivery.id)
    assert detail["address"] == moved
    assert [row["address"] for row in detail["statements"]] == [ADDRESS, moved]


def test_picking_moves_the_goods_and_the_reservation_to_staging(session, business):
    tenant = business.tenant.id
    staging, promise = _setup(session, business)
    core.reserve(session, tenant, promise.id)
    delivery = _plan(session, business, promise, staging)

    pick_outbound_delivery(
        session, tenant, delivery.id, [{"commitment_id": promise.id, "quantity": "6"}]
    )

    assert _stock(session, business, staging.id) == 6
    assert _reserved(session, business, staging.id) == 6
    assert _stock(session, business, business.location.id) == 14
    assert _reserved(session, business, business.location.id) == 4
    detail = outbound_delivery_detail(session, tenant, delivery.id)
    assert (detail["state"], detail["lines"][0]["picked"]) == ("picking", "6")
    assert [row["kind"] for row in detail["lines"][0]["movements"]] == ["pick"]
    # Availability stays true: ten reserved, ten more free, in both places together.
    assert _reserved(session, business, None) == 10


def test_a_pick_beyond_the_plan_is_refused_and_nothing_moves(session, business):
    tenant = business.tenant.id
    staging, promise = _setup(session, business)
    core.reserve(session, tenant, promise.id)
    delivery = _plan(session, business, promise, staging, quantity="5")
    before = session.scalar(select(func.count()).select_from(Movement))

    _refused(
        "outbound_delivery_pick_beyond_planned",
        lambda: pick_outbound_delivery(
            session,
            tenant,
            delivery.id,
            [{"commitment_id": promise.id, "quantity": "6"}],
        ),
    )

    assert session.scalar(select(func.count()).select_from(Movement)) == before
    # Positive control: the planned five can be picked.
    pick_outbound_delivery(
        session, tenant, delivery.id, [{"commitment_id": promise.id, "quantity": "5"}]
    )
    assert _stock(session, business, staging.id) == 5


def test_a_pick_needs_a_reservation_and_a_staging_location(session, business):
    tenant = business.tenant.id
    staging, promise = _setup(session, business)
    unstaged = _plan(session, business, promise, quantity="2")
    _refused(
        "outbound_delivery_staging_missing",
        lambda: pick_outbound_delivery(
            session, tenant, unstaged.id, [{"commitment_id": promise.id, "quantity": "1"}]
        ),
    )
    staged = _plan(session, business, promise, staging, quantity="2")
    _refused(
        "outbound_delivery_pick_not_reserved",
        lambda: pick_outbound_delivery(
            session, tenant, staged.id, [{"commitment_id": promise.id, "quantity": "1"}]
        ),
    )


def test_a_put_back_moves_both_back(session, business):
    tenant = business.tenant.id
    staging, promise = _setup(session, business)
    core.reserve(session, tenant, promise.id)
    delivery = _plan(session, business, promise, staging)
    pick_outbound_delivery(
        session, tenant, delivery.id, [{"commitment_id": promise.id, "quantity": "10"}]
    )

    put_back_outbound_delivery(
        session,
        tenant,
        delivery.id,
        [
            {
                "commitment_id": promise.id,
                "quantity": "3",
                "to_location_id": business.location.id,
            }
        ],
    )

    assert _stock(session, business, staging.id) == 7
    assert _reserved(session, business, staging.id) == 7
    assert _reserved(session, business, business.location.id) == 3
    _refused(
        "outbound_delivery_put_back_beyond_picked",
        lambda: put_back_outbound_delivery(
            session,
            tenant,
            delivery.id,
            [
                {
                    "commitment_id": promise.id,
                    "quantity": "8",
                    "to_location_id": business.location.id,
                }
            ],
        ),
    )


def test_a_cancelled_promise_leaves_its_goods_waiting_to_be_put_back(
    session, business
):
    tenant = business.tenant.id
    staging, promise = _setup(session, business)
    core.reserve(session, tenant, promise.id)
    delivery = _plan(session, business, promise, staging)
    pick_outbound_delivery(
        session, tenant, delivery.id, [{"commitment_id": promise.id, "quantity": "10"}]
    )

    core.cancel_commitment(session, tenant, promise.id, reason="Customer cancelled")

    line = outbound_delivery_detail(session, tenant, delivery.id)["lines"][0]
    assert (line["promise_status"], line["to_put_back"]) == ("cancelled", "10")
    assert _reserved(session, business, staging.id) == 0
    put_back_outbound_delivery(
        session,
        tenant,
        delivery.id,
        [
            {
                "commitment_id": promise.id,
                "quantity": "10",
                "to_location_id": business.location.id,
            }
        ],
    )
    assert _stock(session, business, business.location.id) == 20
    line = outbound_delivery_detail(session, tenant, delivery.id)["lines"][0]
    assert line["to_put_back"] == "0"


def test_a_dispatch_through_the_delivery_keeps_where_it_went(session, business):
    tenant = business.tenant.id
    staging, promise = _setup(session, business)
    core.reserve(session, tenant, promise.id)
    slot = {"from": "2026-10-08T08:00:00+00:00", "until": "2026-10-08T10:00:00+00:00"}
    delivery = _plan(session, business, promise, staging, slot=slot)
    pick_outbound_delivery(
        session, tenant, delivery.id, [{"commitment_id": promise.id, "quantity": "10"}]
    )
    detail = outbound_delivery_detail(session, tenant, delivery.id)

    output = _dispatch(session, business, detail)

    shipment = shipment_explain(session, tenant, output["shipment_id"])
    assert shipment["outbound_delivery_id"] == delivery.id
    assert (shipment["address"], shipment["slot"]) == (ADDRESS, slot)
    detail = outbound_delivery_detail(session, tenant, delivery.id)
    assert (detail["state"], detail["shipment_id"]) == ("shipped", output["shipment_id"])
    assert detail["lines"][0]["shipped"] == "10"
    assert _stock(session, business, staging.id) == 0
    session.refresh(promise)
    assert promise.status == "fulfilled"
    _refused(
        "outbound_delivery_shipped",
        lambda: revise_outbound_delivery(session, tenant, delivery.id, note="late"),
    )


def test_a_dispatch_that_differs_from_the_delivery_is_refused(session, business):
    tenant = business.tenant.id
    staging, promise = _setup(session, business)
    core.reserve(session, tenant, promise.id)
    delivery = _plan(session, business, promise, staging)
    pick_outbound_delivery(
        session, tenant, delivery.id, [{"commitment_id": promise.id, "quantity": "6"}]
    )
    detail = outbound_delivery_detail(session, tenant, delivery.id)
    _refused(
        "outbound_delivery_dispatch_not_picked",
        lambda: _dispatch(session, business, detail),
    )
    pick_outbound_delivery(
        session, tenant, delivery.id, [{"commitment_id": promise.id, "quantity": "4"}]
    )
    detail = outbound_delivery_detail(session, tenant, delivery.id)
    wrong = json.loads(json.dumps(detail["dispatch"]))
    wrong["movements"][0]["quantity"] = "9"
    _refused(
        "outbound_delivery_dispatch_mismatch",
        lambda: create_change_proposal(session, tenant, "shipment_dispatch", wrong),
    )
    # Positive control: what the delivery carries ships.
    assert _dispatch(session, business, detail)["shipment_id"]


def test_a_dispatch_without_a_delivery_is_unchanged(session, business):
    tenant = business.tenant.id
    _, promise = _setup(session, business, quantity="2")
    core.reserve(session, tenant, promise.id)
    output = _dispatch(
        session,
        business,
        {
            "dispatch": {
                "purpose": "customer_delivery",
                "counterparty_id": business.customer.id,
                "movements": [
                    {
                        "commitment_id": promise.id,
                        "item_id": business.item.id,
                        "from_location_id": business.location.id,
                        "quantity": "2",
                    }
                ],
            }
        },
    )
    shipment = shipment_explain(session, tenant, output["shipment_id"])
    assert (shipment["outbound_delivery_id"], shipment["address"]) == (None, {})


def test_another_company_sees_nothing(session, business):
    tenant = business.tenant.id
    _, promise = _setup(session, business)
    delivery = _plan(session, business, promise)
    other = core.create_tenant(session, "Other GmbH")

    assert outbound_deliveries(session, other.id) == []
    _refused(
        "outbound_delivery_not_found",
        lambda: outbound_delivery_detail(session, other.id, delivery.id),
    )
    assert outbound_deliveries(session, tenant)[0]["id"] == delivery.id
    assert Decimal(outbound_deliveries(session, tenant)[0]["lines"][0]["planned"]) == 10
