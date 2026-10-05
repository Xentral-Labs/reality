"""Actual lower boundaries, stale prerequisites and mixed responsibility."""

import json

import pytest
from sqlalchemy import select
from test_operational_cases import activate, order

from reality.db.core import BusinessEvent, ChangeProposal, Commitment, now, uid
from reality.services import core
from reality.services import operational_cases as cases
from reality.services.case_action_guards import (
    automated_execution,
    bind_arguments,
    guard_operation,
    guard_proposal,
)
from reality.services.memberships import Principal
from reality.tools.application import (
    approve_and_execute_proposal,
    create_change_proposal,
)


def owned(session, business, owner):
    activate(session, business, owner)
    promise = order(session, business)
    case_id = cases.object_cases(session, business.tenant.id, "commitment", promise.id)[
        0
    ]
    return promise, case_id


def takeover(session, business, owner, case_id):
    return cases.takeover(
        session,
        business.tenant.id,
        case_id,
        Principal(owner.id),
        expected_revision=1,
        request_key=uid("req"),
        confirmed=True,
    )


def test_generic_proposal_freezes_business_prerequisites_without_worker_catchup(
    session, business, scheduled_owner
):
    promise, _ = owned(session, business, scheduled_owner)
    proposal = create_change_proposal(
        session,
        business.tenant.id,
        "commitment_revise",
        {"commitment_id": promise.id, "quantity": "20"},
    )
    core.revise_commitment(session, business.tenant.id, promise.id, quantity="25")
    with pytest.raises(core.InvalidOperation, match="changed"):
        approve_and_execute_proposal(
            session, business.tenant.id, proposal.id, confirmed=True
        )
    assert proposal.status == "proposed"
    assert core.commitment_quantity(session, business.tenant.id, promise.id) == 25


def test_actual_generic_execution_refuses_takeover_but_human_confirmation_can_repair(
    session, business, scheduled_owner
):
    promise, case_id = owned(session, business, scheduled_owner)
    proposal = create_change_proposal(
        session,
        business.tenant.id,
        "commitment_revise",
        {"commitment_id": promise.id, "quantity": "20"},
    )
    takeover(session, business, scheduled_owner, case_id)
    with pytest.raises(core.InvalidOperation, match="manually owned"):
        approve_and_execute_proposal(
            session, business.tenant.id, proposal.id, confirmed=True
        )
    assert proposal.status == "proposed"
    approve_and_execute_proposal(
        session,
        business.tenant.id,
        proposal.id,
        review_token=json.loads(proposal.input)["_delivery_review"]["token"],
        confirmed=True,
        confirming_principal=Principal(scheduled_owner.id),
    )
    assert core.commitment_quantity(session, business.tenant.id, promise.id) == 20
    # Executed receipt replay still returns, even though this generation is obsolete.
    assert (
        approve_and_execute_proposal(
            session, business.tenant.id, proposal.id, confirmed=True
        ).status
        == "executed"
    )


def test_combined_work_cannot_bypass_one_human_case_with_forged_case_id(
    session, business, scheduled_owner
):
    promise, first_id = owned(session, business, scheduled_owner)
    doc, _ = core.create_manual_document_with_lines(
        session,
        business.tenant.id,
        "sales_order",
        "SECOND",
        business.customer.id,
        gross_amount="20",
        lines=[
            {
                "item_id": business.item.id,
                "quantity": "2",
                "unit_price": "10",
                "gross_amount": "20",
            }
        ],
    )
    second = core.create_commitment(
        session,
        business.tenant.id,
        "customer_delivery",
        business.company.id,
        business.customer.id,
        business.item.id,
        business.location.id,
        "2",
        None,
        document_id=doc.id,
    )
    second_id = cases.object_cases(
        session, business.tenant.id, "commitment", second.id
    )[0]
    takeover(session, business, scheduled_owner, second_id)
    with (
        automated_execution(session, business.tenant.id),
        pytest.raises(core.InvalidOperation, match="manually owned"),
    ):
        guard_operation(
            session,
            business.tenant.id,
            "record_packaged_execution",
            {
                "case_id": first_id,
                "lines": [{"commitment_id": promise.id}, {"commitment_id": second.id}],
            },
        )


def test_automatic_unanchored_promise_and_unannounced_return_are_unavailable(
    session, business, scheduled_owner
):
    activate(session, business, scheduled_owner)
    with (
        automated_execution(session, business.tenant.id),
        pytest.raises(core.InvalidOperation, match="no supported case"),
    ):
        core.create_commitment(
            session,
            business.tenant.id,
            "customer_delivery",
            business.company.id,
            business.customer.id,
            business.item.id,
            business.location.id,
            "2",
            None,
        )
    assert session.scalar(select(Commitment)) is None
    with (
        automated_execution(session, business.tenant.id),
        pytest.raises(core.InvalidOperation, match="no supported case"),
    ):
        core.record_movement(
            session,
            business.tenant.id,
            "return",
            business.item.id,
            "1",
            to_location_id=business.location.id,
        )


def test_default_work_stays_guarded_after_legacy_activation(
    session, business, scheduled_owner
):
    promise = order(session, business)
    activate(session, business, scheduled_owner)
    case_id = cases.object_cases(session, business.tenant.id, "commitment", promise.id)[
        0
    ]
    cases.takeover(
        session,
        business.tenant.id,
        case_id,
        Principal(scheduled_owner.id),
        expected_revision=1,
        request_key="default-guard",
        confirmed=True,
    )
    with (
        automated_execution(session, business.tenant.id),
        pytest.raises(core.InvalidOperation, match="manually owned"),
    ):
        core.cancel_commitment(
            session, business.tenant.id, promise.id, reason="No longer needed"
        )
    assert (
        cases.explain(session, business.tenant.id, case_id)["control_mode"] == "human"
    )


def test_relevant_new_source_blocks_automation_and_handback_without_accepting_it(
    session, business, scheduled_owner
):
    promise, case_id = owned(session, business, scheduled_owner)
    from test_operational_cases import FIXTURE

    payload = json.loads(FIXTURE.read_text())
    payload["note"] = "A newer external version that has not been interpreted"
    source, _ = core.enqueue_shopify_order(
        session,
        business.tenant.id,
        payload,
        business.company.id,
        business.customer.id,
        business.location.id,
    )
    before = core.commitment_quantity(session, business.tenant.id, promise.id)
    with (
        automated_execution(session, business.tenant.id),
        pytest.raises(core.InvalidOperation, match="not yet reconciled"),
    ):
        core.revise_commitment(session, business.tenant.id, promise.id, quantity="20")
    assert (
        cases.explain(session, business.tenant.id, case_id)["coverage_gaps"][0][
            "source_record_id"
        ]
        == source.id
    )
    takeover(session, business, scheduled_owner, case_id)
    review = cases.handback_preview(session, business.tenant.id, case_id)
    with pytest.raises(core.InvalidOperation, match="not yet reconciled"):
        cases.handback(
            session,
            business.tenant.id,
            case_id,
            Principal(scheduled_owner.id),
            review_digest=review["digest"],
            request_key="blocked-return",
            confirmed=True,
        )
    assert core.commitment_quantity(session, business.tenant.id, promise.id) == before


def test_action_attribution_does_not_invent_external_correlation(
    session, business, scheduled_owner
):
    promise, case_id = owned(session, business, scheduled_owner)
    proposal = create_change_proposal(
        session,
        business.tenant.id,
        "commitment_revise",
        {"commitment_id": promise.id, "quantity": "20"},
    )
    approve_and_execute_proposal(
        session,
        business.tenant.id,
        proposal.id,
        review_token=json.loads(proposal.input)["_delivery_review"]["token"],
        confirming_principal=Principal(scheduled_owner.id),
        confirmed=True,
    )
    event = session.scalar(
        select(BusinessEvent)
        .where(
            BusinessEvent.tenant_id == business.tenant.id,
            BusinessEvent.event_type == "commitment.revised",
        )
        .order_by(BusinessEvent.sequence.desc())
    )
    assert event.action_id == proposal.id
    assert event.correlation_id is None
    traced = core.emit_business_event(
        session,
        business.tenant.id,
        "commitment.held",
        "commitment",
        promise.id,
        {},
        action_id=proposal.id,
        correlation_id="foreign-system-run-17",
    )
    session.flush()
    assert traced.correlation_id == "foreign-system-run-17"
    assert traced.correlation_id not in {proposal.id, case_id}


def test_binding_never_refreshes_old_control_generation(
    session, business, scheduled_owner
):
    promise, case_id = owned(session, business, scheduled_owner)
    action = ChangeProposal(
        id=uid("act"),
        tenant_id=business.tenant.id,
        type="tool:commitment_revise",
        actor_type="agent",
        status="proposed",
        input=json.dumps({"commitment_id": promise.id, "quantity": "20"}),
        created_at=now(),
    )
    session.add(action)
    session.flush()
    bind_arguments(
        session,
        business.tenant.id,
        action.id,
        "commitment_revise",
        json.loads(action.input),
    )
    takeover(session, business, scheduled_owner, case_id)
    review = cases.handback_preview(session, business.tenant.id, case_id)
    cases.handback(
        session,
        business.tenant.id,
        case_id,
        Principal(scheduled_owner.id),
        review_digest=review["digest"],
        request_key="return",
        confirmed=True,
    )
    bind_arguments(
        session,
        business.tenant.id,
        action.id,
        "commitment_revise",
        json.loads(action.input),
    )
    with pytest.raises(core.InvalidOperation, match="older case control"):
        guard_proposal(session, business.tenant.id, action.id, automatic=True)
