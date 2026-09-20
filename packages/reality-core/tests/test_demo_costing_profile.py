"""FR-026: the canonical baseline owns bounded, source-backed costing stories."""

from decimal import Decimal

import pytest
from conftest import seed_company
from sqlalchemy import func, select

from reality.db.contribution import CostCommercialMatchRevision
from reality.db.core import PlaygroundRun, SourceRecord
from reality.db.inventory_costing import CostInventoryReview
from reality.demo.international import PROFILE_VERSION
from reality.services import company_setup
from reality.services.costing import (
    commercial_match,
    cost_query,
    inventory_cost,
    reviewed_contribution,
)
from reality.services.tenant_policy import (
    PlaygroundOperationDenied,
    profile_cost_action_scope,
)


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
    run = session.get(PlaygroundRun, result["run_id"])
    assert run.status == "active", (run.initialization_error_code, run.initialization_progress)
    return run


def test_canonical_profile_versions_and_replays_one_costing_baseline(
    session, scheduled_owner
):
    run = _seed(session, scheduled_owner)
    manifest = run.initialization_progress
    assert PROFILE_VERSION == 2
    assert manifest["profile"] == {"key": "international_demo", "version": 2}
    assert set(manifest["costing_cases"]) == {
        "fixture_a",
        "missing_cost",
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
    )

    with pytest.raises(PlaygroundOperationDenied), profile_cost_action_scope(
        session,
        run.id,
        scheduled_owner.id,
        {"operation": "inventory_review"},
    ):
        pass


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


def test_missing_and_late_return_cases_remain_truthful(session, scheduled_owner):
    run = _seed(session, scheduled_owner, "costing-gaps")
    cases = run.initialization_progress["costing_cases"]
    missing = commercial_match(
        session, run.tenant_id, cases["missing_cost"]["invoice_line_id"]
    )
    assert missing["db1"] is None
    assert "commercial_match_not_reviewed" in missing["missing_basis"]
    assert cases["missing_cost"]["quantity"] == "5"

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
