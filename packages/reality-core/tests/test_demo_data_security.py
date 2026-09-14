import pytest

from reality.services import company_setup
from reality.services.core import InvalidOperation


def test_demo_cannot_be_ordinary_or_unconfirmed(session, scheduled_owner):
    with pytest.raises(InvalidOperation):
        company_setup.create_company(
            session,
            scheduled_owner.id,
            "invalid-demo",
            "Acme",
            "business",
            "international_demo",
            confirmed=True,
        )
    with pytest.raises(InvalidOperation):
        company_setup.create_company(
            session,
            scheduled_owner.id,
            "unconfirmed",
            "Acme",
            "sandbox",
            "empty",
            confirmed=False,
        )


def test_profile_scope_refuses_cross_tenant_and_commit(
    session, scheduled_owner, business, monkeypatch
):
    from reality.db.core import PlaygroundRun
    from reality.services.core import create_item
    from reality.services.tenant_policy import PlaygroundOperationDenied, _profile_scope

    monkeypatch.setenv("REALITY_PLAYGROUND_ENABLED", "true")
    result = company_setup.create_company(
        session, scheduled_owner.id, "scope", "Demo", "sandbox", "empty", confirmed=True
    )
    run = session.get(PlaygroundRun, result["run_id"])
    run.preset_key, run.status = "international-demo", "initializing"
    session.flush()
    with _profile_scope(session, run.id, scheduled_owner.id):
        with pytest.raises(PlaygroundOperationDenied):
            create_item(
                session, business.tenant.id, "forbidden", "Forbidden", _commit=False
            )
        with pytest.raises(PlaygroundOperationDenied):
            session.commit()
    session.rollback()


def test_all_demo_connection_boundaries_refuse_foreign_scope(
    session, scheduled_owner, monkeypatch
):
    from reality.services import demo_data
    from reality.services.core import RealityError

    monkeypatch.setenv("REALITY_PLAYGROUND_ENABLED", "true")
    actor = scheduled_owner.id
    operations = [
        lambda: demo_data.eligible(session, "foreign", actor),
        lambda: demo_data.preview(session, "foreign", actor),
        lambda: demo_data.connect(
            session, "foreign", actor, "foreign", "x" * 64, confirmed=True
        ),
        lambda: demo_data.control(
            session, "foreign", actor, "start", 1, "foreign", confirmed=True
        ),
        lambda: demo_data.status(session, "foreign", actor),
        lambda: demo_data.imports(session, "foreign", actor),
        lambda: demo_data.read_import(session, "foreign", actor, "foreign"),
        lambda: demo_data.retry_import(
            session, "foreign", actor, "foreign", confirmed=True
        ),
    ]
    for operation in operations:
        with pytest.raises(RealityError):
            operation()
    with pytest.raises(RealityError), demo_data.intake_scope(session, "foreign", actor):
        pytest.fail("Foreign intake scope entered")


def test_bound_import_refuses_foreign_job(session, business):
    from reality.services import core

    _source, job = core.enqueue_source(
        session,
        business.tenant.id,
        "demo_data",
        "order",
        "foreign-bound",
        {},
        _commit=False,
    )
    with pytest.raises(core.NotFound):
        core.process_import_job_bound(session, "foreign", job.id)


@pytest.mark.parametrize(
    "restriction", ["archived", "initializing", "execution", "revoked", "suspended"]
)
def test_demo_rechecks_current_owner_and_profile(
    session, scheduled_owner, monkeypatch, restriction
):
    from sqlalchemy import select

    from reality.db.core import PlaygroundRun, TenantMembership
    from reality.services import demo_data
    from reality.services.core import RealityError

    monkeypatch.setenv("REALITY_PLAYGROUND_ENABLED", "true")
    actor = scheduled_owner.id
    result = company_setup.create_company(
        session,
        actor,
        f"restricted-{restriction}",
        "Restricted",
        "sandbox",
        "empty",
        confirmed=True,
    )
    run = session.get(PlaygroundRun, result["run_id"])
    if restriction == "archived":
        from reality.db.core import now

        run.status = "archived"
        run.archived_at = now()
    elif restriction == "initializing":
        run.status = restriction
    elif restriction == "execution":
        run.preset_key = "atlas-execution"
    elif restriction == "revoked":
        membership = session.scalar(
            select(TenantMembership).where(
                TenantMembership.tenant_id == run.tenant_id,
                TenantMembership.user_id == actor,
            )
        )
        session.delete(membership)
    else:
        scheduled_owner.status = "suspended"
    session.flush()
    with pytest.raises(RealityError):
        demo_data.preview(session, run.tenant_id, actor)


def test_order_scope_cannot_post_money_and_settlement_scope_is_bounded(
    session, scheduled_owner, business, monkeypatch
):
    """Feature 168 FR-021: two authorities, neither accepts the other's work."""
    from sqlalchemy import select

    from reality.db.core import Party
    from reality.services import core, demo_data
    from reality.services.tenant_policy import (
        PlaygroundOperationDenied,
        require_demo_intake,
    )

    monkeypatch.setenv("REALITY_PLAYGROUND_ENABLED", "true")
    actor = scheduled_owner.id
    tenant = company_setup.create_company(
        session, actor, "money-scope", "Money", "sandbox", "empty", confirmed=True
    )["tenant_id"]
    demo_data.connect(
        session,
        tenant,
        actor,
        "money-connect",
        demo_data.preview(session, tenant, actor)["fingerprint"],
        confirmed=True,
    )
    customer = session.scalar(
        select(Party).where(Party.tenant_id == tenant, Party.type == "customer")
    )
    money = (
        lambda: core.record_customer_payment(
            session, tenant, customer.id, "10", _commit=False
        ),
        lambda: core.post_ledger(
            session,
            tenant,
            None,
            customer.id,
            [("cash", "debit", "1"), ("accounts_receivable", "credit", "1")],
            _commit=False,
        ),
    )
    with demo_data.intake_scope(session, tenant, actor):
        require_demo_intake(session, tenant)
        with pytest.raises(PlaygroundOperationDenied):
            require_demo_intake(session, tenant, settlement=True)
        for attempt in money:
            with pytest.raises(PlaygroundOperationDenied):
                attempt()
    with demo_data.settlement_scope(session, tenant, actor):
        require_demo_intake(session, tenant, settlement=True)
        with pytest.raises(PlaygroundOperationDenied):
            require_demo_intake(session, tenant)
        entries = money[0]()
        assert {entry.account for entry in entries} == {"cash", "accounts_receivable"}
        # Nothing beyond recording and allocating: no reductions, credits, refunds,
        # reservations or movements.
        with pytest.raises(PlaygroundOperationDenied):
            core.record_customer_refund(
                session, tenant, customer.id, "1", _commit=False
            )
        with pytest.raises(PlaygroundOperationDenied):
            core.create_party(session, tenant, "Intruder", "customer", _commit=False)
        with pytest.raises(PlaygroundOperationDenied):
            session.commit()
    session.rollback()
    # Ordinary tenants and non-owners never receive the settlement authority.
    with (
        pytest.raises(PlaygroundOperationDenied),
        demo_data.settlement_scope(session, business.tenant.id, actor),
    ):
        pass


def test_settlement_job_authorization_is_bound_to_its_schedule(
    session, scheduled_owner, monkeypatch
):
    """Feature 168 FR-021: the settlement occurrence re-checks owner, connection and schedule."""
    from datetime import timedelta

    from reality.db.core import now
    from reality.db.scheduled_jobs import ScheduledJob, ScheduledJobRun
    from reality.jobs.handlers.demo_data import SettleConfig, authorize_settle
    from reality.jobs.registry import JobContext, JobError
    from reality.services import demo_data

    monkeypatch.setenv("REALITY_PLAYGROUND_ENABLED", "true")
    actor = scheduled_owner.id
    tenant = company_setup.create_company(
        session, actor, "settle-auth", "Auth", "sandbox", "empty", confirmed=True
    )["tenant_id"]
    connected = demo_data.connect(
        session,
        tenant,
        actor,
        "c",
        demo_data.preview(session, tenant, actor)["fingerprint"],
        confirmed=True,
    )
    started = demo_data.control(
        session, tenant, actor, "start", connected["revision"], "s", confirmed=True
    )
    settlement = session.get(ScheduledJob, started["settlement_schedule_id"])
    config = SettleConfig(**settlement.configuration["arguments"])

    def context(run_id):
        return JobContext(tenant, actor, run_id, None, now() + timedelta(minutes=1))

    authorize_settle(session, context(None), config)
    with pytest.raises(JobError) as wrong_connection:
        authorize_settle(
            session, context(None), config.model_copy(update={"connection_id": "ddc_x"})
        )
    assert wrong_connection.value.code == "not_authorized"
    with pytest.raises(JobError) as wrong_references:
        authorize_settle(
            session,
            context(None),
            config.model_copy(update={"references": {"items": {"P01": "itm_other"}}}),
        )
    assert wrong_references.value.code == "incompatible_references"
    from sqlalchemy import select

    from reality.services import scheduled_jobs

    order_schedule = session.get(ScheduledJob, started["schedule_id"])
    for schedule in (order_schedule, settlement):
        schedule.next_run_at = now() - timedelta(seconds=1)
    session.flush()
    for _ in (order_schedule, settlement):  # one occurrence per sweep
        scheduled_jobs.materialize_due(session, tenant)
    runs = {
        run.schedule_id: run
        for run in session.scalars(
            select(ScheduledJobRun).where(ScheduledJobRun.tenant_id == tenant)
        )
    }
    with pytest.raises(JobError) as wrong_schedule:
        authorize_settle(session, context(runs[order_schedule.id].id), config)
    assert wrong_schedule.value.code == "inactive_connection"
    authorize_settle(session, context(runs[settlement.id].id), config)
    settle_run = runs[settlement.id]
    demo_data.control(
        session, tenant, actor, "pause", started["revision"], "p", confirmed=True
    )
    with pytest.raises(JobError) as paused:
        authorize_settle(session, context(settle_run.id), config)
    assert paused.value.code == "inactive_connection"
