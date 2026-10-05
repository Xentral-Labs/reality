"""Accepted Shopify evidence, an obsolete plan and explicit repair/handback."""

import json

import pytest
from test_operational_cases import FIXTURE, activate, order

from reality.services import core
from reality.services import operational_cases as cases
from reality.services.intake import apply_prepared_intake, prepare_intake, review_intake
from reality.services.memberships import Principal
from reality.tools.application import (
    approve_and_execute_proposal,
    create_change_proposal,
)


def test_shopify_repair_uses_current_evidence_and_never_revives_old_work(
    session, business, scheduled_owner
):
    activate(session, business, scheduled_owner)
    promise = order(session, business)
    case_id = cases.object_cases(session, business.tenant.id, "commitment", promise.id)[
        0
    ]
    old = create_change_proposal(
        session,
        business.tenant.id,
        "commitment_revise",
        {"commitment_id": promise.id, "quantity": "20"},
    )
    principal = Principal(scheduled_owner.id)
    cases.takeover(
        session,
        business.tenant.id,
        case_id,
        principal,
        expected_revision=1,
        request_key="repair",
        confirmed=True,
    )
    # External edits are lossless Sources, not accepted facts and not fresh authority.
    payload = json.loads(FIXTURE.read_text())
    payload["note"] = "Customer repaired the order externally"
    _, job = core.enqueue_shopify_order(
        session,
        business.tenant.id,
        payload,
        business.company.id,
        business.customer.id,
        business.location.id,
    )
    assert cases.explain(session, business.tenant.id, case_id)["coverage_gaps"]
    prepared = prepare_intake(session, business.tenant.id, job.id)
    review = review_intake(session, business.tenant.id, prepared.id)
    apply_prepared_intake(
        session,
        business.tenant.id,
        prepared.id,
        review["digest"],
        confirmed=True,
        principal=principal,
    )
    # Supported accepted evidence is reconciled; human local repair uses the same leaves.
    core.revise_commitment(session, business.tenant.id, promise.id, quantity="25")
    current = cases.handback_preview(session, business.tenant.id, case_id)
    assert not current["coverage_gaps"]
    returned = cases.handback(
        session,
        business.tenant.id,
        case_id,
        principal,
        review_digest=current["digest"],
        request_key="resume",
        confirmed=True,
    )
    assert returned["control_mode"] == "automation"
    assert any(
        row["proposal_id"] == old.id and row["obsolete"] for row in returned["actions"]
    )
    with pytest.raises(core.InvalidOperation):
        approve_and_execute_proposal(
            session, business.tenant.id, old.id, confirmed=True
        )
    assert core.commitment_quantity(session, business.tenant.id, promise.id) == 25
    assert cases.object_cases(
        session, business.tenant.id, "commitment", promise.id
    ) == [case_id]
