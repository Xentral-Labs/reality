"""T086 source-backed owner-confirmed carrying-value assessments."""

import json

import pytest
import test_inventory_costing_services as stock
from sqlalchemy import func, select

from reality.db.core import BusinessEvent
from reality.db.inventory_costing import (
    CostInventoryMember,
    CostValuationAssessmentPart,
    CostValuationAssessmentRevision,
)
from reality.mcp.catalog import MCP_TOOL_REGISTRY
from reality.services import core
from reality.services.analytics.reports import caller
from reality.services.costing import cost_record, inventory_cost, preview_cost_change
from reality.services.memberships import Principal
from reality.tools.application import (
    approve_and_execute_proposal,
    create_change_proposal,
    run_read_tool,
)

cost_owner = stock.cost_owner


def prepared_assessment(session, business, owner, **changes):
    inventory_args, _, _ = stock.prepared(session, business, owner)
    _, inventory = stock.commit_review(session, business, owner, inventory_args)
    remaining = inventory["remaining"][0]
    member = session.scalar(
        select(CostInventoryMember)
        .where(
            CostInventoryMember.tenant_id == business.tenant.id,
            CostInventoryMember.review_id == inventory["review_id"],
        )
        .join(
            stock.CostMovementBasis,
            (stock.CostMovementBasis.tenant_id == CostInventoryMember.tenant_id)
            & (stock.CostMovementBasis.id == CostInventoryMember.movement_basis_id),
        )
        .where(stock.CostMovementBasis.movement_id == remaining["entry_movement_id"])
    )
    args = {
        "operation": "valuation_assessment",
        "expected_event_sequence": session.scalar(
            select(func.max(BusinessEvent.sequence)).where(
                BusinessEvent.tenant_id == business.tenant.id
            )
        ),
        "reason": "Source-backed lower-value review",
        "inventory_review_id": inventory["review_id"],
        "kind": "write_down",
        "effective_at": inventory["effective_at"],
        "parts": [
            {
                "inventory_member_id": member.id,
                "evidence_source_record_id": inventory_args["receipts"][0][
                    "ownership_source_record_id"
                ],
                "quantity": remaining["quantity"],
                "assessed_value": "300",
                "currency": "EUR",
            }
        ],
    }
    args.update(changes)
    return args, inventory


def commit_assessment(session, business, owner, args):
    with caller(Principal(owner.id)):
        proposal = create_change_proposal(
            session, business.tenant.id, "cost.change", args
        )
    done = approve_and_execute_proposal(
        session,
        business.tenant.id,
        proposal.id,
        confirming_principal=Principal(owner.id),
        confirmed=True,
    )
    return json.loads(done.output)


def test_write_down_preview_confirmation_replay_and_atomic_audit(
    session, business, cost_owner
):
    args, inventory = prepared_assessment(session, business, cost_owner)
    preview = preview_cost_change(
        session, business.tenant.id, args, principal=Principal(cost_owner.id)
    )
    assert preview["review"]["assessment"] == {
        "acquisition_value": "420.0000",
        "assessed_value": "300.0000",
        "adjustment": "-120.0000",
        "quantity": "40.0000",
    }
    assert preview["review"]["inventory_review_id"] == inventory["review_id"]
    assert (
        session.scalar(
            select(func.count()).select_from(CostValuationAssessmentRevision)
        )
        == 0
    )

    with caller(Principal(cost_owner.id)):
        proposal = create_change_proposal(
            session, business.tenant.id, "cost.change", args
        )
    done = approve_and_execute_proposal(
        session,
        business.tenant.id,
        proposal.id,
        confirming_principal=Principal(cost_owner.id),
        confirmed=True,
    )
    result = json.loads(done.output)
    assert result["assessment_revision_id"]
    assert result["revision"] == 1
    assert result["assessment"] == preview["review"]["assessment"]
    assert (
        session.scalar(
            select(func.count()).select_from(CostValuationAssessmentRevision)
        )
        == 1
    )
    assert (
        session.scalar(select(func.count()).select_from(CostValuationAssessmentPart))
        == 1
    )
    replay = approve_and_execute_proposal(
        session,
        business.tenant.id,
        proposal.id,
        confirming_principal=Principal(cost_owner.id),
        confirmed=True,
    )
    assert json.loads(replay.output) == result


def test_stale_foreign_member_and_missing_source_refuse_without_partial_rows(
    session, business, cost_owner
):
    args, _ = prepared_assessment(session, business, cost_owner)
    invalid = json.loads(json.dumps(args))
    invalid["parts"][0]["inventory_member_id"] = "inv_foreign_or_missing"
    with pytest.raises(core.NotFound):
        preview_cost_change(
            session,
            business.tenant.id,
            invalid,
            principal=Principal(cost_owner.id),
        )
    invalid = json.loads(json.dumps(args))
    invalid["parts"][0]["evidence_source_record_id"] = "src_foreign_or_missing"
    with pytest.raises(core.NotFound):
        preview_cost_change(
            session,
            business.tenant.id,
            invalid,
            principal=Principal(cost_owner.id),
        )
    args["expected_event_sequence"] -= 1
    with pytest.raises(core.Conflict, match="stale"):
        preview_cost_change(
            session,
            business.tenant.id,
            args,
            principal=Principal(cost_owner.id),
        )
    assert (
        session.scalar(
            select(func.count()).select_from(CostValuationAssessmentRevision)
        )
        == 0
    )


def test_recovery_supersedes_exact_scope_and_member_cannot_approve(
    session, business, cost_owner
):
    args, _ = prepared_assessment(session, business, cost_owner)
    with caller(Principal(cost_owner.id)):
        proposal = create_change_proposal(
            session, business.tenant.id, "cost.change", args
        )
    first = json.loads(
        approve_and_execute_proposal(
            session,
            business.tenant.id,
            proposal.id,
            confirming_principal=Principal(cost_owner.id),
            confirmed=True,
        ).output
    )
    recovery = json.loads(json.dumps(args))
    recovery.update(
        kind="recovery",
        supersedes_id=first["assessment_revision_id"],
        expected_event_sequence=session.scalar(
            select(func.max(BusinessEvent.sequence)).where(
                BusinessEvent.tenant_id == business.tenant.id
            )
        ),
        reason="Source-backed recovery review",
    )
    recovery["parts"][0]["assessed_value"] = "400"
    with caller(Principal(cost_owner.id)):
        proposal = create_change_proposal(
            session, business.tenant.id, "cost.change", recovery
        )
    second = json.loads(
        approve_and_execute_proposal(
            session,
            business.tenant.id,
            proposal.id,
            confirming_principal=Principal(cost_owner.id),
            confirmed=True,
        ).output
    )
    assert second["revision"] == 2
    assert second["assessment"]["assessed_value"] == "400.0000"
    assert second["assessment"]["adjustment"] == "-20.0000"

    membership = session.scalar(
        select(stock.TenantMembership).where(
            stock.TenantMembership.tenant_id == business.tenant.id,
            stock.TenantMembership.user_id == cost_owner.id,
        )
    )
    membership.role = "member"
    session.flush()
    with pytest.raises(core.InvalidOperation, match="owner"):
        preview_cost_change(
            session,
            business.tenant.id,
            recovery,
            principal=Principal(cost_owner.id),
        )


def test_current_and_historical_inventory_reads_derive_carrying_bridge(
    session, business, cost_owner
):
    args, inventory = prepared_assessment(session, business, cost_owner)
    assessment = commit_assessment(session, business, cost_owner, args)

    current = inventory_cost(session, business.tenant.id, business.item.id)
    assert current["review_state"] == "reviewed_complete_at_cutoff"
    assert current["acquisition_value"] == "420.0000"
    assert current["carrying_value"] == "300.0000"
    assert current["carrying_adjustment"] == "-120.0000"
    assert current["carrying_value_state"] == "reviewed_assessment"
    assert (
        current["valuation_assessment"]["assessment_revision_id"]
        == assessment["assessment_revision_id"]
    )

    historical = inventory_cost(
        session,
        business.tenant.id,
        business.item.id,
        review_id=inventory["review_id"],
        assessment_revision_id=assessment["assessment_revision_id"],
    )
    assert historical["carrying_value"] == "300.0000"
    assert historical["acquisition_value"] == "420.0000"

    core.record_movement(
        session,
        business.tenant.id,
        "receipt",
        business.item.id,
        "1",
        to_location_id=business.location.id,
    )
    stale = inventory_cost(session, business.tenant.id, business.item.id)
    assert stale["review_state"] == "stale"
    assert stale["carrying_value"] is None
    replay = inventory_cost(
        session,
        business.tenant.id,
        business.item.id,
        review_id=inventory["review_id"],
        assessment_revision_id=assessment["assessment_revision_id"],
    )
    assert replay["carrying_value"] == "300.0000"


def test_assessment_inspection_and_shared_read_tool_pass_through(
    session, business, cost_owner
):
    args, inventory = prepared_assessment(session, business, cost_owner)
    assessment = commit_assessment(session, business, cost_owner, args)
    revision_id = assessment["assessment_revision_id"]

    record = cost_record(
        session,
        business.tenant.id,
        "cost_valuation_assessment_revision",
        revision_id,
    )
    assert record["fields"]["inventory_review_id"] == inventory["review_id"]
    assert record["member_page"]["total"] == 1
    part_link = record["sections"][2]["rows"][0]["link"]
    assert part_link["kind"] == "cost_valuation_assessment_part"
    part = cost_record(
        session, business.tenant.id, kind=part_link["kind"], record_id=part_link["id"]
    )
    assert part["fields"]["assessed_value"] == "300.0000"
    assert {row["link"]["kind"] for row in part["sections"][1]["rows"]} >= {
        "cost_inventory_member",
        "source_record",
    }

    read_args = {
        "item_id": business.item.id,
        "review_id": inventory["review_id"],
        "assessment_revision_id": revision_id,
    }
    expected = inventory_cost(session, business.tenant.id, **read_args)
    assert (
        run_read_tool(session, business.tenant.id, "cost.inventory.get", read_args)
        == expected
    )
    tool = MCP_TOOL_REGISTRY["cost_inventory_get"]
    assert "assessment_revision_id" in tool.input_schema["properties"]
    assert tool.handler(session, business.tenant.id, read_args) == expected
