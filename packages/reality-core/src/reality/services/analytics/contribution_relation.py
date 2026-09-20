"""Typed historical contribution population; the shared service admits and pins it."""

from typing import Any

from sqlalchemy import Date, Select, case, cast, func, literal, select
from sqlalchemy.orm import Session
from sqlalchemy.sql.selectable import Subquery

from reality.db.contribution import CostContributionReview, CostRevenueMatchBasis
from reality.db.cost_generations import (
    CostContributionGeneration,
    CostContributionSnapshot,
)
from reality.db.inventory_costing import CostInventoryMember, CostInventoryReview
from reality.domain.traversal import (
    CapturedCostContext,
    CompanyCostContext,
    ContributionCostContext,
)


def contribution_relation(tenant: str, generation_id: str) -> Select:
    """No readiness claim: callers must verify membership/hash and protect cache rows."""
    g, s, r, b, m, i = (
        model.__table__
        for model in (
            CostContributionGeneration,
            CostContributionSnapshot,
            CostContributionReview,
            CostRevenueMatchBasis,
            CostInventoryMember,
            CostInventoryReview,
        )
    )
    source = (
        g.join(s, (s.c.tenant_id == tenant) & (s.c.generation_id == g.c.id))
        .join(
            r,
            (r.c.tenant_id == tenant)
            & (r.c.id == s.c.review_id)
            & (r.c.action_id == g.c.action_id),
        )
        .join(b, (b.c.tenant_id == tenant) & (b.c.id == r.c.revenue_basis_id))
        .join(m, (m.c.tenant_id == tenant) & (m.c.id == r.c.inventory_member_id))
        .join(i, (i.c.tenant_id == tenant) & (i.c.id == m.c.review_id))
    )
    return (
        select(
            g.c.tenant_id,
            g.c.id.label("generation_id"),
            g.c.action_id.label("profile_scope_action_id"),
            s.c.id.label("snapshot_id"),
            r.c.id.label("review_id"),
            b.c.document_line_id,
            b.c.order_line_id,
            b.c.item_id,
            b.c.customer_id,
            b.c.sales_channel,
            b.c.currency,
            b.c.base_unit,
            b.c.quantity,
            i.c.policy_id.label("policy_revision_id"),
            i.c.effective_at,
            r.c.economic_at,
            cast(func.timezone("UTC", r.c.economic_at), Date).label("economic_date"),
            r.c.knowledge_at,
            b.c.stated_net.label("revenue"),
            literal("reviewed").label("revenue_state"),
            s.c.goods_cost,
            literal("reviewed").label("goods_cost_state"),
            s.c.known_direct_selling_cost,
            s.c.known_allocated_selling_cost,
            case((s.c.selling_complete, s.c.known_direct_selling_cost)).label(
                "direct_selling_cost"
            ),
            case((s.c.selling_complete, s.c.known_allocated_selling_cost)).label(
                "allocated_selling_cost"
            ),
            case((s.c.selling_complete, "reviewed"), else_="unknown").label(
                "direct_selling_cost_state"
            ),
            case((s.c.selling_complete, "reviewed"), else_="unknown").label(
                "allocated_selling_cost_state"
            ),
        )
        .select_from(source)
        .where(g.c.tenant_id == tenant, g.c.id == generation_id)
    )


CONTRIBUTION_COLUMNS = {
    column.name: column.type
    for column in contribution_relation("", "schema-only").selected_columns
}


def empty_relation(data: list[dict[str, Any]]) -> Subquery:
    """Compile-only shape, never an arbitrary populated JSON recordset."""
    if data:
        raise ValueError("Contribution reports do not accept populated recordsets")
    return contribution_relation("", "schema-only").where(False).subquery()


def report_relation(
    session: Session,
    tenant_id: str,
    context: ContributionCostContext | None,
    captured: CapturedCostContext | None = None,
    company: CompanyCostContext | None = None,
) -> tuple[Subquery, dict[str, Any]]:
    """Validate exact membership and protect observations through final SQL."""
    from reality.services.analytics.traversal import TraversalRefused
    from reality.services.contribution_generations import (
        _load,
        _resolve,
        _validate_mode,
    )

    if captured is not None:
        from reality.services.analytics.captured_relation import (
            contribution_report_relation,
        )

        return contribution_report_relation(session, tenant_id, captured.generation_id)
    if company is not None:
        from reality.services.analytics.costing_relation import (
            company_contribution_report_relation,
        )

        return company_contribution_report_relation(
            session, tenant_id, company.generation_id
        )
    if context is None:
        raise TraversalRefused(
            "A contribution cost context is required", "cost_context_required"
        )
    _validate_mode(session, context.mode)
    basis, members = _resolve(session, tenant_id, context.action_id)
    generation = _load(session, tenant_id, basis, members)
    if generation is None:
        raise TraversalRefused(
            "The complete confirmed contribution basis is unavailable",
            "cost_basis_unavailable",
        )
    return contribution_relation(tenant_id, generation.id).subquery(), {
        "kind": "contribution",
        "action_id": context.action_id,
        "generation_ids": [generation.id],
        "context": basis | {"review_ids": [member[0].id for member in members]},
        "coverage": {
            "expected_positions": len(members),
            "available_positions": len(members),
        },
        "freshness": {"state": "historical"},
    }


def _finalize_report(session: Session, tenant_id: str, basis: dict, mode: str) -> None:
    """Check after numeric SQL, so concurrent intake cannot retain a ready label."""
    from reality.services.analytics.traversal import TraversalRefused
    from reality.services.contribution_generations import _freshness

    if mode == "historical":
        return
    freshness = _freshness(
        session, tenant_id, basis["context"], mode=mode, initialized=True
    )
    if freshness["state"] == "pending":
        raise TraversalRefused(
            "New company data arrived after this confirmation; use historical mode or a newly confirmed basis",
            "cost_basis_pending",
        )
    basis["freshness"] = freshness
