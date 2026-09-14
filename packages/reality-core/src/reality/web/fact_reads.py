"""Scoped recorded-observation register; no current-value or validity derivation."""

from typing import Any

from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session

from reality.db.core import Fact, InterpretationRule, SourceRecord
from reality.db.query_order import query_order
from reality.web.read_models import page_for


def fact_page(
    session: Session,
    tenant_id: str,
    *,
    query: str = "",
    subject_type: str = "",
    subject_id: str = "",
    source_record_id: str = "",
    page: int = 1,
    size: int = 50,
    sort: str = "",
    sort_direction: str = "asc",
) -> dict[str, Any]:
    statement = (
        select(
            Fact.id,
            Fact.subject_type,
            Fact.subject_id,
            Fact.predicate,
            Fact.value,
            Fact.observed_at,
            Fact.source_record_id,
            Fact.interpretation_rule_id,
            SourceRecord.id.label("source_id"),
            SourceRecord.source_system,
            SourceRecord.source_type,
            SourceRecord.external_id,
            SourceRecord.version.label("source_version"),
            InterpretationRule.id.label("rule_id"),
            InterpretationRule.logical_name,
            InterpretationRule.version.label("rule_version"),
        )
        .outerjoin(
            SourceRecord,
            and_(
                SourceRecord.tenant_id == Fact.tenant_id,
                SourceRecord.id == Fact.source_record_id,
            ),
        )
        .outerjoin(
            InterpretationRule,
            and_(
                InterpretationRule.tenant_id == Fact.tenant_id,
                InterpretationRule.id == Fact.interpretation_rule_id,
            ),
        )
        .where(Fact.tenant_id == tenant_id)
    )
    if query.strip():
        pattern = f"%{query.strip()}%"
        statement = statement.where(
            or_(
                *(
                    column.ilike(pattern)
                    for column in (
                        Fact.id,
                        Fact.predicate,
                        Fact.subject_type,
                        Fact.subject_id,
                        Fact.value,
                        SourceRecord.source_system,
                        SourceRecord.source_type,
                        SourceRecord.external_id,
                    )
                )
            )
        )
    for column, value in (
        (Fact.subject_type, subject_type),
        (Fact.subject_id, subject_id),
        (Fact.source_record_id, source_record_id),
    ):
        if value:
            statement = statement.where(column == value)
    total = int(
        session.scalar(select(func.count()).select_from(statement.subquery())) or 0
    )
    pager = page_for(total, page, size)
    rows = (
        session.execute(
            statement.order_by(
                *query_order(
                    sort,
                    sort_direction,
                    {
                        "id": Fact.id,
                        "predicate": Fact.predicate,
                        "value": Fact.value,
                        "subject_type": Fact.subject_type,
                        "observed_at": Fact.observed_at,
                    },
                    Fact.id,
                    (
                        Fact.observed_at.desc(),
                        Fact.id.desc(),
                    ),
                )
            )
            .offset(pager.offset)
            .limit(pager.size)
        )
        .mappings()
        .all()
    )
    subject_types = list(
        session.scalars(
            select(Fact.subject_type)
            .where(Fact.tenant_id == tenant_id)
            .distinct()
            .order_by(Fact.subject_type)
            .limit(101)
        )
    )
    return {
        "items": [
            {
                "id": row.id,
                "subject_type": row.subject_type,
                "subject_id": row.subject_id,
                "predicate": row.predicate,
                "value": row.value,
                "observed_at": row.observed_at,
                "source_record_id": row.source_record_id,
                "source_version": row.source_version,
                "interpretation_rule_id": row.interpretation_rule_id,
                "source": {
                    "system": row.source_system,
                    "type": row.source_type,
                    "external_id": row.external_id,
                }
                if row.source_id
                else None,
                "interpretation_rule": {
                    "id": row.rule_id,
                    "logical_name": row.logical_name,
                    "version": row.rule_version,
                }
                if row.rule_id
                else None,
            }
            for row in rows
        ],
        "page": {
            "number": pager.number,
            "size": pager.size,
            "total": pager.total,
            "pages": pager.pages,
            "has_previous": pager.has_previous,
            "has_next": pager.has_next,
        },
        "subject_types": subject_types[:100],
        "subject_types_has_more": len(subject_types) > 100,
    }
