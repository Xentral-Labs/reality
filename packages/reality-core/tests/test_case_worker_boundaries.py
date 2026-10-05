"""A retained human batch decision does not impersonate a new interactive repair."""

import json

from test_operational_cases import FIXTURE, activate, order

from reality.services import core, intake_batches
from reality.services import operational_cases as cases
from reality.services.intake import apply_prepared_intake, prepare_intake, review_intake
from reality.services.memberships import Principal


def test_queued_human_batch_stops_at_takeover_and_fresh_interactive_repair_remains_allowed(
    session, business, scheduled_owner
):
    activate(session, business, scheduled_owner)
    promise = order(session, business)
    tenant = business.tenant.id
    principal = Principal(scheduled_owner.id)
    case_id = cases.object_cases(session, tenant, "commitment", promise.id)[0]
    payload = json.loads(FIXTURE.read_text())
    payload["line_items"][0]["current_quantity"] = 25
    _, job = core.enqueue_shopify_order(
        session,
        tenant,
        payload,
        business.company.id,
        business.customer.id,
        business.location.id,
    )
    child = prepare_intake(session, tenant, job.id)
    review = review_intake(session, tenant, child.id)
    batch = intake_batches.prepare_batch(
        session,
        tenant,
        [{"proposal_id": child.id, "digest": review["digest"]}],
        request_id="old-human-batch",
    )
    intake_batches.approve_batch(
        session,
        tenant,
        batch.id,
        json.loads(batch.input)["digest"],
        confirmed=True,
        principal=principal,
    )
    cases.takeover(
        session,
        tenant,
        case_id,
        principal,
        expected_revision=1,
        request_key="stop-queued-batch",
        confirmed=True,
    )
    intake_batches.settle_chunk(
        session,
        tenant,
        batch.id,
        continuation_id=json.loads(batch.output)["continuation_id"],
    )
    result = json.loads(batch.output)["results"][0]
    assert result["disposition"] == "review_required"
    assert result["reason_code"] == "case_human_owned"
    assert core.commitment_quantity(session, tenant, promise.id) == 30
    assert child.status == "proposed"
    assert cases.explain(session, tenant, case_id)["coverage_gaps"]
    # A current, explicit human decision still accepts the repair using normal intake.
    current = review_intake(session, tenant, child.id)
    apply_prepared_intake(
        session,
        tenant,
        child.id,
        current["digest"],
        confirmed=True,
        principal=principal,
    )
    assert core.commitment_quantity(session, tenant, promise.id) == 25
    assert not cases.explain(session, tenant, case_id)["coverage_gaps"]
