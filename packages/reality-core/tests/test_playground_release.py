"""Independent release uses the shared reservation tool and exact review."""

import pytest
import test_playground_steps
from sqlalchemy import select
from sqlalchemy.orm import Session

from reality.db.core import BusinessEvent, PlaygroundRun, Reservation
from reality.services.core import (
    Conflict,
    InvalidOperation,
    NotFound,
    open_quantity,
    stock_at,
)
from reality.services.playground import confirm_step, prepare_step, reject_step

durable_playground = test_playground_steps.durable_playground


def test_release_authority_rejects_another_target(monkeypatch):
    from types import SimpleNamespace

    from reality.services import tenant_policy

    monkeypatch.setattr(
        tenant_policy,
        "_current_decision",
        lambda *args: SimpleNamespace(
            proposal_id="proposal", intent='{"reservation_id":"expected"}'
        ),
    )
    with pytest.raises(tenant_policy.PlaygroundOperationDenied):
        tenant_policy.require_decision_release(None, "tenant", "other", "proposal")
    with pytest.raises(tenant_policy.PlaygroundOperationDenied):
        tenant_policy.require_decision_release(
            None, "tenant", "expected", "other-proposal"
        )


def test_reviewed_release_preserves_stock_and_obligation(durable_playground):
    engine, owner, run_id = durable_playground
    with Session(engine) as session:
        run = session.get(PlaygroundRun, run_id)
        tenant, refs = run.tenant_id, run.initialization_progress
    item, location = refs["items"]["BIKE-LIGHT"], refs["locations"]["warehouse"]
    with pytest.raises(NotFound):
        prepare_step(
            engine,
            owner,
            run_id,
            "foreign",
            "reservation_release",
            {"reservation_id": "res_other_tenant"},
        )

    def execute(key, tool, args):
        step = prepare_step(engine, owner, run_id, key, tool, args)
        return confirm_step(
            engine,
            owner,
            run_id,
            step["step_id"],
            step["preview"]["revision"],
            confirmed=True,
        )

    execute(
        "stock",
        "movement_create",
        {
            "movement_type": "opening_stock",
            "item_id": item,
            "to_location_id": location,
            "quantity": "10",
        },
    )
    order = execute(
        "order",
        "order_create",
        {
            "direction": "sales",
            "number": "RELEASE-1",
            "company_party_id": refs["parties"]["company"],
            "counterparty_id": refs["parties"]["customer_huber"],
            "item_id": item,
            "location_id": location,
            "quantity": "4",
            "unit_price": "10",
        },
    )
    commitment = next(
        row["id"]
        for row in order["receipt"]["records"]
        if row["family"] == "commitment"
    )
    reserved = execute(
        "reserve", "reserve", {"commitment_id": commitment, "quantity": "4"}
    )
    reservation = reserved["receipt"]["records"][0]["id"]
    rejected = prepare_step(
        engine,
        owner,
        run_id,
        "reject-release",
        "reservation_release",
        {"reservation_id": reservation},
    )
    reject_step(engine, owner, run_id, rejected["step_id"], confirmed=True)
    with Session(engine) as session:
        assert session.get(Reservation, reservation).status == "active"
    step = prepare_step(
        engine,
        owner,
        run_id,
        "release",
        "reservation_release",
        {"reservation_id": reservation},
    )
    with Session(engine) as session:
        assert session.get(Reservation, reservation).status == "active"
    result = confirm_step(
        engine,
        owner,
        run_id,
        step["step_id"],
        step["preview"]["revision"],
        confirmed=True,
    )
    assert result["status"] == "executed"
    assert result["receipt"]["after"]["status"] == "released"
    assert result["receipt"]["event_ids"]
    confirm_step(
        engine,
        owner,
        run_id,
        step["step_id"],
        step["preview"]["revision"],
        confirmed=True,
    )
    with Session(engine) as session:
        assert stock_at(session, tenant, item, location) == 10
        assert open_quantity(session, tenant, commitment) == 4
        events = list(
            session.scalars(
                select(BusinessEvent).where(
                    BusinessEvent.tenant_id == tenant,
                    BusinessEvent.event_type == "reservation.released",
                )
            )
        )
        assert len(events) == 1
    with pytest.raises((InvalidOperation, Conflict)):
        prepare_step(
            engine,
            owner,
            run_id,
            "released-again",
            "reservation_release",
            {"reservation_id": reservation},
        )
    second = execute(
        "reserve-two", "reserve", {"commitment_id": commitment, "quantity": "2"}
    )
    target = second["receipt"]["records"][0]["id"]
    stale = prepare_step(
        engine,
        owner,
        run_id,
        "stale-review",
        "reservation_release",
        {"reservation_id": target},
    )
    execute("winning-review", "reservation_release", {"reservation_id": target})
    with pytest.raises(Conflict):
        confirm_step(
            engine,
            owner,
            run_id,
            stale["step_id"],
            stale["preview"]["revision"],
            confirmed=True,
        )
