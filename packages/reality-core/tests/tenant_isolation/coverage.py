from __future__ import annotations

from collections.abc import Callable
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from reality.db.core import Base, BusinessEvent


def tenant_row_counts(session: Session, tenant_ids: tuple[str, ...]) -> dict[str, dict[str, int]]:
    """Capture tenant-owned row counts for atomicity assertions."""
    result: dict[str, dict[str, int]] = {}
    for table in sorted(Base.metadata.tables.values(), key=lambda item: item.name):
        tenant_column = table.c.get("tenant_id")
        if tenant_column is None:
            continue
        result[table.name] = {
            tenant_id: int(
                session.scalar(
                    select(func.count()).select_from(table).where(tenant_column == tenant_id)
                )
                or 0
            )
            for tenant_id in tenant_ids
        }
    return result


def event_sequences(session: Session, tenant_ids: tuple[str, ...]) -> dict[str, int]:
    return {
        tenant_id: int(
            session.scalar(
                select(func.coalesce(func.max(BusinessEvent.sequence), 0)).where(
                    BusinessEvent.tenant_id == tenant_id
                )
            )
            or 0
        )
        for tenant_id in tenant_ids
    }


def assert_no_side_effects(
    before: Any, after: Any, action: Callable[[], Any] | None = None
) -> None:
    if action is not None:
        action()
    assert after == before
