"""Explainable, tenant-scoped fulfillment readiness derived from Reality."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from reality.db.core import (
    Commitment,
    CommitmentHold,
    Document,
    DocumentLine,
    LedgerEntry,
    PaymentTerm,
    Reservation,
)
from reality.services.core import (
    InvalidOperation,
    active_party_delivery_hold,
    active_settlement_allocations,
    commitment_quantity,
    movement_quantity,
    stock_at,
)

ZERO = Decimal(0)


@dataclass(frozen=True)
class FulfillmentReadiness:
    commitment_id: str
    order_id: str | None
    ship_ready: bool
    blocker_codes: tuple[str, ...]
    currency: str
    required_amount: Decimal
    received_amount: Decimal
    remaining_amount: Decimal
    payment_term_id: str | None
    requires_prepayment: bool
    invoice_ids: tuple[str, ...]
    allocation_ids: tuple[str, ...]
    open_quantity: Decimal
    reserved_quantity: Decimal
    physical_quantity: Decimal
    commitment_hold_ids: tuple[str, ...]
    party_hold_ids: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        payment_policy = "prepayment" if self.requires_prepayment else "standard"
        blockers = [
            {
                "code": code,
                "detail": _blocker_detail(code, self),
                "links": _blocker_links(code, self),
            }
            for code in self.blocker_codes
        ]
        basis = {
            "commitment": {
                "id": self.commitment_id,
                "open_quantity": str(self.open_quantity),
            },
            "inventory": {
                "physical_quantity": str(self.physical_quantity),
                "reserved_quantity": str(self.reserved_quantity),
            },
            "commitment_hold_ids": list(self.commitment_hold_ids),
            "party_hold_ids": list(self.party_hold_ids),
            "invoice_ids": list(self.invoice_ids),
            "allocation_ids": list(self.allocation_ids),
        }
        return {
            "commitment_id": self.commitment_id,
            "document_id": self.order_id,
            "order_id": self.order_id,
            "ship_ready": self.ship_ready,
            "blocker_codes": list(self.blocker_codes),
            "blocking_reasons": list(self.blocker_codes),
            "blockers": blockers,
            "currency": self.currency,
            "required_amount": str(self.required_amount),
            "received_amount": str(self.received_amount),
            "remaining_amount": str(self.remaining_amount),
            "payment_term_id": self.payment_term_id,
            "requires_prepayment": self.requires_prepayment,
            "invoice_ids": list(self.invoice_ids),
            "allocation_ids": list(self.allocation_ids),
            "payment": {
                "policy": payment_policy,
                "required": str(self.required_amount),
                "received": str(self.received_amount),
                "remaining": str(self.remaining_amount),
                "payment_term_id": self.payment_term_id,
                "invoice_ids": list(self.invoice_ids),
                "allocation_ids": list(self.allocation_ids),
            },
            "lines": [
                {
                    "commitment_id": self.commitment_id,
                    "open_quantity": str(self.open_quantity),
                    "reserved_quantity": str(self.reserved_quantity),
                    "physical_quantity": str(self.physical_quantity),
                }
            ],
            "basis": basis,
            "links": [
                {"kind": kind, "id": identity}
                for kind, identities in (
                    ("payment_term", (self.payment_term_id,) if self.payment_term_id else ()),
                    ("invoice", self.invoice_ids),
                    ("settlement_allocation", self.allocation_ids),
                    ("commitment_hold", self.commitment_hold_ids),
                    ("party_hold", self.party_hold_ids),
                )
                for identity in identities
            ],
        }


def _blocker_detail(code: str, result: FulfillmentReadiness) -> str:
    if code == "prepayment_required":
        return (
            f"{result.required_amount} {result.currency} is required; "
            f"{result.received_amount} {result.currency} is allocated."
        )
    return {
        "prepayment_invoice_missing": "No posted order-backed customer receivable proves the payment basis.",
        "prepayment_attribution_ambiguous": "Invoice evidence covers more than this order and cannot be attributed automatically.",
        "insufficient_reservation": "The open delivery quantity is not fully reserved.",
        "insufficient_stock": "Physical stock is below the open delivery quantity.",
        "commitment_hold": "The delivery commitment has an active hold.",
        "party_delivery_hold": "The customer has an active delivery hold.",
    }.get(code, code.replace("_", " "))


def _blocker_links(code: str, result: FulfillmentReadiness) -> list[dict[str, str]]:
    if code.startswith("prepayment") and result.payment_term_id:
        return [{"kind": "payment_term", "id": result.payment_term_id}]
    if code == "commitment_hold":
        return [{"kind": "commitment_hold", "id": row} for row in result.commitment_hold_ids]
    if code == "party_delivery_hold":
        return [{"kind": "party_hold", "id": row} for row in result.party_hold_ids]
    return [{"kind": "commitment", "id": result.commitment_id}]


def fulfillment_readiness(
    session: Session, tenant_id: str, commitment_id: str
) -> FulfillmentReadiness:
    """Derive payment readiness for one customer-delivery commitment.

    Amounts are stated document and allocation values. This function never creates
    payment or fulfillment authority and never infers policy from a term label.
    """
    commitment = session.scalar(
        select(Commitment).where(
            Commitment.tenant_id == tenant_id,
            Commitment.id == commitment_id,
        )
    )
    if commitment is None:
        raise InvalidOperation("Fulfillment commitment not found.")
    if commitment.type != "customer_delivery":
        raise InvalidOperation("Readiness requires a customer-delivery commitment.")
    open_quantity = max(
        commitment_quantity(session, tenant_id, commitment.id)
        - movement_quantity(session, tenant_id, commitment.id, "shipment"),
        ZERO,
    )
    reserved_quantity = Decimal(
        session.scalar(
            select(func.coalesce(func.sum(Reservation.quantity), 0)).where(
                Reservation.tenant_id == tenant_id,
                Reservation.commitment_id == commitment.id,
                Reservation.status == "active",
            )
        )
        or ZERO
    )
    physical_quantity = (
        stock_at(session, tenant_id, commitment.item_id, commitment.location_id)
        if commitment.item_id
        else ZERO
    )
    commitment_hold_ids = tuple(
        session.scalars(
            select(CommitmentHold.id)
            .where(
                CommitmentHold.tenant_id == tenant_id,
                CommitmentHold.commitment_id == commitment.id,
                CommitmentHold.released_at.is_(None),
            )
            .order_by(CommitmentHold.id)
        )
    )
    party_hold = (
        active_party_delivery_hold(session, tenant_id, commitment.to_party_id)
        if commitment.to_party_id
        else None
    )
    party_hold_ids = (party_hold.id,) if party_hold else ()
    operational_blockers: list[str] = []
    if commitment_hold_ids:
        operational_blockers.append("commitment_hold")
    if party_hold_ids:
        operational_blockers.append("party_delivery_hold")
    if reserved_quantity < open_quantity:
        operational_blockers.append("insufficient_reservation")
    if physical_quantity < open_quantity:
        operational_blockers.append("insufficient_stock")
    if not commitment.document_id:
        return FulfillmentReadiness(
            commitment.id,
            None,
            not operational_blockers,
            tuple(operational_blockers),
            commitment.currency,
            ZERO,
            ZERO,
            ZERO,
            None,
            False,
            (),
            (),
            open_quantity,
            reserved_quantity,
            physical_quantity,
            commitment_hold_ids,
            party_hold_ids,
        )
    order = session.scalar(
        select(Document).where(
            Document.tenant_id == tenant_id,
            Document.id == commitment.document_id,
        )
    )
    if order is None or order.type != "sales_order":
        raise InvalidOperation("Customer-delivery order not found.")
    term = (
        session.scalar(
            select(PaymentTerm).where(
                PaymentTerm.tenant_id == tenant_id,
                PaymentTerm.id == order.payment_term_id,
            )
        )
        if order.payment_term_id
        else None
    )
    required = Decimal(order.gross_amount)
    if term is None or not term.requires_prepayment:
        return FulfillmentReadiness(
            commitment.id,
            order.id,
            not operational_blockers,
            tuple(operational_blockers),
            order.currency,
            required,
            ZERO,
            ZERO,
            order.payment_term_id,
            False,
            (),
            (),
            open_quantity,
            reserved_quantity,
            physical_quantity,
            commitment_hold_ids,
            party_hold_ids,
        )

    order_line_ids = set(
        session.scalars(
            select(DocumentLine.id).where(
                DocumentLine.tenant_id == tenant_id,
                DocumentLine.document_id == order.id,
            )
        )
    )
    invoice_rows = list(
        session.execute(
            select(DocumentLine.document_id, DocumentLine.billed_document_line_id)
            .join(
                Document,
                (Document.tenant_id == DocumentLine.tenant_id)
                & (Document.id == DocumentLine.document_id),
            )
            .where(
                DocumentLine.tenant_id == tenant_id,
                Document.type == "sales_invoice",
                Document.party_id == order.party_id,
                Document.currency == order.currency,
                DocumentLine.billed_document_line_id.in_(order_line_ids),
            )
        )
    )
    candidate_invoice_ids = {row.document_id for row in invoice_rows}
    ambiguous = False
    for invoice_id in candidate_invoice_ids:
        billed_ids = set(
            session.scalars(
                select(DocumentLine.billed_document_line_id).where(
                    DocumentLine.tenant_id == tenant_id,
                    DocumentLine.document_id == invoice_id,
                    DocumentLine.billed_document_line_id.is_not(None),
                )
            )
        )
        if not billed_ids.issubset(order_line_ids):
            ambiguous = True

    invoice_entries = list(
        session.scalars(
            select(LedgerEntry).where(
                LedgerEntry.tenant_id == tenant_id,
                LedgerEntry.document_id.in_(candidate_invoice_ids),
                LedgerEntry.account == "accounts_receivable",
                LedgerEntry.party_id == order.party_id,
                LedgerEntry.currency == order.currency,
            )
        )
    )
    invoice_ids = {entry.document_id for entry in invoice_entries if entry.document_id}
    entry_ids = {entry.id for entry in invoice_entries}
    allocations = active_settlement_allocations(
        session, tenant_id, entry_ids=entry_ids
    )
    payment_entry_ids = {row.payment_ledger_entry_id for row in allocations}
    valid_payments = {
        row.id
        for row in session.scalars(
            select(LedgerEntry).where(
                LedgerEntry.tenant_id == tenant_id,
                LedgerEntry.id.in_(payment_entry_ids),
                LedgerEntry.party_id == order.party_id,
                LedgerEntry.currency == order.currency,
            )
        )
    }
    qualifying = [] if ambiguous else [
        row
        for row in allocations
        if row.invoice_ledger_entry_id in entry_ids
        and row.payment_ledger_entry_id in valid_payments
        and row.currency == order.currency
    ]
    received = sum((Decimal(row.amount) for row in qualifying), ZERO)
    remaining = max(required - received, ZERO)
    blockers = list(operational_blockers)
    if not invoice_ids:
        blockers.append("prepayment_invoice_missing")
    if ambiguous:
        blockers.append("prepayment_attribution_ambiguous")
    if remaining > ZERO:
        blockers.append("prepayment_required")
    return FulfillmentReadiness(
        commitment.id,
        order.id,
        not blockers,
        tuple(blockers),
        order.currency,
        required,
        received,
        remaining,
        term.id,
        True,
        tuple(sorted(invoice_ids)),
        tuple(sorted(row.id for row in qualifying)),
        open_quantity,
        reserved_quantity,
        physical_quantity,
        commitment_hold_ids,
        party_hold_ids,
    )
