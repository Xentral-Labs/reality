"""Private reviews disclose held changes only to their original active author."""

import json
from uuid import uuid4

import pytest
from cryptography.fernet import Fernet
from test_proposal_decision_policy import _member
from test_reporting_graph_lifecycle import _propose

from reality.services.analytics.reports import caller
from reality.services.core import NotFound, create_tenant
from reality.services.memberships import Principal
from reality.services.proposal_reviews import proposal_review
from reality.tools.application import create_change_proposal


def test_author_reads_private_change_without_carrier_and_storage_is_unchanged(
    session, business, scheduled_owner
):
    author = Principal(scheduled_owner.id)
    proposal = _propose(session, business, author)
    original = proposal.input
    result = proposal_review(session, business.tenant.id, proposal.id, principal=author)
    assert result["private_review"]["state"] == "readable"
    assert result["private_review"]["details"]["operation"] == "create"
    assert result["private_review"]["details"]["name"]
    assert result["private_review"]["details"]["definition"]["from_"] == "order"
    assert "private_report_change" not in result["input"]
    assert json.loads(original)["private_report_change"] not in json.dumps(result)
    assert result["confirmable"] is True
    session.refresh(proposal)
    assert proposal.input == original


@pytest.mark.parametrize("identity", ["none", "member", "owner", "removed"])
def test_other_readers_cannot_read_or_review_private_content(
    session, business, scheduled_owner, identity
):
    proposal = _propose(session, business, Principal(scheduled_owner.id))
    user, membership = _member(session, business.tenant.id)
    if identity == "owner":
        membership.role = "owner"
    if identity == "removed":
        membership.status = "removed"
    session.flush()
    principal = None if identity == "none" else Principal(user.id)
    result = proposal_review(
        session, business.tenant.id, proposal.id, principal=principal
    )
    assert result["private_review"]["state"] == "hidden"
    assert not result["private_review"].get("details")
    assert result["input"] == {}
    assert result["preview"] == {}
    assert result["receipt"] == {}
    assert result["confirmable"] is False
    assert result["rejectable"] is True


def test_unreadable_private_payload_can_be_rejected_without_exposing_ciphertext(
    session, business, scheduled_owner
):
    proposal = _propose(session, business, Principal(scheduled_owner.id))
    payload = json.loads(proposal.input)
    payload["private_report_change"] = (
        Fernet(Fernet.generate_key()).encrypt(b"{}").decode()
    )
    proposal.input = json.dumps(payload)
    session.flush()
    result = proposal_review(
        session,
        business.tenant.id,
        proposal.id,
        principal=Principal(scheduled_owner.id),
    )
    assert result["private_review"]["state"] == "unavailable"
    assert result["confirmable"] is False
    assert result["rejectable"] is True
    assert payload["private_report_change"] not in json.dumps(result)


def test_private_request_uses_same_author_boundary_without_asking_question(
    session, business, scheduled_owner
):
    principal = Principal(scheduled_owner.id)
    with caller(principal):
        proposal = create_change_proposal(
            session,
            business.tenant.id,
            "graph.requests.create",
            {
                "request_id": str(uuid4()),
                "question": {
                    "from": "order",
                    "as": "o",
                    "measures": ["stated_order_amount"],
                    "group_by": [{"field": "o.currency"}],
                },
            },
        )
    original = proposal.input
    result = proposal_review(
        session, business.tenant.id, proposal.id, principal=principal
    )
    assert result["private_review"]["state"] == "readable"
    assert result["private_review"]["details"]["question"]["from"] == "order"
    assert result["input"] == {}
    assert json.loads(original)["requested_analysis"] not in json.dumps(result)
    assert proposal.status == "proposed"
    assert proposal.input == original
    foreign = create_tenant(session, "Foreign private review")
    with pytest.raises(NotFound):
        proposal_review(session, foreign.id, proposal.id, principal=principal)


def test_private_receipt_stays_hidden_from_other_active_owner(
    session, business, scheduled_owner
):
    proposal = _propose(session, business, Principal(scheduled_owner.id))
    proposal.status = "executed"
    proposal.output = json.dumps({"name": "Confidential saved report"})
    user, membership = _member(session, business.tenant.id)
    membership.role = "owner"
    session.flush()
    result = proposal_review(
        session, business.tenant.id, proposal.id, principal=Principal(user.id)
    )
    assert result["private_review"]["state"] == "hidden"
    assert result["receipt"] == {}
    assert "Confidential saved report" not in json.dumps(result)


def test_web_review_forwards_authenticated_principal(
    session, business, scheduled_owner, monkeypatch
):
    from fastapi.testclient import TestClient

    from reality.web import api
    from reality.web.app import app

    proposal = _propose(session, business, Principal(scheduled_owner.id))
    principals = []
    original = api.optional_request_principal

    def principal(request):
        principals.append(request)
        return Principal(scheduled_owner.id)

    def database():
        yield session

    monkeypatch.setattr(api, "optional_request_principal", principal)
    app.dependency_overrides[api.database_session] = database
    try:
        with TestClient(app) as client:
            response = client.get(
                f"/api/tenants/{business.tenant.id}/change-proposals/{proposal.id}/review"
            )
        assert response.status_code == 200
        assert response.json()["private_review"]["state"] == "readable"
        assert principals
    finally:
        app.dependency_overrides.pop(api.database_session, None)
        monkeypatch.setattr(api, "optional_request_principal", original)


def test_original_author_with_removed_membership_cannot_read(
    session, business, scheduled_owner
):
    from sqlalchemy import select

    from reality.db.core import TenantMembership

    principal = Principal(scheduled_owner.id)
    proposal = _propose(session, business, principal)
    membership = session.scalar(
        select(TenantMembership).where(
            TenantMembership.tenant_id == business.tenant.id,
            TenantMembership.user_id == scheduled_owner.id,
        )
    )
    membership.status = "removed"
    session.flush()
    result = proposal_review(
        session, business.tenant.id, proposal.id, principal=principal
    )
    assert result["private_review"]["state"] == "hidden"
    assert result["confirmable"] is False


def test_retired_private_report_also_withholds_receipt(
    session, business, scheduled_owner
):
    proposal = _propose(session, business, Principal(scheduled_owner.id))
    proposal.type = "tool:analytics.reports.change"
    proposal.status = "executed"
    proposal.output = json.dumps({"name": "Retired private name"})
    session.flush()
    result = proposal_review(session, business.tenant.id, proposal.id)
    assert result["private_review"]["state"] == "hidden"
    assert result["receipt"] == {}
    assert "Retired private name" not in json.dumps(result)
