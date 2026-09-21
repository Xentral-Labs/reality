import json
from datetime import timedelta
from decimal import Decimal

import pytest
from conftest import record_by_id

from reality.db.core import (
    AppUser,
    BusinessEvent,
    CompanyInvitation,
    InvitationDelivery,
    Reservation,
    TenantMembership,
    now,
    uid,
)
from reality.services.core import (
    Conflict,
    InvalidOperation,
    NotFound,
    active_reserved,
    create_commitment,
    create_item,
    create_location,
    create_tenant,
    record_movement,
    reserve,
)
from reality.services.memberships import Principal
from reality.tools.application import (
    confirm_tool,
    propose_tool,
    reject_tool,
    run_read_tool,
)


def commitment_with_stock(session, business):
    record_movement(
        session,
        business.tenant.id,
        "opening_stock",
        business.item.id,
        5,
        to_location_id=business.location.id,
    )
    return create_commitment(
        session,
        business.tenant.id,
        "customer_delivery",
        business.company.id,
        business.customer.id,
        business.item.id,
        business.location.id,
        5,
        "2026-09-03",
    )


def test_read_tool_executes_without_proposal(session, business):
    commitment_with_stock(session, business)

    from reality.services.projections import rebuild_projections

    rebuild_projections(session, business.tenant.id, ["inventory"])
    result = run_read_tool(session, business.tenant.id, "inventory")

    assert result[0]["physical"] == "5.0000"
    assert result[0]["item_id"] == business.item.id


def test_exception_explain_reads_one_current_derived_exception(session, business):
    commitment = commitment_with_stock(session, business)
    exceptions = run_read_tool(session, business.tenant.id, "exceptions")

    explained = run_read_tool(
        session,
        business.tenant.id,
        "exception_explain",
        {"exception_id": exceptions[0]["id"]},
    )

    assert exceptions
    assert explained["id"] == exceptions[0]["id"]
    assert explained["record_id"] == commitment.id


def test_mutation_changes_reality_only_after_confirmation(session, business):
    commitment = commitment_with_stock(session, business)
    proposal = propose_tool(
        session, business.tenant.id, "reserve", {"commitment_id": commitment.id}
    )

    assert proposal.status == "proposed"
    assert active_reserved(session, business.tenant.id, business.item.id) == 0

    executed = confirm_tool(
        session,
        business.tenant.id,
        proposal.id,
        review_token=json.loads(proposal.input)["_delivery_review"]["token"],
        confirmed=True,
    )

    assert executed.status == "executed"
    assert Decimal(json.loads(executed.output)["reserved"]) == Decimal(5)
    assert active_reserved(session, business.tenant.id, business.item.id) == 5
    replayed = confirm_tool(session, business.tenant.id, proposal.id)
    assert replayed.output == executed.output
    assert (
        session.query(Reservation).filter_by(commitment_id=commitment.id).count() == 1
    )

    receipt = json.loads(executed.output)
    assert receipt["proposal_id"] == proposal.id
    assert receipt["capability"] == "reserve"
    assert receipt["commitment_id"] == commitment.id
    assert receipt["reservation_id"]
    assert receipt["event_id"]
    event = record_by_id(session, BusinessEvent, receipt["event_id"])
    assert event.action_id == proposal.id
    assert event.subject_id == receipt["reservation_id"]

    status = run_read_tool(
        session,
        business.tenant.id,
        "proposal_execution_status",
        {"proposal_id": proposal.id},
    )
    assert status["receipt"] == receipt
    assert status["verification"] == {
        "execution": "verified",
        "operational_state": "verified",
        "business_outcome": "not_proven",
        "checks": {
            "proposal_matches": True,
            "capability_matches": True,
            "commitment_matches": True,
            "reservation_matches": True,
            "event_matches": True,
        },
    }


def test_executing_proposal_requires_reconciliation_without_reexecution(
    session, business
):
    commitment = commitment_with_stock(session, business)
    proposal = propose_tool(
        session, business.tenant.id, "reserve", {"commitment_id": commitment.id}
    )
    proposal.status = "executing"
    session.commit()

    with pytest.raises(InvalidOperation, match="reconcile by proposal ID"):
        confirm_tool(session, business.tenant.id, proposal.id)

    assert (
        session.query(Reservation).filter_by(commitment_id=commitment.id).count() == 0
    )
    status = run_read_tool(
        session,
        business.tenant.id,
        "proposal_execution_status",
        {"proposal_id": proposal.id},
    )
    assert status["status"] == "executing"
    assert status["verification"]["execution"] == "unknown"


def test_reconciliation_finds_effect_committed_before_proposal_receipt(
    session, business
):
    commitment = commitment_with_stock(session, business)
    proposal = propose_tool(
        session, business.tenant.id, "reserve", {"commitment_id": commitment.id}
    )
    proposal.status = "executing"
    session.commit()
    committed = reserve(
        session,
        business.tenant.id,
        commitment.id,
        action_id=proposal.id,
    )

    status = run_read_tool(
        session,
        business.tenant.id,
        "proposal_execution_status",
        {"proposal_id": proposal.id},
    )

    assert status["status"] == "executing"
    assert status["receipt"] is None
    assert status["reconciliation_evidence"] == {
        "event_id": committed.event.id,
        "reservation_id": committed.reservation.id,
        "commitment_id": commitment.id,
        "applied": "5",
    }
    assert status["verification"]["execution"] == "effect_observed_proposal_unsettled"
    assert status["verification"]["operational_state"] == "verified"
    with pytest.raises(InvalidOperation, match="reconcile by proposal ID"):
        confirm_tool(session, business.tenant.id, proposal.id)


@pytest.mark.parametrize(
    ("field", "wrong_value"),
    [
        ("commitment_id", "com_wrong"),
        ("reservation_id", "res_wrong"),
        ("applied", "999"),
        ("event_id", "evt_wrong"),
    ],
)
def test_reservation_verification_rejects_mismatched_receipt(
    session, business, field, wrong_value
):
    commitment = commitment_with_stock(session, business)
    proposal = propose_tool(
        session, business.tenant.id, "reserve", {"commitment_id": commitment.id}
    )
    executed = confirm_tool(
        session,
        business.tenant.id,
        proposal.id,
        review_token=json.loads(proposal.input)["_delivery_review"]["token"],
        confirmed=True,
    )
    receipt = json.loads(executed.output)
    receipt[field] = wrong_value
    executed.output = json.dumps(receipt, sort_keys=True)
    session.commit()

    status = run_read_tool(
        session,
        business.tenant.id,
        "proposal_execution_status",
        {"proposal_id": proposal.id},
    )

    assert status["verification"]["execution"] == "unresolved"
    assert status["verification"]["operational_state"] == "unresolved"
    assert status["verification"]["business_outcome"] == "not_proven"


def test_movement_correction_tool_previews_before_confirmed_effect(session, business):
    movement = record_movement(
        session,
        business.tenant.id,
        "receipt",
        business.item.id,
        2,
        to_location_id=business.location.id,
    )
    proposal = propose_tool(
        session,
        business.tenant.id,
        "movement_correct",
        {"movement_id": movement.id, "reason": "Duplicate receipt"},
    )
    arguments = json.loads(proposal.input)
    assert arguments["expected_revision"]
    assert arguments["preview_fingerprint"]
    assert len(session.query(type(movement)).all()) == 1

    executed = confirm_tool(
        session,
        business.tenant.id,
        proposal.id,
        confirmed=True,
        review_token=arguments["_delivery_review"]["token"],
    )

    output = json.loads(executed.output)
    assert output["original_movement_id"] == movement.id
    assert len(session.query(type(movement)).all()) == 2


def test_rejection_and_tenant_scope_prevent_mutation(session, business):
    commitment = commitment_with_stock(session, business)
    proposal = propose_tool(
        session, business.tenant.id, "reserve", {"commitment_id": commitment.id}
    )

    with pytest.raises(NotFound):
        confirm_tool(session, "ten_other", proposal.id)
    rejected = reject_tool(session, business.tenant.id, proposal.id)

    assert rejected.status == "rejected"
    assert active_reserved(session, business.tenant.id, business.item.id) == 0


def test_read_tool_excludes_populated_foreign_tenant(session, business):
    commitment_with_stock(session, business)
    other = create_tenant(session, "Tool Boundary Other")
    other_item = create_item(session, other.id, business.item.sku, business.item.name)
    other_location = create_location(session, other.id, business.location.name)
    record_movement(
        session,
        other.id,
        "opening_stock",
        other_item.id,
        17,
        to_location_id=other_location.id,
    )

    from reality.services.projections import rebuild_projections

    rebuild_projections(session, business.tenant.id, ["inventory"])
    result = run_read_tool(session, business.tenant.id, "inventory")

    assert {row["item_id"] for row in result} == {business.item.id}
    assert other_item.id not in {row["item_id"] for row in result}


def test_membership_invite_proposal_is_effect_free_and_reauthorizes_owner(session):
    tenant = create_tenant(session, "Chat Membership Company")
    owner = AppUser(
        id=uid("usr"),
        email="chat-owner@example.com",
        password_hash="x",
        status="active",
        email_verified_at=now(),
    )
    session.add(owner)
    session.flush()
    owner_membership = TenantMembership(
        id=uid("tmb"),
        tenant_id=tenant.id,
        user_id=owner.id,
        role="owner",
        status="active",
    )
    session.add(owner_membership)
    session.flush()

    proposal = propose_tool(
        session,
        tenant.id,
        "member_invite",
        {"email": "chat-member@example.com"},
    )
    assert session.query(CompanyInvitation).filter_by(tenant_id=tenant.id).count() == 0
    assert session.query(InvitationDelivery).filter_by(tenant_id=tenant.id).count() == 0
    assert json.loads(proposal.input)["email"] == "chat-member@example.com"
    assert json.loads(proposal.output) == {
        "action": "member_invite",
        "company_id": tenant.id,
        "requires_human_confirmation": True,
        "target": {"email": "chat-member@example.com"},
    }

    with pytest.raises(InvalidOperation, match="confirming human owner"):
        confirm_tool(session, tenant.id, proposal.id)
    executed = confirm_tool(
        session,
        tenant.id,
        proposal.id,
        confirming_principal=Principal(owner.id),
    )
    assert executed.status == "executed"
    assert session.query(CompanyInvitation).filter_by(tenant_id=tenant.id).count() == 1
    assert session.query(InvitationDelivery).filter_by(tenant_id=tenant.id).count() == 1

    stale = propose_tool(
        session,
        tenant.id,
        "member_invite",
        {"email": "later@example.com"},
    )
    owner_membership.role = "member"
    session.commit()
    with pytest.raises(InvalidOperation, match="owner"):
        confirm_tool(
            session,
            tenant.id,
            stale.id,
            confirming_principal=Principal(owner.id),
        )


def test_membership_proposals_cover_reject_replay_resend_revoke_and_remove(session):
    tenant = create_tenant(session, "Chat Membership Lifecycle")
    owner = AppUser(
        id=uid("usr"),
        email="lifecycle-owner@example.com",
        password_hash="x",
        status="active",
        email_verified_at=now(),
    )
    member = AppUser(
        id=uid("usr"),
        email="lifecycle-member@example.com",
        password_hash="x",
        status="active",
        email_verified_at=now(),
    )
    session.add_all([owner, member])
    session.flush()
    session.add_all(
        [
            TenantMembership(
                id=uid("tmb"),
                tenant_id=tenant.id,
                user_id=owner.id,
                role="owner",
                status="active",
            ),
            TenantMembership(
                id=uid("tmb"),
                tenant_id=tenant.id,
                user_id=member.id,
                role="member",
                status="active",
            ),
        ]
    )
    session.commit()
    principal = Principal(owner.id)

    rejected = propose_tool(
        session, tenant.id, "member_invite", {"email": "rejected@example.com"}
    )
    reject_tool(session, tenant.id, rejected.id)
    assert session.query(CompanyInvitation).filter_by(tenant_id=tenant.id).count() == 0
    with pytest.raises(NotFound):
        confirm_tool(session, tenant.id, rejected.id, confirming_principal=principal)

    invited = propose_tool(
        session, tenant.id, "member_invite", {"email": "pending@example.com"}
    )
    executed = confirm_tool(
        session, tenant.id, invited.id, confirming_principal=principal
    )
    invitation_id = json.loads(executed.output)["invitation_id"]
    replayed = confirm_tool(
        session, tenant.id, invited.id, confirming_principal=principal
    )
    assert replayed.output == executed.output

    delivery = (
        session.query(InvitationDelivery)
        .filter_by(tenant_id=tenant.id, invitation_id=invitation_id)
        .one()
    )
    delivery.created_at = now() - timedelta(seconds=61)
    session.commit()
    resent = propose_tool(
        session,
        tenant.id,
        "invitation_resend",
        {"invitation_id": invitation_id},
    )
    confirm_tool(session, tenant.id, resent.id, confirming_principal=principal)
    assert (
        session.query(InvitationDelivery)
        .filter_by(tenant_id=tenant.id, invitation_id=invitation_id)
        .count()
        == 2
    )

    revoked = propose_tool(
        session,
        tenant.id,
        "invitation_revoke",
        {"invitation_id": invitation_id},
    )
    confirm_tool(session, tenant.id, revoked.id, confirming_principal=principal)
    invitation = record_by_id(session, CompanyInvitation, invitation_id)
    assert invitation is not None and invitation.status == "revoked"

    stale = propose_tool(
        session,
        tenant.id,
        "invitation_revoke",
        {"invitation_id": invitation_id},
    )
    with pytest.raises(Conflict, match="no longer pending"):
        confirm_tool(session, tenant.id, stale.id, confirming_principal=principal)

    membership = (
        session.query(TenantMembership)
        .filter_by(tenant_id=tenant.id, user_id=member.id)
        .one()
    )
    removed = propose_tool(
        session,
        tenant.id,
        "member_remove",
        {"membership_id": membership.id},
    )
    confirm_tool(session, tenant.id, removed.id, confirming_principal=principal)
    session.refresh(membership)
    assert membership.status == "removed"


# --- An invoice somebody can actually book (spec 091) ----------------------


def test_an_agent_can_record_a_document_and_book_the_invoice(session, business):
    """Recording and booking are two acts, and an agent can now do both.

    Before spec 091 an agent could create an order and nothing else on this
    path: recording a document was HTTP-only and booking an invoice was
    reachable from nowhere at all.
    """
    from reality.services.core import open_invoice_amount

    tenant_id = business.tenant.id
    recording = propose_tool(
        session,
        tenant_id,
        "document_create",
        {
            "document_type": "sales_invoice",
            "number": "RE-091-AGENT",
            "party_id": business.customer.id,
            "gross_amount": "250.00",
            "document_date": "2026-08-01",
            "lines": [
                {
                    "item_id": business.item.id,
                    "quantity": "1",
                    "unit": "pcs",
                    "unit_price": "250.00",
                    "gross_amount": "250.00",
                }
            ],
        },
    )
    assert recording.status == "proposed"
    recorded = json.loads(confirm_tool(session, tenant_id, recording.id).output)
    invoice_id = recorded["document_id"]
    assert len(recorded["document_line_ids"]) == 1

    # Recording did not book: nothing in the ledger answers for it yet.
    with pytest.raises(InvalidOperation):
        open_invoice_amount(session, tenant_id, invoice_id)

    booking = propose_tool(
        session, tenant_id, "sales_invoice_post", {"document_id": invoice_id}
    )
    assert booking.status == "proposed"
    booked = json.loads(confirm_tool(session, tenant_id, booking.id).output)

    assert len(booked["records"]) == 2
    assert open_invoice_amount(session, tenant_id, invoice_id) == Decimal(250)


def test_the_invoice_reaches_every_surface_the_credit_note_does(session, business):
    """FR-004 and FR-006: the credit note is the yardstick, so it is diffed.

    The two documents drifted apart because nobody compared them. This compares
    them, in the three places a drift would show.
    """
    from reality.catalogs import load_application_catalog
    from reality.mcp.catalog import tool_definitions
    from reality.tools.application import TOOLS

    for note, invoice in (
        ("credit_note_post", "sales_invoice_post"),
        ("credit_note_post", "supplier_invoice_post"),
    ):
        assert note in TOOLS and invoice in TOOLS
        assert TOOLS[note].mutating == TOOLS[invoice].mutating is True

    proposals = {definition.name for definition in tool_definitions()}
    assert {
        "sales_invoice_post_propose",
        "supplier_invoice_post_propose",
        "document_create_propose",
    } <= proposals

    services = {
        command["service"] for command in load_application_catalog()["commands"]
    }
    assert {
        "post_sales_invoice",
        "post_supplier_invoice",
        "create_manual_document_with_lines",
    } <= services
