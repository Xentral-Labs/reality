"""Acceptance proofs for cost findings over one pinned company generation."""

from decimal import Decimal

import test_company_generation_jobs as jobs

from reality.services import exceptions

company_database = jobs.company_database

READY = {
    "state": "ready",
    "generation_id": "generation-current",
    "manifest_id": "manifest-current",
}


def derive(*, basis=READY, inventory=(), components=(), contributions=(), previous=()):
    """Exercise the future internal derivation seam without database recomputation."""
    return exceptions._derive_cost_findings(
        tenant_id="tenant-a",
        basis=basis,
        inventory_rows=inventory,
        component_rows=components,
        contribution_rows=contributions,
        previous_rows=previous,
    )


def by_class(rows):
    return {row.class_id: row for row in rows}


def test_missing_acquisition_cost_includes_unsold_inventory_subject():
    rows = derive(
        inventory=(
            {
                "tenant_id": "tenant-a",
                "item_id": "item-unsold",
                "support_state": "unknown",
                "review_id": None,
                "has_sale": False,
            },
        )
    )

    finding = by_class(rows)["missing_acquisition_cost"]
    assert finding.record_type == "item"
    assert finding.record_id == "item-unsold"
    assert finding.causal_values["has_sale"] is False
    assert finding.trace["generation_id"] == "generation-current"


def test_unassigned_component_uses_existing_document_line_subject():
    rows = derive(
        components=(
            {
                "tenant_id": "tenant-a",
                "component_id": "component-1",
                "document_line_id": "line-cost",
                "assignment_state": "unassigned",
            },
        )
    )

    finding = by_class(rows)["unassigned_cost_component"]
    assert finding.record_type == "document_line"
    assert finding.record_id == "line-cost"
    assert finding.trace["component_id"] == "component-1"


def test_stale_review_identity_is_stable_across_generations():
    row = {
        "tenant_id": "tenant-a",
        "item_id": "item-reviewed",
        "support_state": "known",
        "review_id": "review-1",
        "review_state": "stale",
    }
    first = by_class(derive(inventory=(row,)))["stale_cost_review"]
    second = by_class(
        derive(basis={**READY, "generation_id": "generation-next"}, inventory=(row,))
    )["stale_cost_review"]

    assert first.id == second.id
    assert first.trace["generation_id"] != second.trace["generation_id"]
    assert first.trace["review_id"] == "review-1"


def test_negative_actual_db1_requires_complete_supported_db1_not_db2():
    rows = derive(
        contributions=(
            {
                "tenant_id": "tenant-a",
                "document_line_id": "line-loss",
                "db1_state": "known",
                "db2_state": "unknown",
                "revenue": Decimal("50.0000"),
                "goods_cost": Decimal("60.0000"),
                "review_id": "contribution-review",
            },
        )
    )

    finding = by_class(rows)["negative_actual_db1"]
    assert finding.record_type == "document_line"
    assert finding.record_id == "line-loss"
    assert finding.causal_values["db1"] == Decimal("-10.0000")


def test_incomplete_db1_refuses_negative_margin_and_reports_cost_gap():
    rows = derive(
        contributions=(
            {
                "tenant_id": "tenant-a",
                "document_line_id": "line-unknown",
                "db1_state": "unknown",
                "db2_state": "unknown",
                "revenue": Decimal("50.0000"),
                "goods_cost": None,
                "review_id": None,
            },
        )
    )

    assert "negative_actual_db1" not in by_class(rows)
    assert "missing_acquisition_cost" in by_class(rows)


def test_evaluated_current_empty_scope_clears_previous_finding():
    previous = derive(
        inventory=(
            {
                "tenant_id": "tenant-a",
                "item_id": "item-cleared",
                "support_state": "unknown",
                "review_id": None,
                "has_sale": False,
            },
        )
    )

    assert derive(previous=previous) == []


def test_pending_basis_preserves_previous_findings_as_stale():
    previous = derive(
        inventory=(
            {
                "tenant_id": "tenant-a",
                "item_id": "item-pending",
                "support_state": "unknown",
                "review_id": None,
                "has_sale": False,
            },
        )
    )
    pending = derive(
        basis={**READY, "state": "pending", "target_event_sequence": 12},
        previous=previous,
    )

    assert [row.id for row in pending] == [row.id for row in previous]
    assert pending[0].trace["cost_basis_state"] == "pending"
    assert pending[0].trace["generation_id"] == "generation-current"


def test_foreign_input_rows_are_not_disclosed():
    rows = derive(
        inventory=(
            {
                "tenant_id": "tenant-b",
                "item_id": "foreign-item",
                "support_state": "unknown",
                "review_id": None,
                "has_sale": False,
            },
        ),
        components=(
            {
                "tenant_id": "tenant-b",
                "component_id": "foreign-component",
                "document_line_id": "foreign-line",
                "assignment_state": "unassigned",
            },
        ),
    )

    assert rows == []


def test_provider_reads_verified_known_company_generation(company_database):
    factory, tenant, manifest = jobs._manifest(company_database)
    with factory() as session:
        built = jobs.costing.build_company_cost_generation(
            session, tenant, manifest["id"]
        )
        jobs.costing.publish_company_cost_generation(
            session, tenant, built["generation_id"], previous_generation_id=None
        )
        session.commit()
    with factory() as session:
        rows = exceptions.cost_findings(session, tenant)

    assert rows == []


def test_provider_reports_unknown_population_and_preserves_it_while_pending(
    company_database,
):
    factory, tenant, manifest = jobs._manifest(company_database, reviewed=False)
    with factory() as session:
        built = jobs.costing.build_company_cost_generation(
            session, tenant, manifest["id"]
        )
        jobs.costing.publish_company_cost_generation(
            session, tenant, built["generation_id"], previous_generation_id=None
        )
        session.commit()
    with factory() as session:
        current = exceptions.cost_findings(session, tenant)
        jobs.core.emit_business_event(
            session, tenant, "test.later", "tenant", tenant, {}
        )
        session.commit()
    assert {row.record_type for row in current} == {"item", "document_line"}
    assert {row.class_id for row in current} == {"missing_acquisition_cost"}
    with factory() as session:
        pending = exceptions.cost_findings(
            session, tenant, previous_rows=tuple(current)
        )
    assert [row.id for row in pending] == [row.id for row in current]
    assert all(row.trace["cost_basis_state"] == "pending" for row in pending)
