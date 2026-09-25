"""Reviewed opening stock is additive, state-bound and recoverable without replay."""

import json
from decimal import Decimal

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from reality.db.core import BusinessEvent, Movement
from reality.services.core import (
    InvalidOperation,
    NotFound,
    correct_movement,
    create_tenant,
    record_movement,
    stock_at,
    update_item,
)
from reality.services.delivery_actions import (
    delivery_proposal_detail,
    prepare_delivery_action,
    reconcile_delivery,
    review_existing,
)
from reality.tools.application import (
    approve_and_execute_proposal,
    create_change_proposal,
)


def args(business, **extra):
    return {
        "movement_type": "opening_stock",
        "item_id": business.item.id,
        "to_location_id": business.location.id,
        "quantity": "5.25",
        **extra,
    }


def prepare(session, business, request="opening", **extra):
    return prepare_delivery_action(
        session,
        business.tenant.id,
        "movement_create",
        args(business, **extra),
        request_id=request,
    )


def confirm(session, business, proposal):
    return approve_and_execute_proposal(
        session,
        business.tenant.id,
        proposal.id,
        review_token=json.loads(proposal.input)["_delivery_review"]["token"],
        confirmed=True,
    )


def test_opening_review_adds_and_replay_is_inert(session, business):
    tid = business.tenant.id
    record_movement(
        session,
        tid,
        "opening_stock",
        business.item.id,
        "10",
        to_location_id=business.location.id,
    )
    proposal = prepare(session, business)
    detail = delivery_proposal_detail(session, tid, proposal.id)
    assert detail["review"]["state"]["physical"] == "10"
    assert detail["review"]["effect"] == {
        "added": "5.25",
        "physical_after": "15.25",
        "reserved_after": "0",
    }
    assert stock_at(session, tid, business.item.id, business.location.id) == Decimal(10)
    confirm(session, business, proposal)
    done = delivery_proposal_detail(session, tid, proposal.id)
    assert done["verification"] == "verified"
    assert done["observation"]["physical"] == "15.25"
    assert prepare(session, business).id == proposal.id
    confirm(session, business, proposal)
    assert stock_at(session, tid, business.item.id, business.location.id) == Decimal(
        "15.25"
    )
    with pytest.raises(InvalidOperation):
        prepare(session, business, quantity="7")


@pytest.mark.parametrize(
    "extra",
    [
        {"quantity": "0"},
        {"quantity": "-1"},
        {"quantity": "NaN"},
        {"quantity": "0.00001"},
        {"quantity": "100000000000000"},
        {"source_record_id": "other"},
        {"from_location_id": "other"},
        {"commitment_id": "other"},
        {"reason": "not retained"},
        {"lot_id": "other"},
    ],
)
def test_invalid_review_is_inert(session, business, extra):
    with pytest.raises(InvalidOperation):
        prepare(session, business, **extra)
    assert (
        session.scalar(
            select(func.count())
            .select_from(Movement)
            .where(Movement.tenant_id == business.tenant.id)
        )
        == 0
    )


def test_stale_stock_references_and_foreign_scope(session, business):
    proposal = prepare(session, business)
    record_movement(
        session,
        business.tenant.id,
        "opening_stock",
        business.item.id,
        "1",
        to_location_id=business.location.id,
    )
    with pytest.raises(InvalidOperation):
        confirm(session, business, proposal)
    fresh = prepare(session, business, "fresh")
    update_item(
        session,
        business.tenant.id,
        business.item.id,
        business.item.sku,
        "Renamed",
        business.item.unit,
    )
    with pytest.raises(InvalidOperation):
        confirm(session, business, fresh)
    foreign = create_tenant(session, "Other")
    with pytest.raises(NotFound):
        delivery_proposal_detail(session, foreign.id, proposal.id)
    with pytest.raises(NotFound):
        prepare_delivery_action(
            session, foreign.id, "movement_create", args(business), request_id="foreign"
        )


def test_opening_receipt_recovery_and_later_correction(session, business):
    tid = business.tenant.id
    proposal = prepare(session, business, occurred_at="2026-09-08T10:00:00+02:00")
    confirm(session, business, proposal)
    movement_id = json.loads(proposal.output)["records"][0]["id"]
    proposal.status = "executing"
    proposal.output = "{}"
    session.commit()
    detail = delivery_proposal_detail(session, tid, proposal.id)
    assert detail["verification"] == "recorded_unsettled"
    recovered = reconcile_delivery(session, tid, proposal.id)
    assert recovered["verification"] == "verified"
    correct_movement(session, tid, movement_id, reason="Mistaken opening")
    historical = delivery_proposal_detail(session, tid, proposal.id)
    assert historical["verification"] == "verified"
    assert historical["observation"]["physical"] == "0"
    proposal.output = '{"records": []}'
    session.commit()
    assert (
        delivery_proposal_detail(session, tid, proposal.id)["verification"]
        == "unresolved"
    )


def test_event_payload_must_match_and_raw_opening_stays_compatible(session, business):
    tid = business.tenant.id
    proposal = create_change_proposal(session, tid, "movement_create", args(business))
    approve_and_execute_proposal(session, tid, proposal.id)
    assert (
        delivery_proposal_detail(session, tid, proposal.id)["verification"]
        == "verified"
    )
    event = session.scalar(
        select(BusinessEvent).where(
            BusinessEvent.tenant_id == tid,
            BusinessEvent.action_id == proposal.id,
            BusinessEvent.event_type == "movement.recorded",
        )
    )
    value = json.loads(event.payload)
    value["quantity"] = "999"
    event.payload = json.dumps(value)
    session.commit()
    assert (
        delivery_proposal_detail(session, tid, proposal.id)["verification"]
        == "unresolved"
    )


def test_existing_chat_proposal_can_acquire_review(session, business):
    proposal = create_change_proposal(
        session, business.tenant.id, "movement_create", args(business)
    )
    review_existing(session, business.tenant.id, proposal.id)
    assert "_delivery_review" in json.loads(proposal.input)
    with pytest.raises(InvalidOperation):
        approve_and_execute_proposal(session, business.tenant.id, proposal.id)
    confirm(session, business, proposal)


def test_two_independent_reviews_cannot_both_use_old_balance(postgres_database):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier
    from types import SimpleNamespace

    from reality.db.core import Base, build_engine
    from reality.services.core import create_item, create_location

    engine = build_engine(postgres_database)
    Base.metadata.create_all(engine)
    try:
        with Session(engine, expire_on_commit=False) as session:
            tenant = create_tenant(session, "Concurrent opening")
            business = SimpleNamespace(
                tenant=tenant,
                item=create_item(session, tenant.id, "OPEN", "Opening item"),
                location=create_location(session, tenant.id, "Main"),
            )
            proposals = [prepare(session, business, name) for name in ("one", "two")]
            identities = [
                (p.id, json.loads(p.input)["_delivery_review"]["token"])
                for p in proposals
            ]
        barrier = Barrier(2)

        def execute(identity):
            with Session(engine) as separate:
                barrier.wait(timeout=10)
                try:
                    approve_and_execute_proposal(
                        separate,
                        tenant.id,
                        identity[0],
                        review_token=identity[1],
                        confirmed=True,
                    )
                    return "done"
                except InvalidOperation:
                    return "stale"

        with ThreadPoolExecutor(max_workers=2) as pool:
            assert sorted(pool.map(execute, identities)) == ["done", "stale"]
        with Session(engine) as session:
            assert stock_at(
                session, tenant.id, business.item.id, business.location.id
            ) == Decimal("5.25")
    finally:
        engine.dispose()


@pytest.mark.parametrize(
    "tracking,item_type",
    [("lot", "stocked"), ("serial", "stocked"), ("none", "service")],
)
def test_unsupported_item_is_inert(session, business, tracking, item_type):
    from reality.services.core import create_item

    item = create_item(
        session,
        business.tenant.id,
        "OTHER",
        "Other",
        tracking_type=tracking,
        item_type=item_type,
    )
    with pytest.raises(InvalidOperation):
        prepare(session, business, item_id=item.id)
    assert stock_at(session, business.tenant.id, item.id, business.location.id) == 0


def test_destination_must_allow_stock(session, business):
    from reality.services.core import create_location

    location = create_location(session, business.tenant.id, "Group", allows_stock=False)
    with pytest.raises(InvalidOperation):
        prepare(session, business, to_location_id=location.id)


@pytest.mark.parametrize("other_tool", ["reserve", "movement_correct"])
@pytest.mark.parametrize("opening_first", [True, False])
def test_unresolved_pool_overlap_is_mutual(
    session, business, other_tool, opening_first
):
    from unified_fixtures import delivery_fixture

    from reality.services.core import create_location

    tid = business.tenant.id
    commitment = delivery_fixture(session, business).commitment
    original = record_movement(
        session,
        tid,
        "opening_stock",
        business.item.id,
        "10",
        to_location_id=business.location.id,
    )
    other = (
        {"commitment_id": commitment.id, "quantity": "1"}
        if other_tool == "reserve"
        else {"movement_id": original.id, "reason": "Check"}
    )
    first_tool, first_args = (
        ("movement_create", args(business)) if opening_first else (other_tool, other)
    )
    second_tool, second_args = (
        (other_tool, other) if opening_first else ("movement_create", args(business))
    )
    pending = prepare_delivery_action(
        session, tid, first_tool, first_args, request_id="pending"
    )
    pending.status = "executing"
    session.commit()
    with pytest.raises(InvalidOperation, match="unresolved"):
        prepare_delivery_action(
            session, tid, second_tool, second_args, request_id="blocked"
        )
    location = create_location(session, tid, "Unrelated")
    assert (
        prepare(session, business, "unrelated", to_location_id=location.id).status
        == "proposed"
    )


def test_opening_http_actor_and_practice(session, business):
    from types import SimpleNamespace

    from fastapi.testclient import TestClient
    from sqlalchemy.orm import sessionmaker

    from reality.db.core import Tenant
    from reality.services.core import uid
    from reality.web.api import database_session
    from reality.web.app import app

    tid = business.tenant.id
    proposal = prepare(session, business)
    with pytest.raises(NotFound):
        approve_and_execute_proposal(
            session,
            tid,
            proposal.id,
            confirmed=True,
            review_token=json.loads(proposal.input)["_delivery_review"]["token"],
            confirming_principal=SimpleNamespace(
                user_id="absent", is_platform_admin=False
            ),
        )
    factory = sessionmaker(session.bind, expire_on_commit=False)

    def database():
        with factory() as connection:
            yield connection

    app.dependency_overrides[database_session] = database
    try:
        with TestClient(app) as client:
            base = f"/api/tenants/{tid}"
            response = client.post(
                f"{base}/delivery-actions/prepare",
                json={
                    "tool": "movement_create",
                    "request_id": "http",
                    "arguments": args(business),
                },
            )
            assert response.status_code == 200, response.text
            value = response.json()
            assert (
                client.post(
                    f"{base}/change-proposals/{value['id']}/approve",
                    json={"confirmed": False},
                ).status_code
                >= 400
            )
            response = client.post(
                f"{base}/change-proposals/{value['id']}/approve",
                json={"confirmed": True, "review_token": value["review"]["token"]},
            )
            assert response.status_code == 200, response.text
            assert (
                client.get(f"{base}/delivery-actions/{value['id']}").json()[
                    "verification"
                ]
                == "verified"
            )
    finally:
        app.dependency_overrides.clear()
    practice = Tenant(id=uid("ten"), name="Practice", purpose="playground")
    session.add(practice)
    session.commit()
    with pytest.raises(InvalidOperation, match="practice"):
        prepare_delivery_action(
            session,
            practice.id,
            "movement_create",
            args(business),
            request_id="practice",
        )


def test_failure_before_commit_has_no_partial_movement(session, business, monkeypatch):
    from reality.services import core

    proposal = prepare(session, business)
    original = core.emit_business_event

    def fail(connection, tenant, event_type, *args, **kwargs):
        if event_type == "movement.recorded":
            raise RuntimeError("Injected before commit")
        return original(connection, tenant, event_type, *args, **kwargs)

    monkeypatch.setattr(core, "emit_business_event", fail)
    with pytest.raises(RuntimeError, match="Injected"):
        confirm(session, business, proposal)
    session.rollback()
    assert (
        stock_at(session, business.tenant.id, business.item.id, business.location.id)
        == 0
    )
    assert (
        delivery_proposal_detail(session, business.tenant.id, proposal.id)[
            "verification"
        ]
        == "unresolved"
    )


@pytest.mark.parametrize(
    "tracking,item_type",
    [("lot", "stocked"), ("serial", "stocked"), ("none", "service")],
)
def test_raw_opening_refuses_an_unsupported_item_when_proposed(
    session, business, tracking, item_type
):
    """Spec 132 FR-002: an item opening stock cannot accept is refused as it is proposed.

    The refusal used to wait for confirmation, so an agent asked to prepare opening stock
    created a decision a person could open, read and never approve.
    """
    from reality.db.core import ChangeProposal
    from reality.services.core import create_item

    tid = business.tenant.id
    item = create_item(
        session, tid, "OTHER", "Other", tracking_type=tracking, item_type=item_type
    )
    decisions = (
        select(func.count())
        .select_from(ChangeProposal)
        .where(ChangeProposal.tenant_id == tid)
    )
    before = session.scalar(decisions)
    with pytest.raises(InvalidOperation):
        create_change_proposal(
            session, tid, "movement_create", args(business, item_id=item.id)
        )
    assert session.scalar(decisions) == before
    assert stock_at(session, tid, item.id, business.location.id) == 0


def test_raw_opening_refuses_a_destination_that_holds_no_stock_when_proposed(
    session, business
):
    """Spec 132 FR-002: the destination is proved as the decision is proposed."""
    from reality.services.core import create_location

    tid = business.tenant.id
    location = create_location(session, tid, "Group", allows_stock=False)
    with pytest.raises(InvalidOperation):
        create_change_proposal(
            session, tid, "movement_create", args(business, to_location_id=location.id)
        )
