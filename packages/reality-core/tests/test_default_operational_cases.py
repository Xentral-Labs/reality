"""Default coordination, resumable upgrade and truthful internal authority."""

import json

import pytest
from sqlalchemy import select
from test_operational_cases import order

from reality.db.core import (
    BusinessEvent,
    ChangeProposal,
    Commitment,
    Document,
    DocumentLine,
    LedgerEntry,
    Movement,
    Reservation,
    SourceRecord,
)
from reality.db.operational_cases import CaseAdoption, OperationalCase
from reality.services import core
from reality.services import operational_cases as cases
from reality.services import scheduled_jobs as jobs
from reality.services.case_jobs import due_case_tenants, enqueue_case_run


def test_ordinary_accepted_order_has_one_case_without_activation(session, business):
    commitment = order(session, business)
    core.create_commitment(
        session,
        business.tenant.id,
        "customer_delivery",
        business.company.id,
        business.customer.id,
        business.item.id,
        business.location.id,
        "1",
        None,
        document_id=commitment.document_id,
    )
    rows = cases.list_cases(session, business.tenant.id)
    assert len(rows) == 1
    assert rows[0]["order_document_id"] == commitment.document_id
    assert len(rows[0]["work"]) == 2
    assert session.get(CaseAdoption, business.tenant.id) is None
    assert not list(
        session.scalars(
            select(ChangeProposal).where(ChangeProposal.type == "case:adopt")
        )
    )


def test_no_owner_company_is_discovered_and_internal_job_completes(session, business):
    tenant_id = business.tenant.id
    assert tenant_id in due_case_tenants(session)
    run = enqueue_case_run(session, tenant_id)
    assert run is not None
    assert run.actor_id is None
    assert run.schedule_id is None
    assert enqueue_case_run(session, tenant_id) is None
    claim = jobs.claim_next(session, tenant_id)
    jobs.execute_claim(session, tenant_id, run.id, claim.claim_token)
    assert run.status == "succeeded"
    assert cases.coordination_status(session, tenant_id)["coverage_ready"]
    assert tenant_id not in due_case_tenants(session)


def test_backfill_rollback_retry_preserves_business_records(session, business):
    from reality.db.operational_cases import (
        CaseCommitmentLink,
        CaseProposalLink,
        CaseRollout,
    )

    tenant_id = business.tenant.id
    order(session, business)
    # Reproduce an upgraded pre-feature company using only test-owned coordination cleanup.
    session.query(CaseProposalLink).filter_by(tenant_id=tenant_id).delete()
    session.query(CaseCommitmentLink).filter_by(tenant_id=tenant_id).delete()
    session.query(OperationalCase).filter_by(tenant_id=tenant_id).delete()
    session.flush()
    before = {
        model: [
            (row.id, tuple(getattr(row, c.name) for c in model.__table__.columns))
            for row in session.scalars(
                select(model).where(model.tenant_id == tenant_id)
            )
        ]
        for model in (
            Commitment,
            Movement,
            Reservation,
            LedgerEntry,
            Document,
            DocumentLine,
            SourceRecord,
            BusinessEvent,
            ChangeProposal,
        )
    }
    with session.begin_nested() as savepoint:
        cases.reconcile_events(session, tenant_id, limit=1, _commit=False)
        assert len(cases.list_cases(session, tenant_id)) == 1
        assert not cases.coordination_status(session, tenant_id)["coverage_ready"]
        savepoint.rollback()
    assert cases.list_cases(session, tenant_id) == []
    for _ in range(100):
        cases.reconcile_events(session, tenant_id, limit=1, _commit=False)
        if cases.coordination_status(session, tenant_id)["coverage_ready"]:
            break
    assert cases.coordination_status(session, tenant_id)["coverage_ready"]
    identity = cases.list_cases(session, tenant_id)[0]["case_id"]
    cases.reconcile_events(session, tenant_id, limit=1, _commit=False)
    assert cases.list_cases(session, tenant_id)[0]["case_id"] == identity
    rollout = session.get(CaseRollout, tenant_id)
    assert rollout.version == 377
    for model, expected in before.items():
        assert [
            (row.id, tuple(getattr(row, c.name) for c in model.__table__.columns))
            for row in session.scalars(
                select(model).where(model.tenant_id == tenant_id)
            )
        ] == expected


def test_internal_job_cannot_be_selected_by_public_owner(
    session, business, scheduled_owner
):
    with pytest.raises(jobs.JobError, match="not_authorized"):
        jobs.create_manual_run(
            session,
            business.tenant.id,
            scheduled_owner.id,
            "operational_cases.reconcile",
            {"limit": 100},
            request_id="public-case",
        )


def _historical_coordination_cleanup(session, tenant_id):
    from reality.db.operational_cases import CaseCommitmentLink, CaseProposalLink

    session.query(CaseProposalLink).filter_by(tenant_id=tenant_id).delete()
    session.query(CaseCommitmentLink).filter_by(tenant_id=tenant_id).delete()
    session.query(OperationalCase).filter_by(tenant_id=tenant_id).delete()
    session.flush()


def _promise(session, business, number, quantity="3"):
    doc = core.create_document(
        session, business.tenant.id, "sales_order", number, business.customer.id, "0"
    )
    return core.create_commitment(
        session,
        business.tenant.id,
        "customer_delivery",
        business.company.id,
        business.customer.id,
        business.item.id,
        business.location.id,
        quantity,
        None,
        document_id=doc.id,
    )


def test_upgrade_selects_only_outstanding_orders_and_open_returns(session, business):
    tenant = business.tenant.id
    opened = _promise(session, business, "OPEN")
    partial = _promise(session, business, "PARTIAL")
    completed = _promise(session, business, "DONE")
    cancelled = _promise(session, business, "CANCEL")
    core.record_movement(
        session,
        tenant,
        "opening_stock",
        business.item.id,
        "20",
        to_location_id=business.location.id,
    )
    core.record_movement(
        session,
        tenant,
        "shipment",
        business.item.id,
        "1",
        from_location_id=business.location.id,
        commitment_id=partial.id,
    )
    core.record_movement(
        session,
        tenant,
        "shipment",
        business.item.id,
        "3",
        from_location_id=business.location.id,
        commitment_id=completed.id,
    )
    core.cancel_commitment(session, tenant, cancelled.id, reason="Withdrawn")
    opened_return = core.announce_customer_return(session, tenant, partial.id, "1")
    closed_return = core.announce_customer_return(session, tenant, completed.id, "1")
    core.withdraw_return_announcement(
        session, tenant, closed_return.id, note="Withdrawn"
    )
    _historical_coordination_cleanup(session, tenant)
    assert cases.list_cases(session, tenant) == []
    assert not cases.coordination_status(session, tenant)["coverage_ready"]
    for _ in range(10):
        cases.reconcile_events(session, tenant, limit=2, _commit=False)
        if cases.coordination_status(session, tenant)["coverage_ready"]:
            break
    rows = cases.list_cases(session, tenant)
    assert {
        row["order_document_id"] for row in rows if row["kind"] == "order_fulfillment"
    } == {opened.document_id, partial.document_id}
    assert {
        row["return_announcement_id"]
        for row in rows
        if row["kind"] == "customer_return"
    } == {opened_return.id}
    # Correction of excluded completed history creates coverage immediately.
    shipment = session.scalar(
        select(Movement).where(
            Movement.tenant_id == tenant,
            Movement.commitment_id == completed.id,
            Movement.type == "shipment",
        )
    )
    core.correct_movement(
        session,
        tenant,
        shipment.id,
        reason="Received correction",
        replacement={
            "type": "shipment",
            "item_id": business.item.id,
            "quantity": "1",
            "from_location_id": business.location.id,
            "commitment_id": completed.id,
        },
    )
    assert len(cases.object_cases(session, tenant, "commitment", completed.id)) == 1


def test_rollout_preserves_manual_revision_binding_and_uncertain_execution(
    session, business, scheduled_owner
):
    from reality.db.operational_cases import CaseProposalLink
    from reality.services.case_action_guards import automated_execution
    from reality.services.memberships import Principal

    tenant = business.tenant.id
    promise = order(session, business)
    case_id = cases.object_cases(session, tenant, "commitment", promise.id)[0]
    action = ChangeProposal(
        id="act_retained",
        tenant_id=tenant,
        type="tool:shipment_dispatch",
        status="executing",
        input="{}",
        output='{"unknown": true}',
    )
    session.add(action)
    session.flush()
    cases.bind_proposal(session, tenant, action.id, [case_id])
    actor = Principal(scheduled_owner.id)
    cases.takeover(
        session,
        tenant,
        case_id,
        actor,
        expected_revision=1,
        request_key="retained-manual",
        confirmed=True,
    )
    before = cases.handback_preview(session, tenant, case_id)
    binding = session.get(CaseProposalLink, (tenant, case_id, action.id))
    bound_revision = binding.bound_control_revision
    cases.reconcile_events(session, tenant)
    assert (
        cases.handback_preview(session, tenant, case_id)["digest"] == before["digest"]
    )
    assert binding.bound_control_revision == bound_revision
    assert action.output == '{"unknown": true}' and action.status == "executing"
    assert cases.explain(session, tenant, case_id)["control_revision"] == 2
    with (
        automated_execution(session, tenant),
        pytest.raises(core.InvalidOperation) as error,
    ):
        core.cancel_commitment(session, tenant, promise.id, reason="Agent attempt")
    assert error.value.code == "case_human_owned"
    with pytest.raises(core.InvalidOperation) as error:
        cases.handback(
            session,
            tenant,
            case_id,
            actor,
            review_digest=before["digest"],
            request_key="uncertain-back",
            confirmed=True,
        )
    assert error.value.code == "case_execution_unresolved"


def test_legacy_pending_business_proposal_requires_fresh_review(session, business):
    from reality.services.case_action_guards import guard_proposal

    tenant = business.tenant.id
    promise = order(session, business)
    legacy = ChangeProposal(
        id="act_legacy",
        tenant_id=tenant,
        type="tool:commitment_revise",
        actor_type="agent",
        status="proposed",
        input='{"commitment_id": "' + promise.id + '", "quantity": "2"}',
        output="{}",
    )
    session.add(legacy)
    session.flush()
    with pytest.raises(core.InvalidOperation) as error:
        guard_proposal(session, tenant, legacy.id, automatic=True)
    assert error.value.code == "case_review_stale"
    assert legacy.status == "proposed" and legacy.output == "{}"


def test_legacy_acknowledgement_retries_never_reset_ownership(
    session, business, scheduled_owner
):
    from reality.services.memberships import Principal

    tenant = business.tenant.id
    promise = order(session, business)
    case_id = cases.object_cases(session, tenant, "commitment", promise.id)[0]
    actor = Principal(scheduled_owner.id)
    cases.takeover(
        session,
        tenant,
        case_id,
        actor,
        expected_revision=1,
        request_key="legacy-control",
        confirmed=True,
    )
    for _ in range(2):
        result = cases.adopt(
            session,
            tenant,
            actor,
            confirmed=True,
            request_key="legacy-enable",
            order_ids=[promise.document_id],
        )
        assert result["adopted"] and not result["can_adopt"]
    assert session.get(CaseAdoption, tenant) is None
    assert cases.explain(session, tenant, case_id)["control_revision"] == 2
    assert cases.explain(session, tenant, case_id)["control_mode"] == "human"
    other = core.create_tenant(session, "Other company")
    with pytest.raises(core.NotFound):
        cases.ensure_commitment(session, other.id, promise.id)


def test_concurrent_backfill_and_canonical_acceptance_share_one_anchor(
    postgres_database,
):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier

    from conftest import business as business_fixture
    from sqlalchemy import create_engine, func
    from sqlalchemy.orm import Session

    from reality.db.core import Base
    from reality.db.operational_cases import CaseCommitmentLink

    engine = create_engine(postgres_database)
    Base.metadata.create_all(engine)
    try:
        with Session(engine, expire_on_commit=False) as setup:
            business = business_fixture.__wrapped__(setup)
            promise = _promise(setup, business, "CONCURRENT")
            tenant, doc_id = business.tenant.id, promise.document_id
            _historical_coordination_cleanup(setup, tenant)
            setup.commit()
        barrier = Barrier(2)

        def backfill():
            with Session(engine) as db:
                barrier.wait(timeout=5)
                cases.reconcile_events(db, tenant, limit=1)

        def accept():
            with Session(engine) as db:
                barrier.wait(timeout=5)
                core.create_commitment(
                    db,
                    tenant,
                    "customer_delivery",
                    business.company.id,
                    business.customer.id,
                    business.item.id,
                    business.location.id,
                    "2",
                    None,
                    document_id=doc_id,
                )

        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(backfill), pool.submit(accept)]
            for future in futures:
                future.result(timeout=20)
        with Session(engine) as check:
            for _ in range(20):
                cases.reconcile_events(check, tenant, limit=1)
                if cases.coordination_status(check, tenant)["coverage_ready"]:
                    break
            assert cases.coordination_status(check, tenant)["coverage_ready"]
            rows = cases.list_cases(check, tenant)
            assert len(rows) == 1 and rows[0]["order_document_id"] == doc_id
            assert (
                check.scalar(
                    select(func.count())
                    .select_from(CaseCommitmentLink)
                    .where(CaseCommitmentLink.tenant_id == tenant)
                )
                == 2
            )
    finally:
        engine.dispose()


def test_internal_recovery_retains_failed_run_and_restarts_without_owner(
    session, business
):
    tenant = business.tenant.id
    first = enqueue_case_run(session, tenant)
    first.status = "failed"
    first.last_error_code = "child_exited"
    session.flush()
    recovered = enqueue_case_run(session, tenant)
    assert recovered.id != first.id and recovered.actor_id is None
    assert first.status == "failed" and first.last_error_code == "child_exited"
    claimed = jobs.claim_next(session, tenant)
    assert claimed.id == recovered.id
    jobs.execute_claim(session, tenant, claimed.id, claimed.claim_token)
    assert cases.coordination_status(session, tenant)["coverage_ready"]


def test_archived_company_and_foreign_internal_context_are_refused(session, business):
    from datetime import timedelta

    from reality.db.core import now
    from reality.jobs.handlers.operational_cases import CaseConfig, authorize
    from reality.jobs.registry import JobContext

    tenant = business.tenant.id
    run = enqueue_case_run(session, tenant)
    foreign = core.create_tenant(session, "Foreign internal context")
    with pytest.raises(jobs.JobError, match="not_authorized"):
        authorize(
            session,
            JobContext(foreign.id, None, run.id, None, now() + timedelta(seconds=30)),
            CaseConfig(),
        )
    business.tenant.archived_at = now()
    session.flush()
    assert tenant not in due_case_tenants(session)
    assert enqueue_case_run(session, tenant) is None
    with pytest.raises(jobs.JobError, match="not_authorized"):
        authorize(
            session,
            JobContext(tenant, None, run.id, None, now() + timedelta(seconds=30)),
            CaseConfig(),
        )


def test_exhausted_expired_claims_resume_database_only_rollout(session, business):
    from datetime import timedelta

    from reality.db.core import now

    tenant = business.tenant.id
    run = enqueue_case_run(session, tenant)
    for _ in range(3):
        claim = jobs.claim_next(session, tenant)
        assert claim.id == run.id
        run.lease_expires_at = now() - timedelta(seconds=1)
        session.flush()
    assert jobs.claim_next(session, tenant) is None
    assert run.status == "failed" and run.last_error_code == "attempts_exhausted"
    assert enqueue_case_run(session, tenant).actor_id is None


def test_revoked_legacy_owner_run_does_not_block_platform_rollout(
    session, business, scheduled_owner
):
    from reality.db.core import TenantMembership, uid
    from reality.db.scheduled_jobs import ScheduledJobRun

    tenant = business.tenant.id
    envelope = {"version": 1, "arguments": {"limit": 100}}
    legacy = ScheduledJobRun(
        id=uid("run"),
        tenant_id=tenant,
        actor_id=scheduled_owner.id,
        job_type="operational_cases.reconcile",
        configuration=envelope,
        request_id="legacy-owner",
        request_fingerprint=jobs._fingerprint(envelope),
    )
    session.add(legacy)
    member = session.scalar(
        select(TenantMembership).where(
            TenantMembership.tenant_id == tenant,
            TenantMembership.user_id == scheduled_owner.id,
        )
    )
    member.status = "removed"
    session.flush()
    assert jobs.claim_next(session, tenant) is None
    assert legacy.last_error_code == "not_authorized"
    recovered = enqueue_case_run(session, tenant)
    assert recovered.actor_id is None and recovered.id != legacy.id
    assert legacy.actor_id == scheduled_owner.id and legacy.status == "failed"
    claim = jobs.claim_next(session, tenant)
    jobs.execute_claim(session, tenant, claim.id, claim.claim_token)
    assert cases.coordination_status(session, tenant)["coverage_ready"]


def test_default_case_prevents_downgrade_before_first_job(
    postgres_database, monkeypatch
):
    from alembic import command
    from alembic.config import Config
    from conftest import business as business_fixture
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session

    from reality.db.operational_cases import CaseRollout

    monkeypatch.setenv("REALITY_DATABASE_URL", postgres_database)
    config = Config("alembic.ini")
    command.upgrade(config, "head")
    engine = create_engine(postgres_database)
    try:
        with Session(engine) as setup:
            company = business_fixture.__wrapped__(setup)
            _promise(setup, company, "SYNCHRONOUS")
            assert setup.get(CaseRollout, company.tenant.id) is None
        with pytest.raises(RuntimeError, match="control history"):
            command.downgrade(config, "0144_operational_cases")
    finally:
        engine.dispose()


def test_staged_raw_source_never_becomes_goal_without_acceptance(session, business):
    import json

    from test_operational_cases import FIXTURE

    from reality.services.intake import prepare_intake

    tenant = business.tenant.id
    payload = json.loads(FIXTURE.read_text())
    source, job = core.enqueue_shopify_order(
        session,
        tenant,
        payload,
        business.company.id,
        business.customer.id,
        business.location.id,
    )
    prepare_intake(session, tenant, job.id)
    captured = source.payload
    cases.reconcile_events(session, tenant)
    assert cases.list_cases(session, tenant) == []
    assert source.payload == captured
    assert session.get(CaseAdoption, tenant) is None


def test_http_review_replay_preserves_final_proposal_identity_and_case_binding(
    session, business
):
    from reality.db.operational_cases import CaseProposalLink
    from reality.services.delivery_actions import prepare_delivery_action

    commitment = order(session, business)
    arguments = {"commitment_id": commitment.id, "reason_code": "customer_request", "note": "Reviewed customer agreement"}
    proposal = prepare_delivery_action(
        session, business.tenant.id, "commitment_hold", arguments, request_id="http-bound"
    )
    case_id = cases.object_cases(session, business.tenant.id, "commitment", commitment.id)[0]
    link = session.get(CaseProposalLink, (business.tenant.id, case_id, proposal.id))
    assert link is not None
    assert link.bound_control_revision == 1
    assert case_id in json.loads(proposal.output)["_case_business_review"]
    replay = prepare_delivery_action(
        session, business.tenant.id, "commitment_hold", arguments, request_id="http-bound"
    )
    assert replay.id == proposal.id
    assert session.get(CaseProposalLink, (business.tenant.id, case_id, replay.id)) is link
    assert proposal.status == "proposed"
    assert not list(session.scalars(select(Reservation)))


def test_owned_sandbox_can_read_default_status_without_business_control_rights(
    session, scheduled_owner, monkeypatch
):
    from fastapi.testclient import TestClient

    from reality.services import company_setup
    from reality.services.memberships import Principal
    from reality.web import auth as web_auth
    from reality.web import operational_cases as web_cases
    from reality.web.api import database_session
    from reality.web.app import app

    monkeypatch.setenv("REALITY_PLAYGROUND_ENABLED", "true")
    created = company_setup.create_company(
        session, scheduled_owner.id, "case-status-sandbox", "Case status sandbox",
        "sandbox", "empty", confirmed=True,
    )
    tenant = created["tenant_id"]
    monkeypatch.setattr(web_auth, "user_from_request", lambda request, db: scheduled_owner)
    monkeypatch.setattr(
        web_cases, "optional_request_principal", lambda request: Principal(scheduled_owner.id)
    )
    app.dependency_overrides[database_session] = lambda: session
    try:
        with TestClient(app) as client:
            response = client.get(f"/api/tenants/{tenant}/operational-cases/status")
            assert response.status_code == 200, response.text
            status = response.json()
            assert status["enabled"] and status["migration_ready"]
            assert not status["coverage_ready"] and not status["can_control"]
            with pytest.raises(core.NotFound):
                cases._member(session, tenant, Principal(scheduled_owner.id))
            assert session.get(CaseAdoption, tenant) is None
            monkeypatch.setattr(web_auth, "user_from_request", lambda request, db: None)
            assert client.get(f"/api/tenants/{tenant}/operational-cases/status").status_code == 401
    finally:
        app.dependency_overrides.clear()
