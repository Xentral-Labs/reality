"""Database-only notification reconciliation and existing shared queue lifecycle."""

from sqlalchemy import select
from test_operational_cases import activate, order

from reality.db.core import BusinessEvent
from reality.db.operational_cases import CaseConsumerCheckpoint, OperationalCase
from reality.services import core
from reality.services import operational_cases as cases
from reality.services import scheduled_jobs as jobs
from reality.services.case_jobs import due_case_tenants, enqueue_case_run


def test_checkpoint_rolls_back_with_case_membership_and_restarts(
    session, business, scheduled_owner
):
    activate(session, business, scheduled_owner)
    order(session, business)
    checkpoint = session.get(CaseConsumerCheckpoint, (business.tenant.id, 1))
    captured = checkpoint.incorporated_sequence
    with session.begin_nested() as savepoint:
        assert (
            cases.reconcile_events(session, business.tenant.id, limit=2, _commit=False)
            == 2
        )
        assert checkpoint.incorporated_sequence > captured
        savepoint.rollback()
    session.refresh(checkpoint)
    assert checkpoint.incorporated_sequence == captured
    while cases.reconcile_events(session, business.tenant.id, _commit=False):
        pass
    assert len(cases.list_cases(session, business.tenant.id)) == 1
    assert cases.reconcile_events(session, business.tenant.id, _commit=False) == 0


def test_unknown_and_self_events_advance_cursor_without_business_work(
    session, business, scheduled_owner
):
    activate(session, business, scheduled_owner)
    core.emit_business_event(
        session,
        business.tenant.id,
        "unknown.future",
        "commitment",
        "not-a-real-object",
        {},
    )
    session.flush()
    before = session.scalar(
        select(BusinessEvent.id)
        .where(BusinessEvent.tenant_id == business.tenant.id)
        .order_by(BusinessEvent.sequence.desc())
        .limit(1)
    )
    cases.reconcile_events(session, business.tenant.id)
    assert session.scalar(select(OperationalCase)) is None
    assert (
        session.scalar(
            select(BusinessEvent.id)
            .where(BusinessEvent.tenant_id == business.tenant.id)
            .order_by(BusinessEvent.sequence.desc())
            .limit(1)
        )
        == before
    )


def test_shared_scheduler_discovers_deduplicates_and_worker_consumes(
    session, business, scheduled_owner
):
    activate(session, business, scheduled_owner)
    order(session, business)
    assert business.tenant.id in due_case_tenants(session)
    assert business.tenant.id in jobs.scheduler_tenants(session)
    run = enqueue_case_run(session, business.tenant.id)
    assert run.job_type == "operational_cases.reconcile"
    assert run.actor_id is None
    assert enqueue_case_run(session, business.tenant.id) is None
    claim = jobs.claim_next(session, business.tenant.id)
    assert claim.id == run.id
    jobs.execute_claim(session, business.tenant.id, run.id, claim.claim_token)
    session.flush()
    assert run.status == "succeeded"
    assert due_case_tenants(session) == []
    assert enqueue_case_run(session, business.tenant.id) is None


def test_default_company_needs_no_adoption_for_coordination(session, business):
    assert business.tenant.id in due_case_tenants(session)
    assert enqueue_case_run(session, business.tenant.id) is not None
    assert cases.reconcile_events(session, business.tenant.id) == 0
    assert business.tenant.id not in due_case_tenants(session)
