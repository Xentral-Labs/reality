"""Typed graph relations over one verified captured report generation."""

from sqlalchemy import Date, String, case, cast, literal, select
from sqlalchemy.orm import Session

from reality.db.captured_report import (
    CostContributionRow,
    CostGeneration,
    CostInventoryRow,
)
from reality.db.cost_captured_basis import (
    CostCapturedBasis,
    CostCapturedContributionBasis,
    CostCapturedInventoryBasis,
)
from reality.db.cost_census import CostCompanyCensus


def _metadata(session: Session, tenant_id: str, generation_id: str) -> dict:
    from reality.services import captured_report

    header, _ = captured_report._verified(session, tenant_id, generation_id)
    return {
        **captured_report._metadata(header),
        "context": {
            "effective_at": header["effective_at"].isoformat(),
            "observed_at": header["observed_at"].isoformat(),
            "event_sequence": header["event_sequence"],
        },
        "coverage": {
            "inventory_required": header["inventory_count"],
            "contribution_required": header["contribution_count"],
        },
        "freshness": {"state": "captured"},
    }


def _header_source(tenant_id: str, generation_id: str):
    generation = CostGeneration.__table__
    basis = CostCapturedBasis.__table__
    census = CostCompanyCensus.__table__
    return (
        generation.join(
            basis,
            (basis.c.tenant_id == tenant_id)
            & (basis.c.id == generation.c.captured_basis_id),
        ).join(
            census,
            (census.c.tenant_id == tenant_id) & (census.c.id == basis.c.census_id),
        ),
        generation,
        basis,
        census,
    )


def inventory_report_relation(session: Session, tenant_id: str, generation_id: str):
    """Expose cached inventory rows while retaining unknown members as coverage."""
    metadata = _metadata(session, tenant_id, generation_id)
    source, generation, _, census = _header_source(tenant_id, generation_id)
    row = CostInventoryRow.__table__
    member = CostCapturedInventoryBasis.__table__
    source = source.join(
        row,
        (row.c.tenant_id == tenant_id) & (row.c.generation_id == generation.c.id),
    ).join(
        member,
        (member.c.tenant_id == tenant_id)
        & (member.c.id == row.c.inventory_basis_member_id)
        & (member.c.basis_id == generation.c.captured_basis_id),
    )
    relation = (
        select(
            generation.c.tenant_id,
            row.c.id.label("snapshot_id"),
            generation.c.id.label("generation_id"),
            member.c.review_id,
            member.c.item_id,
            row.c.owner_party_id,
            row.c.currency,
            row.c.base_unit,
            row.c.method,
            census.c.effective_at,
            census.c.observed_at.label("knowledge_at"),
            census.c.event_sequence.label("processed_event_sequence"),
            generation.c.algorithm_version,
            generation.c.completed_at,
            row.c.remaining_quantity,
            row.c.acquisition_value,
            row.c.carrying_value,
        )
        .select_from(source)
        .where(
            generation.c.tenant_id == tenant_id,
            generation.c.id == generation_id,
        )
        .subquery()
    )
    return relation, metadata


def contribution_report_relation(session: Session, tenant_id: str, generation_id: str):
    """Expose cached commercial inputs to the one canonical DB aggregate."""
    metadata = _metadata(session, tenant_id, generation_id)
    source, generation, _, census = _header_source(tenant_id, generation_id)
    row = CostContributionRow.__table__
    member = CostCapturedContributionBasis.__table__
    source = source.join(
        row,
        (row.c.tenant_id == tenant_id) & (row.c.generation_id == generation.c.id),
    ).join(
        member,
        (member.c.tenant_id == tenant_id)
        & (member.c.id == row.c.contribution_basis_member_id)
        & (member.c.basis_id == generation.c.captured_basis_id),
    )
    reviewed = row.c.state == "available_at_capture"
    selling = (
        reviewed
        & row.c.direct_selling_cost.is_not(None)
        & row.c.allocated_selling_cost.is_not(None)
    )
    relation = (
        select(
            generation.c.tenant_id,
            row.c.id.label("snapshot_id"),
            generation.c.id.label("generation_id"),
            member.c.review_id,
            member.c.document_line_id,
            cast(literal(None), String).label("order_line_id"),
            cast(literal(None), String).label("item_id"),
            cast(literal(None), String).label("customer_id"),
            cast(literal(None), String).label("sales_channel"),
            row.c.currency,
            row.c.base_unit,
            census.c.effective_at,
            census.c.effective_at.label("economic_at"),
            cast(census.c.effective_at, Date).label("economic_date"),
            census.c.observed_at.label("knowledge_at"),
            row.c.revenue,
            case((reviewed, "reviewed"), else_="unknown").label("revenue_state"),
            row.c.goods_cost,
            case((reviewed, "reviewed"), else_="unknown").label("goods_cost_state"),
            row.c.direct_selling_cost,
            row.c.allocated_selling_cost,
            case((selling, "reviewed"), else_="unknown").label(
                "direct_selling_cost_state"
            ),
            case((selling, "reviewed"), else_="unknown").label(
                "allocated_selling_cost_state"
            ),
        )
        .select_from(source)
        .where(
            generation.c.tenant_id == tenant_id,
            generation.c.id == generation_id,
        )
        .subquery()
    )
    return relation, metadata
