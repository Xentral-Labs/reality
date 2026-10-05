"""Controls retain one meaning across adapters, and batch entrypoints refuse before writes."""

import json

import pytest
from sqlalchemy import select
from test_operational_cases import activate, order

from reality.db.core import BusinessEvent, DocumentLine, Reservation
from reality.services import core
from reality.services import operational_cases as cases
from reality.services.case_action_guards import automated_execution
from reality.services.memberships import Principal
from reality.tools.application import (
    approve_and_execute_proposal,
    create_change_proposal,
)


def test_generic_control_retry_and_web_retry_share_the_retained_decision(
    session, business, scheduled_owner
):
    activate(session, business, scheduled_owner)
    promise = order(session, business)
    tenant = business.tenant.id
    case_id = cases.object_cases(session, tenant, "commitment", promise.id)[0]
    arguments = {
        "case_id": case_id,
        "expected_revision": 1,
        "request_key": "same-confirmation",
    }
    proposal = create_change_proposal(
        session, tenant, "operational_case_takeover", arguments
    )
    settled = approve_and_execute_proposal(
        session,
        tenant,
        proposal.id,
        confirmed=True,
        confirming_principal=Principal(scheduled_owner.id),
    )
    assert json.loads(settled.output)["control_revision"] == 2
    replay = cases.takeover(
        session,
        tenant,
        principal=Principal(scheduled_owner.id),
        confirmed=True,
        **arguments,
    )
    assert replay["control_revision"] == 2
    retry = create_change_proposal(
        session, tenant, "operational_case_takeover", arguments
    )
    approve_and_execute_proposal(
        session,
        tenant,
        retry.id,
        confirmed=True,
        confirming_principal=Principal(scheduled_owner.id),
    )
    assert cases.explain(session, tenant, case_id)["control_revision"] == 2
    assert (
        len(
            list(
                session.scalars(
                    select(BusinessEvent).where(
                        BusinessEvent.tenant_id == tenant,
                        BusinessEvent.event_type == "operational_case.taken_over",
                    )
                )
            )
        )
        == 1
    )
    with pytest.raises(core.InvalidOperation, match="request key"):
        cases.takeover(
            session,
            tenant,
            principal=Principal(scheduled_owner.id),
            confirmed=True,
            **{**arguments, "reason": "changed meaning"},
        )


@pytest.mark.parametrize("operation", ["backorders", "assignment", "stale_closure"])
def test_batch_or_assignment_boundary_refuses_the_whole_scope_before_mutation(
    session, business, scheduled_owner, operation
):
    activate(session, business, scheduled_owner)
    promise = order(session, business)
    tenant = business.tenant.id
    case_id = cases.object_cases(session, tenant, "commitment", promise.id)[0]
    cases.takeover(
        session,
        tenant,
        case_id,
        Principal(scheduled_owner.id),
        expected_revision=1,
        request_key="take-batch",
        confirmed=True,
    )
    from reality.services.backorders import serve_backorders
    from reality.services.order_line_items import assign_line_item

    line = session.scalar(
        select(DocumentLine).where(
            DocumentLine.tenant_id == tenant,
            DocumentLine.document_id == promise.document_id,
        )
    )
    calls = {
        "backorders": lambda: serve_backorders(
            session,
            tenant,
            business.item.id,
            business.location.id,
            [{"commitment_id": promise.id, "quantity": "1"}],
        ),
        "assignment": lambda: assign_line_item(
            session, tenant, document_line_id=line.id, item_id=business.item.id
        ),
        "stale_closure": lambda: core.close_stale_promises(
            session,
            tenant,
            direction="sales",
            due_before="2030-01-01",
            expected_count=1,
            reason="Cleanup",
        ),
    }
    with (
        automated_execution(session, tenant),
        pytest.raises(core.InvalidOperation, match="manually owned"),
    ):
        calls[operation]()
    assert (
        session.scalar(select(Reservation).where(Reservation.tenant_id == tenant))
        is None
    )
    assert core.commitment_quantity(session, tenant, promise.id) == 30


def test_return_explanation_includes_its_own_source_in_addition_to_the_order(
    session, business, scheduled_owner
):
    activate(session, business, scheduled_owner)
    promise = order(session, business)
    tenant = business.tenant.id
    core.record_movement(
        session,
        tenant,
        "opening_stock",
        business.item.id,
        "30",
        to_location_id=business.location.id,
    )
    core.record_movement(
        session,
        tenant,
        "shipment",
        business.item.id,
        "2",
        from_location_id=business.location.id,
        commitment_id=promise.id,
    )
    source = core.create_master_source_record(
        session,
        tenant,
        "return_statement",
        "customer_portal",
        "return-1",
        {"quantity": "1"},
    )
    announcement = core.announce_customer_return(
        session, tenant, promise.id, "1", source_record_id=source.id
    )
    case_id = cases.object_cases(
        session, tenant, "return_announcement", announcement.id
    )[0]
    explanation = cases.explain(session, tenant, case_id)
    assert source.id in explanation["source_record_ids"]
    assert len(explanation["source_record_ids"]) == 2


def test_explanation_reports_changed_business_meaning_before_worker_catchup(
    session, business, scheduled_owner
):
    activate(session, business, scheduled_owner)
    promise = order(session, business)
    tenant = business.tenant.id
    case_id = cases.object_cases(session, tenant, "commitment", promise.id)[0]
    proposal = create_change_proposal(
        session,
        tenant,
        "commitment_revise",
        {"commitment_id": promise.id, "quantity": "20"},
    )
    assert (
        next(
            row
            for row in cases.explain(session, tenant, case_id)["actions"]
            if row["proposal_id"] == proposal.id
        )["obsolete"]
        is False
    )
    core.revise_commitment(session, tenant, promise.id, quantity="25")
    action = next(
        row
        for row in cases.explain(session, tenant, case_id)["actions"]
        if row["proposal_id"] == proposal.id
    )
    assert action["obsolete"] is True
    assert action["obsolescence_reason"] == "business_state_changed"
