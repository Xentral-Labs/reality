"""Spec 355: fixed selections settle independent exact decisions in bounded chunks."""

import json

import pytest
from sqlalchemy import func, select

from reality.db.core import ChangeProposal, Document
from reality.services import core, intake_batches
from reality.services.intake import prepare_intake, review_intake
from reality.services.memberships import Principal


def prepared_orders(session, business, count, *, lines=1):
    entries = []
    for number in range(count):
        payload = {
            "id": f"bulk-{number}",
            "name": f"B{number}",
            "currency": "EUR",
            "total_price": str(lines),
            "line_items": [
                {
                    "id": f"line-{position}",
                    "sku": business.item.sku,
                    "name": "Received item",
                    "quantity": 1,
                    "price": "1",
                    "total_price": "1",
                }
                for position in range(lines)
            ],
        }
        _, job = core.enqueue_shopify_order(
            session,
            business.tenant.id,
            payload,
            business.company.id,
            business.customer.id,
            business.location.id,
        )
        proposal = prepare_intake(session, business.tenant.id, job.id)
        entries.append(
            {
                "proposal_id": proposal.id,
                "digest": review_intake(session, business.tenant.id, proposal.id)[
                    "digest"
                ],
            }
        )
    return entries


def test_manifest_is_fixed_and_preparation_has_no_effects(session, business):
    entries = prepared_orders(session, business, 2)
    batch = intake_batches.prepare_batch(
        session, business.tenant.id, entries, request_id="fixed-selection"
    )
    assert batch.status == "proposed"
    assert session.scalar(select(func.count()).select_from(Document)) == 0
    assert (
        intake_batches.prepare_batch(
            session, business.tenant.id, entries, request_id="fixed-selection"
        ).id
        == batch.id
    )
    assert len(json.loads(batch.input)["manifest"]["entries"]) == 2
    with pytest.raises(core.InvalidOperation):
        intake_batches.prepare_batch(
            session, business.tenant.id, entries + entries, request_id="duplicates"
        )


def test_confirmed_batch_settles_at_most_25_and_preserves_reviewer(
    session, business, scheduled_owner
):
    entries = prepared_orders(session, business, 30)
    batch = intake_batches.prepare_batch(
        session, business.tenant.id, entries, request_id="thirty"
    )
    digest = json.loads(batch.input)["digest"]
    intake_batches.approve_batch(
        session,
        business.tenant.id,
        batch.id,
        digest,
        confirmed=True,
        principal=Principal(scheduled_owner.id),
    )
    first = intake_batches.settle_chunk(
        session,
        business.tenant.id,
        batch.id,
        continuation_id=json.loads(batch.output)["continuation_id"],
    )
    assert first["settled"] == 25
    assert session.scalar(select(func.count()).select_from(Document)) == 25
    child = session.get(ChangeProposal, (business.tenant.id, entries[0]["proposal_id"]))
    assert child.decided_by_user_id == scheduled_owner.id
    assert json.loads(child.output)["batch_authorization"]["batch_id"] == batch.id
    second = intake_batches.settle_chunk(
        session,
        business.tenant.id,
        batch.id,
        continuation_id=json.loads(batch.output)["continuation_id"],
    )
    assert second["settled"] == 5
    assert batch.status == "executed"
    assert session.scalar(select(func.count()).select_from(Document)) == 30


def test_infrastructure_failure_rolls_back_the_entire_chunk(
    session, business, scheduled_owner, monkeypatch
):
    entries = prepared_orders(session, business, 2)
    batch = intake_batches.prepare_batch(
        session, business.tenant.id, entries, request_id="rollback"
    )
    intake_batches.approve_batch(
        session,
        business.tenant.id,
        batch.id,
        json.loads(batch.input)["digest"],
        confirmed=True,
        principal=Principal(scheduled_owner.id),
    )
    actual = intake_batches.apply_prepared_intake
    calls = 0

    def disconnected(*args, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise RuntimeError("Injected connection loss")
        return actual(*args, **kwargs)

    monkeypatch.setattr(intake_batches, "apply_prepared_intake", disconnected)
    with pytest.raises(RuntimeError):
        intake_batches.settle_chunk(
            session,
            business.tenant.id,
            batch.id,
            continuation_id=json.loads(batch.output)["continuation_id"],
        )
    assert session.scalar(select(func.count()).select_from(Document)) == 0
    assert json.loads(batch.output)["next_index"] == 0
    assert all(
        session.get(ChangeProposal, (business.tenant.id, entry["proposal_id"])).status
        == "proposed"
        for entry in entries
    )


def test_current_revocation_is_a_no_effect_disposition_for_each_child(
    session, business, scheduled_owner
):
    from reality.db.core import TenantMembership

    entries = prepared_orders(session, business, 2)
    batch = intake_batches.prepare_batch(
        session, business.tenant.id, entries, request_id="revoked"
    )
    intake_batches.approve_batch(
        session,
        business.tenant.id,
        batch.id,
        json.loads(batch.input)["digest"],
        confirmed=True,
        principal=Principal(scheduled_owner.id),
    )
    membership = session.scalar(
        select(TenantMembership).where(
            TenantMembership.tenant_id == business.tenant.id,
            TenantMembership.user_id == scheduled_owner.id,
        )
    )
    membership.status = "removed"
    session.flush()
    result = intake_batches.settle_chunk(
        session,
        business.tenant.id,
        batch.id,
        continuation_id=json.loads(batch.output)["continuation_id"],
    )
    assert result["terminal"]
    assert session.scalar(select(func.count()).select_from(Document)) == 0
    assert {row["disposition"] for row in json.loads(batch.output)["results"]} == {
        "review_required"
    }


def test_stop_leaves_pending_children_available_for_another_review(
    session, business, scheduled_owner
):
    entries = prepared_orders(session, business, 2)
    batch = intake_batches.prepare_batch(
        session, business.tenant.id, entries, request_id="stopped"
    )
    principal = Principal(scheduled_owner.id)
    intake_batches.approve_batch(
        session,
        business.tenant.id,
        batch.id,
        json.loads(batch.input)["digest"],
        confirmed=True,
        principal=principal,
    )
    intake_batches.stop_batch(
        session, business.tenant.id, batch.id, principal=principal
    )
    intake_batches.settle_chunk(
        session,
        business.tenant.id,
        batch.id,
        continuation_id=json.loads(batch.output)["continuation_id"],
    )
    assert batch.status == "executed"
    assert session.scalar(select(func.count()).select_from(Document)) == 0
    assert {row["disposition"] for row in json.loads(batch.output)["results"]} == {
        "stopped"
    }
    assert all(
        session.get(ChangeProposal, (business.tenant.id, entry["proposal_id"])).status
        == "proposed"
        for entry in entries
    )


def test_authorization_queues_compact_registered_continuations(
    session, business, scheduled_owner
):
    from reality.db.scheduled_jobs import ScheduledJobRun
    from reality.jobs.registry import JobContext, get_definition

    entries = prepared_orders(session, business, 26)
    batch = intake_batches.prepare_batch(
        session, business.tenant.id, entries, request_id="queued"
    )
    intake_batches.approve_batch(
        session,
        business.tenant.id,
        batch.id,
        json.loads(batch.input)["digest"],
        confirmed=True,
        principal=Principal(scheduled_owner.id),
    )
    runs = list(
        session.scalars(
            select(ScheduledJobRun).where(
                ScheduledJobRun.tenant_id == business.tenant.id,
                ScheduledJobRun.job_type == "intake.batch_apply",
            )
        )
    )
    assert len(runs) == 1
    first = runs[0]
    assert set(first.configuration["arguments"]) == {
        "batch_id",
        "manifest_revision",
        "continuation_id",
    }
    assert len(json.dumps(first.configuration).encode()) < 15000
    definition = get_definition(first.job_type)
    context = JobContext(
        business.tenant.id, scheduled_owner.id, first.id, None, core.now()
    )
    parsed = definition.validate(first.configuration["arguments"])
    definition.authorize(session, context, parsed)
    result = definition.handler(session, context, parsed)
    assert result.counts["settled"] == 25
    assert len(result.model_dump_json().encode()) < 3500
    assert result.references[0].id == batch.id
    assert batch.status == "executing"
    assert (
        session.scalar(
            select(func.count())
            .select_from(ScheduledJobRun)
            .where(ScheduledJobRun.job_type == "intake.batch_apply")
        )
        == 2
    )
    replay = definition.handler(session, context, parsed)
    assert replay.counts["settled"] == 0
    assert session.scalar(select(func.count()).select_from(Document)) == 25


def test_shared_tools_require_exact_batch_confirmation(
    session, business, scheduled_owner
):
    from reality.tools.application import (
        approve_and_execute_proposal,
        create_change_proposal,
        run_read_tool,
    )

    entries = prepared_orders(session, business, 2)
    batch = create_change_proposal(
        session,
        business.tenant.id,
        "intake_batch_apply",
        {"entries": entries, "request_id": "tools"},
    )
    page = run_read_tool(
        session, business.tenant.id, "intake_batch_review", {"batch_id": batch.id}
    )
    assert page["digest"] == json.loads(batch.input)["digest"]
    assert len(page["entries"]) == 2
    with pytest.raises(core.InvalidOperation):
        approve_and_execute_proposal(
            session,
            business.tenant.id,
            batch.id,
            confirming_principal=Principal(scheduled_owner.id),
            confirmed=True,
            review_token="wrong",
        )
    assert session.scalar(select(func.count()).select_from(Document)) == 0
    approved = approve_and_execute_proposal(
        session,
        business.tenant.id,
        batch.id,
        confirming_principal=Principal(scheduled_owner.id),
        confirmed=True,
        review_token=page["digest"],
    )
    assert approved.status == "executing"


def test_foreign_tenant_cannot_read_or_settle_batch(session, business, scheduled_owner):
    entries = prepared_orders(session, business, 1)
    batch = intake_batches.prepare_batch(
        session, business.tenant.id, entries, request_id="tenant"
    )
    foreign = core.create_tenant(session, "Foreign intake")
    for operation in (
        lambda: intake_batches.review_batch(session, foreign.id, batch.id),
        lambda: intake_batches.batch_status(session, foreign.id, batch.id),
        lambda: intake_batches.settle_chunk(
            session, foreign.id, batch.id, continuation_id="untrusted"
        ),
        lambda: intake_batches.prepare_batch(
            session, foreign.id, entries, request_id="foreign"
        ),
        lambda: intake_batches.approve_batch(
            session,
            foreign.id,
            batch.id,
            json.loads(batch.input)["digest"],
            confirmed=True,
            principal=Principal(scheduled_owner.id),
        ),
        lambda: intake_batches.stop_batch(
            session, foreign.id, batch.id, principal=Principal(scheduled_owner.id)
        ),
        lambda: intake_batches.reject_batch(
            session, foreign.id, batch.id, principal=Principal(scheduled_owner.id)
        ),
    ):
        with pytest.raises(core.NotFound):
            operation()
    assert session.scalar(select(func.count()).select_from(Document)) == 0


def test_real_queue_commits_child_receipts_and_run_success_together(
    session, business, scheduled_owner
):
    from reality.db.scheduled_jobs import ScheduledJobRun
    from reality.services import scheduled_jobs

    entries = prepared_orders(session, business, 26)
    batch = intake_batches.prepare_batch(
        session, business.tenant.id, entries, request_id="worker"
    )
    intake_batches.approve_batch(
        session,
        business.tenant.id,
        batch.id,
        json.loads(batch.input)["digest"],
        confirmed=True,
        principal=Principal(scheduled_owner.id),
    )
    for expected in (25, 26):
        claim = scheduled_jobs.claim_next(session, business.tenant.id)
        assert claim.job_type == "intake.batch_apply"
        session.commit()
        scheduled_jobs.execute_claim(
            session, business.tenant.id, claim.id, claim.claim_token
        )
        session.commit()
        assert (
            session.get(ScheduledJobRun, (business.tenant.id, claim.id)).status
            == "succeeded"
        )
        assert session.scalar(select(func.count()).select_from(Document)) == expected
    assert (
        intake_batches.batch_status(session, business.tenant.id, batch.id)["status"]
        == "executed"
    )


def test_500_five_line_orders_use_bounded_durable_runs_and_full_result_pages(
    session, business, scheduled_owner
):
    from reality.db.core import DocumentLine
    from reality.db.scheduled_jobs import ScheduledJobRun
    from reality.services import scheduled_jobs

    entries = prepared_orders(session, business, 500, lines=5)
    batch = intake_batches.prepare_batch(
        session, business.tenant.id, entries, request_id="five-hundred"
    )
    assert session.scalar(select(func.count()).select_from(Document)) == 0
    assert intake_batches.review_batch(session, business.tenant.id, batch.id)[
        "has_more"
    ]
    with pytest.raises(core.InvalidOperation):
        intake_batches.review_batch(session, business.tenant.id, batch.id, limit=101)
    intake_batches.approve_batch(
        session,
        business.tenant.id,
        batch.id,
        json.loads(batch.input)["digest"],
        confirmed=True,
        principal=Principal(scheduled_owner.id),
    )
    for chunk in range(20):
        claim = scheduled_jobs.claim_next(session, business.tenant.id)
        assert claim.job_type == "intake.batch_apply"
        assert len(json.dumps(claim.configuration).encode()) < 15000
        assert set(claim.configuration["arguments"]) == {
            "batch_id",
            "manifest_revision",
            "continuation_id",
        }
        session.commit()
        assert (
            scheduled_jobs.execute_claim(
                session, business.tenant.id, claim.id, claim.claim_token
            )
            == "succeeded"
        )
        session.commit()
        assert claim.result["counts"]["settled"] == 25
        assert len(json.dumps(claim.result).encode()) < 3500
        assert (
            session.scalar(select(func.count()).select_from(Document))
            == (chunk + 1) * 25
        )
    assert session.scalar(select(func.count()).select_from(DocumentLine)) == 2500
    assert (
        session.scalar(
            select(func.count())
            .select_from(ScheduledJobRun)
            .where(ScheduledJobRun.job_type == "intake.batch_apply")
        )
        == 20
    )
    results = []
    for cursor in range(0, 500, 100):
        page = intake_batches.batch_status(
            session, business.tenant.id, batch.id, cursor=cursor
        )
        assert page["status"] == "executed"
        results.extend(page["results"])
    assert len(results) == 500
    assert {row["disposition"] for row in results} == {"applied"}
