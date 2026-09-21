from datetime import UTC, datetime, timedelta

from conftest import record_by_id
from sqlalchemy import func, select

from reality.db.core import SourceRecord
from reality.db.scheduled_jobs import ScheduledJob
from reality.services import company_setup, demo_data
from reality.services import scheduled_jobs as jobs


def test_confirmed_live_setup_starts_three_orders_even_when_random_demand_is_zero(
    session, scheduled_owner, monkeypatch
):
    clock = [datetime.now(UTC) + timedelta(minutes=5)]
    monkeypatch.setattr(jobs, "now", lambda: clock[0])
    monkeypatch.setattr("reality.integrations.demo_data.burst_size", lambda *args: 0)
    result = company_setup.create_company(
        session,
        scheduled_owner.id,
        "fast-live",
        "Fast demo",
        "sandbox",
        "international_demo",
        _initialize_inline=True,
        live_simulation=True,
        confirmed=True,
    )
    tenant = result["tenant_id"]
    status = demo_data.status(session, tenant, scheduled_owner.id)
    schedule = record_by_id(session, ScheduledJob, status["schedule_id"])
    anchor = clock[0]
    assert schedule.next_run_at == anchor
    for offset in [0, 12, 24]:
        clock[0] = anchor + timedelta(seconds=offset)
        assert jobs.materialize_due(session, tenant) == 1
        run = jobs.claim_next(session, tenant)
        assert (
            jobs.execute_claim(session, tenant, run.id, run.claim_token) == "succeeded"
        )
        assert run.result["counts"]["imported"] == 1
        assert (
            jobs.execute_claim(session, tenant, run.id, run.claim_token or "expired")
            == "succeeded"
        )
    assert demo_data.status(session, tenant, scheduled_owner.id)["imported"] == 3
    assert schedule.next_run_at == anchor + timedelta(seconds=84)
    # The settlement stream becomes due at 60; drain it before the next order.
    clock[0] = anchor + timedelta(seconds=84)
    for _ in range(2):
        assert jobs.materialize_due(session, tenant) == 1
        run = jobs.claim_next(session, tenant)
        assert (
            jobs.execute_claim(session, tenant, run.id, run.claim_token) == "succeeded"
        )
    assert (
        session.scalar(
            select(func.count())
            .select_from(SourceRecord)
            .where(
                SourceRecord.tenant_id == tenant,
                SourceRecord.source_type == "order",
                SourceRecord.source_system == "demo_data",
            )
        )
        == 3
    )
    repeated = company_setup.create_company(
        session,
        scheduled_owner.id,
        "fast-live",
        "Fast demo",
        "sandbox",
        "international_demo",
        _initialize_inline=True,
        live_simulation=True,
        confirmed=True,
    )
    assert repeated["tenant_id"] == tenant
    assert (
        demo_data.status(session, tenant, scheduled_owner.id)["schedule_id"]
        == schedule.id
    )
