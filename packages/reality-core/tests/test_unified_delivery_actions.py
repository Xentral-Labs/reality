from decimal import Decimal

import pytest
from unified_fixtures import delivery_fixture

from reality.services.core import InvalidOperation, record_movement, stock_at
from reality.services.delivery_actions import prepare_delivery_action
from reality.tools.application import approve_and_execute_proposal


def test_review_is_required_and_stale_stock_never_executes(session, business):
    fixture = delivery_fixture(session, business)
    tid, cid = business.tenant.id, fixture.commitment.id
    proposal = prepare_delivery_action(
        session,
        tid,
        "reserve",
        {"commitment_id": cid, "quantity": "12"},
        request_id="request-one",
    )
    assert stock_at(session, tid, business.item.id, business.location.id) == Decimal(20)
    with pytest.raises(InvalidOperation):
        approve_and_execute_proposal(session, tid, proposal.id)
    record_movement(
        session,
        tid,
        "shipment",
        business.item.id,
        "10",
        from_location_id=business.location.id,
    )
    import json

    token = json.loads(proposal.input)["_delivery_review"]["token"]
    with pytest.raises(InvalidOperation, match="review"):
        approve_and_execute_proposal(
            session, tid, proposal.id, review_token=token, confirmed=True
        )
    assert proposal.status == "proposed"


def test_same_preparation_and_confirmation_have_one_effect(session, business):
    import json

    fixture = delivery_fixture(session, business)
    tid, cid = business.tenant.id, fixture.commitment.id
    args = {"commitment_id": cid, "quantity": "12"}
    proposal = prepare_delivery_action(
        session, tid, "reserve", args, request_id="same-request"
    )
    again = prepare_delivery_action(
        session, tid, "reserve", args, request_id="same-request"
    )
    assert again.id == proposal.id
    token = json.loads(proposal.input)["_delivery_review"]["token"]
    first = approve_and_execute_proposal(
        session, tid, proposal.id, review_token=token, confirmed=True
    )
    second = approve_and_execute_proposal(
        session, tid, proposal.id, review_token=token, confirmed=True
    )
    assert first.output == second.output
    assert Decimal(json.loads(first.output)["applied"]) == 12


def test_shipment_recovery_uses_recorded_evidence_without_reexecution(
    session, business
):
    import json

    from reality.services.core import reserve
    from reality.services.delivery_actions import (
        delivery_proposal_detail,
        reconcile_delivery,
    )

    fixture = delivery_fixture(session, business)
    tid, cid = business.tenant.id, fixture.commitment.id
    reserve(session, tid, cid, "12")
    args = {
        "movement_type": "shipment",
        "commitment_id": cid,
        "item_id": business.item.id,
        "from_location_id": business.location.id,
        "quantity": "5",
    }
    proposal = prepare_delivery_action(
        session, tid, "movement_create", args, request_id="shipment-recovery"
    )
    proposal.status = "executing"
    session.commit()
    movement = record_movement(session, tid, **args, action_id=proposal.id)
    before = stock_at(session, tid, business.item.id, business.location.id)
    assert (
        delivery_proposal_detail(session, tid, proposal.id)["verification"]
        == "recorded_unsettled"
    )
    result = reconcile_delivery(session, tid, proposal.id)
    assert result["status"] == "executed"
    assert result["verification"] == "verified"
    assert json.loads(proposal.output)["records"][0]["id"] == movement.id
    assert stock_at(session, tid, business.item.id, business.location.id) == before


def test_original_reservation_verifies_after_consumption(session, business):
    import json

    from reality.services.delivery_actions import delivery_proposal_detail

    fixture = delivery_fixture(session, business)
    tid, cid = business.tenant.id, fixture.commitment.id
    proposal = prepare_delivery_action(
        session,
        tid,
        "reserve",
        {"commitment_id": cid, "quantity": "12"},
        request_id="historical",
    )
    approve_and_execute_proposal(
        session,
        tid,
        proposal.id,
        review_token=json.loads(proposal.input)["_delivery_review"]["token"],
        confirmed=True,
    )
    record_movement(
        session,
        tid,
        "shipment",
        business.item.id,
        "5",
        from_location_id=business.location.id,
        commitment_id=cid,
    )
    detail = delivery_proposal_detail(session, tid, proposal.id)
    assert detail["verification"] == "verified"
    assert Decimal(detail["receipt"]["applied"]) == 12
    assert Decimal(detail["observation"]["case"]["reserved"]) == 7


def test_context_is_tenant_validated_and_preserved_as_history(
    session, business, monkeypatch
):
    import json

    from reality.services.core import (
        NotFound,
        create_chat_session,
        create_tenant,
        send_chat_message,
    )

    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    fixture = delivery_fixture(session, business)
    chat = create_chat_session(session, business.tenant.id)
    user, _ = send_chat_message(
        session,
        business.tenant.id,
        chat.id,
        "Explain Source and Evidence",
        context_commitment_id=fixture.commitment.id,
    )
    context = json.loads(user.content.split(":", 1)[1])
    assert context["commitment_id"] == fixture.commitment.id
    assert context["message"] == "Explain Source and Evidence"
    other = create_tenant(session, "Other company")
    other_chat = create_chat_session(session, other.id)
    with pytest.raises(NotFound):
        send_chat_message(
            session,
            other.id,
            other_chat.id,
            "Explain",
            context_commitment_id=fixture.commitment.id,
        )


def test_two_connections_cannot_overallocate_or_execute_two_stale_reviews(
    postgres_database,
):
    import json
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier

    from sqlalchemy import func, select
    from sqlalchemy.orm import sessionmaker

    from reality.db.core import Base, Reservation, build_engine
    from reality.services.core import (
        create_commitment,
        create_item,
        create_location,
        create_party,
        create_tenant,
        reserve,
    )

    engine = build_engine(postgres_database)
    Base.metadata.create_all(engine)
    factory = sessionmaker(engine, expire_on_commit=False)
    try:
        with factory() as session:
            tenant = create_tenant(session, "Concurrent deliveries")
            company = create_party(session, tenant.id, "Company", "company")
            customer = create_party(session, tenant.id, "Customer", "customer")
            item = create_item(session, tenant.id, "LAMP", "Lamp")
            location = create_location(session, tenant.id, "Warehouse")
            record_movement(
                session, tenant.id, "receipt", item.id, "10", to_location_id=location.id
            )
            commitments = [
                create_commitment(
                    session,
                    tenant.id,
                    "customer_delivery",
                    company.id,
                    customer.id,
                    item.id,
                    location.id,
                    "7",
                    None,
                ).id
                for _ in range(2)
            ]
        barrier = Barrier(2)

        def allocate(cid):
            with factory() as session:
                barrier.wait(timeout=5)
                return reserve(session, tenant.id, cid, "7").reserved

        with ThreadPoolExecutor(max_workers=2) as workers:
            quantities = list(workers.map(allocate, commitments))
        assert sum(quantities) == Decimal(10)
        with factory() as session:
            assert (
                session.scalar(
                    select(func.sum(Reservation.quantity)).where(
                        Reservation.tenant_id == tenant.id,
                        Reservation.status == "active",
                    )
                )
                == 10
            )
            # A separate stock pool proves exact-review competition, not only core capping.
            item2 = create_item(session, tenant.id, "SECOND", "Second lamp")
            record_movement(
                session,
                tenant.id,
                "receipt",
                item2.id,
                "10",
                to_location_id=location.id,
            )
            commitments2 = [
                create_commitment(
                    session,
                    tenant.id,
                    "customer_delivery",
                    company.id,
                    customer.id,
                    item2.id,
                    location.id,
                    "7",
                    None,
                ).id
                for _ in range(2)
            ]
            reviews = []
            for index, cid in enumerate(commitments2):
                proposal = prepare_delivery_action(
                    session,
                    tenant.id,
                    "reserve",
                    {"commitment_id": cid, "quantity": "7"},
                    request_id=f"race-{index}",
                )
                reviews.append(
                    (
                        proposal.id,
                        json.loads(proposal.input)["_delivery_review"]["token"],
                    )
                )
        barrier = Barrier(2)

        def confirm(review):
            with factory() as session:
                barrier.wait(timeout=5)
                try:
                    approve_and_execute_proposal(
                        session,
                        tenant.id,
                        review[0],
                        review_token=review[1],
                        confirmed=True,
                    )
                    return "executed"
                except InvalidOperation:
                    return "review_required"

        with ThreadPoolExecutor(max_workers=2) as workers:
            results = list(workers.map(confirm, reviews))
        assert sorted(results) == ["executed", "review_required"]
        with factory() as session:
            assert (
                session.scalar(
                    select(func.sum(Reservation.quantity)).where(
                        Reservation.tenant_id == tenant.id,
                        Reservation.item_id == item2.id,
                        Reservation.status == "active",
                    )
                )
                == 7
            )
    finally:
        engine.dispose()


def test_old_review_upgrade_and_empty_allocation_keep_existing_identity(
    session, business
):
    import json

    from reality.db.core import ChangeProposal, uid
    from reality.services.core import reserve
    from reality.services.delivery_actions import review_existing

    fixture = delivery_fixture(session, business)
    tid, cid = business.tenant.id, fixture.commitment.id
    proposal = ChangeProposal(
        id=uid("act"),
        tenant_id=tid,
        type="tool:reserve",
        actor_type="agent",
        status="proposed",
        input=json.dumps({"commitment_id": cid}),
        output="{}",
    )
    session.add(proposal)
    session.commit()
    with pytest.raises(InvalidOperation, match="review"):
        approve_and_execute_proposal(session, tid, proposal.id)
    original_id = proposal.id
    reviewed = review_existing(session, tid, proposal.id)
    assert reviewed.id == original_id
    assert json.loads(reviewed.input)["commitment_id"] == cid
    reserve(session, tid, cid, "12")
    empty = prepare_delivery_action(
        session, tid, "reserve", {"commitment_id": cid}, request_id="empty-allocation"
    )
    confirmed = approve_and_execute_proposal(
        session,
        tid,
        empty.id,
        review_token=json.loads(empty.input)["_delivery_review"]["token"],
        confirmed=True,
    )
    assert Decimal(json.loads(confirmed.output)["applied"]) == 0


def test_recorded_receipt_survives_observation_failure(session, business, monkeypatch):
    import json

    import reality.services.delivery_actions as actions

    fixture = delivery_fixture(session, business)
    tid, cid = business.tenant.id, fixture.commitment.id
    proposal = prepare_delivery_action(
        session,
        tid,
        "reserve",
        {"commitment_id": cid, "quantity": "12"},
        request_id="observation-failure",
    )
    approve_and_execute_proposal(
        session,
        tid,
        proposal.id,
        review_token=json.loads(proposal.input)["_delivery_review"]["token"],
        confirmed=True,
    )

    def unavailable(*args, **kwargs):
        raise InvalidOperation("Current observation unavailable")

    monkeypatch.setattr(actions, "delivery_case", unavailable)
    result = actions.delivery_proposal_detail(session, tid, proposal.id)
    assert result["status"] == "executed"
    assert result["verification"] == "verified"
    assert Decimal(result["receipt"]["applied"]) == 12
    assert result["observation"] is None
    assert result["observation_error"]


@pytest.mark.parametrize("change", ["hold", "revision", "correction"])
def test_direct_writer_changes_invalidate_exact_review(postgres_database, change):
    import json
    from types import SimpleNamespace

    from sqlalchemy.orm import sessionmaker

    from reality.db.core import Base, build_engine
    from reality.services.core import (
        correct_movement,
        create_item,
        create_location,
        create_party,
        create_tenant,
        hold_commitment,
        revise_commitment,
    )

    engine = build_engine(postgres_database)
    Base.metadata.create_all(engine)
    factory = sessionmaker(engine, expire_on_commit=False)
    try:
        with factory() as session:
            tenant = create_tenant(session, "Concurrent state changes")
            business = SimpleNamespace(
                tenant=tenant,
                company=create_party(session, tenant.id, "Company", "company"),
                customer=create_party(session, tenant.id, "Customer", "customer"),
                item=create_item(session, tenant.id, "LAMP", "Lamp"),
                location=create_location(session, tenant.id, "Warehouse"),
            )
            fixture = delivery_fixture(session, business)
            tid, cid = business.tenant.id, fixture.commitment.id
            proposal = prepare_delivery_action(
                session,
                tid,
                "reserve",
                {"commitment_id": cid, "quantity": "12"},
                request_id=f"stale-{change}",
            )
            token = json.loads(proposal.input)["_delivery_review"]["token"]
            from concurrent.futures import ThreadPoolExecutor
            from threading import Event

            from sqlalchemy.orm import sessionmaker

            from reality.services.business_locks import lock_delivery_state

            factory = sessionmaker(session.bind, expire_on_commit=False)
            started, completed = Event(), Event()

            def mutate():
                with factory() as writer_session:
                    started.set()
                    if change == "hold":
                        hold_commitment(writer_session, tid, cid, "manual_review")
                    elif change == "revision":
                        revise_commitment(
                            writer_session,
                            tid,
                            cid,
                            quantity="11",
                            note="Customer restated quantity",
                        )
                    else:
                        from sqlalchemy import select

                        from reality.db.core import Movement

                        opening = writer_session.scalar(
                            select(Movement).where(
                                Movement.tenant_id == tid,
                                Movement.item_id == business.item.id,
                            )
                        )
                        correct_movement(
                            writer_session,
                            tid,
                            opening.id,
                            reason="Opening count was incorrect",
                        )
                    completed.set()

            lock_delivery_state(session, tid)
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(mutate)
                assert started.wait(5)
                assert not completed.wait(0.15)
                session.rollback()
                future.result(timeout=5)
            with pytest.raises(InvalidOperation):
                approve_and_execute_proposal(
                    session, tid, proposal.id, review_token=token, confirmed=True
                )
            assert proposal.status == "proposed"
    finally:
        engine.dispose()


@pytest.mark.parametrize("release", ["rollback", "connection_loss"])
def test_transaction_guard_releases_on_rollback_and_blocks_direct_writer(
    postgres_database,
    release,
):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Event

    from sqlalchemy.orm import sessionmaker

    from reality.db.core import Base, build_engine
    from reality.services.business_locks import lock_delivery_state
    from reality.services.core import create_item, create_location, create_tenant

    engine = build_engine(postgres_database)
    Base.metadata.create_all(engine)
    factory = sessionmaker(engine, expire_on_commit=False)
    started, completed = Event(), Event()
    try:
        with factory() as setup:
            tenant = create_tenant(setup, "Rollback guard")
            item = create_item(setup, tenant.id, "LOCK", "Guard test")
            location = create_location(setup, tenant.id, "Warehouse")

        def writer():
            with factory() as session:
                started.set()
                result = record_movement(
                    session,
                    tenant.id,
                    "receipt",
                    item.id,
                    "1",
                    to_location_id=location.id,
                )
                completed.set()
                return result.id

        with factory() as held:
            lock_delivery_state(held, tenant.id)
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(writer)
                assert started.wait(5)
                assert not completed.wait(0.15)
                if release == "connection_loss":
                    held.connection().invalidate()
                held.rollback()
                assert future.result(timeout=5)
        with factory() as session:
            assert stock_at(session, tenant.id, item.id, location.id) == 1
    finally:
        engine.dispose()
