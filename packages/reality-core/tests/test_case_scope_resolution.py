"""Owned effects stay separate from independent goals, raw data and read prerequisites."""

import pytest
from test_operational_cases import activate, order

from reality.services import core
from reality.services import operational_cases as cases
from reality.services.case_action_guards import automated_execution, resolve_cases
from reality.services.memberships import Principal
from reality.tools.application import (
    approve_and_execute_proposal,
    create_change_proposal,
)
from reality.tools.finance import FINANCE_COMMANDS


def test_raw_source_and_finance_order_references_are_not_fulfillment_ownership(
    session, business, scheduled_owner
):
    activate(session, business, scheduled_owner)
    promise = order(session, business)
    tenant = business.tenant.id
    for operation in (
        "source_ingest",
        "source_record_ingest",
        next(iter(FINANCE_COMMANDS)),
    ):
        assert resolve_cases(
            session,
            tenant,
            operation,
            {"order_id": promise.document_id, "payload": {"commitment_id": promise.id}},
        ) == ([], False)
    # A readonly dependency is not an effect, even in an accepted interpretation.
    assert resolve_cases(
        session,
        tenant,
        "intake_apply",
        {
            "effects": [
                {
                    "operation": "return_announcement",
                    "arguments": {"commitment_id": promise.id},
                }
            ],
            "observations": [{"arguments": {"order_id": promise.document_id}}],
        },
    ) == ([], False)


def test_readonly_review_snapshots_do_not_add_unselected_cases(
    session, business, scheduled_owner
):
    activate(session, business, scheduled_owner)
    promise = order(session, business)
    tenant = business.tenant.id
    assert resolve_cases(
        session,
        tenant,
        "backorders_serve",
        {"lines": [], "reviewed": {"waiting": [{"commitment_id": promise.id}]}},
    ) == ([], False)


def test_announced_return_proposal_owns_its_new_goal_without_taking_over_the_order(
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
    fulfillment = cases.object_cases(session, tenant, "commitment", promise.id)[0]
    cases.takeover(
        session,
        tenant,
        fulfillment,
        Principal(scheduled_owner.id),
        expected_revision=1,
        request_key="own-order-only",
        confirmed=True,
    )
    proposal = create_change_proposal(
        session,
        tenant,
        "return_announce",
        {"commitment_id": promise.id, "quantity": "1"},
    )
    assert cases.object_cases(session, tenant, "proposal", proposal.id) == []
    approve_and_execute_proposal(session, tenant, proposal.id, confirmed=True)
    owned = cases.object_cases(session, tenant, "proposal", proposal.id)
    assert len(owned) == 1 and fulfillment not in owned
    assert cases.explain(session, tenant, owned[0])["kind"] == "customer_return"
    assert cases.explain(session, tenant, fulfillment)["control_mode"] == "human"


def test_completed_human_owned_history_does_not_block_a_party_hold_for_current_work(
    session, business, scheduled_owner
):
    activate(session, business, scheduled_owner)
    promise = order(session, business)
    tenant = business.tenant.id
    old = cases.object_cases(session, tenant, "commitment", promise.id)[0]
    core.cancel_commitment(session, tenant, promise.id, reason="No longer needed")
    cases.takeover(
        session,
        tenant,
        old,
        Principal(scheduled_owner.id),
        expected_revision=1,
        request_key="retain-old-ownership",
        confirmed=True,
    )
    doc = core.create_document(
        session, tenant, "sales_order", "NEW", business.customer.id, "0"
    )
    current = core.create_commitment(
        session,
        tenant,
        "customer_delivery",
        business.company.id,
        business.customer.id,
        business.item.id,
        business.location.id,
        "1",
        None,
        document_id=doc.id,
    )
    current_case = cases.object_cases(session, tenant, "commitment", current.id)[0]
    assert resolve_cases(
        session, tenant, "hold_party_delivery", {"party_id": business.customer.id}
    ) == ([current_case], False)
    with automated_execution(session, tenant):
        core.hold_party_delivery(session, tenant, business.customer.id, "manual_review")
    assert (
        core.active_party_delivery_hold(session, tenant, business.customer.id)
        is not None
    )


def test_automatic_shipment_cannot_omit_its_business_anchor(
    session, business, scheduled_owner
):
    activate(session, business, scheduled_owner)
    core.record_movement(
        session,
        business.tenant.id,
        "opening_stock",
        business.item.id,
        "5",
        to_location_id=business.location.id,
    )
    with (
        automated_execution(session, business.tenant.id),
        pytest.raises(core.InvalidOperation) as refusal,
    ):
        core.record_movement(
            session,
            business.tenant.id,
            "shipment",
            business.item.id,
            "1",
            from_location_id=business.location.id,
        )
    assert refusal.value.code == "case_coverage_unavailable"
