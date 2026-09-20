"""Provider-agnostic intake of customer invoices and payments (feature 168).

Every source that delivers a sales invoice or a customer payment, synthetic Demo
Data today and payment providers later, normalises its payload into the shapes
below and hands them to the two interpretation cores. The cores compose only the
existing posting and settlement primitives in ``services.core``:

* an invoice is recorded with its lines linked to the order lines it bills, then
  posted (spec 076, spec 091);
* a payment is always recorded (tier 1); it is allocated only when a reference
  the source states resolves to exactly one posted invoice of the same party and
  currency (tier 2); otherwise ``payment_candidates`` offers read-time candidates
  with reasons that a person or agent confirms (tier 3).

Nothing here computes a discount or a difference from a rate (spec 088 DR-007),
writes off a residual, accepts a reduction, or invents an invoice for a payment.
Candidates are observations and are never stored.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session, aliased

from reality.db.core import (
    Document,
    DocumentLine,
    LedgerEntry,
    Party,
    SettlementAllocation,
    SourceRecord,
)
from reality.services import core
from reality.services.finance.accounts import resolve_account

ReferenceType = Literal[
    "invoice_number",
    "shop_id",
    "shop_order_number",
    "customer_reference",
    "customer_number",
]


class Reference(BaseModel):
    """One identifier the payer or provider stated, kept exactly as stated."""

    model_config = ConfigDict(frozen=True)
    type: ReferenceType
    value: str = Field(min_length=1)


class NormalisedInvoiceLine(BaseModel):
    model_config = ConfigDict(frozen=True)
    order_source_line_id: str = Field(min_length=1)
    source_line_id: str = Field(min_length=1)
    item_id: str | None = None
    quantity: Decimal = Field(gt=0)
    unit_price: Decimal = Field(ge=0)
    gross_amount: Decimal = Field(ge=0)
    unit: str = Field(min_length=1)
    description: str = ""


class NormalisedInvoice(BaseModel):
    """What the invoice core acts on; everything else stays in the lossless payload."""

    model_config = ConfigDict(frozen=True)
    order_source_system: str = Field(min_length=1)
    order_source_type: str = Field(min_length=1)
    order_external_id: str = Field(min_length=1)
    number: str = Field(min_length=1)
    party_id: str = Field(min_length=1)
    currency: str = Field(min_length=3, max_length=3)
    issued_at: datetime
    due_at: datetime | None = None
    payment_term_code: str = ""
    gross_amount: Decimal = Field(ge=0)
    lines: tuple[NormalisedInvoiceLine, ...] = Field(min_length=1)


class NormalisedPayment(BaseModel):
    """What the payment core acts on, named like the bank-statement file profile."""

    model_config = ConfigDict(frozen=True)
    party_id: str = Field(min_length=1)
    amount: Decimal = Field(gt=0)
    currency: str = Field(min_length=3, max_length=3)
    effective_at: datetime
    external_payment_id: str = Field(min_length=1)
    payment_number: str = ""
    money_path: str = ""
    references: tuple[Reference, ...] = ()
    remittance_text: str = ""


@dataclass(frozen=True)
class Resolution:
    """Where the stated references lead; ``invoices`` holds posted, unreversed ones."""

    invoices: tuple[Document, ...]
    reasons: tuple[str, ...] = ()

    @property
    def unambiguous(self) -> Document | None:
        return self.invoices[0] if len(self.invoices) == 1 else None


@dataclass(frozen=True)
class Candidate:
    invoice_id: str
    number: str
    open_amount: Decimal
    currency: str
    reasons: tuple[str, ...] = field(default_factory=tuple)


# ---------------------------------------------------------------------------
# Invoice core


def _existing(
    session: Session, tenant_id: str, source: SourceRecord, document_type: str
) -> Document | None:
    return session.scalar(
        select(Document).where(
            Document.tenant_id == tenant_id,
            Document.source_record_id == source.id,
            Document.type == document_type,
        )
    )


def _lines_of(session: Session, tenant_id: str, document_id: str) -> list[DocumentLine]:
    return list(
        session.scalars(
            select(DocumentLine).where(
                DocumentLine.tenant_id == tenant_id,
                DocumentLine.document_id == document_id,
            )
        )
    )


def _entries_of(
    session: Session, tenant_id: str, document_id: str
) -> list[LedgerEntry]:
    return list(
        session.scalars(
            select(LedgerEntry).where(
                LedgerEntry.tenant_id == tenant_id,
                LedgerEntry.document_id == document_id,
            )
        )
    )


def _order_document(
    session: Session, tenant_id: str, system: str, source_type: str, external_id: str
) -> Document:
    order_source = session.scalar(
        select(SourceRecord)
        .where(
            SourceRecord.tenant_id == tenant_id,
            SourceRecord.source_system == system,
            SourceRecord.source_type == source_type,
            SourceRecord.external_id == external_id,
        )
        .order_by(SourceRecord.version.desc())
    )
    order = (
        session.scalar(
            select(Document).where(
                Document.tenant_id == tenant_id,
                Document.source_record_id == order_source.id,
                Document.type == "sales_order",
            )
        )
        if order_source
        else None
    )
    if order is None:
        raise core.InvalidOperation("The invoice names an order Reality does not hold.")
    return order


def interpret_sales_invoice(
    session: Session, tenant_id: str, source: SourceRecord, invoice: NormalisedInvoice
) -> tuple[SourceRecord, Document, list[DocumentLine], list[LedgerEntry]]:
    """Record the stated invoice with lines billing the order lines, then post it."""
    existing = _existing(session, tenant_id, source, "sales_invoice")
    if existing:
        return (
            source,
            existing,
            _lines_of(session, tenant_id, existing.id),
            _entries_of(session, tenant_id, existing.id),
        )
    order = _order_document(
        session,
        tenant_id,
        invoice.order_source_system,
        invoice.order_source_type,
        invoice.order_external_id,
    )
    if order.party_id != invoice.party_id:
        raise core.InvalidOperation("The invoice names another party than its order.")
    order_lines = {
        line.source_line_id: line for line in _lines_of(session, tenant_id, order.id)
    }
    lines: list[dict[str, Any]] = []
    for line in invoice.lines:
        billed = order_lines.get(line.order_source_line_id)
        if billed is None:
            raise core.InvalidOperation(
                "The invoice bills an order line Reality does not hold."
            )
        lines.append(
            {
                "item_id": line.item_id or billed.item_id,
                "quantity": str(line.quantity),
                "unit_price": str(line.unit_price),
                "gross_amount": str(line.gross_amount),
                "unit": line.unit,
                "source_line_id": line.source_line_id,
                "description": line.description,
                "billed_document_line_id": billed.id,
            }
        )
    if invoice.payment_term_code:
        try:
            core.payment_term_by_code(session, tenant_id, invoice.payment_term_code)
        except core.NotFound as error:
            raise core.InvalidOperation(
                "The invoice names a payment term Reality does not hold."
            ) from error
    document, document_lines = core.create_manual_document_with_lines(
        session,
        tenant_id,
        "sales_invoice",
        invoice.number,
        invoice.party_id,
        lines,
        invoice.gross_amount,
        currency=invoice.currency,
        document_date=invoice.issued_at.date().isoformat(),
        payment_term_code=invoice.payment_term_code,
        source_record_id=source.id,
        _commit=False,
    )
    entries = core.post_sales_invoice(
        session, tenant_id, document.id, effective_at=invoice.issued_at, _commit=False
    )
    return source, document, document_lines, entries


# ---------------------------------------------------------------------------
# Reference resolution


def _posted_control(
    session: Session, tenant_id: str, invoice: Document
) -> LedgerEntry | None:
    """The invoice's receivable control entry when it is posted and not reversed."""
    try:
        entry = core._settlement_control_entry(session, tenant_id, invoice.id)
    except core.InvalidOperation:
        return None
    if core._ledger_reversal_for_group(session, tenant_id, entry.posting_group_id)[0]:
        return None
    return entry


def _invoices_billing(
    session: Session, tenant_id: str, order: Document
) -> list[Document]:
    order_line_ids = [line.id for line in _lines_of(session, tenant_id, order.id)]
    if not order_line_ids:
        return []
    invoice_ids = set(
        session.scalars(
            select(DocumentLine.document_id).where(
                DocumentLine.tenant_id == tenant_id,
                DocumentLine.billed_document_line_id.in_(order_line_ids),
            )
        )
    )
    return (
        list(
            session.scalars(
                select(Document).where(
                    Document.tenant_id == tenant_id,
                    Document.id.in_(invoice_ids),
                    Document.type == "sales_invoice",
                )
            )
        )
        if invoice_ids
        else []
    )


def _orders_by(
    session: Session, tenant_id: str, party_id: str, **where: str
) -> list[Document]:
    query = select(Document).where(
        Document.tenant_id == tenant_id,
        Document.party_id == party_id,
        Document.type == "sales_order",
    )
    for column, value in where.items():
        query = query.where(getattr(Document, column) == value)
    return list(session.scalars(query))


def resolve_references(
    session: Session,
    tenant_id: str,
    party_id: str,
    currency: str,
    references: tuple[Reference, ...] | list[Reference],
    *,
    source_system: str | None = None,
) -> Resolution:
    """Follow every stated reference to the posted invoices it names, party-scoped.

    Human numbers are looked up, never stored. A reference that leads to no
    invoice, to an unposted or reversed one, to another currency, or to several
    invoices explains itself in ``reasons`` and never allocates.
    """
    found: dict[str, Document] = {}
    reasons: list[str] = []
    for reference in references:
        if reference.type == "invoice_number":
            invoices = list(
                session.scalars(
                    select(Document).where(
                        Document.tenant_id == tenant_id,
                        Document.party_id == party_id,
                        Document.type == "sales_invoice",
                        Document.number == reference.value,
                    )
                )
            )
            if not invoices:
                reasons.append(f"no invoice {reference.value} for this customer")
        elif reference.type == "shop_id":
            order_sources = list(
                session.scalars(
                    select(SourceRecord).where(
                        SourceRecord.tenant_id == tenant_id,
                        SourceRecord.source_type == "order",
                        SourceRecord.external_id == reference.value,
                        *(
                            [SourceRecord.source_system == source_system]
                            if source_system
                            else []
                        ),
                    )
                )
            )
            orders = (
                list(
                    session.scalars(
                        select(Document).where(
                            Document.tenant_id == tenant_id,
                            Document.party_id == party_id,
                            Document.type == "sales_order",
                            Document.source_record_id.in_(
                                [s.id for s in order_sources]
                            ),
                        )
                    )
                )
                if order_sources
                else []
            )
            invoices = [
                inv
                for order in orders
                for inv in _invoices_billing(session, tenant_id, order)
            ]
            if not orders:
                reasons.append(
                    f"no order with shop id {reference.value} for this customer"
                )
            elif not invoices:
                reasons.append(f"order {reference.value} is not invoiced yet")
        elif reference.type in {"shop_order_number", "customer_reference"}:
            column = (
                "number"
                if reference.type == "shop_order_number"
                else "customer_reference"
            )
            orders = _orders_by(
                session, tenant_id, party_id, **{column: reference.value}
            )
            invoices = [
                inv
                for order in orders
                for inv in _invoices_billing(session, tenant_id, order)
            ]
            if not orders:
                reasons.append(f"no order {reference.value} for this customer")
            elif not invoices:
                reasons.append(f"order {reference.value} is not invoiced yet")
        else:  # customer_number
            party = session.scalar(
                select(Party).where(
                    Party.tenant_id == tenant_id,
                    Party.accounting_code == reference.value,
                )
            )
            reasons.append(
                "customer number identifies the customer only"
                if party is None or party.id == party_id
                else f"customer number {reference.value} names another customer"
            )
            continue
        for invoice in invoices:
            if invoice.currency != currency:
                reasons.append(
                    f"invoice {invoice.number} is in {invoice.currency}, not {currency}"
                )
            elif _posted_control(session, tenant_id, invoice) is None:
                reasons.append(f"invoice {invoice.number} is not posted")
            else:
                found[invoice.id] = invoice
    if len(found) > 1:
        reasons.append(
            "stated references name several invoices: "
            + ", ".join(sorted(invoice.number for invoice in found.values()))
        )
    return Resolution(tuple(found.values()), tuple(reasons))


# ---------------------------------------------------------------------------
# Payment core


def _receivable_entry(entries: list[LedgerEntry]) -> LedgerEntry:
    return next(entry for entry in entries if entry.account == "accounts_receivable")


def _allocations_touching(
    session: Session, tenant_id: str, entry_id: str
) -> list[SettlementAllocation]:
    return [
        allocation
        for allocation in core.active_settlement_allocations(
            session, tenant_id, entry_ids={entry_id}
        )
        if entry_id
        in (allocation.payment_ledger_entry_id, allocation.invoice_ledger_entry_id)
    ]


def interpret_customer_payment(
    session: Session, tenant_id: str, source: SourceRecord, payment: NormalisedPayment
) -> tuple[
    SourceRecord, Document, list[LedgerEntry], SettlementAllocation | None, Resolution
]:
    """Record the payment; allocate only an unambiguous stated reference, never more than open."""
    existing = _existing(session, tenant_id, source, "customer_payment")
    if existing:
        entries = _entries_of(session, tenant_id, existing.id)
        allocations = _allocations_touching(
            session, tenant_id, _receivable_entry(entries).id
        )
        return (
            source,
            existing,
            entries,
            allocations[0] if allocations else None,
            Resolution(()),
        )
    resolution = resolve_references(
        session,
        tenant_id,
        payment.party_id,
        payment.currency,
        payment.references,
        source_system=source.source_system,
    )
    invoice = resolution.unambiguous
    control = _posted_control(session, tenant_id, invoice) if invoice else None
    control_account_id = None
    if control is not None:
        try:
            resolve_account(
                session, tenant_id, "accounts_receivable", control.account_id
            )
            control_account_id = control.account_id
        except core.InvalidOperation:
            # The invoice's account is blocked: still record the money to an allowed
            # account, but leave matching to a reviewed correction.
            control = None
            resolution = Resolution(
                (),
                resolution.reasons
                + (f"invoice {invoice.number} uses a blocked account",),
            )
    entries = core.record_customer_payment(
        session,
        tenant_id,
        payment.party_id,
        payment.amount,
        currency=payment.currency,
        payment_number=payment.payment_number or None,
        source_record_id=source.id,
        effective_at=payment.effective_at,
        _control_account_id=control_account_id,
        _commit=False,
    )
    document = core._tenant_record(session, Document, tenant_id, entries[0].document_id)
    allocation = None
    if control is not None:
        open_amount = core.open_invoice_amount(session, tenant_id, invoice.id)
        allocatable = min(payment.amount, open_amount)
        if allocatable > 0:
            allocation = core.allocate_settlement(
                session,
                tenant_id,
                _receivable_entry(entries).id,
                control.id,
                allocatable,
                _commit=False,
            )
        else:
            resolution = Resolution(
                resolution.invoices,
                resolution.reasons + (f"invoice {invoice.number} is already settled",),
            )
    return source, document, entries, allocation, resolution


def unallocated_amount(
    session: Session, tenant_id: str, payment_document_id: str
) -> Decimal:
    """The payment's receivable credit minus its active allocations; read-time only."""
    entries = _entries_of(session, tenant_id, payment_document_id)
    if not entries:
        return Decimal(0)
    entry = _receivable_entry(entries)
    if core._ledger_reversal_for_group(session, tenant_id, entry.posting_group_id)[0]:
        return Decimal(0)
    used = sum(
        (
            allocation.amount
            for allocation in _allocations_touching(session, tenant_id, entry.id)
        ),
        Decimal(0),
    )
    return entry.amount - used


def _stated(source: SourceRecord | None) -> tuple[tuple[Reference, ...], str]:
    if source is None:
        return (), ""
    payload = json.loads(source.payload) if source.payload else {}
    references = tuple(
        Reference.model_validate(item)
        for item in payload.get("references", [])
        if isinstance(item, dict)
    )
    text = str(payload.get("remittance_text") or payload.get("reference") or "")
    return references, text


def _invoices_that_can_still_owe(
    session: Session, tenant_id: str, party_id: str | None, currency: str
) -> list[Document]:
    """The party's invoices a payment could still belong to, chosen in one read."""
    from reality.db.core import LedgerEntry, LedgerReversal, SettlementAllocation

    control_account, _ = core.SETTLEMENT_CONTROL["sales_invoice"]
    payment_entry = aliased(LedgerEntry)
    invoice_entry = aliased(LedgerEntry)
    reversal = aliased(LedgerReversal)
    settled = (
        select(
            invoice_entry.document_id.label("document_id"),
            func.sum(SettlementAllocation.amount).label("settled"),
        )
        .select_from(SettlementAllocation)
        .join(
            invoice_entry,
            invoice_entry.id == SettlementAllocation.invoice_ledger_entry_id,
        )
        .join(
            payment_entry,
            payment_entry.id == SettlementAllocation.payment_ledger_entry_id,
        )
        .outerjoin(
            reversal,
            and_(
                reversal.tenant_id == tenant_id,
                or_(
                    reversal.original_posting_group_id
                    == payment_entry.posting_group_id,
                    reversal.reversing_posting_group_id
                    == payment_entry.posting_group_id,
                ),
            ),
        )
        .where(
            SettlementAllocation.tenant_id == tenant_id,
            invoice_entry.account == control_account,
            reversal.id.is_(None),
        )
        .group_by(invoice_entry.document_id)
        .subquery()
    )
    charged = (
        select(
            LedgerEntry.document_id.label("document_id"),
            func.sum(LedgerEntry.amount).label("charged"),
        )
        .where(
            LedgerEntry.tenant_id == tenant_id,
            LedgerEntry.account == control_account,
            LedgerEntry.document_id.is_not(None),
        )
        .group_by(LedgerEntry.document_id)
        .subquery()
    )
    return list(
        session.scalars(
            select(Document)
            .join(charged, charged.c.document_id == Document.id)
            .outerjoin(settled, settled.c.document_id == Document.id)
            .where(
                Document.tenant_id == tenant_id,
                Document.party_id == party_id,
                Document.type == "sales_invoice",
                Document.currency == currency,
                func.coalesce(settled.c.settled, 0) < charged.c.charged,
            )
            .order_by(Document.number)
        )
    )


def payment_candidates(
    session: Session, tenant_id: str, payment_document_id: str
) -> list[Candidate]:
    """Invoices an unallocated payment may belong to, each with its reasons. Never stored."""
    payment = core._tenant_record(session, Document, tenant_id, payment_document_id)
    if payment.type != "customer_payment":
        raise core.InvalidOperation("Candidates exist for customer payments only.")
    remaining = unallocated_amount(session, tenant_id, payment.id)
    if remaining <= 0:
        return []
    source = (
        core._tenant_record(session, SourceRecord, tenant_id, payment.source_record_id)
        if payment.source_record_id
        else None
    )
    references, text = _stated(source)
    ambiguous = {
        invoice.id
        for invoice in resolve_references(
            session,
            tenant_id,
            payment.party_id,
            payment.currency,
            references,
            source_system=source.source_system if source else None,
        ).invoices
    }
    candidates: list[Candidate] = []
    invoices = _invoices_that_can_still_owe(
        session, tenant_id, payment.party_id, payment.currency
    )
    # Five reads for all of the customer's invoices instead of five per invoice: the
    # per-invoice form read every allocation of the company each time, so one payment
    # cost invoices × allocations and grew with every order recorded (spec 181).
    positions = core.settlement_positions(session, tenant_id, invoices)
    for invoice in invoices:
        position = positions.get(invoice.id)
        # Not posted, or touched by a reversal either way: what `_posted_control` refuses.
        if position is None or position.relation is not None:
            continue
        open_amount = position.open
        if open_amount <= 0:
            continue
        reasons: list[str] = []
        if open_amount == remaining:
            reasons.append("amount equals the open amount")
        if text and invoice.number and invoice.number in text:
            reasons.append("invoice number appears in the remittance text")
        if len(ambiguous) > 1 and invoice.id in ambiguous:
            reasons.append("stated reference names this invoice among others")
        if reasons:
            candidates.append(
                Candidate(
                    invoice.id,
                    invoice.number,
                    open_amount,
                    invoice.currency,
                    tuple(reasons),
                )
            )
    return candidates
