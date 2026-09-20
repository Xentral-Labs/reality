"""Source-backed selling decisions preserve conservation and independent DB2 coverage."""

import pytest

from reality.domain.costing import SellingAssign


def request(**changes):
    return {
        "operation": "selling_assign",
        "expected_event_sequence": 0,
        "reason": "Received supplier selling expense",
        "document_id": "supplier",
        "expected_evidence_hash": "a" * 64,
        "tax_treatment": "recoverable",
        "selling_expense_confirmed": True,
        "parts": [
            {
                "document_line_id": "sold",
                "category": "payment_fee",
                "source_share": "24",
                "cost_effect": 1,
            }
        ],
        **changes,
    }


def test_selling_request_requires_explicit_scope_and_unique_targets():
    assert SellingAssign.model_validate(request()).parts[0].source_share == 24
    for changes in [
        {"selling_expense_confirmed": False},
        {"tax_treatment": "unknown"},
        {"parts": request()["parts"] * 2},
        {"parts": [request()["parts"][0] | {"source_share": "0"}]},
    ]:
        with pytest.raises(ValueError):
            SellingAssign.model_validate(request(**changes))


import test_contribution_reviews as revenue
import test_costing_services as costs
import test_inventory_costing_services as stock
from sqlalchemy import select

from reality.db.core import Movement
from reality.mcp.catalog import MCP_TOOL_REGISTRY
from reality.services import core
from reality.services.costing import (
    contribution_preview,
    cost_evidence,
    execute_cost_change,
    preview_cost_change,
    reviewed_contribution,
)
from reality.services.memberships import Principal
from reality.tools.application import run_read_tool

cost_owner = costs.cost_owner
CATEGORIES = (
    "outbound_freight",
    "fulfilment",
    "packaging",
    "payment_fee",
    "marketplace_commission",
    "sales_commission",
    "other_selling",
)


def selling(session, business, line, doc, amount="114", **changes):
    ctx = cost_evidence(session, business.tenant.id, doc.id)
    return request(
        document_id=doc.id,
        expected_event_sequence=ctx["event_sequence"],
        expected_evidence_hash=ctx["evidence_hash"],
        parts=[
            {
                "document_line_id": line.id,
                "category": "outbound_freight",
                "source_share": amount,
                "cost_effect": 1,
            }
        ],
        **changes,
    )


def categories(*evidenced):
    return [
        {
            "category": c,
            "disposition": "evidenced" if c in evidenced else "confirmed_zero",
            "reason": "Reviewed evidenced selling scope",
        }
        for c in CATEGORIES
    ]


def refresh(session, business, owner, args, data, decisions):
    prior = data[5]
    source = prior["receipt_sources"][0]
    stock.commit_review(
        session,
        business,
        owner,
        {
            "operation": "inventory_review",
            "expected_event_sequence": cost_evidence_cursor(session, business),
            "item_id": business.item.id,
            "owner_party_id": business.company.id,
            "method": "fifo",
            "currency": "EUR",
            "base_unit": business.item.unit,
            "history_start": prior["history_start"],
            "effective_at": core.now().isoformat(),
            "history_complete_from_zero": True,
            "receipt_cost_scopes_confirmed": True,
            "economic_issue_ids": [data[4].id],
            "receipts": [
                {
                    "movement_id": source["movement_id"],
                    "manifest_id": source["receipt_manifest_id"],
                    "ownership_source_record_id": source["ownership_source_record_id"],
                }
            ],
            "reason": "Refresh bounded inventory after selling input",
        },
    )
    preview = contribution_preview(session, business.tenant.id, data[0].id)
    return args | {
        "expected_event_sequence": preview["event_sequence"],
        "expected_candidate_hash": preview["candidate_hash"],
        "selling_categories": decisions,
    }


def cost_evidence_cursor(session, business):
    from reality.services.costing import _sequence

    return _sequence(session, business.tenant.id)


def test_fixture_a_db2_history_revision_withdrawal_and_tool_parity(
    session, business, cost_owner
):
    args, data = revenue.prepared(session, business, cost_owner)
    doc = costs.evidence(session, business, "114", "0")
    assign = selling(session, business, data[0], doc)
    assign["parts"] = [
        assign["parts"][0] | {"source_share": "90"},
        assign["parts"][0]
        | {
            "source_share": "24",
            "category": "payment_fee",
            "assignment_kind": "allocated",
        },
    ]
    _, assigned = stock.commit_review(session, business, cost_owner, assign)
    reviewed = refresh(
        session,
        business,
        cost_owner,
        args,
        data,
        categories("outbound_freight", "payment_fee"),
    )
    _, first = stock.commit_review(session, business, cost_owner, reviewed)
    assert first["db1"] == "570.0000"
    assert first["db2"] == "456.0000" and first["db2_rate"] == "38.0000"
    assert first["direct_selling_cost"] == "90.0000"
    assert first["allocated_selling_cost"] == "24.0000"
    assert not first["missing_basis"]
    read_args = {"document_line_id": data[0].id, "review_id": first["review_id"]}
    assert (
        run_read_tool(session, business.tenant.id, "cost.contribution.get", read_args)
        == first
    )
    assert (
        MCP_TOOL_REGISTRY["cost_contribution_get"].handler(
            session, business.tenant.id, read_args
        )
        == first
    )
    assert len(first["trace"]["selling"]["parts"]) == 2
    costs.execute(
        session,
        business,
        cost_owner,
        {
            "operation": "withdraw",
            "component_basis_id": assigned["component_basis_id"],
            "expected_event_sequence": cost_evidence_cursor(session, business),
            "reason": "Withdraw allocation",
        },
    )
    current = reviewed_contribution(session, business.tenant.id, data[0].id)
    assert current["db2"] is None and current["basis_db2"] == "456.0000"
    assert reviewed_contribution(session, business.tenant.id, **read_args) == first
    zero = refresh(session, business, cost_owner, args, data, categories())
    _, second = stock.commit_review(session, business, cost_owner, zero)
    assert second["db2"] == "570.0000" and second["revision"] == 2
    assert (
        reviewed_contribution(session, business.tenant.id, **read_args)["db2"]
        == "456.0000"
    )


@pytest.mark.parametrize("amount", ["-10", "10"])
def test_supplier_credit_has_explicit_reducing_effect(
    session, business, cost_owner, amount
):
    args, data = revenue.prepared(session, business, cost_owner)
    doc = costs.evidence(session, business, amount, "0", "supplier_credit_note")
    assign = selling(session, business, data[0], doc, amount)
    assign["parts"][0]["cost_effect"] = -1
    stock.commit_review(session, business, cost_owner, assign)
    reviewed = refresh(
        session, business, cost_owner, args, data, categories("outbound_freight")
    )
    _, result = stock.commit_review(session, business, cost_owner, reviewed)
    assert result["db2"] == "580.0000"


def test_independent_unknown_and_contradictory_zero(session, business, cost_owner):
    args, data = revenue.prepared(session, business, cost_owner)
    doc = costs.evidence(session, business, "24", "0")
    stock.commit_review(
        session, business, cost_owner, selling(session, business, data[0], doc, "24")
    )
    reviewed = refresh(session, business, cost_owner, args, data, categories())
    with pytest.raises(core.InvalidOperation, match="zero"):
        preview_cost_change(
            session, business.tenant.id, reviewed, principal=Principal(cost_owner.id)
        )
    reviewed["selling_categories"] = categories("outbound_freight")
    reviewed["selling_categories"][1]["disposition"] = "unresolved"
    _, result = stock.commit_review(session, business, cost_owner, reviewed)
    assert result["db1"] == "570.0000" and result["db2"] is None
    assert result["known_selling_cost"] == "24.0000"
    assert result["known_direct_selling_cost"] == "24.0000"
    assert result["direct_selling_cost"] is result["allocated_selling_cost"] is None
    assert "selling_category:fulfilment" in result["missing_basis"]


@pytest.mark.parametrize(
    "change, message",
    [
        ("excess", "exceed"),
        ("sign", "sign"),
        ("effect", "effect"),
        ("tax", "tax"),
        ("currency", "currency"),
        ("foreign", "not found"),
        ("stale", "stale"),
        ("hash", "stale"),
        ("target", "sales invoice"),
    ],
)
def test_selling_assignment_refusals(session, business, cost_owner, change, message):
    _args, data = revenue.prepared(session, business, cost_owner)
    doc = costs.evidence(session, business, "24", "5")
    assign = selling(session, business, data[0], doc, "24")
    if change == "excess":
        assign["parts"][0]["source_share"] = "25"
    if change == "sign":
        assign["parts"][0]["source_share"] = "-24"
    if change == "effect":
        assign["parts"][0]["cost_effect"] = -1
    if change == "tax":
        assign["tax_treatment"] = "not_applicable"
    if change == "currency":
        doc.currency = "USD"
        session.flush()
        assign["expected_evidence_hash"] = cost_evidence(
            session, business.tenant.id, doc.id
        )["evidence_hash"]
    if change == "foreign":
        assign["parts"][0]["document_line_id"] = "foreign"
    if change == "stale":
        assign["expected_event_sequence"] = 0
    if change == "hash":
        assign["expected_evidence_hash"] = "0" * 64
    if change == "target":
        assign["parts"][0]["document_line_id"] = data[1].id
    with pytest.raises(
        (core.InvalidOperation, core.Conflict, core.NotFound), match=message
    ):
        preview_cost_change(
            session, business.tenant.id, assign, principal=Principal(cost_owner.id)
        )


def test_source_cannot_be_reused_across_acquisition_and_selling(
    session, business, cost_owner
):
    _args, data = revenue.prepared(session, business, cost_owner)
    movement = session.get(Movement, data[5]["receipt_sources"][0]["movement_id"])
    doc = costs.evidence(session, business, "24", "0")
    costs.execute(
        session,
        business,
        cost_owner,
        costs.assignment(session, business, movement, doc, "24"),
    )
    with pytest.raises(core.InvalidOperation, match="[Aa]cquisition"):
        costs.execute(
            session,
            business,
            cost_owner,
            selling(session, business, data[0], doc, "24"),
        )
    other = costs.evidence(session, business, "10", "0")
    assigned = costs.execute(
        session, business, cost_owner, selling(session, business, data[0], other, "10")
    )
    with pytest.raises(core.InvalidOperation, match="[Ss]elling"):
        costs.execute(
            session,
            business,
            cost_owner,
            costs.assignment(session, business, movement, other, "10"),
        )
    fresh = costs.evidence(session, business, "10", "0")
    replace = costs.assignment(
        session,
        business,
        movement,
        fresh,
        "10",
        operation="replace",
        previous_component_basis_id=assigned["component_basis_id"],
    )
    with pytest.raises(core.InvalidOperation, match="[Ss]elling"):
        costs.execute(session, business, cost_owner, replace)


def test_selling_owner_confirmation_rollback_and_immutable_evidence(
    session, business, cost_owner, monkeypatch
):
    from reality.db.contribution import CostSellingPart
    from reality.services import selling_costs

    _args, data = revenue.prepared(session, business, cost_owner)
    doc = costs.evidence(session, business, "24", "0")
    args = selling(session, business, data[0], doc, "24")
    with pytest.raises(core.InvalidOperation, match="confirmation"):
        execute_cost_change(
            session,
            business.tenant.id,
            arguments=args,
            action_id="none",
            actor_id=cost_owner.id,
        )
    original = selling_costs._new

    def fail(*a, **kw):
        result = original(*a, **kw)
        if a[1] is CostSellingPart:
            raise RuntimeError("rollback selling")
        return result

    monkeypatch.setattr(selling_costs, "_new", fail)
    with pytest.raises(RuntimeError, match="rollback selling"):
        costs.execute(session, business, cost_owner, args)
    assert session.scalar(select(CostSellingPart.id)) is None
    monkeypatch.setattr(selling_costs, "_new", original)
    costs.execute(session, business, cost_owner, args)
    from reality.services.costing import _protect_document

    with pytest.raises(core.InvalidOperation, match="immutable"):
        _protect_document(session, business.tenant.id, doc.id)
    with pytest.raises(core.InvalidOperation, match="cannot be overwritten"):
        core.correct_manual_document(
            session,
            business.tenant.id,
            doc.id,
            document_type=doc.type,
            number=doc.number,
            party_id=doc.party_id,
            amount="99",
        )


def test_reassignment_replaces_complete_revision_and_preserves_history(
    session, business, cost_owner
):
    args, data = revenue.prepared(session, business, cost_owner)
    doc = costs.evidence(session, business, "114", "0")
    first_assignment = costs.execute(
        session, business, cost_owner, selling(session, business, data[0], doc)
    )
    review = refresh(
        session, business, cost_owner, args, data, categories("outbound_freight")
    )
    _, first = stock.commit_review(session, business, cost_owner, review)
    changed = costs.execute(
        session, business, cost_owner, selling(session, business, data[0], doc, "24")
    )
    assert changed["revision"] == 2 and changed["unassigned_basis"] == "90.0000"
    assert changed["component_basis_id"] == first_assignment["component_basis_id"]
    review = refresh(
        session, business, cost_owner, args, data, categories("outbound_freight")
    )
    _, second = stock.commit_review(session, business, cost_owner, review)
    assert second["db2"] == "546.0000"
    _, lines = core.create_manual_document_with_lines(
        session,
        business.tenant.id,
        "sales_invoice",
        "OTHER",
        business.customer.id,
        [
            {
                "item_id": business.item.id,
                "quantity": "1",
                "unit": business.item.unit,
                "gross_amount": "1",
            }
        ],
        "1",
    )
    costs.execute(
        session, business, cost_owner, selling(session, business, lines[0], doc, "114")
    )
    review = refresh(session, business, cost_owner, args, data, categories())
    _, third = stock.commit_review(session, business, cost_owner, review)
    assert third["db2"] == "570.0000"
    old = reviewed_contribution(
        session, business.tenant.id, data[0].id, review_id=first["review_id"]
    )
    assert old["db2"] == "456.0000"


def test_selling_foreign_links_and_historical_read_refuse(
    session, business, cost_owner
):
    args, data = revenue.prepared(session, business, cost_owner)
    doc = costs.evidence(session, business, "24", "0")
    other = core.create_tenant(session, "Neighbor")
    party = core.create_party(session, other.id, "Neighbor customer", "customer")
    foreign_doc, lines = core.create_manual_document_with_lines(
        session,
        other.id,
        "sales_invoice",
        "FOREIGN",
        party.id,
        [{"quantity": "1", "unit": "piece", "gross_amount": "1"}],
        "1",
    )
    for changed in [
        selling(session, business, lines[0], doc, "24"),
        selling(session, business, data[0], doc, "24")
        | {"document_id": foreign_doc.id},
    ]:
        with pytest.raises(core.NotFound):
            preview_cost_change(
                session, business.tenant.id, changed, principal=Principal(cost_owner.id)
            )
    costs.execute(
        session, business, cost_owner, selling(session, business, data[0], doc, "24")
    )
    review = refresh(
        session, business, cost_owner, args, data, categories("outbound_freight")
    )
    _, result = stock.commit_review(session, business, cost_owner, review)
    for read in [
        lambda: reviewed_contribution(
            session, other.id, data[0].id, review_id=result["review_id"]
        ),
        lambda: run_read_tool(
            session,
            other.id,
            "cost.contribution.get",
            {"document_line_id": data[0].id, "review_id": result["review_id"]},
        ),
    ]:
        with pytest.raises(core.NotFound):
            read()
    from sqlalchemy.exc import IntegrityError

    from reality.db.contribution import CostSellingReviewMember

    with pytest.raises(IntegrityError), session.begin_nested():
        session.add(
            CostSellingReviewMember(
                id=core.uid("wrong"),
                tenant_id=other.id,
                review_id=result["review_id"],
                part_id=result["trace"]["selling"]["parts"][0]["part"]["id"],
            )
        )
        session.flush()


def test_selling_frozen_reads_do_not_write_or_enumerate_live_assignments(
    session, business, cost_owner, monkeypatch
):
    from sqlalchemy import event

    from reality.db.contribution import CostSellingPart
    from reality.services import selling_costs

    args, data = revenue.prepared(session, business, cost_owner)
    doc = costs.evidence(session, business, "24", "0")
    costs.execute(
        session, business, cost_owner, selling(session, business, data[0], doc, "24")
    )
    review = refresh(
        session, business, cost_owner, args, data, categories("outbound_freight")
    )
    _, result = stock.commit_review(session, business, cost_owner, review)

    def no_live(*a, **kw):
        raise AssertionError("live attribution scan during frozen read")

    monkeypatch.setattr(selling_costs, "_active", no_live)
    writes = []

    def observe(conn, cursor, statement, parameters, context, executemany):
        if statement.lstrip().split()[0].upper() in {"INSERT", "UPDATE", "DELETE"}:
            writes.append(statement)

    conn = session.connection()
    event.listen(conn, "before_cursor_execute", observe)
    try:
        assert (
            reviewed_contribution(
                session, business.tenant.id, data[0].id, review_id=result["review_id"]
            )
            == result
        )
    finally:
        event.remove(conn, "before_cursor_execute", observe)
    assert not writes
    part = session.get(
        CostSellingPart, result["trace"]["selling"]["parts"][0]["part"]["id"]
    )
    part.source_share += 1
    session.flush()
    with pytest.raises(core.InvalidOperation, match="integrity"):
        reviewed_contribution(
            session, business.tenant.id, data[0].id, review_id=result["review_id"]
        )


def test_selling_proposal_binding_replay_and_demotion(session, business, cost_owner):
    import json

    from reality.db.core import TenantMembership
    from reality.services.analytics.reports import caller
    from reality.tools.application import (
        approve_and_execute_proposal,
        create_change_proposal,
    )

    _args, data = revenue.prepared(session, business, cost_owner)
    doc = costs.evidence(session, business, "24", "0")
    args = selling(session, business, data[0], doc, "24")
    with caller(Principal(cost_owner.id)):
        action = create_change_proposal(
            session, business.tenant.id, "cost.change", args
        )
    with pytest.raises(core.InvalidOperation, match="bound"):
        execute_cost_change(
            session,
            business.tenant.id,
            arguments=args | {"reason": "changed"},
            action_id=action.id,
            actor_id=cost_owner.id,
            confirmed=True,
        )
    membership = session.scalar(
        select(TenantMembership).where(
            TenantMembership.tenant_id == business.tenant.id,
            TenantMembership.user_id == cost_owner.id,
        )
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
    membership.role = "owner"
    session.flush()
    first = approve_and_execute_proposal(
        session,
        business.tenant.id,
        action.id,
        confirming_principal=Principal(cost_owner.id),
        confirmed=True,
    )
    retained = json.loads(first.output)
    again = approve_and_execute_proposal(
        session,
        business.tenant.id,
        action.id,
        confirming_principal=Principal(cost_owner.id),
        confirmed=True,
    )
    assert json.loads(again.output) == retained


def test_selling_schema_preserves_existing_receipt_tax_and_parts():
    from reality.tools.costing import change_input_schema

    schema = change_input_schema()
    assert "mixed" in schema["properties"]["tax_treatment"]["enum"]
    assert schema["properties"]["parts"]["items"]["anyOf"] == [
        {"$ref": "#/$defs/CostPart"},
        {"$ref": "#/$defs/SellingPart"},
    ]


def test_missing_net_is_not_recomputed_and_assignment_bound_refuses(
    session, business, cost_owner, monkeypatch
):
    from reality.services import selling_costs

    _args, data = revenue.prepared(session, business, cost_owner)
    doc = core.create_document(
        session,
        business.tenant.id,
        "supplier_invoice",
        "GROSS-ONLY",
        business.supplier.id,
        "24",
    )
    with pytest.raises(core.InvalidOperation, match="Received net"):
        costs.execute(
            session,
            business,
            cost_owner,
            selling(session, business, data[0], doc, "24"),
        )
    doc = costs.evidence(session, business, "24", "0")
    monkeypatch.setattr(selling_costs, "LIMIT", 1)
    costs.execute(
        session, business, cost_owner, selling(session, business, data[0], doc, "24")
    )
    extra = costs.evidence(session, business, "1", "0")
    with pytest.raises(core.InvalidOperation, match="bound"):
        costs.execute(
            session,
            business,
            cost_owner,
            selling(session, business, data[0], extra, "1"),
        )


def test_selling_review_requires_all_categories_and_exact_precision():
    from reality.domain.costing import ContributionReview

    base = {
        "operation": "contribution_review",
        "expected_event_sequence": 1,
        "reason": "Review",
        "document_line_id": "line",
        "expected_candidate_hash": "a" * 64,
        "profile": "commercial_v1",
        "profile_confirmed": True,
        "revenue_complete": True,
        "economic_at": "2026-09-19T12:00:00Z",
    }
    for values in [[], categories()[:-1], categories() + [categories()[0]]]:
        with pytest.raises(ValueError):
            ContributionReview.model_validate(base | {"selling_categories": values})
    for amount in ["0.00001", "NaN", "Infinity"]:
        parts = request()["parts"]
        parts[0]["source_share"] = amount
        with pytest.raises(ValueError):
            SellingAssign.model_validate(request(parts=parts))
