"""Company receipt/release stories through the canonical reviewed tools."""

import json
from decimal import Decimal

import pytest
from sqlalchemy import func, select
from unified_fixtures import delivery_fixture

from reality.db.core import BusinessEvent
from reality.services.core import (
    InvalidOperation,
    NotFound,
    active_reserved,
    create_commitment,
    record_movement,
    release_reservation,
    reserve,
    stock_at,
)
from reality.services.delivery_actions import (
    delivery_proposal_detail,
    prepare_delivery_action,
    reconcile_delivery,
)
from reality.services.delivery_reads import delivery_case
from reality.tools.application import (
    approve_and_execute_proposal,
    create_change_proposal,
)


def incoming(session, business):
    return create_commitment(
        session,
        business.tenant.id,
        "supplier_delivery",
        business.customer.id,
        business.company.id,
        business.item.id,
        business.location.id,
        "8",
        None,
    )


def confirm(session, tid, proposal):
    return approve_and_execute_proposal(
        session,
        tid,
        proposal.id,
        review_token=json.loads(proposal.input)["_delivery_review"]["token"],
        confirmed=True,
    )


def receipt_args(business, commitment, quantity="3"):
    return {
        "movement_type": "receipt",
        "commitment_id": commitment.id,
        "item_id": business.item.id,
        "to_location_id": business.location.id,
        "quantity": quantity,
    }


def test_partial_receipt_review_replay_and_trace(session, business):
    tid = business.tenant.id
    commitment = incoming(session, business)
    args = receipt_args(business, commitment)
    proposal = prepare_delivery_action(
        session, tid, "movement_create", args, request_id="receipt"
    )
    assert stock_at(session, tid, business.item.id, business.location.id) == 0
    review = json.loads(proposal.input)["_delivery_review"]
    assert review["effect"] == {"received": "3"}
    assert review["state"]["case"]["party_id"] == business.customer.id
    assert (
        prepare_delivery_action(
            session, tid, "movement_create", args, request_id="receipt"
        ).id
        == proposal.id
    )
    confirm(session, tid, proposal)
    confirm(session, tid, proposal)
    assert stock_at(session, tid, business.item.id, business.location.id) == 3
    assert Decimal(delivery_case(session, tid, commitment.id)["case"]["open"]) == 5
    assert (
        delivery_proposal_detail(session, tid, proposal.id)["verification"]
        == "verified"
    )
    with pytest.raises(InvalidOperation):
        prepare_delivery_action(
            session,
            tid,
            "movement_create",
            receipt_args(business, commitment, "9"),
            request_id="excess",
        )


def test_full_release_preserves_physical_and_commitment_and_replays(session, business):
    fixture = delivery_fixture(session, business)
    tid = business.tenant.id
    reservation = reserve(session, tid, fixture.commitment.id, "6")
    args = {"reservation_id": reservation.reservation.id}
    proposal = prepare_delivery_action(
        session, tid, "reservation_release", args, request_id="release"
    )
    assert active_reserved(session, tid, business.item.id, business.location.id) == 6
    assert json.loads(proposal.input)["_delivery_review"]["effect"] == {"released": "6"}
    confirm(session, tid, proposal)
    confirm(session, tid, proposal)
    assert stock_at(session, tid, business.item.id, business.location.id) == 20
    assert active_reserved(session, tid, business.item.id, business.location.id) == 0
    assert (
        Decimal(delivery_case(session, tid, fixture.commitment.id)["case"]["open"])
        == 12
    )
    assert (
        delivery_proposal_detail(session, tid, proposal.id)["verification"]
        == "verified"
    )
    assert (
        session.scalar(
            select(func.count())
            .select_from(BusinessEvent)
            .where(
                BusinessEvent.tenant_id == tid, BusinessEvent.action_id == proposal.id
            )
        )
        == 1
    )
    with pytest.raises(InvalidOperation):
        prepare_delivery_action(
            session, tid, "reservation_release", args, request_id="inactive"
        )


def test_release_stale_and_foreign_reviews_do_not_execute(session, business):
    fixture = delivery_fixture(session, business)
    tid = business.tenant.id
    reservation = reserve(session, tid, fixture.commitment.id, "6")
    proposal = prepare_delivery_action(
        session,
        tid,
        "reservation_release",
        {"reservation_id": reservation.reservation.id},
        request_id="stale",
    )
    release_reservation(session, tid, reservation.reservation.id)
    with pytest.raises(InvalidOperation):
        confirm(session, tid, proposal)
    assert proposal.status == "proposed"
    with pytest.raises(NotFound):
        prepare_delivery_action(
            session,
            tid,
            "reservation_release",
            {"reservation_id": "foreign"},
            request_id="foreign",
        )


@pytest.mark.parametrize("action", ["receipt", "release"])
def test_new_action_recovery_and_pool_guard(session, business, action):
    tid = business.tenant.id
    fixture = delivery_fixture(session, business)
    if action == "receipt":
        commitment = incoming(session, business)
        tool, args = "movement_create", receipt_args(business, commitment)
    else:
        reservation = reserve(session, tid, fixture.commitment.id, "6")
        tool, args = (
            "reservation_release",
            {"reservation_id": reservation.reservation.id},
        )
    proposal = prepare_delivery_action(session, tid, tool, args, request_id="recovery")
    proposal.status = "executing"
    session.commit()
    if action == "receipt":
        record_movement(session, tid, **args, action_id=proposal.id)
    else:
        release_reservation(session, tid, **args, action_id=proposal.id)
    before = stock_at(session, tid, business.item.id, business.location.id)
    with pytest.raises(InvalidOperation, match="unresolved"):
        prepare_delivery_action(
            session,
            tid,
            "reserve",
            {"commitment_id": fixture.commitment.id, "quantity": "1"},
            request_id="conflicting",
        )
    result = reconcile_delivery(session, tid, proposal.id)
    assert result["verification"] == "verified"
    assert result["status"] == "executed"
    assert stock_at(session, tid, business.item.id, business.location.id) == before
    assert reconcile_delivery(session, tid, proposal.id)["receipt"] == result["receipt"]


def test_company_tool_proposal_uses_same_release_review(session, business):
    fixture = delivery_fixture(session, business)
    reservation = reserve(session, business.tenant.id, fixture.commitment.id, "2")
    proposal = create_change_proposal(
        session,
        business.tenant.id,
        "reservation_release",
        {"reservation_id": reservation.reservation.id},
    )
    assert json.loads(proposal.input)["_delivery_review"]["effect"] == {"released": "2"}
    with pytest.raises(InvalidOperation, match="confirmation"):
        approve_and_execute_proposal(session, business.tenant.id, proposal.id)


def test_receipt_stale_state_and_foreign_commitment(session, business):
    from reality.services.core import create_tenant

    tid = business.tenant.id
    commitment = incoming(session, business)
    args = receipt_args(business, commitment)
    proposal = prepare_delivery_action(
        session, tid, "movement_create", args, request_id="stale-receipt"
    )
    record_movement(session, tid, **receipt_args(business, commitment, "1"))
    with pytest.raises(InvalidOperation, match="review"):
        confirm(session, tid, proposal)
    assert proposal.status == "proposed"
    other = create_tenant(session, "Another company")
    with pytest.raises(NotFound):
        prepare_delivery_action(
            session, other.id, "movement_create", args, request_id="foreign-receipt"
        )


def test_release_wrong_receipt_cannot_verify(session, business):
    fixture = delivery_fixture(session, business)
    tid = business.tenant.id
    reservation = reserve(session, tid, fixture.commitment.id, "6").reservation
    proposal = prepare_delivery_action(
        session,
        tid,
        "reservation_release",
        {"reservation_id": reservation.id},
        request_id="bad-receipt",
    )
    confirm(session, tid, proposal)
    proposal.output = json.dumps(
        {"records": [{"family": "reservation", "id": "wrong"}]}
    )
    session.commit()
    assert (
        delivery_proposal_detail(session, tid, proposal.id)["verification"]
        == "unresolved"
    )


def test_receipt_and_release_http_review_round_trip(session, business):
    from fastapi.testclient import TestClient
    from sqlalchemy.orm import sessionmaker

    from reality.web.api import database_session
    from reality.web.app import app

    fixture = delivery_fixture(session, business)
    reservation = reserve(
        session, business.tenant.id, fixture.commitment.id, "6"
    ).reservation
    commitment = incoming(session, business)
    factory = sessionmaker(session.bind, expire_on_commit=False)

    def database():
        with factory() as connection:
            yield connection

    app.dependency_overrides[database_session] = database
    try:
        with TestClient(app) as client:
            base = f"/api/tenants/{business.tenant.id}"
            for tool, args in [
                ("reservation_release", {"reservation_id": reservation.id}),
                ("movement_create", receipt_args(business, commitment)),
            ]:
                response = client.post(
                    f"{base}/delivery-actions/prepare",
                    json={"tool": tool, "arguments": args, "request_id": tool},
                )
                assert response.status_code == 200, response.text
                proposal = response.json()
                response = client.post(
                    f"{base}/change-proposals/{proposal['id']}/approve",
                    json={
                        "review_token": proposal["review"]["token"],
                        "confirmed": True,
                    },
                )
                assert response.status_code == 200, response.text
                result = client.get(f"{base}/delivery-actions/{proposal['id']}")
                assert result.json()["verification"] == "verified"
    finally:
        app.dependency_overrides.clear()


def test_receipt_guards_actual_destination_pool(session, business):
    from reality.services.core import create_location

    tid = business.tenant.id
    alternate = create_location(session, tid, "Second warehouse")
    prior = create_commitment(
        session,
        tid,
        "supplier_delivery",
        business.supplier.id,
        business.company.id,
        business.item.id,
        alternate.id,
        "8",
        None,
    )
    pending = prepare_delivery_action(
        session,
        tid,
        "movement_create",
        {**receipt_args(business, prior), "to_location_id": alternate.id},
        request_id="pending-destination",
    )
    pending.status = "executing"
    session.commit()
    current = incoming(session, business)
    with pytest.raises(InvalidOperation, match="unresolved"):
        prepare_delivery_action(
            session,
            tid,
            "movement_create",
            {**receipt_args(business, current), "to_location_id": alternate.id},
            request_id="same-destination",
        )
