"""Integration contract for the separately delivered live simulator runtime."""

import pytest

from reality.db.core import now

live_company = pytest.importorskip("reality.services.live_company", reason="Simulator runtime is still on feat/company-reference-simulator")


def test_live_order_uses_default_cases_and_respects_takeover(
    session, business, scheduled_owner
):
    from reality.services import core
    from reality.services import operational_cases as cases
    from reality.services.case_action_guards import automated_execution
    from reality.services.memberships import Principal

    tenant = business.tenant.id
    actor = Principal(scheduled_owner.id)
    run = live_company.start(
        session,
        tenant,
        scheduled_owner.id,
        request_id="case-integration",
        confirmed=True,
    )
    assert cases.adoption(session, tenant) is None
    live_company.tick(session, tenant, run["run_id"], "first-case-order", now())
    message = live_company.inbox(session, tenant, run["run_id"])[0]
    document_id = message["document_id"]
    case_ids = cases.object_cases(session, tenant, "document", document_id)
    assert len(case_ids) == 1
    live_company.tick(session, tenant, run["run_id"], "first-case-order", now())
    cases.reconcile_events(session, tenant)
    cases.reconcile_events(session, tenant)
    assert cases.object_cases(session, tenant, "document", document_id) == case_ids
    assert len(cases.list_cases(session, tenant)) == 1
    commitment = next(
        c for c in core.commitments(session, tenant) if c.document_id == document_id
    )
    quantity = core.commitment_quantity(session, tenant, commitment.id)
    cases.takeover(
        session,
        tenant,
        case_ids[0],
        actor,
        expected_revision=1,
        request_key="take-live",
        confirmed=True,
    )
    with (
        automated_execution(session, tenant),
        pytest.raises(core.InvalidOperation, match="manually owned"),
    ):
        core.revise_commitment(session, tenant, commitment.id, quantity=quantity)
    assert core.commitment_quantity(session, tenant, commitment.id) == quantity
    review = cases.handback_preview(session, tenant, case_ids[0])
    cases.handback(
        session,
        tenant,
        case_ids[0],
        actor,
        review_digest=review["digest"],
        request_key="return-live",
        confirmed=True,
    )
    with automated_execution(session, tenant):
        core.revise_commitment(session, tenant, commitment.id, quantity=quantity)
    assert cases.object_cases(session, tenant, "document", document_id) == case_ids
