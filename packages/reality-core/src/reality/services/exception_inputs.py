"""Tenant-scoped retained inputs for one read-only exception evaluation."""

from collections import defaultdict
from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from reality.db.core import (
    Commitment,
    CommitmentRevision,
    Document,
    DocumentLine,
    Item,
    Movement,
    Reservation,
)
from reality.services.core import _effective_commitment_value, _movement_quantities


@dataclass
class _ExceptionInputs:
    session: Session
    tenant_id: str
    terms: dict[str, tuple[datetime | None, Decimal, int]]
    movements: dict[tuple[str | None, str], Decimal]
    last_movements: dict[tuple[str | None, str], datetime]
    reserved: dict[str, Decimal]
    documents: dict[str, Document]
    lines: dict[str, DocumentLine]
    items: dict[str, Item]
    billing: dict[str, list[DocumentLine]]
    # Reads several classes share within one evaluation (the open items register,
    # for one); like every input here it lives no longer than the scope.
    cache: dict[Any, Any] = field(default_factory=dict)


_current: ContextVar[_ExceptionInputs | None] = ContextVar(
    "exception_inputs", default=None
)


def _inputs(session: Session, tenant_id: str) -> _ExceptionInputs | None:
    current = _current.get()
    if (
        current is not None
        and current.session is session
        and current.tenant_id == tenant_id
    ):
        return current
    return None


def _load(session: Session, tenant_id: str) -> _ExceptionInputs:
    revisions: dict[str, list[CommitmentRevision]] = defaultdict(list)
    for revision in session.scalars(
        select(CommitmentRevision)
        .where(CommitmentRevision.tenant_id == tenant_id)
        .order_by(CommitmentRevision.stated_at, CommitmentRevision.id)
    ):
        revisions[revision.commitment_id].append(revision)
    terms = {
        row.id: (
            _effective_commitment_value(row, revisions[row.id], "due_at"),
            Decimal(_effective_commitment_value(row, revisions[row.id], "quantity")),
            len(revisions[row.id]),
        )
        for row in session.scalars(
            select(Commitment).where(Commitment.tenant_id == tenant_id)
        )
    }
    documents = {
        row.id: row
        for row in session.scalars(
            select(Document).where(Document.tenant_id == tenant_id)
        )
    }
    lines = {
        row.id: row
        for row in session.scalars(
            select(DocumentLine).where(DocumentLine.tenant_id == tenant_id)
        )
    }
    billing: dict[str, list[DocumentLine]] = defaultdict(list)
    for line in lines.values():
        if line.billed_document_line_id:
            billing[line.billed_document_line_id].append(line)
    return _ExceptionInputs(
        session=session,
        tenant_id=tenant_id,
        terms=terms,
        movements=_movement_quantities(session, tenant_id),
        last_movements={
            (identity, kind): instant
            for identity, kind, instant in session.execute(
                select(
                    Movement.commitment_id,
                    Movement.type,
                    func.max(Movement.occurred_at),
                )
                .where(Movement.tenant_id == tenant_id)
                .group_by(Movement.commitment_id, Movement.type)
            )
        },
        reserved={
            identity: quantity
            for identity, quantity in session.execute(
                select(Reservation.commitment_id, func.sum(Reservation.quantity))
                .where(
                    Reservation.tenant_id == tenant_id, Reservation.status == "active"
                )
                .group_by(Reservation.commitment_id)
            )
        },
        documents=documents,
        lines=lines,
        items={
            row.id: row
            for row in session.scalars(select(Item).where(Item.tenant_id == tenant_id))
        },
        billing=dict(billing),
    )


@contextmanager
def _exception_input_scope(session: Session, tenant_id: str) -> Iterator[None]:
    """Never retain input facts beyond this evaluation, including on failure."""
    token = _current.set(_load(session, tenant_id))
    try:
        yield
    finally:
        _current.reset(token)
