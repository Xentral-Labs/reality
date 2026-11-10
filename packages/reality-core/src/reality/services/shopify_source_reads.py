"""Shared exact Shopify identity reads on current and schema99 stable records."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from reality.db.core import Document, SourceRecord


def accepted_order_exists(
    session: Session, tenant_id: str, source: SourceRecord
) -> str | None:
    """Same external Shopify identity cannot enter first-order intake twice."""
    if source.tenant_id != tenant_id:
        return None
    return session.scalar(
        select(Document.id)
        .join(SourceRecord, Document.source_record_id == SourceRecord.id)
        .where(
            Document.tenant_id == tenant_id,
            SourceRecord.tenant_id == tenant_id,
            Document.type == "sales_order",
            SourceRecord.source_system == "shopify",
            SourceRecord.external_id == source.external_id,
        )
        .limit(1)
    )
