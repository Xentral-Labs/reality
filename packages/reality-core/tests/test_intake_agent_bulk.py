"""Spec 355: retained agent verdicts never become blanket queued authority."""

import json

import pytest
from sqlalchemy import select
from test_bulk_intake_admission import prepared_orders
from test_intake_agent_review import agent_context, owner_mandate, reviewed_evidence

from reality.db.core import ChangeProposal, Document
from reality.services import core, intake_batches, intake_review


def reviewed_batch(session, business, owner, count=2):
    mandate_id, token = owner_mandate(session, business, owner)
    entries = prepared_orders(session, business, count)
    batch = intake_batches.prepare_batch(
        session, business.tenant.id, entries, request_id="agent-reviewed-batch"
    )
    held = json.loads(batch.input)
    with agent_context(business, token):
        evidence = {
            "batch_id": batch.id,
            "manifest_digest": held["digest"],
            "manifest_revision": held["manifest"]["revision"],
            "reviews": [
                reviewed_evidence(
                    session,
                    business,
                    mandate_id,
                    session.get(
                        ChangeProposal, (business.tenant.id, entry["proposal_id"])
                    ),
                )
                for entry in entries
            ],
        }
    return batch, token, evidence


def test_agent_batch_keeps_actual_token_and_independent_child_receipts(
    session, business, scheduled_owner
):
    batch, token, evidence = reviewed_batch(session, business, scheduled_owner)
    with agent_context(business, token):
        intake_review.submit_agent_batch_review(session, business.tenant.id, evidence)
    assert batch.decided_by_user_id is None
    assert batch.decided_via_token_id == token.id
    assert session.scalar(select(Document)) is None
    result = intake_batches.settle_chunk(
        session,
        business.tenant.id,
        batch.id,
        continuation_id=json.loads(batch.output)["continuation_id"],
    )
    assert result == {"settled": 2, "terminal": True}
    assert len(list(session.scalars(select(Document)))) == 2
    for review in evidence["reviews"]:
        child = session.get(ChangeProposal, (business.tenant.id, review["proposal_id"]))
        assert child.decided_by_user_id is None
        assert child.decided_via_token_id == token.id
        assert json.loads(child.output)["agent_review"]["evidence"] == {
            "schema_version": 1,
            **review,
        }


def test_token_revocation_after_batch_decision_refuses_every_remaining_unit(
    session, business, scheduled_owner
):
    batch, token, evidence = reviewed_batch(session, business, scheduled_owner)
    with agent_context(business, token):
        intake_review.submit_agent_batch_review(session, business.tenant.id, evidence)
    token.revoked_at = core.now()
    session.flush()
    intake_batches.settle_chunk(
        session,
        business.tenant.id,
        batch.id,
        continuation_id=json.loads(batch.output)["continuation_id"],
    )
    assert session.scalar(select(Document)) is None
    assert all(
        row["disposition"] == "review_required"
        for row in json.loads(batch.output)["results"]
    )


def test_incomplete_or_uncertain_verdicts_do_not_enqueue_business_acceptance(
    session, business, scheduled_owner
):
    _batch, token, evidence = reviewed_batch(session, business, scheduled_owner)
    with agent_context(business, token):
        with pytest.raises(core.InvalidOperation):
            intake_review.submit_agent_batch_review(
                session,
                business.tenant.id,
                {**evidence, "reviews": evidence["reviews"][:1]},
            )
        uncertain = json.loads(json.dumps(evidence))
        uncertain["reviews"][1]["verdict"] = "uncertain"
        result = intake_review.submit_agent_batch_review(
            session, business.tenant.id, uncertain
        )
    assert result.status == "proposed"
    assert "authorization" not in json.loads(result.output)
    assert session.scalar(select(Document)) is None


def test_tampered_retained_batch_evidence_refuses_before_effects(
    session, business, scheduled_owner
):
    batch, token, evidence = reviewed_batch(session, business, scheduled_owner)
    with agent_context(business, token):
        intake_review.submit_agent_batch_review(session, business.tenant.id, evidence)
    progress = json.loads(batch.output)
    progress["authorization"]["agent_review"]["evidence"]["reviews"][0]["digest"] = (
        "0" * 64
    )
    batch.output = json.dumps(progress)
    session.flush()
    with pytest.raises(core.InvalidOperation):
        intake_batches.settle_chunk(
            session,
            business.tenant.id,
            batch.id,
            continuation_id=progress["continuation_id"],
        )
    assert session.scalar(select(Document)) is None


def test_batches_share_current_daily_quota_at_execution(
    session, business, scheduled_owner
):
    mandate_id, token = owner_mandate(session, business, scheduled_owner, daily_units=3)
    entries = prepared_orders(session, business, 4)
    batches = []
    with agent_context(business, token):
        for index in range(2):
            selected = entries[index * 2 : (index + 1) * 2]
            batch = intake_batches.prepare_batch(
                session, business.tenant.id, selected, request_id=f"quota-batch-{index}"
            )
            held = json.loads(batch.input)
            intake_review.submit_agent_batch_review(
                session,
                business.tenant.id,
                {
                    "batch_id": batch.id,
                    "manifest_digest": held["digest"],
                    "manifest_revision": held["manifest"]["revision"],
                    "reviews": [
                        reviewed_evidence(
                            session,
                            business,
                            mandate_id,
                            session.get(
                                ChangeProposal,
                                (business.tenant.id, entry["proposal_id"]),
                            ),
                        )
                        for entry in selected
                    ],
                },
            )
            batches.append(batch)
    for batch in batches:
        intake_batches.settle_chunk(
            session,
            business.tenant.id,
            batch.id,
            continuation_id=json.loads(batch.output)["continuation_id"],
        )
    assert len(list(session.scalars(select(Document)))) == 3
    assert [row["disposition"] for row in json.loads(batches[1].output)["results"]] == [
        "applied",
        "review_required",
    ]


def test_agent_worker_is_database_only_and_exact_request_replay_is_free(
    session, business, scheduled_owner, monkeypatch
):
    from reality.services import artifacts

    batch, token, evidence = reviewed_batch(session, business, scheduled_owner)
    with agent_context(business, token):
        intake_review.submit_agent_batch_review(session, business.tenant.id, evidence)
        first = batch.output
        assert (
            intake_review.submit_agent_batch_review(
                session, business.tenant.id, evidence
            ).output
            == first
        )

    def forbidden(*args, **kwargs):
        raise RuntimeError("Worker must not fetch or assess external source content")

    monkeypatch.setattr(artifacts, "materialize_artifact", forbidden)
    intake_batches.settle_chunk(
        session,
        business.tenant.id,
        batch.id,
        continuation_id=json.loads(batch.output)["continuation_id"],
    )
    with agent_context(business, token):
        assert (
            intake_review.submit_agent_batch_review(
                session, business.tenant.id, evidence
            ).status
            == "executed"
        )
    assert len(list(session.scalars(select(Document)))) == 2


def test_foreign_company_cannot_submit_agent_batch(session, business, scheduled_owner):
    _, token, evidence = reviewed_batch(session, business, scheduled_owner)
    foreign = core.create_tenant(session, "Foreign agent batch")
    with agent_context(business, token), pytest.raises(core.InvalidOperation):
        intake_review.submit_agent_batch_review(session, foreign.id, evidence)
    assert session.scalar(select(Document)) is None


def test_unknown_failure_rolls_back_every_provisional_agent_receipt(
    session, business, scheduled_owner, monkeypatch
):
    batch, token, evidence = reviewed_batch(session, business, scheduled_owner)
    with agent_context(business, token):
        intake_review.submit_agent_batch_review(session, business.tenant.id, evidence)
    continuation = json.loads(batch.output)["continuation_id"]
    original = core.create_commitment
    calls = 0

    def fail_second(*args, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise RuntimeError("Late infrastructure failure")
        return original(*args, **kwargs)

    monkeypatch.setattr(core, "create_commitment", fail_second)
    with pytest.raises(RuntimeError, match="Late infrastructure"):
        intake_batches.settle_chunk(
            session, business.tenant.id, batch.id, continuation_id=continuation
        )
    assert session.scalar(select(Document)) is None
    assert json.loads(batch.output)["next_index"] == 0
    assert all(
        session.get(ChangeProposal, (business.tenant.id, review["proposal_id"])).status
        == "proposed"
        for review in evidence["reviews"]
    )
    monkeypatch.setattr(core, "create_commitment", original)
    intake_batches.settle_chunk(
        session, business.tenant.id, batch.id, continuation_id=continuation
    )
    assert len(list(session.scalars(select(Document)))) == 2


def test_retained_agent_authority_cannot_escape_private_child_scope(
    session, business, scheduled_owner
):
    batch, token, evidence = reviewed_batch(session, business, scheduled_owner)
    with agent_context(business, token):
        intake_review.submit_agent_batch_review(session, business.tenant.id, evidence)
    with pytest.raises(core.InvalidOperation):
        intake_review._settle_agent_batch_child(
            session,
            business.tenant.id,
            evidence["reviews"][0]["proposal_id"],
            json.loads(batch.output)["authorization"],
        )
    assert session.scalar(select(Document)) is None


def test_current_token_tool_restrictions_refuse_queued_units(
    session, business, scheduled_owner
):
    batch, token, evidence = reviewed_batch(session, business, scheduled_owner)
    with agent_context(business, token):
        intake_review.submit_agent_batch_review(session, business.tenant.id, evidence)
    token.allowed_tools = '["intake_agent_review_and_execute"]'
    session.flush()
    intake_batches.settle_chunk(
        session,
        business.tenant.id,
        batch.id,
        continuation_id=json.loads(batch.output)["continuation_id"],
    )
    assert session.scalar(select(Document)) is None
    assert all(
        row["disposition"] == "review_required"
        for row in json.loads(batch.output)["results"]
    )
