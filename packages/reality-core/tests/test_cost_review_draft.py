"""Cost reviews are drafted from held records (spec 282)."""

import pytest
import test_contribution_services as revenue
import test_costing_services as fixtures
import test_inventory_costing_services as stock
from sqlalchemy import func, select

from reality.db.core import BusinessEvent, ChangeProposal, SourceRecord
from reality.domain.cost_review_draft import method_choices
from reality.services import core
from reality.services.cost_review_draft import cost_review_draft
from reality.services.costing import preview_cost_change

cost_owner = fixtures.cost_owner


def codes(draft):
    return [entry["code"] for entry in draft["open_inputs"]]


# Foundation ----------------------------------------------------------------------


def test_method_choices_follow_tracking_type():
    assert method_choices("none") == ["fifo"]
    assert method_choices("lot") == ["fifo", "specific"]
    assert method_choices("serial") == ["fifo", "specific"]


def test_draft_shape_for_both_kinds(session, business, cost_owner):
    billed, *_ = revenue.prepared(session, business, cost_owner)
    for kind, scope in (("contribution", billed.id), ("inventory", business.item.id)):
        draft = cost_review_draft(
            session, business.tenant.id, kind=kind, scope_id=scope
        )
        assert draft["kind"] == kind and draft["scope_id"] == scope
        assert isinstance(draft["event_sequence"], int)
        assert set(draft) >= {"arguments", "open_inputs", "basis"}


def test_draft_writes_nothing(session, business, cost_owner):
    billed, *_ = revenue.prepared(session, business, cost_owner)
    fixtures.receipt(session, business)
    session.flush()

    def counts():
        return (
            session.scalar(select(func.count()).select_from(BusinessEvent)),
            session.scalar(select(func.count()).select_from(ChangeProposal)),
            session.scalar(select(func.count()).select_from(SourceRecord)),
        )

    before = counts()
    cost_review_draft(
        session, business.tenant.id, kind="contribution", scope_id=billed.id
    )
    cost_review_draft(
        session, business.tenant.id, kind="inventory", scope_id=business.item.id
    )
    assert not session.new and not session.dirty
    assert counts() == before


# US1 contribution ------------------------------------------------------------------


def test_contribution_draft_equals_preview_values(session, business, cost_owner):
    from reality.services.costing import contribution_preview

    billed, *_ = revenue.prepared(session, business, cost_owner)
    preview = contribution_preview(session, business.tenant.id, billed.id)
    draft = cost_review_draft(
        session, business.tenant.id, kind="contribution", scope_id=billed.id
    )
    assert draft["open_inputs"] == []
    arguments = draft["arguments"]
    assert arguments["operation"] == "contribution_review"
    assert arguments["document_line_id"] == billed.id
    assert arguments["expected_candidate_hash"] == preview["candidate_hash"]
    assert arguments["expected_event_sequence"] == preview["event_sequence"]
    assert arguments["economic_at"] == preview["trace"]["proposed_economic_at"]
    assert arguments["profile"] == "commercial_v1"
    assert "selling_categories" not in arguments
    assert {"kind": "document_line", "id": billed.id} in [
        {"kind": row["kind"], "id": row["id"]} for row in draft["basis"]
    ]


def test_complete_contribution_arguments_pass_preview_cost_change(
    session, business, cost_owner
):
    billed, *_ = revenue.prepared(session, business, cost_owner)
    draft = cost_review_draft(
        session, business.tenant.id, kind="contribution", scope_id=billed.id
    )
    review = preview_cost_change(session, business.tenant.id, draft["arguments"])
    assert review["requires_confirmation"] is True


def test_open_input_upstream_not_ready(session, business, cost_owner):
    billed, *_ = revenue.prepared(session, business, cost_owner, reviewed=False)
    draft = cost_review_draft(
        session, business.tenant.id, kind="contribution", scope_id=billed.id
    )
    assert draft["arguments"] is None
    assert codes(draft) == ["upstream_not_ready"]
    assert draft["open_inputs"][0]["reason"] == "inventory_scope_not_reviewed"


def test_preview_conflict_falls_back_to_upstream_not_ready(
    session, business, cost_owner, monkeypatch
):
    from reality.services import costing

    billed, *_ = revenue.prepared(session, business, cost_owner)

    def moved(*args, **kwargs):
        raise core.Conflict(
            "Contribution inputs changed during preview; retry the read."
        )

    monkeypatch.setattr(costing, "contribution_preview", moved)
    draft = cost_review_draft(
        session, business.tenant.id, kind="contribution", scope_id=billed.id
    )
    assert draft["arguments"] is None and codes(draft) == ["upstream_not_ready"]


def test_cross_company_scope_is_not_found(session, business, cost_owner):
    billed, *_ = revenue.prepared(session, business, cost_owner)
    other = core.create_tenant(session, "Neighbor")
    with pytest.raises(core.NotFound):
        cost_review_draft(session, other.id, kind="contribution", scope_id=billed.id)
    with pytest.raises(core.NotFound):
        cost_review_draft(
            session, other.id, kind="inventory", scope_id=business.item.id
        )
    # Positive control: the own company drafts the same scope.
    assert cost_review_draft(
        session, business.tenant.id, kind="contribution", scope_id=billed.id
    )["arguments"]


def test_unknown_kind_is_refused(session, business):
    with pytest.raises(core.InvalidOperation):
        cost_review_draft(session, business.tenant.id, kind="payment", scope_id="x")


# US2 inventory ---------------------------------------------------------------------


def inventory(session, business, **answers):
    return cost_review_draft(
        session,
        business.tenant.id,
        kind="inventory",
        scope_id=business.item.id,
        answers=answers or None,
    )


def test_the_method_is_always_asked_with_fifo_preselected(
    session, business, cost_owner
):
    stock.prepared(session, business, cost_owner)
    draft = inventory(session, business)
    assert draft["arguments"] is None
    assert draft["open_inputs"] == [
        {"code": "valuation_method", "choices": ["fifo"], "default": "fifo"}
    ]
    assert draft["partial_arguments"]["owner_party_id"] == business.company.id


def test_inventory_draft_passes_inventory_check(session, business, cost_owner):
    expected, receipt, issue = stock.prepared(session, business, cost_owner)
    draft = inventory(session, business, method="fifo")
    assert draft["open_inputs"] == []
    arguments = draft["arguments"]
    for field in (
        "operation",
        "item_id",
        "owner_party_id",
        "method",
        "currency",
        "base_unit",
        "economic_issue_ids",
        "history_complete_from_zero",
        "receipt_cost_scopes_confirmed",
    ):
        assert arguments[field] == expected[field], field
    assert [row["movement_id"] for row in arguments["receipts"]] == [receipt.id]
    assert arguments["economic_issue_ids"] == [issue.id]
    assert (
        arguments["receipts"][0]["manifest_id"]
        == expected["receipts"][0]["manifest_id"]
    )
    # The strongest proof: the existing check and confirmed execution accept it.
    preview_cost_change(session, business.tenant.id, arguments)
    _, review = stock.commit_review(session, business, cost_owner, arguments)
    assert review["acquisition_value"] is not None


def test_open_input_company_party_missing(session, business, cost_owner):
    from reality.db.core import PartyRole

    stock.prepared(session, business, cost_owner)
    # Positive control: with the company party the draft names no owner question.
    assert "company_party_missing" not in codes(inventory(session, business))
    for role in session.scalars(
        select(PartyRole).where(
            PartyRole.tenant_id == business.tenant.id, PartyRole.role == "company"
        )
    ):
        session.delete(role)
    business.company.type = "supplier"
    session.flush()
    assert "company_party_missing" in codes(inventory(session, business, method="fifo"))


def test_open_input_receipt_cost_incomplete(session, business, cost_owner):
    receipt = fixtures.receipt(session, business)
    draft = inventory(session, business, method="fifo")
    incomplete = [
        e for e in draft["open_inputs"] if e["code"] == "receipt_cost_incomplete"
    ]
    assert incomplete == [
        {
            "code": "receipt_cost_incomplete",
            "subject": {"kind": "movement", "id": receipt.id},
            "reason": "not_admitted",
        }
    ]
    assert draft["arguments"] is None


def test_open_input_return_portion_undetermined(session, business, cost_owner):
    stock.prepared(session, business, cost_owner)
    assert "return_portion_undetermined" not in codes(inventory(session, business))
    returned = core.record_movement(
        session,
        business.tenant.id,
        "return",
        business.item.id,
        "2",
        to_location_id=business.location.id,
    )
    entry = [
        e
        for e in inventory(session, business, method="fifo")["open_inputs"]
        if e["code"] == "return_portion_undetermined"
    ]
    assert entry == [
        {
            "code": "return_portion_undetermined",
            "subject": {"kind": "movement", "id": returned.id},
        }
    ]


def test_bounds_report_instead_of_truncate(session, business, cost_owner, monkeypatch):
    from reality.services import cost_review_draft as drafting

    monkeypatch.setattr(drafting, "MAX_RECEIPTS", 2)
    for _ in range(3):
        fixtures.receipt(session, business)
    draft = inventory(session, business, method="fifo")
    assert codes(draft) == ["review_bound_exceeded"]
    assert draft["arguments"] is None and draft["partial_arguments"] is None


# US4 chat and MCP --------------------------------------------------------------------


def test_mcp_and_chat_offer_the_same_draft(session, business, cost_owner):
    from reality.mcp.catalog import MCP_TOOL_REGISTRY, model_tool_schemas

    billed, *_ = revenue.prepared(session, business, cost_owner)
    arguments = {"kind": "contribution", "scope_id": billed.id}
    direct = cost_review_draft(session, business.tenant.id, **arguments)
    assert (
        MCP_TOOL_REGISTRY["cost_review_draft"].handler(
            session, business.tenant.id, arguments
        )
        == direct
    )
    # Read-only chats (practice companies) get it too; it writes nothing.
    names = {tool["function"]["name"] for tool in model_tool_schemas(access=("read",))}
    assert "cost_review_draft" in names
    with pytest.raises(core.InvalidOperation):
        MCP_TOOL_REGISTRY["cost_review_draft"].handler(
            session, business.tenant.id, {**arguments, "answers": {"price": "1"}}
        )


def test_agent_guidance_names_the_draft_first():
    import yaml

    from reality.config import config_text

    guidance = yaml.safe_load(config_text("command_catalog.yaml"))[
        "capability_guidance"
    ]
    assert "cost_review_draft first" in guidance["cost_change_propose"]["purpose"]
    draft_block = guidance["cost_review_draft"]
    assert (
        draft_block["confirmation"] == "none" and draft_block["side_effects"] == "none"
    )
