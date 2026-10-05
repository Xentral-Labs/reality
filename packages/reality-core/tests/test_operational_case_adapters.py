"""All adapters expose shared reads and retain human responsibility authority."""

import json

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from test_operational_cases import activate, order

from reality.db.core import BusinessEvent, TenantMembership
from reality.services import core
from reality.services import operational_cases as cases
from reality.services.memberships import Principal
from reality.services.proposal_reviews import proposal_review
from reality.tools.application import (
    approve_and_execute_proposal,
    create_change_proposal,
    run_read_tool,
)
from reality.web.api import database_session
from reality.web.app import app


def test_existing_order_review_receipt_and_mcp_reads_expose_same_cases(
    session, business, scheduled_owner
):
    activate(session, business, scheduled_owner)
    promise = order(session, business)
    case_ids = cases.object_cases(session, business.tenant.id, "commitment", promise.id)
    from reality.mcp.catalog import dispatch_tool

    read = dispatch_tool(
        session,
        business.tenant.id,
        "operational_case_object",
        {"record_type": "document", "record_id": promise.document_id},
    )
    assert read["case_ids"] == case_ids
    assert (
        run_read_tool(
            session,
            business.tenant.id,
            "order_explain",
            {"order_reference": promise.document_id},
        )["case_ids"]
        == case_ids
    )
    proposal = create_change_proposal(
        session,
        business.tenant.id,
        "commitment_revise",
        {"commitment_id": promise.id, "quantity": "20"},
    )
    assert (
        proposal_review(session, business.tenant.id, proposal.id)["case_ids"]
        == case_ids
    )
    approve_and_execute_proposal(
        session,
        business.tenant.id,
        proposal.id,
        confirming_principal=Principal(scheduled_owner.id),
        review_token=json.loads(proposal.input)["_delivery_review"]["token"],
        confirmed=True,
    )
    receipt_before = proposal.output
    assert (
        run_read_tool(
            session,
            business.tenant.id,
            "proposal_execution_status",
            {"proposal_id": proposal.id},
        )["case_ids"]
        == case_ids
    )
    assert proposal.output == receipt_before


def test_reads_are_pure_and_historical_associations_are_explicitly_empty(
    session, business
):
    promise = order(session, business)
    before = list(
        session.scalars(
            select(BusinessEvent.id).where(
                BusinessEvent.tenant_id == business.tenant.id
            )
        )
    )
    for _ in range(2):
        assert (
            cases.object_cases(
                session, business.tenant.id, "document", promise.document_id
            )
            == []
        )
        assert cases.list_cases(session, business.tenant.id) == []
        assert (
            run_read_tool(
                session,
                business.tenant.id,
                "order_explain",
                {"order_reference": promise.document_id},
            )["case_ids"]
            == []
        )
    assert (
        list(
            session.scalars(
                select(BusinessEvent.id).where(
                    BusinessEvent.tenant_id == business.tenant.id
                )
            )
        )
        == before
    )


def test_generic_control_requires_observed_human_not_actor_label_or_external_confirmation(
    session, business, scheduled_owner
):
    activate(session, business, scheduled_owner)
    promise = order(session, business)
    case_id = cases.object_cases(session, business.tenant.id, "commitment", promise.id)[
        0
    ]
    proposal = create_change_proposal(
        session,
        business.tenant.id,
        "operational_case_takeover",
        {"case_id": case_id, "expected_revision": 1, "request_key": "control"},
    )
    with pytest.raises(core.InvalidOperation, match="authenticated human"):
        approve_and_execute_proposal(
            session, business.tenant.id, proposal.id, confirmed=True
        )
    assert (
        cases.explain(session, business.tenant.id, case_id)["control_mode"]
        == "automation"
    )
    assert proposal.status == "proposed"
    # Responsibility controls have no external claim; rejection leaves no uncertainty.
    second = create_change_proposal(
        session,
        business.tenant.id,
        "operational_case_takeover",
        {"case_id": case_id, "expected_revision": 1, "request_key": "human-control"},
    )
    approve_and_execute_proposal(
        session,
        business.tenant.id,
        second.id,
        confirmed=True,
        confirming_principal=Principal(scheduled_owner.id),
    )
    assert (
        cases.explain(session, business.tenant.id, case_id)["control_mode"] == "human"
    )


def test_web_uses_shared_controls_and_denies_nonmember_after_revocation(
    session, business, scheduled_owner, monkeypatch
):
    from reality.web import operational_cases as web_cases

    activate(session, business, scheduled_owner)
    promise = order(session, business)
    case_id = cases.object_cases(session, business.tenant.id, "commitment", promise.id)[
        0
    ]
    monkeypatch.setattr(
        web_cases, "request_principal", lambda request: Principal(scheduled_owner.id)
    )
    app.dependency_overrides[database_session] = lambda: session
    try:
        with TestClient(app) as client:
            base = f"/api/tenants/{business.tenant.id}/operational-cases"
            read = client.get(base)
            assert read.status_code == 200, read.text
            assert read.json()[0]["case_id"] == case_id
            taken = client.post(
                base + f"/{case_id}/takeover",
                json={
                    "expected_revision": 1,
                    "request_key": "web-take",
                    "confirmed": True,
                },
            )
            assert taken.status_code == 200, taken.text
            review = client.get(base + f"/{case_id}/handback-review").json()
            returned = client.post(
                base + f"/{case_id}/handback",
                json={
                    "review_digest": review["digest"],
                    "request_key": "web-return",
                    "confirmed": True,
                },
            )
            assert returned.status_code == 200, returned.text
            member = session.scalar(
                select(TenantMembership).where(
                    TenantMembership.tenant_id == business.tenant.id,
                    TenantMembership.user_id == scheduled_owner.id,
                )
            )
            member.status = "removed"
            session.flush()
            denied = client.post(
                base + f"/{case_id}/takeover",
                json={
                    "expected_revision": 3,
                    "request_key": "revoked",
                    "confirmed": True,
                },
            )
            assert denied.status_code in {403, 404}
    finally:
        app.dependency_overrides.clear()


def test_direct_control_replay_does_not_duplicate_audit_and_changed_request_refuses(
    session, business, scheduled_owner
):
    activate(session, business, scheduled_owner)
    promise = order(session, business)
    case_id = cases.object_cases(session, business.tenant.id, "commitment", promise.id)[
        0
    ]
    args = {
        "expected_revision": 1,
        "request_key": "stable",
        "confirmed": True,
        "reason": "Repair externally",
    }
    first = cases.takeover(
        session, business.tenant.id, case_id, Principal(scheduled_owner.id), **args
    )
    assert (
        cases.takeover(
            session, business.tenant.id, case_id, Principal(scheduled_owner.id), **args
        )
        == first
    )
    assert (
        len(
            list(
                session.scalars(
                    select(BusinessEvent).where(
                        BusinessEvent.tenant_id == business.tenant.id,
                        BusinessEvent.event_type == "operational_case.taken_over",
                    )
                )
            )
        )
        == 1
    )
    with pytest.raises(core.InvalidOperation, match="different case control"):
        cases.takeover(
            session,
            business.tenant.id,
            case_id,
            Principal(scheduled_owner.id),
            **{**args, "reason": "Different meaning"},
        )


def test_foreign_case_tools_and_links_cannot_cross_tenant(
    session, business, scheduled_owner
):
    from sqlalchemy.exc import IntegrityError

    from reality.db.operational_cases import CaseCommitmentLink, OperationalCase
    from reality.services.case_action_guards import execution_context
    from reality.tools.application import TOOLS

    activate(session, business, scheduled_owner)
    promise = order(session, business)
    foreign = core.create_tenant(session, "Foreign cases")
    party = core.create_party(session, foreign.id, "Foreign customer", "customer")
    doc = core.create_document(session, foreign.id, "sales_order", "FOREIGN", party.id, "0")
    foreign_case = OperationalCase(
        id=core.uid("case"),
        tenant_id=foreign.id,
        kind="order_fulfillment",
        order_document_id=doc.id,
    )
    session.add(foreign_case)
    session.flush()
    tenant_id = business.tenant.id
    assert all(
        row["case_id"] != foreign_case.id
        for row in run_read_tool(session, tenant_id, "operational_case_list")
    )
    for name in ["operational_case_explain", "operational_case_handback_preview"]:
        with pytest.raises(core.NotFound):
            run_read_tool(session, tenant_id, name, {"case_id": foreign_case.id})
    with pytest.raises(core.NotFound):
        run_read_tool(
            session,
            tenant_id,
            "operational_case_object",
            {"record_type": "document", "record_id": doc.id},
        )
    with execution_context(
        session, tenant_id, automatic=False, principal=Principal(scheduled_owner.id)
    ):
        for name, args in [
            (
                "operational_case_takeover",
                {
                    "case_id": foreign_case.id,
                    "expected_revision": 1,
                    "request_key": "foreign-take",
                },
            ),
            (
                "operational_case_handback",
                {
                    "case_id": foreign_case.id,
                    "review_digest": "0" * 64,
                    "request_key": "foreign-back",
                },
            ),
        ]:
            with pytest.raises(core.NotFound):
                TOOLS[name].handler(session, tenant_id, args)
    with pytest.raises(core.NotFound):
        cases.adopt(
            session,
            foreign.id,
            Principal(scheduled_owner.id),
            confirmed=True,
            request_key="foreign-adopt",
        )
    with pytest.raises(IntegrityError), session.begin_nested():
        session.add(
            CaseCommitmentLink(
                tenant_id=tenant_id, case_id=foreign_case.id, commitment_id=promise.id
            )
        )
        session.flush()
