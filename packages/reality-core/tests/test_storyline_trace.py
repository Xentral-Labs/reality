"""Spec 182 FR-004: the call trace of a storyline run."""

import json

import pytest
from sqlalchemy import select

from reality.db.core import (
    AppUser,
    PlaygroundRun,
    PlaygroundStep,
    StorylineTraceEntry,
    now,
    uid,
)
from reality.services.core import NotFound, record_movement
from reality.storyline import recorder
from reality.tools.application import (
    approve_and_execute_proposal,
    create_change_proposal,
    reject_proposal,
    run_read_tool,
)


@pytest.fixture(autouse=True)
def fresh_cache():
    recorder.clear_cache()
    yield
    recorder.clear_cache()


def storyline_run(session, tenant_id: str) -> PlaygroundRun:
    """Mark a tenant as a storyline company: orchestration metadata, no business data."""
    owner = AppUser(
        id=uid("usr"),
        email=f"{uid('mail')}@example.test",
        password_hash="unused",
        status="active",
        email_verified_at=now(),
    )
    session.add(owner)
    session.flush()
    run = PlaygroundRun(
        id=uid("run"),
        tenant_id=tenant_id,
        owner_user_id=owner.id,
        preset_key="storyline",
        sandbox_kind="practice",
        preset_version=1,
        lesson_key="storyline",
        lesson_version=1,
        client_request_key=uid("req"),
        status="active",
        ready_at=now(),
        storyline_key="order-to-close",
        storyline_version=1,
    )
    session.add(run)
    session.flush()
    recorder.clear_cache(tenant_id)
    return run


def entries(session, tenant_id: str) -> list[StorylineTraceEntry]:
    return list(
        session.scalars(
            select(StorylineTraceEntry)
            .where(StorylineTraceEntry.tenant_id == tenant_id)
            .order_by(StorylineTraceEntry.ordinal)
        )
    )


def commitment(session, business):
    from reality.services.core import create_commitment

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
        None,
    )


def test_reads_are_recorded_only_for_storyline_tenants(session, business):
    tenant_id = business.tenant.id
    run_read_tool(session, tenant_id, "exceptions", {})
    assert entries(session, tenant_id) == []

    run = storyline_run(session, tenant_id)
    result = run_read_tool(session, tenant_id, "exceptions", {})

    recorded = entries(session, tenant_id)
    assert [(e.kind, e.name, e.access, e.actor) for e in recorded] == [
        ("read", "exceptions", "read", "mcp")
    ]
    assert recorded[0].run_id == run.id
    assert recorded[0].step_id is None
    assert recorded[0].result == json.loads(json.dumps(result, default=str))
    assert recorded[0].duration_ms is not None

    with pytest.raises(NotFound):
        run_read_tool(session, tenant_id, "no_such_tool", {})
    assert entries(session, tenant_id)[-1].kind == "error"
    assert "NotFound" in entries(session, tenant_id)[-1].result["error"]


def test_proposals_confirmations_and_rejections_carry_markers(session, business):
    tenant_id = business.tenant.id
    storyline_run(session, tenant_id)
    first = commitment(session, business)
    second = commitment(session, business)
    before = len(entries(session, tenant_id))

    proposal = create_change_proposal(
        session, tenant_id, "reserve", {"commitment_id": first.id}
    )
    token = json.loads(proposal.input)["_delivery_review"]["token"]
    executed = approve_and_execute_proposal(
        session, tenant_id, proposal.id, review_token=token, confirmed=True
    )
    other = create_change_proposal(
        session, tenant_id, "reserve", {"commitment_id": second.id}
    )
    reject_proposal(session, tenant_id, other.id)

    recorded = entries(session, tenant_id)[before:]
    assert [(e.kind, e.name, e.proposal_id) for e in recorded] == [
        ("propose", "reserve", proposal.id),
        ("confirm", "reserve", proposal.id),
        ("propose", "reserve", other.id),
        ("reject", "reserve", other.id),
    ]
    propose, confirm, _, reject = recorded
    assert propose.input["commitment_id"] == first.id
    assert propose.marker_sequence is None
    assert confirm.marker_sequence is not None
    assert confirm.marker_at is not None
    assert isinstance(confirm.before_exceptions, list)
    assert (
        confirm.result["reservation_id"]
        == json.loads(executed.output)["reservation_id"]
    )
    assert reject.access == "confirm"


def test_a_scope_attaches_the_chapter_step_and_the_actor(session, business):
    tenant_id = business.tenant.id
    run = storyline_run(session, tenant_id)
    step = PlaygroundStep(
        id=uid("stp"),
        tenant_id=tenant_id,
        run_id=run.id,
        sequence=1,
        request_key="chapter-1",
        proposal_id=None,
        lesson_step_key="order",
    )
    session.add(step)
    session.flush()

    with recorder.trace_scope(tenant_id, run.id, step_id=step.id):
        run_read_tool(session, tenant_id, "exceptions", {})
    run_read_tool(session, tenant_id, "exceptions", {})

    scoped, unscoped = entries(session, tenant_id)
    assert (scoped.step_id, scoped.actor) == (step.id, "storyline")
    assert (unscoped.step_id, unscoped.actor) == (None, "mcp")
    assert (
        recorder.read_trace(session, tenant_id, run.id, step_id=step.id)["items"][0][
            "step_id"
        ]
        == step.id
    )


def test_entries_are_bounded_and_the_run_keeps_a_ring(session, business, monkeypatch):
    tenant_id = business.tenant.id
    run = storyline_run(session, tenant_id)
    target = recorder.TraceScope(tenant_id, run.id)
    monkeypatch.setattr(recorder, "ENTRY_BYTE_BOUND", 200)
    monkeypatch.setattr(recorder, "RUN_ENTRY_LIMIT", 3)

    big = recorder.record(
        session, target, kind="read", name="exceptions", input={"blob": "x" * 500}
    )
    assert big.input["truncated"] is True
    assert big.input["bytes"] > 200
    for index in range(4):
        recorder.record(session, target, kind="view", name=f"/parties/{index}")

    remaining = entries(session, tenant_id)
    assert [e.ordinal for e in remaining] == [3, 4, 5]
    page = recorder.read_trace(session, tenant_id, run.id, limit=2)
    assert [item["ordinal"] for item in page["items"]] == [3, 4]
    assert page["has_more"] is True

    other_tenant = uid("ten")
    assert entries(session, other_tenant) == []
    with pytest.raises(ValueError):
        recorder.record(session, target, kind="nope", name="x")


def test_http_views_are_recorded_for_storyline_tenants_only(
    session, business, monkeypatch
):
    from tests.test_http_boundary import client_for

    tenant_id = business.tenant.id
    client = client_for(session, monkeypatch)
    assert client.get(f"/api/tenants/{tenant_id}/parties").status_code == 200
    assert entries(session, tenant_id) == []

    storyline_run(session, tenant_id)
    session.commit()
    assert client.get(f"/api/tenants/{tenant_id}/parties?q=Acme").status_code == 200
    assert client.get(f"/api/tenants/{tenant_id}/activity-signal").status_code == 200

    session.expire_all()
    recorded = entries(session, tenant_id)
    assert [(e.kind, e.name, e.actor, e.access) for e in recorded] == [
        ("view", "/parties", "person", "read")
    ]
    assert recorded[0].input == {"q": "Acme"}
    assert recorded[0].result == {"status": 200}
