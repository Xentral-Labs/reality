"""Shared preview/confirm/replay behavior for partial commercial matching."""

import json
from decimal import Decimal

import pytest
import test_contribution_services as fixtures
import test_costing_services as costs
import test_inventory_costing_services as stock
from sqlalchemy import func, select

from reality.db.contribution import CostCommercialMatchRevision
from reality.db.inventory_costing import CostInventoryMember, CostMovementBasis
from reality.mcp.catalog import MCP_TOOL_REGISTRY
from reality.services import core
from reality.services.costing import (
    _sequence,
    commercial_match,
    contribution_preview,
    preview_cost_change,
)
from reality.services.exceptions import (
    explain_operational_exception,
    operational_exceptions,
)
from reality.services.finance import components
from reality.services.memberships import Principal
from reality.tools.application import approve_and_execute_proposal, run_read_tool

cost_owner = costs.cost_owner


def arguments(session, business, owner):
    data = fixtures.prepared(session, business, owner)
    candidate = contribution_preview(session, business.tenant.id, data[0].id)
    return {
        "operation": "commercial_match_review",
        "expected_event_sequence": candidate["event_sequence"],
        "document_line_id": data[0].id,
        "expected_evidence_hash": candidate["trace"]["revenue"]["evidence_hash"],
        "profile": "commercial_v1",
        "profile_confirmed": True,
        "goods_cost_disposition": "not_applicable",
        "reason": "Confirmed line-specific commercial disposition",
    }, data


def test_commercial_match_confirm_replay_and_revision(session, business, cost_owner):
    args, _data = arguments(session, business, cost_owner)
    preview = preview_cost_change(
        session, business.tenant.id, args, principal=Principal(cost_owner.id)
    )
    assert preview["requires_human_confirmation"] is True
    action, first = stock.commit_review(session, business, cost_owner, args)
    assert first["revision"] == 1
    assert first["goods_cost_disposition"] == "not_applicable"
    replay = approve_and_execute_proposal(
        session,
        business.tenant.id,
        action.id,
        confirming_principal=Principal(cost_owner.id),
        confirmed=True,
    )
    assert json.loads(replay.output) == first
    assert (
        session.scalar(select(func.count()).select_from(CostCommercialMatchRevision))
        == 1
    )

    updated = args | {
        "expected_event_sequence": first["event_sequence"],
        "reason": "Reconfirmed after the retained commercial review event",
    }
    _action, second = stock.commit_review(session, business, cost_owner, updated)
    assert second["revision"] == 2
    assert second["supersedes_id"] == first["match_revision_id"]


def test_commercial_match_rejects_stale_foreign_and_ambiguous_shapes(
    session, business, cost_owner
):
    args, _data = arguments(session, business, cost_owner)
    with pytest.raises(core.Conflict, match="evidence"):
        preview_cost_change(
            session,
            business.tenant.id,
            args | {"expected_evidence_hash": "0" * 64},
            principal=Principal(cost_owner.id),
        )


def test_commercial_inventory_match_uses_exact_frozen_portions(
    session, business, cost_owner
):
    args, data = arguments(session, business, cost_owner)
    candidate = contribution_preview(session, business.tenant.id, data[0].id)
    consumption = candidate["trace"]["consumption"]
    movement_basis = session.scalar(
        select(CostMovementBasis).where(
            CostMovementBasis.tenant_id == business.tenant.id,
            CostMovementBasis.movement_id == candidate["trace"]["movement_id"],
        )
    )
    member = session.scalar(
        select(CostInventoryMember).where(
            CostInventoryMember.tenant_id == business.tenant.id,
            CostInventoryMember.review_id == candidate["trace"]["inventory_review_id"],
            CostInventoryMember.movement_basis_id == movement_basis.id,
        )
    )
    parts = []
    for portion in consumption["parts"]:
        entry = session.scalar(
            select(CostMovementBasis).where(
                CostMovementBasis.tenant_id == business.tenant.id,
                CostMovementBasis.movement_id == portion["entry_movement_id"],
            )
        )
        receipt = session.scalar(
            select(CostMovementBasis).where(
                CostMovementBasis.tenant_id == business.tenant.id,
                CostMovementBasis.movement_id == portion["receipt_movement_id"],
            )
        )
        parts.append(
            {
                "inventory_member_id": member.id,
                "entry_movement_basis_id": entry.id,
                "receipt_movement_basis_id": receipt.id,
                "quantity": portion["quantity"],
            }
        )
    inventory_args = args | {
        "goods_cost_disposition": "inventory",
        "inventory_parts": parts,
    }
    preview_cost_change(
        session,
        business.tenant.id,
        inventory_args,
        principal=Principal(cost_owner.id),
    )
    _action, result = stock.commit_review(session, business, cost_owner, inventory_args)
    assert len(result["inventory_part_ids"]) == len(parts)
    observed = commercial_match(session, business.tenant.id, data[0].id)
    assert observed["goods_cost"] == "630.0000"
    assert observed["db1"] == candidate["known_db1"] == "570.0000"
    assert observed["persistence"]["business_writes"] is False
    assert (
        commercial_match(
            session,
            business.tenant.id,
            data[0].id,
            match_revision_id=result["match_revision_id"],
        )
        == observed
    )
    read_arguments = {
        "document_line_id": data[0].id,
        "match_revision_id": result["match_revision_id"],
    }
    assert (
        run_read_tool(
            session,
            business.tenant.id,
            "cost.commercial-match.get",
            read_arguments,
        )
        == observed
    )
    assert (
        MCP_TOOL_REGISTRY["cost_commercial_match_get"].handler(
            session, business.tenant.id, read_arguments
        )
        == observed
    )
    foreign = core.create_tenant(session, "Foreign commercial read")
    for read in (
        lambda: commercial_match(
            session,
            foreign.id,
            data[0].id,
            match_revision_id=result["match_revision_id"],
        ),
        lambda: run_read_tool(
            session, foreign.id, "cost.commercial-match.get", read_arguments
        ),
        lambda: MCP_TOOL_REGISTRY["cost_commercial_match_get"].handler(
            session, foreign.id, read_arguments
        ),
    ):
        with pytest.raises(core.NotFound):
            read()

    too_large = inventory_args | {
        "expected_event_sequence": result["event_sequence"],
        "inventory_parts": [parts[0] | {"quantity": "120"}],
    }
    with pytest.raises(core.InvalidOperation):
        preview_cost_change(
            session,
            business.tenant.id,
            too_large,
            principal=Principal(cost_owner.id),
        )
    with pytest.raises(core.InvalidOperation):
        preview_cost_change(
            session,
            business.tenant.id,
            args
            | {
                "goods_cost_disposition": "inventory",
                "inventory_parts": [],
            },
            principal=Principal(cost_owner.id),
        )
    other = core.create_tenant(session, "Other commercial company")
    with pytest.raises(core.NotFound):
        preview_cost_change(
            session,
            other.id,
            args | {"document_line_id": data[0].id},
            principal=Principal(cost_owner.id),
        )


def test_commercial_direct_match_observes_retained_attribution(
    session, business, cost_owner
):
    args, data = arguments(session, business, cost_owner)
    movement = costs.receipt(session, business)
    document = costs.evidence(session, business, "100", "0")
    assigned = costs.execute(
        session,
        business,
        cost_owner,
        costs.assignment(session, business, movement, document, "100"),
    )
    refreshed = contribution_preview(session, business.tenant.id, data[0].id)
    direct_args = args | {
        "expected_event_sequence": refreshed["event_sequence"],
        "goods_cost_disposition": "direct_evidence",
        "direct_cost_complete": True,
        "direct_parts": [
            {
                "attribution_revision_id": assigned["attribution_revision_id"],
                "input_role": "service_input",
            }
        ],
    }
    _action, result = stock.commit_review(session, business, cost_owner, direct_args)
    observed = commercial_match(
        session,
        business.tenant.id,
        data[0].id,
        match_revision_id=result["match_revision_id"],
    )
    assert observed["goods_cost"] == "100.0000"
    assert observed["db1"] == "1100.0000"
    assert observed["missing_basis"] == []

    partial_document = costs.evidence(session, business, "100", "0")
    partial = costs.execute(
        session,
        business,
        cost_owner,
        costs.assignment(session, business, movement, partial_document, "50"),
    )
    partial_request = direct_args | {
        "expected_event_sequence": _sequence(session, business.tenant.id),
        "direct_parts": [
            {
                "attribution_revision_id": partial["attribution_revision_id"],
                "input_role": "service_input",
            }
        ],
    }
    with pytest.raises(core.InvalidOperation, match="complete retained attribution"):
        preview_cost_change(
            session,
            business.tenant.id,
            partial_request,
            principal=Principal(cost_owner.id),
        )


def test_commercial_credit_uses_exact_original_return_portion(
    session, business, cost_owner
):
    inventory_args, receipt, issue = stock.prepared(session, business, cost_owner)
    returned = core.record_movement(
        session,
        business.tenant.id,
        "return",
        business.item.id,
        "10",
        to_location_id=business.location.id,
    )
    inventory_args.update(
        effective_at=core.now().isoformat(),
        expected_event_sequence=_sequence(session, business.tenant.id),
        customer_return_ids=[returned.id],
        return_parts=[
            {
                "movement_id": returned.id,
                "issue_movement_id": issue.id,
                "entry_movement_id": receipt.id,
                "receipt_movement_id": receipt.id,
                "quantity": "10",
            }
        ],
    )
    _inventory_action, inventory = stock.commit_review(
        session, business, cost_owner, inventory_args
    )
    credit, lines = core.create_manual_document_with_lines(
        session,
        business.tenant.id,
        "credit_note",
        "CN-RETURN",
        business.customer.id,
        [
            {
                "item_id": business.item.id,
                "quantity": "10",
                "unit": business.item.unit,
                "gross_amount": "124.95",
            }
        ],
        "124.95",
    )
    line = lines[0]
    line.payload = json.dumps({"reality_finance_v1": {"net": "-105", "tax": "-19.95"}})
    session.flush()
    received = components._received(session, business.tenant.id, credit, line)
    return_basis = session.scalar(
        select(CostMovementBasis).where(
            CostMovementBasis.tenant_id == business.tenant.id,
            CostMovementBasis.movement_id == returned.id,
        )
    )
    issue_basis = session.scalar(
        select(CostMovementBasis).where(
            CostMovementBasis.tenant_id == business.tenant.id,
            CostMovementBasis.movement_id == issue.id,
        )
    )
    receipt_basis = session.scalar(
        select(CostMovementBasis).where(
            CostMovementBasis.tenant_id == business.tenant.id,
            CostMovementBasis.movement_id == receipt.id,
        )
    )
    return_member = session.scalar(
        select(CostInventoryMember).where(
            CostInventoryMember.tenant_id == business.tenant.id,
            CostInventoryMember.review_id == inventory["review_id"],
            CostInventoryMember.movement_basis_id == return_basis.id,
        )
    )
    issue_member = session.scalar(
        select(CostInventoryMember).where(
            CostInventoryMember.tenant_id == business.tenant.id,
            CostInventoryMember.review_id == inventory["review_id"],
            CostInventoryMember.movement_basis_id == issue_basis.id,
        )
    )
    request = {
        "operation": "commercial_match_review",
        "expected_event_sequence": _sequence(session, business.tenant.id),
        "document_line_id": line.id,
        "expected_evidence_hash": received["evidence_hash"],
        "profile": "commercial_v1",
        "profile_confirmed": True,
        "goods_cost_disposition": "inventory",
        "inventory_parts": [
            {
                "inventory_member_id": return_member.id,
                "original_issue_member_id": issue_member.id,
                "entry_movement_basis_id": receipt_basis.id,
                "receipt_movement_basis_id": receipt_basis.id,
                "quantity": "10",
            }
        ],
        "reason": "Exact customer return portion confirmed for the credit",
    }
    _action, matched = stock.commit_review(session, business, cost_owner, request)
    observed = commercial_match(
        session,
        business.tenant.id,
        line.id,
        match_revision_id=matched["match_revision_id"],
    )
    assert Decimal(observed["stated_net"]) == Decimal(-105)
    assert observed["goods_cost"] == "-105.0000"
    assert observed["db1"] == "0.0000"


def test_return_goods_and_credit_lifecycles_remain_independent_and_explainable(
    session, business
):
    tenant_id = business.tenant.id
    core.record_movement(
        session,
        tenant_id,
        "opening_stock",
        business.item.id,
        "10",
        to_location_id=business.location.id,
    )
    _, order, order_lines, commitments = core.create_manual_order(
        session,
        tenant_id,
        "sales",
        "SO-RETURN-LIFECYCLE",
        business.company.id,
        business.customer.id,
        business.location.id,
        [
            {
                "item_id": business.item.id,
                "quantity": "5",
                "unit": business.item.unit,
                "unit_price": "10",
                "gross_amount": "50",
            }
        ],
        "50",
        document_date="2026-09-01",
    )
    core.record_movement(
        session,
        tenant_id,
        "shipment",
        business.item.id,
        "5",
        from_location_id=business.location.id,
        commitment_id=commitments[0].id,
    )
    core.create_manual_document_with_lines(
        session,
        tenant_id,
        "sales_invoice",
        "INV-RETURN-LIFECYCLE",
        business.customer.id,
        [
            {
                "item_id": business.item.id,
                "quantity": "5",
                "unit": business.item.unit,
                "gross_amount": "50",
                "billed_document_line_id": order_lines[0].id,
            }
        ],
        "50",
        document_date="2026-09-02",
    )
    core.record_movement(
        session,
        tenant_id,
        "return",
        business.item.id,
        "3",
        to_location_id=business.location.id,
        commitment_id=commitments[0].id,
    )

    rows = {row.class_id: row for row in operational_exceptions(session, tenant_id)}
    short = rows["returned_not_credited"]
    assert short.causal_values["uncredited_quantity"] == Decimal(3)
    explained = explain_operational_exception(session, tenant_id, short.id)
    assert explained["record_id"] == order_lines[0].id
    assert explained["trace"]["commitment_id"] == commitments[0].id
    assert explained["trace"]["document_id"] == order.id

    def credit(number: str, quantity: str) -> None:
        core.create_manual_document_with_lines(
            session,
            tenant_id,
            "credit_note",
            number,
            business.customer.id,
            [
                {
                    "item_id": business.item.id,
                    "quantity": quantity,
                    "unit": business.item.unit,
                    "gross_amount": str(Decimal(quantity) * Decimal(10)),
                    "billed_document_line_id": order_lines[0].id,
                }
            ],
            str(Decimal(quantity) * Decimal(10)),
            document_date="2026-09-03",
        )

    credit("CN-RETURN-PARTIAL", "1")
    rows = {row.class_id: row for row in operational_exceptions(session, tenant_id)}
    assert rows["returned_not_credited"].causal_values[
        "uncredited_quantity"
    ] == Decimal(2)

    credit("CN-RETURN-OVER", "3")
    rows = {row.class_id: row for row in operational_exceptions(session, tenant_id)}
    assert "returned_not_credited" not in rows
    excess = rows["credited_not_returned"]
    assert excess.causal_values["unreturned_quantity"] == Decimal(1)
    assert (
        explain_operational_exception(session, tenant_id, excess.id)["trace"][
            "document_line_id"
        ]
        == order_lines[0].id
    )

    core.record_movement(
        session,
        tenant_id,
        "return",
        business.item.id,
        "1",
        to_location_id=business.location.id,
        commitment_id=commitments[0].id,
    )
    rows = {row.class_id: row for row in operational_exceptions(session, tenant_id)}
    assert "returned_not_credited" not in rows
    assert "credited_not_returned" not in rows


def test_commercial_split_lines_share_capacity_without_overlap(
    session, business, cost_owner
):
    _args, data = arguments(session, business, cost_owner)
    inventory = data[5]
    issue_basis = session.scalar(
        select(CostMovementBasis).where(
            CostMovementBasis.tenant_id == business.tenant.id,
            CostMovementBasis.movement_id == data[4].id,
        )
    )
    issue_member = session.scalar(
        select(CostInventoryMember).where(
            CostInventoryMember.tenant_id == business.tenant.id,
            CostInventoryMember.review_id == inventory["review_id"],
            CostInventoryMember.movement_basis_id == issue_basis.id,
        )
    )
    frozen_part = inventory["consumption"][0]["parts"][0]
    entry_basis = session.scalar(
        select(CostMovementBasis).where(
            CostMovementBasis.tenant_id == business.tenant.id,
            CostMovementBasis.movement_id == frozen_part["entry_movement_id"],
        )
    )
    receipt_basis = session.scalar(
        select(CostMovementBasis).where(
            CostMovementBasis.tenant_id == business.tenant.id,
            CostMovementBasis.movement_id == frozen_part["receipt_movement_id"],
        )
    )
    invoice, lines = core.create_manual_document_with_lines(
        session,
        business.tenant.id,
        "sales_invoice",
        "INV-SPLIT",
        business.customer.id,
        [
            {
                "item_id": business.item.id,
                "quantity": "30",
                "unit": business.item.unit,
                "gross_amount": "714",
            },
            {
                "item_id": business.item.id,
                "quantity": "30",
                "unit": business.item.unit,
                "gross_amount": "714",
            },
        ],
        "1428",
    )
    for line in lines:
        line.payload = json.dumps({"reality_finance_v1": {"net": "600", "tax": "114"}})
    session.flush()

    def request(line, quantity):
        received = components._received(session, business.tenant.id, invoice, line)
        return {
            "operation": "commercial_match_review",
            "expected_event_sequence": _sequence(session, business.tenant.id),
            "document_line_id": line.id,
            "expected_evidence_hash": received["evidence_hash"],
            "profile": "commercial_v1",
            "profile_confirmed": True,
            "goods_cost_disposition": "inventory",
            "inventory_parts": [
                {
                    "inventory_member_id": issue_member.id,
                    "entry_movement_basis_id": entry_basis.id,
                    "receipt_movement_basis_id": receipt_basis.id,
                    "quantity": quantity,
                }
            ],
            "reason": "Exact split invoice portion confirmed",
        }

    results = []
    for line in lines:
        _action, result = stock.commit_review(
            session, business, cost_owner, request(line, "30")
        )
        results.append(result)
        observed = commercial_match(
            session,
            business.tenant.id,
            line.id,
            match_revision_id=result["match_revision_id"],
        )
        assert observed["goods_cost"] == "315.0000"
        assert observed["db1"] == "285.0000"

    excess_invoice, excess_lines = core.create_manual_document_with_lines(
        session,
        business.tenant.id,
        "sales_invoice",
        "INV-EXCESS",
        business.customer.id,
        [
            {
                "item_id": business.item.id,
                "quantity": "1",
                "unit": business.item.unit,
                "gross_amount": "11.90",
            }
        ],
        "11.90",
    )
    excess = excess_lines[0]
    excess.payload = json.dumps({"reality_finance_v1": {"net": "10", "tax": "1.90"}})
    session.flush()
    excess_received = components._received(
        session, business.tenant.id, excess_invoice, excess
    )
    excess_request = request(excess, "1") | {
        "expected_evidence_hash": excess_received["evidence_hash"]
    }
    with pytest.raises(core.InvalidOperation, match="match_capacity"):
        preview_cost_change(
            session,
            business.tenant.id,
            excess_request,
            principal=Principal(cost_owner.id),
        )
    first_received = components._received(
        session, business.tenant.id, invoice, lines[0]
    )
    released = request(lines[0], "30") | {
        "expected_event_sequence": _sequence(session, business.tenant.id),
        "expected_evidence_hash": first_received["evidence_hash"],
        "goods_cost_disposition": "unresolved",
        "inventory_parts": [],
        "reason": "Release the prior split while its replacement is unresolved",
    }
    _release_action, released_result = stock.commit_review(
        session, business, cost_owner, released
    )
    assert released_result["supersedes_id"] == results[0]["match_revision_id"]
    excess_request["expected_event_sequence"] = _sequence(session, business.tenant.id)
    _excess_action, excess_result = stock.commit_review(
        session, business, cost_owner, excess_request
    )
    assert excess_result["revision"] == 1
    historical = commercial_match(
        session,
        business.tenant.id,
        lines[0].id,
        match_revision_id=results[0]["match_revision_id"],
    )
    assert historical["db1"] == "285.0000"
    assert (
        commercial_match(session, business.tenant.id, lines[0].id)["review_state"]
        == "incomplete"
    )
    assert len(results) == 2


def test_free_goods_keep_inventory_cost_and_zero_revenue(session, business, cost_owner):
    _args, data = arguments(session, business, cost_owner)
    inventory = data[5]
    issue_basis = session.scalar(
        select(CostMovementBasis).where(
            CostMovementBasis.tenant_id == business.tenant.id,
            CostMovementBasis.movement_id == data[4].id,
        )
    )
    issue_member = session.scalar(
        select(CostInventoryMember).where(
            CostInventoryMember.tenant_id == business.tenant.id,
            CostInventoryMember.review_id == inventory["review_id"],
            CostInventoryMember.movement_basis_id == issue_basis.id,
        )
    )
    frozen = inventory["consumption"][0]["parts"][0]
    entry = session.scalar(
        select(CostMovementBasis).where(
            CostMovementBasis.tenant_id == business.tenant.id,
            CostMovementBasis.movement_id == frozen["entry_movement_id"],
        )
    )
    receipt = session.scalar(
        select(CostMovementBasis).where(
            CostMovementBasis.tenant_id == business.tenant.id,
            CostMovementBasis.movement_id == frozen["receipt_movement_id"],
        )
    )
    invoice, lines = core.create_manual_document_with_lines(
        session,
        business.tenant.id,
        "sales_invoice",
        "INV-FREE",
        business.customer.id,
        [
            {
                "item_id": business.item.id,
                "quantity": "60",
                "unit": business.item.unit,
                "gross_amount": "0",
            }
        ],
        "0",
    )
    line = lines[0]
    line.payload = json.dumps({"reality_finance_v1": {"net": "0", "tax": "0"}})
    session.flush()
    received = components._received(session, business.tenant.id, invoice, line)
    request = {
        "operation": "commercial_match_review",
        "expected_event_sequence": _sequence(session, business.tenant.id),
        "document_line_id": line.id,
        "expected_evidence_hash": received["evidence_hash"],
        "profile": "commercial_v1",
        "profile_confirmed": True,
        "goods_cost_disposition": "inventory",
        "inventory_parts": [
            {
                "inventory_member_id": issue_member.id,
                "entry_movement_basis_id": entry.id,
                "receipt_movement_basis_id": receipt.id,
                "quantity": "60",
            }
        ],
        "reason": "Free goods retain their exact issued acquisition cost",
    }
    _action, result = stock.commit_review(session, business, cost_owner, request)
    observed = commercial_match(
        session,
        business.tenant.id,
        line.id,
        match_revision_id=result["match_revision_id"],
    )
    assert observed["stated_net"] == "0.0000"
    assert observed["goods_cost"] == "630.0000"
    assert observed["db1"] == "-630.0000"


@pytest.mark.parametrize(
    "input_role", ["shipping_input", "kit_input", "production_input"]
)
def test_shipping_kit_production_direct_cost_and_unresolved_wip_are_explicit(
    session, business, cost_owner, input_role
):
    movement = costs.receipt(session, business)
    supplier_document = costs.evidence(session, business, "40", "0")
    assigned = costs.execute(
        session,
        business,
        cost_owner,
        costs.assignment(session, business, movement, supplier_document, "40"),
    )
    sales_document, lines = core.create_manual_document_with_lines(
        session,
        business.tenant.id,
        "sales_invoice",
        "INV-SERVICE-WIP",
        business.customer.id,
        [
            {
                "quantity": "1",
                "unit": "service",
                "line_type": "shipping",
                "gross_amount": "119",
            },
            {
                "quantity": "1",
                "unit": "service",
                "line_type": "service",
                "gross_amount": "238",
            },
        ],
        "357",
    )
    lines[0].payload = json.dumps({"reality_finance_v1": {"net": "100", "tax": "19"}})
    lines[1].payload = json.dumps({"reality_finance_v1": {"net": "200", "tax": "38"}})
    session.flush()
    shipping_evidence = components._received(
        session, business.tenant.id, sales_document, lines[0]
    )
    shipping_request = {
        "operation": "commercial_match_review",
        "expected_event_sequence": _sequence(session, business.tenant.id),
        "document_line_id": lines[0].id,
        "expected_evidence_hash": shipping_evidence["evidence_hash"],
        "profile": "commercial_v1",
        "profile_confirmed": True,
        "goods_cost_disposition": "direct_evidence",
        "direct_cost_complete": True,
        "direct_parts": [
            {
                "attribution_revision_id": assigned["attribution_revision_id"],
                "input_role": input_role,
            }
        ],
        "reason": "Shipping-only direct input confirmed from complete evidence",
    }
    _shipping_action, shipping = stock.commit_review(
        session, business, cost_owner, shipping_request
    )
    observed_shipping = commercial_match(
        session,
        business.tenant.id,
        lines[0].id,
        match_revision_id=shipping["match_revision_id"],
    )
    assert observed_shipping["goods_cost"] == "40.0000"
    assert observed_shipping["db1"] == "60.0000"

    wip_evidence = components._received(
        session, business.tenant.id, sales_document, lines[1]
    )
    wip_request = {
        "operation": "commercial_match_review",
        "expected_event_sequence": _sequence(session, business.tenant.id),
        "document_line_id": lines[1].id,
        "expected_evidence_hash": wip_evidence["evidence_hash"],
        "profile": "commercial_v1",
        "profile_confirmed": True,
        "goods_cost_disposition": "unresolved",
        "reason": "Unsupported WIP remains visible instead of receiving inferred cost",
    }
    _wip_action, wip = stock.commit_review(session, business, cost_owner, wip_request)
    observed_wip = commercial_match(
        session,
        business.tenant.id,
        lines[1].id,
        match_revision_id=wip["match_revision_id"],
    )
    assert observed_wip["stated_net"] == "200.0000"
    assert observed_wip["goods_cost"] is observed_wip["db1"] is None
    assert observed_wip["missing_basis"] == ["commercial_goods_cost_unresolved"]
