"""Cost guidance names the ordered steps to a proven value (spec 279, US2/US3)."""

import json

import pytest
import test_contribution_services as revenue
import test_cost_records as reviewed
import test_costing_services as fixtures
import test_inventory_costing_services as stock
from sqlalchemy import func, select

from reality.db.core import BusinessEvent, ChangeProposal
from reality.mcp.catalog import MCP_TOOL_REGISTRY
from reality.services import core
from reality.services.analytics.reports import caller
from reality.services.costing import cost_query
from reality.services.memberships import Principal
from reality.tools.application import create_change_proposal

cost_owner = fixtures.cost_owner


def guidance(session, business, kind, scope_id):
    return cost_query(session, business.tenant.id, kind=kind, scope_id=scope_id)[
        "guidance"
    ]


def states(result):
    return [(step["code"], step["state"]) for step in result["steps"]]


def first_open(result):
    return next(step for step in result["steps"] if step["state"] == "open")


def propose(session, business, owner, args):
    with caller(Principal(owner.id)):
        return create_change_proposal(session, business.tenant.id, "cost.change", args)


# Inventory scope ----------------------------------------------------------------


def test_item_without_receipts_starts_at_the_inventory_review(session, business):
    result = guidance(session, business, "inventory", business.item.id)
    assert result["reason_code"] == "inventory_scope_not_reviewed"
    assert states(result) == [
        ("inventory_review", "open"),
        ("owner_confirmation", "blocked"),
    ]
    step = first_open(result)
    assert step["role"] == "member" and step["path"] == "chat"


def test_receipt_without_cost_is_the_first_open_step(session, business):
    receipt = fixtures.receipt(session, business)
    result = guidance(session, business, "inventory", business.item.id)
    assert states(result) == [
        ("receipt_cost_evidence", "open"),
        ("inventory_review", "blocked"),
        ("owner_confirmation", "blocked"),
    ]
    step = first_open(result)
    assert step["targets"] == [receipt.id]
    assert step["target_count"] == 1


def test_reviewed_receipts_open_the_inventory_review(session, business, cost_owner):
    stock.prepared(session, business, cost_owner)
    result = guidance(session, business, "inventory", business.item.id)
    assert states(result) == [
        ("receipt_cost_evidence", "done"),
        ("inventory_review", "open"),
        ("owner_confirmation", "blocked"),
    ]


def test_waiting_proposal_links_the_owner_confirmation(session, business, cost_owner):
    args, _, _ = stock.prepared(session, business, cost_owner)
    proposal = propose(session, business, cost_owner, args)
    result = guidance(session, business, "inventory", business.item.id)
    assert states(result) == [
        ("receipt_cost_evidence", "done"),
        ("inventory_review", "done"),
        ("owner_confirmation", "open"),
    ]
    owner_step = first_open(result)
    assert owner_step["proposal_id"] == proposal.id
    assert owner_step["role"] == "owner" and owner_step["path"] == "decision_review"


def test_confirmed_current_review_needs_no_steps(session, business, cost_owner):
    args, _, _ = stock.prepared(session, business, cost_owner)
    stock.commit_review(session, business, cost_owner, args)
    result = guidance(session, business, "inventory", business.item.id)
    assert result["reason_code"] == "cost_complete"
    assert result["steps"] == []


def test_stale_review_names_the_renewal_after_the_new_receipt(
    session, business, cost_owner
):
    args, _, _ = stock.prepared(session, business, cost_owner)
    stock.commit_review(session, business, cost_owner, args)
    late = fixtures.receipt(session, business)
    result = guidance(session, business, "inventory", business.item.id)
    assert result["reason_code"] == "inventory_review_stale"
    assert states(result) == [
        ("receipt_cost_evidence", "open"),
        ("inventory_review_renew", "blocked"),
        ("owner_confirmation", "blocked"),
    ]
    assert first_open(result)["targets"] == [late.id]


def test_inventory_guidance_explains_a_missing_carrying_value(
    session, business, cost_owner
):
    args, _, _ = stock.prepared(session, business, cost_owner)
    stock.commit_review(session, business, cost_owner, args)
    result = guidance(session, business, "inventory", business.item.id)
    assert result["value_reasons"] == {"carrying_value": "assessment_missing"}


# Contribution scope --------------------------------------------------------------


def test_contribution_reports_the_upstream_inventory_blocker(
    session, business, cost_owner
):
    billed, *_ = revenue.prepared(session, business, cost_owner, reviewed=False)
    result = guidance(session, business, "contribution", billed.id)
    assert result["reason_code"] == "inventory_scope_not_reviewed"
    assert states(result) == [
        ("receipt_cost_evidence", "done"),
        ("inventory_review", "open"),
        ("contribution_review", "blocked"),
        ("owner_confirmation", "blocked"),
    ]


def test_reviewed_stock_opens_the_contribution_review(session, business, cost_owner):
    billed, *_ = revenue.prepared(session, business, cost_owner)
    result = guidance(session, business, "contribution", billed.id)
    assert result["reason_code"] == "commercial_match_not_reviewed"
    assert first_open(result)["code"] == "contribution_review"
    # Selling costs affect DB2 only; they never block the DB1 path.
    assert ("selling_cost_review", "open") in states(result)
    assert states(result).index(("contribution_review", "open")) < states(result).index(
        ("selling_cost_review", "open")
    )


def test_stale_contribution_names_the_stale_inventory_review(
    session, business, cost_owner
):
    _, data, _ = reviewed.prepared(session, business, cost_owner)
    fixtures.receipt(session, business)
    result = guidance(session, business, "contribution", data[0].id)
    assert result["stage"] == "stale"
    assert result["reason_code"] == "inventory_review_stale"
    codes = [step["code"] for step in result["steps"]]
    assert "inventory_review_renew" in codes
    assert codes.index("inventory_review_renew") < codes.index("contribution_review")


def test_source_data_limit_has_no_action_path(session, business, cost_owner):
    billed, *_ = revenue.prepared(session, business, cost_owner)
    billed.billed_document_line_id = None
    session.flush()
    result = guidance(session, business, "contribution", billed.id)
    assert result["reason_code"] == "billed_order_line_missing"
    assert states(result) == [("source_data_limit", "open")]
    assert result["steps"][0]["path"] == "none"


# Boundaries ----------------------------------------------------------------------


def test_guidance_writes_nothing(session, business, cost_owner):
    billed, *_ = revenue.prepared(session, business, cost_owner, reviewed=False)
    fixtures.receipt(session, business)
    session.flush()
    events = session.scalar(
        select(func.count())
        .select_from(BusinessEvent)
        .where(BusinessEvent.tenant_id == business.tenant.id)
    )
    proposals = session.scalar(select(func.count()).select_from(ChangeProposal))
    guidance(session, business, "inventory", business.item.id)
    guidance(session, business, "contribution", billed.id)
    assert not session.new and not session.dirty
    assert (
        session.scalar(
            select(func.count())
            .select_from(BusinessEvent)
            .where(BusinessEvent.tenant_id == business.tenant.id)
        )
        == events
    )
    assert session.scalar(select(func.count()).select_from(ChangeProposal)) == proposals


def test_cross_company_scope_is_not_found(session, business):
    other = core.create_tenant(session, "Neighbor")
    with pytest.raises(core.NotFound):
        cost_query(session, other.id, kind="inventory", scope_id=business.item.id)


def test_other_company_proposal_is_ignored(session, business, cost_owner):
    args, _, _ = stock.prepared(session, business, cost_owner)
    other = core.create_tenant(session, "Neighbor")
    session.add(
        ChangeProposal(
            id=core.uid("act"),
            tenant_id=other.id,
            type="tool:cost.change",
            status="proposed",
            input=json.dumps(args, sort_keys=True),
            output="{}",
        )
    )
    session.flush()
    foreign = guidance(session, business, "inventory", business.item.id)
    assert ("owner_confirmation", "blocked") in states(foreign)
    assert all("proposal_id" not in step for step in foreign["steps"])
    # Positive control: the company's own proposal is linked.
    own = propose(session, business, cost_owner, args)
    linked = guidance(session, business, "inventory", business.item.id)
    assert first_open(linked)["proposal_id"] == own.id


def test_business_company_is_writable_and_mcp_returns_the_same_steps(
    session, business, cost_owner
):
    stock.prepared(session, business, cost_owner)
    args = {"kind": "inventory", "scope_id": business.item.id}
    direct = cost_query(session, business.tenant.id, **args)
    assert direct["guidance"]["writable"] is True
    mcp = MCP_TOOL_REGISTRY["cost_query_get"].handler(session, business.tenant.id, args)
    assert mcp["guidance"]["steps"] == direct["guidance"]["steps"]
    # The fields MCP clients already read keep their meaning.
    assert direct["guidance"]["next_action"]["tool"] == "cost_change_propose"
    assert direct["guidance"]["stage"] == "uninitialized"


def test_historical_reads_carry_no_steps(session, business, cost_owner):
    args, _, _ = stock.prepared(session, business, cost_owner)
    _, review = stock.commit_review(session, business, cost_owner, args)
    historical = cost_query(
        session,
        business.tenant.id,
        kind="inventory",
        scope_id=business.item.id,
        review_id=review["review_id"],
    )
    assert historical["guidance"]["steps"] == []


def test_practice_company_without_run_is_not_writable(session):
    from reality.db.core import Item, Tenant

    sandbox = Tenant(id=core.uid("ten"), name="Practice", purpose="playground")
    session.add(sandbox)
    session.flush()
    item = Item(id=core.uid("itm"), tenant_id=sandbox.id, sku="P-1", name="P")
    session.add(item)
    session.flush()
    result = cost_query(session, sandbox.id, kind="inventory", scope_id=item.id)
    assert result["guidance"]["writable"] is False
    # The steps stay visible: people still learn what would resolve the gap.
    assert result["guidance"]["steps"]
