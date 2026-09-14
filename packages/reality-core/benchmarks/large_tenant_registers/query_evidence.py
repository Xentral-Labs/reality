from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass

from sqlalchemy import event
from sqlalchemy.orm import Session


@dataclass(frozen=True)
class QueryEvidence:
    statement: str
    has_tenant_scope: bool
    has_limit: bool
    has_order: bool
    is_count: bool
    is_bounded: bool


@contextmanager
def capture_queries(session: Session) -> Iterator[list[QueryEvidence]]:
    evidence: list[QueryEvidence] = []
    bind = session.get_bind()

    def observe(_conn, _cursor, statement, _parameters, _context, _executemany):
        normalized = " ".join(statement.split())
        lowered = normalized.lower()
        if not lowered.startswith(("select", "with")):
            return
        is_count = "count(" in lowered
        is_bounded = any(
            marker in lowered
            for marker in (
                " limit ",
                "count(",
                "max(",
                " group by ",
                " in (",
                "tenant.id = ",
                " document_id = ",
                " posting_group_id = ",
                " projection_name = ",
                " commitment_id = ",
                " item_id = ",
            )
        )
        evidence.append(
            QueryEvidence(
                statement=normalized,
                has_tenant_scope="tenant_id" in lowered,
                has_limit=" limit " in lowered,
                has_order=" order by " in lowered,
                is_count=is_count,
                is_bounded=is_bounded,
            )
        )

    event.listen(bind, "before_cursor_execute", observe)
    try:
        yield evidence
    finally:
        event.remove(bind, "before_cursor_execute", observe)


def summarize_queries(evidence: list[QueryEvidence]) -> list[dict[str, object]]:
    unique = {row.statement: row for row in evidence}
    return [
        {
            "statement": row.statement,
            "has_tenant_scope": row.has_tenant_scope,
            "has_limit": row.has_limit,
            "has_order": row.has_order,
            "is_count": row.is_count,
            "is_bounded": row.is_bounded,
        }
        for row in unique.values()
    ]
