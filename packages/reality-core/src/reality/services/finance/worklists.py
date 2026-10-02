"""Named finance worklists reuse canonical aging; membership is never stored."""

from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy.orm import Session

from reality.domain.finance import FEE_RECEIVABLE_TYPES
from reality.services.core import aging_register


def overdue_document_ids(
    session: Session, tenant_id: str, *, as_of: datetime | None = None
) -> set[str]:
    moment = as_of or datetime.now(UTC)
    return {
        row["document"].id
        for row in aging_register(session, tenant_id, as_of=moment)
        if row["status"] in {"open", "partial"}
        and Decimal(row["open"]) > 0
        and (row.get("days_overdue") or 0) > 0
        and row["document"].type not in FEE_RECEIVABLE_TYPES
    }
