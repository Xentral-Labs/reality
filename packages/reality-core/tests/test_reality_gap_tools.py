from __future__ import annotations

from reality.mcp.catalog import dispatch_tool, model_tool_schemas
from reality.tools.application import approve_and_execute_proposal, run_read_tool


def test_gap_capture_uses_one_proposal_boundary_for_mcp_and_application(
    session, business
):
    arguments = {
        "question": "Which orders are express?",
        "intended_use": "Prioritize warehouse work",
        "origin": "mcp",
        "idempotency_key": "mcp-gap-1",
    }
    proposal = dispatch_tool(
        session,
        business.tenant.id,
        "reality_gap_create_propose",
        arguments,
        allowed_access=("propose",),
    )
    assert run_read_tool(session, business.tenant.id, "reality_gaps")["total"] == 0
    executed = approve_and_execute_proposal(
        session, business.tenant.id, proposal["proposal_id"]
    )
    assert executed.status == "executed"
    assert run_read_tool(session, business.tenant.id, "reality_gaps")["total"] == 1


def test_gap_mcp_surface_exposes_complete_lifecycle_tools():
    schemas = model_tool_schemas(access=("read", "propose"))
    names = {row["function"]["name"] for row in schemas}
    assert {
        "reality_gaps",
        "reality_gap_get",
        "reality_gap_simulate",
        "reality_gap_create_propose",
        "reality_gap_entry_add_propose",
        "reality_gap_recommend_propose",
        "reality_gap_decide_propose",
        "reality_gap_implementation_prepare_propose",
        "reality_gap_rule_activate_propose",
        "reality_gap_rule_disable_propose",
        "reality_gap_rule_replay_propose",
    } <= names
    replay = next(
        row
        for row in schemas
        if row["function"]["name"] == "reality_gap_rule_replay_propose"
    )
    assert "cursor" in replay["function"]["parameters"]["properties"]
