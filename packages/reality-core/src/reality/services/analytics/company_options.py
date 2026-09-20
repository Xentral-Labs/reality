"""Read the verified published company generation for explicit graph selection."""

from typing import Literal

from sqlalchemy import select
from sqlalchemy.orm import Session

from reality.db.company_generations import CostCompanyGeneration, CostCompanyManifest
from reality.services.analytics.costing_relation import company_generation_basis


def company_generation_option(
    session: Session,
    tenant_id: str,
    *,
    family: Literal["inventory", "contribution"],
) -> dict:
    """Return metadata only; values remain behind graph execution verification."""
    with session.no_autoflush:
        basis = company_generation_basis(session, tenant_id)
        if basis["generation_id"] is None:
            return {"item": None}
        generation, manifest = session.execute(
            select(CostCompanyGeneration, CostCompanyManifest)
            .join(
                CostCompanyManifest,
                (CostCompanyManifest.tenant_id == tenant_id)
                & (CostCompanyManifest.id == CostCompanyGeneration.manifest_id),
            )
            .where(
                CostCompanyGeneration.tenant_id == tenant_id,
                CostCompanyGeneration.id == basis["generation_id"],
            )
        ).one()
        count = (
            generation.inventory_count
            if family == "inventory"
            else generation.contribution_count
        )
        return {
            "item": {
                **basis,
                "family": family,
                "subject_count": count,
                "completed_at": generation.completed_at.isoformat(),
                "effective_at": manifest.effective_at.isoformat(),
                "knowledge_at": manifest.knowledge_at.isoformat(),
                "authority_scope": "independent_member_reviews",
            }
        }
