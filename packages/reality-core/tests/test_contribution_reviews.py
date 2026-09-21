"""Confirmed whole-line DB1 retains its source and inventory basis."""

import json

import pytest
import test_contribution_services as fixtures
import test_costing_services as costs
import test_inventory_costing_services as stock
from conftest import record_by_id
from sqlalchemy import func, select

from reality.db.contribution import CostContributionReview, CostRevenueMatchBasis
from reality.db.core import ChangeProposal, TenantMembership
from reality.mcp.catalog import MCP_TOOL_REGISTRY
from reality.services import core
from reality.services.analytics.reports import caller
from reality.services.costing import (
    contribution_preview,
    execute_cost_change,
    preview_cost_change,
    reviewed_contribution,
)
from reality.services.memberships import Principal
from reality.tools.application import (
    approve_and_execute_proposal,
    create_change_proposal,
    run_read_tool,
)

cost_owner = costs.cost_owner


def prepared(session, business, owner):
    data = fixtures.prepared(session, business, owner)
    preview = contribution_preview(session, business.tenant.id, data[0].id)
    args = {
        "operation": "contribution_review",
        "document_line_id": data[0].id,
        "expected_event_sequence": preview["event_sequence"],
        "expected_candidate_hash": preview["candidate_hash"],
        "profile": "commercial_v1",
        "profile_confirmed": True,
        "revenue_complete": True,
        "economic_at": preview["trace"]["proposed_economic_at"],
        "reason": "Whole invoice and shipment scope, revenue completeness and commercial profile confirmed",
    }
    return args, data


def test_confirmed_db1_replay_and_tool_parity(session, business, cost_owner):
    args, data = prepared(session, business, cost_owner)
    assert reviewed_contribution(session, business.tenant.id, data[0].id)["db1"] is None
    action, result = stock.commit_review(session, business, cost_owner, args)
    assert result["db1"] == "570.0000" and result["db1_rate"] == "47.5000"
    assert result["db2"] is result["db2_rate"] is None
    assert result["missing_basis"] == ["selling_costs_unknown"]
    assert result["review_state"] == "reviewed_complete_at_cutoff"
    assert result["action_id"] == action.id
    session.commit()
    read_args = {"document_line_id": data[0].id}
    assert (
        run_read_tool(session, business.tenant.id, "cost.contribution.get", read_args)
        == result
    )
    assert (
        MCP_TOOL_REGISTRY["cost_contribution_get"].handler(
            session, business.tenant.id, read_args
        )
        == result
    )
    again = approve_and_execute_proposal(
        session,
        business.tenant.id,
        action.id,
        confirming_principal=Principal(cost_owner.id),
        confirmed=True,
    )
    assert json.loads(again.output) == result
    assert session.scalar(select(func.count()).select_from(CostContributionReview)) == 1


def test_later_events_preserve_frozen_db1(session, business, cost_owner):
    args, data = prepared(session, business, cost_owner)
    _, result = stock.commit_review(session, business, cost_owner, args)
    core.correct_movement(
        session, business.tenant.id, data[4].id, reason="Delivery correction"
    )
    current = reviewed_contribution(session, business.tenant.id, data[0].id)
    assert current["db1"] is current["db1_rate"] is None
    assert current["basis_db1"] == "570.0000"
    assert current["review_state"] == "stale"
    past = reviewed_contribution(
        session, business.tenant.id, data[0].id, review_id=result["review_id"]
    )
    assert past["db1"] == "570.0000"
    assert past["economic_at"] == args["economic_at"]


def test_review_owner_confirmation_binding_and_rollback(
    session, business, cost_owner, monkeypatch
):
    args, _data = prepared(session, business, cost_owner)
    with caller(Principal(cost_owner.id)):
        action = create_change_proposal(
            session, business.tenant.id, "cost.change", args
        )
    with pytest.raises(core.InvalidOperation, match="confirmation"):
        execute_cost_change(
            session,
            business.tenant.id,
            arguments=args,
            action_id=action.id,
            actor_id=cost_owner.id,
        )
    with pytest.raises(core.InvalidOperation, match="bound"):
        execute_cost_change(
            session,
            business.tenant.id,
            arguments=args | {"reason": "different"},
            action_id=action.id,
            actor_id=cost_owner.id,
            confirmed=True,
        )
    from reality.services import contribution_reviews

    original = contribution_reviews._new

    def fail(db, model, tenant, **values):
        if model is CostContributionReview:
            raise RuntimeError("Injected review failure")
        return original(db, model, tenant, **values)

    monkeypatch.setattr(contribution_reviews, "_new", fail)
    with pytest.raises(RuntimeError, match="Injected"):
        execute_cost_change(
            session,
            business.tenant.id,
            arguments=args,
            action_id=action.id,
            actor_id=cost_owner.id,
            confirmed=True,
        )
    assert session.scalar(select(func.count()).select_from(CostRevenueMatchBasis)) == 0
    assert record_by_id(session, ChangeProposal, action.id).status == "proposed"
    monkeypatch.setattr(contribution_reviews, "_new", original)
    membership = session.scalar(
        select(TenantMembership).where(TenantMembership.user_id == cost_owner.id)
    )
    membership.role = "member"
    session.flush()
    with pytest.raises(core.InvalidOperation, match="owner"):
        execute_cost_change(
            session,
            business.tenant.id,
            arguments=args,
            action_id=action.id,
            actor_id=cost_owner.id,
            confirmed=True,
        )


def test_review_foreign_scope_is_unavailable(session, business, cost_owner):
    args, data = prepared(session, business, cost_owner)
    _, result = stock.commit_review(session, business, cost_owner, args)
    other = core.create_tenant(session, "Other")
    for read in [
        lambda: reviewed_contribution(
            session, other.id, data[0].id, review_id=result["review_id"]
        ),
        lambda: run_read_tool(
            session, other.id, "cost.contribution.get", {"document_line_id": data[0].id}
        ),
        lambda: MCP_TOOL_REGISTRY["cost_contribution_get"].handler(
            session, other.id, {"document_line_id": data[0].id}
        ),
    ]:
        with pytest.raises(core.NotFound):
            read()


@pytest.mark.parametrize(
    "field,value",
    [("expected_candidate_hash", "0" * 64), ("economic_at", "2020-01-01T00:00:00Z")],
)
def test_review_changed_candidate_refuses(session, business, cost_owner, field, value):
    args, _ = prepared(session, business, cost_owner)
    with pytest.raises((core.Conflict, core.InvalidOperation)):
        preview_cost_change(
            session,
            business.tenant.id,
            args | {field: value},
            principal=Principal(cost_owner.id),
        )


def test_admitted_invoice_and_order_protected(session, business, cost_owner):
    args, data = prepared(session, business, cost_owner)
    stock.commit_review(session, business, cost_owner, args)
    from reality.db.core import Document

    for doc in (data[2], record_by_id(session, Document, data[1].document_id)):
        with pytest.raises(core.InvalidOperation, match="contribution"):
            core.correct_manual_document(
                session,
                business.tenant.id,
                doc.id,
                document_type=doc.type,
                number=doc.number,
                party_id=doc.party_id,
                amount=doc.gross_amount,
                currency=doc.currency,
                document_date="2026-01-01",
            )


def test_review_hash_corruption_refuses(session, business, cost_owner):
    args, data = prepared(session, business, cost_owner)
    _, result = stock.commit_review(session, business, cost_owner, args)
    basis = session.scalar(select(CostRevenueMatchBasis))
    basis.stated_net += 1
    session.flush()
    with pytest.raises(core.InvalidOperation, match="integrity"):
        reviewed_contribution(
            session, business.tenant.id, data[0].id, review_id=result["review_id"]
        )


def test_late_cost_reaffirmation_preserves_old_db1(session, business, cost_owner):
    from reality.db.core import Movement
    from reality.services.costing import receipt_cost

    args, data = prepared(session, business, cost_owner)
    _, first = stock.commit_review(session, business, cost_owner, args)
    prior_inventory = data[5]
    source = prior_inventory["receipt_sources"][0]
    movement = record_by_id(session, Movement, source["movement_id"])
    extra = costs.evidence(session, business, "50", "0")
    costs.execute(
        session,
        business,
        cost_owner,
        costs.assignment(session, business, movement, extra, "50", "inbound_freight"),
    )
    reviewed_receipt = costs.review(
        session,
        business,
        cost_owner,
        movement,
        {"goods", "inbound_freight", "purchase_reduction"},
    )
    inventory_args = {
        "operation": "inventory_review",
        "expected_event_sequence": receipt_cost(
            session, business.tenant.id, movement.id
        )["event_sequence"],
        "item_id": business.item.id,
        "owner_party_id": business.company.id,
        "method": "fifo",
        "currency": "EUR",
        "base_unit": business.item.unit,
        "history_start": prior_inventory["history_start"],
        "effective_at": core.now().isoformat(),
        "history_complete_from_zero": True,
        "receipt_cost_scopes_confirmed": True,
        "economic_issue_ids": [data[4].id],
        "receipts": [
            {
                "movement_id": movement.id,
                "manifest_id": reviewed_receipt["manifest_id"],
                "ownership_source_record_id": source["ownership_source_record_id"],
            }
        ],
        "reason": "Reaffirm inventory after received late freight",
    }
    stock.commit_review(session, business, cost_owner, inventory_args)
    preview = contribution_preview(session, business.tenant.id, data[0].id)
    renewed = args | {
        "expected_event_sequence": preview["event_sequence"],
        "expected_candidate_hash": preview["candidate_hash"],
    }
    _, second = stock.commit_review(session, business, cost_owner, renewed)
    assert second["db1"] == "540.0000" and second["revision"] == 2
    assert (
        reviewed_contribution(
            session, business.tenant.id, data[0].id, review_id=first["review_id"]
        )["db1"]
        == "570.0000"
    )
    assert session.scalar(select(func.count()).select_from(CostRevenueMatchBasis)) == 1


def test_binding_database_constraints_prevent_quantity_reuse(
    session, business, cost_owner
):
    from sqlalchemy.exc import IntegrityError

    args, data = prepared(session, business, cost_owner)
    stock.commit_review(session, business, cost_owner, args)
    basis = session.scalar(select(CostRevenueMatchBasis))
    values = {c.name: getattr(basis, c.name) for c in basis.__table__.columns}
    other = core.create_tenant(session, "Foreign binding")
    for override in (
        {"tenant_id": other.id},
        {"document_line_id": data[1].id},
        {"movement_basis_id": "foreign-or-missing"},
    ):
        with pytest.raises(IntegrityError), session.begin_nested():
            session.add(
                CostRevenueMatchBasis(**(values | override | {"id": core.uid("bad")}))
            )
            session.flush()


def test_frozen_read_neither_writes_nor_scans_live_movements(
    session, business, cost_owner
):
    from sqlalchemy import event

    from reality.db.core import Item

    args, data = prepared(session, business, cost_owner)
    _, first = stock.commit_review(session, business, cost_owner, args)
    statements = []

    def observe(conn, cursor, statement, parameters, context, executemany):
        statements.append(statement.lower())

    pending = Item(
        id="pending-db1",
        tenant_id=business.tenant.id,
        sku="pending-db1",
        name="Pending",
        unit="pcs",
    )
    session.add(pending)
    connection = session.connection()
    event.listen(connection, "before_cursor_execute", observe)
    try:
        result = reviewed_contribution(
            session, business.tenant.id, data[0].id, review_id=first["review_id"]
        )
    finally:
        event.remove(connection, "before_cursor_execute", observe)
    assert result["db1"] == "570.0000" and pending in session.new
    assert not any(
        s.lstrip().startswith(("insert", "update", "delete")) for s in statements
    )
    movement_reads = [
        s for s in statements if "from movement " in s or "from movement\n" in s
    ]
    assert all(
        "movement.id =" in s and "movement.item_id =" not in s for s in movement_reads
    )


def test_contribution_review_stale_input_and_cross_line_history(
    session, business, cost_owner
):
    args, data = prepared(session, business, cost_owner)
    _, first = stock.commit_review(session, business, cost_owner, args)
    with pytest.raises(core.Conflict, match="stale"):
        preview_cost_change(
            session, business.tenant.id, args, principal=Principal(cost_owner.id)
        )
    with pytest.raises(core.NotFound):
        reviewed_contribution(
            session, business.tenant.id, data[1].id, review_id=first["review_id"]
        )


def test_current_review_refuses_old_snapshot_but_history_is_explicit(
    session, business, cost_owner, monkeypatch
):
    args, data = prepared(session, business, cost_owner)
    _, result = stock.commit_review(session, business, cost_owner, args)
    monkeypatch.setattr(
        session.connection(), "get_isolation_level", lambda: "REPEATABLE READ"
    )
    with pytest.raises(core.InvalidOperation, match="READ COMMITTED"):
        reviewed_contribution(session, business.tenant.id, data[0].id)
    assert (
        reviewed_contribution(
            session, business.tenant.id, data[0].id, review_id=result["review_id"]
        )["db1"]
        == "570.0000"
    )


@pytest.mark.parametrize("flag", ["revenue_complete", "profile_confirmed"])
def test_review_requires_each_explicit_declaration(session, business, cost_owner, flag):
    args, _ = prepared(session, business, cost_owner)
    with pytest.raises(core.InvalidOperation):
        preview_cost_change(
            session,
            business.tenant.id,
            args | {flag: False},
            principal=Principal(cost_owner.id),
        )
