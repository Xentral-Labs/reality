"""Reviewed single-record master data uses the production application tools."""

import pytest
import test_playground_steps
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from reality.db.core import BusinessEvent, Item, Location, Party, PlaygroundRun
from reality.services.core import Conflict, InvalidOperation, NotFound
from reality.services.playground import confirm_step, prepare_step, reject_step

durable_playground = test_playground_steps.durable_playground


def test_app_cannot_bypass_playground_confirmation_for_practice(durable_playground):
    from reality.services.tenant_policy import (
        PlaygroundOperationDenied,
        require_proposal_decision,
    )

    engine, owner, run_id = durable_playground
    with Session(engine) as session:
        run = session.get(PlaygroundRun, run_id)
        run.sandbox_kind = "practice"
        tenant_id = run.tenant_id
        session.commit()
    step = prepare_step(
        engine,
        owner,
        run_id,
        "app-boundary",
        "item_create",
        {"records": [{"name": "Reviewed", "sku": "REVIEWED", "unit": "pcs"}]},
    )
    with Session(engine) as session:
        from reality.db.core import PlaygroundStep

        proposal_id = session.get(PlaygroundStep, step["step_id"]).proposal_id
        with pytest.raises(PlaygroundOperationDenied):
            require_proposal_decision(
                session, tenant_id, proposal_id, "proposal_execute"
            )
    assert (
        confirm_step(
            engine,
            owner,
            run_id,
            step["step_id"],
            step["preview"]["revision"],
            confirmed=True,
        )["status"]
        == "executed"
    )


@pytest.mark.parametrize("tamper", ["name", "action", "tool"])
def test_master_exact_service_authority(durable_playground, monkeypatch, tamper):
    from dataclasses import replace

    from reality.tools import application

    engine, owner, run_id = durable_playground
    record = {"name": "Expected", "sku": "EXPECTED", "unit": "pcs"}
    step = prepare_step(
        engine, owner, run_id, "review", "item_create", {"records": [record]}
    )
    original = application.TOOLS["item_create"]

    def handler(session, tenant_id, arguments):
        from reality.services.core import create_items, create_locations

        if tamper == "name":
            arguments["records"][0]["name"] = "Unreviewed"
        if tamper == "action":
            arguments["_action_id"] = "wrong-action"
        if tamper == "tool":
            return create_locations(
                session,
                tenant_id,
                [{"name": "Wrong family", "type": "warehouse"}],
                action_id=arguments["_action_id"],
            )
        return create_items(
            session, tenant_id, arguments["records"], action_id=arguments["_action_id"]
        )

    monkeypatch.setitem(
        application.TOOLS, "item_create", replace(original, handler=handler)
    )
    result = confirm_step(
        engine,
        owner,
        run_id,
        step["step_id"],
        step["preview"]["revision"],
        confirmed=True,
    )
    assert result["status"] != "executed"
    with Session(engine) as session:
        tenant = session.get(PlaygroundRun, run_id).tenant_id
        assert (
            session.scalar(
                select(Item.id).where(Item.tenant_id == tenant, Item.sku == "EXPECTED")
            )
            is None
        )
        assert (
            session.scalar(
                select(Location.id).where(
                    Location.tenant_id == tenant, Location.name == "Wrong family"
                )
            )
            is None
        )


@pytest.mark.parametrize(
    "family,model,record",
    [
        (
            "party",
            Party,
            {"name": "New customer", "type": "customer", "roles": ["customer"]},
        ),
        ("item", Item, {"name": "New bell", "sku": "NEW-BELL", "unit": "pcs"}),
        ("location", Location, {"name": "New warehouse", "type": "warehouse"}),
    ],
)
def test_master_create_edit_review_and_stale(durable_playground, family, model, record):
    from reality.services.core import (
        create_items,
        create_locations,
        create_parties,
        create_tenant,
    )

    engine, owner, run_id = durable_playground
    with Session(engine) as session:
        tenant = session.get(PlaygroundRun, run_id).tenant_id
        initial = session.scalar(
            select(func.count()).select_from(model).where(model.tenant_id == tenant)
        )

    def prepare(key, mode, value):
        return prepare_step(
            engine, owner, run_id, key, f"{family}_{mode}", {"records": [value]}
        )

    def confirm(step):
        result = confirm_step(
            engine,
            owner,
            run_id,
            step["step_id"],
            step["preview"]["revision"],
            confirmed=True,
        )
        assert result["status"] == "executed", result
        assert result["receipt"] is not None
        return result

    rejected = prepare("reject", "create", record)
    reject_step(engine, owner, run_id, rejected["step_id"], confirmed=True)
    step = prepare("create", "create", record)
    with Session(engine) as session:
        assert (
            session.scalar(
                select(func.count()).select_from(model).where(model.tenant_id == tenant)
            )
            == initial
        )
    result = confirm(step)
    target = result["receipt"]["records"][0]["id"]
    assert result["receipt"]["event_ids"]
    confirm(step)
    with Session(engine) as session:
        assert (
            session.scalar(
                select(func.count()).select_from(model).where(model.tenant_id == tenant)
            )
            == initial + 1
        )
        preserved_field, preserved_value = {
            "party": ("accounting_code", "KEEP-42"),
            "item": ("lead_time_days", 7),
            "location": ("allows_stock", False),
        }[family]
        setattr(session.get(model, target), preserved_field, preserved_value)
        session.commit()
    changed = {**record, "id": target, "name": "Renamed"}
    stale = prepare("stale", "update", changed)
    winner = prepare("winner", "update", {**changed, "name": "Intermediate"})
    confirm(winner)
    with pytest.raises(Conflict):
        confirm(stale)
    reject_step(engine, owner, run_id, stale["step_id"], confirmed=True)
    confirm(prepare("edit", "update", changed))
    with Session(engine) as session:
        assert session.get(model, target).name == "Renamed"
        assert getattr(session.get(model, target), preserved_field) == preserved_value
        events = list(
            session.scalars(
                select(BusinessEvent).where(
                    BusinessEvent.tenant_id == tenant,
                    BusinessEvent.subject_id == target,
                )
            )
        )
        assert [event.event_type for event in events] == [
            f"{family}.created",
            f"{family}.updated",
            f"{family}.updated",
        ]
    with Session(engine) as session:
        other = create_tenant(session, "Unrelated company")
        foreign = {
            "party": create_parties,
            "item": create_items,
            "location": create_locations,
        }[family](session, other.id, [record])[0]
        foreign_id = foreign.id
    with pytest.raises(NotFound):
        prepare("foreign", "update", {**changed, "id": foreign_id})
    with Session(engine) as session:
        assert session.get(model, foreign_id).name == record["name"]
    with pytest.raises(InvalidOperation):
        prepare("extra", "create", {**record, "source_system": "external"})
