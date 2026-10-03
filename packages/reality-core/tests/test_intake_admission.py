"""Proofs for spec 351's retained, decision-gated interpretation boundary."""

import json
from pathlib import Path

import pytest
from sqlalchemy import func, select

from reality.db.core import ChangeProposal, Commitment, Document, InterpretationOutcome
from reality.services.core import InvalidOperation, enqueue_shopify_order
from reality.services.intake import apply_prepared_intake, prepare_intake, review_intake

FIXTURE = Path(__file__).parents[1] / "fixtures/shopify/order_10473.json"


def prepare(session, business):
    payload = json.loads(FIXTURE.read_text())
    payload["line_items"][0]["total_price"] = "1470.00"
    source, job = enqueue_shopify_order(
        session,
        business.tenant.id,
        payload,
        business.company.id,
        business.customer.id,
        business.location.id,
    )
    proposal = prepare_intake(session, business.tenant.id, job.id)
    return source, job, proposal


def test_preparation_has_no_business_effects(session, business):
    source, job, proposal = prepare(session, business)
    assert proposal.status == "proposed"
    assert job.status == "awaiting_decision"
    assert session.scalar(select(func.count()).select_from(Document)) == 0
    assert session.scalar(select(func.count()).select_from(Commitment)) == 0
    review = review_intake(session, business.tenant.id, proposal.id)
    assert review["plan"]["source_record_id"] == source.id
    assert review["plan"]["effects"][0]["arguments"]["gross_amount"] == "1470.00"
    assert prepare_intake(session, business.tenant.id, job.id).id == proposal.id
    assert session.scalar(select(func.count()).select_from(InterpretationOutcome)) == 1


def test_stale_or_forged_approval_refused(session, business):
    _, _, proposal = prepare(session, business)
    with pytest.raises(InvalidOperation):
        apply_prepared_intake(
            session, business.tenant.id, proposal.id, "forged", confirmed=True
        )
    assert session.scalar(select(func.count()).select_from(Document)) == 0
    assert (
        session.get(ChangeProposal, (business.tenant.id, proposal.id)).status
        == "proposed"
    )


def test_effects_and_receipt_are_atomic_and_replayable(session, business):
    source, job, proposal = prepare(session, business)
    digest = review_intake(session, business.tenant.id, proposal.id)["digest"]
    applied = apply_prepared_intake(
        session, business.tenant.id, proposal.id, digest, confirmed=True
    )
    assert applied.status == "executed"
    receipt = json.loads(applied.output)
    assert receipt["source_record_id"] == source.id
    assert receipt["proposal_id"] == proposal.id
    assert session.scalar(select(func.count()).select_from(Document)) == 1
    assert session.scalar(select(func.count()).select_from(Commitment)) == 1
    assert job.status == "completed"
    assert (
        apply_prepared_intake(
            session, business.tenant.id, proposal.id, digest, confirmed=True
        ).output
        == applied.output
    )
    assert session.scalar(select(func.count()).select_from(InterpretationOutcome)) == 2


def test_apply_failure_keeps_entire_unit_pending(session, business, monkeypatch):
    from reality.services import core

    _, _, proposal = prepare(session, business)
    digest = review_intake(session, business.tenant.id, proposal.id)["digest"]

    def fail(*args, **kwargs):
        raise InvalidOperation("Injected commitment failure")

    monkeypatch.setattr(core, "create_commitment", fail)
    with pytest.raises(InvalidOperation):
        apply_prepared_intake(
            session, business.tenant.id, proposal.id, digest, confirmed=True
        )
    assert session.scalar(select(func.count()).select_from(Document)) == 0
    assert (
        session.get(ChangeProposal, (business.tenant.id, proposal.id)).status
        == "proposed"
    )


def test_changed_reference_is_stale(session, business):
    _, _, proposal = prepare(session, business)
    digest = review_intake(session, business.tenant.id, proposal.id)["digest"]
    business.item.unit = "box"
    session.commit()
    with pytest.raises(InvalidOperation, match="changed"):
        apply_prepared_intake(
            session, business.tenant.id, proposal.id, digest, confirmed=True
        )
    assert session.scalar(select(func.count()).select_from(Document)) == 0


def test_new_source_version_invalidates_review(session, business):
    _, _, proposal = prepare(session, business)
    digest = review_intake(session, business.tenant.id, proposal.id)["digest"]
    payload = json.loads(FIXTURE.read_text())
    payload["total_price"] = "1600.00"
    enqueue_shopify_order(
        session,
        business.tenant.id,
        payload,
        business.company.id,
        business.customer.id,
        business.location.id,
    )
    with pytest.raises(InvalidOperation, match="changed"):
        apply_prepared_intake(
            session, business.tenant.id, proposal.id, digest, confirmed=True
        )
    assert session.scalar(select(func.count()).select_from(Document)) == 0


def test_raw_survives_prepare_failure(session, business):
    payload = json.loads(FIXTURE.read_text())
    payload["line_items"][0]["quantity"] = 0
    source, job = enqueue_shopify_order(
        session,
        business.tenant.id,
        payload,
        business.company.id,
        business.customer.id,
        business.location.id,
    )
    with pytest.raises(InvalidOperation, match="greater than zero"):
        prepare_intake(session, business.tenant.id, job.id)
    assert json.loads(source.payload) == payload
    assert session.scalar(select(func.count()).select_from(Document)) == 0


def test_foreign_tenant_cannot_review_or_apply(session, business):
    from reality.services.core import NotFound, create_tenant

    _, job, proposal = prepare(session, business)
    foreign = create_tenant(session, "Foreign intake company")
    with pytest.raises(NotFound):
        prepare_intake(session, foreign.id, job.id)
    with pytest.raises(NotFound):
        review_intake(session, foreign.id, proposal.id)
    with pytest.raises(NotFound):
        apply_prepared_intake(
            session, foreign.id, proposal.id, "forged", confirmed=True
        )


def test_direct_effect_application_has_no_authority(session, business):
    from reality.domain.intake import PreparedIntake
    from reality.services.intake import _apply_effects

    _, _, proposal = prepare(session, business)
    plan = PreparedIntake.model_validate(
        review_intake(session, business.tenant.id, proposal.id)["plan"]
    )
    with pytest.raises(InvalidOperation, match="transaction-bound"):
        _apply_effects(session, business.tenant.id, proposal, plan)
    assert session.scalar(select(func.count()).select_from(Document)) == 0


def test_mapping_change_does_not_silently_reinterpret(session, business):
    _, job, proposal = prepare(session, business)
    digest = review_intake(session, business.tenant.id, proposal.id)["digest"]
    context = json.loads(job.input)
    context["location_id"] = "loc_changed"
    job.input = json.dumps(context)
    session.commit()
    with pytest.raises(InvalidOperation, match="changed"):
        apply_prepared_intake(
            session, business.tenant.id, proposal.id, digest, confirmed=True
        )


def test_application_confirmation_uses_atomic_intake_branch(session, business):
    from reality.tools.application import approve_and_execute_proposal

    _, _, proposal = prepare(session, business)
    review = review_intake(session, business.tenant.id, proposal.id)
    with pytest.raises(InvalidOperation):
        approve_and_execute_proposal(
            session, business.tenant.id, proposal.id, confirmed=True
        )
    applied = approve_and_execute_proposal(
        session,
        business.tenant.id,
        proposal.id,
        confirmed=True,
        review_token=review["digest"],
    )
    assert applied.status == "executed"
    assert session.scalar(select(func.count()).select_from(Document)) == 1


def test_generic_proposal_cannot_forge_a_retained_plan(session, business):
    from reality.tools.application import create_change_proposal

    with pytest.raises(InvalidOperation):
        create_change_proposal(
            session,
            business.tenant.id,
            "intake_apply",
            {"plan": {}, "digest": "forged"},
        )


def test_canonical_writer_cannot_commit_partial_intake(session, business, monkeypatch):
    from reality.services import core

    _, _, proposal = prepare(session, business)
    digest = review_intake(session, business.tenant.id, proposal.id)["digest"]
    actual = core.create_commitment

    def committing(*args, **kwargs):
        result = actual(*args, **kwargs)
        session.commit()
        return result

    monkeypatch.setattr(core, "create_commitment", committing)
    with pytest.raises(InvalidOperation, match="commit together"):
        apply_prepared_intake(
            session, business.tenant.id, proposal.id, digest, confirmed=True
        )
    assert session.scalar(select(func.count()).select_from(Document)) == 0


def test_revoked_membership_cannot_apply(session, business, scheduled_owner):
    from reality.db.core import TenantMembership
    from reality.services.core import NotFound
    from reality.services.memberships import Principal

    _, _, proposal = prepare(session, business)
    digest = review_intake(session, business.tenant.id, proposal.id)["digest"]
    membership = session.scalar(
        select(TenantMembership).where(
            TenantMembership.tenant_id == business.tenant.id,
            TenantMembership.user_id == scheduled_owner.id,
        )
    )
    membership.status = "removed"
    session.commit()
    with pytest.raises(NotFound):
        apply_prepared_intake(
            session,
            business.tenant.id,
            proposal.id,
            digest,
            confirmed=True,
            principal=Principal(scheduled_owner.id),
        )
    assert session.scalar(select(func.count()).select_from(Document)) == 0


def test_rejection_retains_raw_and_appends_one_immutable_outcome(session, business):
    from reality.tools.application import reject_proposal

    source, job, proposal = prepare(session, business)
    before = [
        (row.id, row.classification)
        for row in session.scalars(select(InterpretationOutcome))
    ]
    rejected = reject_proposal(session, business.tenant.id, proposal.id)
    assert rejected.status == "rejected"
    assert job.status == "rejected"
    assert json.loads(source.payload)["name"] == "#10473"
    assert session.scalar(select(func.count()).select_from(Document)) == 0
    assert session.scalar(select(func.count()).select_from(InterpretationOutcome)) == 2
    assert [
        (row.id, row.classification)
        for row in session.scalars(
            select(InterpretationOutcome).where(
                InterpretationOutcome.id.in_([row[0] for row in before])
            )
        )
    ] == before
    reject_proposal(session, business.tenant.id, proposal.id)
    assert session.scalar(select(func.count()).select_from(InterpretationOutcome)) == 2


def test_prepared_shop_day_uses_and_freezes_the_company_calendar(session, business):
    from reality.services.company_time_zone import set_company_time_zone

    set_company_time_zone(session, business.tenant.id, "America/New_York")
    payload = json.loads(FIXTURE.read_text())
    payload["created_at"] = "2026-10-01T00:30:00Z"
    payload["line_items"][0]["total_price"] = "1470.00"
    _, job = enqueue_shopify_order(
        session,
        business.tenant.id,
        payload,
        business.company.id,
        business.customer.id,
        business.location.id,
    )
    proposal = prepare_intake(session, business.tenant.id, job.id)
    review = review_intake(session, business.tenant.id, proposal.id)
    assert review["plan"]["effects"][0]["arguments"]["document_date"] == "2026-09-30"
    set_company_time_zone(session, business.tenant.id, "UTC")
    with pytest.raises(InvalidOperation):
        apply_prepared_intake(
            session, business.tenant.id, proposal.id, review["digest"], confirmed=True
        )
    assert session.scalar(select(func.count()).select_from(Document)) == 0


def test_approved_effect_cannot_authorize_an_unplanned_writer(
    session, business, monkeypatch
):
    from reality.services import core

    _, _, proposal = prepare(session, business)
    digest = review_intake(session, business.tenant.id, proposal.id)["digest"]
    actual = core.create_commitment

    def unexpected(*args, **kwargs):
        core.create_item(
            session, business.tenant.id, "UNREVIEWED", "Unreviewed", _commit=False
        )
        return actual(*args, **kwargs)

    monkeypatch.setattr(core, "create_commitment", unexpected)
    with pytest.raises(InvalidOperation):
        apply_prepared_intake(
            session, business.tenant.id, proposal.id, digest, confirmed=True
        )
    assert session.scalar(select(func.count()).select_from(Document)) == 0


def test_an_approved_operation_cannot_change_the_reviewed_arguments(
    session, business, monkeypatch
):
    from reality.services import core

    _, _, proposal = prepare(session, business)
    digest = review_intake(session, business.tenant.id, proposal.id)["digest"]
    actual = core.create_commitment

    def changed(*args, **kwargs):
        return actual(*args, **{**kwargs, "quantity": "99"})

    monkeypatch.setattr(core, "create_commitment", changed)
    with pytest.raises(InvalidOperation):
        apply_prepared_intake(
            session, business.tenant.id, proposal.id, digest, confirmed=True
        )
    assert session.scalar(select(func.count()).select_from(Document)) == 0
