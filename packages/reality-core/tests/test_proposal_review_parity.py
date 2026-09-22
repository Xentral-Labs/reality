import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from reality.mcp.catalog import proposal_bindings, tool_definitions
from reality.services.core import NotFound, create_tenant
from reality.services.proposal_reviews import classify_proposal, proposal_review
from reality.tools.application import (
    approve_and_execute_proposal,
    create_change_proposal,
    reject_proposal,
)
from reality.web.api import database_session
from reality.web.app import app


def test_every_mcp_proposal_has_one_web_review_class():
    definitions = tool_definitions(access=("propose",))
    bindings = proposal_bindings()
    assert len(definitions) >= 102
    assert set(bindings) == {definition.name for definition in definitions}
    assert {classify_proposal(name, {}) for name in bindings.values()} <= {
        "import",
        "reference",
        "analytics_report",
        "delivery",
        "common",
    }


def test_common_review_redacts_secrets_and_restores_receipt(session, business):
    proposal = create_change_proposal(
        session,
        business.tenant.id,
        "source_record_ingest",
        {
            "source_system": "manual",
            "source_type": "test",
            "external_id": "one",
            "payload": {"api_key": "never-return", "value": "visible"},
        },
    )
    review = proposal_review(session, business.tenant.id, proposal.id)
    assert review["review_kind"] == "common"
    assert review["input"]["payload"] == {"api_key": "[redacted]", "value": "visible"}
    assert review["confirmable"] is True

    settled = approve_and_execute_proposal(
        session, business.tenant.id, proposal.id, confirmed=True
    )
    restored = proposal_review(session, business.tenant.id, settled.id)
    assert restored["status"] == "executed"
    assert restored["confirmable"] is False
    assert restored["receipt"]


def test_review_is_tenant_scoped_and_rejection_has_no_execution(session, business):
    proposal = create_change_proposal(
        session,
        business.tenant.id,
        "source_record_ingest",
        {
            "source_system": "manual",
            "source_type": "test",
            "external_id": "reject-one",
            "payload": {"value": "unchanged"},
        },
    )
    foreign = create_tenant(session, "Foreign")
    with pytest.raises(NotFound):
        proposal_review(session, foreign.id, proposal.id)

    reject_proposal(session, business.tenant.id, proposal.id)
    restored = proposal_review(session, business.tenant.id, proposal.id)
    assert restored["status"] == "rejected"
    assert restored["confirmable"] is False
    assert restored["rejectable"] is False


def test_web_list_and_review_endpoint_expose_the_same_routing(session, business):
    proposal = create_change_proposal(
        session,
        business.tenant.id,
        "payment_term_create",
        {"records": [{"code": "NET30", "name": "Net 30", "due_days": 30}]},
    )
    factory = sessionmaker(session.bind, expire_on_commit=False)

    def database():
        with factory() as connection:
            yield connection

    app.dependency_overrides[database_session] = database
    try:
        with TestClient(app) as client:
            base = f"/api/tenants/{business.tenant.id}/change-proposals"
            listed = client.get(base).json()["items"]
            row = next(item for item in listed if item["id"] == proposal.id)
            reviewed = client.get(f"{base}/{proposal.id}/review")
            assert reviewed.status_code == 200
            assert row["review_kind"] == reviewed.json()["review_kind"] == "common"
            assert row["review_label"] == reviewed.json()["label"] == "Payment term create"
            assert reviewed.json()["input"]["records"][0]["code"] == "NET30"
    finally:
        app.dependency_overrides.clear()


def test_malformed_stored_proposal_can_only_be_rejected(session, business):
    proposal = create_change_proposal(
        session,
        business.tenant.id,
        "source_record_ingest",
        {
            "source_system": "manual",
            "source_type": "test",
            "external_id": "malformed",
            "payload": {},
        },
    )
    proposal.input = "not-json"
    session.commit()

    review = proposal_review(session, business.tenant.id, proposal.id)
    assert review["review_kind"] == "retired"
    assert review["confirmable"] is False
    assert review["rejectable"] is True
    assert "malformed" in review["message"]
