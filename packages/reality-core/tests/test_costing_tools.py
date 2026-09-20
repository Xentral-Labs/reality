"""The actual application and MCP boundaries preserve confirmed owner decisions."""

import json

import pytest
import test_costing_services as cost_fixtures
from sqlalchemy import func, select
from test_costing_services import (
    assignment,
    evidence,
    receipt,
)

from reality.db.core import ChangeProposal, TenantMembership
from reality.db.costing import CostAttribution
from reality.mcp.catalog import MCP_TOOL_REGISTRY
from reality.services import core
from reality.services.analytics.reports import caller
from reality.services.memberships import Principal
from reality.tools.application import (
    approve_and_execute_proposal,
    create_change_proposal,
    run_read_tool,
)

cost_owner = cost_fixtures.cost_owner


def test_cost_tool_confirmation_replay_and_demotion(session, business, cost_owner):
    movement = receipt(session, business)
    doc = evidence(session, business)
    principal = Principal(cost_owner.id)
    args = assignment(session, business, movement, doc, "1000")
    with caller(principal):
        proposal = create_change_proposal(
            session, business.tenant.id, "cost.change", args
        )
    with pytest.raises(core.InvalidOperation, match="confirmation"):
        approve_and_execute_proposal(
            session, business.tenant.id, proposal.id, confirming_principal=principal
        )
    assert session.scalar(select(func.count()).select_from(CostAttribution)) == 0
    done = approve_and_execute_proposal(
        session,
        business.tenant.id,
        proposal.id,
        confirming_principal=principal,
        confirmed=True,
    )
    output = done.output
    repeated = approve_and_execute_proposal(
        session,
        business.tenant.id,
        proposal.id,
        confirming_principal=principal,
        confirmed=True,
    )
    assert repeated.output == output
    assert session.scalar(select(func.count()).select_from(CostAttribution)) == 1
    assert (
        run_read_tool(
            session,
            business.tenant.id,
            "cost.receipt.get",
            {"movement_id": movement.id},
        )["known_cost"]
        == "1000.0000"
    )
    member = session.scalar(
        select(TenantMembership).where(TenantMembership.user_id == cost_owner.id)
    )
    member.role = "member"
    session.commit()
    with pytest.raises(core.InvalidOperation, match="owner"):
        approve_and_execute_proposal(
            session,
            business.tenant.id,
            proposal.id,
            confirming_principal=principal,
            confirmed=True,
        )


def test_mcp_cost_schema_and_handlers_use_application_services(
    session, business, cost_owner
):
    movement = receipt(session, business)
    doc = evidence(session, business)
    command = MCP_TOOL_REGISTRY["cost_change_propose"]
    assert command.input_schema["type"] == "object"
    assert "parts" in command.input_schema["properties"]
    with caller(Principal(cost_owner.id)):
        result = command.handler(
            session,
            business.tenant.id,
            assignment(session, business, movement, doc, "1000"),
        )
    assert result["requires_human_confirmation"]
    assert session.scalar(select(func.count()).select_from(CostAttribution)) == 0
    assert (
        json.loads(session.get(ChangeProposal, result["proposal_id"]).input)[
            "operation"
        ]
        == "assign"
    )
    read = MCP_TOOL_REGISTRY["cost_evidence_get"].handler(
        session, business.tenant.id, {"document_id": doc.id}
    )
    assert read["amounts"]["net"] == "1000"
    other = core.create_tenant(session, "Other costing company")
    with pytest.raises(core.NotFound):
        MCP_TOOL_REGISTRY["cost_receipt_get"].handler(
            session, other.id, {"movement_id": movement.id}
        )
    with pytest.raises(core.NotFound):
        MCP_TOOL_REGISTRY["cost_evidence_get"].handler(
            session, other.id, {"document_id": doc.id}
        )
    with (
        caller(Principal(cost_owner.id)),
        pytest.raises((core.NotFound, core.InvalidOperation)),
    ):
        create_change_proposal(
            session,
            other.id,
            "cost.change",
            assignment(session, business, movement, doc, "1000"),
        )


def test_company_mcp_token_does_not_impersonate_a_human_owner(
    session, business, cost_owner, monkeypatch
):
    from contextlib import nullcontext
    from types import SimpleNamespace

    from reality.mcp import server

    movement = receipt(session, business)
    doc = evidence(session, business)
    monkeypatch.setattr(
        server,
        "get_access_token",
        lambda: SimpleNamespace(subject=business.tenant.id, scopes=["reality:tool:*"]),
    )
    monkeypatch.setattr(server, "Session", lambda: nullcontext(session))
    read = server._handler(MCP_TOOL_REGISTRY["cost_evidence_get"])(document_id=doc.id)
    assert read["amounts"]["net"] == "1000"
    with pytest.raises(
        core.InvalidOperation, match="authenticated active company owner"
    ):
        server._handler(MCP_TOOL_REGISTRY["cost_change_propose"])(
            **assignment(session, business, movement, doc, "1000")
        )
    assert session.scalar(select(func.count()).select_from(ChangeProposal)) == 0
