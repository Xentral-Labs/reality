import pytest
from conftest import record_by_id, seed_company
from sqlalchemy import func, select

from reality.db.core import ChangeProposal, PlaygroundRun
from reality.services import company_setup, core, demo_data, playground


def test_execution_is_fresh_unexecuted_and_uses_real_confirmation(
    session, scheduled_owner, monkeypatch
):
    actor = scheduled_owner.id
    baseline = company_setup.create_company(
        session,
        actor,
        "analysis",
        "Analysis",
        "sandbox",
        "international_demo",
        confirmed=True,
    )
    assert baseline["status"] == "initializing"
    assert seed_company(session, baseline["tenant_id"]) == "succeeded"
    execution = company_setup.create_execution(
        session, actor, "analysis", "execution", "Reservation practice", confirmed=True
    )
    assert execution["status"] == "ready", execution
    tenant, run_id = execution["tenant_id"], execution["run_id"]
    refs = record_by_id(session, PlaygroundRun, run_id).initialization_progress
    item, location = refs["items"]["P01"], refs["locations"]["A"]
    assert core.stock_at(session, tenant, item, location) == 1
    assert core.active_reserved(session, tenant, item, location) == 0
    assert (
        session.scalar(
            select(func.count())
            .select_from(ChangeProposal)
            .where(ChangeProposal.tenant_id == tenant)
        )
        == 0
    )
    with pytest.raises(core.InvalidOperation):
        demo_data.preview(session, tenant, actor)
    assert (
        company_setup.create_execution(
            session,
            actor,
            "analysis",
            "execution",
            "Reservation practice",
            confirmed=True,
        )["tenant_id"]
        == tenant
    )
    preview = playground.prepare_step(
        session.get_bind(),
        actor,
        run_id,
        "one-unit",
        "reserve",
        {"commitment_id": refs["cases"]["E01"]["commitment_id"], "quantity": "1"},
        db_session=session,
    )
    assert core.active_reserved(session, tenant, item, location) == 0
    result = playground.confirm_step(
        session.get_bind(),
        actor,
        run_id,
        preview["step_id"],
        preview["preview"]["revision"],
        confirmed=True,
        db_session=session,
    )
    assert result["status"] == "executed" and result["receipt"]
    assert core.stock_at(session, tenant, item, location) == 1
    assert core.active_reserved(session, tenant, item, location) == 1
    refusal = playground.prepare_step(
        session.get_bind(),
        actor,
        run_id,
        "held-unit",
        "reserve",
        {"commitment_id": refs["cases"]["E02"]["commitment_id"], "quantity": "1"},
        db_session=session,
    )
    denied = playground.confirm_step(
        session.get_bind(),
        actor,
        run_id,
        refusal["step_id"],
        refusal["preview"]["revision"],
        confirmed=True,
        db_session=session,
    )
    assert denied["status"] != "executed"
    fresh = company_setup.create_execution(
        session,
        actor,
        "analysis",
        "execution-fresh",
        "Fresh reservation practice",
        confirmed=True,
    )
    assert fresh["tenant_id"] not in {tenant, baseline["tenant_id"]}
    assert core.active_reserved(session, tenant, item, location) == 1
