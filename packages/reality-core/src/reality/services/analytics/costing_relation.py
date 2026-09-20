"""Canonical inventory observation at an explicitly pinned tenant/generation."""

from datetime import datetime
from typing import Any

from sqlalchemy import Date, Join, Select, case, cast, func, literal, select
from sqlalchemy.orm import Session
from sqlalchemy.sql.selectable import Subquery

from reality.db.company_generations import (
    CostCompanyContributionInput,
    CostCompanyContributionResult,
    CostCompanyGeneration,
    CostCompanyInventoryInput,
    CostCompanyInventoryResult,
    CostCompanyManifest,
    CostCompanyPublication,
)
from reality.db.contribution import CostContributionReview, CostRevenueMatchBasis
from reality.db.core import BusinessEvent
from reality.db.cost_census import CostCompanyCensusLine
from reality.db.cost_generations import (
    CostContributionSnapshot,
    CostInventoryGeneration,
    CostInventorySnapshot,
)
from reality.db.inventory_costing import CostInventoryReview, CostPolicyRevision
from reality.domain.traversal import (
    CapturedCostContext,
    CompanyCostContext,
    InventoryCostContext,
)


def _company_graph_metadata(report: dict[str, Any], family: str) -> dict[str, Any]:
    resolved = report["resolved"]
    if family == "inventory":
        coverage = {
            "expected_items": report["coverage"]["inventory"]["expected"],
            "available_items": report["coverage"]["inventory"]["known"],
        }
    else:
        coverage = {
            "expected_positions": report["coverage"]["contribution"]["expected"],
            "available_positions": report["coverage"]["contribution"]["db1_known"],
            "db2_available_positions": report["coverage"]["contribution"]["db2_known"],
        }
    return {
        "kind": "financial_company_generation",
        "generation_id": report["generation_id"],
        "manifest_id": resolved["manifest_id"],
        "scope_key": resolved["scope_key"],
        "authority_scope": resolved["authority_scope"],
        "context_id": report["context_id"],
        "requested": report["requested"],
        "resolved": resolved,
        "context": {
            "effective_at": resolved["effective_at"],
            "knowledge_at": resolved["knowledge_at"],
            "event_sequence": resolved["event_sequence"],
            "inventory_algorithm_version": resolved["inventory_algorithm_version"],
            "contribution_algorithm_version": resolved[
                "contribution_algorithm_version"
            ],
        },
        "coverage": coverage,
        "freshness": report["freshness_context"],
        "freshness_context": report["freshness_context"],
    }


def inventory_relation(tenant_id: str, generation_id: str) -> Select:
    """Never resolve a mutable publication pointer inside the numeric relation."""
    return select(
        CostInventorySnapshot.remaining_quantity,
        CostInventorySnapshot.acquisition_value,
        CostInventorySnapshot.carrying_value,
    ).where(
        CostInventorySnapshot.tenant_id == tenant_id,
        CostInventorySnapshot.generation_id == generation_id,
    )


def company_inventory_relation(tenant_id: str, generation_id: str) -> Select:
    """One fixed company generation joined to its verified inventory caches."""
    return (
        select(
            CostCompanyInventoryResult.tenant_id,
            CostCompanyInventoryInput.id.label("input_id"),
            CostCompanyInventoryInput.item_id,
            CostCompanyInventoryInput.review_id,
            CostCompanyInventoryInput.input_fingerprint,
            CostCompanyInventoryResult.state,
            CostCompanyInventoryResult.inventory_generation_id,
            CostInventorySnapshot.remaining_quantity,
            CostInventorySnapshot.acquisition_value,
            CostInventorySnapshot.carrying_value,
        )
        .select_from(CostCompanyInventoryResult)
        .join(
            CostCompanyInventoryInput,
            (CostCompanyInventoryInput.tenant_id == tenant_id)
            & (
                CostCompanyInventoryInput.id
                == CostCompanyInventoryResult.inventory_input_id
            ),
        )
        .outerjoin(
            CostInventorySnapshot,
            (CostInventorySnapshot.tenant_id == tenant_id)
            & (
                CostInventorySnapshot.generation_id
                == CostCompanyInventoryResult.inventory_generation_id
            ),
        )
        .where(
            CostCompanyInventoryResult.tenant_id == tenant_id,
            CostCompanyInventoryResult.generation_id == generation_id,
        )
    )


def company_contribution_relation(tenant_id: str, generation_id: str) -> Select:
    """One fixed company generation joined to its exact contribution review rows."""
    return (
        select(
            CostCompanyContributionResult.tenant_id,
            CostCompanyContributionInput.id.label("input_id"),
            CostCompanyCensusLine.document_line_id,
            CostCompanyContributionResult.review_id,
            CostCompanyContributionInput.input_fingerprint,
            CostCompanyContributionResult.db1_state,
            CostCompanyContributionResult.db2_state,
            CostCompanyContributionResult.contribution_generation_id,
            CostRevenueMatchBasis.stated_net.label("revenue"),
            CostRevenueMatchBasis.order_line_id,
            CostRevenueMatchBasis.item_id,
            CostRevenueMatchBasis.customer_id,
            CostRevenueMatchBasis.sales_channel,
            CostRevenueMatchBasis.currency,
            CostRevenueMatchBasis.base_unit,
            CostContributionReview.economic_at,
            CostContributionReview.knowledge_at,
            CostContributionSnapshot.goods_cost,
            CostContributionSnapshot.known_direct_selling_cost,
            CostContributionSnapshot.known_allocated_selling_cost,
        )
        .select_from(CostCompanyContributionResult)
        .join(
            CostCompanyContributionInput,
            (CostCompanyContributionInput.tenant_id == tenant_id)
            & (
                CostCompanyContributionInput.id
                == CostCompanyContributionResult.contribution_input_id
            ),
        )
        .join(
            CostCompanyCensusLine,
            (CostCompanyCensusLine.tenant_id == tenant_id)
            & (CostCompanyCensusLine.id == CostCompanyContributionInput.census_line_id),
        )
        .outerjoin(
            CostContributionSnapshot,
            (CostContributionSnapshot.tenant_id == tenant_id)
            & (
                CostContributionSnapshot.generation_id
                == CostCompanyContributionResult.contribution_generation_id
            )
            & (
                CostContributionSnapshot.review_id
                == CostCompanyContributionResult.review_id
            ),
        )
        .outerjoin(
            CostContributionReview,
            (CostContributionReview.tenant_id == tenant_id)
            & (CostContributionReview.id == CostCompanyContributionResult.review_id),
        )
        .outerjoin(
            CostRevenueMatchBasis,
            (CostRevenueMatchBasis.tenant_id == tenant_id)
            & (CostRevenueMatchBasis.id == CostContributionReview.revenue_basis_id),
        )
        .where(
            CostCompanyContributionResult.tenant_id == tenant_id,
            CostCompanyContributionResult.generation_id == generation_id,
        )
    )


def company_inventory_report_relation(
    session: Session, tenant_id: str, generation_id: str
) -> tuple[Subquery, dict[str, Any]]:
    """Expose one verified fixed company inventory generation to graph SQL."""
    from reality.services import company_generations

    report = company_generations._report(session, tenant_id, generation_id, page_size=1)
    metadata = _company_graph_metadata(report, "inventory")
    source = company_inventory_relation(tenant_id, generation_id).subquery()
    review = CostInventoryReview.__table__
    policy = CostPolicyRevision.__table__
    relation = (
        select(
            source.c.tenant_id,
            source.c.input_id.label("snapshot_id"),
            literal(generation_id).label("generation_id"),
            source.c.review_id,
            source.c.item_id,
            policy.c.owner_party_id,
            policy.c.currency,
            policy.c.base_unit,
            policy.c.method,
            literal(datetime.fromisoformat(metadata["resolved"]["effective_at"])).label(
                "effective_at"
            ),
            literal(datetime.fromisoformat(metadata["resolved"]["knowledge_at"])).label(
                "knowledge_at"
            ),
            literal(metadata["resolved"]["event_sequence"]).label(
                "processed_event_sequence"
            ),
            literal(metadata["resolved"]["inventory_algorithm_version"]).label(
                "algorithm_version"
            ),
            source.c.remaining_quantity,
            source.c.acquisition_value,
        )
        .select_from(source)
        .outerjoin(
            review,
            (review.c.tenant_id == tenant_id) & (review.c.id == source.c.review_id),
        )
        .outerjoin(
            policy,
            (policy.c.tenant_id == tenant_id) & (policy.c.id == review.c.policy_id),
        )
        .subquery()
    )
    return relation, metadata


def company_contribution_report_relation(
    session: Session, tenant_id: str, generation_id: str
) -> tuple[Subquery, dict[str, Any]]:
    """Expose one verified fixed company commercial generation to graph SQL."""
    from reality.services import company_generations

    report = company_generations._report(session, tenant_id, generation_id, page_size=1)
    metadata = _company_graph_metadata(report, "contribution")
    source = company_contribution_relation(tenant_id, generation_id).subquery()
    db1_known = source.c.db1_state == "known"
    db2_known = source.c.db2_state == "known"
    relation = select(
        source.c.tenant_id,
        source.c.input_id.label("snapshot_id"),
        literal(generation_id).label("generation_id"),
        source.c.review_id,
        source.c.document_line_id,
        source.c.order_line_id,
        source.c.item_id,
        source.c.customer_id,
        source.c.sales_channel,
        source.c.currency,
        source.c.base_unit,
        literal(datetime.fromisoformat(metadata["resolved"]["effective_at"])).label(
            "effective_at"
        ),
        source.c.economic_at,
        cast(source.c.economic_at, Date).label("economic_date"),
        source.c.knowledge_at,
        source.c.revenue,
        case((db1_known, "reviewed"), else_="unknown").label("revenue_state"),
        source.c.goods_cost,
        case((db1_known, "reviewed"), else_="unknown").label("goods_cost_state"),
        case((db2_known, source.c.known_direct_selling_cost)).label(
            "direct_selling_cost"
        ),
        case((db2_known, source.c.known_allocated_selling_cost)).label(
            "allocated_selling_cost"
        ),
        case((db2_known, "reviewed"), else_="unknown").label(
            "direct_selling_cost_state"
        ),
        case((db2_known, "reviewed"), else_="unknown").label(
            "allocated_selling_cost_state"
        ),
    ).subquery()
    return relation, metadata


def company_generation_basis(
    session: Session, tenant_id: str, *, protect: bool = False
) -> dict[str, Any]:
    """Verify and pin the newest published company basis for future cost findings."""
    from reality.services.company_generations import _verify_generation

    statement = (
        select(CostCompanyPublication, CostCompanyGeneration, CostCompanyManifest)
        .join(
            CostCompanyGeneration,
            (CostCompanyGeneration.tenant_id == tenant_id)
            & (CostCompanyGeneration.id == CostCompanyPublication.generation_id),
        )
        .join(
            CostCompanyManifest,
            (CostCompanyManifest.tenant_id == tenant_id)
            & (CostCompanyManifest.id == CostCompanyGeneration.manifest_id),
        )
        .where(
            CostCompanyPublication.tenant_id == tenant_id,
            CostCompanyGeneration.state == "sealed",
            CostCompanyManifest.state == "sealed",
        )
        .order_by(
            CostCompanyManifest.target_event_sequence.desc(),
            CostCompanyManifest.effective_at.desc(),
            CostCompanyGeneration.id.desc(),
        )
        .limit(1)
    )
    if protect:
        statement = statement.with_for_update(read=True, of=CostCompanyPublication)
    with session.no_autoflush:
        row = session.execute(statement).first()
        if row is None:
            return {
                "state": "unavailable",
                "generation_id": None,
                "manifest_id": None,
                "scope_key": None,
                "processed_event_sequence": None,
                "target_event_sequence": int(
                    session.scalar(
                        select(func.max(BusinessEvent.sequence)).where(
                            BusinessEvent.tenant_id == tenant_id
                        )
                    )
                    or 0
                ),
            }
        _, generation, manifest = row
        _verify_generation(session, tenant_id, generation)
        target = int(
            session.scalar(
                select(func.max(BusinessEvent.sequence)).where(
                    BusinessEvent.tenant_id == tenant_id
                )
            )
            or 0
        )
        if target < manifest.target_event_sequence:
            from reality.services import core

            raise core.InvalidOperation("Company cost event cursor is invalid.")
        return {
            "state": (
                "ready" if target == manifest.target_event_sequence else "pending"
            ),
            "generation_id": generation.id,
            "manifest_id": manifest.id,
            "scope_key": generation.scope_key,
            "effective_at": manifest.effective_at.isoformat(),
            "knowledge_at": manifest.knowledge_at.isoformat(),
            "processed_event_sequence": manifest.target_event_sequence,
            "target_event_sequence": target,
        }


def selection_ids(generation_ids: list[str] | tuple[str, ...]) -> tuple[str, ...]:
    """Freeze a bounded exact selection before any database access."""
    from reality.services import core

    if (
        not isinstance(generation_ids, (list, tuple))
        or not 1 <= len(generation_ids) <= 100
        or any(type(value) is not str or not value.strip() for value in generation_ids)
        or len(set(generation_ids)) != len(generation_ids)
    ):
        raise core.InvalidOperation(
            "Inventory selection requires 1–100 distinct nonempty generation IDs."
        )
    return tuple(sorted(generation_ids))


def inventory_selection_source(
    tenant_id: str, generation_ids: list[str] | tuple[str, ...]
) -> Join:
    """One tenant-constrained source shared by inspection and reporting SQL.

    Completeness, checksum verification and report-context admission belong to the
    shared service. Missing members simply do not join; absence is never zero.
    """
    selected = selection_ids(generation_ids)
    generation = CostInventoryGeneration.__table__
    review = CostInventoryReview.__table__
    policy = CostPolicyRevision.__table__
    snapshot = CostInventorySnapshot.__table__
    return (
        generation.join(
            review,
            (generation.c.tenant_id == tenant_id)
            & generation.c.id.in_(selected)
            & (review.c.tenant_id == tenant_id)
            & (review.c.id == generation.c.review_id),
        )
        .join(
            policy,
            (policy.c.tenant_id == tenant_id) & (policy.c.id == review.c.policy_id),
        )
        .join(
            snapshot,
            (snapshot.c.tenant_id == tenant_id)
            & (snapshot.c.generation_id == generation.c.id),
        )
    )


def inventory_selection_relation(
    tenant_id: str, generation_ids: list[str] | tuple[str, ...]
) -> Select:
    """Typed observations at snapshot grain, pinned without following publication.

    This is an internal SQL building block, not an authorized report. Consumers
    must admit one complete compatible basis and protect it through aggregation.
    Do not SUM values across cutoffs or quantities across different base units.
    """
    return select(
        CostInventoryGeneration.tenant_id.label("tenant_id"),
        CostInventorySnapshot.id.label("snapshot_id"),
        CostInventoryGeneration.id.label("generation_id"),
        CostInventoryReview.id.label("review_id"),
        CostInventoryReview.action_id.label("review_action_id"),
        CostPolicyRevision.id.label("policy_revision_id"),
        CostPolicyRevision.item_id.label("item_id"),
        CostPolicyRevision.owner_party_id.label("owner_party_id"),
        CostPolicyRevision.currency.label("currency"),
        CostPolicyRevision.base_unit.label("base_unit"),
        CostPolicyRevision.method.label("method"),
        CostInventoryReview.effective_at.label("effective_at"),
        CostInventoryReview.knowledge_at.label("knowledge_at"),
        CostInventoryReview.target_event_sequence.label("processed_event_sequence"),
        CostInventoryGeneration.algorithm_version.label("algorithm_version"),
        CostInventoryGeneration.completed_at.label("completed_at"),
        CostInventorySnapshot.remaining_quantity.label("remaining_quantity"),
        CostInventorySnapshot.acquisition_value.label("acquisition_value"),
    ).select_from(inventory_selection_source(tenant_id, generation_ids))


# Metadata comes from the executable SQL relation, not a second column definition.
INVENTORY_COLUMNS = {
    column.name: column.type
    for column in inventory_selection_relation("", ["schema-only"]).selected_columns
}


def empty_relation(data: list[dict[str, Any]]) -> Subquery:
    """Compile-only shape for interpretation validation; no arbitrary row injection."""
    if data:
        raise ValueError("Inventory reports do not accept populated recordsets")
    return inventory_selection_relation("", ["schema-only"]).where(False).subquery()


def report_relation(
    session: Session,
    tenant_id: str,
    context: InventoryCostContext | None,
    captured: CapturedCostContext | None = None,
    company: CompanyCostContext | None = None,
) -> tuple[Subquery, dict[str, Any]]:
    """Admit and lock the complete basis before exposing it to the SQL compiler."""
    from reality.services.analytics.traversal import TraversalRefused
    from reality.services.inventory_batch_generations import _read

    if captured is not None:
        from reality.services.analytics.captured_relation import (
            inventory_report_relation,
        )

        return inventory_report_relation(session, tenant_id, captured.generation_id)
    if company is not None:
        return company_inventory_report_relation(
            session, tenant_id, company.generation_id
        )
    if context is None:
        raise TraversalRefused(
            "An inventory cost context is required", "cost_context_required"
        )
    basis = _read(session, tenant_id, context.action_id, _protect=True)
    if basis["result"] is None:
        raise TraversalRefused(
            "The complete confirmed inventory basis is unavailable",
            "cost_basis_unavailable",
        )
    metadata = {
        key: basis[key]
        for key in ("action_id", "generation_ids", "context", "coverage", "freshness")
    }
    return inventory_selection_relation(
        tenant_id, basis["generation_ids"]
    ).subquery(), metadata
