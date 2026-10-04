"""Spec 359: a received payment is proposed before posting or allocation."""

import json

import pytest
from sqlalchemy import func, select

from reality.db.core import BusinessEvent, Document, LedgerEntry
from reality.services import core
from reality.services.intake import apply_prepared_intake, prepare_intake, review_intake


def prepared_payment(session, business):
    source, job = core.enqueue_source(
        session,
        business.tenant.id,
        "bank",
        "customer_payment",
        "payment-1",
        {
            "party_id": business.customer.id,
            "amount": "41.29",
            "currency": "EUR",
            "effective_at": "2026-09-12T10:00:00Z",
            "external_payment_id": "payment-1",
            "payment_number": "PAY-1",
            "references": [],
            "remittance_text": "Received bank statement",
        },
        context={"profile": "customer_payment.v1"},
    )
    proposal = prepare_intake(session, business.tenant.id, job.id)
    return source, proposal


def test_financial_prepare_is_non_posting(session, business):
    source, proposal = prepared_payment(session, business)
    review = review_intake(session, business.tenant.id, proposal.id)
    assert review["plan"]["effects"][0]["arguments"]["amount"] == "41.29"
    assert review["plan"]["source_record_id"] == source.id
    assert session.scalar(select(func.count()).select_from(LedgerEntry)) == 0
    assert session.scalar(select(func.count()).select_from(Document)) == 0


def test_unmatched_payment_can_be_accepted_explicitly(
    session, business, scheduled_owner
):
    from reality.services.memberships import Principal

    source, proposal = prepared_payment(session, business)
    digest = review_intake(session, business.tenant.id, proposal.id)["digest"]
    result = apply_prepared_intake(
        session,
        business.tenant.id,
        proposal.id,
        digest,
        confirmed=True,
        principal=Principal(scheduled_owner.id),
    )
    receipt = json.loads(result.output)
    assert receipt["source_record_id"] == source.id
    assert result.decided_by_user_id == scheduled_owner.id
    assert session.scalar(select(func.count()).select_from(LedgerEntry)) == 2
    assert session.scalar(select(Document)).gross_amount == core.decimal("41.29")
    event = session.scalar(
        select(BusinessEvent).where(
            BusinessEvent.tenant_id == business.tenant.id,
            BusinessEvent.event_type == "ledger.posted",
        )
    )
    assert event.action_id == proposal.id
    assert event.source_record_id == source.id
    assert {row["id"] for row in json.loads(event.payload)["entries"]} == {
        row.id for row in session.scalars(select(LedgerEntry))
    }


def test_financial_review_does_not_grant_member_owner_authority(
    session, business, scheduled_owner
):
    from reality.db.core import TenantMembership
    from reality.services.memberships import Principal

    _, proposal = prepared_payment(session, business)
    digest = review_intake(session, business.tenant.id, proposal.id)["digest"]
    member = session.scalar(
        select(TenantMembership).where(
            TenantMembership.tenant_id == business.tenant.id,
            TenantMembership.user_id == scheduled_owner.id,
        )
    )
    member.role = "member"
    session.commit()
    with pytest.raises(core.InvalidOperation):
        apply_prepared_intake(
            session,
            business.tenant.id,
            proposal.id,
            digest,
            confirmed=True,
            principal=Principal(scheduled_owner.id),
        )
    assert session.scalar(select(func.count()).select_from(LedgerEntry)) == 0
