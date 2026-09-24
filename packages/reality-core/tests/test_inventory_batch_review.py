"""Joint confirmation retains one real action/event basis without new authority."""

import copy
import json
from datetime import datetime, timedelta
from types import SimpleNamespace

import pytest
import test_inventory_costing_services as fixtures
from conftest import record_by_id
from pydantic import ValidationError
from sqlalchemy import func, select

from reality.db.core import BusinessEvent, ChangeProposal, TenantMembership
from reality.db.inventory_costing import CostInventoryReview, CostPolicyRevision
from reality.domain.costing import CHANGE
from reality.mcp.catalog import MCP_TOOL_REGISTRY
from reality.services import core, costing
from reality.services.analytics.reports import caller
from reality.services.memberships import Principal
from reality.tools.application import (
    approve_and_execute_proposal,
    create_change_proposal,
)

cost_owner = fixtures.cost_owner


def prepared(session, business, owner):
    first, _, _ = fixtures.prepared(session, business, owner)
    second_business = SimpleNamespace(**vars(business))
    second_business.item = core.create_item(
        session, business.tenant.id, "SECOND", "Second", unit="kg"
    )
    second, _, _ = fixtures.prepared(session, second_business, owner)
    cutoff = core.now().isoformat()
    scopes = []
    for request in (first, second):
        scopes.append(
            {
                key: value
                for key, value in request.items()
                if key not in {"operation", "reason", "expected_event_sequence"}
            }
        )
        scopes[-1]["effective_at"] = cutoff
    return {
        "operation": "inventory_batch_review",
        "expected_event_sequence": second["expected_event_sequence"],
        "reason": "Confirm exact whole-item scopes together",
        "scopes": scopes,
    }


def counts(session, tenant):
    return tuple(
        session.scalar(
            select(func.count()).select_from(model).where(model.tenant_id == tenant)
        )
        for model in (CostInventoryReview, CostPolicyRevision, BusinessEvent)
    )


def propose(session, tenant, owner, args):
    with caller(Principal(owner.id)):
        return create_change_proposal(session, tenant, "cost.change", args)


def test_batch_mcp_confirmation_shared_basis_replay_and_snapshots(
    session, business, cost_owner
):
    tenant = business.tenant.id
    args = prepared(session, business, cost_owner)
    command = MCP_TOOL_REGISTRY["cost_change_propose"]
    branch = next(
        branch
        for branch in command.input_schema["oneOf"]
        if branch["properties"]["operation"]["const"]
        == "inventory_batch_review"
    )
    assert branch["properties"]["scopes"]["maxItems"] == 10
    before = counts(session, tenant)
    with caller(Principal(cost_owner.id)):
        proposed = command.handler(session, tenant, args)
    assert proposed["requires_human_confirmation"]
    assert counts(session, tenant) == before
    with pytest.raises(core.InvalidOperation, match="confirmation"):
        approve_and_execute_proposal(
            session,
            tenant,
            proposed["proposal_id"],
            confirming_principal=Principal(cost_owner.id),
        )
    action = approve_and_execute_proposal(
        session,
        tenant,
        proposed["proposal_id"],
        confirming_principal=Principal(cost_owner.id),
        confirmed=True,
    )
    result = json.loads(action.output)
    assert result["action_id"] == action.id
    assert len(result["reviews"]) == 2
    assert counts(session, tenant) == (before[0] + 2, before[1] + 2, before[2] + 1)
    reviews = list(
        session.scalars(
            select(CostInventoryReview).where(CostInventoryReview.tenant_id == tenant)
        )
    )
    assert {r.action_id for r in reviews} == {action.id}
    assert len({r.introduced_event_id for r in reviews}) == 1
    assert len({r.target_event_sequence for r in reviews}) == 1
    assert len({r.knowledge_at for r in reviews}) == 1
    assert len({r.effective_at for r in reviews}) == 1
    repeated = approve_and_execute_proposal(
        session,
        tenant,
        action.id,
        confirming_principal=Principal(cost_owner.id),
        confirmed=True,
    )
    assert repeated.output == action.output
    assert counts(session, tenant) == (before[0] + 2, before[1] + 2, before[2] + 1)
    generations = [
        costing.build_inventory_generation(session, tenant, r.id)["generation_id"]
        for r in reviews
    ]
    rows = costing.inventory_cost_snapshots(session, tenant, generations)["rows"]
    assert {r["context"]["review_action_id"] for r in rows} == {action.id}
    assert {datetime.fromisoformat(r["context"]["knowledge_at"]) for r in rows} == {
        datetime.fromisoformat(result["knowledge_at"])
    }
    assert {r["result"]["acquisition_value"] for r in rows} == {"420.0000"}
    assert len({r["context"]["policy_revision_id"] for r in rows}) == 2
    assert {r["context"]["base_unit"] for r in rows} == {"pcs", "kg"}


def test_batch_stale_preview_and_owner_revocation_refuse(session, business, cost_owner):
    tenant = business.tenant.id
    args = prepared(session, business, cost_owner)
    action = propose(session, tenant, cost_owner, args)
    core.record_movement(
        session,
        tenant,
        "receipt",
        business.item.id,
        "1",
        to_location_id=business.location.id,
    )
    before = counts(session, tenant)
    with pytest.raises(core.Conflict, match="stale"):
        costing.execute_cost_change(
            session,
            tenant,
            arguments=args,
            action_id=action.id,
            actor_id=cost_owner.id,
            confirmed=True,
        )
    assert counts(session, tenant) == before
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
    assert counts(session, tenant) == before


def test_batch_second_execution_failure_rolls_back_all_members(
    session, business, cost_owner, monkeypatch
):
    import reality.services.inventory_costing as service

    tenant = business.tenant.id
    args = prepared(session, business, cost_owner)
    action = propose(session, tenant, cost_owner, args)
    before = counts(session, tenant)
    execute = service._execute
    called = []

    def fail_second(*args, **kwargs):
        called.append(1)
        if len(called) == 2:
            raise core.InvalidOperation("Injected second member failure")
        return execute(*args, **kwargs)

    monkeypatch.setattr(service, "_execute", fail_second)
    with pytest.raises(core.InvalidOperation, match="Injected"):
        costing.execute_cost_change(
            session,
            tenant,
            arguments=args,
            action_id=action.id,
            actor_id=cost_owner.id,
            confirmed=True,
        )
    assert len(called) == 2
    assert counts(session, tenant) == before
    assert record_by_id(session, ChangeProposal, action.id).status == "proposed"


def test_batch_foreign_or_absent_member_refuses_without_writes(
    session, business, cost_owner
):
    tenant = business.tenant.id
    args = prepared(session, business, cost_owner)
    foreign = core.create_tenant(session, "Foreign")
    foreign_item = core.create_item(session, foreign.id, "FOREIGN", "Foreign")
    before = counts(session, tenant)
    for item in (foreign_item.id, "absent"):
        invalid = copy.deepcopy(args)
        invalid["scopes"][1]["item_id"] = item
        with pytest.raises(core.NotFound):
            costing.preview_cost_change(
                session, tenant, invalid, principal=Principal(cost_owner.id)
            )
        assert counts(session, tenant) == before


def test_batch_total_movement_budget_refuses_before_writes(
    session, business, cost_owner
):
    tenant = business.tenant.id
    args = prepared(session, business, cost_owner)
    # Each individual item remains below 100; the common request exceeds 100.
    for scope in args["scopes"]:
        for _ in range(49):
            core.record_movement(
                session,
                tenant,
                "transfer",
                scope["item_id"],
                "1",
                from_location_id=business.location.id,
                to_location_id=business.location.id,
            )
    cutoff = core.now().isoformat()
    for scope in args["scopes"]:
        scope["effective_at"] = cutoff
    args["expected_event_sequence"] = costing._sequence(session, tenant)
    before = counts(session, tenant)
    with pytest.raises(core.InvalidOperation, match="bound"):
        costing.preview_cost_change(
            session, tenant, args, principal=Principal(cost_owner.id)
        )
    assert counts(session, tenant) == before


@pytest.mark.parametrize(
    "mutation",
    ["duplicate", "cutoff", "currency", "owner", "one", "eleven", "receipts"],
)
def test_batch_domain_refuses_incompatible_scope(mutation):
    instant = core.now()
    scope = {
        "item_id": "first",
        "owner_party_id": "owner",
        "method": "fifo",
        "currency": "EUR",
        "base_unit": "pcs",
        "history_start": instant.isoformat(),
        "effective_at": instant.isoformat(),
        "history_complete_from_zero": True,
        "receipt_cost_scopes_confirmed": True,
        "economic_issue_ids": [],
        "receipts": [
            {
                "movement_id": "receipt",
                "manifest_id": "manifest",
                "ownership_source_record_id": "source",
            }
        ],
    }
    second = {**scope, "item_id": "second"}
    scopes = [scope, second]
    if mutation == "duplicate":
        second["item_id"] = "first"
    if mutation == "cutoff":
        second["effective_at"] = (instant + timedelta(seconds=1)).isoformat()
    if mutation == "currency":
        second["currency"] = "USD"
    if mutation == "owner":
        second["owner_party_id"] = "other"
    if mutation == "one":
        scopes = [scope]
    if mutation == "eleven":
        scopes = [{**scope, "item_id": str(i)} for i in range(11)]
    if mutation == "receipts":
        scope["receipts"] = [
            {**scope["receipts"][0], "movement_id": f"receipt-{index}"}
            for index in range(20)
        ]
    with pytest.raises(ValidationError):
        CHANGE.validate_python(
            {
                "operation": "inventory_batch_review",
                "expected_event_sequence": 0,
                "reason": "Confirm",
                "scopes": scopes,
            }
        )
