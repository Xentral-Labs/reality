"""First-slice coordination: current facts, takeover and exact handback."""

import json
from pathlib import Path

import pytest
from sqlalchemy import select

from reality.db.core import ChangeProposal, now, uid
from reality.db.operational_cases import OperationalCase
from reality.services import core
from reality.services import operational_cases as cases
from reality.services.case_action_guards import automated_execution, guard_operation
from reality.services.intake import apply_prepared_intake, prepare_intake, review_intake
from reality.services.memberships import Principal

FIXTURE = Path(__file__).parent.parent / "fixtures/shopify/order_10473.json"


def order(session, business):
    payload = json.loads(FIXTURE.read_text())
    _, job = core.enqueue_shopify_order(
        session,
        business.tenant.id,
        payload,
        business.company.id,
        business.customer.id,
        business.location.id,
    )
    proposal = prepare_intake(session, business.tenant.id, job.id)
    review = review_intake(session, business.tenant.id, proposal.id)
    apply_prepared_intake(
        session,
        business.tenant.id,
        proposal.id,
        review["digest"],
        confirmed=True,
    )
    return core.commitments(session, business.tenant.id)[0]


def activate(session, business, owner):
    return cases.adopt(
        session,
        business.tenant.id,
        Principal(owner.id),
        confirmed=True,
        request_key=uid("req"),
    )


def test_staging_does_not_create_case(session, business, scheduled_owner):
    activate(session, business, scheduled_owner)
    payload = json.loads(FIXTURE.read_text())
    _, job = core.enqueue_shopify_order(
        session,
        business.tenant.id,
        payload,
        business.company.id,
        business.customer.id,
        business.location.id,
    )
    prepare_intake(session, business.tenant.id, job.id)
    assert session.scalar(select(OperationalCase)) is None


def test_acceptance_ensures_case_and_event_replay_is_idempotent(
    session,
    business,
    scheduled_owner,
):
    activate(session, business, scheduled_owner)
    commitment = order(session, business)
    initial = cases.list_cases(session, business.tenant.id)
    assert len(initial) == 1
    assert initial[0]["order_document_id"] == commitment.document_id
    cases.reconcile_events(session, business.tenant.id)
    cases.reconcile_events(session, business.tenant.id)
    assert [c["case_id"] for c in cases.list_cases(session, business.tenant.id)] == [
        initial[0]["case_id"]
    ]


def test_historical_order_is_not_implicitly_adopted(session, business, scheduled_owner):
    commitment = order(session, business)
    activate(session, business, scheduled_owner)
    assert (
        cases.object_cases(session, business.tenant.id, "commitment", commitment.id)
        == []
    )
    assert cases.list_cases(session, business.tenant.id) == []


def test_takeover_blocks_direct_automation_but_allows_human_repair(
    session,
    business,
    scheduled_owner,
):
    activate(session, business, scheduled_owner)
    commitment = order(session, business)
    case_id = cases.list_cases(session, business.tenant.id)[0]["case_id"]
    taken = cases.takeover(
        session,
        business.tenant.id,
        case_id,
        Principal(scheduled_owner.id),
        expected_revision=1,
        request_key="take-1",
        confirmed=True,
    )
    assert taken["control_mode"] == "human"
    with (
        automated_execution(session, business.tenant.id),
        pytest.raises(core.InvalidOperation, match="manually owned"),
    ):
        core.revise_commitment(
            session, business.tenant.id, commitment.id, quantity="20"
        )
    core.revise_commitment(session, business.tenant.id, commitment.id, quantity="20")
    assert core.commitment_quantity(session, business.tenant.id, commitment.id) == 20


def test_handback_is_exact_and_old_action_generation_stays_invalid(
    session,
    business,
    scheduled_owner,
):
    activate(session, business, scheduled_owner)
    commitment = order(session, business)
    case_id = cases.list_cases(session, business.tenant.id)[0]["case_id"]
    proposal = ChangeProposal(
        id=uid("act"),
        tenant_id=business.tenant.id,
        type="tool:commitment_revise",
        actor_type="agent",
        status="proposed",
        input="{}",
        created_at=now(),
    )
    session.add(proposal)
    session.flush()
    cases.bind_proposal(session, business.tenant.id, proposal.id, [case_id])
    cases.takeover(
        session,
        business.tenant.id,
        case_id,
        Principal(scheduled_owner.id),
        expected_revision=1,
        request_key="take-2",
        confirmed=True,
    )
    review = cases.handback_preview(session, business.tenant.id, case_id)
    core.revise_commitment(session, business.tenant.id, commitment.id, quantity="20")
    with pytest.raises(core.InvalidOperation, match="case changed"):
        cases.handback(
            session,
            business.tenant.id,
            case_id,
            Principal(scheduled_owner.id),
            review_digest=review["digest"],
            request_key="back-1",
            confirmed=True,
        )
    review = cases.handback_preview(session, business.tenant.id, case_id)
    cases.handback(
        session,
        business.tenant.id,
        case_id,
        Principal(scheduled_owner.id),
        review_digest=review["digest"],
        request_key="back-2",
        confirmed=True,
    )
    with (
        automated_execution(session, business.tenant.id, proposal_id=proposal.id),
        pytest.raises(core.InvalidOperation, match="older case control"),
    ):
        guard_operation(
            session,
            business.tenant.id,
            "revise_commitment",
            {
                "commitment_id": commitment.id,
            },
        )


def test_executing_action_prevents_handback(session, business, scheduled_owner):
    activate(session, business, scheduled_owner)
    order(session, business)
    case_id = cases.list_cases(session, business.tenant.id)[0]["case_id"]
    action = ChangeProposal(
        id=uid("act"),
        tenant_id=business.tenant.id,
        type="tool:shipment_dispatch",
        status="executing",
        input="{}",
    )
    session.add(action)
    session.flush()
    cases.bind_proposal(session, business.tenant.id, action.id, [case_id])
    cases.takeover(
        session,
        business.tenant.id,
        case_id,
        Principal(scheduled_owner.id),
        expected_revision=1,
        request_key="take-3",
        confirmed=True,
    )
    review = cases.handback_preview(session, business.tenant.id, case_id)
    assert review["unsettled_actions"] == [action.id]
    with pytest.raises(core.InvalidOperation, match="unresolved execution"):
        cases.handback(
            session,
            business.tenant.id,
            case_id,
            Principal(scheduled_owner.id),
            review_digest=review["digest"],
            request_key="back-3",
            confirmed=True,
        )


def test_announced_return_is_distinct_and_not_transferred(
    session, business, scheduled_owner
):
    activate(session, business, scheduled_owner)
    commitment = order(session, business)
    core.record_movement(
        session,
        business.tenant.id,
        "opening_stock",
        business.item.id,
        "30",
        to_location_id=business.location.id,
    )
    core.record_movement(
        session,
        business.tenant.id,
        "shipment",
        business.item.id,
        "2",
        from_location_id=business.location.id,
        commitment_id=commitment.id,
    )
    announcement = core.announce_customer_return(
        session,
        business.tenant.id,
        commitment.id,
        "1",
    )
    result = cases.list_cases(session, business.tenant.id)
    assert {c["kind"] for c in result} == {"order_fulfillment", "customer_return"}
    ret = next(c for c in result if c["kind"] == "customer_return")
    assert ret["return_announcement_id"] == announcement.id
    fulfillment = next(c for c in result if c["kind"] == "order_fulfillment")
    cases.takeover(
        session,
        business.tenant.id,
        fulfillment["case_id"],
        Principal(scheduled_owner.id),
        expected_revision=1,
        request_key="take-4",
        confirmed=True,
    )
    assert (
        cases.explain(session, business.tenant.id, ret["case_id"])["control_mode"]
        == "automation"
    )


def test_foreign_case_and_missing_principal_refused(session, business, scheduled_owner):
    activate(session, business, scheduled_owner)
    order(session, business)
    case_id = cases.list_cases(session, business.tenant.id)[0]["case_id"]
    foreign = core.create_tenant(session, "Other")
    with pytest.raises(core.NotFound):
        cases.explain(session, foreign.id, case_id)
    with pytest.raises(core.NotFound):
        cases.takeover(
            session,
            business.tenant.id,
            case_id,
            None,
            expected_revision=1,
            request_key="take-5",
            confirmed=True,
        )
