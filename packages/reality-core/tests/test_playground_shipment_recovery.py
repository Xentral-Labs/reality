"""097/FR-008: invalid shipments cannot strand an otherwise usable sandbox."""

import pytest
import test_playground_steps
from sqlalchemy import select
from sqlalchemy.orm import Session

from reality.db.core import (
    BusinessEvent,
    ChangeProposal,
    Movement,
    PlaygroundRun,
    PlaygroundStep,
)
from reality.services.core import Conflict, InvalidOperation
from reality.services.playground import (
    confirm_step,
    prepare_step,
    read_step,
    reject_step,
)

durable_playground = test_playground_steps.durable_playground
opening_arguments = test_playground_steps.opening_arguments


@pytest.fixture
def shipment_case(durable_playground):
    engine, owner, run_id = durable_playground

    def execute(key, tool, args):
        p = prepare_step(engine, owner, run_id, key, tool, args)
        return confirm_step(
            engine,
            owner,
            run_id,
            p["step_id"],
            p["preview"]["revision"],
            confirmed=True,
        )

    execute("stock", "movement_create", opening_arguments(engine, run_id))
    with Session(engine) as s:
        run = s.get(PlaygroundRun, run_id)
        tenant, refs = run.tenant_id, run.initialization_progress
    order = execute(
        "order",
        "order_create",
        {
            "direction": "sales",
            "number": "ONE",
            "quantity": "1",
            "unit_price": "25",
            "company_party_id": refs["parties"]["company"],
            "counterparty_id": refs["parties"]["customer_huber"],
            "item_id": refs["items"]["BIKE-LIGHT"],
            "location_id": refs["locations"]["warehouse"],
        },
    )
    commitment = next(
        r["id"] for r in order["receipt"]["records"] if r["family"] == "commitment"
    )
    args = {
        "movement_type": "shipment",
        "commitment_id": commitment,
        "item_id": refs["items"]["BIKE-LIGHT"],
        "from_location_id": refs["locations"]["warehouse"],
        "quantity": "12",
    }
    return engine, owner, run_id, tenant, args


def test_overdelivery_rejected_before_preparation(shipment_case):
    engine, owner, run, tenant, args = shipment_case
    with pytest.raises(InvalidOperation, match="open quantity"):
        prepare_step(engine, owner, run, "invalid", "movement_create", args)
    with Session(engine) as s:
        assert (
            s.scalar(
                select(ChangeProposal.id).where(
                    ChangeProposal.tenant_id == tenant,
                    ChangeProposal.status == "executing",
                )
            )
            is None
        )


@pytest.mark.parametrize("executing", [False, True])
def test_legacy_overdelivery_can_be_discarded_without_replay(
    shipment_case, monkeypatch, executing
):
    import reality.services.playground as pg

    engine, owner, run, tenant, args = shipment_case
    # Reproduce a preview created by the older release, without running the action.
    with monkeypatch.context() as m:
        m.setattr(pg, "validate_commitment_movement_quantity", lambda *a, **kw: None)
        preview = prepare_step(engine, owner, run, "legacy", "movement_create", args)
    if not executing:
        with pytest.raises(InvalidOperation, match="open quantity"):
            confirm_step(
                engine,
                owner,
                run,
                preview["step_id"],
                preview["preview"]["revision"],
                confirmed=True,
            )
    else:
        with Session(engine) as s:
            step = s.get(PlaygroundStep, preview["step_id"])
            p = s.get(ChangeProposal, step.proposal_id)
            step.before_observation = {"state": pg._shipment_state(s, tenant, args)}
            p.status = "executing"
            s.commit()
        with Session(engine) as s:
            assert read_step(s, owner, run, preview["step_id"])["can_discard"]
    result = reject_step(engine, owner, run, preview["step_id"], confirmed=True)
    assert result["status"] == "rejected"
    with Session(engine) as s:
        assert not list(
            s.scalars(
                select(Movement).where(
                    Movement.tenant_id == tenant,
                    Movement.commitment_id == args["commitment_id"],
                )
            )
        )
    valid = prepare_step(
        engine, owner, run, "corrected", "movement_create", {**args, "quantity": "1"}
    )
    assert valid["status"] == "proposed"


def test_unknown_execution_cannot_be_discarded(shipment_case):
    engine, owner, run, _tenant, args = shipment_case
    preview = prepare_step(
        engine, owner, run, "unknown", "movement_create", {**args, "quantity": "1"}
    )
    with Session(engine) as s:
        step = s.get(PlaygroundStep, preview["step_id"])
        p = s.get(ChangeProposal, step.proposal_id)
        p.status = "executing"
        step.before_observation = {"state": {"open_quantity": "1"}}
        s.commit()
    with pytest.raises(Conflict):
        reject_step(engine, owner, run, preview["step_id"], confirmed=True)


@pytest.mark.parametrize("evidence", ["event", "movement"])
def test_existing_effect_evidence_prevents_discard(
    shipment_case, monkeypatch, evidence
):
    import reality.services.playground as pg

    engine, owner, run, tenant, args = shipment_case
    with monkeypatch.context() as m:
        m.setattr(pg, "validate_commitment_movement_quantity", lambda *a, **kw: None)
        preview = prepare_step(engine, owner, run, "legacy", "movement_create", args)
    with Session(engine) as s:
        step = s.get(PlaygroundStep, preview["step_id"])
        proposal = s.get(ChangeProposal, step.proposal_id)
        proposal.status = "executing"
        step.before_observation = {"state": pg._shipment_state(s, tenant, args)}
        # Fixture evidence is deliberately ambiguous: it must prevent recovery.
        if evidence == "event":
            event = s.scalar(
                select(BusinessEvent).where(BusinessEvent.tenant_id == tenant)
            )
            event.action_id = proposal.id
        else:
            movement = s.scalar(select(Movement).where(Movement.tenant_id == tenant))
            movement.commitment_id = args["commitment_id"]
        s.commit()
    with Session(engine) as s:
        assert not read_step(s, owner, run, preview["step_id"])["can_discard"]
    with pytest.raises(Conflict):
        reject_step(engine, owner, run, preview["step_id"], confirmed=True)
