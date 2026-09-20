"""One owner action confirms exact compatible contribution scopes atomically."""

import copy
import json
from datetime import datetime
from types import SimpleNamespace

import pytest
import test_contribution_services as sales
import test_inventory_costing_services as stock
from pydantic import ValidationError
from sqlalchemy import func, select

from reality.db.contribution import CostContributionReview, CostRevenueMatchBasis
from reality.db.core import BusinessEvent, ChangeProposal, TenantMembership
from reality.domain.costing import CHANGE, SELLING_CATEGORIES
from reality.mcp.catalog import MCP_TOOL_REGISTRY
from reality.services import core, costing
from reality.services.analytics.reports import caller
from reality.services.memberships import Principal
from reality.tools.application import (
    approve_and_execute_proposal,
    create_change_proposal,
)

cost_owner = stock.cost_owner


def prepared(session, business, owner, *, second_unit="kg"):
    data = []
    scopes = []
    for index in range(2):
        current = SimpleNamespace(**vars(business))
        if index:
            current.item = core.create_item(
                session,
                business.tenant.id,
                "SECOND-SALE",
                "Second sale",
                unit=second_unit,
            )
        sale = sales.prepared(session, current, owner)
        data.append(sale)
        action = session.get(ChangeProposal, sale[-1]["action_id"])
        scopes.append(
            {
                key: value
                for key, value in json.loads(action.input).items()
                if key not in {"operation", "reason", "expected_event_sequence"}
            }
        )
    cutoff = core.now().isoformat()
    for scope in scopes:
        scope["effective_at"] = cutoff
    inventory_action, _ = stock.commit_review(
        session,
        business,
        owner,
        {
            "operation": "inventory_batch_review",
            "reason": "Joint inventory basis for contributions",
            "expected_event_sequence": costing._sequence(session, business.tenant.id),
            "scopes": scopes,
        },
    )
    positions = []
    for sale in data:
        candidate = costing.contribution_preview(
            session, business.tenant.id, sale[0].id
        )
        positions.append(
            {
                "document_line_id": sale[0].id,
                "expected_candidate_hash": candidate["candidate_hash"],
                "profile": "commercial_v1",
                "profile_confirmed": True,
                "revenue_complete": True,
                "economic_at": candidate["trace"]["proposed_economic_at"],
            }
        )
    positions[0]["selling_categories"] = [
        {
            "category": category,
            "disposition": "confirmed_zero",
            "reason": "Confirmed no applicable expense in this position",
        }
        for category in SELLING_CATEGORIES
    ]
    return (
        {
            "operation": "contribution_batch_review",
            "reason": "Confirm exact sales together",
            "expected_event_sequence": costing._sequence(session, business.tenant.id),
            "positions": positions,
        },
        data,
        inventory_action.id,
    )


def counts(session, tenant):
    return tuple(
        session.scalar(
            select(func.count()).select_from(model).where(model.tenant_id == tenant)
        )
        for model in (CostRevenueMatchBasis, CostContributionReview, BusinessEvent)
    )


def propose(session, tenant, owner, args):
    with caller(Principal(owner.id)):
        return create_change_proposal(session, tenant, "cost.change", args)


def test_joint_confirmation_mcp_replay_and_historical_members(
    session, business, cost_owner
):
    args, data, inventory_action = prepared(session, business, cost_owner)
    tenant = business.tenant.id
    command = MCP_TOOL_REGISTRY["cost_change_propose"]
    assert (
        "contribution_batch_review"
        in command.input_schema["properties"]["operation"]["enum"]
    )
    assert command.input_schema["properties"]["positions"]["maxItems"] == 10
    before = counts(session, tenant)
    with caller(Principal(cost_owner.id)):
        proposal = command.handler(session, tenant, args)
    assert counts(session, tenant) == before
    with pytest.raises(core.InvalidOperation, match="confirmation"):
        approve_and_execute_proposal(
            session,
            tenant,
            proposal["proposal_id"],
            confirming_principal=Principal(cost_owner.id),
        )
    action = approve_and_execute_proposal(
        session,
        tenant,
        proposal["proposal_id"],
        confirming_principal=Principal(cost_owner.id),
        confirmed=True,
    )
    result = json.loads(action.output)
    assert result["action_id"] == result["profile_scope_action_id"] == action.id
    assert result["inventory_action_id"] == inventory_action
    assert result["currency"] == "EUR"
    assert result["owner_party_id"] == business.company.id
    assert counts(session, tenant) == (before[0] + 2, before[1] + 2, before[2] + 1)
    reviews = list(
        session.scalars(
            select(CostContributionReview).where(
                CostContributionReview.tenant_id == tenant
            )
        )
    )
    assert {r.action_id for r in reviews} == {action.id}
    event = session.get(BusinessEvent, reviews[0].introduced_event_id)
    assert event.event_type == "cost.reviewed"
    assert event.action_id == event.subject_id == action.id
    assert json.loads(event.payload)["operation"] == "contribution_batch_review"
    assert len({r.introduced_event_id for r in reviews}) == 1
    assert {r.event_sequence for r in reviews} == {result["event_sequence"]}
    assert {r.knowledge_at for r in reviews} == {
        datetime.fromisoformat(result["knowledge_at"])
    }
    assert {r["db1"] for r in result["reviews"]} == {"570.0000"}
    by_line = {r["document_line_id"]: r for r in result["reviews"]}
    assert by_line[data[0][0].id]["db2"] == "570.0000"
    assert by_line[data[1][0].id]["db2"] is None
    assert {r["base_unit"] for r in result["reviews"]} == {"pcs", "kg"}
    assert "db1" not in result and "db2" not in result
    for member in result["reviews"]:
        assert member["profile_revision_id"] == member["review_id"]
        assert (
            costing.reviewed_contribution(session, tenant, member["document_line_id"])
            == member
        )
    replay = approve_and_execute_proposal(
        session,
        tenant,
        action.id,
        confirming_principal=Principal(cost_owner.id),
        confirmed=True,
    )
    assert replay.output == action.output
    assert counts(session, tenant) == (before[0] + 2, before[1] + 2, before[2] + 1)
    core.record_movement(
        session,
        tenant,
        "receipt",
        business.item.id,
        "1",
        to_location_id=business.location.id,
    )
    for member in result["reviews"]:
        historical = costing.reviewed_contribution(
            session, tenant, member["document_line_id"], review_id=member["review_id"]
        )
        assert historical == member
        assert (
            costing.reviewed_contribution(session, tenant, member["document_line_id"])[
                "db1"
            ]
            is None
        )


def test_joint_second_failure_rolls_back_every_member(
    session, business, cost_owner, monkeypatch
):
    args, _, _ = prepared(session, business, cost_owner)
    tenant = business.tenant.id
    action = propose(session, tenant, cost_owner, args)
    before = counts(session, tenant)
    from reality.services import contribution_reviews

    original = contribution_reviews._execute
    calls = []

    def fail(*values, **kwargs):
        calls.append(1)
        if len(calls) == 2:
            raise RuntimeError("second contribution failed")
        return original(*values, **kwargs)

    monkeypatch.setattr(contribution_reviews, "_execute", fail)
    with pytest.raises(RuntimeError, match="second contribution"):
        costing.execute_cost_change(
            session,
            tenant,
            arguments=args,
            action_id=action.id,
            actor_id=cost_owner.id,
            confirmed=True,
        )
    assert counts(session, tenant) == before
    assert session.get(ChangeProposal, action.id).status == "proposed"


def test_joint_stale_revoked_and_foreign_refuse(session, business, cost_owner):
    args, _, _ = prepared(session, business, cost_owner)
    tenant = business.tenant.id
    action = propose(session, tenant, cost_owner, args)
    changed_candidate = copy.deepcopy(args)
    changed_candidate["positions"][1]["expected_candidate_hash"] = "0" * 64
    with pytest.raises(core.Conflict, match="candidate changed"):
        costing.preview_cost_change(
            session, tenant, changed_candidate, principal=Principal(cost_owner.id)
        )
    foreign = core.create_tenant(session, "Other company")
    before = counts(session, tenant)
    foreign_party = core.create_party(
        session, foreign.id, "Foreign customer", "company"
    )
    _, foreign_lines = core.create_manual_document_with_lines(
        session,
        foreign.id,
        "sales_invoice",
        "FOREIGN",
        foreign_party.id,
        [{"quantity": "1", "unit": "pcs", "gross_amount": "1"}],
        "1",
    )
    for identity in (foreign_lines[0].id, "missing-line"):
        foreign_args = copy.deepcopy(args)
        foreign_args["positions"][1]["document_line_id"] = identity
        with pytest.raises(core.NotFound):
            costing.preview_cost_change(
                session, tenant, foreign_args, principal=Principal(cost_owner.id)
            )
    with pytest.raises(core.NotFound):
        costing.execute_cost_change(
            session,
            foreign.id,
            arguments=args,
            action_id=action.id,
            actor_id=cost_owner.id,
            confirmed=True,
        )
    with pytest.raises(core.InvalidOperation, match="bound"):
        costing.execute_cost_change(
            session,
            tenant,
            arguments=args | {"reason": "Changed decision"},
            action_id=action.id,
            actor_id=cost_owner.id,
            confirmed=True,
        )
    core.record_movement(
        session,
        tenant,
        "receipt",
        business.item.id,
        "1",
        to_location_id=business.location.id,
    )
    with pytest.raises(core.Conflict, match="stale"):
        costing.execute_cost_change(
            session,
            tenant,
            arguments=args,
            action_id=action.id,
            actor_id=cost_owner.id,
            confirmed=True,
        )
    membership = session.scalar(
        select(TenantMembership).where(
            TenantMembership.tenant_id == tenant,
            TenantMembership.user_id == cost_owner.id,
        )
    )
    membership.role = "member"
    session.flush()
    with pytest.raises(core.InvalidOperation, match="owner"):
        costing.execute_cost_change(
            session,
            tenant,
            arguments=args,
            action_id=action.id,
            actor_id=cost_owner.id,
            confirmed=True,
        )
    assert counts(session, tenant)[:2] == before[:2]


def test_joint_request_bounds_and_duplicate_scope():
    position = {
        "document_line_id": "one",
        "expected_candidate_hash": "a" * 64,
        "profile": "commercial_v1",
        "profile_confirmed": True,
        "revenue_complete": True,
        "economic_at": "2026-09-19T10:00:00Z",
    }
    args = {
        "operation": "contribution_batch_review",
        "expected_event_sequence": 1,
        "reason": "Reviewed together",
        "positions": [position, position | {"document_line_id": "two"}],
    }
    assert len(CHANGE.validate_python(args).positions) == 2
    for positions in (
        [],
        [position],
        [position, position],
        [position | {"document_line_id": str(i)} for i in range(11)],
    ):
        with pytest.raises(ValidationError):
            CHANGE.validate_python(args | {"positions": positions})
    changed = copy.deepcopy(args)
    changed["positions"][1]["revenue_complete"] = False
    with pytest.raises(ValidationError):
        CHANGE.validate_python(changed)


@pytest.mark.parametrize(
    "change",
    [
        "duplicate_shipment",
        "action_id",
        "effective_at",
        "knowledge_at",
        "introduced_event_id",
        "target_event_sequence",
        "owner_party_id",
        "currency",
    ],
)
def test_joint_guard_requires_compatible_inventory_and_disjoint_shipments(
    monkeypatch, change
):
    """Isolate the cross-member guard after each single member has been admitted."""
    from reality.db.inventory_costing import CostInventoryReview, CostPolicyRevision
    from reality.services import contribution_reviews

    position = {
        "document_line_id": "a",
        "expected_candidate_hash": "a" * 64,
        "profile": "commercial_v1",
        "profile_confirmed": True,
        "revenue_complete": True,
        "economic_at": "2026-09-19T10:00:00Z",
    }
    request = CHANGE.validate_python(
        {
            "operation": "contribution_batch_review",
            "expected_event_sequence": 1,
            "reason": "Exact membership",
            "positions": [position, position | {"document_line_id": "b"}],
        }
    )
    instant = datetime.fromisoformat(position["economic_at"])
    inventories = {
        key: SimpleNamespace(
            action_id="inventory-action",
            policy_id=key,
            effective_at=instant,
            knowledge_at=instant,
            introduced_event_id="event",
            target_event_sequence=1,
        )
        for key in ("a", "b")
    }
    policies = {
        key: SimpleNamespace(owner_party_id="owner", currency="EUR")
        for key in ("a", "b")
    }
    if change in ("owner_party_id", "currency"):
        setattr(policies["b"], change, "other")
    elif change != "duplicate_shipment":
        value = (
            instant.replace(hour=11)
            if change.endswith("_at")
            else 2
            if change == "target_event_sequence"
            else "other"
        )
        setattr(inventories["b"], change, value)

    def admitted(session, tenant, member):
        return {
            "basis": {
                "movement_basis_id": "same"
                if change == "duplicate_shipment"
                else member.document_line_id
            },
            "candidate": {"trace": {"inventory_review_id": member.document_line_id}},
        }

    def retained(session, model, tenant, identity):
        assert tenant == "tenant"
        assert model in (CostInventoryReview, CostPolicyRevision)
        return (inventories if model is CostInventoryReview else policies)[identity]

    monkeypatch.setattr(contribution_reviews, "_check", admitted)
    monkeypatch.setattr(contribution_reviews, "_row", retained)
    monkeypatch.setattr(contribution_reviews, "_sequence", lambda *_: 1)
    with pytest.raises(
        core.InvalidOperation, match="shipment binding|compatible confirmed inventory"
    ):
        contribution_reviews._check_batch(None, "tenant", request)
