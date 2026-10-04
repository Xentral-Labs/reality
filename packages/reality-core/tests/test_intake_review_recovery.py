"""Spec 356: phase failures and explicit renewed review never alter accepted intent."""

import json

import pytest
from sqlalchemy import select
from test_intake_admission import prepare

from reality.db.core import Document, InterpretationOutcome
from reality.services import core, intake
from reality.services.memberships import Principal


def test_prepare_failure_retains_phase_and_never_accepts_source(session, business):
    source, job = core.enqueue_source(
        session,
        business.tenant.id,
        "unmapped-provider",
        "unknown-statement",
        "REVIEW-FAIL",
        {"original": "retained"},
    )
    with pytest.raises(core.InvalidOperation):
        intake.prepare_intake(session, business.tenant.id, job.id)
    outcomes = list(
        session.scalars(
            select(InterpretationOutcome)
            .where(InterpretationOutcome.import_job_id == job.id)
            .order_by(InterpretationOutcome.attempt)
        )
    )
    assert outcomes[-1].classification == "failed"
    assert outcomes[-1].interpreter_name == "intake.prepare"
    assert json.loads(job.error)["phase"] == "prepare"
    assert job.next_attempt_at is None
    assert json.loads(source.payload) == {"original": "retained"}
    assert session.scalar(select(Document)) is None


def test_renewed_review_is_explicit_immutable_and_request_idempotent(
    session, business, scheduled_owner
):
    _, job, old = prepare(session, business)
    old_input = old.input
    old_digest = intake.review_intake(session, business.tenant.id, old.id)["digest"]
    business.customer.name = "Changed after original review"
    session.flush()
    fresh = intake.renew_prepared_intake(
        session,
        business.tenant.id,
        job.id,
        previous_proposal_id=old.id,
        request_id="explicit-renewal",
    )
    assert fresh.id != old.id
    assert old.input == old_input
    assert fresh.status == "proposed"
    assert (
        intake.renew_prepared_intake(
            session,
            business.tenant.id,
            job.id,
            previous_proposal_id=old.id,
            request_id="explicit-renewal",
        ).id
        == fresh.id
    )
    assert (
        intake.review_intake(session, business.tenant.id, old.id)["status"] == "stale"
    )
    with pytest.raises(core.InvalidOperation):
        intake.apply_prepared_intake(
            session,
            business.tenant.id,
            old.id,
            old_digest,
            confirmed=True,
            principal=Principal(scheduled_owner.id),
        )
    assert session.scalar(select(Document)) is None
    intake.apply_prepared_intake(
        session,
        business.tenant.id,
        fresh.id,
        intake.review_intake(session, business.tenant.id, fresh.id)["digest"],
        confirmed=True,
        principal=Principal(scheduled_owner.id),
    )
    assert session.scalar(select(Document)) is not None
    assert (
        intake.renew_prepared_intake(
            session,
            business.tenant.id,
            job.id,
            previous_proposal_id=old.id,
            request_id="explicit-renewal",
        ).id
        == fresh.id
    )


def test_completed_receipt_is_never_reprepared(session, business, scheduled_owner):
    _, job, proposal = prepare(session, business)
    intake.apply_prepared_intake(
        session,
        business.tenant.id,
        proposal.id,
        intake.review_intake(session, business.tenant.id, proposal.id)["digest"],
        confirmed=True,
        principal=Principal(scheduled_owner.id),
    )
    with pytest.raises(core.InvalidOperation):
        intake.renew_prepared_intake(
            session,
            business.tenant.id,
            job.id,
            previous_proposal_id=proposal.id,
            request_id="must-not-renew-completed",
        )
    assert proposal.status == "executed"


def test_known_apply_failure_retains_apply_phase_after_atomic_rollback(
    session, business, scheduled_owner, monkeypatch
):
    _, job, proposal = prepare(session, business)
    digest = intake.review_intake(session, business.tenant.id, proposal.id)["digest"]

    def fail(*args, **kwargs):
        raise core.InvalidOperation("Injected known no-effect refusal")

    monkeypatch.setattr(core, "create_commitment", fail)
    with pytest.raises(core.InvalidOperation):
        intake.apply_prepared_intake(
            session,
            business.tenant.id,
            proposal.id,
            digest,
            confirmed=True,
            principal=Principal(scheduled_owner.id),
        )
    assert session.scalar(select(Document)) is None
    latest = session.scalar(
        select(InterpretationOutcome)
        .where(InterpretationOutcome.import_job_id == job.id)
        .order_by(InterpretationOutcome.attempt.desc())
    )
    assert latest.interpreter_name == "intake.apply"
    assert latest.classification == "failed"
    assert json.loads(job.error)["phase"] == "apply"
    assert job.status == "awaiting_decision"
    assert job.next_attempt_at is None


def test_foreign_company_cannot_renew_retained_review(session, business):
    _, job, proposal = prepare(session, business)
    foreign = core.create_tenant(session, "Foreign review recovery")
    before = session.scalar(
        select(core.ImportJob.attempts).where(core.ImportJob.id == job.id)
    )
    with pytest.raises(core.NotFound):
        intake.renew_prepared_intake(
            session,
            foreign.id,
            job.id,
            previous_proposal_id=proposal.id,
            request_id="foreign-renewal",
        )
    assert (
        session.scalar(
            select(core.ImportJob.attempts).where(core.ImportJob.id == job.id)
        )
        == before
    )
    assert proposal.status == "proposed"


def test_unknown_prepare_infrastructure_failure_is_not_a_business_refusal(
    session, business, monkeypatch
):
    source, job = core.enqueue_shopify_order(
        session,
        business.tenant.id,
        {"id": "INFRA", "line_items": [], "total_price": "0", "currency": "EUR"},
        business.company.id,
        business.customer.id,
        business.location.id,
    )
    before = session.scalar(
        select(core.ImportJob.attempts).where(core.ImportJob.id == job.id)
    )
    from reality.services import shopify_intake

    def fail(*args, **kwargs):
        raise RuntimeError("Uncertain infrastructure failure")

    monkeypatch.setattr(shopify_intake, "prepare_order", fail)
    with pytest.raises(RuntimeError):
        intake.prepare_intake(session, business.tenant.id, job.id)
    assert job.attempts == before
    assert session.scalar(select(Document)) is None
    assert json.loads(source.payload)["id"] == "INFRA"
