"""Tenant-scoped retained inputs for one read-only exception evaluation."""

from collections import defaultdict
from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from datetime import datetime
from decimal import Decimal
from functools import cached_property
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from reality.db.core import (
    Commitment,
    CommitmentRevision,
    Document,
    DocumentLine,
    Item,
    LedgerEntry,
    LedgerReversal,
    Movement,
    Reservation,
    SourceRecord,
)
from reality.services.core import _effective_commitment_value, _movement_quantities


class _ExceptionInputs:
    """Tenant-scoped inputs, read when a class first asks for one.

    Every one of these used to be read before any class ran, because the classes
    share them and reading per class was what made the derivation take 229 seconds
    (spec 181, PR #227). Sharing is kept; the eagerness is not. A class that has
    nothing to do — because the change set cannot have affected it — should cost
    nothing, and it cannot while the scope reads the company before it is asked.

    Each input is read at most once per evaluation and never retained beyond it.
    """

    def __init__(self, session: Session, tenant_id: str) -> None:
        self.session = session
        self.tenant_id = tenant_id
        # Reads several classes share within one evaluation (the open items register,
        # for one); like every input here it lives no longer than the scope.
        self.cache: dict[Any, Any] = {}

    @cached_property
    def terms(self) -> dict[str, tuple[datetime | None, Decimal, int]]:
        revisions: dict[str, list[CommitmentRevision]] = defaultdict(list)
        for revision in self.session.scalars(
            select(CommitmentRevision)
            .where(CommitmentRevision.tenant_id == self.tenant_id)
            .order_by(CommitmentRevision.stated_at, CommitmentRevision.id)
        ):
            revisions[revision.commitment_id].append(revision)
        return {
            row.id: (
                _effective_commitment_value(row, revisions[row.id], "due_at"),
                Decimal(
                    _effective_commitment_value(row, revisions[row.id], "quantity")
                ),
                len(revisions[row.id]),
            )
            for row in self.session.scalars(
                select(Commitment).where(Commitment.tenant_id == self.tenant_id)
            )
        }

    @cached_property
    def movements(self) -> dict[tuple[str | None, str], Decimal]:
        return _movement_quantities(self.session, self.tenant_id)

    @cached_property
    def last_movements(self) -> dict[tuple[str | None, str], datetime]:
        return {
            (identity, kind): instant
            for identity, kind, instant in self.session.execute(
                select(
                    Movement.commitment_id,
                    Movement.type,
                    func.max(Movement.occurred_at),
                )
                .where(Movement.tenant_id == self.tenant_id)
                .group_by(Movement.commitment_id, Movement.type)
            )
        }

    @cached_property
    def reserved(self) -> dict[str, Decimal]:
        return {
            identity: quantity
            for identity, quantity in self.session.execute(
                select(Reservation.commitment_id, func.sum(Reservation.quantity))
                .where(
                    Reservation.tenant_id == self.tenant_id,
                    Reservation.status == "active",
                )
                .group_by(Reservation.commitment_id)
            )
        }

    @cached_property
    def documents(self) -> dict[str, Document]:
        return {
            row.id: row
            for row in self.session.scalars(
                select(Document).where(Document.tenant_id == self.tenant_id)
            )
        }

    @cached_property
    def sources(self) -> dict[str, SourceRecord]:
        return {
            row.id: row
            for row in self.session.scalars(
                select(SourceRecord)
                .join(Document, Document.source_record_id == SourceRecord.id)
                .where(Document.tenant_id == self.tenant_id)
                .distinct()
            )
        }

    @cached_property
    def lines(self) -> dict[str, DocumentLine]:
        return {
            row.id: row
            for row in self.session.scalars(
                select(DocumentLine).where(DocumentLine.tenant_id == self.tenant_id)
            )
        }

    @cached_property
    def items(self) -> dict[str, Item]:
        return {
            row.id: row
            for row in self.session.scalars(
                select(Item).where(Item.tenant_id == self.tenant_id)
            )
        }

    @cached_property
    def released_invoices(self) -> set[str]:
        """Documents whose every posting group is reversed (spec 124 FR-004)."""
        groups: dict[str, set[str]] = defaultdict(set)
        for document_id, group in self.session.execute(
            select(LedgerEntry.document_id, LedgerEntry.posting_group_id).where(
                LedgerEntry.tenant_id == self.tenant_id,
                LedgerEntry.document_id.is_not(None),
            )
        ):
            groups[document_id].add(group)
        reversed_groups = set(
            self.session.scalars(
                select(LedgerReversal.original_posting_group_id).where(
                    LedgerReversal.tenant_id == self.tenant_id
                )
            )
        )
        return {
            document_id
            for document_id, values in groups.items()
            if values <= reversed_groups
        }

    @cached_property
    def billing(self) -> dict[str, list[DocumentLine]]:
        billing: dict[str, list[DocumentLine]] = defaultdict(list)
        for line in self.lines.values():
            if line.billed_document_line_id:
                billing[line.billed_document_line_id].append(line)
        return dict(billing)


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


@contextmanager
def _exception_input_scope(session: Session, tenant_id: str) -> Iterator[None]:
    """Never retain input facts beyond this evaluation, including on failure."""
    token = _current.set(_ExceptionInputs(session, tenant_id))
    try:
        yield
    finally:
        _current.reset(token)
