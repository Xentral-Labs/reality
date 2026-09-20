"""Bounded discovery of sealed captured reports, without reading their values."""

from typing import Literal

from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session

from reality.db.captured_report import CostGeneration, CostPublication
from reality.db.cost_captured_basis import CostCapturedBasis
from reality.db.cost_census import CostCompanyCensus
from reality.services import core
from reality.services.costing import _sequence


def captured_report_options(
    session: Session,
    tenant_id: str,
    *,
    family: Literal["inventory", "contribution"],
    limit: int = 20,
    cursor: str | None = None,
) -> dict:
    """List fixed report identities; graph execution still verifies their contents."""
    if type(limit) is not int or not 1 <= limit <= 50:
        raise core.InvalidOperation(
            "Captured report selection limit must be between 1 and 50."
        )
    if family not in {"inventory", "contribution"}:
        raise core.InvalidOperation("Unsupported captured report family.")
    if cursor is not None and (
        type(cursor) is not str or not cursor.strip() or len(cursor) > 128
    ):
        raise core.InvalidOperation("Invalid captured report cursor.")
    generation, basis, census, publication = (
        CostGeneration,
        CostCapturedBasis,
        CostCompanyCensus,
        CostPublication,
    )
    statement = (
        select(
            generation.id.label("generation_id"),
            generation.captured_basis_id.label("basis_id"),
            generation.kind,
            generation.algorithm_version,
            census.effective_at,
            census.observed_at,
            census.event_sequence,
            generation.completed_at,
            generation.inventory_count,
            generation.contribution_count,
            publication.id.is_not(None).label("published"),
        )
        .join(
            basis,
            (basis.tenant_id == tenant_id) & (basis.id == generation.captured_basis_id),
        )
        .join(
            census,
            (census.tenant_id == tenant_id) & (census.id == basis.census_id),
        )
        .outerjoin(
            publication,
            (publication.tenant_id == tenant_id)
            & (publication.generation_id == generation.id),
        )
        .where(
            generation.tenant_id == tenant_id,
            generation.state == "sealed",
            getattr(generation, f"{family}_count") > 0,
        )
    )
    with session.no_autoflush:
        core.get_tenant(session, tenant_id)
        if cursor is not None:
            position = session.execute(
                select(census.event_sequence, generation.id)
                .join(
                    basis,
                    (basis.tenant_id == tenant_id)
                    & (basis.id == generation.captured_basis_id),
                )
                .join(
                    census,
                    (census.tenant_id == tenant_id) & (census.id == basis.census_id),
                )
                .where(generation.tenant_id == tenant_id, generation.id == cursor)
            ).one_or_none()
            if position is None:
                raise core.NotFound("Captured report selection not found.")
            sequence, identity = position
            statement = statement.where(
                or_(
                    census.event_sequence < sequence,
                    and_(census.event_sequence == sequence, generation.id > identity),
                )
            )
        rows = (
            session.execute(
                statement.order_by(
                    census.event_sequence.desc(), generation.id.asc()
                ).limit(limit + 1)
            )
            .mappings()
            .all()
        )
        current = _sequence(session, tenant_id)
        return {
            "items": [
                {
                    **{
                        key: value.isoformat()
                        if key in {"effective_at", "observed_at", "completed_at"}
                        else value
                        for key, value in row.items()
                    },
                    "freshness": (
                        "ready" if row["event_sequence"] == current else "pending"
                    ),
                    "financial_publication_eligible": False,
                }
                for row in rows[:limit]
            ],
            "next_cursor": (
                rows[limit - 1]["generation_id"] if len(rows) > limit else None
            ),
        }
