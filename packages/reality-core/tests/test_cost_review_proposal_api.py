"""The web proposes exactly what the shared draft derives (spec 282 FR-006/FR-007)."""

import json

import test_contribution_services as revenue
import test_costing_services as fixtures
import test_inventory_costing_services as stock
from sqlalchemy import func, select
from test_http_boundary import client_for

from reality.db.core import ChangeProposal
from reality.services import core

cost_owner = fixtures.cost_owner


def proposals(session, tenant):
    return session.scalar(
        select(func.count())
        .select_from(ChangeProposal)
        .where(
            ChangeProposal.tenant_id == tenant,
            ChangeProposal.type == "tool:cost.change",
        )
    )


def test_draft_read_and_submit_create_one_cost_proposal(
    session, business, cost_owner, monkeypatch
):
    billed, *_ = revenue.prepared(session, business, cost_owner)
    session.commit()
    before = proposals(session, business.tenant.id)
    client = client_for(session, monkeypatch)
    base = f"/api/tenants/{business.tenant.id}"
    draft = client.get(
        f"{base}/cost-review-draft",
        params={"kind": "contribution", "scope_id": billed.id},
    ).json()
    assert draft["open_inputs"] == [] and draft["arguments"]
    body = {
        "kind": "contribution",
        "scope_id": billed.id,
        "event_sequence": draft["event_sequence"],
    }
    created = client.post(f"{base}/cost-review-proposals", json=body)
    assert created.status_code == 201, created.text
    from reality.services.costing import _request

    proposal = session.get(ChangeProposal, (business.tenant.id, created.json()["id"]))
    # Exactly the drafted decision, in the proposal's normalized form.
    assert _request(json.loads(proposal.input)).model_dump(mode="json") == _request(
        draft["arguments"]
    ).model_dump(mode="json")
    # Submitting the same draft again is idempotent: one proposal, the same one.
    again = client.post(f"{base}/cost-review-proposals", json=body)
    assert again.json()["id"] == created.json()["id"]
    assert proposals(session, business.tenant.id) == before + 1


def test_a_drifted_draft_is_refused_with_the_new_draft(
    session, business, cost_owner, monkeypatch
):
    stock.prepared(session, business, cost_owner)
    session.commit()
    before = proposals(session, business.tenant.id)
    client = client_for(session, monkeypatch)
    base = f"/api/tenants/{business.tenant.id}"
    draft = client.get(
        f"{base}/cost-review-draft",
        params={"kind": "inventory", "scope_id": business.item.id, "method": "fifo"},
    ).json()
    core.record_movement(
        session,
        business.tenant.id,
        "shipment",
        business.item.id,
        "1",
        from_location_id=business.location.id,
    )
    session.commit()
    refused = client.post(
        f"{base}/cost-review-proposals",
        json={
            "kind": "inventory",
            "scope_id": business.item.id,
            "event_sequence": draft["event_sequence"],
            "answers": {"method": "fifo"},
        },
    )
    assert refused.status_code == 409
    detail = refused.json()["detail"]
    assert detail["code"] == "draft_changed"
    assert detail["draft"]["event_sequence"] > draft["event_sequence"]
    assert proposals(session, business.tenant.id) == before


def test_open_inputs_are_refused_until_answered(
    session, business, cost_owner, monkeypatch
):
    stock.prepared(session, business, cost_owner)
    session.commit()
    client = client_for(session, monkeypatch)
    base = f"/api/tenants/{business.tenant.id}"
    draft = client.get(
        f"{base}/cost-review-draft",
        params={"kind": "inventory", "scope_id": business.item.id},
    ).json()
    body = {
        "kind": "inventory",
        "scope_id": business.item.id,
        "event_sequence": draft["event_sequence"],
    }
    unanswered = client.post(f"{base}/cost-review-proposals", json=body)
    assert unanswered.status_code == 409
    assert (
        unanswered.json()["detail"]["draft"]["open_inputs"][0]["code"]
        == "valuation_method"
    )
    # Positive control: the answered draft is proposed.
    answered = client.post(
        f"{base}/cost-review-proposals", json={**body, "answers": {"method": "fifo"}}
    )
    assert answered.status_code == 201, answered.text


def test_the_endpoint_proposes_through_the_shared_draft(
    session, business, cost_owner, monkeypatch
):
    from reality.services import cost_review_draft as drafting

    billed, *_ = revenue.prepared(session, business, cost_owner)
    session.commit()
    calls = []
    original = drafting.cost_review_draft

    def spy(*args, **kwargs):
        calls.append(kwargs)
        return original(*args, **kwargs)

    monkeypatch.setattr(drafting, "cost_review_draft", spy)
    client = client_for(session, monkeypatch)
    base = f"/api/tenants/{business.tenant.id}"
    draft = client.get(
        f"{base}/cost-review-draft",
        params={"kind": "contribution", "scope_id": billed.id},
    ).json()
    client.post(
        f"{base}/cost-review-proposals",
        json={
            "kind": "contribution",
            "scope_id": billed.id,
            "event_sequence": draft["event_sequence"],
        },
    )
    assert len(calls) == 2


def test_foreign_scope_is_not_found(session, business, cost_owner, monkeypatch):
    billed, *_ = revenue.prepared(session, business, cost_owner)
    other = core.create_tenant(session, "Neighbor")
    session.commit()
    client = client_for(session, monkeypatch)
    assert (
        client.get(
            f"/api/tenants/{other.id}/cost-review-draft",
            params={"kind": "contribution", "scope_id": billed.id},
        ).status_code
        == 404
    )
    assert (
        client.post(
            f"/api/tenants/{other.id}/cost-review-proposals",
            json={"kind": "contribution", "scope_id": billed.id, "event_sequence": 0},
        ).status_code
        == 404
    )
