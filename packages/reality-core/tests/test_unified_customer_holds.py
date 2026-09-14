"""Reviewed customer-wide shipment controls preserve reservations and history."""

import json
from types import SimpleNamespace

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from reality.db.core import BusinessEvent, PartyHold
from reality.services import core
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

PLACE = "party_delivery_hold"
RELEASE = "party_delivery_hold_release"


def prepare(session, business, tool=PLACE, request="place", **extra):
    arguments = {
        "party_id": business.customer.id,
        **(
            {"reason_code": "manual_review", "note": " Check <original> "}
            if tool == PLACE
            else {}
        ),
        **extra,
    }
    return prepare_delivery_action(
        session, business.tenant.id, tool, arguments, request_id=request
    )


def confirm(session, business, proposal):
    return approve_and_execute_proposal(
        session,
        business.tenant.id,
        proposal.id,
        review_token=json.loads(proposal.input)["_delivery_review"]["token"],
        confirmed=True,
    )


def detail(session, business, proposal):
    return delivery_proposal_detail(session, business.tenant.id, proposal.id)


def test_review_place_release_history_and_replay(session, business):
    tid = business.tenant.id
    proposal = prepare(session, business)
    assert detail(session, business, proposal)["review"]["state"]["holds"] == []
    assert core.active_party_delivery_hold(session, tid, business.customer.id) is None
    confirm(session, business, proposal)
    assert detail(session, business, proposal)["verification"] == "verified"
    assert prepare(session, business).id == proposal.id
    confirm(session, business, proposal)
    hold = core.active_party_delivery_hold(session, tid, business.customer.id)
    assert hold.note == "Check <original>"
    released = prepare(session, business, RELEASE, "release")
    confirm(session, business, released)
    assert detail(session, business, released)["verification"] == "verified"
    assert detail(session, business, proposal)["verification"] == "verified"
    again = prepare(session, business, request="again")
    confirm(session, business, again)
    assert detail(session, business, released)["verification"] == "verified"
    assert (
        detail(session, business, released)["observation"]["holds"][0]["id"] != hold.id
    )
    assert core.stock_at(session, tid, business.item.id, business.location.id) == 0
    with pytest.raises(core.InvalidOperation):
        prepare(session, business, note="different")


@pytest.mark.parametrize(
    "extra",
    [
        {"reason_code": "invalid"},
        {"note": 12},
        {"created_by": "admin"},
        {"action_id": "fake"},
        {"reason": "not retained"},
    ],
)
def test_invalid_intent_is_inert(session, business, extra):
    with pytest.raises(core.InvalidOperation):
        prepare(session, business, **extra)
    assert (
        core.active_party_delivery_hold(
            session, business.tenant.id, business.customer.id
        )
        is None
    )


def test_noop_foreign_noncustomer_and_stale_reference(session, business):
    with pytest.raises(core.InvalidOperation):
        prepare(session, business, RELEASE)
    with pytest.raises(core.NotFound):
        prepare(session, business, party_id=business.supplier.id)
    foreign = core.create_tenant(session, "Other")
    customer = core.create_party(session, foreign.id, "Other customer", "customer")
    with pytest.raises(core.NotFound):
        prepare(session, business, party_id=customer.id)
    proposal = prepare(session, business)
    with pytest.raises(core.NotFound):
        delivery_proposal_detail(session, foreign.id, proposal.id)
    business.customer.name = "Renamed"
    session.commit()
    with pytest.raises(core.InvalidOperation):
        confirm(session, business, proposal)
    fresh = prepare(session, business, request="fresh")
    confirm(session, business, fresh)
    with pytest.raises(core.InvalidOperation):
        prepare(session, business, request="duplicate")


def test_release_reapply_with_same_reason_invalidates_old_review(session, business):
    core.hold_party_delivery(
        session, business.tenant.id, business.customer.id, "manual_review"
    )
    proposal = prepare(session, business, RELEASE)
    core.release_party_delivery_hold(session, business.tenant.id, business.customer.id)
    core.hold_party_delivery(
        session, business.tenant.id, business.customer.id, "manual_review"
    )
    with pytest.raises(core.InvalidOperation):
        confirm(session, business, proposal)


def test_future_shipments_blocked_reservations_allowed_and_own_hold_remains(
    session, business
):
    tid = business.tenant.id
    core.record_movement(
        session,
        tid,
        "opening_stock",
        business.item.id,
        "10",
        to_location_id=business.location.id,
    )
    placed = prepare(session, business)
    confirm(session, business, placed)
    cid = core.create_commitment(
        session,
        tid,
        "customer_delivery",
        business.company.id,
        business.customer.id,
        business.item.id,
        business.location.id,
        "3",
        None,
    ).id
    assert core.reserve(session, tid, cid).reserved == 3
    with pytest.raises(core.InvalidOperation, match="delivery hold"):
        core.record_movement(
            session,
            tid,
            "shipment",
            business.item.id,
            "1",
            from_location_id=business.location.id,
            commitment_id=cid,
        )
    core.hold_commitment(session, tid, cid, "manual_review")
    released = prepare(session, business, RELEASE, "release")
    confirm(session, business, released)
    with pytest.raises(core.InvalidOperation):
        core.record_movement(
            session,
            tid,
            "shipment",
            business.item.id,
            "1",
            from_location_id=business.location.id,
            commitment_id=cid,
        )
    assert (
        core.active_reserved(session, tid, business.item.id, business.location.id) == 3
    )
    assert core.stock_at(session, tid, business.item.id, business.location.id) == 10


def test_exact_event_recovery_without_replay_and_tamper_rejection(session, business):
    proposal = prepare(session, business)
    confirm(session, business, proposal)
    proposal.status = "executing"
    proposal.output = "{}"
    session.commit()
    assert detail(session, business, proposal)["verification"] == "recorded_unsettled"
    assert (
        reconcile_delivery(session, business.tenant.id, proposal.id)["verification"]
        == "verified"
    )
    event = session.scalar(
        select(BusinessEvent).where(
            BusinessEvent.tenant_id == business.tenant.id,
            BusinessEvent.action_id == proposal.id,
            BusinessEvent.event_type == "party.delivery_hold_placed",
        )
    )
    value = json.loads(event.payload)
    value["hold"]["note"] = "tampered"
    event.payload = json.dumps(value)
    session.commit()
    assert detail(session, business, proposal)["verification"] == "unresolved"


def test_raw_tool_compatibility_and_explicit_review(session, business):
    raw = create_change_proposal(
        session,
        business.tenant.id,
        PLACE,
        {"party_id": business.supplier.id, "reason_code": "manual_review"},
    )
    approve_and_execute_proposal(session, business.tenant.id, raw.id)
    assert core.active_party_delivery_hold(
        session, business.tenant.id, business.supplier.id
    )
    customer = create_change_proposal(
        session,
        business.tenant.id,
        PLACE,
        {"party_id": business.customer.id, "reason_code": "manual_review"},
    )
    review_existing(session, business.tenant.id, customer.id)
    with pytest.raises(core.InvalidOperation):
        approve_and_execute_proposal(session, business.tenant.id, customer.id)
    confirm(session, business, customer)


@pytest.mark.parametrize("first_hold", [True, False])
def test_unresolved_shipment_overlap_is_mutual(session, business, first_hold):
    from unified_fixtures import delivery_fixture

    fixture = delivery_fixture(session, business)
    shipment = {
        "movement_type": "shipment",
        "item_id": business.item.id,
        "from_location_id": business.location.id,
        "commitment_id": fixture.commitment.id,
        "quantity": "1",
    }
    held = {"party_id": business.customer.id, "reason_code": "manual_review"}
    first = prepare_delivery_action(
        session,
        business.tenant.id,
        PLACE if first_hold else "movement_create",
        held if first_hold else shipment,
        request_id="pending",
    )
    first.status = "executing"
    session.commit()
    with pytest.raises(core.InvalidOperation, match="unresolved"):
        prepare_delivery_action(
            session,
            business.tenant.id,
            "movement_create" if first_hold else PLACE,
            shipment if first_hold else held,
            request_id="blocked",
        )


def test_concurrent_placement_has_one_effect(postgres_database):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier

    from reality.db.core import Base, build_engine

    engine = build_engine(postgres_database)
    Base.metadata.create_all(engine)
    try:
        with Session(engine, expire_on_commit=False) as connection:
            tenant = core.create_tenant(connection, "Concurrent holds")
            business = SimpleNamespace(
                tenant=tenant,
                customer=core.create_party(
                    connection, tenant.id, "Customer", "customer"
                ),
            )
            proposals = [
                prepare(connection, business, request=x) for x in ("one", "two")
            ]
            identities = [
                (p.id, json.loads(p.input)["_delivery_review"]["token"])
                for p in proposals
            ]
        barrier = Barrier(2)

        def execute(identity):
            with Session(engine) as connection:
                barrier.wait(timeout=10)
                try:
                    approve_and_execute_proposal(
                        connection,
                        tenant.id,
                        identity[0],
                        review_token=identity[1],
                        confirmed=True,
                    )
                    return True
                except core.InvalidOperation:
                    return False

        with ThreadPoolExecutor(max_workers=2) as pool:
            assert sorted(pool.map(execute, identities)) == [False, True]
        with Session(engine) as connection:
            assert (
                len(
                    list(
                        connection.scalars(
                            select(PartyHold).where(PartyHold.tenant_id == tenant.id)
                        )
                    )
                )
                == 1
            )
    finally:
        engine.dispose()


def test_release_recovers_exact_multiple_hold_set_and_receipt_mismatch(
    session, business
):
    tid = business.tenant.id
    core.hold_party_delivery(session, tid, business.customer.id, "manual_review")
    session.add(
        PartyHold(
            id=core.uid("phd"),
            tenant_id=tid,
            party_id=business.customer.id,
            hold_type="delivery",
            reason_code="credit_check",
            note="Legacy second hold",
            created_by="human",
        )
    )
    session.commit()
    proposal = prepare(session, business, RELEASE)
    assert len(detail(session, business, proposal)["review"]["state"]["holds"]) == 2
    confirm(session, business, proposal)
    proposal.status = "executing"
    proposal.output = "{}"
    session.commit()
    assert reconcile_delivery(session, tid, proposal.id)["verification"] == "verified"
    assert len(json.loads(proposal.output)["records"]) == 2
    proposal.output = '{"records": []}'
    session.commit()
    assert detail(session, business, proposal)["verification"] == "unresolved"


def test_held_customer_invalidates_prepared_shipment(session, business):
    from unified_fixtures import delivery_fixture

    fixture = delivery_fixture(session, business)
    shipment = prepare_delivery_action(
        session,
        business.tenant.id,
        "movement_create",
        {
            "movement_type": "shipment",
            "item_id": business.item.id,
            "from_location_id": business.location.id,
            "commitment_id": fixture.commitment.id,
            "quantity": "1",
        },
        request_id="shipment",
    )
    confirm(session, business, prepare(session, business))
    with pytest.raises(core.InvalidOperation):
        confirm(session, business, shipment)


def test_unresolved_shipment_correction_blocks_customer_hold(session, business):
    from unified_fixtures import delivery_fixture

    fixture = delivery_fixture(session, business)
    original = core.record_movement(
        session,
        business.tenant.id,
        "shipment",
        business.item.id,
        "1",
        from_location_id=business.location.id,
        commitment_id=fixture.commitment.id,
    )
    correction = prepare_delivery_action(
        session,
        business.tenant.id,
        "movement_correct",
        {"movement_id": original.id, "reason": "Wrong quantity"},
        request_id="correction",
    )
    correction.status = "executing"
    session.commit()
    with pytest.raises(core.InvalidOperation, match="unresolved"):
        prepare(session, business)


def test_failure_before_commit_leaves_no_hold(session, business, monkeypatch):
    proposal = prepare(session, business)
    original = core.emit_business_event

    def fail(connection, tenant, event_type, *args, **kwargs):
        if event_type == "party.delivery_hold_placed":
            raise RuntimeError("Injected failure")
        return original(connection, tenant, event_type, *args, **kwargs)

    monkeypatch.setattr(core, "emit_business_event", fail)
    with pytest.raises(RuntimeError, match="Injected"):
        confirm(session, business, proposal)
    session.rollback()
    assert (
        core.active_party_delivery_hold(
            session, business.tenant.id, business.customer.id
        )
        is None
    )
    assert detail(session, business, proposal)["verification"] == "unresolved"


def test_customer_hold_http_actor_and_practice(session, business):
    from fastapi.testclient import TestClient
    from sqlalchemy.orm import sessionmaker

    from reality.db.core import Tenant
    from reality.web.api import database_session
    from reality.web.app import app

    tid = business.tenant.id
    proposal = prepare(session, business)
    with pytest.raises(core.NotFound):
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
            assert (
                client.get(f"{base}/customer-holds/{business.customer.id}").json()[
                    "holds"
                ]
                == []
            )
            assert (
                client.get(f"{base}/customer-holds/{business.supplier.id}").status_code
                == 404
            )
            response = client.post(
                f"{base}/delivery-actions/prepare",
                json={
                    "tool": PLACE,
                    "request_id": "http",
                    "arguments": {
                        "party_id": business.customer.id,
                        "reason_code": "manual_review",
                    },
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
    practice = Tenant(id=core.uid("ten"), name="Practice", purpose="playground")
    session.add(practice)
    session.commit()
    with pytest.raises(core.InvalidOperation, match="practice"):
        prepare_delivery_action(
            session,
            practice.id,
            PLACE,
            {"party_id": business.customer.id, "reason_code": "manual_review"},
            request_id="practice",
        )
