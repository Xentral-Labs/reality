"""Bounded metadata reads over the existing source and evidence authorities."""

from typing import Any

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from reality.db.core import ImportJob, SourceRecord, SourceSystem
from reality.db.query_order import query_order
from reality.services.core import get_tenant
from reality.web.read_models import Page, page_for


def source_metadata_page(
    session: Session,
    tenant_id: str,
    view: str,
    *,
    query: str = "",
    source_system: str = "",
    page: int = 1,
    size: int = 50,
    sort: str = "",
    sort_direction: str = "asc",
) -> tuple[list[dict[str, Any]], Page]:
    get_tenant(session, tenant_id)
    if view not in {"systems", "records"}:
        raise ValueError("Unknown source register.")
    model = SourceSystem if view == "systems" else SourceRecord
    criteria = [model.tenant_id == tenant_id]
    search_columns = (
        (SourceSystem.id, SourceSystem.code, SourceSystem.name)
        if view == "systems"
        else (
            SourceRecord.id,
            SourceRecord.source_system,
            SourceRecord.source_type,
            SourceRecord.external_id,
        )
    )
    if query.strip():
        pattern = f"%{query.strip().lower()}%"
        criteria.append(
            or_(*(func.lower(column).like(pattern) for column in search_columns))
        )
    if view == "records" and source_system:
        criteria.append(SourceRecord.source_system == source_system)
    total = (
        session.scalar(select(func.count()).select_from(model).where(*criteria)) or 0
    )
    pager = page_for(total, page, size)
    if view == "systems":
        counts = (
            select(SourceRecord.source_system, func.count().label("record_count"))
            .where(SourceRecord.tenant_id == tenant_id)
            .group_by(SourceRecord.source_system)
            .subquery()
        )
        statement = (
            select(
                SourceSystem.id,
                SourceSystem.code,
                SourceSystem.name,
                SourceSystem.description,
                SourceSystem.is_active,
                func.coalesce(counts.c.record_count, 0).label("record_count"),
            )
            .outerjoin(counts, counts.c.source_system == SourceSystem.code)
            .order_by(SourceSystem.name, SourceSystem.id)
        )
    else:
        statement = (
            select(
                SourceRecord.id,
                SourceRecord.source_system,
                SourceRecord.source_type,
                SourceRecord.external_id,
                SourceRecord.version,
                SourceRecord.received_at,
                SourceRecord.supersedes_source_record_id,
                ImportJob.status.label("job_status"),
            )
            .outerjoin(
                ImportJob,
                (ImportJob.tenant_id == tenant_id)
                & (ImportJob.source_record_id == SourceRecord.id),
            )
            .order_by(SourceRecord.received_at.desc(), SourceRecord.id.desc())
        )
    rows = session.execute(
        statement.order_by(None)
        .order_by(
            *query_order(
                sort,
                sort_direction,
                {"id": model.id, "name": SourceSystem.name}
                if view == "systems"
                else {
                    "id": model.id,
                    "reference": SourceRecord.external_id,
                    "date": SourceRecord.received_at,
                    "version": SourceRecord.version,
                    "type": SourceRecord.source_type,
                },
                model.id,
                tuple(statement._order_by_clauses),
            )
        )
        .where(*criteria)
        .limit(pager.size)
        .offset(pager.offset)
    ).mappings()
    return [dict(row) for row in rows], pager
