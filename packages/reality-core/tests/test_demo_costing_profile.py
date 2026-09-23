"""FR-026: the canonical baseline owns bounded, source-backed costing stories."""

import re
from decimal import Decimal

import pytest
from conftest import record_by_id, seed_company
from sqlalchemy import func, select

from reality.db.contribution import (
    CostCommercialMatchRevision,
    CostContributionReview,
    CostRevenueMatchBasis,
    CostSellingPart,
)
from reality.db.core import (
    Document,
    DocumentLine,
    Item,
    Movement,
    PlaygroundRun,
    SourceRecord,
)
from reality.db.inventory_costing import CostInventoryReview
from reality.demo.international import PROFILE_VERSION
from reality.services import company_setup
from reality.services.costing import (
    commercial_match,
    contribution_snapshot,
    cost_query,
    inventory_cost,
    reviewed_contribution,
)
from reality.services.tenant_policy import (
    PlaygroundOperationDenied,
    profile_cost_action_scope,
)

COMPLETE_PORTFOLIO = {
    "fixture_a": {
        "revenue": "1200.0000",
        "goods_cost": "630.0000",
        "direct": "90.0000",
        "allocated": "24.0000",
        "db1": "570.0000",
        "db2": "456.0000",
        "db2_rate": "38.0000",
    },
    "portfolio_healthy": {
        "revenue": "250.0000",
        "goods_cost": "100.0000",
        "direct": "20.0000",
        "allocated": "5.0000",
        "db1": "150.0000",
        "db2": "125.0000",
        "db2_rate": "50.0000",
    },
    "portfolio_low": {
        "revenue": "150.0000",
        "goods_cost": "100.0000",
        "direct": "25.0000",
        "allocated": "15.0000",
        "db1": "50.0000",
        "db2": "10.0000",
        "db2_rate": "6.6667",
    },
    "portfolio_negative": {
        "revenue": "130.0000",
        "goods_cost": "100.0000",
        "direct": "35.0000",
        "allocated": "25.0000",
        "db1": "30.0000",
        "db2": "-30.0000",
        "db2_rate": "-23.0769",
    },
    "portfolio_zero_selling": {
        "revenue": "180.0000",
        "goods_cost": "100.0000",
        "direct": "0.0000",
        "allocated": "0.0000",
        "db1": "80.0000",
        "db2": "80.0000",
        "db2_rate": "44.4444",
    },
    "portfolio_allocated_heavy": {
        "revenue": "220.0000",
        "goods_cost": "100.0000",
        "direct": "10.0000",
        "allocated": "50.0000",
        "db1": "120.0000",
        "db2": "60.0000",
        "db2_rate": "27.2727",
    },
}


def test_demo_documents_are_dated_uniformly_numbered_and_contribution_complete(
    session, scheduled_owner
):
    run = _seed(session, scheduled_owner, "demo-document-quality")
    documents = list(
        session.scalars(select(Document).where(Document.tenant_id == run.tenant_id))
    )
    assert documents
    assert all(document.document_date is not None for document in documents)
    invoices = [document for document in documents if document.type == "sales_invoice"]
    assert invoices
    assert all(
        re.fullmatch(r"INV-\d{8}-[A-Z0-9]{6}", document.number) for document in invoices
    )
    invoice_line_ids = set(
        session.scalars(
            select(DocumentLine.id).where(
                DocumentLine.tenant_id == run.tenant_id,
                DocumentLine.document_id.in_([document.id for document in invoices]),
            )
        )
    )
    reviewed_line_ids = set(
        session.scalars(
            select(CostRevenueMatchBasis.document_line_id)
            .join(
                CostContributionReview,
                (CostContributionReview.tenant_id == CostRevenueMatchBasis.tenant_id)
                & (CostContributionReview.revenue_basis_id == CostRevenueMatchBasis.id),
            )
            .where(CostContributionReview.tenant_id == run.tenant_id)
        )
    )
    edge_case_line_ids = {
        value
        for key in ("split_invoices",)
        for name, value in run.initialization_progress["cases"][key].items()
        if name.endswith("_line_id") and name.startswith("invoice_")
    }
    edge_case_line_ids.update(
        session.scalars(
            select(DocumentLine.id).where(
                DocumentLine.tenant_id == run.tenant_id,
                DocumentLine.document_id.in_(
                    [
                        run.initialization_progress["cases"][key]["invoice_id"]
                        for key in (
                            "price_only_credit",
                            "invoice_reversal",
                            "customer_prepayment",
                            "dunning_with_fee",
                            "customer_bad_debt",
                            "customer_deposit_clearing",
                        )
                    ]
                ),
            )
        )
    )
    assert invoice_line_ids - edge_case_line_ids <= reviewed_line_ids


def _seed(session, owner, key: str = "costing-demo") -> PlaygroundRun:
    result = company_setup.create_company(
        session,
        owner.id,
        key,
        "Harbor Supply",
        "sandbox",
        "international_demo",
        confirmed=True,
    )
    assert seed_company(session, result["tenant_id"]) == "succeeded"
    run = record_by_id(session, PlaygroundRun, result["run_id"])
    assert run.status == "active", (
        run.initialization_error_code,
        run.initialization_progress,
    )
    return run


def test_canonical_profile_versions_and_replays_one_costing_baseline(
    session, scheduled_owner
):
    run = _seed(session, scheduled_owner)
    manifest = run.initialization_progress
    assert PROFILE_VERSION == 12
    assert manifest["profile"] == {"key": "international_demo", "version": 12}
    assert set(manifest["costing_cases"]) == {
        *COMPLETE_PORTFOLIO,
        "late_cost_return",
    }
    counts = (
        session.scalar(
            select(func.count())
            .select_from(CostInventoryReview)
            .where(CostInventoryReview.tenant_id == run.tenant_id)
        ),
        session.scalar(
            select(func.count())
            .select_from(CostCommercialMatchRevision)
            .where(CostCommercialMatchRevision.tenant_id == run.tenant_id)
        ),
        session.scalar(
            select(func.count())
            .select_from(CostContributionReview)
            .where(CostContributionReview.tenant_id == run.tenant_id)
        ),
        session.scalar(
            select(func.count())
            .select_from(CostSellingPart)
            .where(CostSellingPart.tenant_id == run.tenant_id)
        ),
        session.scalar(
            select(func.count())
            .select_from(SourceRecord)
            .where(
                SourceRecord.tenant_id == run.tenant_id,
                SourceRecord.source_system == "demo_profile",
                SourceRecord.external_id.like("COST-PORTFOLIO-%"),
            )
        ),
    )
    assert (
        company_setup.initialize_profile(session, run.id, scheduled_owner.id).id
        == run.id
    )
    assert counts == (
        session.scalar(
            select(func.count())
            .select_from(CostInventoryReview)
            .where(CostInventoryReview.tenant_id == run.tenant_id)
        ),
        session.scalar(
            select(func.count())
            .select_from(CostCommercialMatchRevision)
            .where(CostCommercialMatchRevision.tenant_id == run.tenant_id)
        ),
        session.scalar(
            select(func.count())
            .select_from(CostContributionReview)
            .where(CostContributionReview.tenant_id == run.tenant_id)
        ),
        session.scalar(
            select(func.count())
            .select_from(CostSellingPart)
            .where(CostSellingPart.tenant_id == run.tenant_id)
        ),
        session.scalar(
            select(func.count())
            .select_from(SourceRecord)
            .where(
                SourceRecord.tenant_id == run.tenant_id,
                SourceRecord.source_system == "demo_profile",
                SourceRecord.external_id.like("COST-PORTFOLIO-%"),
            )
        ),
    )

    with (
        pytest.raises(PlaygroundOperationDenied),
        profile_cost_action_scope(
            session,
            run.id,
            scheduled_owner.id,
            {"operation": "inventory_review"},
        ),
    ):
        pass


def test_canonical_profile_declares_current_contribution_readiness(
    session, scheduled_owner
):
    run = _seed(session, scheduled_owner, "costing-readiness")
    manifest = run.initialization_progress
    coverage = manifest["cost_readiness"]

    declared = coverage["contribution_line_ids"]
    assert declared == sorted(
        case["invoice_line_id"]
        for name, case in manifest["costing_cases"].items()
        if name in COMPLETE_PORTFOLIO
    )
    assert coverage["contribution"] == {
        "expected": len(COMPLETE_PORTFOLIO),
        "current": len(COMPLETE_PORTFOLIO),
    }
    assert coverage["state"] == "ready"
    assert coverage["event_sequence"] > 0

    for line_id in declared:
        result = cost_query(
            session,
            run.tenant_id,
            kind="contribution",
            scope_id=line_id,
        )
        assert result["freshness"]["state"] == "ready"
        assert result["result"] is not None
        assert result["result"]["db1"] is not None
        assert result["result"]["db2"] is not None


def test_fresh_demo_cost_context_is_identical_for_web_tool_and_mcp(
    session, scheduled_owner
):
    from reality.mcp.catalog import MCP_TOOL_REGISTRY
    from reality.tools.application import run_read_tool
    from reality.web.api import get_cost_query

    run = _seed(session, scheduled_owner, "costing-interface-parity")
    manifest = run.initialization_progress
    inventory_ids = [manifest["items"][sku] for sku in ("P01", "P02", "P03")]
    contribution_ids = manifest["cost_readiness"]["contribution_line_ids"][:3]
    assert len(set(inventory_ids)) == len(contribution_ids) == 3

    for kind, scope_ids in (
        ("inventory", inventory_ids),
        ("contribution", contribution_ids),
    ):
        for scope_id in scope_ids:
            arguments = {"kind": kind, "scope_id": scope_id}
            shared = cost_query(session, run.tenant_id, **arguments)
            assert shared["freshness"]["state"] == "ready"
            assert (
                get_cost_query(
                    tenant_id=run.tenant_id,
                    session=session,
                    kind=kind,
                    scope_id=scope_id,
                )
                == shared
            )
            assert (
                run_read_tool(
                    session, run.tenant_id, "cost.query.get", arguments
                )
                == shared
            )
            assert (
                MCP_TOOL_REGISTRY["cost_query_get"].handler(
                    session, run.tenant_id, arguments
                )
                == shared
            )


def test_every_positively_stocked_demo_item_has_current_positive_acquisition_basis(
    session, scheduled_owner
):
    from reality.services.core import stock_at

    run = _seed(session, scheduled_owner, "costing-stock-readiness")
    stocked = [
        item
        for item in session.scalars(
            select(Item).where(Item.tenant_id == run.tenant_id).order_by(Item.sku)
        )
        if stock_at(session, run.tenant_id, item.id) > 0
    ]
    assert stocked
    assert run.initialization_progress["cost_readiness"]["inventory"] == {
        "expected": len(stocked),
        "current": len(stocked),
    }
    assert run.initialization_progress["cost_readiness"]["diagnostics"] == []

    unavailable = {}
    non_positive = {}
    for item in stocked:
        result = cost_query(session, run.tenant_id, kind="inventory", scope_id=item.id)
        if result["freshness"]["state"] != "ready" or result["result"] is None:
            unavailable[item.sku] = result["freshness"]["state"]
            continue
        if Decimal(result["result"]["acquisition_value"]) <= 0:
            non_positive[item.sku] = result["result"]["acquisition_value"]
    movement_summary = {
        item.sku: [
            (row.type, str(row.quantity), row.id, row.resolves_movement_id)
            for row in session.scalars(
                select(Movement)
                .where(
                    Movement.tenant_id == run.tenant_id,
                    Movement.item_id == item.id,
                )
                .order_by(Movement.occurred_at, Movement.id)
            )
        ]
        for item in stocked
        if item.sku in unavailable or item.sku in non_positive
    }
    assert not unavailable, repr(movement_summary)
    assert not non_positive, repr(non_positive)


def test_complete_case_has_exact_quantity_coverage_and_source_lineage(
    session, scheduled_owner
):
    run = _seed(session, scheduled_owner, "costing-complete")
    case = run.initialization_progress["costing_cases"]["fixture_a"]
    stock = inventory_cost(
        session,
        run.tenant_id,
        case["item_id"],
        review_id=case["inventory_review_id"],
    )
    margin = commercial_match(
        session,
        run.tenant_id,
        case["invoice_line_id"],
        match_revision_id=case["match_revision_id"],
    )
    assert stock["remaining_quantity"] == "40.0000"
    assert stock["acquisition_value"] == "420.0000"
    current_inventory = cost_query(
        session,
        run.tenant_id,
        kind="inventory",
        scope_id=case["item_id"],
    )
    assert current_inventory["freshness"]["state"] == "ready"
    assert current_inventory["result"]["remaining_quantity"] == "40.0000"
    assert current_inventory["result"]["acquisition_value"] == "420.0000"
    assert margin["stated_quantity"] == "60.0000"
    assert margin["goods_cost"] == "630.0000"
    assert margin["db1"] == "570.0000"
    assert margin["coverage"] == {
        "matched_quantity": "60.0000",
        "stated_quantity": "60.0000",
        "complete": True,
    }
    contribution = reviewed_contribution(
        session,
        run.tenant_id,
        case["invoice_line_id"],
        review_id=case["contribution_review_id"],
    )
    assert contribution["db1"] == "570.0000"
    assert contribution["direct_selling_cost"] == "90.0000"
    assert contribution["allocated_selling_cost"] == "24.0000"
    assert contribution["db2"] == "456.0000"
    assert contribution["db2_rate"] == "38.0000"
    assert contribution["missing_basis"] == []
    current = cost_query(
        session,
        run.tenant_id,
        kind="contribution",
        scope_id=case["invoice_line_id"],
    )
    assert current["freshness"]["state"] == "ready"
    assert current["result"]["db1"] == "570.0000"
    assert current["result"]["db2"] == "456.0000"
    assert (
        session.scalar(
            select(func.count())
            .select_from(SourceRecord)
            .where(
                SourceRecord.tenant_id == run.tenant_id,
                SourceRecord.source_system == "demo_profile",
                SourceRecord.external_id.like("COST-A-%"),
            )
        )
        >= 4
    )


def test_complete_portfolio_has_varied_exact_outcomes(session, scheduled_owner):
    run = _seed(session, scheduled_owner, "costing-portfolio")
    cases = run.initialization_progress["costing_cases"]
    observed = {}
    for name, expected in COMPLETE_PORTFOLIO.items():
        case = cases[name]
        assert case["reference"].startswith("COST-")
        result = reviewed_contribution(
            session,
            run.tenant_id,
            case["invoice_line_id"],
            review_id=case["contribution_review_id"],
        )
        observed[name] = {
            "revenue": result["trace"]["received_net"],
            "goods_cost": result["trace"]["consumption"]["cost"],
            "direct": result["direct_selling_cost"],
            "allocated": result["allocated_selling_cost"],
            "db1": result["db1"],
            "db2": result["db2"],
            "db2_rate": result["db2_rate"],
        }
        assert observed[name] == expected
        assert result["currency"] == "EUR"
        assert result["missing_basis"] == []
        assert result["economic_at"]
        assert result["knowledge_at"]
    assert Decimal(observed["portfolio_healthy"]["db2"]) > Decimal(
        observed["portfolio_low"]["db2"]
    )
    assert Decimal(observed["portfolio_negative"]["db2"]) < 0


def test_complete_portfolio_publishes_its_confirmed_contribution_generation(
    session, scheduled_owner
):
    run = _seed(session, scheduled_owner, "costing-generation")
    action_id = session.scalar(
        select(CostContributionReview.action_id)
        .where(CostContributionReview.tenant_id == run.tenant_id)
        .group_by(CostContributionReview.action_id)
        .having(func.count() == 6)
    )

    result = contribution_snapshot(session, run.tenant_id, action_id)

    assert result["state"] == "historical"
    assert result["coverage"] == {
        "expected_positions": 6,
        "available_positions": 6,
    }
    assert len(result["rows"]) == 6


def test_portfolio_selling_costs_reconcile_and_remain_source_backed(
    session, scheduled_owner
):
    run = _seed(session, scheduled_owner, "costing-portfolio-selling")
    cases = run.initialization_progress["costing_cases"]
    compositions = set()
    for name in COMPLETE_PORTFOLIO:
        case = cases[name]
        result = reviewed_contribution(
            session,
            run.tenant_id,
            case["invoice_line_id"],
            review_id=case["contribution_review_id"],
        )
        direct = Decimal(result["direct_selling_cost"])
        allocated = Decimal(result["allocated_selling_cost"])
        compositions.add((direct, allocated))
        assert Decimal(result["db2"]) == Decimal(result["db1"]) - direct - allocated
        assert result["trace"]["selling"]["categories"]
    assert len(compositions) >= 3
    assert (
        session.scalar(
            select(func.count())
            .select_from(SourceRecord)
            .where(
                SourceRecord.tenant_id == run.tenant_id,
                SourceRecord.source_system == "demo_profile",
                SourceRecord.external_id.like("COST-PORTFOLIO-%"),
            )
        )
        >= 12
    )


def test_late_return_case_remains_truthful(session, scheduled_owner):
    run = _seed(session, scheduled_owner, "costing-gaps")
    cases = run.initialization_progress["costing_cases"]
    late = commercial_match(
        session,
        run.tenant_id,
        cases["late_cost_return"]["credit_line_id"],
        match_revision_id=cases["late_cost_return"]["return_match_revision_id"],
    )
    assert Decimal(late["stated_quantity"]) < 0
    assert Decimal(late["goods_cost"]) < 0
    assert late["coverage"]["complete"] is True
    assert cases["late_cost_return"]["initial_state"] == "cost_incomplete"
    assert cases["late_cost_return"]["current_state"] == "late_cost_return_reviewed"
